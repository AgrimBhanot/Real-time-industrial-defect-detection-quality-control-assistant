"""Operator site: local Flask server (no CDN assets, works fully offline)."""
from __future__ import annotations

import io
import ipaddress
import logging
import re
import time
from pathlib import Path

import cv2
from flask import Flask, Response, abort, jsonify, request, send_from_directory

from qc import overlay
from qc.advisory.summary import shift_summary
from qc.app.line import Line
from qc.config import Config
from qc.pipeline import Pipeline
from qc.schema import Detection, InspectionRecord
from qc.sources import CameraSource

STATIC = Path(__file__).parent / "static"
UNIT_ID = re.compile(r"^[A-Za-z0-9_-]{1,60}$")
BOUNDARY = "multipart/x-mixed-replace; boundary=frame"


def network_state() -> dict:
    """Is there a way to the internet? (shown on the site as offline evidence; nothing is contacted)"""
    out = {"default_route": None, "wifi": None}
    try:
        for line in Path("/proc/net/route").read_text().splitlines()[1:]:
            f = line.split()
            if f[1] == "00000000" and int(f[3], 16) & 1:
                out["default_route"] = out["default_route"] or f[0]
        for d in Path("/sys/class/net").iterdir():
            if (d / "wireless").exists():
                out["wifi"] = (d / "operstate").read_text().strip()
    except OSError:
        pass
    return out


def unit_image(u: dict, boxes: bool = True, width: int = 0):
    """Evidence image of a logged unit, with its boxes drawn from the stored record."""
    for p in (u.get("frame_path"), u.get("image_ref")):
        if p and Path(p).is_file():
            img = cv2.imread(str(p))
            if img is not None:
                break
    else:
        return None
    if width and img.shape[1] > width:   # scale first: thumbnails stay fast and their lines stay visible
        k = width / img.shape[1]
        img = cv2.resize(img, (width, max(1, round(img.shape[0] * k))), interpolation=cv2.INTER_AREA)
    else:
        k = 1.0
    if boxes:
        r = u["record"]
        names = {f for f in Detection.__dataclass_fields__}
        dets = [Detection(**{a: b for a, b in d.items() if a in names}) for d in r.get("detections", [])]
        parts = [dict(p) for p in r.get("parts", [])]
        for d in dets:
            d.bbox = [v * k for v in d.bbox]
        for p in parts:
            p["bbox"] = [v * k for v in p["bbox"]]
            p["poly"] = [[x * k, y * k] for x, y in p.get("poly") or []]
        rec = InspectionRecord(r.get("unit_id", ""), "", "", "", [0, 0], dets, u["result"], parts=parts)
        img = overlay.draw(img, rec, banner=False, labels=not 0 < width <= 480)
    return img


def create_app(line, cfg: Config) -> Flask:
    """line: a Line (switchable), or a bare Pipeline in tests."""
    if isinstance(line, Pipeline):
        line = _Fixed(line, cfg)
    app = Flask(__name__, static_folder=None)
    srv = cfg.section("server")
    stream_dt = 1.0 / float(srv.get("stream_fps", 12))
    allow = [ipaddress.ip_network(n) for n in srv.get("allow") or []]
    thumbs: dict = {}

    @app.before_request
    def guard():
        if allow:
            ip = ipaddress.ip_address(request.remote_addr)
            ip = getattr(ip, "ipv4_mapped", None) or ip
            if not any(ip in n for n in allow):
                abort(403)
        # a page on another site can send a plain form to this address, but not this header
        if request.method == "POST" and request.headers.get("X-QC") != "1":
            abort(403)

    @app.after_request
    def headers(resp):
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html", max_age=0)

    @app.get("/static/<path:name>")
    def static_file(name):
        return send_from_directory(STATIC, name, max_age=0)

    @app.get("/stream.mjpg")
    def stream():
        """Newest view with overlay; follows the line when it is switched."""
        def frames():
            # Browsers show an MJPEG part only when the next one starts, so each new frame is sent twice:
            # otherwise a slow conveyor would always show the previous unit next to the current verdict.
            last, again = None, False
            while True:
                jpg = line.pipe.state.jpeg if line.pipe else None
                if jpg is not None and (jpg is not last or again):
                    again = jpg is not last
                    last = jpg
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
                time.sleep(stream_dt)

        return Response(frames(), mimetype=BOUNDARY)

    @app.get("/camera.mjpg")
    def camera():
        """Raw live view: every camera frame, not only inspected units."""
        def frames():
            last = None
            while True:
                img = getattr(line.pipe.source, "latest", None) if line.pipe else None
                if img is not None and img is not last:
                    last = img
                    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ok:
                        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
                time.sleep(1 / 30)

        if not isinstance(line.pipe.source, CameraSource):
            return Response("source is not a camera", status=404)
        return Response(frames(), mimetype=BOUNDARY)

    @app.get("/api/state")
    def state():
        pipe = line.pipe
        s, w = pipe.state, pipe.worker
        with s.lock:
            rec = s.record
            current = s.advice.get(rec["unit_id"]) if rec else None
            latest = s.advice[s.advice_order[-1]] if s.advice_order else None
            body = {"record": rec, "advice_current": current, "advice_latest": latest, "fps": s.fps, "live": s.live,
                    "counts": dict(s.counts), "gt_counts": dict(s.gt_counts), "recent": list(s.recent)}
        c = pipe.cfg
        body.update({
            "session": pipe.run_id, "profile": c.profile_name, "title": c.profile.get("title"),
            "label": c.profile.get("label") or c.profile.get("title"), "station": c.profile.get("station"),
            "vision_backend": pipe.detector.backend if pipe.detector else "off (camera only)",
            "inspect": pipe.inspect, "paused": pipe.control.paused, "fps_limit": pipe.control.fps_limit,
            "trigger": pipe.trigger is not None, "switching": line.switching,
            "error": line.error or s.error,
            "camera": ({"live": pipe.source.latest is not None, "error": s.source_error,
                        "name": f"{pipe.source.kind} {pipe.source.index}"}
                       if isinstance(pipe.source, CameraSource) else None),
            "advisory_backend": pipe.advisor.backend if w else "disabled",
            "advice_pending": w.q.unfinished_tasks if w else 0, "advice_dropped": w.dropped if w else 0,
            "advice_writing": w.current if w else None,
            "telemetry": pipe.telemetry.snapshot() if pipe.telemetry else {}, "network": network_state(),
        })
        return jsonify(body)

    # ---- controls
    @app.get("/api/lines")
    def lines():
        return jsonify({"current": line.pipe.cfg.profile_name, "switching": line.switching, "lines": line.available()})

    @app.post("/api/line")
    def set_line():
        name = (request.get_json(silent=True) or {}).get("name")
        match = [x for x in line.available() if x["name"] == name]
        if not match:
            return jsonify({"error": f"unknown line {name!r}"}), 400
        if not match[0]["ready"]:
            return jsonify({"error": f"{match[0]['label']}: {match[0]['why']}"}), 409
        try:
            line.switch(name)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 409
        return jsonify({"switching": name})

    @app.post("/api/control")
    def control():
        b = request.get_json(silent=True) or {}
        c = line.pipe.control
        act = b.get("action")
        if act in ("pause", "play", "step", "inspect_now"):
            getattr(c, act)()
        elif act == "pace":
            try:
                c.fps_limit = min(30.0, max(0.05, float(b.get("value"))))
            except (TypeError, ValueError):
                return jsonify({"error": "pace must be a number"}), 400
        else:
            return jsonify({"error": f"unknown action {act!r}"}), 400
        return jsonify({"paused": c.paused, "fps_limit": c.fps_limit})

    # ---- inspection log
    def filters() -> dict:
        a = request.args
        f = {k: a.get(k, "").strip() for k in
             ("profile", "session", "defect", "decision", "gt_outcome", "since", "until", "q")}
        f["results"] = [r for r in a.get("results", "").split(",") if r]
        return f

    def whole(name: str, default: int, top: int) -> int:
        try:
            return min(top, max(0, int(request.args.get(name, default))))
        except ValueError:
            return default

    def unit_or_404(unit_id: str) -> dict:
        u = line.pipe.db.unit(unit_id) if UNIT_ID.match(unit_id) else None
        if u is None:
            abort(404)
        return u

    @app.get("/api/log")
    def log_page():
        return jsonify(line.pipe.db.search(filters(), whole("limit", 50, 500), whole("offset", 0, 10**7)))

    @app.get("/api/facets")
    def facets():
        return jsonify(line.pipe.db.facets())

    @app.get("/api/unit/<unit_id>")
    def unit(unit_id):
        return jsonify(unit_or_404(unit_id))

    @app.get("/api/unit/<unit_id>/image.jpg")
    def image(unit_id):
        w, boxes = whole("w", 0, 4000), request.args.get("boxes", "1") != "0"
        key = (unit_id, w, boxes)
        if key not in thumbs:
            img = unit_image(unit_or_404(unit_id), boxes, w)
            if img is None:
                abort(404)
            jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
            if not 0 < w <= 480:
                return Response(jpg, mimetype="image/jpeg")
            if len(thumbs) > 600:
                thumbs.clear()
            thumbs[key] = jpg
        return Response(thumbs[key], mimetype="image/jpeg", headers={"Cache-Control": "max-age=86400"})

    @app.post("/api/unit/<unit_id>/decision")
    def decide(unit_id):
        b = request.get_json(silent=True) or {}
        if not UNIT_ID.match(unit_id):
            abort(404)
        try:
            line.pipe.db.decide(unit_id, str(b.get("decision")), str(b.get("operator") or ""), str(b.get("note") or ""))
        except KeyError:
            abort(404)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(line.pipe.db.unit(unit_id))

    @app.get("/api/export.csv")
    def export():
        buf = io.StringIO()
        line.pipe.db.export_csv(buf, filters=filters())
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=inspections.csv"})

    # ---- analytics and system
    @app.get("/api/analytics")
    def analytics():
        return jsonify(line.pipe.db.analytics(filters()))

    @app.get("/api/metrics")
    def metrics():
        return jsonify(line.pipe.db.metrics(whole("limit", 240, 2000)))

    @app.post("/api/shift_summary")
    def summary():
        pipe = line.pipe
        llm = pipe.advisor.primary if pipe.worker else None
        return jsonify(shift_summary(pipe.cfg.profile, pipe.db, llm, whole("last_n", 200, 5000)))

    return app


class _Fixed:
    """A single pipeline that cannot be switched (tests, camera-only tools)."""
    switching = error = None

    def __init__(self, pipe: Pipeline, cfg: Config):
        self.pipe, self.cfg = pipe, cfg

    def available(self) -> list:
        return [{"name": self.cfg.profile_name, "label": self.cfg.profile.get("title"), "ready": True, "why": "",
                 "camera": False}]

    def switch(self, name: str) -> None:
        raise RuntimeError("this line cannot be switched")


def serve(cfg: Config, overrides: list[str] | None = None, config_path=None) -> None:
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # the page polls; one line per request hides real messages
    line = Line(cfg, overrides, config_path)
    line.start()
    srv = cfg.section("server")
    host, port = srv.get("host", "0.0.0.0"), int(srv.get("port", 8000))
    print(f"operator site: http://localhost:{port} on the board, http://192.168.55.1:{port} over USB-C", flush=True)
    try:
        create_app(line, cfg).run(host=host, port=port, threaded=True, use_reloader=False)
    finally:
        line.close()
