"""m2_rg11a_growth v1 (GNC, 2026-10-13): review REV-GNC-1 RG-11 (a), throat growth frozen above J_ref. How much does the
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
Output: <out>/rg11a_growth.json"""
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

VERSION = "m2_rg11a_growth v1"
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


def main():
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
