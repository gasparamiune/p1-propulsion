#!/usr/bin/env python3
"""Electronics v2.13 (2026-10-21): summary of the A5 (SEAT_STEP before a relight: proceed held vs inhibit) and S13F (TC4 fault set)
SIL runs, both builds (bpc1 false / true). Reads <sil dir>/A5_seat_step_relight_bpc1_{false,true}.json and
S13F_tc4_fault_bpc1_{false,true}.json; writes one JSON. Every number is SIM (SIL plant on ASSUMED / Combustion bands x Mechanical SIM
seat history, SIL-only seat time-axis variant, disclosed); firmware-sequencing evidence only, not physical approval.
Run: python3 -B -I a5_s13f_summary_v2p13.py <sil dir> <out.json>
"""
import hashlib, json, os, sys
from collections import OrderedDict, Counter

d, out = sys.argv[1], sys.argv[2]
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
res = OrderedDict([('id', 'a5_s13f_summary_v2p13'), ('tag', 'SIM (SIL plant, ASSUMED / Combustion bands) x Mechanical SIM seat history; '
                   'SIL-only seat time-axis variant (seat_ts_hook) - disclosed; TC4 faults are TEST VALUES'), ('inputs', OrderedDict()),
                   ('A5', OrderedDict()), ('S13F', OrderedDict())])
for b in ('false', 'true'):
    p = os.path.join(d, 'A5_seat_step_relight_bpc1_%s.json' % b)
    if os.path.exists(p):
        r = json.load(open(p)); res['inputs']['A5_bpc1_' + b] = h16(p)
        runs = r['runs']; ctl = {x['case']: x for x in runs if x['fault'] == 'none'}
        cells = OrderedDict()
        for x in runs:
            if x['fault'] == 'none': continue
            loc = x['case'].split('_T0_')[0]; lit = 'lit' if x['case'].endswith('_lit') else 'unlit'
            when = 'burn1' if 'burn1' in x['fault'] else 'coast'
            key = '%s %s %s %s' % (loc, when, x['option'], lit)
            c = cells.setdefault(key, Counter())
            c['n'] += 1; c[x['outcome']] += 1
            if x['outcome'] == 'FALSE_E2': c['FALSE_E2!'] += 1
            # refuse_code = TLM_RELIGHT d6 & 0x3F sampled at the RELIGHT command: a refusal reason only when the outcome is REFUSED (an accepted
            # relight from PURGE reads NOT_COAST 10 there by design)
            if x.get('refuse_code') and x['outcome'] == 'REFUSED': c['refuse_%d' % x['refuse_code']] += 1
            if x.get('first_abort') and x['first_abort'] not in ('NONE', 'none', ''): c['abort_' + x['first_abort']] += 1
            if x.get('SEAT_STEP'): c['SEAT_STEP'] += 1
        res['A5']['bpc1_' + b] = OrderedDict([
            ('n_runs', r['n_runs']), ('n_FALSE_E2', r['n_FALSE_E2']), ('n_E2_before_light', r['n_E2_before_light']),
            ('n_lit_RUN', r['n_lit_RUN']), ('n_lit_refused', r['n_lit_refused']), ('n_lit_abort_or_other', r['n_lit_abort_or_other']),
            ('n_lit_controls_RUN', r['n_lit_controls_RUN']), ('tally', r['tally']),
            ('controls', OrderedDict((k, v['outcome'] + (' SEAT_STEP' if v.get('SEAT_STEP') else '')) for k, v in ctl.items())),
            ('cells', OrderedDict((k, OrderedDict(sorted(v.items()))) for k, v in cells.items()))])
    p = os.path.join(d, 'S13F_tc4_fault_bpc1_%s.json' % b)
    if os.path.exists(p):
        r = json.load(open(p)); res['inputs']['S13F_bpc1_' + b] = h16(p)
        runs = r['runs']; ctl = [x for x in runs if x['fault'] == 'none']; fr = [x for x in runs if x['fault'] != 'none']
        by_fault = OrderedDict()
        for x in fr:
            c = by_fault.setdefault(x['fault'], Counter()); c['n'] += 1; c[x['outcome']] += 1
            if x.get('SEAT_STEP'): c['SEAT_STEP'] += 1
            if not x.get('pass'): c['FAIL'] += 1
        cov = Counter((x['outcome']) for x in ctl)
        res['S13F']['bpc1_' + b] = OrderedDict([
            ('n_controls', r['n_controls']), ('n_controls_without_start', r['n_controls_without_start']), ('n_fault_runs', r['n_fault_runs']),
            ('n_FALSE_E2', r['n_FALSE_E2']), ('n_E2_before_light', r['n_E2_before_light']), ('n_lit_not_RUN', r['n_lit_not_RUN']),
            ('n_unlit_not_NO_IGNITION', r['n_unlit_not_NO_IGNITION']), ('n_other_differs', r['n_other_differs']),
            ('n_failures', len(r['failures'])), ('failures_first_20', r['failures'][:20]),
            ('control_outcomes', OrderedDict(sorted(cov.items()))),
            ('controls_without_start', [x['case'] + ' ' + x['outcome'] for x in ctl if x['outcome'] in ('ARM_REFUSED', 'REFUSED') or x.get('t_E1') is None]),
            ('n_fault_runs_SEAT_STEP', sum(1 for x in fr if x.get('SEAT_STEP'))),
            ('by_fault', OrderedDict((k, OrderedDict(sorted(v.items()))) for k, v in by_fault.items()))])
# stale compensation at the relight after an A5 trip (T_c frozen at the trip): coef x (TC4 node at the relight E0 - at the trip), on the
# Mechanical time axis (SIL burn 0.866 s from the first plant light to the 3.40 s shutdown mapped onto the Mechanical burn; after the
# shutdown 1:1). DERIVED on SIM (Mechanical seat histories dT_sensor_K, Electronics v2.12 results/v2p12/seat_hist); coef k = 1 / 3:
# 0.0248 / 0.0744 bar/K (sim.h seat_c_PaK x k)
import csv
HS = '/home/claude/work/electronics/results/v2p12/seat_hist/'
def hist(fn):
    t, y = [], []
    for r in csv.DictReader(open(HS + fn)): t.append(float(r['t_s'])); y.append(float(r['dT_sensor_K']))
    return t, y
def at(t, y, x):
    if x <= t[0]: return y[0]
    for i in range(1, len(t)):
        if t[i] >= x: return y[i - 1] + (y[i] - y[i - 1]) * (x - t[i - 1]) / (t[i] - t[i - 1])
    return y[-1]
BURN_SIL, T_SD = 0.866, 3.40
stale = OrderedDict([('tag', 'DERIVED on SIM (Mechanical seat histories, TC4 node dT_sensor_K; SIL burn %.3f s mapped onto the Mechanical burn)' % BURN_SIL)])
for nm, fn, msd, rl in (('A1_flight', 'seat_hist_A1_NF2b.csv', 3.541, 22.211), ('stand_after_B1_GVHI', 'seat_hist_B1_R4_GVHI.csv', 21.651, 40.321),
                        ('stand_after_B1_GVLO', 'seat_hist_B1_R4_GVLO.csv', 21.651, 40.321)):
    t, y = hist(fn); row = OrderedDict()
    for lab, ts in (('burn1_2.90s', 2.90), ('coast_10.0s', 10.0)):
        m = 0.001 + (ts - (T_SD - BURN_SIL)) / BURN_SIL * (msd - 0.001) if ts < T_SD else msd + (ts - T_SD)
        dT = at(t, y, rl) - at(t, y, m)
        row[lab] = OrderedDict([('t_mech_trip_s', round(m, 3)), ('t_mech_relight_E0_s', rl), ('dT_K', round(dT, 2)),
                                ('error_k1_bar', round(0.0248 * dT, 3)), ('error_k3_bar', round(0.0744 * dT, 3))])
    stale[nm] = row
res['A5_stale_compensation_at_relight'] = stale
json.dump(res, open(out, 'w'), indent=1)
print('stale', json.dumps(stale))
for b, v in res['A5'].items():
    print('A5', b, 'runs', v['n_runs'], 'FALSE_E2', v['n_FALSE_E2'], 'E2<light', v['n_E2_before_light'], 'lit RUN', v['n_lit_RUN'], 'lit refused',
          v['n_lit_refused'], 'lit abort/other', v['n_lit_abort_or_other'], 'ctl RUN', v['n_lit_controls_RUN'])
    for k, c in v['cells'].items(): print('   ', k, dict(c))
    print('   controls', v['controls'])
for b, v in res['S13F'].items():
    print('S13F', b, 'ctl', v['n_controls'], 'no-start', v['n_controls_without_start'], 'faults', v['n_fault_runs'], 'FALSE_E2', v['n_FALSE_E2'],
          'E2<light', v['n_E2_before_light'], 'lit!RUN', v['n_lit_not_RUN'], 'unlit!NOIGN', v['n_unlit_not_NO_IGNITION'], 'other', v['n_other_differs'],
          'SEAT_STEP', v['n_fault_runs_SEAT_STEP'])
    print('   control outcomes', dict(v['control_outcomes'])); print('   no-start', v['controls_without_start'][:10])
    for f in v['failures_first_20']: print('   FAIL', f)
