"""m2_cap_rule v1 (GNC, 2026-10-13): review REV-GNC-1 RG-04 (and RG-11 b), the B1 hop cap written as a rule in MEASURED engine
quantities, with the reserve searched on a grid that resolves the 10 ms MECO steps, a conditional Monte Carlo at fixed engine
properties, and the A1 success probability at a fixed delivered-thrust-per-flow factor.

Rule (PROPOSAL for the lead, to be re-applied per engine after T1-T4):
  inputs  k = delivered thrust per propellant flow relative to the map (T1-T4 load cell / flow), u_k its 1-sigma;
          (a, n) regression law with its 2-sigma region; g = throat growth per flight with u_g; N2O load 2.00 kg.
  corner  k_c = k - 2 u_k; (a_c, n_c) = the 2-sigma point with the lowest regression (low a, high n: the longest burn and
          the largest N2O use); g_c = g + 2 u_g.
  cap     h_cap = the largest grid height (0.25 m steps from H_LO) such that EVERY grid height up to it meets the +25 %
          reserve rule (usable N2O = liquid left - 3 % trapped >= 25 % of the N2O burned) on the nominal flight at the
          corner. Grid, not bisection: reserve(h) is a step function of the 10 ms MECO quantisation (RG-11 b).
  check   conditional MC at h_cap with (k_c, a_c, n_c, g_c) fixed in every run and every other dispersion drawn (seed 101,
          500 runs): P >= 0.99 and no exhausted run; otherwise lower h_cap by 0.25 m and repeat.
Pre-T1-T4 demonstration (the measured values do not exist yet; the rows are examples, not flight values):
  k in {1.00, 0.97, 0.95, 0.90} with u_k = 0; corner (a 0.6, n 0.68), g 0.11 (the reviewer's corner, rg11 / rg14); and the
  band centre (a 1.05, n 0.515) for comparison. Cross-check against the reviewer's independent rg11 cap search
  (62.92 / 59.65 / 56.43 / 50.79 m at k 1.00 / 0.97 / 0.95 / 0.90).
Conditional MC (B1): (k 1.00, corner) at 62 m and at its cap; (k 0.97, corner) at 62 m and at its cap.
A1 at fixed efficiency: A1_none base with thrust_scale fixed at 1.00 / 0.97 / 0.95 / 0.90 in every run, other dispersions
drawn (seed 101, 500 runs, paired with the stored A1_none table); nominal A1 reserve at each k.
Output: <out>/cap_rule.json, cond_<case>.csv"""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_CAP_OUT", f"{S}/cap_rule")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_cap_rule v1"
PARTS = os.environ.get("GNC_CAP_PARTS", "grid,cond,a1,eval").split(",")
SPLIT = os.environ.get("GNC_CAP_SPLIT", "0/1")
N = 500
H_LO, H_HI, DH = 45.0, 68.0, 0.25
KS = (1.00, 0.97, 0.95, 0.90)
CORNERS = {"corner": (0.6, 0.68, 0.11), "centre": (1.05, 0.515, 0.11)}
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
REVIEWER_RG11 = {1.00: 62.92, 0.97: 59.65, 0.95: 56.43, 0.90: 50.79}


def b1_over():
    _, over, m, _ = WL.base_cfg()
    return over, m


def nominal(over, m, disp):
    """PC.nominal with a dispersion dict (engine properties fixed): reserve-rule quantities."""
    cfg = R.cfg_of(**dict(over, m_n2o=m))
    res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.01), dict(R.DISP, **disp), nrec=20000)
    t = rec[:, I["t"]]
    burned = float(np.sum(0.5 * (rec[1:, I["mox"]] + rec[:-1, I["mox"]]) * np.diff(t)))
    liq = float(res["liq_left"])
    usable = liq - PC.TRAP * m
    return dict(h=float(over.get("h_target", 0.0)), burned=burned, liquid_left=liq, usable=usable,
                reserve=usable / burned if burned > 0 else float("nan"), landed_ok=bool(R.success(res)),
                closes=bool(R.success(res) and usable >= PC.RESERVE * burned), t_meco=float(res["t_meco"]),
                burn_time=float(res["burn_time"]), h_max=float(res["h_max"]))


def part_grid():
    over, m = b1_over()
    hs = np.arange(H_LO, H_HI + 1e-9, DH)
    out = {}
    for cn, (a, n, g) in CORNERS.items():
        for k in KS:
            t0 = time.time()
            rows = [nominal(dict(over, h_target=float(h)), m, dict(thrust_scale=k, reg_a=a, reg_n=n, throat_g=g)) for h in hs]
            cl = np.array([r["closes"] for r in rows])
            first_fail = int(np.argmin(cl)) if not cl.all() else len(cl)
            cap = float(hs[first_fail - 1]) if first_fail > 0 else None
            nonmono = int(np.sum(cl[first_fail:]))
            r62 = rows[int(np.argmin(np.abs(hs - 62.0)))]
            out[f"{cn}|k{k:.2f}"] = dict(a=a, n=n, g=g, k=k, cap_m=cap, closing_heights_above_first_failure=nonmono,
                                         reserve_at_62m=r62["reserve"], reviewer_rg11_cap_m=REVIEWER_RG11.get(k) if cn == "corner" else None,
                                         grid=[dict(h=r["h"], reserve=r["reserve"], closes=r["closes"], t_meco=r["t_meco"]) for r in rows])
            print(f"grid {cn} k {k:.2f}: cap {cap} m (non-monotone closings above {nonmono}) reserve@62 {100 * r62['reserve']:.1f} % "
                  f"rg11 {REVIEWER_RG11.get(k) if cn == 'corner' else '-'} ({time.time() - t0:.0f} s)", flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cap_grid.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


def cond_cases():
    gp = os.path.join(OUT, "cap_grid.json")
    G = json.load(open(gp)) if os.path.exists(gp) else {}
    c = {}
    for k in (1.00, 0.97):
        cap = (G.get(f"corner|k{k:.2f}") or {}).get("cap_m")
        c[f"B1_corner_k{k:.2f}_h62"] = dict(prof="B1", k=k, h=62.0)
        if cap is not None and abs(cap - 62.0) > 1e-9:
            c[f"B1_corner_k{k:.2f}_cap"] = dict(prof="B1", k=k, h=float(cap))
    for k in KS:
        c[f"A1_k{k:.2f}"] = dict(prof="A1", k=k)
    return c


def fly_cond(spec):
    rows = []
    if spec["prof"] == "B1":
        over, m = b1_over()
        a, n, g = CORNERS["corner"]
        cfg = R.cfg_of(**dict(over, m_n2o=m, h_target=spec["h"]))
        D = R.draw(np.random.default_rng(101), N, cfg)
        for i in range(N):
            d = dict(D[i], thrust_scale=spec["k"], reg_a=a, reg_n=n, throat_g=g)
            c, disp = R.run_cfg(cfg, d)
            res = R.fly(c, disp, nrec=10)[0]
            rows.append(R.flat_row(i, d, res, R.success(res), cfg))
    else:
        over, _, bj = E.base_ref("A1_none")
        m = json.load(open(bj))["m_n2o_mc_kg"]
        cfg = R.cfg_of(**dict({k_: v for k_, v in over.items() if k_ != "m_fixed"}, m_n2o=float(m)))
        D = R.draw(np.random.default_rng(101), N, cfg)
        for i in range(N):
            d = dict(D[i], thrust_scale=spec["k"])
            c, disp = R.run_cfg(cfg, d)
            res = R.fly(c, disp, nrec=10)[0]
            rows.append(R.flat_row(i, d, res, R.success(res), cfg))
    return rows


def part_cond(which):
    os.makedirs(OUT, exist_ok=True)
    C = {k: v for k, v in cond_cases().items() if v["prof"] == which}
    kk, nn = (int(x) for x in SPLIT.split("/"))
    for name in list(C)[kk::nn]:
        p = os.path.join(OUT, f"cond_{name}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_CAP_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        t0 = time.time()
        rows = fly_cond(C[name])
        M.write_csv(p, rows)
        print(f"cond {name}: P {np.mean([r['ok'] for r in rows]):.3f} exhausted {sum(r['exhausted'] > 0.5 for r in rows)} "
              f"({time.time() - t0:.0f} s)", flush=True)


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return dict(P_ref=float(a.mean()), P_case=float(b.mean()), lost=lost, gained=gained,
                p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0, n=int(len(a)))


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               reserve_rule=dict(reserve=PC.RESERVE, trapped=PC.TRAP, m_n2o_kg=2.00), grid_step_m=DH, grid={}, cond={})
    gp = os.path.join(OUT, "cap_grid.json")
    if os.path.exists(gp):
        G = json.load(open(gp))
        out["grid"] = {k: {kk: vv for kk, vv in v.items() if kk != "grid"} for k, v in G.items()}
        out["grid_full_path"] = gp
    refA = rows_csv("/home/claude/work/space/out/relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv")
    for name, spec in cond_cases().items():
        rows = rows_csv(os.path.join(OUT, f"cond_{name}.csv"))
        if not rows:
            continue
        ok = col(rows, "ok") > 0.5
        e = dict(spec, P=float(ok.mean()), P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(ok))],
                 exhausted=int(np.sum(col(rows, "exhausted") > 0.5)),
                 liquid_left_kg=dict(p01=float(np.percentile(col(rows, "liq_left"), 1)), min=float(col(rows, "liq_left").min())),
                 usable_left_kg=dict(p01=float(np.percentile(col(rows, "liq_left") - PC.TRAP * 2.0, 1)),
                                     min=float((col(rows, "liq_left") - PC.TRAP * 2.0).min())),
                 burn_time_s=dict(p99=float(np.percentile(col(rows, "burn_time"), 99)), max=float(col(rows, "burn_time").max())))
        if spec["prof"] == "A1" and refA:
            e["vs_stored_A1_none"] = mcnemar(col(refA, "ok") > 0.5, ok)
        out["cond"][name] = e
    with open(os.path.join(OUT, "cap_rule.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for k, v in out["grid"].items():
        print(f"{k:14s} cap {v['cap_m']} m (rg11 {v['reviewer_rg11_cap_m']}) reserve@62 {100 * v['reserve_at_62m']:.1f} % "
              f"non-monotone {v['closing_heights_above_first_failure']}", flush=True)
    for k, v in out["cond"].items():
        vs = v.get("vs_stored_A1_none", {})
        print(f"{k:22s} P {v['P']:.3f} {v['P_wilson']} exhausted {v['exhausted']} usable p01 {v['usable_left_kg']['p01']:.3f} kg "
              f"min {v['usable_left_kg']['min']:.3f}" + (f" | vs stored -{vs['lost']}/+{vs['gained']} p {vs['p_exact']:.3g}" if vs else ""),
              flush=True)


def main():
    if "grid" in PARTS:
        part_grid()
    if "cond" in PARTS:
        part_cond("B1")
    if "a1" in PARTS:
        part_cond("A1")
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
