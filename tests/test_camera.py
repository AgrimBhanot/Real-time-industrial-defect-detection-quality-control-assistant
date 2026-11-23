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
