"""CLI.

  python -m qc check                      # what is installed / missing for the current config
  python -m qc run --max-frames 50        # headless inspection loop, prints one line per unit
  python -m qc serve                      # operator UI on :8000
  python -m qc advise-sample              # one advisory call on a hand-made record (Llama smoke test)

Every command accepts --config and repeated --set key=value overrides, e.g.
  python -m qc run --set vision.backend=groundtruth --set advisory.backend=executorch
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import shutil
import sys

from qc.config import load_config


def cmd_check(cfg) -> int:
    ok = True

    def line(good: bool, what: str, detail: str = "") -> None:
        nonlocal ok
        ok &= good
        print(f"  [{'ok' if good else '--'}] {what}{(': ' + detail) if detail else ''}")

    print(f"profile: {cfg.profile_name} ({cfg.profile.get('title')})")
    print("python packages:")
    for mod in ("numpy", "cv2", "yaml", "psutil", "flask", "torch", "ultralytics", "onnxruntime", "tensorrt"):
        try:
            m = importlib.import_module(mod)
            extra = ""
            if mod == "torch":
                extra = f" cuda={m.cuda.is_available()}"
            if mod == "onnxruntime":
                extra = f" providers={m.get_available_providers()}"
            if mod == "cv2":
                extra = " gstreamer=" + str("GStreamer:                   YES" in m.getBuildInformation())
            line(True, mod, getattr(m, "__version__", "") + extra)
        except Exception as exc:
            line(False, mod, type(exc).__name__)
    print("vision:")
    v = cfg.section("vision")
    wd = cfg.path(v.get("weights_dir", "models/vision/{profile}"))
    for f in ("best.pt", "best.onnx", "best.engine"):
        line((wd / f).exists(), str(wd / f))
    print(f"  backend = {v.get('backend')}")
    print("advisory:")
    e = cfg.section("advisory").get("executorch", {})
    for k in ("server", "runner", "model", "tokenizer"):
        if k in e:
            line(cfg.path(e[k]).exists(), f"{k}: {cfg.path(e[k])}")
    print(f"  backend = {cfg.section('advisory').get('backend')}  mode = {e.get('mode', 'server')}")
    print("source:")
    s = cfg.section("source")
    if s.get("type") in ("folder", "video"):
        line(cfg.path(s["path"]).exists(), f"{s['type']}: {cfg.path(s['path'])}")
    else:
        print(f"  camera: {s.get('camera')}")
    line(shutil.which("tegrastats") is not None, "tegrastats")
    return 0 if ok else 1


def cmd_run(cfg, args) -> int:
    from qc.pipeline import Pipeline

    pipe = Pipeline(cfg)

    def show(rec):
        if not args.quiet:
            defects = " ".join(f"{d.defect}:{d.severity}" for d in rec.detections) or "-"
            print(f"{rec.unit_id} {rec.inspection_result:<14} vision {rec.timings_ms['vision']:6.1f} ms  {defects}")

    pipe.run(max_frames=args.max_frames, on_record=show, render=False)
    if pipe.worker:
        print("waiting for pending advice ...")
        pipe.drain_advice()
        pipe.close()
    for row in pipe.db.recent(5):
        if row["advice_summary"]:
            print(f"  {row['unit_id']} [{row['advice_backend']}] {row['advice_summary']}")
    print(json.dumps(pipe.db.stats(), indent=2))
    return 0


def cmd_advise_sample(cfg) -> int:
    from qc.advisory import Advisor
    from qc.rules import RuleEngine
    from qc.schema import Detection, InspectionRecord

    cls = cfg.profile["classes"]
    dets = [Detection(cls[0], 0.93, [120, 80, 160, 110]), Detection(cls[min(2, len(cls) - 1)], 0.71, [300, 300, 330, 320])]
    rules = RuleEngine(cfg.profile)
    trace = rules.annotate(dets, 640, 640)
    result, why = rules.decide(dets)
    rec = InspectionRecord("U-SAMPLE", "now", "sample", "-", [640, 640], dets, result, trace + why,
                           {"station": cfg.profile.get("station"), "recent_units": 50, "recent_fail": 6,
                            "recent_defects": {cls[0]: 4}})
    print("record:", json.dumps(rec.llm_view(), indent=2))
    advisor = Advisor(cfg)
    try:
        res = advisor.advise(rec)
    finally:
        advisor.close()
    print("advice:", json.dumps(res.to_dict(), indent=2))
    return 0 if res.valid else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="qc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["check", "run", "serve", "advise-sample"])
    p.add_argument("--config", default=None)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--max-frames", type=int, default=None)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config(args.config, args.set)
    if args.command == "check":
        return cmd_check(cfg)
    if args.command == "run":
        return cmd_run(cfg, args)
    if args.command == "advise-sample":
        return cmd_advise_sample(cfg)
    from qc.app.server import serve

    serve(cfg, args.set, args.config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
