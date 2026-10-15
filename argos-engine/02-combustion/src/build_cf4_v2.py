"""Build CF-4-SPEC v2 (Combustion v2.4a) from the published v1.0 by asserted literal replacements."""
import hashlib, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert hashlib.sha256(s.encode('utf-8')).hexdigest()[:16] == 'c9e1efbb18177155'
R = []
R.append(("Version 1.0 (Combustion v2.4), 2026-10-13. Owner of the specification: Combustion and Propulsion. Physical execution: the founders. Status: accepted by the lead as the gate for the A1 relight claim (CHANGELOG line 164); digital specification only, no test has been run. A passing simulation is not a pass of this test.",
"Version 2.0 (Combustion v2.4a), 2026-10-13. It replaces v1.0, which is archived as `02-combustion/superseded/v2p4/CF-4-SPEC.md`. Owner of the specification: Combustion and Propulsion. Physical execution: the founders. Status: accepted by the lead as the gate for the A1 relight claim (CHANGELOG line 164). This is a digital specification only; no test has been run. A passing simulation is not a pass of this test.\n\n"
"Changes in v2.0:\n"
"- P4 is now defined per tap and per phase, and names the model bracket it is judged against (REV-COMB-2 R2-06).\n"
"- P6 follows the E1 closure term of LEAD line 166 (3). The closure deadline is at or before the torch gate; Electronics sets it at E0 + 0.15 s.\n"
"- The PURGE commit rule of LEAD line 175 (3) is stated, together with Combustion's finding on unpurged starts (§1).\n"
"- A 3 deg attitude is added, because GNC's specific-force angle exceeds the 2 deg basis (§4).\n"
"- A tank-outlet probe is added (§3), and optional run O-3, an unpurged start (§8)."))
R.append(("Related documents: `02-combustion/REPORT` v2.4 §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input), §10 (test plan); `interfaces/combustion.json` v2.4 (`purge`, `cf4_gate`).",
"Related documents:\n"
"- `02-combustion/REPORT` v2.4a: §2.8 (the purge and the integrated trade), §7.3 (sequence), §9.1 (hazards and FMEA input) and §10 (test plan);\n"
"- `interfaces/combustion.json` v2.4a: `purge`, `cf4_gate`, `igniter.sequence` and `purge_commit_rule_v2p4a`."))
R.append(("The adopted design (LEAD line 164) removes that vapour before the relight with a forced purge: the main valve MV-P opens with the pintle seated, both head-end bleed taps vent for 2.5 s, and the flow stops 0.05 s before T_fire (E0).",
"The adopted design (LEAD line 164) removes that vapour before the relight with a forced purge. The main valve MV-P opens with the pintle seated, both head-end bleed taps vent for 2.5 s, and the flow stops 0.05 s before T_fire (E0).\n\n"
"**PURGE commit (LEAD line 175 (3), PROVISIONAL).** PURGE commits no later than the plain relight trigger minus 1.7 s; otherwise no purge is run. The withdrawn rule of line 164 had the FC delay T_fire instead.\n"
"- Under the provisional rule, a relight without a commit proceeds unpurged.\n"
"- Combustion finds that an unpurged start carries a hazard outside its abort model (`unpurged_start_check_v2p4a.json`, SIM/DERIVED):\n"
"  - In the PURGE NOT RUN LO worst state, every light (P 0.758) happens inside the first liquid slug.\n"
"  - A 23.4 cm3 vapour gap follows that light 0-0.19 s after E2. That is after the drogue-release term (Pc >= 3 bar abs) is already true.\n"
"  - The gap drives A3. The ratio during the gap is at most 0.24, against the 0.40 threshold.\n"
"- REPORT v2.4a §2.8 has the analysis, and the lead decides the rule. CF-4 tests the purge, not the commit rule. Optional run O-3 (§8) measures the unpurged sequence."))
R.append(("- A tilt fixture for 0 and 2 deg, toward azimuth 45 and 180 deg (sensitivity runs at 4 deg).",
"- A tilt fixture for 0, 2 and 3 deg, toward azimuth 45 and 180 deg, with sensitivity runs at 4 deg. The 3 deg setting is new; see §4."))
R.append(("- Masses: tank load cell; vent catch-volume load cell.",
"- Masses: tank load cell; vent catch-volume load cell.\n"
"- Per-tap flow: the pressure upstream of each restrictor and downstream of V2, read against that restrictor's own flow test. Each restrictor is flow-tested before assembly in liquid and in vapour, giving a dP-flow curve for each phase. The sum of the two taps must agree with the vent load cell within 10 % (ASSUMED).\n"
"- Tank outlet: a void probe at the tank outlet when the flight tank is used. GNC's liquid mass during the flow is 766-1170 g. The outlet geometry is MISSING (tank not in CAD; REPORT v2.4a §2.8)."))
R.append(("Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget.",
"Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K. Segment heaters set to Mechanical's segment heat budget.\n\n"
"Attitude:\n"
"- The model behind C-RL covers theta <= 2 deg.\n"
"- GNC rev2 re-flown records give the angle between the specific force and the body axis during the purge flow as up to 2.71 deg raw, or 2.65 deg as a 0.1 s mean (`purge_outlet_inputs.json` 47b4deb96ea22043, six records; no 500-run distribution).\n"
"- The model is not computed at 2.7 deg; this is OPEN, and the purge grid was not re-run in v2.4a.\n"
"- CF-4 therefore runs at 3 deg as well as 0 and 2 deg. The 4 deg sensitivity runs bracket it."))
R.append(("At least 5 runs per state and attitude (sample size ASSUMED; the founders may raise it). In each run the ECU executes PURGE (command at E0 - 2.90 s; 2.5 s of flow ending at E0 - 0.05 s) and then the lift to 0.2039 mm.",
"At least 5 runs per state and attitude (sample size ASSUMED; the founders may raise it). In each run the ECU executes PURGE and then the lift to 0.2039 mm. PURGE is commanded at E0 - 2.90 s and gives 2.5 s of flow ending at E0 - 0.05 s; the FC's commit rule (§1) is not under test."))
R.append(("| P4 | Each tap passes >= 80 % of the model: liquid >= 12.5 g/s per tap (model 15.62), vapour >= 3.4 g/s (model 4.25); Cd_eff >= 0.56 with V1 and V2 in series; dP across V1 + V2 <= 11 % of the path total | F1: the restrictors control the flow |",
"| P4 | Per tap and per phase, from the per-tap flow channel (§3). Each phase is identified by the tap-jet thermocouple and the phase probes. Vapour phase, from the start of flow to the arrival of liquid at that tap: >= 3.4 g/s per tap (80 % of the HEM model, 4.25). Liquid phase: >= 12.5 g/s per tap (80 % of the Dyer model, 15.62). Cd_eff >= 0.56 with V1 and V2 in series, and dP across V1 + V2 <= 11 % of the path total, in each phase. The model reference is the open-element reading. The barrier-element reading is a bracket only: its stall of the T4 tap is a model construct (bubble point about 0.7 kPa against 45.5 bar) that a real T4 will not reproduce, so P4 is not judged against it. A measured T4 stall is a finding: it fails P4 for that tap. | F1: the restrictors control the flow. Brackets: `vented_mass_brackets_v2p4a.json` |"))
R.append(("| P5 | N2O vented <= 76 g per run from IS-1 and IS-2 (load cell; model 34-73 g). IS-3 calibrates the path at 2 x 15.62 g/s, about 78 g in 2.5 s; a mass below 80 % of that flags a restricted path | LEAD plan <= 76 g per purge |",
"| P5 | N2O vented <= 76 g per run from IS-1 and IS-2 (load cell; model 34-73 g). Model bracket of m(t) for the decided path: open-element minimum = the all-vapour line 8.49 t g until 1.0 s, then 10.4 g at 1.1 s and 44.9 g at 2.5 s; maximum 11.9 g at 0.5 s and 72.9 g at 2.5 s. The all-liquid line 31.24 t (78.1 g at 2.5 s) is never reached, because every record starts with vapour. IS-3 calibrates the path at 2 x 15.62 g/s, about 78 g in 2.5 s; a mass below 80 % of that flags a restricted path | LEAD plan <= 76 g per purge. Brackets: `vented_mass_brackets_v2p4a.json` |"))
R.append(("| P6 | Both bleed valves closed, with the flow stopped, by E0 - 0.05 s, on the signal the ECU uses for closure. A run with one valve held open must raise BLEED_FAULT | Tests the detection behind A14 |",
"| P6 | (a) Flow stopped by the scheduled end, E0 - 0.05 s (LEAD line 164), read on the pressure downstream of V2. (b) Closure confirmed by the closure deadline on the signal the ECU uses: V1 first, read on P_mid. The deadline is at or before the torch gate, E0 + 0.16 s; Electronics sets it at E0 + 0.15 s (`electronics.json` v2). E1 = torch confirmed 2oo2 AND [closure confirmed OR deadline reached] (LEAD line 166 (3)). (c) A run with one valve held open must raise BLEED_FAULT at the deadline. The flight build then commands V2 closed, the lift proceeds, and BLEED_FAULT goes to the FC as log-only (LEAD line 168). The stand build aborts. | Tests the detection behind A14 and the E1 closure term |"))
R.append(("They settle open disagreements, not the claim:\n- Generation runs: MV closed, heated hold at the LO and HI budgets, void growth of the full head trap. This settles the wet and dry readings.\n- The SIL's 0.17 s prep-path purge credit.",
"They settle open disagreements, not the claim:\n- Generation runs: MV closed, heated hold at the LO and HI budgets, void growth of the full head trap. This settles the wet and dry readings.\n- The SIL's 0.17 s prep-path purge credit.\n"
"- O-3, unpurged start (new). From IS-2 with PURGE not run, lift directly to 0.2039 mm. Record the phase sequence at the pintle inlet for 1.5 s, then compare it with the PURGE NOT RUN LO state: pocket 12.5 cm3, slug 11.2 cm3, gap 23.4 cm3 (`rg01_line_states_v2p4.json`). A sequence with no gap after the first slug refutes Combustion's unpurged-start finding for that state. A gap confirms it."))
for a, b in R:
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
open(out, 'w', encoding='utf-8').write(s)
print('wrote', out, hashlib.sha256(s.encode('utf-8')).hexdigest()[:16])
