"""Train a YOLO detector for a profile. Runs the same on Colab/Kaggle (GPU) or on the Jetson.

  python training/train.py --profile pcb --model yolo11n.pt --epochs 100 --batch 32

Copies the best checkpoint to models/vision/<profile>/best.pt and writes model_card.json beside it.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Geometry-preserving augmentation: rotation/shear/perspective would change what a defect looks like
# (e.g. trace geometry on PCBs), so they are off. Flips are safe for both PCBs and fasteners.
AUG = dict(degrees=0.0, shear=0.0, perspective=0.0, translate=0.1, scale=0.3, fliplr=0.5, flipud=0.5,
           mosaic=1.0, close_mosaic=10, hsv_h=0.0, hsv_s=0.2, hsv_v=0.3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="pcb")
    ap.add_argument("--data", default=None, help="dataset.yaml (default data/datasets/<profile>/dataset.yaml)")
    ap.add_argument("--model", default="yolo11n.pt", help="yolo11n.pt (fastest) | yolo11s.pt (better on small defects)")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="0")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--patience", type=int, default=30)
    ap.add_argument("--name", default=None)
    ap.add_argument("--resume", default=None, help="path to an interrupted run's weights/last.pt")
    args = ap.parse_args()

    import torch
    import ultralytics
    from ultralytics import YOLO

    data = Path(args.data) if args.data else ROOT / f"data/datasets/{args.profile}/dataset.yaml"
    name = args.name or f"{Path(args.model).stem}_{args.imgsz}_{datetime.now():%m%d_%H%M}"
    if args.resume:  # continue an interrupted run with its original arguments
        model = YOLO(args.resume)
        results = model.train(resume=True)
    else:
        model = YOLO(args.model)
        results = model.train(data=str(data), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
                              device=args.device, workers=args.workers, patience=args.patience,
                              project=str(ROOT / "runs/train" / args.profile), name=name, seed=0, deterministic=True,
                              plots=True, **AUG)

    best = Path(model.trainer.best)
    dest = ROOT / "models/vision" / args.profile
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, dest / "best.pt")
    used = model.trainer.args  # actual run arguments: after --resume they differ from the CLI defaults
    card = {
        "profile": args.profile, "base_model": args.model, "data": str(used.data), "epochs": int(used.epochs),
        "imgsz": int(used.imgsz), "batch": int(used.batch), "augmentation": AUG, "run_dir": str(best.parent.parent),
        "trained_at": datetime.now().isoformat(timespec="seconds"), "platform": platform.machine(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "versions": {"ultralytics": ultralytics.__version__, "torch": torch.__version__},
        "val_metrics": {k: float(v) for k, v in getattr(results, "results_dict", {}).items()},
    }
    (dest / "model_card.json").write_text(json.dumps(card, indent=2))
    print(f"best.pt -> {dest / 'best.pt'}")
    print(json.dumps(card["val_metrics"], indent=2))


if __name__ == "__main__":
    main()
