"""SPHEREx Blink — backend
"""
import json
import hashlib
import io
import pathlib
import re
import time
import warnings

import numpy as np
import requests
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.visualization import AsinhStretch, ImageNormalize, ZScaleInterval
from astropy.wcs import WCS
from astroquery.ipac.irsa import Irsa
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from scipy.ndimage import map_coordinates

warnings.filterwarnings("ignore")

IRSA = "https://irsa.ipac.caltech.edu/"
CACHE = pathlib.Path(__file__).parent / "cache"
CACHE.mkdir(exist_ok=True)
HERE = pathlib.Path(__file__).parent

app = FastAPI(title="SPHEREx Blink")


@app.get("/api/resolve")
def resolve(name: str):
    """Turn an object name (e.g. 'WISE 0855-0714') into RA/Dec using CDS Sesame."""
    try:
        c = SkyCoord.from_name(name)
    except Exception:
        raise HTTPException(404, f"Could not find '{name}'. Try another name or enter RA/Dec.")
    return {"ra": c.ra.deg, "dec": c.dec.deg}


def run_tap(query, tries=3):
    """Ask IRSA's database. Async job first (best for slower queries), then a plain query; retry on hiccups."""
    last = None
    for attempt in range(1, tries + 1):
        for how in ("async", "sync"):
            try:
                res = Irsa.tap.run_async(query) if how == "async" else Irsa.query_tap(query)
                return res.to_table() if hasattr(res, "to_table") else res
            except Exception as e:
                last = e
                if "proxy error" in str(e).lower():
                    raise
        if attempt < tries:
            time.sleep(3 * attempt)
    raise last


@app.get("/api/search")
def search(
    ra: float,
    dec: float,
    band: str = "D2",
    max_frames: int = Query(60, le=200),
):
    if band != "all" and not re.fullmatch(r"D[1-6]", band):
        raise HTTPException(400, "band must be 'all' or D1 to D6")

    search_key = hashlib.md5(f"search_{ra:.5f}_{dec:.5f}_{band}_{max_frames}".encode()).hexdigest()
    search_cache = CACHE / f"{search_key}.json"

    band_filter = f"AND p.energy_bandpassname = 'SPHEREx-{band}'" if band != "all" else ""
    query = f"""
        SELECT a.uri AS uri, p.time_bounds_lower AS mjd, p.energy_bandpassname AS band
        FROM spherex.artifact a
        JOIN spherex.plane p ON a.planeid = p.planeid
        WHERE 1 = CONTAINS(POINT('ICRS', {float(ra)}, {float(dec)}), p.poly)
        {band_filter}
        ORDER BY p.time_bounds_lower
    """
    try:
        tbl = run_tap(query)
        frames, seen = [], set()
        for row in tbl:
            uri = str(row["uri"]).lstrip("/")
            if uri in seen:
                continue
            seen.add(uri)
            t = float(row["mjd"])
            frames.append({
                "url": IRSA + uri,
                "mjd": t,
                "date": Time(t, format="mjd").iso[:16],
                "band": str(row["band"]).replace("SPHEREx-", ""),
            })
        total = len(frames)
        if total > max_frames:
            keep = np.unique(np.linspace(0, total - 1, max_frames).astype(int))
            frames = [frames[i] for i in keep]
        result = {"count": total, "shown": len(frames), "frames": frames}
        search_cache.write_text(json.dumps(result))
        return result
    except Exception as e:
        if search_cache.exists():
            return json.loads(search_cache.read_text())
        if "proxy error" in str(e).lower():
            raise HTTPException(
                502,
                "IRSA's TAP service returned a proxy error. Check your network, VPN, or proxy, then try again.",
            )
        raise HTTPException(502, f"IRSA's database did not answer ({type(e).__name__}). Usually temporary, so try again in a minute.")

def _target_wcs(ra, dec, size_deg, npix):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(npix + 1) / 2, (npix + 1) / 2]
    s = size_deg / npix
    w.wcs.cdelt = [-s, s]
    return w


def _reproject_interp(data, src_wcs, target_wcs, shape_out):
    y, x = np.indices(shape_out, dtype=float)
    ra, dec = target_wcs.pixel_to_world_values(x, y)
    src_x, src_y = src_wcs.world_to_pixel_values(ra, dec)
    out = map_coordinates(
        data,
        [src_y, src_x],
        order=1,
        mode="constant",
        cval=np.nan,
        prefilter=False,
    )
    return out, None


def _download_cutout(url, ra, dec, size_deg):
    key = hashlib.md5(f"{url}{ra}{dec}{size_deg}".encode()).hexdigest()
    path = CACHE / f"{key}.fits"
    if not path.exists():
        sep = "&" if "?" in url else "?"
        r = requests.get(f"{url}{sep}center={ra},{dec}d&size={size_deg}", timeout=120)
        r.raise_for_status()
        if not r.content.startswith(b"SIMPLE"):
            raise ValueError("IRSA did not return a FITS file")
        path.write_bytes(r.content)
    return path


@app.get("/api/frame")
def frame(url: str, ra: float, dec: float, size: float = 0.1, npix: int = Query(400, le=800)):
    """One cutout, regridded to the shared sky grid (north up, east left), as PNG."""
    if not url.startswith(IRSA):  # only ever fetch from IRSA
        raise HTTPException(400, "Only IRSA URLs are allowed")
    png_path = CACHE / (hashlib.md5(f"{url}{ra}{dec}{size}{npix}".encode()).hexdigest() + ".png")
    if png_path.exists():
        return Response(png_path.read_bytes(), media_type="image/png")
    try:
        with fits.open(_download_cutout(url, ra, dec, size)) as hdul:
            names = [h.name for h in hdul]
            hdu = hdul["IMAGE"] if "IMAGE" in names else next(h for h in hdul if h.data is not None and h.data.ndim == 2)
            data = np.array(hdu.data, dtype=float)
            src_wcs = WCS(hdu.header)
        out, _ = _reproject_interp(data, src_wcs, _target_wcs(ra, dec, size, npix), (npix, npix))
    except Exception as e:
        raise HTTPException(502, f"Could not build frame: {e}")

    good = np.isfinite(out)
    if good.sum() < 10:
        raise HTTPException(404, "Target is outside this image")
    filled = np.where(good, out, np.nanmedian(out))
    norm = ImageNormalize(filled, interval=ZScaleInterval(), stretch=AsinhStretch(0.3))
    img = np.where(good, np.clip(norm(filled), 0, 1), 0)
    img = (img * 255).astype(np.uint8)
    img = np.flipud(img)  # FITS origin is bottom-left
    buf = io.BytesIO()
    Image.fromarray(img, "L").save(buf, format="PNG")
    png_path.write_bytes(buf.getvalue())
    return Response(buf.getvalue(), media_type="image/png")


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
