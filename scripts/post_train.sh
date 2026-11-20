#!/usr/bin/env bash
# After training: severity thresholds from training-data sizes, TensorRT FP16 engine + ONNX, test-set evaluation.
cd "$(dirname "$0")/.."
PROFILE=${PROFILE:-pcb}
PY=.venv/bin/python
set -ex
$PY training/calibrate_severity.py --profile "$PROFILE"
$PY training/export.py --profile "$PROFILE" --to both
$PY training/evaluate.py --profile "$PROFILE" --backend tensorrt --map
$PY training/evaluate.py --profile "$PROFILE" --backend onnxruntime
