"""REV-COMB-2 reviewer script: trace the minimum and maximum vented-mass records of the decided path (2 x 0.707 mm, unlined,
theta 0 and 2 deg) in the author's raw trade file, to find the cause of the early-flow anomaly (minimum rising at ~6 g/s,
below the 8.49 g/s all-vapour flow).  Independent reader (own regex streamer); the author's code is not imported.
usage: python -I r2_vented_trace.py RAW_GZ OUT_JSON
"""
import gzip, hashlib, json, re, sys
from collections import defaultdict

raw, out = sys.argv[1:3]
h16 = hashlib.sha256(open(raw, 'rb').read()).hexdigest()[:16]
assert h16 == '02c30eb2e6569e8d', h16
pat = re.compile(r'"(purge0\.707\|2tap\|[^"]*)":\{([^{}]*)\}')
recs = {}
buf = ''
with gzip.open(raw, 'rt') as fh:
    while True:
        ch = fh.read(1 << 24)
        if not ch:
            break
        buf += ch
        end = 0
        for m in pat.finditer(buf):
            recs[m.group(1)] = json.loads('{' + m.group(2) + '}')
            end = m.end()
        buf = buf[max(end, len(buf) - 20000):]
for m in pat.finditer(buf):
    recs[m.group(1)] = json.loads('{' + m.group(2) + '}')

keys = list(recs)
sample_key = keys[0]
fields = sorted(recs[sample_key].keys())
byTp = defaultdict(list)
for k, r in recs.items():
    p = k.split('|')
    Tp = float(p[3][2:]); lin = p[4][3:]; th = float(p[9])
    if lin == '0.0' and th in (0.0, 2.0) and 'N2O_g' in r:
        byTp[Tp].append((r['N2O_g'], k, r))
res = dict(raw_sha16=h16, n_records=len(recs), sample_key=sample_key, key_fields=sample_key.split('|'), record_fields=fields, rows=[])
for Tp in sorted(byTp):
    L = sorted(byTp[Tp], key=lambda x: x[0])
    lo, hi = L[0], L[-1]
    def brief(x):
        r = x[2]
        return dict(key=x[1], N2O_g=r['N2O_g'], vented_vap_cm3=r.get('vented_vap_cm3'), vented_liq_cm3=r.get('vented_liq_cm3'))
    # how many of the 20 lowest records are 'barrier' vs 'open'
    low20 = [x[1] for x in L[:20]]
    res['rows'].append(dict(Tp=Tp, n=len(L), min=brief(lo), max=brief(hi), low20_keys=low20[:5],
                            low20_barrier=sum('barrier' in k or '|bar' in k for k in low20)))
json.dump(res, open(out, 'w'), indent=1)
print('records', len(recs), 'sample key', sample_key)
print('fields', fields)
for r in res['rows']:
    print(r['Tp'], r['n'], 'MIN', r['min'], '\n     MAX', r['max'], '\n     low20 barrier', r['low20_barrier'], r['low20_keys'][:2])
