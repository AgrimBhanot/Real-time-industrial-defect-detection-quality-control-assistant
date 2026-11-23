import json

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from qc.config import load_profile  # noqa: E402
from qc.sources import center_square  # noqa: E402
from training.live_test import summarise  # noqa: E402
from training.parts import parse_name  # noqa: E402
from training.prepare_fasteners import build  # noqa: E402

CONDS = ("good", "thread_damage", "deformation", "rust")


def make(tmp_path, n=5):
    prof, im, lb = load_profile("fasteners"), tmp_path / "im", tmp_path / "lb"
    im.mkdir()
    lb.mkdir()
    for c in CONDS:
        for i in range(n):
            for k in range(3):
                stem = f"{c[0].upper()}{i}__{c}__{k}"
                cv2.imwrite(str(im / f"{stem}.jpg"), np.zeros((64, 64, 3), np.uint8))
                if c != "good":
                    (lb / f"{stem}.txt").write_text(f"{prof['classes'].index(c)} 0.5 0.5 0.2 0.2\n")
    return prof, im, lb


def test_profile_is_consistent():
    p = load_profile("fasteners")
    assert set(p["classes"]) == set(p["severity"]["classes"]) == set(p["sop"])


def test_split_is_by_part(tmp_path):
    prof, im, lb = make(tmp_path)
    out = tmp_path / "ds"
    build([im], [lb], out, prof)
    where = {}
    for f in out.glob("images/*/*.jpg"):
        where.setdefault(parse_name(f.stem)[0], set()).add(f.parent.name.split("_")[0])
    assert len(where) == 20 and all(len(s) == 1 for s in where.values())
    for s in ("train", "val", "test"):
        conds = {parse_name(f.stem)[1] for f in out.glob(f"images/{s}*/*.jpg")}
        assert conds == set(CONDS)
    g = json.loads((out / "groups.json").read_text())
    assert not set(g["train_groups"]) & set(g["test_groups"])


@pytest.mark.parametrize("break_it", ["missing", "labelled_good", "bad_class"])
def test_label_mistakes_are_refused(tmp_path, break_it):
    prof, im, lb = make(tmp_path)
    if break_it == "missing":
        (lb / "R0__rust__0.txt").unlink()
    elif break_it == "labelled_good":
        (lb / "G0__good__0.txt").write_text("0 .5 .5 .1 .1\n")
    else:
        (lb / "R0__rust__0.txt").write_text("9 .5 .5 .1 .1\n")
    with pytest.raises(ValueError):
        build([im], [lb], tmp_path / "ds", prof)
    assert not (tmp_path / "ds").exists()


def test_too_few_parts(tmp_path):
    prof, im, lb = make(tmp_path, n=2)
    with pytest.raises(ValueError, match="at least 3"):
        build([im], [lb], tmp_path / "ds", prof)


def test_center_square():
    img = np.zeros((720, 1280, 3), np.uint8)
    img[:, 640] = 255
    out = center_square(img)
    assert out.shape[:2] == (720, 720) and out[0, 360, 0] == 255


def test_live_summary():
    rows = [dict(part="a", truth="rust", found=["rust"], verdict="PASS_WITH_NOTE"),
            dict(part="b", truth="rust", found=[], verdict="PASS"),
            dict(part="c", truth="good", found=["rust"], verdict="REVIEW"),
            dict(part="d", truth="good", found=[], verdict="PASS")]
    s = summarise(rows)
    assert (s["defect_missed"], s["right_type_found"], s["good_not_passed"], s["defective_verdict_pass"]) == (1, 1, 1, 1)
