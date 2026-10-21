# REVIEW-ELECTRONICS-R3 (REV-ELEC-3)

Independent delta review of Electronics v2.11, closed by the reviewer 2026-10-21T06:57:10Z and returned 06:59:45Z (reviewer stamps, date -u). Saved here by the lead on 2026-10-21T07:05:48Z (date -u), verbatim from the reviewer's final message: the harness does not let a subagent write a report file, so the handback text is the review. Reviewer artefacts: `reviews/electronics/r3/` (`MANIFEST_REV-ELEC-3.sha256` 44fdbc2ebb7e355c, 31 entries, verified by the lead 31/31 OK at 07:02:55Z). Reviewed set: `06-electronics/staging_v2.11/` (`SHA256SUMS-v2.11.txt` dca5c3d8de4d1ea6). Lead disposition: CHANGELOG line 253. A verdict is not physical approval: no hardware exists.

```text
BEGIN REVIEW-ELECTRONICS-R3

REVIEW-ELECTRONICS-R3: independent delta review of Electronics v2.11 (REV-ELEC-3)
Reviewer: REV-ELEC-3 subagent. Review closed 2026-10-21T06:57:10Z and returned 2026-10-21T06:59:45Z (both stamps from date -u).
Scope: the reviewer tried to refute the author's claims. A reproduced number is SIL or derived evidence only. It is not physical approval: no hardware exists and nothing here was weighed, built or measured.

## 0. INPUTS (sha256/16, checked in this review)

- Staging 06-electronics/staging_v2.11/: SHA256SUMS-v2.11.txt dca5c3d8de4d1ea6, 170 of 170 files OK [CALC].
- results/electronics_v4.json: 11f7896ad0d0613b.
- SIL record MANIFEST_v1.json: eaa9efc5112a8178. All 75 of its result hashes match the staged files [CALC].
- Handback ELEC-V211-HANDBACK.txt: 62c967bbe57f8480.
- Baseline: REVIEW-ELECTRONICS-R2.md c7dee8d6c73c9920.
- Interfaces: combustion.json v2.4b fd3a7da6d27c7c66, LC-TB70 lc_tb70_envelope_v1.json 6f710726e4787134.
- Mechanical C1 seat history: pc_transducer_temperature_v1.json 774519536f26c762, with its monitors.csv 84ec53d6b81b4c88.
- The other inputs are as listed in the brief.

## 1. VERDICT

Overall: ACCEPT WITH COMMENTS. Findings: 0 BLOCKING, 1 MAJOR, 5 MINOR, 10 NOTE.

v2.11 can be promoted as the v2.11 SIL and design baseline under two conditions:
- R3-01 is carried as an open MAJOR, and decision (3) stays held.
- The bench plan text corrections are made before the plan goes to the founders.

| Deliverable | Verdict | Reason |
|---|---|---|
| Firmware v2.11 core and SIL record (MANIFEST eaa9efc5112a8178) | ACCEPT WITH COMMENTS as the v2.11 SIL baseline. NOT accepted for the C1 re-zero and BASE constants (R3-01) | Rebuild byte-identical. Full record re-run: 73 files identical and 3 identical except wall-time lines, 0 differ. Threshold probes P1-P5 pass |
| electronics_v4.json | ACCEPT WITH COMMENTS for promotion | Counts verified (47 / 25 / 31 / 29 / 15). Corrections R3-02 (wrong F-14 citation, l.6575) and R3-04 (conditions of the 227 (5) verdict). The lead should add R3-01 to open_issues: the OI-A1-BASE-AMB evidence (0 of 500) is structural |
| Bench plan v4 | REVISE (text only, before it goes to the founders) | R3-02 (F-14 J-FWD rule), R3-03 (B-TC-1 trim step), R3-06 (F-13), R3-05 (C1 compensated band) |
| BOM v2.3 | ACCEPT WITH COMMENTS | R3-05: row 251 order text. 266 rows, all TO-QUOTE to DK-6400 or n/a; no 0 price and no "from" price |
| pc_transducer_v3 (C1 reselection) | ACCEPT WITH COMMENTS | Selection, datasheet arithmetic and mass confirmed. The thermal-zero use in sections E and F is R3-01; the compensated band is R3-05 |
| case_tc_channel_v1 / tf1_rate_v1 | ACCEPT | Arithmetic reproduced. The ASSUMED terms go to B-TC-1, and R3-03 adds the trim step there |
| fa1_chain_v2p11 and the ride-through candidate | ACCEPT WITH COMMENTS | N-04: the 46 of 896 grid cases outside Z3 belong with decision (1) |
| Handback | ACCEPT WITH COMMENTS | Its own findings are confirmed and its numbers traced. Two small count differences are listed in N-10 |

## 2. FINDINGS

### R3-01 (MAJOR). The C1 re-zero and BASE limits were not re-derived for C1, and the S13 A "0 of 500 BASE_AMB" result is structural

This was sent as an interim report to the lead. The lead checked it and asked for it to be carried as MAJOR. Decision (3) is held.

**What the record shows**

- **Re-zero limit.** config.h l.795-807 sets `kPcRezeroMax_Pa` = 0.30 bar [LEAD 2026-10-13, B-PC-1 target]. Its basis comment is still the 070BG: TEB 1.5 %FS = 1.03 bar over -20..85 C, about 0.01 bar/K. It also says "same rule for the torch transducer (same 070BG part)".
- **BASE check.** `kIgnBaseCheck_Pa` = residual + 0.1 bar (l.746-748). That is 0.70 bar in the default build and 0.40 bar in the `kBpc1Shown` build. Neither limit uses the C1 thermal zero.
- **C1 thermal zero.** Typical 1 %FS per 100 F = 0.0248 bar/K [DATASHEET Kulite XTL-190 (M), as recorded in pc_transducer_v3.json]. The maximum is MISSING (F-10). The standard compensated range is 25-80 C [DATASHEET].
- **The SIL has no thermal drift.** sim.h l.72 sets `pc_zero_err` to a constant 0.2 bar, which the ARM auto-zero removes. pcErrG in sim.cpp l.72-79 models span, a constant zero, non-linearity and a pc_off step.
  - So the S13 A Monte Carlo reaches E1 with no residual offset: BASE_AMB 0/250 lit and 0/250 unlit, BASE_HIGH 0/500 [SIM, reproduced byte-identical]. That result holds by construction.
  - S13 C/D exercise only constant in-burn steps of ±0.2 / 0.3 / 0.6 bar.
  - S13 C shows the acceptance edge [SIM]: a -0.3 bar step is rejected (P0 -0.300 bar) while +0.3 bar is accepted (P0 +0.002 bar).
- **Wrong reference temperature.** pc_transducer_v3.py:465 takes dT = at_RELIGHT_C - 20, which is the rise from the 20 C bench trim: 13.8 K, giving 0.343 bar. The re-zero test compares against the ARM zero (engine_ecu.cpp l.486, l.497), so the quantity that matters is the rise since ARM.

**Reviewer calculation** [DERIVED; data/r3_01_c1_drift_v1.json from scripts/r3_01_c1_drift_v1.py]

Basis: Mechanical's A1 seat history (SIM, 20 C start) × 0.0248 bar/K × k, where k = maximum/typical coefficient (ASSUMED sweep 1-3). The relight outcome bands come from the recorded S13 B-ext classes [SIM]:
- default build: RUN for offsets -0.70..+1.00 bar; PC_SENSOR (relight lost) at -0.75..-0.80; TORCH_FAULT at +1.05..+1.20;
- `kBpc1Shown` build: RUN for -0.45..+1.00 bar; PC_SENSOR at -0.50..-0.80.

| Quantity | Node T1_head_top_bracket_foot | Node head_bore_N2O |
|---|---|---|
| Seat temperature at ARM / re-zero2 block (E0 - 2.95 s) / E1 (E0 + 45 ms) | 20.0 / 31.80 / 33.84 C | 20.0 / 38.66 / 39.71 C |
| Re-zero2 shift at typical | 0.293 bar: accepted, 0.007 bar inside 0.30 | 0.463 bar: REJECTED |
| k at which re-zero2 is rejected | 1.024 | 0.648 |
| Drift at the E1 BASE check at typical | 0.051 bar | 0.489 bar (`kBpc1Shown` build: BASE_AMB band) |
| k at which a negative drift loses the A1 relight, `kBpc1Shown` build | 1.46 | 1.02 |
| k at which a negative drift loses the A1 relight, default build | 2.18 | 1.53 |
| Positive drift of 1.05 bar or more | TORCH_FAULT at k ≥ about 3.1 | TORCH_FAULT at k ≥ 2.15 |

Which node represents the C1 diaphragm decides whether re-zero2 is accepted at the typical coefficient. The sign of the coefficient is unknown.

**Exact correction** (for the Electronics round after this review; the reviewer does not fix it)

1. **Coefficient.**
   - Now: the C1 thermal zero typical, 0.0248 bar/K [DATASHEET].
   - When F-10 answers: Kulite's maximum over the ordered compensated band. Until then, carry k as a stated sweep (1, 1.5, 2, 3) [MISSING].
   - The ordered band must be a datasheet "100 F" band that covers the coldest ARM through the hottest relight or burn seat temperature (R3-05).
   - B-PC-1 measures the zero temperature coefficient per serial number over that band.
2. **Seat-temperature source.**
   - Mechanical names the node that represents the C1 diaphragm and port.
   - Mechanical gives that node's history ΔT_seat(t) = T_seat(t) - T_seat,ARM from ARM through:
     - the first coast re-zero (COAST + 1 s);
     - the re-zero2 block before PURGE / RELIGHT;
     - E1;
     - the light.
   - Mechanical then does one of two things:
     - shows that ΔT_seat(t) does not depend on T0 over a stated ambient range. Stand: the T0 ≤ 24 C rule. Flight: no range is bounded today, so one must be stated (for example 0-40 C). For linear conduction with T0 as a common offset the rise is independent of T0 to first order, but this must be shown, for example with the 0.96 factor used in case_tc_channel;
     - or gives the limit as a function of T_seat,ARM.
   - The comparator in item 7 uses T_seat - T_trim, not the rise since ARM.
3. **Re-derive `kPcRezeroMax_Pa`.** It must be at least k_max × 0.0248 × max ΔT_seat(ARM → re-zero2 block), plus the B-PC-1 post-zero residual, plus noise. Two ways to do it:
   - Option a: widen the limit, and state the largest non-vented chamber pressure the wider limit would then accept as a zero. Catching that case is why the limit exists (OI-12).
   - Option b: replace the fixed limit with a temperature-compensated zero. This needs the per-serial coefficient from B-PC-1 and a seat temperature measurement. C1 has no temperature output, so a seat TC or RTD would be added. 0.30 bar is then kept on the compensated residual.
4. **Re-derive `kIgnBaseCheck_Pa`** for both builds. It must be at least residual + k_max × 0.0248 × ΔT_seat(latest accepted zero → E1) + 0.1 bar. State the rejected-re-zero case explicitly; there the full drift since ARM applies.
5. **SIL drift model.** Replace the constant `pc_zero_err` and the pc_off step with:
   - pc_zero_err(t) = s × k × 0.0248 bar/K × (T_seat(t) - T_seat,ARM) on the C1 Pc chain;
   - T_seat(t) interpolated from Mechanical's monitor CSV onto the SIL timeline (A1: MECO 3.54 s, relight E0 22.21 s; B1 for the stand);
   - s = ±1 and k in {1, 1.5, 2, 3} until F-10 answers;
   - the drift applied before the ADC and before the U330 RC. The comparator then also sees (T_trim → T_seat) plus 0.0248 × (T0 - 20 C).
   Do the same for P_mid / U570 at the BL-08 temperature once Mechanical gives it.
6. **S13 A re-run with the drift model.**
   - Matrix: both builds, both signs, the k sweep, the T0 range, and both seat nodes until Mechanical picks one.
   - Report per case:
     - re-zero1 and re-zero2 accepted or rejected (f2 REZERO2 / REZERO2_REJ);
     - the NOT_VENTED flag;
     - BASE_AMB and BASE_HIGH;
     - the relight outcome (RUN / PC_SENSOR / TORCH_FAULT / NO_IGNITION);
     - false E2, which must stay 0;
     - E2 - light, for the IGN-1 margin.
   - Add a stand relight after a B1-length burn (bracket foot 36.2 C at shutdown, soak maximum 118.3 C [SIM]). There the rejected re-zero makes the vented check refuse the relight NOT_VENTED: a refusal on the stand, a flag in flight. Either state that as the expected stand outcome or change the rule.
   - Decision (3) is put to the lead again on that result.
7. **Torch transducer (same rule).**
   - It uses the same `kPcRezeroMax_Pa` (engine_ecu.cpp l.486-488 and l.500-501). Its 070BG basis is unchanged: the torch unit stays the M3200 070BG, TEB 1.05 bar over -20..85 C, about 0.010 bar/K [DATASHEET].
   - Give it its own constant `kPtorchRezeroMax_Pa` with that basis and the torch-port ΔT, which Mechanical has not given [MISSING]. Correct the stale comment at config.h l.795-803.
   - The consequence is bounded [code reading, DERIVED]:
     - the gate needs pt_abs ≥ 2.0 bar abs after a low reading (l.1476-1484), so a +0.3-0.5 bar drift cannot confirm the torch falsely;
     - a negative drift can only delay or refuse the confirmation (TORCH_FAULT, fail-safe).
   - No value change is required until the torch-port ΔT is known.
8. **Hardware comparator U330 (affected).**
   - U330 has no zero. Its Pc-equivalent trip moves by -s × k × 0.0248 × (T_seat - T_trim), with T_trim = 20 C.
   - At typical that is 0.36 bar (bracket foot) or 0.47 bar (head bore) at the end of the relight burn, plus 0.0248 × (T0 - 20 C) [DERIVED].
   - pc_transducer_v3 F gives the circuit band only: ±1.513 bar, i.e. 31.08-34.11 bar abs.
   - Its claim "hardware_low_end_above_firmware_30bar: True (transducer error common to both paths)" is false for the zero term: the firmware path is re-zeroed, the comparator is not.
     - At typical the low end is 30.61 bar abs, still above 30.0.
     - It falls below 30.0 at k ≥ 2.3 (head bore, T0 20 C) or k ≥ 1.3 (T0 35 C). The hardware path then trips first: a latched HW_OVERPRESSURE, which is fail-safe.
   - The FA-1 false-trip margin is kept. With the fixed RC the RC-node maximum is about 25-28 bar abs equivalent (cmp_v_max at tau 10-15 ms) [SIM fa1_chain]. That leaves at least 2.5 bar to the shifted low edge at k = 3 on a hot day.
   - Correction:
     - add the term to the U330 band (per k, per node, with the ambient);
     - restate the ordering claim;
     - re-check the S6R / S6C hardware-only band-high runs with the wider band. No change of conclusion is expected: the tightest case is ramp60_20ms, 13.48 ms above 58.1 bar against 300 ms allowed [SIM].
   - U570 already carries the thermal zero at the BL-08 temperature [MISSING]. Add k_max when F-10 answers.
   - After a rejected re-zero2, the firmware 30 bar abort and the T45 level also move by the uncorrected drift. This is small against their persistence-based margins, but it belongs in the budget.

### R3-02 (MINOR). Bench plan F-14 (J-FWD founder rule) is incomplete, and v4 cites it wrongly

- **What F-14 says (l.61):** "after ANY case-TC abort (OVER_TEMP 6 at 423.15 K) or a TB-state abort the J-FWD joint counts as used".
- **What is missing:**
  - The LC-TB70 rules (l.104-105): "any head excursion above 60.0 bar abs: replace all J-FWD screws (HW-101) and gauge the TC-01 holes / TC-02 taps", and "an event that leaves the envelope ... engine quarantined for inspection".
  - CHANGELOG 248, which puts the founder rule "beside the 60 bar abs rule of the LC-TB70 envelope".
  - A definition of "TB-state abort" in ECU abort codes.
  - The signal that detects a head excursion above 60 bar.
- **Wrong citation:** v4 l.6575 says the 60 bar rule is triggered in 25 required S6R runs and that "after such an abort the J-FWD joint counts as used (bench plan v4 F-14)". F-14 has no 60 bar rule.
- **Why it matters** [SIM, Combustion v2.4a grid replay; grid fractions are not probabilities]:
  - 185 of 896 FA-1 grid head peaks exceed 60 bar abs, so the rule would mark the joint used after about a fifth of normal lights.
  - The C1 chain reading exceeds 60 bar in only 152-168 of 896. The ECU log under-reads the head peak.
- **Correction:**
  1. Add both LC-TB70 rules verbatim.
  2. Define the TB-state abort set with Mechanical and the lead. Proposed: HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START.
  3. State the logged quantity and threshold used to detect more than 60 bar head. Either a C1 raw-peak threshold set from the fa1_chain under-read, or the B-DPC-1 dynamic transducer on the stand.
  4. Fix the v4 l.6575 citation.

### R3-03 (MINOR). B-TC-1 has no CJTO trim step, but the calibrated tolerance and the A 165 re-basing route depend on one

- case_tc_channel_v1 after_B_TC_1_calibration says "offset written to CJTO". Its static worst case of 4.36 K gives tol_lo_cal = 5.85 + 0.630 r: 10.28 K at 7.03 K/s, TC-01 maximum 161.82 C [DERIVED]. Bench plan l.187 and LEAD 249 (3) use those numbers.
- B-TC-1 (l.182) only accepts |offset| ≤ 0.6 K and has no step that writes the offset. Without the trim, a 0.6 K offset stays in the reading: 6.45 + 0.630 r, i.e. 10.88 K and TC-01 162.4 C [DERIVED].
- The EMI row tests "reading spread ≤ 0.5 K". The budget's 0.5 K EMI term is a ground-offset bias, so the test must be a mean shift.
- **Correction:**
  - Add the step "measure at 150 C against the BOM 266 reference, write the offset to CJTO (0.0625 C LSB), re-measure, residual ≤ 0.3 K", or use the untrimmed formula.
  - Change the EMI pass to |mean(actuators on) - mean(off)| ≤ 0.5 K, plus the spike rejection.

### R3-04 (MINOR). The 227 (5) "0.8 s CONFIRMED" verdict omits two conditions found in its own data

All counts below are from the reproduced S17v2 JSON [SIM].

1. **The FC Pc branch.**
   - With the branch on, every normal-family run is released at E2 (0 ms after E2), at both windows, 1000 of 1000. That includes the dead kind, which flames out 1-50 ms later. The evaluator books those as LIT_RELEASED.
   - The verdict's conditions list does not name "Pc branch off, or its threshold moved with margin". It is only in fc_pc_branch_finding.
2. **The cold-flow bound.**
   - At cold flow × 1.3 (in the record), the hold + flush margins fall from +5.789 / +4.954 N to +2.077 / +1.242 N.
   - The FC iid noise budget for P ≤ 1e-3 falls to 1.10 / 0.63 N rms at 0.5 / 0.8 s, against 3.06 / 2.51 N at × 1.0.
3. **The discriminating count.** Of the "0 of 2000" per window, in 1360 runs the ECU leaves RUN (FLAMEOUT) before any R2 decision. 640 runs are decided by R2.

**Correction:** add items 1 and 2 to verdict_227_5.conditions, with the Combustion v2.4a adiabatic bound named as the cold-flow basis, and state the 640.

### R3-05 (MINOR). The C1 compensated band ordered as "20-120 C" contradicts the datasheet clause it cites

- BOM row 251, F-6, F-10 and B-PC-1 (l.151) all order "compensated 20-120 C" and cite "any 100 F range on request" [DATASHEET].
- 100 F is 55.6 K. A 100 K band is not what the sheet offers. The standard band, 25-80 C, does not cover a stand ARM at 24 C or below.
- **Correction:** order a 100 F band that covers the coldest ARM through the hottest relight seat temperature (for example 0-55 C). Or ask Kulite in F-10 for a wider band together with its thermal-zero maximum. Then restate the B-PC-1 zero-TC row over that band.

### R3-06 (MINOR). F-13 leaves out the two terms its 24 C basis uses

- The lead's derivation (249 (2)) is 20 + 4.48 / 0.96 = 24.67 C, less 0.5 K for the facility thermometer.
- The F-13 row (l.60) states neither the soak condition ("engine soaked at the stand ambient") nor the thermometer accuracy (±0.5 K).
- **Correction:** add both, with a soak criterion, for example both case TCs within 1 K of the facility thermometer for N minutes.

### NOTES

- **N-01. S6R decay model.** ramp60_50ms aborts at the same firmware time (34 ms) in both builds, but the head peak is 56.61 bar as built against 47.94 bar with the ride-through [SIM; data/s6r_ramp60_50ms__*.csv].
  - Cause: the as-built comparator drops the ARM bus at 5.211 s against 5.218 s, and the pintle is powered from the ARM bus (sim.cpp l.289).
  - The post-abort model gop = profile × ff is ASSUMED.
  - Both results are inside LC-TB70 (Z1 margin 1.49 bar). B-MV-1 / HIL should confirm the post-abort closure.
- **N-02. S6R input_peak field.** For the slow ramps it reports the profile value at the abort (36.41 / 18.71 bar), not the 60 bar target. No classification depends on it.
- **N-03. T45 guard.** In the 9 ride-build ideal-step runs T45 never fires; the window end or the comparator ends them. Only 4 runs discriminate the guard. The 1.0 ms rise convention hides no envelope failure.
- **N-04. Ride-through against out-of-envelope FA-1** [SIM, fa1_chain_v2p11_cases.csv]:
  - 46 of 896 grid head peaks are above Z3 (75.519 bar). 29-33 of them abort as built and 0 with the ride-through.
  - 95 are in the Z3 band with the 3 ms / 0.8 ms rule unchecked; 67-69 of them abort as built.
  - Routing to REV-COMB-4 and Mechanical (OI-S6R-INPUT / OI-FACE-PEAK) is right. The numbers should go with decision (1).
- **N-05. Offline evaluation.** The S17v2 offline R2 v2 evaluation on recorded histories is not a strict closed-loop bound. GNC's re-run with the flush closes it.
- **N-06. Stand false-trip spare.** At stand T0 24 C the false-trip spare is 0.64 K [DERIVED: 12.26 - 0.96 × 4 - 7.78]. It rests on the ASSUMED EMI 0.5 K, CJ gradient 1.0 K and inhomogeneity 0.3 K, which B-TC-1 must measure.
- **N-07. DC-D first burn.** The DC-D first burn (31.76 s) would cross A = 150 C at about 23.5 s (merged bound), 26.4 s (GVHI) and 27.9 s (GVLO) if the B1 end-of-burn rate held [DERIVED, linear extrapolation of the case_tc_channel station data]. Combustion and Mechanical should re-size the T1-T4 DC-C / DC-D segments.
- **N-08. Pc_f at E2.** The 3.04 bar abs value is quoted from the sc_v211_r2.inc header and was not reproduced independently: the record holds no per-run Pc_f series. The behaviour (release at 0 ms in 1000 of 1000) is confirmed.
- **N-09. Stale comments.** Those at config.h l.757-768, 832-834, 865-866 and 900 are confirmed and disclosed in OI-STALE-LABELS. l.795-803, the 070BG re-zero basis, is not listed there; it is covered by R3-01.
- **N-10. Combustion v2.4b stale texts (author's finding).** Confirmed. My regex finds 6 "112 bar abs" and 4 "E0 + 0.15 s" occurrences; the handback says 4 and 3 places. The other self-reported findings are confirmed:
  - the S12 label: both_open_at injects BOTH valves; the 4 S12 fails are the both-stuck-open cases;
  - IGN-1: 20.0 ms at the -0.6 bar S13 D corners;
  - the LC-TB70 Z1 label reads "case at the 448.15 K abort" (l.30);
  - S6 band_high is fixed.

## 3. REV-ELEC-2 CLOSURE (23 items)

| R2 item | Author status | Reviewer | Evidence (reproduced unless noted) |
|---|---|---|---|
| R2-01 MAJOR | CLOSED WITH RESIDUAL | AGREE, CLOSED WITH RESIDUAL; R3-04 adds conditions | S17v2 counts traced (section 4). Residuals: GNC re-run, OI-FC-PC-BRANCH, OI-PHOTODIODE-VIEW |
| R2-02 MAJOR | CLOSED WITH RESIDUAL | AGREE | test_core v211b-2: backstop at E2 + 0.850 s, 1 event, hold 699/699 ticks; per-burn reset; B-FC-1 row l.284. Residual: OI-FC; link latency 10 ms ASSUMED |
| R2-03 MAJOR | CLOSED WITH RESIDUAL | AGREE; still a CANDIDATE | C1 chains: longest filtered run above 30 bar 12.0 ms → 15 ms persistence; RC ≥ 10 ms gives 0 low-band trips; over-range 0/896; as built 374-379/896 abort, with the ride-through 0; S6R 105/105 required runs inside, 0 put outside by the ECU; S6C 21/21 inside. Residuals: schematic v2.6, OI-SEAT-RINGING, N-01, N-03, N-04, the R3-01 band term |
| R2-04 MAJOR | CLOSED WITH RESIDUAL | REOPENED IN PART via R3-01 | Per-location criteria met (S13 B-ext 0 fails in both builds, 246 runs each). The A1 BASE_AMB outcome evidence (0 of 500) is structural |
| R2-05 MAJOR | CLOSED WITH RESIDUAL | AGREE | One basis, 29.25 g/s. At the cap (2.60 s flow) 76.05 / 80.76 / 86.14 g; scheduled 73.13 / 77.65 / 82.83 g; timer bound (2.791 s) 81.65 / 86.70 / 92.48 g; PURGE_WIN 96.33 / 102.29 / 109.10 g [DERIVED]. S12 EVIDENCE: 81.79 g at the cap; timer alone 82.61 / 85.21 / 87.84 g at 2.577 / 2.659 / 2.741 s; 0 timer cuts in the normal cases [SIM]. Residual: the cap decision; timer not drawn; DIVCODE AS RECALLED |
| R2-06 MAJOR | CLOSED | CLOSED WITH RESIDUAL (R3-02, R3-06) | F-1..F-14 can be executed now |
| R2-07 MINOR | CLOSED | AGREE | v4 pc_overrange_fa1.firmware_behaviour gives the per-tick validity |
| R2-08 MINOR | CLOSED | AGREE | No-hooks build 325/0; log 226a5bb1e36b1954 identical |
| R2-09 MINOR | CLOSED (disclosed and explained) | ACCEPT the explanation | RE-04 lift clamp plus integrator hold: a jam at a steady command is caught when the command moves |
| R2-10 MINOR | CLOSED | AGREE | Statistics over the 230 flying of 300 runs, with denominators |
| R2-11 MINOR | CLOSED (cold side) | AGREE | S10v211: 17 cases, 0 fail; 1.5 × 0.2219 + 0.07 = 0.4029 ≤ 0.42 K. Hot side stays OI-GUARD-BAND |
| R2-12 MINOR | CLOSED | AGREE | A7 comment fixed; "4.75 V = 73 bar" is gone. Other stale comments: N-09 |
| R2-13 MINOR | CLOSED WITH RESIDUAL | AGREE | OI-E0-SUPPLY row, B-PNT-1, IGN-1 ≤ 20 ms (no margin at -0.6 bar), T1-T4 written out, LOST DROGUE 0 row |
| R2-14 MINOR | CLOSED | AGREE | BOM rows 212 / 214 O2-clean notes; row 245 medium separation |
| R2-15 MINOR | CLOSED | AGREE | S6 record: 53.42 bar abs, 0.033 s above MEOP |
| R2-16 MINOR | CLOSED | AGREE | Starve threshold 0.45 s at 0.5 s and 0.75 s at 0.8 s (reference none). Reference at E2: never / 0.70 s. Reference at the light: 0.40 / 0.75 s |
| R2-17 NOTE | CLOSED | AGREE | No "06/2026" left |
| R2-18 NOTE | NOTED | AGREE | C1 SIL chain limits each sample |
| R2-19 NOTE | NOTED | AGREE | S15 stand: 4 of 230 NO_IGNITION; IGN-1 row exists |
| R2-20 NOTE | CLOSED | AGREE | test_core.json is v2.11; BOM row 250 says HARD; leftovers disclosed |
| R2-21 NOTE | CLOSED | AGREE | Four C1 chains in fa1_chain_v2p11 |
| R2-22 NOTE | CLOSED | AGREE | `kR2HoldLift_m` 0.21776 mm = `kIgnLiftTab_m[6]` at 286.70 K (the A1 row) |
| R2-23 NOTE | CLOSED | AGREE | One HIGH tick engages the hold for one tick. A late glitch at E2 + 350 ms trips U330 (HW_OVERPRESSURE, OI-R2-23-GLITCH) |

Summary: 21 agreed as stated (residuals noted), 1 downgraded from CLOSED to CLOSED WITH RESIDUAL (R2-06), 1 reopened in part (R2-04, through R3-01).

## 4. CONFIRMED NUMBERS

All are SIM or DERIVED and reproduced by the reviewer. None is physical approval.

**Build and SIL record**
- Rebuild byte-identical [CALC]: sil d4bf5d5436a179e6, sil_bpc1 6c7a32aeb66bebf4, test_core 361d7182363c0d54, test_core_nohooks 2715becf5628c699.
- test_core 326 passed / 0 failed; no-hooks 325 / 0 [SIM].
- Full SIL record re-run: 76 recorded files. 73 are byte-identical. 3 are identical except wall-time lines: sil_all_time.txt, S17v2_log.txt and S17v2_r2v2_sweep.json (wall_s). 0 differ [SIM; data/repro_compare_v2p11.tsv].

**S17v2** [SIM]
- Hold + flush, W10 < 6: 0/2000 dead runs released at each window. Minimum margins +5.789 N (0.5 s) and +4.954 N (0.8 s).
- No hold: 320 of 1000 released.
- No flush: 264 / 326 (normal) and 160 / 172 (starved040).
- Photodiode-blind families: 20 / 42 and 42 / 98.
- All winds at 0.8 s: 320.
- Noise budget [SIM + DERIVED, iid ASSUMED]: 3.06 / 2.51 N rms iid and 2.00 / 1.65 N AR(1). At 5 N rms, P = 6.9 % / 22.9 %.

**Case-TC channel** [DERIVED on DATASHEET MAX31856 19-7534 Rev 0, LITERATURE IEC 60584-1 AS RECALLED, and ASSUMED terms]
- High-reading error 7.78 K worst case, 3.55 K RSS. False-trip margin 12.26 K.
- Nominal burn: 137.74 + 7.78 = 145.52 C < 150 C, so no false trip.
- tol_lo = 9.05 + 0.630 r. Calibrated: 5.85 + 0.630 r = 10.28 K at 7.03 K/s.
- Relight limit: 130 + 15.9 = 145.9 C ≤ 150 C.
- The T-F1 A 175 basis follows (7.03 > 7.00 K/s).

**Reviewer threshold probes** [SIM, logic rig, TEST VALUES; scripts/probe_thresholds.cpp; data/probe_thresholds_out.txt]: all pass with ±0.05 K steps.
- P1 stand T0: at 297.15 K exactly → ARMED; +0.05 K → CASE_WARM_STAND on TC1 and TC2; flight not affected.
- P2 ARM start limit: 403.15 K + 0.05 → OVER_TEMP in both modes.
- P3 COAST RELIGHT: 403.15 K + 0.05 → refused CASE_HOT (TC1 and TC2); - 0.05 → accepted.
- P4 in-burn abort: 423.15 K - 0.05 → no abort in 1.5 s; + 0.05 → OVER_TEMP at 200 ms; hot for 190 ms → no abort; hot for 210 ms → abort; stand mode the same.
- P5: 430 K in COAST for 1 s → no abort.

**Other confirmed values**
- U330: 32.59 bar abs, circuit band ±1.513 bar [DERIVED].
- Mass: net -0.061 kg; worst combination +0.025 kg, below the 0.10 kg trigger [DERIVED; cable mass ASSUMED].
- S6R / S6C counts as listed under R2-03.

## 5. RECOMMENDATIONS ON THE SIX DECISIONS

1. **Ride-through: adopt, as the flight-relight build option.** As built, 374-379 of 896 grid relights abort; with the ride-through 0 [SIM]. The independent hardware path keeps a fixed RC. Conditions:
   - schematic v2.6 is drawn;
   - the R3-01 drift term is added to the bands;
   - OI-SEAT-RINGING is closed at B-DPC-1 / HIL-TR-1;
   - the lead sees N-04: with the ride-through, 29-33 out-of-envelope grid cases continue to burn instead of aborting. REV-COMB-4 / Mechanical should settle whether those peaks are real.
2. **Purge: take the 2.43 s flow with the 2.39 s cap**, if Combustion confirms that a 2.43 s purge is adequate. Its comment gives a shortest adequate purge of 1.0-2.0 s.
   - The warm-end scheduled mass is then 75.5 g, inside 76 g, against 77.65 g today; at the cap 75.8 g [DERIVED].
   - Otherwise GNC must accept 80.76 g.
3. **A1 BASE_AMB outcome: keep it held** (R3-01). If the re-derived drift exceeds the re-zero acceptance, re-centre or compensate the zero (R3-01 item 3, option b) rather than accept a lost relight.
4. **Unprimed / UNKNOWN relight with the bleed fitted: keep the refusal for A1 (fail-safe).** Record the lost-relight mission consequence with GNC until Combustion models an unpurged relight.
5. **Both bleed valves stuck open: carry it as an FMEA residual for A1** (104.17 g in the first burn, leak flag 5.05 s after injection [SIM]). Keep the pad BIT. The low U570 threshold has not been shown to separate the cases.
6. **Cite MANIFEST eaa9efc5112a8178.** It is verified: its 75 result hashes match, and the binaries equal the rebuild.

## 6. ANSWERS TO THE BRIEF (a)-(i)

- (a) Section 3.
- (b) Sections 4 and 2. All re-runs are byte-identical. My probes discriminate the limits that the author's ±0.5 K / +1 K / 600 K tests cannot.
- (c) Confirmed (section 4; N-06).
- (d) band_high is fixed. Seat ringing / the 1.0 ms rise convention: N-03. A1 BASE_AMB: R3-01.
- (e) Counts and self_check verified. Corrections: R3-02, R3-04.
- (f) R3-02, R3-03, R3-06. The B-FC-1 LOST DROGUE 0 row agrees with the firmware.
- (g) Datasheet arithmetic: 2000 psia = 137.9 bar; proof 1.5 × = 206.8 bar; 0.0248 bar/K. Mass and BOM rule met; R3-05.
- (h) The S6R input routing is right. No v2.11 claim depends on those runs (the 0/896 is a detector-side result); N-04.
- (i) Section 5, plus N-08 to N-10.

## 7. NOT RUN, WITH REASONS

- SIL run with a seat-temperature drift model. The fix and the S13 A re-run belong to the Electronics round (lead); R3-01 gives DERIVED bands instead.
- Independent Pc_f-at-E2 series. The record has no per-run Pc series; an instrumented S17v2 run is outside the time box.
- Re-fetching the Kulite and MAX31856 datasheets. Values were checked only for consistency with the author's quoted sources (TO-VERIFY remains, F-10).
- Re-implementing the S17v2 noise recursion. The values were traced to the record only.
- Any hardware or bench item. No hardware exists.

## 8. FILES

reviews/electronics/r3/MANIFEST_REV-ELEC-3.sha256 is 44fdbc2ebb7e355c: 31 entries, all OK, 468 kB in total. The RAM folder /dev/shm/rev_elec3 has been removed. Entries (sha256/16):

**data/**
- data/build_v211.log 2c5021a0462ce47a
- data/probe_thresholds_out.txt 71dcc7fc65b57aec
- data/r3_01_c1_drift_v1.json 70eb36f6484ccc2b
- data/repro_compare_v2p11.tsv 9bd906027d2480e5
- data/rest_chain_log.txt 9c454e1fdf0cdec2
- data/s6r_ramp60_50ms__as_built.csv e8b644ec3feb1390
- data/s6r_ramp60_50ms__ride.csv c874ad442d7088d0

**diff/** (v2.10 hub → v2.11 staging)
- diff/Makefile.diff b6c664a59a84dd54
- diff/sil_ovp_hw_params.h.diff fd75a47e73d1dbc0
- diff/sil_plant.cpp.diff 56a7ba97852a49d9
- diff/sil_plant.h.diff eafdee599fe69e98
- diff/sil_sil_main.cpp.diff 8e975bed675fa572
- diff/sil_sim.cpp.diff d040d1d00cb05d1a
- diff/sil_sim.h.diff ef6945180dac42a4
- diff/sil_test_core.cpp.diff 6385af7f76c08003
- diff/sil_test_v210.inc.diff e30abe71b88dae92
- diff/src_core_config.h.diff 3ae586a8784e0472
- diff/src_core_control.cpp.diff 7efd0e7f63440a3a
- diff/src_core_control.h.diff 038034493af9638b
- diff/src_core_engine_ecu.cpp.diff ba55c996892cb485
- diff/src_core_engine_ecu.h.diff 6aa710043dd83c45
- diff/src_core_filters.h.diff e3b0c44298fc1c14 (empty: no change)
- diff/src_core_protocol.cpp.diff e85f1c86dbfab17b
- diff/src_core_protocol.h.diff a9200ed4a729b4f5
- diff/src_core_sensor_scale.cpp.diff 1e42e5d353ee7f4d
- diff/src_core_sensor_scale.h.diff d54ee3298f539eaa
- diff/src_core_types.h.diff af957675901d4f11

**scripts/**
- scripts/probe_thresholds.cpp 58c33b99225493a8 (build line in its header; rebuild from the staged firmware tree)
- scripts/r3_01_c1_drift_v1.py 7b7a82fcf75241de (re-runnable: reads Mechanical's files)
- scripts/repro_compare_v2p11.py dbb2d877774dc718 (its RAM-folder inputs are removed by rule)
- scripts/rest_chain.sh 50b260d095802cac (commands follow sil_v2p11_runmap.json)

## 9. PROCESS NOTES

- Twice I used `cd` inside a compound read-only command: a file listing, and writing the MANIFEST with relative paths. No other file was touched.
- Earlier in the session one command contained `sleep 1`.
- Neither had any effect on inputs or outputs.
- Every heavy process was mine, run one at a time at nice 15. Lowest free disk was 2217 MiB.
- No writes outside reviews/electronics/r3/ and /dev/shm/rev_elec3/. No git operations.

END REVIEW-ELECTRONICS-R3
```
