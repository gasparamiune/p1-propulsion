"""m2_meco_eval v2.2 (v2.2: no ENG-05 entry for a case without MECO, profile B; v2.1 stopped there). Evaluate the MECO / tail-off / relight cases (m2_meco_mc.py; v2: NC-closed relight timeline, relight altitude): P (Wilson), paired exact McNemar vs AD_prov_2kg and
vs a named comparator, apogee, MECO thrust fraction and ENG-05 time to 10 % per run (reduced model), tail-off impulse,
propellant, relight command-to-90 % (t90_relight). Env GNC_OUT / GNC_SUFFIX as m2_meco_mc.py.
Output: <out>/meco_eval_<suf>.json"""
import csv
import json
import os
import sys
import numpy as np
from scipy.stats import binomtest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, tailoff  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/meco")
SUF = os.environ.get("GNC_SUFFIX", "mr")
COMP = {"mr_toff": "AD_prov_2kg", "mr_td72": "mr_toff", "mr_td70": "mr_td72", "mr_td72_fix": "mr_td72",
        "mr_td72_fix_rs20": "mr_td72_fix", "mr_td72_tign10": "mr_td72", "mr_td72_tign20": "mr_td72",
        "mr_td72_tign30": "mr_td72", "mr_f125_td72_floorstart": "mr_f125", "mr_f125_td72_rs20": "mr_f125_td72_floorstart",
        "mr_J2.7_fix_td72": "mr_J2.7_fix", "mr_J1.6_fix_td72": "mr_J2.7_fix_td72", "mr_fins_f20_td72_fix": "mr_fins_f20",
        "mr_AF_fix": "mr_AF", "mr_AF_fix_td72": "mr_AF", "mr_B_fix": "mr_B", "mr_B_fix_toff": "mr_B",
        "mr_td72_ncmin": "mr_td72", "mr_td72_nc": "mr_td72", "mr_td72_nc_unplanned": "mr_td72_nc",
        "mr_td72_nc_m10": "mr_td72_nc", "mr_td72_nc_m20": "mr_td72_nc", "mr_td72_nc_m30": "mr_td72_nc",
        "mr_fsw_J1.6": "mr_J1.6_fix_td72", "mr_fsw_J1.6_nc": "mr_fsw_J1.6", "mr_f125_rs20_nc": "mr_f125_td72_rs20",
        "mr_AF_fix_td72_nc": "mr_AF_fix_td72", "mr_td72_nc_ecu": "mr_td72_nc", "mr_AF_nc": "mr_AF",
        "mr_AF_td72_nc": "mr_AF_nc", "mr_AF_fix_td72_nc_rat": "mr_AF_fix_td72_nc", "mr_AF_rat_nc": "mr_AF_fix_td72_nc",
        "mr_fsw_J1.6_nc_rat": "mr_fsw_J1.6_nc", "mr_B_fix_toff_rat": "mr_B_fix_toff"}


def rows(c):
    p = os.path.join(OUT, f"mc6_runs_{c}_{SUF}.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def pair(a, b):
    oa = np.array([int(r["ok"]) for r in a]) > 0
    ob = np.array([int(r["ok"]) for r in b]) > 0
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), loses=bool(ob.mean() < oa.mean() and p < 0.05),
                lost_runs=[int(r["run"]) for r, x, y in zip(a, oa, ob) if x and not y],
                gained_runs=[int(r["run"]) for r, x, y in zip(a, oa, ob) if y and not x])


def pct(x, q):
    return float(np.percentile(x, q)) if len(x) else float("nan")


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUF}.json")))["cases"]
    base = rows("AD_prov_2kg")
    comb = R.sources()["comb"]
    try:
        chk, sha, _ = tailoff.load_checks(comb)
        tl, tf, vs, _tg = tailoff.table(chk, 0.25)
        cal = tailoff.calibration(sha, 0.25)
    except Exception as e:  # noqa: BLE001
        chk = None
        print("no tail-off table:", e)
    out = {}
    for c in S:
        r = rows(c)
        if r is None:
            continue
        g = lambda k: np.array([float(x[k]) for x in r])  # noqa: E731
        ok = g("ok") > 0.5
        lo, hi = R.wilson(int(ok.sum()), len(ok))
        cfg = S[c]["config"]
        tsc = g("thrust_scale")
        fme = g("F_meco_cmd")
        frac = np.where(fme > 0, fme / (500.0 * tsc), np.nan)
        rec = dict(case=c, note=S[c]["note"], P=float(ok.mean()), ci95=[lo, hi], fail_modes=S[c]["summary"]["fail_modes"],
                   m_n2o_sized_kg=S[c]["m_n2o_sized_kg"], m_n2o_mc_kg=S[c]["m_n2o_mc_kg"],
                   nominal=dict((k, S[c]["nominal"][k]) for k in ("h_max", "t_meco", "prop_used", "liq_left", "F_meco_cmd",
                                                                     "tailoff_imp", "t90_relight", "burn_time")
                                if k in S[c]["nominal"]),
                   h_max=dict(mean=float(g("h_max").mean()), p01=pct(g("h_max"), 1), p50=pct(g("h_max"), 50),
                              p99=pct(g("h_max"), 99), min=float(g("h_max").min()), max=float(g("h_max").max())),
                   prop_used=dict(mean=float(g("prop_used").mean()), p99=pct(g("prop_used"), 99)),
                   liq_left=dict(mean=float(g("liq_left").mean()), p01=pct(g("liq_left"), 1), min=float(g("liq_left").min())),
                   ENG07b_longest_ep_p99_s=pct(g("act_sat_max_dur"), 99))
        if np.isfinite(frac).any():
            fr = frac[np.isfinite(frac)]
            rec["meco_thrust_frac"] = dict(mean=float(fr.mean()), max=float(fr.max()), p99=pct(fr, 99),
                                           n_above_0p75=int(np.sum(fr > 0.75 + 1e-9)))
        ti = g("tailoff_imp")
        if (ti > 0).any():
            rec["tailoff_imp_Ns"] = dict(mean=float(ti[ti > 0].mean()), max=float(ti.max()))
        if chk is not None and int(cfg.get("toff_model", 0)) == 1:
            t10 = np.array([tailoff.simulate(f / ts, tl, tf, vs, cal["lag_a_s"], cal["lag_c_s"], cal["l_cut_mm"])[0]
                            if f > 0 else np.nan for f, ts in zip(fme, tsc)])
            t10 = t10[np.isfinite(t10)]
            if len(t10):   # v2.2: profile B has no MECO (no commanded cut-off level), so no ENG-05 time to 10 %
                rec["ENG05_t10_s"] = dict(max=float(t10.max()), p99=pct(t10, 99), mean=float(t10.mean()),
                                          pass_all=bool(t10.max() <= 0.100))
        t9 = g("t90_relight")
        t9v = t9[t9 > 0]
        if len(t9v):
            rec["t90_relight_s"] = dict(min=float(t9v.min()), p01=pct(t9v, 1), p50=pct(t9v, 50), p99=pct(t9v, 99),
                                        max=float(t9v.max()), frac_ge_0p53=float(np.mean(t9v >= 0.53)),
                                        frac_ge_0p65=float(np.mean(t9v >= 0.65)), n=int(len(t9v)),
                                        n_not_reached=int(np.sum(t9 <= 0)))
        tti = g("t_ign")
        rec["t_ign_draw_s"] = dict(min=float(tti.min()), max=float(tti.max()))
        rec["t_ign_est_s"] = float(cfg.get("t_ign_est", R.DEF["t_ign_est"]))
        # v2: relight command altitude / speed and the altitude at 90 % of the start level (constant-speed estimate under
        # the drogue: h_ign + v_ign t90), for the NC-closed relight timeline
        h_i, v_i = g("h_ign"), g("v_ign")      # v2.1: renamed (v2 shadowed the Wilson bound 'hi' and the print failed)
        okr = (h_i > 0) & (t9 > 0)
        if okr.any():
            h90 = h_i[okr] + v_i[okr] * t9[okr]
            rec["relight_cmd_h_m"] = dict(p01=pct(h_i[okr], 1), p50=pct(h_i[okr], 50), p99=pct(h_i[okr], 99), min=float(h_i[okr].min()))
            rec["relight_cmd_v_mps"] = dict(p01=pct(v_i[okr], 1), p50=pct(v_i[okr], 50), p99=pct(v_i[okr], 99))
            rec["h_at_t90_est_m"] = dict(p01=pct(h90, 1), p50=pct(h90, 50), min=float(h90.min()))
        if base is not None and c != "AD_prov_2kg":
            rec["vs_baseline"] = pair(base, r)
        if c in COMP and rows(COMP[c]) is not None:
            rec["vs_" + COMP[c]] = pair(rows(COMP[c]), r)
        out[c] = rec
        vb = rec.get("vs_baseline", {})
        vc = rec.get("vs_" + COMP.get(c, "-"), {})
        t9s = rec.get("t90_relight_s", {})
        print(f"{c:26s} P {rec['P']:.3f} [{lo:.3f},{hi:.3f}] vsBase -{vb.get('lost', '')}/+{vb.get('gained', '')} "
              f"p {vb.get('p', float('nan')):.2g}{' LOSES' if vb.get('loses') else ''} | vs {COMP.get(c, '-')} "
              f"-{vc.get('lost', '')}/+{vc.get('gained', '')} p {vc.get('p', float('nan')):.2g} | hmax {rec['h_max']['p50']:.1f} "
              f"[{rec['h_max']['p01']:.1f},{rec['h_max']['p99']:.1f}] | prop {rec['prop_used']['mean']:.3f} liq_min "
              f"{rec['liq_left']['min']:.3f} | Fmeco {rec.get('meco_thrust_frac', {}).get('max', float('nan')):.3f} "
              f"t10max {rec.get('ENG05_t10_s', {}).get('max', float('nan')):.3f} | t90 {t9s.get('p01', float('nan')):.3f}/"
              f"{t9s.get('p50', float('nan')):.3f}/{t9s.get('max', float('nan')):.3f} | sized {rec['m_n2o_sized_kg']:.4f}")
    with open(os.path.join(OUT, f"meco_eval_{SUF}.json"), "w") as f:
        json.dump(dict(version=f"m2_meco_eval v2.2 {SUF}", cases=out), f, indent=1, default=float)


if __name__ == "__main__":
    main()
