# REVISION-RESPONSE-R3: Combustion v2.4b answer to REV-COMB-3

v2.4c note (2026-10-21, lead): this file records the v2.4b answer to REV-COMB-3. REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`, `2908321d7f75d439`) closed all 17 R3 items (10 CLOSED, 7 CLOSED WITH RESIDUAL); the v2.4c corrections are listed in REPORT §17 and annotated in place below (row R3-01, §6 point 3, §9 item 3). The line references resolve against the v2.4b files as answered: REPORT, CF-4 and T1-T4 keep their line numbers in v2.4c (in-place edits), and `combustion.json` v2.4b is kept as `02-combustion/superseded/v2p4b/combustion.json`. Superseded since: the 112 bar abs proof texts (row R3-10, §6 point 1) by >= 166.14 bar abs (LEAD 249 (4)), and the ABORT time of row R3-09 (0.5 s after E2) by 0.8 s after E2 (LEAD 227 (5)). Version v2.4b, 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228 and the lead requests of 2026-10-19 in §9). Author: Combustion and Propulsion. Answers `reviews/REVIEW-COMBUSTION-R3.md` (REV-COMB-3, REVISE (targeted),
`a786101f28d45d6f`) on REPORT v2.4a (`062e307a8d25e1ec`). Answering files (sha256/16): `02-combustion/REPORT.md` v2.4b (`d8b795478d4013ee`),
`interfaces/combustion.json` v2.4b (`fd3a7da6d27c7c66`), `02-combustion/CF-4-SPEC.md` v2.1 (`60bbc51f6f487682`),
`02-combustion/T1-T4-REGRESSION-SPEC.md` v3 (`b0c42b09ba47cb9c`), `02-combustion/DATASHEET-INPUTS-COMBUSTION.md` (`46a8222018666b1d`), data in `02-combustion/data/v2p4b/` (`HASHES.txt`). References are
1-based lines of those files, resolved by `src/build_response_r3_v2p4b.py` at build time (combustion.json as written, indent 1).

This is the author's statement. A reviewer other than the author records criteria and verdict. Status words: ADDRESSED (changed as asked
or as the lead decided); CONTRADICTION KEPT (a remaining disagreement recorded for the lead); PARTLY / OPEN (data or a decision outside
Combustion is needed). No test, hash match or rendered table here is physical approval.

## 1. Findings R3-01 to R3-17

| Item | Severity | Status | Change | Where |
|---|---|---|---|---|
| R3-01 | MAJOR | ADDRESSED | The "E2 + 0.22 s" hold came from one state; the lead withdrew it (194 (3)). Table 2.18 now gives the hold over all 2160 PURGE NOT RUN records by command profile: 0.30 s at zero residual on the 2500 N/s ramp to 200 N unlined and 0.31 s lined (latest A3 trip 0.282 / 0.290 s + one 10 ms frame, rounded up to 10 ms; v2.4c wording, REV-COMB-4 R4-14), 0.19 s on the ramp to 500 N, and none inside W with the flow held (0.75 s). Counted from the ECU E2 the holds move by at most +14.7 ms. The per-record classes of all three profiles are published as data; the unpurged alternative is NOT ADOPTED (204 (2)). | `REPORT.md:45`; `REPORT.md:817`; `REPORT.md:2787`; `REPORT.md:2797`; `REPORT.md:2635`; `combustion.json:8423` (`release_hold_v2p4b`); `combustion.json:6640` (`drogue_release_hold.v.line175_5_note_v2p4a_superseded`); `data/v2p4b/release_hold_v2p4b.json` (`a926426da0e6e436`); `data/v2p4b/release_hold_records_v2p4b.csv` (`59e7f44e44fbfeef`) |
| R3-02 | MAJOR | ADDRESSED; CONTRADICTION KEPT (OI-41) | Head and aft equivalent-pressure spectra to 50 ms on the 896 FA-1 cases, dense below 1 ms; the load rule carries the period domain of LEAD 194 (1). The dense all-case values exceed the 194 (1) numbers below 1 ms (93.6 bar abs at T <= 0.1 ms against 90; 120.3 bar abs at 0.1-1 ms against 93 / 102; baseline 88.6 and 102.5). Kept for the lead (OI-41). | `REPORT.md:46`; `REPORT.md:2097`; `REPORT.md:2560`; `REPORT.md:2636`; `combustion.json:9056` (`fa1_spectra_v2p4b`); `combustion.json:7134` (`fa1_envelope_v2p4a.v.structural_load_LEAD_173_superseded`); `data/v2p4b/fa1_spectra_dense_v2p4b.json` (`7468996959538d0f`) |
| R3-03 | MINOR | ADDRESSED | Long-period thrust spectrum published (all cases, Cf 1.35: 1743 N at 25 ms, 1452 N at 40 ms, 1032 N at 100 ms). The 1.8 kN x 4 ms rectangle bounds T <= 20 ms (minimum ratio 1.077); the spectrum governs above it (LEAD 194 (2)). | `REPORT.md:2111`; `combustion.json:9056` (`fa1_spectra_v2p4b`); `data/v2p4b/fa1_thrust_spectra_dense_v2p4b.csv` (`072f2e0f2987fda5`) |
| R3-04 | MINOR | ADDRESSED by LEAD 194 (1); see OI-41 | Line 194 (1) replaced 92 by 93 bar abs (yield) with 102 bar abs (ultimate) for 0.1-1 ms paths. The dense 0.1-1 ms values (baseline 102.5, all cases 120.3 bar abs) lie above 93; recorded in OI-41. | `REPORT.md:2091`; `REPORT.md:2560` |
| R3-05 | MINOR | ADDRESSED (closure is physical: CF-3) | The 16.31 N margin is stated CONDITIONAL on Cd x A x G at the start lift (factor 1.22-1.31). CF-3 start-lift acceptance: F <= 16.31 N minus the heat allowance, or mdot <= 52.6-56.3 g/s with no heat allowance. | `REPORT.md:1837`; `REPORT.md:2557`; `combustion.json:9287` (`cold_flow_start_lift_v2p4b`); `data/v2p4b/cold_flow_start_lift_v2p4b.json` (`28ce48092f33da1b`) |
| R3-06 | MINOR | ADDRESSED | T1-T4 v3: the flux test is two-sided; a signature below the oxidiser-flux band reads "neither shown" (LEAD 194 (8)). | `T1-T4-REGRESSION-SPEC.md:43`; `T1-T4-REGRESSION-SPEC.md:30`; `combustion.json:7228` (`t1t4_law_v2.v.spec_superseded`); `combustion.json:9882` (`specs_v2p4b`) |
| R3-07 | MINOR | ADDRESSED; stand tank MISSING | T1-T4 v3 adds red lines and aborts, validity of short or aborted firings, the char and melt-layer procedure, and counts and N2O (T1 at 2t = 8 s uses 1.928 kg, 96.4 % of a 2.0 kg flight load; 2t <= 6.04 s on a flight-size tank). The founders' stand tank is MISSING. | `T1-T4-REGRESSION-SPEC.md:223`; `T1-T4-REGRESSION-SPEC.md:254`; `T1-T4-REGRESSION-SPEC.md:266`; `T1-T4-REGRESSION-SPEC.md:279`; `data/v2p4b/test_budgets_v2p4b.json` (`c0e4ce35659f21fa`) |
| R3-08 | MINOR | ADDRESSED; model numbers on CAD v3.4.1 until the v3.5.1 purge re-run | CF-4 v2.1: §1 states the decided commit rule; the hardware baseline is the frozen v3.5.1 bleed path; §4.1 IS-1 to IS-3 preparation and verification; §5.1 the continuous-liquid probe threshold; §9.1 red lines; §12 runs and N2O (59 / 75 / 105 runs, 10.0 / 12.7 / 17.8 kg). | `CF-4-SPEC.md:5`; `CF-4-SPEC.md:80`; `CF-4-SPEC.md:119`; `CF-4-SPEC.md:161`; `CF-4-SPEC.md:185`; `combustion.json:6489` (`cf4_gate.spec_version_superseded`) |
| R3-09 | MINOR | ADDRESSED | Line 181 (2): "the 0.81 s plan holds" is scoped to the predictor path with PURGE committed. Line 181 (4): ABORT at t_E2 + 0.5 s. Line 177 (1)/178: H19 is recomputed for the Inconel 718 lip (lumped 1.10-5.88 s from 342 C; 1 mm depth 5.21-33.92 s). | `REPORT.md:529`; `REPORT.md:1807`; `REPORT.md:1700`; `REPORT.md:2287`; `combustion.json:9540` (`nozzle_lip_melt_in718_v2p4b`); `combustion.json:6601` (`nozzle_joint.v.lip_melt_s_superseded`); `data/v2p4b/nozzle_lip_melt_in718_v2p4b.json` (`23b85b7febb90c60`) |
| R3-10 | MINOR | ADDRESSED | Stand dynamic Pc channel: range >= 100 bar abs; proof >= 112 bar abs flush-mounted (103 needed), >= 132 bar abs for a 0.1-1 ms path; a path period above 1 ms is not acceptable (LEAD 194 (7)). | `REPORT.md:50`; `REPORT.md:2553`; `combustion.json:7166` (`pc_dynamic_channel.v.stand_proof_rating_v2p4b`) |
| R3-11 | NOTE | ADDRESSED | Every item of review §7 (ii) is replaced: the PROVISIONAL rule by L* = 1.3 s; OI-31 closed; OI-38 adopted with the margin CONDITIONAL; OI-40 decided; the configuration notes updated. Old values are kept under `*_superseded` keys and in REPORT §13. | `REPORT.md:39`; `REPORT.md:2550`; `REPORT.md:2557`; `REPORT.md:2559`; `REPORT.md:66`; `combustion.json:7366` (`purge_commit_rule_v2p4a.v.rule_LEAD_175_3_superseded`); `combustion.json:6438` (`fmea_input.v.bleed_superseded`); `combustion.json:6452` (`fmea_input.v.flameout_pc_invalid_v2p4a_superseded`); `combustion.json:8283` (`cold_flow_thrust_v2p4a.v.proposal_superseded`); `combustion.json:8305` (`throat_insert_line183_note_v2p4a.v_superseded`); `CF-4-SPEC.md:5` |
| R3-12 | NOTE | ADDRESSED | The release is read on the firmware release term (Pc valid and >= 3.0 bar abs) with the ECU's relative E2 rule (§15.5); the lift basis is one definition, THE start-level lift h_s(T) (§15.3). | `REPORT.md:789`; `REPORT.md:2769`; `REPORT.md:2787`; `combustion.json:8909` (`E2_rule_v2p4b`); `combustion.json:9342` (`start_level_lift_v2p4b`) |
| R3-13 | NOTE | ADDRESSED | The population statements are counted per command profile. | `REPORT.md:53`; `REPORT.md:816`; `data/v2p4b/population_statements_v2p4b.json` (`bffabc97aee6a5cb`) |
| R3-14 | NOTE | ADDRESSED; injector-body temperature TO-VERIFY | The heat that matters is added at tank pressure (injector-body and feed soak-back at the relight). The R2 lit thrust is the grain_q1d start-level history (Table 7.3b: 33.1-71.0 N between E2 and E2 + 0.5 s at 0.21776 mm, 3 of 72 corners below 37.16 N), not 62.5 N x pcf_k. | `REPORT.md:1839`; `REPORT.md:1842`; `combustion.json:8295` (`cold_flow_thrust_v2p4a.v.line194_4_heat_location_v2p4b`); `combustion.json:9491` (`start_level_lit_thrust_v2p4b`); `combustion.json:6646` (`drogue_release_hold.v.line194_4_lit_history_v2p4b`) |
| R3-15 | NOTE | ADDRESSED; consequence recorded for the lead | The prediction is a script and parameters hashed before the firing; only the logged inputs come from the firing. Consequence: at the literature erosion rate, firing 1 would count as a refutation (8.4-13.6 % against 1.9 % predicted). | `REPORT.md:2898`; `REPORT.md:2567`; `T1-T4-REGRESSION-SPEC.md:311`; `combustion.json:9896` (`nz01_criterion_v2p4b`) |
| R3-16 | NOTE | ADDRESSED | Wording per LEAD 194 (5): 766 g remains at the end of the purge flow, 9.3-9.7x the 78.6-82.5 g that 13.6 mm holds. | `REPORT.md:267`; `REPORT.md:2645`; `combustion.json:7423` (`tank_outlet_coverage_v2p4a.v.min_liquid_for_quasistatic_coverage_g.margin_superseded`) |
| R3-17 | NOTE | ADDRESSED; outlet geometry MISSING (OI-32) | Dip onset by thrust level (Lubin-Springer, LITERATURE; N2O applicability TO-VERIFY): 60.3-62.0 g at 125 N, 67.9-69.9 g at 250 N, 78.3-80.6 g at 500 N (283-289.5 K). GNC fixed its onset at 80 g (LEAD 208 (1)). | `REPORT.md:271`; `REPORT.md:2892`; `combustion.json:9683` (`tank_outlet_dip_v2p4b`); `data/v2p4b/tank_outlet_dip_v2p4b.json` (`6c11d3c19afe983c`) |

## 2. R2 items (review §2)

| Item | R3 status | v2.4b status | Change | Where |
|---|---|---|---|---|
| R2-03 | PARTLY | ADDRESSED through R3-02 and R3-03 | Pressure spectrum to 50 ms; thrust domain stated (LEAD 194 (2)). | `REPORT.md:2097`; `REPORT.md:2111` |
| R2-09 | PARTLY | ADDRESSED through R3-09 | The 316L lip text is replaced by the IN718 values. | `REPORT.md:1700` |
| R2-11 | PARTLY | PARTLY | The design value follows LEAD 194 (1) (R3-04); the 1-D FA-1 run stays OPEN (OI-36). | `REPORT.md:2555` |
| R2-13 | CONFIRMED (notes stale) | ADDRESSED through R3-11 | Configuration paragraph rebuilt. | `REPORT.md:66` |
| R2-01, R2-02, R2-04 to R2-08, R2-10, R2-12 | CONFIRMED or CLOSED | No change | R2-04's new defects are R3-06 and R3-07; R2-10's channel range is R3-10; OI-33 stays open (R2-07). | `REPORT.md:2553` |

## 3. Review §6 and §7

- §6 (1)-(5): the line-186 decisions are folded as decided; the GNC alternative hold is withdrawn (194 (3)); the parenthetical that described
  LO only is restated per profile (R3-13); the heat location is corrected (R3-14); the NZ-01 prediction is frozen (R3-15); the outlet
  wording follows 194 (5) (R3-16). §6 (4): mechanical.json v2.2 is not yet in the hub (v2.1 read; OI-37).
- §7 (i): R3-09. §7 (ii): R3-11. The review found no stale "300 m" hit in v2.4a; after LEAD line 213 the A1 values are labelled as
  300 m / 285 m comparators (`REPORT.md:2922`).

## 4. Lead lines folded (`combustion.json:11036` (`lead_decisions_folded_v2p4b`); REPORT `REPORT.md:2734`)

| Line | Fold |
|---|---|
| 186 (1) | L* = 1.3 s ADOPTED: purge_commit_rule_v2p4b; igniter start[0]; fmea B-5/B-6 |
| 186 (2) | R2 command hold ADOPTED: cold_flow_thrust_v2p4a.proposal; fmea B-7; drogue_release_hold |
| 186 (3) | NZ-01 criterion: throat_insert_line183_note_v2p4a; nz01_criterion_v2p4b (wording of 194 (5)) |
| 186 (4) | interface configuration: open_items_v2p4b OI-37 (mechanical.json v2.2 not yet in the hub) |
| 186 (5) | tank outlet wording (194 (5)): tank_outlet_coverage_v2p4a margin; tank_outlet_dip_v2p4b |
| 194 (1)-(2) | FA-1 period domain and thrust domain: fa1_envelope_v2p4a.structural_load_LEAD_173; fa1_spectra_v2p4b (OI-41) |
| 194 (3) | E2 + 0.22 s withdrawn; population hold table: release_hold_v2p4b; per-record classes |
| 194 (4) | margin CONDITIONAL; CF-3 start-lift point; heat location; lit history: cold_flow_start_lift_v2p4b, start_level_lit_thrust_v2p4b |
| 194 (5) | wording of 186 (3) and 186 (5) |
| 194 (6) | outlet dip for GNC: tank_outlet_dip_v2p4b |
| 194 (7) | stand dynamic channel >= 100 bar abs with proof rating: pc_dynamic_channel.stand_proof_rating_v2p4b |
| 194 (8) | T1-T4 v3, CF-4 v2.1, budgets: specs_v2p4b, test_budgets_v2p4b |
| 194 (9) | stale text replaced (*_superseded keys); H19 for IN718: nozzle_lip_melt_in718_v2p4b |
| 203 (3) | purge flow basis and the 2.55 s cap: purge_basis_v2p4b (OI-42) |
| 203 (7) | THE start-level lift: start_level_lift_v2p4b (OI-43) |
| 204 (2) | unpurged alternative NOT ADOPTED; classes published as data (release_hold_v2p4b) |
| 204 (4) F11 | A1 duration: a1_duration_note_v2p4b |
| 205 | Pc port passage gas sound speed: pc_port_gas_v2p4b (OI-45); flight Pc reselection in igniter arm_preconditions and pc_dynamic_channel |
| 213 (founder) | A1 apogee target about 210 m: a1_apogee_target_v2p4b; line213_note in the A1-profile blocks; CF-4 v2.1 §4 note |
| 208 (1), (3) (cross-reference) | dip onset fixed at 80 g and the ~80 g purge arm: a1_apogee_target_v2p4b.line208_cross_references; NOT ADOPTED strengthened: no change |
| relay items 1-7 of 203-204 | purge_basis_v2p4b, start_level_lift_v2p4b, E2_rule_v2p4b, firmware_constant_sources_v2p4b, fa1_spectra_v2p4b, release_hold_v2p4b.per_record_classes, a1_duration_note_v2p4b |
| 214 | A1 apogee target 210 m DECIDED: a1_apogee_target_v2p4b.v.target.status; CF-4 v2.1 §4; REPORT §16.1, §16.8 |
| 215 | REV-ELEC-2 result: read (Electronics v2.11); no Combustion change |
| 216 (5) | ONE purge flow basis 29.25 g/s: purge_basis_line216_v2p4b; purge_basis_v2p4b.v.answer; CF-4 P5; REPORT §16.5; OI-42 |
| 216 (9) | start-level lift 0.21776 mm at the A1 relight state: start_level_lift_v2p4b.v.line216_9; REPORT §16.6 |
| 216 (other) | Electronics items (v2.11): read; THE start-level lift stays the hold lift (OI-43) |
| 217, 220, 224, 226 | FEA3D results: read for status; shares and break-even used from 221 / 225 (fa1_per_mode_peq_v2p4b) |
| 218 | GNC rev4 staged: read (v32_proposals_rev4 item [15] T/W for the 2.20 kg option; burn p99 at 210 m via 227 (9)) |
| 219 | tank stays 2.00 kg (founder); 2.20 kg option: tank_2p20kg_option_v2p4b; OI-50 |
| 221, 225 | FEA3D modal shares (published subset) and FA-1 columns: fa1_per_mode_peq_v2p4b; OI-51 |
| 222 | ICD-AIRFRAME removed from scope: the two v2.4b references (REPORT §7.6 thrust note; fa1_spectra_v2p4b.v.thrust.rule) restated; no other change |
| 223 | TC-01 J-FWD a 0.1-1 ms path, PROVISIONAL: the Combustion side of condition (a) in fa1_per_mode_peq_v2p4b (shares are FEA3D) |
| 227 (1), (5), (8) | 210 m accepted; R2 starve window 0.8 s (P4c window: p4c_lit_side_v2p4b); RV6-03 gate-delay arm is a GNC item |
| 227 (9) | A1 duty cycle does not shorten (RV6-05): a1_apogee_target_v2p4b.v.statements A1-1; 2.20 kg TO-VERIFY: tank_2p20kg_option_v2p4b |
| 228 | third condition on TC-01: fa1_spectra_damped_v2p4b (published head spectrum, damping stated), fa1_per_mode_peq_v2p4b (per-mode Peq); band values restatement proposed (OI-41) |

## 5. Coordinator relays: lines 203-204 (items 1-7), 205 and 213

| Relay | Question | Answer | Where |
|---|---|---|---|
| 203-204 item 1 | Purge flow basis (SIL 32.0 vs 29.8 g/s); vented mass at 2.5 s and at the 2.55 s cap | Neither constant rate: record basis M(2.5 s) <= 72.93 g; 76.05 g at 2.60 s of flow (the 2.55 s both-open cap with the 0.05 s offset), at the 76 g limit (OI-42). Line 216 (5) then asked for ONE basis: 29.25 g/s (§9). | `REPORT.md:2860`; `REPORT.md:2561`; `combustion.json:8322` (`purge_basis_v2p4b`) |
| 203-204 item 2 | THE start-level lift | h_s(T) = the ignition-lift row at the E0 tank temperature: 0.2039 mm at 20 C, 0.21776 mm at the A1 relight state; the ECU hold lift 0.2154 mm is retired (OI-43). | `REPORT.md:2769`; `REPORT.md:2562`; `combustion.json:9342` (`start_level_lift_v2p4b`) |
| 203-204 item 3 | E2 model against the ECU relative rule | The ECU E2 is earlier than the model E2 by at most 14.7 ms; holds from the ECU E2 are given (OI-44). | `REPORT.md:2787`; `REPORT.md:2563`; `combustion.json:8909` (`E2_rule_v2p4b`) |
| 203-204 item 4 | Source text for 2500 N/s, 0.5 s, 5 bar abs and 0.12 s; FLAMEOUT_OPT in the cold_flow text | Written (OI-46). | `REPORT.md:2880`; `REPORT.md:2565`; `combustion.json:9909` (`firmware_constant_sources_v2p4b`) |
| 203-204 item 5 | FA-1 head spectrum near 6 ms; histories beyond 25 ms | Values near 6 ms and the history limits are given; the head stays at 3.78-22.13 bar after 25 ms. | `REPORT.md:2814`; `combustion.json:9056` (`fa1_spectra_v2p4b`) |
| 203-204 item 6 | Per-record classes for the 500 N ramp | Published as data for all three profiles (the alternative is NOT ADOPTED). | `REPORT.md:2797`; `combustion.json:8423` (`release_hold_v2p4b`) |
| 203-204 item 7 | A1_none p99 8.375 s against the 8.258 s cycle | No A1 statement changes (web >= 4.24 mm; B1 governs). | `REPORT.md:2909`; `combustion.json:9950` (`a1_duration_note_v2p4b`) |
| 205 | Gas sound speed in the Pc port passage at the FA-1 instant | c >= 181 m/s if the passage holds no liquid N2O (near-critical N2O); 202 m/s for N2O compressed from saturation; products 1049-1136 m/s. Combustion cannot bound c better than 222-400 m/s in the direction that matters; the gas-filled lower end is below 222 m/s and two-phase N2O is unbounded (OI-45). | `REPORT.md:2820`; `REPORT.md:2564`; `combustion.json:9959` (`pc_port_gas_v2p4b`) |
| 213 | A1 apogee target about 210 m (founder decision; DECIDED by 214, 227 (1)) | The 300 m and 285 m A1 values are kept as comparators; no 210 m record yet. Directions: the A1 duty cycle does not shorten (line 227 (9), RV6-05, corrects 213); warmer relight state at the same launch temperature, so the purge mass rises by about 0.66 g per K above 289.5 K (76 g on the 2.5 s schedule up to 294.21 K) and the start-level cold-flow bound rises (below 16.31 N to 298.15 K) (OI-49). | `REPORT.md:56`; `REPORT.md:2922`; `REPORT.md:2568`; `CF-4-SPEC.md:66`; `combustion.json:10680` (`a1_apogee_target_v2p4b`); `data/v2p4b/a1_profile_line213_v2p4b.json` (`46b6a1c6efec0351`) |

Line 208 (read; cross-references, no Combustion change): 208 (1) fixes the GNC onset at 80 g ("upper end of the R3-17 bracket"); v2.4b Table 2.4b gives 78.3-80.6 g at 500 N over 283-289.5 K and 82.9-83.6 g at 270 K. 208 (1) sensitivity arm "~80 g purge": on the 289.5 K basis 80 g is reached at 2.726 s of flow; at 2.60 s of flow (the 2.55 s cap) 80 g is reached at a relight state of 295.40 K; on the 2.5 s schedule 80 g is not reached up to 298.15 K. 208 (3) strengthens 204 (2) NOT ADOPTED; no Combustion change.

## 6. Points for the lead

1. OI-41: the published all-case FA-1 spectrum exceeds the 194 (1) values below 1 ms (`REPORT.md:3001`); the lead's flight Pc proof of 112 bar abs
   (1.1 x 102) becomes 132 bar abs on the all-case 0.1-1 ms value. Proposed (`REPORT.md:3037`): restated band values 94 / 121 / 147 / 94 bar abs, or the
   per-mode rule (E rule until FEA3D's share vector, OI-51). Which applies is the lead's call.
2. OI-42: ONE flow basis 29.25 g/s (line 216 (5)); the 2.55 s both-open cap gives 76.05 g on the Combustion bound; a strict 76 g needs
   both-open <= 2.548 s until CF-4 / B-BLEED-1 measure the flow (then overlap <= 76 g / mdot_measured - (t_close - t_open)). The bleed
   Cd is ASSUMED (+-0.7 g per 1 %).
3. Release hold for GNC P6c: 0.30 s is the zero-residual value on the ramp to 200 N; Table 2.18 lists 0.31 s with the 10 ms frame margin. [v2.4c, REV-COMB-4 R4-14: every Table 2.18 value already includes the frame: H >= 0.30 s unlined / 0.31 s lined on the 2500 N/s ramp to 200 N (latest A3 trip 0.282 / 0.290 s + one 10 ms frame, rounded up to 10 ms).]
   The alternative is NOT ADOPTED, so this matters only if GNC flies the comparator.
4. NZ-01 (R3-15): under the decided rule, an erosion at the literature rate on firing 1 counts as a refutation (a conservative false
   refutation), recorded, not changed.
5. Lines 213 / 214: at the same launch temperature a 210 m relight state is warmer than the 289.5 K basis; the purge mass then rises by about
   0.66 g per K and the 2.55 s cap, already at 76 g, exceeds it. GNC's 210 m record settles the
   magnitude (OI-49).
6. Line 208 (1): GNC's fixed onset of 80 g is inside the 500 N bracket at 283-289.5 K (78.3-80.6 g) and below the 270 K row (82.9-83.6 g);
   the 300 m records end the landing burn at 277.66-284.50 K. Whether 80 g bounds the onset depends on the
   thrust when the liquid runs low (GNC).
7. The IN718 datasheet PDF could not be archived: the proxy refused the download from www.specialmetals.com; the values were read through
   the web-fetch reader (OI-47).
8. Line 228 (c): at TC-01 J-FWD the time-domain modal bound is 114.6 bar abs undamped against the 116.3 / 125.8 bar abs
   break-even (MS +0.015 / +0.097; it holds the yield margin while the residual's absolute share is <= 0.487
   against its published signed 0.382); its E-rule form 127.0 and the absolute spectral sum (137.3-147.9) exceed the yield break-even. With the restated
   band value 121 bar abs J-FWD reads MS -0.039 / +0.040 (line 228 lists +0.25 / +0.23 on 93 / 102). The signed spectral sum is an
   interval (101.5-109.4) because FEA3D publishes 9 of 60 shares (OI-51); damping is ASSUMED (OI-52).
9. Line 227 (9): the A1 duty cycle does not shorten; first order the nominal A1 throat-area growth is 1.90 % per flight at 210 m
   (2.00 kg) and up to 2.20 % with the 2.20 kg option, above the NZ-01 2 % criterion (OI-40, OI-50).

## 7. Failures kept as evidence

- Lead-items script, first runs: a format-string error; then no N2O thermal-conductivity model in CoolProp (fixed with an ASSUMED 0.10 W/m K
  upper bound, recorded); then a Pc-passage minimum taken at two pressures only (201 m/s), replaced by the dense minimum (181 m/s) before
  any value was used.
- Population-statement script: a lining-label mismatch (division by zero); fixed by matching the CSV label.
- Interface writer: a first build dropped sub-keys of replaced dicts; fixed so every v2.4a key is kept (3227 of 3227).
- Report builder: a literal percent sign in a formatted string; fixed before output.
- Line-213 patch: a first patch of the interface writer named a line that was not duplicated; no output was written; re-applied.

## 8. Checkpoint

The full checkpoint (claim, configuration, sources, files, tests, unknowns, next closure) is in REPORT §0 (`REPORT.md:66`
and the paragraphs around it). Nothing here is physical approval.

## 9. Final fold (2026-10-19): lead lines 214-228 and the lead requests of 2026-10-19

| Item | Request | Answer | Where |
|---|---|---|---|
| 2026-10-19 item 1 | FA-1 spectra as data (head / aft, T 0.02-50 ms, zeta 0 / 0.02 / 0.05, baseline and all cases; thrust >= 200 ms); state the contradiction with 194 (1); restated band values or a per-mode rule | Published as CSV and JSON. Head, all cases, zeta 0: 93.6 bar abs at T <= 0.1 ms (194 (1): 90) and 120.3 at 0.1-1 ms (115.4 at zeta 0.02; 194 (1): 93 / 102): the band values are below the all-case spectrum. Proposed: 94 / 121 / 147 / 94 bar abs, or the per-mode rule (time-domain modal bound; E rule until the share vector). | `REPORT.md:3001`; `REPORT.md:3037`; `REPORT.md:2560`; `combustion.json:11320` (`fa1_spectra_damped_v2p4b`); `data/v2p4b/fa1_pressure_spectra_published_v2p4b.csv` (`a2c380515cada638`); `data/v2p4b/fa1_pressure_spectra_modal_periods_v2p4b.csv` (`34ff45e392ea9d6b`); `data/v2p4b/fa1_spectra_damped_v2p4b.json` (`3a84a905052d5364`); `data/v2p4b/fa1_thrust_spectra_dense_v2p4b.csv` (`072f2e0f2987fda5`) |
| 2026-10-19 item 2; line 228 (c) | TC-01 per-mode Peq = sum share_i x S(T_i) at J-FWD and LC1; zeta 0 and a justified damping; absolute sum and SRSS; x0.85 / 0.90 / 1.00; residual at the maximum below 0.195 ms; TC-02 / TC-09 / NZ-01 if cheap; say what is missing | J-FWD, zeta 0, worst factor: signed 101.5-109.4, absolute 137.3-147.9, SRSS 55.7-58.1 bar abs (intervals: 9 of 60 shares published); time-domain modal bound 114.6 (108.9 at zeta 0.02, ASSUMED), E rule 127.0; break-even 116.3 / 125.8. Missing: the FEA3D 60-mode share vector per node (OI-51). TC-02, TC-09, NZ-01: spectral sums given. | `REPORT.md:3054`; `REPORT.md:2570`; `REPORT.md:2571`; `combustion.json:11490` (`fa1_per_mode_peq_v2p4b`); `data/v2p4b/fa1_per_mode_peq_v2p4b.json` (`7ade3ee7ef544f7a`); `data/v2p4b/fa1_modal_th_bound_v2p4b.json` (`639f5fbf3db77ee8`); `data/v2p4b/fa1_relative_spectrum_E_v2p4b.csv` (`eead7123600db8d4`) |
| 2026-10-19 item 3 | GNC P4c lit side and the pcf_tmax proposal, as data with tags | At 0.21776 mm: F min 33.14 N in the 0.5 and 0.8 s windows; 3 of 72 corners never reach 37.16 N, the others by E2 + 0.205 s (+3 frames 0.235 s); pcf_tmax 0.8 s is not limited by the lit side [v2.4c, REV-COMB-4 R4-03: one of the 3 corners (Cd 0.65, a 0.6, n 0.68, ri 0.3, eta 0.85) crosses 37.16 N at E2 + 0.857 s; the other two stay below it to the end of the 1.0 s record (36.33 / 36.80 N, still rising); the count is the same for every window from 0.235 to 0.857 s, so the conclusion stands]. | `REPORT.md:3109`; `combustion.json:11260` (`p4c_lit_side_v2p4b`); `data/v2p4b/p4c_lit_side_v2p4b.json` (`12f7699ddbeeecda`) |
| 2026-10-19 item 4; 219, 227 (9) | 2.20 kg tank: B1 / thermal / erosion impact if cheap, else an open item with an owner | First-order A1 estimate (no run): nominal throat-area growth up to 2.20 % per flight; B1 with 2.20 kg not covered: OI-50 (GNC records; Combustion re-run; Mechanical tank / structure). | `REPORT.md:3122`; `REPORT.md:2569`; `combustion.json:11890` (`tank_2p20kg_option_v2p4b`); `data/v2p4b/tank_2p20kg_option_v2p4b.json` (`59995244124f7c9a`) |
| 2026-10-19 item 5 | out_v2p4b/DATASHEET-INPUTS-COMBUSTION.md: one table of the headline engine numbers with tags | Published (`02-combustion/DATASHEET-INPUTS-COMBUSTION.md`). | `REPORT.md:3138`; `combustion.json:12029` (`datasheet_inputs_v2p4b`) |
| 216 (5) | ONE purge flow basis (g/s) with derivation and uncertainty | 29.25 g/s = 76 g / 2.5982 s of flow at 289.5 K; 27.58-31.06 g/s over the relight states; measured-time cap after CF-4. | `REPORT.md:3099`; `REPORT.md:2561`; `combustion.json:11206` (`purge_basis_line216_v2p4b`); `combustion.json:8418` (`purge_basis_v2p4b.v.answer_superseded`); `CF-4-SPEC.md:102`; `data/v2p4b/purge_basis_line216_v2p4b.json` (`ca2ee1f0ea0f0194`) |
| 216 (9) | the start-level lift as a LIFT value at the A1 relight state | 0.21776 mm (ECU table row, DESIGN; model -0.056 %); TO-VERIFY at CF-3. | `REPORT.md:3105`; `REPORT.md:2780`; `combustion.json:9478` (`start_level_lift_v2p4b.v.line216_9`) |
| 214, 227 (1), 227 (9) | A1 = 210 m decided; "A1 duty cycle shortens" corrected (RV6-05) | A1 values stay comparators; corrected in place; first-order values. | `REPORT.md:3122`; `REPORT.md:2568`; `combustion.json:10690` (`a1_apogee_target_v2p4b.v.target.lead_consequences_superseded`); `combustion.json:9957` (`a1_duration_note_v2p4b.line213_note_superseded`) |
| 215-228 (other) | read for status | Folded or read as listed. | `REPORT.md:2980`; `combustion.json:12039` (`final_fold_v2p4b`) |
