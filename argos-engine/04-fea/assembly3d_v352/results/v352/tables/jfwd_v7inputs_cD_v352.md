# J-FWD: Mechanical's v7-quantity inputs on the final envelope v6, with cD [SIM values; DERIVED]

Mechanical's re-map input record together with `results/v352/jfwd_soak_envelope_v352_v6.json` `43a5d78b67c615fc` (lead 2026-10-21T05:27Z (3)). Base: `jfwd_v7inputs_c1_v352.json` `384c1a472add7a4c` (C1 seat-line view). Resultant-type inputs take cD as an instance as solved (05:27Z (2)); the UH band and the seat line keep the base value with cD's refined-mesh value beside (05:27Z (1); 02:01:34Z (C)).

## Final inputs, v7 convention (all instances; cD in the resultant-type inputs)

| state | N_head max (from) | N_head min (from) | seat window min (from) | M_max N mm (from, x') | N_section max | spread N | seat line PmPb / MS (from) | UH band strain MS min (from) |
|---|---|---|---|---|---|---|---|---|
| PRELOAD | 3750.2 ((a)) | 3749.9 (js5) | 901.4 ((b2)) | 2530.8 ((b1), 28.7) | 3821.1 | 0.0001 | 235.5 / +1.038 ((b2)) | 6.345 ((b1)) |
| SOAK70 | 7471.8 ((b2)) | 5613.8 ((b1)) | 1351.3 ((a'')) | 3438.9 ((cD), 30.5) | 7535.3 | 0.331 | 362.1 / -0.055 ((b2)) | 0.415 ((b2)) |
| SOAK | 7382.8 (js5) | 5252.5 ((b2)) | 639.4 ((b2)) | 5116.3 ((b1), 28.7) | 7516.7 | 0.4056 | 366.8 / -0.071 ((b2) rep) | 0.502 ((b1)) |
| SOAK52 | 7764.2 ((b2) rep) | 4802.0 ((b1)) | 630.2 ((b1)) | 3186.7 ((b2) rep, 30.5) | 7828.8 | 0.6169 | 370.3 / -0.030 ((b1)) | 0.296 ((b2)) |
| FA1S | 3138.2 (js5) | 2717.2 ((cD)) | 455.0 ((cD)) | 4269.8 ((b1), 28.7) | 3235.7 | 0.1549 | 448.3 / +0.053 ((b2)) | 0.515 ((a)) |

## Inputs cD moves (against the base)

| state | view | input | base (from) | final (from) |
|---|---|---|---|---|
| PRELOAD | - | none | | |
| SOAK70 | primary | M_max_Nmm | 3415.2 ((b2)) | 3438.9 ((cD), x' 30.5) |
| SOAK70 | v7_convention | M_max_Nmm | 3415.2 ((b2)) | 3438.9 ((cD), x' 30.5) |
| SOAK | - | none | | |
| SOAK52 | - | none | | |
| FA1S | primary | N_head_min_N | 2723.1 ((b2)) | 2717.2 ((cD)) |
| FA1S | primary | seat_window_N | 462.5 ((b2)) | 455.0 ((cD)) |
| FA1S | primary | spread_N_rel | 0.1524 | 0.1549 |
| FA1S | v7_convention | N_head_min_N | 2723.1 ((b2)) | 2717.2 ((cD)) |
| FA1S | v7_convention | seat_window_N | 462.5 ((b2)) | 455.0 ((cD)) |
| FA1S | v7_convention | spread_N_rel | 0.1524 | 0.1549 |

## Local values: the base stands, cD beside

| state | UH band strain MS: stands (from) / cD, strain ratio | label | seat line d+6.051 z'0 PmPb stands (from) / cD, cD / s6 |
|---|---|---|---|
| PRELOAD | 6.345 ((b1)) / 7.293, 0.886 | cD refined-mesh local value beside (not lower than the base) | 235.5 ((b2)) / 218.4, 0.927 |
| SOAK70 | 0.415 ((b2)) / 0.474, 0.960 | cD refined-mesh local value beside (not lower than the base) | 362.1 ((b2)) / 347.3, 0.959 |
| SOAK | 0.502 ((b1)) / 0.746, 0.860 | cD refined-mesh local value beside (not lower than the base) | 366.8 ((b2) rep) / 352.7, 0.966 |
| SOAK52 | 0.296 ((b2)) / 0.267, 1.023 | cD refined-mesh local value beside, strain ratio 1.023, within the (C) 5 % band; the MF note applies | 370.3 ((b1)) / 344.1, 0.947 |
| FA1S | 0.515 ((a)) / 0.59, 0.953 | cD refined-mesh local value beside (not lower than the base) | 448.3 ((b2)) / 441.7, 0.985 |

Inputs (sha256/16): {"results/v352/jfwd_v7inputs_c1_v352.json": "384c1a472add7a4c", "scripts/jfwd_v7inputs_v352.py": "653e00189c5c52fc", "results/v352/jfwd_soak_envelope_v352_v6.json": "43a5d78b67c615fc", "results/v352/jfwd_cD_result_v352.json": "8209e80f09f28af7", "seat_sDL12_mu0/seatforce.json": "52ab8f40fae1bb75", "seat_sDL12_mu0/compare.json": "c891db7dcb3445c9", "seat_sDL12_mu0/shank.json": "0ef43b2e27a72e8c", "seat_sDL12_mu0/runcmp_js5_mu0_T3750_g078.json": "9388cce4e668e44d"}

Nothing here is physical approval.
