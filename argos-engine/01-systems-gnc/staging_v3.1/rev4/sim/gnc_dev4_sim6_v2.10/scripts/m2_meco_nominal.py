"""m2_meco_nominal v1 (2026-10-12): nominal (no wind, no sensor noise) A-D flights on the lead tank (2.00 kg, no roll
RCS) for the shutdown / MECO / relight rules of sim6 v2.6, with the in-sim tail-off impulse checked against the reduced
model (gncsim.tailoff.simulate) from the same MECO thrust.
Variants: v2.5 shutdown (first-order, MECO from 100 %), lift-ramp tail-off from 100 % (fails ENG-05 by design),
throttle-down commands 75 % (kept as evidence: commanding exactly the 75 % gate never satisfies it with a first-order
thrust response, so MECO waits for the waiver and overshoots the apogee target), 72 % (baseline rule) and 70 %; the
12.5 % floor with a floor start and with the 20 % relight start rule.
Env: GNC_OUT (default out/meco), GNC_SUFFIX (default mr), GNC_SIZE=1 also sizes the load. Output <out>/meco_nominal_<suf>.json"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6, tailoff  # noqa: E402
import m2_mc6 as M  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/meco")
SUF = os.environ.get("GNC_SUFFIX", "mr")
VARIANTS = {
    "v2.5_shutdown": {},
    "toff_from_100": dict(toff_model=1),
    "toff_td75_evidence": dict(toff_model=1, meco_td=0.75),
    "toff_td72_rule": dict(toff_model=1, meco_td=0.72),
    "toff_td70": dict(toff_model=1, meco_td=0.70),
    "f125_v2.5": dict(floor=0.125),
    "f125_td72_floorstart": dict(floor=0.125, toff_model=1, meco_td=0.72),
    "f125_td72_rs20": dict(floor=0.125, toff_model=1, meco_td=0.72, relight_start=0.20),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    comb = R.sources()["comb"]
    chk, sha, path = tailoff.load_checks(comb)
    tl, tf, vs, tg = tailoff.table(chk, 0.25)
    cal = tailoff.calibration(sha, 0.25)
    rows = {}
    for name, ov in VARIANTS.items():
        cfg = R.cfg_of(**dict(M.BASE, rcs=False, m_n2o=2.00, **ov))
        res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False), nrec=10)
        r = {k: float(res[k]) for k in ("h_max", "t_meco", "F_meco_cmd", "tailoff_imp", "prop_used", "liq_left", "td_vz",
                                         "td_vh", "t90_relight", "F_start_cmd", "burn_time", "h_ign", "v_ign")}
        r["landed_ok"] = R.success(res)
        if r["F_meco_cmd"] > 0 and ov.get("toff_model"):
            t10, imp = tailoff.simulate(r["F_meco_cmd"], tl, tf, vs, cal["lag_a_s"], cal["lag_c_s"], cal["l_cut_mm"])
            r["reduced_model_t10_s"] = t10
            r["reduced_model_impulse_Ns"] = imp
            r["ENG05_pass"] = bool(t10 <= 0.100)
        if os.environ.get("GNC_SIZE"):
            ms, rn = R.size_load(cfg)
            r["sized_load_kg"] = ms
        rows[name] = r
        print(f"{name:22s} " + " ".join(f"{k} {v:.3f}" if isinstance(v, float) else f"{k} {v}" for k, v in r.items()), flush=True)
    out = dict(version=f"m2_meco_nominal v1 {SUF}", sim=s6.SIM6_VERSION, actuator_rate_check=dict(path=path, sha256=sha),
               calibration=cal, apogee_target_m=R.cfg_of(**dict(M.BASE))["h_target"], rows=rows)
    with open(os.path.join(OUT, f"meco_nominal_{SUF}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
