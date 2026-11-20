#!/usr/bin/env bash
# One-off: finish the ExecuTorch build, then resume the interrupted training (sequential = lower peak power).
cd "$(dirname "$0")/.."
tegrastats --interval 5000 --logfile runs/logs/tegrastats.log &
TS=$!
bash scripts/build_executorch_runner.sh > runs/logs/et_build.log 2>&1; echo "build rc=$?" >> runs/logs/jobs.log
.venv/bin/python training/train.py --profile pcb --resume runs/train/pcb/yolo11n_640_jetson/weights/last.pt \
  > runs/logs/train_pcb.log 2>&1; echo "train rc=$?" >> runs/logs/jobs.log
kill $TS
