# MVTec AD screw and metal nut model

Profile `mvtec_fasteners`, YOLO11n at **960 px** (pass `--set vision.imgsz=960`;
`configs/app.yaml` still says 640 because the deployed PCB model uses that).
Data: public MVTec AD photos, CC BY-NC-SA 4.0, see `THIRD_PARTY.md`.
Boxes are derived from masks by `training/prepare_mvtec.py --repeat 4`: each
defective *training* image is listed four times. Validation and test are not repeated.

All figures: laptop, torch backend, IoU 0.5, confidence 0.25. Not yet measured on the Jetson.

## Validation (31 defective, 81 good), used to choose the model

| model | defective passed | good rejected | macro P | macro R |
|---|---|---|---|---|
| n, 640 px | 17 | 0 | .385 | .314 |
| n, 960 px | 13 | 0 | .593 | .442 |
| **n, 960 px, repeat 4 (chosen)** | **3** | 1 | .825 | .798 |
| s, 960 px, repeat 4 | 6 | 0 | .967 | .754 |

Chosen for the fewest defective parts passed. It is also the smaller model.

## Test (31 defective, 63 good), scored once with the chosen model

3 of 31 defective passed, 0 of 63 good rejected. Macro P .577, R .694.

| class | found | missed | false boxes |
|---|---|---|---|
| tip_damage | 0 | 4 | 2 |
| scratch | 10 | 5 | 4 |
| thread_damage | 3 | 3 | 6 |
| bent | 4 | 0 | 2 |
| discolouration | 3 | 0 | 1 |
| flipped | 3 | 0 | 0 |

Reject/accept holds up on test, but naming and locating the defect is much weaker:
a part can be rejected on a wrong or misplaced box. `tip_damage` was never found.
Counts are tiny: 3 of 31 is consistent with a true miss rate of roughly 2 to 26% (95%).
The photos are studio shots, so this says nothing about a webcam on other parts.
Do not tune against this test split.

"Rejected" here means FAIL or REVIEW: of the 28 caught, 16 were FAIL and 12 REVIEW.
All 16 parts whose true verdict is FAIL were caught (2 only as REVIEW). Of the 3 passed,
2 should have been REVIEW and 1 PASS_WITH_NOTE.
