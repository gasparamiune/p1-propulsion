"""M1 landing-closure Monte Carlo, corrected re-run (v1.1) of m1_landing_mc.py v1.

Why v1.1 (failures of v1 kept as evidence in landing_closure_mc1d_v1.*):
  * v1 recorded the *commanded* landing mode (-1 = auto) instead of the mode actually flown, so
    'hoverslam_fraction' read 0 for auto cases. sim1d now returns the flown mode (res[20]).
  * v1 used fixed N2O loads per profile; the hop (B) load 1.90 kg was below its own nominal
    sizing (2.06 kg at 20 % floor, 20 % reserve) and the 40 % + ballast loads were a heuristic
    (+10 %/kg) far below the sized need -> exhaustion. v1.1 sizes every case first
    (sizing.size: nominal flight, usable liquid >= 20 % of liquid used) and runs the MC at that load.
Cases: floors 12.5/20/25/40 % x {A_drogue, A_freefall, B_hop} with
   mode = auto (flight software picks hoverslam when T_floor > 0.9 W_est at the descent trigger),
   forced hover-capable (only where feasible) and forced hoverslam (A profiles),
   and 'hover with ballast' (ballast bringing T_floor <= 0.9 W_land, sized load).
Run: nice -n 10 python scripts/m1_landing_mc_v1p1.py   (GNC_SUFFIX=v1p2 for the v1.2 guidance)
v1.2 (same script, GNC_SUFFIX=v1p2): guidance defaults changed in run1d.make_par after the v1.1
failure analysis: accelerometer-based thrust-effectiveness estimator (tau 0.1 s), hoverslam terminal
margin 3.0 m/s2, and the hoverslam 'stopping' cut no longer requires h_nav > 0.03 m.
"""
import csv
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import mc1d, sizing, run1d as r  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m1")
os.makedirs(OUT, exist_ok=True)
N = int(os.environ.get("GNC_MC_N", "500"))
SUFFIX = os.environ.get("GNC_SUFFIX", "v1p1")
LOAD_MARGIN = float(os.environ.get("GNC_LOAD_MARGIN", "1.0"))   # MC load = sized nominal load x margin
G0 = 9.80665
FLOORS = [0.125, 0.20, 0.25, 0.40]
PROFILES = {
    "A_drogue_300m": dict(profile=0, h_target=300.0, descent="drogue", drogue_CdA=0.5, kd=0.6, t_ign_est=0.6),
    "A_freefall_300m": dict(profile=0, h_target=300.0, t_ign_est=0.6),
    "B_hop_100m": dict(profile=1, h_target=100.0),
}


def sized_load(pk, floor, ballast=0.0, hslam=None):
    kw = {k: v for k, v in pk.items() if k not in ("profile", "h_target")}
    if hslam is not None:
        kw["hslam"] = hslam
    out = sizing.size(pk["profile"], pk["h_target"], floor, ballast=ballast, **kw)
    if out is None:
        return None, None
    o, rec = out
    return o, rec


def case_row(tag, pname, floor, mode, ballast, o, s, rows):
    return dict(case=tag, profile=pname, floor=floor, mode=mode, ballast_kg=round(ballast, 3),
                m_n2o_sized_kg=round(o["m_n2o"], 3) if o else None,
                m_n2o_mc_kg=round(o["m_n2o"] * LOAD_MARGIN, 3) if o else None,
                m_liftoff_kg=round(o["m_liftoff"], 2) if o else None,
                m_land_nom_kg=round(o["m_land"], 2) if o else None,
                n=s["n"], P_success=round(s["success"], 4), ci_lo=round(s["ci95"][0], 4),
                ci_hi=round(s["ci95"][1], 4), td_v_mean=round(s["td_v_mean"], 3),
                td_v_p01=round(s["td_v_p01"], 3), td_v_p99=round(s["td_v_p99"], 3),
                exhausted=round(s["exhausted"], 4),
                hoverslam_fraction=round(float(np.mean([x["hslam_used"] for x in rows])), 3),
                cut_fraction=round(float(np.mean([x["cut"] for x in rows])), 3),
                prop_used_mean_kg=round(float(np.mean([x["prop_used"] for x in rows])), 3),
                usable_liquid_p05_kg=round(s["margin_p05"], 3),
                v_ign_mean=round(float(np.mean([x["v_ign"] for x in rows])), 2),
                h_ign_mean=round(float(np.mean([x["h_ign"] for x in rows])), 2))


def main():
    t0 = time.time()
    out_rows = []
    for pname, pk in PROFILES.items():
        for fl in FLOORS:
            modes = [("auto", None)]
            if pk["profile"] == 0:
                modes += [("forced_hover", False), ("forced_hoverslam", True)]
            o_auto = None
            for mode, hs in modes:
                tag = f"{pname}|floor={fl}|mode={mode}"
                if mode == "forced_hover" and o_auto is not None and fl * 500.0 > 0.9 * o_auto["m_land"] * G0:
                    # hover-capable guidance is not physically available: T_floor > 0.9 W_land (RV-1)
                    out_rows.append(dict(case=tag, profile=pname, floor=fl, mode=mode, ballast_kg=0.0, n=0,
                                         P_success=None, note="infeasible: T_floor > 0.9 W_land (no ballast)"))
                    print(tag, "skipped (infeasible by the 0.9 W rule)", flush=True)
                    continue
                o, rec = sized_load(pk, fl, hslam=hs)
                if mode == "auto":
                    o_auto = o
                if o is None:
                    out_rows.append(dict(case=tag, profile=pname, floor=fl, mode=mode, ballast_kg=0.0,
                                         m_n2o_sized_kg=None, n=0, P_success=0.0,
                                         note="does not close nominally with <= 6 kg N2O"))
                    print(tag, "no nominal closure", flush=True)
                    continue
                s, rows = mc1d.run_mc(n=N, floor=fl, m_n2o=o["m_n2o"] * LOAD_MARGIN, seed=11, hslam=hs, **pk)
                out_rows.append(case_row(tag, pname, fl, mode, 0.0, o, s, rows))
                print(f"{tag}: load {o['m_n2o']:.3f} kg P={s['success']:.3f} hs={out_rows[-1]['hoverslam_fraction']}"
                      f" ({time.time()-t0:.0f}s)", flush=True)
        # hover with ballast (T_floor <= 0.9 W_land) at the floors where RV-1 cannot hover
        for fl in [0.25, 0.40]:
            o0, _ = sized_load(pk, fl, hslam=False)
            m_land0 = o0["m_land"] if o0 else (r.make_par(**pk)[r.s.I_M_DRY] + 0.5)
            m_req = fl * 500.0 / (0.9 * G0)
            b = 0.0
            for _it in range(4):          # landing mass depends on the sized load: iterate
                b = max(0.0, 1.03 * (m_req - m_land0) + b) if _it == 0 else b + 1.03 * (m_req - m_land0)
                o, rec = sized_load(pk, fl, ballast=b, hslam=False)
                if o is None:
                    break
                m_land0 = o["m_land"]
                if m_land0 >= m_req:
                    break
            tag = f"{pname}|floor={fl}|mode=hover_with_ballast"
            if o is None:
                out_rows.append(dict(case=tag, profile=pname, floor=fl, mode="hover_with_ballast",
                                     ballast_kg=round(b, 3), n=0, P_success=0.0,
                                     note="does not close nominally with <= 6 kg N2O"))
                print(tag, "no closure", flush=True)
                continue
            s, rows = mc1d.run_mc(n=N, floor=fl, m_n2o=o["m_n2o"] * LOAD_MARGIN, ballast=b, seed=11, hslam=False, **pk)
            out_rows.append(case_row(tag, pname, fl, "hover_with_ballast", b, o, s, rows))
            print(f"{tag}: ballast {b:.2f} load {o['m_n2o']:.3f} P={s['success']:.3f} ({time.time()-t0:.0f}s)",
                  flush=True)
    keys = []
    for x in out_rows:
        for k in x:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(OUT, f"landing_closure_mc1d_{SUFFIX}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for x in out_rows:
            w.writerow(x)
    with open(os.path.join(OUT, f"landing_closure_mc1d_{SUFFIX}.json"), "w") as f:
        json.dump(dict(version=f"m1_landing_mc {SUFFIX}", date="2026-10-11", n_runs_per_case=N,
                       model="gncsim.sim1d (1-D vertical)", dispersions=mc1d.__doc__,
                       sizing_rule="nominal flight; usable liquid >= 20 % of liquid used; fill <= 85 % at 25 C",
                       load_margin_in_mc=LOAD_MARGIN,
                       cases=out_rows, cpu_s=time.time() - t0), f, indent=1, default=float)
    print("done", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
