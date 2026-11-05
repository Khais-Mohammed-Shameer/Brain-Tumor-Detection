# Reproducible research workflow

This toolkit is separate from the browser demo. It is ready to use when a documented dataset is supplied; it does not automatically download data or manufacture independent-performance claims.

Use Python 3.12 in a separate environment:

```sh
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements.txt
.venv/bin/python -m unittest discover -s research -p 'test_*.py' -v
```

Prepare a CSV with `path,label,group` columns, following `manifest.example.csv`. Paths are relative to the input CSV. Labels are `1` for tumor-labelled images and `0` for no-tumor-labelled images. Every image from one patient must share a group. If patient identifiers are unavailable, all variants of one original must share an image-family group, and patient independence must remain explicitly unverified. Review near-duplicates, source permissions, labels and provenance before creating splits.

```sh
.venv/bin/python research/workflow.py split research/input.csv research/frozen.csv --grouping patient
.venv/bin/python research/workflow.py train research/frozen.csv research/runs/experiment-01 --epochs 30
.venv/bin/python research/workflow.py evaluate research/frozen.csv research/runs/experiment-01
```

For image-family grouping use `--grouping original-image`. The splitter requires at least 10 groups and both labels in every subset. It approximates 70/15/15 at group level and searches for a reasonably balanced assignment, using a fixed seed. Actual image counts are reported; equal-sized groups are not assumed. It checks exact-byte duplicates, not all visual near-duplicates, and it cannot verify whether a supplied group ID represents a real patient.

Training uses a freshly initialized small CNN with dropout, deterministic seeds, training-only augmentation and validation-loss early stopping. Its input preparation matches the reference browser convention. The test set is not decoded or scored during training. The run stores the frozen manifest hash, training/validation group IDs and image hashes, model hash and training history.

Evaluation refuses a changed manifest or model, cross-split group/hash overlap, or overwriting a prior final test report. It produces the confusion matrix, accuracy, sensitivity, specificity, precision, F1, AUROC and 95% group-bootstrap percentile intervals. Very small test sets can yield uninformative intervals; a successful command is not evidence of adequate sample size. Do not use final test results to tune the experiment and then reuse that test set as independent evidence.

The shipped baseline has unknown historical split membership. Making new splits from its old dataset cannot turn it into an independent benchmark. Keep it as a demonstration baseline, or compare it only on a suitably new external dataset with clearly stated limitations.

The workflow was smoke-tested with 40 synthetic geometric images, a 28/6/6 split, one training epoch and held-out evaluation. This checks software plumbing only. Those images and model are excluded from the shipped app and publication.
