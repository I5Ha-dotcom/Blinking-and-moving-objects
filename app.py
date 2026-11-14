import hashlib
import io
import pathlib
import warnings
from concurrent.futures import ThreadPoolExecutor

import astropy.units as u
import numpy as np
import requests
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.visualization import AsinhStretch,ImageNormalize,ZScaleInterval
from astropy.wcs import WCS
from astroquery.ipac.irsa import Irsa
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import FileResponse.Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from reproject import reproject_interp

warnings.filter.warnings("ignore")

IRSA = "https://irsa.ipac.caltech.edu/"
COLLECTIONS ={"wide":"spherex_qr2","deep":"spherex_qr2_deep"}
CACHE= pathlib.Path(__file__).parent/"cache"
CACHE.mkdir(exist_ok=True)
HERE=pathlib.Path(__file__).parent

app=FastAPI(title="SPHEREx Blink")

@app.get("/api/resolve")
def resolve(name:str):
  try:
    c=SkyCoord.from_name(name)
  except Exception:
    raise HHTPException(404,
