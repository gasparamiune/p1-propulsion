REV-ELEC-2. Independent delta re-review of Electronics v2.10 (hub copy) and of lead CHANGELOG line 203.

Reviewer: the REV-ELEC-1 reviewer. I am not the author of any item reviewed here. Date: 2026-10-13.

Scope: the v2.10 hub copy only. The moving v2.11 workdir was not used.

Everything below is code reading, re-execution of the author's SIL, reviewer-written simulation, or arithmetic. A reproduced number shows that a computation repeats. It does not show that the hardware or the physics is right. Nothing here is physical approval.

Tags used: SIM, DERIVED, DESIGN, DATASHEET, LITERATURE, ASSUMED, TO-VERIFY, MISSING, LEAD. File:line references point to the hub files listed in section 1. References are to engine_ecu.cpp unless another file is named.

## 0. VERDICT

**Overall: REVISE.** 0 BLOCKING, 6 MAJOR, 10 MINOR, 7 NOTE.

**What holds.**
- The v2.10 SIL record reproduces byte-identically under reviewer control.
- The author's RE statuses are truthful:
  - 17 CLOSED: 11 confirmed outright, 6 confirmed with residuals;
  - 8 OPEN: true as stated;
  - 4 DISPOSITIONED: confirmed.

**What drives REVISE.**
- **R2-01.** The S17 result "no released dead vehicle at the W10 < 6 m/s bound" holds only when Pc is lost within about 8 ms of E2 and there is no frame noise.
- **R2-02.** Only a single DROGUE 0 frame can end the R2 command hold.
- **R2-03, R2-04, R2-05.** Three line-203 items, (1)(b), (5) and (3), have acceptance tests or criteria that either cannot discriminate or cannot be met as written.
- **R2-06.** Bench plan v3 has no step the founders can execute now.

| Deliverable | Verdict | Conditions |
|---|---|---|
| Firmware v2.10 core | ACCEPT WITH COMMENTS as the v2.10 SIL baseline | For v2.11: R2-02 (ECU backstop), R2-05 (cap form), R2-08, R2-12. R2-11 needs a lead decision |
| SIL record sil_v2p10 | ACCEPT WITH COMMENTS as a reproducible record | R2-01, R2-09, R2-10, R2-16 |
| FA-1 harness and fa1_overrange_v2p10.json | ACCEPT as SIM evidence for the 070BG no-line chain | R2-03, R2-17. The line-205 transducer needs a new chain (R2-21) |
| interfaces/electronics.json v3 | ACCEPT WITH COMMENTS as the working interface | R2-07, R2-15. v4 must fold lines 203, 205 and 208 |
| Bench plan v3 | REVISE | R2-06, R2-13, R2-02 (c) |
| BOM v2.2 | ACCEPT WITH COMMENTS | R2-14, R2-20 |
| REPORT-v2.10-HANDBACK | ACCEPT WITH COMMENTS | R2-09, R2-11, R2-15 |

**Line 203, item by item.**

| Item | Verdict |
|---|---|
| (1)(a) | Follows from the evidence |
| (1)(b) | REVISE the sizing basis and the acceptance set (R2-03) |
| (2) | Follows; superseded by line 205 |
| (3) | REVISE (R2-05) |
| (4) | Follows |
| (5) | REVISE (R2-04) |
| (6) | Follows |
| (7) | Follows, with NOTE R2-22 |

**RE-12:** ACCEPT the flight extension of the A7 high-side blank as DESIGN, with four conditions (section 5 (f)).

## 1. CONFIGURATION, INPUTS AND METHOD

**Inputs** (sha256/16, all verified):

| Input | sha256/16 | Check |
|---|---|---|
| 06-electronics/REPORT-v2.10-HANDBACK.md | 05af80b9cdbee9b5 | |
| 06-electronics/SHA256SUMS-v2.10.txt | 674eef94498822dd | 502/502 OK |
| archive/v2.9/SHA256SUMS.txt | 5f5f9a172b41339d | 406/406 OK |
| interfaces/electronics.json | 38bf149f368c1d4c | |
| reviews/REVIEW-ELECTRONICS.md | 471d830c8d00dd85 | |
| interfaces/CHANGELOG.md, first 204 lines | 60190e33f21480b6 | as briefed |
| interfaces/CHANGELOG.md, whole file (213 lines) | 07c70c7d72108fdd | |

Lines 205-213 of the CHANGELOG were appended during the review. I cite them as context only:
- line 205 reselects the flight Pc transducer and deletes the sense line;
- line 208 is the lead's decision on REV-GNC-5.

**Firmware files reviewed** (sha256/16):

| File | sha256/16 |
|---|---|
| config.h | 0880af5a27880a5b |
| engine_ecu.cpp | 6e62a7e4e37930bd |
| engine_ecu.h | cc103800ea92ad4e |
| types.h | 76196d18c43330fe |
| protocol.h | 36f3dd3621529bc5 |
| protocol.cpp | 85be2f982558c2cc |
| Makefile | 1ba63ce7b2bc8ed9 |
| test_v210.inc | a92e4e8785791473 |

**Build.**
- 55 hub firmware files were copied; their hashes are identical to the hub.
- MANIFEST_v1 (6d1dd43ddeeba0d7): 39/39 source hashes match.
- Compiler: g++ 13.3.0 with the Makefile flags.
- The rebuilt binaries equal the binary hashes recorded in MANIFEST_v1:

| Binary | sha256/16 |
|---|---|
| sil | 986f77d935ef9f8c |
| sil_bpc1 | 12fde7c8e52daa08 |
| test_core | 9baa6a63eb144e2e |

**Run environment.**
- Python 3.13.16, numpy 2.5.4, scipy 1.18.1, run with -I.
- One heavy job at a time, at nice 15 (lead instruction).

**Reviewer code.** Written independently of the author's code:
- **rev_fa1_chain.py:** the FA-1 chain. It reads Combustion's fa1_envelope_v2p4a.json (64b328150025fa1e) directly.
- **rev_inwindow_probe.py, rev_fa1_tau_sens.py, s5_tail.py, mcone_extract.py, dump_cfg.cpp and xcheck_json_cfg.py.**
- **make_probe.py:**
  - it patches a copy of the S17 scenario file only; the ECU core is not changed;
  - built without R2PROBE, the probe reproduces S17_r2hold.json (c125095719fa563a) and its three traces byte-identically.

## 2. FINDINGS

### MAJOR

**R2-01 (MAJOR). S17's W10 < 6 m/s result holds only for an early Pc loss without frame noise.**

The claim:
- electronics.json l.1946: "R2 never met at d_app 0 and at the W10 < 6 m/s bound 20.85 N, 200 and 500 N commands -> ABORT frame at t_E2 + 500 ms, drogue kept (no released dead vehicle)".
- CHANGELOG l.195 repeats it.
- The recorded cases lose Pc at E2 + 5 ms, with the 100 Hz frame at ms mod 10 = 5.
- l.1958 already reports 2 of 3 frames when Pc is lost at E2 + 10 ms ("one frame short"). l.1946 still states the result without conditions.

Reviewer probe [SIM]. Setup: the S17 stand-in FC, the W10 < 6 m/s bound d_app = 20.85 N (37.16 − 16.31), the hold active, and a flame-out 1 ms after the Pc loss.

| Pc loss after E2 | Dead vehicles released |
|---|---|
| 1 to 8 ms | 0 at every phase (0/20 at 5 ms, over 10 × 2 frame phases) |
| 10 ms | 1/20 (release at E2 + 30 ms, F_max 40.89 N) |
| 12 ms | 4/10, including the recorded phase (release at E2 + 35 ms) |
| 15 ms | 7/10 |
| 20, 30, 50 ms | 3/10 each, released 1 to 3 ms before the ECU FLAMEOUT abort at loss + 23 ms. The other 7 end with no FC decision after that abort |

With 5 N rms frame noise at the same bound (Pc lost at E2 + 5 ms):

| Case | Dead vehicles released |
|---|---|
| Hold active, 200 N | 42/100 |
| Hold active, 500 N | 42/100 |
| No hold | 100/100 |

- With the hold, releases fall between E2 + 35 and E2 + 495 ms; the median is 165 ms.
- The record's noise sweep is at calm only (l.1924-1940: 0/30).
- The result is consistent with the stated 3.59 N steady margin (l.1950) against 5 N rms.
- If GNC's 20.85 N bound already contains the FC's measurement noise, this case double counts [TO-VERIFY with GNC].

Why it matters:
- The hold exists for a flame-out in the first tens of ms after E2, which FLAMEOUT_OPT does not cover (json l.1725: it needs 20 lit ticks).
- That 10-20 ms range is where the stand-in releases dead vehicles. The cause is the low-pass carry-over of the lit thrust.

Gate: GNC R2 v2 freeze; B-FC-1 / HIL.

Action:
1. Restate l.1946 and the CHANGELOG 195 result as conditional: Pc lost within 8 ms of E2, calm.
2. Extend S17 to Pc-loss onsets of 1-50 ms × 10 frame phases × seeded noise, at 200 and 500 N, with and without the hold.
3. GNC states:
   - the R2 counting start and the estimator flush (owner action, json l.1984);
   - whether d_app includes measurement noise.
4. Test against GNC's R2 v2, not the stand-in. CHANGELOG 204 (4) F7 gives +5.30 N at W10; line 208 (5) gives the 0.5 s window margins.

**R2-02 (MAJOR). One lost DROGUE 0 frame keeps the hold on for the rest of the burn.**

Code and interface:
- l.1479: `r2_hold_ = !stand_ && drogue_attached_ && !pc_sensor_ok_`.
- drogue_attached_ changes only on Cmd::DROGUE 0/1 (l.921-922). It resets only at a new arming session (l.613-615).
- The json rule (l.1710) ends the hold only at DROGUE 0 or when Pc is valid again.
- A pure retransmission is rejected (protocol.cpp l.63-65, seqOk), so a resend needs a new sequence number.
- The b6 echo check is specified only "before a RELIGHT" (json l.1721).
- The hold flag is log-only (l.1656; json l.1720-1722).

Probe E [SIM]. Lit and starved engine, Pc lost at E2 + 5 ms, R2 release frame dropped:
- the hold stays on for 1305 ticks (E2 + 5 to E2 + 1309 ms, the end of the run);
- thrust stays at 62.5 N for both the 200 and 500 N commands;
- the control case holds for 421 ticks and ends with the release at E2 + 425 ms.

So a released, lit vehicle with Pc invalid is held at the start level. No B-FC-1 row covers this case (bench_plan_v3.md l.201-216).

Gate: B-FC-1 / HIL; FSW freeze; A1.

Action:
- (a) FC rule: after DROGUE 0, re-send with a new sequence number until d6 b6 = 0 is seen (TLM_RELIGHT, 50 Hz), with a bound.
- (b) ECU backstop: end the hold no later than E2 + pcf_tmax + a stated margin, covering both R2 v2 windows (0.5 s and 0.8 s, CHANGELOG 208 (5)). Log it.
- (c) Add a B-FC-1 row and a test_core case for a lost DROGUE 0.

**R2-03 (MAJOR). Line 203 (1)(b): the acceptance test cannot fail as written, and the sizing quantity is not the one that governs the trips.**

The acceptance set cannot show a cost:
- v2.10 S6 (58 cases) injects every genuine over-pressure in RUN, at t = 3.0-3.3 s.
- The in-window cases (t_inj 1.4-1.45 s) are:
  - torch faults;
  - sensor faults;
  - the two late-light hard-start delays, with plant Pc max 28.6 and 27.0 bar abs (S6_aborts.json).
- S9 has no over-pressure case.
- So a re-run of S6/S9 cannot show what a ride-through costs.

Sizing [SIM]. Reviewer chain, 896 cases × the 8 no-line author configurations; the author's harness agrees:

| Quantity | Result |
|---|---|
| Longest filtered run above 30 bar abs | 12 ms. Persistence 10 ms leaves 127-134 trips; 15 ms leaves 0 |
| Comparator at the low band edge | RC 7.5 ms: 13-14 trips. RC ≥ 10 ms: 0 |
| Readings ≥ 4.75 V | only before E2 and never twice in a row (5-6 cases, tau 0.1 ms only) |
| Firmware 30 bar trips falling after E2 | 276-310 of 361-376 |
| Filtered Pc above 30 bar | until at most 8.0 ms after E2 (19.8 ms after the light) |

- The head time above 45 bar (≤ 4.45 ms, reproduced) is a structural exposure, not a detector duration.
- A window that ends at E2 would leave 276-310 trips.

Cost of a ride-through on genuine in-window events [SIM on synthetic histories; t_close 0.038 s ASSUMED from S6].

The three detector sets compared are:
- set A, as built;
- set B: persistence 13 ms, comparator RC 10 ms, over-range N 13;
- set C: persistence 15 ms, comparator RC 12.5 ms, over-range N 15.

| Event | First detection, set A / B / C | Head time above 45 bar to detection plus closure, set A / B / C |
|---|---|---|
| 50 bar step from 3 ms | 8.44 / 13.23 / 15.78 ms | 43.65 / 48.43 / 50.98 ms |
| Ramp to 60 bar in 30 ms | 22.08 / 26.08 / 27.95 ms | 37.72 / 41.72 / 43.59 ms |
| Worst FA-1, then a 47 bar plateau | 5.48 / 29.46 / 30.99 ms | 22.43 / 46.40 / 47.93 ms |
| Worst FA-1, then a 35 bar plateau | 5.48 / 40.25 / 44.69 ms | none above 45 bar |
| Worst FA-1 alone | 5.48 ms as built; ridden through otherwise | 3.73 ms in all sets |

Other points:
- A comparator RC switched only inside the window would put a firmware-driven element into the independent hardware path (json l.2044: comparator latch, then ARM bus off).
- The SIL limits the averaged 1 kHz reading at 4.95 V, not each sample (handback item 14; json l.2031). An in-loop re-run needs per-sample limiting first.
- Line 205 reselects the flight transducer, so every chain parameter changes.

Gate: v2.11 flight adoption of (1)(b); SIL/HIL freeze.

Action (lead):
1. Size from detector-side durations, re-derived for the line-205 transducer:
   - filtered persistence ≥ 13 ms plus margin;
   - over-range N ≥ 2;
   - comparator either fixed, or RC ≥ 10 ms.
2. Run the window from E1 to at least E2 + 8 ms plus margin.
3. Add in-window genuine over-pressure cases to S6: steps, ramps, and FA-1 followed by 35-50 bar plateaus.
4. Compare them with LC-TB70, stated by Mechanical as a pressure-time envelope.

Reviewer recommendation: keep the comparator RC fixed, so the hardware path stays independent.

**R2-04 (MAJOR). Line 203 (5): the per-class S13 criteria cannot be met as written, and two observed classes are missing.**

"MV never opened" cannot be met. The MV latch is set before the BASE_HIGH check at the lift tick (l.1444-1447), at each of these points:
- PREPRESS entry (l.640, pad);
- IGNITION entry (l.657);
- PURGE entry (l.284);
- a direct relight (l.863).

"Refuse with its reason code" does not match the code:
- Pad/stand BASE_HIGH is doAbort(Abort::PC_SENSOR) with f2 BASE_HIGH and no lift (l.1446-1447).
- S13 B-ext pad +0.8 bar shows E1 = none and refused = 0.
- This matches 166 (1) ("refuses the lift with PC_SENSOR"). It is not a refuse:: code.

Missing classes [SIM; S13B_ext_bpc1_false.json and _true.json]:
- **A1 BASE_HIGH proceeds to RUN on the measured P0** (l.146-149), as 166 (1) decided. Class a1_lit_RUN reaches +1.0 bar; at +0.8 bar, E2 comes at E0 + 0.187 s.
- **Negative offsets beyond about −0.7 bar** (about −0.5 bar with kBpc1Shown):
  - they set BASE_AMB (P0 := 0, l.150);
  - the lift happens (E1 = E0 + 45 ms);
  - PC_SENSOR then aborts, on the pad and at A1.
  - The abort is consistent with the A7 HOLD low edge, P0 − 0.30 bar (l.269-275) [DERIVED from code reading].

Confirmed [SIM]: 0 false E2 in both builds. Every unlit run ends NO_IGNITION, PC_SENSOR or TORCH_FAULT.

Gate: SIL/HIL freeze (RE-02).

Action: restate the criteria per location.

| Class | Criterion |
|---|---|
| Pad/stand BASE_HIGH | PC_SENSOR abort with BASE_HIGH; lift never commanded; MV closed by the abort |
| A1 BASE_HIGH | RUN on the measured P0 |
| BASE_AMB | a stated outcome |
| Torch gate not reached | TORCH_FAULT |
| All unlit runs | 0 false E2 |

**R2-05 (MAJOR). Line 203 (3) purge cap: the flow basis, a check that cannot fail, and the hardware bound.**

**Firmware flow model.**
- hbFlowEnd (l.296-300) counts flow = (V1 close command + 0.080 s) − (V2 open command + 0.030 s) = both-open + 0.050 s.
- Constants: config.h l.782-786; valve times ASSUMED.

**The 75.9 g figure is ambiguous.** It can be reproduced two ways:
- 29.2 g/s × (2.55 + 0.05) s. This is the Combustion basis in bleed_driver_v1.json (73.0 g / 2.5 s, CHANGELOG 166 (3));
- 29.76 g/s × 2.55 s, if flow is taken as equal to the both-open time.

The same item cites Combustion 29.8 g/s and SIL 32.0 g/s; bleed_driver_v1.json has SIL 31.44 g/s. Using the firmware flow model [DERIVED]:

| Flow basis | Result |
|---|---|
| 29.8 g/s | the 2.55 s cap gives 77.5 g; 76 g needs a cap ≤ 2.50 s |
| 31.44 g/s | 76 g needs 2.367 s, below the scheduled 2.45 s overlap |
| The 2.5 s schedule and 76 g | compatible only for mdot ≤ 30.4 g/s |

**The truncation check cannot fail.**
- The schedule fixes the commanded overlap at 2.45 s: V2 open command at 0.32 s, V1 close command at 2.77 s after PURGE.
- The cap (l.337-342) times commands.
- So "not truncated under the valve timing tolerances" is true by construction. It says nothing about the vented mass.

**The hardware bound is above the cap.**
- PURGE_EN AND the LTC6993 one-shot (json l.3005-3012; window 3.048-3.243 s) gates the whole sequence.
- So the hardware-only bound is 3.293 s of flow: 96.2 g at 29.2 g/s, 103.5 g at 31.44 g/s (bleed_driver_v1.json, hardware-window row) [DERIVED].
- CHANGELOG 166 (3) required "a hardware one-shot limiting each enable to the cap".
- The author records that a window equal to the cap would cut the flow (cap_equal_window_would_cut_flow = true).
- So 166 (3) is not met, and 203 (3) does not address it.

Gate: CF-4 / B-BLEED-1; A1.

Action:
1. After B-BLEED-1 and CF-4, set the cap as overlap ≤ 76 g / mdot_measured − (t_close − t_open)_measured.
2. Until then, carry one stated flow basis.
3. Replace the truncation statement with that measured-time check.
4. Then either:
   - add a hardware timer on the both-commanded-open condition that drops V1 at the cap; or
   - the lead restates 166 (3), and the 96-104 g residual goes to GNC and the FMEA.

**R2-06 (MAJOR). Bench plan v3 has no step the founders can execute now.**

Every step in bench_plan_v3.md l.28-41 depends on something that does not exist yet:

| Step | Needs |
|---|---|
| 0 | the layout (not started) |
| 1-2 | a built ECU |
| 3 (B-PT-1 / B-PC-1, including the 194 (7) / 203 (2) over-range row) | step 2. B-PC-1 also requires "a flight ECU from a board that passed the RE-15 checks, and the HAL" (l.104) |
| 5 | selected valves (none yet) |
| 6 | the FC (FSW not implemented; json l.1724) |
| 7 | the HAL |
| 8-9 | rigs and the hot-fire stand |

Gate: B-PC-1; first static fire.

Action: add a block of work the founders can do now:
- **RFQs** delivered to Sønderborg DK-6400 for BOM rows 237, 238, 244, 245 and 250. Enter no price until quoted.
- **Supplier inquiries:**
  - TE: 070BG saturation, recovery and post-over-range shift; the line-205 replacement unit;
  - PCB: 113B22 excitation at 19 V compliance; coating;
  - NI.
- **Anemometer:** the mast and logger (row 250).
- **Spare-070BG over-range row:**
  - run it on a bench supply and DAQ instead of the ECU;
  - reserve that spare for hydraulic testing, never for N2O service;
  - after line 205, this row characterizes the stand unit only.

### MINOR

**R2-07. electronics.json l.2035 is wrong.**
- It says "in RUN no immediate abort, Pc invalid from then on".
- Pc validity is per tick (l.1293). The TLM markers, the open loop (l.1494-1496) and the R2 hold (l.1479) all follow it.
- Only fault::PC_SENSOR (l.1294) and d6 b7 (l.1664) latch, until DISARM in SAFE (l.804).
- Gate: interface freeze. Action: correct it in v4.

**R2-08. test_core is evidence for the hooks build only.**
- Makefile l.31-32 says test_core does not define ECU_SIL_TEST_HOOKS, but l.54-56 builds it with -DECU_SIL_TEST_HOOKS.
- A no-hooks build fails at test_v210.inc:157 (test_inhibit_purge_close; build_test_core_nohooks.log).
- The hook members default to false (engine_ecu.h l.50-55), and the core has 5 #ifdef blocks (l.644, 649, 956, 1188, 1572). So the flight behaviour is equivalent by inspection only [DERIVED].
- Gate: SIL/HIL freeze.
- Action: guard the hook test, record a no-hooks test_core run, and fix the comment.

**R2-09. S6 timing changes from v2.9 to v2.10 are not disclosed.** They appear nowhere in the handback, the CHANGELOG or the json (sil_v2p9 vs sil_v2p10 S6_aborts.json):

| Case | v2.9 | v2.10 |
|---|---|---|
| pintle_jam_steady_cmd_detect_late: abort | 0.927 s | 1.571 s |
| pc_reads_low_x0p70_500N_24C_Cd0p8_over_thrust_pc_valid: abort | 0.165 s | 0.365 s |
| same case: plant Pc above 30 bar (below MEOP) | 0.133 s | 0.209 s |

- The hard-start late-light cases moving to NONE is intended (RE-01).
- Gate: SIL/HIL freeze. Action: disclose, explain, and accept or fix.

**R2-10. S5 summary artifacts (RE-23 residual).**
- S5_mc.json reports overshoot_p95_pct = overshoot_max_pct = 25 and p50 = 7.47. These include non-flying runs: in 3000 runs, all 714 non-flying runs carry dn_ovs = 25.00 % exactly.
- Over flying runs only, the up-step overshoot p50/p95/max is 2.60/7.78/12.31 %.
- The pass fractions use all runs (0.797) or armed runs (0.909) as the denominator.
- Action: compute over flying runs and state the denominators.

**R2-11. OI-GUARD-BAND: mechanism now isolated.**
- The cold decision takes the coldest of the wall TCs and Tsat(P_tank), with no margin (l.577-581). The hot side uses per-channel guard bands (l.569-576, LEAD 172 (4)).
- Runs 125 and 127 [SIM]:
  1. P_tank falls in PREPRESS, after the ARM check has passed: 45.099 to 44.938 bar abs.
  2. The firmware Tsat falls 288.209 → 288.055 K (run 127: 288.186 → 288.030 K).
  3. IGNITE at 1.40 s is refused TANK_COLD (l.548).
  4. The ECU stays in PREPRESS with the MV open until the scenario's SHUTDOWN at 7.60 s (l.873). Without that command the limit would be 60 s (config.h l.149).
- Over 3000 S5 runs, 186 (6.2 %) do not fly:
  - 145 are refused at ARM (T_tank0 288.15-289.08 K);
  - 41 have IGNITE refused after PREPRESS (T_tank0 288.16-289.03 K).
- Gate: pad operations.
- Action (lead decision): either an ARM-time margin of at least the PREPRESS drop (about 0.16 K) plus the estimate uncertainty, or evaluate the cold rule at ARM only.

**R2-12. Contradictory and stale comments.**
- config.h l.369-372 says no E2..E2 + 0.45 s blank is needed in flight. This contradicts l.378-382 and the RE-12 rationale: the A7 flag sets fault::PC_SENSOR (l.274), which latches b7 (l.1664).
- l.955 says "(> 4.75 V = 73 bar)". On the 070BG scale, 4.75 V is 74.4 bar g (75.4 bar abs).
- Action: correct both.

**R2-13. Bench plan v3 residuals (RE-13).**
- l.71: the E0 row cannot pass as written (U3V70F12 rating). Carry it as an open design item with an owner.
- l.144: compares the B-PNT-1 closed-loop t10-90 with the S5 thrust-step t10-90. These are different loops.
- l.246: the IGN-1 latency criterion "≤ the latency GNC accepts" has no number.
- l.255-256: T1-T4 "as in v1", but no v1 is in the hub.
- B-FC-1 (l.201-216) has no lost-DROGUE-0 row (R2-02).

**R2-14. O2/N2O cleanliness (RE-22 partial).**
- bom_v2p2.csv rows 212 (SOL1 torch N2O valve) and 214 (SOL3 tank vent valve) have no O2-clean or medium note, despite the claim of a note on "every N2O-wetted row".
- Row 245 (reference gauge with a hydraulic hand pump) has no medium-separation note, although B-PT-1 checks transducers that may be N2O-wetted.
- Action: add the notes. Reserve the pump for units that never see N2O, or specify re-cleaning.

**R2-15. "72 ms above MEOP" is stale.**
- Handback l.440 and json l.4914 (OI-TB-MEOP) say 53.4 bar abs above MEOP for 72 ms.
- The v2.10 S6 record for throat_blocked_70pct_500N_24C_Cd0p8 gives a 53.4 bar abs peak and t_Pc_above_MEOP_s = 0.034 s. The 72 ms is a v2.7 value.
- This matters for 203 (1)(b), which compares against "what Mechanical has accepted".
- Action: correct it. Mechanical states LC-TB70 as a pressure-time envelope.

**R2-16. The S17 starve threshold is not reported.**
- json l.1970 says "a longer plateau reaches the ABORT of a lit engine (not run)".
- Probe D [SIM, calm, hold active]:
  - starve ≤ 0.46 s: the lit vehicle is released at starve + 25 ms;
  - starve ≥ 0.48 s: the lit vehicle is held and aborted at E2 + 0.5 s;
  - at the W10 < 6 m/s bound, the lit vehicle is released at E2 + 35 ms for every starve length.
- The margin over GNC's 0.1-0.4 s starve range is 60-80 ms.
- Action: record the threshold, and re-run it for the 0.8 s R2 v2 window (CHANGELOG 208).

### NOTE

**R2-17. 070BG datasheet citations disagree.**
- config.h l.347 and l.427 cite "M3200 06/2026". config.h l.858 and json l.1994 cite 08/2018, which is the revision I retrieved (farnell 3007269.pdf).
- The rise-time row reads "< 2 ms (mV output); < 3 ms (mA output)". It has no row for the 0.5-4.5 V output. tau 0.9 ms matches the 2 ms row (10-90 % = 2.2 tau).
- Reviewer sensitivity at tau 1.36 ms (the 3 ms row) [SIM]:

| Quantity | tau 1.36 ms | tau 0.9 ms |
|---|---|---|
| Aborts | 351 | 361 |
| Persistence 5 / 10 / 15 ms | 351 / 128 / 0 | 361 / 131 / 0 |
| Comparator nominal / low | 96 / 143 | 113 / 156 |
| Longest filtered run | 12 ms | 12 ms |

- The sizing conclusions are insensitive to tau. The voltage-output response is TO-VERIFY with TE; it is moot for flight after line 205.

**R2-18. Harness and SIL limit the ADC differently.**
- The harness limits each sample; the SIL limits the average (json l.2031).
- The "vsat none" rows are bounds.
- In the reviewer chain, per-sample and averaged limiting differ by at most 4 cases per flag.

**R2-19. S15 stand starts end NO_IGNITION on 4 late lights.**
- Flight starts have 0 (S15_start_mc.json).
- Plan IGN-1 for it.

**R2-20. Stale labels.**
- test_core.json says "v2.8.3" (disclosed, handback item 20).
- BOM row 250 says "launch commit PROVISIONAL (LEAD l.161 (6))". CHANGELOG 181 (6) made the W10/sigma_u rule HARD for A1.

**R2-21. Line 205 supersedes the 070BG flight items.**
- This covers the proof margin, the port period, the over-range behaviour and the FA-1 chain constants.
- The author's and the reviewer's FA-1 counts are conditional on the 070BG chain.

**R2-22. Line 203 (7) "ECU hold lift equals the start-level lift".**
- The ECU holds a thrust (62.5 N, config.h l.686) through the open-loop map. In S17 that gives 0.2154 mm at the A1 state; json l.1954 lists three unreconciled lifts.
- Equality needs either a lift-commanded hold or a stated map identity at the A1 state.

**R2-23. The hold engages on any invalid tick, including a high over-range reading in RUN** (l.1293, l.1479).
- A one-tick glitch costs a 55 ms return ramp from 62.5 to 200 N.
- With 203 (1)(a)/(b) in v2.11, state whether over-range ticks after E2 engage the hold.

## 3. CONFIRMATIONS

**Integrity and build.**
1. Hub integrity: SHA256SUMS-v2.10 passes 502/502 and archive/v2.9 passes 406/406 (hash only). All brief inputs are at their briefed hashes.
2. Source and binaries:
   - the 55 hub firmware files are identical;
   - MANIFEST_v1 source hashes match 39/39;
   - the rebuilt sil, sil_bpc1 and test_core equal MANIFEST_v1's binary_sha256_16 [SIM].
3. test_core gives 309 passed, 0 failed. The record log matches over its 311 lines.

**SIL re-runs [SIM].**

4. 22 outputs are byte-identical to the record, and 0 differ:

| Scenario | Outputs |
|---|---|
| S17 | json, 3 traces, n2o file |
| S6 | json |
| S15 | csv and json |
| S5 (300 runs) | csv and json |
| probe F | outputs |
| S14 | json |
| S16 | json |
| S12 | json |
| S13 B-ext, both builds | outputs |

   115 trace files have no record counterpart; their hashes are logged.

5. S5 extended to 3000 runs (the first 300 rows are identical to the record). RE-04 holds:

| Quantity | Value |
|---|---|
| Plant Pc p99.9 | 27.316 bar abs |
| Plant Pc max | 28.224 bar abs (1 run above 28 bar) |
| Runs above 29 bar | 0 (one-sided 95 % upper bound 1.31e-3 per run) |
| PC_OVERPRESSURE | 0 |
| Up-step t10-90 p50 / p95 / max | 0.104 / 0.126 / 0.143 s |
| Up-step t10-90 ≤ 0.100 s | 916 of 2286 flying runs |

**FA-1 chain [SIM].**

6. The independent chain agrees with the author's harness:

| Comparison | Result |
|---|---|
| Flag differences per configuration (8 configurations) | ≤ 4 cases |
| Filtered peak | within 0.084 bar |
| E2 | within 0.48 ms |
| Aborts as built (of 896) | reviewer 361-376; author 362-379 |
| Filtered peak max | ≤ 44.75 bar abs |
| Head time above 45 bar | ≤ 4.45 ms |

   The sense-line configurations were not rebuilt; they are moot for flight after line 205.

**R2 hold, interface and json.**

7. The R2 hold logic matches 186 (2) and json l.1710 [DESIGN]:
   - command = min(cmd, 62.5 N) at once, with the limiter parked;
   - return at kStartRamp_Nps (l.1479-1486);
   - resets at l.612 and l.613-615.
8. The interface is consistent [DESIGN]:
   - DROGUE accepts 0/1 only (l.921-922);
   - CMD_STATE 17 (types.h l.41) with key 0xA54B (protocol.h l.31; checked at protocol.cpp l.86);
   - d6 layout: b0-b5 refuse code (mask 0x3F, static_assert at protocol.h l.123), b6 DROGUE, b7 PC_VALID (protocol.cpp l.167-168; decoded at l.180).
9. electronics.json v3 against config.h: all 154 config.h citations agree numerically [DERIVED]. 186 (2), 194 (4) and 194 (7) are folded in.

**Datasheet and purge arithmetic.**

10. 070BG proof is 140 bar g = 141.0 bar abs, burst 5× rated [DATASHEET 08/2018]. Saturation and recovery are MISSING, as the author states.
11. The purge arithmetic in bleed_driver_v1.json reproduces:

| Case | Vented mass |
|---|---|
| 2.5 s scheduled flow | 73.0 / 78.6 g |
| 2.61 s cap | 77.7 / 83.6 g |
| Hardware window | 96.2 / 103.5 g |
| 76 g at 29.2 g/s | needs 2.553 s overlap |

**Author disclosures confirmed.**

12. These disclosures are confirmed:
   - the hardware window cannot equal the cap;
   - the S13 criteria conflict (item 5);
   - OI-GUARD-BAND (item 6);
   - three unreconciled lifts (item 13);
   - SIL ADC limiting (item 14);
   - sense-line floor in 640 of 896 cases (item 17).

## 4. RE-01 TO RE-29

| RE | Author status | Reviewer verdict | Evidence |
|---|---|---|---|
| RE-01 | CLOSED | CONFIRMED | A5 abort removed; LIGHT_SPIKE is a record only (l.187, l.1649); 30 bar check on filtered Pc (l.953-961); S15 0 A7/OVP/HARD (reproduced); S6 late-light cases end NONE |
| RE-02 | OPEN | TRUE | One-sided P0 (l.146-150); S13 B-ext fails 32/164 and 64/164; see R2-04 |
| RE-03 | CLOSED | CONFIRMED | b6/b7 come from the filtered term (l.172-180); v210-3 and v210-8 pass |
| RE-04 | CLOSED | CONFIRMED | Clamp at control.cpp l.146 and l.164; S5 3000 runs p99.9 27.316 bar abs, 0 PC_OVERPRESSURE |
| RE-05 | OPEN | TRUE | No valve; cap gives more than 76 g; bench l.185; R2-05 |
| RE-06 | OPEN | TRUE | firmware/src holds the core only |
| RE-07 | OPEN | TRUE | S16 reproduced; drift not measured |
| RE-08 | CLOSED | CONFIRMED | l.764, l.1044; v210-10 |
| RE-09 | OPEN | TRUE | Bench l.71 |
| RE-10 | OPEN | TRUE | Valve times ASSUMED (config.h l.782-784) |
| RE-11 | CLOSED | CONFIRMED | Second and third generators (sil_main.cpp l.428-457) |
| RE-12 | CLOSED | CONFIRMED WITH RESIDUAL | Blank at l.263-267; S15 0 A7 aborts; R2-12; flight extension in section 5 (f) |
| RE-13 | CLOSED | CONFIRMED WITH RESIDUALS | Criteria per test exist; R2-06, R2-13 |
| RE-14 | CLOSED | CONFIRMED | BOM rows 237, 238, 244, 245, 249, 250 are TO-QUOTE delivered to DK-6400; no price entered |
| RE-15 | OPEN | TRUE | Bench l.28 |
| RE-16 | CLOSED | CONFIRMED WITH RESIDUALS | 154/154 citations agree; R2-07, R2-15 |
| RE-17 | CLOSED | CONFIRMED | l.548, 577-581, 751, 847; guard band in R2-11 |
| RE-18 | CLOSED | CONFIRMED | l.1233 |
| RE-19 | CLOSED | CONFIRMED | l.421, 766, 1097 |
| RE-20 | CLOSED | CONFIRMED | l.625-627, 953-961; FA-1 chain agrees |
| RE-21 | CLOSED | CONFIRMED | MANIFEST_v1 binary hashes equal the reviewer rebuild |
| RE-22 | CLOSED | PARTIAL | R2-14 |
| RE-23 | CLOSED | CONFIRMED WITH RESIDUAL | eng03_clause_map is present; R2-10 |
| RE-24 | DISPOSITIONED | CONFIRMED | Line 203 (6) |
| RE-25 | CLOSED | CONFIRMED WITH RESIDUALS | R2-08, R2-12, R2-20 |
| RE-26 | DISPOSITIONED | CONFIRMED | config.h l.367-368 |
| RE-27 | DISPOSITIONED | CONFIRMED | HIL check stays |
| RE-28 | OPEN | TRUE | HIL-RST-1 not run |
| RE-29 | DISPOSITIONED | CONFIRMED | json requests |

## 5. ANSWERS TO THE BRIEF

### (a) RE status

See section 4.
- 17 CLOSED: 11 confirmed outright; 6 with residuals (RE-12, 13, 16, 22, 23, 25).
- 8 OPEN: true as stated.
- 4 DISPOSITIONED: confirmed.

### (b) Independent rebuild and re-run

See section 3, items 2-6. Everything ran under reviewer control:
- test_core;
- S5 (300 runs and 3000 runs);
- S6, S15, S17;
- S12, S13 B-ext, S14, S16 and probe F;
- the FA-1 harness question on all 896 cases with reviewer chain code.

### (c) R2 command hold

**Logic and interface.** Correct as designed (section 3, items 7-8).

**S17 limits.** The json limits text (l.1982) is honest, but it misses three things:
- the dependence on Pc-loss onset, frame phase and frame noise (R2-01);
- the single-frame end of the hold (R2-02);
- the starve threshold (R2-16).

### (d) electronics.json v3

**Consistent with:**
- config.h (154/154);
- 186 (2);
- 194 (4) and 194 (7).

**Not folded.** v3 predates lines 203, 205 and 208, so it does not include:
- the 2.55 s cap;
- the non-sticky over-range bit;
- RE-12;
- the transducer reselection;
- the R2 v2 windows.

**Stale or wrong:**
- l.2035 (R2-07);
- l.4914, the 72 ms (R2-15).

**Citations.** config.h cites the datasheet as 06/2026 and the json as 08/2018 (R2-17).

### (e) The 194 answers

**070BG.**
- Proof is 2× rated: 140 bar g = 141.0 bar abs. Burst is 5× rated, ≤ 20 kpsi [DATASHEET 08/2018].
- Operating range −40 to 125 °C (cable 105 °C); compensated range −20 to 85 °C.
- TEB ±1.5 % FS; accuracy ±0.25 % FS BFSL.
- Over-range output, saturation, recovery and post-over-range shift: MISSING. This agrees with the author and with 203 (2).
- Rise time for the voltage output: TO-VERIFY (R2-17).
- For flight, these items are superseded by line 205.

**113B22 + NI 9234.**
- Sensitivity is 14.5 mV/bar (5 V / 344.75 bar) [DATASHEET as recorded in BOM row 237].
- A 150 bar event needs 2.18 V of swing. On the 14 V upper bias that reaches 16.2 V, below the 19 V compliance [DERIVED].
- PCB's listed 20-30 V excitation against the NI 9234's 19 V compliance stays TO-VERIFY. This agrees with 203 (7). No fallback IEPE conditioner is named yet; that is a v2.11 item.
- Cable capacitance limit at 2 mA: C_max ≈ (I − 1 mA) / (2π f V) ≈ 3.65 nF at 20 kHz and 2.18 V [DERIVED; LITERATURE form of PCB's cable-driving relation, TO-VERIFY]. With ASSUMED 100 pF/m coax that is about 36 m.
- The coating or thermal protection for the flush mount is unspecified (bench plan l.113-130, TO-VERIFY). It is needed before any hot-fire use.

### (f) Line 203 decisions (1) to (7)

**(1)(a): follows.**
- As built, one reading ≥ 4.75 V latches fault::PC_SENSOR and b7 for the whole power cycle (l.1293-1294, l.1664).
- Make only the high over-range non-sticky. Keep the latch for low faults (open or shorted transducer).
- State the R2-hold interaction (R2-23).

**(1)(b): REVISE** (R2-03).

**(2): follows.**
- The port can reach up to 151.0 bar abs against a 141.0 bar abs proof.
- The line model is ASSUMED and hits its floor in 640 of 896 cases. The design change therefore rests on the period argument, not on the peak value.
- Superseded by line 205.

**(3): REVISE** (R2-05).

**(4): follows.**
- S12 reproduces byte-identically: V1 stuck open with V2 closed is undetected on the stand and detected 5.05 s late in flight (104 g).
- A v2.11 detection within 0.5 s, or an FMEA residual, is the right fork.

**(5): REVISE** (R2-04).

**(6): follows.**
- S6 shows small-amplitude jams below the SIL bound go undetected.
- A test-based bound plus GNC's landing check is the appropriate closure.

**(7): follows.**
- See R2-22.
- The 113B22 TO-VERIFY agrees with (e).
- The ECU guard for an unpurged relight is v2.11 work, not reviewable here.

**RE-12 recommendation: ACCEPT** the flight extension of the A7 high-side blank (E2 to E2 + 0.45 s) as DESIGN.

Conditions:
1. Correct config.h l.369-372.
2. electronics.json states the flight blind window. It also states that the 30 bar abort, the comparator, A3 and the A7 low side stay armed.
3. The FC owner confirms that no launch-commit or relight decision uses the A7 high-side flag before E2 + 0.45 s.
4. Extend test v210-2 (test_v210.inc l.18-43). It already shows a quiet blank and a flag after it. It should also assert that pc_commit_valid (d6 b7) stays 1 through the blanked pool excursion and drops after a post-blank flag.

Rationale:
- Without the extension, the pool sets fault::PC_SENSOR through the A7 flag (l.274):
  - the pool holds Pc above 6.9 bar abs for up to 0.30-0.41 s (Combustion);
  - before the blank, 47 % of lit starts tripped in the S15 smoke test (config.h l.378-380).
- That flag latches d6 b7 = 0 for the power cycle (l.1664, l.804). The result is a pad NO-GO and a spent once-per-burn flag.
- In that window the high side cannot tell a high-reading sensor from the pool. Blanking it removes no detection that the window could give.
- Genuine over-pressure stays covered by the 30 bar abort and the comparator.

### (g) Bench plan v3

**Not executable by the founders as written** (R2-06). Every step depends on something that does not exist yet:
- the layout;
- the ECU board;
- the HAL;
- the valves;
- the FC software;
- the rigs.

**Executable now:**
- the RFQs (delivered to DK-6400, no price entered);
- the TE, PCB and NI inquiries;
- the anemometer;
- the spare-070BG over-range row on a bench DAQ, keeping the media separate (R2-14).

## 6. CHECKPOINT

**Claim.**
- Under reviewer control, the Electronics v2.10 SIL record reproduces byte-identically. The author's RE statuses are truthful.
- Six MAJOR findings bear on:
  - the S17 claim at the W10 < 6 m/s bound;
  - the hold's dependence on a single frame;
  - line 203 items (1)(b), (3) and (5);
  - founder execution of bench plan v3.
- Verdict: REVISE, with 0 BLOCKING.
- Not physical approval.

**Configuration.** As in section 1:
- the v2.10 hub tree, verified 502/502 and 406/406;
- binaries equal to MANIFEST_v1;
- reviewer probe binary sil_r2probe c693581c1f6a49ee, built from generated source 03e51dd2d5c3f85b (make_probe.py applied to sil_main.cpp 094a479ab676f75b).

**Sources.**
- **Hub files:** as listed in section 1, plus:
  - S6_aborts.json 693b3ea2b5f9bb9a;
  - S17_r2hold.json c125095719fa563a;
  - S5_mc.json 38c5d831b4081a11;
  - fa1_overrange_v2p10.json f2b07a3d780a289c;
  - fa1_overrange_v2p10_cases.csv cd96ad39a0f8fb29;
  - bleed_driver_v1.json 298b405b0621acd5;
  - bom_v2p2.csv 75723fd39be88c20;
  - bench_plan_v3.md aa82f280feeeee4c;
  - fa1_envelope_v2p4a.json 64b328150025fa1e;
  - MANIFEST_v1.json 6d1dd43ddeeba0d7.
- **CHANGELOG lines:** 164, 166, 172, 175, 181, 186, 194, 195-201, 203 and 204. Lines 205 and 208 as context.
- **Datasheet:** TE M3200 08/2018 (farnell 3007269.pdf) [DATASHEET].
- **PCB and NI values:** as recorded in BOM rows 237-238; not re-fetched.

**Files in /home/claude/work/shared-fallback/engine/reviews/electronics/r2/** (sha256/16):

Manifest:

| File | sha256/16 |
|---|---|
| MANIFEST_REV-ELEC-2.sha256 (55 entries) | ecb1045f348efec9 |

Scripts:

| File | sha256/16 |
|---|---|
| scripts/fa1/rev_fa1_chain.py | ae63293e629d68d6 |
| scripts/fa1/compare_author.py | df98d1425b6adca9 |
| scripts/fa1/rev_inwindow_probe.py | c2deae4ad4fd80f6 |
| scripts/fa1/rev_fa1_tau_sens.py | d2dd7394fa0b2b41 |
| scripts/r2probe/make_probe.py | 4732ed089cfcbc55 |
| scripts/r2probe/summarize_probe.py | d1b9d2374724b95c |
| scripts/s5/s5_tail.py | 62543dd4b552e041 |
| scripts/s5/mcone_extract.py | fbc172968849d33c |
| scripts/json/xcheck_json_cfg.py | 8d1938898775dd2e |
| scripts/json/dump_cfg.cpp | d9274fbc88ab01af |
| scripts/json/gen_dump.py | e1d3d6369555d18d |
| scripts/run_sil_set.sh | 679bc94d70e07b1d |
| scripts/run_after_mc.sh | 3df0c5307206fe56 |
| scripts/compare_rerun_vs_record.sh | d0a452446c1331f7 |

Logs:

| File | sha256/16 |
|---|---|
| logs/test_core/test_core_stdout.txt | 0c9bb4454b5ad856 |
| logs/build/build_test_core_nohooks.log | 63a6905d802eb817 |
| logs/build/reviewer_binaries.sha256 | f85984b92d53a58b |
| logs/sil_rerun/compare_rerun_vs_record_log.txt | 5216b9ccf13b1afa |
| logs/sil_rerun/rerun_traces_not_in_record.sha256 | 1b2b8005819a21e4 |
| logs/s5_mc3000/S5_mc_3000runs.csv.xz (uncompressed b79b6403380f8f7f) | bd7bcaaef71e00a7 |
| logs/s5_mc3000/s5_tail_log.txt | 37135f12da6d8802 |
| logs/r2probe/probe_stdout.txt.xz (uncompressed f4026dcc00964c15) | d138bd4cc9919d45 |
| logs/r2probe/probe_summary.txt | 84f082c9245bd3f7 |
| logs/r2probe/sanity_vs_rerun.sha256 | cd09ffc1109c47d8 |
| logs/fa1/rev_fa1_summary.json | 1be46afb589e01e5 |
| logs/fa1/compare_author_log.txt | c6aabd037a0ec4fd |
| logs/fa1/rev_fa1_cases.csv.xz (uncompressed 2c3233bb86722174) | 6519c21cf1d72cb1 |
| logs/inwindow/rev_inwindow_probe.json | 2acbf1a23ceae9e2 |
| logs/tau/run_log.txt | 56a1a58b035d66b9 |
| logs/mcone/extract_run125.txt | 922b2db1e6d17f1f |
| logs/mcone/extract_run127.txt | 7840137143dd8dcf |
| logs/json/xcheck_json_cfg_log.txt | 67e3f0e6930778eb |
| logs/hub_inputs_reviewed.sha256 | c59c4daeec90acb7 |
| logs/diff/v2p9_to_v2p10_diffs.tar.xz | f0c13fd37deaa111 |

**Tests.** None of these is a physical test.
1. Hash checks of the hub lists and of every input.
2. Rebuild of sil, sil_bpc1 and test_core; binaries equal to MANIFEST_v1.
3. No-hooks test_core build: FAILS at test_v210.inc:157. This is evidence for R2-08.
4. test_core: 309 passed, 0 failed.
5. SIL re-runs of S17, S6, S15, S5 (300), probe F, S14, S16, S12 and S13 B-ext in both builds: 22 outputs identical, 0 different.
6. S5 extended to 3000 runs (wall time 2214.6 s).
7. R2 probe: the sanity build is identical; 575 cases (A 40, B 110, C 400, D 22, E 3).
8. FA-1 reviewer chain: 896 cases × 18 configurations, and a per-case comparison with the author's 14336 rows.
9. In-window probe: 6 synthetic events × 3 detector sets.
10. tau sensitivity at 0.9 and 1.36 ms.
11. Runs 125 and 127, with mechanism extraction.
12. json/config.h cross-check: 154 entries, 0 mismatches.
13. Code reading at every cited line, and the v2.9 to v2.10 diffs of 15 files.

**Unknowns.**

GNC and the FC:
- GNC R2 v2: counting start, estimator, noise content of d_app, and the 0.5/0.8 s windows [MISSING].
- FC flight software: DROGUE reports, echo check, resend [MISSING].

Purge and valves:
- Bleed valve selection, measured open/close times, and mass flow (B-BLEED-1, CF-4) [MISSING].

Transducers and the stand channel:
- 070BG saturation, recovery and post-over-range shift [MISSING].
- 070BG voltage-output response [TO-VERIFY].
- Data for the line-205 replacement transducer [MISSING].
- 113B22: excitation at 19 V, coating, cable length [TO-VERIFY].

Mechanical:
- LC-TB70 as a pressure-time envelope [TO-VERIFY].

Models and inputs:
- The S5 T_tank0 and sensor-error dispersions [ASSUMED].
- The SIL plant and the stand-in FC are models on ASSUMED/COMB inputs.
- Sense-line FA-1 configurations: not rebuilt.
- Teensy (no-hooks) behaviour: by inspection only.

Not delivered:
- KiCad v2.5 beyond json l.3005-3012;
- the HAL;
- the layout;
- the power budget.

**Reviewer corrections made during this review** (kept as evidence):
1. A draft BLOCKING on the purge cap used 29.77 g/s and ignored the +0.05 s valve-time term. I withdrew it after reading hbFlowEnd and bleed_driver_v1.json; it is now R2-05 (MAJOR).
2. A draft note that refuse codes overflow d6 was wrong: b0-b5 holds 0-63. Withdrawn.
3. A draft tally of 44/100 for "no hold, 500 N" was a transcription error. The log shows 100/100.

**Next closure.**
1. **Electronics v2.11** (takes this as a delta):
   - R2-02: the backstop and its test;
   - R2-05: the ECU cap in measured-time form;
   - R2-07, R2-12, R2-15, R2-20: text corrections;
   - R2-08: a no-hooks test_core;
   - R2-09: the S6 disclosure;
   - R2-10: S5 statistics;
   - R2-01 and R2-16: the S17 sweep;
   - electronics.json v4 folding lines 203, 205 and 208;
   - RE-12 conditions 1-4;
   - a new FA-1 chain for the line-205 transducer.
2. **Lead:**
   - restate 203 (1)(b), 203 (3) or 166 (3), and 203 (5);
   - decide RE-12 (recommendation: ACCEPT with conditions);
   - decide the cold-side margin (R2-11).
3. **GNC:** R2 counting start, the noise basis, and the starve threshold at the R2 v2 windows.
4. **FC owner:** the DROGUE 0 resend rule.
5. **Mechanical:** LC-TB70 in pressure-time form.
6. **Combustion v2.4b:** one purge flow basis.
7. **Founders:** the R2-06 list. Nothing else in bench plan v3 can start yet.
8. **Review:** REV-ELEC-3, a delta review of the v2.11 handback.
