#!/usr/bin/env python3
"""Electronics v2.13 (2026-10-21): S13T no-fault comparison, v2.13 firmware against the v2.12 record (brief A7 pass item 'the no-fault
S13T outcomes unchanged', A8 '0 BASE_AMB with option (b) over the S13T A1 matrix').

Inputs: the v2.12 record staging_v2.12/results/v2p12/sil/S13T_seat_drift_bpc1_{false,true}.json and the v2.13 runs
S13T_seat_drift_bpc1_{false,true}[_ts].json (as is, and the disclosed SIL-only seat time-axis variant _ts). Compared per case: outcome,
first_abort, refuse_code, rezero1/2, NOT_VENTED, BASE_HIGH, BASE_AMB, U330_trip. Tags: SIM (SIL plant x Mechanical SIM seat history).
Run: python3 -B -I s13t_compare_v2p13.py <v2.12 sil dir> <v2.13 sil dir> <out.json>
"""
import hashlib, json, os, sys
from collections import OrderedDict, Counter

d12, d13, out = sys.argv[1], sys.argv[2], sys.argv[3]
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
KEYS = ['outcome', 'first_abort', 'refuse_code', 'rezero1', 'rezero2', 'NOT_VENTED', 'BASE_HIGH', 'BASE_AMB', 'U330_trip']
res = OrderedDict([('id', 's13t_compare_v2p13'), ('tag', 'SIM (SIL plant, ASSUMED / Combustion bands) x Mechanical SIM seat history'),
                   ('keys_compared', KEYS), ('inputs', OrderedDict()), ('builds', OrderedDict())])
for b in ('false', 'true'):
    p12 = os.path.join(d12, 'S13T_seat_drift_bpc1_%s.json' % b)
    if not os.path.exists(p12): continue
    r12 = json.load(open(p12)); c12 = {c['case']: c for c in r12['cases']}
    res['inputs']['v2.12_bpc1_' + b] = h16(p12)
    for var in ('', '_ts'):
        p13 = os.path.join(d13, 'S13T_seat_drift_bpc1_%s%s.json' % (b, var))
        if not os.path.exists(p13): continue
        r13 = json.load(open(p13)); res['inputs']['v2.13_bpc1_%s%s' % (b, var)] = h16(p13)
        same = diff = 0; dl = []; by_loc = Counter(); trans = Counter(); a1_ba_comp = 0; a1_comp_runs = 0; steps = Counter()
        for c in r13['cases']:
            o = c12.get(c['case'])
            if c['location'] == 'A1_flight' and c['comp'] != 'off':
                a1_comp_runs += 1; a1_ba_comp += 1 if c['BASE_AMB'] else 0
            if c.get('SEAT_STEP'): steps[c['location'] + ' ' + c['comp']] += 1
            if o is None: dl.append({'case': c['case'], 'v2.13': c['outcome'], 'v2.12': None}); diff += 1; continue
            d = [k for k in KEYS if o.get(k) != c.get(k)]
            if d:
                diff += 1; by_loc[c['location'] + ' ' + c['comp']] += 1; trans['%s -> %s' % (o['outcome'], c['outcome'])] += 1
                dl.append(OrderedDict([('case', c['case']), ('keys', d), ('v2.12', {k: o.get(k) for k in d}), ('v2.13', {k: c.get(k) for k in d}),
                                       ('SEAT_STEP', c.get('SEAT_STEP')), ('hold_gap_max_K', c.get('hold_gap_max_K'))]))
            else: same += 1
        oc = Counter(c['outcome'] for c in r13['cases'])
        res['builds']['bpc1_%s%s' % (b, var)] = OrderedDict([
            ('variant', 'SIL-only seat time-axis hook (disclosed)' if var else 'as is'), ('n_runs', len(r13['cases'])), ('n_same', same),
            ('n_differ', diff), ('n_FALSE_E2', r13.get('n_false_E2')), ('outcomes', OrderedDict(sorted(oc.items()))),
            ('differ_by_location_comp', OrderedDict(sorted(by_loc.items()))), ('outcome_transitions', OrderedDict(sorted(trans.items()))),
            ('SEAT_STEP_by_location_comp', OrderedDict(sorted(steps.items()))),
            ('A1_comp_runs', a1_comp_runs), ('A1_comp_BASE_AMB', a1_ba_comp), ('differences', dl)])
json.dump(res, open(out, 'w'), indent=1)
for k, v in res['builds'].items():
    print(k, 'runs', v['n_runs'], 'same', v['n_same'], 'differ', v['n_differ'], 'FALSE_E2', v['n_FALSE_E2'], 'A1 comp BASE_AMB',
          v['A1_comp_BASE_AMB'], '/', v['A1_comp_runs'])
    print('   by loc', dict(v['differ_by_location_comp'])); print('   trans', dict(v['outcome_transitions'])); print('   steps', dict(v['SEAT_STEP_by_location_comp']))
