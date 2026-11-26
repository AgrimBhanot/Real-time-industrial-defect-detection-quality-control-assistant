"""Pipeline controls, label comparison, inspection log and web API, without any model."""
import threading
import time

import cv2
import numpy as np
import pytest

pytest.importorskip("flask")
from qc.app.server import create_app  # noqa: E402
from qc.config import load_config  # noqa: E402
from qc.pipeline import Pipeline  # noqa: E402
from qc.schema import Detection, InspectionRecord  # noqa: E402
from qc.storage import InspectionDB  # noqa: E402

POST = {"X-QC": "1"}


class StubDetector:
    """Finds an `open` on every image whose mean is dark."""
    backend, class_conf = "stub", {}

    def warmup(self, n=3):
        pass

    def detect(self, frame):
        dets = [Detection("open", 0.9, [10, 10, 60, 40])] if frame.image.mean() < 100 else []
        return dets, {"pre": 1.0, "infer": 2.0, "post": 1.0}


@pytest.fixture
def demo(tmp_path):
    for d in ("images", "labels"):
        (tmp_path / d).mkdir()
    for name, grey, lbl in (("a", 200, ""), ("b", 50, "0 0.1 0.1 0.1 0.1\n"), ("c", 50, ""), ("d", 200, "0 0.5 0.5 0.1 0.1\n")):
        cv2.imwrite(str(tmp_path / "images" / f"{name}.png"), np.full((200, 200, 3), grey, np.uint8))
        (tmp_path / "labels" / f"{name}.txt").write_text(lbl)
    return tmp_path


def make(demo, monkeypatch, *extra):
    monkeypatch.setattr("qc.pipeline.build_detector", lambda cfg: StubDetector())
    cfg = load_config(overrides=["advisory.backend=template", f"source.path={demo / 'images'}", "source.shuffle=false",
                                 "source.loop=false", "source.fps_limit=0", f"logging.db={demo / 'qc.db'}",
                                 f"logging.frames_dir={demo / 'frames'}", "server.allow=[]", *extra])
    return Pipeline(cfg, with_telemetry=False), cfg


def test_verdicts_are_compared_with_the_labels(demo, monkeypatch):
    pipe, _ = make(demo, monkeypatch)
    seen = []
    pipe.run(on_record=seen.append)
    assert [(r.image_ref[-5], r.inspection_result, r.gt_result, r.gt_outcome) for r in seen] == [
        ("a", "PASS", "PASS", "ok"), ("b", "FAIL", "FAIL", "ok"), ("c", "FAIL", "PASS", "false_reject"),
        ("d", "PASS", "FAIL", "escape")]
    assert pipe.state.gt_counts == {"ok": 2, "false_reject": 1, "escape": 1}
    a = pipe.db.analytics()
    assert a["labels"] == {"n": 4, "outcomes": {"ok": 2, "false_reject": 1, "escape": 1}, "defective": 2, "acceptable": 2}


def test_log_search_paging_and_decisions(demo, monkeypatch):
    pipe, cfg = make(demo, monkeypatch)
    pipe.run()
    pipe.drain_advice(10)
    c = create_app(pipe, cfg).test_client()
    full = c.get("/api/log").get_json()
    assert full["total"] == 4 and full["by_result"] == {"PASS": 2, "FAIL": 2}
    assert [r["result"] for r in c.get("/api/log?results=FAIL").get_json()["rows"]] == ["FAIL", "FAIL"]
    assert c.get("/api/log?defect=open&gt_outcome=false_reject").get_json()["total"] == 1
    assert c.get("/api/log?q=c.png").get_json()["total"] == 1
    assert c.get("/api/log?q=%25").get_json()["total"] == 0          # a typed % is text, not a wildcard
    page = c.get("/api/log?limit=3&offset=3").get_json()
    assert page["total"] == 4 and len(page["rows"]) == 1
    assert c.get("/api/log?decision=open").get_json()["total"] == 2  # stopped units still to be decided

    uid = c.get("/api/log?results=FAIL").get_json()["rows"][0]["unit_id"]
    url = f"/api/unit/{uid}/decision"
    assert c.post(url, json={"decision": "false_alarm"}).status_code == 403              # no X-QC header
    assert c.post(url, json={"decision": "nonsense"}, headers=POST).status_code == 400
    assert c.post("/api/unit/U-none/decision", json={"decision": "scrap"}, headers=POST).status_code == 404
    c.post(url, json={"decision": "confirmed", "operator": "QA"}, headers=POST)
    u = c.post(url, json={"decision": "false_alarm", "note": "dust"}, headers=POST).get_json()
    assert u["decision"] == "false_alarm" and [d["decision"] for d in u["decisions"]] == ["false_alarm", "confirmed"]
    assert c.get("/api/log?decision=open").get_json()["total"] == 1
    assert c.get("/api/analytics").get_json()["decisions"] == {"false_alarm": 1}
    assert u["record"]["detections"][0]["defect"] == "open" and u["advice"]["advice"]["summary"]
    assert "false_alarm" in c.get("/api/export.csv?decision=false_alarm").get_data(as_text=True)
    assert c.get(f"/api/unit/{uid}/image.jpg?w=100").data[:2] == b"\xff\xd8"
    assert c.get("/api/unit/..%2f..%2fetc/image.jpg").status_code == 404


def test_access_is_limited_to_the_board_and_usb(demo, monkeypatch):
    pipe, cfg = make(demo, monkeypatch, "server.allow=[127.0.0.0/8, 192.168.55.0/24]")
    c = create_app(pipe, cfg).test_client()
    assert c.get("/api/state", environ_base={"REMOTE_ADDR": "192.168.55.100"}).status_code == 200
    assert c.get("/api/state", environ_base={"REMOTE_ADDR": "::ffff:127.0.0.1"}).status_code == 200
    assert c.get("/api/state", environ_base={"REMOTE_ADDR": "10.81.3.29"}).status_code == 403


def test_pause_step_play_and_pace(demo, monkeypatch):
    pipe, cfg = make(demo, monkeypatch)
    c = create_app(pipe, cfg).test_client()
    c.post("/api/control", json={"action": "pause"}, headers=POST)
    t = threading.Thread(target=pipe.run, daemon=True)
    t.start()

    def reaches(n):
        end = time.time() + 5
        while pipe.n < n and time.time() < end:
            time.sleep(0.02)
        time.sleep(0.15)
        return pipe.n == n

    assert reaches(0)
    c.post("/api/control", json={"action": "step"}, headers=POST)
    assert reaches(1)
    assert c.post("/api/control", json={"action": "pace", "value": 500}, headers=POST).get_json()["fps_limit"] == 30
    assert c.post("/api/control", json={"action": "pace", "value": "x"}, headers=POST).status_code == 400
    c.post("/api/control", json={"action": "play"}, headers=POST)
    assert reaches(4)
    t.join(5)
    assert not t.is_alive()


def test_old_database_is_migrated(tmp_path):
    import sqlite3

    p = tmp_path / "old.db"
    con = sqlite3.connect(p)
    con.executescript("""CREATE TABLE inspections(unit_id TEXT PRIMARY KEY, ts TEXT, profile TEXT, source TEXT,
      image_ref TEXT, frame_path TEXT, result TEXT, n_defects INTEGER, max_severity TEXT, pre_ms REAL, infer_ms REAL,
      post_ms REAL, vision_ms REAL, rules_ms REAL, e2e_ms REAL, record_json TEXT);
      INSERT INTO inspections(unit_id, result, record_json) VALUES ('U-old', 'PASS', '{}');""")
    con.close()
    db = InspectionDB(p)
    db.log_inspection(InspectionRecord("U-new", "2026-11-26T00:00:00", "s", "=cmd", [1, 1]), "pcb", session="s1")
    assert db.search()["total"] == 2 and db.unit("U-old")["session"] is None
    import io

    buf = io.StringIO()
    db.export_csv(buf)
    assert "'=cmd" in buf.getvalue()  # not a spreadsheet formula


def test_failed_switch_restores_the_old_line(demo, monkeypatch):
    from qc.app.line import Line

    _, cfg = make(demo, monkeypatch)
    ov = ["advisory.backend=template", "vision.backend=groundtruth", f"source.path={demo / 'images'}", "source.type=folder",
          f"logging.db={demo / 'qc.db'}", f"logging.frames_dir={demo / 'frames'}", "lines=[pcb, metal_parts]"]
    ln = Line(cfg, ov)
    ln.start()

    def wait():
        end = time.time() + 10
        while ln.switching and time.time() < end:
            time.sleep(0.02)

    ln.switch("metal_parts")
    wait()
    assert ln.pipe.cfg.profile_name == "metal_parts" and ln.error is None
    real = Pipeline.__init__
    calls = []

    def broken(self, cfg, **kw):
        calls.append(cfg.profile_name)
        if cfg.profile_name == "pcb":
            raise FileNotFoundError("no engine")
        real(self, cfg, **kw)

    monkeypatch.setattr(Pipeline, "__init__", broken)
    ln.switch("pcb")
    wait()
    assert calls == ["pcb", "metal_parts"] and "no engine" in ln.error
    assert ln.pipe.cfg.profile_name == "metal_parts" and ln.thread.is_alive() or ln.pipe.n > 0
    ln.close()
