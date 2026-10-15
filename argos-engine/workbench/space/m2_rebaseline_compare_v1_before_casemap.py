"""Re-baseline comparison for gnc.json v3: the same Monte Carlo cases flown on two interface sets (v2: mechanical.json v1,
combustion.json v1 x relay; v3: mechanical.json v2, combustion.json v2.x map), same draws (seed 101).

Per case present in both run sets: P(landing) with Wilson 95 % interval, paired exact McNemar (runs lost / gained on
the same dispersion draws; the pairing is checked on the wind column), liftoff mass, N2O load and tank, landing mass
and touchdown percentiles, hinge and gimbal percentiles. Vehicle: dry and gimballed mass, CG, pivot station and the
tail-wags-dog zeros of the two twd tables. A change is flagged MATERIAL when (lead request 2026-10-12):
  * P(landing) is lower with McNemar p < 0.05 (the rule used for every requirement comparator), or
  * liftoff mass changes by more than 1 % (DESIGN threshold, about 0.16 kg: the ledger's own item uncertainty is larger), or
  * a tail-wags-dog zero at touchdown changes by more than 5 % or falls below the 20 rad/s requirement (gnc.json v2).
Inputs: GNC_OUT_OLD + GNC_SUFFIX_OLD (default out/m2, v2), GNC_OUT + GNC_SUFFIX (default out/m3, v3), GNC_VEH_OLD /
GNC_VEH_OUT (vehicle outputs), GNC_VEH_TAG_OLD / GNC_VEH_TAG. Output: GNC_RES/rebaseline_<old>_<new>.json and .csv.
Run: python scripts/m2_rebaseline_compare.py
"""
import csv
import json
import os
import sys
import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R  # noqa: E402

OLD = os.environ.get("GNC_OUT_OLD", "/home/claude/work/space/out/m2")
SO = os.environ.get("GNC_SUFFIX_OLD", "v2")
NEW = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m3")
SN = os.environ.get("GNC_SUFFIX", "v3")
VOLD = os.environ.get("GNC_VEH_OLD", "/home/claude/work/space/out/vehicle")
VNEW = os.environ.get("GNC_VEH_OUT", "/home/claude/work/space/out/vehicle_v3")
TOLD = os.environ.get("GNC_VEH_TAG_OLD", "v3c")
TNEW = os.environ.get("GNC_VEH_TAG", "v3d")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v3")
os.makedirs(RES, exist_ok=True)
ALPHA = 0.05
MASS_TOL = 0.01      # DESIGN materiality threshold on liftoff mass (fraction)
TWD_TOL = 0.05       # DESIGN materiality threshold on the tail-wags-dog zero (fraction)
TWD_REQ = 20.0       # gnc.json v2 requirement: TWD zero at touchdown >= 20 rad/s


def rows_of(out, case, suf):
    p = os.path.join(out, f"mc6_runs_{case}_{suf}.csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return list(csv.DictReader(f))


def jl(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return None


def twd_rows(path):
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def main():
    So = jl(os.path.join(OLD, f"mc6_summary_{SO}.json"))["cases"]
    Sn = jl(os.path.join(NEW, f"mc6_summary_{SN}.json"))["cases"]
    out = dict(tool="m2_rebaseline_compare v1", old=dict(out=OLD, suffix=SO), new=dict(out=NEW, suffix=SN),
               rule=dict(P="lower with exact McNemar p < 0.05 on the same draws", liftoff_mass=f"> {MASS_TOL:.0%} change",
                         twd=f"> {TWD_TOL:.0%} change or below {TWD_REQ} rad/s at touchdown"),
               cases={}, vehicle={}, material=[])
    table = []
    for c in Sn:
        if c not in So:
            continue
        ra, rb = rows_of(OLD, c, SO), rows_of(NEW, c, SN)
        if ra is None or rb is None or len(ra) != len(rb):
            continue
        same = all(abs(float(x["wind"]) - float(y["wind"])) < 1e-9 for x, y in zip(ra, rb))
        oa = np.array([int(r["ok"]) for r in ra]) > 0
        ob = np.array([int(r["ok"]) for r in rb]) > 0
        lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
        p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
        a, b = So[c], Sn[c]
        sa, sb = a["summary"], b["summary"]

        def g(s, k):
            return s.get(k) if isinstance(s.get(k), (int, float)) else None
        rec = dict(case=c, pairing_valid=bool(same), sim_old=a.get("sim"), sim_new=b.get("sim"),
                   engine_old=a.get("engine_model"), engine_new=b.get("engine_model"),
                   P_old=float(oa.mean()), P_new=float(ob.mean()),
                   ci_old=list(R.wilson(int(oa.sum()), len(oa))), ci_new=list(R.wilson(int(ob.sum()), len(ob))),
                   lost=lost, gained=gained, mcnemar_exact_p=float(p),
                   loses=bool(same and ob.mean() < oa.mean() and p < ALPHA),
                   fail_modes_old=sa.get("fail_modes"), fail_modes_new=sb.get("fail_modes"),
                   m_liftoff_old=a.get("m_liftoff_kg"), m_liftoff_new=b.get("m_liftoff_kg"),
                   m_n2o_sized_old=a.get("m_n2o_sized_kg"), m_n2o_sized_new=b.get("m_n2o_sized_kg"),
                   m_n2o_flown_old=a.get("m_n2o_mc_kg"), m_n2o_flown_new=b.get("m_n2o_mc_kg"),
                   tank_L_old=a.get("tank_V_L"), tank_L_new=b.get("tank_V_L"),
                   z_pivot_old=a.get("z_pivot_m"), z_pivot_new=b.get("z_pivot_m"),
                   zcg0_old=a.get("zcg0_m"), zcg0_new=b.get("zcg0_m"),
                   m_land_nominal_old=(a.get("nominal") or {}).get("m_land"), m_land_nominal_new=(b.get("nominal") or {}).get("m_land"),
                   prop_used_nominal_old=(a.get("nominal") or {}).get("prop_used"),
                   prop_used_nominal_new=(b.get("nominal") or {}).get("prop_used"))
        for k in ("td_vz_p99", "td_vh_p99", "td_tilt_p99", "td_rate_p99", "td_miss_p50", "max_hinge_p99", "max_hinge_max",
                  "max_gim_p99", "max_gim_rate_p99", "liq_left_p01", "prop_used_p99"):
            rec[k + "_old"], rec[k + "_new"] = g(sa, k), g(sb, k)
        if rec["m_liftoff_old"] and rec["m_liftoff_new"]:
            rec["d_liftoff_frac"] = rec["m_liftoff_new"] / rec["m_liftoff_old"] - 1.0
        out["cases"][c] = rec
        table.append({k: (v if not isinstance(v, (list, dict)) else json.dumps(v)) for k, v in rec.items()})
        print(f"{c:30s} P {rec['P_old']:.3f} -> {rec['P_new']:.3f} (-{lost}/+{gained}, p {p:.3g}{' LOSES' if rec['loses'] else ''}"
              f"{'' if same else ', DRAWS DIFFER'}) liftoff {rec['m_liftoff_old']:.3f} -> {rec['m_liftoff_new']:.3f} kg"
              if rec["m_liftoff_old"] else f"{c} P {rec['P_old']:.3f} -> {rec['P_new']:.3f}", flush=True)
        if rec["loses"]:
            out["material"].append(f"{c}: P(landing) {rec['P_old']:.3f} -> {rec['P_new']:.3f} ({lost} lost / {gained} gained, "
                                   f"McNemar p = {p:.2g})")
        if rec.get("d_liftoff_frac") is not None and abs(rec["d_liftoff_frac"]) > MASS_TOL:
            out["material"].append(f"{c}: liftoff mass {rec['m_liftoff_old']:.3f} -> {rec['m_liftoff_new']:.3f} kg "
                                   f"({100 * rec['d_liftoff_frac']:+.1f} %)")
    # vehicle and tail-wags-dog
    vo = jl(os.path.join(VOLD, f"vehicle_{TOLD}.json")) or {}
    vn = jl(os.path.join(VNEW, f"vehicle_{TNEW}.json")) or {}
    for k in ("m_liftoff_kg", "m_land_nominal_kg", "z_pivot_m", "d_body_m", "tank_internal_length_m"):
        out["vehicle"][k] = dict(old=vo.get(k), new=vn.get(k))
    for k in ("dry_kg", "propulsion_kg", "airframe_kg", "gimballed_dry_kg"):
        out["vehicle"]["sums_" + k] = dict(old=(vo.get("sums") or {}).get(k), new=(vn.get("sums") or {}).get(k))
    to = twd_rows(os.path.join(VOLD, f"twd_table_{SO}.csv"))
    tn = twd_rows(os.path.join(VNEW, f"twd_table_{SN}.csv"))
    tw = []
    for r in tn:
        m = [x for x in to if x["state"] == r["state"] and x["F_label"] == r["F_label"]]
        if not m:
            continue
        o = m[0]
        rec = dict(state=r["state"], F_label=r["F_label"])
        for k in ("w_twd_rad_s", "J_twd_kgm2", "l_p_m", "l_e_m", "m_e_kg", "I_e_own_kgm2", "Mc_per_deg_Nm"):
            if k in r and k in o:
                rec[k + "_old"], rec[k + "_new"] = float(o[k]), float(r[k])
        w0, w1 = rec.get("w_twd_rad_s_old"), rec.get("w_twd_rad_s_new")
        if w0 and w1 and np.isfinite(w0) and np.isfinite(w1):
            rec["d_w_frac"] = w1 / w0 - 1.0
            if r["state"] == "touchdown" and (abs(rec["d_w_frac"]) > TWD_TOL or w1 < TWD_REQ):
                out["material"].append(f"TWD zero at touchdown {r['F_label']}: {w0:.2f} -> {w1:.2f} rad/s "
                                       f"({100 * rec['d_w_frac']:+.1f} %)" + (" BELOW the 20 rad/s requirement" if w1 < TWD_REQ else ""))
        tw.append(rec)
    out["twd"] = tw
    for r in tw:
        if r["F_label"] in ("12.5 %", "20.0 %", "hover (T=W)", "100.0 %"):
            print(f"TWD {r['state']:9s} {r['F_label']:12s} {r.get('w_twd_rad_s_old', float('nan')):6.2f} -> "
                  f"{r.get('w_twd_rad_s_new', float('nan')):6.2f} rad/s  J_twd {r.get('J_twd_kgm2_old', float('nan')):.4f} -> "
                  f"{r.get('J_twd_kgm2_new', float('nan')):.4f}  l_p {r.get('l_p_m_old', float('nan')):.3f} -> {r.get('l_p_m_new', float('nan')):.3f}")
    print("vehicle", json.dumps(out["vehicle"], default=float))
    print("MATERIAL:", out["material"] or "none")
    with open(os.path.join(RES, f"rebaseline_{SO}_{SN}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    if table:
        keys = []
        for r in table:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(os.path.join(RES, f"rebaseline_{SO}_{SN}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(table)
    print("written", os.path.join(RES, f"rebaseline_{SO}_{SN}.json"))


if __name__ == "__main__":
    main()
