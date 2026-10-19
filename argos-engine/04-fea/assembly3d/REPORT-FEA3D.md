# ARGOS H1 engine - assembled-engine 3D FE (FEA3D, F1) - INTERIM

| | |
|---|---|
| Status | **INTERIM 2026-10-19** - F1 results solved and post-processed so far. Convergence level R3, compliant-airframe runs, GM-02 lever-root refinement, modal, F2 cone poses, F3 and F4 are still open (section 9). |
| Author | fea3d (successor Senior FEA analyst 3D), lead brief CHANGELOG 188 + successor brief 2026-10-15 |
| Configuration | CAD v3.5.1 frozen (CHANGELOG 206): MANIFEST `b62c0e0ac8555fb8`, ENGINE STEP sha16 `4ca22820c796b670`, 5.40921 kg wet |
| Tool | CalculiX 2.21 (SPOOLES direct), C3D10 tets (gmsh 4.15 HXT), own Python pre/post (`src/`) |
| Units | SI; mm, N, MPa, degC in the report where conventional. MS = allowable / (SF x stress) - 1 |
| Tags | SIM (FE output), DERIVED (computed from SIM/data), ASSUMED, DATASHEET, LITERATURE, TO-VERIFY, AS RECALLED |

> **Not physical approval.** A converged solution, matching numbers or clean plots do not approve hardware. Negative margins are reported as found; no margin has been forced.

## 1. Claims (checkpoint, SUPERVISION-WORKFLOW)

1. **LC1 (steady max thrust, hot, 4 S-AX thermal states):** negative total-stress margins [SIM] at **NZ-01** graphite throat -0.435 (B1_1; s3 = -69 MPa at 1330 degC, thermal-dominated; S-AX -0.443, 3D reproduces S-AX within 2 %), **TC-03** GlidCop flange corner -0.312 / -0.375 (y/u, B1_1; 98 % thermal = secondary; primary-only +7.8; P+Q 2Fty +1.06) and **TC-02** TB1 seat ultimate -0.119 (B1_19; yield +0.096; 98 % thermal; part at 159 degC > 150 degC T_limit). All other parts positive at LC1.
2. **TC-03 over-constraint check done:** TB1 tied on the thread only (no shoulder / end-face tie), refined mesh: TC-03 -0.259 / -0.327 at the same corner [SIM]. The over-constraint hypothesis is **refuted**; the negative is a thermal (secondary) total-stress finding.
3. **FA-1 (CHANGELOG 194 period domain):** FA1S bound (151.04 bar abs) gives **TC-01 J-FWD screw hole -0.221 / -0.160** [SIM], converged (303.0 MPa L1 vs 302.6 MPa R2). TC-01 is positive under FA1Q / FA1D / FA1U (+0.29 / +0.25 / +0.23 u). Which FA-1 column governs depends on the forward-closure modal period (modal not yet run). FA1T (3.6 kN thrust spike): all gimbal parts positive, min GM-03 +1.49.
4. **LC3 (8 deg stop, 8 stop azimuths x 64 sub-cases, cold):** lever roots govern: **GM-02 +0.182 / +0.018** (stop045), **GM-01 +0.206 / +0.039** (stop315), rod at the 609 N stall limit; NZ-03 +0.194. Hot lower bound (sub-additivity): **GM-02 +0.128 / -0.028**, GM-01 +0.190 / +0.026. The lever-root peak sits next to sliver tets: refinement pending.
5. **Airframe interface (16 x M5), rigid airframe:** max screw shear per hole LC1 75 N, FA1S 554 N, FA1T 642 N, LC3 890 N [SIM]; sum on airframe LC1 Fz 345 N, FA1S 3065 N, FA1T 3600 N, LC3 |F| <= (323, 323, 501) N, |M| <= 23.0 N m.
6. **Open model defect found in this interim (section 7.1):** in unit load steps the inner-gimbal bearing bushings whose springs end on rigid-body reference nodes carry only 56-79 % of the engine load (spring-force free body not closed), while bushings on RBE3 reference nodes (washers, J-FWD) close. Until explained, **bearing loads, rod forces and the LC3 runaway force derived from spring elongation are TO-VERIFY**, and so are the gimbal-path stresses (GM-01/02/03).

## 2. Configuration

### 2.1 Model
- Geometry: CAD v3.5.1 neutral STEP, 23 meshed bodies (engine frame mm, +Z forward, pivot at the origin): TC-01 case, TC-02 forward closure, TC-03 GlidCop seat insert, TC-04, TC-09 IN718 aft closure, NZ-01 graphite throat, NZ-02/NZ-03 carbon-phenolic, NZ-04 flexible-graphite seal, FD-01, PD-01R/PD-01S, GM-01/GM-02 (engine levers), GM-03 ring, GM-08a/b bearing housings, GM-09/GM-10 airframe brackets, GM-13/GM-14 servo brackets, GM-16a/b horns. Boolean sliver faces defeatured with OCC (GM-01/02, TC-04; dV < 1e-4 mm3).
- Mesh: level 1 (L1) 171,123 nodes, 18,340 constraint equations; pose runs (LC3) engine pressure parts at level 2, others L1 (133.6k nodes); convergence R2 / R3 by gmsh ball refinement at the governing points (R2 178,989 nodes).
- Masses: model group masses engine 2.886 kg, ring 0.217 kg, fixed 0.971 kg, horns 0.029 kg [DERIVED] (massprops ledger wet: engine 2.874, ring 0.217 [DATASHEET v3.5.1 massprops]); 1.31 kg of airframe-wall equipment (fixed group) is outside F1 (goes to F4). Grain and liner mass only. Pc transducer **ASSUMED 26 g** on the NPT seat (CHANGELOG 205; no part data yet).

### 2.2 Interfaces
| Interface | Model | Stiffness / tag |
|---|---|---|
| Threads / inserts (TB1, TC-09/TC-01, NZ-04 lip) | tie, rule 'zt' (axial + tangential), design variant | bonded, ASSUMED |
| TB1 variant | 'thread' only (shoulder + end face free) | over-constraint check (4.2) |
| Other contacts (GM-01/02 to TC-01 bore, bolted flanges, nozzle stack) | bonded ties | ASSUMED (stiff bound) |
| Gimbal pins | rigid connectors on pin and seat bores | ASSUMED rigid |
| HK0808 needle cups | radial bushings (2 dirs) | 128,258 / 149,912 N/mm, Palmgren line contact [DERIVED] |
| PTFE thrust washers | axial bushing, locating on +Y (inner) / +X (outer) only | 1e6 N/mm [ASSUMED] |
| Push rods | SPRINGA between rigid horn eye and lever eye | k_chain 11,418.2 N/mm [DERIVED from mechanical.json chain]; servo output rigid |
| J-FWD (8 radial screws TC-01/TC-02) | RBE3 bushings (3 dirs) | screw stiffness [ASSUMED], see model.json |
| PD feet | RBE3 bushings | 1e4 N/mm [ASSUMED] |
| PD-02 | rigid connector (not meshable) | ASSUMED |
| Mass items (25 + hardware) | RBE3-distributed nodal loads | DATASHEET masses |
| Airframe 16 x M5 holes | rigid (this interim); compliant variant queued | k_af 2e3 / 2e4 / 2e4 N/mm radial / tangential / axial [ASSUMED] |

Small fasteners are connectors with the stated stiffness, not meshed; the bodies see them through the connector patch, so stresses within about 1 mm of a patch are idealisation-dependent and excluded from the "regular" set (2.4).

### 2.3 Loads
| Case | Definition | SF | Tags |
|---|---|---|---|
| **LC1** | Pc 25.01 bar on the operating pressure distribution (vacuum outside) + manifold 70 bar + 4.04 g axial + 0.61 g lateral (4 directions, envelope); thermal field mapped from S-AX at B1_21.65 / B1_19 / B1_2 / B1_1 | 1.5 yield / 2.0 ultimate at node temperature (188 (9); 183 (1)) | Pc, manifold DATASHEET (S-AX LC1); g SIM (gnc.json v3.1) |
| **FA1Q** | 90 bar abs (T <= 0.1 ms paths) + manifold 70 bar, A1_22.2 relight thermal state | 1.0 | CHANGELOG 194 |
| **FA1D / FA1U** | 93 bar yield / 102 bar ultimate (0.1 < T <= 1 ms paths) | 1.0 | CHANGELOG 194 |
| **FA1S** | 2.0 x 75.519 = 151.04 bar abs (T > 1 ms paths, interim DLF 2.0 bound until the modal closure) | 1.0 | CHANGELOG 194 |
| **FA1T** | 90 bar shell + unit thrust scaled to 3600 N total (1.8 kN x 4 ms x DLF 2.0), gimbal / mount parts only (T <= 20 ms) | 1.0 | CHANGELOG 194 |
| **LC3** | engine at the 8 deg stop at 8 azimuths (0..315 deg): OP x Pc_max + 6.29 g lateral (8 dirs) + axial {0 static fire, 5.43 g} + 79.28 rad/s2 about the axis maximising the into-stop moment (both signs) + bumper force {0 hold, fb_run}; fb_run = largest bumper force with actuator moment into the stop <= 41.14 N m AND |rod force| <= 609 N; 64 sub-cases per pose. **Cold** (no thermal / manifold stress), allowables at B1_21.65 node T | 1.5 / 2.0 | g, rad/s2 SIM (gnc.json v3.1); 41.14 N m, 609 N DERIVED (mechanical.json v2.1) |
| **LC3 hot bound** | thermal-pressure field of LC1 (TH + OP Pc_max + PM 70 bar, no LC1 inertia) + LC3 increment, combined by von Mises sub-additivity / Weyl (brittle) | 1.5 / 2.0 | DERIVED lower bound on the margin |

Superposition of unit steps (TH, OP, PM, GX, GY, GZ, EAX, EAY, R1, R2, BUMP, TZ), linear elastic, small displacement. OP unit step net axial force 202.92 N/MPa [SIM] (2.501 MPa -> 507.5 N); S-AX 197.52 N/MPa (+2.7 %, aft-face faceting, TO-VERIFY by refinement); ideal ~214 N/MPa [DERIVED].

### 2.4 Criteria and node sets
- Metals: MS_y = Fty(T)/(1.5 vM) - 1 and MS_u = Ftu(T)/(2.0 vM) - 1 (LC1, LC3); SF 1.0 for both in FA-1. Allowables from materials v1 (hub 04-fea/materials) at node temperature; bay structure 60 degC [ASSUMED, TO-VERIFY].
- Brittle (graphite, carbon-phenolic): s1/St and s3/Sc with SF 2.0; char zone (T > T_char) primary s3 only; NZ-03 char strength 20 MPa [ASSUMED, CHANGELOG 212; founder test N-F1].
- Supplementary columns: primary-only MS and P+Q nodal shakedown MS (vM <= 2Fty).
- Regular node set: all nodes except those within 1.0 mm of tie-patch edges, RBE3 / rigid patches, re-entrant CAD edges and tets of quality q < 0.1. Margins are quoted on the regular set; the all-node minimum is kept in the JSON for traceability.

## 3. Per-part minimum margins (all SIM; full table with locations and temperatures: `tables/f1_part_margins.{md,csv,json}`; chart F1-C1)

| Part | Material | LC1 y / u (state) | FA1S y / u | FA1Q y / u | LC3 cold y / u (pose) | LC3 hot bound y / u | governing |
|---|---|---|---|---|---|---|---|
| NZ-01 | graphite | **-0.435** (B1_1) | +1.465 | +3.400 | +4.151 | **-0.443** | LC1 / hot bound, throat compression |
| TC-03 | GlidCop Al-15 | **-0.312 / -0.375** (B1_1) | +2.153 / +2.822 | +4.656 / +5.858 | +9.222 / +8.296 | **-0.357 / -0.415** | LC1 thermal-secondary |
| TC-01 | 6061-T6 | +1.380 / +0.913 | **-0.221 / -0.160** | +0.291 / +0.392 | +0.830 / +0.485 (stop270) | +1.276 / +0.830 | FA1S J-FWD hole |
| TC-02 | 6061-T6 | +0.096 / **-0.119** (B1_19) | +0.855 / +1.001 | +2.117 / +2.363 | +5.332 / +4.091 | +0.022 / **-0.179** | LC1 thermal-secondary, T > T_limit |
| GM-02 | 7075-T6 | +17.2 / +14.7 | +3.44 / +4.10 | +6.47 / +7.58 | **+0.182 / +0.018** (stop045) | +0.128 / **-0.028** | LC3 lever root |
| GM-01 | 7075-T6 | +12.5 / +10.7 | +2.44 / +2.95 | +4.78 / +5.64 | +0.206 / +0.039 (stop315) | +0.190 / +0.026 | LC3 lever root |
| NZ-03 | carbon-phenolic | +0.476 (B1_2) | +0.630 | +1.735 | **+0.194** (stop000) | +0.231 | LC3 |
| TC-04 | 6061-T6 | +1.010 / +0.634 | +3.11 / +3.45 | +3.11 / +3.45 | +6.48 / +5.06 | +0.558 / +0.266 | hot bound |
| TC-09 | IN718 | +1.230 / +0.935 | +1.637 / +2.144 | +2.78 / +3.51 | +11.9 / +10.6 | +1.123 / +0.841 | hot bound |
| NZ-02 | carbon-phenolic | +0.898 | +2.496 | +4.867 | +1.913 | +0.860 | hot bound |
| GM-16a / GM-16b | 7075-T6 | > +100 | > +30 | > +60 | +1.10 / +0.81 ; +1.08 / +0.79 | +1.09 / +0.80 ; +1.07 / +0.78 | LC3 |
| GM-03 | 6061-T6 | +13.1 / +10.4 | +1.90 / +2.11 (FA1T +1.49 / +1.68) | +3.87 / +4.23 | +1.365 / +0.908 | +1.361 / +0.905 | LC3 |
| PD-01S / PD-01R | 6061-T6 | +1.99 / +1.43 ; +2.60 / +1.92 | +2.70 / +3.00 ; +3.85 / +4.24 | > +4 | > +5 | +1.43 / +0.97 ; +1.81 / +1.28 | hot bound |
| FD-01 | 316L | +2.30 / +5.48 | +4.70 / +13.7 | +4.75 / +13.8 | +6.44 / +13.4 | +1.19 / +3.31 | hot bound |
| GM-13, GM-14, GM-10, GM-09, GM-08a, GM-08b | 6061-T6 | > +70 | > +13 | > +23 | +2.88 / +2.13 ; +3.08 / +2.29 ; +3.66 / +2.76 ; +5.96 / +4.61 ; +8.16 / +6.39 ; +17.5 / +13.9 | ~ LC3 cold | LC3 |
| NZ-04 | flexible graphite | +4.66 | +4.52 | +7.35 | +14.8 | +4.39 | - |

FA1D, FA1U and FA1T columns are in the full table (FA1T gimbal / mount parts only: min GM-03 +1.489 / +1.678, all positive).

## 4. Governing findings (decision 212 terms)

**4.1 TC-02 (forward closure, 6061-T6).** L1: +0.096 y / -0.119 u at B1_19, at the TB1 tie end (r 5.86, z 107.51), 159 degC; vM 102.4 MPa of which 100.8 MPa thermal [SIM] -> secondary stress (primary-only +3.45; P+Q 2Fty +2.29). The part reaches 159 degC (B1_19) against its 150 degC limit [SIM vs DATASHEET limit]: the temperature check (d) stays **open** per CHANGELOG 212 (path T-F1 sourced short-time allowables + T-F2 contact FE). Refinement (R2, section 5) moves the regular-set maximum 1.5 mm away from the tie end to (6.44, 0.9, 108.59) at 149 degC: +0.213 y with the same vM (102.1 MPa); the all-node value at the tie end grows with refinement (102 -> 147 MPa) = singularity of the tie termination, not a converged stress. The 'thread' TB1 variant gives +0.196 / -0.054 (B1_19) [SIM]. I do not report a converged TC-02 ultimate margin: it is between -0.12 and -0.05 on total stress, governed by the tie-end idealisation and the temperature-limit question (T-F2 contact model needed).

**4.2 TC-03 (GlidCop seat insert).** L1 -0.312 / -0.375 at B1_1, flange corner r 9.8 / z 105.51, 74 degC; vM 241 MPa, 237 MPa of it thermal. R2 refinement: -0.266 (226 MPa). Thread-only TB1 tie (refined): -0.259 / -0.327 (224 MPa) at the same corner, P+Q shakedown +1.22, primary-only +4.06. The over-constraint hypothesis is refuted (the thread variant changes the corner stress by < 1 %). The 3D P+Q shakedown margin (+1.22) is numerically close to the S-AX figure (+1.203); whether S-AX quotes the shakedown criterion is **TO-VERIFY with Mechanical**. TC-03: negative on total stress, positive on primary and on P+Q shakedown [SIM].

**4.3 NZ-01 (graphite throat).** -0.435 at B1_1 (S-AX -0.443); s3 -69 MPa at 1330 degC, thermal-dominated. R2: -0.454 (s3 -71.4 MPa). A primary design question (brittle, SF 2.0 on total stress) for Mechanical / Combustion; FE refinement will not remove it.

**4.4 NZ-03 (carbon-phenolic retainer).** LC1 +0.476 (B1_2), FA1S +0.630, LC3 +0.19 to +0.21 at all stop poses [SIM], on the **ASSUMED 20 MPa char compressive strength** with the R1.0 edge + 0.25 mm graphite foil (CHANGELOG 212); founder test N-F1 closes it.

**4.5 TC-01 (case) under FA1S.** -0.221 / -0.160 at the J-FWD radial screw hole (r 28.6, z 125.5), 46 degC. Regular-set vM 303.0 MPa at L1 (h 3.0 mm) vs 302.6 MPa at R2 (h 1.3 mm): converged (0.1 %); the all-node value at the RBE3 patch edge grows (357 -> 382 MPa, idealisation). The J-FWD screws carry 4.84-4.89 kN shear each (8 screws) [SIM], = head-end pressure load pi x 28.6^2 x 15.10 MPa / 8 = 4.85 kN [DERIVED]. FA1Q / FA1D / FA1U are positive (+0.29 / +0.25 / +0.23 u); whether FA1S (T > 1 ms bound) applies depends on the forward-closure modal period (not yet available), so the negative stands until then. J-FWD screw shear capacity and hole bearing against a fastener datasheet: TO-VERIFY (Mechanical, fastener selection).

**4.6 GM-01 / GM-02 lever roots (LC3).** Cold: GM-02 +0.182 / +0.018 (stop045), GM-01 +0.206 / +0.039 (stop315), at r 33.7 / z -6.9 [SIM]; hot lower bound +0.128 / **-0.028** and +0.190 / +0.026 [DERIVED]. In these sub-cases the rod is at the 609 N stall limit (mechanical.json F_rod_stop). Superseded but kept as evidence: before the stall limit was imposed, the 41.14 N m-only runaway gave GM-02 -0.003 / -0.140 (that definition over-drives the rod to 722 N). Not final, for two reasons: (a) the peak is next to L1 sliver tets (lever-root fillet, q 0.034); R2 / R3 refinements are queued (`pose_stop045_gm02r2/r3`); (b) the rod and bearing forces depend on the connector defect in 7.1.

## 5. Mesh convergence (partial: L1 and R2; R3 running)

`results/f1_convergence.json` (chart F1-C3 after R3). Same thermal map, ties and loads at every level; quantity = maximum over regular nodes within 3 mm of the governing point.

| Point | Quantity | L1 (h mm) | R2 (h mm) | change | MS L1 / R2 |
|---|---|---|---|---|---|
| NZ-01 throat, B1_1 | -s3 | 69.0 MPa (3.63) | 71.4 MPa (0.72) | +3.5 % | -0.435 / -0.454 |
| TC-03 flange corner, B1_1 | vM | 241.2 (0.98) | 225.9 (0.33) | -6.3 % | -0.312 / -0.266 |
| TC-02 TB1 tie end, B1_19 | vM | 102.4 (4.84) | 102.1 (1.21) | -0.3 % (location moves 1.5 mm) | +0.096 / +0.213 |
| TC-01 J-FWD hole, FA1S | vM | 303.0 (3.04) | 302.6 (1.28) | -0.1 % | -0.221 / -0.220 |

Richardson / GCI need the third level (R3: conv_r3; B1 states solved, A1_22.2 pending).

Cross-check against a hand calculation (TC-01 case mid-section z -60 mm, LC1 B1_21.65): FE Pm (vM, SCL) 20.29-20.36 MPa over 8 azimuths [SIM]; hand: Lame mean hoop p ri/t = 22.51 MPa, axial F/A = 9.87 MPa (FE section force 5936 N), radial -p/2 -> vM 20.59 MPa [DERIVED]; FE is 1.3 % below the hand value.

## 6. LC3 detail (8 stop poses, cold; `results/f1_post_lc3_pose_stopXXX.json`; SIM, but connector rows inherit 7.1)

| pose (stop azimuth) | fb_run range N | max rod force N | governing (regular) | moment-path residual |
|---|---|---|---|---|
| 000 | 382-479 | 494 | NZ-03 +0.194, GM-01 +0.594, GM-02 +0.644 | 2.8 % |
| 045 | 323-418 | 609 (ROD_2, limit) | GM-02 +0.182 / +0.018, NZ-03 +0.200 | 2.9 % |
| 090 | 384-478 | 598 | NZ-03 +0.206, GM-02 +0.263 / +0.088 | 2.6 % |
| 135 | 223-322 | 609 (ROD_1, limit) | NZ-03 +0.206, TC-01 +0.869 | 3.7 % |
| 180 | 317-416 | 609 (ROD_2, limit) | NZ-03 +0.201, GM-02 +0.643 | 5.2 % |
| 225 | 213-310 | 609 (ROD_2, limit) | NZ-03 +0.206, TC-01 +0.865 | 4.0 % |
| 270 | 365-459 | 597 | GM-01 +0.285 / +0.107, NZ-03 +0.206 | 2.6 % |
| 315 | 307-404 | 609 (ROD_1, limit) | GM-01 +0.206 / +0.039, NZ-03 +0.206 | 2.8 % |

Bearing envelope over the 8 poses (from spring elongation, see 7.1) [SIM]: inner needle cup 742 N (stop000), inner washer 724 N (stop090), outer needle cup 727 N (stop000), outer washer 800 N (stop180). For comparison: LC1 bearings <= 244 N; FA1S 1518 N; FA1T 1766 N, and 4036 N on one inner cup (affected by 7.1). Check against HK0808 C0 needs the datasheet value: **TO-VERIFY** (no value invented).

## 7. Open defects and unknowns

### 7.1 Connector free-body check fails on the inner gimbal bushings (found 2026-10-19, OPEN)
Sum of spring forces k x du on the engine side (inner bearing radial springs + inner washer + rods) vs the load applied to the engine, unit steps of `lc1v351_design_rigid` (B1_21.65) [SIM]:

| unit step | spring sum | expected | engine side carries |
|---|---|---|---|
| GX (+1 g) | X 22.39 N | 28.30 N (2.886 kg x 9.807) | 79 % |
| GZ (+1 g) | Z 15.88 N | 28.30 N | 56 % |
| TH (thermal only) | Z -4.20 N | 0 N | - |
| OP (unit Pc) | 200.0 N | 202.9 N | 98.6 % |
| GY (Y through the RBE3 washer) | 28.01 N | 28.30 N | 99 % |

These free bodies do close: the outer bushings carry engine + ring exactly in GX (30.45 N vs 30.43 N, through the outer washer, which ends on RBE3 references); the J-FWD bushings (RBE3 references) carry exactly the head-end pressure load; airframe reactions equal the applied totals (40.22 N per g). Checked: rigid-body fits of the pin and seat node sets are exact (0.01 nm residual); the spring and auxiliary-node equations are in the deck; no ties, rigid sets or RBE3 sets cross from the engine group to the ring group; no element references nodes of another body; ground nodes lie only on GM-09 / GM-10. Pattern: every path that does not close is a SPRINGA from a `*RIGID BODY` reference node to an auxiliary node whose translations are tied by `*EQUATION` to another `*RIGID BODY` reference node; the seat reference nodes report zero displacement in the .frd while their tied auxiliary nodes move.

Working hypothesis [TO-VERIFY]: CalculiX's handling of a linear `*EQUATION` whose independent term is a `*RIGID BODY` REF node (a nonlinear MPC) creates an unintended engine-ring force path. This would also explain the 2.6-5.2 % LC3 moment-path residual and the ~10 % EAX residual the predecessor saw in the nx run.

Consequences: bearing loads, rod forces, the LC3 runaway force fb_run, and K_alpha / K_beta from spring elongation are TO-VERIFY; the gimbal-path stresses (GM-01/02/03) may change. Pressure-part stresses (self-equilibrated inside the engine) and the airframe reactions (exact totals) are not expected to change, but the hole distribution is TO-VERIFY. Planned closure: a small CalculiX connector test, then a corrected bushing formulation (SPRING2 between coincident reference nodes, or RBE3 references), then re-solving the stop poses.

### 7.2 Other unknowns
Thermal map: non-S-AX parts at the 60 degC bay temperature [ASSUMED]. LC3 runs are cold, and the hot bound is a lower bound only (pose runs have no thermal step). Interface stiffness values marked ASSUMED in 2.2 (washers, PD feet, airframe compliant values, bonded contacts). No datasheet values for HK0808 C0 / C, M5 / J-FWD screw allowables or PTFE washer limits. NZ-03 char strength 20 MPa ASSUMED. TC-02 short-time allowables above 150 degC (T-F1). Pc transducer ASSUMED 26 g.

## 8. Airframe interface (ICD), rigid airframe (`tables/f1_icd_airframe.{md,json}`, chart F1-C2)

Screws are radial through the airframe wall: shear = hypot(tangential, axial Z); pull-out = radial outward. SIM.

| case | max screw shear N (hole) | max pull-out N (hole) | max push-in N | sum F on airframe N (|Fx|, |Fy|, |Fz|) | max |M| about pivot N m |
|---|---|---|---|---|---|
| LC1 | 75.1 (AF_GM09_4) | 19.9 (AF_GM09_0) | 8.2 | 24.5, 24.5, 345.0 | 1.16 |
| FA1S | 553.6 (AF_GM09_0) | 101.3 | 53.1 | 0, 0, 3064.9 | 3.34 |
| FA1T | 641.7 (AF_GM09_0) | 117.2 | 62.0 | 0, 0, 3600.0 | 3.24 |
| LC3 (8 poses) | 889.6 (AF_GM10_5) | 281.6 (AF_GM09_7) | 311.1 | 323, 323, 501 | 22.95 |

Long-period thrust spectrum for the ICD (CHANGELOG 194), linear scaling of the FA1T hole envelope with net thrust [DERIVED]: 1.76 kN @ 25 ms -> 314 N max hole shear; 1.45 kN @ 40 ms -> 258 N; 1.04 kN @ 100 ms -> 185 N. Compliant airframe (k_af ASSUMED) queued, to give the second bound the brief asks for.

## 9. Not yet run or not done (at this interim)

1. Convergence level R3 (A1_22.2 still to solve), then GCI and chart F1-C3.
2. GM-02 lever-root refinement (`pose_stop045_gm02r2`, `r3`).
3. Compliant airframe: `lc1v351_compliant`, `pose_stop045_compliant`.
4. Modal `modal_v351` (8 GB cap; coarsened if it fails), giving the periods for Mechanical (pintle / linkage, forward-closure equipment, nozzle on the J1 lip, Pc port) and the FA-1 column selection.
5. 7.1 connector defect: test, fix, re-run the gimbal-path cases.
6. F2: 9 cone poses -> `hub/04-fea/s3d_v351/`.
7. F3: K_alpha / K_beta range.
8. F4: secondary structure hand calcs.

## 10. Files (sha256/16 of every file in MANIFEST.json in this folder)

- `tables/`: part margins and ICD tables.
- `results/`: post-processing JSON (LC1, FA-1 incl. FA1T, LC3 x 8 poses, hot bound, convergence partial, TC-03 thread variant).
- `figs/`: F1-01 LC1 B1_1 MS overall; F1-02 LC1 B1_21.65 vM overall; F1-03 NZ-01 throat zoom MS; F1-04 TB1 zoom vM B1_19; F1-05 FA1S MS overall; F1-06 FA1S TC-01 J-FWD zoom vM; F1-07 LC3 stop045 MS overall; F1-08 GM-02 lever-root section vM; F1-C1 part margins chart; F1-C2 airframe hole loads chart. Each figure title gives the case and the criterion; colour bars give units.
- `runs/`: model, mass and pressure metadata of the L1 run; queue and log.
- `src/`: scripts, for reproduction.
- Solver bulk stays in `/home/claude/work/fea3d/runs` (not published).
