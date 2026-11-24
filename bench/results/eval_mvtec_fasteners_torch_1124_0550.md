### Detection on `val` (torch, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 4 |
| scratch | 0.857 | 0.429 | 0.571 | 0.750 | 6 | 1 | 8 |
| thread_damage | 0.200 | 0.125 | 0.154 | 0.000 | 1 | 4 | 7 |
| bent | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 4 |
| discolouration | 0.250 | 0.333 | 0.286 | 0.000 | 1 | 3 | 2 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| **macro** | 0.385 | 0.314 | 0.335 | | | | |

Unit level: escape rate 54.8% of 31 defective units; false-reject rate 0.0% of 81 clean units.
Vision latency: mean 5.6 ms, p95 6.5 ms.
Board groups all: micro P 0.579, R 0.306; escapes 17/31, false rejects 0/81.
