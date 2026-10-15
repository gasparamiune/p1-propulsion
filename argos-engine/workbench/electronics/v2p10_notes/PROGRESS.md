# v2.10 PROGRESS (Electronics, successor session 2026-10-13)
Resume rule: read this file first, then HANDOFF-v2.10-from-prior-session.md. Do not cat large files.

## 0. Setup
- Baseline: workdir firmware == hub 06-electronics/firmware v2.9 (engine_ecu.cpp dbe1a756c4b77d37, config.h 0ba1e1ef0fbce180).
- Snapshot of v2.9 (for diff + hub archive later): /home/claude/work/electronics/scratch/v2p9_baseline/{src,sil,tools,Makefile,make_interface_json_v2.py}
  (make_interface_json_v2.py snapshot already contains the prior session's unrun lookup fix).
- Next: item 1 (A5 delete), item 2 (30 bar persistence), item 4 (b7 filtered-only).

## Items 1 + 4 (code done, test_core 288/0 at this point)
- config.h ~301-313: A5 consts deleted -> kLightSpikeLoAbs_Pa 8 bar, kLightSpikeHiAbs_Pa (=30 bar abort), kLightSpikeWin_s 0.45 s; A7 comment
  (HOLD has no high side; v2.10 flight-flag note for item 3); static_assert now A7 top (6.9) < 8 bar log level < 30 bar abort.
- engine_ecu.cpp: monitors() A5 block replaced by comment; riseTrack: rise_f_now_ (filtered only) drives RISE_HELD/RISE_HELD_T (b6/b7),
  b5 stays filtered AND raw; new lightSpikeTrack() (after riseTrack in step()); ls_ reset in init + IGNITION entry; pc_map_now_ stored in
  startMonitors; out.light_spike / light_spike_event; fillLog v11.
- engine_ecu.h: rise_f_now_, pc_map_now_, ls_, ls_event_, ls_t_pk_*; p_ihold_ removed; accessor lightSpike().
- types.h: struct LightSpikeRec (before a7:: block), Outputs light_spike + light_spike_event.
- protocol.h: evt::LIGHT_SPIKE 0x20 + lightSpikeArg(); LogRecord v11 = 167 B (ls_* fields).
- tests: test_v28 (19)(b) rewritten (no abort, record checked), (19)(c) new (3 ms raw 40 bar: no 30 bar abort, filtered channel);
  test_v29 (10) uses kLightSpikeLoAbs_Pa; (26) rewritten (3 ms dip keeps hold; 12 ms dip clears; 30 ms trips A3 - finding);
  log version checks 10 -> 11; size check 167; fmtv() variadic helper added in test_core.cpp.
- Item 2 finding: monitors() pc_abs = pc_f_ + pamb = FILTERED (LowPass2 2nd-order 50 Hz, engine_ecu.h:224). Keep 3 ms. Evidence still
  to produce: harness on COMB traces (late_light_spike_v2p4.json 'traces', 6 traces) through SenseLine + xdcr lag + 4:1 avg + LowPass2
  + comparator RC; also checks the 4.75 V HARD_START (step() IGNITION, ~line 1190 now).
- Next: item 2 harness (scratch/v2p10/spike_chain.cpp), then item 3/5 tests + SIL cases.

## Item 2 evidence (done; keep 3 ms filtered)
- calc/v2p10/extract_spike_traces.py (COMB traces -> scratch/v2p10/traces), calc/v2p10/spike_chain.cpp (build: g++ ... -Isrc/core -Isil
  ../calc/v2p10/spike_chain.cpp sil/plant.cpp -> build/spike_chain). Results: results/spike_chain_v2p10.json (+ _noline.json sensitivity).
- With the SIL sense line: A1 traces raw peak 54.5 bar, filtered 23.4 bar, raw >30 bar 4 ms, filtered 0 ms; 43.7 bar scaled bound:
  raw 63.3, filt 27.0, raw >30 bar 5 ms -> a RAW 5 ms persistence would sit at the trip edge; filtered 3 ms has 3 bar margin. Comparator
  max 1.85 V vs 2.30 V nominal / 2.21 V low band: no trip. 4.75 V HARD_START: Vmax 3.56 V (A1), 4.06 V (bound): keep (margin 0.69 V; needs
  sense-line overshoot > 1.73x on 43.7 bar to trip; TO-VERIFY B-PC-1).
- Still to show: S6 throat_blocked comparator first (SIL run).

## SIL so far (results/sil_v2p10, firmware build of this session)
- S14 (new, ./build/sil v210 <out>): sil_main.cpp scV210() + fcRelease() (adopted FC predicate on pc_valid/0xFFFF + interim rule) +
  s14Measure/s14Json; plant.h/.cpp: pool_kg/q/Awet/hvap pool-burn source (mpool, pool_burnt), starve_s/starve_pc_cap_Pa plateau stand-in,
  t_lit_plant; sim.h Rec: pc_valid, ls_flags, mpool. Result: 0 FAIL. Pool replay 16 flight cases: RUN, no abort, OPEN_LOOP 0 ticks,
  Pc invalid 0 ticks, A7 START flag at +50..+177 ms (flag only), FC release Pc branch at E2. Stand pad pool: PC_SENSOR abort at 1.736 s
  (A7 START high side, nuisance, kept). Pc invalid at E2+20 ms (flight, starved plateau stand-in 2.6 bar cap): RUN open loop, no A7,
  b4 with 0xFFFF 1291 ticks, b7 never, FC interim release E2+101 ms (branch 3). Stand: PC_SENSOR +5.0 ms. Reference starved run (no loss)
  -> FLAMEOUT at E2+54 ms (A3; cap stand-in is pessimistic: lift-independent plateau) = observation, not a v2.10 change.
- S6 (./build/sil aborts): late lights 0.20/0.25 s PASS (no abort; plant 26.9/28.6 bar) -> OI-A5-LATE closes; throat_blocked_70pct_500N_24C
  HW_OVERPRESSURE at +8 ms (comparator first, unchanged); remaining FAIL lines = 3 pre-existing (gimbal_jam_moving_cmd, 2 x throat 500N MEOP).
- Next: test_v210.inc (items 3/5 unit tests), then item 6 purge/bleed.

## Items 3 + 5 (done)
- sil/test_v210.inc (included at the end of the test_v29.inc block; Makefile dep added): (v210-1) LIGHT_SPIKE unlit exit + EVENT arg + log v11;
  (v210-2) item 3 flight A7 START flag: no OPEN_LOOP, pc_valid, TLM ok; (v210-3) item 5 Pc invalid at E2+20 ms: RUN open loop, A3/A7
  suspended, d1 RUN + b4 with 0xFFFF, b5-b7 clear; stand PC_SENSOR 5 ms. test_core 291/0.
- Answers: pc_sensor_ok_ has ONE assignment (engine_ecu.cpp step(): 0.25 V < pc_raw_V < 4.75 V). Excitation window (xdcr::excitationOk,
  kXdcrExcMin/Max_V) NOT wired into the core (HAL not written) -> finding/open item. A7 trip sets fault BIT PC_SENSOR only (+ a7_flag_ in
  flight), never pc_sensor_ok_. OPEN_LOOP and 0xFFFF follow pc_sensor_ok_ only -> no blanking needed for item 3.
- Next: item 6 (purge cap, closure-not-confirmed proceeds, hardware inhibit, valve candidates, BOM, drive), item 7 flow split.

## Scope update (CHANGELOG 164) received; item 6 + FA-1 plan
- Purge: PURGE cmd at E0-2.90 s (FC). Tp = FLOW time (both valves open -> both closed), flow end <= E0-0.05 s; close cmd leads by measured
  closing time (S12 77 ms). ECU hard cap = 2.5 s flow + measured open + close times. Never commit relight before complete purge; ECU reports
  achieved flow time; FC delays T_fire if flow < 1.9 s; ECU never truncates. Closure signal defined exactly; unconfirmed -> relight proceeds
  + BLEED_FAULT to FC. FA-1: E1 only on P_torch AND photodiode (2oo2); E1->E2 both no-flame >= 5 ms -> close pintle + MV; lift never before E1;
  photodiode absent from v2.9 design (grep ecu_design.py/types.h/config.h: none) -> add sensor, conditioning, BOM row TO-QUOTE.
  Valve mass target <= 0.15 kg each (Mechanical holds 2 x 0.30 kg risk). Bleed path: 2 x 0.707 mm restrictors + inline element FD-01, no check.
- Next: config.h bleed block + PURGE/hbleedStep rework, then FA-1 torch gate, then hardware (inhibit + photodiode), valves, BOM.

## REV-ELEC-1 received (coordinator, verdict REVISE); hub hold RELEASED for v2.10 with condition: archive the v2.9 tree to
## hub/06-electronics/archive/v2.9/ (copy, verify hashes, then replace). Review hub/reviews/REVIEW-ELECTRONICS.md 471d830c8d00dd85.
- Lead calls: RE-01 (A5 deleted: done; disperse spike gain + ign delay in SIL), RE-02 (P0 high side keep measured + BASE_HIGH, pad/stand
  refuse lift PC_SENSOR, A1 relight proceeds; P0 low side := 0; S13 B extension), RE-03 (done; check raw-dip test), RE-04 (lift clamp to map
  lift at current setpoint + margin while the reference travels; target p99.9 <= 28 bar abs, 0 PC_OVERPRESSURE in S5 300 + probe F 11),
  RE-05 (E1 = 2oo2 AND [closure confirmed OR deadline <= torch gate]; flight proceeds + BLEED_FAULT + V2 closed; stand abort; FC PURGE_EN
  ANDed + one-shot = cap; V1 off the heater pin or AND-gated; delete open-valve hold; new valve item 208; P&H + fast release + TVS),
  RE-20 (30 bar filtered, 5 ms), RE-07, RE-08, RE-12, RE-28, RE-06, RE-09..RE-25 per review.
- In progress before the review: config.h purge/bleed block rewritten for CHANGELOG 164 (flow-time schedule, fill step, vent + hold-test
  closure, cap) and FA-1 constants added (photodiode, TORCH_LOST). Firmware code for these NOT yet written.
- Coordinator add-on (REV-GNC-2, CHANGELOG 168): (1) drogue predicate RELEASE iff RUN AND b4 AND [(Pc valid AND >= 300 kPa) OR b7 OR
  (0xFFFF AND t >= t_E2 + 0.10 s)], latched, t_E2 from EVENT 0x120; b7 only on a VALID filtered channel; spec + tests for Pc invalid
  before E2 / inside [E2, E2+0.10] / after; EVENT 0x120 must carry t_E2 usable by the FC. (2) photodiode as non-Pc flame-out indicator
  in RUN (FLAMEOUT_OPT when Pc invalid) or say why not; FOV, saturation, main-chamber view. (3) N5: electronics.json v3 must carry
  actuators.tvc_A.dynamics_for_GNC, engine_side_at_n7_7V4, hinge_moment_assumed_Nm (v1 names) or confirm v1 values (wn 94.2 ASSUMED,
  zeta 0.7, 4.5 ms). (4) OI-GNC-V3: planning keys at requirements.ignition.relight_planning_value_s.* written by the generator.

## Item 6 firmware + FA-1 + RE-05 + RE-18 + REV-GNC-2 (1)(2) (done in firmware; tests 297/0)
- config.h head-end bleed block rewritten: kPurgeRelight_s 2.90 (PURGE -> E0), kPurgeFlow_s 2.5, kPurgeFlowMin_s 1.9 (FC floor, reported),
  kPurgeFlowEndLead_s 0.05, kHbleedOpenTime_s 0.030 / kHbleedCloseTime_s 0.080 (ASSUMED datasheet-class, S12 77 ms), kPurgeFlowStart_s 0.35
  DERIVED, kHbleedCap_s 2.61, kHbleedVentMax_s 0.03, kHbleedHoldTest_s 0.10, kPurgeHoldMax_s 0.50 (bleed CLOSED), closure description.
- engine_ecu.cpp: enterPurge fill step (V1 only), hbFlowEnd (flow accounting, PURGE_FLOW event), hbClose, hbCloseResult (CONFIRMED iff chain
  proven + vent + hold test; NOT CONFIRMED -> fault MV + bleed_fault flag + EV_NOT_CLOSED; stand abort), hbleedStep (path proof, cap, vent,
  hold test), PURGE schedule (V2 at 0.32 s, V1 close at 2.77 s, IGNITION at flow end + 0.05 s, never truncated, hold expires +0.5 s),
  IGNITION: E1 = 2oo2 AND closure step ended (deadline = kTorchGate_s), supervision both-dark 5 ms -> TORCH_LOST (Abort 29), lift guard.
  FLAMEOUT_OPT (RUN, Pc invalid, view proven 20 ms after torch closed). Propane backstop 3-sample persistence (RE-18). Outputs: hbleed2,
  purge_flow_ms, bleed_fault, fault2 (f2::), fa1, photo, state_event/state_t_ms; EVENT PURGE_FLOW 0x21, FLAGS2 0x22; encodeStateEvent with
  copy index (arg b13-15) for t_E2 on the FC clock. Log v11 now 176 B (hb2, flow ms, fa1, photo mV, dark mV, fault2).
- Tests: test_v29 (16)-(20),(24) rewritten for v2.10 (both P_mid flowing levels 0.95/0.06), test_v210 (v210-4..8): 2oo2, supervision,
  FLAMEOUT_OPT, drogue predicate timing (before E2 / E2+20 ms / E2+150 ms), cap via ECU_SIL_TEST_HOOKS (now also in test_core build).
- Next: RE-20 (5 ms filtered), RE-02, RE-04, RE-07, RE-08, RE-17, RE-19; then SIL photodiode/valve-time model and S11/S12/S5/S6/S13/S14.

## RE-20 + RE-02 (firmware done; tests 297/0)
- RE-20: kPcOverPressureTime_s 0.005 on the FILTERED channel (pc_abs = pc_f_ + ambient). Found + fixed: p_hard_ was reset at IGNITION->RUN,
  so a spike straddling E2 needed 5 more ms; persistence now continues across E2 (enter(): reset only when s != RUN). test_core
  "Pc 40 bar during ignition" -> HARD_START/PC_OVERPRESSURE within 12 ms. S6 trip order to re-run in SIL.
- RE-02 (LEAD CHANGELOG 166): ignDetect PRE_REF one-sided: f0 > +check -> measured P0 kept + f2::BASE_HIGH (FLAGS2 EVENT to FC);
  f0 < -check -> P0 := 0 + BASE_AMB; lift refusal PC_SENSOR when (stand || !lit_since_boot) && baseHighNow() at the lift tick.
  test_v29 (2) and (5) rewritten (pad refusal at E0+34 ms, -0.8 -> BASE_AMB -> A7 HOLD PC_SENSOR, A1 +0.95 bar proceeds on measured P0,
  +0.75 over P0 no light, +1.6 -> RUN). S13 B extension (both builds, pad/A1, lit/unlit, -0.8..+1.2 step 0.05) still TO RUN.
- Noted conflict to report: lead's S13 B pass "every lit start reaches RUN" cannot hold for pad offsets > +check (refused by the same
  decision) nor for < -check (unchanged PC_SENSOR path); also torch gate (main Pc < 1.0 bar g) blocks torch confirmation at A1 for
  offsets >= +1.0 bar -> TORCH_FAULT expected. Report classes separately.

## RE-04, RE-07, RE-08, RE-17 firmware + SIL photodiode model (tests 301/0)
- SIL sim.cpp/h: FA-1 photodiode head model (ASSUMED levels: dark 0.10 V, torch +1.0 V, main +2.0 V, sat 4.95 V, noise 5 mV, rng3_),
  fault hooks photo_fail_at / photo_dark_from, tc_invalid_at[2]; CSV appends pc_valid, ls_flags, mpool, photo_V, fa1, fault2, hbleed2,
  purge_flow_ms. New scenario `sil probef <out>` (RE-04 probe-F replay, S5_probeF.json).
- RE-04: PcController travel clamp: travel = ref model outside settle tol OR pintle not arrived (encoder valid, |cmd - enc| > 0.10 mm);
  during travel u <= (1+trim) * map(sp_active + kLiftClampMarginPc_Pa = 1.0 bar); integrator held during pintle travel. Finding kept:
  ref-only travel (first try, margin 2 bar) left 29.8 bar abs (integrator wound 0.02 -> 0.72 mm while the pintle lagged ~1 mm).
  Scratch A/B (pre-RE-11 S5, 300 runs): plant Pc max 27.18 bar abs (v2.9 30.01), p95 26.33 (29.33), PC_OVERPRESSURE 0 (1), ENG-03
  req 0.91 / target 0.4167 unchanged, up-rise p95 0.122 s unchanged; probe-F 11 runs worst 27.14 bar abs, 0 aborts.
  Final S5 record to be re-run with RE-11 dispersions. Unit test (v210-12).
- RE-07: rolling second re-zero (consecutive 0.2 s quiet blocks after the first), applied at PURGE / RELIGHT in COAST before the vented
  check if block ended <= 0.5 s before, span <= 0.05 bar, <= 0.30 bar from pad zero (f2 REZERO2 / REZERO2_REJ). NOT_VENTED: stand + pad
  first start refusal; flight = f2::NOT_VENTED flag + proceed (also PREPRESS auto-ignite and PURGE->IGNITION waits via ventGate()).
  test_v29 (13) updated; (v210-9) 20.6 s coast drift cases. NOTE for report: in flight the PURGE->IGNITION no longer waits for a vented
  chamber (lead semantics); a real post-purge chamber pressure would also be flagged, not waited for.
- RE-08: ARM needs both case TCs valid (OVER_TEMP); one invalid -> f2::CASE_TC_DEGRADED; both invalid: stand treated hot (OVER_TEMP via
  0.2 s persistence), flight burn continues, caseHot() -> relight refused CASE_HOT. (v210-10).
- RE-17: kTankIgnMin_K 288.15 K; tank_cold_ = no valid reading OR min(valid walls, Tsat) < 15 C; ARM -> Abort::TANK_COLD (30);
  pad first start / stand -> refuse::TANK_COLD (14); flight relight -> f2::TANK_COLD_RELIGHT flag. (v210-11).

## RE-19, RE-25, RE-11, RE-12 (tests 301/0 at the time)
- RE-19: mvLadderDecode: below the lowest window edge -> short_gnd (invalid); OPEN+CLOSED codes -> both_sw (invalid); Inputs
  mv_sw_conflict (5 ms persistence kMvSwConflictTime_s) -> ARM MV_FAULT; RUN: stand MV_FAULT abort, flight fault MV flag. Pad-BIT
  harness step compares the ladder ratio with ladder::nominalRatio() (kLadderBitTol 0.006): 122 kOhm leak (-0.017) fails, +0.003 passes.
- RE-25: log t_us = fmod(t, 2^32 us) + t_us_wraps byte; tc_dK INT16_MIN when a TC is invalid.
- RE-11: S5/S15 start inputs from a second generator (T_tank0 U(15,24) C, ign delay U(0.05,0.30) s, fast part U(0.2,0.6), pool f_ret
  U(0,1), q U(0.5,2.0) MW/m2, A_wet 0.0204 m2, cap 25 g). All ASSUMED bands, COMB-sourced where stated in sil_main.cpp.
- RE-12: kA7StartHiBlank_s 0.45 s: A7 high side blanked E2..E2+0.45 s in every phase, stand AND flight (DESIGN extension of the lead's
  pre-decision: E3 can come early and the once-per-burn flight flag would be spent). S15 smoke (40 runs, ASSUMED pool distribution):
  without the blank 47 % of stand starts tripped A7; with it LIGHT_SPIKE raw max 34.15 bar abs, filtered 24.65, no 30 bar abort, no
  comparator trip, plant max 25.8 bar abs. To the lead for confirmation (flight extension).

## REV-COMB-2 / lead line 172 additions (coordinator message) - tests 304/0
- (4) Interlock guard band. config.h block: wall threshold 24 C - 0.5625 K = 23.44 C (DS18B20 +/-0.5 K + 12-bit step; wall-vs-bulk
  offset and drift MISSING). P_tank: uncalibrated budget 4.94 bar worst-case linear (TEB 2.550, stability 0.425, LT1761-5 excitation
  2 % read ratiometrically against the ADC reference 1.511, divider 0.113, ADC Zin 0.068, ADC 0.231, ambient 0.04; RSS 3.01) ->
  50.34 bar abs (Tsat 19.8 C). Calibrated (B-PT-1) 0.98 bar -> 54.30 bar abs (Tsat 23.2 C). Runtime EngineEcu::ptank_cal_ok (HAL from
  the B-PT-1 NV record; boot default false). Rigs and SIL default calibrated (campaign configuration); (v210-13) proves both thresholds.
  First try with a compile-time flag broke 10+ rig tests (rigs at 51.01 bar abs) - reverted, kept as the reason for the runtime flag.
  CONSEQUENCE for the lead: until B-PT-1 passes, a pad/stand start needs the tank at or below ~19.8 C by pressure.
  S5 now reports interlock refusals at ARM apart (interlock_refused_at_arm, *_frac_of_armed).
- (1) Safing rule: kRetryVentWait_s 5 s and refuse::VENT_WAIT withdrawn. Ground no-light (stand any start, pad first start; abort in
  IGNITION or NO_IGNITION/TORCH_FAULT/TORCH_LOST/FLAMEOUT) -> lockout + safing hold; CLEAR_LOCKOUT refused (refuse::SAFING_HOLD 15)
  until kNoLightSafingMin_s = 60 + 900 = 960 s after the abort. NvJamRecord b4 (set with b1) restarts the hold at a boot (elapsed time
  unknown); nvLockoutClear clears b1/b2/b4; EVENT SAFING_HOLD 0x23; log v11 + safing_left_s (179 B). Tests: test_core ground no-light
  (full 960 s), test_v28 (14)/(17) updated, (v210-14) scope + NV. The ECU cannot see the N2 flow: its timer is a lower bound only.
- (5) LIGHT_SPIKE lower-bound labels (types.h, config.h, protocol.h). Stand dynamic Pc channel B-DPC-1 for bench plan v3 + BOM:
  PCB 113B24 (DATASHEET TM-PRS-113B-102B-0124: 1 kpsi, >= 500 kHz resonance, <= 1 us rise, -73..+135 C) + NI 9234 (DATASHEET
  374238A-02: 51.2 kS/s/ch, alias-free 0.45 fs = 23.04 kHz, 100 dB stopband at 0.55 fs, IEPE 2.0 mA). Prices TO-QUOTE.

## 2026-10-13 LEAD CHANGELOG 175 (GNC rev2) folded into v2.10
- (1) Drogue rule R2 (FC side): ABORT path confirmed: ID 0x010 ABORT frame (len 5, A5 5A code seq CRC-8, no sequence check) or Cmd::ABORT in CMD_STATE; acted on at the next 1 kHz tick ahead of other commands (doAbort(Abort::CMD)). Effect (SIL S6 fc_abort_command, record pre-175 binary): ABORT same tick, MV holding magnet released that tick, valve closed +39 ms (plant), pintle command 0 at +4 ms, needle seated (<= 20 um) +66 ms, oxidiser flow < 1 % +68 ms, ARM bus off +82 ms; EVENT STATE (ABORT | CMD << 8) x3; log abort_cause CMD. Test (v210-15) proves the same-tick behaviour with Pc invalid in flight RUN. RUN (TLM_FAST d1, 500 Hz) and t_E2 (EVENT STATE 0x120 RUN entry, t_ms) do not depend on Pc validity; b7 stays valid-channel only.
- (4) Launch commit: TLM_RELIGHT d6 b7 = PC_VALID (Outputs::pc_commit_valid = valid this tick AND no latched fault::PC_SENSOR AND no latched PC_SENSOR abort); decoder masks d6 & 0x7F. Interface change.
- (3) TLM_FAST d4-d5 defined as the crank-encoder lift [um] (can::tlmPintle), 0xFFFF = encoder invalid; 500 Hz.
- (3 purge rule) The sequence-integrated purge on a bare RELIGHT is DELETED: a RELIGHT with no PURGE is an unpurged relight (direct or prep path from the line state), never refused or delayed for lack of a purge. test_v29 (17) rewritten; (19)(20)(23) now send PURGE then RELIGHT. SIL 'integrated' cases = FC PURGE at TR + RELIGHT 1 ms later (same E0 7.90 s); S12 adds relight_no_purge_fitted_unpurged_LEAD175 (+ stand).
- S10 stand_start_after_abort updated to the safing hold (CLEAR refused inside 960 s, accepted after; SIL clock skip with the plant frozen, sim.h).
- config.h documents the v2.5 hardware window (LTC6993-1, 3.146 s nominal, >= 3.00 s powered span, static_assert).
- test_core 306/0. Binaries: sil 71489602d1c325af, sil_bpc1 cb6a3c8de996852d, test_core f91218d6e23216f3. Record runs restarted (pre-175 results parked in results/sil_v2p10_pre175, not published).

## 2026-10-13 bleed drive calc v1 (calc/bleed_driver_v1.py, results/bleed_driver_v1.json/.txt)
- RUN (nice 10). Window 3.048-3.243 s covers the 3.000 s powered span (margin 0.048 s) [DERIVED from DATASHEET LTC6993 3.0 % + RSET 0.1 %].
- Mass [DERIVED]: nominal 73.0 g COMB / 78.6 g SIL; firmware cap (2.66 s flow) 77.7 / 83.6 g; hardware bound 96.2 / 103.5 g; limit 76 g [REQ].
  -> CONTRADICTION kept: firmware cap exceeds 76 g on both bases. Cap must be <= 2.553 s (COMB basis) to hold 76 g. Not changed in firmware (lead decision; flag).
- Kv >= 0.112 m3/h [DERIVED, Cd 0.7 ASSUMED]; Burkert 6027 1.5 mm Kv 0.07 [DATASHEET] fails.
- Clamp screen (coil UNKNOWN): Vds pk 42 V < 60 V; TVS energy within single-pulse screen up to 10 mH x 10 A; FET current limit 2 A binds first.

## 2026-10-13 record run complete + manifest (RE-21)
- Run A (build/sil all 300 + test_core) and run B (S13 ignrule 300, sil_bpc1 ignruleb, S15 startmc 300, S14, S16, probeF, S11 fault_path_v4) done.
- vs pre-175 record (results/sil_v2p10_pre175, parked): S1-S9, S13, S14, S15, S16, probeF byte-identical JSON; S10 after-abort case now PASS
  (scenario rewritten with the 960 s safing hold: CLEAR refused inside, accepted after, R2 used; ECU clock skip, plant frozen = SIL simplification);
  S12 +2 LEAD175 cases PASS (bare RELIGHT: E0 on the command tick, RUN +0.187/0.188 s, no bleed flow); S11 drained_prep_seg_bleed_fitted +1 ms
  (PURGE refused PURGE_PATH on an unprimed line, RELIGHT 1 ms later takes the prep path).
- Counts: test_core 306/0; S10 31/0; S12 31/4 (known detection gap); S6 55/3 (known); S9 5/4 (known: spike train PC_SENSOR, 3 TEB); S8 5/0;
  S13 rule 88/0, B-ext lead criteria fail 32/164 (false) and 64/164 (true); S14 20/1 (starved reference FLAMEOUT, known observation); S16 12/0.
- Binaries rebuilt from the current tree into build/chk: sil 71489602d1c325af, sil_bpc1 cb6a3c8de996852d, test_core f91218d6e23216f3 identical
  (config.h edit after the build changed comments/static_assert constants only).
- tools/sil_manifest_v1.py -> v1.2 (--bin, --rebuild, --scenarios, recursive walk). MANIFEST_v1.json record 2d41928db00b02ba, 247 files, 0 unmapped.

## 2026-10-13 hardware label fix + bench plan v3
- Found: make_ecu_kicad.py REV was still 'v2.4' in the first v2.5 generation (title blocks, rev field, pin_map_v2p4.csv on v2.5 content).
  Fixed (REV v2.5, pin map name follows REV); run_all.sh re-run (47 s, nice 10): ERC 0/0, netlist cross-check 0/0, 471 symbols,
  grouped BOM 03f769f49624da81 unchanged; stale pin_map_v2p4.csv removed from the workdir (v2.4 copy stays in the hub v2.9 tree).
  KiCad README.md is still the v2.3 text (also in the hub): update for v2.5 before publishing.
- docs/bench_plan_v3.md written (RE-13): criteria/statistic/instrument per test; new B-PT-1, B-DPC-1, B-SAFE-1, CHK-PW, HAL-1, HIL-RST-1.

## 2026-10-13 header stamps + manifest re-record + electronics.json v3 (item 8, RE-16) + generated-header check
- 19 firmware files: line 1 stamped "// [v2.10 2026-10-13, REV-ELEC-1 + LEAD CHANGELOG 164/166/168/172/175: ...]" (line counts unchanged).
  Rebuild of the stamped tree into build/chk2: sil 71489602d1c325af, sil_bpc1 cb6a3c8de996852d, test_core f91218d6e23216f3 identical.
- First manifest record kept: results/sil_v2p10_MANIFEST_v1_record1_pre_header_stamp.json (9d889c999ab7f539).
  Re-recorded (--overwrite, --rebuild = build/chk2): MANIFEST_v1.json 0354f2576b1cd059, record 7f0b917f961e31a5, tree 255abb6a4172a352,
  39 sources, 247 results, 0 unmapped, 0 in several scenarios; every binary identical to the rebuild; 20 sources edited after the build (stamps + config.h comments).
- calc/make_interface_json_v3.py (4b84023ea29013ae) RUN -> results/electronics_v3.json (38d63aea3906a211): 42 keys, 30 abort causes,
  80 constants quoted, 42 pins, 16 open issues. First run refused by its own abort-matrix check (CHANGELOG line numbers in 3 trigger texts):
  citations moved to a per-cause 'decision' field (CHANGELOG line + marker checked). Three literal '%%' strings fixed before the run.
  GNC planning values now keep their gnc.json tags (option (c) 1.41 s PROVISIONAL). Stale strings appear only in superseded_v2 / self_check.
- calc/v2p10/gen_headers_regen_check.py -> results/gen_headers_regen_check_v2p10.json (fd50e8c6dde750ed) [DERIVED]:
  mechanical.json v2.1 regeneration = comment lines only (values identical). gen_tables.py v3.3 FAILS on combustion.json v2.4
  ("no step matching pintle to the ignition lift": epoch-structured sequence) -> engine_params.h etc. stay v2.3-generated (HISTORICAL).
  Keys read by the generator: only 'igniter' differs v2.3 -> v2.4. Values in use with no v2.4 source text: kStartRamp_Nps 2500 N/s,
  kSparkTrain_s 0.5 s, kPropaneOffPcAbs_Pa 5 bar abs, kTimingOnlyLiftAt_s 0.12 s -> OI-GEN-TABLES + request to Combustion.

## 2026-10-13 LEAD CHANGELOG 181 (REV-GNC-3 decisions) folded into v2.10
- (4) R2 ADOPTED in design, pcf_tmax 0.5 s (0.8 s NOT adopted); pcf_tmax, 37.16 N threshold, baseline reference = FC parameters.
  ECU side: new test_core (v210-16): Pc lost at E2 + 5/10 ms in flight RUN, FC ABORT frame at t_E2 + 0.5 s and + 0.8 s ->
  ECU stays RUN (0 non-RUN ticks, Pc 0xFFFF, E2 kept, PC_VALID clear) until the frame, ABORT/CMD on that tick, pintle 0 at +4 ms; 4/4 PASS.
  test_core 307/0 (5d3df53c03519876); the 306 previous lines byte-identical. sil/sil_bpc1 unchanged (71489602d1c325af / cb6a3c8de996852d,
  rebuild build/chk3 identical). results/sil_v2p10/test_core_log.txt re-run; manifest record 2 kept as
  results/sil_v2p10_MANIFEST_v1_record2_pre_181_test.json; re-recorded: MANIFEST_v1.json e1362cae9b962adb, record 0ecd82224385f11f, tree 755cb469fef8dd56.
- (2) PURGE commit: iff lead to the plain relight trigger >= L* (FC parameter, 1.7 s interim, 1.3 s if HI). FC-side; ECU unchanged
  (firmware comments quote the interim 1.7 s). The withdrawn T_fire-delay basis is not repeated anywhere in the v2.10 outputs.
- (3) FC_THRUST NOT armed on A1 (FC keeps the valid flag clear); ECU detector structure stated (3 consecutive fresh valid frames > 650 N,
  no window/hold, reset on any frame <= threshold / invalid / gap > 50 ms / leaving RUN). Not the windowed RG-16 form: GNC budgets it.
- (3) A1 FMEA row recorded in electronics.json v3 fmea_rows_a1: no over-thrust detector after an in-flight Pc loss.
- (6) A1 pad go/no-go list (wind HARD rule, Pc VALID, bleed closure, ECU armed, purge window) in bench plan v3 and electronics.json v3.
  Found while writing it: TLM_RELIGHT d6 reads NOT_COAST (10) on the pad by design (not an ARM refusal); the pad BIT runs in PREPRESS,
  after the launch commit, so the bleed item is "closed + drivers inhibited + no flag" at the commit and the BIT aborts in sequence.
- (10) purge masses labelled VENTED N2O (tank liquid depletion 81.6 g): calc/bleed_driver_v1.py re-run, numbers unchanged
  (results/bleed_driver_v1.json 298b405b0621acd5); bench plan B-BLEED-1 rows; OI-PURGE-CAP.
- bench plan v3: B-FC-1 R2 row corrected (it said ABORT at t_E2 + 0.8 s; now pcf_tmax 0.5 s, FC parameter, SIM v210-16).
- electronics.json v3 regenerated: a3f1dc292bef2cfb, 44 keys, 17 open issues (+ OI-A1-PCLOSS-OVERTHRUST ACCEPTED FMEA record).

## 2026-10-13 author's adversarial diff v2.9 (hub) -> v2.10 (src/core) + comment fix + final manifest
- Baseline scratch/v2p9_baseline == hub 06-electronics/firmware (diff -rq clean). Read the full engine_ecu.cpp, control.cpp, protocol.cpp,
  sensor_scale.cpp diffs. Findings: (F1) two comments in engine_ecu.cpp still said the 30 bar abort persists 3 ms (constant is 5 ms
  since RE-20): FIXED (comment-only). (F2) EVENT STATE arg carries the abort cause in 5 bits (0-31): TANK_COLD = 30 is the last code
  that fits one more (31); a 32nd cause needs a frame change. (F3) the safing hold also opens on an IGNITION-state HARD_START on the
  ground (conservative side). (F4) log photo_dark_mV = 0 before the first valid photodiode sample (no separate invalid marker).
  No logic defect found. This is the author's review, not an independent one.
- Rebuild build/chk4 after the comment fix: sil 71489602d1c325af, sil_bpc1 cb6a3c8de996852d, test_core 5d3df53c03519876 identical;
  ARM objects identical (engine_ecu.o 60b592543ca2e3a7), 93 warnings (unchanged).
- Manifest record 3 kept (results/sil_v2p10_MANIFEST_v1_record3_pre_comment_fix.json). Final: MANIFEST_v1.json b19a8fb2028eed92,
  record 5ee7e91c87ae908d, tree d94fd22d4444934f, 247 results, 0 unmapped, test_core 307/0.
- electronics.json v3 regenerated on the final manifest: c4991a1eedbd0378.

## 2026-10-13 manifest tool v1.3 (FAIL-line undercount found) + final record
- Found while writing the report: tool v1.0-v1.2 kept only run-log lines ENDING in "FAIL"; the S12 table prints FAIL in a column,
  so every v2.x manifest under-listed failures (v2.10: 7 listed, 11 failed: + 4 S12 stuck-open cases). v1.3 adds a status-token scan
  over all scenario logs (sil_fail_lines_v13, sil_fail_count_v13 = 11); the v1.2 field is kept for continuity. Earlier hub manifests
  checked with the v1.3 rule on their hub run logs: sil_v2p8_2 4/4, sil_v2p8_3 4/4, sil_v2p9 8/8 -> no undercount there (the S12
  column format is new in v2.10). [Correction: this note first said they "carry the same undercount" before the check was run.]
- Record 4 kept (results/sil_v2p10_MANIFEST_v1_record4_tool_v1p2.json). Final MANIFEST_v1.json 6bec91895f01fd9f:
  record 90ca7ff46ba0da82, tree 1acdfd8c35bac705 (the tool is part of the tree), binaries unchanged and identical to build/chk4.
- electronics.json v3 regenerated: f321113742a1ddaf; firmware.sil_record_v2p10.fail_count 11 with the lines.

## 2026-10-13 combustion.json v2.4a folded into electronics.json v3 (no firmware change)
- Source: hub interfaces/combustion.json v2.4a (7d1cef9b912eef4d); 02-combustion/data/v2p4a/unpurged_start_check_v2p4a.json (4c745dcfbf09aef7, hash cross-checked by the generator against the combustion entry; it exits if the finding text changes).
- Finding (Combustion, SIM on ASSUMED delays + DERIVED line states, not physical): purge_commit_rule_v2p4a calls the unpurged branch REFUTED as written. LO worst line state: light inside the first liquid slug, vapour gap after E2, drogue-release term already true, A3 after the release in 0.712 of starts (0.8191 lined); A3 ratio in the gap <= 0.24 vs 0.40.
- ECU v2.10 still implements LEAD 175 (3) (unpurged RELIGHT accepted). Not changed: the LEAD decides (Combustion proposal: no relight on that pass, or a ride-through mode). New OI-UNPURGED-RELIGHT (HIGH) and relight_interface.unpurged_relight_contest; LEAD request extended.
- Contradiction kept: Combustion's latency model takes E2 as Pc > 3 bar abs (withdrawn, LEAD 134); the ECU flight E2 is the relative rule. Timing of the relative E2 against the gap: checked by neither side (MISSING).
- SIL limit: plant.cpp models one vapour plug ahead of the liquid (v2.7 C7), not slug/void alternation; the SIL cannot show the gap. No SIL claim made.
- Stale cross-discipline entries in combustion v2.4a, sent as a Combustion request: "Electronics E0 + 0.15 s" closure deadline (start[0], A14, cf4_gate pass_criteria[5]; ECU v2.10 = torch gate E0 + 0.16 s, engine_ecu.cpp closure-deadline branch); drogue_release_hold note t_E2 + 0.8 s (LEAD 181 (4): 0.5 s); rule_LEAD_175_3 to be restated per LEAD 181 (2).
- Generator fixes: the OI-GEN-TABLES request names the current combustion version (was hard-coded "v2.4"); a request cited "LEAD 181 (1)" for pcf_tmax, corrected to 181 (4) before publication (CHANGELOG item numbers differ from the coordinator's list).
- Bench plan v3 B-FC-1 "Unpurged RELIGHT" row: CONTESTED note (ECU command behaviour only; not evidence that an unpurged start is safe).
- electronics_v3.json regenerated: 44 keys, 30 causes, 80 constants, 42 pins, 18 open issues; sha256/16 4310eddfa2a21e90. Scans: withdrawn basis text 0, "v2.4 source text" 0, "181 (1)" 0; stale-string check PASS.

## 2026-10-13 pre-publication checks: ECU values re-run, S5/S15 unclassified runs probe, S12 text
- calc/ecu_v2p3_values_v1.py re-run on the v2.5 design (ecu_design.py b0aed1b5043d07d4): CHECKS FAILED none; only change +5V_SNS budget 4 -> 6
  transducers (30 mA of 100 mA). results/ecu_v2p3_values_v1.json d3f10bb0868cfe59 (old workdir copy, never in the hub, kept in scratch).
  The hub v2.9 KiCad README referenced this result but the hub had no copy: published with v2.10.
- Found while collecting counts: S5 has 241 no-abort runs but 239 lit; runs 125/127 (T_tank0 15.06/15.03 C) end ARMED with no abort.
  Probe (scratch copy + one printf; record binary untouched): IGNITE refused TANK_COLD (14) after a successful ARM; PREPRESS held until the
  profile SHUTDOWN. Mechanism of the crossing not isolated. Evidence: results/sil_v2p10_probe_s5_unclassified_runs.txt (eef5aecc196b67d7).
  OI-GUARD-BAND extended. SIL summary accounting gap (neither interlock nor abort), no firmware change.
- S12 first-burn disposition text corrected: the fail is the leak flag 5.05 s after injection (criterion < 0.5 s), 104 g through the bleed.
- electronics_v3.json regenerated: 193b778ef244558a.

## LEAD CHANGELOG 186 relay (coordinator, 2026-10-13) - R2 command hold, L* 1.3 s, OI-37 hygiene
- 186 (2) R2 command hold IMPLEMENTED in the ECU core (types.h Cmd::DROGUE = 17, tlmf::R2_HOLD/DROGUE log-only b0/b1, Outputs drogue_attached/r2_hold;
  config.h kR2HoldThrust_N 62.5 N + static_assert; engine_ecu.{h,cpp} hold in RUN = !stand && drogue attached && Pc invalid -> thr = min(cmd, 62.5 N)
  at once, limiter parked, return at <= kStartRamp_Nps; protocol.{h,cpp} TLM_RELIGHT d6 b6 DROGUE echo, BLOCK_MASK 0x3F (refuse codes <= 15)).
- Unit test (v210-17), two checks [SIM, ideal Rig9 plant]: test_core 309 passed / 0 failed (307 before + 2). Hold level reached after 26 ms
  (setpoint slew bound 28 ms; the 2500 N/s ramp would take 55 ms), held 62.50 N; release max step 2.500 N/ms, 200 N after 55 ms; boundaries
  B (Pc valid again) / C (no drogue) / S (stand -> PC_SENSOR abort) / D (Pc valid) / E (command handling, CMD_STATE round trip) all pass.
  build/test_core 9baa6a63eb144e2e. Not physical evidence; FC side (deployment report, R2 test, release) to be modelled in SIL S17.
- SIL S17 (new, ./build/sil r2hold <out>; sil_main.cpp scR2Hold + R2Fc in-loop FC stand-in + Combustion v2.4a cold-flow table A1_relight_286.7K
  e094c4be80d12f66) [SIM on ASSUMED/DERIVED inputs]: 17 cases + 2x30 noise runs, 0 not as expected (scratch run, build/sil 28fb26fc00855bb5):
  lit starved plateau + Pc lost at E2+5 ms -> hold 421 ticks, plant thrust in the hold 51.2 N (open-loop map at the A1 state; 62.5 N target),
  R2 release at E2+425 ms (75 ms before pcf_tmax 0.5 s; the no-report control releases at +415 ms), DROGUE 0, command back at 2.500 N/ms;
  flame-out at E2+6 ms with the hold: hold lift 0.2154 mm, F_cold bound 12.72 N -> no release, ABORT at E2+500 ms (calm, W10<6 bound 20.85 N,
  200/500 N); W6 bound: 1 frame >= 37.16 N (37.23 N) from the lit-plateau carry-over through the 20 ms estimator lag; with the onset E2+10 ms
  2 frames in a row (39.54 N): the 3-frame persistence alone prevents the release (one frame short). Steady W6 margin 16.31 - 12.72 = 3.59 N.
  All-winds bound 33.00 N + hold: dead vehicle RELEASED at +35 ms (as LEAD 186 predicts; A1 wind rule HARD). Controls without the report (no
  hold): 200 N lift 0.62 mm F_cold 35.9 N -> calm 0 frames (36.58 N max, held), W6 released at +55 ms, 500 N calm released at +115 ms (F_cold
  117.6 N); 5 N rms noise, calm, 200 N: no hold 27/30 dead released, hold 0/30. HEM nominal cold flow: no-hold 200 N W6 held (33.70 N max).
  With Pc valid the starved plateau ends in FLAMEOUT +54 ms (A3), as S14 (B). S14 (B) FC model = line-161 interim time-only release, which
  line 175 (5) replaced by R2: S14 (B) ECU side stands, its FC release time is historical; S17 carries R2.
- Final record re-run for 186 (2) (scratch run_all + run_small, nice 10, build/sil 986f77d935ef9f8c, sil_bpc1 12fde7c8e52daa08, test_core 9baa6a63eb144e2e):
  245 files byte-identical to the record-5 folder; differ only sil_all_time.txt (timing) and test_core_log.txt (309/0: the 307 earlier lines
  identical + 2 v210-17 lines); 6 new S17 files. Old versions kept in results/sil_v2p10_pre186/; record-5 manifest kept as
  results/sil_v2p10_MANIFEST_v1_record5_pre186.json (6bec91895f01fd9f). results/fault_path_v4.json restored from the pre-run copy (only out_dir
  differed: scratch path). Runmap +S17_r2hold (10 entries). Rebuild build/chk5 identical for all three binaries.
  MANIFEST_v1.json 6d1dd43ddeeba0d7: record 2b4edc73ca0db018, tree 8ec86d515cc9980d, 39 sources, 253 results, 0 unmapped, FAIL lines 7 (v1.3 rule 11).
- make arm re-run after the R2-hold edits: 93 -Wdouble-promotion warnings (unchanged), engine_ecu.o text 29614 B (was 29502);
  results/arm_build_v2p10_log.txt. bom_v2.py re-run: only row 218 text changed (bleed valve: Burkert 6027 screened, not a candidate).
- bench_plan_v3.md: L* row (FC rule), unpurged row per 186 (1), DROGUE echo row, R2 command hold row (SIM numbers from v210-17), mask 0x3F,
  go/no-go drogue echo item, ABORT magic bytes written 0xA5 0x5A, outputs table rows for OI-38.
- Generator (make_interface_json_v3.py) run on the final record: 186 sections added (r2_command_hold, oi37_interface_hygiene), review status
  recast to CLOSED / OPEN (partly done noted) / DISPOSITIONED, hold_2s check (true by construction: config.h derives kPurgeFlowStart_s),
  Combustion request extended (start[0].action also carries the 1.7 s interim), GNC request on the purge "ECU duration cap" wording.
- Found while running it: the lead published gnc.json v3.1 (4f3209323b0e0ed4, CHANGELOG 191-192) at 16:07, after the SIL record and the
  manifest (which therefore lists the gnc v3 header references as current). New calc/v2p10/gnc_v31_read_keys_check.py ->
  results/gnc_v31_read_keys_check_v2p10.json [DERIVED]: under requirements and flight_software 0 numeric leaves changed or removed;
  2 text changes (ignition.relight_conditions v/tag); 2 numeric leaves added (purge_bound.*_rev2); relight planning values identical.
  The generator now re-checks gnc references against the hub file (HISTORICAL since CHANGELOG 192, no numeric change) and keeps the
  manifest status otherwise. Manifest not re-recorded (its configuration did not change).
- gnc v3.1 purge_bound.ecu_cap_mass_kg_rev2 0.073 kg calls 2.5 s the "ECU duration cap": contradiction kept (ECU both-open cap 2.61 s,
  77.7 / 83.6 g; hardware window ~96 g) -> new GNC request in electronics.json v3.
- KiCad README: priced BOM pointer bom_v2.csv -> bom_v2p2.csv (stale since v2.2).
- LEAD 194 (7) / coordinator relay (070BG over-range at FA-1): calc/v2p10/fa1_overrange.py (extract / summarize) +
  calc/v2p10/fa1_overrange_chain.cpp (adapted from spike_chain.cpp; per-sample output limit, ADC 4.99 V, E2 emulation, persistence 5 ms).
  896 FA-1 cases (fa1_envelope_v2p4a 64b328150025fa1e) x {head line on, head line off tau 0.9 / 0.1 ms, aft line on} x v_sat {4.95, 4.74,
  4.50, none} x 4 ADC phases = 57344 runs, 41 s nice 10. results/fa1_overrange_v2p10.json 74d70277fed1af69, _cases.csv cd96ad39a0f8fb29,
  _run_log.txt, _traces/ (5). Cross-check vs published spike_chain (no line, case 743): identical (raw 63.36, filt 42.14, cmp 2.387 V).
  Findings [SIM]: no line, tau 0.9: port = head <= 88.02 bar abs (< 141.3 proof), reading max 4.06 V / 63.4 bar abs (no flag; the log
  under-reads the 88 bar peak), fw 30 bar / 5 ms filtered trips 362/896 (HARD_START), comparator 115 nominal / 156 low band; any 362.
  tau 0.1: 6 readings >= 4.75 V (1.5-1.8 ms), 21-26 at/above FS unflagged, any 379. Line on (linear model): 640/896 hit the 1 kPa floor
  (non-physical swing), port to 151 bar abs (> proof), 264 over-range HARD_START at 3.3 ms; sensitivity only. Sensitivities (not
  proposals): comparator RC 10 / 20 ms low band 0 trips; persistence 10 ms 98-154, 15 ms 0. Grid counts are not probabilities.
- correction: the 070BG proof is 140 bar g = 141.0 bar abs (140 + 1.013), not 141.3 as first written above; fixed in fa1_overrange.py, bench plan, generator before publication.
- LEAD 194 folds (no firmware change): bench_plan_v3.md aa82f280feeeee4c (B-DPC-1 113B22 + NI 9234 values, line-end sensor; B-PC-1
  over-range row; unpurged row per 194 (3); R2 row + CF-3 start-lift point per 194 (4), three lifts 0.2154 / 0.2178 / 0.2039 mm not
  reconciled; outputs rows). bom_v2.py afd3cbfc3394d185 -> bom_v2p2.csv 75723fd39be88c20 (rows 218 note FA-1 domain, 237 113B22 qty 3,
  238 NI 9234 coupling/compliance, 245 + hydraulic pump; counts unchanged 250 / 3 / 213 / 34). Generator 8912b95febe64f0e ->
  electronics_v3.json 38bf149f368c1d4c (47 keys, 20 OIs; new pc_overrange_fa1, OI-FA1-PC-OVERRANGE; unpurged texts, purge_commit note,
  r2_command_hold, OI-38, requests per 194). Scans: costs nothing 0, 181 (1) 0, 141.3 0; every 'E2 + 0.22 s' marked withdrawn.
  NI 9234 specs read at ni.com (377849B-01 Feb 2025: compliance 19 V max, AC -3 dB 0.5 Hz); PCB 113B22 at pcb.com product page.
- Hub: interim interfaces/electronics.json 9052d894578990d4 (never announced) archived at 06-electronics/archive/v3_interim/; published
  38bf149f368c1d4c; calc/docs/results copies; SHA256SUMS-v2.10.txt 674eef94498822dd (504 lines, verified).

## 2026-10-13 17:06 - disk request from the lead (relayed by the coordinator): superseded SIL result folders compressed
- 13 workdir folders (1610 files, 4221591266 B) -> results/archived_tar/<name>.tar.xz (XZ_OPT='-1 -T1', nice 19), each member
  re-hashed from the archive against a per-file sha256 list before the source was deleted; run log 0 failures, exit 0.
- Net freed 3895967293 B (3.90 GB) = du -sb change of results/ (4996487706 -> 1100520413 B). Index with every archive sha256:
  results/archived_tar/INDEX_v2p10.txt (c0883a0d2677d5dc), including the scripts that need an extraction before a re-run.
- Not touched: sil_v2p10 (live record), sil_v2p10_pre186, fa1 traces, snapshot, plots, and every hub file (the hub copies of the
  sil_v2p9 / sil_v2p8_2 / sil_v2p8_3 subsets stay as they were). results/sil re-created empty (default output folder of test_core/sil).

## 2026-10-13 17:12 - CHANGELOG appended
- Guard f3dd884de680e626 (194 lines) held; hub SUMS-v2.10 674eef94498822dd re-verified (502 hashes OK) and electronics.json
  38bf149f368c1d4c just before. 7 Electronics (result) lines appended as lines 195-201; CHANGELOG now 201 lines, c5da284c9c922632.
- Final wording fixes before the append: the 3.59 N W6 margin stated against the 16.31 N allowance; 194 (3) stated as "the baseline
  has no unpurged relight (alternative = GNC comparator only)"; no REPORT file in the 06-electronics top level (report = handback text).

## 2026-10-13 17:20 - handback
- Final report delivered as handback text (no REPORT file in the hub). Extra findings recorded there: spike_chain_v2p10.json label
  "Persist 3 ms" is stale (the tool computes with cfg::kPcOverPressureTime_s = 5 ms); test_core.cpp writes "version": "v2.8.3" in
  test_core.json (label only); sim.cpp ADC path limits the averaged reading at 4.95 V, not each transducer sample (the comparator path
  limits per step); v2.10 pre-194 B-DPC-1 sensor 113B24 (69 bar FS) was below the FA-1 peaks (replaced by 113B22).
