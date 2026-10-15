# CF-4: relight-purge cold-flow test specification

Version 1.0 (Combustion v2.4), 2026-10-13. Owner of the specification: Combustion and Propulsion. Physical execution: the founders. Status: accepted by the lead as the gate for the A1 relight claim (CHANGELOG line 164); digital specification only, no test has been run. A passing simulation is not a pass of this test.

Related documents: `02-combustion/REPORT` v2.4 §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input), §10 (test plan); `interfaces/combustion.json` v2.4 (`purge`, `cf4_gate`). Units are SI except where stated (bar, cm3, g, mm as written).

## 1. Purpose and claim under test

After an A1 coast, vapour collects in the valve-to-seat segment. If too much vapour reaches the pintle at the ignition lift, the main flow is late and the start aborts. The adopted design (LEAD line 164) removes that vapour before the relight with a forced purge: the main valve MV-P opens with the pintle seated, both head-end bleed taps vent for 2.5 s, and the flow stops 0.05 s before T_fire (E0).

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
- A tilt fixture for 0 and 2 deg, toward azimuth 45 and 180 deg (sensitivity runs at 4 deg).
- Back-pressured catch volumes for the pintle flow and for the vent, each with its own relief valve (set at or below its MAWP, sized for the largest inflow as vapour), a burst disc and a remote vent; the vent catch volume on a load cell.
- All wetted parts cleaned for oxygen service and inspected (REPORT §10.1). No water in this hardware unless followed by drying, re-cleaning and an N2 leak check.

## 3. Instruments (minimum)

- Void or phase probes, response <= 5 ms: pintle inlet, FD-01 crown, T4 crown, riser top, TEE, the two hump crowns at 2 deg, S1 cap region.
- Pressures at >= 1 kHz: tank, P_feed, manifold, upstream of each restrictor, downstream of V2.
- Temperatures: a 0.5 mm sheathed thermocouple in each tap jet; head, hose and module walls; tank liquid.
- Masses: tank load cell; vent catch-volume load cell.
- Valve command and current signatures for MV, V1 and V2; pintle encoder.

## 4. Initial states and runs

Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget.

| State | Description | Role |
|---|---|---|
| IS-1 | Vapour-full segment | HI bound |
| IS-2 | ARM-LO-like: traps full, short slug, cap at S1 | Typical coast state |
| IS-3 | Liquid-primed segment | Calibration reference, not a flight state |

At least 5 runs per state and attitude (sample size ASSUMED; the founders may raise it). In each run the ECU executes PURGE (command at E0 - 2.90 s; 2.5 s of flow ending at E0 - 0.05 s) and then the lift to 0.2039 mm. The primary measurement is the time from the lift command to the first continuous liquid at the pintle inlet.

## 5. Pass criteria

The claim is closed for the tested states only if P1-P7 hold in every run.

| ID | Criterion | Basis |
|---|---|---|
| P1 | First continuous liquid at the pintle inlet <= 0.293 s after the pintle reaches the 0.2039 mm lift (encoder), i.e. <= 0.32 s after the lift command (t_lift 29.6 ms) | Zero-abort limit V_zero 18.86 cm3 x 0.015555 s/cm3. Model: <= 0.13 s (pocket <= 8.2 cm3) |
| P2 | Then >= 0.35 s of continuous liquid (15 cm3 at the lift flow). A later void is acceptable only inside Table 1 | `cf4_void_budget_v2p4.json` (`6c294cf2dec7af5d`) |
| P3 | The S1 cap and the hump vapour clear the FD-01 crown before the flow ends: the FD-01 crown, riser-top and hump-crown probes read liquid for >= 0.2 s before closure, i.e. the cap clears <= 2.3 s after the flow starts | Model latest 2.27 s (s 0.5 bracket) |
| P4 | Each tap passes >= 80 % of the model: liquid >= 12.5 g/s per tap (model 15.62), vapour >= 3.4 g/s (model 4.25); Cd_eff >= 0.56 with V1 and V2 in series; dP across V1 + V2 <= 11 % of the path total | F1: the restrictors control the flow |
| P5 | N2O vented <= 76 g per run from IS-1 and IS-2 (load cell; model 34-73 g). IS-3 calibrates the path at 2 x 15.62 g/s, about 78 g in 2.5 s; a mass below 80 % of that flags a restricted path | LEAD plan <= 76 g per purge |
| P6 | Both bleed valves closed, with the flow stopped, by E0 - 0.05 s, on the signal the ECU uses for closure. A run with one valve held open must raise BLEED_FAULT | Tests the detection behind A14 |
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
