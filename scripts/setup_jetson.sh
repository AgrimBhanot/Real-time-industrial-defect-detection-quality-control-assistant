#!/usr/bin/env bash
# One-time environment setup on the Jetson Orin Nano (JetPack 6 / L4T R36, CUDA 12.6, Python 3.10).
# Creates .venv inside the project; nothing outside the project folder is modified except apt packages.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/versions.env

echo "== [1/6] apt: TensorRT python bindings + trtexec, venv, build tools (sudo) =="
if [ "${SKIP_APT:-0}" != 1 ]; then
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-dev python3-pip python3-libnvinfer python3-libnvinfer-dev \
    libnvinfer-bin libopenblas-dev build-essential git cmake ninja-build cuda-cupti-12-6
  sudo ldconfig   # torch needs libcupti.so.12 on the loader path
fi

echo "== [2/6] .venv with system site-packages (TensorRT bindings + GStreamer-enabled OpenCV) =="
[ -d .venv ] || python3 -m venv --system-site-packages .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip wheel setuptools

echo "== [3/6] PyTorch + torchvision built for Jetson (CUDA 12.6) =="
# pinned: newer wheels on the index (2.10+) need libcudss, which JetPack 6 does not ship
pip install "numpy<2" $TORCH_SPEC --index-url "$JETSON_PYPI_INDEX" \
  || pip install "numpy<2" $TORCH_SPEC --index-url "${JETSON_PYPI_INDEX/.io/.dev}"

echo "== [4/6] project requirements =="
pip install "$ULTRALYTICS_SPEC" -r requirements/jetson.txt
pip install "numpy<2" $TORCH_SPEC --index-url "$JETSON_PYPI_INDEX"   # in case a dependency replaced torch

echo "== [5/6] onnxruntime-gpu for Jetson (optional backend) =="
pip install onnxruntime-gpu --index-url "$JETSON_PYPI_INDEX" \
  || echo "!! onnxruntime-gpu wheel not found; the onnxruntime backend will be unavailable/CPU-only"

echo "== [6/6] use system OpenCV (GStreamer, CSI camera) instead of pip wheels pulled in by ultralytics =="
pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python 2>/dev/null || true

python - <<'PY'
import torch, cv2
print("torch", torch.__version__, "cuda:", torch.cuda.is_available())
print("cv2", cv2.__version__, "gstreamer:", "GStreamer:                   YES" in cv2.getBuildInformation())
PY
python -m qc check || true
echo "done. activate with: source .venv/bin/activate"
