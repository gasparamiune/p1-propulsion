#!/usr/bin/env python3
# REV-ELEC-4: the v2.11 SIL record commands re-run on the rebuilt v2.12 binaries (reviewer RAM folder) against the staged v2.11 record
# (staging_v2.11/results/sil_v2p11). File-level sha256/16, then for JSON files a leaf-by-leaf comparison: the number of leaves equal /
# changed, and every changed OUTCOME leaf (keys pass, cause, first_abort, abort, outcome, class, fail, aborted, inside..., result) listed.
# Run: python3 -I compare_v212_vs_v211_record.py <out.json>
import hashlib, json, os, re, sys
REC = '/home/claude/work/shared-fallback/engine/06-electronics/staging_v2.11/results/sil_v2p11'
RUN = '/dev/shm/rev_elec4/run/rec'
OUTK = re.compile(r'(^|[._\[])(pass|cause|first_abort|abort|outcome|class|fail|fails|aborted|inside_LC_TB70|result|refused|detected|ok|verdict|lit|ran)([._\]]|$)', re.I)
def h16(b): return hashlib.sha256(b).hexdigest()[:16]
def leaves(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items(): yield from leaves(v, p + '.' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            key = None
            if isinstance(v, dict):
                key = v.get('case') or v.get('id') or v.get('name') or v.get('run')
                if key is not None and 'build' in v: key = '%s|%s' % (key, v['build'])
            yield from leaves(v, p + '[%s]' % (key if key is not None else i))
    else: yield p, o
res = {'record': REC, 'rerun': RUN, 'files': []}
for root, _, files in os.walk(RUN):
    for f in sorted(files):
        p = os.path.join(root, f); rel = os.path.relpath(p, RUN); r = os.path.join(REC, rel)
        row = {'file': rel, 'sha16_rerun': h16(open(p, 'rb').read())}
        if not os.path.exists(r): row['status'] = 'NOT_IN_RECORD'; res['files'].append(row); continue
        row['sha16_record'] = h16(open(r, 'rb').read())
        if row['sha16_rerun'] == row['sha16_record']: row['status'] = 'IDENTICAL'; res['files'].append(row); continue
        row['status'] = 'DIFF'
        if f.endswith('.json'):
            try:
                a = dict(leaves(json.load(open(p)))); b = dict(leaves(json.load(open(r))))
            except Exception as e:
                row['json_error'] = str(e); res['files'].append(row); continue
            same = sum(1 for k in a if k in b and a[k] == b[k]); chg = [k for k in a if k in b and a[k] != b[k]]
            row['leaves'] = {'rerun': len(a), 'record': len(b), 'equal': same, 'changed': len(chg),
                             'only_rerun': len([k for k in a if k not in b]), 'only_record': len([k for k in b if k not in a])}
            oc = [k for k in chg if OUTK.search(k.split('.')[-1] if '.' in k else k)]
            row['outcome_leaves_changed'] = [[k, b[k], a[k]] for k in oc][:200]
            row['outcome_leaves_only_rerun'] = [k for k in a if k not in b and OUTK.search(k.split('.')[-1])][:50]
            row['outcome_leaves_only_record'] = [k for k in b if k not in a and OUTK.search(k.split('.')[-1])][:50]
        res['files'].append(row)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
for row in res['files']:
    print(row['file'], row['status'], row.get('leaves', ''), 'outcome changes:', len(row.get('outcome_leaves_changed', [])))
