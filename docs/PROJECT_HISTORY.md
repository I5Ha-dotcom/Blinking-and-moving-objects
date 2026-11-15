# SPHEREx Blink: project history and development log

This document records the project idea, how the prototype evolved, the important design decisions, and the problems encountered while building it. It is intended as a human-readable development story, not a claim that every feature was built in one uninterrupted sequence.

> **About the timeline:** The sequence below is reconstructed from the project notes and development conversation. The repository currently has no Git commits, so exact implementation dates and commit-by-commit attribution are unavailable.

## 1. The original idea

The project was created for the **Planet X and SPHEREx** challenge. The starting question was: could someone inspect observations of a sky position across different dates by blinking between images, making changes or possible motion easier to notice?

The idea grew into a browser-based tool that would:

1. Let a user choose one or more objects, or enter sky coordinates.
2. Find SPHEREx observations for those positions through NASA/IPAC Infrared Science Archive (IRSA).
3. Align image cutouts so they can be compared consistently.
4. Let the user browse observations over time and inspect possible changes.
5. Support visual marking and export, while clearly separating exploratory measurements from scientific confirmation.

An important practical requirement emerged early: the project should still be demonstrable if a remote archive or network connection is unavailable. That led to a local synthetic demo. Its generated images are for trying the interface only; they are not SPHEREx observations.

## 2. How the prototype took shape

### Step 1 — Build the archive-backed path

The backend was organized around a FastAPI application. It resolves object names to coordinates, queries IRSA's SPHEREx metadata, requests FITS cutouts, and prepares images for the browser. The browser presents the controls and image panels; the Python backend handles the astronomy data operations.

The image workflow uses Astropy for FITS and world-coordinate information and SciPy interpolation to put cutouts onto a shared north-up, east-left view. Processed images are returned to the browser as PNG frames.

### Step 2 — Make the image viewer usable without archive access

Remote archive calls were unreliable in the development environment, including IRSA TAP proxy errors. Waiting on a remote search made it difficult to demonstrate or test the viewer.

**Change:** a local demo mode was added so the interface could be exercised without contacting IRSA. It generates synthetic frames and simulated dates, and labels them as demo content. The demo helps validate browsing and interaction; it does not validate scientific results or live archive connectivity.

### Step 3 — Compare multiple targets, not just one field

The use case expanded from looking at one position to comparing separate objects. The distinction matters: separate targets belong in separate panels, whereas a sky mosaic shows adjacent patches around one center position.

**Change:** the interface gained view choices for different targets, adjacent sky tiles, and a single field. In the different-target view, each tile represents a different target rather than repeating the same object. The multi-target view also supports a synchronized timeline.

### Step 4 — Make playback work for different observation cadences

A single shared timeline is convenient for comparing targets together, but real targets may have different observation dates and frame counts. A shared control cannot always show every target's sequence at its own pace.

**Change:** playback now offers two modes:

- **Synchronized:** one shared play/pause, timeline, speed, and Difference setting for all panels.
- **Independent per object:** each panel has its own play/pause, frame scrubber, speed, and Difference setting.

The independent mode was checked to ensure that adjusting one target's controls does not change another target's frame.

### Step 5 — Improve visual comparison

The Difference view initially rendered unchanged pixels as gray, which made it difficult to understand what the colors meant.

**Change:** unchanged areas were made black, brighter residuals use warm colors, and dimmer residuals use cyan. The view is described as a visual aid, not calibrated photometry.

### Step 6 — Add source marking and review

The interaction grew beyond passive viewing. Users can pause on a frame, mark a source position, review its apparent angular motion across observations, and export measurements. The app also includes path display and an auto-find suggestion that should be verified by looking at the images.

The distinction between angular motion and distance became important as the project expanded. The app measures apparent angular change on the sky for a marked source. It does **not** calculate physical distance, physical speed, or pairwise separation between different targets in separate panels.

### Step 7 — Preserve browser-local work

Users wanted to revisit earlier searches and marks, including with Back and Forward navigation.

**Change:** successful searches and demos, along with marks, are saved in the current browser profile. The browser History API supports navigation between searches. This is intentionally browser-local storage, not a server account or SQLite database; entries do not sync across devices.

### Step 8 — Explain the interface inside the app

The app's controls and modes can be unfamiliar to a first-time user. A long block of instructions was not a good fit for the main screen.

**Change:** the dense paragraph was replaced with a concise note and an interactive **How to use** guide. The initial guide was too short, so it was expanded to cover the actual controls and skip steps that do not apply to the selected view or playback mode. It can be reopened after the first visit.

### Step 9 — Document and demonstrate the work

The README was expanded to cover the challenge, problem and proposed solution, system workflow, architecture, technologies, data sources, full user guide, results, limitations, and references. A screenshot and a supplied demo recording were added to the repository.

The screenshot is from the local synthetic demo and is labelled as such. The public prototype page was confirmed to load, but that alone does not prove that a new live IRSA search succeeds.

## 3. Problems encountered and what changed

| Problem or question | What was learned | Response or current status |
|---|---|---|
| Online search appeared stuck at “searching IRSA” and no animation appeared. | A remote archive search depends on the network and can fail or take time; the UI cannot animate frames that have not loaded. | Added an offline synthetic demo for trying playback independently. Real-data searches still depend on IRSA availability. |
| IRSA TAP returned proxy errors during development. | This was an upstream/network availability issue in the environment, not evidence that the offline demo was real data. | The app reports an error for proxy failures and the demo provides an offline fallback. End-to-end live search remains unverified here. |
| The reprojection dependency was unavailable. | A dedicated reprojection package was not necessary for the implemented alignment workflow. | Used Astropy WCS with SciPy interpolation instead of requiring `reproject`. |
| Difference view looked gray. | Unchanged image regions were being rendered as gray, obscuring the residual signal. | Switched to black for unchanged regions, warm colors for brighter residuals, and cyan for dimmer residuals. |
| Multiple panels looked like repeated copies of one object. | Comparing distinct targets and viewing neighboring sky tiles are different tasks. | Added separate view modes and made the different-target grid assign one target to each panel. |
| One shared playback control did not suit targets with different dates. | Observation sequences can differ by target. | Added independent per-object controls alongside synchronized playback. |
| It was unclear how to measure distance between two objects. | Marking measures apparent angular motion for a source across frames; it is not a physical distance and is not pairwise separation between target panels. | Documented the distinction and kept unsupported distance calculations out of the claims. |
| The first in-app guide had too few steps. | Users need guidance for the real controls and conditional view modes, not just a short introduction. | Expanded the walkthrough to cover the interface and conditionally omit irrelevant steps. |
| Some guided-tour browser automation clicks timed out. | The tour scrolls and focuses its highlighted target, which can make a timed click unreliable. | Verified tour behavior through direct page interactions instead of treating the timeout as an app failure. |

## 4. Important design decisions

- **Real data and demo data are separate:** synthetic frames are useful for demonstrations and interaction testing, but are never described as NASA observations.
- **Panels have explicit meanings:** a target-comparison grid is distinct from an adjacent-sky mosaic.
- **Playback is flexible:** synchronized controls support side-by-side comparison; independent controls handle differing frame sequences.
- **History is browser-local:** no login, cross-device synchronization, or SQLite history is claimed.
- **Measurements are bounded:** the UI reports apparent angular motion and does not infer a source's physical distance or speed.
- **Online availability is not assumed:** archive and name-resolution services are external dependencies and can be unavailable.

## 5. Current project status

### Implemented in the prototype

- Search by object name or explicit sky coordinates.
- Search IRSA for SPHEREx metadata and request FITS cutouts.
- Align image cutouts to a shared sky orientation for display.
- Different-target, adjacent-sky-tile, and single-field views.
- Synchronized and independent playback.
- Synthetic offline demo.
- Difference visualization, motion marks, path review, and data exports.
- Browser-local saved searches and Back/Forward navigation.
- First-use interactive guide, README, architecture diagrams, screenshot, and demo recording.

### Verified or not verified

- The local synthetic demo and key UI interactions were exercised in a browser.
- The deployed prototype page was observed to load.
- Successful end-to-end querying and loading of real SPHEREx observations through IRSA has **not** been verified in this environment because of prior proxy errors.
- The synthetic demo does not validate the accuracy of detections or measurements on real observations.

### Known limitations

- Coverage and image cadence depend on available archive observations.
- IRSA and the external name resolver must be reachable for online searches.
- A synchronized panel may show its nearest observation to a shared date, not an observation from exactly the same instant.
- Difference colors are a visual comparison, not calibrated photometry.
- Auto-find paths are suggestions and need visual review.
- Motion marks estimate apparent angular movement; no pairwise target separation or physical distance is calculated.
- Browser-local history is tied to one browser profile and can be cleared with browser storage.

## 6. Reproducing the current prototype

From the `spherex-blink` project directory in Windows PowerShell:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`, use **Run demo** to try the interface without archive access, and use **Find images online** only when the external services are reachable.

## 7. A useful next-step backlog

These are possible future improvements, not features currently claimed as complete:

1. Verify and record a successful live IRSA search, including sample query inputs and returned observation metadata.
2. Add automated tests for backend search parsing, cutout handling, and reprojection using small fixtures.
3. Add a comparison tool for angular separation between targets when their sky coordinates are known.
4. If physical distances are needed, integrate an explicitly sourced distance measurement and show its assumptions and uncertainty; do not infer it from image separation.
5. Improve provenance in exported files so users can distinguish archive observations, demo frames, dates, bands, and processing steps.
6. Consider responsive layout, accessibility review, and a clearer online-loading/retry experience.
