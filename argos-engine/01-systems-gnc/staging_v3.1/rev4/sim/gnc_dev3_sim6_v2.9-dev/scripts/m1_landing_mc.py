"""M1 first-pass landing-closure Monte Carlo on the 1-D model (floors, modes, ballast, sweeps).

Outputs (JSON + CSV) to OUT/m1/. Run: nice -n 10 python scripts/m1_landing_mc.py
Brief items: ENG-02 rev1 floors 12.5/20/25/40 %, Falcon-9-style hoverslam vs hover-capable,
ballast trade, throttle response / slew / resolution sweeps, ignition latency/repeatability sweeps.
"""
import json
import os
import sys
import time
import csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import mc1d, sizing, run1d as r  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m1")
os.makedirs(OUT, exist_ok=True)
N = int(os.environ.get("GNC_MC_N", "500"))
G0 = 9.80665
FLOORS = [0.125, 0.20, 0.25, 0.40]
PROFILES = {
    "A_drogue_300m": dict(profile=0, h_target=300.0, descent="drogue", drogue_CdA=0.5, kd=0.6, t_ign_est=0.6),
    "A_freefall_300m": dict(profile=0, h_target=300.0, t_ign_est=0.6),
    "B_hop_100m": dict(profile=1, h_target=100.0),
}
M_N2O = {"A_drogue_300m": 1.30, "A_freefall_300m": 1.90, "B_hop_100m": 1.90}


def summarize(tag, s, rows):
    keep = {k: (float(v) if not isinstance(v, tuple) else [float(x) for x in v]) for k, v in s.items()}
    keep["case"] = tag
    keep["hoverslam_fraction"] = float(np.mean([x["hslam_used"] == 1.0 for x in rows]))
    return keep


def write_csv(path, rows):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for x in rows:
            w.writerow({k: x[k] for k in keys})


def main():
    t0 = time.time()
    results = {"version": "m1_landing_mc v1", "date": "2026-10-11", "n_runs_per_case": N,
               "model": "gncsim.sim1d 1-D vertical (6-DOF supersedes for lateral/tilt)",
               "dispersions": mc1d.__doc__, "cases": []}
    # ---- 1. floors x profiles x landing mode (auto = flight-software choice) + forced hoverslam
    for pname, pk in PROFILES.items():
        for fl in FLOORS:
            s, rows = mc1d.run_mc(n=N, floor=fl, m_n2o=M_N2O[pname], seed=11, **pk)
            results["cases"].append(summarize(f"{pname}|floor={fl}|mode=auto", s, rows))
            if fl <= 0.20 and pname != "B_hop_100m":
                s2, rows2 = mc1d.run_mc(n=N, floor=fl, m_n2o=M_N2O[pname], seed=11, hslam=True, **pk)
                results["cases"].append(summarize(f"{pname}|floor={fl}|mode=forced_hoverslam", s2, rows2))
            print(f"{pname} floor {fl}: P={s['success']:.3f}  ({time.time()-t0:.0f}s)", flush=True)
    # ---- 2. ballast making the floor hover-capable (T_floor <= 0.9 W_land)
    ballast_rows = []
    for pname in ["A_drogue_300m", "A_freefall_300m", "B_hop_100m"]:
        pk = PROFILES[pname]
        base = None
        for b in [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 11.0]:
            out = sizing.size(pk["profile"], pk["h_target"], 0.20, ballast=b,
                              **{k: v for k, v in pk.items() if k not in ("profile", "h_target")})
            if out is None:
                ballast_rows.append(dict(profile=pname, ballast_kg=b, closes=False))
                continue
            o, rec = out
            if base is None:
                base = o
            ballast_rows.append(dict(profile=pname, ballast_kg=b, closes=True, m_n2o_kg=round(o["m_n2o"], 3),
                                     prop_used_kg=round(o["prop_used"], 3), m_liftoff_kg=round(o["m_liftoff"], 2),
                                     m_land_kg=round(o["m_land"], 2),
                                     TW_liftoff=round(500 / (o["m_liftoff"] * G0), 2),
                                     dprop_per_kg_ballast=round((o["prop_used"] - base["prop_used"]) / b, 4) if b > 0 else 0.0,
                                     dn2o_per_kg_ballast=round((o["m_n2o"] - base["m_n2o"]) / b, 4) if b > 0 else 0.0))
    write_csv(os.path.join(OUT, "ballast_trade_v1.csv"), ballast_rows)
    results["ballast_trade"] = ballast_rows
    # MC with ballast for 25 % and 40 % floors (hover-capable after ballast)
    for pname in ["A_drogue_300m", "A_freefall_300m"]:
        pk = PROFILES[pname]
        for fl in [0.25, 0.40]:
            m_req = fl * 500.0 / (0.9 * G0)
            par = r.make_par(**{k: v for k, v in pk.items()}, floor=fl, m_n2o=M_N2O[pname])
            m_land_nom = par[r.s.I_M_DRY] + 0.30 + 0.2    # dry + unburnt fuel + residual N2O (approx.)
            b = max(0.0, m_req - m_land_nom) * 1.05
            mload = M_N2O[pname] * (1 + 0.10 * b)
            s, rows = mc1d.run_mc(n=N, floor=fl, m_n2o=mload, ballast=b, seed=11, hslam=False, **pk)
            c = summarize(f"{pname}|floor={fl}|mode=hover_with_ballast|ballast={b:.2f}kg", s, rows)
            c["ballast_kg"] = b
            results["cases"].append(c)
            print(f"{pname} floor {fl} ballast {b:.2f}: P={s['success']:.3f}", flush=True)
    # ---- 3. throttle response sweep (10-90 % time), slew and resolution
    sweep = []
    for pname in ["A_drogue_300m", "A_freefall_300m", "B_hop_100m"]:
        pk = PROFILES[pname]
        for t1090 in [0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60]:
            s, rows = mc1d.run_mc(n=max(200, N // 2), floor=0.20, m_n2o=M_N2O[pname], tau=t1090 / 2.197, seed=21, **pk)
            sweep.append(dict(profile=pname, param="t10_90_s", value=t1090, P=s["success"], lo=s["ci95"][0],
                              hi=s["ci95"][1], td_v_p01=s["td_v_p01"]))
        for slew in [0.5, 1.0, 2.0, 5.0, 10.0]:
            s, rows = mc1d.run_mc(n=max(200, N // 2), floor=0.20, m_n2o=M_N2O[pname], slew=slew, seed=22, **pk)
            sweep.append(dict(profile=pname, param="slew_Fmax_per_s", value=slew, P=s["success"], lo=s["ci95"][0],
                              hi=s["ci95"][1], td_v_p01=s["td_v_p01"]))
        for q in [0.005, 0.01, 0.02, 0.05]:
            s, rows = mc1d.run_mc(n=max(200, N // 2), floor=0.20, m_n2o=M_N2O[pname], quant=q, seed=23, **pk)
            sweep.append(dict(profile=pname, param="resolution_frac", value=q, P=s["success"], lo=s["ci95"][0],
                              hi=s["ci95"][1], td_v_p01=s["td_v_p01"]))
        print(f"sweeps {pname} done ({time.time()-t0:.0f}s)", flush=True)
    # ---- 4. ignition latency / repeatability (relight profiles only)
    for pname in ["A_drogue_300m", "A_freefall_300m"]:
        pk = dict(PROFILES[pname])
        for mean in [0.3, 0.5, 0.8, 1.2]:
            for half in [0.0, 0.05, 0.1, 0.2, 0.3]:
                lo, hi = max(0.05, mean - half), mean + half
                pk["t_ign_est"] = hi       # plan on the latest ignition (conservative CONOPS)
                s, rows = mc1d.run_mc(n=max(200, N // 2), floor=0.20, m_n2o=M_N2O[pname], ign_lo=lo, ign_hi=hi,
                                      seed=31, **pk)
                sweep.append(dict(profile=pname, param=f"ign_mean{mean}_halfwidth", value=half, P=s["success"],
                                  lo=s["ci95"][0], hi=s["ci95"][1], td_v_p01=s["td_v_p01"]))
        print(f"ignition sweep {pname} done ({time.time()-t0:.0f}s)", flush=True)
    write_csv(os.path.join(OUT, "throttle_ignition_sweeps_v1.csv"), sweep)
    results["sweeps"] = sweep
    # sensitivity on the baseline case
    keys = ['thrust_scale', 'isp_scale', 't_ign', 'tau_f', 'dry_scale', 'T0', 'h_bias', 'v_bias', 'm_est_err',
            'ca_tf_f', 'drogue_f']
    sens = {}
    for pname in PROFILES:
        s, rows = mc1d.run_mc(n=N, floor=0.20, m_n2o=M_N2O[pname], seed=41, **PROFILES[pname])
        sens[pname] = mc1d.sensitivity(rows, keys)
        write_csv(os.path.join(OUT, f"mc1d_runs_{pname}_floor20_v1.csv"), rows)
    results["sensitivity_spearman"] = sens
    results["cpu_s"] = time.time() - t0
    with open(os.path.join(OUT, "landing_closure_mc1d_v1.json"), "w") as f:
        json.dump(results, f, indent=1, default=float)
    case_rows = [dict(case=c["case"], P_success=round(c["success"], 4), ci_lo=round(c["ci95"][0], 4),
                      ci_hi=round(c["ci95"][1], 4), td_v_mean=round(c["td_v_mean"], 3), td_v_p01=round(c["td_v_p01"], 3),
                      exhausted=round(c["exhausted"], 4), hoverslam_fraction=round(c["hoverslam_fraction"], 3),
                      usable_liquid_p05_kg=round(c["margin_p05"], 3)) for c in results["cases"]]
    write_csv(os.path.join(OUT, "landing_closure_mc1d_v1.csv"), case_rows)
    print("done", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
