"""Reliability soak test: the full pipeline (vision + rules + log + async Llama advice) unattended.

  python bench/soak.py --units 1000 --set advisory.backend=executorch
  python bench/soak.py --minutes 15 --set source.fps_limit=2     # thermal run at conveyor pace

Pass criteria written to bench/results/soak_*.json: zero crashes, every unit logged, log integrity ok,
bounded memory (RSS growth of the app and the Llama process reported).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psutil  # noqa: E402

from bench.run_summary import summarize  # noqa: E402
from qc.config import load_config  # noqa: E402
from qc.pipeline import Pipeline  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--units", type=int, default=1000)
    ap.add_argument("--minutes", type=float, default=None, help="stop after this long instead of --units")
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()

    stamp = datetime.now().strftime("%m%d_%H%M")
    db = ROOT / f"runs/soak_{stamp}.db"
    cfg = load_config(overrides=["source.loop=true", "source.fps_limit=0", f"logging.db={db}",
                                 "logging.save_frames=none", *args.set])
    pipe = Pipeline(cfg)
    me = psutil.Process(os.getpid())
    rss, errors, seen = [], [], 0
    deadline = time.time() + args.minutes * 60 if args.minutes else None

    def on_record(rec):
        nonlocal seen
        seen += 1
        if seen % 50 == 0:
            snap = {"unit": seen, "t": time.time(), "app_rss_mb": me.memory_info().rss / 2**20}
            pid = pipe._llm_pid()
            if pid:
                try:
                    snap["llm_rss_mb"] = psutil.Process(pid).memory_info().rss / 2**20
                except psutil.Error:
                    pass
            rss.append(snap)
            print(f"{seen} units  app {snap['app_rss_mb']:.0f} MB  llm {snap.get('llm_rss_mb', 0):.0f} MB  "
                  f"advice queue {pipe.worker.q.unfinished_tasks if pipe.worker else 0}", flush=True)
        if deadline and time.time() > deadline:
            pipe.stop()

    t0 = time.time()
    try:
        pipe.run(max_frames=None if deadline else args.units, on_record=on_record, render=True)
    except Exception:
        errors.append(traceback.format_exc())
    wall = time.time() - t0
    pipe.drain_advice(timeout=900)
    pipe.close()

    s = summarize(db, f"U-{pipe.run_id}-")
    growth = {k: (rss[-1][k] - rss[0][k]) if len(rss) > 1 and k in rss[0] and k in rss[-1] else None
              for k in ("app_rss_mb", "llm_rss_mb")}
    passed = (not errors and s["units"] == seen and s["integrity"]["sqlite_integrity_check"] == "ok"
              and s["integrity"]["advice_without_inspection"] == 0 and s["integrity"]["n_defects_mismatch"] == 0)
    result = {"passed": passed, "units_processed": seen, "wall_s": wall, "units_per_s": seen / wall if wall else None,
              "crashes": errors, "advice_dropped": pipe.worker.dropped if pipe.worker else 0,
              "rss_growth_mb": growth, "rss_trace": rss, "summary": s, "overrides": args.set}
    out = ROOT / f"bench/results/soak_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("passed", "units_processed", "units_per_s", "advice_dropped",
                                             "rss_growth_mb")}, indent=2))
    print(f"wrote {out}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
