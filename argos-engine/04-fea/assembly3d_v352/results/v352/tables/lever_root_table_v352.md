# Lever roots at R3: F1 LC3 at the 8 stops and F2 GS at the 9 cones, cold and hot bound (v3.5.2 item 1)

fea3d, 2026-10-20T20:38:49Z (date -u); results/v352/lever_root_table_v352.json, scripts/lever_root_table_v352.py eaabd770a1833c73.  cold SIM (R3 pose runs, rev 3 levers, CAD v3.5.2); p = 1 cells DERIVED (order ASSUMED, no R4); hot DERIVED (node-wise sub-additivity bound on SIM inputs).  Nothing here is physical approval.

Levers GM-01 (servo 1) and GM-02 (servo 2), rev 3 (CAD v3.5.2), at R3 (the six junction faces at h 0.25 / 0.2 mm).  MS = Fty(T) / (1.5 vM) - 1 and Ftu(T) / (2.0 vM) - 1 at the node temperature (AL7075-T6, 470 / 540 MPa at the lever-root temperatures).  Cold: B1_21.65 node temperatures, no thermal stress.  Cell: the R3 value, or the p = 1 bound where R2 -> R3 exceeded 5 % (lead 12:28Z (5); R2 exists at stop045, stop315, alpha+, alpha- only).  Hot: per pose, node by node, LC1 thermo-pressure vM of the R3 base (GVLO hbg3 / GVHI hbh3, 4 burn states) + the pose's own increment vM; worst base and state.  At the cones the increment is the GS + TD + LC6 envelope of the pose (a lower bound on the GS-only hot margin).  Hot + p1: the hot bound with the cold p = 1 increment added at every lever node (the three p = 1 cells).

Check: the minimum over the poses of the per-pose hot bound equals the published envelope bound per base, state, part and set: PASS (64 of 64 rows exact).  Node numbering of the levers identical in the pose and base models: {'g3': True, 'h3': True}.

## Governing values per lever

| set | lever | cold cell MS y / u (pose) | rule | hot cell MS y / u (pose; base, state) | rule |
|---|---|---|---|---|---|
| F1 LC3, 8 stops, all | GM-01 | +0.534 / +0.322 (stop315) | R3 value (R2 -> R3 within 5 %) | +0.220 / +0.052 (stop315; h3 (GVHI) B1_2) | hot bound |
| F1 LC3, 8 stops, regular | GM-01 | +0.534 / +0.322 (stop315) | R3 value (R2 -> R3 within 5 %) | +0.220 / +0.052 (stop315; h3 (GVHI) B1_2) | hot bound |
| F1 LC3, 8 stops, all | GM-02 | +0.400 / +0.206 (stop045) | p = 1 bound (R2 -> R3 > 5 %; order ASSUMED; lead 12:28Z (5)) | +0.202 / +0.036 (stop045; g3 (GVLO) B1_2) | hot bound + p = 1 increment |
| F1 LC3, 8 stops, regular | GM-02 | +0.400 / +0.206 (stop045) | p = 1 bound (R2 -> R3 > 5 %; order ASSUMED; lead 12:28Z (5)) | +0.202 / +0.036 (stop045; g3 (GVLO) B1_2) | hot bound + p = 1 increment |
| F2 GS, 9 cones, all | GM-01 | +0.648 / +0.420 (alpha+) | R3 value (R2 -> R3 within 5 %) | +0.289 / +0.111 (alpha+; h3 (GVHI) B1_21.65) | hot bound |
| F2 GS, 9 cones, regular | GM-01 | +0.648 / +0.420 (alpha+) | R3 value (R2 -> R3 within 5 %) | +0.289 / +0.111 (alpha+; h3 (GVHI) B1_21.65) | hot bound |
| F2 GS, 9 cones, all | GM-02 | +0.591 / +0.371 (alpha-) | p = 1 bound (R2 -> R3 > 5 %; order ASSUMED; lead 12:28Z (5)) | +0.337 / +0.152 (alpha-; h3 (GVHI) B1_21.65) | hot bound + p = 1 increment |
| F2 GS, 9 cones, regular | GM-02 | +0.591 / +0.371 (alpha-) | p = 1 bound (R2 -> R3 > 5 %; order ASSUMED; lead 12:28Z (5)) | +0.337 / +0.152 (alpha-; h3 (GVHI) B1_21.65) | hot bound + p = 1 increment |

Rows with a negative cell or hot cell: 0.

## F1 LC3 at the 8 stop poses

| pose | lever | set | cold MS y / u (vM MPa; node, class) | R2 -> R3 | cell MS y / u | hot bound MS y / u (vM_LC1 + vMD MPa; node; base, state) | hot + p1 |
|---|---|---|---|---|---|---|---|
| stop000 | GM-01 | all | +0.967 / +0.695 (159.3; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.967 / +0.695 | +0.475 / +0.271 (28.0 + 184.4; 79484; h3 (GVHI), B1_2) | - |
| stop000 | GM-01 | regular | +0.967 / +0.695 (159.3; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.967 / +0.695 | +0.475 / +0.271 (28.0 + 184.4; 79484; h3 (GVHI), B1_2) | - |
| stop000 | GM-02 | all | +0.866 / +0.608 (168.0; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.866 / +0.608 | +0.525 / +0.314 (19.0 + 186.5; 145697; g3 (GVLO), B1_2) | - |
| stop000 | GM-02 | regular | +0.866 / +0.608 (168.0; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.866 / +0.608 | +0.525 / +0.314 (19.0 + 186.5; 145697; g3 (GVLO), B1_2) | - |
| stop045 | GM-01 | all | +2.240 / +1.792 (96.7; 58609, RE 0.2057 mm) | -0.38 % (97.1 -> 96.7) | +2.240 / +1.792 | +2.333 / +1.872 (70.3 + 23.7; 58609; h3 (GVHI), B1_21.65) | - |
| stop045 | GM-01 | regular | +6.704 / +5.638 (40.7; 64910, regular) | -0.27 % (40.8 -> 40.7) | +6.704 / +5.638 | +5.797 / +4.857 (31.9 + 14.2; 64910; h3 (GVHI), B1_21.65) | - |
| stop045 | GM-02 | all | +0.510 / +0.301 (207.5; 145697, regular) | +8.57 % (191.1 -> 207.5) | +0.400 / +0.206 (p1) | +0.283 / +0.105 (19.0 + 225.2; 145697; g3 (GVLO), B1_2) | +0.202 / +0.036 (+16.4 MPa) |
| stop045 | GM-02 | regular | +0.510 / +0.301 (207.5; 145697, regular) | +8.57 % (191.1 -> 207.5) | +0.400 / +0.206 (p1) | +0.283 / +0.105 (19.0 + 225.2; 145697; g3 (GVLO), B1_2) | +0.202 / +0.036 (+16.4 MPa) |
| stop090 | GM-01 | all | +0.993 / +0.717 (157.2; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.993 / +0.717 | +0.971 / +0.699 (28.0 + 130.9; 79484; h3 (GVHI), B1_2) | - |
| stop090 | GM-01 | regular | +0.993 / +0.717 (157.2; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.993 / +0.717 | +0.971 / +0.699 (28.0 + 130.9; 79484; h3 (GVHI), B1_2) | - |
| stop090 | GM-02 | all | +0.925 / +0.658 (162.8; 156852, regular) | no R2; 0.75 mm from R2-checked node 156946 | +0.925 / +0.658 | +0.561 / +0.345 (22.2 + 178.5; 156946; h3 (GVHI), B1_21.65) | - |
| stop090 | GM-02 | regular | +0.925 / +0.658 (162.8; 156852, regular) | no R2; 0.75 mm from R2-checked node 156946 | +0.925 / +0.658 | +0.561 / +0.345 (22.2 + 178.5; 156946; h3 (GVHI), B1_21.65) | - |
| stop135 | GM-01 | all | +1.245 / +0.934 (139.6; 79425, regular) | no R2; 0.12 mm from R2-checked node 79483 | +1.245 / +0.934 | +1.221 / +0.914 (28.0 + 113.1; 79425; h3 (GVHI), B1_2) | - |
| stop135 | GM-01 | regular | +1.245 / +0.934 (139.6; 79425, regular) | no R2; 0.12 mm from R2-checked node 79483 | +1.245 / +0.934 | +1.221 / +0.914 (28.0 + 113.1; 79425; h3 (GVHI), B1_2) | - |
| stop135 | GM-02 | all | +3.667 / +3.021 (67.1; 132532, RE 0.0969 mm) | no R2; 7.66 mm from R2-checked node 132562 | +3.667 / +3.021 | +3.377 / +2.771 (51.8 + 19.8; 132532; h3 (GVHI), B1_21.65) | - |
| stop135 | GM-02 | regular | +9.048 / +7.658 (31.2; 157190, regular) | no R2; 0.37 mm from R2-checked node 156955 | +9.048 / +7.658 | +7.521 / +6.342 (23.8 + 13.0; 156955; h3 (GVHI), B1_1) | - |
| stop180 | GM-01 | all | +1.053 / +0.769 (152.6; 79750, regular) | no R2; 2.14 mm from R2-checked node 79483 | +1.053 / +0.769 | +1.039 / +0.757 (26.9 + 126.8; 79750; g3 (GVLO), B1_2) | - |
| stop180 | GM-01 | regular | +1.053 / +0.769 (152.6; 79750, regular) | no R2; 2.14 mm from R2-checked node 79483 | +1.053 / +0.769 | +1.039 / +0.757 (26.9 + 126.8; 79750; g3 (GVLO), B1_2) | - |
| stop180 | GM-02 | all | +1.038 / +0.756 (153.8; 144722, regular) | no R2; 1.36 mm from R2-checked node 145697 | +1.038 / +0.756 | +1.074 / +0.787 (18.3 + 132.8; 144722; g3 (GVLO), B1_2) | - |
| stop180 | GM-02 | regular | +1.038 / +0.756 (153.8; 144722, regular) | no R2; 1.36 mm from R2-checked node 145697 | +1.038 / +0.756 | +1.074 / +0.787 (18.3 + 132.8; 144722; g3 (GVLO), B1_2) | - |
| stop225 | GM-01 | all | +3.155 / +2.580 (75.4; 58609, RE 0.2057 mm) | no R2; peak node = R2-checked node (stop045 -0.4 %) | +3.155 / +2.580 | +2.143 / +1.708 (70.3 + 29.4; 58609; h3 (GVHI), B1_21.65) | - |
| stop225 | GM-01 | regular | +7.512 / +6.335 (36.8; 64910, regular) | no R2; peak node = R2-checked node (stop045 -0.3 %) | +7.512 / +6.335 | +5.651 / +4.731 (31.9 + 15.3; 64910; h3 (GVHI), B1_21.65) | - |
| stop225 | GM-02 | all | +1.198 / +0.894 (142.6; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +1.198 / +0.894 | +1.245 / +0.935 (19.0 + 120.5; 145697; g3 (GVLO), B1_2) | - |
| stop225 | GM-02 | regular | +1.198 / +0.894 (142.6; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +1.198 / +0.894 | +1.245 / +0.935 (19.0 + 120.5; 145697; g3 (GVLO), B1_2) | - |
| stop270 | GM-01 | all | +0.888 / +0.627 (165.9; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +0.888 / +0.627 | +0.433 / +0.235 (29.0 + 189.6; 65042; h3 (GVHI), B1_21.65) | - |
| stop270 | GM-01 | regular | +0.888 / +0.627 (165.9; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +0.888 / +0.627 | +0.433 / +0.235 (29.0 + 189.6; 65042; h3 (GVHI), B1_21.65) | - |
| stop270 | GM-02 | all | +0.953 / +0.683 (160.5; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.953 / +0.683 | +0.978 / +0.705 (19.0 + 139.3; 145697; g3 (GVLO), B1_2) | - |
| stop270 | GM-02 | regular | +0.953 / +0.683 (160.5; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.953 / +0.683 | +0.978 / +0.705 (19.0 + 139.3; 145697; g3 (GVLO), B1_2) | - |
| stop315 | GM-01 | all | +0.534 / +0.322 (204.3; 79483, regular) | +2.19 % (199.9 -> 204.3) | +0.534 / +0.322 | +0.220 / +0.052 (28.0 + 228.7; 79483; h3 (GVHI), B1_2) | - |
| stop315 | GM-01 | regular | +0.534 / +0.322 (204.3; 79483, regular) | +2.19 % (199.9 -> 204.3) | +0.534 / +0.322 | +0.220 / +0.052 (28.0 + 228.7; 79483; h3 (GVHI), B1_2) | - |
| stop315 | GM-02 | all | +4.028 / +3.333 (62.3; 132562, RE 0.0969 mm) | +2.96 % (60.5 -> 62.3) | +4.028 / +3.333 | +3.085 / +2.520 (56.6 + 20.1; 132562; h3 (GVHI), B1_21.65) | - |
| stop315 | GM-02 | regular | +7.937 / +6.701 (35.1; 156955, regular) | +2.10 % (34.3 -> 35.1) | +7.937 / +6.701 | +7.367 / +6.210 (23.8 + 13.6; 156955; h3 (GVHI), B1_1) | - |

## F2 GS (servo stall) at the 9 cone poses

| pose | lever | set | cold MS y / u (vM MPa; node, class) | R2 -> R3 | cell MS y / u | hot bound MS y / u (vM_LC1 + vMD MPa; node; base, state) | hot + p1 | TD / LC6 cold MS y |
|---|---|---|---|---|---|---|---|---|
| neutral | GM-01 | all | +1.330 / +1.008 (134.5; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +1.330 / +1.008 | +0.671 / +0.440 (28.0 + 159.5; 79483; h3 (GVHI), B1_2) | - | +2.898 / +45.058 |
| neutral | GM-01 | regular | +1.330 / +1.008 (134.5; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +1.330 / +1.008 | +0.671 / +0.440 (28.0 + 159.5; 79483; h3 (GVHI), B1_2) | - | +5.087 / +45.058 |
| neutral | GM-02 | all | +1.300 / +0.982 (136.2; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +1.300 / +0.982 | +0.790 / +0.542 (19.0 + 156.0; 145697; g3 (GVLO), B1_2) | - | +3.764 / +60.031 |
| neutral | GM-02 | regular | +1.300 / +0.982 (136.2; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +1.300 / +0.982 | +0.790 / +0.542 (19.0 + 156.0; 145697; g3 (GVLO), B1_2) | - | +5.945 / +65.275 |
| alpha+ | GM-01 | all | +0.648 / +0.420 (190.2; 65042, regular) | +3.90 % (183.0 -> 190.2) | +0.648 / +0.420 | +0.289 / +0.111 (29.0 + 214.1; 65042; h3 (GVHI), B1_21.65) | - | +3.014 / +48.519 |
| alpha+ | GM-01 | regular | +0.648 / +0.420 (190.2; 65042, regular) | +3.90 % (183.0 -> 190.2) | +0.648 / +0.420 | +0.289 / +0.111 (29.0 + 214.1; 65042; h3 (GVHI), B1_21.65) | - | +4.666 / +48.519 |
| alpha+ | GM-02 | all | +1.098 / +0.808 (149.3; 145697, regular) | +6.84 % (139.8 -> 149.3) | +0.972 / +0.699 (p1) | +0.654 / +0.426 (19.0 + 170.4; 145697; g3 (GVLO), B1_2) | +0.575 / +0.357 (+9.6 MPa) | +3.739 / +59.368 |
| alpha+ | GM-02 | regular | +1.098 / +0.808 (149.3; 145697, regular) | +6.84 % (139.8 -> 149.3) | +0.972 / +0.699 (p1) | +0.654 / +0.426 (19.0 + 170.4; 145697; g3 (GVLO), B1_2) | +0.575 / +0.357 (+9.6 MPa) | +5.903 / +63.086 |
| alpha- | GM-01 | all | +1.135 / +0.840 (146.8; 79484, regular) | +3.57 % (141.7 -> 146.8) | +1.135 / +0.840 | +0.558 / +0.343 (28.0 + 173.0; 79484; h3 (GVHI), B1_2) | - | +2.660 / +47.202 |
| alpha- | GM-01 | regular | +1.135 / +0.840 (146.8; 79484, regular) | +3.57 % (141.7 -> 146.8) | +1.135 / +0.840 | +0.558 / +0.343 (28.0 + 173.0; 79484; h3 (GVHI), B1_2) | - | +5.229 / +47.202 |
| alpha- | GM-02 | all | +0.671 / +0.440 (187.5; 156946, regular) | +5.26 % (178.2 -> 187.5) | +0.591 / +0.371 (p1) | +0.392 / +0.200 (22.2 + 202.8; 156946; h3 (GVHI), B1_21.65) | +0.337 / +0.152 (+9.4 MPa) | +3.783 / +61.380 |
| alpha- | GM-02 | regular | +0.671 / +0.440 (187.5; 156946, regular) | +5.26 % (178.2 -> 187.5) | +0.591 / +0.371 (p1) | +0.392 / +0.200 (22.2 + 202.8; 156946; h3 (GVHI), B1_21.65) | +0.337 / +0.152 (+9.4 MPa) | +5.537 / +79.751 |
| beta+ | GM-01 | all | +0.724 / +0.485 (181.8; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.724 / +0.485 | +0.333 / +0.149 (28.0 + 207.0; 79484; h3 (GVHI), B1_2) | - | +2.786 / +49.605 |
| beta+ | GM-01 | regular | +0.724 / +0.485 (181.8; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.724 / +0.485 | +0.333 / +0.149 (28.0 + 207.0; 79484; h3 (GVHI), B1_2) | - | +5.113 / +49.605 |
| beta+ | GM-02 | all | +0.699 / +0.464 (184.4; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.699 / +0.464 | +0.410 / +0.215 (19.0 + 203.1; 145697; g3 (GVLO), B1_2) | - | +3.643 / +57.344 |
| beta+ | GM-02 | regular | +0.699 / +0.464 (184.4; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.699 / +0.464 | +0.410 / +0.215 (19.0 + 203.1; 145697; g3 (GVLO), B1_2) | - | +5.980 / +76.959 |
| beta- | GM-01 | all | +1.140 / +0.844 (146.5; 64736, regular) | no R2; 0.38 mm from R2-checked node 64910 | +1.140 / +0.844 | +0.565 / +0.349 (30.7 + 169.5; 64736; h3 (GVHI), B1_21.65) | - | +2.998 / +42.346 |
| beta- | GM-01 | regular | +1.140 / +0.844 (146.5; 64736, regular) | no R2; 0.38 mm from R2-checked node 64910 | +1.140 / +0.844 | +0.565 / +0.349 (30.7 + 169.5; 64736; h3 (GVHI), B1_21.65) | - | +4.988 / +42.346 |
| beta- | GM-02 | all | +1.158 / +0.860 (145.2; 156946, regular) | no R2; peak node = R2-checked node (alpha- +5.3 %, alpha- +5.3 %) | +1.158 / +0.860 | +0.696 / +0.462 (22.2 + 162.5; 156946; h3 (GVHI), B1_21.65) | - | +3.944 / +57.337 |
| beta- | GM-02 | regular | +1.158 / +0.860 (145.2; 156946, regular) | no R2; peak node = R2-checked node (alpha- +5.3 %, alpha- +5.3 %) | +1.158 / +0.860 | +0.696 / +0.462 (22.2 + 162.5; 156946; h3 (GVHI), B1_21.65) | - | +5.704 / +57.337 |
| combined045 | GM-01 | all | +0.860 / +0.603 (168.5; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.860 / +0.603 | +0.410 / +0.215 (28.0 + 194.2; 79484; h3 (GVHI), B1_2) | - | +2.698 / +47.648 |
| combined045 | GM-01 | regular | +0.860 / +0.603 (168.5; 79484, regular) | no R2; peak node = R2-checked node (alpha- +3.6 %, alpha- +3.6 %) | +0.860 / +0.603 | +0.410 / +0.215 (28.0 + 194.2; 79484; h3 (GVHI), B1_2) | - | +5.233 / +47.648 |
| combined045 | GM-02 | all | +0.675 / +0.443 (187.1; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.675 / +0.443 | +0.398 / +0.205 (19.0 + 205.0; 145697; g3 (GVLO), B1_2) | - | +3.691 / +59.009 |
| combined045 | GM-02 | regular | +0.675 / +0.443 (187.1; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.675 / +0.443 | +0.398 / +0.205 (19.0 + 205.0; 145697; g3 (GVLO), B1_2) | - | +5.753 / +75.677 |
| combined135 | GM-01 | all | +1.345 / +1.020 (133.6; 79425, regular) | no R2; 0.12 mm from R2-checked node 79483 | +1.345 / +1.020 | +0.667 / +0.436 (28.0 + 160.1; 79425; h3 (GVHI), B1_2) | - | +2.767 / +45.394 |
| combined135 | GM-01 | regular | +1.345 / +1.020 (133.6; 79425, regular) | no R2; 0.12 mm from R2-checked node 79483 | +1.345 / +1.020 | +0.667 / +0.436 (28.0 + 160.1; 79425; h3 (GVHI), B1_2) | - | +5.208 / +45.394 |
| combined135 | GM-02 | all | +0.801 / +0.552 (174.0; 156946, regular) | no R2; peak node = R2-checked node (alpha- +5.3 %, alpha- +5.3 %) | +0.801 / +0.552 | +0.472 / +0.269 (22.2 + 190.6; 156946; h3 (GVHI), B1_21.65) | - | +3.893 / +62.688 |
| combined135 | GM-02 | regular | +0.801 / +0.552 (174.0; 156946, regular) | no R2; peak node = R2-checked node (alpha- +5.3 %, alpha- +5.3 %) | +0.801 / +0.552 | +0.472 / +0.269 (22.2 + 190.6; 156946; h3 (GVHI), B1_21.65) | - | +5.606 / +65.680 |
| combined225 | GM-01 | all | +0.785 / +0.538 (175.6; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +0.785 / +0.538 | +0.365 / +0.176 (29.0 + 200.6; 65042; h3 (GVHI), B1_21.65) | - | +3.027 / +44.058 |
| combined225 | GM-01 | regular | +0.785 / +0.538 (175.6; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +0.785 / +0.538 | +0.365 / +0.176 (29.0 + 200.6; 65042; h3 (GVHI), B1_21.65) | - | +4.792 / +44.058 |
| combined225 | GM-02 | all | +1.305 / +0.986 (135.9; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +1.305 / +0.986 | +0.772 / +0.527 (19.0 + 157.8; 145697; g3 (GVLO), B1_2) | - | +3.864 / +59.215 |
| combined225 | GM-02 | regular | +1.305 / +0.986 (135.9; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +1.305 / +0.986 | +0.772 / +0.527 (19.0 + 157.8; 145697; g3 (GVLO), B1_2) | - | +5.788 / +59.215 |
| combined315 | GM-01 | all | +0.677 / +0.445 (186.9; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +0.677 / +0.445 | +0.311 / +0.130 (29.1 + 209.8; 65051; h3 (GVHI), B1_21.65) | - | +2.907 / +49.581 |
| combined315 | GM-01 | regular | +0.677 / +0.445 (186.9; 65042, regular) | no R2; peak node = R2-checked node (alpha+ +3.9 %, alpha+ +3.9 %) | +0.677 / +0.445 | +0.311 / +0.130 (29.1 + 209.8; 65051; h3 (GVHI), B1_21.65) | - | +4.836 / +50.868 |
| combined315 | GM-02 | all | +0.833 / +0.579 (171.0; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.833 / +0.579 | +0.494 / +0.288 (19.0 + 190.7; 145697; g3 (GVLO), B1_2) | - | +3.663 / +57.442 |
| combined315 | GM-02 | regular | +0.833 / +0.579 (171.0; 145697, regular) | no R2; peak node = R2-checked node (stop045 +8.6 %, stop045 +8.6 %) | +0.833 / +0.579 | +0.494 / +0.288 (19.0 + 190.7; 145697; g3 (GVLO), B1_2) | - | +6.048 / +68.143 |

## Notes

- The cold rows are the R3 post records (SIM) unchanged; the p = 1 cells are those of results/v352/lever_root_bound_v352.json (DERIVED; the R2 and R3 values are shown).  At the 13 poses without an R2 run the cell is the R3 value (no R2 run there), and the row says whether the peak node is one of the R2-checked peak nodes; this table does not extend the p = 1 rule to them.
- The hot rows are a LOWER BOUND on the hot margin (sub-additivity: vM(A + D) <= vM(A) + vM(D)); the exact hot sum is not available because the pose runs carry no thermal step.  The pose-by-pose minimum reproduces the published envelope bound exactly (check above).
- 'hot + p1' adds the cold R3 - R2 peak difference (MPa) at every node of the lever: a uniform shift, conservative away from the peak; it is not a hot R2 / R3 study.
- Node classes (all-node rule 234 (4)): regular, RE (re-entrant edge within 1 mm), ID (idealisation), BT (low-quality tet); the regular set excludes them.
