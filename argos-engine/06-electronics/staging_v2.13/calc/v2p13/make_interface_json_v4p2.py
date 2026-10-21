#!/usr/bin/env python3
"""Electronics v2.13 (2026-10-21): electronics.json v4.2 (STAGED; interfaces/electronics.json v4.1 stays the published file).

Base: the published v4.1 (interfaces/electronics.json = staging_v2.12 results/electronics_v4.1.json, asserted sha256/16 c862375163393adc),
deep-copied. v4.2 folds the REV-ELEC-4 corrections (E4-01 .. E4-06, notes E4-N01 .. E4-N11), CHANGELOG 264 (1)-(8) and 266 (6)-(8), and
the lead's v2.13 rulings (16:11Z, 16:27Z, 16:28Z: RULING 1 (a)-(e) with option (2) EVENT BUILD 0x25, ITEM 2 catch-up, ITEM 3 MAX31856
tCONV, SEAT_TC 32 with the STATE-encoder guard). New constants are read from the v2.13 config.h; result numbers are read from the result
files named in 'inputs' (sha256/16 recorded), not typed. SIL / CALC / DERIVED only: nothing here is hardware validation or physical approval.

Run: python3 -B -I make_interface_json_v4p2.py <generated_utc> <v2.13 root (firmware src + results)> <out.json>
"""
import copy, hashlib, json, os, re, sys
from collections import OrderedDict

H = '/home/claude/work/shared-fallback/engine'
gen_utc, ROOT, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
assert re.fullmatch(r'2026-10-21T\d\d:\d\d:\d\dZ', gen_utc), gen_utc
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def jl(p): return json.load(open(p), object_pairs_hook=OrderedDict)
def tv(v, tag, **kw):
    d = OrderedDict([('v', v), ('tag', tag)]); d.update(kw); return d
SRC = ROOT + '/firmware/src/core'
RES = ROOT + '/results/v2p13'
P = OrderedDict([
    ('v4p1', H + '/interfaces/electronics.json'), ('changelog', H + '/interfaces/CHANGELOG.md'),
    ('review_r4', H + '/reviews/REVIEW-ELECTRONICS-R4.md'), ('combustion', H + '/interfaces/combustion.json'),
    ('gnc', H + '/interfaces/gnc.json'), ('mechanical', H + '/interfaces/mechanical.json'),
    ('config_h', SRC + '/config.h'), ('types_h', SRC + '/types.h'), ('protocol_h', SRC + '/protocol.h'),
    ('item2', RES + '/item2_hold_gap.json'), ('tc_log', RES + '/sil/test_core_v2p13_log.txt'),
    ('tcn_log', RES + '/sil/test_core_nohooks_v2p13_log.txt'),
])
OPT = OrderedDict([
    ('s13t_cmp', RES + '/s13t_compare_v2p13.json'), ('a5_s13f_sum', RES + '/a5_s13f_summary_v2p13.json'), ('s12_cmp', RES + '/s12_compare_v2p13.json'),
    ('s13f_false', RES + '/sil/S13F_tc4_fault_bpc1_false.json'), ('s13f_true', RES + '/sil/S13F_tc4_fault_bpc1_true.json'),
    ('a5_false', RES + '/sil/A5_seat_step_relight_bpc1_false.json'), ('a5_true', RES + '/sil/A5_seat_step_relight_bpc1_true.json'),
    ('bench_plan_v5_1', ROOT + '/docs/bench_plan_v5_1.md'), ('bom_v2p5', ROOT + '/results/bom_v2p5.csv'),
])
for k, p in OPT.items():
    if os.path.exists(p): P[k] = p
SHA = OrderedDict((k, h16(p)) for k, p in P.items())
EXPECT = {'v4p1': 'c862375163393adc', 'review_r4': '70b7103472eebab4', 'combustion': '7dbf425c12300658', 'gnc': 'bde317782574cbd9',
          'mechanical': '66bc53d88d444679'}
for k, s in EXPECT.items():
    assert SHA[k] == s, (k, SHA[k], s)
doc = copy.deepcopy(jl(P['v4p1'])); assert doc['version'] == 'v4.1'
cfg = open(P['config_h']).read(); proto = open(P['protocol_h']).read(); types = open(P['types_h']).read()
n_cl = open(P['changelog'], encoding='utf-8').read().count('\n')

def cnum(name):
    m = re.search(r'constexpr (?:float|double|int|bool) ' + name + r' = ([^;]+);', cfg)
    assert m, name
    e = m.group(1).strip()
    if e in ('true', 'false'): return e == 'true'
    e2 = re.sub(r'(\d)f\b', r'\1', e)
    try: return float(eval(e2, {'__builtins__': {}}, {'kPcSeatAvgselMax': cnum('kPcSeatAvgselMax') if name != 'kPcSeatAvgselMax' else 0}))
    except Exception: return e
def cline(name):
    m = re.search(r'constexpr [^\n]*\b' + name + r' = [^\n]*', cfg); assert m, name
    t = re.search(r'//\s*\[([^\]]*)\]', m.group(0)); return t.group(1) if t else 'DESIGN'
def crow(name, unit, extra_tag=None):
    v = cnum(name); return tv(v, extra_tag or cline(name), unit=unit, src='config.h ' + name)

log_size = int(re.search(r'static_assert\(sizeof\(LogRecord\) == (\d+)', proto).group(1))
log_ver = int(re.search(r'kLogVersion = (\d+)', proto).group(1))
assert log_size == 185 and log_ver == 13
assert re.search(r'constexpr uint8_t BUILD = 0x25;', proto) and re.search(r'constexpr uint8_t IGN_WINDOW = 0x15;', proto)
assert re.search(r'SEAT_RULE_BUILD = 1u << 7', types)
item2 = jl(P['item2'])
def tcount(p):
    t = open(p).read(); m = re.search(r'(\d+) passed, (\d+) failed', t); return int(m.group(1)), int(m.group(2)), t
tc_p, tc_f, tc_t = tcount(P['tc_log']); tn_p, tn_f, tn_t = tcount(P['tcn_log'])
ut_names = ['UT-1', 'UT-2', 'UT-3', 'UT-4', 'UT-5', 'UT-6']
ut = OrderedDict()
for u in ut_names:
    line = [l for l in tc_t.splitlines() if ('v2.13 ' + u + ' ') in l]
    ut[u] = 'PASS' if line and line[0].startswith('PASS') else ('FAIL' if line else 'MISSING')
ut_extra = OrderedDict((nm, ('PASS' if any(l.startswith('PASS') and key in l for l in tc_t.splitlines()) else 'FAIL'))
                       for nm, key in [('E4-N01 40 K', 'v2.13 E4-N01'), ('264 (2) pad rule', 'LEAD 264 (2) A1 pad rule'),
                                       ('264 (7) JFWD / A5 option', 'LEAD 264 (7) PROVISIONAL'), ('EVENT BUILD + log b7', 'EVENT BUILD 0x25'),
                                       ('SEAT_TC no STATE event + encoder guard', 'ARM-refusal only')])

V = 'v4.2'
doc['version'] = V; doc['date'] = '2026-10-21'; doc['generated_utc'] = gen_utc
doc['status'] = ('DESIGN + SIL + schematic, STAGED for the lead (06-electronics/staging_v2.13/, an overlay on staging_v2.12: build = '
                 'v2.11 + the v2.12 overlay + the v2.13 overlay; interfaces/electronics.json v4.1 c862375163393adc stays the published file '
                 'until the lead promotes this one after REV-ELEC-5). Firmware v2.13 runs only in SIL (no Teensy HAL). CARVE-OUT IN FORCE '
                 '(CHANGELOG 266 (6), verbatim there): option (b) (seat coefficient loaded) is not used for any start with ignition until the '
                 'v2.13 delta (light-window hold, TC4 step / rate checks, catch-up) is reviewed; A1 FLIGHT is NO-GO until then. The ECU v2.5 '
                 'schematic does NOT show the v2.11-v2.13 board items (schematic v2.6 NOT drawn); no board has been built and nothing here is '
                 'hardware-validated or physical approval. Values carry tags; open items are in open_issues.')
doc['lead_message_times_v2p13'] = ('citations "LEAD 16:11Z", "LEAD 16:27Z" and "LEAD 16:28Z" in the v2.13 sources and here name the lead messages sent '
                                   '16:11:21Z, 16:25:26Z (headed 16:27Z, CHANGELOG 268 (10)) and 16:28:24Z (CHANGELOG 268 (4))')
doc['supersedes'] = OrderedDict([('file', 'interfaces/electronics.json v4.1'), ('sha256_16', SHA['v4p1']),
                                 ('relation', 'v4.2 = v4.1 + the v2.13 delta and the REV-ELEC-4 folds; v4.1 sections kept unless named in change_summary_v4p1_to_v4p2')])
doc['scripts'] = list(doc.get('scripts', [])) + [OrderedDict([('file', 'calc/v2p13/make_interface_json_v4p2.py'), ('role', 'this file')]),
                                                 OrderedDict([('file', 'calc/v2p13/item2_hold_gap.py'), ('role', 'ITEM 2 hold-end gap and hold cost')]),
                                                 OrderedDict([('file', 'calc/v2p13/s13t_compare_v2p13.py'), ('role', 'S13T v2.13 vs v2.12')]),
                                                 OrderedDict([('file', 'calc/v2p13/a5_s13f_summary_v2p13.py'), ('role', 'A5 / S13F summary, A5 stale-compensation estimate')]),
                                                 OrderedDict([('file', 'calc/v2p13/s12_compare_v2p13.py'), ('role', 'S12 v2.13 vs v2.12, E4-05 (9) check')]),
                                                 OrderedDict([('file', 'calc/v2p13/make_bench_plan_v5p1.py'), ('role', 'bench plan v5.1')]),
                                                 OrderedDict([('file', 'calc/v2p13/make_bom_v2p5.py'), ('role', 'BOM v2.5')])]
inp = OrderedDict()
for k, p in P.items():
    rel = p.replace(H + '/', '') if p.startswith(H) else '06-electronics/staging_v2.13/' + os.path.relpath(p, ROOT)
    inp[k] = OrderedDict([('path', rel), ('sha256_16', SHA[k])])
doc['inputs'] = OrderedDict([('v4p1_inputs', doc.get('inputs')), ('v2p13', inp), ('changelog_lines_at_generation', n_cl)])
changes = []
def note(path, what): changes.append(OrderedDict([('path', path), ('change', what)]))

# ---------------------------------------------------------------- E4-05 (6) labels; 264 (2) / 266 (7) TC4 rename
tcs = doc['sensors']['thermocouples']
assert tcs['channels'][3] == 'TC4 type K bore top (U904)'
tcs['channels'][3] = 'TC4 type K C1 seat (MAX31856 U904, J904; grounded-junction MI type K at the C1 boss; input of the option (b) seat compensation)'
note('/sensors/thermocouples/channels[3]', "'bore top' -> 'C1 seat' (264 (2), 266 (7), E4-05 (6))")
tcs['tc4_hal_contract_v2p13'] = OrderedDict([
    ('hold_last_conversion', 'Inputs::tc_bore_K holds the last MAX31856 conversion between conversions (a change of the value = a new conversion '
                             'for the step check); tc_bore_valid false only on a fault (types.h)'),
    ('filter', tv('50 Hz notch (CR0 bit 0 = 1)', 'LEAD 16:11Z ITEM 3; DK (Sonderborg) and AR mains are 50 Hz')),
    ('mode', tv('auto-conversion, CMODE = 1 ("Conversions occur continuously every 100ms (nominal)")', 'DATASHEET 19-7534 Rev 0 (2/15); TO-VERIFY on the PDF')),
    ('avgsel_max_samples', crow('kPcSeatAvgselMax', '-')),
    ('conversion_period_max', crow('kPcSeatConvMax_s', 's', 'DATASHEET 19-7534 Rev 0 tCONV 50 Hz MAX 110 ms + (samples - 1) x 20 ms; TYP / MAX columns TO-VERIFY on the PDF')),
    ('tCONV_datasheet', tv(OrderedDict([('auto_conversion_2_to_n_ms', OrderedDict([('60Hz', [82, 90]), ('50Hz', [98, 110])])),
                                        ('one_shot_or_first_ms', OrderedDict([('60Hz', [143, 155]), ('50Hz', [169, 185])])),
                                        ('avgsel_add_per_conversion_ms', OrderedDict([('60Hz', '(samples - 1) x 16.67'), ('50Hz', '(samples - 1) x 20')])),
                                        ('avgsel_add_first_conversion_ms', OrderedDict([('60Hz', '33.33 per extra sample'), ('50Hz', '40 per extra sample')]))]),
                           'DATASHEET 19-7534 Rev 0 (2/15), tCONV [TYP, MAX], https://www-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/MAX31856.pdf (LEAD 16:11Z); TYP / MAX columns TO-VERIFY on the PDF')),
    ('step_limit_margin', tv('2.42 K/s x 0.110 s = 0.27 K per conversion = 5.6x under 1.5 K (1 sample); 0.31 K = 4.8x at 2 samples (0.130 s); 4 samples 3.6x, 16 samples 1.5x (not allowed); a longer configured period needs kPcSeatStepMax_K re-derived (6 x 2.42 K/s x period)',
                             'DERIVED (DATASHEET periods x SIM 2.42 K/s, REV-ELEC-4 data/seat_rate_max.json); config.h static_assert 4 x 2.42 x kPcSeatConvMax_s <= kPcSeatStepMax_K')),
    ('bench', 'B-TC-1 measures the conversion period on the flight U904 (bench plan v5.1)'),
    ('E4_N10_grounded_junction', tv('OPEN: v4.1 cites MAX31856 DS Note 6 for the case TCs ("the MAX31856 needs a floating TC, BIAS to T-"); TC4 is a '
                                    'grounded-junction MI TC at the C1 boss, which conflicts with that note (input common-mode range, open-TC detection with '
                                    'BIAS, ground loop and the E4-01 EMI path). Not closed in v2.13: the datasheet text on the grounded-junction common mode and '
                                    'fault detection has not been read from the PDF this round',
                                    'TO-VERIFY (DATASHEET 19-7534 Rev 0 Note 6, as cited in v4.1); OI-TC4-GROUNDED-JUNCTION'))])
note('/sensors/thermocouples/tc4_hal_contract_v2p13', 'new (ITEM 3: 50 Hz, AVGSEL <= 2, tCONV DATASHEET values; E4-N10 OPEN)')
hb = doc['harness_across_gimbal']
assert 'bore-top TC (stand)' in hb['bundle']
hb['bundle'] = hb['bundle'].replace('bore-top TC (stand)', 'C1 seat TC (TC4, J904)').replace('BOM v2.3 line 259', 'BOM v2.5')
note('/harness_across_gimbal/bundle', "'bore-top TC (stand)' -> 'C1 seat TC (TC4, J904)' (E4-05 (6)); BOM v2.3 -> v2.5")
ms = doc['mass_statement']
ms['seat_tc_v2p13'] = tv(OrderedDict([('C1_seat_TC_TC4_g', 5.0), ('note', 'MI type K seat TC at the C1 boss with its lead to J904 (gimballed head side)')]),
                         'ASSUMED (5 g; not weighed); Mechanical carries it in the ledger; below the 0.10 kg re-fly trigger with the v4.1 combination (+0.030 kg worst)')
note('/mass_statement/seat_tc_v2p13', 'seat TC 5 g ASSUMED (E4-05 (6))')

# ---------------------------------------------------------------- E4-05 (1), (2), (4): limits rows; (3) missing rows
L = doc['limits_v2p11']
assert L[4]['limit'] == 'purge both-open command cap'
L[4]['value'] = crow('kHbleedCap_s', 's', 'LEAD 256 (2) / 257 (2)')
L[4]['basis'] = ('v2.12 FINAL basis (CHANGELOG 256 (2), 257 (2), 258 (2)): kPurgeFlow_s 2.43 s and kHbleedCap_s 2.39 s are CALIBRATION constants, '
                 'default AND maximum (EngineEcu::setPurgeCal, SAFE only, all-or-nothing); the cap is 2.397 s at the defaults; re-set after CF-4 / B-BLEED-1 '
                 'by rule (d) with (d1) / (d2) (config.h)')
L[4]['decision'] = 'CHANGELOG 256 (2), 257 (2), 258 (2) (lead, 2026-10-21); REV-ELEC-4 E4-05 (1) replaces the stale 2.55 s / 76.05 g / 80.76 g basis'
assert L[14]['limit'] == 'light-rule baseline check'
L[14]['basis'] = 'residual + kIgnBaseDrift 0.06 + 0.10 bar = 0.76 / 0.46 bar (default / B-PC-1-shown build); per location (pad / stand refuse, A1 keeps / zeroes P0)'
assert '(CANDIDATE, default OFF)' in L[7]['limit']
L[7]['limit'] = L[7]['limit'].replace('(CANDIDATE, default OFF)', '(ADOPTED on the CHANGELOG 253 (7)(i) / 256 (3) conditions; build value kRideThroughBuild from ECU_RIDE_THROUGH)')
for i, w in ((4, 'E4-05 (1)'), (14, 'E4-05 (2)'), (7, 'E4-05 (4)')): note('/limits_v2p11[%d]' % i, w)
new_rows = [
    ('C1 seat coefficient bound', crow('kPcSeatCoefMax_PaPerK', 'Pa/K')), ('seat compensation hold beyond (from ARM)', crow('kPcSeatDevMax_K', 'K')),
    ('seat TC plausible range min', crow('kPcSeatTcMin_K', 'K')), ('seat TC plausible range max', crow('kPcSeatTcMax_K', 'K')),
    ('seat T_cal minimum', crow('kPcSeatTcalMin_K', 'K')), ('seat T_cal default', crow('kPcSeatTcalDefault_K', 'K')),
    ('seat T_cal maximum', crow('kPcSeatTcalMax_K', 'K')),
    ('seat static term at ARM |T_seat - T_cal| (E4-N01: 30 -> 40 K)', crow('kPcSeatArmDevMax_K', 'K')),
    ('light-rule zero drift term', crow('kIgnBaseDrift_Pa', 'Pa')), ('torch re-zero limit (re-base OPEN, 264 (4), E4-N04)', crow('kPtorchRezeroMax_Pa', 'Pa')),
    ('J-FWD indication level (E4-N03: 47.5 bar abs GOVERNS; 47.75 is the lowest raw peak of a Q_JFWD > 60 bar abs case on the binding chain c1_cc1_c400_v6, other chains 47.986 / 48.121 / 48.377: 0.25 bar margin, not a threshold)',
     crow('kJfwdLsRawAbs_Pa', 'Pa', 'DERIVED on SIM (calc/v2p12/jfwd_ls_threshold_v2p12.py); TO-VERIFY with the B-PC-1 chain')),
    ('TC4 step check (every conversion, every state)', crow('kPcSeatStepMax_K', 'K')), ('T_c slew outside the hold', crow('kPcSeatSlew_Kps', 'K/s')),
    ('TC4 rate-check trip |reading - T_c|', crow('kPcSeatRateTrip_K', 'K')), ('light-window hold after E2', crow('kPcSeatHoldPostE2_s', 's')),
    ('catch-up time cap / hold duration (ITEM 2)', crow('kPcSeatCatchCapX', '-')),
    ('A1 pad rule build value (core default; A1 flight build TRUE)', crow('kSeatArmRuleBuild', '-')),
    ('JFWD_LS relight inhibit (264 (7) PROVISIONAL)', crow('kJfwdLsRelightInhibit', '-')),
    ('SEAT_STEP relight inhibit (A5 option; lead to rule)', crow('kSeatStepRelightInhibit', '-')),
]
for nm, val in new_rows:
    L.append(OrderedDict([('limit', nm), ('value', val), ('basis', 'v2.13 (REV-ELEC-4 E4-05 (3), Q2; config.h)'), ('decision', 'v4.2 row (v2.13)')]))
note('/limits_v2p11[+%d rows]' % len(new_rows), 'E4-05 (3) missing rows + the v2.13 constants and flags with tags')

# ---------------------------------------------------------------- E4-02 rule and table (Q3), E4-04 U330 row, E4-05 (8)
r3 = doc['r3_01_c1_drift']
E402 = OrderedDict([
    ('rule', 'The coefficient error |eps| (fit or loaded value against the true slope) must satisfy |eps| <= eps_max(k_meas), k_meas = the B-PC-1 '
             'slope / 0.0248 bar/K, read from the table and interpolated DOWNWARD in k. If |eps| > eps_max(k_meas), the stand relight after a '
             'B1-length burn is planned as REFUSED NOT_VENTED (fail-safe; no relight objective claimed). Replaces "within 5 % at k = 3" '
             '(REV-ELEC-4 E4-02 / Q3; 266 (7))'),
    ('table', [OrderedDict([('k', 1.0), ('eps_max_with_adders_pct', 11.2), ('without_adders_pct', 19.2)]),
               OrderedDict([('k', 1.25), ('eps_max_with_adders_pct', 8.1), ('without_adders_pct', 14.5)]),
               OrderedDict([('k', 1.5), ('eps_max_with_adders_pct', 6.0), ('without_adders_pct', 11.3)]),
               OrderedDict([('k', 2.0), ('eps_max_with_adders_pct', 3.4), ('without_adders_pct', 7.4)]),
               OrderedDict([('k', 2.5), ('eps_max_with_adders_pct', 1.8), ('without_adders_pct', 5.0)]),
               OrderedDict([('k', 3.0), ('eps_max_with_adders_pct', 0.8), ('without_adders_pct', 3.4)])]),
    ('tag', 'DERIVED (REV-ELEC-4 scripts/e4_02_eps_table.py 8cfd6416b913b096, data/e4_02_eps_table.json bc09a12ed3c63351) on Mechanical SIM seat '
            'histories x the DATASHEET typical 0.0248 bar/K; tau 0.25 s and the 0.3 K TC error ASSUMED; adders 0.1012 bar (zero drift 0.05 ASSUMED, '
            'outgassing 0.05 DESIGN, noise 0.0012 DERIVED); T_aw 1500 K ASSUMED'),
    ('re_zero1_note', 're-zero1 does not close at k = 3 with the adders even at eps 0; the NOT_VENTED check against re-zero1 needs eps <= 0.2-8.7 % for k 3-1 (not a second line to count on)'),
    ('A1', 'not affected: A1 re-zero2 closes to 11.5 % at k = 3 with the adders; the 10 % B-PC-1 pass criterion holds for flight (E4-N06: thin, 0.286 vs 0.30 bar)')])
old = r3['stand_relight_after_B1']['v']
assert 'within about 5 % at k = 3' in old
r3['stand_relight_after_B1']['v'] = old.replace('RULE: a stand relight after a B1-length burn needs option (b) with the per-serial coefficient within about 5 % at k = 3 (B-PC-1 row)',
                                                'RULE (E4-02, Q3): a stand relight after a B1-length burn needs option (b) with |eps| <= eps_max(k_meas) of the E4-02 table (e4_02_rule)')
r3['stand_relight_after_B1']['status_v2p13'] = 'SUSPENDED under the 266 (6) carve-out until the v2.13 delta is reviewed (REV-ELEC-5); evidence on v2.13: v2p13_delta.sil'
r3['e4_02_rule'] = E402
r3['A8_U330']['U330_ordering_stand_relight_light_E4_04'] = tv(
    'stand relight light: the U330 low edge falls below the 30 bar abs firmware abort from k = 0.725 at T0 24 C (29.59 bar abs at k = 1, 26.62 at k = 3) and '
    'from k = 1.21 at T0 0 C; under (b) the firmware reads the compensated Pc and U330 the raw path, so on a stand relight the hardware trip can act first. '
    'The SIL S13T stand relights reach a U330 node maximum of 15.73 bar abs [SIM], so no SIL run exercises it; the bench plan row is correct',
    'DERIVED (REV-ELEC-4 E4-04, data/r4_01_c1_drift_v2.json); SIM for the node maximum')
for p_, w in (('/r3_01_c1_drift/stand_relight_after_B1', 'E4-02 rule (5 % sentence removed); SUSPENDED status'), ('/r3_01_c1_drift/e4_02_rule', 'new (Q3 table)'),
              ('/r3_01_c1_drift/A8_U330/U330_ordering_stand_relight_light_E4_04', 'new (E4-04)')): note(p_, w)
for oi in doc['open_issues']:
    if isinstance(oi.get('issue'), str) and 'about 5 % at k = 3' in oi['issue']:
        oi['issue'] = oi['issue'].replace('B-PC-1 must hold the coefficient to about 5 % at k = 3 (safe refusal)',
                                          'B-PC-1 must hold |eps| <= eps_max(k_meas) of the E4-02 table (0.8 % at k = 3 with the adders; beyond it the stand relight is planned REFUSED NOT_VENTED, safe)')
        note('/open_issues/' + oi['id'], 'E4-02 rule in place of 5 %')

# ---------------------------------------------------------------- E4-05 (9) / E4-N05: the stale 73.0 g text
sn = doc['head_end_bleed_provision']['sil_s12']
assert '<= 73.0 g at 2.5 s' in sn['mass_note']
sn['mass_note'] = ('purge mass from the SIL plant (single 1.0 mm equivalent orifice, Cd 0.70 ASSUMED, Dyer flux at the tank state): the SIL nominal 76.38 g '
                   'at 31.85 g/s is an ESTIMATE (the plant flow is 2.5 % above the 31.06 g/s bound) against the FINAL basis DERIVED 71.1-75.8 g (REV-ELEC-4 '
                   'E4-05 (9) / E4-N05); B-BLEED-1 measures the mass (pass <= 76 g)')
note('/head_end_bleed_provision/sil_s12/mass_note', "E4-05 (9): '<= 73.0 g at 2.5 s' -> DERIVED 71.1-75.8 g, SIL 76.38 g ESTIMATE")

# ---------------------------------------------------------------- E4-05 (7): CHANGELOG 264 (1)-(8) folds
sel = doc['sensors']['pressure_transducers']['selection']['v']
assert sel['P_TORCH'] == 'TE M3234-000005-070BG (J901)'
sel['P_TORCH'] = 'Kulite XTL-190SM-2000A (C1 family, proof 206.8 bar abs [DATASHEET]; J901, on the torch body) - 264 (4) option 2 ADOPTED; re-base of kTorchArmZeroMax_Pa / kPtorchRezeroMax_Pa OPEN (E4-N04)'
doc['pc_overrange_fa1']['transducer_datasheet']['kept_070BG'] = ('v4.2 (264 (4)): P_torch moves to the C1-family XTL-190SM-2000A (J901); TE M3234-000005-070BG stays only as '
                                                                  'the B-PC-1 static reference (BOM 199)')
note('/sensors/pressure_transducers/selection/v/P_TORCH', '264 (4) fold: XTL-190SM-2000A, re-base OPEN')
note('/pc_overrange_fa1/transducer_datasheet/kept_070BG', '264 (4) fold')
doc['changelog_folding_v2p13'] = [
    OrderedDict([('item', '264 (1) v2.12 handback received and verified'), ('status', 'FOLDED (information)')]),
    OrderedDict([('item', '264 (2) option (b) ADOPTED; A1 pad rule (coefficient loaded and TC4 valid at ARM)'),
                 ('status', 'IMPLEMENTED v2.13 (EngineEcu::seat_arm_rule, Abort::SEAT_TC 32, refuse::SEAT_TC 18; A1 flight build TRUE = OPEN build item); acceptance sentence replaced by the E4-02 rule (266 (7))'),
                 ('where', 'v2p13_delta.pad_rule_264_2; pad_go_no_go_a1; r3_01_c1_drift.e4_02_rule')]),
    OrderedDict([('item', '264 (3) decision (3) A1 BASE_AMB ADOPTED as built'), ('status', 'evidence re-shown on v2.13 (A8: v2p13_delta.sil.s13t)')]),
    OrderedDict([('item', '264 (4) P_torch -> XTL-190SM-2000A'), ('status', 'FOLDED (sensors, BOM v2.5); re-base OPEN (OI-PTORCH-REBASE, E4-N04)')]),
    OrderedDict([('item', '264 (5) T4 shorter relight'), ('status', 'FOLDED in bench plan v5.1 (T4 = relight-latency demonstration from a soaked state; length from the Combustion T4 re-run; waits for the lift of 266 (6))')]),
    OrderedDict([('item', '264 (6) A1 flight T0 0-40 C ASSUMED design range'), ('status', 'FOLDED (E4-N01: kPcSeatArmDevMax_K 40 K arms T0 0 C with T_cal 35 C); founders confirm the climate')]),
    OrderedDict([('item', '264 (7) JFWD_LS inhibits the A1 relight (PROVISIONAL)'), ('status', 'IMPLEMENTED v2.13 (jfwd_relight_inhibit, refuse::JFWD_USED 17, kJfwdLsRelightInhibit true)')]),
    OrderedDict([('item', '264 (8) REV-ELEC-4'), ('status', 'verdict ACCEPT WITH COMMENTS (266 (4)); v2.13 answers E4-01 .. E4-06; REV-ELEC-5 next')]),
    OrderedDict([('item', '266 (6) carve-out'), ('status', 'IN FORCE in v4.2 (status, pad rows, stand relight)')]),
    OrderedDict([('item', '266 (7) v4.1 promoted; TC4 rename; E4-02 / E4-03 / E4-04 corrections'), ('status', 'FOLDED (this file)')])]
note('/changelog_folding_v2p13', 'new (264 (1)-(8), 266 (6)-(7))')

# ---------------------------------------------------------------- E4-05 (5) / E4-06 (1) / RULING 1 (c): pad go/no-go
pad = doc['pad_go_no_go_a1']
pad['rule'] = ('every item GO before the A1 launch commit; one NO-GO stops the count. The ECU items are SIL evidence (v2.13) until B-ECU-1, B-BLEED-1, '
               'B-TC-1 and B-FC-1 pass on hardware. UNDER THE 266 (6) CARVE-OUT THE A1 PAD IS NO-GO until the v2.13 delta is reviewed (REV-ELEC-5)')
pad['items'].append(OrderedDict([('item', 'seat compensation (264 (2))'),
    ('go', 'the B-PC-1 coefficient is loaded (setPcSeatCoef != 0) and TC4 is valid and in range at ARM: the A1 flight image (seat_arm_rule TRUE) refuses ARM '
           'Abort::SEAT_TC (32) otherwise; on a refused ARM read abort_cause from the log (the only channel for every ARM-refusal cause, LEAD 16:28Z). '
           'NO-GO until the v2.13 delta is reviewed (266 (6))'),
    ('source', 'CHANGELOG 264 (2), 266 (6); ECU v2.13 armChecksOk / startBlock (test_v213 "LEAD 264 (2) A1 pad rule")')]))
pad['items'].append(OrderedDict([('item', 'build bits (RULING 1 (c), LEAD 16:27Z option (2))'),
    ('go', 'EVENT BUILD 0x25 read after power-up AND at the ARM attempt: arg b0 seat_arm_rule = 1 and b1 hbleed_fitted = the A1 build value (1 unless CF-4 clears the bleed: kHbleedFitted, LEAD 2026-10-13); log v13 ovr_flags b7 = 1. '
           'Any other value: NO-GO (an A1 image built with seat_arm_rule FALSE allows a flight ARM without the coefficient: FMEA-A1-SEAT-RULE-BUILD)'),
    ('source', 'LEAD 16:11Z RULING 1 (a)-(e), 16:27Z option (2); ECU v2.13 (test_v213 "EVENT BUILD 0x25")')]))
pad['items'].append(OrderedDict([('item', 'JFWD_LS relight inhibit (264 (7) PROVISIONAL)'),
    ('go', 'the A1 image carries kJfwdLsRelightInhibit TRUE (build constant; no ground input). In flight a flagged first light (f3 JFWD_LS) makes the ECU refuse '
           'PURGE / RELIGHT JFWD_USED (TLM_RELIGHT d6 = 17) and the FC takes the lost-relight outcome of gnc.json v3.2'),
    ('source', 'CHANGELOG 264 (7); ECU v2.13 startBlock (test_v213 "LEAD 264 (7) PROVISIONAL")')]))
pad['bench_plan'] = '06-electronics/staging_v2.13/docs/bench_plan_v5_1.md, A1 pad go/no-go list (v4.2 / v2.13 citations)'
for it in pad['items']:
    if isinstance(it.get('source'), str) and 'combustion.json v2.4b igniter.sequence.v.arm_preconditions' in it['source']:
        it['source'] = it['source'].replace('combustion.json v2.4b igniter.sequence.v.arm_preconditions', 'combustion.json v2.4d igniter.sequence.v.arm_preconditions (path present in v2.4d)')
pad['citation_note_v2p13'] = ('E4-05 (5): item sources name the ECU version that introduced each check (v2.10 / v2.11); every one is present in the v2.13 '
                              'firmware (test_core v2.13 run, v2p13_delta.tests); the rule and the bench plan cite v4.2 / v2.13 / bench plan v5.1')
note('/pad_go_no_go_a1', 'E4-05 (5), E4-06 (1), RULING 1 (c): seat, build-bits and JFWD rows; NO-GO under the carve-out')

# ---------------------------------------------------------------- FMEA rows (Q2, RULING 1 (e))
doc['fmea_rows_a1'].append(OrderedDict([
    ('id', 'FMEA-A1-TC4-READING'),
    ('mode', 'TC4 seat TC (MAX31856 U904, J904, grounded-junction MI type K at the C1 boss) reading error'),
    ('causes', 'spark-coupled interference, a lead short to a colder point, junction debond, open TC, MAX31856 fault'),
    ('local_effect', 'the compensation wrong by coef x dT, i.e. 0.0248-0.0744 bar/K at k 1-3'),
    ('system_effect_without_the_fix', 'false or premature E2 with run-lift flow into an unlit chamber; at A1 k = 3 with >= 30 K the FC release predicate is met '
                                      'at the false E2 and the engine aborts 280 ms later; a lost relight or first start (FLAMEOUT / PC_SENSOR / TORCH_LOST); in RUN '
                                      'a false FLAMEOUT after a true light (+90 K at A1 k = 3: E2 + 58 ms); a Pc bias up to coef x 150 K = 3.7 bar (k = 1), 11.2 bar (k = 3) '
                                      '[SIM reviewer SIL / DERIVED, REV-ELEC-4 Q2]'),
    ('detection', 'MAX31856 fault bits (tc_bore_valid), range 223.15-473.15 K, 150 K from the reference, f3 SEAT_STEP (step 1.5 K per conversion, rate 3 K from T_c)'),
    ('mitigation', 'v2.13: light-window hold (IGNITION entry .. E2 + 0.45 s), step check every conversion in every state, rate check / 5 K/s slew outside the hold, '
                   'catch-up after the hold (ITEM 2), trip = compensation held until the next ARM'),
    ('residual', 'an uncompensated seat drift after a hold or a trip: fail-safe refusals of the v2.11 type (A5 evidence); an error below the step and rate limits '
                 '(< 1.5 K per conversion and a ramp <= 5 K/s) is followed by the compensation: <= coef x 3 K = 0.22 bar at k = 3 outside the hold [DERIVED]; '
                 'inside the hold no TC4 reading moves Pc'),
    ('source', 'REV-ELEC-4 E4-01 / Q2; ECU v2.13; SIL S13F (v2p13_delta.sil.s13f)')]))
doc['fmea_rows_a1'].append(OrderedDict([
    ('id', 'FMEA-A1-SEAT-RULE-BUILD'),
    ('mode', 'A1 image built with seat_arm_rule FALSE (the core default kSeatArmRuleBuild; the A1 HAL must set TRUE)'),
    ('effect', 'flight ARM allowed without the coefficient loaded or with TC4 invalid: the 264 (2) protection is lost (the fallback, which loses the A1 relight at k = 3 [SIM S13T])'),
    ('detection', 'EVENT BUILD 0x25 b0 after power-up and at the ARM attempt, log ovr_flags b7; the pad row "build bits" (NO-GO on 0)'),
    ('mitigation', 'build requirement "A1 flight build: seat_arm_rule TRUE" next to kHbleedFitted (OI-A1-BUILD-SEAT-RULE, owner Electronics; the A1 HAL is not in this tree)'),
    ('residual', 'none beyond the pad procedure being followed'),
    ('source', 'LEAD 16:11Z RULING 1 (e)')]))
note('/fmea_rows_a1', '+ FMEA-A1-TC4-READING (Q2), FMEA-A1-SEAT-RULE-BUILD (RULING 1 (e))')

# ---------------------------------------------------------------- CAN / log additions (RULING 1 (b), SEAT_TC note)
doc['can_interface']['v2p13_additions'] = OrderedDict([
    ('EVENT_BUILD', tv(OrderedDict([('code', '0x25 (0x15 is IGN_WINDOW, in use since v2.8)'), ('arg', 'b0 seat_arm_rule, b1 hbleed_fitted, b2-b15 0'),
                                    ('when', 'once at boot (first step) and at EVERY ARM command received, any state, accepted or refused (Outputs::build_event / build_bits)'),
                                    ('bus_cost', 'one EVENT per occasion x the HAL usual 3 copies 10 ms apart: 3 frames at boot + 3 per ARM attempt'),
                                    ('interface', 'ADDITIVE (no existing layout changes); decoders ignore unknown codes; no in-tree EVENT consumer; GNC to confirm the FC ignores or decodes 0x25 (OI-GNC-EVENT-BUILD)')]),
                       'DESIGN (LEAD 16:27Z option (2), 16:28Z code of record 0x25)')),
    ('SEAT_TC_cause', tv('Abort::SEAT_TC = 32 is an ARM-refusal-only cause: the state stays SAFE, so it never rides an EVENT STATE (5-bit cause field 0-31); it is '
                         'carried in the uint8 log abort_cause, the channel every ARM-refusal cause uses today (no CAN frame carries an ARM-refusal cause). Guard: '
                         'can::encodeStateEvent saturates a cause above 31 to 31 and counts it in can::g_state_cause_overflow (static_assert: SEAT_TC is the only '
                         'cause above the field). A STATE-event cause of 31 means CASE_WARM_STAND only while can::g_state_cause_overflow is 0; the log byte '
                         'abort_cause (uint8) is the authority. The counter is RAM-only (no log / TLM field; no layout change, LEAD 16:28Z)',
                         'DESIGN (LEAD 16:27Z, 16:28Z)'))])
doc['log_v13']['ovr_flags_b7_v2p13'] = 'ovr_flags b7 = ovr::SEAT_RULE_BUILD (EngineEcu::seat_arm_rule; was always 0); layout unchanged, %d B, version %d' % (log_size, log_ver)
note('/can_interface/v2p13_additions', 'EVENT BUILD 0x25 (additive), SEAT_TC 32 note + encoder guard')
note('/log_v13/ovr_flags_b7_v2p13', 'RULING 1 (b) log bit')

# ---------------------------------------------------------------- BOM (E4-05 (6), E4-06 (3)-(4))
if 'bom_v2p5' in P:
    doc['bom']['file'] = 'staging_v2.13/results/bom_v2p5.csv'
    doc['bom']['v2p5'] = OrderedDict([('sha256_16', SHA['bom_v2p5']), ('base', 'results/bom_v2p4.csv eb6e77dcd4610383 (v4.1 bom dict cited v2.3: E4-05 (6))'),
                                      ('changes', ['row 187 relabelled "C1 seat TC (TC4, MAX31856 U904, J904)" (E4-06 (3))',
                                                   'C7 bore-top stand-DAQ TC added as a stand-only row (CHANGELOG l.55; config.h; E4-06 (4))',
                                                   'row 83 (J904) relabelled "type K C1 seat TC (TC4, J904; v2.12 option (b) input)" (E4-05 (6))',
                                                   'P_torch C1-family XTL-190SM-2000A row 267 and its INA333 amplifier row 268 (264 (4)); row 199 TE 070BG qty 2 -> 1 (B-PC-1 reference only), row 225 M3200 mates qty 3 -> 2, row 81 J901 connector to be replaced at schematic v2.6 (NOT drawn)',
                                                   'prices TO-QUOTE, delivered to Sonderborg DK-6400 (all new rows)',
                                                   'seat TC mass 5 g ASSUMED (mass statement)'])])
    note('/bom', 'BOM v2.5')

# ---------------------------------------------------------------- v2.13 delta
def s13(name):
    return jl(P[name]) if name in P else None
sil = OrderedDict()
cmpd = s13('s13t_cmp')
if cmpd:
    sil['s13t'] = OrderedDict([('file', 'results/v2p13/s13t_compare_v2p13.json'), ('sha256_16', SHA['s13t_cmp']),
                               ('builds', OrderedDict((k, OrderedDict([(kk, v[kk]) for kk in ('variant', 'n_runs', 'n_same', 'n_differ', 'n_FALSE_E2', 'outcomes',
                                                                                             'differ_by_location_comp', 'outcome_transitions', 'SEAT_STEP_by_location_comp',
                                                                                             'A1_comp_runs', 'A1_comp_BASE_AMB')]))
                                                       for k, v in cmpd['builds'].items())),
                               ('tag', 'SIM')])
for b in ('false', 'true'):
    d = s13('s13f_' + b)
    if d:
        sil['s13f_bpc1_' + b] = OrderedDict([(k, d[k]) for k in ('n_controls', 'n_controls_without_start', 'n_fault_runs', 'n_FALSE_E2', 'n_E2_before_light',
                                                                  'n_lit_not_RUN', 'n_unlit_not_NO_IGNITION', 'n_other_differs', 'failures', 'pass_rule')])
        sil['s13f_bpc1_' + b]['sha256_16'] = SHA['s13f_' + b]
    d = s13('a5_' + b)
    if d:
        sil['a5_bpc1_' + b] = OrderedDict([(k, d[k]) for k in ('n_runs', 'n_FALSE_E2', 'n_E2_before_light', 'n_lit_RUN', 'n_lit_refused', 'n_lit_abort_or_other',
                                                                 'n_lit_controls_RUN', 'tally')])
        sil['a5_bpc1_' + b]['sha256_16'] = SHA['a5_' + b]
s12c = s13('s12_cmp')
if s12c:
    sil['s12_bpc1_false'] = OrderedDict([(k, s12c[k]) for k in ('n_cases', 'fail', 'failed_cases_v2p13', 'mass_over_limit_cases', 'n_differ', 'differences',
                                                                 'E4_05_9_stale_text_absent', 'mass_note_v2p13')])
    sil['s12_bpc1_false']['file'] = 'results/v2p13/s12_compare_v2p13.json'; sil['s12_bpc1_false']['sha256_16'] = SHA['s12_cmp']
    sil['s12_bpc1_false']['note'] = '[v2.12 record, v2.13]: S12 re-run on v2.13 (standard build) for E4-05 (9) (S12_bleed.json now carries the FINAL mass basis) and as a regression check'
sil['seat_time_axis_variant'] = ('DISCLOSED SIL-only variant (ECU_SIL_TEST_HOOKS, EngineEcu::sil_seat_ts, SimConfig::seat_ts_hook): S13T maps the 0.866 s SIL burn onto the '
                                 'Mechanical burn (stand 21.651 s = 25x, A1 3.541 s = 4.1x), so the stand TC4 node moves 36.5 / 38.9 K/s in SIL time (physical 1.46 / 1.56 K/s). '
                                 'The variant runs the TC4 slew / catch-up bound and the post-E2 hold on the Mechanical axis during the compressed burn only (1 elsewhere). '
                                 'It changes no threshold and is absent from the flight build; the S13T as-is runs are reported beside it')
item2c = item2['cases']
a5rec = OrderedDict([('recommendation', 'PROCEED HELD (kSeatStepRelightInhibit false, as built); the lead rules (OI-SEAT-STEP-RELIGHT)')])
a5s = s13('a5_s13f_sum')
if a5s:
    for b, v in a5s['A5'].items():
        a5rec['sim_' + b] = OrderedDict([(k, v[k]) for k in ('n_runs', 'n_FALSE_E2', 'n_E2_before_light', 'n_lit_RUN', 'n_lit_refused', 'n_lit_abort_or_other',
                                                              'n_lit_controls_RUN', 'tally')])
        a5rec['sim_' + b]['cells'] = v['cells']
    a5rec['stale_compensation_at_relight'] = a5s['A5_stale_compensation_at_relight']
    a5rec['summary_file'] = OrderedDict([('file', 'results/v2p13/a5_s13f_summary_v2p13.json'), ('sha256_16', SHA['a5_s13f_sum'])])
a5rec['why'] = ('SIM (both builds): no FALSE_E2 and no E2 before the plant light with either option. A1 relight: PROCEED keeps the relight where the '
                'stale compensation is small (default build: every k = 1 case and every coast trip at 10.0 s, stale error <= 0.71 bar at k = 3, 12 of 16 '
                'lit relights RUN; B-PC-1-shown build: 10 of 16, the k = 3 s = -1 coast trips at -0.71 bar abort PC_SENSOR because its BASE_AMB bound is '
                '-0.46 bar) and fails safe where it is large (burn-1 trip at k = 3, about 1.0 bar: s = +1 -> TORCH_FAULT; s = -1 -> PC_SENSOR in IGNITION). Mechanism by code reading, '
                'not traced in SIL: TORCH_FAULT because the torch confirmation counts only while the main Pc gauge is below kTorchGateMaxPcG_Pa 1 bar, '
                'so the abort comes at the 0.16 s torch gate before the lift (no main N2O); PC_SENSOR because the A1 BASE_AMB path keeps P0 = 0 and '
                'the E1 -> E2 A7 low edge (P0 - 0.30 bar for 50 ms) trips after the lift, like an early NO_IGNITION. INHIBIT refuses every A1 relight after a SEAT_STEP (refuse 19). Stand relight: both options '
                'refuse (NOT_VENTED 8 is checked before SEAT_STEP 19; the stale error is 0.5-3.8 bar), so the stand outcome does not depend on the option')
a5rec['residual'] = ('with PROCEED the frozen T_c stays frozen to the next ARM, so a stale offset coef x (seat rise since the trip) rides into the relight '
                     'RUN and grows with the relight-burn seat rise: it is not the decaying ITEM 2 error. By code reading the existing gates bound the offset '
                     'that can start the A1 relight: below +1.0 bar (the torch-confirmation gate kTorchGateMaxPcG_Pa) and above -kIgnBaseCheck_Pa = '
                     '-0.76 bar (-0.46 bar in the B-PC-1-shown build: BASE_AMB sets P0 = 0 and the A7 hold low edge trips); SIL A5 agrees (+/-0.71 bar '
                     'ran in the default build, -0.71 bar aborted in the B-PC-1-shown build, +/-1.02 bar aborted in both). It can touch the RUN monitors that read the '
                     'compensated Pc (PC_BAND, the 30 bar firmware over-pressure, FLAMEOUT): s = +1 reads high (a later FLAMEOUT, an earlier over-pressure '
                     'abort), s = -1 reads low (an earlier FLAMEOUT, safe direction). The A1 relight objective is the reason to proceed; INHIBIT is the '
                     'conservative alternative at the cost of every relight after a SEAT_STEP. SIL plant on ASSUMED / Combustion bands: firmware-sequencing '
                     'evidence only')
delta = OrderedDict([
    ('E4_01_hold_and_checks', OrderedDict([
        ('hold', 'T_c frozen from IGNITION entry (the entry-tick compensation is the latched value; entry >= 45 ms before E1 [SIM]) to E2 + kPcSeatHoldPostE2_s, or until IGNITION is left without E2'),
        ('step_check', 'every conversion, every state (inside the hold too): |T_n - T_n-1| > kPcSeatStepMax_K -> SEAT_STEP'),
        ('rate_check', 'outside the hold: T_c slews toward the reading at <= kPcSeatSlew_Kps; |reading - T_c| > kPcSeatRateTrip_K -> SEAT_STEP'),
        ('catch_up_ITEM_2', 'after the hold, if 3 K < g0 <= kPcSeatSlew_Kps x hold duration: the rate trip is replaced, while T_c slews, by a growth trip (gap > lowest gap since the hold end + kPcSeatStepMax_K) and a time cap (gap still > 3 K at kPcSeatCatchCapX x hold duration after the hold end); the normal check resumes at gap <= 3 K; g0 above the bound trips at the hold end; the step check stays on (LEAD 16:27Z ACCEPTED)'),
        ('on_trip', 'T_c holds its last good value, f3 SEAT_STEP (log v13 f3_flags b7) latched until the next ARM'),
        ('constants', OrderedDict((n, crow(n, u)) for n, u in (('kPcSeatStepMax_K', 'K'), ('kPcSeatSlew_Kps', 'K/s'), ('kPcSeatRateTrip_K', 'K'),
                                                                ('kPcSeatHoldPostE2_s', 's'), ('kPcSeatCatchCapX', '-'), ('kPcSeatAvgselMax', '-'), ('kPcSeatConvMax_s', 's')))),
        ('hold_cost_re_derived', tv(item2['hold_cost']['cases'], item2['hold_cost']['tag'], file='results/v2p13/item2_hold_gap.json', sha256_16=SHA['item2'])),
        ('ITEM_2_hold_end_gap', tv(OrderedDict([
            ('longest_legal_hold_s', item2['hold_s']),
            ('A1_relight', OrderedDict([('nominal_E0_g0_K', item2c['A1']['relight_nominal_E0']['g0_K']), ('nominal_margin_vs_3K', item2c['A1']['relight_nominal_E0']['margin_vs_3K']),
                                        ('envelope_g0_K', item2c['A1']['relight_any_time_after_burn1']['g0_K']), ('envelope_margin_vs_3K', item2c['A1']['relight_any_time_after_burn1']['margin_vs_3K']),
                                        ('envelope_max_rate_Kps', item2c['A1']['relight_any_time_after_burn1']['max_rate_0p1s_Kps']),
                                        ('margin_with_catch_up_bound', item2c['A1']['relight_any_time_after_burn1']['margin_catchup_bound_5Kps_x_hold'])])),
            ('stand_relight_GVHI', OrderedDict([('nominal_E0_g0_K', item2c['GVHI']['relight_nominal_E0']['g0_K']), ('envelope_g0_K', item2c['GVHI']['relight_any_time_after_burn1']['g0_K']),
                                                ('envelope_margin_vs_3K', item2c['GVHI']['relight_any_time_after_burn1']['margin_vs_3K']),
                                                ('margin_with_catch_up_bound', item2c['GVHI']['relight_any_time_after_burn1']['margin_catchup_bound_5Kps_x_hold'])])),
            ('stand_relight_GVLO', OrderedDict([('nominal_E0_g0_K', item2c['GVLO']['relight_nominal_E0']['g0_K']), ('envelope_g0_K', item2c['GVLO']['relight_any_time_after_burn1']['g0_K']),
                                                ('envelope_margin_vs_3K', item2c['GVLO']['relight_any_time_after_burn1']['margin_vs_3K']),
                                                ('margin_with_catch_up_bound', item2c['GVLO']['relight_any_time_after_burn1']['margin_catchup_bound_5Kps_x_hold'])])),
            ('first_starts_g0_K', OrderedDict([('A1_pad', item2c['A1']['first_start_nominal']['g0_K']), ('stand', item2c['GVHI']['first_start_nominal']['g0_K'])])),
            ('widest_accepted_g0_compensation_error', 'coef x 5 K/s x hold duration: k = 3, 1.148 s flight-relight hold -> 0.0744 bar/K x 5.74 K = 0.43 bar at the hold end; it decays as T_c closes at (5 - r) K/s: <= 1.6 s at r = 1.383 K/s (A1 envelope), and at most kPcSeatCatchCapX x hold = 2.3 s before a trip; it lands in RUN after E2 + 0.45 s (the relight base and the light rule are latched before E2; it can touch the RUN monitors: PC_BAND, the 30 bar firmware over-pressure and FLAMEOUT read the compensated Pc). A physical seat (<= 2.42 K/s) gives g0 <= 1.59 / 2.06 K = 0.12 / 0.15 bar [DERIVED]; REV-ELEC-5 judges tying the bound to the physical maximum (one constant)')]),
            'DERIVED on SIM (Mechanical seat histories, TC4 node) - results/v2p13/item2_hold_gap.json; preliminary SIM rates from REV-ELEC-4 data/seat_rate_max.json 750d091d7e5ec049'))])),
    ('E4_03', 'both fixes: SAFE entry clears the seat reference / compensation / hold, and the ARM check compares |pc_f_ + pc_zero_ + seat_comp_ - arm_stat| (UT-4: 0 of 8 differ)'),
    ('E4_N01', 'kPcSeatArmDevMax_K 30 -> 40 K (option 2 of the review) with a unit test (T0 0 C / T_cal 35 C arms; +0.6 bar still refused; 40.5 K refused)'),
    ('pad_rule_264_2', OrderedDict([('ecu', 'EngineEcu::seat_arm_rule (core default kSeatArmRuleBuild FALSE; A1 flight build TRUE, the kHbleedFitted pattern, LEAD 16:11Z RULING 1 ACCEPTED)'),
                                    ('flight_ARM', 'refused Abort::SEAT_TC (32) if the coefficient is 0 or TC4 is invalid / out of range'),
                                    ('pad_first_start', 'PREPRESS / IGNITE (starts 0, flight) refused refuse::SEAT_TC (18) with no seat reference (SEAT_NOREF) or SEAT_STEP set'),
                                    ('build_requirement', 'A1 flight build: seat_arm_rule TRUE - OPEN build item, owner Electronics (the A1 HAL is not in this tree): OI-A1-BUILD-SEAT-RULE'),
                                    ('reporting', 'EVENT BUILD 0x25 b0 + log ovr_flags b7 (can_interface.v2p13_additions)')])),
    ('jfwd_inhibit_264_7', 'PURGE / RELIGHT / IGNITE with starts >= 1 in flight refused refuse::JFWD_USED (17) when f3 JFWD_LS is latched (kJfwdLsRelightInhibit true, PROVISIONAL)'),
    ('A5_seat_step_option', 'kSeatStepRelightInhibit (default false = proceed on the held compensation; true = refuse::SEAT_STEP (19)); the lead rules after the A5 evidence (sil.a5_*)'),
    ('A5_recommendation', a5rec),
    ('tests', OrderedDict([('test_core_hooks', '%d passed, %d failed' % (tc_p, tc_f)), ('test_core_nohooks', '%d passed, %d failed' % (tn_p, tn_f)),
                           ('v2p13_units', ut), ('v2p13_other', ut_extra),
                           ('logs', OrderedDict([('hooks', SHA['tc_log']), ('nohooks', SHA['tcn_log'])])),
                           ('disclosures', ['UT-3 measures the step effect over 100 ms and bounds the later residual (the held-compensation residual coef x seat rate x time since the freeze)',
                                            'UT-5 tolerance x 1.001 + 0.5 Pa (float rounding of T_c)',
                                            'v212-1 (a) / (c) stimuli changed from instantaneous jumps to 4 K/s ramps (LEAD ACCEPTED 16:11Z); assertions unchanged'])])),
    ('sil', sil)])
doc['v2p13_delta'] = delta
note('/v2p13_delta', 'new')

# ---------------------------------------------------------------- E4-05 (6) 'pending' statuses and the v4.1 open issues the 264 rulings settle
st = doc['r3_01_c1_drift']['status']
assert 'CLOSED WITH RESIDUAL pending the lead ruling (b) / fallback / decision (3), ' in st
doc['r3_01_c1_drift']['status'] = st.replace('CLOSED WITH RESIDUAL pending the lead ruling (b) / fallback / decision (3), ',
    'CLOSED WITH RESIDUAL: the lead ruled CHANGELOG 264 (2) (option (b) ADOPTED; the fallback is not a flight configuration) and 264 (3) (decision (3), '
    'A1 BASE_AMB ADOPTED as built); the 266 (6) carve-out holds until the v2.13 delta is reviewed (REV-ELEC-5); residual: ')
r301 = doc['rev_elec_3_author_status']['R3-01']
assert '(lead ruling on (b) / fallback / decision (3) pending; B-PC-1, F-10)' in r301
doc['rev_elec_3_author_status']['R3-01'] = r301.replace('(lead ruling on (b) / fallback / decision (3) pending; B-PC-1, F-10)',
    '(lead ruled 264 (2) / 264 (3); 266 (6) carve-out until REV-ELEC-5; B-PC-1, F-10)')
n07 = doc['rev_elec_3_author_status']['N-07']
doc['rev_elec_3_author_status']['N-07'] = n07 + '; v4.2: T4 restated as a relight-latency demonstration from a soaked state (264 (5), bench plan v5.1, E4-06 (2))'
for p_, w in (('/r3_01_c1_drift/status', "E4-05 (6): 'pending' -> the 264 (2) / (3) rulings"), ('/rev_elec_3_author_status/R3-01', 'E4-05 (6)'),
              ('/rev_elec_3_author_status/N-07', 'E4-06 (2)')): note(p_, w)
OI_UPD = {
    'OI-C1-SEAT-DRIFT': 'v4.2: the lead ruled 264 (2) (option (b) ADOPTED, A1 pad rule) and 264 (3); v2.13 adds the light-window hold, the TC4 step / rate checks and the catch-up (E4-01); remaining: REV-ELEC-5 on the v2.13 delta (266 (6) carve-out), the per-serial coefficient and T_cal (B-PC-1, E4-02 rule), F-10, the seat TC mount (Mechanical), P_mid / U570 (MISSING)',
    'OI-PTORCH-PROOF': 'v4.2: CLOSED by 264 (4) option 2 (P_torch on the C1-family XTL-190SM-2000A, proof 206.8 bar abs [DATASHEET] >= 166.14 bar abs; BOM v2.5 rows 267-268); follow-on OI-PTORCH-REBASE (E4-N04)',
    'OI-T4-RESIZE': 'v4.2: 264 (5) adopted the shorter relight (coast not lengthened); bench plan v5.1 restates T4 as a relight-latency demonstration from a soaked state, its length from the Combustion T4 re-run (still OPEN), and T4 waits for the lift of 266 (6) (E4-06 (2))',
    'OI-JFWD-FLIGHT': 'v4.2: 264 (7) PROVISIONAL inhibit IMPLEMENTED in v2.13 (kJfwdLsRelightInhibit true: PURGE / RELIGHT refused JFWD_USED 17 in flight after f3 JFWD_LS; unit test) with a pad row; the final ruling (LEAD 258 (4)) stays OPEN',
}
for oi_ in doc['open_issues']:
    if oi_.get('id') in OI_UPD:
        oi_['status_v2p13'] = OI_UPD[oi_['id']]; note('/open_issues/' + oi_['id'] + '/status_v2p13', '264 rulings / v2.13')
assert sum(1 for oi_ in doc['open_issues'] if 'status_v2p13' in oi_) == len(OI_UPD)
if 'bom_v2p5' in P:
    import csv as _csv
    rows_ = list(_csv.DictReader(open(P['bom_v2p5'], newline='', encoding='utf-8')))
    from collections import Counter as _C
    doc['bom']['summary_note'] = 'summary is the v2.3 record (rows 1-266, unchanged here); v2p4 and v2p5 carry the later changes (E4-05 (6))'
    doc['bom']['v2p5']['rows'] = len(rows_)
    doc['bom']['v2p5']['price_basis_counts'] = OrderedDict(sorted(_C(r['price_basis'] for r in rows_).items()))
    doc['bom']['v2p5']['total'] = 'UNKNOWN: rows are TO-QUOTE (no zero and no from-prices used); delivered prices to Sonderborg, DK-6400 not quoted'

# ---------------------------------------------------------------- open issues with owners (B8)
def oi(id_, sev, issue, owner, closure):
    return OrderedDict([('id', id_), ('severity', sev), ('issue', issue), ('owner', owner), ('closure', closure)])
doc['open_issues'] += [
    oi('OI-REV-ELEC-5', 'HIGH', 'the v2.13 delta is not reviewed: the 266 (6) carve-out stays; A1 flight NO-GO; no stand relight', 'lead (REV-ELEC-5)', 'REV-ELEC-5 verdict + lead lift of 266 (6)'),
    oi('OI-A1-BUILD-SEAT-RULE', 'HIGH', 'A1 flight build requirement: seat_arm_rule TRUE (next to kHbleedFitted); the A1 HAL is not in this tree', 'Electronics', 'HAL-1; pad row "build bits" (EVENT BUILD b0 = 1)'),
    oi('OI-GNC-EVENT-BUILD', 'LOW', 'EVENT 0x25 BUILD is a new code (additive): confirm the FC ignores or decodes it', 'GNC', 'GNC statement against v4.2'),
    oi('OI-SEAT-STEP-RELIGHT', 'MEDIUM', 'A5: SEAT_STEP latched before a relight - proceed on the held compensation (kSeatStepRelightInhibit false) or inhibit', 'lead', 'lead ruling on the A5 evidence (v2p13_delta.sil.a5_*)'),
    oi('OI-TC4-GROUNDED-JUNCTION', 'MEDIUM', 'E4-N10: grounded-junction TC4 on the MAX31856 against DS Note 6 (floating TC, BIAS to T-): common-mode range, open-TC detection, EMI path; TO-VERIFY on the datasheet PDF; option: an insulated-junction TC4', 'Electronics (+ Mechanical for the mount)', 'datasheet read + B-TC-1 TC4 row'),
    oi('OI-MAX31856-TCONV', 'LOW', 'tCONV TYP / MAX columns and the AVGSEL increments TO-VERIFY on the 19-7534 Rev 0 PDF; the bench measures the U904 period', 'Electronics', 'datasheet read + B-TC-1'),
    oi('OI-PTORCH-REBASE', 'MEDIUM', 'E4-N04: with P_torch on the C1-family XTL-190SM-2000A the torch zero shift is 0.32 x k bar (A1) / 1.28 x k bar (stand) at 0.0248 bar/K [DERIVED], above kPtorchRezeroMax_Pa 0.60 bar on the stand for k >= 0.47: the re-base needs compensation or a photodiode-guarded torch gate; the torch local heat is MISSING', 'Electronics (re-base); Combustion / Mechanical (torch local heat)', 'next Electronics round after the torch heat'),
    oi('OI-HB-BACKSTOP-2741', 'MEDIUM', 'E4-N08: the hardware both-open timer U577 allows up to 2.741 s if the firmware cap fails, above Combustion v2.4d "never above" 2.39 s; option RSET 59.0 kOhm (2.475 s nominal, 2.398 s minimum) narrows it', 'Combustion + lead', 'B-BLEED-1 ruling'),
    oi('OI-SIL-MANIFEST-V2', 'LOW', 'E4-N11: SIL MANIFEST_v2 for the full record on v2.13 (Part C): NOT DONE in v2.13 (time box: Part A and B first, brief 15:32Z)', 'Electronics', 'next Electronics round (tools/sil_manifest_v1.py extended to the v2.13 scenarios)'),
    oi('OI-S13T-COMPRESSED-AXIS', 'LOW', 'the S13T compressed SIL burn moves the stand TC4 node 25x faster than physical; the as-is v2.13 stand runs trip SEAT_STEP in burn 1 (artefact); the disclosed seat time-axis variant is the comparison basis; a real-time-burn S13T would remove it', 'Electronics', 'next SIL round'),
]
doc['notes_v2p13'] = OrderedDict([
    ('E4-N06', 'A1 re-zero2 margin at k = 3 is 11.5 % against the 10 % B-PC-1 pass criterion (0.286 vs 0.30 bar with adders) [DERIVED]: holds, thinly'),
    ('E4-N07', 'the compensation is a static linear coefficient; hysteresis, a non-linear zero and diaphragm gradients beyond the modelled sensor-node term (-0.29 to -2.28 K) are not represented; B-PC-1 over 0-85 C with 2 cycles is the only check'),
    ('E4-N09', 'TB-state is conservative (any over-range sample, a nozzle-holder OVER_TEMP): acceptable for a test-bed indication')])
note('/open_issues', '+ %d v2.13 items with owners' % 10)

# ---------------------------------------------------------------- summary, self-check
doc['change_summary_v4p1_to_v4p2'] = changes
cfg_names = ['kPcSeatArmDevMax_K', 'kPcSeatStepMax_K', 'kPcSeatSlew_Kps', 'kPcSeatRateTrip_K', 'kPcSeatHoldPostE2_s', 'kPcSeatCatchCapX', 'kPcSeatAvgselMax',
             'kPcSeatConvMax_s', 'kSeatArmRuleBuild', 'kJfwdLsRelightInhibit', 'kSeatStepRelightInhibit']
doc['config_changes_v4p1_to_v4p2'] = [OrderedDict([('name', n), ('v2p13', cnum(n)), ('tag', cline(n)), ('v2p12', 30.0 if n == 'kPcSeatArmDevMax_K' else 'new')]) for n in cfg_names]
txt = json.dumps(doc)
cur = json.dumps(OrderedDict((k, v) for k, v in doc.items() if k not in ('superseded_v3', 'change_summary_v3_to_v4', 'changelog_folding', 'lead_rulings_v2p11',
                                                                          'change_summary_v4p1_to_v4p2', 'inputs', 'rev_elec_3_author_status', 'rev_elec_2_author_status')))
stale = ['TC4 type K bore top', 'bore-top TC (stand)', 'within about 5 % at k = 3', '<= 73.0 g at 2.5 s', "Combustion's decided-path value"]
doc['self_check_v2p13'] = OrderedDict([('stale_strings_absent_in_current_sections', OrderedDict((s, s not in cur) for s in stale)),
                                       ('log', '%d B v%d' % (log_size, log_ver)), ('EVENT_BUILD_0x25_in_protocol_h', True),
                                       ('tests_pass', tc_f == 0 and tn_f == 0)])
assert all(doc['self_check_v2p13']['stale_strings_absent_in_current_sections'].values()), doc['self_check_v2p13']
open(out_p, 'w').write(json.dumps(doc, indent=1, ensure_ascii=True) + '\n')
print('wrote', out_p, len(open(out_p).read()), 'B;', len(changes), 'changes; tests', tc_p, tc_f, tn_p, tn_f, '; sil keys', list(sil.keys()))
