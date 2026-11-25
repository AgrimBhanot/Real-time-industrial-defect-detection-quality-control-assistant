### Detection on `test` (tensorrt, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| open | 0.683 | 0.976 | 0.804 | 0.964 | 643 | 298 | 16 |
| short | 0.866 | 0.906 | 0.885 | 0.925 | 433 | 67 | 45 |
| mousebite | 0.951 | 0.968 | 0.959 | 0.973 | 567 | 29 | 19 |
| spur | 0.969 | 0.959 | 0.964 | 0.975 | 463 | 15 | 20 |
| copper | 0.928 | 0.974 | 0.951 | 0.974 | 452 | 35 | 12 |
| pin-hole | 0.774 | 0.996 | 0.871 | 1.000 | 468 | 137 | 2 |
| **macro** | 0.862 | 0.963 | 0.906 | | | | |

Unit level: escape rate 0.6% of 500 defective units; false-reject rate 8.4% of 500 clean units.
Vision latency: mean 21.0 ms, p95 23.2 ms.
