### Detection on `test` (tensorrt, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 0.200 | 0.250 | 0.222 | 0.000 | 1 | 4 | 3 |
| scratch | 0.528 | 0.463 | 0.494 | 0.455 | 19 | 17 | 22 |
| thread_damage | 0.500 | 0.500 | 0.500 | 0.000 | 3 | 3 | 3 |
| deformation | 0.957 | 0.759 | 0.846 | 0.875 | 22 | 1 | 7 |
| discolouration | 0.600 | 1.000 | 0.750 | 1.000 | 3 | 2 | 0 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| rust | 1.000 | 1.000 | 1.000 | 1.000 | 6 | 0 | 0 |
| hole | 0.500 | 0.500 | 0.500 | 0.000 | 2 | 2 | 2 |
| paint_defect | 1.000 | 0.750 | 0.857 | 1.000 | 3 | 0 | 1 |
| mismatch | 0.533 | 0.308 | 0.390 | 0.429 | 8 | 7 | 18 |
| **macro** | 0.682 | 0.653 | 0.656 | | | | |

Unit level: escape rate 16.0% of 81 defective units; false-reject rate 6.2% of 97 clean units.
Vision latency: mean 44.3 ms, p95 46.4 ms.
Board groups all: micro P 0.660, R 0.556; escapes 13/81, false rejects 6/97.
