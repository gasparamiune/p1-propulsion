"""Feed routing trade v2 (2026-10-12, Mechanical): the feasibility checks that v1 (hose_routing_trade.py) did not make.

v1 ranked the hose centrelines by hinge stiffness K, moment at 7 deg, bend radius and hose-to-wall / hose-to-engine clearance
(axisymmetric engine profile).  It did not check (a) the window of free length that a straight radial hose (O1) has between the
K rule and the bay wall, (b) how the engine-side end of a low coil (O3) reaches the injector inlet inside the swept envelope,
(c) where a fixed 3/8 in line can pass the swept head/bonnet/stack when it runs on the bay wall, (d) the coil's clearance to the
upper thrust ring GM-09 and (e) the temperature field the coil and the riser sit in.  This script makes those checks.

Inputs: CAD v3.3 engine group (build.build, pivot iterated) without the v3.3 pintle stack TC-11..17, which v3.4 replaces by the
in-line HV69 stack (ESTIMATE: cylinder r 26 mm over z 210.6..252, until CAD v3.4); hose_frame.solve / hose_routing_trade helpers
(linear frame, EI 0.05-0.5 N m2 ASSUMED); thermal FE v1.1 DC-B1 hi bound (runs/thermal/DC-B1_gncv2_hi_SS316L_L2.5_v11,
envelope_nodes.npz) for the case outer-surface peak temperature.  Rules: 3 mm to the 140 mm bay wall at the 8 deg conical stop
for moving parts (same rule as the engine sweep), 3 mm between moving and fixed parts, K <= 20 N m/rad per axis (lead 2026-10-12).
Engine frame, mm in the text and the JSON unless a key says m.  Output: calcs/hose_routing_trade_v2.json.
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "04-fea" / "src"))
import hose_frame as hf
import hose_routing_trade as hrt

OUT = HERE / "hose_routing_trade_v2.json"
THERMAL = Path("/home/claude/work/mechanical/runs/thermal/DC-B1_gncv2_hi_SS316L_L2.5_v11/envelope_nodes.npz")
R_WALL, CLR, STOP = 70.0, 3.0, 8.0                    # mm, mm, deg
OD_TUBE = 9.525                                       # 3/8 in tube (fixed line and riser)
OD_QTR = 6.35                                         # 1/4 in, information only (flow sizing is Combustion's)
CLIP_T = 1.0                                          # mm P-clip band between a wall-mounted line and the wall (ASSUMED)
HEX_JIC6 = 11.0                                       # mm half-size of a -6 JIC nut / tube-weld adapter (3/4 in hex ~ 19 AF, 22 AC) ASSUMED
PINTLE_STACK_V33 = ("ENG-TC-11", "ENG-TC-12", "ENG-TC-13", "ENG-TC-14", "ENG-TC-15", "ENG-TC-16", "ENG-TC-17")
STACK_V34 = {"r_mm": 26.0, "z_mm": (210.6, 252.0), "tag": "ESTIMATE until CAD v3.4 (HV69 in-line stack envelope)"}
GM09_TOP, GM09_R_IN = 32.0, 52.0                      # CAD v3.3 upper thrust ring top face z and inner radius (parts_gimbal)


def r_allowed(z_mm, half_width_mm):
    """Largest centre radius of an engine-mounted feature of radial half-width w at height z so that its 8 deg swept surface keeps
    CLR to the wall: r cos(stop) + |z| sin(stop) + w <= R_WALL - CLR."""
    c, s = math.cos(math.radians(STOP)), math.sin(math.radians(STOP))
    return (R_WALL - CLR - half_width_mm - abs(z_mm) * s) / c


def engine_points():
    import build, sweep
    t0 = time.time()
    P, S, reg, log = build.build(include=("engine", "gimbal"), iterate_cg=True)
    inst = build.posed_instances(reg, S, 0.0, 0.0, groups=("engine",))
    pts, tags = [], []
    for (pn, i, g, s, body) in inst:
        if pn in PINTLE_STACK_V33:
            continue
        Q = sweep._points(s)
        pts.append(Q)
        tags += [pn] * len(Q)
    zs = np.arange(STACK_V34["z_mm"][0], STACK_V34["z_mm"][1] + 0.1, 2.0)
    ph = np.radians(np.arange(0, 360, 3.0))
    cyl = np.array([[STACK_V34["r_mm"] * math.cos(a), STACK_V34["r_mm"] * math.sin(a), z] for z in zs for a in ph])
    pts.append(cyl)
    tags += ["STACK-v3.4-EST"] * len(cyl)
    st = {k: round(float(S[k]), 2) for k in ("head_top", "head_bot", "inj_face", "grain_top", "tube_fwd", "bonnet_top", "bolt_z_fwd")}
    st["fwd_glands"] = [round(float(x), 2) for x in S["fwd_glands"]]
    return np.vstack(pts), np.array(tags), st, round(time.time() - t0, 1)


def envelope(Q, tags, dz=5.0, dphi=2.0, swept=True):
    """Max-radius point per (z band, azimuth sector) over the 8 deg cone (24 tilt directions x 4 angles) or static."""
    nphi = int(round(360 / dphi))
    best = {}
    dirs = range(24) if swept else [0]
    thetas = (0.0, STOP / 3, 2 * STOP / 3, STOP) if swept else (0.0,)
    for k in dirs:
        psi = 2 * math.pi * k / 24
        a = np.array([-math.sin(psi), math.cos(psi), 0.0])        # tilts +Z toward (cos psi, sin psi)
        for th in thetas:
            R = hrt.rodrigues(a, math.radians(th))
            X = Q @ R.T
            r = np.hypot(X[:, 0], X[:, 1])
            key = np.floor(X[:, 2] / dz).astype(int) * 1000 + (np.floor(np.degrees(np.arctan2(X[:, 1], X[:, 0])) % 360 / dphi).astype(int) % nphi)
            o = np.lexsort((r, key))
            ks = key[o]
            last = np.r_[ks[1:] != ks[:-1], True]
            for idx in o[last]:
                kk = int(key[idx])
                if kk not in best or r[idx] > best[kk][0]:
                    best[kk] = (float(r[idx]), X[idx].copy(), tags[idx])
    return best


def line_corridor(env, od, z_lo=35.0, z_hi=265.0, dz=5.0):
    """Fixed line on the bay wall at azimuth phi (centre radius R_WALL - CLIP_T - od/2): per azimuth, the local relief (engine
    scallop or wall groove) needed so that the swept engine keeps CLR to the line, over z_lo..z_hi."""
    rl = R_WALL - CLIP_T - od / 2
    pts = np.array([v[1] for v in env.values()])
    who = np.array([v[2] for v in env.values()])
    out = []
    for phi in np.arange(0.0, 360.0, 2.0):
        c = np.array([rl * math.cos(math.radians(phi)), rl * math.sin(math.radians(phi))])
        m = (pts[:, 2] >= z_lo) & (pts[:, 2] < z_hi)
        d = np.hypot(pts[m, 0] - c[0], pts[m, 1] - c[1]) - od / 2
        z = pts[m, 2]
        relief = np.maximum(0.0, CLR - d)
        bands = {}
        for zz, rr, ww in zip(np.floor(z / dz) * dz, relief, who[m]):
            if rr > bands.get(zz, (0.0, ""))[0]:
                bands[zz] = (float(rr), str(ww))
        need = {f"{int(k)}..{int(k + dz)}": [round(v[0], 2), v[1]] for k, v in sorted(bands.items()) if v[0] > 0}
        out.append({"phi_deg": float(phi), "max_relief_mm": round(float(relief.max()) if len(relief) else 0.0, 2),
                    "min_gap_mm": round(float(d.min()) if len(d) else 99.0, 2), "relief_by_band": need})
    return out


def static_r(env_static, z0, z1, phi, half_deg=12.0):
    """Max static engine radius over z0..z1 within phi +/- half_deg (from the static envelope)."""
    best = (0.0, "")
    for v in env_static.values():
        p = v[1]
        if z0 <= p[2] < z1:
            a = math.degrees(math.atan2(p[1], p[0])) % 360
            if min(abs(a - phi), 360 - abs(a - phi)) <= half_deg and v[0] > best[0]:
                best = (v[0], v[2])
    return best


def o1_window():
    """Straight radial hose: K rule gives L >= L_min(EI); the wall (neutral and 8 deg stop, 3 mm) gives L <= L_max(r_e)."""
    res = {}
    for r_e in (22.0, 15.0, 10.0):
        p0 = np.array([-r_e * 1e-3, 0.0, hrt.Z_ENG_END])
        d = p0 / np.linalg.norm(p0)
        rows, L_max = [], None
        for L in np.arange(0.20, 0.621, 0.01):
            nodes = hf.centreline_straight(p0, d, float(L))
            kx, _, bx, Ux = hf.solve(nodes, 0.5, axis=(1, 0, 0), theta=1e-3)
            ky, _, by, Uy = hf.solve(nodes, 0.5, axis=(0, 1, 0), theta=1e-3)
            c = hrt.clearance(nodes, Ux, Uy, 1e-3)
            ok = c["wall_min_mm_at_stop"] >= CLR and c["wall_min_mm_neutral"] >= CLR
            rows.append({"L_m": round(float(L), 2), "wall_neutral_mm": c["wall_min_mm_neutral"], "wall_stop_mm": c["wall_min_mm_at_stop"],
                         "K_EI0.5": [round(kx, 1), round(ky, 1)], "wall_ok": ok})
            if ok:
                L_max = round(float(L), 2)
        res[f"r_e={r_e:.0f}mm"] = {"L_max_wall_m": L_max, "rows": rows[::2]}
    Lmin = {f"EI={e}": round(hrt.L_min_radial(e), 3) for e in (0.05, 0.1, 0.25, 0.4, 0.45, 0.5)}
    return res, Lmin


def coil_case(name, r0, r1, dphi, z0, z1, phi0=90.0, sense=+1):
    nodes = hrt.helix(r0, phi0, z0, r1, z1, dphi, lead_out=0.0, sense=sense)
    rec = hrt.evaluate(name, nodes, 0.0, "", "", "")
    th = 1e-3
    kx, (F, M, Mp), bx, Ux = hf.solve(nodes, 0.5, axis=(1, 0, 0), theta=th)
    ky, (Fy, My, Mpy), by, Uy = hf.solve(nodes, 0.5, axis=(0, 1, 0), theta=th)
    # floor clearance to GM-09 (top face z 32 for r >= 52) at the 8 deg stop, 16 tilt directions
    sc = math.radians(STOP) / th
    fl = 1e9
    for k in range(16):
        psi = 2 * math.pi * k / 16
        U = (math.cos(psi) * Ux + math.sin(psi) * Uy) * sc
        for i, p in enumerate(nodes):
            q = (p + U[6 * i:6 * i + 3]) * 1e3
            if math.hypot(q[0], q[1]) + hrt.OD * 500 > GM09_R_IN:
                fl = min(fl, q[2] - hrt.OD * 500 - GM09_TOP)
    rec["gm09_floor_clearance_mm_at_stop"] = round(fl, 1)
    rec["engine_end_reaction_EI0.5_at_8deg"] = {"F_N": round(float(np.linalg.norm(F)) * sc, 2), "M_Nm": round(float(np.linalg.norm(M)) * sc, 3),
                                                "note": "hose bending reaction at the engine-end fitting (alpha tilt), EI 0.5 ASSUMED"}
    rec["engine_end_fitting_swept_mm"] = {"r_centre": r0 * 1e3, "z": z0 * 1e3, "r_allowed_for_-6_nut": round(r_allowed(z0 * 1e3, HEX_JIC6), 1),
                                          "ok": bool(r0 * 1e3 <= r_allowed(z0 * 1e3, HEX_JIC6))}
    return rec


def main():
    t0 = time.time()
    Q, tags, st, tb = engine_points()
    env_sw = envelope(Q, tags, swept=True)
    env_st = envelope(Q, tags, swept=False)
    out = {"id": "hose_routing_trade", "version": "v2", "date": "2026-10-12", "script": "03-cad/src/calcs/hose_routing_trade_v2.py",
           "supersedes": "adds feasibility checks to hose_routing_trade_v1.json (kept); v1 numbers for K / M7 / mass are not repeated except where re-run",
           "method": __doc__.strip().splitlines()[0], "cad": "CAD v3.3 engine group (pivot iterated), v3.3 pintle stack removed, v3.4 stack " + json.dumps(STACK_V34),
           "stations_mm": st, "n_points": int(len(Q)), "t_build_s": tb,
           "rules": {"bay_R_mm": R_WALL, "clearance_mm": CLR, "stop_deg": STOP, "K_req_Nm_rad": hrt.K_REQ}}

    # (a) O1 window
    win, Lmin = o1_window()
    out["O1_window"] = {"L_min_for_K20_m": Lmin, "L_max_for_wall": win,
                        "note": "K = 4EI/L (1 + 3x + 3x^2), x = h/L, h = 0.216 m; wall check = 3 mm at neutral and at the 8 deg stop (16 tilt directions) "
                                "for a hose OD 15 mm ASSUMED on the radial line through the pivot"}

    # (b) fixed-line corridor on the bay wall
    cor = line_corridor(env_sw, OD_TUBE)
    cor_q = line_corridor(env_sw, OD_QTR)
    best = sorted(cor, key=lambda r: (r["max_relief_mm"], -r["min_gap_mm"]))[:6]
    out["fixed_line_corridor_3/8in"] = {"line_centre_radius_mm": round(R_WALL - CLIP_T - OD_TUBE / 2, 2), "z_range_mm": [35, 265],
                                        "best_azimuths": best,
                                        "max_relief_over_azimuth_mm": [round(min(r["max_relief_mm"] for r in cor), 2), round(max(r["max_relief_mm"] for r in cor), 2)],
                                        "table_every_10deg": [{"phi": r["phi_deg"], "relief": r["max_relief_mm"], "gap": r["min_gap_mm"]} for r in cor if r["phi_deg"] % 10 == 0]}
    out["fixed_line_corridor_1/4in_info"] = {"best_azimuths": sorted(cor_q, key=lambda r: (r["max_relief_mm"], -r["min_gap_mm"]))[:3]}

    # (c) O3 riser: (O3a) to the v3.3 bonnet-top axial inlet at r 22 (az 180); (O3b) to a low inlet block on the case at the head plug
    w = OD_TUBE / 2
    o3a = []
    for (z0, z1) in ((60, 80), (80, 100), (100, 120), (120, 140), (140, 150), (150, 165), (165, 179), (179, 195), (195, 211)):
        rs, who = static_r(env_st, z0, z1, 180.0)
        need = rs + 1.0 + w                                 # riser centre radius hugging the engine with a 1 mm gap
        allow = r_allowed(z1, w)
        o3a.append({"z_mm": [z0, z1], "engine_r_static_mm": round(rs, 2), "by": who, "riser_centre_needed_mm": round(need, 2),
                    "riser_centre_allowed_mm": round(allow, 2), "margin_mm": round(allow - need, 2)})
    out["O3a_riser_to_bonnet_top_inlet"] = {"rows": o3a, "worst_margin_mm": min(r["margin_mm"] for r in o3a),
                                            "plus": "the v3.3 inlet is an axial -6 ORB port facing +Z at r 22 on the bonnet top: a riser coming from below needs a 180 deg "
                                                    "turn (bend radius >= ~24 mm for 3/8 x 0.035 tube, i.e. a down-leg at r >= 70) or an elbow whose outlet sweeps "
                                                    "beyond the wall -> not routable",
                                            "verdict": "INFEASIBLE inside the 140 mm bay with the 3 mm rule"}
    zb = st["bolt_z_fwd"]
    g = st["fwd_glands"]
    blk_z = (g[1] + g[2] + 1.0, zb + 6.0)                  # inlet block from just above the upper gland to 6 mm above the bolt row
    t_blk = 3.0 + OD_TUBE + 2 * 1.75                       # gap 3 + tube + 2 walls (riser welded into a 316 block)
    r_blk_out = 31.75 + t_blk
    r_riser = 31.75 + 3.0 + w
    o3b = {"inlet_concept": ("port block (316L) on the case OD at the head plug, held by 2 of the 8 radial M5 head screws (longer), O-ring face seal "
                             "around a 4-5 mm hole through the case wall into a new annulus on the plug OD between the upper chamber gland and a NEW third "
                             "gland below the bolt row, 3 mm radial passage from the annulus into the 10 mm manifold bore; riser 3/8 x 0.035 316 welded into "
                             "the block; v3.3 bonnet inlet and its screen seat deleted"),
           "block_z_mm": [round(blk_z[0], 1), round(blk_z[1], 1)], "block_radial_t_mm": round(t_blk, 2), "block_r_out_mm": round(r_blk_out, 2),
           "block_r_allowed_mm": round(r_allowed(blk_z[1], 0.0), 2), "block_margin_mm": round(r_allowed(blk_z[1], 0.0) - r_blk_out, 2),
           "riser_centre_r_mm": round(r_riser, 2), "riser_z_mm": [62.0, round(blk_z[0], 1)],
           "riser_margin_mm_at_block": round(r_allowed(blk_z[0], w) - r_riser, 2),
           "jog_to_coil_end": "S-bend r 39.5 -> 42 at z 62-75 (bend radius >= 24 mm) into a -6 JIC tube-weld adapter at r 42, z 62",
           "verdict": "geometrically feasible (sweep); needs Combustion review of the inlet path (manifold volume, single-side entry) and a CAD v3.4 check of "
                      "the plug section (third gland + annulus between z ~124 and the bolt row)"}
    o3b["manifold_volume_estimate_cm3"] = {"added_annulus": round(2 * math.pi * 27.8 * 1.5 * 4.0 / 1e3, 2), "added_passage": round(math.pi / 4 * 3 ** 2 * 23 / 1e3, 2),
                                           "v33_total": 3.3, "target": 5.0, "tag": "ESTIMATE (groove 1.5 x 4 at r 27.8, passage 3 x 23 mm)"}
    # stepped block: full thickness only below the screw row (riser entry + turn into the case hole), screw-row part 10 mm thick
    z_step = zb - 4.5                                       # bottom of the M5 counterbore zone (head 8.5 / 2 + 0.25)
    o3b["stepped_block"] = {"thick_part_z_mm": [round(blk_z[0], 1), round(z_step, 1)], "thick_r_out_mm": round(r_blk_out, 2),
                            "thick_margin_mm": round(r_allowed(z_step, 0.0) - r_blk_out, 2),
                            "thin_part_z_mm": [round(z_step, 1), round(blk_z[1], 1)], "thin_r_out_mm": 31.75 + 10.0,
                            "thin_margin_mm": round(r_allowed(blk_z[1], 0.0) - 41.75, 2),
                            "note": "margins are beyond the 3 mm rule; the uniform block above fails by 0.16 mm at its top outer edge"}
    o3b["plug_length_impact"] = {"glands_v33_mm": {"g1": [st["fwd_glands"][0], round(st["fwd_glands"][0] + st["fwd_glands"][2], 2)],
                                                   "g2": [st["fwd_glands"][1], round(st["fwd_glands"][1] + st["fwd_glands"][2], 2)]},
                                 "bolt_row_mm": zb, "bolt_hole_mm": [round(zb - 2.75, 2), round(zb + 2.75, 2)],
                                 "estimate": "the annulus (4 mm) + a land, or a third gland (4.85 + 3 mm), does not fit between g2 top 128.3 and the bolt hole "
                                             "133.8: the plug and case grow ~3 mm (annulus between g1 and g2, g1 then separates N2O from chamber gas) to ~8 mm "
                                             "(annulus + third gland, both chamber glands kept) -> head/stack top +3..+8 mm; CAD v3.4 to settle",
                                 "tag": "ESTIMATE"}
    out["O3b_riser_to_low_inlet"] = o3b

    # (d) coil variants incl. GM-09 floor and the engine-end fitting sweep
    coils = [coil_case("O3 coil r 42->54 mm, 300 deg, z 62->45", 0.042, 0.054, 300.0, 0.062, 0.045),
             coil_case("O3 coil r 45->55 mm, 330 deg, z 62->45", 0.045, 0.055, 330.0, 0.062, 0.045),
             coil_case("O3 coil r 46->56 mm, 300 deg, z 58->45", 0.046, 0.056, 300.0, 0.058, 0.045)]
    out["O3_coils"] = coils

    # (e) temperatures (thermal FE v1.1, DC-B1 hi bound: chamber h x2, nozzle x1.3, grey-gas radiation; conservative)
    th = {}
    if THERMAL.exists():
        d = np.load(THERMAL)
        X, T = d["X"], d["Tmax"] - 273.15
        sel = np.abs(X[:, 0] - 31.75) < 0.05
        for (z0, z1) in ((35, 50), (50, 65), (65, 80), (80, 115), (115, 125), (125, 145), (150, 180)):
            m = sel & (X[:, 1] >= z0) & (X[:, 1] < z1)
            if m.any():
                th[f"{z0}..{z1}"] = round(float(T[m].max()), 1)
    out["case_OD_Tmax_C_B1_hi"] = {"by_z_mm": th, "src": str(THERMAL), "tag": "FEA thermal v1.1 (hi bound; flight + 3600 s soak); nominal case pending"}

    # (f) decision (lead rule 2026-10-12: shortest vehicle that meets K <= 20 with no rotating seal in liquid N2O)
    w22 = win["r_e=22mm"]["L_max_wall_m"]
    out["decision"] = {
        "selected": "O3b: low coil around the case above GM-09 (r 42->54 mm, 300 deg, z 62->45 mm, -6 PTFE/SS hose L 0.25 m) + engine riser 3/8 x 0.035 "
                    "316 welded into a low inlet block at the head plug + fixed 3/8 line on the bay wall (corridor azimuths 142 / 218 deg are best; coil angle 300-330 deg sets the fixed-end azimuth; "
                    "or outside the airframe), valve/tank interface directly above the engine zone",
        "why": (f"shortest vehicle: valve end at the zone top (~0.26 m above the pivot) instead of 0.215 + L cos(5.8 deg) + fittings for O1; "
                f"K 0.6-7.8 N m/rad over EI 0.05-0.5 (meets K <= 20 at any EI in the assumed range, so the length does not depend on B-FD-1); "
                f"M at 7 deg <= 0.95 N m; no rotating seal"),
        "length_saved_m": {"vs_O1_as_adopted_L0.40": round(0.215 + 0.40 * 0.9948 + 0.03 - 0.26, 2),
                           "vs_O1_r22_L_max_wall": round(0.215 + (w22 or 0) * 0.9948 + 0.03 - 0.26, 2),
                           "basis": "hose top fitting + 0.03 m vs the zone-top valve station 0.26 m; ESTIMATE"},
        "O1_finding": (f"the adopted O1 rule (radial line, L >= 0.40 m) does not fit the 140 mm bay with the inlet at r 22 mm: the 3 mm wall rule caps "
                       f"L at {w22} m (neutral -0.2 / stop -3.5 mm at L 0.40), and K <= 20 at EI 0.5 needs L >= 0.373 m -> O1 at r 22 works only if "
                       f"B-FD-1 shows EI <= ~0.25 N m2; with the inlet at r 15 mm L_max is 0.50 m"),
        "gates": ["G1 Combustion accepts the low inlet (annulus + 3 mm passage, manifold +1.2 cm3 ESTIMATE to ~4.5 of the 5 cm3 target, single-side entry)",
                  "G2 CAD v3.4: plug/case +3..+8 mm for the annulus/gland, stepped inlet block, riser and coil modelled and swept at all 9 poses + the 8 deg cone",
                  "G3 v3.4 HV69 stack keeps r <= 22.5 mm within +/-15 deg of the fixed-line azimuth over z 215-252 mm (else 1/4 in line, groove or external line)",
                  "G4 hose datasheet: minimum (dynamic) bend radius <= 39 mm at -6, temperature rating covering a 136-178 C case 3-15 mm away (B1 hi bound), "
                  "O2-clean PTFE; B-FD-1 measures K pressurised on the coil",
                  "G5 thermal: riser/hose share the trapped-liquid relief requirement (valve closed in coasts); shield or wrap where the riser passes the "
                  "pre-chamber (case OD up to 312 C at the hi bound)"],
        "fallback": "O1 with the inlet moved to r <= 15 mm (L 0.37-0.50 m, valve end ~0.6 m) or O1 at r 22 with L = 0.27 m if B-FD-1 gives EI <= 0.25 N m2",
        "rejected": {"O2 helix at the stack top": "K 27-132 N m/rad at EI 0.25-0.5, installed bend radius 5.5 mm, wall/engine interference",
                     "O5 inverted U above the stack": "K 32-156 N m/rad at EI 0.25-0.5, wall interference 30-50 mm",
                     "O3a riser to the bonnet-top inlet": "riser cannot pass the bonnet/head inside the sweep (-2.1 to -6.6 mm)",
                     "O4 rotary unions": "rotating seals in liquid N2O at 7 MPa, no qualified part, no length saving without an airframe channel"},
        "tag": "DERIVED (linear frame + CAD v3.3 sweep); hose EI, OD, bend radius and mass ASSUMED until datasheets / B-FD-1"}

    out["t_run_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", OUT, out["t_run_s"], "s")
    print("O1 L_min", Lmin)
    for k, v in win.items():
        print("O1", k, "L_max wall", v["L_max_wall_m"])
    print("fixed line best", [(b["phi_deg"], b["max_relief_mm"], b["min_gap_mm"]) for b in best])
    print("fixed line 1/4 best", [(b["phi_deg"], b["max_relief_mm"]) for b in out["fixed_line_corridor_1/4in_info"]["best_azimuths"]])
    print("O3a worst margin", out["O3a_riser_to_bonnet_top_inlet"]["worst_margin_mm"])
    for r in o3a:
        print("  ", r)
    print("O3b", {k: v for k, v in o3b.items() if k not in ("inlet_concept", "verdict")})
    for c in coils:
        e = c["per_EI"]["EI=0.5"]
        print(c["option"], "L", c["hose_length_m"], "K", e["K_alpha_Nm_rad"], e["K_beta_Nm_rad"], "Rstop", e["min_bend_radius_at_stop_m"], "clr", c["clearance_8deg"]["wall_min_mm_at_stop"],
              c["clearance_8deg"]["engine_min_mm_at_stop"], "floor", c["gm09_floor_clearance_mm_at_stop"], "end", c["engine_end_fitting_swept_mm"], c["engine_end_reaction_EI0.5_at_8deg"])
    print("case T", th)


if __name__ == "__main__":
    main()
