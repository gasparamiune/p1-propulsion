"""m2_rg07_b1_eng07d v1 (GNC, 2026-10-13): review REV-GNC-1 RG-07, B1 62 m flown on the ENG-07d actuator basis.

ENG-07d basis = the actuator overrides of the published A1J tables, copied from m2_eng03_rate base_ref('A1J_pc') (not retyped):
act_model 1 (servo pair on the SB-2292SG DATASHEET torque-speed lines through the Cardan kinematics, hose spring), servo_V 6.6 V
plug, act_n 4.8, supply chain v2.2_as_drawn/typ/15, interface inertia act_Jint, notch tracking the landing-burn rocking mode with
the mistune drawn U(1 +/- gim_notch_mis_w), gim_notch_q, gim_notch_db.
Arms (500 runs, seed 101, paired exact McNemar against the stored reference of the same FSW):
  E07d_66      rbl_B1_lead62_pc_k2 (stored, FSW v2.7 provisional, P 0.996) + ENG-07d basis at 6.6 V
  E07d_74      the same at 7.4 V (B-TVC-1 measures both voltages)
  W1p_E07d_66  the current B1 flight FSW (burn limit action 1, Pc-based apex predictor: m2_web_limit W1p, P 0.994) + ENG-07d 6.6 V
Pairing: run6 draws the notch mistune from its own generator; the common dispersion columns are compared with the reference CSV.
More degrees of freedom (act_model 1) is not proof of accuracy: the servo lines are DATASHEET values; B-TVC-1 measures them.
Output: <out>/rg07_<arm>.csv, <out>/rg07_b1_eng07d.json"""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RG07_OUT", f"{S}/rg07")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_rg07_b1_eng07d v1"
PARTS = os.environ.get("GNC_RG07_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_RG07_SPLIT", "0/1")
N = 500
ACT_KEYS = ("act_model", "servo_V", "act_n", "supply_chain", "supply_Vrest", "act_Jint", "gim_notch_track", "gim_notch_mis_w",
            "gim_notch_q", "gim_notch_db")
COMMON = ("wind", "gust_scale", "isp_scale", "thrust_scale", "m_est_err", "reg_a", "reg_n", "throat_g", "mis_deg", "cg_off_mm")


def eng07d():
    over, _, _ = E.base_ref("A1J_pc")
    return {k: over[k] for k in ACT_KEYS if k in over}


def arms():
    J = eng07d()
    return {"E07d_66": dict(fsw="v27", over=dict(J, servo_V=6.6)), "E07d_74": dict(fsw="v27", over=dict(J, servo_V=7.4)),
            "W1p_E07d_66": dict(fsw="W1p", over=dict(J, servo_V=6.6))}


def ref_csv(fsw):
    return "/home/claude/work/space/out/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv" if fsw == "v27" else \
        os.path.join(S, "web_limit", "web_W1p.csv")


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    A = arms()
    for name in list(A)[k::n]:
        p = os.path.join(OUT, f"rg07_{name}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_RG07_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        a = A[name]
        cfg0, over, m, note = WL.base_cfg()
        cfg = R.cfg_of(**dict(over, m_n2o=float(m), **a["over"]))
        D = R.draw(np.random.default_rng(101), N, cfg)
        Z = WL.meas_draws(N)
        jref = float(cfg.get("throat_jref") or 0.0)
        t0 = time.time()
        rows = []
        for i in range(N):
            c, disp = R.run_cfg(cfg, D[i])
            if a["fsw"] == "W1p":
                c.update(WL.web_over(D[i], Z[i], WL.CASES["W1p"], jref)[0])
            res = R.fly(c, disp, nrec=10)[0]
            rows.append(R.flat_row(i, D[i], res, R.success(res), cfg))
        M.write_csv(p, rows)
        print(f"{name}: P {np.mean([r['ok'] for r in rows]):.3f} ({time.time() - t0:.0f} s)", flush=True)


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def pct(x, qs=(50, 99)):
    x = np.asarray(x, float)
    return dict({f"p{q:02d}": float(np.percentile(x, q)) for q in qs}, min=float(x.min()), max=float(x.max()), n=int(x.size))


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return dict(P_ref=float(a.mean()), P_case=float(b.mean()), lost=lost, gained=gained,
                p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0, n=int(len(a)))


def part_eval():
    A = arms()
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               eng07d_overrides=eng07d(), arms={})
    for name, a in A.items():
        rows = rows_csv(os.path.join(OUT, f"rg07_{name}.csv"))
        ref = rows_csv(ref_csv(a["fsw"]))
        if not rows or not ref:
            continue
        ok, okr = col(rows, "ok") > 0.5, col(ref, "ok") > 0.5
        same = {k: bool(np.allclose(col(rows, k), col(ref, k), equal_nan=True)) for k in COMMON if k in rows[0] and k in ref[0]}
        fail = [dict(run=int(r["run"]), td_vz=float(r["td_vz"]), td_vh=float(r["td_vh"]), td_tilt=float(r["td_tilt"]),
                     td_rate=float(r["td_rate"]), crash=float(r["crash"]), exhausted=float(r["exhausted"]))
                for r, o in zip(rows, ok) if not o]
        out["arms"][name] = dict(over=a["over"], fsw=a["fsw"], reference=ref_csv(a["fsw"]), vs_reference=mcnemar(okr, ok),
                                 P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(ok))], same_common_draws=same,
                                 failures=fail, max_gim_deg=pct(col(rows, "max_gim")), max_gim_rate_dps=pct(col(rows, "max_gim_rate")),
                                 act_sat_time_land_s=pct(col(rows, "act_sat_time_land")), td_vz=pct(col(rows, "td_vz"), (1, 50)),
                                 td_vh=pct(col(rows, "td_vh")), h_max=pct(col(rows, "h_max")))
    with open(os.path.join(OUT, "rg07_b1_eng07d.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for k, v in out["arms"].items():
        m_ = v["vs_reference"]
        print(f"{k:12s} P {m_['P_case']:.3f} vs ref {m_['P_ref']:.3f} (-{m_['lost']}/+{m_['gained']}, p {m_['p_exact']:.3g}) same draws "
              f"{all(v['same_common_draws'].values())} | gim max p99 {v['max_gim_deg']['p99']:.2f} deg | sat land p99 "
              f"{v['act_sat_time_land_s']['p99']:.3f} s | fails {[(f_['run'], round(f_['td_vz'], 2), round(f_['td_vh'], 2)) for f_ in v['failures']]}",
              flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
