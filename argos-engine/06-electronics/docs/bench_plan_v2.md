# ARGOS engine electronics: bench and test plan v2

06-electronics, 2026-10-13. Firmware v2.9 (SIL only), ECU schematic v2.4, BOM v2.1. Electronics prepared this plan. The founders run the physical tests.

Each test closes a number the firmware uses now, and the plan names that number. A SIL result is not hardware evidence, and neither is a matching hash or a passing ERC. Where a value is TO-VERIFY, the test measures it. The plan does not assume it.

Rules for every test:
- Record the raw data at the rate given.
- Record the firmware build: the SIL manifest tree hash and the `config.h` first line.
- Record the bench instrument calibration dates.
- Keep failed runs as evidence. A re-run gets a new run number and does not overwrite the old one.

## 1. Order and gates

| Step | Test | Gate it closes | Needs |
|---|---|---|---|
| 1 | B-PWR-1, B-PWR-2 | rails, e-fuse, ARM interlock | bare ECU, bench supply |
| 2 | B-ECU-1 | I/O, CAN, watchdog, log v10 | step 1 |
| 3 | B-PC-1 | post-zero residual: sets `kBpc1Shown` (floor 1.8 -> 2.0 bar abs, baseline check 0.7 -> 0.4 bar) | step 2, N2 0-70 bar g, reference gauge |
| 4 | B-MV-1, B-PNT-1, B-TVC-1 | actuator timing, ENG-03, MV switch ladder | step 2 |
| 5 | B-BLEED-1 (new) | head-end bleed: pad BIT, P_mid comparator, V1 closure confirmation time | steps 2-4, valves + tee |
| 6 | B-IGN-1, B-FC-1 (+ drogue telemetry) | spark EMI on Pc, FC link, TLM_FAST d1 bits | step 2, FC |
| 7 | HIL-OT-1, HIL-TR-1 | over-thrust and transient replay | steps 2, 6 |
| 8 | LEAK-1, CF-3, CF-4 | feed leak, ignition-lift table, segment void | Mechanical / Combustion rigs |
| 9 | IGN-1, T1-T4 | relative light rule on hardware, start latency, F_acc | hot-fire stand |

## 2. Tests

### B-PWR-1 / B-PWR-2: power and arming
**Measure:**
- All rails at no load and at full load.
- ARM bus on/off timing.
- The firmware e-fuse trip of the TVC chain.

**+12V_ARM (new in v2):** the rail carries the two bleed valve coils. The 6027 HP coil voltage and power are TO-VERIFY. The measurement settles open issue OI-BLEED-COIL.
- Measure the +12V_ARM droop with both bleed coils held for 3 s (purge 2.5 s plus margin), with the MV latch and both torch valves on.
- Pass: the rail stays inside the coil's rated band and the U3V70F12 does not current-limit.

### B-ECU-1: I/O, CAN and log
**Checks:**
- Every pin of `hardware/kicad/pin_map_v2p4.csv`.
- CAN frames against `protocol.h`.
- Watchdog /OE cut of U304 **and** U307.
- 1 kHz log record v10 (150 bytes, CRC-16).

**Pass:** decoder round trip with no CRC error over 10 min.

**Pin 23 ladder:** inject the 10 ladder codes with a resistor box and check that `mvLadderDecode` returns each one. The codes and windows are in `results/hbleed_provision_v1.json`, minimum window gap 0.019 of full scale.
- Record the ADC ratio of every code.
- Pass: every reading lies inside its computed window.

### B-PC-1: Pc chain residual
**Setup and record:**
- N2 0-70 bar g with a reference gauge.
- Use the flight ECU and the flight +5V_SNS.
- Fit `gain_corr` / `offset_Pa`, then the ARMED auto-zero.
- Record the post-zero residual over the temperature range of the pad.

**Gate:** the residual is 0.3 bar or less. If it is, the LEAD constant `kBpc1Shown = true`:
- floor 2.0 bar abs;
- baseline check 0.4 bar;
- re-zero limit unchanged at 0.30 bar.

This is the only planned closure of the S9 +1.034 bar false-light case. There, an unlit chamber reads 1.87 bar abs filtered, which is above the 1.8 floor and below the 2.0 floor.

### B-MV-1: main valve
**Measure:**
- Opener stroke and timing.
- Holding-magnet release by the LTC4365 trip.
- OPEN/CLOSED switch codes through the J508 backshell ladder (R0 82.5k, R1 9.53k, R2 17.8k).

**Pass:**
- The switch codes decode correctly.
- With the harness open, `pmid_valid = false` and both switches read false.

### B-PNT-1: pintle (ENG-03)
**Measure:**
- Rate under load against ENG-03: at least 5 F_max/s (2500 N/s) (LEAD 2026-10-13). A lower value needs an explicit lead decision on the published loss.
- Back-drive with the spring.
- Seat detection (encoder lift at the seat).
- Stall monitor no-progress time. SIL clearance is 46 ms against the 100 ms time path. Record the hardware value.

**Items from the ENG-03 closure:**
- servo deadband and backlash;
- `J_int`;
- latency;
- torque and speed scale at the PRAIL voltage.

These feed the S5 dispersion bands.

### B-TVC-1: gimbal FRF
With `TVC_TEST_ENABLE 2` (filters bypassed in SAFE), record the FRF of both axes and the jam detection threshold on the as-built linkage.

S6 `gimbal_jam_moving_cmd` is an open FIX item: the per-axis mismatch at a 2 deg command is below the 1.5 deg threshold.

### B-BLEED-1 (new): head-end bleed provision
**Hardware:**
- Two NC valves of the 6027 HP class in series.
- A tee with the 170BG between them.
- The restriction downstream of V2.
- The mid volume of the tee (MID) at 0.5 cm3 or less (ICD).
- N2 first, then N2O at feed pressure.

**Measure:**
1. The pad BIT S0-S4 with each valve forced failed-open and failed-closed (mechanically pinned, or with the coil unplugged). Each injected fault must end in BLEED_FAULT at the step listed in config.h.
2. Comparator thresholds while ramping P_mid. Design values: rise 9.86 bar g, fall 8.86 bar g, 170BG TEB 2.55 bar.
3. **V1 closure confirmation time.** This is E0 to V1 confirmed: V1 closes, MID vents through V2, and P_mid reads low for 5 ticks.
   - Prediction: 76-106 ms. That is valve close 50-80 ms (DATASHEET at 6 bar), plus liquid expulsion 12.5 ms, plus vapour blowdown 8.9 ms, plus 5 ms.
   - Limit: `kHbleedCloseConfirm_s` = 0.15 s.
   - Pass: worst of 20 cycles at N2O feed pressure is 0.12 s or less, leaving 30 ms margin.
4. Purge flow at 1.0 mm. SIL predicts liquid 31 g/s and about 79 g per 2.5 s purge. The flow sets the N2O budget line.
5. Leak-monitor timing with V1 forced open and V2 closed. SIL flags at +0.21 s.

**Record:**
- P_mid analog at 1 kHz on a bench DAQ, not only the comparator output.
- Coil current and the 12 V rail.
- N2O temperature at the valve.

### B-IGN-1: igniter EMI
Spark train with the chamber vented. Record raw Pc at 1 kHz. The light rule needs no rise of 0.8 bar on filtered AND raw during the spark.

SIL: under a 20 bar, 2 ms, 50 Hz spike train the torch gate interlock aborts TORCH_FAULT, which is fail-safe.

### B-FC-1: FC link and drogue-release telemetry
CAN at 500 Hz with the FC. Decode TLM_FAST d1 as `state = d1 & 0x0F` and the tlmf bits b4-b7.

**Inject a Pc profile** through the transducer simulator. In order:
- pre-lift 0 bar g;
- light rise to 2.5 bar g;
- after E2, a 3 ms dip below P0 + 0.8 bar.

**Pass:**
- b5 is set before E2.
- At E2 the bits are b4 + b5 + b6.
- b7 is set at E2 + 100 ms (plus or minus 1 ms) without the dip.
- With the dip, b6 clears and b7 never sets.
- The EVENT STATE (RUN) t_ms equals the E2 tick.

This reproduces unit tests (25)-(26) on hardware. The FC rule itself is GNC's test.

### HIL-OT-1 / HIL-TR-1
Over-thrust and transient replay with the FC in the loop, as in bench plan v1. Unchanged by v2.9 apart from TLM_FAST d1, which decoders must mask.

### LEAK-1, CF-3, CF-4 (Mechanical / Combustion rigs; Electronics instrumentation)
**LEAK-1:** feed leak at MEOP.

**CF-3:** cold-flow ignition-lift table.
- Lift against T_tank. Firmware rows: 17 rows from 0.1928 to 0.2520 mm; the A1 row at 286.7 K is 0.2178 mm.
- Warm rows reach 37.4 g/s. That is 0.8 % over the 37.1 g/s limit and must be re-checked.
- Instrumentation: P_feed, P_tank, T_tank (DS18B20 x2), the encoder lift, and a mass flow reference (Coriolis, TO-QUOTE).

**CF-4:** segment void after the coast, for the bleed fitted/not-fitted decision.
- Add P_mid and the bleed valve states to the DAQ.
- Record the T4 crown and FD-01 tap temperatures if Mechanical fits TCs.

### IGN-1 / T1: relative light rule on hardware
**Record at 1 kHz:**
- raw Pc and filtered Pc;
- P0 (the log v10 `ign_ref_hPa`);
- the rise (`ign_rise_hPa`);
- the `det` flags;
- `tlm_flags`;
- the plant light time from a photodiode or the torch TC.

**Evidence wanted:**
- Lit starts: rise above P0 against time. SIL: E2 - light is 16-18 ms against the ~15 ms target (open issue OI-E2-LATENCY).
- Unlit starts (main never lights): the maximum rise. SIL: 0.50 bar against the 0.8 bar rule, with unlit Pc at most 1.51 bar abs.
- A3 ratio minimum during the start ramp. SIL: 0.454 against the 0.40 threshold (OI-A3-MARGIN).
- The A5 behaviour on a late light (OI-A5-LATE). In SIL, a 0.20 / 0.25 s delayed light now aborts HARD_START.
- Drogue support terms. In the SIL A1 MC, the rise held to E2 + 0.10 s in every lit run and Pc reached 3.0 bar abs at most 43 ms after E2. The SIL plant does not reproduce the GNC fuel-starved plateau.

### T1-T4 F_acc
Thrust from the stand load cell against the accelerometer estimate (FC_THRUST), as in v1.

## 3. Outputs back to the design

| Result | Changes |
|---|---|
| B-PC-1 residual | `kBpc1Shown`, so floor and baseline check (LEAD rule) |
| B-BLEED-1 confirmation time | `kHbleedCloseConfirm_s` margin, SIL `hb_t_close` / `hb_tau_vent` |
| B-BLEED-1 thresholds | comparator divider R576/R577, hysteresis R573/R574 |
| B-PWR-2 +12V_ARM droop | coil choice (12 V coil / 24 V boost), BOM v2.1 valve row |
| IGN-1 rise / latency | Combustion / LEAD: `kIgnRise_Pa`, `kIgnConfirmRelN`, A5 window |
| CF-3 | `kIgnLiftTab_m` rows |
