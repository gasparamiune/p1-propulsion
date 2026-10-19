"""m2_rg11a_growth v1.1 (GNC, 2026-10-13): review REV-GNC-1 RG-11 (a), throat growth frozen above J_ref. How much does the
B1 cap of the m2_cap_rule v1.1 grid move when the growth keeps rising in proportion to J beyond J_ref?

sim6 (v2.7 throat model): growth(t) = g x min(1, J(t) / J_ref), J = int (F / F_max)^0.68 dt, J_ref = the nominal flight's J
of the cycle (run6 DERIVED). Above J_ref the growth is held at g (the reviewer's point: 27 % of the 62 m band runs exceed J_ref;
a J-proportional law gives 12.1-12.4 % at g 0.11, rg12).
J-proportional emulation without a simulator change: truth throat_jref' = X J_ref and throat_g' = X g with X = 2, so
growth = X g min(1, J / (X J_ref)) = g J / J_ref for every J <= 2 J_ref (checked per flight: J / J_ref at MECO is recorded and
must stay below 2). The flight software keeps its own growth knowledge (web_jref = J_ref, web_ghat unchanged): only the truth
law changes.
Cases: B1 62 m regression-band corner of m2_cap_rule (a 0.6, n 0.68, g 0.11), flight FSW W1p (burn limit action 1 +
Pc-based apex predictor), k (delivered thrust per flow) 1.00 and 0.97; grid 45-68 m in 0.25 m steps, nominal flight (no wind,
no noise), the same +25 % reserve rule (usable N2O = liquid left - 3 % trapped >= 25 % of the N2O burned) and the same cap
definition (largest grid height such that every height up to it closes).
Identity check: the frozen law ('frozen') must reproduce the stored m2_cap_rule grid (cap and reserve at every height) on the
current simulator (sim6 v2.8-dev amendments M-S, options off for B1).
v1.1 (after v1 found the cap unchanged because the nominal corner flights stay at J / J_ref <= 1.02): the reviewer's
population, the dispersed Monte Carlo, flown with both laws on the same draws (seed 101, 500 runs, paired exact McNemar):
  band   B1 62 m regression band + growth U(0.07, 0.11) per run, FSW W1p (m2_web_limit W1p; frozen = the stored web_W1p table)
  cond   B1 62 m corner k 1.00 (a 0.6, n 0.68, g 0.11 fixed), FSW W1p (m2_cap_rule cond_B1_corner_k1.00_h62_W1p)
The 'frozen' arms are re-flown and compared value by value with the stored tables (identity on the current simulator).
Env: GNC_RG11A_PARTS (grid,mc,eval), GNC_RG11A_SPLIT k/n.
Output: <out>/rg11a_growth.json, <out>/rg11a_<case>_<law>.csv"""
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RG11A_OUT", f"{S}/rg11a_growth")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_cap_rule as CR  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_rg11a_growth v1.1"
PARTS = os.environ.get("GNC_RG11A_PARTS", "grid,mc,eval").split(",")
SPLIT = os.environ.get("GNC_RG11A_SPLIT", "0/1")
N = 500
STORED_MC = {"band": f"{S}/web_limit/web_W1p.csv", "cond": f"{S}/cap_rule/cond_B1_corner_k1.00_h62_W1p.csv"}
X = 2.0
KS = (1.00, 0.97)
A_, N_, G_ = CR.CORNERS["corner"]
STORED = f"{S}/cap_rule/cap_grid.json"


def nominal(over, m, k, law):
    cfg = R.cfg_of(**dict(over, m_n2o=m))
    jref = float(cfg.get("throat_jref") or 0.0)
    c = dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.01)
    dr = dict(reg_a=A_, reg_n=N_, isp_scale=1.0)
    c.update(CR.WL.web_over(dr, (0.0, 0.0, 0.0), CR.WL.CASES["W1p"], jref)[0])     # FSW: web_jref = J_ref
    g = G_
    if law == "jprop":
        c["throat_jref"] = X * jref
        g = X * G_
    res, rec, info = R.fly(c, dict(R.DISP, thrust_scale=k, reg_a=A_, reg_n=N_, throat_g=g), nrec=20000)
    t = rec[:, CR.I["t"]]
    burned = float(np.sum(0.5 * (rec[1:, CR.I["mox"]] + rec[:-1, CR.I["mox"]]) * np.diff(t)))
    liq = float(res["liq_left"])
    usable = liq - CR.PC.TRAP * m
    return dict(h=float(over["h_target"]), reserve=usable / burned if burned > 0 else float("nan"),
                closes=bool(R.success(res) and usable >= CR.PC.RESERVE * burned), landed_ok=bool(R.success(res)),
                J_over_Jref=float(res["throat_J"]) / jref if jref > 0 else None, growth_end=float(res["throat_g_end"]),
                t_meco=float(res["t_meco"]), burn_time=float(res["burn_time"]), h_max=float(res["h_max"]))


def fly_mc(case, law):
    import m2_mc6 as M  # noqa: F401
    if case == "band":
        cfg = CR.WL.base_cfg()[0]
    else:
        over, m = CR.b1_over()
        cfg = R.cfg_of(**dict(over, m_n2o=m, h_target=62.0))
    D = R.draw(np.random.default_rng(101), N, cfg)
    Z = CR.WL.meas_draws(N)
    jref = float(cfg.get("throat_jref") or 0.0)
    rows = []
    for i in range(N):
        d = dict(D[i]) if case == "band" else dict(D[i], thrust_scale=1.00, reg_a=A_, reg_n=N_, throat_g=G_)
        c, disp = R.run_cfg(cfg, d)
        wo, am, nm = CR.WL.web_over(d, Z[i], CR.WL.CASES["W1p"], jref)
        c = dict(c, **wo)
        if law == "jprop":
            c["throat_jref"] = X * jref
            disp = dict(disp, throat_g=X * float(disp["throat_g"]))
        res = R.fly(c, disp, nrec=10)[0]
        r = CR.WL.row_of(i, d, res, am, nm, cfg) if case == "band" else R.flat_row(i, d, res, R.success(res), cfg)
        r["J_over_Jref"] = float(res["throat_J"]) / jref if jref > 0 else float("nan")
        r["growth_end"] = float(res["throat_g_end"])
        rows.append(r)
    return rows


def part_mc():
    import m2_mc6 as M
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    jobs = [(c, l_) for c in ("band", "cond") for l_ in ("frozen", "jprop")][k::n]
    for case, law in jobs:
        p = os.path.join(OUT, f"rg11a_{case}_{law}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100:
            print("exists", case, law, flush=True)
            continue
        t0 = time.time()
        rows = fly_mc(case, law)
        M.write_csv(p, rows)
        print(f"mc {case} {law}: P {np.mean([float(r['ok']) for r in rows]):.3f} exhausted "
              f"{sum(float(r['exhausted']) > 0.5 for r in rows)} ({time.time() - t0:.0f} s)", flush=True)


def part_eval_mc():
    import csv
    from scipy.stats import binomtest
    out = json.load(open(os.path.join(OUT, "rg11a_growth.json"))) if os.path.exists(os.path.join(OUT, "rg11a_growth.json")) else {}
    out["version"] = VERSION
    mc = {}
    for case in ("band", "cond"):
        rr = {l_: list(csv.DictReader(open(os.path.join(OUT, f"rg11a_{case}_{l_}.csv")))) for l_ in ("frozen", "jprop")
              if os.path.exists(os.path.join(OUT, f"rg11a_{case}_{l_}.csv"))}
        if len(rr) < 2:
            continue
        st = list(csv.DictReader(open(STORED_MC[case])))
        keys = [k_ for k_ in st[0] if k_ in s6.RES_NAMES]
        mism = sum(1 for a, b in zip(rr["frozen"], st) for k_ in keys
                   if not (float(a[k_]) == float(b[k_]) or (np.isnan(float(a[k_])) and np.isnan(float(b[k_])))))
        o0 = np.array([float(r["ok"]) > 0.5 for r in rr["frozen"]])
        o1 = np.array([float(r["ok"]) > 0.5 for r in rr["jprop"]])
        lost, gained = int(np.sum(o0 & ~o1)), int(np.sum(~o0 & o1))
        jr = np.array([float(r["J_over_Jref"]) for r in rr["jprop"]])
        ge0 = np.array([float(r["growth_end"]) for r in rr["frozen"]])
        ge1 = np.array([float(r["growth_end"]) for r in rr["jprop"]])
        ul = lambda rows: np.array([float(r["liq_left"]) for r in rows])  # noqa: E731
        mc[case] = dict(stored=STORED_MC[case], identity_frozen_vs_stored=dict(fields=len(keys), runs=len(st), mismatches=mism),
                        P_frozen=float(o0.mean()), P_jprop=float(o1.mean()), lost=lost, gained=gained,
                        p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0,
                        exhausted_frozen=int(sum(float(r["exhausted"]) > 0.5 for r in rr["frozen"])),
                        exhausted_jprop=int(sum(float(r["exhausted"]) > 0.5 for r in rr["jprop"])),
                        share_J_above_Jref=float(np.mean(jr > 1.0)), J_over_Jref_max=float(jr.max()),
                        J_below_X=bool(jr.max() < X), growth_end_pct_frozen_max=100 * float(ge0.max()),
                        growth_end_pct_jprop_max=100 * float(ge1.max()),
                        liq_left_shift_g_p01_p50=[float(np.percentile(1e3 * (ul(rr["jprop"]) - ul(rr["frozen"])), q)) for q in (1, 50)],
                        liq_left_g_p01=[float(np.percentile(1e3 * ul(rr[l_]), 1)) for l_ in ("frozen", "jprop")])
        print(f"{case}: identity mism {mism} | P {o0.mean():.3f} -> {o1.mean():.3f} (-{lost}/+{gained}) | exhausted "
              f"{mc[case]['exhausted_frozen']} -> {mc[case]['exhausted_jprop']} | J>Jref {100 * mc[case]['share_J_above_Jref']:.1f} % "
              f"max {jr.max():.3f} | growth end max {mc[case]['growth_end_pct_frozen_max']:.2f} -> "
              f"{mc[case]['growth_end_pct_jprop_max']:.2f} % | liq p01 {mc[case]['liq_left_g_p01']}", flush=True)
    out["mc"] = mc
    with open(os.path.join(OUT, "rg11a_growth.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "rg11a_growth.json"), flush=True)


def main():
    if "grid" in PARTS:
        main_grid()
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval_mc()


def main_grid():
    os.makedirs(OUT, exist_ok=True)
    over, m = CR.b1_over()
    hs = np.arange(CR.H_LO, CR.H_HI + 1e-9, CR.DH)
    st = json.load(open(STORED))
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(), X=X,
               corner=dict(a=A_, n=N_, g=G_), cases={})
    for k in KS:
        ref = st[f"W1p|corner|k{k:.2f}"]
        for law in ("frozen", "jprop"):
            t0 = time.time()
            rows = [nominal(dict(over, h_target=float(h)), m, k, law) for h in hs]
            cl = np.array([r["closes"] for r in rows])
            ff = int(np.argmin(cl)) if not cl.all() else len(cl)
            cap = float(hs[ff - 1]) if ff > 0 else None
            r62 = rows[int(np.argmin(np.abs(hs - 62.0)))]
            e = dict(k=k, law=law, cap_m=cap, closing_heights_above_first_failure=int(np.sum(cl[ff:])),
                     reserve_at_62m=r62["reserve"], growth_end_at_62m=r62["growth_end"], J_over_Jref_at_62m=r62["J_over_Jref"],
                     J_over_Jref_max=max(r["J_over_Jref"] for r in rows), grid=rows)
            if law == "frozen":
                diffs = [(a["h"], a["reserve"], b["reserve"]) for a, b in zip(rows, ref["grid"])
                         if a["reserve"] != b["reserve"] or a["closes"] != b["closes"]]
                e["identity_vs_stored"] = dict(stored=f"{STORED} W1p|corner|k{k:.2f}", stored_cap_m=ref["cap_m"],
                                               cap_equal=bool(cap == ref["cap_m"]), height_mismatches=len(diffs),
                                               first=diffs[:5])
            else:
                e["J_over_Jref_below_X"] = bool(e["J_over_Jref_max"] < X)
            out["cases"][f"k{k:.2f}|{law}"] = e
            print(f"k {k:.2f} {law:6s}: cap {cap} m | reserve@62 {100 * r62['reserve']:.2f} % | growth end@62 "
                  f"{100 * r62['growth_end']:.2f} % | J/Jref@62 {r62['J_over_Jref']:.3f} max {e['J_over_Jref_max']:.3f}"
                  + (f" | identity cap {e['identity_vs_stored']['cap_equal']} mism {e['identity_vs_stored']['height_mismatches']}"
                     if law == "frozen" else "") + f" ({time.time() - t0:.0f} s)", flush=True)
    for k in KS:
        a, b = out["cases"][f"k{k:.2f}|frozen"], out["cases"][f"k{k:.2f}|jprop"]
        out["cases"][f"k{k:.2f}|delta"] = dict(cap_shift_m=(b["cap_m"] - a["cap_m"]) if (a["cap_m"] and b["cap_m"]) else None,
                                               reserve_shift_at_62m_pts=100 * (b["reserve_at_62m"] - a["reserve_at_62m"]))
    with open(os.path.join(OUT, "rg11a_growth.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "rg11a_growth.json"), flush=True)


if __name__ == "__main__":
    main()
