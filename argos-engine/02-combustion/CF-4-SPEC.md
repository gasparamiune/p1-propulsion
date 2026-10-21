# CF-4: relight-purge cold-flow test specification

Version 2.3 (Combustion v2.4d), 2026-10-21: LEAD line 258 (2) folded by the lead: purge conditions (d1) and (d2) in P5 (line 102) and §10 (line 179); the v2.3 changes are listed in §14 at the end; the edits are in place, so lines 1-204 keep their v2.2 numbers. v2.2 (`4e36be703a9e7d44`) is archived as `02-combustion/superseded/v2p4c/CF-4-SPEC.md`. The v2.2 header follows unchanged. Version 2.2 (Combustion v2.4c), 2026-10-21: text corrections from REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`, `2908321d7f75d439`) and the LEAD line 256 purge decision, applied by the lead; the v2.2 changes are listed in §13 at the end; the edits are in place, so lines 1-191 keep their v2.1 numbers. v2.1 (`60bbc51f6f487682`) is archived as `02-combustion/superseded/v2p4b/CF-4-SPEC.md`. The v2.1 header follows unchanged. Version 2.1 (Combustion v2.4b), 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228, last change bullet below). It replaces v2.0 (Combustion v2.4a), which is archived as `02-combustion/superseded/v2p4a/CF-4-SPEC.md`; v1.0 is in `superseded/v2p4/`. Owner of the specification: Combustion and Propulsion. Physical execution: the founders. Status: accepted by the lead as the gate for the A1 relight claim (CHANGELOG line 164). This is a digital specification only; no test has been run. A passing simulation is not a pass of this test.

Changes in v2.1 (REV-COMB-3 R3-08; LEAD CHANGELOG lines 186 (1) and 194 (3) and (8)):
- §1 states the decided PURGE commit rule (L* = 1.3 s; below it no purge and no unpurged relight) and removes the "proceeds unpurged" text and the 0.22 s hold, which line 194 (3) withdrew.
- §2: the hardware baseline is the frozen CAD v3.5.1 bleed path (REV-MECH-1 RM1-01, LEAD line 188 (1)); the model numbers of §5 are on CAD v3.4.1 until the purge grid is re-run on v3.5.1.
- The lift is THE start-level lift (LEAD line 203 (7)): the ignition-lift table row at the test tank temperature (0.21776 mm at 286.7 K before CF-3; 0.2039 mm at 20 C). P1 is stated in volume, 18.86 cm3 of lift flow after the pintle reaches the lift: 0.275 s at 0.21776 mm, 0.293 s at 0.2039 mm; t_lift 29.5 ms at 0.21776 mm (28.7 ms at 0.2039 mm).
- New: §4.1 preparation and verification of IS-1 to IS-3, §5.1 the continuous-liquid probe threshold, §9.1 red lines and abort criteria, §12 run and N2O budget.
- LEAD line 213 (founder decision), DECIDED by lines 214 and 227 (1): the A1 apogee target is 210 m (it was the 300 m lead default and the 285 m trim). The A1 relight tank state of §4 and the IS-2 coast duration come from the 300 m records and stay as comparators; the 210 m warm-end relight state becomes a tank-state point when GNC publishes the 210 m record (§4; REPORT §15.15).
- Final fold (2026-10-19; LEAD lines 214-228, 216 (5) and 216 (9)): P5 names ONE purge flow basis, 29.25 g/s (DERIVED: 76 g over 2.598 s of flow at the 289.5 K warm-end relight state on the Combustion record bound; REPORT §16.5), and the measured-time form of the cap that CF-4 / B-BLEED-1 set: both-open overlap <= 76 g / mdot_measured - (t_close - t_open). The start-level lift at the A1 relight state is confirmed as 0.21776 mm (216 (9); REPORT §16.6). The A1 duty cycle does not shorten at 210 m (227 (9), RV6-05); the 210 m relight state is still MISSING (OI-49).

Changes in v2.0:
- P4 is now defined per tap and per phase, and names the model bracket it is judged against (REV-COMB-2 R2-06).
- P6 follows the E1 closure term of LEAD line 166 (3). The closure deadline is at or before the torch gate; Electronics v4 sets it at the torch gate, E0 + 0.16 s (160 ms, kTorchGate_s; v2.2 correction, REV-COMB-4 R4-06).
- The PURGE commit rule of LEAD line 175 (3) is stated, together with Combustion's finding on unpurged starts (§1).
- A 3 deg attitude is added, because GNC's specific-force angle exceeds the 2 deg basis (§4).
- A tank-outlet probe is added (§3), and optional run O-3, an unpurged start (§8).

Related documents:
- `02-combustion/REPORT` v2.4b: §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input) and §10 (test plan);
- `interfaces/combustion.json` v2.4b: `purge`, `cf4_gate`, `igniter.sequence`, `purge_commit_rule_v2p4b` and `release_hold_v2p4b`. Units are SI except where stated (bar, cm3, g, mm as written).

## 1. Purpose and claim under test

After an A1 coast, vapour collects in the valve-to-seat segment. If too much vapour reaches the pintle at the ignition lift, the main flow is late and the start aborts. The adopted design (LEAD line 164) removes that vapour before the relight with a forced purge. The main valve MV-P opens with the pintle seated, both head-end bleed taps vent for the decided 2.43 s of flow (LEAD 253 (7)(ii), final in 256 (2); the model numbers of this specification were run with 2.5 s), and the flow stops 0.05 s before T_fire (E0).

**PURGE commit (LEAD line 186 (1); it replaces the PROVISIONAL rule of line 175 (3) and the 1.7 s interim of line 181 (2)).** PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s, for both heat brackets. Below L* there is no purge and no unpurged relight on that pass (drogue descent; vehicle loss in the FMEA).
- Basis (SIM/DERIVED: `unpurged_start_check_v2p4a.json`, `unpurged_outcomes_v2p4a.json`, `release_hold_v2p4b.json`): at the worst PURGE NOT RUN states an unpurged start succeeds with P 0 under both brackets. In the LO worst state every light (P 0.758) happens inside the first liquid slug, and a 23.4 cm3 vapour gap follows 0-0.19 s after E2 (flow held at the lift), when the drogue-release term is already true; the gap drives A3 (ratio <= 0.24 against 0.40).
- The "E2 + 0.22 s" release hold of line 186 (1) is WITHDRAWN (LEAD line 194 (3)). Over all 2160 PURGE NOT RUN records (0 and 2 deg), the latest A3 trip after E2 plus one 10 ms frame is 0.30 s with the 2500 N/s ramp to 200 N flown during the hold, 0.19 s with the ramp to 500 N, and 0.74 s with the flow held at the lift, which is outside W 0.65 s (unlined records; 0.31 / 0.19 / 0.75 s with the lined records). With Pc invalid the command is held at the start level (line 186 (2)), which is the lift-flow case, so the unpurged alternative is not admissible then; GNC flies it only as a comparator.
- CF-4 tests the purge, not the commit rule. Optional run O-3 (§8) measures the unpurged sequence; the generation runs (§8) measure the LO/HI bracket, which stays open (line 186 (1)).

**Claim C-RL.** With the decided purge path as frozen in CAD v3.5.1 (§2) and the decided 2.43 s of flow ending 0.05 s before E0 (LEAD 256 (2); the model behind the claim was run with 2.5 s and needs at most 2.2 s, at the 283.15 K corner), at a tilt theta <= 2 deg, an A1 relight lights within the window W 0.65 s with P_abort <= 1e-3, venting <= 76 g of N2O.

The model behind the claim (SIM on CAD v3.4.1, `data/v2/v2p4/rg01_line_states_v2p4.json`, `2939549811d4c381`; re-run on v3.5.1 before the test, §2) needs 1.9 s of flow at 289.5 K (<= 1.94 s with the FD-01 element) and 2.2 s at 283.15 K (REV-COMB-4) and predicts a vapour pocket of 4.77-8.15 cm3 at the lift after 2.5 s. Its weakest inputs are the cap transport in the lines (slip), the restrictor Cd and the coast vapour generation. CF-4 measures them.

## 2. Hardware

**Baseline (v2.1; R3-08, LEAD line 194 (8)).** The test hardware is the frozen CAD v3.5.1 bleed path. REV-MECH-1 RM1-01 (LEAD line 188 (1)) relocates BL-02 and re-routes BL-03 and BL-04, so the v3.4.1 segment, restrictor positions and line lengths used by the model change. The v3.5.1 paths are MISSING from this specification: Mechanical is freezing them, and the lead forwards them. Before CF-4 is run, Combustion re-runs the two-flow purge grid on the v3.5.1 geometry (about 20 min) and re-issues P1, P3, P4, P5, Table 1 and the segment inventory. Until then the numbers in this specification are the v3.4.1 values.

- Metal, flight-equivalent segment from the MV-P seat to the pintle seat: the FS-01 module with S1 and the J602 cavity, FD-08F, the wall line, the re-routed hose coil clamped as in flight, the riser, the TEE, the FD-01 tap, the head with its 15 um element, the T4 crown tap, the manifold annulus and the pintle.
- The flight bleed path as built (Mechanical, CHANGELOG line 162):
  - two equal sharp-edged restrictors, 0.707 mm each (0.71 mm drill), one per tap; each restrictor flow-tested for Cd before assembly;
  - the inline <= 15 um element on the FD-01 leg, between the tap and the tee, Cd.A >= 1.57 mm2, with its measured dP-flow curve;
  - the two normally-closed bleed valves V1 and V2 in series, each with >= 4x the restrictor's flow capacity (F1);
  - the -2 line and the balanced (opposed pair) or axial outlet.
- The flight MV-P and pintle drive, run by the flight firmware's PURGE sequence (hardware in the loop).
- A tilt fixture for 0, 2 and 3 deg, toward azimuth 45 and 180 deg, with sensitivity runs at 4 deg. The 3 deg setting is new; see §4.
- Back-pressured catch volumes for the pintle flow and for the vent, each with its own relief valve (set at or below its MAWP, sized for the largest inflow as vapour), a burst disc and a remote vent; the vent catch volume on a load cell.
- All wetted parts cleaned for oxygen service and inspected (REPORT §10.1). No water in this hardware unless followed by drying, re-cleaning and an N2 leak check.

## 3. Instruments (minimum)

- Void or phase probes, response <= 5 ms: pintle inlet, FD-01 crown, T4 crown, riser top, TEE, the two hump crowns at 2 deg, S1 cap region.
- Pressures at >= 1 kHz: tank, P_feed, manifold, upstream of each restrictor, downstream of V2.
- Temperatures: a 0.5 mm sheathed thermocouple in each tap jet; head, hose and module walls; tank liquid.
- Masses: tank load cell; vent catch-volume load cell.
- Per-tap flow: the pressure upstream of each restrictor and downstream of V2, read against that restrictor's own flow test. Each restrictor is flow-tested before assembly in liquid and in vapour, giving a dP-flow curve for each phase. The sum of the two taps must agree with the vent load cell within 10 % (ASSUMED).
- Tank outlet: a void probe at the tank outlet when the flight tank is used. GNC's liquid mass during the flow is 766-1170 g. The outlet geometry is MISSING (tank not in CAD; REPORT v2.4a §2.8).
- Valve command and current signatures for MV, V1 and V2; pintle encoder.

## 4. Initial states and runs

Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget. v2.2 (REV-COMB-4 R4-07): the 283.15 K relight corner needs the most flow (2.2 s unlined); add at least one IS-2 run with the tank at or below 283.15 K, or state in the test record that the cold corner is model-only.

A1 profile (LEAD lines 213, 214 and 227 (1); new in v2.1). The A1 apogee target is 210 m, DECIDED (line 214; accepted in 227 (1)); gnc.json v3.2 carries the record (not in the hub at this build). The bracket above comes from the 300 m records and stays as a comparator (300 m records, SIM: relight 282.97-290.07 K, coast 18.22-20.72 s). At the same launch temperature the 210 m relight state is warmer: the modelled tank keeps its MECO temperature over the coast, and a shorter ascent cools it less (DERIVED direction; magnitude MISSING). When GNC publishes the 210 m record, its warm-end relight state is added as a tank-state point and P5 is read there. The purge vented mass rises by about 0.66 g per K above 289.5 K (DERIVED scaling of the records, not re-run); the 2.5 s schedule stays <= 76 g up to 294.21 K, and the 2.55 s cap is already at the 76 g limit at 289.5 K (OI-42) (`a1_profile_line213_v2p4b.json` `46b6a1c6efec0351`). The IS-2 heated hold keeps the 300 m coast duration: the longer coast puts more heat into the segment, which is the conservative side for the vapour cap (DERIVED direction). v2.2: the decided 2.43 s of flow with the 2.39 s both-open cap vents <= 66.7 / 70.8 / 75.1 g at 283.15 / 289.5 / 297.15 K (Cd 0.70) and 75.75 g at the 2.44 s of flow the cap allows, inside 76 g (LEAD 256 (2); REV-COMB-4 R4-07, DERIVED). At Cd 0.80 the same schedule would vent about 80.5 g at 289.5 K and 85.5 g at 297.15 K [ESTIMATE], above the 82.1 g at which GNC's A1 reserve test first fails (REV-GNC-7), so P5 records the measured Cd x A and the flow and cap are re-set from it (LEAD 257 (2)).

Attitude:
- The model behind C-RL covers theta <= 2 deg.
- GNC rev2 re-flown records give the angle between the specific force and the body axis during the purge flow as up to 2.71 deg raw, or 2.65 deg as a 0.1 s mean (`purge_outlet_inputs.json` 47b4deb96ea22043, six records; no 500-run distribution).
- The model is not computed at 2.7 deg; this is OPEN, and the purge grid was not re-run in v2.4a.
- CF-4 therefore runs at 3 deg as well as 0 and 2 deg. The 4 deg sensitivity runs bracket it.

| State | Description | Role |
|---|---|---|
| IS-1 | Vapour-full segment | HI bound |
| IS-2 | ARM-LO-like: traps full, short slug, cap at S1 | Typical coast state |
| IS-3 | Liquid-primed segment | Calibration reference, not a flight state |

### 4.1 Preparation and verification of the initial states (new in v2.1; R3-08)

A run starts only when its state is verified as below; a run whose state is not verified does not count. Tolerances are ASSUMED; the founders may tighten them.

| State | Preparation | Verification before the PURGE command |
|---|---|---|
| IS-3 liquid-primed | MV open with the pintle seated and both bleed valves open until every segment probe reads liquid for >= 2 s; then bleeds and MV closed | Every segment probe liquid for >= 2 s; P_feed within 0.5 bar of P_tank; the probe liquid levels recorded for §5.1 |
| IS-1 vapour-full (HI bound) | From IS-3: MV closed; drain the segment through the bleed path into the vent catch volume with the walls held at T_sat(P_tank) + 2-5 K by the segment heaters until every probe reads vapour; bleeds closed | Every segment probe vapour for >= 10 s; drained mass on the vent load cell >= 90 % of the segment liquid inventory (37.8 g at 20 C on v3.4.1; re-issued for v3.5.1); every wall thermocouple >= T_sat(P_tank); the probe vapour levels recorded for §5.1 |
| IS-2 ARM-LO-like (traps full, short slug, cap at S1) | From IS-3: MV closed; heated hold at Mechanical's LO coast heat budget for the A1 coast duration (the generation-run condition, §8), so that the cap grows at S1 while the traps stay full. A drained measured mass from IS-3 may replace the hold if the probe pattern below is met | S1-cap probe vapour; trap probes (hump crowns at 2 deg, FD-01 crown, T4 crown, riser top) liquid; heat input logged; cap volume estimated from the heat input (0.0067 cm3/J with vapour at the S1 port, 0.0388 cm3/J with liquid; REPORT §2.7) within ±30 % of the model's IS-2 cap (rg01 ARM-LO state, re-issued with the v3.5.1 re-run) |

At least 5 runs per state and attitude (sample size ASSUMED; the founders may raise it). In each run the ECU executes PURGE and then the lift to THE start-level lift: the ignition-lift table row at the test tank temperature (LEAD line 203 (7); 0.21776 mm at 286.7 K and 0.2039 mm at 20 C before CF-3), with the encoder lift recorded. PURGE is commanded at the flight command time that Electronics v2.12 states (E0 - 2.83 s ends the decided 2.43 s of flow at E0 - 0.05 s; E0 - 2.90 s, the analysed command time with 2.5 s of flow, ends it at E0 - 0.12 s [DERIVED]); the FC's commit rule (§1) is not under test. The primary measurement is the time from the lift command to the first continuous liquid at the pintle inlet.

## 5. Pass criteria

The claim is closed for the tested states only if P1-P7 hold in every run.

| ID | Criterion | Basis |
|---|---|---|
| P1 | First continuous liquid (§5.1) at the pintle inlet after at most 18.86 cm3 of lift flow from the moment the pintle reaches the commanded start-level lift (encoder): time limit = 18.86 cm3 / the measured liquid volume flow at the lift. 0.275 s at the A1-state lift 0.21776 mm (37.4 g/s), 0.293 s at 0.2039 mm (35.0 g/s); after the lift command add t_lift (29.5 ms at 0.21776 mm, 28.7 ms at 0.2039 mm: 6.5 ms command, 10 ms lag, lift at 16.7 mm/s). v2.0 quoted 0.293 s after the 0.2039 mm lift with t_lift 29.6 ms, the 0.2192 mm value | Zero-abort limit V_zero 18.86 cm3 x 0.015555 s/cm3. Model: <= 0.13 s (pocket <= 8.2 cm3) |
| P2 | Then >= 0.35 s of continuous liquid (15 cm3 at the lift flow). A later void is acceptable only inside Table 1 | `cf4_void_budget_v2p4.json` (`6c294cf2dec7af5d`) |
| P3 | The S1 cap and the hump vapour clear the FD-01 crown before the flow ends: the FD-01 crown, riser-top and hump-crown probes read liquid for >= 0.2 s before closure, i.e. the cap clears <= 2.3 s after the flow starts | Model latest 2.27 s (s 0.5 bracket) |
| P4 | Per tap and per phase, from the per-tap flow channel (§3). Each phase is identified by the tap-jet thermocouple and the phase probes. Vapour phase, from the start of flow to the arrival of liquid at that tap: >= 3.4 g/s per tap (80 % of the HEM model, 4.25). Liquid phase: >= 12.5 g/s per tap (80 % of the Dyer model, 15.62). Cd_eff >= 0.56 with V1 and V2 in series, and dP across V1 + V2 <= 11 % of the path total, in each phase. The model reference is the open-element reading. The barrier-element reading is a bracket only: its stall of the T4 tap is a model construct (bubble point about 0.7 kPa against 45.5 bar) that a real T4 will not reproduce, so P4 is not judged against it. A measured T4 stall is a finding: it fails P4 for that tap. | F1: the restrictors control the flow. Brackets: `vented_mass_brackets_v2p4a.json` |
| P5 | N2O vented <= 76 g per run from IS-1 and IS-2 (load cell; model 34-73 g). Model bracket of m(t) for the decided path: open-element minimum = the all-vapour line 8.49 t g until 1.0 s, then 10.4 g at 1.1 s and 44.9 g at 2.5 s; maximum 11.9 g at 0.5 s and 72.9 g at 2.5 s. The all-liquid line 31.24 t (78.1 g at 2.5 s) is never reached, because every record starts with vapour. IS-3 calibrates the path at 2 x 15.62 g/s, about 78 g in 2.5 s; a mass below 80 % of that flags a restricted path. Flow basis (LEAD 216 (5)): ONE basis, 29.25 g/s = 76 g / 2.598 s of flow at 289.5 K (flow time = both-open overlap + (t_close - t_open), valve times ASSUMED 30 / 80 ms): strict 76 g needs overlap <= 2.548 s. After the IS-2 runs at the A1 relight state the cap is set from the measurement: overlap <= 76 g / mdot_measured - (t_close - t_open), with mdot_measured = M(t_flow) / t_flow from the load cell and t_open, t_close from the valve position channels. v2.2 (LEAD 256 (2)(b); REV-COMB-4 R4-07): the measured Cd x A of the two-tap path must be >= 0.91 x the Cd 0.70 value (>= 0.95 x with the 4x FD-01 element bound), else the flow is re-sized; with the decided 2.43 s of flow and the 2.39 s cap the model vents <= 66.7 / 70.8 / 75.1 g at 283.15 / 289.5 / 297.15 K (Cd 0.70). From the measured Cd x A, kPurgeFlow_s and the both-open cap are re-set by the measured-time form, overlap <= 76 g / mdot(297.15 K) - (t_close - t_open), never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g; without the re-set the measured Cd x A must also be <= 1.08 x the Cd 0.70 value (vent <= 82 g, inside GNC's A1 reserve test) (LEAD 257 (2); REV-GNC-7). v2.3 (LEAD 258 (2); REV-GNC-7 RV7-04): (d1) the re-set takes the upper 95 % bound of the measured N2O Cd x A, not its mean (at the Cd 0.80 ratio 1.1326 a ratio measured 7.9 % low would give a true vent of 81.99 g, just under the 82.1 g first fail of the A1 reserve test); (d2) the run report shows the 283.15 K need at the re-set flow (the need scaled by 1 / (Cd x A), ASSUMED); below a ratio of 1 the (b) acceptance governs | LEAD plan <= 76 g per purge; basis LEAD 216 (5) (`purge_basis_line216_v2p4b.json` `ca2ee1f0ea0f0194`). Brackets: `vented_mass_brackets_v2p4a.json` |
| P6 | (a) Flow stopped by the scheduled end, E0 - 0.05 s (LEAD line 164), read on the pressure downstream of V2. (b) Closure confirmed by the closure deadline on the signal the ECU uses: V1 first, read on P_mid. The deadline is the torch gate, E0 + 0.16 s (Electronics v4: 160 ms, kTorchGate_s; REV-COMB-4 R4-06). E1 = torch confirmed 2oo2 AND [closure confirmed OR deadline reached] (LEAD line 166 (3)). (c) A run with one valve held open must raise BLEED_FAULT at the deadline. The flight build then commands V2 closed, the lift proceeds, and BLEED_FAULT goes to the FC as log-only (LEAD line 168). The stand build aborts. | Tests the detection behind A14 and the E1 closure term |
| P7 | No unfiltered path from the FD-01 tap to the pintle seat: with the bleed valves closed and >= 264 g/s of liquid through the pintle (100 % flow), the FD-01 -> tee -> T4 flow passes only through the inline element. Check the as-built path against the drawing, record the leg flow (model bypass 1.8-5.4 g/s), and bubble-point test the element before and after the series | F2 (LEAD line 160) |

Table 1. Largest acceptable second void C1 [cm3] after a first pocket P1 and a liquid slug S1 (both in cm3), worst of the two dead-time conventions. 0: no second void is acceptable. "none": no limit below 80 cm3.

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

### 5.1 What "continuous liquid" means (new in v2.1; R3-08)

- Each void probe is calibrated in every series on IS-1 (vapour level V_v) and IS-3 (liquid level V_l), at the test pressure and temperature.
- A sample reads liquid above V_v + 0.6 (V_l - V_v) and vapour below V_v + 0.4 (V_l - V_v); between the two the previous reading holds (hysteresis, ASSUMED).
- Continuous liquid is a liquid reading interrupted by no vapour reading longer than the probe response (5 ms). Each shorter vapour reading counts as a void of one probe response at the lift flow, 0.22 cm3 (37.18 g/s at the A1-state start-level lift 0.21776 mm, liquid 830 kg/m3; DERIVED, CoolProp). These voids are added up and judged against Table 1 as a second void.
- P1 is the time of the first sample of the continuous-liquid interval that meets P2.
- A probe that fails its calibration (contrast V_l - V_v below the maker's minimum, TO-VERIFY) invalidates the run.

## 6. Model checks (not gating)

A failure here triggers a re-run of the trade with the measured value; it does not by itself fail the claim.
- Slip (cap speed over column speed) >= 0.5 in the hose and in the wall line.
- Hump sweep at 2 deg: column flow while hump vapour remains >= 17.4 cm3/s at 1.14 g (model minimum on this path 26.0 cm3/s).
- Vapour regrowth from the end of the flow to the lift.
- Restrictor Cd (0.70 ASSUMED).
- FD-01 element: Cd.A from its dP-flow curve. Below 0.63 mm2 the 0.3 s margin is not shown and Combustion re-runs the two-flow purge grid (about 20 min).

**Ground test against flight.** The specific force at RELIGHT is 0.94-1.14 g. At 1.14 g the drift slip falls: s_flight = 1 - (1 - s_1g) x 1.068. Report both slips and run the model at s_flight; it must pass.

## 7. Refutation

- Any P1 or P2 failure refutes the claim for that state. Combustion re-runs the trade on the measured inputs, GNC re-flies, and RG-01 stays BLOCKING.
- P3 or P4 failing while P1 and P2 pass: the claim holds only for the runs tested; the margin is not shown. Re-run the model with the measured flows and slip.
- P5 above 76 g: GNC re-flies the A1 reserve.
- P6 or P7 failing: hardware fix (F1 or F2) and retest.

## 8. Optional runs

They settle open disagreements, not the claim:
- Generation runs: MV closed, heated hold at the LO and HI budgets, void growth of the full head trap. This settles the wet and dry readings.
- The SIL's 0.17 s prep-path purge credit.
- O-3, unpurged start. From IS-2 with PURGE not run, lift directly to the start-level lift (table row at the test tank temperature). Record the phase sequence at the pintle inlet for 1.5 s, then compare it with the PURGE NOT RUN LO state: pocket 12.5 cm3, slug 11.2 cm3, gap 23.4 cm3 (`rg01_line_states_v2p4.json`). A sequence with no gap after the first slug refutes Combustion's unpurged-start finding for that state. A gap confirms it, and its arrival time after the first liquid is the input of the hold table (`release_hold_v2p4b.json`).

(The earlier optional run on Mechanical's 15.91 cm3 unreached volume is no longer needed: it was a 10 deg robustness row, 4.84 cm3 at theta <= 2 deg, closed at CHANGELOG line 162.)

## 9. Safety

- Remote operation only; nobody within the exclusion zone set by the founders under local rules (stored-energy inputs in REPORT §9.2).
- N2O vents outdoors, away from people; cold-burn protection for handling (vent temperature -88.5 C).
- Every lockable volume of the stand has a relief; the catch volumes as in §2.
- After the series: the tank is vented remotely and still holds cold liquid until its mass shows otherwise (REPORT §10.2).

### 9.1 Red lines and abort criteria (new in v2.1; R3-08)

Heated holds and flowing runs stop as below. "Abort" means: MV de-energised; bleed valves V1 and V2 commanded closed (stand build; a valve that does not close leaves the segment venting into the vent catch volume, which is sized for it); pintle commanded closed; heaters off; then the REPORT §10.2 safing (remote vent, N2 purge, hold before approach). Values are ASSUMED unless tagged; the founders may tighten them; relaxing one needs the lead.

| # | Red line | Limit | Action |
|---|---|---|---|
| C-R1 | Segment over-pressure with the MV closed (S1 flag) | P_feed - P_tank > 2 bar for 1 s (A13, LEAD) | Heaters off; lock out (stand A13); vent through the bleed path |
| C-R2 | Segment wall temperature in a heated hold | above the coast-budget maximum + 5 K, or segment liquid more than 3 K above the tank temperature (a liquid-full segment with S1 stuck reaches MAWP after 7.3 K of warming; REPORT §2.7, DERIVED) | Heaters off; vent through the bleed path |
| C-R3 | Tank state | T_tank > 24 C or P_tank > 5.53 MPa (the ARM interlock; the A1 state is 43.5-46.5 bar, 286.7-289.5 K) | Abort; remote vent |
| C-R4 | Catch-volume pressure | > 80 % of its relief set | Abort; remote vent |
| C-R5 | Any relief or disc lift (stand, segment or catch volume) | any | Abort; the run is invalid; inspect |
| C-R6 | Leak | gas-detector alarm, or a closed-segment pressure decay > 0.5 bar/min at steady temperature | Abort; remote vent; N2 purge |
| C-R7 | Bleed valve stuck open beyond P6 (c) | after BLEED_FAULT at the closure deadline, V2 not closed within 0.10 s of its command, or the pressure downstream of V2 not at the vent back-pressure within 0.5 s | Abort (stand build); recorded as a P6 failure |
| C-R8 | Pintle | A6 or A15 (REPORT §7.4): encoder invalid, jam, or drift > 0.05 mm for 10 ms while commanded seated during PURGE | Abort |
| C-R9 | Channel loss | any red-line channel (P_tank, P_feed, catch-volume pressure, wall thermocouples, pintle encoder) lost for 50 ms | Abort |

## 10. Data to return to Combustion

Raw logs (all channels, time-aligned, with the firmware event log), the run matrix with states and attitudes, the restrictor and element flow-test records, load-cell masses, probe calibration, cleaning records, and any anomaly. Combustion reduces them against P1-P7, re-runs the trade on the measured slip, Cd and element curve, and reports the result through the lead. v2.3 (LEAD 258 (2)): with the measured Cd x A of the two-tap path, Combustion reports its upper 95 % bound (d1) and the 283.15 K need at the re-set flow (d2).

## 11. Cost

Valves, restrictors, the FD-01 element, probes, fixtures and catch volumes, and the N2O of §12: TO-QUOTE, delivered to Sønderborg, DK-6400. No price is assumed.

## 12. Run and N2O budget (new in v2.1; R3-08)

From `test_budgets_v2p4b.json` (c0e4ce35659f21fa; DERIVED on ASSUMED repeats):
- **Runs.** 3 states x 5 attitude settings (0 deg; 2 and 3 deg toward azimuth 45 and 180 deg) x 5 repeats = 75 (base). With the 4 deg settings also repeated 5 times per state: 105. With IS-3 once per attitude and each 4 deg setting once per state: 59.
- **N2O per run:** <= 76 g vented (P5 limit) + 55.8 g of lift flow over the 1.5 s record (37.18 g/s at the A1-state start-level lift; 166.0 g per run at 0.2039 mm) + 37.8 g of segment inventory to set the state (v3.4.1, 20 C) = 170 g.
- **Total N2O:** 10.0 / 12.7 / 17.8 kg for 59 / 75 / 105 runs, or 11.0 / 14.0 / 19.6 kg with a 10 % allowance (ASSUMED) for fills, chill-down and aborted runs.
- That is 6-10 fills of the 2.0 kg flight load, or 1.1-1.9 fills of a 15 L ground tank (10.4 kg, ASSUMED). The founders' stand tank is MISSING. Optional runs (generation runs, the prep-path credit, O-3) and the tank heel are not included.

## 13. v2.2 changes (Combustion v2.4c, 2026-10-21)

Text corrections from REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`; R3-08 residual, R4-06, R4-07) and the LEAD purge decisions of lines 256 and 257 (2). The edits are in place, so lines 1-191 keep their v2.1 numbers.
- §1 (line 26) and C-RL (line 33): the decided 2.43 s of flow with the 2.39 s both-open cap; the model numbers stay on the analysed 2.5 s, which is more flow than decided.
- Line 35: the needed flow is 1.9 s at 289.5 K and 2.2 s at 283.15 K (LEAD 256 (2)(a)).
- §4 (line 64): at least one IS-2 run at or below 283.15 K, or the cold corner stated model-only.
- §4 (line 66): the vented mass of the decided schedule (<= 75.1 g at 297.15 K, Cd 0.70; 75.75 g at the cap); at Cd 0.80 the same schedule would vent about 85.5 g at 297.15 K [ESTIMATE], which fails GNC's A1 reserve test (REV-GNC-7).
- §4 (line 90): the PURGE command time is the one Electronics v2.12 states.
- P5 (line 102): the measured Cd x A of the two-tap path >= 0.91 x the Cd 0.70 value (>= 0.95 x with the FD-01 element bound), else the flow is re-sized (LEAD 256 (2)(b)); from the measured Cd x A, kPurgeFlow_s and the both-open cap are re-set by the measured-time form with the mass flow at 297.15 K, never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g; without the re-set, Cd x A <= 1.08 x the Cd 0.70 value (LEAD 257 (2); REV-GNC-7); the line stays unlined (256 (2)(c)).
- P6 (line 103) and the v2.0 change list (line 15): the closure deadline is the torch gate, E0 + 0.16 s (Electronics v4, kTorchGate_s).

No test has been run; this specification approves nothing.

## 14. v2.3 changes (Combustion v2.4d, 2026-10-21)

LEAD line 258 (2) on REV-GNC-7 RV7-04 (`reviews/REVIEW-GNC-R5.md`, `6b86fcd326568646`). The edits are in place, so lines 1-204 keep their v2.2 numbers.
- Line 3: version header v2.3.
- P5 (line 102): (d1) the re-set takes the upper 95 % bound of the measured N2O Cd x A; (d2) the run report shows the 283.15 K need at the re-set flow; below a Cd x A ratio of 1 the (b) acceptance governs.
- §10 (line 179): Combustion reports the upper 95 % bound of the measured Cd x A and the 283.15 K need at the re-set flow.

No test has been run; this specification approves nothing.
