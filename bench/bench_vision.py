"""Vision benchmark on the deployed device (pre / inference / post, FPS, memory, power, temperature).

  python bench/bench_vision.py --backend tensorrt --frames 300
  python bench/bench_vision.py --backend tensorrt --with-llm     # concurrency: Llama generating at the same time
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench.common import sample_records, stats  # noqa: E402
from qc.config import load_config  # noqa: E402
from qc.rules import RuleEngine  # noqa: E402
from qc.sources import build_source  # noqa: E402
from qc.telemetry import Telemetry  # noqa: E402
from qc.vision import build_detector  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default=None)
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--with-llm", action="store_true")
    ap.add_argument("--llm-calls", type=int, default=3,
                    help="with --with-llm: keep running vision until this many Llama calls have completed")
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()

    ov = ["source.loop=true", *args.set] + ([f"vision.backend={args.backend}"] if args.backend else [])
    cfg = load_config(overrides=ov)
    det, rules = build_detector(cfg), RuleEngine(cfg.profile)
    tel = Telemetry(500)
    tel.start()

    llm_stats, stop = [], threading.Event()
    if args.with_llm:
        from qc.advisory import Advisor

        advisor, recs = Advisor(cfg), sample_records(cfg, 10)

        def llm_loop():
            i = 0
            while not stop.is_set():
                r = advisor.advise(recs[i % len(recs)])
                llm_stats.append(r.to_dict())
                i += 1

        threading.Thread(target=llm_loop, daemon=True).start()

    src = iter(build_source(cfg))
    for _ in range(args.warmup):
        det.detect(next(src))
    rows, samples = [], []
    t_start = time.perf_counter()
    n = 0
    while n < args.frames or (args.with_llm and len(llm_stats) < args.llm_calls):
        n += 1
        f = next(src)
        t0 = time.perf_counter()
        dets, t = det.detect(f)
        h, w = f.image.shape[:2]
        rules.annotate(dets, w, h)
        rules.decide(dets)
        t["total"] = (time.perf_counter() - t0) * 1000
        rows.append(t)
        samples.append(tel.snapshot())
    wall = time.perf_counter() - t_start
    stop.set()
    tel.stop()
    if args.with_llm:
        advisor.close()

    def col(key):
        return [s[key] for s in samples if s.get(key) is not None]

    result = {
        "backend": det.backend, "profile": cfg.profile_name, "frames": n, "with_llm": args.with_llm,
        "wall_s": wall, "fps": n / wall,
        "ms": {k: stats([r[k] for r in rows]) for k in ("pre", "infer", "post", "total")},
        "proc_rss_mb_peak": max(col("proc_rss_mb"), default=None),
        "ram_used_mb_peak": max(col("ram_used_mb"), default=None),
        "gpu_pct_mean": float(np.mean(col("gpu_pct"))) if col("gpu_pct") else None,
        "power_mw_mean": float(np.mean(col("power_mw"))) if col("power_mw") else None,
        "temp_c_max": max(col("temp_c"), default=None),
        "llm_calls_during_run": len(llm_stats),
        "llm": {k: stats([s[k] for s in llm_stats if s.get(k)]) for k in ("ttft_ms", "tok_s", "total_ms")}
        | {"valid_rate": sum(s["valid"] for s in llm_stats) / len(llm_stats)}
        if llm_stats else None,
        "config": {"vision": cfg.section("vision")}, "at": datetime.now().isoformat(timespec="seconds"),
    }
    out = ROOT / "bench/results" / f"vision_{det.backend}{'_with_llm' if args.with_llm else ''}_{datetime.now():%m%d_%H%M}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("backend", "fps", "ms", "proc_rss_mb_peak", "power_mw_mean",
                                             "temp_c_max", "llm")}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
