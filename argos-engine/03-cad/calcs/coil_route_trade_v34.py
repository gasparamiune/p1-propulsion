"""FD-07 coil route trade on CAD v3.4 (v1, 03-cad/src/calcs, 2026-10-13, Mechanical).

Why: coil_o3b_v34 v1 found that the routed v3.4 coil (fixed end az 300, sweep 193 deg, 185.9 mm) misses three gates at the 8 deg stop:
bay-wall clearance 0.23 mm (rule 3), bend radius 34.2 mm (G4 gate 39) and, with the v2 scalar method at EI 0.5 ASSUMED, ENG-07
89.7 deg/s at 7.4 V.  This trade varies the fixed-end azimuth and the plan radius limits of parts_feed.route (the CAD route function)
and evaluates every candidate with the same models:
  * hinge stiffness matrix K (hose_frame.solve, pivot = origin), bend radius at the stop (installed + |change|, 36 directions),
    clearances at the stop to the bay wall (r 70) and the GM-09 ring top (z 32, r >= 52) from the posed centreline (linear field +
    exact rigid end, parts_feed.hose_centreline_at);
  * ENG-07 at 7 deg, 7.4 V and 6.6 V, two load treatments:
      scalar (actuator_slew_v2): other v2 terms 2.731 N m + K_max x 7 deg, all opposing the motion (bound);
      vector: other v2 terms 2.731 N m opposing the motion + the hose spring moment -K (alpha, beta) at the pose (a linear spring
      opposes outward motion and aids inward motion; its direction follows K's principal axes) -- the consistent model for a spring;
  * installation moment if the hose is NOT pre-formed: a straight hose forced to the coil carries M = EI kappa; the engine-end couple
    EI kappa_end b_end (b = binormal) has X/Y (servo) components -> a static hinge moment.  Pre-formed (heat-set) assemblies remove it.
Hose EI 0.25 (nominal) / 0.5 N m2 (upper) ASSUMED; B-FD-1 measures.  Output: calcs/coil_route_trade_v34_v1.json.
"""
from __future__ import annotations
import copy, json, math, sys, time
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
from actuator_loads import SERVO, jac

OUT = HERE / "coil_route_trade_v34_v1.json"
STOP, RANGE = 8.0, 7.0
R_WALL, GM09_TOP, GM09_R_IN, CLR, MBR = 70.0, 32.0, 52.0, 3.0, 39.0
R_CASE = 31.75                     # mm, ENG-TC-01 case OD radius at z 60-150 (hose_routing_trade_v2 O3a table)
L_OTHER = sv.L_V2 - sv.TERMS_V2["hose_radial_L0.40_upper"]
_G = {}


def geom():
    if "g" not in _G:
        P, _ = config.build()
        _G["g"] = tk.geometry(P)
    return _G["g"]


def rates_vec(g, theta, phi, chis, Ts, wnl, L_other, Kmat):
    a, b = tk.cone_to_ab(theta, phi)
    J = jac(g, a, b)
    e, A, ex, ey2 = sv.frame(a, b)
    ph, th = math.radians(phi), math.radians(theta)
    h_ = np.array([math.cos(ph), math.sin(ph), 0.0])
    e_t = -math.sin(th) * np.array([0, 0, 1.0]) + math.cos(th) * h_
    e_p = np.array([-math.sin(ph), math.cos(ph), 0.0])
    Apinv = np.linalg.pinv(A)
    Ms = np.zeros(3)
    Ms[:2] = -Kmat @ np.array([math.radians(a), math.radians(b)])
    out = []
    for chi in chis:
        c = math.radians(chi)
        ed = math.cos(c) * e_t + math.sin(c) * e_p
        qd = Apinv @ ed
        psid = J @ qd
        M = -L_other * np.cross(e, ed) + Ms
        Q = np.array([M @ ex, M @ ey2])
        tau = np.linalg.solve(J.T, -Q)
        lim = []
        for i in range(2):
            if abs(psid[i]) < 1e-12:
                lim.append(float("inf"))
                continue
            drive = tau[i] * math.copysign(1.0, psid[i])
            w = wnl * (1.0 - max(drive, 0.0) / Ts)
            lim.append(w / abs(psid[i]))
        out.append(min(lim))
    return np.array(out)


def worst_rate(Kmat, V, vector=True, L_other=L_OTHER, step=5.0):
    g = geom()
    Ts, wnl = SERVO[V]
    Kmax = float(np.linalg.svd(Kmat, compute_uv=False)[0])
    f = (lambda ph, cc: rates_vec(g, RANGE, ph, cc, Ts, wnl, L_other, Kmat)) if vector else \
        (lambda ph, cc: sv.rates_at_pose(g, RANGE, ph, cc, Ts, wnl, L_other + Kmax * math.radians(RANGE))[0])
    best = (1e9, 0.0, 0.0)
    chis = np.arange(0.0, 360.0, step)
    for ph in np.arange(0.0, 360.0, step):
        w = f(ph, chis)
        k = int(np.argmin(w))
        if w[k] < best[0]:
            best = (float(w[k]), float(ph), float(chis[k]))
    for ph in np.arange(best[1] - step, best[1] + step + 1e-9, 0.5):
        cc = np.arange(best[2] - step, best[2] + step + 1e-9, 0.5) % 360.0
        w = f(ph % 360.0, cc)
        k = int(np.argmin(w))
        if w[k] < best[0]:
            best = (float(w[k]), float(ph % 360.0), float(cc[k]))
    return {"dps": round(best[0], 2), "pose_phi_deg": best[1], "motion_chi_deg": best[2]}


def k_matrix(nodes, EI, th=1e-3):
    _, (_, _, Mpx), _, _ = hf.solve(nodes, EI, axis=(1, 0, 0), theta=th)
    _, (_, _, Mpy), _, _ = hf.solve(nodes, EI, axis=(0, 1, 0), theta=th)
    return np.array([[Mpx[0], Mpy[0]], [Mpx[1], Mpy[1]]]) / th


def _set(params):
    """params: {'fq_az': v} (coil section) or {'tee.side_aim': v, 'ferrule.len': v, ...}; returns the saved sections."""
    secs = {("coil" if "." not in k else k.split(".")[0]) for k in params}
    save = {sec: copy.deepcopy(pf.FEED[sec]) for sec in secs}
    for k, v in params.items():
        sec, key = ("coil", k) if "." not in k else k.split(".", 1)
        pf.FEED[sec][key] = v
    return save


def evaluate(params, eng07=True):
    save = _set(params)
    pf._HOSE_U.clear()
    rec = {"params": params}
    try:
        S = {}
        try:
            f = pf.route(S)
        except RuntimeError as ex:
            rec["feasible"] = False
            rec["why"] = str(ex)
            return rec
        hose = f["hose"]
        if not np.isfinite(f["hose_len_mm"]) or f["hose_len_mm"] > 450.0:
            rec.update(feasible=False, why=f"plan curve diverged (length {f['hose_len_mm']:.0f} mm)")
            return rec
        nodes = hose[::3] * 1e-3
        if not np.allclose(nodes[-1], hose[-1] * 1e-3):
            nodes = np.vstack([nodes, hose[-1] * 1e-3])
        k0 = hf.curvature_installed(nodes)
        od = pf.FEED["hose"]["od"]
        rr = np.hypot(hose[:, 0], hose[:, 1])
        rec.update(feasible=True, plan_opt_ok=bool(f["plan_opt_ok"]), length_mm=round(f["hose_len_mm"], 1), sweep_deg=round(f["coil_sweep_deg"], 1),
                   r_range_mm=[round(float(rr.min()), 1), round(float(rr.max()), 1)], Rmin_installed_mm=round(f["hose_Rmin_mm"], 1),
                   wall_alpha_deg=round(f["wall_alpha_deg"], 2), wall_L2_mm=round(f["wall_L2_mm"], 1), wall_len_mm=round(f["wall_len_mm"], 1))
        dirs = np.arange(0.0, 360.0, 10.0)
        wall_min, ring_min, ww = 1e9, 1e9, None
        for ph in dirs:
            a, b = tk.cone_to_ab(STOP, ph)
            X = pf.hose_centreline_at(S, a, b)
            r = np.hypot(X[:, 0], X[:, 1])
            cw = R_WALL - (r + od / 2)
            i = int(np.argmin(cw))
            if cw[i] < wall_min:
                wall_min, ww = float(cw[i]), (float(ph), [round(float(x), 1) for x in X[i]], round(i / (len(X) - 1), 3))
            m = r + od / 2 > GM09_R_IN
            if m.any():
                ring_min = min(ring_min, float((X[m, 2] - od / 2 - GM09_TOP).min()))
        rmin = 1e9
        for ph in dirs:
            ax = (math.cos(math.radians(ph)), math.sin(math.radians(ph)), 0.0)
            _, _, bend, _ = hf.solve(nodes, 0.25, axis=ax, theta=1e-3)
            kk = np.maximum(k0[:-1], k0[1:]) + bend / 0.25 * (math.radians(STOP) / 1e-3)
            rmin = min(rmin, 1e3 / kk.max())
        rec.update(wall_clr_stop_mm=round(wall_min, 2), wall_worst=ww, ring_clr_stop_mm=round(ring_min, 2), Rmin_stop_mm=round(rmin, 1))
        fe = pf.FEED["ferrule"]
        ts = np.linspace(fe["stub"], fe["stub"] + fe["len"], 60)
        fr = np.hypot(*(f["Pe"][:2, None] + np.outer(f["d"][:2], ts)))
        rec["ferrule_A_to_case_static_mm"] = round(float(fr.min() - fe["od"] / 2 - R_CASE), 2)
        rec["hose_to_case_static_mm"] = round(float(rr.min() - od / 2 - R_CASE), 2)
        rec["Q_r_az_mm_deg"] = [round(float(np.hypot(*f["Q"][:2])), 1), round(math.degrees(math.atan2(f["Q"][1], f["Q"][0])) % 360, 1)]
        # installation moment if not pre-formed (engine-end couple EI kappa b at the first nodes)
        p0, p1, p2 = nodes[0], nodes[2], nodes[4]
        t1, t2 = (p1 - p0) / np.linalg.norm(p1 - p0), (p2 - p1) / np.linalg.norm(p2 - p1)
        bvec = np.cross(t1, t2)
        kap = np.linalg.norm(bvec) / (0.5 * (np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1)))
        bn = bvec / np.linalg.norm(bvec) if np.linalg.norm(bvec) > 1e-12 else np.zeros(3)
        for EI in (0.25, 0.5):
            K = k_matrix(nodes, EI)
            ev = np.linalg.eigvalsh(0.5 * (K + K.T))
            r_ = {"K": [[round(float(x), 3) for x in row] for row in K], "K_eig": [round(float(x), 3) for x in ev],
                  "K_max": round(float(np.linalg.svd(K, compute_uv=False)[0]), 3),
                  "install_moment_if_not_preformed_XY_Nm": round(float(EI * kap * math.hypot(bn[0], bn[1])), 3),
                  "install_moment_total_Nm": round(float(EI * kap), 3)}
            if eng07:
                for V in ("7.4", "6.6"):
                    r_[f"ENG07_vector_{V}V"] = worst_rate(K, V, vector=True)
                    r_[f"ENG07_scalar_{V}V"] = worst_rate(K, V, vector=False)
            rec[f"EI={EI}"] = r_
        rec["gates"] = {"wall_3mm": bool(wall_min >= CLR), "ring_3mm": bool(ring_min >= CLR), "MBR_39": bool(rmin >= MBR),
                        "ENG07_vector_EI0.5_7V4": bool(eng07 and rec["EI=0.5"]["ENG07_vector_7.4V"]["dps"] >= 100.0),
                        "ENG07_scalar_EI0.5_7V4": bool(eng07 and rec["EI=0.5"]["ENG07_scalar_7.4V"]["dps"] >= 100.0)}
        return rec
    finally:
        for sec, d in save.items():
            pf.FEED[sec].clear()
            pf.FEED[sec].update(d)
        pf._HOSE_U.clear()


def main():
    t0 = time.time()
    base = {k: pf.FEED["coil"][k] for k in ("fq_az", "r_max", "r_pref", "R_min_plan", "fq_r")}
    rows = []
    for fq_az in (300.0, 285.0, 270.0, 255.0, 240.0):
        for r_max, r_pref in ((58.0, 54.5), (54.0, 50.5), (52.0, 48.5), (50.0, 46.5)):
            for fq_r in sorted({min(55.0, r_max - 2.0), min(52.0, r_max - 2.0)}, reverse=True):
                p = {"fq_az": fq_az, "r_max": r_max, "r_pref": r_pref, "fq_r": fq_r}
                rec = evaluate(p, eng07=False)
                rows.append(rec)
                print(json.dumps({k: rec.get(k) for k in ("params", "feasible", "plan_opt_ok", "length_mm", "sweep_deg", "r_range_mm", "Rmin_installed_mm",
                                                          "wall_clr_stop_mm", "ring_clr_stop_mm", "Rmin_stop_mm")}), flush=True)
    # ENG-07 for the baseline and every candidate that meets the geometric gates
    for rec in rows:
        if not rec.get("feasible"):
            continue
        geo_ok = rec["wall_clr_stop_mm"] >= CLR and rec["ring_clr_stop_mm"] >= CLR and rec["Rmin_stop_mm"] >= MBR and rec["plan_opt_ok"]
        isbase = rec["params"]["fq_az"] == base["fq_az"] and rec["params"]["r_max"] == base["r_max"] and rec["params"]["fq_r"] == base["fq_r"]
        if geo_ok or isbase:
            full = evaluate(rec["params"], eng07=True)
            rec.update(full)
            print("ENG07", json.dumps({k: rec.get(k) for k in ("params", "length_mm", "sweep_deg", "wall_clr_stop_mm", "Rmin_stop_mm")}),
                  {e: {kk: rec[e][kk] for kk in rec[e] if kk.startswith(("K_max", "K_eig", "ENG07", "install"))} for e in ("EI=0.25", "EI=0.5")}, flush=True)
    out = {"id": "coil_route_trade_v34", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/coil_route_trade_v34.py",
           "method": __doc__.split("\n\n")[1], "baseline_params": base, "L_other_Nm": round(L_OTHER, 4), "rows": rows,
           "tag": "DERIVED (linear frame on CAD route candidates; EI ASSUMED; servo line ASSUMED linear)", "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"])


def main_v2():
    """v2 trade: the engine-end geometry (FD-07A ferrule length, TEE side-port aim) and the plan limits, fixed end at az 300."""
    t0 = time.time()
    out_path = HERE / "coil_route_trade_v34_v2.json"
    rows = []
    for flen in (25.0, 20.0, 15.0):
        for aim in (-14.0, -18.0, -10.0):
            for rmin_plan, r_max, r_pref in ((41.5, 58.0, 54.5), (44.0, 58.0, 54.5), (41.5, 56.0, 52.0)):
                p = {"ferrule.len": flen, "tee.side_aim": aim, "R_min_plan": rmin_plan, "r_max": r_max, "r_pref": r_pref}
                rec = evaluate(p, eng07=False)
                rows.append(rec)
                print(json.dumps({k: rec.get(k) for k in ("params", "feasible", "plan_opt_ok", "length_mm", "sweep_deg", "r_range_mm", "Rmin_installed_mm",
                                                          "wall_clr_stop_mm", "ring_clr_stop_mm", "Rmin_stop_mm", "ferrule_A_to_case_static_mm",
                                                          "hose_to_case_static_mm", "Q_r_az_mm_deg", "why")}), flush=True)
    ok = [r for r in rows if r.get("feasible") and r["wall_clr_stop_mm"] >= CLR and r["Rmin_stop_mm"] >= MBR - 5.0]
    ok.sort(key=lambda r: -r["wall_clr_stop_mm"])
    for rec in ok[:6]:
        full = evaluate(rec["params"], eng07=True)
        rec.update(full)
        print("ENG07", json.dumps(rec["params"]), {e: {kk: rec[e][kk] for kk in rec[e] if kk.startswith(("K_max", "ENG07"))} for e in ("EI=0.25", "EI=0.5")}, flush=True)
    out = {"id": "coil_route_trade_v34", "version": "v2", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/coil_route_trade_v34.py (main_v2)",
           "why": "v1 (fixed-end azimuth and plan radius) could not clear the bay wall at the 8 deg stop: every fixed end other than az 300 has no "
                  "two-bend wall-line solution and the bulge comes from the 28 mm straight engine-end ferrule leaving the TEE 18 deg outward of the "
                  "coil tangent; v2 varies that end (ferrule length, side-port aim) and the plan limits",
           "method": __doc__.split("\n\n")[1], "rows": rows, "case_r_mm": R_CASE,
           "tag": "DERIVED (linear frame on CAD route candidates; EI ASSUMED; ferrule lengths are candidate COTS values TO-VERIFY)", "t_s": round(time.time() - t0, 1)}
    out_path.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "v2":
        main_v2()
    else:
        main()
