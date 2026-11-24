### Detection on `val` (torch, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 1 | 4 |
| scratch | 0.889 | 0.571 | 0.696 | 1.000 | 8 | 1 | 6 |
| thread_damage | 0.667 | 0.250 | 0.364 | 0.000 | 2 | 1 | 6 |
| bent | 0.667 | 0.500 | 0.571 | 0.000 | 2 | 1 | 2 |
| discolouration | 0.333 | 0.333 | 0.333 | 0.000 | 1 | 2 | 2 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| **macro** | 0.593 | 0.442 | 0.494 | | | | |

Unit level: escape rate 41.9% of 31 defective units; false-reject rate 0.0% of 81 clean units.
Vision latency: mean 7.3 ms, p95 8.4 ms.
Board groups all: micro P 0.727, R 0.444; escapes 13/31, false rejects 0/81.
