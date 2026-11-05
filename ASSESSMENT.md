# C.A.R.E. — initial project assessment

Assessed 5 November 2026. Scope: the three supplied files only, plus a pinned copy of their identified public source for comparison. Further files may change the recommendation. The original files in Downloads were not changed. No rebuild has been started.

**Recommendation: keep the idea and the existing model as a baseline; rebuild the application and experimental workflow cleanly.** Repairing the interface is feasible, but it would leave the more important questions about data, evaluation and the meaning of the results unanswered. “Rebuild” here does not mean that training a large neural network from random weights is necessary.

## What is actually here

| Received item | Actual role | Finding |
| --- | --- | --- |
| `app.py` | A Streamlit interface that accepts JPG/PNG images, preprocesses them and runs a binary classifier | Runs in the isolated audit environment. It does not train a model. |
| `convert.py` | Reconstructs the network and transfers existing saved weights into another file format | Conversion only. It does not create a newly trained or improved model. |
| `models.zip` | 22 historical training checkpoints, one duplicate best-model file and one converted model | 24 model artifacts in total. These are not 24 independently developed systems. |

The processing path is:

`image → threshold-based crop → 240 × 240 resize → divide by 255 → CNN → score → threshold at 0.5`

The network has one convolutional layer, batch normalization, ReLU, two pooling layers and a final binary output: 11,137 parameters in total. Its output describes a whole image. The supplied implementation does not locate or outline a tumor, identify its type or stage, process a complete 3D MRI study, or establish a person's diagnosis.

## Provenance is verified

All **22 checkpoint files match the corresponding files in MohamedAliHabib/Brain-Tumor-Detection exactly**. This was checked using their Git blob hashes at commit `30470ae8eb2e4a523df7dc45dd5323903cb98365`; the selected checkpoint was additionally downloaded and compared byte for byte using SHA-256.

`cnn_best_model.h5` is byte-for-byte identical to `cnn-parameters-improvement-23-0.91.model`. All eight saved weight arrays in `care_keras3_model.keras` are exactly equal to those in that checkpoint. The original model metadata identifies Keras `2.1.6-tf`.

This establishes the origin of the supplied weights. It does not establish who wrote the wrapper, what your brother understands, or whether he has other experiments that have not been sent. Nothing supplied so far demonstrates his own model training. Reusing the public model with clear attribution can still support a useful project; the student's contribution needs to be identifiable.

Evidence: [model provenance](assessment/model-provenance.json), [model inspection](assessment/model-inspection.json), [pinned source manifest](assessment/upstream/source-manifest.json). Public source: [original repository](https://github.com/MohamedAliHabib/Brain-Tumor-Detection/tree/30470ae8eb2e4a523df7dc45dd5323903cb98365). The upstream repository includes an Apache 2.0 license; the image dataset's terms and provenance need a separate check before reuse or redistribution.

## What works, and what fails

The unchanged app starts successfully when launched from a directory containing its expected `models/` folder. Its manual weight mapping works in the tested environment. Two images fetched separately from the pinned public repository produced the expected dataset labels. Those images were audit fixtures, not part of the brother's delivery and not an independent test set.

| Audit input | Current app pipeline result | Interpretation |
| --- | --- | --- |
| Source repository image labelled tumor | Tumor score 99.93% | Functional example only; potentially familiar training data |
| Source repository image labelled no tumor | No-tumor score 99.29% | Functional example only; potentially familiar training data |
| Completely black image | No-tumor score 86.61% | Blank input receives a confident classification |
| Completely white image | No-tumor score 98.38% | Blank input receives a confident classification |
| Random RGB noise, seed 42 | Tumor score 99.99% | Meaningless input receives a confident classification |

These observations demonstrate missing input checks and overconfident behavior on unsuitable inputs. They do not estimate MRI sensitivity, specificity or overall accuracy. A future input gate can reject clearly invalid files and blanks, but rejecting all non-MRI or unfamiliar images is a separate problem that also needs evaluation.

Other confirmed problems:

- **Misleading result wording.** `app.py:177–182` presents the raw sigmoid output as a probability of abnormal tissue or healthy scans. No calibration or independent evidence supporting that interpretation is supplied. “No tumor predicted in this image” also cannot establish that a person is healthy. See [probability calibration guidance](https://scikit-learn.org/stable/modules/calibration.html).
- **Preprocessing differs from training.** The source notebook uses OpenCV's BGR channel order and cubic resizing; the app uses RGB and default linear resizing (`app.py:146–168`). Channel order is immaterial for perfectly grayscale images, but not necessarily for colored images or annotations. The resize difference changed the processed tensors and scores of both MRI fixtures. Neither fixture changed class, so this audit does not claim a measured accuracy loss. Compare the [original training notebook](https://github.com/MohamedAliHabib/Brain-Tumor-Detection/blob/30470ae8eb2e4a523df7dc45dd5323903cb98365/Brain%20Tumor%20Detection.ipynb).
- **Sample buttons have no supplied samples.** The required `yes/` and `no/` image folders are absent. Clicking the first sample button silently leaves the selection empty. `os.walk(...)` is a generator and does not test whether a folder exists (`app.py:97–111`).
- **An active upload overrides sample selection.** The uploader's value is assigned after the sample-button handlers on every rerun (`app.py:118–119`). This follows from code inspection; the browser upload interaction was not exercised.
- **Unreadable images raise an unhandled exception.** A text file named `.png` reaches `Image.open` and fails instead of producing a useful validation message (`app.py:123`). The programmatic app check reproduced this path.
- **The converted file is not a portable Keras 3 artifact as named.** Its metadata says Keras `2.21.0`, its configuration references `tf_keras`, and ordinary safe loading failed under Keras `3.15.1`. The converter explicitly enables legacy Keras (`convert.py:2`). The app bypasses this converted file and loads the old checkpoint directly, so this does not prevent the current app from starting.
- **The progress display is simulated.** Its timed stages, including “evaluation finished,” run before preprocessing and inference (`app.py:133–143`). They are not measurements of actual processing stages.
- **The delivery is not reproducible yet.** There is no dependency file, setup guide, training code, evaluation code, dataset manifest or saved split assignment. Model paths depend on the process working directory.

## The largest scientific weakness

The identified source experiment generates augmented images first, combines them with the originals, and then randomly splits that combined pool into training, validation and test sets. There is no grouping by original image or patient in the split code.

**Inference from the source code:** variations of the same original can land in both training and evaluation sets, allowing the model to be tested on images closely related to ones it has already seen. This is a serious leakage risk. The saved split membership is unavailable, so the exact historical overlap and its effect on accuracy have not been measured here. Patient independence is also unverified.

The source repository reports 91% validation accuracy and approximately 89% test accuracy. The `0.91` in the selected filename refers to the source experiment's validation result; it is not verified accuracy for this app, new images, or patients. Sources: [augmentation notebook](https://github.com/MohamedAliHabib/Brain-Tumor-Detection/blob/30470ae8eb2e4a523df7dc45dd5323903cb98365/Data%20Augmentation.ipynb), [training notebook](https://github.com/MohamedAliHabib/Brain-Tumor-Detection/blob/30470ae8eb2e4a523df7dc45dd5323903cb98365/Brain%20Tumor%20Detection.ipynb), [source results](https://github.com/MohamedAliHabib/Brain-Tumor-Detection/tree/30470ae8eb2e4a523df7dc45dd5323903cb98365), and [data-leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).

For a new experiment, split independent originals before augmentation, group by patient where trustworthy identifiers exist, keep related images together, and augment training data only. If patient identifiers cannot be recovered, state that limitation explicitly. The existing pretrained model cannot become an independent benchmark merely by making a new split of its original dataset: it may already have seen those images or their relatives.

## A stronger direction for the science fair

Use a question such as: **“How reliably can an image classifier distinguish tumor-labelled brain MRI images, and when does it fail?”**

1. **Establish the data first.** Record source, permissions, labels, duplicates, patient identifiers where available and fixed split membership. Select the dataset after checking the remaining material and available time and hardware.
2. **Run a defensible comparison.** Keep the inherited CNN as a clearly credited baseline. Compare a newly trained small model or a suitable pretrained feature extractor on the same independently held-out data. Choose model size for the available compute; a larger network alone is not evidence of improvement.
3. **Measure useful outcomes.** Report the confusion matrix, sensitivity/recall, specificity, precision, F1, sample counts and uncertainty. Choose thresholds using validation data; reserve the final test set for evaluation. Include false negatives and false positives in the presentation.
4. **Make the demo explain its work.** Show the original image, actual crop and processed model input, model version, score and measured processing time. Reject clear input failures and communicate uncertainty. Any later heatmap must be described as a model attribution view, not a proven tumor boundary.
5. **Make the student's contribution visible.** Provide a reproducible experiment, documented decisions, failure analysis, source credits and an explanation your brother can present and defend. A distinctive contribution could investigate the effects of cropping, resizing or image degradation rather than merely attaching a new interface to downloaded weights.

The current app is small enough to replace cleanly. Keep the concept, credited reference weights and any useful visual ideas. Replace duplicated architecture definitions, format workarounds, simulated progress and unsupported diagnostic language with one tested inference pipeline and an experiment that supports the claims being shown.

## Audit record and remaining unknowns

Both Python files pass syntax compilation. Runtime checks used Python 3.12.12, TensorFlow 2.21.0, Keras 3.15.1, Streamlit 1.66.1 and OpenCV 5.0.0 in an isolated environment. Programmatic Streamlit checks covered startup, the missing sample button, a selected MRI fixture, a blank image and an invalid image. Full browser upload behavior, deployment, performance on an independent dataset and clinical validity were not tested.

Reproduce the functional audit from the project root with:

```sh
assessment/.venv/bin/python assessment/audit_runtime.py
```

The audit requires network access only if its two source image fixtures are absent. Detailed observations are in [runtime-audit.json](assessment/runtime-audit.json); the script is [audit_runtime.py](assessment/audit_runtime.py), and the installed environment is recorded in [audit-environment.txt](assessment/audit-environment.txt). Input hashes are in [received-manifest.json](assessment/received-manifest.json). Downloaded reference code and models are separated under `assessment/upstream/`; audit images are under `assessment/audit-fixtures/`, and received copies are under `assessment/received/`.

Still needed before deciding the final build: remaining files, dataset or dataset link, any training notebooks, the school brief/rubric, deadline, demonstration computer and offline requirements. The brother's grade is 11; the assessment and recommended standards are based on the project goals, not a reduced expectation for his age.
