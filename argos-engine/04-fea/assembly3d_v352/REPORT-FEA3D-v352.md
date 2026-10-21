# REPORT FEA3D v3.5.2 (re-check)

| | |
|---|---|
| Status | **2026-10-21, FINAL handback of the v3.5.2 re-check** (seat FEA3D-2 from 2026-10-21T00:41Z; seat FEA3D-1 before). The assembled-engine model on CAD v3.5.2 (asm v1.3): LC1 and LC2 on the S-AX gap-conductance bounds GVLO / GVHI, FA-1 (FA1Q / D / U / S / T) on the NF2b relight state, TB70 / TBS, the LC6 soak column, LC3 at the 8 stop poses and F2 (GS / TD / LC6 / LC2F) at the 9 range-cone poses with both lever roots at R3, the LC3 / F2 hot bounds, F3 stiffness, the modal corrections (RM2-06 / RM2-07), the mounting data, the F4 joints, the thermal-joint re-posts (RM2-13) and the J-FWD one-sector contact sub-model with its seat patches, envelope and convergence check. Margin matrix of every part x case (3A) re-run on the J-FWD envelope v5 and, the second and last time, on the final envelope v6; neither re-run moved a cell. Supersedes the v3.5.1 REPORT for v3.5.2; the v3.5.1 record stays as published. |
| Author | fea3d (FEA3D-1, then FEA3D-2), lead briefs and rulings as cited per section (CHANGELOG 231-248; lead rulings 2026-10-20 / 21 by UTC time) |
| Configuration | CAD v3.5.2 INTERIM set as relayed (manifests in 2.1; rev 1 `05a48a8efb89ea8f` ... hardware v1.6 `e25b45808a8f9cf6`). The FINAL v3.5.2 set (CHANGELOG 247: `MANIFEST_v3.5.2.sha256` `a94851ae4dc22cc4`, 441 rows; re-issued with the archive inputs as `0658b176e918f91f`, 448 rows, CHANGELOG 248 (6)) differs in ENG-TC-01 only (J-FWD spot-face flats d11.2 instead of d10.5, coplanar): disclosed in 2.1 and 10A.2; the J-FWD convergence check cD is on the final TC-01. |
| Tool | CalculiX 2.21 (SPOOLES direct), C3D10 tets (gmsh 4.15.2), own Python pre / post (`scripts/`), assembly model **fea3d-asm v1.3** ('tiex' tie formulation, 7.1) |
| Units | mm, N, MPa, degC. MS = allowable / (SF x stress) - 1 |
| Tags | SIM (FE output), DERIVED (computed from SIM / data), CALC (Mechanical's hand calculation), ASSUMED, DATASHEET, LITERATURE, TO-VERIFY, AS RECALLED, ESTIMATE |

> **Not physical approval.** A converged solution, a matching number, a hash match or a clean plot does not approve hardware. Negative margins are reported as found; no margin has been forced. Every number carries its tag in the section that states it.

## 0. Checkpoint (SUPERVISION-WORKFLOW template)

- **Delivered by / reviewed by / date:** fea3d (FEA3D-2) / not reviewed: status *Por revisar* until the independent review / 2026-10-21.
- **Area and configuration:** ARGOS H1 engine, assembled-engine 3D FE on CAD v3.5.2 (interim set; final TC-01 disclosure in 2.1), asm v1.3, CalculiX 2.21; S-AX thermal sources: Mechanical's gap-conductance bounds GVLO / GVHI ('r10free' runs; for example `L1_thv352_NF2b_GVLO_r10free_cad352`) and the NF2b relight state A1_22.2 (2.3, 10B.1).
- **Change and claim to check:** section 1 (claims 1-14). The REV-MECH-2 findings are folded as listed in section 14.
- **Sources and exact files:** section 12 and `MANIFEST.json` in this folder (sha256/16 of every published file); the earlier hub publications listed in 12 stay as they were.
- **Criteria, method and checks run:** sections 2-10B. Checks: the 234 (4) all-node rule on every matrix cell (3A); engine free-body and moment closure in the BUMP unit step (residual <= 2.6e-6 at all 8 stops, 6.1; tie patch test, 7.1); lever-root R2 -> R3 5 % rule with the p = 1 bound (5.2, 6.2); hot bounds node-wise with the part-wide and singular-node checks (4.4); the OP-moment residue check and moment-free estimates (4.5, 9B.3); J-FWD patch acceptance against js5, the history (repeat) tests, the s6 / s9 mesh check, the mesh correction C1 and the convergence check cD on the governing seat line (10A.4-10A.6, 5.3); Mechanical's J-FWD hand checks against the FE (10A.9); deck checks against the source streams and lossless frd compression with raw = decompressed sha256 (12).
- **Verdict and permitted use:** none by the author. SIM / DERIVED results; not physical approval. Usable as design input for Mechanical (the IN718 re-map, the select-fit band, the TS / BR / CH closures in 13) and as engine data for the datasheet (8), with the tags and limits stated.
- **Not yet demonstrated:** section 11.
- **Next closure:** section 13 (open items with owners).

## 1. Claims (checkpoint, SUPERVISION-WORKFLOW)

1. **Model asm v1.3: the tie formulation closes v3.5.1 open item 7.2 (7.1).** In asm v1.1 / v1.2 a tie across a CAD gap or overlap d violated a rigid rotation theta by theta x d (TB1 thread tie: rms 0.35-0.51 mm/rad). On CAD v3.5.2 with the legacy ties the BUMP moment closure was 0.82. With 'tiex' (exact for every linear field; patch-test residual <= 6.7e-12 on all 18 ties) the BUMP moment residual is **<= 2.6e-6 at all 8 stop poses** [SIM]. The v3.5.1 cells are not re-solved with tiex (c71x NOT RUN, section 11); they keep their own 97-99.5 % closure bound.
2. **Lever roots, rev 3 (one R1.5 junction loop on r 38.5), R3 mesh (6.2): no lever-root row is negative** (0 of 68 rows, cold and hot, at all 17 poses). LC3 (8 stops): GM-02 **+0.400 / +0.206** (stop045, p = 1 bound; R3 +0.510 / +0.301), GM-01 **+0.534 / +0.322** (stop315). F2 GS (9 cones): GM-01 **+0.648 / +0.420** (alpha+), GM-02 **+0.591 / +0.371** (alpha-, p = 1 bound). Hot lower bounds: LC3 GM-02 +0.202 / +0.036, GM-01 +0.220 / +0.052; F2 GM-02 +0.337 / +0.152, GM-01 +0.289 / +0.111 [SIM / DERIVED]. The v3.5.1 lever-root negatives (LC3 R3 -0.280 / -0.379 and -0.273 / -0.374; F2 GS -0.223 / -0.330 and -0.209 / -0.319) are removed by the rev-3 junction. This is a SIM statement on CAD v3.5.2, not physical approval (lead 20:44:07Z (1)).
3. **Negative cells as found, by class (sections 3, 4; matrix 3A re-run on the final J-FWD envelope):** 33 negative cells (3A; the re-runs on the J-FWD envelope v5 (03:33:37Z) and on the final v6 (05:22Z) moved no cell, 0 of 26 parts x 21 columns) [SIM / DERIVED]: **DC 1** (TC-01 J-FWD seat / ring line P+Q, -0.075 y); **TS-183 9** (TC-01 LC6 soak -0.356 / -0.482; TC-03 LC1 / LC2 / LC3 hb / F2 hb / TB70, -0.088 / -0.170 to -0.121 / -0.201, S-AX governs +2.564 / +2.241; FD-01 LC6 soak / TB70 / TBS, -0.187 / -0.336 / -0.005 y); **TS-212 2** (TC-02 TB70 -0.236 / -0.271, TBS +0.138 / -0.035); **BR 7** (NZ-01, -0.520 to -0.054, yield only); **CH 3** (NZ-03 LC2 / TB70 / TBS, -0.088 / -0.392 / -0.253); **BT 2** (TC-04 LC3 / F2 hot bounds, -0.004 / -0.008 u, a mesh-defect node; the settling route NOT RUN, final, for disk, lead 03:30:46Z (2)); **MF 9** (TC-01 FA1U / FA1S / TB70 at the J-FWD connector, closed by the J-FWD sub-model; PD-01R / PD-01S LC6 soak / TB70 / TBS, the rigid PD-02 artefact). Classes and closures in section 4.
4. **J-FWD sub-model, FA1S (primary, SF 1.0; 10A.3, 10A.8, 10A.9).** The one-sector contact model with a solid screw replaces the full-bore RBE3 for every J-FWD cell (231 (3)). **The FE refutes none of Mechanical's FA1S hand checks**, on the sharp edge (js5) or on the R0.2 break ((b2), (b1)). Governing FA1S cells: TC-01 hole bearing **+0.005 / +0.239** (CALC, V 3888.1 N at the drawing-limit wall; FE (b2) +0.048 / +0.291, (b1) mu 0.2 BEAR 3435.0 N +0.149 / +0.416 at t_eff 2.388); screw **+0.301** (IN718, NASA-STD-5020A Eq. 22, preload omitted, CALC arm 1.120 mm RETAINED; FE arm (b2) 0.724 mm, (b1) 1.047 mm). For Mechanical's re-map the Eq. 22 inputs are V **4079.2 N** (FE, (b1) shear plane at mu 0.2, above the CALC 3888.1 N) and M **4354.7 N mm** (CALC) (lead 01:30:18Z (6)).
5. **J-FWD soak seat-line P+Q is a found negative (DC, secondary; 10A.4-10A.6, 10A.12).** On the final envelope v6 `43a5d78b67c615fc` (lead 2026-10-21T05:17:36Z (3): v5 `ef22b59cf2413b46` + cD's resultants) (the worst computed instance over js5, (a), (a'), (a''), (b2) with its repeats, (b1) with its repeats under the mesh correction C1, (b2') and cD's resultants; not a proven bound): SOAK **-0.071** ((b2) rep), SOAK70 **-0.055** ((b2)), SOAK52 **-0.030** ((b1) at C1), FA1S +0.053 ((b2), information), PRELOAD +1.038 ((b2), information) [SIM / DERIVED, A4-80 FE]. The soak states depend on the predecessor state: the repeat tests fail by up to +24.7 % on the screw N and +175 % on the seat window at mu 0, and SOAK52 by +16.6 % on N at mu 0.2. The seat-line P+Q is not shown converged with the mesh (MF note). The convergence check cD (s6 + Ball h 0.04 mm at both ends of the governing line, on the FINAL TC-01) gives 0.927 / 0.947 / 0.966 / 0.959 / 0.985 x s6 on that line (PRELOAD / SOAK52 / SOAK / SOAK70 / FA1S) and no line above 1.05 x s6, so s6 + C1 stand in every state (lead 02:01:34Z (C), 05:17:36Z (1)). s9 -> s6 is +12 to +18 % and s6 -> cD -1.5 to -7.3 %: not monotonic, with the mesh and the geometry change not split. cD's resultants move three envelope values (SOAK70 window maximum 3151.1 N, FA1S N minimum 2728.5 N, FA1S window minimum 455.0 N) and no seat-line value. The IN718 TC-01 cell is **-0.075** / +0.239 (Mechanical's v7 rows, mapped on the superseded envelope v3; Mechanical re-maps once on v6 with `jfwd_v7inputs_cD_v352.json`, lead 05:27Z (3)).
6. **Slip at mu 0.2 ((b1), 10A.7 (c), 10A.12).** The head is at the friction limit at every step (T/N 0.195-0.202). At FA1S the head friction carries 600 N against V 4079 N at the shear plane: **the joint is bearing-type at FA1S at mu 0.2**, so the screws act as shear pins (RM2-01 (c) holds) [SIM].
7. **js5b (s5, mu 0, IN718 screw, 3750 N; FA1U / FA1D / LC2U / LC2Y / LC2N / LC2M; 10A.13):** FA1U / FA1D: TC-01 +0.222 / +0.318 and +0.257 / +0.355 (ligament Pm+Pb), TC-02 +1.449 / +1.641 and +1.597 / +1.853, bounded by FA1S. LC2 on the adopted rule (A) (lead 2026-10-21T03:30:46Z (1): the external load is factored, the preload is not): TC-01 **+0.421 / +0.424** (FE-factored LC2Y yield / LC2U ultimate), TC-02 +1.330 / +1.633, screw +1.894 / +2.110 (LC2N) and +2.218 / +2.394 (LC2M) in the 234 (1)(b) form. The hand form (SF 1.5 / 2.0 on the total stress, preload included; linear superposition ASSUMED) is information: TC-01 LC2N +0.016 / **-0.183**. js5b raises no envelope quantity and moves no J-FWD cell [SIM / DERIVED].
8. **F3 stiffness (9).** With the effective lever radius per servo and pose (RM2-05; r_eff 7.88-11.14 mm) the v3.5.1-model table over 17 poses is K_alpha FE 6400-8577 and K_beta 3888-6570 N m/rad; with the servo in series 1129-1388 / 787-1759 (k_s 58) and 2586-2949 / 1681-3436 (k_s 174, coupled) [SIM / DERIVED; k_s ASSUMED]. **The v3.5.2 R3 table** (`k_table_r3_v352.json` `f3c7cfbcfb98bcd7`, ACCEPTED 18:40:44Z) is stiffer: K_alpha FE 7,294-9,337, K_beta 3,972-7,172; with k_s 58 1,150-1,426 / 791-1,799; with k_s 174 2,697-3,076 / 1,697-3,594 N m/rad (neutral +13.2 % / +7.3 % FE against v3.5.1).
9. **Modal (9A).** RM2-07: the loop-relevant rocking pair includes the servo inertia: **16.72 / 17.15 Hz at k_s 58 and 24.49 / 25.95 Hz at k_s 174** (J nominal), 14.9-29.0 Hz at neutral over the k_s and J ranges [DERIVED]; the v3.5.1 '21-33 Hz with the servo in series' omits J and is withdrawn. RM2-06: the modal re-solve with the L1 TC-01 loads (`modal_v351ca2c_c71`) changes the frequencies by at most 0.102 % (MAC >= 0.9944); the mode list stands.
10. **Mounting data for the datasheet (8).** Governing maximum M5 screw shear, rigid airframe (the larger of the as-found value and the moment-free estimate) [DERIVED]: LC1 76 N, LC2 150 N, FA1Q 348 N, FA1D 448 N, FA1U 544 N, FA1S 559 N, FA1T 657 N, LC3 890 N (AF_GM10_2, stop180), F2 GS 808 N, TD 306 N (at Pc max), LC6 80 N, LC2F 288 N. The per-hole rows are the envelope of the rigid airframe and the carried v3.5.1 compliant rows (c351).
11. **OP-moment residue (MF observation; 4.5, 9B.3).** The OP unit step of the v3.5.2 models carries a moment about the pivot that the physical load does not have (L1 0.72 N m/MPa against 0.27 on v3.5.1; the cause found is a couple of about 1.56 N m/MPa at elements 24664 / 23610). The F2 and LC3 cells stand as found with the moment-free statics estimate beside each affected row (not proven conservative for every part); the datasheet hole loads take the larger value (claim 10).
12. **F4 joints on the v3.5.2 hardware (10)** [DERIVED; preload model ASSUMED]: J-FD01 (3 x M4 A4-80, 1.8 N m) **+0.121 / +0.403** (bounding / Phi 0.2), against -0.41 / -0.20 in v3.5.1; J-FD09 (2 x M4 A4-80) **+0.476 / +0.660**, +0.221 / +0.586 at hose EI 0.5. Both v3.5.1 design actions (CHANGELOG 223 (5)) are closed on the F4 formulas.
13. **Thermal joints on the gap-conductance bounds (10B, RM2-13).** The TC-03 flange corner is -0.088 / -0.170 (LC1) and -0.092 / -0.175 (LC2) on GVHI, the conservative bound (GVLO -0.076 / -0.159); the v3.5.1 merged-field value (-0.312 / -0.375) rested mostly on the inherited thermal closure and is superseded for v3.5.2; S-AX v352r4 governs the corner (+2.564 / +2.241, TS-183). The TC-02 seat regular cell is +0.469 / +0.202 (LC2, the lower bound per component over GVLO / GVHI); TC-02 runs at 187.7 C (GVLO) against the 150 C limit, a DESIGN ITEM (236 (4)). The fit closure is CLOSED on the Lame bound (240 (7)).
14. **CAD v3.5.2 FINAL TC-01 (disclosure; 2.1, 10A.2).** The final set differs from the interim set in ENG-TC-01 only: d11.2 spot-face flats instead of d10.5, coplanar (wall 2.688 mm at the hole), 104.037 mm3 less material over the 10 flats; the head footprint lies inside both. All J-FWD FE is on the interim TC-01 except cD, which is on the final TC-01: cD / s6 on the governing line is 0.927-0.985, and its resultants move v6 by -1.6 to +0.9 % (seat window, screw N); the difference to s6 is mesh + geometry, not split (lead 02:01:34Z (C), (D)). The 9 sDL12 boundary nodes extrapolated by more than 0.01 mm (largest 0.0431 mm; s6L12 0.0188 mm) lie on the curved FIT and OD surfaces, none on the flats, so the d11.2 flats do not cause them (s5 facets ASSUMED; 5.3).

## 2. Configuration

### 2.1 Model (fea3d-asm v1.3 on CAD v3.5.2 INTERIM)

- **CAD.** Hub `03-cad/v3.5.2/`, Mechanical INTERIM (not a frozen baseline). I verified every manifest with `sha256sum -c` when it was relayed: rev 1 `05a48a8efb89ea8f` (80 rows, 02:02Z), rev 2 `f524c0ec9add81c1` (122), rev 3 `e53e4a59eed9db90` (151), spot-face TC-01 `39e52d6330319dee` (196), rev 4 / hardware v1.5 `5b2bd906c999d62d` (202), hardware v1.6 `e25b45808a8f9cf6` (212). The check at publish time is in section 12.
- **FINAL CAD set (disclosure, lead 2026-10-21T02:01:34Z (D)).** The FINAL v3.5.2 set (release 2026-10-20T19:09:50Z; CHANGELOG 247: `03-cad/v3.5.2/MANIFEST_v3.5.2.sha256` `a94851ae4dc22cc4`, 441 rows, ACCEPTED 19:53:27Z; re-issued with the archive inputs as `0658b176e918f91f`, 448 rows, published 20:46:49Z, recorded in CHANGELOG 248 (6) with no line of its own; the hub copy is the re-issue) differs from the interim set in one part only, ENG-TC-01 (Mechanical's check `03-cad/v3.5.2/checks/test_final352_v1.json` `aa064886ee64ac94`). Its J-FWD spot-face flats are d11.2 (final `parts/ENG-TC-01.step` `fcb3b5b93bebdb01`) instead of d10.5 (interim `history/ENG-TC-01.step.1ad07e472709b1b2`). The flats are coplanar (x' 31.313, wall 2.688 mm at the hole); the interim-minus-final volume is 104.037 mm3 over the 10 flats (net volume change -103.54 mm3; mass -0.280 g at 2.70 g/cm3) [volumes from Mechanical's CAD check; mass DERIVED]. **All J-FWD FE in this report is on the interim TC-01, except the J-FWD convergence check cD**, which is built on the final TC-01 (5.3, 10A.6). The head bearing footprint (r' <= 4.75 mm from the hole axis, head D 9.5) lies inside both flats (r' 5.25 / 5.6). The effect on the other J-FWD rows is ASSUMED small. cD gives 0.927-0.985 x s6 on the governing seat line, with the mesh and the geometry not split (10A.6). In the global model the J-FWD holes are RBE3 connector regions and the spot face lies inside that exclusion (row below).
- **Which geometry each analysis uses.**

  | Analysis | Part geometry | Note |
  |---|---|---|
  | Global model: LC1, LC2, LC2F, TB70 / TBS, soak, FA-1 | ENGINE STEP rev 1 (149 instances). Exactly the 11 changed parts differ from v3.5.1 and NZ-06 is new. Re-meshed: TC-01, TC-02, TC-09, FD-01 (rev 1). The other 17 meshed bodies are byte-identical to v3.5.1 and reuse its meshes. | GM-01 / GM-02 are rev 1 in the L1 LC1 / LC2 / TB runs. The lever-root junction is not in their load path. |
  | Lever-root runs (LC3 stop poses, GS / TD / LC6 cone poses, hot-bound bases) | GM-01 / GM-02 rev 3 (`6f632a77af8bb312` / `71c3516a3b35a073`): one R1.5 junction loop (6 faces) on r 38.5, min concave radius 1.466 mm. The rest as the global model. | Rev 1 lever results are kept only as the record of the zero-radius finding (section 6). |
  | J-FWD one-sector sub-model | TC-01 with the d10.5 spot face (interim `ENG-TC-01.step` `1ad07e472709b1b2`, flat at x' 31.313, wall 2.688 mm at the hole; the FINAL TC-01 `fcb3b5b93bebdb01` has coplanar d11.2 flats and is used by the convergence check cD only, see the disclosure above), TC-02 rev 1 tap pattern (10 x M5 at 18 + 36k deg, tap wall 1.906 mm at az 18 / 342), solid M5 screw. | In the global model the J-FWD holes are RBE3 connector regions; the spot face lies inside that connector exclusion. |
  | TC-02 / TC-03 seat region | Rev 3 for TC-02 / TC-03 (lead 05:42Z). Rev 4 adds an R0.5 seat-bore entry radius and a TC-03 shank-to-flange undercut. I did not re-mesh them. | Mechanical's rev-4 S-AX contact sub-model is the named sub-model for the seat region (MF disclosure on the seat cells, section 3). |
  | Nozzle | v3.5.1 NZ-01 / NZ-02 meshes. NZ-02 v3.5.1 is identical to N-F2b. NZ-01 differs from N-F2b by a 0.25 mm aft-face step and an R1 corner (V -0.87 %). NZ-06 (N-F2b foil) is a 0.195 g mass item on NZ-03 [DERIVED]. | The interim N-F2 NZ parts are used for nothing: their unmeshed foil gap gave OP net 189.8 N/MPa (a spurious -13 N/MPa in the nozzle stack) against 202.50 N/MPa with the v3.5.1 NZ geometry. The NZ-01 / NZ-03 cells cite Mechanical's S-AX v352_NF2b as the named sub-model at the shoulder / foil interface (MF). |

- **Placements.** `asm_build` places every instance from the ENGINE STEP transforms and takes masses from massprops. It does not read `placements_v3.5.1.json` or `placements_v3.5.2.json`. The identity transforms of the 20 pushrod-item instances in the frozen `placements_v3.5.1.json` (CHANGELOG 233 (7)) therefore affect neither the v3.5.1 nor the v3.5.2 results.
- **Mesh.**
  - Global L1 model: 176,707 nodes, 86,786 C3D10 (v3.5.1 171,123). TC-09 level 2 fails in gmsh on the v3.5.2 part, so the L2 / pose runs mesh it at level 1.8.
  - Pose runs: engine pressure parts at level 2, the rest at L1.
  - Lever-root levels on rev 3: R2 (h 0.5 / 0.4 mm on the 6 junction faces, two balls h 0.5) gives 177,213 nodes. R3 (h 0.25 / 0.2 mm, two balls h 0.25) gives 259,019 nodes.
- **Masses** (`runs/<run>/mass.json`: FE volume x density + point masses) [DERIVED]:

  | Model | Total kg | Engine | Ring | Fixed | Horns |
  |---|---|---|---|---|---|
  | v3.5.1 c71 (lc1v351_c71, fa1_c71) | 4.10307 | 2.88625 | 0.21701 | 0.97058 | 0.02923 |
  | v3.5.2 L1 (lc1v352g, tb352g) | 4.03255 | 2.82932 | 0.21701 | 0.95698 | 0.02923 |
  | v3.5.2 rev-3 R3 pose (pose_stop045_v352r3R3) | 4.02989 | 2.82667 | 0.21701 | 0.95698 | 0.02923 |

  Airframe-wall equipment outside the FE: massprops wet fixed 2.26691 kg minus the model's fixed group 0.95698 kg = **1.30993 kg** (v3.5.1: 2.2805 - 0.97058 = 1.30992 kg).
- **Finding on the v3.5.1 model (minor, fixed in v1.3).**
  - What was wrong: `samples.instance_surface` read `geom/v35_neutral` for every CAD, because its cache was not keyed by CAD. The v3.5.1 BLEED item (33.2 g, on FD-01) and TC10 item (4.7 g, on TC-02) were therefore attached through the v3.5 BL-02 / TC-10 surfaces. Both surfaces changed in v3.5.1. The other 19 sampled instances are identical.
  - Fix: a per-CAD BREP and cache (`geom/samples/<CAD>/`).
  - Bound on the v3.5.1 results [DERIVED]: the item masses and centres were right; only the attachment patch differed (FD-01 22 faces v3.5.1 vs 34 v3.5.2; TC-02 214 vs 215). The largest inertia load on the two items in any case is <= 2.7 N on FD-01 and <= 0.4 N on TC-02 (LC3: 6.29 g lateral + 5.43 g axial). The local stress change is therefore below about 0.1 MPa, and no v3.5.1 cell moves at the published decimals.

### 2.2 Interfaces (asm v1.3)

| Interface | Model | Stiffness / tag |
|---|---|---|
| All ties | **v1.3 tie formulation ('tiex', section 7.1).** The dependent node follows the independent face's tri6 interpolation plus a gradient correction over the parent tet. This is exact for every linear field. In v1.2 a tie across a CAD gap or overlap d violated rigid rotation by theta x d. | patch test residual <= 7e-12 for rigid rotation and affine strain on all 18 ties [SIM model data] |
| TB1 (TC-03 GlidCop insert in TC-02), production variant in v3.5.2 | **'thread'** (CHANGELOG 234 (7)): TC03_TC02_shoulder ('zt', axial + tangential, radial free; 212 dependent nodes, all on the shoulder plane z 107.513, r 6.93-10.00) + TC03_TC02_thread ('zt' along the M14 engagement, R7 major on the R6.5 minor bore, CAD overlap 0.5 mm; 547 nodes at r 6.90-7.00, z 107.51-117.51). The flange OD (r 10.0, across the 0.10 mm design gap to the r 10.1 counterbore) and the end face (z 117.51, r < 6.9) are **not** tied: 0 dependent nodes off the shoulder plane at r > 9.9 mm; the 44 nodes at z 117.51 are the end circle of the thread cylinder (r 7.0). Census: `results/v352/tb1_tie_census_v352.json` (`scripts/tb1_tie_census_v352.py`). | bonded in z and theta on the shoulder and the thread, ASSUMED |
| TB1 in v3.5.1 (record) | Production 'faces' (TC03_TC02_seat, 'zt', tol 0.12 mm): 183 shoulder + 46 flange-OD + 71 end-face dependent nodes (RM2-13 (c)). The 46 OD nodes are tied across the 0.10 mm design gap. The pressure model treated the same gap as open and wetted. **Correction to the v3.5.1 2.2 row "TB1 variant: 'thread' only (shoulder + end face free)":** the v3.5.1 'thread' variant kept the shoulder tie and the thread tie and freed the flange OD and the end face. | RM2-13, CHANGELOG 234 (7) |
| TC-01 / TC-02 f7/H8 fit (TC-02 plug 57.20 f7 in the TC-01 bore 57.25 H8; radial gap 0.025 CAD basic, 0.040-0.078 drawing) | Global model: **no tie and no contact**. The head is held by the 10 J-FWD connectors only. J-FWD sub-model: FIT penalty contact with `*CLEARANCE` 0.078 mm (drawing maximum, the bound for the shell pull and for screw shear before fit closure; lead 09:15Z). | section 10A |
| J-FWD, global model | 10 RBE3 bushings (JF0-JF9) at 18 + 36k deg: radial 1.0e5, tangential and axial 4.27e4 N/mm. Superseded for every J-FWD cell by the one-sector contact sub-model (section 10A; CHANGELOG 231 (3)). | ASSUMED stiffness; cells from 10A |
| J-FD01 (FD-01 on the TC-02 x -29.5 flat) | FD01_TC02_screws bond patches at the 3 x M4 tap axes (y +/-8.5 z 146.51; y 0 z 165.51) | bonded, ASSUMED; joint rows in section 10 |
| Other contacts (GM-01 / GM-02 to the TC-01 bore, bolted flanges, nozzle stack) | bonded ties | ASSUMED (stiff bound) |
| Gimbal pins / seats, HK0808 needle cups, PTFE washers, push rods, PD feet, PD-02, airframe holes | as v3.5.1 (asm v1.2 rows of the v3.5.1 REPORT 2.2): rigid pin / seat bores; needle bushings 128,258 / 149,912 N/mm; SPRINGA 1e6 mm; rods k_chain 11,418.2 N/mm with rigid servo output; rigid airframe and the compliant variant (k_af 2e3 / 2e4 / 2e4 N/mm, ASSUMED) | as v3.5.1 |

**Inherited closure: disclosure (RM2-13, CHANGELOG 234 (7)).**
- *Thermal map.* Every 3-D thermal state is interpolated from S-AX per-part fields. The thermal mesh's TOL_MM 0.10 closure rule (`ax_thermal.py` line 66) merges designed clearances. Two of them carry non-physical heat into results I publish: the TC-03 flange OD gap (r 10.0-10.1) and the TC-01 / TC-02 f7/H8 fit. Every v3.5.1 thermal state and the merged v3.5.2 NF2b state inherit this closure.
- *v3.5.2.* The TC-03, TC-02 seat, TC-02 maximum and NZ-01 cells are re-posted on Mechanical's gap-conductance variant: GVLO and GVHI, both bounds, with the merged field as the perfect-contact bound (section 10B). The structural tie no longer bridges the OD gap ('thread' variant above).
- *v3.5.1 values.* The TC-03 corner (-0.312 / -0.375) and TC-02 seat (+0.096 / -0.119) values of the v3.5.1 report rest on the merged field. They are superseded for v3.5.2 by 10B and stay in the v3.5.1 record with this dependence.

### 2.3 Loads

| Case | Definition (v3.5.2 changes in bold) | SF | Tags |
|---|---|---|---|
| LC1 | as v3.5.1: Pc 25.01 bar, operating distribution + manifold 70 bar + 4.04 g axial + 0.61 g lateral (4 directions); S-AX thermal states. **v3.5.2 thermal source: S-AX v352 gap-conductance GVLO (lc1v352g) and GVHI (lc1v352h) r10free runs.** Their 2-D geometry (`geom_v352/geometry.json`) cuts TC-02 and TC-04 at 78 deg (`angle_part_deg`), as the brief asks. I verified it. The merged-node map enters only as perfect-contact information: interim run lc1v352 maps the v3.5.1 S-AX field `L1_thv351_TB1GC_cad351` on the v3.5.2 geometry. The v3.5.2 merged NF2b field is used only for the FA-1 relight state A1_22.2 (fa1v352n). | 1.5 / 2.0 at node T | SIM (Mechanical S-AX) |
| **LC2** | **loadcases_v1 LC2 (CHANGELOG 234 (2), correcting 231 (4)): chamber 4.5 MPa on the operating distribution, manifold 7.0 MPa, hottest thermal state; every pressure part and the J-FWD screws** | 1.5 / 2.0 at part T | DATASHEET loadcases_v1 |
| LC2F | 907.7 N failure thrust as published for v3.5.1 (carried) | 1.0 / 1.5 | |
| **FA1Q / FA1D / FA1U** | **band values of CHANGELOG 230 (2): 94 / 121 / 147 bar abs** (fa1v352n, NF2b A1_22.2 relight state) | 1.0 | lead 230 |
| FA1S | 151.04 bar abs (DLF 2.0 bound), 45.6 C at J-FWD | 1.0 | 194 |
| FA1T | as v3.5.1 | 1.0 | |
| LC3 cold / hot bound | as v3.5.1 (8 stop poses, 64 sub-cases, fb_run; hot bound = node-wise sub-additive bound on the LC1 thermo-pressure base) **on the rev-3 R3 lever mesh; hot-bound bases lc1v352hbg3 / hbh3 (GVLO / GVHI) on the same mesh.** The cold pose runs take node temperatures for the allowables only, from B1_21.65 of the v3.5.1 map (interim; LC3 cold carries no thermal stress). GM-01 / GM-02 are non-S-AX parts at the 60 C bay [ASSUMED], so the lever-root cells do not depend on that map. | 1.5 / 2.0 | |
| GS / TD / LC6 (F2) | as v3.5.1 S-3D, 9 range-cone poses, **rev-3 R3 lever mesh** | 1.5 / 2.0 | |
| **TB70 / TBS** | **blocked-distribution state of the TB rows (step BL: PC 1.0 + GAS 1.0 for z >= throat + plug P pi r_t^2), GVLO and GVHI; TB70 nominal at SF 1.5 / 2.0, TBS abnormal at SF 1.0 / 1.5 (188 (9), lead 08:58Z)** | as stated | SIM |
| **J-FWD steps** | **PRELOAD (pretension 3750 N = +25 % on HW-101 3.0 N m), SOAK70 / SOAK52 (GVLO B1_70.7 / B1_51.7 mapped), SOAK (64.7 s row means TC-01 158.0 C, TC-02 96.0 C, screw 127 C), FA1S, FA1U / FA1D, LC2U / Y / N / M** | per 234 (1)(b) and 10A | SIM / DERIVED |

### 2.4 Criteria and node sets (CHANGELOG 234 (4) all-node rule)

- Metals: MS_y = Fty(T) / (SF_y vM) - 1 and MS_u = Ftu(T) / (SF_u vM) - 1, at node temperature (materials v1; bay 60 C ASSUMED). Brittle parts as v3.5.1 (s1 / St, s3 / Sc, SF 2.0; NZ-03 char 20 MPa ASSUMED).
- **Every matrix cell carries the all-node minimum** with its node, class and distance beside the regular-set value.
- A regular value stands only in two cases:
  - the all-node minimum sits at an idealisation that a named sub-model or contact FE replaces (owner and CHANGELOG line given in the cell); or
  - refinement converges, and then the refined value is used.
- Classes of the all-node location:
  - RE: re-entrant. Only BREP zero-radius concave edges or facet turns above about 60 deg (brep60). Smaller fillets are refined, not excluded.
  - TE: tie edge.
  - CE: connector / RBE3 edge.
  - ID: interface of a contact or tie.
  - BT: bad tet.
  - regular.
- Negatives are classified with REV-MECH-2's classes: DC, TS-183, TS-212, BR, CH, MF.
- Supplementary checks as v3.5.1: primary-only, P+Q <= 2 Fty(T) (nodal and SCL), and Neuber at contact edges where a ruling asks for it.

## 3. Per-part margins (minimum over every case; the governing column)

From the matrix (3A) [SIM; DERIVED where the cell is a bound]. The flags and classes are those of the matrix.

| part | minimum (column) | class where negative (section 4) |
|---|---|---|
| TC-01 | -0.482 (LC6 soak u) | DC, MF, TS-183 |
| TC-02 | -0.271 (TB70 u) | TS-212 |
| TC-03 | -0.201 (TB70 u) | TS-183 |
| TC-04 | -0.008 (F2 hot bound u) | BT |
| TC-09 | +0.604 (TB70 u) | - |
| NZ-01 | -0.520 (LC1 y) | BR |
| NZ-02 | +0.356 (TB70 y) | - |
| NZ-03 | -0.392 (TB70 y) | CH |
| NZ-04 | +2.265 (TB70 y) | - |
| FD-01 | -0.336 (TB70 y) | TS-183 |
| GM-01 | +0.005 (LC6 soak u) | - |
| GM-02 | +0.034 (LC6 soak u) | - |
| GM-03 | +0.795 (LC3 hot bound u) | - |
| GM-08a | +4.262 (LC3 hot bound u) | - |
| GM-08b | +8.277 (F2 hot bound u) | - |
| GM-09 | +0.626 (J-FD09 y) | - |
| GM-10 | +2.708 (F2 hot bound u) | - |
| GM-13 | +1.723 (LC3 hot bound u) | - |
| GM-14 | +1.758 (LC3 hot bound u) | - |
| GM-16a | +0.179 (LC3 hot bound u) | - |
| GM-16b | +0.248 (LC3 hot bound u) | - |
| PD-01R | -0.509 (TB70 u) | MF |
| PD-01S | -0.555 (TB70 u) | MF |
| HW-101 (J-FWD) | +0.301 (J-FWD u) | - |
| HW-103 (J-FD01) | +0.121 (J-FD01 y) | - |
| HW-127 (J-FD09) | +0.221 (J-FD09 y) | - |

## 3A. Margin matrix v3.5.2 (every part x every case)

Table files: `results/v352/tables/margin_matrix_v352.md` 3d274f66c31a18e4, `margin_matrix_v352.json` e59e35df6759afbb, script `scripts/margin_matrix_v352.py` 0b7c0b20648f27ce. The table file also carries the all-node minima beside every regular value, the negative cells with their governing records and classes (section 4), the J-FWD column rows (section 10A), the columns and the sources.

Cell = MS_y / MS_u after the 234 (4) all-node rule. Flags: r = regular value stands (the all-node minimum sits at an idealisation a named sub-model / contact FE replaces), a = all-node value is the cell, c = includes v3.5.1 carried values (unchanged part), p = some sources pending, s = hot-bound all-node value lowered to the node-wise bound at its node (hb_singular_check_v352), w = hot-bound all-node value replaced by the rigorous part-wide bound over every node of the part, stored value beside it (hb_partwide_v352; lead 21:47:29Z: lc3_bound does not sum the increments of parts outside SAME_MESH_ENGINE node by node). MF (gov. ...) = model-fidelity class with the governing sub-model value (lead 21:15:29Z (3)); BT = bad-tet class (lead 21:15:29Z (4)). '-' = case not evaluated for the part; n/a = no allowable in that slot (brittle parts: one value).

- The TB70 / TBS columns are the TB state of tb352g / tb352h at **A 175 C, hotter than the adopted 150 C** (the T-F1 exposure basis, lead 21:51:30Z).
- The seat at TB is not closed by the global TB pass (section 4.3, Mechanical's S-AX v352r4 at line 106).
- Nothing in the matrix is a physical approval. Negative cells are quoted as found, with their class (section 4).

| part | LC1 | LC2 | LC2F | FA1Q | FA1D | FA1U | FA1S | FA1T | LC3 cold | LC3 hot bound | GS | TD | LC6 F2 | F2 hot bound | LC6 soak | TB70 | TBS | J-FWD | J-FD01 | J-FD09 | min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-01 | +0.955 / +0.580 r | +0.440 / +0.164 r | - | +0.412 / +0.522 r | +0.107 / +0.194 r | -0.083 / -0.012 r MF (gov. sub-model +0.005 / +0.239) | -0.107 / -0.037 r MF (gov. sub-model +0.005 / +0.239) | - | +1.044 / +0.657 a | +0.890 / +0.528 r | +1.080 / +0.686 a | +1.118 / +0.717 a | +30.584 / +24.649 a | +0.877 / +0.518 r | -0.356 / -0.482 r | +0.120 / -0.110 r | +0.570 / +0.109 r | -0.075 / +0.239 p | - | - | -0.482 (LC6 soak u) |
| TC-02 | +0.496 / +0.223 r | +0.469 / +0.202 r | - | +1.705 / +1.918 r | +1.098 / +1.263 r | +0.725 / +0.861 r | +0.679 / +0.811 r | - | +7.561 / +5.883 r | +0.504 / +0.190 r | +7.254 / +5.637 r | +7.689 / +5.986 r | >+99 / >+99 r | +0.493 / +0.181 r | +1.068 / +0.656 a | -0.236 / -0.271 r | +0.138 / -0.035 r | +0.045 / +0.162 p | +0.404 / n/a | - | -0.271 (TB70 u) |
| TC-03 | -0.088 / -0.170 | -0.092 / -0.175 | - | +9.382 / +11.587 | +8.834 / +10.922 | +8.247 / +10.211 | +8.153 / +10.097 | - | +25.346 / +22.957 a | -0.107 / -0.188 r | +25.274 / +22.892 a | +25.529 / +23.124 a | >+99 / >+99 a | -0.107 / -0.188 r | +0.992 / +0.811 r | -0.121 / -0.201 r | +0.325 / +0.071 r | - | - | - | -0.201 (TB70 u) |
| TC-04 | +0.459 / +0.184 a | +0.459 / +0.183 a | - | +1.803 / +2.030 a | +1.802 / +2.029 a | +1.800 / +2.027 a | +1.800 / +2.027 a | - | >+99 / >+99 a | +0.228 / -0.004 as BT | >+99 / +92.532 a | >+99 / >+99 a | >+99 / >+99 a | +0.223 / -0.008 as BT | +6.477 / +5.017 a | +0.401 / +0.122 a | +1.102 / +0.496 a | - | - | - | -0.008 (F2 hot bound u) |
| TC-09 | +1.062 / +0.796 a | +1.003 / +0.744 a | - | +2.053 / +2.636 | +1.548 / +2.034 | +1.197 / +1.617 | +1.151 / +1.563 | - | +10.348 / +9.106 a | +1.031 / +0.774 a | +10.456 / +9.202 a | +10.545 / +9.281 a | >+99 / >+99 a | +1.091 / +0.826 aw (part-wide; stored +1.092 / +0.827) | +1.075 / +0.705 | +0.861 / +0.604 a | +1.763 / +1.117 a | - | - | - | +0.604 (TB70 u) |
| NZ-01 | -0.520 / n/a a | -0.489 / n/a a | - | +3.234 / n/a | +2.134 / n/a a | +1.504 / n/a a | +1.476 / n/a r | - | +4.804 / n/a r | -0.403 / n/a aw (part-wide; stored -0.402 / n/a) | +4.860 / n/a r | +4.866 / n/a r | >+99 / n/a r | -0.401 / n/a | -0.426 / n/a r | -0.315 / n/a a | -0.054 / n/a a | - | - | - | -0.520 (LC1 y) |
| NZ-02 | +0.595 / n/a a | +0.596 / n/a a | - | +4.107 / n/a a | +2.967 / n/a a | +2.265 / n/a a | +2.178 / n/a a | - | +1.559 / n/a a | +0.781 / n/a a | +1.581 / n/a a | +1.581 / n/a a | >+99 / n/a a | +0.784 / n/a as | >+99 / n/a a | +0.356 / n/a a | +0.665 / n/a a | - | - | - | +0.356 (TB70 y) |
| NZ-03 | +0.445 / n/a r | -0.088 / n/a r | - | +1.615 / n/a r | +1.032 / n/a r | +0.672 / n/a r | +0.628 / n/a r | - | +0.179 / n/a r | +0.243 / n/a r | +0.187 / n/a r | +0.190 / n/a r | >+99 / n/a | +0.252 / n/a r | >+99 / n/a r | -0.392 / n/a r | -0.253 / n/a r | - | - | - | -0.392 (TB70 y) |
| NZ-04 | +3.584 / n/a a | +2.897 / n/a a | - | +6.534 / n/a a | +5.282 / n/a a | +4.415 / n/a a | +4.301 / n/a a | - | +13.606 / n/a a | +3.004 / n/a a | +13.685 / n/a a | +13.702 / n/a a | >+99 / n/a | +3.007 / n/a as | +6.093 / n/a a | +2.265 / n/a a | +3.195 / n/a a | - | - | - | +2.265 (TB70 y) |
| FD-01 | +1.227 / +3.422 a | +1.197 / +3.362 a | - | +3.170 / +9.743 a | +3.088 / +9.531 a | +3.011 / +9.334 a | +3.000 / +9.304 a | - | +33.700 / +66.045 a | +0.837 / +2.620 aw (part-wide; stored +0.848 / +2.640) | +35.220 / +68.982 a | +32.090 / +62.934 a | +85.170 / >+99 a | +0.830 / +2.606 aw (part-wide; stored +0.840 / +2.625) | -0.187 / +0.780 a | -0.336 / +0.484 a | -0.005 / +0.976 a | - | - | - | -0.336 (TB70 y) |
| GM-01 | +3.352 / +2.750 a | +1.439 / +1.102 a | +2.551 / +1.720 a | +0.767 / +1.030 a | +0.373 / +0.578 a | +0.130 / +0.299 a | +0.100 / +0.264 a | +0.777 / +1.042 a | +0.534 / +0.322 | +0.220 / +0.052 | +0.648 / +0.420 | +2.660 / +2.154 a | +42.346 / +36.351 | +0.289 / +0.111 | +0.166 / +0.005 a | +0.291 / +0.113 a | +0.936 / +0.483 a | - | - | - | +0.005 (LC6 soak u) |
| GM-02 | +6.556 / +5.511 a | +3.255 / +2.667 a | +3.585 / +2.512 a | +2.091 / +2.551 a | +1.404 / +1.762 a | +0.980 / +1.275 a | +0.927 / +1.215 a | +2.105 / +2.568 a | +0.400 / +0.206 | +0.202 / +0.036 | +0.591 / +0.371 | +3.643 / +3.001 a | +57.337 / +49.269 | +0.337 / +0.152 | +0.200 / +0.034 a | +0.241 / +0.069 a | +0.861 / +0.425 a | - | - | - | +0.034 (LC6 soak u) |
| GM-03 | +13.611 / +10.787 a | +6.254 / +4.852 a | +8.795 / +6.024 a | +3.585 / +3.932 a | +2.564 / +2.833 a | +1.934 / +2.156 a | +1.856 / +2.072 a | +1.353 / +1.531 a | +1.227 / +0.796 a | +1.225 / +0.795 a | +1.893 / +1.334 a | +4.793 / +3.674 a | +11.646 / +9.202 a | +1.881 / +1.324 a | +13.300 / +10.536 a | +72.008 / +57.900 a | >+99 / +71.545 a | - | - | - | +0.795 (LC3 hot bound u) |
| GM-08a | +61.651 / +49.544 a | +32.135 / +25.732 a | +32.080 / +22.722 a | +21.291 / +22.978 a | +16.337 / +17.649 a | +13.281 / +14.362 a | +12.900 / +13.952 a | +10.455 / +11.322 a | +5.528 / +4.266 a | +5.523 / +4.262 a | +12.101 / +9.569 a | +15.110 / +11.997 a | +37.240 / +29.850 a | +12.079 / +9.551 a | +37.360 / +29.947 a | >+99 / >+99 a | >+99 / >+99 a | - | - | - | +4.262 (LC3 hot bound u) |
| GM-08b | +56.638 / +45.500 a | +28.473 / +22.777 a | +35.973 / +25.514 a | +18.126 / +19.573 a | +13.877 / +15.003 a | +11.256 / +12.183 a | +10.929 / +11.832 a | +8.839 / +9.584 a | +10.694 / +8.434 a | +10.667 / +8.412 a | +10.525 / +8.298 a | +22.858 / +18.247 a | +49.715 / +39.914 a | +10.499 / +8.277 a | +49.877 / +40.045 a | >+99 / >+99 a | >+99 / >+99 a | - | - | - | +8.277 (F2 hot bound u) |
| GM-09 | +64.003 / +51.441 a | +31.350 / +25.099 a | +35.853 / +25.428 a | +19.350 / +20.890 a | +14.799 / +15.994 a | +11.999 / +12.983 a | +11.651 / +12.608 a | +9.410 / +10.198 a | +5.134 / +3.948 a | +5.131 / +3.946 a | +12.056 / +9.533 a | +14.319 / +11.359 a | +42.664 / +34.226 a | +11.963 / +9.458 a | +43.439 / +34.851 a | >+99 / >+99 a | >+99 / >+99 a | - | - | +0.626 / n/a | +0.626 (J-FD09 y) |
| GM-10 | +89.997 / +72.412 | +46.871 / +37.620 | +22.208 / +15.643 | +30.505 / +32.889 | +23.597 / +25.458 | +19.309 / +20.846 | +18.773 / +20.270 | +19.238 / +20.769 a | +3.708 / +2.798 | +3.646 / +2.748 | +3.618 / +2.726 | +14.128 / +11.205 | +76.758 / +61.732 a | +3.596 / +2.708 | +77.024 / +61.946 a | +32.616 / +26.119 | +45.559 / +32.388 | - | - | - | +2.708 (F2 hot bound u) |
| GM-13 | +67.053 / +53.901 a | +34.896 / +27.959 a | +15.399 / +10.760 a | +22.696 / +24.490 a | +17.500 / +18.900 a | +14.274 / +15.430 a | +13.872 / +14.997 a | +22.434 / +24.208 a | +2.418 / +1.757 a | +2.375 / +1.723 a | +2.578 / +1.887 a | +9.510 / +7.479 a | +61.967 / +49.799 a | +2.531 / +1.849 a | +76.436 / +61.471 a | +24.422 / +19.509 a | +34.211 / +24.250 a | - | - | - | +1.723 (LC3 hot bound u) |
| GM-14 | >+99 / >+99 a | >+99 / >+99 a | +18.968 / +13.319 a | >+99 / >+99 a | >+99 / >+99 a | >+99 / >+99 a | >+99 / >+99 a | >+99 / >+99 a | +2.434 / +1.771 a | +2.418 / +1.758 a | +2.509 / +1.831 a | +10.565 / +8.330 a | +77.419 / +62.264 a | +2.492 / +1.817 a | >+99 / +81.872 a | >+99 / >+99 a | >+99 / >+99 a | - | - | - | +1.758 (LC3 hot bound u) |
| GM-16a | +29.165 / +24.993 a | +15.354 / +13.092 a | +5.523 / +3.996 a | +10.140 / +11.799 a | +7.697 / +8.993 a | +6.181 / +7.251 a | +5.992 / +7.033 a | +10.140 / +11.799 a | +0.372 / +0.183 a | +0.369 / +0.179 a | +0.568 / +0.351 a | +3.197 / +2.616 a | +29.491 / +25.274 a | +0.548 / +0.334 a | +47.292 / +40.613 a | +10.802 / +9.170 a | +15.346 / +11.521 a | - | - | - | +0.179 (LC3 hot bound u) |
| GM-16b | >+99 / +89.126 a | +89.402 / +76.900 a | +8.123 / +5.988 a | >+99 / >+99 a | >+99 / >+99 a | >+99 / >+99 a | >+99 / >+99 a | >+99 / >+99 a | +0.450 / +0.250 a | +0.449 / +0.248 a | +0.531 / +0.319 a | +4.299 / +3.566 a | +45.191 / +38.802 a | +0.524 / +0.313 a | +71.675 / +61.624 a | >+99 / >+99 a | >+99 / >+99 a | - | - | - | +0.248 (LC3 hot bound u) |
| PD-01R | +1.886 / +1.338 r | +1.862 / +1.318 r | - | +4.444 / +4.883 r | +4.207 / +4.628 r | +2.827 / +3.136 | +2.670 / +2.966 | - | +4.237 / +3.243 | +1.477 / +1.006 r | +2.484 / +1.823 | +3.956 / +3.015 | +20.413 / +16.349 | +0.981 / +0.604 r | -0.315 / -0.451 r | -0.387 / -0.509 r | -0.081 / -0.346 r | - | - | - | -0.509 (TB70 u) |
| PD-01S | +1.590 / +1.097 r | +1.590 / +1.097 r | - | +4.273 / +4.699 r | +4.008 / +4.412 r | +2.850 / +3.161 r | +2.698 / +2.997 r | - | +5.864 / +4.562 | +1.323 / +0.881 r | +3.513 / +2.657 | +5.515 / +4.279 | +21.487 / +17.219 | +0.971 / +0.596 r | -0.378 / -0.502 r | -0.444 / -0.555 r | -0.166 / -0.407 r | - | - | - | -0.555 (TB70 u) |
| HW-101 (J-FWD) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | +0.650 / +0.301 p | - | - | +0.301 (J-FWD u) |
| HW-103 (J-FD01) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | +0.121 / +0.379 | - | +0.121 (J-FD01 y) |
| HW-127 (J-FD09) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | +0.221 / +0.485 | +0.221 (J-FD09 y) |

### OP-moment residue: DERIVED bounds beside cells


GM-01 FA-1 cells (`gm01_rodpath_bound_v352.json` f24544c124289069): ROD_1 residue + (tension) in every case; GM-01 stress per unit rod force from the EA unit steps of pose_neutral_c71 (v3.5.1 L1, rev-1 lever; cell node n88188 = c71 n55792 at 0.000 mm) [DERIVED; transfer ASSUMED].

| cell | as found (posted) | ROD_1 as found / moment-free N | moment-free (tensor) | sign-free bound (triangle) |
|---|---|---|---|---|
| GM-01 FA1Q | +0.767 / +1.030 | +130.1 / +2.9 | +0.796 / +1.063 | +0.730 / +0.987 |
| GM-01 FA1D | +0.373 / +0.578 | +166.6 / +2.9 | +0.396 / +0.603 | +0.344 / +0.544 |
| GM-01 FA1U | +0.130 / +0.299 | +201.8 / +2.9 | +0.149 / +0.320 | +0.107 / +0.272 |
| GM-01 FA1S | +0.100 / +0.264 | +207.3 / +2.9 | +0.118 / +0.285 | +0.077 / +0.238 |
| GM-01 FA1T | +0.777 / +1.042 | +130.1 / +2.9 | +0.806 / +1.075 | +0.739 / +0.998 |

Hot-bound base residue (`hb_base_residue_v352.json` e46d41bace79be47): base +86 / +66 N at Pc_max; rods prescribed (LC3 runaway, GS): REPLACED to within (t_base - t_pose) Pc_max; rods reacting inertia (TD, LC6): ADDS.  Worst-sign estimate dMS <= (1 + MS) dF / F [DERIVED; ASSUMED linear, whole increment rod-driven].

| cell (lever root) | governing pose | lever rod d_rod N (sign) | dF / F |
|---|---|---|---|
| LC3 GM-01 | stop315 | ROD_1 +11.9 | 0.0195 |
| LC3 GM-02 | stop045 | ROD_2 +12.6 | 0.0207 |
| F2 GM-01 | alpha+ | ROD_1 +10.1 | 0.0183 |
| F2 GM-02 | alpha- | ROD_2 +10.9 | 0.0197 |

## 4. Governing findings: the negative cells, their classes and what closes them

Source: `tables/margin_matrix_v352.md` (section 3A), section 'Negative cells and their classes'. Classes are REV-MECH-2 section 10: DC design-check, TS-183 / TS-212 thermal-secondary under lines 183 / 212, BR brittle, CH char primary, MF model fidelity, BT mesh defect. Negatives are quoted as found. No margin is forced, and nothing here is a physical approval.

### 4.1 By class

| class | part / columns | cell y / u (as found) | what closes it (owner) |
|---|---|---|---|
| **DC** | TC-01 J-FWD (seat / ring line P+Q at soak) | **-0.075** / +0.239 (y: SOAK seat line, IN718 at 3750 N, Mechanical v7 mapped on v3; the FE minima on the final envelope v6 `43a5d78b67c615fc`: SOAK -0.071, SOAK70 -0.055, SOAK52 -0.030; 10A.11) | Mechanical: the single IN718 re-map and the select-fit band re-size on the final envelope v6 (inputs `jfwd_v7inputs_cD_v352.json`, lead 05:27Z (3)); the HW-170 disc-spring route (i) and the preload-retention audit (240 (10)); the soak lines are P+Q <= 2 Fty(T) (secondary), the worst computed instance, not a proven bound |
| **MF** | TC-01 FA1U / FA1S global (n9090 regular, 1.05 mm from the J-FWD RBE3) | -0.083 / -0.012; -0.107 / -0.037 | governing = the J-FWD sub-model's TC-01 FA1S criterion rows, **+0.005 / +0.239** (`jfwd_fix_v352_v2.json` 760d6c6f2d7d46d5); v7 +0.259 and js5 +0.171 / +0.263 beside it; FA1U bounded by FA1S, js5b FA1U +0.222 / +0.318 (10A.13) [DERIVED]; the (b1) FA1S rows are information (10A.12) (lead 21:47:29Z (3)) |
| **MF** | TC-01 TB70 (n9090, the J-FWD connector) | +0.120 / -0.110 | connector artefact; the J-FWD sub-model closes it: FA1S and the js5b LC2 rows bound the primary (LC2Y / LC2U +0.421 / +0.424, 10A.13) (lead 08:58Z) |
| **TS-212** | TC-02 TB70 / TBS (n30266, 228.7 C) | -0.236 / -0.271; +0.138 / -0.035 | 212 (1) (a)-(c) pass; (d) time at temperature open with T-F1, Mechanical's (b) package. The seat at TB: see 4.3 |
| **TS-183** | TC-03 LC1 / LC2 (GVHI, n46040, B1_1) | -0.088 / -0.170; -0.092 / -0.175 | 183 (1) (a) primary +8.0 and (b) P+Q +1.74 pass; (c) LCF and (d) GlidCop time at temperature with Mechanical; MF on the value (gap variant, RM2-13); **S-AX governs: v352r4 +2.564 / +2.241** (lead 07:51Z (a)) |
| **TS-183** | TC-03 LC3 / F2 hot bound (n38065), TB70 (n48254, 181.3 C) | -0.107 / -0.188; -0.121 / -0.201 | as above |
| **TS-183** | FD-01 LC6 soak / TB70 / TBS (FD01_TC02_screws bonded-patch edge, ID) | -0.187 / +0.780; -0.336 / +0.484; -0.005 / +0.976 | all-node value kept (no named sub-model, 234 (4)); (a) primary and (b) P+Q pass; (c) LCF with Mechanical; (d) on the sourced long-time allowable where T <= 150 C, else T-F1. The TB rows are at **A 175 C, hotter than the adopted 150 C** (tb352g / h; the T-F1 exposure basis, lead 21:51:30Z) |
| **BR** | NZ-01 LC1 / LC2 / LC3 hb / F2 hb / LC6 soak / TB70 / TBS | -0.520 ... -0.054 (yield only) | brittle and thermal: 183 (2) capture / containment shown plus a test basis, else a design change. S-AX v352_NF2b is the named sub-model; the 3-D value is a global check (lead 05:45Z) |
| **CH** | NZ-03 LC2 / TB70 / TBS (n81357) | -0.088; -0.392; -0.253 | char primary against the ASSUMED 20 MPa: N-F1 (>= 21.96 MPa inside the 23.7 MPa acceptance); tie edge: 188 (3) contact FE + N-F1 |
| **MF** | PD-01R / PD-01S LC6 soak / TB70 / TBS | -0.315 / -0.451 ... -0.444 / -0.555 | PD-02 is rigid in the model (same alloy): the PD-01 / PD-02 mismatch is a model artefact; primary-only above +20 (lead 07:51Z (e), 08:04Z) |
| **BT** | TC-04 LC3 / F2 hot bound (n42993) | +0.228 / **-0.004**; +0.223 / **-0.008** | see 4.2 |

### 4.2 TC-04: a mesh-defect node, found negative

- n42993 sits on two TC-04 tets of quality q 0.040 / 0.027 (post_f1.tet_quality). Its hot-bound values are **-0.004 (LC3) / -0.008 (F2) on ultimate**, node-wise [DERIVED lower bound].
- This is not an exception under 234 (4): a bad tet is a discretisation defect, refinement convergence is not shown, and no refinement or sub-model replaces it. The cell stays negative, class BT, as found (lead 21:47:29Z (4)).
- The part-wide bound (4.4) is equal at 3 decimals on TC-04, so it does not move the cell.
- Settling route: remesh TC-04 to q >= 0.1 and re-solve the hot-bound bases and the 17 R3 poses, sharing one re-solve with the OP-moment route (4.5); about 2.7 h ccx, about 2.50 GiB free needed at each start [DERIVED from the logged runs]. **NOT RUN, final** (lead 2026-10-21T03:30:46Z (2)): each start would end under the 1.86 GiB floor, and nothing frees 1 GB or more (the 23 uncited v3.4.1 result files stay). TC-04 stays a found negative, class BT, -0.004 / -0.008 [DERIVED node-wise lower bound]; the regular nodes within 2 mm are at +0.643 or above (section 11).

### 4.3 The seat at TB (carried wording)

"Mechanical's S-AX v352r4 (tie model, rev 4) fails line 106 at SF 1.0 at TB70: TC-02 regular -0.326 / -0.371, and the TC-03 d12.5 R0.6 undercut root -0.191 / -0.264. So your global TB pass does not close the seat region. Mechanical's T-F2 contact runs and the abort search decide."

### 4.4 Hot-bound cells: node-wise (s) and part-wide (w) bounds

- **s**: a hot-bound all-node value at a singular node is lowered to the node-wise bound at that node (`hb_singular_check_v352.json` 7d4ab97c0d7d3e75, left as written).
- **w**: the hot-bound all-node value is replaced by the part-wide bound over every node of the part where that is lower at 3 decimals, with the stored value beside it (`hb_partwide_v352.json` cc96d78d266df4db). Cells: TC-09 F2 hb +1.091 / +0.826 (stored +1.092 / +0.827), NZ-01 LC3 hb -0.403 (stored -0.402), FD-01 LC3 hb +0.837 / +2.620 (stored +0.848 / +2.640) and F2 hb +0.830 / +2.606 (stored +0.840 / +2.625).
- **Limitation (stated, lead 21:47:29Z):** increments of parts outside SAME_MESH_ENGINE are not summed node by node (lc3_bound is unchanged; no re-solve).

### 4.5 The OP-moment residue (MF observation)

- The OP unit step of the v3.5.2 models carries a moment about the pivot that the physical load does not have (closed cavity, axisymmetric exit). The rods are the only moment path, so it shows as a rod-force pair (sections 7.5, 9B.3). Its size: L1 global Q [539, 484] N mm/MPa (0.72 N m/MPa, against 0.27 on the v3.5.1 L1 model); R3 poses Q [304-307, 2298] N mm/MPa; the cause found is a couple of about 1.56 N m/MPa at elements 24664 / 23610 at p/Pc 0.75 (9B.3).
- Treatment (lead 22:24:34Z, 22:54:03Z, 23:12:52Z):
  - F2 and LC3 cells stand as found, with the moment-free statics estimate beside each affected row; they are **not proven conservative for every part**.
  - Datasheet hole loads: governing = the larger of the as-found value and the moment-free estimates (section 8). The estimate governs every L1 case maximum (3.5-7.8 %).
  - GM-01 FA1Q-S cells: a DERIVED bound beside each, from the ROD_1 force with and without the residue (section 3A).
- Re-solving with a moment-free OP step shares the route in 4.2: **NOT RUN, final**, for disk (lead 2026-10-21T03:30:46Z (2)). The OP couple stays an MF observation, with the moment-free estimate beside each affected row.

## 5. Mesh convergence (RM2-03 folded)

**5.1 The v3.5.1 study, re-stated (RM2-03).**
- What changed: `post_conv.py` `gci()` now returns no observed order and no GCI when |e32 / e21| < 1. The v3.5.1 version extrapolated anyway.
- Republished as `results/v352/f1_convergence.json` (the same L1 / R2 / R3 runs, no new solve) [SIM / DERIVED].
- Result: at every point the changes grow with refinement, or oscillate, so none of the four points is in the asymptotic range. No order and no GCI are quoted.

| Point | Quantity | L1 (h mm) | R2 (h mm) | R3 (h mm) | change L1 -> R2 / R2 -> R3 | e32 / e21 | MS L1 / R2 / R3 |
|---|---|---|---|---|---|---|---|
| NZ-01 throat, B1_1 | -s3 (MPa) | 69.0 (3.63) | 71.4 (0.72) | 75.1 (0.40) | +3.5 % / +5.1 % | 0.67 | -0.435 / -0.454 / -0.481 |
| TC-03 flange corner, B1_1 | vM | 241.2 (0.98) | 225.9 (0.33) | 252.3 (0.21) | -6.4 % / +11.7 % | -0.58 (oscillating) | -0.312 / -0.266 / -0.342 |
| TC-02 TB1 tie end, B1_19 | vM | 102.4 (4.84) | 102.1 (1.21) | 83.0 (0.43) | -0.3 % / -18.7 % | 0.015 | +0.096 / +0.213 / +0.469 (u -0.119 / -0.040 / +0.165) |
| TC-01 J-FWD hole, FA1S | vM | 303.0 (3.04) | 302.6 (1.28) | 295.9 (0.68) | -0.1 % / -2.2 % | 0.056 | -0.221 / -0.220 / -0.202 (u -0.160 / -0.159 / -0.140) |

**J-FWD wording (RM2-03, replaces "converged within 2.4 %" of v3.5.1 REPORT 4.5):** the regular-set value at the TC-01 J-FWD hole changes by -0.1 % from L1 to R2 and by -2.2 % from R2 to R3. It is not in the asymptotic range and it depends on the idealisation. The all-node value at the RBE3 patch edge grows (357 -> 382 -> 399 MPa). For v3.5.2 that value is superseded: the one-sector contact sub-model replaces the RBE3 connector (section 10A).

**5.2 Lever roots on rev 3 (filleted R1.5 junction; section 6).**
- Mesh levels: R2 = h 0.5 / 0.4 mm on the six junction faces; R3 = h 0.25 / 0.2 mm (lever-root faces and balls).
- The governing node lies on the R1.5 junction fillet (CAD faces 31 / 32), 8.5 mm from the nearest flagged re-entrant node, so all-node and regular values coincide.

| Pose / lever | R2 vM max (MPa) | R3 vM max (MPa) | change R2 -> R3 | MS R3 y / u | Note |
|---|---|---|---|---|---|
| stop045 GM-02 (LC3, cold) | 191.1 (n89953) | 207.5 (n145697) | +8.6 % | +0.510 / +0.301 | not converged by the 5 % test: the cell quotes the p = 1 bound, **+0.400 / +0.206** (below); no R4 run |
| stop045 GM-01 (LC3) | 97.1 (n58233) | 96.7 (n58609, RE 0.21 mm) | -0.4 % | +2.240 / +1.792 | R3 value; regular set 40.8 -> 40.7 MPa (-0.3 %), +6.704 / +5.638 |
| stop315 GM-01 (LC3) | 199.9 (n71484) | 204.3 (n79483) | +2.2 % | **+0.534 / +0.322** | R3 value (the F1 LC3 GM-01 cell) |
| stop315 GM-02 (LC3) | 60.5 (n99541) | 62.3 (n132562, RE 0.10 mm) | +3.0 % | +4.028 / +3.333 | R3 value; regular set 34.3 -> 35.1 MPa (+2.1 %) |
| alpha+ GM-01 (GS) | 183.0 (n62856) | 190.2 (n65042) | +3.9 % | **+0.648 / +0.420** | R3 value (the F2 GS GM-01 cell) |
| alpha+ GM-02 (GS) | 139.8 (n89953) | 149.3 (n145697) | +6.8 % | +1.098 / +0.808 | not converged: the cell quotes the p = 1 bound, 158.9 MPa, +0.972 / +0.699 |
| alpha- GM-01 (GS) | 141.7 (n71484) | 146.8 (n79484) | +3.6 % | +1.135 / +0.840 | R3 value |
| alpha- GM-02 (GS) | 178.2 (n103919) | 187.5 (n156946) | +5.3 % | +0.671 / +0.440 | not converged: the cell quotes the p = 1 bound, 196.9 MPa, **+0.591 / +0.371** (the F2 GS GM-02 cell) |

- Two levels cannot show convergence. The cell therefore quotes a bound on the R3 value, with R2 and R3 shown beside it (lead 12:28Z (5)). The bound uses an ASSUMED observed order p = 1 and the h ratio 2 [DERIVED; order ASSUMED; no R4 run]:
  - p = 1: 207.5 + 16.4 = 223.9 MPa, so **MS_y +0.400 and MS_u +0.206** (AL7075-T6 at 22.7 C: Fty 470, Ftu 540 MPa; SF 1.5 / 2.0). This is the GM-02 LC3 cold cell of the matrix.
  - p = 2 (information): 207.5 + 16.4 / 3 = 213.0 MPa, so +0.471 / +0.268.
- The peak is on the smooth R1.5 junction fillet. It is 8.5 mm from the nearest re-entrant node of GM-02 and 7.9 mm from the nearest re-entrant node of any part. The R2 and R3 peaks are 0.41 mm apart (faces 31 and 32).
- R2 exists at stop045, stop315, alpha+ and alpha- (both levers each). Three of the eight lever records change by more than 5 % from R2 to R3, all on GM-02: stop045 +8.6 %, alpha+ +6.8 % and alpha- +5.3 %. These three cells quote the p = 1 bound, the other five the R3 value. The R2 and R3 peaks lie 0.19-0.79 mm apart on the same junction fillet at every R2 pose [SIM; bound DERIVED, order ASSUMED].
- At the 13 poses without an R2 run the cell is the R3 value. Ten of those rows peak at node 145697 or 156946, the R2-checked nodes that changed by +8.6 % and +5.3 %. Adding the same MPa increment there (information, not ruled) leaves the worst at +0.540 / +0.327 cold and +0.303 / +0.123 hot (combined045 GM-02), above the governing values (section 6).
- Numbers: `results/v352/lever_root_bound_v352.json` (scripts/lever_root_bound_v352.py); per pose in `results/v352/lever_root_table_v352.json` (section 6).

**5.3 J-FWD sub-model (section 10A).**
- Mesh: tap-to-drill wall 1.910 mm at h 0.3 (CAD 1.906 mm); hole / tap edge median 0.300 mm.
- The js5 global sector (s5, 110,253 nodes) is the reference. The local seat patch reproduces it at mu 0 at PRELOAD and FA1S within 5 % on the 54 seat lines, the screw sections and the seat window force (10A.4).
- The broken-edge patch is checked at two mesh levels at mu 0, (b2') against (b2) (lead 11:25Z; 240 (9)(v)). The test is the 5 % rule at PRELOAD and FA1S (lead 15:37Z (R3)).
  - s6, (b2): h_brk 0.08 mm with a 0.6 mm transition; the L12 patch has 107,611 nodes. This is the finer mesh.
  - s9, (b2'): h_brk 0.15 / 0.3 mm; 60,812 nodes. This is the coarser mesh, built cheap for the friction run (b1).
- **Result: NOT within 5 %** (`jfwd/runs/seat_s9L12_mu0/judge_seat_s6L12_mu0.json` `3619a7b39613edf0`) [SIM; DERIVED ratios].
  - PRELOAD: the 54 lines differ by up to 15.1 % (32 lines over 5 %); the seat window by +14.4 %; M at x' 28.6 by -36.6 % (273.8 vs 431.9 N mm, a small moment). N is equal.
  - FA1S: lines up to 10.7 % (8 lines over 5 %); N and the HEAD force +5.1 %; the seat window +60.9 %. V (+0.7 %), M at x' 28.6 (+2.3 %) and the hole bearing (+1.0 %) agree.
  - Direction: the P+Q rises with refinement. On the governing line d+6.051 z'0 the s6 / s9 PmPb ratio is 1.178 / 1.124 / 1.126 / 1.124 / 1.119 (PRELOAD / SOAK52 / SOAK / SOAK70 / FA1S). On 47-53 of the 54 lines s6 is the higher.
  - No level finer than s6 was run. Two levels cannot show convergence (as in 5.2), so the s6 values are neither shown to be converged nor shown to bound the converged value.
- Consequence (240 (9)(v)): (b1), solved on s9, is corrected by the s6 / s9 ratio at mu 0 and tagged DERIVED. **C1 ADOPTED** (lead 2026-10-21T01:30:18Z (5); accepted 02:01:34Z (A), `results/v352/jfwd_b1_meshcorr_v352.json` `adac16afd42ef7bd`): per line and state MS_C1 = (1 + MS_b1) / max(1, r) - 1, r = PmPb s6 / s9 at mu 0, floored at 1.00; the repeats take their state's ratio [ASSUMED]. The table is in 10A.6. C0 (as solved) is the record.
- **C2 (sensitivity, not in the cells):** the s6 - s9 difference added in MPa instead of the ratio. On the governing line it gives (b1) SOAK52 -0.074, SOAK -0.083, SOAK70 -0.062, FA1S +0.014 (C1: -0.030 / -0.041 / -0.016 / +0.068) [DERIVED].
- **MF note (lead 01:30:18Z (5b)).** The seat-line P+Q is **not shown converged**: s9 -> s6 raises it by 12-18 % on the governing line. Under 234 (4) the s6 value is quoted as found.
- **Two-mesh estimate, information** [ESTIMATE: two meshes, observed order ASSUMED p = 1 / p = 2, h ratio 0.15 / 0.08; the meshes are not geometrically similar]. Governing line d+6.051 z'0 and the band anchor (the envelope's highest seat-line PmPb in the state):

| State | s9 / s6 PmPb (MPa) | p = 1: factor, line MS | p = 2: factor, line MS | Band anchor (MPa, from), MS | Anchor at p = 1 / p = 2: MS |
|---|---|---|---|---|---|
| PRELOAD | 199.9 / 235.5 | 1.173, +0.738 | 1.060, +0.922 | 235.5 (b2), +1.038 | +0.738 / +0.922 |
| SOAK52 | 323.1 / 363.3 | 1.127, -0.122 | 1.044, -0.053 | 370.3 ((b1) C1), -0.030 | -0.139 / -0.071 |
| SOAK | 324.1 / 365.0 | 1.128, -0.173 | 1.045, -0.107 | 366.8 ((b2) rep), -0.071 | -0.176 / -0.111 |
| SOAK70 | 322.3 / 362.1 | 1.126, -0.160 | 1.044, -0.095 | 362.1 (b2), -0.055 | -0.160 / -0.095 |
| FA1S | 400.5 / 448.3 | 1.122, -0.061 | 1.042, +0.010 | 448.3 (b2), +0.053 | -0.061 / +0.010 |

- **COSTING of one check finer than s6 (lead 01:30:18Z (5b); no solve)** (`results/v352/jfwd_convcheck_costing_v352.json` `b427869869a9e8f8`, table `e670c97d74640e66`, script `jfwd_convcheck_costing_v352.py` `eb5f7e3b6c15e6b2`; evidence `runs/cost_convcheck_v352/`). Candidate meshes were built (gmsh, no deck) and their L12 patch counted; peak RSS ~ N^1.06 and s / increment ~ N^1.50 through the two measured mu 0 runs [ESTIMATE, +/-10 % assumed]. A global break-zone step (h_brk 0.064 / 0.060 / 0.056: 134k / 143k / 155k patch nodes, 7.29 / 7.81 / 8.48 GiB) does not fit the 8 GiB cap with its 10 %. A local refinement on s6 does: **cD**, s6 + two Ball fields h 0.04 mm (r 0.3 + 0.3 transition) at both ends of the governing line (h ratio 2.0 to s6 there), 123k nodes, 6.65 GiB (7.32 with 10 %), 2.1-2.7 h.
- **cD (lead 2026-10-21T02:01:34Z (C): GO after js5b, on the FINAL TC-01 `fcb3b5b93bebdb01`).** Built with a cD-only copy of the mesher (`scripts/jfwd_sub_cD.py` `0422fa6a9910bef2`: only the TC-01 sha expectation and the two Ball fields differ; production `jfwd_sub.py` `cbc4c2ae2a1b61fd` untouched). Mesh sD 176,037 nodes / 109,387 tets (q_min 0.0228; s6 0.0089); patch sDL12 124,669 nodes, deck `d7771451a7369dc1`; RSS 6.73 GiB estimated (7.41 with 10 %, limit 7.5), 2.1-2.7 h [ESTIMATE]. Run folder in /dev/shm (RAM), approved for cD only. It ran 2026-10-21T03:18:46Z-05:09:25Z (6639.2 s; peak RSS 6.875 GB against 6.73 estimated, +2 %; rc 0) and was posted 05:10:18Z (12 posts rc 0, `runs/post_cD.log` `5f696dded48b0c3c`); frd.gz `366a1f9d6d12aa9e` (raw = decompressed `02df780c504237ed`), deck `.inp.xz` `b70aeb2c9d467453` (raw = decompressed `d7771451a7369dc1`); RAM folder peak 187.7 MB against 190 predicted (-1 %), disk folder 42.0 MB against 44.0 (-4 %), lowest free 2.223 GiB; the RAM folder was removed at the stage end [SIM run record]. **Result (rule (C), ACCEPTED 05:17:36Z (1)):** cD / s6 on the governing line 0.927 / 0.947 / 0.966 / 0.959 / 0.985 (PRELOAD / SOAK52 / SOAK / SOAK70 / FA1S): s6 stands in every state (lower by more than 5 % at PRELOAD and SOAK52, within 5 % elsewhere) and C1 stands; no line is above 1.05 x s6 (table in 10A.6; `results/v352/jfwd_cD_result_v352.json` `8209e80f09f28af7`) [SIM; ratios DERIVED]. **MF note** (lead 05:17:36Z (2)): s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 % on the governing line; not monotonic; the mesh and the geometry change are not split; the seat-line P+Q is NOT shown converged. The two-mesh p = 1 / p = 2 estimate and C2 stay information.
- **Boundary extrapolation of the remeshed patches** (lead note on the cD setup; `results/v352/jfwd_patch_extrap_nodes_v352.json` `f95abde5b1489976`, script `jfwd_patch_extrap_nodes_v352.py` `2192167fde400a5d`) [DERIVED]. A remeshed patch's boundary nodes that fall outside the js5 global faceted volume take an extrapolated js5 field. Largest distance outside: s6L12 0.0188 mm (7 nodes > 0.01 mm), s9L12 0.0295 mm (15), sDL12 0.0431 mm (9). The 9 sDL12 nodes lie on the curved fit and outer surfaces: 7 on the TC-02 OD r 28.600 (the FIT interface, |y'| 4.9-7.2 mm, z' -4.6 to +12.1) and 2 on the TC-01 OD R31.75 (z' -11.5 / -12.6). The nearest is 6.02 mm from a Ball centre and from the governing line. None lies on the spot-face flat region, so the d11.2 flats are not the cause; the likely cause is s5's coarse facets on the curved surfaces [ASSUMED]. The extrapolation and the 9 sD nodes are information (lead 05:17:36Z (2)).

## 6. LC3 detail and the lever roots (brief item 1; ACCEPTED lead 20:44:07Z (1))

All values are SIM on CAD v3.5.2 (rev-3 levers, asm v1.3), cold unless stated. The p = 1 cells are DERIVED (order ASSUMED, no R4 run). The hot values are DERIVED: a node-wise sub-additive bound on SIM inputs, so they are lower bounds on the hot margin. None of it is physical approval.

### 6.1 LC3 at the 8 stop poses (R3; `results/v352/tables/f1_lc3_summary_v352r3R3.md`, `scripts/lc3_summary_v352.py`)

The case is the 8 deg stop, runaway with the rod at the 609 N stall limit, maximum thrust plus touchdown inertia: 64 sub-cases per pose, as in v3.5.1. Rod forces are max |F| over the 64 sub-cases (sign: - compression, + tension). Bearing and washer loads are max |component| of one bushing direction. The moment residual is |rods' reaction moment + bumper moment| / bumper moment in the BUMP unit step.

| pose | fb_run N | max rod abs N | lowest regular MS y / u (part) | lowest all-node MS y / u (part, class, d mm) | inner cup / washer N | outer cup / washer N | max hole shear N | moment residual |
|---|---|---|---|---|---|---|---|---|
| stop000 | 412-521 | -502.4 (ROD_2) | NZ-03 +0.179 / n/a; GM-02 +0.866 / +0.608; GM-01 +0.967 / +0.695 | NZ-03 +0.062 / n/a (ID, 0.0); GM-16b +0.774 / +0.529 (RE, 0.43) | 736 / 174 | 703 / 702 | 689 (AF_GM10_5) | 5.0e-7 |
| stop045 | 325-431 | -609.0 (ROD_2) | NZ-03 +0.188 / n/a; **GM-02 +0.510 / +0.301 (cell: p = 1 bound +0.400 / +0.206)**; GM-16b +1.106 / +0.815 | NZ-03 +0.063 / n/a (ID, 0.0); GM-16b +0.450 / +0.250 (RE, 0.54) | 524 / 460 | 510 / 517 | 836 (AF_GM10_5) | 1.6e-6 |
| stop090 | 301-420 | +609.0 (ROD_1) | NZ-03 +0.191 / n/a; GM-02 +0.925 / +0.658; GM-01 +0.993 / +0.717 | NZ-03 +0.063 / n/a (ID, 0.0); GM-16a +0.411 / +0.216 (RE, 0.43) | 195 / 686 | 379 / 189 | 863 (AF_GM10_2) | 2.6e-6 |
| stop135 | 161-269 | +609.0 (ROD_1) | NZ-03 +0.191 / n/a; GM-16a +1.229 / +0.921; GM-01 +1.245 / +0.934 | NZ-03 +0.062 / n/a (ID, 0.0); GM-16a +0.445 / +0.245 (RE, 0.43) | 261 / 526 | 292 / 477 | 882 (AF_GM10_2) | 1.0e-6 |
| stop180 | 246-359 | +609.0 (ROD_1) | NZ-03 +0.180 / n/a; GM-02 +1.038 / +0.756; GM-01 +1.053 / +0.769 | NZ-03 +0.062 / n/a (ID, 0.0); GM-16a +0.493 / +0.287 (RE, 0.43) | 426 / 174 | 459 / 740 | 890 (AF_GM10_2) | 8.9e-7 |
| stop225 | 170-277 | +609.0 (ROD_2) | NZ-03 +0.188 / n/a; GM-02 +1.198 / +0.894; GM-16b +1.225 / +0.917 | NZ-03 +0.063 / n/a (ID, 0.0); GM-16b +0.642 / +0.415 (RE, 0.43) | 272 / 535 | 299 / 484 | 881 (AF_GM10_5) | 2.6e-6 |
| stop270 | 317-433 | +609.0 (ROD_2) | NZ-03 +0.191 / n/a; GM-01 +0.888 / +0.627; GM-02 +0.953 / +0.683 | NZ-03 +0.063 / n/a (ID, 0.0); GM-16b +0.601 / +0.380 (RE, 0.43) | 196 / 698 | 386 / 189 | 861 (AF_GM10_5) | 2.4e-6 |
| stop315 | 334-443 | -609.0 (ROD_1) | NZ-03 +0.190 / n/a; **GM-01 +0.534 / +0.322**; GM-16a +1.100 / +0.809 | NZ-03 +0.062 / n/a (ID, 0.0); GM-16a +0.372 / +0.183 (RE, 0.54) | 534 / 465 | 519 / 524 | 836 (AF_GM10_2) | 2.0e-6 |

Reading the table:
- **Moment closure.** The residual is <= 2.6e-6 at every pose (v3.5.1: 2.6-5.2 %). The v1.3 tie formulation closes v3.5.1 open item 7.2 (section 7.1).
- **NZ-03.** The all-node minimum (+0.062) sits on the NZ-01 / NZ-03 tie-patch edge (ID, d 0). The named sub-model for that interface is Mechanical's S-AX v352_NF2b, so the regular value (+0.179 to +0.191, brittle compression, one value) stands in the matrix (234 (4)).
- **GM-16a / GM-16b horns** (unchanged parts). The all-node minimum lies 0.43-0.54 mm from a BREP re-entrant edge (RE, brep60). No sub-model replaces it, so it is the matrix cell: LC3 cold GM-16a +0.372 / +0.183 (stop315) and GM-16b +0.450 / +0.250 (stop045). These values are positive.
- **Bearing limits.** No HK0808 C0 or PTFE washer limit is in the hub. They stay **TO-VERIFY**; no value is invented.

### 6.2 The lever roots: F1 LC3 at the 8 stops and F2 GS at the 9 cones, cold and hot (`results/v352/lever_root_table_v352.json` 59d834055fa1d359, `results/v352/tables/lever_root_table_v352.md` c55f84ed22b3bb35, `scripts/lever_root_table_v352.py` eaabd770a1833c73)

**Geometry and allowables.**
- Levers: GM-01 (servo 1) and GM-02 (servo 2), rev 3. One R1.5 junction loop of 6 faces on r 38.5; minimum concave radius 1.466 mm.
- Mesh: R3, h 0.25 / 0.2 mm on the junction faces, two balls at h 0.25 (259,019 nodes).
- Material: AL7075-T6, Fty 470 / Ftu 540 MPa at the lever-root temperatures (19.98-24.2 C). SF 1.5 / 2.0.

**Cell rule** (lead 12:28Z (5)).
- The cell is the R3 value, unless R2 -> R3 exceeded 5 % (R2 exists at stop045, stop315, alpha+ and alpha-). There it quotes the p = 1 bound with R2 and R3 beside it (section 5.2).

**Hot bound.**
- Built per pose and node by node: vM_LC1(n) of the R3 base plus vM of the pose's own increment. The bases are hbg3 / hbh3 (GVLO / GVHI) at 4 burn states; the worst base and state are taken.
- At the cones the increment is the GS + TD + LC6 envelope of the pose, so the hot cone values are **lower bounds on the GS-only hot margin** (lead 20:44:07Z (1)).
- Hot + p1: the cold p = 1 increment is added at the three ruled GM-02 cells.
- Check: the per-pose minimum reproduces the published envelope bound exactly, 64 of 64 rows (part, set, base, state). The lever node numbering of the pose and base models is identical.

| case | lever | cold cell MS y / u (pose) | rule | hot cell MS y / u (pose; base, state) | rule |
|---|---|---|---|---|---|
| F1 LC3, 8 stops | GM-01 | **+0.534 / +0.322** (stop315; 204.3 MPa, n79483) | R3 value (+2.2 % R2 -> R3) | **+0.220 / +0.052** (stop315; GVHI B1_2: 28.0 + 228.7 MPa) | hot bound |
| F1 LC3, 8 stops | GM-02 | **+0.400 / +0.206** (stop045; 223.9 MPa) | p = 1 bound (+8.6 %; R3 207.5 MPa, +0.510 / +0.301) | **+0.202 / +0.036** (stop045; GVLO B1_2: 19.0 + 225.2 + 16.4 MPa) | hot bound + p = 1 increment |
| F2 GS, 9 cones | GM-01 | **+0.648 / +0.420** (alpha+; 190.2 MPa, n65042) | R3 value (+3.9 %) | **+0.289 / +0.111** (alpha+; GVHI B1_21.65) | hot bound |
| F2 GS, 9 cones | GM-02 | **+0.591 / +0.371** (alpha-; 196.9 MPa) | p = 1 bound (+5.3 %; R3 187.5 MPa, +0.671 / +0.440) | **+0.337 / +0.152** (alpha-; GVHI B1_21.65: 22.2 + 202.8 + 9.4 MPa) | hot bound + p = 1 increment |

- The all-node and regular sets give the same values at every governing row. The peak is on the smooth R1.5 junction fillet, 8.5 mm from GM-02's nearest re-entrant node and 7.9 mm from any part's (section 5.2).
- **No lever-root row is negative**: 0 of 68 rows, cold or hot, at all 17 poses.
- **Information only, not ruled:** 10 rows at the 13 poses without an R2 run peak at the two R2-checked nodes that changed by +8.6 % (n145697) and +5.3 % (n156946). Adding the same MPa increment there leaves the worst at +0.540 / +0.327 cold and +0.303 / +0.123 hot (combined045 GM-02). Both are above the governing values.

**Change against v3.5.1** (rev-1 levers, zero-radius junction; v3.5.1 report claims 5 and 11):

| | v3.5.1 | v3.5.2 rev 3 |
|---|---|---|
| F2 GS, GM-02 | -0.223 / -0.330 (alpha-, 403 MPa) | +0.591 / +0.371 (p = 1) |
| F2 GS, GM-01 | -0.209 / -0.319 (alpha+, 396 MPa) | +0.648 / +0.420 |
| F1 LC3, GM-02 | -0.280 / -0.379 (R3, 435 MPa) | +0.400 / +0.206 (p = 1) |
| F1 LC3, GM-01 | -0.273 / -0.374 (R3, 431 MPa) | +0.534 / +0.322 |
| F2 hot bound, GM-02 / GM-01 | -0.259 / -0.362, -0.219 / -0.327 | +0.337 / +0.152, +0.289 / +0.111 |

The rev-3 R1.5 junction removes the v3.5.1 lever-root negatives in every case. Quote these values as SIM / DERIVED on CAD v3.5.2, not as physical approval (lead 20:44:07Z (1)).

## 7. Model findings and fixes (asm v1.3, the J-FWD sub-model and the post-processing)

### 7.1 Tie formulation: v3.5.1 open item 7.2 resolved; asm v1.3 'tiex' (FEA3D-owned model finding)

**Finding.** In asm v1.1 / v1.2 a tied (dependent) node follows the tri6 interpolation of the independent face at its projection point. Where the CAD leaves a gap or an overlap d between the two surfaces, a rigid rotation theta of the pair violates the tie by theta x d. The ties then add a spurious rotational stiffness to the engine group, and the reaction moment is not conserved (the force pair is offset by d).

**Evidence** [SIM model data; patch test, no solve: `scripts/tie_patch_legacy.py`, `scripts/tie_patch_tiex.py` -> `results/v352/tie_patch_legacy_v352.json`, `results/v352/tie_patch_tiex_v352.json`; stop045 L1 model on CAD v3.5.2]:
- Legacy ties: the TB1 thread tie TC03_TC02_thread (R7 major on the R6.5 minor bore, CAD overlap 0.5 mm) violates a unit rigid rotation by rms 0.35-0.51 mm/rad (max 1.13 mm/rad). The other 17 ties: rms 0.000-0.055 mm/rad.
- Effect, LC3 BUMP unit step on CAD v3.5.2 (pose_stop045_v352L1, legacy ties): moment closure 0.82 (relative residual 0.181), rods R1 / R2 absorbing 96 %. On the v3.5.1 c71 model (asm v1.2) the same check gave 0.971 (residual 0.029), the 97-99.5 % of v3.5.1 open item 7.2.
- Consequence in v3.5.1 too: under the BUMP step TC-03 carried 0.17 MPa per N bumper (v3.5.2 legacy 0.29) although it is not in the bumper load path. The v3.5.1 LC3 TC-03 cells (stress about 70-150 MPa at fb_run 400-520 N) include this artefact. They are not governing (LC3 cold TC-03 +9.2) and they are not used for v3.5.2.

**Fix (asm v1.3, default for CAD v3.5.2; `asm3d.VERSION` 'fea3d-asm v1.3').** u_d = sum_k N_k(x_p) u_k + sum_i (grad lambda_i . (x_d - x_p)) u_i over the four corners of the independent face's straight-sided parent tet. This is exact for every linear displacement field.
- Patch test: residual <= 6.7e-12 for the three rigid rotations, uniform strain and a random affine field, on all 18 ties; 0 fallbacks; equation counts unchanged.
- Closure with v1.3: BUMP moment residual 1.1e-6 (L1x) and 1.6e-6 (rev-3 R3); R1 / R2 absorbed 100.0 %.
- Effect on the v3.5.1 cells: **NOT RUN.** The bounding re-runs pose_stop045_c71x, pose_neutral_c71x and lc1v351_c71x (CAD v3.5.1, asm v1.2 + tiex) were deferred to the end (lead 16:20Z (3)). They are not run unless disk space appears after js5b (lead 18:50:09Z; section 11).
  - The v3.5.1 cells stay as published, with their own bound (closure 97-99.5 %, v3.5.1 item 7.2).
  - So the tie formulation and the CAD / TB1-mode change are not separated by a solve. Section 9B.3 separates them by load for the F2 rod forces.

### 7.2 Mass-item attachment cache (v3.5.1 model, minor)

Section 2.1 gives it: the v3.5.1 BLEED and TC10 items were attached through the v3.5 surfaces because the sample cache was not keyed by CAD. Fixed in v1.3 (per-CAD cache). Bound: no v3.5.1 cell moves at the published decimals [DERIVED].

### 7.3 J-FWD sub-model and post-processing findings

1. **FIT faceting interference (model finding, fixed before any reported run).**
   - What happened: straight-sided C3D10 chords (sagitta up to 0.05 mm) turned the 0.025 mm design gap of the TC-01 / TC-02 fit into a scattered gap, with some nodes in interference. In the first trial deck t1, 595 of 1190 FIT slave nodes closed at PRELOAD.
   - Fix: `*CLEARANCE` on the FIT pair (0.025 mm, later the drawing maximum 0.078 mm), which overrides the faceted geometric gap. The undeformed-mesh audit (`scripts/jfwd_fit_gap0.py` -> `results/v352/jfwd_fit_gap0.json`) gave t1 median 0.024 mm, 13 of 1025 nodes in interference, min -0.009 mm.
   - t1 is INVALID: TC-02 ground springs of 0.1 N/mm let it drift 0.44 mm, and it had no tap-wall size field. It is kept for the record only. The INTERIM 2 statement "about 51 kN radial" was a biased CPRESS integral (item 2); the exact value is 1878 N.
2. **MF-J1: CPRESS face-mean integration is biased.**
   - Size of the bias: on C3D10 contact faces the face-mean CPRESS integral over-states the contact resultant (js4 PRELOAD x1.8 HEAD, x7 FIT; t1 x1.7 HEAD, x27 FIT).
   - What is used instead: every contact resultant in this report comes from K u nodal forces (`jfwd_post.contact_forces_exact`, `jfwd_seatforce.py`). These close exactly: the PRELOAD head force is 3750.1 N for a 3750 N pretension.
   - CPRESS is kept only for contact state: faces in contact, area, the maximum (information) and the slip fraction at mu > 0.
   - v3.5.1 is not affected: it has no contact pairs, and no v3.5.1 script reads CPRESS.
3. **MF-J2: the first TC-01 net-ligament SCL lines.** The lines `TC01_net_ligament_hole_flank*` of `jfwd_post` ran partly inside the hole (extrapolated, min barycentric -0.20 / -0.34), and one was a hole-edge line. They are SUPERSEDED. `scripts/jfwd_ligament.py` takes the ligament average on the hole plane (ASME VIII-2 Table 5.6 typical ligament: Pm through the section, Pb across the width) and the 80 full-wall stations.
4. **Sharp-corner penalty contact is not unique (numerical, not physics; lead 11:41Z).**
   - Where: the TC-01 bore-side hole-edge corner is sharp in the CAD. Its penalty contact (about 10 GPa at about 0.02 mm penetration) reaches different equilibria depending on the predecessor state and the increment path.
   - Size: the soak screw force spans 5559-7383 N at SOAK over four histories (js5, (a), (a'), (a'')), with the prescribed boundary displacements identical.
   - Ruling: until a history-robust model exists, the sharp-edge soak quantities are the worst over the solved histories per state and per quantity (10A.4).
   - What would remove it: the R0.2 break at the bore-side hole edge that the drawing now calls up, modelled in (b2) / (b1) (10A.5).
5. **ccx zero-size increment.** After converging js5 step 5 (SOAK), ccx appended a zero-size increment (contact pressure ratio -0.73, converged at 1e-6). The .frd then holds two frames for that step. Every J-FWD post takes the LAST frame per step (`read_frd_steps`).

### 7.4 Other notes

- **Lever geometry in the posts.** For lever=r3 runs, `post_f1.load_model` now switches the GM-01 / GM-02 geometry to rev 3 exactly as `run_f1` does (07:33Z). Before that, the first post of pose_stop045_v352r3R2 rebuilt the rev-1 levers and stopped with an error, so no wrong number was written.
- **NZ-06 foil mass.** The v3.5.2 runs carry the interim N-F2 foil as a mass item of 0.303 g on NZ-03. The N-F2b foil is 0.195 g [DERIVED]. The 0.11 g difference has no effect at the published decimals.
- **TC-09 mesh level.** gmsh fails on the v3.5.2 TC-09 at level 2, so the pose and L2 runs mesh it at level 1.8 (`run_f1` COARSE_FALLBACK).
  - That mesh samples the TC-09 aft pressure boundary with only two one-sided faces. They are the source of the OP-moment residue (7.5).
- **Frames.** The pose runs (LC3, GS / TD / LC6) post in the pose frame. The engine-frame predicates of the matrix (J-FWD region z >= 97.5, the TC-02 / TC-03 seat region) were checked by hand on the R3 pose posts (section 3A notes).
- **lc1v352 (information only).** It maps the v3.5.1 merged S-AX field `L1_thv351_TB1GC_cad351` onto the v3.5.2 model and has no sax= option. Its matrix column is labelled 'LC1 merged v351 map (info)'. It is not the v3.5.2 NF2b perfect-contact bound. The docstring of `repost_5b_v352.py` said that it was; that line was corrected at 13:42Z.

### 7.5 OP-moment residue of the pressure faces (MF observation, ACCEPTED lead 22:24:34Z; section 9B.3)

- **Finding** [DERIVED on SIM]: the OP unit step of every v3.5.2 model carries a moment about the gimbal pivot. A closed cavity with an axisymmetric exit has none.
  - R3 pose runs and hot-bound bases (TC-09 at level 1.8): Q [304-307, 2,298] N mm/MPa. Of this, a couple of about 1.56 N m/MPa comes from two TC-09 aft-boundary faces (elements 24664 / 23610) loaded at p/Pc 0.75.
  - L1 global runs (LC1, LC2, FA-1, TB): 0.72 N m/MPa.
  - v3.5.1 L1 carried 0.27 N m/MPa.
  - The pressure.json residual correction balances the lateral force but not the moment.
- **Path.** The rods are the only moment path about the gimbal axes, so the residue appears as a rod-force pair: OP rods +29.7 to +47.1 / +21.3 to +38.5 N/MPa over the 17 R3 poses, against +12.4 to +18.2 / +4.3 to +10.0 N/MPa with the two faces at p/Pc 1.0 (`icd_momentfree_v352.json`).
- **Where it shows** [DERIVED]:
  - F2 rod forces: TD +75-112 N, LC2F +135-200 N (9B.2).
  - Hole loads: the datasheet carries governing values, the larger of as found and estimate (lead 22:54:03Z; section 8).
  - The GM-01 FA1Q-S cells: about 204 N of ROD_1 residue at FA1S.
  - The hot-bound bases: about 86 / 66 N of rod force at Pc_max.
- **Status.** The as-found cells stand; nothing is proven conservative for every part. Route: make the OP load moment-free, then re-solve the 17 R3 poses, shared with the TC-04 route. Its status: "not schedulable under the disk rules as costed; the lead decides after js5b" (lead 22:24:34Z).

## 8. Mounting interface to the airframe (16 x M5) and the datasheet mounting data (RM2-11 folded)

Files: `results/v352/engine_mount_data_v352.json` e5f41bde43a00ba4, `results/v352/tables/engine_mount_data_v352.md` ec986ff940cfed33, script `scripts/icd_export_v352.py` 15a3d8e6be6d4ea1 (log `runs/icd_export_v352_2310.log` af1c74a10609b3b2). Moment-free estimate and governing values: `results/v352/icd_momentfree_v352.json` 785b4e48f407ddfb, `results/v352/tables/icd_momentfree_v352.md` cff5fecafb87c313, script `scripts/icd_momentfree_v352.py` cf90b594ff7ac9f5 (log `runs/icd_momentfree_v352_2305.log` 96c58ee9b0bd2a7a).
- Method: as v3.5.1. Each run's solved unit-step reactions at the 16 hole node sets (ccx RF totals in `f1.dat`) are re-combined with every sub-case of the posted cases [SIM].
- The script reads only `model.json` (the step list) and `f1.dat`. It does not rebuild the FE model.
- Forces are those the engine module applies on the airframe. Radial + is pull-out; shear = hypot(tangential, axial) in the radial screw.
- The v3.5.1 per-hole values and maxima are reproduced exactly: LC1 75 N, FA1S 554 N, FA1T 643 N, LC3 889 N rigid / 453 N compliant, GS 808 N.
- **v3.5.2 datasheet rows are governing values [DERIVED]** (lead 22:54:03Z). The OP unit step of the v3.5.2 models carries a non-physical moment about the pivot (section 9B.3, an MF observation). Each v3.5.2 hole-load row is therefore the larger of:
  - the as-found value [SIM]; and
  - the moment-free estimate [DERIVED, superposition; transfer ASSUMED].

  The larger value is taken per hole and per component (shear, axial, tangential, pull-out, push-in, resultant), and then enveloped with the carried v3.5.1 compliant rows. The table file shows both values; '!' marks a value the estimate governs by 0.5 N or more. The estimate used:
  - L1 global cases (LC1, LC2, FA-1): OP moment zero, transferred through pose_neutral_v352r3R3's EA steps [ASSUMED];
  - R3 pose cases (LC3, F2): both estimates, the two TC-09 faces at p/Pc 1.0 and OP moment zero. At 114 hole values the OP-zero value is the largest, by up to 18 N (LC2F AF_GM09_0).

  The ring resultants follow the same rule. The carried v3.5.1 compliant rows are not re-estimated: they come from the v3.5.1 model, whose L1 residue is 0.27 N m/MPa.

### 8.1 Header of the datasheet mounting rows (RM2-11)

- **Included mass.** The forces include the FE model mass:
  - v3.5.1 model (c71): **4.103 kg** (engine 2.886, ring 0.217, fixed 0.971, horns 0.029 kg);
  - v3.5.2 model: **4.033 kg** for L1 (engine 2.829 kg) and **4.030 kg** for the rev-3 R3 pose model (engine 2.827 kg); ring 0.217, fixed 0.957, horns 0.029 kg [DERIVED, `runs/<run>/mass.json`].
- **Excluded mass.** The forces exclude **1.31 kg** of airframe-wall equipment: the massprops wet fixed group minus the model's fixed group, 2.2805 - 0.9706 = 1.3099 kg (v3.5.1) and 2.2669 - 0.9570 = 1.3099 kg (v3.5.2). Its inertia goes into the airframe wall directly, not through these holes.
- **Sub-cases.**
  - FA1Q / FA1D / FA1U / FA1S are pressure only, with no inertia.
  - The LC2F envelope (908 N) is its thrust-only sub-case. GZ 0 bounds it, because inertia opposes thrust.
- **Rigid against compliant airframe.** The rigid airframe bounds the maximum hole load (LC3 889 N rigid against 453 N compliant). It does not bound every hole, so the per-hole datasheet rows are the **envelope of the rigid and the compliant airframe** (k_af 2e3 / 2e4 / 2e4 N/mm, ASSUMED).
  - Compliant coverage: LC1 at B1_21.65 and LC3 at stop045 only. Every other case and pose is rigid only.
  - Holes where the compliant value is higher (v3.5.1 model, max screw shear, N) [SIM]:

  | case | hole | compliant | rigid envelope |
  |---|---|---|---|
  | LC3 (compliant: stop045 only) | AF_GM09_1 | 102 | 20 |
  | | AF_GM09_2 | 72 | 8 |
  | | AF_GM09_5 | 36 | 10 |
  | | AF_GM09_6 | 140 | 27 |
  | | AF_GM10_7 | 162 | 124 |
  | LC1 | AF_GM10_0 / _3 / _4 / _7 | 47 / 48 / 45 / 47 | 36 / 37 / 37 / 36 |
  | | AF_GM09_1 | 5 | 3 |

  These reproduce RM2-11 (REV-MECH-2 rounds AF_GM09_2 and _5 to 9 N rigid). Where the compliant value is higher, its pull-out and axial components are in the table file.
- **v3.5.2.** There is no compliant v3.5.2 run. The v3.5.2 datasheet rows are therefore the envelope of the v3.5.2 governing rigid rows and the v3.5.1 compliant rows. The compliant rows are carried and marked c351; their model mass is 4.103 kg against 4.030 kg, and their OP net 202.925 against 202.50 N/MPa. With the governing values the compliant rows still govern LC1 at AF_GM09_1 (5 against 3 N) and AF_GM10_0 / _3 / _4 / _7 (47 / 48 / 45 / 47 N against 37-38 N rigid governing) and LC3 at AF_GM09_1 / _2 / _5 / _6 and AF_GM10_7.

### 8.2 Per-hole rows and ring resultants

The table file is in this order:
1. the v3.5.2 **datasheet** per-hole values (governing, with '!');
2. the v3.5.2 as-found per-hole envelope;
3. the v3.5.1 per-hole envelope (rigid u compliant), which restates `tables/engine_mount_data_v351.md` with RM2-11;
4. the OP-moment residue section (as found / estimates / governing, per case and per hole);
5. the ring resultants of both models, with the v3.5.2 governing rows;
6. the extras (8.3).

Maxima per case, v3.5.2 model, rigid. Governing [DERIVED], as found [SIM], estimates [DERIVED; transfer ASSUMED]:

| case | datasheet: governing max screw shear N (hole) | as found (hole) | estimate: moment-free; OP moment zero | max pull-out N, governing (as found) | v3.5.1 c71 max shear N (hole) | source runs |
|---|---|---|---|---|---|---|
| LC1 (GVLO + GVHI, 4 burn states) | **76 !** (AF_GM09_0) | 70 (AF_GM09_4) | n/a; 76 | 20 ! (19) | 75 (AF_GM09_4); compliant 48 (AF_GM10_3) | lc1v352g, lc1v352h |
| LC2 (GVLO + GVHI) | **150 !** (AF_GM09_0) | 139 (AF_GM09_4) | n/a; 150 | 33 ! (31) | no v3.5.1 row | lc1v352g, lc1v352h |
| FA1Q | **348 !** (AF_GM09_0) | 326 (AF_GM09_0) | n/a; 348 | 64 ! (60) | 330 (AF_GM09_0) | fa1v352n (NF2b A1_22.2) |
| FA1D | **448 !** (AF_GM09_0) | 420 (AF_GM09_0) | n/a; 448 | 82 ! (77) | no v3.5.1 row | fa1v352n |
| FA1U | **544 !** (AF_GM09_0) | 510 (AF_GM09_0) | n/a; 544 | 99 ! (93) | no v3.5.1 row | fa1v352n |
| FA1S | **559 !** (AF_GM09_0) | 523 (AF_GM09_0) | n/a; 559 | 102 ! (96) | 554 (AF_GM09_0) | fa1v352n |
| FA1T | **657 !** (AF_GM09_0) | 635 (AF_GM09_0) | n/a; 657 | 120 ! (116) | 643 (AF_GM09_0) | fa1v352n |
| LC3, 8 stop poses at R3 | **890** (AF_GM10_2, stop180) | 890 | 890; 890 | 296 (296) | 889 (AF_GM10_5, stop180); compliant 453 (stop045) | pose_stopXXX_v352r3R3 |
| F2 GS, 9 cone poses at R3 | **808** (AF_GM10_2, beta-) | 808 | 808; 808 | 108 (108) | 808 (AF_GM10_2, beta-) | pose_<cone>_v352r3R3 |
| F2 TD at Pc 0 | **169** (AF_GM10_2, combined135) | 169 | 169; 169 | 89 (89) | 137 (AF_GM10_2, combined135) | as GS |
| F2 TD at Pc max | **306** (AF_GM10_2, combined135) | 306 | 207; 186 | 121 (121) | 181 (AF_GM09_7, alpha+) | as GS |
| F2 LC6 | **80** (AF_GM09_7, beta+) | 80 | 80; 80 | 44 (44) | 81 (AF_GM09_4, alpha+) | as GS |
| F2 LC2F (thrust-only sub-case) | **288** (AF_GM10_2, combined135) | 288 | 184; 197 | 75 ! (74) | 190 (AF_GM09_4, alpha+) | as GS |

- The estimate governs every L1 case maximum, at AF_GM09_0, by 3.5-7.8 %. The as-found values of those rows are not conservative [DERIVED].
- With the residue removed, the v3.5.2 L1 maxima sit near the v3.5.1 values: FA1S 559 against 554 N, FA1T 657 against 643 N, LC1 76 against 75 N. The v3.5.1 L1 residue is small (rods -0.66 / -4.92 N/MPa), so the as-found v3.5.2 drop (FA1S 554 -> 523 N) is not borne out once the residue is removed [DERIVED].
- On the R3 cases the as-found value governs every case maximum. The estimate governs at other holes: TD at Pc max AF_GM09_0 186 against 158 N; LC2F AF_GM09_0 197 against 143 N.
- The hot-bound bases' OP residue (+86 / +66 N of rod force at Pc_max, section 9B.3) does not enter these rows: the LC3 / F2 hole loads are the cold pose-run values, and no hot bound is formed on hole loads. In the pose runs themselves the LC3 rods are prescribed (fb_run re-solved, 609 N) and the GS rods sit at the prescribed corners, so the OP residue there is replaced by the prescribed rods; in TD / LC6 / LC2F the rods react inertia and the residue stays in the as-found rows, which is why the estimates differ there [DERIVED].
- Per case, the number of hole values the estimate governs (of 96) is in the table file. In all, 512 of the 1,248 rigid hole values are governed by the estimate, 495 after the compliant envelope.
- Ring resultants: the as-found total moment of the L1 cases is mostly the residue couple, e.g. FA1S [11.53, 8.01, 0.90] N m as found against [0.41, 0.14, 0.54] N m with the OP moment zero. The governing rows keep the larger, as-found value.
  - The estimate also moves axial load between the rings, because the rods are nearly axial: FA1S GM-09 ring Fz 1,853 -> 1,976 N and GM-10 1,205 -> 1,081 N, total 3,059 -> 3,057 N.
  - The governing rows keep the larger value of each component.

### 8.3 Datasheet extras (8.1 of v3.5.1, corrected)

The table file carries three further tables:
- **K at the 8 stop poses, v3.5.1 model**, re-stated with r_eff per servo and pose. Coupled and diagonal values are labelled (RM2-05, section 9). These are the v3.5.1-model F3.
- **K at the 8 stop poses, v3.5.2 R3 model.** These are the stop rows of the REV-GNC-7 table: `results/v352/k_table_r3_v352.json` f3c7cfbcfb98bcd7, `results/v352/tables/k_table_r3_v352.md` ca3193489b7ca091. All 17 R3 poses are posted and ACCEPTED (lead 18:40:44Z).
  - Range over the 17 poses, coupled, N m/rad [SIM + DERIVED]:
    - K_alpha FE 7,294 (stop000) to 9,337 (stop180); with k_s 58: 1,150 (neutral) to 1,426 (stop000); with k_s 174: 2,697 to 3,076;
    - K_beta FE 3,972 (stop180) to 7,172 (stop000); with k_s 58: 791 to 1,799; with k_s 174: 1,697 to 3,594.
  - GNC sets its K band from the full R3 table, not from stop045 (lead 17:33:40Z).
- **The first engine-mount modes**, with the loop-relevant rocking pair quoted with the servo inertia J (RM2-07, section 9A):
  - k_s 58: 16.72 / 17.15 Hz;
  - k_s 174: 24.49 / 25.95 Hz;
  - 14.9-29.0 Hz over the J range at neutral.

  The datasheet does not present 21-33 Hz as the loop-relevant pair. The RM2-06 re-solve (`modal_v351ca2c_c71`, section 9A) moves modes 1-6 by at most 0.004 %, so the mode table stands.

## 9. Gimbal stiffness (F3), re-stated with the servo in series per servo and pose (RM2-05)

Files: `results/k_stop_c71_v352.json`, `results/k_cone_c71_v352.json`, `results/k_stop045_compliant_c71_v352.json`, `results/k_range_v352.json`, `tables/k_range_v352.md`. The v3.5.1 files `k_stop_c71`, `k_cone_c71`, `k_range_v351` and `tables/k_range_v351.md` are superseded for every with-servo value. Their FE (rigid-servo) values are unchanged.

**What was wrong in v3.5.1 (RM2-05, confirmed):** `post_k` used the neutral lever radius r_h 11.139 mm at every pose (lines 103 and 109). The effective radius of servo i at a pose is r_eff,i = |((H_i - C_i) x e_i) . e_t,i|. It is 7.88-11.14 mm over the 17 poses. The neutral pose is unchanged.

**Method [SIM / DERIVED].**
- FE: unit rod-pair steps EAX / EAY on asm v1.2 (the CAD v3.5.1 c71 pose runs) with the servo output rigid. The 17-pose table below is therefore the F3 of the v3.5.1 model. My draft assumed the v3.5.2 model gives the same K. **The stop045 check refutes that** (see 'v3.5.2 model check' below).
- Servo in series: C = C_FE + A^-T diag(r_eff,i^2 / k_s) A^-1, with k_s 58 / 174 N m/rad per servo [ASSUMED, TO-VERIFY B-TVC]. The two rods make the restraint statically determinate, so this is exact.
- Two values are given per axis:
  - **coupled** = 1 / C_jj: the other axis is moment-free. This is what a single-axis EAX / EAY load measures.
  - **diagonal** = (C^-1)_jj: the other axis is held at zero rotation.
- The scalar r_eff form that REV-MECH-2 (f2) uses is reproduced exactly.

| group (rigid airframe unless stated) | r_eff mm | K_alpha FE coupled / diag | K_alpha +k_s 58 coupled / diag | K_alpha +k_s 174 coupled / diag | K_beta FE coupled / diag | K_beta +k_s 58 coupled / diag | K_beta +k_s 174 coupled / diag |
|---|---|---|---|---|---|---|---|
| 8 stop poses (8 deg) | 7.88-11.10 | 6400-8577 / 6401-8578 | 1169-1388 / 1173-1476 | 2626-2949 / 2698-2985 | 3888-6570 / 3888-6571 | 787-1759 / 787-1759 | 1681-3436 / 1681-3436 |
| 9 range-cone poses (7 deg) incl. neutral | 8.86-11.14 | 6430-8364 / 6430-8364 | 1129-1299 / 1129-1332 | 2586-2880 / 2586-2880 | 4082-6380 / 4082-6380 | 821-1597 / 821-1597 | 1756-3193 / 1756-3193 |
| stop045, compliant airframe (k_af ASSUMED) | 7.88 / 11.07 | 5609 / 5613 | 1286 / 1420 | 2646 / 2772 | 5520 / 5524 | 1477 / 1630 | 2886 / 3024 |
| **all 17 poses** | 7.88-11.14 | **6400-8577** | **1129-1388 / 1129-1476** | **2586-2949 / 2586-2985** | **3888-6570** | **787-1759 / 787-1759** | **1681-3436 / 1681-3436** |
| superseded v3.5.1 (r_h 11.139 at every pose), both axes | - | - | 686-1364 (k_s 58) | 1522-2891 (k_s 174) | - | - | - |

**v3.5.2 model check at stop045 [SIM; post_k on the rev-3 pose runs; `results/k_stop045_v352r3R3_check.json`, `results/k_stop045_v352r3R2_check.json`].**

| stop045 (rigid airframe) | K_alpha FE coupled | K_beta FE coupled | +k_s 58 coupled alpha / beta | +k_s 174 coupled alpha / beta |
|---|---|---|---|---|
| c71: CAD v3.5.1, asm v1.2, TB1 'faces' (table above) | 6531 | 6348 | 1329 / 1530 | 2834 / 3097 |
| v3.5.2 rev 3, asm v1.3 (TB1 'thread' + tiex), lever mesh R2 | 7413 | 6886 | 1362 / 1559 | 2989 / 3220 |
| v3.5.2 rev 3, lever mesh R3 | 7403 | 6881 | 1362 / 1559 | 2987 / 3219 |
| change, R3 vs c71 | +13.4 % | +8.4 % | +2.5 % / +1.9 % | +5.4 % / +3.9 % |

- r_eff (7.88 / 11.07 mm) and the rods-only K (30587 / 38935 N m/rad) are the same in both models. The change is in the structure: its compliance is 15 % lower about alpha and 9 % lower about beta.
- R2 and R3 agree within 0.2 %, so the lever mesh is not the cause.
- I have not isolated the cause. The candidates are the asm v1.3 interface model (TB1 'thread' ties and tiex, RM2-13 and section 2.2), the TC-09 mesh level (1.8 vs 2.0) and the CAD change itself. The runs that would separate them (pose_stop045_v352L1, v352L1x, v352) no longer hold fields.
- Consequence: on the v3.5.2 model, K at stop045 is 8-13 % higher with the servo rigid and 2-6 % higher with the servo in series. The 17-pose table stands as the v3.5.1-model F3. It is not the v3.5.2 F3.
- **The v3.5.2 F3 is the R3 pose table** (REV-GNC-7 input, lead 17:33:40Z): `results/v352/k_table_r3_v352.json` f3c7cfbcfb98bcd7, `results/v352/tables/k_table_r3_v352.md` ca3193489b7ca091 [SIM + DERIVED; k_s ASSUMED]. All 17 R3 poses are posted with post_k (r_eff per servo and pose) and ACCEPTED (lead 18:40:44Z; stop045 accepted without a re-solve, its mirror stop315 corroborating). The table carries each pose's own values and its fraction of the stop045 delta.
  - Range over the 17 poses, coupled (diagonal where it differs), N m/rad:

  | axis | FE (servo rigid) | + k_s 58 | + k_s 174 |
  |---|---|---|---|
  | alpha | 7,294 (stop000) - 9,337 (stop180) | 1,150 (neutral) - 1,426 (stop000); diagonal to 1,521 (stop315) | 2,697 (neutral) - 3,076 (stop000); diagonal to 3,166 (stop315) |
  | beta | 3,972 (stop180) - 7,172 (stop000) | 791 (stop180) - 1,799 (stop000) | 1,697 (stop180) - 3,594 (stop000) |

  - Neutral, R3 against v3.5.1: K_alpha FE 8,246 against 7,284 (+13.2 %), K_beta FE 5,764 against 5,370 (+7.3 %); with the servo 1,150 / 2,697 (alpha) and 1,085 / 2,364 (beta) against 1,129 / 2,586 and 1,070 / 2,295.
  - Cone poses stiffen more than stop045 did: combined045 FE coupled alpha +14.4 % against +13.35 %. Four poses have a fraction of the stop045 delta above 1 (stop000 1.208, beta+ 1.201, combined045 1.081, combined315 1.077) and are ACCEPTED ABOVE THE ORIGINAL BAND (lead 18:40:44Z). The fraction follows the sign of beta (0.17-1.208). GNC sets its K band from the full R3 table, not from stop045 (lead 17:33:40Z).
- The V5c comparison below is on the v3.5.1 neutral pose; the identified bearing cause is a v3.5.1-model statement. On the R3 model the neutral FE K is a further +13.2 % (alpha) / +7.3 % (beta) above v3.5.1, so the excess over V5c grows by those factors [DERIVED]; not re-attributed.

- Neutral: K_alpha 7284, K_beta 5370 N m/rad with the servo rigid. With the servo: 1129 / 2586 (alpha) and 1070 / 2295 (beta) N m/rad, unchanged from v3.5.1.
- Per-pose rows (r_eff of each servo, coupled and diagonal values, scalar form) are in `tables/k_range_v352.md`. Beside them: the V5c comparison (Mechanical SIM, `gimbal_k_summary_V5c_v1.json` 82a737caa138259a) and the superseded r_h values.
- Off-centre, the servo-in-series K is higher than published in v3.5.1, because r_eff < r_h there (servo compliance r^2 / k_s). On both axes it is 787-1759 N m/rad at k_s 58 and 1681-3436 at k_s 174. This reproduces REV-MECH-2 (f2) and confirms GNC rev4b's finding of a low servo factor off-centre.

**FE neutral K against V5c: the beta structure excess (CHANGELOG 234 (5)).** Script `scripts/k_beta_cause.py`, results `results/v352/k_beta_cause.json` [DERIVED, no model change].
- V5c models the bearings as 608 ball bearings: point contact at a 62.5 N load point, 18.2 / 18.6 kN/mm including the pin. Those bearings hold 17.0 % of the V5c beta strain energy (inner 8.6 %, outer 8.4 %) and 0 % of alpha.
- The FE has HK0808 needle cups at the Palmgren line-contact stiffness at 500 N: 128.3 / 149.9 kN/mm.
- Re-weighting V5c's beta compliance with the needle stiffness gives K_beta 5073 N m/rad (+17 %). That explains 72 % of the K_beta excess and leaves the beta structure +4.7 % above V5c (was +26.6 %).
- The alpha excess (+11.3 %) is in the common structure (geometry v3.3 -> v3.5.1) and is not explained further.
- The inner-axis path (needle cups, collar, ring) is therefore the identified cause of most of the beta excess. Pins and seats are rigid in the FE. I did not change the model: the bearing stiffness basis (HK0808 line contact at the operating load) is the documented one.

## 9A. Modal and load-path periods (RM2-06, RM2-07 folded)

The v3.5.1 modal (coarsened all-L2 model, `modal_v351ca2b_c71`, 83,173 nodes, 60 modes to 5130 Hz) stays the basis of the mode list. Two corrections apply.

**RM2-07: the loop-relevant rocking pair is quoted with the servo inertia J and its basis.** Script `scripts/rm207_rocking.py`, results `results/v352/rocking_servo_J_v352.json` [DERIVED from SIM modal + SIM K].
- Inputs: k_s 58 / 174 N m/rad ASSUMED (TO-VERIFY B-TVC). J = servo rotor + gear train at the output shaft, ADDED to the pivot inertia through the kinematic factor g = 23.04 at neutral (CHANGELOG 227 (2)). J_nom 1.6e-3 kg m2, range 0.76-2.7e-3 [ASSUMED, GNC SB-2292SG datasheet-derived, TO-VERIFY B-TVC-1].

| servo | inner axis (beta) f, J nominal | outer axis (alpha) f, J nominal | over J 0.76-2.7e-3 (both axes) | J-free (v3.5.1 '21-33 Hz') |
|---|---|---|---|---|
| k_s 58 N m/rad | **16.72 Hz** | **17.15 Hz** | 14.86-19.19 Hz | 21.35 / 21.86 Hz |
| k_s 174 N m/rad | **24.49 Hz** | **25.95 Hz** | 21.76-29.04 Hz | 31.27 / 33.07 Hz |

- These reproduce REV-MECH-2's 16.7 / 17.2 Hz (k_s 58) and 24.5 / 26.0 Hz (k_s 174), quoted in CHANGELOG 234 (6), to within 0.05 Hz.
- Neutral pose over the whole k_s and J range: **14.9-29.0 Hz**.
- A lumped 2-DOF over the 17 poses (r_eff per servo and pose, section 9):
  - k_s 58: 15.2-19.1 Hz at J nominal (18.3-29.8 Hz J-free);
  - k_s 174: 22.2-27.2 Hz at J nominal (26.8-40.3 Hz J-free);
  - over the J range: 13.8-31.1 Hz.
- **The v3.5.1 '21-33 Hz with the servo in series' is not the loop-relevant pair.** It omits J and is withdrawn.
- The rigid-servo FE pair 51.4 / 59.4 Hz (47.8 / 55.5 Hz at the production K) is unchanged.

**RM2-06: TC-01 wetted-face set on the level-2 modal mesh, and the share vectors.**
- What was wrong: on the all-L2 mesh the TC-01 wetted-face classification differs from L1. The OP net force was 241.1 N/MPa against 201.9 on the production model, so the static OP step and the load-path shares were biased.
- Fix (`asm_build` option l1loads=TC-01): the L1 TC-01 face loads are mapped to the L2 mesh as nodal forces. Force is exact; moment is within about 2 N mm/MPa.
- Dry build (no solve): TC-01 OP resultant [1.28, 1.93, 351.84] N/MPa = the L1 value (the L2 DLOAD gave 391.01); OP net before the closed-vessel correction 201.94 N/MPa, equal to the pose runs.
- Re-solve: `modal_v351ca2c_c71` (OP, PM, FREQ60 on the same L2 mesh, CAD v3.5.1) ran 16:42:20-16:50:06Z, rc 0 [SIM].
  - Method M2: the lead's 16:20Z fallback, accepted 16:53Z. The M3 check (a) failed on an RBE3 difference, isolated to the 02:19:48Z samples CAD fix, which the lead accepted as intended.
  - Files: `results/modal_modal_v351ca2c_c71.json` 619272cd3b66072b; the comparison `results/v352/modal_ca2c_vs_ca2b_v352.json` 1bdaf41b4611094c (table `tables/modal_ca2c_vs_ca2b_v352.md` 53573d96492efed3); the FA-1 column sensitivity `results/v352/fa1_band_sensitivity_modal_v351ca2c_c71.json` 5d1f3e2e876ca6e8 (table 0e0a0fa5ea8bb3c4).
- Results [SIM; shares and MS DERIVED]:
  - OP resultant 241.10 -> 201.94 N/MPa, equal to the pose runs. The share of the OP compliance captured by the 60 modes went from 0.155 to 0.148.
  - Modes 1-44 (to 3.9 kHz) move by at most 0.102 %, MAC 0.9944 or more. The rocking pair (51.42 / 59.42 Hz) and modes 3-6 are unchanged to 0.004 %.
  - The 4.0-5.2 kHz cluster re-orders (largest same-index change +3.5 %, mode 52). In that cluster the forward-equipment (BLEED) modes move up, because the FD-01 patch went from 17 to 24 faces.
  - ca2c supersedes ca2b for RM2-06 only. The mode list of 9A stands.
- Share vectors at TC-01, ca2b -> ca2c (slow share at f x1.00; MS_y / MS_u at slow x1.00 and at f x0.85):

  | point | slow share x1.00 | MS_y / MS_u at x1.00 | MS_y / MS_u at f x0.85 |
  |---|---|---|---|
  | J-FWD (FA-1 governing) | +0.0178 -> +0.0137 | +0.237 / +0.223 -> **+0.240 / +0.225** | +0.231 / +0.218 -> **+0.233 / +0.220** |
  | LC1 governing | +0.0349 -> +0.0302 | +0.224 / +0.213 -> **+0.228 / +0.216** | +0.216 / +0.206 -> **+0.219 / +0.209** |

  - The 11 % OP bias on TC-01 (391.0 against 351.8 N/MPa axial) raised the slow share. Removing it raises the margins by 0.002-0.004, so the published v3.5.1 values were on the conservative side.
  - Distance to break-even: the slow share would reach the break-even value (yield 0.40, ultimate 0.485) only if every mode frequency were scaled by 0.464 (J-FWD) or 0.449 (LC1 governing). Within 2 mm of each point, the slow share at f x1.00 is +0.012 to +0.020 (J-FWD) and +0.030 to +0.035 (LC1 governing).
  - Consumers: the Combustion REV-COMB-4 fold reads the modal JSON and the share vectors.

## 9B. F2: S-3D gimbal strength on CAD v3.5.2 (9 range-cone poses, rev-3 levers at R3; `results/v352/s3d_summary_v352.json` afd39c752fc46d3c, `results/v352/tables/s3d_{part_margins,rods,connectors}_v352.md`, `scripts/s3d_summary_v352.py` 3c010f880bfb11b8, `scripts/post_s3d.py` 2405db11ce62f2f8)

All values are SIM on CAD v3.5.2 (asm v1.3, rev-3 levers at R3) unless tagged. The envelopes, the p = 1 cells and the hot values are DERIVED. None of it is physical approval.

**Model and cases.**
- Model: the F1 model on CAD v3.5.2 at the 9 range-cone poses: neutral, alpha +/-7, beta +/-7 and the four combined poses on the 7 deg cone (`pose_<cone>_v352r3R3`).
  - Engine pressure parts at mesh level 2 (TC-09 at 1.8); gimbal parts at L1; both lever roots at R3 (section 6.2).
  - Unit steps OP, GX / GY / GZ, EAX / EAY; cold; allowables at the B1_21.65 node temperatures.
- Cases (the S-3D v1.1 set on the current loads, as in v3.5.1):
  - **GS**: both servos at stall, rods at +/-F_d (441 N neutral, 552 N on the cone; mechanical.json v2.1, DERIVED), realised by the engine angular acceleration. Added: Pc_max 2.501 MPa, flight inertia (0.61 g lateral, 8 directions; axial {0, 4.04 g}) and the hose 31.2 N.
  - **TD**: touchdown with the servos holding: OP {0, Pc_max}, 6.29 g lateral, 5.43 g axial, 79.28 rad/s2 (gnc.json v3.1, SIM). Rods from statics.
  - **LC6**: 10 g axial + 3 g lateral (ASSUMED envelope), no thrust.
  - **LC2F**: stuck-pintle thrust 907.7 N + flight inertia, SF 1.0 / 1.5. The case stays as published (234 (2)); gimbal and mount parts only.
  - SF 1.5 / 2.0 otherwise.
- SR (runaway onto the 8 deg stop) = F1 LC3 (section 6). FA1T comes from fa1v352n (A1_22.2).
- Every cell carries the all-node minimum beside the regular value (234 (4)).

### 9B.1 Per-part minimum margins, yield / ultimate (pose; all-node rows give the node class and distance in mm) [SIM; GM-01 / GM-02 GS and SR cells from the accepted lever-root table, section 6.2]

| part | set | GS y / u (pose) | TD y / u (pose) | LC6 y / u | LC2F y / u (SF 1.0 / 1.5) | SR = F1 LC3 y / u (pose) | FA1T y / u |
|---|---|---|---|---|---|---|---|
| GM-01 | regular | +0.648 / +0.420 (alpha+) | +4.666 / +3.882 (alpha+) | +42.346 / +36.351 | +7.169 / +5.257 | +0.534 / +0.322 (stop315) | +4.017 / +4.765 |
| GM-01 | all | +0.648 / +0.420 (alpha+) | +2.660 / +2.154 (alpha-, RE 0.21) | +42.346 / +36.351 | +2.551 / +1.720 (RE 0.21) | +0.534 / +0.322 (stop315) | +0.777 / +1.042 (RE 0.21) |
| GM-02 | regular | +0.591 / +0.371 (alpha-, p = 1) | +5.537 / +4.633 (alpha-) | +57.337 / +49.269 | +8.552 / +6.316 | +0.400 / +0.206 (stop045, p = 1) | +5.372 / +6.321 |
| GM-02 | all | +0.591 / +0.371 (alpha-, p = 1) | +3.643 / +3.001 (beta+, RE 0.10) | +57.337 / +49.269 | +3.585 / +2.512 (RE 0.10) | +0.400 / +0.206 (stop045, p = 1) | +2.105 / +2.568 (RE 0.14) |
| GM-03 | regular | +2.041 / +1.453 (alpha+) | +5.114 / +3.932 (beta+) | +12.187 / +9.639 | +8.891 / +6.093 | +1.310 / +0.864 (stop000) | +1.518 / +1.708 |
| GM-03 | all | +1.893 / +1.334 (alpha+, ID 0.0) | +4.793 / +3.674 (beta+, ID 0.0) | +11.646 / +9.202 (ID 0.0) | +8.795 / +6.024 (ID 0.0) | +1.227 / +0.796 (stop000, ID 0.0) | +1.353 / +1.531 (ID 0.0) |
| GM-16a | regular | +1.149 / +0.852 (combined225) | +5.354 / +4.475 (combined135) | +45.041 / +38.673 | +8.908 / +6.589 | +1.069 / +0.783 (stop090) | +12.799 / +14.854 |
| GM-16a | all | +0.568 / +0.351 (alpha-, RE 0.43) | +3.197 / +2.616 (combined135, RE 0.43) | +29.491 / +25.274 (RE 0.43) | +5.523 / +3.996 (RE 0.43) | +0.372 / +0.183 (stop315, RE 0.54) | +10.140 / +11.799 (RE 0.43) |
| GM-16b | regular | +1.158 / +0.859 (combined315) | +5.997 / +5.029 (combined225) | +59.812 / +51.402 | +11.075 / +8.249 | +1.036 / +0.755 (stop270) | > +99 |
| GM-16b | all | +0.531 / +0.319 (alpha-, RE 0.43) | +4.299 / +3.566 (combined225, RE 0.43) | +45.191 / +38.802 (RE 0.43) | +8.123 / +5.988 (RE 0.43) | +0.450 / +0.250 (stop045, RE 0.54) | > +99 (RE 0.43) |
| GM-08a | regular | +14.948 / +11.866 (combined315) | +20.940 / +16.700 (beta-) | +50.247 / +40.343 | +44.171 / +31.393 | +8.282 / +6.488 (stop000) | +12.553 / +13.579 |
| GM-08a | all | +12.101 / +9.569 (combined045, ID 0.0) | +15.110 / +11.997 (beta-, ID 0.0) | +37.240 / +29.850 (ID 0.0) | +32.080 / +22.722 (ID 0.0) | +5.528 / +4.266 (stop000, ID 0.0) | +10.455 / +11.322 (ID 0.0) |
| GM-08b | regular | +17.185 / +13.671 (alpha-) | +36.334 / +29.120 (alpha+) | +78.847 / +63.416 | +57.157 / +40.705 | +17.283 / +13.750 (stop315) | +14.596 / +15.777 |
| GM-08b | all | +10.525 / +8.298 (alpha-, ID 0.0) | +22.858 / +18.247 (alpha+, ID 0.0) | +49.715 / +39.914 (ID 0.0) | +35.973 / +25.514 (ID 0.0) | +10.694 / +8.434 (stop315, ID 0.0) | +8.839 / +9.584 (ID 0.0) |
| GM-09 | regular | +15.260 / +12.118 (alpha-) | +16.943 / +13.475 (beta+) | +55.464 / +44.553 | +47.392 / +33.703 | +6.454 / +5.014 (stop180) | +11.796 / +12.764 |
| GM-09 | all | +12.056 / +9.533 (alpha+, ID 0.0) | +14.319 / +11.359 (beta+, ID 0.0) | +42.664 / +34.226 (ID 0.0) | +35.853 / +25.428 (ID 0.0) | +5.134 / +3.948 (stop000, ID 0.0) | +9.410 / +10.198 (ID 0.0) |
| GM-10 | regular | +3.618 / +2.726 (combined135) | +14.128 / +11.205 (beta-) | +92.245 / +74.225 | +22.208 / +15.643 | +3.708 / +2.798 (stop180) | +30.304 / +32.673 |
| GM-10 | all | +3.618 / +2.726 (combined135) | +14.128 / +11.205 (beta-) | +76.758 / +61.732 (ID 0.0) | +22.208 / +15.643 | +3.708 / +2.798 (stop180) | +19.238 / +20.769 (ID 0.0) |
| GM-13 | regular | +2.910 / +2.154 (combined225) | +10.547 / +8.316 (combined135) | +70.281 / +56.506 | +16.963 / +11.881 | +2.749 / +2.025 (stop180) | +24.700 / +26.644 |
| GM-13 | all | +2.578 / +1.887 (combined225, ID 0.0) | +9.510 / +7.479 (combined135, ID 0.0) | +61.967 / +49.799 (ID 0.0) | +15.399 / +10.760 (ID 0.0) | +2.418 / +1.757 (stop180, ID 0.0) | +22.434 / +24.208 (ID 0.0) |
| GM-14 | regular | +3.211 / +2.398 (combined135) | +13.091 / +10.368 (combined225) | +91.508 / +73.631 | +23.265 / +16.401 | +3.168 / +2.363 (stop180) | > +99 |
| GM-14 | all | +2.509 / +1.831 (combined135, ID 0.0) | +10.565 / +8.330 (combined225, ID 0.0) | +77.419 / +62.264 (ID 0.0) | +18.968 / +13.319 (ID 0.0) | +2.434 / +1.771 (stop180, ID 0.0) | > +99 (ID 0.0) |
| TC-01 | regular | +2.034 / +1.462 (beta+) | +2.163 / +1.568 (beta+) | +41.100 / +33.171 | - | +2.112 / +1.526 (stop090) | - |
| TC-01 | all | +1.080 / +0.686 (combined045, ID 0.0) | +1.118 / +0.717 (combined315, ID 0.0) | +30.584 / +24.649 (ID 0.49) | - | +1.044 / +0.657 (stop090, ID 0.0) | - |

- **No F2 cell is negative.** The lowest cold F2 cells are at the lever roots (GS GM-02 +0.591 / +0.371, p = 1 bound; GM-01 +0.648 / +0.420) and at the GM-16a / GM-16b horns (all-node at a BREP re-entrant edge, RE 0.43 mm: +0.568 / +0.351 and +0.531 / +0.319). No sub-model replaces the RE class, so the all-node values are the matrix cells (234 (4)).
- **GS lever-root minimum per pose** (all-node = regular at every governing row; section 6.2; the hot value is the hot bound, with the p = 1 increment where ruled):

| pose | GM-01 cold MS y / u (vM MPa) | GM-01 hot | GM-02 cold MS y / u (vM MPa) | GM-02 hot |
|---|---|---|---|---|
| neutral | +1.330 / +1.008 (134.5) | +0.671 / +0.440 | +1.300 / +0.982 (136.2) | +0.790 / +0.542 |
| alpha+ | **+0.648 / +0.420** (190.2) | **+0.289 / +0.111** | +0.972 / +0.699 (158.9, p = 1) | +0.575 / +0.357 |
| alpha- | +1.135 / +0.840 (146.8) | +0.558 / +0.343 | **+0.591 / +0.371** (196.9, p = 1) | **+0.337 / +0.152** |
| beta+ | +0.724 / +0.485 (181.8) | +0.333 / +0.149 | +0.699 / +0.464 (184.4) | +0.410 / +0.215 |
| beta- | +1.140 / +0.844 (146.5) | +0.565 / +0.349 | +1.158 / +0.860 (145.2) | +0.696 / +0.462 |
| combined045 | +0.860 / +0.603 (168.5) | +0.410 / +0.215 | +0.675 / +0.443 (187.1) | +0.398 / +0.205 |
| combined135 | +1.345 / +1.020 (133.6) | +0.667 / +0.436 | +0.801 / +0.552 (174.0) | +0.472 / +0.269 |
| combined225 | +0.785 / +0.538 (175.6) | +0.365 / +0.176 | +1.305 / +0.986 (135.9) | +0.772 / +0.527 |
| combined315 | +0.677 / +0.445 (186.9) | +0.311 / +0.130 | +0.833 / +0.579 (171.0) | +0.494 / +0.288 |

- **F2 hot lower bound** (LC1 thermo-pressure base + the cone-pose GS + TD + LC6 increment; DERIVED, matrix column 'F2 hot bound'): lever roots GM-01 +0.289 / +0.111, GM-02 +0.337 / +0.152. The hot cone values are lower bounds on the GS-only hot margin (lead 20:44:07Z (1)).
  - Other gimbal parts: >= +0.524 / +0.313 (GM-16b, all-node RE 0.43).
  - Engine parts: section 3A (the matrix), including the part-wide singular-node bounds (section 4).
- **Change against v3.5.1** (v3.5.1 report section 9B, rev-1 levers):
  - GS lever roots: -0.223 / -0.330 (GM-02) and -0.209 / -0.319 (GM-01) -> +0.591 / +0.371 and +0.648 / +0.420.
  - F2 hot lever roots: -0.259 / -0.362 and -0.219 / -0.327 -> +0.337 / +0.152 and +0.289 / +0.111.
  - The other gimbal parts change by less than 0.15 in GS.
  - TD and LC2F margins fall for the horns and the outer-gimbal parts (regular, yield): TD GM-16a +13.662 -> +5.354, GM-16b +10.988 -> +5.997, GM-10 +24.304 -> +14.128, GM-13 +23.379 -> +10.547, GM-14 +21.857 -> +13.091; LC2F GM-16a > +99 -> +8.908, GM-10 +81.040 -> +22.208, GM-01 +8.871 -> +7.169. This follows from the higher rod forces of 9B.3.
  - The lever-root TD cells rise despite the higher rod forces (GM-01 +3.710 -> +4.666, GM-02 +3.961 -> +5.537, regular), because the rev-3 lever roots are stronger (section 6). GM-02 LC2F rises too (+7.605 -> +8.552).
  - All of these stay positive.
  - TC-01 (changed part, rev 5) GS regular rises from +0.805 / +0.465 to +2.034 / +1.462.

### 9B.2 Rod forces, engine angular acceleration and connector envelopes [SIM as found; estimates DERIVED]

The as-found values carry the OP-moment artefact of 9B.3 (MF observation, lead 22:24:34Z: the as-found cells stand). Beside each affected value, in brackets: the **moment-free statics estimate** (the two TC-09 aft-boundary faces at p/Pc 1.0, OP rods 12.5-17.3 / 4.5-9.3 N/MPa) and, after the semicolon, the value with the OP rod term set to zero (the physical statics: no OP moment about the pivot). Both are statics on the posted unit steps, not re-solves (`results/v352/rods_momentfree_v352.json` 5c328bca44a87375, `scripts/rods_momentfree_v352.py` 22e920b4f93b510d; the as-found recombination reproduces every posted maximum to 0.1 N). LC6 has no OP term and is unaffected.

| pose | GS rods N | GS engine ang. accel. rad/s2 as found (v3.5.1) [moment-free est.; OP term 0] | TD max rod abs N as found (v3.5.1) [moment-free est.; OP term 0] | LC6 max rod abs N (v3.5.1) | LC2F max rod abs N as found (v3.5.1) [moment-free est.; OP term 0] |
|---|---|---|---|---|---|
| neutral | +/-441 | 487-699 (570-612) [556-630; 584-602] | 163 (86) [111; 84] | 20 (15) | 155 (44) [63; 7] |
| alpha+ | +/-552 | 627-840 (689-751) [695-772; 706-743] | 169 (99) [111; 95] | 18 (13) | 144 (50) [58; 6] |
| alpha- | +/-552 | 632-837 (688-754) [695-769; 704-742] | 190 (87) [129; 98] | 25 (17) | 182 (42) [73; 9] |
| beta+ | +/-552 | 726-939 (717-847) [720-871; 731-841] | 155 (84) [110; 83] | 18 (13) | 141 (42) [59; 6] |
| beta- | +/-552 | 504-762 (598-746) [572-755; 599-744] | 193 (102) [130; 100] | 25 (17) | 186 (51) [74; 9] |
| combined045 | +/-552 | 702-911 (705-822) [710-843; 719-814] | 164 (85) [113; 86] | 21 (14) | 156 (41) [64; 7] |
| combined135 | +/-552 | 549-753 (634-731) [616-738; 641-728] | 209 (91) [141; 108] | 28 (19) | 202 (45) [79; 10] |
| combined225 | +/-552 | 543-756 (640-730) [611-739; 640-726] | 188 (110) [121; 105] | 20 (15) | 164 (54) [63; 7] |
| combined315 | +/-552 | 700-913 (705-821) [710-845; 721-815] | 153 (86) [109; 83] | 16 (13) | 136 (45) [57; 5] |
| **9 poses** | | **487-939** (570-847) [556-871; 584-841] | **153-209** (84-110) [109-141; 83-108] | 16-28 (13-19) | **136-202** (41-54) [57-79; 5-10] |

- The OP-moment artefact adds 75-112 N (TD, at Pc_max) and 135-200 N (LC2F, at 907.7 N thrust) to the more loaded rod of each pose (the whole OP rod term; 9B.3).
- v3.5.1's TD values (84-110 N) match the OP-term-zero values (83-108 N): its own OP residue was small at TD. Its LC2F rods (41-54 N) were mostly that residue (OP rods 9-12 N/MPa x 4.4 MPa).
- Part stresses and connector loads are not re-estimated: they would need a re-solve. The airframe-hole loads are estimated by superposition (9B.3); the estimate is the bracketed column below, and the datasheet value is the larger of the two (lead 22:54:03Z).

| case | inner cup max comp. N | inner washer N | outer cup N | outer washer N | max hole shear N (hole, pose) | [moment-free est.; OP term 0] max hole shear N (hole) |
|---|---|---|---|---|---|---|
| GS | 803 (v3.5.1 801) | 281 (280) | 801 (799) | 209 (216) | 808 (AF_GM10_2, beta-; v3.5.1 808) | [808; 808] (AF_GM10_2) |
| LC6 | 135 (137) | 112 (115) | 147 (146) | 91 (94) | 80 (AF_GM09_7, beta+; v3.5.1 81) | [80; 80] (AF_GM09_7) |
| LC2F | 339 (438) | 86 (41) | 334 (435) | 160 (135) | 288 (AF_GM10_2, combined135; v3.5.1 190) | [184 (AF_GM09_4); 197 (AF_GM09_0)] |

- Every rod force stays below the 609 N stall limit (TD maximum 209 N): the servos hold [SIM against the DERIVED stall value].
- The HK0808 C0 and PTFE washer limits are not in the hub. The bearing and washer checks stay **TO-VERIFY** (as in section 6.1).

### 9B.3 Why the TD / LC2F rod forces rose: an OP-moment artefact of the pressure faces, plus a real CG shift (MF observation, ACCEPTED lead 22:24:34Z: the as-found cells stand; `results/v352/op_moment_check_v352.json` bf849ad982fb8bb1, `scripts/op_moment_check_v352.py` 73314071dbde04a3; `results/v352/rodstep_cones_v352.json` 6767d5b837f0189b, `scripts/rodstep_cones_v352.py` 731b75777e3ea692; `results/v352/rods_momentfree_v352.json` 5c328bca44a87375, `scripts/rods_momentfree_v352.py` 22e920b4f93b510d; Python only, no solve)

**As found** [DERIVED on SIM]: a couple of about **1.56 N m per MPa** of chamber pressure, from two TC-09 aft-boundary bore faces (elements 24664 / 23610) loaded at p/Pc 0.75. It is in the OP unit step of every v3.5.2 pose run.

**Unit-step rod tensions.** Recovered from the posts [DERIVED on SIM]:
- cone poses: least squares on the 64 stored GS sub-cases per pose, the only case whose post stores per-sub-case rod tensions (`rodstep_cones_v352.json`; rank 6, largest residual 4.5e-12 N). Recombined with the stored TD0 / TDP / LC6 / LC2F coefficients, they reproduce those cases' stored rod maxima to 0.004 N;
- stop045: the 32 LC3 hold sub-cases (`op_moment_check_v352.json` lc3_unit_rods; rank 5, residual below 1e-12 N).

| step, rod tension per unit (ROD_1 / ROD_2) | v3.5.1 c71 stop045 (CAD v3.5.1, asm v1.2) | v3.5.1 c71 cones | v3.5.2 stop045 L1 (asm v1.2, no tiex) | v3.5.2 stop045 L1x (asm v1.3, tiex; R3 the same) | v3.5.2 R3 cones |
|---|---|---|---|---|---|
| OP, N/MPa | +0.50 / +9.08 | -0.14 to +2.37 / +9.09 to +11.88 | +35.18 / +24.20 | +34.37 / +21.29 | +30.05 to +44.72 / +21.71 to +36.26 |
| GX, N/g | +0.17 / +0.13 | +0.13 to +0.41 / +0.12 to +0.38 | -1.34 / -1.17 | -1.64 / -1.39 | -1.97 to -1.36 / -1.97 to -1.36 |
| GY, N/g | -0.11 / -0.11 | -0.31 to +0.10 / -0.09 to +0.13 | +1.29 / -1.74 | +1.83 / -1.97 | +1.63 to +2.02 / -1.96 to -1.69 |
| GZ, N/g | -1.39 / -0.52 | -1.70 to -1.25 / -1.01 to -0.54 | -2.02 / -0.98 | -1.37 / -0.13 | -2.00 to -0.91 / -1.27 to -0.19 |
| EA, N per rad/s2 (stop045: one step; cones EAX / EAY) | +0.02 / -0.99 | EAX -0.79 to -0.75 / +0.75 to +0.79; EAY -0.98 to -0.64 (both) | +0.05 / -0.81 | +0.02 / -0.98 | EAX -0.78 to -0.74 / +0.74 to +0.78; EAY -0.99 to -0.63 (both) |

The OP and the lateral-g steps changed by an order of magnitude; the angular-acceleration steps did not.

**1. Not the v1.3 tie formulation.**
- On the same CAD v3.5.2 model, asm v1.2 (no tiex) and asm v1.3 (tiex) give the same OP and inertial rod tensions to within 0.8-2.9 N/MPa.
- The rev-3 levers do not change them either (stop045 L1x = R2 = R3; alpha+ / alpha- rev 1 = R3).
- The change came with the v3.5.2 model build: CAD v3.5.2 with its meshes and TB1 in thread mode.
- The c71x runs (tiex on v3.5.1) were not run (lead 18:50:09Z), so CAD and TB1 mode are not separated by a solve. The decks below separate them by load.

**2. The OP rod tensions are pure statics on the OP moment.**
- The two rods are the only moment path about the two gimbal axes. So a step's rod tensions follow from its applied moment Q about those axes alone: t = A^-1 (-Q).
- The OP load was rebuilt from the solver decks: 6,773 C3D10 face pressures (6-point rule on the quadratic face) plus the nodal caps, needle and residual-correction forces.
- The rebuild reproduces pressure.json OP_net to 1e-4 N and the FBD connector moment to 0.1 N mm.
- Applied OP moment about the pivot, per MPa:

  | run | moment (N mm) | Q (N mm) | statics rods (N/MPa) | posted rods (N/MPa) |
  |---|---|---|---|---|
  | v3.5.1 alpha+ | [-331, 204, 24] | [-331, 206] | -2.2 / +7.8 | -0.1 / +11.0 |
  | v3.5.2 alpha+ | [307, 2280, 289] | [307, 2298] | +30.42 / +31.84 | the same |
  | v3.5.2 stop045 | [307, 2285, -248] | [307, 2298] | +34.37 / +21.29 | the same |

  The v1.2 difference is its known moment leakage, v3.5.1 open item 7.2.
- At all 9 v3.5.2 cone poses the statics OP rods equal the post-recovered ones to 0.0005 N/MPa (`rods_momentfree_v352.json`): Q is [304-307, 2,298] N mm/MPa at every pose, because the OP load is fixed in the engine frame.

**3. The physical OP moment is zero; the model's is a residue of the pressure faces.**
- The pressure resultant on a closed cavity with an axisymmetric exit lies on the engine axis, through the pivot. Any OP moment the model carries is therefore a discretisation residue [DERIVED].
- The pressure.json "residual correction" (a uniform traction over about 85,200 mm2 of wetted faces: 4.3e-5 MPa/MPa in v3.5.1, 7.8e-5 in v3.5.2) removes the lateral force imbalance, but not the moment.
- By part, v3.5.2:
  - **The TC-09 face pressures carry 2,286 of the 2,298 N mm/MPa about the inner (Y) axis.** All the other face pressures and nodal loads together carry +12.
    - Two TC-09 bore faces at the aft boundary (z -230.5 mm, r 24.2 mm, azimuth +/-11 deg, 19.3 and 21.3 mm2) carry p/Pc 0.75.
    - All other faces at that station carry 1.0, so the bore has a 9.98 N/MPa lateral imbalance 230 mm aft of the pivot.
    - In v3.5.1 the 580 TC-09 faces all carry 1.0 and the lateral force is 0.000.
  - TC-09 changed in CAD v3.5.2 and was re-meshed (level 1.8, 694 faces).
  - The correction moves that 9.98 N to the wetted-area centroid (z about -74 mm), 157 mm forward of the faces, leaving a couple of about 1.56 N m/MPa.
- With the two faces at 1.0 (correction re-balanced), Q falls from [307, 2,298] to [294, 755] N mm/MPa about the X / Y axes. The OP rods fall to **+12.6 / +7.8 (alpha+) and +13.9 / +4.4 N/MPa (stop045)**; over the 9 cone poses to +12.5 to +17.3 / +4.5 to +9.3 N/MPa [DERIVED]. This is the moment-free statics estimate beside the affected rows of 9B.2.
- The rest comes from smaller lateral imbalances: TC-01 +4.1 / -2.1 N/MPa and NZ-04 -0.3 / -0.6 N/MPa.
- v3.5.1 carried the same kind of residue, but smaller: 0.39 N m/MPa, from TC-02 -4.4 and TC-03 +5.2 N/MPa.
- **Other models** (`results/v352/op_moment_global_v352.json` a7c92f815fb0f55d, `scripts/op_moment_global_v352.py` 46e916ee8fb86ef1) [DERIVED on SIM]:

  | model (deck) | TC-09 faces (fractional) | Q, N mm/MPa | abs Q, N m/MPa | statics OP rods, N/MPa |
  |---|---|---|---|---|
  | v3.5.1 L1 global (lc1v351_c71) | 1850 (71) | [161, -211] | 0.27 | -0.66 / -4.92 |
  | v3.5.2 L1 global: LC1, LC2, FA-1, TB70 / TBS (lc1v352g, fa1v352n, tb352g; TB's BL step the same) | 1858 (71) | [539, 484] | 0.72 | +13.53 / -0.72 |
  | v3.5.2 R3 hot-bound base (lc1v352hbg3; TC-09 level 1.8, as the R3 poses) | 694 (2) | [307, 2,298] | 2.32 | +34.46 / +26.33 |

  - The L1 meshes sample the TC-09 aft boundary all round the bore (71 faces at p/Pc 0.75 / 0.25), so their residue stays small. The level-1.8 mesh of the R3 poses and the hot-bound bases has only the two one-sided faces.
  - The hot-bound bases therefore carry the same artefact in their LC1 OP step: +86 / +66 N (ROD_1 / ROD_2, both tension) at Pc_max. Whether it adds to the prescribed rod forces or is replaced by them (lead 22:54:03Z (3); `results/v352/hb_base_residue_v352.json` e46d41bace79be47, script `scripts/hb_base_residue_v352.py` f7c2266242af1f1b) [DERIVED]:
    - lc3_bound forms hot = A + D, with D = sub-case - OP x Pc_max of the same pose. Each pose's own OP rods leave with D and the base's enter with A, so the rods implied by A + D are the cold sub-case rods plus (t_base - t_pose) Pc_max.
    - Rods prescribed (LC3 runaway fb_run, 609 N; GS at the +/-F_d corners, 441-552 N): the base residue is **replaced** by the prescribed rods, to within the pose difference: ROD_1 -31.7 to +11.9 N and ROD_2 -30.5 to +12.6 N over the stop poses; -25.7 to +11.0 and -24.8 to +11.6 N over the cone poses.
    - Rods reacting inertia (TD, LC6): the base residue **adds**, +86 / +66 N.
    - Governing lever-root cells (governing pose = the largest increment at the cell node): LC3 GM-01 stop315 ROD_1 **+11.9 N** (2.0 % of 609 N); LC3 GM-02 stop045 ROD_2 **+12.6 N** (2.1 %); F2 GM-01 alpha+ ROD_1 **+10.1 N** (1.8 % of 552 N); F2 GM-02 alpha- ROD_2 **+10.9 N** (2.0 %). Positive means A + D carries more tension on the lever rod than prescribed. At the lever roots the governing F2 increment is GS (the cold GS cells are the F2 minima there), so the 'replaced' branch applies.
    - Cheap bound for either sign [DERIVED; ASSUMED linear in the lever rod force, with the whole increment rod-driven]: dMS <= (1 + MS) dF / F. MS_u LC3 GM-01 +0.052 -> no lower than +0.031; LC3 GM-02 (p = 1 cell) +0.036 -> +0.015; F2 GM-01 +0.111 -> +0.091; F2 GM-02 +0.152 -> +0.129. All stay positive. The as-found cells stand; no re-solve.
  - In the L1 global OP-carrying cases ROD_1 carries a residue of +13.5 N/MPa (tension): about 34 N at LC1, 61 N at LC2, and FA1Q +127, FA1D +164, FA1U +199, FA1S +204, FA1T +127 N; ROD_2 -0.7 N/MPa. **GM-01 FA-1 bound by the rod-force path** (lead 23:12:52Z (2)) [DERIVED; transfer ASSUMED; `results/v352/gm01_rodpath_bound_v352.json` f24544c124289069, table `results/v352/tables/gm01_rodpath_bound_v352.md` 3d098441b2006bd9, script `scripts/gm01_rodpath_bound_v352.py` 84dc0ed81b350e6f]:
    - Moment-free ROD_1 is +2.9 N in every FA-1 case (the manifold and thermal share): lower than as found.
    - GM-01 stress per unit rod force: the EA unit steps of the v3.5.1 L1 neutral run `pose_neutral_c71` (S_EAX / S_EAY with its own EA unit rods; the same rev-1 lever). The cell node n88188 coincides with c71 n55792 at 0.000 mm. The v3.5.2 L1 model has no EA step, and the R3 pose runs keep U only.
    - The posted cells are reproduced exactly. With the residue removed (tensor sum), the cells rise: FA1S +0.100 / +0.264 -> +0.118 / +0.285; FA1U +0.130 / +0.299 -> +0.149 / +0.320; FA1D +0.373 / +0.578 -> +0.396 / +0.603; FA1Q +0.767 / +1.030 -> +0.796 / +1.063; FA1T +0.777 / +1.042 -> +0.806 / +1.075. The minimum stays at n88188, so **the as-found cells are the lower values and stand**.
    - Sign-free bound (triangle inequality, for a transferred tensor of the wrong sign): FA1S +0.077 / +0.238, FA1U +0.107 / +0.272, FA1D +0.344 / +0.544, FA1Q +0.730 / +0.987, FA1T +0.739 / +0.998. All positive.
    - The residue field at n88188 is 9.2 of 427.2 MPa (FA1S). Its GM-01 maximum, 107 MPa (FA1S), lies on the lever near the rod eye (n92054), where the cells do not govern.

**4. The inertial-step change is physical: the engine CG moved forward.**
- The CG implied by the FBD connector moments moved from [-2.64, 0.81, -0.55] mm (v3.5.1 stop045) to [-2.24 to -2.68, 0.36 to 1.34, 4.29 to 4.40] mm (v3.5.2, asm v1.3: stop045 L1x, alpha+ and neutral R3) [SIM]. The asm v1.2 model on CAD v3.5.2 (stop045 L1) gives [-3.34, 1.06, 3.52] mm.
- That is about +4.9 mm along the axis. CAD massprops agree: engine group mid CG z +0.52 -> +5.93 mm [CALC, 03-cad massprops v3.5.1 / v3.5.2].
- A lateral g now acts about 4.4 mm off the pivot: m g z is about 121 N mm/g. That is the GX / GY change of about 1.6-2.0 N/g per rod.

**Effect** (9B.2 gives every row with the estimates beside it).
- At Pc_max the OP residue adds **75-112 N** to the more loaded rod of each pose in TD (the Pc_max corners; OP rod term x 2.501 MPa). At 907.7 N thrust (OP 4.48 MPa) it adds **135-200 N**, most of the LC2F rod force [DERIVED]. LC6 has no thrust; its +3-9 N comes from the CG shift.
- Moment-free statics estimate over the 9 poses: TD 109-141 N (as found 153-209), LC2F 57-79 N (as found 136-202); with the OP rod term at zero, TD 83-108 N and LC2F 5-10 N [DERIVED].
- Rod path: higher rod forces are conservative for the rods, rod ends and servos. All stay below the 609 N stall.
- GS: the rods are prescribed, so the residue enters only through the solved engine angular acceleration. As found 487-939 rad/s2 (v3.5.1 570-847); moment-free estimate 556-871: some corners are loaded more and some less.
- The governing lever-root cells (GS at +/-552 N, LC3 at the 609 N rod limit) sit at prescribed rod forces. The OP moment reaches them only through the angular acceleration (GS) or the bumper force (LC3).
- **Airframe-hole loads and the LC3 bumper force**, estimated by superposition of the posted unit steps (`results/v352/icd_momentfree_v352.json` 785b4e48f407ddfb, `results/v352/tables/icd_momentfree_v352.md` cff5fecafb87c313, `scripts/icd_momentfree_v352.py` cf90b594ff7ac9f5) [DERIVED on SIM; transfer ASSUMED]:
  - Method: the residue reaches the airframe as the rod-force pair it produces plus the opposite bearing forces, so its hole reactions are taken from the engine angular-acceleration unit steps EAX / EAY, combined to give the same rod tensions. The transfer is ASSUMED independent of where on the engine the couple acts; neglected are the EA steps' small net force (about 0.012 N per rad/s2) and the roll part of the residue (about 6 % of the couple). The L1 global runs have no EA steps and use those of pose_neutral_v352r3R3 [ASSUMED]. GS re-solves the angular acceleration and LC3 re-solves the runaway bumper force, as their posts do.
  - Checks: as found reproduces the datasheet's as-found envelope (`engine_mount_data_v352.json`) at every hole and component to 5e-4 N (GS 0.04 N: its angular acceleration is re-solved from the 4-decimal unit rods); the statics OP rods match the posts to 0.0005 N/MPa; the EA unit rods from the fields match the posts to 5e-5 N; the recomputed LC3 bumper force matches the posted one to 3e-13 N.
  - R3 pose cases: TD at Pc_max max hole shear 306 N (AF_GM10_2) -> 207 (moment-free) / 186 (OP term zero); LC2F 288 -> 184 / 197. GS 808, TD at Pc 0 169, LC6 80 and LC3 890 N do not change. The LC3 runaway bumper force over the 8 stop poses moves from 161-521 N to 192-482 / 212-466 N.
  - **L1 global cases** (OP term zero only; the L1 mesh has no two-face variant): the OP-zero estimate is **3.5-7.8 % above** the as-found maximum, and its maximum sits at AF_GM09_0 in every case. LC1 70 -> 76, LC2 139 -> 150, FA1Q 326 -> 348, FA1D 420 -> 448, FA1U 510 -> 544, FA1S 523 -> 559 and FA1T 635 -> 657 N. For these rows the as-found hole loads are **not conservative**.
  - **Governing value (lead 22:54:03Z)** [DERIVED]: every datasheet hole-load row, L1 and R3 alike, is the larger of the as-found value and the estimate, per hole and component (pull-out and axial follow the same rule), and is then enveloped with the carried v3.5.1 compliant rows. Both values are shown; '!' marks where the estimate governs by 0.5 N or more. The as-found value carries the non-physical couple and the estimate rests on the ASSUMED transfer, so the larger bounds both. L1 rows: estimate = OP moment zero, through pose_neutral_v352r3R3's EA steps (ASSUMED). R3 rows: both estimates are included, because at 114 hole values the OP-zero value is the largest (by up to 18 N, LC2F AF_GM09_0 shear 197 N against 179 N two-face and 143 N as found). Case maxima: LC1 76, LC2 150, FA1Q 348, FA1D 448, FA1U 544, FA1S 559, FA1T 657 N (estimate governs); LC3 890, GS 808, TD at Pc 0 169, TD at Pc max 306, LC6 80, LC2F 288 N (as found governs). 512 of the 1,248 rigid hole values are governed by the estimate, 495 after the compliant envelope (section 8).
- Not estimated: part stresses and connector loads. They carry the same couple through the rods and the gimbal; separating it would need a re-solve.
- The residue is **not proven conservative for every part and corner**. It is a model-fidelity observation (MF) on the OP moment, reported as found, and the as-found cells stand (lead 22:24:34Z).

**Route that would remove it:**
- Make the OP load moment-free about the pivot: sample the TC-09 aft boundary consistently, and extend the residual correction to cancel the moment too.
- Then re-solve the 17 R3 poses. These are the same runs as the TC-04 route (section 4), so the two can share one re-solve.
- **Status: not schedulable under the disk rules as costed; the lead decides after js5b** (lead 22:24:34Z). The per-run start gate needs about 2.50 GiB free, and the route leaves free space about 0.95 GB lower (section 4). Nothing is scheduled.

## 10. F4 secondary joints J-FD01 / J-FD09 on the v3.5.2 hardware (item 3)

Files: `results/v352/f4_v352.json` (`fd5a06671fd4456a`), `tables/f4_v352.md` (`02613b8c56193fee`), `scripts/f4_v352.py`. These are hand calculations on the FEA3D F4 formulas [DERIVED]. No FE solve is involved.

**Method.**
- The formulas are those of `f4_secondary.py`, the v3.5.1 F4. Mechanical re-implemented them in `04-fea/v352/joints_v352_v1.json` (`460a2caceeb1391b`).
- Preload is F = T / (K d), with K 0.20 [ASSUMED, hardware rule] and ±25 % scatter [ASSUMED].
- Load factors: bounding Phi 0 (separation, slip) / Phi 1 (screw, host thread), plus the Phi 0.2 variant.
- Hot screw strength: k_T = SS316L Fty(T) / Fty(20 °C) proxy [ASSUMED, TO-VERIFY]. SF per CHANGELOG 188 (9).
- Host-thread strip area: FED-STD-H28/2 form [AS RECALLED].
- Cases:
  - LC1 flight;
  - LC3 touchdown 5.43 g (gnc.json v3.1) [SIM];
  - LC3 hard-landing envelope 10 g;
  - transport 3 g on any axis;
  - FA-1 spike (equipment bound).
- **New in v3.5.2:**
  - per-joint grade: A4-80, Rp0.2 600 / Rm 800 MPa (ISO 3506-1 minima, engmat SS-A4-80) [LITERATURE];
  - the J-FD01 three-screw pattern:
    - HW-103: 2 x M4x20 DIN 7984, lower pair at y ±8.5, z 146.51, engagement 8.5 mm;
    - HW-103B: 1 x M4x16, upper, y 0, z 165.51, engagement 5.5 mm;
    - all at 1.8 N m (M-T1) into the TC-02 flat at x -29.5. The 6061 host is at the soak-back head-top temperature, 121.1 °C.
  - J-FD09: HW-127 2 x M4x12 ISO 4762 A4-80 at 1.8 N m into GM-09 with a helicoil. Its thread is checked as a direct M4 tap in 6061 over 6.0 mm, which is conservative. Loads and geometry are those of the v3.5.1 F4 (prying lever 5 mm), with the hose at EI 0.184 and 0.5 N m².
- **Two load distributions for J-FD01:**
  - (a) **F4 bounding.** This is Mechanical's joints_v352_v1 method.
    - The cap force (P_MAN x A, on the R7 bounding area or the groove OD 9.9) is split by the elastic bolt group about the pattern centroid (rigid block, joint plane in contact). The cap shares are 0.4738 for the upper screw and 0.2631 for each lower screw.
    - The inertia force and the hose wrench F + M / s (s 19.0 mm) are added in full to every screw.
  - (b) **Elastic bolt group with vector loads.** This is an independent check.
    - The same cap force is used.
    - The inertia m a acts at the supported-mass CG: 0.1750 kg at [-31.9, 3.9, 109.9] mm.
    - The hose engine-end wrench (hose_end_reactions_v341_v1: 36 stop-axis rows of F and M vectors) acts at the hose engine end, [-36.2, 24.2, 72.0] mm. Both are reduced to the pattern centroid.
    - The lateral acceleration is swept over 24 directions x 2 axial signs. Every hose row is combined with every inertia direction, which is bounding because the stop direction and the touchdown direction are not correlated here.
  - In both, the 3 screws take the whole hose wrench and all listed masses. The FD-04 riser clamp on the case is not credited, which is bounding.

**Results [DERIVED].**

| joint | distribution | MS min bounding (criterion; case / area / screw; P) | MS min Phi 0.2 | other criteria, bounding (min over all rows) | Mechanical joints_v352_v1 (bounding / Phi 0.2) |
|---|---|---|---|---|---|
| J-FD01, 3 x M4 A4-80, 1.8 N m | (a) F4 bounding | **+0.121** (screw yield; LC3 10 g / R7 / upper; P 629.3 N) | +0.403 | ultimate +0.379, host thread +0.404, separation +0.788, slip +0.881, shear +27.2 | +0.122 / +0.403 |
| J-FD01 | (b) bolt group, vector loads | +0.128 (screw yield; LC3 touchdown 5.43 g / R7 / upper; P 613.4 N) | +0.405 | ultimate +0.389, host thread +0.415, separation +0.831, slip +0.507, shear +20.9 | - |
| J-FD09, 2 x M4 A4-80, 1.8 N m | hose EI 0.184 | **+0.476** (screw yield; LC3 10 g; P 302.1 N) | +0.660 | - | +0.476 / +0.660 |
| J-FD09 | hose EI 0.5 (sensitivity) | +0.221 (screw yield; LC3 10 g; P 757.7 N) | +0.586 | ultimate +0.485, separation +0.485, slip +0.550, host thread +0.626 | +0.221 / +0.586 |

- **Preload.** The preload is the same for both joints at 1.8 N m: F_nom 2250 N, range 1688-2812 N. Assembly utilisation is 0.55 nominal and 0.69 at +25 % [DERIVED; ASSUMED preload model]. In v3.5.1 it was 0.94 / 1.18 for J-FD01 (1.0 N m on M3 A4-70).
- **Agreement with Mechanical.** Distribution (a) reproduces joints_v352_v1 within 0.001 on every governing value. J-FD09 is identical. Distribution (b) is not lower than (a) on screw yield (+0.128 against +0.121), so the F4 bounding row governs.
- **Change from v3.5.1** (REPORT ff24718e9db201e5, claim 8 and section 8):
  - J-FD01 goes from **-0.41** bounding / -0.20 Phi 0.2 (2 x M3 A4-70, 1.0 N m, 121 °C) to **+0.121 / +0.403**.
  - J-FD09 goes from -0.17 / +0.05 (2 x M4 A4-70) to +0.476 / +0.660, or +0.221 / +0.586 at EI 0.5.
  - Both v3.5.1 design actions (CHANGELOG 223 (5)) are closed on the F4 formulas. This is not physical approval: K, the scatter and the hot factor remain ASSUMED.
- **Hardware revision check.** f4_v352 was computed on `hardware_v352.json` v1.2 (`1f1b82840c57de7c`, now `03-cad/v3.5.2/history/hardware_v352.json.1f1b82840c57de7c`). The current file is v1.6 (`0ed3f31d3e166f85`, MANIFEST e25b45808a8f9cf6). Every J-FD01, J-FD09, HW-103 and HW-127 entry is JSON-identical between the two, so I did not re-run; the results stand for v1.6.
- **RM2-09 (NOTE; line 234 (8): recorded against v3.5.1).**
  - The reviewer's precisions on the v3.5.1 F4 [DERIVED by Mechanical] are recorded against v3.5.1 and are superseded for v3.5.2 by the rows above:
    - J-FD01 was negative at the hot soak from preload alone: -0.131 (F_max 2083 N, k_T 0.799 at 121 °C).
    - J-FD01 at RT: bounding -0.259, Phi 0.2 -0.006.
    - J-FD01 torque window at Phi 0.2 (separation and screw yield): 0.621-0.775 N m.
    - A4-80 at 1.0 N m: -0.21 / +0.059.
    - J-FD09 at the specified EI 0.184: bounding -0.011.
  - The v3.5.2 hardware answers the reviewer's point that the fix is sized on preload. At 1.8 N m on M4 A4-80 the assembly utilisation is 0.55 / 0.69. At the soak head-top temperature (121.1 °C) the maximum preload alone uses 0.67 of the hot screw yield: F_max / (k_T Rp0.2 A_s) = 2812 / (0.799 x 600 x 8.78), from the `f4_v352.json` rows [DERIVED].

## 10A. J-FWD: the one-sector contact sub-model (item 2)

Files (FEA3D):
- js5 full post in hub `04-fea/assembly3d_v352/jfwd_interim/` (INDEX `76f9852492a597dd`): post `0a7a6a6f678957f7`, seatforce `a57642fe4a61f9ac`, shank `7393149774aec641`, screw_bend `6d926dd20af13e77`, ligament `5c1ad7c5293c5e5c`, midbay `08c2487411ae906b`, relax `4279825ae8af65b2`, spotface `62fc7329a8990fc4`, ccx_run `8e0184a6d9eed516`.
- Cells on the A_n 68.4 basis: `jfwd/runs/js5_mu0_T3750_g078/cells_v352An.json` (`3eda247150eb0c82`). The interim `cells.json` (`f9ed41727b0d4a46`, A_n 63.5) is superseded for the two thread rows only.
- **Soak envelope, final: v6 `results/v352/jfwd_soak_envelope_v352_v6.json` (`43a5d78b67c615fc`, script `jfwd_envelope_v6.py` `ac75b2c41146aead`; lead 2026-10-21T05:17:36Z (3)).** v5 `jfwd_soak_envelope_v352_v5.json` (`ef22b59cf2413b46`, script `jfwd_envelope_v5.py` `18886bbde22e1493`; ACCEPTED 03:30:46Z (3) as final unless cD moves a quantity) is superseded and kept. Delta tables (10A.12.2): v6 against v4 `results/v352/jfwd_envelope_delta_v352_v6_vs_v4.json` (`95e6eeee99e8196d`), `tables/jfwd_envelope_delta_v352_v6_vs_v4.md` (`c4601df48055b8fb`); v6 against v5 `results/v352/jfwd_envelope_delta_v352_v6_vs_v5.json` (`3844deef9c385a74`), `tables/jfwd_envelope_delta_v352_v6_vs_v5.md` (`545602a9d07129d2`); v5 against v4 `results/v352/jfwd_envelope_delta_v352_v5_vs_v4.json` (`a8c6aa69742fba5f`), `tables/jfwd_envelope_delta_v352_v5_vs_v4.md` (`de87c19ffedaba26`). Script `jfwd_envelope_delta_v352.py` (`04457425db504d8a`: the cited `32212446a8469f7c` plus an optional note, kept as `scripts/records/jfwd_envelope_delta_v352_32212446a8469f7c.py`; without the note it reproduces the v5-against-v4 files byte for byte). Mechanical's re-map inputs with cD (lead 2026-10-21T05:27Z (3)): `results/v352/jfwd_v7inputs_cD_v352.json` (`5a41c8d74897bdda`), `tables/jfwd_v7inputs_cD_v352.md` (`424146c89c8c9f01`), script `jfwd_v7inputs_cD_v352.py` (`0cc1c2bf2d3f0092`) (10A.12.1).
- Envelope records, kept and not rewritten: v4 `results/v352/jfwd_soak_envelope_v352_v4.json` (`9d9fd8ee991f9887`, script `jfwd_envelope_v4.py` `c10fe68a8fcb1f5e`; ADOPTED 2026-10-21T00:39:30Z (1), superseded by the final envelope); v3 `jfwd_soak_envelope_v352_v3.json` (`0872de4ea7e3601d`, adopted 15:37Z (R1)); v2 `jfwd_soak_envelope_v352.json` (`336568296bdb896f`, the sharp-edge envelope adopted 13:14Z); v1 `jfwd_soak_envelope_v352_v1.json` (`1d970741cb95a885`); the cited v5 candidate before C1 `results/v352/candidates/jfwd_soak_envelope_v352_v5_candidate_noC1.json` (`e3e06bf302d9bc3e`, script `scripts/candidates/jfwd_envelope_v5_candidate_noC1.py` `43e9ed370ff42401`).
- (b1) mu 0.2 patch `jfwd/runs/seat_s9L12_mu02A/`: compare `eba047e47f69e8af`, seatforce `553a0ed1cbe51548`, shank `a7c05620613b091a`, lig_station `9e3643ea9ed2f5c4`, histcheck `be67a617cef47d67`; frd.gz `97f77ab30c5f432f` (raw `30d065222690795d`) (10A.12).
- (b2') mu 0 s9 patch `jfwd/runs/seat_s9L12_mu0/`: compare `0ae76ed185599268`, seatforce `722b28f49473b8dc`, shank `c402e74c125b5182`, lig_station `aa9fdb776e73f99d`, judge against (b2) `judge_seat_s6L12_mu0.json` `3619a7b39613edf0`; frd.gz `fb9878210f1176cb` (raw `75db214df62fb11d`) (10A.6).
- Mesh correction C1: `results/v352/jfwd_b1_meshcorr_v352.json` (`adac16afd42ef7bd`), `tables/jfwd_b1_meshcorr_v352.md` (`8fed1d2a24e443b1`), script `jfwd_b1_meshcorr_v352.py` (`2b7f28b06b0f4f58`). Convergence-check costing `results/v352/jfwd_convcheck_costing_v352.json` (`b427869869a9e8f8`, md `e670c97d74640e66`, script `jfwd_convcheck_costing_v352.py` `eb5f7e3b6c15e6b2`); patch extrapolation nodes `results/v352/jfwd_patch_extrap_nodes_v352.json` (`f95abde5b1489976`, script `jfwd_patch_extrap_nodes_v352.py` `2192167fde400a5d`) (5.3).
- cD convergence check `jfwd/runs/seat_sDL12_mu0/` (s6 + Ball h 0.04 mm at the governing-line ends, FINAL TC-01, mu 0; deck `d7771451a7369dc1`): compare `c891db7dcb3445c9`, shank `0ef43b2e27a72e8c`, seatforce `52ab8f40fae1bb75`, lig_station `39fffa388a7bf366`, histcheck `8567e026a7b3dcc4`, judge against (b2) `judge_seat_s6L12_mu0.json` `eeb9067f1c3400db` and against (b2') `judge_seat_s9L12_mu0.json` `beebcbed7eeb845c`, ccx_run `8e044cd991afe0bc`; frd.gz `366a1f9d6d12aa9e` (raw `02df780c504237ed`), deck `.inp.xz` `b70aeb2c9d467453` (`DECK_XZ.txt`); posts `runs/post_cD.log` (`5f696dded48b0c3c`). Result: `results/v352/jfwd_cD_result_v352.json` (`8209e80f09f28af7`), `tables/jfwd_cD_result_v352.md` (`e19a834997c0e473`), script `jfwd_cD_result_v352.py` (`6dfd6d331b946b48`) (10A.6, 5.3).
- js5b `jfwd/runs/js5b_in718_mu0_T3750_g078_cf/`: cells_v352An `d25745ca0ff96cb5`, spotface `64180d98c6e30d5b`, shank `6892b603129f2813`, seatforce `2ce7f8524c6cc149`, post `080131ee23d4e712`, ligament `b5c19c20f493b2b2`; frd.gz `a7c3c22d985ff327` (raw `e1f1f39a98425547`). Rows: `results/v352/jfwd_js5b_rows_v352.json` (`91278d6b039c5b27`), `tables/jfwd_js5b_rows_v352.md` (`953524963267f934`), script `jfwd_js5b_rows_v352.py` (`41f1d46ca5457f1e`) (10A.13).
- Final-envelope inputs in Mechanical's v7 quantities (lead 01:01:13Z): `results/v352/jfwd_v7inputs_v352.json` and `tables/jfwd_v7inputs_v352.md`, script `jfwd_v7inputs_v352.py`; the C1 view `jfwd_v7inputs_c1_v352` (10A.12.1).
- (b2) broken-edge patch `jfwd/runs/seat_s6L12_mu0/`: summary `961b19102a002f6b`, histcheck `8990fb284f66f75a`, compare `727e10ba6c8fb41b`, shank `280e383e5b87dd07`, seatforce `9eb36a729ef6b5a5`, lig_station `1003aec74127d605`, envelope candidate `de99e3cd582d7f8f`; frd.gz `af909d1dc7f06a3a` (raw `19d26ce0bc554641`).
- Flat bearing on the ruled ring area: `results/v352/jfwd_flat_bearing_arow_v352.json` (`bdb34ca4af677bca`).
- Scripts: `jfwd_sub.py`, `jfwd_deck.py`, `jfwd_seat.py`, `jfwd_post.py`, `jfwd_cforce.py`, `jfwd_seatforce.py`, `jfwd_shank.py`, `jfwd_screw_bend.py`, `jfwd_ligament.py`, `jfwd_lig_station.py`, `jfwd_relax.py`, `jfwd_midbay.py`, `jfwd_spotface.py`, `jfwd_cells.py`, `jfwd_envelope.py`, `jfwd_seat_cmp.py`, `jfwd_runcmp.py`, `jfwd_patch_judge.py`, `jfwd_histcheck.py`, `jfwd_patch_summary.py`, `jfwd_envelope_b2.py`, `jfwd_flat_bearing_arow.py`, `jfwd_envelope_v4.py`, `jfwd_envelope_v5.py`, `jfwd_envelope_v6.py`, `jfwd_envelope_delta_v352.py`, `jfwd_b1_meshcorr_v352.py`, `jfwd_v7inputs_v352.py`, `jfwd_v7inputs_c1_v352.py`, `jfwd_v7inputs_cD_v352.py`, `jfwd_convcheck_costing_v352.py`, `jfwd_patch_extrap_nodes_v352.py`, `jfwd_sub_cD.py`, `jfwd_cD_run_v352.py`, `watch_cD_v352.py`, `jfwd_cD_result_v352.py`, `jfwd_js5b_rows_v352.py`; stage `runs/stage_cD_v352.sh`.

All FE values are [SIM]; the cells built from them are [DERIVED]. Mechanical's rows are [CALC] or [DERIVED] as Mechanical tags them. Nothing here is physical approval.

### 10A.1 What the sub-model replaces, and the criterion

- In the global model the ten J-FWD screws are RBE3 bushings (section 2). Line 231 (3) replaces them for every J-FWD cell by a one-sector contact model with a solid screw. The TC-01 cells at z >= 97.5 come from this model (lead 07:51Z (d)).
- The criterion is Mechanical's hand checks (i)-(iii) with the 234 (1)(b) preload treatment. The FE confirms or refutes them (10A.9).
- Status:
  - Solved and posted: the js5 global sector, the sharp-edge seat patches (a), (a') and (a''), the broken-edge patch (b2) at mu 0 (10A.5), the broken-edge patch (b1) at mu 0.2 (posted 2026-10-21T00:30:31Z; 10A.12), the mesh check (b2') at mu 0 on s9 (posted 01:18:57Z; 10A.6), js5b on IN718 (FA1U / FA1D / LC2; posted 03:18:21Z; 10A.13), and the convergence check cD on the FINAL TC-01 (s6 + Balls, mu 0; ran 03:18:46Z-05:09:25Z, posted 05:10:18Z; 10A.6).
  - The tail after (b2) was ruled at 15:37Z (R3): (b2') (mesh check, 10A.6), then (b1), then js5b (FA1U / FA1D / LC2). The order was set at 18:04:32Z / 18:50:09Z: (b1), soak352g / h, (b2'), js5b; cD followed js5b (lead 02:01:34Z (C)).
  - The J-FWD basis is the final envelope v6 `43a5d78b67c615fc` (lead 02:01:34Z (E), 03:30:46Z (3), 05:17:36Z (3)); v5 (ACCEPTED 03:30:46Z (3)) and v4 (ADOPTED 00:39:30Z (1)) are superseded records.

### 10A.2 Model

- **Geometry.** CAD v3.5.2 interim: TC-01 spot-face revision `1ad07e472709b1b2`, TC-02 `a1e7098da05183c3`.
  - **FINAL TC-01 (disclosure, lead 2026-10-21T02:01:34Z (D); section 2.1).** The FINAL v3.5.2 TC-01 `parts/ENG-TC-01.step` `fcb3b5b93bebdb01` has d11.2 spot-face flats in place of the interim d10.5 flats. The flats are coplanar (x' 31.313, wall 2.688 at the hole); the interim-minus-final volume is 104.037 mm3 over the 10 flats (Mechanical's CAD check `test_final352_v1.json` `aa064886ee64ac94`). **All J-FWD FE in this section is on the interim TC-01, except the convergence check cD (10A.6).** The head footprint (r' <= 4.75 mm from the hole axis) lies inside both flats (r' 5.25 / 5.6), so the head bearing face is the same; what moves is the outer edge of the flat, 0.50 / 0.85 mm outside the head edge. The effect on the other rows is ASSUMED small; cD quantifies it on the governing line.
  - One 36 deg sector (az 0-36), with the screw at az 18 (10x at 18 + 36k).
  - The az 0 plane is the mirror plane of the torch passage. The sector therefore holds half the passage and the 1.906 mm tap-to-passage wall (233 (4)). TC-02 is modelled at the thread-root diameter over the engaged length.
- **Screw HW-101, ISO 7380-1 M5 x 10, solid.**
  - Head: a cylinder D 9.5 x k 2.75 with a flat bearing face. The dome and the socket are omitted [ASSUMED idealisation].
  - Shank: D 5.0 in the D 5.5 hole.
  - The head bears on the d10.5 spot-face flat at x' 31.313 (wall 2.688 at the hole; the final d11.2 flat is coplanar, see above).
  - The tip is at x' 21.313. The thread is bonded over x' 21.313-28.600 (7.287 mm).
  - The FE keeps L 10.0. The report rows use the drawn M5 x 10.2 basis (lead 13:14Z; 10A.8); the effect on stiffness is [ASSUMED] small.
- **Materials.**
  - TC-01 and TC-02: AL6061-T6, engmat properties at temperature.
  - FE screw: A4-80 properties (E 193 GPa scaled by SS316L E(T); SS316L alpha(T)) [LITERATURE / ASSUMED proxy].
  - The ruled flight screw is IN718 (240 (4)). Mechanical maps the IN718 screw onto these runs (240 (9)(v)). js5b carries IN718 properties.
- **Preload.**
  - A pretension section at x' 30.2: SEAT closes the gaps (d1 0.05 mm); PRELOAD applies 3750 N; d1 is then fixed, so the bolt force follows the thermal and pressure loads.
  - 3750 N is the +25 % value of the 3.0 N m nominal 3000 N (relay 03:10Z). The lead set 3750 N for the FE (06:36Z, 08:17Z).
  - Lower preloads are not solved: the 2250 N minimum and the 3000 N nominal sit in Mechanical's joint model on this FE (relax v4-v7). The J-F1 maximum is capped at 3750 N (lead 17:56:12Z), so the 3750 N runs are the governing basis. Mechanical's 4096 N rows are information.
- **Contacts.** Penalty, linear, K 5e5 MPa/mm [ASSUMED numerical]. Every solved run is frictionless except (b1) (mu 0.2; 10A.12).
  - HEAD: head on the spot face.
  - BEAR: shank in the hole.
  - FIT: TC-02 OD r 28.600 in the TC-01 bore r 28.625. `*CLEARANCE` is 0.078 mm radial, the H8/f7 drawing maximum. That end bounds the shell pull and the screw shear before the fit closes (lead 09:15Z).
  - Resultants are exact K u nodal forces. The CPRESS face integral is biased by x1.7 to x27 (MF-J1) and is not used.
- **Boundary conditions.**
  - Symmetry on az 0 and az 36 (u_theta = 0).
  - The TC-01 aft cut at z 97.5 is held axially.
  - TC-02 hangs on the contacts and the bonded thread. Ten axial springs of 1 N/mm remove its rigid-body mode; their reaction is at most 1.0 N.
  - The TC-01 sector is shifted -0.24 mm in z. The shank then starts 0.01 mm from the hole's +z wall, so the head bears at once under pressure (the 234 (1)(c) bearing-type joint).
- **Loads.**
  - Pc (absolute, vacuum ambient) on the wetted faces of TC-02 and TC-01, plus the torch cap force and the TC-03 disc load on the M14 bore.
  - No manifold pressure: it is internal to the TC-02 / TC-03 / TC-04 manifold, carries no net J-FWD load and acts more than 18 mm from the screw.
  - At FA1S the FE head load per sector is 15.104 x 257.42 = 3888.1 N, which equals Mechanical's CALC V (240 (3)).
- **Temperatures.**
  - Either uniform per part and step, or the mapped S-AX GVLO fields B1_70.7 / B1_51.7. Source: Mechanical's run `L1_thv352_NF2b_GVLO_r10free_cad352`, mesh `c1b81a9aea53d395`, res `5d0783af6cdf0a94` / `a11bec10dbc54cf7`.
  - SOAK keeps the 64.7 s row means (TC-01 158.0, TC-02 96.0, screw 127 C) as the reference (lead 04:13Z).
  - Section check: S-AX cuts TC-02 at az 78. Each S-AX mesh (GVLO, GVHI, NF2b) has 126 TC-02 elements in the tap envelope, all solid material; the largest gap is 1.044 mm at r 10.2. This is consistent with the az 78 cut (`results/v352/sax_section_check_v352.json`).
- **Mesh s5.** C3D10, h 0.3 mm at the holes and on the tap wall (brief: h <= 0.3), hmax 2.5.
  - 103,727 nodes; 110,253 with the duplicated tie and pretension nodes.
  - Tets: TC-01 13,499; TC-02 34,616; screw 18,785.
  - js5 ran 8879 s, peak RSS 5.97 GB, rc 0.

**Steps.**

| Run | Steps (in solve order) | Load |
|---|---|---|
| js5 (solved) | SEAT, PRELOAD, SOAK70, FA1S, SOAK, SOAK52 | PRELOAD 20 C; SOAK70 / SOAK52 on the mapped GVLO fields; SOAK at the 64.7 s row means; FA1S 151.04 bar abs at 45.6 C, SF 1.0 (line 231) |
| js5b (solved; IN718; source `js5b_in718_mu0_T3750_g078`, raw `fd5c555220cab427`, run as `js5b_in718_mu0_T3750_g078_cf` (deck `0d852f10082883e8`) with restricted contact output + FREQUENCY=1000, lead 19:09:50Z / 19:53:27Z (2); ran 2026-10-21T01:18:59Z-03:16Z after (b2'), 7036 s, peak RSS 6.13 GB, rc 0 (10A.13); the 09:20Z A4-80 deck `js5b_mu0_T3750_g078` `3842f1c070f5d1a3` was never run, SUPERSEDED 11:50:19Z by the IN718 deck, lead 11:25Z (3)) | SEAT, PRELOAD, FA1U, FA1D, LC2U, LC2Y, LC2N, LC2M | FA1U / FA1D 147 / 121 bar abs (230 (2) band) at 45.6 C; LC2 x2.0 / x1.5 / x1.0 on 45 bar at 78.6 C uniform; LC2M 45 bar on the GVLO B1_21.65 field |

### 10A.3 js5 results (global sector, sharp hole edges, mu 0, 3750 N, fit 0.078)

**Joint forces.** Screw forces are the exact shear-plane resultants. Seat force is the exact contact force at the fit. Shell pull = tie force - seat force.

| State | Screw N (N) | V (N) | M_max on thread (N mm, at x') | Seat force (N) | Shell pull (N) |
|---|---|---|---|---|---|
| PRELOAD | 3750.0 | 0.1 | 298.7 (28.3) | 1118.6 | 2634.8 |
| SOAK70 | 5694.7 | 11.2 | 1107.8 (28.6) | 1400.4 | 4299.6 |
| FA1S | 3147.9 | 3750.2 | 2984.6 (28.6) | 1154.0 | 2000.1 |
| SOAK | 7382.9 | 6.8 | 3481.0 (28.6) | 3125.8 | 4263.8 |
| SOAK52 | 6559.8 | 3.1 | 2417.0 (28.6) | 2337.1 | 4230.9 |

- The seat stays loaded at every step (minimum 1115 N).
- The contact footprint is one ring round the TC-01 hole edge: r' 2.50-3.30 mm from the tap axis, z' -3.25 to +2.75, arc ±3.0 mm.
- FA1S load balance: applied 3888.1 = tie 3750.7 + hole-edge contact 136.3 + springs 1.0 + symmetry 0.8 - unclassified 0.8 N. So 10 V / applied = 0.965, and the 136 N per screw into the hole-edge contact is not credited (240 (3)).

**TC-01 and TC-02.**
- "All-node" is the peak over every node. "Band" is the peak more than 1 mm from the hole (TC-01) or the tap (TC-02).
- TC-01 all-node peaks sit at the hole / head contact edge; TC-02 all-node peaks sit at the bonded-thread tie edge. Both are information (lead 06:17Z, 07:21Z).
- Margins are yield / ultimate at the case SF (1.0 for every state here).

| State | TC-01 all-node (info) | TC-01 band | TC-01 cell (criterion) | TC-02 all-node (info) | TC-02 cell (criterion) |
|---|---|---|---|---|---|
| PRELOAD | 4073 MPa n388 | 197.8 MPa n4037 (1.08 mm), +0.213 / +0.314 | secondary, information (lead 08:40Z / 09:15Z); band Neuber +9.15 | 1780 MPa n1660 | thread A_n +1.526 / +1.846 |
| SOAK70 | 3371 n398 | 377.0 n11688 (1.01 mm, on the flat), Neuber n30 +0.788 | P+Q <= 2 Fty(T): 54 seat lines -0.011 (js5), envelope **-0.019**; ring +0.198; mid-bay +0.268; flat bearing +0.623 (A_ROW) | 1035 n1660 | thread +0.581 / +0.756 (at the envelope N 6388.9: +0.410 / +0.566 [DERIVED]) |
| FA1S | 4390 n388 | 556.9 n11688, elastic -0.576 / -0.543 (info) | **+0.171 / +0.263** (i) ligament Pm+Pb; see below | 2148 n1660 | **+0.981 / +1.136** (i) shear-out Pm+Pb; see below |
| SOAK | 3843 n338 | 379.6 n11688, Neuber +0.832 | 54 lines +0.042 (js5), envelope **-0.035**; ring +0.111; mid-bay +0.233; flat bearing +0.233 (A_ROW) | 2100 n1642 | thread +0.221 / +0.357 |
| SOAK52 | 5035 n395 | 384.5 n9512 (1.03 mm), Neuber +0.479 | 54 lines +0.034 (envelope); ring +0.213; mid-bay +0.331; flat bearing +0.487 (A_ROW) | 1299 n17845 | thread +0.375 / +0.528 (at the envelope N 6742.0: +0.338 / +0.487 [DERIVED]) |

- **Flat bearing area basis.** The table quotes the under-head flat bearing on the ruled ring area A_ROW 38.171 mm2: the minimum ring at the rev-5 worst stack (lead 14:14Z, rows v4 (a); Mechanical rows v5). The full flat annulus of `jfwd_spotface.py` (d9.5 / d5.5, 47.12 mm2: +1.003 / +0.522 / +0.836) is superseded because it is not conservative. These FE rows use the js5 head force on A4-80 at 3750 N and are information. On the head forces of the envelopes, the A_ROW rows are: sharp SOAK70 +0.446, SOAK52 +0.447; (b2) SOAK70 +0.237, SOAK52 +0.257 [DERIVED, `jfwd_flat_bearing_arow_v352.json`]. The criterion row is Mechanical's IN718 row: SOAK at 4096 N, +0.076 on A_ROW.
- **Soak and preload states are secondary** (lead 08:40Z): the preload pull on the TC-01 wall is imposed by tightening. Their criterion is P+Q <= 2 Fty(T) on the SCLs, plus the under-head band by the local-strain (Neuber) check. The TC-01 under-head cell is class "DC adopted (d10.5 spot face), FE closure pending" (lead 07:21Z).
- **Ligament station.** It sits 0.087 mm from the hole wall and is a contact-edge field, so it is information (240 (9); Mechanical carries it the same way): PRELOAD -0.096, SOAK70 -0.395, SOAK -0.200, SOAK52 -0.208.
- **FA1S rows, TC-01** (primary: pressure plus the screw shear-bearing reaction; SF 1.0, 45.6 C):
  - (i) Ligament, half-ligament average: Pm 104.1, Pm+Pb 201.6 MPa, giving +1.268 / +0.171 (yield) and +1.446 / +0.263 (ultimate). At the seat station: Pm 95.9, Pm+Pb 201.5 (+0.172 / +0.264).
  - (i) Shear-out flanks: Pm +0.991 / +0.952 (yield), Pm+Pb +0.809 / +0.769.
  - (ii) Hole bearing: exact V 3603.6 N on t 2.688 gives 268.1 MPa, +0.233 / +0.519.
  - (iii) Band Neuber (n 30): +0.518.
  - Cell: **+0.171 / +0.263**.
- **FA1S rows, TC-02:**
  - (i) Shear-out at x' 28.0: Pm+Pb 119.2 MPa, +0.981 / +1.136.
  - (ii) Thread shear on A_n 68.4: tau 45.9 MPa, +1.969 / +2.330. Tap bearing on L_e 6.84: 106.1 MPa, +2.115 / +2.839.
  - (iii) Band Neuber: +7.89.
  - The band (204.5 MPa, +0.155 / +0.245) lies 0.99 mm from the TC-01 hole-edge footprint, in a contact-edge field, so it is information. The through-wall SCL at that band node passes: Pm +1.814, Pm+Pb +0.346 (lead 07:21Z condition).
  - Cell: **+0.981 / +1.136** (js5). The cell the lead closed at 07:25Z was the js4 cell (CAD seat, s4), +1.144 / +1.404 on the thread.
- **FA1S P+Q** (bore node n4308 -0.034, under-head n37224 -0.137) is information for this single abnormal event (240 (2)).
- **Screw rows as run (A4-80 properties), information only** (A4-80 is withdrawn for J-FWD, 240 (4)): soak tension on A_s SOAK70 +0.113, SOAK -0.089, SOAK52 -0.025 (N_exact basis). The flight rows are the IN718 rows in 10A.8.

### 10A.4 Seat patches at mu 0, sharp edge: validation and history

- **Patch method** (`jfwd_seat.py`). A box round the hole (x' >= 26; |y'|, |z'| <= L) is cut out of the js5 model. The js5 displacement is prescribed on the cut per step. The local mesh is the same (s5) or re-meshed (s6 / s9, with the global field interpolated by the C3D10 shape functions).
- **Acceptance (lead 08:17Z, 10:14Z):** within 5 % of js5 on the 54 seat lines, the screw sections and the seat force.

| Patch | Order | Result against js5 [SIM] |
|---|---|---|
| (a) seat_s5L8_mu0 | physical (PRELOAD, SOAK52, SOAK, SOAK70, FA1S) | PASS at PRELOAD / FA1S (54 lines <= 2.6 %; N, V, M <= 2 %). FAIL at the soaks (P+Q up to 36 %; N -11 % to -19 %, and +12 %) |
| (a') seat_s5L8_mu0_go | js5's order and SEAT | PASS at SOAK70 (<= 2.6 %) and FA1S (<= 1.4 %; seat window +7.8 %). Not at the PRELOAD side lines (10.5 %), SOAK (N -21.7 %) or SOAK52 (<= 8 %) |
| (a'') seat_s5L12_mu0_go | js5's order, box L12 (full sector width) | Not within 5 % of (a'): PRELOAD M28.6 +29 %, FA1S window -9.5 %, SOAK M -57 %, N -3.8 %. A third footprint, so L12 is used for (b2) / (b2') / (b1) (lead 12:28Z (2)) |

- **Finding: the sharp-edge soak states are history-dependent.**
  - The prescribed boundary displacements are identical.
  - The difference sits at the TC-01 bore-side hole-edge corner. There the penalty pressures reach about 10 GPa, and different nodes carry them depending on the predecessor state and the increment path.
  - The lead recorded this as numerical non-uniqueness of the sharp-corner penalty contact, not physics (11:41Z). Model note: section 7.
- **Ruling 240 (9)(i), envelope v2 `336568296bdb896f` (adopted 13:14Z; superseded by v3 at 15:37Z (R1) and by v4 at 2026-10-21T00:39:30Z (1)).** Every sharp-edge soak quantity is the worst over the four histories js5, (a), (a') and (a''), taken per state and per quantity. The table is that sharp-edge record.

| State | Screw N max (N) | Seat window min (N) | 54-line P+Q MS min | M_max on thread (N mm) |
|---|---|---|---|---|
| PRELOAD | 3750 | 1118.6 (js5) | +1.114 (a') | 744.8 (a'') |
| SOAK70 | 6388.9 (a) | 1351.3 (a'') | **-0.019** (a') | 2099.0 (a) |
| SOAK | 7382.9 (js5) | 1223.7 (a') | **-0.035** (a') | 3481.0 (js5) |
| SOAK52 | 6742.0 (a') | 1332.0 (a) | +0.034 (js5) | 2494.4 (a'') |
| FA1S | 3147.9 (js5) | 1126.1 (a'') | +0.097 | 2990.9 (a'') |

- Found negatives on the sharp geometry: the **SOAK70 and SOAK seat-line P+Q cells**. Both are TC-01 secondary (shakedown) cells in a steep near-edge gradient, 0.26 mm from the hole wall.
- FA1S is history-independent (N within 1.4 %; line MS spread 0.03). Its seat window varies from 1126 to 1244 N, but that does not touch the FA1S screw cell (lead 13:14Z).
- The seat line stands as the arbiter (240 (10)). It is re-arbitrated with the R0.2 break, which moves the contact ring onto it (10A.5).

### 10A.5 Broken edge: (b2) at mu 0 and (b1) at mu 0.2

- **Geometry, mesh s6.** The drawing break: R0.2 at the bore-side hole edge (hard maximum) and 0.1 x 45 at the flat end (240 (5)). h 0.08 at the break; 159,178 nodes. The BEAR surface is widened onto the fillet and the chamfer (48.0 mm2; s5 45.0).
- **(b2) seat_s6L12_mu0.**
  - L12 patch, 107,611 nodes, deck `0a28d63315dc8365`, on the js5 field. A4-80 screw properties at 3750 N, mu 0. Mechanical maps the run to IN718 (240 (9)(v)).
  - Form (A): the physical order plus two repeats, SOAK after FA1S and SOAK52 after SOAK. The solve order is PRELOAD, SOAK52, SOAK, SOAK70, FA1S, SOAK_rep, SOAK52_rep.
  - Ran 13:07:16-15:18Z: 7861 s, peak RSS 5.76 GB, rc 0. Every step converged in one increment (SEAT in two).
- **Test (240 (9)(iv)).** Each repeat must fall within 5 % of its first instance on the 54 lines, the screw N and M and the seat window.
  - If it does, (b2)'s soak values become the basis for the built part, and the sharp-edge values become information.
  - Otherwise the envelope over every history is carried.

**Result: the test FAILS for both repeats on all four quantities** [SIM; DERIVED ratios].

| Repeat vs first instance | Screw N (N) | M at x' 28.6 (N mm) | Seat window (N) | 54 lines |
|---|---|---|---|---|
| SOAK_rep (after FA1S) vs SOAK (after SOAK52) | 6337.0 vs 5252.3 (+20.7 %) | 1131.9 vs 644.5 (+76 %) | 1760.7 vs 639.4 (+175 %) | max 15.8 %; 50 lines > 5 % |
| SOAK52_rep (after SOAK_rep) vs SOAK52 (after PRELOAD) | 7764.0 vs 6228.2 (+24.7 %) | 2915.7 vs 2099.2 (+39 %) | 3413.0 vs 1802.8 (+89 %) | max 23.8 %; 36 lines > 5 % |

- **Finding: the broken edge does not remove the history dependence.** As on the sharp edge, the footprint follows the predecessor state. Each state converged in one increment, so this is predecessor dependence of the penalty contact, not the increment path.
- So (b2)'s soak values are not a unique basis. They are carried as an envelope over the histories (10A.5.1). The lead adopted the worst of sharp and (b2) as envelope v3 (15:37Z (R1)). v4 adds (b1) and is the current basis (2026-10-21T00:39:30Z (1)).

**(b2) per step** [SIM]. The seat window is the TC-02 seat normal force over |daz| <= 9 deg, |z'| <= 9 mm. Shell pull uses the patch definition of `seatforce.json`: the thread below x' 26.0 enters through the prescribed cut.

| Step | Head force (N) | Screw N (N) | Seat window (N) | Footprint centroid z' (mm) | Shell pull (N) | 54-line P+Q MS min | Lines negative / Pm > Fty |
|---|---|---|---|---|---|---|---|
| PRELOAD | 3749.9 | 3750.0 | 901.4 | -0.99 | 1063.8 | +1.038 | 0 / 0 |
| SOAK52 | 6228.4 | 6228.2 | 1802.8 | -2.29 | 638.5 | -0.011 | 1 / 6 |
| SOAK | 5252.5 | 5252.3 | 639.4 | -0.35 (three clusters) | 1987.9 | -0.067 | 2 / 16 |
| SOAK70 | 7471.8 | 7471.8 | 3123.4 | -2.14 | 195.4 | -0.055 | 1 / 18 |
| FA1S | 2723.1 | 2734.6 | 462.5 | -0.04 | 694.6 | +0.053 | 0 / 2 |
| SOAK_rep | 6336.7 | 6337.0 | 1760.7 | +1.74 | 1826.9 | -0.071 | 1 / 16 |
| SOAK52_rep | 7764.2 | 7764.0 | 3413.0 | -1.77 | 179.9 | +0.048 | 0 / 6 |

- The footprint is always the ring round the hole edge: daz ±6.0 deg, z' -3.4 to +3.4. The force-weighted radius from the tap axis is r' 2.76-3.08 (sharp edge 2.73-2.85). The ring moves out to the end of the break.
- The governing seat line is d+6.051 z'0 in every state; it lies wholly in the material (minimum barycentric +0.0004). It starts about 0.07 mm past the end of the R0.2 break, so the contact ring now sits on it. This is the re-arbitration 10A.4 expected.
- Against (a'') (sharp edge, L12, js5's order) at the same line: SOAK52 -0.011 vs +0.118, SOAK -0.067 vs -0.035, SOAK70 -0.055 vs -0.016, FA1S +0.053 vs +0.101. The (a'') SOAK70 came after PRELOAD and the (b2) SOAK70 after SOAK, so geometry and history differ together.
- The lines with Pm > Fty at the soaks are reported as found. The soak criterion is P+Q (secondary, lead 08:40Z); the Pm counts go to Mechanical's shakedown and relaxation work with the P+Q rows.

**(b2) FA1S, the screw** (lead 10:24Z list) [SIM]:

| x' (mm) | N (N) | V (N) | M (N mm) |
|---|---|---|---|
| 26.5 | 1676 | 457 | 2139 |
| 27.5 | 1969 | 1138 | 2586 |
| 28.1 | 2296 | 2025 | **2726.1** (maximum on the threaded length) |
| 28.6 (shear plane) | 2594 | 3598 | 2717.4 |
| 29.0 | 2763 | 3335 | 1825 |
| 29.5 | 2725 | 2579 | 362 |
| 30.0 | 2753 | 1941 | 801 |
| 31.0 | 2741 | 544 | 2067 (maximum in the TC-01 shank, under the head) |

- Section values are stress resultants. The exact shear-plane resultant (screw nodal forces, tip side) is N 2734.6, V 3766.5 N. The screw bends in double curvature: M passes through zero near x' 29.6.
- **FE bending arm** M_max / V = 2726.1 / 3766.5 = **0.724 mm** (M28.6 / V 0.721) [DERIVED]. Sharp edge: (a'') 0.797, js5 0.796. CALC: 1.120 (0.920 + 0.2 for the break). The break shortens the FE arm. The BEAR resultant acts at x' 30.02, 1.42 mm from the plane, and the head contact reacts the rest of its moment.
- **Load balance.** 10 V = 37,665 N against 38,881 N applied: 0.969 (js5 0.965). The patch carries no cap pressure, and its boundary is js5's field. Inside the box the seat carries 12.6 N axially; js5's sharp hole-edge contact carried 136.3 N. Mechanical's scale-up (lead 10:24Z) is x 1.032, which gives V 3888.1 N and M_max 2814 N mm with the arm unchanged. The CALC moment is 3888.1 x 1.120 = 4355 N mm, so the FE moment is 35 % lower [DERIVED].
- FA1S has one instance in (b2). Its predecessor is SOAK70, as in every run. History robustness at FA1S is shown on the sharp edge ((a) vs js5: N -0.4 %, M -2.0 %), not on the broken edge.
- The lead RETAINED the CALC arm 1.120 mm (15:37Z (R2)), and the FE arm is information. At 1.120 the HW-101 u cell is +0.301. At mu 0.2, (b1) gives a longer FE arm, 1.047 mm, with a plane shear above the CALC V (10A.8, 10A.12).

**(b2) FA1S, TC-01 hole bearing** (V / (D t_eff), D 5.0; SF 1; Fbry / Fbru 330.5 / 407.4 MPa at 45.6 C) [DERIVED]:

| Basis | sigma_br (MPa) | MS y / u |
|---|---|---|
| FE V_plane 3766.5 N, t_eff 2.388 | 315.5 | +0.048 / +0.291 |
| FE BEAR contact resultant 3722.7 N, t_eff 2.388 (as posted) | 311.8 | +0.060 / +0.307 |
| FE V_plane, drawing-limit wall t_eff 2.365 | 318.5 | +0.038 / +0.279 |
| Mechanical CALC V 3888.1 N, t_eff 2.365 (240 (5)) | 328.8 | **+0.005 / +0.239** |

- The FE V is 3.1 % below the CALC V, so the CALC row governs and the FE confirms it. BEAR contact area 7.40 mm2 over x' 28.71-31.25.
- Under-head band (557.2 MPa at 1.00 mm from the hole, on the flat): Neuber n15 +0.609, n30 +0.516. This confirms (iii) (js5 n30 +0.518).

**(b2) FA1S, ligament station and TC-02 thread** [SIM]:
- Ligament station (12:52Z (2)). It starts at r 28.652, clipped 0.025 mm into the material, 0.0898 mm off the broken hole wall; length 2.81 mm. Pm 300.1 / 312.4, Pm+Pb 484.5 / 517.9 MPa (sides - / +). js5 (sharp), + side: 379.7 / 758.4. Information row (in-plane Kt; the local check is (iii)).
- The (i) half-ligament average is not re-posted on (b2). The sharp js5 value (Pm 104.1, Pm+Pb 201.6 MPa) stays quoted.
- TC-02 thread resultant (exact plane): N -2734.6 N along the screw, Vz 3766.5, Vt 8.1 N.

#### 10A.5.1 The broken-edge envelope (candidate)

`jfwd_envelope_b2.py` forms the (b2) envelope in the form of ruling 11:41Z (3): the highest screw N, the lowest seat window and the lowest MS per line, with M at the highest, over (b2)'s instances. It also forms the worst of that envelope and the sharp-edge one. The file `336568296bdb896f` is unchanged (record). The lead adopted the worst of the two as v3 `0872de4ea7e3601d` (15:37Z (R1)); v4 superseded it (2026-10-21T00:39:30Z (1); 10A.12). The table is the v3 record.

| State | (b2) N max | (b2) window min | (b2) line min | Sharp + (b2): N max | Window min | M28.6 max | Line min |
|---|---|---|---|---|---|---|---|
| PRELOAD | 3750.0 | 901.4 | +1.038 | 3750.0 | 901.4 (b2) | 744.8 (a'') | +1.038 (b2) |
| SOAK52 | 7764.0 (rep) | 1802.8 | -0.011 | 7764.0 (b2 rep) | 1332.0 (a) | 2915.7 (b2 rep) | -0.011 (b2) |
| SOAK | 6337.0 (rep) | 639.4 | -0.071 (rep) | 7382.9 (js5) | 639.4 (b2) | 3481.0 (js5) | **-0.071** (b2 rep); 2 lines negative |
| SOAK70 | 7471.8 | 3123.4 | -0.055 | 7471.8 (b2) | 1351.3 (a'') | 3111.7 (b2) | **-0.055** (b2) |
| FA1S | 2734.6 | 462.5 | +0.053 | 3147.9 (js5) | 462.5 (b2) | 2990.9 (a'') | +0.053 (b2) |

- FEA3D recommended the worst of sharp and (b2), because the drawing allows R0.1-R0.2 at the bore-side edge, between the two models. The lead adopted it as v3 (15:37Z (R1)).
- Mechanical re-mapped its IN718 rows on v3 (`jfwd_in718_rows_v352_v7` `6113d28b64d0dba5`, route (i)). The TC-01 y cell is now **-0.075** (SOAK seat line, (b2) rep, 3750 N). It was -0.039 on the sharp-edge envelope at 4096 N; the change combines the envelope, the 3750 N cap (17:56:12Z) and route (i). The N-based rows at SOAK70 / SOAK52 now come from (b2) / (b2) rep (10A.8, 10A.11).
- **(b1) seat_s9L12_mu02A** (mu 0.2, s9, physical order with the SOAK / SOAK52 repeats; deck `2b914daa78293c6f`; the held deck `e491b04b2b559c99` of `seat_s9L12_mu02` was not run) is the design-value run. It ran from 19:10:53Z to 00:28:31Z and was posted at 00:30:31Z (10A.12). It decides:
  - the slip state: the head slips at every step (T/N = mu), and the joint is bearing-type at FA1S (10A.7 (c));
  - the FE hole bearing with the break at mu 0.2: BEAR 3435.0 N, below the CALC V, so the CALC row still governs (10A.9);
  - the seat-line re-arbitration: (b1) lowers no seat-line minimum. Its only negative line is SOAK_rep -0.002 (d-6.051 z'0); the minimum stays -0.071 ((b2) rep).

### 10A.6 Mesh check (b2') against (b2); the mesh correction C1; the convergence check cD

- (b2') seat_s9L12_mu0 (deck `31678e81850ebee4`) is s9 (h_brk 0.15 / 0.3) at mu 0, the mesh of (b1). It ran 2026-10-21T00:33:57Z-01:17:13Z (2594.7 s, peak RSS 3.146 GB, rc 0) and was posted at 01:18:57Z: compare `0ae76ed185599268`, seatforce `722b28f49473b8dc`, shank `c402e74c125b5182`, lig_station `aa9fdb776e73f99d`; frd.gz `fb9878210f1176cb` (raw = decompressed `75db214df62fb11d`); folder peak 92.5 MB against 111.9 predicted [SIM].
- It is checked against (b2) on s6. Required agreement: within 5 % on the 54 lines, the screw sections, the seat force and footprint, and the hole bearing; otherwise (b1) is corrected by the s6 / s9 ratio at mu 0 and tagged DERIVED (240 (9)(v)). The test is the 5 % rule at PRELOAD and FA1S; the soak states join the envelope (lead 15:37Z (R3)).
- **Result: NOT within 5 %** at PRELOAD and FA1S (`jfwd/runs/seat_s9L12_mu0/judge_seat_s6L12_mu0.json` `3619a7b39613edf0`; numbers in 5.3) [DERIVED]. The P+Q rises with refinement; s6 is the higher on 47-53 of the 54 lines. (b2')'s soak states enter envelope v5; its minimum MS is above (b2)'s in every state.
- **C1, ADOPTED** (lead 2026-10-21T01:30:18Z (5); accepted 02:01:34Z (A)): MS_C1 = (1 + MS_b1) / max(1, r) - 1 per line and state, r = PmPb (b2) / PmPb (b2') at mu 0, floored at 1.00; the repeats take their state's ratio [ASSUMED]; DERIVED (`results/v352/jfwd_b1_meshcorr_v352.json` `adac16afd42ef7bd`, table `tables/jfwd_b1_meshcorr_v352.md` `8fed1d2a24e443b1`, script `jfwd_b1_meshcorr_v352.py` `2b7f28b06b0f4f58`). On the governing line d+6.051 z'0:

| State | r | (b1) as solved: PmPb MPa (MS) | (b1) C1: PmPb MPa (MS) |
|---|---|---|---|
| PRELOAD | 1.1781 | 186.1 (+1.579) | 219.2 (+1.189) |
| SOAK52 | 1.1244 | 329.3 (+0.091) | **370.3 (-0.030)** |
| SOAK52_rep | 1.1244 | 308.7 (+0.164) | 347.1 (+0.035) |
| SOAK | 1.1262 | 315.5 (+0.080) | 355.3 (-0.041) |
| SOAK_rep | 1.1262 | 314.8 (+0.082) | 354.5 (-0.039) |
| SOAK70 | 1.1235 | 309.5 (+0.105) | 347.7 (-0.016) |
| FA1S | 1.1194 | 395.2 (+0.195) | 442.4 (+0.068) |

- With C1, (b1) sets the SOAK52 seat-line minimum: **-0.030** ((b1) C1, PmPb 370.3 MPa; v4 -0.011 (b2)). The other state minima stand: SOAK -0.071 ((b2) rep), SOAK70 -0.055 (b2), FA1S +0.053 (b2), PRELOAD +1.038 (b2).
- **Resultants are as solved** (lead 01:30:18Z (5)). Beside them, as a disclosure, the mu 0 s6 / s9 ratio per state; only M at PRELOAD and SOAK would make a governing resultant more than 5 % more severe (M at x' 28.6 x 1.577 / x 1.741; M_max on the thread x 1.404 / x 1.476), and these come from small mu 0 moments. **The mu 0 M ratios are NOT applied to (b1)'s friction-driven moments** (lead 02:01:34Z (B)); Mechanical's screw fibre and LCF rows quote M as solved, with M x 1.404 (PRELOAD) and x 1.476 (SOAK) as information (10A.8).
- **MF note:** the seat-line P+Q is not shown converged (s9 -> s6 +12-18 % on the governing line); the s6 value is quoted as found (234 (4); lead 01:30:18Z (5b)). The two-mesh p = 1 / p = 2 estimate and C2 are information (5.3).
- **cD** (lead 02:01:34Z (C)): one mu 0 check finer than s6 on the governing line, built on the FINAL TC-01 (s6 + Ball h 0.04 mm at both line ends; 124,669 patch nodes; 5.3). Result rule per state on the governing line: within 5 % of s6 -> s6 and C1 stand; cD higher by more than 5 % -> cD governs and anchors the band, (b1) is re-based as C1' = cD / s9 per line and state (floored 1.00) on the lines cD refines, C1 elsewhere, and the cD - s6 difference is quoted as mesh + geometry; cD lower -> s6 stands and the difference is quoted. It ran 2026-10-21T03:18:46Z-05:09:25Z after js5b (6639.2 s, peak RSS 6.875 GB, rc 0) and was posted 05:10:18Z [SIM run record].
- **cD result, ACCEPTED** (lead 2026-10-21T05:17:36Z (1); `results/v352/jfwd_cD_result_v352.json` `8209e80f09f28af7`) [SIM; ratios DERIVED]:

| State | PmPb s9 / s6 / cD (MPa) | cD / s6 | Rule (C) | All 54 lines: cD / s6 max |
|---|---|---|---|---|
| PRELOAD | 199.9 / 235.5 / 218.4 | 0.927 | cD lower by more than 5 %: s6 stands (-7.3 %) | 1.035 |
| SOAK52 | 323.1 / 363.3 / 344.1 | 0.947 | cD lower by more than 5 %: s6 stands (-5.3 %) | 1.025 |
| SOAK | 324.1 / 365.0 / 352.7 | 0.966 | within 5 %: s6 and C1 stand | 1.041 |
| SOAK70 | 322.3 / 362.1 / 347.3 | 0.959 | within 5 %: s6 and C1 stand | 1.029 |
| FA1S | 400.5 / 448.3 / 441.7 | 0.985 | within 5 %: s6 and C1 stand | 1.036 |

- So s6 + C1 stand in every state: no line is above 1.05 x s6, and cD governs no line. The band anchors stay PRELOAD 235.5 / SOAK52 370.3 / SOAK 366.8 / SOAK70 362.1 / FA1S 448.3 MPa (lead 05:17:36Z (1)). cD's own line minima (MS +1.160 / +0.044 / -0.047 / -0.015 / +0.069) are above the envelope minima in every state. cD's lines are recorded beside the envelope lines (v6 `cD_check`), not entered.
- **MF note, with the numbers** (lead 05:17:36Z (2)): s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 % on the governing line; not monotonic; the mesh and the geometry change (cD is on the final d11.2 TC-01) are not split; the seat-line P+Q is NOT shown converged. The boundary extrapolation and the 9 sD nodes (5.3) are information.
- The patch judge's all-quantity 5 % test is information beside the rule [DERIVED]. Against (b2) (`judge_seat_s6L12_mu0.json` `eeb9067f1c3400db`) it passes at FA1S only. It fails on lines where cD is more than 5 % below s6 (Pm+Pb up to 7.3 % at PRELOAD and 5.3 % at SOAK52; Pm 5.1 % on one line at SOAK), and on the threaded-length M at mu 0, which is 5.9-20.4 % above s6 at PRELOAD / SOAK52 / SOAK / SOAK70 (small mu 0 moments; M at x' 28.6 +10.9 % at SOAK). Against (b2') (`judge_seat_s9L12_mu0.json` `beebcbed7eeb845c`) it fails in every state, as s6 did.
- **cD's resultants enter v6 as solved** (lead 05:17:36Z (3), by the rule fixed before the run; 10A.12). The first version of the result script checked one side of N and of the window only; the version used checks both (10A.12.2).

### 10A.7 RM2-01 addenda against the sub-model

- **(a)** The case Pm+Pb comes from the sub-model SCLs. FA1S TC-01: ligament Pm 104.1 / Pm+Pb 201.6 MPa. The "case Pm+Pb about +3.4" of v3.5.1 is withdrawn.
- **(b)** Preload treatment of the screws. The FA1S screw uses NASA-STD-5020A Eq. 22 with the preload omitted (240 (3)). Soak uses the 234 (1)(b) tension form. LC2 uses the combined form at the maximum preload (js5b, 10A.13; criterion per lead 2026-10-21T03:30:46Z (1)). See 10A.8.
- **(c) Slip.** Hand estimate at mu 0.2 on the js5 FA1S forces [DERIVED]: friction = 0.2 x (head 3138.2 + seat 1154.0) = 858 N per screw, against an FA1S shear of 3856 N per screw. **The joint slips into bearing at FA1S**, so the screws act as shear pins, and RM2-01 (c) holds (240 (2)). (b1), the only run with friction, confirms it (below).
  - LC1 retention is Mechanical's preload-retention check, not repeated here.
  - The FE slip state at mu 0.2 is (b1), posted 00:30:31Z [SIM]: the head-to-TC-01 friction ratio T/N is 0.195-0.202 at every step (= mu 0.2: the head is at the friction limit, slipping). At FA1S the head friction carries 600 N against V 4079 N at the shear plane: the joint is **bearing-type at FA1S at mu 0.2** (hole bearing 255.6 MPa), as Mechanical found for LC2 / FA1D / FA1U.
  - LC2 / FA1D / FA1U are bearing-type at any torque on Mechanical's numbers. Their FE rows are js5b's (10A.13), at mu 0, where the whole shear goes into bearing by construction (hole bearing V: FA1U 3562.7 N, FA1D 2825.1 N, LC2N 988.2 N) [SIM].
- **(d)** Geometry is the v3.5.2 joint: 10 x M5 at 18 + 36k deg, tap wall 1.906 mm, d10.5 spot face, wall 2.688 at the hole.
- **(e)** LC2 and FA1U / FA1D are in the js5b deck: s5, mu 0, IN718, 3750 N. It runs after (b2') (lead 15:37Z (R3), 18:50:09Z), with restricted contact output + FREQUENCY=1000. Its start gate is 1.86 + 1.25 x 197.6 MB + 0.10 = 2.190 GiB free; it started 2026-10-21T01:18:59Z at 2.36 GiB free, ran 7036 s (peak RSS 6.13 GB, rc 0), folder peak 186.3 MB against 197.6 predicted (-6 %), lowest free 2.158 GiB, posted 03:18:21Z (10A.13).
- **(f)** The hole-edge profile is replaced by the 54 seat lines and the ligament station. Every negative band within 3 mm of the hole sits at a contact or tie edge (lead 07:25Z).

### 10A.8 The screw

- **Ruling (240 (4)).** The J-FWD screw is IN718 M5 x 10, ENG-HW-101-IN718. A4-80 is withdrawn for J-FWD.
- **FA1S criterion** (240 (3)): 5020A Eq. 22, threads in the shear plane, preload omitted, V = 3888.1 N [CALC]. The bending arm is 1.120 mm (0.920 to the thread entry plus 0.2 for the break) until (b2) gives the moment with the break.
  - (b2) gives it: the FE arm on the R0.2 break is 0.724 mm (M_max 2726.1 N mm at x' 28.1 / V 3766.5 N), against 0.796 on the sharp edge (10A.5). The CALC arm is therefore conservative. The lead RETAINED the CALC arm 1.120 mm (15:37Z (R2)); the FE arm is information. At mu 0.2, (b1) gives 1.047 mm (10A.12).
  - **Eq. 22 inputs (lead 2026-10-21T01:30:18Z (6)).** Mechanical evaluates Eq. 22 at the larger of CALC and FE per resultant: V **4079.2 N** (FE, (b1) FA1S shear-plane V at mu 0.2, above the CALC 3888.1 N) and M **4354.7 N mm** (CALC, 3888.1 x 1.120; the FE maxima on the thread are lower: (b1) 4269.8, (b2) 2726.1 N mm) [SIM / CALC]. This is the hole-load rule max(as found, estimate). Mechanical's IN718 row on these inputs comes with its re-map on the final envelope [pending Mechanical]; until then the cell quotes the row below at V 3888.1 N.
  - Mechanical's IN718 row: **+0.301** (governing). With preload included: +0.082 (information). With the arm +0.4: +0.165 / -0.035 (sensitivity). Direct shear on the minor area: +0.933 / +1.408. Source: `jfwd_fix_v352_v2.json` via `jfwd_in718_rows_v352_v4.json` `6b41f1ce01e489f1`.
  - FE inputs behind it: exact N 3147.9, V 3750.2, M_max 2985 N mm on the thread (sharp arm 0.796 mm). Over the histories M_max is at most 2990.9 N mm.
  - Mechanical's CALC V (3888.1 N), which equals the FE applied load per sector, is used in place of the FE V.
- **Soak tension, IN718** (234 (1)(b), Mechanical v4 on the envelope): SOAK N 8110 N at 3750 N preload gives +0.757 / +1.088; at the 4096 N J-F1 maximum, N 8456 N gives +0.685 / +1.002. The A4-80 FE row at the FE N is -0.089, information only.
- **Fibre yield and bending.**
  - FA1S bending is primary. The thread-root fibre yield is information under 231 (inspect, or replace the screws, after any FA-1-class event).
  - Soak bending is secondary. It goes to Mechanical's relaxation model, shakedown and screw LCF.
  - Mechanical flags the IN718 soak fibre rows as negative: SOAK -0.257 at 3750 N and -0.305 at 4096 N; SOAK70 at 4096 N -0.046; SOAK52 -0.080. Mechanical asks for FE confirmation.
  - **Screw moments from (b1) (lead 2026-10-21T02:01:34Z (B)).** The mu 0 s6 / s9 M ratios are NOT applied to (b1)'s friction-driven moments. Mechanical's screw fibre and LCF rows quote M as solved; as information beside them, M x 1.404 (PRELOAD) and x 1.476 (SOAK), the mu 0 ratios of M_max on the thread (10A.6) [DERIVED, not applied].
- **TC-02 thread shear, IN718 (basis A_n 68.4, drawn M5 x 10.2; lead 13:14Z).**
  - Mechanical's v4 row (b), at the governing SOAK, js5 history: **+0.112 at 3750 N, +0.066 at the 4096 N J-F1 maximum** [CALC on the FE envelope]. My re-basing of Mechanical's A_n 63.48 row agrees (+0.111 / +0.066) [DERIVED].
  - The 63.48 row (+0.032 / -0.010) and the L 10.0 / ISO-tolerance checks (67.4 / 64.5 mm2) are in Mechanical's file. The 63.48 row is superseded as a report basis.
  - On the FE screw (A4-80) the same row is SOAK +0.221 / +0.357 (above).

### 10A.9 Mechanical's hand checks (i)-(iii) against the FE: confirms or refutes

Mechanical's TC-01 / TC-02 FA1S rows sit at the drawing-limit wall (2.665, L 2.365) and hold for any M5 grade (240 (4)) [CALC]. The FE values are on the sharp js5 geometry at the nominal wall 2.688 [SIM / DERIVED].

| Check | Mechanical CALC | FE (js5) | Verdict |
|---|---|---|---|
| (ii) TC-01 hole bearing | +0.005 / +0.239 (CALC V 3888.1, t_eff 2.365) | +0.233 / +0.519 (exact V 3603.6, t 2.688) | FE confirms; CALC conservative, CALC governs (240 (5)) |
| (i) TC-01 ligament Pm+Pb | +0.161 / +0.252 | +0.171 / +0.263 (half-ligament) | FE confirms, within 0.01 |
| (i) TC-01 Pm | +1.483 (Pm about 95 MPa) | +1.268 (half-ligament, worse side, Pm 104.1); full ligament 98.5 MPa, +1.397 | FE stress 3-9 % above the CALC; both far positive; the FE value is quoted |
| (i) TC-01 shear-out | +0.727 | Pm +0.952 (flank -) | FE confirms |
| (iii) TC-01 local (Neuber) | +1.384 (hole-edge Kt) | +0.518 (n 30) on the band: the under-head contact edge on the flat, 1.01 mm from the hole | different location; both positive; the FE value is quoted |
| (ii) TC-02 tap bearing | +1.385 / +1.940 | +2.115 / +2.839 (L_e 6.84) | FE confirms |
| (ii) TC-02 thread shear | +1.332 / +1.615 (at 3965 N) | +1.969 / +2.330 (A_n 68.4, N 3147.9) | FE confirms |
| (i) TC-02 shear-out Pm+Pb | not in the CALC set | +0.981 / +1.136 | FE only |
| (ii) TC-01 hole bearing, broken edge | +0.005 / +0.239 | (b2): +0.048 / +0.291 (V_plane 3766.5, t_eff 2.388); +0.038 / +0.279 at t_eff 2.365 | FE confirms; CALC governs |
| (iii) TC-01 local, broken edge | +1.384 | (b2): n30 +0.516, n15 +0.609 (band, 1.00 mm from the hole) | FE confirms; the FE value is quoted |
| (ii) TC-01 hole bearing, broken edge, mu 0.2 | +0.005 / +0.239 | (b1): BEAR contact 3435.0 N: 255.6 MPa, +0.293 / +0.594 (t 2.688); 287.7 MPa, +0.149 / +0.416 (t_eff 2.388) | FE confirms; CALC governs (lead 01:30:18Z (6)) |
| Screw arm (Eq. 22 input), broken edge | 1.120 mm | (b2): 0.724 mm; (b1) mu 0.2: 1.047 mm | CALC conservative; RETAINED (15:37Z (R2)) |
| (i) TC-01 ligament Pm+Pb at LC2 (IN718, js5b) | no CALC parts row at LC2 | FE-factored: LC2Y +0.421 (y), LC2U +0.424 (u); hand form LC2N +0.016 / -0.183, LC2M +0.266 / +0.021 | FE-factored = criterion, hand form = information (rule (A) ADOPTED, lead 2026-10-21T03:30:46Z (1); 10A.13) |
| Screw at LC2 (234 (1)(b) form, IN718 FE) | Mechanical's LC2 screw rows are A4-80 (`jfwd_preload_v352_v2`), superseded for J-FWD by 240 (4) | LC2N +1.894 / +2.110, LC2M +2.218 / +2.394 (N 3984.6 / 3366.1 N, V 1033.5 / 1031.8 N) | FE row = criterion (rule (1)); far positive |

- **On FA1S, the FE refutes none of Mechanical's hand checks**, on the sharp edge (js5) or on the R0.2 break ((b2)).
- **At LC2 (js5b, IN718)** no hand check of Mechanical's is refuted either: the parts rows are FE-only, and on the adopted rule (FE-factored criterion) they stay above +0.42. The hand form (SF on the total stress, preload included) is shown as information; it reaches -0.183 on the TC-01 ligament at LC2N.
- On two rows (TC-01 Pm, and the local Neuber at a different location) the FE margin is lower than the CALC margin. The FE value is quoted there; both stay positive.
- The governing FA1S joint cells are therefore:
  - TC-01 hole bearing, CALC: +0.005 / +0.239.
  - Screw, CALC: +0.301 on IN718.
- The (b2) bearing with the break and the (b1) bearing at mu 0.2 (posted 00:30:31Z) are in the table above. At mu 0.2 the shear-plane V (4079.2 N) is above the CALC V, but the load carried in bearing (BEAR resultant 3435.0 N) is below it; the hole bearing stays on the CALC row, +0.005 / +0.239 (lead 01:30:18Z (6)). The V 4079.2 N enters Eq. 22 (10A.8).
- **Soak (secondary) states.** Mechanical's IN718 seat-line rows are negative, the same as the FE found on A4-80: SOAK70 -0.022, SOAK -0.037 (P+Q, F_sh form); the head-force bound is -0.082 / -0.098. These rows are the open negatives of 240 (10).
  - The re-arbitration on the broken edge, (b2), makes them worse, not better. On A4-80 at 3750 N the seat line reaches SOAK -0.071, SOAK70 -0.055 and SOAK52 -0.011 (sharp envelope -0.035 / -0.019 / +0.034). It is also history-dependent (10A.5).
  - The rows wait for Mechanical's IN718 re-mapping on the final envelope (10A.12) and the slack fix (disc spring, or open plus the preload-retention audit).

### 10A.10 Not run, and open

- Not run by ruling (section 11): the J-FWD spring-footprint run (route (i) flat bearing under the screw head) and c71x, which ran only if space appeared after js5b; the tail F ended 2026-10-21T03:18:21Z with both NOT RUN (lead 18:50:09Z (5)).
- A history-robust contact model (for example mortar contact, or a softened penalty at the ring) is not run and not proposed for this schedule. The soak states therefore stay the worst computed instances, not a proven bound (lead 15:37Z).
- Nominal-preload FE (3000 N): not run (the lead set 3750 N, the J-F1 cap). Lower-preload rows are Mechanical's joint model.
- Mesh convergence of the seat-line P+Q is not shown (MF note, 10A.6 and 5.3). cD, the one finer check, ran on the FINAL TC-01: s6 + C1 stand (cD / s6 0.927-0.985 on the governing line), and the trend s9 -> s6 -> cD is not monotonic. No further refinement is run.
- Open negatives (secondary, class DC): the SOAK70 / SOAK / SOAK52 seat-line P+Q on the final envelope (v6, seat lines as v5: SOAK70 -0.055 ((b2)), SOAK -0.071 ((b2) rep), SOAK52 -0.030 ((b1) at C1)) [SIM / DERIVED, A4-80 FE]; Mechanical's IN718 seat / ring line rows (SOAK -0.075 at 3750 N, mapped on v3) and the IN718 soak fibre rows. Owner: Mechanical (single IN718 re-map and the select-fit band re-size on the final envelope v6 with `jfwd_v7inputs_cD_v352.json`, relaxation, shakedown, LCF; 240 (10)).

### 10A.11 The J-FWD column of the margin matrix

Built by `margin_matrix_v352.py` `jfwd_cells()` (section 3; run 2026-10-21T03:33:37Z on v5 and, the second and last time, 05:22Z on the final envelope v6 `43a5d78b67c615fc` (lead 03:30:46Z (5), 05:17:36Z (4)), with C1 and the LC2 rule of 03:30:46Z (1)). The cell is the minimum over the criterion rows. Information rows are listed beside it and do not enter the minimum: PRELOAD, the ligament station, all-node and elastic-band values at contact or tie edges, A4-80 screw rows, head-force bounds, fibre yield, the js5b screw FE rows beside Eq. 22, and the LC2 hand-form parts rows. Mechanical's IN718 rows are at the 3750 N J-F1 cap, which governs (lead 17:56:12Z); the 4096 N rows are information.

| Member | Cell y / u | Governing row (y; u) |
|---|---|---|
| TC-01 | **-0.075** / +0.239 | y: SOAK seat line d6.051 z'0 P+Q <= 2 Fty(T), F_sh form, IN718 at 3750 N, history (b2) rep (Mechanical v7, mapped on v3; the FE envelope minimum on the final envelope is SOAK -0.071 ((b2) rep) and SOAK52 -0.030 ((b1) at C1)). u: FA1S hole bearing CALC at the drawing-limit wall, V 3888.1 N (240 (5)). Class DC, see 10A.9 |
| TC-02 | +0.045 / +0.162 | SOAK52 thread shear on THE ROW A_n 67.93 (route (i): M5 x 10.7 + HW-170 spring, L_e min 7.294), IN718 at 3750 N, N 8572.2 N ((b2) rep), 94.9 C |
| HW-101 | +0.650 / +0.301 | y: SOAK52 tension on A_s (234 (1)(b)), IN718 at 3750 N, N 8572.2 N ((b2) rep), 154.1 C. u: FA1S 5020A Eq. 22, preload omitted, arm 1.120 mm (CALC, RETAINED) |

- LC2 rows (js5b, rule 03:30:46Z (1); 10A.13): TC-01 LC2Y +0.421 (y) and LC2U +0.424 (u), ligament Pm+Pb; TC-02 +1.330 / +1.633 (A_n thread shear); HW-101 LC2N +1.894 / +2.110 and LC2M +2.218 / +2.394 (234 (1)(b) form) [SIM / DERIVED]. None governs a cell. Information beside them: the hand form at LC2N / LC2M, TC-01 ligament Pm+Pb **+0.016 / -0.183** (LC2N) and +0.266 / +0.021 (LC2M), labelled "hand form: SF on the total stress including preload, linear superposition ASSUMED".
- FA1U / FA1D rows (js5b, criterion 231 (1)): TC-01 +0.222 / +0.318 and +0.257 / +0.355, TC-02 +1.449 / +1.641 and +1.597 / +1.853; bounded by FA1S. The js5b screw FE rows are information beside Eq. 22 (240 (3)).
- Pending in the column: Mechanical's single IN718 re-map and the select-fit band re-size on the final envelope v6 (inputs `jfwd_v7inputs_cD_v352.json`, lead 05:27Z (3)), with Eq. 22 at V 4079.2 N (FE, (b1)) and M 4354.7 N mm (CALC) (lead 00:39:30Z (1), 01:30:18Z (6)). The TC-01 flat-bearing row is Mechanical's IN718 row on A_ROW 38.171 mm2 (rows v5).
- Neither re-run changed a cell: v5 (03:33:37Z) against the 00:50Z table, and v6 (05:22Z) against the v5 table, whose run changes only the envelope file name and sha in the sources and the texts (cell and value diff over every part and column) [DERIVED].

### 10A.12 (b1): s9 R0.2, mu 0.2, physical order with SOAK / SOAK52 repeats (posted 2026-10-21T00:30:31Z)

Run `jfwd/runs/seat_s9L12_mu02A` (ccx 19,057 s, peak RSS 6.46 GB, rc 0; 7 post steps rc 0; frd gzipped lossless, raw 30d065222690795d = decompressed, gz 97f77ab30c5f432f; folder peak 146.4 MB against 149.9 predicted; lowest free 2.360 GiB) [SIM].

| step | N plane (N) | V plane (N) | head T/N | seat normal on TC-02, radial sum (N) | seat lines P+Q min (patch) |
|---|---|---|---|---|---|
| PRELOAD | 3750.0 | 748.5 | 0.200 | 1273.9 | +1.423 |
| SOAK52 | 4801.9 | 949.4 | 0.198 | 620.9 | +0.036 |
| SOAK | 6554.3 | 1324.6 | 0.202 | 2433.0 | +0.014 |
| SOAK70 | 5614.0 | 1096.5 | 0.195 | 1493.5 | +0.039 |
| FA1S | 2963.9 | 4079.2 | 0.196 | 1083.9 | +0.147 |
| SOAK_rep | 6515.1 | 1314.5 | 0.202 | 2391.1 | **-0.002** (1 line) |
| SOAK52_rep | 5600.5 | 1090.7 | 0.195 | 1493.4 | +0.095 |

- History check (5 % rule): SOAK_rep against SOAK within 1 % (N -0.6 %, V -0.8 %, M -1.0 %). SOAK52_rep against SOAK52 fails it (N +16.6 %, V +14.9 %, M at the shear plane -88 %): the soak state depends on its predecessor at mu 0.2 as at mu 0, so the instances are carried separately.
- FA1S TC-01: under-head band vM 491.3 MPa (n80299), hole bearing 255.6 MPa; information beside Mechanical's CALC criterion rows (the TC-01 FA1S MF cell stays +0.005 / +0.239, lead 21:47:29Z (3)).
- **Envelope v4** (`results/v352/jfwd_soak_envelope_v352_v4.json` 9d9fd8ee991f9887, script `scripts/jfwd_envelope_v4.py` c10fe68a8fcb1f5e; ADOPTED by the lead 2026-10-21T00:39:30Z (1), superseding v3 0872de4ea7e3601d) = v3 + the (b1) instances [DERIVED]. (b1) sets the screw bending at x' 28.6: PRELOAD 2,517 (v3 745), SOAK 5,079 (v3 3,481), FA1S 4,240 (v3 2,991) N mm, and the SOAK52 window minimum 630 N (v3 1,332). Screw N maxima and the seat-line P+Q minima are unchanged (worst SOAK -0.071, (b2) rep). Mechanical's IN718 screw rows are mapped on v3; on v4 the bending rises by up to 46 % (SOAK), so the HW-101 rows need Mechanical's re-mapping on the final envelope.
- **Envelope v5** (`results/v352/jfwd_soak_envelope_v352_v5.json` `ef22b59cf2413b46`, script `jfwd_envelope_v5.py` `18886bbde22e1493`; lead 2026-10-21T01:30:18Z (3), 02:01:34Z (E); ACCEPTED 03:30:46Z (3) as final unless cD moves a quantity; superseded by v6) = v4 + the (b2') instances, with (b1)'s 54 seat-line stresses at their C1 values; (b1)'s resultants as solved [DERIVED]. js5b raises no envelope quantity: its only envelope state is PRELOAD (N 3750.0 N, window 1114.8 N, M 98.8 N mm at x' 28.6 and 300.5 N mm on the thread), inside v5 (record `js5b_check` in the file). The changes against v4 are in 10A.12.2.
- **Envelope v6, FINAL** (`results/v352/jfwd_soak_envelope_v352_v6.json` `43a5d78b67c615fc`, script `jfwd_envelope_v6.py` `ac75b2c41146aead`; lead 2026-10-21T05:17:36Z (3), by the rule fixed before the run: any envelope quantity moved -> v6 final, 02:01:34Z (E), 03:30:46Z (3)) = v5 + cD's resultants as solved, as an instance like (b2') [SIM / DERIVED]. cD moves three envelope values: SOAK70 seat window maximum 3123.4 ((b2)) -> **3151.1 N**, FA1S screw N minimum 2734.6 ((b2)) -> **2728.5 N**, FA1S seat window minimum 462.5 ((b2)) -> **455.0 N**. Recorded per instance for Mechanical, outside the envelope block: the SOAK70 threaded-length M maximum 3013.4 ((b2')) -> 3095.9 N mm (cD), and the new record `M_max_shank_in_TC01_Nmm`, whose SOAK70 maximum moves from 3415.2 ((b2), Mechanical's v7 input) to 3438.9 N mm (cD), both at x' 30.5. cD's seat lines are not entered (record `cD_check`; the (C) rule keeps s6 + C1), so the seat-line values, the minima and the band anchors are those of v5. The screw N maximum, M at x' 28.6 and `js5b_check` are unchanged. The lead diffed the states of v5 against v6 (05:22Z): the envelope block changes in exactly these three values; the rest are added (cD) entries.

#### 10A.12.1 Final-envelope inputs in Mechanical's v7 quantities (lead 2026-10-21T01:01:13Z)

Mechanical's v7 relaxation inputs (`04-fea/v352/jfwd_relax_v352_v7.json` `345e27062d54ad20`) are re-extracted per instance from the FE runs, read-only, fit 0.078, no new run [SIM values; DERIVED envelopes]. Step 1 reproduces v7's history envelope and cross-check exactly (extraction check). v7 holds js5, (a), (a'), (a''), (b2) and (b2) rep; added: (b1), (b1) rep and (b2').
- Files, as solved: `results/v352/jfwd_v7inputs_v352.json` `753431eb50f36f58`, `tables/jfwd_v7inputs_v352.md` `fdc96347e9a87025`, script `jfwd_v7inputs_v352.py` `653e00189c5c52fc` (unchanged since they were cited).
- Files, with the C1 view of the seat line (lead 01:30:18Z (5)): `results/v352/jfwd_v7inputs_c1_v352.json` `384c1a472add7a4c`, `tables/jfwd_v7inputs_c1_v352.md` `95a3062c633ad229`, script `jfwd_v7inputs_c1_v352.py` `a731440e64361e4f` (a copy, so the cited files stay as they were).
- The inputs that move against v7 (v7 convention, as solved): M_max on the thread PRELOAD 823.6 -> 2530.8 ((b1)), SOAK 3855.3 -> 5116.3 ((b1)), FA1S 2990.9 -> 4269.8 N mm ((b1)); SOAK52 head force minimum 5826.2 -> 4802.0 N and seat window 1332.0 -> 630.2 N ((b1)); under-head band strain MS PRELOAD 7.083 -> 6.345, SOAK 0.738 -> 0.502 ((b1)); SOAK70 head force minimum 5623.6 -> 5613.8 N.
- With C1, one more input moves: the SOAK52 seat line d+6.051 z'0, PmPb 363.3 -> 370.3 MPa, MS -0.011 -> **-0.030** ((b1) C1). The other state minima stand: PRELOAD +1.038, SOAK70 -0.055, SOAK -0.071 ((b2) rep), FA1S +0.053, all (b2).
- (b2') moves no v7 input and no value of the envelope block (screw N, seat window, M at x' 28.6, seat-line minima): its seat-line MS is above (b2)'s in every state. It does set one per-instance maximum outside that block: M on the threaded length at SOAK70, 3013.4 against (b2) 2912.3 N mm (+3.5 %; delta table 10A.12.2); v7's M at x' 30.5 stays (b2) 3415.2 N mm in v5 (lead 2026-10-21T03:30:46Z (3)); cD moves it in v6 (next bullet) [DERIVED].
- **With cD, on v6 (lead 2026-10-21T05:27Z):** `results/v352/jfwd_v7inputs_cD_v352.json` `5a41c8d74897bdda` (table `tables/jfwd_v7inputs_cD_v352.md` `424146c89c8c9f01`, script `jfwd_v7inputs_cD_v352.py` `0cc1c2bf2d3f0092`; the cited v7inputs files are untouched) is Mechanical's re-map input record together with v6 (05:27Z (3)). Resultant-type inputs take cD as an instance as solved (05:27Z (2)): SOAK70 M_max 3415.2 ((b2)) -> **3438.9 N mm** (cD, x' 30.5); FA1S N_head minimum 2723.1 -> **2717.2 N**, seat window 462.5 -> **455.0 N** and spread_N_rel 0.1524 -> 0.1549 (cD). Local values keep the base (05:27Z (1)): the SOAK52 under-head band strain MS stays **0.296** ((b2)) with cD's 0.267 beside, labelled 'cD refined-mesh local value beside, strain ratio 1.023, within the (C) 5 % band; the MF note applies'; the seat line keeps the C1 view. PRELOAD, SOAK and every other v7 input stand. The datasheet J-FWD table shows the UH row as '0.296 (s6), cD 0.267 beside' (05:27Z (3)) [SIM values; DERIVED].

#### 10A.12.2 The final envelope v6 against v4 and v5 (delta tables)

v6 against v4: `results/v352/jfwd_envelope_delta_v352_v6_vs_v4.json` `95e6eeee99e8196d` (table `tables/jfwd_envelope_delta_v352_v6_vs_v4.md` `c4601df48055b8fb`); v6 against v5: `results/v352/jfwd_envelope_delta_v352_v6_vs_v5.json` `3844deef9c385a74` (table `545602a9d07129d2`); v5 against v4 (ACCEPTED 2026-10-21T03:30:46Z (3)): `results/v352/jfwd_envelope_delta_v352_v5_vs_v4.json` `a8c6aa69742fba5f` (table `de87c19ffedaba26`, written by the script version `32212446a8469f7c`) [DERIVED]. The v6 files carry the note (lead 05:17:36Z (3)) that the first version of the cD result script checked one side of N and of the seat window only (N maximum, window minimum) and missed the SOAK70 window maximum and the FA1S N minimum; the version used checks both sides.

| State | Quantity that changed | v4 (from) | v5 (from) | v6 (from) |
|---|---|---|---|---|
| SOAK52 | seat-line minimum, line d+6.051 z'0 | -0.011 ((b2)) | **-0.030** ((b1) at C1) | -0.030 ((b1) at C1) |
| SOAK70 | seat window maximum | 3123.4 N ((b2)) | 3123.4 N ((b2)) | **3151.1 N** ((cD)) |
| SOAK70 | M on the threaded length, maximum over the instances (outside the envelope block) | 2912.3 N mm ((b2)) | 3013.4 N mm ((b2'); +3.5 %) | **3095.9 N mm** ((cD)) |
| FA1S | screw N minimum | 2734.6 N ((b2)) | 2734.6 N ((b2)) | **2728.5 N** ((cD)) |
| FA1S | seat window minimum | 462.5 N ((b2)) | 462.5 N ((b2)) | **455.0 N** ((cD)) |
| all | largest spread of a line's MS over the instances | PRELOAD 1.885, SOAK70 0.427, SOAK 1.013, SOAK52 0.637, FA1S 0.557 | 1.688, 0.504, 0.994, 0.676, 0.461 | as v5 |

- Unchanged in every state from v4 to v6: the screw N maximum, M at x' 28.6, the number of negative lines (SOAK70 1, SOAK 2, SOAK52 1), and the seat-line minima other than SOAK52 (SOAK -0.071 (b2) rep, SOAK70 -0.055 (b2), FA1S +0.053 (b2), PRELOAD +1.038 (b2)). v5 -> v6 moves no seat line (0 lower / 0 higher / 54 equal in every state).
- Seat lines whose envelope MS is lower in v5 and v6 than in v4 / higher / equal (3 decimals): PRELOAD 21 / 0 / 33, SOAK70 15 / 0 / 39, SOAK 21 / 0 / 33, SOAK52 23 / 0 / 31, FA1S 34 / 0 / 20. The lower lines come from (b1) at C1 (20, 13, 20, 23, 32) and (b2') (1, 2, 1, 0, 2). The largest drops: PRELOAD d-7.607 z'+1.5 +1.902 -> +1.653; SOAK70 d-6.570 z'-1.5 +0.500 -> +0.346; SOAK d-7.607 z'+1.5 +0.202 -> +0.110; SOAK52 d-6.570 z'-1.5 +0.401 -> +0.330; FA1S d-8.126 z'0 +0.930 -> +0.839.

### 10A.13 js5b: s5, mu 0, IN718 screw, FA1U / FA1D / LC2 (posted 2026-10-21T03:18:21Z)

Run `jfwd/runs/js5b_in718_mu0_T3750_g078_cf` (deck `0d852f10082883e8` = the IN718 source stream, raw `fd5c555220cab427`, with restricted contact output + FREQUENCY=1000; ccx 7036 s, peak RSS 6.13 GB, rc 0; 11 posts and cite_guard rc 0; frd gzipped lossless, raw `e1f1f39a98425547` = decompressed, gz `a7c3c22d985ff327`; folder peak 186.3 MB against 197.6 predicted (-6 %); lowest free 2.158 GiB) [SIM]. **Hand fix** (ACCEPTED lead 2026-10-21T03:30:46Z (4)): the stage ran `jfwd_cells.py` before `jfwd_spotface.py`, so the first cells posts had no hole-bearing rows; both cells posts were re-run by hand after spotface (`cells_v352An.json` `d25745ca0ff96cb5`); only the hole-bearing entries changed (`runs/post_js5b.log`). Rows: `results/v352/jfwd_js5b_rows_v352.json` `91278d6b039c5b27` (script `jfwd_js5b_rows_v352.py` `41f1d46ca5457f1e`).

**Joint forces** (exact shear-plane resultants; bearing = the contact resultant on the hole) [SIM]:

| Step | Load | Screw N (N) | V plane (N) | Bearing V (N) | M_max on the thread (N mm, at x') | Seat window (N) |
|---|---|---|---|---|---|---|
| PRELOAD | 3750 N, 20 C | 3750.0 | 0.2 | 0.1 | 300.5 (28.3) | 1114.8 |
| FA1U | 147 bar abs, 45.6 C | 3517.2 | 3718.6 | 3562.7 | 2416.0 (27.3) | 1485.1 |
| FA1D | 121 bar abs, 45.6 C | 3581.7 | 2958.9 | 2825.1 | 2984.7 (28.6) | 1425.3 |
| LC2U | 45 bar x 2.0, 78.6 C | 3857.4 | 2160.8 | 2044.7 | 2455.8 (28.6) | 1501.5 |
| LC2Y | 45 bar x 1.5, 78.6 C | 3911.9 | 1611.2 | 1514.6 | 1988.5 (28.6) | 1452.8 |
| LC2N | 45 bar x 1.0, 78.6 C | 3984.2 | 1062.6 | 988.2 | 1511.2 (28.6) | 1422.3 |
| LC2M | 45 bar x 1.0, GVLO B1_21.65 field | 3366.0 | 1065.2 | 995.4 | 1912.6 (28.6) | 1423.3 |

**Rows and their treatment** (lead 2026-10-21T03:30:46Z (1); MS_y / MS_u) [SIM / DERIVED]:

| Step | Form (SF) | TC-01 ligament Pm+Pb | TC-01 hole bearing | TC-01 band Neuber n30 | TC-02 231 (1) cell | Screw IN718 FE | Treatment |
|---|---|---|---|---|---|---|---|
| FA1U | FA1 (1.0) | +0.222 / +0.318 | +0.247 / +0.537 | +0.403 | +1.449 / +1.641 | +1.070 / +1.287 | parts criterion (231 (1)), bounded by FA1S; screw information beside Eq. 22 (240 (3)) |
| FA1D | FA1 (1.0) | +0.257 / +0.355 | +0.573 / +0.938 | +1.231 | +1.597 / +1.853 | +1.641 / +1.724 | as FA1U |
| LC2Y | FE-factored x1.5 (1.0) | **+0.421** / - | +1.871 / - | +3.070 | +1.330 / - | +1.919 / +2.534 | parts: yield slot (criterion); screw information |
| LC2U | FE-factored x2.0 (1.0) | - / **+0.424** | - / +1.605 | - | - / +1.633 | +1.583 / +2.145 | parts: ultimate slot (criterion); screw information |
| LC2N | hand form (1.5 / 2.0) | +0.016 / **-0.183** | +1.933 / +1.695 | +5.146 | +0.526 / +0.276 | **+1.894 / +2.110** | parts INFORMATION (hand form: SF on the total stress including preload, linear superposition ASSUMED); screw criterion (234 (1)(b)) |
| LC2M | hand form (1.5 / 2.0) | +0.266 / +0.021 | +1.952 / +1.723 | +6.441 | +0.793 / +0.496 | **+2.218 / +2.394** | as LC2N |
| PRELOAD | soak | - | - | +9.322 | thread A_n +1.526 / +1.845 | +2.910 / +3.693 | information (240 (9)) |

- **Basis of the LC2 rule (lead 2026-10-21T03:30:46Z (1)).** The external load is factored, the preload is not (NASA-STD-5020A practice [LITERATURE, AS RECALLED]; 234 (1)(b) for the screw). The FE-factored steps solve the factored state with contact at the 3750 N maximum preload, the J-F1 cap (line 245) and the physical upper bound. The hand form puts SF 2.0 on the preload share as well: of the LC2N ligament Pm+Pb 151.6 MPa, about 129.2 MPa is the zero-pressure intercept of LC2N 151.6 / LC2Y 162.6 / LC2U 174.0 MPa at x1.0 / x1.5 / x2.0 [DERIVED; linearity ASSUMED; reproduced by the lead]. The hand-form rows stay visible as information.
- **Effect on the matrix:** none of the J-FWD cells moves (TC-01 -0.075 / +0.239, TC-02 +0.045 / +0.162, HW-101 +0.650 / +0.301; 10A.11).
- **Bearing at mu 0:** the whole shear goes into bearing by construction. The FA1U bearing V 3562.7 N lies below the FA1S js5 3603.6 N and the CALC 3888.1 N; the CALC row governs (10A.9). The screw moments on the thread (at most 2984.7 N mm, FA1D) lie below the Eq. 22 CALC M 4354.7 N mm.
- **Screw rows** are on engmat's AMS 5662 / 5663 bar minimums (engmat v1.6 snapshot `snap/engmat_v1p6`, hub 04-fea/src `46ba163b864c7fc5`, with engmat's own tags); the fastener allowables are Mechanical's (240 (4)).
- The ruling also puts the LC2N / LC2M parts rows into the datasheet's J-FWD table as information under the same label (07-datasheet, not an FEA3D file; lead 03:30:46Z (1)). The source for that table is this one and `jfwd_js5b_rows_v352.json`.

## 10B. Thermal joints on the gap-conductance variant (item 5b; REV-MECH-2 RM2-13 corrections 1-6)

Files (FEA3D): re-posts `results/v352/repost_5b_lc1v352g.json` (GVLO, `73905ef3358f8fa0`), `repost_5b_lc1v352h.json` (GVHI, `cc652bed59e6df9d`), `repost_5b_lc1v352.json` (the v3.5.1 merged map on the v3.5.2 model, information, `5933a932139c379d`); tables `results/v352/tables/repost_5b_v352.{md,json}` (A-H; `7a5917eb5a009de7` / `b166a4a470feba03`); the instant of the S-AX TC-02 maximum `results/v352/tc02_t215_v352.json` (`32a307a481fb05d8`); merged-map surrogate check `results/v352/merged_surrogate_check_v352.json` (`3785d3e1dcb29269`); tie census `results/v352/tb1_tie_census_v352.json` (`2e532f14d3f20561`); fit dT `results/v352/fit_dT_sax_v352.json` (`93d87757edbcdcaf`) and the land-A closure `results/v352/landA_closure_gvhi_v352.json` (`7754f21e2910220a`). Scripts: `repost_5b_v352.py`, `repost_5b_tables_v352.py`, `tc02_t215_v352.py`, `merged_surrogate_check_v352.py`, `tb1_tie_census_v352.py`, `fit_dT_sax.py`, `landA_closure_gvhi.py`. Thermal sources (Mechanical, read-only): index `04-fea/v352/gapvar_fields_v352_v2.json` (`f60394c3f096c946`); S-AX `L1_thv352_NF2b_GVLO_r10free_cad352` (mesh `c1b81a9aea53d395`) and `L1_thv352_NF2b_GVHI_r10free_cad352` (mesh `0fb90c125e228f23`).

All FE values are [SIM] (3-D linear elastic, mapped S-AX fields, TC-02 / TC-03 rev 3 per the lead 05:42Z); rows built from them are [DERIVED]. MS at SF 1.5 yield / 2.0 ultimate on the total stress at node temperature; LC1 and LC2 with 4 lateral sub-cases each (node-wise envelope); the four burn states B1_21.65 / B1_19 / B1_2 / B1_1. Nothing here is physical approval.

### 10B.1 Question, bounds and status

- Brief item 5b: re-map the gap-conductance variant and re-state the TC-03 corner (total and primary), the TC-02 seat rows and the TC-02 maximum on it, taking for each part the bound that is conservative for it; the merged-node field stays the perfect-contact bound. State whether my 3-D model ties or merges the two interfaces structurally. Line 234 (7) adds the RM2-13 corrections 1-6.
- Bounds:
  - **GVLO** (low conductance, widest hot gaps; J1 fit at the drawing maximum 0.078 mm): lc1v352g, solved and re-posted. The lead ruled on it at 07:51Z (239 (4)).
  - **GVHI** (high conductance; J1 at the drawing minimum 0.040 mm, k_gas x1.5): lc1v352h, solved in chain E and re-posted. The 5b posts were re-run after the lossless repack and are byte-identical (lead 16:20Z (2), P2).
  - **Merged (perfect contact)**: no LC1 was solved on the v3.5.2 NF2b merged field. The interim run lc1v352 maps the v3.5.1 merged field `L1_thv351_TB1GC_cad351` on the v3.5.2 model. On TC-02 and TC-03 it reproduces the v3.5.2 merged field: largest difference 3.3 K, 95th percentile 0.03 K, 0.0-0.3 K at the TC-03 corner and the TC-02 seat, at all four states (table G) [DERIVED]. It therefore stands for the perfect-contact bound on TC-02 / TC-03 (information). On NZ-01 it does not (N-F2b changed the shoulder: up to 44 K), and no surrogate claim is made there.
- The S-AX variant runs are 'r10free': the S-AX z-tie on the r-10 clearance is released, as the CAD has it.

### 10B.2 Correction 1: the inherited closure (disclosure)

- The v3.5.1 report's mapped temperatures (its sections 2.2, 4.1 and 4.2) inherit the S-AX 0.10 mm thermal-mesh closure (`ax_thermal.py` TOL_MM) at two designed clearances:
  - the **TC-03 flange OD**: the Ø20.0 flange in the Ø20.2 TC-02 counterbore, **0.10 mm radial**, no fit given (0.103-0.109 mm at the four states from the mapped temperatures and the CTEs; it does not close in operation, RM2-13 (a));
  - the **TC-01 / TC-02 fit, bore 57.25 H8 on plug 57.20 f7**: radial 0.025 mm at the basic sizes, 0.040-0.078 mm toleranced.
- The v3.5.1 TC-03 corner (-0.312 / -0.375) and TC-02 seat (+0.096 / -0.119) values depend on both closures. They stay in the v3.5.1 record with that dependence and are superseded for v3.5.2 by this section. Section 2 carries the same disclosure for the v3.5.2 configuration.

### 10B.3 Corrections 2 and 4: what my 3-D model ties (census in the record)

The question "does the 3-D model tie or merge these two interfaces structurally" has this answer for v3.5.2 [SIM model data, `tb1_tie_census_v352.json`; the LC1 model built exactly as lc1v352g, no solve]:

| Interface | v3.5.2 production model ('design' ties, TB1 **'thread'**, tiex) | v3.5.1 production model (record, RM2-13 (c)) |
|---|---|---|
| TC-03 / TC-02 shoulder (z 107.513) | **tied**, TC03_TC02_shoulder 'zt' (axial + tangential, radial free): 250 dependent TC-03 nodes, 212 with equations (38 far nodes skipped by tiex), 424 equations, all on the one plane z 107.513, r 6.93-10.00. The 29 nodes at r 9.9-10.0 are the outer edge of the flange's aft face on the shoulder, not nodes of the OD cylinder. | 'faces': TC03_TC02_seat 'zt', tolerance 0.12 mm: 183 shoulder nodes |
| TC-03 / TC-02 M14 engagement (r 7.0) | **tied**, TC03_TC02_thread 'zt': 588 dependent nodes, 547 with equations, 1094 equations, r 6.90-7.00, z 107.51-117.51 | tied (shoulder + thread in the 'thread' variant) |
| TC-03 flange OD (r 10.0) to the r 10.1 counterbore, 0.10 mm design gap | **free**: no dependent node off the shoulder plane at r > 9.9 mm | **46 of 320 OD nodes tied across the gap** (the 0.12 mm tolerance exceeds the 0.10 mm gap; the L1 counterbore's 11 facets cut 0.31 mm into the flange) |
| TC-03 end face z 117.51 | **free**, except its outer edge circle (44 nodes at r 6.90-7.00), which belongs to the thread cylinder | 71 end-face nodes tied |
| TC-01 / TC-02 f7 / H8 fit | **no tie and no contact** in the global model (the head is held by the 10 J-FWD connectors). The J-FWD sub-model has a FIT penalty contact with clearance 0.078 (10A). | no tie and no contact |

- The v3.5.2 tie is therefore consistent with the open, wetted gap of the pressure model (the 6.31 mm2 ring at Pc), as correction 4 asks. Because the 3-D model no longer ties the flange OD, the TC-03 corner on the variant (lc1v352g / lc1v352h) is already the corner "with the interface as the CAD has it" (free); no separate re-run is needed.
- Corrected row texts (correction 2), carried in section 2:
  - thread variant: "shoulder and M14 engagement tied ('zt'); flange OD and end face free";
  - 'faces' (v3.5.1): "the 0.12 mm tolerance ties 46 flange-OD nodes across the 0.10 mm design gap, and the z 117.51 end face (71 nodes)".

### 10B.4 Correction 3: the tie variant against the same mesh

- The v3.5.1 thread-only value at the TC-03 corner, **-0.259 / -0.327 (224.1 MPa)**, is quoted against the same-mesh R2 'faces' value **-0.266 (225.9 MPa)**: the tie variant moves the corner by **+0.007**. The v3.5.1 report compared it with the L1 value -0.312, which overstates the effect of the ties (RM2-13 (d)).
- The v3.5.2 runs confirm that the field, not the tie, drives the corner: with the same 'thread' tie at the same node n46040 (B1_1, LC1), the merged field gives -0.332 / -0.393 (248.5 MPa) and the GVLO field -0.076 / -0.159 (177.6 MPa).

### 10B.5 Correction 5: the re-posts (summary; every region, state and case in `repost_5b_v352.md` A-C)

Region minima over the four states, all-node and regular. The GVHI column and table C name the bound that is conservative for each region (GVLO | GVHI | merged surrogate, information):

| Region | Case | GVLO all-node MS y / u (node, class, state, T) | GVLO regular | GVHI all-node ; regular (T, vM) | thermal share (vM_TH / vM) | primary-only y / u (at node; region minimum) | P+Q 2 Fty (at node; region minimum) | merged surrogate all-node / regular (info) |
|---|---|---|---|---|---|---|---|---|
| **TC-03 corner** n46040 (r 9.8, z 105.513) | LC1 | **-0.076 / -0.159** (regular, B1_1, 88.9 C, 177.6 MPa) | same node | **-0.088 / -0.170** (same node and state, 89.6 C, 179.8 MPa) | 0.972 | +31.8 / +28.8 | +1.77 | -0.332 / -0.393 (74.4 C, 248.5 MPa; P+Q +1.00) |
| | LC2 | **-0.080 / -0.164** (B1_1, 178.5 MPa) | same node | **-0.092 / -0.175** (180.7 MPa) | 0.967 | +26.7 / +24.2 | +1.76 | -0.335 / -0.395 |
| TC-03 whole | LC1 | = the corner | = the corner | = the corner | | part minimum +7.52 / +6.75 (n47852, r 3.96 z 113.95, B1_21.65) | +1.77 (B1_1) | -0.332 / -0.393 |
| | LC2 | = the corner | = the corner | = the corner | | part minimum +7.18 / +6.44 (n47852, B1_21.65) | +1.76 | -0.335 / -0.395 |
| TC-03 shoulder (within 1 mm of the shoulder tie) | LC1 | +0.177 / +0.070 (n48093 RE, r 6.98 z 108.39, B1_19, 164.5 C) | +3.122 / +2.748 (n49590, B1_1) | +0.184 / +0.076 ; +3.067 / +2.698 (162.3 C) | 1.012 | +34.9 / +31.7 | +2.53 | +0.213 / +0.103 ; +2.468 / +2.153 |
| TC-03 thread root (within 1 mm of the thread tie) | LC1 | +0.089 / **-0.010** (n46569 ID tie-patch edge, r 6.93 z 117.51 = the thread-tie end, B1_19, 100.8 C) | +0.219 / +0.109 (n48057, r 6.99 z 108.48, B1_19, 163.5 C) | +0.132 / +0.029 ; +0.225 / +0.114 (98.3 C) | 1.006 | +28.3 / +25.7 | +2.27 | +0.248 / +0.135 ; +0.341 / +0.219 |
| | LC2 | +0.119 / +0.017 (n46569) | +0.229 / +0.117 | +0.164 / +0.058 ; +0.234 / +0.122 | 1.034 | +21.9 / +19.8 | +2.36 | +0.290 / +0.173 ; +0.352 / +0.229 |
| **TC-02 seat** (r <= 12, z 105-118) | LC1 | -0.006 / -0.179 (n26422 ID tie-patch edge, r 6.5 z 107.513 = the M14 thread-tie end, B1_19, 173.0 C, 96.5 MPa) | **+0.496 / +0.226** (n30265, r 7.98 z 107.513, B1_19, 169.5 C, 66.9 MPa) | -0.007 / -0.183 (171.0 C, 99.0 MPa) ; +0.498 / +0.223 (167.4 C) | 0.983 | +49.6 / +40.8 (seat minimum +20.1 / +15.9) | +1.98 | +0.160 / -0.068 (n26863, 159.2 C) ; +0.771 / +0.412 |
| | LC2 | -0.023 / -0.193 (n26422, 98.2 MPa) | **+0.469 / +0.204** (n30265, 68.1 MPa) | -0.023 / -0.197 (100.6 MPa) ; +0.472 / +0.202 (69.7 MPa) | 0.966 | +26.5 / +21.7 | +1.93 | +0.141 / -0.083 ; +0.741 / +0.388 |
| **TC-02 forward face** (z 103.513; holds the S-AX TC-02 maximum point r 24.95) | LC1 | +0.716 / +0.457 (n26625 regular, r 24.78, B1_19, 183.6 C, 48.7 MPa) | same node | +1.008 / +0.674 (176.9 C, 45.5 MPa) | 1.034 | +44.9 / +37.9 | +4.15 | +2.931 / +2.126 (152.7 C) |
| | LC2 | +0.763 / +0.497 (n26625, 47.4 MPa) | same node | +1.067 / +0.723 (44.2 MPa) | 1.063 | +24.8 / +20.9 | +4.29 | +3.094 / +2.256 |
| TC-02 whole | LC1 / LC2 | = the seat | = the seat regular | = the seat | | part minimum +0.709 / +0.385 (n27244, r 16.0 z 169.51, the TC-04 interface; mechanical stress, every state) | | |
| **NZ-01 at the v3.5.1 n72033** (v3.5.2 n73561, 0.0005 mm away; graphite, brittle criterion) | LC1 | -0.520 (RE, B1_19, 1311.6 C, 27.0 MPa) | none within the point set | -0.520 (the same) | 1.073 | - | - | -0.522 (not a surrogate on NZ-01) |
| | LC2 | -0.442 (B1_19) | | -0.442 | 1.139 | - | - | -0.444 |
| NZ-01 whole | LC1 | -0.520 (n73561) | -0.434 (n75973, r 6.48 z -223.34, B1_1, 1330.3 C) | -0.520 ; -0.434 | | | | -0.522 ; -0.435 |
| | LC2 | -0.489 (n74175 BT, B1_1) | -0.458 (n75973) | -0.489 ; -0.458 | | | | -0.490 ; -0.459 |

The four states one by one (LC1, GVLO; merged surrogate in brackets; table B has LC2 and the regular set):

| State | TC-03 corner n46040 MS y / u (T C; share) | TC-03 whole all-node (node) | TC-02 seat all-node / regular (T C at n26422) | TC-02 forward face n26625 (T C) | NZ-01 n72033 |
|---|---|---|---|---|---|
| B1_21.65 | +86.4 / +78.4 (165.4; 2.74) [+3.149 / +2.772] | +0.092 / -0.007 (n46558 ID, thread-tie end) | +0.513 / +0.229 ; +1.231 / +0.806 (165.0) [+0.696 / +0.350] | +1.277 / +0.926 (182.4) [+4.344 / +3.266] | -0.440 [-0.443] |
| B1_19 | +1.814 / +1.559 (171.1; 0.91) [+0.368 / +0.244] | +0.089 / -0.010 (n46569 ID) | -0.006 / -0.179 ; +0.496 / +0.226 (173.0) [+0.160 / -0.068] | +0.716 / +0.457 (183.6) [+2.931 / +2.126] | -0.520 [-0.522] |
| B1_2 | +0.879 / +0.708 (73.5; 0.94) [+0.292 / +0.175] | +0.800 / +0.637 (n46291) | +1.366 / +0.902 ; +1.971 / +1.395 (77.9) [+1.434 / +0.958] | +3.865 / +2.915 (73.4) [+5.809 / +4.520] | -0.061 [-0.066] |
| B1_1 | **-0.076 / -0.159** (88.9; 0.97) [-0.332 / -0.393] | = the corner | +0.370 / +0.098 ; +0.821 / +0.465 (97.7) [+0.469 / +0.178] | +2.755 / +2.022 (73.6) [+4.370 / +3.329] | -0.411 [-0.413] |

The same four states on GVHI (LC1) [SIM, `repost_5b_lc1v352h.json` cc652bed59e6df9d]:

| State | TC-03 corner n46040 MS y / u (T C; share) | TC-03 whole all-node (node) | TC-02 seat all-node ; regular (T C at the all-node minimum, n26422 unless named) | TC-02 forward face n26625 (T C) | NZ-01 n72033 |
|---|---|---|---|---|---|
| B1_21.65 | +21.475 / +19.437 (163.0; 0.33) | +0.137 / +0.034 (n46558 ID) | +0.501 / +0.215 ; +1.225 / +0.794 (162.9) | +1.684 / +1.233 (176.0) | -0.440 |
| B1_19 | +1.505 / +1.278 (168.7; 0.92) | +0.132 / +0.029 (n46569 ID) | -0.007 / -0.183 ; +0.498 / +0.223 (171.0) | +1.008 / +0.674 (176.9) | -0.520 |
| B1_2 | +0.824 / +0.659 (74.7; 0.95) | +0.750 / +0.591 (n46291) | +1.290 / +0.841 ; +1.878 / +1.319 (n26867, 79.1) | +4.117 / +3.119 (72.4) | -0.061 |
| B1_1 | **-0.088 / -0.170** (89.6; 0.97) | = the corner | +0.353 / +0.084 ; +0.799 / +0.447 (n26867, 98.5) | +2.829 / +2.082 (73.1) | -0.411 |

Findings [SIM; DERIVED where stated]:
- **GVHI against GVLO, region by region (table C names the bound).**
  - TC-03 corner: **GVHI governs**, -0.088 / -0.170 (LC1) and -0.092 / -0.175 (LC2) against GVLO -0.076 / -0.159 and -0.080 / -0.164. Same node and state (n46040, B1_1), 97 % thermal; primary-only +31.8 / +28.8 (LC1), P+Q +1.74 (LC1) / +1.72 (LC2). GVHI lies between GVLO and the merged field (-0.332 / -0.393), as its higher joint conductance moves it toward perfect contact [DERIVED, reading].
  - TC-02 seat all-node: **GVHI governs**, -0.007 / -0.183 (LC1) and -0.023 / -0.197 (LC2; yield equal to GVLO). The GVHI seat is cooler (171.0 against 173.0 C) but carries more stress (100.6 against 98.2 MPa, LC2). Regular set: GVLO is lower on yield (+0.496 against +0.498 LC1; +0.469 against +0.472 LC2), GVHI on ultimate (+0.223 against +0.226; +0.202 against +0.204). The two bounds differ by at most 0.004 on the seat.
  - TC-02 forward face: GVLO governs (+0.716 / +0.457 against GVHI +1.008 / +0.674, B1_19 LC1).
  - TC-03 thread root: GVLO governs (+0.089 / -0.010 against +0.132 / +0.029). TC-03 shoulder: GVLO governs (+0.177 / +0.070 against +0.184 / +0.076).
  - NZ-01: identical on both bounds (-0.520 LC1, -0.442 LC2 at n72033).
- **TC-03 corner, total and primary.** On GVLO the corner stays the TC-03 minimum, at the same node and state as on the merged field, but the opened flange-OD path removes most of the cool-rim hoop stress: -0.076 / -0.159 against -0.332 / -0.393 (vM 177.6 against 248.5 MPa; 97 % thermal on both). Primary-only +31.8 / +28.8 at the node (part minimum +7.18 / +6.44 at n47852, B1_21.65, LC2); P+Q +1.77 against +1.00. It stays negative on total stress, positive on primary and on P+Q. The governing TC-03 location did not move to the shoulder (all-node +0.177 / +0.070, regular +3.1). The next lowest TC-03 values are the all-node tie-end nodes of the thread tie (+0.089 / -0.010 at z 117.51), which are tie-termination nodes (class ID).
- **TC-02 seat.** On GVLO the seat is hotter (173.0 C against 159.2 C at the seat node) and its margins fall: all-node -0.006 / -0.179 (LC1) and -0.023 / -0.193 (LC2) at the M14 thread-tie end, regular +0.496 / +0.226 and +0.469 / +0.204. The seat stress stays thermal (97-98 %) with primary-only above +20 and P+Q +1.93.
- **TC-02 maximum.** Mapped at the four states it is 183.6 C at the forward-face OD corner (B1_19, GVLO), where n26625 is +0.716 / +0.457. The S-AX thermal maximum, 187.7 C at 21.5 s, is treated in 10B.6.
- **NZ-01** is unchanged by the variant (-0.520 GVLO against -0.522, the joints are 300 mm away). Per the lead 05:45Z, S-AX v352_NF2b is the named sub-model at the shoulder / foil interface and the 3-D value is a global check (the 3-D NZ-01 / NZ-02 meshes are the v3.5.1 ones, without the 0.25 mm NZ-06 foil).

### 10B.6 The instant of the S-AX TC-02 maximum (21.5 s)

- The S-AX TC-02 thermal maximum is **187.7 C (GVLO) / 181.3 C (GVHI) / 160.3 C (merged), all at 21.5 s**, at the forward-face OD corner by the TC-10 contact (thermal r 24.85, z 110.06 = S-AX z 103.516) [SIM, Mechanical envelope_parts]. 21.5 s is not an S-AX L1 state: the L1 states bracketing it are B1_19 and B1_21.65, both among my four states. The 3-D model has no 21.5 s state, so no stress is solved there.
- I read Mechanical's 21.501 s thermal frame and interpolated T at the 3-D governing nodes (`tc02_t215_v352.py`; the 19.001 / 21.651 s frames reproduce the S-AX L1 states B1_19 / B1_21.65 to 0.0 K, and the interpolated node temperatures match my 3-D mapped values within 0.6 K) [SIM + DERIVED]:

| Node (set) | T at 19.0 / 21.5 / 21.65 s, GVLO (C) | GVHI (C) | MS y / u at 21.5 s, GVLO, vM held at the larger bracketing state [DERIVED] | posted at B1_19 (governing) |
|---|---|---|---|---|
| TC-02 forward face n26625 (regular) | 183.6 / **187.7** / 182.4 | 176.9 / 181.3 / 176.0 | **+0.617 / +0.390** (48.7 MPa, B1_19 LC1) | +0.716 / +0.457 |
| TC-02 seat n30265 (regular) | 170.1 / 165.5 / 163.6 | 167.9 / 163.3 / 161.4 | +0.538 / +0.250 (68.1 MPa, B1_19 LC2) | +0.469 / +0.204 |
| TC-02 seat n26422 (all-node, ID) | 173.0 / 167.7 / 165.0 | 171.0 / 165.6 / 162.9 | +0.041 / -0.150 (98.2 MPa) | -0.023 / -0.193 |

- So the 21.5 s instant moves the forward-face corner by 4.1 K (to 187.7 C) and costs it about 0.10 / 0.07 at constant stress; it stays positive. The seat is cooler at 21.5 s than at B1_19, so B1_19 governs the seat. Assumption, stated: the stress at 21.5 s does not exceed the larger bracketing state (B1_19 at all three nodes). A solved 21.5 s state would need a 21.5 s S-AX L1 state from Mechanical or a direct thermal-frame map plus one LC1 solve; not run (section 11; the lead decides).
- GVHI rows at 21.5 s [DERIVED, constant stress; `tc02_t215_v352.json` 32a307a481fb05d8], vM held at the larger bracketing state as for GVLO:
  - forward face n26625: **+0.896 / +0.599** (181.3 C, 45.5 MPa from B1_19 LC1; posted +1.008 / +0.674);
  - seat n30265 (regular): +0.540 / +0.247 (163.3 C, 69.7 MPa from B1_19 LC2; posted +0.472 / +0.202);
  - seat n26422 (all-node, ID): +0.041 / -0.154 (165.6 C, 100.6 MPa from B1_19 LC2; posted -0.023 / -0.197);
  - seat n31012 (regular, the B1_21.65 seat minimum): +1.162 / +0.711 (147.0 C, 57.9 MPa from B1_21.65 LC2).
  - As on GVLO, 21.5 s costs the forward face about 0.11 / 0.08 and it stays positive; B1_19 governs the seat.

### 10B.7 The plug-to-bore dT at the fit, and the fit contact

| State | GVLO dT max (z), K | above the RM2-13 37-59 K trigger | closes at GVLO's own cold gap 0.078 (115.6 K) | merged |
|---|---|---|---|---|
| B1_21.65 | 77.5 (land A, z 106.51) | yes | no (0.026 mm left) | 3.2 K |
| B1_19 | 85.6 (land A) | yes | no (0.020 mm left) | 3.2 K |
| B1_2 | 32.1 (z 103.51) | no | no | 1.1 K |
| B1_1 | 23.3 | no | no | 1.1 K |

- dT = T(TC-02 plug OD) - T(TC-01 bore), 3-D mapped [SIM + DERIVED]; closure dT = gap / (r alpha) = 37.0 / 59.3 / 115.6 K at 0.025 / 0.040 / 0.078 mm (alpha 23.6e-6 /K). The S-AX-frame record over every S-AX state is `fit_dT_sax_v352.json` (GVLO maximum 88.4 K, 240 (7)).
- On GVLO the dT exceeds the RM2-13 trigger at B1_19 and B1_21.65, but GVLO's own gap (the drawing maximum) does not close. GVHI's gap (the drawing minimum 0.040) closes at land A from B1_8 to B1_19 (free-ring interference <= 0.0086 mm). The fit contact that correction 5 asks for was replaced by the lead's ruling (10:36Z, 240 (7)): **closure CLOSED on the Lame bound** (p 1.1 MPa; superposed on the land-A primary and P+Q cells at GVHI B1_8-B1_19, every cell positive; governing TC-02 wall at the hot spigot corner MS_y +1.35 -> +0.95, MS_u +0.96 -> +0.63); js5c dropped. The merged field holds the fit at perfect contact by construction (dT <= 3.2 K).

### 10B.8 Correction 6: TC-02 T-F1 at the variant temperature

T-F1 (212 (1)) needs sourced short-time 6061-T6 allowables. They are **NOT OBTAINED** (238 (6)); the evaluation is Mechanical's (b) package on the rev-4 fields (236 (4)). What the FE can state is the requirement at the variant temperature: the ratio k of the short-time strength at T to the room-temperature minimum (Ftu 260 / Fty 240 MPa) that a positive margin needs at each governing TC-02 location (table H) [DERIVED]:

| Location (GVLO) | T C | vM MPa | k_y needed (1.5 vM / 240) | k_u needed (2.0 vM / 260) | engmat 10,000 h ratio y / u at T (as posted) |
|---|---|---|---|---|---|
| TC-02 seat all-node n26422 (ID, thread-tie end; information per 239 (4)(b)) | 173.0 | 98.2 | 0.614 | 0.755 | 0.600 / 0.610 |
| TC-02 seat regular n30265 | 169.5 | 68.1 | 0.426 | 0.524 | 0.625 / 0.631 |
| TC-02 forward face n26625, B1_19 | 183.6 | 48.7 | 0.304 | 0.375 | 0.522 / 0.546 |
| TC-02 forward face n26625 at 21.5 s (the S-AX TC-02 maximum; constant stress) | 187.7 | 48.7 | 0.304 | 0.375 | 0.492 / 0.521 |

| Location (GVHI) | T C | vM MPa | k_y needed (1.5 vM / 240) | k_u needed (2.0 vM / 260) | engmat 10,000 h ratio y / u at T |
|---|---|---|---|---|---|
| TC-02 seat all-node n26422 (ID; information) | 171.0 | 100.6 | 0.629 | 0.774 | 0.614 / 0.622 |
| TC-02 seat regular n30265 | 167.4 | 69.7 | 0.436 | 0.536 | 0.641 / 0.644 |
| TC-02 forward face n26625, B1_19 | 176.9 | 45.5 | 0.284 | 0.350 | 0.571 / 0.586 |
| TC-02 forward face n26625 at 21.5 s (constant stress) | 181.3 | 45.5 | 0.284 | 0.350 | 0.539 / 0.560 |

- Reference: on the v3.5.1 merged field the seat node needed k_u >= 0.788 at 159.2 C (RM2-13 (e)); line 212 gave Ftu(149 C) >= 0.765 and Ftu(181 C) >= 0.661 of Ftu,RT,min.
- Reading: on the regular set every TC-02 location passes on the 10,000 h engmat ratios already, at its variant temperature, on both bounds. Only the tie-end all-node seat value needs short-time data above the 10,000 h ratio (GVLO 0.755 against 0.610 at 173.0 C; GVHI 0.774 against 0.622 at 171.0 C). Check (d), the 150 C usable limit, is exceeded at the TC-02 maximum on every bound and stays **OPEN** with T-F1 (239: TC-02 188.4 C in the nominal burn on rev 4, 247.8 C at TB). This is not a structural margin and the FE does not close it.

### 10B.9 The bound conservative for each part

| Part | Conservative bound (physical) | Its value | Other bound | Perfect-contact (merged) bound, information |
|---|---|---|---|---|
| TC-03 (corner governs) | **GVHI** (GVLO governs the thread root and the shoulder, 10B.5) | -0.088 / -0.170 LC1, -0.092 / -0.175 LC2 | GVLO -0.076 / -0.159 LC1, -0.080 / -0.164 LC2 | -0.332 / -0.393: lower, but the flange OD cannot carry the merged heat across a 0.10 mm gas gap (about 6600-7000 K needed, RM2-13 (b)); the merged field is kept only as the perfect-contact bound (236 (2)) |
| TC-02 seat | **GVHI** on all-node; on regular GVLO for yield, GVHI for ultimate (within 0.004) | all-node -0.023 / -0.197, regular +0.469 / +0.202 (LC2, lower bound per component) | GVLO all-node -0.023 / -0.193, regular +0.469 / +0.204; GVHI regular +0.472 / +0.202 | +0.141 / -0.083 ; +0.741 / +0.388 |
| TC-02 temperature | GVLO | 187.7 C S-AX at 21.5 s (183.6 C mapped at B1_19) | GVHI 181.3 C | 160.3 C (non-conservative, 236 (2)) |
| NZ-01 | GVLO = merged within 0.002 (S-AX v352_NF2b governs) | -0.520 LC1 | GVHI identical (-0.520 LC1) | -0.522 (v3.5.1 map; not a surrogate on NZ-01) |

GVHI value at n46040 in the GVLO form (lead request): **n46040 at B1_1 (GVHI LC1 -0.088 / -0.170, 97 % thermal)**; LC2 -0.092 / -0.175, 97 % thermal [SIM, `repost_5b_lc1v352h.json` cc652bed59e6df9d].

### 10B.10 Classification and the lead's rulings in force

- **TC-03 corner**: thermal-secondary (TS-183) with a model-fidelity question on its value (234 (7)). Lead 07:51Z (239 (4)(a)): a global check under the MF disclosure; **S-AX governs (v352r4 +2.564 / +2.241, TS-183)**; the 4x global / S-AX difference is a model-fidelity note for T-F2. The variant answers the direction of the MF question: the closure carried most of the v3.5.1 negative (10B.4, 10B.5). It does not make the global value positive on total stress.
- **TC-02 seat**: stress class TS-212. The all-node minima at the M14 thread-tie end are information (239 (4)(b)); the regular values are +0.496 / +0.226 (LC1) and +0.469 / +0.204 (LC2) on GVLO, +0.498 / +0.223 and +0.472 / +0.202 on GVHI. Mechanical's rev-4 S-AX contact sub-model is the named sub-model for the seat region (lead 05:42Z), with the MF disclosure for the seat entry.
- **TC-02 temperature**: a model-fidelity question with a direct design consequence; DESIGN ITEM (236 (4)): GVLO 187.7 C / GVHI 181.3 C against the 150 C limit and the 181 C T-F1 acceptance; T-F1 not obtained; (d) OPEN; path (b) with Mechanical.
- **NZ-01**: S-AX v352_NF2b is the named sub-model; the 3-D value is a global check (lead 05:45Z).

### 10B.11 Not done here, and open

- No LC1 on the v3.5.2 NF2b merged field; the v3.5.1 merged map stands for it on TC-02 / TC-03 (table G), not on NZ-01.
- No solved 21.5 s state (10B.6); the 21.5 s rows are constant-stress [DERIVED].
- TC-02 / TC-03 stay rev 3 in the 3-D model (lead 05:42Z): the rev-4 seat-bore entry radius and the TC-03 undercut are only in Mechanical's S-AX contact sub-model.

## 11. Not run, superseded, and runs that wait for the lead

Nothing in this list is a margin. Each item names the ruling that holds it.

**Not run by ruling**
- **c71x** (the tie-impact runs `pose_stop045_c71x`, `pose_neutral_c71x`, `lc1v351_c71x`; CAD v3.5.1 with tiex): NOT RUN (lead 16:20Z (3), 18:50:09Z (5)). It could run only if disk space appeared after js5b; none did, and the tail F ended 2026-10-21T03:18:21Z with 'spring run and c71x NOT RUN'. Consequence: the K change between the v3.5.1 and v3.5.2 models (section 9) is not split between the asm v1.3 interfaces, the TC-09 mesh level and the CAD change.
- **The J-FWD spring-footprint run** (route (i) for the flat bearing under the screw head): NOT RUN (lead 18:50:09Z (5)). It was ranked after (b1) and js5b and could run only if space appeared after js5b; none did (tail F end line 03:18:21Z). The flat-bearing row stays Mechanical's IN718 row on A_ROW (10A.11).
- **The shared re-solve route** for the TC-04 BT cells (hot bounds -0.004 / -0.008 u at n42993, section 4) and the OP-moment residue of the F2 cells (section 9B): remesh TC-04 to tet quality q >= 0.1, re-solve the 2 hot-bound bases x 4 states and the 17 R3 poses with a moment-free OP step, then re-post, lc3_bound and the matrix. Cost [DERIVED from the logged runs]: about 2.7 h ccx, 3.1 h wall, peak RSS 5.64 GB, about 0.46 GB transient per run and 0.49 GB held. **NOT RUN, final** (lead 2026-10-21T03:30:46Z (2); earlier 22:24:34Z, 21:47:29Z (4)). Each run needs about 2.50 GiB free at its start and would end under the 1.86 GiB floor; the route leaves free space about 0.95 GB lower, and nothing frees 1 GB or more (the 23 uncited v3.4.1 result files stay). TC-04 stays a found negative (class BT, -0.004 / -0.008 DERIVED node-wise lower bound; regular nodes within 2 mm >= +0.643); the OP couple stays an MF observation. The as-found cells stand, with the node-wise / part-wide bounds and the moment-free estimates beside them.
- **js5c** (the TC-01 / TC-02 fit contact): dropped. The fit closure is CLOSED on the Lame bound (lead 10:36Z, 240 (7); section 10B.7).

**Not run, stated where the value is used**
- No solved 21.5 s thermal state: the 21.5 s TC-02 rows are constant-stress [DERIVED] (10B.6). A solved state needs a 21.5 s S-AX L1 state from Mechanical, or a direct thermal-frame map plus one LC1 solve.
- No LC1 on the v3.5.2 NF2b merged field: the v3.5.1 merged map stands for TC-02 / TC-03 as the perfect-contact information bound (10B), not on NZ-01.
- No R4 lever-root mesh: where R2 -> R3 changes by more than 5 %, the cell quotes the p = 1 bound (5.2).
- No compliant-airframe v3.5.2 run: the datasheet rows carry the v3.5.1 compliant rows, marked c351 (8.1).
- The runs that would isolate the stop045 K change (`pose_stop045_v352L1`, `v352L1x`, `v352`) no longer hold fields (9).

**Superseded**
- **lc1v352hb** (rev-1 lever, R3 hot-bound base, default S-AX map; DONE 04:01:54Z): **superseded, never posted.** GVLO / GVHI (about 04:15Z) and the rev-3 bases hbg3 / hbh3 (about 05:55Z) replaced it before any post. Its fields were pruned at 08:53:19Z as uncited (`runs/PRUNED_v352.txt` lines 23-30). Nothing uses it. ACCEPTED as found, not re-run (lead 21:47:29Z (2)).
- The R2 / R3 stop045 runs without a check_fbd JSON are ACCEPTED as found (lead 21:47:29Z (2)). stop045 is the K band reference; its mirror pose stop315 corroborates it (fractions 0.955-0.998, fbd 0.0087 N; section 9).
- `modal_v351ca2b_c71` is superseded by `modal_v351ca2c_c71` for RM2-06 only. The 9A mode list stands.
- The v3.5.1 K files (`k_stop_c71`, `k_cone_c71`, `k_range_v351`) are superseded for every with-servo value (9).

## 12. Files (sha256/16 of every published file in MANIFEST.json in this folder)

**Hub folder `04-fea/assembly3d_v352/`.** This release adds NEW files only. No existing hub file is rewritten; the publish script compares every destination that already exists and reports a differing one as a clash without touching it.
- `REPORT-FEA3D-v352.md` (this report), `MANIFEST.json` (sha256/16, bytes and work-area source of every file in this release) and `MANIFEST.sha256` (the full sha256 of every file in this release and of `MANIFEST.json`, paths relative to this folder; `sha256sum -c MANIFEST.sha256` run in this folder checks them).
- `tables/margin_matrix_v352.{md,json}`: section 3A, from the second and last re-run, on the final J-FWD envelope v6 (2026-10-21T05:22Z; the first re-run was on v5 at 03:33:37Z; neither changed a cell).
- `results/v352/`, `results/`: the post-processing JSON and tables cited in sections 3-10B and 14.
- `scripts/`: the scripts behind them, for reproduction (CalculiX 2.21; Python in `/opt/engine-venv`).
- `jfwd_patches/<run>/`: J-FWD run evidence added in this release: posts, the solver logs (`.sta` / `.cvg` / `.dat` / `.log`), `ccx_run.json`, `meta.json`, `COMPRESSED.txt` (frd raw sha256 = decompressed sha256) and the decks of (b1) (raw `.inp`), js5b (`.inp.gz`) and cD (`.inp.xz`, raw sha256 = decompressed sha256 in `DECK_XZ.txt`). The frd.gz files stay in the work area.
- `runs/`: `PRUNED_v352.txt` (every pruned or released solver file with its raw sha256, size and deck), the two ICD export logs, the js5b and cD stage scripts (`runs/tail_F_js5b.sh`, `runs/stage_cD_v352.sh`), their post logs (`runs/post_js5b.log`, `runs/post_cD.log`) and the logs of the two matrix re-runs (`runs/margin_matrix_v352_0333.log` on v5, `runs/margin_matrix_v352_v6_0522.log` on v6).

**Already in the hub before this release (unchanged):** `C71-RELEASED-FIELDS-v352.md` (release note and regeneration recipe of the released fields) and `samples.py.bak_v352` (the pre-fix `samples.py`, 2.1); `jfwd_interim/` (js5 post, INDEX `76f9852492a597dd`); `jfwd_patches/` ((a), (a'), (a''), (b2) evidence, the s9 decks, INDEX and MANIFEST.sha256); `results/v352/` (envelopes v1 `1d970741cb95a885`, v2 `336568296bdb896f`, v3 `0872de4ea7e3601d`, the A_ROW flat bearing, the land-A closure); `scripts/landA_closure_gvhi.py`. J-FWD scripts whose sha has not changed since that publication (for example `jfwd_post.py`, `jfwd_seat.py`, the production `jfwd_sub.py` `cbc4c2ae2a1b61fd`) are cited from `jfwd_patches/scripts/` or `jfwd_interim/`.

**v3.5.1 records** cited here stay in `04-fea/assembly3d/` (for example `tables/engine_mount_data_v351.md` `917d497681939e65`, `tables/k_range_v351.md` `b5093e0276611f7f`) and `04-fea/s3d_v351/`.

**Not published (work area `/home/claude/work/fea3d`):** solver bulk (frd.gz, fields.npz, the other decks .inp.gz / .inp.xz) with their raw sha256 in each run's `COMPRESSED.txt` / `DECK_XZ.txt`, `runs/deck_raw_sha_v352.jsonl` and `runs/REPACKED_deck_v352.txt`; the run logs (`runs/tail_F.log`, `runs/chain_*.log`); the record copies of files that changed after CHANGELOG lines 249 / 250 cited them, each named by the sha it was cited with (`results/v352/records/`, for example the v5 matrix `margin_matrix_v352_5568033c68742a65.md` and `margin_matrix_v352_a53b309c5d7e1f55.json`; `scripts/records/`, for example `margin_matrix_v352_79d3605788f134d9.py` and `jfwd_envelope_delta_v352_32212446a8469f7c.py`; `report_v352/records/03A_margin_matrix_3a102a4a0e2cec56.md`); the 23 v3.4.1 result files whose delete was refused by the permission check stay where they are, unused.

### 12.1 Key files (sha256/16 at writing; the full list with bytes is MANIFEST.json)

| published path | sha256/16 | content |
|---|---|---|
| `tables/margin_matrix_v352.md` | `3d274f66c31a18e4` | 3A margin matrix (every part x case; final J-FWD envelope) |
| `tables/margin_matrix_v352.json` | `e59e35df6759afbb` | 3A, machine-readable |
| `results/v352/jfwd_soak_envelope_v352_v6.json` | `43a5d78b67c615fc` | 10A.12 J-FWD envelope v6 (FINAL) |
| `results/v352/jfwd_soak_envelope_v352_v5.json` | `ef22b59cf2413b46` | 10A.12 envelope v5 (ACCEPTED lead 2026-10-21T03:30:46Z (3); superseded by v6, 05:17:36Z (3)) |
| `results/v352/jfwd_soak_envelope_v352_v4.json` | `9d9fd8ee991f9887` | 10A.12 envelope v4 (ADOPTED 00:39:30Z; superseded by the final) |
| `results/v352/jfwd_envelope_delta_v352_v6_vs_v5.json` | `3844deef9c385a74` | 10A.12.2 delta v6 against v5 (with the note on the one-side check) |
| `results/v352/jfwd_envelope_delta_v352_v6_vs_v4.json` | `95e6eeee99e8196d` | 10A.12.2 delta v6 against v4 |
| `results/v352/jfwd_envelope_delta_v352_v5_vs_v4.json` | `a8c6aa69742fba5f` | 10A.12.2 delta v5 against v4 |
| `results/v352/jfwd_b1_meshcorr_v352.json` | `adac16afd42ef7bd` | 10A.6 / 5.3 mesh correction C1 (ADOPTED) |
| `results/v352/jfwd_js5b_rows_v352.json` | `91278d6b039c5b27` | 10A.13 js5b rows (FA1U / FA1D / LC2, IN718) |
| `results/v352/jfwd_cD_result_v352.json` | `8209e80f09f28af7` | 10A.6 / 5.3 convergence check cD result |
| `results/v352/jfwd_patch_extrap_nodes_v352.json` | `f95abde5b1489976` | 5.3 patch boundary extrapolation (s6 / s9 / sD) |
| `results/v352/jfwd_convcheck_costing_v352.json` | `b427869869a9e8f8` | 5.3 convergence-check costing |
| `results/v352/jfwd_v7inputs_cD_v352.json` | `5a41c8d74897bdda` | 10A.12.1 v7 inputs with cD: Mechanical's re-map input record with v6 (lead 2026-10-21T05:27Z (3)) |
| `results/v352/jfwd_v7inputs_c1_v352.json` | `384c1a472add7a4c` | 10A.12.1 v7 inputs, C1 view |
| `results/v352/jfwd_v7inputs_v352.json` | `753431eb50f36f58` | 10A.12.1 v7 inputs, as solved |
| `results/v352/lever_root_table_v352.json` | `59d834055fa1d359` | 6.2 lever-root table (cold / hot, 17 poses) |
| `results/v352/lc3_hot_bound_v352r3_gvlo_gvhi.json` | `c4ecb8b4e4a03afd` | 6 / 3A LC3 / F2 hot bound on R3 (GVLO / GVHI) |
| `results/v352/hb_partwide_v352.json` | `cc96d78d266df4db` | 4.4 part-wide hot bound (w) |
| `results/v352/hb_singular_check_v352.json` | `7d4ab97c0d7d3e75` | 4.4 node-wise hot bound at singular nodes (s) |
| `results/v352/s3d_summary_v352.json` | `afd39c752fc46d3c` | 9B F2 summary |
| `results/v352/op_moment_check_v352.json` | `bf849ad982fb8bb1` | 9B.3 OP-moment residue |
| `results/v352/k_table_r3_v352.json` | `f3c7cfbcfb98bcd7` | 9 v3.5.2 R3 K table (17 poses) |
| `results/k_range_v352.json` | `08c1bf80e2754c9c` | 9 K range with the servo in series (RM2-05) |
| `results/v352/modal_ca2c_vs_ca2b_v352.json` | `1bdaf41b4611094c` | 9A RM2-06 modal re-solve comparison |
| `results/v352/rocking_servo_J_v352.json` | `e655a92b3818bf32` | 9A RM2-07 rocking pair with servo J |
| `results/v352/engine_mount_data_v352.json` | `e5f41bde43a00ba4` | 8 datasheet mounting rows |
| `results/v352/icd_momentfree_v352.json` | `785b4e48f407ddfb` | 8 moment-free estimate and governing hole loads |
| `results/v352/repost_5b_lc1v352g.json` | `73905ef3358f8fa0` | 10B GVLO re-post |
| `results/v352/repost_5b_lc1v352h.json` | `cc652bed59e6df9d` | 10B GVHI re-post |
| `results/v352/f4_v352.json` | `fd5a06671fd4456a` | 10 F4 joints |
| `results/v352/f1_convergence.json` | `8eec4261cbe43b53` | 5.1 convergence (RM2-03) |
| `results/v352/gm01_rodpath_bound_v352.json` | `f24544c124289069` | 3A GM-01 rod-path bound (ACCEPTED) |
| `results/v352/hb_base_residue_v352.json` | `e46d41bace79be47` | 9B.3 hot-bound base residue (ACCEPTED) |

### 12.2 Runs behind this report (v3.5.2 model unless stated) [SIM run records]

Status from the run folders: DONE marker, solver records (`runs.jsonl` / `ccx_run.json`), and `runs/PRUNED_v352.txt`.

| run | what | used in | solves (rc) | solver h | peak RSS GB | status |
|---|---|---|---|---|---|---|
| `lc1v352g` | LC1 / LC2 on S-AX GVLO (4 burn states) | 3A, 10B | 7 (0) | 0.55 | 3.23 | posted; 2 files pruned |
| `lc1v352h` | LC1 / LC2 on S-AX GVHI | 3A, 10B | 6 (0) | 0.48 | 3.23 | posted |
| `lc1v352` | LC1 on the v3.5.1 merged map (perfect-contact information) | 10B | 4 (0) | 0.33 | 3.22 | posted (information); 4 files pruned |
| `lc1v352hb` | R3 hot-bound base, rev-1 lever, default S-AX map | - | 4 (0) | 0.22 | 5.44 | superseded, never posted; fields pruned (PRUNED_v352.txt) |
| `lc1v352hbg3` | hot-bound base, rev-3 R3, GVLO | 6, 3A | 4 (0) | 0.25 | 5.57 | posted |
| `lc1v352hbh3` | hot-bound base, rev-3 R3, GVHI | 6, 3A | 4 (0) | 0.23 | 5.57 | posted |
| `fa1v352n` | FA-1 (FA1Q / D / U / S / T) on the NF2b A1_22.2 relight state | 3A, 8 | 1 (0) | 0.09 | 3.22 | posted |
| `tb352g` | TB70 / TBS, GVLO (A 175 C) | 3A, 4 | 1 (0) | 0.06 | 3.22 | posted |
| `tb352h` | TB70 / TBS, GVHI (A 175 C) | 3A, 4 | 1 (0) | 0.05 | 3.21 | posted |
| `soak352g` | LC6 soak column, GVLO (B1_86.7, B1_286.7) | 3A | 2 (0) | 0.03 | 3.13 | posted (TS2) |
| `soak352h` | LC6 soak column, GVHI (B1_86.7, B1_226.7) | 3A | 2 (0) | 0.02 | 3.13 | posted (TS2) |
| `pose_stop000_v352r3R3` | pose stop000, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.14 | 5.63 | posted |
| `pose_stop045_v352r3R3` | pose stop045, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.61 | posted |
| `pose_stop090_v352r3R3` | pose stop090, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.64 | posted |
| `pose_stop135_v352r3R3` | pose stop135, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.61 | posted |
| `pose_stop180_v352r3R3` | pose stop180, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.64 | posted |
| `pose_stop225_v352r3R3` | pose stop225, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.62 | posted |
| `pose_stop270_v352r3R3` | pose stop270, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.64 | posted |
| `pose_stop315_v352r3R3` | pose stop315, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.61 | posted |
| `pose_neutral_v352r3R3` | pose neutral, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.62 | posted |
| `pose_alpha+_v352r3R3` | pose alpha+, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.12 | 5.61 | posted |
| `pose_alpha-_v352r3R3` | pose alpha-, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.11 | 5.64 | posted |
| `pose_beta+_v352r3R3` | pose beta+, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.64 | posted |
| `pose_beta-_v352r3R3` | pose beta-, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.14 | 5.63 | posted |
| `pose_combined045_v352r3R3` | pose combined045, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.14 | 5.62 | posted |
| `pose_combined135_v352r3R3` | pose combined135, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.12 | 5.62 | posted |
| `pose_combined225_v352r3R3` | pose combined225, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.14 | 5.62 | posted |
| `pose_combined315_v352r3R3` | pose combined315, rev-3 levers at R3 | 6, 9, 9B, 8 | 1 (0) | 0.13 | 5.62 | posted |
| `pose_stop045_v352r3R2` | pose stop045, rev-3 levers at R2 (5 % rule) | 5.2, 6.2 | 1 (0) | 0.07 | 3.21 | posted |
| `pose_stop315_v352r3R2` | pose stop315, rev-3 levers at R2 (5 % rule) | 5.2, 6.2 | 1 (0) | 0.07 | 3.20 | posted |
| `pose_alpha+_v352r3R2` | pose alpha+, rev-3 levers at R2 (5 % rule) | 5.2, 6.2 | 1 (0) | 0.07 | 3.19 | posted |
| `pose_alpha-_v352r3R2` | pose alpha-, rev-3 levers at R2 (5 % rule) | 5.2, 6.2 | 1 (0) | 0.06 | 3.19 | posted |
| `pose_stop045_v352L1` | stop045 L1, legacy ties (tie finding) | 7.1 | 1 (0) | 0.08 | 2.40 | record; fields pruned |
| `pose_stop045_v352L1x` | stop045 L1, tiex (tie fix check) | 7.1 | 1 (0) | 0.09 | 2.29 | record; fields pruned |
| `pose_stop045_v352` | stop045, rev-1 lever at R3 (zero-radius record) | 6 | 1 (0) | 0.17 | 5.03 | record; fields pruned |
| `pose_stop315_v352` | stop315, rev-1 lever (zero-radius record) | 6 | 1 (0) | 0.13 | 5.04 | record; fields pruned |
| `pose_alpha+_v352` | alpha+, rev-1 lever (zero-radius record) | 6 | 1 (0) | 0.11 | 5.17 | record; fields pruned |
| `pose_alpha-_v352` | alpha-, rev-1 lever (zero-radius record) | 6 | 1 (0) | 0.11 | 5.19 | record; fields pruned |
| `pose_stop045_v352r2` | stop045, rev-1 lever at R2 (zero-radius record) | 6 | 1 (0) | 0.09 | 2.65 | record; fields pruned |
| `modal_v351ca2c_c71` | modal re-solve, CAD v3.5.1, L2 mesh with L1 TC-01 loads (RM2-06) | 9A | 1 (0) | 0.12 | 3.54 | posted |
| `js5_mu0_T3750_g078` | J-FWD global sector s5, sharp, mu 0, 3750 N | 10A.3 | 1 (0) | 2.47 | 5.97 | posted (hub jfwd_interim) |
| `seat_s5L8_mu0` | (a) seat patch s5 L8, physical order | 10A.4 | 1 (0) | 0.49 | 2.64 | posted (hub jfwd_patches) |
| `seat_s5L8_mu0_go` | (a') seat patch s5 L8, js5's order | 10A.4 | 1 (0) | 0.59 | 2.68 | posted (hub jfwd_patches) |
| `seat_s5L12_mu0_go` | (a'') seat patch s5 L12, js5's order | 10A.4 | 1 (0) | 0.76 | 2.70 | posted (hub jfwd_patches) |
| `seat_s6L12_mu0` | (b2) s6 L12, R0.2, mu 0, with repeats | 10A.5 | 1 (0) | 2.18 | 5.76 | posted (hub jfwd_patches) |
| `seat_s9L12_mu02A` | (b1) s9 L12, R0.2, mu 0.2, physical order with repeats (design-value run) | 10A.12 | 1 (0) | 5.29 | 6.46 | posted |
| `seat_s9L12_mu0` | (b2') s9 L12, R0.2, mu 0 (mesh check) | 10A.6 | 1 (0) | 0.72 | 3.15 | posted |
| `js5b_in718_mu0_T3750_g078_cf` | js5b: s5, mu 0, IN718, FA1U / FA1D / LC2U / Y / N / M | 10A.13 | 1 (0) | 1.95 | 6.13 | posted; jfwd_cells re-run by hand after jfwd_spotface (the stage ran cells first, so the hole-bearing rows were empty; runs/post_js5b.log; ACCEPTED lead 2026-10-21T03:30:46Z (4)) |
| `seat_sDL12_mu0` | cD: s6 + Balls h 0.04 on the governing line, FINAL TC-01, mu 0 | 10A.6, 5.3 | 1 (0) | 1.84 | 6.88 | posted |

Not run, or superseded before a solve:

- `js5b_mu0_T3750_g078`: A4-80 js5b deck 3842f1c070f5d1a3: never run, SUPERSEDED by the IN718 deck (lead 11:25Z (3)).
- `js5b_in718_mu0_T3750_g078`: IN718 source deck (raw fd5c555220cab427): run as js5b_in718_mu0_T3750_g078_cf.
- `seat_s9L12_mu02`: held deck e491b04b2b559c99: not run; (b1) ran as seat_s9L12_mu02A.
- `seat_s6L8_mu0`: deck only, not run (L8 superseded by L12, lead 12:28Z (2)).
- `seat_s9L8_mu0`: deck only, not run (L8 superseded by L12).
- `seat_s9L8_mu02`: deck only, not run (L8 superseded by L12).
- `js4_mu0_T3750`: js4 (CAD seat, s4): superseded by js5; its FA1S TC-02 cell is the 07:25Z record (10A.3).
- `jt1_mu0_T3000`: t1 trial: INVALID (7.3 item 1), kept as the record.

## 13. Open items and owners (2026-10-21)

Every number is as found and carries its tag in the section named. Nothing here is physical approval.

| # | item | status / numbers | owner | closure |
|---|---|---|---|---|
| 1 | **TC-01 J-FWD seat / ring line P+Q** (secondary, shakedown; class DC) | found negative on the final envelope v6 `43a5d78b67c615fc` (lead 05:17:36Z (3); the seat lines are those of v5): SOAK **-0.071** ((b2) rep), SOAK70 **-0.055** ((b2)), SOAK52 **-0.030** ((b1) at C1) (P+Q <= 2 Fty(T), A4-80 FE; the worst computed instance, not a proven bound; the contact solution depends on the predecessor state, 10A.5). Not shown converged with the mesh (MF note with cD: s9 -> s6 +12 to +18 %, s6 -> cD -1.5 to -7.3 % on the governing line, not monotonic; 5.3, 10A.6). IN718 cell on Mechanical's v7 rows (mapped on v3): TC-01 J-FWD **-0.075** / +0.239 (SOAK seat line at 3750 N, (b2) rep; FA1S hole bearing CALC) [SIM / DERIVED / CALC] | **Mechanical** (IN718 re-map once on the final envelope v6 with `jfwd_v7inputs_cD_v352.json`, lead 05:27Z (3); select-fit band re-size from the P+Q-vs-gap sensitivity, lead 00:39:30Z (1), (4)) | the band inside [0.040, 0.0761] mm that closes it, or the seat-line P+Q stays a found negative in the datasheet; the HW-170 disc-spring route (i) and the preload-retention audit (240 (10)) |
| 2 | **HW-101 IN718 screw rows** on the final envelope | Eq. 22 inputs V 4079.2 N (FE, (b1)) and M 4354.7 N mm (CALC) (lead 01:30:18Z (6)); the cell quotes +0.301 at V 3888.1 N until the re-map; Mechanical's soak fibre rows negative (SOAK -0.257 at 3750 N; 10A.8); (b1) moments as solved, M x 1.404 / x 1.476 as information (lead 02:01:34Z (B)) | **Mechanical** | the re-map on the final envelope v6; the relaxation / shakedown / LCF rows |
| 3 | **TC-02 TB70 / TBS** (n30266, 228.7 C; TS-212) | -0.236 / -0.271; +0.138 / -0.035 [SIM] | Mechanical / founder | 212 (1) (d) time at temperature with T-F1; Mechanical's (b) package |
| 4 | **The seat region at TB** (4.3) | Mechanical's S-AX v352r4 fails line 106 at SF 1.0 at TB70 (TC-02 -0.326 / -0.371; TC-03 undercut root -0.191 / -0.264) [CALC / SIM, Mechanical] | Mechanical | T-F2 contact runs and the abort search |
| 5 | **TC-03** LC1 / LC2 / LC3 / F2 hot bound / TB70 (TS-183) | -0.088 / -0.170 ... -0.121 / -0.201 [SIM / DERIVED]; S-AX governs +2.564 / +2.241 (lead 07:51Z (a)) | Mechanical | 183 (1) (c) LCF and (d) GlidCop time at temperature |
| 6 | **FD-01** bonded-patch edge (TS-183) | LC6 soak -0.187 / +0.780, TB70 -0.336 / +0.484, TBS -0.005 / +0.976 (A 175 C, hotter than the adopted 150 C) [SIM] | Mechanical | 183 (1) (c) LCF; (d) on the sourced long-time allowable where T <= 150 C, else T-F1 |
| 7 | **NZ-01** graphite (BR) | -0.520 ... -0.054 (yield only, brittle, thermal) [SIM]; S-AX v352_NF2b is the named sub-model | Mechanical / Combustion | 183 (2) capture / containment plus a test basis, else a design change |
| 8 | **NZ-03** char (CH) | LC2 -0.088, TB70 -0.392, TBS -0.253 (n81357) against the ASSUMED 20 MPa | founder / Mechanical | N-F1 (>= 21.96 MPa inside the 23.7 MPa acceptance); 188 (3) contact FE at the tie edge |
| 9 | **PD-01R / PD-01S** (MF) | -0.315 / -0.451 ... -0.444 / -0.555; primary-only above +20 | fea3d (model) | PD-02 is rigid in the model; a deformable PD-02 if the lead asks for it (lead 07:51Z (e), 08:04Z) |
| 10 | **TC-04 BT node n42993** (q 0.040 / 0.027) | LC3 hot bound +0.228 / **-0.004**, F2 hot bound +0.223 / **-0.008** [DERIVED node-wise lower bound]; regular nodes within 2 mm >= +0.643; a found negative in the datasheet | lead (ruled 2026-10-21T03:30:46Z (2): the settling route NOT RUN, final, for disk) | the settling route (remesh TC-04 to q >= 0.1, re-solve the hot-bound bases and the 17 R3 poses, shared with item 11; about 2.7 h ccx, about 2.50 GiB free at each start) if disk is ever granted; until then the cell stays negative, class BT |
| 11 | **OP-moment residue** (MF observation, 4.5, 9B.3) | L1 Q [539, 484] N mm/MPa; R3 poses [304-307, 2298]; cells stand as found with the moment-free estimates beside them; datasheet hole loads take the larger value (8) | lead (ruled 03:30:46Z (2): NOT RUN, final, for disk) | a moment-free OP step on the shared route of item 10, if disk is ever granted |
| 12 | **J-FWD contact history dependence** (10A.4, 10A.5) | the soak states depend on the predecessor state at mu 0 and mu 0.2; carried as the envelope over the computed histories | fea3d / lead | a history-robust contact model (mortar, or a softened penalty at the ring) is not run and not proposed for this schedule |
| 13 | **J-FWD on the FINAL TC-01** (2.1, 10A.2) | all J-FWD FE except cD on the interim TC-01 (d10.5 flats; the final d11.2 flats are coplanar); cD ran on the FINAL TC-01: cD / s6 0.927-0.985 on the governing line, s6 + C1 stand; mesh and geometry not split (10A.6) | fea3d / Mechanical | effect on the other J-FWD rows ASSUMED small; Mechanical cites the same basis in its re-map |
| 13a | **LC2 hand form, TC-01 ligament** (information, 10A.13) | LC2N Pm+Pb +0.016 / **-0.183**, LC2M +0.266 / +0.021 with SF 1.5 / 2.0 on the total stress including the preload (about 129 of 151.6 MPa) [SIM / DERIVED; linear superposition ASSUMED]; criterion = FE-factored LC2Y / LC2U +0.421 / +0.424 (rule (A), lead 03:30:46Z (1)) | lead (ruled) / datasheet owner | shown as information beside the cells (10A, the datasheet J-FWD table); no closure needed under the rule |
| 14 | Bearing, washer and screw datasheets | HK0808 C0 / C, PTFE washers: TO-VERIFY; loads in 6.1 and 8 | Mechanical | datasheet values into the hub (none invented here) |
| 15 | 7075-T6 temperature table (RM2-10, RM1-06) | allowables temperature-independent 470 / 540 MPa [LITERATURE] | Mechanical | the 188 (5) table and the mill certificate |
| 16 | Servo output stiffness and inertia | k_s 58-174 N m/rad and J 0.76-2.7e-3 kg m2 ASSUMED; rocking 14.9-29.0 Hz at neutral (9A) | Electronics / bench B-TVC-1; REV-GNC | bench measurement |
| 17 | Runs not made (section 11) | c71x tie-impact runs and the J-FWD spring-footprint run (NOT RUN: no space after js5b, lead 18:50:09Z (5)); the TC-04 / OP shared route (NOT RUN, final, 03:30:46Z (2)); a compliant-airframe v3.5.2 run; a solved 21.5 s state; an R4 lever-root mesh; the modal on the production mesh (8 GB cap) | fea3d (if disk space or memory is granted) | as section 11 |

## 14. REV-MECH-2 findings: where each is folded (item 6)

Source: `reviews/REVIEW-MECHANICAL-R2.md` (`dbe81010096d76d5`; verdict REVISE, 0 blocking), adopted in full by CHANGELOG 234 with the rulings quoted below. "Done" means the v3.5.2 report carries the correction. "Pending" names the run or input that is still missing (section 11 / 13).

| Finding (class) | Line 234 ruling, short form | Where in this report | Status |
|---|---|---|---|
| RM2-01 (MAJOR; adopted in 231): the TC-01 J-FWD FA1S value is an idealisation number | 231 (1)-(3) + addenda (a)-(f): (a) withdraw "case Pm+Pb about +3.4"; net-section Pm 84.0 MPa at FA1S; (b) preload treatment of the screws; (c) the joint slips into bearing, so the screws are shear pins; (d) joint geometry, e/D 2.40; (e) LC2 in the contact sub-model at nominal and +25 % preload; (f) hole-edge profile | 10A: the one-sector contact sub-model replaces the full-bore RBE3. 10A.7 maps each addendum to the sub-model numbers. | done: js5, (a) / (a') / (a''), (b2), (b1), (b2'), js5b and cD posted; cD on the FINAL TC-01: s6 + C1 stand (lead 05:17:36Z (1)); final envelope v6 `43a5d78b67c615fc` (lead 02:01:34Z (E), 03:30:46Z (3), 05:17:36Z (3)); LC2 rule (A) ADOPTED 03:30:46Z (1); Mechanical's single IN718 re-map on v6 with `jfwd_v7inputs_cD_v352.json` (lead 05:27Z (3)) is Mechanical's (13) |
| RM2-02 (MINOR): LC2 rows missing; no factor conflict | LC2 = chamber MEOP 45 bar on the pressure parts, SF 1.5 / 2.0 at part temperature; LC2F (907.7 N, SF 1.0 / 1.5) stands as published; 231 (4) corrected | 10B (LC2 rows on the gap-variant bounds GVLO / GVHI) and the LC2 column of the matrix (3A) | done: GVLO (lc1v352g) and GVHI (lc1v352h) both solved and posted |
| RM2-03 (MINOR): "converged" at TC-01 J-FWD not supported; GCI has no applicability check | Wording '-0.1 % (L1 to R2), -2.2 % (R2 to R3); not in the asymptotic range; idealisation-dependent'; fix `post_conv.py` gci(); republish f1_convergence.json | 5.1 | done (`results/v352/f1_convergence.json`) |
| RM2-04 (MAJOR): the regular-node rule hides negative all-node values; the re-entrant flag is too broad | Every matrix cell carries the all-node minimum with node, class and distance. A regular value stands only behind a named sub-model or contact FE (owner and line), or where refinement converges. Re-entrant = BREP zero-radius concave edges or facet turns above about 60 deg. | 3 (matrix rule and columns), 4 (findings), 7.4 | done in `margin_matrix_v352.py`; chain E complete (34 runs DONE); the final matrix is the one re-run on the final J-FWD envelope (3A) |
| RM2-05 (MAJOR): post_k uses r_h 11.139 mm at every pose | r_eff per servo and pose; K with the servo in series at all 17 poses; republish k_stop / k_cone / k_range and the table, section 9, claim 9, the 8.1 table; label diagonal / coupled | 9 (+ the v3.5.2 model check at stop045; the R3 K table) | done: v3.5.1 model republished; v3.5.2 R3 table `results/v352/k_table_r3_v352.json` `f3c7cfbcfb98bcd7` (all 17 R3 poses, r_eff per servo and pose) |
| RM2-06 (MINOR): the modal deck's unit-pressure load differs (net axial 241.10 against 202.925 N/MPa) | Correct the load, re-solve the modal mesh's static OP, republish the share vectors with the bias stated | 9A. `asm_build` l1loads=TC-01 maps the L1 TC-01 face loads onto the L2 mesh (OP net 201.936 N/MPa, the value of the pose runs); `modal_v351ca2c_c71` | done: `modal_v351ca2c_c71` solved and posted; comparison `results/v352/modal_ca2c_vs_ca2b_v352.json` `1bdaf41b4611094c`; FA-1 band sensitivity re-run on ca2c (9A) |
| RM2-07 (MINOR): servo J missing from the "with servo" rocking pair | Quote K_s 58: 16.7 / 17.2 Hz; K_s 174: 24.5 / 26.0 Hz; 14.9-29.0 Hz over J 0.76-2.7e-3 kg m²; never 21-33 Hz as the loop-relevant pair | 9A (reproduced: 16.72 / 17.15 and 24.49 / 25.95 Hz, `results/v352/rocking_servo_J_v352.json`) | done |
| RM2-08 (MINOR): matrix completeness | Add the LC2 column, the LC3 lever-root R3 hot bound, the joints, the all-node companions, the 230 (2) band columns (94 / 121 / 147 bar abs), and FA1T for TC-01 with the reason the other pressure parts show '-' | 3 | done: columns in place; lever-root R3 hot bound from hbg3 / hbh3 (`lc3_hot_bound_v352r3_gvlo_gvhi.json` `c4ecb8b4e4a03afd`); the J-FWD column on the final envelope (10A.12) |
| RM2-09 (NOTE): F4 precisions | Recorded against v3.5.1 | 10 | done |
| RM2-10 (NOTE): 7075-T6 allowables are temperature-independent | The 188 (5) temperature table is owed by Mechanical | 13 (open item, Mechanical) | open (Mechanical) |
| RM2-11 (NOTE): mounting-data header and per-hole envelope | Datasheet rows = envelope of rigid and compliant airframe; header: 4.103 kg model mass included, 1.31 kg airframe-wall equipment excluded; sub-case notes | 8 (`results/v352/engine_mount_data_v352.json`) | done: v3.5.2 rows `results/v352/engine_mount_data_v352.json` `e5f41bde43a00ba4` (with the moment-free estimate, 4.5); compliant rows carried from v3.5.1 (marked c351) |
| RM2-12 (NOTE): reproduction details (121,788 vs 121,741 regular nodes; tensor-projection share 0.105 vs "<= 0.104") | No action | - | noted |
| RM2-13 (MINOR): the thermal map inherits the S-AX 0.10 mm closure at the TC-03 flange OD and the TC-01/TC-02 f7/H8 fit | 234 (7): disclose the inherited closure (REPORT 2.2, 4.1, 4.2); correct the thread-variant row text; quote -0.259 against R2 -0.266; use the 'thread' tie (or remove r > 9.9 mm and z 117.51 from TC03_TC02_seat) in v3.5.2; on the gap-conductance variant, re-map and re-post the whole of TC-03, the TC-02 seat and forward face and NZ-01 incl. n72033 at the four states + the instant of the S-AX TC-02 maximum, with the plug-to-bore dT (fit contact if above about 37-59 K) | 2.2 and 4.1-4.2 (disclosure, row text, -0.259 / -0.266), 10B (variant re-map; tie census `results/v352/tb1_tie_census_v352.json`; fit dT `results/v352/fit_dT_sax_v352.json` `93d87757edbcdcaf`; land-A closure `results/v352/landA_closure_gvhi_v352.json` `7754f21e2910220a`) | done: GVLO (`repost_5b_lc1v352g.json` `73905ef3358f8fa0`) and GVHI (`repost_5b_lc1v352h.json` `cc652bed59e6df9d`; n46040 in the GVLO form, 10B) |

**RM2-01 addenda against the v3.5.2 sub-model (10A.7):** (a) the case Pm+Pb is taken from the SCL lines of the sub-model, not from the RBE3 mid-ligament line. (b) Lead ruling, CHANGELOG 240: the FA1S screw criterion is NASA-STD-5020A Eq. 22 with the preload omitted. LC2 uses the combined form of 234 (1)(b) at the maximum preload. Mechanical maps the IN718 rows onto my FE envelope: `jfwd_in718_rows_v352_v3.json` `f69595255aa9543d` (accepted by the lead 14:03Z, as Mechanical's v4 records), now `jfwd_in718_rows_v352_v4.json` `6b41f1ce01e489f1` (adds the rev-5 worst-stack flat-bearing and OD h9 rows). (c) Slip: the FE seat window force and the contact status are reported per step. (d) The geometry is that of the v3.5.2 joint: 10 x M5 at 18 + 36k deg, tap wall 1.906 mm, spot face d10.5 (interim TC-01; the FINAL TC-01 has d11.2 flats, coplanar, and only cD is built on it: 2.1, 10A.2). (e) LC2 (LC2U / LC2Y / LC2N / LC2M) and FA1U / FA1D are in the js5b deck: s5, mu 0, IN718 screw properties (240 (9)(v)), 3750 N, which is the +25 % value of the 3.0 N m nominal 3000 N (lead relay 03:10Z). js5b ran 2026-10-21T01:18:59Z-03:16Z (rc 0) and was posted 03:18:21Z (10A.13); the LC2 parts criterion is the FE-factored state (LC2Y yield, LC2U ultimate), the hand form is information, the screw LC2N / LC2M rows are criterion (lead 03:30:46Z (1)). The 3750 N preload is the J-F1 cap (lead 17:56:12Z). The patch runs stay at 3750 N on A4-80 properties for consistency with js5, and Mechanical maps them to IN718 (240 (9)(v)). (f) The hole-edge profile is replaced by the sub-model's 54 seat lines and the ligament station.
