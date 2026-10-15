"""Pintle drive v3.4 - in-line MKS HV69 toggle crank on its own bearings: fit, loads, spring, guide (03-cad/src/calcs, v2, 2026-10-12, Mechanical).

v2 (2026-10-12): v1 sized the guide friction on the 224 N link force of the needle-spring layout; with the torsion spring on the crank
the link carries only pressure + friction, so the link force is now solved self-consistently with the carriage-guide friction
(offset couple F y_l + link-angle side load), the link-pin friction is explicit (replaces the 0.90 crank efficiency), the spring
torque tolerance is +/-10 % (ASSUMED commercial), the seated (closing) pressure force at crack-open is included, and the spring is
chosen per guide option.  v1 outputs stay in pintle_inline_v34_v1.json as history.

Lead decision 2026-10-12 (CHANGELOG): provisional baseline MKS HV69 in-line, toggle crank r 3.0 mm closed 15 deg from TDC, 28 mm
link, ~99 deg travel; crank on its own outboard bearings with a torque-only coupling to the 6 mm 25T spline (no link side load on
the servo output bearing); size bearings and stop for 378 N (servo stall into the 4.2 mm open stop, Electronics); keep the torsion
spring for spring-to-close and preload; swept radius <= 67 mm with the HV69 envelope 29 x 13 x 28.7; report the forward zone extent.

What this script answers (numbers tagged; nothing here is a test result):
 1. FIT: the HV69 case (28.7 mm along the shaft) must be coaxial with the crank; the crank's link plane must sit over the needle.
    For each stack option the minimum link-plane offset y_l from the needle axis that keeps every point inside the 8 deg
    swept cone r cos 8 + z sin 8 <= 67 mm is computed (ANALYTIC on box envelopes; the CAD check in try_v34 confirms).
 2. LOADS on the link, pins, bearings, stop (378 N basis per the lead + a crank-side stop).
 3. SPRING: a torsion spring on the crankshaft can only close the needle through a push-pull link, so Electronics' lost motion
    (tension-only slot at the needle) moves into the coupling backlash; the spring torque law T(phi) >= F_req * dx/dphi is sized here.
 4. GUIDE: the link-plane offset y_l puts a couple F * y_l on the needle carriage; sliding vs rolling guidance friction.
 5. TORQUE DEMAND (preliminary, for Electronics to re-run with their force map): spring + friction at the stop on the bench.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SIN8, COS8 = math.sin(math.radians(8.0)), math.cos(math.radians(8.0))
R_SWEEP = 67.0                                  # mm: 70 mm bay radius - 3 mm moving clearance (ICD; CAD sweep check)

# ---------------------------------------------------------------------------------------------- inputs (tagged)
HV69 = {"L": 29.0, "W": 13.0, "H": 28.7, "mass_kg": 0.021,
        "stall_Nm": {"4.8": 0.59, "6.0": 0.74, "7.4": 0.90, "8.2": 1.00},
        "tag": "Electronics msg 2026-10-12 (retailer copies of MKS data, TO-CONFIRM with MKS; ear pattern unpublished)"}
ASSUMED_GEOM = {"spline_protrusion_mm": 4.0, "shaft_from_case_end_mm": 7.25,
                "tag": "ASSUMED (MKS drawing not available): spline face 4.0 mm beyond the case face, shaft axis 7.25 mm (L/4) from one "
                       "case end along L - VERIFY on the MKS drawing / B-PNT-1 sample"}
CRANK = {"r": 3.0, "L": 28.0, "phi_closed": 15.0, "phi_cmd_closed": 10.0, "x_stop": 4.2, "tag": "Electronics pintle_mini_servo_v1 / lead 2026-10-12"}
NEEDLE = {"F_open_max_N": 86.7, "F_close_max_N": 77.2, "seal_friction_N": 25.0, "margin_N": 10.0,
          "tag": "combustion.json v1 force envelope [-86.7, +77.2] N (+ closing) at tank MEOP 7.0 MPa; seal friction 25 N ASSUMED upper bound"}
LOADS = {"link_operating_N": 224.0, "link_stall_N": 378.0, "tag": "Electronics msg 2026-10-12 (crack at MEOP / HV69 stall 1.00 N m at 8.2 V into the stop)"}
STATIONS = {"z_k0": 215.59, "bonnet_top": 210.59, "head_top": 178.59,
            "tag": "CAD v3.3 (checks_v33.json): head top, bonnet top; needle-end (carriage) pin closed at z 215.6"}
BEARINGS = {   # d x D x B mm, C0r kN
    # VERIFIED 2026-10-12: NSK catalogue "Thin Section Deep Groove Ball Bearings" e1153a.pdf (nsk.com), C0r as printed
    "NB701 (12x18x4)": (12, 18, 4, 0.655), "NB700 (10x15x3)": (10, 15, 3, 0.515), "6800 (10x19x5)": (10, 19, 5, 0.840),
    "6801 (12x21x5)": (12, 21, 5, 1.040),
    # NOT VERIFIED (v1 'as recalled' values; the 6700/6701 C0 0.98/1.03 kN could not be confirmed and are NOT used)
    "694-2Z": (4, 11, 4, 0.39), "695-2Z": (5, 13, 4, 0.43)}
BEARING_SOURCE = "NSK e1153a (https://www.nsk.com/content/dam/nsk/common/catalogs/ctrgPdf/bearings/e1153a.pdf), read 2026-10-12"
# v2 friction / pressure / tolerance inputs
GUIDE_OPTIONS = {   # carriage guidance reacting the link-plane offset couple F y_l and the link-angle side load F tan(psi)
    "PTFE_8mm_v33": {"mu": 0.10, "s_mm": 8.0, "tag": "v3.3 carriage: 2 pins, PTFE-glass bushings 8 mm long; mu 0.10 ASSUMED (PTFE/steel dry, low speed)"},
    "PTFE_15mm": {"mu": 0.10, "s_mm": 15.0, "tag": "v3.4 envelope: 2 fixed pins, 2 PTFE-lined bushings per pin 15 mm apart (carriage 211.1..230.8 between the bonnet top 210.6 "
                                                  "and the crank housing 235.5 less the 4.2 mm stroke); mu 0.10 ASSUMED"},
    "PTFE_15mm_mu0.20": {"mu": 0.20, "s_mm": 15.0, "tag": "sensitivity: dry polymer bushing upper value ASSUMED"},
    "PTFE_18mm": {"mu": 0.10, "s_mm": 18.0, "tag": "2 pins, 2 PTFE-lined bushings per pin 18 mm apart (needs the crank axis 3 mm higher, zone +3 mm); mu 0.10 ASSUMED"},
    "PTFE_18mm_mu0.20": {"mu": 0.20, "s_mm": 18.0, "tag": "sensitivity: dry polymer bushing upper value ASSUMED"},
    "rolling_18mm": {"mu": 0.005, "s_mm": 18.0, "tag": "miniature cam-follower rollers (4x) on a hardened track, preloaded; effective mu 0.005 ASSUMED"},
}
PIN = {"mu": 0.15, "r_mm": 1.5, "tag": "3 mm link pins (17-4PH, dry-film lubricated), mu 0.15 ASSUMED; replaces Electronics' crank efficiency 0.90"}
SPRING_TOL = 0.10            # +/- fraction on spring torque (ASSUMED commercial torsion-spring tolerance; vendor to confirm)
P_AMB = 101325.0
STEM_D, SEAT_D, BLEND = 4.0, 5.5, 0.10   # mm: stem through the seal (Mechanical), seat (combustion.json), seated->open force blend (Electronics model)
PRESSURES = {"bench": P_AMB, "P3.5MPa": 3.5e6, "P5.5MPa": 5.5e6, "MEOP": 7.0e6}
OMEGA0_DPS = {"7.4": 60.0 / 0.11, "6.6": 60.0 / 0.123}   # HV69 no-load speed (Electronics: 0.11 s/60 deg at 7.4 V; 6.6 V interpolated 6.0-7.4 V)


def s_of(phi_deg, r=None, L=None):
    r = CRANK["r"] if r is None else r                      # read at call time (v2: crank-radius study)
    L = CRANK["L"] if L is None else L
    p = math.radians(phi_deg)
    return r * math.cos(p) + math.sqrt(L * L - (r * math.sin(p)) ** 2)


def lift(phi_deg):
    return s_of(CRANK["phi_closed"]) - s_of(phi_deg)


def dxdphi(phi_deg, h=1e-4):
    return (lift(phi_deg + h) - lift(phi_deg - h)) / math.radians(2 * h)      # mm/rad


def phi_at_lift(x):
    lo, hi = CRANK["phi_closed"], 179.0
    for _ in range(80):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if lift(m) < x else (lo, m)
    return 0.5 * (lo + hi)


def r_allow(z):
    return (R_SWEEP - abs(z) * SIN8) / COS8


def swept_ok(pts):
    return max(math.hypot(p[0], p[1]) * COS8 + abs(p[2]) * SIN8 for p in pts)


def box_pts(x0, x1, y0, y1, z0, z1):
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def fit(stack, z_c, case_down=True):
    """Minimum and maximum link-plane offset y_l (servo on -Y, crank housing on +Y) inside the swept cone.
    stack: servo_side = distance link plane -> servo case face; crank_side = link plane -> housing outer face;
    housing_half = half size of the crank housing in X and Z."""
    a = ASSUMED_GEOM["shaft_from_case_end_mm"]
    zc0, zc1 = (z_c - (HV69["L"] - a), z_c + a) if case_down else (z_c - a, z_c + (HV69["L"] - a))
    res = {}
    ys = np.arange(0.0, 40.0, 0.05)
    ok = []
    for yl in ys:
        y_face = yl - stack["servo_side"]
        case = box_pts(-HV69["W"] / 2, HV69["W"] / 2, y_face - HV69["H"], y_face, zc0, zc1)
        hh = stack["housing_half"]
        hous = box_pts(-hh, hh, yl - stack["servo_side"] + 1.0, yl + stack["crank_side"], z_c - hh, z_c + hh)
        ok.append(swept_ok(case) <= R_SWEEP and swept_ok(hous) <= R_SWEEP)
    ok = np.array(ok)
    if ok.any():
        res = {"y_l_min_mm": float(ys[ok].min()), "y_l_max_mm": float(ys[ok].max())}
    else:
        res = {"y_l_min_mm": None, "y_l_max_mm": None}
    res["case_z_mm"] = [zc0, zc1]
    return res


def spring_law(F_req, phis):
    """Linear torsion spring T = T0 + k (phi - phi_closed) >= F_req * dx/dphi on [phi_closed, phi_stop]; scan T0, minimum k for
    each, report the trade between the seat load (T0 / dxdphi at closed) and the servo-side maximum T(phi_stop)."""
    req = np.array([F_req * dxdphi(p) * 1e-3 for p in phis])        # N m
    dphi = np.radians(np.array(phis) - CRANK["phi_closed"])
    out = []
    for T0 in np.arange(0.10, 0.40, 0.02):
        with np.errstate(divide="ignore", invalid="ignore"):
            kreq = np.where(dphi > 1e-9, (req - T0) / dphi, -np.inf)
        if T0 < req[0] - 1e-12:
            continue
        k = max(0.0, float(np.max(kreq)))
        Tmax = T0 + k * dphi[-1]
        out.append({"T0_Nm": round(float(T0), 3), "k_Nm_per_rad": round(k, 4), "T_stop_Nm": round(float(Tmax), 3),
                    "seat_load_N": round(float(T0 / (dxdphi(CRANK['phi_closed']) * 1e-3)), 1)})
    return req, out


def spring_assist_design(phis, T_open_max, F_req, seat_max=None):
    """Lead 2026-10-12 (2nd update): the torsion spring must ASSIST CLOSING as well as preload, with the opening stall/peak
    margin >= 1.5.  Linear law T = T0 + k (phi - 15 deg).  Constraints: bench opening demand T + f dx/dphi <= T_open_max (all phi);
    T >= F_req dx/dphi (closes against the max opening pressure + friction + 10 N).  Objective: the worst-case closing assist
    min(T - (F_open_max + f) dx/dphi).  Returns the Pareto table over T0 (seat load rises with T0)."""
    f = NEEDLE["seal_friction_N"]
    Fo = NEEDLE["F_open_max_N"] + f
    dphi = np.radians(np.array(phis) - CRANK["phi_closed"])
    dx = np.array([dxdphi(p) * 1e-3 for p in phis])
    rows = []
    for T0 in np.arange(0.10, 0.50, 0.01):
        best = None
        for k in np.arange(0.0, 0.60, 0.0025):
            T = T0 + k * dphi
            if np.any(T + f * dx > T_open_max + 1e-12) or np.any(T < F_req * dx - 1e-12):
                continue
            a = float(np.min(T - Fo * dx))
            if best is None or a > best[1]:
                best = (k, a, float(np.max(T + f * dx)), float(T[-1]))
        if best:
            rows.append({"T0_Nm": round(float(T0), 3), "k_Nm_per_rad": round(best[0], 4), "T_stop_Nm": round(best[3], 3),
                         "assist_worst_Nm": round(best[1], 3), "bench_open_demand_Nm": round(best[2], 3),
                         "seat_load_N": round(float(T0 / dx[0]), 1)})
    return rows


def F_po(x_mm, P):
    """Pressure force on the needle, + = OPENING (N).  Seated: dp (A_seat - A_stem) closing; lifted (> 0.1 mm): dp A_stem opening;
    linear blend over the first 0.1 mm (Electronics pintle_mini_servo_v1 model, combustion.json v1 envelope -86.7/+77.2 N at MEOP)."""
    dp = max(0.0, P - P_AMB) * 1e-6
    a_st, a_se = math.pi / 4 * STEM_D ** 2, math.pi / 4 * SEAT_D ** 2
    w = min(1.0, max(0.0, x_mm / BLEND))
    return -(1 - w) * dp * (a_se - a_st) + w * dp * a_st


def g_of(phi_deg, y_mm, s_mm):
    """Guide normal force per N of link force: offset couple on two pins (2 y / s) + link-angle side load tan(psi)."""
    psi = math.asin(CRANK["r"] * math.sin(math.radians(phi_deg)) / CRANK["L"])
    return 2.0 * y_mm / s_mm + abs(math.tan(psi))


def link_force(phi_deg, P, closing, guide, y_mm, f_seal):
    """Link force F (N, + = compression pushing the needle closed), quasi-static, needle moving (closing or opening).
    Needle: F = F_po + (f_seal + mu_g |F| g) sgn(u), u = closing velocity."""
    x = lift(phi_deg)
    fp = F_po(x, P)
    mg = guide["mu"] * g_of(phi_deg, y_mm, guide["s_mm"])
    if closing:
        num = fp + f_seal
        return num / (1 - mg) if num > 0 else num / (1 + mg)
    num = fp - f_seal
    return num / (1 - mg) if num < 0 else num / (1 + mg)


def pin_loss_factor(phi_deg):
    """|relative rotation| at the two link pins per unit crank rotation: crank pin |1 - dpsi/dphi| + needle pin |dpsi/dphi|."""
    p = math.radians(phi_deg)
    psi = math.asin(CRANK["r"] * math.sin(p) / CRANK["L"])
    a = CRANK["r"] * math.cos(p) / (CRANK["L"] * math.cos(psi))
    return abs(1 - a) + abs(a)


def servo_torque(phi_deg, T_s, P, opening, guide, y_mm, f_seal):
    """Servo torque (N m, + = opening) for a quasi-static move: T_m = T_s - F dx/dphi +/- mu_p |F| r_p (pins oppose motion).
    Opening: required drive.  Closing: T_m is the surplus the spring delivers (assist; the servo dog brakes it); < 0 = no close."""
    F = link_force(phi_deg, P, not opening, guide, y_mm, f_seal)
    dx = dxdphi(phi_deg) * 1e-3
    pl = PIN["mu"] * abs(F) * PIN["r_mm"] * 1e-3 * pin_loss_factor(phi_deg)
    return T_s - F * dx + (pl if opening else -pl), F


def spring_design_v2(phis, guide, y_mm, f_seal, T_open_max):
    """Linear law T = T0 + k (phi - 15 deg), tolerance +/- SPRING_TOL.
    C1 spring close (throttle function; safety shutoff = NC isolation valve): the -10 % spring closes from every lift at tank MEOP.
    C2 opening: +10 % spring, max servo opening torque over bench / crack-open at MEOP / 3.5 / 5.5 MPa <= T_open_max (stall/1.5).
    Objective: worst closing assist at MEOP with the -10 % spring; report the assist at 5.5 / 3.5 MPa (MECO pressures)."""
    dphi = np.radians(np.array(phis) - CRANK["phi_closed"])
    rows = []
    for T0 in np.arange(0.10, 0.60, 0.01):
        for k in np.arange(0.0, 0.40, 0.005):
            T = T0 + k * dphi
            op = max(servo_torque(p, (1 + SPRING_TOL) * t, P, True, guide, y_mm, f_seal)[0] for p, t in zip(phis, T) for P in PRESSURES.values())
            if op > T_open_max + 1e-12:
                continue
            a_meop = min(servo_torque(p, (1 - SPRING_TOL) * t, PRESSURES["MEOP"], False, guide, y_mm, f_seal)[0] for p, t in zip(phis, T))
            if a_meop < 0:
                continue
            a55 = min(servo_torque(p, (1 - SPRING_TOL) * t, PRESSURES["P5.5MPa"], False, guide, y_mm, f_seal)[0] for p, t in zip(phis, T))
            a35 = min(servo_torque(p, (1 - SPRING_TOL) * t, PRESSURES["P3.5MPa"], False, guide, y_mm, f_seal)[0] for p, t in zip(phis, T))
            rows.append({"T0_Nm": round(float(T0), 3), "k_Nm_per_rad": round(float(k), 4), "T_stop_Nm": round(float(T[-1]), 3),
                         "open_demand_max_Nm": round(op, 3), "assist_min_MEOP_Nm": round(a_meop, 3), "assist_min_5p5_Nm": round(a55, 3),
                         "assist_min_3p5_Nm": round(a35, 3), "seat_load_nom_N": round(float(T0 / (dxdphi(CRANK["phi_closed"]) * 1e-3)), 1)})
    return rows


def spiral_spring(T_max_Nm, k_Nm_rad, b=6.0, sigma_allow=1300.0, E=206e3, r_i=4.0, r_o=10.5):
    """Flat spiral (clock) spring, free-spiral approximation: k = E b t^3 / (12 L), sigma = 6 T / (b t^2) (Wahl; no end-clamp factor).
    Strip: hardened spring steel (1.4310 / C75S class, Rm ~1800 MPa AS RECALLED) -> static allowable 1300 MPa ASSUMED."""
    t = math.ceil(math.sqrt(6 * T_max_Nm * 1e3 / (b * sigma_allow)) * 20) / 20.0
    L = E * b * t ** 3 / (12 * k_Nm_rad * 1e3)
    n = L / (math.pi * (r_i + r_o))
    pitch = (r_o - r_i) / n
    return {"type": "flat spiral spring in the crank housing, outboard of the crank web (inner end on the crank shaft, outer end in the housing)",
            "strip_b_mm": b, "strip_t_mm": t, "strip_length_mm": round(L, 1), "r_inner_mm": r_i, "r_outer_mm": r_o, "turns": round(n, 2),
            "pitch_mm": round(pitch, 2), "gap_free_mm": round(pitch - t, 2), "windup_at_stop_turns": None,
            "sigma_max_MPa": round(6 * T_max_Nm * 1e3 / (b * t * t), 0), "sigma_allow_MPa": sigma_allow, "mass_g": round(b * t * L * 7.85e-3, 1),
            "tag": "DERIVED (free-spiral formulas); spring maker to design/confirm (rate, preload set, end clamps, fatigue for the throttle-cycle count)"}


CONFIGS = {   # stem / seal friction / guide / link pins
    "S4_PTFE18_plainpins": {"stem_d": 4.0, "f_seal": 25.0, "guide": "PTFE_18mm", "pin_mu": 0.15},
    "S4_rolling_ballpins": {"stem_d": 4.0, "f_seal": 25.0, "guide": "rolling_18mm", "pin_mu": 0.005},
    "S3_PTFE18_plainpins": {"stem_d": 3.0, "f_seal": 18.75, "guide": "PTFE_18mm", "pin_mu": 0.15},
    "S3_PTFE15_plainpins": {"stem_d": 3.0, "f_seal": 18.75, "guide": "PTFE_15mm", "pin_mu": 0.15},
    "S3_PTFE15mu20_plainpins": {"stem_d": 3.0, "f_seal": 18.75, "guide": "PTFE_15mm_mu0.20", "pin_mu": 0.15},
    "S3_PTFE8v33_plainpins": {"stem_d": 3.0, "f_seal": 18.75, "guide": "PTFE_8mm_v33", "pin_mu": 0.15},
}
BASELINE = "S3_PTFE15mu20_plainpins"   # v2.2 (lead 2026-10-12): spring sized for guide mu 0.20 (15 mm spacing); v2.1 used mu 0.10
BASELINE_NOMINAL_GUIDE = "S3_PTFE15_plainpins"
BASELINE_SPRING = {"T0_Nm": 0.30, "k_Nm_per_rad": 0.10, "tolerance": 0.10,
                   "tag": "lead decision 2026-10-12: S3_PTFE15mu20 design (robust to dry-N2O PTFE guide mu 0.20); v2.1 spring 0.19 + 0.17 withdrawn "
                          "(MEOP closing assist 0.050 / 0.028 / 0.000 N m at mu 0.10 / 0.15 / 0.20, Electronics reproduction)"}
JAM_LINK_N_ELECTRONICS = {"7.505": 688.0, "8.4": 789.0}   # Electronics 2026-10-12 via lead: regulator upper tolerance / regulator fail-through
CHOICE_RULE = {"assist_min_MEOP_Nm": 0.05, "assist_min_5p5_Nm": 0.08, "seat_load_nom_N_max": 300.0, "k_min_Nm_per_rad": 0.10,
               "objective": "minimum stored energy 1.1 T_stop^2 / (2 k) (smallest spring) among the rows meeting the targets"}


def set_config(c):
    global STEM_D
    STEM_D = c["stem_d"]
    PIN["mu"] = c["pin_mu"]


def choose(rows):
    ok = [r for r in rows if r["assist_min_MEOP_Nm"] >= CHOICE_RULE["assist_min_MEOP_Nm"] and r["assist_min_5p5_Nm"] >= CHOICE_RULE["assist_min_5p5_Nm"]
          and r["seat_load_nom_N"] <= CHOICE_RULE["seat_load_nom_N_max"] and r["k_Nm_per_rad"] >= CHOICE_RULE["k_min_Nm_per_rad"]]
    for r in rows:
        r["U_plus10_J"] = round(1.1 * r["T_stop_Nm"] ** 2 / (2 * r["k_Nm_per_rad"]), 3) if r["k_Nm_per_rad"] > 0 else None
    if ok:
        return min(ok, key=lambda r: (r["U_plus10_J"], -r["assist_min_5p5_Nm"])), "targets met"
    feas = [r for r in rows if r["k_Nm_per_rad"] >= CHOICE_RULE["k_min_Nm_per_rad"]]
    if feas:
        return max(feas, key=lambda r: (r["assist_min_5p5_Nm"], -r["seat_load_nom_N"])), "targets NOT met: best assist at 5.5 MPa shown"
    return None, "INFEASIBLE: no linear spring meets C1 (fail-safe close at MEOP, -10 % spring) and C2 (opening margin 1.5 at 7.4 V, +10 % spring)"


def main():
    phi_stop = phi_at_lift(CRANK["x_stop"])
    phis = list(np.linspace(CRANK["phi_closed"], phi_stop, 30))
    phis_fine = list(np.linspace(CRANK["phi_closed"], phi_stop, 200))
    law = [{"phi_deg": round(p, 2), "lift_mm": round(lift(p), 4), "dx_dphi_mm_per_rad": round(dxdphi(p), 4)} for p in
           [15, 20, 30, 40, 48.8, 60, 69.9, 80, 89.1, 100, 108.8, phi_stop]]
    T_open_max = HV69["stall_Nm"]["7.4"] / 1.5                       # lead rule: stall / peak >= 1.5 at the regulated 7.4 V rail
    # ---------------- 1. fit
    z_c = STATIONS["z_k0"] + s_of(CRANK["phi_closed"])
    stacks = {
        "A_straddle_external_coupling": {"servo_side": 4.0 + 4.0 + 6.0 + ASSUMED_GEOM["spline_protrusion_mm"], "crank_side": 10.0, "housing_half": 8.0,
                                         "note": "link eye 4 + web 2 / bearing A 4 / Oldham 6 (hub + disc + slot) / spline 4; bearing B 4 + wall 2"},
        "B_straddle_nested_coupling": {"servo_side": 4.0 + 4.0 + 1.0 + ASSUMED_GEOM["spline_protrusion_mm"], "crank_side": 10.0, "housing_half": 11.0,
                                       "note": "one-sided dog coupling nested inside the crank's 12 mm journal tube in bearing A (6701, 12x18x4); bearing B 694"},
        "C_nested_coupling_spiral_spring": {"servo_side": 4.0 + 4.0 + 1.0 + ASSUMED_GEOM["spline_protrusion_mm"], "crank_side": 16.0, "housing_half": 11.0,
                                            "note": "B + flat spiral spring OD 21 x 6 wide inside the crank housing, outboard of the crank web (v3.4 BASELINE)"},
        "D_helical_torsion_outboard": {"servo_side": 4.0 + 4.0 + 1.0 + ASSUMED_GEOM["spline_protrusion_mm"], "crank_side": 21.0, "housing_half": 14.0,
                                       "note": "B + helical torsion spring d 1.6 D 26 (~10 mm body) outboard of bearing B"},
    }
    fits = {}
    for k, st in stacks.items():
        for down in (True, False):
            fits[f"{k}|case_{'down' if down else 'up'}"] = dict(fit(st, z_c, case_down=down), stack=st)
    a = ASSUMED_GEOM["shaft_from_case_end_mm"]
    z_top_C = max(z_c + a, z_c + stacks["C_nested_coupling_spiral_spring"]["housing_half"]) + 1.5     # + bracket cap 1.5 mm
    y_l = fits["C_nested_coupling_spiral_spring|case_down"]["y_l_min_mm"]
    y_use = math.ceil((y_l or 12.0) + 0.5)
    # ---------------- 2. spring + friction per configuration (v2)
    designs = {}
    for name, c in CONFIGS.items():
        set_config(c)
        rows = spring_design_v2(phis, GUIDE_OPTIONS[c["guide"]], y_use, c["f_seal"], T_open_max)
        ch, note = choose(rows)
        designs[name] = {"config": c, "n_feasible": len(rows), "choice": ch, "choice_note": note}
    # ---------------- 3. baseline detail (fine phi grid), loads, jam case, MECO
    c = CONFIGS[BASELINE]
    set_config(c)
    g = GUIDE_OPTIONS[c["guide"]]
    ch = dict(designs[BASELINE]["choice"])
    T0, kk = BASELINE_SPRING["T0_Nm"], BASELINE_SPRING["k_Nm_per_rad"]
    assert abs(ch["T0_Nm"] - T0) < 1e-9 and abs(ch["k_Nm_per_rad"] - kk) < 1e-9, "baseline spring differs from the mu 0.20 design row"
    ch["T_stop_Nm"] = round(T0 + kk * math.radians(phi_stop - CRANK["phi_closed"]), 3)
    Tn = lambda p: T0 + kk * math.radians(p - CRANK["phi_closed"])
    # same spring with the nominal guide (mu 0.10): reference values
    g_nom = GUIDE_OPTIONS[CONFIGS[BASELINE_NOMINAL_GUIDE]["guide"]]
    nominal_guide = {"guide": CONFIGS[BASELINE_NOMINAL_GUIDE]["guide"],
                     "open_demand_bench_Nm": round(max(servo_torque(p, (1 + SPRING_TOL) * Tn(p), PRESSURES["bench"], True, g_nom, y_use, c["f_seal"])[0] for p in phis_fine), 3),
                     "assist_min_Nm": {P_nm: round(min(servo_torque(p, (1 - SPRING_TOL) * Tn(p), P, False, g_nom, y_use, c["f_seal"])[0] for p in phis_fine), 3)
                                       for P_nm, P in PRESSURES.items()}}
    nominal_guide["margin_bench_7V4"] = round(HV69["stall_Nm"]["7.4"] / nominal_guide["open_demand_bench_Nm"], 2)
    mu_scan = {}
    for mu in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
        gg = {"mu": mu, "s_mm": g["s_mm"]}
        mu_scan[f"{mu:.2f}"] = {"assist_min_MEOP_Nm": round(min(servo_torque(p, (1 - SPRING_TOL) * Tn(p), PRESSURES["MEOP"], False, gg, y_use, c["f_seal"])[0] for p in phis_fine), 3),
                                "open_demand_max_Nm": round(max(servo_torque(p, (1 + SPRING_TOL) * Tn(p), P, True, gg, y_use, c["f_seal"])[0] for p in phis_fine for P in PRESSURES.values()), 3)}
        mu_scan[f"{mu:.2f}"]["margin_7V4"] = round(HV69["stall_Nm"]["7.4"] / mu_scan[f"{mu:.2f}"]["open_demand_max_Nm"], 2)
    prof = []
    for p in phis_fine[::10] + [phis_fine[-1]]:
        row = {"phi_deg": round(p, 2), "lift_mm": round(lift(p), 3), "dx_dphi_mm_per_rad": round(dxdphi(p), 3), "T_spring_nom_Nm": round(Tn(p), 3)}
        for P_nm, P in PRESSURES.items():
            to, Fo = servo_torque(p, (1 + SPRING_TOL) * Tn(p), P, True, g, y_use, c["f_seal"])
            tc, Fc = servo_torque(p, (1 - SPRING_TOL) * Tn(p), P, False, g, y_use, c["f_seal"])
            row[f"open_T_{P_nm}_Nm"] = round(to, 3)
            row[f"close_assist_{P_nm}_Nm"] = round(tc, 3)
            row[f"link_F_open_{P_nm}_N"] = round(Fo, 1)
            row[f"link_F_close_{P_nm}_N"] = round(Fc, 1)
        prof.append(row)
    open_bench = max(servo_torque(p, (1 + SPRING_TOL) * Tn(p), PRESSURES["bench"], True, g, y_use, c["f_seal"])[0] for p in phis_fine)
    open_flight = max(servo_torque(p, (1 + SPRING_TOL) * Tn(p), P, True, g, y_use, c["f_seal"])[0] for p in phis_fine
                      for P in (PRESSURES["P3.5MPa"], PRESSURES["P5.5MPa"], PRESSURES["MEOP"]))
    assist = {P_nm: min(servo_torque(p, (1 - SPRING_TOL) * Tn(p), P, False, g, y_use, c["f_seal"])[0] for p in phis_fine) for P_nm, P in PRESSURES.items()}
    Fl_max = max(abs(link_force(p, P, cl, g, y_use, c["f_seal"])) for p in phis_fine for P in PRESSURES.values() for cl in (True, False))
    seat = {"nominal_N": round(T0 / (dxdphi(CRANK["phi_closed"]) * 1e-3), 1),
            "plus10_N": round(1.1 * T0 / (dxdphi(CRANK["phi_closed"]) * 1e-3), 1),
            "plus10_plus_MEOP_seated_pressure_N": round(1.1 * T0 / (dxdphi(CRANK["phi_closed"]) * 1e-3) - F_po(0.0, PRESSURES["MEOP"]), 1)}
    # jam at the seat (needle stuck closed), servo stall opening, -10 % spring: link tension
    dx0 = dxdphi(CRANK["phi_closed"]) * 1e-3
    jam = {}
    for V in ("7.4", "8.2"):
        Fj = (HV69["stall_Nm"][V] - 0.9 * T0) / (dx0 + PIN["mu"] * PIN["r_mm"] * 1e-3 * pin_loss_factor(CRANK["phi_closed"]))
        jam[V] = round(Fj, 1)
    pin_d = 3.0
    F_link_design = max(LOADS["link_stall_N"], jam["8.2"])
    link = {"max_link_angle_deg": round(max(math.degrees(math.asin(CRANK["r"] * math.sin(math.radians(p)) / CRANK["L"])) for p in phis_fine), 2),
            "pin_d_mm": pin_d, "F_design_N": F_link_design, "F_design_basis": "max(378 N servo stall into the 4.2 mm stop [lead], jam at the seat at 8.2 V stall)",
            "tau_pin_double_shear_MPa": round(F_link_design / (2 * math.pi * pin_d ** 2 / 4), 1),
            "eye_bearing_pressure_MPa": round(F_link_design / (pin_d * 4.0), 1),
            "stem_M3_thread_stress_MPa": round(F_link_design / 5.03, 1),
            "material": "17-4PH H1150 (Fty 724 MPa, engmat); stem top M3 (A_s 5.03 mm2) into the carriage with a lock nut"}
    r_stop = 6.0
    F_stop = HV69["stall_Nm"]["8.2"] / (r_stop * 1e-3)
    brg = {}
    # straddle mounting, link plane mid-span (each bearing 1/2 of the radial load); cases do not coincide:
    # (a) jam at the seat at 8.2 V stall (link only), (b) servo stall into the open stop: stop tang + needle loads (link <= 160 N)
    P0_cases = {"jam_at_seat_8V2": 0.5 * jam["8.2"], "stall_into_open_stop": 0.5 * (F_stop + 160.0), "lead_378N_link_basis": 0.5 * LOADS["link_stall_N"]}
    for name in ("NB701 (12x18x4)", "6800 (10x19x5)", "6801 (12x21x5)", "NB700 (10x15x3)"):
        d, D, B, C0 = BEARINGS[name]
        P0 = max(P0_cases.values())
        brg[name] = {"d_D_B_mm": [d, D, B], "C0r_kN": C0, "source": BEARING_SOURCE, "P0_N_governing": round(P0, 1), "s0": round(C0 * 1e3 / P0, 2),
                     "s0_jam_7V4": round(C0 * 1e3 / (0.5 * jam["7.4"]), 2), "s0_lead_378N": round(C0 * 1e3 / P0_cases["lead_378N_link_basis"], 2)}
    brg["P0_cases_N"] = {k_: round(v_, 1) for k_, v_ in P0_cases.items()}
    # v2.1 lead decision 2026-10-12: regulated 7.4 V pintle rail -> jam design case = 7.4 V + regulator tolerance (tolerance not yet
    # specified by Electronics): s0 of bearing A tabulated against the rail voltage (stall torque interpolated in the HV69 table)
    Vtab = sorted((float(k_), v_) for k_, v_ in HV69["stall_Nm"].items())
    def T_stall(V):
        return float(np.interp(V, [a_ for a_, _ in Vtab], [b_ for _, b_ in Vtab]))
    s0_vs_V = {}
    def T_stall_x(V):    # linear through the 7.4 / 8.2 V points, EXTRAPOLATED above 8.2 V (flagged)
        return HV69["stall_Nm"]["7.4"] + (V - 7.4) * (HV69["stall_Nm"]["8.2"] - HV69["stall_Nm"]["7.4"]) / 0.8
    for V in (7.4, 7.505, 7.6, 7.8, 8.0, 8.2, 8.4):
        Ts_ = T_stall(V) if V <= 8.2 else T_stall_x(V)
        Fj = (Ts_ - 0.9 * T0) / (dx0 + PIN["mu"] * PIN["r_mm"] * 1e-3 * pin_loss_factor(CRANK["phi_closed"]))
        s0_vs_V[f"{V:g}"] = {"T_stall_Nm": round(Ts_, 3), "T_stall_extrapolated": V > 8.2, "link_jam_N": round(Fj, 1),
                               "s0_NB701": round(BEARINGS["NB701 (12x18x4)"][3] * 1e3 / (0.5 * Fj), 2),
                               "s0_6800": round(BEARINGS["6800 (10x19x5)"][3] * 1e3 / (0.5 * Fj), 2)}
    brg["s0_vs_rail_voltage"] = s0_vs_V
    brg["jam_design_case_electronics"] = {V: {"link_N": F_, "P0_per_bearing_N": 0.5 * F_,
                                              "s0_NB701": round(BEARINGS["NB701 (12x18x4)"][3] * 1e3 / (0.5 * F_), 2),
                                              "s0_6800": round(BEARINGS["6800 (10x19x5)"][3] * 1e3 / (0.5 * F_), 2)}
                                          for V, F_ in JAM_LINK_N_ELECTRONICS.items()}
    brg["jam_design_case_note"] = ("DESIGN CASE (lead 2026-10-12): Electronics' jam link loads 688 N at the 7.505 V regulator upper tolerance and 789 N with the "
                                   "regulator failed through at 8.4 V (both computed with the v2.1 spring 0.19 N m -10 %, i.e. less spring credit than the "
                                   "S3 spring 0.30 N m -> conservative for S3; this script gives the S3 values in s0_vs_rail_voltage). Exceptional event: "
                                   "s0 >= 1 required; firmware stall detection; maintenance rule: any recorded pintle jam -> bearing A replaced before the next flight")
    brg["s0_vs_rail_voltage_note"] = ("jam at the seat, -10 % spring, straddle split 1/2 per bearing; HV69 stall torque linear between the 7.4 V (0.90) and "
                                      "8.2 V (1.00 N m) table points (retailer copies of MKS data, TO-CONFIRM); regulator tolerance of the 7.4 V rail = UNKNOWN "
                                      "(Electronics to specify) - read s0 at 7.4 V x (1 + tolerance)")
    bA, bB = brg["NB701 (12x18x4)"], brg["6800 (10x19x5)"]
    brg["selection"] = (f"A (servo side, nested dog coupling): 12x18x4 thin-section, NSK NB701 class, C0r 0.655 kN -> s0 {bA['s0']} jam at 8.2 V / "
                        f"{bA['s0_jam_7V4']} at 7.4 V / {bA['s0_lead_378N']} at the 378 N basis; B (outboard): 6800 10x19x5, C0r 0.84 kN -> s0 {bB['s0']} jam at "
                        "8.2 V (s0 >= 1 normal duty; the jam is an exceptional case). v1 6700/6701 'as recalled' C0 (0.98/1.03 kN) WITHDRAWN (not verifiable). "
                        "Shield/seal and high-temperature grease variants TO-VERIFY with the maker (head-top soak)")
    guide_N = round(Fl_max * g_of(90.0, y_use, g["s_mm"]), 1)
    spiral_variants = []
    for b_ in (6.0, 7.0, 8.0):
        for ro_ in (10.5,):
            sv = spiral_spring(1.1 * ch["T_stop_Nm"], kk, b=b_, r_o=ro_)
            sv["windup_at_stop_turns"] = round(ch["T_stop_Nm"] / kk / (2 * math.pi), 3)
            sv["preload_angle_deg"] = round(math.degrees(T0 / kk), 1)
            # coil-clearance screen (free-spiral validity): wind-up changes the mean coil radius by ~windup/turns; require the free gap to
            # stay >= 50 % of the strip thickness after a uniform radial contraction (r_o - r_i)(windup/turns) shared by the n gaps (SCREEN, maker to confirm)
            contraction = (ro_ - 4.0) * sv["windup_at_stop_turns"] / sv["turns"]
            sv["gap_after_windup_mm"] = round(sv["gap_free_mm"] - contraction / max(sv["turns"], 1.0), 3)
            sv["screen_ok"] = bool(sv["sigma_max_MPa"] <= sv["sigma_allow_MPa"] and sv["gap_after_windup_mm"] >= 0.5 * sv["strip_t_mm"])
            spiral_variants.append(sv)
    ok_sv = [v for v in spiral_variants if v["screen_ok"]]
    spiral = dict(ok_sv[0] if ok_sv else spiral_variants[-1])
    spiral["variants"] = [{k_: v[k_] for k_ in ("strip_b_mm", "strip_t_mm", "strip_length_mm", "turns", "pitch_mm", "gap_free_mm", "gap_after_windup_mm",
                                                 "sigma_max_MPa", "windup_at_stop_turns", "screen_ok")} for v in spiral_variants]
    spiral["material_note"] = ("strip allowable 1300 MPa is a REQUIREMENT on the spring maker's strip (static, at +10 % torque), not a recalled property: "
                               "maker to confirm against its datasheet (strip grade, Rm, set/relaxation at the head-top soak temperature)")
    # MECO close estimate: servo no-load speed at 7.4 V raised along the torque-speed line by the worst-case spring assist at that pressure
    # (-10 % spring), + 20 ms servo dead time/acceleration ASSUMED; chamber thrust lag not included (Combustion)
    lift_map = {"F75_P3.5MPa": (1.679, "P3.5MPa"), "F100_P3.5MPa": (2.981, "P3.5MPa"), "F75_P5.5MPa": (1.181, "P5.5MPa"), "F100_P5.5MPa": (1.775, "P5.5MPa")}
    x10 = 0.20
    meco = {}
    for nm, (x0, Pk) in lift_map.items():
        dphi_ = phi_at_lift(x0) - phi_at_lift(x10)
        w = OMEGA0_DPS["7.4"] * (1.0 + max(0.0, assist[Pk]) / HV69["stall_Nm"]["7.4"])
        meco[nm] = {"lift_from_mm": x0, "lift_to_mm": x10, "crank_deg": round(dphi_, 1), "assist_Nm": round(assist[Pk], 3),
                    "t_s_estimate": round(dphi_ / w + 0.02, 3), "t_s_no_assist": round(dphi_ / OMEGA0_DPS["7.4"] + 0.02, 3)}
    # ---------------- 4. crank radius growth (MKS travel < 99 deg): largest r with a feasible baseline spring meeting the choice targets
    r_study = []
    r0 = CRANK["r"]
    for r in (3.0, 3.25, 3.5, 3.75, 4.0):
        CRANK["r"] = r
        ps = phi_at_lift(CRANK["x_stop"])
        ph = list(np.linspace(CRANK["phi_closed"], ps, 30))
        rows = spring_design_v2(ph, g, y_use, c["f_seal"], T_open_max)
        chr_, note = choose(rows)
        r_study.append({"r_mm": r, "phi_stop_deg": round(ps, 1), "travel_cmd_deg": round(ps - CRANK["phi_cmd_closed"], 1), "n_feasible": len(rows),
                        "choice": chr_, "note": note})
    CRANK["r"] = r0
    out = {"version": "v2.2", "date": "2026-10-12", "script": "03-cad/src/calcs/pintle_inline_v34.py v2.2",
           "revision_note": "v2.2: baseline spring = S3 mu 0.20 design 0.30 N m + 0.10 N m/rad (lead); v2.1: 15 mm bushing spacing (v2 used 18 mm, does not fit v3.4); bearings NSK-verified C0r",
           "inputs": {"HV69": HV69, "assumed_geometry": ASSUMED_GEOM, "crank": CRANK, "needle_v1_envelope": NEEDLE, "loads": LOADS, "stations": STATIONS,
                      "guide_options": GUIDE_OPTIONS, "pin": PIN, "spring_tolerance": SPRING_TOL, "pressures_Pa": PRESSURES, "omega0_deg_s": OMEGA0_DPS,
                      "configs": CONFIGS, "baseline": BASELINE, "choice_rule": CHOICE_RULE, "y_link_plane_mm": y_use},
           "criteria": {"C1": "spring close (THROTTLE function, not the safety shutoff - that is the NC isolation valve, closed when de-energised; lead "
                              "2026-10-12): -10 % spring closes the needle from every lift at tank MEOP 7.0 MPa against pressure + seal + guide + pin friction",
                        "B-PNT-1_performance_check": "unpowered HV69 back-drive torque at the output < the MEOP closing assist (0.05 N m) so the spring alone "
                                                     "closes the pintle; a performance check, not a safety requirement",
                        "C2": "opening: +10 % spring; max servo torque over bench / crack-open at MEOP / 3.5 / 5.5 MPa <= HV69 stall at 7.4 V / 1.5",
                        "assist": "closing surplus with the -10 % spring (the servo dog brakes it); speeds MECO along the torque-speed line"},
           "crank_law": law, "phi_stop_deg": round(phi_stop, 2), "travel_cmd_deg": round(phi_stop - CRANK["phi_cmd_closed"], 1),
           "z_crank_axis_mm": round(z_c, 2), "fit": fits, "zone_forward_extent_mm_option_C": round(z_top_C, 1),
           "designs": designs,
           "baseline": {"config": BASELINE, "spring_law": {"T0_Nm_at_15deg": T0, "k_Nm_per_rad": kk, "T_stop_Nm": ch["T_stop_Nm"], "tolerance": SPRING_TOL},
                        "open_demand_bench_Nm": round(open_bench, 3), "open_demand_flight_Nm": round(open_flight, 3),
                        "margin_bench_7V4": round(HV69["stall_Nm"]["7.4"] / open_bench, 2), "margin_flight_7V4": round(HV69["stall_Nm"]["7.4"] / open_flight, 2),
                        "margin_bench_8V2": round(HV69["stall_Nm"]["8.2"] / open_bench, 2),
                        "assist_min_Nm": {k_: round(v_, 3) for k_, v_ in assist.items()}, "seat_load": seat, "link_force_max_N": round(Fl_max, 1),
                        "guide_normal_max_N": guide_N, "jam_at_seat_link_tension_N": jam, "profile": prof, "spring_hardware": spiral,
                        "spring_source": BASELINE_SPRING, "same_spring_nominal_guide_mu0.10": nominal_guide, "guide_mu_scan": mu_scan,
                        "B-PNT-1_acceptance": "measured guide friction mu <= 0.20 (15 mm spacing, 2 PTFE-lined bushings per pin) AND spring-only closing "
                                              "at tank MEOP demonstrated (lead 2026-10-12)"},
           "link": link, "stop": {"r_stop_mm": r_stop, "F_stop_N_at_8V2_stall": round(F_stop, 1),
                                  "note": "crank-web tang on a pressed 3 mm stop pin; link load at the stop = needle loads only"},
           "bearings": brg, "meco_close_estimate": meco, "crank_radius_study": r_study,
           "lead_decisions_2026-10-12": {
               "bearing_A": "keep the 12x18x4 NB701 class (6801 12x21x5 NOT adopted)",
               "jam_design_case": "regulated 7.4 V pintle rail: jam design case = 7.4 V + regulator tolerance (not 8.2 V); s0 1.94 at 7.4 V accepted for an "
                                  "exceptional event with firmware stall detection",
               "maintenance_rule": "any recorded pintle jam -> bearing A replaced before the next flight (BOM note)",
               "approved": "15 mm bushing spacing; spring v2.1 (0.19 + 0.17) approved then SUPERSEDED the same day by the S3 mu 0.20 design "
                           "(0.30 N m at closed + 0.10 N m/rad, +/-10 %)",
               "B-PNT-1_acceptance": "measured guide mu <= 0.20 with closing at MEOP demonstrated",
               "rail_update": "Electronics raises the pintle rail setpoint ~1 % to ~7.49 V typ (opening margin >= 1.5 at the servo plug); jam ~602 N at the "
                              "new upper tolerance with S3 < the 688 N case checked -> no change (lead FYI 2026-10-12)",
               "gating_item": "HV69 commanded travel >= 103 deg (10 -> 113 deg) - founder action: buy one HV69 early, B-PNT-1 travel / back-drive / guide "
                              "friction before the pintle CAD freezes (Electronics owns the procedure); fallback = jackshaft layout (sketch + zone length)",
               "datasheet_discipline": "every bearing, O-ring and fastener in the BOM carries a maker datasheet reference; no 'as recalled' values"}}
    (HERE / "pintle_inline_v34_v2p2.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("phi_stop_deg", "travel_cmd_deg", "z_crank_axis_mm", "zone_forward_extent_mm_option_C", "link", "bearings",
                                         "meco_close_estimate")}, indent=1, default=float))
    bl = dict(out["baseline"]); bl.pop("profile")
    print(json.dumps(bl, indent=1, default=float))
    for k, v in designs.items():
        print(k, v["n_feasible"], v["choice_note"], v["choice"])
    for k, v in fits.items():
        print(k, {kk_: v[kk_] for kk_ in ("y_l_min_mm", "y_l_max_mm", "case_z_mm")})
    for r in r_study:
        print(r["r_mm"], r["travel_cmd_deg"], r["n_feasible"], r["note"], r["choice"])


if __name__ == "__main__":
    main()
