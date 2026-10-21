# 06-electronics v2.11 handback

Electronics (engine team), closed out 2026-10-21T05:40:27Z. Saved here by the lead on 2026-10-21T05:49:57Z (date -u), verbatim from the author's final message: the harness does not let a subagent write a report file, so the handback text is the report. Staged set: `06-electronics/staging_v2.11/` (`SHA256SUMS-v2.11.txt` dca5c3d8de4d1ea6, 170 files, sha256sum -c OK at 05:43Z). Author: Electronics. Reviewer: REV-ELEC-3 (running). The lead promotes v2.11 and `interfaces/electronics.json` v4 only after that review. Nothing here is physical approval.

```text
BEGIN ELEC-V211-HANDBACK

Electronics v2.11, from the lead brief "Electronics v2.11" (2026-10-20). Closed out 2026-10-21T05:40:27Z (UTC, date -u).

RESULT
- All seven Part B items are answered. The work is staged in hub 06-electronics/staging_v2.11/: 170 files plus SHA256SUMS-v2.11.txt dca5c3d8de4d1ea6, and sha256sum -c passes. The v2.10 tree and interfaces/electronics.json v3 (38bf149f368c1d4c) are unchanged. Promotion is yours.
- Part A is built as you ruled in 249 (1)-(4). Tests pass in SIL.
- Two items come back to you for a decision:
  - B5: the scheduled purge does not fit a 2.39 s cap, so the cap stays 2.55 s and the warm-end mass is stated.
  - B3: adopting the ride-through for flight stays your decision.
- 227 (5): the 0.8 s window is CONFIRMED, with conditions.
- REPORT-v2.11.md is NOT in the staging folder. The harness refuses report .md files written by a subagent, so this handback is the report. You can save it as staging_v2.11/REPORT-v2.11.md; the SUMS header says so.
- Nothing below is physical approval. A SIL pass or a hash match shows that a computation repeats, not that the hardware or the physics is right.

CHANGELOG
- My line is 251, appended under the exclusive flock at 05:39:53Z. Inside the lock I asserted 250 lines and b31c5453833d02ee: the lead added line 250 at about 05:24Z. Line 250 gives Electronics no item; v4 records it as NOTED.
- Re-read at 05:40:16Z: 251 lines, sha256/16 caf7f632a1ddd139.
- Line 250 had earmarked 251 for FEA3D-2. FEA3D-2's line now becomes 252 or later; it is gated on your go with count / sha anyway.

FILES (sha256/16; paths relative to staging_v2.11/)
- results/electronics_v4.json 11f7896ad0d0613b
  - Generator: calc/v2p11/make_interface_json_v4.py 0d5399d262f626d3.
  - It imports calc/make_interface_json_v3.py 8912b95febe64f0e, which is identical to the hub copy.
  - It runs in /home/claude/work/electronics and is deterministic apart from generated_utc.
- docs/bench_plan_v4.md 5b1c9336d7b8db50
- firmware/: 60 files; 28 changed or added against hub v2.10.
  - Makefile 88bffc3d62595061
  - src/core/config.h 8e85c419b3125cdf
  - src/core/engine_ecu.cpp 2b47b62b0887c937
  - src/core/protocol.h 905de7204a814ca3
  - src/core/types.h d7fe0f1522a5948c
  - sil/sil_main.cpp 54eedc9c1cddd3fa
  - sil/sim.cpp 9772f034b795b178
  - sil/sim.h b2cf751475494091
  - sil/sc_v211.inc 3f76026c88768ecb
  - sil/sc_v211_r2.inc b7def3b13a22d708
  - sil/test_v211.inc f93db1303f8344a7
  - sil/test_v211b.inc b047bafb5196c7c4
- SIL record v2.11: results/sil_v2p11/ (76 files)
  - MANIFEST_v1.json eaa9efc5112a8178: record 8c1a534c3af1b0ba, tree cb3e35025d7ec130, record_utc 2026-10-21T02:35:43Z, tool v1.4, 44 sources, 75 results, 0 unmapped.
  - results/sil_v2p11_runmap.json fd78364bc21458fd.
  - results/sil_v2p11_record1_superseded/: 6 gzipped logs.
  - Key result files:
    - compare_v2p10_v2p11.json 7bb97d757dbdcc46
    - S17v2_r2v2_sweep.json 404a19d7064b336f
    - S6R_in_window_overpressure.json 006985357aca234e
    - S6C_rc_cost.json 7b8b53b17a520775
    - S12_bleed.json 40a11d4d42d69026
    - S6_aborts.json 3930a3a24345e4d9
    - S10v211_cold_rule.json f87935edb5f23564
    - S13/S13B_ext_bpc1_false.json a932482085179686
    - S13/S13B_ext_bpc1_true.json b27c919c09eacd48
    - test_core_log.txt 3d9c40a8cd5d417d
    - test_core_nohooks_log.txt 226a5bb1e36b1954
- Other results:
  - pc_transducer_v3.json 161982ca107d83a7
  - fa1_chain_v2p11.json eea3b964e41f0afe, and _cases.csv eecbff7c67550447
  - case_tc_channel_v1.json 6f29c93eff893adf
  - tf1_rate_v1.json 0c1bb777739dcf8f
  - bom_v2p3.json 82d1ef1c6fcf92d3, .csv 305dc29ff856475b
  - gen_tables_v2p4b_leafdiff_v1.json 711f8f01f81d9497
  - gen_headers_regen_check_v2p11.json 3223fcc77035a012
  - arm_build_v2p11_log.txt db0c07a664e69932
- calc/v2p11/: 11 scripts, hashes in SUMS.
- Work log (not staged): /home/claude/work/electronics/v2p11_notes/PROGRESS.md 2128e09f0647b682.

BUILD AND TEST [SIM]
- I rebuilt the four binaries from the STAGED sources in scratch (make -j1, nice 15). All are byte-identical to the record:
  - sil d4bf5d5436a179e6
  - sil_bpc1 6c7a32aeb66bebf4
  - test_core 361d7182363c0d54: 326 passed, 0 failed
  - test_core_nohooks 2715becf5628c699: 325 passed, 0 failed
- ARM objects (arm-none-eabi-g++ 13.2.1 -Os, Cortex-M7): 41,084 B text (v2.10: 39,316 B), 0 errors, 96 -Wdouble-promotion warnings (v2.10: 93). Objects only: not linked, no HAL.
- Every v2.10 result file was compared against v2.11, case by case or leaf by leaf:
  - S6: 58 cases, 9 identical, 49 changed; passed 55 -> 55.
  - S7: 9 identical.
  - S8: 5 -> 5.
  - S10: 31 -> 31.
  - S12: 35 changed; fails 4 -> 4.
  - S13 B extension: fails 32 -> 0 and 64 -> 0 (v2.10 was scored on the 203 (5) criteria; v2.11 on the 216 (4) per-location criteria).
  - S14: 21 changed. S17_r2hold: 17 changed.
  - S1-S5, S9, S13, S15, S16 and probeF: changed leaves (C1 chain, lift-commanded hold, new limits).
  - New in v2.11: S10v211, S6R, S6C, S17v2.
- Fail lines are the v2.10 set, all dispositioned in sil_fail_dispositions:
  - S6 (3): gimbal jam RE-24; throat-blocked x2, where HW_OVERPRESSURE acts first and the case is inside LC-TB70.
  - S9 (4): the spike train gives a BASE_HIGH refusal (fail-safe); 3 TEB cases (OI-TEB-FALSE-LIGHT).
  - S12 (4): both bleed valves stuck open (OI-BLEED-DETECT).

PART A AS BUILT (249 (1)-(4))
- Case-TC abort A = 423.15 K on TC1 / TC2, 0.20 s persistence. Test: 420.15 K, no abort; 425.15 K, OVER_TEMP after 0.2 s.
- False-trip side: 7.78 K worst case, 3.55 K RSS, inside +12.26 K [DERIVED; DATASHEET MAX31856 19-7534 Rev 0; IEC 60584-1 AS RECALLED; EMI 0.5 K and CJ gradient 1.0 K ASSUMED].
- Low-reading tolerance tol_lo = 9.05 + 0.630 r K.
- Start / relight limit 403.15 K. A COAST RELIGHT is refused CASE_HOT at 405.15 K and accepted at 400.15 K. ARM is refused OVER_TEMP above the limit.
- Stand T0: in stand mode ARM is refused CASE_WARM_STAND (31) when TC1 or TC2 > 297.15 K; accepted 0.5 K below. Flight has no T0 rule. Founder row F-13.
- TC3 ARM refusal at 523.15 K.
- T-F1 is on the A 175 rows. After B-TC-1 calibration: tol_lo 10.28 K at 7.03 K/s.
- 248 founder rule: bench plan F-14. 25 required S6R runs exceed 60 bar abs.

PART B
- B1: S17 v2.11 against GNC R2 v2, evaluated offline. Sweep: onsets 1-50 ms x 10 frame phases x seeded noise, 200 / 500 N, hold on / off, windows 0.5 / 0.8 s.
  - With the ECU hold and the mode-3 flush, 0 of 2000 dead evaluations are released at either window. Minimum margins: +5.789 N (0.5 s), +4.954 N (0.8 s) [SIM].
  - Without the hold, 320 of 1000 normal dead runs are released. Without the flush, 264 / 326 (normal) and 160 / 172 (starved040) of 1000 at 0.5 / 0.8 s.
  - 227 (5): 0.8 s is CONFIRMED for W10 < 6 m/s, not returned. Conditions:
    - the hold, with the FC DROGUE report;
    - the flush;
    - the photodiode main-chamber view proven, or the reference re-taken at E2 or at the light (photodiode-blind families release 20 / 42 and 42 / 98 of 1000);
    - FC noise inside the budget below;
    - W10 < 6 m/s only (all winds: 320 of 1000 at 0.8 s).
  - Lit side: a starved plateau is released up to 0.75 s at the 0.8 s window, against 0.45 s at 0.5 s.
  - 227 (6): the flush is implemented in the S17 evaluator. The ECU has no mode-3 filter; the flight implementation is the FC owner's.
  - FC frame-noise budget [SIM + DERIVED, iid ASSUMED]:
    - 0.8 s window: <= 2.51 N rms iid, or 1.65 N AR(1) with rho 0.61.
    - 0.5 s window: <= 3.06 N rms iid, or 2.00 N AR(1).
    - 5 N rms is not admissible: P = 6.9 % / 22.9 %.
    - GNC's own design maxima reproduce RV6-07's 6.5-18.4 %.
  - 230 (5) is carried as OI-FMIN-LIT: with the lit thrust capped at 33.14 N, no lit run is released when the flush is on; without the flush, 274 of 1000 are released.
- B2: R2-02.
  - FC rule: re-send DROGUE 0 with a new sequence number on each TLM_RELIGHT frame that still shows b6 = 1, at most 10 times (0.2 s), then log DROGUE_ECHO.
  - ECU backstop: E2 + 850 ms = 0.8 s window + 2 x 20 ms FC frames + 10 ms latency (latency ASSUMED). It is latched, logs EVENT R2_BACKSTOP 0x24 and sets tlm_flags b2.
  - Bench plan B-FC-1 has a "LOST DROGUE 0" row.
  - test_core cases "lost DROGUE 0" and "R2 backstop is per burn" pass.
- B3: R2-03 ride-through, a build option, default OFF.
  - Flight relights only; window E1 to E2 + 15 ms.
  - Filtered persistence 15 ms (13 + 2; longest C1 episode 12.0 ms).
  - Over-range N = 2.
  - T45 guard 7 ms.
  - Comparator RC FIXED at 12.825 ms (12.100-13.552 ms with tolerances).
  - On the C1 chain, 0 of 896 FA-1 cases reach over-range. As built, 374-379 of 896 abort; with the ride-through, 0.
  - S6R: 105 of 105 required in-window over-pressure runs abort inside LC-TB70; 0 runs put the ECU outside it.
  - S6C: the fixed RC costs +2.8 to +10.8 ms on the comparator trip and up to +1.11 bar on the peak; all inside LC-TB70.
  - Every S6 / S6R / S6C case uses A = 423.15 K. The LC-TB70 Z1 label still says 448.15 K, which is a hotter state than the 423.15 K abort admits.
  - Face-peak contradiction: the C1 face peaks 104.5 / 121.6 / 125.1 bar abs sat above the old 102 bar proof basis [SIM, ASSUMED passage model]. 249 (4) resolved this (>= 166 bar abs required; C1 is 206.8) and routed it to REV-COMB-4.
  - S6R input finding (10 runs with input outside LC-TB70: replay peak 88.02 > Z3 75.519; 46 of 896 grid cases) is routed to REV-COMB-4 and Mechanical. No v2.11 claim depends on those runs.
- B4:
  - 216 (4), per location:
    - Pad / stand: BASE_HIGH or BASE_AMB refuses the lift.
    - A1: BASE_HIGH runs on the measured P0. BASE_AMB sets P0 := 0; the A7 HOLD band then aborts PC_SENSOR 50 ms after the lift, with no light and no false E2.
    - S13 B extension: 0 fails in both builds. A1 Monte Carlo: 0 of 500 runs are BASE_AMB.
  - 216 (7): the ARM margin is 0.42 K (1.5 x 0.23 + 0.07). PREPRESS safe exit: back to ARMED on the refusal tick, MV dropped, CLOSED switch within 0.5 s; the test sees it after 1 ms.
  - 216 (8): A7 blank conditions 1, 2 and 4 are done; 3 (FC owner) is open.
  - 216 (9) / 230 (4): the hold is lift-commanded at 0.21776 mm, equal to the kIgnLiftTab_m A1 row.
  - R2-23: yes, for the over-range tick only (non-sticky). A glitch at E2 + 350 ms trips U330: HW_OVERPRESSURE, fail-safe.
- B5: purge.
  - The command span 2.50 + 0.03 - 0.08 = 2.45 s is above 2.39 s, so the cap stays 2.55 s [valve times ASSUMED].
  - Vented mass against the 76 g limit, at 29.25 / 31.06 / 33.13 g/s:
    - at the cap: 76.05 / 80.76 / 86.14 g;
    - scheduled flow: 73.13 / 77.65 / 82.83 g;
    - timer bound (firmware cap failed): 81.65 / 86.70 / 92.48 g;
    - PURGE_WIN bound: 96.33 / 102.29 / 109.10 g.
  - Measured-time form: 2.548 s on the basis.
  - Option not taken: a 2.43 s flow with a 2.39 s cap.
  - Hardware both-commanded-open timer (166 (3)) is designed: U576-U579, LTC6993-2, DIVCODE AS-RECALLED, schematic v2.6 not drawn.
    - Range 2.577-2.741 s.
    - T_hw,min is above cap + 1 tick, which is above span + 2 ticks, so the timer never cuts the schedule and 166 (3) stands.
    - SIL evidence: 81.79 g with the cap; 82.61 / 85.21 / 87.84 g with the timer alone.
- B6:
  - Founder block F-1..F-14 is in bench plan v4 section 0, including RFQs to Sonderborg DK-6400, the inquiries, F-12 / F-13 / F-14, and B-TC-1 with the BOM 266 calibrator.
  - 216 (10): statuses are in v4 rev_elec_2_author_status.
  - Transducer reselection: C1 Kulite XTL-190SM-2000A, 137.9 bar abs FS, proof 206.8 bar abs [DATASHEET]. Output above FS and recovery are MISSING (F-10).
  - Mass: -0.074 kg on P_feed + P_mid and +0.0131 kg for the Pc C1, net -0.061 kg. The worst combination is +0.025 kg, below GNC's 0.10 kg re-fly trigger. Not confirmed: nothing weighed.
  - BOM v2.3: 266 rows, all TO-QUOTE delivered to DK-6400 or n/a; no 0 and no "from" prices.
- B7: electronics_v4 contents.
  - 47 CHANGELOG items folded (203-250).
  - 31 abort causes, CASE_WARM_STAND added.
  - 15 limits, each with value and basis.
  - superseded_v3: 25 entries.
  - self_check passes.

FINDINGS
- S12 label: the stuck-open cases inject BOTH bleed valves (sil_main.cpp both_open_at), so the 203 (4) label "V1 stuck open with V2 closed" is wrong. V1 alone is detected in 200 ms. Residual vented mass: 28.36 / 50.37 / 78.60 g after the lift, 104.17 g in the first burn. FMEA row FMEA-A1-BLEED-BOTH-OPEN added.
- IGN-1 margin: E2 - light is 20 ms at the -0.6 bar S13 corners, so the <= 20 ms criterion has no margin there (<= 18 ms within ±0.3 bar).
- FC Pc branch: Pc_f at E2 is 3.04 vs the 3.0 bar abs threshold. Every normal run is released at the E2 frame (OI-FC-PC-BRANCH).
- S6 band_high SIL defect found and fixed before the record.
- Seat ringing with ideal 25 µs steps:
  - T45 does not fire. In the record, the 9 ride-build ideal-step runs abort 10-17 ms after the trigger.
  - The 38-61 bar raw swing comes from a pre-record diagnostic and is not in the record.
  - The main step cases use the 1.0 ms rise convention.
- Combustion v2.4b still says 112 bar abs proof (4 places) and "E0 + 0.15 s" (3 places). Its OI-46 mapping is confirmed.
- gnc.json v3.1 purge_bound wording: 2.5 s is the flow, not the cap.
- The LC-TB70 Z1 label should be redone.

DECISIONS FOR THE LEAD
1. Adopt the ride-through or not.
2. Purge: 2.55 s with 80.76 g at the warm end, or the 2.43 s / 2.39 s option.
3. Accept the A1 BASE_AMB outcome, or rule an alternative.
4. Decide on the missing relight path for an unprimed / UNKNOWN line with the bleed fitted.
5. The both-stuck-open bleed case: FMEA residual or a detection design.
6. Cite MANIFEST eaa9efc5112a8178. The 620b3d566fe0c8b9 named in 249 (13) is superseded by two re-records; the binaries are identical.

OPEN ITEMS WITH OWNERS (v4 open_issues, 29)
- Electronics: OI-HAL, OI-POWER, OI-RE15, OI-SCHEMATIC-V2P6, OI-STALE-LABELS.
- Electronics / Mechanical: OI-BLEED-VALVE, OI-GUARD-BAND (hot side, B-PT-1).
- LEAD: OI-PURGE-CAP, OI-A1-BASE-AMB.
- Electronics / LEAD: OI-BLEED-DETECT.
- LEAD / Electronics / founders: OI-FA1-PC-OVERRANGE.
- FC owner + GNC: OI-FC.
- GNC / FC owner: OI-FC-PC-BRANCH.
- GNC (FC) / Combustion / Electronics: OI-38-R2-COMMAND-HOLD.
- GNC / LEAD: OI-FMIN-LIT.
- Combustion / Mechanical / GNC: OI-PHOTODIODE-VIEW.
- Combustion / Electronics / GNC: OI-E2-LATENCY.
- Combustion / LEAD: OI-STAND-LATE-LIGHT.
- LEAD / Combustion / GNC: OI-UNPURGED-RELIGHT.
- Electronics + Combustion: OI-GEN-TABLES.
- Electronics + GNC: OI-GIMBAL-JAM.
- LEAD / Electronics: OI-TEB-FALSE-LIGHT.
- Electronics / FC owner: OI-WINDOW-LATENT.
- Electronics / founders: OI-R2-23-GLITCH.
- Electronics / Combustion / founders: OI-SEAT-RINGING.
- Accepted: OI-TB-MEOP, OI-A1-PCLOSS-OVERTHRUST.
- Routed to REV-COMB-4 / Mechanical: OI-FACE-PEAK, OI-S6R-INPUT.
- The 13 requests (FC owner, GNC, Combustion, REV-COMB-4 / Mechanical, Mechanical, LEAD, founders) are in v4 requests.

DISCLOSURES (no binary effect)
- tf1_rate_v1.json changed after your ruling: 5b995ead2f99d0e7 -> 0c1bb777739dcf8f.
- pc_transducer_v3.json still records the pre-249 (4) "112.2 bar abs" check and its combustion v2.4a input.
- Stale comments, not edited to avoid another re-record:
  - config.h l.757-768: the v2.10 thrust-commanded hold.
  - config.h l.832-834 / 865-866: the 170BG P_mid chain.
  - config.h l.900: U576-U578 (should be U576-U579).
- Stale labels:
  - scenario labels S9 / S12 / S14_v2p10 / S15 / S16 / S17_r2hold / probeF;
  - test_core v210-16;
  - BOM 212 / 214 / 245 notes;
  - the mech_params.h / mech_tables.h comment names mechanical.json v2 (0 code lines change on regeneration);
  - the config.h tags cite "21:46:49Z items 5 / 3", which are 249 (4) / (2).
- The manifest rebuild paths and the regen-check "scratch" field point to removed scratch folders. The manifest "date" field is the tool default.
- engine_params.h and the related generated headers still come from combustion v2.3 (OI-GEN-TABLES).

NOT DONE
- No HAL, no linked image, no board or bench work; schematic v2.6 not drawn.
- No design to detect both bleed valves stuck open.
- gen_tables.py not updated.
- S11 not re-run.
- Hot-side guard band not closed.
- Bleed valve not selected.
- LTC6993 DIVCODE not re-checked.
- The FC side is not implemented; the R2 v2 evaluation is offline, from GNC's text.

DISK AND PROCESSES
- Free disk 2,373,718,016 B at 05:40:12Z.
- Electronics tree +6.70 MB against the baseline; staging +8.64 MB. Net-new total about 15.3 MB of the 60 MB budget.
- Removed my scratch: ana/, run/, v4/, temp files, results/sil/ (duplicate JSONs), two .pyc files.
- No process of mine is running. I touched no ccx or other agent process.
- No git push.

END ELEC-V211-HANDBACK
```
