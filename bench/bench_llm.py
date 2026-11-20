"""Llama (ExecuTorch) benchmark on the device: TTFT, tokens/s, total time, JSON validity, faithfulness, peak RSS.

  python bench/bench_llm.py --n 30 --set advisory.backend=executorch
"""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psutil  # noqa: E402

from bench.common import sample_records, stats  # noqa: E402
from qc.advisory import Advisor  # noqa: E402
from qc.config import load_config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()

    cfg = load_config(overrides=args.set)
    advisor = Advisor(cfg)
    t0 = time.perf_counter()
    start_info = getattr(advisor.primary, "start", lambda: {})() or {}
    start_wall_ms = (time.perf_counter() - t0) * 1000
    records = sample_records(cfg, args.n)
    results, peak_rss = [], 0.0
    try:
        for i, rec in enumerate(records):
            r = advisor.advise(rec)
            results.append(r.to_dict())
            pid = getattr(advisor.primary, "pid", None)
            if pid:  # persistent server: sample its RSS after each generation
                try:
                    peak_rss = max(peak_rss, psutil.Process(pid).memory_info().rss / 2**20)
                except psutil.Error:
                    pass
            print(f"[{i + 1}/{len(records)}] {rec.inspection_result:<14} valid={r.valid} fallback={r.fallback} "
                  f"ttft={r.ttft_ms} tok/s={r.tok_s} total={r.total_ms}")
    finally:
        advisor.close()

    err_kinds = Counter(e.split(": ", 1)[-1].split(":")[0] for r in results for e in r["errors"])
    summary = {
        "backend": advisor.backend, "n": len(results),
        "valid_rate": sum(r["valid"] for r in results) / len(results),
        # valid on the first attempt with no repair: the model's own JSON was correct
        "strict_first_try_rate": sum(r["valid"] and r["attempts"] == 1 and not r["repaired"] for r in results)
        / len(results),
        "repaired_rate": sum(r["valid"] and r["repaired"] for r in results) / len(results),
        "loop_stops": sum(r["loop_stop"] for r in results),
        "fallback_rate": sum(r["fallback"] for r in results) / len(results),
        "faithfulness_failures": sum(1 for r in results for e in r["errors"] if "not in record" in e),
        "error_kinds": dict(err_kinds),
        **{k: stats([r[k] for r in results if r.get(k)]) for k in ("ttft_ms", "tok_s", "total_ms", "load_ms")},
        "server_start": {**start_info, "wall_ms": start_wall_ms} if start_info else None,
        "llm_process_peak_rss_mb": peak_rss or resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024,
        "prompt_tokens": stats([r["prompt_tokens"] for r in results if r.get("prompt_tokens")]),
        "generated_tokens": stats([r["generated_tokens"] for r in results if r.get("generated_tokens")]),
        "config": cfg.section("advisory"), "at": datetime.now().isoformat(timespec="seconds"),
    }
    out = ROOT / "bench/results" / f"llm_{advisor.backend}_{datetime.now():%m%d_%H%M}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "samples": results}, indent=2))
    # hand-review sheet for the advice-quality rubric (report section "Useful advice")
    review = [f"# Advice review sheet ({advisor.backend}, {summary['at']})\n",
              "Score each 0-2: grounded (only findings in the record), actionable, correct per SOP, concise.\n"]
    for rec, r in zip(records, results):
        review += [f"## {rec.unit_id} - {rec.inspection_result}",
                   "findings: " + ", ".join(f"{d.defect}/{d.severity}/{d.zone}" for d in rec.detections),
                   f"backend: {r['backend']} valid={r['valid']} fallback={r['fallback']}",
                   "```json", json.dumps(r["advice"], indent=2, ensure_ascii=False), "```",
                   "| grounded | actionable | correct | concise |", "|---|---|---|---|", "|  |  |  |  |", ""]
    out.with_suffix(".review.md").write_text("\n".join(review))
    print(json.dumps({k: v for k, v in summary.items() if k != "config"}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
