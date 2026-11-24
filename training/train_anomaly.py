"""Build the good-parts-only anomaly detector.

  python training/train_anomaly.py --profile mvtec_fasteners --backbone resnet18 --size 384

Uses only images with an EMPTY label file from the train split: 80% (by part, when groups.json exists) fill the memory
bank, 20% set the threshold (mean + k*std per product). The validation split is then scored; test is never opened.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.sources import IMAGE_EXTS, label_for  # noqa: E402


def product_of(stem: str) -> str:
    """MVTec images carry their product; own captures (<part>__<condition>__...) are one product."""
    return stem.split("_good_")[0] if "__" not in stem and "_good_" in stem else "part"


def is_good(p: Path) -> bool:
    if "__" in p.stem and p.stem.split("__")[1] != "good":
        return False  # damaged part seen from its good side: empty label, but not a good part
    lbl = label_for(p)
    return lbl is not None and not lbl.read_text().strip()


def split_good(files: list[Path], group_of: dict, seed: int = 0, calib: float = 0.2) -> tuple[list, list]:
    """Whole groups (physical parts) go to bank or calibration, per product; ungrouped images are their own group."""
    rng, bank, cal = random.Random(seed), [], []
    by_prod: dict = {}
    for p in sorted(files):
        by_prod.setdefault(product_of(p.stem), {}).setdefault(group_of.get(p.stem, p.stem), []).append(p)
    for groups in by_prod.values():
        keys = sorted(groups)
        rng.shuffle(keys)
        n = max(1, round(calib * len(keys)))
        for i, k in enumerate(keys):
            (cal if i < n else bank).extend(groups[k])
    return bank, cal


def auroc(good, bad) -> float:
    g, b = np.asarray(good)[None], np.asarray(bad)[:, None]
    return float(((b > g) + 0.5 * (b == g)).mean())


class Features(nn.Module):
    def __init__(self, name: str):
        super().__init__()
        import torchvision

        weights = {"resnet18": "IMAGENET1K_V1", "wide_resnet50_2": "IMAGENET1K_V1"}[name]
        m = getattr(torchvision.models, name)(weights=weights)
        self.stem = nn.Sequential(m.conv1, m.bn1, m.relu, m.maxpool, m.layer1)
        self.l2, self.l3 = m.layer2, m.layer3
        self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, bgr):
        x = (bgr.flip(1) / 255.0 - self.mean) / self.std
        a = self.l2(self.stem(x))
        b = self.l3(a)
        a, b = F.avg_pool2d(a, 3, 1, 1), F.avg_pool2d(b, 3, 1, 1)
        f = torch.cat([a, F.interpolate(b, size=a.shape[-2:], mode="bilinear")], 1)
        return F.normalize(f, dim=1)  # unit vectors: distances stay well-scaled in fp16


class Net(nn.Module):
    def __init__(self, feats: Features, bank: torch.Tensor, tag: torch.Tensor, n_products: int):
        super().__init__()
        self.feats = feats
        self.register_buffer("bank", bank.t().contiguous())
        self.register_buffer("onehot", F.one_hot(tag, n_products).float())

    def forward(self, bgr):
        f = self.feats(bgr)
        h, w = f.shape[-2:]
        sim, idx = (f[0].flatten(1).t() @ self.bank).max(1)
        d = (2.0 - 2.0 * sim).clamp(min=0.0).sqrt()
        amap = F.avg_pool2d(d.view(1, 1, h, w), 3, 1, 1, count_include_pad=False)[0, 0]
        return amap, self.onehot[idx].mean(0)


def coreset(x: torch.Tensor, n: int, pool: int, seed: int = 0) -> torch.Tensor:
    """Indices of a greedy k-centre subset (on a 128-d random projection of at most `pool` vectors)."""
    g = torch.Generator().manual_seed(seed)
    cand = torch.randperm(len(x), generator=g)[:pool]
    proj = torch.randn(x.shape[1], 128, generator=g) / 128 ** 0.5
    z = (x[cand].float() @ proj).cuda()
    best = torch.full((len(z),), float("inf"), device="cuda")
    pick, i = [], 0
    for _ in range(min(n, len(z))):
        pick.append(i)
        best = torch.minimum(best, ((z - z[i]) ** 2).sum(1))
        i = int(best.argmax())
    return cand[torch.tensor(pick)]


def load(p: Path, size: int) -> np.ndarray:
    return cv2.resize(cv2.imread(str(p)), (size, size), interpolation=cv2.INTER_AREA)


def rotations(img: np.ndarray, n: int) -> list[np.ndarray]:
    h, w = img.shape[:2]
    out = [img]
    for k in range(1, n):
        m = cv2.getRotationMatrix2D(((w - 1) / 2, (h - 1) / 2), 360 * k / n, 1)
        out.append(cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="mvtec_fasteners")
    ap.add_argument("--backbone", default="resnet18", choices=["resnet18", "wide_resnet50_2"])
    ap.add_argument("--size", type=int, default=384)
    ap.add_argument("--bank", type=int, default=8000, help="memory bank vectors per product")
    ap.add_argument("--rot", type=int, default=1, help="rotated copies of each bank image")
    ap.add_argument("--k", type=float, default=3.0, help="threshold = mean + k*std of unseen good parts")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None, help="default models/vision/<profile>")
    a = ap.parse_args()
    ds = ROOT / f"data/datasets/{a.profile}"
    files = lambda s: sorted(p for p in (ds / "images" / s).glob("*") if p.suffix.lower() in IMAGE_EXTS)  # noqa: E731
    gf = ds / "groups.json"
    bank_f, cal_f = split_good([p for p in files("train") if is_good(p)],
                               json.loads(gf.read_text())["group_of"] if gf.exists() else {}, a.seed)
    if len(bank_f) < 10 or len(cal_f) < 5:
        sys.exit(f"too few good images: {len(bank_f)} bank, {len(cal_f)} calibration")
    products = sorted({product_of(p.stem) for p in bank_f})
    feats = Features(a.backbone).eval().cuda()
    banks, tags = [], []
    with torch.inference_mode():
        for k, prod in enumerate(products):
            xs = []
            mine = [p for p in bank_f if product_of(p.stem) == prod]
            g = torch.Generator().manual_seed(a.seed)
            per = max(50, 250_000 // (len(mine) * a.rot))
            for p in mine:
                for im in rotations(load(p, a.size), a.rot):
                    f = feats(torch.from_numpy(im).cuda().permute(2, 0, 1)[None].float())[0].flatten(1).t().half().cpu()
                    xs.append(f[torch.randperm(len(f), generator=g)[:per]])
            x = torch.cat(xs)
            b = x[coreset(x, a.bank, 200_000, a.seed)].float()
            banks.append(b)
            tags.append(torch.full((len(b),), k))
    out = Path(a.out) if a.out else ROOT / f"models/vision/{a.profile}"
    out.mkdir(parents=True, exist_ok=True)
    net = Net(feats, torch.cat(banks).cuda(), torch.cat(tags).cuda(), len(products)).eval().cuda()
    with torch.inference_mode():
        ts = torch.jit.trace(net, torch.zeros(1, 3, a.size, a.size).cuda())
    ts.save(str(out / "anomaly.pt"))
    meta = {"profile": a.profile, "backbone": a.backbone, "size": a.size, "bank_per_product": a.bank, "rot": a.rot,
            "k": a.k, "seed": a.seed, "products": products, "thresholds": {p: 0.0 for p in products},
            "n_bank_images": len(bank_f), "n_calibration_images": len(cal_f)}
    (out / "anomaly.json").write_text(json.dumps(meta))

    from qc.vision.anomaly import AnomalyModel

    m = AnomalyModel(out)  # thresholds come from the same code and precision the line uses
    cal: dict = {p: [] for p in products}
    for p in cal_f:
        cal[product_of(p.stem)].append(m.score(cv2.imread(str(p)))[0])
    meta["thresholds"] = {p: float(np.mean(v) + a.k * np.std(v, ddof=1)) for p, v in cal.items()}
    meta["built_at"] = datetime.now().isoformat(timespec="seconds")

    rows = []
    for p in files("val"):
        s, _, prod, _ = m.score(cv2.imread(str(p)))
        rows.append((p.stem, is_good(p), s, prod))
    rep = {}
    for prod in products:
        r = [x for x in rows if x[3] == prod]
        good, bad = [x[2] for x in r if x[1]], [x[2] for x in r if not x[1]]
        t = meta["thresholds"][prod]
        rep[prod] = {"defective": len(bad), "missed": sum(s < t for s in bad), "good": len(good),
                     "false_alarms": sum(s >= t for s in good),
                     "auroc": auroc(good, bad) if good and bad else None}
    meta["val"] = rep
    meta["val_wrong_product"] = sum(len(products) > 1 and not s.startswith(pr) for s, _, _, pr in rows)
    (out / "anomaly.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
