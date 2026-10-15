"""rg10_settling v1 (independent GNC review, 2026-10-13): first estimate of the A1 axial specific force from MECO to RELIGHT
(the input the lead asked of GNC for the 'retained vapour <= 19 cm3' design requirement, CHANGELOG 2026-10-13 line 102),
and of the MECO -> RELIGHT hold duration (the window for the stale-flag rule).

Method (DERIVED from simulation records, nominal flight only, no dispersion):
  - author's 6-DOF nominal A1 flight (plan 0.81 s, liquid-line median delay; recorded by rg05 part 'nominal' with the author's
    PC.nominal configuration, 0.1 s records): vertical specific force f_z = dvz/dt + g by central differences; the vehicle is
    nose-up from liftoff to touchdown (nose-first coast, nose drogue engine-down descent), so f_z is the axial specific force
    to within cos(attitude error). f_z < 0: apparent gravity on the liquid points to the nose (liquid away from the outlet);
    f_z > 0: liquid settles toward the engine.
  - reviewer's 1-DOF nominal A1 flight (rg03_vertical v1.1, same plan and delay), same differencing.
Limitations: 0.1 s records smooth the drogue-inflation and MECO transients; lateral / rotational accelerations and the slosh
model are not included; the segment geometry (where the MV and the seat sit relative to the tank outlet) is Mechanical's.
Output: rg10_settling.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
G = 9.80665


def regimes(t, vz, t_meco, t_cmd, t_light):
    a = np.gradient(vz, t)
    f = a + G
    s = (t >= t_meco + 0.3) & (t <= t_light)          # after the MECO tail-off
    out = dict(t_meco=float(t_meco), t_relight_cmd=float(t_cmd), t_light=float(t_light),
               hold_MECO_to_relight_cmd_s=float(t_cmd - t_meco), hold_MECO_to_light_s=float(t_light - t_meco))
    # apogee: first sign change of vz after MECO
    idx = np.where((t > t_meco) & (vz <= 0.0))[0]
    t_apo = float(t[idx[0]]) if idx.size else float("nan")
    out["t_apogee"] = t_apo
    fs, ts = f[s], t[s]
    out["fz_min_mps2"] = float(fs.min())
    out["fz_max_mps2"] = float(fs.max())
    for lab, lo, hi in (("MECO_to_apogee", t_meco + 0.3, t_apo), ("apogee_to_relight_cmd", t_apo, t_cmd), ("relight_cmd_to_light", t_cmd, t_light)):
        m = (t >= lo) & (t <= hi)
        if m.sum() < 2:
            continue
        out[lab] = dict(duration_s=float(hi - lo), fz_mean_mps2=float(np.mean(f[m])), fz_min_mps2=float(np.min(f[m])),
                        fz_max_mps2=float(np.max(f[m])), time_fz_negative_s=float(np.sum(f[m] < 0.0) * np.median(np.diff(t))),
                        time_fz_abs_below_0p1g_s=float(np.sum(np.abs(f[m]) < 0.1 * G) * np.median(np.diff(t))),
                        time_fz_above_0p5g_s=float(np.sum(f[m] > 0.5 * G) * np.median(np.diff(t))))
    # last continuous settling interval (f_z > 0.5 g) before the light
    m = (t <= t_light) & (t >= t_apo)
    ok = (f > 0.5 * G) & m
    last = 0.0
    run = 0.0
    dt = float(np.median(np.diff(t)))
    for k in np.where(m)[0]:
        run = run + dt if ok[k] else 0.0
        last = run
    out["settled_above_0p5g_continuous_before_light_s"] = float(last)
    return out


def main():
    res = {}
    d = json.load(open(os.path.join(HERE, "rg05_sens.json")))["nominal"]["A1_plan0.81_liq_med"]
    h = np.array(d["hist"])
    c = {k: h[:, i] for i, k in enumerate(d["hist_cols"])}
    t, vz = c["t"], c["vz"]
    # relight command time: t_relight recorded by the author's sim; light = first F > 1 N after the coast
    t_cmd = float(d["t_relight"])
    on = np.where((t > d["t_meco"] + 1.0) & (c["F"] > 1.0))[0]
    t_light = float(t[on[0]]) if on.size else float("nan")
    res["author_6dof_nominal"] = regimes(t, vz, d["t_meco"], t_cmd, t_light)
    import rg03_vertical as V
    r = V.fly("A", 300.0, 16.0746 - 2.0, False, d_ign=0.3152, t_est=0.81)
    hm = np.array(r["hist"])
    m = {k: hm[:, i] for i, k in enumerate(r["hist_cols"])}
    res["reviewer_1dof_nominal"] = regimes(m["t"], m["v"], r["t_meco"], r["t_cmd"], r["t_light"])
    print(json.dumps(res, indent=1))
    json.dump(dict(script="rg10_settling v1", results=res), open(os.path.join(HERE, "rg10_settling.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
