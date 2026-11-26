### Detection on `val` (tensorrt, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 0.750 | 0.750 | 0.750 | 0.000 | 3 | 1 | 1 |
| scratch | 0.512 | 0.478 | 0.494 | 0.500 | 22 | 21 | 24 |
| thread_damage | 0.600 | 0.375 | 0.462 | 0.000 | 3 | 2 | 5 |
| deformation | 1.000 | 0.947 | 0.973 | 1.000 | 18 | 0 | 1 |
| discolouration | 0.750 | 1.000 | 0.857 | 1.000 | 3 | 1 | 0 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| rust | 1.000 | 1.000 | 1.000 | 1.000 | 8 | 0 | 0 |
| hole | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 2 | 3 |
| paint_defect | 1.000 | 1.000 | 1.000 | 1.000 | 6 | 0 | 0 |
| mismatch | 0.500 | 0.533 | 0.516 | 0.375 | 16 | 16 | 14 |
| **macro** | 0.711 | 0.708 | 0.705 | | | | |

Unit level: escape rate 9.1% of 88 defective units; false-reject rate 3.5% of 115 clean units.
Vision latency: mean 44.1 ms, p95 46.5 ms.
Board groups all: micro P 0.656, R 0.631; escapes 8/88, false rejects 4/115.
