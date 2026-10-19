Modal, CAD v3.5.1, asm v1.2, model modal_v351ca2b_c71: 83173 nodes (every body at level 2), 60 modes to 5130 Hz (T_min 0.195 ms), rigid airframe holes, rigid servo output, unstressed, T_REF. SIM.

| mode | f Hz | T ms | shape | engine KE share | engine rigid share | eff. mass kg (x, y, z) | eff. inertia about pivot kg m2 (x, y, z) |
|---|---|---|---|---|---|---|---|
| 1 | 51.4 | 19.45 | engine rocking about the inner axis (beta) | 1.00 | 1.00 | 0.000, 0.001, 0.015 | 0.0000, 0.0585, 0.0000 |
| 2 | 59.4 | 16.83 | engine rocking about the outer axis X (alpha, engine + ring) | 1.00 | 0.97 | 0.000, 0.001, 0.000 | 0.0590, 0.0000, 0.0000 |
| 3 | 186.3 | 5.37 | local: pintle_linkage 81%, aft_TC09 13%, case 3% | 1.00 | 0.17 | 0.014, 0.465, 0.001 | 0.0001, 0.0000, 0.0000 |
| 4 | 266.5 | 3.75 | engine lateral X (on the mount) | 0.97 | 0.90 | 2.191, 0.407, 0.178 | 0.0000, 0.0001, 0.0000 |
| 5 | 372.1 | 2.69 | engine lateral Y (on the mount) | 0.99 | 0.86 | 0.538, 1.425, 0.376 | 0.0000, 0.0001, 0.0000 |
| 6 | 408.3 | 2.45 | engine axial (thrust path through the gimbal) | 0.98 | 0.96 | 0.005, 0.427, 2.463 | 0.0000, 0.0003, 0.0000 |
| 7 | 518.2 | 1.93 | local: pintle_linkage 62%, head 13%, fwd_equipment 10% | 0.98 | 0.27 | 0.274, 0.066, 0.006 | 0.0000, 0.0000, 0.0000 |
| 8 | 791.7 | 1.26 | local: pintle_linkage 99%, case 0%, aft_TC09 0% | 1.00 | 0.01 | 0.000, 0.000, 0.002 | 0.0000, 0.0000, 0.0000 |
| 9 | 824.7 | 1.21 | local: fwd_equipment 40%, aft_TC09 19%, case 13% | 0.96 | 0.54 | 0.001, 0.022, 0.002 | 0.0000, 0.0000, 0.0014 |
| 10 | 916.9 | 1.09 | local: case 25%, fwd_equipment 25%, aft_TC09 15% | 0.93 | 0.06 | 0.065, 0.000, 0.008 | 0.0000, 0.0000, 0.0001 |
| 11 | 1010.3 | 0.99 | local: case 31%, aft_TC09 20%, fwd_equipment 20% | 0.97 | 0.31 | 0.032, 0.116, 0.003 | 0.0000, 0.0000, 0.0003 |
| 12 | 1090.9 | 0.92 | local: pintle_linkage 87%, case 4%, fwd_equipment 3% | 1.00 | 0.03 | 0.001, 0.005, 0.002 | 0.0000, 0.0000, 0.0000 |
| 13 | 1188.8 | 0.84 | local: fwd_equipment 57%, case 15%, aft_TC09 13% | 0.98 | 0.21 | 0.000, 0.013, 0.002 | 0.0000, 0.0000, 0.0001 |
| 14 | 1220.0 | 0.82 | local: fwd_equipment 52%, case 22%, aft_TC09 11% | 0.97 | 0.09 | 0.028, 0.033, 0.001 | 0.0000, 0.0000, 0.0000 |
| 15 | 1466.4 | 0.68 | local: pintle_linkage 95%, aft_TC09 3%, fwd_equipment 1% | 1.00 | 0.01 | 0.000, 0.000, 0.001 | 0.0000, 0.0000, 0.0000 |
| 16 | 1611.2 | 0.62 | local: servo_brackets 42%, servos 40%, collar 10% | 0.11 | 0.00 | 0.000, 0.182, 0.000 | 0.0007, 0.0000, 0.0000 |

Engine-mount modes (first mode per engine rigid-body DOF); rocking with the servo output compliance in series (DERIVED):

| DOF | mode | f FE, rigid servo Hz | Rayleigh check (static K same mesh) Hz | f at the pose-model K Hz | f with servo k_s 58 / 174 Hz | K used N m/rad |
|---|---|---|---|---|---|---|
| engine rocking about the inner axis (beta) | 1 | 51.4 | 51.9 | 47.8 | 21.3 / 31.3 | 6209 (same mesh), 5370 (pose model), servo 1070 / 2295 |
| engine rocking about the outer axis X (alpha, engine + ring) | 2 | 59.4 | 59.9 | 55.5 | 21.9 / 33.1 | 8347 (same mesh), 7284 (pose model), servo 1129 / 2586 |
| engine lateral X (on the mount) | 4 | 266.5 | - | - | - | - |
| engine lateral Y (on the mount) | 5 | 372.1 | - | - | - | - |
| engine axial (thrust path through the gimbal) | 6 | 408.3 | - | - | - | - |

Load-path periods under chamber pressure (lead 194 domain; shares of the static OP response carried by modes in each band):

| path | governing T ms (basis) | share T > 1 ms | share 0.1-1 ms | residual (T < T_min) | FA-1 column |
|---|---|---|---|---|---|
| pintle / linkage (needle vs seat, axial) | 2.449 (mode 6) | +0.61 | +0.30 | +0.09 | T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies |
| forward closure head (seat vs rim, axial) | 19.447 (mode 1) | +0.63 | -0.07 | +0.44 | T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies |
| nozzle on the J1 lip (NZ-01 vs TC-09 lip, axial) | < 0.195 (residual of the modes above f_max carrie) | -0.00 | +0.11 | +0.90 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| engine axial on the mount | 2.449 (mode 6) | +1.06 | -0.18 | +0.12 | T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies |
| Pc transducer (ASSUMED 26 g) relative to the head | < 0.195 (residual of the modes above f_max carrie) | -0.29 | +0.50 | +0.79 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| forward equipment: torch | 0.498 (mode 20) | +0.50 | -3.04 | +3.54 | T > 1 ms share 50%: FA1S on that share, FA1Q (93 / 102 bar) on the rest |
| forward equipment: riser | 0.498 (mode 20) | +3.31 | -6.40 | +4.09 | T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies |
| forward equipment: bleed valve | 0.210 (mode 57) | -0.85 | -2.93 | +4.78 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| forward equipment: FD-02 | < 0.195 (residual of the modes above f_max carrie) | -0.14 | -2.20 | +3.34 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| forward equipment: FD-04 | < 0.195 (residual of the modes above f_max carrie) | +0.08 | +0.62 | +0.30 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| pintle drive (PD-02) relative to the head | < 0.195 (residual of the modes above f_max carrie) | -0.08 | +0.09 | +0.99 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| GM-01 node 36503 (LC1@B1_21.65 MS 12.710 (mapped 0.15 mm from L1 node 85791)) | < 0.195 (residual of the modes above f_max carrie) | -0.06 | -0.00 | +1.06 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| GM-02 node 42321 (LC1@B1_21.65 MS 17.402 (mapped 0.31 mm from L1 node 101317)) | 0.464 (mode 23) | -0.10 | +0.01 | +1.09 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| GM-02 node 42480 (FA1Q@A1_22.2 MS 6.472 (mapped 1.51 mm from L1 node 102248)) | < 0.195 (residual of the modes above f_max carrie) | +0.32 | +0.20 | +0.48 | T > 1 ms share 32%: FA1S on that share, FA1Q (93 / 102 bar) on the rest |
| GM-03 node 56891 (FA1Q@A1_22.2 MS 3.849 (mapped 0.19 mm from L1 node 129757)) | 19.447 (mode 1) | +0.95 | -0.07 | +0.12 | T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies |
| GM-03 node 56900 (LC1@B1_21.65 MS 13.115 (mapped 1.34 mm from L1 node 129184)) | 3.753 (mode 4) | +0.88 | +0.00 | +0.12 | T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies |
| NZ-01 node 30938 (LC1@B1_21.65 MS -0.210 (mapped 1.10 mm from L1 node 73187)) | < 0.195 (residual of the modes above f_max carrie) | -0.00 | +0.05 | +0.96 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| NZ-01 node 32380 (FA1Q@A1_22.2 MS 3.400 (mapped 0.82 mm from L1 node 72409)) | < 0.195 (residual of the modes above f_max carrie) | -0.00 | +0.10 | +0.90 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| NZ-01 node 32601 (LC1@B1_19 MS -0.225 (mapped 0.85 mm from L1 node 74445)) | < 0.195 (residual of the modes above f_max carrie) | -0.00 | +0.00 | +1.00 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-01 node 2785 (LC1@B1_2 MS 2.269 (mapped 0.55 mm from L1 node 8314)) | < 0.195 (residual of the modes above f_max carrie) | +0.02 | +0.60 | +0.38 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-01 node 2800 (LC1@B1_21.65 MS 1.383 (mapped 0.78 mm from L1 node 8843)) | < 0.195 (residual of the modes above f_max carrie) | +0.03 | +0.52 | +0.44 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-02 node 8035 (LC1@B1_21.65 MS 0.646 (mapped 0.00 mm from L1 node 26334)) | < 0.195 (residual of the modes above f_max carrie) | +0.03 | +0.42 | +0.55 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-02 node 14242 (FA1Q@A1_22.2 MS 2.118 (mapped 1.01 mm from L1 node 41165)) | < 0.195 (residual of the modes above f_max carrie) | +0.07 | +0.61 | +0.32 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-03 node 18601 (LC1@B1_19 MS 0.289 (mapped 0.10 mm from L1 node 44861)) | < 0.195 (residual of the modes above f_max carrie) | +0.11 | +0.42 | +0.46 | T > 1 ms share 11%: FA1S on that share, FA1Q (93 / 102 bar) on the rest |
| TC-03 node 19390 (FA1Q@A1_22.2 MS 4.650 (mapped 0.74 mm from L1 node 46193)) | < 0.195 (residual of the modes above f_max carrie) | -0.13 | +0.06 | +1.08 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-03 node 19648 (LC1@B1_21.65 MS 0.521 (mapped 0.63 mm from L1 node 46790)) | 0.469 (mode 22) | -0.01 | +1.03 | -0.01 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-09 node 25238 (LC1@B1_2 MS 8.895 (mapped 0.22 mm from L1 node 55385)) | < 0.195 (residual of the modes above f_max carrie) | -0.01 | +0.18 | +0.83 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-09 node 25719 (FA1Q@A1_22.2 MS 2.780 (mapped 1.80 mm from L1 node 64682)) | < 0.195 (residual of the modes above f_max carrie) | -0.00 | +0.17 | +0.83 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
| TC-09 node 26534 (LC1@B1_21.65 MS 1.230 (mapped 1.80 mm from L1 node 57605)) | < 0.195 (residual of the modes above f_max carrie) | -0.00 | +0.06 | +0.94 | fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column only if the residual is shown to be T <= 0.1 ms |
