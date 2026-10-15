"""Pintle drive v3.4 - in-line MKS HV69 toggle crank, v2.3 (03-cad/src/calcs, 2026-10-13, Mechanical).

v2.3 implements the lead decision of 2026-10-12 (CHANGELOG line 44, combustion.json pintle_actuator.lead_decision_v2p3):
rolling-guide needle carriage, spring 0.25 N m at closed + 0.12 N m/rad (+/-10 %), C1 (spring close) on the L0 needle-force law,
C2 (opening margin >= 1.5 at the HV69 stall 0.90 N m, 7.4 V) on L1 AND L2, datasheet values only for guide/bearing capacities.
The v2.2 script (pintle_inline_v34.py, unchanged, imported read-only by Combustion's needle_force_v2p3.py) stays the v2.2 record.

What v2.3 answers (numbers tagged; nothing here is a test result):
 1. VALIDATION: re-implements Combustion's C1/C2 cases (bench, start <= 0.3 mm at 5.05/7.0 MPa with the torch, hot-fire line of
    throttle_map_v2) and reproduces their 'rolling_plainpins T0.25 k0.12' result before using the model.
 2. GUIDE: HIWIN miniature guideway selection from the catalogue static moment M0 against the carriage couple F y_l at the jam case.
 3. LINK EYES: rolling (ball / needle) vs plain eyes - datasheet static capacity against the closed-hold and jam link loads, and the
    width each adds to the crank stack inside the 8 deg swept cone (fit window from v2.2, 3 mm slack).
 4. C1/C2 of the final configuration with sensitivities (guide mu, end-seal drag S, pin mu, stem seal friction).
 5. JAM: link tension with the needle held closed and the HV69 stalled (opening) vs rail voltage; the design value uses pin friction 0
    (friction cannot be relied on to absorb servo torque); component static margins at that load.
 6. SEAT break-out (15 deg self-locking wedge) margins vs seat friction, MECO close estimate, crank-radius / jackshaft fallback table
    for the HV69 travel gate (>= 103 deg).
 7. OI-7 / lead condition C5: 15 um filter element downstream of the hose and riser weld - catalogue screening (Swagelok MS-01-92)
    and the element area requirement.
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
MIRROR = Path("/home/claude/work/mechanical/iface_snapshot/mirror/engine/02-combustion/data/v2")
HOT_CSV = MIRROR / "needle_force_bounds_v2p3.csv"
SIN8, COS8 = math.sin(math.radians(8.0)), math.cos(math.radians(8.0))
R_SWEEP = 67.0
PA = 101325.0
P_TORCH = 1.5e5                                  # Combustion needle_force_v2p3.py (ASSUMED chamber with the torch lit)

# ------------------------------------------------------------------------------------------------ inputs (tagged)
HV69 = {"L": 29.0, "W": 13.0, "H": 28.7, "stall_Nm": {"4.8": 0.59, "6.0": 0.74, "7.4": 0.90, "8.2": 1.00},
        "tag": "Electronics msg 2026-10-12 (retailer copies of MKS data, TO-CONFIRM with MKS)"}
ASSUMED_GEOM = {"spline_protrusion_mm": 4.0, "shaft_from_case_end_mm": 7.25, "tag": "ASSUMED (MKS drawing not available) - as v2.2"}
CRANK = {"r": 3.0, "L": 28.0, "phi_closed": 15.0, "phi_cmd_closed": 10.0, "x_stop": 4.2, "tag": "Electronics pintle_mini_servo_v1 / lead 2026-10-12"}
STATIONS = {"z_k0": 215.59, "tag": "CAD v3.3 needle-end (carriage) pin closed at z 215.6"}
SPRING = {"T0_Nm": 0.25, "k_Nm_per_rad": 0.12, "tol": 0.10, "tag": "LEAD decision 2026-10-12 (combustion.json pintle_actuator.lead_decision_v2p3)"}
STEM_D, SEAT_D, ALPHA_DEG = 3.0, 5.5, 15.0      # mm, mm, deg (Mechanical v2 stem; combustion.json seat and cone)
A_STEM, A_SEAT = math.pi / 4 * STEM_D ** 2, math.pi / 4 * SEAT_D ** 2
F_SEAL = {"design": 18.75, "low": 5.0, "tag": "design 18.75 N ASSUMED upper bound (v2); Combustion c_seal estimate 1-5 N (DERIVED order of magnitude)"}
C1_P = {"P3.5MPa": 3.5e6, "P5.5MPa": 5.5e6, "MEOP": 7.0e6}
START_P1 = (5.05e6, 7.0e6)
T_ALLOW = 0.90 / 1.5                              # C2: stall at 7.4 V / 1.5

# HIWIN MG catalogue 2023 (HIWIN publication 3455-3, copy https://damencnc.com/userdata/file/3455-3_HIWIN_MGN_and_MGW_Product_Catalog_2023.pdf,
# read 2026-10-12/13): Table 3.76 load ratings / static moments, Tables 3.79/3.80 block dimensions; extraction of a PDF copy -> VERIFY at order
GUIDES = {
    "MGN07H": {"C0_N": 1960, "M0X_Nm": 7.6, "M0Y_Nm": 4.8, "M0Z_Nm": 4.8, "L_mm": 30.8, "L1_mm": 21.8, "W_mm": 17, "H_mm": 8, "mass_kg": 0.020},
    "MGN09C": {"C0_N": 2550, "M0X_Nm": 11.8, "M0Y_Nm": 7.4, "M0Z_Nm": 7.4, "L_mm": 28.9, "L1_mm": 18.9, "W_mm": 20, "H_mm": 10, "mass_kg": 0.020},
    "MGN09H": {"C0_N": 4020, "M0X_Nm": 19.6, "M0Y_Nm": 18.6, "M0Z_Nm": 18.6, "L_mm": 39.9, "L1_mm": 29.9, "W_mm": 20, "H_mm": 10, "mass_kg": 0.030},
    "MGN12C": {"C0_N": 3920, "M0X_Nm": 25.5, "M0Y_Nm": 13.7, "M0Z_Nm": 13.7, "L_mm": 34.7, "L1_mm": 21.7, "W_mm": 27, "H_mm": 13, "mass_kg": 0.030},
    "MGW09C": {"C0_N": 4120, "M0X_Nm": 40.1, "M0Y_Nm": 18.0, "M0Z_Nm": 18.0, "L_mm": 39.3, "L1_mm": 27.5, "W_mm": 30, "H_mm": 12, "mass_kg": 0.040},
}
GUIDE_SRC = ("HIWIN MG series catalogue 2023 (3455-3) Tables 3.76/3.79/3.80 via the damencnc.com copy; rail MGNR09R 9 x 6.5 mm, 0.38 kg/m, "
             "hole pitch 20 mm (Table 3.81); default end seals both sides; bottom seal not available for size 9")
MU_GUIDE = {"datasheet": 0.004, "design": 0.010,
            "tag": "HIWIN Linear Guideway E (https://hiwin.com/wp-content/uploads/Linear_Guideway-E.pdf) section 1-6: ball type 'about 0.004', "
                   "F = mu W + S; design 0.010 = lead bound (mu <= 0.01)"}
S_END_SEAL = {"design_N": 2.0, "range_N": [0.0, 1.0, 2.0, 5.0],
              "tag": "MGN end-seal resistance S NOT PUBLISHED in the catalogue read (HIWIN F = mu W + S); 2 N ASSUMED design, B-PNT-1 measures it"}
# link-eye options (rolling options with datasheet C0r; plain = v2.2 pins, the basis of Combustion's adopted check)
EYES = {
    "plain_3mm_DU": {"pin_d_mm": 3.0, "eye_w_mm": 4.0, "mu": 0.15, "mu_low": 0.0, "C0r_N": None,
                     "src": "v2.2 pins: 17-4PH H900 pin in a PTFE-lined (DU-class) bush or dry-film; mu 0.15 = Combustion check basis (ASSUMED), "
                            "lower bound 0 for the jam load"},
    "ball_623ZZ": {"pin_d_mm": 3.0, "eye_w_mm": 4.0, "mu": 0.010, "mu_low": 0.0, "C0r_N": 218.0,
                   "src": "NSK 623ZZ 3x10x4, Cr 695 N, C0r 218 N (RS Components datasheet https://docs.rs-online.com/9a61/A700000014623800.pdf)"},
    "needle_HK0408": {"pin_d_mm": 4.0, "eye_w_mm": 8.0, "mu": 0.010, "mu_low": 0.0, "C0r_N": 1270.0,
                      "src": "NTN HK0408T2 Fw 4 x D 8 x C 8, Cr 1.77 kN, C0r 1.27 kN, -20..100 C (polyamide cage), 0.002 kg "
                             "(RS Components datasheet https://docs.rs-online.com/29da/A700000013904625.pdf)"},
}
CRANK_BEARINGS = {"A_NB701": (12, 18, 4, 655.0), "B_6800": (10, 19, 5, 840.0),
                  "src": "NSK e1153a thin-section catalogue (C0r as printed), read 2026-10-12 (v2.2)"}
RAIL_V = {"7.4": "nominal", "7.505": "Electronics v2.1 regulator upper tolerance", "7.6": "covers the ~7.57 V upper tolerance after the "
          "+1 % setpoint raise (lead FYI 2026-10-12; Electronics to confirm)", "8.2": "HV69 table top", "8.4": "regulator failed through (EXTRAPOLATED)"}


def stall(V):
    tab = sorted((float(k), v) for k, v in HV69["stall_Nm"].items())
    if V <= tab[-1][0]:
        return float(np.interp(V, [a for a, _ in tab], [b for _, b in tab]))
    return HV69["stall_Nm"]["7.4"] + (V - 7.4) * (HV69["stall_Nm"]["8.2"] - HV69["stall_Nm"]["7.4"]) / 0.8


# ------------------------------------------------------------------------------------------------ crank kinematics (as v2.2)
def s_of(phi_deg, r=None, L=None):
    r = CRANK["r"] if r is None else r
    L = CRANK["L"] if L is None else L
    p = math.radians(phi_deg)
    return r * math.cos(p) + math.sqrt(L * L - (r * math.sin(p)) ** 2)


def lift(phi_deg):
    return s_of(CRANK["phi_closed"]) - s_of(phi_deg)


def dxdphi(phi_deg, h=1e-4):
    return (lift(phi_deg + h) - lift(phi_deg - h)) / math.radians(2 * h)       # mm/rad


def phi_at_lift(x):
    lo, hi = CRANK["phi_closed"], 179.0
    for _ in range(80):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if lift(m) < x else (lo, m)
    return 0.5 * (lo + hi)


def psi_of(phi_deg):
    return math.asin(CRANK["r"] * math.sin(math.radians(phi_deg)) / CRANK["L"])


def pin_factor(phi_deg):
    """|relative rotation| crank-pin eye |1 - dpsi/dphi| + needle-pin eye |dpsi/dphi| per unit crank rotation."""
    p = math.radians(phi_deg)
    a = CRANK["r"] * math.cos(p) / (CRANK["L"] * math.cos(psi_of(phi_deg)))
    return abs(1 - a) + abs(a)


# ------------------------------------------------------------------------------------------------ needle pressure force (+ = OPENING here)
def F_L0(x_mm, P1):
    """L0 = v2.2 blend: seated dp (A_seat - A_stem) closing -> dp A_stem opening over the first 0.1 mm (P_down = Pa)."""
    dp = max(0.0, P1 - PA) * 1e-6
    w = min(1.0, max(0.0, x_mm / 0.10))
    return -(1 - w) * dp * (A_SEAT - A_STEM) + w * dp * A_STEM


def F_law(law, x_mm, P1, Pdown):
    """Combustion needle_force_v2p3 laws, converted to + opening.  Combustion: F = (P1 - Pdown) A_eff - (P1 - Pa) A_stem (+ closing)."""
    h = max(0.0, x_mm)
    if h <= 0.0:
        a_eff = A_SEAT
    elif law == "L1":
        a_eff = math.pi * (SEAT_D / 2 - h * math.sin(math.radians(ALPHA_DEG)) * math.cos(math.radians(ALPHA_DEG))) ** 2
    elif law == "L2":
        a_eff = A_SEAT
    else:
        raise ValueError(law)
    return -((P1 - Pdown) * 1e-6 * a_eff - (P1 - PA) * 1e-6 * A_STEM)


# ------------------------------------------------------------------------------------------------ friction / torque model
class Cfg:
    def __init__(self, name, mu_g, s_eff, S, mu_p, r_p, y_l, f_seal, T0=None, k=None, tol=None):
        self.name, self.mu_g, self.s_eff, self.S, self.mu_p, self.r_p, self.y_l, self.f_seal = name, mu_g, s_eff, S, mu_p, r_p, y_l, f_seal
        self.T0 = SPRING["T0_Nm"] if T0 is None else T0
        self.k = SPRING["k_Nm_per_rad"] if k is None else k
        self.tol = SPRING["tol"] if tol is None else tol

    def T(self, phi):
        return self.T0 + self.k * math.radians(phi - CRANK["phi_closed"])

    def d(self):
        return {k: getattr(self, k) for k in ("name", "mu_g", "s_eff", "S", "mu_p", "r_p", "y_l", "f_seal", "T0", "k", "tol")}


def g_of(phi_deg, y_mm, s_mm):
    return 2.0 * y_mm / s_mm + abs(math.tan(psi_of(phi_deg)))


def link_force(c, phi, fpo, closing):
    """Link force (N, + = compression pushing the needle closed), needle moving: F = F_po + (f_seal + S + mu_g |F| g) sgn(u)."""
    mg = c.mu_g * g_of(phi, c.y_l, c.s_eff)
    fc = c.f_seal + c.S
    if closing:
        num = fpo + fc
        return num / (1 - mg) if num > 0 else num / (1 + mg)
    num = fpo - fc
    return num / (1 - mg) if num < 0 else num / (1 + mg)


def servo_torque(c, phi, T_s, fpo, opening):
    """T_m = T_s - F dx/dphi +/- mu_p |F| r_p pin_factor (pins oppose motion). Opening: required drive; closing: spring surplus (assist)."""
    F = link_force(c, phi, fpo, not opening)
    pl = c.mu_p * abs(F) * c.r_p * 1e-3 * pin_factor(phi)
    return T_s - F * dxdphi(phi) * 1e-3 + (pl if opening else -pl), F


def hot_rows():
    import csv
    rows = []
    with open(HOT_CSV) as fh:
        rd = csv.DictReader(l for l in fh if not l.startswith("#"))
        for r in rd:
            if abs(float(r["D_port_m"]) - 0.025) < 1e-9:
                rows.append({k: float(v) for k, v in r.items()})
    return rows


def evaluate(c, laws=("L1", "L2"), n_full=200):
    phi_c = CRANK["phi_closed"]
    phis_full = list(np.linspace(phi_c, phi_at_lift(CRANK["x_stop"]), n_full))
    phis_start = list(np.linspace(phi_c, phi_at_lift(0.3), 12))
    out = {"cfg": c.d()}
    # C1 (L0, -10 % spring, closing, full stroke)
    a = {nm: min(servo_torque(c, p, (1 - c.tol) * c.T(p), F_L0(lift(p), P), False)[0] for p in phis_full) for nm, P in C1_P.items()}
    out["C1_assist_min_Nm"] = {k: round(v, 3) for k, v in a.items()}
    out["C1_pass"] = bool(min(a.values()) >= 0)
    hr = hot_rows()
    for law in laws:
        t_b = max(servo_torque(c, p, (1 + c.tol) * c.T(p), 0.0, True)[0] for p in phis_full)
        t_s = max(servo_torque(c, p, (1 + c.tol) * c.T(p), F_law(law, lift(p), P1, P_TORCH), True)[0] for P1 in START_P1 for p in phis_start)
        col = "F_L1_3mm_N" if law == "L1" else "F_L2_3mm_N"
        t_h = max(servo_torque(c, phi_at_lift(r["lift_mm"]), (1 + c.tol) * c.T(phi_at_lift(r["lift_mm"])), -r[col], True)[0] for r in hr)
        t2 = max(t_b, t_s, t_h)
        out[f"C2_{law}"] = {"bench_start_hot_Nm": [round(t_b, 3), round(t_s, 3), round(t_h, 3)], "max_Nm": round(t2, 3),
                            "margin_7V4": round(HV69["stall_Nm"]["7.4"] / t2, 2), "pass": bool(t2 <= T_ALLOW + 1e-9)}
    # unlit full stroke at tank pressure (ground-test procedure cases, not flight): N2 at 3.5 MPa, P_down = Pa
    ul = {}
    for law in ("L1", "L2"):
        ul[law] = round(HV69["stall_Nm"]["7.4"] / max(servo_torque(c, p, (1 + c.tol) * c.T(p), F_law(law, lift(p), 3.5e6, PA), True)[0]
                                                      for p in phis_full), 2)
    ul["L0"] = round(HV69["stall_Nm"]["7.4"] / max(servo_torque(c, p, (1 + c.tol) * c.T(p), F_L0(lift(p), 3.5e6), True)[0] for p in phis_full), 2)
    out["unlit_full_stroke_3p5MPa_margin_7V4"] = ul
    out["seat_load_N"] = {"minus10": round((1 - c.tol) * c.T0 / (dxdphi(phi_c) * 1e-3), 1), "nominal": round(c.T0 / (dxdphi(phi_c) * 1e-3), 1),
                          "plus10": round((1 + c.tol) * c.T0 / (dxdphi(phi_c) * 1e-3), 1)}
    return out


# ------------------------------------------------------------------------------------------------ fit (as v2.2, stack per option)
def fit(stack, z_c, case_down=True):
    a = ASSUMED_GEOM["shaft_from_case_end_mm"]
    zc0, zc1 = (z_c - (HV69["L"] - a), z_c + a) if case_down else (z_c - a, z_c + (HV69["L"] - a))
    pts = lambda x0, x1, y0, y1, z0, z1: [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    sw = lambda P: max(math.hypot(p[0], p[1]) * COS8 + abs(p[2]) * SIN8 for p in P)
    ok = []
    ys = np.arange(0.0, 40.0, 0.05)
    for yl in ys:
        yf = yl - stack["servo_side"]
        case = pts(-HV69["W"] / 2, HV69["W"] / 2, yf - HV69["H"], yf, zc0, zc1)
        hh = stack["housing_half"]
        hous = pts(-hh, hh, yl - stack["servo_side"] + 1.0, yl + stack["crank_side"], z_c - hh, z_c + hh)
        ok.append(sw(case) <= R_SWEEP and sw(hous) <= R_SWEEP)
    ok = np.array(ok)
    if ok.any():
        return {"y_l_min_mm": round(float(ys[ok].min()), 2), "y_l_max_mm": round(float(ys[ok].max()), 2), "feasible": True}
    return {"y_l_min_mm": None, "y_l_max_mm": None, "feasible": False}


# ------------------------------------------------------------------------------------------------ OI-7 / C5 filter screening
def filter_screen():
    """Swagelok MS-01-92 'Flow Data at 70 F (20 C)', 15 um elements, water flow (US gal/min) at 10 / 50 / 100 psi drop.
    Fit dP = a Q + b Q^2 (viscous + inertial), scale to liquid N2O: a x mu_N2O/mu_water, b x rho_N2O/rho_water."""
    data = {"Swagelok 6TF/8TF-15 (3/8-1/2 in tee, sintered 15 um, element 1280 mm2)": [(0.84, 10.0), (2.6, 50.0), (4.1, 100.0)],
            "Swagelok FW-15 (1/4 in all-welded, pleated 316 mesh 15 um, element 1450 mm2)": [(1.7, 10.0), (5.5, 50.0), (8.3, 100.0)]}
    rho = 820.7                       # kg/m3 saturated liquid 15 C (Combustion low_inlet_check n2o_liquid_CoolProp)
    mu_ratio = 0.07                   # mu_N2O / mu_water: ESDU 91022 correlation 0.062 mPa s at 15 C (AS RECALLED; CoolProp has no N2O viscosity)
    mdot = 0.26
    Q = mdot / rho / 3.785411784e-3 * 60.0     # US gal/min
    out = {"basis": {"mdot_kg_s": mdot, "T_C": 15, "rho_kg_m3": rho, "Q_usgpm": round(Q, 3), "mu_ratio_N2O_water": mu_ratio,
                     "src": "Swagelok Filters catalogue MS-01-92 (https://swagelok.com/downloads/webcatalogs/EN/MS-01-92.PDF) flow tables; "
                            "filtration areas from the same catalogue ('Filtration area' table)",
                     "allocation": "filter Cv 2.2 at 0.26 kg/s: dP = SG (Q/Cv)^2 = %.3f bar (combustion.json isolation_valve / OI-7)" %
                                   ((rho / 1000.0) * (Q / 2.2) ** 2 / 14.5038)},
           "units": {}}
    for nm, pts in data.items():
        A = np.array([[q, q * q] for q, _ in pts]); y = np.array([p for _, p in pts])
        (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
        dp_psi = a * mu_ratio * Q + b * (rho / 998.0) * Q * Q
        cv_eq = Q * math.sqrt((rho / 1000.0) / dp_psi)
        out["units"][nm] = {"fit_a_psi_per_gpm": round(float(a), 3), "fit_b_psi_per_gpm2": round(float(b), 3),
                            "dP_N2O_bar": round(dp_psi / 14.5038, 2), "Cv_equivalent": round(cv_eq, 2),
                            "verdict": "REJECT as the filter unit: dP %.2f bar >> allocation" % (dp_psi / 14.5038)}
    out["units"]["Swagelok FW-15 (1/4 in all-welded, pleated 316 mesh 15 um, element 1450 mm2)"]["note"] = (
        "1/4 in tube ports (ID ~4.6 mm, ~16 mm2) also violate lead condition C1 (every flow section >= 35 mm2); the catalogue lists IDENTICAL "
        "flows for the 2, 7 and 15 um pleated elements -> the 1450 mm2 pleated element is not the limiting resistance at 8.3 US gpm")
    out["requirement_v34"] = (
        "custom element in the inlet block, DOWNSTREAM of the hose and riser weld (lead C5): 15 um absolute class 316L woven (Dutch twill) "
        "mesh, pleated or cylindrical, filtration area >= 1450 mm2 (the FW pleated element area, shown non-limiting by the catalogue data), "
        "every passage >= 35 mm2 (C1), element dP at 0.26 kg/s N2O <= 0.30 bar (Cv 2.2 allocation) from the maker's dP-flow curve "
        "(TO-VERIFY / TO-QUOTE, Sonderborg DK-6400), oxygen-clean (ASTM G93 level per Combustion), removable for inspection; "
        "the CAD v3.3 TC-04 40 um sintered disc 10 x 2.5 mm under the inlet is deleted")
    return out


def main():
    phi_c = CRANK["phi_closed"]
    phi_stop = phi_at_lift(CRANK["x_stop"])
    dx0 = dxdphi(phi_c) * 1e-3
    out = {"id": "pintle_inline_v34", "version": "v2.3", "date": "2026-10-13", "script": "03-cad/src/calcs/pintle_v2p3.py",
           "supersedes": "pintle_inline_v34_v2p2.json (v2.2 kept as history; script pintle_inline_v34.py unchanged)",
           "inputs": {"HV69": HV69, "crank": CRANK, "spring": SPRING, "stem_d_mm": STEM_D, "seat_d_mm": SEAT_D, "f_seal": F_SEAL,
                      "guides": GUIDES, "guide_src": GUIDE_SRC, "mu_guide": MU_GUIDE, "S_end_seal": S_END_SEAL, "eyes": EYES,
                      "crank_bearings": CRANK_BEARINGS, "rail_voltages": RAIL_V, "P_torch_Pa": P_TORCH,
                      "hot_fire_rows": {"file": str(HOT_CSV), "sha256_16": hashlib.sha256(HOT_CSV.read_bytes()).hexdigest()[:16],
                                        "rows_D25": len(hot_rows()), "tag": "Combustion needle_force_bounds_v2p3.csv (SIM throttle_map_v2 states), mirrored"}},
           "criteria": {"C1": "L0, -10 % spring: closing assist >= 0 over the stroke at 3.5 / 5.5 / 7.0 MPa (targets 0.05 at MEOP, 0.08 at 5.5 MPa)",
                        "C2": "L1 AND L2, +10 % spring: max opening torque over bench + start (<= 0.3 mm, 5.05/7.0 MPa, torch 1.5 bar) + hot-fire line "
                              "<= 0.60 N m (HV69 stall 0.90 N m at 7.4 V / 1.5)",
                        "jam": "needle held closed, HV69 stalled opening, -10 % spring, pin friction 0 (lower bound): static capacity s0 >= 1 "
                               "(exceptional event; parts replaced after any recorded jam)"},
           "crank": {"phi_stop_deg": round(phi_stop, 2), "travel_cmd_deg": round(phi_stop - CRANK["phi_cmd_closed"], 1),
                     "dx_dphi_closed_mm_per_rad": round(dx0 * 1e3, 4)}}

    # 1. validation against Combustion's adopted check (rolling_18mm mu 0.005 / s 18 mm, plain pins mu 0.15 r 1.5, y 11, seal 18.75)
    cval = Cfg("combustion_rolling_plainpins", mu_g=0.005, s_eff=18.0, S=0.0, mu_p=0.15, r_p=1.5, y_l=11.0, f_seal=18.75)
    ev = evaluate(cval)
    ref = {"L1": [0.555, 0.534, 0.496], "L2": [0.555, 0.55, 0.54], "MEOP": 0.108, "P5.5MPa": 0.137, "P3.5MPa": 0.172}
    dev = max([abs(a - b) for law in ("L1", "L2") for a, b in zip(ev[f"C2_{law}"]["bench_start_hot_Nm"], ref[law])] +
              [abs(ev["C1_assist_min_Nm"][k] - ref[k]) for k in ("MEOP", "P5.5MPa", "P3.5MPa")])
    out["validation_vs_combustion"] = {"case": "pintle_spring_window_v2p3 rolling_plainpins_T0.25_k0.12", "this_model": ev, "combustion": ref,
                                       "max_abs_dev_Nm": round(dev, 4), "pass": bool(dev <= 0.002)}
    assert dev <= 0.002, ("model does not reproduce Combustion's adopted check", ev, ref)

    # 2. fit window (v2.2 stack C) and the width each link-eye option adds
    z_c = STATIONS["z_k0"] + s_of(phi_c)
    base = {"servo_side": 13.0, "crank_side": 16.0, "housing_half": 11.0}
    fits = {}
    for nm, e in EYES.items():
        dw = (e["eye_w_mm"] - 4.0) / 2.0
        st = {"servo_side": base["servo_side"] + dw, "crank_side": base["crank_side"] + dw, "housing_half": base["housing_half"]}
        fits[nm] = dict(fit(st, z_c), stack=st)
    out["fit_by_eye_option"] = fits
    out["fit_note"] = ("v2.2 stack C (link eye 4 mm + 2 mm webs / bearing A 4 / nested one-sided dog 1 / spline 4; crank side bearing B, wall, "
                       "spiral spring 6): y_l window 10.4-13.45 mm = 3 mm slack; an eye wider than ~7 mm closes the window (HV69 case corner at "
                       "the case top vs the 8 deg cone at z ~254 on one side, crank housing on the other)")

    # 3. jam link tension vs rail voltage; design value with pin friction 0
    jam = {}
    for V in (7.4, 7.505, 7.6, 8.2, 8.4):
        Ts = stall(V)
        row = {"T_stall_Nm": round(Ts, 3), "extrapolated": V > 8.2}
        for nm, mu_p, r_p in (("mu_p_0", 0.0, 1.5), ("plain_mu_0.15", 0.15, 1.5)):
            row[f"F_link_N_{nm}"] = round((Ts - (1 - SPRING["tol"]) * SPRING["T0_Nm"]) / (dx0 + mu_p * r_p * 1e-3 * pin_factor(phi_c)), 1)
        jam[f"{V:g}V"] = row
    F_jam = jam["7.6V"]["F_link_N_mu_p_0"]
    out["jam"] = {"by_rail_voltage": jam, "design_F_link_N": F_jam,
                  "basis": "7.6 V (covers the ~7.57 V upper tolerance), -10 % spring, pin friction 0: friction cannot be relied on to absorb the "
                           "servo stall torque, so the v2.2/Electronics '~600 N' (plain-pin mu 0.15 credited) is NOT a design value",
                  "direction": "link, carriage, stem in TENSION (servo opening, needle held in the seat); one-sided dog -> the servo never pushes "
                               f"the needle closed: link compression <= +10 % spring hold {(1 + SPRING['tol']) * SPRING['T0_Nm'] / dx0:.0f} N"}

    # 4. link-eye capacity: rolling options vs closed hold (+10 % spring) and the jam
    F_hold = (1 + SPRING["tol"]) * SPRING["T0_Nm"] / dx0
    eyes = {}
    for nm, e in EYES.items():
        r = {"src": e["src"], "eye_w_mm": e["eye_w_mm"], "fits_swept_cone": fits[nm]["feasible"]}
        if e["C0r_N"]:
            r["s0_closed_hold"] = round(e["C0r_N"] / F_hold, 2)
            r["s0_jam"] = round(e["C0r_N"] / F_jam, 2)
            r["capacity_ok"] = bool(r["s0_closed_hold"] >= 2.0 and r["s0_jam"] >= 1.0)
        else:
            p = F_jam / (e["pin_d_mm"] * e["eye_w_mm"])
            r["bearing_pressure_jam_MPa"] = round(p, 1)
            r["pin_double_shear_jam_MPa"] = round(F_jam / (2 * math.pi / 4 * e["pin_d_mm"] ** 2), 1)
            r["capacity_ok"] = True
            r["capacity_note"] = ("static bearing pressure %.0f MPa at the jam: PTFE-lined steel-backed (DU class) static limit is a maker value "
                                  "(TO-VERIFY, commonly quoted ~250 MPa AS RECALLED); hardened pin H900" % p)
        r["selectable"] = bool(r["capacity_ok"] and r["fits_swept_cone"])
        eyes[nm] = r
    out["link_eyes"] = eyes
    out["link_eye_decision"] = (
        "PLAIN eyes (3 mm 17-4PH H900 pins in PTFE-lined DU-class bushes, eye 4 mm): the only option that both fits the 3 mm stack slack and "
        "carries the loads. Ball 623ZZ fits but C0r 218 N < the %.0f N closed hold (s0 %.2f) and the %.0f N jam; needle HK0408 carries them "
        "(s0 %.1f / %.2f) but its 8 mm eye closes the y_l window (stack +4 mm). Combustion's adopted margins 1.62 / 1.62 were computed with "
        "plain pins mu 0.15, so the performance basis of the lead decision is unchanged; the deviation from 'ball-bearing link eyes' is "
        "reported to the lead" % (F_hold, 218.0 / F_hold, F_jam, 1270.0 / F_hold, 1270.0 / F_jam))

    # 5. guide selection against the jam couple and the hold couple
    y_l = 11.0
    gsel = {}
    for nm, gd in GUIDES.items():
        M_jam = F_jam * y_l * 1e-3
        M_hold = F_hold * y_l * 1e-3
        gsel[nm] = {"M0Y_Nm": gd["M0Y_Nm"], "s0_M_jam": round(gd["M0Y_Nm"] / M_jam, 2), "s0_M_hold": round(gd["M0Y_Nm"] / M_hold, 2),
                    "L_mm": gd["L_mm"], "W_mm": gd["W_mm"], "H_mm": gd["H_mm"], "mass_kg": gd["mass_kg"],
                    "ok": bool(gd["M0Y_Nm"] / M_jam >= 1.0 and gd["M0Y_Nm"] / M_hold >= 2.0)}
    out["guide_selection"] = {"y_l_mm": y_l, "M_jam_Nm": round(F_jam * y_l * 1e-3, 2), "M_hold_Nm": round(F_hold * y_l * 1e-3, 2), "blocks": gsel,
                              "selected": "MGN09H (narrowest block meeting s0 >= 1 at the jam; MGN12C alternate if the 39.9 mm length does not fit)",
                              "fit_note": "block 39.9 mm + 4.2 mm stroke does not fit the 19.7 mm carriage zone z 211-231 on the needle axis: CAD v3.4 "
                                          "places the rail beside the bonnet/crank housing (swept-cone check in the CAD); couple about the axis "
                                          "normal to the link plane = block pitch/yaw moment (M0Y/M0Z), not roll",
                              "temperature": "MGN operating temperature not stated in the catalogue read; end caps/recirculation parts are polymer "
                                             "(TO-VERIFY with HIWIN) vs the head-top soak (bonnet top 128 C, bracket foot 130 C, DC-B1 hi soak, "
                                             "thermal FEA v1.1): guide temperature from the servo-mount thermal network (pending) or HIWIN metal-cap option",
                              "src": GUIDE_SRC}

    # 6. final configuration and sensitivities
    gH = GUIDES["MGN09H"]
    final = Cfg("v2.3 baseline: MGN09H + plain DU pins", mu_g=MU_GUIDE["design"], s_eff=gH["L1_mm"], S=S_END_SEAL["design_N"], mu_p=0.15,
                r_p=1.5, y_l=y_l, f_seal=F_SEAL["design"])
    out["baseline"] = evaluate(final)
    sens = {}
    for lab, kw in (("mu_g 0.004 (datasheet), S 0", dict(mu_g=0.004, S=0.0)), ("mu_g 0.02, S 5 N", dict(mu_g=0.02, S=5.0)),
                    ("pins mu 0.05", dict(mu_p=0.05)), ("pins mu 0.25", dict(mu_p=0.25)), ("seal 5 N", dict(f_seal=5.0)),
                    ("seal 25 N", dict(f_seal=25.0)), ("y_l 13.45 (window max)", dict(y_l=13.45)),
                    ("needle eyes mu 0.01 r 2 (if the stack fitted)", dict(mu_p=0.01, r_p=2.0))):
        d = final.d(); d.update(kw); d.pop("name")
        e = evaluate(Cfg(lab, **d))
        sens[lab] = {"C1_assist_min_Nm": e["C1_assist_min_Nm"], "C2_margin_L1": e["C2_L1"]["margin_7V4"], "C2_margin_L2": e["C2_L2"]["margin_7V4"],
                     "C1_pass": e["C1_pass"], "C2_pass": bool(e["C2_L1"]["pass"] and e["C2_L2"]["pass"])}
    out["sensitivity"] = sens

    # 7. component static margins at the design jam
    a_, b_ = 9.0 - 2.0, 9.0 - 2.5         # link plane to bearing A / B centre (mm) ~ half eye 2 + web 2 + half bearing (ASSUMED layout)
    RA, RB = F_jam * b_ / (a_ + b_), F_jam * a_ / (a_ + b_)
    out["jam_component_margins"] = {
        "F_link_N": F_jam,
        "bearing_A_NB701": {"P0_N": round(RA, 1), "s0": round(CRANK_BEARINGS["A_NB701"][3] / RA, 2)},
        "bearing_B_6800": {"P0_N": round(RB, 1), "s0": round(CRANK_BEARINGS["B_6800"][3] / RB, 2)},
        "guide_MGN09H": {"M_Nm": round(F_jam * y_l * 1e-3, 2), "s0": gsel["MGN09H"]["s0_M_jam"],
                         "side_load_N": round(F_jam * math.tan(psi_of(phi_c)), 1), "s0_side": round(gH["C0_N"] / (F_jam * math.tan(psi_of(phi_c))), 1)},
        "stem_3mm_tension_MPa": round(F_jam / A_STEM, 1),
        "stem_M3_thread_tensile_MPa": round(F_jam / 5.03, 1),
        "carriage_internal_thread_shear_MPa": round(F_jam / (math.pi * 3.0 * 4.5 * 0.6), 1),
        "link_pin_double_shear_MPa": eyes["plain_3mm_DU"]["pin_double_shear_jam_MPa"],
        "eye_bearing_pressure_MPa": eyes["plain_3mm_DU"]["bearing_pressure_jam_MPa"],
        "crank_pin_bending_MPa": round(F_jam * (4.0 + 2.0) / 4.0 / (math.pi * 3.0 ** 3 / 32.0), 1),
        "allowables": "17-4PH H1150 Fty 724 MPa (engmat) / H900 ~1170 MPa (AS RECALLED, TO-VERIFY per MMPDS): every stress above is <= 0.25 Fty(H1150) "
                      "except the crank-pin bending (3 mm pin, span 6 mm simply supported, conservative): 0.64 Fty(H1150) / 0.40 Fty(H900) -> pin in "
                      "H900; exceptional load case checked to yield (no ultimate factor applied: parts replaced after any jam)",
        "rule": "any recorded pintle jam -> bearing A, the MGN09H block and the link pins replaced before the next flight (BOM note)"}

    # 8. seat break-out (self-locking 15 deg wedge) at MEOP, final configuration
    al = math.radians(ALPHA_DEG)
    P_close = (7.0e6 - PA) * 1e-6 * (A_SEAT - A_STEM)
    bo = {}
    for mu_s in (0.0, 0.3, 0.4, 0.5, 0.6):
        F_ax = (1 + SPRING["tol"]) * SPRING["T0_Nm"] / dx0 + P_close
        F_w = max(0.0, F_ax * (mu_s * math.cos(al) - math.sin(al)) / (math.sin(al) + mu_s * math.cos(al)))
        F_req = P_close + F_w + final.f_seal + final.S
        mg = final.mu_g * g_of(phi_c, final.y_l, final.s_eff)
        T = (1 + SPRING["tol"]) * SPRING["T0_Nm"] + F_req * dx0 / (1 - mg) + final.mu_p * F_req * final.r_p * 1e-3 * pin_factor(phi_c)
        bo[f"mu_seat_{mu_s:.1f}"] = {"F_wedge_N": round(F_w, 1), "T_crack_Nm": round(T, 3), "margin_7V4": round(HV69["stall_Nm"]["7.4"] / T, 2)}
    out["seat_breakout_MEOP"] = {"rows": bo, "P_closing_seated_N": round(P_close, 1),
                                 "method": "F_wedge = F_ax (mu cos a - sin a)/(sin a + mu cos a), F_ax = +10 % spring hold + seated pressure; servo "
                                           "torque at crack = +10 % spring + (pressure + wedge + seal + S) dx/dphi / (1 - guide) + pins",
                                 "combustion_ref_rolling_T0.25": {"mu_0.0": 2.14, "mu_0.3": 2.01, "mu_0.4": 1.75, "mu_0.5": 1.6, "mu_0.6": 1.49}}

    # 9. MECO close estimate (as v2.2, with the v2.3 assist)
    om = 60.0 / 0.11
    lift_map = {"F75_P3.5MPa": (1.679, "P3.5MPa"), "F100_P3.5MPa": (2.981, "P3.5MPa"), "F75_P5.5MPa": (1.181, "P5.5MPa"), "F100_P5.5MPa": (1.775, "P5.5MPa")}
    meco = {}
    for nm, (x0, Pk) in lift_map.items():
        dphi_ = phi_at_lift(x0) - phi_at_lift(0.20)
        asst = out["baseline"]["C1_assist_min_Nm"][Pk]
        w = om * (1.0 + max(0.0, asst) / HV69["stall_Nm"]["7.4"])
        meco[nm] = {"crank_deg": round(dphi_, 1), "assist_Nm": asst, "t_s_estimate": round(dphi_ / w + 0.02, 3)}
    out["meco_close_estimate"] = {"rows": meco, "basis": "HV69 0.11 s/60 deg at 7.4 V raised along the torque-speed line by the -10 % spring assist "
                                                         "(L0), + 20 ms ASSUMED dead time; Combustion owns the thrust lag"}

    # 10. HV69 travel gate fallbacks: crank radius growth and a jackshaft (gear ratio n_j: travel x n_j, torque / n_j)
    rs = []
    r0 = CRANK["r"]
    for r in (3.0, 3.25, 3.5, 3.75, 4.0):
        CRANK["r"] = r
        ps = phi_at_lift(CRANK["x_stop"])
        e = evaluate(final, n_full=80)
        rs.append({"r_mm": r, "travel_cmd_deg": round(ps - CRANK["phi_cmd_closed"], 1), "seat_load_nom_N": e["seat_load_N"]["nominal"],
                   "C1_assist_MEOP_Nm": e["C1_assist_min_Nm"]["MEOP"], "C2_margin_L1": e["C2_L1"]["margin_7V4"], "C2_margin_L2": e["C2_L2"]["margin_7V4"],
                   "F_jam_7V6_N": round((stall(7.6) - 0.9 * SPRING["T0_Nm"]) / (dxdphi(15.0) * 1e-3), 1)})
    CRANK["r"] = r0
    jk = []
    base_m = min(out["baseline"]["C2_L1"]["margin_7V4"], out["baseline"]["C2_L2"]["margin_7V4"])
    for th in (90.0, 95.0, 100.0):
        nj = out["crank"]["travel_cmd_deg"] / th
        jk.append({"HV69_travel_deg": th, "ratio_n_j": round(nj, 3), "C2_margin_min": round(base_m / nj, 2), "pass_1p5": bool(base_m / nj >= 1.5)})
    out["travel_gate_fallbacks"] = {"crank_radius_study": rs, "jackshaft": jk,
                                    "note": "spring held at 0.25 + 0.12 (seat load and assist change with r); jackshaft = HV69 on a parallel shaft "
                                            "with a gear/lever ratio n_j > 1 driving the crank: +1 bearing pair, zone length +~12 mm (ESTIMATE) - "
                                            "sketch level; B-PNT-1 measures the HV69 travel first (GATING)"}
    # 11. filter
    out["filter_OI7_C5"] = filter_screen()
    out["open_items"] = ["B-PNT-1: guide drag S and mu (end seals), needle force vs lift, break-out after a dwell at MEOP, HV69 travel >= 103 deg",
                         "HIWIN MGN temperature limit vs head-top soak (servo-mount thermal network)",
                         "DU-class bush static limit and dry-N2O-compatible lubrication (outside the wetted path) - maker data",
                         "filter element dP-flow curve (maker), O2 cleaning level (Combustion)",
                         "Electronics: confirm the pintle-rail upper tolerance (7.6 V used) and the jam detection time"]
    (HERE / "pintle_inline_v34_v2p3.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("validation_vs_combustion",)}, default=float)[:600])
    print("fits", json.dumps(fits))
    print("jam", json.dumps(out["jam"]["by_rail_voltage"]))
    print("eyes", json.dumps(eyes, default=float)[:1500])
    print("guide", json.dumps(gsel))
    b = out["baseline"]
    print("BASELINE C1", b["C1_assist_min_Nm"], b["C1_pass"], "C2 L1", b["C2_L1"], "L2", b["C2_L2"], "unlit", b["unlit_full_stroke_3p5MPa_margin_7V4"], b["seat_load_N"])
    for k, v in sens.items():
        print("SENS", k, v)
    print("jam margins", json.dumps(out["jam_component_margins"])[:900])
    print("breakout", json.dumps(bo))
    print("meco", json.dumps(meco))
    for r in rs:
        print("r", r)
    print("jack", jk)
    print("filter", json.dumps(out["filter_OI7_C5"]["units"], indent=0))


if __name__ == "__main__":
    main()
