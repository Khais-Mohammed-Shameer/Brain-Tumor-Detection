# Browser QA — 5 November 2026

Verified using the Codex in-app Chromium browser against the actual Vite app and the built production app, not a static mockup.

| Check | Observed outcome |
| --- | --- |
| Source tumor-labelled reference | Tumor label favored; score `0.9997071623802185` in the production browser run |
| Source no-tumor-labelled reference | No-tumor label favored; score `0.006684696301817894` |
| Black PNG upload | Rejected as blank/low contrast; no prediction shown |
| Random RGB noise PNG upload | Rejected as high-frequency noise; no prediction shown |
| Text file renamed `.png` | Read error explained in the viewer; no uncaught UI exception |
| 32 × 32 PNG upload | Rejected as undersized |
| Model-input view, zoom and reset | Display changes work; reset returns to 100% |
| Grad-CAM | Actual computed PNG overlay appears on the processed input; map pixels have nonzero alpha and varying colors |
| JSON export | File downloaded, parsed and checked against the numerical Python reference; retained as `browser-export-example.json` |
| Evidence view | Source attribution, independent-evaluation status and leakage limitation are visible |
| Interactive model view | Selecting processing tabs changes the explanation and model-input view |
| Mobile navigation | Menu opens/closes and switches views |
| 390 px mobile layout | No horizontal document overflow; loaded images have nonzero natural dimensions |
| 1440 px desktop layout | No horizontal document overflow or missing images |
| Production offline installation | OFFLINE READY appears after all application assets are cached |
| Cold page reload after stopping the local HTTP server | Page reloads from the service worker, reference inference completes and Grad-CAM computes without a running server |

The production offline reference run reported approximately 26 ms for WebGL inference and 238 ms for the full warmed analysis on this computer. These are observed local timings, not performance guarantees for other devices.

The reference examples are from the source dataset and are not an independent accuracy test. Numerical parity and software behavior do not establish clinical validity. Basic input gates cannot identify every non-MRI image.

Windows/macOS launch scripts are provided; the Python server and production HTTP serving were exercised on macOS. The Windows batch launcher, physical drag-and-drop from the operating system, other browsers and a wider range of medical image formats were not independently tested. The app supports JPG/PNG, not DICOM studies.

Numerical CPU checks and repeated-inference tensor retention are recorded in `model-parity-results.json`. Six research integrity tests pass. A complete research-workflow smoke test trained and evaluated a fresh model on 40 synthetic geometric images; that checks software plumbing only and is excluded from MRI performance evidence.

Screenshots are retained locally in `outputs/studio-desktop.jpg` and `outputs/studio-mobile.jpg`.
