# Engine mounting data (datasheet), v3.5.2 re-check with RM2-11 folded

Generated 2026-10-20T23:06:59Z by scripts/icd_export_v352.py from the f1.dat reaction totals of the listed runs (SIM unless tagged). 16 radial M5 holes: GM-09 forward ring z +27 mm, GM-10 aft ring z -94.8 mm. Forces of the engine module ON the airframe; radial + = pull-out; shear = hypot(tangential, axial) in the radial screw.

**Header (RM2-11).**
- Included mass: the forces include the FE model mass. v3.5.1 model (c71): **4.103 kg** (engine 2.886, ring 0.217, fixed 0.971, horns 0.029 kg). v3.5.2 model: **4.033 kg** L1 (engine 2.829) / **4.030 kg** rev-3 R3 pose model (engine 2.827); ring 0.217, fixed 0.957, horns 0.029 kg [DERIVED, mass.json].
- Excluded: **1.31 kg** of airframe-wall equipment (massprops wet fixed group minus the model's fixed group: 2.2805 - 0.9706 = 1.3099 kg v3.5.1; 2.2669 - 0.9570 = 1.3099 kg v3.5.2). Its inertia loads go into the airframe wall directly, not through these 16 holes.
- Sub-cases: FA1Q / FA1D / FA1U / FA1S are pressure only (no inertia). The LC2F envelope (908 N) is its thrust-only sub-case: GZ 0 bounds, because inertia opposes thrust.
- Rigid against compliant airframe: the rigid airframe bounds the maximum hole load, but not every hole. The per-hole datasheet rows are the ENVELOPE of the rigid and the compliant airframe (k_af 2e3 / 2e4 / 2e4 N/mm, ASSUMED). Compliant coverage: LC1 at B1_21.65 (lc1v351_compliant_c71) and LC3 at stop045 only (pose_stop045_compliant_c71); every other case and pose is rigid only.
- v3.5.2: no compliant run. The v3.5.2 datasheet rows are the envelope of the v3.5.2 rigid rows and the v3.5.1 compliant rows (carried, marked c351; model mass 4.103 vs 4.030 kg, OP net 202.925 vs 202.50 N/MPa).

## v3.5.2 model: DATASHEET per-hole values, governing [DERIVED] (lead 22:54:03Z)

Governing = the larger of the as-found value (SIM, the table further down) and the moment-free estimate (section 'OP-moment residue' below), per hole and component, then enveloped with the carried v3.5.1 compliant rows (c351) as before. The as-found value carries a non-physical OP couple; the estimate rests on an ASSUMED transfer (the residue as the rod-force pair it produces, hole reactions from the EAX / EAY unit steps). LC1 / LC2 / FA-1 (L1 global): estimate = OP moment zero, transferred through pose_neutral_v352r3R3's EA steps (ASSUMED). LC3 / F2 (R3 poses): both estimates (two TC-09 faces at p/Pc 1.0; OP moment zero), so the governing value bounds every value shown. Pull-out, axial and the other components follow the same rule.

Cell = max shear / max |axial| / max pull-out, N; ! = an estimate governs that value by 0.5 N or more; * = a compliant-airframe value exceeds the rigid governing one by more than 1 N and 5 %.

| hole (x, y, z mm) | LC1 | LC2 | FA1Q | FA1D | FA1U | FA1S | FA1T | LC3 | GS | TD0 | TDP | LC6 | LC2F |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AF_GM09_0 (59.4, 24.6, 27.0) | 76! / 68! / 20! | 150! / 136! / 33! | 348! / 320! / 64! | 448! / 412! / 82! | 544! / 500! / 99! | 559! / 514! / 102! | 657! / 604! / 120! | 306! / 303 / 295 | 333 / 298 / 86 | 113 / 91 / 88 | 186! / 157! / 120! | 79 / 69 / 44 | 197! / 175! / 75! |
| AF_GM09_1 (24.6, 59.4, 27.0) | 5 / 3 / 0 * | 5 / 5 / 0 | 10! / 9! / 0 | 13! / 12! / 0 | 16! / 14! / 0 | 16! / 14! / 0 | 19! / 17! / 0 | 102 / 16 / 20! * | 10 / 9 / 5 | 6 / 4 / 6 | 9 / 6! / 7 | 3 / 2 / 2 | 7! / 6! / 4 |
| AF_GM09_2 (-24.6, 59.4, 27.0) | 3 / 3 / 0 | 5 / 5 / 0 | 10! / 9! / 0 | 14! / 12! / 0 | 16! / 14! / 0 | 17! / 15! / 0 | 20! / 18! / 0 | 72 / 7 / 5 * | 10 / 9 / 1 | 2 / 2 / 2 | 5! / 4! / 2 | 1 / 1 / 1 | 5! / 5! / 0 |
| AF_GM09_3 (-59.4, 24.6, 27.0) | 71! / 65! / 14! | 143! / 131! / 27! | 336! / 310! / 61! | 434! / 400! / 78! | 527! / 486! / 95! | 542! / 499! / 98! | 638! / 588! / 115! | 323! / 269 / 94! | 338 / 301 / 74 | 118 / 95 / 31 | 176! / 149! / 48! | 78 / 68 / 20 | 191! / 170! / 42! |
| AF_GM09_4 (-59.4, -24.6, 27.0) | 76! / 69! / 15! | 149! / 136! / 28! | 346! / 320! / 62! | 446! / 411! / 79! | 541! / 499! / 96! | 556! / 513! / 99! | 654! / 603! / 116! | 332! / 276! / 97! | 349 / 311 / 76 | 121 / 97 / 32 | 181! / 153! / 48! | 79 / 69 / 20 | 196! / 175! / 43! |
| AF_GM09_5 (-24.6, -59.4, 27.0) | 3 / 3 / 1 * | 5 / 5 / 0 | 10! / 9! / 0 | 13! / 12! / 0 | 16! / 14! / 0 | 17! / 15! / 0 | 20! / 18! / 0 | 36 / 9 / 4 * | 10 / 9 / 1 | 4 / 4 / 2 | 6! / 6! / 2 | 2 / 2 / 1 | 5! / 5! / 0 |
| AF_GM09_6 (24.6, -59.4, 27.0) | 6 / 6 / 0 * | 8 / 8 / 0 | 10! / 9! / 0 | 13! / 11! / 0 | 15! / 14! / 0 | 16! / 14! / 0 | 19! / 17! / 0 | 140 / 20 / 22! * | 14 / 12 / 6 | 14 / 8 / 8 | 17 / 11 / 10 | 10 / 9 / 4 | 10! / 9! / 4 |
| AF_GM09_7 (59.4, -24.6, 27.0) | 72! / 66! / 18! | 145! / 133! / 32! | 343! / 316! / 62! | 442! / 408! / 80! | 538! / 495! / 97! | 553! / 509! / 100! | 651! / 600! / 118! | 304! / 302 / 296 | 329 / 295 / 85 | 113 / 92 / 89 | 185! / 157! / 121 | 80 / 70 / 44 | 195! / 174! / 75! |
| AF_GM10_0 (53.1, 22.0, -94.8) | 47 / 47 / 0 * | 76! / 72! / 0 | 183! / 174! / 0 | 236! / 224! / 0 | 286! / 272! / 0 | 294! / 279! / 0 | 347! / 329! / 0 | 130! / 116! / 162! | 161 / 148 / 23 | 50 / 48 / 27 | 87! / 83! / 26 | 41 / 40 / 15 | 98! / 94! / 2 |
| AF_GM10_1 (22.0, 53.1, -94.8) | 19 / 19 / 4 | 33 / 32 / 6 | 64 / 63 / 12 | 81 / 80 / 16 | 99 / 97 / 19 | 101 / 100 / 19 | 68 / 68 / 13 | 329! / 311 / 164! | 284 / 274 / 83 | 56 / 52 / 17 | 109 / 104 / 34 | 10 / 8 / 4 | 100 / 98 / 31 |
| AF_GM10_2 (-22.0, 53.1, -94.8) | 39 / 39 / 1 | 76 / 75 / 0 | 176 / 175 / 0 | 225 / 224 / 0 | 273 / 272 / 0 | 280 / 279 / 0 | 170 / 169 / 0 | 890 / 889 / 214 | 808 / 806 / 98 | 169 / 169 / 28 | 306 / 304 / 28! | 55 / 55 / 10 | 288 / 287 / 6 |
| AF_GM10_3 (-53.1, 22.0, -94.8) | 48 / 48 / 0 * | 76! / 73! / 0 | 183! / 176! / 0 | 236! / 227! / 0 | 286! / 276! / 0 | 294! / 283! / 0 | 346! / 333! / 0 | 195 / 160 / 217 | 162 / 156 / 29 | 48 / 44 / 13 | 78! / 73! / 11 | 39 / 37 / 8 | 96! / 92! / 0 |
| AF_GM10_4 (-53.1, -22.0, -94.8) | 45 / 45 / 0 * | 76! / 73! / 0 | 184! / 177! / 0 | 237! / 228! / 0 | 288! / 277! / 0 | 296! / 285! / 0 | 349! / 336! / 0 | 196 / 161 / 211 | 162 / 156 / 34 | 49 / 45 / 14 | 80! / 75! / 12 | 40 / 38 / 8 | 97! / 93! / 0 |
| AF_GM10_5 (-22.0, -53.1, -94.8) | 20 / 20 / 1 | 23 / 23 / 0 | 21 / 21 / 0 | 25 / 25 / 0 | 30 / 30 / 0 | 30 / 30 / 0 | 27 / 27 / 0 | 889! / 889! / 221 | 807 / 807 / 108 | 163 / 163 / 30 | 275 / 275 / 29! | 45 / 45 / 9 | 233 / 233 / 2 |
| AF_GM10_6 (22.0, -53.1, -94.8) | 3 / 3 / 1 * | 4! / 4! / 1 | 6! / 4! / 1! | 8! / 6! / 1! | 10! / 8! / 2! | 10! / 8! / 2! | 12! / 10! / 2! | 322! / 311! / 164! | 281 / 275 / 81 | 54 / 50 / 16 | 98 / 95 / 30 | 12 / 10 / 3 | 82 / 81 / 25 |
| AF_GM10_7 (53.1, -22.0, -94.8) | 47 / 47 / 0 * | 75! / 71! / 0 | 180! / 171! / 0 | 232! / 220! / 0 | 282! / 267! / 0 | 290! / 274! / 0 | 341! / 323! / 0 | 162 / 160 / 163! * | 160 / 146 / 22 | 52 / 49 / 27 | 88! / 84! / 25 | 42 / 40 / 15 | 98! / 94! / 2 |

- LC1: LC1 (GVLO + GVHI) (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 27 of 96 hole values governed by the estimate
  - compliant above rigid governing: AF_GM09_1 shear 5 vs 3, abs_tangential 5 vs 1, resultant 5 vs 3; AF_GM09_5 abs_tangential 2 vs 1; AF_GM09_6 abs_tangential 5 vs 2; AF_GM10_0 shear 47 vs 37, abs_axial 47 vs 35, resultant 47 vs 37; AF_GM10_3 shear 48 vs 38, abs_axial 48 vs 36, resultant 48 vs 38; AF_GM10_4 shear 45 vs 37, abs_axial 45 vs 36, resultant 45 vs 38; AF_GM10_6 abs_tangential 2 vs 1; AF_GM10_7 shear 47 vs 37, abs_axial 47 vs 35, resultant 47 vs 38
- LC2: LC2 (GVLO + GVHI) (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 42 of 96 hole values governed by the estimate
- FA1Q: FA1Q (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 56 of 96 hole values governed by the estimate
- FA1D: FA1D (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 56 of 96 hole values governed by the estimate
- FA1U: FA1U (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 57 of 96 hole values governed by the estimate
- FA1S: FA1S (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 57 of 96 hole values governed by the estimate
- FA1T: FA1T (L1 global; estimate op_zero; transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue): 56 of 96 hole values governed by the estimate
- LC3: LC3 (8 stop poses at R3) (R3 pose; estimate tc09_removed + op_zero; transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue): 38 of 96 hole values governed by the estimate
  - compliant above rigid governing: AF_GM09_1 shear 102 vs 21, abs_tangential 102 vs 14, resultant 102 vs 28; AF_GM09_2 shear 72 vs 9, abs_tangential 72 vs 5, pullout 5 vs 2, pushin 6 vs 3, resultant 72 vs 9; AF_GM09_5 shear 36 vs 10, abs_tangential 36 vs 5, pullout 4 vs 3, pushin 15 vs 3, resultant 37 vs 10; AF_GM09_6 shear 140 vs 28, abs_tangential 140 vs 19, resultant 141 vs 32; AF_GM10_7 shear 162 vs 126, abs_axial 160 vs 111
- GS: F2 GS servo stall (9 cone poses) (R3 pose; estimate tc09_removed + op_zero; transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue): 0 of 96 hole values governed by the estimate
- TD0: F2 TD touchdown Pc 0 (R3 pose; estimate tc09_removed + op_zero; transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue): 0 of 96 hole values governed by the estimate
- TDP: F2 TD touchdown Pc max (R3 pose; estimate tc09_removed + op_zero; transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue): 50 of 96 hole values governed by the estimate
- LC6: F2 LC6 hard landing 10 g (R3 pose; estimate tc09_removed + op_zero; transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue): 0 of 96 hole values governed by the estimate
- LC2F: F2 LC2F stuck pintle (thrust-only sub-case bounds) (R3 pose; estimate tc09_removed + op_zero; transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue): 56 of 96 hole values governed by the estimate

## v3.5.2 model: AS FOUND per-hole envelope (SIM; v3.5.2 rigid u v3.5.1 compliant, carried); the governing table above is the datasheet (lead 22:54:03Z)

Cell = max shear / max |axial| / max pull-out, N; * = a compliant-airframe value exceeds the rigid one at that hole by more than 1 N and 5 % (listed under the table).

| hole (x, y, z mm) | LC1 | LC2 | FA1Q | FA1D | FA1U | FA1S | FA1T | LC3 | GS | TD0 | TDP | LC6 | LC2F |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AF_GM09_0 (59.4, 24.6, 27.0) | 70 / 63 / 19 | 139 / 127 / 31 | 326 / 300 / 60 | 420 / 386 / 77 | 510 / 468 / 93 | 523 / 481 / 96 | 635 / 584 / 116 | 304 / 303 / 295 | 333 / 298 / 86 | 113 / 91 / 88 | 158 / 130 / 119 | 79 / 69 / 44 | 143 / 131 / 73 |
| AF_GM09_1 (24.6, 59.4, 27.0) | 5 / 3 / 0 * | 5 / 4 / 0 | 10 / 8 / 0 | 12 / 11 / 0 | 15 / 13 / 0 | 15 / 14 / 0 | 18 / 16 / 0 | 102 / 16 / 18 * | 10 / 9 / 5 | 6 / 4 / 6 | 9 / 6 / 7 | 3 / 2 / 2 | 6 / 5 / 4 |
| AF_GM09_2 (-24.6, 59.4, 27.0) | 3 / 2 / 0 | 5 / 4 / 0 | 10 / 9 / 0 | 13 / 11 / 0 | 15 / 14 / 0 | 16 / 14 / 0 | 19 / 17 / 0 | 72 / 7 / 5 * | 10 / 9 / 1 | 2 / 2 / 2 | 4 / 3 / 2 | 1 / 1 / 1 | 4 / 4 / 0 |
| AF_GM09_3 (-59.4, 24.6, 27.0) | 66 / 60 / 13 | 133 / 122 / 25 | 315 / 291 / 57 | 406 / 375 / 73 | 494 / 455 / 89 | 507 / 468 / 92 | 617 / 569 / 111 | 318 / 269 / 93 | 338 / 301 / 74 | 118 / 95 / 31 | 158 / 130 / 46 | 78 / 68 / 20 | 157 / 136 / 40 |
| AF_GM09_4 (-59.4, -24.6, 27.0) | 70 / 64 / 14 | 139 / 127 / 26 | 326 / 300 / 58 | 419 / 386 / 75 | 508 / 469 / 90 | 522 / 482 / 93 | 633 / 584 / 112 | 330 / 274 / 95 | 349 / 311 / 76 | 121 / 97 / 32 | 162 / 133 / 47 | 79 / 69 / 20 | 160 / 139 / 40 |
| AF_GM09_5 (-24.6, -59.4, 27.0) | 3 / 3 / 1 * | 5 / 5 / 0 | 10 / 9 / 0 | 12 / 11 / 0 | 15 / 14 / 0 | 16 / 14 / 0 | 19 / 17 / 0 | 36 / 9 / 4 * | 10 / 9 / 1 | 4 / 4 / 2 | 5 / 5 / 2 | 2 / 2 / 1 | 4 / 4 / 0 |
| AF_GM09_6 (24.6, -59.4, 27.0) | 6 / 6 / 0 * | 8 / 7 / 0 | 9 / 8 / 0 | 12 / 11 / 0 | 14 / 13 / 0 | 15 / 13 / 0 | 18 / 16 / 0 | 140 / 20 / 20 * | 14 / 12 / 6 | 14 / 8 / 8 | 17 / 11 / 10 | 10 / 9 / 4 | 9 / 8 / 4 |
| AF_GM09_7 (59.4, -24.6, 27.0) | 66 / 60 / 18 | 135 / 124 / 30 | 322 / 297 / 58 | 415 / 382 / 75 | 504 / 465 / 91 | 518 / 477 / 94 | 630 / 580 / 114 | 303 / 302 / 296 | 329 / 295 / 85 | 113 / 92 / 89 | 157 / 131 / 121 | 80 / 70 / 44 | 142 / 131 / 74 |
| AF_GM10_0 (53.1, 22.0, -94.8) | 47 / 47 / 0 * | 71 / 68 / 0 | 173 / 166 / 0 | 223 / 213 / 0 | 271 / 259 / 0 | 279 / 266 / 0 | 337 / 321 / 0 | 127 / 112 / 140 | 161 / 148 / 23 | 50 / 48 / 27 | 72 / 70 / 26 | 41 / 40 / 15 | 72 / 70 / 2 |
| AF_GM10_1 (22.0, 53.1, -94.8) | 19 / 19 / 4 | 33 / 32 / 6 | 64 / 63 / 12 | 81 / 80 / 16 | 99 / 97 / 19 | 101 / 100 / 19 | 68 / 68 / 13 | 326 / 310 / 154 | 284 / 274 / 83 | 56 / 52 / 17 | 109 / 104 / 34 | 10 / 8 / 4 | 100 / 98 / 31 |
| AF_GM10_2 (-22.0, 53.1, -94.8) | 39 / 39 / 0 | 76 / 75 / 0 | 176 / 175 / 0 | 225 / 224 / 0 | 273 / 272 / 0 | 280 / 279 / 0 | 170 / 169 / 0 | 890 / 889 / 214 | 808 / 806 / 98 | 169 / 169 / 28 | 306 / 304 / 15 | 55 / 55 / 10 | 288 / 287 / 6 |
| AF_GM10_3 (-53.1, 22.0, -94.8) | 48 / 48 / 0 * | 72 / 69 / 0 | 175 / 168 / 0 | 225 / 216 / 0 | 273 / 263 / 0 | 280 / 270 / 0 | 338 / 325 / 0 | 195 / 160 / 217 | 162 / 156 / 29 | 48 / 44 / 13 | 67 / 62 / 11 | 39 / 37 / 8 | 75 / 72 / 0 |
| AF_GM10_4 (-53.1, -22.0, -94.8) | 45 / 45 / 0 * | 71 / 68 / 0 | 172 / 166 / 0 | 222 / 214 / 0 | 270 / 260 / 0 | 277 / 267 / 0 | 337 / 324 / 0 | 196 / 161 / 211 | 162 / 156 / 34 | 49 / 45 / 14 | 68 / 64 / 12 | 40 / 38 / 8 | 77 / 73 / 0 |
| AF_GM10_5 (-22.0, -53.1, -94.8) | 20 / 20 / 1 | 23 / 23 / 0 | 21 / 21 / 0 | 25 / 25 / 0 | 30 / 30 / 0 | 30 / 30 / 0 | 27 / 27 / 0 | 883 / 882 / 221 | 807 / 807 / 108 | 163 / 163 / 30 | 275 / 275 / 12 | 45 / 45 / 9 | 233 / 233 / 2 |
| AF_GM10_6 (22.0, -53.1, -94.8) | 3 / 3 / 0 * | 2 / 2 / 1 | 4 / 1 / 0 | 6 / 2 / 1 | 7 / 2 / 1 | 7 / 2 / 1 | 10 / 6 / 2 | 319 / 308 / 150 | 281 / 275 / 81 | 54 / 50 / 16 | 98 / 95 / 30 | 12 / 10 / 3 | 82 / 81 / 25 |
| AF_GM10_7 (53.1, -22.0, -94.8) | 47 / 47 / 0 * | 70 / 66 / 0 | 169 / 160 / 0 | 217 / 205 / 0 | 264 / 250 / 0 | 271 / 256 / 0 | 329 / 312 / 0 | 162 / 160 / 140 * | 160 / 146 / 22 | 52 / 49 / 27 | 74 / 71 / 25 | 42 / 40 / 15 | 72 / 70 / 2 |

- LC1: LC1 (GVLO + GVHI) [rigid] (32 sub-cases); LC1 (v3.5.1 model) [compliant, c351] (4 sub-cases)
  - compliant above rigid: AF_GM09_1 shear 5 vs 3, abs_tangential 5 vs 1, resultant 5 vs 3; AF_GM09_5 abs_tangential 2 vs 1; AF_GM09_6 abs_tangential 5 vs 2; AF_GM10_0 shear 47 vs 34, abs_axial 47 vs 33, resultant 47 vs 35; AF_GM10_3 shear 48 vs 35, abs_axial 48 vs 34, resultant 48 vs 36; AF_GM10_4 shear 45 vs 34, abs_axial 45 vs 32, resultant 45 vs 35; AF_GM10_6 shear 3 vs 2, abs_axial 3 vs 2, abs_tangential 2 vs 1, resultant 3 vs 2; AF_GM10_7 shear 47 vs 34, abs_axial 47 vs 32, resultant 47 vs 35
- LC2: LC2 (GVLO + GVHI) [rigid] (32 sub-cases)
- FA1Q: FA1Q [rigid] (1 sub-cases)
- FA1D: FA1D [rigid] (1 sub-cases)
- FA1U: FA1U [rigid] (1 sub-cases)
- FA1S: FA1S [rigid] (1 sub-cases)
- FA1T: FA1T [rigid] (1 sub-cases)
- LC3: LC3 (stop poses at R3: 8 of 8) [rigid] (512 sub-cases); LC3 stop045 only (v3.5.1 model) [compliant, c351] (64 sub-cases)
  - compliant above rigid: AF_GM09_1 shear 102 vs 21, abs_tangential 102 vs 14, resultant 102 vs 27; AF_GM09_2 shear 72 vs 8, abs_tangential 72 vs 5, pullout 5 vs 2, pushin 6 vs 3, resultant 72 vs 8; AF_GM09_5 shear 36 vs 10, abs_tangential 36 vs 5, pullout 4 vs 3, pushin 15 vs 3, resultant 37 vs 10; AF_GM09_6 shear 140 vs 28, abs_tangential 140 vs 19, resultant 141 vs 32; AF_GM10_7 shear 162 vs 121, abs_axial 160 vs 105, resultant 162 vs 143
- GS: F2 GS servo stall (cone poses at R3: 9 of 9) [rigid] (576 sub-cases)
- TD0: F2 TD touchdown Pc 0 (cone poses at R3: 9 of 9) [rigid] (576 sub-cases)
- TDP: F2 TD touchdown Pc max (cone poses at R3: 9 of 9) [rigid] (576 sub-cases)
- LC6: F2 LC6 hard landing 10 g (cone poses at R3: 9 of 9) [rigid] (144 sub-cases)
- LC2F: F2 LC2F stuck pintle (cone poses at R3: 9 of 9) [rigid] (144 sub-cases)

## v3.5.1 model: per-hole envelope of the rigid and the compliant airframe (RM2-11; restates tables/engine_mount_data_v351.md)

Cell = max shear / max |axial| / max pull-out, N; * = a compliant-airframe value exceeds the rigid one at that hole by more than 1 N and 5 % (listed under the table).

| hole (x, y, z mm) | LC1 | FA1Q | FA1S | FA1T | LC3 | GS | TD0 | TDP | LC6 | LC2F |
|---|---|---|---|---|---|---|---|---|---|---|
| AF_GM09_0 (59.4, 24.6, 27.0) | 75 / 68 / 20 | 330 / 304 / 61 | 554 / 509 / 101 | 643 / 591 / 118 | 305 / 302 / 281 | 332 / 298 / 90 | 112 / 93 / 92 | 181 / 152 / 122 | 79 / 69 / 44 | 187 / 168 / 76 |
| AF_GM09_1 (24.6, 59.4, 27.0) | 5 / 3 / 0 * | 10 / 8 / 0 | 16 / 14 / 0 | 19 / 17 / 0 | 102 / 15 / 20 * | 10 / 9 / 6 | 6 / 4 / 6 | 9 / 7 / 7 | 3 / 2 / 2 | 7 / 6 / 3 |
| AF_GM09_2 (-24.6, 59.4, 27.0) | 3 / 3 / 0 | 10 / 9 / 0 | 17 / 15 / 0 | 20 / 17 / 0 | 72 / 7 / 5 * | 9 / 9 / 1 | 2 / 2 / 2 | 4 / 4 / 2 | 1 / 1 / 1 | 5 / 5 / 0 |
| AF_GM09_3 (-59.4, 24.6, 27.0) | 71 / 64 / 14 | 319 / 294 / 58 | 537 / 495 / 97 | 624 / 576 / 113 | 324 / 269 / 95 | 336 / 300 / 74 | 118 / 95 / 31 | 173 / 145 / 47 | 79 / 68 / 20 | 185 / 164 / 42 |
| AF_GM09_4 (-59.4, -24.6, 27.0) | 75 / 68 / 15 | 329 / 304 / 59 | 552 / 509 / 98 | 641 / 592 / 114 | 328 / 276 / 96 | 347 / 309 / 75 | 122 / 98 / 32 | 178 / 150 / 48 | 81 / 70 / 20 | 190 / 169 / 42 |
| AF_GM09_5 (-24.6, -59.4, 27.0) | 3 / 3 / 1 * | 10 / 9 / 0 | 16 / 15 / 0 | 19 / 17 / 0 | 36 / 9 / 4 * | 10 / 9 / 1 | 4 / 4 / 2 | 6 / 6 / 2 | 2 / 2 / 1 | 5 / 5 / 0 |
| AF_GM09_6 (24.6, -59.4, 27.0) | 6 / 6 / 0 * | 9 / 8 / 0 | 16 / 14 / 0 | 18 / 16 / 0 | 140 / 19 / 22 * | 14 / 12 / 6 | 14 / 9 / 8 | 17 / 11 / 10 | 10 / 9 / 4 | 10 / 9 / 4 |
| AF_GM09_7 (59.4, -24.6, 27.0) | 72 / 65 / 19 | 327 / 301 / 59 | 550 / 506 / 100 | 639 / 588 / 116 | 300 / 299 / 281 | 328 / 295 / 89 | 112 / 94 / 92 | 181 / 152 / 122 | 80 / 70 / 44 | 187 / 166 / 75 |
| AF_GM10_0 (53.1, 22.0, -94.8) | 47 / 47 / 0 * | 174 / 166 / 0 | 293 / 278 / 0 | 341 / 324 / 0 | 128 / 113 / 167 | 160 / 147 / 22 | 49 / 47 / 27 | 82 / 78 / 24 | 41 / 39 / 15 | 94 / 90 / 0 |
| AF_GM10_1 (22.0, 53.1, -94.8) | 7 / 6 / 2 | 18 / 18 / 4 | 30 / 30 / 6 | 35 / 35 / 7 | 321 / 300 / 165 | 284 / 274 / 83 | 46 / 42 / 17 | 50 / 46 / 19 | 8 / 4 / 4 | 9 / 9 / 4 |
| AF_GM10_2 (-22.0, 53.1, -94.8) | 4 / 4 / 1 | 34 / 34 / 0 | 55 / 54 / 0 | 66 / 66 / 0 | 882 / 879 / 204 | 808 / 807 / 98 | 137 / 137 / 25 | 130 / 130 / 24 | 40 / 40 / 8 | 17 / 17 / 0 |
| AF_GM10_3 (-53.1, 22.0, -94.8) | 48 / 48 / 0 * | 175 / 168 / 0 | 293 / 282 / 0 | 340 / 328 / 0 | 192 / 158 / 201 | 162 / 155 / 29 | 48 / 44 / 14 | 75 / 70 / 8 | 39 / 37 / 8 | 92 / 88 / 0 |
| AF_GM10_4 (-53.1, -22.0, -94.8) | 45 / 45 / 0 * | 175 / 168 / 0 | 294 / 283 / 0 | 343 / 330 / 0 | 192 / 160 / 197 | 162 / 156 / 34 | 49 / 45 / 15 | 78 / 72 / 9 | 40 / 38 / 8 | 94 / 90 / 0 |
| AF_GM10_5 (-22.0, -53.1, -94.8) | 20 / 20 / 1 | 22 / 22 / 0 | 34 / 34 / 0 | 10 / 10 / 0 | 889 / 889 / 227 | 807 / 807 / 108 | 131 / 131 / 26 | 157 / 157 / 20 | 30 / 29 / 8 | 74 / 74 / 1 |
| AF_GM10_6 (22.0, -53.1, -94.8) | 3 / 3 / 0 * | 5 / 1 / 0 | 8 / 2 / 1 | 19 / 18 / 4 | 323 / 312 / 176 | 281 / 275 / 81 | 46 / 43 / 17 | 62 / 58 / 22 | 10 / 7 / 3 | 30 / 30 / 10 |
| AF_GM10_7 (53.1, -22.0, -94.8) | 47 / 47 / 0 * | 171 / 162 / 0 | 287 / 272 / 0 | 334 / 316 / 0 | 162 / 160 / 168 * | 158 / 145 / 21 | 50 / 48 / 27 | 83 / 80 / 23 | 41 / 40 / 15 | 93 / 89 / 0 |

- LC1: LC1 [rigid] (16 sub-cases); LC1 [compliant] (4 sub-cases)
  - compliant above rigid: AF_GM09_1 shear 5 vs 3, abs_tangential 5 vs 1, resultant 5 vs 3; AF_GM09_5 abs_tangential 2 vs 1; AF_GM09_6 abs_tangential 5 vs 2; AF_GM10_0 shear 47 vs 36, abs_axial 47 vs 34, resultant 47 vs 37; AF_GM10_3 shear 48 vs 37, abs_axial 48 vs 36, resultant 48 vs 38; AF_GM10_4 shear 45 vs 37, abs_axial 45 vs 35, resultant 45 vs 38; AF_GM10_6 shear 3 vs 1, abs_axial 3 vs 1, abs_tangential 2 vs 1, resultant 3 vs 1; AF_GM10_7 shear 47 vs 36, abs_axial 47 vs 34, resultant 47 vs 37
- FA1Q: FA1Q [rigid] (1 sub-cases)
- FA1S: FA1S [rigid] (1 sub-cases)
- FA1T: FA1T [rigid] (1 sub-cases)
- LC3: LC3 (8 stop poses, runaway / hold) [rigid] (512 sub-cases); LC3 stop045 only [compliant] (64 sub-cases)
  - compliant above rigid: AF_GM09_1 shear 102 vs 20, abs_tangential 102 vs 14, resultant 102 vs 27; AF_GM09_2 shear 72 vs 8, abs_tangential 72 vs 5, pullout 5 vs 2, pushin 6 vs 3, resultant 72 vs 8; AF_GM09_5 shear 36 vs 10, abs_tangential 36 vs 4, pullout 4 vs 3, pushin 15 vs 3, resultant 37 vs 10; AF_GM09_6 shear 140 vs 27, abs_tangential 140 vs 19, resultant 141 vs 31; AF_GM10_7 shear 162 vs 124, abs_axial 160 vs 108
- GS: F2 GS servo stall (9 cone poses) [rigid] (576 sub-cases)
- TD0: F2 TD touchdown Pc 0 [rigid] (576 sub-cases)
- TDP: F2 TD touchdown Pc max [rigid] (576 sub-cases)
- LC6: F2 LC6 hard landing 10 g [rigid] (144 sub-cases)
- LC2F: F2 LC2F stuck pintle (thrust-only sub-case bounds) [rigid] (144 sub-cases)

## v3.5.2: OP-moment residue (MF observation, lead 22:24:34Z): the moment-free estimate beside each affected row

The as-found rows (SIM) stand as found; the datasheet rows are the governing values [DERIVED] (lead 22:54:03Z: the larger of the as-found value and the estimate, table at the top). The OP unit step of the v3.5.2 models carries a moment about the pivot that the physical load does not have (closed cavity, axisymmetric exit): in the R3 pose runs (LC3, F2) a couple of about 1.56 N m/MPa from two one-sided TC-09 aft-boundary faces (elements 24664 / 23610 at p/Pc 0.75), within a total of about 2.3 N m/MPa; in the L1 global runs (LC1, LC2, FA-1) 0.72 N m/MPa. The rods carry it to the airframe as a rod-force pair. Estimates [DERIVED, superposition of the posted unit steps through the EAX / EAY steps; ASSUMED transmission as a pure couple; the L1 global runs use pose_neutral_v352r3R3's EA steps]: 'moment-free' = the two TC-09 faces at p/Pc 1.0 (R3 runs); 'OP moment zero' = the physical statics. Not proven conservative for every hole: where an estimate is ABOVE the as-found value it is marked !.

| case | max screw shear N as found (hole) | moment-free estimate (hole) | OP moment zero (hole) | governing [DERIVED] (hole, by) | max pull-out N as found / estimate / zero / governing |
|---|---|---|---|---|---|
| LC1 (GVLO + GVHI) | 70 (AF_GM09_4) | n/a (L1 mesh) | 76 (AF_GM09_0) ! | **76** ! (AF_GM09_0, op zero) | 19 / n/a / 20 / **20** ! |
| LC2 (GVLO + GVHI) | 139 (AF_GM09_4) | n/a (L1 mesh) | 150 (AF_GM09_0) ! | **150** ! (AF_GM09_0, op zero) | 31 / n/a / 33 / **33** ! |
| FA1Q | 326 (AF_GM09_0) | n/a (L1 mesh) | 348 (AF_GM09_0) ! | **348** ! (AF_GM09_0, op zero) | 60 / n/a / 64 / **64** ! |
| FA1D | 420 (AF_GM09_0) | n/a (L1 mesh) | 448 (AF_GM09_0) ! | **448** ! (AF_GM09_0, op zero) | 77 / n/a / 82 / **82** ! |
| FA1U | 510 (AF_GM09_0) | n/a (L1 mesh) | 544 (AF_GM09_0) ! | **544** ! (AF_GM09_0, op zero) | 93 / n/a / 99 / **99** ! |
| FA1S | 523 (AF_GM09_0) | n/a (L1 mesh) | 559 (AF_GM09_0) ! | **559** ! (AF_GM09_0, op zero) | 96 / n/a / 102 / **102** ! |
| FA1T | 635 (AF_GM09_0) | n/a (L1 mesh) | 657 (AF_GM09_0) ! | **657** ! (AF_GM09_0, op zero) | 116 / n/a / 120 / **120** ! |
| LC3 (8 stop poses at R3) | 890 (AF_GM10_2) | 890 (AF_GM10_2) | 890 (AF_GM10_2) | **890** (AF_GM10_2, op zero) | 296 / 282 / 275 / **296** |
| F2 GS servo stall (9 cone poses) | 808 (AF_GM10_2) | 808 (AF_GM10_2) | 808 (AF_GM10_2) | **808** (AF_GM10_2, as found) | 108 / 108 / 108 / **108** |
| F2 TD touchdown Pc 0 | 169 (AF_GM10_2) | 169 (AF_GM10_2) | 169 (AF_GM10_2) | **169** (AF_GM10_2, as found) | 89 / 89 / 89 / **89** |
| F2 TD touchdown Pc max | 306 (AF_GM10_2) | 207 (AF_GM10_2) | 186 (AF_GM09_0) | **306** (AF_GM10_2, as found) | 121 / 121 / 121 / **121** |
| F2 LC6 hard landing 10 g | 80 (AF_GM09_7) | 80 (AF_GM09_7) | 80 (AF_GM09_7) | **80** (AF_GM09_7, as found) | 44 / 44 / 44 / **44** |
| F2 LC2F stuck pintle (thrust-only sub-case bounds) | 288 (AF_GM10_2) | 184 (AF_GM09_4) | 197 (AF_GM09_0) | **288** (AF_GM10_2, as found) | 74 / 75 / 75 / **75** ! |

Per hole, max screw shear N where an estimate differs from the as-found value by more than 1 N (as found / moment-free estimate / OP moment zero; L1 global cases as found / zero):

- LC1 (GVLO + GVHI): AF_GM09_0 70 / 76; AF_GM09_3 66 / 71; AF_GM09_4 70 / 76; AF_GM09_7 66 / 72; AF_GM10_0 34 / 37; AF_GM10_1 19 / 4; AF_GM10_2 39 / 13; AF_GM10_3 35 / 38; AF_GM10_4 34 / 37; AF_GM10_5 20 / 17; AF_GM10_7 34 / 37
- LC2 (GVLO + GVHI): AF_GM09_0 139 / 150; AF_GM09_3 133 / 143; AF_GM09_4 139 / 149; AF_GM09_7 135 / 145; AF_GM10_0 71 / 76; AF_GM10_1 33 / 5; AF_GM10_2 76 / 14; AF_GM10_3 72 / 76; AF_GM10_4 71 / 76; AF_GM10_5 23 / 19; AF_GM10_6 2 / 4; AF_GM10_7 70 / 75
- FA1Q: AF_GM09_0 326 / 348; AF_GM09_3 315 / 336; AF_GM09_4 326 / 346; AF_GM09_7 322 / 343; AF_GM10_0 173 / 183; AF_GM10_1 64 / 8; AF_GM10_2 176 / 3; AF_GM10_3 175 / 183; AF_GM10_4 172 / 184; AF_GM10_5 21 / 12; AF_GM10_6 4 / 6; AF_GM10_7 169 / 180
- FA1D: AF_GM09_0 420 / 448; AF_GM09_3 406 / 434; AF_GM09_4 419 / 446; AF_GM09_7 415 / 442; AF_GM10_0 223 / 236; AF_GM10_1 81 / 9; AF_GM10_2 225 / 5; AF_GM10_3 225 / 236; AF_GM10_4 222 / 237; AF_GM10_5 25 / 14; AF_GM10_6 6 / 8; AF_GM10_7 217 / 232
- FA1U: AF_GM09_0 510 / 544; AF_GM09_2 15 / 16; AF_GM09_3 494 / 527; AF_GM09_4 508 / 541; AF_GM09_7 504 / 538; AF_GM10_0 271 / 286; AF_GM10_1 99 / 11; AF_GM10_2 273 / 7; AF_GM10_3 273 / 286; AF_GM10_4 270 / 288; AF_GM10_5 30 / 16; AF_GM10_6 7 / 10; AF_GM10_7 264 / 282
- FA1S: AF_GM09_0 523 / 559; AF_GM09_3 507 / 542; AF_GM09_4 522 / 556; AF_GM09_5 16 / 17; AF_GM09_7 518 / 553; AF_GM10_0 279 / 294; AF_GM10_1 101 / 12; AF_GM10_2 280 / 7; AF_GM10_3 280 / 294; AF_GM10_4 277 / 296; AF_GM10_5 30 / 16; AF_GM10_6 7 / 10; AF_GM10_7 271 / 290
- FA1T: AF_GM09_0 635 / 657; AF_GM09_3 617 / 638; AF_GM09_4 633 / 654; AF_GM09_7 630 / 651; AF_GM10_0 337 / 347; AF_GM10_1 68 / 13; AF_GM10_2 170 / 9; AF_GM10_3 338 / 346; AF_GM10_4 337 / 349; AF_GM10_5 27 / 18; AF_GM10_6 10 / 12; AF_GM10_7 329 / 341
- LC3 (8 stop poses at R3): AF_GM09_0 304 / 303 / 306; AF_GM09_3 318 / 320 / 323; AF_GM09_4 330 / 332 / 331; AF_GM09_7 303 / 303 / 304; AF_GM10_0 127 / 129 / 130; AF_GM10_1 326 / 326 / 329; AF_GM10_3 195 / 191 / 189; AF_GM10_4 196 / 192 / 189; AF_GM10_5 883 / 883 / 889; AF_GM10_6 319 / 320 / 322; AF_GM10_7 121 / 124 / 126
- F2 GS servo stall (9 cone poses): no hole changes by more than 1 N
- F2 TD touchdown Pc 0: no hole changes by more than 1 N
- F2 TD touchdown Pc max: AF_GM09_0 158 / 177 / 186; AF_GM09_3 158 / 171 / 176; AF_GM09_4 162 / 175 / 181; AF_GM09_7 157 / 176 / 185; AF_GM10_0 72 / 82 / 87; AF_GM10_1 109 / 76 / 56; AF_GM10_2 306 / 207 / 171; AF_GM10_3 67 / 74 / 78; AF_GM10_4 68 / 76 / 80; AF_GM10_5 275 / 178 / 165; AF_GM10_6 98 / 66 / 55; AF_GM10_7 74 / 83 / 88
- F2 LC6 hard landing 10 g: no hole changes by more than 1 N
- F2 LC2F stuck pintle (thrust-only sub-case bounds): AF_GM09_0 143 / 179 / 197; AF_GM09_2 4 / 5 / 5; AF_GM09_3 157 / 180 / 191; AF_GM09_4 160 / 184 / 196; AF_GM09_5 4 / 5 / 5; AF_GM09_7 142 / 178 / 195; AF_GM10_0 72 / 90 / 98; AF_GM10_1 100 / 41 / 5; AF_GM10_2 288 / 111 / 23; AF_GM10_3 75 / 89 / 96; AF_GM10_4 77 / 90 / 97; AF_GM10_5 233 / 59 / 18; AF_GM10_6 82 / 24 / 6; AF_GM10_7 72 / 89 / 98

## Ring resultants, v351 model (envelope over the sub-cases): max |Fx|, |Fy|, |Fz| N; max lateral |F| N; max |M| about the pivot N m

| case | airframe | GM-09 ring F | GM-09 lat | GM-09 M | GM-10 ring F | GM-10 lat | GM-10 M | total F | total M |
|---|---|---|---|---|---|---|---|---|---|
| LC1 | rigid | 18, 18, 241 | 18 | 0.33, 0.36, 0.34 | 7, 7, 110 | 7 | 1.16, 0.74, 0.05 | 25, 25, 345 | 1.15, 0.38, 0.40 |
| LC1 | compliant | 17, 17, 181 | 17 | 0.45, 0.46, 0.33 | 8, 9, 165 | 9 | 1.06, 0.78, 0.04 | 25, 25, 345 | 0.78, 0.44, 0.36 |
| FA1Q | rigid | 1, 1, 1168 | 1 | 0.14, 0.38, 0.44 | 1, 1, 658 | 1 | 2.23, 1.22, 0.02 | 0, 0, 1826 | 2.08, 0.84, 0.42 |
| FA1S | rigid | 1, 2, 1961 | 2 | 0.24, 0.65, 0.55 | 1, 2, 1104 | 2 | 3.58, 2.03, 0.07 | 0, 0, 3065 | 3.34, 1.38, 0.47 |
| FA1T | rigid | 1, 2, 2280 | 3 | 0.28, 0.74, 0.59 | 1, 2, 1320 | 3 | 2.40, 3.88, 0.15 | 0, 0, 3600 | 2.12, 3.14, 0.43 |
| LC3 (8 stop poses, runaway / hold) | rigid | 677, 686, 986 | 686 | 5.55, 12.48, 2.28 | 502, 498, 1056 | 502 | 27.80, 17.13, 3.43 | 323, 323, 501 | 22.95, 7.94, 2.37 |
| LC3 stop045 only | compliant | 424, 416, 477 | 523 | 9.67, 6.97, 0.83 | 284, 277, 294 | 363 | 12.29, 9.89, 1.09 | 303, 303, 500 | 7.17, 7.35, 0.84 |
| F2 GS servo stall (9 cone poses) | rigid | 186, 176, 1038 | 201 | 1.67, 3.51, 8.12 | 115, 104, 910 | 128 | 56.57, 50.61, 4.45 | 132, 131, 509 | 56.14, 50.94, 7.56 |
| F2 TD touchdown Pc 0 | rigid | 223, 229, 238 | 230 | 2.35, 4.44, 1.20 | 96, 90, 224 | 96 | 12.54, 11.43, 0.72 | 297, 297, 219 | 10.40, 7.00, 1.32 |
| F2 TD touchdown Pc max | rigid | 276, 282, 417 | 283 | 2.71, 5.28, 1.41 | 105, 96, 328 | 105 | 14.13, 12.62, 0.86 | 359, 359, 506 | 11.55, 7.80, 1.47 |
| F2 LC6 hard landing 10 g | rigid | 88, 90, 230 | 90 | 1.32, 2.02, 0.22 | 37, 34, 199 | 37 | 2.92, 3.66, 0.17 | 120, 120, 402 | 1.86, 1.64, 0.24 |
| F2 LC2F stuck pintle (thrust-only sub-case bounds) | rigid | 114, 118, 575 | 118 | 1.03, 2.21, 0.51 | 25, 22, 376 | 25 | 3.72, 3.89, 0.28 | 136, 136, 908 | 2.74, 2.61, 0.42 |

## Ring resultants, v352 model (envelope over the sub-cases): max |Fx|, |Fy|, |Fz| N; max lateral |F| N; max |M| about the pivot N m

| case | airframe | GM-09 ring F | GM-09 lat | GM-09 M | GM-10 ring F | GM-10 lat | GM-10 M | total F | total M |
|---|---|---|---|---|---|---|---|---|---|
| LC1 (GVLO + GVHI) | rigid | 17, 18, 221 | 18 | 0.33, 0.37, 0.39 | 7, 7, 127 | 7 | 2.43, 1.30, 0.11 | 24, 24, 347 | 2.43, 1.00, 0.50 |
| LC2 (GVLO + GVHI) | rigid | 17, 18, 466 | 18 | 0.30, 0.37, 0.43 | 7, 7, 287 | 7 | 3.94, 2.43, 0.13 | 24, 24, 752 | 3.92, 2.06, 0.57 |
| FA1Q | rigid | 0, 1, 1153 | 1 | 0.12, 0.33, 0.53 | 0, 1, 750 | 1 | 7.42, 5.31, 0.16 | 0, 0, 1904 | 7.29, 4.98, 0.70 |
| FA1D | rigid | 1, 2, 1485 | 2 | 0.16, 0.43, 0.60 | 1, 2, 966 | 2 | 9.46, 6.84, 0.20 | 0, 0, 2450 | 9.30, 6.41, 0.79 |
| FA1U | rigid | 1, 2, 1804 | 2 | 0.19, 0.52, 0.66 | 1, 2, 1173 | 2 | 11.42, 8.31, 0.23 | 0, 0, 2977 | 11.23, 7.79, 0.89 |
| FA1S | rigid | 1, 2, 1853 | 2 | 0.20, 0.53, 0.67 | 1, 2, 1205 | 2 | 11.73, 8.54, 0.23 | 0, 0, 3059 | 11.53, 8.01, 0.90 |
| FA1T | rigid | 1, 2, 2250 | 2 | 0.24, 0.68, 0.68 | 1, 2, 1350 | 2 | 7.58, 5.75, 0.04 | 0, 0, 3600 | 7.34, 5.07, 0.72 |
| LC3 (stop poses at R3: 8 of 8) | rigid | 632, 651, 992 | 651 | 5.42, 11.52, 2.64 | 443, 449, 1054 | 449 | 25.84, 22.05, 3.40 | 321, 321, 506 | 21.51, 11.99, 1.61 |
| F2 GS servo stall (cone poses at R3: 9 of 9) | rigid | 180, 178, 1039 | 198 | 1.67, 3.66, 7.83 | 117, 104, 911 | 129 | 56.47, 50.49, 4.49 | 140, 140, 514 | 56.10, 50.98, 7.42 |
| F2 TD touchdown Pc 0 (cone poses at R3: 9 of 9) | rigid | 218, 226, 215 | 226 | 2.32, 4.45, 1.28 | 98, 89, 204 | 98 | 11.11, 10.38, 0.84 | 294, 294, 215 | 8.90, 6.02, 1.51 |
| F2 TD touchdown Pc max (cone poses at R3: 9 of 9) | rigid | 282, 287, 327 | 290 | 2.76, 5.45, 2.29 | 100, 95, 410 | 102 | 12.59, 16.72, 0.95 | 356, 356, 511 | 10.10, 11.76, 1.97 |
| F2 LC6 hard landing 10 g (cone poses at R3: 9 of 9) | rigid | 87, 89, 223 | 89 | 1.31, 1.98, 0.30 | 36, 34, 190 | 36 | 2.55, 3.30, 0.19 | 119, 119, 395 | 1.44, 1.31, 0.31 |
| F2 LC2F stuck pintle (cone poses at R3: 9 of 9) | rigid | 134, 132, 447 | 139 | 1.16, 2.42, 1.94 | 13, 18, 550 | 18 | 3.67, 13.10, 0.64 | 136, 136, 908 | 2.67, 11.64, 1.43 |

## Ring resultants, v352 model, governing [DERIVED] (lead 22:54:03Z): rigid airframe, the larger of the as-found value and the estimate(s) per component; max |Fx|, |Fy|, |Fz| N; max lateral |F| N; max |M| about the pivot N m

The as-found total moment of the L1 global cases (LC1, LC2, FA-1) is mostly the OP residue couple (0.72 N m/MPa); the governing value keeps it (the as-found value is the larger).

| case | GM-09 ring F | GM-09 lat | GM-09 M | GM-10 ring F | GM-10 lat | GM-10 M | total F | total M |
|---|---|---|---|---|---|---|---|---|
| LC1 (GVLO + GVHI) | 18, 18, 241 | 18 | 0.33, 0.37, 0.39 | 7, 7, 127 | 7 | 2.43, 1.30, 0.11 | 24, 24, 347 | 2.43, 1.00, 0.50 |
| LC2 (GVLO + GVHI) | 18, 18, 503 | 18 | 0.30, 0.41, 0.44 | 7, 7, 287 | 7 | 3.94, 2.43, 0.13 | 25, 25, 752 | 3.92, 2.06, 0.57 |
| FA1Q | 0, 1, 1230 | 1 | 0.14, 0.41, 0.55 | 1, 1, 750 | 2 | 7.42, 5.31, 0.16 | 1, 1, 1904 | 7.29, 4.98, 0.70 |
| FA1D | 1, 2, 1583 | 2 | 0.18, 0.53, 0.62 | 1, 2, 966 | 2 | 9.46, 6.84, 0.20 | 1, 2, 2450 | 9.30, 6.41, 0.79 |
| FA1U | 1, 2, 1923 | 2 | 0.22, 0.64, 0.68 | 1, 2, 1173 | 2 | 11.42, 8.31, 0.23 | 2, 2, 2977 | 11.23, 7.79, 0.89 |
| FA1S | 1, 2, 1976 | 2 | 0.22, 0.66, 0.69 | 1, 2, 1205 | 3 | 11.73, 8.54, 0.23 | 2, 2, 3059 | 11.53, 8.01, 0.90 |
| FA1T | 1, 2, 2327 | 2 | 0.26, 0.76, 0.69 | 1, 2, 1350 | 3 | 7.58, 5.75, 0.20 | 1, 1, 3600 | 7.34, 5.07, 0.72 |
| LC3 (8 stop poses at R3) | 683, 681, 992 | 683 | 5.63, 12.58, 2.64 | 493, 478, 1073 | 493 | 27.56, 22.05, 3.48 | 322, 321, 506 | 22.90, 11.99, 2.58 |
| F2 GS servo stall (9 cone poses) | 180, 178, 1039 | 198 | 1.67, 3.66, 7.83 | 117, 104, 911 | 129 | 56.47, 50.49, 4.49 | 140, 140, 514 | 56.10, 50.98, 7.42 |
| F2 TD touchdown Pc 0 | 218, 226, 215 | 226 | 2.32, 4.45, 1.28 | 98, 89, 204 | 98 | 11.11, 10.38, 0.84 | 294, 294, 215 | 8.90, 6.02, 1.51 |
| F2 TD touchdown Pc max | 282, 287, 421 | 290 | 2.76, 5.45, 2.29 | 109, 97, 410 | 109 | 12.59, 16.72, 0.95 | 357, 356, 511 | 10.10, 11.76, 1.97 |
| F2 LC6 hard landing 10 g | 87, 89, 223 | 89 | 1.31, 1.98, 0.30 | 36, 34, 190 | 36 | 2.55, 3.30, 0.19 | 119, 119, 395 | 1.44, 1.31, 0.31 |
| F2 LC2F stuck pintle (thrust-only sub-case bounds) | 134, 132, 600 | 139 | 1.16, 2.42, 1.94 | 28, 24, 550 | 28 | 3.67, 13.10, 0.64 | 138, 136, 908 | 2.67, 11.64, 1.43 |

## Gimbal-axis stiffness at the 8 deg stop poses (RM2-05 folded)

N m/rad. FE = SIM unit steps EAX / EAY with the servo output rigid (CAD v3.5.1 c71 pose runs, asm v1.2: the v3.5.1-model F3; the v3.5.2 R3 values are in the next table; at stop045 they are 8-13 % stiffer with the servo rigid and 2-6 % with it in series, report section 9). With the servo = DERIVED: r_eff per servo and pose in series, k_s 58 / 174 N m/rad per servo (ASSUMED, TO-VERIFY B-TVC-1). coupled = 1 / C_jj (other axis moment-free; what a single-axis load measures); diagonal = (C^-1)_jj (other axis held at zero rotation). The v3.5.1 table used r_h 11.139 mm at every pose and is superseded.

| pose (alpha, beta deg) | r_eff 1 / 2 mm | K_alpha FE coupled | K_alpha +58 coupled / diag | K_alpha +174 coupled / diag | K_beta FE coupled | K_beta +58 coupled / diag | K_beta +174 coupled / diag |
|---|---|---|---|---|---|---|---|
| stop000 (-0.00, +8.00) | 9.43 / 9.43 | 6400 | 1388 / 1388 | 2905 / 2905 | 6570 | 1759 / 1759 | 3436 / 3436 |
| stop045 (-5.68, +5.65) | 11.07 / 7.88 | 6531 | 1329 / 1475 | 2834 / 2982 | 6348 | 1530 / 1698 | 3097 / 3258 |
| stop090 (-8.00, +0.00) | 10.61 / 9.88 | 6954 | 1170 / 1226 | 2626 / 2698 | 5488 | 1111 / 1165 | 2373 / 2438 |
| stop135 (-5.68, -5.65) | 9.77 / 11.10 | 7844 | 1169 / 1173 | 2701 / 2708 | 4426 | 866 / 869 | 1868 / 1872 |
| stop180 (-0.00, -8.00) | 10.23 / 10.23 | 8577 | 1275 / 1275 | 2949 / 2949 | 3888 | 787 / 787 | 1681 / 1681 |
| stop225 (+5.68, -5.65) | 11.10 / 9.77 | 7856 | 1169 / 1173 | 2702 / 2710 | 4162 | 856 / 859 | 1819 / 1824 |
| stop270 (+8.00, -0.00) | 9.88 / 10.61 | 6964 | 1170 / 1226 | 2627 / 2701 | 5176 | 1098 / 1151 | 2313 / 2378 |
| stop315 (+5.68, +5.65) | 7.88 / 11.07 | 6533 | 1329 / 1476 | 2835 / 2985 | 6183 | 1520 / 1688 | 3057 / 3220 |

## Gimbal-axis stiffness at the 8 deg stop poses, v3.5.2 R3 model (REV-GNC-7 input)

N m/rad; SIM (FE unit steps EAX / EAY on the v3.5.2 R3 pose runs, rev-3 levers) + DERIVED (servo in series as above; k_s 58 / 174 ASSUMED, TO-VERIFY B-TVC-1). Source results/v352/k_table_r3_v352.json f3c7cfbcfb98bcd7 (17 of 17 poses posted; lead 18:40:44Z: all 13 chain-E R3 poses ACCEPTED (runs/.hb3_trim_ok)); all 17 poses with the v3.5.1 values, deltas and fractions: results/v352/tables/k_table_r3_v352.md. GNC sets its K band from the full R3 table (lead 17:33:40Z), not from stop045. Range over the 17 poses, coupled: K_alpha FE 7294 (stop000) - 9337 (stop180), +58 1150 (neutral) - 1426 (stop000), +174 2697 (neutral) - 3076 (stop000); K_beta FE 3972 (stop180) - 7172 (stop000), +58 791 (stop180) - 1799 (stop000), +174 1697 (stop180) - 3594 (stop000).

| pose (alpha, beta deg) | K_alpha FE coupled / diag | K_alpha +58 coupled / diag | K_alpha +174 coupled / diag | K_beta FE coupled / diag | K_beta +58 coupled / diag | K_beta +174 coupled / diag |
|---|---|---|---|---|---|---|
| stop000 (-0.00, +8.00) | 7294 / 7294 | 1426 / 1426 | 3076 / 3076 | 7172 / 7172 | 1799 / 1799 | 3594 / 3594 |
| stop045 (-5.67, +5.65) | 7403 / 7408 | 1362 / 1520 | 2987 / 3163 | 6881 / 6885 | 1559 / 1740 | 3219 / 3409 |
| stop090 (-8.00, +0.00) | 7756 / 7774 | 1190 / 1250 | 2732 / 2819 | 5808 / 5822 | 1124 / 1181 | 2431 / 2508 |
| stop135 (-5.67, -5.65) | 8595 / 8612 | 1184 / 1188 | 2785 / 2794 | 4569 / 4578 | 871 / 875 | 1892 / 1899 |
| stop180 (-0.00, -8.00) | 9337 / 9337 | 1291 / 1291 | 3034 / 3034 | 3972 / 3972 | 791 / 791 | 1697 / 1697 |
| stop225 (+5.67, -5.65) | 8606 / 8630 | 1184 / 1189 | 2786 / 2796 | 4268 / 4280 | 860 / 863 | 1839 / 1845 |
| stop270 (+8.00, -0.00) | 7764 / 7787 | 1190 / 1251 | 2733 / 2821 | 5443 / 5459 | 1109 / 1166 | 2364 / 2440 |
| stop315 (+5.67, +5.65) | 7402 / 7410 | 1362 / 1521 | 2987 / 3166 | 6678 / 6685 | 1549 / 1729 | 3174 / 3364 |

## First engine-mount modes (RM2-07 folded)

Coarsened all-L2 modal (modal_v351ca2b_c71, CAD v3.5.1 model; SIM), rigid airframe holes. The loop-relevant rocking pair is the one WITH the servo in series AND the servo inertia J (rotor + gear train at the output shaft, added through the kinematic factor g = 23.04 at neutral; J nominal 1.6e-3, range 0.76-2.7e-3 kg m2, ASSUMED from the GNC SB-2292SG datasheet, TO-VERIFY B-TVC-1) [DERIVED]. The v3.5.1 '21-33 Hz with the servo in series' omitted J and is WITHDRAWN as the loop-relevant pair.

| mode | f FE, servo rigid Hz | f at production K Hz | servo k_s 58: J nominal (J range) Hz | servo k_s 174: J nominal (J range) Hz |
|---|---|---|---|---|
| engine rocking about the inner axis (beta) | 51.4 | 47.8 | 16.72 (14.86-18.73) | 24.49 (21.76-27.43) |
| engine rocking about the outer axis X (alpha, engine + ring) | 59.4 | 55.5 | 17.15 (15.25-19.19) | 25.95 (23.08-29.04) |
| engine lateral X (on the mount) | 266.5 | - | - | - |
| engine lateral Y (on the mount) | 372.1 | - | - | - |
| engine axial (thrust path through the gimbal) | 408.3 | - | - | - |

Over the 17 poses (lumped 2-DOF, r_eff per servo and pose): k_s 58 15.2-19.1 Hz at J nominal; k_s 174 22.2-27.2 Hz; over the J range 13.8-31.1 Hz. Neutral over the k_s and J ranges: 14.9-29.0 Hz.

RM2-06 re-solve (modal_v351ca2c_c71, TC-01 OP loads mapped from L1; report 9A): modes 1-6 move by at most 0.004 % (MAC >= 1.0000); the table stands [SIM; results/v352/modal_ca2c_vs_ca2b_v352.json 1bdaf41b4611094c].

