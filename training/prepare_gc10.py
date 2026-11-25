"""GC10-DET steel-sheet defects -> YOLO dataset, split BY COIL.

  python training/prepare_gc10.py --src ~/ps5-phase2-private/gc10/data_data

The common random 80/10/10 split puts neighbouring frames of one coil into train and test (file names carry the coil id
and frame number). Here whole coils go to one split and byte-identical images are dropped, so test coils are unseen.
GC10-DET has almost no defect-free images, so a false-reject rate cannot be measured on it.
"""
from __future__ import annotations

import argparse
import hashlib
import random
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["crease", "crescent_gap", "inclusion", "oil_spot", "punching_hole", "rolled_pit", "silk_spot",
         "waist_folding", "water_spot", "welding_line"]


def coil(stem: str) -> str:
    m = re.match(r"img_\d+_(\d+)_\d+", stem)
    return m.group(1) if m else stem


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="data/datasets/steel_sheet")
    ap.add_argument("--demo", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    src, out = Path(a.src).expanduser(), ROOT / a.out
    seen, groups = set(), defaultdict(list)
    n_dup = 0
    for img in sorted((src / "images").rglob("*.jpg")):
        h = hashlib.md5(img.read_bytes()).hexdigest()
        if h in seen:
            n_dup += 1
            continue
        seen.add(h)
        lbl = Path(str(img).replace("/images/", "/labels/")).with_suffix(".txt")
        if lbl.exists():
            groups[coil(img.stem)].append((img, lbl))
    # largest coils first, always to the split that is furthest below its target share (keeps every split varied)
    target = {"train": 0.7, "val": 0.15, "test": 0.15}
    count, assign = Counter(), {}
    order = sorted(groups)
    random.Random(a.seed).shuffle(order)
    order.sort(key=lambda g: -len(groups[g]))
    total = sum(len(v) for v in groups.values())
    for g in order:
        s = min(target, key=lambda k: count[k] / (target[k] * total))
        assign[g] = s
        count[s] += len(groups[g])
    boxes = defaultdict(Counter)
    for s in target:
        for sub in ("images", "labels"):
            shutil.rmtree(out / sub / s, ignore_errors=True)
            (out / sub / s).mkdir(parents=True)
    for g, items in groups.items():
        for img, lbl in items:
            s = assign[g]
            shutil.copy2(img, out / "images" / s / img.name)
            shutil.copy2(lbl, out / "labels" / s / lbl.name)
            boxes[s].update(NAMES[int(line.split()[0])] for line in lbl.read_text().splitlines() if line.strip())
    (out / "dataset.yaml").write_text(f"path: {out}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n"
                                      + "".join(f"  {i}: {n}\n" for i, n in enumerate(NAMES)))
    demo = ROOT / "data/demo/steel_sheet"
    shutil.rmtree(demo, ignore_errors=True)
    test = sorted((out / "images/test").glob("*.jpg"))
    for img in random.Random(a.seed).sample(test, min(a.demo, len(test))):
        for sub, f in (("images", img), ("labels", out / "labels/test" / f"{img.stem}.txt")):
            (demo / sub).mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, demo / sub / f.name)
    print(f"{n_dup} duplicate images dropped; {len(groups)} coils; images {dict(count)}")
    for s in target:
        print(s, dict(sorted(boxes[s].items())))


if __name__ == "__main__":
    main()
