import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from qc.config import load_profile  # noqa: E402
from training.prepare_mvtec import CLASS_OF, build, mask_boxes  # noqa: E402


def test_profile_covers_mapping():
    p = load_profile("mvtec_fasteners")
    assert set(CLASS_OF.values()) == set(p["classes"]) == set(p["sop"]) == set(p["severity"]["classes"])


def test_mask_boxes_merge_specks_but_not_far_regions():
    m = np.zeros((700, 700), np.uint8)
    m[100:110, 100:110] = m[100:110, 120:130] = m[500:540, 600:620] = 255
    assert sorted(mask_boxes(m)) == [(100, 100, 130, 110), (600, 500, 620, 540)]


def test_build_split_disjoint_and_complete(tmp_path):
    src = tmp_path / "mvtec"
    for cat, defect in CLASS_OF:
        for d in (f"test/{defect}", f"ground_truth/{defect}", "train/good", "test/good"):
            (src / cat / cat / d).mkdir(parents=True, exist_ok=True)
        for i in range(20):
            mask = np.zeros((64, 64), np.uint8)
            mask[10:20, 10:20] = 255
            base = src / cat / cat
            cv2.imwrite(str(base / f"test/{defect}/{i:03}.png"), np.zeros((64, 64, 3), np.uint8))
            cv2.imwrite(str(base / f"ground_truth/{defect}/{i:03}_mask.png"), mask)
            cv2.imwrite(str(base / f"train/good/{i:03}.png"), np.zeros((64, 64, 3), np.uint8))
            cv2.imwrite(str(base / f"test/good/{i:03}.png"), np.zeros((64, 64, 3), np.uint8))
    out = tmp_path / "ds"
    build(src, out, load_profile("mvtec_fasteners")["classes"])
    stems = [p.stem for p in out.glob("images/*/*.png")]
    assert len(stems) == len(set(stems)) == 9 * 20 + 2 * 20 * 2
    assert all(p.read_text() for p in out.glob("labels/test/*.txt"))
    assert not any(p.read_text() for p in out.glob("labels/test_clean/*.txt"))
