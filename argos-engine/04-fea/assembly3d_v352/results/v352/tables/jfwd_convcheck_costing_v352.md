# J-FWD governing-line convergence check finer than s6: COSTING (lead 01:30:18Z (5b)); no solve

Measured (b2) s6: 107,611 nodes, 5.76 GiB, 7861 s / 9 inc; (b2') s9: 60,812, 3.146 GiB, 2595 s / 7 inc [SIM].  RSS ~ N^1.06, s/inc ~ N^1.50 [ESTIMATE].  Patch nodes from built meshes x 1.028 (scratch s6 rebuild 104,678 vs 107,611) [DERIVED].

| tag | family | mesh | patch nodes | peak RSS GiB (+10 %) | fits 8.0 cap with 10 % | runtime h (7-9 inc) | folder peak MB | gate GiB |
|---|---|---|---|---|---|---|---|---|
| cA5 | (i) global step | h_brk 0.064 / transition 0.6 (whole break zone) | 134,333 | 7.29 (8.01) | no | 2.37-3.05 | 244.8 | 2.245 |
| cA3 | (i) global step | h_brk 0.060 / transition 0.6 | 143,343 | 7.81 (8.59) | no | 2.61-3.36 | 261.1 | 2.264 |
| cA2 | (i) global step | h_brk 0.056 / transition 0.6 | 154,938 | 8.48 (9.32) | no | 2.94-3.77 | 282.1 | 2.288 |
| cD | (i-b) local on s6 | s6 + Ball h 0.04, r 0.3 + 0.3 at both ends of the governing line (bore R0.2 end, flat chamfer end) | 123,321 | 6.65 (7.32) | yes | 2.08-2.68 | 224.9 | 2.222 |
| cD3 | (i-b) local on s6 | s6 + Ball h 0.05, r 0.3 + 0.3 at both ends | 115,587 | 6.21 (6.83) | yes | 1.89-2.43 | 210.9 | 2.206 |
| cD2 | (i-b) local on s6 | s6 + Ball h 0.04, r 0.4 + 0.4 at both ends | 144,295 | 7.86 (8.65) | no | 2.64-3.39 | 262.8 | 2.266 |
| cB | (i-b) local on s6 | s6 + Ball h 0.04, r 0.45 + 0.5 at the bore end only | 131,872 | 7.14 (7.86) | yes | 2.3-2.96 | 240.4 | 2.24 |
| cB2 | (i-b) local on s6 | s6 + Ball h 0.04, r 0.3 + 0.3 at the bore end only | 115,207 | 6.19 (6.81) | yes | 1.88-2.42 | 210.2 | 2.205 |
