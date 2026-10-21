#!/usr/bin/env python3
# Electronics v2.12 (2026-10-21): bench plan v5 from bench plan v4 (docs/bench_plan_v4.md 5b1c9336d7b8db50) by named row edits.
# REV-ELEC-3 R3-02 (F-14 LC-TB70 v2 rules verbatim, TB-state set, Q_JFWD), R3-03 (B-TC-1 CJTO trim, EMI mean shift), R3-05 (C1 band,
# B-PC-1 zero-TC row per serial), R3-06 (F-13 soak), N-01 (B-MV-1 / HIL post-abort closure), N-07 (T1-T4 re-size), R3-01 option (b)
# rows; LEAD 253 (7)(i)-(ii), 256 (2), 257 (2), 258 (2)-(4); REV-COMB-4 R4-09 / R4-12 / R4-13. Texts quoted from the hub
# interfaces/mechanical.json v2.4 (66bc53d88d444679) lc_tb70_envelope_v352 are read from the file (verbatim) and asserted.
# Run: python3 -B -I make_bench_plan_v5.py <out.md>
import hashlib, json, sys
E = '/home/claude/work/electronics'
H = '/home/claude/work/shared-fallback/engine'
V4 = E + '/docs/bench_plan_v4.md'
MECH = H + '/interfaces/mechanical.json'
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert h16(V4) == '5b1c9336d7b8db50', h16(V4)
assert h16(MECH) == '66bc53d88d444679', h16(MECH)
env = json.load(open(MECH))['lc_tb70_envelope_v352']
RULE = env['jfwd_replace_rule_v2']['rule']
QTY = env['jfwd_replace_rule_v2']['quantity']
R_ENV = env['rules'][1]
R_ONE = env['rules'][2]
F4 = env['F4_abort_set']['verdict']
Z3P = env['Z3_v2']['REV-COMB-4_Z3_prime_verbatim']
assert RULE.startswith('J-FWD REPLACE RULE (LC-TB70 v2)') and 'no minimum duration' not in RULE
assert R_ENV.startswith('an event that leaves the envelope') and R_ONE.startswith('one Z3 event per J-FWD assembly')
lines = open(V4, encoding='utf-8').read().split('\n')

def at(prefix):
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, (prefix, idx)
    return idx[0]

def rep(prefix, new):
    lines[at(prefix)] = new

def after(prefix, new_lines):
    i = at(prefix)
    lines[i + 1:i + 1] = new_lines

# ---------------------------------------------------------------- header
i_end = at('What changed from v2 (REV-ELEC-1 RE-13)')
lines[0:i_end] = [
    '# ARGOS engine electronics: bench and test plan v5',
    '',
    '06-electronics, 2026-10-21. Firmware v2.12 (SIL only), ECU schematic v2.5 (the v2.11 board changes are DESIGN rows in BOM v2.3;',
    'schematic v2.6 is NOT drawn), BOM v2.3 (`results/bom_v2p3.csv`) with the v2.12 text changes of rows 205 and 251 in',
    '`results/bom_v2p4.csv` (no new line numbers). Supersedes bench plan v4 (docs/bench_plan_v4.md 5b1c9336d7b8db50, kept).',
    'Electronics prepared this plan. The founders run the physical tests.',
    '',
    'What changed from v4 (REV-ELEC-3 R3-01 option (b) as the working basis (LEAD 2026-10-21T11:25Z), R3-02, R3-03, R3-05, R3-06, N-01,',
    'N-07; LEAD CHANGELOG 253 (7)(i)-(ii), 256 (2), 257 (2), 258 (2)-(4), 259 (F4), 261; REV-COMB-4 R4-09, R4-12, R4-13):',
    '- F-14: the LC-TB70 v2 rules quoted verbatim from mechanical.json v2.4 (J-FWD replace rule on Q_JFWD > 60.0 bar abs, no minimum',
    '  duration; the envelope and one-Z3-per-assembly rules), the TB-state abort set as confirmed by Mechanical (F4) with PC_SENSOR HIGH,',
    '  and the Q_JFWD signal per platform (SIL exact, stand B-DPC-1 after a noise record, flight C1 LIGHT_SPIKE raw >= 47.5 bar abs).',
    '  The v4 citation (electronics_v4 l.6575, "bench plan v4 F-14") is corrected in electronics_v4.1.json.',
    '- F-13: the soak condition and the facility thermometer accuracy (R3-06). F-6 / F-10 / BOM 251: the C1 compensated band (R3-05).',
    '- B-PC-1: the zero TC per serial (seat coefficient and T_cal for option (b)), the seat-TC channel and the ARM sanity static term rows;',
    '  the comparator band with the uncompensated drift (R3-01 item 8); the over-range margin on the R4-09 face bound.',
    '- B-DPC-1: the stand Q_JFWD row. B-TC-1: the CJTO trim step and the EMI mean-shift pass (R3-03). B-MV-1: post-abort closure (N-01).',
    '- B-BLEED-1 / CHK-BT: the purge FINAL (2.43 s flow, 2.39 s cap, calibration constants, rule (d) with (d1) / (d2), PURGE at E0 - 2.90 s).',
    '- T1-T4: the DC-C / DC-D segments and the re-sized T4 firing planned inside A = 150 C at the B1 end-of-burn heating rate (N-07).',
    '- B-ECU-1: log v13 (185 B). A1 pad go/no-go: the seat-compensation row.',
    '',
    'What changed from v3 (REV-ELEC-2 R2-02, R2-06, R2-13, R2-14, R2-19, R2-22; LEAD CHANGELOG 203 (2), 205, 206 (3), 216 (2)(c), (5), (6),',
    '(9), 230 (3)-(4), 243 (3), 248 and the Part A rulings of 2026-10-20): section 0 (founder block); B-PC-1 on C1; B-TC-1 and CHK-BT;',
    'B-FC-1 lost-DROGUE-0 and lift-commanded R2 hold; B-BLEED-1 on the one flow basis; R2-13 residuals; HIL-OT-1 / HIL-TR-1 written out.',
    '',
]

# ---------------------------------------------------------------- section 0
rep('| F-6 |', '| F-6 | RFQ BOM 251 (Electronics addition) | Kulite XTL-190SM-2000A × 3 + 1 spare: absolute mode, M5 × 0.8 short body, O2-clean '
    'processing, FKM or metal seal instead of the supplied silicone O-ring. Compensated band (R3-05; the v4 "20-120 °C" is WITHDRAWN: the sheet '
    'offers "any 100 °F range", 55.6 K): order the 100 °F band 0-55.6 °C (32-132 °F) from the coldest ARM (flight ambient 0 °C, stand ≥ 0 °C '
    'ASSUMED) through the hottest flight A1 relight seat (40 + 14.7 = 54.7 °C at the light [DERIVED, Mechanical SIM rise from ARM]); the stand '
    'relight after a B1-length burn reaches about 78 °C at E1 (24 + 54.4 K [DERIVED]), outside any 100 °F band that starts at 0 °C: F-10 (b) | '
    'flight Pc / P_feed / P_mid (LEAD 205, 206 (3)); option (b) seat compensation | quote and the inquiry F-10 answered |')
rep('| F-10 |', '| F-10 | Kulite inquiry (XTL-190SM-2000A) | ordering code in absolute mode at 2000 psi; compensated band (R3-05): (a) the 100 °F band '
    '0-55.6 °C of F-6 and (b) a wider compensated band 0-85 °C (coldest ARM to the hottest stand relight seat + margin) if offered; for each, '
    'the thermal zero shift MAXIMUM (the sheet gives ±1 % FS / 100 °F typical only = 0.0248 bar/K; the firmware residual budget uses k = 3 '
    'and the SIL S13T sweeps k 1-3, ASSUMED) and the zero non-linearity over the band; seal options; O2-clean processing; cable mass per metre '
    '(the mass delta uses 10 g/m ASSUMED); shock rating (MISSING in the sheet); current datasheet revision; delivery to DK-6400 | BOM 251, the '
    'mass statement, B-PC-1 zero-TC row, kPcRezeroMax_Pa basis | written answer on file |')
rep('| F-13 |', '| F-13 | stand T0 rule (LEAD ruling 2026-10-20; basis LEAD 249 (2): 20 + 4.48 / 0.96 = 24.67 °C less 0.5 K for the facility '
    'thermometer) | founder pre-fire checklist row (R3-06): the engine SOAKED at the stand ambient: both case TCs TC1 / TC2 within 1 K of the '
    'facility thermometer for at least 30 min [DESIGN], with the facility thermometer calibrated to ±0.5 K (certificate on file), and that '
    'reading ≤ 24 °C (297.15 K) before any stand ARM; the ECU refuses a stand ARM above 24 °C on TC1 / TC2 (Abort CASE_WARM_STAND 31, a '
    'backstop; the checklist is the control) | stand start temperature basis of the case-TC rows | checklist row in use |')
rep('| F-14 |', '| F-14 | J-FWD replace rule and TB-state (LC-TB70 v2; LEAD 248, 258 (3); Mechanical F4, line 259) | (1) Quoted verbatim from '
    'mechanical.json v2.4 lc_tb70_envelope_v352.jfwd_replace_rule_v2.rule: "' + RULE + '". (2) The quantity, verbatim (.quantity): "' + QTY +
    '"; level 60.0 bar abs, duration: none (one exceedance at any time in the run). (3) Envelope rules, verbatim (.rules[1], [2]): "' + R_ENV +
    '"; "' + R_ONE + '". (4) Founder rule (LEAD 248), beside (1): after ANY case-TC abort (Abort OVER_TEMP 6 from TC1 / TC2 at 423.15 K) or a '
    'TB-state abort the J-FWD joint counts as used: the same inspection as (1) before the next firing. TB-STATE ABORT = the ECU abort cause '
    'HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START, OVER_TEMP, or PC_SENSOR on the HIGH side (transducer output ≥ 4.75 V = 146.5 bar abs); '
    'the LOW side (below 0.25 V: open wire, short) is NOT one; OVER_THRUST is information only (Mechanical F4 verdict, verbatim: "' + F4 +
    '"). Firmware v2.12 latches it as f3 TB_STATE (log v13 f3_flags b0; b1 TB_PCS_HIGH for the HIGH cause), cleared at the next ARM. '
    '(5) Signal for Q_JFWD: stand = B-DPC-1 DC-restored with C1, sample step ≤ 0.05 ms in the windows, Q_JFWD computed post-run with '
    'inside_v2 (04-fea/v352/lc_tb70_envelope.py d14489808338006b), usable only after a no-event B-DPC-1 noise record has been run through '
    'inside_v2 (B-DPC-1 row; TO-VERIFY: until a noise-floor rule is derived and reviewed, a noise-driven trigger still means the inspection); '
    'flight = the C1 LIGHT_SPIKE raw peak ≥ 47.5 bar abs sets f3 JFWD_LS (log v13 b5) [DERIVED from the C1 chain model on the 896-case grid: '
    '0 misses of the 298 Q_JFWD > 60 cases on each of the four C1 chains (lowest raw peak among them 47.750 bar abs), and 128-152 of the 598 '
    'other cases flagged as well; TO-VERIFY on hardware; the ideal sampler gives 40.381 bar abs, information]; the 1 kHz flight record is a '
    'LOWER BOUND and Z3 v2 is NOT EVALUATED in flight. In flight the joint cannot be replaced before the relight (OPEN, lead) | joint life '
    '(Mechanical) | rule in the stand procedure; the post-run Q_JFWD script on the stand PC |')

# ---------------------------------------------------------------- order and gates
rep('| 2 | B-ECU-1 |', '| 2 | B-ECU-1 | I/O, CAN, watchdog, log v13, ladder decode with decade box (RE-19) | step 1 |')
rep('| 3 | B-PT-1, B-PC-1, B-TC-1 |', '| 3 | B-PT-1, B-PC-1, B-TC-1 | P_tank calibrated budget (guard band); C1 Pc trims, post-zero residual '
    '(`kBpc1Shown`), zero TC per serial (seat coefficient and T_cal, option (b)), seat-TC channel, 20 s drift, comparator; case-TC CJTO trim, '
    'offset and tau | step 2, clean dry N2 0-70 bar g, reference gauge (BOM 245), TC reference (BOM 266), temperature chamber 0-85 °C (TO-DEFINE) |')

# ---------------------------------------------------------------- B-ECU-1
rep('| CAN frames against `protocol.h` v2.11', '| CAN frames against `protocol.h` v2.12 (TLM_FAST d4-d5 encoder lift, TLM_RELIGHT d6 b7 PC_VALID, '
    'EVENT 0x120 incl. R2_BACKSTOP 0x24) | decoder round trip, 0 CRC errors over 10 min |')
rep('| Log record v12', '| Log record v13 (185 B = v12 + seat_comp_hPa int16 + seat_ref_dK int16 + f3_flags uint8, CRC-16; `kLogVersion` 13) '
    'at 1 kHz | 0 CRC errors, 0 missing records over 10 min; f3 bits b0 TB_STATE, b1 TB_PCS_HIGH, b2 SEAT_COMP, b3 SEAT_FROZEN, b4 SEAT_NOREF, '
    'b5 JFWD_LS, b6 PT_RZ_REJ decode as set by the injected conditions |')

# ---------------------------------------------------------------- B-PC-1
rep('| Zero TC and 20 s drift (RE-07) |', '| Zero TC per serial (R3-01 option (b), R3-05) | in a temperature chamber with the seat TC (TC4, '
    'BOM 205 at the C1 boss as flown) fitted: the zero at ≥ 6 temperatures over 0-85 °C (coldest ARM to the hottest stand relight seat + margin), '
    '2 cycles, reference ≤ 0.05 bar; fit the coefficient [Pa/K] (linear) and T_cal (the temperature of the XdcrCal::offset_Pa zero); record '
    'them per serial (table below) and load them with setPcSeatCoef / setPcSeatTcal (SAFE only). Pass: |coef| ≤ 1.0e4 Pa/K (firmware '
    'bound) and the fit residual over each ARM → relight span used (A1 ARM → re-zero2 12.5 K; stand ARM → re-zero2 50.4 K [DERIVED, '
    'Mechanical SIM]) ≤ 10 % of coef × ΔT (the eps of the option (b) residual budget: A1 0.185 / 0.027 bar, stand 0.551 / 0.054 bar at '
    'k = 3 [DERIVED]); otherwise the budget is re-done with the measured residual before kPcRezeroMax_Pa (0.30 bar) is kept. A stand '
    'relight after a B1-length burn needs ≤ 5 % at k = 3: with the coefficient 10 % low the SIL stand relight is REFUSED NOT_VENTED at '
    'k ≥ 2 (safe, no light; S13T comp_under [SIM]) |')
after('| Zero TC per serial (R3-01 option (b), R3-05) |', [
    '| 20 s drift (RE-07) and post-burn zero | the A1 relight needs the COMPENSATED residual < 0.30 bar from the ARM zero (re-zero limit '
    'kPcRezeroMax_Pa); 20 s drift at 25 and 55 °C ≤ 0.05 bar; at the first static fire the post-burn zero check logs seat_comp_hPa / seat_ref_dK '
    '(log v13) against the vented-chamber reading (LEAD 205 closures) |',
    '| Seat-TC channel (TC4: MAX31856 U904, J904, BOM 205; option (b)) | offset ≤ 0.3 K against BOM 266 at 0 / 25 / 85 °C after the CJTO '
    'trim (as B-TC-1); time constant ≤ 0.25 s on the boss (the SIL lag); TC open at ARM → f3 SEAT_NOREF and compensation OFF for that arming; '
    'TC open or a jump > 150 K after ARM → f3 SEAT_FROZEN (last value held); 5 trials each |',
    '| ARM sanity static term (v2.12) | soaked at 0, 20 and 40 °C (chamber), vented: the reading minus coef × (T_seat − T_cal) within 0.5 bar '
    '(kPcArmZeroMax_Pa) and ARM accepted; with the coefficient 0 (v2.11 fallback) the uncompensated zero shift k × 0.0248 bar/K × (T0 − T_cal) '
    'is checked alone: ARM refused PC_SENSOR beyond 0.5 bar (SIL S13T before the static term, and the v2.12 fallback runs: refused at 0 / 40 °C for k ≥ 1.5, and on one sign at k = 1.0 [SIM]) |',
    '',
    'Per-serial record (B-PC-1 zero-TC row; loaded at boot by the HAL; SAFE-only setters):',
    '',
    '| Serial | coef [Pa/K] | T_cal [K] | fit residual [bar] over 0-85 °C | span A1 12.5 K / stand 50.4 K residual [bar] | date, run |',
    '|---|---|---|---|---|---|',
    '| (C1 #1) | MISSING | MISSING | MISSING | MISSING | |',
    '',
])
rep('| HW comparator U330', '| HW comparator U330 (C1 tap 47.5k / 47.5k, threshold 174k / 29.4k) | trips inside 31.08-34.11 bar abs (DERIVED band; '
    'nominal 32.59) and above the firmware 30.0 bar abs, 5 ramps at 25 °C; default build tau 5.225 ms; ride-through build (C330 + C330B, 540 nF) '
    'tau 12.10-13.55 ms measured by a step. U330 is NOT seat-compensated: the C1 thermal zero shift moves its band by k × 0.0248 bar/K × '
    '(T_seat − 20 °C) (A8, results/v2p12/c1_drift_v2p12.json [DERIVED]): k = 3, stand relight light at T0 24 °C 26.62-38.56 bar abs, A1 burn end '
    'at T0 40 °C 28.44-36.74; repeat 3 ramps with the C1 at 55 °C to confirm the shift sign and size per serial |')
rep('| Over-range (C1) |', '| Over-range (C1) | NOT required for flight (0 of 896 FA-1 cases reach 146.5 bar abs, SIM). R4-09: the Pc-port face '
    'bound is 130.2 / 131.3 / 130.5 bar abs over c 181-1200 m/s (CC-1 6 mm3 / CC-1 20 mm3 / CC-2) [Combustion v2.4c], so the margin to the '
    '137.9 bar abs FS is ≥ 6.6 bar at c ≥ 181 m/s (not about 16 bar), 15.2 bar to the 4.75 V level 146.5 bar abs [DERIVED]; the 070BG row is F-12 |')
rep('| `kBpc1Shown` |', '| `kBpc1Shown` | set only after RE-02 closes; stays false in v2.12 (the SIL runs both builds) |')

# ---------------------------------------------------------------- B-DPC-1
after('| Use | IGN-1 and the T series.', [
    '| Q_JFWD (LC-TB70 v2 J-FWD replace rule, F-14) | DC-restore with the C1 channel (pre-light level and the first-order coupling inverted); '
    'sample step ≤ 0.05 ms in the windows (51.2 kS/s = 0.0195 ms); the whole run from before the light (first sample ≤ 2.0 bar abs); '
    'inside_v2(t, p) post-run (log inside, zone_max, ESP max and its period, Q_JFWD, jfwd_rule_triggered). FIRST a no-event record (stand '
    'pressurised, no firing, ≥ 60 s) through inside_v2: Q_JFWD and the ESP of the noise alone logged (TO-VERIFY; until a noise-floor rule '
    'is derived and reviewed a noise-driven trigger still means the inspection) |',
])

# ---------------------------------------------------------------- B-TC-1
rep('| Static offset in situ', '| Static offset and CJTO trim (R3-03) | step 1: case heated to 150 °C, steady, each channel against the BOM 266 '
    'reference; step 2: write the offset to the MAX31856 CJTO register (0.0625 °C LSB) per channel; step 3: re-measure at 100 / 130 / 150 °C: '
    'residual ≤ 0.3 K at each point. The calibrated tolerance uses it: tol_lo,cal = 5.85 + 0.630 r K, 10.28 K at 7.03 K/s, TC-01 maximum at the '
    'trip 161.82 °C [DERIVED, case_tc_channel_v1]. Without the trim (CJTO 0) the untrimmed formula applies: |offset| ≤ 0.6 K, tol_lo = 6.45 + '
    '0.630 r K, 10.88 K at 7.03 K/s, TC-01 162.4 °C [DERIVED] |')
rep('| EMI | servos, pintle rail and spark running', '| EMI (R3-03) | servos, pintle rail and spark running against all off, ≥ 30 s each, '
    '3 repeats: |mean(actuators on) − mean(off)| ≤ 0.5 K (the budget term is a ground-offset bias, so the pass is a mean shift), and the spike '
    'rejection: a burst of single-conversion spikes to 443 K for < 0.20 s gives no OVER_TEMP (0.20 s persistence) |')

# ---------------------------------------------------------------- B-MV-1 (N-01)
after('| OPEN/CLOSED switch codes through the J508 ladder |', [
    '| Post-abort closure with the pintle on the ARM bus (REV-ELEC-3 N-01; with HIL-TR-1) | replay the S6R ramp60_50ms case on both builds: '
    'U330 drops +12V_ARM (SIL 5.211 s as built, 5.218 s ride-through); record the MV-P closed switch, the pintle encoder and drive current '
    'after the drop (the pintle is powered from +12V_ARM, sim.cpp l.289: no drive after it) and the head-pressure decay (bridge simulator in '
    'HIL; B-DPC-1 on the stand). Pass: MV closed ≤ 2 ms + its travel after the trip; the decay no slower than the SIL post-abort model '
    '(gop × ff, ASSUMED), otherwise the model is re-fitted and S6R re-run (SIL head peak 56.61 bar as built, 47.94 bar ride, both inside LC-TB70) |',
])

# ---------------------------------------------------------------- CHK-BT and B-BLEED-1 (purge FINAL)
rep('| Timer width (BOTH held high on a fixture)', '| Timer width (BOTH held high on a fixture), 10 trials at 25 °C and at the board temperature '
    'extremes | 2.577-2.741 s (nominal 2.659 s; DATASHEET 3.0 % grade + 0.1 % RSET) and > the firmware cap + 1 tick (v2.12 FINAL: 2.39 + 0.001 = '
    '2.391 s). Option, not applied: RSET 59.0 kΩ → 2.475 s nominal, 2.398 s minimum (closer to the 2.397 s rule-(d) bound) |')
rep('| Schedule not cut |', '| Schedule not cut | a scheduled purge (both-open command span 2.38 s = 2.43 + 0.03 − 0.08): V1 never dropped by the '
    'timer, 10 purges |')
rep('| Purge mass per scheduled purge |', '| Purge mass per scheduled purge (FINAL, LEAD 256 (2), 257 (2)) | 10 purges, weigh scale or Coriolis '
    '(BOM 244) | ≤ 76 g VENTED N2O (LEAD; the vehicle-level mass leaving through the bleed). Scheduled flow 2.43 s → 71.1 g at 29.25 g/s '
    '(289.5 K basis, LEAD 230 (3)), 75.5 g at the 31.06 g/s warm end (297.15 K) [DERIVED]. Need: 1.9 s at 289.5 K and 2.2 s at 283.15 K '
    '(Combustion purge_duration_v2p4.json 1ff6bfcd7d2f454c on 2 × 0.707 mm; LEAD 256 (2)(a)): margin 0.23 s at 283.15 K. Tank LIQUID depletion '
    'is larger (LEAD 181 (10)) |')
rep('| Purge mass at the firmware cap', '| Purge mass at the firmware cap (both-open COMMAND cap 2.39 s, physical flow 2.44 s) | 5 purges with V1\'s '
    'close command inhibited (test build) | ≤ 76 g vented: 71.4 g on the 29.25 g/s basis, 75.8 g at the 31.06 g/s warm end [DERIVED] |')
after('| Purge mass at the firmware cap', [
    '| Rule (d) re-set of the calibration constants (LEAD 256 (2), 257 (2), 258 (2)) | CF-4 / B-BLEED-1: ≥ 10 purges | measure the N2O Cd × A '
    'of the two-tap path and the valve times t_open / t_close; cap ≤ 76 g / mdot(297.15 K) − (t_close − t_open), mdot at the warm end from '
    '(d1) the UPPER 95 % BOUND of the measured Cd × A (not its mean); flow ≤ cap + t_close − t_open − 2 ticks; never above 2.43 s flow / '
    '2.39 s cap (the defaults are the maxima); (d2) CF-4 shows the 283.15 K need at the re-set flow. Load with setPurgeCal (SAFE only); '
    'S12 re-run. At the defaults the bound is 2.397 s (76 / 31.06 − 0.05) |',
    '| PURGE command time | B-FC-1 timing | the FC sends PURGE at E0 − 2.90 s (kPurgeRelight_s kept); flow start PURGE + 0.42 s, flow end E0 − 0.05 s; '
    'logged edge to edge on 10 purges, ± 1 tick |',
])

# ---------------------------------------------------------------- T1-T4 (N-07)
after('| Also logged | IMU vibration spectrum', [
    '',
    'Planning rule (REV-ELEC-3 N-07; LEAD 261; gnc.json v3.2 duty_cycles.note_n07_rev_gnc_7; T1-T4 v3.2 l.294): no planned burn may reach the '
    'case abort A = 150 °C at the B1 end-of-burn heating rate 7.03 K/s (GVHI rev-4 station rate [SIM]); from a soaked start (F-13, ≤ 24 °C) '
    'the DC-D first burn would cross at about 23.5 s (merged bound [DERIVED]). A burn starting with the case TCs at T_s is planned for '
    't ≤ (150 − 5 − T_s) / 7.03 s (5 K margin); a relight is held until TC1 / TC2 ≤ T_s (the firmware refuses above 130 °C, CASE_HOT, a backstop).',
    '',
    '| Firing (re-sized) | Content and objective | Planned burns | Case condition | N2O |',
    '|---|---|---|---|---|',
    '| D1 (GNC DC-D segments 1-2) | staircase 500 → 62.5 N (throttle 1.0 → 0.125), then steps 100 ↔ 500 N: throttle map and Pc loop | one burn '
    '15.6 s (0.90-16.52 s of DC-D v2) | soaked start; ends ≥ 7.9 s before the 23.5 s crossing | 2.06 kg [DERIVED from GNC] |',
    '| D2 (DC-D segment 3) | sweep 175-399 N | one burn 8.0 s | soaked start | 1.16 kg |',
    '| D3 (DC-D 500 N hold; GNC F_acc at ≥ 450 N and IMU vibration at F_max) | 500 N hold, twice for ≥ 10.13 s at ≥ 450 N in total | two firings of '
    '6.0 s | soaked start each | 2 × 1.44 kg |',
    '| D4 (DC-D burns 2 and 3: triangle to 428 N, hold at 130 N) | relight content (not the A1 relight) | after a cold first burn ≤ 10 s; burn 2 '
    '7.75 s needs T_s ≤ 90 °C, burn 3 9.76 s needs T_s ≤ 76 °C [DERIVED] | relight held until the case is there | 0.94 + 0.60 kg |',
    '| T4 (Combustion, re-sized to the shortest firing, LEAD 261) | burn 1 on the B1 p99 profile (21.76 s at 0.257, 1.54 kg; erosion and soak at '
    'the B1 sizing duty), coast, one relight 4.59 s at 0.47 (relight latency from a soaked state; the A1 p99 record 3.78 s at 0.88, coast to 22.79 s) | '
    'burn 1 21.76 s (1.7 s before the 23.5 s crossing; the 23.58 s max-profile burn is NOT planned: it reaches A); relight 4.59 s | the relight needs '
    'T_s ≤ 112.7 °C (150 − 5 − 32.3): at the B1 p99 end the case is about 137.8 °C, so the coast is "about 19 s or until TC1 / TC2 ≤ 112.7 °C", '
    'whichever is later; if the case is not there by the end of the planned coast the relight is shortened to (145 − T_s) / 7.03 s or not run | about '
    '2.0 kg [ESTIMATE, LEAD 261] |',
    '| DC-C | no Combustion T4 objective (T1-T4 v3.2 l.294); GNC F_acc rows at ≥ 450 N are flown in D3 | not planned | | 0 |',
    '',
    'OPEN (Combustion / Mechanical, N-07): whether a coast longer than about 19 s (case to 112.7 °C) still meets the "relight from a soaked state" '
    'objective, and the case soak-back after B1 (the cooling the coast row relies on is not in any published history); the T4 rows of T1-T4 v3.2 '
    'l.61, 143-145 and 171 stay the DC-D computation [SIM] until Combustion re-runs them on the re-sized profile.',
])

# ---------------------------------------------------------------- A1 pad go/no-go
after('| Tank cold rule |', [
    '| Seat compensation (v2.12 option (b), LEAD working basis) | after ARM: log v13 f3 SEAT_COMP set and SEAT_NOREF clear (per-serial coefficient '
    'and T_cal loaded, seat TC valid over the ARM window); with the fallback build (coefficient 0) the A1 relight runs on the v2.11 limits and the '
    'flight ARM ambient must satisfy |T0 − T_cal| × k × 0.0248 bar/K < 0.5 bar (ARM sanity) | Electronics (B-PC-1 record); LEAD to confirm (b) |',
])

# ---------------------------------------------------------------- outputs
after('| B-PC-1 (C1) |', [
    '| B-PC-1 zero TC per serial | seat coefficient and T_cal (setPcSeatCoef / setPcSeatTcal); kPcRezeroMax_Pa / kIgnBaseCheck_Pa kept or re-derived '
    'with the measured residual; F-10 answer (thermal-zero maximum k) |',
    '| B-DPC-1 Q_JFWD | the stand J-FWD replace rule in use (F-14) after the noise record; a noise-floor rule if the noise trips it |',
    '| Rule (d) (CF-4 / B-BLEED-1) | setPurgeCal(flow, cap) per rule (d) with (d1) / (d2); S12 re-run |',
])
out = '\n'.join(lines)
open(sys.argv[1], 'w', encoding='utf-8').write(out)
print('written', sys.argv[1], len(out), 'chars', out.count('\n') + 1, 'lines')
