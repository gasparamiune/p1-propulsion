# 06-electronics v2.10 handback
Electronics (engine team), 2026-10-13. Firmware/ECU v2.10, ECU schematic v2.5, BOM v2.2, bench plan v3, `interfaces/electronics.json` v3.

This text is the report. No REPORT file was written in 06-electronics. The hub top level has no REPORT file now; the v2.9 report is in `archive/v2.9/`.

**Read first.**
- All evidence is SIM, DERIVED, DATASHEET or DESIGN.
- A passing unit test, a SIL case marked as expected, ERC 0/0 or a matching hash is not physical validation and not a review verdict.
- Author: Electronics. Reviewer: none yet. An independent reviewer (REV-ELEC-2) is needed, and that reviewer, not the author, records the verdict in supervision.json.

**Tags:**
- SIM: simulation output.
- DERIVED: computed from cited inputs.
- ASSUMED.
- DATASHEET.
- LITERATURE.
- TO-VERIFY.
- DESIGN: a choice made here.
- REQ: a requirement or LEAD decision.
- MISSING: data that does not exist yet.

## 1. Checkpoint

### CLAIM

1. **Firmware v2.10 ECU core.** Implemented in the SIL build [SIM]:
   - REV-ELEC-1 firmware items RE-01, 02, 03, 04, 05 (firmware part), 07, 08, 11, 12, 17, 18, 19, 20 and 25.
   - LEAD 164, 166, 168, 172, 175, 181 and 186 (2).
   - Evidence: test_core 309 passed, 0 failed; SIL record MANIFEST_v1 6d1dd43ddeeba0d7.
2. **R2 command hold (186 (2)).** It works in SIL against an in-loop FC stand-in written by Electronics (S17, section 4). This is not FSW evidence and not hardware evidence.
3. **electronics.json v3 (38bf149f368c1d4c).** It is consistent with its sources by its own self-checks:
   - 30 abort causes and 80 constants quoted from config.h;
   - stale-string and A5 token scans;
   - manifest binary check.
   This checks the file's consistency only.
4. **LEAD 194 (7) / R3-10, 070BG over-range.** Answered from the datasheet plus a SIL-chain study of the 896 Combustion FA-1 histories (section 3.1). The saturation level and recovery are MISSING, so the answer is bounded by a sweep, not measured.
5. **LEAD 194 (7), stand dynamic Pc channel.** Candidate named with datasheet values: PCB 113B22 plus NI 9234. Price TO-QUOTE, delivered to Sønderborg DK-6400 (section 3.2).
6. **LEAD 194 (1), (3), (4).** Folded into the bench plan, the BOM and electronics.json. No firmware change was made for 194.
7. **Hub publication.**
   - The v2.9 tree was archived and verified, then replaced with v2.10.
   - SHA256SUMS-v2.10.txt (674eef94498822dd): 502 hashes OK, checked twice.
   - CHANGELOG appended.

### CONFIGURATION

- **Firmware v2.10 build:** `g++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter -Isrc/core -Isil`. SIL builds add `-DECU_SIL_TEST_HOOKS`.
- **Binaries.** Each is identical to a rebuild of the current tree.

  | Binary | sha256/16 | Note |
  |---|---|---|
  | build/sil | 986f77d935ef9f8c | |
  | build/sil_bpc1 | 12fde7c8e52daa08 | built with `-DECU_BPC1_SHOWN_VARIANT` |
  | build/test_core | 9baa6a63eb144e2e | |
  | build/fa1_overrange_chain | 5b511f1a904a885a | `calc/v2p10/fa1_overrange_chain.cpp` + `sil/plant.cpp`, 0 warnings |

- **ARM:** `make arm` (arm-none-eabi-g++ 13.2.1, Cortex-M7) is a compile and size check only.
  - 93 `-Wdouble-promotion` warnings.
  - engine_ecu.o text 29614 B.
  - No HAL, no link, no target run.
- **SIL record:** `results/sil_v2p10/MANIFEST_v1.json` (tool v1.3), 6d1dd43ddeeba0d7.
  - Record 2b4edc73ca0db018; source tree 8ec86d515cc9980d.
  - 39 sources, 253 result files, 0 unmapped.
  - No source was edited after the run. The 194 work changed no firmware source.
- **Generated headers:** still from combustion.json v2.3 and mechanical.json v2 (OI-GEN-TABLES).
  - gnc.json v3.1 arrived after the record.
  - The leaves the generators read have 0 numeric changes from v3 [DERIVED].
- **Tools:** KiCad 7.0.11 (schematic v2.5). Python 3 for the generators.
- **Processes:** at most 2, at nice 10. The compression ran at nice 19, single-threaded.
- **Paths:**
  - workdir: /home/claude/work/electronics;
  - hub: /home/claude/work/shared-fallback/engine/06-electronics.

### SOURCES (sha256/16)

| Source | sha256/16 | Used for |
|---|---|---|
| reviews/REVIEW-ELECTRONICS.md (REV-ELEC-1) | 471d830c8d00dd85 | RE-01..RE-29 |
| interfaces/CHANGELOG.md, read through line 194 (lines 164-194 used) | f3dd884de680e626 (before the append) | LEAD decisions |
| interfaces/combustion.json v2.4a | 5237d4584bad38c4 | stale entries; unpurged finding |
| 02-combustion/data/v2p4a/fa1_envelope_v2p4a.json | 64b328150025fa1e | 896 FA-1 head histories (Combustion SIM) |
| 02-combustion/data/v2p4a/cold_flow_thrust_v2p4a.csv | e094c4be80d12f66 | S17 F_cold (DERIVED adiabatic bound) |
| 02-combustion/data/v2p4a/unpurged_start_check_v2p4a.json | 4c745dcfbf09aef7 | OI-UNPURGED-RELIGHT |
| interfaces/gnc.json v3.1 | 4f3209323b0e0ed4 | planning keys; purge_bound wording |
| 01-systems-gnc/superseded/gnc_v3_3e97c378cfebee95.json | 3e97c378cfebee95 | generated-header provenance |
| interfaces/mechanical.json v2.1 | e4d3e7c9df529171 | header provenance |
| interfaces/electronics.json v2 (superseded) | da067408c1594814 | `--prev` of the v3 generator; archived |
| DATASHEET TE M3200, 08/2018 (farnell.com/datasheets/3007269.pdf) | not stored | 070BG proof, burst, rise time, TEB |
| DATASHEET PCB 113B22 product page (pcb.com, read 2026-10-13; sheet 113b22_g.pdf, revision not stated) | not stored | B-DPC-1 sensor |
| DATASHEET NI 9234 377849B-01 (Feb 2025) and 374238A-02 (Oct 2015) | not stored | B-DPC-1 DAQ |
| DATASHEET LTC6993 Rev F | not stored | purge-window one-shot |

The coordinator relays (181, 186, 194 and the disk request) are agent messages: task direction, not LEAD decisions or user consent. Where a relay differs from the CHANGELOG, I used the CHANGELOG text and state the difference (section 5, item 12).

### FILES (sha256/16)

The workdir copies equal the hub copies: 23 of 23 key files checked. The full list is in `06-electronics/SHA256SUMS-v2.10.txt`.

| File | sha256/16 |
|---|---|
| firmware/src/core/config.h | 0880af5a27880a5b |
| firmware/src/core/engine_ecu.cpp | 6e62a7e4e37930bd |
| firmware/src/core/engine_ecu.h | cc103800ea92ad4e |
| firmware/sil/plant.cpp | 24538c55be54a323 |
| firmware/sil/sil_main.cpp | 094a479ab676f75b |
| firmware/sil/test_core.cpp | aeabfa212e3c0350 |
| firmware/Makefile | 1ba63ce7b2bc8ed9 |
| results/sil_v2p10/MANIFEST_v1.json | 6d1dd43ddeeba0d7 |
| results/electronics_v3.json (= interfaces/electronics.json) | 38bf149f368c1d4c |
| results/fa1_overrange_v2p10.json | f2b07a3d780a289c |
| results/fa1_overrange_v2p10_cases.csv (14336 rows) | cd96ad39a0f8fb29 |
| results/fa1_overrange_v2p10_run_log.txt | 2ea74b3bc4ec6c4e |
| results/bom_v2p2.csv | 75723fd39be88c20 |
| results/bom_v2p2.json | 17d3d767768b4744 |
| results/bom_v2p2.txt | 6e5c200868ce59d1 |
| results/gnc_v31_read_keys_check_v2p10.json | 68f0459f360a845d |
| results/spike_chain_v2p10.json | 52d8976ca4e851d1 |
| results/bleed_driver_v1.json | 298b405b0621acd5 |
| calc/make_interface_json_v3.py | 8912b95febe64f0e |
| calc/bom_v2.py | afd3cbfc3394d185 |
| calc/v2p10/fa1_overrange.py | 4dbfd243966da8fb |
| calc/v2p10/fa1_overrange_chain.cpp | 818bc268a052a3d8 |
| docs/bench_plan_v3.md | aa82f280feeeee4c |
| hardware/kicad/argos_ecu.kicad_sch | c0192697e551394e |
| hardware/kicad/pin_map_v2p5.csv | ab8b28958d33062c |
| hub: 06-electronics/SHA256SUMS-v2.10.txt (502 entries) | 674eef94498822dd |
| hub: 06-electronics/archive/v2.9/SHA256SUMS.txt (406 entries) | 5f5f9a172b41339d |
| hub: 06-electronics/archive/v3_interim/electronics_v3_9052d894578990d4.json | 9052d894578990d4 |
| hub: interfaces/CHANGELOG.md after the append (201 lines) | c5da284c9c922632 |
| workdir: results/archived_tar/INDEX_v2p10.txt | c0883a0d2677d5dc |

### TESTS (counts as run; SIM or unit tests unless stated)

**Unit tests**
- test_core: 309 passed, 0 failed. v210-17 adds 2 checks for the R2 hold.

**SIL record** (status tokens as printed)

| Scenario | Result |
|---|---|
| S6 aborts | 55 PASS / 3 FAIL (known) |
| S8 | 5 / 0 |
| S9 | 5 PASS / 4 FAIL (known) |
| S10 relight | 31 / 0 |
| S12 bleed | 31 PASS / 4 FAIL (detection gap) |
| S13 deterministic | B 52 cases / 0 fail; C 24 and D 12 cases recorded |
| S13 Monte Carlo | 263 lit + 263 unlit runs per rule, 0 false lights |
| S13 B-extension | LEAD criteria fail 32/164 and 64/164 |
| S14 | 18 / 0, plus INFO observations |
| S15 | 300 runs |
| S16 | 12 / 0 |
| S17 R2 hold | 17 cases + 2 × 30 noise runs, 0 not as expected |
| Probe F | 11 runs; worst plant Pc 27.293 bar abs; 0 PC_OVERPRESSURE |
| S5 | 300 runs; plant Pc max 27.316 bar abs; 0 PC_OVERPRESSURE |
| S11 fault path v4 | 2 configurations |

- Failing scenario lines: 11 by the manifest v1.3 rule (S6 3, S9 4, S12 4), all known. The v1.2 rule counted 7.
- Torch N2O without propane: 0 ms in every scenario.
- Re-record check against the previous record folder:
  - 245 files byte-identical;
  - 2 differ (the timing file, and the test log with +2 tests);
  - 6 are new (S17).

**FA-1 over-range harness**
- 896 cases × 16 chain configurations = 14336 rows, worst of 4 ADC phases. Exit 0, 34.4 s.
- Cross-check against the published spike_chain tool on case 743: identical Vmax 4.063 V, raw 63.36 bar abs, filtered 42.14 bar abs, comparator 2.387 V, and both trips. Both tools share the firmware constants and the plant model, so this shows consistency, not independent confirmation.

**Other checks**
- ARM compile: 93 warnings, 0 errors.
- KiCad v2.5: ERC 0/0 on 9 sheets. Netlist cross-check: 471 symbols, 288 nets, 1301 pins, 0/0. Self-consistency only.
- electronics.json v3 self-check: PASS. Scans of the published file:
  - withdrawn T_fire basis: 0 hits;
  - "181 (1)": 0 hits;
  - the stale proof figure: 0 hits;
  - "%%": 0 hits;
  - every "E2 + 0.22" occurrence is marked withdrawn.
- BOM v2.2: 250 rows.
  - 3 CATALOGUE listing prices: 379.00 SEK + 422.96 EUR. These are not quotes and not a total.
  - 213 TO-QUOTE; 34 no purchase.
  - TOTAL UNKNOWN.
- Hub: `sha256sum -c` of SHA256SUMS-v2.10.txt gave 502 OK, run twice (after publication, and again before the CHANGELOG append). The v2.9 archive was verified against its sources before the replacement.
- Disk job: 13 archives, 1610 files. Every file was re-hashed from its archive against the source list before deletion. 0 failures.

**Not run**
- Any hardware, HIL or target test.
- gen_tables on combustion v2.4a (it fails).
- A SIL re-record after the 194 work (no firmware changed).

### UNKNOWNS / MISSING

- **070BG above full scale:** saturation level, recovery time, bandwidth, and any zero or span shift after an over-range below proof are all MISSING; the datasheet is silent. They need the B-PC-1 over-range row and an inquiry to TE.
- **Pc port and sense line:** the geometry (length, ID, end volume, routing) and its period are MISSING (owner: Mechanical). The ~6 ms period comes only from the SIL linear model on ASSUMED geometry (0.30 m, 1.59 mm ID).
- **Head pressure spectrum at the line period:** needed from Combustion v2.4b. The reviewer value is up to 146.4 bar abs at 3 ms (194 (1)). FA-1 histories beyond 25 ms are also missing.
- **113B22 with NI 9234 excitation:** PCB lists 20-30 V; NI compliance is 19 V max. TO-VERIFY.
- **Bleed valve:** no candidate qualifies. The requirement is Kv ≥ 0.11 m3/h verified at 55 bar, flashing N2O, 12 V DC, ≤ 0.15 kg. Unknown with it:
  - coil data;
  - open/close times (ASSUMED 30 / 80 ms);
  - mass (Mechanical carries 2 × 0.30 kg ASSUMED).
- **Not designed or written:**
  - peak-and-hold and the time-resolved power budget (RE-09);
  - the Teensy HAL (RE-06; TLM_SLOW is undefined);
  - the PCB layout (RE-15).
- **Cold-flow thrust at the start or hold lift:** TO-VERIFY at CF-3. The 194 (4) heat item (injector-body and feed soak-back, 2.8-3.7 kW) is TO-VERIFY (owner: Combustion).
- **Lifts not reconciled:**
  - 0.2154 mm: ECU hold;
  - 0.21776 mm: ECU ignition row at 286.70 K;
  - 0.2039 mm: grain_q1d start level, 194 (4).
- **Thermal and timing inputs:** tank wall-vs-bulk offset; transducer temperature from MECO to RELIGHT (owner: Mechanical); Combustion's tolerance of a later E0 (the basis of kPurgeHoldMax_s).
- **Photodiode levels:** ASSUMED (dark 0.10 V, torch +1.0 V, main +2.0 V). The main-chamber view is MISSING until IGN-1.
- **Four firmware values without source text in combustion.json v2.4a:** 2500 N/s, 0.5 s, 5 bar abs and 0.12 s.
- **FC side:** DROGUE reports, the R2 implementation, L*, the PURGE_EN discrete and the IMU filter delay are MISSING (owner: FC / GNC).
- **Prices:** all TO-QUOTE, delivered to Sønderborg, DK-6400. No total exists.

### NEXT CLOSURE

- **Reviewer:** REV-ELEC-2 against section 2 (the RE table), section 3 (194), the S17 limits and section 5. The reviewer records the criteria and the verdict in supervision.json.
- **LEAD:**
  - OI-FA1-PC-OVERRANGE: abort FA-1 at the A1 relight (as built) or ride through it. A ride-through needs three changes (the filtered 30 bar persistence, the 4.75 V IGNITION rule and the comparator RC) plus an S6 re-run.
  - The v2.11 offers: a non-sticky over-range bit, an above-full-scale flag, and an unpurged RELIGHT guard.
  - Purge cap vs 76 g.
  - S13 B criteria per class.
  - RE-12 flight extension of the A7 blank.
  - RE-24 bound.
- **Mechanical (194 (1)):**
  - List the Pc port and sense line with their period and basis. Until then the 070BG port is at FA1S (~151 bar abs), above its proof.
  - Transducer temperature from MECO to RELIGHT.
  - Bleed valve mass and mounting.
- **Combustion:**
  - v2.4b spectrum at the line period;
  - FA-1 histories beyond 25 ms;
  - the 194 (4) heat item;
  - the stale v2.4a entries;
  - the four sequence values;
  - FLAMEOUT_OPT in the cold_flow text.
- **GNC / FC:**
  - send DROGUE 1 and 0, and check the d6 b6 echo before a RELIGHT;
  - state when R2 starts counting after a Pc loss;
  - fly R2 v2 with grain_q1d at 0.2039 mm and the hold profile;
  - put L* = 1.3 s in the FSW record;
  - fix the purge_bound wording in gnc.json v3.1.
- **Founders (physical):**
  - B-PC-1 over-range row: spare 070BG at 70, 80, 90 and 100 bar g (below the 140 bar g proof); record V_sat, zero shift and recovery.
  - Buy B-DPC-1 (TO-QUOTE).
  - CF-3 start-lift point.
  - B-PT-1, B-BLEED-1, B-FC-1, IGN-1 and HIL-RST-1, in the order of bench plan v3.
  - The over-range inquiry to TE.
- **Electronics:**
  - valve selection, then peak-and-hold, then RE-09;
  - HAL (RE-06);
  - layout and the RE-15 checks;
  - gen_tables v3.4;
  - v2.11 with a re-record if the LEAD accepts the offers;
  - fix the stale labels (section 5, items 16 and 20);
  - limit each transducer sample in the SIL ADC path (item 14).

## 2. REV-ELEC-1 status, RE-01 to RE-29

This is the author's status; acceptance is the reviewer's. CLOSED means closed in SIL or in a document. No item is closed on hardware.

| ID | Status | What was done / what is left | Evidence |
|---|---|---|---|
| RE-01 | CLOSED | A5 deleted as an abort. LIGHT_SPIKE is now a record only (log + EVENT 0x20, no abort). The 30 bar abort runs on the filtered channel. S15, 300 runs: 0 A7 aborts, 0 OVP/HW/HARD; LIGHT_SPIKE raw p99 31.42 bar, filtered max 24.55 bar abs [SIM]. | test_v28, v210-1; S15; spike_chain_v2p10.json |
| RE-02 | OPEN, partly done | One-sided baseline (LEAD 166 (1)) implemented and unit-tested. The S13 B-extension LEAD criteria fail 32/164 and 64/164 because of the same rule. LEAD to restate the criteria per class. | OI-RE02-CRITERIA |
| RE-03 | CLOSED | b6/b7 come from the valid filtered channel only; E2 keeps both channels. | v210-3, v210-8; S14 |
| RE-04 | CLOSED | Lift clamp during pintle travel, plus integrator hold. S5 300 runs: max 27.316 bar abs. Probe F 11 runs: max 27.293 bar abs. 0 PC_OVERPRESSURE [SIM]. A p99.9 cannot be resolved with 300 runs, so the maximum is reported. | v210-12; S5; probe F |
| RE-05 | OPEN, partly done | Firmware: E1 = 2oo2 torch AND closure step ended; flight continues with BLEED_FAULT and V2 closed; stand aborts. Hardware v2.5: PURGE_EN AND the one-shot gate both drives. Left: no qualifying valve; peak-and-hold not drawn; the 2.61 s cap allows 77.7 / 83.6 g, above 76 g. | OI-BLEED-VALVE, OI-PURGE-CAP |
| RE-06 | OPEN, not done | Teensy HAL not written. | OI-HAL |
| RE-07 | OPEN, partly done | Rolling re-zero and NOT_VENTED semantics; S16 12/0. Left: the B-PC-1 drift measurement (B-PC-1 now also has the over-range row) and the transducer temperature from MECO to RELIGHT (MISSING). | S16; bench plan v3 |
| RE-08 | CLOSED | Both case TCs checked at ARM; degraded and lost cases handled. | v210-10 |
| RE-09 | OPEN, not done | Time-resolved power budget, sequencing and peak-and-hold. Needs the valve coil data. | OI-POWER |
| RE-10 | OPEN, partly done | P_mid level and closure rule published from ASSUMED valve times. The final timing waits for B-BLEED-1. | electronics.json v3; S12 |
| RE-11 | CLOSED | S5/S15 inputs come from a second generator (ASSUMED bands, Combustion-sourced where stated). | sil_main.cpp |
| RE-12 | CLOSED | A7 high side blanked from E2 to E2 + 0.45 s; S15 has 0 A7 aborts. The flight extension is a DESIGN choice awaiting the LEAD. | config.h kA7StartHiBlank_s |
| RE-13 | CLOSED | Bench plan v3 gives criteria per test. 194 additions: B-DPC-1 rewritten, B-PC-1 over-range row, CF-3 start-lift point. | docs/bench_plan_v3.md |
| RE-14 | CLOSED | BOM v2.2 bench equipment. 194 additions: 113B22 × 3 (row 237), NI 9234 (row 238), hydraulic pump (row 245), all TO-QUOTE. | bom_v2p2 |
| RE-15 | OPEN, not done | No layout, pin-function check, footprints or derating table. | OI-RE15 |
| RE-16 | CLOSED | electronics.json v3 generated with self-checks. v2 superseded with history. 186 (4) hygiene added. New 194 section pc_overrange_fa1. | 38bf149f368c1d4c |
| RE-17 | CLOSED | 15 °C lower bound for the tank. | v210-11 |
| RE-18 | CLOSED | Propane backstop with 3-sample persistence. | test_v210 |
| RE-19 | CLOSED | Ladder decode codes; 5 ms conflict persistence; pad BIT ratio check. | test_v29; v210 |
| RE-20 | CLOSED | 30 bar abort on the FILTERED channel, 5 ms persistence, continuing across E2. | test_core |
| RE-21 | CLOSED | The manifest binds each result to its scenario and binary. Tool v1.3 corrects the FAIL-line undercount. | MANIFEST_v1 |
| RE-22 | CLOSED | O2-clean and medium-temperature notes on every N2O-wetted BOM row. | bom_v2p2 |
| RE-23 | CLOSED | S5 metrics mapped to the amended ENG-03 clauses. | S5_mc.json |
| RE-24 | DISPOSITIONED | A small-amplitude gimbal jam is not detected below the SIL bound. B-TVC-1 measures the bound; LEAD to accept. | S6 |
| RE-25 | CLOSED | Log wrap byte, invalid-TC code, header stamps and stale comments fixed. One stale label is left (section 5, item 20). | test_core |
| RE-26 | DISPOSITIONED | No A7 rate criterion; the review accepted the stated reason. | config.h |
| RE-27 | DISPOSITIONED | TLM_FAST has CAN CRC-15 only. The b4 persistence is harmless under the RUN gate if the FC implements it. HIL check. | electronics.json v3 |
| RE-28 | OPEN, not done | HIL-RST-1 is written but not run. No in-flight recovery path (LEAD 166 (8)). | bench plan v3 |
| RE-29 | DISPOSITIONED | Stale entries owned by other disciplines sent as requests. | electronics.json v3 requests |

**Count:**
- CLOSED: 17.
- OPEN: 8. RE-02, 05, 07 and 10 are partly done; RE-06, 09, 15 and 28 are not done.
- DISPOSITIONED: 4.

## 3. LEAD 194 answers

### 3.1 070BG over-range at the FA-1 peaks (194 (7) / R3-10)

**Inputs** [Combustion SIM]: 896 FA-1 head histories.
- 448 vapour_once + 448 as_written.
- 0.1 ms grid, 0-25 ms.
- Peaks 22.2-88.02 bar abs at 1-7 ms.

**Chain** [SIM]: each history runs through the SIL Pc chain with the v2.10 firmware constants, worst of 4 ADC phases. Swept:
- sense line on or off;
- transducer lag τ 0.9 ms (the slowest the datasheet rise time allows) or 0.1 ms;
- saturation level 4.95, 4.74 or 4.50 V, or none.

**Transducer** (TE M3200, 08/2018) [DATASHEET]:
- proof 2× rated = 140 bar g = 141.0 bar abs;
- burst 5×;
- rise time < 2 ms;
- TEB ±1.5 % FS;
- saturation level, recovery and bandwidth not stated: MISSING.

The 141.0 bar abs proof is above 90 bar abs, so the 070BG is NOT a design-change item at the head pressure.

**Firmware v2.10 as built:**
- A reading ≥ 4.75 V (74.4 bar g) sets the sticky PC_SENSOR fault. PC_VALID then stays 0 until DISARM in SAFE. In IGNITION it also aborts HARD_START on that tick.
- Readings of 4.5-4.75 V are used without a flag.
- The 30 bar abs abort uses the FILTERED (50 Hz) channel with 5 ms persistence.
- The hardware comparator sees PC_SIG through an RC of 5.283 ms. It trips at 2.298 V nominal, 2.208 V at the low band edge.

**Results [SIM].** All case counts are out of 896.

| Chain | Aborted | First abort path | Reading ≥ 4.75 V | Logged ≥ full scale without a flag | Port peak / logged peak, bar abs | Comparator trips, nominal / low band |
|---|---|---|---|---|---|---|
| head, no line, τ 0.9 ms (any V_sat) | 362 | firmware 247, comparator 115 | 0 | 0 | 88.02 / 63.36 | 115 / 156 |
| head, no line, τ 0.1 ms, V_sat 4.95 V | 379 | firmware 255, comparator 118, over-range 6 | 6 (first at 1.77 ms after the light) | 21 | 88.02 / 76.77 | 124 / 163 |
| head, 0.3 m line, τ 0.9 ms, V_sat 4.95 V (sensitivity only) | 494 | over-range 264, firmware 155, comparator 75 | 264 | 46 | 150.99 / 78.89 | 267 / 354 |
| same, V_sat 4.74 V | 461 | firmware 234, comparator 227 | 0 | 310 | 150.99 / 75.21 | 227 / 341 |
| same, V_sat 4.50 V | 438 | firmware 256, comparator 182 | 0 | 288 | 150.99 / 71.01 | 182 / 313 |

- In every case E2 comes 10.0-13.0 ms after the light, and every reading ≥ 4.75 V occurs before E2 (in IGNITION).
- The sense-line model is linear and hits its 1 kPa floor in 640 of 896 cases. The line rows are therefore a sensitivity, not evidence.

**Effects the relay asked about:**
- **(a) The 30 bar abort and its 5 ms persistence.**
  - On the filtered channel it trips whatever the saturation level. The filtered peak is 44.2-49.1 bar abs, and the channel is above 30 bar abs for up to 12.0 ms in total [SIM].
  - Saturation only lowers the comparator trip counts.
  - Sensitivity [SIM]:
    - 15 ms persistence: the firmware check trips in 0 cases;
    - 10 ms persistence: 98-154 cases;
    - comparator RC of 10 or 20 ms: 0 low-band trips.
- **(b) The Pc-valid flag must not latch.**
  - v2.10 latches on any reading ≥ 4.75 V: 0, 6 or 264 cases depending on the chain.
  - If the real saturation level is below 4.75 V, it never latches, but it never flags either.
  - v2.10 does NOT guarantee the "must not latch" requirement.
- **(c) The logged FA-1 peak needs an over-range flag.**
  - v2.10 has no above-full-scale flag.
  - Without a line, the log under-reads the head peak by up to 24.7 bar (88.02 bar abs read as 63.36). The cause is the transducer lag and the ADC averaging; saturation plays no part.
  - Cases logged at or above full scale without a flag: 0 (no line, τ 0.9 ms), 7-26 (no line, τ 0.1 ms) and 46-310 (line model).
  - ls_.overrange is set only at ≥ 4.75 V and is sampled at the abort tick.

**Consequence.**
- FA-1 at the A1 relight is aborted (HARD_START, or HW_OVERPRESSURE through the comparator) in 362-494 of the 896 grid cases. These are grid counts, not probabilities.
- Abort or ride-through is a LEAD decision (OI-FA1-PC-OVERRANGE, HIGH).
- Offered for v2.11 and not implemented:
  - a non-sticky over-range bit, with PC_VALID 0 only while the over-range lasts;
  - an above-full-scale flag in LIGHT_SPIKE and in the 1 kHz log.

**Under 194 (1).**
- The 070BG port behind the sense line has a period of about 6 ms (SIL model, ASSUMED geometry). That is the T > 1 ms domain.
- The level there is FA1S, about 151 bar abs, or the spectrum value (the reviewer gives up to 146.4 bar abs at 3 ms). Both are above the 141.0 bar abs proof.
- This is a DESIGN CHANGE candidate unless Mechanical and Combustion show the line response is below the proof.

### 3.2 Stand dynamic Pc channel (≥ 100 bar abs, stated proof, ≥ 10-20 kHz)

**Sensor: PCB Piezotronics 113B22** [DATASHEET, pcb.com product page, read 2026-10-13]
- Range 5 kpsi = 344.75 bar at ±5 V. Maximum pressure 15 kpsi = 1034 bar.
- Sensitivity 1.0 mV/psi ±10 % (14.5 mV/bar).
- Resonance ≥ 500 kHz; rise time ≤ 1 µs; low-frequency limit (−5 %) 0.001 Hz; DTC ≥ 500 s.
- −73 to +135 °C; flash 1649 °C.
- Excitation 20-30 VDC at 2-20 mA; bias 8-14 V; 10-32 connector.
- It replaces the 113B24 (1 kpsi = 69 bar full scale), which fails the ≥ 100 bar abs requirement.

**Conditioner / DAQ: NI 9234** (377849B-01, Feb 2025) [DATASHEET]
- ±5 V input.
- IEPE 2.0 mA min; compliance 19 V max.
- AC coupled, −3 dB at 0.5 Hz.
- 51.2 kS/s; alias-free up to 0.45 fs = 23.04 kHz; 100 dB stopband from 0.55 fs.

**Fit** [DERIVED]
- Output 1.45 V at 100 bar and 2.18 V at 151 bar abs.
- Bias plus signal is at most about 16.2 V, below the 19 V compliance.
- AC coupling: a flat pulse of length T reads about T/0.32 s low at its end (0.3 % at 1 ms, 3 % at 10 ms). Static levels therefore come from the 070BG chain.
- Excitation compatibility (PCB 20-30 V vs NI 19 V): TO-VERIFY with PCB and NI.

**Placement and price**
- Three sensors: one flush at the head, one at the transducer end of a flight-like 0.3 m line next to the 070BG, and one spare. Mounting adapter TO-SELECT.
- Price TO-QUOTE, delivered to Sønderborg, DK-6400 (BOM rows 237 and 238).
- BOM row 245 gains a hydraulic hand pump to ≥ 100 bar g for the B-PC-1 over-range row.

### 3.3 Folds

- **194 (1):** the FA-1 period domain is recorded in `pc_overrange_fa1.period_domain` and in BOM row 218. The port/line listing is requested from Mechanical and the spectrum from Combustion.
- **194 (3):** "E2 + 0.22 s" is marked WITHDRAWN in every unpurged-relight text. The baseline now has no unpurged relight, so Electronics recommends the ECU guard for v2.11 (not implemented).
- **194 (4):**
  - The 16.31 N margin is CONDITIONAL on Cd × A × G at the start lift.
  - CF-3 now has a start-lift point. Acceptance: F ≤ 16.31 N minus the heat allowance, or mdot ≤ 52.6-56.3 g/s.
  - The heat item moves to injector-body and feed soak-back (2.8-3.7 kW, owner Combustion).
  - GNC uses grain_q1d at 0.2039 mm; the ECU commands 0.2154 mm in the hold (section 5, item 13).

## 4. R2 command hold and S17 (LEAD 186 (2))

**Rule in the ECU.** In flight RUN, with Cmd::DROGUE 1 and Pc invalid:
- the thrust command is limited at once to min(FC command, 62.5 N);
- the hold ends at DROGUE 0 or when Pc is valid again;
- after the hold, the command returns at ≤ 2500 N/s;
- the ECU takes no drogue decision.

**Interface.**
- CMD_STATE cmd 17: arg 1 = attached, arg 0 = released; reset at power-up and at ARM.
- TLM_RELIGHT d6: b0-b5 refuse reason (mask 0x3F), b6 DROGUE echo, b7 PC_VALID.

**S17 setup** [SIM]: FC stand-in written by Electronics; F_cold from cold_flow_thrust_v2p4a; dead-vehicle term d_app of 0, 20.85 or 33.00 N.

**S17 results:**
- Flame-out with the hold: drogue kept; the FC sends ABORT at t_E2 + 0.5 s. Hold lift 0.2154 mm, F_cold 12.72 N. At the W6 bound one frame reaches ≥ 37.16 N (max 37.23 N).
- All-winds bound: the dead vehicle is released at E2 + 35 ms, as 186 (2) predicts.
- No DROGUE report (no hold): released at E2 + 55 ms at W6, and at E2 + 115 ms at 500 N.
- 5 N rms noise: dead vehicle released in 0/30 runs with the hold, 27/30 without.
- Lit starved plateau under the hold: the plant makes 51.2 N, not 62.5 N.
- W6 steady margin: 3.59 N = 16.31 − 12.72 [DERIVED]. Chamber heat is excluded and is TO-VERIFY.

**Limits:** d_app is a constant bound; the FC is a stand-in; the cold-flow thrust is an adiabatic bound; the plant runs on ASSUMED and Combustion inputs.

## 5. Contradictions and failures kept as evidence

1. **Purge cap vs 76 g** [DERIVED].
   - The 2.61 s cap allows 77.7 g (Combustion basis) or 83.6 g (SIL basis) of vented N2O; the hardware window bounds about 96 g.
   - Holding 76 g needs a cap ≤ 2.553 s. This is a LEAD decision (OI-PURGE-CAP).
   - gnc.json v3.1 calls 2.5 s the ECU duration cap; 2.5 s is actually the scheduled flow.
2. **S12 detection gap** [SIM].
   - V1 stuck open with V2 closed is not detected on the stand.
   - In flight it is flagged 5.05 s late (104 g through the bleed), against a < 0.5 s criterion (OI-BLEED-DETECT).
3. **S6** [SIM].
   - A small-amplitude gimbal jam is not detected (RE-24).
   - With the throat 70 % blocked at 500 N, HW_OVERPRESSURE comes first (expected cause 17, got 18), and Pc is 53.4 bar abs, above MEOP, for 72 ms. Accepted under OI-TB-MEOP; Mechanical carries LC-TB70.
4. **S9** [SIM]. The spike train trips PC_SENSOR on an unlit start, and the three ±1.034 bar TEB cases fail as in v2.9. B-PC-1 must show ≤ 0.3 bar.
5. **S13 B-extension.** "Every lit start reaches RUN" cannot hold under the 166 (1) rule, because of BASE_HIGH refusals and the torch gate at ≥ +1.0 bar. 32/164 and 64/164 runs fail.
6. **S5/S15 runs 125 and 127** (T_tank0 15.06 / 15.03 °C) end ARMED: IGNITE was refused TANK_COLD after a successful ARM. The mechanism is not isolated (OI-GUARD-BAND).
7. **Manifest undercount**, found by the author. Tool v1.2 and earlier listed 7 failing lines for 11 failed cases; v1.3 counts 11. The older hub manifests were checked and show no undercount.
8. **Generated headers.** gen_tables v3.3 fails on combustion v2.4a. Four values in use have no source text. gnc.json v3.1 arrived after the record (0 numeric change in the leaves read).
9. **Combustion v2.4a stale entries:**
   - E0 + 0.15 s (the ECU uses the torch gate, E0 + 160 ms);
   - t_E2 + 0.8 s (181 (4) says 0.5 s);
   - the 1.7 s interim with an unpurged relight;
   - the cold_flow text omits FLAMEOUT_OPT.
10. **E2 model mismatch.** Combustion's latency model uses E2 = Pc > 3 bar abs, which LEAD 134 withdrew. The ECU uses the relative rule. Neither side has checked the timing against the vapour gap of an unpurged start.
11. **Errors made and corrected during v2.10:**
    - a "181 (1)" citation, corrected to 181 (4);
    - an S12 disposition text;
    - a probe patch run on a scratch copy (the record binary was untouched);
    - Combustion republished v2.4a during the work, and the generator was re-run on it;
    - a config.h comment that misnamed the source of the 62.5 N level;
    - a superseded-v2 description of TLM_RELIGHT d6;
    - a KiCad README pointing at the old BOM;
    - the v2.9 hub omitted ignition_lift_v2.json and ignition_detect_margin_v1.json; both are published with v2.10.
12. **Relay wording.** The 194 relay called the 5 ms persistence "raw". The firmware applies it to the FILTERED channel (RE-20). I used the CHANGELOG and electronics.json wording.
13. **Three start/hold lifts are not reconciled:** 0.2154 mm (ECU hold, S17 map), 0.21776 mm (ECU ignition row at 286.70 K) and 0.2039 mm (grain_q1d start level, 194 (4)). CF-3 measures at the commanded hold lift with the encoder recorded.
14. **SIL ADC path.** sim.cpp limits the averaged 1 kHz reading at 4.95 V [ASSUMED] rather than each transducer sample. The comparator path does limit each step.
    - This matters only above full scale.
    - The over-range harness limits each sample.
    - The SIL record was not re-checked for this.
15. **Unannounced interim file.** An earlier v3 build (9052d894578990d4), without the 194 folds, stood unannounced in interfaces/ during this session. It is archived at archive/v3_interim/ and stated in CHANGELOG line 196.
16. **Stale label in spike_chain_v2p10.json.** It says "Persist 3 ms", but the tool computes with cfg::kPcOverPressureTime_s = 5 ms. Only the label is stale; the numbers are not affected. Not yet fixed in the published file.
17. **Sense-line rows are non-physical.** The linear model hits its floor in 640 of 896 cases, so these rows are a sensitivity only. The ~6 ms line period also comes from this ASSUMED-geometry model.
18. **Proof figure corrected.** An earlier draft figure for the 070BG proof in bar abs was wrong. It was corrected to 141.0 (140 bar g + 1.013) before publication; the summary counts did not change.
19. **Under-ranged stand sensor before 194.** The v2.10 B-DPC-1 sensor was the 113B24 (69 bar full scale), below both the FA-1 peaks and the ≥ 100 bar abs requirement. It is replaced by the 113B22.
20. **Stale test label.** test_core.cpp still writes "version": "v2.8.3" into test_core.json. Label only; it was left after RE-25.

## 6. Publication and housekeeping

**Hub**
- The v2.9 tree (405 files plus electronics_v2.json) was copied to 06-electronics/archive/v2.9/ and verified (SHA256SUMS.txt 5f5f9a172b41339d).
- Replaced with v2.10:
  - calc, docs, hardware;
  - firmware (src, sil, tools and Makefile; no build folder);
  - results: every v2.9 file is kept and the v2.10 files are added;
  - firmware_archive is kept as it was.
- interfaces/electronics.json is v3, 38bf149f368c1d4c.
- SHA256SUMS-v2.10.txt is 674eef94498822dd (502 entries), verified.
- There is no REPORT file in 06-electronics; this handback is the report.

**CHANGELOG**
- Lines 195-201 appended: 7 Electronics result lines.
- The append was guarded by the hash read just before it (f3dd884de680e626).
- The file is now 201 lines, c5da284c9c922632. Each line has 6 fields and owner electronics.

**Disk (LEAD request via the coordinator; workdir only)**
- 13 superseded SIL result folders (1610 files, 4.22 GB) became `results/archived_tar/*.tar.xz` (xz level 1, single thread, nice 19).
- Every file was re-hashed from its archive against the source list before the source folder was deleted. 0 failures.
- Freed 3.90 GB (3895967293 B). This equals the du change of results/, from 5.00 GB to 1.10 GB.
- INDEX_v2p10.txt (c0883a0d2677d5dc) holds every archive sha256 and lists the scripts that need an extraction before a re-run.
- Untouched: the hub copies of the sil_v2p9, sil_v2p8_2 and sil_v2p8_3 subsets, and the live sil_v2p10 runs.
- results/sil was re-created empty, because it is the default output folder of `make test` and `make run`.
- Main was sent the one-line note.

## 7. Done / partly done / not done

**Done** (digital, as described; evidence is SIM, DERIVED or DATASHEET)
- Firmware v2.10: test_core 309/0 and the SIL record (11 known failing lines).
- R2 command hold and S17.
- electronics.json v3.
- Schematic v2.5 (self-consistency checks only).
- BOM v2.2 and bench plan v3.
- 194 over-range study, stand-channel selection and the 194 folds.
- Hub archive and replacement, the CHANGELOG lines, and the disk request.

**Partly done**
- RE-02: criteria conflict.
- RE-05: no valve, no peak-and-hold, cap above 76 g.
- RE-07: drift measurement.
- RE-10: valve times ASSUMED.
- 070BG over-range: answered within the sweep only; the saturation and recovery data are MISSING.

**Not done**
- HAL (RE-06).
- Power budget and peak-and-hold (RE-09).
- Layout and the RE-15 checks.
- HIL reset test (RE-28).
- Bleed valve selection.
- FC side of R2, DROGUE and L*.
- The v2.11 items (offered only).
- gen_tables on v2.4a.
- Any hardware, HIL or target test.
- Independent review.
