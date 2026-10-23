import csv, sys
a = {r['line']: r for r in csv.DictReader(open(sys.argv[1], newline='', encoding='utf-8'))}
b = {r['line']: r for r in csv.DictReader(open(sys.argv[2], newline='', encoding='utf-8'))}
print('v2.4 rows', len(a), 'v2.5 rows', len(b))
only_b = sorted(set(b) - set(a), key=int); only_a = sorted(set(a) - set(b), key=int)
print('added lines', only_b, 'removed lines', only_a)
changed = []
for k in sorted(set(a) & set(b), key=int):
    fa = a[k]; fb = b[k]
    d = [f for f in fb if fa.get(f) != fb.get(f)]
    if d: changed.append((k, d))
print('changed rows', len(changed))
for k, d in changed:
    print(k, d)
    for f in d:
        print('   -', f, 'OLD:', (a[k].get(f) or '')[:400])
        print('   +', f, 'NEW:', (b[k].get(f) or '')[:400])
