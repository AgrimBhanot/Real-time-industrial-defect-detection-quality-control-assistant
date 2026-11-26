### Detection on `test` (tensorrt, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| crease | 1.000 | 0.429 | 0.600 | 0.000 | 3 | 0 | 4 |
| crescent_gap | 0.750 | 0.973 | 0.847 | 0.900 | 36 | 12 | 1 |
| inclusion | 0.500 | 0.100 | 0.167 | 0.154 | 5 | 5 | 45 |
| oil_spot | 0.607 | 0.739 | 0.667 | 1.000 | 17 | 11 | 6 |
| punching_hole | 0.959 | 0.959 | 0.959 | 0.846 | 47 | 2 | 2 |
| rolled_pit | 0.833 | 0.500 | 0.625 | 0.333 | 5 | 1 | 5 |
| silk_spot | 0.529 | 0.213 | 0.304 | 0.140 | 36 | 32 | 133 |
| waist_folding | 0.727 | 0.533 | 0.615 | 0.250 | 8 | 3 | 7 |
| water_spot | 0.290 | 0.581 | 0.387 | 0.250 | 18 | 44 | 13 |
| welding_line | 0.900 | 0.960 | 0.929 | 0.947 | 72 | 8 | 3 |
| **macro** | 0.710 | 0.599 | 0.610 | | | | |

Unit level: escape rate 41.4% of 345 defective units; false-reject rate - of 0 clean units.
Vision latency: mean 24.4 ms, p95 25.6 ms.
Board groups all: micro P 0.677, R 0.530; escapes 143/345, false rejects 0/0.
