# ARGOS H1: Combustion and propulsion report (02-combustion)

Version 2.4a, 2026-10-13. Owner: Combustion and Propulsion. Interface: `interfaces/combustion.json` v2.4a (sha256/16 `5237d4584bad38c4`); v2.4 (`469727032124329f`) is kept as `data/v2/combustion_interface_v2p4_as_published.json` and v2.3 (`d9ec54fbf450e243`) as `data/v2/combustion_interface_v2p3_as_published.json`. Status: targeted revision v2.4a in answer to the independent re-review `reviews/REVIEW-COMBUSTION-R2.md` (REV-COMB-2, REVISE (targeted)) and to the lead decisions to CHANGELOG line 177. v2.4 of this report (`32e366bd78437dc0`), which answered REV-COMB-1, REV-GNC-1 and the Electronics SIL items, is archived as `02-combustion/superseded/v2p4/REPORT.md`. Digital only, *Por revisar*: the v2.4a changes await re-review. Companion files: `02-combustion/CF-4-SPEC.md` v2.0, `02-combustion/T1-T4-REGRESSION-SPEC.md` v2 and the item-by-item answer `02-combustion/REVISION-RESPONSE-R2.md`.

Tag legend:
- REQ: founder or lead requirement.
- LEAD: lead decision (CHANGELOG line given where it matters).
- LITERATURE: cited source; LITERATURE-UNVERIFIED or "as recalled" means quoted from memory and not re-checked.
- CEA: NASA CEA through RocketCEA.
- SIM: our simulation.
- FEA: Mechanical's finite-element results, used as delivered.
- DERIVED: calculation from tagged inputs.
- ASSUMED: engineering assumption with a stated band.
- TO-QUOTE / TO-VERIFY: open procurement or verification items. Prices are quoted to Sønderborg, DK-6400; none is set to zero or to a "from" price.

No number in this report is MEASURED. No hardware has been tested. A passing simulation, a matching hash or a correct user interface is not physical approval.

## 0. Checkpoint

**Claim.** The v2.3 design point stands: N2O/ABS hybrid, 500 N at Pc 25 bar (software cap), Dt 13.724 mm, eps 2.0, S230 straight-port grain, servo pintle with a normally-closed main valve (MV-P). The reviewer reproduced the thermochemistry, sizing, injector model, throat heat flux, floor separation and grain at n 0.5 to 0.1-1 %; that core is not repeated here. v2.4 added or replaced items 1-11 below, each with its evidence; v2.4a amends them in place and item 12 lists the patch (REV-COMB-2):

1. **Sequence and abort logic (RC-01; §7.3-7.5).** The relight follows the firmware v2.8 epochs (E0 T_fire, E1 torch confirmed, E2 main light, E3 steady). E1 needs P_torch AND the photodiode (2oo2) and the torch is supervised from E1 to E2 (FA-1 (a) and (b), REQUIRED of Electronics, LEAD line 164). Light windows W: 0.40 s at a flight first start, 0.65 s at a flight relight, 0.35 s on the stand. On an A1 relight with the bleed fitted, E1 also needs [closure confirmed OR the closure deadline reached], the deadline being <= the torch gate (LEAD line 166 (3)). A5 is deleted and replaced by the LIGHT_SPIKE record; A4 trips at 30 bar abs on the FILTERED channel for 5 ms (LEAD line 166 (4)); A14-A16 cover the bleed valves, the purge and the torch. MV closed in coasts; normal shutdown pintle-first, abort MV-first.
2. **Hard start (RC-02; §7.6).** Decomposition-only late light: head peaks 43.7 / 43.1 / 42.0 bar at a 15 / 20 / 25 C pad start with the sharp entrance, 40.6 / 40.1 / 39.3 bar rounded; 37.8 bar (36.7 rounded) at the A1 relight (SIM, `late_light_tables_v2p4.json`). MEOP 45 bar holds for that case and the rounded entrance is REQUIRED. The v2.4-draft 44.9 bar is superseded. A **fuel-assisted** fast part at a relight (FA-1) is published in v2.4a as an envelope over O/F 3-12 and burn times of 1-7 ms (896 cases; SIM on an ASSUMED construct; §7.6): head peak 83.0 bar abs (baseline: vapour once, rounded entrance) to 88.0 bar abs (upper bracket), aft 0.95-1.00 of the head, above MEOP 45 bar for <= 3.65 ms (4.45 ms), above proof 67.5 bar for <= 1.0 ms (1.3 ms), never above 90 bar abs. The v2.4 figure 48.9-75.5 bar (O/F 8 only) is superseded. MEOP is NOT shown for FA-1. The structural load is 90 bar abs quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a 1.8 kN x 4 ms thrust spike (LEAD line 173). FA-1 is an FMEA item, a single-control hazard accepted by the lead for design continuation only (§9.1).
3. **Relight with retained vapour (RG-01; §2.8).** Design basis (LEAD line 164): the coil re-route plus a pre-scheduled two-tap purge on the decided path (two equal 0.707 mm restrictors, Cd 0.70 ASSUMED, valves non-controlling), 2.5 s of flow ending at E0 - 0.05 s, PURGE commanded at E0 - 2.90 s, theta <= 2 deg, balanced or axial vent, no lining. Needed flow time 1.9 s (<= 1.94 s with the FD-01 element), P_abort 0 at W 0.65 s in 200 000 samples per case, N2O vented 34.3-72.9 g (plan <= 76 g), E0 -> E2 max 0.626 s on the worst purged state, so the 0.81 s plan holds (SIM, `rg01_line_states_v2p4.json`). The claim is gated by CF-4 (founders; `CF-4-SPEC.md`). v2.4a: the PURGE commit rule of LEAD line 175 (3) and Combustion's check of an unpurged start are in item 12 and §2.8.
4. **Stuck-open bleed (§2.8, §9.1).** 31.24 g/s with both taps liquid (upper bound); additive tank outflow governs (GNC S313). Two NC valves in series: a stuck-open path then needs two faults or one common cause, but the pair doubles the fail-closed probability (no purge, so no relight on that pass). Both go to the FMEA.
5. **Relight latency (RC-03; §7.7).** Latency distributions by line state are delivered to GNC (Table 2.15); the GNC re-fly runs on `rg01_line_states_v2p4.json` (`2939549811d4c381`).
6. **MEOP basis (RC-08; §3.6).** 44.33 bar at the 24 C interlock with the designed line loss and the conservative bands: margin 0.67 bar (1.5 %) to MEOP 45 bar; proof 67.5 bar keeps >= 21.9 bar (SIM). v2.4a: the interlock thresholds sit below 24 C / 55.28 bar abs by the total channel uncertainty, and CF-1 / CF-3 accept only a full-stroke Cd <= 0.80 and a line loss >= the model (LEAD line 172 (4); §3.6).
7. **Trapped volumes, relief and stored energy (RC-04, RC-05, RC-12; §2.7, §9.2, §10.2).** Relief on every lockable volume, with the set points in the interface block `relief_v2p4a` (LEAD line 172 (6)); stored energy of the flight tank 0.77 kg TNT equivalent by decomposition (6.9 kPa at 16.4 m), ground 15 L tank 4.0 kg (28.4 m) (DERIVED).
8. **Throat life (RC-06; §5.4).** Plan one insert per flight until T1/T4 bore data exist; the literature-kinetics case gives 0.38-0.60 A1 flights on the gnc.json v3 p99 cycle (SIM).
9. **Regression band (RC-07; §4.1, §4.6).** The whole band is run. ENG-06 (web >= 1 mm) holds on A1 and B2 and fails on B1 85 m at a x1.5 with n <= 0.5; "85 m covers 62 m" is withdrawn; B1 flies only under the lead's gating rule after T1-T4. v2.4a: the burden of proof is reversed (LEAD line 172 (3)); the T1-T4 specification v2 sets the law stations, the σ target and the errs-safe check (§10.4).
10. **Minor items.** eta_cf band 0.95-0.975 (RC-09; decided by LEAD line 170 (1): the 25 bar cap stays); L* 2.03 m on 300.9 cm3 (RC-16); Bartz curvature stated (RC-17); eroded-throat separation at constant mass flow (RC-18); seat insert TC-03 in Inconel 718 and the coast leak ceiling 0.0055 g/s (RC-02, RC-13 g); cleaning, drying and catch-volume rules (RC-14; §10.1); load-bearing material data still TO-VERIFY (RC-15).
11. **Nozzle joint (§6.5).** The NZ-03 mica/vermiculite gasket (900 C rating) sees 1595 C in Mechanical's FE: it fails by 695 K. Joint J1, CONFIRMED by the lead (CHANGELOG line 146): a 2.0 mm carbon-phenolic flange with a 0.5 mm flexible-graphite seal at the lip face. An unsealed joint leaks 0.83-1.10 % of the engine flow and could melt the 316L lip in 1.07-5.70 s (lumped bound); hence hazard H19 and an N2 leak check at 67.5 bar before and after every firing. [v2.4a: LEAD line 182 (4) treats the NZ-04 flexible-graphite seal as FAIL (577 C soak against a 450 C oxidising-service limit, as recalled) until a maker datasheet shows >= 627 C; otherwise Mechanical selects a datasheet-rated seal and re-checks the joint (OI-39).]
12. **v2.4a patch (REV-COMB-2; LEAD lines 166-177; the line-181 requests (2), (4) and (10)).**
    - E1 and A14 follow LEAD line 166 (3): closure confirmed OR the closure deadline (<= the torch gate) reached; at the deadline in flight BLEED_FAULT goes to the FC, V2 is commanded closed and the lift proceeds; on the stand it is an abort. A4 runs on the filtered channel for 5 ms (line 166 (4)) (R2-01; §7.3-7.4).
    - One stand safing rule after a no-light (LEAD line 172 (1); R2-02; §7.6, §10.2).
    - The FA-1 envelope and the line-173 load (item 2; R2-03; §7.6, §9.1).
    - The T1-T4 specification v2: reversed burden, law stations x/L 0.80-0.90, σ(S) <= 1.5 %, systematic terms and the errs-safe check on 78 B1 records (R2-04; §10.4).
    - Superseded interface values tagged and the `relief_v2p4a` block added (R2-05); vented-mass sentences corrected and CF-4 P4 defined per tap and per phase (R2-06); interlock guard band (R2-07); Table 2.15 rows relabelled (R2-08); J1, the lip goal, the segment heat and RC-09 aligned (R2-09); stand dynamic Pc channel, with flight LIGHT_SPIKE values at 1 kHz as lower bounds (R2-10); the FA-1 outflow-form sensitivity (R2-11).
    - **PURGE commit rule (LEAD line 175 (3), PROVISIONAL): PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge.** Line 164's "the FC delays T_fire" is withdrawn. Combustion's check (§2.8, `unpurged_start_check_v2p4a.json`, SIM/DERIVED): the branch "the relight proceeds unpurged" carries a hazard outside the abort model. In the PURGE NOT RUN LO worst state every light (P 0.758) is followed by the 23.4 cm3 vapour gap, 0-0.19 s after E2; the drogue-release term is already true at E2, and A3 then aborts in 0.712 of the starts (H20). Proposal: no commit by the deadline -> no relight on that pass. The lead decides (OI-31). **Line 181 (2):** LO or HI is not settled by analysis (both are ends of Mechanical's ASSUMED wall heat-transfer bracket; CF-4 generation runs and T4 measure it), and L* does not need it: at the worst PURGE NOT RUN states an unpurged start succeeds with P = 0 under LO (no light 0.242, A3 before the release 0.046, released then A3 0.712) and under HI (no light). Combustion recommends L* = 1.3 s (§2.8, Table 2.17).
    - Tank outlet coverage during PURGE: covered quasi-statically, with a large margin, if the outlet is on the aft bulkhead of an axial tank; the outlet geometry is MISSING (§2.4 note).
    - Tank outlet coverage on liquid depletion (line 181 (10)): the check already used the liquid left at the END of the PURGE flow (766.4 g minimum; 79.8-81.8 g depleted in the flow window, consistent with the 81.6 g liquid depletion), not the 73.0 g vented. Quasi-static coverage needs 13.6 mm of liquid, 78.6-82.5 g: about 9x below the minimum (§2.4).
    - **Cold-flow apparent thrust under the drogue (line 181 (4); §7.3, Table 7.3a; DERIVED).** After an undetected flame-out with Pc invalid, the open-loop pintle keeps N2O flowing. Bound (Cd <= 0.80, no line loss, isentropic equilibrium expansion to 1 atm, adiabatic; tank 283.15-289.5 K): 12.5-13.3 N with the command held at the 62.5 N start level, 35.6-37.5 N at 200 N, 117.7-119.9 N at 500 N and 181.5-206.5 N at the 4.0 mm stroke. Nominal HEM (Cd 0.70): 0.8-0.9 / 12.5-13.2 / 69.1-70.6 / 105.8-122.4 N. The cold flow alone exceeds the 37.16 N R2 threshold above about 200 N of command (bound) or 310-350 N (nominal), and heat pick-up from the hot chamber is excluded. PROPOSAL: hold the open-loop command at the start level while the drogue is attached with Pc invalid (OI-38).
    - GNC rev2 gives a specific-force angle of up to 2.71 deg during the purge flow, above the 2 deg purge basis: OPEN (OI-35; §2.8).

**Configuration.** CAD v3.4.1 (Mechanical: coil re-route, FS-01 module with MV-P, bleed taps T4 and FD-01); mechanical.json v2 (`4f024ed4ccb4618c`); gnc.json v3 (`3e97c378cfebee95`); electronics.json v2 (`da067408c1594814`) and firmware sequence v2.8; ENGINE-BASELINE v0; REQUIREMENTS rev 2; lead decisions to CHANGELOG line 177 (Mechanical bleed path line 162; Mechanical FA-1 margins line 176; GNC rev2 line 174, SIM, staged and under review REV-GNC-3). Mechanical status to line 179 (CAD v3.5 run 6 with TC-09 in Inconel 718 and the bleed modelled, line 178; mechanical.json v2.1 `e4d3e7c9df529171`, line 179) is quoted for status only: the v2.4a analyses stay on CAD v3.4.1. GNC `purge_outlet_inputs.json` (`47b4deb96ea22043`) for the v2.4a checks. mechanical.json v2.1 still has no MEOP, MAWP or rounded-entrance keys and quotes the tank relief as "<= 7.5 MPa", and electronics.json v2 keeps points the decisions have overtaken (REV-COMB-2 R2-13, a configuration item for the lead). The throttle floor requirement is ENG-02 <= 20 %, which closes; 25 % is a flight fallback only (RC-13 a). The v2.3 duty-cycle claim is withdrawn: A2 is removed and B1 is capped at 85 m by the lead, with the 62 m records handled in §4.6 (RC-13 e). v2.4a addendum: LEAD line 181 (REV-GNC-3 decisions; requests (2), (4) and (10) are answered here) and line 182 (Mechanical handback: TC-02 classification, 608 bearings with C0 >= 1.80 kN, bleed valves 2 x 0.30 kg ASSUMED, the NZ-04 flexible-graphite seal treated as FAIL at a 577 C soak until a datasheet shows >= 627 C, the bay-wall clearance) are quoted for status; line 182 changes no v2.4a analysis. Line 183 (lead read of the max-thrust FEA tables) is also quoted for status: TC-02 DESIGN CHANGE mandatory; TC-03 (Inconel 718 seat insert) passes primary and P+Q, LCF to be shown; NZ-01 graphite throat insert MS -0.44 (thermal) accepted TEST-BASED if captured, refuted by fragment loss or a throat-area change > 2 % (see OI-40: erosion alone can exceed 2 % per A1 flight).

**Sources.** NASA CEA (RocketCEA); CoolProp 8 HEOS for N2O; Dyer et al. and HEM for two-phase injection and bleed flow; Bartz; Lewis & Carlson; Rotondi et al. (JPP 2024) and Nagle-Strickland-Constable for graphite erosion; Mechanical's CAD, FEA and bleed-path files; GNC's records; Electronics' SIL; the review. Material data quoted "as recalled" are marked TO-VERIFY. v2.4a adds Lubin and Springer (1967) for the tank-drain dip screening (LITERATURE, applicability to N2O TO-VERIFY) and the GNC rev2 records.

**Files.** Hub `02-combustion/`: scripts in `src/`, data in `data/v2/` and `data/v2/v2p4/` (index `data/v2/v2p4/FILE-INDEX.txt`; superseded runs in `data/v2/v2p4/superseded/`), the CF-4 specification `CF-4-SPEC.md` (v2.0), the T1-T4 specification `T1-T4-REGRESSION-SPEC.md` (v2), the v2.4a data in `data/v2p4a/` (`HASHES.txt`), and §14 here.

**Tests (digital).** Every v2.4 script asserts its input hashes. The decided-path reduction reproduces the post-abort pocket base set before it extends it. The FD-01 element deficit is bounded on three readings of the element flow. Contradictions found during the work are kept in §13: the "restart" convention artefact in the purge reduction, the v3.4 inverted-U analysis, the 44.9 bar figure, the A5 abort and others. v2.4a: the FA-1 envelope script reproduces the v2.4 late-light case to 1e-6 bar before it extends the grid; the unpurged-start check reproduces six published P_abort values of `rg01_line_states_v2p4.json` before it follows the voids after a light; the T1-T4 law model reproduces the grain_q1d web on DC-D (14.25 against 14.24 mm). A first T1-T4 pass read the wrong DC-D file and let the analytic model burn past burn-through; both were corrected before any value was used (§13). Line-181 addendum: the outcome-class script is a verbatim copy of the parent check's code and reproduces its P(light), P(light then gap) and P(released, then A3) to 1e-12, plus the parent's population means, before it classes the starts; the cold-flow model reproduces the published ignition-lift flow at the A1 state (34.8-35.0 g/s against 35.0 g/s) and the map lifts at 4.5 MPa.

**Unknowns** (§11). The regression law; two-phase pintle Cd; the cap transport (slip) in the bleed path; the restrictor Cd; the torch reliability and photodiode false-positive rate (FA-1); the real late-light burn time and fuel fraction; graphite erosion kinetics; the joint materials at temperature. v2.4a: the fuel-vapour inventory at an A1 light (FA-1); the tank outlet geometry; the purge at the 2.7 deg specific-force angle; whether a light inside a liquid slug survives the vapour gap behind it; which end of the wall heat-transfer bracket (LO or HI) governs the coast flashing; the cold-flow thrust of the engine, above all with a hot chamber.

**Next closure** (§12). Lead: the PURGE commit rule after Combustion's unpurged-start finding (OI-31; L* = 1.3 s recommended); R2 with the cold-flow term and the command hold (OI-38); the configuration items of R2-13. Founders: CF-4 v2.0 (with 3 deg and per-tap flow), IGN-1 (>= 30 lights with photodiode false-positive tests, on the stand dynamic Pc channel), B-PNT-1, CF-1 to CF-3, then T1-T4 per specification v2. Electronics: the channel uncertainty behind the interlock guard band, the stand dynamic Pc channel, the closure deadline (E0 + 0.15 s), A4 on the filtered channel, A7, A14-A16, LIGHT_SPIKE. GNC: the 500-run specific-force angle during PURGE and a slosh bound (tank outlet); the cold-flow term in the sim6 V flame-out case and the command trace there (OI-38); the re-fly at the actual mass ledger (LEAD line 181 (5) replaced the 0.30 kg trigger by >= 0.10 kg). Mechanical: the gimbal bearing selection (line 179), the TC-02 head margin in LC-TB70 (line 179, OPEN), the tank outlet in CAD, the measured dP-flow curve of the FD-01 element, the joint FE re-run. Combustion: the purge at 2.7 deg (OI-35), a 1-D gas-dynamic run of the worst FA-1 row (OI-36), and the reduction of CF-4, IGN-1 and T1-T4.

## Contents

- §1 Thermochemistry (v2.3, unchanged)
- §2 N2O tank and feed: 2.1 properties (RC-13 b corrected); 2.2-2.5 (v2.3; 2.4 note); 2.6 feed line (v2.4); 2.7 trapped volumes, relief and transducer protection (v2.4); 2.8 the valve-to-seat segment at relight and the forced purge (v2.4)
- §3 Throttle and shutoff: 3.1 (v2.4 valve status); 3.2-3.4 (v2.3); 3.5 force law (v2.3) with the seat and seal (v2.4); 3.6 MEOP basis (v2.4); 3.7 throat block, runaway and tail-off (v2.4)
- §4 Grain: 4.1 regression law (v2.4); 4.2-4.5 (v2.3 with v2.4 notes); 4.6 regression band, the B1 burn limit and oxidiser-rich operation (v2.4)
- §5 Nozzle and erosion: 5.1 (v2.4 note); 5.2-5.3 (v2.3); 5.4 erosion and life (v2.4)
- §6 Heat loads: 6.1-6.4 (v2.3 with v2.4 notes); 6.5 nozzle joint (v2.4)
- §7 Ignition, restart, start-up and shutdown: 7.1-7.2 (v2.3; torch gate note); 7.3 sequence (v2.4); 7.4 abort matrix; 7.5 torch N2O line; 7.6 hard start and maximum unignited inventory; 7.7 relight latency
- §8 Combustion stability (v2.3 with v2.4 note)
- §9 N2O hazard list (v2.4): 9.1 purge, stuck-open and FA-1 (FMEA input); 9.2 stored energy
- §10 Cold-flow and static-fire test plan (v2.4): 10.1 cleaning, drying and catch volumes; 10.2 safing; 10.3 CF-4 summary; 10.4 regression-rate measurement at T1-T4 (RG-03)
- §11 Unknowns; §12 Open items with owners; §13 Failures and superseded evidence; §14 File index and reproduction
- v2.4a changes are marked "v2.4a" in place: §0 item 12; §2.4 tank outlet; §2.8 the PURGE commit rule, the unpurged start (Tables 2.16 and 2.17) and the 2.7 deg note; §3.6 guard band; §7.3-7.4 the E1 and A14 closure term, A4 filtered, the cold-flow thrust under the drogue (Table 7.3a); §7.6 the FA-1 envelope (Tables 7.6a and 7.6b); §8 the dynamic Pc channel; §9 H20, the vented mass and the FA-1 FMEA; §10 the v2.4a test-plan amendments, safing, CF-4 v2.0 and the T1-T4 specification v2; §11-§14.

## 1. Thermochemistry

### 1.1 Method

RocketCEA (NASA CEA) computes shifting and frozen equilibrium over Pc 3-30 bar and O/F 2-10 (`src/thermo_tables.py` writes `data/thermo/*_v1.{csv,json}`). Outputs:
- c*, Tc, gamma and MW;
- Isp_SL and Isp_vac against eps, aware of Schmucker separation;
- transport properties (mu, cp, Pr, k) in the chamber and at the throat;
- exit composition at eps 2.

The oxidiser card is CEA "N2O", an ideal gas at 298.15 K. Cantera (GRI-3.0 thermodynamics) supplies the delivered-state compositions for the erosion model and the plume afterburning post-processor.

### 1.2 Fuel cards and heats of formation

The lead's v0 card, C15H17N with hf +62.6 kJ/mol (+296 kJ/kg), was checked against three independent routes (`src/cea_cards.py`).

Table 1.1. ABS and PETG cards. c* is ideal shifting equilibrium at 25 bar (CEA). Source of hf: DERIVED from the stated LITERATURE.

| Card | Basis | hf [kJ/kg] | c* peak [m/s] | O/F at peak |
|---|---|---|---|---|
| ABS_LEAD_v0 | lead v0, C15H17N +62.6 kJ/mol (ASSUMED) | +296 | 1601 | 5.50 |
| ABS_TYP_v1 (design card) | monomer hf + polymerisation enthalpy, composition A/B/S 0.24/0.185/0.575 | +476 | 1601 | 5.50 |
| ABS_FAA_v1 | FAA bomb calorimetry Qc 39.84 kJ/g | +452 | 1603 | 5.50 |
| ABS_FAAGC_v1 | FAA group contribution Qc 39.43 kJ/g | +42 | 1597 | 5.50 |
| ABS_SRICH / BRICH / ARICH_v1 | composition corners of the published ranges | +458 / +458 / +494 | 1600 / 1603 / 1600 | 5.50 / 5.75 / 5.50 |
| ABS_USU5043_v1 | 50:43:7 B:A:S (withdrawn USU record) | +711 | 1611 | 5.25 |
| PETG_NOM / LO / HI_v1 | PET hf -704 / -812 / -441 kJ/mol, CHDM 0.31 (ASSUMED) | -3406 / -3902 / -2197 | 1538 / 1529 / 1562 | 3.75 / 4.00 / 3.50 |
| PARABS50_v1 | 50/50 wt paraffin/ABS (research option) | n/a | 1608 | 6.25 |

Findings:
- The v0 value is not reproduced by any source. The spread of ABS heat of formation (+42 to +494 kJ/kg) moves c* by no more than +/-0.3 %, so it does not matter for performance. ABS_TYP_v1 is the design card.
- PETG reaches 3-4.5 % lower c* at a much lower optimum O/F (3.5-4). PETG as a backup therefore needs its own grain design with more fuel surface or length, and its own regression law.
- Paraffin/ABS is listed as a research option only.

Research proposal, paraffin/ABS composite:
- Hypothesis: higher regression gives a shorter grain at the same O/F.
- Comparator: S230 ABS.
- Evidence: none of our own; the composite concept is from the USU literature (McCulley et al. 2012, LITERATURE-UNVERIFIED).
- Refutation criterion: measured regression gain below 1.5x, or a print or structural defect.

### 1.3 Performance against O/F

Table 1.2. N2O/ABS_TYP_v1 at Pc 25 bar, shifting equilibrium, ideal (CEA).

| O/F | c* [m/s] | Tc [K] | MW | gamma_c | Isp_vac eps 2 [s] | Isp_SL eps 2 [s] | pe/pa eps 2 |
|---|---|---|---|---|---|---|---|
| 3.00 | 1449 | 2446 | 22.53 | 1.2133 | 215.3 | 203.3 | 2.68 |
| 4.00 | 1548 | 3009 | 24.27 | 1.2297 | 230.4 | 217.6 | 2.73 |
| 5.00 | 1595 | 3296 | 25.85 | 1.1787 | 237.7 | 224.6 | 2.89 |
| 5.50 | 1601 | 3354 | 26.41 | 1.1635 | 239.1 | 225.9 | 3.00 |
| 6.00 | 1600 | 3379 | 26.85 | 1.1548 | 239.3 | 226.1 | 3.11 |
| 7.00 | 1585 | 3380 | 27.52 | 1.1472 | 237.5 | 224.4 | 3.22 |
| 8.00 | 1566 | 3353 | 28.00 | 1.1449 | 234.8 | 221.9 | 3.24 |
| 9.00 | 1548 | 3316 | 28.35 | 1.1448 | 232.0 | 219.2 | 3.23 |
| 10.00 | 1530 | 3275 | 28.62 | 1.1459 | 229.3 | 216.6 | 3.21 |

Stoichiometric O/F is 8.17 (CEA, `chamber_port_state_v2.json`).

### 1.4 Liquid-N2O injection

Table 1.3 compares liquid N2O injected at 20 C with gas N2O at 298 K. The effective hf of the liquid is 70.82 kJ/mol (CEA + CoolProp, `data/thermo/n2o_liquid_correction_v1.json`).

| Pc [bar] | O/F | c* gas [m/s] | c* liquid [m/s] | dc* [%] | Tc gas [K] | Tc liquid [K] |
|---|---|---|---|---|---|---|
| 25.00 | 7.76 | 1571 | 1554 | -1.10 | 3361 | 3310 |
| 13.25 | 5.48 | 1594 | 1574 | -1.26 | 3292 | 3235 |
| 6.18 | 3.70 | 1522 | 1491 | -1.99 | 2827 | 2736 |
| 4.36 | 3.11 | 1453 | 1425 | -1.91 | 2491 | 2391 |

The engine maps use the gas card with eta_c* 0.92, so this 1-2 % penalty is not applied separately. It lies inside the eta_c* band. eta_c* measured in T1-T2 with liquid injection will include it.

### 1.5 Design O/F and its shift with throttle

The O/F is not a free choice in a hybrid. With n = 0.5:
- fuel flow scales as G_ox^0.5 x (burning area), so O/F scales as mdot_ox^0.5;
- the port diameter drops out (D^(2n-1) = 1), so at n = 0.5 the O/F at a given oxidiser flow does not drift as the port opens. With n < 0.5 it would rise; with n > 0.5 it would fall. The measured n decides this.

Consequences for the S230 grain:
- O/F is 10.4 at 100 % (initial port) and 4.06 at 12.5 %. 10.4 / sqrt(241/36.5) = 4.05.
- The 100 % point is lean of the c* optimum (O/F 5.5-6). That costs about 4 % in c* (1530 against 1601 m/s ideal) and leaves an oxidiser-rich exhaust: about 7 % O2 in the chamber, and no plume afterburning (05-plume-cfd).
- The floor runs close to the low-pressure c* optimum (5.25 at 4.36 bar).
- The lean 100 % point is the cost of a short grain. S260 lowers the A1 mean O/F only from 8.9 to 7.8 (Table 4.2), and the gimbal sweep makes length expensive.

## 2. N2O tank and feed

### 2.1 Properties

CoolProp 8.0 (`NitrousOxide`, Lemmon & Span) is compared with ESDU 91022 in `src/n2o_validation.py` and `data/v2/n2o_validation_v2.json`.

Table 2.1. Maximum absolute deviation [%] (LITERATURE against LITERATURE).

| T band | P_sat | rho_l | rho_v | h_fg |
|---|---|---|---|---|
| 230-290 K | 0.33 | 0.60 | 0.72 | 0.29 |
| 290-300 K | 0.15 | 0.19 | 0.98 | 0.92 |
| 300-305 K | 0.14 | 0.09 | 2.22 | 2.08 |
| 305-309.5 K | 0.09 | 4.88 | 3.37 | 47.61 |

Validity:
- About 1 % property uncertainty up to 300 K (27 C), about 2 % to 305 K.
- Within 4 K of the critical point (Tc 309.52 K in CoolProp against 309.57 K in ESDU; Pc 72.5 bar) the representations diverge. The 30-36 C range is a hazard regime, never a design point. The conditioning requirement is 15-24 C at ARM (ENG-12 as amended; RC-13 b; REV-COMB-2 R2-05), with the 24 C liquid-line interlock (§2.8), its guard band (§3.6) and the arm limits of §7.3. Values quoted at 25 C are bounds, not operating points.
- CoolProp 8 has no N2O transport properties. CO2 at the same reduced temperature is used as a surrogate (ASSUMED), for the tank heat-transfer closure only.

### 2.2 Blowdown models and the thrust ceiling against time

Two tank models are used:
- Equilibrium, Whitmore & Chandler type (`src/tank.py`).
- Two-control-volume non-equilibrium, Zilliac & Karabeyoglu type (`src/tank_nheq.py`). Its evaporation enhancement factor E is not calibrated, so it runs as a band: E = 100 and 1000.

The baseline tank (LEAD 2026-10-12) holds 2.00 kg in 3.17 L, conditioned to 15-24 C at ARM (ENG-12 as amended; 25 C is kept as a bound). Saturation pressure is 45.0 / 50.5 / 56.5 bar at 15 / 20 / 25 C (CoolProp).

Table 2.2. Continuous 500 N command from t = 0 on the baseline tank: S230 grain, Dyer pintle Cd 0.70 (SIM, `data/v2/ceiling_vs_time_BLtank_v2.csv`).

| Tank model | T0 [C] | Ceiling at t=0 [N] | 500 N held [s] | Liquid end [s] | Ceiling at liquid end [N] | P_tank at liquid end [bar] | N2O used [kg] | Impulse to liquid end [N s] |
|---|---|---|---|---|---|---|---|---|
| eq | 15 | 666 | 5.81 | 7.31 | 445 | 29.7 | 1.737 | 3611 |
| eq | 20 | 719 | 7.01 | 7.08 | 492 | 32.8 | 1.704 | 3541 |
| eq | 25 | 771 | 6.93 | 6.93 | 544 | 36.2 | 1.669 | 3467 |
| neq E1e2 | 15 | 666 | 4.06 | 7.50 | 423 | 28.2 | 1.737 | 3616 |
| neq E1e2 | 20 | 719 | 6.15 | 7.12 | 467 | 31.1 | 1.704 | 3542 |
| neq E1e2 | 25 | 771 | 6.92 | 6.92 | 516 | 34.4 | 1.666 | 3461 |
| neq E1e3 | 15 | 666 | 5.73 | 7.22 | 450 | 29.9 | 1.717 | 3570 |
| neq E1e3 | 20 | 719 | 6.97 | 6.97 | 497 | 33.2 | 1.678 | 3486 |
| neq E1e3 | 25 | 771 | 6.77 | 6.77 | 551 | 36.9 | 1.630 | 3387 |

- The old gnc.json v1 tank (2.06 L, 1.30 kg) holds 500 N for 2.63-4.56 s (`ceiling_vs_time_v2.csv`).
- On every gnc.json v2 cycle the ceiling never limits. The minimum ceiling is 556-598 N, the minimum dP/Pc is 0.55-0.80, and liquid left over oxidiser used is 0.27-0.51, which meets the GNC reserve rule (>= 0.20 + 0.03).

### 2.3 N2 supercharge trade

Table 2.3. DC-A1 v1 profile, equilibrium tank, N2 treated as insoluble (ASSUMPTION). SIM, `data/v2/supercharge_trade_v2.json`.

| Option | P start [bar] | P at MECO [bar] | P at relight [bar] | P end [bar] | Note |
|---|---|---|---|---|---|
| SP0 self-pressurised 20 C | 50.5 | 41.9 | 41.8 | 37.2 | baseline |
| SP1 self 25 C | 56.5 | 46.1 | 46.0 | 40.7 | ground heater, removed at liftoff |
| SP1 self 28 C | 60.3 | 48.8 | 48.7 | 42.9 | ground heater |
| SP2 N2 pad 60 bar | 59.9 | 45.3 | 45.2 | 39.8 | 5.5 g N2 |
| SP3 regulated 55 bar | 54.8 | 55.0 | 55.0 | 55.0 | 44.9 g N2 from a 0.21 L, 300 bar bottle |

Recommendation (DERIVED, recorded as a v2 decision): self-pressurised N2O conditioned to 15-24 C at ARM (ENG-12 as amended) with a heater blanket that is removed at liftoff. Supercharge is not baselined:
- Heating to 25 C adds 4.3 bar at MECO; an N2 pad adds 3.4 bar and needs a fill system and a bottle.
- Regulated N2 adds about 13 bar at the end, but adds a 300 bar system, a regulator and a cost, all TO-QUOTE (Sønderborg DK-6400).
- The landing margin is already met: the ceiling is >= 556 N on all v2 cycles.
- The N2 options also carry an unverified solubility effect, since N2 dissolves in N2O.

### 2.4 Propellant settling for relight

Table 2.4. Settling before relight (DERIVED from the GNC acceleration histories). Files: `settling_v2.json` and `settling_v2wip_preview.json`. The v2 rows were run on the 19:15Z working copy; its accelerations differ from the published files by no more than 1e-4 m/s2.

| Duty cycle | Coast [s] | a_min [m/s2] | Time a<0 [s] | Settled before relight [s] | a mean, last 0.5 s [m/s2] | Bond | t_settle [s] |
|---|---|---|---|---|---|---|---|
| DC-A1 (gnc v1) | 22.16 | -1.20 | 6.63 | 14.96 | 9.82 | 6442 | 0.25 |
| DC-A2 (gnc v1) | 12.78 | -1.15 | 6.60 | 3.13 | 1.77 | 1158 | 0.58 |
| DC-A1 (gnc v2) | 20.92 | -1.24 | 6.66 | 13.93 | 9.76 | 6400 | 0.25 |
| DC-A2 (gnc v2) | 11.26 | -1.18 | 3.54 | 2.20 | 2.43 | 1595 | 0.50 |

- During 3.5-6.7 s of each coast the axial specific force is negative, down to -1.2 m/s2. The liquid moves forward and the outlet can uncover.
- Before relight, drag or the drogue resettles it. The Bond number of 1158-6442 means gravity dominates; the settled interval is 2.2-15 s against a 0.25-0.58 s settle estimate.
- No dip tube or baffle is needed for these cycles.
- Condition, proposed (DERIVED): the relight permissive requires a positive axial specific force for at least t_settle with margin. A2 v2 has 2.2 s against 0.5 s.
- The igniter sequence also requires P_feed >= 0.5 P_tank. Otherwise the priming rule applies (§7).

**v2.4 note (sequence v2.8 and the A1 purge).** On an A1 relight the liquid must cover the tank outlet from the PURGE command, E0 - 2.90 s, not only from T_fire: the purge is sized for liquid at both taps (15.62 g/s per tap) and vents vapour at 4.25 g/s per tap. The settling condition above therefore applies from E0 - 2.90 s - t_settle. Under the drogue the axial specific force at RELIGHT is 0.94-1.14 g (GNC records), so the condition is expected to hold. If the outlet uncovers during PURGE, the vented mass falls and the segment may not clear: the relight then rests on the line-state tables of §2.8 for an incomplete purge. [v2.4a: the T_fire delay of LEAD line 164, which v2.4 cited here, is withdrawn by line 175 (3).] That case is listed in §11.

**v2.4a: tank outlet coverage during PURGE** (lead request after GNC rev2; `unpurged_start_check_v2p4a.json` part D; DERIVED with CoolProp densities and the GNC SIM inputs of `purge_outlet_inputs.json` `47b4deb96ea22043`; quasi-static).
- Geometry used: the baseline tank of mechanical.json v1, a 6061-T6 tube 101.6 x 3.175 mm (ID 95.25 mm), internal length 0.4449 m, flat bolted bulkheads. It is a concept, not yet in CAD (DATASHEET tube size, DESIGN concept).
- Liquid at the purge in the six re-flown records: 766-1170 g at 0.89-1.12 g axial. Depth over the aft bulkhead: 126-133 mm at 766 g and 193-202 mm at 1170 g (283.15-289.5 K).
- The free surface drops at the wall by 2.3 mm at the largest specific-force angle in the records (2.71 deg), 5.7 mm at the largest tilt (6.86 deg) and 47.6 mm at an illustrative 45 deg. The lowest liquid height at the wall stays >= 120 mm (78.6 mm at 45 deg). The wall uncovers only beyond 69.3 deg.
- Screening: the Lubin-Springer dip height for a non-swirling drain is 7.9 mm (LITERATURE; applicability to near-saturated N2O TO-VERIFY). Roll spin-up of the liquid (Ekman) takes >= 359 s at <= 35.4 deg/s with an ASSUMED kinematic viscosity of 0.5-2e-7 m2/s, so no drain vortex develops in the 2.9 s. First slosh mode 2.92 Hz.
- **Verdict:** covered quasi-statically, with a large margin, IF the outlet sits on the aft bulkhead of an axial tank. This is not a final verdict.
- **Liquid basis (LEAD line 181 (10)).** The check uses the liquid in the tank at the END of the PURGE flow: GNC gives m_liq as [start, end] pairs and the minimum end value, 766.4 g, is the one used above. The depletion in the flow window is 79.8-81.8 g, consistent with the 81.6 g liquid depletion of line 181 (10) (8.6 g boils into the ullage; 73.0 g is the vented, vehicle-level mass). Quasi-static coverage with the outlet anywhere on the aft bulkhead needs a depth of 13.6 mm (h_c 7.9 mm plus the 5.7 mm wall drop at 6.86 deg), that is 78.6-82.5 g of liquid at 289.5-283.15 K: about 9x below the 766 g minimum (DERIVED; `tank_outlet_coverage_v2p4a` in the interface).
- MISSING: the outlet position and diameter; any dip tube, sump, anti-vortex plate or screen; the tank orientation in the vehicle and which bulkhead is aft; the bulkhead face near the outlet (bosses, protrusions); a slosh amplitude (sim6 carries the liquid as a lumped mass); the specific-force angle over the 500 runs (six records were given). Owners: Mechanical (CAD), GNC (OI-32).

### 2.5 Injector two-phase flow and Cd

Three models are compared (`src/injector.py`, `src/injector_compare.py`):
- SPI (incompressible);
- HEM (homogeneous equilibrium, isentropic);
- Dyer NHNE, the non-equilibrium blend of the two. It is the baseline.

The upstream state is metastable liquid after the line loss. At the max-thrust point the ratio G_model/G_Dyer is 0.64-0.68 for HEM and 1.34-1.37 for SPI.

Table 2.5. Thrust ceiling against Cd with the Dyer model (SIM, `injector_compare_v2.json`).

| T [C] | Cd 0.50 | Cd 0.60 | Cd 0.70 | Cd 0.80 | Limit at Cd 0.8 |
|---|---|---|---|---|---|
| 15 | 563 N | 619 N | 666 N | 669 N | dP/Pc 0.25 |
| 20 | 603 N | 666 N | 719 N | 747 N | dP/Pc 0.25 |
| 25 | 642 N | 712 N | 771 N | 822 N | stroke |

Worst model case: HEM at 15 C with Cd 0.6 is equivalent to Dyer with Cd_eff 0.407, which gives a 498.6 N ceiling.

Acceptance criterion (DERIVED): Cd_eff measured in N2O cold flow, relative to Dyer, must be >= 0.41. This keeps the 15 C ceiling at or above 500 N. Cd is measured first in water (single-phase Cd against lift), then in N2O against back-pressure (§10).

### 2.6 Feed line, hose and sense line (v2.4)

The feed layout in v2.4 follows the lead's decisions of 2026-10-13:
- Main valve: MV-P, a balanced poppet. Cv 3.6 (Cd 0.65 ASSUMED), seat 11 mm, lift 2.75 mm.
  - Closing time: about 30 ms with the dashpot; 0.10 s is the bounding value until bench B-MV-1.
  - Rating: MAWP >= 8.42 MPa, proof >= 10.5 MPa.
- MV-P location: in the FS-01 module at the top of the zone (option A), with a fixed 3/8 in line down the wall to the coil (LEAD).
- Back-relief check: FS-01 also carries a check valve (crack 0.03-0.07 MPa) that relieves the segment back to the tank (§2.7).

Table 2.6. Feed pressure drop at 0.26 kg/s (DERIVED, `throat_block_v2p4.json` `feed_budget_MVP`). "Smooth" and "rough" are the ASSUMED friction bounds of the hose.

| Tank | MV-P Cv 3.6 + filter Cv 2.2, smooth hose | Same, rough hose | Cv 3 valve (v2.3 basis), smooth |
|---|---|---|---|
| 15 C | 107.2 kPa | 113.9 kPa | 112.0 kPa |
| 20 C | 112.0 kPa | 119.1 kPa | 117.1 kPa |
| 25 C | 118.3 kPa | 125.8 kPa | 123.6 kPa |

How the drop splits, at 20 C:
- MV-P 11.5 kPa;
- filter 30.8 kPa;
- fittings and bends 60.9 kPa;
- hose 8.7-15.8 kPa.

The fixed 3/8 in wall line from the zone-top MV-P to the coil (278.75 mm on v3.4.1) adds about 8-15 kPa (ESTIMATE). Every simulation uses a line-loss budget of 270.4 kPa, so the margin is at least 129 kPa.

The MEOP basis (§3.6) uses this hardware line loss. A larger loss lowers the stuck-pintle Pc. A smaller loss raises it, up to 45.55 bar at the 24 C interlock with zero loss. CF-3 therefore measures the line loss.

Hose and sense line are unchanged from v2.3:
- **Hose.** -6 PTFE-lined braid across the gimbal.
  - Velocity: 6.3 m/s at 0.241 kg/s and 6.5-7.1 m/s at 0.26 kg/s.
  - Friction: 8-17 kPa.
  - Surge on slow closure: 14-106 kPa, for a 40-150 ms closure and a 0.4-0.8 m line.
- **Pc sense line.**
  - 1/8 in tube (1.6 mm ID), no longer than 0.3 m; transducer dead volume <= 0.3 cm3.
  - Natural frequency >= 144 Hz in N2O-like gas and >= 188 Hz in N2.
  - Phase lag <= 0.64 deg at 50 Hz (DERIVED).

**Priming.** The v2.3 bleed-lift rule is no longer a separate step. The v2.8 sequence (§7.3) handles priming on two paths:
- **Primed** (P_feed >= 0.5 P_tank): the MV-P opens at E0 with the pintle seated. On an A1 relight it opens at the PURGE command, 2.90 s before E0 (§2.8, §7.3).
  - Any gas in the segment is already at >= 0.5 P_tank.
  - Isentropic compression of saturated vapour from 0.5 P_tank to P_tank heats it to at most 310 / 315 / 319 K at 15 / 20 / 24 C (CoolProp, DERIVED). From 0.8 P_tank the bound is 295-304 K.
  - This is far below the 614-646 K of a line compressed from 1 bar (Table 2.7). No bleed is needed.
- **Unprimed** (P_feed < 0.5 P_tank or a pressure invalid, including the first start on a fresh line; also any latched prep path): the PREPRESS of fw v2.8.2 / v2.8.3 (§7.3).
  - The pintle goes to the 0.10 mm bleed lift 0.06 s before the MV ramp starts; the MV ramps open over 0.35 s and holds 0.15 s; the bleed lasts until the feed reads primed, at most 0.56 s. A gas-filled dead end is therefore never compressed fast.
  - Read in `engine_ecu.cpp` (5e5771220a602301) and `config.h` (0ee2a75b6c4441d5): the bleed lift and a ramp >= 0.3 s (`kMvOpenRampSlow_s` 0.35 s, with a static assert against Combustion's minimum) are present. The v2.4-draft open item is closed. With valid pressures and P_feed >= 0.5 P_tank the prep path runs the ramp without a bleed.

Table 2.7 is unchanged and remains the bound for a fast valve onto a gas-filled line.

Table 2.7. Upper-bound gas temperature from adiabatic compression when the isolation valve opens fast onto a dead-ended line (DERIVED).

| P_tank [bar] | N2 ideal [K] | N2 CoolProp [K] | N2O vapour CoolProp [K] |
|---|---|---|---|
| 45 | 870 | 847 | 614 |
| 52 | 907 | 879 | 630 |
| 60 | 944 | 913 | 646 |

### 2.7 Trapped volumes, relief and transducer protection (v2.4; RC-04, RC-12)

Basis files:
- `safing_relief_v2p4.json` (script `safing_relief_v2p4.py`);
- `segment_recheck_v2p4.json` (script `segment_recheck_v2p4.py`);
- CoolProp 8 equilibrium unless stated.

Volumes are SI, quoted in cm3 for readability.

Table 2.8. Lockable N2O volumes.

| Volume | Size | Liquid at 15 / 20 / 25 C | Trapped when | Source and status |
|---|---|---|---|---|
| MV-P to pintle seat, CAD v3.4.1 re-route (adopted) | 48.23 cm3 with the filter element as a capillary barrier, 50.04 cm3 with it open (Mechanical DERIVED on the v3.4.1 solids) | 39.6 / 37.8 / 35.8 g (40.0 g at the A1 relight state, 286.7 K), barrier | Every coast; after every burn and every abort | LEAD (re-route baseline). The v2.4-draft 44 cm3 (v3.4) is superseded; results computed on 44 cm3 and not re-run say so |
| Flow-path traps at 0 deg (part of the segment) | 12.00 / 13.81 cm3, including the 4.42 cm3 manifold annulus at the seat. Above about 0.6 deg of tilt the hose forms humps: 3.84 cm3 at 2 deg, 16.9 at 10 deg (worst azimuth) | – | Every coast (§2.8) | Mechanical `segment_traps_v341_v1`, DERIVED. Replaces the v3.4 inverted U (27.87 cm3, superseded) |
| Torch N2O line, SOL0 to SOL1 (§7.5) | 1.21 cm3 (ASSUMED 1/8 in line, 1.6 mm bore, 0.6 m) | 0.95 g at 20 C | Only if SOL0 closes on liquid; R-T4 gives it a backward relief path | ASSUMED routing (Mechanical) |
| Flight tank | 3.17 L, 2.00 kg | Liquid volume fraction 72 / 75 / 80 % | Always (closed vessel) | LEAD |
| Ground panel lines and the CF-3 catch volume | Stand-specific | – | Any closed pair of valves | Founders' panel; every lockable volume gets a relief (§10.1) |

**Liquid-full segment against warming** (isochore from saturated liquid; `segment_recheck_v2p4.json` part C):
- dP/dT at constant density is 0.551 MPa/K at the A1 relight state, 0.471 MPa/K at 20 C and 0.405 MPa/K at 25 C.
- From the A1 state, the warming needed to reach each pressure is:
  - 8.42 MPa (MAWP): 7.3 K;
  - 9.03 MPa (lower burst limit of the secondary disc): 8.4 K;
  - 10.5 MPa (proof): 11.1 K.
- A trapped-liquid relief must therefore be a working device. It acts within a few kelvin of warming.

**Relief arrangement** (Mechanical FS-01, adopted by the lead 2026-10-13; Combustion basis):

| Item | Value | Basis |
|---|---|---|
| S1, back-relief check | In FS-01, around the MV-P, flowing from the segment to the tank. Crack 0.03-0.07 MPa | Mechanical FS-01 (LEAD adopted). Holds the segment at <= P_tank + 0.07 MPa. Nothing is discharged near hot parts (C5 closed) |
| S1 capacity needed | Liquid expansion 0.075 / 0.241 / 0.831 cm3/s at 18 / 58 / 200 W. Boiling displacement 0.72 / 2.32 / 7.98 cm3/s. Required Cv of liquid at the crack: 0.0032 / 0.0105 / 0.036. The vapour-venting requirement is lower (about 0.014 at 200 W) | DERIVED, volume-independent. Any soft-seat check valve with Cv >= 0.1 passes 200 W with a margin of 2.8 |
| Secondary disc on FS-01 | 9.5 MPa +/- 5 % (burst 9.03-9.98 MPa), reverse-acting, rated at the coincident temperature. Discharges overboard (ICD item) | LEAD adopted. Operating ratio 0.93 against the 8.42 MPa fire case and 0.77 against normal relief (6.97 MPa) |
| Part ratings, N2O side | MAWP >= 8.42 MPa, proof >= 10.5 MPa: tank, MV-P, S1, hose, riser, block, manifold, transducers | LEAD (Mechanical relief note). 8.42 MPa = fire-case tank relief 8.35 MPa + S1 crack 0.07 MPa |
| Tank relief set pressure | 6.9 MPa, below the 7.0 MPa tank MEOP (ENG-09) | Combustion proposal, CONFIRMED by LEAD line 172 (6) with fire relieving at 8.35 MPa, MAWP >= 8.42 MPa, proof >= 10.5 MPa, the back-relief check (Cv >= 0.1) and the 9.5 MPa +/- 5 % disc. Interface block `relief_v2p4a`; it supersedes the v1 trapped-liquid relief "<= 7.5 MPa" |
| Tank relief reseat | Above 5.53 MPa (Psat at the 24 C interlock) | TO-VERIFY with the part |
| Tank relief capacity, flight tank | Fire, relieving at 8.35 MPa (set x 1.21): 2.87-4.71 mm2, d_eq 1.9-2.4 mm. Heater runaway at 100 W, relieving at 7.59 MPa: 0.036 mm2 | DERIVED. Fire heat by the API 521 form Q = C1 F A^0.82 (as recalled, TO-VERIFY), C1 43.2 / 70.9 kW, F 1, whole outer surface. Relieving state scanned along the isobar (supercritical above 7.245 MPa). HEM isentropic flux, Kd 0.85 (ASSUMED) |
| Tank relief capacity, 15 L ground tank (10.4 kg; ASSUMED 140 mm x 0.974 m) | Fire: 6.9-11.3 mm2, d_eq 3.0-3.8 mm | Same method. A commercial cylinder carries its own relief under its standard (TO-VERIFY on the purchased cylinder) |
| Discharge | Tank relief and remote vent through a line routed away from the nozzle, the case and people; never through the engine | H1, H8. Mechanical routes it |
| Transducers | P_feed and P_tank 170BG (proof 34 MPa, burst 85 MPa); Pc and P_torch 070BG | LEAD. Above the 9.98 MPa upper disc limit: protected by the relief chain. Overpressure and burst ratings of the 070BG units against the 10.5 MPa proof are TO-VERIFY (§12) |

**What S1 does not do** (§2.8). S1 vents the volume that heating adds, not the vapour.
- With vapour at its port, the segment's void still grows by 0.0067 cm3 per joule that boils liquid; with liquid at its port, by 0.0388 cm3/J.
- Only an exchange with the tank or a bleed returns liquid to the segment.
- The S1 sizing above is unaffected.

**RC-12, set point against MEOP:**
- The tank relief set point is now below MEOP (6.9 against 7.0 MPa).
- The parts are rated for the relieving pressure, MAWP >= 8.42 MPa, not for MEOP. The finding is closed by the adopted MAWP basis.
- COTS ratings are checked against 8.42 MPa (Mechanical, TO-VERIFY per part).

**Flight tank against temperature:**
- The 2.00 kg / 3.17 L load becomes liquid-full at 306.6 K (33.5 C) and 6.80 MPa. Above that the pressure rises at 0.4-0.5 MPa/K and the relief flows liquid or supercritical fluid.
- The ignition interlock (T_tank <= 24 C at ARM and at ignition, §3.6) keeps the vehicle well below this.
- A pad hold in the sun with the heater disabled is the credible way to reach it. The tank relief and the remote vent (§10.2) cover it.

**S1 failure (stuck shut) and the S1 flag** (`segment_recheck_v2p4.json` part C, 44 cm3):

Table 2.9. Heating time for a liquid-full segment with S1 stuck shut, from saturated liquid.

| Threshold | Warming [K] (A1 / 25 C start) | Time at 18 / 58 / 200 W [s] (A1 start) |
|---|---|---|
| S1 flag: P_feed - P_tank > 2 bar | 0.36 / 0.49 | 0.7 / 0.2 / 0.06 |
| MAWP 8.42 MPa | 7.34 / 6.78 | 13.7 / 4.3 / 1.2 |
| Disc lower limit 9.03 MPa | 8.44 / 8.26 | 15.8 / 4.9 / 1.4 |
| Proof 10.5 MPa | 11.08 / 11.82 | 20.7 / 6.4 / 1.9 |

- **Flag rule.** The S1 flag fires when the MV is closed and P_feed - P_tank > 2 bar for 1 s (LEAD).
  - At 18 W it precedes MAWP by 9.8-12.0 s; at 58 W by 2.3-3.1 s, over the 15-25 C bound (ARM window 15-24 C) and the A1 starts.
  - At 200 W it does not precede MAWP (-0.03 to +0.17 s); only the passive disc protects.
  - Times scale with the segment volume: for the v3.4.1 segment (48.23 cm3) they are 1.096 times longer (MAWP at 15.0 / 4.7 / 1.3 s).
- **Flag action** (LEAD):
  - Stand: lockout.
  - Flight: flag and log. The relight proceeds, because opening the MV at E0 relieves the segment.

**O3b reply** (RC-04, C16). The O3b coil is part of the segment and is re-routed on v3.4.1 (LEAD).
- The thermal question is the heat input to the whole segment. On v3.4.1 it comes from Mechanical's slab model and FE head-end W(t): 0.83-9.0 kJ over the coast (§2.8).
- The 2026-10-12 O3b conditions C1-C7 stand.
- The relight requirement and the forced purge in §2.8 replace the v2.4-draft condition C8 ("manifold <= 30 W").

### 2.8 The valve-to-seat segment at relight: retained vapour, the integrated trade and the forced purge (v2.4, CAD v3.4.1)

**Status.** This section replaces the v2.4-draft §2.8 (44 cm3 inverted U on CAD v3.4, options (a), (b), (d) and the no-U research case). That analysis applies to hardware that no longer exists. It is kept as superseded evidence in `superseded/s2_8_v34_inverted_U.txt` and summarised in §13. Its results that still hold are carried here: the single-pocket abort curve, the prep-path and wide-W inventories, the refutation of (d), and the shutdown order.

**Lead decisions in force** (CHANGELOG 2026-10-13):
1. The coil re-route is the baseline (CAD v3.4.1).
2. The head-end bleed is a designed-in A1 provision in forced-purge form: MV open, pintle seated, both bleed taps open, ending before E1. It is fitted for A1 unless CF-4 shows the segment void at a relight-equivalent time below the zero-abort limit (18.86 cm3) in the ARM-hot case, wet and dry.
3. CF-4 gates the W 0.65 s relight claim.
4. (d), early MV opening under the drogue, stays dropped. Wider W and the prep path at W 0.88 s are rejected (inventory > 26.6 g). The drain pose is refuted (Mechanical).
5. Retained vapour is an integrated trade owned by Combustion: re-route, forced purge (2 taps, >= 0.8 mm), PTFE lining (research; dropped by the lead, line 164) and relight attitude.
6. Design attitude at RELIGHT is theta <= 2 deg [v2.4a: GNC rev2 gives a specific-force angle of up to 2.71 deg to the body axis during the purge flow, above this basis; OPEN (OI-35), see the note under Table 2.14]. 4, 10 and 20 deg are robustness information, not the design case. The purge vent is balanced (opposed pair) or axial, never a single lateral jet.
7. PURGE is pre-scheduled: it ends before T_fire, so the 0.81 s plan holds; the integrated form is the fallback (line 153).
8. The bleed path is set by its TOTAL flow, about 31 g/s (1.0 mm-equivalent), scheduled 2.5 s, planned at <= 76 g per purge (line 160):
   - F3: a restrictor at each tap, areas summing to the 1.0 mm equivalent;
   - F1: each valve >= 4x the restriction's capacity (seat >= 2 mm or Kv verified at 55 bar); the Burkert 6027 HP 1.0 mm does not qualify;
   - F2: no unfiltered path to the pintle seat during the burn (check valve on the T4 leg or an inline <= 15 um element on the FD-01 leg; Mechanical chooses). Mechanical chose the element (line 162, item 12 below).
   - 0.8 mm per tap (40 g/s) is not adopted; 1.0 mm per tap never; GNC's <= 0.8 mm total (about 20 g/s) is not adopted.
9. A stuck-open bleed (31.3 g/s) is handled as a risk:
   - two NC valves in series, with the drivers hardware-inhibited outside the scheduled purge window;
   - an FMEA on the double or common-cause fault;
   - if closure is not confirmed by the closure deadline (<= the torch gate; Electronics E0 + 0.15 s), E1 is declared at the deadline, BLEED_FAULT goes to the FC, V2 is commanded closed and the relight proceeds; on the stand it is an abort (amended by LEAD line 166 (3); item 15).
10. The purge trigger gate is adopted (quasi-steady descent, constant-velocity extrapolation), with an ECU hard cap on the purge duration (line 161).
11. Line 164: the minimal set (3) is the RG-01 design basis and the PTFE lining is dropped. PURGE is commanded at E0 - 2.90 s. The ECU cap is 2.5 s of flow plus the measured valve opening and closing times. The relight is never committed before a complete purge: if T_fire would cut the flow below 1.9 s, the FC delays T_fire [SUPERSEDED: withdrawn by LEAD line 175 (3); item 18]. The 0.81 s plan holds. Additive tank outflow governs the stuck-open case. CF-4 is the gate (spec: `02-combustion/CF-4-SPEC.md`).
12. Mechanical (line 162): F3 equal 0.707 mm restrictors; F2 an inline <= 15 um element on the FD-01 leg, between the tap and the tee, with Cd.A >= 1.57 mm2 (4x the restrictor's); the T4 check valve is not used. Mechanical's 15.91 cm3 was a 10 deg robustness row; at theta <= 2 deg the value is 4.84 cm3, which Combustion reproduces. That finding is closed.
13. Line 164 item 7: the F1 valves at 2 x 0.30 kg are a MASS RISK (target <= 0.15 kg per valve).
14. RG-01 stays BLOCKING until GNC re-flies on Combustion's re-routed-coil tables and CF-4 (line 161). [v2.4a: GNC rev2 re-flew it (line 174; SIM, staged; REV-GNC-3 running); CF-4 remains.]
15. Line 166 (v2.4a): E1 = torch confirmed (2oo2) AND [closure confirmed OR the closure deadline reached], the deadline <= the torch gate; at the deadline in flight the lift proceeds, BLEED_FAULT goes to the FC and V2 is commanded closed; on the stand it stays an abort (3). The 30 bar abort runs on the filtered channel with 5 ms persistence (4). A second re-zero ends before the PURGE command (5).
16. Lines 172 and 173 (v2.4a): one stand safing rule (172 (1)); the FA-1 load restated as an envelope, then fixed at 90 bar abs quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a 1.8 kN x 4 ms thrust spike (172 (2), 173); the relief set points confirmed (172 (6)); RG-16 miss side: GNC flies the published vented-mass table (172 (8)).
17. Line 175 (1)-(2) (v2.4a): A1 apogee target 285 m; the bleed-valve mass trigger is > 0.30 kg added by the selected pair. [Replaced by LEAD line 181 (5): GNC re-flies at the actual ledger for any confirmed landing-mass growth >= 0.10 kg summed over all changes.]
18. Line 175 (3) (v2.4a), PROVISIONAL: **PURGE commits no later than the plain relight trigger - 1.7 s (T_fire delay <= 0.6 s); otherwise no purge.** Line 164's "the FC delays T_fire" is withdrawn. The rule's second branch, "the relight proceeds unpurged", is refuted by Combustion's check (v2.4a subsection after Table 2.15); the lead decides between no relight on that pass and a ride-through mode (OI-31).

Basis files (scripts of the same name in `src/`; input hashes inside each JSON):
- `retained_vapour_v341_v2p4.json` (`cde7fa0cb3d41c18`): the trade. The full summary, including every purge case, is in `retained_vapour_v341_v2p4_summary.json.gz` (`184452b0727634d7`).
- `retained_table_v341_v2p4.json` (`812cacc5b318e351`): the tables below.
- `segment_heat_v341_v2p4.json` (`22d44495311a136a`): route heat on v3.4.1, unlined and lined.
- `cf4_void_budget_v2p4.json` (`6c294cf2dec7af5d`): the CF-4 pass/fail budget (§10).
- `purge_hazard_v2p4.json` (`ba24882f3ca956ba`): hazard numbers for the purge (§9).
- `purge_duration_v2p4.json` (`1ff6bfcd7d2f454c`): the purge time on a 0.1 s grid for 0.707 mm (equal split), 0.8 mm and 1.0 mm per tap and FD-01 alone. Trade files: `_trade.json` (`69e7192f63b5d8b8`), `_trade_summary.json.gz` (`5971815ccd035b29`), `_trade.json.raw.json.gz` (`02c30eb2e6569e8d`).
- `rg01_line_states_v2p4.json` (`2939549811d4c381`): the decided path per tilt and lining, the stuck-open flow, the GNC line states and the minimal set.
- Ignition model, carried from the earlier v2.4 runs: `relight_vapour_order_v2p4.json`, `coast_migration_v2p4.json`, `start_latency_v2p4.json`, `post_abort_pocket_v2p4.json`.

Inputs read:
- Mechanical:
  - `03-cad/calcs/segment_traps_v341_v1.json` (`6c1f557ae0a99c68`): volumes, plus the voxel tilt sensitivity at 10 and 20 deg per direction;
  - `drain_pose_v341_v1.json` (`52704e75870f8701`): neutral-pose path pockets at 0, 2, 4 and 10 deg, which give the hump shape at 2 and 4 deg;
  - `bleed_taps_v341_v1.json` (`a05927e74d08e479`);
  - `04-fea/thermal/segment_heat_budget_v1.json` (`218ff7242bcf71b1`): head-end W(t) and needle;
  - all DERIVED, FEA or ESTIMATE. The drain-pose and bleed-tap files are in Mechanical's workdir and not yet in the hub (open item, §12).
- GNC:
  - `staging_v3.1/results/a1_coast_accel/coast_accel_a1_series_v1.csv` (`cec7df69803059b9`): five coast series, windows 17.76-20.67 s from MECO to RELIGHT, drogue load 6.76-8.43 s after MECO;
  - `staging_v3.1/relight_attitude/relight_attitude_v1.json` (`e1c355e97dd4687e`);
  - both SIM.

**Questions** (lead and coordinator, 2026-10-13):
- P_abort at W 0.65 s for four combinations, (1) re-route only, (2) plus PTFE lining, (3) plus the 2-tap purge at 0.8 and 1.0 mm, (4) plus lining and purge, at 0, 2, 4 and 10 deg, LO / HI / ARM-hot, wet and dry.
- The minimal set for P_abort <= 1e-3 at 2 deg.
- Confirm or refute the lead's reading: "the re-route alone might pass at 2 deg in LO, and the open question is still the HI S1-side cap".
- Purge sizing and hazard (ask (a)); CF-4 as a test specification (ask (b), §10).

**Answer.**
1. **Re-route alone at the design attitude (0 and 2 deg).** P_abort is 0 in isothermal LO and hot-wall LO on both readings, in ARM LO dry and in isothermal HI dry. It fails in:
   - ARM LO wet: 0.24 (0.075 with the open element);
   - hot-wall HI dry: 0.65;
   - ARM HI dry: 1.0;
   - every HI case on the wet reading: 1.0.
2. **The lead's reading is confirmed for LO and refuted for HI.**
   - LO passes at 2 deg except ARM-hot LO wet, where the S1-side cap governs: 16.0-20.6 cm3 at 2 deg (19.9-24.4 at 0 deg) behind an 11-16 cm3 liquid slug.
   - In HI the S1-side cap is not the main problem. On the wet reading the head trap takes 4.2-7.4 kJ, 82-87 % of the segment heat. Its overflow, together with the coast-up void (bubbles stay put while S1 expels liquid), turns **the whole 48.2-50.0 cm3 segment to vapour** in all three HI cases (P = 1).
   - On the dry reading the cap governs hot-wall HI (24-25.5 cm3 behind a short slug; P 0.65) and ARM HI is vapour-full (1.0).
3. **The PTFE lining does not close the gap.** It cuts the route heat but not the head-trap heat that governs.
   - Without the purge it brings hot-wall HI dry to 0 and ARM HI dry to 0.15. HI wet stays at 1, and ARM LO wet falls only to 0.14.
   - With the purge it adds nothing, and in the s 0.5 slip bracket it lengthens the robust purge time from 1.5 to 2.0 s.
   - Not recommended; the research proposal is below.
4. **The forced purge closes every decision case.**
   - On the decided path (a restrictor per tap, 2 x 0.707 mm, the area of one 1.0 mm orifice, valves non-controlling), the needed flow time is 1.9 s unlined at 0 and at 2 deg (2.2 s lined). Over the needed time, P_abort is 0 in 200 000 samples. That covers every heat case and reading, both element models, all eight azimuths at 2 deg, all four cap-slip brackets and the five coast series (Table 2.13).
   - Scheduled 2.5 s (LEAD): margin 0.6 s unlined. N2O vented 34.3-72.9 g, inside the 76 g plan.
   - Residual at the lift (2.5 s): 4.77-8.15 cm3 at the seat, of which 4.42 cm3 is the manifold annulus that no tap sweeps. No cap and no hump vapour remain. The margin to the 18.86 cm3 zero-abort pocket is >= 10.7 cm3.
   - The earlier coarse grid (Table 2.11) gave 1.5 s for 0.8 mm per tap, which is now not adopted (line 160).
5. **Minimal set: re-route plus the 2-tap pre-scheduled purge on the decided path, theta <= 2 deg with a balanced or axial vent, and no lining** (Table 2.14).
   - Re-route alone and re-route plus lining both leave P_abort 1.0 (HI wet, whole segment vapour).
   - With the purge, the lining adds nothing and lengthens the needed time from 1.9 to 2.2 s.
   - PURGE is commanded at E0 - 2.90 s (0.35 s MV ramp + 2.5 s flow + 0.05 s); this supersedes the draft E0 - 2.40 s (0.8 mm per tap, 2.0 s).
   - The draft recommendation of 0.8 mm per tap at Tp 2.0 s (37.6-75.2 g) is superseded by the lead's path decision. Its numbers stay in Tables 2.11 and 2.12 as evidence.
   - FD-01 alone fails at 0.8 mm and at 0.707 mm (2.5 s: 18.6-47.8 g vented, P_abort > 1e-3 on the conservative slip). That is why F3 puts a restrictor on each tap.
6. **The 0.81 s plan holds.** The purge flow stops 0.05 s before E0, with both bleed valves closed. The torch gate and W are unchanged, so the light still falls within 0.81 s of T_fire (E0 -> E2 max 0.626 s on the worst purged state; Table 2.15). What moves is the commitment: the FC issues PURGE 2.90 s before T_fire. If RELIGHT is cancelled after PURGE, the MV and the bleed valves close.
7. **Hazard (ask (a); details in §9.1).**
   - The MV is open onto the seated pintle for 2.99-3.06 s, instead of 0.09-0.16 s.
   - The seat leak rate does not change: the segment is at P_tank through the coast via S1 either way. Scaled from `purge_hazard_v2p4.json` (computed for the 2.49-2.56 s exposure of the Tp 2.0 s draft), the purge adds 2.9-4.2 mg at the 10 sccm acceptance and 41-251 mg in Mechanical's fault leaks.
   - No sustained light is possible from a leak (G_ox <= 0.17 kg/m2s against >= 25).
   - The purge path is <= 424 K, far below decomposition. The stagnant annulus at the seat is the open item: the wetted seat face must stay <= 800 K from MECO to E1 (Mechanical).
   - The new path is a pintle drift or runaway during PURGE. It is now tank-fed for about 3 s. A15 monitors it and inhibits the torch. The residual exposure is about 19-34 times the v2.8 window, which is a decision for the lead.
   - Stuck-open bleed: 31.24 g/s (both taps liquid; 11.8 % of the 100 % flow; an upper bound). It is additive tank outflow while the Pc loop is closed. GNC's S313 arm (31.3 g/s) bounds it (§9.1).
8. **CF-4 gates the claim (§10.3).** Pass means, in every run, from a vapour-full and an ARM-LO-like segment at 0 and 2 deg:
   - first continuous liquid at the pintle inlet <= 0.293 s after the pintle reaches the lift;
   - then >= 0.35 s (15 cm3) of continuous liquid, or a later void inside the Table 10.4 budget;
   - the cap cleared <= 2.3 s after the flow starts;
   - each tap flow >= 80 % of the model, and the restrictors control (F1);
   - <= 76 g vented;
   - the flow stopped by E0 - 0.05 s, and closure confirmed by the closure deadline (<= the torch gate; LEAD line 166 (3));
   - no unfiltered flow between the legs during a simulated burn (F2).

**Segment on CAD v3.4.1** (Mechanical DERIVED; volumes in cm3; filter element as a capillary barrier / element open):

| Item | Barrier | Open | Note |
|---|---|---|---|
| Segment, MV-P seat to pintle seat | 48.23 | 50.04 | Every result is computed on both |
| Flow-path vapour retained at 0 deg | 12.00 | 13.81 | Held by the geometry when the rest drains to S1 |
| of which upstream of the element | 4.72 | 4.72 | FD-01 crown and riser top; includes the 0.52 cm3 hose micro-trap |
| of which downstream of the element | 7.28 | 9.09 | Head crown (T4); includes the 4.42 cm3 manifold annulus at the seat, which no tap sweeps (kept as vapour at the lift: conservative) |
| Dead ends | 1.08 | 1.08 | Module 1.01 (J602 cavity, MV balance chamber: part of the S1 cap region) + head 0.07 |
| Hose humps above 0 deg, worst azimuth (45 deg) | 3.84 / 9.27 / 16.91 / 18.55 | same | At 2 / 4 / 10 / 20 deg. Toward az 0: 2.64 / 6.21 / 12.93 / 15.16. 10 and 20 deg are voxel values; 2 and 4 deg come from the drain-pose path-pocket proxy, scaled per direction to the 10 deg voxel |

- The coil rises only about 2 mm over 180 mm, so a tilt above about 0.6 deg makes humps (Mechanical).
- Hose ID 10.59 mm; wall line 278.75 mm; riser 67.03 mm.
- With the element as a barrier, buoyancy alone needs both taps (T4 crown and FD-01 radial plug): the residual outside the hose is <= 0.52 cm3 at 10 deg and <= 1.16 cm3 at 20 deg. The hose humps must then be swept by flow (Mechanical `bleed_taps_v341_v1`).

**Heat into the segment over the 18.67 s A1 coast** (J; DERIVED with Mechanical's slab model and FE head-end W(t), ESTIMATE; `segment_heat_v341_v2p4.json`).

| Heat case | Head trap qT | Hose region qH | S1 cap region qU | Total | Lined 1 mm PTFE: qH / qU |
|---|---|---|---|---|---|
| Isothermal LO | 600 | 138 | 93 | 831 | 119 / 74 |
| Hot wall +5 K LO | 704 | 201 | 117 | 1022 | 178 / 106 |
| ARM (45 C bay, 24 C liquid) LO | 1037 | 405 | 193 | 1635 | 367 / 210 |
| Isothermal HI | 4207 | 313 | 291 | 4811 | 168 / 116 |
| Hot wall +5 K HI | 4964 | 468 | 375 | 5807 | 258 / 171 |
| ARM HI | 7390 | 973 | 648 | 9011 | 551 / 352 |

- The groups are:
  - head trap: FE manifold bore, TC-04, FD-01, TC-02, needle, riser and half of the TEE;
  - hose region: hose, sleeves and half of the TEE;
  - S1 cap region: module, FD-08F and wall line.
- The lining leaves qT within 2 %. The v3.4.1 route heat (module to TEE) is 246-1775 J unlined (204-935 J lined), against 290-2656 J for the v3.4 route.

**Model** (`retained_vapour_v341_v2p4.py`; DERIVED volume balance on SIM windows; 10 ms coast step, 1 ms purge step):
- **Coast:**
  - coast-up (MECO to the drogue load, f_z <= 0): bubbles stay where they form and S1 expels liquid;
  - drogue load: bubbles in the hose region fill the humps first, and the rest join the cap under S1;
  - descent: S1 vents only the expansion (§2.7).
- **Readings for a full trap:** "wet" means it keeps boiling at its liquid front, and the overflow joins the hose region and the cap. "Dry" means it stops boiling, which is the lower bound.
- **Purge:** both taps open for Tp, with the MV open and the pintle seated, ending 0.05 s before E0.
  - The T4 tap draws the head crown; in the barrier model it stops at a vapour front.
  - The FD-01 tap draws the upstream front, then the hump vapour, then the liquid slug, then the cap.
  - The cap moves at s times the column speed (slip). Regrowth during the purge is followed.
  - All head, riser, TEE and hose heat from the purge end to E1 (<= 0.21 s) is added to the pocket.
- **Tap fluxes** per tap (Cd 0.70 ASSUMED): choked HEM vapour 15 450 kg/m2s and Dyer liquid 56 843 kg/m2s at the coast state (46.45 bar, 289.5 K).
  - On the decided path (0.707 mm per tap): 4.25 g/s vapour or 15.62 g/s liquid per tap. Both taps together take 31.24 g/s, 11.8 % of the 100 % engine flow.
  - At 0.8 mm per tap: 5.44 g/s vapour or 20.0 g/s liquid per tap; both taps take 15 %.
- **Slip brackets:**
  - "scons": the smaller of the hose-downslope and wall-line values, with Taylor-bubble drift, C0 1.0, Fr 0.63 shallow and 0.35 vertical (LITERATURE as recalled, TO-VERIFY), at 1.14 g (the GNC maximum at RELIGHT): s 0.548 on the decided path (0.707 mm 2-tap); s 0.647 / 0.295 / 0.774 / 0.549 for 0.8 mm 2-tap / FD-01 alone / 1.0 mm 2-tap / FD-01 alone;
  - "swall": wall line only, the design-attitude estimate with the hose near horizontal: s 0.885 on the decided path; s 0.91 / 0.82 / 0.94 / 0.89;
  - s 1.0 and s 0.5 as brackets.
  - At 0 and 2 deg every bracket runs at every azimuth. At 4, 10 and 20 deg, scons runs at every azimuth and the other brackets at az 45.
- **Ignition:** the v2.4 200 000-sample E1 -> E2 distribution (seed 2024, assert).
  - Pocket purge 0.015555 s/cm3; liquid dead time 0.023192 s/cm3; up to two vapour gaps behind the first liquid.
  - P_abort is the worse of the "paused" and "restart" slug conventions. It is also the maximum over the five coast series, both element models and the azimuths at that tilt.
  - Zero-abort pocket V_zero = 18.86 cm3.
- **Checks:**
  - The purge model reproduces the analytic phase times for 2-tap and FD-01 alone, at s 1.0 and 0.7, within 2-4 ms (assert).
  - The hump-sweep condition holds: the column flow while hump vapour remains is >= 26.0 cm3/s on the decided path, >= 34.4 cm3/s with 0.8 mm 2-tap and >= 20.4 cm3/s with 0.8 mm FD-01 alone, against the 17.4 cm3/s the drift needs at 1.14 g.
  - The reduction script reproduces purge_duration_v2p4's combined-tilt robust times and N2O ranges (assert) and the published 19 cm3 line state of post_abort_pocket_v2p4 to 1e-12 (assert).
  - Convention artefact (found in v2.4, kept as evidence): the trade's "restart" convention adds the dead time of the 1 cm3 tank-liquid placeholder (+0.023 s) to single-pocket sequences. It is conservative and does not move the governing needed times (1.9 / 2.2 s). It does move two non-governing brackets by one 0.1 s step. Tables 2.13 and 2.15 use the corrected form; Tables 2.10-2.12 are as run.
  - Letting the annulus vent changes no P_abort.

**Relight attitude** (GNC `relight_attitude_v1`, sim6 v2.8-dev, 500 runs; SIM):
- Angle between body +z and specific force at the hose station, at RELIGHT, no purge: p50 / p95 / p99 / max 0.11 / 0.45 / 0.63 / 0.75 deg. No preferred azimuth.
- Last 5 s per-run maximum: 0.30 / 0.78 / 0.96 / 1.30 deg.
- Over a 10 s window, pooled over time: up to 8.41 deg, which is the deployment swing.
- A single 2.1 N lateral vent raises the angle to 1.18-1.85 deg toward the jet; a balanced or axial vent leaves it unchanged.
- The specific force at RELIGHT is 0.94-1.14 g.
- The drogue is modelled quasi-steady and massless, so real canopy swing adds on top (lead: an ICD requirement, §12).
- The design attitude of 2 deg covers p99 with margin, so 0 and 2 deg are the decision cases.

Table 2.10. P_abort at W 0.65 s without the purge: combinations (1) re-route only and (2) plus PTFE lining. Pairs are wet / dry. 0 means none in 200 000 samples.

| Comb. | Tilt [deg] | Iso LO | Hot wall LO | ARM LO | Iso HI | Hot wall HI | ARM HI |
|---|---|---|---|---|---|---|---|
| (1) | 0 and 2 | 0 / 0 | 0 / 0 | **0.24** / 0 | **1.0** / 0 | **1.0 / 0.65** | **1.0 / 1.0** |
| (1) | 4 | 0.26 / 0.02 | 0.26 / 0.18 | 0.27 / 0.24 | 1.0 / 0.24 | 1.0 / 0.65 | 1.0 / 1.0 |
| (1) | 10 | 0.73 / 0.02 | 0.73 / 0.18 | 0.74 / 0.72 | 1.0 / 0.43 | 1.0 / 0.72 | 1.0 / 1.0 |
| (1) | 20 | 0.82 / 0.02 | 0.84 / 0.18 | 0.85 / 0.72 | 1.0 / 0.43 | 1.0 / 0.81 | 1.0 / 1.0 |
| (2) | 0 and 2 | 0 / 0 | 0 / 0 | **0.14** / 0 | **1.0** / 0 | **1.0** / 0 | **1.0 / 0.15** |
| (2) | 4 | 0.25 / 0 | 0.26 / 0.12 | 0.27 / 0.24 | 1.0 / 0.08 | 1.0 / 0.24 | 1.0 / 0.24 |
| (2) | 10 | 0.73 / 0 | 0.73 / 0.12 | 0.74 / 0.62 | 1.0 / 0.08 | 1.0 / 0.31 | 1.0 / 0.72 |
| (2) | 20 | 0.76 / 0 | 0.84 / 0.12 | 0.85 / 0.62 | 1.0 / 0.08 | 1.0 / 0.31 | 1.0 / 0.82 |

The failures at 0 and 2 deg (barrier element shown; the open element is similar):

| Case | State at the lift | Failure mode |
|---|---|---|
| ARM LO wet | Pocket 12.5-18.1 cm3 at 2 deg (by azimuth and element model), slug 11-16 cm3, cap 16.0-20.6 cm3 (2 deg, az 45; 19.9-24.4 at 0 deg) | Vapour gap behind a short slug: the cap |
| Hot wall HI dry | Pocket 12.0-15.9 cm3, cap 24.2-29.4 cm3 | The cap |
| ARM HI dry, every HI wet | Whole segment vapour (47.2-51.8 cm3 with the regrowth to E1) | Void at the seat beyond the zero-abort pocket |

- At 0 and 2 deg the passing cases hold 12.0-18.1 cm3 at the seat (the flow-path traps plus the 2 deg hump), below the 18.86 cm3 limit.
- At 4 deg the 9.27 cm3 hump alone pushes the pocket past the limit in most cases. Without a purge, the re-route is therefore attitude-limited at about 2-3 deg as well as heat-limited.

Table 2.11. Robust purge time Tp_r (s): the smallest grid time (1.0-4.0 s in 0.5 s steps) from which every longer grid time gives P_abort <= 1e-3, over every heat case, reading, element model and azimuth at that tilt. Columns are 0-2 deg (decision) / 4 / 10 / 20 deg (sensitivity). "None" means no Tp up to 4.0 s passes.

| Orifice, taps | Slip | (3) no lining | (4) lining |
|---|---|---|---|
| 0.8 mm, both taps | scons (0.647) | 1.5 / 1.5 / 1.5 / 1.5 | 1.5 / 1.5 / 1.5 / 1.5 |
| | swall (0.91) | 1.0 / 1.0 / 1.0 / 1.0 | 1.0 / 1.0 / 1.0 / 1.0 |
| | s 1.0 | 1.0 / 1.0 / 1.0 / 1.0 | 1.0 / 1.0 / 1.0 / 1.0 |
| | s 0.5 | 1.5 / 1.5 / 2.0 / 2.0 | 2.0 / 2.0 / 2.0 / 2.0 |
| 0.8 mm, FD-01 alone | scons (0.295) | None | None |
| | swall (0.82) | 2.0 / 2.0 / 2.5 / 2.5 | 2.0 / 2.0 / 2.5 / 2.5 |
| | s 1.0 | 2.0 / 2.0 / 2.0 / 2.0 | 2.0 / 2.0 / 2.0 / 2.0 |
| | s 0.5 | 3.0 / 3.0 / 3.5 / 3.5 | 3.0 / 3.0 / 3.5 / 3.5 |
| 1.0 mm, both taps | every bracket | 1.0 at every tilt | 1.0 at every tilt, except s 0.5: 1.0 / 1.5 / 1.5 / 1.5 |
| 1.0 mm, FD-01 alone | scons (0.549) and s 0.5 | 2.0 at every tilt | 2.0 at every tilt |
| | swall and s 1.0 | 1.0 at every tilt | 1.0 at every tilt |

Cap clearing time with both 0.8 mm taps at 0-2 deg (latest over the cases): 1.36 s (scons), 1.17 s (swall), 1.14 s (s 1.0) and 1.77 s (s 0.5; 1.92 s lined).

Table 2.12. N2O vented per relight, and the worst P_abort, by purge time (coarse grid; no lining; worst over every bracket, case, reading, element model and azimuth).

| Configuration | Tp [s] | N2O vented [g] | Worst P_abort, 0-2 deg | Worst P_abort, 4-20 deg |
|---|---|---|---|---|
| 0.8 mm, both taps | 1.0 | 7.1-35.9 | 0.76 | 0.90 |
| | 1.5 | 20.9-55.6 | 0 | 0.11 |
| | 2.0 (draft recommendation, superseded) | 37.6-75.2 | 0 | 0 |
| | 2.5 | 54.4-94.8 | 0 | 0 |
| 1.0 mm, both taps | 1.0 | 24.5-58.4 | 0 | 0 |
| | 1.5 | 52.5-89.2 | 0 | 0 |
| 1.0 mm, FD-01 alone | 1.5 | 22.0-44.9 | 0.43 | 0.44 |
| | 2.0 | 34.4-60.4 | 0 | 0 |
| 0.8 mm, FD-01 alone | 2.0-3.0 | 11.8-57.8 | 0.84-1.0 (scons) | 1.0 |

The lower end of each N2O range is a vapour-full HI segment; the upper end is a mostly liquid LO segment. Liquid at 40 g/s (both 0.8 mm taps) makes up most of the vented mass once the vapour is out, so each extra 0.5 s of margin costs about 20 g.

Tables 2.11 and 2.12 are the coarse-grid trade (0.5 s steps) that preceded the lead's path decision. The draft recommendation they supported (0.8 mm per tap at Tp 2.0 s, commanded at E0 - 2.40 s, 37.6-75.2 g) is superseded (§13).

**The purge time the sweep needs, on a 0.1 s grid** (`purge_duration_v2p4.json`; Electronics S13 relayed "about 76 g per purge at 1.0 mm"). Table 2.13a: worst case at 0 and 2 deg combined, no lining, P_abort <= 1e-3 from that time on.

| Path | Total liquid flow | Needed Tp (s 0.5 / scons) | N2O at the needed Tp | N2O at 2.5 s | Latest cap clearing |
|---|---|---|---|---|---|
| 0.8 mm per tap | 40.0 g/s | 1.5 / 1.2 s | 20.9-55.6 g | 54.4-94.8 g | 1.14-1.76 s |
| 1.0 mm per tap | 62.5 g/s | 1.0 / 0.6 s | 24.5-58.4 g | 108.3-151.0 g | 0.70-1.12 s |
| One 1.0 mm restriction, all flow through FD-01 | 31.25 g/s | 1.8 / 1.7 s | 29.4-54.2 g | 46.7-75.9 g | 1.01-2.06 s |
| **Decided: 2 x 0.707 mm, equal split** | **31.24 g/s** | **1.9 / 1.7 s** | **19.5-54.7 g** | **34.3-72.9 g** | **1.50-2.27 s** |
| FD-01 alone at 0.8 or 0.707 mm | 20.0 / 15.6 g/s | fails | – | 18.6-47.8 g | – |

- Low end of each mass range: a vapour-full HI segment, where the taps pass vapour at 4.25-5.44 g/s each for most of the purge. High end: a mostly liquid LO segment.
- 1.0 mm per tap at 2.5 s vents 108-151 g, twice the 76 g plan: never adopt it (LEAD).
- Tp is the flow time, counted from both bleed valves open to both closed. It is not the command interval.

Table 2.13. Decided path (2 x 0.707 mm), per tilt and lining (`rg01_line_states_v2p4.json`; corrected convention). Needed Tp is the worst slip bracket.

| Lining | Tilt | Needed Tp | Needed Tp by bracket: scons / swall / s 1.0 / s 0.5 | N2O at the needed Tp | N2O at 2.5 s | Latest cap clearing at 2.5 s | Pocket at the lift, 2.5 s |
|---|---|---|---|---|---|---|---|
| None | 0 deg | 1.9 s | 1.7 / 1.2 / 1.1 / 1.9 | 19.5-54.7 g | 34.3-72.9 g | 2.26 s | 4.77-8.15 cm3 |
| None | 2 deg | 1.9 s | 1.7 / 1.2 / 1.1 / 1.9 | 19.5-54.7 g | 34.3-72.9 g | 2.27 s | 4.77-8.15 cm3 |
| 1 mm PTFE | 0 deg | 2.2 s | 2.0 / 1.2 / 1.2 / 2.2 | 26.1-63.9 g | 33.5-73.0 g | 2.45 s | 4.77-8.18 cm3 |
| 1 mm PTFE | 2 deg | 2.2 s | 2.0 / 1.2 / 1.2 / 2.2 | 26.1-63.9 g | 33.5-73.0 g | 2.49 s | 4.77-9.08 cm3 |

- Governing cases:
  - Unlined: s 0.5, open element, isothermal LO dry. At 1.8 s a 0.2 cm3 residual cap behind a 9.6 cm3 slug gives P 0.098 under the "restart" convention. With "paused" alone the time would be 1.7 s (0 deg) and 1.8 s (2 deg). The needed time is therefore set by how completely the cap is cleared, which is what CF-4 measures (P3).
  - Lined: hot-wall HI dry, s 0.5. At 2.1 s a 6.0 cm3 gap behind a 3.8 cm3 slug gives P 0.064.
- In 24 lined records at 2 deg (s 0.5), the cap is still in the line at 2.5 s, behind a slug too long to reach the seat (P 0).
- The tilt does not change the vented mass.

Truncated purge on the decided path (worst over every decision case; corrected convention):

| Flow time [s] | 1.0 | 1.5 | 1.6 | 1.7 | 1.8 | 1.9-2.5 |
|---|---|---|---|---|---|---|
| P_abort, no lining | 1.0 | 0.52 | 0.37 | 0.24 | 0.098 | 0 |
| P_abort, lined | 0.99 | 0.85 | 0.72 | 0.60 | 0.49 | 0.35 (1.9), 0.20 (2.0), 0.064 (2.1), 0 (2.2-2.5) |

A trigger-gate delay must therefore never shorten the flow below 1.9 s, and the ECU hard cap (line 161) must allow 2.5 s of flow plus the valve opening and closing times.

**Why the decided path** (LEAD, line 160, on these numbers):
- It meets the needed time with 0.6 s of margin at 2.5 s, and vents <= 73 g, inside the 76 g plan.
- Against 0.8 mm per tap: it needs 1.5 s, and at 2.0 s vents 37.7-75.2 g, about the same mass with 0.5 s of margin. But it raises the stuck-open flow from 31.2 to 40 g/s, and GNC's stuck-open arms lose more P as the flow rises.
- Against GNC's <= 0.8 mm total (about 20 g/s): that path fails the sweep. The FD-01 tap alone at 15.6 g/s does not clear the humps and the cap on the conservative slip, and the sweep is the A1 blocker.
- Jet reaction per tap 1.6-2.5 N, and 3.3-5.0 N if both taps vented one way (`purge_hazard_v2p4` scaled by area). Joukowsky surge at an instantaneous closure about 2.9 bar (scaled by flow from 3.7 bar at 40 g/s).
- F1: with two 1.0 mm Burkert 6027 HP valves in series with a 1.0 mm-equivalent restriction, the path behaves like a 0.76 mm orifice (<= 18 g/s), close to the 14.1 g/s hump-sweep floor. Hence the >= 4x valve capacity rule.
- F2: the FD-01-to-T4 tee bypasses the 15 um element at 1.8-5.4 g/s during the burn. Hence the check valve or element. Mechanical chose the element (line 162).
- F3: without a restrictor per tap the split is uncontrolled. A split that starves FD-01 is outside every bracket run.
- **FD-01 element deficit** (line 164 check; `fd01_element_deficit_v2p4.json`, `035189ab53929eb2`; DERIVED, CoolProp HEOS with Dyer and HEM). In series with the 0.707 mm restrictor (Cd.A 0.2748 mm2), the element at Cd.A 1.57 mm2 cuts the FD-01 leg flow by 1.5 % (incompressible), 0.7 % (metastable liquid through the element, element dP 0.60 bar), 2.2 % (liquid flashing to equilibrium in the element, restrictor inlet quality 0.8 %) and 0.6 % (vapour, dP 0.26 bar).
  - Bound: needed time <= 1.9 s / (worst leg flow ratio) = 1.94 s, so the margin at 2.5 s is >= 0.56 s. The bound is conservative: T4 keeps its flow, and the s 0.5 bracket that governs does not scale with the column speed.
  - At the coordinator's 4x estimate (Cd.A 1.10 mm2) the cut is 1.4-4.3 % and the bound 1.99 s (margin >= 0.51 s).
  - The margin stays >= 0.3 s down to an element Cd.A of about 0.63 mm2 (DERIVED, approximate 1/(Cd.A)^2 scaling of the flashing reading).
  - The two-flow purge grid is therefore not run. It is run (about 20 min) if the element's measured dP-flow curve (CF-4 P2) gives Cd.A < 0.63 mm2, or if the restrictors are made unequal.

**Purge provision** (Combustion specification for Mechanical and Electronics, through the lead):

| Item | Value | Basis |
|---|---|---|
| Taps | T4 head crown (the existing S12 plug location) and the FD-01 radial plug | Mechanical `bleed_taps_v341_v1`: both are needed while the element is a capillary barrier. If the filter moves off the head, re-run |
| Restrictor (F3) | Two equal sharp-edged restrictors, one per tap, 0.707 mm each (0.71 mm drill), the 1.0 mm equivalent in total; each restrictor flow-tested (CF-4 P2). Cd 0.70 ASSUMED (CF-4 measures) | LEAD line 160; Mechanical line 162; Table 2.13 |
| Valves (F1) | Two NC valves in series on the joined path, each with >= 4x the restriction's flow capacity (seat >= 2 mm, or Kv verified at 55 bar), so the restrictors control. Burkert 6027 HP 1.0 mm does not qualify. 12 V NC coil with peak-and-hold drive (OI-BLEED-COIL). Rated MAWP >= 8.42 MPa and proof >= 10.5 MPa, oxygen-clean, on the fixed side. Drivers hardware-inhibited outside the scheduled purge window. Mass 2 x 0.30 kg is a MASS RISK; target <= 0.15 kg per valve | LEAD lines 154, 160; §2.7 ratings |
| Filtering (F2) | No unfiltered path to the pintle seat during the burn: an inline <= 15 um element on the FD-01 leg, between the tap and the tee, Cd.A >= 1.57 mm2 (4x the restrictor's). FD-01 leg deficit <= 2.2 %, needed time <= 1.94 s. Mechanical supplies the measured dP-flow curve; Cd.A < 0.63 mm2 triggers the two-flow re-run | LEAD line 160; Mechanical line 162; `fd01_element_deficit_v2p4.json` |
| Vent | Balanced (opposed pair) or axial outlet, routed overboard away from the nozzle, case and torch. Both taps venting one way would give 3.3-5.0 N | LEAD; `purge_hazard_v2p4.json` jet bounds scaled by area |
| Lines | 1/8 in lines; a -2 line across the gimbal (Mechanical: +0.5-2 N m/rad of the 17.2 N m/rad budget); engine-side mass 35-50 g | Mechanical provision concept (ESTIMATE) |
| Sequence | PURGE command at E0 - (0.35 + 2.5 + 0.05) = E0 - 2.90 s. MV latch and opener ramp (0.35 s) with the pintle seated; both taps flow for 2.5 s; the close command leads by the measured valve closing time so that the flow has stopped by E0 - 0.05 s. The MV stays open; E0 then proceeds as in §7.3. The ECU caps the bleed-open time at 2.5 s of flow plus the measured valve times. Commit rule (LEAD line 175 (3), PROVISIONAL): PURGE commits no later than the plain relight trigger - 1.7 s, so that >= 1.9 s of flow fits with T_fire delayed by <= 0.6 s; otherwise no purge. The v2.4 rule "the FC delays T_fire" (line 164) is withdrawn. What follows a missed commit is open: Combustion's check refutes "the relight proceeds unpurged" (v2.4a subsection below) | LEAD lines 153, 160, 161, 164, 175 |
| Closure | V1 first, confirmed on P_mid by the closure deadline (<= the torch gate; Electronics E0 + 0.15 s). E1 = torch confirmed AND [closure confirmed OR deadline reached]: at the deadline in flight BLEED_FAULT goes to the FC, V2 is commanded closed and the lift proceeds; on the stand it is an abort. The FC action is LOG-ONLY; closure from P_mid is a pad go/no-go on every flight with the bleed fitted | LEAD lines 160, 166 (3), 168 |
| Cancel | RELIGHT cancelled after PURGE: MV and bleed valves close; the vented N2O is lost | – |
| Monitors | A14 (bleed valve faults) and A15 (pintle or chamber anomaly during PURGE), §7.4 | §7.4 |
| N2O | 34.3-72.9 g per relight at 2.5 s; planned <= 76 g in the A1 reserve | Table 2.13; LEAD line 160 |
| Stuck-open | 31.24 g/s with both taps liquid (upper bound), additive tank outflow | §9.1; GNC S313 |
| Price | TO-QUOTE, Sønderborg DK-6400 (valves, restrictors, the FD-01 element, lines, ports) | – |

Table 2.14. The integrated trade on the decided path: worst P_abort at W 0.65 s at the decision tilts (0 and 2 deg), over every heat case, reading, element model, slip bracket and coast series (`rg01_line_states_v2p4.json`).

| Combination | Worst P_abort | Governing failure |
|---|---|---|
| (1) Re-route alone | 1.0 | Every HI wet case: the whole segment is vapour. Also ARM LO wet 0.24 and hot-wall HI dry 0.65 |
| (2) Re-route + 1 mm PTFE lining (dropped, line 164) | 1.0 | HI wet unchanged |
| **(3) Re-route + purge on the decided path, 2.5 s, no lining: ADOPTED (LEAD line 164)** | **0** | Needed 1.9 s (<= 1.94 s with the FD-01 element) |
| (4) Re-route + lining + purge, 2.5 s (dropped) | 0 | Needed 2.2 s: the lining costs time |

The minimal set is (3) with theta <= 2 deg and a balanced or axial vent. The purge covers LO and HI, wet and dry, so nothing in the set depends on the reading. GNC's relight attitude (max 0.76 deg at RELIGHT; 0 of 500 above 1 deg) lies inside the 2 deg case. v2.4a: the angle that governs the liquid in the segment during PURGE is the specific-force angle to the body axis, not the attitude. GNC rev2 gives up to 2.71 deg raw (2.65 deg as a 0.1 s mean) in six re-flown records (`purge_outlet_inputs.json`), above the 2 deg basis. The purge model is not computed at 2.7 deg (OPEN, OI-35); CF-4 v2.0 adds 3 deg runs.

Table 2.15. Line states for the GNC re-fly (RG-01). Format as `post_abort_pocket_v2p4` "line_states_for_gnc_44cm3": same 200 000-sample ignition set (seed 2024) and E0 -> E1 torch-gate sample. E0 = T_fire. A light requires E1 -> E2 <= W 0.65 s. SIM on ASSUMED delays; line states DERIVED. The 5 % quantiles of E0 -> E2 given a light are in the JSON (`E0_E2_given_light_quantiles_5pct_s`). v2.4a (R2-08): in the PURGE NOT RUN rows the last column is taken over all samples, a would-be time that W does not limit (A2 aborts beyond W); the given-light values are stated in the row.

| Line state | Pocket at the seat [cm3] | P_abort | E0 -> E2 median / p99 / max [s] |
|---|---|---|---|
| Liquid line (reference) | 0 | 0 | 0.315 / 0.462 / 0.499 |
| PURGED, no lining, 2.5 s, worst (ARM HI wet, scons, barrier, 0 deg) | 8.15 | 0 | 0.442 / 0.589 / 0.626 |
| PURGED, no lining, 2.5 s, least | 4.77 | 0 | 0.390 / 0.537 / 0.573 |
| PURGED, lined, 2.5 s, worst (2 deg) | 9.08 | 0 | 0.456 / 0.603 / 0.640 |
| PURGED, no lining, at the needed 1.9 s, worst | 14.88 | 0 | 0.547 / 0.694 / 0.730 |
| PURGE NOT RUN, LO worst (ARM LO wet) | 12.5, then an 11.2 slug and a 23.4 gap | 0.242 | All samples, would-be (A2 aborts beyond W): 0.510 / 1.281 / 1.318. Given a light: median 0.480, p95 0.576, max 0.628. Every such light is followed by the 23.4 cm3 gap (v2.4a subsection below) |
| PURGE NOT RUN, HI worst | 51.8 (whole segment) | 1.0 | All samples, would-be (A2 aborts beyond W): 1.121 / 1.268 / 1.305. No light within W |
| BLEED_FAULT (closure not confirmed; the relight proceeds) | as PURGED | as PURGED | as PURGED; plus 31.2 g/s additive outflow to the end of the flight |

- GNC flies "PURGED, no lining, 2.5 s, worst" as the nominal relight state; "least" is the other end.
- "PURGE NOT RUN" is a failure state: a bleed valve fails closed, the trigger gate never releases, or (v2.4a) the commit deadline of LEAD line 175 (3) passes without a commit. Its probability belongs to the FMEA, not to the nominal.
- E0 -> E3 for the purged states: median 0.482-0.535 s, p95 0.603-0.656 s (v2.4 draft; same pocket range).

**v2.4a: unpurged start at the late-commit point** (LEAD line 175 (3) asks whether an unpurged start carries a hazard outside its abort model; `src/unpurged_start_check_v2p4a.py` `41fad4500f472bd4`, `data/v2p4a/unpurged_start_check_v2p4a.json` `4c745dcfbf09aef7`; SIM on the ASSUMED delays of the rg01 set, which the script reproduces before it extends it, plus DERIVED line states; no grid re-run).

The abort model behind Table 2.15 ends at E2: a light inside a liquid slug counts as a success, and the voids behind that slug are not followed. The check follows them.

Table 2.16. Post-light vapour gap (200 000 samples). Gap timing with the 2500 N/s start ramp to 200 N (volumetric flow scaled by mdot_ox(F) of the S230 map, DERIVED; ramp ASSUMED to start at E2) or with the flow held at the lift (an upper bound on times). Sequences P1 / S1 / C1 in cm3.

| State (0-2 deg) | P(light within W) | Lights followed by a vapour gap | Gap arrival after E2 [s]: ramp / lift flow | Gap duration [s]: ramp / lift flow | P(released, then A3): ramp / lift flow |
|---|---|---|---|---|---|
| PURGE NOT RUN, LO worst, unlined (12.5 / 11.2 / 23.4) | 0.758 | all | 0-0.091 (median 0.053) / 0-0.193 (median 0.094) | 0.139-0.156 / 0.365 | 0.712 / 0.717 |
| PURGE NOT RUN, LO worst, lined (15.6 / 12.4 / 19.2; lining dropped, line 164; reference) | 0.865 | all | 0-0.101 (median 0.058) / 0-0.220 (median 0.108) | 0.113-0.131 / 0.298 | 0.819 / 0.825 |
| PURGE NOT RUN, least, unlined (12.0 / 34.4 / 0.74) | 1.0 | all | 0.196-0.295 / 0.470-0.731 | 0.004 / 0.011 | 0 / 0 (dip shorter than the 22 ms A3 detection) |
| PURGE NOT RUN, HI worst (51.8, whole segment) | 0 | - | - | - | 0 (no light; A2 abort under the drogue) |
| PURGED 2.5 s, worst, unlined and lined; lined 2.2 s robust edge | 1.0 | none | - | - | 0 |

- **Release.** E2 in the latency model is Pc > 3 bar abs held 10 ms, so the drogue-release term (Pc valid AND >= 300 kPa abs, LEAD line 168 (1)) is already true at E2; the release follows within one 10 ms telemetry frame. On the 200 N ramp the unlined gap arrives before the 0.10 s hold of b7 in every sample, so b7 is never the first term.
- **A3 in the gap.** The oxidiser flow falls to 0.23 of the liquid flow (saturated vapour 128.2 against liquid 830.2 kg/m3 at 286.7 K, CoolProp). The A3 ratio in the gap is 0.008-0.030 at 62.5 N, 0.085-0.10 at 100 N, about 0.17 at 200 N and <= 0.24 at 500 N (CEA c*, n 0.35-0.68 ASSUMED, flame assumed to survive), below the 0.40 threshold, so A3 trips about 22 ms into the gap and aborts. A vapour light at the lift flow gives Pc 1.04-1.11 bar abs, below E2.
- **Consequence.** In 0.712 of the LO-worst starts (0.94 of its lights) the vehicle is released from the drogue and the engine then aborts. That is GNC's "dead vehicle released" class (touchdown about -32 m/s in GNC rev2, line 174), not the abort under the drogue that the model assumes (about -22 m/s). The same model leaves no successful relight in that state: P_total is about 0, not the 0.75 assumed in line 175 (3).
- **Population** (all PURGE NOT RUN records at 0 and 2 deg; bracket cases, not probability-weighted; first 20 000 samples): a light followed by a gap in 499 of 540 unlined LO records (mean P(released, then A3) 0.58), 477 / 540 lined LO (0.52), 180 / 540 unlined HI (0.22) and 270 / 540 lined HI (0.44).
- **Purged states:** no post-light gap. The 2.5 s purge removes the hazard. The HI worst unpurged state never lights within W and adds nothing new.
- **FA-1 interaction.** At 200 N the pintle seats before the liquid returns (no re-admission). On a 500 N ramp, 25 % of the trips re-admit liquid before the seat: <= 3.56 g with the flow held at the command point (above the 2.141 g FA-1 fast part) or <= 0.53 g with a linear closing. It matters only if the flame went out in the gap, which is not modelled.
- **Verdict (SIM/DERIVED, not physical).** The provisional rule is refuted as written: an unpurged start at the late-commit point carries a hazard outside its abort model (H20).
- **Proposal for the lead.** No commit by the plain trigger - 1.7 s -> no relight on that pass, as A14 does for a fail-closed bleed. A ride-through mode (drogue release held on unpurged starts; torch kept on and A3 adapted through the gap) is a research option only. Hypothesis: the flame survives a 0.14-0.37 s vapour gap. Comparator: the no-relight rule. Evidence needed: CF-4 optional run O-3 and IGN-1 on the dynamic Pc channel. Refutation: a flame-out or an A3 trip in the gap.
- **Limits.** Two-convention bracket of the trade (paused, restart; the larger result is kept); the ramp start at E2 is ASSUMED; flame survival through the gap is not modelled (if the flame goes out the ratio is lower and A3 trips sooner); no slosh or tilt above 2 deg.

**v2.4a: outcome classes, LO or HI, and L\* (LEAD line 181 (2))** (`src/unpurged_outcomes_v2p4a.py` `8256face5bcf7b27`, generated by `gen_unpurged_outcomes_v2p4a.py` as a verbatim copy of the parent check's code; `data/v2p4a/unpurged_outcomes_v2p4a.json` `18a639d61b58ce8a`; it reproduces the parent's P(light), P(light then gap) and P(released, then A3) to 1e-12 before it classes the starts). Line 181 (2) sets the PURGE deadline as a P_total-maximising rule: L* = 1.7 s if an unpurged start is LO (break-even against P_total ~0.75) and 1.3 s if HI (P_abort 1.0), and asks which applies.

Table 2.17. Outcome of an unpurged start (each start in exactly one class; Pc valid; A3 per §7.4; values: 2500 N/s start ramp / flow held at the lift). Population rows: mean over all PURGE NOT RUN records at 0 and 2 deg (540 each; bracket records, not probability-weighted).

| State | No light (A2, drogue held) | A3 before the release | Released, then A3 | Success |
|---|---|---|---|---|
| PURGE NOT RUN, LO worst, unlined (12.5 / 11.2 / 23.4) | 0.242 | 0.046 / 0.040 | 0.712 / 0.717 | 0 |
| PURGE NOT RUN, LO worst, lined (reference) | 0.135 | 0.046 / 0.040 | 0.819 / 0.825 | 0 |
| PURGE NOT RUN, HI worst (51.8) | 1.0 | 0 | 0 | 0 |
| PURGE NOT RUN, least, unlined and lined | 0 | 0 | 0 | 1.0 (unlined: a dip shorter than the A3 detection) |
| PURGED 2.5 s worst, unlined and lined; lined 2.2 s robust edge | 0 | 0 | 0 | 1.0 |
| Population, LO, unlined | 0.012 | 0.005 | 0.58 / 0.80 | 0.40 / 0.18 |
| Population, LO, lined | 0.003 | 0.003 | 0.52 / 0.77 | 0.47 / 0.23 |
| Population, HI, unlined | 0.771 | 0.008 | 0.22 / 0.22 | 0 / 0 |
| Population, HI, lined | 0.516 | 0.006 | 0.44 / 0.48 | 0.04 / 0 |

- **LO or HI.** Not settled, and not settleable by analysis. LO and HI are the two ends of Mechanical's wall heat-transfer bracket (segment heat cases isothermal, hw+5K and ARM_bay45C_liq24C, each at h LO and h HI) that sets how much liquid in the segment flashes during the coast. Both ends are ASSUMED; no evidence supports or excludes either. CF-4 optional generation runs and T4 measure it (§11 item 32).
- **The decision does not need it.** At the worst states an unpurged start succeeds with P = 0 under both ends: HI because it never lights, LO because every light is followed by the vapour gap and A3. GNC's LO premise (P_total ~0.75 = 1 - P_abort) counted every light as a success, which the abort model never checked. In the population, P(success) per record is bimodal (0 or 1): 0 in 82 % of the unlined and 77 % of the lined LO records, and in every HI record. The released-then-A3 hazard is present under both ends (population means 0.52-0.80 LO, 0.22-0.48 HI).
- **Recommendation (SIM/DERIVED; the lead decides, OI-31).** FSW L* = 1.3 s (the HI value): PURGE commits whenever the lead to the plain trigger is >= 1.3 s. Below 1.3 s, no unpurged relight on that pass (no purge -> no relight, as A14), unless GNC shows that holding the drogue release on unpurged starts to >= E2 + 0.22 s (gap arrival <= 0.193 s with the flow held at the lift, plus 0.022 s A3 detection) gains P. With that hold the light-gap-A3 sequence aborts with the drogue attached.
- **Hazard (evidence class SIM on ASSUMED delays + DERIVED line states).** RELEASED_THEN_A3: light, drogue release at E2 (Pc >= 3 bar abs), post-light vapour gap, A3 abort: a dead vehicle released (GNC's class, about -32 m/s at touchdown against about -22 m/s on the drogue). Per start: 0.712 (unlined) and 0.819 (lined) at the LO worst states.

ENG-04 status is in §7.7.

**The PRIMED flag.** A segment full of saturated vapour reads P_feed = P_tank, so it reads PRIMED; MSS-1 and MSS-2 read T_sat either way (Electronics). PURGE therefore runs on every A1 relight, whatever the flag says. Unpriming within a coast needs >= 1 g/s of seat leakage, i.e. a stuck-open pintle (Mechanical), so UNPRIMED in flight is a fault indication. The fault path (§7.3) runs the PREPRESS and then PURGE.

**Refutation criteria for the recommendation** (any one refutes it, and Combustion re-runs the trade):
1. **CF-4** (§10.3) at 0 and 2 deg (az 45 and az 180), from a vapour-full and an ARM-LO-like segment, on the decided path with 2.5 s of flow. Any one of these refutes the claim for that state:
   - the first continuous liquid at the pintle inlet comes later than 0.293 s after the pintle reaches the lift;
   - a later void falls outside the Table 10.4 budget (simple form: less than 0.35 s of continuous liquid after the first liquid).
   The model is also refuted, and the trade is re-run with the measured value, if:
   - the cap needs more than 2.3 s to clear;
   - either tap passes less than 80 % of the modelled vapour or liquid flow;
   - hump vapour is still visible at 2 deg after the purge.
2. **CF-4 generation runs**, if the measured void growth of the full trap matches the "wet" reading in LO: the re-route-alone pass in LO at 2 deg is then confirmed or withdrawn for the measured case.
3. **IGN-1/T1:** the ignition-delay p99.9 exceeds 0.30 s. That moves V_zero and every margin above.
4. **GNC:** P(landing) with 76 g less N2O per relight (PS10 flew 94.5 g), or with PURGE committed 2.90 s before T_fire, falls below the lead's threshold. Also: the canopy swing at RELIGHT exceeds 2 deg.
5. **Mechanical:** the wetted seat face exceeds 800 K at any time from MECO to E1 (§9.1), or the FE heat on the v3.4.1 route exceeds the cases used by more than 25 % in the head trap.

**Research proposal (dropped by the lead, line 164): PTFE lining of the route.**
- Hypothesis: lining the hose region and wall line with >= 1 mm PTFE cuts the delivered heat to 0.23-0.31 of unlined (Mechanical) and removes the need for the purge.
- Comparator: the unlined re-route with the purge.
- Evidence: the route heat falls by about half in HI (44-54 %), but the head trap carries 82-87 % of the HI heat and the lining does not reach it. Without the purge, HI wet stays at P_abort 1 (Table 2.10).
- Refutation criterion, met: no lined case passes HI wet at 0-2 deg without the purge. The proposal is refuted as a replacement for the purge. The lead dropped it (line 164); it is reopened only if CF-4 shows the wet reading wrong.

**Research proposal (not adopted): sensed purge end.**
- Hypothesis: a 0.5 mm sheathed thermocouple in each tap jet sees liquid arrival as a step toward the 1 bar saturation temperature (-88.5 C). Ending the purge a fixed margin after the cap has passed both taps would cut the vented N2O from 34.3-72.9 g toward the 19.5-54.7 g of the needed time.
- Comparator: the fixed 2.5 s flow.
- Evidence needed: CF-4 runs with thermocouples in both jets and the void probe at the injector.
- Refutation criterion: the signal takes longer than 50 ms, does not separate vapour from liquid, or misses the cap passage.

**Carried from the v3.4 analysis (still valid).**

Single-pocket abort curve (SIM on ASSUMED delays; `post_abort_pocket_v2p4.json`; MV open before the lift; W from the lift command). It underlies every P_abort above.

| Pocket [cm3] | 0 | 8 | 12 | 16 | 18.86 | 20 | 22 | 24 | 30 | 44 |
|---|---|---|---|---|---|---|---|---|---|---|
| P_abort, W 0.65 s, 0.2039 mm | 0 | 0 | 0 | 0 | 0 | 0.046 | 0.17 | 0.29 | 0.67 | 1.00 |
| E1 -> E2 maximum [s] | 0.357 | 0.481 | 0.543 | 0.606 | 0.650 | 0.668 | 0.699 | 0.730 | 0.823 | 1.041 |

Segment contents (DERIVED; 48.23 / 50.04 cm3):

| State | Liquid-full [g] | Vapour-full [g] | Whole-segment purge through the pintle [s] |
|---|---|---|---|
| A1 relight state (286.7 K, 43.5 bar) | 40.0 / 41.5 | 6.18 / 6.41 | 0.750 / 0.778 at 0.2039 mm |
| 15 / 20 / 25 C | 39.6 / 37.8 / 35.8 (barrier) | 6.47 / 7.62 / 9.11 (barrier) | Same |

Shutdown order (SIM, `segment_drain_v2p4.json`, computed on 44 cm3; the vapour volumes scale with the segment):
- Normal shutdown is pintle-first (LEAD), so the segment is liquid-full at MECO. The coast then fills the traps, and in HI wet the whole segment, with vapour. Pintle-first minimises the starting vapour but no longer guarantees a primed relight.
- An abort is MV-first (the NC valve is the fail-safe). It empties about half the segment (22-24 cm3 of vapour at the 30 ms close). The next attempt is a vapour start (LEAD), which PURGE clears like any other.

Options rejected or dropped by the lead (numbers for the record; they do not depend on the routing):
- **Wider W:** a vapour-full segment needs W >= 1.11-1.14 s on v3.4.1 (48.2-50.0 cm3; 1.041 s for the old 44 cm3). Already at W 1.05 s a liquid line takes 36.8-40.3 g of unignited N2O (40.0 g at 24 C), against the 26.6 g accepted.
- **Prep path at W 0.88 s:** 30.9-33.8 g without the PREPRESS bleed and 38.0-41.7 g with it (41.4 g at 24 C); both exceed 26.6 g. The SIL's 0.17 s prep-path purge credit is not reproduced on Combustion's plant (disagreement kept; CF-4 can settle it).
- **(d), early MV opening under the drogue:** it reaches neither the head trap nor the humps; it removes only dry caps. It also puts tank pressure behind a seated pintle for 9.3-15.6 s.
- **Drain pose:** refuted by Mechanical at 10 deg; partial help below about 4 deg.

**Stand rules on v3.4.1** (LEAD stand relief (b): aft DN32 disc only, R1 = R2 = 0.35 s, rounded port entrance; §7.6):
- The liquid-line inventory at W does not depend on the segment volume. Unignited N2O admitted by the deadline W, from the lift command, at the 0.2039 mm lift (DERIVED, `relight_window_rule_seg44_v2p4.json`; Dyer, Cd 0.70 ASSUMED):

  | W [s] | Liquid line, A1 state / 15 C / 20 C / 25 C [g] | At the 24 C interlock [g] |
  |---|---|---|
  | 0.35 | 12.4 / 12.6 / 13.1 / 13.6 | 13.5 |
  | 0.65 | 22.9 / 23.2 / 24.2 / 25.0 | 24.9 |
  | 0.85 | 29.8 / 30.2 / 31.5 / 32.7 | – |
  | 1.05 | 36.8 / 37.3 / 38.9 / 40.3 | 40.0 |

  At 0.35 s and 24 C that is 13.5 g against the 13.84 g allowable of the aft DN32 disc with the rounded entrance (§7.6).
- At 0.35 s even a primed start aborts 0.5 % of would-be lights (E1 -> E2 max 0.357 s), and any pocket at the seat raises that steeply. Stand relights therefore need the seat primed.
- PURGE replaces the v3.4 crest bleed as the stand procedure. It clears the traps and the cap but not the 4.42 cm3 annulus, which is counted as vapour (conservative).
- T4 records the abort rate of purged relights at 0.35 s. An abort there is data, not a hazard: the inventory stays within the allowable.
- No stand test lights a vapour start within the 13.84 g allowable (OI-23).

## 3. Throttle and shutoff architecture

### 3.1 Trade and decision

Three architectures were compared (`src/throttle_trade.py`), evaluated at the v1-grain points. The S230 points need 6 % more oxidiser flow at 100 %, which does not change the ranking.
- (a) V-ball valve upstream with a fixed injector.
- (b) Variable-area pintle.
- (c) Valve with a showerhead.

Table 3.1. Throttle trade (SIM/DERIVED, `throttle_trade_v2.json`).

| Throttle % | Pc [bar] | mdot_ox [g/s] | (b) lift [mm] | (b) dP/Pc | (b) dF/dh [N/mm] | (a,c) vapour quality after valve | (a,c) dP/Pc | (a) manifold tau [ms] | (c) manifold tau [ms] |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 24.99 | 226.6 | 1.765 | 0.94 | 177 | 0.028 | 0.94 | 0.0 | 0.2 |
| 75 | 19.11 | 168.5 | 1.164 | 1.58 | 242 | 0.028 | 1.54 | 0.0 | 0.2 |
| 50 | 13.25 | 113.0 | 0.711 | 2.78 | 319 | 0.118 | 2.08 | 0.0 | 0.2 |
| 25 | 7.36 | 61.3 | 0.358 | 5.84 | 390 | 0.273 | 2.27 | 0.1 | 0.4 |
| 20 | 6.18 | 51.5 | 0.296 | 7.16 | 410 | 0.304 | 2.33 | 0.1 | 0.4 |
| 12.5 | 4.36 | 36.3 | 0.205 | 10.57 | 371 | 0.355 | 2.43 | 0.1 | 0.5 |

Criteria:
- Flashing. (b) meters at the injector with single-phase liquid upstream. (a) and (c) flash between valve and injector, with vapour quality 0.27-0.36 at <= 25 % throttle.
- Chug margin. At 12.5 %, dP/Pc is 10.6 for (b) against 2.4 for (a) and (c).
- Linearity. For (b), dF/dh varies by 2.3x over the range and K_h by 2.7x (Table 3.3); this is handled by gain scheduling.
- Response. The chamber fills in 4 ms; manifold time constants are <= 0.5 ms.
- Shutoff tightness. (b) gives two barriers, the seat and the NC valve.
- Cost and buildability. (b) needs custom machining; (a) uses a COTS V-ball valve.
- N2O compatibility. All three need oxygen cleaning.

Decision (LEAD 2026-10-11, confirmed by the v2 trade): a servo-driven variable-area pintle at the head end, plus a separate normally-closed main isolation valve upstream, on the tank side and off the gimbal.

v2.4 status of the isolation valve (LEAD 2026-10-13; CHANGELOG):
- **MV-P**, a balanced poppet with electric actuation, is the baseline. It is integrated in the FS-01 module at the top of the engine zone (option A), with a fixed 3/8 in line down the case wall to the O3b coil.
- Values used here: Cv 3.6 (Cd 0.65 ASSUMED by Mechanical); fail-safe closed bias; over-centre latch; dashpot close of about 30 ms (0.10 s is the bounding value, B-MV-1 measures it); body MAWP >= 8.42 MPa and proof >= 10.5 MPa (§2.7).
- B-MV-1 gates MV-P. The fallback is a Swagelok 62-series ball valve with a pneumatic spring-return actuator. The custom oxidiser valve is a programme risk (LEAD).
- The v2.3 values "MEOP 70 bar, closes in <= 0.15 s" are superseded by the MAWP basis (§2.7) and the 0.10 s bounding close.
- The FS-01 module also carries S1 (back-relief check to the tank), MSS-2, the P_feed transducer J602 and the secondary disc (§2.7).
- Price TO-QUOTE (Sønderborg DK-6400).

### 3.2 Flow area against position

A(h) = pi h sin(a) (D_s - h sin(a) cos(a)), with a = 15 deg and D_s = 5.5 mm. A is 15.2 mm2 at the 4.2 mm stop.

Files:
- `data/pintle_area_vs_lift_v1.csv`: geometric area.
- `data/v2/engine_S230/throttle_map_v2.csv`: lift for each thrust fraction. Axes are P_tank 35-55 bar, D_port 25-45 mm and fraction 0.125-1.
- The ceiling column is the lower of the 4 mm stroke and the lift where dP/Pc reaches 0.25.

Lift is 1.916 mm at 100 % and 0.207 mm at 12.5 % (20 C, initial port).

### 3.3 Actuator requirements (for Mechanical and Electronics)

| Item | Value | Tag |
|---|---|---|
| Stroke | 4.0 mm; mechanical stop 4.2 mm | v1 / Mechanical |
| Position resolution | <= 10 um. A 0.5 % F_max deadband open-loop needs 16 um at 100 % and 6.8 um at 12.5 %. Closed loop it is 0.13 bar Pc at 100 % and 0.17 bar at the floor (OI-13). | DERIVED |
| Full-stroke time | The v1 value of 0.08 s is retired (no combustion basis). ENG-05 (< 10 % thrust within 0.10 s) from 100 % needs <= 0.205 s. From 75 %, a 0.25 s drive gives 0.082 s. | SIM, LEAD |
| MECO rule | GNC throttles down to <= 75 % before MECO. The spring assists closing. Closing time at 25 bar is measured in B-PNT-1. | LEAD 2026-10-12 |
| Slew and response | >= 2 F_max/s and t10-90 <= 0.15 s (gnc.json v2 ENG-03). The start ramp cap is <= 2500 N/s. | gnc.json v2 / DERIVED |
| Needle forces | Law and envelope in §3.5 | DERIVED |
| Servo environment | HV69 rated -10 to 60 C; mount limit 50 C in flight, including relight (OI-15) | Mechanical/Electronics |

Shutdown tail-off with the pintle closing in 0.08 / 0.149 / 0.240 / 0.250 / 0.400 s full stroke (SIM):
- time to < 10 % from 100 % is 0.052 / 0.078 / 0.115 / 0.119 / 0.182 s;
- tail-off impulse is 16.4 N s at 0.08 s and 36.3 N s at 0.25 s.

### 3.4 Plant model for the Pc loop

Pc(s)/h(s) = K_h [ (1 - phi)/(tau_c s + 1) + phi/(tau_f s + 1) ]. The model is fitted to +3 % lift steps of the quasi-1D model with the tank frozen at 50.5 bar (SIM, `engine_S230/plant_valve_to_pc_v2.json`).

| Throttle % | Lift h0 [mm] | Pc0 [bar] | K_h [bar/mm] | dF/dh [N/mm] | tau_c [ms] | tau_f [ms] | phi |
|---|---|---|---|---|---|---|---|
| 100 | 1.900 | 25.03 | 7.55 | 159 | 4.0 | 107 | 0.060 |
| 50 | 0.751 | 13.22 | 13.65 | 290 | 4.0 | 181 | 0.094 |
| 25 | 0.366 | 7.34 | 17.77 | 378 | 4.0 | 316 | 0.089 |
| 12.5 | 0.206 | 4.37 | 20.11 | 369 | 4.0 | 528 | 0.053 |

- The injection and vaporisation delay is 3-10 ms (ASSUMED).
- K_h grows 2.7x toward the floor, so a gain-scheduled closed Pc loop is needed.
- The slow fuel/thermal mode (0.3-1.5 Hz) lies inside the 2.3 Hz Pc-loop bandwidth of gnc.json v2 (OI-2).

### 3.5 Pintle force law (v2.3 review of Mechanical's pintle v2), seat and seal (v2.4)

**Stem.** Mechanical reduced the stem through the seal from 4 mm to 3 mm.
- The stem area is not in the injector flow model. Flow passes the seat annulus; the stem only sets the bonnet pressure area. The throttle map is unchanged.
- Bonnet volume increases by 0.14 cm3. Stem conduction falls from 2.3e-3 to 1.3e-3 W/K, which leaves the head-end BC unchanged.
- Pressure areas: A_seat = 23.758 mm2; A_stem = 7.069 mm2.

**Force law.** + is the closing direction. Script: `src/needle_force_v2p3.py`; output `data/v2/needle_force_bounds_v2p3.{csv,json}`.
- Mechanical's v2-v2.2 law blends to the opening bound -dp A_stem after 0.1 mm of lift. This is L0. It is conservative for the closing check C1, but not for the opening check C2. The seat gap keeps metering at every lift, so a closing pressure force persists.
- L1 (central) uses the geometric throat. L2 (upper bound) uses the seated area at every lift.

Unlit at 70 bar, L1 gives 115.1 / 100.6 / 86.7 / 61.0 / 37.9 / 17.6 / 13.9 N at h = 0 / 0.5 / 1 / 2 / 3 / 4 / 4.2 mm. L2 stays at 115.1 N at every lift.

Bounds:
- Seated at 70 bar: +115.1 N.
- L0 open bound: -48.8 N.
- Hot-fire envelope over the map:
  - L0 minimum -38.1 N;
  - L1 -12.6 to +77.7 N;
  - L2 maximum +82.0 N.
- L1 and L2 differ by up to 163.9 N at MEOP above 0.1 mm lift.

Flashing at the gap moves the force toward L0. B-PNT-1 measures F(h, P).

Rule, adopted by the lead: C1 (spring closing) is evaluated on L0; C2 (servo opening) on L1, with L2 as the sensitivity case.

**Re-run with Mechanical's own code** (`pintle_inline_v34.py`, sha256/16 10f5130fb51147ea). L0 reproduces Mechanical exactly:
- v2: 0.59 / 0.05;
- v2.1: 0.593 / 0.05 / 0.082;
- v2.2: 0.597 / 0.537 / 0.047 / 0.094.

Table 3.4. C2 opening margins at the 7.4 V servo rail. The requirement is >= 1.5 (SIM with Mechanical's servo_torque).

| Configuration | Flight hot-fire line (L1 / L2) | Start to 0.3 mm, 70 bar (L1 / L2) | Start, 50.5 bar (L1 / L2) | Unlit full stroke at MEOP, ground (L1 / L2) |
|---|---|---|---|---|
| S3, 0.30/0.10, PTFE mu 0.20 (lead baseline at the time) | 1.47 / 1.37 | 1.32 / 1.28 | 1.50 / 1.46 | 1.11 / 0.81 |
| v2 spring, PTFE mu 0.18 (0.18/0.175) | 1.89 / 1.67 | | | |
| v2.1 spring, PTFE mu 0.10 (0.19/0.17) | 1.85 / 1.64 | | | |
| **Rolling guide, plain pins, 0.25/0.12 (adopted)** | **1.62 / 1.62** | | | |

Spring feasibility window (`src/pintle_spring_window_v2p3.py`, `data/v2/pintle_spring_window_v2p3.json`):
- Criteria: C1 >= 0 under L0 with the -10 % spring; flight C2 <= 0.60 N m under L1/L2 with the +10 % spring.
- PTFE mu 0.20: one feasible spring under L1 (0.21/0.15, MEOP assist only 0.004 N m) and none under L2. There is no robust spring.
- PTFE mu 0.10: 138 (L1) and 117 (L2) feasible springs.
- Rolling guide, hypothetical: 272/257 feasible springs with plain pins (T0 0.10-0.33 N m) and 335/322 with ball pins.
- The adopted 0.25/0.12 spring gives a MEOP closing assist of 0.108 N m and a nominal seat load of 292 N.
- The final guide and pins are Mechanical's. Their v2.3 run carries L1/L2 natively and supersedes these hypothetical rolling-guide numbers.

**Seat (v2.4).** Metal-to-metal: a 15 deg 17-4PH H900 needle on a 5.5 mm sharp-edged seat with a 0.3 mm lapped land (land area 5.184 mm2). The seat insert TC-03 is now **Inconel 718** (LEAD 2026-10-13). Mechanical's upper-bound in-burn face temperature on A1 is 695-712 C, above the about 621 C ageing temperature of 17-4PH H1150 (AS RECALLED). The flux bound could not be narrowed with evidence, so the alloy changes. 17-4PH H1150 may return if the T1 thermocouples, 1 mm behind the seat face, show <= about 350 C.

Table 3.5. Seat loads and land contact pressure (DERIVED). Normal factor on the land is 3.864 at mu 0 and 1.823 at mu 0.3. Net pressure area 16.689 mm2 (A_seat - A_stem).

| Case | S3 load [N] | Land pressure, mu 0 / 0.3 [MPa] | Adopted 0.25/0.12 load [N] | Land pressure, mu 0 / 0.3 [MPa] |
|---|---|---|---|---|
| -10 % spring, bench | 315.1 | 234.9 / 110.8 | 262.6 | 195.7 / 92.3 |
| nominal | 350.1 | 261.0 / 123.1 | 291.8 | 217.5 / 102.6 |
| +10 % | 385.1 | 287.0 / 135.4 | 321.0 | 239.3 / 112.9 |
| +10 % at 7.0 MPa | 500.3 | 372.9 / 175.9 | 436.1 | 325.1 / 153.4 |
| +10 % at 7.5 MPa | 508.6 | 379.1 / 178.9 | 444.4 | 331.2 / 156.3 |
| +10 % at MAWP 8.42 MPa (v2.4) | – | – | 459.9 | 342.8 / 161.7 |
| +10 % at proof 10.5 MPa | 558.7 | 416.4 / 196.5 | 494.5 | 368.6 / 173.9 |

Strength (RC-15):
- Inconel 718, aged: room-temperature Fty about 1030 MPa (AS RECALLED; AMS 5662/5663 class). The land then works at 33 % of Fty at MAWP and 36 % at proof. In718 keeps most of its strength to about 650 C (AS RECALLED).
- 17-4PH H900 needle: Fty about 1170 MPa (AS RECALLED).
- These values are TO-VERIFY against maker data or MMPDS before the seat and needle drawings are released (RC-15). The v2.3 values for H1150 (724 MPa; 0.85 x at 316 C; creep negligible below 370 C) were also AS RECALLED and are no longer load-bearing for the seat.
- The upper-bound face peak (695-712 C) lies near the In718 ageing temperatures (about 620-720 C, AS RECALLED). The exposure is seconds per flight. Land stability over repeated cycles is TO-VERIFY: T1 thermocouples, and inspection of the land by bluing after T1 and T4.

Thermal expansion (DERIVED). The CTEs of In718 (about 13.0 um/m/K) and 17-4PH (about 10.8-11 um/m/K) are AS RECALLED. The mismatch moves the seat line by about 6-7 um of lift per 300 K of common temperature rise (5.5 mm seat, 15 deg cone).
- At the 0.2039 mm ignition lift that is about 3 % of the flow area on a hot relight. It is inside the CF-3 lift calibration band and is recorded with the head temperature at T4.
- The v2.3 rejection of Nitronic 60 (about 16 um per 300 K) is unchanged.

Conditions (v2.3 conditions carried over, with the v2.4 seat):
- Needle and stem H900; seat insert In718 (aged).
- Galling of In718 against hardened 17-4PH is TO-VERIFY in B-PNT-1 cycling, with inspection of the land.
- Lapped contact band >= 0.24 mm all round, checked by bluing. A 0.15 mm band would reach 758 MPa at the relief load and coin the land; 0.24 mm gives 474 MPa.
- PFPE film on the land.

Self-locking. tan 15 deg = 0.268, so the cone wedges if the seat friction coefficient exceeds 0.27.

Table 3.6. Crack-open margin at MEOP against seat friction (Mechanical's servo_torque, guide amplification included).

| Configuration | mu 0 | 0.3 | 0.4 | 0.5 | 0.6 |
|---|---|---|---|---|---|
| S3, PTFE 0.20 | 1.68 | 1.55 | 1.31 | 1.17 | 1.08 |
| Rolling guide, 0.25/0.12 | 2.14 | 2.01 | 1.75 | 1.60 | 1.49 |

B-PNT-1 measures the break-out torque after a dwell closed at MEOP.

Polymer seat: not feasible. Land pressure of 111-379 MPa exceeds the compressive strength of PTFE (about 10-15 MPa), PCTFE (about 30-50 MPa) and PEEK (about 120 MPa), all AS RECALLED. PCTFE is also limited to about 150 C against the 339-586 K soak band.

**Leak tightness (v2.4; RC-02, RC-13 g).**
- **Acceptance** (adopted by the lead, 2026-10-13, as proposed by Mechanical):
  - B-PNT-1 seat <= 10 sccm GN2 at 56 bar, at room temperature and after a 150 C soak;
  - stem seal <= 1 sccm;
  - MV-P seat Class VI at 56 and 84.2 bar (room temperature and 60 C);
  - CF-3 logs J602 and the segment thermocouple decay on every closed hold.
- **Coast leak ceiling.** The accumulated seat leak over the longest A1 coast stays <= 10 % of the smallest credible fast part of a hard start (§7.6): 0.10 x 1.22 g over 22.21 s gives 0.0055 g/s (DERIVED). This replaces the v2.3 ceiling of 0.039 g/s, which inherited the 8.74 g inventory.
- **Consistency of the acceptance with the ceiling** (DERIVED, TO-VERIFY at CF-3):
  - 10 sccm of GN2 is 2.1e-4 g/s of N2.
  - The same leak path passes liquid N2O at 1.0-1.4e-3 g/s at tank pressure. Factors: x4.6 for a laminar path (viscosity and density ratio) and x6.5 for an orifice path (density ratio at the same pressure drop).
  - That is 4-5x inside the 0.0055 g/s ceiling.
- **Leak models outside the acceptance.** Mechanical's Class V-scaled seat leak (13.5-15.5 mg/s) and its 15 um particle case (77-82 mg/s) exceed the ceiling by 2.5-15x. They are fault cases: a seat that fails B-PNT-1, or a particle on the seat. They are not the design leak. The filter (<= 15 um) and the cleaning rules (§10.1) are the controls.
- **Draining.** Mechanical shows that unpriming the segment needs >= 1 g/s, i.e. a stuck-open pintle (seat_leak_drain_v1, computed on 44 cm3; the v3.4.1 segment is 10-14 % larger). A leak within the acceptance does not change the relight state within a coast.
- **Operating rule** (LEAD): the MV stays closed during coasts. In the v2.8 sequence it opens at E0 with the pintle seated (§7.3). On an A1 relight it opens at the PURGE command, 2.90 s before E0, still with the pintle seated (LEAD provision, §2.8). During PURGE the seat leak rate does not change, because S1 holds the segment at P_tank through the coast either way; the leaked mass over the 2.99-3.06 s exposure is 2.9-4.2 mg at the acceptance (§9.1). Option (d), the MV opened under the drogue, stays dropped (§2.8).

**Rod seal.** A spring-energised PTFE-family seal is suitable in principle for a 3 mm rod in N2O at the 8.42 MPa MAWP and 10.5 MPa proof (ASSUMED).
- Temperature range: from -88.5 C (N2O normal boiling point, venting; CoolProp) up to the bonnet temperature from Mechanical's FEA. The PTFE jacket limit is about 260 C (AS RECALLED, TO-VERIFY). It lies inside the 339-586 K head soak band, so the seal temperature is checked in Mechanical's FEA (RC-15).
- Vendor classes, all TO-VERIFY per part:
  - Trelleborg Turcon Variseal M2 (rod);
  - Saint-Gobain OmniSeal 103A class;
  - Parker FlexiSeal;
  - Bal Seal canted-coil.
- Specification:
  - virgin PTFE or an oxygen-compatible filled jacket;
  - Elgiloy, Hastelloy or 17-7PH spring;
  - oxygen-cleaned, PFPE lubricant only;
  - split or open gland;
  - rod Ra 0.1-0.2 um, H900.
- Friction is 1-5 N (DERIVED). Mechanical's ASSUMED 18.75 N is conservative.
- Price TO-QUOTE (Sønderborg DK-6400).

**Stem buckling.** Link compression is <= 385 N, i.e. 54 MPa on the 3 mm stem. Euler load over an ASSUMED 40 mm free length is 4.8 kN, a margin of 13. Mechanical confirms the free length.

**Operating rules** (LEAD 2026-10-12, updated 2026-10-13):
1. Hold the ignition lift until Pc confirms light. A no-light abort de-energises the MV and closes the pintle in parallel (§7.4).
2. N2O cold flows go into a back-pressured catch volume with its own relief and vent (§10.1). Full-stroke checks use N2 at <= 3.5 MPa.
3. Keep the MV closed during coasts. It opens at E0 with the pintle seated (v2.8), or at the PURGE command of an A1 relight (E0 - 2.90 s; §2.8, §7.3).

### 3.6 Failure case and the MEOP basis (v2.4; RC-08)

Table 3.7 is the v2.3 basis. It is kept as evidence and is superseded below.

Table 3.7. Pintle stuck at full stroke (4 mm), initial port (SIM, `full_stroke_failure_case_v2.json`; v2.3 simulation line-loss law, eta_c* 0.92).

| T [C] | P_v [bar] | Cd | Pc [bar] | F [N] | O/F | dP/Pc |
|---|---|---|---|---|---|---|
| 15 | 45.0 | 0.60 | 30.7 | 619 | 11.68 | 0.358 |
| 15 | 45.0 | 0.70 | 32.9 | 666 | 12.13 | 0.257 |
| 15 | 45.0 | 0.80 | 34.7 | 704 | 12.50 | 0.188 |
| 20 | 50.5 | 0.60 | 32.9 | 666 | 12.14 | 0.414 |
| 20 | 50.5 | 0.70 | 35.4 | 719 | 12.64 | 0.301 |
| 20 | 50.5 | 0.80 | 37.5 | 764 | 13.05 | 0.223 |
| 25 | 56.5 | 0.60 | 35.1 | 712 | 12.57 | 0.480 |
| 25 | 56.5 | 0.70 | 37.9 | 771 | 13.12 | 0.355 |
| 25 | 56.5 | 0.80 | 40.3 | 822 | 13.58 | 0.265 |
| 30 | 63.1 | 0.60 | 37.0 | 753 | 12.95 | 0.562 |
| 30 | 63.1 | 0.70 | 40.1 | 818 | 13.55 | 0.421 |
| 30 | 63.1 | 0.80 | 42.9 | 876 | 14.05 | 0.319 |

**Why it is superseded (RC-08, accepted).** The v2.3 basis of 42.85 bar used the simulation line-loss law (2.5 bar x (mdot/0.25)^2, about 0.75 MPa at the failure flow) and eta_c* 0.92. Both are non-conservative for an over-pressure basis. The reviewer's 42.4 bar confirms the v2.3 value to -1.0 %.

**v2.4 basis** (SIM, `meop_basis_v2p4.json`, `meop_cv36_check_v2p4.json`; script `meop_basis_v2p4.py`). Same failure: pintle stuck at full stroke, S230 initial port, saturated tank. Worst corner of the uncertainty bands:
- Cd 0.80 and eta_c* 0.96 (top of both bands);
- regression band corner a x1.5, n 0.68;
- line loss from the designed hardware (MV-P Cv 3.6 plus the filter, Table 2.6), and zero line loss as a bound.

Table 3.8. Stuck-pintle Pc at the worst corner against tank temperature (SIM).

| T_tank [C] | P_sat [bar abs] | Hardware Cv 3.6 [bar] | Hardware Cv 3 [bar] | Zero line loss [bar] |
|---|---|---|---|---|
| 22 | 52.86 | – | 42.85 | 44.08 |
| 23 | 54.06 | 43.61 | 43.56 | 44.85 |
| **24 (interlock)** | **55.28** | **44.33** | 44.28 | **45.55** |
| 25 | 56.52 | 45.06 | 45.01 | 46.27 |
| 30 (not a credible ignition state) | 63.08 | 48.46 | 48.40 | 49.87 |

**MEOP restated (LEAD 2026-10-13).**
- MEOP stays 45 bar, with an ignition interlock: T_tank <= 24 C at ARM and again at ignition. ENG-12's ignition range becomes 15-24 C, and 30 C is no longer a credible ignition state.
- In pressure terms the interlock is P_tank <= 55.28 bar abs, i.e. 54.27 bar g on the 170BG tank transducer (DERIVED, CoolProp). Electronics implements it on T_tank and P_tank together.
- **Basis:** 44.33 bar at the interlock with the designed line loss. **Margin 0.67 bar (1.5 %)** to MEOP.
- That margin depends on the hardware line loss. With zero line loss the same corner gives 45.55 bar, 0.55 bar (1.2 %) above MEOP. CF-3 verifies the line loss at the failure flow (about 0.38 kg/s).
- With the n 0.5 law the zero-loss maximum at <= 25 C is 43.96 bar.
- **Proof 67.5 bar is unaffected.** The margin is >= 21.9 bar at the interlock and >= 17.6 bar even at 30 C with zero line loss.
- Unchanged: software Pc cap 25 bar; ECU over-pressure abort at 31.47 bar g (OVP comparator, A4 in §7.4); Pc transducer range >= 70 bar.
- **Guard band (v2.4a; LEAD line 172 (4); R2-07).** The 0.67 bar margin on Pc equals about 0.92 K or 1.14 bar of P_tank (Table 3.8 slopes: +0.73 bar of Pc and +1.24 bar of P_sat per K, DERIVED). The interlock thresholds therefore sit below 24 C and 55.28 bar abs by the total channel uncertainty of T_tank and P_tank, which Electronics states (MISSING until then; interface `interlock_guard_band`).
- **CF-1 / CF-3 acceptance (LEAD line 172 (4)).** Full-stroke Cd <= 0.80 (the top of the ASSUMED band; Cd 0.85 alone adds about 1.4 bar, REV-COMB-2) and a line loss at the failure flow (about 0.38 kg/s) >= the modelled value. Otherwise MEOP is restated.

### 3.7 Throat block, runaway and tail-off with the 44 cm3 segment (v2.4; RC-01)

These runs used the v3.4 segment (44 cm3). They were not repeated on v3.4.1 (48.23-50.04 cm3, +10-14 %). The throat-block peaks and the runaway bound do not depend on the segment volume (the no-valve row bounds any volume). The tail-off rows depend on it only through the slower pressure decay of a larger flashing segment after an MV-first cut. The change is expected to be small but is not shown; the re-run is open (§11).

Basis:
- `throat_block_v2p4.json` and `throat_block_seg44_v2p4.json` (script `throat_block_v2p4.py`): grain_q1d v2 engine plus a series valve and a flashing segment (homogeneous equilibrium, CoolProp HEOS), RC-01 shutdown kinematics.
- `abort_cases_v2p4.json` (pintle runaway) and `segment_drain_v2p4.json` (shutdown order).
- Pintle kinematics: command 6.5 ms after the decision, 16.7 mm/s behind a 10 ms lag (CHANGELOG 2026-10-12).

**Throat block (S6; lead question on A4).** 70 % or 90 % of the throat blocked at 500 N, Cd 0.8. Values are SIM.

| Tank | Block | Pc peak [bar abs] | Peak after the block | Time above MEOP 45 bar [ms] | Time above 30 bar [ms] |
|---|---|---|---|---|---|
| 30 C | 70 % | 53.8 | 18 ms | 47.8-48.6 | 81-82 |
| 30 C | 90 % | 61.6 | 12 ms | 96.6-98.0 | 119-120 |
| 25 C | 70 % | 50.3 | 16 ms | 42.8-43.2 | 83-85 |
| 25 C | 90 % | 55.3-55.4 | 9-37 ms | 96.2-98.0 | 121-122 |

Ranges cover MV closing in 30 ms and 0.10 s.

Reading:
- Every peak is below proof (67.5 bar). The peak comes 9-37 ms after the block, so faster detection cannot lower it.
- The MV close time changes the time above MEOP by <= 2 ms. Only the pintle closing rate shortens it.
- Electronics' SIL plant gives 55.7 bar abs (transducer 58.1 bar) and 72 ms above MEOP for the 70 % / 30 C case. The two plants agree in kind.
- **Combustion's answer to the lead (A4 / RC-01):** S6 is acceptable as a FAULT load case, because the peak stays below proof. The chamber, closure and seat are checked for it in the assembled FEA:
  - **LC-TB70:** 58.1 bar abs peak, > 45 bar for 72 ms, > 30 bar for 112 ms, case at 448.15 K (the case-abort threshold).
  - **LC-TB-S:** 63.1 bar abs held for 0.30 s. This is a static bound: the chamber at the 30 C tank pressure for the simulated window. It covers the 90 % block with the abort (61.6 bar peak).
  - LEAD 2026-10-13: adopted, relayed to Mechanical.
- Without any abort, a near-full block (99 %) overshoots to 67.1 bar at 30 C, i.e. proof, and to 61.4 bar at 25 C (SIM, `throat_block_v2p4.json` no-abort rows). At the 24 C interlock the tank is <= 55.3 bar. The abort (A4) is still required.
- No faster cut is required for the chamber, provided LC-TB70 and LC-TB-S pass. If they do not, the pintle closing rate is the only effective lever.

**Pintle runaway to full stroke from 100 %** (row A4). Runs at 20 C / Cd 0.7 and 30 C / Cd 0.8:

| Case | Pc peak [bar] | Time above 30 bar [s] |
|---|---|---|
| Valve cut, no segment | 33.7-37.3 | 0.096-0.097 |
| Valve cut, 21.4 cm3 segment | 35.8-41.2 | 0.125 |
| No valve action | 34.7-41.7 | 0.39-0.41 |

- All are below MEOP.
- The no-valve case bounds both the peak and the duration for any segment volume. With the valve closed and a larger segment, the segment only feeds the pintle until it is empty, so the 44 cm3 case lies between the 21.4 cm3 row and the no-valve row (DERIVED argument; not re-run).

**Tail-off from 500 N and shutdown order** (`throat_block_seg44_v2p4.json`, `segment_drain_v2p4.json`; Cd 0.70 ASSUMED):

| Case | Impulse after the decision [N s] | t10 [s] | N2O after the decision [g] |
|---|---|---|---|
| 20 C, MV-first 30 ms / 0.10 s, 44 cm3 | 37.5 / 38.2 | 0.120-0.121 | 19.3-19.6 |
| 30 C, MV-first, 44 cm3 | 33.1-33.5 | – | – |
| 13.9 C (cold A1 state), MV-first 30 ms, 44 cm3 | 42.5 | – | – |
| Pintle-first (normal shutdown), all temperatures, 44 cm3 | 33.5-43.6 | – | 17.0-22.7 |
| Pintle only, no valve, earlier 21.4 cm3 basis (`abort_cases_v2p4.json`) | 38.3 | 0.121 | 19.7 |

- GNC should use 33-44 N s and t10 0.12 s for every abort and every planned cut-off. The upper end is the cold-tank case: at 13.9 C the tail-off impulse exceeds the 20 C value (42.5 against 37.5 N s).
- With the liquid segment present, the MV cut does not shorten the tail-off. In an abort the MV's role is the fail-safe for a pintle that does not close (A6), not a faster tail-off.
- **Shutdown order** (LEAD 2026-10-13): a normal shutdown is pintle-first, with the MV de-energised on seat confirmation or after a 0.30 s time-out. The segment is liquid-full at MECO, and the coast then fills its traps, and in HI wet the whole segment, with vapour (§2.8). An abort is MV-first and leaves about half the segment as vapour (22.2-24.3 cm3 on 44 cm3). After any abort the next attempt is treated as a vapour-segment start, which PURGE clears (§2.8).

## 4. Grain and internal ballistics

### 4.1 Regression law (v2.4; RC-07)

No verified N2O/ABS (or N2O/PETG) regression law was found in the literature accessed. Design law: r = a G_ox^n, with:
- a ASSUMED, anchored at about 1 mm/s at 300 kg/m2s for HTPB/N2O (Boughaba & Hendrick, EUCASS 2013, citing literature);
- n = 0.5 ASSUMED, band 0.35-0.68, covering GOX polymer laws with n 0.50-0.68 (Zilliac & Karabeyoglu, AIAA 2006-4504) and the low end the review ran.

**v2.4: the whole band is run.** Every law is re-anchored at r(300 kg/m2s) = band x 1 mm/s, so a and n vary about the anchor, as in the review. The band is a x0.6 / 1.0 / 1.5 against n 0.35 / 0.5 / 0.68 on every flight cycle, and a x1.1-1.65 on the B1 62 m records for the gating rule. Results: §4.4 (A1, B2) and §4.6 (B1 85 m and 62 m).
- Baseline form: oxidiser-flux law with the local G_ox(x) of the quasi-1D model. The total-flux form (G = G_ox + G_fuel, regressing faster aft) runs as a sensitivity on B1 (§4.6). Which form holds is a T1-T4 measurement: the port bore at several stations.
- The solid thermal lag (first order, kappa/r^2) and the 30 % preheat at each start are as in v2.3.

Static fires T1-T2 measure (a, n) by mass loss and port bore at several fluxes. PETG has no law at all and needs its own tests.

### 4.2 Port geometry and length

The v1 helical port was rejected for two reasons:
- On the v1 B1 cycle it burned through (web -3.12 mm at 15.0 s).
- It is a roll-torque source.

The LEAD decision of 2026-10-12 is a centred straight round port, S230. The length was minimised under three constraints:
- residual web >= 1 mm at the x1.5 regression bound;
- thrust ceiling;
- gimbal sweep.

Initial G_ox at the head end is 491 kg/m2s at 100 %. No flooding or blow-off limit for N2O/ABS was found; T1 at 100 % checks it.

Table 4.1. Grain trade over the gnc.json v1 cycles (SIM, `grain_trade_v2.csv`).

| Variant | DC | Regression x | Impulse [N s] | O/F mean | Isp mean [s] | Web end [mm] | Min ceiling [N] | Fuel [kg] |
|---|---|---|---|---|---|---|---|---|
| S200 | A1 | 1.0 | 1855 | 10.39 | 185.4 | 9.47 | 549 | 0.090 |
| S230 (v2) | A1 | 1.0 | 1852 | 8.90 | 188.2 | 9.53 | 558 | 0.101 |
| S260 | A1 | 1.0 | 1851 | 7.77 | 190.3 | 9.58 | 565 | 0.113 |
| S200 | B1 | 1.5 | 2744 | 4.22 | 166.8 | 0.92 | 590 | 0.321 |
| S230 (v2) | B1 | 1.5 | 2745 | 3.65 | 163.2 | 0.94 | 593 | 0.369 |
| S260 | B1 | 1.5 | 2750 | 3.22 | 160.2 | 0.97 | 595 | 0.415 |
| v1 helix L200 | B1 | 1.0 | 2746 | 4.52 | 167.3 | -3.12 (burn-through at 15.0 s) | 579 | 0.303 |

### 4.3 Chambers, efficiency and model

Chambers:
- Pre-chamber 30 mm long: vaporisation and distribution at the head end.
- Post-chamber 40 mm long: mixing. The diameter of both is 53.9 mm.
- Initial free volume is 2.846e-4 m3 and L* is 1.92 m.
- At 100 % the mean port mixture stays oxidiser-rich along the whole port (exit O/F 10.4 against stoichiometric 8.17). Mixing finishes in the post-chamber and nozzle. At <= 50 % the mean O/F crosses stoichiometric inside the port (`chamber_port_state_v2.json` and figure).

eta_c* is 0.92, ASSUMED with a band of 0.85-0.96; no source specific to N2O/ABS was found. eta_cf is 0.975, ASSUMED.

The quasi-1D model (`src/grain_q1d.py`) couples:
- the tank, equilibrium or two-CV non-equilibrium;
- the feed loss and the Dyer pintle table;
- a chamber filling ODE with CEA c*(Pc, O/F) x eta_c*;
- N axial port cells holding D(x), G_ox(x), G(x), cumulative fuel and local O/F;
- the CEA Cf with Schmucker separation;
- the throat history from the erosion model.

Fuel response lags the quasi-steady law by the solid thermal time kappa/r^2, a first-order form (ASSUMED; physics after Karabeyoglu et al. 2005). Control is feed-forward inversion of the map every 10 ms, limited by the dP/Pc >= 0.25 ceiling and the 4 mm stroke.

Table 4.2. Operating points: S230, 20 C tank (50.5 bar), initial port 25 mm (SIM). Lift and dP/Pc come from the map row at 50 bar. T0 delivered = eta_c*^2 Tc.

| Throttle % | F [N] | Pc [bar] | O/F | mdot_ox [g/s] | mdot_f [g/s] | Isp_SL [s] | Lift [mm] | dP/Pc | Tc CEA [K] | T0 del. [K] |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 500.0 | 25.01 | 10.43 | 241.0 | 23.1 | 193.1 | 1.916 | 0.91 | 3257 | 2757 |
| 75 | 375.0 | 19.10 | 8.99 | 179.0 | 19.9 | 192.2 | 1.252 | 1.55 | n/a | n/a |
| 50 | 250.0 | 13.20 | 7.34 | 119.1 | 16.2 | 188.4 | 0.755 | 2.74 | 3303 | 2795 |
| 40 | 200.0 | 10.85 | 6.58 | 95.9 | 14.6 | 184.6 | 0.588 | 3.58 | n/a | n/a |
| 25 | 125.0 | 7.33 | 5.32 | 62.6 | 11.8 | 171.4 | 0.367 | 5.80 | n/a | n/a |
| 20 | 100.0 | 6.16 | 4.85 | 52.0 | 10.7 | 162.5 | 0.301 | 7.10 | 3158 | 2673 |
| 15 | 75.0 | 4.98 | 4.34 | 41.7 | 9.6 | 149.0 | 0.238 | 9.02 | n/a | n/a |
| 12.5 | 62.5 | 4.37 | 4.06 | 36.5 | 9.0 | 140.2 | 0.207 | 10.43 | 2953 | 2500 |

Max-thrust point: c* delivered 1401 m/s, gamma 1.147, MW 28.72, chamber fill time constant 3.4 ms (DERIVED; the step fit gives 4 ms).

**v2.4: free volume and nozzle efficiency** (RC-16, RC-09).
- **Free volume.** v2.3 quoted 284.6 cm3 (L* 1.92 m) without the convergent. With the 28.26 cm3 convergent of the published contour the initial free volume is 300.9 cm3 and L* is 2.03 m, as the reviewer found. v2.4 uses 300.9 cm3 in the hard-start and chamber-gas calculations (§7.6, §9). The chamber fill time constant scales to about 3.6 ms (DERIVED). No conclusion changes.
- **eta_cf band.** 0.975 stays the nominal and 0.95 is the low end, from the CFD: own solver with slip walls 0.9755, OpenFOAM slip 0.962, OpenFOAM no-slip SST 0.9525 (review RC-09). `rc09_etacf_band_v2p4.json` (DERIVED, Cf_vac backed out of the design point):

| eta_cf | 0.975 | 0.970 | 0.965 | 0.960 | 0.955 | 0.950 |
|---|---|---|---|---|---|---|
| Pc for 500 N at sea level [bar] | 25.01 | 25.13 | 25.25 | 25.38 | 25.50 | 25.63 |
| Thrust at the 25 bar cap [N] | 499.8 | 497.2 | 494.7 | 492.1 | 489.5 | 487.0 |

- The reviewer's 25.27 / 25.40 / 25.67 bar at 0.965 / 0.960 / 0.950 agree within 0.04 bar.
- ENG-01 has no margin at the cap even at the nominal. If T1 measures eta_cf at the low end, the lead chooses between a cap of about 25.7 bar (still far below the 45 bar MEOP and the 31.47 bar g abort) and 487 N at 25 bar (open item, §12). The maps keep 0.975; combustion.json v2.4 publishes the band.

### 4.4 Duty-cycle results

Table 4.3. S230 over the gnc.json v2 cycles (published 20:34Z). The inputs were the 19:15Z working copy, whose F_N and F_cmd_N histories are identical to the published files (`inputs/gnc_v2_published_20261012T2034/MANIFEST.txt`). SIM, `data/v2/dc_gncv2wip/summary_v2.json`.

| DC | Regression x | Tank | Burn [s] | Impulse [N s] (GNC) | N2O [kg] | Fuel [kg] | O/F mean | Web end [mm] | Liquid left [kg] | Min ceiling [N] | Tracking rms [N] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 1.0 | 3.17 L / 2.00 kg | 7.40 | 2528 (2504) | 1.222 | 0.137 | 8.95 | 8.17 | 0.477 | 578 | 22.85 |
| A1 | 1.5 | 3.17 L / 2.00 kg | 7.40 | 2528 (2504) | 1.126 | 0.198 | 5.69 | 6.01 | 0.579 | 598 | 21.89 |
| A1 | 0.6 | 3.17 L / 2.00 kg | 7.40 | 2539 (2504) | 1.334 | 0.084 | 15.80 | 10.22 | 0.359 | 556 | 21.89 |
| A2 | 1.0 | 4.02 L / 2.54 kg | 8.89 | 3080 (3057) | 1.493 | 0.164 | 9.11 | 7.18 | 0.667 | 579 | 21.96 |
| B1 | 1.0 | 3.87 L / 2.44 kg | 19.04 | 2871 (2842) | 1.437 | 0.242 | 5.93 | 4.57 | 0.641 | 581 | 17.54 |
| B1 | 1.5 | 3.87 L / 2.44 kg | 19.05 | 2868 (2842) | 1.379 | 0.355 | 3.89 | 1.31 | 0.702 | 594 | 16.73 |
| B2 | 1.0 | 2.87 L / 1.81 kg | 14.49 | 2078 (2050) | 1.043 | 0.182 | 5.74 | 6.55 | 0.499 | 584 | 20.62 |

No cycle is ever ceiling-limited (0.00 s). The A2 and B1 tanks are larger than the lead baseline (OI-1).

Table 4.4. S230 over the gnc.json v1 cycles (SIM; non-equilibrium tank with E 1000 in flight; ASSUMED 15 L ground tank for C and D).

| DC | Regression x | Burn [s] | Impulse [N s] | N2O [kg] | Fuel [kg] | O/F mean | Isp mean [s] | Web end [mm] | Liquid left [kg] | Min ceiling [N] | Min dP/Pc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 0.6 | 5.83 | 1863 | 0.985 | 0.062 | 15.87 | 181.4 | 11.19 | 0.110 | 533 | 0.51 |
| A1 | 1.0 | 5.83 | 1852 | 0.902 | 0.101 | 8.90 | 188.2 | 9.53 | 0.195 | 558 | 0.55 |
| A1 | 1.5 | 5.83 | 1860 | 0.833 | 0.148 | 5.63 | 193.3 | 7.75 | 0.268 | 579 | 0.60 |
| A2 | 1.0 | 7.73 | 2520 | 1.222 | 0.138 | 8.87 | 189.0 | 8.12 | 0.258 | 548 | 0.61 |
| B1 | 1.0 | 20.73 | 2748 | 1.391 | 0.251 | 5.54 | 170.6 | 4.30 | 0.607 | 581 | 0.79 |
| B1 | 1.5 | 20.74 | 2745 | 1.347 | 0.368 | 3.65 | 163.2 | 0.94 | 0.655 | 593 | 0.82 |
| B2 | 1.0 | 14.72 | 1994 | 1.007 | 0.181 | 5.58 | 171.2 | 6.60 | 1.026 | 623 | 0.81 |
| B2 | 1.5 | 14.72 | 1992 | 0.973 | 0.264 | 3.68 | 164.1 | 3.91 | 1.063 | 635 | 0.83 |
| C | 1.0 | 36.32 | 4230 | 2.161 | 0.404 | 5.35 | 168.2 | 0 (burn-through 46.4 s) | 6.943 | 638 | 5.08 |
| D | 1.0 | 49.81 | 13160 | 7.018 | 0.404 | 17.37 | 180.9 | 0 (burn-through 24.1 s) | 1.665 | 528 | 0.50 |

- A round port leaves no sliver; the residual fuel is the remaining web.
- Residual web rule: >= 1 mm at the x1.5 bound on every flight cycle. The ABS thermal layer kappa/r is 0.1-0.3 mm. B1 is the limiting cycle: 1.31 mm on gnc v2 and 0.94 mm on gnc v1 (OI-10).
- With one grain, ground cycles C and D burn through. The test plan splits C into two grain loads and D into three.
- The A1 cycle at x0.6 has a cumulative mean O/F of 15.9, beyond the clamp at O/F 14 used in the c* lookup. Its O/F and Isp are approximate.

**v2.4: gnc.json v3 cycles.** Table 4.5. S230 on the gnc.json v3 sizing records at a x1.0, n 0.5 (SIM, `data/v2/dc_gncv3/summary_v2p4.json`; non-equilibrium tank E 1000, 2.00 kg / 3.17 L as in GNC's record index; "growth" = GNC's throat-growth reproduction, sim6 v2.7 Pc hold, At +7.2 % by the end of B1).

| Record | Burn [s] | N2O [kg] | Fuel [kg] | O/F mean | Web end [mm] | Liquid left [kg] | Min ceiling [N] | Min dP/Pc |
|---|---|---|---|---|---|---|---|---|
| A1 dispersed p99 | 8.26 | 1.430 | 0.158 | 9.05 | 7.39 | 0.250 | 557 | 0.60 |
| A1 p99, growth | 8.14 | 1.432 | 0.156 | 9.19 | 7.47 | 0.214 | 626 | 0.70 |
| B1 85 m p99 | 21.78 | 1.497 | 0.269 | 5.57 | 3.76 | 0.226 | 491 | 0.61 |
| B1 85 m p99, growth | 21.66 | 1.663 | 0.282 | 5.89 | 3.37 | 0.047 | 507 | 0.44 |
| B1 85 m max | 23.63 | 1.520 | 0.284 | 5.36 | 3.33 | 0.170 | 527 | 0.71 |
| B1 85 m max, growth | 23.46 | 1.524 | 0.283 | 5.39 | 3.34 | 0.167 | 565 | 0.77 |

- No record is ceiling-limited (0.00 s). The minimum dP/Pc stays >= 0.44, above the 0.25 rule.
- B1 85 m p99 with growth ends with 0.047 kg of liquid. The 85 m records are thermal and erosion sizing cases, not flight cases (62 m cap, LEAD), but GNC should know the margin (§12).
- Residual web: the ENG-06 rule is now >= 1 mm over the whole envelope a x0.6-1.5, n 0.35-0.68. A1 and B2 meet it everywhere (Table 4.6); B1 at 85 m does not (§4.6).
- The A1 cases at a x0.6 have cumulative O/F 15.8-16.3, beyond the O/F 14 clamp of the c* table; their O/F and Isp are approximate, as in v2.3.

### 4.5 All-max-thrust case

Table 2.2 above is the continuous 500 N case. The Pc(t) and F(t) history for the thermal load case is `data/v2/engine_S230_BL/maxthrust_BLtank_neqE1e+03_T20C.csv`.

### 4.6 Regression band, the B1 burn limit and oxidiser-rich operation (v2.4; RC-07, REV-GNC-1 RG-03)

Basis (SIM, grain_q1d v2.4 driven by the GNC records):
- `dc_gncv3_band/summary_v2p4.json`: gnc.json v3 records, a x0.6 / 1.0 / 1.5 against n 0.35 / 0.5 / 0.68;
- `dc_gncv31_62m/lane*/summary_v2p4.json`: GNC staging v3.1 B1 62 m records (p99 and max, with and without growth), a x0.6-1.65;
- `b1_web_fix_v2p4.json` (smaller ports), `b1_axial_law_v2p4.json` (total-flux law), `b1_62m_gating_v2p4.json`, `burn_limit_proxy_v2p4.json`, `oxrich_62m_v2p4.json`.

Table 4.6. Minimum residual web at the end of the cycle [mm] against the regression band; "BT t" = local burn-through at t seconds (SIM).

| Cycle (record, burn) | a x0.6: n 0.35 / 0.5 / 0.68 | a x1.0: n 0.35 / 0.5 / 0.68 | a x1.5: n 0.35 / 0.5 / 0.68 |
|---|---|---|---|
| A1 dispersed p99 (8.26 s) | 9.64 / 9.66 / 9.67 | 7.12 / 7.39 / 7.62 | 4.35 / 5.02 / 5.61 |
| A1 p99, growth (8.14 s) | 9.71 / 9.73 / 9.73 | 7.20 / 7.46 / 7.69 | 4.46 / 5.10 / 5.68 |
| B1 85 m p99 (21.78 s) | 5.85 / 6.86 / 7.72 | 1.79 / 3.76 / 5.29 | BT 17.65 / 0.25 / 2.77 |
| B1 85 m p99, growth (21.66 s) | 5.63 / 6.62 / 7.48 | 1.48 / 3.36 / 4.85 | BT 17.02 / BT 21.23 / 2.24 |
| B1 85 m max (23.63 s) | 5.41 / 6.55 / 7.54 | 1.14 / 3.32 / 5.02 | BT 17.76 / BT 22.92 / 2.41 |
| B1 85 m max, growth (23.46 s) | not run | 1.18 / 3.34 / not run | BT 17.73 / BT 22.82 / not run |
| B2 (gnc v2, 14.49 s) | 8.29 / 8.89 / 9.41 | 5.30 / 6.55 / 7.55 | 1.89 / 3.86 / 5.55 |

- **The review is confirmed.** It found B1 v2 at n 0.35, a x1.5 burning through at 17.4 s; on the v3 85 m records the same corner burns through at 17.0-17.8 s. n 0.68 is benign everywhere (>= 2.2 mm).
- **Web rule.** ENG-06 (>= 1 mm over the envelope) holds on A1 and B2. On B1 85 m it fails at a x1.5 for n <= 0.5 and is close at a x1.0, n 0.35 (1.14-1.79 mm).
- **Liner margin.** The rule keeps >= 1 mm of ABS, 3-10 times the ABS thermal layer (kappa/r 0.1-0.3 mm). No credit is taken for the 1.6 mm phenolic liner, whose recession under direct flame is unknown (T1-T4 post-test inspection).
- **A smaller port does not restore B1 85 m** (`b1_web_fix_v2p4.json`, a x1.5, n 0.35): burn-through moves from 17.02 s (25 mm) to 18.31 s (22 mm) and 18.92 s (20 mm) on the p99 record with growth, and to 19.12 / 19.94 s on the max record, against 21.66 s and 23.63 s of burn. A smaller port also raises the head-end flux. It is not proposed.
- **Total-flux law** (`b1_axial_law_v2p4.json`, B1 85 m p99 with growth): a x1.0, n 0.5 leaves 2.71 mm (oxidiser-flux law 3.36 mm); a x1.0, n 0.35 leaves 0.73 mm (1.48 mm); a x1.5, n 0.35 burns through at 15.24 s (17.02 s), first at the aft end (x/L 0.99).

**B1 62 m** (LEAD: hop cap 62 m, provisional until the T1-T4 regression law). Table 4.7. Minimum residual web at the end of the 62 m records [mm] (SIM; "BT t" = burn-through at t s).

| Record (burn) | a x1.0 n 0.35 | x1.0 n 0.5 | x1.1 n 0.35 | x1.25 n 0.35 | x1.375 n 0.35 | x1.5 n 0.35 | x1.5 n 0.5 | x1.65 n 0.5 |
|---|---|---|---|---|---|---|---|---|
| p99 (18.63 s) | 3.29 | 4.96 | 2.42 | 1.16 | 0.16 | BT 17.45 | 1.79 | 0.90 |
| p99, growth (18.28 s) | 3.10 | not run | 2.22 | 0.94 | BT 18.15 | BT 16.77 | 1.44 | 0.53 |
| max (20.65 s) | 2.44 | 4.33 | 1.51 | 0.16 | BT 19.17 | BT 17.79 | 0.96 | 0.02 |
| max, growth (20.15 s) | 2.65 | not run | 1.74 | 0.41 | BT 19.11 | BT 17.64 | 1.17 | 0.24 |

At low a the 62 m records keep 5.7-8.5 mm (a x0.6, n 0.35-0.68: 6.31-8.46 mm; a x0.8, n 0.5: 5.74-6.30 mm).

**"85 m covers 62 m" is withdrawn for fuel, web and O/F** (REV-GNC-1 RG-03, accepted). GNC's 85 m sizing populations carry no regression band. At equal (a, n) the 62 m records burn through about as early as the 85 m records (a x1.5, n 0.35: 16.8-17.8 s against 17.0-17.8 s), so the 85 m cycles cannot stand in for the 62 m web. They still cover engine-on time, N2O burned and the throat-growth integral J.

**The lead's gating rule** (LEAD 2026-10-13): B1 flies only after the T1-T4 regression law; burn limit at t(w_min = 1 mm) computed with 1.1 x the measured a; grain change if a >= 1.25 x nominal with n <= 0.4. Check against the 62 m records (`b1_62m_gating_v2p4.json`; the limit is computed with a x1.1 the "true" law, then applied to the true-law history; MC fractions from GNC's 500-run tables, thrust-on p50 / p99 / max 15.86 / 18.41 / 20.65 s without growth and 15.84 / 18.21 / 20.15 s with the Pc hold):

| Measured law | Limit case | t_L [s] | N2O used at t_L [kg] | Web at t_L, true law [mm] | MC fraction burning past t_L |
|---|---|---|---|---|---|
| a x1.0, n 0.35 | x1.1 | never reached (web at the end 1.51-2.42 mm) | – | – | 0 |
| a just below x1.25, n 0.35 | x1.375 | 16.64-17.67 | 1.09-1.23 | 1.94-1.95 | 0.02-0.15 |
| a x1.5, n 0.5 | x1.65 | 17.48-18.81 | 1.19-1.29 | 1.89 | 0.004-0.034 |
| a x1.5, n 0.35 (corner) | grain-change branch: this grain does not fly | burns through at 16.77-17.79 s | – | – | (0.02-0.12 would burn past it) |

- Within the oxidiser-flux law the rule holds: wherever the limit binds, the true-law web at t_L is 1.9 mm, and the corner that burns through is excluded by the grain-change branch.
- **The 1.1 factor does not cover an error in the law's form.** If the true law were the total-flux form while a and the limit use the oxidiser-flux form, the web at the oxidiser-law t_L would be zero (p99 and max records with growth). Under the total-flux law, t_L itself falls at 15.30-15.87 s, and 48-81 % of the MC runs burn past it. The burn-limit law below therefore requires a to be taken at the station of largest local regression; that reading needs the T1-T4 bore at several stations.

**Burn-limit law for GNC** (REV-GNC-1 item 2; `burn_limit_proxy_v2p4.json`; DERIVED proxy of grain_q1d v2.4, ASSUMED until T1-T4):
- State: port diameter D, uniform along the grain; D(0) = 25.0 mm; web w = (53.5 mm - D)/2.
- Rate: dD/dt = 2 k_a x 1.0e-3 m/s x (G_ox / 300 kg/m2s)^n, with G_ox = 4 mdot_ox / (pi D^2); no regression while mdot_ox = 0 (coasts).
- k_a = 1.1 x a_meas / a_ref (lead rule), a_meas re-anchored at r(300 kg/m2s) and taken at the station of largest local regression; n = n_meas, evaluated at both ends of its T1-T4 confidence band, keeping the earlier t_L.
- Limit: t_L = first time with w <= 1.0 mm. The FSW action at t_L is GNC's and the lead's to define (REV-GNC-1).
- Optional second state for higher fidelity: r_eff with a first-order lag to the quasi-steady rate, tau = 1.2e-7 / max(r_eff, r_qs)^2 s clipped to 0.02-2 s, r_eff = 0.3 r_qs at the first flow and decaying in 0.05 s when the flow stops (this reproduces grain_q1d).
- Verification on 43 grain_q1d histories of the 62 m records (oxidiser-flux law):
  - with k_a = 1.0 the proxy reaches w = 1 mm 0.043-0.267 s later than the model's minimum web; a factor of 1.004-1.016 on a closes that gap, inside the rule's 1.1;
  - largest web difference 0.34 mm, the proxy's web being the larger; with the lag state 0.11 mm and 0.029-0.062 s;
  - to match the total-flux histories the oxidiser-flux proxy needs 1.10-1.15 on a: the measurement allowance would be consumed by a law-form error, hence the station rule above.

**Oxidiser-rich operation at low a** (REV-GNC-1 RG-03; `oxrich_62m_v2p4.json`). GNC's 62 m band population reaches a mean O/F of 11.6 (p50 8.0 in the a 0.6-0.9 tercile) against <= 6.6 in its 85 m sizing populations.

Table 4.8. Oxidiser-rich 62 m histories (SIM; O/F time-weighted over the burn; stoichiometric O/F 8.17).

| Record and law | Cumulative O/F | Instantaneous O/F, median | Time at O/F >= 8.17 [s] | N2O used [kg] | Liquid left [kg] | Web end [mm] |
|---|---|---|---|---|---|---|
| 62 m p99 / max, a x1.0 n 0.5 (reference) | 5.54 / 5.40 | 4.96 | 1.0-1.2 | 1.28 / 1.35 | 0.40 / 0.34 | 4.96 / 4.33 |
| a x0.8, n 0.5 | 6.84-7.02 | 6.30 | 1.0-1.2 | 1.33-1.41 | 0.29-0.34 | 5.74-6.30 |
| a x0.6, n 0.35 | 7.59-7.89 | 6.83-6.92 | 1.0-1.2 | 1.36-1.43 | 0.26-0.32 | 6.31-6.90 |
| a x0.6, n 0.5 | 9.28-9.51 | 8.62 | 16.4-18.4 | 1.41-1.49 | 0.20-0.26 | 7.28-7.74 |
| a x0.6, n 0.68 (with and without growth) | 11.26-11.94 | 10.96-11.34 | 17.7-19.9 | 1.46-1.62 | 0.087-0.20 | 8.10-8.46 |

- At a x0.6 with n >= 0.5 the engine runs above stoichiometric for 16-20 s of an 18-21 s burn.
- **Performance** (CEA, card ABS_TYP_v1, Pc 5-25 bar; the c* and Isp optimum lies at O/F 5-6): c* falls by 2.1-2.5 % at O/F 8, 6.0-6.1 % at O/F 11.6 and 8.0-8.2 % at O/F 14; sea-level Isp at eps 2 by 1.9-2.1 %, 5.8-5.9 % and 7.9-8.2 %. Tc falls only to 2990-3210 K at O/F 11.6-14 (3160-3380 K at the optimum).
- **Oxidising species in the chamber** (equilibrium mole fractions, Pc 5-25 bar): O2 3.6-4.1 % at O/F 8, 8.8-9.3 % at 11.6, 11.8-12.1 % at 14, against 0.1-1.2 % at O/F 5-6; O 1.3-2.0 % and OH 2.6-3.3 % above O/F 8. These drive the throat (§5.4) and wall (§6) oxidation.
- **Consequences:**
  - for GNC: at a given Pc the thrust per kilogram of N2O falls with the Isp deficit, about 6 % at O/F 11.6, so these runs use 0.05-0.23 kg more N2O than the a x1.0 runs on the same record, and the lowest liquid left is 0.087 kg (a x0.6, n 0.68, p99 with growth). The throat-growth integral J does not see O/F, but the erosion does (§5.4): GNC's growth law under-states At growth in the low-a tercile;
  - for the grain: no web concern (7.3-8.5 mm left);
  - stability: §8.

## 5. Nozzle and throat erosion

### 5.1 Expansion ratio

Table 5.1. Ideal sea-level Isp [s] against eps, with Schmucker separation (CEA/DERIVED, `nozzle_perf_v2.json`).

| Throttle % | Pc [bar] | O/F | eps 1.5 | eps 2.0 | eps 2.5 | eps 3.0 | eps 4.0 |
|---|---|---|---|---|---|---|---|
| 100 | 25.01 | 10.43 | 206.0 | 215.6 | 220.9 | 224.1 | 226.8 |
| 50 | 13.20 | 7.34 | 203.6 | 210.6 | 213.4 | 213.9 | 211.2 |
| 20 | 6.16 | 4.85 | 183.5 | 182.5 | 177.3 | 175.4 | 175.4 |
| 12.5 | 4.37 | 4.06 | 163.9 | 158.2 | 158.2 | 158.2 | 158.2 |

Table 5.2. Separation and side-load bound (DERIVED, `nozzle_perf_v2.csv`). The side-load bound assumes half the circumference attached and half separated.

| Throttle % | eps | pe/pa | Schmucker psep/pa | Summerfield separation | Schmucker separation | eps_sep | Side-load bound [N] |
|---|---|---|---|---|---|---|---|
| 100 | 2.0 | 3.199 | 0.519 | no | no | n/a | 0 |
| 25 | 2.0 | 0.891 | 0.517 | no | no | n/a | 0 |
| 20 | 2.0 | 0.723 | 0.514 | no | no | n/a | 0 |
| 15 | 2.0 | 0.564 | 0.509 | no | no | n/a | 0 |
| 12.5 | 2.0 | 0.485 | 0.506 | no | yes (at the lip) | 1.94 | 0.0 |
| 20 | 3.0 | 0.383 | 0.449 | yes | yes | 2.64 | 3.5 |
| 15 | 3.0 | 0.297 | 0.443 | yes | yes | 2.17 | 8.7 |
| 12.5 | 3.0 | 0.254 | 0.440 | yes | yes | 1.94 | 11.2 |
| 12.5 | 1.8 (eroded throat) | 0.580 | 0.529 | no | no | n/a | 0 |

Decision: eps 2.0 (DERIVED). The flow stays attached down to 15 %, with incipient lip separation at 12.5 % (Schmucker eps_sep 1.94; Summerfield attached). The cost against eps 3 is 8.5 s of ideal Isp at 100 % (215.6 against 224.1).

**v2.4 (RC-18).** The eroded-throat row of Table 5.2 (eps 1.8, pe/pa 0.580) held Pc constant. If the Pc loop does not compensate, the mass flow stays and Pc falls by about 10 %: pe/pa is then 0.522 against Schmucker's 0.529 (reviewer, DERIVED), i.e. incipient lip separation, as at eps 2.0. With GNC's Pc hold the 0.580 row applies. Accepted without re-run; the eps 2.0 decision is unaffected. T3 measures lip separation and side load at the floor.

### 5.2 Contour

Conical nozzle, `data/v2/nozzle_contour_v2.csv` as (x_face, x_throat, r) in metres. The v1 shape is shifted +30 mm for S230. In CAD, +Z forward gives z = x_exit_face - x_face.
- Convergent half-angle 45 deg (DERIVED, compact).
- Throat radius of curvature 10.293 mm upstream (1.5 Rt) and 2.621 mm downstream (0.382 Rt), per Rao 1958 and Huzel & Huang practice (LITERATURE).
- Divergent half-angle 15 deg. Divergence factor lambda = (1 + cos a)/2 = 0.983 (LITERATURE).
- Throat at x_face 0.32767 m, exit at 0.33862 m. Gas-path length from the injector face to the exit is 0.3386 m.

### 5.3 Graphite insert

Specification (DERIVED from the density and porosity sensitivity of the erosion model):
- isomolded or extruded fine-grain graphite;
- bulk density >= 1.80-1.85 g/cm3;
- ash <= 0.1 %.

The grade and its allowables come from the maker's datasheet: TO-QUOTE (Sønderborg DK-6400). The envelope is Mechanical's CAD v3.1: 44 mm OD with a 30 x 6.5 mm aft spigot through a 6 mm lip. The gas side is unchanged; the models used the v3.0 slice of 44 x 32 mm.

### 5.4 Erosion per flight and life (v2.4; RC-06, REV-GNC-1 RG-03)

Model (`src/nozzle.py`, `src/erosion_dc.py`, `src/erosion_v2p4.py`):
- 1-D radial transient conduction at the throat;
- Bartz h_g(T_w) and a radiation band;
- semi-global surface kinetics as tabulated by Rotondi et al., JPP 2024 (C + H2O, C + CO2, C + OH, C + O) and Nagle-Strickland-Constable for O2;
- film mass transfer (Chilton-Colburn).

Three estimates, all quoted (RC-06):
- Nominal: delivered composition.
- Conservative: CEA ideal composition with T0 = Tc.
- Literature-scaled: measured N2O/HDPE rates scaled with (Pc/35 bar)^0.68 and binned by O/F, after a 1.5 s onset per flight. A pessimistic reading repeats no onset at the relight ("no onset credit").

The literature rates are not re-verified in this revision (LITERATURE as used in v2). The life rule is DERIVED from ENG-06: replace the insert at dAt/At = 5 %, i.e. 0.169 mm of radial recession on Rt 6.862 mm.

Table 5.3. Throat recession per flight on the gnc.json v3 and v3.1 records (SIM, `data/v2/v2p4/erosion/erosion_v2p4.json`; histories from §4.4 and §4.6; regression band as labelled).

| Record and law | Burn [s] | Nominal [mm] | Nominal dAt/At [%] | Nominal Tw max [K] | Conservative [mm] | Conservative dAt/At [%] | Conservative Tw max [K] | Literature [mm] | Literature dAt/At [%] | Literature flights per insert |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 dispersed p99, a x1.0 n 0.5 | 8.24 | 0.063 | 1.86 | 1613 | 0.284 | 8.45 | 1882 | 0.301-0.452 | 9.0-13.6 | 0.38-0.56 |
| A1 p99, growth | 8.12 | 0.060 | 1.76 | 1594 | 0.268 | 7.95 | 1859 | 0.283-0.426 | 8.4-12.8 | 0.40-0.60 |
| A1 p99, a x0.6 n 0.5 | 8.24 | 0.056 | 1.64 | 1529 | 0.234 | 6.94 | 1775 | 0.397-0.564 | 11.9-17.1 | 0.30-0.43 |
| A1 p99, a x1.5 n 0.5 | 8.25 | 0.026 | 0.76 | 1686 | 0.195 | 5.77 | 1956 | 0.059-0.146 | 1.7-4.3 | 1.16-2.86 |
| A1 p99, a x1.0 n 0.68 | 8.24 | 0.070 | 2.05 | 1615 | 0.301 | 8.97 | 1885 | 0.376-0.539 | 11.2-16.3 | 0.32-0.45 |
| B1 85 m p99, a x1.0 n 0.5 | 21.77 | 0.028 | 0.82 | 1688 | 0.202 | 5.96 | 1968 | 0.149-0.350 | 4.4-10.5 | 0.48-1.13 |
| B1 85 m p99, growth | 21.65 | 0.034 | 1.00 | 1704 | 0.254 | 7.53 | 1988 | 0.153-0.364 | 4.5-10.9 | 0.47-1.11 |
| B1 85 m max | 23.62 | 0.024 | 0.69 | 1682 | 0.183 | 5.41 | 1958 | 0.141-0.347 | 4.2-10.4 | 0.49-1.20 |
| B1 85 m max, growth | 23.44 | 0.023 | 0.68 | 1638 | 0.178 | 5.26 | 1905 | 0.140-0.343 | 4.1-10.3 | 0.49-1.21 |
| B1 62 m p99, a x1.0 n 0.5 | 18.62 | 0.023 | 0.67 | 1614 | 0.167 | 4.93 | 1876 | 0.125-0.295 | 3.7-8.8 | 0.57-1.36 |
| B1 62 m max, a x1.0 n 0.5 | 20.64 | 0.022 | 0.63 | 1618 | 0.168 | 4.97 | 1879 | 0.126-0.309 | 3.7-9.2 | 0.55-1.34 |
| B1 62 m p99 / max, a x0.8 n 0.5 | 18.62 / 20.64 | 0.043-0.045 | 1.26-1.31 | 1589-1606 | 0.311-0.338 | 9.27-10.08 | 1857-1878 | 0.148-0.349 | 4.4-10.4 | 0.49-1.15 |
| B1 62 m, a x0.6 n 0.35 (p99, max, max growth) | 18.62-20.63 | 0.053-0.056 | 1.55-1.63 | 1573-1607 | 0.352-0.381 | 10.5-11.4 | 1843-1884 | 0.279-0.497 | 8.3-15.0 | 0.34-0.61 |
| B1 62 m, a x0.6 n 0.5 (p99, max) | 18.62-20.63 | 0.082-0.090 | 2.42-2.65 | 1573-1589 | 0.389-0.429 | 11.7-12.9 | 1847-1869 | 0.562-0.881 | 17.0-27.3 | 0.19-0.30 |
| B1 62 m, a x0.6 n 0.68 (p99, max, both with growth) | 18.27-20.63 | 0.083-0.091 | 2.44-2.67 | 1530-1576 | 0.362-0.396 | 10.9-11.9 | 1795-1847 | 0.572-0.892 | 17.4-27.7 | 0.19-0.30 |
| B2 (gnc v2), a x1.0 n 0.5 | 14.48 | 0.022 | 0.65 | 1545 | 0.141 | 4.14 | 1792 | 0.054-0.096 | 1.6-2.8 | 1.77-3.15 |

Flights per insert at the 5 % rule:
- **A1 (gnc v3 p99):** nominal 2.67-2.81, conservative 0.60-0.63, literature 0.38-0.60; with no onset credit 0.27-0.42. Across the whole a and n band the literature case spans 0.30-3.55 (a x0.6 to a x1.5, n 0.35, with growth).
- **B1 62 m at a x1.0:** nominal 7.4-7.8, conservative 1.0, literature 0.55-1.36.
- **B1 62 m, low-a oxidiser-rich corner (a x0.6, n >= 0.5):** nominal 1.9-2.1, conservative 0.40-0.47, literature 0.19-0.30.

**Life statement (replaces "1.0-4.3 A1 flights", v2.3).**
- Model spread on the gnc.json v3 A1 p99 cycle: 0.27-2.8 A1 flights per insert. The literature-anchored case gives 0.38-0.60 (review: 0.46-0.71 on the v2 cycles).
- A single A1 flight can exceed the 5 % rule: 8.4-13.6 % in the literature case, 8.0-8.5 % in the conservative model.
- v2.4a (LEAD line 183 (2)): the NZ-01 cracked-but-contained acceptance is refuted by "fragment loss or a throat-area change > 2 %". Erosion alone changes the throat area by 1.9 % (nominal), 8.0-8.5 % (conservative) or 8.4-13.6 % (literature) in one A1 flight, so that criterion cannot tell a crack from erosion. Combustion proposes that the post-firing inspection compare the measured bore with the erosion expected for the firing (pre/post bore, duty cycle), and count as refutation any area change > 2 % beyond that expectation, any non-axisymmetric step or any missing fragment (contradiction kept for the lead, OI-40).
- **Plan on one insert per flight** (ENG-06 as amended) until bore data from T1 and T4 exist. For the lead's ENG-06 text: replace "0.46-0.71" with "0.38-0.60 on the gnc.json v3 A1 p99 cycle (0.27-0.42 with no onset credit at the relight)".
- The insert is measured with a pin gauge or bore scan after every firing.

**Throat growth within a flight** (for the Pc loop and GNC):
- A1: up to 13.6 % (literature), 8.5 % (conservative), 1.9 % (nominal).
- B1 62 m at low a: up to 27.7 % (literature), 12.9 % (conservative).
- GNC's growth reproduction (sim6 v2.7, tg711) saturates at +7.2 % and depends on the thrust integral J only, not on O/F. It is therefore below the literature and conservative readings on A1, and well below them in the oxidiser-rich low-a tercile (REV-GNC-1 RG-03; open item, GNC). ENG-06 asks the loop to tolerate 7-11 %; the v3 figures suggest 14 % on A1 and up to 28 % in the B1 low-a corner, both ASSUMED until bore data.
- Effect: 5 % throat growth shifts the Pc-to-thrust map by about 5 % (F = Cf Pc At) and lowers eps toward 1.9. An 11 % growth (eps 1.8) costs 3.1 s of ideal Isp at 100 %. The Pc loop and the map should use the measured bore.

**Oxidiser-rich attack** (REV-GNC-1 RG-03, throat and walls):
- The low-a corner is 2.3-4.5 times more erosive per flight than a x1.0 on the same 62 m record, whichever model is used (Table 5.3). It runs 16-20 s above stoichiometric with 9-12 % O2 in the chamber (§4.6).
- The literature method's O/F >= 7 bin is anchored on near-stoichiometric N2O/HDPE data (review RC-06). At O/F 9-12 it may under-state the attack, and none of the three models bounds it from above with evidence.
- T1 at 100 % runs at O/F 10.4 at the initial port (Table 4.2), and the A1 cycle spends about 5.3 s above stoichiometric. The insert bore after T1 therefore measures an oxidiser-rich rate directly; T4 adds the duty-cycle value.
- Walls: at O/F 11.6-14, Tc is 2990-3210 K, below the 3160-3380 K at the c* optimum, so the convective load at equal Pc does not rise (CEA). The change is chemical: oxidation of phenolic char in the pre- and post-chamber liners, of the graphite insert faces, and of any exposed metal (injector face disc, retainer). None is modelled. Post-test inspection at T1-T4 (char depth and liner thickness at several stations) closes it.

**Proposed research item** (not adopted):
- Hypothesis: a denser fine-grain graphite (>= 1.85 g/cm3) or a pyrolytic-carbon / SiC-coated insert halves the literature-scaled recession at O/F >= 8.
- Comparator: the baseline isomolded grade.
- Evidence needed: bore after T1 and T4 on both grades, same cycle.
- Refutation criterion: the measured recession ratio is above 0.75. Prices TO-QUOTE (Sønderborg DK-6400).

## 6. Heat loads

### 6.1 Gas-side boundary conditions

The Bartz (1957) closed form uses CEA frozen transport properties, the recovery factor Pr^(1/3) and T_aw from the delivered T0 (`src/heat.py`, `src/thermal_bc_v2.py`).

Table 6.1. Boundary conditions for the FEA (DERIVED, `thermal_bc_summary_v2.json`).

| Point | Throttle % | Pc [bar] | O/F | T0 del. [K] | Peak q at Tw 600 K [MW/m2] | Peak h_g [W/m2K] | x of peak from throat [mm] | T_aw [K] | CSV |
|---|---|---|---|---|---|---|---|---|---|
| max | 100 | 25.01 | 10.43 | 2757 | 21.92 | 10259 | 0.0 | 2737 | thermal_bc_max_v2.csv |
| 75pct | 75 | 19.10 | 8.99 | 2783 | 18.09 | 8362 | 0.0 | 2763 | thermal_bc_75pct_v2.csv |
| 50pct | 50 | 13.20 | 7.34 | 2795 | 13.78 | 6338 | 0.0 | 2774 | thermal_bc_50pct_v2.csv |
| 20pct | 20 | 6.16 | 4.85 | 2668 | 7.43 | 3640 | -0.5 | 2642 | thermal_bc_20pct_v2.csv |
| floor12p5 | 12.5 | 4.37 | 4.06 | 2496 | 5.34 | 2865 | -0.5 | 2463 | thermal_bc_floor12p5_v2.csv |

CSV columns:
- x_face, x_throat, r, region, A/At, Mach, p, T_static, T_aw;
- h_g at Tw 600 K and 1500 K;
- h_g with equilibrium properties;
- q_conv, the q_rad band, and an uncertainty factor.

Uncertainty factors:
- nozzle 0.7-1.3;
- pre- and post-chamber 0.5-2. Bartz is outside its validity there (recirculating flow); h_g is 889 W/m2K and q is 1.9 MW/m2 at 100 %.

Equilibrium-property Bartz gives 3.0x h_g at the throat (30.9 kW/m2K). It is kept as an upper sensitivity, not as the baseline: with equilibrium properties the driving potential should be an enthalpy difference.

Radiation: gas plus soot emissivity 0.05-0.20 (ASSUMED), path 0.9 D. That gives 0.12-0.49 MW/m2 at the throat and 0.16-0.65 MW/m2 in the chamber.

Cold-wall start transient (coupled insert model): incident 27.1-31.6 MW/m2.

Grain zone: while the web is >= 1 mm, the burning fuel surface (about 700-900 K, ASSUMED) shields the case and liner. After burnout, which happens only in the ground cycles, use the post-chamber rows.

Duty-cycle timing:
- Pc(t), O/F(t), F(t) and the coasts are explicit in `data/v2/dc_g3/*.csv` (gnc v1) and `data/v2/dc_gncv2wip/*.csv` (gnc v2).
- The head end has `headend_bc_<DC>_v2.csv`.

**v2.4 (RC-17).** The 21.92 MW/m2 peak uses the mean throat radius of curvature, Rc = 0.941 Rt, the mean of 1.5 Rt upstream and 0.382 Rt downstream (`nozzle.py`); the reviewer reproduced it exactly. Over that Rc range the peak is 20.2-24.0 MW/m2; with no eta credit (T0 = Tc) it is 26.0-28.4 MW/m2. Both lie inside the stated x0.7-1.3 band (15.3-28.5 MW/m2). T0 = eta_c*^2 Tc may under-state local streak heating; at the throat the band covers it. Oxidiser-rich operation (§4.6) lowers Tc by 2-6 % and does not raise the convective peak; its effect on the walls is chemical (§5.4).

### 6.2 Throat insert soak-back and the retention lip (OI-5)

Table 6.2. Soak into a lumped 0.15 kg retainer (DERIVED lumped/1-D, insert 0.081 kg, v3.0 geometry; the v3.1 insert is larger, so FEA is required).

| DC | Contact h [W/m2K] | Retainer | Last shutdown [s] | Tw at shutdown [K] | Insert mean [K] | Retainer at shutdown [K] | Retainer peak [K] | Peak after shutdown [s] | Retainer at 900 s [K] |
|---|---|---|---|---|---|---|---|---|---|
| B1 | 2000 | Al | 20.7 | 1521 | 1229 | 709 | 920 | 33 | 625 |
| B1 | 2000 | steel | 20.7 | 1569 | 1292 | 890 | 1084 | 22 | 612 |
| B1 | 500 | Al | 20.7 | 1646 | 1385 | 477 | 847 | 102 | 616 |
| B1 | 150 | Al | 20.7 | 1707 | 1467 | 359 | 758 | 255 | 619 |
| A1 | 2000 | Al | 28.0 | 1176 | 877 | 538 | 663 | 32 | 509 |
| A1 | 2000 | steel | 28.0 | 1224 | 929 | 632 | 774 | 24 | 517 |
| A1 | 500 | Al | 28.0 | 1254 | 962 | 444 | 634 | 97 | 505 |
| A1 | 150 | Al | 28.0 | 1326 | 1042 | 354 | 588 | 251 | 505 |

Reading, per the lead note of 2026-10-12:
- 240 C (513 K) is Mechanical's v3.1 allowable for the aluminium lip at 51 MPa.
- A 0.15 kg aluminium retainer peaks at 588-920 K, above that allowable. About 0.6 kg of aluminium (about 540 J/K) in good contact gives 435-532 K.
- The steel rows (774-1084 K) are to be compared with a steel temperature-dependent allowable. That allowable is not defined here. They are not a failure.

Governing cases (LEAD), with numbers from `soakback_relight_v2.csv` (DERIVED). TS-1 is the relight after the MECO coast with pressure, at Pc 25 bar (normal) and 45 bar (MEOP):
- A cycles, coasts of 11.3-22.2 s treated as adiabatic.
- Retainer at relight: 302-558 K with aluminium brackets; 324-540 K with a 0.30 kg steel retainer.
- At the landing-burn Pc maximum (17.7-22.5 bar): 303-562 K (Al).
- The in-burn maximum, 305-597 K (Al), occurs at the end of the landing burn at Pc 1.0-2.9 bar.
- The aft land behind 5 mm of phenolic is at 303-335 K at relight.

TS-2 is the post-landing soak judged for reuse (3600 s, A and B cycles):
- Retainer peak 408-920 K, 0-3195 s above 150 C.
- Aft land peak 493-699 K, 874-2106 s above 150 C.

Action (Mechanical): choose retainer material, mass and interlayer. Mechanical's thermal FEA of the v3.1/v3.2 insert supersedes these lumped bounds.

### 6.3 Post-chamber wall (OI-4)

Table 6.3. Phenolic liner plus 3.175 mm 6061 case (DERIVED 1-D; no char or ablation credit and no axial conduction, so conservative).

| DC | Liner | h_g | Case peak [C] | Time of peak [s] | Case at last shutdown [K] | Liner surface max [K] |
|---|---|---|---|---|---|---|
| A1 | 1.6 mm | x1 / x2 | 364 / 452 | 51 | 507 / 556 | 1956 / 2238 |
| A1 | 3.0 mm | x1 / x2 | 287 / 353 | 90 | 416 / 441 | 1956 / 2238 |
| A1 | 5.0 mm | x1 / x2 | 220 / 269 | 166 | 332 / 341 | 1956 / 2238 |
| B1 | 1.6 mm | x1 / x2 | 641 / 780 | 41 | 757 / 874 | 2044 / 2331 |
| B1 | 3.0 mm | x1 / x2 | 474 / 563 | 82 | 464 / 508 | 2147 / 2406 |
| B1 | 5.0 mm | x1 / x2 | 360 / 426 | 160-161 | 321 / 330 | 2160 / 2416 |

Every case exceeds the 192 C aft-land allowable. The insulator thickness and material come from Mechanical's thermal FEA with the BC CSVs (band x0.5-2).

### 6.4 Head end and servo (OI-15)

Lumped head bound: T_aw = T0, no char credit, gnc v1/v2 A1/A2/B1, h_g x0.5-2. CAD v3.2 has a 2 mm face disc and a 0.44 kg head.

| Case | Head temperature |
|---|---|
| At relight | 37-66 C (x1: 46-55 C) |
| Maximum in flight | 41-110 C (x1: 53-82 C) |
| Post-landing soak peak | 66-190 C, at 61-65 s after the last shutdown |
| Ground DC-C | 106-200 C in operation; soak peak 151-272 C |

Heat into the head in flight (CAD disc, x1):
- 7.8-18.3 kJ through the face;
- 7.4-12.2 kJ through the pre-chamber case joint;
- N2O removes 2.5-5.7 kJ.

The forward case node behind 1.6 mm of phenolic reaches 106-454 C in flight; this joins OI-4.

Consequence: the HV69 mount (-10 to 60 C rating; 50 C mount limit in flight) must not rely on a cool head. Measures:
- keep the 2 mm face disc;
- a low-conductance bracket foot (G10 or PEEK washers, stainless or titanium screws);
- consider a thicker pre-chamber insulator;
- at T1, thermocouples on the face-disc back, head top, bracket foot and servo case.

**v2.4 notes.**
- The relight-side heat now comes from Mechanical's FEA and estimates: 0.83-9.0 kJ into the valve-to-seat segment over the 18.67 s A1 coast in six heat cases on CAD v3.4.1 (831-9011 J, `segment_heat_v341_v2p4.json`; §2.7-2.8). The 0.88-9.87 kJ printed here in v2.4 were Mechanical's totals on the superseded v3.4 route (875-9872 J) (R2-09). That heat, not the head temperature, governs the relight (§2.8).
- The seat insert TC-03 is Inconel 718 (LEAD 2026-10-13): Mechanical's upper-bound in-burn seat-face temperature on A1 is 695-712 C (§3.5).
- Case thermocouple rules (LEAD): in-burn abort at 448.15 K for 0.2 s while the MV is open; RELIGHT refused above 433.15 K (§7.4).
- OI-15 (HV69 mount at <= 50 C in flight) stands; T1 thermocouples on the face-disc back, head top, bracket foot and servo case.

### 6.5 Nozzle joint: hot layer, seal and hazard H19 (v2.4)

**v2.4a status (LEAD line 182 (4)).** The flexible-graphite seal of J1 (Mechanical NZ-04) sees a 577 C soak against a 450 C oxidising-service limit (as recalled) and is treated as FAIL until a maker datasheet for the chosen grade shows an oxidising-gas limit >= 627 C; otherwise Mechanical selects a datasheet-rated seal material and re-checks the joint (OI-39). The hot-layer and leak numbers below are unchanged.

Basis: `nozzle_joint_v2p4.json` (`b5f396c7155c06c4`, script `nozzle_joint_v2p4.py`) and `nozzle_lip_melt_v2p4.json` (`118b7901855d74a4`, script `nozzle_lip_melt_v2p4.py`), on Mechanical's FE runs of the assembled nozzle (FEA, used as delivered).

**Finding.** The NZ-03 insert-shoulder gasket (mica/vermiculite, 1 mm, continuous rating 900 C as recalled, TO-VERIFY) reaches 1595 C in the FE runs (B1 p99, in-burn 1593 C, soak 1595 C): it fails by 695 K. NZ-02 peaks at 1551 C (soak), which also rules out a glass-phenolic sleeve (as recalled, TO-VERIFY); Mechanical confirms the NZ-02 material in the same FE re-run.

**Leak path if the joint does not seal** (DERIVED on design dimensions): grooves 2.0 mm2 (0.014 At) and the spigot-lip radial gap 23.8-33.9 mm2 (0.16-0.23 At). The hot-gas leak is 0.83-1.10 % of the engine flow, 2.2-2.9 g/s at 100 %.

**Lip melt if the leak impinges** (DERIVED; 316L melting at 1400 C; deposition 5-20 % ASSUMED; adiabatic outer face and no latent heat, so the times are short and conservative):

| Joint and start temperature | Lumped, 1 mm of lip [s] | Finite difference, 1 mm depth [s] |
|---|---|---|
| J1, start 342 C (B1 p99, the worst start) | 1.07-5.70 | 6.63-40.26 |
| J1b (0.5 mm graphite), B1 start 223 C | 1.19-6.34 | 7.39-44.33 |

All are shorter than an A1 or B1 burn: a leaking joint is not tolerable, and sealing is the control.

**Joint J1, CONFIRMED by the lead (CHANGELOG line 146; material data LITERATURE as recalled, TO-VERIFY).**
- Hot layer: a 2.0 mm carbon-phenolic flange, integral with NZ-02 (top-hat sleeve) or a separate washer. Requirement: service >= 1700 C (FE 1595 C + 100 K); bearing 10.6 MPa (Mechanical load case BN, 63.1 bar) with >= 2x strength at temperature; through-conductivity about 1 W/m K or less, for the lip, 250 C was a goal, not a limit (CHANGELOG line 145); with J1 the lip runs at about 342 C in-burn (`nozzle_lip_melt_v2p4.json`); no SiO2 in contact with graphite above about 1400-1500 C.
- Seal: a 0.5 mm flexible-graphite ring (oxidation-inhibited grade) at the cold lip face, gas-tight at MEOP 45 bar. Free O2 reaches up to 12 % at O/F 8-11.6 (§4.6), hence the inhibited grade.
- Risks: char depth and shrinkage (the preload is pressure-energised); pyrolysis gas into the annulus, which vents to the chamber through the grooves.
- Alternative J2 (zirconia washer), not selected (J1 confirmed, line 146; Mechanical rejects J2 in line 179), is listed in the data file.

**Verification.**
- Mechanical FE re-run with the two-layer stack and contact conductances: hot-layer peak, seal-face peak in-burn and in soak, lip peak.
- T1: a thermocouple well in the lip at r 21 mm and one at the lip bore edge.
- Before and after every firing: pressure-decay leak check of the assembled joint with N2 at 67.5 bar (criterion TO-DEFINE with Mechanical). This is the control for H19 (§9).
- Post-test: section the hot layer (char depth, cracks), inspect the lip bore and the spigot OD for leak tracks, and measure the stack height loss.
- Prices TO-QUOTE (Sønderborg DK-6400): carbon-phenolic tube or plate, zirconia washers, flexible-graphite sheet, C-rings.

## 7. Ignition, restart, start-up and shutdown

### 7.1 Trade and choice

Criterion weights (engineering judgement, DERIVED, `ignition_v2.json`):
- restarts >= 3: 3;
- reliability with N2O: 3;
- hard-start risk: 2;
- mass on the gimbal: 1;
- electrical energy and HV: 1;
- extra fluids or hazmat: 2;
- buildability and cost: 2;
- evidence base: 2.

| Option | Score | Main reasons |
|---|---|---|
| Torch, N2O/propane, spark | 0.800 | Independent of grain state. A hot jet of about 3 kW for 0.3-0.6 s. Restarts limited only by propane. Needs a propane cylinder, 2 NC solenoids, 2 check valves and a plug. Widely used on amateur and university hybrids. |
| Arc-ABS (USU type) | 0.675 | No extra fluid. Relights are shown with GOX; with N2O the published work needed more arc power or an O2 assist (LITERATURE-UNVERIFIED). Electrodes in every grain. 200-1000 V class supply. |
| Pyrotechnic cartridges | 0.637 | Excellent first start, but one cartridge per start, debris, and explosives rules in Denmark (TO-VERIFY). |
| Catalytic N2O decomposition | 0.525 | 50-200 W preheat for minutes. Bed poisoning. Decomposition can propagate upstream into the feed. |

Decision: the spark-ignited N2O/propane torch, firing radially into the pre-chamber.

Research proposal, arc-ABS:
- Hypothesis: arc ignition of printed ABS with N2O meets >= 3 starts and +/-50 ms latency scatter with no propane system.
- Comparator: the torch.
- Evidence: GOX literature only.
- Refutation criterion: in a bench series, any no-light, or latency scatter above +/-50 ms.

### 7.2 Torch specification

Sizing is DERIVED/CEA (`ignition_v2.json`):
- Operating point: torch Pc 3 bar, O/F 5.5, throat 2 mm, c* 1586 m/s, Tc 2852 K.
- Flow: mdot 0.594 g/s, of which propane 0.091 g/s and N2O 0.503 g/s; enthalpy flux 3.03 kW.
- Per 0.6 s start: 0.055 g propane and 0.302 g N2O.
- Orifices:
  - N2O 0.131 mm at 20 C (Dyer model, Cd 0.65 ASSUMED; 0.128-0.137 mm over 10-25 C);
  - propane 0.254 mm (Cd 0.80 ASSUMED);
  - both calibrated by weighing.
- Torch Pc of 3 bar keeps the outlet choked into a cold chamber and stays below the propane vapour pressure down to about 0 C (4.7 bar).
- Envelope (for Mechanical): body <= 45 mm long and <= 20 mm diameter, on a radial boss at x_face 0.015 m, axis inclined 30 deg inward and aft.
- Electrical (for Electronics): 12 V; coil primary peak 4 A; spark 50 mJ at 50 Hz for 0.5 s; two solenoids at 12 V, 0.8 A each, for 0.6 s; 15 J per start.
- Mass: 0.2-0.3 kg (ASSUMED).
- Starts: >= 3 per flight, limited by propane and N2O consumption.

**Torch-confirmation gate (v2.4).** kTorchConfirmBy_s = **0.16 s** from E0 (`torch_gate_v2p4.json`; SIM on ASSUMED distributions).
- E0 -> E1 is the sum of solenoid opening U(5, 20) ms, torch light U(20, 100) ms and flame detection U(5, 30) ms. Over 1e6 samples: median 0.0900 s, p99 0.1378 s, maximum 0.1494 s; the sum is bounded at 0.150 s by construction.
- The gate is that bound plus a 10 ms allowance for ECU sampling and debounce (DERIVED).
- The v2.3 value of 0.100 s would have rejected 37.5 % of good torch lights. It is withdrawn as a gate.
- Condition: IGN-1 measures the three delays. The gate stands if the measured p99.9 of E0 -> E1 is <= 0.15 s; otherwise Combustion re-derives it.
- LEAD 2026-10-13: adopted as the ECU design value, provisional until this publication. combustion.json v2.4 publishes it.

### 7.3 Sequence (v2.4: the v2.8 relight design; replaces the v2.3 sequence)

The v2.3 sequence is kept in §13 as superseded evidence. It had an N2O-only torch interval, an ungated N2O admission, a fail-safe path that waited for the pintle, and an unworkable in-flight retry (RC-01). The design below is Electronics' v2.8 firmware sequence as adopted by the lead on 2026-10-13, with Combustion's inputs to it. Electronics owns the implementation (OI-8).

**Epochs** (combustion.json `igniter.sequence_v2p4.epochs`):

| Epoch | Event |
|---|---|
| E0 | ECU executes START or RELIGHT at the planned T_fire. The MV latch is set and the opener ramps it open (0.35 s), with the pintle seated; on an A1 relight the MV is already open from PURGE (step 1). SOL1 (torch N2O) and SOL2 (propane) open; spark from E0 + 0.02 s |
| E1 | Torch flame confirmed on BOTH the torch-cavity pressure P_torch (070BG) AND the photodiode (2oo2, REQUIRED by LEAD line 164, FA-1 (a)), 10 ms persistence (Electronics). Gate: E1 by E0 + 0.16 s, otherwise TORCH_FAULT (A1). On an A1 relight with the bleed fitted, E1 also needs [bleed closure confirmed OR the closure deadline reached]; the deadline is <= the torch gate (Electronics: E0 + 0.15 s). At the deadline without confirmation: in flight BLEED_FAULT goes to the FC (log-only), V2 is commanded closed and the lift proceeds; on the stand, abort (LEAD line 166 (3)). At E1 the pintle is commanded to the ignition lift. From E1 to E2 the torch is supervised (A16) |
| E2 | Light confirmed by the relative rule (LEAD 2026-10-13): Pc rises >= 0.8 bar above the pre-lift baseline on filtered AND raw Pc for 10 ms, above a sanity floor of 1.8 bar abs. SOL1 de-energised first, SOL2 within 20 ms, spark off, ramp released. Baseline fallback (LEAD line 166, RE-02): a pre-lift P0 above the +check keeps the measured P0 (BASE_HIGH logged, FC flagged; on the pad and the stand the lift is refused with PC_SENSOR; at the A1 relight the start proceeds); P0 below the -check is set to 0 |
| E3 | Thrust >= 90 % of the start or relight command (ENG-04 latency, §7.7) |

The abort deadline W is counted from the ignition-lift command (LEAD 2026-10-13; Electronics and Combustion aligned on that epoch).

**Light rule** (LEAD 2026-10-13, on Combustion's `ignition_detect_v2p4.json`; replaces kIgnitionPcAbs 3.0 bar abs, which is withdrawn everywhere: ENG-04 P_conf, A2, E2):
- Why: at the 0.2039 mm ignition lift the first 0.1-0.4 s of a lit start are fuel-starved (O/F at the 14 clamp of the c* table). The lit plateau at the A1 state is 2.66-3.11 bar abs at 30 ms (SIM, grain_q1d over a x0.6-1.5, n 0.35-0.68, preheat 0-0.6, eta_c* 0.85-0.92). That is on the old 3.0 bar threshold: Electronics' SIL S5 lost 31 of 300 lit pad starts to it. An unlit chamber at 29-42 g/s reads 1.08-1.52 bar abs (gas-phase 190-600 K and the SIL cold model). With a post-zero residual of +/-0.6 bar no absolute threshold separates the two.
- Baseline: mean Pc over [E1 - 20 ms, E1] (torch lit, pintle seated), checked against the auto-zero ambient.
- Light: rise >= 0.8 bar on filtered AND raw Pc for 10 ms. Margins (SIM/DERIVED): unlit rises 0.07-0.51 bar, 0.29-0.45 bar below the threshold; lit rises clear it by 0.58-0.85 bar. E2 falls 14.0-15.5 ms after light on all ten corners run.
- Sanity floor 1.8 bar abs, raised to 2.0 bar abs once B-PC-1 shows a post-zero residual <= 0.3 bar.
- Earliest credible light: 0.079 s after the lift command on a liquid line (lift reached 28.7 ms, ignition delay >= 0.05 s ASSUMED).
- The bleed flow has stopped by E0 - 0.05 s, so the baseline window never sees bleed flow. If closure is not confirmed by the closure deadline (<= the torch gate), E1 is declared at the deadline with BLEED_FAULT to the FC and V2 commanded closed, and the relight proceeds (LEAD line 166 (3)); on the stand it is an abort. The open bleed draws from the feed upstream of the pintle and does not change Pc.

**Drogue release** (LEAD 2026-10-13, superseding the 08:05Z rule): release at E2 AND [measured Pc >= 3.0 bar abs OR the 0.8 bar rise held continuously to E2 + 0.10 s]. GNC finds a 0.10 s hold P-neutral (a 0.4 s hold costs P).
- The hold bit (TLM_FAST b7) is evaluated on the FILTERED channel only (LEAD line 156, on the check below). E2 itself keeps filtered AND raw.
- FC predicate (restated, LEAD line 168): while the drogue is attached, on each new TLM_FAST frame, RELEASE iff RUN AND b4 AND [(Pc valid AND >= 300 kPa abs) OR b7 OR (d2-d3 = 0xFFFF AND t >= t_E2 + 0.10 s)], latched, with t_E2 from EVENT 0x120; a late invalidity releases on the first invalid frame. b7 sets only on a valid filtered channel, never on an invalid one.
- The line-161 sentence "the FC never holds the drogue with the engine in RUN beyond E2 + 0.10 s" is withdrawn (line 168); the invalid-Pc term is now inside the predicate. A release on a dead engine under Pc invalid (sensor fault plus flame-out in [E2, E2 + 0.10 s]) goes to the FMEA; Electronics assesses whether the FA-1 photodiode can serve as a non-Pc flame-out indicator in RUN.
- A7 must therefore not set telemetered Pc invalid on a late-light plateau in flight (§7.4, A7).
- v2.4a: LEAD line 175 (5) replaces the time-only 0xFFFF term in design by an accelerometer-gated term (with Pc invalid, release iff ECU RUN AND accelerometer thrust >= 37.16 N for 3 frames at 100 Hz; otherwise hold the drogue and command ABORT at t_E2 + 0.8 s; a PROPOSAL to be flown), and line 175 (4) makes Pc VALID a launch-commit condition. With Pc valid the release at E2 is unchanged; that is why an unpurged LO start is released before its vapour gap (§2.8, v2.4a).

**v2.4a: cold-flow apparent thrust under the drogue after a flame-out (LEAD line 181 (4))** (`src/cold_flow_thrust_v2p4a.py` `b4cbf147753ecc7c`; `data/v2p4a/cold_flow_thrust_v2p4a.json` `a226dfacf494cb2c`; table for GNC `cold_flow_thrust_v2p4a.csv` `e094c4be80d12f66`). GNC's R2 releases on an accelerometer thrust >= 37.16 N; its undetected flame-out at E2 peaks at 33.0 N (29.92 N on A1_none) over 0.5 s with no cold-flow term (20.85 N inside W10 < 6 m/s). With Pc invalid the ECU runs the pintle open loop on the P_feed map (A7) and A3 is blind, so nothing closes the pintle on a flame-out: N2O keeps flowing through the injector and the nozzle at the lift the thrust command sets.

- **Bound (DERIVED).** F <= mdot_max x v_iso,eq. mdot_max: Cd 0.80 (the CF-1 / CF-3 acceptance limit, line 172 (4)) x pintle area x Dyer flux with P1 = P_tank (no line loss), saturated liquid at T_tank, downstream at 1 atm. v_iso,eq: isentropic equilibrium expansion of the tank liquid to 1 atm (CoolProp): 289.7 / 301.0 / 310.2 m/s at 283.15 / 286.7 / 289.5 K. For steady adiabatic quasi-1D flow dF = (P_e - P_a) dA_e, so the thrust is largest at P_e = P_a, and every irreversibility (injector throttling, slip, non-equilibrium, friction) raises the entropy and lowers it. The bound holds for any adiabatic flow; it does not cover heat pick-up.
- **Nominal (DERIVED on ASSUMED inputs).** Quasi-steady HEM: the Dyer injector at Cd 0.70 (0.80 variant) with the grain_q1d line loss, an adiabatic chamber at the tank-liquid enthalpy, an HEM nozzle (A_t 147.9 mm2 x 0.98, eps 2.0), choked or as a venturi, optimum-expansion thrust (the eps 2.0 exit would lie below the triple point, 0.88 bar, so the full-flowing value is not evaluated). Cross-check: at the 0.2039 mm ignition lift and the A1 state the model gives 34.8-35.0 g/s against the published 35.0 g/s.
- At low lift the bound is about 15 times the nominal. The bound credits the whole tank-to-ambient expansion as axial momentum, as if the pintle were an ideal nozzle pointed aft. In the nominal model the radial pintle spray is throttled into a chamber at 1.02-1.3 bar (lifts <= 0.5 mm), and almost all of that work is lost. Only a measurement can place the truth between the two.

Table 7.3a. Cold-flow apparent thrust with the pintle at the open-loop map lift of the command (ranges over the tank states 283.15 / 286.7 / 289.5 K, 40.0 / 43.5 / 46.5 bar; drive 16.7 mm/s, 10 ms lag).

| Open-loop command | Lift [mm] | Bound [N] | Nominal, Cd 0.70 [N] | Nominal, Cd 0.80 [N] |
|---|---|---|---|---|
| 62.5 N (start level) | 0.213-0.228 | 12.5-13.3 | 0.8-0.9 | 1.1 |
| 100 N | 0.311-0.333 | 18.2-19.3 | 2.0-2.1 | 2.9-3.3 |
| 150 N | 0.453-0.488 | 26.4-28.0 | 6.2-6.7 | 8.7-9.3 |
| 200 N | 0.611-0.662 | 35.6-37.5 | 12.5-13.2 | 16.3-17.1 |
| 250 N | 0.787-0.859 | 45.8-47.9 | 20.0-20.7 | 24.6-25.5 |
| 375 N | 1.319-1.481 | 76.5-78.2 | 41.7-42.1 | 49.3-49.9 |
| 500 N | 2.059-2.431 | 117.7-119.9 | 69.1-70.6 | 80.1-81.2 |
| Any command: pintle at the full drive rate to the 4.0 mm stroke (reached 0.24 s after E2) | 4.0 | 181.5-206.5 | 105.8-122.4 | 118.9-139.2 |

- **Window 0-0.8 s after E2.** The plant is quasi-steady, so the thrust follows the lift. Holding at the start level: <= 12.5-13.3 N over the whole window (bound). On a 2500 N/s ramp to 500 N the bound passes 37.16 N 0.065-0.070 s after E2, the nominal 0.125 s after; with the pintle at the full drive rate, 0.035-0.040 s and 0.070-0.078 s.
- **Command at which the cold flow alone reaches** the 4.16 N all-winds margin (33.0 against 37.16 N): the start level (bound), 125-130 N (nominal; 108-112 N at Cd 0.80). The 16.31 N margin inside W10 < 6 m/s: 81-88 N (bound), 221-225 N (nominal; 195-200 N). The 37.16 N threshold by itself: 198-208 N (bound), 346-348 N (nominal; 309-312 N).
- **Heat pick-up (excluded; sensitivity).** With heat added at tank pressure (the largest work per joule), v_iso rises to 355 / 402 / 483 m/s at +50 / +100 / +200 kJ/kg (A1 state). The start-level bound then rises from 13.0 to 15.3 / 17.3 / 20.8 N. It reaches 16.31 N at 66-85 kJ/kg, that is 2.8-3.7 kW at the start-level flow. The nominal at the start level stays <= 1.9 N with 200 kJ/kg; at 200 N it rises from 12.9 to 24.5 N. The thermal state of the chamber, grain and nozzle at the relight is MISSING. The hot gas in the chamber at the flame-out holds about 0.55-0.80 kJ (365.65 cm3 at 3-4.4 bar).
- **Also excluded:** N2O decomposition or re-ignition on the hot grain (then the engine is not dead); the hot-gas blowdown at the flame-out (GNC's t_off decay: add the two, do not replace one with the other); vapour in the line (it lowers the thrust: HEM vapour flux 15 450 against Dyer liquid 56 843 kg/m2s); nozzle separation (it lies between the eps 2.0 and the optimum values).
- **Consequence for R2 (DERIVED; GNC re-flies).** With the command held at the start level the dead engine stays within the inside-W10 < 6 m/s margin (13.3 N against 16.31 N) unless the heat pick-up exceeds about 2.8 kW. It does not stay within the all-winds margin (4.16 N). Above about 200 N of command (bound) or 310-350 N (nominal), the cold flow alone satisfies R2 and a dead vehicle is released. The sim6 V result "R2 holds the drogue in 1000/1000" has no cold-flow term and does not cover such commands. With the engine dead the descent does not slow, so the guidance command is expected to rise; sim6 V does not record that command.
- **PROPOSAL (for GNC R2 v2 and the lead; OI-38).** While the drogue is attached and Pc is invalid, hold the open-loop command at the start level, or cap the lift at the start-level lift, until R2 confirms; GNC adds F_cold(lift, P_tank) from the CSV, bound and nominal, to the sim6 V truth thrust and re-flies. Alternative: a ratio test of the accelerometer thrust against the open-loop expected thrust. Hypothesis: the hold keeps the dead-engine apparent thrust within the margin while a lit engine still releases (62.5 N x pcf_k 0.875 = 54.7 N; GNC's release estimate >= 48.4 N). Comparator: R2 as flown. Evidence: CF-3 with a thrust load cell at the start-level, 200 N and 500 N lifts (cold chamber); a post-burn N2O pulse at the start-level lift in the T series (hot chamber; it also shows whether the grain re-ignites). Refutation: a measured cold-flow thrust above 16.3 N at the start-level lift, or a GNC re-fly in which the hold loses P.

Combustion check of the 0.10 s hold (`drogue_hold_check_v2p4.json`, `70820e0038be39a7`; SIM: grain_q1d v2 held at the ignition lift with no ramp, 288 corners: the A1 relight state and pad 15 / 20 / 24 C, Cd 0.65 / 0.70 / 0.75, three regression laws, fuel preheat 0-0.6 at main ignition, eta_c* 0.85 / 0.92):
- Every lit corner reaches E2 (13.5-18 ms after light) and keeps the rise >= 0.8 bar from E2 to E2 + 0.10 s, on the true and on the measured channel.
- Minimum margin: 0.74 bar, or 0.48 bar if the torch adds 0.3 bar to the pre-lift baseline and nothing after E2.
- The worst corner is the fuel-starved start at the A1 relight state (fuel from zero, a x0.6 with n 0.68, Cd 0.65, eta_c* 0.85, 32 g/s). There Pc stays at 2.60-2.62 bar abs, below 3.0 bar abs, so at that corner the hold branch, not the 3.0 bar branch, releases the drogue.
- The plant is quasi-steady. The margin is therefore the zero-to-peak roughness the hold tolerates: 0.48 bar, 18 % of Pc. No data exclude roughness of that size in the first 0.1 s; IGN-1 and T1 measure it. Combustion recommends evaluating the hold on the filtered channel, which attenuates roughness above about 50 Hz. The 0.3-2 Hz hybrid modes (§8) are too slow to matter within 0.1 s.
- Unlit: the largest unlit rise at 29-42 g/s is 0.51 bar (gas-phase 190-600 K and the SIL cold model; Electronics' SIL gives 0.50 bar). No unlit case reaches 0.8 bar at all, so none can hold it.
- A late light (§7.6) only raises Pc during the hold.

**ARM preconditions:**
- **Tank interlock** (LEAD 2026-10-13): T_tank 15-24 C and P_tank <= 55.28 bar abs (54.27 bar g on the 170BG tank transducer). It is checked at ARM and again at every START or RELIGHT command (§3.6).
- Tank heater hard-disabled at ARM (ENG-12; RC-13 c).
- Mode: the 2-pin coded hardware mode strap and the load-cell check agree; a mismatch refuses ARM (LEAD).
- Pintle seated and encoder healthy. MV, SOL1 and SOL2 closed (and SOL0 if adopted, §7.5).
- Continuity of the spark primary and of every solenoid.
- Sensors healthy:
  - Pc and P_torch 070BG (ENG-09 >= 70 bar; RC-13 d); P_feed and P_tank 170BG;
  - P_torch auto-zero in ARMED; ARM refused above 1.05 bar abs;
  - MSS-1 (riser-foot TEE) and MSS-2 (MV outlet, FS-01) thermocouples; the two case thermocouples.
- Chamber vented: Pc within 0.1 bar of ambient.
- Ground only:
  - stand vertical, nozzle down;
  - stand relief per §7.6, with the burst-disc break-wire in series with the ARM loop;
  - N2 purge connected;
  - remote operation, crew outside the exclusion distance (§9.2).

**Line-state flag** (option (c), adopted provisionally by the lead):
- The ECU reports PRIMED or UNPRIMED to the FC at >= 10 Hz during the coast. UNPRIMED means P_feed < 0.5 P_tank. UNKNOWN is treated as UNPRIMED.
- On UNPRIMED the FC plans 1.41 s and the ECU runs the unprimed path below. UNKNOWN = UNPRIMED: plan 1.41 s and the prep path (LEAD line 161). The stale or missing-flag rule is as in gnc.json v3 (requirements.ignition.relight_planning_value_s.stale_or_missing_flag). 0.81 s and 1.41 s are not frozen.
- After any abort the ECU takes the prep path until a confirmed light (Combustion recommendation; implemented in fw v2.8 final, NV b3). An abort empties about half of the segment.
- fw v2.8.2 (RG-08) also forces the prep path after a coast pintle anomaly: encoder invalid in COAST gives UNKNOWN, and a lift > 0.10 mm for 20 ms gives UNPRIMED.
- A segment full of saturated vapour reads PRIMED. The flag therefore does not see coast boil-off (§2.8). The re-route alone leaves more than the 18.86 cm3 zero-abort pocket in ARM LO wet and in HI (§2.8), so PURGE runs on every A1 relight whatever the flag says.

**Start and relight sequence, primed path** (P_feed >= 0.5 P_tank). The same sequence serves a pad start, a ground restart and an in-flight relight.
1. **Before E0** (relight only): chamber vented; RELIGHT refused if a case thermocouple reads > 433.15 K (LEAD). Settling under the drogue does not empty the segment (§2.8).
   - **PURGE (A1 relight; pre-scheduled, LEAD lines 153 and 160; sized in §2.8).** The FC commands PURGE 2.90 s before T_fire, through the purge trigger gate (line 161). **PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge** (LEAD line 175 (3), PROVISIONAL; T_fire delay <= 0.6 s; line 164's "the FC delays T_fire" is withdrawn). What follows a missed commit is for the lead: line 175 (3) says the relight proceeds unpurged; Combustion's check refutes that branch and proposes no relight on that pass (§2.8, v2.4a; H20).
     - The MV latches and ramps open over 0.35 s with the pintle seated.
     - The bleed path flows for 2.5 s: both taps (T4 and FD-01), a restrictor at each (two equal 0.707 mm restrictors, Mechanical line 162; the FD-01 leg carries the inline <= 15 um element), joined at a tee, then two NC valves in series (each >= 4x the restrictions' capacity), then a balanced or axial vent. The needed flow time is 1.9 s; the ECU caps the duration (line 161).
     - The close command leads by the measured valve closing time, so the flow has stopped by E0 - 0.05 s. Closure (V1 first) is confirmed on P_mid by the closure deadline, <= the torch gate (Electronics: E0 + 0.15 s); E1 needs closure confirmed OR the deadline reached. At the deadline in flight BLEED_FAULT goes to the FC, V2 is commanded closed and the lift proceeds; on the stand it is an abort (LEAD line 166 (3)). The FC action on BLEED_FAULT is LOG-ONLY until a leak response is flown and reviewed, and bleed closure confirmed from P_mid is a pad go/no-go (launch-commit item) on every flight with the bleed fitted (LEAD line 168).
     - A15 watches the pintle and Pc from the PURGE command to E1.
     - If RELIGHT is cancelled, the MV and the bleed valves close.
     - The MV is already open at E0. PURGE vents 34.3-72.9 g of N2O (planned <= 76 g) and leaves 4.77-8.15 cm3 of vapour at the seat (§2.8, Table 2.13).
2. **E0:** MV latch and opener ramp (already open after PURGE); SOL1 and SOL2 open; spark train 50 Hz, 50 mJ, from E0 + 0.02 s. The pintle stays seated, so no N2O reaches the chamber. Opening the MV onto a seated pintle pressurises the segment and relieves it if S1 was stuck (S1 flag).
3. **Torch gate:** if E1 has not occurred by E0 + 0.16 s, TORCH_FAULT (A1). No main-chamber N2O has been admitted.
4. **E1:** the pintle is commanded to the ignition lift: 0.2039 mm, the v2.8 default (37.1 g/s cold flow at 20 C, 35.0 g/s at the A1 relight state). CF-3 calibrates a lift-against-T_tank table that keeps the flow <= 37.1 g/s at 20 C and <= 37.4 g/s at the A1 state (LEAD). The lift is held until E2 (ENG-04 ignition-lift hold).
5. **Abort deadline W from the lift command:**

   | Use | Rule | W |
   |---|---|---|
   | Flight first start (pad, ground-filled liquid line) | electronics.json v2 firmware W_build_constant (LEAD). A liquid line has E1 -> E2 max 0.357 s, so P_abort 0; inventory 12.9-14.0 g at W | 0.40 s |
   | Flight relight | Sensors are telemetry only; a TC or P_feed reading cannot prove liquid or vapour at saturation (LEAD). An A1 relight lights within it with PURGE (P_abort 0 at 0-2 deg in every heat case; residual 4.77-8.15 cm3). Without PURGE the re-route alone aborts 24-100 % of would-be lights in ARM LO wet and in HI (§2.8) | 0.65 s |
   | Stand R1 | First start (LEAD 2026-10-13, stand relief option (b), fw v2.8.1) | 0.35 s |
   | Stand R2 | Every relight, after PURGE (§2.8) | 0.35 s |
   | Stand R3 | Deleted (LEAD 2026-10-13) | – |
   | Stand R4 | Any state sensor invalid | No relight |

   If E2 has not occurred by the lift command + W, main no-light (A2).
6. **E2:** SOL1 (N2O) is de-energised first and SOL2 (propane) within 20 ms, so the torch ends propane-only and never runs N2O-only. At E2, Pc is about 3 bar, below the propane supply (6.4 bar at 10 C), so propane still flows until it is cut. The spark stops. The pintle ramps to the command at <= 2500 N/s, under the Pc loop; the drive must still deliver >= 2 F_max/s (ENG-03).
7. **Run:** Pc loop at 1 kHz (Electronics). The abort monitors are listed in §7.4. MV-open supervision at E0 + 0.95 s.

**Unprimed path** (fault path; UNPRIMED, UNKNOWN, or a latch after an abort or a coast pintle anomaly). The PREPRESS runs before E0 (fw v2.8.2, as coded):
- MV opener ramp 0.35 s and hold 0.15 s with the pintle seated.
- Only if P_feed < 0.5 P_tank, or a pressure is invalid, the pintle first goes to the 0.10 mm bleed lift. The ramp then starts 0.06 s later, and the bleed lasts until the feed reads primed: in flight with an invalid pressure, until the MV OPEN switch (<= 0.41 s; bound 0.56 s). The v2.4-draft reading "0.10 mm for 0.06 s" is superseded (§2.8).
- The prepress lasts 0.50-0.56 s, after which the primed path runs from E0.
- On a liquid line with valid pressures the prep path admits no N2O before the ignition lift; with the bleed it admits 7.2-7.8 g (liquid line) before E0 (`prep_path_inventory_v2p4.json`). The latest possible light is therefore 0.56 + 0.16 + 0.65 = 1.37 s after RELIGHT. This is a deadline construction and does not depend on the segment volume (§7.7).
- **With PURGE (A1 relight)** the MV already opens on the 0.35 s ramp, and the open taps vent the segment, so a gas-filled line is not compressed fast. PURGE therefore does the PREPRESS's job. The 0.10 mm pintle bleed of the PREPRESS must not run during PURGE: it would admit N2O to the chamber, and A15 trips on a lift > 0.05 mm. Combustion recommends that on an A1 relight PURGE replaces the PREPRESS on both paths, which keeps the 0.81 s plan from T_fire. Electronics merges the two paths and GNC the planning values (open item, §12).

**Normal shutdown** (pintle-first; LEAD 2026-10-13):
1. Pre-MECO throttle-down to <= 75 % (LEAD; ENG-05).
2. The pintle closes at full drive speed.
3. The MV is de-energised on seat confirmation (encoder at the seat and Pc < 2 bar abs) or 0.30 s after the shutdown command, whichever comes first. The 0.30 s time-out is DERIVED: full stroke at 16.7 mm/s is 0.24 s, plus the 10 ms lag and 6.5 ms command latency. The segment is liquid-full at MECO; the coast then fills its traps, and in HI wet the whole segment, with vapour (§2.8).
4. Trapped liquid in the segment relieves to the tank through S1 (§2.7).
5. Ground only: after a 30 s hold, the post-test safing procedure applies (§10.2).

**Abort** (any row of §7.4):
- the MV is de-energised at once (fail-safe closed, about 30 ms);
- the pintle is commanded closed in parallel;
- SOL1 and SOL2 (and SOL0) are de-energised; the spark stops;
- if the pintle shows no closing progress 0.10 s after the command, servo power is released and the spring closes the unpowered servo (Electronics pintle_rail_v3; B-PNT-1 back-drive check);
- the ECU reports the abort to GNC and takes the prep path for the next attempt (fw v2.8 final, NV b3);
- the next attempt after any abort is treated as a vapour-segment start (LEAD).

**No automatic retry** (LEAD 2026-10-13):
- In flight, a no-light means the MV is de-energised and the pintle closed at once; the vehicle is accepted as lost under the drogue.
- On the ground, the stand is safed (§10.2) and the cause is investigated before any new attempt.
- Research proposal (not adopted): an in-flight torch-only retry after a TORCH_FAULT, when no main-chamber N2O has been admitted.
  - Hypothesis: it raises P(relight) without raising hard-start exposure.
  - Comparator: the adopted no-retry rule.
  - Evidence needed: torch no-light probability (IGN-1) and GNC's landing margin for a light about 0.2-0.4 s later.
  - Refutation criterion: negative GNC margin, or IGN-1 torch reliability that makes the retry irrelevant.

**Model transients.** The start and relight transients of the adopted sequence are in §7.7. The v2.3 figures (0.28-0.29 s to 90 %) assumed a 0.10 s torch-to-main delay, a direct step to the command, no lift hold and no valve step; they are superseded.

### 7.4 Abort matrix (v2.4; RC-01)

Every row's action is the abort of §7.3 (MV de-energised at once, pintle commanded closed in parallel, torch valves de-energised), unless stated otherwise.

Latencies used:
- Pc sensor 2.3 ms; command to servo 6.5 ms; pintle 16.7 mm/s behind a 10 ms lag (DERIVED, CHANGELOG 2026-10-12).
- MV-P closing about 30 ms; 0.10 s bounding until B-MV-1.
- Hardware over-pressure comparator: RC tau 5.28 ms, detection 2.1 ms (45 bar g step) to 10.5 ms (32.5 bar g) (Electronics v2.8).
- ECU monitor rate 1 kHz; watchdog 50 ms (electronics.json v1).

| # | Trigger | Detection, threshold and persistence | Phase | Action | Consequence (SIM unless stated) |
|---|---|---|---|---|---|
| A1 | Torch no-light (TORCH_FAULT) | E1 not reached by E0 + 0.16 s | Start, relight | MV de-energised (it has opened only onto the seated pintle); SOL1 and SOL2 off; spark off. Ground: hold and investigate. Flight: abort, no retry (LEAD) | Main-chamber N2O 0 g. Unburnt torch flow <= 0.10 g (0.594 g/s x 0.16 s, DERIVED) |
| A2 | Main no-light | E2 (relative light rule, §7.3) not reached by the lift command + W (flight first start 0.40 s, flight relight 0.65 s; stand R1 = R2 = 0.35 s) | Start, relight | Abort. Ground: post-no-light safing (§10.2). Flight: no retry; vehicle lost under the drogue (LEAD) | Liquid-line inventory at 0.2039 mm (independent of the segment volume): 12.4-13.6 g (W 0.35), 12.9-14.0 g (W 0.40) and 22.9-25.1 g (W 0.65) over the A1 state to 25 C; 13.5 / 24.9 g at the 24 C interlock (§7.6). Prep path with the PREPRESS bleed: + 7.2-7.8 g |
| A3 | Flame-out | Rise above the pre-lift baseline < 0.40 x (Pc_map(lift, P_feed) - baseline) for 20 ms (LEAD 2026-10-13, relative form, same baseline as E2). On the fuel-starved plateau after a lit start the ratio stays >= 0.53; an unlit chamber gives <= 0.25 (SIM/DERIVED, `ignition_detect_v2p4.json` part F, ten corners). At steady 12.5-100 % flow an unlit chamber gives 0.02-0.15 of the lit rise (`hard_start_sup_v2p4.json`). The v2.4-draft figure 0.15-0.25 was the ratio of absolute pressures | After E2 | Abort | Detection about 22 ms. Cold N2O then accumulates at up to 0.30 kg/s at 100 %, so detection speed matters |
| A4 | Over-pressure (hard start, runaway, blocked throat) | Software: Pc > 30 bar abs on the FILTERED channel for 5 ms (code 2 HARD_START during IGNITION, code 17 PC_OVERPRESSURE after; LEAD line 166 (4), which amends "raw" in line 160 (2); was 3 ms). Hardware OVP comparator on Pc at 31.47 bar g (band 30.90-34.06 bar abs); detection 2.1-10.5 ms; it stays the fast path for a blocked throat (Electronics confirms the S6 blocked-throat trip still comes first) | All | Abort | Runaway to full stroke: 33.7-41.7 bar, all below MEOP (§3.7). Throat block: 50.3-61.6 bar, below proof; fault load cases LC-TB70 and LC-TB-S (§3.7). A late-light spike trips neither: filtered peak <= 21.4 bar abs (LEAD line 166 (4); raw above 30 bar <= 1.9 ms); comparator RC peak <= 19.3 bar abs (§7.6). A hard-start spike (ms) is faster than any actuator: the row stops the run, and the bound is by design (§7.6) |
| A5 | Deleted (LEAD line 160) | Was: Pc > 8.0 bar abs for 5 ms from E1 to the ramp start. Replaced by the LIGHT_SPIKE log event: raw and filtered peak, time above 8 and 30 bar abs, time from the light | – | None (log only) | A5 tripped on 98 % of credible late lights, 7.4-11.7 ms after the light and before E2, early lights included. It covered no hazard: a lift error before the light is A6/A3's; after E2 the Pc loop, A7, the 30 bar abort, the comparator and the 650 N over-thrust cover it (§7.6). OI-A5-LATE closes when Electronics implements this and SIL S6 passes |
| A6 | PINTLE_FAULT | Rail OV disconnect (LTC4365 trip; abort 5 ms after the trip, MV latch drops +1 ms); jam (no motion with a command error: 0.10 s time path, 0.07 s current path); encoder invalid; position error > 0.05 mm for 50 ms (ASSUMED, Electronics sets) | All | Abort. Servo power released after a further 0.10 s without closing progress; the spring closes the unpowered servo | With the pintle jammed open, flow stops when the MV closes; the segment (37.8 g at 20 C on v3.4.1) then drains through the jammed lift. During PURGE see A15 |
| A7 | Loss or implausibility of Pc | Range, open or short, rate > 5 bar/ms, disagreement with the P_feed-based estimate > 30 % for 50 ms (ASSUMED, Electronics sets). Bands, 50 ms persistence: HOLD from E1 (low side P0 - 0.3 bar); START from E2 to E3 (low side the A3 threshold; high side 1.3 x max(map, 5.3 bar)); RUN_MAP after E3 (0.7-1.3 x map) | Stand: all phases. Flight: E0 to the ramp start; from E1 to E3 the estimate uses the lit-start band (fuel-starved plateau), not the steady map (LEAD 2026-10-13; disarming only with a written reason) | Stand: abort (Electronics v2.7); a START high-side trip on a late light is a nuisance abort. Flight during the run: open loop on P_feed with a lift cap, plus the over-thrust abort on FC_THRUST > 650 N for 20 ms (PROVISIONAL, LEAD). START high side in flight (LEAD line 160): it must neither switch the Pc loop to open loop nor set telemetered Pc invalid (0xFFFF), which would also block the drogue Pc branch. If the firmware ties the two, the START high side is blanked from E2 to E2 + 0.45 s in flight | A late-light pool holds Pc above 6.9 bar (1.3 x 5.3) for up to 0.30 s at the A1 relight and 0.41 s at 26.6 g (§7.6), so the START high side trips on a real light. Keeps an over-pressure guard when Pc is lost in flight. Recommendation kept: a second independent Pc channel on the stand (fast high-range channel adopted, TO-QUOTE) |
| A8 | Torch-line over-temperature | Thermocouples on the SOL1 body and the torch check valve > T_lim, ASSUMED 120 C, TO-SET at IGN-1 below the solenoid seal and coil rating | Burn and coast | Burn: abort. Coast or post-landing: torch isolation closed, remote vent armed (§10.2) | Guards the only dead-ended N2O volume near the hot torch (§7.5) |
| A9 | Torch valve not closed after E2 | SOL drive-current signature (Electronics) at E2 + 50 ms | After E2 | Torch isolation closed (SOL0 if adopted). Ground: the run continues only if the operator accepts. Flight: abort | Two closures in series on the torch N2O path (§7.5, R-T3) |
| A10 | Watchdog or ECU power loss | Hardware, 50 ms | All | Hardware fail-safe: MV, SOL0, SOL1 and SOL2 de-energise to close; the unpowered pintle servo is closed by the spring | Same consequence as A6 |
| A11 | Link loss | Degraded 0.02 s, lost 0.1 s (electronics.json v1) | All | Ignition: abort. Run: shutdown or the GNC HOLD policy (Electronics and GNC) | – |
| A12 | Case over-temperature | Either case thermocouple > 448.15 K for 0.2 s, armed while the MV is open (LEAD; supersedes 433.15 K) | Burn | Abort | Mechanical pre36: in-burn case maxima 86.6 C (A1 p99) to 151.8 C (B1 max) with TC-06 3.6 mm. RELIGHT refused if a case TC > 433.15 K at the command |
| A13 | S1 fault | MV closed and P_feed - P_tank > 2.0 bar for 1 s (in-situ zero required; raw error +/-5.1 bar) | Coast, post-burn | Stand: lockout, no relight, remote vent. Flight: flag and log; the relight proceeds, since opening the MV (at E0, or at the PURGE command of an A1 relight) relieves the segment (LEAD) | Lead time to MAWP 9.8-12.0 s at 18 W and 2.3-3.1 s at 58 W; none at 200 W, where only the disc protects (§2.7) |
| A14 | Bleed valve fault (two NC valves in series on the joined bleed path, downstream of the tee) | Position or current feedback per valve (Electronics sets): a valve not open within its command window, or closure not confirmed by the closure deadline (<= the torch gate; Electronics E0 + 0.15 s; LEAD line 166 (3)) | PURGE command to E1; run | One valve not opening: no purge flow at all (the taps share the pair). No commit or no flow means no purge (LEAD line 175 (3), PROVISIONAL). Combustion proposes no relight on that pass (H20; OI-31); the lead decides. If the relight proceeds unpurged, the line state is "PURGE NOT RUN" (P_abort 0.24 LO to 1.0 HI, Table 2.15), and in the LO state a vapour gap follows every light, so A3 aborts after the drogue release (§2.8, v2.4a). One valve not closing: its series partner holds; flag. Closure not confirmed by the deadline (both open, double or common-cause fault): in flight E1 is declared at the deadline, BLEED_FAULT goes to the FC (log-only, line 168), V2 is commanded closed and the relight proceeds; on the stand, abort (LEAD line 166 (3)) | Both valves open: up to 31.24 g/s liquid overboard (11.8 % of the 100 % flow; upper bound) for the rest of the flight, additive tank outflow (GNC S313, ADDITIVE governs, line 164). The injector loses <= 0.09 % at the lift and about 1.5 % at 100 % if open loop (§9.1). Jet 3.3-5.0 N through the balanced or axial vent. The series pair doubles the fail-closed probability of the purge; FMEA input (§9.1) |
| A15 (new) | PURGE anomaly: pintle drift, runaway or unplanned flow into the chamber while the MV is open with the pintle commanded seated | Pintle encoder > 0.05 mm for 10 ms, or encoder invalid; or Pc rise > 0.3 bar over the pre-PURGE baseline for 20 ms (backup for a pintle that reads seated but leaks) | PURGE command to E1 | MV de-energised; both taps closed; pintle commanded closed (spring backup as A6); torch inhibited (SOL1, SOL2, spark); no relight. Flight: vehicle lost under the drogue. Ground: hold, N2 purge, safing (§10.2) | Without A15 a tank-fed pintle runaway with a hot grain and throat is a delayed-light or hard-start path (§7.6). The exposure is 2.99-3.06 s per relight with PURGE, against 0.09-0.16 s in v2.8 (19-34 times). A15 removes the ignition source and closes the MV in about 30 ms (0.10 s bound). It cannot stop the segment's 40 g from draining through a jammed lift. Residual risk for the lead (§9.1) |
| A16 (new) | Torch loss between E1 and E2 (FA-1 (b), REQUIRED by LEAD line 164) | Loss of the flame on BOTH P_torch and the photodiode for >= 5 ms | E1 to E2 | Pintle and MV closed (abort of §7.3). In flight this is an accepted mission loss, taken to avoid a pulse above proof | Bounds the unlit N2O admitted after a torch loss to 0.9-4.0 g (35-38 g/s x 5 ms detection + 20-100 ms closing), comparable to the 1.2-2.1 g fast part: it limits the fuel-assisted hazard but does not remove it (§7.6, §9.1 FA-1) |

Inhibits (no abort, the command is refused): tank interlock exceeded at START or RELIGHT; mode mismatch at ARM; P_torch > 1.05 bar abs at ARM; burst-disc break-wire open (stand); state sensor invalid (stand R4: no relight).

Tail-off after an abort and in a planned cut-off: 33-44 N s with t10 about 0.12 s, computed on the 44 cm3 segment and not re-run on v3.4.1 (§3.7).

### 7.5 Torch N2O line and flashback (RC-01 points 1, 2 and 4; C4)

The v2.3 contradiction (C4) is removed:
- v2.3 closed propane at 0.4 s and torch N2O at 0.6 s, which gave an N2O-only interval through a hot torch.
- v2.4 closes SOL1 (N2O) first at E2 and SOL2 (propane) within 20 ms. The torch ends propane-only. No N2O sweep is kept. Electronics' SIL v2.7 shows 0 ms of torch N2O alone over 300 runs.

Requirements for the torch feed (for Mechanical and Electronics, through the lead; open item §12):

| ID | Requirement | Reason |
|---|---|---|
| R-T1 | No N2O-only flow through a hot torch, in any sequence or abort. SOL1 closes no later than SOL2. If IGN-1 shows that a propane-rich tail damages the torch, "both together" is the alternative | RC-01 point 1; ENG-05 |
| R-T2 | Dead-ended N2O volume between the last N2O closure and the torch orifice <= 0.05 cm3. SOL1 sits on a thermal stand-off at the torch inlet, with its body <= T_lim (ASSUMED 120 C, TO-SET at IGN-1) through the burn and the soak | RC-01 point 4 (hot dead-ended line) |
| R-T3 | Two closures in series between the tank and the torch. Baseline: torch N2O tapped on the tank side of the MV (FS-01 inlet), so the torch lights independently of the MV; SOL0 (NC) at the tap (cold) and SOL1 (NC) at the torch. SOL0 is open from ARM to SAFE and closes on any abort | A single stuck SOL1 must not leave an N2O-only flow path from the tank to a hot torch |
| R-T4 | SOL0 relieves backwards to the tank (built-in reverse relief or a check valve around it), so the SOL0-SOL1 line (about 1.2 cm3, 0.95 g liquid at 20 C, ASSUMED 1/8 in line, 0.6 m) is never a closed liquid volume | RC-04 trapped liquid |
| R-T5 | Check valve plus a sintered-metal flame arrestor at the torch N2O inlet, rated to MEOP 45 bar and hot gas. The flame-quench test of the arrestor and the 1/8 in line at tank pressure is TO-TEST in IGN-1 | ENG-05: no flashback or decomposition in the feed |
| R-T6 | Thermocouples on the SOL1 body and the check valve in IGN-1 and T1; the SOL1 thermocouple also in flight (A8) | RC-01 point 4 |

If Mechanical keeps both torch solenoids on the fixed side: tap the torch N2O downstream of the MV, so the MV is the second closure, and fit the check valve on a stand-off whose temperature IGN-1/T1 show <= T_lim. That leaves a dead-ended line from the fixed-side solenoid to the check valve, and with the v2.8 order (MV at E0) the torch would then wait for the MV. Not recommended.

### 7.6 Hard-start bound, stand relief and the maximum unignited inventory (v2.4; RC-02)

Basis:
- `hard_start_v2p4.json` and `hard_start_sup_v2p4.json` (single volume; first v2.4 basis);
- `sil_inventory_bound_v2p4.json` (SIL inventories);
- `hard_start_multivolume_v2p4.json` (three-node head / port / aft network; script `hard_start_multivolume_v2p4.py`).

Common inputs: cold flow by Dyer with Cd 0.70 (ASSUMED); HEM flash; products by Cantera GRI-3.0 equilibrium; gas path with D_pre 49.9 mm (TC-06 3.6 mm) and the 28.26 cm3 convergent (RC-16). In the data files "ESTIMATE" means DERIVED from ASSUMED inputs: an order of magnitude, not acceptance evidence.

**Inventory against W.** At the 0.2039 mm lift the admitted N2O, from the lift command until the pintle seats, is in the §2.8 stand table: 12.4-13.6 g at 0.35 s (stand R1 = R2) and 22.9-25.1 g at 0.65 s (flight), A1 state to 25 C. The 0.40 s and 0.50 s rows of the v2.4 draft (14.2-15.5 g and 17.6-19.3 g) applied to the former R1 and R2. The v2.3 figure of 8.74 g covered one lift and one window only and is superseded (RC-02).

**Constant-volume bound** (Cantera UV, reactants only): 190 bar for 8.74 g, 325 bar for 15 g, 434 bar for 20 g with decomposition products (284.6 cm3); with fuel at O/F 8, 404 / 703 / 944 bar. These reproduce the order of the review (165-354 bar). They are not credible peaks, because the chamber vents through the throat in 3.8-4.7 ms.

**Why a two-volume model.** Mechanical found that the only room for a stand burst disc is at the aft end, and that the initial port (491 mm2) is smaller than A_t + A_disc (639 mm2). The port therefore chokes the relief path from the head end (CHANGELOG 2026-10-13). The single-volume basis (one 25 mm disc at 55 bar holding proof to 20.75 g at tau 5 ms) is withdrawn. The three-node network reproduces the single-volume model within 0.6 % when the port is opened up (validation block).

Table 7.1. Allowable unignited inventory: the largest N2O mass that keeps the head node <= proof 67.5 bar. Decomposition products at 20 C, top-hat release at the head, reaction time tau 5 ms (SIM; discs at 55 bar, DN32 MNFA 792 mm2, K_D 0.62 per Mechanical; DN40 MNFA ASSUMED = bore).

| Stand relief | Sharp port entrance (Cd 0.65) [g] | Rounded entrance, r >= 4 mm (Cd 1.0) [g] | Rounded port exit [g] |
|---|---|---|---|
| None (flight) | 5.79 | 6.06 | 6.10 |
| DN32 at the aft end | 9.09 | 13.84 | 14.82 |
| DN40 at the aft end | 9.17 | 14.16 | 15.90 |
| DN32 at the head end | 20.68 | 20.78 | 20.72 |
| DN32 at the head and aft ends | 24.69 (23.86 with both edges sharp) | 29.44 | 30.67 |

- Reaction-time dependence: with no disc, 3.5-18.9 g over tau 2-20 ms; with both discs and a rounded entrance, 11.77 g at 2 ms and 58.9 g at 10 ms.
- Allowables against MEOP instead of proof are 2.3-12.6 g. They are not the criterion, because the stand discs protect the test article against proof.

**Credible case: the late light inside W** (`late_light_spike_v2p4.json` `57fce738164fd571`, `late_light_tables_v2p4.json` `7baa4f6fa76bfdd3`; scripts of the same name; SIM/DERIVED on ASSUMED inputs). The draft table of this paragraph (37.1-44.9 bar at tf 1 ms, from an unflown state) is superseded.
- Model: the RC-02 construct, with time histories, in the three-node network.
  - The fast part is the vapour already in the chamber plus the spray in transit (residence 20 or 60 ms), reacting over tf 1, 2, 5, 10 or 20 ms.
  - The slow part is the retained pool (none, or all of it) evaporating at 0.5-2.0 MW/m2 over the wetted port and head: 27-109 g/s on the pad grain (25 mm port), 34-136 g/s at the A1 relight (32.2 mm port).
  - The pintle is held at the ignition lift; the ramp is not modelled.
  - Measured channel delay 2.3 ms; E2 as fielded (raw rise >= 0.8 bar for 10 ms).
  - 5 400 rows: four states (pad 15 / 20 / 25 C, A1 relight), light times through W, both entrances, every tf, residence time, pool and q.

Table 7.4. Head-node peak, bar abs (it does not depend on W or on the inventory: the fast part, 1.2-2.1 g, sets it).

| State | p50 | p99 | Max, sharp entrance | Max, rounded r >= 4 mm |
|---|---|---|---|---|
| Pad 15 C | 22.8 | 43.3 | 43.7 | 40.6 |
| Pad 20 C | 22.8 | 42.7 | 43.1 | 40.1 |
| Pad 25 C | 22.8 | 41.5 | 42.0 | 39.3 |
| A1 relight (32.2 mm port) | 23.2 | 37.3 | 37.8 | 36.7 |

- By tf: 1 ms 24-44; 2 ms 22-38; 5 ms 17-31; 10 ms 11-25; 20 ms 7.4-19.4 bar abs.
- No row exceeds MEOP 45 bar. **MEOP is confirmed for the decomposition late light.** Margin of the worst row: 1.3 bar sharp, 4.4 bar with the required rounded entrance; >= 23.8 bar to proof.
- The pool sets the duration (Table 7.5). It does not raise the peak.

Table 7.5. Time above thresholds, s (p99 / max over the grid unless stated; q sweep 0.8-2.0 MW/m2 with the retained pool, tf 5 ms, residence 60 ms, rounded entrance).

| Case | Above 8 bar abs | Above 6.9 bar abs (A7 START high side) |
|---|---|---|
| A1 relight, flight W 0.65 s | 0.190 / 0.196; q sweep max 0.235 (q 1.2) | 0.298 |
| Pad states at W 0.65 s (envelope) | 0.244-0.267 / 0.252-0.274; sweep 0.251-0.285 | 0.317-0.363 |
| Flight first start, W 0.40 s (12.9-14.0 g) | 0.143-0.157; sweep 0.139-0.159 | 0.176-0.203 |
| Stand, W 0.35 s, pad states | 0.120-0.131 / 0.122-0.133 | 0.136-0.171 |
| Stand, A1 state | 0.092 / 0.094; sweep <= 0.134 | – |
| No retained pool | <= 0.017 | – |
| 26.6 g (the lead's accepted inventory) | <= 0.298-0.326 | 0.377-0.415 |

- Above 30 bar abs: raw <= 1.9 ms. Filtered (first-order 50 Hz stand-in): peak <= 21.4 bar, 0 ms above 30 bar. The comparator RC model peaks at <= 19.3 bar abs: no trip.
- A5 (8.0 bar / 5 ms, now deleted) tripped on 98 % of the grid (90 % at tf 20 ms), 7.4-11.7 ms after the light and always before E2 (raw E2 12.3-12.7 ms after the light; SIL 16-18 ms).
- Electronics' SIL S6 light times (0.20 and 0.25 s): 25.1-27.1 bar abs at tf 1 ms and residence 20 ms, against the SIL plant's 26.9 and 28.6 bar abs.
- Decisions on these numbers (LEAD line 160): A5 deleted and replaced by LIGHT_SPIKE logging; the 30 bar abort persistence raised to 5 ms raw (raw margin 1.1 ms over the 1.9 ms spike); A7's START high side must not force open loop or Pc invalid in flight; rounded entrance REQUIRED. [Amended by LEAD line 166 (4): the 30 bar abort runs on the FILTERED channel with 5 ms persistence; filtered light-spike peak <= 21.4 bar abs.]

**Fuel-assisted fast part at a relight: FA-1 envelope (v2.4a; REV-COMB-2 R2-03; LEAD lines 172 (2) and 173).** `src/fa1_envelope_v2p4a.py` (`a6b71cb487c9642e`) re-runs the v2.4 construct of `late_light_spike_v2p4.py` (hot chamber, fuel vapour premixed with the arriving N2O), first reproducing the v2.4 case to 1e-6 bar. It runs at the A1 relight (32.2 mm port, products at the A1 tank state 286.7 K) over O/F 3-12 x burn time tf 1-7 ms (1 ms steps) x residence 0.02 / 0.06 s x pool none / q 2 MW/m2, for two readings of the chamber vapour ("vapour once", the baseline; "as written", the v2.4 double count, an upper bracket) and both entrances: 896 cases, each with head and aft histories (`data/v2p4a/fa1_envelope_v2p4a.json` `64b328150025fa1e`; summary CSV `86d764bc80ed1dd5`). SIM on an ASSUMED construct (burn time, fuel fraction); tables DERIVED (`fa1_tables_v2p4a.json` `677fd9ccd297fdf4`). It supersedes the v2.4 table at O/F 8 only (48.9-75.5 bar at 1 ms, <= 55.5 bar at 5 ms, <= 41.4 bar at 10 ms), which is kept in §13.

Table 7.6a. FA-1 envelope maxima over O/F 4-12, tf 1-7 ms, residence and pool (impulse above P0 = 1.071 bar over 25 ms).

| Reading | Entrance | Head peak [bar abs] | Aft peak [bar abs] | Above 45 bar, head [ms] (longest continuous) | Above 67.5 bar, head [ms] | Above 90 bar [ms] | Impulse above P0, head, 25 ms [bar ms] | Aft / head peak |
|---|---|---|---|---|---|---|---|---|
| vapour once | rounded | 83.0 | 81.7 | 3.6 (3.6) | 0.95 | 0.0 | 721 | 0.979-0.999 |
| vapour once | sharp | 84.8 | 81.6 | 3.65 (3.65) | 1.0 | 0.0 | 726 | 0.951-0.998 |
| as written | rounded | 86.4 | 85.2 | 4.45 (4.45) | 1.3 | 0.0 | 752 | 0.982-0.999 |
| as written | sharp | 88.0 | 85.0 | 4.45 (4.45) | 1.3 | 0.0 | 757 | 0.957-0.998 |

Table 7.6b. Head peak [bar abs] by O/F and burn time, maximum over residence and pool: baseline (vapour once, rounded entrance) / upper bracket (as written, sharp entrance).

| O/F | tf 1 ms | tf 2 ms | tf 3 ms | tf 4 ms | tf 5 ms | tf 6 ms | tf 7 ms |
|---|---|---|---|---|---|---|---|
| 3 | 78.3 / 82.9 | 71.0 / 75.2 | 65.5 / 69.4 | 61.0 / 64.4 | 57.2 / 60.1 | 53.9 / 56.4 | 51.2 / 53.2 |
| 3.5 | 82.5 / 87.4 | 74.5 / 79.1 | 68.4 / 72.7 | 63.4 / 67.2 | 59.3 / 62.5 | 55.8 / 58.4 | 52.8 / 54.9 |
| 4 | 83.0 / 88.0 | 75.0 / 79.8 | 68.8 / 73.4 | 63.8 / 67.9 | 59.6 / 63.0 | 56.1 / 58.9 | 53.0 / 55.3 |
| 5 | 81.2 / 86.2 | 73.6 / 78.6 | 67.7 / 72.6 | 62.9 / 67.2 | 58.8 / 62.5 | 55.3 / 58.4 | 52.4 / 54.9 |
| 6 | 77.7 / 82.6 | 70.6 / 75.6 | 65.2 / 70.1 | 60.7 / 65.1 | 56.8 / 60.7 | 53.6 / 56.8 | 50.7 / 53.4 |
| 8 | 71.2 / 75.8 | 65.1 / 69.9 | 60.3 / 65.1 | 56.3 / 60.7 | 52.9 / 56.8 | 50.0 / 53.2 | 47.4 / 50.1 |
| 10 | 66.4 / 70.9 | 60.9 / 65.5 | 56.6 / 61.3 | 53.0 / 57.3 | 49.9 / 53.7 | 47.2 / 50.5 | 44.9 / 47.6 |
| 12 | 62.9 / 67.2 | 57.8 / 62.2 | 53.9 / 58.3 | 50.5 / 54.7 | 47.7 / 51.4 | 45.1 / 48.4 | 43.0 / 45.7 |

- **O/F.** The closed-volume pressure of the fast part (2.141 g N2O in 365.65 cm3) peaks at O/F 3.5-4 (about 89 bar) and falls at lower O/F (84.5 bar at 3, 61 bar at 2). The first-order fuel-vapour bound does not exclude O/F below 4 (minimum about 1.5-2.0), but within the construct the O/F 3.5-4 rows bound the peak. The fuel-vapour inventory at the light remains MISSING (IGN-1, T4).
- **Burn time.** At O/F 4 (baseline) the peak falls from 83.0 bar at tf 1 ms to 53.0 bar at 7 ms, while the time above 45 bar stays at 3.15-3.6 ms and the impulse at 718-721 bar ms: a slower burn trades peak for duration at about constant impulse.
- **Entrance and aft end.** The rounded entrance lowers the baseline peak by about 2 % at the 32.2 mm port (83.0 against 84.8 bar). The aft node carries 0.95-1.00 of the head peak, so the J1 lip and the aft closure take the same load.
- **Thrust.** Peak 1.63-1.70 kN (Cf 1.35) or 1.69-1.77 kN (quasi-steady, eta_cf 0.975). The SDOF equivalent is <= 3.05 kN at periods of 0.5-5 ms, against 3.48-3.60 kN for the interim 1.8 kN x 4 ms rectangle, which therefore bounds.
- **Pressure DLF.** <= 1.007 for periods <= 0.1 ms (shell and bonnet: quasi-static valid); 1.05-1.20 for periods of 0.25-1 ms, giving a head equivalent static of <= 89.0 bar abs (baseline, rounded) and <= 102.0 bar abs (upper bracket, sharp).
- **Fuel basis.** Styrene gas instead of the ABS card: +1.8-2.8 % on the peak (90.1 bar on the as-written sharp case; 85.0 bar baseline rounded).
- **Outflow model form (R2-11).** Frozen-gamma outflow vents about 4 % fast. Reducing the throat area by 3.7 % (8 %) raises the tf 1 ms peak by 0.5-0.6 % (1.1-1.3 %), the tf 3 ms peak by 1.4-1.6 % (3.0-3.5 %) and the time above 45 bar by 0.15-0.25 ms (0.35-0.55 ms) (`fa1_outflow_sens_v2p4a.json` `540a78f8b9634f76`; a first-order emulation, ASSUMED). The 92 bar design value (89.0 x 1.03) becomes about 92.2 bar with the 4 % form (92.9 bar at 8 %); the 102 bar sensitivity covers it.
- **Not modelled:** acoustic and wave peaks along the 230 mm port (lumped nodes; transit about 0.3 ms hot and 1 ms cold); equilibrium thermochemistry (kappa fitted at 40 kg/m3 overstates the pressure by about 3.7 % at 6.6 kg/m3, conservative); flame spread, heat loss and roughness; the torch contribution before the light. A 1-D gas-dynamic run of the worst row would close the model-form items (R2-11; OI-36).
- **Load (LEAD line 173).** FA-1 structural load: 90 bar abs quasi-static at head and aft for every part; parts with natural periods of 0.25-1 ms also at 92 bar abs (design: baseline rounded with DLF and the +3 % fuel basis) and 102 bar abs (sensitivity: upper bracket, sharp, DLF); thrust spike 1.8 kN x 4 ms, confirmed bounding. Mechanical's margins (line 176, SF 1.0, FE and hand results) led to the lead's actions (line 177): the TC-09 aft section changes to Inconel 718 (316L yields at 90 bar); J-FWD to yield MS >= 0 at 92 bar and ultimate MS >= 0 at 102 bar; seal S13 (-0.016 at 102 bar only) accepted as a sensitivity result; the gimbal 608 bearings reselected against a maker-datasheet C0 at Combustion's SDOF 3.05 kN with DLF 2.0. Status from Mechanical (lines 178-179, SIM/DERIVED): TC-09 Inconel 718 is in CAD v3.5; J-FWD moves to A4-80 screws (yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar); the bearing selection is OPEN (C0 >= 1.80 kN per bearing from a maker datasheet, not done).
- A pad start from a cold chamber has only the torch propane as fuel before main ignition (0.027 g over 0.30 s, enough to burn 0.27 g of N2O, 14-22 % of the fast part), so the fuel-assisted case does not apply to it.
- **MEOP is NOT confirmed for the fuel-assisted case.** The control is the torch-first gate alone: a single-control hazard, FA-1 in §9.1 (LEAD lines 160 and 164). Electronics is required to fit (a) E1 on P_torch AND photodiode and (b) torch supervision from E1 to E2 (A16). These limit the exposure; they do not remove it. FA-1 is accepted for design continuation only. Flight acceptance needs IGN-1 (>= 30 lights with photodiode false-positive tests, on the stand dynamic Pc channel) and Mechanical's margins against the line-173 load with the line-177 actions closed (LEAD lines 170 (2), 172 (2), 173, 177).

**Stand relief options** (not to be confused with the relight-vapour options (a), (b), (d) of §2.8):
- **Stand relief (b), adopted by the lead on 2026-10-13** (Mechanical found no room for a head-end disc): aft DN32 disc only, R1 = R2 = 0.35 s with the rounded entrance, R3 deleted, R4 kept (fw v2.8.1). At 24 C, 0.35 s admits 13.5 g against the 13.84 g allowable, a margin of only 0.3 g. With a sharp entrance (9.09 g) the rule would fail by 4.4 g.
- Stand relief (a), for the record: a stand-only DN32 disc at the head end plus the aft disc. R1 0.40 s (15.4 g at 24 C) and R2 0.50 s (19.2 g) were inside the head-disc allowable alone (20.7 g); R3 0.65 s (24.9 g) needed both discs and the rounded entrance (29.44 g allowable).

**Rounded port entrance, r >= 4 mm: REQUIRED on every grain, flight and stand (LEAD line 160).**
- Under the adopted stand relief (b) it sets the 13.84 g allowable (above).
- In flight it lowers the decomposition late-light peak at the pad states from 43.7 to 40.6 bar abs (Table 7.4). It does not lower the fuel-assisted peak at the 32.2 mm relight port. The draft figures of 44.9 to 41.5 bar and 72.8 to 62.9 bar are superseded.
- Combustion downsides: none found in the models.
  - Every relight already starts from an entrance rounded by the previous burn: the head end regresses at about 1.28 mm/s at the initial G_ox of 491 kg/m2s, so a 4 mm radius forms within about 3 s.
  - The pre-chamber recirculation, not the port lip, holds the flame.
  - The radius removes about 0.29 g of ABS and adds a little burning area at the head (negligible for O/F). It prints without support.
  - Cd 0.95-1.0 for r/D 0.16 is ASSUMED (LITERATURE as recalled).
  - Ignition delay and flame holding are measured at T1 on grains that carry the radius, so no separate test is needed.

**Maximum unignited inventory** (RC-02 closure statement):
- **Stand:** the allowable of the installed relief at tau 5 ms: 13.84 g with the adopted aft DN32 disc and the rounded entrance. R1 = R2 = 0.35 s admit <= 13.5 g at 24 C (margin 0.3 g). The 20 g criterion would have applied with stand relief (a) only.
- **Flight:** up to 26.6 g accepted by the lead, on the inventory-independent decomposition peak (<= 43.7 bar abs sharp, <= 40.6 rounded; <= 37.8 at the A1 relight). The inventory sets only the duration (Table 7.5). The fuel-assisted relight case is FA-1 (above). In flight a no-light loses the vehicle (no retry), and the hazard of a delayed light is to the vehicle.
- **Inputs:** every input of the credible case is ASSUMED. IGN-1 and T1 supply the ignition delay; nothing measures the pooled-liquid reaction time, and it is not to be measured deliberately (review §11).

**Stand provisions** (IGN-1 with main N2O, CF-3, T1-T4):
- **Orientation:** vertical, nozzle down, so liquid drains through the throat instead of pooling below a horizontal lip (RC-02 point 5).
- **Test article:** proof-tested chamber (67.5 bar); remote operation; crew beyond the exclusion distance (§9.2).
- **Discs:** the aft DN32 disc (stand relief (b)), test-article only. Mechanical places them, protects them from hot gas and routes the discharge (reaction 3.3-4.1 kN axial; LC-HS in the assembled FEA). Break-wire in the ARM loop.
- **Wait after a no-light:** after W the chamber can hold 6.5-15 g of liquid. Wall conduction alone needs >= 5-27 s to evaporate it, and a pool takes far longer. An N2 purge at 10 g/s needs 11-25 s at 20 % effectiveness (ASSUMED). The v2.3 rule "wait >= 5 s" is withdrawn. Ground rule: N2 purge >= 60 s at >= 10 g/s, then a hold of >= 15 min before approach with Pc at ambient and the head thermocouples falling, then the safing procedure (§10.2). This is the one stand rule after a no-light (LEAD line 172 (1)); H9, §10.2 and the interface (`stand_safing_v2p4a`) carry the same text.
- **Coast leak ceiling:** 0.0055 g/s (§3.5).

### 7.7 Relight latency of the adopted sequence and ENG-04 (v2.4; RC-03)

Method (`start_latency_v2p4.py`, `relight_latency_sup_v2p4.py`, `post_abort_pocket_v2p4.py`):
- Part 1: grain_q1d runs of the ignition-lift start at each state and lift, over a x0.6-1.5, n 0.35-0.68, preheat 0.15-0.6 and eta_c* 0.85/0.92 (ramp 2500 N/s, feed-forward and with a Pc loop of gain K 15).
- Part 2: a 200 000-sample Monte Carlo (seed 2024) over ASSUMED delays: solenoid U(0.005, 0.020) s; torch light U(0.02, 0.10) s; flame detection U(0.005, 0.030) s; valve flow onset U(0.05, 0.15) s; main ignition delay U(0.05, 0.30) s (the review's band); purge of vapour in the segment at 0.31 s per 21.42 cm3 at the 12.5 % lift, scaled with volume and with the lift.
- No distribution is MEASURED; IGN-1, T1 and T4 replace them.

**Epochs for ENG-04** (for the lead): ENG-04's 0.5 s is counted from E0 (RELIGHT executed at T_fire) to E3 (90 % of the relight command). In the v2.8 design the MV opens at E0, so no valve onset remains in the path.

Table 7.2. A1 relight, 44 cm3 segment, MV open before the lift, Pc loop K 15 (`relight_latency_sup_seg44_v2p4.json`; s).

| Segment state at the lift | E0->E2 median / p95 / p99 / max | E0->E3 median / p95 / p99 / max | E1->E2 max |
|---|---|---|---|
| Liquid | 0.315 / 0.437 / 0.462 / 0.499 | 0.408 / 0.529 / 0.555 / 0.591 | 0.357 |
| Vapour only in the 4.51 cm3 manifold (full) | 0.381 / 0.502 / 0.528 / 0.564 | 0.473 / 0.594 / 0.621 / 0.657 | 0.422 |
| Hot-end pocket 8 cm3 (full) | 0.431 / 0.553 / 0.578 / 0.615 | 0.523 / 0.645 / 0.671 / 0.707 | 0.472 |
| Vapour fraction U(0,1) of 44 cm3 | 0.633 / 0.954 / 1.026 / 1.124 | 0.726 / 1.046 / 1.119 / 1.219 | 0.989 |
| Whole segment vapour (44 cm3) | 0.952 / 1.074 / 1.099 / 1.136 | 1.044 / 1.166 / 1.192 / 1.228 | 0.993 |

These are latencies of a light without the W abort. With the flight W of 0.65 s, any case with E1->E2 > 0.65 s aborts instead (P_abort against pocket volume, §2.8). Table 7.2 was computed on the v3.4 segment (44 cm3). Its liquid and fixed-pocket rows depend on the pocket, not the segment, and hold for v3.4.1; its whole-segment rows are superseded (48.2-50.0 cm3: E1->E2 max 1.11-1.14 s).
- **Purge basis of Table 7.2.** Its vapour rows use the 0.31 s per 21.42 cm3 purge of the 0.2192 mm lift (0.637 s for 44 cm3), not the 0.685 s of the 0.2039 mm lift; the method text "scaled with the lift" did not hold for this file. The §2.8 tables use 0.2039 mm and govern: whole segment E0->E2 median 1.000 / max 1.183 s, E1->E2 max 1.041 s. The vapour-first inventory rows of `relight_window_rule_seg44_v2p4.json` carry the same 0.637 s; at the longer purge less liquid is admitted by W, so those rows overstate the inventory by up to about 1.7 g (conservative).

Table 7.3. Relight latency at the 0.2039 mm lift by line state (`route_void_bracket_v2p4.json` `fixed_states`; W 1.05 s; s). The PURGE rows are DERIVED: the liquid row shifted by the pocket at 0.015555 s/cm3, the same construction that reproduces the file's fixed-pocket rows (for example 6.9 cm3: +0.107 s). They replace the v2.4-draft rows for the v3.4 bore leg (4.51 cm3) and the option (a) residuals (6.9 and 9.6 cm3), which are superseded.

| Line state at the lift | E0->E2 median / p99 / max | E0->E3 median / p95 / p99 / max | W for P_abort 0 |
|---|---|---|---|
| Liquid | 0.315 / 0.462 / 0.499 | 0.408 / 0.529 / 0.555 / 0.591 | 0.357 |
| PURGE residual, low end (4.8 cm3: the 4.42 cm3 annulus plus regrowth) | 0.389 / 0.536 / 0.573 | 0.482 / 0.603 / 0.629 / 0.665 | 0.431 |
| PURGE residual, high end (8.2 cm3) | 0.442 / 0.589 / 0.626 | 0.535 / 0.656 / 0.682 / 0.718 | 0.484 |
| 19 cm3 (the requirement) | 0.611 / 0.758 / 0.794 | 0.703 / 0.825 / 0.851 / 0.887 | 0.652 |

**ENG-04 status** (Combustion's reading; the lead states the status):
- Liquid segment: E0->E3 median 0.408 s, p95 0.529 s, p99 0.555 s. Met at the median and to about p90, not at p95, under the ASSUMED delays.
- The dominant term is the ASSUMED main-ignition delay U(0.05, 0.30) s. IGN-1 and T1 decide.
- With retained vapour <= 19 cm3 (the flight requirement), lights occur within W; their E0->E2 is median 0.463 s and at most 0.784-0.794 s (`line_states_for_gnc_44cm3`).
- No relight after a coast starts liquid at the pintle: PURGE leaves 4.8-8.2 cm3 at the seat, including the 4.42 cm3 annulus that no tap sweeps (§2.8). The relight E0->E3 is then median 0.482-0.535 s and p95 0.603-0.656 s. **ENG-04 (<= 0.5 s) is met at the median only at the low end of the residual, and not at p95**, under the ASSUMED delays. The 0.81 s planning value is a deadline and is unaffected; GNC's thrust-onset distribution moves by 0.07-0.13 s (open item, GNC).

**Planning values for GNC** (LEAD 2026-10-13, unchanged by the segment volume):
- Flight planning value **0.81 s** = torch gate 0.16 + W 0.65. It is the latest Pc confirmation of any light, by construction.
- Unprimed fault path: **1.37 s** = prepress 0.56 + gate 0.16 + W 0.65. The FC plans 1.41 s on UNPRIMED.
- **The segment volume does not move either bound.** Both are deadline constructions: a larger vapour pocket produces more aborts, not later lights. GNC's open item (the 1.37 s path derived on the old segment with only 0.04 s of plan margin) is answered by this argument; the abort probability is what changes.
- **With PURGE** (A1 relight) the FC issues PURGE 2.90 s before T_fire (LEAD line 164); the 0.81 s plan from T_fire and W 0.65 s stay (E0 -> E2 max 0.626 s on the worst purged state). N2O per relight: 34.3-72.9 g, planned <= 76 g (GNC mass budget). PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL; it withdraws line 164's "the FC delays T_fire"). In GNC rev2 the T_fire delay is <= 0.6 s and costs no measurable P; the decided-path height cost is <= 3.04 m (line 174, SIM). After a missed commit see H20 (§2.8, v2.4a). With PURGE replacing the PREPRESS on A1 relights (§7.3, recommendation), the 1.41 s UNPRIMED plan is not needed for A1 relights.
- **The prep path at W 0.88 s** (GNC's zero-abort comparator, plan 1.60 s) admits 30.9-33.8 g on a liquid line (33.6 g at 24 C) without the PREPRESS bleed and 38.0-41.7 g (41.4 g at 24 C) with it. On Combustion's plant it lights a vapour-full segment only with the bleed: the SIL's 0.17 s prep credit is not reproduced (§2.8).
- Line states for GNC's re-run at 44 cm3 (`post_abort_pocket_v2p4.json` `line_states_for_gnc_44cm3`; 5 %-step E0->E2 quantiles given a light):

| Line state | P(abort of a would-be light), W 0.65 s | E0->E2 median / max [s] |
|---|---|---|
| Pocket U(0, 19) cm3 (meets the requirement) | 0 in 200 000 | 0.463 / 0.784 |
| Pocket 19 cm3 (at the requirement) | 0.0005 | – / 0.794 |
| After an abort, compressed to tank pressure (20.1 cm3) | 0.0515 | – / 0.812 |
| After an abort, not compressed (24.3 cm3) | 0.313 | – / 0.877 |
| PURGE residual 4.77-8.15 cm3 (A1 relight, v3.4.1, decided path; Table 2.15) | 0 in 200 000 | 0.390-0.442 / 0.573-0.626 |

- On the unprimed path the prepress compresses the segment to tank pressure before E0. An UNPRIMED segment holds P_feed < 0.5 P_tank, so its pocket after compression is <= 22 cm3 without condensation credit (P_abort <= 0.17) and smaller with it (DERIVED, isothermal).

**What keeps the relight inside the planning value** (v2.4 final, CAD v3.4.1):
- the pintle-first normal shutdown keeps the segment liquid-full at MECO, but not through the coast;
- S1 vents only the expansion. The coast fills the flow-path traps (12.0-13.8 cm3 at 0 deg, plus hose humps at tilt) and, in HI wet, the whole segment (§2.8);
- the re-route alone keeps the pocket below 18.86 cm3 at 0-2 deg only in LO (except ARM LO wet) and in isothermal HI dry;
- PURGE on the decided path brings the pocket at the lift to 4.77-8.15 cm3 in every case at 0-2 deg (P_abort 0; Table 2.13). The 4-20 deg sensitivity was run only on the coarse grid at 0.8 and 1.0 mm per tap;
- the prep path after an abort remains the fault path; on an A1 relight Combustion recommends that PURGE replaces the PREPRESS (open item, §12).

**Options for the lead if ENG-04 must hold at p95** (under the ASSUMED delays it does not):
1. Accept ENG-04 as a median requirement, with GNC planning on the distributions above.
2. Shorten the ignition delay with a hotter torch or a longer torch overlap; IGN-1 measures the effect.
3. Count ENG-04 from E1 (torch confirmed) instead of E0; this removes 0.09-0.15 s.

## 8. Combustion stability

Table 8.1. Feed-coupled (chug) stability and acoustic frequencies (DERIVED, `stability_v2.json`). Model: double-time-lag (Crocco/Summerfield class) with the hybrid fuel path. Karabeyoglu-type hybrid low-frequency modes are not modelled.

| Port [mm] | Throttle % | Pc [bar] | O/F | dP/Pc | GM (tau 1 ms) | GM (tau 10 ms) | tau_crit | Thermal lag [ms] | f thermal lag [Hz] | f Helmholtz [Hz] | f 1L [Hz] | f 1T [Hz] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100 | 25.01 | 10.43 | 0.93 | 21.8 | 4.7 | inf | 73 | 2.2 | 1125 | 1460 | 10407 |
| 25 | 75 | 19.10 | 8.99 | 1.58 | 34.0 | 7.5 | inf | 99 | 1.6 | 1138 | 1477 | 10524 |
| 25 | 50 | 13.20 | 7.34 | 2.78 | 56.8 | 12.5 | inf | 149 | 1.1 | 1155 | 1499 | 10686 |
| 25 | 25 | 7.33 | 5.32 | 5.86 | 106.0 | 23.7 | inf | 283 | 0.6 | 1180 | 1532 | 10916 |
| 25 | 20 | 6.16 | 4.85 | 7.18 | 121.5 | 27.2 | inf | 340 | 0.5 | 1186 | 1539 | 10965 |
| 25 | 12.5 | 4.37 | 4.06 | 10.54 | 172.4 | 38.6 | inf | 485 | 0.3 | 1190 | 1544 | 11003 |
| 38 | 100 | 25.01 | 10.43 | 0.93 | 31.9 | 5.6 | inf | 170 | 0.9 | 1710 | 1460 | 10407 |
| 38 | 12.5 | 4.37 | 4.06 | 10.54 | 251.6 | 45.5 | inf | 1121 | 0.1 | 1808 | 1544 | 11003 |

Requirement (DERIVED): injector dP/Pc >= 0.25 everywhere. This is the ceiling rule; the minimum on the flight cycles is 0.50-0.83.

Chug:
- the gain margin is >= 4.7 at a 10 ms delay;
- the critical delay is infinite at every point;
- the pintle makes the floor the stiffest point.

Acoustics:
- 1L is about 1.5 kHz, Helmholtz 1.1-1.8 kHz and 1T about 10-11 kHz;
- all are far above the actuator band;
- the Pc sense line (>= 144 Hz) sits between the loop band and the acoustics.

Hybrid low-frequency modes:
- Thermal-lag and boundary-layer coupled modes fall in a 0.3-2 Hz band, which overlaps the slow plant mode (§3.4).
- Their amplitude is not predicted; the solid-phase response model is not included.
- Mitigation: the pre- and post-chambers, and a closed Pc loop with gain scheduling.
- Test requirement: T2 and T3 log Pc on the stand dynamic channel (>= 10-20 kHz with an anti-alias filter, flush mount or a characterised short sense line; LEAD line 172 (5)) at every throttle level. Logging at 1 kHz would alias the 1.1-1.8 kHz modes.

**v2.4: oxidiser-rich low-a points** (REV-GNC-1 RG-03; `oxrich_62m_v2p4.json` part C, same model as Table 8.1). Points: a x0.6 with n 0.5 and 0.68, ports 30 / 40 / 45 mm, 30-70 % thrust, 46 bar tank; reference a x1.0, n 0.5 at the same ports and thrusts.

| Case | O/F | dP/Pc | GM (tau 1 ms) | GM (tau 10 ms) | tau_crit | Thermal lag [s] | f thermal lag [Hz] | dc*/dO/F term k_c |
|---|---|---|---|---|---|---|---|---|
| a x0.6, n 0.5 and 0.68 (18 points) | 10.1-18.1 | 1.48-4.39 | 32.8-159.2 | 6.45-25.56 | inf | 0.38-3.34 | 0.048-0.42 | -0.106 to -0.119 where O/F < 14; unknown at the c* table clamp (11 points; 0 used) |
| a x1.0, n 0.5, reference (9 points) | 5.8-8.7 | 1.51-4.38 | 37.3-148.1 | 7.51-24.29 | inf | 0.15-0.78 | 0.20-1.04 | -0.03 to -0.10 |

- **Feed-coupled (chug) margins are unchanged:** the gain margin at a 10 ms delay is >= 6.4 and the critical delay is infinite at every point. The injector stays stiff (dP/Pc >= 1.48).
- **The low-frequency band moves lower.** At low a the solid thermal lag lengthens to 0.38-3.3 s, so the hybrid thermal-lag frequency falls to 0.05-0.42 Hz, against 0.2-1.0 Hz at a x1.0. That overlaps the slow plant mode and GNC's throttle commands more than the baseline does (§3.4).
- **c* slope.** k_c = d ln c*/d ln(O/F) is -0.106 to -0.119 at O/F 10-14, close to the reference at O/F 8.7 (-0.103) and steeper than near the optimum (-0.03 at O/F 5.8). The model includes it; above O/F 14, where the c* table is clamped, it is unknown.
- **Not modelled:** the Karabeyoglu-type coupled modes; their amplitude is not predicted.
- **Test requirement:** T2 and T3 log Pc on the stand dynamic channel (>= 10-20 kHz, anti-alias filter; LEAD line 172 (5)) at every throttle level. The oxidiser-rich regime is reached at T1 at 100 % (O/F 10.4) and in the second half of T4; low a itself cannot be commanded and is identified from the T1-T4 regression data.

## 9. N2O hazard list (v2.4)

Rows H1-H13 are the v2.3 rows with their v2.4 controls; H14-H19 are new. A control marked REQUIRED is a lead decision or a Combustion requirement. No control has been verified by test.

| # | Hazard | Mechanism and numbers | Control (v2.4) |
|---|---|---|---|
| H1 | Exothermic decomposition | N2O -> N2 + 1/2 O2 releases about 1.85 MJ/kg as gas, 1.60 MJ/kg from liquid (hf N2O(g) +82 kJ/mol, NIST, LITERATURE). Triggers: heat, adiabatic compression, catalytic surfaces, a hot cavity. Gas-phase induction at 46.45 bar (Cantera gri30, SIM): none within the run at <= 800 K, 43 s at 850 K, 8.0 s at 900 K, 0.46 s at 1000 K | No heat source upstream of the injector. No N2O-only flow through a hot torch (R-T1, §7.5). The purge path stays <= 424 K. REQUIRED: the wetted seat face <= 800 K from MECO to E1 (Mechanical FE, §9.1). Clean, PFPE-lubricated hardware only (§10.1) |
| H2 | Adiabatic compression on priming | A dead-ended line compressed by a fast valve reaches 847-913 K (N2) or 614-646 K (N2O vapour) at 45-60 bar (Table 2.7) | The MV opens with the pintle seated (v2.8); on an A1 relight it opens at PURGE, so the segment is swept before the lift. No fast-opening valve into a vapour-filled dead end |
| H3 | Trapped liquid (hydraulic lock) | Liquid between closed valves warms; a liquid-full segment rises 5.5 bar/K at 286.7 K (`safing_relief_v2p4.json`) | Relief on every lockable volume, set points and capacities in §2.7. Ground panel: every closed pair of valves gets a relief (§10.1) |
| H4 | Near-critical tank | Tc 36.4 C, Pc 72.5 bar; the 2.00 kg / 3.17 L tank is liquid-full above 33.5 C (68.0 bar) | Arm window 15-24 C at ARM (ENG-12 as amended); 24 C liquid-line interlock (§2.8) with the thresholds lowered by the channel uncertainty (guard band, §3.6); heater hard-disabled at ARM (§7.3); tank relief per §2.7; sun and heat shielding |
| H5 | Particles and galling debris | Particles are ignition sources; a particle on the seat is Mechanical's 77-82 mg/s fault leak | Filter <= 15 um at the head, and the inline <= 15 um element on the FD-01 bleed leg (F2, §2.8). H900 needle on an Inconel 718 seat (§3.5). Cleaning per §10.1. Seat inspection after B-PNT-1 |
| H6 | Material compatibility | Hydrocarbon greases and some elastomers are incompatible with oxidisers | PTFE, PCTFE, PFPE. Elastomers only where the maker rates them for N2O (TO-VERIFY per part). No silicone or hydrocarbon lubricants |
| H7 | Cold burns and embrittlement | Venting liquid reaches -88.5 C at 1 atm; a vented tank keeps cold liquid (§10.2) | Gloves and face shield. Seals and polymers rated for venting temperatures. Bleed vent overboard, away from people |
| H8 | Asphyxia and anaesthetic exposure | N2O displaces air and is an anaesthetic. Each A1 relight purge vents 34.3-72.9 g (§2.8) | Fill, vent and cold-flow outdoors or in ventilated areas; vent lines and catch-volume vents routed away from people |
| H9 | Pooled N2O in the chamber after a no-light | A later spark into pooled oxidiser causes a hard start | No retry into a pooled chamber. Ground: N2 purge >= 60 s at >= 10 g/s, then a hold of >= 15 min before approach with Pc at ambient and the head thermocouples falling, then safing (§7.6, §10.2; LEAD line 172 (1)). Inventories in §7.6: flight unignited inventory accepted 26.6 g; stand allowable 13.84 g with the aft DN32 disc and the rounded entrance |
| H10 | Seat leak during coast | Leaked liquid flashes and leaves vapour in the feed | MV closed during coasts. Seat acceptance <= 10 sccm GN2 at 56 bar; coast leak ceiling 0.0055 g/s (§3.5) |
| H11 | Over-pressure | Stuck-open pintle: MEOP basis 44.33 bar (§3.6); throat block below proof (§3.7) | MEOP 45 bar, proof 67.5 bar, software cap 25 bar; A4 at 30 bar abs on the filtered channel for 5 ms (§7.4; LEAD line 166 (4)); Pc transducer range >= 70 bar (ENG-09) |
| H12 | Combustion products | Fuel-rich exhaust and a smouldering grain release CO and nitrogen-containing species (ABS contains acrylonitrile); oxidiser-rich operation at low a (§4.6) | Remote operation. Treat the stand area as toxic until ventilated |
| H13 | Pressure-system failure | Hose whip; tank or fitting burst. Stored energy in §9.2 | Restrained hoses; proof testing per Mechanical; remote filling; exclusion zone set by the founders under local rules, informed by §9.2 |
| H14 | Late light at start or relight | Decomposition-only fast part: 43.7 bar (pad, 15 C, sharp entrance), 40.6 bar rounded; 37.8 bar at the A1 relight. Fuel-assisted fast part at a relight (FA-1 envelope): head 83.0-88.0 bar abs, above MEOP for <= 3.65-4.45 ms, never above 90 bar abs (§7.6) | Torch-first gate; rounded entrance REQUIRED; W per §7.3; LIGHT_SPIKE logging (lower bounds at 1 kHz in flight; the stand dynamic channel measures); FA-1 (a) and (b) REQUIRED; structural load per LEAD line 173 (§9.1) |
| H15 | Purge jets and vented N2O near the vehicle | 1.6-2.5 N per tap; 3.3-5.0 N if both taps vent one way; vent at -88.5 C; closure surge about 2.9 bar | Balanced (opposed pair) or axial vent, overboard, away from the nozzle, case and torch (LEAD) |
| H16 | Stuck-open bleed | 31.24 g/s with both taps liquid (upper bound), additive tank outflow | Two NC valves in series; drivers hardware-inhibited outside the purge window; ECU cap; A14; BLEED_FAULT to the FC (§9.1) |
| H17 | Bleed fails closed (no purge) | The segment keeps its coast vapour: P_abort 0.242 (LO) to 1.0 (HI, 51.8 cm3) at W 0.65 s (Table 2.15) | No commit by the plain trigger - 1.7 s -> no purge (LEAD line 175 (3), PROVISIONAL; the T_fire delay of line 164 is withdrawn). Proposal: no relight on that pass (H20) |
| H18 | Torch line: flashback, hot dead-ended N2O | §7.5 | R-T1 and R-T2 (§7.5); A8 |
| H19 | Hot-gas leak past the nozzle joint | An unsealed joint leaks 0.83-1.10 % of the engine flow; the 316L lip could melt in 1.07-5.70 s (lumped bound) (§6.5) | Seal layer of joint J1 (CONFIRMED, LEAD line 146); N2 pressure-decay leak check at 67.5 bar before and after every firing (criterion TO-DEFINE with Mechanical) |
| H20 (v2.4a) | Unpurged start after a missed PURGE commit or a fail-closed bleed (LEAD line 175 (3)) | PURGE NOT RUN LO worst: every light (P 0.758) is followed by a 23.4 cm3 vapour gap 0-0.19 s after E2; the drogue-release term is already true at E2, and A3 aborts in the gap: released, then A3, in 0.712 of starts (lined 0.819; population means 0.22-0.58) (§2.8, v2.4a; SIM/DERIVED) | Proposal: no relight on that pass (as A14). Research option: ride-through (release held on unpurged starts; torch kept on; A3 adapted) on CF-4 O-3 and IGN-1 evidence. The lead decides (OI-31). Line 181 (2): worst-state P(success) 0 under LO and under HI; Combustion recommends L* = 1.3 s (Table 2.17) |

### 9.1 Purge, stuck-open bleed and FA-1: FMEA input

**Purge exposure** (`purge_hazard_v2p4.json`, `ba24882f3ca956ba`; SIM and DERIVED):
- With PURGE at E0 - 2.90 s the MV is open with the pintle seated for 2.99-3.06 s before the light, against 0.09-0.16 s in the v2.8 sequence (19-34 times longer).
- The seat leak rate does not change, because the segment is at tank pressure through the coast via S1 either way. The purge adds 2.9-4.2 mg at the seat acceptance and 40-251 mg in Mechanical's fault leaks. No sustained light is possible from a leak (G_ox <= 0.17 kg/m2s against >= 25).
- The purge path stays <= 424 K. The open item is the stagnant annulus at the seat: the wetted seat face must stay <= 800 K from MECO to E1 (Mechanical FE; at 850 K the gas-phase induction time is 43 s, at 900 K 8.0 s).
- A pintle drift or runaway during PURGE is tank-fed for about 3 s. A15 monitors it and inhibits the torch. The lead accepted the exposure with the purge (line 160).

**Stuck-open bleed** (LEAD lines 160 and 164; GNC S313):
- 31.24 g/s with both taps liquid, 11.8 % of the 264.08 g/s at 100 % (upper bound); additive tank outflow governs.
- Open loop at 100 %: 0.70 bar more line loss on a dP_inj of 22.7 bar, so the injector flow falls by 1.54 %; at the ignition lift <= 0.09 %. In closed loop the Pc loop compensates.
- Detection: A14 (valve position or current signature, and closure not confirmed by the closure deadline, <= the torch gate, LEAD line 166 (3)), BLEED_FAULT to the FC (LOG-ONLY until a leak response is flown, LEAD line 168). Closure from P_mid is a pad go/no-go on every flight with the bleed fitted (line 168). FC_THRUST is not armed on A1 at this path until RG-16 is re-flown at about 31 g/s (line 168); the table below supports that re-fly.

**Vented mass against time on the decided path** (REV-GNC-2 RG-16; `purge_vented_mass_v2p4.json` `0038561f71a51502`, script `purge_vented_mass_v2p4.py`; SIM on ASSUMED Cd and slip brackets; unlined, 0 and 2 deg, 4320 records per time). The mass vented by a time t into the flow equals the total of a purge truncated at t, so the envelope at Tp = t is the vented-mass envelope at t. The full 0.1 s grid is in the file.

| Flow time [s] | Time from E0 [s] | Min [g] | Median [g] | p99 [g] | Max [g] |
|---|---|---|---|---|---|
| 0.5 | -2.05 | 3.2 | 9.7 | 11.9 | 11.9 |
| 1.0 | -1.55 | 5.9 | 21.8 | 27.1 | 27.2 |
| 1.5 | -1.05 | 9.6 | 30.6 | 42.4 | 42.5 |
| 1.9 | -0.65 | 19.5 | 41.0 | 54.6 | 54.7 |
| 2.0 | -0.55 | 21.9 | 42.7 | 57.7 | 57.8 |
| 2.5 | -0.05 | 34.3 | 56.6 | 72.5 | 72.9 |

- Before liquid reaches the taps, the minimum of the open-element bracket is the all-vapour line 8.49 t (g, with t in s) up to 1.0 s. The minimum of the barrier-element bracket lies below that line until 1.6 s (3.17 g at 0.5 s, 5.93 g at 1.0 s), because that model stalls the T4 tap behind a capillary barrier (bubble point about 0.7 kPa against 45.5 bar): a model construct that a real T4 will not reproduce (REV-COMB-2 R2-06; `vented_mass_brackets_v2p4a.json` `8e8ca9329c74a01f`). GNC flies the published table, which is conservative on the miss side (LEAD line 172 (8)); GNC rev2 reports that its RG-16 miss-side failure is not caused by these minima (line 174). The flow rate never exceeds 31.24 g/s.
- The maximum is not all-liquid flow from the start: every record starts with vapour, so the maximum is 11.9 g at 0.5 s and 72.9 g at 2.5 s, against 15.6 g and 78.1 g on the all-liquid line 31.24 t. The barrier minimum rises at about 5.5 g/s until liquid reaches the taps, then at about 25 g/s after 1.6 s. [v2.4 wording corrected per R2-06.]
- Closure: the close command leads the flow end by the measured valve closing time, so the 2.5 s already contains the closing transient. If the closing time is not subtracted, add at most 31.24 g/s x t_close (0.6-1.6 g for an ASSUMED 0.02-0.05 s). After a failed closure the flow continues at <= 31.24 g/s (B-2).

**FMEA rows for the bleed path** (occurrence values are not available; the founders and Electronics supply them from part data):

| ID | Failure | Effect | Detection | Control and owner |
|---|---|---|---|---|
| B-1 | One bleed valve stuck open | None while the other closes; the next fault is the stuck-open path | A14 at the closure check | Series pair; replace before flight (Electronics, founders) |
| B-2 | Both stuck open, or a common cause (driver, harness, software) | H16: 31.24 g/s additive outflow to landing | A14, BLEED_FAULT | Drivers hardware-inhibited outside the purge window; independent drivers (Electronics) |
| B-3 | One valve fails closed | No purge: H17 | Flow not seen (CF-4 P6 shows the signal; in flight, the closure signal and the P downstream of V2) | The series pair doubles this probability. No relight on that pass (LEAD line 164) |
| B-4 | Restrictor or FD-01 element partly blocked | Slower purge; the s 0.5 margin shrinks | CF-4 P4 and P5 on the ground; none in flight | Cleaning, filtering upstream of each restrictor; flow test of each restrictor (Mechanical, founders) |
| B-5 | Purge truncated by T_fire, or not committed | P_abort up to 0.098 at 1.8 s, 1.0 at 1.0 s (truncated-purge table, §2.8); without a purge see B-6 | FC timing | PURGE commits no later than the plain trigger - 1.7 s, so >= 1.9 s of flow fits with T_fire delayed by <= 0.6 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL; the T_fire delay of line 164 is withdrawn) |
| B-6 (v2.4a) | Unpurged relight (no commit by the plain trigger - 1.7 s, or no flow) | H20: in the PURGE NOT RUN LO worst state every light is followed by a 23.4 cm3 vapour gap after the drogue release; A3 aborts: released, then A3, in 0.712 of starts (§2.8, v2.4a) | None in time: the release term is true at E2, before the gap | Proposal: no relight on that pass (OI-31); the lead decides. L* = 1.3 s recommended (line 181 (2), Table 2.17) |
| B-7 (v2.4a) | Undetected flame-out after E2 with Pc invalid (R2 branch, line 181 (4)) | The open-loop lift keeps N2O flowing: cold-flow thrust <= 12.5-13.3 N at the start level and, by itself, above 37.16 N beyond about 200 N of command (bound; nominal 310-350 N); R2 may release a dead vehicle (§7.3, Table 7.3a; DERIVED) | None in the engine: A3 is blind without Pc | PROPOSAL: command hold at the start level while the drogue is attached; GNC re-flies R2 with the cold-flow term (OI-38) |

**FA-1: fuel-assisted fast part at an A1 relight (single-control hazard; LEAD lines 160 (4), 164 (8), 172 (2) and 173).**
- Hazard: the main N2O reaches the 32.2 mm port of the warm grain with no torch flame, accumulates and lights late. The fast part (1.2-2.1 g, vapour and spray in transit) burns with fuel vapour. Envelope over O/F 4-12 and burn times of 1-7 ms (v2.4a, §7.6): head peak 83.0 bar abs (baseline) to 88.0 bar abs (upper bracket), aft 0.95-1.00 of the head; above MEOP 45 bar for <= 3.65 ms (4.45 ms), above proof 67.5 bar for <= 1.0 ms (1.3 ms), never above 90 bar abs; thrust spike <= 1.77 kN, SDOF equivalent <= 3.05 kN. SIM on an ASSUMED construct (`fa1_envelope_v2p4a.json`); the fuel-vapour inventory at the light is MISSING.
- Single control: the torch-first gate (pintle lift only after E1, torch flame confirmed).
- Failure modes of the control: FM1 false torch confirmation (P_torch bias or drift; photodiode false positive); FM2 lift commanded before E1 (sequence or firmware fault); FM3 torch blown out or quenched by the main flow between E1 and E2; FM4 torch lit but not igniting the main flow promptly.
- Detection without (a) and (b): before the start, the P_torch auto-zero and the ARM refusal above 1.05 bar abs (gross bias only); at E1, 10 ms persistence; between E1 and E2, nothing. The 30 bar abort (filtered channel, 5 ms; LEAD line 166 (4)) and the comparator (RC 5.28 ms) cannot act within a 1-4 ms pulse. LIGHT_SPIKE records the event afterwards: evidence, not protection; at the 1 kHz flight logging its values are lower bounds (LEAD line 172 (5)).
- REQUIRED of Electronics (LEAD line 164): (a) E1 declared only on P_torch AND the photodiode (2oo2), which cuts FM1 and FM2 (FM2 is also covered by the firmware sequence checks in SIL); (b) torch supervision from E1 to E2, where loss on BOTH sensors for >= 5 ms closes the pintle and the MV. (b) bounds the unlit N2O to about 35-38 g/s x (5 ms detection + 20-100 ms closing), 0.9-4.0 g. That is comparable to the fast part itself: (b) limits the hazard but does not remove it (FM3, FM4). Nothing can detect the pulse in time to stop it. In flight, the (b) closure is an accepted mission loss in exchange for avoiding a pulse above proof.
- Severity: catastrophic if the case or closures fail; critical otherwise. Consequence (LEAD line 172 (2)): yield possible and ultimate not demonstrated until the line-177 actions close. Status (Mechanical lines 178-179, SIM/DERIVED at SF 1.0): TC-09 Inconel 718 in CAD v3.5; J-FWD A4-80 (yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar); the gimbal bearing selection OPEN (C0 >= 1.80 kN per bearing from a maker datasheet). Occurrence: unknown (no torch reliability data; photodiode false-positive rate unknown).
- Verification: IGN-1 with >= 30 lights, including photodiode false-positive tests and torch stability under the main N2O flow at the lift (blow-out margin); T4 relights with LIGHT_SPIKE logging to measure the real burn time and peak; Mechanical's margins against the line-173 load (90 bar abs quasi-static at head and aft; 92 / 102 bar abs for parts with periods of 0.25-1 ms; 1.8 kN x 4 ms thrust spike), reported in line 176.
- Status: accepted as a single-control hazard for design continuation only. Flight acceptance needs IGN-1 and Mechanical's margins against the line-173 load with the line-177 actions closed (LEAD lines 164, 170 (2), 173, 177).
- Owners: Electronics (a), (b) and the sequence checks; Combustion refines the bound with IGN-1 and T4 data; Mechanical the margins and the line-177 actions; the lead the acceptance.
- Research option (not proposed for adoption): a lower relight ignition lift shrinks the fast part in proportion to the flow at the lift, at the cost of the A3 margin. Hypothesis: a lift giving half the flow halves the fast part. Comparator: the 0.2039 mm lift. Evidence needed: IGN-1 showing FM3. Refutation: the A3 margin goes negative.

### 9.2 Stored energy (RC-05)

Basis (DERIVED; `safing_relief_v2p4.json` `33a95a70e8008e2e` and `stored_energy_sup_v2p4.json` `1b846c99f3145985`): decomposition energy 1.854 MJ/kg (gas) and 1.603 MJ/kg (liquid); TNT 4.184 MJ/kg; distance to 6.9 kPa side-on overpressure from the scaled distance 17.9 m/kg^(1/3) (LITERATURE as recalled, TO-VERIFY). Full decomposition of the whole mass is a bound, not an expected event. Expansion energy is the isentropic expansion of the contents (Brode form for the chamber gas).

| Inventory | Mass | Decomposition [kg TNT] / R(6.9 kPa) [m] | Expansion [kg TNT] / R [m] |
|---|---|---|---|
| Flight tank, 20 C | 2.00 kg | 0.774 / 16.4 | 0.030 / 5.6 |
| Flight tank, 35 C | 2.00 kg | 0.766 / 16.4 | 0.040 / 6.1 |
| A1 residual at landing, 20 C | 0.61 kg | 0.262 / 11.5 | 0.014 / 4.3 |
| Ground tank 15 L, 20 C | – | 4.01 / 28.4 | 0.154 / 9.6 |
| Valve-to-seat segment, liquid, A1 relight state (44 cm3; v3.4.1 is 10-14 % larger, R +3-5 %) | 36.5 g | 0.014 / 4.3 | 0.0005 / 1.4 |
| Flight unignited inventory accepted | 26.6 g | 0.010 / 3.9 | 0.0004 / 1.3 |
| Stand allowable (aft DN32 disc, rounded entrance) | 13.84 g | 0.005 / 3.1 | 0.0002 / 1.0 |
| Chamber gas at MEOP (Brode) | – | – | 0.0012 / 1.9 |

The founders set the exclusion zone under local rules; these distances are inputs to that decision, not the decision.

## 10. Cold-flow and static-fire test plan (v2.3 plan with the v2.4 amendments at the end)

Physical execution belongs to the founders. Combustion supplies the method, the measurands and the acceptance numbers. Every N2O test is remote, uses metal hardware, and vents into a back-pressured catch volume (LEAD rule).

| ID | Test | Hardware | Measured | Acceptance / use |
|---|---|---|---|---|
| CF-0 | PETG fit-check and low-pressure water visualisation | PETG copies of the pintle body, needle and head | Assembly, stroke and linkage kinematics; spray fan shape and symmetry against lift; gross leak paths; sensor port positions | Qualitative only (see the limits below) |
| CF-1 | Water cold flow, metal injector | Machined pintle, Coriolis or weigh tank | Single-phase Cd(h) at several dP; lift repeatability and hysteresis | Cd_liquid map; input to CF-3 |
| CF-2 | N2 flow and leak tests | Metal pintle and valves | Seat leak at 5 and 70 bar, before and after cycling and after a soak; full stroke with N2 at <= 3.5 MPa; filter and valve dP | Leak <= 1 scc/min N2 (proposed, TO-AGREE); valve Cv >= 3, filter Cv >= 2.2 |
| B-PNT-1 | Pintle bench (Mechanical/Electronics; combustion items listed) | Flight-like pintle and HV69 | F(h, P) at 3.5 / 5.5 / 7.0 MPa (N2, then N2O) by load cell or servo current; break-out after a dwell closed at MEOP; closing time at 25 bar and MEOP; guide friction; HV69 travel >= 103 deg; unpowered spring closing at the MEOP-equivalent needle load | C2 >= 1.5 under the measured law; C1 >= 0; ENG-05 tail-off re-run with the measured closing curve |
| CF-3 | N2O cold flow into a back-pressured catch volume | Metal injector, flight valve, filter and hose | mdot(h, P_tank, T) at 15 / 20 / 25 C with back-pressure 1-25 bar; feed pressure oscillations; line temperature during priming | Cd_eff against Dyer >= 0.41; maps re-run with the measured Cd |
| IGN-1 | Torch bench | Torch, solenoids, check valves | Orifice flows by weighing at 10 / 20 / 25 C; spark reliability; flame-confirmation sensor; latency and its scatter over a series (proposed >= 30 lights, ASSUMED sample size); torch body temperature over 30 s at Pc | Zero no-lights in the series; latency scatter within +/-50 ms |
| T1 | Short static fire, 3-5 s at 50-100 % | Flight-like engine on a stand with a 6-axis balance or two load cells | Pc on the stand dynamic channel (>= 10-20 kHz, LEAD line 172 (5)) and the 1 kHz control channel, F, roll torque (resolution well below 0.02 N m), thrust misalignment, mdot_ox (tank load cell), grain mass and bore before and after, throat bore, thermocouples (face-disc back, head top, bracket foot, servo case, post-chamber case, retainer) | First (a, n) and eta_c* point; RCS decision (LEAD: delete only if roll torque <= 0.02 N m); head-end BC replaced by measurement |
| T2 | Throttle steps 100 -> 50 -> 25 % | As T1 | Plant K_h and tau; low-frequency modes; regression at several fluxes | (a, n) band; Pc-loop tuning |
| T3 | Floor holds at 20 % and 12.5 % | As T1 | Combustion efficiency and stability at G_ox 25-74 kg/m2s; lip separation and side load; Isp | Stretch floor accepted or rejected |
| T4 | Duty cycle with coasts and relights (DC-D: 3 starts, grain split into 3 loads; DC-C into 2) | As T1 | Relight latency, soak temperatures, erosion per cycle | Erosion and life rule; TS-1 and TS-2 data |

What a PETG cold-flow part can and cannot do:
- It can:
  - check fit, stroke and linkage kinematics before metal is cut;
  - show the spray-fan shape and symmetry against lift with water at a few bar at room temperature;
  - check sensor and port positions;
  - check how the parts are handled.
- It cannot:
  - carry N2O at all (oxidiser compatibility, ignition hazard);
  - represent flashing two-phase flow;
  - survive the -88.5 C venting temperature or the 45-70 bar pressures;
  - stand in for the metal seat in leak or break-out tests;
  - give an acceptance Cd, because its surface finish, sharp edges and land differ from the machined part;
  - stand in for the metal under force-versus-lift loads, because it bends and creeps;
  - represent any thermal or combustion behaviour.

**v2.4 amendments to the test plan.**
- **All N2O tests:** remote, metal hardware, into a back-pressured catch volume with its own relief and vent (§10.1). Water tests are followed by drying, re-cleaning and an N2 leak check before any N2O (§10.1).
- **CF-2:** the leak acceptance is now the lead's (§3.5): B-PNT-1 seat <= 10 sccm GN2 at 56 bar at room temperature and after a 150 C soak; stem seal <= 1 sccm; MV-P seat Class VI at 56 and 84.2 bar (room temperature and 60 C). The v2.3 "<= 1 scc/min (proposed)" is superseded.
- **CF-4 (new): relight purge cold flow.** The gate for the W 0.65 s relight claim (LEAD lines 160 and 164). The full specification is the standalone `02-combustion/CF-4-SPEC.md`; the summary is §10.3.
- **IGN-1:** >= 30 lights including photodiode false-positive tests (LEAD line 164); torch stability under the main N2O flow at the ignition lift (blow-out margin, FA-1 FM3); the three E0 -> E1 delays (the 0.16 s gate stands if the measured p99.9 is <= 0.15 s); T_lim for SOL1. v2.4a: Pc and P_torch on the stand dynamic channel (>= 10-20 kHz, LEAD line 172 (5)), so that 1-3 ms spikes are resolved; flight LIGHT_SPIKE values at 1 kHz are lower bounds.
- **T1:** LIGHT_SPIKE logging at every start; the nozzle-joint N2 leak check at 67.5 bar before and after (H19); lip thermocouples (§6.5); Pc transducer >= 70 bar.
- **T4:** relights with the flight PURGE sequence: vented mass per purge, line state at the lift, latency, and LIGHT_SPIKE (FA-1 burn time and peak).

**v2.4a amendments to the test plan** (REV-COMB-2; LEAD line 172).
- **Stand dynamic Pc channel (LEAD line 172 (5); R2-10):** IGN-1 and T1-T3 log Pc (and P_torch at IGN-1) at >= 10-20 kHz behind an anti-alias filter, with a flush-mounted transducer or a characterised short sense line (resonance measured), and a range >= 100 bar abs to cover the FA-1 envelope. The 1 kHz control channel aliases the 1.1-1.8 kHz modes and under-reads 1-3 ms spikes; flight LIGHT_SPIKE values logged at 1 kHz are lower bounds.
- **CF-1 and CF-3 acceptance (LEAD line 172 (4); R2-07):** full-stroke Cd <= 0.80, and a line loss at the failure flow (about 0.38 kg/s) >= the modelled value; otherwise MEOP is restated (§3.6).
- **Stand safing after a no-light (LEAD line 172 (1)):** the one rule of §10.2.
- **CF-4 v2.0:** 3 deg runs, per-tap flow, P4 per tap and per phase, P6 per line 166 (3), optional run O-3 (§10.3).
- **T1-T4:** specification v2 (§10.4): law stations x/L 0.80-0.90, the T3 holds at 20 % and 12.5 % as the law firings, repeats to σ(S) <= 1.5 %, N2 quench, witness sectioning, a density map.
- **Cold-flow thrust (LEAD line 181 (4); OI-38):** CF-3 adds a thrust load cell and logs the cold-flow thrust at the start-level (about 0.22 mm), 200 N and 500 N lifts (cold chamber). The T series adds, at the end of one firing, a short N2O pulse at the start-level lift with the igniter off (hot chamber); it measures the thrust and shows whether the grain re-ignites. Safing per §10.2.

### 10.1 Cleaning, drying and catch volumes (RC-14)

- **Cleaning standard.** Every N2O-wetted part is cleaned and verified for oxygen service per ASTM G93/G93M with CGA G-4.1 as the procedure reference (LITERATURE as recalled, TO-VERIFY against the current editions). Proposed acceptance: particulate and non-volatile residue levels per IEST-STD-CC1246 as referenced by G93, proposed level 100A (as recalled, TO-VERIFY; the founders confirm with the cleaning supplier).
- **Inspection.** White light and UV (black-light) inspection of every wetted surface for hydrocarbon fluorescence and particles; a solvent-rinse NVR and particle-count sample per cleaning batch; parts bagged and capped until assembly; cleaning records kept per part.
- **Water before N2O (CF-1 to CF-3, and CF-0 parts never reused).** After any water test: drain; blow down with dry N2; dry with heated N2 or vacuum until the outlet dew point is <= -40 C (ASSUMED criterion); re-clean per the standard if the water carried additives, dye or particles; then an N2 leak check (CF-2 criteria) before the first N2O.
- **Catch volumes** (CF-3, CF-4 and any back-pressured volume): a relief valve set at or below the volume's MAWP, with capacity for the largest test inflow as vapour at the set pressure (264 g/s for CF-3 at 100 %, 31.24 g/s for the CF-4 bleed path, plus the pintle flow at the lift); a burst disc as the second device; a remote vent valve; the vent routed outdoors away from people; oxygen-clean; no hydrocarbon lubricants. Stand-specific values belong to the founders' panel design.

### 10.2 Safing after a test, a no-light or a landing

- **No-light or abort on the stand** (LEAD line 172 (1), the one rule): no retry into a pooled chamber; N2 purge of the chamber >= 60 s at >= 10 g/s; then a hold of >= 15 min before anyone approaches, with Pc at ambient and the head thermocouples falling; then the post-test procedure. The v2.3 "wait >= 5 s" is withdrawn everywhere (§7.6).
- **Post-test:** MV and torch isolation closed; tank vented remotely; the segment drained through the bleed path or by its relief.
- **Tank vent times** (`safing_vent_v2p4.json` `ccc94365e1c8e737`; DERIVED, CoolProp blow-down through a top vent, Cd 0.80 ASSUMED, vent-line losses not included). Full 2.00 kg load at 20 C (50.5 bar): to 11 bar in 148-204 s through 1.0 mm, 37-49 s through 2.0 mm, 16-22 s through 3.0 mm. A1 landing residual 0.61 kg: to 11 bar in 70-91 s (1.0 mm), 18-23 s (2.0 mm), 8-10 s (3.0 mm).
- **A vented tank is not empty.** The adiabatic bound ends at about 1.2 bar with 0.92 kg (full load) or 0.13 kg (A1 residual) of liquid at about -86 C; with wall heating the full load still holds 0.49-0.54 kg at 1.2 bar through 2-3 mm vents; only the 1.0 mm vent ends nearly empty (0.01 kg after 1660 s), and the A1 residual ends at 0.007-0.009 kg. Treat the tank as holding cold liquid N2O until its mass or temperature shows otherwise (H7).
- **Flight, post-landing:** torch isolation closed and the remote vent armed (§7.4).

### 10.3 CF-4 summary (full text in `CF-4-SPEC.md` v2.0)

- **Claim under test (C-RL).** On CAD v3.4.1 with the decided purge path and 2.5 s of flow ending 0.05 s before E0, at theta <= 2 deg, an A1 relight lights within W 0.65 s with P_abort <= 1e-3, venting <= 76 g.
- **Hardware.** The metal, flight-equivalent segment from the MV-P seat to the pintle seat, with the flight bleed path as built (two 0.707 mm restrictors, the FD-01 inline element, V1 and V2, the -2 line, the vent), the flight MV-P and pintle drive under the flight firmware's PURGE sequence (HIL), a 0 / 2 / 3 deg tilt fixture (v2.0), per-tap flow instruments and a tank-outlet probe.
- **States.** IS-1 vapour-full (HI bound), IS-2 ARM-LO-like, IS-3 liquid-primed reference; >= 5 runs per state and attitude.
- **Pass criteria P1-P7.** P1 first continuous liquid at the pintle inlet <= 0.293 s after the pintle reaches the lift; P2 then >= 0.35 s of continuous liquid, or a later void inside Table 10.4; P3 the cap clears the FD-01 crown <= 2.3 s after the flow starts; P4 each tap >= 80 % of the model flow, per tap and per phase (vapour, then liquid), against the open-element reading (the barrier reading's T4 stall is a model construct and cannot pass or fail P4); P5 <= 76 g vented from IS-1 and IS-2, read against the vented-mass brackets; P6 (a) the flow stopped by E0 - 0.05 s, (b) closure confirmed (V1 first, on P_mid) by the closure deadline <= the torch gate (E0 + 0.15 s), (c) with one valve held open, BLEED_FAULT at the deadline, then V2 commanded closed and the lift (flight build) or an abort (stand build) (LEAD line 166 (3)); P7 no unfiltered path from the FD-01 tap to the seat.
- **v2.0 changes (v2.4a).** Tilt runs at 0, 2 and 3 deg (GNC rev2's 2.71 deg specific-force angle; 4 deg sensitivity); per-tap flow channels and a tank-outlet probe; P4 per tap and per phase; P5 against the vented-mass brackets; P6 per LEAD line 166 (3); optional run O-3, an unpurged start, which tests the post-light vapour gap of §2.8 (a sequence with no gap after the first slug refutes the finding for that state). CF-4 tests the purge, not the commit rule.

Table 10.4. Largest acceptable second void C1 [cm3] after a first pocket P1 and a liquid slug S1, both in cm3 (`cf4_void_budget_v2p4.json`, `6c294cf2dec7af5d`; worst of the "paused" and "restart" conventions). 0 means no second void is acceptable; "none" means no limit below 80 cm3.

| P1 \ S1 | 2.5 | 5 | 10 | >= 15 |
|---|---|---|---|---|
| 0 | 15.3 | 11.6 | 4.2 | none |
| 2.5 | 12.8 | 9.1 | 1.7 | none |
| 5 | 10.3 | 6.6 | 0 | none |
| 7.5 | 7.8 | 4.1 | 0 | none |
| 10 | 5.3 | 1.6 | 0 | none |
| 12.5 | 2.8 | 0 | 0 | none |
| 15 | 0.3 | 0 | 0 | none |
| 17.5 | 0 | 0 | 0 | none |

### 10.4 Regression-rate measurement at T1-T4 and the law form (RG-03; specification v2)

The full text is `02-combustion/T1-T4-REGRESSION-SPEC.md` v2 (REV-COMB-2 R2-04; LEAD line 172 (3)); the computation is `t1t4_law_resolution_v2p4a.json` (`05b5ae5c20e04bd8`; DERIVED from published SIM histories, no grain re-run). The v2.4 text of this section is superseded: its law decision could not resolve the signature at T1, and it defaulted to the less safe gate when nothing was detected.

- **Burden of proof reversed (LEAD line 172 (3)).** The B1 gate is "current rule OR a_meas >= 1.25 -> change the grain" by default. It is relaxed only if the oxidiser-flux law is positively shown at σ(S) <= 1.5 %.
- **Law stations.** x/L 0.80, 0.85 and 0.90 against the head reference x/L 0.10 (x/L 0.30 if the spray check fails). a_meas stays at x/L 0.97 for the gate (REQUIREMENTS line 117).
- **Signature.** S = r(0.85)/r(0.10) over a 0.6-1.5 and n 0.35-0.68: 1.014-1.072 at T1 100 %; 1.037-1.135 on the T3 holds at 20 % and 12.5 %. At a x1.0 the probability of showing the oxidiser-flux law at σ 1.5 % is 0.47-0.95 at T1 and 0.99-1.00 on the T3 holds, which carry the decision.
- **σ target and repeats.** σ(S) <= 1.5 %; N = ceil(s1^2 / (0.015^2 - s_s^2)) repeats for a single-firing scatter s1 and a residual systematic term s_s (both ASSUMED bands until measured). A practical count (N <= 8) needs s_s <= 1.0 %.
- **Systematic terms** with ASSUMED residual targets: post-shutdown melt and soak-back (N2 quench; two-duration differential), the char and melt layer (witness sectioning), ovality (>= 4 diameters), the print density along x (density map), start and tail-off transients, head-end spray, aft-end flow, station position.
- **Errs safe (DERIVED; 78 B1 grain_q1d records: 30 on the 85 m band, 48 on the 62 m records; O/F down to 1.78).** Under a total-flux truth the gate keeps its 10 % allowance only if ρ = E_B1 / E_cal <= 1. A T1-only calibration gives ρ_max 1.068 (3.0 % of the allowance left). With a T3 hold, ρ_max is 1.004 (9.6 % left) at 20 % and 0.990 (11.2 %) at 12.5 %. Proposal for the lead: a_meas,gate = max(1, ρ_max) x a_meas whenever the oxidiser-flux law is not shown; a calibration set with a T3 hold makes the correction negligible.
- **Measurements.** Grain mass (<= 0.1 g, dried); >= 4 diameters per station (bore gauge <= 0.02 mm, or a 3-D scan) at x/L 0.10, 0.30, 0.50, 0.70, 0.80, 0.85, 0.90 and 0.97; Pc on the stand dynamic channel and the control channel; the oxidiser flow from the load cell and P_feed; the N2 quench at shutdown; witness sectioning; a density map of the printed grain.
- The burn limit for GNC is recomputed with 1.1 x a_meas and the declared law form (§4.6). O/F is not a gnc.json quantity: the B1 O/F histories come from Combustion's grain model run on the gnc.json duty cycles.
- **Limits.** The analytic signature model reproduces the grain_q1d record on DC-D to about 0.5 % (E at x/L 0.97 1.0607 against 1.0664; web 14.25 against 14.24 mm; regression-weighted O/F 8.37 against 8.17). A first pass of the computation read the wrong DC-D file, counted start rows as run rows, let the analytic model burn past burn-through and counted the 62 m records in the 85 m group; all were corrected before any value was used (§13).

## 11. Unknowns

Each unknown is listed with the test that closes it.

1. N2O/ABS regression law (a, n) and its band: T1-T2.
2. Pintle Cd for two-phase N2O at every lift: CF-1 water, then CF-3 N2O. Acceptance Cd_eff >= 0.41.
3. eta_c* of the straight port at O/F 4-10 (assumed 0.92, band 0.85-0.96), including the 1-2 % liquid-N2O c* penalty: T1-T2.
4. Low-flux combustion at the 12.5 % stretch floor (G_ox about 25-74 kg/m2s): T3.
5. Ignition delay with the torch (assumed 0.10 s torch-to-main plus 30 % preheat): IGN-1, T1.
6. Graphite grade, density and erosion kinetics: bore measurement after each firing.
7. Residual roll torque and thrust misalignment of the straight port: T1.
8. Plume afterburning and radiation: the CFD gives fast-chemistry bounds only (05-plume-cfd).
9. Head-end gas temperature and heat transfer. The bound uses T_aw = T0 and Bartz outside its validity: T1 thermocouples.
10. Pintle closing time under load at 25 bar and at MEOP: B-PNT-1.
11. Needle pressure force against lift (L0-L2 differ by up to 163.9 N at MEOP): B-PNT-1 with N2, then N2O.
12. Seat friction, break-out after a dwell at MEOP, and leak rate: B-PNT-1 and CF-2.
13. N2O transport properties (CO2 surrogate) in the tank heat-transfer closure, and the tank enhancement factor E: tank pressure history in T1-T4.
14. PETG regression law and grain design: only if the backup is used.

v2.4 additions:

15. Cap transport (slip) in the bleed path, the restrictor Cd and the hump sweep: CF-4.
16. Whether the wet or dry reading of the coast vapour generation holds: CF-4 optional generation runs.
17. The real late-light burn time and fuel fraction (FA-1): T4 with LIGHT_SPIKE logging. v2.4a: also IGN-1 on the stand dynamic Pc channel.
18. Torch reliability, blow-out margin under the main flow and photodiode false-positive rate: IGN-1.
19. The wetted seat-face temperature from MECO to E1 (<= 800 K required): Mechanical FE, then T4 thermocouples.
20. The FD-01 element's dP-flow curve (Cd.A >= 0.63 mm2 keeps the margin): Mechanical, then CF-4.
21. Tank outlet coverage from the PURGE command (§2.4 notes): covered quasi-statically if the outlet is on the aft bulkhead of an axial tank (v2.4a); the outlet geometry (Mechanical, CAD), the slosh amplitude and the 500-run specific-force angle (GNC) are MISSING; then flight data.
22. Joint materials at temperature (carbon-phenolic char rate and strength, graphite seal): Mechanical FE re-run, T1 sectioning.
23. Throat erosion kinetics in oxidiser-rich exhaust at low a: T1-T4 bore data.
24. The tail-off rows of §3.7 on the v3.4.1 segment (+10-14 %): not re-run; expected small.
25. The fuel-vapour inventory in the warm 32.2 mm port at the moment of an A1 light (FA-1 basis; MISSING): IGN-1 and T4 on the stand dynamic Pc channel.
26. The FA-1 wave peaks along the port and the equilibrium outflow (R2-11): a 1-D gas-dynamic run of the worst row (Combustion, OI-36).
27. Whether a light inside a liquid slug survives the vapour gap that follows it (unpurged start, H20): CF-4 optional run O-3, IGN-1.
28. The purge at the 2.7 deg specific-force angle of GNC rev2 against the 2 deg basis: Combustion model run (OI-35), then CF-4 at 3 deg.
29. The total channel uncertainty of T_tank and P_tank behind the interlock guard band: Electronics, then CF-1 / CF-3.
30. The single-firing scatter s1 and the residual systematic term s_s of the law signature: T1-T3 repeats (T1-T4 specification v2).
31. The cold-flow thrust after a flame-out, cold and with a hot chamber, grain and nozzle (heat pick-up MISSING): CF-3 with a load cell; a post-burn N2O pulse in the T series (§10, v2.4a).
32. Which end of the wall heat-transfer bracket (LO or HI) governs the coast flashing in the segment: CF-4 optional generation runs, T4.

## 12. Open items with owners (v2.4, updated in v2.4a)

Status of the v2.3 items:

| ID | Item | v2.4 status | Owner |
|---|---|---|---|
| OI-1 | N2O load against the GNC cycles | Closed by the lead: A2 removed, B1 capped at 85 m; gnc.json v3 published (`3e97c378cfebee95`) | Lead |
| OI-2 | Engine map in the GNC Monte Carlo | Open: GNC flies the v3 records; the RG-01 re-fly uses the §2.8 line states | GNC |
| OI-3 | Grain in CAD | Open: confirm S230 in CAD v3.4.1 and the mass budget | Mechanical |
| OI-4, OI-5 | Post-chamber insulator; insert retention lip | Open: thermal FEA; the nozzle joint adds H19 and joint J1, CONFIRMED by line 146 (§6.5) | Mechanical |
| OI-6 | Pc transducer | Range >= 70 bar per ENG-09 (RC-13 d) | Electronics |
| OI-7 | Valve and filter | MV-P Cv 3.6 baseline; filter <= 15 um; FD-01 inline element added (F2) | Mechanical |
| OI-8 | ECU sequence | v2.8 in SIL; v2.4 changes listed below | Electronics |
| OI-9 | Roll torque | Open: T1 | Founders |
| OI-10 | Residual web | Superseded by §4.6 and the lead's B1 gating rule | Lead, GNC |
| OI-11, OI-14 | Pintle force and spring; ENG-05 shutdown | Resolved (v2.3) | – |
| OI-12 | Relight precondition "purged" | In v2.4 "PURGE" is the forced bleed purge of an A1 relight (§2.8); the ground N2 chamber purge stays a ground step | – |
| OI-13 | Deadband and resolution | Open: bench with the measured plant | Electronics, Mechanical |
| OI-15 | Servo thermal | Open: FEA and T1 thermocouples | Mechanical |
| internal | Relight text "the isolation valve may stay open between burns" | Corrected: `igniter.sequence` v2.4 keeps the MV closed in coasts | – |

v2.4 items:

| ID | Item | Need | Owner |
|---|---|---|---|
| OI-16 | FA-1 | (a) 2oo2 E1 and (b) torch supervision, REQUIRED; sequence checks in SIL | Electronics |
| OI-17 | FA-1 load | Margins against the line-173 load (90 bar abs quasi-static at head and aft for every part; 92 / 102 bar abs for parts with periods of 0.25-1 ms; 1.8 kN x 4 ms): reported in line 176. Line-177 actions: TC-09 Inconel 718 in CAD v3.5 (line 178) and J-FWD A4-80 (line 179) done on paper; open: the gimbal bearing selection (C0 >= 1.80 kN per bearing from a maker datasheet) | Mechanical |
| OI-18 | Abort matrix changes | A5 deleted and the LIGHT_SPIKE record; A4 at 30 bar abs on the filtered channel for 5 ms (line 166 (4)); the E1 closure term and A14 per line 166 (3); A7 bands and the flight START high-side rule; A14-A16 | Electronics |
| OI-19 | Bleed control | Closure signal behind BLEED_FAULT; ECU cap = 2.5 s of flow plus the measured valve times; drivers hardware-inhibited outside the window; 12 V NC valves with >= 4x capacity, mass target <= 0.15 kg each (2 x 0.30 kg is a MASS RISK); price TO-QUOTE (Sønderborg DK-6400) | Electronics |
| OI-20 | FD-01 element | Measured dP-flow curve; Cd.A < 0.63 mm2 triggers the two-flow re-run (about 20 min) | Mechanical, then Combustion |
| OI-21 | Seat face | <= 800 K from MECO to E1 in the FE (line 179: base case < 800 K; adiabatic case OPEN) | Mechanical |
| OI-22 | Nozzle joint | J1 CONFIRMED (line 146); FE re-run with the two-layer stack; the 316L lip at about 342 C against the 10.6 MPa bearing; leak criterion | Mechanical, Combustion |
| OI-23 | RG-01 re-fly | Fly the PURGED tables (Table 2.15) from the pinned hub copies `02-combustion/data/v2p4/` (HASHES.txt), the purge at the ECU cap (<= 73.0 g, line 168) and the vented mass against time (§9.1), PURGE committed at E0 - 2.90 s; one flight FSW for every base and arm (line 168); the height cost of the PURGE commit timing (the T_fire delay rule of line 164 is withdrawn by line 175 (3)); the +0.60 kg valve-mass sensitivity; tank outlet coverage from PURGE (§2.4; v2.4a screening done; the 500-run angle and slosh remain). Status: re-flown in GNC rev2 (line 174, SIM, staged), under REV-GNC-3 | GNC |
| OI-24 | Gates | CF-4 (relight claim), IGN-1 (>= 30 lights), B-PNT-1, CF-1 to CF-3, T1-T4 | Founders |
| OI-25 | Material data (RC-15) | 17-4PH H900/H1150 Fty and hot strength (maker data or MMPDS); Inconel 718 TC-03; PTFE rod-seal temperature in the FEA | Mechanical, Combustion |
| OI-26 | Interface hygiene (RC-20) | Tags added to `props_100pct` and `props_12p5pct` in combustion.json v2.4; gnc.json v3 now published | Done |
| OI-27 | HANDBACK-SUMMARY lines 79-80 | Done (line 170); the remaining wording (R2-12) was done by the lead (line 172 (7)) | Done |
| OI-28 | ENG-01 at the 25 bar cap (RC-09) | Decided (line 170 (1)): the 25 bar software cap stays; at the eta_cf low end the rated thrust is about 487 N at 25 bar; T1 measures eta_cf, and the measured k feeds GNC's cap rule | Decided; T1 |
| OI-29 | Regression law form (RG-03) | Specification v2 (§10.4): reversed burden (line 172 (3)), law stations x/L 0.80-0.90, σ(S) <= 1.5 %, T3 holds, systematic terms; errs-safe correction proposed | Founders, Combustion; lead (correction) |
| OI-30 | Bleed-size comparator | Optional: two taps at about 20 g/s total (2 x 0.57 mm) through the purge sweep, if the FMEA cannot bound the stuck-open probability | Combustion (offered) |
| OI-31 | PURGE commit rule (H20) | Line 175 (3) is PROVISIONAL; Combustion's check refutes "the relight proceeds unpurged" (§2.8, v2.4a). Decide: no relight on that pass, or a ride-through mode on evidence. Line 181 (2): LO/HI not settled; worst-state P(success) 0 under both; Combustion recommends L* = 1.3 s and, below it, no unpurged relight unless a release hold on unpurged starts (>= E2 + 0.22 s) gains P (Table 2.17) | Lead (GNC, Combustion) |
| OI-32 | Tank outlet | Outlet position and diameter, dip tube or sump, anti-vortex device, orientation and bulkhead face in CAD; a slosh bound; the 500-run specific-force angle during PURGE | Mechanical, GNC |
| OI-33 | Interlock guard band | Total channel uncertainty of T_tank and P_tank; thresholds lowered by it; CF-1 / CF-3 acceptance (Cd <= 0.80, line loss >= model) | Electronics, founders |
| OI-34 | Stand dynamic Pc channel | >= 10-20 kHz, anti-alias filter, flush mount or a characterised short sense line, range >= 100 bar abs, for IGN-1 and T1-T3; price TO-QUOTE (Sønderborg DK-6400) | Electronics, founders |
| OI-35 | Purge at 2.7 deg | Re-run the decided-path purge at the GNC rev2 specific-force angle (2.71 deg raw) and at 3 deg; CF-4 v2.0 adds 3 deg | Combustion |
| OI-36 | FA-1 model form | A 1-D gas-dynamic run of the worst FA-1 row (R2-11) | Combustion |
| OI-37 | Interface configuration (R2-13) | mechanical.json v2.1 (line 179) adds the bleed topology and the FA-1 per-part tables, but has no MEOP, MAWP or rounded-entrance keys and quotes the tank relief as <= 7.5 MPa; electronics.json v2 (as reviewed) shows A5 OPEN, the 2.0 s hold and the Burkert 6027 HP | Lead |
| OI-38 | Cold-flow thrust and R2 (line 181 (4)) | GNC adds F_cold(lift, P_tank) (`cold_flow_thrust_v2p4a.csv`) to the sim6 V flame-out case, records the command trace there and re-flies R2 with the command hold at the start level; CF-3 load-cell measurement; post-burn N2O pulse (T series) | GNC, lead; founders (tests); Combustion (model) |
| OI-39 | J1 seal material (line 182 (4)) | NZ-04 flexible graphite FAIL at the 577 C soak until a datasheet shows >= 627 C; Mechanical re-checks the joint with a datasheet-rated seal; the §6.5 hot-layer inputs are unchanged | Mechanical |
| OI-40 | NZ-01 acceptance criterion (line 183 (2)) | "Throat-area change > 2 %" is below the erosion expected in one A1 flight (1.9-13.6 %, §5.4); proposal: > 2 % beyond the expected erosion, a non-axisymmetric step or a missing fragment | Lead; Mechanical; founders (inspection) |

## 13. Failures and superseded evidence

All of these are kept as evidence.

| Item | What happened | Consequence |
|---|---|---|
| v1 helical grain (L 200) | Burned through on B1: web -3.12 mm at 15.0 s; also a roll-torque source | S230 straight port (LEAD) |
| eps 3 nozzle | Separates at <= 20 %; side-load bound 3.5-11.2 N | eps 2.0 |
| Mechanical pintle force law v2-v2.2 | Unconservative for opening: the closing pressure force persists while the gap meters | S3 failed C2 under L1 (1.28-1.47); rolling guide adopted |
| First pintle force answer | Used the v2 spring before the S3 baseline change | Recomputed on S3; failure reported to the lead and Mechanical |
| Pintle full-stroke 0.08 s | Carried from the v1 ENG-03 target; no combustion basis | Retired in v2.2; drive sized by the GNC v2 requirements and ENG-05 |
| actuator_rate_check_v2 run 1 | Start rule tested against the 2500 N/s cap instead of the >= 1000 N/s requirement | Patched analytically; run-1 file kept |
| headend_thermal_v2 run 1 | No re-radiation and a one-way joint gave an unphysical case node of 670-1890 K | v2.2b supersedes it; file kept |
| A1 x0.6 O/F | Cumulative O/F 15.9 beyond the O/F 14 c* table clamp | Values approximate; flagged |
| CoolProp transport | No N2O viscosity or conductivity model | CO2 surrogate (ASSUMED) |
| Early interface-writer drafts | Hand-typed numbers | Every value now computed from data, with asserts |

v2.4 failures and superseded evidence (kept; superseded runs in `data/v2/v2p4/superseded/` with `SUPERSEDED.txt`):

| Item | What happened | Consequence |
|---|---|---|
| §2.8 on the CAD v3.4 inverted U (44 cm3) | The hardware changed (re-route, CAD v3.4.1) | Text kept as `superseded/s2_8_v34_inverted_U.txt`; segment-void and pre-void-fix runs superseded |
| Late-light 44.9 bar (v2.4 draft) and the 37.1-44.9 bar table | Single-case run before the full grid | Tables 7.4 and 7.5 (43.7 bar sharp, 40.6 bar rounded at 15 C) |
| Fuel-assisted 72.8 / 62.9 bar (draft) | Run 1 at 20 C and the A1 relight only | 48.9-75.5 bar at 1 ms (run 2, full grid); FA-1 |
| A5 (Pc > 8.0 bar for 5 ms from E1) | Tripped on 98 % of the late-light grid | Deleted (LEAD line 160); LIGHT_SPIKE |
| "About 50 g" per purge; 0.8 mm per tap; PURGE at E0 - 2.40 s | Coarse-grid and Tp 2.0 drafts | Decided path, 34.3-72.9 g at 2.5 s, E0 - 2.90 s (LEAD lines 160, 164) |
| Purge reduction, first run | The trade's "restart" convention added 0.023 s of dead time to single-pocket sequences: E0 -> E2 max 0.649 s | Corrected to 0.626 s; two non-governing brackets moved (s 1.0 unlined 1.2 -> 1.1 s; swall lined 1.3 -> 1.2 s); governing times unchanged |
| PTFE lining (research) | Refuted as a replacement for the purge; costs 0.3 s of margin | Dropped (LEAD line 164) |
| ECU cap 2.5 + 0.3 s | Placeholder | 2.5 s of flow plus measured valve times (LEAD line 164) |
| Mechanical's 15.91 cm3 | A 10 deg robustness row read as the design case | 4.84 cm3 at theta <= 2 deg, reproduced; closed (line 162) |
| v2.3 MEOP basis 42.85 bar | Non-conservative line loss and eta_c* (RC-08) | 44.33 bar (§3.6) |
| v2.3 hard-start inventory 8.74 g and coast leak ceiling 0.039 g/s | Understated (RC-02) | §7.6 inventories; ceiling 0.0055 g/s |
| v2.3 throat life "1.0-4.3 A1 flights" | Not supported on the v2 cycles (RC-06) | One insert per flight (§5.4) |
| "85 m covers 62 m" | No regression band in GNC's 85 m populations | Withdrawn (§4.6) |
| NZ-03 mica/vermiculite gasket | 1595 C against a 900 C rating | J1 (§6.5), CONFIRMED by line 146 |
| Draft files `sec2_relief.txt`, `sec7_sequence.txt` | Earlier drafts | Replaced by §2.6-2.7 and §7.3 |
| Run-1 files: late_light_spike, ignition_detect, prep_path_inventory (0.06 s bleed reading), purge_hazard label fix | Corrected runs | Listed in `SUPERSEDED.txt` |

v2.4a failures and superseded evidence (kept; the v2.4 report and specifications are archived under `superseded/v2p4/`):

| Item | What happened | Consequence |
|---|---|---|
| A4 "raw" (v2.4 §0, §7.4, §8, §9.1, §12) | Line 166 (4) moved the 30 bar abort to the filtered channel; v2.4 kept "raw" (R2-01) | Filtered, 5 ms, everywhere; the line-160 record in §7.6 kept with an amendment note |
| E1 / A14 closure "before E1" and "by E0 - 0.05 s" | Three different deadlines (R2-01); E0 - 0.05 s is the scheduled flow end | Closure deadline <= the torch gate (line 166 (3)); E0 - 0.05 s kept only as the flow end |
| Stand rule "wait >= 5 s" in H9, §10.2 and the interface | Withdrawn in §7.6 but live elsewhere (R2-02) | One rule (line 172 (1)) |
| FA-1 "48.9-75.5 bar at 1 ms" and the "75.5 bar, <= 3 ms" pulse check | One O/F (8) at an ASSUMED fuel fraction (R2-03) | FA-1 envelope 83.0-88.0 bar abs; load per line 173 |
| T1-T4 specification v2.4 | Could not resolve the signature at T1; non-detection defaulted to the less safe gate (R2-04) | Specification v2, reversed burden |
| T1-T4 computation, first pass | Wrong DC-D file (not the S230 record); start rows read as run rows; the analytic model burned past burn-through (web 25.6 mm); the 62 m records counted in the 85 m group | Corrected before any value was used; the model check reproduces the q1d web (14.25 against 14.24 mm) |
| §9.1 vented-mass sentences | Contradicted their own table (R2-06) | Corrected; the barrier-bracket minimum stated as a model construct |
| Table 2.15 PURGE NOT RUN rows | All-sample would-be times under a given-light caption (R2-08) | Relabelled; given-light values stated |
| §6.4 segment heat 0.88-9.87 kJ | Mechanical's totals on the superseded v3.4 route | 0.83-9.0 kJ on CAD v3.4.1 |
| J1 "pending agreement"; lip "<= 250 C" as a requirement | J1 confirmed (line 146); 250 C a goal (line 145) | Text aligned (R2-09) |
| Line 164 "the FC delays T_fire" | GNC rev2: P 0 for commits at the plain trigger (line 174) | Withdrawn by line 175 (3) |
| Line 175 (3) "the relight proceeds unpurged (P_total ~0.75)" | Combustion's check: a light in a slug, a vapour gap, A3 after the release (§2.8) | Refuted as written (SIM/DERIVED); OI-31 for the lead |
| Purge basis theta <= 2 deg | GNC rev2 gives a 2.71 deg specific-force angle during the flow | OPEN (OI-35); CF-4 at 3 deg |
| Unpurged-start population scan, first run | Stopped after more than 600 s on the shared CPU | Re-run on a 20 000-sample subset (resolution 5e-5) |
| Interface v2.4 live values (42.85 bar, 1.0-4.3 flights per insert, 0.039 g/s, <= 7.5 MPa, 0-69 bar, 15-25 C, "valve left open", 0.28-0.29 s) | Withdrawn in the report but live in the JSON (R2-05) | Tagged SUPERSEDED or replaced in v2.4a; the block `superseded_v2p4a` lists them |
| GNC's LO premise for L* (line 181 (2)): an unpurged LO start at P_total ~0.75 | Outcome classes: worst-state P(success) 0 under LO and HI (Table 2.17) | Refuted (SIM/DERIVED); L* = 1.3 s recommended |
| sim6 V flame-out case "R2 holds the drogue in 1000/1000" | No cold-flow term; the open-loop lift keeps N2O flowing and the cold flow alone exceeds 37.16 N above about 200 N of command (bound) | Not supported for such commands (DERIVED); OI-38 |
| First cold-flow thrust run | The heat and cross-check outputs were added before any value was used; the CSV is unchanged | Second run published |
| Line 183 (2) refutation "throat-area change > 2 %" | Combustion's erosion per A1 flight: 1.9 % nominal, 8.0-8.5 % conservative, 8.4-13.6 % literature (§5.4) | Contradiction kept; criterion relative to the expected erosion proposed (OI-40) |

## 14. File index and reproduction

All paths are under the hub `/home/claude/work/shared-fallback/engine/02-combustion/`.

| Area | Scripts (`src/`) | Data and figures |
|---|---|---|
| Thermochemistry | `cea_cards.py`, `thermo_tables.py`, `perf_tables.py` | `data/thermo/*` (shifting and frozen tables, `hf_sensitivity_v1.csv`, `n2o_liquid_correction_v1.json`); `figs/v2/thermo_cstar_Tc_v2.png` |
| N2O and tank | `n2o.py`, `n2o_validation.py`, `tank.py`, `tank_nheq.py`, `tank_trades.py` | `n2o_validation_v2.*`, `supercharge_trade_*_v2.*`, `settling_v2*.json`, `ceiling_vs_time*_v2.csv`; figures `n2o_validation_v2.png`, `supercharge_v2.png`, `ceiling_vs_time*_v2.png` |
| Injector and feed | `injector.py`, `injector_compare.py`, `feed_line_checks.py` | `injector_compare_v2.*`, `injector_G_table_v2.npz`, `feed_line_checks_v2.json`; figure `injector_models_v2.png` |
| Throttle and pintle | `throttle_trade.py`, `actuator_rate_check.py`, `failure_cases.py`, `needle_force_v2p3.py`, `pintle_spring_window_v2p3.py` | `throttle_trade_v2.*`, `engine_S230/throttle_map_v2.csv`, `engine_S230/plant_valve_to_pc_v2.json`, `actuator_rate_check_v2.json`, `full_stroke_failure_case_v2.json`, `needle_force_bounds_v2p3.*`, `pintle_spring_window_v2p3.json`; figures `throttle_map_v2.png`, `plant_v2.png`, `actuator_rate_check_v2.png` |
| Grain and duty cycles | `grain_q1d.py`, `run_dc.py`, `run_dc_extra.py`, `plot_dc.py`, `chamber_port_state.py`, `m1_design.py` | `grain_trade_v2.csv`, `dc*/`, `engine_S230*/`, `chamber_port_state_v2.json`; figures `dc_DC-*_v2.png`, `grain_trade_v2.png`, `chamber_port_state_v2.png` |
| Nozzle and erosion | `nozzle.py`, `nozzle_perf.py`, `erosion_dc.py` | `nozzle_contour_v2.csv`, `nozzle_perf_v2.*`, `throat_props_v2.json`, `erosion*/`; figures `nozzle_eps_trade_v2.png`, `nozzle_sep_v2.png`, `erosion_v2.png` |
| Heat loads | `heat.py`, `thermal_bc_v2.py`, `soakback.py`, `soakback_sens.py`, `soakback_relight.py`, `headend_thermal_v2.py` | `thermal_bc_*_v2.csv`, `thermal_bc_summary_v2.json`, `soakback*_v2.*`, `headend_bc_*_v2.csv`, `headend_thermal_v2.json`; figures `thermal_bc_v2.png`, `soakback_v2.png`, `soakback_wall_v2.png`, `headend_thermal_v2.png` |
| Ignition and stability | `ignition_v2.py`, `stability.py` | `ignition_v2.json`, `stability_v2.*`; figure `stability_v2.png` |
| Interface and tables | `write_interface_v1.py`, `write_interface_v2.py`, `write_interface_v2p3.py`, `build_report_tables.py`, `make_figs_v2.py`, `summary_figs.py` | `combustion_interface_v2*_as_published.json` (v2, v2.1, v2.2, v2.3) |

Reproduction:
- Every script states its usage in its docstring.
- `python src/build_report_tables.py data` regenerates all the tables of this report from the data files.
- Inputs used from GNC are frozen in `inputs/` (snapshots with a MANIFEST).

v2.4 additions (all under `02-combustion/`; per-file hashes and producing scripts in `data/v2/v2p4/FILE-INDEX.txt`):

| Area | Scripts (`src/`) | Data (`data/v2/v2p4/`) |
|---|---|---|
| Relight vapour and purge (§2.8) | `retained_vapour_v341_v2p4.py`, `retained_table_v341_v2p4.py`, `segment_heat_v341_v2p4.py`, `purge_sizing_v2p4.py`, `purge_slip_v2p4.py`, `purge_table_v2p4.py`, `purge_duration_v2p4.py`, `rg01_line_states_v2p4.py`, `fd01_element_deficit_v2p4.py`, `cf4_void_budget_v2p4.py`, `purge_hazard_v2p4.py` | `retained_vapour_v341_v2p4*`, `purge_*_v2p4.json`, `rg01_line_states_v2p4.json`, `fd01_element_deficit_v2p4.json`, `cf4_void_budget_v2p4.json` |
| Ignition and sequence (§7) | `start_latency_v2p4.py`, `torch_gate_v2p4.py`, `ignition_detect_v2p4.py`, `relight_*_v2p4.py`, `post_abort_pocket_v2p4.py`, `drogue_hold_check_v2p4.py`, `hard_start*_v2p4.py`, `late_light_spike_v2p4.py`, `late_light_tables_v2p4.py`, `sil_inventory_bound_v2p4.py` | matching `*_v2p4.json` |
| Relief, safing, stored energy (§2.7, §9, §10) | `safing_relief_v2p4.py`, `safing_vent_v2p4.py`, `stored_energy_sup_v2p4.py`, `meop_basis_v2p4.py` | matching `*_v2p4.json` |
| Grain, erosion, nozzle (§4-§6) | `run_dispersed_v2p4.py`, `dispersed_checks_v2p4.py`, `b1_*_v2p4.py`, `burn_limit_proxy_v2p4.py`, `oxrich_62m_v2p4.py`, `coast_migration_v2p4.py`, `erosion_v2p4.py`, `rc09_etacf_band_v2p4.py`, `nozzle_joint_v2p4.py`, `nozzle_lip_melt_v2p4.py` | matching files and `erosion/` |
| Report and interface | `build_report_v2p4.py` (assembles this report from v2.3 and the v2.4 section drafts), `write_interface_v2p4.py` (combustion.json v2.4 from v2.3 by keyed edits; every v2.3 key kept), `hub_copy_v2p4.py` | `combustion_interface_v2p4_as_published.json` |

Reproduction: each script states its usage and asserts its input hashes; run with `python -I`. The CF-4 specification is `CF-4-SPEC.md`.

v2.4a additions (scripts in `02-combustion/src/`; data in `02-combustion/data/v2p4a/` with `HASHES.txt`; sha256/16):

| Script | Data | Use |
|---|---|---|
| `fa1_envelope_v2p4a.py` (`a6b71cb487c9642e`) | `fa1_envelope_v2p4a.json` (`64b328150025fa1e`), `fa1_envelope_summary_v2p4a.csv` (`86d764bc80ed1dd5`), log | FA-1 envelope (§7.6) |
| `fa1_tables_v2p4a.py` (`cd4f66e9b5a5a52b`) | `fa1_tables_v2p4a.json` (`677fd9ccd297fdf4`) | Tables 7.6a and 7.6b |
| `fa1_outflow_sens_v2p4a.py` (`eb487c6139c7f72a`) | `fa1_outflow_sens_v2p4a.json` (`540a78f8b9634f76`) | R2-11 outflow sensitivity |
| `vented_mass_brackets_v2p4a.py` (`114108a9807a86d3`) | `vented_mass_brackets_v2p4a.json` (`8e8ca9329c74a01f`) | §9.1, CF-4 P5 |
| `t1t4_law_resolution_v2p4a.py` (`3701b74681de700b`) | `t1t4_law_resolution_v2p4a.json` (`05b5ae5c20e04bd8`), log | §10.4 and the T1-T4 specification v2 |
| `unpurged_start_check_v2p4a.py` (`41fad4500f472bd4`) | `unpurged_start_check_v2p4a.json` (`4c745dcfbf09aef7`), log | §2.8 (Table 2.16), §2.4 tank outlet |
| `unpurged_outcomes_v2p4a.py` (`8256face5bcf7b27`), generated by `gen_unpurged_outcomes_v2p4a.py` (`394bd079a3b50f92`) | `unpurged_outcomes_v2p4a.json` (`18a639d61b58ce8a`), log | §2.8 (Table 2.17), line 181 (2) |
| `cold_flow_thrust_v2p4a.py` (`b4cbf147753ecc7c`) | `cold_flow_thrust_v2p4a.json` (`a226dfacf494cb2c`), `cold_flow_thrust_v2p4a.csv` (`e094c4be80d12f66`), log | §7.3 (Table 7.3a), line 181 (4) |
| `build_cf4_v2.py` (`77151ba0c7e9712f`) | `CF-4-SPEC.md` v2.0 | §10.3 |
| `write_interface_v2p4a.py` (`5c06eb0a06e09daf`) | `interfaces/combustion.json` v2.4a (`5237d4584bad38c4`) | every v2.4 key kept |
| `build_report_v2p4a.py` | this report, from v2.4 by asserted edits | - |

Reproduction (v2.4a): each script asserts its input hashes; run with `/opt/engine-venv/bin/python -I`.
