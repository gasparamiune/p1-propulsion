"""REV-COMB-3 reviewer script (independent of the author's stale-phrase scan).

Question 1 (R2-01/02/05/09 re-check): do the values REV-COMB-2 found live in combustion.json v2.4 / REPORT v2.4 still appear in
v2.4a, and if so, is each hit marked (SUPERSEDED / withdrawn / amended / superseded_* block / §13)?
Question 2 (check (f)): which v2.4a texts and keys contradict LEAD decisions published after the v2.4a fold point, up to
CHANGELOG line 186 (181 (2)-(6), 182, 183, 186 (1)-(5))?
JSON: every leaf except revision_history, revision_note and the superseded_* blocks (listed separately).  REPORT: every line with
its section; §13 lines are counted apart.  A hit is a pointer for the reviewer to read, not a verdict.
usage: python -I r3_stale_scan.py COMBUSTION_JSON REPORT_MD CF4_SPEC OUT_JSON
"""
import hashlib, json, re, sys

fj, fr, fc, out = sys.argv[1:5]
H = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H(fj) == '5237d4584bad38c4', H(fj)
assert H(fr) == '062e307a8d25e1ec', H(fr)
assert H(fc) == 'a94211a295fe0224', H(fc)
J = json.load(open(fj))
MARK = re.compile(r'SUPERSEDED|[Ww]ithdrawn|WITHDRAWN|[Aa]mended|superseded|[Rr]eplaced|REPLACED|was |no longer|refuted|REFUTED')
PAT = {
    # ---- REV-COMB-2 items (should now be marked or gone)
    'R2-01 30 bar raw': r'30 bar[^.;]{0,25}raw|raw[^.;]{0,25}30 bar|5 ms raw',
    'R2-01 closure before E1 / by E0 - 0.05 s': r'(closure|closed)[^.;]{0,40}(before E1|by E0 - 0\.05)',
    'R2-02 wait >= 5 s': r'wait >= ?5 ?s|>= 5 s wait|wait 5 s',
    'R2-05 42.85': r'42\.85',
    'R2-05 1.0-4.3 flights': r'1\.0-4\.3|\[1\.0, 4\.3\]',
    'R2-05 0.039 g/s': r'0\.039 ?g/s|"0\.039',
    'R2-05 <= 7.5 MPa': r'7\.5 MPa',
    'R2-05 0-69 bar': r'0-69 bar',
    'R2-05 15-25 C': r'15-25 ?C',
    'R2-05 valve left open': r'valve left open|left open',
    'R2-05 0.28-0.29 s': r'0\.28-0\.29',
    'R2-09 0.88-9.87 kJ': r'0\.88-9\.87',
    'R2-09 J1 pending / J1 or J2': r'J1 or J2|pending agreement|[Pp]roposal J1',
    'R2-03 75.5 bar pulse': r'75\.5 bar',
    # ---- decisions after the v2.4a fold point (181-186)
    '186(1) L* 1.7 s / commit plain trigger - 1.7 s': r'- ?1\.7 s|L\* ?= ?1\.7|1\.7 s interim|minus 1\.7',
    '186(1) relight proceeds unpurged': r'proceeds unpurged|relight proceeds UNPURGED|the relight proceeds unpurged',
    '186(1) PROVISIONAL commit rule': r'PROVISIONAL',
    '181(2) T_fire delay costs no measurable P': r'no measurable P|costs no measurable',
    '181(2) 0.81 s plan holds (now scoped to the predictor path)': r'0\.81 s plan holds',
    '181(4) pcf_tmax 0.8 s / ABORT at t_E2 + 0.8 s': r't_E2 \+ 0\.8|pcf_tmax 0\.8|ABORT at t_E2',
    '181(3) RG-16 per-flight provisional support': r'per-flight',
    '181(5) 0.30 kg mass trigger': r'0\.30 kg',
    '181(6) A1 apogee 300 m': r'300 m',
    '186(2) OI-38 command hold PROPOSAL': r'PROPOSAL[^.]{0,80}(hold|start level)|OI-38',
    '186(3) NZ-01 criterion (OI-40)': r'OI-40|> 2 %',
    '186(1) OI-31 open': r'OI-31',
    '177(1)/178 TC-09 316L lip': r'316L',
    '186(4) mechanical.json v2 / v2.1 configuration': r'mechanical\.json v2(\.1)?\b',
    'electronics.json v2 configuration': r'electronics\.json v2\b',
    'fold point line 177': r'line 177\b|to CHANGELOG line 177|lines? to 177',
}
leaves, sup = [], []


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
    s = json.dumps(v) if not isinstance(v, str) else v
    if p.startswith(('revision_history', 'revision_note')):
        continue
    (sup if p.startswith(('superseded_v2p4', 'superseded_v2p4a')) or '.superseded' in p or 'SUPERSEDED' in p else leaves).append((p, s))
lines = open(fr).read().split('\n')
sec, cur = [], ''
for L in lines:
    if L.startswith('#'):
        cur = L.strip('# ').split(' ')[0]
    sec.append(cur)
cf = open(fc).read().split('\n')
res = {}
for name, pat in PAT.items():
    rx = re.compile(pat)
    jh = []
    for p, v in leaves:
        for m in rx.finditer(v):
            ctx = v[max(0, m.start() - 160):m.end() + 120]
            jh.append(dict(path=p, marked=bool(MARK.search(ctx)), ctx=ctx))
    rh = []
    for i, L in enumerate(lines):
        for m in rx.finditer(L):
            ctx = L[max(0, m.start() - 160):m.end() + 120]
            rh.append(dict(line=i + 1, sec=sec[i], marked=bool(MARK.search(ctx)), ctx=ctx))
    ch = [dict(line=i + 1, ctx=L[:300]) for i, L in enumerate(cf) if rx.search(L)]
    res[name] = dict(json=jh, json_superseded_blocks=sum(1 for p, v in sup if rx.search(v)),
                     report_live=[x for x in rh if not x['sec'].startswith('13')],
                     report_s13=len([x for x in rh if x['sec'].startswith('13')]), cf4=ch)
json.dump(dict(inputs=dict(combustion_json=H(fj), report=H(fr), cf4=H(fc)), results=res), open(out, 'w'), indent=1)
for name, r in res.items():
    ju = [x for x in r['json'] if not x['marked']]
    ru = [x for x in r['report_live'] if not x['marked']]
    print('== %-62s JSON %3d (unmarked %3d) | REPORT live %3d (unmarked %3d) | §13 %2d | CF-4 %d'
          % (name, len(r['json']), len(ju), len(r['report_live']), len(ru), r['report_s13'], len(r['cf4'])))
print('wrote', out, H(out))
