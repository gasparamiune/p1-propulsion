# ARGOS H1 engine - S-3D gimbal strength on CAD v3.5.1 (F2, fea3d)

| | |
|---|---|
| Status | **2026-10-19, F2 on fea3d-asm v1.2**: 9 of 9 range-cone poses (neutral, alpha+, alpha-, beta+, beta-, combined045, combined135, combined225, combined315); the 8 deg stop poses (runaway, SR) and the FA-1 thrust spike (FA1T) are taken from F1 (REPORT-FEA3D sections 6, 4.6, 3). Replaces S-3D v1.1 (Mechanical, CAD v3.4 V5c, centre + betam7) for CAD v3.5.1 (lead 188 (6), RM1-07/15). |
| Author | fea3d (successor Senior FEA analyst 3D); brief lead CHANGELOG 188 + coordinator 2026-10-19 |
| Configuration | CAD v3.5.1 frozen (CHANGELOG 206): MANIFEST `b62c0e0ac8555fb8`, ENGINE STEP `4ca22820c796b670`; collar GM-01 / GM-02 7075-T6 with the lever-root fillets as modelled in v3.5.1 |
| Tool | CalculiX 2.21 (SPOOLES), C3D10; own pre / post (`src/`); assembly model fea3d-asm v1.2 (connector fix 7.1 of REPORT-FEA3D) |
| Units | SI; mm, N, MPa, degC where conventional. MS = allowable / (SF x stress) - 1 |
| Tags | SIM (FE), DERIVED, ASSUMED, DATASHEET, LITERATURE, TO-VERIFY, AS RECALLED |

> **Not physical approval.** Converged solutions, matching numbers or clean plots do not approve hardware. Negative margins are reported as found; none is forced.

## 1. Claims (checkpoint, SUPERVISION-WORKFLOW)

1. **GS (both servos at stall, rods +/-441 N at neutral, +/-552 N on the 7 deg cone) is NEGATIVE at both lever roots** with the fillet zone resolved (R3 refinement in every cone run): **GM-02 -0.223 / -0.330 (alpha-, 403 MPa)**, **GM-01 -0.209 / -0.319 (alpha+, 396 MPa)** [SIM]. The lever-root GS margin is ultimate-negative at 9 of 9 cone poses and yield-negative at 7 (least severe: neutral, MS_y +0.088 GM-02, MS_u -0.063 GM-02; per pose in 4.1a). Same location as the F1 LC3 finding (R1.2 lever-root fillet where it meets the R32.5 collar OD). Mechanical DESIGN CHANGE item (CHANGELOG 223 (5)); not redesigned here.
2. **SR (runaway onto the 8 deg stop = F1 LC3, rod at the 609 N stall limit):** L1 regular set GM-02 +0.182 / +0.019 (stop045), GM-01 +0.206 / +0.039 (stop315); **refined R3: GM-02 -0.280 / -0.379, GM-01 -0.273 / -0.374** (REPORT-FEA3D 4.6; the L1 value is unconservative).
3. **All other gimbal and mount parts are positive** in every case [SIM]: lowest GS GM-16a +0.852, TD GM-03 +3.417, LC6 GM-03 +9.320, LC2F (SF 1.0 / 1.5) GM-03 +4.919 (min of yield and ultimate); SR (F1 LC3, L1) GM-16b +0.791; FA1T (F1) GM-03 +1.483.
4. **Touchdown (TD, servos holding):** rod forces stay at or below 110 N against the 609 N stall force at every cone pose, so the servos hold and the engine does not reach the stop under the touchdown loads [SIM]; lever-root margins >= +3.710 (yield). LC6 rods <= 19 N, LC2F rods <= 54 N.
5. **Connector loads (GS envelope):** needle-cup radial component up to 801 N, thrust washers up to 280 N; largest M5 hole shear at the mount 808 N (AF_GM10_2, beta-) [SIM]. Bearing / washer / screw capacities against datasheets: TO-VERIFY (Mechanical).
6. **Stiffness (F3):** over the 9 cone poses K_alpha 6430-8364, K_beta 4082-6380 N m/rad (rigid servo); over the 8 stop poses 6400-8577 / 3888-6570; with the servo output (k_s 58-174 N m/rad, ASSUMED) 686-2891 N m/rad overall [SIM / DERIVED]; compliant airframe at stop045 -14 / -13 % vs rigid.
7. **Hot lower bound** (cone-pose increments added to the LC1 thermo-pressure field by sub-additivity; for the refined collars the part-maximum increment is added to every L1 node, a conservative but coarse bound): GM-01 -0.219 / -0.327, GM-02 -0.259 / -0.362 [DERIVED]; other gimbal parts in section 4.4.

## 2. Scope and what changed from S-3D v1.1

- S-3D v1.1 (Mechanical, 2026-10-13; hub `04-fea/structural/results/s3d_results_v1.1.json` beeba889ae549415, `s3d_margin_table_v1.1.csv` 8fe7b075398d9b24): CAD v3.4 V5c, poses centre and betam7 only, collar in 6061-T6 with 7075-T6 design-change columns, 1.5 mm exclusion around connectors and edges, gimbal-only model with the engine rigid.
- This F2 (lead 188 (6)): CAD v3.5.1 with the GM-01 / GM-02 lever-root fillets modelled and the collar in 7075-T6; all 9 range-cone poses + the 8 deg stop poses (F1); the flexible engine in the assembled model; v3.5.1 mass properties; gnc.json v3.1 inertial loads (flight 0.61 g lateral / 4.04 g axial, touchdown 6.29 g lateral / 5.43 g axial / 79.28 rad/s2, SIM); the FA-1 thrust spike (FA1T, F1). The GNC hinge moments (flight max 19.53 N m, touchdown 7.83 N m; gnc.json v3.1 design_limit_loads, SIM) are enveloped by GS (both-servo stall, M_engine_GS 37.95 N m) and SR (M_engine_stop 41.14 N m), mechanical.json v2.1 tvc_actuation.design_loads [DERIVED].

## 3. Method

- **Model:** the F1 assembled-engine model, fea3d-asm v1.2 (CalculiX 2.21, C3D10; connector fix 7.1 of REPORT-FEA3D), CAD v3.5.1, posed by rotating the engine group (alpha about the outer axis X, then beta about the ring axis Y) and the ring group (alpha) exactly as the Mechanical pose list (cone_to_ab, re-implemented): neutral, alpha +/-7, beta +/-7, four combined poses on the 7 deg cone (azimuths 45 / 135 / 225 / 315), and the eight 8 deg stop poses of F1 LC3. Engine pressure parts at mesh level 2 (coarse=2), all gimbal parts at L1, **both lever roots (GM-01, GM-02) with the R3 refinement ball (h 0.25 mm target, r 2.5 mm)** because F1 showed that the L1 regular-set margin there is unconservative (REPORT-FEA3D 4.6). Airframe rigid at the 16 M5 holes (the compliant variant changes the gimbal margins by <= 0.001, F1 section 8).
- **Unit steps:** OP (operating pressure distribution, 1 MPa), GX / GY / GZ (1 g on every group), EAX (1 rad/s2 of engine + ring about X), EAY (1 rad/s2 of the engine about the ring axis), R1 / R2 (unit actuator pairs across each rod spring). Cold (no thermal step; thermal stress in the gimbal is not part of S-3D, as in v1.1); allowables at the B1_21.65 node temperatures of the F1 thermal map (collar 22.8 degC). The 7075-T6 collar allowables are temperature-independent in the material table (470 / 540 MPa, LITERATURE, MMPDS bar, verify with mill cert; no 7075 temperature table yet, RM1-06 open, Mechanical), so the 60 degC bay temperature of S-3D v1.1 would not change them here; 6061-T6 parts use Fty(T)/Ftu(T) at their node temperature.
- **Cases (post_s3d.py; all superposition of the unit steps, linear elastic):**
  - **GS - both servos at stall** (S-3D v1.1 definition): rod forces prescribed at +/-F_d(pose) in all four sign corners, F_d = 441 N at neutral and 552 N on the 7 deg cone (mechanical.json v2.1 tvc_actuation.design_loads, DERIVED, lead governs); the stall moment is reacted by the engine's angular acceleration (EAX, EAY solved so the two FE rod forces equal the corner values); + OP x Pc_max 2.501 MPa + flight inertia 0.61 g lateral (8 directions) + axial {0, 4.04 g} (gnc.json v3.1 SIM max) + the hose end force 31.2 N (hose_end_reactions_v341_v1, EI 0.184 N m2, at the 8 deg stop, used as a bound at 7 deg) as an equivalent lateral g along the lateral direction (DERIVED approximation). SF 1.5 / 2.0. GS envelopes the mechanical part of the flight case LC1 at the cone poses (its rod forces lie inside the corner box; von Mises is convex in the load vector); the thermal part is covered by the hot lower bound (4.4).
  - **TD - touchdown, servos holding:** OP {0, Pc_max} + 6.29 g lateral (8 directions) + hose equivalent + axial {0, 5.43 g} + 79.28 rad/s2 in 4 directions (gnc.json v3.1 design_limit_loads touchdown, SIM max); rod forces from statics, reported against the 609 N stall force. SF 1.5 / 2.0.
  - **LC6 - hard landing** (loadcases v1 LC6, ASSUMED envelope, same 10 g as the F4 envelope): 10 g axial (both signs) + 3 g lateral (8 directions), no thrust. SF 1.5 / 2.0.
  - **LC2F - stuck-pintle thrust** 907.7 N (loadcases v2 LC2F) as OP scaled to that net thrust + flight inertia; SF 1.0 yield / 1.5 ultimate; gimbal and mount parts only.
  - **SR - runaway onto the 8 deg stop** = F1 LC3 at the 8 stop poses (rod at the 609 N stall limit, max thrust + touchdown inertia; REPORT-FEA3D 2.3, 6), with the R3 lever-root results.
  - **FA1T - FA-1 thrust spike** 3.6 kN (1.8 kN x 4 ms x DLF 2.0, CHANGELOG 194) at neutral, SF 1.0 (F1).
- **Criteria:** MS_y = Fty(T)/(SF_y vM) - 1, MS_u = Ftu(T)/(SF_u vM) - 1, regular node set (1 mm from connector patches, re-entrant edges and bad tets excluded; with the refined lever roots the fillet zone is inside the regular set).

## 4. Results

### 4.1 Per-part minimum margins, regular node set, yield / ultimate (pose of the minimum) [SIM]; SR lever root R3 from F1; FA1T from F1

| part | GS y / u (pose) | TD y / u (pose) | LC6 y / u | LC2F y / u (SF 1.0 / 1.5) | SR = F1 LC3 runaway y / u (pose), L1 | SR lever root R3 | FA1T y / u |
|---|---|---|---|---|---|---|---|
| GM-01 | -0.209 / -0.319 (alpha+) | +3.710 / +3.058 (alpha+) | +29.530 / +25.307 | +8.871 / +6.561 | +0.206 / +0.039 (stop315) | -0.273 / -0.374 | +4.979 / +5.870 |
| GM-02 | -0.223 / -0.330 (alpha-) | +3.961 / +3.275 (alpha-) | +45.191 / +38.803 | +7.605 / +5.591 | +0.182 / +0.019 (stop045) | -0.280 / -0.379 | +4.840 / +5.709 |
| GM-03 | +2.042 / +1.454 (alpha+) | +4.475 / +3.417 (beta+) | +11.792 / +9.320 | +7.254 / +4.919 | +1.368 / +0.910 (stop000) | - | +1.483 / +1.671 |
| GM-16a | +1.149 / +0.852 (combined225) | +13.662 / +11.634 (combined135) | +67.573 / +58.089 | >+99 / >+99 | +1.100 / +0.809 (stop315) | - | +30.957 / +35.716 |
| GM-16b | +1.158 / +0.859 (combined315) | +10.988 / +9.330 (combined225) | >+99 / +90.867 | +35.648 / +27.071 | +1.079 / +0.791 (stop270) | - | >+99 / >+99 |
| GM-08a | +15.264 / +12.121 (combined315) | +20.174 / +16.082 (combined225) | +50.340 / +40.419 | +36.077 / +25.588 | +8.178 / +6.404 (stop180) | - | +12.358 / +13.369 |
| GM-08b | +17.277 / +13.745 (alpha-) | +33.373 / +26.731 (alpha+) | +77.517 / +62.343 | +49.016 / +34.867 | +17.471 / +13.902 (stop315) | - | +14.399 / +15.564 |
| GM-09 | +15.323 / +12.168 (alpha-) | +17.152 / +13.644 (beta+) | +54.453 / +43.737 | +44.253 / +31.452 | +5.971 / +4.624 (stop180) | - | +11.623 / +12.578 |
| GM-10 | +3.618 / +2.725 (combined135) | +24.304 / +19.414 (beta-) | +99.929 / +80.424 | +81.040 / +57.832 | +3.655 / +2.756 (stop180) | - | +29.746 / +32.072 |
| GM-13 | +2.907 / +2.152 (combined225) | +23.379 / +18.668 (combined135) | +88.706 / +71.370 | >+99 / >+99 | +2.881 / +2.131 (stop180) | - | +57.376 / +61.793 |
| GM-14 | +3.211 / +2.397 (combined135) | +21.857 / +17.440 (combined225) | >+99 / >+99 | +71.218 / +50.788 | +3.079 / +2.291 (stop180) | - | >+99 / >+99 |
| TC-01 | +0.805 / +0.465 (beta-) | +0.829 / +0.485 (beta-) | +40.369 / +32.578 | - | +0.830 / +0.485 (stop270) | - | - |


### 4.1a GS lever-root minimum per cone pose (GM-01 / GM-02 at R3, regular set) [SIM]

| pose | MS_y (part) | MS_u (part) | vM at the MS_y node MPa | peak to the R3-ball centre, GM-01 / GM-02 mm |
|---|---|---|---|---|
| neutral | +0.088 (GM-02) | -0.063 (GM-02) | 288 | 0.58 / 0.48 |
| alpha+ | -0.209 (GM-01) | -0.319 (GM-01) | 396 | 0.58 / 0.48 |
| alpha- | -0.223 (GM-02) | -0.330 (GM-02) | 403 | 0.48 / 0.48 |
| beta+ | -0.170 (GM-02) | -0.285 (GM-02) | 378 | 0.58 / 0.48 |
| beta- | +0.033 (GM-02) | -0.110 (GM-02) | 303 | 0.58 / 0.48 |
| combined045 | -0.220 (GM-02) | -0.328 (GM-02) | 402 | 0.48 / 0.48 |
| combined135 | -0.147 (GM-02) | -0.265 (GM-02) | 367 | 0.58 / 0.48 |
| combined225 | -0.134 (GM-01) | -0.254 (GM-01) | 362 | 0.58 / 0.48 |
| combined315 | -0.204 (GM-01) | -0.314 (GM-01) | 394 | 0.58 / 0.48 |

In every pose the regular-set lever-root peak of both collar halves lies 0.48-0.58 mm from the refinement-ball centre (ball radius 2.5 mm, body frame), i.e. inside the refined zone; the ball spec is the F1 R3 spec (target h 0.25 mm, achieved about 0.34 mm in F1 4.6).

Chart S3D-C1 (`figs/S3D-C1_gimbal_margins.png`); lever-root field S3D-01 (`figs/S3D-01_alpha-_GM02_R3_zoom_vM.png`).

### 4.2 Rod forces and engine angular acceleration (GS realised by the engine inertia) [SIM]

| pose | GS rods (N) | GS engine ang. accel. rad/s2 | TD max rod abs N | LC6 max rod abs N | LC2F max rod abs N |
|---|---|---|---|---|---|
| neutral | +/-441 | 570-612 | 86 | 15 | 44 |
| alpha+ | +/-552 | 689-751 | 99 | 13 | 50 |
| alpha- | +/-552 | 688-754 | 87 | 17 | 42 |
| beta+ | +/-552 | 717-847 | 84 | 13 | 42 |
| beta- | +/-552 | 598-746 | 102 | 17 | 51 |
| combined045 | +/-552 | 705-822 | 85 | 14 | 41 |
| combined135 | +/-552 | 634-731 | 91 | 19 | 45 |
| combined225 | +/-552 | 640-730 | 110 | 15 | 54 |
| combined315 | +/-552 | 705-821 | 86 | 13 | 45 |

### 4.3 Connector envelopes and mount hole shear [SIM]

| case | inner cup max comp. N | inner washer N | outer cup N | outer washer N | max hole shear N (hole, pose) |
|---|---|---|---|---|---|
| GS | 801 | 280 | 799 | 216 | 808 (AF_GM10_2, beta-) |
| LC6 | 137 | 115 | 146 | 94 | 81 (AF_GM09_4, alpha+) |
| LC2F | 438 | 41 | 435 | 135 | 190 (AF_GM09_4, alpha+) |

### 4.4 Hot lower bound (DERIVED; `results/f1_lc3_hot_bound_s3d.json`)

| part | MS_y bound | MS_u bound | state | method |
|---|---|---|---|---|
| GM-01 | -0.219 | -0.327 | B1_1 | LC1 vm + part-max F2 cone-pose (GS + TD + LC6) increment (pose mesh differs: coarser, or refined at the lever roots) |
| GM-02 | -0.259 | -0.362 | B1_1 | LC1 vm + part-max F2 cone-pose (GS + TD + LC6) increment (pose mesh differs: coarser, or refined at the lever roots) |
| GM-03 | +2.035 | +1.449 | B1_2 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-16a | +1.138 | +0.842 | B1_2 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-16b | +1.148 | +0.851 | B1_21.65 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-08a | +15.177 | +12.050 | B1_2 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-08b | +17.186 | +13.671 | B1_21.65 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-09 | +15.273 | +12.129 | B1_21.65 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-10 | +3.599 | +2.710 | B1_21.65 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-13 | +2.887 | +2.136 | B1_2 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| GM-14 | +3.193 | +2.383 | B1_21.65 | F2 cone-pose (GS + TD + LC6) cold vm (9 poses) + LC1-run thermal + manifold vm (node-wise) |
| TC-01 | +1.251 | +0.810 | B1_21.65 | LC1 vm + node-wise F2 cone-pose (GS + TD + LC6) increment (same mesh) |

### 4.5 Comparison with S-3D v1.1 (collar 7075-T6 design-change columns, 1.5 mm exclusion; Mechanical) [SIM, both]

| part, case | v1.1 (CAD v3.4 V5c) MS_y / MS_u (pose, vM outside 1.5 mm) | v3.5.1 this work MS_y / MS_u (pose) |
|---|---|---|
| GM-01 GS | +0.156 / -0.004 (betam7, 271 MPa) | -0.209 / -0.319 (alpha+, 396 MPa) |
| GM-01 SR | +0.048 / -0.097 (betam7, 299 MPa) | L1 +0.206 / +0.039 (stop315); R3 -0.273 / -0.374 |
| GM-01 LC6 | +33.737 / +28.933 (betam7, 9 MPa) | +29.530 / +25.307 (alpha+, 10 MPa) |
| GM-01 LC2F | +49.018 / +37.312 (betam7, 9 MPa) | +8.871 / +6.561 (combined315, 48 MPa) |
| GM-02 GS | +0.166 / +0.005 (betam7, 269 MPa) | -0.223 / -0.330 (alpha-, 403 MPa) |
| GM-02 SR | +0.057 / -0.089 (betam7, 296 MPa) | L1 +0.182 / +0.019 (stop045); R3 -0.280 / -0.379 |
| GM-02 LC6 | +49.585 / +42.589 (betam7, 6 MPa) | +45.191 / +38.803 (beta-, 7 MPa) |
| GM-02 LC2F | +48.442 / +36.871 (centre, 10 MPa) | +7.605 / +5.591 (combined135, 55 MPa) |

Reading: the prescribed rod forces are the same in both (v1.1 441 / 552 / 609 N; here 441 / 552 / 609 N). v1.1 excluded 1.5 mm around edges and connectors, which removes the R1.2 lever-root fillet zone; with the fillet zone resolved (R3) the GS load gives 396-403 MPa there and SR 431-435 MPa (F1 4.6: stable 0.5 mm from the edge line, not a singularity). On the same v3.5.1 model the L1 1 mm exclusion gives SR +0.182 / +0.019 (GM-02) against R3 -0.280 / -0.379, so the stress resolution at the fillet explains most of the difference [DERIVED]; the geometry change CAD v3.4 V5c -> v3.5.1 is not separated here. The v1.1 GS / SR yield margins (+0.16 / +0.05) are therefore not conservative for the lever root. LC2F: v1.1 applied the stuck-pintle thrust alone (rods unloaded); this work adds the flight inertia (rods up to 54 N), hence about 50 MPa against 9-10 MPa (both far positive).

## 5. Stiffness over the cone and stop poses (F3; `results/k_cone_c71.json`, `results/k_range_v351.json`, `tables/k_range_v351.md`)

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
| range cone, rigid airframe | pose_neutral_c71 | +0.00, +0.00 | 7284 | 1129 / 2586 | 5370 | 1070 / 2295 | 32641 / 32641 | 0.78 / 0.84 |
| range cone, rigid airframe | pose_alpha+_c71 | +7.00, +0.00 | 6992 | 1067 / 2452 | 5184 | 1023 / 2200 | 30756 / 31123 | 0.77 / 0.83 |
| range cone, rigid airframe | pose_alpha-_c71 | -7.00, +0.00 | 6985 | 1067 / 2452 | 5453 | 1033 / 2247 | 30756 / 31123 | 0.77 / 0.82 |
| range cone, rigid airframe | pose_beta+_c71 | +0.00, +7.00 | 6430 | 1071 / 2411 | 6380 | 1331 / 2818 | 31407 / 41089 | 0.80 / 0.84 |
| range cone, rigid airframe | pose_beta-_c71 | +0.00, -7.00 | 8364 | 1111 / 2633 | 4082 | 737 / 1624 | 31297 / 21960 | 0.73 / 0.81 |
| range cone, rigid airframe | pose_combined045_c71 | -4.96, +4.94 | 6563 | 1066 / 2413 | 6184 | 1251 / 2672 | 31080 / 38316 | 0.79 / 0.84 |
| range cone, rigid airframe | pose_combined135_c71 | -4.96, -4.94 | 7779 | 1091 / 2557 | 4552 | 818 / 1805 | 31010 / 24350 | 0.75 / 0.81 |
| range cone, rigid airframe | pose_combined225_c71 | +4.96, -4.94 | 7788 | 1092 / 2558 | 4326 | 810 / 1768 | 31010 / 24350 | 0.75 / 0.82 |
| range cone, rigid airframe | pose_combined315_c71 | +4.96, +4.94 | 6564 | 1066 / 2414 | 6034 | 1245 / 2644 | 31080 / 38316 | 0.79 / 0.84 |
| stop045, compliant airframe | pose_stop045_compliant_c71 | -5.68, +5.65 | 5609 | 1024 / 2250 | 5520 | 1237 / 2562 | 30587 / 38935 | 0.82 / 0.86 |

| group | K_alpha FE | K_alpha +servo 58 | K_alpha +servo 174 | K_beta FE | K_beta +servo 58 | K_beta +servo 174 |
|---|---|---|---|---|---|---|
| stop (8 deg), rigid airframe | 6400-8577 | 1050-1102 | 2385-2630 | 3888-6570 | 686-1364 | 1522-2891 |
| range cone, rigid airframe | 6430-8364 | 1066-1129 | 2411-2633 | 4082-6380 | 737-1331 | 1624-2818 |
| stop045, compliant airframe | 5609-5609 | 1024-1024 | 2250-2250 | 5520-5520 | 1237-1237 | 2562-2562 |
| ALL | 5609-8577 | 1024-1129 | 2250-2633 | 3888-6570 | 686-1364 | 1522-2891 |

V5c comparison (Mechanical SIM, hub/04-fea/stiffness/gimbal_k_summary_V5c_v1.json 82a737caa138259a; CAD v3.3, engine case rigid, 9 poses at 7 deg; ENG-11 range 3133-7406 per CHANGELOG 188 (7)):

| V5c variant | K_alpha | K_beta |
|---|---|---|
| mech_T | 5808-7406 | 3239-5167 |
| mech_T_chainlow | 5573-7026 | 3133-5023 |
| mech_C_chainhigh | 6609-8764 | 3585-5630 |
| mech_rigidchain | 7328-10080 | 3880-6015 |
| smin_T | 1110-1299 | 780-1508 |
| smax_T | 2485-2757 | 1579-2857 |

## 6. Not run or not done

1. Hot S-3D on the refined lever-root meshes node by node (only the conservative part-maximum bound of 4.4; the collar thermal stress is small: F1 LC1 collar margins >= +10.672, min of yield and ultimate).
2. Lever-root fatigue (servo dither / vibration) and a local strain criterion at the fillet: not run (no load spectrum; lead 188 (4) asks for it at corner peaks).
3. 7075-T6 temperature table (RM1-06, Mechanical): allowables taken temperature-independent (470 / 540 MPa, LITERATURE, verify mill cert).
4. Needle-cup / thrust-washer / M5 screw capacities against datasheets (HK0808, PTFE washers, A4 screws): TO-VERIFY (Mechanical).
5. Compliant airframe at the cone poses (only stop045 run in F1: rigid bounds the hole loads, gimbal margins change <= 0.001).
6. Moment-closure observation 7.2 of REPORT-FEA3D (97-99.5 %, bounded rod-force impact <= ~6 N) applies here too.

## 7. Files (sha256/16 of every file in MANIFEST.json in this folder)

- `results/`: `s3d_pose_<pose>_c71.json` (9 cone poses: per case GS / TD0 / TDP / TD / LC6 / LC2F margins, rods, connector and mount envelopes, sub-case coefficients), `s3d_summary_v351.json`, the F1 stop-pose LC3 posts and lever-root refinements used for SR, `f1_post_fa1_c71.json` (FA1T), `f1_lc3_hot_bound_s3d.json`, `k_cone_c71.json`, `k_stop_c71.json`, `k_range_v351.json`, `engine_mount_data_v351.json`.
- `tables/`: `s3d_part_margins_v351.md`, `s3d_rods_v351.md`, `s3d_connectors_v351.md`, `k_range_v351.md`, `engine_mount_data_v351.md` (mounting data as engine data, lead 222), `margin_matrix_v351.md` (every part x case, F1 + F2).
- `figs/`: S3D-01 GM-02 lever root at alpha -7 deg (vM, R3), S3D-C1 margins chart.
- `src/`: scripts (post_s3d.py, s3d_summary.py, s3d_report.py, post_k.py, k_range.py, chart_s3d.py, icd_export.py, ...). Solver bulk stays in /home/claude/work/fea3d/runs.
