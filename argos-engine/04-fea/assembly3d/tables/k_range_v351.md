K about the gimbal axes, N m/rad (engine best-fit rotation; SIM rigid servo output; DERIVED with servo k_s 58 / 174 N m/rad per servo in series).

| group | run | pose (alpha, beta) deg | K_alpha FE | K_alpha +servo 58 / 174 | K_beta FE | K_beta +servo 58 / 174 | rods-only alpha / beta | structure share alpha / beta |
|---|---|---|---|---|---|---|---|---|
| stop (8 deg), rigid airframe | pose_stop000_c71 | -0.00, +8.00 | 6400 | 1060 / 2389 | 6570 | 1364 / 2891 | 31026 / 42028 | 0.79 / 0.84 |
| stop (8 deg), rigid airframe | pose_stop045_c71 | -5.68, +5.65 | 6531 | 1051 / 2385 | 6348 | 1274 / 2727 | 30587 / 38935 | 0.79 / 0.84 |
| stop (8 deg), rigid airframe | pose_stop090_c71 | -8.00, +0.00 | 6954 | 1050 / 2420 | 5488 | 1022 / 2234 | 30223 / 30677 | 0.77 / 0.82 |
| stop (8 deg), rigid airframe | pose_stop135_c71 | -5.68, -5.65 | 7844 | 1079 / 2538 | 4426 | 775 / 1723 | 30548 / 22965 | 0.74 / 0.81 |
| stop (8 deg), rigid airframe | pose_stop180_c71 | -0.00, -8.00 | 8577 | 1102 / 2630 | 3888 | 686 / 1522 | 30882 / 20355 | 0.72 / 0.81 |
| stop (8 deg), rigid airframe | pose_stop225_c71 | +5.68, -5.65 | 7856 | 1079 / 2539 | 4163 | 767 / 1681 | 30548 / 22965 | 0.74 / 0.82 |
| stop (8 deg), rigid airframe | pose_stop270_c71 | +8.00, -0.00 | 6964 | 1051 / 2421 | 5176 | 1011 / 2181 | 30223 / 30677 | 0.77 / 0.83 |
| stop (8 deg), rigid airframe | pose_stop315_c71 | +5.68, +5.65 | 6533 | 1051 / 2385 | 6183 | 1267 / 2696 | 30587 / 38935 | 0.79 / 0.84 |
| stop045, compliant airframe | pose_stop045_compliant_c71 | -5.68, +5.65 | 5609 | 1024 / 2250 | 5520 | 1237 / 2562 | 30587 / 38935 | 0.82 / 0.86 |

| group | K_alpha FE | K_alpha +servo 58 | K_alpha +servo 174 | K_beta FE | K_beta +servo 58 | K_beta +servo 174 |
|---|---|---|---|---|---|---|
| stop (8 deg), rigid airframe | 6400-8577 | 1050-1102 | 2385-2630 | 3888-6570 | 686-1364 | 1522-2891 |
| stop045, compliant airframe | 5609-5609 | 1024-1024 | 2250-2250 | 5520-5520 | 1237-1237 | 2562-2562 |
| ALL | 5609-8577 | 1024-1102 | 2250-2630 | 3888-6570 | 686-1364 | 1522-2891 |

V5c comparison (Mechanical SIM, hub/04-fea/stiffness/gimbal_k_summary_V5c_v1.json 82a737caa138259a; CAD v3.3, engine case rigid, 9 poses at 7 deg; ENG-11 range 3133-7406 per CHANGELOG 188 (7)):

| V5c variant | K_alpha | K_beta |
|---|---|---|
| mech_T | 5808-7406 | 3239-5167 |
| mech_T_chainlow | 5573-7026 | 3133-5023 |
| mech_C_chainhigh | 6609-8764 | 3585-5630 |
| mech_rigidchain | 7328-10080 | 3880-6015 |
| smin_T | 1110-1299 | 780-1508 |
| smax_T | 2485-2757 | 1579-2857 |
