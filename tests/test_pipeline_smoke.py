"""End-to-end without any model: synthetic images + YOLO labels -> groundtruth detector -> rules -> DB -> template advice."""
import cv2
import numpy as np
import pytest

from qc.config import load_config
from qc.pipeline import Pipeline


@pytest.fixture
def demo_dir(tmp_path):
    img_dir, lbl_dir = tmp_path / "images", tmp_path / "labels"
    img_dir.mkdir()
    lbl_dir.mkdir()
    labels = {
        "u0": "",                                          # clean
        "u1": "0 0.25 0.25 0.05 0.05\n",                   # open -> FAIL
        "u2": "3 0.50 0.50 0.03 0.03\n",                   # spur -> size-dependent
        "u3": "5 0.70 0.70 0.01 0.01\n",                   # tiny pin-hole -> PASS_WITH_NOTE
    }
    for name, lbl in labels.items():
        cv2.imwrite(str(img_dir / f"{name}.jpg"), np.full((640, 640, 3), 128, np.uint8))
        (lbl_dir / f"{name}.txt").write_text(lbl)
    return tmp_path


def test_end_to_end(demo_dir):
    cfg = load_config(overrides=[
        "vision.backend=groundtruth", "advisory.backend=template", f"source.path={demo_dir / 'images'}",
        "source.shuffle=false", "source.loop=false", "source.fps_limit=0",
        f"logging.db={demo_dir / 'qc.db'}", f"logging.frames_dir={demo_dir / 'frames'}",
    ])
    pipe = Pipeline(cfg, with_telemetry=False)
    pipe.rules.thresholds = {"spur": [0.02, 0.06], "pin-hole": [0.01, 0.03]}  # independent of calibration file
    seen = []
    pipe.run(on_record=seen.append)
    pipe.drain_advice(timeout=10)

    results = {r.image_ref.split("/")[-1]: r.inspection_result for r in seen}
    assert results["u0.jpg"] == "PASS"
    assert results["u1.jpg"] == "FAIL"
    assert results["u3.jpg"] == "PASS_WITH_NOTE"

    rows = pipe.db.recent(10)
    assert len(rows) == 4
    advised = [r for r in rows if r["advice_summary"]]
    assert len(advised) == 3  # every unit with findings got advice; the clean one did not
    assert all(r["advice_backend"] == "template" for r in advised)
    stats = pipe.db.stats()
    assert stats["units"] == 4 and stats["defects"]["open"] == 1
    assert len(list((demo_dir / "frames").glob("*.jpg"))) == 3  # save_frames: defective


def test_flask_app_routes(demo_dir):
    pytest.importorskip("flask")
    from qc.app.server import create_app

    cfg = load_config(overrides=[
        "vision.backend=groundtruth", "advisory.backend=template", f"source.path={demo_dir / 'images'}",
        "source.loop=false", "source.fps_limit=0", f"logging.db={demo_dir / 'qc.db'}",
        f"logging.frames_dir={demo_dir / 'frames'}",
    ])
    pipe = Pipeline(cfg, with_telemetry=False)
    pipe.run()
    pipe.drain_advice(timeout=10)
    client = create_app(pipe, cfg).test_client()
    state = client.get("/api/state").get_json()
    assert state["record"] is not None and state["vision_backend"] == "groundtruth"
    assert client.get("/api/log").get_json()["total"] == 4
    assert client.get("/api/export.csv").data.decode().startswith("unit_id,")
    assert "trend" in client.post("/api/shift_summary", headers={"X-QC": "1"}).get_json()
    assert b"QC Inspector" in client.get("/").data
