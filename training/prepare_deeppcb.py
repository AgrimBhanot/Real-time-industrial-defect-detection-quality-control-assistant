"""DeepPCB -> YOLO dataset (group-level train/val split, official test split, optional clean templates).

  python training/prepare_deeppcb.py --download --templates --demo 200

Output:
  data/datasets/pcb/images/{train,val,test,test_clean}  + labels/...  + dataset.yaml
  data/demo/pcb/images + labels   (random real test images for the simulated conveyor)
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_profile  # noqa: E402

REPO = "https://github.com/tangsanli5201/DeepPCB.git"


def read_list(path: Path) -> list[tuple[str, str]]:
    pairs = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            pairs.append((parts[0], parts[1]))
    return pairs


def to_yolo(ann: Path, w: int, h: int) -> list[str]:
    rows = []
    for line in ann.read_text().splitlines():
        vals = [v for v in re.split(r"[,\s]+", line.strip()) if v]
        if len(vals) < 5:
            continue
        x1, y1, x2, y2, t = (int(float(v)) for v in vals[:5])
        x1, x2 = sorted((max(0, x1), min(w, x2)))
        y1, y2 = sorted((max(0, y1), min(h, y2)))
        if x2 <= x1 or y2 <= y1:
            continue
        rows.append(f"{t - 1} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}")
    return rows


def emit(img: Path, rows: list[str], out: Path, split: str, stem: str) -> None:
    (out / "images" / split).mkdir(parents=True, exist_ok=True)
    (out / "labels" / split).mkdir(parents=True, exist_ok=True)
    shutil.copy2(img, out / "images" / split / f"{stem}.jpg")
    (out / "labels" / split / f"{stem}.txt").write_text("\n".join(rows) + ("\n" if rows else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default="data/raw/DeepPCB", help="DeepPCB repo checkout")
    ap.add_argument("--out", default="data/datasets/pcb")
    ap.add_argument("--download", action="store_true", help="git clone DeepPCB into --src if missing")
    ap.add_argument("--val-frac", type=float, default=0.15)
    ap.add_argument("--val-groups", nargs="+", default=None, help="explicit board groups for val")
    ap.add_argument("--templates", action="store_true", help="add defect-free templates as negatives + test_clean")
    ap.add_argument("--demo", type=int, default=200, help="test images copied to data/demo/pcb (0 = none)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    src, out = ROOT / args.src, ROOT / args.out
    if not (src / "PCBData").exists():
        if not args.download:
            sys.exit(f"{src}/PCBData not found; re-run with --download")
        src.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPO, str(src)], check=True)
    data = src / "PCBData"
    if out.exists():
        shutil.rmtree(out)

    trainval, test = read_list(data / "trainval.txt"), read_list(data / "test.txt")
    groups = sorted({p.split("/")[0] for p, _ in trainval})
    rng = random.Random(args.seed)
    rng.shuffle(groups)
    # Groups differ a lot in size, so fill val by image count, not by number of groups.
    if args.val_groups:
        val_groups = set(args.val_groups)
        if val_groups - set(groups):
            sys.exit(f"unknown val groups: {sorted(val_groups - set(groups))}; choose from {groups}")
    else:
        target, n_imgs, val_groups = args.val_frac * len(trainval), 0, set()
        for g in groups:
            size = sum(p.split("/")[0] == g for p, _ in trainval)
            if n_imgs + size <= 1.2 * target:
                val_groups.add(g)
                n_imgs += size
            if n_imgs >= target:
                break
    if not val_groups or val_groups == set(groups):
        sys.exit("the val split needs at least one group and must leave at least one for training")
    group_of: dict[str, str] = {}

    counts: dict[str, int] = {}
    for pairs, default_split in ((trainval, None), (test, "test")):
        for img_rel, ann_rel in pairs:
            group = img_rel.split("/")[0]
            split = default_split or ("val" if group in val_groups else "train")
            img = data / img_rel.replace(".jpg", "_test.jpg")
            tmpl = data / img_rel.replace(".jpg", "_temp.jpg")
            ann = data / ann_rel
            if not img.exists() or not ann.exists():
                continue
            h, w = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE).shape[:2]
            stem = Path(img_rel).stem
            group_of[stem] = group
            emit(img, to_yolo(ann, w, h), out, split, stem)
            counts[split] = counts.get(split, 0) + 1
            if args.templates and tmpl.exists():
                tsplit = "test_clean" if split == "test" else split
                emit(tmpl, [], out, tsplit, f"{stem}_temp")
                counts[tsplit] = counts.get(tsplit, 0) + 1

    names = load_profile("pcb")["classes"]
    (out / "dataset.yaml").write_text(yaml.safe_dump({
        "path": str(out), "train": "images/train", "val": "images/val", "test": "images/test",
        "names": dict(enumerate(names)),
    }, sort_keys=False))
    # The official test list shares most groups with trainval; evaluate.py reports seen/unseen groups separately.
    (out / "groups.json").write_text(json.dumps({
        "train_groups": sorted(set(groups) - val_groups), "val_groups": sorted(val_groups), "group_of": group_of,
    }, indent=1))
    print("images per split:", counts)
    print(f"val groups: {sorted(val_groups)}")

    if args.demo:
        demo = ROOT / "data/demo/pcb"
        if demo.exists():
            shutil.rmtree(demo)
        (demo / "images").mkdir(parents=True)
        (demo / "labels").mkdir(parents=True)
        pool = sorted((out / "images/test").glob("*.jpg"))
        if args.templates:
            pool += sorted((out / "images/test_clean").glob("*.jpg"))[: len(pool) // 5]
        for p in rng.sample(pool, min(args.demo, len(pool))):
            shutil.copy2(p, demo / "images" / p.name)
            lbl = out / "labels" / p.parent.name / f"{p.stem}.txt"
            shutil.copy2(lbl, demo / "labels" / lbl.name)
        print(f"demo conveyor set: {demo} ({len(list((demo / 'images').glob('*.jpg')))} images)")
    print(f"dataset yaml: {out / 'dataset.yaml'}")


if __name__ == "__main__":
    main()
