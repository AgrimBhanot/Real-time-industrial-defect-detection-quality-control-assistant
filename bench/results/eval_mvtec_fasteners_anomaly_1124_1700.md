### Detection on `val` (anomaly, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| tip_damage | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 4 |
| scratch | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 14 |
| thread_damage | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 8 |
| bent | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 4 |
| discolouration | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 3 |
| flipped | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 3 |
| **macro** | 0.000 | 0.000 | 0.000 | | | | |

Unit level: escape rate 6.5% of 31 defective units; false-reject rate 3.7% of 81 clean units.
Vision latency: mean 6.3 ms, p95 6.9 ms.
Board groups all: micro P 0.000, R 0.000; escapes 2/31, false rejects 3/81.
