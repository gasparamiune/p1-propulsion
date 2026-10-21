# J-FWD envelope delta v6 against v4 [DERIVED]

Old `jfwd_soak_envelope_v352_v4.json` `9d9fd8ee991f9887`; new `jfwd_soak_envelope_v352_v6.json` `43a5d78b67c615fc`. Only changed quantities are listed; lines = the 54 seat lines' envelope MS (P+Q <= 2 Fty(T)) at 3 decimals.

| state | quantity | old (from) | new (from) |
|---|---|---|---|
| PRELOAD | max_spread_MS | 1.885 | 1.688 |
| PRELOAD | seat lines lower / higher / equal | | 21 / 0 / 33 |
| SOAK70 | window_max_N | 3123.4 (b2) | 3151.1 (cD) |
| SOAK70 | max_spread_MS | 0.427 | 0.504 |
| SOAK70 | M_max_threaded_max_Nmm | 2912.3 (b2) | 3095.9 (cD) |
| SOAK70 | seat lines lower / higher / equal | | 15 / 0 / 39 |
| SOAK | max_spread_MS | 1.013 | 0.994 |
| SOAK | seat lines lower / higher / equal | | 21 / 0 / 33 |
| SOAK52 | lines_min_MS_PQ | -0.011 (b2) 6.051 0.0 | -0.03 (b1) 6.051 0.0 |
| SOAK52 | max_spread_MS | 0.637 | 0.676 |
| SOAK52 | seat lines lower / higher / equal | | 23 / 0 / 31 |
| FA1S | N_min_N | 2734.6 (b2) | 2728.5 (cD) |
| FA1S | window_min_N | 462.5 (b2) | 455.0 (cD) |
| FA1S | max_spread_MS | 0.557 | 0.461 |
| FA1S | seat lines lower / higher / equal | | 34 / 0 / 20 |

Note: cD (seat_sDL12_mu0, FINAL TC-01, mu 0) enters v6 for its resultants only, as solved, like (b2') in v5 (lead 2026-10-21T05:17:36Z (3)); its seat lines are recorded in v6 'cD_check' (02:01:34Z (C) rule: s6 + C1 stand in every state) and are not entered, so no seat line moves through cD. One-side check: the first version of scripts/jfwd_cD_result_v352.py (a2d5c42150d9a5c8; its outputs efe65cacb656ee4f / 0d9d5d89e4b9da74, not cited, overwritten) checked one side of N and of the seat window only (N max, window min) and missed the SOAK70 window max and the FA1S N min; the version used (6dfd6d331b946b48; results/v352/jfwd_cD_result_v352.json 8209e80f09f28af7) checks both sides. Recorded for Mechanical, outside envelope{}: SOAK70 M max over the screw shank in TC-01 3415.2 N mm (b2) -> 3438.9 N mm (cD), both at x' 30.5 (Mechanical's v7 input M_max; v6 'M_max_shank_in_TC01_Nmm', 'v5_to_v6').

Nothing here is physical approval.
