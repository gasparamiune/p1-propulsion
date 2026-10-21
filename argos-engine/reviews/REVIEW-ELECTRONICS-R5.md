# REVIEW-ELECTRONICS-R5 (REV-ELEC-5)

Independent delta review of Electronics firmware v2.13, closed by the reviewer 2026-10-21T19:12:54Z (reviewer stamp, date -u) and returned 19:16:10Z (transcript); the handback reached the lead at 19:16:13Z (transcript). Saved here by the lead on 2026-10-21T19:20:47Z (date -u), verbatim from the reviewer's final message (lead copy: scratchpad handbacks/REV-ELEC-5-FULL-1912Z.txt 3a6355acd6ecf89f): the harness does not let a subagent write a report file, so the handback text is the review. Its interim (E5-05, 18:41:08Z) and the lead ruling of 18:43Z (option (A)) are answered in its sections 2 and 8. Reviewer artefacts: `reviews/electronics/r5/` (`MANIFEST_REV-ELEC-5.sha256` 48d5f6a11c81d529, 33 entries, verified by the lead 33/33 OK at 19:19:09Z). Reviewed set: `06-electronics/staging_v2.13/` (`SHA256SUMS-v2.13.txt` 3dde265441938225). Verdict: ACCEPT WITH COMMENTS, 0 BLOCKING; carve-out 266 (6) LIFT IN FULL with conditions; A1 FLIGHT stays NO-GO on five items (section 16). Lead disposition: CHANGELOG line 270. A verdict is not physical approval: no hardware exists.

```text
BEGIN REVIEW-ELECTRONICS-R5

# REVIEW-ELECTRONICS-R5: independent delta review of Electronics firmware v2.13 (REV-ELEC-5, max rigour)

**Closing stamp:** 2026-10-21T19:12:54Z, from date -u run just before this handback.

**Inputs**
- Brief: LS/brief_REV-ELEC-5.txt 926e86dfc0240141 (lead, 17:52Z).
- Lead ruling on E5-05: LS/handbacks/LEAD-TO-REVELEC5-E5-05-1843Z.txt 1dd9b9abc4d115e5 (18:43Z).
- Author handback: ELEC-V213-HANDBACK-1740Z.txt bfabdfc3643b9980.

**Reviewed (sha256/16)**
- staging_v2.13/results/electronics_v4.2.json de02c29f9add1979
- staging_v2.13/docs/bench_plan_v5_1.md 8b052fb2006ee859
- staging_v2.13/results/bom_v2p5.csv d684c4442e48a6eb
- the v2.13 firmware overlay (core: config.h, engine_ecu.cpp/.h, protocol.cpp/.h; SIL sim.cpp; tests)
- interfaces/CHANGELOG.md c915eed88ef3e9a6 (269 lines)

**Nothing here is physical approval.** A reproduced number shows that a computation repeats. It does not show that the hardware or the physics is right.

---

## 0. Bottom line

- **No BLOCKING finding.**
- **One MAJOR finding, E5-05.** The 17:50Z FC rule for A5 could not be implemented on the v2.13 CAN interface. The lead's 18:43Z ruling (option (A)) resolves it. I agree with that ruling, including deferring b2 (section 8).
- **Six MINOR findings** (E5-01 to E5-04, E5-06, E5-07) and **fourteen notes**.
- **The E4-01 fix works as designed [SIM].**
  - A TC4 error that starts inside [IGNITION entry, E2 + 0.45 s] never moved the compensation, P0 or the E2 tick. It never produced an unlit E2 (probe H: 2016 in-window runs per build out of 2464, both builds).
  - In the hold-disabled control the compensation moved in 256 runs, so the probe does detect movement when the hold is absent.
- **Reproduction is byte-identical.** All four binaries and every cited SIL output match the staged files. test_core: 343 passed / 0 failed. No-hooks build: 342 / 0 [SIM].
- **Carve-out 266 (6): LIFT IN FULL**, with conditions for each unit. Its own condition (a reviewed v2.13 delta with the light-window hold and the TC4 step / rate checks) is now met. A1 FLIGHT stays NO-GO on five items (section 16).

## 1. Verdicts

| Deliverable | Verdict |
|---|---|
| Firmware and SIL v2.13 | **ACCEPT WITH COMMENTS** |
| electronics_v4.2.json | **ACCEPT WITH COMMENTS** |
| Bench plan v5.1 | **ACCEPT WITH COMMENTS** |
| BOM v2.5 | **ACCEPT** |
| **Overall** | **ACCEPT WITH COMMENTS** |

- **Firmware and SIL v2.13:** no code change is needed now. E5-05 is resolved by ruling. The comments are a comment fix (F1), a test-wording fix (E5-02) and the overflow tripwire (N10).
- **electronics_v4.2.json:** promote it byte for byte. Line 270 carries the corrections in section 15 (V1 to V13).
- **Bench plan v5.1:** line 270 carries B1 to B9.
- **BOM v2.5:** 266 → 269 rows. Rows 267-269 are added: P_torch Kulite XTL-190SM-2000A, its bridge amplifier, and the stand-DAQ C7 bore-top TC. Rows 81, 83, 187, 199, 205 and 225 change, all consistent with 264 (4), the TC4 relabel and E4-06 [CALC bom_diff.py]. N12 is a truncation that predates v2.5.

## 2. Findings

### E5-01 (MINOR): the FMEA residual understates the followed-drift exposure

This is fmea_rows_a1[5] FMEA-A1-TC4-READING. Its residual says "<= coef x 3 K = 0.22 bar at k = 3". That is true only for a step split over conversions.

**What happens.** Outside the hold, an error that passes both checks is followed without limit up to kPcSeatDevMax_K = 150 K. Passing both checks means ≤ 1.5 K per conversion (step check) and a ramp ≤ 5 K/s (rate check).

**Probe D** (coast, k 3) [SIM]:

| Ramp | Result |
|---|---|
| 2.0 K/s for 20 s | 40 K, 2.98 bar, no flag |
| 4.9 K/s | 98 K, 7.29 bar, no flag |
| 5.5 K/s | trips at 6.05 s (30.27 K, 2.252 bar) |
| 7.0 K/s | trips at 1.502 s (7.51 K, 0.559 bar) |
| 14 K/s | trips at 0.333 s (1.66 K, 0.124 bar) |

**Bound** [CALC]
- coef × 150 K = 3.7 bar at k = 1 and 11.2 bar at k = 3.
- s = −1: true Pc up to 36.2 bar abs at the 25 bar cap and 41.2 bar abs at the 30 bar firmware abort. MEOP is 45 bar.
- s = +1: true Pc below the landing floor at low setpoints.
- Backstops: U330 on the raw path (independent of the compensation), the A7 map (flight flag), and the range / 150 K checks.

**Context.** v2.12 had no step or rate check, so v2.13 strictly reduces the exposure. What remains is the slow-drift class: a creeping junction debond, or a lead short that warms slowly.

**Correction**
- fmea_rows_a1[5].residual becomes V11.
- Add a v2.14 candidate, OI-TC4-DRIFT-BOUND (owner Electronics, MEDIUM): bound the T_c travel since ARM to the profile's physical seat rise plus a margin. A cumulative-rate bound is an alternative. Either way, a followed drift then has a stated bar limit.

### E5-02 (MINOR): a step up to 3 K split over two conversions is followed, not tripped

**Probe S** (coast, k 3) [SIM]:

| Step | Result |
|---|---|
| 2.90 K as 2 × 1.45 K | no trip, 0.216 bar |
| 3.20 K as 2 × 1.60 K | trips |
| 1.40 K as 2 × 0.70 K | no trip, 0.104 bar |

**Why it matters on hardware.** A TC simulator edge is not synchronised to the MAX31856 conversion. A ±2 K step can therefore land as two partial steps and be followed, adding ≤ 0.22 bar at k = 3 [SIM].
- Bench l.223 says ±2 K steps "set SEAT_STEP". That is not deterministic on hardware.
- The ±2 K criterion was mine (R4 Q2; see N11).

**Correction**
- Bench l.223 becomes B5.
- The UT-2 description (test_v213 and any text that cites it) becomes "a step presented to the core within one conversion".

### E5-03 (MINOR): claim 2 (BASE_AMB → PC_SENSOR at the A1 relight) depends on the light time

**Probe A** (A1 flight relight, k 3, SEAT_STEP latched in coast, stale offset e) [SIM]

Default build:
- Light at E1 + 128 ms: e from −0.77 to −3.80 bar gives BASE_AMB → PC_SENSOR (pintle 0.205 mm).
- Light at E1 + 50, 60 or 80 ms: PC_SENSOR.
- Light at E1 + 30 ms:
  - −0.77 bar: E2 at E1 + 47 ms, RUN;
  - −1.00 bar: E2 at E1 + 48 ms, RUN;
  - −2.00 bar: NO_IGNITION;
  - −3.80 bar: PC_SENSOR.

bpc1 build:
- BASE_AMB from −0.48 bar → PC_SENSOR with the light at E1 + 128 ms.
- With the light at E1 + 30 ms, RUN on P0 = 0 for −0.48, −0.77 and −1.00 bar.

**What it means.** With an early light, E2 follows the real light on P0 = 0 and the offset rides into RUN. This is not a false E2.

**Bound** [CALC]
- |e| < 2.0 bar (NO_IGNITION at −2.00 bar on this grid; a finer grid was NOT RUN).
- True Pc ≤ 27 bar abs at the 25 bar cap and ≤ 32 bar abs at the 30 bar firmware abort. MEOP is 45 bar.

**Effect under option (A).**
- No SEAT_STEP stale offset reaches the A1 relight start: a trip before the command is refused with code 19. A trip after the command gives about 0.04-0.07 bar, far inside the −0.76 bar gate.
- So the operational effect is small. The finding corrects the record, because other zero errors can still reach BASE_AMB.

**Correction:** V4, and the 264 (3) evidence condition in section 16.

### E5-04 (MINOR): the B-TC-1 EMI pass criterion measures the wrong quantity

- The criterion is set on the deviation, but the step check acts on the change between consecutive conversions.
- The hold-end gap check, by contrast, does depend on the deviation.
- The physical change per 0.130 s conversion is 0.31 K [CALC: 2.42 K/s × 0.130 s].
- The stand's physical hold-end gap of 2.06 K against the 3 K rate trip [DERIVED, v4.2] leaves 0.94 K for noise.
- Under option (A), a nuisance SEAT_STEP before the relight command costs the A1 vehicle (code 19, then the lost-relight outcome). The EMI row must therefore test what actually trips.
- The criterion came from my own R4 Q2 (N11).

**Correction:** B5.

### E5-05 (MAJOR): no CAN channel for f3; the 17:50Z FC rule could not be implemented. RESOLVED by the 18:43Z ruling (option (A))

**Code facts (v2.13)**
- f3 SEAT_STEP exists only in Outputs and in log v13 f3_flags b7 (engine_ecu.cpp l.1449-1453, l.2067, l.2175).
- protocol.cpp encodes no f3 bit.
- TLM_SLOW 0x110 is NOT DEFINED.
- TLM_RELIGHT d2 bits b0-b7 are all in use.
- No EVENT code exists for SEAT_STEP.
- With kSeatStepRelightInhibit false (as built), startBlock() l.581 returns no SEAT_STEP reason, so TLM_RELIGHT d6 shows nothing.

**Ruling (A).** Agreed; see section 8 for my reasoning.

**Remaining correction:** a comment fix in config.h, F1 in section 15.

### E5-06 (MINOR): bench plan B-ECU-1 rows l.139-140 still carry v2.12 text

- l.139 cites protocol.h v2.12. It lists neither BUILD 0x25 nor refusal reasons 17-19.
- l.140 lists f3 b0-b6 only (b7 SEAT_STEP is missing). It has no ovr_flags b7 and no abort_cause 32.
- No B-ECU-1 row checks the A1 image's build constants functionally.

**Correction:** B7 and B3.

### E5-07 (MINOR): v4.2 texts that are stale or inconsistent

Promote byte for byte; line 270 governs.
- log_v13.v says "b7 zero"; b7 is SEAT_STEP in v2.13. Correction: V9.
- The "6 x 2.42 K/s x period" rule contradicts the as-built 1.5 K at 0.130 s, which is a 4.77× margin [CALC]. The rule actually in use is 4×. It appears in tc4_hal_contract_v2p13.step_limit_margin and in bench l.224. Correction: V10 and B6.
- Several texts predate the 17:50Z and 18:43Z rulings. Correction: V1 to V8. The texts are:
  - limits_v2p11[33];
  - v2p13_delta.A5_recommendation, A5_seat_step_option and residual;
  - open_issues[35] and [37];
  - pad_rule_264_2.build_requirement and reporting;
  - fmea_rows_a1[6];
  - pad items[7] and [8];
  - can_interface EVENT_BUILD.arg.
- The E5-01 and E5-03 texts. Correction: V4 and V11.

## 3. Notes

- **E5-N01.** S13F contains only step faults: all 2576 of 2576 runs latch SEAT_STEP. It tests the step check, not the hold. The hold is evidenced by UT-1 and probe H.
- **E5-N02.** The UT-6 catch-up ratchet (fmin) is not tested on its own. Add a case: reading static for 0.10 s after the hold end, then 7 K/s.
- **E5-N03.** Use the 4× rule everywhere: 1.5 K holds up to a 0.155 s period [CALC]. See V10 and B6.
- **E5-N04.** Measure the conversion period with the flight image's open-circuit fault detection (CR0 OCFAULT) setting enabled. Fold this into E4-N10. See B6.
- **E5-N05.** After a dropout, the step check compares against the last valid reading.
  - A dropout of ≥ 0.62 s at 2.42 K/s gives a nuisance trip. At 0.66 K/s the dropout must last ≥ 2.3 s [CALC].
  - This is fail-safe, but under option (A) it costs an A1 relight.
  - v2.14 candidate: re-seed with a rate-bounded allowance.
- **E5-N06.** The n2o files are byte-identical across builds. That is expected: they have no build field.
- **E5-N07.** config.h l.906 says the hold cost is "inside the kIgnBaseDrift basis". The envelope value is 0.072 bar at k = 3 (0.97 K), which is above kIgnBaseDrift 0.06 bar [CALC]. The cost comes mostly off the unlit-rise margin, which stays ≥ 0.22 bar [DERIVED, REV-ELEC-5 working]. The S13T-time values (0.033-0.039 bar) are inside the basis. Correction: F2.
- **E5-N08.** Add EVENT BUILD b3 = jfwd_relight_inhibit in the same change as b2. Nothing reports it today. The core default is TRUE, so the risk is lower than for b2.
- **E5-N09.** Purge cooling of the seat-TC node is MISSING (Mechanical). It affects the coast seat history and the A5 stale-offset sizes.
- **E5-N10.** Add an overflow tripwire: assert g_state_cause_overflow == 0 at the end of test_core and of every SIL run.
- **E5-N11.** Corrections to my own R4 text:
  - the "0.8 s / 1.9 K" figure in Q2 is wrong (the as-built margins are in section 7);
  - the two B-TC-1 criteria I proposed (corrected by E5-02 and E5-04);
  - the kIgnBaseDrift wording (N07);
  - "the rate check catches a ramp-type error": ramps ≤ 5 K/s are followed (E5-01).
- **E5-N12.** BOM row 187's description is truncated at "(L". This predates v2.5.
- **E5-N13.** Two v2.12 tests changed their step inputs to 4 K/s ramps, because a step now trips SEAT_STEP. That is acceptable, but the change should be listed in the v4.2 change summary.
- **E5-N14.** The FC release predicate needs a false E2 with ≥ 30 K at k 3. It cannot be reached in the window: 0 false E2 in probe H [SIM].

## 4. Q2 and E4 closure table

The author's statuses are truthful. The exceptions are wording only (E5-01, E5-03, E5-07).

| Item | Status | Evidence |
|---|---|---|
| Q2-1 light-window hold | CLOSED | Code l.(seatCompStep hold: st_ == IGNITION \|\| t < t_e2 + 0.45 s, judged at the start of the tick; the entry tick moves T_c by at most 5 K/s × 1 tick); UT-1 PASS; probe H 0 / 2016 per build [SIM] |
| Q2-2 step / rate checks | CLOSED WITH RESIDUAL | UT-2, UT-3, UT-6 PASS; S13F; probes S and D (E5-01, E5-02) |
| Q2-3 E4-03 fix | CLOSED | canArm no longer subtracts the static term twice; Q1 probe 0 / 8 differ [SIM] |
| Q2-4 FC / lead rule | CLOSED WITH RESIDUAL | Option (A) ruled; b2, the A1 HAL, GNC handling of reason 19 and the founders' confirmation are OPEN (section 16) |
| UT-1 to UT-4 | CLOSED | All PASS in test_core v2.13 [SIM]; UT-5 and UT-6 also PASS |
| S13F TC-fault set | CLOSED | Covers my R4 NOT RUN list; 2576 / 2576 SEAT_STEP (N01) |
| S13T no-fault outcomes | CLOSED WITH RESIDUAL | One outcome changed, in the fail-safe direction; it cannot be attributed to a single part of the delta |
| FMEA row | CLOSED WITH RESIDUAL | E5-01 |
| B-TC-1 TC4 row | CLOSED WITH RESIDUAL | E5-02, E5-04, E4-N10 |
| E4-01 | CLOSED for the light-window hazard | Hold plus the step check in every state; residual E5-01 outside the window |
| E4-02 | CLOSED | r3_01_c1_drift.e4_02_rule equals my Q3 table (eps_max 11.2 / 8.1 / 6.0 / 3.4 / 1.8 / 0.8 % at k = 1 / 1.25 / 1.5 / 2 / 2.5 / 3) [DERIVED] |
| E4-03 | CLOSED | — |
| E4-04 | CLOSED | A8_U330 now includes the stand relight rows (k 1, T0 24 C, band 29.59-35.59 bar abs) |
| E4-05 | CLOSED WITH RESIDUAL | E5-07 |
| E4-06 | CLOSED | — |
| E4-N01 (ARM deviation comment) | CLOSED | — |
| E4-N02 (pad rule and JFWD inhibit) | CLOSED in code; A1 HAL OPEN | OI-A1-BUILD-SEAT-RULE |
| E4-N03 (JFWD_LS threshold) | CLOSED | — |
| E4-N04 (P_torch re-base) | OPEN | 264 (4) |
| E4-N05 (purge mass text) | CLOSED | — |
| E4-N06 (re-zero2 margin) | Noted | — |
| E4-N07 (static linear coefficient) | Noted | — |
| E4-N08 (U577 backstop) | OPEN | Combustion and lead |
| E4-N09 (TB-state) | Noted | — |
| E4-N10 (grounded junction) | OPEN | TO-VERIFY; author NOT DONE |
| E4-N11 (SIL MANIFEST_v2) | NOT DONE | OI-SIL-MANIFEST-V2 |

## 5. (b) Reproduction

**Method.** I assembled the tree as v2.11 + the v2.12 overlay + the v2.13 overlay (data/assembly_note.txt). I built and ran in /dev/shm/rev_elec5 at nice 15 with make -j1.

**Binaries: all IDENTICAL to staged** [SIM]

| Binary | sha256/16 |
|---|---|
| sil | 58675c5a8dad9d18 |
| sil_bpc1 | 992f3dd22e25e1cb |
| test_core | 3b62a7d1f2306f89 |
| test_core_nohooks | 4ad12911b063c03d |

**Outputs: all IDENTICAL to staged** [SIM]

| Run | sha256/16 |
|---|---|
| A5 false | 0ddace7afedfc751 |
| A5 true | c23d50fea0044ad6 |
| S13F false | 504ae39fb9b76803 |
| S13F true | 4d7fcdff06eeac50 |
| S13T _false_ts | da70006c69bf0e96 |
| S13T as is | dfc8c42e1b9ffebf |
| S13T _true_ts | 321b4b53827b11fb |
| S12 | b007ed77a2cd51a3 |

- The n2o files are identical too (data/rerun_hashes.txt). The run logs are identical apart from the staged trailing "exit 0".
- Tests: 343 passed / 0 failed; no-hooks build 342 / 0.
- S12: 38 cases, 34 PASS and 4 FAIL. The 4 failures are the v2.12 dispositioned set [SIM].

## 6. (c) The E4-01 code fix: can a TC4 error reach E2, P0, the relight base or the FC release predicate?

**Inside the window: no path.** Evidence from code reading of the hold condition and from probe H [SIM]:
- 2016 in-window error runs per build: 0 compensation movement, 0 P0 deviation, 0 E2-tick deviation.
- 0 unlit E2 and 0 unlit b7, both builds.
- 2312 runs latched SEAT_STEP; 24 were refused before IGNITION.

Why each output is protected:
- The relight base and the light rule are latched before E2.
- The FC release predicate needs a false E2 (N14).

**Before the window, an error that passes the checks is followed like a real drift** (448 before-entry runs per build) [SIM]:
- P0 moved in 328 runs, by at most 0.347 bar.
- On a real light the E2 tick moved in 1 run (default build) and 22 runs (bpc1).
- No run gave an unlit E2.
- This is the E5-01 class.

**Hold-disabled control** (types 0 and 1 only; the relight controls are excluded because their comp is constant): the compensation moved in 256 runs, P0 in 240, with 0 false E2 [SIM].

## 7. (d) ITEM 2: should the catch-up bound be tied to the physical maximum?

**Recommendation: do not tie it. Keep 5 K/s.** It is already one constant shared with the slew.

**Why not**
- Tying it gives 2.42 K/s × 1.148 s = 2.78 K, which is below the 3 K rate trip [CALC]. The exemption range (3 K, bound] would then be empty, so the catch-up becomes dead code.
- Every hold-end gap above the physical rate × hold would trip. That leaves only a 1.35× margin at the stand [CALC], on a physical maximum that is itself [DERIVED on SIM].

**The cost of keeping 5 K/s is bounded** [CALC]
- Widest g0 = 5 K/s × 1.148 s = 5.74 K, i.e. 0.427 bar at k 3.
- It decays, and the cap is 2 × hold = 2.296 s.
- It lands in RUN after the base is latched.

**Margins** [CALC]
- Physical hold-end gaps are ≤ 1.59 K (A1) and ≤ 2.06 K (stand), i.e. 0.12 / 0.15 bar [DERIVED, v4.2].
- Against the 3 K trip: 1.89× (A1) and 1.45-1.48× (stand).
- Against the bound: 3.62× (A1) and 2.06-2.10× (stand).

**UT-6 [SIM, PASS]**

| Case | Result |
|---|---|
| under | D 0.812 s, g0 3.979 K against a bound of 4.060 |
| over | g0 4.141 K, trips at the hold end |
| growth | trip 0.752 s after the end, gap 5.479 K |
| cap | trip 1.625 s after the end (2 × D = 1.624 s) |
| 2 K step | trip 0.100 s after the end |
| resume | trips at a 3.000 K gap |

The ratchet is not tested on its own (N02).

## 8. (e) A5 and the 18:43Z ruling

### (e)(i) The residual

**Pre-command trip.** With option (A) a SEAT_STEP latched before the PURGE / RELIGHT command refuses the relight (code 19). The decision point is the later of the two commands, normally RELIGHT.

**Trip after the command.** Option (A) does not stop this. T_c stays frozen to the next ARM, so the error is coef × (seat rise since the trip). It grows through the relight RUN.

Size for a trip at the command:
- **A1:** ≥ 0.037 bar at k 3 (0.012 at k 1) over the 4.59 s relight. That is a lower bound: the NF2b history has no relight-burn heating [DERIVED on SIM]. About 1 K, 0.07 bar at k 3, is likely [ESTIMATE]. The relight-burn seat history is MISSING.
- **Stand after B1** (the inhibit does not act on the stand; same lower-bound caveat) [DERIVED on SIM, GVHI / GVLO]:
  - 1.07-1.26 K in the first second, i.e. 0.080-0.094 bar/s at k 3;
  - 4.4-5.4 K over 4.59 s, i.e. 0.33-0.40 bar at k 3 (0.11-0.13 at k 1);
  - 8.4-10.5 K over 10 s, i.e. 0.62-0.78 bar at k 3.

Effects at the A1 size (about 0.07 bar):
- PC_BAND does not see a steady offset (closed loop).
- s = +1, landing floor: true Pc at the ECU minimum setpoint is 4.151 − 0.074 = 4.077 bar abs, which is 6.7 % below the 4.370 bar abs floor. That adds 1.7 % to the existing 5 % allowance [CALC].
- s = −1: true Pc 25.07 bar abs at the cap and 30.07 at the abort, against MEOP 45.
- FLAMEOUT (ratio 0.4) and A7 are not materially moved: A7 s+1 flags only when the abs setpoint is below 0.30 bar [CALC].

Stand effects (s = −1, at the end of a 4.59 s burn): +0.4 bar on the true Pc, against the cap, the 30 bar abort and MEOP 45. Tolerable [CALC].

**Recommendation:** the residual is acceptable. Record it (V4, V8 / B2), and have the Mechanical relight-burn seat history replace the lower bound.

### (e)(ii) The author's two code claims

**Claim 1: CONFIRMED** [SIM probe A]. TORCH_FAULT at +1.0 bar and above: the torch confirmation counts only while the main Pc gauge is below kTorchGateMaxPcG_Pa (1 bar).
- At +1.01, +1.05 and +1.20 bar: TORCH_FAULT, no E1, pintle 0.000 mm.
- +0.35 to +0.99 bar runs with P0 = e (BASE_HIGH from +0.80 bar, default build; from +0.70 bar, bpc1).

**Claim 2: CONFIRMED WITH A CONDITION** (E5-03). PC_SENSOR after BASE_AMB holds only if the light comes at E1 + 50 ms or later.

**Landing-floor effect (s = +1)**, not stated in the staged residual [CALC]. True Pc at sp_min 4.151 bar abs:

| e (bar) | True Pc (bar abs) | vs floor |
|---|---|---|
| 0.30 | 3.851 | −11.9 % |
| 0.71 | 3.441 | −21.2 % |
| 0.99 | 3.161 | −27.7 % |
| 1.02 | 3.131 | −28.3 % |

**s = −1:** 25.3-25.76 bar abs at the cap and 30.3-30.76 at the abort, for |e| ≤ 0.76 bar.

**False FLAMEOUT after BASE_AMB** needs a gauge setpoint below |e| / 1.5 [CALC]:

| \|e\| (bar) | Setpoint below (bar) |
|---|---|
| 0.77 | 0.513 |
| 1.02 | 0.68 |
| 2.0 | 1.333 |
| 3.8 | 2.533 |

### (e)(iii) Recommendation

- **A1 flight image: INHIBIT** (this is option (A)).
- **Stand: PROCEED** (the core default). On the stand the relight is refused NOT_VENTED (8) before SEAT_STEP is checked in every A5 cell [SIM].
- The cost of option (A) is one vehicle per pre-command trip, through the lost-relight outcome. That is why the B-TC-1 EMI criterion matters (E5-04).

### Judgment of the 18:43Z ruling: AGREE

Option (A) puts the decision where the FC can see it: refusal code 19 in TLM_RELIGHT d6 before the command. That is what the 17:50Z rule intended. It needs no code change, and the stand is unaffected (!stand_).

**Deferring b2 to the A1 HAL build round is ACCEPTABLE. I would not require it in v2.13 before the lift.**
- The lift concerns option (b) starts on the stand and at the pad. The inhibit acts only on flight relights (!stand_ && starts_ >= 1, l.581), so b2 changes nothing at any start the lift enables.
- No A1 image can exist before the HAL round. b2 reports a value the HAL sets, so the bit and the setting are best verified together.
- The pad row fails safe. It requires b2 = 1; until the bit exists it reads 0, so the pad is NO-GO. Omitting it cannot produce a GO.
- Adding b2 now would reopen a reviewed core build without changing any permitted start.

**Conditions on the deferral**
1. b2 is a core change (buildBits() and protocol.h), not HAL-only. It comes with a unit test for both values and is reviewed as a delta.
2. b3 = jfwd_relight_inhibit goes in the same change (N08).
3. Add the B-ECU-1 A1-image functional row (B3).
4. GNC confirms the FC takes the lost-relight outcome on TLM_RELIGHT d6 & 0x3F = 19, as for 17.
5. The pad "Build bits" row is corrected now through line 270 (B1 / V7). Otherwise a crew reading l.433 as it stands would check only b0 and b1.

## 9. (f) RULING 1 (a)-(e), SEAT_TC 32 and the counter

**RULING 1: CLOSED in code; the A1 HAL setting is OPEN** (OI-A1-BUILD-SEAT-RULE). Implemented as ruled:
- the seat_arm_rule member (core default FALSE; the A1 HAL sets TRUE);
- ARM refusal Abort::SEAT_TC (32), carried in the log byte abort_cause;
- the first start refused with refuse::SEAT_TC (18);
- EVENT BUILD 0x25 (b0, b1), emitted at boot and at every ARM attempt (the 3 HAL copies are a specification only);
- ovr_flags b7;
- the FMEA-A1-SEAT-RULE-BUILD row.

**SEAT_TC 32 test: PASS** [SIM].

**Counter.** The STATE-event cause field is 5 bits (kStateCauseMax 0x1F). The guard saturates a larger cause and counts it in g_state_cause_overflow (RAM only).
- Code 32 is ARM-refusal only: the ECU stays in SAFE and no STATE event carries it. The guard is therefore unreachable by construction.
- No readable counter is needed. Add the tripwire (N10).

## 10. (g) ITEM 3: TC4 conversion period

- The tCONV values agree with the datasheet [AS RECALLED; TYP / MAX columns TO-VERIFY on the PDF, DATASHEET 19-7534 Rev 0].
- The static_assert on the period is correct.
- The first conversion takes up to 225 ms, giving 0.54 K at 2.42 K/s. That is a 2.8× margin under 1.5 K [CALC].
- The step-limit margin is 5.63× at 0.110 s and 4.77× at 0.130 s [CALC].

## 11. (h) v4.2 for promotion, and the status texts that change on a lift

**Promote v4.2 byte for byte** (de02c29f9add1979). Line 270 governs it where they differ. The corrections are V1 to V12.

**The status texts that change on a lift are V13:**
- /status;
- /pad_go_no_go_a1/rule and items[7];
- /open_issues[29], [32] and [34];
- /r3_01_c1_drift/status and stand_relight_after_B1/status_v2p13;
- /rev_elec_3_author_status/R3-01;
- /changelog_folding_v2p13[4], [7] and [8].

/change_summary_v4p1_to_v4p2[16] stays as history.

## 12. (i) Bench plan and BOM rows

**Bench plan v5.1**
- **Consistent with v2.13:** l.168 (B-PC-1 seat-TC row) and l.427 (refused-ARM causes, SEAT_TC 32).
- **To correct:**
  - l.223 (E5-02, E5-04);
  - l.224 (N03, N04);
  - l.139-140 (E5-06);
  - l.432-434 (the ruling);
  - l.9-10, l.14 and l.420 (lift status);
  - l.95-96 (B9).

**BOM v2.5:** ACCEPT (section 1); N12.

## 13. (j) SIL disclosures

**The seat_ts variant** is guarded by ECU_SIL_TEST_HOOKS (default 1.0).
- Its window runs from the first plant light (seat_burn0) to shutdown (sim.cpp l.221, l.288-291, l.424). Relights run unscaled.
- At first starts E2 falls inside the window, so sil_ts_e2_ = ts (l.745). The post-E2 hold becomes 0.45 s / ts: 18 ms on the stand and 110 ms for A1 [code reading].
- The step check is not scaled. The plant TC lag is scaled too, which is why the one S13T outcome change cannot be attributed to a single part of the delta.
- It hides no step fault. It could mask ramp faults inside the compressed burn, but S13F contains none.

**Other disclosures**
- The discarded run is explained.
- The n2o identity across builds is expected (N06).

## 14. (k) The author's NOT DONE items

- **Part C, E4-N11 SIL MANIFEST_v2** (OI-SIL-MANIFEST-V2): needed before A1 flight acceptance. Not needed for the lift.
- **E4-N10** (grounded-junction common mode and open-TC detection): needed before the first hardware start with option (b) (condition C2 in section 16).
- **The B-PC-1-shown as-is S13T run** was skipped; I did not run it either. It is not needed for the lift. It is recommended for the next round.

## 15. Line-270 texts (verbatim; each names the field it replaces)

### v4.2

**V1. /limits_v2p11[33]**
- limit: 'SEAT_STEP relight inhibit (A5; LEAD 18:43Z option (A))'
- value.v: 'A1 FLIGHT image TRUE (EngineEcu::seat_step_relight_inhibit set by the A1 HAL; OI-A1-BUILD-SEAT-RULE; reported in EVENT BUILD 0x25 b2 from the A1 HAL build round); core default cfg::kSeatStepRelightInhibit FALSE for the stand and SIL builds (no effect on the stand: !stand_)'
- value.tag: 'DESIGN (LEAD 18:43Z ruling on REV-ELEC-5 E5-05)'
- value.src: 'config.h kSeatStepRelightInhibit; engine_ecu.h l.75; engine_ecu.cpp startBlock l.581'
- basis: 'v2.13 (REV-ELEC-4 E4-05 (3), Q2; REV-ELEC-5 E5-05; LEAD 18:43Z)'

**V2. /v2p13_delta/A5_recommendation/recommendation**
'RULED, LEAD 18:43Z option (A) (replaces points 1-2 of the 17:50Z A5 ruling for the A1 flight): INHIBIT in the A1 FLIGHT image (seat_step_relight_inhibit TRUE): a SEAT_STEP latched before the PURGE / RELIGHT command makes the ECU refuse it refuse::SEAT_STEP (19), published in TLM_RELIGHT d6 before the command, and the vehicle takes the lost-relight outcome of gnc.json v3.2 (264 (3)); a trip after the command does not stop the relight and the ECU never self-aborts on SEAT_STEP. The core default stays FALSE (proceed on the held compensation) for the stand and SIL builds; the stand relight is refused NOT_VENTED (8) before SEAT_STEP in every A5 cell [SIM]. The author's PROCEED recommendation and the 17:50Z reason "the flag left false keeps the decision with the FC" are withdrawn: no CAN frame carries f3 (REV-ELEC-5 E5-05). Option (B), a CAN signal for SEAT_STEP, may be asked for in v2.14 under OI-SEAT-STEP-RELIGHT (lead + GNC)'

**V3. /v2p13_delta/A5_seat_step_option**
'EngineEcu::seat_step_relight_inhibit (core default cfg::kSeatStepRelightInhibit FALSE = proceed on the held compensation, stand and SIL builds; TRUE = refuse::SEAT_STEP (19) at PURGE / RELIGHT when SEAT_STEP is latched, flight only: !stand_, starts >= 1). LEAD 18:43Z option (A): the A1 FLIGHT image sets TRUE (A1 HAL; OI-A1-BUILD-SEAT-RULE; EVENT BUILD b2)'

**V4. /v2p13_delta/A5_recommendation/residual**
'A1 flight image (inhibit TRUE, LEAD 18:43Z): a SEAT_STEP latched before the PURGE / RELIGHT command refuses the relight (19), so no pre-command stale offset reaches a relight. A trip after the command, or any trip with the core default FALSE (stand, SIL), keeps T_c frozen to the next ARM: a stale offset coef x (seat rise since the trip) rides into the relight RUN and grows with the seat rise; it is not the decaying ITEM 2 error. Size for a trip at the command: A1 >= 0.037 bar at k = 3 over the 4.59 s relight [DERIVED on SIM; lower bound, the NF2b seat history has no relight-burn heating], about 0.07 bar [ESTIMATE]; stand after B1 >= 0.33-0.40 bar at k = 3 over 4.59 s [DERIVED on SIM, same caveat]. Start gates (default build; B-PC-1-shown build in brackets) [SIM REV-ELEC-5 probe A]: +1.0 bar and above aborts TORCH_FAULT at the torch gate (kTorchGateMaxPcG_Pa) before the lift; from +0.80 (+0.70) bar BASE_HIGH is set and the start runs on P0 = e; below -kIgnBaseCheck_Pa = -0.76 (-0.46) bar BASE_AMB sets P0 = 0 and the A7 low edge aborts PC_SENSOR when the plant light comes at E1 + 50 ms or later, but with a light by about E1 + 30 ms E2 follows on the real light and the offset rides into RUN (-0.77 / -1.00 bar ran; -2.00 bar gave NO_IGNITION). In RUN the compensated Pc feeds the throttle loop and the monitors: s = +1 (reads high) lowers the true Pc by e (at the ECU minimum setpoint 4.151 bar abs: 3.85 / 3.44 / 3.16 bar abs for e = 0.30 / 0.71 / 0.99 bar, 11.9 / 21.2 / 27.7 % below the 4.370 bar abs landing floor [CALC]) and delays FLAMEOUT; s = -1 (reads low) raises the true Pc by |e| (25.3-25.8 bar abs at the 25 bar cap and 30.3-30.8 bar abs at the 30 bar firmware abort for |e| <= 0.76 bar; <= 27 / 32 bar abs for a BASE_AMB ride-in with |e| < 2.0 bar; MEOP 45 bar [CALC]) and brings FLAMEOUT earlier; PC_BAND does not see a steady offset (closed loop). Backstops: U330 on the raw path, A7 map (flight flag), range / 150 K. SIL plant on ASSUMED / Combustion bands: firmware-sequencing evidence only'

**V5. /open_issues[37] (OI-SEAT-STEP-RELIGHT)**
- owner: 'lead + GNC'
- issue: 'A5: SEAT_STEP latched before a relight. RULED LEAD 18:43Z option (A): the A1 FLIGHT image refuses PURGE / RELIGHT refuse::SEAT_STEP (19). OPEN: option (B) (a CAN signal for SEAT_STEP, v2.14) if GNC wants a finer FC rule; the residual of a trip after the relight command (REV-ELEC-5 (e)(i)); founders confirm with OI-JFWD-FLIGHT at flight acceptance'
- closure: 'GNC statement (option (B) wanted or not) + founders confirmation at flight acceptance with OI-JFWD-FLIGHT'
- severity: unchanged (MEDIUM)

**V6. The A1 build requirement rows**

/open_issues[35] (OI-A1-BUILD-SEAT-RULE):
- issue: 'A1 flight build requirements: seat_arm_rule TRUE and seat_step_relight_inhibit TRUE (LEAD 16:11Z RULING 1, 18:43Z option (A)), next to kHbleedFitted; EVENT 0x25 BUILD gains b2 = seat_step_relight_inhibit (an additive core change to buildBits() / protocol.h with a unit test for both values, delta-reviewed) in the A1 HAL build round; the A1 HAL is not in this tree'
- owner: 'Electronics'
- closure: 'A1 HAL image built; the b2 core change and its test reviewed; pad row "build bits" reads b0 = 1, b1 = the A1 build value and b2 = 1; B-ECU-1 A1-image row PASSED'

/v2p13_delta/pad_rule_264_2:
- build_requirement: 'A1 flight build: seat_arm_rule TRUE and seat_step_relight_inhibit TRUE (LEAD 18:43Z) - OPEN build items, owner Electronics (the A1 HAL is not in this tree; EVENT BUILD b2 comes in the A1 HAL build round): OI-A1-BUILD-SEAT-RULE'
- reporting: 'EVENT BUILD 0x25 b0 (seat_arm_rule) and, from the A1 HAL build round, b2 (seat_step_relight_inhibit) + log ovr_flags b7 (can_interface.v2p13_additions)'

/fmea_rows_a1[6]:
- mode: 'A1 image built with seat_arm_rule FALSE or seat_step_relight_inhibit FALSE (the core defaults; the A1 HAL must set both TRUE)'
- effect: append '; with the inhibit FALSE a SEAT_STEP latched before the relight is not refused and nothing on CAN tells the FC (REV-ELEC-5 E5-05): the relight runs on the stale compensation (A5 residual)'
- detection: 'EVENT BUILD 0x25 b0 and b2 (b2 from the A1 HAL build round) after power-up and at the ARM attempt, log ovr_flags b7; the pad row "build bits" (NO-GO on b0 = 0 or b2 = 0)'
- mitigation: 'build requirement "A1 flight build: seat_arm_rule TRUE, seat_step_relight_inhibit TRUE" next to kHbleedFitted (OI-A1-BUILD-SEAT-RULE, owner Electronics; the A1 HAL is not in this tree)'
- source: append '; LEAD 18:43Z'

**V7. Build bits**

/pad_go_no_go_a1/items[8]:
- item: 'build bits (RULING 1 (c), LEAD 16:27Z option (2), 18:43Z (3))'
- go: 'EVENT BUILD 0x25 read after power-up AND at the ARM attempt: arg b0 seat_arm_rule = 1, b1 hbleed_fitted = the A1 build value (1 unless CF-4 clears the bleed: kHbleedFitted, LEAD 2026-10-13) and b2 seat_step_relight_inhibit = 1 (LEAD 18:43Z; b2 is added in the A1 HAL build round and reads 0 until then: NO-GO); log v13 ovr_flags b7 = 1. Any other value: NO-GO (an A1 image built with seat_arm_rule FALSE allows a flight ARM without the coefficient; one built with seat_step_relight_inhibit FALSE relights on a stale compensation after a SEAT_STEP: FMEA-A1-SEAT-RULE-BUILD)'
- source: append '; LEAD 18:43Z (3)'

/can_interface/v2p13_additions/EVENT_BUILD/v/arg: 'b0 seat_arm_rule, b1 hbleed_fitted, b2 seat_step_relight_inhibit (LEAD 18:43Z; added in the A1 HAL build round; 0 in v2.13), b3-b15 0'

**V8. A1 pad SEAT_STEP rows**

New /pad_go_no_go_a1/items[10]:
- item: 'SEAT_STEP relight inhibit (LEAD 18:43Z option (A))'
- go: 'the A1 image carries seat_step_relight_inhibit TRUE (build constant, no ground input; items[8] b2 = 1). In flight a SEAT_STEP latched before the PURGE / RELIGHT command makes the ECU refuse it refuse::SEAT_STEP (TLM_RELIGHT d6 & 0x3F = 19) and the FC takes the lost-relight outcome of gnc.json v3.2; a trip after the command does not stop the relight (compensation held; REV-ELEC-5 (e)(i))'
- source: 'LEAD 18:43Z; ECU v2.13 startBlock l.581 (test_v213 "264 (7) / A5 option"); GNC: FC handling of d6 = 19; founders confirm at flight acceptance with OI-JFWD-FLIGHT'

/pad_go_no_go_a1/items[7]:
- go: replace 'NO-GO until the v2.13 delta is reviewed (266 (6))' with 'After ARM: log v13 f3 SEAT_COMP set, SEAT_NOREF and SEAT_STEP (b7) clear, read from the log (no CAN frame carries f3). A SEAT_STEP that latches after ARM refuses the first start refuse::SEAT_TC (18): NO-GO (the latch clears only at the next ARM). In flight see items[10]. 266 (6) lifted by CHANGELOG 270; the A1 items of 270 apply'
- source: append '; CHANGELOG 270; LEAD 18:43Z'

**V9. /log_v13/v**
Replace 'b6 PT_RZ_REJ, b7 zero)' with 'b6 PT_RZ_REJ, b7 SEAT_STEP (v2.13))'.

**V10. /sensors/thermocouples/tc4_hal_contract_v2p13/step_limit_margin/v**
Replace '; a longer configured period needs kPcSeatStepMax_K re-derived (6 x 2.42 K/s x period)' with '; rule: kPcSeatStepMax_K >= 4 x 2.42 K/s x period, so 1.5 K holds up to a 0.155 s period [CALC]; a longer configured period needs kPcSeatStepMax_K re-derived'.

**V11. /fmea_rows_a1[5]/residual**
'an uncompensated seat drift after a hold or a trip: fail-safe refusals of the v2.11 type (A5 evidence; A1 image refuse 19, LEAD 18:43Z); outside the light-window hold an error that passes the step check (<= 1.5 K per conversion) and the rate check (a ramp <= 5 K/s, or a step <= 3 K split over conversions) is followed by the compensation up to kPcSeatDevMax_K: coef x 150 K = 3.7 bar at k = 1, 11.2 bar at k = 3 [CALC] in RUN and coast (REV-ELEC-5 probe D at k = 3: 2.0 K/s for 20 s = 40 K = 2.98 bar and 4.9 K/s = 98 K = 7.29 bar with no flag; probe S: 2 x 1.45 K = 0.216 bar with no flag [SIM]); s = -1 raises the true Pc up to 36.2 bar abs at the 25 bar cap and 41.2 bar abs at the 30 bar firmware abort (MEOP 45 bar) [CALC]; inside the light-window hold no TC4 reading moves Pc [SIM probe H, UT-1]; backstops U330 on the raw path, A7 map (flight flag), range / 150 K; v2.14 candidate OI-TC4-DRIFT-BOUND (bound the T_c travel since ARM)'

Add /open_issues entry:
- id 'OI-TC4-DRIFT-BOUND', severity 'MEDIUM', owner 'Electronics'
- issue: 'a TC4 drift below the step and rate limits is followed up to 150 K (3.7 / 11.2 bar at k = 1 / 3) [CALC; REV-ELEC-5 E5-01]'
- closure: 'v2.14 T_c travel bound or a reasoned NO with the lead'

**V12. UT-2 description** (v2p13_delta.tests and test_v213, next round): 'a step presented to the core within one conversion'.

**V13. Status texts on the lift**
- /status: replace 'CARVE-OUT IN FORCE (CHANGELOG 266 (6), verbatim there): option (b) (seat coefficient loaded) is not used for any start with ignition until the v2.13 delta (light-window hold, TC4 step / rate checks, catch-up) is reviewed; A1 FLIGHT is NO-GO until then.' with 'CARVE-OUT 266 (6) LIFTED by CHANGELOG 270 (REV-ELEC-5 ACCEPT WITH COMMENTS): option (b) is used for starts with ignition under the 270 conditions; A1 FLIGHT stays NO-GO on the 270 A1 items; line 270 governs this file where they differ.'
- /pad_go_no_go_a1/rule: replace 'UNDER THE 266 (6) CARVE-OUT THE A1 PAD IS NO-GO until the v2.13 delta is reviewed (REV-ELEC-5)' with '266 (6) LIFTED (CHANGELOG 270); THE A1 PAD STAYS NO-GO until the 270 A1 items close'.
- /open_issues[34] (OI-REV-ELEC-5): add status 'CLOSED: REV-ELEC-5 ACCEPT WITH COMMENTS; 266 (6) lifted by CHANGELOG 270'.
- /open_issues[29]/status_v2p13: replace 'remaining: REV-ELEC-5 on the v2.13 delta (266 (6) carve-out), the per-serial' with 'REV-ELEC-5 ACCEPT WITH COMMENTS and 266 (6) lifted (270); remaining: the per-serial'.
- /open_issues[32]/status_v2p13: replace 'and T4 waits for the lift of 266 (6) (E4-06 (2))' with '266 (6) is lifted (270); T4 waits for the Combustion T4 re-run'.
- /r3_01_c1_drift/status: replace 'the 266 (6) carve-out holds until the v2.13 delta is reviewed (REV-ELEC-5)' with '266 (6) lifted by CHANGELOG 270 after REV-ELEC-5'.
- /r3_01_c1_drift/stand_relight_after_B1/status_v2p13: 'RE-INSTATED by CHANGELOG 270 (266 (6) lifted): planned with the E4-02 k-dependent eps rule (beyond it REFUSED NOT_VENTED, fail-safe); evidence on v2.13: v2p13_delta.sil; REV-ELEC-5'.
- /rev_elec_3_author_status/R3-01: replace '266 (6) carve-out until REV-ELEC-5' with '266 (6) lifted by 270 (REV-ELEC-5)'.
- /changelog_folding_v2p13[4]/status: replace 'waits for the lift of 266 (6)' with '266 (6) lifted (270); waits for the Combustion T4 re-run'.
- /changelog_folding_v2p13[7]/status: replace 'REV-ELEC-5 next' with 'REV-ELEC-5 ACCEPT WITH COMMENTS (270)'.
- /changelog_folding_v2p13[8]/status: 'LIFTED by CHANGELOG 270 (REV-ELEC-5); A1 flight NO-GO items in 270'.

### Bench plan v5.1

**B1. l.433 (Build bits), whole row**
'| Build bits (LEAD 16:11Z RULING 1 (c), 16:27Z option (2), 18:43Z (3)) | EVENT BUILD 0x25 read after power-up AND at the ARM attempt: arg b0 seat_arm_rule = 1, b1 hbleed_fitted = the A1 build value (1 unless CF-4 clears the bleed: kHbleedFitted, LEAD 2026-10-13) and b2 seat_step_relight_inhibit = 1 (LEAD 18:43Z; b2 is added in the A1 HAL build round: until it exists it reads 0 and the row is NO-GO); log v13 ovr_flags b7 = 1. Any other value: NO-GO (FMEA-A1-SEAT-RULE-BUILD) | LEAD RULING 1, 18:43Z; ECU v2.13 (Outputs::build_event / build_bits) + the A1 HAL build round (b2); Electronics |'

**B2. New row after l.434**
'| SEAT_STEP relight inhibit (LEAD 18:43Z option (A)) | the A1 image carries seat_step_relight_inhibit TRUE (Build bits row: b2 = 1); in flight a SEAT_STEP latched before the PURGE / RELIGHT command makes the ECU refuse it SEAT_STEP (TLM_RELIGHT d6 & 0x3F = 19) and the FC takes the lost-relight outcome of gnc.json v3.2; a trip after the command does not stop the relight (the compensation stays held; REV-ELEC-5 (e)(i)) | LEAD 18:43Z; ECU v2.13 startBlock; GNC (FC handling of d6 = 19, OI-GNC-EVENT-BUILD); founders confirm at flight acceptance with OI-JFWD-FLIGHT |'

**B3. New B-ECU-1 row after l.140**
'| A1 flight image build constants (LEAD RULING 1, 264 (7), 18:43Z) | on the A1 HAL image: EVENT BUILD 0x25 b0 = 1, b1 = the A1 build value, b2 = 1; ARM refused SEAT_TC (abort_cause 32) with the coefficient 0 and with TC4 open; with SEAT_STEP forced in COAST (TC simulator step >= 10 K) TLM_RELIGHT d6 & 0x3F = 19 and PURGE / RELIGHT refused; with JFWD_LS forced on the first light d6 & 0x3F = 17. Any deviation: A1 NO-GO |'

**B4. l.432 (Seat compensation), whole row**
'| Seat compensation (264 (2); v2.13; LEAD 18:43Z) | the B-PC-1 coefficient is loaded (non-zero) and TC4 is valid and in range at ARM (the A1 flight image refuses ARM SEAT_TC (32) otherwise; read abort_cause from the log); after ARM: log v13 f3 SEAT_COMP set, SEAT_NOREF and SEAT_STEP (b7) clear, read from the log (no CAN frame carries f3). A SEAT_STEP that latches after ARM refuses the first start SEAT_TC (18): NO-GO (the latch clears only at the next ARM). In flight: see the SEAT_STEP relight inhibit row. The fallback (coefficient 0) is NOT a flight configuration (264 (2)). 266 (6) lifted by line 270; the A1 items of 270 apply | LEAD 264 (2), 266 (6), 270, 18:43Z; ECU v2.13 armChecksOk / startBlock; Electronics (B-PC-1 record) |'

**B5. l.223**
Replace 'Pass: mean shift ≤ 0.3 K; per-conversion peak deviation ≤ 1.0 K (below the 1.5 K step threshold: no nuisance SEAT_STEP); no MAX31856 fault bit (OVUV / open); with the TC simulator, one-conversion steps of ±2, ±10, ±55 and +140 K: inside [IGNITION entry, E2 + 0.45 s] they change neither P0, nor the rise, nor the E2 tick; inside or outside that window they set SEAT_STEP and the compensation holds.' with:

'Pass: mean shift ≤ 0.3 K; peak change between consecutive conversions ≤ 1.0 K (the step check acts on that change, 1.5 K threshold; the physical seat change is ≤ 0.31 K per 0.130 s conversion) and peak deviation from the all-off mean ≤ 0.5 K (the hold-end gap: stand physical gap up to 2.06 K against the 3 K rate trip); 0 SEAT_STEP in all repeats with the A1 sequence powered (spark, torch valves, servos, pintle rail, bleed / purge valves); no MAX31856 fault bit (OVUV / open); with the TC simulator: steps of ±10, ±55 and +140 K must set SEAT_STEP, and inside [IGNITION entry, E2 + 0.45 s] they change neither P0, nor the rise, nor the E2 tick; a ±2 K step sets SEAT_STEP when it falls within one conversion and may be followed (≤ 0.22 bar at k = 3) when the simulator edge spans two conversions: record which (both PASS); after SEAT_STEP the compensation holds.'

**B6. l.224**
- Replace '(6 × 2.42 K/s × period)' with '(kPcSeatStepMax_K ≥ 4 × 2.42 K/s × period: 1.5 K holds up to 0.155 s)'.
- After 'over ≥ 300 conversions' insert ', with the open-circuit fault detection (CR0 OCFAULT) setting of the flight image (E4-N10)'.

**B7. l.139-140**

l.139, whole row: '| CAN frames against `protocol.h` v2.13 (TLM_FAST d4-d5 encoder lift, TLM_RELIGHT d6 b7 PC_VALID and d6 & 0x3F refusal reasons incl. JFWD_USED 17, SEAT_TC 18, SEAT_STEP 19, EVENT 0x120 incl. R2_BACKSTOP 0x24 and BUILD 0x25) | decoder round trip, 0 CRC errors over 10 min |'

l.140: replace 'b6 PT_RZ_REJ decode as set by the injected conditions' with 'b6 PT_RZ_REJ, b7 SEAT_STEP decode as set by the injected conditions; ovr_flags b7 = seat_arm_rule of the build; abort_cause SEAT_TC (32) on a refused ARM'.

**B8. Lift status texts**
- l.9-10: replace 'CARVE-OUT (266 (6)): option (b) (coefficient loaded) is not used for any start with ignition until the v2.13 delta is reviewed; the coefficient may be loaded for B-PC-1 / B-TC-1 bench work without ignition. A1 flight and the stand relight wait for it.' with 'CARVE-OUT 266 (6) LIFTED by line 270 (REV-ELEC-5): option (b) is used for starts with ignition under the 270 conditions; A1 flight stays NO-GO on the 270 A1 items.'
- l.14: replace 'it is a stand relight and waits for the lift of 266 (6).' with 'it is a stand relight; 266 (6) is lifted (270); it waits for the Combustion T4 re-run.'
- l.420: replace 'UNDER THE 266 (6) CARVE-OUT THE A1 PAD IS NO-GO until the v2.13 delta is reviewed (REV-ELEC-5).' with '266 (6) LIFTED (line 270); THE A1 PAD STAYS NO-GO until the 270 A1 items close.'

**B9. l.95-96** ("First static fire needs, in addition, …"): append 'With option (b) (coefficient loaded): also the B-TC-1 TC4 rows on that unit (spark row as corrected by 270; conversion period ≤ 0.130 s) and the E4-N10 grounded-junction check.'

### Firmware comments (next Electronics round; no rebuild now)

**F1. config.h l.920:** replace '(log v13 f3_flags b7, TLM)' with '(log v13 f3_flags b7 only: no CAN frame carries f3; with seat_step_relight_inhibit TRUE a latched SEAT_STEP is published as TLM_RELIGHT d6 & 0x3F = 19 in COAST / PURGE)'.

**F2. config.h l.906:** replace '(A1 and stand) - inside the kIgnBaseDrift basis.' with '(A1 and stand) - the S13T-time values are inside the kIgnBaseDrift 0.06 bar basis; the 0.072 bar envelope exceeds it by 0.012 bar, which comes off the unlit-rise margin (still >= 0.22 bar) [DERIVED, REV-ELEC-5 N07].'

## 16. (l) Carve-out answer: LIFT IN FULL, with conditions; A1 flight stays NO-GO

**Exact text for line 270:**

'266 (6) CARVE-OUT LIFTED (REV-ELEC-5 ACCEPT WITH COMMENTS, 2026-10-21): the v2.13 delta with the light-window hold, the TC4 step / rate checks and the catch-up is reviewed. Option (b) (seat coefficient loaded, setPcSeatCoef != 0) may be used for starts with ignition (pad first start, stand starts, stand relights) on a unit for which (C1) the B-PC-1 coefficient and T_cal of that serial are loaded (264 (2)), and (C2) the B-TC-1 TC4 rows (spark row as corrected by this line; conversion period <= 0.130 s) have PASSED and the E4-N10 grounded-junction check is done; (C3) a stand relight additionally needs the E4-02 k-dependent eps rule (266 (7)); beyond it the relight is planned REFUSED NOT_VENTED. Re-instated, as corrected by this line: the option (b) firmware rows, residuals and S13T outcomes (FMEA residual per REV-ELEC-5 E5-01); the kIgnBaseDrift 0.06 bar basis for a relight (wording per N07); the evidence of 264 (3), re-shown on v2.13 with a condition: a BASE_AMB at the A1 relight aborts PC_SENSOR when the plant light comes at E1 + 50 ms or later; with a light by about E1 + 30 ms E2 follows on the real light and the offset (< 2.0 bar; -2.0 bar gives NO_IGNITION) rides into RUN, true Pc <= 27 / 32 bar abs at the 25 bar cap / 30 bar firmware abort (MEOP 45) [SIM probe A; CALC]; under option (A) no SEAT_STEP stale offset reaches the A1 relight base; the A1 pad seat row; the stand relight after B1; the B-PC-1 / B-TC-1 TC4 rows. A1 FLIGHT STAYS NO-GO until all of: (i) the 264 (2) pad row is GO on the flight serial (coefficient loaded, TC4 valid at ARM); (ii) OI-A1-BUILD-SEAT-RULE is closed: the A1 HAL image built with seat_arm_rule TRUE and seat_step_relight_inhibit TRUE, EVENT BUILD b2 added to the core with its test for both values and reviewed as a delta, and the pad reads b0 = 1, b1 = the build value, b2 = 1; (iii) OI-GNC-EVENT-BUILD is closed and GNC confirms the FC takes the lost-relight outcome on TLM_RELIGHT d6 & 0x3F = 19 (as for 17); (iv) B-PC-1, B-TC-1 (TC4 rows), B-ECU-1 (with the A1-image row) and the other pad-rule hardware items (B-BLEED-1, B-FC-1) PASSED on the flight hardware; (v) the founders confirm OI-SEAT-STEP-RELIGHT together with OI-JFWD-FLIGHT at flight acceptance (the 264 (7) PROVISIONAL pattern). The fallback (coefficient 0) stays allowed on the stand only within 264 (2). Nothing here is physical approval.'

**What holds for A1:**
- The firmware delta itself is accepted.
- The A1 design is: option (b), plus seat_arm_rule TRUE, plus seat_step_relight_inhibit TRUE, plus kJfwdLsRelightInhibit TRUE.

**Items that keep A1 NO-GO:**
- 264 (2): item (i);
- OI-A1-BUILD-SEAT-RULE, including b2: item (ii);
- OI-GNC-EVENT-BUILD and the FC rule for code 19: item (iii);
- B-PC-1, B-TC-1 and B-ECU-1: item (iv);
- the founders' confirmation: item (v).

## 17. Confirmed numbers

| Number | Value | Tag |
|---|---|---|
| Probe H | 2464 runs per build; 2016 in-window with 0 moves; 448 before-entry (P0 moved in 328, max 0.347 bar; E2 tick moved in 1 / 22); 0 unlit E2; control 256 / 240 moves | SIM |
| Probe A | the tables in E5-03 and (e)(ii) | SIM |
| Probe S, probe D, UT-6 | as above | SIM |
| Probe Q1 | 0 / 8 differ | SIM |
| Widest catch-up g0 | 5.74 K → 0.427 bar at k 3; cap 2.296 s | CALC |
| Hold-end margins | 1.89× / 1.45-1.48× (against 3 K); 3.62× / 2.06-2.10× (against the bound) | CALC |
| Step-limit margins | 5.63× at 0.110 s, 4.77× at 0.130 s | CALC |
| 4× rule | holds to 0.155 s | CALC |
| 6× rule | gives 1.60 / 1.89 K | CALC |
| First conversion | 0.54 K, 2.8× | CALC |
| Tying the bound to the physical maximum | 2.78 K < 3 K | CALC |
| Followed drift bound | 3.7 / 11.2 bar at k 1 / 3 | CALC |
| Split-step bound | ≤ 0.22 bar | SIM |
| kPcSpMinAbs | 0.95 × 4.36985 = 4.151 bar abs | CALC on config.h |
| A1 relight growth | ≥ 0.037 bar at k 3 (0.012 at k 1) | DERIVED on SIM, lower bound |
| Stand relight growth | 0.080-0.094 bar/s at k 3; 0.33-0.40 bar over 4.59 s | DERIVED on SIM, lower bound |
| E4-02 eps table | equals my R4 Q3 | DERIVED |
| test_core | 343 / 0; no-hooks 342 / 0 | SIM |
| S12 | 34 / 38 PASS | SIM |
| Binaries and outputs | byte-identical | SIM |
| Hold cost | 0.033-0.039 bar at the S13T times; 0.072 bar envelope | DERIVED, author; checked against config.h |

## 18. NOT RUN by me

- a full cross-file consistency pass of v4.2 (I checked the rows cited here);
- the MAX31856 datasheet PDF (tCONV and OCFAULT; AS RECALLED / TO-VERIFY);
- a slew-only variant;
- a separate UT-6 ratchet probe;
- stand A5 probe cells;
- a finer light-delay sweep (between 30 and 50 ms) and a finer e sweep (between −1.0 and −2.0 bar);
- a dropout probe (N05);
- the bpc1 as-is S13T run;
- anything on hardware.

## 19. Process and resources

- **Work area.** All builds and runs were in /dev/shm/rev_elec5 at nice 15, one heavy process at a time, make -j1.
- **Memory.** Peak RSS was about 41 MB [measured]. The /dev/shm peak was about 186 MB. /dev/shm/rev_elec5 was removed at 18:54:51Z (confirmed absent at 19:12:54Z).
- **Disk.** Hub net-new is 240,258 B, within the 40 MB budget. Free was 2,300,293,120 B at 19:12:54Z; the stop line is 2,093,796,557 B. None of my processes remain.
- **Slip.** A stray file, /tmp/x_unused_list (2,408 B), was written at 17:53Z (minute only; not stamped with date -u at the time) and removed at once.
- **Probe fixes.**
  - Round 1 had rig flaws: an 18 K/s stand seat ramp, a torch delay of 0, and a plant that did not follow after E2. Its outputs are not cited.
  - An sf("%s", double) call was fixed before round 1.
  - In round 2 the CONTROL BAD message had 7 format specifiers for 6 arguments, which is undefined behaviour. It was fixed (r2b) and re-run. The default and bpc1 outputs are byte-identical across the fix.
- **Blocked command.** One rm with a variable path was blocked by the safety check. I re-ran it with the literal path.
- **Messages.** Interim to the lead at 18:41:08Z (E5-05); lead ruling at 18:43Z.
- **Write scope.** I wrote nothing outside reviews/electronics/r5/ and /dev/shm/rev_elec5/.

## 20. Files

All under reviews/electronics/r5/. **MANIFEST_REV-ELEC-5.sha256 48d5f6a11c81d529** (33 entries; verified at 19:10:15Z).

**data/**

| File | sha256/16 |
|---|---|
| a5_residual_calc.json | 889a1014326d1a3a |
| assembly_note.txt | c18ec7a5a7d8a9bd |
| build_v213.log | 0afcb13f4b015a9e |
| chain.log | 306d2a384a94d6d3 |
| diff_engine_ecu.txt | 656bcac87ee7c212 |
| rerun_hashes.txt | c6f0e66112adeefb |
| test_core_nohooks_out.txt | 223d38c05d28ee02 |
| test_core_out.txt | f53e88766369c8b4 |

**probes/**

| File | sha256/16 |
|---|---|
| nohold_control_patch.diff | 1940313bda7c25b6 |
| probe.log | 8679d31f65030d5d |
| probe_build_bpc1.txt, probe_build_def.txt, probe_build_nohold.txt | e3b0c44298fc1c14 (empty = clean builds) |
| probe_v213.cpp | 3a207fdc9f14c556 |
| probe_v213_bpc1_out.txt | d303d3c8a0412f2b |
| probe_v213_def_out.txt | 8a5f432da2fbb70b |
| probe_v213_nohold_out.txt | eb170e2d2d9c39ae |

**scripts/**

| File | sha256/16 |
|---|---|
| a5_residual_calc.py | e4a53dafc2a84841 |
| bom_diff.py | 611b9a2e8a25218e |
| bom_rows.py | 6ef305e3eb42b8eb |
| build.sh | 69cff9d78e039bb0 |
| chain_sil.sh | cd34b128c078fedd |
| check_sf.py | 1cfe02914fca2ee8 |
| make_manifest.sh | c0e8d1bdffc75240 |
| make_nohold.py | 4fce1c142bf7a374 |
| probe_build_run.sh | a07b07fabb019416 |
| rerun_hashes.sh | f2b9f43cfd4f4a04 |
| s13f_cov.py | f9291eb8100cd0d1 |
| s13f_cov2.py | a389db2c5c867909 |
| v42_get.py | f7abf4fe4952679f |
| v42_grep.py | 17beb3220bf383c6 |
| v42_limits.py | 82b4971fa1167ee0 |
| v42_scan.py | d4a3a2540af069c9 |

**The stand relight-growth figures in (e)(i)** were computed read-only at 19:0x from staging_v2.12 results/v2p12/seat_hist/*.csv with the method of a5_residual_calc.py. They are not saved as a file. Command: python3 -I inline, the seat rise from E0 + 0.05 s over 1 / 4.59 / 10 s.

END REVIEW-ELECTRONICS-R5
```
