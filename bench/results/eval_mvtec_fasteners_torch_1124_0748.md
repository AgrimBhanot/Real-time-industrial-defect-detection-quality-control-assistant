### Detection on `val` (torch, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 1.000 | 0.500 | 0.667 | 0.000 | 2 | 0 | 2 |
| scratch | 1.000 | 0.857 | 0.923 | 1.000 | 12 | 0 | 2 |
| thread_damage | 1.000 | 0.500 | 0.667 | 0.000 | 4 | 0 | 4 |
| bent | 0.800 | 1.000 | 0.889 | 1.000 | 4 | 1 | 0 |
| discolouration | 1.000 | 0.667 | 0.800 | 1.000 | 2 | 0 | 1 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| **macro** | 0.967 | 0.754 | 0.824 | | | | |

Unit level: escape rate 19.4% of 31 defective units; false-reject rate 0.0% of 81 clean units.
Vision latency: mean 10.9 ms, p95 12.0 ms.
Board groups all: micro P 0.964, R 0.750; escapes 6/31, false rejects 0/81.
