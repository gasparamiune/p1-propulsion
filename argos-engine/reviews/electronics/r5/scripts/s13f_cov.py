import json, sys, re
from collections import Counter
d = json.load(open(sys.argv[1], encoding='utf-8'))
print('top keys', list(d.keys())[:30])
runs = None
for k in ('runs', 'cases', 'results'):
    if k in d: runs = d[k]; break
if runs is None:
    for k, v in d.items():
        if isinstance(v, list) and v and isinstance(v[0], dict): runs = v; print('using', k); break
print('n runs', len(runs)); print('keys of a run', list(runs[0].keys()))
print(json.dumps(runs[0])[:800])
