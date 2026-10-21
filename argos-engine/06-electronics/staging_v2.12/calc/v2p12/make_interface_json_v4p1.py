#!/usr/bin/env python3
"""Electronics v2.12 (2026-10-21): interfaces/electronics.json v4.1 (STAGED; the hub v4 stays the published file).

Base: the hub electronics.json v4 (asserted: version v4, sha256/16 11f7896ad0d0613b), deep-copied. Every embedded config constant
({v, unit, tag, src 'config.h kName'}) is re-read from the v2.12 headers with the v3 evaluator (calc/make_interface_json_v3.py Cfg) and
the v2.11 refresh (calc/v2p11/make_interface_json_v4.py refresh_cfg / complete_tags); changes are listed. New and changed sections carry
the REV-ELEC-3 R3-01..R3-06 closures, LEAD 253 (7), 256 (2), 257 (2), 258 (2)-(4), 261 (2)-(3), and REV-COMB-4 R4-02 / R4-09 / R4-12 /
R4-13 as routed (combustion.json v2.4d electronics_open_issues_v2p4c.routed_to_electronics_v2p12). Result numbers are read from the
result files named in 'inputs' (sha256/16 recorded), not typed. SIL / CALC / DERIVED only: nothing here is hardware validation.

Run: python3 -B -I make_interface_json_v4p1.py <generated_utc> <out.json>
"""
import copy, hashlib, json, os, re, sys
from collections import OrderedDict, Counter
E = '/home/claude/work/electronics'
H = '/home/claude/work/shared-fallback/engine'
sys.path.insert(0, E + '/calc')
sys.path.insert(0, E + '/calc/v2p11')
import make_interface_json_v3 as G3   # noqa: E402
import make_interface_json_v4 as G4   # noqa: E402  (main() not run)

def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def jl(p): return json.load(open(p), object_pairs_hook=OrderedDict)
def tv(v, tag, **kw):
    d = OrderedDict([('v', v), ('tag', tag)]); d.update(kw); return d

gen_utc, out_p = sys.argv[1], sys.argv[2]
assert re.fullmatch(r'2026-10-21T\d\d:\d\d:\d\dZ', gen_utc), gen_utc
R = E + '/results/v2p12'
S = R + '/sil'
P = OrderedDict([
    ('v4', H + '/interfaces/electronics.json'), ('combustion', H + '/interfaces/combustion.json'), ('gnc', H + '/interfaces/gnc.json'),
    ('mechanical', H + '/interfaces/mechanical.json'), ('changelog', H + '/interfaces/CHANGELOG.md'),
    ('review', H + '/reviews/REVIEW-ELECTRONICS-R3.md'), ('lctb70_v2', H + '/04-fea/v352/lc_tb70_envelope_v2.json'),
    ('lctb70_py', H + '/04-fea/v352/lc_tb70_envelope.py'), ('purge_duration', H + '/02-combustion/data/v2p4/purge_duration_v2p4.json'),
    ('c1_drift', R + '/c1_drift_v2p12.json'), ('jfwd_ls', R + '/jfwd_ls_threshold_v2p12.json'),
    ('s13t_false', S + '/S13T_seat_drift_bpc1_false.json'), ('s13t_true', S + '/S13T_seat_drift_bpc1_true.json'),
    ('s13t_prefix_log', S + '/S13T_prefix_v212a_run_log_bpc1_false.txt'), ('s12', S + '/S12_bleed.json'),
    ('s12_v211', E + '/results/sil_v2p11/S12_bleed.json'),
    ('r4_02', S + '/r4_02_reclass_v2p12.json'), ('a8_s6r', S + '/a8_bandhigh/S6R_in_window_overpressure.json'),
    ('a8_s6c', S + '/a8_bandhigh/S6C_rc_cost.json'), ('tc_log', S + '/test_core_v2p12_log.txt'),
    ('tcn_log', S + '/test_core_nohooks_v2p12_log.txt'), ('binaries', S + '/binaries_v2p12.txt'),
    ('bench_plan_v5', E + '/docs/bench_plan_v5.md'), ('bom_v2p4', E + '/results/bom_v2p4.csv'),
    ('config_h', E + '/firmware/src/core/config.h'), ('protocol_h', E + '/firmware/src/core/protocol.h'),
])
SHA = OrderedDict((k, h16(p)) for k, p in P.items())
EXPECT = {'v4': '11f7896ad0d0613b', 'combustion': '7dbf425c12300658', 'gnc': 'bde317782574cbd9', 'mechanical': '66bc53d88d444679',
          'lctb70_v2': '7ebd2fd63dc878ef', 'lctb70_py': 'd14489808338006b', 'purge_duration': '1ff6bfcd7d2f454c'}
for k, s in EXPECT.items():
    assert SHA[k] == s, (k, SHA[k], s)
v4 = jl(P['v4']); assert v4['version'] == 'v4'
comb = jl(P['combustion']); assert comb['version'] == 'v2.4d'
n_cl = open(P['changelog'], encoding='utf-8').read().count('\n')
C = G3.Cfg(); G4.complete_tags(C)
cfg_changes = []
doc = G4.refresh_cfg(copy.deepcopy(v4), C, cfg_changes)
def cv(name): return C(name)
proto = open(P['protocol_h']).read()
log_size = int(re.search(r'static_assert\(sizeof\(LogRecord\) == (\d+)', proto).group(1))
log_ver = int(re.search(r'kLogVersion = (\d+)', proto).group(1))
assert (log_size, log_ver) == (185, 13), (log_size, log_ver)
cfg1 = open(P['config_h']).readline().strip()
assert 'v2.12' in cfg1, cfg1

# ------------------------------------------------------------------------------------------------ results
def tests(p):
    m = re.search(r'(\d+) passed, (\d+) failed', open(p).read()); return int(m.group(1)), int(m.group(2))
tc, tcn = tests(P['tc_log']), tests(P['tcn_log'])
assert tc[1] == 0 and tcn[1] == 0
assert all(x['misses_Q_above_60_raw_below_level'] == 0 for x in jl(P['jfwd_ls'])['chains'].values())
bins = OrderedDict((l.split()[1].split('/')[-1], l.split()[0][:16]) for l in open(P['binaries']) if l.strip())
drift = jl(P['c1_drift']); jls = jl(P['jfwd_ls'])
def s13(p):
    d = jl(p); c = d['cases']
    def cnt(**f):
        return sum(1 for x in c if all((x[k] == v) if not callable(v) else v(x[k]) for k, v in f.items()))
    out = OrderedDict([('file', 'results/v2p12/sil/' + os.path.basename(p)), ('sha256_16', h16(p)), ('n_runs', d['n_runs']),
                       ('n_false_E2', d['n_false_E2']), ('n_ARM_refused', d['n_ARM_refused']),
                       ('U330_trips', cnt(U330_trip=True)), ('TB_STATE', cnt(TB_STATE=True)), ('JFWD_LS', cnt(JFWD_LS=True))])
    tab = OrderedDict()
    for loc in ('A1_flight', 'stand_after_B1_GVHI', 'stand_after_B1_GVLO'):
        for comp in ('comp', 'comp_under', 'comp_over', 'off'):
            sel = [x for x in c if x['location'] == loc and x['comp'] == comp]
            if not sel: continue
            tab['%s/%s' % (loc, comp)] = OrderedDict(sorted(Counter(x['outcome'] for x in sel).items()))
    out['outcomes'] = tab
    e2 = [x['E2_minus_light_ms'] for x in c if x['outcome'] == 'RUN']
    out['E2_minus_light_ms_RUN'] = [min(e2), max(e2), len(e2)]
    out['U330_node_max_relight_bar_abs_equiv'] = max(x['U330_node_max_relight_bar_abs_equiv'] for x in c if x['U330_node_max_relight_bar_abs_equiv'] is not None)
    out['BASE_AMB_runs'] = sorted(x['case'] for x in c if x['BASE_AMB'])
    out['comp_under_refused'] = sorted(x['case'] for x in c if x['comp'] == 'comp_under' and x['outcome'] != 'RUN')
    out['A1_option_b'] = OrderedDict([('lit_RUN', cnt(location='A1_flight', comp=lambda v: v != 'off', plant_lit=True, outcome='RUN')),
                                      ('lit', cnt(location='A1_flight', comp=lambda v: v != 'off', plant_lit=True)),
                                      ('unlit_NO_IGNITION', cnt(location='A1_flight', comp=lambda v: v != 'off', plant_lit=False, outcome='unlit_NO_IGNITION')),
                                      ('unlit', cnt(location='A1_flight', comp=lambda v: v != 'off', plant_lit=False)),
                                      ('BASE_AMB', cnt(location='A1_flight', comp=lambda v: v != 'off', BASE_AMB=True)),
                                      ('NOT_VENTED', cnt(location='A1_flight', comp=lambda v: v != 'off', NOT_VENTED=True))])
    out['A1_fallback_T0_20C'] = OrderedDict(sorted(Counter((x['k'], x['sign'], x['outcome']) for x in c if x['location'] == 'A1_flight'
                                                            and x['comp'] == 'off' and x['T0_C'] == 20 and x['plant_lit']).items()))
    out['A1_fallback_T0_20C'] = [[k[0], k[1], k[2], n] for k, n in out['A1_fallback_T0_20C'].items()]
    return out
S13F, S13B = s13(P['s13t_false']), s13(P['s13t_true'])
pre = open(P['s13t_prefix_log']).read()
pre_lines = [l for l in pre.splitlines() if l.startswith('S13T ')]
pre_a1 = [l for l in pre_lines if l.startswith('S13T A1_flight')]
pre_st = [l for l in pre_lines if l.startswith('S13T stand')]
assert len(pre_a1) + len(pre_st) == len(pre_lines) == 240, (len(pre_a1), len(pre_st), len(pre_lines))
pre_ref = OrderedDict([
    ('A1_flight', tv('%d of %d runs REFUSED at ARM (ARM sanity 0.5 bar without the static term: T0 0 / 40 C, both comp modes, every run at k >= 1.5 '
                     'and one sign at k = 1.0 - the static term 0.496 bar plus the SIL ARM reading)' % (sum('| REFUSED ' in l for l in pre_a1), len(pre_a1)),
                     'SIM (pre-fix log)')),
    ('stand', tv('%d of %d runs REFUSED: SIL harness error (the A1 tank-state jump was applied to the stand and tripped the S1 MV-seat monitor, '
                 'LOCKOUT 6); fixed in sc_v212.inc (no tank jump on the stand); not a firmware finding' % (sum('| REFUSED ' in l for l in pre_st), len(pre_st)),
                 'SIM (pre-fix log)'))])
s12 = jl(P['s12']); s12o = jl(P['s12_v211'])
s12_rows = OrderedDict()
for x in s12['cases']:
    if x['case'] in ('purge_integrated_nominal', 'purge_prescheduled_nominal', 'cap_test_v1_close_inhibited') or 'cap' in x['case']:
        s12_rows[x['case']] = OrderedDict((k, x.get(k)) for k in ('pass', 'purge_mass_g', 'mass_checked', 'purge_mass_limit_g', 'mass_le_limit',
                                                                   'ecu_purge_flow_ms_DERIVED_from_commands', 'both_valves_cmd_open_s',
                                                                   'bleed_flow_max_g_s', 'first_abort'))
s12_fail = sorted(x['case'] for x in s12['cases'] if not x['pass'])
s12_fail_o = sorted(x['case'] for x in s12o['cases'] if not x['pass'])
assert s12_fail == s12_fail_o and len(s12_fail) == s12['fail'] == 4, (s12_fail, s12_fail_o)
s12_mass_o = {x['case']: x.get('purge_mass_g') for x in s12o['cases']}
r402 = jl(P['r4_02'])
a8r, a8c = jl(P['a8_s6r']), jl(P['a8_s6c'])

# ------------------------------------------------------------------------------------------------ top
doc['version'] = 'v4.1'
doc['date'] = '2026-10-21'
doc['generated_utc'] = gen_utc
doc['status'] = ('DESIGN + SIL + schematic, STAGED for the lead (06-electronics/staging_v2.12/; interfaces/electronics.json v4 stays the '
                 'published file until the lead promotes this one). Firmware v2.12 runs only in SIL (no Teensy HAL): the REV-ELEC-3 R3-01 '
                 'option (b) seat compensation of the C1 Pc reading on the working basis given at 11:25Z (LEAD 261 (3); the lead confirms or '
                 'changes it, the fallback and decision (3) at this handback), the TB-state of the LC-TB70 v2 F4 set with PC_SENSOR HIGH, the '
                 'flight J-FWD indication, the purge FINAL as calibration constants with rule (d), log v13. The ECU v2.5 schematic does NOT show '
                 'the v2.11 / v2.12 board items (schematic v2.6 NOT drawn); no board has been built and nothing here is hardware-validated or '
                 'physical approval. Values carry tags; open items are in open_issues.')
doc['supersedes'] = OrderedDict([('file', 'electronics.json v4 (2026-10-21, firmware v2.11)'), ('sha256_16', SHA['v4']),
                                 ('hub_path', 'interfaces/electronics.json (unchanged by this staging)'),
                                 ('staged_from', '06-electronics/staging_v2.11/'), ('earlier', v4['supersedes'])])
doc['scripts'] = ['06-electronics/calc/v2p12/make_interface_json_v4p1.py (this file; reuses calc/make_interface_json_v3.py Cfg and '
                  'calc/v2p11/make_interface_json_v4.py refresh_cfg)',
                  '06-electronics/calc/v2p12/c1_drift_v2p12.py (R3-01 A1-A5, A7, A8 numbers)',
                  '06-electronics/calc/v2p12/jfwd_ls_threshold_v2p12.py (flight J-FWD indication on the 896 grid)',
                  '06-electronics/calc/v2p12/r4_02_reclass_v2p12.py (R4-02 re-classification with Mechanical inside_v2)',
                  '06-electronics/calc/v2p12/make_bench_plan_v5.py, make_bom_v2p4.py'] + list(v4['scripts'])
doc['inputs'] = OrderedDict([
    ('combustion.json', 'v2.4d %s' % SHA['combustion']), ('gnc.json', 'v3.2 %s' % SHA['gnc']), ('mechanical.json', 'v2.4 %s' % SHA['mechanical']),
    ('lc_tb70_envelope', '04-fea/v352/lc_tb70_envelope_v2.json %s; classifier lc_tb70_envelope.py %s' % (SHA['lctb70_v2'], SHA['lctb70_py'])),
    ('purge_duration', '02-combustion/data/v2p4/purge_duration_v2p4.json %s (R4-13)' % SHA['purge_duration']),
    ('review', 'reviews/REVIEW-ELECTRONICS-R3.md %s (REV-ELEC-3; R3-01..R3-06, N-01..N-10)' % SHA['review']),
    ('changelog', 'interfaces/CHANGELOG.md, %d lines at generation, %s (the brief was written on 260 lines 01c944f5997648da)' % (n_cl, SHA['changelog'])),
    ('firmware', 'v2.12 (config.h line 1 in firmware.v2p12.config_h_line_1); no v2.12 SIL MANIFEST (not run in the time box): binaries and '
                 'test logs in firmware.v2p12'),
    ('files_read_sha256_16', OrderedDict((os.path.relpath(p, E) if p.startswith(E) else os.path.relpath(p, H), SHA[k]) for k, p in P.items())),
])
doc['change_summary_v4_to_v4p1'] = [
    'R3-01 (MAJOR): C1 thermal-zero drift re-derived from the seat rise from ARM (Mechanical SIM, both nodes), k 1-3, both signs, T0 '
    'flight 0-40 C / stand 0-24 C; option (b) seat compensation implemented (firmware + SIL); S13T re-run on the drift model in both builds',
    'v2.12 finding of the S13T pre-run: the ARM sanity check (0.5 bar) refuses ARM at the T0 extremes for k >= 1.5 with the uncompensated '
    'static zero term; option (b) now removes coef x (T_seat - T_cal) at the check (setPcSeatTcal); the fallback keeps the v2.11 check',
    'R3-02: bench plan v5 F-14 with the LC-TB70 v2 rules verbatim, the TB-state set (F4 + PC_SENSOR HIGH, implemented), Q_JFWD per platform; '
    'the v4 S6R jfwd_rule citation corrected',
    'R3-03 / R3-05 / R3-06: bench plan v5 B-TC-1 CJTO trim + EMI mean shift; C1 compensated band (F-6, F-10, BOM 251 in BOM v2.4); F-13 soak',
    'R3-04: verdict_227_5.conditions gains the FC Pc branch and the cold-flow bound; the 640 runs decided by R2 stated',
    'LEAD 256 (2) / 257 (2) / 258 (2): purge FINAL 2.43 s / 2.39 s as calibration constants with rule (d) (d1) (d2); PURGE at E0 - 2.90 s; S12 re-run',
    'LEAD 258 (3)-(4) / REV-COMB-4 R4-02: S6R and N-04 burn-on cases re-classified with inside_v2 (Z3 v2, Q_JFWD); flight J-FWD indication',
    'REV-COMB-4 R4-09 / R4-12 / R4-13 texts; torch re-zero limit on the 070BG basis; kIgnBaseCheck_Pa = residual + drift + 0.1 bar',
    'log v13 (185 B); bench plan v5; BOM v2.4 (rows 205 and 251 text)']
for c in cfg_changes:   # refresh_cfg (written for v3 -> v4) labels the old value 'v3' and the new 'v4': here they are v4 and v4.1
    assert 'v3' in c and 'v4' in c, c
cfg_changes = [OrderedDict([('path', c.get('path')), ('src', c.get('src')), ('v4', c['v3']), ('v4p1', c['v4'])] +
                           [(k, v) for k, v in c.items() if k not in ('path', 'src', 'v3', 'v4')]) for c in cfg_changes]
doc['config_changes_v4_to_v4p1'] = cfg_changes

# ------------------------------------------------------------------------------------------------ rulings
doc['lead_rulings_v2p12'] = OrderedDict([
    ('253_7_i', tv('ride-through = the flight-relight build, fixed RC; recorded with its four conditions', 'LEAD 253 (7)(i)', conditions=[
        OrderedDict([('n', 1), ('condition', 'schematic v2.6 drawn'), ('status', 'OPEN (OI-SCHEMATIC-V2P6)')]),
        OrderedDict([('n', 2), ('condition', 'the R3-01 drift term in the comparator bands'),
                     ('status', 'DONE in SIL / CALC: U330 bands per k, node and ambient (r3_01_c1_drift.A8); S6R / S6C band-high re-check with +4.456 bar (a8)')]),
        OrderedDict([('n', 3), ('condition', 'OI-SEAT-RINGING closed at B-DPC-1 / HIL-TR-1'), ('status', 'OPEN (hardware)')]),
        OrderedDict([('n', 4), ('condition', 'N-04: if REV-COMB-4 finds the 29-33 burn-on peaks physical and Mechanical cannot cover them, re-opened'),
                     ('status', 'R4-02 re-classification against Z3 v2 below (rev_comb_4_items_v2p12.R4-02)')])])),
    ('253_7_ii', tv('purge: PROVISIONAL in 253, FINAL by 256 (2) with (a)-(c), (d) by 257 (2), (d1) / (d2) by 258 (2)', 'LEAD 253 (7)(ii), 256 (2), 257 (2), 258 (2)',
                    implemented='purge_final_v2p12')),
    ('253_7_iii', tv('decision (3), the A1 BASE_AMB outcome, held for the S13 A re-run with the drift model: recommendation in r3_01_c1_drift.decision_3', 'LEAD 253 (7)(iii)')),
    ('253_7_iv', tv('an unprimed or UNKNOWN-line relight with the bleed fitted stays refused for A1 (fail-safe); OI-UNPURGED-RELIGHT open until Combustion models it', 'LEAD 253 (7)(iv)',
                    firmware='unchanged (refuse UNPURGED 16; prep path refused with the bleed fitted)')),
    ('253_7_v', tv('both bleed valves stuck open is an FMEA residual for A1 (104.17 g in the first burn, leak flag 5.05 s after injection [SIM]); the pad BIT stays; the low U570 threshold is not credited as detection', 'LEAD 253 (7)(v)')),
    ('253_7_vi', tv('cite SIL MANIFEST eaa9efc5112a8178 in place of 620b3d566fe0c8b9', 'LEAD 253 (7)(vi)', status='done in v4 (firmware.record); kept')),
    ('256_2', tv('PURGE FINAL: 2.43 s flow with the 2.39 s cap ADOPTED with (a) 2.2 s at 283.15 K stated wherever 1.9 s is quoted, (b) measured '
                 'Cd x A >= 0.91 x the Cd 0.70 value (>= 0.95 x with the FD-01 bound) else re-sized, (c) line unlined', 'LEAD 256 (2)')),
    ('257_2', tv('(d): kPurgeFlow_s and the cap re-set from the measured Cd x A (measured-time form, mdot at 297.15 K), never above 2.43 / 2.39 s', 'LEAD 257 (2)')),
    ('258_2', tv('(d1) upper 95 % bound of the measured Cd x A; (d2) CF-4 shows the 283.15 K need at the re-set flow', 'LEAD 258 (2)')),
    ('258_3_4', tv('Z3 v2 ADOPTED (NOT EVALUATED in flight); J-FWD replace rule on Q_JFWD > 60.0 bar abs, no minimum duration; routed: F4 PC_SENSOR HIGH '
                   'abort, inside_v2 re-classification, Q_JFWD logging', 'LEAD 258 (3)-(4)', implemented='tb_state_v2p12, jfwd_v2p12, rev_comb_4_items_v2p12.R4-02')),
    ('261_2', tv('T4 re-sized to the shortest firing (about 2.0 kg); bench plan v5 T1-T4 rows re-sized inside A = 150 C (N-07)', 'LEAD 261 (2)')),
    ('261_3', tv('working basis: option (b) with the seat TC on the MAX31856 #4 channel and the flagged v2.11 fallback; ruled at the handback', 'LEAD 261 (3)')),
])

# ------------------------------------------------------------------------------------------------ firmware v2.12
doc['firmware']['version'] = 'v2.12'
doc['firmware']['v2p12'] = OrderedDict([
    ('config_h_line_1', cfg1), ('tests', OrderedDict([('test_core', '%d passed, %d failed' % tc), ('test_core_nohooks', '%d passed, %d failed' % tcn),
                                                      ('logs', ['results/v2p12/sil/test_core_v2p12_log.txt %s' % SHA['tc_log'],
                                                                'results/v2p12/sil/test_core_nohooks_v2p12_log.txt %s' % SHA['tcn_log']])])),
    ('binaries_sha256_16', bins), ('binaries_note', 'built with g++ -O2 (Makefile flags) in /dev/shm; not part of a manifest (no v2.12 MANIFEST)'),
    ('changes', [
        'seat compensation (R3-01 option (b)): Pc_comp = Pc_in - coef x (T_seat - T_seat,ARM) before every use; coef per serial (setPcSeatCoef), '
        'T_seat = Inputs::tc_bore_K (TC4, MAX31856 U904); SEAT_NOREF / SEAT_FROZEN fallbacks; U330 not compensated',
        'ARM sanity static term: |gauge - coef x (T_seat - T_cal)| <= kPcArmZeroMax_Pa (T_cal per serial, setPcSeatTcal; v2.11 check when coef 0)',
        'TB-state (f3 b0/b1): HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START, OVER_TEMP, PC_SENSOR HIGH (>= 4.75 V) in any non-SAFE state; '
        'stand: the HIGH over-range aborts PC_SENSOR as before and now sets TB_STATE; flight: TB_STATE latched, no abort',
        'flight J-FWD indication (f3 b5): LIGHT_SPIKE raw >= kJfwdLsRawAbs_Pa 47.5 bar abs or raw >= 4.75 V',
        'torch re-zero limit kPtorchRezeroMax_Pa 0.60 bar (070BG basis; f3 b6 on a rejection)',
        'kIgnBaseCheck_Pa = kIgnResidual_Pa + kIgnBaseDrift_Pa 0.06 bar + 0.10 bar',
        'purge FINAL: kPurgeFlow_s 2.43 s, kHbleedCap_s 2.39 s, both calibration constants (setPurgeCal, SAFE only, rule (d) bounds)',
        'log v13: + seat_comp_hPa, seat_ref_dK, f3_flags (185 B)'])])
doc['log_v13'] = tv('LogRecord v13 = %d bytes at 1 kHz: v12 + int16 seat_comp_hPa (INT16_MIN = compensation off) + int16 seat_ref_dK '
                    '(T_seat,ARM - 273.15 K in 0.1 K; INT16_MIN = no reference) + uint8 f3_flags (b0 TB_STATE, b1 TB_PCS_HIGH, b2 SEAT_COMP, '
                    'b3 SEAT_FROZEN, b4 SEAT_NOREF, b5 JFWD_LS, b6 PT_RZ_REJ, b7 zero); kLogVersion %d' % (log_size, log_ver),
                    'DESIGN protocol.h; test_core "LogRecord v13 is 185 bytes"')
doc['log_v12']['superseded_by'] = 'log_v13 (v2.12)'

# ------------------------------------------------------------------------------------------------ R3-01
dk = drift
doc['r3_01_c1_drift'] = OrderedDict([
    ('status', 'SIL / CALC evidence complete for items 1-8 except P_mid / U570 (MISSING, Mechanical); option (b) implemented on the working '
               'basis; CLOSED WITH RESIDUAL pending the lead ruling (b) / fallback / decision (3), B-PC-1 (per-serial coefficient, T_cal) and '
               'F-10 (thermal-zero maximum)'),
    ('evidence', OrderedDict([('c1_drift', 'results/v2p12/c1_drift_v2p12.json %s' % SHA['c1_drift']),
                              ('S13T_default_build', 'results/v2p12/sil/S13T_seat_drift_bpc1_false.json %s' % SHA['s13t_false']),
                              ('S13T_bpc1_build', 'results/v2p12/sil/S13T_seat_drift_bpc1_true.json %s' % SHA['s13t_true']),
                              ('S13T_pre_run_log', 'results/v2p12/sil/S13T_prefix_v212a_run_log_bpc1_false.txt %s (before the ARM static term)' % SHA['s13t_prefix_log'])])),
    ('A1_k_sweep', dk.get('k_sweep_ASSUMED')), ('A2_seat_rise_vs_ARM_K', dk.get('A2_seat_rise_vs_ARM_K')), ('A2_T0', dk.get('A2_T0')),
    ('A1_A3_uncompensated_by_k', dk.get('A1_A3_uncompensated_by_k')), ('A3_option_b_residual_budget', dk.get('A3_option_b_residual_budget')),
    ('A3_recommendation', tv('option (b): kPcRezeroMax_Pa stays 0.30 bar on the COMPENSATED residual; option (a) (widened limit) would defeat '
                             'OI-12 (the vented check)', 'DERIVED')),
    ('A4_base_check', dk.get('A4_base_check')), ('A7_torch', dk.get('A7_torch')), ('A8_U330', dk.get('A8_U330')),
    ('A5_model', tv('pc_zero_err(t) = s x k x 0.0248 bar/K x ((T0 - T_trim) + f(T0) x dT_seat(t)), dT_seat from Mechanical\'s seat history '
                    'interpolated onto the SIL timeline (burn compressed onto the SIL burn, coast and relight in real time); applied to the C1 '
                    'reading before the ADC and the U330 RC; seat TC model: lag 0.25 s, error +/-0.30 K after 0.70 s (comp_under / comp_over '
                    'with the coefficient -/+10 %); P_mid / U570 at BL-08: MISSING (Mechanical c1seat/torch_port_bl08_v352_v1.json '
                    '20220647d32cbbbc gives the steps)', 'SIM on Mechanical SIM + DATASHEET typical; k ASSUMED')),
    ('A8_fw_thresholds_after_rejected_rezero2', OrderedDict([
        ('v', 'after a REJECTED re-zero2 the ARM zero is kept: the firmware 30 bar abs abort (PC_OVERPRESSURE) and the ride-through T45 rule '
              '(raw > 45 bar abs for kRideT45_s 7 ms -> HARD_START) then see the zero error e since ARM and act at an actual Pc of 30 - e / 45 - e '
              '(s = +1 reads high: earlier; s = -1 reads low: later)'),
        ('e_option_b_budget_bar', OrderedDict((k, OrderedDict([('A1', x['A1_ARM_to_E1_bar']), ('stand', x['stand_B1_ARM_to_E1_bar'])]))
                                              for k, x in dk['A3_option_b_residual_budget']['by_k'].items())),
        ('e_fallback_bar', dk['A4_base_check']['rejected_rezero_uncompensated_ARM_to_E1_bar']),
        ('when', 'fallback: re-zero2 is rejected at EVERY A1 relight (shift 0.32-0.95 bar > 0.30 for k 1-3), so the A1 relight burn runs on the '
                 'ARM zero: at k = 2 the 30 bar abort acts at 29.27-30.73 bar abs and T45 at 44.27-45.73 bar abs, at k = 3 28.90-31.10 / '
                 '43.90-46.10 bar abs (the k = 3 relight is lost anyway, decision_3); on the stand a rejected re-zero ends in the NOT_VENTED '
                 'refusal (no light, S13T). Option (b): re-zero2 accepted at the A1 relight for k 1-3 (e at E1 0.009-0.027 bar; 0.065-0.195 bar '
                 'if it were rejected); on the stand rejected only with a coefficient error near 10 % (budget: k >= 1.5; S13T comp_under: k >= 2 '
                 'GVHI, k = 3 GVLO), and the vent check then refuses'),
        ('U330_ordering', 'U330 is not compensated: with option (b) the firmware reading is right and the U330 low band edge falls below the '
                          '30 bar abort when its shift exceeds 1.077 bar (A8_U330: k 1.227 at A1 T0 40 C, 2.82 at A1 T0 20 C, 1.73 on the '
                          'stand at T0 24 C) - an earlier HW_OVERPRESSURE instead of PC_OVERPRESSURE, both abort'),
        ('tag', 'DERIVED (c1_drift_v2p12.json A3 / A4 numbers); k ASSUMED')])),
    ('A6_S13T', OrderedDict([('default_build', S13F), ('bpc1_build', S13B),
                             ('pre_run_refusals_before_the_v2p12_fixes', pre_ref)])),
    ('stand_relight_after_B1', tv('option (b): RUN (all comp / comp_over runs; comp_under refused NOT_VENTED at k >= 2-3: a coefficient '
                                  '10 % low leaves 0.27-0.40 bar on the 0.30 bar limit); fallback (coefficient 0): REFUSED NOT_VENTED (refuse '
                                  '8) in every run that arms - the uncompensated drift 0.78-4.10 bar exceeds the re-zero limit, both re-zeros '
                                  'are rejected and the stand vent check refuses (safe: no light attempted). RULE: a stand relight after a '
                                  'B1-length burn needs option (b) with the per-serial coefficient within about 5 % at k = 3 (B-PC-1 row)',
                                  'SIM (S13T)')),
    ('decision_3', tv('RECOMMENDATION: keep the A1 BASE_AMB outcome as built (PC_SENSOR abort on the relight, fail-safe, no false E2) and adopt '
                      'option (b): with the compensation BASE_AMB occurs in 0 of the A1 runs (T0 0 / 20 / 40 C, k 1-3, both signs, coefficient '
                      '+/-10 %, TC +/-0.3 K), every lit A1 run reaches RUN with E2 - light 15-19 ms and no unlit run reaches E2 (both builds). '
                      'With the fallback (coefficient 0) at T0 20 C the A1 relight is lost at k = 3 in the default build (TORCH_FAULT on +, '
                      'BASE_AMB -> PC_SENSOR on -) and already at k >= 1.5 on the - sign in the B-PC-1-shown build (base check 0.46 bar against '
                      'the 0.55 bar needed); ARM is refused at T0 0 / 40 C (|T0 - T_cal| = 20 K) for k >= 1.5 and on one sign at k = 1.0 in SIL '
                      '(static term 0.496 bar plus the ARM reading against 0.5 bar). The fallback is acceptable only with k <= 2 (default build) '
                      'or k <= 1 (B-PC-1-shown build) by F-10, and with k x 0.0248 bar/K x |T0 - T_cal| clearly below 0.5 bar at ARM',
                      'SIM (S13T) + DERIVED')),
])

# ------------------------------------------------------------------------------------------------ TB-state, J-FWD, purge
doc['tb_state_v2p12'] = OrderedDict([
    ('set', tv('HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START, OVER_TEMP, PC_SENSOR HIGH (>= 4.75 V = 146.5 bar abs); LOW side not added; '
               'OVER_THRUST information only', 'Mechanical F4 CONFIRMED (mechanical.json v2.4 lc_tb70_envelope_v352.F4_abort_set) + LEAD 258 (4)')),
    ('firmware', tv('f3 TB_STATE latched from the cause in any non-SAFE state until the next ARM; TB_PCS_HIGH for the HIGH cause; stand: the '
                    'HIGH over-range aborts PC_SENSOR (5 ms persistence); flight: latched, no abort (the non-sticky over-range bit, log ovr_flags b0)',
                    'DESIGN engine_ecu.cpp tbMark; test_core v212-2')),
    ('founder_rule', 'bench plan v5 F-14 (LEAD 248): after a TB-state abort or a case-TC abort the J-FWD joint counts as used')])
doc['jfwd_v2p12'] = OrderedDict([
    ('rule', tv('Q_JFWD = max(head peak, max S(T) at T 0.2-0.5 ms on the light and excursion windows) > 60.0 bar abs at any time, no minimum '
                'duration -> line-231 J-FWD inspection and TC-02 taps gauged', 'LEAD 258 (3); mechanical.json v2.4 jfwd_replace_rule_v2')),
    ('SIL', 'inside_v2 on the plant head pressure at 25 us (exact): calc/v2p12/r4_02_reclass_v2p12.py'),
    ('stand', 'B-DPC-1 DC-restored with C1, step <= 0.05 ms, after a no-event noise record (TO-VERIFY): bench plan v5 F-14 / B-DPC-1'),
    ('flight', tv('C1 LIGHT_SPIKE raw >= %.1f bar abs -> f3 JFWD_LS: on the 896 grid 0 misses of the Q_JFWD > 60 cases on each C1 chain; '
                  'lowest raw peak of a Q > 60 case per chain %s; flags of the Q <= 60 cases %s; ideal sampler 40.381 bar abs (information); '
                  'Z3 v2 NOT EVALUATED in flight' % (cv('kJfwdLsRawAbs_Pa')['v'] / 1e5,
                                                    json.dumps(OrderedDict((k, x['min_raw_over_Q_above_60_bar_abs']) for k, x in jls['chains'].items())),
                                                    json.dumps(OrderedDict((k, '%d of %d' % (x['flags_Q_le_60_raw_at_or_above_level'], x['n_Q_le_60']))
                                                                           for k, x in jls['chains'].items()))),
                  'DERIVED (results/v2p12/jfwd_ls_threshold_v2p12.json %s); TO-VERIFY on hardware' % SHA['jfwd_ls']))])
doc['purge_final_v2p12'] = OrderedDict([
    ('kPurgeFlow_s', cv('kPurgeFlow_s')), ('kHbleedCap_s', cv('kHbleedCap_s')), ('kPurgeRelight_s', cv('kPurgeRelight_s')),
    ('calibration', tv('both constants are calibration values: the config values are the DEFAULTS and the MAXIMA; EngineEcu::setPurgeCal(flow, cap) '
                       'in SAFE only, 1.0 s <= flow <= 2.43 s, cap <= 2.39 s, flow + t_o - t_c + 2 ticks < cap', 'DESIGN; test_core v212-3')),
    ('rule_d', tv('after CF-4 / B-BLEED-1: cap <= 76 g / mdot(297.15 K) - (t_close - t_open) with mdot from (d1) the upper 95 % bound of the '
                  'measured N2O Cd x A; flow <= cap + t_close - t_open - 2 ticks; never above 2.43 / 2.39 s; (d2) CF-4 shows the 283.15 K need at '
                  'the re-set flow; 2.397 s at the defaults', 'LEAD 257 (2), 258 (2); config.h')),
    ('purge_command_time', tv('PURGE at E0 - 2.90 s; flow start PURGE + 0.42 s; flow end E0 - 0.05 s; scheduled both-open command span 2.38 s', 'DERIVED config.h')),
    ('vented_mass_DERIVED', tv('scheduled 2.43 s: 71.1 g at 29.25 g/s (289.5 K), 75.5 g at 31.06 g/s (297.15 K); at the cap (flow 2.44 s) 71.4 / 75.8 g', 'DERIVED')),
    ('need', tv('1.9 s at 289.5 K AND 2.2 s at 283.15 K (LEAD 256 (2)(a)); 1.8 s at 297.15 K', 'Combustion purge_duration_v2p4.json %s (R4-13)' % SHA['purge_duration'])),
    ('S12', OrderedDict([('file', 'results/v2p12/sil/S12_bleed.json %s' % SHA['s12']), ('fail', s12.get('fail')),
                         ('fail_cases', s12_fail),
                         ('fail_disposition', 'the same 4 cases as v2.11 (results/sil_v2p11/S12_bleed.json %s): sil_fail_dispositions "S12 '
                                              'stuck_open_after_lift d0.6/0.8/1.0 mm stand, stuck_open_first_burn d1.0 mm", OPEN (OI-BLEED-DETECT, '
                                              'LEAD 203 (4)); the first-burn case is the LEAD 253 (7)(v) FMEA residual; no new fail' % SHA['s12_v211']),
                         ('mass_over_limit_cases', s12.get('mass_over_limit_cases')),
                         ('mass_over_limit_cases_v2p11', s12o.get('mass_over_limit_cases')),
                         ('nominal_purge_mass_g_v2p11_to_v2p12', [s12_mass_o.get('purge_integrated_nominal'),
                                                                  s12_rows['purge_integrated_nominal']['purge_mass_g']]),
                         ('rows', s12_rows),
                         ('note', 'SIL plant mass is an ESTIMATE on its own bleed flow (single 1.0 mm equivalent orifice, Cd 0.70, Dyer flux at the '
                                  'SIL tank state: 31.85 g/s, 2.5 % above the 31.06 g/s bound, hence 76.38 g nominal against 75.5 g DERIVED), not '
                                  'the 29.25 / 31.06 g/s Combustion basis the decision uses; EVIDENCE cases are not mass-checked (mass_checked '
                                  'false); B-BLEED-1 measures')])),
    ('hardware_timer', tv('T_hw,min 2.577 s >= cap + 1 tick 2.391 s; option RSET 59.0 kOhm -> 2.475 s nominal / 2.398 s minimum, NOT applied', 'DERIVED (DATASHEET LTC6993 AS RECALLED, TO-VERIFY)'))])

# ------------------------------------------------------------------------------------------------ REV-COMB-4 items
doc['rev_comb_4_items_v2p12'] = OrderedDict([
    ('R4-09', tv('Pc-port face bound 130.2 / 131.3 / 130.5 bar abs over c 181-1200 m/s (CC-1 6 mm3 / CC-1 20 mm3 / CC-2): C1 over-range '
                 'margin to the 137.9 bar abs FS >= 6.6 bar at c >= 181 m/s (not about 16 bar); 15.2 bar to the 4.75 V level 146.5 bar abs',
                 'DERIVED on Combustion v2.4c SIM')),
    ('R4-12', tv('P_torch (TE M3234-000005-070BG on J901) sees the FA-1 passage pressure, design case FA1S 151.04 bar abs = 150.03 bar g: the '
                 '070BG proof 140 bar g = 141.0 bar abs [DATASHEET, bench plan F-12] is BELOW the required 1.1 x FA1S = 166.14 bar abs: NOT MET. '
                 'Saturation level and recovery after over-range: MISSING in the datasheet (F-7 (a)-(c), F-12 measure them on the spare). '
                 'Options for the lead: (1) isolate the 070BG from the passage during the light (a snubber or orifice: changes the torch gate '
                 'reading, TO-DESIGN with Combustion / Mechanical); (2) move P_torch to a C1-family XTL-190SM-2000A (proof 206.8 bar abs '
                 '[DATASHEET] >= 166.14; output saturates at the INA333 rail above 146.5 bar abs; recovery TO-VERIFY at B-PC-1), which re-bases '
                 'kTorchArmZeroMax_Pa and kPtorchRezeroMax_Pa on the C1 zero (not done here)', 'DATASHEET + DERIVED; OPEN (OI-PTORCH-PROOF)')),
    ('R4-13', tv('config.h now cites purge_duration_v2p4.json 1ff6bfcd7d2f454c (1.9 s at 289.5 K on 2 x 0.707 mm, 2.2 s at 283.15 K); 256 (2)(a) '
                 'applied wherever 1.9 s is quoted (config.h kPurgeFlowMin_s, bench plan v5, this file)', 'DONE (source text)')),
    ('R4-02', OrderedDict([('file', 'results/v2p12/sil/r4_02_reclass_v2p12.json %s' % SHA['r4_02']),
                           ('S6R_summary', r402.get('S6R_summary')), ('N04_summary', r402.get('N04_summary')),
                           ('S6R_runs', [OrderedDict((k, x.get(k)) for k in ('run', 'inside', 'zone_max', 'peak_bar_abs', 'S_max_0p02_50ms_bar_abs',
                                                                             'S_max_at_T_ms', 'Q_JFWD_bar_abs', 'jfwd_rule_triggered', 'reasons'))
                                         for x in r402.get('S6R', [])]),
                           ('tag', r402.get('tag')), ('flight', r402.get('flight'))])),
    ('A8_band_high_recheck', OrderedDict([('S6R', 'results/v2p12/sil/a8_bandhigh/S6R_in_window_overpressure.json %s: required %s / passed %s, '
                                                  'ECU runs outside the envelope %s' % (SHA['a8_s6r'], a8r.get('required_cases'), a8r.get('required_passed'),
                                                                                        a8r.get('runs_outside_envelope_ecu'))),
                                          ('S6C', 'results/v2p12/sil/a8_bandhigh/S6C_rc_cost.json %s: %d cases, causes %s' % (
                                              SHA['a8_s6c'], len(a8c['cases']), json.dumps(Counter(x.get('cause') for x in a8c['cases'])))),
                                          ('basis', 'band high + 4.456 bar (k = 3 stand relight light at T0 24 C, the largest drift term of A8); '
                                                    'v1 classifier labels in these files (the S6R JSON keeps the v2.11 LC-TB70 v1 inside()); Z3 v2 is R4-02')])),
])

# ------------------------------------------------------------------------------------------------ R3 corrections in place
rt = doc['ride_through']['S6R_in_window_overpressure']['jfwd_rule']
rt['v_v4'] = rt['v']
rt['v'] = ('v4.1 (REV-ELEC-3 R3-02): the v4 text cited "bench plan v4 F-14" for a 60 bar rule F-14 did not hold. The LC-TB70 v1 60 bar rule '
           '(any head excursion above 60.0 bar abs: replace the J-FWD screws, gauge the TC-01 holes / TC-02 taps) was triggered in 25 required '
           'S6R runs (FA-1 envelope + 50 bar plateau family, zone 3, peak 75.52 bar abs); it is now the LC-TB70 v2 J-FWD replace rule on '
           'Q_JFWD > 60.0 bar abs (LEAD 258 (3)), quoted verbatim in bench plan v5 F-14 with the founder rule (LEAD 248) beside it; the S6R '
           'runs are re-classified with Q_JFWD in rev_comb_4_items_v2p12.R4-02')
rt['tag'] = 'SIM + LEAD 248, 258 (3); corrected v4.1'
vd = doc['drogue_release_support']['r2v2_sweep']['verdict_227_5']
vd['conditions'] = list(vd['conditions']) + [
    'R3-04 (1): the FC Pc branch OFF, or its threshold moved with margin: with the branch on (release on Pc valid and filtered Pc >= 3.0 bar abs) '
    'every normal-family run is released at E2 (0 ms after E2), at both windows, 1000 of 1000, the dead kind included (OI-FC-PC-BRANCH)',
    'R3-04 (2): the cold-flow bound, basis the Combustion v2.4a adiabatic bound (cold_flow_thrust_v2p4a): at cold flow x 1.3 the hold + flush '
    'margins fall from +5.789 / +4.954 N to +2.077 / +1.242 N and the FC iid noise budget for P <= 1e-3 to 1.10 / 0.63 N rms at 0.5 / 0.8 s '
    '(3.06 / 2.51 N at x 1.0)']
vd['decided_by_R2_runs'] = tv('640 of the 2000 runs per window are decided by R2; in 1360 the ECU leaves RUN (FLAMEOUT) before any R2 decision',
                              'SIM (S17v2, REV-ELEC-3 R3-04 (3))')
doc['rev_elec_3_author_status'] = OrderedDict([
    ('R3-01', 'CLOSED WITH RESIDUAL: r3_01_c1_drift (lead ruling on (b) / fallback / decision (3) pending; B-PC-1, F-10)'),
    ('R3-02', 'CLOSED: bench plan v5 F-14 (verbatim rules, TB-state set, Q_JFWD signals); TB-state implemented; citation corrected (ride_through.S6R_in_window_overpressure.jfwd_rule)'),
    ('R3-03', 'CLOSED: bench plan v5 B-TC-1 CJTO trim step (or the untrimmed formula) and EMI mean-shift pass'),
    ('R3-04', 'CLOSED: verdict_227_5.conditions + decided_by_R2_runs'),
    ('R3-05', 'CLOSED: 100 F band 0-55.6 C ordered, 0-85 C and the thermal-zero maximum asked (F-6, F-10, BOM v2.4 row 251); B-PC-1 zero-TC row per serial over 0-85 C'),
    ('R3-06', 'CLOSED: F-13 soak (TC1 / TC2 within 1 K of the facility thermometer for 30 min) and the +/-0.5 K thermometer'),
    ('N-01', 'bench plan v5 B-MV-1 row (post-abort closure with the pintle on the ARM bus, with HIL-TR-1)'),
    ('N-02', 'label: S6R input_peak_bar_abs = the profile head pressure at the abort (or at the run end), NOT the profile target (slow ramps abort '
             'before it: 36.41 / 18.71 bar against 60); SIL field name unchanged'),
    ('N-04', 'R4-02 re-classification'), ('N-07', 'bench plan v5 T1-T4 rows re-sized inside A = 150 C (open conflict on the T4 coast: OI-T4-RESIZE)'),
    ('N-09', 'config.h comments corrected (R2 hold, 070BG re-zero basis, P_mid chain, closure-confirmation signal, U576-U579; also the ARM limit FS basis and the flow-start 0.42 s); OI-STALE-LABELS CLOSED'),
])

# ------------------------------------------------------------------------------------------------ bench plan, BOM, open issues
doc['bench_plan'] = OrderedDict([('file', '06-electronics/docs/bench_plan_v5.md %s' % SHA['bench_plan_v5']),
                                 ('generator', '06-electronics/calc/v2p12/make_bench_plan_v5.py (from bench_plan_v4.md 5b1c9336d7b8db50)'),
                                 ('v4', v4['bench_plan'])])
doc['bom']['v2p4'] = OrderedDict([('file', '06-electronics/results/bom_v2p4.csv %s' % SHA['bom_v2p4']),
                                  ('change', 'rows 205 (TC4 becomes the C1 seat TC, flight use defined) and 251 (compensated band, R3-05) text only; '
                                             '266 rows, line numbers kept; no price entered (TO-QUOTE delivered to Soenderborg, DK-6400)')])
oi = doc['open_issues']
def oi_get(i): return next(o for o in oi if o['id'] == i)
o = oi_get('OI-PURGE-CAP'); o['issue_v4'] = o['issue']; o['severity'] = 'CLOSED (LEAD 256 (2), 257 (2), 258 (2))'
o['issue'] = 'FINAL: 2.43 s flow / 2.39 s cap as calibration constants, rule (d) (d1) (d2) (purge_final_v2p12); residual: CF-4 / B-BLEED-1 re-set'
o = oi_get('OI-A1-BASE-AMB'); o['issue_v4'] = o['issue']
o['issue'] = ('S13T with the drift model: option (b) 0 BASE_AMB in the A1 sweep (both builds); fallback BASE_AMB -> PC_SENSOR at k = 3 '
              '(default build) and at k >= 1.5 on the - sign (B-PC-1-shown build) (r3_01_c1_drift.decision_3); LEAD decision (3) at this handback')
o = oi_get('OI-STALE-LABELS'); o['issue_v4'] = o['issue']; o['severity'] = 'CLOSED (N-09, v2.12)'
o['issue'] = 'config.h comments corrected in v2.12 (rev_elec_3_author_status.N-09)'
oi += [
    OrderedDict([('id', 'OI-C1-SEAT-DRIFT'), ('severity', 'HIGH'), ('owner', 'LEAD (ruling) / Electronics / founders (B-PC-1, F-10) / Mechanical (seat TC mount)'),
                 ('issue', 'R3-01: option (b) implemented in SIL; needs the lead ruling, the per-serial coefficient and T_cal (B-PC-1 over 0-85 C), '
                           'the thermal-zero maximum (F-10), the seat TC mounting at the C1 boss and the P_mid / U570 temperature (MISSING)'),
                 ('closure', 'lead ruling; B-PC-1 zero-TC row; F-10 answer')]),
    OrderedDict([('id', 'OI-STAND-RELIGHT-COEF'), ('severity', 'MEDIUM'), ('owner', 'Electronics / founders'),
                 ('issue', 'S13T: a stand relight after a B1-length burn is refused NOT_VENTED when the seat coefficient is 10 % low at k >= 2 '
                           '(0.27-0.40 bar residual on the 0.30 bar limit): B-PC-1 must hold the coefficient to about 5 % at k = 3 (safe refusal)'),
                 ('closure', 'B-PC-1 per-serial residual over the 50.4 K span')]),
    OrderedDict([('id', 'OI-PTORCH-PROOF'), ('severity', 'HIGH'), ('owner', 'LEAD / Electronics / Combustion / Mechanical'),
                 ('issue', 'R4-12: 070BG proof 141.0 bar abs < 166.14 bar abs required at FA1S; isolate or move P_torch to a C1-family unit (rev_comb_4_items_v2p12.R4-12)'),
                 ('closure', 'lead choice; F-7 / F-12 data')]),
    OrderedDict([('id', 'OI-T4-RESIZE'), ('severity', 'MEDIUM'), ('owner', 'Combustion / Mechanical / LEAD'),
                 ('issue', 'N-07: at the B1 end-of-burn rate the re-sized T4 relight (4.59 s) needs the case TCs <= 112.7 C at the relight; '
                           'the B1 p99 burn ends at about 137.8 C; a coast longer than about 19 s or a shorter relight (bench plan v5 T1-T4)'),
                 ('closure', 'Combustion re-run of the T4 rows on the re-sized profile; Mechanical soak-back')]),
    OrderedDict([('id', 'OI-JFWD-FLIGHT'), ('severity', 'MEDIUM'), ('owner', 'LEAD'),
                 ('issue', 'a flagged first light (f3 JFWD_LS) leaves the relight on a used joint; line 231 covers one Z3 event per assembly (LEAD 258 (4) OPEN)'),
                 ('closure', 'lead ruling before flight acceptance')]),
]
sc = doc['self_check']
sc['firmware_version'] = 'v2.12 (config.h line 1)'
sc['log'] = 'protocol.h: LogRecord %d bytes, kLogVersion %d (asserted 185 / 13)' % (log_size, log_ver)
sc['tests_v2p12'] = 'test_core %d / %d, no-hooks %d / %d (passed / failed)' % (tc + tcn)
sc['sil_manifest'] = 'v2.11 manifest eaa9efc5112a8178 describes v2.11; no v2.12 manifest (NOT DONE in the time box)'
sc['config_changes_listed'] = len(cfg_changes)
json.dump(doc, open(out_p, 'w'), indent=1, ensure_ascii=False)
open(out_p, 'a').write('\n')
print('written', out_p, h16(out_p), 'config changes', len(cfg_changes), 'open issues', len(oi))
