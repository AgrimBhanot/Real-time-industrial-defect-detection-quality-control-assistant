"""Industrial metal parts: MVTec AD (metal nut, screw) + MPDD (brackets, connectors, tubes, plates) -> one YOLO dataset.

  python training/prepare_metal_parts.py --mpdd ~/ps5-phase2-private/mpdd/MPDD

MVTec images keep the split already used by data/datasets/mvtec_fasteners (its test split stays unseen by training).
MPDD has no defective training images, so its test images are divided 60/20/20 per defect type in CONTIGUOUS blocks of
file numbers: neighbouring shots often show the same piece, and a random split would leak it. Boxes are the bounding
boxes of mask regions. Both datasets are CC BY-NC-SA 4.0 (non-commercial); images are not redistributed here.
"""
from __future__ import annotations

import argparse
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["tip_damage", "scratch", "thread_damage", "deformation", "discolouration", "flipped", "rust", "hole",
         "paint_defect", "mismatch"]
MVTEC = ["tip_damage", "scratch", "thread_damage", "deformation", "discolouration", "flipped"]  # bent -> deformation
MPDD = {"scratches": "scratch", "hole": "hole", "defective_painting": "paint_defect", "anomalous": "deformation",
        "parts_mismatch": "mismatch", "bend_and_parts_mismatch": "mismatch", "major_rust": "rust", "total_rust": "rust"}


def boxes_from_mask(mask: np.ndarray, min_frac: float = 0.00003, join: int = 15) -> list:
    h, w = mask.shape
    m = cv2.dilate((mask > 0).astype(np.uint8), np.ones((join, join)))
    n, _, st, _ = cv2.connectedComponentsWithStats(m)
    out = []
    for i in range(1, n):
        x, y, bw, bh, _ = st[i]
        ys, xs = np.nonzero(mask[y:y + bh, x:x + bw])
        if len(xs) < min_frac * w * h:
            continue
        x1, x2, y1, y2 = x + xs.min(), x + xs.max() + 1, y + ys.min(), y + ys.max() + 1
        out.append(((x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mpdd", required=True)
    ap.add_argument("--mvtec", default="data/datasets/mvtec_fasteners", help="output of prepare_mvtec.py")
    ap.add_argument("--out", default="data/datasets/metal_parts")
    ap.add_argument("--repeat", type=int, default=4, help="times each defective MPDD training image is listed")
    ap.add_argument("--good-per-part", type=int, default=45, help="MPDD good training images kept per product")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out, mv, mp = ROOT / a.out, ROOT / a.mvtec, Path(a.mpdd).expanduser()
    shutil.rmtree(out, ignore_errors=True)
    n_img, n_box = Counter(), defaultdict(Counter)

    def put(img: Path, lines: list, split: str, name: str, repeat: int = 1):
        for k in range(repeat):
            stem = f"{name}_r{k}" if k else name
            for sub in ("images", "labels"):
                (out / sub / split).mkdir(parents=True, exist_ok=True)
            shutil.copy2(img, out / "images" / split / f"{stem}{img.suffix}")
            (out / "labels" / split / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
        n_img[split] += 1
        n_box[split].update(NAMES[int(x.split()[0])] for x in lines)

    for split in ("train", "val", "test", "test_clean"):  # training repeats are already files here
        for img in sorted((mv / "images" / split).iterdir()):
            lbl = mv / "labels" / split / f"{img.stem}.txt"
            lines = []
            for line in lbl.read_text().splitlines() if lbl.exists() else []:
                c, rest = line.split(" ", 1)
                lines.append(f"{NAMES.index(MVTEC[int(c)])} {rest}")
            put(img, lines, split, f"mvtec_{img.stem}")

    for prod in sorted(p for p in mp.iterdir() if p.is_dir()):
        goods = sorted((prod / "train/good").iterdir())
        for img in rng.sample(goods, min(a.good_per_part, len(goods))):
            put(img, [], "train", f"mpdd_{prod.name}_good_{img.stem}")
        for d in sorted((prod / "test").iterdir()):
            files = sorted(d.iterdir())
            n = len(files)
            for i, img in enumerate(files):
                split = "train" if i < 0.6 * n else "val" if i < 0.8 * n else "test"
                lines = []
                if d.name != "good":
                    gt = next((prod / "ground_truth" / d.name).glob(f"{img.stem}_mask.*"), None)
                    mask = cv2.imread(str(gt), 0) if gt else None
                    shape = cv2.imread(str(img)).shape[:2]
                    if mask is None or mask.shape != shape:
                        print("skip (mask)", img)
                        continue
                    cls = NAMES.index(MPDD[d.name])
                    bxs = boxes_from_mask(mask)
                    if not bxs:
                        print("skip (empty mask)", img)
                        continue
                    lines = [f"{cls} " + " ".join(f"{v:.6f}" for v in b) for b in bxs]
                s = "test_clean" if split == "test" and not lines else split
                put(img, lines, s, f"mpdd_{prod.name}_{d.name}_{img.stem}", a.repeat if split == "train" and lines else 1)
    (out / "dataset.yaml").write_text(f"path: {out}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n"
                                      + "".join(f"  {i}: {n}\n" for i, n in enumerate(NAMES)))
    demo = ROOT / "data/demo/metal_parts"  # held-out images only
    shutil.rmtree(demo, ignore_errors=True)
    for sub in ("images", "labels"):
        (demo / sub).mkdir(parents=True)
        for s in ("test", "test_clean"):
            for f in (out / sub / s).iterdir():
                shutil.copy2(f, demo / sub / f.name)
    print(dict(n_img))
    for s in ("train", "val", "test"):
        print(s, "boxes", dict(n_box[s]))


if __name__ == "__main__":
    main()
