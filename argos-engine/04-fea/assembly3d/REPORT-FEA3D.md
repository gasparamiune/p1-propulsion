# ARGOS H1 engine - assembled-engine 3D FE (FEA3D) - F1 final on asm v1.2, F4 done, F2 / F3 / modal in progress

| | |
|---|---|
| Status | **2026-10-19, F1 FINAL on the corrected connector model (asm v1.2, REPORT 7.1 closed)**: LC1 (4 S-AX thermal states), FA-1 (FA1Q/D/U/S + FA1T), LC3 (8 stop poses x 64 sub-cases, cold + hot lower bound), rigid and compliant airframe, mesh convergence (3 levels at 4 points; lever roots R2 / R3). **F4** secondary-structure joints done (hand calcs on F1 loads). **Pending at this publish (queued, section 11):** modal + periods, F2 cone poses (S-3D on v3.5.1), F3 stiffness range over the cone poses. Supersedes the INTERIM of 2026-10-19 (hub commit 9bd6958). |
| Author | fea3d (successor Senior FEA analyst 3D), lead brief CHANGELOG 188 + successor brief 2026-10-15 + coordinator 2026-10-19 (lead decision: fix 7.1 before modal and cones) |
| Configuration | CAD v3.5.1 frozen (CHANGELOG 206): MANIFEST `b62c0e0ac8555fb8`, ENGINE STEP sha16 `4ca22820c796b670`, 5.40921 kg wet. (03-cad/v3.5.2 is a GNC mass sensitivity per CHANGELOG 209/211, not used.) |
| Tool | CalculiX 2.21 (SPOOLES direct), C3D10 tets (gmsh 4.15 HXT), own Python pre/post (`src/`), assembly model **fea3d-asm v1.2** |
| Units | SI; mm, N, MPa, degC in the report where conventional. MS = allowable / (SF x stress) - 1 |
| Tags | SIM (FE output), DERIVED (computed from SIM/data), ASSUMED, DATASHEET, LITERATURE, TO-VERIFY, AS RECALLED |

> **Not physical approval.** A converged solution, matching numbers or clean plots do not approve hardware. Negative margins are reported as found; no margin has been forced. Every number below is SIM unless tagged otherwise.

## 1. Claims (checkpoint, SUPERVISION-WORKFLOW)

1. **Connector defect 7.1 closed (lead decision 2026-10-19).** Root cause: CalculiX SPRINGA uses the current (deformed) geometry also in linear static steps; with 1 mm auxiliary springs the inner-gimbal bushings on rigid-body references carried only 56-79 % of the engine load. Fix (asm v1.2): spring length 1e6 mm. **Unit-step free body of the engine now closes to <= 0.006 N in every unit step (100.00 % of the engine load through the inner bearings, inner washer and rods)** at LC1 neutral and at the 8 deg stop pose [SIM]. The deck changed, so LC1, the 8 LC3 stop poses and FA-1 were re-solved; the LC3 stop poses and the FA1T gimbal margins are re-posted on v1.2 (sections 6, 7).
2. **Effect of the fix:** engine-part stresses change <= 0.15 %, airframe hole loads < 0.3 %, LC3 margins unchanged to the third decimal; the bearing loads change materially: FA1T now 1764 N on each of the four needle cups (v1.1 gave 4036 N / 1766 N and 440 N on the inner washer), LC1 inner cups 199.8 N each. One residual observation stays open (7.2: moment closure 97-99.5 %, bounded impact).
3. **LC1:** negative total-stress margins at **NZ-01** throat -0.435 (B1_1, thermal, S-AX -0.443), **TC-03** flange corner -0.312 / -0.375 (B1_1, 98 % thermal; primary-only +7.3) and **TC-02** TB1 seat ultimate -0.119 (B1_19; 159 degC > 150 degC limit, check (d) open per CHANGELOG 212). All other parts positive.
4. **FA-1:** FA1S (151.04 bar abs, T > 1 ms bound) **TC-01 J-FWD hole -0.221 / -0.160**, converged (R3 -0.202 / -0.140). FA1Q/D/U positive. FA1T (3.6 kN spike, gimbal / mount parts) all positive, min GM-03 +1.483 / +1.671. Column selection waits for the modal (pending).
5. **LC3 (8 deg stop, runaway with the rod at the 609 N stall limit, max thrust + touchdown inertia, cold):** at the L1 regular-node convention GM-02 +0.182 / +0.019 (stop045), GM-01 +0.206 / +0.039 (stop315), NZ-03 +0.194 (stop000). **Refinement of the GM-02 lever root makes it NEGATIVE: R3 -0.280 / -0.379** (435 MPa at the R1.2 lever-root fillet where it meets the collar OD; the stress 0.5 mm from the edge line is stable R2 -> R3, 420 -> 416 MPa, i.e. not a singularity). The L1 value was unconservative because the 1 mm exclusion around a flagged edge removed the 1.2 mm fillet zone (section 4.6). GM-01 (mirror): **GM-01 R3 -0.273 / -0.374** (431 MPa; 421 MPa at 0.5 mm from the edge line): the same finding for both levers.
6. **LC3 hot lower bound:** NZ-01 -0.443, TC-03 -0.357 / -0.415, TC-02 +0.022 / -0.179, GM-02 +0.128 / -0.028 (L1 convention; refined: worse, section 4.6).
7. **Airframe interface (16 x M5):** max screw shear LC1 75 N, FA1S 554 N, FA1T 643 N, LC3 889 N (rigid airframe) [SIM]; compliant airframe (k_af ASSUMED): max hole shear LC1 48 N, LC3 stop045 454 N (rigid 837 N at the same pose) - the rigid airframe bounds the hole loads; engine-part margins unchanged.
8. **F4 joints:** **J-FD01 (2 x M3 A4-70 into TC-02) NEGATIVE: -0.41 bounding / -0.20 with load factor 0.2**, driven by the specified 1.0 N m (assembly utilisation 0.94 nominal, 1.18 at +25 % scatter) and the 121 degC screw temperature; J-FD09 -0.17 bounding / +0.05 (EI 0.5 sensitivity, 10 g); others +0.04 to +0.15 bounding (all hand calcs on ASSUMED preload scatter, K and hot-strength factor).
9. **Gimbal stiffness at the 8 stop poses** (rigid servo, flexible engine and structure): K_alpha 6400-8577, K_beta 3888-6570 N m/rad; with the ASSUMED servo output stiffness 58-174 N m/rad in series: 686-2891 N m/rad [SIM/DERIVED].

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

FA1D / FA1U columns and the primary-only and P+Q columns are in the full table. The asm v1.1 (interim) tables are kept in `tables_legacy_v1.1/` as evidence.

## 4. Governing findings (decision 212 terms)

**4.1 TC-02 (forward closure, 6061-T6).** L1 +0.096 y / -0.119 u at B1_19, at the TB1 tie end (r 5.86, z 107.51), 159 degC; vM 102.4 MPa of which 100.8 MPa thermal -> secondary (primary-only +3.44; P+Q 2Fty +2.29). The part reaches 159 degC against its 150 degC limit [SIM vs DATASHEET limit]: check (d) stays **open** (CHANGELOG 212: T-F1 sourced short-time allowables + T-F2 contact FE). Refinement moves the regular-set maximum away from the tie end (R2 +0.213 / -0.040, R3 +0.469 / +0.165); the all-node value at the tie end grows (102 -> 147 -> 143 MPa) = tie-termination singularity. 'thread' TB1 variant +0.196 / -0.054. **No converged TC-02 ultimate margin is claimed**: between -0.12 and +0.17 on total stress depending on the tie-end idealisation; the decision rests on T-F2.

**4.2 TC-03 (GlidCop seat insert).** L1 -0.312 / -0.375 at B1_1, flange corner r 9.8 / z 105.51, 74 degC; vM 241 MPa, 237 MPa of it thermal. R2 -0.266 (226 MPa), R3 -0.342 (252 MPa): oscillating, not asymptotic. Thread-only TB1 tie: -0.259 / -0.327 at the same corner (over-constraint hypothesis refuted). Primary-only +7.3; P+Q shakedown +1.06 (L1) to +1.22 (refined). Negative on total stress, positive on primary and on P+Q [SIM]; whether S-AX's +1.203 is the same shakedown criterion is TO-VERIFY with Mechanical.

**4.3 NZ-01 (graphite throat).** -0.435 at B1_1 (S-AX -0.443); s3 -69 MPa at 1330 degC, thermal-dominated; refinement makes it worse (R2 -0.454, R3 -0.481; growth 3.5 % then 5.1 %, not asymptotic). A primary design question (brittle, SF 2.0 on total stress) for Mechanical / Combustion; refinement will not remove it.

**4.4 NZ-03 (carbon-phenolic retainer).** LC1 +0.476 (B1_2), FA1S +0.630, LC3 +0.194 to +0.206 at all stop poses [SIM], on the **ASSUMED 20 MPa char compressive strength** (CHANGELOG 212); founder test N-F1 closes it.

**4.5 TC-01 (case) under FA1S.** -0.221 / -0.160 at the J-FWD radial screw hole (r 28.6, z 125.5), 46 degC; regular-set vM 303.0 / 302.6 / 295.9 MPa at L1 / R2 / R3 (h 3.0 / 1.3 / 0.7 mm): converged within 2.4 %, R3 -0.202 / -0.140; the all-node value at the RBE3 patch edge grows (357 -> 382 -> 399 MPa, idealisation). J-FWD screws carry 4.85 kN shear each [SIM] = pi x 28.6^2 x 15.10 MPa / 8 [DERIVED]. FA1Q/D/U positive (+0.29 / +0.25 / +0.23 u). The negative stands until the modal decides whether FA1S applies to the forward closure path. J-FWD screw shear / hole bearing vs a fastener datasheet: TO-VERIFY (Mechanical).

**4.6 GM-01 / GM-02 lever roots (LC3 runaway, rod at 609 N).** L1 regular: GM-02 +0.182 / +0.019 (stop045), GM-01 +0.206 / +0.039 (stop315), peak at r 33.7 / z -6.9 (posed). The all-node maximum there was 459 MPa (MS -0.32 / -0.41) next to sliver tets. Refinement balls at the GM-02 lever root (R2 h 0.60 mm, R3 h 0.34 mm; `pose_stop045_gm02r2/r3_c71`):

| level | h (mm) | regular-set MS y / u | vM at the peak node (MPa) | max vM within 3 mm, > 0.5 mm from the R2 edge line | same, > 1.0 mm |
|---|---|---|---|---|---|
| L1 | 1.46 | +0.182 / +0.019 (265 MPa, 1.06 mm from the edge) | 414 (excluded) | 459 (bad tets) | 265 |
| R2 | 0.60 | +0.139 / -0.018 (275 MPa) | 420 (excluded) | 420 | 275 |
| R3 | 0.34 | **-0.280 / -0.379** (435 MPa) | 435 (regular) | 416 | 297 |

CAD check (defeatured BREP of GM-02, faces at the peak): the R1.2 mm cylindrical lever-root fillet and an R0.5 mm toroidal edge fillet meet the R32.5 mm collar OD along B-spline intersection edges; the surface normal turns by ~92 deg within 0.3 mm at every level (a sharp intersection edge next to the fillet). The edge detector flags it as re-entrant on L1 and R2 but not on R3, which is why the regular-set value jumps. The stress 0.5 mm from that edge line is **stable under refinement (420 -> 416 MPa)**, so it is a finite fillet-zone concentration, not a singularity; the 1 mm exclusion at L1 / R2 removed the fillet zone and was **unconservative**. Result: **GM-02 lever root under the LC3 runaway (cold) MS_y about -0.25 to -0.28, MS_u about -0.35 to -0.38** [SIM, R2/R3]; the hot increment adds about +14 MPa at L1 (hot bound +0.128 vs cold +0.182) [DERIVED], making it slightly worse. GM-01 (mirror lever, stop315, R3 ball h 0.34 mm, `pose_stop315_gm01r3_c71`): regular set -0.273 / -0.374 (431 MPa), 421 MPa at 0.5 mm from the edge line, L1 all-node 460 MPa - the same finding for both levers (`results/f1_lever_root_GM0{1,2}_c71.json`, figure F1-09). What this means for the design (Mechanical owns it): the lever root of the 7075-T6 collar halves does not carry the 609 N stall-limited rod force with SF 1.5 / 2.0 in the bounding LC3 combination; options are a larger lever-root fillet / thicker root, a lower stall-limited rod force, or a lower design combination (the LC3 combination of max thrust + touchdown inertia + runaway is bounding by construction). The sharp fillet-to-collar intersection edge itself (zero-radius edge in CAD) should be blended.

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

Compliant airframe at stop045 (`pose_stop045_compliant_c71`): fb_run 324-419 N, rod 2 at 609 N, GM-02 +0.181 / +0.018 (rigid +0.182 / +0.019), NZ-03 +0.200, max hole shear 454 N (rigid 837 N), moment residual 3.3 % [SIM].

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

## 8. Airframe interface (ICD), rigid and compliant airframe (`tables/f1_icd_airframe.{md,json}`, chart F1-C2)

Screws are radial through the airframe wall: shear = hypot(tangential, axial Z); pull-out = radial outward [SIM].

| Case | max screw shear N (hole) | max radial pull-out N (hole) | max push-in N | max |axial| N | sum F on airframe N (max |Fx|, |Fy|, |Fz|) |
|---|---|---|---|---|---|
| LC1_rigid | 75.2 (AF_GM09_4) | 19.8 (AF_GM09_0) | 8.2 (AF_GM10_7) | 68.1 (AF_GM09_4) | 24.5, 24.5, 345.0 |
| LC1_compliant | 48.0 (AF_GM10_3) | 1.2 (AF_GM09_0) | 0.6 (AF_GM09_7) | 47.9 (AF_GM10_3) | 24.6, 24.6, 344.9 |
| FA1S_rigid | 553.6 (AF_GM09_0) | 101.3 (AF_GM09_0) | 53.1 (AF_GM10_7) | 509.3 (AF_GM09_4) | 0.0, 0.0, 3064.9 |
| FA1T_rigid | 643.2 (AF_GM09_0) | 117.7 (AF_GM09_0) | 62.2 (AF_GM10_7) | 591.8 (AF_GM09_4) | 0.0, 0.0, 3600.0 |
| LC3_rigid_8poses | 889.4 (AF_GM10_5) | 281.1 (AF_GM09_7) | 310.7 (AF_GM09_0) | 889.0 (AF_GM10_5) | 323.2, 323.0, 500.7 |
| LC3_compliant_stop045 | 453.5 (AF_GM10_5) | 25.4 (AF_GM09_0) | 15.4 (AF_GM09_5) | 450.1 (AF_GM10_5) | 302.6, 302.6, 500.4 |

Rigid vs compliant airframe (k_af 2e3 / 2e4 / 2e4 N/mm radial / tangential / axial, ASSUMED): the compliant ring of springs spreads the load (LC1 max hole shear 75 -> 48 N; LC3 stop045 837 -> 454 N; pull-out 247 -> 25 N at stop045) and leaves the totals unchanged; **the rigid airframe is the bounding case for the hole loads**. The engine-part margins do not change (<= 0.005); frame-part margins drop (e.g. GM-09 LC1 +72.2 -> +36.0, GM-10 +192.5 -> +70.8) but stay large; GM-02 at stop045 +0.181 / +0.018 compliant vs +0.182 / +0.019 rigid [SIM].

Long-period thrust spectrum for the ICD (CHANGELOG 194), linear scaling of the FA1T hole envelope with net thrust [DERIVED]: 1.76 kN @ 25 ms -> 314 N max hole shear; 1.45 kN @ 40 ms -> 259 N; 1.04 kN @ 100 ms -> 186 N.

## 9. Gimbal stiffness (F3, stop poses; cone poses pending) (`results/k_stop_c71.json`)

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

Range over the 8 stop poses: **K_alpha 6400-8577, K_beta 3888-6570 N m/rad** (rigid servo); with the servo 686-2891 N m/rad, i.e. the servo dominates the loop stiffness. Comparison: Mechanical V5c (CAD v3.3, engine rigid, chain variants) K_alpha 5573-8764, K_beta 3133-5631 N m/rad (rigid servo), 780-1518 with k_s 58 - consistent [DATASHEET hub 04-fea/stiffness/gimbal_k_summary_V5c_v1.json]. The interim neutral value from the predecessor's nx run (7834 / 5782, asm v1.1) used the rod REF-node elongation (zero output, 7.1) and is superseded by the cone-pose neutral run (pending).

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

## 11. Not run or not done at this publish

1. **Modal** (`modal_v351_c71`, 8 GB cap; coarse=2 fallback queued) -> periods for Mechanical (pintle / linkage, forward-closure equipment, nozzle on the J1 lip, Pc port) and the FA-1 column selection. Previous full-L1 attempt was killed at the 6 GB cap.
2. **F2 cone poses** (9, with GM-01/02 lever-root R3 balls) -> S-3D on v3.5.1 in `hub/04-fea/s3d_v351/` (post script `post_s3d.py` written and tested).
3. **F3** K range over the cone poses (incl. neutral) and the compliant stop045 pose.
4. 7.2 moment-closure path not identified.
5. LC3 hot bound on the refined lever-root meshes (only the L1 bound exists; refined values in 4.6 are cold).
6. Thermal FE of the gimbal / bay (60 degC ASSUMED); TC-02 T-F1 / T-F2 (Mechanical / founder); NZ-03 N-F1 (founder); LC-TB70 is Mechanical's (216 (4)).
7. Datasheet checks: HK0808 C0, PTFE washers, J-FWD / M5 / M3 screw allowables.

## 12. Files (sha256/16 of every file in MANIFEST.json in this folder)

- `tables/`: part margins, ICD, LC3 summary, F4 tables (asm v1.2). `tables_legacy_v1.1/`: interim tables.
- `results/`: post-processing JSON on asm v1.2 (LC1, FA-1 incl. FA1T, LC3 x 8 poses, GM-02 refinements and edge metric, hot bound, compliant airframe, convergence, TB1 thread variant, free-body checks, v1.1-vs-v1.2 comparisons, stiffness, F4). `results/legacy_asm_v1.1/`: interim JSON kept as evidence.
- `figs/`: F1-01 LC1 B1_1 MS overall; F1-02 LC1 B1_21.65 vM; F1-03 NZ-01 throat MS; F1-04 TB1 zoom vM B1_19; F1-05 FA1S MS overall; F1-06 FA1S TC-01 J-FWD zoom vM; F1-07 LC3 stop045 MS overall; F1-08 GM-02 lever-root section vM (L1 mesh); F1-09 GM-02 lever root refined R3 vM; F1-C1 part margins; F1-C2 airframe holes; F1-C3 convergence. Each title gives case and criterion; colour bars give units; footer gives CAD, tool, asm version.
- `tests/conn71/`: connector test models (7.1 evidence).
- `runs/`: model, mass and pressure metadata of the v1.2 L1 run; queue and chain log.
- `src/`: scripts, for reproduction. Solver bulk stays in `/home/claude/work/fea3d/runs` (not published).
