import sys; sys.path.insert(0, "."); from rvlib import *
import numpy as np
bases = ("A1_none", "A1J_pc", "A1_pc", "A1J_none")
R = []
for b in bases:
    r = load(b, "e19|G73")
    if r is None: print("missing", b); continue
    R += r
def c(k): return np.array([f(r, k) for r in R])
src, h0, hop, top, t0, aq, sp, hE0, fl, pm, tgo = (c(k) for k in ("pgg_src", "pgg_h0", "pgg_hopen", "pgg_topen", "pgg_t0", "pgg_aqmax", "pgg_spur", "pgg_hE0", "pgg_fl", "prg_mass", "pgg_tgo"))
print("runs", len(R), "| pgg_src values", {v: int(np.sum(src == v)) for v in np.unique(src)})
print("commit height min/max", h0.min().round(1), h0.max().round(1), "| gate open height min/max", hop.min().round(1), hop.max().round(1))
g2c = t0 - top
print("gate->commit min / p01", g2c.min().round(2), np.percentile(g2c, 1).round(2), "| aqmax p99/max", np.percentile(aq, 99).round(2), aq.max().round(2), "| spurious", int(np.sum(sp > 0.5)))
print("E0 height p50/min", np.median(hE0).round(1), hE0.min().round(1), "| flow min", fl.min().round(3), "| purge mass g min/max", (1e3 * pm.min()).round(1), (1e3 * pm.max()).round(1))
lead = np.where(tgo >= 0, tgo - t0, np.nan)
print("plain trigger fired in", int(np.sum(tgo >= 0)), "runs; min lead commit->plain trigger", np.nanmin(lead).round(2))
