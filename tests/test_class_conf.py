import numpy as np
import pytest

pytest.importorskip("cv2")
from qc.vision.detector import check_class_conf  # noqa: E402
from training.tune_class_conf import choose  # noqa: E402


def test_check_class_conf():
    assert check_class_conf(None, ["open"]) == {}
    assert check_class_conf({"open": 0.5}, ["open"]) == {"open": 0.5}
    with pytest.raises(ValueError):
        check_class_conf({"nope": 0.5}, ["open"])
    with pytest.raises(ValueError):
        check_class_conf({"open": 0}, ["open"])


def test_choose_removes_low_confidence_false_alarms():
    scores = [(0.9, True)] * 20 + [(0.3, False)] * 10
    assert 0.3 < choose(scores, 20, 0.25, 0.95) <= 0.9


def test_choose_keeps_recall():
    scores = [(0.9, True)] * 10 + [(0.3, True)] * 10 + [(0.5, False)] * 30
    assert choose(scores, 20, 0.25, 0.95) <= 0.3


def test_detector_filters_per_class(monkeypatch, tmp_path):
    ul = pytest.importorskip("ultralytics")
    torch = pytest.importorskip("torch")
    from types import SimpleNamespace as NS

    from qc.sources import Frame
    from qc.vision.detector import UltralyticsDetector
    seen = {}

    class FakeYOLO:
        def __init__(self, *a, **k):
            pass

        def predict(self, img, **kw):
            seen.update(kw)
            boxes = [[0, 0, 9, 9]] * 3
            b = type("B", (), {"__len__": lambda s: 3})()
            b.xyxy, b.conf, b.cls = torch.tensor(boxes), torch.tensor([0.4, 0.4, 0.2]), torch.tensor([0, 1, 1])
            return [NS(boxes=b, names={}, speed={})]

    monkeypatch.setattr(ul, "YOLO", FakeYOLO)
    w = tmp_path / "best.pt"
    w.touch()
    d = UltralyticsDetector("torch", w, ["open", "short"], conf=0.25, class_conf={"open": 0.5, "short": 0.15})
    dets, _ = d.detect(Frame(np.zeros((9, 9, 3), np.uint8), "x", "t"))
    assert [x.defect for x in dets] == ["short", "short"] and seen["conf"] == 0.15
