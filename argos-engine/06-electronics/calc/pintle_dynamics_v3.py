#!/usr/bin/env python3
"""HV69 pintle drive dynamics v3 on Mechanical's adopted v2.3/v2.4 drive (Electronics, 2026-10-13).

Why v3: the lead accepted Mechanical pintle v2.3/v2.4 (rolling MGN09H carriage guide mu 0.01 + end-seal drag S 2 N, plain DU
link pins mu 0.15 on r 1.5 mm, y_l 11 mm over s_eff 29.9 mm, stem 3.0 mm with seal friction 18.75 N, spiral spring 0.25 N m at
the 15 deg seat angle + 0.12 N m/rad, +/-10 %) and the adopted pintle rail (pintle_rail_v3 divider B: 7.38-7.62 V static).
v2 (pintle_dynamics_v2.py) ran the superseded v2.2 PTFE-guide drive (S3 spring 0.30/0.10, guide mu 0.10-0.20, L0 only).
What v3 answers:
  1. 33 throttle steps (11 steps x 3.5 / 5.0 / 5.5 MPa) and ENG-05 closing from 75 / 100 % at 3.5 / 5.5 MPa, under Combustion's
     needle-force laws (needle_force_v2p3: hot-fire rows L0 / L1 / L2 for the steps; L0 at tank pressure, chamber ambient =
     Mechanical's C1 basis, for the closing), on the rail min / typ;
  2. the crank-radius fallback r 3.5 mm (MECH travel_gate_fallbacks, if B-PNT-1 measures HV69 travel < 103 deg);
  3. the firmware stall-monitor clearance and closing-time constants (src/core/config.h kPintleNoProgNormal_s,
     kPintleFullStrokeSlow_s, kPintleCloseSlow_s and the static_asserts that use them);
  4. B-PNT-1 (LEAD 2026-10-13): the spring's closing torque surplus over the full stroke, against which the unpowered HV69
     back-drive torque is measured, and the unpowered closing-time acceptance tied to the firmware's SAFE check.
Force/torque model RE-IMPLEMENTED from the equations in Mechanical's pintle_v2p3.py docstrings (link force with guide friction
F = F_po + (f_seal + S + mu_g |F| g) sgn(u), g = 2 y_l / s_eff + |tan psi|; pin friction mu_p |F| r_p (|1 - a| + |a|)) and
CROSS-CHECKED against Mechanical's published v2.4 numbers (C1, C2 L1/L2, unlit margins, seat loads, crank-radius row, jam):
independent code, same equations. Servo model as v2 (ASSUMED where marked). Thrust = Combustion's quasi-steady throttle map.
Outputs: results/pintle_dynamics_v3.{json,txt}, results/plots/pintle_dynamics_v3.png. Nothing here is a measurement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'results')
FW = os.path.join(HERE, '..', 'firmware', 'src', 'core')
P_AMB = 101325.0
KGCM = 0.0980665


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


ap = argparse.ArgumentParser()
ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
ap.add_argument('--quick', action='store_true', help='fewer cases (development)')
ARGS = ap.parse_args()
ER = ARGS.engine_root

# ------------------------------------------------------------------------------------------------ inputs (read, tagged)
MECH_PATH = next(p for p in (os.path.join(ER, '03-cad', 'calcs', 'pintle_inline_v34_v2p4.json'),
                             os.path.join(ER, '03-cad', 'src', 'calcs', 'pintle_inline_v34_v2p4.json')) if os.path.exists(p))
M = json.load(open(MECH_PATH))
COMB_PATH = os.path.join(ER, 'interfaces', 'combustion.json')
C = json.load(open(COMB_PATH))
GNC_PATH = os.path.join(ER, 'interfaces', 'gnc.json')
G = json.load(open(GNC_PATH))
NF = C['valves_and_actuators']['pintle_actuator']['needle_force_v2p3']
NF_CSV = os.path.join(ER, '02-combustion', NF['csv'])
NF_JSON = os.path.join(ER, '02-combustion', NF['tag'].split('DERIVED ')[1].split(' ')[0])
NFJ = json.load(open(NF_JSON))
MAP_PATH = C['operating_points']['throttle_map_csv']
if not os.path.exists(MAP_PATH):
    MAP_PATH = os.path.join(ER, MAP_PATH.split('/engine/', 1)[1])
RAIL_PATH = os.path.join(OUT, 'pintle_rail_v3.json')
RAIL = json.load(open(RAIL_PATH))
SERVO_PATH = os.path.join(OUT, 'pintle_mini_servo_v1.json')
SV = next(c for c in json.load(open(SERVO_PATH))['candidates'] if c['id'] == 'MKS HV69')
CFG_H = os.path.join(FW, 'config.h')


def cfg_const(name):
    m = re.search(r'constexpr\s+float\s+' + name + r'\s*=\s*([0-9.eE+-]+)f', open(CFG_H).read())
    if not m:
        raise SystemExit(f'config.h: {name} not found')
    return float(m.group(1))


INP = M['inputs']
BCFG = M['baseline']['cfg']                       # MECH v2.4 baseline config (copied from v2.3)
CR = INP['crank']
STEM_D, SEAT_D = INP['stem_d_mm'] * 1e-3, INP['seat_d_mm'] * 1e-3
ALPHA = math.radians(NFJ['inputs']['cone_half_angle_deg'])
A_STEM, A_SEAT = math.pi / 4 * STEM_D ** 2, math.pi / 4 * SEAT_D ** 2
P_TORCH = INP['P_torch_Pa']                       # MECH (Combustion needle_force_v2p3 ASSUMED chamber with the torch lit)
P_MEOP = C['operating_points']['tank_MEOP_Pa']['v']
STALL_TAB = sorted((float(k), v) for k, v in INP['HV69']['stall_Nm'].items())
STROKE = C['valves_and_actuators']['pintle_actuator']['stroke_m']['v']
# Mechanical C1 pressures: the keys of the published C1 result ('P3.5MPa', 'P5.5MPa', 'MEOP' = combustion tank MEOP)
C1_P = {k: (P_MEOP if k == 'MEOP' else float(k[1:-3]) * 1e6) for k in M['baseline']['C1_assist_min_Nm']}
# start cases (C2): Combustion's partial-stroke unlit cases at the ignition lift with the torch lit (P1 from the case keys)
START_P1 = sorted({float(re.search(r'P1_([0-9.]+)bar', k).group(1)) * 1e5 for k in NFJ['partial_stroke_unlit_C2']
                   if 'start_to_ignition_lift' in k})
START_LIFT = 0.3e-3                               # MECH C2 text: start <= 0.3 mm (Combustion ignition lift case)
GT = G['requirements']['throttle']
T1090 = GT['t10_90_s']['v']
F_MAX = 500.0
SLEW = GT['slew_min_Fmax_per_s']['v'] * F_MAX
F_ENG05 = 0.10 * F_MAX                            # [REQ ENG-05] < 10 % thrust within 0.10 s
# rail (adopted divider B, pintle_rail_v3)
RB = RAIL['dividers']['B_v3_proposed_24k9_4k75']
V_TYP, V_MIN, V_MAX = RB['Vout_typ_V'], RB['static_lower_worst_V'], RB['static_upper_worst_V']
V_STEP = RAIL['publish']['V_rail_line_step_during_stall_V']['v']
V_FAIL = RAIL['publish']['V_rail_failure_static_max_V']['v']
R_LEAD, I_ST = 0.030, 1.5                          # [ASSUMED] rail -> servo plug lead (sim.h) and HV69 stall current (B-PNT-1)
V_SLOW = V_MIN - R_LEAD * I_ST                     # slow-servo case: rail static minimum at the plug
# servo model (as v2, ASSUMED)
TAU_M = 0.010
PB_DEG, ZETA, LAT = 2.0, 0.7, 0.004
W_EPS = 0.05
BLEND = 0.10e-3                                   # MECH L0 blend over the first 0.1 mm
T_PRE = 0.30
# firmware constants (read, not copied)
FWC = {n: cfg_const(n) for n in ('kPintleStallErr_m', 'kPintleProgMin_m', 'kPintleStallTime_s', 'kPintleTrackTime_s',
                                 'kPintleNoProgNormal_s', 'kPintleFullStrokeSlow_s', 'kPintleCloseSlow_s',
                                 'kPintleUnpoweredClose_s', 'kMvSeatTimeout_s', 'kPintleCloseRate_mps', 'kPintleRateCmd_mps')}


def stall_T(V):
    """HV69 stall torque [N m] from the MECH table (retailer copies of MKS data); above 8.2 V the 7.4-8.2 V slope (EXTRAPOLATED)."""
    vs, ts = [a for a, _ in STALL_TAB], [b for _, b in STALL_TAB]
    if V <= vs[-1]:
        return float(np.interp(V, vs, ts))
    return ts[-1] + (ts[-1] - ts[-2]) / (vs[-1] - vs[-2]) * (V - vs[-1])


# ------------------------------------------------------------------------------------------------ needle force laws (+ = OPENING)
def F_L0(x, P1):
    """MECH/Electronics L0 blend: seated dp (A_seat - A_stem) closing -> dp A_stem opening over the first 0.1 mm (P_down = Pa)."""
    dp = max(0.0, P1 - P_AMB)
    w = min(1.0, max(0.0, x / BLEND))
    return -(1 - w) * dp * (A_SEAT - A_STEM) + w * dp * A_STEM


def F_law(law, x, P1, Pdown):
    """Combustion needle_force_v2p3 L1/L2 (+ closing there), converted to + opening: -((P1 - Pdown) A_eff - (P1 - Pa) A_stem)."""
    h = max(0.0, x)
    if h <= 0.0 or law == 'L2':
        a_eff = A_SEAT
    elif law == 'L1':
        a_eff = math.pi * (SEAT_D / 2 - h * math.sin(ALPHA) * math.cos(ALPHA)) ** 2
    else:
        raise ValueError(law)
    return -((P1 - Pdown) * a_eff - (P1 - P_AMB) * A_STEM)


HOT = [r for r in csv.DictReader(l for l in open(NF_CSV) if not l.startswith('#')) if abs(float(r['D_port_m']) - 0.025) < 1e-9]


class HotForce:
    """Hot-fire needle force along the throttle line at one tank pressure (Combustion rows, D_port 25 mm), + opening,
    interpolated in lift (clamped outside the 12.5-100 % rows)."""

    def __init__(s, P_tank, law):
        rows = sorted((float(r['lift_mm']) * 1e-3, -float(r[f'F_{law}_3mm_N'])) for r in HOT if abs(float(r['P_tank_Pa']) - P_tank) < 1.0)
        if not rows:
            raise SystemExit(f'no needle-force rows at {P_tank}')
        s.x = np.array([a for a, _ in rows]); s.f = np.array([b for _, b in rows])

    def __call__(s, x):
        return float(np.interp(x, s.x, s.f))


# ------------------------------------------------------------------------------------------------ drive mechanics
class Mech:
    def __init__(s, tol=0.0, r_mm=None, mu_g=None, S=None, seal=None, mu_p=None, T0=None, k=None):
        s.r = (CR['r'] if r_mm is None else r_mm) * 1e-3
        s.L = CR['L'] * 1e-3
        s.phic, s.phicmd = math.radians(CR['phi_closed']), math.radians(CR['phi_cmd_closed'])
        s.xstop = CR['x_stop'] * 1e-3
        s.mug = BCFG['mu_g'] if mu_g is None else mu_g
        s.S = BCFG['S'] if S is None else S
        s.seal = BCFG['f_seal'] if seal is None else seal
        s.mup = BCFG['mu_p'] if mu_p is None else mu_p
        s.rp, s.yl, s.seff = BCFG['r_p'] * 1e-3, BCFG['y_l'] * 1e-3, BCFG['s_eff'] * 1e-3
        s.T0 = BCFG['T0'] if T0 is None else T0
        s.k = BCFG['k'] if k is None else k
        s.tol = tol
        s.s0 = s._s(s.phic)
        s.phistop = s.phi_of(s.xstop)

    def _s(s, p):
        return s.r * math.cos(p) + math.sqrt(s.L ** 2 - (s.r * math.sin(p)) ** 2)

    def lift(s, p):
        return max(0.0, s.s0 - s._s(p)) if p > s.phic else 0.0

    def lift_vec(s, P):
        P = np.asarray(P)
        x = s.s0 - (s.r * np.cos(P) + np.sqrt(s.L ** 2 - (s.r * np.sin(P)) ** 2))
        return np.where(P > s.phic, np.maximum(x, 0.0), 0.0)

    def dxdphi(s, p):
        q = math.sqrt(s.L ** 2 - (s.r * math.sin(p)) ** 2)
        return s.r * math.sin(p) * (1.0 + s.r * math.cos(p) / q)

    def phi_of(s, x):
        if x <= 0:
            return s.phic
        lo, hi = s.phic, math.pi
        for _ in range(70):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if s.lift(m) < x else (lo, m)
        return 0.5 * (lo + hi)

    def psi(s, p):
        return math.asin(s.r * math.sin(p) / s.L)

    def pin_factor(s, p):
        a = s.r * math.cos(p) / (s.L * math.cos(s.psi(p)))
        return abs(1 - a) + abs(a)

    def spring(s, p):
        return (1.0 + s.tol) * (s.T0 + s.k * (p - s.phic))

    def link_force(s, p, fpo, closing):          # + = compression pushing the needle closed
        mg = s.mug * (2.0 * s.yl / s.seff + abs(math.tan(s.psi(p))))
        fc = s.seal + s.S
        if closing:
            num = fpo + fc
            return num / (1 - mg) if num > 0 else num / (1 + mg)
        num = fpo - fc
        return num / (1 - mg) if num < 0 else num / (1 + mg)

    def torque(s, p, fpo, opening):
        """Opening: servo torque required (+). Closing: the crank's closing surplus on the dog (assist, + = crank follows)."""
        F = s.link_force(p, fpo, not opening)
        pl = s.mup * abs(F) * s.rp * s.pin_factor(p)
        return s.spring(p) - F * s.dxdphi(p) + (pl if opening else -pl), F


class Tables:
    """Opening demand / closing assist / link force on a crank-angle grid for one mechanics + needle-force function."""

    def __init__(s, m, ffun, n=1601):
        s.m = m
        s.p0, s.p1 = m.phic, m.phistop
        s.ph = np.linspace(s.p0, s.p1, n)
        s.d = (s.p1 - s.p0) / (n - 1)
        To, Tc, Fo, Fc = [], [], [], []
        for p in s.ph:
            x = m.lift(p)
            f = ffun(x)
            a, fa = m.torque(p, f, True)
            b, fb = m.torque(p, f, False)
            To.append(a); Tc.append(b); Fo.append(fa); Fc.append(fb)
        s.To, s.Tc, s.Fo, s.Fc = (np.array(v) for v in (To, Tc, Fo, Fc))
        s.To_l, s.Tc_l = s.To.tolist(), s.Tc.tolist()
        s.xt = m.lift_vec(s.ph)                        # monotonic lift table for the inverse (command) map

    def phi_of_vec(s, x):
        x = np.asarray(x)
        return np.where(x <= 0.0, s.m.phicmd, np.interp(x, s.xt, s.ph))


class Servo:
    def __init__(s, V, tau_m=TAU_M):
        Vs = SV['V_rated']
        T = [t * KGCM for t in SV['T_kgcm']]
        w = [math.radians(60.0) / x for x in SV['s60']]
        Vc = min(max(V, Vs[0]), Vs[-1])
        s.Ts, s.wnl = float(np.interp(Vc, Vs, T)), float(np.interp(Vc, Vs, w))
        T74, w74 = float(np.interp(7.4, Vs, T)), float(np.interp(7.4, Vs, w))
        s.J = tau_m * T74 / w74
        s.pb = math.radians(PB_DEG)
        wn = math.sqrt(s.Ts / (s.pb * s.J))
        s.kd = max(0.0, 2 * ZETA * wn * s.J / s.Ts - 1.0 / s.wnl)
        s.V, s.tau_m = V, tau_m


class ThrustMap:
    def __init__(s, P):
        rows = [r for r in csv.DictReader(l for l in open(MAP_PATH) if not l.startswith('#'))
                if r['lift_m'] not in ('', None) and abs(float(r['D_port_m']) - 0.025) < 1e-6 and abs(float(r['P_tank_Pa']) - P) < 1.0]
        pts = sorted((float(r['lift_m']), float(r['F_N']), float(r['frac'])) for r in rows)
        if not pts:
            raise SystemExit(f'throttle map has no rows at P_tank {P}')
        s.h = np.array([0.0] + [p[0] for p in pts]); s.F = np.array([0.0] + [p[1] for p in pts])
        s.frac = {round(p[2], 4): p[0] for p in pts}

    def F_vec(s, h):
        h = np.asarray(h)
        sl = (s.F[-1] - s.F[-2]) / (s.h[-1] - s.h[-2])
        return np.where(h <= s.h[-1], np.interp(h, s.h, s.F), s.F[-1] + sl * (h - s.h[-1]))

    def lift(s, frac):
        k = round(frac, 4)
        return s.frac[k] if k in s.frac else float(np.interp(frac * F_MAX, s.F, s.h))


def simulate(tb, sv, phid0, cmd_arr, dt=1e-4):
    """Dog angle dynamics (crank frame). cmd_arr = commanded dog angle per step (latency already applied). Returns PH, TM, amin."""
    m = tb.m
    n = len(cmd_arr)
    PH = np.empty(n); TM = np.empty(n)
    phid, om = phid0, 0.0
    amin = float('inf')
    lo_stop = m.phicmd - math.radians(3.0)        # servo end stop beyond the closed command (ASSUMED)
    p0, d, To, Tc, nmax = tb.p0, tb.d, tb.To_l, tb.Tc_l, len(tb.To_l) - 2
    Ts, wnl, pb, kd, J = sv.Ts, sv.wnl, sv.pb, sv.kd, sv.J
    phistop = m.phistop
    tanh = math.tanh
    for i in range(n):
        u = (cmd_arr[i] - phid) / pb - kd * om
        u = 1.0 if u > 1.0 else (-1.0 if u < -1.0 else u)
        Tm = Ts * (u - om / wnl)
        lim = Ts * (1 + abs(om) / wnl)
        Tm = lim if Tm > lim else (-lim if Tm < -lim else Tm)
        Tl = 0.0
        if phid >= p0:
            q = (phid - p0) / d
            j = int(q)
            if j > nmax:
                j = nmax
            f = q - j
            a = To[j] + f * (To[j + 1] - To[j])
            b = Tc[j] + f * (Tc[j + 1] - Tc[j])
            if b < amin:
                amin = b
            sg = tanh(om / W_EPS)
            Tl = 0.5 * (a + b) + 0.5 * (a - b) * sg
        om += (Tm - Tl) / J * dt
        phid += om * dt
        if phid >= phistop and om > 0:
            phid, om = phistop, 0.0
        if phid <= lo_stop and om < 0:
            phid, om = lo_stop, 0.0
        PH[i] = phid; TM[i] = Tm
    return PH, TM, amin


def noprog_max(tt, xcmd, X, err=None, pmin=None):
    """Firmware stall-monitor metric (config.h kPintleStallErr_m / kPintleProgMin_m): longest interval with |cmd - lift| > err
    without a progress mark (lift moved >= pmin toward the command since the last mark)."""
    err = FWC['kPintleStallErr_m'] if err is None else err
    pmin = FWC['kPintleProgMin_m'] if pmin is None else pmin
    worst, active, ref, t_ref = 0.0, False, 0.0, 0.0
    e_arr = xcmd - X
    for k in range(len(tt)):
        e = e_arr[k]
        if abs(e) > err:
            adv = (X[k] - ref) * (1.0 if e > 0 else -1.0)
            if not active or adv >= pmin:
                active, ref, t_ref = True, X[k], tt[k]
            if tt[k] - t_ref > worst:
                worst = tt[k] - t_ref
        else:
            active = False
    return round(float(worst), 4)


def track_err_max(tt, xcmd, X, err=None):
    """Longest continuous interval with |cmd - lift| > kPintleStallErr_m (the firmware tracking-timeout criterion runs on it)."""
    err = FWC['kPintleStallErr_m'] if err is None else err
    big = np.abs(xcmd - X) > err
    worst, t0 = 0.0, None
    for k in range(len(tt)):
        if big[k]:
            if t0 is None:
                t0 = tt[k]
            worst = max(worst, tt[k] - t0)
        else:
            t0 = None
    return round(float(worst), 4)


def run_profile(tb, sv, phid0, cmd_lift_fun, tmax, dt=1e-4):
    """cmd_lift_fun(t array) -> commanded LIFT [m] (<= 0 means the closed command). Returns t, X, PH, TM, amin, xcmd."""
    n = int(round(tmax / dt))
    t = np.arange(n) * dt
    xcmd = cmd_lift_fun(t)
    xlat = cmd_lift_fun(np.maximum(0.0, t - LAT))
    cmd_phi = tb.phi_of_vec(xlat)
    PH, TM, amin = simulate(tb, sv, phid0, cmd_phi.tolist(), dt)
    X = tb.m.lift_vec(np.clip(PH, tb.m.phic, tb.m.phistop))
    return t, X, PH, TM, amin, xcmd


def step_metrics(tb, sv, tm, f0, f1, slew=None, tmax=0.6):
    x0, x1 = tm.lift(f0), tm.lift(f1)

    def cmdf(t):
        if slew:
            dx = np.minimum(abs(x1 - x0), slew * np.maximum(0.0, t - T_PRE))
            return np.where(t < T_PRE, x0, x0 + math.copysign(1.0, x1 - x0) * dx)
        return np.where(t < T_PRE, x0, x1)
    t, X, PH, TM, amin, xcmd = run_profile(tb, sv, tb.m.phi_of(x0), cmdf, T_PRE + tmax)
    F = tm.F_vec(X)
    sel = t >= T_PRE
    np_max = noprog_max(t[sel] - T_PRE, xcmd[sel], X[sel])
    k0 = int(np.argmax(t >= T_PRE + LAT)) - 1
    Fa, Fb = float(F[k0]), float(np.mean(F[t >= t[-1] - 0.05]))
    dF = Fb - Fa
    tt = t[k0:] - T_PRE
    g = (F[k0:] - Fa) / dF if abs(dF) > 1e-9 else np.zeros_like(tt)
    if np.any(g >= 0.1) and np.any(g >= 0.9):
        t10, t90 = float(tt[np.argmax(g >= 0.1)]), float(tt[np.argmax(g >= 0.9)])
    else:
        t10 = t90 = float('nan')
    t1090 = t90 - t10
    dF_cmd = float(tm.F_vec(x1) - tm.F_vec(x0))
    treq = max(T1090, 0.8 * abs(dF_cmd) / SLEW)
    return {'from': f0, 'to': f1, 'dir': 'open' if f1 > f0 else 'close', 'dF_cmd_N': round(dF_cmd, 1),
            'x0_mm': round(x0 * 1e3, 3), 'x1_mm': round(x1 * 1e3, 3),
            'droop_end_N': round(Fb - float(tm.F_vec(x1)), 1),
            't10_90_s': round(t1090, 4), 't90_from_cmd_s': round(t90, 4), 't_req_s': round(treq, 4),
            'margin': round(treq / t1090, 2) if t1090 > 0 else None,
            'pass_gnc': bool(t1090 == t1090 and t1090 <= treq), 'pass_strict_0p15': bool(t1090 == t1090 and t1090 <= T1090),
            'peak_motor_torque_Nm': round(float(np.max(np.abs(TM[k0:]))), 3), 'assist_min_Nm': round(amin, 4) if amin < 1e9 else None,
            'noprog_max_s': np_max}


def close_time(tb, sv, tm, frac, close_rate=None, tmax=0.6):
    """SHUTDOWN / MECO from a settled thrust fraction: lift command ramps to 0 at kPintleCloseRate, then the closed command."""
    close_rate = FWC['kPintleCloseRate_mps'] if close_rate is None else close_rate
    x0 = tm.lift(frac)

    def cmdf(t):
        return np.where(t < T_PRE, x0, x0 - close_rate * np.maximum(0.0, t - T_PRE))
    t, X, PH, TM, amin, xcmd = run_profile(tb, sv, tb.m.phi_of(x0), cmdf, T_PRE + tmax)
    sel = t >= T_PRE
    tt = t[sel] - T_PRE
    F = tm.F_vec(X[sel])
    i10 = int(np.argmax(F < F_ENG05)) if np.any(F < F_ENG05) else None
    iseat = int(np.argmax(X[sel] <= 1e-7)) if np.any(X[sel] <= 1e-7) else None
    return {'frac': frac, 'x0_mm': round(x0 * 1e3, 3), 'F0_N': round(float(tm.F_vec(x0)), 1),
            't_to_10pct_s': round(float(tt[i10]), 4) if i10 is not None else None,
            't_seated_s': round(float(tt[iseat]), 4) if iseat is not None else None,
            'pass_eng05': bool(i10 is not None and tt[i10] <= 0.10), 'assist_min_Nm': round(amin, 4),
            'noprog_max_s': noprog_max(tt, np.maximum(xcmd[sel], 0.0), X[sel])}


def full_stroke(tb, sv, opening, x_full=STROKE, tmax=1.0):
    """Closed command <-> x_full; times from the command to 90 / 99 % of the SETTLED lift change, end droop (P-band)."""
    xa, xb_cmd = (0.0, x_full) if opening else (x_full, 0.0)
    pa = tb.m.phicmd if opening else tb.m.phi_of(x_full)

    def cmdf(t):
        return np.where(t < T_PRE, xa if opening else x_full, xb_cmd if opening else -1.0)
    t, X, PH, TM, amin, xcmd = run_profile(tb, sv, pa, cmdf, T_PRE + tmax)
    sel = t >= T_PRE
    x0 = float(X[sel][0]); xe = float(np.mean(X[t >= t[-1] - 0.05]))
    g = (X[sel] - x0) / (xe - x0) if abs(xe - x0) > 1e-9 else np.zeros(int(np.sum(sel)))
    tt = t[sel] - T_PRE
    i90 = int(np.argmax(g >= 0.90)) if np.any(g >= 0.90) else None
    i99 = int(np.argmax(g >= 0.99)) if np.any(g >= 0.99) else None
    iseat = int(np.argmax(X[sel] <= 1e-7)) if (not opening and np.any(X[sel] <= 1e-7)) else None
    return {'t90_s': round(float(tt[i90]), 4) if i90 is not None else None, 't99_s': round(float(tt[i99]), 4) if i99 is not None else None,
            't_seated_s': round(float(tt[iseat]), 4) if iseat is not None else None,
            'x_end_mm': round(xe * 1e3, 3), 'droop_mm': round(((xb_cmd if opening else 0.0) - xe) * 1e3, 3),
            'noprog_max_s': noprog_max(tt, np.full_like(tt, xb_cmd if opening else 0.0), X[sel]),
            'track_err_max_s': track_err_max(tt, np.full_like(tt, xb_cmd if opening else 0.0), X[sel]),
            'assist_min_Nm': round(amin, 4) if amin < 1e9 else None}


# ------------------------------------------------------------------------------------------------ cross-check vs MECH v2.4
def evaluate_static(m_lo, m_hi, phis_full, phis_start, n_rows=True):
    """Mechanical C1/C2 recipe on this code. m_lo = -10 % spring (C1), m_hi = +10 % spring (C2)."""
    out = {'C1_assist_min_Nm': {k: round(min(m_lo.torque(p, F_L0(m_lo.lift(p), P), False)[0] for p in phis_full), 3) for k, P in C1_P.items()}}
    for law in ('L1', 'L2'):
        t_b = max(m_hi.torque(p, 0.0, True)[0] for p in phis_full)
        t_s = max(m_hi.torque(p, F_law(law, m_hi.lift(p), P1, P_TORCH), True)[0] for P1 in START_P1 for p in phis_start)
        t_h = max(m_hi.torque(m_hi.phi_of(float(r['lift_mm']) * 1e-3), -float(r[f'F_{law}_3mm_N']), True)[0] for r in HOT)
        t2 = max(t_b, t_s, t_h)
        out[f'C2_{law}'] = {'bench_start_hot_Nm': [round(t_b, 3), round(t_s, 3), round(t_h, 3)], 'max_Nm': round(t2, 3),
                            'margin_7V4': round(stall_T(7.4) / t2, 2)}
    ul = {law: round(stall_T(7.4) / max(m_hi.torque(p, F_law(law, m_hi.lift(p), 3.5e6, P_AMB), True)[0] for p in phis_full), 2)
          for law in ('L1', 'L2')}
    ul['L0'] = round(stall_T(7.4) / max(m_hi.torque(p, F_L0(m_hi.lift(p), 3.5e6), True)[0] for p in phis_full), 2)
    out['unlit_full_stroke_3p5MPa_margin_7V4'] = ul
    m0 = Mech(0.0, r_mm=m_lo.r * 1e3)
    dx0 = m0.dxdphi(m0.phic)
    t_ = BCFG['tol']
    out['seat_load_N'] = {'minus10': round((1 - t_) * m0.T0 / dx0, 1), 'nominal': round(m0.T0 / dx0, 1),
                          'plus10': round((1 + t_) * m0.T0 / dx0, 1)}
    return out


def grids(m):
    return (list(np.linspace(m.phic, m.phi_of(m.xstop), 200)), list(np.linspace(m.phic, m.phi_of(START_LIFT), 12)))


def jam_tension(V, r_mm=None):
    m0 = Mech(0.0, r_mm=r_mm)
    return (stall_T(V) - (1 - BCFG['tol']) * m0.T0) / m0.dxdphi(m0.phic)      # pin friction 0, -10 % spring (MECH jam basis)


def cross_check():
    tol = BCFG['tol']
    mlo, mhi = Mech(-tol), Mech(+tol)
    pf, ps = grids(mlo)
    mine = evaluate_static(mlo, mhi, pf, ps)
    ref = M['baseline']
    dev = {}
    dev['C1'] = max(abs(mine['C1_assist_min_Nm'][k] - ref['C1_assist_min_Nm'][k]) for k in C1_P)
    dev['C2'] = max(abs(a - b) for law in ('L1', 'L2') for a, b in zip(mine[f'C2_{law}']['bench_start_hot_Nm'], ref[f'C2_{law}']['bench_start_hot_Nm']))
    dev['unlit_margin'] = max(abs(mine['unlit_full_stroke_3p5MPa_margin_7V4'][k] - ref['unlit_full_stroke_3p5MPa_margin_7V4'][k]) for k in ('L0', 'L1', 'L2'))
    dev['seat_load_N'] = max(abs(mine['seat_load_N'][k] - ref['seat_load_N'][k]) for k in ('minus10', 'nominal', 'plus10'))
    # crank-radius fallback row r 3.5 mm
    row = next(r for r in M['travel_gate_fallbacks']['crank_radius_study'] if abs(r['r_mm'] - 3.5) < 1e-9)
    mlo5, mhi5 = Mech(-tol, r_mm=3.5), Mech(+tol, r_mm=3.5)
    pf5, ps5 = grids(mlo5)
    r35 = evaluate_static(mlo5, mhi5, pf5, ps5)
    m35 = Mech(0.0, r_mm=3.5)
    r35_mine = {'travel_cmd_deg': round(math.degrees(m35.phistop - m35.phicmd), 1), 'seat_load_nom_N': r35['seat_load_N']['nominal'],
                'C1_assist_MEOP_Nm': r35['C1_assist_min_Nm']['MEOP'], 'C2_margin_L1': r35['C2_L1']['margin_7V4'],
                'C2_margin_L2': r35['C2_L2']['margin_7V4']}
    dev['r3p5'] = {k: round(abs(r35_mine[k] - row[k]), 4) for k in r35_mine}
    # jam rows
    jam = M['jam']['by_rail_voltage']
    jam_dev = {k: round(abs(jam_tension(float(k[:-1])) - v['F_link_N_mu_p_0']), 2) for k, v in jam.items()}
    m0 = Mech(0.0)
    geo = {'phi_stop_deg': round(math.degrees(m0.phistop), 2), 'travel_cmd_deg': round(math.degrees(m0.phistop - m0.phicmd), 2),
           'dx_dphi_closed_mm_per_rad': round(m0.dxdphi(m0.phic) * 1e3, 4)}
    dev['crank'] = {k: round(abs(geo[k] - M['crank'][k]), 4) for k in geo}
    tolerances = {'C1': 0.002, 'C2': 0.002, 'unlit_margin': 0.011, 'seat_load_N': 0.11}
    ok = all(dev[k] <= v for k, v in tolerances.items()) and all(v <= 0.11 for v in dev['r3p5'].values()) and \
        all(v <= 0.11 for v in jam_dev.values()) and all(v <= 0.011 for v in dev['crank'].values())
    return {'mine': mine, 'mine_r3p5': r35_mine, 'mech_r3p5': row, 'max_abs_dev': dev, 'jam_dev_N': jam_dev, 'geometry': geo,
            'tolerances': tolerances, 'pass': bool(ok),
            'note': 'independent re-implementation of the MECH v2.3 equations; deviations are rounding of the published values'}


# ------------------------------------------------------------------------------------------------ B-PNT-1 back-drive table
def backdrive_table():
    tol = BCFG['tol']
    m_lo, m_nom = Mech(-tol), Mech(0.0)
    rows = []
    for deg in list(range(16, int(math.degrees(m_nom.phistop)) + 1, 6)) + [round(math.degrees(m_nom.phistop), 2)]:
        p = math.radians(deg)
        x = m_lo.lift(p)
        rec = {'crank_deg': round(deg, 2), 'servo_deg_from_closed_cmd': round(deg - CR['phi_cmd_closed'], 2), 'lift_mm': round(x * 1e3, 3),
               'spring_nom_Nm': round(m_nom.spring(p), 4), 'spring_m10_Nm': round(m_lo.spring(p), 4),
               'assist_bench_m10_Nm': round(m_lo.torque(p, 0.0, False)[0], 4)}
        for k, P in C1_P.items():
            rec[f'assist_{k}_L0_m10_Nm'] = round(m_lo.torque(p, F_L0(x, P), False)[0], 4)
        rec['assist_min_m10_Nm'] = round(min(v for kk, v in rec.items() if kk.startswith('assist_')), 4)
        rec['T_bd_allow_Nm'] = round(0.5 * rec['assist_min_m10_Nm'], 4)
        rows.append(rec)
    amin = min(r['assist_min_m10_Nm'] for r in rows)
    return {'rows': rows, 'assist_min_over_stroke_m10_Nm': round(amin, 4),
            'acceptance': {'T_bd_max_Nm': round(min(0.05, 0.5 * amin), 3),
                           'rule': 'measured unpowered back-drive torque at the HV69 output (slow, and at ~2 rad/s), every crank angle over '
                                   'the full stroke, <= 0.5 x the -10 % spring closing assist at that angle (column T_bd_allow_Nm, the minimum '
                                   'of bench and L0 at 3.5 / 5.5 / 7.0 MPa); scalar target <= 0.05 N m kept from v2',
                           'unpowered_close_s_max': round(FWC['kPintleUnpoweredClose_s'] / 3.0, 3),
                           'unpowered_close_rule': 'unpowered spring closing 4.0 mm -> seated (servo unpowered, bench, nominal spring) '
                                                   'within kPintleUnpoweredClose_s / 3 = SAFE-check margin 3 (config.h static_assert)'},
            'tag': 'DERIVED from the MECH v2.3 model (L0, -10 % spring); the back-drive torque itself is UNKNOWN (B-PNT-1)'}


# ------------------------------------------------------------------------------------------------ main
STEPS = [(0.125, 1.0), (0.2, 1.0), (0.25, 1.0), (0.2, 0.5), (0.5, 1.0), (0.5, 0.55), (0.95, 1.0),
         (1.0, 0.2), (1.0, 0.125), (0.5, 0.2), (0.55, 0.5)]
P_STEPS = (3.5e6, 5.0e6, 5.5e6)
LAWS = ('L0', 'L1', 'L2')


def main():
    tol = BCFG['tol']
    out = {'id': 'pintle_dynamics', 'version': 'v3', 'date': '2026-10-13', 'owner': 'Electronics',
           'supersedes': 'pintle_dynamics_v2 (MECH v2.2 PTFE-guide drive, superseded by the lead 2026-10-12/13)',
           'inputs': {'mechanical': {'path': os.path.relpath(MECH_PATH, ER), 'version': M['version'], 'sha256_16': sha(MECH_PATH),
                                     'baseline_cfg': BCFG, 'crank': CR, 'HV69_stall_Nm': INP['HV69']['stall_Nm'], 'P_torch_Pa': P_TORCH},
                      'combustion.json': [C['version'], sha(COMB_PATH)],
                      'needle_force_csv': [os.path.relpath(NF_CSV, ER), sha(NF_CSV)], 'needle_force_json': [os.path.relpath(NF_JSON, ER), sha(NF_JSON)],
                      'start_P1_Pa': START_P1, 'C1_P_Pa': C1_P, 'gnc.json': [G['version'], sha(GNC_PATH)],
                      'throttle_map': [os.path.relpath(MAP_PATH, ER), sha(MAP_PATH)],
                      'rail': {'file': 'results/pintle_rail_v3.json', 'sha256_16': sha(RAIL_PATH), 'divider': 'B 24.9k/4.75k',
                               'V_min_typ_max_static': [V_MIN, V_TYP, V_MAX], 'V_line_step': V_STEP, 'V_failure_static_max': V_FAIL,
                               'V_slow_case_plug': round(V_SLOW, 4)},
                      'servo': {'id': SV['id'], 'V': SV['V_rated'], 'T_kgcm': SV['T_kgcm'], 's60': SV['s60'], 'tag': 'retailer copies of MKS data'},
                      'firmware_config_h': {'path': 'firmware/src/core/config.h', 'sha256_16': sha(CFG_H), 'constants': FWC},
                      'assumed': {'tau_m_s': TAU_M, 'pb_deg': PB_DEG, 'zeta': ZETA, 'latency_s': LAT, 'R_lead_ohm': R_LEAD, 'I_stall_A': I_ST,
                                  'thrust': 'quasi-steady map, no chamber/fuel lag (Combustion owns the tail-off)'}},
           'requirements': {'t10_90_s': T1090, 'slew_N_s': SLEW, 'criterion': 't10-90 <= max(t10_90_s, 0.8 |dF| / slew); strict <= t10_90_s',
                            'ENG-05': '< 10 % F_max (50 N) within 0.10 s of the shutdown command'}}
    cc = cross_check()
    out['cross_check_vs_mech_v2p4'] = cc
    print('cross-check', cc['max_abs_dev'], cc['jam_dev_N'], 'PASS' if cc['pass'] else 'FAIL')
    # static summary on the adopted rail
    mlo, mhi = Mech(-tol), Mech(+tol)
    st = cc['mine']
    out['static'] = {'C1_assist_min_Nm_L0_m10': st['C1_assist_min_Nm'], 'C2': {l: st[f'C2_{l}'] for l in ('L1', 'L2')},
                     'opening_margin_vs_rail': {}}
    dem = max(st['C2_L1']['max_Nm'], st['C2_L2']['max_Nm'])
    for lab, V in (('rail min static', V_MIN), ('servo plug at rail min (- 30 mOhm x 1.5 A)', V_SLOW), ('rail typ', V_TYP), ('7.4 V (MECH C2 basis)', 7.4)):
        out['static']['opening_margin_vs_rail'][lab] = {'V': round(V, 4), 'T_stall_Nm': round(stall_T(V), 4), 'margin_C2': round(stall_T(V) / dem, 3)}
    out['jam_link_tension_N'] = {f'{V:.3f} V': round(jam_tension(V), 1) for V in (V_MIN, V_TYP, V_MAX, V_STEP, 8.2, V_FAIL, 8.4)}
    out['jam_link_tension_r3p5_N'] = {f'{V:.3f} V': round(jam_tension(V, 3.5), 1) for V in (V_MAX, V_STEP, V_FAIL)}
    # ---- 33 throttle steps under the hot-fire laws
    cases = [('nominal: spring 0, MECH baseline friction, rail typ', 0.0, V_TYP, TAU_M, {}, None, None),
             ('spring +10 %, plug at rail min', +tol, V_SLOW, TAU_M, {}, None, None),
             ('spring -10 %, plug at rail min', -tol, V_SLOW, TAU_M, {}, None, None),
             ('guide mu 0.02 + S 5 N (MECH sens.), spring +10 %, rail min', +tol, V_SLOW, TAU_M, {'mu_g': 0.02, 'S': 5.0}, None, None),
             ('tau_m 20 ms, spring +10 %, rail min', +tol, V_SLOW, 0.020, {}, None, None),
             ('ECU 60 mm/s command slew, nominal', 0.0, V_TYP, TAU_M, {}, FWC['kPintleRateCmd_mps'], None),
             ('r 3.5 mm fallback, nominal', 0.0, V_TYP, TAU_M, {}, None, 3.5),
             ('r 3.5 mm fallback, spring +10 %, rail min', +tol, V_SLOW, TAU_M, {}, None, 3.5)]
    if ARGS.quick:
        cases = cases[:2]
    step_cases = []
    for tag, tl, V, tau, kw, slew, r in cases:
        m = Mech(tl, r_mm=r, **kw)
        sv = Servo(V, tau)
        rec = {'case': tag, 'V': round(V, 4), 'spring_tol': tl, 'tau_m_s': tau, 'mech_overrides': kw, 'ecu_slew_m_s': slew, 'r_mm': r or CR['r'],
               'steps': []}
        for P in P_STEPS:
            tm = ThrustMap(P)
            tbs = {law: Tables(m, HotForce(P, law)) for law in LAWS}
            for f0, f1 in STEPS:
                per = {law: step_metrics(tbs[law], sv, tm, f0, f1, slew) for law in LAWS}
                worst_law = max(LAWS, key=lambda l: per[l]['t10_90_s'] if per[l]['t10_90_s'] == per[l]['t10_90_s'] else 1e9)
                w = dict(per[worst_law])
                w.update({'P_tank_MPa': P / 1e6, 'worst_law': worst_law,
                          't10_90_by_law_s': {l: per[l]['t10_90_s'] for l in LAWS},
                          'noprog_max_s': max(per[l]['noprog_max_s'] for l in LAWS),
                          'assist_min_Nm': min(per[l]['assist_min_Nm'] for l in LAWS if per[l]['assist_min_Nm'] is not None)})
                rec['steps'].append(w)
        S = rec['steps']
        rec['n_steps'] = len(S)
        rec['all_pass_gnc'] = all(s['pass_gnc'] for s in S)
        rec['all_pass_strict_0p15'] = all(s['pass_strict_0p15'] for s in S)
        for d in ('open', 'close'):
            sd = [s for s in S if s['dir'] == d]
            rec[f'{d}_max_t10_90_s'] = max(s['t10_90_s'] for s in sd)
            rec[f'{d}_min_margin'] = min(s['margin'] for s in sd if s['margin'] is not None)
        rec['assist_min_Nm'] = min(s['assist_min_Nm'] for s in S)
        rec['noprog_max_s'] = max(s['noprog_max_s'] for s in S)
        step_cases.append(rec)
        print(f"steps {tag:62s} GNC {rec['all_pass_gnc']} strict {rec['all_pass_strict_0p15']} open max {rec['open_max_t10_90_s']:.3f} "
              f"close max {rec['close_max_t10_90_s']:.3f} noprog {rec['noprog_max_s']:.4f}", flush=True)
    out['steps'] = step_cases
    # ---- ENG-05 closing (L0 at tank pressure, chamber ambient = MECH C1 basis)
    eng05 = []
    ecases = [('nominal, rail typ', 0.0, V_TYP, TAU_M, None), ('spring -10 %, plug at rail min', -tol, V_SLOW, TAU_M, None),
              ('spring -10 %, rail min, tau_m 20 ms', -tol, V_SLOW, 0.020, None), ('r 3.5 mm, spring -10 %, rail min', -tol, V_SLOW, TAU_M, 3.5)]
    for tag, tl, V, tau, r in ecases:
        m = Mech(tl, r_mm=r); sv = Servo(V, tau)
        for P in (3.5e6, 5.5e6):
            tm = ThrustMap(P)
            tb = Tables(m, lambda x, P=P: F_L0(x, P))
            for frac in (0.75, 1.0):
                rr = close_time(tb, sv, tm, frac)
                rr.update({'case': tag, 'P_tank_MPa': P / 1e6})
                eng05.append(rr)
    out['eng05_close'] = eng05
    mc = M['meco_close_estimate']['rows']
    out['eng05_vs_mech_estimate'] = {k: {'mech_t_s': v['t_s_estimate'],
                                         'this_nominal_t_seated_s': next(r['t_seated_s'] for r in eng05 if r['case'] == 'nominal, rail typ' and
                                                                         abs(r['P_tank_MPa'] - float(k.split('_P')[1][:-3])) < 1e-9 and
                                                                         abs(r['frac'] - float(k[1:].split('_')[0]) / 100) < 1e-9)}
                                     for k, v in mc.items()}
    print('ENG-05 worst t<10% ', max(r['t_to_10pct_s'] for r in eng05), 'all pass', all(r['pass_eng05'] for r in eng05), flush=True)
    # ---- full strokes (4.0 mm): bench (no pressure), unlit 3.5 MPa N2 ground check (L1/L2 opening), MEOP L0 closing
    fs = {}
    fcases = [('nominal, rail typ', 0.0, V_TYP, TAU_M, None), ('spring +10 %, plug at rail min', +tol, V_SLOW, TAU_M, None),
              ('spring -10 %, plug at rail min', -tol, V_SLOW, TAU_M, None), ('spring -10 %, rail min, tau_m 20 ms', -tol, V_SLOW, 0.020, None),
              ('spring +10 %, rail min, tau_m 20 ms', +tol, V_SLOW, 0.020, None),
              ('r 3.5 mm, spring +10 %, rail min', +tol, V_SLOW, TAU_M, 3.5), ('r 3.5 mm, spring -10 %, rail min', -tol, V_SLOW, TAU_M, 3.5)]
    for tag, tl, V, tau, r in fcases:
        m = Mech(tl, r_mm=r); sv = Servo(V, tau)
        tb0 = Tables(m, lambda x: 0.0)
        rec = {'open_bench': full_stroke(tb0, sv, True), 'close_bench': full_stroke(tb0, sv, False),
               'close_MEOP_L0': full_stroke(Tables(m, lambda x: F_L0(x, P_MEOP)), sv, False)}
        for law in ('L1', 'L2'):
            rec[f'open_3p5MPa_unlit_{law}'] = full_stroke(Tables(m, lambda x, law=law: F_law(law, x, 3.5e6, P_AMB)), sv, True)
        fs[tag] = rec
    out['full_stroke'] = fs
    # ---- firmware constants vs this model. 'normal' = flight-relevant records (steps, ENG-05, bench / MEOP strokes) with the
    # nominal ASSUMED servo time constant; 'sens' adds tau_m 20 ms; 'ground' = unlit N2 full strokes at 3.5 MPa (cold-flow
    # procedure only: flight never opens past the ignition lift unlit, LEAD rule a)
    def is_sens(tag):
        return 'tau_m 20' in tag

    def is_r35(tag):
        return 'r 3.5' in tag
    rec_np = [(c['case'], s_['noprog_max_s']) for c in step_cases for s_ in c['steps']] + [(r['case'], r['noprog_max_s']) for r in eng05] + \
        [(k, v['noprog_max_s']) for k, rec in fs.items() for n, v in rec.items() if 'unlit' not in n]
    np_nominal = max(v for k, v in rec_np if not is_sens(k))
    np_sens = max(v for k, v in rec_np)
    fl_strokes = [(k, n, v) for k, rec in fs.items() for n, v in rec.items() if 'unlit' not in n]
    gr_strokes = [(k, n, v) for k, rec in fs.items() for n, v in rec.items() if 'unlit' in n]

    def t_done(n, v):
        return v['t99_s'] if n.startswith('open') else v['t_seated_s']
    slow_nom = max(((k, n, t_done(n, v)) for k, n, v in fl_strokes if not is_sens(k)), key=lambda z: z[2])
    slow_sens = max(((k, n, t_done(n, v)) for k, n, v in fl_strokes), key=lambda z: z[2])
    cl_nom = max(((k, n, v['t_seated_s']) for k, n, v in fl_strokes if n == 'close_MEOP_L0' and not is_sens(k)), key=lambda z: z[2])
    cl_sens = max(((k, n, v['t_seated_s']) for k, n, v in fl_strokes if n == 'close_MEOP_L0'), key=lambda z: z[2])
    gr_slow = max(((k, n, v['t99_s'], v['track_err_max_s']) for k, n, v in gr_strokes), key=lambda z: z[3])
    fwchk = {'noprog_normal_max_s': {'nominal_tau_m': round(np_nominal, 4), 'with_tau_m_20ms': round(np_sens, 4),
                                     'source': 'lost motion at the opening from the closed command (dog crosses 5 deg before the crank moves)'},
             'slowest_full_stroke_flight': {'nominal_tau_m': {'case': slow_nom[0], 'record': slow_nom[1], 't_s': slow_nom[2]},
                                            'with_tau_m_20ms': {'case': slow_sens[0], 'record': slow_sens[1], 't_s': slow_sens[2]}},
             'slowest_powered_close_4mm_MEOP_L0': {'nominal_tau_m': {'case': cl_nom[0], 't_seated_s': cl_nom[2]},
                                                   'with_tau_m_20ms': {'case': cl_sens[0], 't_seated_s': cl_sens[2]}},
             'ground_unlit_N2_full_stroke_3p5MPa': {'case': gr_slow[0], 'record': gr_slow[1], 't99_s': gr_slow[2], 'track_err_max_s': gr_slow[3],
                                                    'note': 'cold-flow procedure case; the tracking timeout runs on the error > kPintleStallErr_m'},
             'firmware': {k: FWC[k] for k in ('kPintleNoProgNormal_s', 'kPintleFullStrokeSlow_s', 'kPintleCloseSlow_s', 'kPintleStallTime_s',
                                              'kPintleTrackTime_s', 'kPintleUnpoweredClose_s', 'kMvSeatTimeout_s')}}
    chk = {
        'kPintleNoProgNormal_s bounds the v3 nominal value': FWC['kPintleNoProgNormal_s'] >= np_nominal - 1e-9,
        'kPintleFullStrokeSlow_s bounds the v3 flight full strokes (nominal)': FWC['kPintleFullStrokeSlow_s'] >= slow_nom[2],
        'kPintleCloseSlow_s bounds the v3 powered closing (nominal)': FWC['kPintleCloseSlow_s'] >= cl_nom[2],
        'stall time >= 4 x no-progress (nominal tau_m)': FWC['kPintleStallTime_s'] >= 4.0 * np_nominal,
        'track time >= 1.5 x slowest flight full stroke (nominal)': FWC['kPintleTrackTime_s'] >= 1.5 * slow_nom[2],
        'unpowered check >= 3 x slowest powered close (with tau_m 20 ms)': FWC['kPintleUnpoweredClose_s'] >= 3.0 * cl_sens[2],
        'seat timeout >= 1.4 x slowest powered close (with tau_m 20 ms)': FWC['kMvSeatTimeout_s'] >= 1.4 * cl_sens[2]}
    fwchk['checks'] = {k: bool(v) for k, v in chk.items()}
    fwchk['sensitivity_ratios'] = {'stall_time_over_noprog_tau20': round(FWC['kPintleStallTime_s'] / np_sens, 2),
                                   'track_time_over_slowest_flight_stroke_tau20': round(FWC['kPintleTrackTime_s'] / slow_sens[2], 2),
                                   'track_time_over_ground_unlit_track_err': round(FWC['kPintleTrackTime_s'] / gr_slow[3], 2) if gr_slow[3] > 0 else None,
                                   'seat_timeout_over_close_tau20': round(FWC['kMvSeatTimeout_s'] / cl_sens[2], 2)}
    out['firmware_constants_check'] = fwchk
    out['bpnt1_backdrive'] = backdrive_table()
    with open(os.path.join(OUT, 'pintle_dynamics_v3.json'), 'w') as f:
        json.dump(out, f, indent=1)
    write_txt(out)
    plot(out)


def write_txt(out):
    L = []
    p = L.append
    i = out['inputs']
    p(f"pintle_dynamics_v3 (Electronics 2026-10-13): MKS HV69 on MECH {i['mechanical']['path']} {i['mechanical']['version']} "
      f"sha {i['mechanical']['sha256_16']}; rail divider B {V_MIN:.3f}/{V_TYP:.3f}/{V_MAX:.3f} V (slow case {V_SLOW:.3f} V at the plug)")
    p(f"MECH baseline cfg {BCFG}")
    p(f"needle force: Combustion needle_force_v2p3 (csv sha {i['needle_force_csv'][1]}); steps under hot-fire L0/L1/L2 (worst law per step); "
      f"closing under L0 at tank pressure (MECH C1 basis); start P1 {[round(x / 1e5, 1) for x in START_P1]} bar with P_torch {P_TORCH / 1e5:.1f} bar")
    cc = out['cross_check_vs_mech_v2p4']
    p(f"cross-check vs MECH v2.4 published values ({'PASS' if cc['pass'] else 'FAIL'}): max |dev| {cc['max_abs_dev']}; jam rows |dF| N {cc['jam_dev_N']}")
    p(f"  this code: C1 {cc['mine']['C1_assist_min_Nm']}, C2 L1 {cc['mine']['C2_L1']}, C2 L2 {cc['mine']['C2_L2']}, unlit "
      f"{cc['mine']['unlit_full_stroke_3p5MPa_margin_7V4']}, seat {cc['mine']['seat_load_N']}; r 3.5 mm {cc['mine_r3p5']}")
    p('opening margin (stall / max C2 demand) vs rail:')
    for k, v in out['static']['opening_margin_vs_rail'].items():
        p(f"  {k:44s} {v['V']:.3f} V  T_stall {v['T_stall_Nm']:.4f} N m  margin {v['margin_C2']:.3f}")
    p(f"jam link tension (servo stalled opening, needle held, -10 % spring, pin friction 0): {out['jam_link_tension_N']}; r 3.5 mm {out['jam_link_tension_r3p5_N']}")
    p(f'33 throttle steps (11 x 3.5/5.0/5.5 MPa) x laws L0/L1/L2 (worst per step); GNC criterion t10-90 <= max(0.15 s, 0.8 dF / {SLEW:.0f} N/s):')
    for c in out['steps']:
        p(f"  {c['case']:62s} GNC {str(c['all_pass_gnc']):5s} strict {str(c['all_pass_strict_0p15']):5s} | open max {c['open_max_t10_90_s']:.3f} s "
          f"(min margin {c['open_min_margin']:.2f}) | close max {c['close_max_t10_90_s']:.3f} s (min margin {c['close_min_margin']:.2f}) | "
          f"assist min {c['assist_min_Nm']:+.3f} N m | no-progress max {c['noprog_max_s'] * 1e3:.1f} ms")
    c = out['steps'][1]
    p(f"  per step, {c['case']} (t10-90 s by law L0/L1/L2, worst margin):")
    for s in c['steps']:
        tl = s['t10_90_by_law_s']
        p(f"    {s['P_tank_MPa']:.1f} MPa {s['from']:5.3f}->{s['to']:5.3f} {s['dir']:5s} {s['x0_mm']:.3f}->{s['x1_mm']:.3f} mm  "
          f"{tl['L0']:.3f}/{tl['L1']:.3f}/{tl['L2']:.3f} (req {s['t_req_s']:.3f}, margin {s['margin']:.2f}, worst {s['worst_law']})")
    p('ENG-05 closing (SHUTDOWN, lift command ramp 0.2 m/s; L0 at tank pressure, chamber ambient):')
    for r in out['eng05_close']:
        p(f"  {r['case']:38s} {r['P_tank_MPa']:.1f} MPa from {int(100 * r['frac']):3d} % ({r['F0_N']:.0f} N, {r['x0_mm']:.3f} mm): "
          f"<10 % at {r['t_to_10pct_s']} s, seated {r['t_seated_s']} s  ENG-05 {'PASS' if r['pass_eng05'] else 'FAIL'}  assist min {r['assist_min_Nm']:+.3f}")
    p(f"  MECH meco_close_estimate vs this (nominal, seated): {out['eng05_vs_mech_estimate']}")
    p('full strokes 0 <-> 4.0 mm: t90/t99 [s] (seated for closing), end droop [mm]:')
    for k, v in out['full_stroke'].items():
        p(f"  {k:36s} " + ' | '.join(f"{n} {v[n]['t90_s']}/{v[n]['t99_s']}" + (f" seat {v[n]['t_seated_s']}" if v[n]['t_seated_s'] is not None else '') +
                                     f" ({v[n]['droop_mm']:+.3f})" for n in v))
    fc = out['firmware_constants_check']
    p(f"firmware constants vs v3: no-progress normal max {fc['noprog_normal_max_s']}; slowest flight full stroke {fc['slowest_full_stroke_flight']}; "
      f"slowest powered close {fc['slowest_powered_close_4mm_MEOP_L0']}; ground unlit N2 stroke {fc['ground_unlit_N2_full_stroke_3p5MPa']}")
    p(f"  firmware {fc['firmware']}")
    for k, v in fc['checks'].items():
        p(f"  {'PASS' if v else 'FAIL'}  {k}")
    p(f"  sensitivity ratios: {fc['sensitivity_ratios']}")
    b = out['bpnt1_backdrive']
    p(f"B-PNT-1 back-drive (L0, -10 % spring): min closing assist over the stroke {b['assist_min_over_stroke_m10_Nm']} N m; acceptance {b['acceptance']}")
    for r in b['rows']:
        p(f"  crank {r['crank_deg']:6.2f} deg (servo +{r['servo_deg_from_closed_cmd']:6.2f}) lift {r['lift_mm']:.3f} mm: spring -10 % {r['spring_m10_Nm']:.3f}, "
          f"assist bench {r['assist_bench_m10_Nm']:.3f} / 3.5 {r['assist_P3.5MPa_L0_m10_Nm']:.3f} / 5.5 {r['assist_P5.5MPa_L0_m10_Nm']:.3f} / "
          f"MEOP {r['assist_MEOP_L0_m10_Nm']:.3f} N m -> T_bd allowed {r['T_bd_allow_Nm']:.3f} N m")
    open(os.path.join(OUT, 'pintle_dynamics_v3.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def plot(out):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('WARNING: matplotlib not available; plot skipped')
        return
    tol = BCFG['tol']
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    mh, ml, m0 = Mech(+tol), Mech(-tol), Mech(0.0)
    phis = np.linspace(m0.phic, m0.phistop, 300)
    xs = [m0.lift(p) * 1e3 for p in phis]
    ax[0].plot(xs, [mh.torque(p, 0.0, True)[0] for p in phis], 'k', label='open demand, bench, +10 % spring')
    for law, ls in (('L1', '-'), ('L2', '--')):
        ax[0].plot(xs, [mh.torque(p, F_law(law, m0.lift(p), 3.5e6, P_AMB), True)[0] for p in phis], ls=ls, label=f'open demand, unlit 3.5 MPa {law}, +10 %')
    for k, P in C1_P.items():
        ax[0].plot(xs, [ml.torque(p, F_L0(m0.lift(p), P), False)[0] for p in phis], ls=':', label=f'close assist L0 {k}, -10 % spring')
    ax[0].axhline(stall_T(V_SLOW), color='r', lw=0.8, label=f'HV69 stall {V_SLOW:.2f} V')
    ax[0].axhline(stall_T(7.4) / 1.5, color='r', ls=':', lw=0.8, label='C2 limit (0.90/1.5)')
    ax[0].set_xlabel('needle lift [mm]'); ax[0].set_ylabel('torque at the dog [N m]'); ax[0].legend(fontsize=6); ax[0].grid(alpha=0.3)
    ax[0].set_title('MECH v2.4 drive: opening demand / closing assist')
    sv = Servo(V_SLOW)
    for P in (3.5e6, 5.5e6):
        tm = ThrustMap(P)
        for f0, f1, law in ((0.2, 1.0, 'L2'), (1.0, 0.2, 'L0')):
            tb = Tables(Mech(+tol if f1 > f0 else -tol), HotForce(P, law))
            x0, x1 = tm.lift(f0), tm.lift(f1)
            t, X, PH, TM, _, _ = run_profile(tb, sv, tb.m.phi_of(x0), lambda t, a=x0, b=x1: np.where(t < T_PRE, a, b), T_PRE + 0.5)
            sel = t >= T_PRE
            ax[1].plot(t[sel] - T_PRE, tm.F_vec(X[sel]), label=f'{int(100 * f0)}->{int(100 * f1)} %, {P / 1e6:.1f} MPa, hot {law}')
    ax[1].set_xlabel('time from command [s]'); ax[1].set_ylabel('quasi-steady thrust [N]'); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=7)
    ax[1].set_title(f'throttle steps, worst spring, plug {V_SLOW:.2f} V')
    for tl, ls in ((-tol, '--'), (0.0, '-')):
        m = Mech(tl)
        for P in (3.5e6, 5.5e6):
            tm = ThrustMap(P)
            tb = Tables(m, lambda x, P=P: F_L0(x, P))
            for frac in (0.75, 1.0):
                x0 = tm.lift(frac)
                t, X, PH, TM, _, _ = run_profile(tb, Servo(V_SLOW if tl < 0 else V_TYP), m.phi_of(x0),
                                                 lambda t, x0=x0: np.where(t < T_PRE, x0, x0 - 0.2 * np.maximum(0.0, t - T_PRE)), T_PRE + 0.3)
                sel = t >= T_PRE
                ax[2].plot(t[sel] - T_PRE, tm.F_vec(X[sel]), ls=ls, label=f'{int(100 * frac)} %, {P / 1e6:.1f} MPa, spring {int(100 * tl):+d} %')
    ax[2].axhline(F_ENG05, color='r', lw=0.8); ax[2].axvline(0.10, color='r', lw=0.8, label='ENG-05: < 50 N by 0.10 s')
    ax[2].set_xlabel('time from SHUTDOWN [s]'); ax[2].set_ylabel('quasi-steady thrust [N]'); ax[2].grid(alpha=0.3); ax[2].legend(fontsize=6)
    ax[2].set_title('MECO closing, L0 (no chamber tail-off)')
    fig.tight_layout()
    os.makedirs(os.path.join(OUT, 'plots'), exist_ok=True)
    fig.savefig(os.path.join(OUT, 'plots', 'pintle_dynamics_v3.png'), dpi=110)


if __name__ == '__main__':
    main()
