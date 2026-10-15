"""FD-07 re-routed coil (CAD v3.4.1 feed): route check, ENG-07 slew rates and hose end reactions at the 8 deg stop (v1, 2026-10-13, Mechanical).

1. Re-evaluates the parts_feed v3.4.1 FEED (the grid candidate selected in coil_reroute_v341_v4.json: z_end 74, fq_az 303, fq_r 54, R_min_plan
   41.5, r_max 56, r_pref 50, rigid hose-end sleeve 15 mm, TEE side aim -12 deg) with coil_reroute_v341.evaluate (same gates), so the CAD
   that make_all builds is the one whose clearances are reported.
2. ENG-07 worst vector slew rate at 7.4 V and 6.6 V (coil_route_trade_v34.worst_rate, actuator_slew_v2 servo lines) for EI 0.05 / 0.184
   (break-even limit) / 0.25 / 0.5 N m2 (pressurised EI ASSUMED; B-FD-1 measures it).
3. Hose end reactions for the assembled FEA (S-3D gimbal cases LC3 / GS / SR): linear 3-D frame (hose_frame.solve, engine end node 0 driven
   by a rotation about an axis through the pivot, fixed end clamped), scaled from theta = 1e-3 rad to the 8 deg stop, 36 axis directions.
   Engine-end wrench (F, M) at the FD-07A sleeve exit (TEE side port) and fixed-end wrench (equilibrium transfer to FD-07B) per EI.
   Braided hose: the pressure end load P*A is carried by the braid between the two ferrules, so no net pressure thrust reaches the TEE
   (momentum flux ~1 N at 0.26 kg/s, neglected); pressurised bending stiffness is inside the EI range.  Linear theory at 8 deg: first-order.
Output: calcs/hose_end_reactions_v341_v1.json.  DERIVED (EI ASSUMED).
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import parts_feed as pf
import hose_frame as hf
import coil_route_trade_v34 as ct
import coil_reroute_v341 as cr
import tvc_kinematics as tk

OUT = HERE / "hose_end_reactions_v341_v1.json"
STOP = 8.0
EIS = (0.05, 0.184, 0.25, 0.5)


def main():
    t0 = time.time()
    c, fe, t = pf.FEED["coil"], pf.FEED["ferrule"], pf.FEED["tee"]
    params = {"z_end": c["z_end"], "fq_az": c["fq_az"], "fq_r": c["fq_r"], "R_min_plan": c["R_min_plan"], "r_max": c["r_max"],
              "r_pref": c["r_pref"], "ferrule.len": fe["len"], "tee.side_aim": t["side_aim"]}
    rec = cr.evaluate(params, eng07=False)
    S = {}
    pf._HOSE_U.clear()
    f = pf.route(S)
    hose = f["hose"]
    nodes = hose[::3] * 1e-3
    if not np.allclose(nodes[-1], hose[-1] * 1e-3):
        nodes = np.vstack([nodes, hose[-1] * 1e-3])
    K1 = ct.k_matrix(nodes, 1.0)
    eng07 = {}
    for EI in EIS:
        eng07[str(EI)] = {"K_max_Nm_rad": round(float(np.linalg.svd(K1 * EI, compute_uv=False)[0]), 2),
                          **{f"{V}V": ct.worst_rate(K1 * EI, V, vector=True) for V in ("7.4", "6.6")}}
    th = 1e-3
    sc = math.radians(STOP) / th
    r_eng, r_fix = nodes[0], nodes[-1]
    reac = {}
    for EI in EIS:
        best = {"F_eng": (0, None), "M_eng": (0, None), "F_fix": (0, None), "M_fix": (0, None), "Mp": (0, None)}
        rows = []
        for ph in np.arange(0.0, 360.0, 10.0):
            ax = (math.cos(math.radians(ph)), math.sin(math.radians(ph)), 0.0)
            _, (F, M, Mp), _, _ = hf.solve(nodes, EI, axis=ax, theta=th)
            F8, M8, Mp8 = F * sc, M * sc, Mp * sc
            Ffix = -F8
            Mfix = -(M8 + np.cross(r_eng - r_fix, F8))
            row = {"axis_az_deg": float(ph), "F_eng_N": [round(float(x), 3) for x in F8], "M_eng_Nm": [round(float(x), 4) for x in M8],
                   "F_fix_N": [round(float(x), 3) for x in Ffix], "M_fix_Nm": [round(float(x), 4) for x in Mfix],
                   "M_pivot_Nm": [round(float(x), 4) for x in Mp8]}
            rows.append(row)
            for key, vec in (("F_eng", F8), ("M_eng", M8), ("F_fix", Ffix), ("M_fix", Mfix), ("Mp", Mp8)):
                n = float(np.linalg.norm(vec))
                if n > best[key][0]:
                    best[key] = (n, float(ph))
        reac[str(EI)] = {"max": {k: {"norm": round(v[0], 4), "axis_az_deg": v[1]} for k, v in best.items()}, "rows": rows}
    out = {"id": "hose_end_reactions_v341", "version": "v1", "date": "2026-10-13", "owner": "mechanical",
           "script": "03-cad/src/calcs/hose_end_reactions_v341.py", "method": __doc__,
           "feed_params": params, "route_check": rec, "ENG07_worst_vector_dps": eng07,
           "nodes_m": {"engine_end": [round(float(x), 5) for x in r_eng], "fixed_end": [round(float(x), 5) for x in r_fix], "n": int(len(nodes))},
           "frame": "engine frame, pivot origin, +Z forward (m, N, N m); engine at the 8 deg stop, rotation axis horizontal at axis_az",
           "reactions_8deg": reac,
           "tag": "DERIVED (linear frame; EI ASSUMED 0.05-0.5 N m2, 0.184 = ENG-07 break-even; B-FD-1 measures pressurised EI)",
           "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: rec.get(k) for k in ("feasible", "length_mm", "sweep_deg", "saddle_nominal", "wall_clr_stop_mm", "case_clr_stop_mm",
                                                "tee_riser_clr_stop_mm", "Rmin_stop_mm", "K_max_per_EI", "EI_breakeven_Nm2", "gates", "plan_end_err_mm",
                                                "plan_end_heading_err_deg", "plan_residual_before_closure", "Fq_mm", "Fe_mm", "z_range_mm", "r_range_mm")},
                     default=float, indent=0))
    print(json.dumps(rec.get("saddle_tilt"), default=float))
    print(json.dumps(eng07, indent=0))
    for EI in EIS:
        print(EI, json.dumps(reac[str(EI)]["max"]))
    print("done", out["t_s"])


if __name__ == "__main__":
    main()
