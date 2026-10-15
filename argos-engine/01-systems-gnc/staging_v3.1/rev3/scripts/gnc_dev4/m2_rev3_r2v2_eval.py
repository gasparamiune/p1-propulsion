"""m2_rev3_r2v2_eval v1.0 (GNC rev3, 2026-10-13): P4 R2 v2 (lead CHANGELOG lines 181 (4), 186 (2)) - window statistics of the
accelerometer release confirmation with Pc invalid under the drogue, threshold re-derivation per baseline mode and window,
margins for all winds and inside W10 < 6 m/s, confirmation-flight summary.

Input: m2_rev3_fly v2.0 tables (sim6 v2.10-dev amendment V2): statistics arms pw|G73|r2s_<case>|h285 (pcf_Facc 1e9: no
release; the pcf_n-frame running minimum of the R2 estimate, maxima over E2 + 0.5 s and E2 + 0.8 s, four baseline modes)
and, when present, confirmation arms pw|G73|r2c_<...>|h285 (release decided by the chosen mode and threshold).
Definitions: a lit run is released inside window w iff its statistic s_w >= T; a flame-out run is falsely released (a dead
vehicle) iff s_w >= T. Lit margin = min over lit runs of s_w - T; flame-out margin = T - max over flame-out runs of s_w.
Design flame-out set = cold-flow DERIVED bound at the hold (fo_cb) and at the onsets 5 / 10 ms (fo_cb_dt05 / dt10);
sensitivities: bound x 1.3 (heat pick-up), HEM nominal, no cold flow, bound without the hold. T_mid = midpoint of the gap
(equal margins). v1.1: a run enters the statistics only if its R2 window opened (statistic > -998: the drogue was still
attached at the Pc-invalid onset); runs released by the Pc branch before a late onset (e.g. onset 10 ms after the light) are
counted apart and carry no R2 statistic (v1.0 pooled their -999 placeholder). SIM on DERIVED / ASSUMED inputs; no hardware
data; not a physical approval.
Output: <out>/r2v2_eval.json."""
import json
import os
import sys
from collections import OrderedDict
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev3_fly as RF  # noqa: E402
import m2_rg01_refly as F  # noqa: E402
from gncsim import run6 as R  # noqa: E402

VERSION = "m2_rev3_r2v2_eval v1.1"
MODES = {0: "E0-frozen (rev2 amendment V)", 1: "E2 re-reference", 2: "E0-frozen + drag compensation",
         3: "E2 re-reference + drag compensation"}
LIT = ("lit_k100", "lit_k875", "lit_k875_L400", "lit_k875_dt05", "lit_k875_dt10")
FO_DESIGN = ("fo_cb", "fo_cb_dt05", "fo_cb_dt10")
FO_SENS = ("fo_cb130", "fo_cn", "fo_none", "fo_cb_nohold")
T_REV2 = 37.15933451611584


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def q(x, ps=(0, 1, 50, 99, 100)):
    x = np.asarray(x, float)
    if x.size == 0:
        return None
    return OrderedDict((("min" if p == 0 else "max" if p == 100 else f"p{p:02d}"), round(float(np.percentile(x, p)), 3))
                       for p in ps)


def load(case):
    out = {}
    for base in F.BASES_MAIN:
        r, p, org = RF.table(base, f"pw|G73|r2s_{case}|h285", src=("rev3",))
        if r:
            out[base] = (r, p)
    return out


def main():
    out = OrderedDict(version=VERSION, date="2026-10-13", method=__doc__.split("\n\n")[1].strip(), modes=MODES, cases=OrderedDict(),
                      thresholds=OrderedDict(), missing=[])
    S = {}
    for case in LIT + FO_DESIGN + FO_SENS:
        d = load(case)
        if not d:
            out["missing"].append(case)
            continue
        S[case] = {}
        for base, (rows, p) in d.items():
            w = col(rows, "wind")
            e = OrderedDict(table=dict(path=p, sha256_16=RF.sha16(p)), n=len(rows), n_W10_lt6=int(np.sum(w < 6.0)),
                            released=int(np.sum(col(rows, "pcf_rel") > 0.5)), aborted=int(np.sum(col(rows, "pcf_abt") > 0.5)),
                            hold_s=q(col(rows, "pv2_hold_s"), (0, 50, 100)), Pt0_bar=q(col(rows, "pv2_Pt0") / 1e5, (0, 50, 100)))
            act0 = col(rows, "pv2_s8_0") > -998.0
            e["n_R2_window"] = int(act0.sum())
            e["n_W10_lt6_R2_window"] = int(np.sum(act0 & (w < 6.0)))
            e["no_R2_window_released_before_onset"] = int(np.sum(~act0))
            if case.startswith("fo"):
                e["Fcold_max_N"] = q(col(rows, "pv2_Fcl_max"), (0, 50, 100))
                e["lift_max_mm"] = q(col(rows, "pv2_l_max"), (0, 50, 100))
                e["cold_mass_g"] = q(1e3 * col(rows, "pv2_mcold"), (0, 50, 100))
            for m in MODES:
                for win in (5, 8):
                    s = col(rows, f"pv2_s{win}_{m}")
                    act = s > -998.0
                    e[f"s{win}_mode{m}"] = OrderedDict(all=q(s[act]), W10_lt6=q(s[act & (w < 6.0)]))
                    S[case].setdefault((m, win), []).append((s[act], w[act]))
            out["cases"][f"{base}|{case}"] = e
    # thresholds per mode and window
    for m in MODES:
        for win in (5, 8):
            def pool(cases, inside=False):
                xs = [s[w < 6.0] if inside else s for c in cases if c in S for (s, w) in S[c].get((m, win), [])]
                return np.concatenate(xs) if xs else np.array([])
            t = OrderedDict()
            for lab, inside in (("all_winds", False), ("W10_lt6", True)):
                lit = pool(LIT, inside)
                fod = pool(FO_DESIGN, inside)
                if lit.size == 0 or fod.size == 0:
                    continue
                lmin, fmax = float(lit.min()), float(fod.max())
                tm = 0.5 * (lmin + fmax)
                e = OrderedDict(lit_min_N=round(lmin, 3), lit_p01_N=round(float(np.percentile(lit, 1)), 3),
                                flameout_design_max_N=round(fmax, 3),
                                flameout_design_p99_N=round(float(np.percentile(fod, 99)), 3),
                                gap_N=round(lmin - fmax, 3), T_mid_N=round(tm, 3), margin_each_side_N=round(0.5 * (lmin - fmax), 3),
                                at_T_rev2=OrderedDict(T=round(T_REV2, 3), lit_margin_N=round(lmin - T_REV2, 3),
                                                      flameout_margin_N=round(T_REV2 - fmax, 3),
                                                      lit_not_released=int(np.sum(lit < T_REV2)),
                                                      flameout_released=int(np.sum(fod >= T_REV2)),
                                                      n_lit=int(lit.size), n_fo=int(fod.size)))
                sens = OrderedDict()
                for c in FO_SENS:
                    x = pool((c,), inside)
                    if x.size:
                        sens[c] = OrderedDict(max_N=round(float(x.max()), 3), margin_at_T_mid_N=round(tm - float(x.max()), 3),
                                              released_at_T_mid=int(np.sum(x >= tm)), n=int(x.size))
                e["sensitivities_at_T_mid"] = sens
                t[lab] = e
            out["thresholds"][f"mode{m}|w{win / 10:.1f}s"] = t
    # confirmation arms (present after the confirmation flights)
    conf = OrderedDict()
    for name, spec in RF.ARMS.items():
        if spec["group"] != "P4c":
            continue
        for base in spec["bases"]:
            r, p, org = RF.table(base, name, src=("rev3",))
            if not r:
                out["missing"].append(f"{base}|{name}")
                continue
            w = col(r, "wind")
            ok = col(r, "ok") > 0.5
            rel = col(r, "pcf_rel")
            relt = col(r, "pcf_relt")
            e = OrderedDict(table=dict(path=p, sha256_16=RF.sha16(p)), P=float(ok.mean()),
                            P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(r))],
                            P_W10_lt6=float(ok[w < 6.0].mean()), released_R2=int(np.sum(rel == 2.0)),
                            aborted=int(np.sum(col(r, "pcf_abt") > 0.5)),
                            release_after_light_s=q(relt[relt >= 0], (0, 50, 99, 100)),
                            fa_at_release_N=q(col(r, "pv2_fa_rel")[relt >= 0], (0, 1, 50)),
                            hold_s=q(col(r, "pv2_hold_s"), (0, 50, 100)), fail_modes={})
            for j in np.where(~ok)[0]:
                k = F.fail_mode(r[j])
                e["fail_modes"][k] = e["fail_modes"].get(k, 0) + 1
            if "fo" in name:
                td = col(r, "td_vz")
                e["dead_vehicle_released"] = int(np.sum(rel == 2.0))
                e["td_vz_m_s"] = q(td, (0, 1, 50, 100))
                e["Fcold_at_release_N"] = q(col(r, "pv2_Fcl_rel")[relt >= 0], (0, 50, 100))
            if spec.get("ref"):
                rr, rp, ro = RF.table(base, spec["ref"])
                if rr:
                    e["paired_vs_" + spec["ref"]] = RF.pair(rr, r)
            conf[f"{base}|{name}"] = e
    out["confirmation"] = conf
    p = os.path.join(RF.OUT, "r2v2_eval.json")
    json.dump(out, open(p, "w"), indent=1, default=float)
    print("wrote", p, RF.sha16(p))
    for k, v in out["thresholds"].items():
        for lab, e in v.items():
            print(f"{k:22s} {lab:9s} lit_min {e['lit_min_N']:8.2f} fo_max {e['flameout_design_max_N']:8.2f} gap {e['gap_N']:8.2f} "
                  f"T_mid {e['T_mid_N']:7.2f} | at 37.16: lit {e['at_T_rev2']['lit_margin_N']:7.2f} fo "
                  f"{e['at_T_rev2']['flameout_margin_N']:7.2f} | sens "
                  + " ".join(f"{c}:{s['max_N']:.1f}" for c, s in e["sensitivities_at_T_mid"].items()))
    for k, e in conf.items():
        print(f"{k:50s} P {e['P']:.3f} W<6 {e['P_W10_lt6']:.3f} relR2 {e['released_R2']} abort {e['aborted']} "
              f"rel_t {e['release_after_light_s']} {('dead ' + str(e.get('dead_vehicle_released'))) if 'fo' in k else ''}")
    if out["missing"]:
        print("missing", out["missing"])


if __name__ == "__main__":
    main()
