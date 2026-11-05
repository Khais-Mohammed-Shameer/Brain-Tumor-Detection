# Science-fair demo guide

## Before the fair

Extract the portable ZIP and run its launcher on the actual demonstration computer. Check both reference examples, the attribution view, the Evidence page and a JSON export. Keep the server terminal open. The portable build has all runtime assets locally, so Internet access and a hosting account are unnecessary.

For the hosted build, visit once while connected, wait for **OFFLINE READY** in the footer, then test a reload without Internet access on that device. Browser caching can be cleared by the browser or an administrator; keep the portable folder as the dependable fallback. An initial hosted visit requires network access.

Use public demonstration images, and avoid putting real patient-identifying material into a public presentation.

## A five-minute walkthrough

1. **The question — 30 seconds.** Introduce the distinction between classifying one image and diagnosing a person. The experiment asks what patterns a small CNN uses and where it fails.
2. **The reference — 60 seconds.** Open Workspace and choose reference 01. Identify it as a source-dataset example. Explain the favored label and raw score without calling that score a disease probability.
3. **The actual input — 60 seconds.** Switch to Original, show crop bounds, then switch to Model input. Explain cropping, BGR order, 240 × 240 resizing and normalization. Zoom and display contrast change the view, not the prediction.
4. **The attribution — 45 seconds.** Compute Attribution. Explain that Grad-CAM shows model influence for the predicted class. It is not a tumor outline and cannot validate a diagnosis.
5. **The counterexample — 45 seconds.** Try a blank image or the noise fixture from the source project's tests. The quality gate rejects it before classification. Explain that simple checks still cannot identify every non-MRI image.
6. **The evidence — 60 seconds.** Open Evidence. Credit the source model and distinguish functional tests from independent accuracy. Explain the augmentation-before-splitting problem and the proposed corrected experiment. Export a research record to show reproducibility.

## Concepts to be able to explain

- A convolutional filter learns a spatial pattern; pooling reduces spatial resolution.
- One sigmoid output and a 0.5 threshold produce a binary label.
- The raw score, classification accuracy and calibration are different quantities.
- False negatives and false positives have different implications; a confusion matrix shows both.
- Data augmentation creates variants of existing images, not new independent patients.
- Related images must stay together when splitting. Augmentation belongs in the training subset.
- A model can be confidently wrong. A high score is not evidence that an unfamiliar input is valid.
- The app is newly rebuilt, while its shipped baseline weights come from the credited public project.

The strongest next addition is a documented independent dataset and a reproducible experiment. That evidence has not been invented or implied in this release.
