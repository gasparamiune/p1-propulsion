"""REV-GNC-3 reviewer analysis: RG-16 miss-side budget with the random term taken AT THE DETECTOR OUTPUT (line 175 (6)).

Input: rg16held_<CASE>.npz from rv_rg16_held.py (reproduces the author's per-run statistics exactly) and the author's
rg16_fct_terms_v2.json (mass-estimate terms, purge term, b_sys median, Form B) for the same comparator.
Budget convention of the author (m2_rg16_fct_terms v2.1 side_budget): random 1 sigma = (p50 - p1) / 2.326 of the pooled
statistic, RSS the mass-estimate random 1 sigma; bias = mass bias bound + purge term + |median b_sys|; total = 3 RSS + bias;
the miss side passes if 670 (1 - total) > 650 N (allowed 2.985 %).
Detector (m2_fc_thrust v1.1): 20 ms filter, 100 Hz frames, abort iff min over 3 consecutive frames > 650 N.
Statistics at the detector output:
  H1  instantaneous held output: min over frames k-2..k of (fa / ft) - 1, the 3 frames inside the author's selection
  H1d same with the detector's own form min(fa[k-2..k]) / ft[k] - 1
  MW  sustained-fault view: max of H1 over the last W frames (the fault is detected within W iff 670 (1 + MW) > 650)
"""
import json
import os
import sys
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv

D = os.environ["RV_OUT"]
AUTH = json.load(open(os.environ["RV_AUTH"]))
Z = 2.326
ALLOW = 1.0 - 650.0 / 670.0


def q(x, p):
    return float(np.percentile(x, p))


def runs(case):
    z = np.load(os.path.join(D, f"rg16held_{case}.npz"))
    n = len([k for k in z.files if k.startswith("fa_")])
    for i in range(n):
        yield i, z[f"fa_{i}"], z[f"ft_{i}"], z[f"nf_{i}"], z[f"sel_{i}"]


def analyse(case, mkey):
    b = AUTH["budget"][mkey]["miss_side"]
    s_mass = b["mass_1sigma"]
    bias = b["bias_sum"]
    eps_all, h1, h1d, noise, sysp, lag1, lag2 = [], [], [], [], [], [], []
    per_run_med_h1, per_run_med_eps = [], []
    WS = (5, 10, 20, 30, 50, 100)
    mw = {w: [] for w in WS}
    for i, fa, ft, nf, sel in runs(case):
        r = np.full(len(fa), np.nan)
        ok = ft > 1.0
        r[ok] = fa[ok] / ft[ok] - 1.0
        eps_all.append(r[sel])
        nz = np.where(sel, (fa - nf) / np.where(ok, ft, 1.0), np.nan)
        noise.append(nz[sel])
        sysp.append((nf / np.where(ok, ft, 1.0) - 1.0)[sel])
        # lag correlations of the frame noise inside the selection
        for L, acc in ((1, lag1), (2, lag2)):
            m_ = sel[L:] & sel[:-L]
            acc.append(np.stack([nz[L:][m_], nz[:-L][m_]]))
        if len(fa) < 3:
            continue
        s3 = swv(sel, 3).all(axis=1)                      # frames k = 2..n-1 (index j = k - 2)
        rr = np.where(np.isnan(r), np.inf, r)
        e1 = swv(rr, 3).min(axis=1)
        e1d = swv(fa, 3).min(axis=1) / np.where(ft[2:] > 1.0, ft[2:], 1.0) - 1.0
        h1.append(e1[s3])
        h1d.append(e1d[s3])
        if s3.any():
            per_run_med_h1.append(float(np.median(e1[s3])))
            per_run_med_eps.append(float(np.median(r[sel])))
        for w in WS:
            if len(e1) < w:
                continue
            full = swv(s3, w).all(axis=1)
            mx = swv(np.where(s3, e1, -np.inf), w).max(axis=1)
            mw[w].append(mx[full])
    E = np.concatenate(eps_all)
    H1 = np.concatenate(h1)
    H1D = np.concatenate(h1d)
    NZ = np.concatenate(noise)
    SY = np.concatenate(sysp)
    rho = [float(np.corrcoef(np.concatenate([a[0] for a in acc]), np.concatenate([a[1] for a in acc]))[0, 1]) for acc in (lag1, lag2)]

    def line(x, shift_ref=None, label=""):
        s = (q(x, 50) - q(x, 1)) / Z
        rnd = float(np.hypot(s, s_mass))
        tot = 3.0 * rnd + bias
        o = dict(label=label, n=int(len(x)), p1=q(x, 1), p50=q(x, 50), s_1sigma=s, total=tot, passes=bool(670.0 * (1.0 - tot) > 650.0),
                 share_below_allow=float(np.mean(x <= -ALLOW)),
                 share_below_allow_after_bias=float(np.mean(x - (b["purge_term"] + AUTH["mass_budget_A1_fc"]["bias_linear_bound"]) <= -ALLOW)))
        if shift_ref is not None:
            sh = q(E, 50) - q(x, 50)                    # > 0: the statistic reads lower than the single frame (hurts the miss side)
            o["median_shift_vs_single_frame"] = sh
            o["total_with_shift"] = tot + sh
            o["passes_with_shift"] = bool(670.0 * (1.0 - (tot + sh)) > 650.0)
        return o

    out = dict(case=case, comparator_key=mkey, allowed_total=ALLOW, s_mass=s_mass, bias_author=bias,
               author_total_single_frame=b["total"], author_formB_total=b["formB_per_flight"]["total"],
               frame_noise=dict(sd=float(np.std(NZ)), p1=q(NZ, 1), p50=q(NZ, 50), rho_lag1=rho[0], rho_lag2=rho[1]),
               systematic_part=dict(p1=q(SY, 1), p50=q(SY, 50), s_1sigma=(q(SY, 50) - q(SY, 1)) / Z),
               single_frame=line(E, None, "D0 single frame (author)"),
               held_inst=line(H1, True, "D1 held output, instantaneous (min of 3 frames of fa/ft)"),
               held_inst_det=line(H1D, True, "D1d held output, min(fa)/ft[k]"),
               per_flight_detector=dict(n_runs=len(per_run_med_h1),
                                        s_run_med_h1=(q(per_run_med_h1, 50) - q(per_run_med_h1, 1)) / Z,
                                        s_run_med_eps=(q(per_run_med_eps, 50) - q(per_run_med_eps, 1)) / Z),
               windowed={f"W{w}_{w * 10}ms": line(np.concatenate(mw[w]), True, f"D2 max of held output over {w * 10} ms") for w in WS if mw[w]})
    pf = out["per_flight_detector"]
    for k_ in ("s_run_med_h1", "s_run_med_eps"):
        rnd = float(np.hypot(pf[k_], s_mass))
        pf[k_ + "_total"] = 3.0 * rnd + bias
    return out


if __name__ == "__main__":
    res = {c: analyse(c, k) for c, k in (("H_cal_comp_path", "H_cal_comp_path"), ("H_cal_path", "H_cal_path"))}
    json.dump(res, open(os.path.join(D, "rv_rg16_budget.json"), "w"), indent=1)
    for c, o in res.items():
        print(f"== {c}: allowed {100 * o['allowed_total']:.3f} % | author single-frame {100 * o['author_total_single_frame']:.3f} % "
              f"Form B {100 * o['author_formB_total']:.3f} % | bias {100 * o['bias_author']:.3f} % s_mass {100 * o['s_mass']:.3f} %")
        fn = o["frame_noise"]
        print(f"   frame noise sd {100 * fn['sd']:.3f} % rho1 {fn['rho_lag1']:.3f} rho2 {fn['rho_lag2']:.3f} | systematic s {100 * o['systematic_part']['s_1sigma']:.3f} %")
        for k in ("single_frame", "held_inst", "held_inst_det"):
            L = o[k]
            ex = f" shift {100 * L['median_shift_vs_single_frame']:+.3f} -> {100 * L['total_with_shift']:.3f} % {L['passes_with_shift']}" if "total_with_shift" in L else ""
            print(f"   {L['label'][:58]:58s} n {L['n']:6d} p1 {100 * L['p1']:+.3f} p50 {100 * L['p50']:+.3f} s {100 * L['s_1sigma']:.3f} "
                  f"total {100 * L['total']:.3f} % {L['passes']}{ex} | <=-allow {L['share_below_allow']:.5f} after bias {L['share_below_allow_after_bias']:.5f}")
        for k, L in o["windowed"].items():
            print(f"   {L['label'][:58]:58s} n {L['n']:6d} p1 {100 * L['p1']:+.3f} p50 {100 * L['p50']:+.3f} s {100 * L['s_1sigma']:.3f} "
                  f"total {100 * L['total']:.3f} % {L['passes']} shift {100 * L['median_shift_vs_single_frame']:+.3f} -> {100 * L['total_with_shift']:.3f} % "
                  f"{L['passes_with_shift']} | <=-allow {L['share_below_allow']:.5f} after bias {L['share_below_allow_after_bias']:.5f}")
        pf = o["per_flight_detector"]
        print(f"   per-flight at detector: runs {pf['n_runs']} s(med held) {100 * pf['s_run_med_h1']:.3f} % -> total {100 * pf['s_run_med_h1_total']:.3f} % | "
              f"s(med eps) {100 * pf['s_run_med_eps']:.3f} % -> {100 * pf['s_run_med_eps_total']:.3f} %")
