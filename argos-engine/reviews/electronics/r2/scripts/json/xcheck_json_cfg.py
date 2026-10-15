#!/usr/bin/env python3
"""REV-ELEC-2: cross-check interfaces/electronics.json v3 numeric entries that cite 'config.h kName' against the compiled config.h values."""
import json, re, sys
cfg = {}
for line in open(sys.argv[2]):
    n, v = line.split()
    cfg[n] = float(v)
d = json.load(open(sys.argv[1]))
rows, bad, unmatched = [], [], []
def num(v):
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    return None
def walk(o, p):
    if isinstance(o, dict):
        s = o.get('src')
        if isinstance(s, str) and s.startswith('config.h'):
            names = re.findall(r'\bk\w+', s)
            v = num(o.get('v'))
            if names and v is not None:
                n = names[0]
                if n not in cfg:
                    unmatched.append((p, s, v))
                else:
                    c = cfg[n]
                    ok = None
                    for scale, lab in ((1, 'SI'), (1e-5, 'Pa->bar'), (1e3, 's->ms'), (1e3, 'm->mm'), (1e-3, 'x1e-3'), (100, 'frac->%'), (1e6, 'x1e6')):
                        if abs(c * scale - v) <= max(1e-6, 2e-4 * abs(v)):
                            ok = lab
                            break
                    rows.append((p, n, v, c, ok, o.get('unit')))
                    if ok is None:
                        bad.append((p, n, v, c, o.get('unit')))
            elif names and v is None and 'v' in o:
                rows.append((p, names[0], o.get('v'), cfg.get(names[0]), 'non-numeric v', o.get('unit')))
        for k, v in o.items():
            walk(v, p + '.' + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, p + '[%d]' % i)
walk(d, '')
print('entries citing config.h:', len(rows), '| numeric mismatches:', len(bad), '| constant not found in config.h:', len(unmatched))
for b in bad:
    print('MISMATCH', b)
for u in unmatched:
    print('NOT-IN-CONFIG', u)
scales = {}
for r in rows:
    scales[r[4]] = scales.get(r[4], 0) + 1
print('match classes:', scales)
for r in rows:
    if r[4] not in ('SI',):
        print('  ', r)
