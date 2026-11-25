import numpy as np
import pytest

pytest.importorskip("cv2")
from qc.sources import CameraSource, StableTrigger  # noqa: E402


def scene(v):
    return np.full((240, 320, 3), v, np.uint8)


def test_one_unit_per_part_at_rest():
    t = StableTrigger(frames=3)
    stream = [scene(50)] * 10 + [scene(v) for v in (80, 110, 140)] + [scene(170)] * 10
    assert [i for i, f in enumerate(stream) if t.update(f)] == [3, 16]


def test_no_fire_while_moving_or_for_sensor_noise():
    t = StableTrigger(frames=3)
    assert not any(t.update(scene(v)) for v in range(0, 250, 10))
    rng, t = np.random.default_rng(0), StableTrigger(frames=3)
    noisy = [np.clip(120 + rng.normal(0, 4, (240, 320, 3)), 0, 255).astype(np.uint8) for _ in range(30)]
    assert sum(t.update(f) for f in noisy) == 1


class FakeCap:
    def __init__(self, frames):
        self.frames = list(frames)

    def read(self):
        return (True, self.frames.pop(0)) if self.frames else (False, None)

    def release(self):
        pass


def test_camera_reconnects(monkeypatch):
    caps = iter([FakeCap([scene(1)]), FakeCap([]), FakeCap([scene(2), scene(3)])])
    cam = CameraSource(reconnect_s=0.2)
    monkeypatch.setattr("qc.sources.time.sleep", lambda s: None)
    monkeypatch.setattr(cam, "_open", lambda: next(caps))
    it = iter(cam)
    assert next(it).image[0, 0, 0] == 1
    assert next(it).image[0, 0, 0] == 3


def test_dead_camera_gives_up(monkeypatch):
    cam = CameraSource(reconnect_s=0.05)
    monkeypatch.setattr(cam, "_open", lambda: FakeCap([]))
    with pytest.raises(RuntimeError):
        next(iter(cam))


def camera_cfg(tmp_path, *extra):
    from qc.config import load_config

    return load_config(overrides=["source.type=camera", "source.camera.reconnect_s=0", "advisory.enabled=false",
                                  f"logging.db={tmp_path / 'qc.db'}", *extra])


def test_latest_view_follows_every_frame_and_clears(monkeypatch):
    cam = CameraSource(trigger=StableTrigger(frames=3), reconnect_s=0)
    monkeypatch.setattr(cam, "_open", lambda: FakeCap([scene(7)] * 6))
    it = iter(cam)
    next(it)
    assert cam.latest[0, 0, 0] == 7
    with pytest.raises(RuntimeError):
        next(it)
    assert cam.latest is None


def test_camera_only_mode_needs_no_model(tmp_path, monkeypatch):
    pytest.importorskip("flask")
    from qc.app.server import create_app
    from qc.pipeline import Pipeline

    cfg = camera_cfg(tmp_path, "source.inspect=false")
    pipe = Pipeline(cfg, with_telemetry=False)
    assert pipe.detector is None
    s = create_app(pipe, cfg).test_client().get("/api/state").get_json()
    assert s["camera"]["live"] is False and s["inspect"] is False
    pipe.source.latest = scene(9)
    r = create_app(pipe, cfg).test_client().get("/camera.mjpg", buffered=False)
    assert b"image/jpeg" in next(r.response)


def test_served_camera_is_retried(tmp_path, monkeypatch):
    from qc.pipeline import Pipeline

    pipe = Pipeline(camera_cfg(tmp_path, "source.inspect=false"), with_telemetry=False)
    pipe.keep_alive = True
    caps = iter([FakeCap([]), FakeCap([scene(3)])])
    monkeypatch.setattr(pipe.source, "_open", lambda: next(caps))
    errors = []
    monkeypatch.setattr(pipe._halt, "wait", lambda t: errors.append(pipe.state.source_error))
    frame = next(pipe._frames())
    assert frame.image[0, 0, 0] == 3 and "camera read failed" in errors[0] and pipe.state.source_error is None
