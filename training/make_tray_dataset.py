"""Build a part-segmentation dataset (nut / bolt / washer) from one labelled camera view by rearranging its real parts.

  python training/make_tray_dataset.py --view data/raw/captures/tray0 --train 600 --val 100

`--view` holds mean.png (time-averaged camera frame) and masks.npz (types, masks: one per whole part). Cut-out parts are
rotated, scaled, re-lit and pasted onto mat texture taken from the same view. These are REARRANGED REAL PARTS, not
independent photos: the val split reuses the same parts, so its score only shows that training worked. Score on new
camera frames before quoting any accuracy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["nut", "bolt", "washer"]
W, H = 1280, 720


def complete_round(img, mask, box):
    """A washer cut off by the frame edge is completed with its own half turned by 180 degrees."""
    x1, y1, x2, y2 = box
    r = (x2 - x1) / 2
    cx, cy = (x1 + x2) / 2, y2 - r
    size = int(2 * r) + 8
    M = np.float32([[1, 0, size / 2 - cx], [0, 1, size / 2 - cy]])
    c, m = cv2.warpAffine(img, M, (size, size)), cv2.warpAffine(mask, M, (size, size))
    ok = cv2.warpAffine(np.full(mask.shape, 255, np.uint8), M, (size, size)) > 0
    c2, m2 = cv2.rotate(c, cv2.ROTATE_180), cv2.rotate(m, cv2.ROTATE_180)
    c[~ok], m[~ok] = c2[~ok], m2[~ok]
    return c, m


def load_parts(view: Path):
    img = cv2.imread(str(view / "mean.png"))
    z = np.load(view / "masks.npz")
    parts = []
    for t, m in zip(z["types"], z["masks"]):
        m = m.astype(np.uint8) * 255
        ys, xs = np.nonzero(m)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        if t == "washer" and box[1] == 0:
            c, mm = complete_round(img, m, box)
        else:
            x1, y1, x2, y2 = box
            c, mm = img[y1:y2, x1:x2].copy(), m[y1:y2, x1:x2].copy()
        parts.append((str(t), c, mm))
    allm = cv2.dilate((z["masks"].any(0) * 255).astype(np.uint8), np.ones((61, 61)))
    return img, allm, parts


def mat_patches(img, allm, rng, n=300, s=160):
    """Background squares that touch no part; also a few from the cluttered edge as distractors."""
    h, w = img.shape[:2]
    mat, edge = [], []
    for _ in range(20000):
        y, x = rng.integers(0, h - s), rng.integers(0, w - s)
        p = img[y:y + s, x:x + s]
        if x > 0.9 * w - s:
            edge.append(p)
        elif not allm[y:y + s, x:x + s].any() and p.mean() < 80 and p.std() < 22:
            mat.append(p)
        if len(mat) >= n:
            break
    return mat, edge


def background(mat, edge, rng):
    s = mat[0].shape[0]
    if rng.random() < 0.5:  # smooth base colour plus texture from one patch
        tile = np.tile(mat[rng.integers(len(mat))], (H // s + 2, W // s + 2, 1))[:H, :W]
        tile = cv2.GaussianBlur(tile, (0, 0), 0.8)
    else:
        tile = np.zeros((H, W, 3), np.uint8)
        for y in range(0, H, s):
            for x in range(0, W, s):
                p = mat[rng.integers(len(mat))]
                p = cv2.flip(p, int(rng.integers(-1, 2)))
                tile[y:y + s, x:x + s] = p[: min(s, H - y), : min(s, W - x)]
    bg = tile.astype(np.float32)
    gx, gy = rng.uniform(-30, 30, 2)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg += (gx * (xx / W - 0.5) + gy * (yy / H - 0.5))[..., None] + rng.uniform(-12, 25)
    for _ in range(rng.integers(0, 3)):  # distractors that are not parts
        if rng.random() < 0.5 and edge:
            p = cv2.resize(edge[rng.integers(len(edge))], (int(rng.integers(60, 260)), int(rng.integers(60, 700))))
            x = 0 if rng.random() < 0.5 else W - p.shape[1]
            y = int(rng.integers(0, max(1, H - p.shape[0])))
            bg[y:y + p.shape[0], x:x + p.shape[1]] = p[: H - y]
        else:
            col = tuple(float(v) for v in rng.integers(20, 230, 3))
            c = (int(rng.integers(0, W)), int(rng.integers(0, H)))
            ax = (int(rng.integers(20, 260)), int(rng.integers(10, 80)))
            cv2.ellipse(bg, c, ax, float(rng.uniform(0, 180)), 0, 360, col, -1, cv2.LINE_AA)
    return bg


def compose(parts, mat, edge, rng):
    img = background(mat, edge, rng)
    inst = np.zeros((H, W), np.int32)
    types, scale = [], rng.uniform(0.40, 0.95)
    by = {n: [p for p in parts if p[0] == n] for n in NAMES}
    for _ in range(int(rng.integers(0, 17))):
        t = NAMES[rng.choice(3, p=[0.5, 0.25, 0.25])]
        _, c, m = by[t][rng.integers(len(by[t]))]
        s = scale * rng.uniform(0.9, 1.1)
        h, w = m.shape
        d = int(np.hypot(h, w) * s) + 4
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(0, 360), s)
        M[:, 2] += (d / 2 - w / 2, d / 2 - h / 2)
        cc = cv2.warpAffine(c, M, (d, d), flags=cv2.INTER_AREA).astype(np.float32)
        mm = cv2.warpAffine(m, M, (d, d))
        if rng.random() < 0.5:
            cc, mm = cv2.flip(cc, 1), cv2.flip(mm, 1)
        if t == "washer" and rng.random() < 0.3:  # clean grey washer
            cc = np.repeat(cc.mean(2, keepdims=True), 3, 2) * rng.uniform(0.9, 1.3)
        cc = np.clip(cc * rng.uniform(0.75, 1.2) * rng.uniform(0.95, 1.05, 3), 0, 255)
        for _try in range(12):
            x, y = int(rng.integers(-d // 4, W - 3 * d // 4)), int(rng.integers(-d // 4, H - 3 * d // 4))
            X1, Y1, X2, Y2 = max(0, x), max(0, y), min(W, x + d), min(H, y + d)
            sub = mm[Y1 - y:Y2 - y, X1 - x:X2 - x] > 127
            if sub.sum() < 0.5 * (mm > 127).sum():
                continue
            if ((inst[Y1:Y2, X1:X2] > 0) & sub).sum() > 0.04 * sub.sum():
                continue
            sh = cv2.GaussianBlur(np.roll(mm, (6, 6), (0, 1)), (0, 0), 7).astype(np.float32) / 255 * rng.uniform(0, .6)
            img[Y1:Y2, X1:X2] *= 1 - sh[Y1 - y:Y2 - y, X1 - x:X2 - x, None] * (inst[Y1:Y2, X1:X2] == 0)[..., None]
            a = cv2.GaussianBlur(mm, (3, 3), 0).astype(np.float32)[Y1 - y:Y2 - y, X1 - x:X2 - x, None] / 255
            img[Y1:Y2, X1:X2] = img[Y1:Y2, X1:X2] * (1 - a) + cc[Y1 - y:Y2 - y, X1 - x:X2 - x] * a
            types.append(t)
            inst[Y1:Y2, X1:X2][sub] = len(types)
            break
    if rng.random() < 0.3:
        img = cv2.GaussianBlur(img, (0, 0), rng.uniform(0.4, 1.2))
    img = np.clip(img * rng.uniform(0.8, 1.2) + rng.normal(0, rng.uniform(1, 7), img.shape), 0, 255).astype(np.uint8)
    lines = []
    for i, t in enumerate(types, 1):
        cs, _ = cv2.findContours((inst == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cs:
            continue
        c = max(cs, key=cv2.contourArea)
        c = cv2.approxPolyDP(c, 1.2, True)[:, 0]
        if len(c) >= 4:
            lines.append(f"{NAMES.index(t)} " + " ".join(f"{px / W:.5f} {py / H:.5f}" for px, py in c))
    return img, lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--view", default="data/raw/captures/tray0")
    ap.add_argument("--out", default="data/datasets/tray_parts")
    ap.add_argument("--train", type=int, default=600)
    ap.add_argument("--val", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    img, allm, parts = load_parts(ROOT / a.view)
    mat, edge = mat_patches(img, allm, rng)
    out = ROOT / a.out
    for split, n in (("train", a.train), ("val", a.val)):
        for sub in ("images", "labels"):
            (out / sub / split).mkdir(parents=True, exist_ok=True)
        for i in range(n):
            im, lines = compose(parts, mat, edge, rng)
            cv2.imwrite(str(out / "images" / split / f"{split}{i:04d}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 92])
            (out / "labels" / split / f"{split}{i:04d}.txt").write_text("\n".join(lines))
    (out / "dataset.yaml").write_text(
        f"path: {out}\ntrain: images/train\nval: images/val\nnames: {json.dumps(dict(enumerate(NAMES)))}\n")
    print(f"{len(parts)} real parts, {len(mat)} mat patches -> {a.train}+{a.val} images in {out}")


if __name__ == "__main__":
    main()
