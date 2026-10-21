# ARGOS engine electronics: bench and test plan v5

06-electronics, 2026-10-21. Firmware v2.12 (SIL only), ECU schematic v2.5 (the v2.11 board changes are DESIGN rows in BOM v2.3;
schematic v2.6 is NOT drawn), BOM v2.3 (`results/bom_v2p3.csv`) with the v2.12 text changes of rows 205 and 251 in
`results/bom_v2p4.csv` (no new line numbers). Supersedes bench plan v4 (docs/bench_plan_v4.md 5b1c9336d7b8db50, kept).
Electronics prepared this plan. The founders run the physical tests.

What changed from v4 (REV-ELEC-3 R3-01 option (b) as the working basis (LEAD 2026-10-21T11:25Z), R3-02, R3-03, R3-05, R3-06, N-01,
N-07; LEAD CHANGELOG 253 (7)(i)-(ii), 256 (2), 257 (2), 258 (2)-(4), 259 (F4), 261; REV-COMB-4 R4-09, R4-12, R4-13):
- F-14: the LC-TB70 v2 rules quoted verbatim from mechanical.json v2.4 (J-FWD replace rule on Q_JFWD > 60.0 bar abs, no minimum
  duration; the envelope and one-Z3-per-assembly rules), the TB-state abort set as confirmed by Mechanical (F4) with PC_SENSOR HIGH,
  and the Q_JFWD signal per platform (SIL exact, stand B-DPC-1 after a noise record, flight C1 LIGHT_SPIKE raw >= 47.5 bar abs).
  The v4 citation (electronics_v4 l.6575, "bench plan v4 F-14") is corrected in electronics_v4.1.json.
- F-13: the soak condition and the facility thermometer accuracy (R3-06). F-6 / F-10 / BOM 251: the C1 compensated band (R3-05).
- B-PC-1: the zero TC per serial (seat coefficient and T_cal for option (b)), the seat-TC channel and the ARM sanity static term rows;
  the comparator band with the uncompensated drift (R3-01 item 8); the over-range margin on the R4-09 face bound.
- B-DPC-1: the stand Q_JFWD row. B-TC-1: the CJTO trim step and the EMI mean-shift pass (R3-03). B-MV-1: post-abort closure (N-01).
- B-BLEED-1 / CHK-BT: the purge FINAL (2.43 s flow, 2.39 s cap, calibration constants, rule (d) with (d1) / (d2), PURGE at E0 - 2.90 s).
- T1-T4: the DC-C / DC-D segments and the re-sized T4 firing planned inside A = 150 C at the B1 end-of-burn heating rate (N-07).
- B-ECU-1: log v13 (185 B). A1 pad go/no-go: the seat-compensation row.

What changed from v3 (REV-ELEC-2 R2-02, R2-06, R2-13, R2-14, R2-19, R2-22; LEAD CHANGELOG 203 (2), 205, 206 (3), 216 (2)(c), (5), (6),
(9), 230 (3)-(4), 243 (3), 248 and the Part A rulings of 2026-10-20): section 0 (founder block); B-PC-1 on C1; B-TC-1 and CHK-BT;
B-FC-1 lost-DROGUE-0 and lift-commanded R2 hold; B-BLEED-1 on the one flow basis; R2-13 residuals; HIL-OT-1 / HIL-TR-1 written out.

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
- Prices: none in this plan. Every purchase is an RFQ to the named vendor, TO-QUOTE delivered to Sønderborg, DK-6400; no price is
  entered until a quote is in hand (no 0 and no "from" prices).

## 0. Founder block: executable now (LEAD CHANGELOG 216 (6), REV-ELEC-2 R2-06)

None of these needs the ECU, the layout, the HAL or the FC. Each row says what it closes. Order: the RFQs and inquiries first (lead
times), then F-11 / F-12 when the instruments arrive. Record every answer and quote with its date in the founder action list.

| # | Action | Content | Closes / feeds | Done when |
|---|---|---|---|---|
| F-1 | RFQ BOM 237 | PCB Piezotronics 113B22 × 3 (two in use, one spare) with calibration certificates; flush seal rings 065A02, recess seal sleeves 065A05, clamp nuts 060A03 5/16-24; mounting adapter TO-SELECT; delivered DK-6400 | B-DPC-1, IGN-1, T series | quote with lead time on file |
| F-2 | RFQ BOM 238 | NI 9234 + CompactDAQ chassis + 10-32 low-noise coax (length TO-DEFINE); delivered DK-6400 | B-DPC-1 | quote on file |
| F-3 | RFQ BOM 244 | Coriolis mass-flow meter, liquid N2O service, 0-200 g/s class, response ≤ 100 ms, O2-clean (RE-22 note on the row); Endress+Hauser DK first, Emerson / Bronkhorst as alternates | CF-3, B-BLEED-1 (mdot for the measured-time purge cap, LEAD 216 (5)) | quote on file |
| F-4 | RFQ BOM 245 | reference pressure gauge / calibrator 0-100 bar, uncertainty ≤ 0.05 bar, traceable certificate; hydraulic hand test pump to ≥ 100 bar g RESERVED for units that never see N2O (R2-14); a clean dry-N2 path (regulator + manifold) for N2O-wetted units | B-PT-1, B-PC-1, F-12 | quote on file |
| F-5 | RFQ BOM 250 | anemometer at 3 m (ultrasonic or cup) with ≥ 1 Hz output, 3 m mast, logger with a UTC time base | GSE wind rule (LEAD 181 (6) HARD) | quote on file |
| F-6 | RFQ BOM 251 (Electronics addition) | Kulite XTL-190SM-2000A × 3 + 1 spare: absolute mode, M5 × 0.8 short body, O2-clean processing, FKM or metal seal instead of the supplied silicone O-ring. Compensated band (R3-05; the v4 "20-120 °C" is WITHDRAWN: the sheet offers "any 100 °F range", 55.6 K): order the 100 °F band 0-55.6 °C (32-132 °F) from the coldest ARM (flight ambient 0 °C, stand ≥ 0 °C ASSUMED) through the hottest flight A1 relight seat (40 + 14.7 = 54.7 °C at the light [DERIVED, Mechanical SIM rise from ARM]); the stand relight after a B1-length burn reaches about 78 °C at E1 (24 + 54.4 K [DERIVED]), outside any 100 °F band that starts at 0 °C: F-10 (b) | flight Pc / P_feed / P_mid (LEAD 205, 206 (3)); option (b) seat compensation | quote and the inquiry F-10 answered |
| F-7 | TE inquiry (M3234-000005-070BG) | (a) output above full scale: the saturation voltage, (b) recovery time after an over-range, (c) zero shift after an over-range of 70-100 bar g (below the 140 bar g proof), (d) the rise time of the 0.5-4.5 V output (the datasheet rows are for mV / mA outputs, R2-17); (e) whether TE has a unit for the line-205 requirement as a second source to C1: seat-mounted, body within Ø12 × 30 mm above a named thread, front dead volume ≤ 20 mm³, proof ≥ 166 bar abs (lead ruling 2026-10-20: 1.1 × FA1S 151.04), range covering the 45 bar MEOP with the 30 bar abort resolvable, operating ≥ 120 °C, N2O / O2 compatible | 070BG behaviour (stand reference, P_torch); second source | written answer on file |
| F-8 | PCB inquiry (113B22) | (a) operation from the NI 9234 IEPE source (2.0 mA, 19 V compliance) with the 8-14 V bias and 1.45 V at 100 bar: does the full 344.75 bar range hold? (b) coating (RTV / ablative) for a hybrid N2O chamber; (c) the conditioner PCB recommends if 19 V is not enough (482C series model; BOM 265 fallback) | B-DPC-1 excitation (LEAD 203 (7) TO-VERIFY) | written answer on file |
| F-9 | NI inquiry (NI 9234) | IEPE compliance at 2.0 mA with the 113B22; AC coupling with IEPE OFF behind an external conditioner (BOM 265); external sync / trigger with the stand DAQ | B-DPC-1 | written answer on file |
| F-10 | Kulite inquiry (XTL-190SM-2000A) | ordering code in absolute mode at 2000 psi; compensated band (R3-05): (a) the 100 °F band 0-55.6 °C of F-6 and (b) a wider compensated band 0-85 °C (coldest ARM to the hottest stand relight seat + margin) if offered; for each, the thermal zero shift MAXIMUM (the sheet gives ±1 % FS / 100 °F typical only = 0.0248 bar/K; the firmware residual budget uses k = 3 and the SIL S13T sweeps k 1-3, ASSUMED) and the zero non-linearity over the band; seal options; O2-clean processing; cable mass per metre (the mass delta uses 10 g/m ASSUMED); shock rating (MISSING in the sheet); current datasheet revision; delivery to DK-6400 | BOM 251, the mass statement, B-PC-1 zero-TC row, kPcRezeroMax_Pa basis | written answer on file |
| F-11 | anemometer mast and logger (BOM 250) | set up at the launch site: 3 m mast, ≥ 1 Hz logging with UTC time; compute W10 (10-min mean) and sigma_u(3 m) (10-min standard deviation of the along-wind component); dry run of the launch-commit rule over one afternoon with the 10-min windows logged | W10 < 6 m/s AND sigma_u ≤ 1.0 m/s is HARD for A1 (LEAD 181 (6)); the R2 0.8 s window is confirmed only inside it (S17 v2.11) | one logged day; the rule evaluated on it |
| F-12 | spare-070BG over-range row (LEAD 203 (2), 216 (6); moved from B-PC-1) | on the SPARE 070BG (label it "HYDRAULIC ONLY - NEVER N2O"; it never returns to N2O service): bench supply 5.00 V (inside 4.75-5.25 V), bench DAQ ≥ 10 kS/s (no ECU), hydraulic pump + reference gauge (BOM 245). Steps 70, 80, 90, 100 bar g (all below the 140 bar g proof, DATASHEET), 3 cycles. Record the output at each step (saturation level: MISSING in the datasheet), the zero before and after (shift within the TEB ±1.5 % FS, DATASHEET) and the output after a fast release at ≥ 10 kS/s (recovery: MISSING; the release time bounds what can be shown) | after line 205 this characterises the 070BG kept for P_torch (J901) and as the B-PC-1 static reference, NOT the flight Pc (C1) | data and a one-page note on file |
| F-13 | stand T0 rule (LEAD ruling 2026-10-20; basis LEAD 249 (2): 20 + 4.48 / 0.96 = 24.67 °C less 0.5 K for the facility thermometer) | founder pre-fire checklist row (R3-06): the engine SOAKED at the stand ambient: both case TCs TC1 / TC2 within 1 K of the facility thermometer for at least 30 min [DESIGN], with the facility thermometer calibrated to ±0.5 K (certificate on file), and that reading ≤ 24 °C (297.15 K) before any stand ARM; the ECU refuses a stand ARM above 24 °C on TC1 / TC2 (Abort CASE_WARM_STAND 31, a backstop; the checklist is the control) | stand start temperature basis of the case-TC rows | checklist row in use |
| F-14 | J-FWD replace rule and TB-state (LC-TB70 v2; LEAD 248, 258 (3); Mechanical F4, line 259) | (1) Quoted verbatim from mechanical.json v2.4 lc_tb70_envelope_v352.jfwd_replace_rule_v2.rule: "J-FWD REPLACE RULE (LC-TB70 v2): when Q_JFWD of a run's head-end pressure exceeds 60.0 bar abs at any time, the joint counts as used: before the next run the line-231 J-FWD inspection (C6 (2) list: the ten ENG-HW-101-IN718 screws and their HW-170 springs replaced, new, single-use; the TC-01 holes gauged with the pins GO 5.50 / NO-GO 5.62, a hole that takes the 5.62 pin rejected; hole edges and the bore within 3 mm of a hole at 10x; S01 / S02 replaced; the removed screws inspected per C6 (3)) and the TC-02 taps gauged (M5-6H GO / NO-GO)". (2) The quantity, verbatim (.quantity): "Q_JFWD = max(the head peak over the record, max over T in 0.2-0.5 ms of S(T) on the light window (record start before the light to 150 ms after the first crossing of 8 bar abs, from rest, held after it) and on each excursion window (50 ms before to 150 ms after an upward crossing of 45 bar abs later than the light window, from equilibrium at its start)); S(T) the undamped SDOF ESP of Z3 v2; sample step <= 0.05 ms in the windows, else Q_JFWD is a lower bound (the peak)"; level 60.0 bar abs, duration: none (one exceedance at any time in the run). (3) Envelope rules, verbatim (.rules[1], [2]): "an event that leaves the envelope is outside the structural basis: no margin claim, engine quarantined for inspection (v1, kept)"; "one Z3 event per J-FWD assembly: the line-231 basis is a one-off abnormal event; a second Z3 excursion before the replacement is outside the envelope (stated in v2; OPEN for the lead where it bears on the flight relight)". (4) Founder rule (LEAD 248), beside (1): after ANY case-TC abort (Abort OVER_TEMP 6 from TC1 / TC2 at 423.15 K) or a TB-state abort the J-FWD joint counts as used: the same inspection as (1) before the next firing. TB-STATE ABORT = the ECU abort cause HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START, OVER_TEMP, or PC_SENSOR on the HIGH side (transducer output ≥ 4.75 V = 146.5 bar abs); the LOW side (below 0.25 V: open wire, short) is NOT one; OVER_THRUST is information only (Mechanical F4 verdict, verbatim: "CONFIRMED, with one addition: PC_SENSOR raised on the HIGH side (transducer output >= 4.75 V = 146.5 bar abs: the stand latches and aborts; in flight the non-sticky over-range bit, log v12 ovr_flags b0)"). Firmware v2.12 latches it as f3 TB_STATE (log v13 f3_flags b0; b1 TB_PCS_HIGH for the HIGH cause), cleared at the next ARM. (5) Signal for Q_JFWD: stand = B-DPC-1 DC-restored with C1, sample step ≤ 0.05 ms in the windows, Q_JFWD computed post-run with inside_v2 (04-fea/v352/lc_tb70_envelope.py d14489808338006b), usable only after a no-event B-DPC-1 noise record has been run through inside_v2 (B-DPC-1 row; TO-VERIFY: until a noise-floor rule is derived and reviewed, a noise-driven trigger still means the inspection); flight = the C1 LIGHT_SPIKE raw peak ≥ 47.5 bar abs sets f3 JFWD_LS (log v13 b5) [DERIVED from the C1 chain model on the 896-case grid: 0 misses of the 298 Q_JFWD > 60 cases on each of the four C1 chains (lowest raw peak among them 47.750 bar abs), and 128-152 of the 598 other cases flagged as well; TO-VERIFY on hardware; the ideal sampler gives 40.381 bar abs, information]; the 1 kHz flight record is a LOWER BOUND and Z3 v2 is NOT EVALUATED in flight. In flight the joint cannot be replaced before the relight (OPEN, lead) | joint life (Mechanical) | rule in the stand procedure; the post-run Q_JFWD script on the stand PC |

## 1. Order and gates

| Step | Test | Gate it closes | Needs |
|---|---|---|---|
| F | section 0 (founder block) | RFQs, inquiries, anemometer, spare-070BG over-range, stand rules | nothing: executable now |
| 0 | RE-15 board checks, HAL-1 | board fit for B-PC-1; HAL in place | schematic v2.6 (the v2.11 rows of BOM v2.3; NOT drawn) + layout (not started) |
| 1 | B-PWR-1, B-PWR-2 | rails, e-fuse, ARM interlock, overlaps at 6.6 / 8.1 V (RE-09) | bare ECU, bench PSU |
| 2 | B-ECU-1 | I/O, CAN, watchdog, log v13, ladder decode with decade box (RE-19) | step 1 |
| 3 | B-PT-1, B-PC-1, B-TC-1 | P_tank calibrated budget (guard band); C1 Pc trims, post-zero residual (`kBpc1Shown`), zero TC per serial (seat coefficient and T_cal, option (b)), seat-TC channel, 20 s drift, comparator; case-TC CJTO trim, offset and tau | step 2, clean dry N2 0-70 bar g, reference gauge (BOM 245), TC reference (BOM 266), temperature chamber 0-85 °C (TO-DEFINE) |
| 4 | B-MV-1, B-PNT-1, B-TVC-1 | actuator timing, ENG-03, MV ladder, TVC jam threshold (RE-24) | step 2 |
| 5 | CHK-PW, CHK-BT, B-BLEED-1 | purge window, both-open timer, valve, closure timing, purge mass, comparator, pad BIT | steps 1-4, selected valves (none yet) |
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
| E0: V2 + torch valves + spark dwell | same | CANNOT PASS AS DESIGNED: reviewer estimate 12.1-15.7 A with the spark peak exceeds the U3V70F12 rating (REV R17, DERIVED). OPEN DESIGN ITEM OI-E0-SUPPLY, owner Electronics (RE-09 / LEAD 166 (8)): power sequencing at E0 (spark dwell after the valve pull-in) or added +12V_ARM capacity, decided before the layout; this row is run after that change |
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
| CAN frames against `protocol.h` v2.12 (TLM_FAST d4-d5 encoder lift, TLM_RELIGHT d6 b7 PC_VALID, EVENT 0x120 incl. R2_BACKSTOP 0x24) | decoder round trip, 0 CRC errors over 10 min |
| Log record v13 (185 B = v12 + seat_comp_hPa int16 + seat_ref_dK int16 + f3_flags uint8, CRC-16; `kLogVersion` 13) at 1 kHz | 0 CRC errors, 0 missing records over 10 min; f3 bits b0 TB_STATE, b1 TB_PCS_HIGH, b2 SEAT_COMP, b3 SEAT_FROZEN, b4 SEAT_NOREF, b5 JFWD_LS, b6 PT_RZ_REJ decode as set by the injected conditions |
| Watchdog /OE cut of U304 and U307 | both cut on an injected hang (10 trials) |
| MV ladder (pin 23) with the decade box (BOM 247) (RE-19) | each of the 10 codes decodes as its window in `results/hbleed_provision_v1.json`; OPEN+CLOSED decodes invalid; below the lowest edge decodes short_gnd; the pad-BIT harness step (tolerance 0.006) fails a 122 kΩ leak and passes +0.003 |
| Mode strap and NTC channels with the decade box | each code / temperature inside its window |

### B-PT-1 (new): tank-pressure channel calibration (LEAD 172 (4) guard band)
Closes `ptank_cal_ok` (runtime, NV record) and the calibrated P_tank interlock threshold 54.30 bar abs (Tsat 23.2 °C) instead of the
uncalibrated 50.34 bar abs (Tsat 19.8 °C) (DERIVED, `config.h` guard band). Until it passes, a pad or stand start needs the tank at or
below about 19.8 °C by pressure.

| Item | Value |
|---|---|
| Instrument | reference gauge / calibrator, uncertainty ≤ 0.05 bar (BOM 245); clean dry N2 only on N2O-wetted units (the hydraulic pump is reserved for never-N2O units, R2-14) |
| Points | ≥ 6 pressures between 0 and 65 bar g, ≥ 3 up/down cycles, at 2 board temperatures spanning the pad range |
| Statistic | maximum absolute residual after the gain/offset fit, over all points and cycles |
| Pass | residual ≤ 0.3 bar AND the total calibrated budget recomputed with the measured residual ≤ 0.98 bar (`kTankPUncCal_Pa`) |
| Validity | 3 months (DESIGN); the NV record carries the date; an expired record clears `ptank_cal_ok` (HAL, not written) |

### B-PC-1: Pc chain on the C1 transducer (REV §9; LEAD 166 (1), (5), 205, 206 (3))
Prerequisites: a flight ECU from a board that passed the RE-15 checks (schematic v2.6 with the INA333 chains), the HAL, a C1 unit (BOM
251) on a calibration manifold next to the 070BG static reference (BOM 199), clean dry N2 and the reference gauge (BOM 245). The same
rows run for P_feed and P_mid (same family, same conditioning).
| Item | Pass |
|---|---|
| Zero and span trims (select-on-test) | REF divider chosen so that 0 bar abs reads 0.10 Vexc ± 2 mV and RG (E96, 946-1911 Ω) so that full scale spans 0.80 Vexc ± 0.5 % (DESIGN, pc_transducer_v3 E); values recorded per serial |
| Accuracy | max post-zero residual ≤ 0.3 bar at ≥ 6 pressures 0-45 bar g (absolute reading: add the barometric reading), ≥ 3 cycles across the pad temperature range; reference ≤ 0.05 bar. Expected error budget at 30 bar abs 0.77 bar RSS / 1.14 bar linear sum (DERIVED, typ thermal terms; the max terms are MISSING in the sheet) |
| Zero TC per serial (R3-01 option (b), R3-05) | in a temperature chamber with the seat TC (TC4, BOM 205 at the C1 boss as flown) fitted: the zero at ≥ 6 temperatures over 0-85 °C (coldest ARM to the hottest stand relight seat + margin), 2 cycles, reference ≤ 0.05 bar; fit the coefficient [Pa/K] (linear) and T_cal (the temperature of the XdcrCal::offset_Pa zero); record them per serial (table below) and load them with setPcSeatCoef / setPcSeatTcal (SAFE only). Pass: |coef| ≤ 1.0e4 Pa/K (firmware bound) and the fit residual over each ARM → relight span used (A1 ARM → re-zero2 12.5 K; stand ARM → re-zero2 50.4 K [DERIVED, Mechanical SIM]) ≤ 10 % of coef × ΔT (the eps of the option (b) residual budget: A1 0.185 / 0.027 bar, stand 0.551 / 0.054 bar at k = 3 [DERIVED]); otherwise the budget is re-done with the measured residual before kPcRezeroMax_Pa (0.30 bar) is kept. A stand relight after a B1-length burn needs ≤ 5 % at k = 3: with the coefficient 10 % low the SIL stand relight is REFUSED NOT_VENTED at k ≥ 2 (safe, no light; S13T comp_under [SIM]) |
| 20 s drift (RE-07) and post-burn zero | the A1 relight needs the COMPENSATED residual < 0.30 bar from the ARM zero (re-zero limit kPcRezeroMax_Pa); 20 s drift at 25 and 55 °C ≤ 0.05 bar; at the first static fire the post-burn zero check logs seat_comp_hPa / seat_ref_dK (log v13) against the vented-chamber reading (LEAD 205 closures) |
| Seat-TC channel (TC4: MAX31856 U904, J904, BOM 205; option (b)) | offset ≤ 0.3 K against BOM 266 at 0 / 25 / 85 °C after the CJTO trim (as B-TC-1); time constant ≤ 0.25 s on the boss (the SIL lag); TC open at ARM → f3 SEAT_NOREF and compensation OFF for that arming; TC open or a jump > 150 K after ARM → f3 SEAT_FROZEN (last value held); 5 trials each |
| ARM sanity static term (v2.12) | soaked at 0, 20 and 40 °C (chamber), vented: the reading minus coef × (T_seat − T_cal) within 0.5 bar (kPcArmZeroMax_Pa) and ARM accepted; with the coefficient 0 (v2.11 fallback) the uncompensated zero shift k × 0.0248 bar/K × (T0 − T_cal) is checked alone: ARM refused PC_SENSOR beyond 0.5 bar (SIL S13T before the static term, and the v2.12 fallback runs: refused at 0 / 40 °C for k ≥ 1.5, and on one sign at k = 1.0 [SIM]) |

Per-serial record (B-PC-1 zero-TC row; loaded at boot by the HAL; SAFE-only setters):

| Serial | coef [Pa/K] | T_cal [K] | fit residual [bar] over 0-85 °C | span A1 12.5 K / stand 50.4 K residual [bar] | date, run |
|---|---|---|---|---|---|
| (C1 #1) | MISSING | MISSING | MISSING | MISSING | |

| HW comparator U330 (C1 tap 47.5k / 47.5k, threshold 174k / 29.4k) | trips inside 31.08-34.11 bar abs (DERIVED band; nominal 32.59) and above the firmware 30.0 bar abs, 5 ramps at 25 °C; default build tau 5.225 ms; ride-through build (C330 + C330B, 540 nF) tau 12.10-13.55 ms measured by a step. U330 is NOT seat-compensated: the C1 thermal zero shift moves its band by k × 0.0248 bar/K × (T_seat − 20 °C) (A8, results/v2p12/c1_drift_v2p12.json [DERIVED]): k = 3, stand relight light at T0 24 °C 26.62-38.56 bar abs, A1 burn end at T0 40 °C 28.44-36.74; repeat 3 ramps with the C1 at 55 °C to confirm the shift sign and size per serial |
| Open wire (pc_transducer_v3 E open_wire) | SIG+ open and SIG- open read LOW (< 0.25 V, PC_SENSOR); EXC+ open, EXC- open and SIG+/SIG- short: record the output (MISSING: INA333 outside its common-mode range) and the firmware reaction; a HIGH reading must trip the comparator |
| Over-range (C1) | NOT required for flight (0 of 896 FA-1 cases reach 146.5 bar abs, SIM). R4-09: the Pc-port face bound is 130.2 / 131.3 / 130.5 bar abs over c 181-1200 m/s (CC-1 6 mm3 / CC-1 20 mm3 / CC-2) [Combustion v2.4c], so the margin to the 137.9 bar abs FS is ≥ 6.6 bar at c ≥ 181 m/s (not about 16 bar), 15.2 bar to the 4.75 V level 146.5 bar abs [DERIVED]; the 070BG row is F-12 |
| `kBpc1Shown` | set only after RE-02 closes; stays false in v2.12 (the SIL runs both builds) |

### B-DPC-1 (new): stand dynamic Pc channel (LEAD 172 (5); range and proof per LEAD 194 (7), REV-COMB-3 R3-10)
Sensor PCB Piezotronics 113B22 (BOM 237; replaces the 113B24 of BOM v2.2-v2.9, whose 1 kpsi = 69 bar range fails the ≥ 100 bar abs
requirement). One flush at the head next to the C1 seat; the flight sense line is DELETED (LEAD 205), so the second in-use unit moves
to the stand reference port next to the B-PC-1 070BG (position TO-DEFINE with Mechanical) or stays the spare. NI 9234 + cDAQ (BOM 238);
fallback conditioner BOM 265 if F-8 / F-9 answer "not at 19 V".
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
| Use | IGN-1 and the T series. The flight LIGHT_SPIKE at 1 kHz on the 50 Hz filtered channel is a LOWER BOUND of the real spike (SIM). The head unit gives the FA-1 pressure-time history at the C1 seat (the face peaks 104-125 bar abs of the ASSUMED construct vs Combustion's 102 bar ultimate is an open contradiction, v2.11 report) |
| Q_JFWD (LC-TB70 v2 J-FWD replace rule, F-14) | DC-restore with the C1 channel (pre-light level and the first-order coupling inverted); sample step ≤ 0.05 ms in the windows (51.2 kS/s = 0.0195 ms); the whole run from before the light (first sample ≤ 2.0 bar abs); inside_v2(t, p) post-run (log inside, zone_max, ESP max and its period, Q_JFWD, jfwd_rule_triggered). FIRST a no-event record (stand pressurised, no firing, ≥ 60 s) through inside_v2: Q_JFWD and the ESP of the noise alone logged (TO-VERIFY; until a noise-floor rule is derived and reviewed a noise-driven trigger still means the inspection) |
| Price | TO-QUOTE, delivered to Sønderborg, DK-6400 (BOM 237, 238); no price is entered |

### B-TC-1 (new): case-TC channel (Part A, LEAD rulings 2026-10-20; LEAD 243 (3))
Case TCs J605 / J606 (type K, Class 1, junction 13.5 ± 0.5 mm aft of the injector face), MAX31856 U604 / U605, abort 423.15 K with
0.20 s persistence; start / ARM limit 403.15 K; stand T0 limit 297.15 K (stand mode). Reference: TC calibrator (BOM 266).
| Item | Pass |
|---|---|
| Static offset and CJTO trim (R3-03) | step 1: case heated to 150 °C, steady, each channel against the BOM 266 reference; step 2: write the offset to the MAX31856 CJTO register (0.0625 °C LSB) per channel; step 3: re-measure at 100 / 130 / 150 °C: residual ≤ 0.3 K at each point. The calibrated tolerance uses it: tol_lo,cal = 5.85 + 0.630 r K, 10.28 K at 7.03 K/s, TC-01 maximum at the trip 161.82 °C [DERIVED, case_tc_channel_v1]. Without the trim (CJTO 0) the untrimmed formula applies: |offset| ≤ 0.6 K, tol_lo = 6.45 + 0.630 r K, 10.88 K at 7.03 K/s, TC-01 162.4 °C [DERIVED] |
| Time constant (pad step from a heater block) | tau ≤ 0.25 s (DESIGN target; a void or a thick bond line raises it) |
| EMI (R3-03) | servos, pintle rail and spark running against all off, ≥ 30 s each, 3 repeats: |mean(actuators on) − mean(off)| ≤ 0.5 K (the budget term is a ground-offset bias, so the pass is a mean shift), and the spike rejection: a burst of single-conversion spikes to 443 K for < 0.20 s gives no OVER_TEMP (0.20 s persistence) |
| Abort and limits | firmware: abort OVER_TEMP (6) at 423.15 K after 0.20 s; ARM refused above 403.15 K (OVER_TEMP), a COAST relight refused CASE_HOT (2); stand ARM refused above 297.15 K (CASE_WARM_STAND); 5 trials each with the decade box / TC simulator |
| T-F1 exposure basis (LEAD 249 (3)) | founder text: "T-F1 runs on the A 175 rows (TB, tb352g / h, both bounds) unless the lead re-bases it." Reason: the GVHI rev-4 B1 end-of-burn station rate 7.03 K/s [SIM] is above the 7.00 K/s limit of the A 165 rows. After a PASSED B-TC-1 calibration (offset and tau rows above) the low-reading tolerance becomes tol_lo = 5.85 + 0.630 r = 10.28 K at 7.03 K/s, TC-01 maximum at the trip 161.82 °C [DERIVED, results/tf1_rate_v1.json]; only then may the lead move T-F1 to the A 165 rows, and only before T-F1 is run |
| Stand T0 limit re-derivation (LEAD 249 (2)) | after B-TC-1: T0_max = 20 + (12.26 − e_hi,cal) / 0.96 °C, with e_hi,cal the calibrated high-reading error of the channel [DERIVED, dT_station / dT0 about 0.96]; until then the stand limit stays 24 °C (F-13, `kCaseStandArmMax_K` 297.15 K) |

### B-MV-1: main valve
| Item | Pass |
|---|---|
| Opener stroke and timing, 20 cycles | record; feeds S8/S10 timing |
| Holding-magnet release by the LTC4365 trip and by an ABORT frame | release ≤ 2 ms after the trip / frame (10 trials; SIM: same 1 ms tick) |
| OPEN/CLOSED switch codes through the J508 ladder | correct decode; harness open → `pmid_valid = false` and both switches false |
| Post-abort closure with the pintle on the ARM bus (REV-ELEC-3 N-01; with HIL-TR-1) | replay the S6R ramp60_50ms case on both builds: U330 drops +12V_ARM (SIL 5.211 s as built, 5.218 s ride-through); record the MV-P closed switch, the pintle encoder and drive current after the drop (the pintle is powered from +12V_ARM, sim.cpp l.289: no drive after it) and the head-pressure decay (bridge simulator in HIL; B-DPC-1 on the stand). Pass: MV closed ≤ 2 ms + its travel after the trip; the decay no slower than the SIL post-abort model (gop × ff, ASSUMED), otherwise the model is re-fitted and S6R re-run (SIL head peak 56.61 bar as built, 47.94 bar ride, both inside LC-TB70) |

### B-PNT-1: pintle (ENG-03; REV §9)
| Item | Pass |
|---|---|
| Closing rate under load | ≥ 2500 N/s equivalent (5 F_max/s, LEAD), worst of 10 |
| Opening rate | ≥ the rate map (`results/pintle_rate_map_v1.json`) at every map point |
| Closed-loop t10-90 under load (ENG-03 clause (c): the pintle POSITION loop including the drive, REQUIREMENTS l.88) | ≤ 100 ms, measured on the encoder with the rig load. This is a different loop from the S5 THRUST step (v2.11 flying up-step t10-90 p50/p95/max 0.105/0.126/0.142 s, SIM, scored against clause (a) 0.32 s: 230/230 flying runs pass); the two numbers are not compared |
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

Pre-flight check (proposal, NOT in firmware v2.10 or v2.11): the FC holds PURGE_EN low while the ECU commands V1 open for one BIT step; P_mid
must stay low. A P_mid rise means the window chain is stuck high → BLEED_FAULT. The ECU cannot read PURGE_WIN (no free pin).
FC ICD items: PURGE_EN raised ≤ 20 ms before Cmd::PURGE (`kFcPurgeEnLead_s`, ASSUMED) and dropped at E0; raised for the pad BIT;
drive level 3.3 or 5 V TO-VERIFY.

### CHK-BT (new): hardware both-commanded-open timer (LEAD 166 (3), 216 (5); schematic v2.6 U576-U579, NOT drawn)
BOTH = V1 drive AND V2 drive (U576, after the PURGE_WIN gating); U577 LTC6993-2 (rising edge, retriggerable, POL 1, RSET 63.4k 0.1 %,
DIVCODE 8 = NDIV 2^21: AS-RECALLED Table 1, TO-VERIFY before layout); U578 D-FF latches BOTH at the end of the pulse; U579 drops V1.
| Item | Pass |
|---|---|
| Timer width (BOTH held high on a fixture), 10 trials at 25 °C and at the board temperature extremes | 2.577-2.741 s (nominal 2.659 s; DATASHEET 3.0 % grade + 0.1 % RSET) and > the firmware cap + 1 tick (v2.12 FINAL: 2.39 + 0.001 = 2.391 s). Option, not applied: RSET 59.0 kΩ → 2.475 s nominal, 2.398 s minimum (closer to the 2.397 s rule-(d) bound) |
| Schedule not cut | a scheduled purge (both-open command span 2.38 s = 2.43 + 0.03 − 0.08): V1 never dropped by the timer, 10 purges |
| Firmware cap disabled (test build) | V1 drops at the timer; V2 still closes on its command; V1 stays off until a command drops |
| Re-trigger | two both-open episodes 0.5 s apart: the second is timed from its own start |
| Vented-mass residual (cap failed, timer only) | DERIVED 81.65 g at 29.25 g/s (86.70 g at 31.06 g/s; 92.48 g at 33.13 g/s, Cd 0.80): T_hw,max 2.7414 s + (t_close - t_open) 0.05 s = 2.7914 s of flow: B-BLEED-1 measures the flow; the residual goes to GNC / FMEA |

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
| Purge mass per scheduled purge (FINAL, LEAD 256 (2), 257 (2)) | 10 purges, weigh scale or Coriolis (BOM 244) | ≤ 76 g VENTED N2O (LEAD; the vehicle-level mass leaving through the bleed). Scheduled flow 2.43 s → 71.1 g at 29.25 g/s (289.5 K basis, LEAD 230 (3)), 75.5 g at the 31.06 g/s warm end (297.15 K) [DERIVED]. Need: 1.9 s at 289.5 K and 2.2 s at 283.15 K (Combustion purge_duration_v2p4.json 1ff6bfcd7d2f454c on 2 × 0.707 mm; LEAD 256 (2)(a)): margin 0.23 s at 283.15 K. Tank LIQUID depletion is larger (LEAD 181 (10)) |
| Purge mass at the firmware cap (both-open COMMAND cap 2.39 s, physical flow 2.44 s) | 5 purges with V1's close command inhibited (test build) | ≤ 76 g vented: 71.4 g on the 29.25 g/s basis, 75.8 g at the 31.06 g/s warm end [DERIVED] |
| Rule (d) re-set of the calibration constants (LEAD 256 (2), 257 (2), 258 (2)) | CF-4 / B-BLEED-1: ≥ 10 purges | measure the N2O Cd × A of the two-tap path and the valve times t_open / t_close; cap ≤ 76 g / mdot(297.15 K) − (t_close − t_open), mdot at the warm end from (d1) the UPPER 95 % BOUND of the measured Cd × A (not its mean); flow ≤ cap + t_close − t_open − 2 ticks; never above 2.43 s flow / 2.39 s cap (the defaults are the maxima); (d2) CF-4 shows the 283.15 K need at the re-set flow. Load with setPurgeCal (SAFE only); S12 re-run. At the defaults the bound is 2.397 s (76 / 31.06 − 0.05) |
| PURGE command time | B-FC-1 timing | the FC sends PURGE at E0 − 2.90 s (kPurgeRelight_s kept); flow start PURGE + 0.42 s, flow end E0 − 0.05 s; logged edge to edge on 10 purges, ± 1 tick |
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
| Unpurged RELIGHT (no PURGE) (v2.11 LEAD 203 (7)) | flight build with the bleed fitted: a RELIGHT or IGNITE in COAST with no purge running is REFUSED (TLM_RELIGHT d6 & 0x3F = UNPURGED 16; the ECU stays in COAST, no E0, no valve moves); in COAST with no other block TLM_RELIGHT reports relight_block UNPURGED with READY 0 (the FC reads it as 'PURGE first'); a PURGE is accepted and the RELIGHT received during PURGE is the only accepted flight relight (E0 at PURGE + 2.90 s). Stand build: the unpurged start is kept (CF-4 / T4 measure it; direct path when PRIMED, E0 on the command tick, prep path when UNPRIMED / UNKNOWN). A build without the bleed fitted keeps the v2.10 relight paths (LEAD to rule). Basis: Combustion v2.4a (purge_commit_rule_v2p4a, SIM/DERIVED) finds the unpurged branch refuted as written (light in the first slug, vapour gap after E2, A3 after the drogue release); LEAD 186 (1): no unpurged relight below L* (FC rule); LEAD 194 (3) withdrew the 'E2 + 0.22 s' held-release alternative (a GNC comparator only, not admissible with Pc invalid because of the 186 (2) hold). SIM: test_core 'v2.11 LEAD 203 (7) unpurged RELIGHT guard'; S12 relight_no_purge_flight_refused_UNPURGED_LEAD203_7 (flight, refused, stays COAST) and relight_no_purge_fitted_unpurged_LEAD175_stand (stand, E0 at once). This row checks the ECU command behaviour only; it is not evidence that an unpurged start is safe |
| FC drogue rule R2 v2 (LEAD 181 (4), 227 (5) / (6)): with Pc invalid, release iff ECU RUN AND the mode-3 statistic ≥ 37.159 N on 3 consecutive 100 Hz frames inside E2 + W, else hold the drogue and ABORT the ECU at E2 + W. W = 0.8 s ADOPTED for the W10 < 6 m/s envelope (227 (5); Electronics S17 v2.11 confirms it with conditions, see the v2.11 report); the mode-3 filter is RE-INITIALISED at the Pc-invalid onset (227 (6)); W, the threshold and the reference are FC parameters | GNC's test; Electronics supplies the frames and the ABORT path above. ECU side SIM: v210-16 (Pc lost at E2 + 5/10 ms, ABORT frame at t_E2 + 0.5 s and + 0.8 s: ECU in RUN until the frame, ABORT/CMD on that tick, pintle command 0 at +4 ms). Bench: frame at t_E2 + 0.8 s (the adopted W) and at t_E2 + 0.5 s (comparator) from the FC with the simulator open; the R2 hold (row below) runs until the frame |
| Cmd::DROGUE echo (LEAD 186 (2)) | CMD_STATE cmd 17 DROGUE arg 1 → TLM_RELIGHT d6 b6 = 1 on the next frame, arg 0 → 0; other args ignored; b6 = 0 after power-up and after an accepted ARM; accepted in every state. SIM: test_core v210-17 (incl. the CMD_STATE round trip) |
| LOST DROGUE 0 (LEAD 216 (2)(c), R2-02): flight build, RUN at 200 N, DROGUE 1, simulator opened at E2 + 0.15 s; the FC's DROGUE 0 suppressed on the bus | (a) FC side: after its DROGUE 0 the FC re-sends DROGUE 0 with a NEW sequence number on every TLM_RELIGHT frame (50 Hz) that still shows d6 b6 = 1, from the second such frame, at most 10 times (0.2 s); then it logs DROGUE_ECHO. (b) ECU backstop: the hold ends at E2 + 0.85 s (0.8 s window + 2 × 20 ms FC frames + 10 ms link latency, `kR2HoldBackstop_s`) whatever the drogue report: one EVENT R2_BACKSTOP 0x24 (arg = hold ticks), log tlm_flags b2, no hold after it, command back to 200 N at ≤ 2.5 N/ms, RUN kept. With the FC's DROGUE 0 delivered at E2 + 0.40 s the hold ends then and no backstop event follows. SIM: test_core v211b-2 (and the per-burn backstop check) |
| R2 command hold, LIFT-COMMANDED (LEAD 186 (2), OI-38; v2.11 LEAD 216 (9), 230 (4)): flight build, RUN, DROGUE 1, simulator opened to invalidate Pc | pintle commanded to the start-level lift 0.21776 mm (`kR2HoldLift_m`, Combustion v2.4b ECU hold-lift row; encoder within its resolution) on every tick while Pc is invalid (the FC command is capped at 62.5 N while the hold is on) (Pc setpoint slew 250 bar/s still applies); log tlm_flags b0 (hold) and b1 (drogue) set; DROGUE 0 → hold off on that tick, command back at ≤ 2500 N/s; Pc valid again → hold off; no hold without DROGUE 1, with Pc valid, or on the stand build (stand: PC_SENSOR abort instead). SIM: test_core v210-17 (setpoint at the hold level after 26 ms against a 28 ms slew bound, the start ramp would take 55 ms; back to 200 N in 55 ms at ≤ 2.50 N/ms), SIL S17 v2.11 (hold lift steady 0.2084-0.2092 mm in the SIL plant against the 0.21776 mm command: servo / linkage model; lit hold thrust 48.96 N normal / 41.61 N starved, dead cold flow 12.31-12.36 N; SIM). Hardware: encoder lift and the pintle command in the hold on the DAQ; the hold-level thrust at the A1 state is a TO-VERIFY item for CF-3. R2-23 (S17 v2.11): one HIGH over-range tick after E2 engages the hold for exactly 1 tick (SIM) |

### B-SAFE-1 (new): stand safing after a no-light (LEAD 172 (1))
Procedure (stand, any start; pad first start): N2 purge ≥ 60 s at ≥ 10 g/s (≥ 0.6 kg; BOM 246 with flow indication), then hold
≥ 15 min before anyone approaches, with Pc at ambient (|Pc| ≤ 0.10 bar g) and the head TCs falling, then safing.
| Check | Pass |
|---|---|
| ECU lockout | CLEAR_LOCKOUT refused (refuse reason SAFING_HOLD 15) until 960 s after the abort; accepted after (SIM S10) |
| Boot during the hold | the hold restarts (NV b4) |
| N2 flow | measured ≥ 10 g/s for ≥ 60 s; the ECU cannot see the N2 flow, its timer is a lower bound only |

### HIL-OT-1 / HIL-TR-1 / HIL-RST-1 (RE-28; LEAD 166 (8))
HIL-OT-1 (over-thrust, with B-ECU-1, B-FC-1, B-MV-1; RG-19 budget in results/over_thrust_v3.json, written out here from v1): flight FC
and flight ECU (Teensy 4.1 build) on the bench harness, flight CAN at 1 Mbit/s with the flight stub lengths and terminations; CAN analyser
with hardware timestamps (≤ 1 µs); logic analyser / scope on IMU DR, FC read GPIO, FC decision GPIO, ECU MVL_G, latch coil current and the
MV-P position switch; MV-P on its bench rig (B-MV-1). Stimulus: (a) SPI replay of the GNC sim6 F_acc traces into the FC estimator input
(FC test hook): steps 500 → 876 N, ramps 2500 / 3600 N/s from 150 and 500 N, the healthy 571.5 N maxima for the no-trip check; (b) the
flight IMU on a step fixture (E0 / E1, B-FC-1); (c) FC_THRUST frames injected by the analyser directly to the ECU (E5 / E6 alone). Rule
under test (firmware, unchanged since v2.8.1): OVER_THRUST on the 3rd consecutive fresh FC_THRUST frame with the valid flag and > 650 N
(frames ≤ 50 ms apart) in RUN, flight mode. Measure every budget term edge to edge, 1000 repetitions per stimulus (mean, p99, max).
Pass: each term ≤ its budget max or allocation; end-to-end p99 ≤ the sum (known terms 78.6 ms mean / 84.1 ms max, DERIVED, plus the
allocated IMU / FC terms); no trip on the healthy replay; a term over budget goes back to its owner with the measured value. Not covered:
airframe axial modes and combustion oscillation (T1-T4 hot fires).

HIL-TR-1 (Pc transient replay, with B-PC-1 / B-DPC-1; DESIGN, Electronics): a DAC (≥ 100 kS/s, ≥ 16 bit) drives the C1 conditioning
input through a bridge simulator in place of the transducer, playing recorded pressure-time histories: the FA-1 chain cases
(results/fa1_chain_v2p11_cases.csv: v210_line, v210_noline and the C1 as-built chains, incl. the face-peak construct), the S6R
in-window over-pressure set and the S6 start and over-pressure profiles. Flight ECU on the flight build (default, C330 220 nF) and on the
ride-through CANDIDATE build (C330 540 nF), FC in the loop reading TLM_FAST / TLM_RELIGHT. Measure: abort cause and abort tick, the MVL_G
edge, the U330 comparator output and its delay against the injected edge, PC_VALID (d6 b7), the over-range flags and the log v12
ovr_flags. Pass: abort cause equal to the SIL record case by case on both builds; abort tick within one tick (1 ms) of the SIL; the
comparator delay inside the band of the fitted C330 (220 nF: tau 5.225 ms; 540 nF: 12.10-13.55 ms); for the S6R cases the abort taken
with the replayed head pressure-time inside the LC-TB70 envelope. A case outside goes back to the SIL chain model with the measured trace.

HIL-RST-1: an ECU reset injected in ARMED, IGNITION, RUN, COAST and
PURGE (5 each). Pass: the ECU boots to SAFE, MV and both bleed valves closed, RUN never reported after the reset, the drogue not
released by the FC, NV lockout as specified. No in-flight recovery path exists (LEAD).

### LEAK-1, CF-3, CF-4 (Mechanical / Combustion rigs; Electronics instrumentation)
LEAK-1: feed leak at MEOP. CF-3: lift against T_tank (17 firmware rows, 0.1928-0.2520 mm; A1 row 286.7 K 0.2178 mm), Coriolis
reference (BOM 244); warm rows at 37.4 g/s are 0.8 % over the 37.1 g/s limit and must be re-checked. CF-3 start-lift point (LEAD 194 (4)):
mdot (Coriolis) and load-cell F at the start-level lift with the encoder lift recorded; acceptance F ≤ 16.31 N minus the heat allowance,
or mdot ≤ 52.6-56.3 g/s; a failure returns the hold level and the W10 rule to the LEAD. v2.11: the hold is lift-commanded at Combustion v2.4b's start-level lift
0.21776 mm (LEAD 216 (9), 230 (4)), the same value as the ECU ignition-lift row at the A1 state (0.2178 mm); measure at that lift with
the encoder recorded. Combustion's lit-side F_min 33.14 N at that lift (3 of 72 corners never reach 37.16 N, LEAD 230 (5)) is an open
item for GNC / Combustion; CF-3 gives the cold-flow side. Heat:
injector-body and feed soak-back temperature at the relight (heat at tank pressure, threshold 2.8-3.7 kW; TO-VERIFY, Combustion). CF-4: segment void after the
coast, P_mid and the bleed valve states on the DAQ, T4 crown / FD-01 tap temperatures if fitted.

### IGN-1 / T1: relative light rule on hardware (REV §9)
Record at 1 kHz: raw and filtered Pc, P0, rise, det flags, tlm flags, photodiode volts; B-DPC-1 (head flush and line end) at 51.2 kS/s.
| Item | Pass |
|---|---|
| E2 − light | ≤ 20 ms on every lit start (DESIGN: SIL 12-13 ms in S5, 16-17 ms at the A1 relight in S17, + margin; GNC models thrust onset AT E2, so a longer latency is lit time GNC does not model - GNC to confirm 20 ms) AND command → E2 ≤ 0.81 s (the flight Pc-confirm deadline = GNC planning value) |
| Unlit maximum rise | ≤ 0.6 bar (rule 0.8 bar) |
| A3 ratio minimum | ≥ 0.45 |
| P0 shift during the spark / raw spikes | ≤ 0.1 bar / < 2 bar g |
| BASE_AMB | no event |
| b4 / b7 timing | as specified in B-FC-1 |
| LIGHT_SPIKE | logged (raw and filtered peak, time above 8 and 30 bar abs, time from light); compared with B-DPC-1 |
| Photodiode | lit rise and dark level measured; sets `kPhotoLitRise_V` (0.20 V placeholder); the head must VIEW THE MAIN CHAMBER: FLAMEOUT_OPT proven with the torch closed on every lit start (S17 v2.11: with a torch-only view the R2 window releases dead vehicles at late Pc-loss onsets, SIM) |
| Late lights on the stand (R2-19) | S15 v2.10/v2.11: 4 stand starts with a late light end NO_IGNITION (flight 0): record E1 → light for every stand start; a stand light later than the stand window W 0.35 s is a NO_IGNITION by design (safing per B-SAFE-1), not a fault |

### T1-T4 F_acc (written out; no v1 text is needed)
Combustion's T1-T4-REGRESSION-SPEC v3 (b0c42b09ba47cb9c) governs the firing matrix; Electronics supplies the channels. FC_THRUST is
NOT armed on A1 (LEAD 168 (5), 181 (3)): this test is evidence for RG-16 / B1 only.
| Item | Value or pass |
|---|---|
| Channels | stand load cell (BOM 236, ADC1 CH3) at 1 kHz; the FC with its IMU on the stand structure, F_acc = m_est f_z + D_model at 100 Hz frames (GNC definition); Pc (C1) and B-DPC-1; common time base ≤ 1 ms (sync GPIO, BOM 239 / 240) |
| Statistic | relative error F_acc / F_loadcell - 1 for frames with F > 0.15 F_max after the first 0.1 s of each window; step delay (50 % and 90 %) on the thrust steps; per-firing bias and 3-sigma |
| Pass | inside GNC's published 3-sigma band (gnc.json fc_thrust error_3sigma); a result outside it goes to GNC (the v3.1 staging already notes DC-C / DC-D at ≥ 450 N outside the band) |
| Also logged | IMU vibration spectrum at each thrust level (GNC asks for it; the RG-16 white-vibration model is ASSUMED) |

Planning rule (REV-ELEC-3 N-07; LEAD 261; gnc.json v3.2 duty_cycles.note_n07_rev_gnc_7; T1-T4 v3.2 l.294): no planned burn may reach the case abort A = 150 °C at the B1 end-of-burn heating rate 7.03 K/s (GVHI rev-4 station rate [SIM]); from a soaked start (F-13, ≤ 24 °C) the DC-D first burn would cross at about 23.5 s (merged bound [DERIVED]). A burn starting with the case TCs at T_s is planned for t ≤ (150 − 5 − T_s) / 7.03 s (5 K margin); a relight is held until TC1 / TC2 ≤ T_s (the firmware refuses above 130 °C, CASE_HOT, a backstop).

| Firing (re-sized) | Content and objective | Planned burns | Case condition | N2O |
|---|---|---|---|---|
| D1 (GNC DC-D segments 1-2) | staircase 500 → 62.5 N (throttle 1.0 → 0.125), then steps 100 ↔ 500 N: throttle map and Pc loop | one burn 15.6 s (0.90-16.52 s of DC-D v2) | soaked start; ends ≥ 7.9 s before the 23.5 s crossing | 2.06 kg [DERIVED from GNC] |
| D2 (DC-D segment 3) | sweep 175-399 N | one burn 8.0 s | soaked start | 1.16 kg |
| D3 (DC-D 500 N hold; GNC F_acc at ≥ 450 N and IMU vibration at F_max) | 500 N hold, twice for ≥ 10.13 s at ≥ 450 N in total | two firings of 6.0 s | soaked start each | 2 × 1.44 kg |
| D4 (DC-D burns 2 and 3: triangle to 428 N, hold at 130 N) | relight content (not the A1 relight) | after a cold first burn ≤ 10 s; burn 2 7.75 s needs T_s ≤ 90 °C, burn 3 9.76 s needs T_s ≤ 76 °C [DERIVED] | relight held until the case is there | 0.94 + 0.60 kg |
| T4 (Combustion, re-sized to the shortest firing, LEAD 261) | burn 1 on the B1 p99 profile (21.76 s at 0.257, 1.54 kg; erosion and soak at the B1 sizing duty), coast, one relight 4.59 s at 0.47 (relight latency from a soaked state; the A1 p99 record 3.78 s at 0.88, coast to 22.79 s) | burn 1 21.76 s (1.7 s before the 23.5 s crossing; the 23.58 s max-profile burn is NOT planned: it reaches A); relight 4.59 s | the relight needs T_s ≤ 112.7 °C (150 − 5 − 32.3): at the B1 p99 end the case is about 137.8 °C, so the coast is "about 19 s or until TC1 / TC2 ≤ 112.7 °C", whichever is later; if the case is not there by the end of the planned coast the relight is shortened to (145 − T_s) / 7.03 s or not run | about 2.0 kg [ESTIMATE, LEAD 261] |
| DC-C | no Combustion T4 objective (T1-T4 v3.2 l.294); GNC F_acc rows at ≥ 450 N are flown in D3 | not planned | | 0 |

OPEN (Combustion / Mechanical, N-07): whether a coast longer than about 19 s (case to 112.7 °C) still meets the "relight from a soaked state" objective, and the case soak-back after B1 (the cooling the coast row relies on is not in any published history); the T4 rows of T1-T4 v3.2 l.61, 143-145 and 171 stay the DC-D computation [SIM] until Combustion re-runs them on the re-sized profile.

### GSE: launch commit wind (LEAD 181 (6): HARD rule for A1; was provisional in LEAD 161 (6))
Anemometer at 3 m (BOM 250): W10 < 6 m/s AND sigma_u(3 m) ≤ 1.0 m/s over the 10 min before ARM. Ground procedure: the ECU has no wind input.

### A1 pad go/no-go list (LEAD 181 (6); LEAD 175 (4); combustion.json v2.4 arm preconditions)
Every item is GO before the A1 launch commit. One NO-GO stops the count; the cause and the telemetry are logged. Nothing here is validated
on hardware yet: the ECU items are SIL evidence (v2.11) until B-ECU-1, B-BLEED-1, B-TC-1 and B-FC-1 pass.

| Item | GO when | Source / owner |
|---|---|---|
| Wind | W10 < 6 m/s AND sigma_u(3 m) ≤ 1.0 m/s over the 10 min before ARM (anemometer at 3 m) | LEAD 181 (6) HARD rule; ground crew |
| Pc VALID | TLM_RELIGHT d6 b7 = 1 (Pc channel valid AND no latched PC_SENSOR fault or abort) | LEAD 175 (4); ECU since v2.10 (v2.11: per tick, the flight high over-range is non-sticky), FC launch commit |
| Bleed closure | Before IGNITE: V1 and V2 commanded closed with the drivers inhibited, P_mid low, no EVENT HBLEED leak/fault and no MV fault bit in TLM_FAST d6-d7. In the sequence (automatic): the pad BIT S0-S4 runs in PREPRESS (first start, feed primed) and aborts BLEED_FAULT before IGNITION if a step fails, so no main N2O is admitted; the BIT result is not available at the launch commit | combustion.json v2.4 igniter.sequence.arm_preconditions; ECU v2.10 pad BIT (engine_ecu.cpp) |
| ECU armed | TLM_FAST state = ARMED. A refused ARM leaves the ECU in SAFE with the inhibit cause latched as the abort cause (e.g. TANK_HOT incl. the guard band, TANK_COLD, BAY_HOT, TVC_SUPPLY, MODE_MISMATCH, MAINT_JAM, RELIGHT_LOCKOUT, PC_SENSOR, OVER_TEMP for a case TC above 403.15 K; on the stand also CASE_WARM_STAND above 297.15 K); DISARM clears it (engine_ecu.cpp armChecksOk; v2.11 adds OVER_TEMP at ARM and CASE_WARM_STAND). On the pad TLM_RELIGHT d6 & 0x3F reads NOT_COAST (10) by design: it is not an ARM refusal | ECU interlocks (since v2.10; v2.11 rows OVER_TEMP at ARM, CASE_WARM_STAND, TANK_COLD margin) |
| Drogue echo | TLM_RELIGHT d6 b6 = 0 after ARM (the accepted ARM resets the drogue state; the FC reports the deployment in flight with Cmd::DROGUE 1) | LEAD 186 (2); ECU since v2.10 (test v210-17) |
| Purge window | CHK-PW passed on this board; PURGE_EN low at the pad (a stuck-high window chain is latent to the ECU) | LEAD 166 (3); Electronics (pre-flight firmware step proposed, not implemented) |
| Both-open timer | CHK-BT passed on this board | LEAD 166 (3) / 216 (5); Electronics |
| Tank cold rule | tmin = min(wall DS18B20, Tsat(P_tank)) ≥ 288.15 K + 0.42 K at ARM (the ECU refuses TANK_COLD below it; an IGNITE refused in PREPRESS exits to ARMED with the MV closed on that tick) | LEAD 216 (7); ECU v2.11 |
| Seat compensation (v2.12 option (b), LEAD working basis) | after ARM: log v13 f3 SEAT_COMP set and SEAT_NOREF clear (per-serial coefficient and T_cal loaded, seat TC valid over the ARM window); with the fallback build (coefficient 0) the A1 relight runs on the v2.11 limits and the flight ARM ambient must satisfy |T0 − T_cal| × k × 0.0248 bar/K < 0.5 bar (ARM sanity) | Electronics (B-PC-1 record); LEAD to confirm (b) |
| Photodiode view | the FA-1 head views the main chamber (IGN-1 row) | S17 v2.11; Electronics + Combustion |


## 3. Outputs back to the design

| Result | Changes |
|---|---|
| B-PT-1 | `ptank_cal_ok` NV record; P_tank threshold 50.34 → 54.30 bar abs |
| B-PC-1 residual, drift | `kBpc1Shown` (only after RE-02 closes); second re-zero limits |
| B-BLEED-1 valve times | `kHbleedOpenTime_s`, `kHbleedCloseTime_s`, cap, schedule; S12 re-run |
| B-BLEED-1 mass | purge cap in the measured-time form (LEAD 216 (5)); N2O budget line |
| CHK-PW | one-shot RSET if the width is outside the band; pre-flight check firmware step |
| B-PWR-2 | power sequencing or converter capacity (RE-09) |
| B-PNT-1 | S5 dispersion bands (speed_scale, J_int, latency) |
| B-TVC-1 | notch frequencies, jam threshold (RE-24) |
| IGN-1 | `kIgnRise_Pa`, `kIgnConfirmRelN`, photodiode thresholds, A3 margin |
| CF-3 | `kIgnLiftTab_m` rows; start-lift point per LEAD 194 (4): mdot and load-cell F at the commanded hold lift (encoder recorded), acceptance F ≤ 16.31 N minus the heat allowance or mdot ≤ 52.6-56.3 g/s; for GNC's R2 v2 and the S17 bound (OI-38) |
| F-12 (070BG over-range) | 070BG saturation level and recovery (MISSING in the datasheet) for the stand reference and P_torch (not the flight Pc after LEAD 205) |
| B-PC-1 (C1) | trims per serial, comparator band, drift; `kPcXdcrC1*`; open-wire behaviour |
| B-PC-1 zero TC per serial | seat coefficient and T_cal (setPcSeatCoef / setPcSeatTcal); kPcRezeroMax_Pa / kIgnBaseCheck_Pa kept or re-derived with the measured residual; F-10 answer (thermal-zero maximum k) |
| B-DPC-1 Q_JFWD | the stand J-FWD replace rule in use (F-14) after the noise record; a noise-floor rule if the noise trips it |
| Rule (d) (CF-4 / B-BLEED-1) | setPurgeCal(flow, cap) per rule (d) with (d1) / (d2); S12 re-run |
| B-DPC-1 | head dynamic Pc at the C1 seat: the FA-1 pressure-time history against the LC-TB70 envelope and Combustion's spectrum |
| B-TC-1 | case-TC offset and tau against the Part A budget; T-F1 exposure statement |
| CHK-BT | timer width; hardware residual mass for GNC / FMEA |
| F-11 | launch-site W10 / sigma_u statistics; the hard wind rule in practice |
| B-FC-1 DROGUE / R2 hold | OI-38 / OI-43 hardware evidence; `kR2HoldLift_m` kept or re-set against the hold-level thrust measured at CF-3; `kR2HoldBackstop_s` and the FC re-send bound against the measured link timing |
| HIL-RST-1, HAL-1 | RE-06, RE-28 closure |
