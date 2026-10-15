#!/usr/bin/env python3
"""gnc.json v3 -> v3.1 check of the keys the firmware generators read (Electronics, 2026-10-13, firmware v2.10).

Question: the lead published interfaces/gnc.json v3.1 (CHANGELOG line 192, 4f3209323b0e0ed4) after the v2.10 SIL record. The
generated headers sil/gnc_tables.h and src/core/engine_params.h name gnc.json v3 (3e97c378cfebee95, archived by the lead at
01-systems-gnc/superseded/gnc_v3_3e97c378cfebee95.json). Does v3.1 change any leaf under the subtrees tools/gen_tables.py reads
(requirements, flight_software) or the relight planning keys make_interface_json_v3.py reads?

Method: flatten both files under those subtrees and compare leaf by leaf (paths containing 'superseded' are reported apart).
gen_tables.py itself cannot be re-run (it fails on combustion.json v2.4a, OI-GEN-TABLES), so this compares inputs, not headers.
Output: results/gnc_v31_read_keys_check_v2p10.json. Tag: DERIVED (file comparison; no physical meaning).
"""
import argparse, datetime, hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'results')
SUBTREES = ['requirements', 'flight_software']


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def flat(o, p, out):
    if isinstance(o, dict):
        for k, v in o.items():
            flat(v, p + '.' + k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            flat(v, p + '[%d]' % i, out)
    else:
        out[p] = o


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--out', default=os.path.join(RES, 'gnc_v31_read_keys_check_v2p10.json'))
    a = ap.parse_args()
    f_old = os.path.join(a.engine_root, '01-systems-gnc', 'superseded', 'gnc_v3_3e97c378cfebee95.json')
    f_new = os.path.join(a.engine_root, 'interfaces', 'gnc.json')
    A, B = json.load(open(f_old)), json.load(open(f_new))
    out = {'id': 'gnc_v31_read_keys_check', 'version': 'v1', 'date': datetime.date.today().isoformat(), 'owner': 'electronics',
           'firmware': 'v2.10', 'tag': 'DERIVED (file comparison; no physical meaning)',
           'old': {'file': os.path.relpath(f_old, a.engine_root), 'version': A.get('version'), 'sha256_16': sha16(f_old)},
           'new': {'file': 'interfaces/gnc.json', 'version': B.get('version'), 'sha256_16': sha16(f_new)}, 'by_subtree': {}}
    for st in SUBTREES:
        fa, fb = {}, {}
        flat(A.get(st), st, fa)
        flat(B.get(st), st, fb)
        live = lambda x: 'superseded' not in x.lower()
        chg = sorted(x for x in fa if x in fb and fa[x] != fb[x])
        out['by_subtree'][st] = {
            'leaves_old': len(fa), 'leaves_new': len(fb),
            'changed_numeric': [{'path': x, 'old': fa[x], 'new': fb[x]} for x in chg if (num(fa[x]) or num(fb[x])) and live(x)],
            'changed_text_paths': [x for x in chg if not (num(fa[x]) or num(fb[x])) and live(x)],
            'removed': sorted(x for x in fa if x not in fb),
            'added_numeric_live': sorted(x for x in fb if x not in fa and num(fb[x]) and live(x)),
            'added_superseded_leaves': sum(1 for x in fb if x not in fa and not live(x)),
            'added_text_live': sum(1 for x in fb if x not in fa and not num(fb[x]) and live(x))}
    pl_old = A.get('requirements', {}).get('ignition', {}).get('relight_planning_value_s')
    pl_new = B.get('requirements', {}).get('ignition', {}).get('relight_planning_value_s')
    out['relight_planning_value_s_identical'] = pl_old == pl_new
    json.dump(out, open(a.out, 'w'), indent=1)
    for st, v in out['by_subtree'].items():
        print(st, 'leaves %d -> %d' % (v['leaves_old'], v['leaves_new']), 'changed numeric', len(v['changed_numeric']),
              'changed text', len(v['changed_text_paths']), 'removed', len(v['removed']), 'added numeric (live)', len(v['added_numeric_live']))
        for c in v['changed_numeric'][:12]:
            print('  ', c)
    print('relight_planning_value_s identical:', out['relight_planning_value_s_identical'])
    print('->', a.out, sha16(a.out))


if __name__ == '__main__':
    main()
