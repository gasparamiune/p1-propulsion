"""FD-07 coil RE-ROUTE for the retained-vapour fix (CAD v3.4.1 feed, v1, 2026-10-13, Mechanical).

Lead decision 2026-10-13 (on Mechanical's relay-3 answer): re-route the coil as the baseline retained-vapour fix.  Targets:
fixed end at the wall-line start (z >= 71, airframe clamp or GM-09 standoff); bore-crown low point >= 75 mm; bay wall >= 3 mm at
the 8 deg stop; K_max <= 17.2 N m/rad; MBR per the hose maker.

Hose data (sourced 2026-10-13; the v3.4 model assumed a smooth-bore -6 hose with a 39 mm gate):
  * Parker 919B-6 smooth-bore PTFE/SS braid (ph.parker.com/us/en/919b-6): ID 8 mm, OD 11.6 max, 172 bar, MBR 102 mm, 0.15 kg/m
    -> a smooth-bore hose cannot be coiled at R 40-55 mm in the 140 mm bay: the coil needs a CONVOLUTED PTFE hose.
  * Convoluted PTFE 3/8 in, 1 SS braid: Flowfit tech data sheet 1962 (flowfitonline.com MFH2.pdf): ID 10.2, OD 15.9, 97 bar,
    bend radius static 30 / DYNAMIC 100 mm; Indunorm TEF3W10-H: OD 15.9, 103 bar (burst 414, 4:1), MBR 20 mm, -60..+260 C;
    DICSA anti-static convoluted PTFE 1 braid M293009 (2024-03-16): ID 10-11, OD 14.7-16.2, 120 bar, burst 480, MBR 30 mm.
  Model values (v3.4.1): ID 10.5 (mid of 10-11, convolution volume above the root TO-VERIFY), OD 16.2 (max, for clearance), static
  MBR gate 30 mm, dynamic MBR 100 mm reported (Flowfit; the coil flexes +/-8 deg about a static R ~40-55 bend: duty acceptance by the
  maker or a B-FD-1 flex-life test), working pressure >= SEG-P 9.975 MPa required (97 bar Flowfit FAILS, 103 / 120 bar pass),
  crimp ferrule OD 20 x 25 mm ESTIMATE (maker drawing TO-VERIFY), mass 0.21 kg/m (Indunorm '0,21 kg', TO-VERIFY per metre).

Method: the CAD route function parts_feed.route (plan curve + monotonic quintic z from the TEE side port z 72 to the fixed end
z_end, fixed 3/8 line with a horizontal and a vertical R24 bend into the wall line at az 219.5) is evaluated on a grid of fixed-end
height, azimuth, radius, plan limits and engine-end ferrule; per candidate:
  * saddle = lowest bore crown on the series path TEE side port -> FD-07A -> hose -> FD-07B -> FD-08 (crown = centre elevation +
    a sqrt(1 - (t.u)^2)), at the nominal drogue attitude (u = +Z) and tilted 10 / 20 deg in 8 directions (proxy: the full trap
    analysis is segment_traps on the chosen CAD);
  * posed clearances at the 8 deg stop (36 directions; linear frame shape + exact rigid end): bay wall (r 70), engine case
    (r 31.75 about the posed axis), TEE / riser (posed cylinders; first 25 mm of hose excluded: attachment);
  * bend radius at the stop (installed + |change|), K matrix (hose_frame, pivot origin) at EI 0.05 / 0.25 / 0.5 ASSUMED,
    EI break-even for K_max = 17.17 N m/rad (ENG-07 at 7.4 V, actuator_slew_v2), ENG-07 vector rates for the selected candidates.
Output: calcs/coil_reroute_v341_v1.json.  DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data sourced as listed).
"""
from __future__ import annotations
import itertools, json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import tvc_kinematics as tk
import parts_feed as pf
import hose_frame as hf
import coil_route_trade_v34 as ct

OUT = HERE / "coil_reroute_v341_v1.json"
STOP, CLR, R_WALL, R_CASE = 8.0, 3.0, 70.0, 31.75
K_BREAK = 17.17                     # N m/rad, ENG-07 hose break-even at 7.4 V (actuator_slew_v2 / coil_o3b_v34)
MBR_STATIC, MBR_DYN = 30.0, 100.0
HOSE_NEW = {"id": 10.5, "od": 16.2, "mass_kg_m": 0.21}
FERRULE_NEW = {"od": 20.0}
TB_R = 7.747 / 2                    # 3/8 x 0.035 tube bore radius


def crowns(P, a, u):
    """Bore-crown elevation along a centreline polyline P (mm) of bore radius a, up vector u."""
    P = np.asarray(P, float)
    t = np.gradient(P, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    return P @ u + a * np.sqrt(np.clip(1.0 - (t @ u) ** 2, 0.0, 1.0))


def series_path(f):
    t = pf.FEED["tee"]
    Pe, d = f["Pe"], f["d"]
    side = np.array([Pe - (t["side_socket_depth"] + 3.0) * d + k * d for k in np.linspace(0.0, t["side_socket_depth"] + 3.0, 12)] +
                    [Pe + k * (f["Q"] - Pe) for k in np.linspace(0.0, 1.0, 12)])
    fixed = np.array([f["Fq"] + k * (f["Fe"] - f["Fq"]) for k in np.linspace(0.0, 1.0, 12)])
    return [("TEE side passage + FD-07A", side, TB_R), ("FD-07 hose", f["hose"], pf.FEED["hose"]["id"] / 2),
            ("FD-07B", fixed, TB_R), ("FD-08 wall line", f["wall"], TB_R)]


def saddle(f, u):
    best = (1e9, "")
    for name, P, a in series_path(f):
        c = crowns(P, a, u)
        i = int(np.argmin(c))
        if c[i] < best[0]:
            best = (float(c[i]), name, [round(float(x), 1) for x in P[i]])
    return best


def tilt_u(deg, az):
    th, ph = math.radians(deg), math.radians(az)
    return np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])


def seg_dist(X, p0, p1):
    v = p1 - p0
    s = np.clip(((X - p0) @ v) / (v @ v), 0.0, 1.0)
    return np.linalg.norm(X - (p0 + np.outer(s, v)), axis=1)


def evaluate(params, eng07=False):
    save = ct._set(params)
    pf._HOSE_U.clear()
    rec = {"params": params}
    try:
        S = {}
        try:
            f = pf.route(S)
        except RuntimeError as ex:
            rec.update(feasible=False, why=str(ex))
            return rec
        hose = f["hose"]
        if not np.isfinite(f["hose_len_mm"]) or f["hose_len_mm"] > 450.0:
            rec.update(feasible=False, why=f"plan curve diverged ({f['hose_len_mm']:.0f} mm)")
            return rec
        od = pf.FEED["hose"]["od"]
        rr = np.hypot(hose[:, 0], hose[:, 1])
        dz = np.diff(hose[:, 2])
        rec.update(feasible=True, plan_opt_ok=bool(f["plan_opt_ok"]), length_mm=round(f["hose_len_mm"], 1), sweep_deg=round(f["coil_sweep_deg"], 1),
                   r_range_mm=[round(float(rr.min()), 1), round(float(rr.max()), 1)], z_range_mm=[round(float(hose[:, 2].min()), 1), round(float(hose[:, 2].max()), 1)],
                   hose_monotonic_rise=bool((dz >= -1e-6).all()), Rmin_installed_mm=round(f["hose_Rmin_mm"], 1),
                   Fq_mm=[round(float(x), 1) for x in f["Fq"]], Fe_mm=[round(float(x), 1) for x in f["Fe"]],
                   wall_vertical_from_z_mm=round(float(f["V0"][2]), 1), wall_len_mm=round(f["wall_len_mm"], 1), wall_alpha_deg=round(f["wall_alpha_deg"], 2))
        t_end = hose[-1] - hose[-2]
        rec["plan_end_err_mm"] = round(float(np.linalg.norm(hose[-1] - f["Fq"])), 3)          # v1.1: hose end to the fixed ferrule (after closure)
        rec["plan_end_heading_err_deg"] = round(math.degrees(math.acos(float(np.clip((t_end / np.linalg.norm(t_end)) @ f["cdir"], -1.0, 1.0)))), 2)
        if "plan_end_err_mm" in f:                                                            # parts_feed v3.4.1 closes the SLSQP residuals
            rec["plan_residual_before_closure"] = {"mm": round(f["plan_end_err_mm"], 3), "deg": round(f["plan_end_heading_err_deg"], 2)}
        s0 = saddle(f, np.array([0.0, 0.0, 1.0]))
        rec["saddle_nominal"] = {"z_mm": round(s0[0], 2), "at": s0[1], "xyz": s0[2]}
        tl = {}
        for deg in (10.0, 20.0):
            rows = []
            for az in range(0, 360, 45):
                s_ = saddle(f, tilt_u(deg, az))
                rows.append((round(s_[0], 2), az, s_[1]))
            rows.sort()
            tl[f"{deg:.0f}"] = {"min_crown_elev_mm": rows[0][0], "toward_az": rows[0][1], "at": rows[0][2],
                                "all": [r[0] for r in sorted(rows, key=lambda r: r[1])]}
        rec["saddle_tilt"] = tl
        # posed clearances at the stop
        t = pf.FEED["tee"]
        wall_min, case_min, tee_min, worst = 1e9, 1e9, 1e9, {}
        s_arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(hose, axis=0), axis=1))])
        for ph in np.arange(0.0, 360.0, 10.0):
            a, b = tk.cone_to_ab(STOP, ph)
            X = pf.hose_centreline_at(S, a, b)
            sX = np.interp(np.linspace(0, 1, len(X)), np.linspace(0, 1, len(s_arc)), s_arc)
            R = tk.R_pose(a, b)
            r = np.hypot(X[:, 0], X[:, 1])
            cw = R_WALL - (r + od / 2)
            if cw.min() < wall_min:
                wall_min, worst["wall"] = float(cw.min()), (float(ph), [round(float(v), 1) for v in X[int(np.argmin(cw))]])
            ez = R @ np.array([0.0, 0.0, 1.0])
            ax_ = X @ ez
            rad = np.linalg.norm(X - np.outer(ax_, ez), axis=1)
            cc = rad - R_CASE - od / 2
            if cc.min() < case_min:
                case_min, worst["case"] = float(cc.min()), (float(ph), [round(float(v), 1) for v in X[int(np.argmin(cc))]])
            m = sX > 25.0
            tee0, tee1 = R @ np.array([t["axis_xy"][0], t["axis_xy"][1], t["z_bot"]]), R @ np.array([t["axis_xy"][0], t["axis_xy"][1], t["z_top"]])
            ris1 = R @ np.array([t["axis_xy"][0], t["axis_xy"][1], 156.0])
            dt = np.minimum(seg_dist(X[m], tee0, tee1) - t["od"] / 2, seg_dist(X[m], tee1, ris1) - 9.525 / 2) - od / 2
            if dt.min() < tee_min:
                tee_min, worst["tee"] = float(dt.min()), (float(ph), [round(float(v), 1) for v in X[m][int(np.argmin(dt))]])
        nodes = hose[::3] * 1e-3
        if not np.allclose(nodes[-1], hose[-1] * 1e-3):
            nodes = np.vstack([nodes, hose[-1] * 1e-3])
        k0 = hf.curvature_installed(nodes)
        rmin = 1e9
        for ph in np.arange(0.0, 360.0, 10.0):
            axv = (math.cos(math.radians(ph)), math.sin(math.radians(ph)), 0.0)
            _, _, bend, _ = hf.solve(nodes, 0.25, axis=axv, theta=1e-3)
            kk = np.maximum(k0[:-1], k0[1:]) + bend / 0.25 * (math.radians(STOP) / 1e-3)
            rmin = min(rmin, 1e3 / kk.max())
        K1 = ct.k_matrix(nodes, 1.0)
        Kmax1 = float(np.linalg.svd(K1, compute_uv=False)[0])
        rec.update(wall_clr_stop_mm=round(wall_min, 2), case_clr_stop_mm=round(case_min, 2), tee_riser_clr_stop_mm=round(tee_min, 2), worst=worst,
                   Rmin_stop_mm=round(rmin, 1), K_per_EI_Nm_rad=[[round(float(x), 3) for x in row] for row in K1],
                   K_max_per_EI=round(Kmax1, 3), EI_breakeven_Nm2=round(K_BREAK / Kmax1, 3),
                   K_max_at_EI={str(e): round(Kmax1 * e, 2) for e in (0.05, 0.25, 0.5)})
        rec["gates"] = {"saddle_75": bool(s0[0] >= 75.0), "wall_3": bool(wall_min >= CLR), "case_3": bool(case_min >= CLR),
                        "tee_3": bool(tee_min >= CLR), "MBR_static_30": bool(rmin >= MBR_STATIC), "MBR_dynamic_100": bool(rmin >= MBR_DYN),
                        "K_EI0.25": bool(Kmax1 * 0.25 <= K_BREAK), "plan_ok": bool(f["plan_opt_ok"]), "monotonic": rec["hose_monotonic_rise"]}
        rec["pass_all_but_dynamic"] = all(v for k, v in rec["gates"].items() if k not in ("MBR_dynamic_100", "plan_ok"))
        if eng07:
            for EI in (0.05, 0.25, 0.5):
                K = K1 * EI
                rec[f"ENG07_EI{EI}"] = {V: ct.worst_rate(K, V, vector=True) for V in ("7.4", "6.6")}
        return rec
    finally:
        for sec, dd in save.items():
            pf.FEED[sec].clear()
            pf.FEED[sec].update(dd)
        pf._HOSE_U.clear()


def main():
    t0 = time.time()
    pf.FEED["hose"].update(HOSE_NEW)
    pf.FEED["ferrule"].update(FERRULE_NEW)
    rows = []
    grid = itertools.product((74.0, 78.0), (300.0, 295.0, 305.0), (55.0, 57.5),
                             ((41.5, 58.0, 54.5), (41.5, 56.0, 52.0), (44.0, 56.0, 52.0), (41.5, 54.0, 50.0)),
                             (25.0, 20.0, 15.0), (-10.0, -14.0, -18.0))
    for z_end, fq_az, fq_r, (rmp, rmax, rpref), flen, aim in grid:
        p = {"z_end": z_end, "fq_az": fq_az, "fq_r": fq_r, "R_min_plan": rmp, "r_max": rmax, "r_pref": rpref,
             "ferrule.len": flen, "tee.side_aim": aim}
        rec = evaluate(p)
        rows.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("params", "feasible", "why", "length_mm", "sweep_deg", "saddle_nominal", "wall_clr_stop_mm",
                                                  "case_clr_stop_mm", "tee_riser_clr_stop_mm", "Rmin_stop_mm", "EI_breakeven_Nm2", "pass_all_but_dynamic")}),
              flush=True)
    ok = [r for r in rows if r.get("feasible") and r.get("pass_all_but_dynamic")]
    ok.sort(key=lambda r: (r["K_max_per_EI"], -r["saddle_tilt"]["10"]["min_crown_elev_mm"]))
    for rec in ok[:5]:
        full = evaluate(rec["params"], eng07=True)
        rec.update(full)
        print("ENG07", json.dumps(rec["params"]), {k: rec[k] for k in rec if k.startswith("ENG07")}, flush=True)
    out = {"id": "coil_reroute_v341", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/coil_reroute_v341.py",
           "method": __doc__.split("\n\n")[1] + "\n\n" + __doc__.split("\n\n")[2] + "\n\n" + __doc__.split("\n\n")[3],
           "hose_model": {**HOSE_NEW, "ferrule": FERRULE_NEW, "MBR_static_gate_mm": MBR_STATIC, "MBR_dynamic_mm": MBR_DYN},
           "rows": rows, "n_pass_all_but_dynamic": len(ok),
           "tag": "DERIVED (linear frame on CAD route candidates; EI ASSUMED; hose data sourced, see method)", "t_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("done", out["t_s"], "pass", len(ok))


if __name__ == "__main__":
    main()
