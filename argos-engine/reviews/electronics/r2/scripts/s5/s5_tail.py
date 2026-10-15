#!/usr/bin/env python3
"""REV-ELEC-2: S5 tail statistics from a reviewer N-run S5 (same binary and generator as the record; first 300 rows must equal the
record). Flying runs = abort 'none' with both step rise times finite (the step profile was flown). Usage: s5_tail.py <record_csv> <run_csv>"""
import csv, math, sys
rec = open(sys.argv[1]).read().splitlines()
new = open(sys.argv[2]).read().splitlines()
same = sum(1 for a, b in zip(rec[1:301], new[1:301]) if a == b)
print('first 300 data rows identical to the record:', same, '/ 300; header identical:', rec[0] == new[0])
r = list(csv.DictReader(open(sys.argv[2])))
def f(x, k):
    try:
        return float(x[k])
    except Exception:
        return float('nan')
n = len(r)
ab = {}
for x in r:
    ab[x['abort']] = ab.get(x['abort'], 0) + 1
fly = [x for x in r if x['abort'] in ('none', '0') and not math.isnan(f(x, 'up_rise')) and not math.isnan(f(x, 'dn_rise'))]
pc = sorted(f(x, 'pc_max') / 1e5 for x in fly)
m = len(pc)
def q(p):
    i = max(0, min(m - 1, int(math.ceil(p * m)) - 1))
    return pc[i]
print('runs', n, '| abort classes', ab, '| flying runs', m)
print('plant Pc max bar abs over flying runs: max %.3f | p99.9 (empirical, rank ceil(0.999 m)) %.3f | p99 %.3f | p95 %.3f | p50 %.3f' % (pc[-1], q(0.999), q(0.99), q(0.95), q(0.5)))
print('top 10:', ['%.3f' % v for v in pc[-10:]])
for thr in (27.0, 27.5, 28.0, 29.0, 29.5, 30.0):
    k = sum(1 for v in pc if v > thr)
    up = 1 - 0.05 ** (1.0 / m) if k == 0 else float('nan')
    print('  > %.1f bar abs: %d of %d%s' % (thr, k, m, ('  (0 seen: one-sided 95 %% upper bound on the exceedance probability %.2e)' % up) if k == 0 else ''))
ups = sorted(f(x, 'up_rise') for x in fly)
print('up-step t10-90 over flying runs: p50 %.3f p95 %.3f max %.3f; > 0.150 s: %d; <= 0.100 s: %d of %d' % (
    ups[m // 2], ups[int(0.95 * (m - 1))], ups[-1], sum(1 for v in ups if v > 0.150), sum(1 for v in ups if v <= 0.100), m))
ov = sorted(f(x, 'up_ovs') for x in fly)
print('up-step overshoot %% over flying runs: p50 %.2f p95 %.2f max %.2f' % (ov[m // 2], ov[int(0.95 * (m - 1))], ov[-1]))
nonfly = [x for x in r if x not in fly]
dn25 = sum(1 for x in nonfly if abs(f(x, 'dn_ovs') - 25.0) < 1e-6)
print('non-flying runs', len(nonfly), '| of them with dn_ovs = 25.00 % exactly (zero-thrust artifact):', dn25)
tc = [(int(x['run']), f(x, 'T_tank0'), x['abort'], x['final_state']) for x in r if x['abort'] in ('none', '0') and x not in fly]
print('abort none but step profile not flown (start refused after ARM):', len(tc), tc[:12])
