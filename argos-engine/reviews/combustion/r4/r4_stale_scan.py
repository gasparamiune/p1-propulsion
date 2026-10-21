"""REV-COMB-4 reviewer script: stale texts in interfaces/combustion.json v2.4b (CHANGELOG 253 (10)).

Walks every string leaf (and key) of the JSON and reports, with its JSON path, each occurrence of the patterns below; also counts
raw-file regex hits so the reviewer's earlier count (6 / 4) and the handback's (4 / 3) can be reconciled.
  P112:  '112 bar abs', '>= 112', '1.1 x 102' (the superseded stand-proof rule; 249 (4): proof >= 166 bar abs = 1.1 x FA1S 151.04)
  P015:  'E0 + 0.15 s' and variants (the superseded closure deadline; the torch gate is E0 + 0.16 s / 160 ms)
  PCF05: 'pcf_tmax 0.5' / 't_E2 + 0.5 s' (181 (4) value; LEAD 227 (5) ADOPTED the 0.8 s R2 starve window, pcf_tmax 0.8 s)
  FLOW19: '1.9 s of flow' (the 289.5 K need; 2.2 s at the 283.15 K corner, REV-COMB-4)
Optional further arguments: text files (.md) scanned line by line for the same patterns (1-based line numbers).
Tags: text scan (CALC); corrections are the reviewer's proposals.
usage: python -I r4_stale_scan.py COMBUSTION_JSON OUT_JSON [TEXT_FILE ...]
"""
import hashlib, json, re, sys

src, out_f = sys.argv[1:3]
raw = open(src, encoding='utf-8').read()
H16 = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
PAT = {'P112': re.compile(r'112 bar abs|>= ?112\b|1\.1 x 102\b|\b112 bar\b'),
       'P015': re.compile(r'E0 ?\+ ?0\.15 ?s|E0 ?\+ ?150 ?ms|0\.15 s after E0'),
       'PCF05': re.compile(r'pcf_tmax 0\.5|t_E2 \+ 0\.5 s'),
       'FLOW19': re.compile(r'1\.9 s of flow|needs 1\.9 s')}
D = json.loads(raw)
hits = []


def walk(x, path):
    if isinstance(x, dict):
        for k, v in x.items():
            for name, p in PAT.items():
                for m in p.finditer(k):
                    hits.append(dict(pattern=name, path=path + [k], where='key', match=m.group(0), text=k))
            walk(v, path + [k])
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, path + [i])
    elif isinstance(x, str):
        for name, p in PAT.items():
            for m in p.finditer(x):
                s0 = max(0, m.start() - 160); s1 = min(len(x), m.end() + 160)
                hits.append(dict(pattern=name, path=path, where='value', match=m.group(0), context=x[s0:s1], leaf_len=len(x)))


walk(D, [])
raw_counts = {name: len(p.findall(raw)) for name, p in PAT.items()}
leaf_counts = {name: sum(h['pattern'] == name for h in hits) for name in PAT}
distinct_leaves = {name: len(set(json.dumps(h['path']) for h in hits if h['pattern'] == name)) for name in PAT}
res = dict(script='r4_stale_scan.py', script_sha16=hashlib.sha256(open(sys.argv[0], 'rb').read()).hexdigest()[:16], input=src,
           input_sha16=H16, version=D.get('version'), raw_regex_counts=raw_counts, occurrences=leaf_counts, distinct_leaves=distinct_leaves,
           hits=hits)
text = {}
for tf in sys.argv[3:]:
    rows = []
    for ln, line in enumerate(open(tf, encoding='utf-8'), 1):
        for name, p in PAT.items():
            for m in p.finditer(line):
                s0 = max(0, m.start() - 120); s1 = min(len(line), m.end() + 120)
                rows.append(dict(pattern=name, line=ln, match=m.group(0), context=line[s0:s1].rstrip()))
    text[tf] = dict(sha16=hashlib.sha256(open(tf, 'rb').read()).hexdigest()[:16], hits=rows,
                    counts={name: sum(r['pattern'] == name for r in rows) for name in PAT})
res['text_files'] = text
json.dump(res, open(out_f, 'w'), indent=1)
print(json.dumps(dict(input_sha16=H16, version=D.get('version'), raw=raw_counts, occ=leaf_counts, leaves=distinct_leaves)))
for h in hits:
    print('---', h['pattern'], h['where'], json.dumps(h['path']), '|', h['match'])
    print('   ', h.get('context', h.get('text')))
