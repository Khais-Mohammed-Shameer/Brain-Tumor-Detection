"""Functional audit of the received project; does not modify received files.

Run from the project root with assessment/.venv/bin/python assessment/audit_runtime.py.
These are compatibility and behavior checks, not clinical performance tests.
"""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")

import cv2
import h5py
import numpy as np
from PIL import Image
import streamlit
from streamlit.testing.v1 import AppTest
import tensorflow as tf

ROOT = Path(__file__).resolve().parent
RECEIVED = ROOT / "received"
FIXTURES = ROOT / "audit-fixtures"
FIXTURES.mkdir(exist_ok=True)
os.chdir(RECEIVED)
source = (RECEIVED / "app.py").read_text()
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
function.decorator_list = []
namespace = {"tf": tf, "h5py": h5py}
exec(compile(ast.Module(body=[function], type_ignores=[]), "received_loader", "exec"), namespace)
model = namespace[function.name]()
result = {
    "scope": "Functional audit only; sample images are from the upstream project and are not an unseen test set.",
    "versions": {"tensorflow": tf.__version__, "keras": tf.keras.__version__,
                 "streamlit": streamlit.__version__, "opencv": cv2.__version__,
                 "numpy": np.__version__},
    "model": {"input_shape": list(model.input_shape), "output_shape": list(model.output_shape),
              "parameters": model.count_params()},
}

# Compare arrays directly, without deserializing arbitrary model classes.
legacy_path = RECEIVED / "models/cnn-parameters-improvement-23-0.91.model"
with h5py.File(legacy_path) as old, zipfile.ZipFile(RECEIVED / "models/care_keras3_model.keras") as archive:
    with h5py.File(io.BytesIO(archive.read("model.weights.h5"))) as converted:
        pairs = [
            ("conv0/conv0/kernel:0", "layers\\conv2d/vars/0"),
            ("conv0/conv0/bias:0", "layers\\conv2d/vars/1"),
            ("bn0/bn0/gamma:0", "layers\\batch_normalization/vars/0"),
            ("bn0/bn0/beta:0", "layers\\batch_normalization/vars/1"),
            ("bn0/bn0/moving_mean:0", "layers\\batch_normalization/vars/2"),
            ("bn0/bn0/moving_variance:0", "layers\\batch_normalization/vars/3"),
            ("fc/fc/kernel:0", "layers\\dense/vars/0"),
            ("fc/fc/bias:0", "layers\\dense/vars/1"),
        ]
        result["converted_weights_equal_legacy"] = {
            a: bool(np.array_equal(old["model_weights/" + a][:], converted[b][:])) for a, b in pairs
        }

try:
    tf.keras.models.load_model(RECEIVED / "models/care_keras3_model.keras", compile=False, safe_mode=True)
    result["converted_file_load"] = {"success": True}
except Exception as exc:
    result["converted_file_load"] = {"success": False, "error_type": type(exc).__name__, "error": str(exc)}

# Execute the actual preprocessing statements from the received app.
right_if = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and n.lineno == 129)
preprocess_nodes = [n for n in right_if.body if 146 <= n.lineno <= 168]
preprocess_code = compile(ast.Module(body=preprocess_nodes, type_ignores=[]), "received_preprocessing", "exec")

def preprocess(image):
    env = {"image": image, "np": np, "cv2": cv2}
    exec(preprocess_code, env)
    return env["img_reshaped"]

def upstream_preprocess(image):
    # Same effective steps as the pinned upstream notebook: BGR + cubic resize.
    a = np.array(image.convert("RGB"))[:, :, ::-1].copy()
    gray = cv2.GaussianBlur(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    mask = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
    mask = cv2.dilate(cv2.erode(mask, None, iterations=2), None, iterations=2)
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    if contours:
        c = max(contours, key=cv2.contourArea)
        left = int(c[c[:, :, 0].argmin()][0][0])
        right = int(c[c[:, :, 0].argmax()][0][0])
        top = int(c[c[:, :, 1].argmin()][0][1])
        bottom = int(c[c[:, :, 1].argmax()][0][1])
        if right > left and bottom > top:
            a = a[top:bottom, left:right]
    return (cv2.resize(a, (240, 240), interpolation=cv2.INTER_CUBIC) / 255.0)[None]

rng = np.random.default_rng(42)
images = {
    "black_non_mri": Image.new("RGB", (300, 300), "black"),
    "white_non_mri": Image.new("RGB", (300, 300), "white"),
    "random_noise_non_mri": Image.fromarray(rng.integers(0, 256, (300, 300, 3), dtype=np.uint8)),
}
manifest = json.loads((ROOT / "upstream/source-manifest.json").read_text())
for label, name in [("upstream_tumor_label", "yes/Y1.jpg"), ("upstream_no_tumor_label", "no/1 no.jpeg")]:
    url = f'https://raw.githubusercontent.com/MohamedAliHabib/Brain-Tumor-Detection/{manifest["commit"]}/' + urllib.parse.quote(name)
    path = FIXTURES / (label + Path(name).suffix)
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(url, timeout=30).read())
    images[label] = Image.open(path).copy()
    result.setdefault("fixture_sources", []).append({"file": str(path.relative_to(ROOT)), "url": url,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

result["inference_checks"] = []
for label, image in images.items():
    current = preprocess(image)
    historical = upstream_preprocess(image)
    output = float(model(current, training=False).numpy()[0, 0])
    historical_output = float(model(historical, training=False).numpy()[0, 0])
    result["inference_checks"].append({"input": label, "app_score": output,
        "app_label": "tumor" if output > 0.5 else "no_tumor", "upstream_preprocessing_score": historical_output,
        "max_input_tensor_difference": float(np.max(np.abs(current-historical)))})

# Exercise Streamlit using the unmodified received app in its expected working directory.
at = AppTest.from_file(str(RECEIVED / "app.py"), default_timeout=60).run()
result["streamlit_checks"] = {"startup_exceptions": [x.message for x in at.exception],
    "startup_errors": [x.value for x in at.error], "startup_success": [x.value for x in at.success]}
at.button[0].click().run()
result["streamlit_checks"]["missing_sample_button"] = {
    "selected_image": at.session_state["selected_image"],
    "errors": [x.value for x in at.error], "exceptions": [x.message for x in at.exception]}
at.session_state["selected_image"] = str(FIXTURES / "upstream_tumor_label.jpg")
at.run()
result["streamlit_checks"]["selected_sample"] = {
    "exceptions": [x.message for x in at.exception], "output": [x.value for x in at.info]}
black_path = FIXTURES / "black.png"
images["black_non_mri"].save(black_path)
at.session_state["selected_image"] = str(black_path)
at.run()
result["streamlit_checks"]["black_non_mri"] = {
    "exceptions": [x.message for x in at.exception], "output": [x.value for x in at.info]}
invalid_path = FIXTURES / "invalid.png"
invalid_path.write_text("This is not an image.")
at.session_state["selected_image"] = str(invalid_path)
at.run()
result["streamlit_checks"]["invalid_image"] = {
    "exceptions": [x.message for x in at.exception], "errors": [x.value for x in at.error]}

(ROOT / "runtime-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "converted_file_load"}, indent=2))
print("Converted artifact loads:", result["converted_file_load"]["success"])
print("Full results:", ROOT / "runtime-audit.json")
