"""Summarise an inspection log (SQLite) into the numbers the report needs.

  python bench/run_summary.py runs/inspections.db [--since-unit U-1120-101500-00001]

End-to-end latency (frame captured -> verdict logged, and -> validated advice ready), advice validity /
fallback / faithfulness rates, Llama timings, system metrics over the run, and log integrity checks.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench.common import stats  # noqa: E402


def summarize(db_path: Path, run_prefix: str | None = None) -> dict:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    where, args = ("WHERE unit_id LIKE ?", [run_prefix + "%"]) if run_prefix else ("", [])

    def col(sql, *a):
        return [r[0] for r in con.execute(sql, a) if r[0] is not None]

    insp = [dict(r) for r in con.execute(f"SELECT * FROM inspections {where}", args)]
    adv = [dict(r) for r in con.execute(f"SELECT * FROM advice {where}", args)]
    ts = [r["ts"] for r in insp]
    metrics = [dict(r) for r in con.execute(
        "SELECT * FROM system_metrics WHERE ts BETWEEN ? AND ?", (min(ts), max(ts)))] if ts else []
    by_result: dict = {}
    for r in insp:
        by_result[r["result"]] = by_result.get(r["result"], 0) + 1
    orphans = con.execute("SELECT count(*) FROM advice a LEFT JOIN inspections i ON i.unit_id = a.unit_id "
                          "WHERE i.unit_id IS NULL").fetchone()[0]
    det_mismatch = con.execute(
        f"SELECT count(*) FROM inspections i {where.replace('unit_id', 'i.unit_id')} "
        f"{'AND' if where else 'WHERE'} i.n_defects != (SELECT count(*) FROM detections d WHERE d.unit_id = i.unit_id)",
        args).fetchone()[0]
    faithfulness = sum(1 for a in adv if "not in record" in (a["errors"] or ""))

    def m(key):
        return stats([x[key] for x in metrics if x.get(key) is not None])

    return {
        "db": str(db_path), "run": run_prefix, "units": len(insp), "results": by_result,
        "first_ts": min(ts) if ts else None, "last_ts": max(ts) if ts else None,
        "latency_ms": {
            "vision": stats([r["vision_ms"] for r in insp if r["vision_ms"] is not None]),
            "infer": stats([r["infer_ms"] for r in insp if r["infer_ms"] is not None]),
            "frame_to_verdict": stats([r["e2e_ms"] for r in insp if r["e2e_ms"] is not None]),
            "frame_to_advice": stats([a["e2e_ms"] for a in adv if a.get("e2e_ms") is not None]),
            "advice_queue_wait": stats([a["queue_ms"] for a in adv if a.get("queue_ms") is not None]),
        },
        "advice": {
            "n": len(adv),
            "backends": {b: sum(1 for a in adv if a["backend"] == b) for b in {a["backend"] for a in adv}},
            "valid_rate": sum(a["valid"] for a in adv) / len(adv) if adv else None,
            "fallback_rate": sum(a["fallback"] for a in adv) / len(adv) if adv else None,
            "faithfulness_failures": faithfulness,
            "ttft_ms": stats([a["ttft_ms"] for a in adv if a["ttft_ms"]]),
            "tok_s": stats([a["tok_s"] for a in adv if a["tok_s"]]),
            "llm_total_ms": stats([a["total_ms"] for a in adv if a["total_ms"]]),
        },
        "system": {k: m(k) for k in ("cpu_pct", "ram_used_mb", "gpu_pct", "temp_c", "power_mw", "proc_rss_mb",
                                      "llm_rss_mb")},
        "integrity": {
            "sqlite_integrity_check": con.execute("PRAGMA integrity_check").fetchone()[0],
            "advice_without_inspection": orphans,
            "n_defects_mismatch": det_mismatch,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("db", nargs="?", default=str(ROOT / "runs/inspections.db"))
    ap.add_argument("--run", default=None, help="unit_id prefix of one run, e.g. U-1120-101500-")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    s = summarize(Path(args.db), args.run)
    text = json.dumps(s, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
