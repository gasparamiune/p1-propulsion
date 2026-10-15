"""REV-COMB-2 reviewer script: scan combustion.json v2.4 for (1) every string mentioning 'raw' near '30 bar' / A4 / over-pressure,
(2) the superseded_v2p4 list and whether each superseded value still appears in live (non-superseded, non-history) text,
(3) v2.3 key paths kept, (4) untagged leaf values in the new v2.4 blocks, (5) igniter.sequence key inventory.
usage: python -I r2_json_scan.py COMBUSTION_JSON V23_JSON OUT_JSON
"""
import hashlib, json, re, sys

f24, f23, out = sys.argv[1:4]
h24 = hashlib.sha256(open(f24, 'rb').read()).hexdigest()[:16]
h23 = hashlib.sha256(open(f23, 'rb').read()).hexdigest()[:16]
assert h24 == '469727032124329f', h24
assert h23 == 'd9ec54fbf450e243', h23
J = json.load(open(f24)); J23 = json.load(open(f23))


def walk(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + '.' + str(k) if p else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + '[%d]' % i)
    else:
        yield p, o


def paths(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items():
            q = p + '.' + str(k) if p else str(k)
            yield q
            yield from paths(v, q)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from paths(v, p + '[%d]' % i)


res = dict(sha16=h24, v23_sha16=h23)
leaves = list(walk(J))
res['n_leaves'] = len(leaves)
p23 = set(q for q in paths(J23) if '[' not in q.split('.')[-1] or True)
p24 = set(paths(J))
dict23 = set(q for q in p23 if not re.search(r'\[\d+\]', q))
dict24 = set(q for q in p24 if not re.search(r'\[\d+\]', q))
res['v23_dict_paths'] = len(dict23)
res['v23_dict_paths_missing_in_v24'] = sorted(dict23 - dict24)[:50]
res['n_missing'] = len(dict23 - dict24)

# (1) 'raw' with 30 bar / A4 / overpressure
hits = []
for p, v in leaves:
    if isinstance(v, str):
        s = v
        for m in re.finditer(r'raw', s):
            ctx = s[max(0, m.start() - 160):m.end() + 120]
            if re.search(r'30 ?bar|A4|over-?pressure|OVERPRESSURE|HARD_START|30e5|3\.0e6|persistence', ctx):
                hits.append(dict(path=p, ctx=ctx.replace('\n', ' ')))
res['raw_30bar_hits'] = hits
# filtered mention for the 30 bar abort
filt = []
for p, v in leaves:
    if isinstance(v, str) and re.search(r'30 ?bar', v) and re.search(r'[Ff]iltered', v):
        filt.append(dict(path=p, ctx=v[:400]))
res['filtered_30bar_mentions'] = filt
# numeric keys about the abort
num = [(p, v) for p, v in leaves if re.search(r'(abort|overpressure|A4).*(persist|channel)', p, re.I)]
res['abort_persistence_keys'] = num

# (2) superseded list
sup = J.get('superseded_v2p4', {})
res['superseded_v2p4'] = sup
json.dump(res, open(out, 'w'), indent=1, default=str)
print('sha', h24, 'leaves', len(leaves), 'v2.3 dict paths', len(dict23), 'missing in v2.4', len(dict23 - dict24))
for m in res['v23_dict_paths_missing_in_v24'][:20]:
    print('  missing:', m)
print('--- raw + 30 bar/A4 hits:', len(hits))
for h in hits:
    print(' ', h['path'], '::', h['ctx'][:330])
print('--- filtered + 30 bar mentions:', len(filt))
for h in filt:
    print(' ', h['path'], '::', h['ctx'][:300])
print('--- abort persistence keys:', num)
