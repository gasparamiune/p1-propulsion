# K about the gimbal axes, v3.5.2 republication (RM2-05)

N m/rad. Engine best-fit rotation. SIM: FE unit steps EAX / EAY, asm v1.2, CAD v3.5.1 c71 pose runs, rigid servo output. DERIVED: servo output compliance in series with r_eff,i = |((H_i - C_i) x e_i) . e_t,i| per servo and pose, k_s 58 / 174 N m/rad per servo (ASSUMED, TO-VERIFY bench B-TVC).

- **coupled** = 1 / C_jj: the other axis is moment-free (a single-axis load; this is what the EAX / EAY steps measure).
- **diagonal** = (C^-1)_jj: the other axis is held at zero rotation.
- With the servo, C = C_FE + A^-T diag(r_eff,i^2 / k_s) A^-1. This is exact, because the two rods make the restraint statically determinate.
- scalar r_eff = K_FE (single-axis step) in series with sum_i (k_s / r_eff,i^2) a_ij^2, the scalar form REV-MECH-2 (f2) uses.
- The superseded r_h values (v3.5.1, r_h 11.139 mm at every pose) are given in results/k_range_v352.json for comparison only.

## Per pose

| group | run | pose (alpha, beta) deg | r_eff 1 / 2 mm | FE alpha coupled / diag | FE beta coupled / diag | alpha +k_s 58 coupled / diag | beta +k_s 58 coupled / diag | alpha +k_s 174 coupled / diag | beta +k_s 174 coupled / diag | scalar r_eff 58: alpha / beta | scalar r_eff 174: alpha / beta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stop (8 deg), rigid airframe | pose_stop000_c71 | -0.00, +8.00 | 9.43 / 9.43 | 6400 / 6401 | 6570 / 6571 | 1388 / 1388 | 1759 / 1759 | 2905 / 2905 | 3436 / 3436 | 1388 / 1759 | 2905 / 3436 |
| stop (8 deg), rigid airframe | pose_stop045_c71 | -5.68, +5.65 | 11.07 / 7.88 | 6531 / 6533 | 6348 / 6350 | 1329 / 1475 | 1530 / 1698 | 2834 / 2982 | 3097 / 3258 | 1523 / 1741 | 3116 / 3373 |
| stop (8 deg), rigid airframe | pose_stop090_c71 | -8.00, +0.00 | 10.61 / 9.88 | 6954 / 6961 | 5488 / 5493 | 1170 / 1226 | 1111 / 1165 | 2626 / 2698 | 2373 / 2438 | 1237 / 1172 | 2737 / 2464 |
| stop (8 deg), rigid airframe | pose_stop135_c71 | -5.68, -5.65 | 9.77 / 11.10 | 7844 / 7850 | 4426 / 4430 | 1169 / 1173 | 866 / 869 | 2701 / 2708 | 1868 / 1872 | 1173 / 869 | 2708 / 1872 |
| stop (8 deg), rigid airframe | pose_stop180_c71 | -0.00, -8.00 | 10.23 / 10.23 | 8577 / 8578 | 3888 / 3888 | 1275 / 1275 | 787 / 787 | 2949 / 2949 | 1681 / 1681 | 1275 / 787 | 2949 / 1681 |
| stop (8 deg), rigid airframe | pose_stop225_c71 | +5.68, -5.65 | 11.10 / 9.77 | 7856 / 7867 | 4162 / 4168 | 1169 / 1173 | 856 / 859 | 2702 / 2710 | 1819 / 1824 | 1173 / 858 | 2710 / 1823 |
| stop (8 deg), rigid airframe | pose_stop270_c71 | +8.00, -0.00 | 9.88 / 10.61 | 6964 / 6974 | 5176 / 5184 | 1170 / 1226 | 1098 / 1151 | 2627 / 2701 | 2313 / 2378 | 1237 / 1158 | 2738 / 2400 |
| stop (8 deg), rigid airframe | pose_stop315_c71 | +5.68, +5.65 | 7.88 / 11.07 | 6533 / 6536 | 6183 / 6186 | 1329 / 1476 | 1520 / 1688 | 2835 / 2985 | 3057 / 3220 | 1523 / 1729 | 3117 / 3326 |
| range cone (7 deg) + neutral, rigid airframe | pose_neutral_c71 | +0.00, +0.00 | 11.14 / 11.14 | 7284 / 7284 | 5370 / 5370 | 1129 / 1129 | 1070 / 1070 | 2586 / 2586 | 2295 / 2295 | 1129 / 1070 | 2586 / 2295 |
| range cone (7 deg) + neutral, rigid airframe | pose_alpha+_c71 | +7.00, +0.00 | 10.23 / 10.71 | 6992 / 6997 | 5184 / 5188 | 1157 / 1192 | 1092 / 1125 | 2607 / 2654 | 2305 / 2346 | 1199 / 1130 | 2678 / 2360 |
| range cone (7 deg) + neutral, rigid airframe | pose_alpha-_c71 | -7.00, +0.00 | 10.71 / 10.23 | 6985 / 6988 | 5453 / 5456 | 1156 / 1192 | 1104 / 1137 | 2606 / 2652 | 2357 / 2398 | 1199 / 1142 | 2677 / 2415 |
| range cone (7 deg) + neutral, rigid airframe | pose_beta+_c71 | +0.00, +7.00 | 9.90 / 9.90 | 6430 / 6430 | 6380 / 6380 | 1299 / 1299 | 1597 / 1597 | 2776 / 2776 | 3193 / 3193 | 1299 / 1597 | 2776 / 3193 |
| range cone (7 deg) + neutral, rigid airframe | pose_beta-_c71 | +0.00, -7.00 | 10.42 / 10.42 | 8364 / 8364 | 4082 / 4082 | 1246 / 1246 | 821 / 821 | 2880 / 2880 | 1756 / 1756 | 1246 / 821 | 2880 / 1756 |
| range cone (7 deg) + neutral, rigid airframe | pose_combined045_c71 | -4.96, +4.94 | 11.09 / 8.86 | 6563 / 6564 | 6184 / 6184 | 1259 / 1331 | 1428 / 1510 | 2730 / 2808 | 2931 / 3015 | 1353 / 1529 | 2874 / 3069 |
| range cone (7 deg) + neutral, rigid airframe | pose_combined135_c71 | -4.96, -4.94 | 10.04 / 11.11 | 7779 / 7782 | 4552 / 4553 | 1167 / 1170 | 892 / 894 | 2693 / 2698 | 1922 / 1926 | 1170 / 894 | 2699 / 1926 |
| range cone (7 deg) + neutral, rigid airframe | pose_combined225_c71 | +4.96, -4.94 | 11.11 / 10.04 | 7788 / 7794 | 4326 / 4329 | 1167 / 1171 | 883 / 885 | 2695 / 2700 | 1881 / 1885 | 1171 / 885 | 2700 / 1884 |
| range cone (7 deg) + neutral, rigid airframe | pose_combined315_c71 | +4.96, +4.94 | 8.86 / 11.09 | 6564 / 6566 | 6034 / 6036 | 1259 / 1332 | 1420 / 1503 | 2730 / 2810 | 2897 / 2983 | 1353 / 1520 | 2874 / 3032 |
| stop045, compliant airframe | pose_stop045_compliant_c71 | -5.68, +5.65 | 11.07 / 7.88 | 5609 / 5613 | 5520 / 5524 | 1286 / 1420 | 1477 / 1630 | 2646 / 2772 | 2886 / 3024 | 1467 / 1672 | 2890 / 3124 |

## Ranges

| group | r_eff mm | K_alpha FE coupled | K_alpha +58 coupled / diag | K_alpha +174 coupled / diag | K_beta FE coupled | K_beta +58 coupled / diag | K_beta +174 coupled / diag |
|---|---|---|---|---|---|---|---|
| stop (8 deg), rigid airframe | 7.88-11.10 | 6400-8577 | 1169-1388 / 1173-1476 | 2626-2949 / 2698-2985 | 3888-6570 | 787-1759 / 787-1759 | 1681-3436 / 1681-3436 |
| range cone (7 deg) + neutral, rigid airframe | 8.86-11.14 | 6430-8364 | 1129-1299 / 1129-1332 | 2586-2880 / 2586-2880 | 4082-6380 | 821-1597 / 821-1597 | 1756-3193 / 1756-3193 |
| stop045, compliant airframe | 7.88-11.07 | 5609-5609 | 1286-1286 / 1420-1420 | 2646-2646 / 2772-2772 | 5520-5520 | 1477-1477 / 1630-1630 | 2886-2886 / 3024-3024 |
| ALL 17 poses (rigid airframe) | 7.88-11.14 | 6400-8577 | 1129-1388 / 1129-1476 | 2586-2949 / 2586-2985 | 3888-6570 | 787-1759 / 787-1759 | 1681-3436 / 1681-3436 |

## Both axes, 17 poses (rigid airframe)

| quantity | k_s 58 | k_s 174 |
|---|---|---|
| with servo, coupled (other axis moment-free) | 787-1759 | 1681-3436 |
| with servo, diagonal (other axis held) | 787-1759 | 1681-3436 |
| with servo, scalar r_eff form (REV-MECH-2 (f2)) | 787-1759 | 1681-3436 |
| superseded r_h form (v3.5.1 published) | 686-1364 | 1522-2891 |
| FE rigid servo, coupled / diagonal | 3888-8577 / 3888-8578 | (same) |

V5c comparison (Mechanical SIM, hub/04-fea/stiffness/gimbal_k_summary_V5c_v1.json 82a737caa138259a; CAD v3.3, engine case rigid, 9 poses at 7 deg; ENG-11 range 3133-7406 per CHANGELOG 188 (7)):

| V5c variant | K_alpha | K_beta |
|---|---|---|
| mech_T | 5808-7406 | 3239-5167 |
| mech_T_chainlow | 5573-7026 | 3133-5023 |
| mech_C_chainhigh | 6609-8764 | 3585-5630 |
| mech_rigidchain | 7328-10080 | 3880-6015 |
| smin_T | 1110-1299 | 780-1508 |
| smax_T | 2485-2757 | 1579-2857 |
