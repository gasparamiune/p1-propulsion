import json, sys, re
from collections import Counter, defaultdict
d = json.load(open(sys.argv[1], encoding='utf-8'))
runs = d['runs']
cases = sorted(set(r['case'] for r in runs)); faults = sorted(set(r['fault'] for r in runs))
print('pass_rule:', d['pass_rule'][:600])
print('n cases', len(cases), 'n faults', len(faults))
# case families: strip the s/k/lit suffix
fam = Counter(re.sub(r'_s[+-]1_k\d+(\.\d+)?_(lit|unlit)$', '', c) for c in cases)
for f, n in sorted(fam.items()): print('  family', f, n)
print('faults:', faults)
print('ks', sorted(set(re.search(r'_k(\d+(?:\.\d+)?)_', c).group(1) for c in cases)))
oc = Counter((r['fault'] == 'none', r['outcome']) for r in runs)
print('outcomes', oc.most_common())
print('SEAT_STEP among faults', Counter(r['SEAT_STEP'] for r in runs if r['fault'] != 'none'))
# which faults did NOT latch SEAT_STEP
nolatch = Counter(r['fault'] for r in runs if r['fault'] != 'none' and not r['SEAT_STEP'])
print('faults without SEAT_STEP', nolatch.most_common(20))
