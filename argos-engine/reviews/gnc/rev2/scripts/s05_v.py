import sys; sys.path.insert(0, ".")
from rvlib import *
import numpy as np
def q(x, ps=(0,1,5,50,95,99,100)):
    x = np.asarray(x, float); return " ".join(f"p{p:02d}={np.percentile(x,p):.3f}" for p in ps)
for arm in ("pcfR1", "pcfR2", "pcfR2k875", "pcfR2L400", "pcfR1L400", "pcfR1k875", "pcfR2fo", "pcfR1fo", "pcfR3fo", "pcfR3", "pcfR0"):
    for b in ("A1_none", "A1J_pc"):
        r = load(b, "pw|G73|" + arm)
        o = np.array(ok(r)); rel = np.array([f(x, "pcf_rel") for x in r]); abt = np.array([f(x, "pcf_abt") for x in r])
        relt = np.array([f(x, "pcf_relt") for x in r]); fmx = np.array([f(x, "pcf_Facc_max") for x in r])
        relt_all = np.array([f(x, "rel_t") for x in r]); tdvz = np.array([f(x, "td_vz") for x in r])
        fz0 = np.array([f(x, "pcf_fz0") for x in r])
        s = f"{b:8s} {arm:10s} P {o.mean():.3f} rel_int {int(np.sum(rel==1))} rel_acc {int(np.sum(rel==2))} abt {int(np.sum(abt>0.5))} norel {int(np.sum(relt_all<0))}"
        if np.any(relt >= 0): s += f" | relt[ms] {q(1e3*relt[relt>=0], (0,50,99,100))}"
        s += f" | Facc_max {q(fmx, (0,1,50,99,100))}"
        if arm.endswith("fo"): s += f" | td_vz {q(tdvz,(1,50,99))}"
        print(s)
