import sys, csv, os; sys.path.insert(0, "."); from rvlib import *
import numpy as np
V = os.environ["RV_VOUT"]
def lv(n): return list(csv.DictReader(open(os.path.join(V, f"rf_A1_none_{n.replace('|','_')}.csv"))))
pairs = (("pw|G73|rvR2fo_t08", "pw|G73|pcfR2fo"), ("pw|G73|rvR2L400_t08", "pw|G73|pcfR2L400"), ("pw|G73|rvR2L400k_t05", "pw|G73|pcfR2L400"),
         ("pw|G73|rvR2L400k_t05", "pw|G73|pcfR2k875"), ("pw|G73|rvR2L400k_t05", "pw|G73"), ("pw|G73|rvR2L400k_t08", "pw|G73|rvR2L400k_t05"))
for a, b in pairs:
    ra = lv(a); rb = lv(b) if b.startswith("pw|G73|rv") else load("A1_none", b)
    m = mcnemar(ok(rb), ok(ra))
    cols = [c for c in ra[0] if c in rb[0]]
    diffc = [c for c in cols if any(x[c] != y[c] for x, y in zip(ra, rb))]
    print(f"{a:22s} vs {b:20s}: {fmt(m)} | columns differing {len(diffc)}/{len(cols)}: {diffc[:8]}")
for n, rows in (("stored pcfR2fo t0.5 A1_none", load("A1_none", "pw|G73|pcfR2fo")), ("stored pcfR2fo t0.5 A1J_pc", load("A1J_pc", "pw|G73|pcfR2fo")),
                ("probe  rvR2fo_t08  A1_none", lv("pw|G73|rvR2fo_t08"))):
    fm = np.array([f(r, "pcf_Facc_max") for r in rows])
    print(f"{n}: Facc_max p50 {np.median(fm):.2f} p99 {np.percentile(fm, 99):.2f} max {fm.max():.2f} N | >=33 N {int(np.sum(fm >= 33.0))} | released {sum(f(r,'pcf_rel') > 0 for r in rows)}")
fa = np.array([f(r, "pcf_Facc_max") for r in load("A1_none", "pw|G73|pcfR2fo")]); fb = np.array([f(r, "pcf_Facc_max") for r in lv("pw|G73|rvR2fo_t08")])
print("per-run paired: t0.8 max - t0.5 max: >0 in", int(np.sum(fb > fa + 1e-9)), "runs; equal", int(np.sum(np.abs(fb - fa) <= 1e-9)), "; largest increase", round(float(np.max(fb - fa)), 2), "N")
