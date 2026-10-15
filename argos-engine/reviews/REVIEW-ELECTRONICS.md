REV-ELEC-1. Independent review of Electronics v2.9: firmware v2.9, the SIL record sil_v2p9, KiCad ECU schematic v2.4, BOM v2.1, bench plan v2 and interfaces/electronics.json v2.
Reviewer: the independent Electronics reviewer. I did not author any of this work. Date: 2026-10-13.

Everything below is code reading, simulation or arithmetic. Nothing here is physical approval. A reproduced number shows that the computation can be repeated. It does not show that the hardware or the physics is right.

## 1. SCOPE AND FILES

Hub: /home/claude/work/shared-fallback/engine/ (written "hub/" below). All hashes are sha256/16. I re-checked all of them at the end of the review; none had changed.

| File (hub/06-electronics/ unless stated) | Version | sha256/16 |
|---|---|---|
| firmware/src/core/config.h | v2.9 | 0ba1e1ef0fbce180 |
| firmware/src/core/engine_ecu.cpp | v2.9 | dbe1a756c4b77d37 |
| firmware/src/core/engine_ecu.h | v2.9 | d9c557b96d1f809f |
| firmware/src/core/types.h | v2.9 | 0fe8be0bbc628807 |
| firmware/src/core/filters.h | | b698f33b51ea0b22 |
| firmware/src/core/control.cpp | | cdd9749198b146eb |
| firmware/src/core/protocol.h / protocol.cpp | | ee974e67adac9c28 / 0557e09db6d03a00 |
| firmware/src/core/sensor_scale.cpp / mv_ladder_table.h | | c60bbcbe3fd3585e / 330eb425aaaf37f0 |
| firmware/Makefile | header still says v2.8.3 | f21094341faa5d88 |
| firmware/sil/sil_main.cpp / sim.cpp / sim.h | | e64158cbe2471bdf / 2f3291a993a0ead2 / 8bf1990e510790c0 |
| firmware/sil/plant.cpp / plant.h | | fb1da8546197f97c / 0daac33dfa6327db |
| firmware/sil/test_core.cpp / test_v29.inc | | 8200ddfa26c14a4d / 3f641b99ac3ae818 |
| results/sil_v2p9/MANIFEST_v1.json / test_core_log.txt | | 5307366143b0237f / 1a0463d81f4ac24f |
| results/sil_v2p9/S1_mission.json, S5_mc.json, S5_mc.csv | | 72da86ff6b473a41, 2145c2533fa09c18, 9f18d99b185e4077 |
| results/sil_v2p9/S6_aborts.json, S9_pc_transducer.json, S12_bleed.json | | 68600b12dfaa7c4f, 6ba10af7e8c0842e, 102576c2550e1b3b |
| results/fault_path_v3.json (S11 v2.9) / ignition_rule_sil_v1.json (S13) / hbleed_provision_v1.json | | 786c3982616fe7f3 / baff9efcdd49da66 / d9709d1e28dc12d7 |
| hardware/kicad_gen/ecu_design.py (v2.4 generator) | v2.4 | f6c13591f6486cab |
| hardware/kicad/README.md, pin_map_v2p4.csv, intended_netlist.json, argos_ecu_bom_grouped.csv | v2.4 | f69f6fa0af9b6537, 36cba2dc400dda69, 5cd8d6f001b8a345, ddc7c1ab702f140b |
| results/bom_v2p1.csv / bom_v2p1.json | v2.1 | a6353169e3e74ca3 / f754c27fec8c2971 |
| docs/bench_plan_v2.md | v2 | ece8ad4a1465886d |
| REPORT-v2.9-HANDBACK.md | | a7f047b1858f1293 |
| calc/make_interface_json_v2.py | | a67f76f1bfc9176f |
| hub/interfaces/electronics.json | v2 | da067408c1594814 |

**Context, read only:**
- **Interface files:**
  - gnc.json v3: 3e97c378cfebee95.
  - 01-systems-gnc/staging_v3.1/gnc_v3.1_staging.json: 695a069e8fc8dc53.
  - combustion.json v2.3: d9ec54fbf450e243.
  - mechanical.json v2: 4f024ed4ccb4618c.
  - ENGINE-BASELINE-v0.json: 508faa652ccbd539.
  - ICD-AIRFRAME.md: 09c09dcc0916a6fd.
  - SUPERVISION.json: 138e28a5def98d50. I did not edit it.
- **CHANGELOG.md.**
  - First read at 243837e888f55ada (158 lines). Re-read at e2aefd1f62481877 (161 lines).
  - Lines 154–161 were written after the handback (l.153). I treat them as the current baseline.
  - Where v2.9 departs from these lines, the finding is marked "post-handback". These are deltas the author could not have met; they are not errors.
- **REQUIREMENTS.md.**
  - First read at 7826834a2e5b9b08. Re-read at 8e3cb85b87f62aa2, after amendments l.112–114 were added at 10:20Z.
  - Line numbers refer to the current file.
- **Electronics workdir (/home/claude/work/electronics/).**
  - It now holds v2.10 work in progress, which differs from the published v2.9 (for example config.h 036afedfa28b5a35, saved at 10:32Z).
  - I did not review it, and I did not modify it.
  - Every build in this review used copies of the hub-published v2.9 tree. I checked those copies byte for byte against the hub.

**Reviewer artefacts.** All are in hub/reviews/electronics/.

Recomputation:
- re_recompute_v1.py a230a19654d86f02.
- Outputs: re_recompute_v1.json f5e034853d56d95f and re_recompute_v1.txt d25c2799a9e52709.

Probes A–E:
- Driver and build script: re_sil_probe.cpp 44ab24457e1599da; re_build_probe.sh 208d0d9a1054cc0b.
- Variant builds (config.h hash): base 0ba1e1ef0fbce180 (identical to the hub), bpc1 099042ea895b182c, a5off 93dee86bc2e4263f.
- Outputs, as json / txt:
  - A, late light: base f0a2d5aaae1d782b / 915df4a4d4ee0fed; a5off 6ca596f9f52a7738 / df29e5983411e0be.
  - B, pad offset: base e1da1ae58587f83a / 9b4f184250c12b31; bpc1 9d412cc110c2b8d6 / 3a23613bd73e2dc3.
  - C, A1 relight offset: base 4f8bb63cd6585511 / 5dbec00d2272cfd0; bpc1 59126c7b0173a6d8 / 3e4cf0ab846db2ee.
  - D, false E2 and drogue: base 2d8c92b22b7db053 / 71be100233aa5f19; bpc1 36645cc82071c127 / 9b385dcfb53e4bd9.
  - E, coast shift: a8bb89733853ec25 / bd6388299c55c3a0.

Probe F:
- Build script: re_build_ovp5.sh 9b07ece339e1a492. Variants: ovp5 (config.h 34e4e9c85af6081d) and ovp5raw (engine_ecu.cpp 9ef5a9d7f9a1d429).
- re_probeF_s5_ovp.py 78b928f24a8a5bfa; outputs json 81ac9d861fe5d461, txt d2640315d493f067.
- re_probeF_s6_compare.py ea7201d2696e7d8a; outputs json e4baa3a6535cd20e, txt 59ee859734d743fe.

## 2. METHOD

**Reproduction.**
- **Build.** I copied src/ and sil/ to the reviewer scratch and confirmed they are byte-identical to the hub. I rebuilt test_core and sil with the Makefile flags (sil with -DECU_SIL_TEST_HOOKS). The build gave 0 warnings.
- **test_core:** 287 pass, 0 fail, the same as test_core_log.txt.
- **S1, S6, S9 and S12:** re-run with explicit scenario and output arguments. All four outputs are bit-identical to the published JSON.
- **S5:** I re-ran 11 runs singly ('sil mcone k'). They reproduce the published pc_max values and the run-127 abort exactly: PC_OVERPRESSURE at 3.217 s.

**Independent recomputation.** re_recompute_v1.py is my own code, in sections A–J:
- the Pc chain and both over-pressure paths;
- the P_mid comparator;
- the pin-23 ladder decode;
- the TPS552882 and LTC4365 dividers;
- the +12V_ARM and ARM-bus currents;
- bleed closure timing and the filter group delay;
- the A5 race against the light confirmation;
- the A1 coast and re-zero timeline;
- the BASE_AMB false-light windows;
- the BOM audit.

Datasheet values I did not fetch myself are tagged "DATASHEET (as quoted)".

**Targeted SIL probes.**
- **Setup.** The probes are my own driver, linked against the author's unchanged plant and the published core. Variant builds are made from copies.
- **A:** late light. Ignition delay 0.04–0.36 s × hard_start_gain 0, 0.25, 0.5 and 1.0, on the base and a5off builds.
- **B:** a DC offset on Pc at E0, from −0.75 to +0.90 bar. Pad start, lit and unlit, on the base and bpc1 builds.
- **C:** the same at the A1 relight state.
- **D:** offsets of +1.0 to +2.5 bar at the relight. The GNC FC release predicate is evaluated each tick.
- **E:** the A1 coast lengthened to 20.6 s, with a Pc shift injected after the coast re-zero.
- **F:** the 30 bar firmware abort at 5 ms persistence, on the filtered channel and on the raw channel. Applied to the S5 high-overshoot runs and to the full S6 set.

The probes test the firmware logic against the author's plant model. They are not independent physics.

**Constraints.** At most 2 CPU-heavy processes at a time. I wrote nothing outside hub/reviews/electronics/ and my scratch directory, and I edited no hub file.

**Severity scale:**
- **BLOCKING:** a value or behaviour that a gate depends on is wrong or unsupported.
- **MAJOR:** an overstated claim, or a missing dependency that must close before the named gate.
- **MINOR:** a correction with limited effect on gate decisions.
- **NOTE:** an observation.

**Evidence tags:** SIM, DERIVED, ASSUMED, DATASHEET, TO-VERIFY and LITERATURE. I also use DESIGN for the author's own design choices and LEAD for lead decisions.

## 3. RECOMPUTATION TABLE (reviewer vs author)

| # | Quantity | Author | Reviewer | Result |
|---|---|---|---|---|
| R1 | Pc divider factor k_div (12.7k/4.02k into the ADS131M04) | ecu_design.py l.568–570 | 0.238226 at Zin 330 kΩ; 0.238008 at 300 kΩ; 0.240431 unloaded (DERIVED) | agree |
| R2 | ADC clip referred to PC_SIG; resolution | — | 5.037 V, above the 4.75 V valid-window top; 1.051 Pa/count (DERIVED) | headroom OK |
| R3 | FW over-pressure 30 bar abs | config.h l.271–273 | 28.987 bar g = 2.156 V at PC_SIG (DERIVED) | agree |
| R4 | HW comparator trip | 31.47 bar g (ecu_design.py l.362–384) | 31.465 bar g. Electronic band 30.68–32.26 bar g (0.1 % resistors, Vio ±9 mV, DATASHEET as quoted). The band bottom is 1.69 bar above the FW trip. The 070BG TEB of 1.05 bar is common to both paths (DERIVED) | agree; HW always backs up FW |
| R5 | HW path RC; step trip time | τ 5.28 ms | τ 5.283 ms. Ideal steps: 1→45 bar abs 6.64 ms; 1→63 bar 3.74 ms; 25→45 bar 2.47 ms; 25→35 bar 7.28 ms (DERIVED; comparator and latch < 10 µs ignored) | agree; S6 SIM 5.7 ms on the 500 N blocked throat |
| R6 | P_mid comparator | rise 9.86 / fall 8.86 bar g | 9.864 / 8.864; 9.834 with V_OL 0.15 V (ASSUMED). Electronic bands: rise 8.95–10.79, fall 7.93–9.80. With the 170BG TEB of 2.55 bar: rise 6.40–13.34, fall 5.38–12.35 bar g (DERIVED). P_mid with both valves open is NOT PUBLISHED (TO-VERIFY) | agree; purge level open (RE-10) |
| R7 | Pin-23 ladder | mv_ladder_table.h | Nominal ratios reproduced. OPEN+CLOSED decodes VALID. Any ratio in [0.02, 0.348) decodes as VALID OPEN+CLOSED+P_mid-high; that is a 1.1–4.3 kΩ short to GND. Leaks to GND of 72.5 / 70.9 / 121.8 kΩ flip the coast-closed, burn-open and R0-only codes. τ ≤ 0.99 ms; settling 4.1 ms (DERIVED) | values agree; plausibility gaps (RE-19) |
| R8 | TPS552882 output | 7.49 V | 7.4905 V, using the author's 1.2 V reference (TO-VERIFY). The sim.h l.62 comment divider gives 7.483 V and is stale | agree |
| R9 | LTC4365 OV / UV | OV 8.20 V; UV 5.05 V | OV 8.20 V, band 8.062–8.339 V (DERIVED; DATASHEET as quoted). The band top equals the 8.34 V jam failure case (REQUIREMENTS l.111) to within 1 mV. The band bottom is 0.571 V above 7.49 V. UV band 4.955–5.137 V on an ASSUMED 0.5 V threshold. The firmware rail-lost limit of 5.5 V sits above it | agree; no bench test (RE-13) |
| R10 | Pc filter group delay | LowPass2 50 Hz | 4.466 ms at DC (DERIVED; filters.h replicated) | — |
| R11 | Bleed closure confirmation, E0 → V1 confirmed | bench plan l.108: 76–106 ms at 1.0 mm | 78.7–108.7 ms at 1.0 mm (includes 2.4 ms ladder settling); 90.7–120.7 ms at 0.8 mm; 116.6–146.6 ms at 0.6 mm. Valve closing 50–80 ms (DATASHEET as quoted, BOM item 208) (DERIVED) | agree at 1.0 mm; 11–41 ms margin to the 0.12 s pass |
| R12 | A5 against the 10-tick light confirmation | — | Largest first-order rise τ for which A5 trips before E2: never for 8.5–10 bar abs targets; 1.25 ms at 12; 2.75 ms at 15.85; 4.5 ms at 20; 8.75 ms at 25; 11.25 ms at 30 bar abs (DERIVED) | A5 pre-empts E2 only on fast, large rises |
| R13 | A1 coast and re-zero | — | Burn-off to burn-on 20.599 s (gnc.json v3 DC-A1). The re-zero ends 18.3–19.4 s before T_fire. Drift allowance left: 0–0.10 bar. At the author's 0.01 bar/K about 10 K exhausts it (DERIVED / TO-VERIFY) | the SIL tests a 2.6 s coast (RE-07) |
| R14 | Relight worst case | 0.81 / 1.37 s; GNC plans 0.81 / 1.41 s | direct 810 ms; prep path 1370 ms; purge integrated 3310 ms (DERIVED) | agree |
| R15 | BASE_AMB false-light window for a DC offset δ at P0 | handback l.136: "S13 B showed no failure" | Base build: 0.70 ≤ δ ≲ 1.0 bar. After B-PC-1: 0.58 / 0.56 / 0.49 ≤ δ ≲ 1.0 bar for an unlit rise c = 0.41 / 0.43 / 0.50 bar (DERIVED). The upper edge is the torch gate at 1 bar g | DIFFERS (RE-02) |
| R16 | Torch flow's contribution to main Pc before E1 | — | ≤ 0.064 bar. This is a choked upper bound from combustion.json: 0.594 g/s, c* 1586 m/s (DERIVED) | cannot explain P0 > 0.4 bar |
| R17 | +12V_ARM boost input current | "TO-CHECK/OPEN" (electronics.json l.2607) | Purge, both coils, 2 × 16 W: 4.4–5.7 A; at 2 × 21 W: 5.8–7.5 A. E0 overlap of V2 + torch: 5.5–7.2 A; adding a roll pair: 8.0–10.4 A; adding the spark dwell peak: 12.1–15.7 A (DERIVED; VIN 6.6–8.1 V; η 0.85–0.90 ASSUMED). Limits: 6 A prolonged / 7 A for seconds / 10 A per cycle (DATASHEET as quoted, ecu_design.py l.466) | EXCEEDS (RE-09) |
| R18 | ARM_BUS current at PURGE entry | — | 14.5–22.8 A: MV opener stall 9.2 A (DATASHEET) or 10.4 A (ASSUMED), pintle rail 0–4.33 A, boost and latch. F301 is 15 A; fuse I²t TO-VERIFY (DERIVED) | EXCEEDS rating (RE-09) |
| R19 | Purge duration and mass | 2.5 s plus a hold of up to 2.0 s, "≤ 40 g at 20 g/s" (config.h l.603–604); S12 79.3 g; bench plan l.111 about 79 g | Up to 4.5 s in PURGE (DESIGN). At Combustion's total flow of about 31.25 g/s (CHANGELOG l.159): about 78 g at 2.5 s and 141 g at 4.5 s (DERIVED, constant flow). The plan is ≤ 76 g (l.160 (5)) | DIFFERS (RE-05) |
| R20 | BOM v2.1 | 194 rows TO-QUOTE | 229 rows: 194 TO-QUOTE, 3 CATALOGUE, 32 no-purchase. No zero prices and no "from" prices. 197 delivered rows TO-QUOTE to DK-6400. 87 rows with MPN TO-SELECT. 5 N2O-wetted rows, of which 1 has an O2-clean note (DERIVED) | ENG-14 met; RE-14, RE-22 |
| R21 | S5 high-overshoot runs with the FW abort at 3 ms filtered / 5 ms filtered / 5 ms raw | "1 PC_OVERPRESSURE" (handback l.69) | 11 of 300 runs reach plant Pc 29.5–30.0 bar abs on the 100→500 N step, against the 25 bar cap. Run 127 (plant 30.005 bar abs, 4 ms above 30; read as 30.075 with a span error of +0.21 %) aborts in all three variants, at 3.217 / 3.219 / 3.215 s. Run 12 (plant 30.014, 5 ms above 30) does not abort because its span error is −0.47 % (SIM) | 5 ms does not remove it (RE-04) |
| R22 | S6 with 5 ms persistence | — | No pass/fail change in the 58 cases. Blocked throat 70 % in RUN: FW 17 ms vs comparator 15 ms on the filtered channel; FW 13 ms vs 15 ms on the raw channel. 500 N blocked throat: comparator first at 5.7 ms (filtered); FW and HW both abort at 8 ms (raw) (SIM) | supports l.160 (2) on the filtered channel only (RE-20) |

## 4. FINDINGS

| ID | Severity | Title | Gates |
|---|---|---|---|
| RE-01 | BLOCKING | A5 is still an abort, and the late-light spike that decides it is not in the SIL (post-handback) | SIL/HIL freeze; IGN-1; first static fire; A1 |
| RE-02 | BLOCKING | The BASE_AMB high-side fallback turns a positive Pc offset into a false light | SIL/HIL freeze; B-PC-1 (kBpc1Shown); IGN-1; A1 |
| RE-03 | BLOCKING | Drogue hold bit b7 is not on the filtered channel only (post-handback) | SIL/HIL freeze; HIL/B-FC-1; A1 |
| RE-04 | BLOCKING | S5 up-step overshoot reaches the 30 bar abort; 5 ms persistence does not remove it | SIL/HIL freeze; first static fire; B1; A1 |
| RE-05 | BLOCKING | Bleed logic and hardware do not match the purge/bleed decisions of l.160–161 (post-handback) | SIL/HIL freeze (A1 build); B-BLEED-1; A1 |
| RE-06 | MAJOR | The Teensy HAL does not exist, and safety functions are assigned to it | B-PC-1 (flight ECU); HIL; first static fire |
| RE-07 | MAJOR | Coast re-zero and vented check untested over the real A1 coast; a 0.11 bar drift loses the relight | B-PC-1; A1 |
| RE-08 | MAJOR | An invalid case TC silently disables the case abort and the relight refusal | first static fire; A1 |
| RE-09 | MAJOR | +12V_ARM and ARM bus over rating in purge and E0 overlaps; peak-and-hold not designed | B-PWR-2; B-BLEED-1; A1 |
| RE-10 | MAJOR | Closure deadline rests on an assumption the listed valve contradicts; P_mid purge level unpublished | B-BLEED-1; A1 |
| RE-11 | MAJOR | The SIL Monte Carlo fixes the inputs the start logic is most sensitive to | SIL/HIL freeze |
| RE-12 | MAJOR | Stand A7 start band (6.89 bar abs) vs Combustion's pool (> 6.9 bar for up to 0.41 s) | first static fire |
| RE-13 | MAJOR | Bench plan v2 lacks measurable pass criteria | every bench gate; IGN-1 |
| RE-14 | MAJOR | BOM v2.1 lacks the bench equipment and bleed plumbing | CF-3; B-PC-1; B-BLEED-1 |
| RE-15 | MAJOR | ERC 0/0 shows self-consistency only; checks needed before board build | board build for B-PC-1 |
| RE-16 | MAJOR | electronics.json v2 publishes stale and wrong entries | interface freeze for SIL/HIL |
| RE-17 | MINOR | No lower tank-temperature bound (15 °C) | first static fire; B1; A1 |
| RE-18 | MINOR | Propane backstop acts on one raw sample | B-IGN-1; A1 |
| RE-19 | MINOR | Ladder decode accepts impossible and degraded states as valid | B-BLEED-1; HIL |
| RE-20 | MINOR | 30 bar abort channel: decision says raw, firmware uses filtered | SIL/HIL freeze |
| RE-21 | MINOR | Handback overstatements and provenance | next checkpoint |
| RE-22 | MINOR | BOM: O2-clean notes and medium-temperature classes of wetted parts | B-BLEED-1; procurement |
| RE-23 | MINOR | S5 response metrics not traced to the amended ENG-03 | B-PNT-1; SIL/HIL freeze |
| RE-24 | MINOR | S6 gimbal_jam_moving_cmd is still an open FIX | SIL/HIL freeze; B-TVC-1 |
| RE-25 | MINOR | Record hygiene (log markers, stale comments, Makefile header) | next build |
| RE-26 | NOTE | A7 has no rate criterion (reasoned) | — |
| RE-27 | NOTE | TLM_FAST has no application CRC; b4 persists through ABORT | HIL |
| RE-28 | NOTE | In-flight MCU reset: recovery path undefined | HIL; A1 |
| RE-29 | NOTE | Stale cross-discipline entries (not owned by Electronics) | lead |

### RE-01 (BLOCKING). A5 is still an abort, and the late-light spike that decides it is not in the SIL.

**Gates:** SIL/HIL freeze; IGN-1; first static fire; A1. Post-handback.

**Evidence.**
- **What the firmware does.**
  - A5 aborts HARD_START when filtered Pc exceeds 8.0 bar abs for 5 ms in IGNITION after the lift command (engine_ecu.cpp l.762–764; config.h l.305–306).
  - electronics.json l.309 still shows the disposition as "OPEN".
- **What the lead decided.**
  - A5 is deleted as an abort, in flight and on the stand. A LIGHT_SPIKE log event replaces it.
  - OI-A5-LATE closes when this is implemented and S6 passes (CHANGELOG l.160 (1); REQUIREMENTS l.112).
- **Probe A (SIM; re_probeA_late_light_*.txt).**
  - With gain ≤ 0.25, no case aborts, even for a light 0.403 s after E0.
  - With gain 0.5, ignition delays ≥ 0.12 s abort HARD_START.
  - With gain 1.0, delays ≥ 0.06 s abort (light 0.133 s after E0).
  - In every aborted case A5 is the only trigger.
  - The plant peak is the same with and without A5: for example 28.73 bar abs at gain 1.0 / 0.25 s, and 30.45 bar abs at gain 1.0 / 0.36 s, in both builds. A5 reacts to the spike; it does not limit it.
  - With A5 disabled, every case reaches RUN. Filtered Pc stays ≤ 26.15 bar abs, so the 30 bar abort never trips. The transducer model reads up to 43.0 bar on the sense-line overshoot.
- **The boundary rests on an assumption.**
  - Where starts change from "run" to "abort" depends on the ASSUMED spike gain (plant.h l.70–71: ign_delay 0.100 s, hard_start_gain 0).
  - S5 and S13 never disperse either input (sil_main.cpp l.427–448).
  - Combustion's grid has A5 tripping on 98 % of 5400 rows, 7.4–11.7 ms after light (CHANGELOG l.159).
  - The SIL plant has no pool or fast part (handback l.114), so the SIL cannot show this.
- S6 hard_start_0p20s and hard_start_0p25s fail (HARD_START 0.283 s and 0.331 s after injection). These are the OI-A5-LATE cases.

**Required action:**
1. Implement l.160 (1) in both modes. Add LIGHT_SPIKE to the log and the EVENT stream: raw and filtered peak, time above 8 and above 30 bar abs, and time from light. Update the electronics.json abort matrix and l.309, and bench plan l.166.
2. Re-run S6. Both hard_start cases must reach RUN with no abort, and every other cause and time must stay unchanged.
3. Add Combustion's pool and fast-part source to the SIL plant; this is the replay requested in l.160 (3). Disperse spike gain and ignition delay (RE-11). Report the LIGHT_SPIKE statistics and the 30 bar and A7 behaviour on that source.

### RE-02 (BLOCKING). The BASE_AMB high-side fallback turns a positive Pc offset into a false light.

**Gates:** SIL/HIL freeze; B-PC-1 (the kBpc1Shown switch); IGN-1; A1.

**Evidence.**
- **The rule.**
  - If |P0| exceeds kIgnBaseCheck (residual + 0.1 bar: 0.7 bar now, 0.4 bar with kBpc1Shown), P0 is replaced by ambient, P0 := 0 (engine_ecu.cpp l.134–135; config.h l.544–546).
- **Basis.**
  - Combustion and the lead require only that the baseline be "checked against auto-zero ambient" (CHANGELOG l.133, l.134). Neither says what to do when the check fails, and ENG-04 has no fallback (REQUIREMENTS l.52).
  - electronics.json l.3022–3023 nevertheless tags the whole rule, fallback included, as "LEAD/COMB". The handback calls the clamp option a LEAD choice (l.136).
  - The direction of the fallback is therefore an Electronics DESIGN choice that carries a LEAD/COMB tag.
- **Direction.**
  - config.h l.536 notes that "a pure offset after the zero cancels in the rise". Setting P0 := 0 removes that cancellation exactly when the offset is large.
  - For false lights a high P0 is the conservative case; zeroing it lowers the bar.
- **Arithmetic (R15).**
  - A false E2 needs δ > check and δ + c ≥ max(0.8 bar, floor − 1.013 bar).
  - The resulting window is 0.70 to about 1.0 bar on the base build, and 0.49–0.58 to about 1.0 bar after B-PC-1.
- **Probes B and C (SIM).**
  - Base build, δ ≤ +0.69 bar: correct (lit → RUN; unlit → NO_IGNITION).
  - Base build, δ ≥ +0.71 bar: BASE_AMB, a false E2, then FLAMEOUT 19 ms later, for lit and unlit starts alike.
  - The lit start is lost because E2 comes before the real light. At the A1 relight, +0.71 bar gives E2 at E0 + 0.099 s and the abort at E0 + 0.118 s, before the plant has lit.
  - bpc1 build, +0.41 and +0.45 bar: BASE_AMB without a false light; the 2.0 bar floor holds.
  - bpc1 build, ≥ +0.60 bar: false E2 and FLAMEOUT, lit and unlit (filtered max 2.04 bar abs).
  - −0.75 bar: PC_SENSOR, as intended.
- **Coverage.**
  - S13 B ran only ±0.3 and ±0.6 bar, and only on the base build (sil_main.cpp l.1998–2110). None of these exceeds the 0.7 bar check, so the fallback was never exercised.
  - Handback l.136 ("S13 B showed no failure") and l.88 ("cannot be contaminated, because there is no main N2O before E1") therefore overstate. A Pc offset needs no N2O: EMI, ground shift, drift or a sensor fault can produce one.
  - The S9 +TEB disposition, "B-PC-1 closes them through the 2.0 bar floor" (handback l.104–107; bench plan l.63–64), holds for +1.034 bar. It does not hold for 0.49–1.0 bar on the bpc1 build.
- **Credible offset sources.**
  - Torch flow cannot raise P0 that far: at most 0.064 bar (R16).
  - The credible sources are EMI and ground shift during [E1 − 20 ms, E1], when the spark is running (from E0 + 0.02 s, for 0.5 s); transducer drift; and a tap near the torch jet. None is bounded yet.
- The drogue was not released in any probe (C-15).

**Required action:**
1. **LEAD decision on the fallback.** Reviewer proposal, one-sided:
   - P0 > +check: keep P0, or refuse the lift with PC_SENSOR. Never declare E2 on ambient.
   - P0 < −check: set P0 := 0.
   - Until the lead decides, retag the rule as DESIGN.
2. **Extend S13 B.** Run both builds, pad and A1 relight, lit and unlit, with offsets from −0.8 to +1.2 bar in 0.05 bar steps. Acceptance:
   - no false E2;
   - every lit start reaches RUN;
   - every unlit start ends NO_IGNITION or TORCH_FAULT.
3. Correct handback l.88 and l.136 and the S9 disposition.
4. B-IGN-1 must bound the DC shift of filtered and raw Pc during the spark (RE-13).

### RE-03 (BLOCKING). Drogue hold bit b7 is not on the filtered channel only.

**Gates:** SIL/HIL freeze; HIL/B-FC-1; A1. Post-handback.

**Evidence.**
- **Decisions.**
  - The lead set b7 on the FILTERED channel only, so that a raw dip cannot clear it (CHANGELOG l.156).
  - The adopted FC predicate (l.161 (1); REQUIREMENTS l.114) is: RELEASE iff (d1 & 0x0F) = RUN AND b4 AND [(d2–d3 ≠ 0xFFFF AND ≥ 300 kPa abs) OR b7], latched.
- **Firmware.**
  - rise_now is filtered AND raw over P0, and b6/b7 derive from it (engine_ecu.cpp l.149–163, especially l.157; types.h l.218–221).
  - One raw tick below P0 + 0.8 bar clears b6 and prevents b7.
- **The old rule is still written down.**
  - Bench plan B-FC-1 l.136: "With the dip, b6 clears and b7 never sets".
  - electronics.json l.3108: "b5 rise now (filtered AND raw over P0)".
- **Consequence.** Without b7, release waits for Pc ≥ 3.0 bar abs. The fuel-starved plateau can delay that by up to about 0.4 s, which GNC prices at −21/+6, p 0.006, with 2 crashes (CHANGELOG l.141).

**Required action:**
1. Compute b7, and b6 if it feeds b7, from the filtered rise only. Keep E2 on filtered AND raw.
2. Add a test_core case: a 1–3 ms raw dip after E2 must not clear b7; a filtered drop below the rise threshold must.
3. Update B-FC-1 l.136, electronics.json l.3108 and the TLM_FAST description.

### RE-04 (BLOCKING). S5 up-step overshoot reaches the 30 bar abort; 5 ms persistence does not remove it.

**Gates:** SIL/HIL freeze; first static fire (step tests); B1; A1.

**Evidence.**
- **Requirements.** Normal Pc ≤ 25 bar, with the abort at about 30 bar (ENG-09, l.60). Pc is capped at 25 bar in software (ENG-01, l.49). The setpoint peaks at exactly 25.000 bar abs.
- **Published S5.**
  - Overshoot p50 14.7 %, p95 25.0 %, max 26.5 %.
  - Plant Pc max p50 27.59, p95 29.33, max 30.014 bar abs.
  - 1 PC_OVERPRESSURE in 300 runs (run 127). The handback lists it (l.69) without a disposition, and v2.8.3 had the same result.
- **Probe F (SIM; re_probeF_s5_ovp.txt).**
  - All 11 runs with plant Pc ≥ 29.5 bar abs come from the 100→500 N up-step (overshoot 24–26.5 %).
  - Run 127 aborts with the published 3 ms (3.217 s), with 5 ms on the filtered channel (3.219 s) and with 5 ms on the raw channel (3.215 s).
  - Run 12 survives only because its span error is −0.47 %.
  - At this corner the outcome is decided by the ASSUMED ±0.5 % span error.
- **Mechanism (SIM, run 127 trace).**
  - The setpoint slews at 250 bar/s (config.h l.214) and reaches 25 bar at 3.08 s. At that moment the slew-limited pintle is 1.54 mm behind its command (x 0.765 mm against x_cmd 2.303 mm).
  - The proportional term on the reference-model error then drives the command to 2.79 mm, against a settled lift of about 1.65 mm (run 12). The pintle reaches 2.51 mm at 3.20 s.
  - The integrator is held during the transient (control.cpp l.150–156), so this is proportional overdrive against a slower actuator, not integral windup.
  - The pattern is consistent: 9 of the 11 runs have reg_scale ≥ 1.25 (drawn 0.6–1.5), and all 11 have servo speed_scale ≤ 0.954 (drawn 0.85–1.0).
- **Consequence.** In flight, a PC_OVERPRESSURE abort on a nominal throttle-up loses the vehicle. 11 of 300 runs have 0–0.5 bar of margin.

**Required action:**
1. Disposition run 127 and the overshoot tail. Target: nominal-profile plant Pc ≤ 28 bar abs at p99.9, or a lead-accepted margin that covers the ±0.5 % span error. Possible means:
   - limit the lift command to the map lift at the setpoint (plus a margin) while the reference is travelling; or
   - use a lift-rate-aware reference model; or
   - reduce the slew above about 80 % thrust.
2. Re-run all 300 S5 runs and the 11 probe-F runs. Acceptance: no PC_OVERPRESSURE on the nominal profile.
3. B-PNT-1 must measure servo speed and torque under load. speed_scale is ASSUMED at 0.85–1.0; feed the measured values back into S5.

### RE-05 (BLOCKING). Bleed logic and hardware do not match the purge/bleed decisions of l.160–161.

**Gates:** SIL/HIL freeze (A1 build); B-BLEED-1; A1. Post-handback. It does not apply to B1, B2, C or D while kHbleedFitted is false (config.h l.602).

**Evidence.**

(a) **Unconfirmed closure.**
- If V1 is not confirmed closed by E0 + 0.15 s, the relight aborts BLEED_FAULT, in flight and on the stand (engine_ecu.cpp l.249–256; config.h l.594–598). The lift itself waits for the confirmation (engine_ecu.cpp l.1194–1195).
- The lead now requires that "if closure is not confirmed before E1 the relight proceeds and BLEED_FAULT goes to the FC" (l.160 (5)).
- S12 pmid_chain_dead_after_bit shows what v2.9 does instead: one dead P_mid chain gives BLEED_FAULT at E0 + 0.151 s, and the relight is lost.
- "Before E1" is ambiguous in v2.9, because E1 itself waits for the closure.

(b) **Hardware inhibit.**
- Required: bleed drivers hardware-inhibited outside the scheduled purge window (l.160 (5)).
- In v2.4, V1 and V2 are gated only by ARM (OE_ARM_N, +5V_ARM, +12V_ARM) and the watchdog (ecu_design.py l.532–539). V1 also shares pin 15 with the heater permit (l.3–4, l.67).
- A firmware or pin fault during ascent can therefore open both valves.

(c) **Purge cap and mass.**
- Required: ≤ 76 g per purge, total flow about 31 g/s, and an ECU-enforced hard cap on purge duration (l.160 (5); l.161 (4)).
- v2.9: PURGE lasts 2.5 s plus a hold of up to 2.0 s with both valves open (config.h l.603–604, commented "≤ 40 g at 20 g/s"; engine_ecu.cpp l.1289–1293).
- At 31 g/s that is about 78 g for the purge and about 140 g with the full hold (R19). S12 (79.3 g) and bench plan l.111 are already above 76 g.

(d) **Valve.**
- BOM item 208 is a Burkert 6027 HP with a 1.0 mm orifice.
- The lead requires each valve to have at least 4× the restriction's flow capacity (seat ≥ 2 mm, or Kv verified at 55 bar). The lead states that the 6027 HP 1.0 mm does not qualify, and requires a 12 V NC valve with peak-and-hold (l.160 (6)).
- The listed coil is 16–21 W, and the product page gives 24 V (CHANGELOG l.152).

(e) **Driver.**
- Each coil channel is a low-side DMN6075S with an SS14 + SMAJ24A fast-release clamp (BOM items 37, 38, 90).
- A PWM hold through a 24 V clamp dumps coil energy into the TVS every cycle: about 2–3 W at a 0.3 A hold (DERIVED).
- Peak-and-hold needs a slow-decay path during hold that is switched out at release.

**Required action:**
1. Implement the flight rule: closure not confirmed by the deadline → the lift proceeds, BLEED_FAULT goes to the FC, and V2 closes. Keep the stand abort. Agree with the lead whether E1 waits for the closure up to a deadline ≤ the torch gate. I recommend yes, then proceed.
2. Add a hardware purge-window enable, for example an FC enable line ANDed in U304/U307, or a hardware one-shot. Exercise it in S6 and S12 fault cases.
3. Set the hard cap from GNC amendment (a), and size kPurgeHoldMax_s so that the worst purge stays ≤ 76 g at the flow measured in B-BLEED-1. Alternatively, close the valves during the hold.
4. Replace item 208 with a qualifying 12 V NC valve. Its medium-temperature class must cover flashing N2O. Design peak-and-hold with fast release (RE-09).
5. Re-run S11 and S12.

### RE-06 (MAJOR). The Teensy HAL does not exist, and safety functions are assigned to it.

**Gates:** B-PC-1 with the flight ECU; HIL; first static fire.

**Evidence.**
- The Makefile says "The Teensy HAL and its PlatformIO project are NOT written yet (open item)" (Makefile l.1–3).
- The design assigns these functions to the HAL:
  - the pin-15 heater/V1 OR (ecu_design.py l.3–4: "the HAL ORs both");
  - the four 4 kSPS raw Pc codes per millisecond (engine_ecu.cpp l.1483);
  - the ADC, TC, encoder and 1-Wire drivers;
  - CAN framing;
  - the watchdog kick;
  - the non-volatile lockout record (types.h l.149–150, l.306–308).
- The handback unknowns (l.109–116) and the bench plan do not mention the HAL.
- B-PC-1 needs the flight ECU (bench_plan_v2.md l.53–54).

**Required action:**
1. Make the HAL an open item with an owner and a test plan. Implement it before B-PC-1.
2. Specify the pin-15 exclusivity in the HAL and test it in HIL: heater only in SAFE with the ARM bus off; V1 only with the ARM bus on and inside the purge window.
3. Add HIL tests of the watchdog, the NV lockout and CAN timing.

### RE-07 (MAJOR). Coast re-zero and vented check untested over the real A1 coast; a 0.11 bar drift loses the relight.

**Gates:** B-PC-1; A1.

**Evidence.**
- **The rule.** The coast re-zero runs at COAST + 1.0 s over 200 samples. It is accepted if the span is ≤ 0.05 bar and the shift ≤ 0.30 bar (config.h l.556–570, marked "LEAD to confirm"). RELIGHT is refused NOT_VENTED if |Pc gauge| ≥ 0.1 bar (config.h l.247).
- **Timeline (R13).**
  - The re-zero ends 18.3–19.4 s before T_fire, leaving 0–0.10 bar of drift allowance.
  - At the author's estimate of 0.01 bar/K (config.h l.558; TO-VERIFY), about 10 K of transducer warming uses it up.
- **SIL coverage.** The SIL A1 relight uses a 2.6 s coast (sil_main.cpp l.1936–1960: t_meco 2.40 s, t_rl 5.00 s).
- **Probe E (SIM, 20.6 s coast, shift applied at COAST + 2.0 s).**
  - +0.05 and +0.09 bar: the relight proceeds.
  - +0.11, +0.15 and −0.11 bar: refused NOT_VENTED.
  - There is no retry (REQUIREMENTS l.103), so a refusal means A1 is lost.

**Required action:**
1. B-PC-1: measure the zero TC and the 20 s drift. Mechanical to supply the transducer temperature from MECO to RELIGHT.
2. Lead to confirm the re-zero and choose a policy: a second re-zero near T_fire with an independent leak indicator; a wider limit; or NOT_VENTED as a flag in flight.
3. Add a SIL case with the 20.6 s coast and drift steps.

### RE-08 (MAJOR). An invalid case TC silently disables the case abort and the relight refusal.

**Gates:** first static fire; A1.

**Evidence.**
- The case-TC monitors count valid TCs only:
  - the case abort (engine_ecu.cpp l.826–836);
  - the relight refusal, caseHot (engine_ecu.h l.179–181; engine_ecu.cpp l.375);
  - the ARM check (engine_ecu.cpp l.565–566).
- Nothing requires a case TC to be valid.
- Other monitors fail safe:
  - bay invalid is treated as hot (engine_ecu.h l.182);
  - tank invalid is treated as hot (engine_ecu.cpp l.399, l.554);
  - an invalid torch transducer refuses ARM (l.562);
  - ARM needs the pintle encoder (l.568).
- With both case TCs open the engine arms, fires and relights with no case protection. The case limits come from Mechanical: 448.15 K / 0.2 s, and relight refused above 433.15 K (REQUIREMENTS l.108).
- No test covers this: S6 has only case_over_temp_455K and case_445K.

**Required action:**
1. Lead and Mechanical to set a policy. Suggested:
   - require both case TCs valid at ARM;
   - continue on one TC if the other is lost;
   - if both are lost: abort on the stand; in flight, flag and refuse or accept explicitly.
2. Add S6 cases with one and with two invalid case TCs in ARMED, RUN and COAST.

### RE-09 (MAJOR). +12V_ARM and ARM bus over rating in purge and E0 overlaps; peak-and-hold not designed.

**Gates:** B-PWR-2; B-BLEED-1; A1.

**Evidence.**
- **Loads.** The U3V70F12 feeds the spark coil, the torch solenoids, the roll pairs, the MV latch and V1/V2 (ecu_design.py l.463–470, l.488–496, l.538–539).
- **Currents.** R17 and R18 exceed the converter limits and F301.
- **Stale published budget.**
  - electronics.json l.406–408 and README l.128 still carry the v2.3 budget: "coil ≤ 0.75 A, ~9 W … inside budget if not overlapping".
  - electronics.json l.2607 still marks arm_bus_peak_vs_F301 as OPEN.
- **B-PWR-2 coverage.**
  - The test holds the bleed coils with the MV latch and the torch valves (bench_plan_v2.md l.35–37).
  - It omits the spark and the roll pairs, and it does not fix VIN at the 6.6 V worst case.
  - It does not measure R_src or R_branch against the 15 / 20 mΩ assumptions (REQUIREMENTS l.90; config.h l.630–631).
- **Brown-out.** A brown-out at E0 can reset the MCU (RE-28).
- **New valve.** A valve with a ≥ 2 mm seat at 55 bar will probably need more coil power (TO-VERIFY).

**Required action:**
1. Publish a time-resolved budget at VIN 6.6 V for PURGE, E0 and the spark train. Then either sequence the loads (no roll pulses or spark dwell during pull-in) or add converter capacity.
2. Design a peak-and-hold driver with fast release. Size the TVS for the release energy.
3. Extend B-PWR-2 to all overlaps at 6.6 V and 8.1 V, the U3V70F12 input current and output droop, F301 I²t, and R_src / R_branch.
4. Correct electronics.json l.406–408, l.2604 and l.2607, and README l.128.

### RE-10 (MAJOR). Closure deadline rests on an assumption the listed valve contradicts; P_mid purge level unpublished.

**Gates:** B-BLEED-1; A1.

**Evidence.**
- **The assumption.** config.h l.606 sets the 0.15 s deadline on "valve close ≤ 0.03 s ASSUMED". The listed valve's datasheet gives 50–80 ms (item 208; bench plan l.108). Nominal S12 uses ASSUMED times of 15/20 ms.
- **Margins.** Recomputed closure times are in R11. At 1.0 mm the margin is 11–41 ms to the 0.12 s pass and 41–71 ms to the 0.15 s deadline.
- **Final path undefined.**
  - The lead now requires restrictors at each tap, summing to a 1.0 mm equivalent, and valves with ≥ 4× the restriction's capacity (l.160 (6)).
  - Where P_mid sits relative to the restrictors sets its vent time.
  - mechanical.json v2 has no bleed content.
- **P_mid during the purge.**
  - The comparator must read HIGH during the purge (path proof by 0.10 s, config.h l.605). With the 170BG TEB, the rise threshold lies anywhere in 6.40–13.34 bar g (R6).
  - P_mid with both valves open is not published.
  - A level inside that band would give a false "path not proven": a flag in flight, BLEED_FAULT on the stand.

**Required action:**
1. With Mechanical, publish the topology: restrictor positions, the mid volume (≤ 0.5 cm³ per the ICD) and the V2 vent path. Recompute P_mid in the purge and the closure time with the new valve.
2. Set the deadline and the bench pass from that result. Correct config.h l.606.
3. B-BLEED-1 acceptance criteria are in §9.

### RE-11 (MAJOR). The SIL Monte Carlo fixes the inputs the start logic is most sensitive to.

**Gates:** SIL/HIL freeze.

**Evidence.**
- **Spike and light delay.** ign_delay and hard_start_gain are fixed (plant.h l.70–71), and mcConfigs does not draw them (sil_main.cpp l.427–448). In probe A, the abort boundary moves from "never" at gain ≤ 0.25 to 0.06 s at gain 1.0.
- **Start plateau and pool.** No fuel-starved plateau or pool is modelled (handback l.114).
  - Combustion predicts 2.66–3.11 bar abs for 0.1–0.4 s at the A1 state (l.133), and a pool > 6.9 bar for up to 0.30–0.41 s (l.159).
  - The SIL A1 lit Pc is about 2.39 bar abs.
- **Tank temperature.** T_tank0 is drawn U(17, 23) °C (sil_main.cpp l.436); the ARM range is 15–24 °C (REQUIREMENTS l.106).
- **A1 coast.** 2.6 s in the SIL against 20.6 s (RE-07).
- **Bleed valve times.** ASSUMED in S12 (RE-10).
- **Consequence.** The S13 results — 0 light-rule aborts in 273 runs and 0/300 unlit false lights (l.150) — hold only for these fixed inputs.

**Required action:** add the pool / fast-part source; disperse spike gain and light delay; draw T_tank0 from U(15, 24) °C; use the 20.6 s coast and datasheet valve times. Re-run S5, S12 and S13 against the same acceptance numbers.

### RE-12 (MAJOR). Stand A7 start band (6.89 bar abs) vs Combustion's pool.

**Gates:** first static fire.

**Evidence.**
- **The band.** At the ignition lift, the top of the A7 START band is 1.30 × max(Pc_map, 5.3 bar abs) = 6.89 bar abs (config.h l.320–323; engine_ecu.cpp l.200–204). Out of band for 50 ms gives a PC_SENSOR abort on the stand; in flight it is a flag (l.214–217).
- **The pool.** Combustion's pool holds Pc above 6.9 bar for up to 0.30 s at the A1 state and 0.41 s at 26.6 g (l.159).
- **The lead's position.** The lead keeps this as "a nuisance abort" on the stand (l.160 (3)).
- **Consequence.** If the pool is common, stand starts end in PC_SENSOR and T1 may never reach RUN. The rate is unknown because the SIL has no pool (RE-11).

**Required action:** replay the pool in the SIL and report the stand trip rate. If it is material, the lead re-decides before T1: blank the stand START high side from E2 to E2 + 0.45 s, as in flight, or raise kA7StartHiAbs.

### RE-13 (MAJOR). Bench plan v2 lacks measurable pass criteria.

**Gates:** every bench gate; IGN-1.

**Evidence, item by item.**
- **IGN-1 (l.156–170).** "Evidence wanted" only, with no pass criteria. The A5 item (l.166) is obsolete (RE-01).
- **B-IGN-1 (l.119–122).** The only pass criterion is "no 0.8 bar rise during the spark". Missing:
  - the DC shift of filtered and raw Pc during the spark, measured against the 0.7 / 0.4 bar check (RE-02);
  - the same shift against the A3 margin. The spark stops at E2 (config.h l.387), so a spark-induced shift in P0 lowers Pc − P0 in RUN. First-order, the tolerable shift is 0.03–0.3 bar depending on where the A3 minimum falls (DERIVED);
  - single-sample raw spikes against the 4.0 bar abs propane backstop (config.h l.249; RE-18);
  - EMI on P_torch, on the pin-23 ladder and on the P_mid comparator during the closure window E0 to E0 + 0.15 s, which overlaps the spark.
- **Threshold tests.** No test of the HW comparator (30.68–32.26 bar g) or of the LTC4365 thresholds (8.06–8.34 V OV; 4.96–5.14 V UV).
- **B-PWR (l.29–37).** No measurement of R_src or R_branch (REQUIREMENTS l.90), and an incomplete load set (RE-09).
- **B-PNT-1 (l.76–89).**
  - It says "at least 5 F_max/s (2500 N/s)" without a direction. Amended ENG-03 sets closing ≥ 2500 N/s and opening ≥ the HV69 rate map (l.51).
  - It lacks the REQUIREMENTS l.88 items: travel ≥ 103°; unpowered spring closing at the MEOP-equivalent load; guide μ ≤ 0.20; break-out after a dwell; closing time at 25 bar; HV69 torque-speed at 7.335 and 7.49 V; closed-loop t10–90 ≤ 100 ms under load; N2 leak test at 5 and 70 bar.
- **B-TVC-1 (l.91–94).** FRF and jam threshold only. Missing:
  - from REQUIREMENTS l.89: K_s at 6.6 and 7.4 V with the ~100 N·m/rad contingency criterion; damping; J_int; the rotor/structure split; stall-hold heating;
  - the ENG-07 slew ≥ 100°/s at 7° and 7.4 V;
  - the ENG-07d notch frequencies.
- **B-PC-1 (l.52–64).** No statistic, pressure points, cycle count or temperature range is stated. No zero TC or drift measurement (RE-07).
- **B-BLEED-1 (l.96–117).** Based on 1.0 mm. No comparator pass band, no temperature range, no P_mid purge level. The mass is about 79 g against the 76 g plan (RE-05, RE-10).
- **B-FC-1.** l.136 contradicts l.156 (RE-03).
- **HIL (l.141–142).** Cites "bench plan v1"; no such file is in the hub.
- **CF-3 (l.149).** The note "0.8 % over the 37.1 g/s limit and must be re-checked" conflicts with the lead's acceptance of 37.4 g/s within the inventory caps (l.134; l.79). State the limit row by row.

**Required action:** publish bench plan v3. Give each item a pass/fail criterion, the statistic used, the test conditions and the instrument. §9 lists the minimum criteria per gate.

### RE-14 (MAJOR). BOM v2.1 lacks the bench equipment and bleed plumbing.

**Gates:** CF-3; B-PC-1; B-BLEED-1; ENG-16 cold flows.

**Evidence.** I searched the part field (re_recompute_v1 section I). There are no rows for:
- a Coriolis mass-flow reference (CF-3);
- a reference pressure gauge (B-PC-1);
- the bleed tee, restrictors and -2 line (B-BLEED-1); mechanical.json v2 has none either;
- an N2 bottle and regulator;
- a resistor decade box;
- a transducer simulator (B-FC-1);
- a back-pressured catch volume (ENG-16, l.67).

Item 208 is disqualified (RE-05).

**Required action:** add these as TO-QUOTE rows delivered to Sønderborg DK-6400, or reference the owning discipline's BOM. Replace item 208.

### RE-15 (MAJOR). ERC 0/0 shows self-consistency only; checks needed before board build.

**Gates:** board build, which B-PC-1 needs (bench_plan_v2.md l.53).

**Evidence.**
- **The README states the limit correctly.** Its l.3 says the clean ERC and matching netlist show "self-consistent; they do not validate the hardware".
- **How the checks ran.**
  - ERC ran through the KiCad 7.0.11 GUI, with one test ignored (l.11, l.90–99).
  - The cross-check compares KiCad's netlist with the generator's own intent (l.101).
- **What ERC 0/0 does show.** Every net is driven, there are no pin-type conflicts, and a live negative control is in place (l.99). The pin map agrees with the firmware (C-01).
- **What it does not cover:**
  1. a datasheet pin-function check of the four custom symbols: Teensy41, ADS131M04_PW, Pololu_U3V70F12 and TPS552882_RPM (l.46). I found no record of one;
  2. the TPS552882 land pattern, which is a placeholder (l.135);
  3. layout, DRC and thermal design (l.134);
  4. derating: TVS release energy, MOSFET SOA, F301 I²t at 14.5–22.8 A;
  5. the logic gaps in RE-05 (b) and RE-19.

**Required action:** before fabrication:
- a signed pin-function check of each custom symbol against its datasheet;
- real footprints;
- layout and DRC;
- a derating table;
- ERC and the cross-check re-run on the final design.

### RE-16 (MAJOR). electronics.json v2 publishes stale and wrong entries.

**Gates:** interface freeze for SIL/HIL.

**Evidence.**
- **Schematic version.** The file says the schematic is v2.3 (l.6, l.2755); the delivery is v2.4.
- **Relight planning keys.**
  - l.399–400 say option_c_unprimed_s and stale_or_missing_flag are "NOT in gnc.json v3".
  - Both exist, under requirements.ignition.relight_planning_value_s (I verified this in 3e97c378cfebee95).
  - The generator reads one level too high (make_interface_json_v2.py l.330–334). The lead confirmed this (l.161 (9)); CHANGELOG l.152 repeats the error.
- **Bleed block.** l.406–408 still say "FALLBACK only; no design" with the old 0.75 A / 9 W budget.
- **Abort matrix.**
  - Code 2 HARD_START (from l.639) lists only the 30 bar trip.
  - Code 4 FLAMEOUT (from l.695) lists the legacy 1.5 bar / 0.35 thresholds, not A3 at k 0.40 / 20 ms.
  - Code 12 PC_SENSOR (from l.895) lists only the 0.25–4.75 V window and omits A7.
  - Code 28 (l.608) is correct.
- **F501.** l.2604 calls F501 the "12 V boost" fuse. It is the VBAT vent-branch fuse (ecu_design.py l.501). The boost sits on ARM_BUS behind F301 (l.318, l.463–464).
- **Other stale entries.** l.309 (RE-01), l.3022–3023 (RE-02) and l.3108 (RE-03).

**Required action:** regenerate the file as v3 from a corrected generator, and add a self-check that every abort-matrix entry quotes the config.h constants it describes.

### RE-17 (MINOR). No lower tank-temperature bound.

**Gates:** first static fire; B1; A1.

**Evidence.**
- The ARM range is 15–24 °C (REQUIREMENTS l.63, l.106).
- tankUpdate enforces only the 24 °C top (engine_ecu.cpp l.387–401; config.h l.360), so a 10 °C tank arms.
- The CF-3 table extends down to 273.15 K (config.h l.107).

**Action:** add the lower bound at ARM, with the same validity logic as the upper bound.

### RE-18 (MINOR). Propane backstop acts on one raw sample.

**Gates:** B-IGN-1; A1.

**Evidence.**
- One raw sample ≥ 4.0 bar abs closes the torch (engine_ecu.cpp l.1008–1021; config.h l.249).
- A single EMI spike of about 3 bar g during the spark therefore ends the start in TORCH_FAULT. That is fail-safe, but the relight is lost.
- The SIL spike-train result (bench plan l.122) confirms the mechanism.

**Action:** require 2–3 samples of persistence, or bound raw spikes at B-IGN-1.

### RE-19 (MINOR). Ladder decode accepts impossible and degraded states as valid.

**Gates:** B-BLEED-1; HIL.

**Evidence.**
- R7, in sensor_scale.cpp mvLadderDecode:
  - OPEN+CLOSED decodes VALID;
  - a soft short of 1.1–4.3 kΩ to GND decodes VALID;
  - leaks of 71–122 kΩ flip codes.

**Action:**
- treat OPEN+CLOSED as MV_FAULT;
- narrow the soft-short region;
- add a harness-resistance step to the pad BIT;
- test with a decade box.

### RE-20 (MINOR). 30 bar abort channel: decision says raw, firmware uses filtered.

**Gates:** SIL/HIL freeze.

**Evidence.**
- l.160 (2) says "raw persistence 3 → 5 ms". The firmware checks filtered Pc (engine_ecu.cpp l.748; config.h l.273).
- Probe F (R22):
  - filtered at 5 ms keeps the comparator first;
  - raw at 5 ms trips at or before the comparator;
  - neither changes any S6 pass/fail;
  - both still abort S5 run 127 (RE-04).

**Action:** the lead names the channel; Electronics records the S6 trip order for it.

### RE-21 (MINOR). Handback overstatements and provenance.

**Gates:** next checkpoint.

**Evidence.**
- l.88 and l.136 overstate (RE-02).
- l.104–107 does not mark S9 unlit +TEB and lit +TEB as failures new in v2.9; both passed in v2.8.3. Only lit −TEB was failing before.
- l.16 says S12 was re-run on "the final binary", but the manifest records no binary hash per scenario. My rebuild reproduces S1, S6, S9 and S12 bit-identically, so the claim holds.
- l.109–116 omit the HAL (RE-06).

**Action:** correct these in the next checkpoint, and record the binary hash for each scenario in the manifest.

### RE-22 (MINOR). BOM wetted parts: O2-clean notes and medium-temperature classes.

**Gates:** B-BLEED-1; procurement.

**Evidence.**
- Five rows are N2O-wetted: 190, 191, 198, 208 and 209. Only row 190 carries an O2-clean note (ENG-16, l.67).
- Item 208 lists a medium range of −10…80 °C, but V2 and the P_mid transducer see flashing N2O: saturation at 1 atm is about −88 °C (LITERATURE).
- PEEK/FKM compatibility with N2O is TO-VERIFY (handback l.110).
- 87 MPNs are TO-SELECT, so temperature grades are not yet fixed.

**Action:**
- add O2-clean notes to every wetted row;
- make medium temperature and N2O compatibility selection criteria;
- fix temperature grades when MPNs are selected.

### RE-23 (MINOR). S5 response metrics not traced to the amended ENG-03.

**Gates:** B-PNT-1; SIL/HIL freeze.

**Evidence.**
- Amended ENG-03 (l.51) requires a closed-loop t10–90 ≤ 100 ms under load, including the drive.
- S5 reports two metrics: "req 150 ms" passed in 91 % of runs and "target 100 ms" in 41.7 %. On the up-step, t10–90 is 0.102 / 0.122 / 0.132 s at p50 / p95 / max.

**Action:** state which ENG-03 clause each S5 metric checks. If the 100 ms clause applies to the thrust loop, S5 does not meet it on the up-step.

### RE-24 (MINOR). S6 gimbal_jam_moving_cmd is still an open FIX.

**Gates:** SIL/HIL freeze; B-TVC-1.

**Evidence.** Carried over from v2.8.3 (handback l.100; bench plan l.94): at a 2° moving command the per-axis mismatch stays below the 1.5° threshold.

**Action:** fix it, or disposition it with the B-TVC-1 threshold, before the freeze.

### RE-25 (MINOR). Record hygiene.

**Gates:** next build.

**Evidence.**
- **Log markers.** tc_dK has no invalid marker (engine_ecu.cpp l.1485), unlike prail_mV and fc_thr_dN (l.1504, l.1515).
- **Time wrap.** The log t_us wraps at 71.6 min.
- **Stale comment.** sim.h l.62 still has the old divider.
- **Makefile header.** Makefile l.1 still says "v2.8.3".

**Action:** fix all four at the next build.

### RE-26 (NOTE). A7 has no rate criterion.

**Evidence.** config.h l.316–318 states it is not implemented, with a written reason: a spike and a glitch cannot be separated. The reason is acceptable.

### RE-27 (NOTE). TLM_FAST has no application CRC; b4 persists through ABORT.

**Evidence.**
- **CRC and sequence.** Command frames carry a CRC-8; TLM_FAST does not, and seqOk rejects only repeats (protocol.cpp l.9–94). CAN's CRC-15 covers errors on the bus.
- **b4.** b4 persists until the next IGNITION (types.h l.218). This is harmless under the adopted state gate (l.161 (1)), provided the FC implements that gate.

### RE-28 (NOTE). In-flight MCU reset: recovery path undefined.

**Evidence.**
- A reset returns the ECU to SAFE and loses the arming-session state. NV flags b1/b2, or a corrupt NV record, also force the relight lockout (types.h l.149–150, l.306–308).
- An E0 brown-out is credible (RE-09).

**Action:** HIL must test this; the lead should define whether any in-flight recovery path is required.

### RE-29 (NOTE). Stale cross-discipline entries (not owned by Electronics).

**Gates:** lead.

**Evidence.**
- ICD-AIRFRAME l.90 says "about 3-10 g N2O per purge"; the plan is now ≤ 76 g.
- REQUIREMENTS l.109 says "0.6-0.8 mm", but l.113 says "~31 g/s (1.0 mm equivalent)".
- gnc.json v3:
  - relight_conditions still says "drogue release only on Pc >= 50 % of floor Pc";
  - purge_bound is still 14.5 g.
- mechanical.json v2 has no bleed content.
- S6 throat_blocked_70pct_500N reaches 53.4 bar abs, above MEOP for 34 ms, and is accepted as load case LC-TB70. I did not verify that the FEA carries it (TO-VERIFY with Mechanical).

## 5. SIL / MODEL ADEQUACY

**Reproduction.**
- test_core: 287/0.
- S1, S6, S9 and S12: bit-identical to the published files.
- S5: the 11 runs reproduce exactly.
- The "all" binary was built before the S12 additions. My rebuild from the final sources still reproduces S1, S6 and S9, which confirms the author's "core logic identical" claim.

**Dispositions.**
- **S5:** 272 NONE; 27 TVC_SUPPLY pad refusals at the weak-battery corner (pre-existing); 1 PC_OVERPRESSURE with no disposition (RE-04); 1 A7 flag (run 6).
- **S9 (TEB ±1.034 bar):**
  - lit −TEB: pre-existing failure, acceptable as outside the band;
  - unlit +TEB and lit +TEB: new failures from the BASE_AMB path. The disposition is only partly valid (RE-02, RE-21).
- **S11 v2.9:** the 28.92 cm³ direct start gives NO_IGNITION, and the purge cases light, as claimed. The 15.91 cm³ input is unpublished Mechanical data (l.160 (7)).
- **S12:** 25/25 reproduced. The bleed is 79.3 g at 1.0 mm. The dead-P_mid case loses the relight, which must change (RE-05).
- **S13:**
  - case B covered the base build only (RE-02);
  - the lighting results depend on fixed inputs (RE-11).
- **Pre-existing failures:**
  - gimbal_jam_moving_cmd: FIX still open (RE-24);
  - throat_blocked_70pct_500N: accepted with reason, if the FEA carries LC-TB70 (RE-29);
  - ballvalve_compare: OBSOLETE; accept, and remove it from the failure count;
  - S9 lit −TEB: acceptable, but depends on B-PC-1.
- **OI-A5-LATE:** decided by the lead; it closes on implementation and an S6 pass (RE-01).

**Fit for:**
- firmware sequencing, interlocks and monitor logic against a lumped plant;
- comparing variants, as in probes A–F;
- 1 kHz timing budgets.

**Not yet fit for:**
- start-transient claims: no pool or plateau, fixed spike gain and light delay;
- A1 coast effects: 2.6 s instead of 20.6 s;
- bleed timing: ASSUMED valve times, unpublished topology;
- absolute over-pressure margins, which depend on ASSUMED servo speed and span error.

**Plant features worth knowing.**
- **Sense line.** The model resonates near 172 Hz (S9 log). On fast steps it raises the transducer reading by ×1.1–1.8.
- **Measured vs true pressure.** Measured Pc can exceed the true peak through the span error alone (run 127).
- **Stuck-open bleed.** It is modelled in parallel with the injector, which is approximately additive and meets l.134 to within about 3 %.

## 6. EVIDENCE RIGOUR

**Strong:**
- explicit tags;
- failures kept on record;
- an honest README;
- a manifest, with bit-identical reproducibility;
- static_asserts on threshold order (config.h l.272, l.432–433, l.504–505, l.614–615);
- a live ERC negative control;
- written reasons for deviations, such as the A7 rate criterion.

**Weak:**
- DATASHEET values for the U3V70F12, LTC4365, TPS552882 reference and LMV331 are cited without archived sources;
- the "ASSUMED 0.03 s" valve-closing time contradicts the BOM's own datasheet line;
- the BASE_AMB fallback is tagged LEAD/COMB;
- "SIL predicts" is used as a bench pass basis (bench plan l.108–111);
- the overstatements in RE-21;
- DESIGN constants still marked "LEAD to confirm" sit in a freeze candidate (the re-zero).

## 7. CONSISTENCY TABLE

| Item | Statement A | Statement B | Status |
|---|---|---|---|
| A5 | config.h l.305–306; engine_ecu.cpp l.762–764: abort | CHANGELOG l.160 (1); REQ l.112: deleted | post-handback delta (RE-01) |
| 30 bar abort | config.h l.273: 3 ms, filtered | l.160 (2): 5 ms, "raw" | delta and wording (RE-20) |
| A7 START high side, flight | engine_ecu.cpp l.214–217: flag only, closed loop, Pc stays valid | l.160 (3) | consistent (C-22) |
| FC drogue predicate | d1 low nibble = state; b4–b7 | l.161 (1) | consistent except the b7 channel (RE-03) |
| b7 channel | engine_ecu.cpp l.157; json l.3108; bench l.136: filtered AND raw | l.156: filtered only | inconsistent (RE-03) |
| Pc invalid in [E2, release] | protocol.cpp l.121–123: 0xFFFF on the raw window only | l.161 (2): interim rule | consistent |
| UNKNOWN state | plan 1.41 s, prep path | l.161 (3) | consistent |
| Relight planning keys | json l.399–400: "NOT in gnc.json v3" | gnc.json v3 (nested); l.161 (9) | json wrong (RE-16) |
| Unconfirmed bleed closure | engine_ecu.cpp l.249–256: relight aborted | l.160 (5): proceed and flag | delta (RE-05) |
| Bleed inhibit | ecu_design.py l.532–539: ARM and watchdog only | l.160 (5): hardware purge window | delta (RE-05) |
| Purge mass | config.h l.604: ≤ 40 g at 20 g/s; S12 79.3 g; bench l.111 ~79 g; gnc.json 14.5 g; ICD l.90 3–10 g | l.159 / l.160 (5): ≤ 76 g at ~31 g/s | inconsistent (RE-05, RE-29) |
| Bleed path size | REQ l.109: 0.6–0.8 mm; l.158: GNC ≤ 0.8 mm | REQ l.113; l.160 (5): 1.0 mm equivalent | REQ internally inconsistent (RE-29) |
| Bleed valve | BOM 208: 6027 HP 1.0 mm, 16–21 W, 24 V page | l.160 (6): ≥ 4× capacity; 12 V NC; peak-and-hold | delta (RE-05) |
| Bleed coil budget | json l.406–408; README l.128: 0.75 A / 9 W | head_end_bleed_provision: 16/21 W; R17 | stale (RE-09, RE-16) |
| F501 | json l.2604: 12 V boost | ecu_design.py l.501: vent branch | wrong (RE-16) |
| Schematic version | json l.6, l.2755: v2.3 | CHANGELOG l.149: v2.4 | stale (RE-16) |
| Abort matrix | json l.639 / l.695 / l.895 | config.h A3/A5/A7 | stale (RE-16) |
| Light-rule fallback | REQ l.52; CHANGELOG l.133–134: "checked" only | engine_ecu.cpp l.135; json l.3022–3023 "LEAD/COMB" | unsupported (RE-02) |
| CF-3 table | config.h l.92–112: up to 37.4 g/s | l.134 accepted; bench l.149: "must be re-checked" | bench note stale (RE-13) |
| Drogue Pc criterion | gnc.json v3: 50 % of floor Pc | l.142 / l.161: 3.0 bar abs | gnc.json stale (RE-29) |
| Torch and spark | combustion.json: 0.594 g/s; 0.8 A at 12 V; 4 A, 50 Hz, 0.5 s | config.h torch and spark constants | consistent |
| Case limits | config.h l.330–343 | REQ l.108 | consistent; validity gap (RE-08) |
| T_tank | config.h l.360: ≤ 24 °C | REQ l.106: 15–24 °C | lower bound missing (RE-17) |
| LTC4365 | R9: 8.20 V; band top 8.339 V | REQ l.111: 8.2 V; failure case 8.34 V | consistent |
| Cap < abort < MEOP | config.h l.272 | ENG-09 | consistent; margin (RE-04) |
| A1 coast | gnc.json v3: 20.6 s | sil_main.cpp l.1936–1960: 2.6 s | coverage gap (RE-07, RE-11) |
| Bleed in Mechanical | ecu_design.py: J508–J511 | mechanical.json v2: none | missing (RE-29) |
| igniter.sequence | combustion.json | l.161 (10) | consistent |

## 8. REQUIREMENTS TRACEABILITY

| Requirement | Electronics evidence | Reviewer status |
|---|---|---|
| ENG-01 (l.49) | 25 bar cap; static_assert at l.272 | PARTIAL: transient reaches 30.0 bar abs (RE-04) |
| ENG-02 (l.50) | S3/S5 deep throttle (S5 deep resolution 90.7 %) | not re-verified |
| ENG-03 (l.51) | S5; B-PNT-1 | OPEN (RE-04, RE-13, RE-23) |
| ENG-04 (l.52, l.103) | kMaxStarts 4; light rule; lift held until light (positive trim not applied, engine_ecu.cpp l.1188–1196); no retry; 0.81 / 1.41 s | PARTIAL (RE-01, RE-02) |
| ENG-05 (l.53, l.107) | pintle-first shutdown with 0.30 s timeout; aborts drop the MV at once; MV closed in coast after 30 s (config.h l.148) | consistent (C-09) |
| ENG-07 / 07b / 07c / 07d (l.55–58) | tracker; SAT_LONG; per-axis notch commands | bench criteria missing (RE-13); FIX open (RE-24) |
| ENG-09 (l.60, l.105) | FW 30 bar; HW 31.47 bar g; 070BG; T_tank ≤ 24 °C | consistent (RE-04, RE-20) |
| ENG-10 (l.61, l.111) | LTC4365 OV 8.2 V | consistent; untested (RE-13) |
| ENG-12 (l.63, l.106) | tank top 24 °C; heater hard-disabled at ARM (C-02) | PARTIAL (RE-17) |
| ENG-13 (l.64) | ARM rule 6.6 V / 8.1 V (engine_ecu.cpp l.557–559); 7.49 V rail; PINTLE_FAULT closes the MV; flags only in flight | consistent in the core; no HAL (RE-06) |
| ENG-14 (l.65) | BOM v2.1 | met for the listed rows; list incomplete (RE-14) |
| ENG-16 (l.67) | NC MV fail-safe; arming plug; OVP AND gate | PARTIAL (RE-08, RE-14, RE-22) |
| REQ l.108 (case limits) | config.h l.330–343 | consistent (RE-08) |
| REQ l.109 / l.113 (bleed) | v2.4 provision | delta (RE-05, RE-10) |
| REQ l.112 (ignition monitors) | — | not implemented; post-handback (RE-01, RE-20) |
| REQ l.114 (drogue) | TLM_FAST d1 | PARTIAL (RE-03) |
| REQ gates l.88–90 | bench plan v2 | not covered (RE-13) |

## 9. VERDICTS AND ACCEPTANCE CRITERIA

**Overall: REVISE.**

| Deliverable | Verdict | Conditions |
|---|---|---|
| Firmware v2.9 (core) | REVISE | RE-01 to RE-05, RE-07, RE-08, RE-12, RE-17 to RE-20 |
| SIL record sil_v2p9 (test_core, S1–S13) | ACCEPT WITH COMMENTS as a reproducible record. Not yet freeze evidence | RE-04, RE-11, RE-21 |
| Teensy HAL | not delivered | RE-06 |
| KiCad ECU schematic v2.4 | REVISE | RE-05 (b)(e), RE-09, RE-15 |
| BOM v2.1 | ACCEPT WITH COMMENTS for the ECU board sections (ENG-14 met). REVISE section F (bleed) and the bench list | RE-05 (d), RE-14, RE-22 |
| Bench plan v2 | REVISE | RE-13 |
| interfaces/electronics.json v2 | REVISE | RE-16 |
| REPORT-v2.9-HANDBACK | ACCEPT WITH COMMENTS | RE-21 |

**Acceptance criteria by gate.**

**SIL/HIL freeze:**
- **RE-01:** A5 removed and LIGHT_SPIKE logged; the S6 hard_start cases pass; all other S6 causes and times unchanged.
- **RE-20:** the channel is named and S6 trip order recorded.
- **RE-02:** the lead has decided the fallback, and the extended S13 B shows no false E2 with every lit start reaching RUN.
- **RE-03:** b7 is filtered-only, with a test.
- **RE-04:** S5 shows no PC_OVERPRESSURE in 300 runs, and plant Pc ≤ 28 bar abs at p99.9 (or a lead-accepted margin).
- **RE-05:** the flight closure rule, the hard cap and purge ≤ 76 g are in place; S11 and S12 re-run.
- **RE-08 and RE-11:** closed.
- **RE-16:** electronics.json v3 passes its self-check.
- **HAL:** in place for HIL (RE-06).
- **RE-24:** closed.

**B-PC-1:**
- **Prerequisites:** a flight ECU from a board that passed RE-15, and the HAL.
- **Accuracy:** maximum |post-zero residual| ≤ 0.3 bar, measured at ≥ 6 pressures between 0 and 45 bar g, over ≥ 3 cycles across the pad temperature range. Use a reference gauge with uncertainty ≤ 0.05 bar.
- **Drift:** zero TC and 20 s drift measured (RE-07).
- **HW comparator:** trips inside 30.68–32.26 bar g and above the FW trip.
- **kBpc1Shown:** set only after RE-02 closes.

**B-PNT-1:**
- all REQUIREMENTS l.88 items;
- closing ≥ 2500 N/s; opening ≥ the rate map; closed-loop t10–90 ≤ 100 ms under load;
- HV69 speed and torque at 7.335 V and 7.49 V, fed back into S5 (RE-04);
- LTC4365 OV trip within 8.06–8.34 V and UV within 4.96–5.14 V, with no trip at 7.49 V when the load is released.

**B-TVC-1:**
- all REQUIREMENTS l.89 items;
- slew ≥ 100°/s at 7° at 7.4 V;
- notch centre frequencies set;
- the jam threshold for RE-24.

**B-BLEED-1:**
- **Hardware:** a qualifying valve and the peak-and-hold driver (RE-05).
- **Comparator:** rise within 8.95–10.79 bar g and fall within 7.93–9.80 bar g, measured against a reference gauge.
- **P_mid during the purge:** above the rise band including TEB (13.34 bar g) plus margin, or a computed value shown to be clear of the band.
- **Closure:** the worst of 20 cycles at N2O feed pressure ≤ deadline − 30 ms, across the valve's temperature range.
- **Mass:** ≤ 76 g per scheduled purge.
- **Supply:** +12V_ARM droop and U3V70F12 current measured with all overlapping loads at VIN 6.6 V.
- **Monitoring:** the leak monitor and pad BIT steps S0–S4 demonstrated.

**IGN-1:**
- E2 − light ≤ the latency GNC accepts (SIL 16–18 ms);
- unlit maximum rise ≤ 0.6 bar;
- A3 ratio minimum ≥ 0.45;
- P0 shift during the spark ≤ 0.1 bar;
- raw spikes < 2 bar g during the spark;
- no BASE_AMB event;
- b4/b7 timing as specified;
- LIGHT_SPIKE logged.

**First static fire:**
- the RE-01 build;
- RE-12 trip rate quantified and decided;
- RE-08 and RE-17 closed;
- the HAL in place;
- B-PC-1 and B-IGN-1 passed;
- HW comparator and LTC4365 thresholds measured.

**B1:**
- RE-04 closed for the B1 landing-burn profile;
- the FC predicate with the state gate implemented;
- if bleed valves are fitted, a hardware inhibit for the whole flight;
- RE-09 measured at 6.6 V.

**A1:**
- everything above that applies;
- RE-05 complete;
- RE-07: drift measured and policy decided;
- RE-10: closure timing on the final path;
- RE-28: reset behaviour tested in HIL;
- CF-4 as the lead conditions it;
- the purge within ≤ 76 g of the A1 reserve.

**Supervision.** The lead registers this verdict in SUPERVISION.json; that file is outside my write scope.

## 10. CONFIRMATIONS

**Hardware values reproduced:**
- **C-01. Pin map.** pin_map_v2p4.csv agrees with the generator's pin table and with firmware use. Every pin is used, and pin 24 is freed for BLEED_B.
- **C-02. Heater/V1 exclusivity.** R328 is present. Heater and V1 are exclusive by the ARM bus in hardware (ecu_design.py l.3–4, l.421) and in firmware.
- **C-03. OVP.** The trip of 31.465 bar g is reproduced, and the HW path stays above the FW path across its whole electronic band (R4).
- **C-04. P_mid comparator.** 9.864 / 8.864 bar g reproduced.
- **C-05. Pintle rail.** LTC4365 OV 8.20 V (band top at the 8.34 V failure case) and TPS552882 7.49 V reproduced.
- **C-06.** Ladder ratios and ADC headroom reproduced.
- **C-07. BOM pricing.** No zero or "from" prices; every purchase row is TO-QUOTE delivered to Sønderborg DK-6400 (ENG-14).

**Logic matches the decisions:**
- **C-08. Light rule.** Matches l.134 except for the fallback (RE-02): baseline over [E1 − 20 ms, E1]; 0.8 bar on filtered AND raw for 10 ticks; floor 1.8 / 2.0 bar abs (config.h l.541–546).
- **C-09. Shutdown.** Normal shutdown is pintle-first with the 0.30 s seat timeout (config.h l.498, l.504–505). Every abort drops the MV at once with the pintle closing in parallel; in S6 the MV is closed 38 ms after the abort.
- **C-10. Case limits.** Implemented as decided (448.15 K / 0.2 s with the MV open, also armed in PURGE; 433.15 K for relight refusal). In S6, 455 K aborts and 445 K does not. The validity gap is RE-08.
- **C-11. Bay and tank.**
  - Bay ≤ 45 °C at ARM and at the first start, with invalid treated as hot.
  - Tank ≤ 24 °C at ARM and for pad or stand starts, with invalid treated as hot.
  - Flight relights only raise a flag (ENG-13).
- **C-12. Windows and mode strap.**
  - W is 0.40 s for the flight first start, 0.65 s for a flight relight and 0.35 s on the stand.
  - The order is enforced by a static_assert, and the what-if build is guarded (config.h l.419–433).
  - The mode strap is cross-checked against the load cell (engine_ecu.h l.176–177).
- **C-13. Over-thrust.** FC_THRUST 650 N for 3 frames, stale after 50 ms, flight RUN only, active whether or not Pc is valid (config.h l.477–484; engine_ecu.cpp l.754–759). The k_est freeze is as specified.
- **C-14. Relight state reporting.** The TLM_RELIGHT invariants hold. The worst case of 1.37 s is within the 1.41 s plan, and UNKNOWN maps to the 1.41 s path (l.161 (3)). The RG-08 coast latches are in place.
- **C-15. Drogue protected against a false E2 (probe D).**
  - Offsets of +1.0 to +2.5 bar on both builds: the FC predicate is never true.
  - At +1.0 bar there is a false E2 with Pc ≤ 2.06 bar abs, and FLAMEOUT 19 ms later. b7 never sets, leaving about 80 ms of margin to the hold window.
  - At ≥ +1.5 bar the start ends in TORCH_FAULT.
- **C-16.** The torch N2O-alone time is 0 ms in all runs.
- **C-17. Ignition lift.**
  - The CF-3 table has 17 rows, up to 37.4 g/s.
  - An invalid P_tank selects the smallest lift.
  - A positive trim is never applied before light.
  - The published inventories, 24.8 g and 13.45 g, are within the 26.6 g and 13.84 g caps (author values, checked against l.134).
- **C-18. Starts and retry.** kMaxStarts is 4, against a requirement of ≥ 3. Lockout is applied after an abort, with no in-flight retry.
- **C-19. Torch gate.** The confirmation counts only while main Pc gauge is below 1 bar, within 0.16 s; otherwise TORCH_FAULT.
- **C-20. Bleed sequence design is sound** (aside from RE-05 and RE-10):
  - V1 closes first while V2 vents the mid volume;
  - the pad BIT runs steps S0–S4;
  - there is a leak monitor;
  - the pintle is held seated during the purge, with PINTLE_FAULT on lift;
  - the case abort stays armed in PURGE.
- **C-21. TLM_FAST d1.** d1 carries the state in b0–b3 and the flags in b4–b7, consistent with the adopted mask (l.151, l.161 (1)).
- **C-22. A7 START high side in flight complies with l.160 (3):**
  - it only raises a flag;
  - the loop stays closed;
  - telemetered Pc is marked invalid only from the raw voltage window (engine_ecu.cpp l.214–217, l.1064, l.1354; protocol.cpp l.121–123).
- **C-23. A3 (relative form).** k 0.40, 20 ms, with the mlo denominator (engine_ecu.cpp l.176–182). It handles throttle-down transients; the S5 A3 minimum is 0.463.
- **C-24.** The stuck-open bleed in the SIL is approximately additive (l.134).

**Reproducibility:**
- **C-25. Reproduction.** test_core 287/0; S1, S6, S9 and S12 bit-identical; S5 runs reproduced.
- **C-26. Blocked throat.** In S6 the HW comparator trips faster than the FW path (5.7 ms on the 500 N case). The pass/fail result is unchanged with 5 ms persistence (R22).
