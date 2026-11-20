"""Export best.pt for the on-device runtimes.

  python training/export.py --profile pcb --to onnx     # anywhere (Colab or Jetson)
  python training/export.py --profile pcb --to engine   # ON THE JETSON ONLY: TensorRT engines are tied to the
                                                        # GPU + TensorRT version they were built with
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="pcb")
    ap.add_argument("--weights", default=None)
    ap.add_argument("--to", choices=["onnx", "engine", "both"], default="onnx")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--fp32", action="store_true", help="engine: FP32 instead of FP16")
    ap.add_argument("--int8", action="store_true", help="engine: INT8 with calibration on the dataset")
    ap.add_argument("--workspace", type=float, default=2.0, help="engine: TensorRT workspace GiB")
    args = ap.parse_args()

    from ultralytics import YOLO

    weights = Path(args.weights) if args.weights else ROOT / f"models/vision/{args.profile}/best.pt"
    dest = ROOT / f"models/vision/{args.profile}"
    dest.mkdir(parents=True, exist_ok=True)
    # engine first: a CPU ONNX export makes Ultralytics set CUDA_VISIBLE_DEVICES=-1 for the rest of the process
    targets = ["engine", "onnx"] if args.to == "both" else [args.to]
    for fmt in targets:
        model = YOLO(str(weights))
        kw = dict(format=fmt, imgsz=args.imgsz)
        if fmt == "onnx":
            kw.update(opset=17, simplify=True, dynamic=False)
        else:
            kw.update(device=0, half=not args.fp32 and not args.int8, int8=args.int8, workspace=args.workspace)
            if args.int8:
                kw["data"] = str(ROOT / f"data/datasets/{args.profile}/dataset.yaml")
        out = Path(model.export(**kw))
        final = dest / f"best{out.suffix}"
        if out.resolve() != final.resolve():
            shutil.copy2(out, final)
        print(f"{fmt}: {final}")


if __name__ == "__main__":
    main()
