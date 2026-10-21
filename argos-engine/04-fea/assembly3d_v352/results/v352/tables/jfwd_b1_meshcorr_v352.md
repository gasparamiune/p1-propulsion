# (b1) s6 / s9 mesh correction, 240 (9)(v): C1 ADOPTED (lead 2026-10-21T01:30:18Z (5)); DERIVED

(b2') `seat_s9L12_mu0` FAILS the 5 % rule against (b2) `seat_s6L12_mu0` at PRELOAD and FA1S (judge `judge_seat_s6L12_mu0.json` 3619a7b39613edf0). s6 is the finer break mesh (h_brk 0.08 mm; L12 patch 107,611 nodes), s9 the coarser (h_brk 0.15 mm; 60,812 nodes). C1: (b1) line stresses x max(1, r), r = PmPb(b2) / PmPb(b2') per line and state; repeats take their state's ratio [ASSUMED]. C2 = sensitivity only. Envelope v4 `9d9fd8ee991f9887` for comparison. [SIM inputs; DERIVED values; extrapolation ESTIMATE]

## s6 / s9 PmPb ratio at mu 0, per state (54 lines)

| state | governing line d+6.051 z'0 | min | max | lines r > 1 | lines floored (r < 1) |
|---|---|---|---|---|---|
| PRELOAD | 1.1781 | 0.9724 | 1.1781 | 53 / 54 | 1 |
| SOAK52 | 1.1244 | 0.9871 | 1.1244 | 47 / 54 | 7 |
| SOAK | 1.1262 | 0.9820 | 1.1262 | 49 / 54 | 5 |
| SOAK70 | 1.1235 | 0.9829 | 1.1235 | 47 / 54 | 6 |
| FA1S | 1.1194 | 0.9915 | 1.1194 | 52 / 54 | 2 |

## (b1) seat lines: as solved (C0), C1 (ADOPTED), C2 (sensitivity)

| state | instance | C0 min MS (line) | C1 min MS (line) | C1 governing line PmPb MPa (MS) | C2 min MS (sensitivity) | v4 envelope min MS (from) |
|---|---|---|---|---|---|---|
| PRELOAD | (b1) | +1.423 (d-6.051_z+0.0) | +1.189 (d+6.051_z+0.0) | 219.2 (+1.189) | +1.189 (d+6.051_z+0.0) | +1.038 ((b2)) |
| SOAK52 | (b1) | +0.036 (d-6.051_z+0.0) | -0.030 (d+6.051_z+0.0) | 370.3 (-0.030) | -0.074 (d+6.051_z+0.0) | -0.011 ((b2)) |
| SOAK52 | (b1) rep | +0.095 (d-6.051_z+0.0) | +0.035 (d+6.051_z+0.0) | 347.1 (+0.035) | -0.012 (d+6.051_z+0.0) | -0.011 ((b2)) |
| SOAK | (b1) | +0.014 (d-6.051_z+0.0) | -0.041 (d+6.051_z+0.0) | 355.3 (-0.041) | -0.083 (d+6.051_z+0.0) | -0.071 ((b2) rep) |
| SOAK | (b1) rep | -0.002 (d-6.051_z+0.0) | -0.039 (d+6.051_z+0.0) | 354.5 (-0.039) | -0.082 (d+6.051_z+0.0) | -0.071 ((b2) rep) |
| SOAK70 | (b1) | +0.039 (d-6.051_z+0.0) | -0.016 (d+6.051_z+0.0) | 347.7 (-0.016) | -0.062 (d+6.051_z+0.0) | -0.055 ((b2)) |
| FA1S | (b1) | +0.147 (d-6.051_z+0.0) | +0.068 (d+6.051_z+0.0) | 442.4 (+0.068) | +0.014 (d+6.051_z+0.0) | +0.053 ((b2)) |

## Envelope state minimum with (b1) at C1 (and the C2 sensitivity)

| state | v4 min MS (from) | with C1: min (line, instance) | C1 lines below v4 | C2 sensitivity: min | band anchor with C1: PmPb max (from) / MS min (from) |
|---|---|---|---|---|---|
| PRELOAD | +1.038 ((b2)) | +1.038 ((b2); v4 stands) | 20 | +1.038 | 235.5 ((b2)) / +1.038 ((b2)) |
| SOAK52 | -0.011 ((b2)) | -0.030 (d+6.051_z+0.0, SOAK52 C1; moves) | 23 | -0.074 (moves) | 370.3 ((b1)) / -0.030 ((b1)) |
| SOAK | -0.071 ((b2) rep) | -0.071 ((b2) rep; v4 stands) | 20 | -0.083 (moves) | 366.8 ((b2) rep) / -0.071 ((b2) rep) |
| SOAK70 | -0.055 ((b2)) | -0.055 ((b2); v4 stands) | 13 | -0.062 (moves) | 362.1 ((b2)) / -0.055 ((b2)) |
| FA1S | +0.053 ((b2)) | +0.053 ((b2); v4 stands) | 32 | +0.014 (moves) | 448.3 ((b2)) / +0.053 ((b2)) |

## Not shown converged (5b): two-mesh extrapolation on the governing line d+6.051 z'0 [ESTIMATE; p ASSUMED; h ratio 0.15 / 0.08]

| state | s9 PmPb | s6 PmPb (as found) | s6 / s9 | p = 1 factor | p = 1 PmPb (MS on (b2)) | p = 2 factor | p = 2 PmPb (MS on (b2)) | band anchor (from) | anchor x p1 / x p2 | band MS min (from) -> p1 / p2 |
|---|---|---|---|---|---|---|---|---|---|---|
| PRELOAD | 199.9 | 235.5 (+1.038) | 1.1781 | 1.1728 | 276.2 (+0.738) | 1.0601 | 249.7 (+0.922) | 235.5 ((b2)) | 276.2 / 249.7 | +1.038 ((b2)) -> +0.738 / +0.922 |
| SOAK52 | 323.1 | 363.3 (-0.011) | 1.1244 | 1.1265 | 409.2 (-0.122) | 1.0440 | 379.3 (-0.053) | 370.3 ((b1)) | 417.1 / 386.6 | -0.030 ((b1)) -> -0.139 / -0.071 |
| SOAK | 324.1 | 365.0 (-0.067) | 1.1262 | 1.1281 | 411.7 (-0.173) | 1.0445 | 381.3 (-0.107) | 366.8 ((b2) rep) | 413.8 / 383.1 | -0.071 ((b2) rep) -> -0.176 / -0.111 |
| SOAK70 | 322.3 | 362.1 (-0.055) | 1.1235 | 1.1256 | 407.6 (-0.160) | 1.0437 | 377.9 (-0.095) | 362.1 ((b2)) | 407.6 / 377.9 | -0.055 ((b2)) -> -0.160 / -0.095 |
| FA1S | 400.5 | 448.3 (+0.053) | 1.1194 | 1.1219 | 502.9 (-0.061) | 1.0424 | 467.3 (+0.010) | 448.3 ((b2)) | 502.9 / 467.3 | +0.053 ((b2)) -> -0.061 / +0.010 |

## (b1) resultants as solved, with the mu 0 s6 / s9 resultant ratio per state (disclosure; not corrected)

| state | instance | N plane N | V plane N | seat window N | M x' 28.6 N mm | M_max threaded N mm | ratio N / V / window / M28.6 / M_max thr |
|---|---|---|---|---|---|---|---|
| PRELOAD | (b1) | 3750.0 | 748.5 | 1270.3 | 2517.1 | 2517.1 | 1.000 / n/a / 0.874 / 1.577 / 1.404 |
| SOAK52 | (b1) | 4801.9 | 949.4 | 630.2 | 1054.9 | 1229.0 | 1.044 / 1.226 / 1.099 / 1.077 / 1.026 |
| SOAK52 | (b1) rep | 5600.5 | 1090.7 | 1503.8 | 125.3 | 1385.6 | 1.044 / 1.226 / 1.099 / 1.077 / 1.026 |
| SOAK | (b1) | 6554.3 | 1324.6 | 2437.2 | 5078.6 | 5078.6 | 0.993 / 1.188 / 0.808 / 1.741 / 1.476 |
| SOAK | (b1) rep | 6515.1 | 1314.5 | 2395.4 | 5028.7 | 5028.7 | 0.993 / 1.188 / 0.808 / 1.741 / 1.476 |
| SOAK70 | (b1) | 5614.0 | 1096.5 | 1505.0 | 235.3 | 1445.8 | 1.039 / 0.462 / 1.061 / 1.033 / 0.966 |
| FA1S | (b1) | 2963.9 | 4079.2 | 1088.9 | 4239.8 | 4239.8 | 0.952 / 0.993 / 0.622 / 0.978 / 0.981 |

## Flags: governing resultants the s6 / s9 ratio would make more than 5 % more severe (01:30:18Z (5))

| state | quantity | (b1) instance | as solved | ratio | scaled | envelope governing (from) | (b1) governs now | more severe by |
|---|---|---|---|---|---|---|---|---|
| PRELOAD | M_x28.6_Nmm max | (b1) | 2517.1 | 1.577 | 3970.5 | 2517.1 ((b1)) | yes | 57.7 % |
| PRELOAD | M_max_threaded_Nmm max | (b1) | 2517.1 | 1.404 | 3533.0 | 2517.1 ((b1)) | yes | 40.4 % |
| SOAK | M_x28.6_Nmm max | (b1) | 5078.6 | 1.741 | 8843.9 | 5078.6 ((b1)) | yes | 74.1 % |
| SOAK | M_x28.6_Nmm max | (b1) rep | 5028.7 | 1.741 | 8757.0 | 5078.6 ((b1)) | no | 72.4 % |
| SOAK | M_max_threaded_Nmm max | (b1) | 5078.6 | 1.476 | 7498.0 | 5078.6 ((b1)) | yes | 47.6 % |
| SOAK | M_max_threaded_Nmm max | (b1) rep | 5028.7 | 1.476 | 7424.4 | 5078.6 ((b1)) | no | 46.2 % |
