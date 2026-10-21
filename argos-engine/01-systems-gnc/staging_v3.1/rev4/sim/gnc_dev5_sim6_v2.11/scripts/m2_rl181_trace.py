"""m2_rl181_trace v1 (GNC, 2026-10-13): fly selected A1 Monte Carlo draws with the recorder at the 1.81 s relight planning
value in the LATE / EARLY variants (and, when the option exists in sim6, EARLY with the hold-to-planned-light option) and
write the landing-burn history around the light. Evidence for relight_planning_181.mechanism; not a statistic.

Usage: m2_rl181_trace.py [run ...]   (default run 0). Output: $GNC_RL181_OUT/rl181_trace.json
Basis: A1 pc2 basis (m2_prop_closure DC A1, ratchet), FSW v2.7 k_est_asc 2, seed 101 draw table of 500 runs."""
import csv, os, sys, json
import numpy as np
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_SUFFIX", "pc2")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "scripts"))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402

VERSION = "m2_rl181_trace v1"
OUT = os.environ.get("GNC_RL181_OUT", "/home/claude/work/space/out/relight_181")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
VARIANTS = [("late", dict(t_ign_add=1.21, t_ign_est=1.81)), ("early", dict(t_ign_add=0.56, t_ign_est=1.81))]
MC_CSV = {"late": "mc6_runs_rl181_A1_none_k2_rl181.csv", "early": "mc6_runs_rl181e_A1_none_k2_rl181.csv",
          "early_hold": "mc6_runs_rl181h_A1_none_k2_rl181.csv"}
if "relight_hold" in R.cfg_of(**dict(PC.DC["A1"], m_n2o=PC.M_TANK)):
    VARIANTS.append(("early_hold", dict(t_ign_add=0.56, t_ign_est=1.81, relight_hold=1)))


def trace(run, over):
    cfg = R.cfg_of(**dict(PC.DC["A1"], k_est_asc=2, m_n2o=PC.M_TANK, **over))
    D = R.draw(np.random.default_rng(101), 500, cfg)
    c, disp = R.run_cfg(cfg, D[run])
    res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
    t, ph, F = rec[:, I["t"]], rec[:, I["phase"]], rec[:, I["F"]]
    i4 = int(np.where(ph >= 4)[0][0])
    lit = np.where((ph >= 5) & (F > 1.0))[0]
    i5 = int(lit[0]) if len(lit) else int(np.where(ph >= 5)[0][0])
    w = np.degrees(np.hypot(rec[:, I["wx"]], rec[:, I["wy"]]))
    vh = np.hypot(rec[:, I["vx"]], rec[:, I["vy"]])
    land = ph >= 5
    hist = [dict(t=round(float(t[k]), 2), phase=int(ph[k]), z_m=round(float(rec[k, I["z"]]), 2), vz_mps=round(float(rec[k, I["vz"]]), 2),
                 F_N=round(float(F[k]), 1), Fcmd_N=round(float(rec[k, I["Fcmd"]]), 1), tilt_deg=round(float(rec[k, I["tilt"]]), 1),
                 rate_dps=round(float(w[k]), 1), vh_mps=round(float(vh[k]), 2))
            for k in range(max(0, i4 - 20), min(len(t), i5 + 400), 10)]
    return dict(ok=bool(R.success(res)), t_relight_cmd_s=round(float(t[i4]), 2), t_light_s=round(float(t[i5]), 2),
                h_at_light_m=round(float(rec[i5, I["z"]]), 2), vz_at_light_mps=round(float(rec[i5, I["vz"]]), 2),
                vh_at_light_mps=round(float(vh[i5]), 2), max_tilt_landing_burn_deg=round(float(rec[land, I["tilt"]].max()), 1),
                max_rate_landing_burn_dps=round(float(w[land].max()), 1), td_rate_dps=round(float(res["td_rate"]), 6),
                td_vh_mps=round(float(res["td_vh"]), 6), td_vz_mps=round(float(res.get("td_vz", np.nan)), 3),
                n2o_burned_kg=round(float(res.get("n2o_burned", np.nan)), 4), history_every_0p1s=hist)


def main():
    runs = [int(a) for a in sys.argv[1:]] or [0]
    out = dict(version=VERSION, sim=s6.SIM6_VERSION, basis="A1 pc2 (m2_prop_closure DC A1, ratchet), FSW v2.7 k_est_asc 2, seed 101, "
               "500-run draw table", variants={k: v for k, v in VARIANTS}, runs={})
    for r in runs:
        out["runs"][str(r)] = {lab: trace(r, ov) for lab, ov in VARIANTS}
        for lab, x in out["runs"][str(r)].items():   # the recorded flight must reproduce the Monte Carlo row of the same draw
            p = os.path.join(OUT, MC_CSV.get(lab, ""))
            if os.path.isfile(p):
                row = list(csv.DictReader(open(p)))[r]
                x["mc_row_check"] = dict(csv=os.path.basename(p), ok_mc=row["ok"] in ("1", "True", "1.0"),
                                         same=all(abs(float(row[k]) - x[f"{k}_{u}"]) < 1e-3 for k, u in
                                                  (("td_rate", "dps"), ("td_vh", "mps"))))
        for lab in out["runs"][str(r)]:
            x = out["runs"][str(r)][lab]
            print(f"run {r} {lab:10s} ok {x['ok']} light {x['t_light_s']:.2f} s at {x['h_at_light_m']:.1f} m vh {x['vh_at_light_mps']:.2f} | "
                  f"max tilt {x['max_tilt_landing_burn_deg']:.1f} deg rate {x['max_rate_landing_burn_dps']:.1f} deg/s | td rate "
                  f"{x['td_rate_dps']:.1f} vh {x['td_vh_mps']:.2f}")
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "rl181_trace.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", p)


if __name__ == "__main__":
    main()
