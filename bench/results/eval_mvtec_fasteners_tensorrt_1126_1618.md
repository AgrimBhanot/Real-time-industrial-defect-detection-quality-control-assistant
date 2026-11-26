### Detection on `test` (tensorrt, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 2 | 4 |
| scratch | 0.714 | 0.667 | 0.690 | 0.500 | 10 | 4 | 5 |
| thread_damage | 0.333 | 0.500 | 0.400 | 0.000 | 3 | 6 | 3 |
| bent | 0.667 | 1.000 | 0.800 | 1.000 | 4 | 2 | 0 |
| discolouration | 0.750 | 1.000 | 0.857 | 1.000 | 3 | 1 | 0 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| **macro** | 0.577 | 0.694 | 0.624 | | | | |

Unit level: escape rate 9.7% of 31 defective units; false-reject rate 0.0% of 63 clean units.
Vision latency: mean 43.5 ms, p95 46.1 ms.
Board groups all: micro P 0.605, R 0.657; escapes 3/31, false rejects 0/63.
