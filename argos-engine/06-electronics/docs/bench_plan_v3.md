# ARGOS engine electronics: bench and test plan v3

06-electronics, 2026-10-13. Firmware v2.10 (SIL only), ECU schematic v2.5, BOM v2.2. Supersedes bench plan v2 (kept in the hub archive).
Electronics prepared this plan. The founders run the physical tests.

What changed from v2 (REV-ELEC-1 RE-13): every test now states the number it closes, the conditions, the instrument (BOM v2.2 line),
the statistic and a pass/fail criterion. New tests: B-PT-1 (tank-pressure calibration for the interlock guard band), B-DPC-1 (stand
dynamic Pc channel), B-SAFE-1 (stand safing after a no-light), CHK-PW (hardware purge window), HAL-1 and HIL-RST-1. B-BLEED-1, B-PC-1,
B-PNT-1, B-TVC-1, IGN-1 and B-FC-1 carry the REV-ELEC-1 §9 criteria and the LEAD CHANGELOG 166, 168, 172, 175, 181, 186 and 194 items.
Section 2 ends with the A1 pad go/no-go list (LEAD 181 (6)).

A SIL result is not hardware evidence, and neither is a matching hash, an ERC 0/0 or a passing UI check. Where a value is TO-VERIFY,
the test measures it. Where a pass value depends on a part that is not selected yet, the criterion names the datasheet quantity and
the test cannot pass until the part is selected; the number is not invented here.

Evidence tags: DATASHEET, DERIVED, ASSUMED, DESIGN, LEAD, REQ, SIM, TO-VERIFY. "REV §9" = REV-ELEC-1 §9 acceptance criteria (REQ).

Rules for every test:
- Record raw data at the rate given, the firmware build (SIL manifest tree hash, binary sha256/16, `config.h` first line), the
  board serial and the instrument calibration dates.
- Keep failed runs as evidence. A re-run gets a new run number and does not overwrite the old one.
- A test that changes a firmware constant ends with the constant change, a test_core run and the affected SIL scenarios re-run.

## 1. Order and gates

| Step | Test | Gate it closes | Needs |
|---|---|---|---|
| 0 | RE-15 board checks, HAL-1 | board fit for B-PC-1; HAL in place | schematic v2.5 + layout (not started) |
| 1 | B-PWR-1, B-PWR-2 | rails, e-fuse, ARM interlock, overlaps at 6.6 / 8.1 V (RE-09) | bare ECU, bench PSU |
| 2 | B-ECU-1 | I/O, CAN, watchdog, log v11, ladder decode with decade box (RE-19) | step 1 |
| 3 | B-PT-1, B-PC-1 | P_tank calibrated budget (guard band); Pc post-zero residual (`kBpc1Shown`), zero TC, 20 s drift; 070BG over-range (LEAD 194 (7)) | step 2, N2 0-70 bar g, reference gauge; hydraulic source to 100 bar g for the over-range row (BOM 245) |
| 4 | B-MV-1, B-PNT-1, B-TVC-1 | actuator timing, ENG-03, MV ladder, TVC jam threshold (RE-24) | step 2 |
| 5 | CHK-PW, B-BLEED-1 | purge window, valve, closure timing, purge mass, comparator, pad BIT | steps 1-4, selected valves (none yet) |
| 6 | B-IGN-1, B-FC-1 | spark EMI on Pc, FC link, TLM_FAST bits, ABORT path, PC_VALID, encoder TLM | step 2, FC |
| 7 | HIL-OT-1, HIL-TR-1, HIL-RST-1 | over-thrust and transient replay; reset behaviour (RE-28) | steps 2, 6, HAL |
| 8 | LEAK-1, CF-3, CF-4 | feed leak, ignition-lift table, segment void | Mechanical / Combustion rigs |
| 9 | B-SAFE-1 (procedure dry run), B-DPC-1, IGN-1, T1-T4 | relative light rule, start latency, LIGHT_SPIKE, F_acc | hot-fire stand |

Gate summary (REV §9): SIL/HIL freeze needs RE-01, RE-02, RE-03, RE-04, RE-05, RE-08, RE-11, RE-16, RE-20, RE-24 and the HAL.
First static fire needs, in addition, B-PC-1, B-IGN-1, HW comparator and LTC4365 thresholds measured, RE-12 quantified, RE-08 and
RE-17 closed. A1 needs RE-05 complete, RE-07 drift measured, RE-10 closure timing on the final path, RE-28 in HIL, purge ≤ 76 g.

## 2. Tests

### RE-15 board checks (before fabrication)
| Item | Criterion |
|---|---|
| Pin-function check of every custom symbol against its datasheet | signed table, one row per pin, 0 open rows |
| Real footprints | every BOM line with a footprint from the manufacturer drawing; 0 placeholder footprints |
| Layout + DRC | DRC 0 errors on the final layout (not started) |
| Derating table | every power part at ≤ the DESIGN derating (voltage ≤ 80 %, current ≤ 70 %, power ≤ 50 % of rating at 85 °C board) |
| ERC + netlist cross-check | re-run on the final design: 0/0. Self-consistency only; it does not replace the rows above |

### HAL-1: Teensy HAL (RE-06; LEAD 166 (9): Electronics open item, required before B-PC-1)
Status: not written. Test plan, run on the flight ECU with the HAL build:
| Check | Pass |
|---|---|
| Pin-15 exclusivity | heater output only in SAFE with the ARM bus off; V1 drive only with the ARM bus on AND PURGE_WIN high (scope on U574 out, 10 attempts per illegal combination, 0 violations) |
| Watchdog | MCU hang injected in SAFE, ARMED, RUN, COAST, PURGE: /OE of U304 and U307 cut ≤ the watchdog period (DATASHEET of the selected watchdog; record), all outputs safe |
| NV lockout | lockout bits b1/b2/b4 survive a power cycle and a watchdog reset (10 cycles) |
| CAN timing | TLM_FAST 500 Hz: period 2.000 ms ± 0.1 ms (DESIGN), 0 missing frames in 10 min; EVENT copies ×3 |
| 1 kHz tick | tick jitter ≤ 50 µs p99.9 (DESIGN) over 10 min with full CAN and log load |

### B-PWR-1 / B-PWR-2: power and arming (RE-09)
Conditions: VIN 6.6 V and 8.1 V (pack ends, DERIVED), bench PSU with a series source resistance equal to the measured pack
R_src (record), harness branch resistances R_branch as built.

| Overlap (each at 6.6 V and 8.1 V) | Record (scope + current probe, 100 kS/s) | Pass |
|---|---|---|
| PURGE entry: MV opener + latch + pintle rail + both bleed coils | ARM bus current, +12V_ARM, U3V70F12 input current and output droop | U3V70F12 input ≤ 7 A for ≤ 3 s and ≤ 10 A per cycle (DATASHEET as quoted, ecu_design.py); F301 I²t ≤ 50 % of its melting I²t (DESIGN; fuse I²t TO-VERIFY); no brown-out reset |
| E0: V2 + torch valves + spark dwell | same | same; reviewer estimate 12.1-15.7 A with the spark peak EXCEEDS the U3V70F12 rating (REV R17, DERIVED) - sequencing or added capacity required before this can pass |
| E0 + roll pulse pair | same | same |
| Purge 3 s, both coils held | +12V_ARM droop | rail inside the selected coil's rated band (DATASHEET, valve not selected) and U3V70F12 not current-limiting |

Firmware e-fuse of the TVC chain and LTC4365 thresholds (REV §9): OV trip 8.06-8.34 V, UV trip 4.96-5.14 V, no trip at 7.49 V when the
load is released; 5 trips each, all inside the band.
Status: the time-resolved budget (RE-09 action 1) and power sequencing (LEAD 166 (8): remove the E0 brown-out) are NOT done. This test
measures; it does not replace the design work.

### B-ECU-1: I/O, CAN and log
| Check | Pass |
|---|---|
| Every pin of `hardware/kicad/pin_map_v2p5.csv` | functional check, 0 failures |
| CAN frames against `protocol.h` v2.10 (TLM_FAST d4-d5 encoder lift, TLM_RELIGHT d6 b7 PC_VALID, EVENT 0x120) | decoder round trip, 0 CRC errors over 10 min |
| Log record v11 (179 B, CRC-16) at 1 kHz | 0 CRC errors, 0 missing records over 10 min |
| Watchdog /OE cut of U304 and U307 | both cut on an injected hang (10 trials) |
| MV ladder (pin 23) with the decade box (BOM 247) (RE-19) | each of the 10 codes decodes as its window in `results/hbleed_provision_v1.json`; OPEN+CLOSED decodes invalid; below the lowest edge decodes short_gnd; the pad-BIT harness step (tolerance 0.006) fails a 122 kΩ leak and passes +0.003 |
| Mode strap and NTC channels with the decade box | each code / temperature inside its window |

### B-PT-1 (new): tank-pressure channel calibration (LEAD 172 (4) guard band)
Closes `ptank_cal_ok` (runtime, NV record) and the calibrated P_tank interlock threshold 54.30 bar abs (Tsat 23.2 °C) instead of the
uncalibrated 50.34 bar abs (Tsat 19.8 °C) (DERIVED, `config.h` guard band). Until it passes, a pad or stand start needs the tank at or
below about 19.8 °C by pressure.

| Item | Value |
|---|---|
| Instrument | reference gauge / calibrator, uncertainty ≤ 0.05 bar (BOM 245) |
| Points | ≥ 6 pressures between 0 and 65 bar g, ≥ 3 up/down cycles, at 2 board temperatures spanning the pad range |
| Statistic | maximum absolute residual after the gain/offset fit, over all points and cycles |
| Pass | residual ≤ 0.3 bar AND the total calibrated budget recomputed with the measured residual ≤ 0.98 bar (`kTankPUncCal_Pa`) |
| Validity | 3 months (DESIGN); the NV record carries the date; an expired record clears `ptank_cal_ok` (HAL, not written) |

### B-PC-1: Pc chain (REV §9; LEAD 166 (1), (5))
Prerequisites: a flight ECU from a board that passed the RE-15 checks, and the HAL.
| Item | Pass |
|---|---|
| Accuracy | max post-zero residual ≤ 0.3 bar at ≥ 6 pressures 0-45 bar g, ≥ 3 cycles across the pad temperature range; reference ≤ 0.05 bar |
| Zero TC and 20 s drift (RE-07) | measured and reported; Mechanical supplies the transducer temperature MECO→RELIGHT; the A1 relight needs drift < 0.30 bar from the pad zero (second re-zero limit) |
| HW comparator | trips inside 30.68-32.26 bar g and above the firmware trip, 5 ramps |
| Over-range (LEAD 194 (7)) | on the SPARE 070BG (not the flight unit), hydraulic source and reference gauge: 70, 80, 90, 100 bar g (all below the 140 bar g proof, DATASHEET), 3 cycles. Record the output voltage at each step (saturation level: MISSING in the datasheet), the zero before and after (shift within the TEB ±1.5 % FS, DATASHEET) and the output after a fast release at ≥ 10 kS/s (recovery: MISSING; the release time bounds what can be shown). The result decides whether an FA-1 over-range reads ≥ 4.75 V (flagged, PC_SENSOR latched, HARD_START in IGNITION) or clips below it (silent); see electronics.json `pc_overrange_fa1` and results/fa1_overrange_v2p10.json (SIM) |
| `kBpc1Shown` | set only after RE-02 closes. The v2.10 S13 B extension still fails the lead criteria (32/164 runs with false, 64/164 with true; SIM) - kBpc1Shown stays false |

### B-DPC-1 (new): stand dynamic Pc channel (LEAD 172 (5); range and proof per LEAD 194 (7), REV-COMB-3 R3-10)
Sensor PCB Piezotronics 113B22 (BOM 237; replaces the 113B24 of BOM v2.2-v2.9, whose 1 kpsi = 69 bar range fails the ≥ 100 bar abs
requirement). One flush at the head; one at the transducer end of a flight-like 0.3 m sense line, next to the 070BG on a tee (end volume
recorded), for the line response (LEAD 194 (1): the Pc port and sense line are FA-1 listing candidates). NI 9234 + cDAQ (BOM 238).
Datasheet values (pcb.com 113B22 product page, read 2026-10-13; NI 9234 specifications 377849B-01, Feb 2025):
| Item | Value or pass |
|---|---|
| Range (≥ 100 bar abs, LEAD 194 (7)) | 5 kpsi = 344.75 bar at ±5 V (DATASHEET); useful over-range 10 kpsi at +10 V needs ≥ 24 V supply, not available on the NI 9234: usable range 344.75 bar (DERIVED) |
| Proof rating | maximum pressure 15 kpsi = 1034 bar (PCB's no-damage rating, DATASHEET) |
| Sensitivity | 1.0 mV/psi ± 10 % = 14.5 mV/bar (DATASHEET); 1.45 V at 100 bar (DERIVED); per-unit calibration certificate used |
| Sensor dynamics | resonance ≥ 500 kHz, rise ≤ 1 µs, low-frequency response (−5 %) 0.001 Hz, discharge time constant ≥ 500 s (DATASHEET) |
| Environment | −73 to +135 °C operating, flash temperature 1649 °C, acceleration sensitivity 0.002 psi/g (DATASHEET); RTV/ablative coating for the hybrid chamber TO-VERIFY with PCB |
| Excitation | NI 9234 IEPE 2.0 mA minimum, compliance 19 V maximum (DATASHEET); sensor bias 8-14 V (DATASHEET) + 1.45 V at 100 bar = ≤ 15.5 V (DERIVED). PCB lists 20-30 V excitation: compatibility of the 19 V compliance TO-VERIFY with PCB/NI |
| Coupling | the 8-14 V bias is outside the ±5 V input, so the channel is AC coupled: −3 dB 0.5 Hz, −0.1 dB 4.6 Hz maximum (DATASHEET). A flat pulse of duration T reads about T / 0.32 s low at its end (DERIVED, first order): 0.3 % at 1 ms, 3 % at 10 ms. Static levels come from the 070BG chain, not from this channel |
| Bandwidth | flat (± 1 dB) to ≥ 10 kHz including the mount (step or shock-tube test); alias-free to 23.04 kHz at 51.2 kS/s, stopband 100 dB from 0.55 fs (DATASHEET NI 9234). Mount: flush with seal rings 065A02 or recess with seal sleeve 065A05, clamp nut 060A03 5/16-24 (PCB accessories); a recess cavity lowers the bandwidth and is characterised in the step test |
| Time base | common with the stand DAQ and the ECU log, ≤ 1 ms (sync GPIO) |
| Use | IGN-1 and the T series. The flight LIGHT_SPIKE at 1 kHz on the 50 Hz filtered channel is a LOWER BOUND of the real spike (SIM: a 88 bar abs FA-1 head peak reads 63.4 bar abs, results/fa1_overrange_v2p10.json). The line-end sensor gives the 070BG port pressure against its 141.0 bar abs proof |
| Price | TO-QUOTE, delivered to Sønderborg, DK-6400 (BOM 237, 238); no price is entered |

### B-MV-1: main valve
| Item | Pass |
|---|---|
| Opener stroke and timing, 20 cycles | record; feeds S8/S10 timing |
| Holding-magnet release by the LTC4365 trip and by an ABORT frame | release ≤ 2 ms after the trip / frame (10 trials; SIM: same 1 ms tick) |
| OPEN/CLOSED switch codes through the J508 ladder | correct decode; harness open → `pmid_valid = false` and both switches false |

### B-PNT-1: pintle (ENG-03; REV §9)
| Item | Pass |
|---|---|
| Closing rate under load | ≥ 2500 N/s equivalent (5 F_max/s, LEAD), worst of 10 |
| Opening rate | ≥ the rate map (`results/pintle_rate_map_v1.json`) at every map point |
| Closed-loop t10-90 under load | ≤ 100 ms (amended ENG-03). SIL S5 v2.10 up-step p50/p95/max 0.105/0.126/0.142 s does NOT meet it (SIM; RE-23; v2.9 0.102/0.122/0.132 s) |
| HV69 speed and torque at 7.335 V and 7.49 V | measured (BOM 242 rig); fed into S5 (RE-04) |
| Stall monitor no-progress time | hardware value recorded (SIL clearance 46 ms against the 100 ms time path) |
| LTC4365 OV / UV | as B-PWR |

### B-TVC-1: gimbal (REV §9; RE-24)
| Item | Pass |
|---|---|
| Slew | ≥ 100 °/s at 7° at 7.4 V, both axes |
| FRF with `TVC_TEST_ENABLE 2` | recorded; notch centre frequencies set from it |
| Jam threshold (RE-24) | the detection bound on the as-built linkage is measured. SIL bound: a jam is detectable only for commands ≥ 3° per axis (2.12° along the servo line) with the 1.5° threshold; S6 gimbal_jam_moving_cmd (2° command) stays undetected (SIM). Lead to accept the bound or fund the travel-ratio detector (research proposal) |

### CHK-PW (new): hardware purge window (LEAD 166 (3); schematic v2.5)
PURGE_WIN = FC PURGE_EN (J512) AND LTC6993-1 one-shot (U572), ANDed into V1 (U574) and V2 (U575).
| Item | Pass |
|---|---|
| One-shot width at TP571, 10 triggers at 25 °C and at the board temperature extremes | 3.048-3.243 s (DATASHEET LTC6993 3.0 % grade + 0.1 % RSET; nominal 3.146 s) and ≥ 3.00 s powered span (DERIVED) |
| Non-retrigger | a second PURGE_EN edge inside the window does not extend it |
| PURGE_EN low | firmware commands V1, V2 and the heater pin: 0 coil current on both valves (current probe), TP570 low, 10 trials |
| PURGE_EN open wire / FC unpowered | window closed (R593 pull-down) |
| Latent stuck-high chain | with U573's output forced high on a bench fixture, the pre-flight check below detects it |

Pre-flight check (proposal, NOT in firmware v2.10): the FC holds PURGE_EN low while the ECU commands V1 open for one BIT step; P_mid
must stay low. A P_mid rise means the window chain is stuck high → BLEED_FAULT. The ECU cannot read PURGE_WIN (no free pin).
FC ICD items: PURGE_EN raised ≤ 20 ms before Cmd::PURGE (`kFcPurgeEnLead_s`, ASSUMED) and dropped at E0; raised for the pad BIT;
drive level 3.3 or 5 V TO-VERIFY.

### B-BLEED-1: head-end bleed (REV §9; LEAD 164, 166 (3))
Hardware: two NC valves in series (none selected: no candidate meets all four LEAD criteria, see the v2.10 report), restrictors
2 × 0.707 mm upstream of V1, the 170BG tee between V1 and V2 (mid volume ≤ 0.5 cm3, ICD), the peak-and-hold driver (not designed).
N2 first, then N2O at feed pressure; catch volume (BOM 249).

| Item | Statistic | Pass |
|---|---|---|
| Valve Kv | each valve, N2O at 55 bar | Kv ≥ 0.112 m3/h (4 × the restriction, Cd 0.7 ASSUMED; DERIVED) or seat ≥ 2 mm (LEAD) |
| Valve close time (command → flow stopped) | worst of 20 cycles at N2O feed pressure over the valve temperature range | ≤ 0.080 s (`kHbleedCloseTime_s`, ASSUMED); if longer, the constant, the cap and the schedule change and S12 is re-run |
| Valve open time | worst of 20 | ≤ 0.030 s (`kHbleedOpenTime_s`, ASSUMED); same rule |
| Closure step (V1 close command → vent seen → hold test passed) | worst of 20 | ends ≤ E0 + 0.130 s (deadline E0 + 0.160 s minus 30 ms; REV §9) |
| P_mid comparator | rise and fall against the reference gauge, 5 ramps | rise 8.95-10.79 bar g; fall 7.93-9.80 bar g |
| P_mid during the purge | bench DAQ at 1 kHz | above the rise band incl. TEB (13.34 bar g) plus margin, or computed clear of the band. Decided path: P_mid both open 0.06 × P_feed (SIM, ASSUMED) is BELOW the band - the path proof relies on the fill step |
| Purge mass per scheduled purge | 10 purges, weigh scale or Coriolis (BOM 244) | ≤ 76 g VENTED N2O (LEAD; vehicle-level mass leaving through the bleed = the tank-and-vehicle mass drop the scale sees). SIL estimate 78.6 g, Combustion 73.0 g (both ESTIMATES). Tank LIQUID depletion is larger: 81.6 g at 73.0 g vented, 8.6 g boils into the ullage (LEAD 181 (10)); tank-outlet coverage checks use the liquid figure, not this one |
| Purge mass at the firmware cap (both open 2.61 s) | 5 purges | ≤ 76 g vented; the cap allows 77.7 g (Combustion basis) / 83.6 g (SIL basis) (DERIVED) - expected to FAIL unless the measured flow is ≤ 28.6 g/s; the lead decides (cap ≤ 2.553 s holds 76 g on the Combustion basis) |
| Supply | with B-PWR-2 | +12V_ARM droop and U3V70F12 current with all overlapping loads at VIN 6.6 V |
| Pad BIT S0-S4 | each valve forced failed-open and failed-closed | every injected fault ends in BLEED_FAULT at the step listed in `config.h` |
| Leak monitor | V1 forced open, V2 closed | flag within 0.20 s + 5 ticks (SIM +0.21 s) |
| Release clamp | coil current and drain voltage at release, 20 cycles | V_DS peak < 60 V (42 V DERIVED for the SMAJ24A clamp); TVS energy per release inside its single-pulse rating; coil current ≤ 2.0 A (DMN6075S, DATASHEET) |

### B-IGN-1: igniter EMI (REV §9 via IGN-1; RE-18)
Spark train with the chamber vented, raw and filtered Pc at 1 kHz plus B-DPC-1.
| Item | Pass |
|---|---|
| P0 shift during the spark | ≤ 0.1 bar |
| Raw spikes during the spark | < 2 bar g |
| BASE_AMB / BASE_HIGH events | none |
| Propane backstop | 3-sample persistence holds on the recorded spike train (no trip on single samples) |
| Photodiode (FA-1) | dark level and spark pick-up recorded; the head must not report LIT on the spark alone |

### B-FC-1: FC link, drogue telemetry, ABORT path, R2 command hold (LEAD 168, 175, 181, 186)
CAN at 500 Hz with the FC. Transducer simulator (BOM 248) injects Pc.
| Check | Pass |
|---|---|
| TLM_FAST d1 | `state = d1 & 0x0F`; b4-b7 per spec; b7 only from the VALID filtered channel |
| Pc profile 0 → 2.5 bar g → 3 ms dip after E2 | b5 before E2; at E2 b4 + b5 + b6; b7 at E2 + 100 ms ± 1 ms without the dip; with the dip b6 clears and b7 never sets |
| t_E2 | EVENT STATE (RUN) t_ms equals the E2 tick |
| Pc invalid after E2 (simulator open) | RUN and t_E2 still reported; TLM_FAST d2-d3 = 0xFFFF; b7 clear (SIM: v210-15) |
| ABORT frame 0x010 (magic bytes 0xA5 0x5A, code, seq, CRC-8) | MV latch released ≤ 2 ms after the frame; pintle command 0 ≤ 10 ms; EVENT STATE (ABORT | CMD << 8) × 3; log abort_cause CMD. SIM: same tick, pintle 0 at +4 ms, valve closed +39 ms, needle seated +66 ms |
| TLM_RELIGHT d6 b7 PC_VALID (launch commit) | 1 with a valid channel; 0 on the invalid tick; back to 1 on recovery unless a PC_SENSOR fault or abort is latched; d6 & 0x3F = refuse reason (b6 = DROGUE echo, row below) |
| TLM_FAST d4-d5 encoder lift (500 Hz) | equals a reference displacement (dial gauge) within the encoder resolution at 5 positions; 0xFFFF with the encoder unplugged |
| PURGE commit deadline L* (LEAD 186 (1)) | FC rule, not an ECU check: PURGE commits iff the lead to the plain relight trigger is ≥ L* = 1.3 s (FC parameter, both brackets; replaces the 181 (2) interim value); below L* the FC sends neither PURGE nor RELIGHT on that pass and the drogue stays attached. Bench: the FC record shows no PURGE and no RELIGHT frame on a pass started with a lead below L* (replayed lead values on both sides of 1.3 s). The ECU does not know the plain trigger and does not check L* |
| Unpurged RELIGHT (no PURGE) | accepted; direct path when PRIMED (E0 on the command tick), prep path when UNPRIMED/UNKNOWN. Combustion v2.4a (purge_commit_rule_v2p4a, SIM/DERIVED) finds the unpurged branch refuted as written (light in the first slug, vapour gap after E2, A3 after the drogue release); LEAD 186 (1) decided: no unpurged relight below L* (FC rule). LEAD 194 (3) withdrew the 'E2 + 0.22 s' held-release alternative: it is a GNC comparator only (H ≥ 0.30 s with the ramp to 200 N, ≥ 0.19 s to 500 N, none with flow held at the start lift) and is not admissible with Pc invalid because of the 186 (2) hold. The ECU still accepts an unpurged RELIGHT; no flight use of it remains, and an ECU guard is offered, not implemented (OI-UNPURGED-RELIGHT). This row checks the ECU command behaviour only; it is not evidence that an unpurged start is safe |
| FC drogue rule R2, ADOPTED in design (LEAD 181 (4)): with Pc invalid, release iff ECU RUN AND accelerometer thrust ≥ 37.16 N for 3 frames at 100 Hz (baseline referenced at E0 for now), else hold the drogue and ABORT the ECU at t_E2 + pcf_tmax. pcf_tmax = 0.5 s (0.8 s NOT adopted) until GNC flies R2 v2; pcf_tmax, the threshold and the baseline reference are FC parameters | GNC's test; Electronics supplies the frames and the ABORT path above. ECU side SIM: v210-16 (Pc lost at E2 + 5/10 ms, ABORT frame at t_E2 + 0.5 s and + 0.8 s: ECU in RUN until the frame, ABORT/CMD on that tick, pintle command 0 at +4 ms). Bench: frame at t_E2 + 0.5 s from the FC with the simulator open |
| Cmd::DROGUE echo (LEAD 186 (2)) | CMD_STATE cmd 17 DROGUE arg 1 → TLM_RELIGHT d6 b6 = 1 on the next frame, arg 0 → 0; other args ignored; b6 = 0 after power-up and after an accepted ARM; accepted in every state. SIM: test_core v210-17 (incl. the CMD_STATE round trip) |
| R2 command hold (LEAD 186 (2), OI-38): flight build, RUN, DROGUE 1, simulator opened to invalidate Pc | thrust command held at min(FC command, 62.5 N) on every tick while Pc is invalid (Pc setpoint slew 250 bar/s still applies); log tlm_flags b0 (hold) and b1 (drogue) set; DROGUE 0 → hold off on that tick, command back at ≤ 2500 N/s; Pc valid again → hold off; no hold without DROGUE 1, with Pc valid, or on the stand build (stand: PC_SENSOR abort instead). SIM: test_core v210-17 (setpoint at the hold level after 26 ms against a 28 ms slew bound, the start ramp would take 55 ms; back to 200 N in 55 ms at ≤ 2.50 N/ms), SIL S17 (A1 relight, FC stand-in). Hardware: pintle encoder lift and Pc command in the hold on the DAQ; the hold-level thrust at the A1 state is a TO-VERIFY item for CF-3 (S17 plant 51.2 N at 0.215 mm against the 62.5 N target). LEAD 194 (4): the 16.31 N margin is CONDITIONAL on Cd × A × G at the start lift; CF-3 start-lift point below |

### B-SAFE-1 (new): stand safing after a no-light (LEAD 172 (1))
Procedure (stand, any start; pad first start): N2 purge ≥ 60 s at ≥ 10 g/s (≥ 0.6 kg; BOM 246 with flow indication), then hold
≥ 15 min before anyone approaches, with Pc at ambient (|Pc| ≤ 0.10 bar g) and the head TCs falling, then safing.
| Check | Pass |
|---|---|
| ECU lockout | CLEAR_LOCKOUT refused (refuse reason SAFING_HOLD 15) until 960 s after the abort; accepted after (SIM S10) |
| Boot during the hold | the hold restarts (NV b4) |
| N2 flow | measured ≥ 10 g/s for ≥ 60 s; the ECU cannot see the N2 flow, its timer is a lower bound only |

### HIL-OT-1 / HIL-TR-1 / HIL-RST-1 (RE-28; LEAD 166 (8))
Over-thrust and transient replay with the FC in the loop as in v1. HIL-RST-1: an ECU reset injected in ARMED, IGNITION, RUN, COAST and
PURGE (5 each). Pass: the ECU boots to SAFE, MV and both bleed valves closed, RUN never reported after the reset, the drogue not
released by the FC, NV lockout as specified. No in-flight recovery path exists (LEAD).

### LEAK-1, CF-3, CF-4 (Mechanical / Combustion rigs; Electronics instrumentation)
LEAK-1: feed leak at MEOP. CF-3: lift against T_tank (17 firmware rows, 0.1928-0.2520 mm; A1 row 286.7 K 0.2178 mm), Coriolis
reference (BOM 244); warm rows at 37.4 g/s are 0.8 % over the 37.1 g/s limit and must be re-checked. CF-3 start-lift point (LEAD 194 (4)):
mdot (Coriolis) and load-cell F at the start-level lift with the encoder lift recorded; acceptance F ≤ 16.31 N minus the heat allowance,
or mdot ≤ 52.6-56.3 g/s; a failure returns the hold level and the W10 rule to the LEAD. Three lifts are in play and are not reconciled:
the ECU ignition-lift row at 286.7 K (0.2178 mm), the lift the ECU commands in the R2 hold through the open-loop map (0.2154 mm in SIL
S17) and the grain_q1d start level (0.2039 mm, LEAD 194 (4)); measure at the lift the ECU commands in the hold and record it. Heat:
injector-body and feed soak-back temperature at the relight (heat at tank pressure, threshold 2.8-3.7 kW; TO-VERIFY, Combustion). CF-4: segment void after the
coast, P_mid and the bleed valve states on the DAQ, T4 crown / FD-01 tap temperatures if fitted.

### IGN-1 / T1: relative light rule on hardware (REV §9)
Record at 1 kHz: raw and filtered Pc, P0, rise, det flags, tlm flags, photodiode volts; B-DPC-1 (head flush and line end) at 51.2 kS/s.
| Item | Pass |
|---|---|
| E2 − light | ≤ the latency GNC accepts (SIL 16-18 ms) |
| Unlit maximum rise | ≤ 0.6 bar (rule 0.8 bar) |
| A3 ratio minimum | ≥ 0.45 |
| P0 shift during the spark / raw spikes | ≤ 0.1 bar / < 2 bar g |
| BASE_AMB | no event |
| b4 / b7 timing | as specified in B-FC-1 |
| LIGHT_SPIKE | logged (raw and filtered peak, time above 8 and 30 bar abs, time from light); compared with B-DPC-1 |
| Photodiode | lit rise and dark level measured; sets `kPhotoLitRise_V` (0.20 V placeholder) |

### T1-T4 F_acc
Thrust from the stand load cell against the accelerometer estimate (FC_THRUST), as in v1.

### GSE: launch commit wind (LEAD 181 (6): HARD rule for A1; was provisional in LEAD 161 (6))
Anemometer at 3 m (BOM 250): W10 < 6 m/s AND sigma_u(3 m) ≤ 1.0 m/s over the 10 min before ARM. Ground procedure: the ECU has no wind input.

### A1 pad go/no-go list (LEAD 181 (6); LEAD 175 (4); combustion.json v2.4 arm preconditions)
Every item is GO before the A1 launch commit. One NO-GO stops the count; the cause and the telemetry are logged. Nothing here is validated
on hardware yet: the ECU items are SIL evidence (v2.10) until B-ECU-1, B-BLEED-1 and B-FC-1 pass.

| Item | GO when | Source / owner |
|---|---|---|
| Wind | W10 < 6 m/s AND sigma_u(3 m) ≤ 1.0 m/s over the 10 min before ARM (anemometer at 3 m) | LEAD 181 (6) HARD rule; ground crew |
| Pc VALID | TLM_RELIGHT d6 b7 = 1 (Pc channel valid AND no latched PC_SENSOR fault or abort) | LEAD 175 (4); ECU v2.10, FC launch commit |
| Bleed closure | Before IGNITE: V1 and V2 commanded closed with the drivers inhibited, P_mid low, no EVENT HBLEED leak/fault and no MV fault bit in TLM_FAST d6-d7. In the sequence (automatic): the pad BIT S0-S4 runs in PREPRESS (first start, feed primed) and aborts BLEED_FAULT before IGNITION if a step fails, so no main N2O is admitted; the BIT result is not available at the launch commit | combustion.json v2.4 igniter.sequence.arm_preconditions; ECU v2.10 pad BIT (engine_ecu.cpp) |
| ECU armed | TLM_FAST state = ARMED. A refused ARM leaves the ECU in SAFE with the inhibit cause latched as the abort cause (e.g. TANK_HOT incl. the guard band, TANK_COLD, BAY_HOT, TVC_SUPPLY, MODE_MISMATCH, MAINT_JAM, RELIGHT_LOCKOUT, PC_SENSOR); DISARM clears it (engine_ecu.cpp armChecksOk). On the pad TLM_RELIGHT d6 & 0x3F reads NOT_COAST (10) by design: it is not an ARM refusal | ECU v2.10 interlocks |
| Drogue echo | TLM_RELIGHT d6 b6 = 0 after ARM (the accepted ARM resets the drogue state; the FC reports the deployment in flight with Cmd::DROGUE 1) | LEAD 186 (2); ECU v2.10 (test v210-17) |
| Purge window | CHK-PW passed on this board; PURGE_EN low at the pad (a stuck-high window chain is latent to the ECU) | LEAD 166 (3); Electronics (pre-flight firmware step proposed, not implemented) |


## 3. Outputs back to the design

| Result | Changes |
|---|---|
| B-PT-1 | `ptank_cal_ok` NV record; P_tank threshold 50.34 → 54.30 bar abs |
| B-PC-1 residual, drift | `kBpc1Shown` (only after RE-02 closes); second re-zero limits |
| B-BLEED-1 valve times | `kHbleedOpenTime_s`, `kHbleedCloseTime_s`, cap, schedule; S12 re-run |
| B-BLEED-1 mass | purge cap (lead decision); N2O budget line |
| CHK-PW | one-shot RSET if the width is outside the band; pre-flight check firmware step |
| B-PWR-2 | power sequencing or converter capacity (RE-09) |
| B-PNT-1 | S5 dispersion bands (speed_scale, J_int, latency) |
| B-TVC-1 | notch frequencies, jam threshold (RE-24) |
| IGN-1 | `kIgnRise_Pa`, `kIgnConfirmRelN`, photodiode thresholds, A3 margin |
| CF-3 | `kIgnLiftTab_m` rows; start-lift point per LEAD 194 (4): mdot and load-cell F at the commanded hold lift (encoder recorded), acceptance F ≤ 16.31 N minus the heat allowance or mdot ≤ 52.6-56.3 g/s; for GNC's R2 v2 and the S17 bound (OI-38) |
| B-PC-1 over-range | 070BG saturation level and recovery (MISSING in the datasheet): whether an FA-1 over-range is flagged (≥ 4.75 V) or silent (LEAD 194 (7)) |
| B-DPC-1 | head and line-end dynamic Pc: the sense-line response for the Pc port / sense line FA-1 listing (LEAD 194 (1)) and the 070BG port pressure against its 141.0 bar abs proof |
| B-FC-1 DROGUE / R2 hold | OI-38 hardware evidence; `kR2HoldThrust_N` kept or re-set against the measured hold-level thrust |
| HIL-RST-1, HAL-1 | RE-06, RE-28 closure |
