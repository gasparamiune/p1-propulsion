"""Feed hose FD-07 coil of CAD v3.4 (lead Option A route, parts_feed.route): hinge stiffness, bend radius and clearances at the
8 deg stop, engine-end reaction, and the ENG-07 slew at 7 deg with the v2 hinge terms (v1, 03-cad/src/calcs, 2026-10-13, Mechanical).

Why: the v3.4 coil is the CAD route (193 deg, 185.9 mm, plan radius >= 41.5 mm, z 72 -> 47) instead of the hose_routing_trade_v2
O3b candidate (300 deg, 0.252 m) that carried K <= 7.79 N m/rad into actuator_slew_v2 (107.75 deg/s at 7.4 V).  ENG-07 and the
REV-GNC-1 request need the number for the routed coil.

Method:
  * centreline = parts_feed.route() (same function the CAD sweeps), flexible part from Q (engine sleeve end) to Fq (fixed sleeve end),
    nodes every 3 mm (as parts_feed.hose_modes).  hose_frame.solve (linear 3-D Euler-Bernoulli frame, fixed end clamped, engine end
    given the rigid rotation about the pivot = engine-frame origin) for unit rotations about X and Y -> the 2x2 hinge stiffness matrix
    K_ij = e_i . M_pivot(j) / theta and its largest singular value (worst moment per rad over tilt directions).
  * bend radius at the stop: installed curvature + |curvature change| at 8 deg (hose_frame v1.1 rule, magnitudes added: conservative),
    36 tilt directions.  Posed centreline (linear field + exact rigid end, parts_feed.hose_centreline_at) at the 8 deg stop in 36
    directions -> clearance to the bay wall (r 70) and to the GM-09 ring top (z 32 for r >= 52); the displacement field does not depend
    on EI (uniform section, displacement-driven).  Hose-to-engine clearance at the stop is in make_all checks (posed solids).
  * ENG-07: actuator_slew_v2.rates_at_pose with L = L_v2 - 2.136 (v2 radial-hose term) + K_max x 7 deg, as v2 (a scalar load opposing
    the motion: conservative for a spring, which aids the return half of every cycle); 2 deg pose / motion scan then 0.5 deg refinement.
Hose EI 0.05 / 0.25 / 0.5 N m2 ASSUMED (-6 PTFE smooth bore, SS braid, pressurised value unknown; B-FD-1 measures K at 0 and 45 bar).
Not modelled: pressure effective axial force (braid angle != 54.7 deg makes a fixed-end hose push or pull), hose damping, inertia.
Output: calcs/coil_o3b_v34_v1.json.
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import config
import tvc_kinematics as tk
import parts_feed as pf
import hose_frame as hf
import actuator_slew_v2 as sv
from actuator_loads import SERVO

OUT = HERE / "coil_o3b_v34_v1.json"
EIS = (0.05, 0.25, 0.5)
STOP, RANGE = 8.0, 7.0
R_WALL, GM09_TOP, GM09_R_IN = 70.0, 32.0, 52.0
MBR_REQ = 39.0                   # mm: hose_routing_trade_v2 rule (G4 datasheet minimum dynamic bend radius <= 39 mm at -6), TO-VERIFY


def k_matrix(nodes, EI, th=1e-3):
    _, (Fx, Mx, Mpx), bx, Ux = hf.solve(nodes, EI, axis=(1, 0, 0), theta=th)
    _, (Fy, My, Mpy), by, Uy = hf.solve(nodes, EI, axis=(0, 1, 0), theta=th)
    K = np.array([[Mpx[0], Mpy[0]], [Mpx[1], Mpy[1]]]) / th
    return K, (Fx / th, Mx / th, Fy / th, My / th)


def main():
    t0 = time.time()
    S = {}
    f = pf.route(S)
    hose = f["hose"]
    nodes = hose[::3] * 1e-3
    if not np.allclose(nodes[-1], hose[-1] * 1e-3):
        nodes = np.vstack([nodes, hose[-1] * 1e-3])
    k0 = hf.curvature_installed(nodes)
    od = pf.FEED["hose"]["od"]
    res = {"id": "coil_o3b_v34", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/coil_o3b_v34.py",
           "supersedes": "hose_routing_trade_v2 O3b candidate numbers for ENG-07 (K 7.79 N m/rad at EI 0.5; kept as the trade record)",
           "method": __doc__.split("\n\n")[2],
           "route": {"engine_end_Q_mm": [round(float(x), 2) for x in f["Q"]], "fixed_end_Fq_mm": [round(float(x), 2) for x in f["Fq"]],
                     "length_mm": round(f["hose_len_mm"], 1), "coil_sweep_deg": round(f["coil_sweep_deg"], 1),
                     "r_range_mm": [round(float(np.hypot(hose[:, 0], hose[:, 1]).min()), 1), round(float(np.hypot(hose[:, 0], hose[:, 1]).max()), 1)],
                     "z_range_mm": [round(float(hose[:, 2].min()), 1), round(float(hose[:, 2].max()), 1)],
                     "installed_Rmin_mm_1mm_points": round(f["hose_Rmin_mm"], 2), "installed_Rmin_mm_3mm_nodes": round(1e3 / k0.max(), 2),
                     "hose_od_mm": od, "n_nodes": len(nodes)},
           "EI_tag": "ASSUMED 0.05-0.5 N m2 (pressurised -6 PTFE/SS braid unknown; B-FD-1)", "per_EI": {}}
    # posed centrelines at the stop (EI-independent field)
    dirs = np.arange(0.0, 360.0, 10.0)
    wall_min, ring_min, worst_w, worst_r = 1e9, 1e9, None, None
    for ph in dirs:
        a, b = tk.cone_to_ab(STOP, ph)
        X = pf.hose_centreline_at(S, a, b)
        r = np.hypot(X[:, 0], X[:, 1])
        cw = R_WALL - (r + od / 2)
        i = int(np.argmin(cw))
        if cw[i] < wall_min:
            wall_min, worst_w = float(cw[i]), (float(ph), [round(float(x), 1) for x in X[i]])
        m = r + od / 2 > GM09_R_IN
        if m.any():
            cr = X[m, 2] - od / 2 - GM09_TOP
            j = int(np.argmin(cr))
            if cr[j] < ring_min:
                ring_min, worst_r = float(cr[j]), (float(ph), [round(float(x), 1) for x in X[m][j]])
    r0 = np.hypot(nodes[:, 0], nodes[:, 1]) * 1e3
    res["clearance_mm"] = {"bay_wall_neutral": round(float((R_WALL - (r0 + od / 2)).min()), 2), "bay_wall_at_8deg_stop": round(wall_min, 2),
                           "bay_wall_worst": {"tilt_dir_deg": worst_w[0], "point_mm": worst_w[1]},
                           "gm09_ring_top_at_8deg_stop": round(ring_min, 2), "gm09_worst": {"tilt_dir_deg": worst_r[0], "point_mm": worst_r[1]} if worst_r else None,
                           "rule": "3 mm (hose_routing_trade_v2 CLR)", "engine": "make_all checks (posed solids, FD-07 re-swept per pose)"}
    for EI in EIS:
        K, (Fx, Mx, Fy, My) = k_matrix(nodes, EI)
        sv_ = np.linalg.svd(K, compute_uv=False)
        Ks = 0.5 * (K + K.T)
        ev = np.linalg.eigvalsh(Ks)
        rmin, arg = 1e9, None
        for ph in dirs:
            ax = (math.cos(math.radians(ph)), math.sin(math.radians(ph)), 0.0)
            _, _, bend, _ = hf.solve(nodes, EI, axis=ax, theta=1e-3)
            dk = bend / EI * (math.radians(STOP) / 1e-3)
            kk = np.maximum(k0[:-1], k0[1:]) + dk
            rr = 1e3 / kk.max()
            if rr < rmin:
                rmin, arg = rr, float(ph)
        th = math.radians(STOP)
        Fmax = max(np.linalg.norm(math.cos(p) * Fx + math.sin(p) * Fy) for p in np.radians(dirs)) * th
        Mmax = max(np.linalg.norm(math.cos(p) * Mx + math.sin(p) * My) for p in np.radians(dirs)) * th
        res["per_EI"][f"EI={EI}"] = {"K_matrix_Nm_per_rad": [[round(float(x), 3) for x in row] for row in K],
                                     "K_alpha_Nm_rad": round(float(K[0, 0]), 3), "K_beta_Nm_rad": round(float(K[1, 1]), 3),
                                     "K_sym_eig_Nm_rad": [round(float(x), 3) for x in ev], "K_max_singular_Nm_rad": round(float(sv_[0]), 3),
                                     "M_hinge_at_7deg_Nm": round(float(sv_[0]) * math.radians(RANGE), 3),
                                     "min_bend_radius_at_8deg_mm": round(rmin, 1), "at_axis_dir_deg": arg,
                                     "MBR_rule_mm": MBR_REQ, "MBR_ok": bool(rmin >= MBR_REQ),
                                     "engine_end_reaction_at_8deg": {"F_N": round(float(Fmax), 2), "M_Nm": round(float(Mmax), 3),
                                                                     "note": "worst over axis directions; at the FD-07A sleeve end Q (engine side)"}}
    # ENG-07 slew
    P, _ = config.build()
    g = tk.geometry(P)
    base = sv.L_V2 - sv.TERMS_V2["hose_radial_L0.40_upper"]
    phis, chis = np.arange(0.0, 360.0, 2.0), np.arange(0.0, 360.0, 2.0)

    def worst(L, V, outward=False):
        Ts, wnl = SERVO[V]
        best = (1e9, None, None)
        for ph in phis:
            w, lim, _ = sv.rates_at_pose(g, 7.0, ph, ([0.0] if outward else chis), Ts, wnl, L)
            k = int(np.argmin(w))
            if w[k] < best[0]:
                best = (float(w[k]), float(ph), float(([0.0] if outward else chis)[k]))
        if not outward:                                   # refine
            for ph in np.arange(best[1] - 4.0, best[1] + 4.01, 0.5):
                cc = np.arange(best[2] - 4.0, best[2] + 4.01, 0.5) % 360.0
                w, lim, _ = sv.rates_at_pose(g, 7.0, ph % 360.0, cc, Ts, wnl, L)
                k = int(np.argmin(w))
                if w[k] < best[0]:
                    best = (float(w[k]), float(ph % 360.0), float(cc[k]))
        return best
    eng07 = {"load_basis": "v2 terms minus the radial-hose term 2.136 plus K_max(EI) x 7 deg (actuator_slew_v2 method)",
             "base_without_hose_Nm": round(base, 4), "cases": {}}
    for EI in EIS + (0.0,):
        Kmax = res["per_EI"][f"EI={EI}"]["K_max_singular_Nm_rad"] if EI > 0 else 0.0
        L = base + Kmax * math.radians(RANGE)
        for V in ("6.6", "7.4", "8.4"):
            wa = worst(L, V)
            wo = worst(L, V, outward=True)
            eng07["cases"][f"EI={EI}|{V}V"] = {"load_Nm": round(L, 4), "worst_any_dps": round(wa[0], 2), "at_pose_phi_deg": wa[1], "motion_chi_deg": wa[2],
                                               "worst_outward_dps": round(wo[0], 2), "ENG07_100dps_any": bool(wa[0] >= 100.0)}
            print(EI, V, eng07["cases"][f"EI={EI}|{V}V"], flush=True)
    eng07["hose_K_breakeven_7V4_Nm_rad"] = "17.17 (any direction) / 17.31 (outward): actuator_slew_v2, unchanged"
    eng07["6V6_note"] = "6.6 V is below 100 deg/s even with a zero-stiffness hose when the EI=0.0 row says so: the 6.6 V case is set by the other v2 terms"
    res["ENG07"] = eng07
    res["unknowns"] = ["pressurised hose EI and the pressure effective axial force (fixed-end hose with braid angle != 54.7 deg): B-FD-1 measures the "
                       "hinge moment vs angle at 0 and 4.5 MPa", "hose maker's minimum dynamic bend radius at -6 (rule <= 39 mm TO-VERIFY at order)",
                       "servo torque-speed shape and plug-to-servo drop (Electronics); pushrod joint friction"]
    res["tag"] = "DERIVED (linear frame on the CAD v3.4 route; EI ASSUMED)"
    res["t_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("route", "clearance_mm")}, indent=1))
    for k, v in res["per_EI"].items():
        print(k, {kk: v[kk] for kk in ("K_alpha_Nm_rad", "K_beta_Nm_rad", "K_max_singular_Nm_rad", "M_hinge_at_7deg_Nm", "min_bend_radius_at_8deg_mm",
                                        "engine_end_reaction_at_8deg")})


if __name__ == "__main__":
    main()
