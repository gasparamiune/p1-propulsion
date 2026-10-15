"""M2 6-DOF Monte Carlo cases (sim6 v2.0, run6 v2.0).

For each case: size the N2O load on the deterministic nominal 6-DOF flight (20 % reserve), fly
N dispersed runs (brief C.7 dispersions, run6.draw) at the sized load x LOAD_MARGIN, record every run,
summarise (success vs vz <= 2, vh <= 0.5, tilt <= 5 deg, rate <= 10 deg/s, no exhaustion, no tip-over,
Wilson 95 % interval) and rank sensitivities (Spearman).

Env: GNC_MC_N (default 500), GNC_CASES (comma list, default all), GNC_SUFFIX (default v2),
GNC_OUT (default /home/claude/work/space/out/m2). Run: nice -n 10 python scripts/m2_mc6.py
"""
import csv
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
os.makedirs(OUT, exist_ok=True)
N = int(os.environ.get("GNC_MC_N", "500"))
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
LOAD_MARGIN = float(os.environ.get("GNC_LOAD_MARGIN", "1.15"))

# case name -> (config overrides, note)
CASES = {
    # baseline A-D (ballistic, nose drogue, relight) - fins vs finless
    "AD_fins_f20": (dict(profile="A-D", fins=True, floor=0.20), "baseline candidate: A-D + aft fins, 20 % floor, ADIS16470, PD lateral"),
    "AD_nofins_f20": (dict(profile="A-D", fins=False, floor=0.20), "A-D finless (coast tumble)"),
    # throttle floors (auto hover/hoverslam selection, T_floor > 0.9 W -> hoverslam)
    "AD_fins_f125": (dict(profile="A-D", fins=True, floor=0.125), "stretch floor 12.5 %"),
    "AD_fins_f25": (dict(profile="A-D", fins=True, floor=0.25), "requirement floor 25 % (auto -> hoverslam)"),
    "AD_fins_f40": (dict(profile="A-D", fins=True, floor=0.40), "40 % floor (hoverslam)"),
    "AD_fins_f20_hslam": (dict(profile="A-D", fins=True, floor=0.20, hslam=True), "forced Falcon-9-style hoverslam at 20 %"),
    "AD_fins_f40_ballast": (dict(profile="A-D", fins=True, floor=0.40, hslam=False, ballast=10.3),
                            "40 % floor, hover with 10.3 kg ballast (1-D ballast trade)"),
    "AD_fins_f25_ballast": (dict(profile="A-D", fins=True, floor=0.25, hslam=False, ballast=2.4),
                            "25 % floor, hover with 2.4 kg ballast"),
    # sensors
    "AD_fins_f20_BMI088": (dict(profile="A-D", fins=True, floor=0.20, imu="BMI088"), "cheaper IMU class (BMI088)"),
    "AD_fins_f20_ICM42688": (dict(profile="A-D", fins=True, floor=0.20, imu="ICM42688"), "cheaper IMU class (ICM-42688-P)"),
    "AD_fins_f20_rtk": (dict(profile="A-D", fins=True, floor=0.20, gnss="rtk"), "RTK GNSS"),
    "AD_fins_f20_lidar12": (dict(profile="A-D", fins=True, floor=0.20, lidar_range=12.0), "short-range LiDAR (12 m)"),
    # guidance comparison
    "AD_fins_f20_zemzev": (dict(profile="A-D", fins=True, floor=0.20, lat_mode=1, vert_mode=1), "ZEM/ZEV vertical + lateral"),
    "AD_fins_f20_cvx": (dict(profile="A-D", fins=True, floor=0.20, lat_mode=2), "reference+PI vertical, convex-lite lateral"),
    # roll
    "AD_fins_f20_rcs": (dict(profile="A-D", fins=True, floor=0.20, rcs=True), "roll RCS on"),
    # engine plant: open-loop pintle (fuel lag phi 0.1, tau_f 0.5 s)
    "AD_fins_f20_openloop": (dict(profile="A-D", fins=True, floor=0.20, fuel_phi=0.1, tau_fuel=0.5),
                             "open-loop pintle (fuel lag per combustion.json plant)"),
    # other profiles
    "AF_fins_f20": (dict(profile="A-F", fins=True, floor=0.20), "A-F freefall tail-first, relight ~130 m"),
    "B_f20": (dict(profile="B", fins=False, floor=0.20), "continuous-burn hop 100 m"),
    "B_f25": (dict(profile="B", fins=False, floor=0.25), "continuous-burn hop 100 m, 25 % floor"),
    "B_f125": (dict(profile="B", fins=False, floor=0.125), "continuous-burn hop 100 m, 12.5 % floor"),
}


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


def run_case(name, over, note, seed=101):
    t0 = time.time()
    cfg = R.cfg_of(**over)
    m_sized, res_nom = R.size_load(cfg)
    if m_sized is None:
        return dict(case=name, note=note, closes=False, nominal=res_nom), []
    m_mc = m_sized * LOAD_MARGIN
    cfg = R.cfg_of(**dict(over, m_n2o=m_mc))
    rng = np.random.default_rng(seed)
    D = R.draw(rng, N, cfg)
    rows = []
    for i, dr in enumerate(D):
        res = R.run_one(cfg, dr)
        rows.append(R.flat_row(i, dr, res, R.success(res)))
    s = R.summarize(rows)
    sens = R.sensitivity(rows)
    par, apar, comp, mp, tab, info = R.build(cfg)
    out = dict(case=name, note=note, closes=True, config={k: (v if not callable(v) else str(v)) for k, v in cfg.items()},
               m_n2o_sized_kg=m_sized, m_n2o_mc_kg=m_mc, tank_V_L=info["tank_V"] * 1e3,
               m_liftoff_kg=info["m_liftoff"], zcg0_m=info["zcg0"], z_pivot_m=info["z_pivot"],
               nominal=dict((k, float(v)) for k, v in res_nom.items()), summary=s, sensitivity=sens,
               cpu_s=time.time() - t0)
    return out, rows


def main():
    names = os.environ.get("GNC_CASES")
    names = names.split(",") if names else list(CASES)
    allsum = {}
    for name in names:
        over, note = CASES[name]
        out, rows = run_case(name, over, note)
        allsum[name] = out
        if rows:
            write_csv(os.path.join(OUT, f"mc6_runs_{name}_{SUFFIX}.csv"), rows)
            s = out["summary"]
            print(f"{name:24s} m_sized {out['m_n2o_sized_kg']:.3f} P {s['success']:.3f} "
                  f"[{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} "
                  f"vz99 {s['td_vz_p99']:.2f} vh99 {s['td_vh_p99']:.2f} tilt99 {s['td_tilt_p99']:.2f} "
                  f"rate99 {s['td_rate_p99']:.2f} miss50 {s['td_miss_p50']:.1f} ({out['cpu_s']:.0f}s)", flush=True)
        else:
            print(f"{name:24s} NO CLOSURE", flush=True)
        with open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json"), "w") as f:
            json.dump(dict(version=f"m2_mc6 {SUFFIX}", sim="sim6 v2.0", n=N, load_margin=LOAD_MARGIN,
                           criteria=R.CRIT, cases=allsum), f, indent=1, default=float)


if __name__ == "__main__":
    main()
