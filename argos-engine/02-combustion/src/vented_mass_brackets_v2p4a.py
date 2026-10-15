"""Combustion v2.4a (R2-06): split the decided-path vented-mass envelope by filter-element model.
Reduction of existing trade records only (no re-run). Reads the raw trade file, keeps the decided path
(purge0.707|2tap), unlined, theta 0 and 2 deg, and reports per flow time Tp the min / max N2O vented for the
'barrier' (filter element as a capillary barrier) and 'open' element readings, against the all-vapour (8.4916 g/s)
and all-liquid (31.2416 g/s) rate lines. SIM records (purge_duration_v2p4 trade) on ASSUMED Cd and slip brackets.
usage: python -I vented_mass_brackets_v2p4a.py RAW_GZ OUT_JSON
"""
import gzip, hashlib, json, re, sys
from collections import defaultdict
raw, out = sys.argv[1:3]
h16 = hashlib.sha256(open(raw, 'rb').read()).hexdigest()[:16]
assert h16 == '02c30eb2e6569e8d', h16
pat = re.compile(r'"(purge0\.707\|2tap\|[^"]*)":\{([^{}]*)\}')
num = re.compile(r'"N2O_g":\s*([-0-9.eE+]+)')
groups = defaultdict(list)   # (Tp, element) -> list of (N2O_g, key)
seen = set()
def take(key, body):
    if key in seen:
        return
    seen.add(key)
    p = key.split('|')
    Tp = round(float(p[3][2:]), 3); lin = p[4][3:]; elem = p[5]; th = float(p[9])
    if lin != '0.0' or th not in (0.0, 2.0):
        return
    m = num.search(body)
    if m:
        groups[(Tp, elem)].append((float(m.group(1)), key))
buf = ''
with gzip.open(raw, 'rt') as fh:
    while True:
        ch = fh.read(1 << 24)
        if not ch:
            break
        buf += ch
        end = 0
        for m in pat.finditer(buf):
            take(m.group(1), m.group(2)); end = m.end()
        buf = buf[max(end, len(buf) - 20000):]
for m in pat.finditer(buf):
    take(m.group(1), m.group(2))
VAP, LIQ = 8.4916, 31.2416
rows = []
for Tp in sorted({k[0] for k in groups}):
    r = dict(t_flow_s=Tp, vapour_line_g=round(VAP * Tp, 2), liquid_line_g=round(LIQ * Tp, 2))
    for el in ('barrier', 'open'):
        L = sorted(groups.get((Tp, el), []))
        if not L:
            continue
        r[el] = dict(n=len(L), min_g=round(L[0][0], 2), max_g=round(L[-1][0], 2), min_key=L[0][1], max_key=L[-1][1],
                     n_below_vapour_line=sum(1 for x in L if x[0] < VAP * Tp - 1e-9))
    rows.append(r)
res = dict(version='v2.4a', date='2026-10-13', script='02-combustion/src/vented_mass_brackets_v2p4a.py',
           inputs={'purge_duration_v2p4_trade.json.raw.json.gz': h16}, n_records_read=len(seen),
           selection='purge0.707|2tap, lin 0.0, theta 0 and 2 deg, all slip brackets, heat cases, readings and azimuths',
           rate_lines_g_s=dict(all_vapour=VAP, all_liquid=LIQ), rows=rows,
           tags='SIM records (purge_duration_v2p4 trade) on ASSUMED Cd and slip brackets; split by element model DERIVED')
json.dump(res, open(out, 'w'), indent=1)
print('records read', len(seen))
for r in rows:
    b = r.get('barrier', {}); o = r.get('open', {})
    print(f"Tp {r['t_flow_s']:.1f} vap {r['vapour_line_g']:6.2f} liq {r['liquid_line_g']:6.2f} | barrier n {b.get('n')} min {b.get('min_g')} max {b.get('max_g')} below {b.get('n_below_vapour_line')} | open n {o.get('n')} min {o.get('min_g')} max {o.get('max_g')} below {o.get('n_below_vapour_line')}")
