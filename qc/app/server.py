"""Operator UI: local Flask server (no CDN assets, works fully offline)."""
from __future__ import annotations

import io
import threading
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from qc.advisory.summary import shift_summary
from qc.config import Config
from qc.pipeline import Pipeline

STATIC = Path(__file__).parent / "static"


def create_app(pipe: Pipeline, cfg: Config) -> Flask:
    app = Flask(__name__, static_folder=None)
    stream_dt = 1.0 / float(cfg.section("server").get("stream_fps", 12))

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/stream.mjpg")
    def stream():
        def frames():
            last = None
            while True:
                jpg = pipe.state.jpeg
                if jpg is not None and jpg is not last:
                    last = jpg
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
                time.sleep(stream_dt)

        return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.get("/api/state")
    def state():
        s = pipe.state
        with s.lock:
            rec = s.record
            current = s.advice.get(rec["unit_id"]) if rec else None
            latest = s.advice[s.advice_order[-1]] if s.advice_order else None
            body = {"record": rec, "advice_current": current, "advice_latest": latest, "fps": s.fps,
                    "counts": dict(s.counts)}
        w = pipe.worker
        body.update({
            "profile": cfg.profile_name, "title": cfg.profile.get("title"),
            "vision_backend": pipe.detector.backend,
            "advisory_backend": pipe.advisor.backend if w else "disabled",
            "advice_pending": w.q.unfinished_tasks if w else 0, "advice_dropped": w.dropped if w else 0,
            "telemetry": pipe.telemetry.snapshot() if pipe.telemetry else {},
        })
        return jsonify(body)

    @app.get("/api/log")
    def log():
        return jsonify(pipe.db.recent(int(request.args.get("limit", 50))))

    @app.get("/api/export.csv")
    def export():
        buf = io.StringIO()
        pipe.db.export_csv(buf)
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=inspections.csv"})

    @app.post("/api/shift_summary")
    def summary():
        llm = pipe.advisor.primary if pipe.worker else None
        return jsonify(shift_summary(cfg.profile, pipe.db, llm, int(request.args.get("last_n", 200))))

    return app


def serve(cfg: Config) -> None:
    pipe = Pipeline(cfg)
    threading.Thread(target=pipe.run, name="inspection", daemon=True).start()
    srv = cfg.section("server")
    host, port = srv.get("host", "0.0.0.0"), int(srv.get("port", 8000))
    print(f"operator UI: http://{host}:{port}  (over USB-C: http://192.168.55.1:{port})")
    create_app(pipe, cfg).run(host=host, port=port, threaded=True, use_reloader=False)
