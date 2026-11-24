### Detection on `val` (torch+anomaly, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 1.000 | 0.500 | 0.667 | 0.000 | 2 | 0 | 2 |
| scratch | 0.786 | 0.786 | 0.786 | 0.750 | 11 | 3 | 3 |
| thread_damage | 0.500 | 0.500 | 0.500 | 0.000 | 4 | 4 | 4 |
| bent | 0.667 | 1.000 | 0.800 | 1.000 | 4 | 2 | 0 |
| discolouration | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| flipped | 1.000 | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 |
| **macro** | 0.825 | 0.798 | 0.792 | | | | |

Unit level: escape rate 6.5% of 31 defective units; false-reject rate 2.5% of 81 clean units.
Vision latency: mean 13.1 ms, p95 14.4 ms.
Board groups all: micro P 0.659, R 0.750; escapes 2/31, false rejects 2/81.
