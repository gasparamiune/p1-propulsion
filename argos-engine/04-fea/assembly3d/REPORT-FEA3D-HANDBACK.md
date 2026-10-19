BEGIN FEA3D-HANDBACK
# ARGOS H1 engine - assembled-engine 3D FE (FEA3D) - FINAL: F1 on asm v1.2, F2 (S-3D on v3.5.1), F3, F4 and the modal (coarsened)

| | |
|---|---|
| Status | **2026-10-19, FINAL handback (lead 188 scope: F1-F4 + modal)**: **F1** on the corrected connector model (asm v1.2, 7.1 closed): LC1 (4 S-AX thermal states), FA-1 (FA1Q/D/U/S + FA1T), LC3 (8 stop poses x 64 sub-cases, cold + hot lower bound), rigid and compliant airframe, mesh convergence (3 levels at 4 points; lever roots R2 / R3). **F2** S-3D on v3.5.1 at all 9 range-cone poses with both lever roots refined (9B; full report `hub/04-fea/s3d_v351/REPORT-S3D.md`). **F3** gimbal stiffness over the 9 cone and 8 stop poses and the compliant airframe (9). **F4** secondary-structure joints (hand calcs, 10). **Modal** on a coarsened all-L2 model with the FA-1 column sensitivity (9A, 9A.1). Margin matrix of every part x case (3A); mounting data as engine data for the datasheet (8.1; ICD-AIRFRAME v2.1 removed from scope, CHANGELOG 222); open items with owners (13). Supersedes REPORT a9f7f30055063c8e (modal / F3 publish), a66d660022618f48 (F1 FINAL) and the INTERIM (hub commit 9bd6958). |
| Author | fea3d (successor Senior FEA analyst 3D), lead brief CHANGELOG 188 + successor brief 2026-10-15 + coordinator 2026-10-19 (lead decision: fix 7.1 before modal and cones) |
| Configuration | CAD v3.5.1 frozen (CHANGELOG 206): MANIFEST `b62c0e0ac8555fb8`, ENGINE STEP sha16 `4ca22820c796b670`, 5.40921 kg wet. (03-cad/v3.5.2 is a GNC mass sensitivity per CHANGELOG 209/211, not used.) |
| Tool | CalculiX 2.21 (SPOOLES direct), C3D10 tets (gmsh 4.15 HXT), own Python pre/post (`src/`), assembly model **fea3d-asm v1.2** |
| Units | SI; mm, N, MPa, degC in the report where conventional. MS = allowable / (SF x stress) - 1 |
| Tags | SIM (FE output), DERIVED (computed from SIM/data), ASSUMED, DATASHEET, LITERATURE, TO-VERIFY, AS RECALLED |

> **Not physical approval.** A converged solution, matching numbers or clean plots do not approve hardware. Negative margins are reported as found; no margin has been forced. Every number below is SIM unless tagged otherwise.

## 0. Checkpoint (SUPERVISION-WORKFLOW template)

- **Delivered by / reviewed by / date:** fea3d (successor Senior FEA analyst 3D) / not reviewed: status *Por revisar* until the independent 3D FEA review (REV-MECH-2) / 2026-10-19.
- **Area and configuration:** ARGOS H1 engine, assembled-engine 3D FE. CAD v3.5.1 frozen (CHANGELOG 206; MANIFEST `b62c0e0ac8555fb8`, ENGINE STEP `4ca22820c796b670`); CalculiX 2.21 (SPOOLES), C3D10; assembly model fea3d-asm v1.2; interfaces gnc.json v3.1 (`4f3209323b0e0ed4`), mechanical.json v2.1 (`e4d3e7c9df529171`).
- **Change and claim to check:** section 1 (claims 1-12), F2 in 9B; margins as found, negatives not forced.
- **Sources and exact files:** section 12 and `MANIFEST.json` in this folder (sha256/16 of every file); S-3D folder `hub/04-fea/s3d_v351/MANIFEST.json`. Numbers are SIM unless tagged otherwise (DERIVED / ASSUMED / DATASHEET / LITERATURE / TO-VERIFY / AS RECALLED).
- **Criteria, method and checks run:** sections 2-10. Checks: engine free-body closure in every unit step (7.1), moment closure (7.2, open), mesh convergence at 4 points (5), lever-root refinement R2 / R3 (4.6) and the peak-inside-refinement check in every F2 pose (9B), Rayleigh / static-K cross-check of the modal on the same mesh (9A), stress probe vs ccx (9A.1), FA-1 band sensitivity to frequency scaling (9A.1), rigid vs compliant airframe (8).
- **Verdict and permitted use:** none by the author. SIM results; not physical approval. Usable as design input for Mechanical's design changes and as engine data for the datasheet, with the tags and limits stated.
- **Not yet demonstrated:** section 11.
- **Next closure:** section 13 (open items with owners).

## 1. Claims (checkpoint, SUPERVISION-WORKFLOW)

1. **Connector defect 7.1 closed (lead decision 2026-10-19).** Root cause: CalculiX SPRINGA uses the current (deformed) geometry also in linear static steps; with 1 mm auxiliary springs the inner-gimbal bushings on rigid-body references carried only 56-79 % of the engine load. Fix (asm v1.2): spring length 1e6 mm. **Unit-step free body of the engine now closes to <= 0.006 N in every unit step (100.00 % of the engine load through the inner bearings, inner washer and rods)** at LC1 neutral and at the 8 deg stop pose [SIM]. The deck changed, so LC1, the 8 LC3 stop poses and FA-1 were re-solved; the LC3 stop poses and the FA1T gimbal margins are re-posted on v1.2 (sections 6, 7).
2. **Effect of the fix:** engine-part stresses change <= 0.15 %, airframe hole loads < 0.3 %, LC3 margins unchanged to the third decimal; the bearing loads change materially: FA1T now 1764 N on each of the four needle cups (v1.1 gave 4036 N / 1766 N and 440 N on the inner washer), LC1 inner cups 199.8 N each. One residual observation stays open (7.2: moment closure 97-99.5 %, bounded impact).
3. **LC1:** negative total-stress margins at **NZ-01** throat -0.435 (B1_1, thermal, S-AX -0.443), **TC-03** flange corner -0.312 / -0.375 (B1_1, 98 % thermal; primary-only +7.3) and **TC-02** TB1 seat ultimate -0.119 (B1_19; 159 degC > 150 degC limit, check (d) open per CHANGELOG 212). All other parts positive.
4. **FA-1:** FA1S (151.04 bar abs, T > 1 ms bound) **TC-01 J-FWD hole -0.221 / -0.160**, converged (R3 -0.202 / -0.140). FA1Q/D/U positive. FA1T (3.6 kN spike, gimbal / mount parts) all positive, min GM-03 +1.483 / +1.671. Column selection (9A, DERIVED): 98 % of the J-FWD pressure stress is carried by modes with T <= 1 ms and the slow share (T > 1 ms) is 0.02, so the node is a **0.1-1 ms path: FA1D 93 bar yield +0.251 / FA1U 102 bar ultimate +0.233** apply; with the slow share at 151.04 bar the mixed-pressure margin is +0.237 / +0.223, and the slow share stays <= 0.035 (signed) / <= 0.104 (sum of magnitudes) with the frequencies scaled by 0.90 and 0.85 (9A.1; break-even 0.40 / 0.485). Lead decision CHANGELOG 223 (PROVISIONAL): FA-1 design margin +0.25 / +0.23 on the period reading; FA1S -0.221 / -0.160 stays in the tables as the bound. *Correction: the first version of this text (REPORT a9f7f30055063c8e, CHANGELOG 221) quoted FA1Q +0.291 / +0.393, which is the 90 bar T <= 0.1 ms column, by mistake (lead 223 (1)).*
5. **LC3 (8 deg stop, runaway with the rod at the 609 N stall limit, max thrust + touchdown inertia, cold):** at the L1 regular-node convention GM-02 +0.182 / +0.019 (stop045), GM-01 +0.206 / +0.039 (stop315), NZ-03 +0.194 (stop000). **Refinement of the GM-02 lever root makes it NEGATIVE: R3 -0.280 / -0.379** (435 MPa at the R1.2 lever-root fillet where it meets the collar OD; the stress 0.5 mm from the edge line is stable R2 -> R3, 420 -> 416 MPa, i.e. not a singularity). The L1 value was unconservative because the 1 mm exclusion around a flagged edge removed the 1.2 mm fillet zone (section 4.6). GM-01 (mirror): **GM-01 R3 -0.273 / -0.374** (431 MPa; 421 MPa at 0.5 mm from the edge line): the same finding for both levers.
6. **LC3 hot lower bound:** NZ-01 -0.443, TC-03 -0.357 / -0.415, TC-02 +0.022 / -0.179, GM-02 +0.128 / -0.028 (L1 convention; refined: worse, section 4.6).
7. **Airframe interface (16 x M5):** max screw shear LC1 75 N, FA1S 554 N, FA1T 643 N, LC3 889 N (rigid airframe) [SIM]; compliant airframe (k_af ASSUMED): max hole shear LC1 48 N, LC3 stop045 453 N (rigid 837 N at the same pose) - the rigid airframe bounds the hole loads; engine-part margins unchanged.
8. **F4 joints:** **J-FD01 (2 x M3 A4-70 into TC-02) NEGATIVE: -0.41 bounding / -0.20 with load factor 0.2**, driven by the specified 1.0 N m (assembly utilisation 0.94 nominal, 1.18 at +25 % scatter) and the 121 degC screw temperature; J-FD09 -0.17 bounding / +0.05 (EI 0.5 sensitivity, 10 g); others +0.04 to +0.15 bounding (all hand calcs on ASSUMED preload scatter, K and hot-strength factor).
9. **Gimbal stiffness (F3)** (rigid servo output, flexible engine and structure): 9 range-cone poses **K_alpha 6430-8364, K_beta 4082-6380 N m/rad**; 8 stop poses K_alpha 6400-8577, K_beta 3888-6570; with the ASSUMED servo output stiffness 58-174 N m/rad in series 686-2891 N m/rad over all poses [SIM / DERIVED]. Neutral 7284 / 5370; compliant airframe at stop045 -14 / -13 % (section 9).
10. **Modal (coarsened, all bodies at mesh level 2; 9A):** first engine-mount modes 51.4 Hz (rocking, inner axis) and 59.4 Hz (rocking, outer axis) with the servo output rigid, **about 48 / 56 Hz at the production-model stiffness and 21-33 Hz with the servo in series** [DERIVED]; lateral 267 / 372 Hz, axial 408 Hz; pintle linkage 186 Hz (upper bound, rigid linkage). Verified by a Rayleigh check on the same mesh (<= 1 %). A first all-L2 run had a broken collar-case bond (15 of ~2850 equations) and gave 24 / 36 Hz: a model defect, found, fixed and kept as evidence. Full-L1 and partly-L1 modals do not fit the 8 GB cap.
11. **F2, S-3D on v3.5.1 (9 range-cone poses, both lever roots refined; 9B):** GS (both servos at stall, rods +/-441 N at neutral, +/-552 N on the 7 deg cone) is **NEGATIVE at both lever roots: GM-02 -0.223 / -0.330 (alpha-, 403 MPa), GM-01 -0.209 / -0.319 (alpha+, 396 MPa)**; ultimate-negative at 9 of 9 poses, yield-negative at 7 [SIM]. Same R1.2 fillet location as the LC3 finding (4.6); the S-3D v1.1 yield margins there (GS +0.16, SR +0.05; 1.5 mm exclusion) are not conservative. Touchdown rods <= 110 N against the 609 N stall force (servos hold). All other gimbal and mount parts positive in every case (lowest GS GM-16a +0.852, TD GM-03 +3.417, LC6 GM-03 +9.320, LC2F GM-03 +4.919; min of yield and ultimate). F2 hot lower bound GM-01 -0.219 / -0.327, GM-02 -0.259 / -0.362 [DERIVED]. Routed to Mechanical as a DESIGN CHANGE item (CHANGELOG 223 (5)); not redesigned here.
12. **Mounting data (engine data for the datasheet, lead CHANGELOG 222; 8.1):** max M5 screw shear per case, rigid airframe: LC1 75 N (AF_GM09_4), FA1S 554 N (AF_GM09_0), FA1T 643 N (AF_GM09_0), LC3 889 N (AF_GM10_5), F2 GS 808 N (AF_GM10_2), TD 181 N (AF_GM09_7), LC6 81 N (AF_GM09_4), LC2F 190 N (AF_GM09_4) [SIM]; the rigid airframe bounds the hole loads (compliant LC3 stop045 453 N (AF_GM10_5)). Per-hole shear / axial / pull-out and the ring resultants of every case, K at the stop poses and the first engine-mount modes are in 8.1.

## 2. Configuration

### 2.1 Model
- Geometry: CAD v3.5.1 neutral STEP, 23 meshed bodies (engine frame mm, +Z forward, pivot at the origin): TC-01 case, TC-02 forward closure, TC-03 GlidCop seat insert, TC-04, TC-09 IN718 aft closure, NZ-01 graphite throat, NZ-02/NZ-03 carbon-phenolic, NZ-04 flexible-graphite seal, FD-01, PD-01R/PD-01S, GM-01/GM-02 (collar halves with the servo levers, 7075-T6), GM-03 ring, GM-08a/b bearing housings, GM-09/GM-10 airframe brackets, GM-13/GM-14 servo brackets, GM-16a/b horns. Boolean sliver faces defeatured with OCC (GM-01/02, TC-04; dV < 1e-4 mm3).
- Mesh: level 1 (L1) 171,123 nodes; pose runs (LC3) engine pressure parts at level 2, others L1 (133.6k nodes); local gmsh ball refinements R2 / R3 for convergence (section 5).
- Masses: model groups engine 2.880 kg (pose runs) / 2.886 kg (L1), ring 0.217 kg, fixed 0.971 kg, horns 0.029 kg [DERIVED] (massprops wet: engine 2.874, ring 0.217 [DATASHEET v3.5.1]); 1.31 kg of airframe-wall equipment is outside F1 (F4). Pc transducer **ASSUMED 26 g** (CHANGELOG 205). Solver gravity constant 9.810 m/s2 (model constant; +0.034 % vs 9.80665, conservative).

### 2.2 Interfaces (asm v1.2)
| Interface | Model | Stiffness / tag |
|---|---|---|
| Threads / inserts (TB1, TC-09/TC-01, NZ-04 lip) | tie, rule 'zt' (axial + tangential), design variant | bonded, ASSUMED |
| TB1 variant | 'thread' only (shoulder + end face free) | over-constraint check (4.2) |
| Other contacts (GM-01/02 to TC-01 bore, bolted flanges, nozzle stack) | bonded ties | ASSUMED (stiff bound) |
| Gimbal pins / seats | *RIGID BODY on pin and seat bores | ASSUMED rigid |
| HK0808 needle cups | radial bushings (2 dirs), SPRINGA **length 1e6 mm** (v1.2) between the seat reference and an auxiliary node tied to the pin reference | 128,258 / 149,912 N/mm, Palmgren line contact [DERIVED] |
| PTFE thrust washers | axial bushing, locating on +Y (inner) / +X (outer) only | 1e6 N/mm [ASSUMED] |
| Push rods | SPRINGA (v1.2: 1e6 mm, auxiliary node on the posed rod line, tied to the lever eye) between horn eye and lever eye | k_chain 11,418.2 N/mm [DERIVED, mechanical.json chain]; servo output rigid |
| J-FWD (8 radial screws TC-01/TC-02) | RBE3 bushings (3 dirs) | screw stiffness [ASSUMED], model.json |
| PD feet | RBE3 bushings | 1e4 N/mm [ASSUMED] |
| PD-02 | rigid connector | ASSUMED |
| Mass items (25 + hardware) | RBE3-distributed nodal loads | DATASHEET masses |
| Airframe 16 x M5 holes | rigid; compliant variant (SPRINGA 1e6 mm to ground) | k_af 2e3 / 2e4 / 2e4 N/mm radial / tangential / axial [ASSUMED] |

Fasteners are connectors with the stated stiffness, not meshed; stresses within about 1 mm of a connector patch are idealisation-dependent and excluded from the "regular" node set (2.4).

### 2.3 Loads
| Case | Definition | SF | Tags |
|---|---|---|---|
| **LC1** | Pc 25.01 bar on the operating pressure distribution (vacuum outside) + manifold 70 bar + 4.04 g axial + 0.61 g lateral (4 directions, envelope); thermal field mapped from S-AX at B1_21.65 / B1_19 / B1_2 / B1_1 | 1.5 yield / 2.0 ultimate at node temperature (188 (9); 183 (1)) | Pc, manifold DATASHEET (S-AX LC1); g SIM (gnc.json v3.1) |
| **FA1Q** | 90 bar abs (T <= 0.1 ms paths) + manifold 70 bar, A1_22.2 relight thermal state | 1.0 | CHANGELOG 194 |
| **FA1D / FA1U** | 93 bar yield / 102 bar ultimate (0.1 < T <= 1 ms paths) | 1.0 | CHANGELOG 194 |
| **FA1S** | 2.0 x 75.519 = 151.04 bar abs (T > 1 ms paths, DLF 2.0 bound until the modal closure) | 1.0 | CHANGELOG 194 |
| **FA1T** | 90 bar shell + unit thrust TZ scaled to 3600 N total (1.8 kN x 4 ms x DLF 2.0), gimbal / mount parts only (T <= 20 ms); TZ now solved in the same run (v1.2) | 1.0 | CHANGELOG 194 |
| **LC3** | engine at the 8 deg stop, 8 azimuths: OP x Pc_max + 6.29 g lateral (8 dirs) + axial {0, 5.43 g} + 79.28 rad/s2 (both signs, direction maximising the into-stop moment) + bumper force {0 hold, fb_run}; fb_run = largest bumper force with actuator moment <= 41.14 N m AND each rod <= 609 N; 64 sub-cases per pose; **cold**, allowables at B1_21.65 node T | 1.5 / 2.0 | g, rad/s2 SIM (gnc.json v3.1); 41.14 N m, 609 N DERIVED (mechanical.json v2.1) |
| **LC3 hot bound** | LC1 thermo-pressure field (TH + OP Pc_max + PM, no LC1 inertia) + LC3 increment, von Mises sub-additivity / Weyl | 1.5 / 2.0 | DERIVED lower bound on the margin |

Unit steps (TH, OP, PM, GX, GY, GZ, EAX, EAY, R1, R2, BUMP, TZ) superposed, linear elastic, small displacement. OP net axial 202.92 N/MPa [SIM] (S-AX 197.52 N/MPa, +2.7 %; ideal ~214 N/MPa [DERIVED]).

### 2.4 Criteria and node sets
- Metals: MS_y = Fty(T)/(SF_y vM) - 1, MS_u = Ftu(T)/(SF_u vM) - 1; allowables from materials v1 (hub 04-fea/materials) at node temperature; bay structure 60 degC [ASSUMED, TO-VERIFY].
- Brittle (graphite, carbon-phenolic): s1/St and s3/Sc with SF 2.0; char zone (T > T_char) primary s3 only; NZ-03 char strength 20 MPa [ASSUMED, CHANGELOG 212; founder test N-F1].
- Supplementary: primary-only MS and P+Q nodal shakedown MS (vM <= 2 Fty).
- Regular node set: all nodes except those within 1.0 mm of tie-patch edges, RBE3 / rigid patches, ground, re-entrant CAD edges (facet dihedral > 30 deg, concave) and tets with quality q < 0.1. **Caveat found in this release (4.6): where a small fillet (R1.2) sits next to an edge that the detector flags on a coarse mesh, the 1 mm exclusion removes the fillet zone; refinement is then required (done for the GM-01/02 lever roots).**

## 3. Per-part minimum margins (asm v1.2; all SIM; full table `tables/f1_part_margins.{md,csv,json}`, chart F1-C1)

| Part | Material | LC1 y / u (state) | FA1S y / u | FA1Q y / u | FA1T y / u | LC3 cold y / u (pose), L1 | LC3 hot bound y / u | governing |
|---|---|---|---|---|---|---|---|---|
| NZ-01 | graphite | **-0.435** (B1_1) | +1.465 | +3.400 | - | +4.151 | **-0.443** | LC1 / hot bound, throat compression |
| TC-03 | GlidCop Al-15 | **-0.312 / -0.375** (B1_1) | +2.150 / +2.819 | +4.650 / +5.850 | - | +9.224 / +8.297 | **-0.357 / -0.415** | LC1 thermal-secondary |
| TC-01 | 6061-T6 | +1.383 / +0.916 | **-0.221 / -0.160** | +0.291 / +0.393 | - | +0.830 / +0.485 (stop270) | +1.279 / +0.832 | FA1S J-FWD hole |
| TC-02 | 6061-T6 | +0.096 / **-0.119** (B1_19) | +0.855 / +1.001 | +2.118 / +2.363 | - | +5.332 / +4.091 | +0.022 / **-0.179** | LC1 thermal-secondary, T > T_limit |
| GM-02 | 7075-T6 | +17.2 / +14.7 | +3.443 / +4.105 | +6.472 / +7.585 | +4.840 / +5.709 | +0.182 / +0.019 (stop045); **R3: -0.280 / -0.379** | +0.128 / **-0.028** (L1) | LC3 lever root |
| GM-01 | 7075-T6 | +12.5 / +10.7 | +2.436 / +2.948 | +4.777 / +5.637 | +4.979 / +5.870 | +0.206 / +0.039 (stop315); **R3: -0.273 / -0.374** | +0.190 / +0.026 (L1) | LC3 lever root |
| NZ-03 | carbon-phenolic | +0.476 (B1_2) | +0.630 | +1.735 | - | **+0.194** (stop000) | +0.231 | LC3 |
| TC-04 | 6061-T6 | +1.010 / +0.634 | +3.112 / +3.448 | +3.111 / +3.446 | - | +6.476 / +5.061 | +0.558 / +0.266 | hot bound |
| TC-09 | IN718 | +1.230 / +0.934 | +1.637 / +2.144 | +2.780 / +3.508 | - | +11.9 / +10.6 | +1.123 / +0.841 | hot bound |
| NZ-02 | carbon-phenolic | +0.898 (B1_2) | +2.496 | +4.867 | - | +1.913 | +0.860 | hot bound |
| GM-16a / GM-16b | 7075-T6 | > +100 | > +37 | > +60 | +30.96 ; +107.9 | +1.100 / +0.809 ; +1.079 / +0.791 | +1.092 / +0.803 ; +1.070 / +0.783 | LC3 |
| GM-03 | 6061-T6 | +13.1 / +10.4 | +1.887 / +2.105 | +3.849 / +4.216 | **+1.483 / +1.671** | +1.368 / +0.910 | +1.365 / +0.908 | LC3 |
| PD-01S / PD-01R | 6061-T6 | +1.993 / +1.425 ; +2.599 / +1.916 | +2.698 / +2.997 ; +3.846 / +4.237 | > +4 | - | > +5 | +1.430 / +0.969 ; +1.810 / +1.277 | hot bound |
| FD-01 | 316L | +2.302 / +5.484 | +4.697 / +13.67 | +4.746 / +13.80 | - | +6.438 / +13.38 | +1.194 / +3.309 | hot bound |
| GM-13, GM-14, GM-10, GM-09, GM-08a, GM-08b | 6061-T6 | > +70 | > +13 | > +23 | > +11 | +2.881 / +2.131 ; +3.079 / +2.291 ; +3.655 / +2.756 ; +5.971 / +4.624 ; +8.178 / +6.404 ; +17.47 / +13.90 | ~ LC3 cold | LC3 |
| NZ-04 | flexible graphite | +4.658 | +4.523 | +7.348 | - | +14.82 | +4.386 | - |

FA1D / FA1U columns and the primary-only and P+Q columns are in the full table and in the margin matrix (section 3A). For TC-01: FA1D +0.251 / +0.349, FA1U +0.144 / +0.233; the 0.1-1 ms design pair is the FA1D yield and the FA1U ultimate value (lead CHANGELOG 223, PROVISIONAL; 9A.1). The asm v1.1 (interim) tables are kept in `tables_legacy_v1.1/` as evidence.

## 3A. Margin matrix: every part x every case, F1 + F2 (`tables/margin_matrix_v351.{md,json}`; cell = MS_y / MS_u, minimum over states / poses / sub-cases)

| part | material | LC1 | FA1Q | FA1D | FA1U | FA1S | FA1T | LC3 cold | LC3 hot bound (DERIVED) | LC3 lever root R3 | GS | TD | LC6 | LC2F | F2 hot bound (DERIVED) | min (case) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-01 | AL6061-T6 | +1.383 / +0.916 | +0.291 / +0.393 | +0.251 / +0.349 | +0.144 / +0.233 | -0.221 / -0.160 | - | +0.830 / +0.485 | +1.279 / +0.832 | - | +0.805 / +0.465 | +0.829 / +0.485 | +40.369 / +32.578 | - | +1.251 / +0.810 | -0.221 (FA1S y) |
| TC-02 | AL6061-T6 | +0.096 / -0.119 | +2.118 / +2.363 | +2.017 / +2.254 | +1.750 / +1.966 | +0.855 / +1.001 | - | +5.332 / +4.091 | +0.022 / -0.179 | - | +5.147 / +3.942 | +5.397 / +4.143 | >+99 / >+99 | - | +0.025 / -0.176 | -0.179 (LC3 hot bound (DERIVED) u) |
| TC-03 | GLIDCOP-AL15 | -0.312 / -0.375 | +4.650 / +5.850 | +4.438 / +5.593 | +3.888 / +4.926 | +2.150 / +2.819 | - | +9.224 / +8.297 | -0.357 / -0.415 | - | +8.959 / +8.056 | +35.082 / +31.810 | >+99 / >+99 | - | -0.352 / -0.410 | -0.415 (LC3 hot bound (DERIVED) u) |
| TC-04 | AL6061-T6 | +1.010 / +0.634 | +3.111 / +3.446 | +3.111 / +3.446 | +3.111 / +3.447 | +3.112 / +3.448 | - | +6.476 / +5.061 | +0.558 / +0.266 | - | +5.865 / +4.566 | +27.139 / +21.812 | >+99 / +83.923 | - | +0.586 / +0.289 | +0.266 (LC3 hot bound (DERIVED) u) |
| TC-09 | IN718 | +1.230 / +0.934 | +2.780 / +3.508 | +2.702 / +3.414 | +2.484 / +3.154 | +1.637 / +2.144 | - | +11.917 / +10.622 | +1.123 / +0.841 | - | +12.016 / +10.711 | +12.260 / +10.930 | >+99 / >+99 | - | +1.143 / +0.859 | +0.841 (LC3 hot bound (DERIVED) u) |
| NZ-01 | GRAPHITE-ISO | -0.435 / n/a | +3.400 / n/a | +3.263 / n/a | +2.897 / n/a | +1.465 / n/a | - | +4.151 / n/a | -0.443 / n/a | - | +3.965 / n/a | +4.673 / n/a | >+99 / n/a | - | -0.445 / n/a | -0.445 (F2 hot bound (DERIVED) y) |
| NZ-02 | CARBON-PHENOLIC | +0.898 / n/a | +4.867 / n/a | +4.678 / n/a | +4.177 / n/a | +2.496 / n/a | - | +1.913 / n/a | +0.860 / n/a | - | +1.905 / n/a | +1.994 / n/a | >+99 / n/a | - | +0.865 / n/a | +0.860 (LC3 hot bound (DERIVED) y) |
| NZ-03 | CARBON-PHENOLIC | +0.476 / n/a | +1.735 / n/a | +1.647 / n/a | +1.413 / n/a | +0.630 / n/a | - | +0.194 / n/a | +0.231 / n/a | - | +0.205 / n/a | +0.206 / n/a | +71.573 / n/a | - | +0.259 / n/a | +0.194 (LC3 cold y) |
| NZ-04 | FLEX-GRAPHITE-OI | +4.658 / n/a | +7.348 / n/a | +7.146 / n/a | +6.594 / n/a | +4.523 / n/a | - | +14.824 / n/a | +4.386 / n/a | - | +15.018 / n/a | +15.097 / n/a | >+99 / n/a | - | +4.384 / n/a | +4.384 (F2 hot bound (DERIVED) y) |
| FD-01 | SS316L | +2.302 / +5.484 | +4.746 / +13.799 | +4.743 / +13.793 | +4.736 / +13.774 | +4.697 / +13.674 | - | +6.438 / +13.380 | +1.194 / +3.309 | - | +5.837 / +12.218 | +27.453 / +54.009 | +66.136 / >+99 | - | +1.240 / +3.400 | +1.194 (LC3 hot bound (DERIVED) y) |
| GM-01 | AL7075-T6 | +12.545 / +10.672 | +4.777 / +5.637 | +4.590 / +5.422 | +4.095 / +4.853 | +2.436 / +2.948 | +4.979 / +5.870 | +0.206 / +0.039 | +0.190 / +0.026 | -0.273 / -0.374 | -0.209 / -0.319 | +3.710 / +3.058 | +29.530 / +25.307 | +8.871 / +6.561 | -0.219 / -0.327 | -0.374 (LC3 lever root R3 u) |
| GM-02 | AL7075-T6 | +17.239 / +14.716 | +6.472 / +7.585 | +6.230 / +7.307 | +5.589 / +6.570 | +3.443 / +4.105 | +4.840 / +5.709 | +0.182 / +0.019 | +0.128 / -0.028 | -0.280 / -0.379 | -0.223 / -0.330 | +3.961 / +3.275 | +45.191 / +38.803 | +7.605 / +5.591 | -0.259 / -0.362 | -0.379 (LC3 lever root R3 u) |
| GM-03 | AL6061-T6 | +13.115 / +10.388 | +3.849 / +4.216 | +3.692 / +4.047 | +3.277 / +3.601 | +1.887 / +2.105 | +1.483 / +1.671 | +1.368 / +0.910 | +1.365 / +0.908 | - | +2.042 / +1.454 | +4.475 / +3.417 | +11.792 / +9.320 | +7.254 / +4.919 | +2.035 / +1.449 | +0.908 (LC3 hot bound (DERIVED) u) |
| GM-08a | AL6061-T6 | +73.873 / +59.404 | +25.125 / +27.102 | +24.278 / +26.190 | +22.036 / +23.779 | +14.532 / +15.707 | +12.358 / +13.369 | +8.178 / +6.404 | +8.163 / +6.392 | - | +15.264 / +12.121 | +20.174 / +16.082 | +50.340 / +40.419 | +36.077 / +25.588 | +15.177 / +12.050 | +6.392 (LC3 hot bound (DERIVED) u) |
| GM-08b | AL6061-T6 | +84.367 / +67.870 | +28.968 / +31.236 | +28.006 / +30.201 | +25.457 / +27.459 | +16.891 / +18.245 | +14.399 / +15.564 | +17.471 / +13.902 | +17.378 / +13.826 | - | +17.277 / +13.745 | +33.373 / +26.731 | +77.517 / +62.343 | +49.016 / +34.867 | +17.186 / +13.671 | +13.671 (F2 hot bound (DERIVED) u) |
| GM-09 | AL6061-T6 | +72.199 / +58.053 | +23.593 / +25.454 | +22.801 / +24.602 | +20.706 / +22.348 | +13.668 / +14.778 | +11.623 / +12.578 | +5.971 / +4.624 | +5.964 / +4.618 | - | +15.323 / +12.168 | +17.152 / +13.644 | +54.453 / +43.737 | +44.253 / +31.452 | +15.273 / +12.129 | +4.618 (LC3 hot bound (DERIVED) u) |
| GM-10 | AL6061-T6 | >+99 / >+99 | +59.527 / +64.107 | +57.568 / +62.000 | +52.386 / +56.426 | +35.020 / +37.746 | +29.746 / +32.072 | +3.655 / +2.756 | +3.636 / +2.740 | - | +3.618 / +2.725 | +24.304 / +19.414 | +99.929 / +80.424 | +81.040 / +57.832 | +3.599 / +2.710 | +2.710 (F2 hot bound (DERIVED) u) |
| GM-13 | AL6061-T6 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | +99.762 / >+99 | +68.905 / +74.194 | +57.376 / +61.793 | +2.881 / +2.131 | +2.861 / +2.115 | - | +2.907 / +2.152 | +23.379 / +18.668 | +88.706 / +71.370 | >+99 / >+99 | +2.887 / +2.136 | +2.115 (LC3 hot bound (DERIVED) u) |
| GM-14 | AL6061-T6 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | +3.079 / +2.291 | +3.062 / +2.277 | - | +3.211 / +2.397 | +21.857 / +17.440 | >+99 / >+99 | +71.218 / +50.788 | +3.193 / +2.383 | +2.277 (LC3 hot bound (DERIVED) u) |
| GM-16a | AL7075-T6 | >+99 / >+99 | +60.822 / +70.030 | +59.012 / +67.950 | +54.164 / +62.380 | +37.306 / +43.011 | +30.957 / +35.716 | +1.100 / +0.809 | +1.092 / +0.803 | - | +1.149 / +0.852 | +13.662 / +11.634 | +67.573 / +58.089 | >+99 / >+99 | +1.138 / +0.842 | +0.803 (LC3 hot bound (DERIVED) u) |
| GM-16b | AL7075-T6 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | >+99 / >+99 | +1.079 / +0.791 | +1.070 / +0.783 | - | +1.158 / +0.859 | +10.988 / +9.330 | >+99 / +90.867 | +35.648 / +27.071 | +1.148 / +0.851 | +0.783 (LC3 hot bound (DERIVED) u) |
| PD-01R | AL6061-T6 | +2.599 / +1.916 | +5.398 / +5.915 | +5.401 / +5.918 | +5.325 / +5.836 | +3.846 / +4.237 | - | +5.296 / +4.101 | +1.810 / +1.277 | - | +3.067 / +2.295 | +4.957 / +3.827 | +25.571 / +20.528 | - | +1.259 / +0.830 | +0.830 (F2 hot bound (DERIVED) u) |
| PD-01S | AL6061-T6 | +1.993 / +1.425 | +4.273 / +4.699 | +4.273 / +4.699 | +4.273 / +4.699 | +2.698 / +2.997 | - | +5.864 / +4.561 | +1.430 / +0.969 | - | +3.636 / +2.757 | +5.522 / +4.284 | +21.487 / +17.219 | - | +1.030 / +0.644 | +0.644 (F2 hot bound (DERIVED) u) |

FA-1 columns (lead CHANGELOG 194, SF 1.0): FA1Q 90 bar abs (T <= 0.1 ms), FA1D 93 bar yield / FA1U 102 bar ultimate (0.1 < T <= 1 ms; the governing pair is the FA1D yield and the FA1U ultimate value, the other halves are shown for completeness), FA1S 151.04 bar abs bound (T > 1 ms, 2 x 75.519, DLF 2.0), FA1T thrust spike 3.6 kN. The 'min' column is the plain minimum over every column, FA1S included: for TC-01 the lead's PROVISIONAL decision (CHANGELOG 223 (3)) classes J-FWD as a 0.1-1 ms path (design margin FA1D +0.251 / FA1U +0.233), FA1S stays as the bound; mixed-share check and the 0.85 / 0.90 frequency sensitivity in REPORT-FEA3D 9A.1 (results/fa1_band_sensitivity.json).

Conventions: regular node set (idealisation singularities excluded, REPORT-FEA3D 2.4); SF 1.5 / 2.0 except FA-1 (1.0) and LC2F (1.0 / 1.5); brittle parts (graphite, carbon-phenolic) on principal stress (s1 / St, s3 / Sc) with the case ultimate SF (2.0; 1.0 in FA-1), one value in the yield slot, n/a in the ultimate slot. LC3 cold / hot bound for GM-01 / GM-02 are at the L1 convention, which is UNCONSERVATIVE at the lever root (REPORT-FEA3D 4.6): the refined value is the 'LC3 lever root R3' column. GS / TD / LC6 / LC2F (F2, 9 cone poses) carry both lever roots at R3 inside the regular set. 'F2 hot bound' = LC1 thermo-pressure field + the F2 cone-pose increment (GS + TD + LC6) by sub-additivity (node-wise for TC-01; part maximum for the lever-root-refined collars and the coarser engine pressure parts) - a lower bound on the hot margin. The engine pressure parts are at mesh level 2 in the pose runs (LC3, F2).

## 4. Governing findings (decision 212 terms)

**4.1 TC-02 (forward closure, 6061-T6).** L1 +0.096 y / -0.119 u at B1_19, at the TB1 tie end (r 5.86, z 107.51), 159 degC; vM 102.4 MPa of which 100.8 MPa thermal -> secondary (primary-only +3.44; P+Q 2Fty +2.29). The part reaches 159 degC against its 150 degC limit [SIM vs DATASHEET limit]: check (d) stays **open** (CHANGELOG 212: T-F1 sourced short-time allowables + T-F2 contact FE). Refinement moves the regular-set maximum away from the tie end (R2 +0.213 / -0.040, R3 +0.469 / +0.165); the all-node value at the tie end grows (102 -> 147 -> 143 MPa) = tie-termination singularity. 'thread' TB1 variant +0.196 / -0.054. **No converged TC-02 ultimate margin is claimed**: between -0.12 and +0.17 on total stress depending on the tie-end idealisation; the decision rests on T-F2.

**4.2 TC-03 (GlidCop seat insert).** L1 -0.312 / -0.375 at B1_1, flange corner r 9.8 / z 105.51, 74 degC; vM 241 MPa, 237 MPa of it thermal. R2 -0.266 (226 MPa), R3 -0.342 (252 MPa): oscillating, not asymptotic. Thread-only TB1 tie: -0.259 / -0.327 at the same corner (over-constraint hypothesis refuted). Primary-only +7.3; P+Q shakedown +1.06 (L1) to +1.22 (refined). Negative on total stress, positive on primary and on P+Q [SIM]; whether S-AX's +1.203 is the same shakedown criterion is TO-VERIFY with Mechanical.

**4.3 NZ-01 (graphite throat).** -0.435 at B1_1 (S-AX -0.443); s3 -69 MPa at 1330 degC, thermal-dominated; refinement makes it worse (R2 -0.454, R3 -0.481; growth 3.5 % then 5.1 %, not asymptotic). A primary design question (brittle, SF 2.0 on total stress) for Mechanical / Combustion; refinement will not remove it.

**4.4 NZ-03 (carbon-phenolic retainer).** LC1 +0.476 (B1_2), FA1S +0.630, LC3 +0.194 to +0.206 at all stop poses [SIM], on the **ASSUMED 20 MPa char compressive strength** (CHANGELOG 212); founder test N-F1 closes it.

**4.5 TC-01 (case) under FA1S.** -0.221 / -0.160 at the J-FWD radial screw hole (r 28.6, z 125.5), 46 degC; regular-set vM 303.0 / 302.6 / 295.9 MPa at L1 / R2 / R3 (h 3.0 / 1.3 / 0.7 mm): converged within 2.4 %, R3 -0.202 / -0.140; the all-node value at the RBE3 patch edge grows (357 -> 382 -> 399 MPa, idealisation). J-FWD screws carry 4.85 kN shear each [SIM] = pi x 28.6^2 x 15.10 MPa / 8 [DERIVED]. FA1Q / FA1D / FA1U positive (FA1Q +0.291 / +0.393; FA1D +0.251 yield; FA1U +0.233 ultimate). Modal (9A / 9A.1): the J-FWD stress is a 0.1-1 ms path (slow share 0.02; <= 0.035 signed / 0.104 magnitude-sum at f x 0.85-0.90), so FA1D / FA1U (+0.251 / +0.233) apply on the line-194 reading (lead 223, PROVISIONAL); FA1S stays as the bound. J-FWD screw shear / hole bearing vs a fastener datasheet: TO-VERIFY (Mechanical).

**4.6 GM-01 / GM-02 lever roots (LC3 runaway, rod at 609 N).** L1 regular: GM-02 +0.182 / +0.019 (stop045), GM-01 +0.206 / +0.039 (stop315), peak at r 33.7 / z -6.9 (posed). The all-node maximum there was 459 MPa (MS -0.32 / -0.41) next to sliver tets. Refinement balls at the GM-02 lever root (R2 h 0.60 mm, R3 h 0.34 mm; `pose_stop045_gm02r2/r3_c71`):

| level | h (mm) | regular-set MS y / u | vM at the peak node (MPa) | max vM within 3 mm, > 0.5 mm from the R2 edge line | same, > 1.0 mm |
|---|---|---|---|---|---|
| L1 | 1.46 | +0.182 / +0.019 (265 MPa, 1.06 mm from the edge) | 414 (excluded) | 459 (bad tets) | 265 |
| R2 | 0.60 | +0.139 / -0.018 (275 MPa) | 420 (excluded) | 420 | 275 |
| R3 | 0.34 | **-0.280 / -0.379** (435 MPa) | 435 (regular) | 416 | 297 |

CAD check (defeatured BREP of GM-02, faces at the peak): the R1.2 mm cylindrical lever-root fillet and an R0.5 mm toroidal edge fillet meet the R32.5 mm collar OD along B-spline intersection edges; the surface normal turns by ~92 deg within 0.3 mm at every level (a sharp intersection edge next to the fillet). The edge detector flags it as re-entrant on L1 and R2 but not on R3, which is why the regular-set value jumps. The stress 0.5 mm from that edge line is **stable under refinement (420 -> 416 MPa)**, so it is a finite fillet-zone concentration, not a singularity; the 1 mm exclusion at L1 / R2 removed the fillet zone and was **unconservative**. Result: **GM-02 lever root under the LC3 runaway (cold) MS_y about -0.25 to -0.28, MS_u about -0.35 to -0.38** [SIM, R2/R3]; the hot increment adds about +14 MPa at L1 (hot bound +0.128 vs cold +0.182) [DERIVED], making it slightly worse. GM-01 (mirror lever, stop315, R3 ball h 0.34 mm, `pose_stop315_gm01r3_c71`): regular set -0.273 / -0.374 (431 MPa), 421 MPa at 0.5 mm from the edge line, L1 all-node 460 MPa - the same finding for both levers (`results/f1_lever_root_GM0{1,2}_c71.json`, figure F1-09). What this means for the design (Mechanical owns it): the lever root of the 7075-T6 collar halves does not carry the 609 N stall-limited rod force with SF 1.5 / 2.0 in the bounding LC3 combination; options are a larger lever-root fillet / thicker root, a lower stall-limited rod force, or a lower design combination (the LC3 combination of max thrust + touchdown inertia + runaway is bounding by construction). The sharp fillet-to-collar intersection edge itself (zero-radius edge in CAD) should be blended. **F2 adds the servo-stall case GS at the same location (9B): GM-02 -0.223 / -0.330, GM-01 -0.209 / -0.319 with the rods at +/-552 N (no stop contact)**, so a lower design combination for LC3 alone would not clear the lever root.

## 5. Mesh convergence

`results/f1_convergence.json` (chart F1-C3), LC1-core / FA1S-core combinations, same thermal map, ties and loads at every level; quantity = maximum over regular nodes within 3 mm of the governing point. Study solved on asm v1.1; the v1.2 fix changes engine-part stresses by <= 0.15 % (`results/cmp_f1_post_lc1v351_c71.json`), so it stays representative. Lever roots: section 4.6 (v1.2).

| Point | Quantity | L1 (h mm) | R2 (h mm) | R3 (h mm) | MS L1 / R2 / R3 |
|---|---|---|---|---|---|
| NZ-01 throat, B1_1 | -s3 | 69.0 (3.63) | 71.4 (0.72) | 75.1 (0.40) | -0.435 / -0.454 / -0.481 |
| TC-03 flange corner, B1_1 | vM | 241.2 (0.98) | 225.9 (0.33) | 252.3 (0.21) | -0.312 / -0.266 / -0.342 |
| TC-02 TB1 tie end, B1_19 | vM | 102.4 (4.84) | 102.1 (1.21) | 83.0 (0.43) | +0.096 / +0.213 / +0.469 (u -0.119 / -0.040 / +0.165) |
| TC-01 J-FWD hole, FA1S | vM | 303.0 (3.04) | 302.6 (1.28) | 295.9 (0.68) | -0.221 / -0.220 / -0.202 (u -0.160 / -0.159 / -0.140) |

Richardson / GCI is **not** quoted: NZ-01 and TC-03 are non-monotone or not asymptotic; TC-02 and TC-01 give observed orders 6.2 / 7.1, far above the formal order of C3D10 (~2). Level-to-level changes are the honest statement.

Hand-calculation cross-check (TC-01 mid-section z -60 mm, LC1 B1_21.65): FE membrane vM 20.29-20.36 MPa over 8 azimuths [SIM] vs Lame mean hoop 22.51 MPa + axial 9.87 MPa + radial -p/2 -> 20.59 MPa [DERIVED]; FE 1.3 % below.

## 6. LC3 detail (8 stop poses, cold, asm v1.2; `tables/f1_lc3_summary_c71.md`, `results/f1_post_lc3_pose_stopXXX_c71.json`)

| pose | fb_run N | max rod abs N (- compr / + tens) | lowest regular MS y / u (part) | inner cup / washer N | outer cup / washer N | max hole shear N | moment residual |
|---|---|---|---|---|---|---|---|
| stop000 | 382-479 | -493.5 (ROD_1) | NZ-03 +0.194 / nan; GM-01 +0.594 / +0.374; GM-02 +0.644 / +0.417 | 733 / 179 | 702 / 662 | 686 (AF_GM10_2) | 2.8 % |
| stop045 | 323-418 | -609.0 (ROD_2) | GM-02 +0.182 / +0.019; NZ-03 +0.200 / nan; TC-01 +0.832 / +0.487 | 560 / 442 | 543 / 505 | 837 (AF_GM10_5) | 2.9 % |
| stop090 | 384-478 | +598.3 (ROD_1) | NZ-03 +0.206 / nan; GM-02 +0.263 / +0.088; GM-01 +0.810 / +0.560 | 253 / 723 | 388 / 192 | 841 (AF_GM10_2) | 2.6 % |
| stop135 | 223-322 | +609.0 (ROD_1) | NZ-03 +0.206 / nan; TC-01 +0.869 / +0.516; GM-01 +0.999 / +0.723 | 294 / 557 | 299 / 513 | 882 (AF_GM10_2) | 3.7 % |
| stop180 | 317-416 | +609.0 (ROD_2) | NZ-03 +0.201 / nan; GM-02 +0.643 / +0.416; GM-01 +0.763 / +0.519 | 450 / 178 | 455 / 795 | 889 (AF_GM10_5) | 5.2 % |
| stop225 | 213-310 | +609.0 (ROD_2) | NZ-03 +0.206 / nan; TC-01 +0.865 / +0.513; GM-02 +0.941 / +0.672 | 294 / 545 | 291 / 503 | 881 (AF_GM10_5) | 4.0 % |
| stop270 | 365-459 | +596.9 (ROD_2) | NZ-03 +0.206 / nan; GM-01 +0.285 / +0.107; GM-02 +0.767 / +0.523 | 254 / 703 | 378 / 192 | 839 (AF_GM10_5) | 2.6 % |
| stop315 | 307-404 | -609.0 (ROD_1) | NZ-03 +0.206 / nan; GM-01 +0.206 / +0.039; TC-01 +0.837 / +0.491 | 549 / 435 | 533 / 497 | 838 (AF_GM10_2) | 2.8 % |

Rod forces are max |F| over the 64 sub-cases (sign: - compression, + tension); the 609 N stall limit is reached in compression or tension depending on the pose. "Moment residual" = |rods' reaction moment + bumper moment| / bumper moment in the BUMP unit step (7.2). Bearing loads are max |component| of one bushing direction over the sub-cases [SIM]; they replace the v1.1 values. HK0808 C0 / PTFE washer limits: no datasheet value in the hub - **TO-VERIFY** (no value invented).

Compliant airframe at stop045 (`pose_stop045_compliant_c71`): fb_run 324-419 N, rod 2 at 609 N, GM-02 +0.181 / +0.018 (rigid +0.182 / +0.019), NZ-03 +0.200, max hole shear 453 N (rigid 837 N), moment residual 3.3 % [SIM].

## 7. Connector defect 7.1 (CLOSED) and residual observation 7.2 (OPEN)

### 7.1 Inner-gimbal bushings on rigid-body references - root cause, fix, verification
- **Symptom (interim):** in unit steps of the v1.1 model the inner bushings carried 56-79 % of the engine load (GX/GZ), TH gave -4.2 N.
- **Root cause [SIM, test models `tests/conn71/`]:** CalculiX 2.21 SPRINGA elements evaluate length and direction on the current (deformed) geometry also in linear *STATIC steps, and the previous step's displacement (here the thermal step) is the reference state of the next one. With the 1 mm auxiliary springs of v1.1, transverse relative displacements of order 0.01-0.1 mm rotate the spring axis by up to several degrees and add du^2/(2L) terms, so a large part of the force leaves the intended direction. *RIGID BODY is not the cause (a linear *EQUATION rigid gives identical numbers). Test: a 2-node spring model after an 800 K pre-step closes 99.93 % with 1e6 mm springs and is garbage with 1 mm springs.
- **Fix (asm v1.2):** SPRINGA length 1e6 mm (`asm_build.SPRING_OFF_MM`) for the bearing / washer bushings, the ground springs of the compliant airframe and the rods (auxiliary node on the posed rod line, tied to the lever eye).
- **Verification (`results/fbd_*.json`, `scripts/check_fbd.py`):** engine free body, sum of inner-bearing + inner-washer + rod forces vs the load applied to the engine, every unit step: LC1 neutral (TH, OP, PM, GX, GY, GZ) and stop045 (OP, GX, GY, GZ, EAX, EAY, R1, R2, BUMP) **residual <= 0.006 N, closure 100.00 %** (v1.1: 5.9-8.1 N); ring free body residual <= 0.005 N. With R1/R2 the rod absorbs 99.38 / 99.47 % of its unit pair (the rest flows through the structure in parallel, as it should).
- **Also explained:** *RIGID BODY reference nodes that belong to no element are not written to the .frd (zero in the fields) - this was the interim's "seat reference nodes report zero displacement"; the stiffness and modal scripts now take rod elongation at the spring's auxiliary node.
- **Re-solves (deck changed):** `lc1v351_c71` (4 states), `pose_stop000..315_c71` (8), `fa1_c71` (TZ in the same run). Effects (`results/cmp_*.json`): engine parts <= 0.15 % (TC-01 J-FWD -0.15 %), ICD < 0.3 %, gimbal parts <= 1.8 % (high-margin ones), LC3 margins and the LC3 hot bound unchanged to the third decimal. Bearing loads: LC1 inner cups 199.8 / 199.8 N, outer 195.4 / 195.6 N, washers 17.3 / 18.6 N; FA1S 1517 N per cup; **FA1T 1764 N per cup, washers 0** (v1.1: 4036 N and 1766 N on the inner cups, 440 N on the inner washer - an artefact).

### 7.2 Moment closure 97-99.5 % (OPEN observation, bounded)
Forces close exactly, the moment of the connector forces on the engine about the pivot closes to 99.39 / 99.46 % for R1 / R2, **97.13 % for BUMP** at stop045 (applied moment checked against the deck's nodal loads: 70.87 N mm per N about X and Y), and the g steps at LC1 neutral leave +12 / +7 / +28 N mm per g about the inner axis (GX / GY / GZ; for GY the applied moment about that axis is zero by construction, so at least 7 N mm/g is real); CG fit residual 22.7 N mm (LC1), 7.2 N mm (stop045). The same numbers appear in v1.1 and v1.2, so this is not the SPRINGA effect. Checked without finding the path: 15 *RIGID BODY cards with unique ROT nodes referenced nowhere else; no *TIE / *CONTACT cards; only 21 *EQUATION cards tie the engine group to other groups (all connector auxiliary ties). **Impact [DERIVED]:** (a) the LC3 moment residual column (2.6-5.2 %) is the same effect: the FE rods react 95-97 % of the bumper moment, so fb_run is 3-5 % higher than with full closure (conservative for the bumper-side load path; rod forces are capped at 609 N by construction); (b) the g-step leak at the touchdown accelerations is <= ~6 N of rod force (<= 1 % of 609 N). Not resolved; reported as found.

### 7.3 Other unknowns
Thermal map: non-S-AX parts at 60 degC bay [ASSUMED]; LC3 runs are cold and the hot bound is a lower bound. Interface stiffness values marked ASSUMED in 2.2. No datasheet values for HK0808 C0 / C, M5 / J-FWD screw allowables or PTFE washer limits. NZ-03 char strength 20 MPa ASSUMED. TC-02 short-time allowables above 150 degC (T-F1). Pc transducer 26 g ASSUMED.

## 8. Mounting interface to the airframe (16 x M5), rigid and compliant airframe (`tables/f1_icd_airframe.{md,json}`, chart F1-C2)

Screws are radial through the airframe wall: shear = hypot(tangential, axial Z); pull-out = radial outward [SIM].

| Case | max screw shear N (hole) | max radial pull-out N (hole) | max push-in N | max |axial| N | sum F on airframe N (max |Fx|, |Fy|, |Fz|) |
|---|---|---|---|---|---|
| LC1_rigid | 75.2 (AF_GM09_4) | 19.8 (AF_GM09_0) | 8.2 (AF_GM10_7) | 68.1 (AF_GM09_4) | 24.5, 24.5, 345.0 |
| LC1_compliant | 48.0 (AF_GM10_3) | 1.2 (AF_GM09_0) | 0.6 (AF_GM09_7) | 47.9 (AF_GM10_3) | 24.6, 24.6, 344.9 |
| FA1S_rigid | 553.6 (AF_GM09_0) | 101.3 (AF_GM09_0) | 53.1 (AF_GM10_7) | 509.3 (AF_GM09_4) | 0.0, 0.0, 3064.9 |
| FA1T_rigid | 643.2 (AF_GM09_0) | 117.7 (AF_GM09_0) | 62.2 (AF_GM10_7) | 591.8 (AF_GM09_4) | 0.0, 0.0, 3600.0 |
| LC3_rigid_8poses | 889.4 (AF_GM10_5) | 281.1 (AF_GM09_7) | 310.7 (AF_GM09_0) | 889.0 (AF_GM10_5) | 323.2, 323.0, 500.7 |
| LC3_compliant_stop045 | 453.5 (AF_GM10_5) | 25.4 (AF_GM09_0) | 15.4 (AF_GM09_5) | 450.1 (AF_GM10_5) | 302.6, 302.6, 500.4 |

Rigid vs compliant airframe (k_af 2e3 / 2e4 / 2e4 N/mm radial / tangential / axial, ASSUMED): the compliant ring of springs spreads the load (LC1 max hole shear 75 -> 48 N; LC3 stop045 837 -> 453 N; pull-out 247 -> 25 N at stop045) and leaves the totals unchanged; **the rigid airframe is the bounding case for the hole loads**. The engine-part margins do not change (<= 0.005); frame-part margins drop (e.g. GM-09 LC1 +72.2 -> +36.0, GM-10 +192.5 -> +70.8) but stay large; GM-02 at stop045 +0.181 / +0.018 compliant vs +0.182 / +0.019 rigid [SIM].

Long-period thrust spectrum for the mounting data (CHANGELOG 194), linear scaling of the FA1T hole envelope with net thrust [DERIVED]: 1.76 kN @ 25 ms -> 314 N max hole shear; 1.45 kN @ 40 ms -> 259 N; 1.04 kN @ 100 ms -> 186 N.

### 8.1 Engine mounting data for the datasheet (lead CHANGELOG 222; `tables/engine_mount_data_v351.md`, `results/engine_mount_data_v351.json`)

ICD-AIRFRAME v2.1 was removed from the finish scope (CHANGELOG 222); `tables/icd_airframe_v21.md` and `results/icd_airframe_v21_fea3d.json` stay as published (sha16 `cedcfab909095d85` / `7b0b466eced574c0`, not rewritten). The same data, extended with the F2 cases, are kept here as engine data. Forces are those of the engine module ON its mount (the airframe), from the solved unit-step reactions at the 16 hole node sets recombined with every sub-case of each case [SIM, asm v1.2]; envelopes per case (maximum over the sub-cases and poses of that case); rigid airframe unless marked compliant (k_af ASSUMED).

Engine mounting data (datasheet; CAD v3.5.1, fea3d-asm v1.2, SIM unless tagged). 16 radial M5 holes: GM-09 forward ring z +27 mm, GM-10 aft ring z -94.8 mm.

Per-hole envelopes, N (shear in the radial M5 screw / max |axial| / max pull-out); forces of the engine module ON its mount; SIM asm v1.2.

| hole (x, y, z mm) | LC1 [rigid] | LC1 [compliant] | FA1Q [rigid] | FA1S [rigid] | FA1T [rigid] | LC3 (8 stop poses, runaway / hold) [rigid] | LC3 stop045 [compliant] | F2 GS servo stall (9 cone poses) [rigid] | F2 TD touchdown Pc 0 [rigid] | F2 TD touchdown Pc max [rigid] | F2 LC6 hard landing 10 g [rigid] | F2 LC2F stuck pintle [rigid] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AF_GM09_0 (59.4, 24.6, 27.0) | 75 / 68 / 20 | 47 / 47 / 1 | 330 / 304 / 61 | 554 / 509 / 101 | 643 / 591 / 118 | 305 / 302 / 281 | 160 / 157 / 25 | 332 / 298 / 90 | 112 / 93 / 92 | 181 / 152 / 122 | 79 / 69 / 44 | 187 / 168 / 76 |
| AF_GM09_1 (24.6, 59.4, 27.0) | 3 / 3 / 0 | 5 / 1 / 1 | 10 / 9 / 0 | 16 / 14 / 0 | 19 / 17 / 0 | 20 / 15 / 20 | 102 / 6 / 6 | 10 / 9 / 5 | 6 / 4 / 6 | 9 / 7 / 7 | 3 / 2 / 2 | 7 / 6 / 3 |
| AF_GM09_2 (-24.6, 59.4, 27.0) | 3 / 3 / 0 | 2 / 1 / 0 | 10 / 9 / 0 | 17 / 15 / 0 | 20 / 17 / 0 | 9 / 7 / 3 | 72 / 4 / 5 | 9 / 9 / 1 | 2 / 2 / 2 | 4 / 4 / 2 | 1 / 1 / 1 | 5 / 5 / 0 |
| AF_GM09_3 (-59.4, 24.6, 27.0) | 71 / 64 / 14 | 46 / 46 / 0 | 319 / 294 / 58 | 537 / 495 / 97 | 624 / 576 / 113 | 324 / 269 / 95 | 140 / 105 / 5 | 336 / 300 / 74 | 118 / 95 / 31 | 173 / 145 / 47 | 79 / 68 / 20 | 185 / 164 / 42 |
| AF_GM09_4 (-59.4, -24.6, 27.0) | 75 / 68 / 15 | 47 / 47 / 1 | 329 / 304 / 59 | 552 / 509 / 98 | 641 / 592 / 114 | 328 / 276 / 96 | 127 / 114 / 2 | 347 / 309 / 75 | 122 / 98 / 32 | 178 / 150 / 48 | 81 / 70 / 20 | 190 / 169 / 42 |
| AF_GM09_5 (-24.6, -59.4, 27.0) | 3 / 3 / 0 | 2 / 1 / 1 | 10 / 9 / 0 | 17 / 15 / 0 | 19 / 17 / 0 | 9 / 9 / 3 | 36 / 4 / 4 | 10 / 9 / 1 | 4 / 3 / 2 | 6 / 6 / 2 | 2 / 2 / 1 | 5 / 5 / 0 |
| AF_GM09_6 (24.6, -59.4, 27.0) | 6 / 6 / 0 | 5 / 2 / 0 | 9 / 8 / 0 | 16 / 14 / 0 | 18 / 16 / 0 | 27 / 19 / 22 | 140 / 16 / 3 | 14 / 12 / 6 | 14 / 9 / 9 | 17 / 11 / 10 | 10 / 9 / 4 | 10 / 9 / 3 |
| AF_GM09_7 (59.4, -24.6, 27.0) | 72 / 65 / 19 | 46 / 46 / 1 | 327 / 301 / 59 | 550 / 506 / 100 | 639 / 589 / 116 | 300 / 299 / 281 | 194 / 137 / 18 | 328 / 295 / 89 | 113 / 94 / 92 | 181 / 152 / 122 | 80 / 71 / 44 | 187 / 166 / 75 |
| AF_GM10_0 (53.1, 22.0, -94.8) | 37 / 34 / 0 | 47 / 47 / 0 | 174 / 166 / 0 | 293 / 278 / 0 | 341 / 324 / 0 | 128 / 113 / 167 | 113 / 112 / 3 | 160 / 147 / 22 | 49 / 47 / 27 | 82 / 78 / 24 | 41 / 39 / 15 | 94 / 89 / 0 |
| AF_GM10_1 (22.0, 53.1, -94.8) | 7 / 6 / 2 | 5 / 5 / 0 | 18 / 18 / 4 | 29 / 29 / 6 | 35 / 35 / 7 | 321 / 300 / 165 | 23 / 11 / 2 | 284 / 274 / 83 | 46 / 42 / 17 | 50 / 46 / 19 | 8 / 4 / 4 | 9 / 9 / 4 |
| AF_GM10_2 (-22.0, 53.1, -94.8) | 4 / 4 / 1 | 3 / 2 / 0 | 34 / 34 / 0 | 55 / 54 / 0 | 66 / 66 / 0 | 882 / 879 / 205 | 54 / 19 / 2 | 808 / 807 / 98 | 137 / 137 / 25 | 130 / 130 / 23 | 40 / 39 / 8 | 17 / 17 / 0 |
| AF_GM10_3 (-53.1, 22.0, -94.8) | 37 / 36 / 0 | 48 / 48 / 0 | 175 / 168 / 0 | 293 / 282 / 0 | 341 / 328 / 0 | 192 / 158 / 201 | 149 / 112 / 1 | 161 / 155 / 29 | 48 / 44 / 14 | 75 / 70 / 8 | 39 / 37 / 8 | 92 / 88 / 0 |
| AF_GM10_4 (-53.1, -22.0, -94.8) | 37 / 35 / 0 | 45 / 45 / 0 | 175 / 168 / 0 | 294 / 283 / 0 | 343 / 330 / 0 | 192 / 160 / 197 | 84 / 82 / 15 | 162 / 156 / 34 | 49 / 45 / 15 | 77 / 73 / 9 | 40 / 38 / 8 | 94 / 90 / 0 |
| AF_GM10_5 (-22.0, -53.1, -94.8) | 20 / 20 / 1 | 11 / 11 / 0 | 22 / 21 / 0 | 35 / 35 / 0 | 10 / 10 / 0 | 889 / 889 / 227 | 453 / 450 / 14 | 807 / 807 / 108 | 131 / 131 / 26 | 157 / 157 / 20 | 30 / 29 / 8 | 74 / 74 / 1 |
| AF_GM10_6 (22.0, -53.1, -94.8) | 1 / 1 / 1 | 3 / 3 / 0 | 5 / 1 / 0 | 8 / 2 / 1 | 19 / 18 / 4 | 323 / 312 / 176 | 123 / 86 / 2 | 281 / 275 / 81 | 46 / 43 / 17 | 62 / 58 / 22 | 10 / 7 / 3 | 30 / 30 / 9 |
| AF_GM10_7 (53.1, -22.0, -94.8) | 36 / 34 / 0 | 47 / 47 / 0 | 171 / 162 / 0 | 287 / 272 / 0 | 334 / 316 / 0 | 124 / 108 / 168 | 162 / 160 / 2 | 158 / 145 / 21 | 51 / 48 / 27 | 83 / 80 / 23 | 41 / 39 / 15 | 93 / 89 / 0 |

Ring resultants (engine module ON airframe), envelope over the sub-cases: max |Fx|, |Fy|, |Fz| N ; max lateral |F| N ; max |M| about the pivot N m (x, y, z).

| case | airframe | GM-09 ring (z +27) F | GM-09 lat | GM-09 M | GM-10 ring (z -94.8) F | GM-10 lat | GM-10 M | total F | total M |
|---|---|---|---|---|---|---|---|---|---|
| LC1 | rigid | 18, 18, 241 | 18 | 0.33, 0.36, 0.34 | 7, 7, 110 | 7 | 1.16, 0.74, 0.05 | 25, 25, 345 | 1.15, 0.38, 0.40 |
| LC1 | compliant | 17, 17, 181 | 17 | 0.45, 0.46, 0.33 | 8, 9, 165 | 9 | 1.06, 0.78, 0.04 | 25, 25, 345 | 0.78, 0.44, 0.36 |
| FA1Q | rigid | 1, 1, 1168 | 1 | 0.14, 0.38, 0.44 | 1, 1, 658 | 1 | 2.23, 1.22, 0.02 | 0, 0, 1826 | 2.08, 0.84, 0.42 |
| FA1S | rigid | 1, 2, 1961 | 2 | 0.24, 0.65, 0.55 | 1, 2, 1104 | 2 | 3.58, 2.02, 0.07 | 0, 0, 3065 | 3.34, 1.38, 0.47 |
| FA1T | rigid | 1, 2, 2280 | 3 | 0.28, 0.74, 0.59 | 1, 2, 1320 | 3 | 2.40, 3.88, 0.15 | 0, 0, 3600 | 2.12, 3.14, 0.43 |
| LC3 (8 stop poses, runaway / hold) | rigid | 677, 686, 986 | 686 | 5.54, 12.48, 2.28 | 502, 498, 1056 | 502 | 27.79, 17.12, 3.43 | 323, 323, 501 | 22.95, 7.94, 2.37 |
| LC3 stop045 | compliant | 424, 416, 477 | 523 | 9.67, 6.97, 0.83 | 284, 277, 294 | 363 | 12.28, 9.89, 1.09 | 303, 303, 500 | 7.17, 7.35, 0.84 |
| F2 GS servo stall (9 cone poses) | rigid | 186, 176, 1038 | 201 | 1.67, 3.51, 8.12 | 115, 104, 910 | 128 | 56.56, 50.60, 4.45 | 132, 131, 509 | 56.14, 50.94, 7.56 |
| F2 TD touchdown Pc 0 | rigid | 223, 229, 238 | 230 | 2.35, 4.44, 1.20 | 96, 90, 224 | 96 | 12.54, 11.43, 0.72 | 297, 297, 219 | 10.40, 7.00, 1.32 |
| F2 TD touchdown Pc max | rigid | 276, 282, 417 | 283 | 2.71, 5.28, 1.41 | 105, 96, 328 | 105 | 14.13, 12.61, 0.86 | 359, 359, 506 | 11.55, 7.80, 1.47 |
| F2 LC6 hard landing 10 g | rigid | 88, 90, 230 | 90 | 1.32, 2.02, 0.22 | 37, 34, 199 | 37 | 2.92, 3.66, 0.17 | 120, 120, 402 | 1.86, 1.64, 0.24 |
| F2 LC2F stuck pintle | rigid | 114, 118, 575 | 118 | 1.03, 2.21, 0.51 | 25, 22, 376 | 25 | 3.72, 3.89, 0.28 | 136, 136, 908 | 2.74, 2.61, 0.42 |

Gimbal-axis stiffness at the 8 deg stop poses (engine held by the two TVC chains; rigid airframe; SIM with the servo output rigid, DERIVED with the servo output k_s 58 / 174 N m/rad per servo in series, ASSUMED TO-VERIFY B-TVC-1), N m/rad:

| pose (alpha, beta deg) | K_alpha FE | K_alpha +servo 58 / 174 | K_beta FE | K_beta +servo 58 / 174 |
|---|---|---|---|---|
| stop000 (-0.00, +8.00) | 6400 | 1060 / 2389 | 6570 | 1364 / 2891 |
| stop045 (-5.68, +5.65) | 6531 | 1051 / 2385 | 6348 | 1274 / 2727 |
| stop090 (-8.00, +0.00) | 6954 | 1050 / 2420 | 5488 | 1022 / 2234 |
| stop135 (-5.68, -5.65) | 7844 | 1079 / 2538 | 4426 | 775 / 1723 |
| stop180 (-0.00, -8.00) | 8577 | 1102 / 2630 | 3888 | 686 / 1522 |
| stop225 (+5.68, -5.65) | 7856 | 1079 / 2539 | 4163 | 767 / 1681 |
| stop270 (+8.00, -0.00) | 6964 | 1051 / 2421 | 5176 | 1011 / 2181 |
| stop315 (+5.68, +5.65) | 6533 | 1051 / 2385 | 6183 | 1267 / 2696 |

First engine-mount modes (modal_v351ca2b_c71, every body at mesh level 2, rigid airframe holes, servo output rigid, unstressed T_REF; SIM; production-K and servo-in-series columns DERIVED):

| mode | shape | f FE Hz | f at production K Hz | f with servo k_s 58 / 174 Hz |
|---|---|---|---|---|
| 1 | engine rocking about the inner axis (beta) | 51.4 | 47.8 | 21.3 / 31.3 |
| 2 | engine rocking about the outer axis X (alpha, engine + ring) | 59.4 | 55.5 | 21.9 / 33.1 |
| 4 | engine lateral X (on the mount) | 266.5 | - | - |
| 5 | engine lateral Y (on the mount) | 372.1 | - | - |
| 6 | engine axial (thrust path through the gimbal) | 408.3 | - | - |

## 9. Gimbal stiffness (F3: 8 stop poses, 9 range-cone poses, compliant airframe) (`results/k_stop_c71.json`, `results/k_cone_c71.json`, `results/k_pose_neutral_c71.json`, `results/k_stop045_compliant_c71.json`, `results/k_range_v351.json`, `tables/k_range_v351.md`)

Unit rod-pair steps R1/R2 on asm v1.2; K_FE = actuator moment / engine rotation about the gimbal axis with the servo output rigid; rods-only = rod chain alone; structure share = fraction of the compliance in the structure (bearings, levers, ring, brackets, engine) [SIM]; with servo = series with the ASSUMED servo output stiffness 58-174 N m/rad (electronics.json v1) [DERIVED].

| pose | K_alpha (outer X) N m/rad | K_beta (inner Y) N m/rad | rods-only alpha / beta kN m/rad | structure share | with servo 58 / 174 N m/rad: alpha ; beta |
|---|---|---|---|---|---|
| stop000 (0, 8) | 6400 | 6570 | 31.0 / 42.0 | 0.79 / 0.84 | 1060 / 2389 ; 1364 / 2891 |
| stop045 | 6531 | 6348 | 30.6 / 38.9 | 0.79 / 0.84 | 1051 / 2385 ; 1274 / 2727 |
| stop090 (-8, 0) | 6954 | 5488 | 30.2 / 30.7 | 0.77 / 0.82 | 1050 / 2420 ; 1022 / 2234 |
| stop135 | 7844 | 4426 | 30.5 / 23.0 | 0.74 / 0.81 | 1079 / 2538 ; 775 / 1723 |
| stop180 (0, -8) | 8577 | 3888 | 30.9 / 20.4 | 0.72 / 0.81 | 1102 / 2630 ; 686 / 1522 |
| stop225 | 7856 | 4163 | 30.5 / 23.0 | 0.74 / 0.82 | 1079 / 2539 ; 767 / 1681 |
| stop270 (8, 0) | 6964 | 5176 | 30.2 / 30.7 | 0.77 / 0.83 | 1051 / 2421 ; 1011 / 2181 |
| stop315 | 6533 | 6183 | 30.6 / 38.9 | 0.79 / 0.84 | 1051 / 2385 ; 1267 / 2696 |

Range over the 8 stop poses: **K_alpha 6400-8577, K_beta 3888-6570 N m/rad** (rigid servo); with the servo 686-2891 N m/rad, i.e. the servo dominates the loop stiffness. Comparison: Mechanical V5c (CAD v3.3, engine rigid, chain variants) K_alpha 5573-8764, K_beta 3133-5631 N m/rad (rigid servo), 780-1508 with k_s 58 (smin_T) - overlapping; the K_beta upper end here (6570) is 17 % above the V5c chain-high maximum [SIM by Mechanical, hub 04-fea/stiffness/gimbal_k_summary_V5c_v1.json 82a737caa138259a; chain-low to chain-high envelope; mech_T alone 5808-7406 / 3239-5167]. **Neutral pose** (`pose_neutral_c71`, both lever-root R3 balls): **K_alpha 7284, K_beta 5370 N m/rad** (rigid servo); with the servo 1129 / 2586 and 1070 / 2295 N m/rad [SIM / DERIVED]; this supersedes the predecessor's nx value (7834 / 5782, asm v1.1, rod REF-node elongation, 7.1). **Compliant airframe** (stop045, k_af ASSUMED): K_alpha 5609 / K_beta 5520 vs rigid 6531 / 6348 N m/rad (**-14 / -13 %**); with the servo 1024 / 2250 and 1237 / 2562 N m/rad - the airframe compliance matters for the rigid-servo K but little once the servo is in series. Static K on the coarsened modal meshes (Rayleigh checks, 9A): all-L2 8347 / 6209 (+15 / +16 % vs the production model), mixed L1/L2 7422 / 5479 (+2 %). 

**Range cone (the 9 F2 runs, `results/k_cone_c71.json`; both lever-root R3 balls in every run):**

| cone pose (alpha, beta deg) | K_alpha (outer X) N m/rad | K_beta (inner Y) N m/rad | rods-only alpha / beta kN m/rad | structure share | with servo 58 / 174 N m/rad: alpha ; beta |
|---|---|---|---|---|---|
| neutral (+0.00, +0.00) | 7284 | 5370 | 32.6 / 32.6 | 0.78 / 0.84 | 1129 / 2586 ; 1070 / 2295 |
| alpha+ (+7.00, +0.00) | 6992 | 5184 | 30.8 / 31.1 | 0.77 / 0.83 | 1067 / 2452 ; 1023 / 2200 |
| alpha- (-7.00, +0.00) | 6985 | 5453 | 30.8 / 31.1 | 0.77 / 0.82 | 1067 / 2452 ; 1033 / 2247 |
| beta+ (+0.00, +7.00) | 6430 | 6380 | 31.4 / 41.1 | 0.80 / 0.84 | 1071 / 2411 ; 1331 / 2818 |
| beta- (+0.00, -7.00) | 8364 | 4082 | 31.3 / 22.0 | 0.73 / 0.81 | 1111 / 2633 ; 737 / 1624 |
| combined045 (-4.96, +4.94) | 6563 | 6184 | 31.1 / 38.3 | 0.79 / 0.84 | 1066 / 2413 ; 1251 / 2672 |
| combined135 (-4.96, -4.94) | 7779 | 4552 | 31.0 / 24.3 | 0.75 / 0.81 | 1091 / 2557 ; 818 / 1805 |
| combined225 (+4.96, -4.94) | 7788 | 4326 | 31.0 / 24.3 | 0.75 / 0.82 | 1092 / 2558 ; 810 / 1768 |
| combined315 (+4.96, +4.94) | 6564 | 6034 | 31.1 / 38.3 | 0.79 / 0.84 | 1066 / 2414 ; 1245 / 2644 |

Range over the cone: **K_alpha 6430-8364, K_beta 4082-6380 N m/rad** (rigid servo); with the servo 737-2818 N m/rad [SIM / DERIVED]. Over every pose and the compliant variant (`tables/k_range_v351.md`): K_alpha 5609-8577, K_beta 3888-6570; with the servo 686-2891 N m/rad. K_beta falls when beta goes negative, with the rod chain: rods-only beta stiffness 20-22 kN m/rad at beta -7 / -8 deg against 41-42 at +7 / +8 [SIM]; the structure carries 72-84 % of the compliance in every rigid-airframe pose (86 % compliant). Against Mechanical V5c (CAD v3.3, engine rigid; chain-low to chain-high 5573-8764 / 3133-5631) [SIM by Mechanical]: K_alpha lies inside that envelope; K_beta reaches 6380 (cone, beta +7) and 6570 (stop000), 13-17 % above the V5c chain-high maximum.

## 9A. Modal and load-path periods (coarsened model; `results/modal_modal_v351ca2b_c71.json`, `results/modal_summary_v351.json`, `tables/modal_v351.md`; defective first run kept as `results/modal_modal_v351ca2_c71_DEFECT_bore_bond.json` and `results/k_kchk_ca2_c71_DEFECT_bore_bond.json`)

**Model actually solved (say it plainly):** asm v1.2, CAD v3.5.1, **every body at mesh level 2** (83,173 nodes, 7,059 constraint equations), neutral pose, rigid airframe holes, rigid servo output, unstressed at T_REF, item point masses (translational) and the ASSUMED 26 g Pc transducer; 60 modes to 5130 Hz (T_min 0.195 ms), ccx *FREQUENCY (SPOOLES / ARPACK), 430 s, peak 3.97 GB. It is a coarsened model, not the F1 L1 model.

- **Why coarsened:** the eigen step needs far more memory than a static solve of the same deck (ccx expands the tie equations in K and M): full L1 (171k nodes) killed at 8.13 GB, coarse=2 (133.6k) at 8.02 GB, mixed TC-01 / GM-01 / GM-02 at L1 (115k, 10.7k equations) at 8.08 GB (8 GB cap). [SIM, run logs `runs/chain_C.log`]
- **Defect found and fixed on the way (evidence kept):** the first all-L2 run (`modal_v351ca2_c71`) gave rocking modes at 23.8 / 35.9 Hz. Diagnosis (`tests/modal_diag/`): rod springs held only 3.9 / 9.1 % of the modal strain energy and the collar turned 0.36 x the case (0.89 in the static L1 step); the collar-to-case bore bond kept **15 of about 2850 equations** at L2 because the coarse TC-01 bore faces straddle the +/-10 mm selection band and their chords sit up to 0.5 mm off the collar bore. A static EAX/EAY run on that same mesh gave K 3019 / 1330 N m/rad, matching the modal values (within 1 %), so the eigen step was right and the mesh rule was wrong. Fix (asm_build, **only when TC-01 is at level >= 2**; the L1 models of F1 / F2 are unchanged): band +/-16 mm, tie tolerance 0.6 mm -> 789 / 843 equations, bonded area 1941 / 1961 mm2 (L1: 1930 / 1957). The 23.8 / 35.9 Hz values are a model defect and are not results.
- **Verification of the corrected modal:** Rayleigh check against a static EAX/EAY run on the same mesh (`kchk_ca2b_c71`): 51.9 / 59.9 Hz vs 51.4 / 59.4 Hz FE (<= 1 %); mode shapes: collar / case rotation 0.89 / 0.86 (static 0.885 / 0.895); lumped generalised mass 1.000-1.017; per-mode effective masses reproduced by a lumped-mass recomputation. **Coarsening bias:** the all-L2 gimbal is stiffer than the production pose model (TC-01 + gimbal parts at L1): K_beta 6209 vs 5370, K_alpha 8347 vs 7284 N m/rad (+16 / +15 %), so the FE rocking frequencies are about 7 % high; the values scaled to the production K are the best estimate. Lateral / axial mount modes carry a similar (unquantified) upward bias. Hot E of 6061 (-5 to -10 % at 120-150 degC) lowers f by a further 2.5-5 %.

**First engine-mount modes (engine data for the datasheet, 8.1; rigid airframe at the 16 M5 holes):**

| mode | shape | f FE (all L2, rigid servo) Hz | f at the production K Hz [DERIVED] | f with servo output k_s 58 / 174 N m/rad in series Hz [DERIVED] | eff. mass / inertia |
|---|---|---|---|---|---|
| 1 | engine rocking about the inner axis (beta) | 51.4 | 47.8 | 21.3 / 31.3 | 0.0585 kg m2 about the pivot |
| 2 | engine + ring rocking about the outer axis X (alpha) | 59.4 | 55.5 | 21.9 / 33.1 | 0.0590 kg m2 |
| 4 | engine lateral X on the mount | 266.5 | - | - | 2.19 kg (x) |
| 5 | engine lateral Y on the mount | 372.1 | - | - | 1.43 kg (y) |
| 6 | engine axial (thrust path through bearings, ring, posts) | 408.3 | - | - | 2.46 kg (z) |

Local modes below 1 kHz: 186 Hz pintle linkage (81 % KE; needle, PD-02 crank and servo drive are rigid bodies, so this is an upper bound on f), 518 Hz pintle linkage + head, 792 Hz pintle linkage (99 %), 825 / 917 / 1010 Hz forward equipment + case; servo brackets + servos 1611 / 1624 Hz. With the servo in series the loop sees the rocking pair at **about 21-33 Hz** (k_s range ASSUMED, TO-VERIFY bench B-TVC-1; servo rotor / gear-train reflected inertia NOT included, which would lower these further). Comparison: Mechanical V5c f_rock_min 53.2 / 39.8 Hz (mech_T, CAD v3.3, engine rigid) [SIM by Mechanical].

**Load-path periods under chamber pressure (lead 194 period domain).** The static unit-pressure response is decomposed into modal contributions u = sum phi_i (phi_i . F_OP) / omega_i^2 plus the residual of the modes above 5130 Hz (T < 0.195 ms). Shares of the static response by band [SIM / DERIVED]:

| path / governing node | share T > 1 ms | share 0.1-1 ms | residual T < 0.195 ms | period-domain reading |
|---|---|---|---|---|
| **TC-01 J-FWD hole (FA1S governing node, L1 node 8314, mapped 0.55 mm)** | +0.02 | +0.60 | +0.38 | 0.1-1 ms band: FA1D 93 bar (yield) / FA1U 102 bar (ultimate) apply, not FA1S |
| TC-01 LC1 governing node | +0.03 | +0.52 | +0.44 | 0.1-1 ms band (FA1D / FA1U) |
| TC-02 / TC-03 governing nodes (head, seat) | -0.13 to +0.11 | +0.06 to +1.03 | -0.01 to +1.08 | 0.1-1 ms band (FA1D / FA1U); TC-03 LC1 node: 11 % slow share |
| NZ-01 / TC-09 governing nodes (nozzle, aft closure) | 0.00 | +0.00 to +0.18 | +0.83 to +1.00 | 0.1-1 ms band or faster (residual T < 0.195 ms not resolved: FA1D / FA1U taken, FA1Q not claimed) |
| nozzle NZ-01 vs J1 lip (axial) | 0.00 | +0.11 | +0.90 | 0.1-1 ms band or faster (FA1D / FA1U) |
| Pc transducer (ASSUMED 26 g) vs head | -0.29 | +0.50 | +0.79 | 0.1-1 ms band or faster (FA1D / FA1U) |
| pintle needle vs seat (axial) | +0.61 | +0.30 | +0.09 | slow: governed by the axial mount mode (2.45 ms) -> FA1S on the pintle path |
| engine axial on the mount / GM-03 ring nodes | +0.88 to +1.06 | -0.18 to 0.00 | +0.12 | slow (thrust path): FA1S applies, as used for FA1T |
| GM-01 / GM-02 collar nodes | -0.10 to +0.32 | 0.00 to +0.20 | +0.48 to +1.09 | mostly 0.1-1 ms or faster; the GM-02 node that governs the FA1Q case has a 32 % slow share (FA1S on that share) |
| forward equipment vs head: torch, riser, bleed, FD-02 | -0.85 to +3.31 | -6.40 to -2.20 | +3.34 to +4.78 | not classifiable here: the shares cancel (tiny relative motions; items are point masses on RBE3) |
| forward equipment vs head: FD-04 | +0.08 | +0.62 | +0.30 | 0.1-1 ms band (FA1D / FA1U) |

**Reading for the FA-1 column selection (DERIVED, for the lead and Mechanical):** the pressure stress at the TC-01 J-FWD hole is carried by modes with T <= 1 ms (98 %; slow share 0.02), i.e. it is a 0.1-1 ms path in the line-194 sense (the residual above 5130 Hz is not resolved below 0.195 ms, so the T <= 0.1 ms / 90 bar column FA1Q is not claimed). On that reading the TC-01 FA-1 margin is **FA1D 93 bar yield +0.251 / FA1U 102 bar ultimate +0.233**, and the FA1S value **-0.221 / -0.160** (151.04 bar, DLF 2.0) is a bound that does not apply to this node. *Correction (lead CHANGELOG 223 (1)): the first version of this paragraph (REPORT a9f7f30055063c8e) and CHANGELOG 221 quoted FA1Q +0.291 / +0.393 (90 bar, T <= 0.1 ms) for this band by mistake.* The same band reading holds for the head, nozzle and aft-closure nodes. The thrust path (GM-03 ring, posts, pintle linkage via the axial mount mode at 2.45 ms) is slow, so FA1S / FA1T apply there (all positive). Caveats: L2 mesh (local stresses coarse; the band shares are a property of the modes and are less mesh-sensitive than the stress itself), unstressed T_REF stiffness, rigid airframe, and the residual band is not resolved below 0.195 ms (the 90 bar T <= 0.1 ms column is NOT claimed). The lead decides the column; both values stay in the tables.

### 9A.1 FA-1 column sensitivity at TC-01 (lead CHANGELOG 223 (3)(a); `results/fa1_band_sensitivity.json`, `tables/fa1_band_sensitivity.md`, `scripts/fa1_band_sensitivity.py`)

Post-processing of the same modal (no new eigen run). The static unit-pressure stress at the node (OP step, same mesh; the stress probe reproduces the ccx nodal stress: vM 14.822 vs 14.823 MPa per MPa) is split into modal terms; the FE frequencies are scaled by 1.00 / 0.90 / 0.85 (all-L2 coarsening makes K 15-16 % high, hot E lowers f by 2.5-5 %). A uniform scaling multiplies every modal term and the static value by 1/s^2, so only the band membership changes. Shares on the dominant principal direction (tensor projection in brackets) [SIM]:

| node (nearest L2 node) | f scale | slow T > 1 ms | 0.1-1 ms | residual (fast) | mode 11, 1010 Hz | mode 12, 1091 Hz | mode 13, 1189 Hz | MS_y / MS_u at the share [DERIVED] |
|---|---|---|---|---|---|---|---|---|
| TC-01 J-FWD (L1 8314 -> 2785, 0.55 mm) | 1.00 | +0.018 (+0.017) | +0.600 (+0.621) | +0.382 (+0.362) | +0.006 | +0.002 | +0.004 | +0.237 / +0.223 |
| | 0.90 | +0.026 (+0.026) | +0.592 (+0.612) | +0.382 | (slow) | (slow) | +0.004 (fast) | +0.231 / +0.218 |
| | 0.85 | +0.026 (+0.026) | +0.592 (+0.612) | +0.382 | (slow) | (slow) | +0.004 (fast, 1010 Hz) | +0.231 / +0.218 |
| TC-01 LC1 governing (L1 8843 -> 2800, 0.78 mm) | 1.00 | +0.035 (+0.035) | +0.524 | +0.441 | -0.004 | +0.016 | -0.005 | (+0.224 / +0.213)* |
| | 0.90 / 0.85 | +0.046 (+0.046) | +0.512 | +0.441 | (slow) | (slow) | -0.005 (fast) | (+0.216 / +0.206)* |

\* The LC1 node is not the FA-1 governing node; its margins are shown with the J-FWD columns as a bound.

- **Named modes:** mode 11 (1010.3 Hz; case 31 %, aft closure TC-09 20 %, forward equipment 20 % of the kinetic energy) carries **+0.006** of the J-FWD stress (-0.004 at the LC1 node); mode 12 (1090.9 Hz, pintle linkage 87 %) +0.002 (+0.016); mode 13 (1188.8 Hz, forward equipment 57 %) +0.004 (-0.005). With f x 0.90 and x 0.85, modes 11 and 12 move to T > 1 ms; mode 13 stays at T < 1 ms (1070 / 1010 Hz). The J-FWD stress is carried mainly by modes 22 (2134 Hz, +0.31) and 23 (2157 Hz, +0.21; collar / case / aft-closure modes); the slow share would reach 0.40 only if every frequency dropped to x 0.46 (J-FWD) / x 0.45 (LC1 node).
- **Neighbours (all TC-01 nodes within 2 mm, 6 each):** slow share +0.015 to +0.025 (x 1.00) and +0.024 to +0.035 (x 0.90 / 0.85) at J-FWD; +0.035 to +0.040 and +0.046 to +0.053 at the LC1 node. Counting every slow modal term with its magnitude (in-phase bound) gives 0.065-0.104 at J-FWD and 0.047-0.082 at the LC1 node; the worst of these (0.104 at J-FWD, x 0.90) gives **MS +0.175 / +0.175**.
- **Proportionality check (lead 223 (2)):** break-even pressure P x (1 + MS) at the J-FWD node over the four F1 columns: yield 116.2 / 116.3 / 116.6 / 117.7 bar (FA1Q / FA1D / FA1U / FA1S), ultimate 125.3 / 125.5 / 125.8 / 126.9 bar: spread **1.27 %** (thermal + manifold part), confirming the lead's 1.3 %. Break-even slow share **0.402 (yield) / 0.485 (ultimate)** with stress proportional to pressure from FA1D / FA1U (the lead's values); 0.414 / 0.499 with an affine fit through the four columns.
- **Result:** the slow share stays below 0.40 at both nodes at f x 0.85 and x 0.90 (largest signed value 0.053, largest magnitude sum 0.104). Criterion (a) of lead 223 (3) is met on this model. Caveats: all-L2 mesh (the band shares are a property of the modes and the static field, not of the local peak; the probe matches ccx), unstressed T_REF stiffness, rigid airframe, residual band not resolved below 0.195 ms. Criterion (b), the independent 3D FEA review (REV-MECH-2), is outside fea3d.

## 9B. F2: S-3D gimbal strength on CAD v3.5.1 (summary; full report `hub/04-fea/s3d_v351/REPORT-S3D.md`, results `hub/04-fea/s3d_v351/results/s3d_pose_<pose>_c71.json`)

**Model and cases:** the F1 model (asm v1.2) posed at the 9 range-cone poses (neutral, alpha +/-7, beta +/-7, four combined poses on the 7 deg cone) with the engine pressure parts at mesh level 2, all gimbal parts at L1 and **both lever roots at the R3 refinement**; unit steps OP, GX / GY / GZ, EAX / EAY, R1 / R2; cold, allowables at the B1_21.65 node temperatures. Cases (S-3D v1.1 set on the current loads): **GS** both servos at stall, rods at +/-F_d (441 N neutral, 552 N on the cone; mechanical.json v2.1, DERIVED) reacted by the engine angular acceleration + Pc_max + flight inertia 0.61 g lateral / {0, 4.04 g} axial + hose 31.2 N; **TD** touchdown with the servos holding (6.29 g lateral, 5.43 g axial, 79.28 rad/s2; gnc.json v3.1 SIM); **LC6** 10 g axial + 3 g lateral (ASSUMED envelope); **LC2F** stuck-pintle thrust 907.7 N + flight inertia (SF 1.0 / 1.5); SF 1.5 / 2.0 otherwise. SR (runaway onto the 8 deg stop) = F1 LC3; FA1T from F1.

**Per-part minimum margins, regular set, yield / ultimate (pose) [SIM]:**

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

**GS lever-root minimum per pose [SIM]:**

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

**Rod forces and engine angular acceleration [SIM]:**

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

**Connector envelopes and mount hole shear [SIM]:**

| case | inner cup max comp. N | inner washer N | outer cup N | outer washer N | max hole shear N (hole, pose) |
|---|---|---|---|---|---|
| GS | 801 | 280 | 799 | 216 | 808 (AF_GM10_2, beta-) |
| LC6 | 137 | 115 | 146 | 94 | 81 (AF_GM09_4, alpha+) |
| LC2F | 438 | 41 | 435 | 135 | 190 (AF_GM09_4, alpha+) |

**Comparison with S-3D v1.1** (Mechanical, CAD v3.4 V5c, centre + betam7, 7075-T6 design-change columns, 1.5 mm exclusion): GS GM-01 +0.156 / -0.004, GM-02 +0.166 / +0.005; SR +0.048 / -0.097 and +0.057 / -0.089 [SIM by Mechanical]. The rod forces are the same (441 / 552 / 609 N); the 1.5 mm exclusion removes the R1.2 fillet zone, which carries 396-403 MPa (GS) and 431-435 MPa (SR) when resolved, so the v1.1 margins are not conservative at the lever root [DERIVED; geometry change v3.4 -> v3.5.1 not separated]. F2 hot lower bound (LC1 thermo-pressure field + the cone-pose increment, part maximum for the refined collars): GM-01 -0.219 / -0.327, GM-02 -0.259 / -0.362; every other gimbal part >= +0.842 [DERIVED]. Charts and figures: `hub/04-fea/s3d_v351/figs/S3D-C1_gimbal_margins.png`, `S3D-01_alpha-_GM02_R3_zoom_vM.png`.

## 10. F4 secondary structure (hand calcs on F1 loads; `results/f4_secondary.json`, `tables/f4_secondary.md`, `scripts/f4_secondary.py`)

Method [DERIVED]: per-screw limit tension P and shear V from the attached mass x the case accelerations (LC1 flight 4.04 g / 0.61 g; LC3 touchdown 6.29 g / 5.43 g / 79.28 rad/s2; hard-landing envelope 10 g axial (gnc DERIVED v1); FA-1 equipment bound 26.85 g = DLF 2.0 x 1.8 kN / 13.671 kg dry; transport 3 g) plus pressure and hose end loads; J-PD01 loads are the FE PDFOOT connector forces (SIM, asm v1.2). Preload F = T / (K d) with K 0.2 and +/-25 % scatter [ASSUMED]; friction 0.20 [ASSUMED]; bounding load factor Phi 0 (separation / slip) and Phi 1 (screw, thread), second variant Phi 0.2 [ASSUMED typical]; hot screw strength k_T = SS316L Fty(T)/Fty(20 C) [ASSUMED proxy]; host-thread stripping area FED-STD-H28 [AS RECALLED]; G11 bearing vs Sc(T). SF per 188 (9).

| joint | screws | governing case | MS bounding (criterion) | MS Phi 0.2 | assembly utilisation nu nominal / +25 % |
|---|---|---|---|---|---|
| J-PD01 | 4 x M3 A2-70, G11 spacer, into TC-02 | FA1S, soak-back thermal preload (+170..+499 N for G11 CTE 30-70e-6, TO-VERIFY) | +0.15 (screw yield) | +0.20 | 0.57 / 0.71 |
| **J-FD01** | 2 x M3 A4-70 into TC-02 (FD-01 manifold with BL-02 / BL-03), 121 degC | 10 g hard landing, pressure on the R7 bounding area | **-0.41** (screw yield; slip -0.28, ultimate -0.17) | **-0.20** | **0.94 / 1.18** |
| J-FD09 | 2 x M4 A4-70 into GM-09 (hose fixed-end sleeve) | 10 g, hose EI 0.5 N m2 sensitivity | -0.17 (screw yield) | +0.05 | 0.84 / 1.05 |
| J-FS15 | 2 x M4 module -> FS-15 | FA-1 equipment bound | +0.04 | +0.11 | 0.84 / 1.05 |
| J-FS15 (ICD-2) | 2 x M5 FS-15 -> airframe wall | 10 g | +0.07 | +0.11 | 0.84 / 1.05 |
| J-BL05 | 4 x M3 per valve -> BL-07 (2 x 0.30 kg valves ASSUMED, CG 45 mm, 22 mm pattern ASSUMED) | 10 g | +0.09 | +0.12 | 0.83 / 1.04 |

J-FD01 is negative in every case, also in LC1 flight (-0.38 bounding) and with the AS568-010 seal-OD pressure area instead of R7 (-0.31 bounding / -0.17 Phi 0.2): the specified 1.0 N m on an M3 A4-70 screw gives 1667 N nominal preload (nu 0.94; the VDI 2230 guide is <= 0.9, AS RECALLED) and the ASSUMED hot-strength factor 0.80 at 121 degC leaves no room (hot preload utilisation 1.15 before external load). Torque window keeping every case MS >= 0 [DERIVED]: none in the bounding model; Phi 0.2 without slip 0.62-0.77 N m; Phi 0.2 with the seal-OD area 0.66-0.82 N m. J-FD09: the bounding window [0.65, 2.02] N m ends just below the specified 2.05 N m. All joints sit at nu 0.83-0.84 nominal / 1.04-1.05 at +25 % scatter, so the screw-yield margins are set by the tightening scatter, not by the external loads. **For Mechanical (owner of the specs):** J-FD01 needs a lower torque with controlled scatter (about 0.7 N m), a stronger screw (A4-80 or M4) or a sourced hot-strength value; J-FD09 about 1.8 N m; all joints need a defined tightening method / scatter. ICD-14 bleed cluster: 0.740 kg at [12.4, 33.0, 303.0] mm, inertial resultants per case in the JSON.

## 11. Not run or not done (exact list)

1. **Modal on the production mesh:** not possible under the 8 GB cap (full L1 8.13 GB, coarse=2 8.02 GB, mixed L1/L2 8.08 GB: killed). Reported on the all-L2 model with its bias (9A). Not run: prestressed (Pc / thrust) or hot modal; servo rotor / gear-train reflected inertia; airframe flexibility in the modal; forward-equipment local periods (shares cancel on point masses).
2. **F2:** hot S-3D on the refined lever-root meshes node by node (only the part-maximum hot bound, 9B); lever-root fatigue (servo dither, vibration) and a local strain criterion at the fillet (no load spectrum); compliant airframe at the cone poses (only stop045, F1 section 8).
3. **F3:** compliant airframe only at stop045; no K with a measured servo output stiffness (k_s 58-174 N m/rad ASSUMED, bench B-TVC-1).
4. 7.2 moment-closure path not identified.
5. LC3 hot bound on the refined lever-root meshes (only the L1 bound exists; the refined values in 4.6 are cold).
6. Thermal FE of the gimbal / bay (60 degC ASSUMED); TC-02 T-F1 / T-F2 (Mechanical / founder); NZ-03 N-F1 (founder); LC-TB70 is Mechanical's (216 (4)).
7. Datasheet checks: HK0808 C0, PTFE washers, J-FWD / M5 / M3 screw allowables (no datasheet value in the hub; none invented).
8. No redesign of the negatives (GM-01 / GM-02 lever roots, J-FD01, J-FD09): routed to Mechanical as design actions (CHANGELOG 223 (5)); no analysis of a changed design.
9. ICD-AIRFRAME v2.1 paste format: dropped with the ICD (CHANGELOG 222); the data are in 8.1 as engine data.

## 12. Files (sha256/16 of every file in MANIFEST.json in this folder)

- `tables/`: part margins, ICD, LC3 summary, F4 tables (asm v1.2). `tables_legacy_v1.1/`: interim tables.
- `results/`: post-processing JSON on asm v1.2 (LC1, FA-1 incl. FA1T, LC3 x 8 poses, GM-02 refinements and edge metric, hot bound, compliant airframe, convergence, TB1 thread variant, free-body checks, v1.1-vs-v1.2 comparisons, stiffness, F4). `results/legacy_asm_v1.1/`: interim JSON kept as evidence.
- `figs/`: F1-01 LC1 B1_1 MS overall; F1-02 LC1 B1_21.65 vM; F1-03 NZ-01 throat MS; F1-04 TB1 zoom vM B1_19; F1-05 FA1S MS overall; F1-06 FA1S TC-01 J-FWD zoom vM; F1-07 LC3 stop045 MS overall; F1-08 GM-02 lever-root section vM (L1 mesh); F1-09 GM-02 lever root refined R3 vM; F1-C1 part margins; F1-C2 airframe holes; F1-C3 convergence. Each title gives case and criterion; colour bars give units; footer gives CAD, tool, asm version.
- `tests/conn71/`: connector test models (7.1 evidence). `tests/modal_diag/`: modal diagnostics (spring strain-energy shares, per-body rotations, lumped effective masses) - evidence for the L2 bore-bond defect of 9A.
- `runs/`: model, mass and pressure metadata of the v1.2 L1 run; queue and chain log.
- Added in this final release: `tables/margin_matrix_v351.{md,json}` (3A), `tables/engine_mount_data_v351.md` + `results/engine_mount_data_v351.json` (8.1), `results/k_cone_c71.json` + `results/k_range_v351.json` + `tables/k_range_v351.md` (9), `results/s3d_summary_v351.json` + `tables/s3d_*.md` (9B), `results/fa1_band_sensitivity.json` + `tables/fa1_band_sensitivity.md` (9A.1), `results/modal_summary_v351.json` + `tables/modal_v351.md` (9A). The F2 per-pose results, the F2 hot bound and figures are in `hub/04-fea/s3d_v351/` (own MANIFEST).
- `src/`: scripts, for reproduction. Solver bulk stays in `/home/claude/work/fea3d/runs` (not published).

### 12.1 Key files (sha256/16; the full list with byte counts is MANIFEST.json)

| published path | sha256/16 | content |
|---|---|---|
| `tables/margin_matrix_v351.md` | `1067bc60db684d15` | 3A margin matrix (every part x case) |
| `tables/margin_matrix_v351.json` | `edaaff6bdf7d392a` | 3A, machine-readable |
| `tables/f1_part_margins.json` | `69af428e79367cd5` | 3 F1 per-part margins (all columns) |
| `tables/engine_mount_data_v351.md` | `917d497681939e65` | 8.1 mounting data |
| `results/engine_mount_data_v351.json` | `7aa3faf0f15d992d` | 8.1, machine-readable |
| `tables/icd_airframe_v21.md` | `cedcfab909095d85` | 8.1, ICD v2.1 paste kept as published (not rewritten) |
| `results/k_stop_c71.json` | `fd9ca16b0b3d2304` | 9 K at the 8 stop poses |
| `results/k_cone_c71.json` | `bfb9b56ed85b6a2f` | 9 K at the 9 cone poses |
| `results/k_range_v351.json` | `27421efb09e7daf0` | 9 K range + V5c comparison |
| `results/modal_modal_v351ca2b_c71.json` | `9af80c657eed11ac` | 9A modal (all-L2, fixed bond) |
| `results/modal_summary_v351.json` | `242b38ffab643434` | 9A engine-mount modes, path periods |
| `results/fa1_band_sensitivity.json` | `794155b97167a784` | 9A.1 FA-1 band sensitivity |
| `results/s3d_summary_v351.json` | `44b7648633eaf7a3` | 9B F2 summary |
| `results/f1_post_fa1_c71.json` | `7d5970a387779ab3` | FA-1 (FA1Q/D/U/S/T) |
| `results/f1_post_lc1v351_c71.json` | `79507be526bde2dc` | LC1 |
| `results/f1_lc3_summary_c71.json` | `3a5848fa1bb686d3` | LC3 summary |
| `results/f1_lever_root_GM01_c71.json` | `87f7f3e5912af4b6` | 4.6 GM-01 lever root R3 |
| `results/f1_lever_root_GM02_c71.json` | `6f0d280217bd6ad7` | 4.6 GM-02 lever root R2 / R3 |
| `results/f4_secondary.json` | `0746e62e2d9e87da` | 10 F4 joints |
| `s3d_v351/REPORT-S3D.md` | `88c34c5fe7394e60` | F2 full report (other folder) |

## 13. Open items and owners (2026-10-19)

| # | item | status / numbers | owner | closure |
|---|---|---|---|---|
| 1 | **GM-01 / GM-02 lever roots** (7075-T6 collar halves, R1.2 fillet at the R32.5 collar OD) | LC3 runaway R3: GM-01 -0.273 / -0.374, GM-02 -0.280 / -0.379; F2 GS servo stall: GM-01 -0.209 / -0.319, GM-02 -0.223 / -0.330 (ultimate-negative at all 9 cone poses); hot bounds worse [SIM / DERIVED] | **Mechanical - DESIGN CHANGE** (CHANGELOG 223 (5)) | larger lever-root fillet / thicker root with the fillet-to-collar edge blended, or a lower stall-limited rod force; then F2 GS + F1 LC3 at R3 on the changed CAD (fea3d) |
| 2 | **J-FD01** (2 x M3 A4-70 into TC-02, 121 degC) | -0.41 bounding / -0.20 Phi 0.2; nu 0.94 nominal at the specified 1.0 N m [DERIVED, ASSUMED preload model] | **Mechanical - DESIGN CHANGE** (CHANGELOG 223 (5)) | about 0.7 N m with controlled scatter, A4-80 or M4, or a sourced hot strength |
| 3 | J-FD09 (2 x M4 A4-70 into GM-09) | -0.17 bounding / +0.05 Phi 0.2 | Mechanical | about 1.8 N m; a defined tightening method / scatter for every joint |
| 4 | TC-01 J-FWD hole, FA-1 column | FA1S -0.221 / -0.160 (bound, kept); FA1D +0.251 yield / FA1U +0.233 ultimate on the 0.1-1 ms reading; criterion (a) met (9A.1: slow share <= 0.053 signed, <= 0.104 magnitude sum, against 0.40) | lead (decision PROVISIONAL, CHANGELOG 223 (3)); REV-MECH-2 for criterion (b) | independent review confirms the modal decomposition and the band reading |
| 5 | TC-02 TB1 seat | ultimate -0.119 LC1 / -0.179 hot bound; 159 degC > 150 degC limit (check (d)) | Mechanical / founder (T-F1 sourced short-time allowables, T-F2 contact FE; CHANGELOG 212) | T-F1 / T-F2 |
| 6 | NZ-01 graphite throat | -0.435 LC1 / -0.443 hot bound (brittle, total stress, thermal); refinement makes it worse | Mechanical / Combustion | primary design question (not a mesh issue) |
| 7 | TC-03 GlidCop flange corner | -0.312 / -0.375 total stress; primary-only +7.3; P+Q shakedown +1.06 to +1.22 | Mechanical | criterion decision (S-AX +1.203 shakedown, TO-VERIFY) |
| 8 | NZ-03 char strength | 20 MPa ASSUMED; LC3 +0.194 | founder | test N-F1 |
| 9 | Bearing / washer / screw datasheets | HK0808 C0 / C, PTFE washers, M5 / J-FWD / M3 screw allowables: TO-VERIFY (loads: FA1T 1764 N per needle cup, GS 801 N; M5 shear up to 889 N) | Mechanical | datasheet values into the hub (none invented here) |
| 10 | 7075-T6 temperature table (RM1-06) | allowables temperature-independent 470 / 540 MPa (LITERATURE) | Mechanical | table + mill certificate |
| 11 | LC-TB70 | outside fea3d | Mechanical (CHANGELOG 216 (4)) | - |
| 12 | Servo output stiffness and reflected inertia | k_s 58-174 N m/rad ASSUMED; rocking 21-33 Hz with the servo in series; reflected inertia not included | Electronics / bench B-TVC-1; REV-GNC-6 for the ENG-11 plant check (CHANGELOG 223 (5)) | bench measurement |
| 13 | Moment closure 7.2 | 97-99.5 %, bounded impact (rod force <= ~6 N) | fea3d (successor) | find the path |
| 14 | Hot lever-root margins node by node on the refined meshes (LC3, F2) | only part-maximum / L1 bounds | fea3d (successor) | with the TH step on the refined mesh, after the design change |
| 15 | Modal on the production mesh, prestressed / hot | not possible under the 8 GB cap | fea3d (if a larger memory cap is granted) | - |
| 16 | Airframe first bending mode before K_s is frozen (ENG-11) | to be MEASURED (CHANGELOG 218 / 222) | airframe work (deferred by the founder, CHANGELOG 222) | - |
END FEA3D-HANDBACK
