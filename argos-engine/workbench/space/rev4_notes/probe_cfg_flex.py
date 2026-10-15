"""probe (rev4, ENG-11): which actuator / mount / notch settings the rev3 decided flights use (gnc_dev3 m2_rev3_fly v1.1)."""
import json, os, sys
import numpy as np
T = "/home/claude/work/space/gnc_dev3"
sys.path.insert(0, T); sys.path.insert(0, T + "/scripts")
import m2_rev3_fly as RF
from m2_rev3_fly import F
from gncsim import run6 as R, sim6 as s6
keys = ("vehicle", "rock", "act_model", "servo_V", "act_n", "act_Jint", "supply_chain", "rock_K_eng", "eng_I_pivot_wet",
        "gim_notch_f", "gim_notch_q", "gim_notch_db", "gim_notch_track", "gim_notch_mis_w", "gim_lpf_w", "gim_cmd_acc",
        "att_ref_rate", "k_est_asc", "h_target", "ballast", "ballast_z", "rock_zeta", "hose_K")
for base in ("A1_none", "A1J_pc"):
    spec = RF.ARMS["liq|G73|h285"]
    cfg, m = F.base_cfg(base, "liq", RF.cfg_extra(spec, F.engine_bay_mid()[0]))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), 3, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    c, disp = F.MV.run_cfg_case(cfg, D[0], ms, 0, "base")
    c.update(F.DEC); c.update(F.PURGE["G73"])
    print(base, "m_n2o", m)
    print("  cfg:", {k: cfg.get(k) for k in keys if k in cfg})
    print("  c  :", {k: c.get(k) for k in keys if k in c})
    print("  disp keys rock:", {k: disp.get(k) for k in ("rock_K", "rock_zeta", "notch_mis", "hose_K")} if isinstance(disp, dict) else type(disp))
    print("  D[0] rock_K", D[0]["rock_K"], "kax range", R._kax_range(cfg))
    par, apar, comp, mp, tab, info = R.build(c, disp)
    names = s6.PAR_NAMES if hasattr(s6, "PAR_NAMES") else None
    tg = info["tags"]
    for k in ("rock_K", "rock_zeta", "act_model", "act_Jint", "gim_notch_f", "gim_notch_q", "gim_notch_db", "gim_lpf_w", "servo_V"):
        if k in tg: print("   tag", k, tg[k][0], "|", str(tg[k][1])[:150])
