"""REV-COMB-2 reviewer script: are the values in combustion.json v2.4 superseded_v2p4 (and other values superseded by lead lines
160-170 / REQUIREMENTS amendments) still present in live JSON leaves or in the live REPORT text?
JSON: every leaf except superseded_v2p4, revision_history, revision_note.  REPORT: every line, with the section it sits in; lines
inside §13 (failures/superseded) are reported separately.  A hit is not automatically an error: the reviewer reads each one.
usage: python -I r2_superseded_scan.py COMBUSTION_JSON REPORT_MD OUT_JSON
"""
import hashlib, json, re, sys

fj, fr, out = sys.argv[1:4]
assert hashlib.sha256(open(fj, 'rb').read()).hexdigest()[:16] == '469727032124329f'
assert hashlib.sha256(open(fr, 'rb').read()).hexdigest()[:16] == '32e366bd78437dc0'
J = json.load(open(fj))
PAT = {
    'late light 44.9 bar': r'44\.9 ?bar',
    'about 50 g per purge': r'(about|~) ?50 g',
    '0.8 mm per tap': r'0\.8 mm per tap|0\.8 mm, both taps',
    'PURGE at E0 - 2.40 s': r'2\.40 ?s',
    'A5 8.0 bar abort': r'8\.0 bar[^.]{0,40}5 ms|Pc > 8',
    'ECU cap 2.5 + 0.3 s': r'2\.5 ?\+ ?0\.3',
    'coast leak ceiling 0.039': r'0\.039 ?g/s',
    'MEOP basis 42.85': r'42\.85',
    'throat life 1.0-4.3': r'1\.0-4\.3|\[1\.0, 4\.3\]|1-4 A1',
    '15.91 cm3': r'15\.91',
    'inventory 8.74 g': r'8\.74 ?g',
    'wait >= 5 s (withdrawn, REPORT 7.6)': r'wait >= ?5 ?s|>= 5 s wait',
    'tank 15-25 C (ENG-12 amended to 15-24 C)': r'15-25 ?C',
    '20 +/- 3 C': r'20 \+/- 3',
    '0-69 bar transducer': r'0-69 bar',
    '3.0 bar abs light threshold (withdrawn)': r'kIgnitionPcAbs|3\.0 bar abs',
    'torch gate 0.10 s (withdrawn)': r'gate[^.]{0,30}0\.10 s|0\.100 s',
    '30 bar abort raw': r'30 bar[^.;]{0,25}raw|raw[^.;]{0,25}30 bar',
    '30 bar persistence 3 ms': r'3 ms persistence|persistence 3 ms|raw persistence 3',
    'bleed 0.6-0.8 mm (superseded by 1.0 mm equivalent)': r'0\.6-0\.8 mm',
    'J1 pending / J1 or J2 (J1 confirmed line 146)': r'J1 or J2|pending agreement',
    'lip <= 250 C as a requirement (line 145: goal)': r'250 C in-burn|at or below its present 250',
    'heat into segment 0.88-9.87 kJ vs 0.83-9.0 kJ': r'0\.88-9\.87|0\.83-9\.0 kJ',
    'PURGE NOT RUN would-be latencies': r'1\.318|1\.305',
    'lead decisions to line 164 (handback says 168)': r'line 164 and Mechanical|to CHANGELOG line 164',
}
leaves = []


def walk(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + '.' + str(k) if p else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + '[%d]' % i)
    else:
        yield p, o


for p, v in walk(J):
    if p.startswith(('superseded_v2p4', 'revision_history', 'revision_note')):
        continue
    leaves.append((p, json.dumps(v) if not isinstance(v, str) else v))
lines = open(fr).read().split('\n')
sec = []
cur = ''
for i, L in enumerate(lines):
    if L.startswith('#'):
        cur = L.strip('# ').split(' ')[0]
    sec.append(cur)
res = {}
for name, pat in PAT.items():
    rx = re.compile(pat)
    jh = [(p, v) for p, v in leaves if rx.search(v)]
    rh = [(i + 1, sec[i], lines[i]) for i, L in enumerate(lines) if rx.search(L)]
    res[name] = dict(json=jh, report_live=[x for x in rh if not x[1].startswith('13')], report_s13=[x for x in rh if x[1].startswith('13')])
json.dump(res, open(out, 'w'), indent=1)
for name, r in res.items():
    print('==', name, '| JSON', len(r['json']), '| REPORT live', len(r['report_live']), '| §13', len(r['report_s13']))
    for p, v in r['json'][:6]:
        m = re.search(PAT[name], v)
        s = max(0, m.start() - 90)
        print('   J', p, '::', v[s:s + 200].replace('\n', ' '))
    for i, s_, L in r['report_live'][:8]:
        m = re.search(PAT[name], L)
        s = max(0, m.start() - 80)
        print('   R', i, '§' + s_, '::', L[s:s + 190])
