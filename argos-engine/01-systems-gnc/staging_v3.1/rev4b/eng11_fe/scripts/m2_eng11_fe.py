"""m2_eng11_fe v1.0 (GNC rev4b, 2026-10-19): ENG-11 K_s window re-run on the 3D FE plant of CAD v3.5.1, per REV-GNC-6
RV6-14 (a)-(e) and lead CHANGELOG 227 (3) / (10).  Linear CSI margins, DERIVED; staged apart from the v3.2 text.

Question: does the design-to window 100 <= K_s <= 130 N m/rad (RV6-01 text, V5c plant, CAD v3.3) hold on the FE plant,
and what is the window for each J and structure, with the corners that set it?

Model, conditions, notch rule, metric and corner set are m2_eng11 v1.1 (imported unchanged, not copied): pitch-plane loop
(m2_csi.loop_flex) with the engine rocking mode in the actuator path, floor20 conditions on GNC_IFACE = iface_v351 with the
v351 cfg ballast, fixed ECU notch Q 1 / -12 dB at e x the landing-state centre-pose mode (e 0.95 / 1 / 1.05, B-TVC-1
measurement error), mount damping zeta 0.02 / 0.05 / 0.10; ENG-07d = closed loop stable and upper GM >= 6 dB at every
corner.  Continuous pose envelope exactly as REV-GNC-6 v05 part B: the loop depends on (f, zeta) only and f moves
continuously with the gimbal angle (continuity ASSUMED), so every f in [pose min, pose max] of each condition is
evaluated (0.1 Hz grid + the pose values + 0.02 Hz within +/-1 Hz of the condition's bending frequency).
  f = sqrt(K_tot / (I_piv + J_refl)) / 2 pi,  K_tot = 1 / (1/S + 1/(K_s g)),  J_refl = J g ('cons') or J n^2 ('n48').
Plant inputs (all read-only):
  S(p, a)  (a) structure + rod chain, servo output rigid: FE K_FE_engine of CAD v3.5.1 at the 9 range-cone poses (centre +
           8 at 7 deg, k_cone_c71.json; the same (alpha, beta) as the V5c poses) and the 8 conical-stop poses at 8 deg
           (k_stop_c71.json); V5c mech_T (CAD v3.3) as the anchor.  Compliant airframe: a pose-independent airframe
           rotational spring K_af in series, fitted to the only compliant FE run (stop045: -14 / -13 %) (ASSUMED
           pose-independent).  Hot E: S x 0.95 / 0.90 (REPORT-FEA3D 9A: 6061 E -5 to -10 % at 120-150 degC; applied to the
           whole S, ASSUMED, as REV-GNC-6 v09); the airframe spring is not heated.
  g(p, a)  servo kinematic factor (engine-side servo stiffness per unit K_s).  Primary: m2_eng11's V5c g (Mechanical's FE
           series split), which equals the exact CAD linkage kinematics (03-cad/src/tvc_kinematics.py solve_psi,
           sum_i (d psi_i / d theta_a)^2, horn crank included) within the check below; at the 8 deg stops the exact
           CAD kinematics.  Variants: exact CAD kinematics on the cone ('kin'); FEA3D's post_k factor ('fea': rod arm
           over the full horn radius, horn normal to the rod at every pose, as in REPORT 9 'with servo' columns).
  I_piv    (b) of each flight condition, as now (0.059436 full / 0.058823 landing kg m2; FE modal 0.0585 / 0.0590).
  J        (c) 0.76 / 1.6 / 2.7e-3 kg m2 at the servo output shaft (Electronics SB-2292SG, DERIVED, ASSUMED), 'cons'
           and 'n48'; rotor-placement bracket: 'J0' (rotor held by a stiff servo loop, K_s in the gear train: the rotor
           is not in the rocking mode) and the two-mass chain 'tm' (rotor at the servo output between the servo spring
           K_s g and the structure S: command -K_s g- rotor J g -S- engine I_piv; first mode below, exact 13-state loop,
           modal damping zeta on both modes; envelope sampled on the pose skeleton: 8 radial segments from the centre and
           the 8 cone arcs, (S, g) linear between poses, ASSUMED).
  bending  (d) m2_csi uniform PETG tube (E 2.0 GPa ASSUMED) 24.30 Hz full / 25.64 Hz landing, x 0.9 / 1.0 / 1.1.
  K_s      (e) 90-160 N m/rad in 5 N m/rad steps.
Notch reference: the ECU notch is fixed for the flight from B-TVC-1; it is placed (+/-5 %) on the centre-pose landing-state
mode of the BENCH plant = the FE structure at T_REF on a rigid fixture (ASSUMED bench condition) with the variant's J,
kinematics and rotor model; the hot / compliant variants therefore fly with the bench notch ('bench'); 'own' re-references
the notch on the variant's own structure (m2_eng11 / REV-GNC-6 convention) and is run once for comparison.
Pass / fail per (axis, K_s): every corner evaluated for a PASS (minimum GM reported); a FAIL stops at the first failing
corner (corners ordered: full-tank zeta 0.02 near the bending frequency first, then the pose minimum at zeta 0.10) and then
completes that corner's (condition, e, zeta) block for its worst GM.
DERIVED (linear) from SIM FE stiffness and SIM / DATASHEET-derived inputs; K_s, J, bending, damping ASSUMED until B-TVC-1
and the airframe measurement; no hardware data; not physical approval.
Usage (env): GNC_E11FE_PART=check|run|summary, GNC_E11FE_VARIANTS=A01,A02,... (run), GNC_E11FE_OUT=<dir>;
needs GNC_IFACE=iface_v351 and GNC_E11_MASS=v351 (m2_eng11 conditions)."""
import hashlib
import importlib.util
import json
import math
import os
import sys
import time

import numpy as np
import control as ct

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_eng11 as E  # noqa: E402
import m2_csi as C  # noqa: E402
import m2_csi_v3 as V3  # noqa: E402

VERSION = "m2_eng11_fe v1.0"
HUB = E.HUB
FEA = f"{HUB}/04-fea/assembly3d"
K_CONE = f"{FEA}/results/k_cone_c71.json"
K_STOP = f"{FEA}/results/k_stop_c71.json"
K_NEU = f"{FEA}/results/k_pose_neutral_c71.json"
K_COMP = f"{FEA}/results/k_stop045_compliant_c71.json"
K_RANGE = f"{FEA}/results/k_range_v351.json"
MODAL = f"{FEA}/results/modal_summary_v351.json"
REPORT = f"{FEA}/REPORT-FEA3D.md"
TVCK = f"{HUB}/03-cad/src/tvc_kinematics.py"
CADCFG = f"{HUB}/03-cad/src/config.py"
V05 = f"{HUB}/reviews/gnc/rev4/results/v05_eng11_env.json"
V09 = f"{HUB}/reviews/gnc/rev4/results/v09_fe_plant.json"
OUT = os.environ.get("GNC_E11FE_OUT", "/home/claude/work/space/out/rev4b/eng11_fe")
PART = os.environ.get("GNC_E11FE_PART", "check")
AXES = E.AXES
KS = tuple(float(k) for k in range(90, 161, 5))
JV = dict(J_C=E.J_C, J_LO=E.J_LO, J_HI=E.J_HI, J0=0.0)
NOTCH = ("fixed", 1.0) + E.NOTCH_ECU
CONE = ("centre", "alphap7", "alpham7", "betap7", "betam7", "cone7_045", "cone7_135", "cone7_225", "cone7_315")
STOPS = ("stop000", "stop045", "stop090", "stop135", "stop180", "stop225", "stop270", "stop315")
V5C2FE = {"centre": "neutral", "alphap7": "alpha+", "alpham7": "alpha-", "betap7": "beta+", "betam7": "beta-",
          "cone7_045": "combined045", "cone7_135": "combined135", "cone7_225": "combined225", "cone7_315": "combined315"}
# perimeter order of the 7 deg cone poses (FE azimuth 0, 45, ..., 315 deg: alpha = -r sin(phi), beta = r cos(phi))
RING = ("betap7", "cone7_045", "alpham7", "cone7_135", "betam7", "cone7_225", "alphap7", "cone7_315")
# CAD TVC linkage parameters (03-cad/src/config.py put() values, CAD v3 servo position; FEA3D asm3d: servo / horn / lever
# eyes identical in v3.5.1): servo box 40.3 x 20.2 x 40.3 mm (electronics body, H reserved), bay ID 140 mm, wall gap 1.25 mm,
# horn r_h 11.139 mm (lead 2026-10-12, n 4.80), shaft z -70.3 mm, lever z -28 mm, eye offset 9.5 mm, levers at 135 / 225 deg.
CAD_P = {"tvc_servo_box": {"v": [0.0403, 0.0202, 0.0403]}, "engine_bay_ID": {"v": 0.140}, "tvc_wall_gap_mm": {"v": 1.25},
         "tvc_horn_r": {"v": 0.011139}, "tvc_shaft_z": {"v": -0.0703}, "tvc_lever_z": {"v": -0.028},
         "tvc_eye_offset_mm": {"v": 9.5}, "tvc_lever_phi_deg": {"v": [135.0, 225.0]}}

# variant id -> spec.  struct V5c | FE; poses cone | cone+stop; air rigid | compliant; hot 1 / 0.95 / 0.90; g v5c | kin | fea;
# J key; kin cons | n48; model lumped | tm; wb bending scale; notch bench | own.
_B = dict(struct="FE", poses="cone", air="rigid", hot=1.0, g="v5c", J="J_C", kin="cons", model="lumped", wb=1.0, notch="bench")
VARIANTS = {
    "A01": dict(_B),
    "A02": dict(_B, J="J_LO"),
    "A03": dict(_B, J="J_HI"),
    "A04": dict(_B, hot=0.95),
    "A05": dict(_B, hot=0.90),
    "A06": dict(_B, air="compliant"),
    "A07": dict(_B, air="compliant", hot=0.90),
    "A07o": dict(_B, air="compliant", hot=0.90, notch="own"),
    "A08": dict(_B, poses="cone+stop"),
    "A09": dict(_B, air="compliant", hot=0.90, J="J_LO"),
    "A10": dict(_B, air="compliant", hot=0.90, J="J_HI"),
    "A11": dict(_B, poses="cone+stop", air="compliant", hot=0.90),
    "A12": dict(_B, struct="V5c", notch="own"),
    "B01": dict(_B, kin="n48"),
    "B02": dict(_B, J="J_LO", kin="n48"),
    "B03": dict(_B, J="J_HI", kin="n48"),
    "B04": dict(_B, g="fea"),
    "B05": dict(_B, g="kin"),
    "B06": dict(_B, J="J0"),
    "B07": dict(_B, model="tm"),
    "C01": dict(_B, wb=0.9),
    "C02": dict(_B, wb=1.1),
    "C03": dict(_B, struct="V5c", notch="own", wb=0.9),
    "C04": dict(_B, struct="V5c", notch="own", wb=1.1),
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def jdump(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, path)


# ------------------------------------------------------------------------------------------------------------- inputs
def fe_runs():
    out = {}
    for fn in (K_CONE, K_STOP):
        for r in json.load(open(fn))["runs"]:
            nm = r["variant"]["posename"]
            ax = {}
            for key, v in r["axes"].items():
                a = "alpha" if key.startswith("alpha") else "beta"
                ss = v["servo_series"]
                ax[a] = dict(K=float(v["K_FE_engine_Nm_per_rad"]), K_noz=float(v["K_FE_nozzle_Nm_per_rad"]),
                             g_fea=float(ss["k_s58_engine"]["K_servo_engine_Nm_per_rad"]) / 58.0,
                             g_fea174=float(ss["k_s174_engine"]["K_servo_engine_Nm_per_rad"]) / 174.0,
                             share=float(v["structure_compliance_share"]), K_rods=float(v["K_rods_only_Nm_per_rad"]))
            out[nm] = dict(pose_deg=[float(x) for x in r["pose_deg"]], run=r["run"], airframe=r["variant"]["airframe"], axes=ax)
    rn = json.load(open(K_NEU))["runs"][0]
    neu_same = all(abs(float(v["K_FE_engine_Nm_per_rad"]) - out["neutral"]["axes"]["alpha" if k.startswith("alpha") else "beta"]["K"]) < 1e-6
                   for k, v in rn["axes"].items())
    rc = json.load(open(K_COMP))["runs"][0]
    comp = {("alpha" if k.startswith("alpha") else "beta"): float(v["K_FE_engine_Nm_per_rad"]) for k, v in rc["axes"].items()}
    kaf = {a: 1.0 / (1.0 / comp[a] - 1.0 / out["stop045"]["axes"][a]["K"]) for a in AXES}
    return out, dict(neutral_file_equal_cone_neutral=neu_same, compliant_stop045=comp, K_af=kaf,
                     compliant_ratio={a: comp[a] / out["stop045"]["axes"][a]["K"] for a in AXES})


_KIN = {}


def kin_module():
    if "m" not in _KIN:
        spec = importlib.util.spec_from_file_location("tvc_kinematics_ro", TVCK)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _KIN["m"] = m
        _KIN["g"] = m.geometry(CAD_P)
    return _KIN["m"], _KIN["g"]


def kin_factor(alpha, beta, h=1e-3):
    """Exact CAD linkage: J_ia = d psi_i / d theta_a by central differences of solve_psi (alpha about the fixed X axis, beta
    about the ring Y axis, R = Rx(alpha) Ry(beta)); g_a = sum_i J_ia^2 (diagonal, other axis held) and the free-axis value."""
    m, g = kin_module()

    def ps(a, b):
        return np.array([m.solve_psi(g, sv, a, b)[0] for sv in g["servos"]])
    Ja = (ps(alpha + h, beta) - ps(alpha - h, beta)) / (2 * h)
    Jb = (ps(alpha, beta + h) - ps(alpha, beta - h)) / (2 * h)
    Jm = np.vstack([Ja, Jb]).T
    Kn = Jm.T @ Jm
    Cm = np.linalg.inv(Kn)
    return dict(alpha=float(Kn[0, 0]), beta=float(Kn[1, 1]), free_alpha=float(1.0 / Cm[0, 0]), free_beta=float(1.0 / Cm[1, 1]),
                psi_deg=[round(float(x), 3) for x in ps(alpha, beta)])


class Ctx:
    """Inputs shared by all variants (read once)."""

    def __init__(self):
        self.d5, self.T5, self.n_m, self.gchk = E.v5c_table()
        self.conds0, self.meta, self.src, self.extra, self.cchk = E.conditions()
        self.FE, self.fe_chk = fe_runs()
        self.kin = {}
        for p in CONE:
            a5, b5 = self.T5[(p, "alpha")]["alpha_deg"], self.T5[(p, "alpha")]["beta_deg"]
            fa, fb = self.FE[V5C2FE[p]]["pose_deg"]
            self.kin[p] = kin_factor(fa, fb)
            self.kin[p]["pose_V5c_deg"] = [a5, b5]
        for p in STOPS:
            fa, fb = self.FE[p]["pose_deg"]
            self.kin[p] = kin_factor(fa, fb)
        self.wb = None
        self.conds = None
        self.set_wb(1.0)

    def set_wb(self, s):
        if self.wb == s:
            return
        self.conds = {k: dict(v, w_b=v["w_b"] * s) for k, v in self.conds0.items()} if s != 1.0 else self.conds0
        E._CACHE.clear()
        E._RCACHE.clear()
        _TMC.clear()
        self.wb = s

    def pose_list(self, spec):
        return CONE + (STOPS if spec["poses"] == "cone+stop" else ())

    def table(self, spec, bench=False):
        """T[(p, a)] = dict(S=dict(T=S), g=g) for the variant (bench=True: T_REF, rigid fixture, cone poses)."""
        T = {}
        poses = CONE if bench else self.pose_list(spec)
        hot = 1.0 if bench else spec["hot"]
        air = "rigid" if bench else spec["air"]
        for p in poses:
            for a in AXES:
                if spec["struct"] == "V5c":
                    S = self.T5[(p, a)]["S"]["T"]
                    g = self.T5[(p, a)]["g"]
                else:
                    fe = self.FE[V5C2FE.get(p, p)]["axes"][a]
                    Sr = hot * fe["K"]
                    S = Sr if air == "rigid" else 1.0 / (1.0 / Sr + 1.0 / self.fe_chk["K_af"][a])
                    if spec["g"] == "fea":
                        g = fe["g_fea"]
                    elif spec["g"] == "kin" or p not in V5C2FE:
                        g = self.kin[p][a]
                    else:
                        g = self.T5[(p, a)]["g"]
                T[(p, a)] = dict(S=dict(T=float(S)), g=float(g))
        return T


# ------------------------------------------------------------------------------------------------- two-mass chain
_TMC = {}


def tm_modes(k1, k2, m1, m2):
    Mm = np.diag([m1, m2])
    Kk = np.array([[k1 + k2, -k2], [-k2, k2]])
    w2, ph = np.linalg.eig(np.linalg.solve(Mm, Kk))
    o = np.argsort(w2.real)
    w = np.sqrt(w2.real[o])
    ph = ph[:, o].real
    return w, ph


def loop_flex_tm(case, k1, k2, m1, zr):
    """m2_csi.loop_flex with the rotor as a second DOF: servo output d_s (2nd order, delayed command) -k1- rotor d_r (m1)
    -k2- engine d_e (I_piv); modal damping zeta on both modes, damping on velocities relative to d_s; thrust, tail-wags-dog,
    slosh and bending use d_e as in loop_flex.  States [th, th', eta, eta', qb, qb', d_s, d_s', int, d_e, d_e', d_r, d_r']."""
    It, F, lp, Jt, ms, mr, ws, zs, rs, Ma = (case[k] for k in ["It", "F", "lp", "Jtwd", "m_s", "m_r", "w_s", "z_s", "r_s", "M_alpha"])
    wb, zb, phig, sig, Mb = (case[k] for k in ["w_b", "z_b", "phi_g", "sigma_imu", "M_b"])
    wa, za, tau = case["w_a"], case["z_a"], case["tau"]
    wn, z, Ki = case["wn"], case["zeta"], case["Ki"]
    m2 = case["I_piv"]
    Mm = np.diag([m1, m2])
    Kk = np.array([[k1 + k2, -k2], [-k2, k2]])
    w2, U = np.linalg.eigh(np.diag(1 / np.sqrt([m1, m2])) @ Kk @ np.diag(1 / np.sqrt([m1, m2])))
    Phi = np.diag(1 / np.sqrt([m1, m2])) @ U            # mass-normalised: Phi^T M Phi = I
    om = np.sqrt(np.maximum(w2, 0.0))
    Cc = Mm @ Phi @ np.diag(2.0 * zr * om) @ Phi.T @ Mm
    n = 13
    eye = np.eye(n)
    disp = np.vstack([eye[11] - eye[6], eye[9] - eye[6]])
    vel = np.vstack([eye[12] - eye[7], eye[10] - eye[7]])
    acc = np.diag([1.0 / m1, 1.0 / m2]) @ (-Kk @ disp - Cc @ vel)
    a_r, a_de = acc[0], acc[1]
    A = np.zeros((n, n))
    B = np.zeros((n, 1))
    a_th = np.zeros(n)
    a_th[0] += Ma / It
    a_th[2] += rs * ms * ws ** 2 / It
    a_th[3] += rs * ms * 2 * zs * ws / It
    a_th[9] += -F * lp / It
    a_th -= Jt * a_de / It
    a_eta = np.zeros(n)
    a_eta[2] = -ws ** 2 - ms * ws ** 2 / mr
    a_eta[3] = -2 * zs * ws - ms * 2 * zs * ws / mr
    a_eta[9] = -F / mr
    a_eta -= rs * a_th
    A[0, 1] = 1.0
    A[1, :] = a_th
    A[2, 3] = 1.0
    A[3, :] = a_eta
    A[4, 5] = 1.0
    A[5, 4] = -wb ** 2
    A[5, 5] = -2 * zb * wb
    A[5, 9] = phig * F / Mb
    A[6, 7] = 1.0
    A[7, 6] = -wa ** 2
    A[7, 7] = -2 * za * wa
    B[7, 0] = wa ** 2
    A[8, 0] = -1.0
    A[9, 10] = 1.0
    A[10, :] = a_de
    A[11, 12] = 1.0
    A[12, :] = a_r
    k0 = -It / (F * lp)
    Cm = np.zeros((1, n))
    Cm[0, 0] = k0 * (-wn ** 2)
    Cm[0, 1] = k0 * (-2 * z * wn)
    Cm[0, 5] = k0 * (-2 * z * wn) * sig
    Cm[0, 8] = k0 * Ki
    P = ct.ss(A, B, Cm, np.zeros((1, 1)))
    num, den = ct.pade(tau, 3)
    return -ct.series(ct.tf(num, den), P)


def ev_tm(cn, cond, k1, k2, m1, zr, notch):
    key = (cn, round(k1, 4), round(k2, 3), round(m1, 9), zr, None if notch is None else tuple(round(x, 6) for x in notch))
    if key in _TMC:
        return _TMC[key]
    c = dict(cond)
    L = ct.series(C.cmd_filter(c), loop_flex_tm(c, k1, k2, m1, zr))
    if notch is not None:
        L = ct.series(V3.notch_tf(*notch), L)
    gm_up, gm_lo, pm_min, sm, pm_abs = E.margins(L)
    stable = bool(np.all(np.real(ct.poles(ct.feedback(L, 1))) < 0))
    r = (stable, gm_up, pm_min, bool(stable and (gm_up is None or gm_up >= 6.0)), pm_abs, sm)
    _TMC[key] = r
    return r


def tm_f1(S, g, Ks, J, Ip):
    w, ph = tm_modes(Ks * g, S, max(J * g, 1e-12), Ip)
    return float(w[0] / (2 * np.pi)), float(w[1] / (2 * np.pi)), float(ph[0, 0] / ph[1, 0])


def skeleton(T, a, n_int=3):
    """Pose skeleton for the two-mass envelope: the 9 cone poses, n_int interior points on each radial segment centre ->
    cone pose and on each cone arc between neighbours; (S, g) linear between the end poses (ASSUMED)."""
    pts = [(p, T[(p, a)]["S"]["T"], T[(p, a)]["g"]) for p in CONE]
    ts = [(k + 1) / (n_int + 1) for k in range(n_int)]
    c = T[("centre", a)]
    for p in RING:
        q = T[(p, a)]
        for t in ts:
            pts.append((f"centre-{p}@{t:.2f}", (1 - t) * c["S"]["T"] + t * q["S"]["T"], (1 - t) * c["g"] + t * q["g"]))
    for i, p in enumerate(RING):
        p2 = RING[(i + 1) % len(RING)]
        q1, q2 = T[(p, a)], T[(p2, a)]
        for t in ts:
            pts.append((f"{p}-{p2}@{t:.2f}", (1 - t) * q1["S"]["T"] + t * q2["S"]["T"], (1 - t) * q1["g"] + t * q2["g"]))
    return pts


# ----------------------------------------------------------------------------------------------------- envelopes
def _block_worst(evalf, cn, e, zr, fs):
    worst = None
    for f_r in fs:
        st, gm, pm, ok, pma, sm = evalf(f_r)
        g = gm if st else -99.0
        if g is not None and (worst is None or g < worst[0]):
            worst = (g, f_r)
    return worst


def env_lumped(ctx, M, Mb, a, Ks, J, kin, early=True, step=0.1, fine=0.02, near=1.0):
    """REV-GNC-6 v05 envelope for one (axis, K_s); notch from the bench model Mb (landing-state centre pose)."""
    t0 = time.time()
    fn_c = Mb.f("centre", a, Ks, J, kin, "T")
    corners, frng = [], {}
    for cn, cond in M.conds.items():
        if E.is62(cn):
            continue
        fp = [M.f(p, a, Ks, J, kin, "T", Ip=cond["I_piv"]) for p in M.poses]
        lo, hi = min(fp), max(fp)
        fb = cond["w_b"] / (2 * np.pi)
        grid = set(np.round(np.arange(lo, hi + 1e-9, step), 4).tolist()) | set(np.round(fp, 6).tolist())
        grid |= set(np.round(np.arange(max(lo, fb - near), min(hi, fb + near) + 1e-9, fine), 4).tolist())
        grid = sorted(x for x in grid if lo - 1e-9 <= x <= hi + 1e-9)
        frng[cn] = dict(lo=lo, hi=hi, fb=fb, grid=grid, argmin=M.poses[int(np.argmin(fp))], argmax=M.poses[int(np.argmax(fp))])
        for e in E.ERRS:
            for zr in E.ZETAS:
                for f_r in grid:
                    pr = 0 if (cn.startswith("full") and zr == 0.02 and abs(f_r - fb) <= 0.6) else (1 if (f_r == grid[0] and zr == 0.10) else 2)
                    corners.append((pr, cn, e, zr, f_r))
    corners.sort(key=lambda x: x[0])
    worst, n, first_fail, pma_min, sm_min, nbad = None, 0, None, None, None, 0
    for pr, cn, e, zr, f_r in corners:
        nt = (NOTCH[1] * e * fn_c, NOTCH[2], NOTCH[3])
        st, gm, pm, ok, pma, sm = E.ev(cn, M.conds[cn], float(f_r), zr, nt)
        n += 1
        g = gm if st else -99.0
        if g is not None and (worst is None or g < worst[0]):
            worst = (g, cn, f_r, e, zr)
        if st and pma is not None and (pma_min is None or pma < pma_min):
            pma_min = pma
        if st and (sm_min is None or sm < sm_min):
            sm_min = sm
        if not ok:
            nbad += 1
            if first_fail is None:
                first_fail = (cn, f_r, e, zr, None if not st else gm, st)
            if early:
                break
    complete = (n == len(corners))
    blk = None
    if first_fail is not None and not complete:
        cn, f_r, e, zr = first_fail[:4]
        nt = (NOTCH[1] * e * fn_c, NOTCH[2], NOTCH[3])
        w = _block_worst(lambda ff: E.ev(cn, M.conds[cn], float(ff), zr, nt), cn, e, zr, frng[cn]["grid"])
        blk = dict(block=f"{cn}|e{e:g}|z{zr:g}", worst_gm_dB=round(w[0], 3), at_f_Hz=round(w[1], 3))
    res = dict(pass_6dB=(first_fail is None and complete), complete=complete, n_eval=n, n_corners=len(corners),
               n_below_6dB=(nbad if complete else None),
               gm_up_min_dB=(round(worst[0], 3) if (worst and complete) else None),
               worst=(f"{worst[1]}|f{worst[2]:.3f}|e{worst[3]:g}|z{worst[4]:g}" if (worst and complete) else None),
               first_fail=(None if first_fail is None else f"{first_fail[0]}|f{first_fail[1]:.3f}|e{first_fail[2]:g}|z{first_fail[3]:g}|"
                           + ("UNSTABLE" if not first_fail[5] else f"GM{first_fail[4]:.3f}")),
               fail_block_worst=blk, pm_abs_min_deg=(round(pma_min, 2) if (pma_min is not None and complete) else None),
               sm_min=(round(sm_min, 4) if (sm_min is not None and complete) else None), notch_ref_Hz=round(fn_c, 4),
               f_full_Hz=[round(frng[k]["lo"], 3), round(frng[k]["hi"], 3)] if (k := next(x for x in frng if x.startswith("full"))) else None,
               f_full_argminmax=[frng[k]["argmin"], frng[k]["argmax"]],
               f_land_Hz=[round(min(v["lo"] for c_, v in frng.items() if c_.startswith("landing")), 3),
                          round(max(v["hi"] for c_, v in frng.items() if c_.startswith("landing")), 3)],
               t_s=round(time.time() - t0, 1))
    if res["pass_6dB"]:
        res["rigid_with_lowest_notch"] = E.ev_rigid(M.conds, (NOTCH[1] * min(E.ERRS) * fn_c, NOTCH[2], NOTCH[3]))
    return res


def env_tm(ctx, T, Tb, a, Ks, J, early=True):
    """Two-mass envelope on the pose skeleton (exact 13-state loop at every skeleton point)."""
    t0 = time.time()
    Ip_land = ctx.conds["landing|hover|act_nom|noaero"]["I_piv"]
    cb = Tb[("centre", a)]
    fn_c = tm_f1(cb["S"]["T"], cb["g"], Ks, J, Ip_land)[0]
    pts = skeleton(T, a)
    corners, f1r = [], {}
    for cn, cond in ctx.conds.items():
        if E.is62(cn):
            continue
        fb = cond["w_b"] / (2 * np.pi)
        f1s = []
        for lab, S, g in pts:
            f1, f2, r = tm_f1(S, g, Ks, J, cond["I_piv"])
            f1s.append((f1, f2, lab))
            for e in E.ERRS:
                for zr in E.ZETAS:
                    pr = 0 if (cn.startswith("full") and zr == 0.02 and abs(f1 - fb) <= 0.6) else 2
                    corners.append((pr, cn, e, zr, lab, S, g, f1))
        f1r[cn] = dict(lo=min(x[0] for x in f1s), hi=max(x[0] for x in f1s), f2_lo=min(x[1] for x in f1s), f2_hi=max(x[1] for x in f1s))
    corners.sort(key=lambda x: x[0])
    worst, n, first_fail, pma_min, sm_min, nbad = None, 0, None, None, None, 0
    for pr, cn, e, zr, lab, S, g, f1 in corners:
        nt = (NOTCH[1] * e * fn_c, NOTCH[2], NOTCH[3])
        st, gm, pm, ok, pma, sm = ev_tm(cn, ctx.conds[cn], Ks * g, S, J * g, zr, nt)
        n += 1
        gv = gm if st else -99.0
        if gv is not None and (worst is None or gv < worst[0]):
            worst = (gv, cn, lab, f1, e, zr)
        if st and pma is not None and (pma_min is None or pma < pma_min):
            pma_min = pma
        if st and (sm_min is None or sm < sm_min):
            sm_min = sm
        if not ok:
            nbad += 1
            if first_fail is None:
                first_fail = (cn, lab, f1, e, zr, gm, st)
            if early:
                break
    complete = (n == len(corners))
    kf = next(x for x in f1r if x.startswith("full"))
    return dict(pass_6dB=(first_fail is None and complete), complete=complete, n_eval=n, n_corners=len(corners),
                n_below_6dB=(nbad if complete else None), gm_up_min_dB=(round(worst[0], 3) if (worst and complete) else None),
                worst=(f"{worst[1]}|{worst[2]}|f1 {worst[3]:.3f}|e{worst[4]:g}|z{worst[5]:g}" if (worst and complete) else None),
                first_fail=(None if first_fail is None else f"{first_fail[0]}|{first_fail[1]}|f1 {first_fail[2]:.3f}|e{first_fail[3]:g}|z{first_fail[4]:g}|"
                            + ("UNSTABLE" if not first_fail[6] else f"GM{first_fail[5]:.3f}")),
                pm_abs_min_deg=(round(pma_min, 2) if (pma_min is not None and complete) else None),
                sm_min=(round(sm_min, 4) if (sm_min is not None and complete) else None), notch_ref_Hz=round(fn_c, 4),
                f1_full_Hz=[round(f1r[kf]["lo"], 3), round(f1r[kf]["hi"], 3)], f2_full_Hz=[round(f1r[kf]["f2_lo"], 2), round(f1r[kf]["f2_hi"], 2)],
                n_skeleton_points=len(pts), t_s=round(time.time() - t0, 1))


# ----------------------------------------------------------------------------------------------- frequency map
BAND_FULL = (24.14, 24.71)       # REV-GNC-6 v09: full-tank rocking frequencies of the failing corners at the nominal bending


def fmap(ctx, spec, Ks_list=KS):
    """Full-tank pose range per K_s (lumped or two-mass first mode) and the K_s at which the pose maximum first reaches the
    coincidence band (band x wb): frequency arithmetic only."""
    T = ctx.table(spec)
    Jv = JV[spec["J"]]
    Ipf = ctx.meta["full"]["I_piv"]
    poses = ctx.pose_list(spec)
    band = (BAND_FULL[0] * spec["wb"], BAND_FULL[1] * spec["wb"])

    def rng(a, Ks):
        fs = []
        if spec["model"] == "tm":
            for lab, S, g in skeleton(T, a):
                fs.append(tm_f1(S, g, Ks, Jv, Ipf)[0])
        else:
            for p in poses:
                t = T[(p, a)]
                Kt = 1.0 / (1.0 / t["S"]["T"] + 1.0 / (Ks * t["g"]))
                Jr = Jv * (t["g"] if spec["kin"] == "cons" else ctx.n_m ** 2)
                fs.append(math.sqrt(Kt / (Ipf + Jr)) / (2 * math.pi))
        return min(fs), max(fs)
    out = {}
    for a in AXES:
        lo, hi = 40.0, 600.0
        if rng(a, lo)[1] >= band[0]:
            edge = lo
        elif rng(a, hi)[1] < band[0]:
            edge = None
        else:
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if rng(a, mid)[1] >= band[0]:
                    hi = mid
                else:
                    lo = mid
            edge = hi
        out[a] = dict(Ks_pose_max_reaches_band=(None if edge is None else round(edge, 1)), band_Hz=[round(band[0], 3), round(band[1], 3)],
                      f_full_range_Hz={f"{k:g}": [round(x, 3) for x in rng(a, k)] for k in Ks_list})
    return out


# ------------------------------------------------------------------------------------------------------------- parts
def inputs_record(ctx):
    files = dict(m2_eng11=E.__file__, m2_eng11_fe=os.path.abspath(__file__), k_cone=K_CONE, k_stop=K_STOP, k_pose_neutral=K_NEU,
                 k_stop045_compliant=K_COMP, k_range=K_RANGE, modal_summary=MODAL, report_fea3d=REPORT, tvc_kinematics=TVCK,
                 cad_config=CADCFG, v5c=E.V5C, mechanical=E.MECH_HUB, rev_gnc6_v05=V05, rev_gnc6_v09=V09)
    return dict(files={k: dict(path=v, sha256_16=sha16(v)) for k, v in files.items()}, iface=os.environ.get("GNC_IFACE"),
                mass_variant=E.MASS_VARIANT, cfg_ballast=ctx.extra, base_version=E.VERSION,
                I_piv=dict(full=ctx.meta["full"]["I_piv"], landing=ctx.meta["landing"]["I_piv"]),
                bending_Hz=dict(full=ctx.meta["full"]["f_bend_Hz"], landing=ctx.meta["landing"]["f_bend_Hz"]))


def part_check(ctx):
    out = dict(version=VERSION, part="check", date=time.strftime("%Y-%m-%d"), inputs=inputs_record(ctx))
    # c1 FE table
    rows = {}
    for nm, r in ctx.FE.items():
        rows[nm] = dict(pose_deg=r["pose_deg"], **{f"{a}_K": round(r["axes"][a]["K"], 1) for a in AXES},
                        **{f"{a}_g_fea": round(r["axes"][a]["g_fea"], 4) for a in AXES},
                        g_fea_k58_equals_k174=all(abs(r["axes"][a]["g_fea"] / r["axes"][a]["g_fea174"] - 1) < 1e-9 for a in AXES))
    out["c1_fe_table"] = dict(rows=rows, **ctx.fe_chk)
    # c2 kinematics: exact CAD linkage vs V5c g (cone) and vs FEA3D post_k g
    m, g = kin_module()
    kc = {}
    for p in CONE + STOPS:
        fe = ctx.FE[V5C2FE.get(p, p)]["axes"]
        row = dict(pose_deg=ctx.FE[V5C2FE.get(p, p)]["pose_deg"], psi_deg=ctx.kin[p]["psi_deg"])
        for a in AXES:
            row[f"g_kin_{a}"] = round(ctx.kin[p][a], 4)
            row[f"g_kin_free_{a}"] = round(ctx.kin[p][f"free_{a}"], 4)
            row[f"g_fea_{a}"] = round(fe[a]["g_fea"], 4)
            if p in V5C2FE:
                row[f"g_v5c_{a}"] = round(ctx.T5[(p, a)]["g"], 4)
                row[f"kin_over_v5c_{a}"] = round(ctx.kin[p][a] / ctx.T5[(p, a)]["g"], 4)
            row[f"kin_over_fea_{a}"] = round(ctx.kin[p][a] / fe[a]["g_fea"], 4)
        kc[p] = row
    dv = [abs(kc[p][f"kin_over_v5c_{a}"] - 1) for p in CONE for a in AXES]
    out["c2_kinematics"] = dict(cad_geometry={k: (round(v, 4) if isinstance(v, float) else v) for k, v in g.items() if k != "servos"},
                                rows=kc, max_rel_diff_kin_vs_v5c=round(max(dv), 4),
                                note="g_kin = sum_i (d psi_i/d theta_a)^2 from the CAD solve_psi (horn crank included), other axis held; "
                                     "g_fea = FEA3D post_k (rod arm / full horn radius: horn normal to the rod); g_v5c = m2_eng11 (V5c FE split)")
    # c3 reproduction of REV-GNC-6 v05 part B on the V5c plant (J_C, cons), every corner (early=False)
    v05 = json.load(open(V05))["B"]
    spec = VARIANTS["A12"]
    M = E.Model(ctx.table(spec), ctx.n_m, ctx.conds)
    rep = {}
    for a, k in (("alpha", 100.0), ("alpha", 130.0), ("beta", 100.0), ("beta", 130.0), ("beta", 190.0)):
        r = env_lumped(ctx, M, M, a, k, E.J_C, "cons", early=False)
        ref = v05[f"{a}|Ks{k:g}"]
        rep[f"{a}|Ks{k:g}"] = dict(mine=dict(pass_6dB=r["pass_6dB"], gm=r["gm_up_min_dB"], n_below=r["n_below_6dB"], n=r["n_corners"], worst=r["worst"]),
                                   rev_gnc6=dict(pass_6dB=ref["pass_6dB"], gm=ref["gm_up_min_dB"], n_below=ref["n_below_6dB"], n=ref["n_corners"], worst=ref["worst"]),
                                   same=bool(r["pass_6dB"] == ref["pass_6dB"] and abs(r["gm_up_min_dB"] - ref["gm_up_min_dB"]) < 2e-3
                                             and r["n_corners"] == ref["n_corners"] and r["n_below_6dB"] == ref["n_below_6dB"]), t_s=r["t_s"])
        print("c3", a, k, rep[f"{a}|Ks{k:g}"], flush=True)
    out["c3_reproduce_rev_gnc6_v05B"] = dict(rows=rep, all_same=all(v["same"] for v in rep.values()))
    # c4 two-mass loop limits against loop_flex
    rng = np.random.default_rng(4)
    names = [k for k in ctx.conds if not E.is62(k)]
    t1, t2 = [], []
    for _ in range(12):
        cn = names[int(rng.integers(len(names)))]
        cond = ctx.conds[cn]
        zr = float(rng.choice(E.ZETAS))
        Ks = float(rng.uniform(90, 160)); gg = float(rng.uniform(16, 37)); S = float(rng.uniform(3500, 8500))
        nt = (float(rng.uniform(18, 28)), 1.0, -12.0)
        # T1: structure rigid (k2 -> large): rotor and engine move together = lumped K_s g with I_piv + J g
        k1 = Ks * gg; m1 = E.J_C * gg
        a1 = ev_tm(cn, cond, k1, 1e3 * k1, m1, zr, nt)
        f_l = math.sqrt(k1 / (cond["I_piv"] + m1)) / (2 * math.pi)
        c = V3.flex_case(cond, k1, zr, 0.0, 1.0)
        c["I_add"] = m1
        c["w_rock"] = math.sqrt(k1 / (cond["I_piv"] + m1))
        L = ct.series(C.cmd_filter(c), C.loop_flex(c))
        L = ct.series(V3.notch_tf(*nt), L)
        b1 = E.margins(L)
        st1 = bool(np.all(np.real(ct.poles(ct.feedback(L, 1))) < 0))
        t1.append(dict(cond=cn, zr=zr, f_lumped=round(f_l, 3), tm=[a1[0], a1[1]], lumped=[st1, b1[0]],
                       d_gm=(None if (a1[1] is None or b1[0] is None) else round(abs(a1[1] - b1[0]), 4))))
        # T2: massless rotor (m1 -> 0): series springs on the engine alone = lumped K_tot with J = 0
        Kt = 1.0 / (1.0 / S + 1.0 / k1)
        a2 = ev_tm(cn, cond, k1, S, 1e-7, zr, nt)
        f2 = math.sqrt(Kt / cond["I_piv"]) / (2 * math.pi)
        b2 = E.ev(cn, cond, f2, zr, nt)
        t2.append(dict(cond=cn, zr=zr, f_lumped=round(f2, 3), tm=[a2[0], a2[1]], lumped=[b2[0], b2[1]],
                       d_gm=(None if (a2[1] is None or b2[1] is None) else round(abs(a2[1] - b2[1]), 4))))
    ok1 = all(r["tm"][0] == r["lumped"][0] and (r["d_gm"] is None or r["d_gm"] < 0.05) for r in t1)
    ok2 = all(r["tm"][0] == r["lumped"][0] and (r["d_gm"] is None or r["d_gm"] < 0.05) for r in t2)
    out["c4_two_mass_limits"] = dict(T1_rigid_structure=t1, T2_massless_rotor=t2, T1_ok=ok1, T2_ok=ok2,
                                     note="T1 k2 = 1000 k1: rotor locked to the engine (lumped K_s g, I_piv + J g, damper on d_s - d_e); "
                                          "T2 m1 = 1e-7: massless rotor (lumped series K, J 0). Pass: same stability and |dGM| < 0.05 dB.")
    # c5 centre-pose frequencies on the FE plant (like-for-like with REV-GNC-6 v09)
    T = ctx.table(VARIANTS["A01"])
    Ipf = ctx.meta["full"]["I_piv"]
    lfl = {}
    for a in AXES:
        t = T[("centre", a)]
        for Ks in (100.0, 130.0):
            Kt = 1.0 / (1.0 / t["S"]["T"] + 1.0 / (Ks * t["g"]))
            lfl[f"{a}|Ks{Ks:g}"] = dict(J0=round(math.sqrt(Kt / Ipf) / (2 * math.pi), 3),
                                        JC=round(math.sqrt(Kt / (Ipf + E.J_C * t["g"])) / (2 * math.pi), 3),
                                        tm_f1_JC=round(tm_f1(t["S"]["T"], t["g"], Ks, E.J_C, Ipf)[0], 3),
                                        tm_f2_JC=round(tm_f1(t["S"]["T"], t["g"], Ks, E.J_C, Ipf)[1], 2))
    out["c5_centre_full_Hz"] = lfl
    out["passed"] = bool(out["c3_reproduce_rev_gnc6_v05B"]["all_same"] and ok1 and ok2 and out["c1_fe_table"]["neutral_file_equal_cone_neutral"])
    jdump(out, os.path.join(OUT, "eng11fe_check.json"))
    print("check passed:", out["passed"], "kin vs v5c max rel diff", out["c2_kinematics"]["max_rel_diff_kin_vs_v5c"], flush=True)


def run_variant(ctx, vid):
    spec = VARIANTS[vid]
    path = os.path.join(OUT, f"eng11fe_{vid}.json")
    prev = json.load(open(path)) if os.path.exists(path) else None
    if prev and prev.get("version") == VERSION and prev.get("spec") == spec and prev.get("done"):
        print(f"{vid}: done, skipped", flush=True)
        return
    ctx.set_wb(spec["wb"])
    T = ctx.table(spec)
    Tb = T if spec["notch"] == "own" else ctx.table(spec, bench=True)
    M = E.Model(T, ctx.n_m, ctx.conds)
    Mb = E.Model(Tb, ctx.n_m, ctx.conds)
    J = JV[spec["J"]]
    kin = spec["kin"]
    rows = (prev or {}).get("rows", {}) if (prev and prev.get("version") == VERSION and prev.get("spec") == spec) else {}
    out = dict(version=VERSION, date=time.strftime("%Y-%m-%d"), variant=vid, spec=spec, J_kgm2=J, poses=list(M.poses),
               table={f"{p}|{a}": v for (p, a), v in T.items()}, notch_table_centre={a: Tb[("centre", a)] for a in AXES},
               fmap=fmap(ctx, spec), rows=rows, done=False)
    for a in AXES:
        for Ks in KS:
            k = f"{a}|Ks{Ks:g}"
            if k in rows:
                continue
            if spec["model"] == "tm":
                r = env_tm(ctx, T, Tb, a, Ks, J)
            else:
                r = env_lumped(ctx, M, Mb, a, Ks, J, kin)
            rows[k] = r
            out["rows"] = rows
            jdump(out, path)
            print(f"{vid} {a:5s} Ks {Ks:5.0f}: {'PASS' if r['pass_6dB'] else 'fail'} GM {r['gm_up_min_dB']} "
                  f"{'' if r['pass_6dB'] else r['first_fail']} ({r['t_s']} s, {r['n_eval']}/{r['n_corners']})", flush=True)
    out["done"] = True
    jdump(out, path)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    ctx = Ctx()
    print(f"{VERSION}: {E.VERSION} mass {E.MASS_VARIANT} {ctx.extra}; iface {os.environ.get('GNC_IFACE')}; load {time.time() - t0:.1f} s", flush=True)
    if PART == "check":
        part_check(ctx)
    elif PART == "run":
        for vid in [v for v in os.environ.get("GNC_E11FE_VARIANTS", "").split(",") if v]:
            t1 = time.time()
            run_variant(ctx, vid)
            print(f"== {vid} wall {time.time() - t1:.0f} s", flush=True)
    print(f"done {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
