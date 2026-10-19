"""M1 requirement sweeps on the 1-D model (v1.2 guidance): throttle 10-90 % time, slew, resolution,
ignition latency/repeatability (with propellant and relight-altitude cost), ballast/payload trade,
and Spearman sensitivity on the baseline cases.

Outputs to OUT (default /home/claude/work/space/out/m1): sweeps_<SUFFIX>.csv, ballast_trade_<SUFFIX>.csv,
sensitivity_<SUFFIX>.json, mc1d_runs_<profile>_floor20_<SUFFIX>.csv.
Run: nice -n 10 python scripts/m1_sweeps.py
"""
import csv
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import mc1d, sizing  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m1")
os.makedirs(OUT, exist_ok=True)
N = int(os.environ.get("GNC_MC_N", "500"))
NS = max(200, N // 2)
SUFFIX = os.environ.get("GNC_SUFFIX", "v1p2")
G0 = 9.80665
PROFILES = {
    "A_drogue_300m": dict(profile=0, h_target=300.0, descent="drogue", drogue_CdA=0.5, kd=0.6, t_ign_est=0.6),
    "A_freefall_300m": dict(profile=0, h_target=300.0, t_ign_est=0.6),
    "B_hop_100m": dict(profile=1, h_target=100.0),
}
# recommended loads (sized nominal + MC margin; see landing_closure_mc1d_*.json)
LOAD = {"A_drogue_300m": 1.30, "A_freefall_300m": 1.75, "B_hop_100m": 2.35}   # = sized nominal x ~1.15


def write_csv(path, rows):
    keys = []
    for x in rows:
        for k in x:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for x in rows:
            w.writerow(x)


def srow(pname, param, value, s, rows):
    return dict(profile=pname, param=param, value=value, n=s["n"], P=round(s["success"], 4),
                lo=round(s["ci95"][0], 4), hi=round(s["ci95"][1], 4), td_v_p01=round(s["td_v_p01"], 3),
                prop_used_mean_kg=round(float(np.mean([x["prop_used"] for x in rows])), 4),
                prop_used_p99_kg=round(float(np.percentile([x["prop_used"] for x in rows], 99)), 4),
                h_ign_mean_m=round(float(np.mean([x["h_ign"] for x in rows])), 2),
                exhausted=round(s["exhausted"], 4))


def main():
    t0 = time.time()
    sweep = []
    for pname, pk in PROFILES.items():
        for t1090 in [0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60]:
            s, rows = mc1d.run_mc(n=NS, floor=0.20, m_n2o=LOAD[pname], tau=t1090 / 2.197, seed=21, **pk)
            sweep.append(srow(pname, "t10_90_s", t1090, s, rows))
        for slew in [0.5, 1.0, 2.0, 5.0, 10.0]:
            s, rows = mc1d.run_mc(n=NS, floor=0.20, m_n2o=LOAD[pname], slew=slew, seed=22, **pk)
            sweep.append(srow(pname, "slew_Fmax_per_s", slew, s, rows))
        for q in [0.005, 0.01, 0.02, 0.05]:
            s, rows = mc1d.run_mc(n=NS, floor=0.20, m_n2o=LOAD[pname], quant=q, seed=23, **pk)
            sweep.append(srow(pname, "resolution_frac", q, s, rows))
        print(f"throttle sweeps {pname} done ({time.time()-t0:.0f}s)", flush=True)
    for pname in ["A_drogue_300m", "A_freefall_300m"]:
        pk = dict(PROFILES[pname])
        for mean in [0.3, 0.5, 0.8, 1.2]:
            for half in [0.0, 0.05, 0.1, 0.2, 0.3]:
                lo, hi = max(0.05, mean - half), mean + half
                pk["t_ign_est"] = hi       # plan on the latest ignition (conservative CONOPS)
                s, rows = mc1d.run_mc(n=NS, floor=0.20, m_n2o=LOAD[pname], ign_lo=lo, ign_hi=hi, seed=31, **pk)
                sweep.append(srow(pname, f"ign_mean{mean}_halfwidth", half, s, rows))
        print(f"ignition sweep {pname} done ({time.time()-t0:.0f}s)", flush=True)
    write_csv(os.path.join(OUT, f"sweeps_{SUFFIX}.csv"), sweep)
    # ballast / payload trade at the 20 % floor (sized nominal load, 20 % reserve)
    brow = []
    for pname, pk in PROFILES.items():
        base = None
        for b in [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 11.0, 15.0]:
            out = sizing.size(pk["profile"], pk["h_target"], 0.20, ballast=b,
                              **{k: v for k, v in pk.items() if k not in ("profile", "h_target")})
            if out is None:
                brow.append(dict(profile=pname, ballast_kg=b, closes=False))
                continue
            o, rec = out
            if base is None:
                base = o
            brow.append(dict(profile=pname, ballast_kg=b, closes=True, m_n2o_kg=round(o["m_n2o"], 3),
                             tank_V_L=round(o["tank_V"] * 1e3, 3), prop_used_kg=round(o["prop_used"], 3),
                             m_liftoff_kg=round(o["m_liftoff"], 2), m_land_kg=round(o["m_land"], 2),
                             TW_liftoff=round(500 / (o["m_liftoff"] * G0), 2),
                             T_floor_over_W_land=round(100.0 / (o["m_land"] * G0), 3),
                             dprop_per_kg_ballast=round((o["prop_used"] - base["prop_used"]) / b, 4) if b > 0 else 0.0,
                             dn2o_per_kg_ballast=round((o["m_n2o"] - base["m_n2o"]) / b, 4) if b > 0 else 0.0))
        print(f"ballast {pname} done ({time.time()-t0:.0f}s)", flush=True)
    write_csv(os.path.join(OUT, f"ballast_trade_{SUFFIX}.csv"), brow)
    keys = ['thrust_scale', 'isp_scale', 't_ign', 'tau_f', 'dry_scale', 'T0', 'h_bias', 'v_bias', 'm_est_err',
            'ca_tf_f', 'drogue_f', 'a_bias']
    sens = {}
    for pname in PROFILES:
        for fl in [0.20, 0.25]:
            s, rows = mc1d.run_mc(n=N, floor=fl, m_n2o=LOAD[pname], seed=41, **PROFILES[pname])
            sens[f"{pname}|floor={fl}"] = dict(P=s["success"], ci95=s["ci95"], spearman=mc1d.sensitivity(rows, keys))
            if fl == 0.20:
                write_csv(os.path.join(OUT, f"mc1d_runs_{pname}_floor20_{SUFFIX}.csv"), rows)
    with open(os.path.join(OUT, f"sensitivity_{SUFFIX}.json"), "w") as f:
        json.dump(dict(version=f"m1_sweeps {SUFFIX}", loads_kg=LOAD, n=N, keys=keys,
                       note="Spearman rank correlation of each dispersion with |touchdown velocity| and with failure",
                       cases=sens, cpu_s=time.time() - t0), f, indent=1, default=float)
    print("done", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
