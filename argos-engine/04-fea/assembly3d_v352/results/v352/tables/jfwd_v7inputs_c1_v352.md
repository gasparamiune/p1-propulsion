# J-FWD final-envelope inputs in Mechanical's v7 quantities (FEA3D-2, 2026-10-21)

Mechanical v7 `jfwd_relax_v352_v7.json` 345e27062d54ad20 (script 82221fdf0035f338); FEA3D runs read-only, fit 0.078 throughout, no new run. Instances: v7 = js5, (a), (a'), (a''), (b2), (b2) rep; added = (b1), (b1) rep, (b2'); pending = none. Step 1 reproduces v7's history_envelope and crosscheck exactly (extraction check). [SIM values; DERIVED envelopes]

## Per instance (v7 definitions)

| state | instance | form | N_head N | seat window N | seat line d+6.051 z'0 PmPb MPa | MS_PQ | M_max N mm (x') | step |
|---|---|---|---|---|---|---|---|---|
| PRELOAD | js5 | s5 global, sharp, mu 0 | 3749.9 | 1118.6 | 226.5 | +1.119 | 298.7 (28.3) | PRELOAD |
| PRELOAD | (a) | s5 L8, sharp, mu 0 | 3750.2 | 1172.2 | 222.5 | +1.157 | 318.8 (28.3) | PRELOAD |
| PRELOAD | (a') | s5 L8 js5 order, sharp, mu 0 | 3750.1 | 1198.7 | 227.1 | +1.114 | 651.5 (28.8) | PRELOAD |
| PRELOAD | (a'') | s5 L12 js5 order, sharp, mu 0 | 3750.1 | 1173.6 | 225.4 | +1.130 | 823.6 (28.8) | PRELOAD |
| PRELOAD | (b2) | s6 L12, R0.2, mu 0 | 3749.9 | 901.4 | 235.5 | +1.038 | 458.7 (30.5) | PRELOAD |
| PRELOAD | (b1) | s9 L12, R0.2, mu 0.2 | 3750.1 | 1270.3 | 186.1 | +1.579 | 2530.8 (28.7) | PRELOAD |
| PRELOAD | (b2') | s9 L12, R0.2, mu 0 | 3749.9 | 1031.2 | 199.9 | +1.401 | 301.3 (30.5) | PRELOAD |
| SOAK70 | js5 | s5 global, sharp, mu 0 | 5694.7 | 1400.3 | 345.7 | -0.011 | 1295.5 (30.5) | SOAK70 |
| SOAK70 | (a) | s5 L8, sharp, mu 0 | 6389.1 | 2385.0 | 323.1 | +0.058 | 2378.2 (30.5) | SOAK70 |
| SOAK70 | (a') | s5 L8 js5 order, sharp, mu 0 | 5627.3 | 1364.0 | 348.8 | -0.019 | 1286.8 (30.5) | SOAK70 |
| SOAK70 | (a'') | s5 L12 js5 order, sharp, mu 0 | 5623.6 | 1351.3 | 347.6 | -0.016 | 1273.3 (30.5) | SOAK70 |
| SOAK70 | (b2) | s6 L12, R0.2, mu 0 | 7471.8 | 3123.4 | 362.1 | -0.055 | 3415.2 (30.5) | SOAK70 |
| SOAK70 | (b1) | s9 L12, R0.2, mu 0.2 | 5613.8 | 1505.0 | 309.5 | +0.105 | 2235.5 (31.0) | SOAK70 |
| SOAK70 | (b2') | s9 L12, R0.2, mu 0 | 7190.1 | 2944.8 | 322.3 | +0.061 | 3251.6 (30.5) | SOAK70 |
| SOAK | js5 | s5 global, sharp, mu 0 | 7382.8 | 3125.9 | 326.8 | +0.042 | 3855.3 (30.5) | SOAK |
| SOAK | (a) | s5 L8, sharp, mu 0 | 6010.3 | 1324.9 | 343.9 | -0.010 | 1215.0 (28.3) | SOAK |
| SOAK | (a') | s5 L8 js5 order, sharp, mu 0 | 5780.1 | 1223.7 | 352.9 | -0.035 | 908.6 (28.2) | SOAK |
| SOAK | (a'') | s5 L12 js5 order, sharp, mu 0 | 5558.8 | 1225.7 | 352.9 | -0.035 | 543.8 (31.0) | SOAK |
| SOAK | (b2) | s6 L12, R0.2, mu 0 | 5252.5 | 639.4 | 365.0 | -0.067 | 666.8 (30.5) | SOAK |
| SOAK | (b2) rep | s6 L12, R0.2, mu 0 (repeat) | 6336.7 | 1760.7 | 366.8 | -0.071 | 1358.7 (29.4) | SOAK_rep |
| SOAK | (b1) | s9 L12, R0.2, mu 0.2 | 6554.6 | 2437.2 | 315.5 | +0.080 | 5116.3 (28.7) | SOAK |
| SOAK | (b1) rep | s9 L12, R0.2, mu 0.2 (repeat) | 6515.2 | 2395.4 | 314.8 | +0.082 | 5065.7 (28.7) | SOAK_rep |
| SOAK | (b2') | s9 L12, R0.2, mu 0 | 5289.1 | 791.1 | 324.1 | +0.051 | 402.0 (28.0) | SOAK |
| SOAK52 | js5 | s5 global, sharp, mu 0 | 6559.9 | 2337.1 | 347.5 | +0.034 | 2669.2 (30.5) | SOAK52 |
| SOAK52 | (a) | s5 L8, sharp, mu 0 | 5826.2 | 1332.0 | 345.2 | +0.041 | 1528.6 (30.5) | SOAK52 |
| SOAK52 | (a') | s5 L8 js5 order, sharp, mu 0 | 6742.0 | 2524.2 | 320.9 | +0.120 | 2770.6 (30.5) | SOAK52 |
| SOAK52 | (a'') | s5 L12 js5 order, sharp, mu 0 | 6719.5 | 2497.9 | 321.5 | +0.118 | 2793.1 (30.5) | SOAK52 |
| SOAK52 | (b2) | s6 L12, R0.2, mu 0 | 6228.4 | 1802.8 | 363.3 | -0.011 | 2295.3 (29.1) | SOAK52 |
| SOAK52 | (b2) rep | s6 L12, R0.2, mu 0 (repeat) | 7764.2 | 3413.0 | 342.7 | +0.048 | 3186.7 (30.5) | SOAK52_rep |
| SOAK52 | (b1) | s9 L12, R0.2, mu 0.2 | 4802.0 | 630.2 | 329.3 | +0.091 | 1229.0 (26.6) | SOAK52 |
| SOAK52 | (b1) rep | s9 L12, R0.2, mu 0.2 (repeat) | 5600.6 | 1503.8 | 308.7 | +0.164 | 2330.4 (31.0) | SOAK52_rep |
| SOAK52 | (b2') | s9 L12, R0.2, mu 0 | 5964.1 | 1641.0 | 323.1 | +0.112 | 2098.0 (30.5) | SOAK52 |
| FA1S | js5 | s5 global, sharp, mu 0 | 3138.2 | 1154.1 | 430.3 | +0.097 | 2984.6 (28.6) | FA1S |
| FA1S | (a) | s5 L8, sharp, mu 0 | 3124.5 | 1272.3 | 425.1 | +0.111 | 2926.2 (28.6) | FA1S |
| FA1S | (a') | s5 L8 js5 order, sharp, mu 0 | 3096.0 | 1243.9 | 430.0 | +0.098 | 2979.9 (28.6) | FA1S |
| FA1S | (a'') | s5 L12 js5 order, sharp, mu 0 | 3088.0 | 1126.1 | 428.7 | +0.101 | 2990.9 (28.6) | FA1S |
| FA1S | (b2) | s6 L12, R0.2, mu 0 | 2723.1 | 462.5 | 448.3 | +0.053 | 2727.9 (28.7) | FA1S |
| FA1S | (b1) | s9 L12, R0.2, mu 0.2 | 3065.7 | 1088.9 | 395.2 | +0.195 | 4269.8 (28.7) | FA1S |
| FA1S | (b2') | s9 L12, R0.2, mu 0 | 2861.0 | 744.2 | 400.5 | +0.179 | 2778.9 (28.6) | FA1S |

## Envelope per state (primary = no repeats; rep = SOAK_rep / SOAK52_rep rows; v7 convention = both)

| state | view | N_head max (from) | N_head min (from) | window min (from) | seat-line PmPb max (from) | MS_PQ min (from) | M_max (from) |
|---|---|---|---|---|---|---|---|
| PRELOAD | primary | 3750.2 ((a)) | 3749.9 (js5) | 901.4 ((b2)) | 235.5 ((b2)) | +1.038 ((b2)) | 2530.8 ((b1)) |
| PRELOAD | v7_convention | 3750.2 ((a)) | 3749.9 (js5) | 901.4 ((b2)) | 235.5 ((b2)) | +1.038 ((b2)) | 2530.8 ((b1)) |
| SOAK70 | primary | 7471.8 ((b2)) | 5613.8 ((b1)) | 1351.3 ((a'')) | 362.1 ((b2)) | -0.055 ((b2)) | 3415.2 ((b2)) |
| SOAK70 | v7_convention | 7471.8 ((b2)) | 5613.8 ((b1)) | 1351.3 ((a'')) | 362.1 ((b2)) | -0.055 ((b2)) | 3415.2 ((b2)) |
| SOAK | primary | 7382.8 (js5) | 5252.5 ((b2)) | 639.4 ((b2)) | 365.0 ((b2)) | -0.067 ((b2)) | 5116.3 ((b1)) |
| SOAK | rep | 6515.2 ((b1) rep) | 6336.7 ((b2) rep) | 1760.7 ((b2) rep) | 366.8 ((b2) rep) | -0.071 ((b2) rep) | 5065.7 ((b1) rep) |
| SOAK | v7_convention | 7382.8 (js5) | 5252.5 ((b2)) | 639.4 ((b2)) | 366.8 ((b2) rep) | -0.071 ((b2) rep) | 5116.3 ((b1)) |
| SOAK52 | primary | 6742.0 ((a')) | 4802.0 ((b1)) | 630.2 ((b1)) | 363.3 ((b2)) | -0.011 ((b2)) | 2793.1 ((a'')) |
| SOAK52 | rep | 7764.2 ((b2) rep) | 5600.6 ((b1) rep) | 1503.8 ((b1) rep) | 342.7 ((b2) rep) | +0.048 ((b2) rep) | 3186.7 ((b2) rep) |
| SOAK52 | v7_convention | 7764.2 ((b2) rep) | 4802.0 ((b1)) | 630.2 ((b1)) | 363.3 ((b2)) | -0.011 ((b2)) | 3186.7 ((b2) rep) |
| FA1S | primary | 3138.2 (js5) | 2723.1 ((b2)) | 462.5 ((b2)) | 448.3 ((b2)) | +0.053 ((b2)) | 4269.8 ((b1)) |
| FA1S | v7_convention | 3138.2 (js5) | 2723.1 ((b2)) | 462.5 ((b2)) | 448.3 ((b2)) | +0.053 ((b2)) | 4269.8 ((b1)) |

## v7 inputs that move (v7 convention)

- PRELOAD M_max_Nmm: v7 823.6 (patch_a3) -> 2530.8 ((b1)); delta +1707.2 (+207.3 %)
- PRELOAD UH_band_MS_strain_min: v7 7.083 (patch_b2) -> 6.345 ((b1)); delta -0.738 (-10.4 %)
- SOAK70 N_head_min_N: v7 5623.6 (patch_a3) -> 5613.8 ((b1)); delta -9.8 (-0.2 %)
- SOAK70 spread_N_rel: v7 0.3287 (None) -> 0.331 (None); delta +0.0023 (+0.7 %)
- SOAK M_max_Nmm: v7 3855.3 (js5) -> 5116.3 ((b1)); delta +1261.0 (+32.7 %)
- SOAK UH_band_MS_strain_min: v7 0.738 (patch_b2) -> 0.502 ((b1)); delta -0.236 (-32.0 %)
- SOAK52 N_head_min_N: v7 5826.2 (patch_a) -> 4802.0 ((b1)); delta -1024.2 (-17.6 %)
- SOAK52 seat_window_N: v7 1332.0 (patch_a) -> 630.2 ((b1)); delta -701.8 (-52.7 %)
- SOAK52 spread_N_rel: v7 0.3326 (None) -> 0.6169 (None); delta +0.2843 (+85.5 %)
- FA1S M_max_Nmm: v7 2990.9 (patch_a3) -> 4269.8 ((b1)); delta +1278.9 (+42.8 %)
- FA1S N_section_max_N: v7 3211.6 (None) -> 3235.7 (None); delta +24.1 (+0.8 %)

## C1 view (lead 01:30:18Z (5), C1 ADOPTED): (b1) seat line at x max(1, s6/s9) [DERIVED]; resultants as solved

| state | instance | as solved PmPb MPa (MS) | ratio floored | C1 PmPb MPa (MS) |
|---|---|---|---|---|
| PRELOAD | (b1) | 186.1 (+1.579) | 1.1781 | 219.2 (+1.189) |
| SOAK70 | (b1) | 309.5 (+0.105) | 1.1235 | 347.7 (-0.016) |
| SOAK | (b1) | 315.5 (+0.080) | 1.1262 | 355.3 (-0.041) |
| SOAK | (b1) rep | 314.8 (+0.082) | 1.1262 | 354.5 (-0.039) |
| SOAK52 | (b1) | 329.3 (+0.091) | 1.1244 | 370.3 (-0.030) |
| SOAK52 | (b1) rep | 308.7 (+0.164) | 1.1244 | 347.1 (+0.035) |
| FA1S | (b1) | 395.2 (+0.195) | 1.1194 | 442.4 (+0.068) |

| state | view | seat-line PmPb max (from) | MS_PQ min (from) |
|---|---|---|---|
| PRELOAD | primary | 235.5 ((b2)) | +1.038 ((b2)) |
| PRELOAD | v7_convention | 235.5 ((b2)) | +1.038 ((b2)) |
| SOAK70 | primary | 362.1 ((b2)) | -0.055 ((b2)) |
| SOAK70 | v7_convention | 362.1 ((b2)) | -0.055 ((b2)) |
| SOAK | primary | 365.0 ((b2)) | -0.067 ((b2)) |
| SOAK | rep | 366.8 ((b2) rep) | -0.071 ((b2) rep) |
| SOAK | v7_convention | 366.8 ((b2) rep) | -0.071 ((b2) rep) |
| SOAK52 | primary | 370.3 ((b1)) | -0.030 ((b1)) |
| SOAK52 | rep | 347.1 ((b1) rep) | +0.035 ((b1) rep) |
| SOAK52 | v7_convention | 370.3 ((b1)) | -0.030 ((b1)) |
| FA1S | primary | 448.3 ((b2)) | +0.053 ((b2)) |
| FA1S | v7_convention | 448.3 ((b2)) | +0.053 ((b2)) |

C1 view, v7 inputs that move (v7 convention; the seat-line rows only differ from the as-solved list above):

- SOAK52 seat_line_PmPb_MPa: v7 363.3 (None) -> 370.3 ((b1)); delta +7.0 (+1.9 %)
- SOAK52 seat_line_MS_PQ: v7 -0.011 (patch_b2) -> -0.03 ((b1)); delta -0.019 (-172.7 %)
