#!/usr/bin/env python3
"""Electronics v2.13 (2026-10-21): bench plan v5.1 = bench plan v5 (staging_v2.12/docs/bench_plan_v5.md 360c1d6695cc305c) with the
REV-ELEC-4 corrections E4-02 (B-PC-1 l.156 rule and table), E4-06 (1)-(5) (A1 pad row, T4 restated, BOM row label, C7 stand-DAQ TC,
the TC4 rows of B-PC-1 l.158 and B-TC-1) and the lead's v2.13 rulings (RULING 1 (c) build-bits pad row; ITEM 3 TC4 conversion period).
Every replaced line is asserted before it is changed. Run: python3 -B -I make_bench_plan_v5p1.py <v5.md> <out.md> <generated_utc>
"""
import hashlib, re, sys
src, out, gen = sys.argv[1], sys.argv[2], sys.argv[3]
assert re.fullmatch(r'2026-10-21T\d\d:\d\d:\d\dZ', gen)
raw = open(src, encoding='utf-8').read()
assert hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16] == '360c1d6695cc305c'
L = raw.split('\n')
def sub(idx, old, new):
    assert old in L[idx], (idx + 1, old[:60]); L[idx] = L[idx].replace(old, new)

# header (l.1-6)
L[0] = '# ARGOS engine electronics: bench and test plan v5.1'
sub(2, '06-electronics, 2026-10-21. Firmware v2.12 (SIL only)', '06-electronics, 2026-10-21 (v5.1 generated %s). Firmware v2.13 (SIL only; build = v2.11 + the v2.12 overlay + the v2.13 overlay)' % gen)
sub(4, 'Supersedes bench plan v4 (docs/bench_plan_v4.md 5b1c9336d7b8db50, kept).',
    'BOM v2.5 (`staging_v2.13/results/bom_v2p5.csv`) carries the v2.13 label and row changes. Supersedes bench plan v5 (staging_v2.12/docs/bench_plan_v5.md 360c1d6695cc305c, kept).')
v51 = [
    '',
    'What changed from v5 (v2.13; REV-ELEC-4 E4-01 MAJOR, E4-02, E4-06 (1)-(5), E4-N02; LEAD CHANGELOG 264 (2), (4), (5), (7), 266 (6)-(7); lead rulings',
    '2026-10-21 16:11Z / 16:27Z / 16:28Z). CARVE-OUT (266 (6)): option (b) (coefficient loaded) is not used for any start with ignition until the v2.13',
    'delta is reviewed; the coefficient may be loaded for B-PC-1 / B-TC-1 bench work without ignition. A1 flight and the stand relight wait for it.',
    '- B-PC-1: the "5 % at k = 3" acceptance is replaced by the k-dependent E4-02 rule and table; the seat-TC row gains the v2.13 step / rate thresholds.',
    '- B-TC-1: the TC4 row of REV-ELEC-4 Q2 (with the spark) and the TC4 conversion-period row (50 Hz filter, AVGSEL <= 2: ITEM 3).',
    '- Stand DAQ: the C7 bore-top TC (stand only, CHANGELOG l.55) is listed (BOM v2.5 stand-only row).',
    '- T4: restated as a relight-latency demonstration from a soaked state (264 (5)); it is a stand relight and waits for the lift of 266 (6).',
    '- A1 pad go/no-go: the 264 (2) seat row (NO-GO until the v2.13 delta is reviewed), the build-bits row (EVENT BUILD 0x25 after power-up and at',
    '  the ARM attempt), the 264 (7) JFWD_LS row; a refused ARM is read from the log byte abort_cause (SEAT_TC 32 among the causes).',
]
for i, l in enumerate(v51): L.insert(6 + i, l)
off = len(v51)
def I(n): return n - 1 + off   # v5 line number -> index in L

# B-PC-1 l.156: E4-02
sub(I(156), 'A stand relight after a B1-length burn needs ≤ 5 % at k = 3: with the coefficient 10 % low the SIL stand relight is REFUSED NOT_VENTED at k ≥ 2 (safe, no light; S13T comp_under [SIM])',
    'A stand relight after a B1-length burn needs |eps| ≤ eps_max(k_meas) of the E4-02 table below (k_meas = the fitted slope / 0.0248 bar/K, interpolated DOWNWARD in k); beyond it the stand relight after B1 is planned REFUSED NOT_VENTED (fail-safe, no relight objective claimed) [REV-ELEC-4 E4-02 / Q3; 266 (7)]')
# B-PC-1 l.158: TC4 thresholds
sub(I(158), 'TC open or a jump > 150 K after ARM → f3 SEAT_FROZEN (last value held); 5 trials each |',
    'TC open or a jump > 150 K after ARM → f3 SEAT_FROZEN (last value held); v2.13: a step > 1.5 K between consecutive conversions (every state, the light window included) → f3 SEAT_STEP; outside the light-window hold (IGNITION entry .. E2 + 0.45 s) the compensation temperature slews at ≤ 5 K/s and a reading > 3 K from it → f3 SEAT_STEP (after a hold the catch-up rule applies: trip if the gap grows 1.5 K above its lowest value or is still > 3 K at 2 × the hold duration); on SEAT_STEP the compensation is held until the next ARM (decade box / TC simulator, 5 trials each) |')
# E4-02 table after the B-PC-1 table: insert after l.159 (ARM sanity row)
e402 = ['',
        'E4-02 acceptance table (REV-ELEC-4 Q3; DERIVED on Mechanical SIM seat histories x the DATASHEET typical 0.0248 bar/K; tau 0.25 s and the 0.3 K TC error ASSUMED; adders 0.1012 bar):',
        '| k | eps_max with the 0.1012 bar adders (governs) | without adders | SIL point (REV-ELEC-4 F3, no adders) [SIM] |',
        '|---|---|---|---|',
        '| 1.0 | 11.2 % | 19.2 % | not run |',
        '| 1.25 | 8.1 % | 14.5 % | not run |',
        '| 1.5 | 6.0 % | 11.3 % | not run |',
        '| 2.0 | 3.4 % | 7.4 % | all 5 variants RUN, both re-zeros accepted |',
        '| 2.5 | 1.8 % | 5.0 % | not run |',
        '| 3.0 | 0.8 % | 3.4 % | -3 % RUN; -4 % RUN on re-zero1; -5 % / -0.3 K GVLO REFUSED NOT_VENTED (both signs); +5 % / +0.3 K RUN |',
        'Re-zero1 does not close at k = 3 with the adders even at eps 0 (not a second line to count on). The A1 relight is not affected (A1 re-zero2 closes to 11.5 % at k = 3 with the adders; the 10 % pass criterion holds for flight, thinly: E4-N06).']
for i, l in enumerate(e402): L.insert(I(159) + 1 + i, l)
off += len(e402)
def I2(n): return n - 1 + off   # v5 line numbers after l.159

# B-TC-1 (v5 l.193-201): TC4 rows appended after the last B-TC-1 table row (v5 l.201)
assert L[I2(193)].startswith('### B-TC-1 (new): case-TC channel')
last = I2(201)
while not L[last + 1].startswith('| ') and False: pass
tc4 = ['| TC4 seat TC with the spark (v2.13, REV-ELEC-4 Q2; option (b)) | set-up: TC4 as installed (C1 boss, flight J904 harness, engine grounded as flown); spark at the flight rate, torch valves cycling, servos and pintle rail on, against all off; ≥ 30 s each, 3 repeats, every conversion logged. Pass: mean shift ≤ 0.3 K; per-conversion peak deviation ≤ 1.0 K (below the 1.5 K step threshold: no nuisance SEAT_STEP); no MAX31856 fault bit (OVUV / open); with the TC simulator, one-conversion steps of ±2, ±10, ±55 and +140 K: inside [IGNITION entry, E2 + 0.45 s] they change neither P0, nor the rise, nor the E2 tick; inside or outside that window they set SEAT_STEP and the compensation holds. Also verify the grounded-junction common-mode behaviour on the MAX31856 input [TO-VERIFY against the datasheet; E4-N10, OI-TC4-GROUNDED-JUNCTION] |',
       '| TC4 conversion period (v2.13, LEAD ITEM 3) | U904 configured 50 Hz notch (CR0 bit 0 = 1), auto-conversion (CMODE = 1), AVGSEL ≤ 2 samples: the logged conversion-to-conversion period ≤ 0.130 s (DATASHEET 19-7534 Rev 0 tCONV 50 Hz 98 / 110 ms TYP / MAX + 20 ms per extra sample; TYP / MAX columns TO-VERIFY on the PDF) over ≥ 300 conversions; a longer period needs kPcSeatStepMax_K re-derived (6 × 2.42 K/s × period) before any start with option (b) |']
k = I2(201)
assert L[k].startswith('| Abort and limits |'), L[k][:40]
for i, l in enumerate(tc4): L.insert(k + 1 + i, l)
off += len(tc4)
daq = ['',
       'Stand DAQ thermocouple (v2.13, REV-ELEC-4 E4-06 (4); CHANGELOG l.55): the C7 bore-top TC (type K, the v2.7 CF-3 / T1 bore-top position) is a STAND-DAQ channel only (not on the ECU; the ECU MAX31856 #4 is the C1 seat TC since v2.12): BOM v2.5 stand-only row; logged on the stand DAQ time base (≤ 1 ms sync).']
k = I2(201) + len(tc4)
for i, l in enumerate(daq): L.insert(k + 1 + i, l)
off += len(daq)

# T4 row (v5 l.385) and the OPEN line (l.388): 264 (5)
k = I2(385)
assert L[k].startswith('| T4 (Combustion, re-sized to the shortest firing, LEAD 261) |')
L[k] = ('| T4 (Combustion; LEAD 261, 264 (5) SHORTER RELIGHT ADOPTED) | burn 1 on the B1 p99 profile (21.76 s at 0.257, 1.54 kg), coast, one relight that '
        'DEMONSTRATES RELIGHT LATENCY FROM A SOAKED STATE (the light, the latency measurement and a steady-Pc segment); it is not a 4.59 s landing-length relight '
        'from the B1-soaked state | burn 1 21.76 s; relight length set by Combustion in the T4 re-run of 261 (2) with Mechanical\'s soak-back, cut so that no '
        'planned segment crosses A = 150 °C (case about 137.8 °C at the B1 p99 end [DERIVED]); the coast is NOT lengthened to make margin | T4 is a stand relight: '
        'it waits for the lift of the 266 (6) carve-out (v2.13 reviewed) and needs |eps| ≤ eps_max(k_meas) (E4-02) | TO-SET by the T4 re-run |')
k = I2(388)
assert L[k].startswith('OPEN (Combustion / Mechanical, N-07)')
L[k] = ('OPEN (Combustion / Mechanical, N-07; 264 (5)): the T4 relight length from the T4 re-run with the soak-back (soak-back can raise the case after '
        'shutdown and is not modelled); the T4 rows of T1-T4 v3.2 stay the DC-D computation [SIM] until Combustion re-runs them on the shorter-relight profile.')

# A1 pad list (v5 l.393-409)
k = I2(395)
sub(k, 'the ECU items are SIL evidence (v2.11) until B-ECU-1, B-BLEED-1, B-TC-1 and B-FC-1 pass.',
    'the ECU items are SIL evidence (v2.13) until B-ECU-1, B-BLEED-1, B-TC-1 and B-FC-1 pass. UNDER THE 266 (6) CARVE-OUT THE A1 PAD IS NO-GO until the v2.13 delta is reviewed (REV-ELEC-5).')
idx_armed = [i for i, l in enumerate(L) if l.startswith('| ECU armed |')]
assert len(idx_armed) == 1
L[idx_armed[0]] = L[idx_armed[0]].replace('on the stand also CASE_WARM_STAND above 297.15 K)',
                                          'on the stand also CASE_WARM_STAND above 297.15 K; v2.13 flight A1 image: SEAT_TC (32) without the coefficient or with TC4 invalid). '
                                          'On a refused ARM read the cause from the log byte abort_cause (no CAN frame carries an ARM-refusal cause)', 1)
assert 'SEAT_TC (32)' in L[idx_armed[0]]
idx_seat = [i for i, l in enumerate(L) if l.startswith('| Seat compensation (v2.12 option (b), LEAD working basis) |')]
assert len(idx_seat) == 1
L[idx_seat[0]] = ('| Seat compensation (264 (2); v2.13) | the B-PC-1 coefficient is loaded (non-zero) and TC4 is valid and in range at ARM (the A1 flight image refuses ARM SEAT_TC otherwise); '
                  'after ARM: log v13 f3 SEAT_COMP set, SEAT_NOREF and SEAT_STEP clear. The fallback (coefficient 0) is NOT a flight configuration (264 (2)). NO-GO until the v2.13 delta is reviewed (266 (6)) | '
                  'LEAD 264 (2), 266 (6); ECU v2.13 armChecksOk / startBlock; Electronics (B-PC-1 record) |')
extra = ['| Build bits (LEAD 16:11Z RULING 1 (c), 16:27Z option (2)) | EVENT BUILD 0x25 read after power-up AND at the ARM attempt: arg b0 seat_arm_rule = 1 and b1 hbleed_fitted = the A1 build value (1 unless CF-4 clears the bleed: kHbleedFitted, LEAD 2026-10-13); log v13 ovr_flags b7 = 1. Any other value: NO-GO (FMEA-A1-SEAT-RULE-BUILD) | LEAD RULING 1; ECU v2.13 (Outputs::build_event / build_bits); Electronics |',
         '| JFWD_LS relight inhibit (264 (7) PROVISIONAL) | the A1 image carries kJfwdLsRelightInhibit TRUE; in flight a flagged first light (f3 JFWD_LS) makes the ECU refuse PURGE / RELIGHT JFWD_USED (TLM_RELIGHT d6 & 0x3F = 17) and the FC takes the lost-relight outcome of gnc.json v3.2 | LEAD 264 (7); ECU v2.13; founders confirm at flight acceptance with T-F1 |']
for i, l in enumerate(extra): L.insert(idx_seat[0] + 1 + i, l)
txt = '\n'.join(L)
for s in ('≤ 5 % at k = 3', 'SIL evidence (v2.11)', 'Seat compensation (v2.12 option (b), LEAD working basis)', 'relight 4.59 s |'):
    assert s not in txt, s
open(out, 'w', encoding='utf-8').write(txt)
print('wrote', out, len(txt.encode('utf-8')), 'B', txt.count('\n') + 1, 'lines')
