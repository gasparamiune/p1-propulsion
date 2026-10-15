"""Gimbal pivot-location trade (forward / CG / aft) with the engine CAD mass properties.  v1 2026-10-12.

Inputs: engine parts built from the interface-driven parameters (parts_engine), gnc.json v1 (vehicle CG,
limit loads, tail-wags-dog requirement, thrust floor), electronics.json v1 (servo), ASSUMED hose EI range.
All candidates use the SAME gimballed engine; only the pivot station changes.  Metrics:
  * tail-wags-dog zero  w_twd = sqrt(T l_p / J_twd), J_twd = I_e + m_e l_e (l_e + l_p)   (gnc.json v1 note)
  * hinge-moment terms (inertia, axial and lateral acceleration, hose, misalignment, nozzle side load)
  * sweep radius of every engine vertex at the conical stop -> required airframe ID (enclosed to the
    RV-1 base plane) and the protrusion length needed to live with a 120 mm ID
  * GNC range requirement interpolated between the two gnc.json v1 points (mid 7 deg, forward 10 deg)
Engine frame here = the CAD build frame (z = 0 at the head mid-plane, +z forward, mm).
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC)); sys.path.insert(0, str(SRC.parents[1] / "04-fea" / "src"))
import config, layout, engmat
from partlib import Registry
from geom import mass_props, apply, bbox, parallel_axis

G0 = 9.80665


def engine_props(reg, groups=("engine",)):
    """Mass, CG (mm), inertia about CG (kg m2), vertex cloud (mm) of the parts in `groups`."""
    m_t, mom, items, pts = 0.0, np.zeros(3), [], []
    for p in reg:
        for T, g in p.placements:
            if g not in groups:
                continue
            sh = apply(p.shape, T)
            if p.mass_each_kg is not None:
                bb = bbox(sh); m = p.mass_each_kg
                cg = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2]) * 1e-3
                d = np.array([bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]) * 1e-3
                Icg = m / 12 * np.diag([d[1]**2 + d[2]**2, d[0]**2 + d[2]**2, d[0]**2 + d[1]**2])   # solid box
            else:
                mp = mass_props(sh, engmat.rho(p.material)); m = mp["m"]; cg = np.array(mp["cg"]); Icg = np.array(mp["I_cg"])
            items.append((p.pn, m, cg, Icg))
            m_t += m; mom += m * cg
            vs, tris = sh.tessellate(0.5, 0.5)
            V = np.array([(v.x, v.y, v.z) for v in vs])
            pts.append(V)
            # densify long triangle edges (straight cylinders tessellate with end vertices only)
            for t in tris:
                for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    L = np.linalg.norm(V[a] - V[b])
                    if L > 4.0:
                        n = int(L // 3.0)
                        f = np.linspace(0, 1, n + 2)[1:-1, None]
                        pts.append(V[a] + f * (V[b] - V[a]))
    cg = mom / m_t
    I = np.zeros((3, 3))
    for _, m, c, Icg in items:
        I += parallel_axis(Icg, m, c - cg)
    return dict(m=m_t, cg_mm=cg * 1e3, I_cg=I, items=items, pts=np.vstack(pts))


def sweep_radius(pts, z_p, theta_deg):
    """Max distance from the vehicle axis of every vertex when the engine tilts theta about a pivot at z_p
    (any azimuth; conical stop).  Returns per-vertex sweep radius (mm)."""
    th = math.radians(theta_deg)
    r = np.hypot(pts[:, 0], pts[:, 1]); d = pts[:, 2] - z_p
    return r * math.cos(th) + np.abs(d) * math.sin(th)


def hose_K(EI, L, h):
    """Hinge stiffness (N m/rad) of a straight hose, clamped at a fixed fitting a distance L above the engine-side
    fitting, which sits h above the pivot on the axis.  Clamped-clamped beam with end translation h*theta and
    rotation theta:  K = (4 EI / L) (3 x^2 - 3 x + 1), x = h / L."""
    x = h / L
    return 4 * EI / L * (3 * x * x - 3 * x + 1)


def main(out_dir=None):
    P, _ = config.build()
    S = layout.stations(P)
    reg = Registry()
    import parts_engine
    parts_engine.build_engine_parts(P, S, reg, engmat)
    E = engine_props(reg)
    grain = [it for it in E["items"] if it[0].startswith("ENG-GR")]
    m_gr = sum(it[1] for it in grain); cg_gr = sum(it[1] * it[2] for it in grain) / m_gr
    dry_m = E["m"] - m_gr; dry_cg = (E["m"] * E["cg_mm"] / 1e3 - m_gr * cg_gr) / dry_m * 1e3

    gnc = config._load("gnc.json")
    ev = {e["event"]: e for e in gnc["reference_vehicle"]["mass_properties_vs_time"]["events"]}
    z_exit_station = -0.03                                   # gnc.json v1 conventions.stations
    T_max = 500.0
    floors = {"12.5 %": 0.125 * T_max, "20 %": 0.20 * T_max, "100 %": T_max}
    twd_min = gnc["requirements"]["structure"]["tail_wags_dog_zero_min_rad_s"]["v"]
    theta_dd = gnc["requirements"]["gimbal"]["angular_accel_min_rad_s2"]["v"]
    a_ax = gnc["design_limit_loads"]["axial_accel_flight_g"]["v"] * G0
    a_lat = gnc["design_limit_loads"]["lateral_accel_flight_g"]["v"] * G0
    pv = gnc["reference_vehicle"]["gimballed_subassembly"]["v"]["pivot_options"]
    lp_mid, lp_fwd = pv["mid"]["l_p"], pv["forward"]["l_p"]
    theta_stop = P["gimbal_stop_deg"]["v"]
    EI_rng = P["hose_EI"]["v"]
    ID = P["airframe_ID"]["v"] * 1e3; clear = P["airframe_clear"]["v"] * 1e3
    z_exit = S["exit"]

    I_e = E["I_cg"][0, 0]                                    # transverse about CG (x); y similar
    I_e_y = E["I_cg"][1, 1]
    cands = {
        "forward (head mid-plane, CAD v2 build)": 0.0,
        "forward+90 mm (TWD-limit search)": -90.0,
        "CG (wet, full grain)": float(E["cg_mm"][2]),
        "aft (post-chamber)": -300.0,
    }
    rows = []
    for name, z_p in cands.items():
        l_e = (z_p - E["cg_mm"][2]) / 1e3                   # CG distance AFT of the pivot (m), >0 = CG below pivot
        z_piv_station = z_exit_station + (z_p - z_exit) / 1e3
        res = {"candidate": name, "z_pivot_engine_mm": round(z_p, 1), "z_pivot_RV1_station_m": round(z_piv_station, 4), "l_e_m": round(l_e, 4)}
        I_piv = max(I_e, I_e_y) + E["m"] * l_e ** 2
        res["I_pivot_kgm2"] = round(I_piv, 5)
        for evn in ("liftoff", "touchdown"):
            l_p = ev[evn]["z_cg_m"] - z_piv_station
            J = max(I_e, I_e_y) + E["m"] * l_e * (l_e + l_p)
            res[f"l_p_{evn}_m"] = round(l_p, 4)
            res[f"J_twd_{evn}_kgm2"] = round(J, 5)
            for fl, T in floors.items():
                w = math.sqrt(T * l_p / J) if J > 0 else float("nan")
                res[f"w_twd_{evn}_{fl}_rad_s"] = round(w, 1)
        l_p = ev["touchdown"]["z_cg_m"] - z_piv_station
        res["GNC_range_req_deg_interp"] = round(7.0 + 3.0 * (lp_mid - l_p) / (lp_mid - lp_fwd), 2)
        # hinge-moment terms at 7 deg (linear sum, as gnc.json v1)
        d7 = math.radians(7.0)
        h_inlet = (S["bonnet_top"] - 12.0 - z_p) / 1e3             # side inlet ~12 mm below bonnet top
        L_hose = 0.20
        terms = {
            "inertia_Ipivot_x_thetadd": I_piv * theta_dd,
            "axial_accel_m_a_le_sin7": E["m"] * a_ax * abs(l_e) * math.sin(d7),
            "lateral_accel_m_alat_le": E["m"] * a_lat * abs(l_e),
            "hose_K_x_7deg_EI_lo": hose_K(EI_rng[0], L_hose, h_inlet) * d7,
            "hose_K_x_7deg_EI_hi": hose_K(EI_rng[1], L_hose, h_inlet) * d7,
            "misalignment_T_x_(0.5mm+0.25deg*arm)": T_max * (0.0005 + math.radians(0.25) * abs((z_exit - z_p) / 1e3)),
            "nozzle_side_load_floor_scaled_from_GNC": 1.3 * abs((z_exit - z_p) / 1e3) / 0.2346,
        }
        res["hose_inlet_height_m"] = round(h_inlet, 4)
        res["hinge_terms_Nm"] = {k: round(v, 3) for k, v in terms.items()}
        res["hinge_total_linear_sum_Nm_EI_hi"] = round(sum(v for k, v in terms.items() if k != "hose_K_x_7deg_EI_lo"), 3)
        # sweep
        rs = sweep_radius(E["pts"], z_p, theta_stop)
        z_base = z_exit + 30.0                                       # RV-1: exit 30 mm below the base plane
        inside = E["pts"][:, 2] >= z_base
        res["sweep_max_radius_enclosed_to_RV1_base_mm"] = round(float(rs[inside].max()), 1)
        res["required_ID_enclosed_mm"] = round(2 * (float(rs[inside].max()) + clear), 1)
        # highest base plane (lowest z) for which the 120 mm ID still clears everything above it
        ok_r = ID / 2 - clear
        bad = E["pts"][rs > ok_r]
        if len(bad):
            above = bad[bad[:, 2] > z_p]; below = bad[bad[:, 2] <= z_p]
            res["sweep_violations_above_pivot_count"] = int(len(above))
            res["max_sweep_above_pivot_mm"] = round(float(rs[E["pts"][:, 2] > z_p].max()), 1)
            if len(below):
                z_cut = float(below[:, 2].max())
                res["airframe_must_end_above_z_mm"] = round(z_cut, 1)
                res["protrusion_below_120ID_airframe_mm"] = round(z_cut - (S["aft_bottom"]), 1)
            if len(above):
                res["features_above_pivot_beyond_ID"] = sorted({tuple(np.round(v, 0)) for v in above[np.argsort(-rs[E['pts'][:, 2] > z_p][rs[E['pts'][:, 2] > z_p] > ok_r])][:5]})
        rows.append(res)

    out = {"id": "ENG-GIMBAL-TRADE", "version": "v1", "date": "2026-10-12", "owner": "mechanical",
           "inputs": {"engine_parts": "parts_engine v2 (CAD)", "gnc": f"gnc.json {gnc['version']}",
                      "theta_stop_deg": theta_stop, "airframe_ID_mm": ID, "hose_EI_Nm2": EI_rng, "hose_free_length_m": 0.20,
                      "twd_requirement_rad_s": twd_min, "theta_dd_rad_s2": theta_dd, "a_axial_mps2": a_ax, "a_lateral_mps2": a_lat},
           "engine_wet": {"m_kg": round(E["m"], 4), "cg_mm": np.round(E["cg_mm"], 2).tolist(), "I_cg_kgm2": np.round(E["I_cg"], 6).tolist()},
           "engine_dry_no_grain": {"m_kg": round(dry_m, 4), "cg_mm": np.round(dry_cg, 2).tolist()},
           "grain": {"m_kg": round(m_gr, 4), "cg_mm": np.round(cg_gr * 1e3, 2).tolist()},
           "candidates": rows}
    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        Path(out_dir, "gimbal_trade_v1.json").write_text(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    return out


if __name__ == "__main__":
    o = main(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({k: o[k] for k in ("engine_wet", "engine_dry_no_grain", "grain")}, indent=1))
    for r in o["candidates"]:
        print(json.dumps(r, default=str))
