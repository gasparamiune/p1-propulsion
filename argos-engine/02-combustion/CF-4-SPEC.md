# CF-4: relight-purge cold-flow test specification

Version 2.0 (Combustion v2.4a), 2026-10-13. It replaces v1.0, which is archived as `02-combustion/superseded/v2p4/CF-4-SPEC.md`. Owner of the specification: Combustion and Propulsion. Physical execution: the founders. Status: accepted by the lead as the gate for the A1 relight claim (CHANGELOG line 164). This is a digital specification only; no test has been run. A passing simulation is not a pass of this test.

Changes in v2.0:
- P4 is now defined per tap and per phase, and names the model bracket it is judged against (REV-COMB-2 R2-06).
- P6 follows the E1 closure term of LEAD line 166 (3). The closure deadline is at or before the torch gate; Electronics sets it at E0 + 0.15 s.
- The PURGE commit rule of LEAD line 175 (3) is stated, together with Combustion's finding on unpurged starts (§1).
- A 3 deg attitude is added, because GNC's specific-force angle exceeds the 2 deg basis (§4).
- A tank-outlet probe is added (§3), and optional run O-3, an unpurged start (§8).

Related documents:
- `02-combustion/REPORT` v2.4a: §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input) and §10 (test plan);
- `interfaces/combustion.json` v2.4a: `purge`, `cf4_gate`, `igniter.sequence` and `purge_commit_rule_v2p4a`. Units are SI except where stated (bar, cm3, g, mm as written).

## 1. Purpose and claim under test

After an A1 coast, vapour collects in the valve-to-seat segment. If too much vapour reaches the pintle at the ignition lift, the main flow is late and the start aborts. The adopted design (LEAD line 164) removes that vapour before the relight with a forced purge. The main valve MV-P opens with the pintle seated, both head-end bleed taps vent for 2.5 s, and the flow stops 0.05 s before T_fire (E0).

**PURGE commit (LEAD line 175 (3), PROVISIONAL).** PURGE commits no later than the plain relight trigger minus 1.7 s; otherwise no purge is run. The withdrawn rule of line 164 had the FC delay T_fire instead.
- Under the provisional rule, a relight without a commit proceeds unpurged.
- Combustion finds that an unpurged start carries a hazard outside its abort model (`unpurged_start_check_v2p4a.json`, SIM/DERIVED):
  - In the PURGE NOT RUN LO worst state, every light (P 0.758) happens inside the first liquid slug.
  - A 23.4 cm3 vapour gap follows that light 0-0.19 s after E2. That is after the drogue-release term (Pc >= 3 bar abs) is already true.
  - The gap drives A3. The ratio during the gap is at most 0.24, against the 0.40 threshold.
- REPORT v2.4a §2.8 has the analysis, and the lead decides the rule. CF-4 tests the purge, not the commit rule. Optional run O-3 (§8) measures the unpurged sequence.

**Claim C-RL.** On CAD v3.4.1 with the decided purge path and 2.5 s of flow ending 0.05 s before E0, at a tilt theta <= 2 deg, an A1 relight lights within the window W 0.65 s with P_abort <= 1e-3, venting <= 76 g of N2O.

The model behind the claim (SIM, `data/v2/v2p4/rg01_line_states_v2p4.json`, `2939549811d4c381`) needs 1.9 s of flow (<= 1.94 s with the FD-01 element) and predicts a vapour pocket of 4.77-8.15 cm3 at the lift after 2.5 s. Its weakest inputs are the cap transport in the lines (slip), the restrictor Cd and the coast vapour generation. CF-4 measures them.

## 2. Hardware

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

Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget.

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

At least 5 runs per state and attitude (sample size ASSUMED; the founders may raise it). In each run the ECU executes PURGE and then the lift to 0.2039 mm. PURGE is commanded at E0 - 2.90 s and gives 2.5 s of flow ending at E0 - 0.05 s; the FC's commit rule (§1) is not under test. The primary measurement is the time from the lift command to the first continuous liquid at the pintle inlet.

## 5. Pass criteria

The claim is closed for the tested states only if P1-P7 hold in every run.

| ID | Criterion | Basis |
|---|---|---|
| P1 | First continuous liquid at the pintle inlet <= 0.293 s after the pintle reaches the 0.2039 mm lift (encoder), i.e. <= 0.32 s after the lift command (t_lift 29.6 ms) | Zero-abort limit V_zero 18.86 cm3 x 0.015555 s/cm3. Model: <= 0.13 s (pocket <= 8.2 cm3) |
| P2 | Then >= 0.35 s of continuous liquid (15 cm3 at the lift flow). A later void is acceptable only inside Table 1 | `cf4_void_budget_v2p4.json` (`6c294cf2dec7af5d`) |
| P3 | The S1 cap and the hump vapour clear the FD-01 crown before the flow ends: the FD-01 crown, riser-top and hump-crown probes read liquid for >= 0.2 s before closure, i.e. the cap clears <= 2.3 s after the flow starts | Model latest 2.27 s (s 0.5 bracket) |
| P4 | Per tap and per phase, from the per-tap flow channel (§3). Each phase is identified by the tap-jet thermocouple and the phase probes. Vapour phase, from the start of flow to the arrival of liquid at that tap: >= 3.4 g/s per tap (80 % of the HEM model, 4.25). Liquid phase: >= 12.5 g/s per tap (80 % of the Dyer model, 15.62). Cd_eff >= 0.56 with V1 and V2 in series, and dP across V1 + V2 <= 11 % of the path total, in each phase. The model reference is the open-element reading. The barrier-element reading is a bracket only: its stall of the T4 tap is a model construct (bubble point about 0.7 kPa against 45.5 bar) that a real T4 will not reproduce, so P4 is not judged against it. A measured T4 stall is a finding: it fails P4 for that tap. | F1: the restrictors control the flow. Brackets: `vented_mass_brackets_v2p4a.json` |
| P5 | N2O vented <= 76 g per run from IS-1 and IS-2 (load cell; model 34-73 g). Model bracket of m(t) for the decided path: open-element minimum = the all-vapour line 8.49 t g until 1.0 s, then 10.4 g at 1.1 s and 44.9 g at 2.5 s; maximum 11.9 g at 0.5 s and 72.9 g at 2.5 s. The all-liquid line 31.24 t (78.1 g at 2.5 s) is never reached, because every record starts with vapour. IS-3 calibrates the path at 2 x 15.62 g/s, about 78 g in 2.5 s; a mass below 80 % of that flags a restricted path | LEAD plan <= 76 g per purge. Brackets: `vented_mass_brackets_v2p4a.json` |
| P6 | (a) Flow stopped by the scheduled end, E0 - 0.05 s (LEAD line 164), read on the pressure downstream of V2. (b) Closure confirmed by the closure deadline on the signal the ECU uses: V1 first, read on P_mid. The deadline is at or before the torch gate, E0 + 0.16 s; Electronics sets it at E0 + 0.15 s (`electronics.json` v2). E1 = torch confirmed 2oo2 AND [closure confirmed OR deadline reached] (LEAD line 166 (3)). (c) A run with one valve held open must raise BLEED_FAULT at the deadline. The flight build then commands V2 closed, the lift proceeds, and BLEED_FAULT goes to the FC as log-only (LEAD line 168). The stand build aborts. | Tests the detection behind A14 and the E1 closure term |
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
- O-3, unpurged start (new). From IS-2 with PURGE not run, lift directly to 0.2039 mm. Record the phase sequence at the pintle inlet for 1.5 s, then compare it with the PURGE NOT RUN LO state: pocket 12.5 cm3, slug 11.2 cm3, gap 23.4 cm3 (`rg01_line_states_v2p4.json`). A sequence with no gap after the first slug refutes Combustion's unpurged-start finding for that state. A gap confirms it.

(The earlier optional run on Mechanical's 15.91 cm3 unreached volume is no longer needed: it was a 10 deg robustness row, 4.84 cm3 at theta <= 2 deg, closed at CHANGELOG line 162.)

## 9. Safety

- Remote operation only; nobody within the exclusion zone set by the founders under local rules (stored-energy inputs in REPORT §9.2).
- N2O vents outdoors, away from people; cold-burn protection for handling (vent temperature -88.5 C).
- Every lockable volume of the stand has a relief; the catch volumes as in §2.
- After the series: the tank is vented remotely and still holds cold liquid until its mass shows otherwise (REPORT §10.2).

## 10. Data to return to Combustion

Raw logs (all channels, time-aligned, with the firmware event log), the run matrix with states and attitudes, the restrictor and element flow-test records, load-cell masses, probe calibration, cleaning records, and any anomaly. Combustion reduces them against P1-P7, re-runs the trade on the measured slip, Cd and element curve, and reports the result through the lead.

## 11. Cost

Valves, restrictors, the FD-01 element, probes, fixtures and catch volumes: TO-QUOTE, delivered to Sønderborg, DK-6400. No price is assumed.
