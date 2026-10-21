# REVIEW-MECHANICAL-R2 - independent review of the FEA3D assembled-engine 3D FE (REV-MECH-2)

**Conventions**
- **Tags.** SIM: FE output (a reviewer re-post of FEA3D's stored unit fields with the reviewer's own code is still SIM). DERIVED: reviewer arithmetic from tagged inputs. ASSUMED, DATASHEET, TO-VERIFY, AS RECALLED as usual; the author's LITERATURE tag is quoted as given.
- **Units.** mm, N, MPa, degC. MS = allowable(T) / (SF x stress) - 1; "y / u" = yield / ultimate.
- **Node sets.** "Regular" = FEA3D's set (REPORT 2.4: nodes more than 1.0 mm from RBE3 / rigid / ground / tie-patch edges / re-entrant facet edges (dihedral > 30 deg, concave) / bad tets q < 0.1). "All-node" = every node. "Class" = the exclusion class of the nearest singular node and its distance in mm.
- Matching numbers prove repeatability, not physical acceptance. **Nothing in this review is physical approval.**

## 0. Verdict and checkpoint (SUPERVISION-WORKFLOW)

**Verdict: REVISE.** 0 BLOCKING; 3 MAJOR (RM2-01, adopted by the lead as CHANGELOG 231; RM2-04; RM2-05); 6 MINOR (RM2-02, RM2-03, RM2-06, RM2-07, RM2-08, RM2-13); 4 NOTE (RM2-09 to RM2-12).

Why, in four lines:
1. The stored solution reproduces.
   - My re-solve of the FA-1 deck's TH and OP steps (ccx 2.21, lead-authorised) matches FEA3D's stored fields to float precision: relative norm difference 2.6e-8 on stress, 0.0 N on all 32 airframe-hole totals.
   - Every margin I re-posted from FEA3D's unit fields with my own code matches the published value to the published decimals at the same node.
   - Equilibrium, free-body and membrane hand checks close within 0.3 %. The solver output is not in question.
2. Three published statements do not hold as written:
   - the FA1S J-FWD value is an idealisation number, and "converged" is not supported (RM2-01, RM2-03);
   - the regular-node rule hides negative all-node values at four locations, one of them in a nominal case (RM2-04);
   - the "with servo" gimbal stiffnesses are wrong off-centre (RM2-05).
3. The margin matrix lacks the LC2 (MEOP) rows, the refined lever-root hot bound, the joints and the restated FA-1 bands (RM2-02, RM2-08).
4. The TC-03 corner and TC-02 seat values rest on a mapped thermal field in which two designed clearances are closed: the TC-03 flange OD gap and the TC-01/TC-02 f7/H8 fit (RM2-13). Both stay classified as they are, but their values are open until the gap-conductance variant is re-mapped.

**Permitted use until the revision.**
- Regular-set margins as found, together with the all-node list in section 6 of this review.
- All negatives as found. The TC-03 and TC-02 values are quoted with the RM2-13 dependence.
- Rigid-servo stiffness K (F3) as published; the with-servo K only at the neutral pose.
- Modal frequencies only with the J statement of RM2-07.
- Mounting data with the RM2-11 notes.
- Nothing here approves hardware.

**Checkpoint**

| Item | Content |
|---|---|
| Delivered by / reviewed by / date | fea3d (successor Senior FEA analyst 3D) / REV-MECH-2, independent, read-only on the author's hub folders and the FEA3D working tree / 2026-10-20. The lead records the verdict; I wrote only `reviews/mechanical/r2/` and this file. |
| Area and configuration | ARGOS H1 assembled-engine 3D FE: CAD v3.5.1 frozen; CalculiX 2.21 C3D10; fea3d-asm v1.2 (L1 171,123 nodes). F2 = S-3D on v3.5.1 (9 cone poses, lever roots R3). F3 = gimbal stiffness. F4 = joints. Modal = all-L2, 83,173 nodes, 60 modes to 5130 Hz. |
| Claims checked | REPORT-FEA3D section 1, claims 1-12, plus 9A / 9A.1 / 9B / 10, against the brief's criteria (a)-(h) and (f2). |
| Criteria | REQUIREMENTS ENG-09 / ENG-10 / ENG-11 (lines 60, 61, 62); CHANGELOG 183 (1), 188 (3) / (5) / (9), 194 (1), 212, 223, 227, 230, 231, 232; loadcases_v1. |
| Method and checks run | Section 2. |
| Not demonstrated | Section 12. |
| Interim | Sent 2026-10-19 about 23:50Z (RM2-01, RM2-02). The lead adopted RM2-01 (CHANGELOG 231). Corrections to my interim are in RM2-01 (a) and (b) and in section 5. |

## 1. Inputs and integrity (sha256/16, read 2026-10-19/20)

| Input | sha256/16 | Check |
|---|---|---|
| `04-fea/assembly3d/MANIFEST.json` | fa25b7f9ff8a19b7 | 209 / 209 listed files match. 12 files on disk are not listed: REPORT-FEA3D-HANDBACK.md and 11 superseded results (f1_lc3_hot_bound, f1_post_fa1_v351, f1_post_lc1v351_design_rigid, 8 x f1_post_lc3_pose_stopXXX without _c71). |
| `04-fea/assembly3d/REPORT-FEA3D.md` | ff24718e9db201e5 | The HANDBACK copy (7dfb4f8b53eaf84f) differs only by the BEGIN / END lines. |
| `04-fea/s3d_v351/MANIFEST.json` | c650c7449af04738 | 88 / 88 match. |
| `04-fea/s3d_v351/REPORT-S3D.md` | 88c34c5fe7394e60 | |
| `interfaces/CHANGELOG.md` | 2fc2c87d796bfb8d | 233 lines. At the brief it had 230 lines (838fb2278498d908). Line 231 = lead interim on REV-MECH-2; line 232 = GNC rev4b staged; line 233 = Mechanical v3.5.2 INTERIM, read for context only. Line 233's v3.5.1 J-FWD screw value, -0.139 at 45 C, agrees with RM2-01 (b): -0.10 RT and -0.15 hot with the ASSUMED k_T proxy. |
| `04-fea/assembly3d/src/asm_build.py` / `asm3d.py` | a98509e27cc1dc99 / 01e146a3ef668ba6 | Ties, TB1 pressure ring, thermal map (RM2-13); identical to the FEA3D working tree. |
| `03-cad/src/parts_engine.py` | 6150bddad816b403 | TC-02 / TC-03 / NZ-02 geometry and fits (RM2-13). |
| `04-fea/thermal/ax_thermal.py` | cd00f37a02ddbfd2 | TOL_MM 0.10 closure rule (RM2-13). |
| `04-fea/assembly3d/results/f1_post_tc03_thread.json` | 6486568413df1073 | TB1 thread-only variant (RM2-13). |
| `reviews/REVIEW-MECHANICAL-R1.md` | dc1c1c6b8931c95d | |
| `00-requirements/REQUIREMENTS.md` | 012b14cbaaddfdc6 | |
| `04-fea/loadcases_v1.json` | cbafa22eb69ef039 | LC2 / LC2F definitions. |
| `04-fea/src/engmat.py` (allowables) | 46ba163b864c7fc5 | |
| `03-cad/src/data/hardware_v351.json` | 0938bd1c13701524 | HW-101 J-FWD M5 A4-80, 5.53 N m. |
| `04-fea/stiffness/gimbal_k_summary_V5c_v1.json` | 82a737caa138259a | |
| `01-systems-gnc/staging_v3.1/rev4b/REPORT-GNC-rev4b-HANDBACK.md` | 6748187541eba25a | |
| `01-systems-gnc/staging_v3.1/rev4b/eng11_fe/scripts/m2_eng11_fe.py` | fab0f05eb87d8e61 | |
| `interfaces/combustion.json` v2.4b | fd3a7da6d27c7c66 | OI-51 / OI-52. |

FEA3D results read (hub):

| File | sha256/16 |
|---|---|
| f1_post_fa1_c71.json | 7d5970a387779ab3 |
| f1_post_lc1v351_c71.json | 79507be526bde2dc |
| f1_post_lc3_pose_stop045_gm02r3_c71.json | b08642ae806bb02d |
| s3d_pose_alpha-_c71.json | f1df085c84c044ce |
| margin_matrix_v351.json / .md | edaaff6bdf7d392a / 1067bc60db684d15 |
| f1_convergence.json | c2fd80b99e120462 |
| fa1_band_sensitivity.json | 794155b97167a784 |
| modal_modal_v351ca2b_c71.json | 9af80c657eed11ac |
| k_cone_c71.json / k_stop_c71.json / k_range_v351.json | bfb9b56ed85b6a2f / fd9ca16b0b3d2304 / 27421efb09e7daf0 |
| engine_mount_data_v351.json | 7aa3faf0f15d992d |
| f4_secondary.json | 0746e62e2d9e87da |
| src/post_k.py, src/post_conv.py, src/f4_secondary.py | 63a67bfe4639c660, 66b966c11c578894, 72fe3708f5f2aa28 |

FEA3D solver bulk read, from `/home/claude/work/fea3d/runs/`:

| File | sha256/16 |
|---|---|
| fa1_c71/A1_22.2/fields.npz | ae445b96ed1526e1 |
| fa1_c71/A1_22.2/f1.inp.gz | 9e048668353fa96e |
| fa1_c71/A1_22.2/f1.dat | 45d47759fd2dfb36 |
| lc1v351_c71/{B1_1, B1_2, B1_19, B1_21.65}/f1.inp.gz | ca8facc70411706d / 01ea6856d45a9ca5 / ec0910e7734abe5b / fec518ce72f59805 |
| lc1v351_c71/B1_1/thermal.json | 2768777863b08afc |
| conv_r2/model.json / tc03_thread/model.json | 2e006523742971a8 / e15288ad6400dc58 |
| fa1_c71/A1_22.2/T.npz | a9c9e34e0cf3f50b |
| fa1_c71/model.json | 9335d8c096c51472 |
| lc1v351_c71/{B1_21.65, B1_19, B1_2, B1_1}/fields.npz | dd9f4c2893b3beec / c7d28fb5f40e681d / 580804f0588b8c4b / 0dd537cc6c3c2d43 |
| lc1v351_c71/model.json | 11468eb3e0cea224 |
| modal_v351ca2b_c71/B1_21.65/fields.npz | 86803cf464e24b14 |
| modal_v351ca2b_c71/model.json | 54bfa4605785f9a7 |
| pose_stop045_gm02r3_c71/B1_21.65/fields.npz | 1aa506d510619952 |
| pose_alpha-_c71/B1_21.65/fields.npz | 349b3a9665dbe125 |
| pose_neutral_c71/B1_21.65/fields.npz | de0a32d6fa3db7ae |

## 2. Method (what I re-ran)

**Own code** (`reviews/mechanical/r2/scripts/`, Python, no FEA3D module imported).

| Script | What it does |
|---|---|
| `rm2_deck.py` | Deck parser. |
| `rm2_repost.py` | Unit-step combination S = S_TH + sum c_i (S_i - S_TH); von Mises and principal stresses; allowables at node temperature from the hub engmat. Brittle parts: s1/St and s3/Sc at the case ultimate SF, with the char zone on primary s3. Rebuilds the regular set with the published rule and audits the exclusions (minimum MS per exclusion class). |
| `rm2_lc3.py` | LC3 runaway and F2 GS: own rod forces, fb_run search and moment residual. |
| `rm2_modal.py` | Modal decomposition from FEA3D's stored eigenvectors. Own integration of the deck's unit-pressure *DLOAD faces (6-point Gauss on the 6-node faces). Own C3D10 stress probe. |
| `rm2_servo_g.py` | Servo kinematics: effective horn radius per pose and servo. |
| `rm2_handcalc.py` | Hand checks. |
| `rm2_resolve_cmp.py`, `rm2_resolve_extra.py` | Re-solve comparison: U / S against fields.npz, FA1S at the governing nodes; hole totals against f1.dat; ccx error estimator. |
| `rm2_closure.py` | TB1 tie census, TC-01 / TC-02 coupling, mapped-temperature continuity across both closed clearances, TC-03 corner stress components (RM2-13). |
| `rm2_*_probe / faces / resultant / hist` | Diagnostics. |

**Cases re-posted** (pose runs use the stored unit fields):
- FA1Q / FA1D / FA1U / FA1S (A1_22.2) and FA1T.
- The restated FA-1 band values of CHANGELOG 230 (2): 94 / 121 / 147 bar abs.
- LC1 at 4 states.
- LC2 at MEOP 45 bar, 4 states, SF 1.5 / 2.0 (new; section 5).
- LC3 stop045 lever root R3 (64 sub-cases).
- F2 GS at alpha- (lever roots R3).

**Hand checks:**
- J-FWD joint at FA1S and LC2.
- TC-01 membrane and section force.
- Mount equilibrium for every case.
- Engine free body.
- F4 J-FD01 / J-FD09 re-computed from the published loads.
- Allowable requirements implied by LC2.
- Servo-in-series rocking frequencies with and without J.

**Re-solve (one cheap re-solve, done)** [SIM, reviewer ccx run].

History:
- My first attempt (01:04Z, PID 31177) collided with another agent's queue under the one-ccx rule. I stopped it after 63 s with no results.
- The lead then authorised one concurrent run with conditions: nice 10, 6 GiB address-space cap, 2 threads, gzip the .frd.

The run:

| Item | Value |
|---|---|
| Deck | TH + OP steps of fa1_c71/A1_22.2: lines 1-561367 of f1.inp.gz, unchanged (sha16 2f8d313be40b129e, equal to those lines of 9e048668353fa96e) |
| Solver | CalculiX 2.21, spooles, 471,278 equations |
| Run | 01:19:09-01:21:11Z, 122 s; peak VmHWM 3.04 GiB, VmPeak 3.26 GiB, so the cap was not reached |
| Settings | nice 10; `prlimit --as=6442450944`; OMP_NUM_THREADS = CCX_NPROC_EQUATION_SOLVER = 2; alongside Mechanical's ccx PID 31180, untouched |
| Output | .frd gzipped in the reviewer scratchpad (not in the hub); log `logs/rm2_resolve_run.log` |

Comparison with FEA3D's stored fields.npz (`rm2_resolve_cmp.py`, all 171,191 nodes):

| Quantity | Step TH | Step OP |
|---|---|---|
| U, max abs difference | 1.0e-11 mm | 1.0e-8 mm |
| U, relative norm difference | 3.5e-13 | 2.4e-10 |
| S, relative norm difference | 2.6e-8 | 2.6e-8 |
| von Mises, max abs difference | 8.7e-6 MPa | 8.2e-6 MPa |

- FA1S von Mises at the governing nodes, rebuilt from the re-solved TH / OP fields and the stored PM increment, matches the stored value within 1e-5 MPa: 302.950 MPa at node 8314 (the published J-FWD value), 374.775 at 580, 280.626 at 25946, 237.700 at 27955.
- Airframe-hole totals (`rm2_resolve_extra.py`, 16 sets x 2 steps) equal FEA3D's f1.dat at print precision, max |dF| 0.0 N. The OP step's sum of Fz is -202.9248 N, equal to the net pressure thrust per MPa.
- CalculiX's own stress error estimator (ERROR, STR %) at the governing nodes is 17-31 %: node 8314 30.9 / 24.9 % (TH / OP); 580 21.9 / 16.6 %; 25946 18.8 / 18.0 %; 27955 18.7 / 22.2 %. This indicates a coarse L1 mesh at these nodes, consistent with RM2-03. It is an indicator, not a convergence measure.

Reproduction therefore rests on:
- the re-solve, which reproduces the stored TH and OP fields;
- re-posts of FEA3D's stored fields, which are identical;
- equilibrium of the stored solution against the applied loads, which closes;
- my stress probe on the modal mesh, which matches ccx: 14.822 against 14.823 MPa/MPa.

**Thermal-closure check** (`rm2_closure.py`, own code on the stored lc1v351_c71 decks and fields; no solve). For the lead's question of 2026-10-20, it checks:
- the TC03_TC02_seat tie, from the deck equations;
- any TC-01 / TC-02 coupling;
- the mapped temperatures across both interfaces at all four states;
- the thermal stress components at the TC-03 corner;
- FEA3D's own TB1 variants, as published.

Results: RM2-13.

## 3. Claims checked (REPORT-FEA3D section 1)

| # | Claim (short) | Result | Evidence [tag] |
|---|---|---|---|
| 1 | 7.1 closed; engine free body 100 % | **CONFIRMED** on the published connector forces | FA1S: 2 x 1517.4 (inner cups) + rods (46.9 - 16.7) = 3065.0 N against the applied 3064.9 N. FA1Q: 2 x 903.9 + 18.4 = 1826.2 against 1826.3 N [DERIVED]. Rod SPRINGA k 11,418.2 N/mm in the solved decks. The unit-step closure itself was not re-run step by step. |
| 2 | Fix changes engine stresses <= 0.15 %, bearing loads materially | not re-checked (v1.1 fields not re-posted) | FA1S cup load 1517 N is consistent with the free body. |
| 3 | LC1: NZ-01 -0.435, TC-03 -0.312 / -0.375, TC-02 +0.096 / -0.119; others positive | **CONFIRMED**; others positive **in the regular set only**; the TC-03 and TC-02 values rest on a thermal map with two designed clearances closed (RM2-13) | Re-post identical at the same nodes (NZ-01 B1_1 n74445; TC-03 B1_1 n44861; TC-02 B1_19 n26334). Hidden all-node values: NZ-01 -0.522, NZ-03 tie edge -0.071 (RM2-04). |
| 4 | FA1S TC-01 J-FWD -0.221 / -0.160, "converged (R3 -0.202 / -0.140)"; FA1Q / D / U positive; FA1T positive; band reading | value **CONFIRMED** (node 8314, 302.95 MPa); "converged" **NOT SUPPORTED** (RM2-03); the value is not a criterion result (RM2-01); the band reading is superseded by 230 (1) (section 7) | FA1Q +0.291 / +0.393, FA1D +0.251 / +0.349, FA1U +0.144 / +0.233 identical. FA1T identical (GM-03 +1.483 / +1.671 at n129757). |
| 5 | LC3 lever roots R3 -0.280 / -0.379 (GM-02), -0.273 / -0.374 (GM-01) | **CONFIRMED** (GM-02 re-posted) | stop045 R3: 435.1 MPa at n66500 [33.57, -157.8 deg, -6.20]; fb_run 322.6-417.4 N; max rod 609.0 N; actuator moment <= 34.77 N m (limit 41.14); BUMP moment residual 2.83 % (FEA3D 0.02829) [SIM re-post]. |
| 6 | LC3 hot bound values | accepted, not re-derived; the R3 hot bound is missing (RM2-08) | - |
| 7 | Airframe 16 x M5 hole loads; rigid bounds compliant | totals **CONFIRMED** by equilibrium; "rigid bounds" holds for the maximum hole, not per hole (RM2-11) | Section 9. |
| 8 | F4: J-FD01 -0.41 / -0.20, J-FD09 -0.17 / +0.05, others +0.04 to +0.15 | **CONFIRMED** (within 0.0005) with precisions (RM2-09) | Section 9. |
| 9 | F3: rigid-servo K ranges; with-servo 686-2891 N m/rad | rigid-servo K accepted (not re-derived); **with-servo K NOT CORRECT off-centre** (RM2-05); neutral confirmed | Section 8. |
| 10 | Modal 51.4 / 59.4 Hz; about 48 / 56 at the production K; 21-33 Hz with servo; axial 408 Hz; pintle 186 Hz | numbers **CONFIRMED**; J missing (RM2-07) | Section 8. |
| 11 | F2 GS negative at both lever roots | **CONFIRMED** at alpha- | GM-02 -0.223 / -0.330, 403.15 MPa at n74502 [SIM re-post]. |
| 12 | Mounting data per case | **CONFIRMED** by equilibrium; header notes (RM2-11) | Section 9. |

## 4. Findings

### RM2-01 (MAJOR; ADOPTED by the lead, CHANGELOG 231) - TC-01 J-FWD FA1S value is an idealisation number, not a criterion result

**Evidence** [SIM re-post / DERIVED]:
- FA1S -0.221 / -0.160 is the von Mises 302.95 MPa at node 8314. That is the first regular node, 1.14 mm from the hole edge and 1.435 mm from the JF1_case RBE3 patch, of a full-bore RBE3 screw idealisation without contact.
- L1 / R2 / R3: 303.0 / 302.6 / 295.9 MPa regular and 357 / 382 / 399 MPa all-node; not converging (RM2-03).
- The basis and corrections are as adopted in 231 (1)-(3).

**Addenda to 231 (corrections of my interim and new evidence):**
- **(a) Withdraw "case Pm+Pb about +3.4"** in 231 (1). That figure was FEA3D's case_screw_row SCL (a mid-ligament line between holes, full-bore RBE3) scaled to FA1S. The net-section primary membrane at the hole row is:

  Pm = (sum of screw shears) / A_net = 38.8 kN / 462.0 mm² = 84.0 MPa (A_net = A_gross 601.7 - 8 x 5.5 x 3.175 mm²)

  | Case (SF) | Pm (MPa) | MS y / u |
  |---|---|---|
  | FA1S (1.0) | 84.0 | +1.81 / +2.03 |
  | LC2 (1.5 / 2.0) | 25.0 | +5.15 / +3.94 |

  The case ligament is still not the marginal item [DERIVED].
- **(b) Screw checks must include the HW-101 installation preload.** Screw: M5 A4-80 at 5.53 N m, fully threaded, minor area 12.686 mm² (d3 4.019 AS RECALLED); stress area As 14.18 mm². Shear per screw (from FEA3D's connector forces, 321.28 N/MPa per screw; p A_bore / 8 gives within 0.7 %): FA1S 4853 mean / 4879 max N; LC2 1446 / 1454 N.

  | Check | FA1S (SF 1.0) | LC2 (SF 1.5 on shear) |
  |---|---|---|
  | Shear alone, minor area, RT (τ_y 0.577 x 600, τ_u 0.6 x 800 MPa, ASSUMED factors) | -0.10 / +0.25 (τ 384.6 MPa). The interim's -0.09 / +0.26 used the mean shear. | +1.01 / +1.10 |
  | Shear alone, minor area, hot (ASSUMED proxy k_T = SS316L Fty(T)/Fty(20)) | -0.15 / +0.18 (k_T 0.945 at 45.9 degC) | +0.76 / +0.83 (k_T 0.874 at 79 degC) |
  | Shear alone, stress area | +0.006 / +0.395 | - |
  | Combined von Mises, unfactored preload 5.53 kN on As (390 MPa; K 0.2 ASSUMED, as F4) + factored shear on the minor area, against k_T Rp0.2 600: nominal RT / nominal hot / +25 % preload hot | **-0.22 / -0.27 / -0.31** | **+0.22 / +0.07 / -0.08** |

  So 231 (1)(ii) must name the preload treatment: a VDI-type combined check, or shear-only with its source and the preload-relaxation argument for a one-off FA-1. The J-FWD change must also clear LC2 (a nominal case) with the preload scatter, not only FA1S [DERIVED].
- **(c) The joint slips into bearing in every pressurised case.** Friction capacity at nominal preload, μ 0.2 [ASSUMED]: 8 x 0.2 x 5.53 kN = 8.85 kN, against a total load of 38.8 kN at FA1S and 11.6 kN at LC2. The screws are shear pins every firing, so hole bearing, fretting and wear over the firing count belong to the sizing and to the inspection rule of 231 (1)(iii) [DERIVED].
- **(d) Geometry for the joint checks.** e = 12.0 mm from the hole centre (z 127.51) to the TC-01 forward end (z 139.51), e/D 2.40.
  - Case bearing at FA1S: 307.3 MPa against Fbry / Fbru 330.5 / 407.3 MPa (engmat e/D 2.0 ratios, conservative at 2.40), MS +0.075 / +0.325.
  - Shear-out (two planes, length e - D_hole/2): 83.0 MPa, MS_u +0.84.
  - LC2 bearing: +1.35 / +1.16 [DERIVED].
  - TC-02 tapped-thread bearing and thread shear were not checked here (no engagement length in the hub).
- **(e) LC2 is in the scope of the 231 (3) sub-model.**
  - At LC2 the TC-01 all-node hole-edge value is -0.031 ultimate (node 580, 0.914 mm from the JF2_case RBE3; regular +0.488 / +0.196).
  - The combined screw check at LC2 is -0.08 (row (b)).
  - The contact sub-model therefore runs LC2 (1.5 / 2.0) as well as FA1S (1.0).
- **(f) Hole-edge profile at FA1S** for the 231 (1)(iii) local-strain check. Minimum MS_y over the 8 holes, by distance from the hole edge [SIM re-post, RBE3 idealisation, orientation only]:

  | Distance from the hole edge | MS_y |
  |---|---|
  | edge | -0.370 |
  | 0.5-1 mm | -0.245 |
  | 1-1.5 mm | -0.221 |
  | 1.5-2 mm | -0.127 |
  | 2-3 mm | +0.052 |
  | 3-4 mm | +0.341 |

  TC-02 at the same holes:

  | Location | MS_y |
  |---|---|
  | Tapped-hole mouth (node 25946) | -0.158 |
  | 0.5-1 mm | +0.360 |

**Owner:** Mechanical (v3.5.2 J-FWD change); FEA3D (231 (3) re-check).

### RM2-02 (MINOR) - LC2 (chamber MEOP 45 bar) rows missing; the factor question has no conflict

**Evidence.**
- The margin matrix has no LC2 column.
- The F2 LC2F column (907.7 N failure thrust, gimbal and mount parts, SF 1.0 / 1.5) is correct, but it does not cover the pressure parts at MEOP.
- REQUIREMENTS line 60 (ENG-09) and loadcases_v1 LC2 require the pressure parts at 1.5 / 2.0 at MEOP and temperature.
- Recommendation and basis: section 5.

**Correction.**
- FEA3D adds an **LC2** column: loadcases_v1 LC2 (chamber 4.5 MPa on the operating distribution, manifold 7.0 MPa, hottest thermal state, SF 1.5 / 2.0 at part temperature), for every pressure part and the J-FWD screws.
- LC2F stays as published.
- Values from my re-post: section 5.
- 231 (4) is restated by the lead as "LC2 rows (MEOP 45 bar, 1.5 / 2.0)". My interim column (OP 4.473 MPa, labelled LC2F, at both factor sets) is withdrawn.

**Owner:** FEA3D (matrix); lead (record).

### RM2-03 (MINOR) - "converged" at TC-01 J-FWD is not supported; the GCI routine has no applicability check

**Evidence** [SIM / DERIVED]:
- Regular-set maxima L1 / R2 / R3 = 303.0 / 302.6 / 295.9 MPa (h 3.04 / 1.28 / 0.68 mm).
  - ε32 = 0.4 and ε21 = 6.7 MPa, so ε32/ε21 = 0.06: the fine-level change is 17 times the coarse-level change.
  - An asymptotic sequence has ε32/ε21 = r^p > 1.
- The quantity is the maximum over nodes at least 1 mm from the RBE3 patch. Its location is tied to an absolute exclusion distance while h shrinks, so it is a property of the idealisation (RM2-01).
- `src/post_conv.py` gci(), line 58: `pn = abs(math.log(abs(e32 / e21)) + qq) / math.log(r21)`. The absolute value returns a positive order also when |ε32/ε21| < 1. This is the Celik et al. formula applied without its asymptotic-range condition (AS RECALLED).
  - `results/f1_convergence.json` therefore carries p 7.14 / GCI_fine 0.031 % for TC-01 and p 6.15 / GCI_fine 0.049 % for TC-02 (102.37 / 102.1 / 83.0 MPa).
  - REPORT section 5 correctly declines to quote them.
  - Claim 4 ("converged (R3 -0.202 / -0.140)"), 4.5 ("converged within 2.4 %") and CHANGELOG 217 ("converged L1/R2 0.1 %") say otherwise.

**Correction.**
- Claim 4 and 4.5 read: "level-to-level -0.1 % (L1 to R2) and -2.2 % (R2 to R3); not in the asymptotic range; idealisation-dependent (231 (1))".
- gci() returns no order and no GCI when |ε32/ε21| < 1 for a monotone sequence; republish f1_convergence.json.
- The lead corrects 217 in the record.

- CalculiX's own stress error estimator, from my re-solve (section 2), is 30.9 % (TH) and 24.9 % (OP) at node 8314, and 17-22 % at the other three governing nodes. This is consistent with a mesh that is not converged at J-FWD [SIM, indicator only].

**Accepted as stated** [SIM]:
- NZ-01 is non-asymptotic and worsens (-0.435 / -0.454 / -0.481).
- TC-03 oscillates (-0.312 / -0.266 / -0.342).
- TC-02 depends on the tie end; no converged TC-02 ultimate is claimed.
- The lever-root R3 evidence holds: 420 to 416 MPa at 0.5 mm from the edge line, peak inside the ball in all 9 F2 poses.

**Owner:** FEA3D.

### RM2-04 (MAJOR) - the regular-node rule hides negative all-node values; the re-entrant flag is too broad

**Evidence** [SIM re-post; table in section 6]:

| Case | Location | All-node (excluded) | Regular |
|---|---|---|---|
| FA1S | TC-02 tapped-hole mouth | -0.158 / -0.092 | +0.855 / +1.001 |
| FA1S | NZ-03 tie edge | -0.126 | +0.630 |
| LC1 | NZ-03 tie edge | -0.071 | +0.476 |
| LC1 | NZ-01 | -0.522 | -0.435 |
| LC2 | NZ-03 | -0.484 | -0.089 |
| LC2 | TC-01 J-FWD | -0.031 u | +0.196 u |
| LC2 | TC-02 tie edge | -0.159 u | -0.134 u |

Re-entrant flags on L1: 8,426 concave edges. Of these, 42 % turn by 30-40 deg and 59 % by 30-50 deg: facets of meshed fillets and blends, not zero-radius edges. Another 26 % turn by 80-120 deg. TC-02 alone has 1923 such edges, GM-10 1044, GM-09 730. FEA3D's own 4.6 shows the consequence: GM-02 lever root L1 +0.182 became R3 -0.280 once the flagged fillet zone was resolved.

**Correction.**
1. Every matrix cell carries the all-node minimum, with node, class and distance, beside the regular value.
2. A regular value may stand for a part only where the all-node minimum is either:
   - (a) at a connector or tie idealisation that a named sub-model or contact FE replaces (owner and line given); or
   - (b) shown by refinement to converge, in which case the refined value is used, as in 4.6.
3. The re-entrant class is restricted to BREP zero-radius concave edges, or to facet turns above about 60 deg. Fillets smaller than the local h are refined, not excluded.
4. The present all-node negatives are listed as found, with their routing:
   - TC-02 mouth and TC-01 J-FWD (FA1S, LC2, FA1T): 231 (2) / (3).
   - NZ-03 tie edge: the RM1-03 contact FE (188 (3)) and N-F1, with the tie-edge requirement stated. If the tie edge is real it needs Sc >= 21.5 MPa (LC1), 22.9 MPa (FA1S, SF 1.0) and 38.6-38.8 MPa (LC2).
   - NZ-01: -0.522 is reported as the LC1 value, because refinement already worsens NZ-01.
   - TC-02 LC2 tie edge: T-F2.

**Owner:** FEA3D; the lead decides the rule.

### RM2-05 (MAJOR) - post_k uses the full horn radius at every pose ("with servo" stiffness wrong off-centre)

**Evidence** [DERIVED from FEA3D's K_FE and model rod geometry]:
- `src/post_k.py` lines 103 and 109 use `g["r_h"]` = 11.139 mm, where the docstring (line 11) defines r_eff.
- Off-centre the rod is not normal to the horn. Then r_eff = |((H - C) x e) . e_t|, where H is the horn eye, C the shaft centre, e the rod direction and e_t the shaft axis. It ranges from 7.88 to 11.14 mm and equals V5c's lambda_h(pose), for example alphap7 10.233 / 10.710 mm.
- The per-axis servo stiffness ratio, kinematic over post_k, is 1.085-1.339 on the off-centre cone poses and 1.103-1.586 at the stops. This is identical to GNC rev4b's g_kin/g_fea (CHANGELOG 232 (2)).
- With the servo in series:

  | | post_k (published) | Kinematic |
  |---|---|---|
  | K_s 58 | 686-1364 N m/rad | 787-1759 N m/rad |
  | K_s 174 | 1522-2891 N m/rad | 1681-3436 N m/rad |

  - The largest ratio is 1.45 (alpha, stop poses, K_s 58). Neutral is unchanged: 1129 / 2586 and 1070 / 2295.
  - The coupled value with the other axis free is lower than the diagonal one (alpha stops 1388 against 1523 at K_s 58).
- Consequence: a K_s window built on the post_k values overstates its top. GNC's B04 variant (FEA3D g) gives 130 against 120 N m/rad with exact kinematics (rev4b handback: "non-conservative by 10").

**Correction.**
- post_k.py uses r_eff per servo and pose.
- Republish:
  - k_stop_c71.json, k_cone_c71.json, k_range_v351.json and tables/k_range_v351.md;
  - REPORT section 9 tables, claim 9 and the 8.1 stiffness table.
- Label the diagonal (other axis held) and coupled values.
- The modal servo-in-series frequencies are at neutral and are unaffected.

**Owner:** FEA3D.

### RM2-06 (MINOR) - the modal deck's unit-pressure load differs from the production model

**Evidence** [SIM: own face integration of the decks' *DLOAD; no duplicate faces in either deck]:
- Net axial 241.10 N/MPa (modal, all-L2), against 202.925 (L1 fa1_c71) and 201.94 (pose runs).
- TC-01 at L2 carries 391.0 against 351.8 N/MPa: wetted-face facets with axial normals near the head joint (z 100-112) and at the aft end (z -160 to -150).
- The other L2 bodies cancel to -1.0 N/MPa, as in the pose runs.
- Static OP stress: 14.82 against 17.39 MPa/MPa at the J-FWD node (-15 %, tensor different) and 8.75 against 12.92 at the LC1 node (-32 %).
- The 60 modes reproduce the modal deck's own static displacement to 11.8 % (norm); the rest is the residual.
- Shares are ratios on one model, so the load error enters only through its distribution. It changes no margin now, since J-FWD is sized on FA1S per 230 (1) and 231, but it enters OI-51.

**Correction.**
- Correct the L2 TC-01 wetted-face set, or map the L1 face loads.
- Re-solve the static OP step on the modal mesh (no new eigen run) and republish the share vectors.
- State the bias in 9A.

**Owner:** FEA3D.

### RM2-07 (MINOR) - servo inertia J is missing from the rocking frequencies quoted "with the servo in series"

**Evidence** [DERIVED]:
- GNC's plant adds J reflected by the kinematic factor: f = sqrt(K_tot / (I_piv + J g)) (m2_eng11_fe.py line 14; 227 (2) "ADDED to I_piv").
- On the FE linkage at neutral, g = sum (a_i / r_h)² = 23.04 (a = 37.806 mm, r_h = 11.139 mm, two chains), which is n² for n = 4.8.
- With J = 1.6e-3 kg m²: f x 0.783 (beta) / 0.785 (alpha). The pair becomes 16.7 / 17.2 Hz at K_s 58 and 24.5 / 26.0 Hz at K_s 174, instead of 21.3 / 21.9 and 31.3 / 33.1 Hz.
- Over J 0.76-2.7e-3 the pair spans 14.9-29.0 Hz (factor 0.70-0.88; lumped model).
- REPORT 9A says only that J "would lower these further".
- My own earlier note of a 1:1 addition (f x 0.98-0.99) is not GNC's convention and is withdrawn.

**Correction.** 9A, 8.1 and 13 #12 quote the J-inclusive values and their basis beside the J-free values. The datasheet must not present 21-33 Hz as the loop-relevant rocking pair.

**Owner:** FEA3D; GNC / datasheet.

### RM2-08 (MINOR) - margin-matrix completeness

**Corrections:**

(a) Add LC2 (RM2-02).

(b) Add the LC3 lever-root R3 hot bound, which is missing. Values are DERIVED by adding FEA3D's own L1 hot increments (GM-02 +12.8 MPa, GM-01 +3.5 MPa) to the R3 cold peaks:

| Part | R3 hot bound MS y / u |
|---|---|
| GM-02 | -0.30 / -0.40 |
| GM-01 | -0.28 / -0.38 |

These are approximate until 13 #14 is run.

(c) Add the joints (J-FWD screws, F4 joints) as rows or as a linked joint table, as 183 (4) asks.

(d) Add the all-node companion values (RM2-04).

(e) Add the FA-1 band columns restated by 230 (2) (provisional). My re-post at 94 / 121 / 147 bar abs gives, for TC-01 regular:

| Band value | TC-01 MS y / u |
|---|---|
| 94 bar | +0.238 / +0.335 |
| 121 bar | -0.032 / +0.044 |
| 147 bar | -0.200 / -0.137 |

Every other part is positive in the regular set. All-node negatives appear only at TC-01 (RBE3 patch), the TC-02 mouth (-0.135 at 147 bar) and the NZ-03 tie edge (-0.102 at 147 bar). The 121 bar value is close to Combustion's DERIVED -0.039 / +0.040 (230 (1)); the FE value is slightly better because the stress is not exactly proportional to pressure (thermal and manifold part).

(f) TC-01 is on the thrust path, so add it to FA1T: +0.211 / +0.305 regular (all-node -0.021 / +0.056 at the J-FWD RBE3 patch). FA1S bounds it.

(g) State why FA1T is "-" on the other pressure parts: 90 bar shell, and FA1S bounds them.

**Owner:** FEA3D.

### RM2-09 (NOTE) - F4 precisions (reproduced within 0.0005; section 9)

- J-FD01 is negative at the hot soak from preload alone: -0.131 (F_max 2083 N, k_T 0.799 at 121 degC).
- At RT: bounding -0.259, Phi 0.2 -0.006.
- Torque window at Phi 0.2 (separation and bolt yield): 0.621-0.775 N m; empty if slip counts.
- A4-80 at 1.0 N m: -0.21 bounding / +0.059 Phi 0.2.
- J-FD09 at the specified hose EI 0.184 N m²: bounding -0.011, not only at the EI 0.5 sensitivity.

So the fix is sized on preload, meaning torque method and scatter, not only on the external loads. Carry these in tables/f4_secondary.md and in 13 #2-3.

### RM2-10 (NOTE) - 7075-T6 allowables are temperature-independent (RT 470 / 540 MPa)

Disclosed by FEA3D (13 #10). The lever-root hot bounds use RT values at the 60 degC bay [ASSUMED]. No classification changes, since these are already negative. The 188 (5) temperature table is still owed by Mechanical.

### RM2-11 (NOTE) - mounting-data header and per-hole envelope

State in 8.1:
- **Included mass.** The forces include the 4.103 kg model mass (engine 2.886, ring 0.217, fixed 0.971, horns 0.029 kg) and exclude 1.31 kg of airframe-wall equipment.
- **Sub-cases.** FA1Q / FA1S are pressure only. The LC2F envelope (908 N) is its thrust-only sub-case: GZ 0 bounds, since inertia opposes thrust.
- **Rigid against compliant airframe.** The rigid airframe bounds the maximum hole load (LC3 889 against 453 N) but not every hole:
  - LC3, compliant (stop045 only) above the rigid 8-pose envelope at 5 of 16 holes: AF_GM09_1 102 vs 20 N, AF_GM09_2 72 vs 9, AF_GM09_5 36 vs 9, AF_GM09_6 140 vs 27, AF_GM10_7 162 vs 124 N.
  - LC1, compliant above rigid at the GM-10 holes: 45-48 vs 36-37 N, and at AF_GM09_1 5 vs 3 N.
  - The per-hole datasheet rows should be the envelope of both, with the compliant LC3 pose coverage stated [SIM, published tables].

### RM2-12 (NOTE) - reproduction details

- My rebuilt regular set has 121,788 nodes against FEA3D's 121,741 (+47, 0.04 %), with the same governing nodes and identical margins.
- At J-FWD, the tensor-projection magnitude sum of the slow shares reaches 0.105 at one neighbour, against the REPORT's "<= 0.104" (principal). No effect.

### RM2-13 (MINOR) - the thermal map inherits the S-AX 0.10 mm closure at two designed clearances that the TC-03 and TC-02 values depend on

**Question** (lead, 2026-10-20).
- Mechanical's closure sweep finds that the 0.10 mm thermal-mesh rule (ax_thermal.py cd00f37a02ddbfd2, TOL_MM line 66) joins 16 designed clearances in v3.5.1. The sweep files are in Mechanical's folder, not in the hub; they are quoted from the lead (SIM / CALC, not reviewed by me).
- Two governing results depend on them: the TC-03 flange corner and the TC-02 maximum next to the f7/H8 fit.
- The lead asks:
  - whether FEA3D's 3D model ties or merges these interfaces too;
  - how the two values classify;
  - for a finding or a refutation.

**Answer.**
- Thermal map: yes, merged at both interfaces.
- Structure: partly tied at the TC-03 flange OD; not tied at the f7/H8 fit.
- I agree that both values depend on the closure, with two refinements, (d) and (e).

**Evidence** [SIM: own code `rm2_closure.py` on the stored lc1v351_c71 decks and fields, `results/rm2_closure_lc1v351_c71.json`. CAD from hub `03-cad/src/parts_engine.py` 6150bddad816b403. FEA3D source `asm_build.py` a98509e27cc1dc99.]

**(a) Geometry** [CAD].
- **TC-03 flange.** Ø20.0 x 2 (z 105.51-107.51, line 240) in the TC-02 counterbore Ø20.2 (line 168).
  - The designed radial gap is 0.10 mm, with no fit given, so the TOL_MM 0.10 rule closes it in the S-AX mesh.
  - From the mapped temperatures and the engmat CTE (GlidCop / 6061), the gap is 0.103-0.109 mm at the four states [DERIVED]. Thermal growth does not close it in operation.
- **The fit.** TC-01 bore 57.25 H8 (+0.046/0) on the TC-02 plug 57.20 f7 (-0.030/-0.060).
  - The radial gap is 0.025 mm in the CAD (basic sizes) and 0.040-0.078 mm toleranced. It is closed too.

**(b) Thermal map: merged at both interfaces.** FEA3D interpolates S-AX's per-part fields, so it inherits the closure by construction.

| Interface | Mapped temperature difference | Basis |
|---|---|---|
| TC-03 flange OD to TC-02 counterbore wall | \|ΔT\| <= 3.3 K at B1_1, B1_2, B1_19 and B1_21.65 | 320 nearest-node pairs, 0.10-1.48 mm apart |
| TC-02 plug to TC-01 bore | \|ΔT\| <= 3.9 K at all four states | 648 node pairs within 1 mm |

A real 0.1 mm gas gap passing 270 W over the 126 mm² flange OD would need several thousand kelvin. With k about 0.03 W/m/K it gives about 7000 K, consistent with Mechanical's 6600 K [DERIVED].

**(c) Structural model.**

*TC-03 flange OD: partly tied.*
- The production variant ('design' ties, TB1 'faces', asm_build.py line 567) uses TC03_TC02_seat: rule 'zt' (axial + tangential, radial free) at tolerance 0.12 mm. The tolerance is larger than the 0.10 mm gap.
- Its 300 dependent nodes (600 equations) are:

  | Location | Nodes | Note |
  |---|---|---|
  | Shoulder, z 107.51 | 183 | the real seat |
  | Flange OD, r 9.95-10.00 | 46 of 320 OD nodes | across the 0.10 mm design gap |
  | End face, z 117.51 | 71 | FEA3D's own source comment says this face opens in operation (lines 554-556) |

- The OD tie is patchy because the L1 TC-02 counterbore has 11 facets. Their chord radius is 9.691 mm against the 10.0 mm flange, so the facets cut 0.31 mm into it.
- FEA3D's pressure model treats the same gap as open and wetted: the 6.31 mm² ring at Pc (lines 900-908).
- The 3D model is therefore inconsistent at this joint: open for pressure, closed for heat, partly closed (in z) for structure.

*TC-01 / TC-02 f7/H8 fit: not tied, and no contact.*
- No equation has both TC-01 and TC-02 nodes. The head is held only by the 8 J-FWD RBE3 bushings (REPORT 2.2).
- With the mapped temperatures the fit stays open. Closing it would need a plug-to-bore ΔT of 37 K (0.025 mm CAD gap), 59 K (0.040 mm) or 116 K (0.078 mm), at α 23.6e-6 /K [DERIVED]. The mapped difference is at most 3.9 K.

**(d) TC-03 corner: the temperature field drives the value, not the structural tie.**
- Node n44861 is at r 9.80, z 105.51, 74.4 °C at B1_1.
  - It is 2.18 mm from the nearest tied node and 2.79 mm from the nearest tied OD node, so it is a regular node.
- Thermal-step stress at the node:

  | Component | MPa |
  |---|---|
  | Hoop | 253.1 |
  | Axial | 49.2 |
  | Radial | -7.0 |
  | Change in hoop from the OP increment | -0.9 |
  | Change in hoop from the PM increment | +0.6 |

  - This is the hoop tension of a cool flange rim. At B1_1 the rim OD is at 68.6-73.3 °C and the nose at 157.8 °C.
- Same-mesh comparison of FEA3D's two TB1 tie variants (both fea3d-asm v1.1, ball r 3 mm, h 0.3 mm):

  | Variant | MS y / u | vM (MPa) |
  |---|---|---|
  | Thread-only (OD and end face free; `f1_post_tc03_thread.json` 6486568413df1073) | -0.259 / -0.327 | 224.1 |
  | 'faces' on the same R2 mesh (conv_r2) | -0.266 | 225.9 |

  - Removing the ties changes the value by +0.007.
  - REPORT 4.2 compares the thread-only value with the L1 value -0.312 instead. That comparison overstates the effect of the ties.
- The rim keeps its shoulder seat on TC-02 (r 7.0-10.0) whether or not the OD gap is open. Opening the gap should therefore reduce the cool-rim stress, not remove it.
- Mechanical's "probably an artefact" is plausible in direction but not shown. Once the 270 W must pass the shoulder, the governing TC-03 location may move to the shoulder or the thread root.

**(e) TC-02: the governing node sits at the TB1 seat, not at the fit.**
- FEA3D's mapped TC-02 maximum at B1_19 is 159.16 °C at n25892 (r 6.50, z 107.51), the TC-03 shoulder corner.
  - It is 3.6 mm from the closed OD gap and about 22 mm from the fit.
  - The governing node n26334 (r 5.86) takes the same value through the nearest-node fallback.
- Only at B1_21.65 does the TC-02 maximum sit near the fit: 155.0 °C on the forward face at r 24.95, 3.65 mm from the plug OD.
- At the seat the two closures act in opposite directions:
  - the f7/H8 closure makes TC-02 too cool;
  - the OD-gap closure moves heat into TC-02 at r 10.1. With the gap open, that heat must pass the shoulder next to the seat node instead.
- So Mechanical's +10-30 K for the f7/H8 path (CALC, TO-VERIFY) does not bound the governing seat node. Only the joint variant does.
- If the S-AX TC-02 maximum of 160.3 °C next to the fit occurs at an instant other than FEA3D's four mapped states, the 3D model has not assessed it. The same gap applies to the LC2 thermal state (section 5).
- Sensitivity, with the stress held at its 159 °C value and engmat 6061-T6 allowables [DERIVED]:

  | TC-02 temperature | MS y / u (total stress) | Primary-only MS |
  |---|---|---|
  | 159.2 °C (as mapped) | +0.095 / -0.120 | +3.44 |
  | +10 K | -0.019 / -0.196 | +2.98 |
  | +20 K | -0.133 / -0.273 | +2.51 |
  | +30 K | -0.247 / -0.350 | +2.05 |

  - Each +10 K costs about 0.11 on yield and 0.08 on ultimate.
  - The T-F1 requirement (>= 0.788 Ftu,RT) then applies at the higher temperature.

**(f) Other governing nodes checked.**
- No closed clearance is near:
  - the NZ-01 regular node n74445 (throat, 15.5 mm from the NZ-01 OD);
  - the NZ-03 nodes (3.9-9.7 mm from the NZ-03 OD).
- The NZ-01 all-node -0.522 at n72033 is 0.5 mm from the NZ-01 OD. It sits next to the NZ-02 sleeve, whose CAD gaps of 0.01 / 0.025 mm (parts_engine.py line 496) are closed too.
- Not every join is an artefact. The CAD defines TC10_NOSE_GAP 0.05 mm (TC-10 bore to the TC-03 nose) as an RTV-filled bond line, closed on purpose (line 51).

**Classification (for the lead).**

| Item | Class | Basis |
|---|---|---|
| TC-03 corner (LC1 -0.312 / -0.375; LC2 -0.314 / -0.376) | **Thermal-secondary (TS-183), with a model-fidelity question on its value; not a primary design issue** | Primary-only +7.3 (LC1) / +5.39 (LC2); P+Q +1.06-1.22 (FEA3D). 98 % thermal (vM 237 of 241 MPa), on a field with a closed design gap. Reported as found until the variant is re-posted. |
| TC-02 temperature (159.2 °C mapped; S-AX 160.3 °C) | **Model-fidelity question with a direct design consequence; the stress class stays TS-212** | Primary-only stays positive at +30 K. The temperature is the input to check (d) (150 °C limit, already exceeded and open under 212) and to the T-F1 allowable. If T-F1 cannot be sourced at the corrected temperature, the head becomes a design-change item. |

**Correction.**
1. REPORT 2.2, 4.1 and 4.2 state that the mapped temperatures inherit the S-AX 0.10 mm closure at designed clearances.
   - Name the TC-03 flange OD (0.10 mm radial) and the 57.25 H8 / 57.20 f7 fit.
   - State that the TC-03 corner and TC-02 seat values depend on them.
2. REPORT 2.2:
   - The thread-variant row reads: "shoulder and M14 engagement tied ('zt'); flange OD and end face free". At present it says "shoulder + end face free", but model.json ties the shoulder (TC03_TC02_shoulder, 568 nodes).
   - The 'faces' row adds that the 0.12 mm tolerance ties 46 flange-OD nodes across the 0.10 mm design gap, and ties the z 117.51 end face.
3. REPORT 4.2 quotes the thread-only value against the same-mesh R2 'faces' value (-0.259 against -0.266), not against L1.
4. The v3.5.2 re-check uses the 'thread' TB1 tie, or removes r > 9.9 and z 117.51 from TC03_TC02_seat. Either is consistent with the open, wetted gap of the pressure model.
5. On the lead-approved gap-conductance variant, FEA3D re-maps and re-posts every mapped part:
   - TC-03 as a whole part, including the shoulder and the thread root;
   - the TC-02 seat and forward face;
   - NZ-01, including n72033;
   - at the four states plus the instant of the S-AX TC-02 maximum.

   It also reports the plug-to-bore ΔT at the fit. It adds a fit contact if that ΔT exceeds about 37 K (CAD gap) to 59 K (minimum toleranced gap).
6. The TC-02 T-F1 check (212 (1)) is evaluated at the variant temperature.

**Owner:** FEA3D (1-6); Mechanical (variant); lead (record).

## 5. RM2-02 recommendation and basis (the factor question of 231 (4))

**Recommendation: there is no conflict to rule.** The interim's "LC2F at both factor sets" came from my own mislabel: I evaluated the pressure-part MEOP case as "LC2F", at OP 4.473 MPa = 907.7 N / 202.92 N/MPa.

**1. LC2 (pressure parts at MEOP): SF 1.5 / 2.0 at part temperature.** Three sources agree:
- **ENG-09** (REQUIREMENTS line 60): "Pressure parts: SF >= 1.5 on yield and >= 2.0 on ultimate, at MEOP and at temperature. Chamber MEOP **45 bar** (stuck-pintle case, 30 C tank), proof 67.5 bar".
- **loadcases_v1 LC2** ("Chamber MEOP + thermal state at the critical time"): chamber 4.5 MPa, manifold 7.0 MPa, SF_y 1.5 / SF_u 2.0, focus "forward closure (head) + 8 x M5 radial screws, aft closure M63x1.5 thread + retaining lip, graphite insert, liner / insulators, case tube".
- **Line 188 (9)**: "Nominal operating states (LC1-LC4, LC6, TS1, TS2, SEGP, TB70) use ENG-10 1.5/2.0". LC2 is in that list.

**2. LC2F (failure thrust on the structure): SF 1.0 / 1.5.**
- loadcases_v1 LC2F, "Pintle full-stroke failure thrust (structure)": 907.7 N, SF_y 1.0 / SF_u 1.5, "Mechanical choice, lead to confirm".
- Confirmed by 188 (9): "abnormal or failure states (LC2F, BN, TBS, FA-1) use SF_y 1.0 / SF_u 1.5".
- FEA3D's F2 LC2F column (gimbal and mount parts) is therefore correct as published.

**3. Why the pressure parts do not take the failure factors at MEOP.**
- ENG-09 placed the MEOP at the stuck-pintle pressure on purpose, raising it from 31 bar, and kept the pressure-vessel factors on it.
- The proof pressure of 67.5 bar is 1.5 x MEOP and must stay below yield. So SF 1.5 on yield at MEOP is already implied at RT by the proof requirement.
- Using 1.0 / 1.5 at MEOP would remove the margin that ENG-09 requires.

**4. Restatements.**
- 231 (4) reads "LC2 rows (MEOP 45 bar, SF 1.5 / 2.0)".
- Its "TC-02 and NZ-03 at both factor sets" becomes "at 1.5 / 2.0".
- My interim column at 1.0 / 1.5 and at OP 4.473 is withdrawn (results/rm2_repost_lc2f_lc1v351_c71.json is INTERIM, superseded).

**5. LC2 values** [SIM re-post]. Inputs: OP 4.5 MPa + PM 7.0 MPa, flight inertia 0.61 g x 8 directions x GZ {0, 4.04 g} added as a small bound, the four mapped S-AX states, SF 1.5 / 2.0.

| Part | Regular y / u (state, node, T) | All-node y / u (class, mm) |
|---|---|---|
| TC-01 | +0.488 / +0.196 (B1_21.65, n8314, 79 C; J-FWD) | +0.205 / **-0.031** (rbe3 0.914, n580) |
| TC-02 | +0.078 / **-0.134** (B1_19, n26334, 159.2 C; tie end 1.144) | +0.047 / -0.159 (tie edge 0.0) |
| TC-03 | **-0.314 / -0.376** (B1_1, n44861; primary +5.39) | same |
| TC-04 | +1.010 / +0.634 | +0.481 / +0.202 (tie edge) |
| TC-09 | +1.151 / +0.866 | +1.008 / +0.746 (tie edge) |
| NZ-01 | **-0.459** (B1_1, n74445, 1330 C) | -0.490 (re-entrant 0.0) |
| NZ-02 | +0.775 | +0.644 |
| NZ-03 | **-0.089** (B1_21.65, n79829, 1277 C; char primary, 20 MPa ASSUMED) | **-0.484** (tie edge, n79267, B1_19) |
| NZ-04 | +3.625 | +2.836 |
| FD-01 | +2.303 / +5.488 | +0.530 / +1.957 (tie edge) |
| PD-01R / PD-01S | +2.607 / +1.923 ; +1.993 / +1.425 | +1.231 / +0.808 ; +1.084 / +0.689 |
| GM-01 / GM-02 / GM-03 | +6.589 / +5.540 ; +8.895 / +7.526 ; +5.330 / +4.107 | all positive |
| J-FWD screw (hand, section 4 RM2-01 (b)) | shear-only +1.01 / +1.10 RT; combined with preload +0.22 / +0.07 / **-0.08** | - |

**What the LC2 values require** [DERIVED]:
- **NZ-03:** regular needs Sc >= 21.96 MPa, inside N-F1's >= 23.7 MPa acceptance (212 (2)). The tie edge would need 38.6-38.8 MPa (RM2-04).
- **TC-02:** needs Ftu(159.2 C) >= 208.1 MPa = 0.800 Ftu,RT (Ftu used 180.24 MPa); LC1 needs 0.788. This is above the 212 (1) T-F1 thresholds (0.765 at 149 C, 0.661 at 181 C) from S-AX, so T-F1's acceptance must add the 3D value. Because the tie-end value refines to +0.165 u at R3, T-F2 (contact FE) remains the real closure. The 159.2 C itself rests on the closed f7/H8 fit and TC-03 OD gap, so the threshold applies at the gap-conductance variant's temperature (RM2-13).
- **Thermal states:** LC2 asks for the "LC5 critical instant". The 3D model maps only the four S-AX LC1 states (hottest TC-02 at B1_19). If the LC5 instant is hotter for any part, FEA3D adds it.

## 6. Exclusion audit: all-node minima hidden by the regular set [SIM re-post]

| Case | Part | All-node MS (node, class, distance mm, T) | Regular MS | Routing |
|---|---|---|---|---|
| FA1S | TC-01 | -0.370 / -0.320 (n580, rbe3 0.914, hole edge) | -0.221 / -0.160 | 231 (3) |
| FA1S | TC-01, re-entrant class minimum | -0.316 | - | 231 (3) |
| FA1S | TC-02 tapped-hole mouth | **-0.158 / -0.092** (n25946, re-entrant flag; 0.718 from JF0_head RBE3; 45 C) | +0.855 / +1.001 | 231 (2) / (3) |
| FA1S | TC-02, rbe3 class minimum | -0.006 | - | 231 (3) |
| FA1S | NZ-03 tie edge | **-0.126** (n79267, tie edge 0.0, 677.6 C) | +0.630 | 188 (3) + N-F1 |
| FA1S | GM-01 boss corner (r 37.0, 168 deg, z -6.7) | +0.277 / +0.468 (n86443, re-entrant 0.206) | +2.436 / +2.948 | positive; refine if loads rise |
| LC1 | NZ-01 | **-0.522** (n72033, re-entrant 0.5, B1_19, 1309 C) | -0.435 (B1_1) | report as found |
| LC1 | NZ-03 tie edge | **-0.071** (n79267, B1_19, 1419 C) | +0.476 | 188 (3) + N-F1 |
| LC1 | TC-02 tie edge | -0.141 u (n25892) | -0.119 u | T-F2 |
| LC1 | TC-03, re-entrant class minimum | -0.284 | -0.312 / -0.375 | regular governs |
| LC2 | TC-01 / TC-02 / NZ-03 / NZ-01 | -0.031 u / -0.159 u / -0.484 / -0.490 | +0.196 u / -0.134 u / -0.089 / -0.459 | section 5 |
| FA1T | TC-01 | -0.021 / +0.056 (n9447, rbe3 0.0) | +0.211 / +0.305 | 231 (3) |
| LC3 / GS | GM-16a/b horns | +0.45 to +0.57 (re-entrant 0.43-0.54) | +1.1 to +1.36 | positive |

## 7. View on (e): TC-01 FA-1 modal shares, OI-51, and band columns

1. **The decomposition reproduces** [SIM / DERIVED]. Inputs: FEA3D's stored 60 mass-normalised eigenvectors and my own integration of the deck's unit-pressure load. My stress probe matches ccx (14.822 against 14.823 MPa/MPa). The numbers equal FEA3D 9A.1 to 4 decimals:

   | Node | Scale | Slow T > 1 ms | Sum of magnitudes | 0.1-1 ms | Residual |
   |---|---|---|---|---|---|
   | 2785 (J-FWD) | 1.00 | +0.0178 | 0.0956 | +0.6002 | +0.3820 |
   | 2785 (J-FWD) | 0.90 and 0.85 | +0.0262 | 0.1040 | +0.5918 | +0.3820 |
   | 2800 (LC1 node) | 1.00 | +0.0349 | 0.0474 | +0.5238 | +0.4412 |
   | 2800 (LC1 node) | 0.90 and 0.85 | +0.0465 | 0.0672 | +0.5123 | +0.4412 |

   - At 2785 the dominant modes are 22 (2134 Hz, +0.307) and 23 (2157 Hz, +0.210).
   - Over FEA3D's six neighbours the maximum is 0.035 signed and 0.104 for the sum of magnitudes (tensor projection 0.105).
2. **Full share vectors.** The full 60-mode signed vectors at these two nodes are in `results/rm2_modal_shares.json` (`shares_all_60`): principal and tensor projections at scales 1.00 / 0.90 / 0.85. They are an independent cross-check of what OI-51 asks FEA3D to publish at every assessed node. They do not replace FEA3D's deliverable.
3. **What the decomposition supports:** the slow (T > 1 ms) share at J-FWD is small, at most 0.035 signed and 0.105 by magnitude over the 0.85-1.00 scaling. **What it does not support:**
   - a precise split between 0.1-1 ms and under 0.1 ms, because 38 % of the static stress is in the residual above 5130 Hz;
   - a band reading for the production model, because the modal deck is all-L2 with a different unit-pressure load (RM2-06) and a J-FWD static stress 15 % lower than the L1 model;
   - damping effects, which are not in the decomposition (OI-52).
4. **Reading for 223 (3)(b).** I confirm the arithmetic and the small slow share. I do not confirm the band reading as a design basis. This agrees with 230 (1), which withdrew the period reading, and with 231, which sizes on FA1S. I recommend that J-FWD stays sized on FA1S whatever OI-51 returns.
5. **No other part relies on a band column in the regular set.** Every other part is positive on FA1S: the lowest are TC-02 +0.855, NZ-03 +0.630, GM-03 +1.887, TC-09 +1.637 and NZ-01 +1.465. Two all-node locations would pass only on a band column:
   - the TC-02 tapped-hole mouth: -0.158 at FA1S, +0.051 at the restated 121 bar;
   - the NZ-03 tie edge: -0.126 at FA1S, +0.091 at 121 bar.

   Neither has its own period: 9A lists the TC-02 head governing nodes, not the mouth, and does not list NZ-03. They close through 231 (2) / (3) and through 188 (3) with N-F1, not through a band column.

## 8. Views on (f) and (f2)

### (f) Modal

**Confirmed** [SIM / DERIVED]:

| Item | Value |
|---|---|
| Rocking, all-L2, rigid servo | 51.42 / 59.42 Hz |
| Scaled to the production K | 47.82 / 55.51 Hz (sqrt(5370/6209), sqrt(7284/8347)) |
| With K_s 58 / 174 at neutral, beta | 21.35 / 31.27 Hz |
| With K_s 58 / 174 at neutral, alpha | 21.86 / 33.07 Hz |
| Axial | 408.3 Hz (T = 2.449 ms) |
| Pintle linkage | 186 Hz (upper bound, rigid linkage) |

- The servo-in-series values use eigenfrequency scaling. A lumped Rayleigh form with I 0.0585 kg m² gives +0.8 %.
- The coarsening bias (K +15 / +16 %, about 7 % in f) is stated and accepted.
- The 0.85-0.90 scaling of the shares covers this bias plus hot E.
- J lowers the rocking pair by the factor 0.70-0.88 (RM2-07).
- RM2-05 does not affect the neutral servo values.

### (f2) GNC rev4b findings

**1. post_k servo factor: confirmed independently (RM2-05).**
- My per-axis servo-stiffness ratios equal GNC's g_kin/g_fea: 1.085-1.339 on the cone and 1.103-1.586 at the stops.
- FEA3D's off-centre with-servo stiffnesses are low by up to 31 % (ratio 1.45), so a window built on them overstates its top: 130 against 120 N m/rad in GNC's B04.
- GNC's rev4b re-run used its own CAD kinematics and is not affected.
- 227 (3)'s 126 / 129 used the neutral K and is not affected either.

**2. "+11 % / +24 % versus V5c": confirmed arithmetically.**
- Neutral K_FE 7284 / 5370 against V5c centre mech_T 6539.3 / 4325.1 N m/rad gives +11.4 % / +24.2 %.
- Both models have the airframe rigid. V5c has the engine case rigid (CAD v3.3); FEA3D has the engine flexible (CAD v3.5.1). The FE is therefore stiffer despite its softer engine.
- Series split, DERIVED from the published numbers:

  | Component | FE | V5c | Difference |
  |---|---|---|---|
  | Chain (both axes) | 32.6 kN m/rad | 29.1 kN m/rad | +12 % |
  | Structure, alpha / beta | 9380 / 6429 N m/rad | rigid-chain 8433 / 5080 N m/rad | +11 % / +27 % |

- Against V5c's own chain spread (chain-low 6253 / 4198 to chain-high 7527 / 4736), the FE alpha lies inside; beta is 13 % above the chain-high value.
- The models therefore differ on the beta (inner-axis) structure path: needle cups, collar and ring, with pins and seats modelled as *RIGID BODY in the FE. Neither author has identified the cause.

**View.**
- GNC's conclusion stands as a statement of plant dependence: the FE plant gives a lower window top.
- The cause of the beta difference should be identified before the FE plant is preferred over V5c, or the B-TVC-1 measured rocking mode decides it, per 227 (3).
- The ASSUMED compliant airframe lowers the FE K by 14 / 13 % at stop045, and GNC's compliant variant covers that.

## 9. (g) F4 joints and mounting data

### F4 joints

**J-FD01** [DERIVED; ASSUMED preload model K 0.2, ±25 %; k_T proxy]:
- Reproduced within 0.0005 of FEA3D on the published per-case loads.
- Bounding -0.407 and Phi 0.2 -0.205, both in the 10 g hard-landing envelope with the R7 area.
- Preload alone at the hot soak: -0.131.
- At RT: bounding -0.259, Phi 0.2 -0.006.
- Torque window at Phi 0.2 (separation and bolt yield): 0.621-0.775 N m; FEA3D gives 0.62-0.77. The window is empty if slip counts.
- A4-80 at 1.0 N m: -0.21 bounding / +0.059 Phi 0.2.
- FEA3D's "about 0.7 N m with controlled scatter, A4-80 or M4" is consistent with this.

**J-FD09:**
- Reproduced within 0.0004: -0.167 bounding at EI 0.5, +0.054 at Phi 0.2.
- At the specified EI 0.184 it is still -0.011 bounding.

The other joints were not re-derived.

### Mounting data

Equilibrium of the published ring totals [DERIVED]:
- Expected axial forces: FA1Q 1826.3, FA1S 3064.9, FA1T 3600.0, LC1 344.9 (= 202.925 x 2.501 - 4.103 x 4.04 x 9.81), LC6 402.5 and LC2F 907.7 N.
- Expected lateral forces: LC1 24.6 and LC6 120.8 N.
- These match the published 1826 / 3065 / 3600 / 345 / 402 / 908 and 25 / 120 N.
- The model mass is 4.103 kg (RM2-11).

**TC-01 checks** [DERIVED]:
- FA1S section force at z -60: FE 35,594 N against (A_bore - OP_NET) x 15.1038 = 35,679 N (ratio 0.9976).
- LC1 membrane: hoop / axial / radial 22.51 / 9.82 / -1.25 MPa, vM 20.59 MPa, against FE 20.29-20.36.

**Not re-derived:** the per-hole distribution (rigid / compliant). The per-hole rigid-against-compliant observation is in RM2-11.

## 10. (h) Classification of every negative

FEA3D matrix: 17 negative cells, 27 values. Classes used in the table:
- **DC:** DESIGN CHANGE item.
- **TS-183:** thermal-secondary under 183 (1): primary and shakedown pass; LCF and temperature with Mechanical.
- **TS-212:** TC-02 under 212 (1): (a)-(c) pass; (d) open.
- **BR:** brittle and thermal, open design or criterion question (183 (2) capture / containment).
- **CH:** char primary against the ASSUMED 20 MPa.
- **MF:** model-fidelity question on the value; the class it carries stands, and the value is re-posted on the named variant (RM2-13).

| # | Part | Column | MS y / u | Class | Closure path |
|---|---|---|---|---|---|
| 1 | TC-01 | FA1S | -0.221 / -0.160 | DC (J-FWD) | 230 (1), 231 + RM2-01 addenda |
| 2 | TC-02 | LC1 | +0.096 / -0.119 | TS-212; tie-end dependent (R3 +0.165 u); MF: temperature from the closed f7/H8 fit and TC-03 OD gap (RM2-13) | T-F1 (>= 0.788 at 159 C on this value, at the variant temperature) / T-F2; gap-conductance re-map |
| 3 | TC-02 | LC3 hot bound | +0.022 / -0.179 | TS-212 (DERIVED bound); MF | as 2 |
| 4 | TC-02 | F2 hot bound | +0.025 / -0.176 | TS-212 (bound); MF | as 2 |
| 5 | TC-03 | LC1 | -0.312 / -0.375 | TS-183 (primary +7.3; P+Q +1.06 to +1.22); MF: cool-rim hoop stress on a field with the 0.10 mm flange-OD gap closed (RM2-13) | LCF (Mechanical); S-AX shakedown criterion identity (13 #7); gap-conductance re-map of the whole of TC-03 |
| 6 | TC-03 | LC3 hot bound | -0.357 / -0.415 | TS-183 (bound); MF | as 5 |
| 7 | TC-03 | F2 hot bound | -0.352 / -0.410 | TS-183 (bound); MF | as 5 |
| 8 | NZ-01 | LC1 | -0.435 (all-node -0.522) | BR; worsens with refinement (R3 -0.481) | 183 (2) capture shown + test basis, else design change |
| 9 | NZ-01 | LC3 hot bound | -0.443 | BR | as 8 |
| 10 | NZ-01 | F2 hot bound | -0.445 | BR | as 8 |
| 11 | GM-01 | LC3 R3 | -0.273 / -0.374 | DC (lever root) | 223 (5); re-check at R3 on the changed CAD |
| 12 | GM-01 | GS | -0.209 / -0.319 | DC | 223 (5) |
| 13 | GM-01 | F2 hot bound | -0.219 / -0.327 | DC (bound) | 223 (5) |
| 14 | GM-02 | LC3 hot bound (L1) | +0.128 / -0.028 | superseded: the L1 convention is unconservative (4.6) | R3 hot bound -0.30 / -0.40 (RM2-08) |
| 15 | GM-02 | LC3 R3 | -0.280 / -0.379 | DC (lever root) | 223 (5) |
| 16 | GM-02 | GS | -0.223 / -0.330 | DC | 223 (5) |
| 17 | GM-02 | F2 hot bound | -0.259 / -0.362 | DC (bound) | 223 (5) |

**New with LC2** (reviewer re-post, section 5):

| Part | MS | Class | Closure path |
|---|---|---|---|
| TC-02 | +0.078 / -0.134 | TS-212; MF (RM2-13) | T-F1 needs Ftu(159 C) >= 0.800 Ftu,RT, at the variant temperature; T-F2 |
| NZ-03 | -0.089 | CH | N-F1 (>= 21.96 MPa, inside the 23.7 MPa acceptance) |
| TC-03 | -0.314 / -0.376 | TS-183; MF (RM2-13) | primary +5.39; gap-conductance re-map |
| NZ-01 | -0.459 | BR | as row 8 |

**Outside the matrix:**

| Item | Values | Class | Closure path |
|---|---|---|---|
| J-FWD screws | FA1S shear yield -0.10 RT / -0.15 hot; combined with preload -0.22 to -0.31; LC2 combined -0.08 at +25 % hot | DC | 231 |
| J-FD01 | -0.41 / -0.20 | DC | 223 (5) |
| J-FD09 | -0.17 / +0.05; -0.011 at the specified EI | Mechanical | 13 #3 |

**Hidden all-node** (RM2-04, section 6):

| Location | Value | Closure path |
|---|---|---|
| TC-01 J-FWD | FA1S -0.370, LC2 -0.031 u, FA1T -0.021 | 231 (3) |
| TC-02 mouth | FA1S -0.158 | 231 (2) / (3) |
| NZ-03 tie edge | LC1 -0.071, FA1S -0.126, LC2 -0.484 | 188 (3) contact FE + N-F1 with the tie-edge requirement |
| NZ-01 | LC1 -0.522 | as row 8 |
| TC-02 tie edge | LC2 -0.159 u | T-F2 |

None is closed by this review.

## 11. Confirmed numbers (reproduced) [SIM re-post / DERIVED]

| Quantity | FEA3D | Reviewer |
|---|---|---|
| FA1S TC-01 J-FWD | -0.221 / -0.160, n8314, 302.95 MPa | identical |
| FA1Q / FA1D / FA1U TC-01 | +0.291 / +0.393; +0.251 / +0.349; +0.144 / +0.233 | identical |
| FA1T GM-03 (min gimbal) | +1.483 / +1.671 | identical (n129757, 94.19 MPa) |
| LC1 NZ-01 / TC-03 / TC-02 | -0.435 / -0.312 / -0.375 / +0.096 / -0.119 | identical, same nodes |
| LC3 stop045 GM-02 R3 | -0.280 / -0.379, 435.1 MPa, n66500 | identical; fb_run 322.6-417.4 N; rods 609.0 N; moment <= 34.77 N m; residual 2.83 % |
| GS alpha- GM-02 | -0.223 / -0.330, 403 MPa | identical (403.15 MPa, n74502) |
| Regular set | 121,741 | 121,788 (RM2-12) |
| Deck vs stored temperatures | - | <= 0.5 mK (T_deck vs T.npz) |
| Engine free body FA1S / FA1Q | 100 % | 3065.0 / 3064.9 N; 1826.2 / 1826.3 N |
| Mount totals | 1826 / 3065 / 3600 / 345 / 402 / 908 N | 1826.3 / 3064.9 / 3600.0 / 344.9 / 402.5 / 907.7 N |
| J-FWD screw shear | 4.85 kN | 4853 mean / 4879 max (FE), 4843 (p A / 8) |
| TC-01 membrane LC1 | 20.29-20.36 MPa (hand 20.59) | 20.59 MPa |
| Modal shares J-FWD / LC1 node | 9A.1 table | identical to 4 decimals |
| Rocking modes / axial | 51.4 / 59.4; 47.8 / 55.5; 21.3-33.1 Hz; 408.3 Hz | 51.42 / 59.42; 47.82 / 55.51; 21.35 / 31.27, 21.86 / 33.07 Hz; 2.449 ms |
| Neutral K, centre vs V5c | 7284 / 5370; +11 % / +24 % (GNC) | +11.4 % / +24.2 % |
| F4 J-FD01 / J-FD09 | -0.41 / -0.20; -0.17 / +0.05 | within 0.0005 / 0.0004 |
| Convergence TC-01 | 303.0 / 302.6 / 295.9 MPa | same numbers; not asymptotic (RM2-03) |
| Re-solve fa1_c71 TH + OP (reviewer ccx, section 2) | stored fields.npz, f1.dat | S relative norm difference 2.6e-8; U 3.5e-13 / 2.4e-10; FA1S vM at n8314 302.950 MPa (difference 4e-6); 32 hole totals, max \|dF\| 0.0 N; OP sum Fz -202.9248 N |
| TB1 thread-only vs 'faces', TC-03 corner, same R2 mesh | -0.259 / -0.327 (224.1 MPa) "over-constraint refuted" | confirmed against R2 'faces' -0.266 (225.9 MPa): +0.007 (RM2-13) |
| Mapped T across TC-03 OD gap / f7/H8 fit | - | \|ΔT\| <= 3.3 K / <= 3.9 K at all four states: closures inherited (RM2-13) |

## 12. Limits of this review (not demonstrated)

1. **One re-solve only** (section 2): the TH and OP steps of fa1_c71/A1_22.2. It reproduces the stored fields, but it is the same deck on the same solver, so it confirms repeatability, not the idealisations. The other steps (PM, g steps), the other runs and the modal run are not re-solved.
2. **Re-posting coverage.**
   - Re-posted: LC1, FA-1 (all columns and the 230 (2) values), FA1T, LC2, LC3 stop045 (R3 lever root) and GS alpha-.
   - Not re-posted: the other 7 stop poses, the other 8 GS poses, TD, LC6, LC2F, the hot bounds, the compliant airframe and the TB1 thread variant.
3. **Rigid-servo K_FE** is not re-derived from the unit rod steps; only the servo factor is.
4. **Modal:** the eigen solution is not re-run. Only post-processing of the stored mass-normalised vectors was done, with my own load integration and stress probe.
5. **Thermal mapping.** S-AX to 3D is audited only for:
   - the identity of the deck temperatures with the stored maps;
   - part-maximum spot checks: TC-02 159.2 C against S-AX 159.7 C (212 (1)); NZ-01 1330 C;
   - the closure check of RM2-13, at the TC-03 flange OD and the f7/H8 fit, plus the distance of the NZ-01 / NZ-03 governing nodes from their ODs.

   Not done:
   - Mechanical's sweep of the 16 joins is in Mechanical's folder, so I have not read or reviewed it. RM2-13 quotes it from the lead.
   - The S-AX thermal model itself is not reviewed.
6. **Lever-root peak stress** is not hand-derived. I accept the refinement evidence of 4.6 and 9B.
7. **Contact:** no contact FE. The bonded ties are the "bonded bound" of 188 (3).
8. **J-FWD hand checks** cover TC-01 and the screw only; TC-02 thread bearing and shear are not covered. The preload model (K 0.2, ±25 %) and k_T are ASSUMED, as in FEA3D F4.
9. **Mounting data:** per-hole values are not re-derived.
10. **Out of scope:** TB70, BN, TBS, TS1/2 and SEGP (outside the FEA3D scope); figures and charts not checked.

## 13. Files (reviewer outputs, sha256/16; full list with sha256 in `reviews/mechanical/r2/MANIFEST_REV-MECH-2.sha256`)

All files are under `reviews/mechanical/r2/`. The manifest uses paths relative to that folder and also lists this file (`../../REVIEW-MECHANICAL-R2.md`). The sha16 of this file and of the manifest are given in the hand-back; this file cannot carry its own hash. The re-solve .frd is kept gzipped in the reviewer scratchpad (sha16 40a5251b857a29c6 before gzip) and is not in the hub.

**scripts/**

| File | sha256/16 | Purpose |
|---|---|---|
| rm2_deck.py | 0502d17d83adcdf3 | deck parser |
| rm2_repost.py | d85eed64b0bf178e | unit-step re-post, regular set, exclusion audit |
| rm2_lc3.py | d7ccf924be6376ab | LC3 / GS rod forces and moment residual |
| rm2_modal.py | 9214d344d24f27c7 | modal shares, load integration, stress probe |
| rm2_servo_g.py | 0a08702199edb403 | servo kinematics r_eff |
| rm2_handcalc.py | 073ff0a394f9bae1 | hand checks (J-FWD, membrane, mounts, F4, LC2 requirements, J) |
| rm2_resolve_cmp.py | 11232fbc7f215df9 | re-solve against fields.npz |
| rm2_resolve_extra.py | becc3785da373cf9 | re-solve hole totals and error estimator |
| rm2_closure.py | a274ed0371fc7416 | RM2-13 closure check |
| rm2_verify_manifest.py | 5348c62d00a520b1 | author manifest check |
| rm2_cmp_op_stress.py | add7e58cc8260d79 | diagnostic (RM2-06) |
| rm2_dup_dload.py | 9e41746ae7b5079d | diagnostic (RM2-06) |
| rm2_jfwd_probe.py | e67e9cbd5ee8ed5d | diagnostic (RM2-01) |
| rm2_op_faces.py | 7dff433f99f1cb1c | diagnostic (RM2-06) |
| rm2_op_resultant.py | cada10d0c7c163bb | diagnostic (RM2-06) |
| rm2_reentrant_hist.py | 2984616917b1ffbf | diagnostic (RM2-04) |
| rm2_tc01_faces.py | 033751f5dde33ba0 | diagnostic (RM2-06) |

**results/**

| File | sha256/16 | Content |
|---|---|---|
| rm2_repost_fa1_c71.json | c9c2fe0dc7c3c4cd | FA1Q / D / U / S and the 230 (2) values |
| rm2_repost_fa1t_c71.json | 960e9ca65248309a | FA1T |
| rm2_repost_lc1v351_c71.json | 8119a0e36e5a7e6a | LC1 |
| rm2_repost_lc2_lc1v351_c71.json | 868a31f2b05acd4c | LC2 (MEOP 45 bar, 1.5 / 2.0), section 5 |
| rm2_repost_lc2f_lc1v351_c71.json | d429fb6a1e42bf53 | **INTERIM, superseded** (OP 4.473 MPa mislabelled LC2F; section 5) |
| rm2_lc3_stop045_gm02r3.json | c5ac745fced5cb33 | LC3 stop045 R3 |
| rm2_gs_alpha-.json | 3ae848153d73a74a | GS alpha- |
| rm2_modal_shares.json | b5e940839c808553 | modal shares (full 60-mode vectors) |
| rm2_servo_g.json | 814adb7631c986b2 | servo factor |
| rm2_handcalc.json | e31e8316b51d657b | hand checks |
| rm2_resolve_fa1_c71_TH_OP.json | e44ed0029157706b | re-solve comparison |
| rm2_resolve_extra.json | 85fb3c7132fe0ad9 | re-solve hole totals, error estimator |
| rm2_closure_lc1v351_c71.json | 416827cca1070154 | RM2-13 |
| rm2_manifest_check_assembly3d.json | 1276c3228a5b44a5 | author manifest check |
| rm2_manifest_check_s3d_v351.json | 368ecd461d1112d9 | author manifest check |

**logs/**

| File | sha256/16 |
|---|---|
| rm2_closure.log | feded168b5fad436 |
| rm2_cmp_op_stress.log | 858f03c9269b619f |
| rm2_dup_dload.log | 900c963dc11b3cea |
| rm2_gs_alpha-.log | e4a7c59181ee8562 |
| rm2_handcalc.log | fe29c1ae1415370b |
| rm2_jfwd_probe.log | 70b181a73702d9b1 |
| rm2_lc3_stop045_gm02r3.log | f353fc66bb3d275e |
| rm2_manifest_check_assembly3d.log | 7b18589837883b42 |
| rm2_manifest_check_s3d_v351.log | 710191f72ac3c5a5 |
| rm2_modal_shares.log | 193d590681d2882a |
| rm2_op_faces.log | 4038a17d15ce502f |
| rm2_op_resultant.log | 23dae1b8b6e8bd62 |
| rm2_reentrant_hist.log | f30044a74a589b15 |
| rm2_repost_fa1_c71.log | 124e43f898501088 |
| rm2_repost_fa1t_c71.log | bca04be5950c73d0 |
| rm2_repost_lc1v351_c71.log | c691ae5737a89a2c |
| rm2_repost_lc2_lc1v351_c71.log | 730734376e0899ff |
| rm2_repost_lc2f_lc1v351_c71.log | 306965afa97e4787 (INTERIM, superseded) |
| rm2_resolve_cmp.log | 4b05eabaac364a08 |
| rm2_resolve_extra.log | 21bdb6f6b461f323 |
| rm2_resolve_run.log | dd7e4eafbfb7730e |
| rm2_servo_g.log | e990c91ede312200 |
| rm2_tc01_faces.log | d7b9a0809f5414d1 |
