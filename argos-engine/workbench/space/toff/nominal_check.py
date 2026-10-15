"""Nominal (no wind, no noise) A-D flights on the dev tree: legacy shutdown vs lift-ramp tail-off vs pre-MECO
throttle-down; in-sim tail-off impulse vs the reduced-model reference (gncsim.tailoff.simulate)."""
import os, sys, json
sys.path.insert(0, "/home/claude/work/space/gnc_dev")
sys.path.insert(0, "/home/claude/work/space/gnc_dev/scripts")
import numpy as np
from gncsim import run6 as R, sim6 as s6, tailoff
import m2_mc6 as M

base = dict(M.BASE, rcs=False)
variants = {
    "legacy": {},
    "toff1": dict(toff_model=1),
    "toff1_td75": dict(toff_model=1, meco_td=0.75),
    "toff1_td72": dict(toff_model=1, meco_td=0.72),
    "toff1_td70": dict(toff_model=1, meco_td=0.70),
    "f125_legacy": dict(floor=0.125),
    "f125_td72": dict(floor=0.125, toff_model=1, meco_td=0.72),
    "f125_td72_rs20": dict(floor=0.125, toff_model=1, meco_td=0.72, relight_start=0.20),
}
comb = R.sources()["comb"]
chk, sha, _ = tailoff.load_checks(comb)
tl, tf, vs, tg = tailoff.table(chk, 0.25)
cal = tailoff.calibration(sha, 0.25)
for name, ov in variants.items():
    cfg = R.cfg_of(**dict(base, m_n2o=2.00, **ov))
    c = dict(cfg, noise=False, wind=0.0, gust=False)
    res, rec, info = R.fly(c, nrec=10)
    r = {k: float(res[k]) for k in s6.RES_NAMES}
    tsc = 1.0
    line = (f"{name:12s} hmax {r['h_max']:6.2f} t_meco {r['t_meco']:.3f} t_td {r['t_td_start']:.3f} F_meco {r['F_meco_cmd']:6.1f} "
            f"tail_imp {r['tailoff_imp']:6.2f} prop {r['prop_used']:.3f} liq {r['liq_left']:.3f} ok {R.success(res)} "
            f"vz {r['td_vz']:.2f} vh {r['td_vh']:.2f} t90rl {r['t90_relight']:.3f} Fst {r['F_start_cmd']:.0f} burn {r['burn_time']:.2f}")
    print(line)
    if r['F_meco_cmd'] > 0 and ov.get('toff_model'):
        t10, imp = tailoff.simulate(r['F_meco_cmd'], tl, tf, vs, cal['lag_a_s'], cal['lag_c_s'], cal['l_cut_mm'])
        print(f"   reference reduced model from F_meco {r['F_meco_cmd']:.1f} N: t10 {t10:.3f} s impulse {imp:.2f} N s")
    # sized load
    if os.environ.get("SIZE"):
        ms, rn = R.size_load(cfg)
        print(f"   sized load {ms:.4f} kg (nominal sizing flight hmax {float(rn['h_max']):.2f})")
