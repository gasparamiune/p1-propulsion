"""Failure forensics for the M2 Monte Carlo (kept as evidence): re-fly every failed run of selected cases with the
same dispersion draw (m2_mc6 draws: numpy default_rng(101), N runs, run6.draw) and full recording, and classify
the failure from the time history.

Output: GNC_RES/mc6_failure_forensics_v2.json/.csv and one PNG time history per failed baseline run.
Run: nice -n 10 python scripts/m2_failure_forensics.py
"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
CASES = os.environ.get("GNC_FX_CASES", "AD_fins_f20,AD_nofins_f20,AF_nofins_f20,B_f20").split(",")
os.makedirs(RES, exist_ok=True)
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PH = {0: "pad", 1: "ascent", 2: "coast", 3: "descent", 4: "relight_wait", 5: "landing_burn", 6: "terminal",
      7: "shutdown", 8: "landed"}


def classify(res, rec):
    t = rec[:, I["t"]]
    ph = rec[:, I["phase"]]
    tilt = rec[:, I["tilt"]]
    why = []
    if res["crash"] > 0.5 or res["landed"] < 0.5:
        k = len(t) - 1
        why.append(f"no touchdown/crash in phase {PH.get(int(ph[k]), int(ph[k]))} at t {t[k]:.2f} s, "
                   f"h_cg {rec[k, I['z']]:.1f} m, vz {rec[k, I['vz']]:.1f} m/s, tilt {tilt[k]:.1f} deg")
    if res["exhausted"] > 0.5:
        why.append("propellant exhausted")
    if res["tipover"] > 0.5:
        why.append("tip-over after touchdown")
    if res["landed"] > 0.5:
        for k_, lim, lab in (("td_vh", R.CRIT["vh"], "lateral speed"), ("td_vz", R.CRIT["vz"], "vertical speed"),
                             ("td_tilt", R.CRIT["tilt"], "tilt"), ("td_rate", R.CRIT["rate"], "tilt rate")):
            val = abs(res[k_])
            if val > lim:
                why.append(f"{lab} {val:.2f} > {lim}")
    land = ph >= 5
    out = dict(reasons="; ".join(why), max_tilt_landing_burn_deg=float(tilt[land].max()) if land.any() else None,
               t_relight_cmd=float(t[np.argmax(ph >= 4)]) if (ph >= 4).any() else None,
               h_relight_cmd=float(rec[np.argmax(ph >= 4), I["z"]]) if (ph >= 4).any() else None,
               tilt_at_relight_cmd=float(tilt[np.argmax(ph >= 4)]) if (ph >= 4).any() else None,
               gim_sat_frac=float(res["gim_sat_frac"]), max_gim=float(res["max_gim"]), td_wind=float(res["td_wind"]))
    return out


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")))
    rows_out = []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for c in CASES:
        if c not in S["cases"] or not S["cases"][c].get("closes", True):
            continue
        cs = S["cases"][c]
        with open(os.path.join(OUT, f"mc6_runs_{c}_{SUFFIX}.csv")) as f:
            runs = list(csv.DictReader(f))
        failed = [int(float(r["run"])) for r in runs if float(r["ok"]) < 0.5]
        over, note = M.CASES[c]
        over = dict(over)
        if over.get("ballast") == "auto":
            over["ballast"] = cs["ballast"]["ballast_kg"]
        cfg = R.cfg_of(**dict(over, m_n2o=cs["m_n2o_mc_kg"]))
        rng = np.random.default_rng(101)
        D = R.draw(rng, S["n"], cfg)
        for i in failed:
            dr = D[i]
            cc, disp = R.run_cfg(cfg, dr)      # same configuration as the MC run (run6.run_one)
            cc["rec_dt"] = 0.01
            res, rec, info = R.fly(cc, disp, nrec=12000)
            # reproducibility check against the MC row
            mc = [r for r in runs if int(float(r["run"])) == i][0]
            repro = abs(float(mc["td_vh"]) - res["td_vh"]) < 1e-6 and abs(float(mc["td_vz"]) - res["td_vz"]) < 1e-6
            cl = classify(res, rec)
            row = dict(case=c, run=i, reproduced=repro, wind=dr["_wind"], gust_scale=dr["_gust_scale"],
                       g_bias_dps=float(np.degrees(np.hypot(dr["g_b"][0], dr["g_b"][1]))), t_ign=dr["_t_ign"],
                       td_vz=float(res["td_vz"]), td_vh=float(res["td_vh"]), td_tilt=float(res["td_tilt"]),
                       td_rate=float(res["td_rate"]), landed=float(res["landed"]), crash=float(res["crash"]),
                       tipover=float(res["tipover"]), h_ign=float(res["h_ign"]), v_ign=float(res["v_ign"]), **cl)
            rows_out.append(row)
            print(c, i, row["reasons"], "| wind", round(dr["_wind"], 2), "repro", repro, flush=True)
            if c == "AD_fins_f20":
                t = rec[:, I["t"]]
                fig, axs = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
                axs[0].plot(t, rec[:, I["z"]] - rec[0, I["z"]], label="h"); axs[0].plot(t, rec[:, I["vz"]], label="vz")
                axs[0].plot(t, np.hypot(rec[:, I["vx"]], rec[:, I["vy"]]), label="v_h"); axs[0].legend(fontsize=7)
                axs[1].plot(t, rec[:, I["F"]], label="F [N]"); axs[1].plot(t, 20 * rec[:, I["phase"]], ":", label="20 x phase")
                axs[1].legend(fontsize=7)
                axs[2].plot(t, rec[:, I["tilt"]], label="tilt [deg]"); axs[2].plot(t, rec[:, I["dgx"]], label="gimbal x [deg]")
                axs[2].plot(t, rec[:, I["dgy"]], label="gimbal y [deg]"); axs[2].legend(fontsize=7)
                axs[2].set_xlabel("t [s]")
                for a_ in axs:
                    a_.grid(alpha=0.3)
                fig.suptitle(f"{c} run {i}: {row['reasons']} (wind {dr['_wind']:.1f} m/s)", fontsize=9)
                fig.tight_layout()
                fig.savefig(os.path.join(RES, f"mc6_failure_{c}_run{i:03d}_v2.png"), dpi=110)
                plt.close(fig)
    if rows_out:
        keys = list(rows_out[0].keys())
        with open(os.path.join(RES, "mc6_failure_forensics_v2.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows_out:
                w.writerow(r)
    json.dump(dict(version="mc6 failure forensics v2", sim=s6.SIM6_VERSION, rows=rows_out),
              open(os.path.join(RES, "mc6_failure_forensics_v2.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
