"""IMU requirement sweep (gnc.json v2): landing success vs the residual gyro bias of the IMU, everything else at the
ADIS16470 class, baseline RV-1c A-D flight. The estimator propagates attitude from the gyros with no in-flight
attitude aiding (sim6 v2.2), so the residual bias integrates over the ~30 s flight; the sweep sets the gyro
residual-bias requirement for that estimator. Also: BMI088 class with only the gyro bias reduced to the ADIS value
(isolates the bias from the noise / accelerometer terms).

Output: GNC_RES/imu_sweep_v2.json/.csv. Run: nice -n 10 python scripts/m2_imu_sweep.py  (GNC_IMU_N runs per point)
"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
N = int(os.environ.get("GNC_IMU_N", "300"))
os.makedirs(RES, exist_ok=True)


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")))
    m_mc = S["cases"]["AD_fins_f20"]["m_n2o_mc_kg"]
    base = R.IMU["ADIS16470"]
    pts = []
    for gb in (0.015, 0.03, 0.045, 0.06, 0.09, 0.125):
        name = f"ADIS_gbias_{gb:.3f}"
        R.IMU[name] = dict(base, g_bias=np.radians(gb), tag=f"ADIS16470 class with residual gyro bias {gb} deg/s (sweep)")
        pts.append((name, gb))
    R.IMU["BMI088_gbias_ADIS"] = dict(R.IMU["BMI088"], g_bias=base["g_bias"],
                                      tag="BMI088 class with the ADIS16470 residual gyro bias (isolation case)")
    pts.append(("BMI088_gbias_ADIS", np.degrees(base["g_bias"])))
    rows = []
    for name, gb in pts:
        cfg = R.cfg_of(profile="A-D", fins=True, floor=0.20, imu=name, m_n2o=m_mc)
        rng = np.random.default_rng(101)
        D = R.draw(rng, N, cfg)
        ok = 0
        vh = []
        crash = 0
        for dr in D:
            res = R.run_one(cfg, dr)
            s = R.success(res)
            ok += s
            crash += int(res["crash"] > 0.5 or res["landed"] < 0.5)
            if res["landed"] > 0.5:
                vh.append(res["td_vh"])
        lo, hi = R.wilson(ok, N)
        r = dict(imu=name, gyro_residual_bias_dps=gb, n=N, success=ok / N, ci95_lo=lo, ci95_hi=hi, crashes=crash,
                 td_vh_p99=float(np.percentile(vh, 99)) if vh else float("nan"))
        rows.append(r)
        print(r, flush=True)
    with open(os.path.join(RES, "imu_sweep_v2.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    json.dump(dict(version="imu_sweep v2", sim=s6.SIM6_VERSION, m_n2o=m_mc, rows=rows,
                   note="gyro-propagated attitude, no in-flight aiding (estimator assumption of sim6)"),
              open(os.path.join(RES, "imu_sweep_v2.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
