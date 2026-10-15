CLAIM
- Firmware v2.9 implements:
  - the LEAD relative light rule;
  - A3 / A7 / E3 start monitors and the CF-3 lift table;
  - coast re-zero;
  - the head-end bleed provision: PURGE (pre-scheduled or integrated), pad BIT S0-S4, V1-first closure, leak monitor, BLEED_FAULT;
  - drogue-release support bits;
  - log v10 (150 B);
  - the MV / P_mid ladder decode.
- All of this is SIL / design evidence only. None of it is hardware validation.
- The schematic v2.4 draws the bleed provision. ERC 0/0 and a netlist cross-check 0/0 do not approve the hardware.

CONFIGURATION
- Firmware v2.9: test_core 287 pass / 0 fail.
- SIL manifest results/sil_v2p9/MANIFEST_v1.json: tree 4455ee5946b835fe, record 89ecd67612d90133, 12 generated-header references, 0 stale.
- Build note: the "all" run used a binary built before the S12 case additions and the ladder decode. The ECU core logic is identical; S12 was re-run on the final binary.
- KiCad 7.0.11. Python /opt/engine-venv. No tools installed this session.

SOURCES (sha256/16)
- Hub segment_traps_v341_v1.json: 48.23 cm3; slug 12.0022 cm3 at 0°; 28.92 cm3 at 10° max.
- CHANGELOG RETAINED-VAPOUR line: 19 cm3.
- Mechanical workdir, UNPUBLISHED:
  - bleed_taps_v341_v1.json (a05927e74d08e479): 15.91 cm3 at 10°.
  - bleed_taps_v341_v1p1.json (11d8e7f613738b53): 4.84 cm3 at 2°.
- Combustion start_latency_v2p4.json A1_relight (T 286.7 K, m 1.16 kg, D 0.032213 m).
- gnc.json v3 (3e97c378cfebee95).
- Bürkert ds6027 PDF via a WebFetch summary [DATASHEET, check against the PDF]:
  - HP 1.0 mm orifice rated 0-250 bar DC.
  - Switching, DC: opening 20-30 ms, closing 50-80 ms.
  - HP medium temperature -10..80 °C.
  - Coil 42 (K): 16 W cold / 21 W warm. The column mapping was ambiguous.
  - Mass not stated.

FILES (workdir /home/claude/work/electronics, mirrored to the hub 06-electronics)
- **Firmware:**
  - src/core/engine_ecu.cpp/.h: riseTrack, tlm_flags
  - types.h: tlmf::
  - config.h: kDrogueRiseHold_s 0.10 [LEAD/GNC]
  - protocol.cpp/.h: TLM_FAST d1 packing, LogRecord v10 = 150 B with tlm_flags
  - sensor_scale.h/.cpp: mvLadderDecode
  - mv_ladder_table.h: GENERATED
- **SIL:**
  - sil/test_v29.inc: tests (25)-(27)
  - sil/sil_main.cpp: S5 start metrics + NaN-percentile fix, S13 drogue scoring, S12 datasheet-timing cases + corrected first-burn expectation, S9 text without 3.0 bar
  - sim.cpp: a7_tlmf column
- Hub firmware v2.8.3 archived to firmware_archive/v2p8_3.
- **Calc:**
  - calc/fault_path_v3.py → results/fault_path_v3.json/.txt
  - calc/ignition_rule_sil_v1.py → results/ignition_rule_sil_v1.json
  - calc/hbleed_provision_v1.py → results/hbleed_provision_v1.json/.txt + mv_ladder_table.h
  - calc/bom_v2.py → results/bom_v2p1.*
  - calc/make_interface_json_v2.py → results/electronics_v2.json = interfaces/electronics.json
- **Hardware:** hardware/kicad_gen/ecu_design.py, make_ecu_kicad.py (REV v2.4); hardware/kicad/* (schematic, PDF, ERC report, pin_map_v2p4.csv).
- **Docs:** docs/bench_plan_v2.md.
- **Results:** results/sil_v2p9 in the workdir is 615 MB. The hub holds a curated subset: 29 files (JSON, logs, S5_mc.csv, S13_a1_mc.csv).

TESTS / VERIFICATION
- **test_core 287/0:**
  - (25) The rise bit is set before E2. At E2 the flags read 112 (= E2 + rise + held). Held-to-0.10 s latches at E2 + 100.0 ms. d1 = 244.
  - (26) A 3 ms dip clears held for the rest of the start; an unlit start sets no bits.
  - (27) The 10 ladder codes decode correctly; short, open node and harness-open codes are invalid.
- **S13 (A1 relight, N = 300 per cell):** 52 residual corners pass. Coast re-zero:
  - with re-zero on, offsets of ±0.2 and -0.3 bar behave correctly;
  - with re-zero on, +0.3 and ±0.6 bar refuse the relight;
  - with re-zero off, any offset of 0.2 bar or more refuses the relight (vented check 0.1 bar).
  - Refusing is the fail-safe outcome; it costs availability.
  - Purge starts leave P0 unchanged (±0.6 bar offsets handled); E2 comes 16-20 ms after the light; each purge uses about 76 g of N2O.
- **S5 pad MC 300:**
  - 272 NONE, 27 TVC_SUPPLY, 1 PC_OVERPRESSURE (v2.8.3 had 31 NO_IGNITION).
  - E2 16-18 ms after the light; lowest A3 ratio 0.463; 1 A7 event.
  - The up-step metric is NaN in 27 runs; these are now excluded and counted.
- **S12:** 25/25 pass, including the corrected expectation for a valve stuck open in the first burn. That case flags at +0.209 s in the burn and ends BLEED_FAULT at the relight (7.651 s).
- **S11v29:** all cases listed in results/fault_path_v3.txt.
- **Bleed calc:**
  - Ladder: R_top 10k, R0 82.5k, R1 9.53k, R2 17.8k, R3 33.2k. Minimum gap between code windows 0.019 of full scale, worst case with 1 % resistors and ADC error.
  - Comparator: rise 9.86 / fall 8.86 bar g.
  - Mid volume vents in 12.5 ms (liquid) + 8.9 ms (vapour). Closure confirmation 76-106 ms after E0 against the 150 ms limit.
- **KiCad:** ERC 0/0, cross-check 0/0. The first GUI ERC attempt failed ("eeschema main window not found"); the re-run passed.

DESIGN ANSWERS
- **What the ECU sees for a bleed stuck open during a burn:**
  - Nothing on P_feed (0.016 bar) and almost nothing on Pc (SIL -0.02..-0.05 bar; oxidiser flow -1 g/s of ~97 g/s).
  - Only the P_mid leak monitor sees it, at +0.21 s: a flag plus an EVENT in flight, BLEED_FAULT on the stand.
  - Flow through the bleed: 11.3 / 20.1 / 31.3 g/s at 0.6 / 0.8 / 1.0 mm.
  - V2 stuck open alone stays hidden until the next pad BIT.
  - After a stuck-open, the next purge relight ends BLEED_FAULT.
- **Purge timing:** both the pre-scheduled and the integrated purge work.
- **Pre-lift baseline:** cannot be contaminated, because there is no main N2O before E1.
- **Rules confirmed:**
  - MV-early-open dropped.
  - PRIMED = DIRECT_PATH; it is not a vapour detector.
  - RG-15: FC_THRUST never freezes; k_est_asc and the apex predictor freeze on the invalid marker.
  - W stays a build constant.
- **A7 written reasons:**
  - A7 stays armed from E1 to E3 with the lit-start band.
  - The rate criterion is not implemented because there is no Combustion rate bound yet.

SIL FAIL DISPOSITIONS
- **S6, unchanged from v2.8.3:**
  - gimbal_jam_moving_cmd: FIX.
  - throat_blocked_70pct: ACCEPTED-WITH-REASON (load case LC-TB70).
  - ballvalve_compare: OBSOLETE.
- **S6, new in v2.9:** hard_start 0.20 s / 0.25 s late light → OPEN, needs a LEAD decision.
- **S9 ±1.034 bar TEB cases:**
  - At +TEB an unlit start reads 1.87 bar abs, above the 1.8 floor. It confirms a false E2, enters RUN, and A3 FLAMEOUT trips 0.14 s after IGNITION.
  - At -TEB the start lights, then A3 trips on the biased ratio.
  - Both are outside the ±0.6 bar band; B-PC-1 closes them through the 2.0 bar floor.

UNKNOWNS
- Coil voltage, holding power and mass of the bleed valve; N2O compatibility of the PEEK/FKM seat.
- U3V70F12 headroom on +12V_ARM.
- Vent time with real-gas effects.
- Whether the 170BG range code is available.
- The hardware value of E2 latency.
- The fuel-starved plateau: not in the SIL plant.
- The unreached vapour volumes come from an unpublished Mechanical file.

NEXT CLOSURE
1. LEAD: decide OI-A5-LATE. Options: accept the abort, or change A5 or the light confirmation.
2. Electronics + Mechanical: choose the coil (12 V coil or a 24 V boost), then B-PWR-2.
3. Bench (founders): B-PC-1, then kBpc1Shown.
4. Bench: B-BLEED-1 confirmation time ≤ 0.12 s.
5. Hot fire: IGN-1 for latency, rise and A3 margin.
6. GNC: re-confirm the gnc.json v3 planning keys.
7. Independent review entry in supervision.json (not done by me: the repo is read-only).

OPEN INTERFACE ISSUES
- OI-A5-LATE (HIGH): late lights abort HARD_START (item 4 above).
- OI-BLEED-COIL (HIGH): coil voltage vs the +12V_ARM rail (item 6 above).
- OI-TEB-FALSE-LIGHT (MEDIUM): the S9 +TEB false light; closed by B-PC-1.
- OI-A3-MARGIN (MEDIUM): lowest A3 ratio 0.454 against 0.40.
- OI-E2-LATENCY (LOW): E2 16-18 ms after light against ~15 ms.
- OI-BLEED-VOL (MEDIUM): unreached volumes from an unpublished file.
- OI-GNC-V3 (MEDIUM): gnc.json v3 planning keys removed.
- TLM_FAST d1 change: every FC/GNC decoder must mask the state as d1 & 0x0F.
- BASE_AMB clamp option (P0 = ±check) stays a LEAD choice; S13 B showed no failure.

ERRORS FROM EARLIER SESSIONS (now recorded)
- ignition_detect_margin_v1 used a conditional statistic.
- The S1 margin needed a correction.
- "7 MAX31856" was really 6 MAX31856 + an NTC.
- The J610 → J901 label was wrong.
- A drogue comment was wrong.
- Proxy 403s: www.analog.com, www.radiolocman.com, ti.com through curl.
- A manifest incident.
- A FET gap on the TPS552882 drawing.
- The schematic lagged behind at v2.2.
- A stale gnc.json v3 finding.
- WebFetch gave a wrong CSD17578Q5A pinout.
- scMC NaN percentiles (fixed now).
- ign_lift_cal write, format and stale-build issues.
- The loadNotch anchor.
- A vmap compile error.

ERRORS THIS SESSION
- A test fmt string used %X on doubles. Fixed; the logic was unaffected.
- Inputs.pc_valid does not exist. Fixed to pc_sensor_ok_.
- A pattern-count abort in the patch script.
- Generator breakages, all fixed:
  - gnc v3 keys missing;
  - the 27-cause assertion;
  - stale kIgnLiftTab_m and 3.0 bar references;
  - wrong 'value' key;
  - a bracket error.
- The pin map file was overwritten under the v2p3 name. It was renamed to v2p4; the v2.3 copy is not in the hub, because the hub never held a hardware/ folder before this session.
