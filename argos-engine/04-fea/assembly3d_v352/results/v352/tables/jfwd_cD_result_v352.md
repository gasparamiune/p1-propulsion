# cD convergence check on the governing seat line (seat_sDL12_mu0; FINAL TC-01; mu 0) [SIM / DERIVED]

Rule: lead 2026-10-21T02:01:34Z (C). Governing line d+6.051_z+0.0. Envelope compared: jfwd_soak_envelope_v352_v5.json `ef22b59cf2413b46`.

| state | PmPb s9 / s6 / cD (MPa) | MS s9 / s6 / cD | cD / s6 | cD / s9 | verdict | all 54 lines cD / s6 min / median / max (n > 1.05) | cD min-MS line |
|---|---|---|---|---|---|---|---|
| PRELOAD | 199.9 / 235.5 / 218.4 | +1.401 / +1.038 / +1.198 | 0.9274 | 1.0925 | cD lower by more than 5 %: s6 stands (conservative); difference quoted | 0.927 / 1.001 / 1.035 (0) | d-6.051_z+0.0 +1.160 |
| SOAK52 | 323.1 / 363.3 / 344.1 | +0.112 / -0.011 / +0.044 | 0.9472 | 1.0650 | cD lower by more than 5 %: s6 stands (conservative); difference quoted | 0.947 / 0.999 / 1.025 (0) | d+6.051_z+0.0 +0.044 |
| SOAK | 324.1 / 365.0 / 352.7 | +0.051 / -0.067 / -0.034 | 0.9663 | 1.0882 | within 5 %: s6 and C1 stand (check passed on the final geometry) | 0.966 / 0.999 / 1.041 (0) | d-6.051_z+0.0 -0.047 |
| SOAK70 | 322.3 / 362.1 / 347.3 | +0.061 / -0.055 / -0.015 | 0.9591 | 1.0776 | within 5 %: s6 and C1 stand (check passed on the final geometry) | 0.959 / 0.998 / 1.029 (0) | d+6.051_z+0.0 -0.015 |
| FA1S | 400.5 / 448.3 / 441.7 | +0.179 / +0.053 / +0.069 | 0.9853 | 1.1029 | within 5 %: s6 and C1 stand (check passed on the final geometry) | 0.978 / 1.002 / 1.036 (0) | d+6.051_z+0.0 +0.069 |

Resultants of cD against the envelope (as solved) [SIM]:

| state | N plane (env min / max) | window (env min / max) | M x' 28.6 (env max) | M max thread (env max) | outside the envelope |
|---|---|---|---|---|---|
| PRELOAD | 3750.0 (3750.0 / 3750.0) | 908.8 (901.4 / 1270.3) | 425.4 (2517.1) | 425.4 (2517.1) | none |
| SOAK52 | 6227.9 (4801.9 / 7764.0) | 1824.8 (630.2 / 3413.0) | 2116.5 (2915.7) | 2116.5 (2728.7) | none |
| SOAK | 5264.4 (5252.3 / 7382.9) | 659.5 (639.4 / 3125.9) | 714.6 (5078.6) | 714.6 (5078.6) | none |
| SOAK70 | 7464.9 (5614.0 / 7471.8) | 3151.1 (1351.3 / 3123.4) | 3095.9 (3111.7) | 3095.9 (3013.4) | window_max, M_max_threaded |
| FA1S | 2728.5 (2734.6 / 3147.9) | 455.0 (462.5 / 1272.3) | 2607.5 (4239.8) | 2708.3 (4239.8) | N_min, window_min |

Boundary extrapolation (`jfwd_patch_extrap_nodes_v352.json`): s6L12 max 0.0188 mm, 7 nodes > 0.01 mm, nearest 9.67 mm from a Ball centre, on the flat region: False; s9L12 max 0.0295 mm, 15 nodes > 0.01 mm, nearest 3.14 mm from a Ball centre, on the flat region: False; sDL12 max 0.0431 mm, 9 nodes > 0.01 mm, nearest 6.02 mm from a Ball centre, on the flat region: False.

Inputs (sha256/16): {"seat_sDL12_mu0/compare.json": "c891db7dcb3445c9", "seat_sDL12_mu0/shank.json": "0ef43b2e27a72e8c", "seat_sDL12_mu0/seatforce.json": "52ab8f40fae1bb75", "seat_s6L12_mu0/compare.json": "727e10ba6c8fb41b", "seat_s6L12_mu0/shank.json": "280e383e5b87dd07", "seat_s6L12_mu0/seatforce.json": "9eb36a729ef6b5a5", "seat_s9L12_mu0/compare.json": "0ae76ed185599268", "seat_s9L12_mu0/shank.json": "c402e74c125b5182", "seat_s9L12_mu0/seatforce.json": "722b28f49473b8dc", "seat_sDL12_mu0/judge_seat_s6L12_mu0.json": "eeb9067f1c3400db", "seat_sDL12_mu0/judge_seat_s9L12_mu0.json": "beebcbed7eeb845c", "seat_sDL12_mu0/ccx_run.json": "8e044cd991afe0bc", "seat_sDL12_mu0/meta.json": "675917103538c9b3", "seat_sDL12_mu0/COMPRESSED.txt": "a4f2553d80adb556", "seat_sDL12_mu0/DECK_XZ.txt": "cdfa5176ab26cee7", "jfwd_soak_envelope_v352_v5.json": "ef22b59cf2413b46", "jfwd_patch_extrap_nodes_v352.json": "f95abde5b1489976"}

Nothing here is physical approval.
