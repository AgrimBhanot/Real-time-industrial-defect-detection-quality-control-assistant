#!/usr/bin/env bash
# Phase 1 on-device benchmark suite (run on the Jetson; for the final numbers turn Wi-Fi off first:
# scripts/offline_check.sh --go-offline). Results: bench/results/*.json, log: runs/logs/benchmarks.log
cd "$(dirname "$0")/.."
PY=.venv/bin/python
set -x
nvpmodel -q
$PY bench/bench_vision.py --backend tensorrt --frames 300
$PY bench/bench_vision.py --backend onnxruntime --frames 300
$PY bench/bench_llm.py --n 30 --set advisory.backend=executorch
$PY bench/bench_vision.py --backend tensorrt --frames 300 --with-llm --set advisory.backend=executorch
$PY bench/soak.py --units 1000 --set advisory.backend=executorch
