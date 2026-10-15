# PROGRESS v3.5.1 (Mechanical successor session, 2026-10-13)

Resume file for a successor. Hub = /home/claude/work/shared-fallback/engine (interfaces/, 03-cad/, 04-fea/). Work = /home/claude/work/mechanical/.
Task list: CHANGELOG 182 (M1-M8) + 183 + 184 (mass critical) + 186 (OI-37, OI-32, NZ-01 refutation) + REV-MECH-1 / lead 188 (priority list
from the coordinator: 1 RM1-01, 2 RM1-02, 3 RM1-03/04/18/19 contact FE, 4 RM1-12 hardware BOM + 0.20 kg allowance, 5 RM1-05 convergence + M63
groove radius + SCL, 6 RM1-06 time-at-temperature + 7075 T table + case at 448.15 K, 7 RM1-10 SF rule, RM1-11 tables + carbon-phenolic
tension, RM1-09 DC-D + modal DLF, RM1-13 docs, RM1-16 Ansys deck label) + lead 194 (FA-1 period domain; modal closure list; FA1S 151 bar
design case for pressure-loaded paths until periods shown; J-FWD restated at 93 bar; thrust 1.8 kN x 4 ms only T <= 20 ms, long-period
spectrum for T > 20 ms into the airframe reactions; mechanical.json v2.2 FA-1 entry with the period domain; OI-32 outlet in CAD/BOM or MISSING).
A NEW FEA AGENT owns RM1-07/08/14/15 + the 3D headline model (writes hub 04-fea/assembly3d/, 04-fea/s3d_v351/). Tell the coordinator the
v3.5.1 geometry paths at freeze. Report line 194 items in the handback.
Rules: kill by PID only; nice heavy runs; one heavy solver at a time; never write /mnt/project-files; append-only CHANGELOG; do not edit hub/reviews.

## Code layout
- DEV tree (runs make_all): /home/claude/work/mechanical/v351/engine/03-cad/src (calcs inside src/calcs), 04-fea/{src,thermal,structural}.
  Reference copies in the dev tree: 03-cad/massprops_v3.5.json (8c11e1e136fc59d8), interfaces/mechanical.json (v2.1 e4d3e7c9df529171).
- HUB sources ported 16:28Z (old versions archived in hub 03-cad/src/history/<file>.<sha16>, 04-fea/src/history/engmat.py.7909d9c292bad06e):
  03-cad/src checks/config/make_all/parts_bleed/parts_engine/parts_feed/parts_gimbal, 03-cad/calcs bay_wall_v351/hardware_v351/
  mass_variant_v351/mass_delta_v351, 03-cad/src/data/hardware_v351.json, 04-fea/src/engmat.py (v1.6: SS-A4-80, FFKM, COPPER, GlidCop DATASHEET).
  NOTE hub make_all cannot run in place (src has no calcs/ package; build imports calcs.inlet_e1m): run from the DEV tree, then sync outputs.

## make_all v3.5.1 attempt 3 (RUNNING, driver PID 16164 / make_all 16166, from 17:09Z)
- Attempt 2 (PID 5407/5409) killed 17:04Z: BL-02/FD-01 47.8 mm3 (spot face not cut) + GM-03/GM-06 0.5 mm3 x2 -> parts_bleed FD-01 spot face
  Ø11 cut; parts_gimbal HK0808 flat land + cut at the washer seat (v351/hw/test_freeze_fix.py, test_gm06.py: zero common volume).
- Attempt 3 chunk A: 111/111 round-trips, asm/GLB PASS, bay sweep fail [], checks neutral + alpha+ 0 non-whitelisted (17:29Z).
- OLD header kept: (detached driver PID 5407 / make_all 5409, relaunched 16:36Z)
- Attempt 1 (PID 4057/4059) killed 16:35Z: GM-01 STEP round-trip FAILED (dV/V 1.74e-4, fillet retry path R 1.5 -> 1.2).
  Fix: config.V5C_LEVER_V351 R_side 1.2 for both halves (direct build). Log kept as make_all_v351_A_attempt1_SUPERSEDED_GM01_roundtrip.log.
- Attempt 2 chunk A 16:40Z: parts 111/111 STEP round-trips PASS; assembly neutral/stop045 PASS; GLB 148 PASS; bom/mass done.
- script /home/claude/work/mechanical/v351/run_make_all_v351.sh; logs /home/claude/work/mechanical/runs/make_all/make_all_v351_{A,B,C}.log
  + make_all_v351_driver.log (MAKE_ALL_V351_DONE at the end). Outputs in the DEV tree 03-cad/ (parts, assembly, drawings, checks, BOM, massprops).
- Chunk A: build,parts,assembly,glb,bom,mass,drawings,checks(neutral, alpha+-, beta+-) + bay-wall sweep; B: combined*, stop000, stop045;
  C: stop090..stop315, stopFD07B + readme.  After DONE: re-run `make_all.py --stages bom,mass,readme` (README results then carry bom/mass),
  then sync dev 03-cad outputs to hub 03-cad/v3.5.1/ (do NOT overwrite hub 03-cad/parts: the FEA agent uses the v3.5 files) + MANIFEST.
- make_all v2 changes: CAD_VERSION v3.5.1, BUILD_OVERRIDES = config.V351_ON; checks merge chunks by build fingerprint; bay_wall_sweep +
  fixed_wall_check in checks; < 3 mm pairs classified (CLOSE_DISPOSITION); BOM categories (FLIGHT/HARDWARE/GSE/PROVISION/CONTINGENCY),
  hardware lines from data/hardware_v351.json, OI-32 ENG-TK-OUT provision line = MISSING; massprops with hardware carried as max(0.20, CALC)
  at host parts + states_without_hardware + evidence classes + deltas vs v3.5 and mechanical.json v2.1; README v3.5.1.

## v3.5.1 geometry changes (config.V351_ON)
- RM1-01 BL-02 inward + BL-03A/E re-route; HK0808 bearings; FD-11 tab on bore; GM-01/02 root sector + fillets; TC-03 TB1 + GlidCop AL-15;
  J-FWD taps drill 4.2 x 9.0 / M5-6H 8.0 full thread (M5 x 10 ISO 7380-1 A4-80, 6.83 engagement; v3.5 6.5 deep bottomed an M5 x 10).
- Dev bay sweep on V351_ON (v351/bay/bay_wall_v351_full.json): moving fail [], fixed fail [] (BL-06 whitelisted), worst GM-01/02 66.902.

## Results so far
- Hardware (RM1-12): 55 lines / 161 items, CALC 0.2239 kg (engine 0.0585, fixed 0.1629, horn 0.0019, ring 0.0006) > 0.20 kg allowance;
  10 lines without mass. Carried in massprops as max(0.20, CALC) = 0.2239 kg at host parts. Tell lead: CALC exceeds the allowance.
- Mass (dev test, mid): CAD-only vs v3.5: engine -2.0 g, fixed -10.0 g, ring -11.9 g, all -23.9 g; with hardware all +0.1999 kg;
  engine mid 2.7911 kg CG (-2.377, 0.905, 0.551) mm.
- Thermal full runs DONE (tag v351_TB1GC): B1 TC-02 160.3 C / TC-03 209.4 C / NZ-04 733.0 C(!) / TC-09 729.9 C; A1 TC-02 122.9 / TC-03 189.3 /
  NZ-04 577.1 / TC-09 570.7 C. (v3.5: TC-02 245 C TB70, TC-03 IN718 710.7/819.5 C.) NZ-04 B1 733 C > 627 C criterion: M2c open.

## Items
- [x] RM1-01 / RM1-02 / FD-11 (dev + hub sources); freeze pending make_all.
- [~] RM1-12 hardware lines + allowance (in make_all). Open: DATASHEET masses; thread-strip check per line.
- [~] M1 182 (1): design TB1 + GlidCop; NEXT: SAX v3.5.1 linear + contact with thermal tag v351_TB1GC, classification, shakedown, LCF.
- [ ] M4 / 182 (6) joints.py J-FWD A4-80 at 93/102 bar + FA1S 151 bar (lead 194; A4-80 entry in engmat v1.6 done).
- [ ] 194 modal closure list (pintle/servo linkage, FS-01/MV-P + bleed valves, nozzle on J1 lip, Pc port + sense line, J-FWD + closures).
- [~] SAX v3.5.1 L1 (sax PID 4793, run dir runs/structural/L1_thv351_TB1GC_cad351, logs runs/structural/logs/{solve,post}_L1_v351.log,
      script v351/run_sax_v351.sh; sax.py dev changes: SAX_CAD=v351, FA1D 93 bar, SF_RULE_188, B1 soak states, n/a print; NOT yet in hub).
- [ ] RM1-03/04/18/19 contact FE; RM1-05; RM1-06; RM1-10; RM1-11; RM1-09; RM1-13; RM1-16.
- [ ] M2c NZ-04 (B1 733 C); NZ-01 capture argument; OI-37/OI-32 mechanical.json v2.2; V5c stiffness publish; M6; M7; mass list.

## Log
- 15:15Z BASE/TB1 screens; 15:33Z run 6 ended; 15:35Z BL-02 -4.5 g, HK0808 -21.9 g (v351/mass/).
- 16:05Z hardware census (v351/gm/hw_census_raw.json, v351/gm/hw_sentences.txt, v351/hw/hole_census_v351.json).
- 16:20Z engmat v1.6; hardware_v351.py; J-FWD tap depth fix; make_all v2; 16:28Z port to hub; 16:30Z make_all v3.5.1 launched.

- 16:33Z S-AX v3.5.1 run INVALID (re-used v3.4.1 rev B mesh): outputs renamed *_SUPERSEDED_v341mesh, run dir deleted (disk);
  sax.py reuse filter by CAD version; valid run 16:55Z results/*L1_thv351_TB1GC_cad351_v1.* (mesh b780ed547ad8f3ba).
- 16:5xZ disk relief: runs/ARCHIVE_MANIFEST_20261013.json (xz of superseded solver files, 1.93 GB freed, reported to main).
- 17:1xZ provenance (lead): v351/prov/{section_compare,dz_check,prov_runs,thermal_geom_compare}*.json; finding so far: no CAD-version mix
  in the v3.5 tables (thermal section = structural within section-angle features TC-04/TC-09/TC-01); L1_TC09IN718_v1 = TC-09 IN718
  structure on a 316L thermal field (screening, superseded by ..._thJ1revB_TC09IN); NZ03ZIRCONIA = 316L TC-09 map + J2 thermal.
- 17:30Z lead 203/204 interim sent to main: Pc port (070BG cannot meet 1 ms; CC-1 0.82-0.99 ms needs a miniature seat transducer
  <= 20 mm3; CC-2 passage <= 30 mm robust), transducer seat temperature (A1 33.8 C at RELIGHT, soak 83.8; B1 118.3), mass status.
  Files v351/pc/. TODO: ENG-PC-01 PROVISION line in make_all BOM; ranked mass list; massprops freeze note to main.

## 17:4xZ-18:0xZ status (successor, after context compaction)
- Lead 206 decisions received: (1) freeze v3.5.1 as built [freeze note sent, massprops 488b47f9d55ff91b]; (2) v3.5.2 with conditions
  (a) TC-09 thinning only if the re-run meets 183 (1) + 194 period domain, (b) Ti-6Al-4V screws non-wetted only (supplier datasheet,
  preload over soak on Al joints, anti-galling, no Ti where N2O leak/decomposition products can impinge), (c) 316L->6061 only upstream of
  the MV, (d) BL-07 pocketing; deliver a mass-delta file + a second massprops (P2 sensitivity); (3) Electronics picks transducers;
  (4) two bleed valves in series, keep searching <= 0.15 kg; (5) gimbal pocketing deferred; (6) rejections stand; (7) TC-02 (TB70 ult -0.15,
  LC2 ult -0.02) and NZ-03 (TB70 -0.16) classified under 183 (1)/RM1-03 with a fix proposal.
- v3.5.1 part set PUBLISHED: hub 03-cad/v3.5.1/ (parts 111 STEP+STL, assembly STEP x2 + GLB + manifest + placements, BOM json/csv,
  massprops) + MANIFEST_v3.5.1.sha256 (230 lines, sha256/16 b62c0e0ac8555fb8); sent to main.
- v3.5.2 isolated tree /home/claude/work/mechanical/v352/engine (copy of the dev v351 tree; dev v351 src untouched while make_all runs).
  - config.V352_ON = V351_ON + tc09_barrel_wall 0.0018 + tc09_socket_R2 0.0345; parts_engine TC-09 keys (barrel radial wall over the
    61.06 bore; socket OD 69.0 from 2 mm above the gland groove, 45 deg step, flats 68 A/F now 11.7 mm wide).
  - v352/checks/test_tc09_v1.json: TC-09 IN718 0.59235 -> 0.51434 kg (-78.0 g CALC), valid solid; engine group wet 2.69774 -> 2.61973.
  - (d) BL-07: v352/checks/bl07_pockets_v1.json manifold 74.94 g (pads 60.73); only 1.98 g free without the valve sub-base + P_mid port
    -> NOT implemented, re-assessed at valve selection.  (c): only FD-12F (13.5 g 316L) is upstream of the MV -> ~9 g, below threshold.
  - sax.py (v352 tree) SAX_CAD=v352 (CADTAG _cad352, geom_v352, V352_ON, SF rule 188 (9), FA1D 93, B1 soak instants from its envelope).
  - CHAIN RUNNING: /home/claude/work/mechanical/v352/run_v352_chain.sh (driver PID 28269, from 17:53Z): thermal B1 -> A1 (tag v352_TC09,
    logs v352/logs/full_*) -> gate v352/SAX_READY (set) -> S-AX L1 (logs v352/logs/{solve,post}_L1_v352.log; run dir
    runs/structural/L1_thv352_TC09_cad352; tables in v352 tree 04-fea/structural/results/*_cad352_v1.*).
- make_all v3.5.1 attempt 3 still running (17:47Z: chunk A checks beta- after alpha+/alpha-/beta+ all 0 non-whitelisted).
- 18:2xZ v3.5.2 MASS SENSITIVITY published: hub 03-cad/v3.5.2/ massprops_v3.5.2.json 8f887d83896aa7dd, massdelta 7e1726c9d9c0dfe5,
  data/hardware_v352.json (v1 d49e602d184ce8ba -> v1.1 8fd2cc8a3dea3bc1: Loctite 222 on HW-115 EL-03 M2, lead request; v1 in history/),
  MANIFEST_v3.5.2.sha256 652d1c25bcfd5f3c.  -91.6 g (TC-09 -78.0 conditional; Ti HW-121/123 -13.6).  CHANGELOG lines 210 (v3.5.1 freeze +
  part set) and 211 (v3.5.2 sensitivity) appended.  Ti analysis v352/ti/ti_screws_v352_v1.json (d190f4b97a78fcc4).
- Lead after 209: Ti R3 stays 100 mm (50 mm declined); HW-126 -> ICD-AIRFRAME discussion; thread locker for EL-03 (done v1.1);
  v3.5.2 stays SENSITIVITY; NEXT ORDER: (1) TC-02/NZ-03 classification + fix proposal (206 (7)); (2) remaining pose-check results;
  (3) full v3.5.1/v3.5.2 handback with the mesh/CAD/material provenance table.
- 18:2xZ TC-02/NZ-03 classification sent (hub 04-fea/structural/results/tc02_nz03_classification_v1.json 24354d74777786d7; v3.5.1 S-AX
  tables published to hub results/*_thv351_TB1GC_cad351_v1.*). NOTE: message said TC-02 part max 159.7 C for LC2: correct value 159.2 C.
- Lead 212 (b049fbd67a554c8b): TC-02 do T-F1 (sourced short-time 6061-T6 allowables) + T-F2 (contact FE of the seat; RM1-03); if either
  fails T-F3 is the design change. NZ-03: N-F2 INTO v3.5.2 (R1.0 NZ-01 shoulder edge + 0.25 mm graphite foil), re-run thermal + S-AX;
  N-F1 to the founder test list (>= 23.7 MPa at >= 1300 C, or >= 18.8 MPa if contact FE puts the peak near the mean). Both negatives
  SHOWN AS FOUND. ORDER: pose checks -> T-F2 contact FE -> full handback (with open-item list + owners + provenance table).
- 18:22Z v352 chain driver 28269 killed by PID (A1 TC-09-only not needed); B1 TC-09-only (python 28272 / ccx 28590) left to finish
  (tag v352_TC09 = TC-09-only sensitivity). New v3.5.2 chain (TC-09 + N-F2) to be launched after N-F2 CAD + contact FE.

## 18:3xZ status
- Lead line 213: Gaspar lowered the A1 apogee target to ~210 m; B1 still governs thermal sizing; A1 cases unchanged, no new case, no
  re-run.  Handback must state the A1 target as ~210 m.
- B1 TC-09-only sensitivity finished 18:31Z (ccx 2213 s): runs/thermal/DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_TC09 (envelope.json
  2389916722e456f9, summary.json d546f96c4672b2f3).  vs v351_TB1GC: TC-09 729.9 -> 736.1 C (+6.2 K, soak 70.7 s, peak moves z -210.84 ->
  -215.44), NZ-04 733.0 -> 735.2 C, TC-04 118.2 -> 118.3, all others unchanged (SIM).  Sensitivity only (no N-F2).
- Pose checks: chunk B running (combined045 0 non-whitelisted, 810 s; combined135 0 non-whitelisted, 719 s); ~12-13 min/pose; chunk C
  (7 poses) after B -> MAKE_ALL_V351_DONE ~20:45Z.
- T-F1 (sourced short-time 6061-T6 allowables): NOT OBTAINED.  Searched MIL-HDBK-5J (Fig. 3.6.2.1.1, everyspec), NASA-CR-123772 (Muraca &
  Whittick 1972, Fig. 7.4131-7.4133), NACA TM-1419 (Stickley & Anderson 1956, 6061-T6 rod at 300/400 F), Kaufman 1999 (NIST MDR
  hdl 11115/180), Summers et al. 2015 Fire Sci. Rev. 4:3: the values are figures or untexted scans; WebFetch returns no numbers and
  direct downloads (curl) are refused by the egress proxy (403).  Engmat stays at 260 MPa x ASM 10 000 h typical ratio.  Acceptance numbers
  for whoever reads the handbook: Ftu(149 C) >= 199.0 MPa (ratio >= 0.765 of 260) and Ftu(181 C) >= 171.8 MPa (>= 0.661), exposure basis
  = cumulative life time above 150 C.  -> founder/handbook action + hot tensile test option on the founder test list.
- T-F2 contact FE launched 18:4xZ: v351/contact/sax_contact_tc0203.py (C3 mu 0.2 / C4 mu 0.6, thread interlock kept, radial contact
  on the shank, contact + friction at flange and tap bottom; C1/C2 axially-free shank not run: non-physical, free body in thermal step).
  First run C3 TB70 (PID 7644, nice 15), log v351/logs/contact_tc0203.log, out runs/structural/contact_tc0203_cad351/.
