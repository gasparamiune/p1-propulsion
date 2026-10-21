# REVIEW-ELECTRONICS-R4 (REV-ELEC-4)

Independent delta review of Electronics v2.12, closed by the reviewer 2026-10-21T14:34:56Z and returned 14:35:54Z (reviewer stamps, date -u); the handback reached the lead at 14:38:25Z (transcript). Saved here by the lead on 2026-10-21T14:43:16Z (date -u), verbatim from the reviewer's final message: the harness does not let a subagent write a report file, so the handback text is the review. Its interim (E4-01 / E4-02, 13:57Z) is superseded by this text. Reviewer artefacts: `reviews/electronics/r4/` (`MANIFEST_REV-ELEC-4.sha256` 71fa2008ffca16cb, 98 entries, verified by the lead 98/98 OK at 14:42:56Z). Reviewed set: `06-electronics/staging_v2.12/` (`SHA256SUMS-v2.12.txt` f6fd3a63817dfb34). Lead disposition: CHANGELOG line 266. A verdict is not physical approval: no hardware exists.

```text
BEGIN REVIEW-ELECTRONICS-R4

REVIEW-ELECTRONICS-R4: independent delta review of Electronics v2.12 (REV-ELEC-4)
Reviewer: REV-ELEC-4 subagent. Review closed 2026-10-21T14:34:56Z and returned 2026-10-21T14:35:54Z (both stamps from date -u). Request 2026-10-21T12:50:21Z; lead message 13:58:21Z answered in section 1.
Scope: I wrote none of v2.12. I tried to refute its claims at max rigour, with the closure of my R3 findings first. A reproduced number shows that a computation repeats. It does not show that the hardware or the physics is right: no hardware exists and nothing here was built, weighed or measured. Interim E4-01 / E4-02 was sent at 13:57Z (saved by the lead as REV-ELEC-4-INTERIM-E4-01-1357Z.txt 3ec59a30dfcbb79b); this text governs over it.

## 0. INPUTS (sha256/16, checked in this review)

- Staging 06-electronics/staging_v2.12/: SHA256SUMS-v2.12.txt f6fd3a63817dfb34, 84 of 84 files OK [CALC]. firmware/ holds the changed files only; I built it as staging_v2.11/firmware + the v2.12 overlay.
- results/electronics_v4.1.json c862375163393adc; docs/bench_plan_v5.md 360c1d6695cc305c; results/bom_v2p4.csv eb6e77dcd4610383.
- Handback ELEC-v212-HANDBACK-124214Z.txt cd6981c0ba07b670 (governs over the interim ELEC-v212-INTERIM-A-1119Z.txt 8a99e98b53e51227). Author brief brief_ELEC-v212_v3_filled.txt e43f417adf46e679 (items A1-A8, B1-B11 used as the checklist).
- Baseline: staging_v2.11 SHA256SUMS dca5c3d8de4d1ea6; interfaces/electronics.json v4 11f7896ad0d0613b; SIL MANIFEST_v1 eaa9efc5112a8178; reviews/REVIEW-ELECTRONICS-R3.md fcf05f8bc7382cd1.
- Interfaces: combustion.json v2.4d 7dbf425c12300658; gnc.json v3.2 bde317782574cbd9; mechanical.json v2.4 66bc53d88d444679; Mechanical 04-fea/v352/lc_tb70_envelope.py d14489808338006b; c1seat/c1_seat_v352_v1.json 435f5d71f6213160, c1_seat_xcheck_v352_v1.json 02a9f27c7965f223, torch_port_bl08_v352_v1.json 20220647d32cbbbc. Author seat histories (results/v2p12/seat_hist): A1_NF2b 5783da72e6251b87, B1_R4_GVHI a07e4a42aa031954, B1_R4_GVLO 837d97281096882f.
- CHANGELOG: 264 lines (f7efe784da3944c5) at the start; line 265 (datasheet, 13:26:26Z) was appended during the review (760cf4fe1fb050d6, 265 lines). Rulings used: 253, 256-261 and 264 (1)-(8).

## 1. VERDICT

Overall: ACCEPT WITH COMMENTS, with option (b) carved out of every start with ignition until a reviewed v2.13 delta. Findings: 0 BLOCKING, 1 MAJOR, 5 MINOR, 11 NOTES.

v2.12 closes R3 except at one point: its central fix, the option (b) seat compensation, adds a new path into the light decision (E4-01). With the seat coefficient unloaded (compensation identically 0) that path does not exist, and everything else in v2.12 reproduces and holds.

| Deliverable | Verdict | Reason |
|---|---|---|
| Firmware and SIL v2.12 | REVISE for option (b) only (v2.13 delta: E4-01 MAJOR, E4-03 MINOR). The other v2.12 changes are ACCEPTED: purge FINAL, TB-state, JFWD_LS, torch re-zero limit, BASE check 0.76 / 0.46 bar, log v13 | Rebuild clean; test_core 332 / 0 and no-hooks 331 / 0, both logs byte-identical to the staged ones. The four binaries and every author run reproduce byte-identically. The v2.11 record re-run on v2.12 is identical for S1-S10, S6R, S6C, S14-S17 and probeF; the S12 / S13 changes are the predicted ones (section 4). Probes: thresholds discriminate; E4-01 and E4-03 confirmed |
| electronics_v4.1.json | ACCEPT WITH COMMENTS for promotion, with the carve-out text (Q1 below), the 264 folds and the E4-02 / E4-04 / E4-05 corrections | Numbers I checked hold. Stale limit bases, missing limit rows and unfolded rulings are listed in E4-05 |
| Bench plan v5 | ACCEPT WITH COMMENTS (text corrections E4-02, E4-06 before founder use; the TC4 rows of v2.13) | F-14, F-13, B-TC-1 (case TCs), B-BLEED-1 (d) / (d1) / (d2), B-MV-1 and T1-T4 inside A = 150 C are executable as written. The B-PC-1 stand sentence, the A1 pad row and the T4 row are not |
| BOM v2.4 | ACCEPT WITH COMMENTS | Row 205 (J904) and row 251 hold. Row 187 still labels TC4 as bore-top, and the C7 stand-DAQ TC is not carried (E4-06) |
| Handback | ACCEPT WITH COMMENTS | Its S13T, S12, R4-02 (10 / 10 and N-04 46 / 46) and A8 band numbers reproduce. Its "<= 5 % at k = 3" (E4-02) and U330 ordering (E4-04) statements are corrected here |

### Answers to the lead's three questions (13:58:21Z)

**Q1. Can v4.1 be accepted with the option (b) relight path carved out, the way 253 carved out R3-01 in v4?**
Yes, with a carve-out, but it must be wider than the relight path. The compensation acts in every state, and the light rule is the same at every start. A TC4 error after E1 of the FIRST start gives a premature E2 as well [SIM, reviewer fw_rv, run/rv/fs/]. The step was applied from E1 + 4 ms of the first start (E1 2.406 s). In the no-fault controls the plant lights at E1 + 128 ms, E2 follows at E1 + 143 ms, and both locations reach RUN.
- Pad, A1 T0 20 C:
  - -8 K at k = 3: E2 at E1 + 62 ms (Pc_meas 1.97 bar abs), before the plant would light. The plant never lights, and FLAMEOUT follows at E2 + 19 ms.
  - -30 K at k = 1: E2 at E1 + 53 ms, then FLAMEOUT.
  - -30 K at k = 3: E2 at E1 + 18 ms (Pc_meas 3.35 bar abs). b7 latches at E2 + 100 ms, and unlit run-lift flow continues for 201 ms (plant 5.58 bar abs) before FLAMEOUT.
- Stand, T0 24 C: -20 K at k = 1 and -8 K at k = 3 give E2 at E1 + 67 / 62 ms, then FLAMEOUT at E2 + 19 ms.
Each case is a lost start, recorded as FLAMEOUT rather than as a sensor fault. I did not evaluate what the FC does with b4 / b7 at a pad start.
Proposed carve-out text:
"Option (b) (seat coefficient loaded, setPcSeatCoef != 0) is not used for any start with ignition (pad first start, stand starts, relights) until a v2.13 delta with the light-window hold and the TC4 step / rate checks is reviewed. The coefficient may be loaded for B-PC-1 / B-TC-1 bench work without ignition."
Consequences under the carve-out, from the rulings in force:
- A1 flight is NO-GO: 264 (2) makes the A1 pad NO-GO unless the coefficient is loaded and TC4 valid at ARM.
- Stand first starts may run on the fallback within 264 (2): k <= 2 (default build) / k <= 1 (kBpc1Shown), and k x 0.0248 x (T0 - T_cal) clearly inside 0.5 bar. k must first be measured (B-PC-1; F-10 is still MISSING).
- No stand relight: the fallback refuses it (S13T fallback stand: in every arming run refused NOT_VENTED, code 8 [SIM]). The T4 relight therefore waits for v2.13.
v4.1 items that depend on E4-01, and should be marked "suspended until v2.13":
- the option (b) firmware rows (firmware.v2p12.changes seat compensation; r3_01_c1_drift option (b) residuals; the S13T option (b) outcomes 40 / 40 A1 RUN and the stand rows);
- the kIgnBaseDrift 0.06 bar basis "compensated, k <= 3": it holds for the fallback first start too, because the seat is at T0 there (ARM -> E1 drift about 0), but not for any relight;
- the decision (3) basis "0 BASE_AMB with option (b)" (264 (3)): the decision stands, but its evidence must be re-shown on v2.13;
- the A1 pad go / no-go seat row (264 (2), not yet written);
- the stand relight after B1 acceptance (E4-02);
- the B-PC-1 / B-TC-1 TC4 rows, which v2.13 must extend.
Independent of E4-01, and acceptable now: purge FINAL (2.43 / 2.39 s, rule (d) with (d1) / (d2)); TB-state; JFWD_LS; kPtorchRezeroMax_Pa 0.60 bar (re-base OPEN by 264 (4)); log v13; kIgnBaseCheck_Pa 0.76 / 0.46 bar; the U330 band rows (raw path, no compensation); R4-02 / R4-09 / R4-13; F-13, F-14, B-MV-1; and the T1-T4 planning rule.

**Q2. Acceptance criteria for the delta (v2.13).**
Minimal firmware change:
1. Light-window hold. At IGNITION entry, latch seat_comp_. IGNITION entry is at least 45 ms before E1 [SIM: first start E1 = entry + 45 ms, relight E1 = entry + 51 ms], so before the P0 window [E1 - 20 ms, E1]. Use the latched value for every Pc use until E2 + 0.45 s (the existing A7 high-side blank), or until IGNITION / RUN is left without E2. Then resume bumplessly, slewing the compensation at <= 5 K/s x coef.
   - Cost: the true seat drift is not followed during the hold. At the relight the diaphragm rate is 0.55-0.70 K/s (A1) and 1.02-1.40 K/s (stand) [SIM, Mechanical]. Over the <= 0.70 s from E1 to the NO_IGNITION timeout this is <= 0.49 / 0.98 K, i.e. <= 0.036 / 0.073 bar at k = 3 [DERIVED]. It reduces the unlit margin (0.29-0.45 bar, Combustion) and belongs in the kIgnBaseDrift basis.
2. TC4 plausibility, evaluated on every conversion in every state, inside the hold window too. The SIM physical maximum is 0.24 K per 0.1 s (2.42 K/s, GVLO at the B1 end) [DERIVED, data/seat_rate_max.json].
   - Step check: |T_n - T_n-1| <= 1.5 K between consecutive conversions.
   - Rate check, outside the hold: the temperature used for the compensation slews toward the reading at <= 5 K/s (about 2 x the physical maximum). If the reading is more than 3 K from the slewed value, the check trips. This catches a ramp-type error that passes the step check. It also lets the compensation catch up after the hold: the true drift over the hold is at most about 1.9 K (0.8 s at 2.42 K/s) [DERIVED], so catching up does not trip it.
   On a trip:
   - hold the compensation at the last good value (the latched value if inside the window);
   - set a new latched flag, f3 SEAT_STEP (log and TLM);
   - stay held until the next ARM, which re-references.
   The existing range (223.15-473.15 K) and 150 K checks stay.
3. E4-03: canArm compares |pc_f_ + pc_zero_ + seat_comp_ - coef x (T - T_cal)| with kPcArmZeroMax_Pa.
4. The FC / lead rule for SEAT_STEP set before a relight (for example the 264 (7) style inhibit) is a lead decision; the ECU provides the flag.
Unit tests (all must pass, plus the existing 332 / 331):
- UT-1, hold. Unlit start with a 0.42 bar cold-flow rise (the probe B rig). TC4 errors:
  - magnitudes -3, -5, -8, -15, -20, -55, +90 and +140 K;
  - starting at E1 - 25, E1 - 10, E1 + 5, E1 + 100, E1 + 300 and E1 + 600 ms;
  - lasting 100 ms, 250 ms or persistent;
  - coef 0.0248e5 and 0.0744e5 Pa/K, both signs.
  Pass: 0 E2. The lit controls give E2 at the same tick as without the error.
- UT-2, step and rate checks:
  - a 2 K one-conversion step, inside or outside the window, holds the compensation (+/- 1 Pa) and sets SEAT_STEP;
  - a 14 K/s ramp error sets SEAT_STEP within 0.5 s, after moving the compensation by <= 2 K x coef;
  - a 2.42 K/s true ramp for 60 s sets neither, and the compensation follows it within 0.1 K.
- UT-3, RUN. A +90 K step in RUN at k = 3 moves pc_f_ by <= 0.02 bar.
- UT-4, re-ARM. The 8 probe B Q1 cases decide as a fresh ECU.
SIL S13T TC-fault cases (the reviewer set in section 4, made part of the record):
- A1 T0 20 C and stand after B1 T0 24 C (GVHI / GVLO), k 1 and 3, s +/-1, lit and unlit;
- TC4 steps of -3 / -5 / -6 / -8 / -10 / -15 / -20 / -30 / -55 K from E1 + 4 ms, the same in the P0 window (E1 - 10 ms), and +90 K from 22.30 s;
- the same steps at the pad and stand FIRST starts.
Pass:
- 0 FALSE_E2 and 0 E2 before the plant light;
- every lit run RUN with no abort;
- every unlit run NO_IGNITION;
- the no-fault S13T outcomes unchanged.
FMEA row (fmea_rows_a1, new):
- Item: TC4 seat TC (MAX31856 U904, J904, grounded-junction MI type K at the C1 boss) reading error.
- Causes: spark-coupled interference, a lead short to a colder point, junction debond, open TC, MAX31856 fault.
- Local effect: the compensation wrong by coef x dT, i.e. 0.0248-0.0744 bar/K at k 1-3.
- System effect without the fix [SIM]:
  - false or premature E2, with run-lift flow into an unlit chamber;
  - at A1 k = 3 with >= 30 K, the FC release predicate is met at the false E2 and the engine aborts 280 ms later;
  - a lost relight or first start (FLAMEOUT / PC_SENSOR / TORCH_LOST);
  - in RUN, a false FLAMEOUT after a true light (+90 K at A1 k = 3: E2 + 58 ms);
  - a Pc bias of up to coef x 150 K: 3.7 bar at k = 1, 11.2 bar at k = 3 [DERIVED].
- Detection: MAX31856 fault bits, range, 150 K, SEAT_STEP.
- Mitigation: the hold and the step / rate checks.
- Residual: an uncompensated drift after a hold (fail-safe refusals of the v2.11 type).
B-TC-1 row for TC4 (new, with the spark):
- Set-up: TC4 as installed (C1 boss, flight J904 harness, engine grounded as flown). Spark at the flight rate, torch valves cycling, servos and pintle rail on, against all off. At least 30 s each, 3 repeats, every conversion logged.
- Pass:
  - mean shift <= 0.3 K;
  - per-conversion peak deviation <= 1.0 K, below the 1.5 K step threshold so there is no nuisance SEAT_STEP;
  - no MAX31856 fault bit (OVUV / open);
  - with the TC simulator, one-conversion steps of +/-2, +/-10, +/-55 and +140 K:
    - inside [IGNITION entry, E2 + 0.45 s] they change neither P0, nor the rise, nor the E2 tick;
    - inside or outside that window they set SEAT_STEP, and the compensation holds.
- Also verify the grounded-junction common-mode behaviour on the MAX31856 input [TO-VERIFY against the datasheet].

**Q3. E4-02: the corrected stand acceptance limit.**
Limit: the coefficient error |eps| (fit or loaded value against the true slope) must satisfy |eps| <= eps_max(k_meas), where k_meas is the B-PC-1 slope / 0.0248 bar/K, read from the table and interpolated downward in k. If |eps| > eps_max(k_meas), the stand relight after a B1-length burn is planned as REFUSED NOT_VENTED. That outcome is fail-safe, and no relight objective is claimed for it.
| k | stand re-zero2, DERIVED worst case with the 0.1012 bar adders | without adders | SIL point (reviewer F3 run, no adders) |
|---|---|---|---|
| 1.0 | 11.2 % | 19.2 % | not run |
| 1.25 | 8.1 % | 14.5 % | not run |
| 1.5 | 6.0 % | 11.3 % | not run |
| 2.0 | 3.4 % | 7.4 % | all 5 variants (-5 % / -0.3 K, -5 % / 0 K, -4 %, -3 %, +5 % / +0.3 K): all 20 runs RUN, both re-zeros accepted |
| 2.5 | 1.8 % | 5.0 % | not run |
| 3.0 | 0.8 % | 3.4 % | -3 %: RUN, both accepted; -4 %: re-zero2 rejected, RUN on re-zero1; -5 % / 0 K: RUN on re-zero1; -5 % / -0.3 K: GVLO REFUSED NOT_VENTED (both signs); +5 % / +0.3 K: RUN, both accepted |
Tags:
- The table is DERIVED (scripts/e4_02_eps_table.py, data/e4_02_eps_table.json) on Mechanical SIM seat histories x the DATASHEET typical 0.0248 bar/K.
- tau 0.25 s and the TC error 0.3 K are ASSUMED. The adders are the author's: zero drift 0.05 bar ASSUMED, outgassing 0.05 bar DESIGN, noise 0.0012 bar DERIVED. T_aw 1500 K is ASSUMED (F = 1.0166 at T0 0 C).
- The SIL column is SIM.
Two related points:
- Re-zero1 does not close at k = 3 with the adders even at eps 0. The NOT_VENTED check against re-zero1 (the path taken when re-zero2 is rejected) needs eps <= 0.2-8.7 % for k 3-1 (worst case), so it is not a second line to count on.
- The A1 relight is not affected: A1 re-zero2 closes to 11.5 % at k = 3 with the adders, and the 10 % B-PC-1 pass criterion holds for flight (see E4-N06).

## 2. FINDINGS

### E4-01 (MAJOR). Option (b): a TC4 reading error after E1 gives a false or premature E2, at every start

What v2.12 does (staged firmware/src/core/engine_ecu.cpp 97a9a4166bdccfe5):
- l.1333-1334: once an ARM reference exists, seat_comp_ = coef x (tc_bore_K - seat_ref_K_), in every state. It is held only when TC4 is invalid, outside 223.15-473.15 K, or more than 150 K (kPcSeatDevMax_K) from the reference. The reference is re-taken only at ARMED entry (l.663).
- l.1379: in_c_.pc_Pa = in.pc_Pa - seat_comp_. The filtered and the raw Pc that ignDetect reads are both compensated.
- ignDetect (l.128-163): P0 is the mean over [E1 - 20 ms, E1], fixed on the first tick after E1. E2 needs a rise >= 0.80 bar on the filtered and the raw Pc, the 1.8 / 2.0 bar abs floor, and 10 held ticks.

Why it fails:
- A TC4 error dT that appears after P0 is fixed moves the compensated Pc by -coef x dT. An error of either sign adds to the rise when coef x dT < 0.
- The unlit cold-flow rise is about 0.42 bar [SIM: max 0.428 bar stand, 0.427 bar A1; data/e1_timing_unlit.json]. That leaves about 0.38 bar to the 0.80 bar E2 rise, which an error of about 15 K at k = 1 (0.0248 bar/K) or 5 K at k = 3 (0.0744 bar/K) closes [DERIVED].
- Nothing checks the TC4 step size or rate. The physical seat rate is at most 0.24 K per 0.1 s (2.42 K/s, GVLO at the B1 end) [DERIVED on SIM, data/seat_rate_max.json], so an error of a few K in one conversion cannot be a real temperature, but the 150 K check passes it. Bench plan v5 l.158 documents the same 150 K threshold ("a jump > 150 K after ARM -> f3 SEAT_FROZEN").

Evidence:
- Reviewer SIL [SIM]: the v2.12 SIL with a TC4 error added after the 0.25 s lag filter (fw_rv, made by scripts/make_fw_rv.py; S13T driftRun; 108 relight runs; N2O-without-propane 0 ms in every run).
  - Overall: 13 of 44 unlit runs reach a FALSE_E2, and 33 of 64 lit runs lose the relight: 17 RUN_then_FLAMEOUT, 2 RUN_then_PC_SENSOR, 12 PC_SENSOR, 2 TORCH_LOST.
  - Stand relight after B1, T0 24 C: unlit FALSE_E2 at k = 3 from -6 K, and at k = 1 from -20 K (-10 K does not). The matching lit runs go RUN_then_FLAMEOUT (TORCH_LOST at -55 K, k = 3): the premature E2 ends the torch before the plant lights.
  - A1 relight, T0 20 C: FALSE_E2 at k = 3 from -8 K (-5 K does not), and at k = 1 at -30 K (-15 K does not).
  - A1, k = 3, -30 K, unlit: E2 at E1 + 17 ms with Pc_meas 3.34 bar abs. The gnc v3.2 release predicate (RUN AND b4 AND Pc valid AND Pc >= 300 kPa abs, latched) holds from that E2, and b7 latches at E2 + 100 ms. Run-lift flow then goes into the unlit chamber for 280 ms (plant 4.16 bar abs) before FLAMEOUT. On the vehicle that is a drogue release with no thrust. The FC is not modelled here: the predicate is evaluated on the SIL telemetry, whose Pc is pcAbsFiltered(), the compensated value.
  - Smaller errors: FLAMEOUT at E2 + 19 ms. b7 does not latch, so the drogue is held and the relight is lost.
  - Coefficient sign -1: a -8 K error at A1 k = 3 lit aborts PC_SENSOR at E1 + 59 ms (lost, fail-safe). A +90 K error from 22.30 s gives a FALSE_E2 in every unlit s = -1 run.
  - In RUN: +90 K from 22.30 s at A1 k = 3 lit (s = +1) gives FLAMEOUT at 22.322 s, E2 + 58 ms. That is a relight lost after a true light.
  - First starts: Q1 in section 1 (the pad and stand first starts fail the same way).
- Probe B (scripts/probe_v212b.cpp on the v2.12 ECU code; rig with a 0.42 bar cold-flow ramp) [CALC]:
  - false E2 in 30 of 60 error cases;
  - thresholds between -15 and -20 K at k = 1, and between -5 and -8 K at k = 3;
  - an error lasting 100 ms is enough;
  - b7 never latched in the rig.
  Probe A (probe_v212.cpp): 4 of 8.
- Credible causes: spark-coupled interference on a grounded-junction TC at the C1 boss next to the torch, a lead short to a colder point, a MAX31856 conversion error.
- Coverage: no v2.12 unit test, SIL case, FMEA row or B-TC-1 row covers a TC4 error in the light window. The B-TC-1 EMI row (bench plan v5 l.193-201) covers the case TCs only.

Correction: the v2.13 delta of Q2 (hold, step / rate checks, E4-03 fix, UT-1 to UT-4, the S13T TC-fault set, the FMEA row, the B-TC-1 TC4 row), and the Q1 carve-out until that delta is reviewed. The bench plan TC4 row (l.158) changes with it.

### E4-02 (MINOR). "Coefficient within 5 % at k = 3" is not supported

Where: bench plan v5 l.156 (B-PC-1); v4.1 r3_01_c1_drift.stand_relight_after_B1; the handback; CHANGELOG 264 (2).
- At k = 3, the stand re-zero2 closes only for |eps| <= 0.8 % with the 0.1012 bar adders, and <= 3.4 % without them [DERIVED, data/e4_02_eps_table.json].
- In the SIL (no adders) at k = 3 [SIM, reviewer F3]:
  - -4 % already rejects re-zero2 (the run reaches RUN on re-zero1);
  - -5 % with the -0.3 K TC error gives REFUSED NOT_VENTED at GVLO, on both signs.
- For k <= 2 the true limit is looser than 5 %. A single 5 % figure is therefore too loose at k = 3 and too tight at k = 1.
- The refusal it leads to is fail-safe, so this is an acceptance and planning error, not a hazard.

Correction: replace the sentence in the bench plan v5 l.156, in v4.1 stand_relight_after_B1 and, at promotion, in the 264 (2) wording, with the rule and table of Q3.

### E4-03 (MINOR). canArm subtracts the static term twice after an earlier ARM

- After a run, SAFE keeps seat_ref_ok_ from the earlier ARM, so pc_f_ is already compensated by coef x (T - T_ref,old). canArm (l.789-791) then subtracts coef x (T - T_cal) again. In SAFE the compensation is 0.124-1.488 bar in the probe cases [CALC].
- Probe B Q1 [CALC on the v2.12 code]: 6 of 8 re-ARM cases decide differently from a fresh ECU (dT = T_seat - T_cal).
  - The re-ARM accepts offsets that a fresh ECU refuses: +0.6 bar (k = 3, dT 10 K), +1.3 bar (k = 3, dT 20 K) and +0.9 bar (k = 1, dT 25 K).
  - The re-ARM refuses at a true offset of 0: k = 1 with 25 K, and k = 3 with 10 K and 20 K.
- Probe A's Q1 passed because it ran with T_cal at T0, so it could not show this.
- The later re-zero (0.30 bar) and NOT_VENTED (0.10 bar) checks still apply, so a false acceptance alone does not give a false E2.

Correction:
- canArm compares |pc_f_ + pc_zero_ + seat_comp_ - coef x (T - T_cal)| with kPcArmZeroMax_Pa, that is, it compensates the uncompensated reading once. Alternatively, clear seat_ref_ok_ and seat_comp_ at SAFE entry.
- Add UT-4 (Q2).

### E4-04 (MINOR). The U330 ordering statement omits the stand relight light

- The handback's thresholds reproduce for the three cases it lists: k = 1.227 (A1, T0 40 C), 2.82 (A1, T0 20 C) and 1.73 (B1 end, T0 24 C) [DERIVED, data/r4_01_c1_drift_v2.json].
- It omits the stand relight light, where the seat rise is largest. There the U330 low edge falls below the 30 bar abs firmware abort from k = 0.725 at T0 24 C (29.59 bar abs at k = 1, 26.62 at k = 3) and from k = 1.21 at T0 0 C [DERIVED].
- Under (b) the firmware reads the compensated Pc while U330 reads the raw path, so on a stand relight the hardware trip can act first.
- The bench plan row is correct. The SIL S13T stand relights reach a U330 node maximum of 15.73 bar abs [SIM], so no SIL run exercises this.

Correction: v4.1 r3_01_c1_drift.A8 U330_ordering and the handback statement gain the stand relight light row: k >= 0.725 at T0 24 C, and >= 1.21 at T0 0 C.

### E4-05 (MINOR). v4.1 folds and stale rows

Correct each item at promotion:
1. limits_v2p11[4]: the basis text is stale (2.55 s / 76.05 g / 80.76 g). Replace it with the v2.12 FINAL basis: kPurgeFlow_s 2.43 s and kHbleedCap_s 2.39 s (defaults and maxima, setPurgeCal SAFE only), cap 2.397 s at the defaults, rule (d) with (d1) / (d2).
2. limits_v2p11[14]: the basis "residual + 0.1 bar" lacks the drift term. Write "residual + kIgnBaseDrift 0.06 + 0.10 bar = 0.76 / 0.46 bar".
3. Missing limit rows, each with its value, tag and source:
   - the seat constants (kPcSeatCoefMax_PaPerK 1.0e4, kPcSeatDevMax_K 150, kPcSeatTcMin_K / kPcSeatTcMax_K 223.15 / 473.15, the T_cal minimum / default / maximum, kPcSeatArmDevMax_K 30);
   - kIgnBaseDrift 0.06 bar;
   - kPtorchRezeroMax_Pa 0.60 bar;
   - kJfwdLsRawAbs 47.5 bar abs.
   config_changes lists only 7 paths.
4. limits_v2p11[7] still says "(CANDIDATE, default OFF)". Restate it as ADOPTED on the 253 (7)(i) / 256 (3) conditions.
5. pad_go_no_go_a1 cites v4 and v2.11 and has no seat or JFWD row. Add:
   - the 264 (2) row (coefficient loaded and TC4 valid at ARM; NO-GO until v2.13 under the carve-out);
   - the 264 (7) JFWD_LS row;
   - the v4.1 / v2.12 citations.
6. Stale labels:
   - the TC4 channel "bore top" becomes "C1 seat" (264 (2));
   - the harness "bore-top TC (stand)" becomes "C1 seat TC (TC4, J904)";
   - the mass statement gains the seat TC (5 g ASSUMED);
   - the bom dict cites v2.3: make it v2.4 eb6e77dcd4610383;
   - the status "pending" is updated.
7. CHANGELOG 264 (1)-(8) is not folded. For example, P_TORCH is still M3234-000005-070BG; 264 (4) moves it to the XTL-190SM-2000A.
8. r3_01_c1_drift.stand_relight_after_B1 still carries the 5 % rule (E4-02), and A8 U330_ordering is incomplete (E4-04).
9. The stale "<= 73.0 g at 2.5 s" at v4.1 l.9974, sil_main.cpp l.2505 / 2668 and S12_bleed.json is replaced by the FINAL basis: DERIVED 71.1-75.8 g; SIL 76.38 g, an ESTIMATE (E4-N05).

### E4-06 (MINOR). Bench plan v5 and BOM v2.4 rows that contradict the rulings

1. The A1 pad row allows the fallback, against 264 (2). Write: A1 pad NO-GO unless the coefficient is loaded and TC4 is valid at ARM; under the Q1 carve-out, NO-GO until v2.13.
2. The T4 row (coast about 19 s / 112.7 C, relight 4.59 s) contradicts 264 (5) (shorter relight adopted, coast not lengthened). Restate T4 as a relight-latency demonstration from a soaked state, with the length set by Combustion's T4 re-run. T4 is also a stand relight, so it waits for v2.13.
3. BOM row 187 still labels TC4 "bore-top / manifold (firmware v2.7, CF-3/T1 evidence)". Relabel it "C1 seat TC (TC4, MAX31856 U904, J904)".
4. The C7 bore-top stand-DAQ TC (CHANGELOG l.55) is carried only in a config.h l.856 comment. Add it to the bench plan stand DAQ list and to the BOM as a stand-only row.
5. The B-PC-1 sentence (E4-02) and the TC4 rows (B-PC-1 l.158 and B-TC-1) change with v2.13 (Q2).

### Notes

- E4-N01. The kPcSeatArmDevMax_K comment "(flight T0 0-40 C, T_cal 10-35 C: <= 30 K)" is false: T0 0 C with T_cal 35 C gives 35 K. Beyond 30 K the static term is dropped, and the v2.11 check then refuses ARM for k > 0.58 [DERIVED: k x 0.0248 x 35 K > 0.5 bar]. That is fail-safe, but it means a cold-day NO-GO. Fix one of two ways: restrict the flight-serial T_cal to 10-30 C, or set kPcSeatArmDevMax_K to 40 K with a unit test.
- E4-N02. Neither the 264 (2) pad rule nor the 264 (7) JFWD_LS relight inhibit is implemented in the ECU or specified for the FC. Both belong in v2.13, or in an FC ICD change, with tests.
- E4-N03. The JFWD_LS threshold, 47.5 bar abs raw, is 0.25 bar below the 47.75 bar abs value in c1_cc1_c400_v6. TO-VERIFY which value governs. Probe Q3b shows the firmware discriminates 47.49 / 47.51 bar abs [CALC].
- E4-N04. With 264 (4) the P_torch sensor becomes C1-family. On the author's head-temperature basis (0.128 / 0.517 bar at 0.01 bar/K, that is 12.8 / 51.7 K), the torch zero shift becomes 0.32 x k bar (A1) and 1.28 x k bar (stand) at the 0.0248 bar/K typical [DERIVED]. That is above kPtorchRezeroMax_Pa 0.60 bar on the stand at every k >= 0.47. The re-base therefore needs either compensation or a photodiode-guarded torch gate, and the torch local heat (MISSING) first.
- E4-N05. The S12 SIL nominal purge mass, 76.38 g at 31.85 g/s, is an ESTIMATE (the plant flow is 2.5 % above the 31.06 g/s bound). The DERIVED basis is 71.1-75.8 g. See E4-05 (9) for the stale 73.0 g text.
- E4-N06. The A1 re-zero2 margin at k = 3 is 11.5 % against the 10 % B-PC-1 pass criterion: 0.286 bar with adders against 0.30 bar at 10 % [DERIVED]. It holds, but thinly.
- E4-N07. The compensation is a static linear coefficient. Hysteresis, a non-linear zero and gradients across the diaphragm beyond the modelled sensor-node term (-0.29 to -2.28 K) are not represented. B-PC-1 over 0-85 C with 2 cycles is the only check.
- E4-N08. The hardware both-open timer (U577: 2.577-2.741 s, DATASHEET 3 % grade + 0.1 % RSET) is correctly ordered after the firmware cap + 1 tick (2.391 s). But if the firmware cap fails, it allows up to 2.741 s, above Combustion v2.4d's "never above" 2.39 s. The bench plan's unapplied option, RSET 59.0 kOhm (2.475 s nominal, 2.398 s minimum), narrows the gap. Combustion and the lead should say whether the backstop must sit inside the Combustion bound. It stays a B-BLEED-1 item.
- E4-N09. TB-state is conservative: any over-range sample sets it, and a nozzle-holder OVER_TEMP sets it. That is acceptable for a test-bed indication.
- E4-N10. TO-VERIFY: a grounded-junction TC4 on the MAX31856 input (common-mode range and fault-detection behaviour against the datasheet). It is also a candidate EMI path for E4-01.
- E4-N11. The author produced no v2.12 SIL MANIFEST (264 (8)). My re-run of the record (section 4) stands in for the comparison. The v2.13 delta should produce a MANIFEST_v2 for the full record.

## 3. R3 CLOSURE

R3-01 items 1-8 are the author's A1-A8. Tags are those of the numbers cited.

| R3 item | v2.12 answer | Reviewer status | Basis / residual |
|---|---|---|---|
| R3-01 (1) k sweep, coefficient basis (A1) | k 1-3, both signs, Mechanical seat histories | CLOSED WITH RESIDUAL | F-10 (thermal-zero maximum) is MISSING. The stand seat reaches about 78.4-78.7 C at the relight (T0 24 C + 54.4-54.7 K) [DERIVED on SIM], outside the ordered 0-55.6 C band, so only the per-serial 0-85 C B-PC-1 fit covers it |
| R3-01 (2) seat rise and T0 (A2) | rises, F = 1.0166 | CLOSED WITH RESIDUAL | Reproduced: A1 12.53 / 14.53 K at re-zero2 / E1; stand 50.41-51.22 / 54.37-54.65 K [DERIVED on SIM]. T_aw 1500 K and T0 0-40 C are ASSUMED (264 (6)) |
| R3-01 (3) re-zero limit (A3) | option (b), 0.30 bar on the compensated residual | CLOSED WITH RESIDUAL | Reproduced: uncompensated re-zero2 shift 0.316-0.948 bar (A1) and 1.291-3.874 bar (stand) for k 1-3; the k = 3, 10 % budget is 0.185 bar (A1) and 0.550 bar (stand) [DERIVED]. Residuals: E4-01 (a new path into the light decision) and E4-02 (the acceptance limit) |
| R3-01 (4) base check (A4) | 0.76 / 0.46 bar | CLOSED | residual + 0.06 + 0.10 bar [CALC]. Probe Q3d: discriminates +/-0.01 bar on both sides [CALC] |
| R3-01 (5) SIL drift model (A5) | s, k, coefficient, lag, TC error | CLOSED | The P_mid / U570 drift stays MISSING (Mechanical). The model has no TC-fault mode: my extension found E4-01 |
| R3-01 (6) S13T (A6) | 240 runs per build | CLOSED | Byte-identical on the rebuilt binaries, both builds [SIM] |
| R3-01 (7) torch (A7) | kPtorchRezeroMax_Pa 0.60 bar | CLOSED WITH RESIDUAL | The torch-port dT is MISSING; the 264 (4) re-base is OPEN; E4-N04 |
| R3-01 (8) U330 (A8) | bands, ordering, thresholds after a rejected re-zero2 | CLOSED WITH RESIDUAL | Bands reproduce (k = 3 stand relight light 26.62-38.56 bar abs [DERIVED]). The ordering is incomplete (E4-04). The thresholds are in v4.1 A8_fw_thresholds_after_rejected_rezero2 |
| R3-02 (MINOR) F-14 / v4 citation | F-14 verbatim, TB-state, Q_JFWD per platform | CLOSED | Probes Q3a / Q3b discriminate [CALC]; E4-N03, E4-N09 |
| R3-03 (MINOR) B-TC-1 CJTO | trim step, EMI mean shift (case TCs) | CLOSED | The TC4 EMI row comes with v2.13 (Q2) |
| R3-04 (MINOR) 227 (5) conditions | two conditions added; 640 / 2000 per window | CLOSED | r2v2 re-run on v2.12 is identical to the v2.11 record apart from wall time [SIM] |
| R3-05 (MINOR) C1 band | 0-55.6 C ordered; 0-85 C and F-10 asked | CLOSED | BOM rows 205 / 251 hold. F-10 stays MISSING (R3-01 (1)) |
| R3-06 (MINOR) F-13 | TC1 / TC2 within 1 K for 30 min, +/-0.5 K thermometer | CLOSED | none |
| N-01 S6R decay | B-MV-1 row | CLOSED | none |
| N-02 input_peak | label in the interface only | CLOSED | The SIL field name is unchanged; no classification depends on it |
| N-03 T45 guard | (information) | no action | none |
| N-04 out-of-envelope FA-1 | R4-02 composition | CLOSED | Reproduced: the author's r4_02_reclass_v2p12.py on my re-run traces gives a byte-identical f3d91aba932ac851: S6R 10 / 10 and N-04 46 / 46 inside Z3 v2, J-FWD triggered in all, Q_JFWD 87.15-113.11 bar abs [SIM on ASSUMED constructs] |
| N-05 offline R2 v2 | (none) | OPEN | GNC's re-run with the flush |
| N-06 stand false-trip spare | B-TC-1 measures EMI / CJ / inhomogeneity | CLOSED WITH RESIDUAL | The measurement is pending (the 0.64 K spare rests on ASSUMED terms) |
| N-07 DC-D / T1-T4 | re-sized within A = 150 C; T4 OPEN | CLOSED WITH RESIDUAL | 264 (5) is adopted but the bench plan T4 row is not updated (E4-06 (2)) |
| N-08 Pc_f at E2 | (none) | OPEN | Not addressed. My first-start control runs give Pc_meas 3.11 bar abs at E2 [SIM]. That is the first start, not the R2 relight case the note concerns |
| N-09 stale comments | config.h corrected, OI-STALE-LABELS CLOSED | CLOSED | Labels outside config.h remain (E4-05 (6), E4-06 (3)) |
| N-10 Combustion v2.4b texts | Combustion v2.4c / v2.4d | CLOSED | The old texts remain only in superseded blocks |

## 4. REPRODUCTION AND CONFIRMED NUMBERS

Build and tests [CALC]:
- staging_v2.11/firmware with the v2.12 overlay, g++ 13.3.0 -O2, make -j1, nice 15. All four binaries are byte-identical to the author's: sil 7023f964d8e35565, sil_bpc1 792bf7affbbfd615, test_core 9ff1535e5f9c5589, test_core_nohooks 7c6d7ce6fe37fb7f.
- test_core 332 passed / 0 failed; no-hooks 331 / 0. Both logs are byte-identical to the staged logs (c645af8aba83dd04, 92b788bcdd5afb23).

Part A, the author's v2.12 runs re-run on my binaries [SIM]. Every file is byte-identical:
- S13T both builds: 24c3aa3c108a7651 and eaae63e074be887e;
- S12_bleed.json 02d49def4fba065e;
- S6R max-face and trace0;
- a8_bandhigh S6R d8a3fbfa684e6f6e and S6C 0d52b41da3402df9.

Part B, the v2.11 SIL record commands re-run on v2.12 and compared with staging_v2.11/results/sil_v2p11 (scripts/compare_v212_vs_v211_record.py; run/compare_partB_3.json):

| Scenario | How v2.12 can reach it | Result |
|---|---|---|
| S1-S5, S7-S9 | log v13, TB-state (flag only); the seat path is inert with coefficient 0 | identical |
| S6 aborts, S6R (all traces), S6C rc cost | TB-state, JFWD_LS (flag), BASE check | identical |
| S10 relight, S10 v2.11 cold rule | torch re-zero limit, BASE check | identical |
| S12 bleed | purge FINAL | 198 leaves changed, 1 outcome leaf: pmid_chain_dead_after_bit_stand t_abort 5.42 to 5.49 s. The same 4 fails as v2.11 |
| S13 ignition rule | purge FINAL | 41 leaves changed (purge-start values, e.g. bleed liquid 75.07 to 72.96 g), 0 outcome leaves |
| S13B ext | BASE check 0.70 / 0.40 to 0.76 / 0.46 bar | default build 82 outcome leaves, B-PC-1-shown build 70. All are PC_SENSOR to RUN (lit) or PC_SENSOR to NO_IGNITION (unlit). 0 unlit runs reach RUN in 264 + 264 runs |
| S14 v2.10, S15 start MC, S16 coast 206, S17 r2hold, probeF | purge timing, BASE check | identical (the S14 CSVs are not in the record) |
| S17v2 r2v2 | none expected | identical apart from wall time (sweep: 1 of 38705 leaves, wall_s) |
| S11 fault path | purge timing | not in the v2.11 record (section 7) |

So v2.12 changes only what its changes predict. The record scenarios run with the coefficient at 0 (sim.h l.93 default; only sc_v212.inc, the S13T set, loads one), so the seat path is inert in them.

Reviewer runs [SIM unless tagged]:
- Probe A (probe_v212): Q3a TB_STATE PC_SENSOR HIGH 4.7495 / 4.7505 V; Q3b JFWD_LS 47.49 / 47.51 bar abs; Q3c torch re-zero 0.595 / 0.605 bar; Q3d BASE 0.76 bar +/-0.01 bar. All discriminate [CALC].
- Probe B: E4-01 (30 / 60) and E4-03 (6 / 8) [CALC].
- fw_rv F3, coefficient error: stand T0 24 C, k 2 and 3, 5 coefficient / TC variants (the E4-02 SIL column).
- fw_rv TC steps: 108 relight runs (E4-01).
- fw_rv first starts: 5 fault cases and 2 controls (Q1).
- In every reviewer run, N2O-without-propane is 0 ms.

Confirmed numbers:
- Seat rate maximum: A1 1.383 K/s, GVHI 2.378 K/s, GVLO 2.424 K/s [DERIVED on SIM].
- Diaphragm rate at the relight E1: A1 0.62 K/s, stand 1.02-1.22 K/s [DERIVED on SIM].
- Unlit relight: cold-flow rise 0.428 bar (stand) and 0.427 bar (A1); E1 22.121 s; NO_IGNITION at 22.472 s (stand) and 22.772 s (A1) [SIM].
- U330 thresholds: k = 1.227 / 2.82 / 1.73 (author) and 0.725 / 1.21 (E4-04) [DERIVED].
- R4-09: at least 6.6 bar to FS and 15.2 bar to 146.5 bar abs [DERIVED].
- R4-13: config.h cites purge_duration 1ff6bfcd7d2f454c; the hash matches [CALC].
- R4-02 / N-04: see the N-04 row of section 3.
- Purge FINAL: 2.43 / 2.39 s, cap 2.397 s at the defaults, PURGE at E0 - 2.90 s, command span 2.38 s [DERIVED]. These equal combustion v2.4d's FINAL values.

## 5. RECOMMENDATIONS ON THE AUTHOR'S RULING REQUESTS (handback items 1-6) AND LEAD 264

The lead ruled on requests 1-6 in CHANGELOG 264 (2)-(7). My recommendation on each:

1. R3-01, option (b) and TC4 (264 (2)).
   - Keep (b) as the design. It is the only configuration that keeps the A1 relight at k = 3 (S13T, reproduced).
   - Suspend its use for any start with ignition until v2.13 is reviewed (E4-01; Q1 carve-out).
   - Replace "within 5 % at k = 3" with the Q3 table (E4-02). Put E4-03 in v2.13.
   - TC4 = MAX31856 U904, J904, BOM row 205: confirmed against config.h, the bench plan and the BOM. The labels are fixed by E4-05 (6) and E4-06 (3).
   - Consequence: A1 flight is NO-GO until v2.13. Stand first starts are allowed on the fallback within 264 (2).
2. Decision (3), A1 BASE_AMB (264 (3)): agree. The PC_SENSOR abort is fail-safe, and the BASE check itself gives no false E2 (Q3d). The "0 BASE_AMB with option (b)" evidence reproduces byte-identically on v2.12, but it must be re-shown on v2.13, because the hold changes the compensation inside the window.
3. R4-12 (264 (4), C1-family P_torch): agree. Before the re-base, see E4-N04: with the C1-family zero slope, the stand torch zero shift (1.28 x k bar) exceeds the 0.60 bar limit at every k >= 0.47. The re-base therefore needs compensation (a torch-body TC) or a photodiode-guarded gate, and the torch local heat (MISSING) first.
4. N-07 T4 (264 (5), shorter relight): agree. Correct the bench plan T4 row (E4-06 (2)). T4 is a stand relight, so it also waits for v2.13.
5. A1 T0 0-40 C (264 (6)): agree, as an ASSUMED design range. Add E4-N01: either limit the flight-serial T_cal to 10-30 C, or widen kPcSeatArmDevMax_K to 40 K with a test. Otherwise a 0 C day with a 35 C T_cal refuses ARM.
6. OI-JFWD-FLIGHT (264 (7), provisional inhibit): agree. It is not implemented (E4-N02). The 47.5 vs 47.75 bar abs threshold is TO-VERIFY (E4-N03). Implement the inhibit as an ECU flag or FC rule in v2.13, with a test, and add the go / no-go row (E4-05 (5)).

Other 264 items:
- 264 (8): the record re-run is done (section 4).
- 264 (2)'s fallback stand rule (k <= 2 / k <= 1, and the static term inside 0.5 bar): agree. It is the only ignition path open under the carve-out.

## 6. ANSWERS TO THE BRIEF (a)-(j)

- (a) R3 closure: section 3. Every R3 item is CLOSED or CLOSED WITH RESIDUAL, except N-05 and N-08 (OPEN: GNC / documentation). The central R3-01 fix opens E4-01.
- (b) Reproduction: section 4. v2.12 can reach S12 and S13 (purge FINAL, BASE check), and S11 / S14 / S16 through the purge timing. S14 and S16 are identical; S11 is not in the record. The outcome changes are only S12 (1) and S13B (82 / 70), all in the predicted direction. No unlit run reaches RUN.
- (c) Drift model: it reproduces (A2, A3, A5; section 3). It is a static linear coefficient (E4-N07) with ASSUMED budget terms (264 (2) residuals) and the P_mid / U570 drift MISSING. It has no TC-fault mode; the fault mode is E4-01.
- (d) Seat TC4 and the fallback: the channel is confirmed. The failure mode is E4-01 (MAJOR), with the fix in Q2. The fallback reproduces as stated [SIM]: the A1 relight is lost at k = 3 (default build) and from k = 1.5 on the minus sign (B-PC-1-shown build), and the stand relight is refused NOT_VENTED in every arming run. It is fail-safe on the stand within 264 (2).
- (e) Torch and U330: the torch re-zero limit discriminates (Q3c). After 264 (4) it must be re-based (E4-N04). U330: E4-04.
- (f) Decision (3): agree (section 5, item 2); re-show it on v2.13.
- (g) v4.1 folds and consistency: the folds are in E4-05.
  - combustion v2.4d 7dbf425c12300658: purge FINAL 2.43 / 2.39 / 2.38 s and rule (d) with (d1) / (d2) match its "never above these values". E4-N08 asks whether the hardware backstop must also sit inside that bound.
  - gnc v3.2 bde317782574cbd9: the release predicate reads the ECU telemetry Pc, which under (b) is the compensated value. A TC4 error therefore reaches the FC predicate (E4-01). This is an ICD point for GNC, and v2.13's hold covers it.
  - mechanical v2.4 66bc53d88d444679: it lists c1_seat_v352_v1 435f5d71f6213160, the x-check 02a9f27c7965f223 and torch_port_bl08 20220647d32cbbbc, the inputs used. The TC4 mount at the C1 boss is still a Mechanical item.
- (h) Bench plan v5 is executable as written for F-14, F-13, B-TC-1 (case TCs), B-BLEED-1 (d) / (d1) / (d2), B-MV-1 and T1-T4 inside A = 150 C. It is not executable as written for:
  - the B-PC-1 stand sentence (E4-02);
  - the A1 pad row and the T4 row (E4-06);
  - the TC4 rows, which v2.13 changes.
- (i) REV-COMB-4 items:
  - R4-09: confirmed.
  - R4-12: 264 (4), with E4-N04.
  - R4-13: hash verified.
  - R4-02: 10 / 10 and 46 / 46, reproduced byte-identically.
- (j) Rulings: section 5.

## 7. NOT RUN, WITH REASONS

- S11 fault path (sil fault, v2.8 final and the v2.9 variant): NOT RUN. It is not in the v2.11 record, so there is no baseline to compare with. v2.12 can reach it only through the purge timing, which S12, S13, S14 and S16 cover.
- The FC side of E4-01 is not simulated: no FC model, no trajectory. "Drogue release without thrust" is the gnc v3.2 predicate evaluated on the SIL telemetry. Also not evaluated: what the FC does with b4 / b7 at a pad first start.
- The S13T TC-fault set is incomplete. NOT RUN in the time box: GVLO unlit, T0 0 / 40 C, steps inside the P0 window (E1 - 10 ms), and +/-2 K single-conversion steps. Q2 makes them part of the v2.13 set.
- The proposed v2.13 hold and step / rate checks are not implemented or tested by me. Their numbers are DERIVED from the SIM rates and the probe results.
- The first r2v2 attempt in chain4 was killed by me at 9 min (my own PID 3672; run/chain4_note.txt). It was re-run in chain6 with a 35 min cap, finished in 11 min 48 s, rc 0 (section 4).
- Nothing physical: no hardware exists, and nothing was built, weighed or measured.

## 8. FILES (hub reviews/electronics/r4/, sha256/16)

Hub reviews/electronics/r4/ holds 98 files plus MANIFEST_REV-ELEC-4.sha256 (sha16 71fa2008ffca16cb; 98 entries, relative paths; sha256sum -c passes, re-checked after the RAM folder was removed). The folder totals 813,744 B, all net new. Key files:
- scripts/
  - r4_01_c1_drift_v2.py e72d1a2f766ee7e1
  - e4_02_eps_table.py 8cfd6416b913b096
  - probe_v212.cpp dba77df9d38ddb8f
  - probe_v212b.cpp 30df3496d533455e
  - make_fw_rv.py 1b1c7410a94c2a0d
  - r4_02_check.py 52af1e4b6037917c
  - compare_v212_vs_v211_record.py 060ab6422615c1d2
  - csv_tlm_extract.py a6db2643588ed700
  - first_start_extract.py 5d96a881899f173a
  - chain1-6.sh, build.sh, waiter_ignrule.sh
- data/
  - r4_01_c1_drift_v2.json be27767b21f61496
  - e4_02_eps_table.json bc09a12ed3c63351
  - seat_rate_max.json 750d091d7e5ec049
  - e1_timing_unlit.json 79a4722c31002ad2
- run/
  - probe_v212_out.txt 1160f89bf56d0826
  - probe_v212b_out.txt 3ba86883819b401b
  - r4_02_check.json a028f8b493ad7521
  - compare_partB_3.json 1e0706f78bb984b9 (_1 and _2 are earlier partial passes)
  - n04_reclass_rerun.json f3d91aba932ac851 (byte-identical to the staged r4_02_reclass_v2p12.json)
  - the chain logs and chain4_note.txt, test_core_out.txt, test_core_nohooks_out.txt, a_S12_csv_sha256.txt
  - run/a/ and run/rec/ text logs
- run/rv/
  - fw_rv_sil.diff cdbc448343f823a2 (the reviewer SIL variant against the v2.12 SIL)
  - f3/S13T_seat_drift_bpc1_false.json 18616e32c62a5e4b
  - tcs_stand/S13T_seat_drift_bpc1_false.json 5b128644a4f22da7 (log dcfb8b9ae974a927)
  - tcs_a1/S13T_seat_drift_bpc1_false.json a4452c2d4a4f828f (log 21b66ed535448358)
  - tcs_csv/*extract*.json: the per-run E2 / b7 / Pc timing for E4-01
  - fs/*_fs.json: the first starts of Q1, for example A1 fsm30 k3 7a0326d42fa51f5a and stand fsm20 k1 24dd891968e48ab9
The RAM folder /dev/shm/rev_elec4/ has been removed (section 9). The 11 MB SIL CSVs behind the extracts are not kept; their sha16 values are in the extract JSONs.

## 9. PROCESS NOTES

- All times are from date -u. Timeline:
  - RAM folder created 12:58:01Z; build 12:58:23-12:59:54Z;
  - run chains 1-6 from 13:05:47Z to 14:26:21Z;
  - N-04 re-run 14:27:49-14:28:45Z;
  - hub copy and MANIFEST at 14:31Z.
- One heavy process at a time:
  - Six chains, serialised by wait loops. Every build, SIL and probe ran at nice 15 and single-threaded (make -j1). The sil r2v2 RSS was 19,864 kB.
  - Light Python checks (hashing and JSON comparison, seconds each) ran alongside the single heavy process. The N-04 reclassification (56 s) ran alone.
- My own processes that I stopped, by PID:
  - chain1 at 13:40:00Z (PID 29281), to run the MAJOR-class probe first. Its ignrule step's rc was not captured; the step was re-run as ignruleb in chain4.
  - r2v2 at 14:09:19Z (PID 3672). It was re-run in chain6 and finished rc 0.
  I touched no other process.
- SLIPS:
  - one `cd` inside a subshell at about 13:21-13:22Z. Absolute paths only; I know of no effect.
  - one foreground `sleep 1` at 14:09:20Z while stopping r2v2. The brief blocks foreground sleep; it ran 1 s with no effect.
- Disk (GB = 1e9 B):
  - Hub net new: 813,744 B, against the 60 MB cap.
  - Free / was 2,175,438,848 B just before the copy and 2,174,296,064 B after it. The lowest reading I took was 2,170,572,800 B (2.022 GiB) at 14:35:50Z, after the RAM folder was removed, above the 1.95 GiB stop line. Free also fell by about 3.4 MB between 14:16Z (2,178,879,488 B) and the copy, and by 3.7 MB after it. My commands wrote only to /dev/shm then, apart from the 0.81 MB copy; this session's transcript under /root/.claude also grows.
  - /dev/shm/rev_elec4/ was 53,798,142 B at 14:32Z (cap 300 MB). The 11 MB SIL CSVs were deleted after extraction.
  - The folder was removed at 2026-10-21T14:35:50Z (my files only).
- I sent the interim (E4-01 / E4-02) to the lead at 13:57Z by SendMessage. This final report goes by SubagentHandback only.
- Writes went only to hub reviews/electronics/r4/ and /dev/shm/rev_elec4/. No .md, no interface, CHANGELOG, staging, author-folder or SUPERVISION writes, and no git. The CHANGELOG was 265 lines (760cf4fe1fb050d6) at my last read, 14:34Z.
- The author's Python scripts were run with python3 -B -I. The token budget stayed far above 150k, so no handover file was needed.

END REVIEW-ELECTRONICS-R4
```
