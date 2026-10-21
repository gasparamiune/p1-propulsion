import json, sys, re
p = sys.argv[1]
d = json.load(open(p, encoding='utf-8'))
print('top keys', len(d))
print(list(d.keys()))
# find all string paths containing given patterns
pats = [r'266 \(6\)', r'carve-out', r'NO-GO', r'STAGED', r'REV-ELEC-5']
hits = {k: [] for k in pats}
def walk(o, path):
    if isinstance(o, dict):
        for k, v in o.items(): walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, path + '[%d]' % i)
    elif isinstance(o, str):
        for pt in pats:
            if re.search(pt, o): hits[pt].append((path, o))
walk(d, '')
for pt in pats:
    print('==', pt, len(hits[pt]))
    for path, s in hits[pt][:40]:
        print('  ', path, '::', s[:260].replace('\n', ' '))
