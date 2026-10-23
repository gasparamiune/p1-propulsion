#!/usr/bin/env python3
"""Electronics v2.13 (2026-10-21): S12 (head-end bleed provision) v2.13 standard build against the v2.12 record, and the E4-05 (9) mass_note
check. Inputs: staging_v2.12 results/v2p12/sil/S12_bleed.json and the v2.13 S12_bleed_bpc1_false.json. Tag: SIM (SIL plant ESTIMATES on
ASSUMED valve, Cd and P_mid parameters). Run: python3 -B -I s12_compare_v2p13.py <v2.12 S12_bleed.json> <v2.13 S12_bleed.json> <out.json>
"""
import hashlib, json, sys
from collections import OrderedDict
a_p, b_p, out = sys.argv[1:4]
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
a = json.load(open(a_p), object_pairs_hook=OrderedDict); b = json.load(open(b_p), object_pairs_hook=OrderedDict)
ca = OrderedDict((c['case'], c) for c in a['cases']); cb = OrderedDict((c['case'], c) for c in b['cases'])
KEYS = ['first_abort', 'bleed_fault_flag', 'pass', 'purge_mass_g', 'mass_le_limit', 'E0_s', 'RUN_s']
diff = []
for k, y in cb.items():
    x = ca.get(k)
    if x is None: diff.append({'case': k, 'v2.12': None}); continue
    d = [kk for kk in KEYS if x.get(kk) != y.get(kk)]
    if d: diff.append(OrderedDict([('case', k), ('keys', d), ('v2.12', {kk: x.get(kk) for kk in d}), ('v2.13', {kk: y.get(kk) for kk in d})]))
res = OrderedDict([('id', 's12_compare_v2p13'), ('tag', 'SIM (SIL plant ESTIMATES on ASSUMED valve, Cd and P_mid parameters)'),
                   ('inputs', OrderedDict([('v2.12', h16(a_p)), ('v2.13', h16(b_p))])), ('keys_compared', KEYS),
                   ('n_cases', [len(ca), len(cb)]), ('fail', [a.get('fail'), b.get('fail')]),
                   ('failed_cases_v2p13', [c['case'] for c in b['cases'] if not c.get('pass')]),
                   ('mass_over_limit_cases', [a.get('mass_over_limit_cases'), b.get('mass_over_limit_cases')]),
                   ('n_differ', len(diff)), ('differences', diff),
                   ('mass_note_v2p13', b.get('mass_note')),
                   ('E4_05_9_stale_text_absent', '73.0 g' not in json.dumps(b) and "decided-path value" not in json.dumps(b))])
json.dump(res, open(out, 'w'), indent=1)
print('S12 cases', res['n_cases'], 'fail', res['fail'], 'differ', len(diff), 'mass>limit', res['mass_over_limit_cases'], 'stale absent', res['E4_05_9_stale_text_absent'])
print('failed v2.13', res['failed_cases_v2p13'])
for d in diff[:10]: print('  ', json.dumps(d)[:300])
