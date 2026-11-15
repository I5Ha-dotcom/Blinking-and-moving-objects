# Blinking-and-moving-objects
 I'm doing the NASA Space Apps Challenge 2026, "Planet X and SPHEREx",  The challenge: build a public web tool where you enter a patch of the sky and see NASA SPHEREx images of it as a short time-lapse, so anyone can spot moving objects like brown dwarfs, comets and asteroids.
# SPHEREx Blink

Compare public SPHEREx observations of multiple targets side by side, in synchronized time order, to spot things that move.

## Problem and proposed solution
Finding a moving or changing source in a large collection of astronomical images can require manually opening and comparing observations from different dates. This makes it difficult to notice motion, especially when observations are separated in time or the object is faint.

SPHEREx Blink brings observations for selected sky positions into one browser view. It aligns image cutouts to a common sky orientation and lets users blink through them in time order, compare different targets together, and mark candidate positions for follow-up. An offline simulation makes the interface usable for demonstrations when IRSA is unavailable; it does not represent real astronomical observations.

## How it works
Enter object names or `RA, Dec` coordinates. Names are resolved to sky coordinates, and the online search asks IRSA for SPHEREx observations covering each position. The app retrieves image cutouts, reprojects them to a common tangent-plane grid (north up, east left), and displays the resulting frames in a synchronized timeline. Users can inspect the images by blinking, stepping, and scrubbing, then mark a source across frames and export the measurements.

The browser UI is served by a FastAPI backend. The backend uses IRSA's TAP service to find observations and its cutout service to fetch FITS images; Astropy WCS and SciPy interpolation align the cutouts, and the backend returns PNG frames. Search results and generated cutouts are cached on the server. Search history and motion marks are stored separately in the browser's local storage.

## Main features
- Compare up to 9 different targets, one per panel, with synchronized playback; alternatively use adjacent sky tiles or a single field.
- Choose synchronized playback with one shared timeline, or independent playback with per-target play/pause, frame scrubber, speed, and Difference controls.
- Search by resolvable object name or explicit sky coordinates.
- Browse observations by date and detector band, focus a panel, or return to the grid.
- View signed differences from the per-band median: warm colors indicate brighter residuals, cyan indicates dimmer residuals, and black indicates no change. This is a visual aid, not calibrated photometry.
- Run a local moving-source demo without contacting IRSA.
- Mark source positions across frames, remove marks, inspect or auto-find candidate paths, and export JSON or CSV measurements.
- Save up to 30 searches in the current browser profile and restore them with the saved-search selector or Back/Forward navigation.

## Run
In Windows PowerShell, from this folder:

    py -3.12 -m venv venv
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
    .\venv\Scripts\python.exe -m uvicorn app:app --reload

    # open http://127.0.0.1:8000

The default **Different targets** mode loads the included watchlist example. Edit it to compare up to 9 different object names or `RA, Dec` coordinate pairs, one per line. Each target gets its own tile.

Other view modes are **Adjacent sky tiles**, which follows one center position across a 2 × 2 or 3 × 3 north-up, east-left mosaic, and **Single field**.

**Find watchlist online** searches IRSA separately for each target. All panels share one timeline and show the nearest observation for each date. Use **Focus** to expand a panel and **Grid** to return to the mosaic. Multi-panel searches are capped at 20 frames per panel (12 for 9 panels) and use 200-pixel cutouts to limit network use and memory.

Choose **Synchronized** playback for a shared date axis, or **Independent per object** to get a separate Play/Pause button, frame scrubber, speed, and Difference toggle on each panel. In online searches, targets can have different observation dates and counts; independent controls let you browse each target's available frames directly.

Use **Run demo** to play a local simulation without contacting IRSA. In different-target mode, every panel has its own synthetic moving source.

## Search history and motion measurements
Successful searches and demos are saved in this browser (up to 30 entries), along with any motion marks. Use **Open selected** to restore a saved run; the **Back** and **Forward** buttons and the browser's own navigation restore earlier runs too. Restoring an online search re-queries IRSA and reloads its frames.

History uses this browser profile's local storage; it is not account-based, shared across devices, or stored in SQLite. Anyone using the same browser profile can see its saved searches. **Clear saved history** removes the local entries.

Pause on a frame and click the moving source to mark it. The app measures its change in sky position from the previous mark; Shift+click removes a mark. **Auto-find path** suggests moving-source positions across frames; verify those suggestions on the images. Use **Download JSON**, **Download CSV**, and **Download day-to-day CSV** to export measurements.

## Results, potential impact, and limitations
The local demo provides a way to exercise the multi-target display, synchronized controls, and motion-mark workflow without a working network connection. In online mode, the app can organize returned public observations into a common view and help users visually inspect possible motion. It is an exploratory visualization aid, not an automated discovery or confirmation system; candidates need independent scientific review.

Online operation depends on IRSA and the external name-resolution service being reachable. IRSA may be slow or return temporary errors; cached search results and cutouts can help for previously requested data, but do not guarantee that a new search will work offline. Real-data coverage, image quality, and the reliability of motion measurements depend on the available observations and user inspection. Auto-find results are suggestions and should be checked against the images.

Search history is local to the browser profile: it is not account-based, shared across devices, or stored in SQLite. Anyone using the same browser profile can see its saved searches. Clearing browser storage or using another profile removes or hides that history. The multi-panel frame caps and smaller cutouts reduce network and memory use, but can limit temporal sampling and image detail. Frames are labelled with detector band (D1 to D6); the separate Colab notebook also computes the exact wavelength at the target.
