"""p6_hold_profile_probe v1.0 (GNC rev3, 2026-10-13): which post-E2 command profile does sim6 v2.10-dev fly during the release
hold of the unpurged-relight alternative (nrLO|none|rh<H>|h285)? Flies runs 0-4 of A1_none with full records and prints the
ECU command and truth thrust from the light to the release (lead line 194 (3): the admissible hold depends on that profile)."""
import os, sys
import numpy as np
sys.path.insert(0, "/home/claude/work/space/gnc_dev4"); sys.path.insert(0, "/home/claude/work/space/gnc_dev4/scripts")
import m2_rev3_fly as RF
import m2_rg01_refly as F
from gncsim import run6 as R, sim6 as s6
name = os.environ.get("ARM", "nrLO|none|rh220|h285")
spec = RF.ARMS[name]
cfg, m = F.base_cfg("A1_none", spec["state"], RF.cfg_extra(spec, F.engine_bay_mid()[0]))
jr = __import__("json").load(open(F.TG))["j_ref"]
F.MV.TG_JREF_DEFAULT = float(jr["A1"])
D = R.draw(np.random.default_rng(101), F.N, cfg)
ms = F.MV.case_specs()["tot_cal_comp"]
iT, iF, iFc, iph, iz, ivz = (s6.REC_NAMES.index(k) for k in ("t", "F", "Fcmd", "phase", "z", "vz"))
for i in range(int(os.environ.get("NRUN", "5"))):
    c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
    c.update(F.DEC); c.update(F.PURGE[spec["purge"]]); c.update(F.PLAT[spec["plat"]]); c.update(spec.get("gex") or {})
    res, rec, info = R.fly(c, disp, nrec=6000)
    t = rec[:, iT]
    j = np.where((t >= res["t_relight"]) & (rec[:, iF] > 1.0))[0]
    tl = t[j[0]] if len(j) else res["t_relight"]   # light (E2) = first record after the relight command with truth thrust > 1 N
    rel = res["rel_t"]
    sel = (t >= tl - 0.05) & (t <= tl + max(rel, 0.0) + 0.15)
    print(f"run {i}: ok {R.success(res)} t_relight {res['t_relight']:.3f} light {tl:.3f} rel_t {rel:.3f} "
          f"F_start_cmd {res['F_start_cmd']:.1f} h_ign {res['h_ign']:.1f} v_ign {res['v_ign']:.2f}")
    for k in np.where(sel)[0][::2]:
        print(f"   t-tl {t[k]-tl:+.3f} Fcmd {rec[k, iFc]:7.1f} F {rec[k, iF]:7.1f} phase {rec[k, iph]:.0f} z {rec[k, iz]:6.1f} vz {rec[k, ivz]:6.2f}")
