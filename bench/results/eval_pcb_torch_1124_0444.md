### Detection on `test` (torch, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| open | 0.798 | 0.973 | 0.877 | 0.958 | 641 | 162 | 18 |
| short | 0.800 | 0.897 | 0.846 | 0.933 | 429 | 107 | 49 |
| mousebite | 0.879 | 0.968 | 0.921 | 0.987 | 567 | 78 | 19 |
| spur | 0.972 | 0.942 | 0.957 | 0.967 | 455 | 13 | 28 |
| copper | 0.947 | 0.972 | 0.960 | 0.983 | 451 | 25 | 13 |
| pin-hole | 0.773 | 0.983 | 0.865 | 0.966 | 462 | 136 | 8 |
| **macro** | 0.862 | 0.956 | 0.904 | | | | |

Unit level: escape rate 0.6% of 500 defective units; false-reject rate 9.2% of 500 clean units.
Vision latency: mean 4.6 ms, p95 5.7 ms.
Board groups seen: micro P 0.949, R 0.933; escapes 3/132, false rejects 2/132.
Board groups unseen: micro P 0.822, R 0.966; escapes 0/368, false rejects 44/368.
