from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("cv2")
from qc.config import load_config, load_profile  # noqa: E402
from qc.rules import RuleEngine  # noqa: E402
from qc.schema import Detection  # noqa: E402
from qc.vision import build_detector  # noqa: E402
from qc.vision.anomaly import fuse  # noqa: E402

PROFILE = load_profile("mvtec_fasteners")


def amap():
    m = np.zeros((10, 10), np.float32)
    m[2:4, 5:7] = 0.8
    m[3, 6] = 1.0
    m[8, 8] = 0.9
    return m


def test_below_threshold_adds_nothing():
    assert fuse([], amap(), 1.0, 1.1, 100, 100) == []


def test_box_is_region_around_peak_only():
    (d,) = fuse([], amap(), 1.0, 0.5, 200, 100)
    assert d.bbox == [100, 20, 140, 40] and d.defect == "anomaly" and 0.5 <= d.confidence <= 1


def test_named_defect_on_peak_suppresses_anomaly():
    s = Detection("scratch", 0.9, [60, 25, 75, 45])
    assert fuse([s], amap(), 1.0, 0.5, 100, 100) == [s]
    assert len(fuse([Detection("scratch", 0.9, [0, 0, 10, 10])], amap(), 1.0, 0.5, 100, 100)) == 2


def verdict(dets):
    r = RuleEngine(PROFILE)
    r.annotate(dets, 100, 100)
    return r.decide(dets)[0]


def test_anomaly_means_review_never_fail():
    an = lambda: Detection("anomaly", 1.0, [0, 0, 90, 90])  # noqa: E731
    assert verdict([an()]) == verdict([an(), an(), an()]) == "REVIEW"
    med = Detection("tip_damage", 0.9, [0, 0, 9, 9])
    assert verdict([med, an()]) == "REVIEW"
    assert verdict([Detection("bent", 0.9, [0, 0, 9, 9]), an()]) == "FAIL"


def test_off_by_default_and_bad_mode():
    cfg = load_config(overrides=["profile=mvtec_fasteners", "vision.backend=groundtruth"])
    assert build_detector(cfg).backend == "groundtruth"
    cfg = load_config(overrides=["profile=mvtec_fasteners", "vision.anomaly=onyl"])
    with pytest.raises(ValueError):
        build_detector(cfg)


def test_calibration_parts_are_not_in_bank():
    pytest.importorskip("torch")
    from training.train_anomaly import split_good

    files = [Path(f"p{i}_{v}.png") for i in range(10) for v in range(4)]
    g = {f.stem: f.stem.split("_")[0] for f in files}
    bank, cal = split_good(files, g)
    assert len(bank) == 32 and len(cal) == 8
    assert not {g[f.stem] for f in bank} & {g[f.stem] for f in cal}


def test_damaged_part_with_empty_label_is_not_good(tmp_path):
    pytest.importorskip("torch")
    from training.train_anomaly import is_good, product_of

    for stem, want in (("b01__good__1", True), ("b02__rust__1", False), ("screw_good_tr_001", True)):
        (tmp_path / f"{stem}.txt").write_text("")
        assert is_good(tmp_path / f"{stem}.png") is want
    assert not is_good(tmp_path / "unlabelled.png")
    assert product_of("b01__good__1") == product_of("b02__good__7") == "part"
    assert product_of("metal_nut_good_tr_003") == "metal_nut"
