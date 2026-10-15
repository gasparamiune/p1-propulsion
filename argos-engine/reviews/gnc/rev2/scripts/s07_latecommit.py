import sys; sys.path.insert(0, ".")
from rvlib import *
import numpy as np
B2 = ("A1_none", "A1J_pc")
rows = []
for arm in ("e19|G73", "e19|G73|hf100", "e19|G73|hf90", "e19|G73|hf80", "e19|G73|hf70", "e19|G73|ant0"):
    for b in B2:
        for r in load(b, arm):
            tgo, t0 = f(r, "pgg_tgo"), f(r, "pgg_t0")
            rows.append(dict(arm=arm, base=b, ok=float(r["ok"]) > 0.5, dly=f(r, "pgg_dly"), lead=(tgo - t0) if tgo >= 0 else np.nan,
                             hE0=f(r, "pgg_hE0"), h0=f(r, "pgg_h0"), src=f(r, "pgg_src"), fl=f(r, "pgg_fl"), tgo=tgo,
                             hgo=f(r, "pgg_hgo"), wind=f(r, "wind")))
import collections
print("per arm: P, delay range, lead (commit->plain trigger) range, E0 height min, src counts")
for arm in ("e19|G73", "e19|G73|hf100", "e19|G73|hf90", "e19|G73|hf80", "e19|G73|hf70", "e19|G73|ant0"):
    x = [r for r in rows if r["arm"] == arm]
    d = np.array([r["dly"] for r in x]); L = np.array([r["lead"] for r in x]); o = np.array([r["ok"] for r in x])
    print(f"{arm:15s} P {o.mean():.3f} dly p50 {np.nanpercentile(d,50):.3f} p99 {np.nanpercentile(d,99):.3f} max {np.nanmax(d):.3f} | lead min {np.nanmin(L):.3f} p50 {np.nanpercentile(L,50):.3f} | hE0 min {min(r['hE0'] for r in x):.1f} | src {dict(collections.Counter(r['src'] for r in x))} | flow min {min(r['fl'] for r in x):.3f}")
# dose-response over all forced-commit arms (hf*) + decided
x = [r for r in rows if r["arm"] != "e19|G73|ant0"]
d = np.array([r["dly"] for r in x]); o = np.array([r["ok"] for r in x]); L = np.array([r["lead"] for r in x])
print("\nP vs T_fire delay (pooled e19 hf100/90/80/70 + decided, 2 bases)")
edges = [-0.01, 0.001, 0.2, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3, 1.4, 1.6, 2.4]
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (d > lo) & (d <= hi)
    if m.sum():
        k = int(o[m].sum()); n = int(m.sum()); w = wilson(k, n)
        print(f"  delay ({lo:.3f},{hi:.3f}] n {n:5d} P {k/n:.3f} W[{w[0]:.3f},{w[1]:.3f}]")
print("\nP vs lead time commit->plain trigger (runs where the plain trigger fired)")
edges = [0.0, 1.0, 1.2, 1.3, 1.4, 1.5, 1.6, 1.65, 1.7, 1.75, 1.8, 1.9, 2.0, 2.3, 2.66, 5]
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (L > lo) & (L <= hi)
    if m.sum():
        k = int(o[m].sum()); n = int(m.sum()); w = wilson(k, n)
        print(f"  lead ({lo:.2f},{hi:.2f}] n {n:5d} P {k/n:.3f} W[{w[0]:.3f},{w[1]:.3f}]")
# failures in hf100 (the 'no measurable cost' arm): delays of failed runs
for arm in ("e19|G73|hf100", "e19|G73|hf90"):
    x = [r for r in rows if r["arm"] == arm]
    fl = sorted([(round(r["dly"], 3), round(r["hE0"], 1), r["base"]) for r in x if not r["ok"]], reverse=True)
    print(arm, "failed runs (delay, hE0):", fl[:12])
    dd = np.array([r["dly"] for r in x]); print("   delay counts >0.5:", int(np.sum(dd > 0.5)), ">0.6:", int(np.sum(dd > 0.6)), "of", len(x))
