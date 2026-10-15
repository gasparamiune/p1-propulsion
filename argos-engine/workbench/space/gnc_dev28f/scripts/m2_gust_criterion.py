"""m2_gust_criterion v1 (GNC, 2026-10-13): review REV-GNC-1 RG-06, launch-commit turbulence criterion, with the lead's interim
B1 rule (mean wind < 6 m/s until B-PNT-1 passes) folded in.

Problem: run6 ties the Dryden intensity to the mean wind, sigma_w = 0.1 W20 x U(0.5, 1.5) (MIL-F-8785C low-altitude form), so a
mean-wind limit bounds turbulence only inside the model. Here the horizontal turbulence intensity at the anemometer height is
drawn INDEPENDENTLY of the mean wind and the success probability is mapped on (mean wind, sigma_u).

Model (no sim change): sim6 sets sigma_w = 0.1 W20 gust_scale and sigma_u(h) = sigma_w / (0.177 + 0.000823 h_ft)^0.4; for a
target sigma_u at the anemometer height Z_ANEM the run's gust_scale is set to sigma_w / (0.1 W20), sigma_w = sigma_u x
(0.177 + 0.000823 Z_ANEM_ft)^0.4 (exact inversion of the sim6 formula). The other draws (seed 101) and the turbulence noise
sequence are unchanged, so every run pairs with its model-tied twin. sigma_u ~ U(0, SIG_MAX) from its own generator (seed
RNG_SIG).
Bases: B1 = m2_web_limit W1p (B1 62 m, regression band + growth, burn limit action 1, RG-10 predictor); A1 = v2.8 liquid plan
0.81 s, A1_none (relight NOT closed, RG-01: the A1 rows are the liquid-line baseline).
Cases (GNC_GUST_CASES):
  B1_map, A1_map   1000 runs, mean wind U(0, 8) m/s at 10 m (as run6), sigma_u(3 m) ~ U(0, 2.5) m/s independent
  B1_lim, A1_lim   the proposed commit limit flown: mean wind U(0, W_LIM) (run6 draw rescaled), every run at sigma_u = S_LIM
  B1_tied, A1_tied the same rescaled mean wind with the model-tied turbulence (comparator)
Proposed criterion (sensor and averaging): 2-D ultrasonic anemometer at 3 m AGL within 30 m of the pad, >= 4 Hz; mean wind = 2-min
vector mean scaled to 10 m with the 1/7-type profile of the model (alpha 0.14; W10 = W3 (10/3)^0.14); sigma_u = standard deviation
of the 1-s means of the horizontal speed over the last 10 min (about 130 Dryden correlation times at 5 m/s: +/- 6 % sampling
error, 1 sigma); both evaluated at T-2 min and confirmed at T-0 (hold at the limit). ASSUMED: the 10-min sigma of the 1-s means
estimates the Dryden sigma_u (no low-frequency mesoscale content); ACEMA site statistics TO-DEFINE.
Output: <out>/gust_criterion.json, <out>/gust_<case>.csv."""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_GUST_OUT", f"{S}/gust_criterion")
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_eng03_rate as E  # noqa: E402

VERSION = "m2_gust_criterion v1"
PARTS = os.environ.get("GNC_GUST_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_GUST_SPLIT", "0/1")
NMAP = int(os.environ.get("GNC_GUST_NMAP", "1000"))
NLIM = 500
SEED = 101
RNG_SIG = 20261027
SIG_MAX = 2.5            # m/s, upper end of the mapped sigma_u(3 m) (model-tied B1/A1 MC reaches ~1.65 m/s at 6 m/s)
Z_ANEM = 3.0             # m AGL, anemometer height (proposal)
ALPHA = 0.14             # run6 wind_alpha (ASSUMED open terrain)
W_LIM = float(os.environ.get("GNC_GUST_WLIM", "6.0"))     # m/s at 10 m (lead interim rule for B1)
S_LIM = float(os.environ.get("GNC_GUST_SLIM", "1.0"))     # m/s sigma_u(3 m), proposal checked by the *_lim cases


def den04(z_m):
    hft = max(z_m, 1.0) / 0.3048
    return (0.177 + 0.000823 * hft) ** 0.4


def gust_scale_for(sig_u, w10):
    w20 = w10 * (6.1 / 10.0) ** ALPHA
    if w20 <= 1e-6:
        return 0.0
    return sig_u * den04(Z_ANEM) / (0.1 * w20)


def sig_u_tied(w10, gs):
    """sigma_u(3 m) of the model-tied draw."""
    return 0.1 * w10 * (6.1 / 10.0) ** ALPHA * gs / den04(Z_ANEM)


def bases():
    cfgB, overB, mB, noteB = WL.base_cfg()
    overA, _, jA = E.base_ref("A1_none")
    mA = json.load(open(jA))["m_n2o_mc_kg"]
    cfgA = R.cfg_of(**dict({k: v for k, v in overA.items() if k != "m_fixed"}, m_n2o=float(mA)))
    return {"B1": cfgB, "A1": cfgA}


def case_list():
    return {"B1_map": ("B1", "map", NMAP), "A1_map": ("A1", "map", NMAP),
            "B1_lim": ("B1", "lim", NLIM), "A1_lim": ("A1", "lim", NLIM),
            "B1_tied": ("B1", "tied", NLIM), "A1_tied": ("A1", "tied", NLIM)}


def fly(prof, cfg, dr, i, kind, sig_draw, Z):
    c, disp = R.run_cfg(cfg, dr)
    w10 = float(dr["_wind"])
    if kind in ("lim", "tied"):
        w10 = w10 * W_LIM / 8.0
        c["wind"] = w10
    if kind == "map":
        su = float(sig_draw[i])
        c["gust_scale"] = gust_scale_for(su, w10)
    elif kind == "lim":
        su = S_LIM
        c["gust_scale"] = gust_scale_for(su, w10)
    else:
        su = sig_u_tied(w10, float(dr["_gust_scale"]))
    if prof == "B1":
        wo, am, nm = WL.web_over(dr, Z[i], WL.CASES["W1p"], float(cfg.get("throat_jref") or 0.0))
        c.update(wo)
    res = R.fly(c, disp, nrec=10)[0]
    row = R.flat_row(i, dr, res, R.success(res), cfg)
    row["wind10"] = w10
    row["sigma_u3"] = su
    row["gust_scale_used"] = float(c.get("gust_scale", dr["_gust_scale"]))
    return row


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    B = bases()
    k, n = (int(x) for x in SPLIT.split("/"))
    sel = os.environ.get("GNC_GUST_CASES")
    names = [c for c in case_list() if (not sel or c in sel.split(","))][k::n]
    for name in names:
        p = os.path.join(OUT, f"gust_{name}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_GUST_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        prof, kind, nr = case_list()[name]
        cfg = B[prof]
        t0 = time.time()
        D = R.draw(np.random.default_rng(SEED), nr, cfg)
        sig = np.random.default_rng(RNG_SIG).uniform(0.0, SIG_MAX, nr)
        Z = WL.meas_draws(max(nr, WL.N))
        rows = [fly(prof, cfg, D[i], i, kind, sig, Z) for i in range(nr)]
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        print(f"{name:8s}: P {ok.mean():.3f} n {nr} ({time.time() - t0:.0f} s)", flush=True)


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def part_eval():
    from scipy.stats import binomtest
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, anemometer_height_m=Z_ANEM, alpha=ALPHA,
               sigma_u_max=SIG_MAX, W_lim_10m=W_LIM, S_lim_3m=S_LIM, rng_sigma=RNG_SIG,
               model=("sigma_u(3 m) imposed through gust_scale (exact inversion of the sim6 Dryden intensity), independent of the "
                      "mean wind; other draws seed 101 unchanged"), cases={})
    for name, (prof, kind, nr) in case_list().items():
        rows = rows_csv(os.path.join(OUT, f"gust_{name}.csv"))
        if not rows:
            continue
        ok = col(rows, "ok") > 0.5
        w = col(rows, "wind10")
        su = col(rows, "sigma_u3")
        e = dict(n=len(rows), P=float(ok.mean()), P_wilson=list(R.wilson(int(ok.sum()), len(rows))))
        if kind == "map":
            grid = []
            for wl, wh in ((0, 4), (4, 6), (6, 8.01)):
                for sl, sh in ((0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 2.51)):
                    m = (w >= wl) & (w < wh) & (su >= sl) & (su < sh)
                    if m.sum():
                        grid.append(dict(wind10=[wl, min(wh, 8.0)], sigma_u3=[sl, min(sh, 2.5)], n=int(m.sum()),
                                         P=float(ok[m].mean()), P_wilson=list(R.wilson(int(ok[m].sum()), int(m.sum()))),
                                         fails=int((~ok[m]).sum())))
            e["grid"] = grid
            # cumulative: P over the commit region {W < W_LIM, sigma_u <= s}
            cum = []
            for s in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5):
                m = (w < W_LIM) & (su <= s)
                cum.append(dict(sigma_u3_max=s, n=int(m.sum()), P=float(ok[m].mean()),
                                P_wilson=list(R.wilson(int(ok[m].sum()), int(m.sum())))))
            e["commit_region_cumulative_W_lt_lim"] = cum
            # failure modes vs sigma
            fm = {}
            for r, o in zip(rows, ok):
                if o:
                    continue
                why = ("vh" if float(r["td_vh"]) > R.CRIT["vh"] else "") + ("|vz" if abs(float(r["td_vz"])) > R.CRIT["vz"] else "") \
                    + ("|tilt" if float(r["td_tilt"]) > R.CRIT["tilt"] else "") + ("|crash" if float(r["crash"]) > 0.5 or
                                                                                  float(r["landed"]) < 0.5 else "")
                fm.setdefault(why or "other", []).append(dict(run=int(r["run"]), wind10=float(r["wind10"]),
                                                              sigma_u3=float(r["sigma_u3"])))
            e["failures"] = fm
        out["cases"][name] = e
    for prof in ("B1", "A1"):
        a, b = rows_csv(os.path.join(OUT, f"gust_{prof}_tied.csv")), rows_csv(os.path.join(OUT, f"gust_{prof}_lim.csv"))
        if a and b:
            oa, ob = col(a, "ok") > 0.5, col(b, "ok") > 0.5
            lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
            out["cases"][f"{prof}_lim"]["vs_tied"] = dict(P_tied=float(oa.mean()), P_lim=float(ob.mean()), lost=lost, gained=gained,
                                                          p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0,
                                                          sigma_u3_tied_p50_p99_max=[float(np.percentile(col(a, "sigma_u3"), 50)),
                                                                                    float(np.percentile(col(a, "sigma_u3"), 99)),
                                                                                    float(col(a, "sigma_u3").max())])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "gust_criterion.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for k, e in out["cases"].items():
        print(k, f"P {e['P']:.3f} n {e['n']}", e.get("vs_tied", ""), flush=True)
        for g in e.get("grid", []):
            print("    W", g["wind10"], "su", g["sigma_u3"], f"n {g['n']} P {g['P']:.3f} fails {g['fails']}", flush=True)
        for c_ in e.get("commit_region_cumulative_W_lt_lim", []):
            print("    W<lim, su<=", c_["sigma_u3_max"], f"n {c_['n']} P {c_['P']:.3f} {c_['P_wilson']}", flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()
