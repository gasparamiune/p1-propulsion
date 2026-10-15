import sys; sys.path.insert(0, ".")
from rvlib import *
import numpy as np
B2 = ("A1_none", "A1J_pc")
pairs = []
for arm in ("e19|G73|hf100", "e19|G73|hf90", "e19|G73|hf80", "e19|G73|hf70"):
    for b in B2:
        ref = load(b, "e19|G73"); x = load(b, arm)
        for r0, r1 in zip(ref, x):
            assert r0["run"] == r1["run"]
            tgo, t0 = f(r1, "pgg_tgo"), f(r1, "pgg_t0")
            pairs.append((float(r0["ok"]) > 0.5, float(r1["ok"]) > 0.5, f(r1, "pgg_dly"), (tgo - t0) if tgo >= 0 else np.nan, arm))
ok0 = np.array([p[0] for p in pairs]); ok1 = np.array([p[1] for p in pairs]); d = np.array([p[2] for p in pairs]); L = np.array([p[3] for p in pairs])
print("Paired: runs that succeed with the decided commit (e19|G73); fraction lost when the commit is forced late, by T_fire delay")
edges = [-0.01, 0.001, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.8, 0.9, 1.0, 2.4]
for lo, hi in zip(edges[:-1], edges[1:]):
    m = ok0 & (d > lo) & (d <= hi)
    n = int(m.sum())
    if n:
        lost = int(np.sum(m & ~ok1)); gained = int(np.sum((~ok0) & (d > lo) & (d <= hi) & ok1)); w = wilson(lost, n)
        print(f"  delay ({lo:.3f},{hi:.3f}] ref-ok n {n:5d} lost {lost:4d} ({lost/n:.3f} W[{w[0]:.3f},{w[1]:.3f}]) | gained among ref-fail {gained}")
print("By lead time commit -> plain trigger:")
edges = [0, 1.3, 1.5, 1.6, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0, 2.1, 2.3, 5]
for lo, hi in zip(edges[:-1], edges[1:]):
    m = ok0 & (L > lo) & (L <= hi)
    n = int(m.sum())
    if n:
        lost = int(np.sum(m & ~ok1)); w = wilson(lost, n)
        print(f"  lead ({lo:.2f},{hi:.2f}] ref-ok n {n:5d} lost {lost:4d} ({lost/n:.3f} W[{w[0]:.3f},{w[1]:.3f}])")
