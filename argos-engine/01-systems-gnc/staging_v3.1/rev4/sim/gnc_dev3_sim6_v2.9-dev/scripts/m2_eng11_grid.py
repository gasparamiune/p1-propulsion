"""m2_eng11_grid v1.0 (GNC rev4, 2026-10-19): ENG-11 final requirement on the V5c structure as is, by a direct K_s grid
instead of bisection. Reason: the v1.1 'ksmin' and 'mink' parts bisect under a monotonicity assumption that the pose scan
contradicts (fixed notch: alpha passes at K_s 87 / 116 / 174 but fails at 145; beta passes at 116 / 145 but fails at
87 / 174), so their single 'K_s min' numbers are not valid requirements (they are kept as found, SUPERSEDED by this grid).
Hypothesis tested here (H-B): the failures between passing K_s values come from the engine rocking mode at full tank
coinciding with the ASSUMED first bending mode (m2_csi: uniform PETG tube, E 2.0 GPa ASSUMED; 24.30 Hz full / 25.64 Hz
landing on v3.5.1). Comparator: the same grid with every condition's bending frequency scaled by 0.9 and 1.1.
Refutation: the failing K_s band does not move with the bending frequency (then the cause is elsewhere).
Model, conditions, notch rule, metric and corner set exactly as m2_eng11 v1.1 (imported, not copied): V5c structure
mech_T, nominal J 1.6e-3, kinematics 'cons', fixed ECU notch Q 1 / -12 dB at c = 1 x e x f(centre pose), e in
{0.95, 1, 1.05}, zeta 0.02 / 0.05 / 0.10, floor20 set; ENG-07d: stable and upper GM >= 6 dB at every corner.
Output out/rev4/eng11/lin_v351/eng11_grid.json. DERIVED (linear), K_s / J / bending ASSUMED; not physical approval."""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_eng11 as E  # noqa: E402

VERSION = "m2_eng11_grid v1.0"
KS_GRID = tuple(float(k) for k in range(70, 271, 10))
KS_SHIFT = (87.0, 116.0, 145.0, 174.0)


def row(M, a, Ks, wb_scale=1.0):
    if wb_scale != 1.0:
        conds0 = M.conds
        M.conds = {k: dict(v, w_b=v["w_b"] * wb_scale) for k, v in conds0.items()}
        E._CACHE.clear()
    try:
        r = E.scan(M, (Ks,), E.J_C, "cons", "T", ("fixed", 1.0) + E.NOTCH_ECU, axes=(a,))[f"{a}|Ks{Ks:g}"]
    finally:
        if wb_scale != 1.0:
            M.conds = conds0
            E._CACHE.clear()
    f = r["floor20"]
    fulls = [v["I_piv"] for k, v in M.conds.items() if k.startswith("full")]
    f_full = [M.f(p, a, Ks, E.J_C, "cons", "T", Ip=fulls[0]) if fulls else None for p in M.poses]
    return dict(K_s=Ks, wb_scale=wb_scale, pass_6dB=f["pass_6dB"], gm_up_min_dB=f["gm_up_min_dB"],
                pm_abs_min_deg=f["pm_abs_min_deg"], sm_min=f["sm_min"], n_below_6dB=f["n_below_6dB"],
                n_unstable=f["n_unstable"], worst=f["worst"],
                f_landing_pose_range_Hz=[min(q["f_land_Hz"] for q in r["per_pose"].values()),
                                         max(q["f_land_Hz"] for q in r["per_pose"].values())],
                f_full_pose_range_Hz=(None if f_full[0] is None else [min(f_full), max(f_full)]),
                rigid_with_lowest_notch=r.get("rigid_with_lowest_notch"),
                f62_gm_up_min_dB=r["f62"]["gm_up_min_dB"])


def main():
    t0 = time.time()
    d5, T, n_m, gchk = E.v5c_table()
    conds, meta, src, extra, cchk = E.conditions()
    M = E.Model(T, n_m, conds)
    fb = {k: v["w_b"] / (2 * np.pi) for k, v in conds.items()}
    out = dict(version=VERSION, date=time.strftime("%Y-%m-%d"), base_script=dict(version=E.VERSION, sha256_16=E.sha16(E.__file__)),
               iface=os.environ.get("GNC_IFACE"), mass_variant=E.MASS_VARIANT, cfg_ballast=extra,
               bending_Hz_by_condition=fb, condition_names=list(conds), grid=[], shift=[])
    for a in E.AXES:
        for Ks in KS_GRID:
            tt = time.time()
            r = row(M, a, Ks)
            r["axis"] = a
            out["grid"].append(r)
            print(f"grid {a:5s} Ks {Ks:5.0f}: {'PASS' if r['pass_6dB'] else 'fail'} GM {r['gm_up_min_dB']:.2f} dB |PM| "
                  f"{r['pm_abs_min_deg']:.1f} deg sm {r['sm_min']:.3f} f_land {r['f_landing_pose_range_Hz'][0]:.1f}-"
                  f"{r['f_landing_pose_range_Hz'][1]:.1f} Hz worst {r['worst'][:70]} ({time.time() - tt:.0f} s)", flush=True)
    for a in E.AXES:
        for Ks in KS_SHIFT:
            for sc in (0.9, 1.1):
                tt = time.time()
                r = row(M, a, Ks, sc)
                r["axis"] = a
                out["shift"].append(r)
                print(f"shift {a:5s} Ks {Ks:5.0f} w_b x{sc}: {'PASS' if r['pass_6dB'] else 'fail'} GM {r['gm_up_min_dB']:.2f} dB "
                      f"|PM| {r['pm_abs_min_deg']:.1f} worst {r['worst'][:70]} ({time.time() - tt:.0f} s)", flush=True)
    out["wall_s"] = round(time.time() - t0, 1)
    p = os.path.join(E.OUT, "eng11_grid.json")
    json.dump(out, open(p, "w"), indent=1, default=float)
    print("wrote", p, E.sha16(p), flush=True)


if __name__ == "__main__":
    main()
