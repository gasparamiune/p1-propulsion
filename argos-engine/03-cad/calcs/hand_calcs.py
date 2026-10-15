"""Hand calculations v2 (DERIVED) for the CAD v3 pressure parts: case tube, forward closure (injector head)
retention by 8 radial M5 screws, aft closure M63x1.5 thread and retaining lip (nozzle retention), graphite
insert, liner, O-ring glands, and the N2O tank.  They are the analytic cross-checks for the FEA (04-fea) and
size CAD parameters.

Run:  python calcs/hand_calcs.py  -> writes calcs/hand_calcs_v2.json and calcs/HAND-CALCS.md
(hand_calcs_v1.json, 2026-10-11, MEOP 31 bar, CAD v2 geometry, is kept as history.)

v2 (2026-10-12): lead decision chamber MEOP 31 -> 45 bar (Combustion pintle full-stroke failure case);
pressure cases from 04-fea/src/loadcases.py: LC1 Pc max, LC2 MEOP 45 bar (SF 1.5 y / 2.0 u at temperature),
LC4 proof 67.5 bar (no yield, 20 C), BN blocked nozzle 63.1 bar (no yield at temperature).  The part
temperatures come from the LC5 thermal FEA; until then every Al row reports MS at 20 C and the highest part
temperature T_allow at which all its MS stay >= 0 (the FEA must show the part stays below T_allow).

Conventions: SI internally; MS = allowable / (SF x applied) - 1 (MS >= 0 passes).
Requirements: ENG-09 pressure parts SF 1.5 yield / 2.0 ultimate at MEOP and temperature; ENG-10 same
for structure under design limit loads.  Graphite / phenolic: no yield, strength x SF ultimate.
References (cited per line):
  [R1] Roark's Formulas for Stress and Strain, 7th ed. (Young & Budynas), Table 13.5 (thick cylinders, Lame);
       Timoshenko & Woinowsky-Krieger, Theory of Plates and Shells (1959) Ch. 3 eqs. for symmetrical bending
       of circular plates (used in closed form, integrated numerically for annular loads, verified against the
       clamped solid plate).
  [R2] Parker O-Ring Handbook ORD 5700: static glands, Fig. 3-2 extrusion limits, stretch <= 5 %.
       Numeric gland ranges are generic guidance values; verify against ORD 5700 Design Table 4-2.
  [R3] ISO 724 / ISO 965-1 metric thread dimensions and tolerances (6g/6H), thread shear areas per the
       FED-STD-H28 / Machinery's Handbook formulas (A_s external at D1max, A_n internal at dmin).
  [R4] Bruhn, Analysis and Design of Flight Vehicle Structures (1973), Ch. D1: shear-out, bearing, net tension.
  [R5] Bryan/Bresse long-tube collapse p_cr = 2E/(1-nu^2) (t/Dm)^3 (Timoshenko & Gere, Theory of Elastic
       Stability, 1961, Sec. 7.2).
  [R6] SAE AS568 O-ring sizes (2-xxx series: 3.53 mm CS, ID 1.984 in for -226, +0.125 in per dash).
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "04-fea" / "src"))
import config  # noqa: E402
from engmat import prop  # noqa: E402

PI = math.pi
THREAD = {  # ISO 261 coarse: d -> pitch
    0.003: 0.5e-3, 0.004: 0.7e-3, 0.005: 0.8e-3, 0.006: 1.0e-3, 0.008: 1.25e-3}


def d3(d):
    return d - 1.22687 * THREAD[round(d, 3)]


def ms(allow, sf, applied):
    if sf is None or allow is None:
        return None
    return allow / (sf * applied) - 1.0 if applied > 0 else float("inf")


def row(name, applied, allow_y, allow_u, sfy, sfu, unit="MPa", note=""):
    s = 1e-6 if unit == "MPa" else 1.0
    return {"check": name, "applied": applied * s, "allow_yield": allow_y * s if allow_y else None,
            "allow_ult": allow_u * s if allow_u else None, "SF_y": sfy, "SF_u": sfu,
            "MS_y": ms(allow_y, sfy, applied), "MS_u": ms(allow_u, sfu, applied), "unit": unit, "note": note}


# ---------------------------------------------------------------------------------------------
def cylinder(P, OD, t, mat, T_C, sfy, sfu, label):
    """Thin-wall and Lame stresses in a closed-end cylinder; von Mises at the bore."""
    ro, ri = OD / 2, OD / 2 - t
    rm = (ro + ri) / 2
    s_h_thin = P * rm / t
    s_a = P * ri ** 2 / (ro ** 2 - ri ** 2)
    s_h_lame = P * (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2)   # [R1] Table 13.5 case 1c, at r = ri
    s_r = -P
    vm = math.sqrt(0.5 * ((s_h_lame - s_a) ** 2 + (s_a - s_r) ** 2 + (s_r - s_h_lame) ** 2))
    Fty, Ftu = prop(mat, "Fty", T_C), prop(mat, "Ftu", T_C)
    out = {"label": label, "P_Pa": P, "OD_m": OD, "t_m": t, "T_C": T_C, "material": mat,
           "hoop_thin_MPa": s_h_thin / 1e6, "hoop_lame_bore_MPa": s_h_lame / 1e6, "axial_MPa": s_a / 1e6,
           "vm_bore_MPa": vm / 1e6,
           "rows": [row(f"{label}: von Mises at bore (Lame)", vm, Fty, Ftu, sfy, sfu)]}
    # max temperature for MS_y >= 0 and MS_u >= 0
    Ts = [t_ / 2 for t_ in range(40, 701)]
    out["T_max_C_for_MS0"] = max([T for T in Ts if prop(mat, "Fty", T) >= sfy * vm and prop(mat, "Ftu", T) >= sfu * vm] or [None])
    return out


def closure_bolts(P, D_seal, n, d, bolt_mat, case_t, case_OD, case_mat, closure_mat, e, Le, T_C, sfy, sfu, label,
                  share=1.15, rows_n=1):
    """Radial screws in single shear retaining a plug closure (end load P*pi/4*D_seal^2)."""
    F = P * PI / 4 * D_seal ** 2
    V = F / n * share  # unequal sharing from hole clearance: x1.15 (ASSUMED)
    A3 = PI / 4 * d3(d) ** 2
    tau = V / A3
    Fty_b, Ftu_b = prop(bolt_mat, "Fty"), prop(bolt_mat, "Ftu")
    fsu_ratio = 0.5 if bolt_mat == "STEEL-12.9" else 0.6  # EN 1993-1-8 alpha_v 0.5 for 10.9/12.9
    Fty_c, Ftu_c = prop(case_mat, "Fty", T_C), prop(case_mat, "Ftu", T_C)
    rows = []
    rows.append(row(f"{label}: screw shear at thread root (d3={d3(d)*1e3:.3f} mm)", tau, 0.577 * Fty_b, fsu_ratio * Ftu_b, sfy, sfu,
                    note=f"V/screw={V:.0f} N incl. x{share} sharing; F_end={F:.0f} N"))
    sbr = V / (d * case_t)
    rows.append(row(f"{label}: bearing in case wall", sbr, 1.4 * Fty_c, 1.6 * Ftu_c, sfy, sfu, note=f"e/D={e/d:.2f} (>=2 for the bearing ratios used)"))
    A_so = 2 * case_t * (e - d / 2)
    rows.append(row(f"{label}: shear-out of case to tube end", V / A_so, 0.577 * Fty_c, 0.6 * Ftu_c, sfy, sfu, note=f"e={e*1e3:.1f} mm [R4]"))
    dh = d + 0.0005
    n_row = n // rows_n
    A_net = PI * (case_OD - case_t) * case_t - n_row * dh * case_t
    s_ax = F / A_net   # inboard row carries the full end load (conservative)
    # The screw rows are OUTBOARD of the O-rings: no internal pressure there, so no hoop stress (physical).
    # Upper bound with full hoop superposed is reported in the note only.
    s_hoop = P * (case_OD / 2 - case_t / 2) / case_t
    vm_ub = math.sqrt(s_hoop ** 2 - s_hoop * s_ax + s_ax ** 2)
    rows.append(row(f"{label}: case net section at inboard screw row ({n_row} holes, axial)", s_ax, Fty_c, Ftu_c, sfy, sfu,
                    note=f"net axial {s_ax/1e6:.1f} MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM {vm_ub/1e6:.1f} MPa"))
    Fty_p, Ftu_p = prop(closure_mat, "Fty", T_C), prop(closure_mat, "Ftu", T_C)
    rows.append(row(f"{label}: bearing of screw on closure thread (Le={Le*1e3:.1f} mm)", V / (d * Le), 1.4 * Fty_p, 1.6 * Ftu_p, sfy, sfu))
    return {"label": label, "F_end_N": F, "n": n, "d_m": d, "V_per_screw_N": V, "T_C": T_C, "rows": rows}


def oring_gland(label, bore, bore_tol, groove_d, groove_tol, W, W_tol, ID, ID_tol, G, plug_d, plug_tol, P, durometer):
    """Static radial (piston) gland per [R2]: squeeze, stretch, fill, extrusion gap."""
    L_max = (bore + bore_tol[1] - (groove_d + groove_tol[0])) / 2
    L_min = (bore + bore_tol[0] - (groove_d + groove_tol[1])) / 2
    sq_min = (W + W_tol[0] - L_max) / (W + W_tol[0])
    sq_max = (W + W_tol[1] - L_min) / (W + W_tol[1])
    stretch_max = (groove_d + groove_tol[1]) / (ID + ID_tol[0]) - 1
    stretch_min = (groove_d + groove_tol[0]) / (ID + ID_tol[1]) - 1
    # CS reduction from stretch (Parker approximation for small stretch: ~0.5 x stretch on W)
    fill_max = (PI / 4 * (W + W_tol[1]) ** 2) / (L_min * G)
    gap_max = (bore + bore_tol[1]) - (plug_d + plug_tol[0])  # diametral clearance
    # extrusion limit (diametral) approximated from Parker Fig. 3-2, verify:
    #   75 Sh A: ~0.25 mm @ 3.5 MPa, ~0.15 mm @ 7 MPa, ~0.10 mm @ 10.5 MPa
    #   90 Sh A: ~0.35 mm @ 3.5 MPa, ~0.25 mm @ 7 MPa, ~0.18 mm @ 10.5 MPa
    table = {75: [(3.5e6, 0.25e-3), (7e6, 0.15e-3), (10.5e6, 0.10e-3), (14e6, 0.07e-3)],
             90: [(3.5e6, 0.35e-3), (7e6, 0.25e-3), (10.5e6, 0.18e-3), (14e6, 0.13e-3)]}[durometer]
    import numpy as np
    gap_lim = float(np.interp(P, [p for p, _ in table], [g for _, g in table]))
    ok = (0.15 <= sq_min) and (sq_max <= 0.32) and (stretch_max <= 0.05) and (stretch_min >= 0.0) and (fill_max <= 0.90) and (gap_max <= gap_lim)
    return {"label": label, "bore_mm": bore * 1e3, "groove_d_mm": groove_d * 1e3, "W_mm": W * 1e3, "ID_mm": ID * 1e3, "G_mm": G * 1e3,
            "gland_depth_mm": [L_min * 1e3, L_max * 1e3], "squeeze_pct": [sq_min * 100, sq_max * 100],
            "stretch_pct": [stretch_min * 100, stretch_max * 100], "fill_max_pct": fill_max * 100,
            "diametral_gap_max_mm": gap_max * 1e3, "extrusion_gap_limit_mm": gap_lim * 1e3, "P_Pa": P, "durometer_ShA": durometer,
            "criteria": "squeeze 15-32 %, stretch 0-5 %, fill <= 90 %, gap <= Parker Fig.3-2 limit (approx) [R2]",
            "pass": bool(ok)}


def circular_plate(label, P, a, t, mat, T_C, sfy, sfu, nu=0.33, edge="simply supported"):
    """[R1] Table 11.2: uniform pressure on a solid circular plate.  10a s.s.: 3(3+nu)qa^2/(8t^2) at centre;
    10b clamped: 3qa^2/(4t^2) at edge."""
    s = 3 * (3 + nu) * P * a ** 2 / (8 * t ** 2) if edge.startswith("simply") else 3 * P * a ** 2 / (4 * t ** 2)
    return row(f"{label}: plate bending ({edge}), a={a*1e3:.1f} t={t*1e3:.1f} mm", s, prop(mat, "Fty", T_C), prop(mat, "Ftu", T_C), sfy, sfu)


# ============================================================================================= v2 additions
import numpy as np  # noqa: E402

INCH = 0.0254


def as568_2xx(dash):
    """[R6] AS568 2-xxx series: CS 0.139 in; ID 1.984 in at -226, +0.125 in per dash from -222 to -247."""
    assert 222 <= dash <= 247
    ID = (1.984 + 0.125 * (dash - 226)) * INCH
    tol = (0.018 if dash <= 227 else 0.025 if dash <= 238 else 0.030) * INCH
    return {"dash": f"AS568-{dash}", "ID": ID, "ID_tol": (-tol, tol), "W": 0.139 * INCH, "W_tol": (-0.004 * INCH, 0.004 * INCH)}


def lame(Pi, Po, ri, ro, r):
    """[R1] Table 13.5: thick cylinder, internal Pi and external Po: (hoop, radial) at radius r."""
    A = (Pi * ri ** 2 - Po * ro ** 2) / (ro ** 2 - ri ** 2)
    B = (Pi - Po) * ri ** 2 * ro ** 2 / (ro ** 2 - ri ** 2)
    return A + B / r ** 2, A - B / r ** 2


def vm3(s1, s2, s3):
    return math.sqrt(0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2))


def T_allow(stress, mat, sfy, sfu, key_y="Fty", key_u="Ftu"):
    """Highest temperature (C, 0.5 C steps up to 350) at which MS_y and MS_u stay >= 0 (None if none)."""
    ok = None
    for T in np.arange(20.0, 350.01, 0.5):
        y = prop(mat, key_y, T) >= (sfy or 0) * stress if sfy else True
        u = prop(mat, key_u, T) >= (sfu or 0) * stress if sfu else True
        if y and u:
            ok = float(T)
        else:
            break
    return ok


def annular_plate(a, b, t, E, nu, load, n=6001):
    """[R1] Timoshenko Ch. 3, axisymmetric Kirchhoff plate b <= r <= a, outer edge CLAMPED, inner edge FREE.
    load: ('band', q, r1, r2) uniform pressure over r1..r2, or ('ring', F_total, r0).
    d/dr[(1/r) d/dr(r w')] = Q/D, Q(r) = (1/r) int_b^r q rho drho; M_r = -D(w'' + nu w'/r), M_t = -D(w'/r + nu w'').
    Returns max |M| (N m/m), the radius, bending stress 6M/t^2 and the mean shear at the clamped edge."""
    D = E * t ** 3 / (12 * (1 - nu ** 2))
    r = np.linspace(b, a, n)
    if load[0] == "band":
        _, q, r1, r2 = load
        qr = np.where((r >= r1) & (r <= r2), q, 0.0)
        F = q * math.pi * (r2 ** 2 - r1 ** 2)
    else:
        _, F, r0 = load
        qr = np.zeros_like(r)
        k = int(np.argmin(abs(r - r0)))
        dr = r[1] - r[0]
        qr[k] = F / (2 * math.pi * r[k] * dr)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (qr[1:] * r[1:] + qr[:-1] * r[:-1]) * np.diff(r))])
    Q = cum / r
    G = np.concatenate([[0.0], np.cumsum(0.5 * (Q[1:] + Q[:-1]) * np.diff(r))]) / D
    H = np.concatenate([[0.0], np.cumsum(0.5 * (r[1:] * G[1:] + r[:-1] * G[:-1]) * np.diff(r))])
    C2 = -H[-1] / (1 + (1 - nu) * (a ** 2 - b ** 2) / (2 * b ** 2))
    C1 = (1 - nu) * C2 / b ** 2
    th = (H + C1 * (r ** 2 - b ** 2) / 2 + C2) / r
    dth = -th / r + G + C1
    Mr = -D * (dth + nu * th / r)
    Mt = -D * (th / r + nu * dth)
    i_r, i_t = int(np.argmax(abs(Mr))), int(np.argmax(abs(Mt)))
    M = max(abs(Mr[i_r]), abs(Mt[i_t]))
    where = r[i_r] if abs(Mr[i_r]) >= abs(Mt[i_t]) else r[i_t]
    return {"F_N": F, "M_max_Nm_per_m": float(M), "at_r_mm": float(where * 1e3), "sigma_bend_Pa": float(6 * M / t ** 2),
            "Mr_outer": float(Mr[-1]), "Mt_inner": float(Mt[0]), "tau_mean_outer_Pa": float(F / (2 * math.pi * a * t)),
            "w_max_m": None}


def _verify_annular():
    """Clamped solid plate limit (b -> 0): M_r(a) = -q a^2/8, centre M = (1+nu) q a^2/16 [R1]."""
    a, q, nu = 0.03, 1e6, 0.3
    res = annular_plate(a, a * 1e-4, 0.004, 70e9, nu, ("band", q, 0.0, a), n=40001)
    return {"Mr_outer_numeric": res["Mr_outer"], "Mr_outer_exact": -q * a ** 2 / 8,
            "Mt_small_hole_numeric": res["Mt_inner"], "Mt_small_hole_exact": 2 * (1 + nu) * q * a ** 2 / 16,
            "note": "small central hole doubles the tangential moment of the solid-plate centre (concentration factor 2)",
            "rel_err_outer": abs(res["Mr_outer"] + q * a ** 2 / 8) / (q * a ** 2 / 8)}


def thread_strip(F, d, p, Le, mat_ext, mat_int, T_C, sfy, sfu, label, es=None, Td2=None, TD2=None, TD1=None):
    """[R3] Stripping of a fine metric thread (6g/6H) under axial load F.  A_s (external thread, sheared at the
    internal minor diameter D1max) and A_n (internal thread, sheared at the external major diameter dmin)."""
    es = es if es is not None else -(15 + 11 * p * 1e3) * 1e-6       # ISO 965-1 fundamental deviation g
    d2 = d - 0.649519 * p
    D1 = d - 1.082532 * p
    d2min = d2 + es - Td2
    D2max = d2 + TD2
    D1max = D1 + TD1
    dmax = d + es
    dmin = dmax - (0.236e-3 if p >= 1.5 else 0.18e-3)                  # Td grade 6 (ISO 965-1: 236 um for P 1.5)
    A_s = math.pi * Le * D1max * (p / 2 + 0.57735 * (d2min - D1max)) / p
    A_n = math.pi * Le * dmin * (p / 2 + 0.57735 * (dmin - D2max)) / p
    rows = [row(f"{label}: external thread (case) stripping, A_s {A_s*1e6:.0f} mm2", F / A_s, 0.577 * prop(mat_ext, "Fty", T_C),
                0.60 * prop(mat_ext, "Ftu", T_C), sfy, sfu, note=f"F {F:.0f} N, Le {Le*1e3:.0f} mm, uniform load share assumed (first-thread peak in FEA)"),
            row(f"{label}: internal thread (closure) stripping, A_n {A_n*1e6:.0f} mm2", F / A_n, 0.577 * prop(mat_int, "Fty", T_C),
                0.60 * prop(mat_int, "Ftu", T_C), sfy, sfu)]
    return {"A_s_m2": A_s, "A_n_m2": A_n, "rows": rows}


def rod_gland(label, rod, rod_tol, bore, bore_tol, groove_d, groove_tol, ring, G, P, durometer):
    """[R2] Static rod gland: O-ring in a groove of the housing bore, sealing on the rod (case aft land)."""
    W, Wt, ID, IDt = ring["W"], ring["W_tol"], ring["ID"], ring["ID_tol"]
    L_max = ((groove_d + groove_tol[1]) - (rod + rod_tol[0])) / 2
    L_min = ((groove_d + groove_tol[0]) - (rod + rod_tol[1])) / 2
    sq_min = (W + Wt[0] - L_max) / (W + Wt[0])
    sq_max = (W + Wt[1] - L_min) / (W + Wt[1])
    stretch_max = (rod + rod_tol[1]) / (ID + IDt[0]) - 1
    stretch_min = (rod + rod_tol[0]) / (ID + IDt[1]) - 1
    fill_max = (math.pi / 4 * (W + Wt[1]) ** 2) / (L_min * G)
    gap_max = (bore + bore_tol[1]) - (rod + rod_tol[0])
    table = {75: [(3.5e6, 0.25e-3), (7e6, 0.15e-3), (10.5e6, 0.10e-3), (14e6, 0.07e-3)],
             90: [(3.5e6, 0.35e-3), (7e6, 0.25e-3), (10.5e6, 0.18e-3), (14e6, 0.13e-3)]}[durometer]
    gap_lim = float(np.interp(P, [p for p, _ in table], [g for _, g in table]))
    ok = (0.15 <= sq_min) and (sq_max <= 0.32) and (stretch_max <= 0.05) and (stretch_min >= 0.0) and (fill_max <= 0.90) and (gap_max <= gap_lim)
    return {"label": label, "ring": ring["dash"], "rod_mm": rod * 1e3, "groove_d_mm": groove_d * 1e3, "W_mm": W * 1e3, "ID_mm": ID * 1e3,
            "gland_depth_mm": [L_min * 1e3, L_max * 1e3], "squeeze_pct": [sq_min * 100, sq_max * 100],
            "stretch_pct": [stretch_min * 100, stretch_max * 100], "fill_max_pct": fill_max * 100,
            "diametral_gap_max_mm": gap_max * 1e3, "extrusion_gap_limit_mm": gap_lim * 1e3, "P_Pa": P, "durometer_ShA": durometer,
            "criteria": "squeeze 15-32 %, stretch 0-5 %, fill <= 90 %, gap <= Parker Fig.3-2 limit (approx) [R2]", "pass": bool(ok)}


def main():
    import layout
    sys.path.insert(0, str(HERE.parents[2] / "04-fea" / "src"))
    import loadcases
    P, log = config.build()
    v = lambda k: P[k]["v"]
    LC = {c["id"]: c for c in loadcases.load_cases(P)}
    S = layout.stations(P)
    sfy, sfu = v("SF_yield"), v("SF_ult")
    # pressure cases: (id, P, SF_y, SF_u, temperature note)
    PC = [("LC1", LC["LC1"]["chamber_Pa"], sfy, sfu), ("LC2", LC["LC2"]["chamber_Pa"], sfy, sfu),
          ("LC4", LC["LC4"]["chamber_Pa"], 1.0, None), ("BN", LC["BN"]["chamber_Pa"], 1.0, None)]
    out = {"id": "ENG-MECH-HANDCALCS", "version": "v2", "date": "2026-10-12", "tag": "DERIVED (this script)",
           "basis": "CAD v3 geometry (config.py v3); loadcases v1 (04-fea/loadcases_v1.json); MEOP 45 bar lead decision 2026-10-12",
           "pressure_cases": [{"id": i, "P_bar": p / 1e5, "SF_y": a, "SF_u": b} for i, p, a, b in PC],
           "temperature_note": "Al rows evaluated at 20 C with T_allow = highest part temperature keeping MS >= 0; LC5 thermal FEA must confirm",
           "inputs": {k: P[k] for k in ["MEOP_chamber", "P_blocked_nozzle", "MEOP_tank", "Pc_max", "case_OD", "case_t", "case_bore_seal",
                                        "n_bolts_chamber", "bolt_d_chamber", "bolt_edge_chamber", "aft_thread_len", "aft_lip_t", "insert_OD",
                                        "insert_sleeve_t", "liner_t", "tank_OD", "tank_t"]},
           "sections": {}, "verification": {"annular_plate_vs_clamped_solid": _verify_annular()}}
    SEC = out["sections"]
    AL = "AL6061-T6"

    def tag_T(rr, stress_Pa, mat, sy, su):
        rr["T_allow_C"] = T_allow(stress_Pa, mat, sy, su) if mat.startswith("AL") else None
        return rr

    # ---- 1) case tube sections (pressurised inside only) -----------------------------------------------------
    ri = (v("case_OD") - 2 * v("case_t")) / 2
    secs = [("full wall 63.50/57.15", v("case_OD") / 2, ri),
            ("fwd seal land 57.25 bore", v("case_OD") / 2, v("case_bore_seal") / 2),
            ("collar groove 62.50 (pivot plane)", v("case_OD") / 2 - v("collar_groove_depth"), ri),
            ("aft seal land 61.0 (above the gland)", v("case_aft_land_d") / 2, ri),
            ("aft thread root M63x1.5 d3 61.16", (0.063 - 1.22687 * 0.0015) / 2, ri)]
    rows = []
    for (cid, Pp, sy, su) in PC:
        for nm, ro, rin in secs:
            sh, sr = lame(Pp, 0.0, rin, ro, rin)
            if "thread root" in nm or "aft seal land" in nm:
                F_ax = Pp * math.pi / 4 * v("case_aft_land_d") ** 2          # aft closure end load through the thread (bound)
            else:
                F_ax = Pp * math.pi / 4 * v("case_bore_seal") ** 2           # forward closure end load carried by the wall
            sa = F_ax / (math.pi * (ro ** 2 - rin ** 2))
            s = vm3(sh, sa, sr)
            rr = row(f"Case {nm} [{cid} {Pp/1e5:.1f} bar]: von Mises at bore (Lame + end load)", s, prop(AL, "Fty"), prop(AL, "Ftu"), sy, su,
                     note=f"hoop {sh/1e6:.1f}, axial {sa/1e6:.1f}, radial {sr/1e6:.1f} MPa; wall {(ro-rin)*1e3:.3f} mm")
            rows.append(tag_T(rr, s, AL, sy, su))
    SEC["case"] = {"rows": rows}

    # ---- 2) forward closure: 8 radial M5 A4-70 -------------------------------------------------------------
    fwd = []
    for (cid, Pp, sy, su) in PC:
        r = closure_bolts(Pp, v("case_bore_seal"), int(v("n_bolts_chamber")), v("bolt_d_chamber"), "SS-A4-70",
                          (v("case_OD") - v("case_bore_seal")) / 2, v("case_OD"), AL, AL, v("bolt_edge_chamber"), 0.0060, 20, sy, su or 1.0,
                          f"Fwd closure 8xM5 A4-70 [{cid} {Pp/1e5:.1f} bar]")
        for rr in r["rows"]:
            if su is None:
                rr["MS_u"], rr["SF_u"] = None, None
            if "screw shear" not in rr["check"]:
                tag_T(rr, rr["applied"] * 1e6 * (1.0 if "shear-out" not in rr["check"] else 1.0), AL, None, None)
        fwd += r["rows"]
    # T_allow for the Al rows of the closure joint (bearing, shear-out, net section, closure thread) at LC2
    r2 = closure_bolts(LC["LC2"]["chamber_Pa"], v("case_bore_seal"), int(v("n_bolts_chamber")), v("bolt_d_chamber"), "SS-A4-70",
                       (v("case_OD") - v("case_bore_seal")) / 2, v("case_OD"), AL, AL, v("bolt_edge_chamber"), 0.0060, 20, sfy, sfu, "tmp")
    Tj = None
    for T in np.arange(20.0, 300.01, 1.0):
        rT = closure_bolts(LC["LC2"]["chamber_Pa"], v("case_bore_seal"), int(v("n_bolts_chamber")), v("bolt_d_chamber"), "SS-A4-70",
                           (v("case_OD") - v("case_bore_seal")) / 2, v("case_OD"), AL, AL, v("bolt_edge_chamber"), 0.0060, float(T), sfy, sfu, "tmp")
        if all((x["MS_y"] is None or x["MS_y"] >= 0) and (x["MS_u"] is None or x["MS_u"] >= 0) for x in rT["rows"]):
            Tj = float(T)
        else:
            break
    SEC["fwd_closure"] = {"rows": fwd, "V_per_screw_LC2_N": r2["V_per_screw_N"], "F_end_LC2_N": r2["F_end_N"],
                          "T_allow_joint_LC2_C": Tj, "note": "A4-70 screws: no temperature knock-down tabulated (engmat) - head end runs cool; verify in LC5"}
    trade = []
    for n, d in [(8, 0.005), (10, 0.005), (12, 0.005), (8, 0.006), (12, 0.006)]:
        r = closure_bolts(LC["LC2"]["chamber_Pa"], v("case_bore_seal"), n, d, "SS-A4-70", (v("case_OD") - v("case_bore_seal")) / 2, v("case_OD"),
                          AL, AL, max(2.4 * d, 0.012), 0.0060, 20, sfy, sfu, f"{n}xM{d*1e3:.0f}")
        trade.append({"n": n, "M": d * 1e3, "min_MS_LC2_20C": round(min(min(x["MS_y"], x["MS_u"]) for x in r["rows"]), 3)})
    SEC["fwd_closure"]["trade_LC2"] = trade

    # ---- 3) aft closure: M63x1.5 x 14 thread (6061 on 6061) ---------------------------------------------------
    aft = []
    for (cid, Pp, sy, su) in PC:
        F = Pp * math.pi / 4 * v("case_aft_land_d") ** 2
        r = thread_strip(F, 0.063, 0.0015, v("aft_thread_len"), AL, AL, 20, sy, su or 1.0, f"Aft closure M63x1.5 x 14 [{cid} {Pp/1e5:.1f} bar]",
                         Td2=0.132e-3, TD2=0.174e-3, TD1=0.300e-3)
        for rr in r["rows"]:
            if su is None:
                rr["MS_u"], rr["SF_u"] = None, None
            tag_T(rr, rr["applied"] * 1e6 / 0.577, AL, sy, None)      # shear yield 0.577 Fty -> equivalent tensile for T_allow
        aft += r["rows"]
    SEC["aft_thread"] = {"rows": aft}

    # ---- 4) retaining lip (nozzle retention): annular plate b = lip ID/2, a = insert bore radius, t = lip t -----
    r_bore = v("insert_OD") / 2 + v("insert_sleeve_t")
    b_lip, t_lip = v("lip_bore_d") / 2, v("aft_lip_t")
    r_g0, r_g1 = v("insert_spigot_d") / 2 + 0.0003, r_bore - 0.0001          # Grafoil ring on the lip
    r_t = S["rt"] * 1e-3
    E_al, nu_al = prop(AL, "E", 20), 0.33
    lip = []
    lip_cases = [("LC2", LC["LC2"]["chamber_Pa"], math.pi * (r_bore ** 2 - r_t ** 2), sfy, sfu, "firing: P x pi (r_bore^2 - r_t^2), divergent relief ignored"),
                 ("LC4", LC["LC4"]["chamber_Pa"], math.pi * r_bore ** 2, 1.0, None, "proof with a solid dummy insert: P x pi r_bore^2"),
                 ("BN", LC["BN"]["chamber_Pa"], math.pi * r_bore ** 2, 1.0, None, "throat blocked: P x pi r_bore^2")]
    for (cid, Pp, A, sy, su, how) in lip_cases:
        F = Pp * A
        q = F / (math.pi * (r_g1 ** 2 - r_g0 ** 2))
        up = annular_plate(r_bore, b_lip, t_lip, E_al, nu_al, ("band", q, r_g0, r_g1))
        lo = annular_plate(r_bore, b_lip, t_lip, E_al, nu_al, ("ring", F, r_bore - 0.0015))
        rr = row(f"Aft lip t {t_lip*1e3:.1f} [{cid} {Pp/1e5:.1f} bar] UPPER bound: uniform gasket pressure, bending at r {up['at_r_mm']:.1f}",
                 up["sigma_bend_Pa"], prop(AL, "Fty"), prop(AL, "Ftu"), sy, su,
                 note=f"F {F:.0f} N ({how}); Kirchhoff plate a {r_bore*1e3:.0f} clamped, b {b_lip*1e3:.0f} free; t/span {t_lip/(r_bore-b_lip):.2f} (thick: FEA governs)")
        lip.append(tag_T(rr, up["sigma_bend_Pa"], AL, sy, su))
        tau = 1.5 * lo["tau_mean_outer_Pa"]
        rr = row(f"Aft lip t {t_lip*1e3:.1f} [{cid} {Pp/1e5:.1f} bar] LOWER bound: rigid insert, load at the lip root: peak shear",
                 tau, 0.577 * prop(AL, "Fty"), 0.60 * prop(AL, "Ftu"), sy, su, note="1.5 x mean shear F/(2 pi a t)")
        lip.append(tag_T(rr, tau / 0.577, AL, sy, None))
    for rr in lip:
        if rr["SF_u"] is None:
            rr["MS_u"] = None
    SEC["aft_lip"] = {"rows": lip, "r_bore_mm": r_bore * 1e3, "lip_ID_mm": 2 * b_lip * 1e3, "t_mm": t_lip * 1e3,
                      "v1_geometry_for_record": "4 mm lip, 22 mm ID under the insert bottom face: BN upper bound 153 MPa (T_allow 168 C), edge in the plume -> replaced (v3.1)"}
    lip_trade = []
    for t_try in (0.004, 0.005, 0.006, 0.008):
        res = {"t_mm": t_try * 1e3}
        for cid, Pp, A in (("BN", LC["BN"]["chamber_Pa"], math.pi * r_bore ** 2), ("LC2", LC["LC2"]["chamber_Pa"], math.pi * (r_bore ** 2 - r_t ** 2))):
            q = Pp * A / (math.pi * (r_g1 ** 2 - r_g0 ** 2))
            sg = annular_plate(r_bore, b_lip, t_try, E_al, nu_al, ("band", q, r_g0, r_g1))["sigma_bend_Pa"]
            res[f"{cid}_sigma_upper_MPa"] = round(sg / 1e6, 1)
            res[f"T_allow_{cid}_C"] = T_allow(sg, AL, 1.0, None) if cid == "BN" else T_allow(sg, AL, sfy, sfu)
        lip_trade.append(res)
    SEC["aft_lip"]["thickness_trade"] = lip_trade

    # ---- 5) graphite insert --------------------------------------------------------------------------------
    gi = []
    r_io = v("insert_OD") / 2
    zi = S["insert_top"]
    rz = sorted(S["contour"], key=lambda q: q[0])
    r_top = float(np.interp(zi, [z for z, _ in rz], [r for _, r in rz])) * 1e-3
    for (cid, Pp, sy, su) in PC:
        su_g = su or 1.0
        for nm, rin in (("insert top edge (bore r %.1f)" % (r_top * 1e3), r_top), ("throat section", r_t)):
            sh_b, _ = lame(Pp, 0.0, rin, r_io, rin)            # bound: OD gap not pressurised
            sh_e, sr_e = lame(Pp, Pp, rin, r_io, rin)          # design: sleeve gap at chamber pressure (vent grooves)
            gi.append(row(f"Graphite {nm} [{cid} {Pp/1e5:.1f} bar] DESIGN (vented OD gap): |compressive| hoop", abs(sh_e), None,
                          prop("GRAPHITE-ISO", "Sc"), None, su_g, note="4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P"))
            rb = row(f"Graphite {nm} [{cid} {Pp/1e5:.1f} bar] BOUND (OD gap not pressurised): hoop tension", sh_b, None, prop("GRAPHITE-ISO", "St"), None, su_g,
                     note="not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5)")
            rb["bound"] = True
            gi.append(rb)
        F = Pp * math.pi * r_bore ** 2
        A = math.pi * (r_io ** 2 - r_g0 ** 2)
        gi.append(row(f"Graphite shoulder bearing on the Grafoil ring [{cid} {Pp/1e5:.1f} bar]", F / A, None, prop("GRAPHITE-ISO", "Sc"), None, su_g,
                      note=f"F {F:.0f} N (upper bound P pi r_bore^2) on {A*1e6:.0f} mm2 (sleeve share neglected)"))
    SEC["graphite_insert"] = {"rows": gi, "r_top_mm": r_top * 1e3, "r_throat_mm": r_t * 1e3, "r_OD_mm": r_io * 1e3}

    # ---- 6) liner (phenolic) -------------------------------------------------------------------------------
    E_ph, t_l = prop("PHENOLIC", "E", 20), v("liner_t")
    Dm = v("liner_OD") - t_l
    p_cr = 2 * E_ph / (1 - 0.3 ** 2) * (t_l / Dm) ** 3
    p_cr_hot = 2 * prop("PHENOLIC", "E", 150) / (1 - 0.3 ** 2) * (t_l / Dm) ** 3
    SEC["liner"] = {"p_collapse_unsupported_Pa": p_cr, "p_collapse_unsupported_150C_Pa": p_cr_hot,
                    "rows": [row(f"Liner hoop, gap pressurised [{cid} {Pp/1e5:.1f} bar] (balanced)", 1.0, None, prop("PHENOLIC", "St"), None, su or 1.0,
                                 note="pressure on both faces: net hoop ~0; collapse only from a transient gap over-pressure (see note)") for (cid, Pp, sy, su) in PC[1:2]],
                    "note": (f"Unsupported long-tube collapse [R5] {p_cr/1e5:.1f} bar (E 7 GPa ASSUMED), {p_cr_hot/1e5:.1f} bar at 150 C: far below MEOP. "
                             "The liner relies on (i) the grain web supporting it and (ii) the case gap venting to the chamber at both liner ends "
                             "(no seals on the liner). A trapped-gap over-pressure at shutdown (chamber tau ~3 ms) is a credible collapse mode near "
                             "burnout when the web is thin; mitigation: 2 axial vent grooves 1 x 0.3 mm on the liner OD (CAD v3.1 note) and inspection "
                             "after every firing. Not resolvable by the static FEA.")}

    # ---- 7) O-ring glands ----------------------------------------------------------------------------------
    Pg = LC["LC4"]["chamber_Pa"]
    r226 = as568_2xx(226)
    gl = [oring_gland(f"Fwd closure piston glands 2x {r226['dash']} FKM 75A at proof {Pg/1e5:.1f} bar (alternative, marginal gap)", v("case_bore_seal"), (0, 46e-6), 0.05165, (-50e-6, 0),
                      r226["W"], r226["W_tol"], r226["ID"], r226["ID_tol"], 4.85e-3, 0.05720, (-60e-6, -30e-6), Pg, 75),
          oring_gland(f"Fwd closure piston glands 2x {r226['dash']} FKM 90A at proof {Pg/1e5:.1f} bar (v3.1 design)", v("case_bore_seal"), (0, 46e-6), 0.05165, (-50e-6, 0),
                      r226["W"], r226["W_tol"], r226["ID"], r226["ID_tol"], 4.85e-3, 0.05720, (-60e-6, -30e-6), Pg, 90)]
    for dash in (229, 233):
        ring = as568_2xx(dash)
        for gd in (0.0667, 0.0665):
            gl.append(rod_gland(f"Aft closure rod gland {ring['dash']} FKM 75A, groove {gd*1e3:.1f} H9, on the 61.0 f7 land at proof {Pg/1e5:.1f} bar"
                                + (" (v3.0 CAD label: error)" if dash == 233 else (" (v3.0 groove)" if gd > 0.0666 else " (v3.1 design)")),
                                v("case_aft_land_d"), (-60e-6, -30e-6), v("case_aft_land_d"), (0, 46e-6), gd, (0, 74e-6), ring, 4.85e-3, Pg, 75))
    gl.append(oring_gland("Tank bulkheads (AS568-238 FKM 90A) at proof", v("tank_bore_seal"), (0, 54e-6), 0.08975, (-50e-6, 0),
                          0.139 * INCH, (-0.004 * INCH, 0.004 * INCH), 3.484 * INCH, (-0.025 * INCH, 0.025 * INCH), 4.85e-3,
                          0.09530, (-60e-6, -30e-6), v("MEOP_tank") * v("proof_factor"), 90))
    SEC["glands"] = gl

    # ---- 8) tank (unchanged pressures, MEOP_tank) ------------------------------------------------------------
    proof = v("proof_factor")
    SEC["tank"] = [cylinder(v("MEOP_tank"), v("tank_OD"), v("tank_t"), AL, 35, sfy, sfu, "Tank tube MEOP 35C"),
                   cylinder(v("MEOP_tank"), v("tank_OD"), (v("tank_OD") - v("tank_bore_seal")) / 2, AL, 35, sfy, sfu, "Tank seal land MEOP 35C"),
                   cylinder(v("MEOP_tank") * proof, v("tank_OD"), (v("tank_OD") - v("tank_bore_seal")) / 2, AL, 20, 1.0, 1.0, "Tank seal land at proof (no yield)")]

    def tank_bolts(T, mat="STEEL-12.9", n=None, d=None, Pp=None, sy=sfy, su=sfu, lab=None):
        n = n or v("n_bolts_tank"); d = d or v("bolt_d_tank"); Pp = Pp or v("MEOP_tank")
        return closure_bolts(Pp, v("tank_bore_seal"), n, d, mat, (v("tank_OD") - v("tank_bore_seal")) / 2, v("tank_OD"),
                             AL, AL, 0.012, 0.009, T, sy, su, lab or f"Tank bulkhead screws {mat} {T:.0f}C", rows_n=2)
    SEC["tank_bolts"] = [tank_bolts(35), tank_bolts(20, Pp=v("MEOP_tank") * proof, sy=1.0, su=1.0, lab="Tank bulkhead screws at proof (no yield)")]
    SEC["tank_bulkhead_plate"] = [circular_plate("Tank bulkhead", v("MEOP_tank"), v("tank_bore_seal") / 2, v("bulkhead_t"), AL, 35, sfy, sfu),
                                  circular_plate("Tank bulkhead at proof", v("MEOP_tank") * proof, v("tank_bore_seal") / 2, v("bulkhead_t"), AL, 20, 1.0, 1.0)]

    # ---------------- collect / write ----------------------------------------------------------------------
    allrows = []
    for k, sec in SEC.items():
        if isinstance(sec, list):
            for s_ in sec:
                if isinstance(s_, dict) and "rows" in s_:
                    allrows += s_["rows"]
                elif isinstance(s_, dict) and "check" in s_:
                    allrows.append(s_)
        elif isinstance(sec, dict) and "rows" in sec:
            allrows += sec["rows"]
    out["summary_rows"] = allrows
    ms_all = [x for r_ in allrows for x in (r_["MS_y"], r_["MS_u"]) if x is not None]
    out["failing_rows"] = [r_["check"] for r_ in allrows if not r_.get("bound") and any(x is not None and x < 0 for x in (r_["MS_y"], r_["MS_u"]))]
    out["bound_rows_below_zero"] = [r_["check"] for r_ in allrows if r_.get("bound") and any(x is not None and x < 0 for x in (r_["MS_y"], r_["MS_u"]))]
    ms_all = [x for r_ in allrows if not r_.get("bound") for x in (r_["MS_y"], r_["MS_u"]) if x is not None]
    out["min_MS"] = min(ms_all)
    out["failing_glands"] = [g["label"] for g in SEC["glands"] if not g["pass"]]
    (HERE / "hand_calcs_v2.json").write_text(json.dumps(out, indent=1, default=float))
    f = lambda x: "-" if x is None else (f"{x:.3g}" if abs(x) < 1e4 else f"{x:.3e}")
    L = ["# Hand calculations v2 (DERIVED, `calcs/hand_calcs.py`, 2026-10-12)", "",
         "Chamber MEOP **45 bar** (lead decision 2026-10-12, Combustion pintle full-stroke failure case), proof **67.5 bar**, "
         "blocked-nozzle bound **63.1 bar** (no yield at temperature). CAD v3 geometry. v1 (31 bar, CAD v2) kept as `hand_calcs_v1.json`.", "",
         "MS = allowable/(SF x applied) - 1. Allowables from `04-fea/src/engmat.py` (spec minimums; temperature knock-down via T_allow). "
         "LC4/BN rows: SF 1.0 on yield (no yield); '-' = not applicable. **T_allow** = highest part temperature at which the row keeps MS >= 0; "
         "the LC5 thermal FEA must show the part below it.", "",
         "| Check | Applied | Allow. yield | Allow. ult | SF y/u | MS y (20 C) | MS u (20 C) | T_allow C | Note |", "|---|---|---|---|---|---|---|---|---|"]
    for r_ in allrows:
        L.append(f"| {r_['check']} | {f(r_['applied'])} {r_['unit']} | {f(r_['allow_yield'])} | {f(r_['allow_ult'])} | {r_['SF_y']}/{r_['SF_u']} | "
                 f"{f(r_['MS_y'])} | {f(r_['MS_u'])} | {f(r_.get('T_allow_C'))} | {r_.get('note','')} |")
    L += ["", "## Forward-closure screw trade at LC2 (20 C, min MS)", "", ", ".join(f"{t['n']}xM{t['M']:.0f}: {t['min_MS_LC2_20C']:.2f}" for t in SEC["fwd_closure"]["trade_LC2"]),
          "", f"Forward-closure joint (Al rows) keeps MS >= 0 at LC2 up to **{SEC['fwd_closure']['T_allow_joint_LC2_C']} C**.", "",
          "## Retaining-lip thickness trade (BN 63.1 bar, upper bound = uniform gasket pressure)", "",
          "| t mm | BN sigma MPa | T_allow BN C | LC2 sigma MPa |", "|---|---|---|---|"]
    L += [f"| {t['t_mm']:.0f} | {t['BN_sigma_upper_MPa']} | {t['T_allow_BN_C']} | {t['LC2_sigma_upper_MPa']} |" for t in SEC["aft_lip"]["thickness_trade"]]
    L += ["", "## Liner", "", SEC["liner"]["note"], "", "## O-ring glands [R2]", ""]
    for g in SEC["glands"]:
        L.append(f"- {g['label']}: depth {g['gland_depth_mm'][0]:.3f}-{g['gland_depth_mm'][1]:.3f} mm, squeeze {g['squeeze_pct'][0]:.1f}-{g['squeeze_pct'][1]:.1f} %, "
                 f"stretch {g['stretch_pct'][0]:.1f}-{g['stretch_pct'][1]:.1f} %, fill max {g['fill_max_pct']:.0f} %, gap {g['diametral_gap_max_mm']:.3f} mm "
                 f"(limit {g['extrusion_gap_limit_mm']:.2f}) -> **{'PASS' if g['pass'] else 'FAIL'}**")
    vf = out["verification"]["annular_plate_vs_clamped_solid"]
    L += ["", "## Verification", "", f"Annular-plate integrator vs clamped solid plate: M_r(a) {vf['Mr_outer_numeric']:.2f} vs exact {vf['Mr_outer_exact']:.2f} N m/m "
          f"(rel. error {vf['rel_err_outer']:.1e}); small-hole edge M_t {vf['Mt_small_hole_numeric']:.2f} vs 2 x solid centre {vf['Mt_small_hole_exact']:.2f}.", "",
          f"Minimum MS over all rows (20 C): **{out['min_MS']:.2f}**", "", "Failing rows: " + ("; ".join(out["failing_rows"]) or "none"),
          "", "Bound rows below zero (not design conditions, listed for transparency): " + ("; ".join(out["bound_rows_below_zero"]) or "none"),
          "", "Failing glands: " + ("; ".join(out["failing_glands"]) or "none")]
    (HERE / "HAND-CALCS.md").write_text("\n".join(L) + "\n")
    return out


if __name__ == "__main__":
    o = main()
    for r in o["summary_rows"]:
        print(f"{r['check'][:96]:96s} {r['applied']:8.2f} MSy={'-' if r['MS_y'] is None else round(r['MS_y'],2)} MSu={'-' if r['MS_u'] is None else round(r['MS_u'],2)} Ta={r.get('T_allow_C')}")
    print("verify", o["verification"])
    print("fwd trade", o["sections"]["fwd_closure"]["trade_LC2"], "Tj", o["sections"]["fwd_closure"]["T_allow_joint_LC2_C"])
    print("lip trade", o["sections"]["aft_lip"]["thickness_trade"])
    for g in o["sections"]["glands"]:
        print(g["label"], [round(x,1) for x in g["squeeze_pct"]], [round(x,1) for x in g["stretch_pct"]], round(g["fill_max_pct"]), round(g["diametral_gap_max_mm"],3), g["extrusion_gap_limit_mm"], g["pass"])
    print("min MS", o["min_MS"]); print("FAIL", o["failing_rows"]); print("FAIL glands", o["failing_glands"])
