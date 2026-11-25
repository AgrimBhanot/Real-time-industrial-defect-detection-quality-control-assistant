### Detection on `test` (tensorrt, IoU>=0.5, conf>=0.25)

| class | P | R | F1 | hard-case R | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| open | 0.768 | 0.974 | 0.859 | 0.958 | 642 | 194 | 17 |
| short | 0.802 | 0.897 | 0.847 | 0.933 | 429 | 106 | 49 |
| mousebite | 0.853 | 0.971 | 0.908 | 0.987 | 569 | 98 | 17 |
| spur | 0.922 | 0.957 | 0.939 | 0.975 | 462 | 39 | 21 |
| copper | 0.915 | 0.978 | 0.946 | 0.991 | 454 | 42 | 10 |
| pin-hole | 0.774 | 0.983 | 0.866 | 0.966 | 462 | 135 | 8 |
| **macro** | 0.839 | 0.960 | 0.894 | | | | |

Unit level: escape rate 0.6% of 500 defective units; false-reject rate 10.4% of 500 clean units.
Vision latency: mean 21.4 ms, p95 23.2 ms.
Board groups seen: micro P 0.939, R 0.941; escapes 3/132, false rejects 2/132.
Board groups unseen: micro P 0.797, R 0.969; escapes 0/368, false rejects 50/368.
