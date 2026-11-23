### Detection on `test` (torch, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| open | 0.767 | 0.973 | 0.858 | 0.958 | 641 | 195 | 18 |
| short | 0.800 | 0.897 | 0.846 | 0.933 | 429 | 107 | 49 |
| mousebite | 0.853 | 0.971 | 0.908 | 0.987 | 569 | 98 | 17 |
| spur | 0.922 | 0.957 | 0.939 | 0.975 | 462 | 39 | 21 |
| copper | 0.917 | 0.978 | 0.947 | 0.991 | 454 | 41 | 10 |
| pin-hole | 0.773 | 0.983 | 0.865 | 0.966 | 462 | 136 | 8 |
| **macro** | 0.839 | 0.960 | 0.894 | | | | |

Unit level: escape rate 0.6% of 500 defective units; false-reject rate 10.4% of 500 clean units.
Vision latency: mean 3.7 ms, p95 5.0 ms.
Board groups seen: micro P 0.939, R 0.941; escapes 3/132, false rejects 2/132.
Board groups unseen: micro P 0.797, R 0.968; escapes 0/368, false rejects 50/368.
