**Conventions**
- **Tags.**
  - SIM: solver output (a reviewer re-solve is still SIM).
  - DERIVED: reviewer arithmetic from tagged inputs.
  - ASSUMED, DATASHEET, TO-VERIFY, AS RECALLED as usual.
  - The author's material tags LITERATURE and LITERATURE-approx are quoted as given.
- **Units.** mm, N, MPa, °C.
- **Margin.** MS = allowable(T) / (SF · stress) − 1.
- Matching numbers prove repeatability, not physical acceptance. Nothing in this review is physical approval.

## 0. Checkpoint (docs/SUPERVISION-WORKFLOW.md)

**Delivered by / reviewed by / date**
- Delivered by Mechanical (CHANGELOG 176, 178, 179; that session has ended).
- Reviewed by REV-MECH-1, independent and read-only on all author areas.
- Date: 2026-10-13. The lead records the verdict; I did not edit SUPERVISION.json, CHANGELOG, interfaces or reports.

**Area and configuration**
- S-AX L1, configuration L1_TC09IN718_thJ1revB_TC09IN:
  - CalculiX 2.21 CAX6; 53,227 nodes and 25,080 elements.
  - 9 parts (TC-01/02/03/04/09, NZ-01/02/03/04).
  - Ties in the 'axial' variant; 19 cases.
- S-3D gimbal v1.1: CAD v3.4 V5c, massprops v3.4.1, poses centre and betam7.
- Stiffness V5c v1: CAD v3.3 plus the V5c stiffening.
- joints v1p1.
- CAD v3.5: 106 BOM lines, 148 assembly instances. make_all run 6 is still running; 12 of 18 poses are logged at 15:39 UTC.

**Claims checked**
- (a) The FEA supports the assembled engine at LC1–LC6 and at FA-1 90/92/102 bar, with negatives reported as found.
- (b) The v3.5 CAD folder is the complete, consistent part set and is ready to freeze once the pose checks finish.

**Sources (sha256/16, as read 2026-10-13)**

Interfaces and requirements:

| File | sha256/16 | Note |
|---|---|---|
| interfaces/mechanical.json v2.1 | e4d3e7c9df529171 | |
| interfaces/combustion.json v2.4a | 5237d4584bad38c4 | |
| interfaces/CHANGELOG.md | b53a35db05dc76ba | 186 lines |
| interfaces/gnc.json v3 | 3e97c378cfebee95 | |
| interfaces/electronics.json v2 | da067408c1594814 | |
| 00-requirements/REQUIREMENTS.md | ef308e24783cba0e | |
| 00-requirements/ICD-AIRFRAME.md | 706455abf4098182 | |
| 02-combustion/data/v2/thermal_bc_max_v2.csv | 83f3eca990fe9ba3 | the file S-AX used |

FEA:

| File | sha256/16 | Note |
|---|---|---|
| 04-fea/loadcases_v1.json | cbafa22eb69ef039 | |
| 04-fea/materials/materials_v1p4.json | 18aa13a888b1e6f3 | |
| 04-fea/structural/sax.py | 3ae4b1767f828ab6 | |
| 04-fea/structural/joints.py | 027c30e030939e5f | |
| 04-fea/structural/gimbal_strength.py | 15b5bbbc54362f20 | |
| results/sax_results_L1_TC09IN718_thJ1revB_TC09IN_v1.json | f0e58699bf30b513 | |
| results/sax_margin_table_…_v1.csv | ba26b3d7a78cc753 | 171 rows |
| results/sax_convergence_v1.json | 95fbe029be5e5c0a | |
| results/s3d_results_v1.1.json | beeba889ae549415 | |
| results/s3d_margin_table_v1.1.csv | 8fe7b075398d9b24 | 132 rows |
| results/joints_v1p1.json | 2b9c8892b9c1d7b0 | |
| stiffness/gimbal_k_summary_V5c_v1.json | 82a737caa138259a | |
| author run A1_22.2 sax.inp | 18a2a45ace110652 | |
| author run A1_22.2 res.npz | 351bc4c85649f4fc | |
| author run A1_22.2 sax.dat | 5756fff4fa19539f | |
| Ansys deck mechanical/engine/04-fea/structural/ansys/sax_FA1QB_A1_22.2_L1_v1.inp | f05abc80a5a1dc2c | |

CAD:

| File | sha256/16 | Note |
|---|---|---|
| 03-cad/BOM_v3.5.json | 2aff55e700ef0536 | |
| 03-cad/massprops_v3.5.json | 8c11e1e136fc59d8 | |
| 03-cad/README.md | 1d80819858356bb2 | still the v3.4.1 text |
| assembly/assembly_manifest_v3.5.json | ece8ffd51f3de146 | |
| assembly/ENGINE_v3.5_neutral.glb | 812b78f59127e670 | |
| assembly/ENGINE_v3.5_neutral.step | 0dd8064359c6aa26 | |
| checks/roundtrip_parts_v3.5.json | db0c29638270a81b | |
| checks/checks_v3.5.json | 974a236f1e6d94b6 | changing; 5 poses stored when read |
| parts/ENG-BL-02.step | 53fe82fe70761b13 | |
| src/make_all.py | 9d74136b6b502c6e | |
| src/checks.py | d13a13fd30558794 | |
| src/config.py | c91b2aa46f35e5a0 | |
| runs/make_all/make_all_v35_run6.log | cfa711ef428a9dc0 | changing |

**Tests run by the reviewer**
- Two exact ccx re-solves of author decks (nice 15, one thread; my processes have all finished):
  - A1_22.2: 27.5 s;
  - B1_21.65: 43 s.
- Hand checks C5(a)–(d).
- Recomputation of the convergence metrics.
- GLB sweep of the engine and ring groups in 72 directions at 7° and 8°.
- Exact B-rep check of BL-02: 16 poses, with a boolean intersection against the wall shell.
- Ten STEP spot checks, BOM arithmetic and coverage.
- Contact superposition estimate on 97 interface pairs.
- NZ-02 interface temperatures.
- Audit of the wall-check output.
- Case collar-band temperature.
- Differential growth across the thread in 5 thermal states.
- Not run: npm test/build (no app change); no new FE models (no contact FE, no S-3D or stiffness re-run).

**Still undemonstrated, and next closure:** see sections 3 and 5.

## 1. Criteria

**C1 Load-case coverage: FAIL for "full"; PASS for the axisymmetric pressure and thermal set at max thrust.**

Covered (SIM):
- **S-AX, 9 parts × 19 cases:** LC1, LC2, BN, LC4, TS1a/b, TS2, SEGP, TB70, TBS, LC6 (axial), and FA1, FA1S, FA1Q/QB (90 bar), FA1D/DB (92), FA1U/UB (102).
- **S-3D, 11 parts × 6 cases × 2 poses:** LC1, LC2F, LC3, GS, SR, LC6.
- **Joints:** J-FWD, J-AFT, J-AFT-TC09, J-BON, J-TC03, J-GIM.
- **FA-1 loads remain bounding.** Combustion v2.4a puts the FA-1 head at 83.0–88.0 bar abs, which is at or below 90 (SIM, CHANGELOG 185).
- **FA1S** is the step bound (DLF 2.0, about 151 bar) and is a sensitivity case. In it J-FWD with A4-70 shows MS_y −0.41 and MS_u −0.047 (SIM). Its status as "sensitivity, not a design case" should be stated.

Gaps:
- Gimbal 8° stop, cone-7 poses and the FA-1 spike in 3D (RM1-07).
- Static-fire duty cycle DC-D (RM1-09).
- Inertial loads are older than gnc.json v3 (RM1-15).
- Secondary structure (RM1-14).
- Contact states (RM1-03, RM1-04).

**C2 Criteria and safety factors: PARTIAL.**
- Flight cases use ENG-10 (1.5 / 2.0) at temperature.
- FA-1 uses yield at 92 bar and ultimate at 102 bar, SF 1.0 (lead 177 (2)).
- The 183 (1) metal criterion is implemented: primary-only MS, P+Q nodal shakedown, and part T versus T_limit.
- BN uses SF 1.0 (lead decision 2026-10-12).
- **Was LC2F ever confirmed? No.** loadcases_v1 says "Mechanical choice, lead to confirm", and LC2F has 0 hits in the CHANGELOG, REQUIREMENTS and mechanical.json (RM1-10).
- The SF 1.0 used for TS2, SEGP and TBS is also untraced.
- The temperature condition was applied using the node temperature (RM1-06).
- For carbon-phenolic the label says "s1 vs St", but no St exists (RM1-11).

**C3 Allowables at temperature: PARTIAL.**

| Material | Allowables as used | Source class |
|---|---|---|
| IN718 | Fty/Ftu at 20, 649, 704 °C | DATASHEET (SMC-045, AMS 5662/5663) |
| 6061-T6 | ASTM minimum × ASM 10,000 h ratio (conservative for minutes of exposure) | LITERATURE |
| SS316L | EN 10088 | LITERATURE |
| Graphite IG-110 | St 25, Sc 78 MPa | DATASHEET |
| Carbon-phenolic | Sc 200/100/20 MPa at 20/300/1000 °C; no St | ASSUMED |
| Flexible graphite | | ASSUMED |
| 7075-T6 | single RT value 470 MPa, no T table; T_max 120 °C | LITERATURE |
| A4-70 | RT only; knock-down at 54/148 °C TO-VERIFY (author's flag) | LITERATURE |
| A4-80 | absent from materials_v1p4 | — |
| 608 bearings | C0 1.37 kN | AS RECALLED (admitted) |

- 7075-T6 has no temperature table although S-3D LC6 runs it at 130.7 °C.
- Sensitivity (DERIVED, knock-downs ASSUMED): a 15 % A4-70 knock-down at 148 °C still leaves TBS at MS_y +0.20. A 5 % knock-down at 54 °C leaves the A4-80 FA-1 yield margin at about +0.22. The signs hold, but the values are not sourced.

**C4 Model fidelity: FAIL.**

Passes:
- **Boundary conditions and units.**
  - Pressure integral versus support reaction ×180: OP 197.357 / 197.402 N per MPa, BL within 0.3 %, PM 0.0 % (SIM; my re-run .dat is identical).
  - Gravity gives 16.19 N/g, which is 1.651 kg modelled against 1.625 kg in the BOM for the 9 parts. The +1.5 % is consistent with axisymmetric idealisation (DERIVED).
  - Stress components (r, z, θ) were verified at the TC-01 governing node.
- **GLB frame.** (x, y, z)_glTF = (x, z, −y)_engine / 1000 is verified: bounds error ≤ 0.087 mm. Pose convention verified at combined045: α −4.962°, β 4.944°. STEP files are in mm.
- **Thermal boundary conditions are current** (v2 file, 83f3eca990fe9ba3). Only the description text is stale (RM1-13).
- **Ring temperature.** The 60 °C ring temperature ASSUMED in flight is conservative: the case collar band is at 22.8–25.5 °C at end of burn (SIM).

Fails:
- Contacts (RM1-03).
- Thread-tie choice (RM1-04).
- Mesh convergence at two or more governing locations (RM1-05).

**C5 Independent recomputation: PASS** (section 2). Only repeatability and arithmetic are confirmed.

**C6 CAD integrity: FAIL** (RM1-01 is BLOCKING).

Passes:
- **STEP spot checks: 10 of 10.**
  - Hashes match the round-trip record; units are mm.
  - Each file holds one valid solid; volume relative difference ≤ 6e-7.
  - STLs are watertight; BOM mass equals volume × ρ within 0.15 %.
- **File coverage.**
  - 111 STEP files = 106 BOM part numbers + 5 declared sub-solids.
  - Every BOM part number has a STEP and an STL.
  - GSE part GM-12 is excluded from the assembly and from flight mass.
- **Mass reconciliation.**
  - BOM flight mass 5.13644 kg plus sub-solids 0.07332 kg gives 5.20976 kg, against massprops wet 5.20973 kg (DERIVED).
  - The 150 massprops entries are the 148 instances plus 2 hose halves (FD-07 and BL-04 split 0.50/0.50, ASSUMED).
- **Interference whitelist.** All 14 entries are justified modelling artefacts.
- **Geometry change since v3.4.1.** v3.5 adds only 13 new BL part numbers; every other part volume is identical, so the S-AX geometry is current.

Fails:
- RM1-01 and RM1-02.
- Pose checks are incomplete: 12 of 18 logged, and checks_v3.5.json held only 5 poses when read.
- 41–55 "unexpected" pairs closer than 3 mm per pose are unclassified; the smallest is GM-15/GM-20 at 0.5 mm.
- The FD-11 P-clip tabs reach 1.8 mm into the wall.
- BOM hardware is missing (RM1-12).

**C7 Deliverable coherence: FAIL.**
- **"Assembled engine" overstates.** S-AX is a tied, axisymmetric 9-part stack. The 3D model covers 11 gimbal parts at 2 poses. The pintle, feed, bleed, servo and secondary structure are not in any FE model.
- **No FEA report.** There is no 04-fea REPORT, although the BOM NZ-04 note cites one.
- **Mixed configurations.** The convergence study, the VTU export and the Ansys deck belong to the superseded 316L L1_v1 configuration. v3.5 plots exist only for FA1Q and FA1UB.
- **Stale interface.** mechanical.json publishes the v3.3 stiffness (RM1-08).
- **Stale README.** README.md is still the v3.4.1 text.
- 183 (4) is met in the tables (171 S-AX rows and 132 S-3D rows), but not in a founder-facing report.

## 2. C5 recomputation

| # | Item | Author value (tag) | Reviewer value (tag) | Result |
|---|---|---|---|---|
| e1 | Exact re-run of A1_22.2 (deck 18a2a45ace110652) | res.npz 351bc4c85649f4fc (SIM) | .dat byte-identical (5756fff4fa19539f); 10 of 10 unit arrays bit-identical (SIM) | FA1Q TC-01 node 30980 at (30.114, −132.460), 23.08 °C: vM 125.5395 MPa, allowable 239.532, MS +0.9080, identical |
| e2 | Exact re-run of B1_21.65 | res.npz (SIM) | .dat identical; 10 of 10 arrays bit-identical (SIM) | LC1 TC-09 governing vM 295.609 vs 295.6 stored |
| a1 | TC-01 plain wall, 90 bar | SCL Pm 73.9; membrane (r, z, θ) = (−4.25, 35.20, 81.00); Fz 21,177 N (SIM) | thick wall: hoop 81.0, σz 35.4 (closed-end 38.4), vM 74.1; Fz 21,311 N (DERIVED) | 0.3–0.6 % |
| a2 | TC-01 relief groove, z −132.46 (ri 28.575, ro 30.5) | peak 125.5, 1.10 mm from the corner (SIM) | isolated section: hoop 133.6, σz 59.7, vM 119.7 upper bound, so membrane MS ≥ +1.00 at SF 1.0 (DERIVED) | membrane positive; peak lies in the singular zone (RM1-05) |
| a3 | TC-01 collar groove | Pm 84.2 (SIM) | vM 87.2 (DERIVED) | author σz is lower because thrust is reacted at the band boundary condition |
| a4 | TC-09 barrel, 90 bar | Pm 105.3 including thermal; hoop 117.8; Fz 24,122 N (SIM) | hoop 109.9, σz 49.2, vM 99.1; Fz 24,578 N (DERIVED) | 2–7 % (author includes thermal) |
| b | J-FWD 8×M5: d3 4.0185, As 12.683 mm², r 28.631 (from F_end), sharing 1.15 (ASSUMED) | A4-80 MS_y +0.29 at 92 bar, MS_u +0.61 at 102; A4-70 at 90 bar MS_y −0.0112 (SIM/DERIVED, scaled) | τ 268.5 at 92 bar gives +0.289; τ 297.7 at 102 gives +0.612; A4-70 at 90 gives −0.0116 (DERIVED; ISO 3506-1 600/800 and 450/700 AS RECALLED; shear 0.577·Rp0.2 and 0.6·Rm) | arithmetic reproduced; 182 (6) still open |
| c | 608 under the FA-1 spike, 8° stop | −0.24 / −0.10 | P0 1.800 kN gives −0.239; SDOF 3.05 kN gives P0 1.525 kN and −0.102 (DERIVED; C0 AS RECALLED) | same (admitted item) |
| d | GM-03 LC1 (one 3D margin) | seat reaction 250.0 N; vM 10.3–11.1; MS_y +13.1 / +14.1 (SIM) | statics 250 N per seat; bearing stress 2.98; Kt 2–4 (ASSUMED) gives 6.0–11.9 and MS +12.1…+25.2 (DERIVED) | consistent; weak check, but sign-conclusive |
| x1 | Convergence metrics | p, GCI, extrapolation (SIM) | identical to machine precision (DERIVED) | classification differs (RM1-05) |
| x2 | Released-interface gaps, LC1 | interfaces_governing (SIM) | −0.1377…−0.0296 mm on 97 pairs (DERIVED) | identical |

## 3. Findings

### RM1-01 — BLOCKING: BL-02 goes through the bay bore inside the flown gimbal envelope

**Gates:** CAD freeze; static fire if run in the flight bay or a bay simulator with gimbal motion; flight.

**Evidence**
- **Position.** BL-02 is a v3.5 bleed adapter on FD-01, in the engine group. It sits at z 153.2–165.2 mm above the pivot and at r ≤ 51.5 mm in neutral. A 7° tilt moves it about 19–20 mm outward (DERIVED).
- **Exact B-rep at 7°** (STEP rotated by R = Rx(α)Ry(β), tessellation 0.002 mm, boolean intersection with a shell r 70–75):

  | φ (°) | r_max (mm) |
  |---|---|
  | 140 | 69.984 |
  | 150 | 70.494 |
  | 155 | 70.594 |
  | 157.5 | 70.605 |
  | 160 | 70.589 |
  | 170 | 70.268 |

  - At most −0.605 mm of clearance and 1.54 mm³ of the part beyond r 70 (DERIVED).
- **Exact B-rep at 8°.** Over φ 135–180° r_max is 72.08–73.26 mm, i.e. −2.08 to −3.26 mm and 30–107 mm³ beyond the wall (DERIVED).
- **GLB sweep, 72 directions at 5° spacing**, engine and ring groups, tolerance +0 / −0.1 mm:
  - at 7°: beyond the wall in 6 of 72 directions (φ 145–170°); inside the 1 mm keep-out in 12 (φ 130–185°);
  - at 8°: beyond the wall in 16 of 72 (φ 120–195°); inside the keep-out in 18 (φ 115–200°);
  - BL-02 is the only rigid-group instance above r 69.0 (DERIVED).
- **The author's own data agree.**
  - BL-02 at β −7° (φ 180°): 0.469 mm. At combined135: 0.423 mm. Mine are 0.469 and 0.424.
  - Both already violate the ≥ 1.0 mm requirement in 182 (5), yet nothing flags them.
- **This is inside the flown envelope.** In the gnc.json v3 v3_check, the per-run maximum gimbal angle has p50 7.26°, p99 7.94° and maximum 8.0° (SIM).
- **This is new evidence, not the admitted 70.6 mm item.** BL-02 is absent from the v3.4.1 rev B corridor sweep, which excluded bleed parts.

**Fix**
- Relocate or re-orient BL-02: lower the tap toward the pivot plane, or turn its outer features inward. Alternatively, obtain a local bore relief from Lauty via ICD-AIRFRAME (182 (5)).
- Re-run the signed sweep from RM1-02 to r ≤ 69.0 up to 8°, plus the tube ID tolerance (TO-VERIFY).
- Re-route BL-03 and BL-04 accordingly.

### RM1-02 — MAJOR: the CAD wall check cannot reveal a moving-part violation and does not implement 182 (5)

**Gate:** CAD freeze.

**Evidence**
- **How the check works.** checks.py uses an unsigned min_distance to a tube r 70–80. It returns 0.0 for touching and for intersecting alike, and stores only the 12 nearest instances.
- **What the stored output shows.** In all 5 stored poses:
  - the 12 entries include 4 fixed instances at 0.0 mm and other fixed parts up to 1.25 mm;
  - the only moving entry ever listed is BL-02 at 0.469 mm, and it is not flagged (rm1_wall_top12_audit_v35.json).
- **Consequence.**
  - A moving part with more than 1.25 mm of clearance never appears in the list.
  - A penetrating moving part ties at 0.0 with the fixed parts.
  - The run-6 log shows "wall min 0.0 (ENG-BL-06#0)" at all 12 completed poses.
- **The fixed 0.0 entries are intersections, not contacts.**
  - BL-06 is the intended through-wall vent fitting, r_max 74.17 mm.
  - FD-11 (three P-clips) reaches r_max 71.80 mm, with 30 % of its vertices beyond r 70. These are flat tabs on a 140 mm bore and sit about 1.8 mm into the wall; the fit is TO-VERIFY (DERIVED).
- **Coverage gaps.**
  - The check samples 8 directions plus the stops, not 72.
  - It has no pass/fail threshold at r 69.0.
  - The horn, pushrod and hose groups are not swept by the author, nor by me.
- **The admitted 70.6 mm is not reproduced.** At az 56/122 the rigid v3.5 engine and ring groups reach at most 63.4 mm (DERIVED). The source part is unidentified (TO-VERIFY: a flexible group or a different pose definition).

**Fix**
- Moving groups: signed per-instance r_max or penetration volume, 72 directions at 7° and 8° plus the stop polygon, pass/fail at 69.0.
- Fixed parts: a separate check against a whitelist of intended through-wall items.
- Flexible groups: include them with their kinematics.
- Make it the permanent check.

### RM1-03 — MAJOR: nozzle-stack radial contact is not modelled

**Gates:** FEA deliverable; static fire; flight.

**Evidence**
- **What the model assumes.** sax.py states that a negative post-check gap is "a contact the linear model does not carry".
- **TC-09 / NZ-02 in LC1** (B1_21.65): all 97 TC-09 bore / NZ-02 OD pairs close over z −229.6 to −210.75. The closure is −0.030 to −0.138 mm (DERIVED from the SIM re-run).
- **Other interfaces in the author's table** (SIM):

  | Interface | Closure (mm) | Case |
  |---|---|---|
  | TC-09 / NZ-04 | −0.093 | |
  | TC-09 / NZ-03 | −0.091 | BN |
  | NZ-01 / NZ-02 | −0.043 | |
  | TC-02 / TC-03 | −0.033 | |
  | TC-01 / TC-09 thread | −0.042 / −0.068 / −0.050 | FA1 / FA1S / SEGP-TS2 |

- **Drawing fit.** The TC-09 insert bore is 50.0 H8, giving at most 0.0195 mm radial clearance (ISO 286, AS RECALLED). The NZ-02 OD tolerance is not stated (TO-VERIFY). The LC1 closure is therefore about 7× that clearance.
- **Bound estimate.** Plane-stress compound cylinder (graphite / carbon-phenolic / IN718), carbon-phenolic E 7/12/20 GPa (ASSUMED), no friction:
  - contact pressure 34.1/36.7/39.5 MPa at r 25 and about 34 MPa at r 22;
  - added TC-09 hoop stress 359/387/415 MPa (DERIVED).
- **Effect on TC-09.** Superposed on the FE LC1 stress at the 97 nodes, the TC-09 interface MS (SF 1.5, Fty DATASHEET) drops from +1.32 to +0.73/+0.61/+0.49 (DERIVED). That is below the FE-only governing value of +1.17.
- **Effect on NZ-02.**
  - The inner side (r 22) is at 1246–1389 °C, fully charred (SIM). About 34 MPa against an ASSUMED char strength of 20 MPa means crush is likely (MS about −0.61, DERIVED).
  - The outer side is at 277–418 °C (virgin material), where Sc is 87–108 MPa, so it is positive.

**Fix**
- Run contact (frictionless at minimum, with a carbon-phenolic modulus band) on TC-09/NZ-02/NZ-03/NZ-04 and the M63 thread. Cover LC1, BN, TB70/TBS, TS2 and FA-1.
- Alternatively, put radial clearances on the drawings that exceed the computed closures at temperature.
- Report NZ-02 and NZ-03 char-zone compression with contact included.

### RM1-04 — MAJOR: thread-tie bound not run for v3.5 or any FA-1 case, and the radially free assumption is contradicted

**Gates:** FEA deliverable; flight.

**Evidence**
- **Sensitivity on the 316L baseline**, bonded versus axial tie (SIM):

  | Part | Case | Axial | Bonded |
  |---|---|---|---|
  | TC-01 | SEGP/TS2 | +1.77 | +0.84 |
  | TC-02 | SEGP/TS2 | +2.6 | +0.96 |
  | TC-03 | BN | −0.05 | −0.21 |
  | TC-03 | LC1 | −0.37 | −0.47 |

  No bonded run exists for the v3.5 configuration or for any FA1 case.
- **The TC-01 FA-1 governing node is in the tie-controlled zone.** It sits 1.10 mm from the corner of the M63 thread-relief groove.
- **The author's own post-check shows the thread closing radially** in FA1, FA1S and SEGP/TS2 (SIM).
- **Free differential radial growth across the M63×1.5 6H/6e thread** (author's mean CTEs and deck temperatures; DERIVED):

  | State | Free growth (mm) | vs 0.033 mm allowance |
  |---|---|---|
  | LC1 | 0.002–0.007 | |
  | FA1 | 0.001–0.004 | |
  | TS2 at 36.7 s | 0.008–0.016 | |
  | TB | 0.012–0.017 | |
  | TS2 at 186.7 s (thread 153.6–165.8 °C) | 0.045–0.048 | 1.44× |

  The allowance is half the 6e allowance (ISO 965-1, AS RECALLED). At 186.7 s a minimum-clearance thread binds.
- **The TC-09 BOM note is stale.** It still quotes "~0.05 mm at +100 K", which is the 316L figure. For IN718 the figure is about 0.066 mm (DERIVED), which equals the whole 6e allowance.

**Fix**
- Run the bonded bound or contact for v3.5 in LC1, BN, TS2, SEGP, TB70/TBS and FA1Q/D/U.
- Report the lower of axial and bonded.
- Update the note.

### RM1-05 — MAJOR: convergence not demonstrated at governing locations, and no v3.5 study

**Gate:** FEA deliverable.

**Evidence** (the study covers only the 316L baseline at h 2 / 1 / 0.5; my p, GCI and extrapolation equal the author's, DERIVED)

| Location | MS (h 2 / 1 / 0.5) | Observed | Author label |
|---|---|---|---|
| TC-01 FA1Q | 1.042 / 0.914 / 0.816 | p 0.38, GCI 49 % | converging (monotonic) |
| TC-01 FA1D | 0.999 / 0.872 / 0.776 | p 0.40 | converging (monotonic) |
| TC-01 FA1U | 0.801 / 0.687 / 0.601 | p 0.39, GCI 58 % | converging (monotonic) |
| TC-01 LC2 | 1.70 / 1.53 / 1.40 | p 0.34 | converging (monotonic) |
| TC-02 LC1 | −0.7466 / −0.7469 / −0.7542 | changes grow | within 2 % |
| TC-02 BN | −0.624 / −0.625 / −0.636 | changes grow | within 2 % |
| NZ-01 FA1Q | 3.34 / 3.23 / 2.34 | diverging | |
| TC-09 FA1Q / FA1D | | oscillatory | |
| NZ-01 LC1 | | p 1.83 | converged |
| TC-03 LC1 | | p 1.46 | converged |

- The CAX6 nominal order is about 2. p well below 1 marks a singular or steep zone, so the Richardson extrapolation (+0.49 for FA1Q) is invalid.
- The v3.5 TC-01 FA-1 value of +0.908 is a medium-mesh peak at a node 1.10 mm from a corner. That is just outside the 1.0 mm exclusion radius, and the root radius is undefined on any drawing.
- Defensible bases instead:
  - membrane MS ≥ +1.00 (DERIVED);
  - the author's SCL value +1.60;
  - the fine-mesh peak +0.82.

**Fix**
- Run a v3.5 study with at least 3 levels at the LC1, FA1Q/D/U, BN and TB70 governing nodes.
- Define and model the groove root radius.
- Treat corner peaks with a local strain or fatigue criterion.

### RM1-06 — MAJOR: the 183 (1) temperature condition is exceeded (new evidence under the adopted criterion)

**Gates:** FEA deliverable; static fire; flight.

**Evidence** (author columns T_part_max_C and T_limit_C, SIM; limits LITERATURE-approx)

| Part | Part max T | Case(s) | Limit | Note |
|---|---|---|---|---|
| TC-03 (IN718) | 710.7 °C | LC1, LC2, BN | 650 °C | line 183 quoted 600 °C, which is the node T; condition 4 fails |
| TC-01 (6061-T6) | 175.0 °C | TB70 / TBS (abort state by construction) | 150 °C | |
| TC-01 | 165.8 °C | TS2 | 150 °C | |
| TC-01 | 155.8 °C | LC6 | 150 °C | |
| TC-01 | 144.6 °C | LC1 | 150 °C | within limit, 5.4 K margin |
| TC-09 (IN718) | 655.2 °C | TS2 / LC6 | 650 °C | |
| TC-02 | 255.5 °C | | 150 °C | line 183 quoted 215 °C node T; design change already mandatory |
| GM-01/02 (7075-T6) | 130.7 °C | LC6, from the case collar soak | 120 °C | 7075-T6 has no temperature table |

- The stand abort temperature (175 °C) is above the case's own usable limit.

**Fix**
- Per 183 (1): either a design change, or a sourced time-at-temperature limit per part (minutes per firing plus cumulative exposure).
- Set the abort at or below the case limit, or justify it.
- Report part-maximum temperature, not node temperature.
- Add temperature-dependent 7075-T6 allowables.

### RM1-07 — MAJOR: 3D gimbal coverage

**Gates:** FEA deliverable; CAD freeze (GM-01/02 geometry); flight.

**Evidence**
- **Poses.** S-3D v1.1 covers only centre and betam7. There is no 8° stop pose, although LC3 defines one and GNC SIM reaches 8.0°. There are no cone-7 poses; the stiffness model used 9 poses.
- **Missing case.** No FA-1 spike (1.8 kN × DLF 2.0) is applied to the rings, pins or collar.
- **Mass properties.** The model uses massprops v3.4.1: engine group 2.76114 kg versus 2.81759 kg in v3.5, and I_pivot +2.4 %.
- **183 (3) is not implemented in geometry.** In v3.5 it appears only as a material change (7075-T6) and the drawing note "all internal corners R ≥ 2".
  - The GM-01/02 solids are volume-identical to v3.4.1 (22,503.064 and 22,960.662 mm³), so the fillet is not modelled.
  - No re-run shows MS ≥ 0 at every LC3 pose in 7075. The stored betam7 values are −0.056 / −0.186 (admitted).

**Fix**
- Re-run S-3D on v3.5(.1) geometry with the fillets modelled.
- Cover all 9 poses plus the 8° stop poses, add the FA-1 spike, and use v3.5 mass properties.

### RM1-08 — MAJOR: ENG-11 stiffness

**Gates:** FEA deliverable (interface coherence); GNC/TVC; flight.

**Evidence**
- **Spread fails.** V5c mech_T is 3238.7–7406.0 N·m/rad with mean 5353.1. The spread is −39.5 / +38.3 % against the required ±20 %, so it fails by the author's own figure (SIM). K_beta alone spans −25.1 / +19.5 % about the centre value 4325.1, which also fails (DERIVED).
- **Hard minimum (3100) is met only narrowly.**
  - Minimum 3238.7 is +4.5 %; chain-low 3133.2 is +1.1 % (SIM).
  - The model is CAD v3.3 plus V5c, with a rigid airframe at the 16 M5 holes, a rigid case, inertia from massprops_v2, and 7° poses only.
  - It has no V5c mesh study (mesh_study is empty). The v3.3 study (h4 → h3 → h2.5: −1.8/−1.3 %, then −0.3/−0.3 %) converges from above.
  - The residual mesh error and the stiffening effect of the rigid boundary conditions are of the same order as the 1.1 % margin. Compliance is therefore not demonstrated with margin.
- **The interface is stale.**
  - mechanical.json v2.1 publishes v3.3 values: centre 2442.0 / 1608.2, total 552.5–1681.0.
  - It also says the stiffening is "not yet in the CAD baseline (v3.4)", while config.py records V5c as accepted into v3.4.
  - No CHANGELOG line records the V5c result.

**Fix**
- Publish V5c in mechanical.json v2.2, with tags.
- Run a mesh study plus a compliant airframe/case bracket, and add 8° poses.
- Record the spread failure as OPEN for GNC and the lead.

### RM1-09 — MAJOR: static-fire state

**Gate:** static fire.

**Evidence**
- **The thermal state is ASSUMED.** TB70/TBS take the end-of-burn field and shift it uniformly to the 448.15 K abort. The static-fire duty cycle DC-D (49 s) has no thermal run.
- **NZ-03 sits near zero on an ASSUMED strength.**

  | Case | MS | MS_all_nodes |
  |---|---|---|
  | BN | +0.036 | −0.660 |
  | TBS | +0.034 | −0.658 |
  | TB70 | +0.123 | −0.628 |

  These are against an ASSUMED char strength of 20 MPa (Combustion requirement ≥ 21 MPa, TO-VERIFY) (SIM).
- **The DLF item is OPEN.**
  - TB70 is run at DLF 1.0 "pending modal".
  - The modal model is axisymmetric n = 0, with the groove band rigid and internals absent, so its frequencies are upper bounds.

**Fix**
- Run the DC-D transient and use it for the TB states.
- Test char compressive strength at temperature, or evaluate the J1b mica contingency.
- Close the modal DLF.

### RM1-10 — MINOR: safety factors not traced to a decision

**Gate:** FEA deliverable.

**Evidence**
- The LC2F factors (1.0 / 1.5) were never confirmed. TS2, SEGP and TBS (SF 1.0) also have 0 CHANGELOG hits.
- Sign check (DERIVED): LC2F stays positive at the ENG-10 factors.
  - GM-03 vM 20.1 gives +6.8 at 1.5 and +5.3 at 2.0 (ultimate).
  - GM-01/02 are at MS_y ≥ +23.6 at SF 1.0.

**Fix:** the lead confirms these factors, or applies ENG-10.

### RM1-11 — MINOR: table artefacts and brittle-criterion labelling

**Gate:** FEA deliverable.

**Evidence**
- **Meaningless margins.** The results JSON holds 27 infinite margins and +1260 to +3626 values for NZ-02/NZ-03; the CSV caps them at 99.0. They come from the char rule, which checks only primary s3 and is near zero in soak.
- **Tension is never checked for carbon-phenolic.** sax.py maps CARBON-PHENOLIC to (None, "Sc") and the material has no St, yet the label prints "s1 vs St". As a result, NZ-03 tensile s1 is unassessed: 34.0–47.5 MPa in TS2, and 115.6 MPa at 500.7 °C in LC6 (SIM).

**Fix**
- Print "n/a" together with s1 and s3.
- State the carbon-phenolic tension rule as a hypothesis with a containment or test criterion (as in 183 (2) / 186 (3)), or source St(T).

### RM1-12 — MAJOR: standard hardware and seals are not in the part set

**Gates:** CAD freeze (the "entire part set" claim); fabrication.

**Evidence**
- **Hardware lines.** The BOM has only 4 hardware lines: 608-2RS, DIN 6799, GE 5 E and ISO 10642 M3.
- **Notes only.** Part notes reference about 130 M2–M5 screw positions (approximate census) and O-rings AS568-010, -012, -013, -016, -226 and -229. None of these has a BOM line or a solid.
- **J-FWD screws.** The A4-80 grade for the J-FWD screws (177 (2)) appears only in the TC-02 notes text.
- **Mass.** There is no hardware mass allowance. The missing mass is of order 0.1–0.2 kg (DERIVED, unit masses ASSUMED), comparable to the 0.10 kg GNC re-fly trigger.

**Fix**
- Add BOM lines (standard, grade, length, quantity, DATASHEET mass, torque), starting with the J-FWD screws.
- Carry a mass allowance until the lines are in.

### RM1-13 — MINOR: documentation currency

**Gates:** FEA deliverable; CAD freeze.

**Evidence**
- README.md is still the v3.4.1 text (182 (8)).
- The TC-09 thread note is stale (RM1-04).
- 41–55 pairs per pose have an empty expected_contact field.
- loadcases_v1 (LC1/LC2) and mechanical.json inputs_read cite thermal_bc_max_v1.csv.
- LC3/LC6 sources cite gnc.json v1.
- The BOM NZ-04 note cites a non-existent 04-fea REPORT.
- There are no v3.5 plots for LC1, LC2 or BN.
- The VTU export and the Ansys deck are 316L-era.
- The checks file was rewritten during the review.

**Fix:** refresh all of these at freeze.

### RM1-14 — MINOR: secondary structure not analysed

**Gates:** fabrication; static fire; flight.

**Evidence**
- PD-01: 4×M3 into TC-02.
- FD-01: 2×M3; it carries BL-02 and BL-03.
- FS-15: 2×M4 plus 2×M5 into the airframe wall.
- FD-09: 2×M4 into GM-09.
- BL-05 valve mounts (TO-DEFINE): they carry two valves of 0.30 kg each (ASSUMED).

**Fix:** hand calculations (bolt shear/tension, bracket bending, fitting moments) at the current limit loads.

### RM1-15 — MINOR: inertial loads predate gnc.json v3

**Gate:** flight.

**Evidence**

| Load | Used by Mechanical (gnc.json v1) | Published in gnc.json v3 (SIM, limit = max of 500 runs) |
|---|---|---|
| Lateral at touchdown | LC6: 3.0 g | 6.29 g at the pivot |
| Body angular acceleration, flight | LC3: 8.59 rad/s² | 11.01 rad/s² |
| Body angular acceleration, touchdown | not applied | 79.28 rad/s² |
| Hinge moment at touchdown, unlocked | not applied | 7.83 N·m |

- Bound: scaling the whole S-3D LC6 stress by 2.10 keeps every gimbal part at MS_y ≥ +6.1 (GM-01, betam7; DERIVED).
- The real exposure is in the RM1-14 items, because S-AX cannot carry lateral loads.

**Fix:** update loadcases_v1 and re-run S-3D LC6.

### RM1-16 — NOTE: the Ansys deck is not a cross-check

The Ansys deck (f05abc80a5a1dc2c) is an unexecuted export of the superseded 316L configuration, not a cross-solver check. Regenerate it for v3.5 and run it, or label it as such.

### RM1-17 — NOTE: non-structural mass

The 1.651 kg modelled mass versus 1.625 kg in the BOM is consistent (+1.5 %). The grain (0.424 kg wet) and the internals are not in the body force: about 15 N at LC1 (3.65 g) and about 42 N at LC6. This is negligible against 21–24 kN of pressure end load (DERIVED).

### RM1-18 — NOTE: TC-02 governing point sits on the M14 thread tie

This does not re-litigate the TC-02 negative.
- The TC-02 governing point (r 7, z 106.6) sits on the TC-02/TC-03 M14 tie and flange seat, which shows a −0.033 mm overlap.
- A 5 mm² TC-02/TC-03 section overlap in the CAD was resolved by the mesher at all three levels.
- The thermal stress there (about 183–204 MPa) is close to the full-constraint mismatch E·Δ(αΔT) ≈ 215 MPa (DERIVED), and the value drifts with refinement.
- Judge the 182 (1) fix with a contact model and a clean CAD fit, so it is not sized against a tie artefact.

### RM1-19 — NOTE: collar/case radial interaction not modelled

- GM-01/02 bore 62.50 H9 on the case groove 62.50 h9 gives 0–0.074 mm radial clearance (ISO 286, AS RECALLED).
- Case radial growth is about 0.035–0.037 mm at 90 bar, plus thermal growth in soak (DERIVED).
- At minimum clearance the case loads the ring in hoop. Neither S-AX nor S-3D models this. Record it as an interface assumption.

## 4. Admitted and decided items: not re-litigated, status in v3.5

| Item | Status |
|---|---|
| 177 (1) TC-09 in IN718 | Done in BOM and S-AX; price TO-QUOTE (not checked). |
| 177 (2) / 182 (6) J-FWD A4-80 | Grade chosen only in notes. A4-80 is absent from materials; joints.py not re-run; no BOM line. OPEN. |
| 177 (4) / 182 (2) 608 C0 ≥ 1.80 kN with a datasheet | BOM still lists 608-2RS. OPEN. |
| 182 (1) TC-02 head | Geometry unchanged in v3.5. OPEN. Successor v3.5.1 thermal runs (v351scr, TBC variants) seen running; not reviewed. |
| 182 (3) bleed valves, 0.30 kg ASSUMED | OPEN. |
| 182 (4) NZ-04 | OPEN. |
| Seat-face adiabatic bound | OPEN; not reviewed. |
| 182 (5) bay wall | OPEN; RM1-01 and RM1-02 are new findings on top. |
| 182 (7) mass deltas | GNC line 184 reports +1.168 kg; hardware mass missing (RM1-12). |
| 182 (8) freeze conditions | Not met: pose checks and README unfinished; (1)–(6) not closed nor carried in a freeze record. |
| 183 (1) criterion | Applied as decided; RM1-06 adds the temperature trips. |
| 183 (2) / 186 (3) NZ-01 | Test-based acceptance; capture demonstration not reviewed (TO-VERIFY). |
| 183 (3) GM-01/02 | OPEN (RM1-07). |
| 183 (4) every part, every case | Tables exist; no founder report. |
| 186 (4) mechanical.json v2.2 content | OPEN. |
| 186 (5) tank outlet | The tank is not a BOM line; only flange FD-12F and the FS-01B port, route TO-DEFINE. OPEN. |
| Other admitted items | 608 above C0, TB70 −0.756, J-FWD scaled margins, NZ-04 577 °C, bay wall r 70.6, AS RECALLED allowables, LC1 and LC3 negatives: acknowledged only. |

## 5. Verdicts

### (a) FEA: REVISE

**Supervision-record mapping**
- The claim as worded ("full FEA of the assembled working engine at max thrust") is Rechazado within its scope.
- The subset below is Condicionado.

**Permitted use**
- S-AX results as reproducible SIM evidence for the configuration L1_TC09IN718_thJ1revB_TC09IN.
- TC-01 and TC-09 membrane and linearised margins at FA-1.
- The negatives as found, to drive design changes.
- J-FWD arithmetic.
- 608 spike loads.
- GM-03 LC1.

**Not permitted**
- TC-09 holder and NZ-02/03/04 margins (RM1-03).
- v3.5 thread-zone soak and TS2/SEGP margins (RM1-04).
- TC-01 FA-1 +0.91 as a converged value (RM1-05).
- TC-03 / TC-01 / TC-09 "pass" statements under 183 (1) (RM1-06).
- Gimbal stop and spike margins (RM1-07).
- ENG-11 compliance (RM1-08).
- Static-fire thermal margins (RM1-09).
- Any physical approval.

**Path forward**
- To reach CONDICIONADO as a whole: close RM1-03 to RM1-08, or carry them as explicit OPEN items with the affected margins removed.
- Before static fire: also close RM1-09.
- To reach ACCEPT WITH COMMENTS: additionally close RM1-10, -11, -13, -14 and -15, and issue a 04-fea REPORT with a checkpoint.

### (b) CAD v3.5: REVISE (not freezable)

**Supervision-record mapping**
- As a freeze candidate it is Rechazado (RM1-01).
- As a design model of record it is Condicionado.

**Permitted use**
- Geometry review.
- Mass properties for GNC, with the RM1-12 caveat.
- FE geometry source; the S-AX parts are unchanged from v3.4.1.
- STEP/GLB exchange; units and frames verified.

**Not permitted**
- Freeze, fabrication drawings or quotes, bay integration.
- Any statement that the gimballed engine clears the bay.

**Closure**
1. BL-02 fix (or bore relief).
2. Signed 72-direction check covering all moving groups at 7° and 8°, with pass/fail at r 69.0.
3. All 18 poses finished.
4. README v3.5.
5. BOM hardware and seal lines plus a mass allowance.
6. The < 3 mm pairs classified.
7. FD-11 tab fit checked.
8. 182 (1), (2), (4), (5) and (6) closed, or carried as OPEN in the freeze record (182 (8)).

A delta re-review of the frozen version is required (182 (10)).

## 6. Evidence package and limits of this review

**Location.** `/home/claude/work/shared-fallback/engine/reviews/mechanical/r1/`. All code is my own; no author module is imported. `MANIFEST_REV-MECH-1.sha256` hashes to b258bc363f99f4fa (39 files) and `sha256sum -c` passes.

**Scripts** (in `scripts/`):

| Script | Covers |
|---|---|
| rm1_sax_rerun_compare | re-run e1 |
| rm1_tc09_contact_superpose | re-run e2 and RM1-03 |
| rm1_hand_checks | C5 (a)–(d) and the contact bound |
| rm1_convergence_recheck | RM1-05 |
| rm1_baywall_sweep | RM1-01 |
| rm1_bl02_exact | RM1-01 |
| rm1_wall_top12_audit | RM1-02 |
| rm1_cad_spotcheck | C6 |
| rm1_nz02_interface_T | RM1-03 |
| rm1_collar_band_T | C4 |
| rm1_thread_fit_T | RM1-04 |

- Each script has a matching results JSON and log; `results/rm1_results_index.json` lists inputs and tags.
- Scratch decks and frd files are in `/home/claude/work/reviews-mech-r1/`.
- Runtime: `/opt/engine-venv/bin/python -I`; nothing was installed.

**Limits**
- No contact or other new FE models were run; the contact and thread results are bound-type indicators.
- Horn, pushrod and hose groups were not swept.
- Combustion and thermal inputs were not re-derived.
- The checks file and the run-6 log are still changing (12 of 18 poses at 15:39 UTC).
