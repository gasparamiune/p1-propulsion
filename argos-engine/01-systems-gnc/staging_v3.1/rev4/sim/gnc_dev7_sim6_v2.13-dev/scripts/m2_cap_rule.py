"""m2_cap_rule v1.1 (GNC, 2026-10-13): review REV-GNC-1 RG-04 (and RG-11 b), the B1 hop cap written as a rule in MEASURED engine
quantities, with the reserve searched on a grid that resolves the 10 ms MECO steps, a conditional Monte Carlo at fixed engine
properties, and the A1 success probability and reserve at a fixed delivered-thrust-per-flow factor.
v1.1 (before the first run of v1): grid and k-scan on two flight-software configurations (v27 = the stored rbl FSW, the basis
of the reviewer's rg11 search; W1p = the current B1 flight FSW, burn limit action 1 + Pc-based apex predictor, m2_web_limit),
nominal-flight k-scan of the reserve at 62 m (B1) and 300 m (A1), conditional MC on both FSW at k 1.00.

Rule (PROPOSAL for the lead, to be re-applied per engine after T1-T4):
  inputs  k = delivered thrust per propellant flow relative to the map (T1-T4 load cell / flow), u_k its 1-sigma;
          (a, n) regression law with its 2-sigma region; g = throat growth per flight with u_g; N2O load 2.00 kg.
  corner  k_c = k - 2 u_k; (a_c, n_c) = the 2-sigma point with the lowest regression (low a, high n: the longest burn and
          the largest N2O use); g_c = g + 2 u_g.
  cap     h_cap = the largest grid height (0.25 m steps from H_LO) such that EVERY grid height up to it meets the +25 %
          reserve rule (usable N2O = liquid left - 3 % trapped >= 25 % of the N2O burned) on the nominal flight at the
          corner with the flight FSW. Grid, not bisection: reserve(h) is a step function of the 10 ms MECO quantisation
          (RG-11 b).
  check   conditional MC at h_cap with (k_c, a_c, n_c, g_c) fixed in every run and every other dispersion drawn (seed 101,
          500 runs): P >= 0.99 and no exhausted run; otherwise lower h_cap by 0.25 m and repeat.
Pre-T1-T4 demonstration (the measured values do not exist yet; the rows are examples, not flight values):
  k in {1.00, 0.97, 0.95, 0.90} with u_k = 0; corner (a 0.6, n 0.68), g 0.11 (the reviewer's corner, rg11 / rg14); and the
  band centre (a 1.05, n 0.515) for comparison. Cross-check against the reviewer's independent rg11 cap search
  (62.92 / 59.65 / 56.43 / 50.79 m at k 1.00 / 0.97 / 0.95 / 0.90) and the reviewer's 1-DOF k limits (rg08: A1 0.922,
  B1 62 m 0.859).
Conditional MC (B1): corner k 1.00 at 62 m on v27 (the reviewer's rg14 basis: P 0.990, 3 exhausted) and on W1p; corner k 0.97
at 62 m and at the W1p cap; corner k 1.00 at the W1p cap when it differs from 62 m.
A1 at fixed efficiency: A1_none base with thrust_scale fixed at 1.00 / 0.97 / 0.95 / 0.90 in every run, other dispersions
drawn (seed 101, 500 runs, paired with the stored A1_none table); nominal A1 reserve at each k (k-scan).
Output: <out>/cap_grid.json, cap_kscan.json, cond_<case>.csv, cap_rule.json"""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_CAP_OUT", f"{S}/cap_rule")
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")   # m2_prop_closure import needs these
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_cap_rule v1.1"
PARTS = os.environ.get("GNC_CAP_PARTS", "grid,kscan,cond,a1,eval").split(",")
SPLIT = os.environ.get("GNC_CAP_SPLIT", "0/1")
N = 500
H_LO, H_HI, DH = 45.0, 68.0, 0.25
KS = (1.00, 0.97, 0.95, 0.90)
KSCAN = tuple(np.round(np.arange(1.00, 0.849, -0.01), 2))
CORNERS = {"corner": (0.6, 0.68, 0.11), "centre": (1.05, 0.515, 0.11)}
FSWS = ("v27", "W1p")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
REVIEWER_RG11 = {1.00: 62.92, 0.97: 59.65, 0.95: 56.43, 0.90: 50.79}
REVIEWER_RG08 = {"A1": 0.922, "B1_62m": 0.859}


def b1_over():
    _, over, m, _ = WL.base_cfg()
    return over, m


def a1_over():
    over, _, bj = E.base_ref("A1_none")
    return {k_: v for k_, v in over.items() if k_ != "m_fixed"}, float(json.load(open(bj))["m_n2o_mc_kg"])


def nominal(over, m, disp, fsw="v27"):
    """Nominal flight (no wind, no noise) with the engine properties in disp fixed: reserve-rule quantities."""
    cfg = R.cfg_of(**dict(over, m_n2o=m))
    c = dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.01)
    if fsw == "W1p":
        dr = dict(reg_a=disp["reg_a"], reg_n=disp["reg_n"], isp_scale=disp.get("isp_scale", 1.0))
        c.update(WL.web_over(dr, (0.0, 0.0, 0.0), WL.CASES["W1p"], float(cfg.get("throat_jref") or 0.0))[0])
    res, rec, info = R.fly(c, dict(R.DISP, **disp), nrec=20000)
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
    for fsw in FSWS:
        for cn, (a, n, g) in CORNERS.items():
            for k in KS:
                t0 = time.time()
                rows = [nominal(dict(over, h_target=float(h)), m, dict(thrust_scale=k, reg_a=a, reg_n=n, throat_g=g), fsw)
                        for h in hs]
                cl = np.array([r["closes"] for r in rows])
                first_fail = int(np.argmin(cl)) if not cl.all() else len(cl)
                cap = float(hs[first_fail - 1]) if first_fail > 0 else None
                nonmono = int(np.sum(cl[first_fail:]))
                r62 = rows[int(np.argmin(np.abs(hs - 62.0)))]
                out[f"{fsw}|{cn}|k{k:.2f}"] = dict(fsw=fsw, a=a, n=n, g=g, k=k, cap_m=cap,
                                                   closing_heights_above_first_failure=nonmono, reserve_at_62m=r62["reserve"],
                                                   reviewer_rg11_cap_m=REVIEWER_RG11.get(k) if cn == "corner" else None,
                                                   grid=[dict(h=r["h"], reserve=r["reserve"], closes=r["closes"],
                                                              t_meco=r["t_meco"], h_max=r["h_max"]) for r in rows])
                print(f"grid {fsw} {cn} k {k:.2f}: cap {cap} m (non-monotone closings above {nonmono}) reserve@62 "
                      f"{100 * r62['reserve']:.1f} % rg11 {REVIEWER_RG11.get(k) if cn == 'corner' else '-'} "
                      f"({time.time() - t0:.0f} s)", flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cap_grid.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


def part_kscan():
    """Reserve against k on the nominal flight: B1 62 m (corner, centre; both FSW), A1 (its own base, nominal engine)."""
    over, m = b1_over()
    oa, ma = a1_over()
    out = {}
    for fsw in FSWS:
        for cn, (a, n, g) in CORNERS.items():
            rows = [dict(k=float(k), **nominal(dict(over, h_target=62.0), m, dict(thrust_scale=float(k), reg_a=a, reg_n=n,
                                                                                     throat_g=g), fsw)) for k in KSCAN]
            out[f"B1_62|{fsw}|{cn}"] = rows
            print(f"kscan B1 62 {fsw} {cn}: " + " ".join(f"{r['k']:.2f}:{100 * r['reserve']:.1f}{'' if r['closes'] else 'x'}"
                                                         for r in rows), flush=True)
    rows = [dict(k=float(k), **nominal(oa, ma, dict(thrust_scale=float(k)))) for k in KSCAN]
    out["A1|v28"] = rows
    print("kscan A1: " + " ".join(f"{r['k']:.2f}:{100 * r['reserve']:.1f}{'' if r['closes'] else 'x'}" for r in rows), flush=True)
    for key, rows in out.items():
        ks = [r["k"] for r in rows if r["closes"]]
        bad = [r["k"] for r in rows if not r["closes"]]
        out[key] = dict(rows=rows, lowest_closing_k=min(ks) if ks else None,
                        highest_failing_k=max(bad) if bad else None,
                        monotone=bool(not bad or not ks or max(bad) < min(ks)))
    out["reviewer_rg08_1dof"] = REVIEWER_RG08
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cap_kscan.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


def cond_cases():
    gp = os.path.join(OUT, "cap_grid.json")
    G = json.load(open(gp)) if os.path.exists(gp) else {}
    c = {"B1_corner_k1.00_h62_v27": dict(prof="B1", k=1.00, h=62.0, fsw="v27")}
    for k in (1.00, 0.97):
        cap = (G.get(f"W1p|corner|k{k:.2f}") or {}).get("cap_m")
        c[f"B1_corner_k{k:.2f}_h62_W1p"] = dict(prof="B1", k=k, h=62.0, fsw="W1p")
        if cap is not None and abs(cap - 62.0) > 1e-9:
            c[f"B1_corner_k{k:.2f}_cap_W1p"] = dict(prof="B1", k=k, h=float(cap), fsw="W1p")
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
        Z = WL.meas_draws(N)
        jref = float(cfg.get("throat_jref") or 0.0)
        for i in range(N):
            d = dict(D[i], thrust_scale=spec["k"], reg_a=a, reg_n=n, throat_g=g)
            c, disp = R.run_cfg(cfg, d)
            if spec["fsw"] == "W1p":
                c.update(WL.web_over(d, Z[i], WL.CASES["W1p"], jref)[0])
            res = R.fly(c, disp, nrec=10)[0]
            rows.append(R.flat_row(i, d, res, R.success(res), cfg))
    else:
        over, m = a1_over()
        cfg = R.cfg_of(**dict(over, m_n2o=m))
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
               reserve_rule=dict(reserve=PC.RESERVE, trapped=PC.TRAP, m_n2o_kg=2.00), grid_step_m=DH, grid={}, kscan={}, cond={})
    gp = os.path.join(OUT, "cap_grid.json")
    if os.path.exists(gp):
        G = json.load(open(gp))
        out["grid"] = {k: {kk: vv for kk, vv in v.items() if kk != "grid"} for k, v in G.items()}
        out["grid_full_path"] = gp
    kp = os.path.join(OUT, "cap_kscan.json")
    if os.path.exists(kp):
        K = json.load(open(kp))
        out["kscan"] = {k: ({kk: vv for kk, vv in v.items() if kk != "rows"} if isinstance(v, dict) and "rows" in v else v)
                        for k, v in K.items()}
        out["kscan_full_path"] = kp
    refA = rows_csv(E.base_ref("A1_none")[1])
    refB = rows_csv(E.base_ref("rbl_B1_lead62_pc_k2")[1])
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
                 burn_time_s=dict(p99=float(np.percentile(col(rows, "burn_time"), 99)), max=float(col(rows, "burn_time").max())),
                 h_max_m=dict(p99=float(np.percentile(col(rows, "h_max"), 99)), max=float(col(rows, "h_max").max())))
        ref = refA if spec["prof"] == "A1" else refB
        if ref:
            e["vs_stored_band_table"] = mcnemar(col(ref, "ok") > 0.5, ok)
        out["cond"][name] = e
    with open(os.path.join(OUT, "cap_rule.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for k, v in out["grid"].items():
        print(f"{k:20s} cap {v['cap_m']} m (rg11 {v['reviewer_rg11_cap_m']}) reserve@62 {100 * v['reserve_at_62m']:.1f} % "
              f"non-monotone {v['closing_heights_above_first_failure']}", flush=True)
    for k, v in out["kscan"].items():
        print("kscan", k, v, flush=True)
    for k, v in out["cond"].items():
        vs = v.get("vs_stored_band_table", {})
        print(f"{k:26s} P {v['P']:.3f} {[round(x, 3) for x in v['P_wilson']]} exhausted {v['exhausted']} usable p01 "
              f"{v['usable_left_kg']['p01']:.3f} kg min {v['usable_left_kg']['min']:.3f} burn max {v['burn_time_s']['max']:.2f} s"
              + (f" | vs stored -{vs['lost']}/+{vs['gained']} p {vs['p_exact']:.3g}" if vs else ""), flush=True)


def main():
    if "grid" in PARTS:
        part_grid()
    if "kscan" in PARTS:
        part_kscan()
    if "cond" in PARTS:
        part_cond("B1")
    if "a1" in PARTS:
        part_cond("A1")
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
