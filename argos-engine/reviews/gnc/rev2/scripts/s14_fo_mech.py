import sys, csv, os; sys.path.insert(0, "."); from rvlib import *
import numpy as np
V = os.environ["RV_VOUT"]
rb = list(csv.DictReader(open(os.path.join(V, "rf_A1_none_pw_G73_rvR2fo_t08.csv"))))
ra = load("A1_none", "pw|G73|pcfR2fo")
fa = np.array([f(r, "pcf_Facc_max") for r in ra]); fb = np.array([f(r, "pcf_Facc_max") for r in rb])
d = fb - fa
idx = np.argsort(-d)[:8]
cols = ["run", "pcf_t0", "pcf_fz0", "wind", "gust_scale", "drogue_f", "m_est_err", "a_bias_h", "start_delay", "rel_t", "td_vz", "h_ign", "pgg_hE0"]
for i in idx:
    print(f"run {i}: max t0.5 {fa[i]:.2f} -> t0.8 {fb[i]:.2f} | " + " ".join(f"{c} {rb[i].get(c, 'NA')[:8]}" for c in cols[1:]))
w = np.array([f(r, "wind") for r in rb]); g = np.array([f(r, "gust_scale") for r in rb])
inc = d > 1e-9
print("runs with increase:", int(inc.sum()), "| wind mean inc/no-inc", round(w[inc].mean(), 2), round(w[~inc].mean(), 2), "| gust_scale mean", round(g[inc].mean(), 2), round(g[~inc].mean(), 2))
print("corr(d, wind)", round(float(np.corrcoef(d, w)[0, 1]), 3), "corr(fb, wind)", round(float(np.corrcoef(fb, w)[0, 1]), 3), "corr(fa, wind)", round(float(np.corrcoef(fa, w)[0, 1]), 3))
for lab, x in (("t0.5", fa), ("t0.8", fb)):
    for wl in (6.0, 8.1):
        m = w < wl
        print(f"{lab} wind<{wl}: n {int(m.sum())} Facc_max max {x[m].max():.2f} p99 {np.percentile(x[m], 99):.2f} N")
