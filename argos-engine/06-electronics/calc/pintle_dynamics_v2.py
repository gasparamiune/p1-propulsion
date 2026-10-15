#!/usr/bin/env python3
"""HV69 pintle drive dynamics v2 on Mechanical's in-line v3.4 baseline profile (Electronics, 2026-10-12).

LEAD requests 2026-10-12 (Mechanical 03-cad/src/calcs/pintle_inline_v34_v2.json, then v2.1 = pintle_inline_v34_v2p1.json:
spring 0.19 N m + 0.17 N m/rad, PTFE bushings 15 mm apart; the lead named v2.1 as the file to use):
  1. re-run the HV69 throttle dynamics with the new spring law and link-force map; recheck the 33 throttle steps at
     7.4 V on the regulated rail, opening and closing, and the ENG-05 closing time from 75 % and 100 % at 3.5 and 5.5 MPa;
  2. (firmware) stall detection with back-off - the jam numbers used for it are reproduced here;
  3. B-PNT-1: unpowered back-drive torque target < 0.05 N m (= the minimum closing assist at MEOP, -10 % spring);
     v2.1 additions: carriage guide friction (mu 0.20 takes the MEOP assist below 0.05 N m) and the pintle-rail
     regulator output tolerance (the bearing jam case is set at 7.4 V plus that tolerance); then the S3 spring (0.30 + 0.10, MECH v2.2)
     and the rail raised ~1 % (pintle_rail_v2: 7.483 V typ) - LEAD decisions 2026-10-12.
What changed against pintle_mini_servo_v1 (needle compression spring F0 121.7 N + 5 N/mm, stem 4 mm, seal 25 N,
crank efficiency 0.90, tension link with 5 deg lost motion):
  - one-sided dog coupling: the servo drives OPENING only; the flat spiral spring on the crank plus the needle pressure
    close it; the servo dog only brakes the closing (the crank follows the dog while the closing assist is >= 0);
    below the seat angle (15 deg) the dog leaves the crank (lost motion moved into the coupling);
  - spiral spring T = T0 + k (phi - 15 deg), T0 0.18 N m, k 0.175 N m/rad, +/-10 % (MECH baseline.spring_law);
  - needle: stem 3.0 mm, seal friction 18.75 N, PTFE guide (mu 0.10, bushings 18 mm apart, link-plane offset 11 mm),
    link pins mu 0.15 on r 1.5 mm (MECH inputs.configs[baseline], guide_options, pin, y_link_plane_mm);
  - force/torque equations re-implemented here from Mechanical's published model (link force solved with the guide
    friction, explicit pin friction) and CROSS-CHECKED against every row of baseline.profile (independent code).
Servo model (unchanged from v1, ASSUMED where marked): DC-motor torque Ts (u - w/w_nl) along the published torque-speed
points (MKS HV69 retailer copies of MKS data), output inertia from a 10 ms mechanical time constant (5/20 ms sensitivity),
PD position loop with a 2 deg proportional band and zeta 0.7, 4 ms command latency; supply = regulated pintle rail (v2: 7.483 V typ, 7.395-7.570 V; LEAD +1 % decision).
Thrust = Combustion's quasi-steady throttle map (no chamber or fuel-mode lag; Combustion owns the tail-off).
Outputs: results/pintle_dynamics_v2.{json,txt}, results/plots/pintle_dynamics_v2.png. Nothing here is a measurement.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_ROOT = os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine')
OUT = os.path.join(HERE, '..', 'results')
COMB = os.path.join(ENGINE_ROOT, 'interfaces', 'combustion.json')
GNCF = os.path.join(ENGINE_ROOT, 'interfaces', 'gnc.json')
_MROOTS = (os.path.join(ENGINE_ROOT, '03-cad', 'src', 'calcs'), os.path.join(ENGINE_ROOT, '03-cad', 'calcs'),
           '/home/claude/work/mechanical/engine/03-cad/src/calcs')
MECH_CANDIDATES = [os.environ.get('MECH_PINTLE_JSON', '')] + [os.path.join(r, f) for f in ('pintle_inline_v34_v2p2.json',
                                                                                           'pintle_inline_v34_v2p1.json') for r in _MROOTS]
MECH_V21 = next((os.path.join(r, 'pintle_inline_v34_v2p1.json') for r in _MROOTS
                 if os.path.exists(os.path.join(r, 'pintle_inline_v34_v2p1.json'))), None)
SERVO_JSON = os.path.join(OUT, 'pintle_mini_servo_v1.json')
RAIL_JSON = next(p for p in (os.path.join(OUT, 'pintle_rail_v2.json'), os.path.join(OUT, 'pintle_rail_v1.json')) if os.path.exists(p))
P_AMB = 101325.0
F_MAX = 500.0
KGCM = 0.0980665


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


MECH_PATH = next(p for p in MECH_CANDIDATES if p and os.path.exists(p))
MECH_NOTE = ('hub path' if MECH_PATH.startswith(ENGINE_ROOT) else
             'Mechanical work folder (not yet in the hub when read; lead named it as published)')
M = json.load(open(MECH_PATH))
C = json.load(open(COMB))
G = json.load(open(GNCF))
SV = next(c for c in json.load(open(SERVO_JSON))['candidates'] if c['id'] == 'MKS HV69')
RAIL = json.load(open(RAIL_JSON))

# ------------------------------------------------------------------------------------------------ inputs (tagged)
INP = M['inputs']
CFG = INP['configs'][INP['baseline']]
GUIDE = INP['guide_options'][CFG['guide']]
MU_DES = GUIDE['mu']                                             # MECH v2.2 baseline config: PTFE guide mu 0.20 design case
MU_NOM = INP['guide_options'].get('PTFE_15mm', GUIDE)['mu']      # PTFE nominal assumption 0.10 (MECH guide_options)
SPR_V21 = json.load(open(MECH_V21))['baseline']['spring_law'] if MECH_V21 else None   # superseded v2.1 spring (evidence)
SPR_MECH = M['baseline']['spring_law']          # spring of the published baseline.profile (cross-check basis)
# LEAD decision 2026-10-12 (after Electronics showed the 0.19/0.17 spring has zero MEOP closing assist at guide mu 0.20):
# baseline spring = Mechanical's S3 choice for mu 0.20 (designs.S3_PTFE15mu20_plainpins.choice: T0 0.30 N m, k 0.10 N m/rad),
# so closing does not depend on the guide friction staying <= 0.10; B-PNT-1 acceptance: guide mu <= 0.20 with closing at MEOP
# demonstrated. Read from the MECH file (designs) unless the published baseline already carries it.
_S3 = M['designs']['S3_PTFE15mu20_plainpins']['choice']
if abs(SPR_MECH['T0_Nm_at_15deg'] - _S3['T0_Nm']) < 1e-9 and abs(SPR_MECH['k_Nm_per_rad'] - _S3['k_Nm_per_rad']) < 1e-9:
    SPR = dict(SPR_MECH, source='MECH baseline.spring_law')
else:
    SPR = {'T0_Nm_at_15deg': _S3['T0_Nm'], 'k_Nm_per_rad': _S3['k_Nm_per_rad'], 'tolerance': SPR_MECH['tolerance'],
           'source': 'LEAD 2026-10-12 decision: MECH designs.S3_PTFE15mu20_plainpins.choice (overrides the published '
                     f"baseline spring {SPR_MECH['T0_Nm_at_15deg']} N m + {SPR_MECH['k_Nm_per_rad']} N m/rad)"}
D_SEAT = C['gas_path']['injector']['seat_diameter_m']['v']
P_MEOP = C['operating_points']['tank_MEOP_Pa']['v']
MAP_PATH = C['operating_points']['throttle_map_csv']
if not os.path.exists(MAP_PATH):
    MAP_PATH = os.path.join(ENGINE_ROOT, MAP_PATH.split('/engine/', 1)[1])
GT = G['requirements']['throttle']
T1090 = GT['t10_90_s']['v']
SLEW = GT['slew_min_Fmax_per_s']['v'] * F_MAX
V_RAIL = RAIL['components']['Vout_V_min_typ_max'][1]   # [LEAD 2026-10-12] rail typ: v2 7.483 V (FB 100k/19.1k, pintle_rail_v2.py)
TAU_M = 0.010                     # [ASSUMED] HV69 mechanical time constant at 7.4 V (coreless; 5-20 ms sensitivity)
PB_DEG, ZETA, LAT = 2.0, 0.7, 0.004   # [ASSUMED] proportional band, damping, 333 Hz frame + 1 ms
W_EPS = 0.05                      # [rad/s] friction-direction smoothing at rest (numerical)
BLEND = 0.10e-3                   # [m] seated -> lifted pressure-force blend (Electronics model, used by Mechanical)
T_PRE = 0.30                      # [s] settle before a step
F_ENG05 = 0.10 * F_MAX            # [REQ ENG-05] < 10 % thrust within 0.10 s


class Mech:
    """Crank-slider + one-sided dog + spiral spring + needle forces, from MECH pintle_inline_v34_v2.json."""

    def __init__(s, tol=0.0, mu_g=None, P_scale=1.0, spring=None):
        cr = INP['crank']
        s.r, s.L = cr['r'] * 1e-3, cr['L'] * 1e-3
        s.phic, s.phicmd = math.radians(cr['phi_closed']), math.radians(cr['phi_cmd_closed'])
        s.xstop = cr['x_stop'] * 1e-3
        s.stem, s.fseal = CFG['stem_d'] * 1e-3, CFG['f_seal']
        s.mug = GUIDE['mu'] if mu_g is None else mu_g
        s.sg, s.yl = GUIDE['s_mm'] * 1e-3, INP['y_link_plane_mm'] * 1e-3
        s.mup, s.rp = CFG['pin_mu'], INP['pin']['r_mm'] * 1e-3
        sp = SPR if spring is None else spring
        s.T0, s.k, s.tol = sp['T0_Nm_at_15deg'], sp['k_Nm_per_rad'], tol
        s.A_st, s.A_se = math.pi / 4 * s.stem ** 2, math.pi / 4 * D_SEAT ** 2
        s.s0 = s._s(s.phic)
        s.phistop = s.phi_of(s.xstop)

    def _s(s, p):
        return s.r * math.cos(p) + math.sqrt(s.L ** 2 - (s.r * math.sin(p)) ** 2)

    def lift(s, p):
        return max(0.0, s.s0 - s._s(p)) if p > s.phic else 0.0

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

    def spring(s, p):
        return (1.0 + s.tol) * (s.T0 + s.k * (p - s.phic))

    def F_po(s, x, P):          # pressure force on the needle, + = OPENING [N] (chamber at ambient, MECH convention)
        dp = max(0.0, P - P_AMB)
        w = min(1.0, max(0.0, x / BLEND))
        return -(1 - w) * dp * (s.A_se - s.A_st) + w * dp * s.A_st

    def g(s, p):
        psi = math.asin(s.r * math.sin(p) / s.L)
        return 2.0 * s.yl / s.sg + abs(math.tan(psi))

    def link_force(s, p, P, closing):   # + = compression pushing the needle closed
        fp = s.F_po(s.lift(p), P)
        mg = s.mug * s.g(p)
        if closing:
            num = fp + s.fseal
            return num / (1 - mg) if num > 0 else num / (1 + mg)
        num = fp - s.fseal
        return num / (1 - mg) if num < 0 else num / (1 + mg)

    def pin_factor(s, p):
        psi = math.asin(s.r * math.sin(p) / s.L)
        a = s.r * math.cos(p) / (s.L * math.cos(psi))
        return abs(1 - a) + abs(a)

    def torque(s, p, P, opening):
        """Opening: servo torque required (+). Closing: closing surplus the crank applies to the dog (assist, + = follows)."""
        F = s.link_force(p, P, not opening)
        pl = s.mup * abs(F) * s.rp * s.pin_factor(p)
        return s.spring(p) - F * s.dxdphi(p) + (pl if opening else -pl), F


class Servo:
    def __init__(s, V=V_RAIL, tau_m=TAU_M):
        Vs = SV['V_rated'] if 'V_rated' in SV else [4.8, 6.0, 7.4, 8.2]
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

    def F_of(s, h):
        if h <= s.h[-1]:
            return float(np.interp(h, s.h, s.F))
        sl = (s.F[-1] - s.F[-2]) / (s.h[-1] - s.h[-2])
        return float(s.F[-1] + sl * (h - s.h[-1]))

    def lift(s, frac):
        k = round(frac, 4)
        return s.frac[k] if k in s.frac else float(np.interp(frac * F_MAX, s.F, s.h))


def simulate(m, sv, P, phid0, cmd, tmax, dt=1e-4, jam_closed=False):
    """Servo dog angle phid (crank frame). The crank follows the dog above the seat angle (closing assist >= 0 checked);
    below it the needle is seated and the dog is free. Returns t, lift, dog angle, motor torque, link force, assist_min."""
    n = int(tmax / dt)
    t = np.arange(n) * dt
    X = np.zeros(n); PH = np.zeros(n); TM = np.zeros(n); FL = np.zeros(n)
    phid, om = phid0, 0.0
    assist_min = float('inf')
    lo_stop = m.phicmd - math.radians(3.0)        # servo end stop beyond the closed command (ASSUMED)
    for i in range(n):
        tgt = cmd(max(0.0, t[i] - LAT))
        u = float(np.clip((tgt - phid) / sv.pb - sv.kd * om, -1.0, 1.0))
        Tm = sv.Ts * (u - om / sv.wnl)
        Tm = float(np.clip(Tm, -sv.Ts * (1 + abs(om) / sv.wnl), sv.Ts * (1 + abs(om) / sv.wnl)))
        Tl, F = 0.0, 0.0
        if phid >= m.phic:
            To, Fo = m.torque(phid, P, True)
            Tc, Fc = m.torque(phid, P, False)
            assist_min = min(assist_min, Tc)
            sgn = math.tanh(om / W_EPS)
            Tl = 0.5 * (To + Tc) + 0.5 * (To - Tc) * sgn
            F = Fo if om >= 0 else Fc
        om += (Tm - Tl) / sv.J * dt
        phid += om * dt
        if jam_closed and phid >= m.phic and om > 0:        # needle stuck in the seat: the dog stalls on the crank
            phid, om = m.phic, 0.0
        if phid >= m.phistop and om > 0:
            phid, om = m.phistop, 0.0
        if phid <= lo_stop and om < 0:
            phid, om = lo_stop, 0.0
        X[i] = m.lift(min(max(phid, m.phic), m.phistop)); PH[i] = phid; TM[i] = Tm; FL[i] = F
    return t, X, PH, TM, FL, assist_min


def step_metrics(m, sv, P, tm, f0, f1, ecu_slew=None, tmax=0.6):
    x0, x1 = tm.lift(f0), tm.lift(f1)
    p0, p1 = m.phi_of(x0), m.phi_of(x1)
    if ecu_slew:   # ECU lift-command slew (kPintleRateCmd 60 mm/s in RUN) before the inverse crank law
        def cmd(tt):
            if tt < T_PRE:
                return p0
            x = x0 + math.copysign(min(abs(x1 - x0), ecu_slew * (tt - T_PRE)), x1 - x0)
            return m.phi_of(x)
    else:
        def cmd(tt):
            return p0 if tt < T_PRE else p1
    t, X, PH, TM, FL, amin = simulate(m, sv, P, p0, cmd, T_PRE + tmax)
    F = np.array([tm.F_of(x) for x in X])
    sel = t >= T_PRE
    np_max = noprog_max(t[sel] - T_PRE, np.array([m.lift(cmd(tt)) for tt in t[sel]]), X[sel])
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
    dF_cmd = tm.F_of(x1) - tm.F_of(x0)
    treq = max(T1090, 0.8 * abs(dF_cmd) / SLEW)
    return {'from': f0, 'to': f1, 'dir': 'open' if f1 > f0 else 'close', 'dF_cmd_N': round(dF_cmd, 1),
            'x0_mm': round(x0 * 1e3, 3), 'x1_mm': round(x1 * 1e3, 3),
            'droop_start_N': round(Fa - tm.F_of(x0), 1), 'droop_end_N': round(Fb - tm.F_of(x1), 1),
            't10_90_s': round(t1090, 4), 't90_from_cmd_s': round(t90, 4), 't_req_s': round(treq, 4),
            'margin': round(treq / t1090, 2) if t1090 > 0 else None,
            'pass_gnc': bool(t1090 == t1090 and t1090 <= treq), 'pass_strict_0p15': bool(t1090 == t1090 and t1090 <= T1090),
            'peak_motor_torque_Nm': round(float(np.max(np.abs(TM[k0:]))), 3), 'assist_min_Nm': round(amin, 4) if amin < 1e9 else None,
            'link_F_max_N': round(float(np.max(np.abs(FL))), 1), 'noprog_max_s': np_max}


def close_time(m, sv, P, tm, frac, close_rate=0.200, tmax=0.6):
    """SHUTDOWN/MECO from a settled thrust fraction: ECU lift command ramps to 0 at kPintleCloseRate (0.2 m/s), then the
    dog goes to the closed command (10 deg). Times from the command: thrust (quasi-steady map) below 10 % F_max, needle seated."""
    x0 = tm.lift(frac)
    p0 = m.phi_of(x0)

    def cmd(tt):
        if tt < T_PRE:
            return p0
        x = max(0.0, x0 - close_rate * (tt - T_PRE))
        return m.phi_of(x) if x > 0 else m.phicmd
    t, X, PH, TM, FL, amin = simulate(m, sv, P, p0, cmd, T_PRE + tmax)
    sel = t >= T_PRE
    tt = t[sel] - T_PRE
    F = np.array([tm.F_of(x) for x in X[sel]])
    i10 = np.argmax(F < F_ENG05) if np.any(F < F_ENG05) else None
    iseat = np.argmax(X[sel] <= 1e-7) if np.any(X[sel] <= 1e-7) else None
    xcmd = np.array([max(0.0, x0 - close_rate * u) for u in tt])
    return {'frac': frac, 'P_tank_MPa': P / 1e6, 'x0_mm': round(x0 * 1e3, 3), 'F0_N': round(tm.F_of(x0), 1),
            'x10_mm': round(tm.lift(0.10) * 1e3, 4),
            't_to_10pct_s': round(float(tt[i10]), 4) if i10 is not None else None,
            't_seated_s': round(float(tt[iseat]), 4) if iseat is not None else None,
            'pass_eng05': bool(i10 is not None and tt[i10] <= 0.10), 'assist_min_Nm': round(amin, 4),
            'noprog_max_s': noprog_max(tt, xcmd, X[sel])}


def bench_close(m, sv, P_equiv, x_from, x_to, close_rate=0.200, tmax=0.6):
    """B-PNT-1 bench reference: SHUTDOWN command profile (0.2 m/s lift ramp, then the closed command) with the needle loaded
    as at P_equiv (MECH convention: upstream P_equiv, chamber ambient). Time from the command to lift <= x_to and to seated."""
    p0 = m.phi_of(x_from)

    def cmd(tt):
        if tt < T_PRE:
            return p0
        x = max(0.0, x_from - close_rate * (tt - T_PRE))
        return m.phi_of(x) if x > 0 else m.phicmd
    t, X, PH, TM, FL, amin = simulate(m, sv, P_equiv, p0, cmd, T_PRE + tmax)
    sel = t >= T_PRE
    tt = t[sel] - T_PRE
    ito = int(np.argmax(X[sel] <= x_to)) if np.any(X[sel] <= x_to) else None
    iseat = int(np.argmax(X[sel] <= 1e-7)) if np.any(X[sel] <= 1e-7) else None
    return {'x_from_mm': round(x_from * 1e3, 3), 'x_to_mm': round(x_to * 1e3, 4),
            't_to_x_s': round(float(tt[ito]), 4) if ito is not None else None,
            't_seated_s': round(float(tt[iseat]), 4) if iseat is not None else None}


def full_stroke(m, sv, P, opening, tmax=1.0):
    """0 -> 4.0 mm (from the closed command) or 4.0 mm -> seated. Times from the command to 90 % and 99 % of the SETTLED
    lift change (the servo's proportional band leaves a load-dependent droop at the top of the stroke, reported separately;
    in flight the Pc loop trims it out)."""
    x_full = 4.0e-3
    pa, pb = (m.phicmd, m.phi_of(x_full)) if opening else (m.phi_of(x_full), m.phicmd)
    t, X, PH, TM, FL, amin = simulate(m, sv, P, pa, lambda tt: pa if tt < T_PRE else pb, T_PRE + tmax)
    sel = t >= T_PRE
    xa = float(X[sel][0]); xb = float(np.mean(X[t >= t[-1] - 0.05]))
    g = (X[sel] - xa) / (xb - xa) if abs(xb - xa) > 1e-9 else np.zeros(int(np.sum(sel)))
    tt = t[sel] - T_PRE
    i90 = int(np.argmax(g >= 0.90)) if np.any(g >= 0.90) else None
    i99 = int(np.argmax(g >= 0.99)) if np.any(g >= 0.99) else None
    cmd_x = x_full if opening else 0.0
    return {'t90_s': round(float(tt[i90]), 4) if i90 is not None else None, 't99_s': round(float(tt[i99]), 4) if i99 is not None else None,
            'x_end_mm': round(xb * 1e3, 3), 'droop_mm': round((cmd_x - xb) * 1e3, 3),
            'noprog_max_s': noprog_max(tt, np.full_like(tt, cmd_x), X[sel]),
            'assist_min_Nm': round(amin, 4) if amin < 1e9 else None}


PROG_ERR, PROG_MIN = 0.15e-3, 0.02e-3     # firmware v2.6 kPintleStallErr_m / kPintleProgMin_m (src/core/config.h)


def noprog_max(tt, xcmd, X):
    """Firmware v2.6 stall monitor metric on a simulated record: longest interval with |cmd - lift| > PROG_ERR without a
    progress mark (lift moved >= PROG_MIN toward the command since the last mark). The time path trips at
    kPintleStallTime_s; this is the normal-operation value it must stay clear of."""
    worst, active, ref, t_ref = 0.0, False, 0.0, 0.0
    for k in range(len(tt)):
        e = xcmd[k] - X[k]
        if abs(e) > PROG_ERR:
            adv = (X[k] - ref) * (1.0 if e > 0 else -1.0)
            if not active or adv >= PROG_MIN:
                active, ref, t_ref = True, X[k], tt[k]
            worst = max(worst, tt[k] - t_ref)
        else:
            active = False
    return round(float(worst), 4)


def cross_check():
    """Re-implemented torque/force model vs Mechanical's baseline.profile rows (opening +10 % spring, closing -10 %)."""
    mo, mc = Mech(+SPR_MECH['tolerance'], spring=SPR_MECH), Mech(-SPR_MECH['tolerance'], spring=SPR_MECH)
    worst = {'open_T': 0.0, 'close_assist': 0.0, 'link_F': 0.0}
    for row in M['baseline']['profile']:
        p = math.radians(row['phi_deg'])
        for key, P in INP['pressures_Pa'].items():
            To, Fo = mo.torque(p, P, True)
            Tc, Fc = mc.torque(p, P, False)
            worst['open_T'] = max(worst['open_T'], abs(To - row[f'open_T_{key}_Nm']))
            worst['close_assist'] = max(worst['close_assist'], abs(Tc - row[f'close_assist_{key}_Nm']))
            worst['link_F'] = max(worst['link_F'], abs(Fo - row[f'link_F_open_{key}_N']), abs(Fc - row[f'link_F_close_{key}_N']))
    return {k: round(v, 4) for k, v in worst.items()}


def main():
    out = {'id': 'pintle_dynamics', 'version': 'v2', 'date': '2026-10-12', 'owner': 'Electronics',
           'inputs': {'mechanical': {'path': MECH_PATH, 'note': MECH_NOTE, 'version': M['version'], 'sha256_16': sha(MECH_PATH),
                                     'baseline': INP['baseline'], 'spring_law_profile': SPR_MECH, 'spring_used': SPR,
                                     'config': CFG, 'guide': GUIDE,
                                     'pin': INP['pin'], 'y_link_plane_mm': INP['y_link_plane_mm'], 'crank': INP['crank']},
                      'combustion.json': [C['version'], sha(COMB)], 'gnc.json': [G['version'], sha(GNCF)],
                      'throttle_map': [MAP_PATH, sha(MAP_PATH)], 'servo': {'id': SV['id'], 'V': [4.8, 6.0, 7.4, 8.2],
                      'T_kgcm': SV['T_kgcm'], 's60': SV['s60'], 'tag': SV.get('tag', 'retailer copies of MKS data')},
                      'rail_V': V_RAIL, 'rail_json': [os.path.basename(RAIL_JSON), RAIL['version']],
                      'assumed': {'tau_m_s': TAU_M, 'pb_deg': PB_DEG, 'zeta': ZETA, 'latency_s': LAT,
                                  'thrust': 'quasi-steady map, no chamber/fuel lag', 'chamber_for_needle_force': 'ambient (MECH convention)'}},
           'requirements': {'t10_90_s': T1090, 'slew_N_s': SLEW, 'criterion': 't10-90 <= max(t10_90_s, 0.8 |dF| / slew); strict: <= t10_90_s',
                            'ENG-05': '< 10 % F_max (50 N) within 0.10 s of the shutdown command'}}
    out['cross_check_vs_mech_profile'] = cross_check()
    m0 = Mech(0.0)
    out['geometry'] = {'phi_stop_deg': round(math.degrees(m0.phistop), 2), 'travel_cmd_deg': round(math.degrees(m0.phistop - m0.phicmd), 2),
                       'seat_load_nom_N': round(m0.T0 / m0.dxdphi(m0.phic), 1)}
    # static torque margins (opening +10 % spring)
    mp = Mech(+SPR['tolerance'])
    phis = np.linspace(m0.phic, m0.phistop, 300)
    sv74 = Servo(V_RAIL)
    stat = {}
    for key, P in INP['pressures_Pa'].items():
        dem = max(mp.torque(p, P, True)[0] for p in phis)
        stat[key] = {'open_demand_max_Nm': round(dem, 3), 'margin_rail_typ': round(sv74.Ts / dem, 2)}
    mm = Mech(-SPR['tolerance'])
    for key, P in INP['pressures_Pa'].items():
        stat[key]['assist_min_m10pct_Nm'] = round(min(mm.torque(p, P, False)[0] for p in phis), 3)
    out['static'] = stat
    # v2.1 B-PNT-1 addition: carriage guide friction. mu 0.20 on the baseline spring (and Mechanical's re-chosen spring)
    gsens = {}
    sens_rows = [('S3 spring, guide mu 0.10', MU_NOM, SPR), ('S3 spring, guide mu 0.20', MU_DES, SPR)]
    if SPR_V21 and abs(SPR_V21['T0_Nm_at_15deg'] - SPR['T0_Nm_at_15deg']) > 1e-9:
        sens_rows.append((f"superseded v2.1 spring {SPR_V21['T0_Nm_at_15deg']}/{SPR_V21['k_Nm_per_rad']}, guide mu 0.20", MU_DES, SPR_V21))
    for tag, mu, sp in sens_rows:
        mo_, mc_ = Mech(+SPR['tolerance'], mu, spring=sp), Mech(-SPR['tolerance'], mu, spring=sp)
        rec = {}
        for key, P in INP['pressures_Pa'].items():
            rec[key] = {'open_demand_max_Nm': round(max(mo_.torque(p, P, True)[0] for p in phis), 3),
                        'assist_min_m10pct_Nm': round(min(mc_.torque(p, P, False)[0] for p in phis), 3)}
        rec['margin_bench_rail_typ'] = round(sv74.Ts / rec['bench']['open_demand_max_Nm'], 2)
        gsens[tag] = rec
    out['guide_mu_sensitivity'] = gsens
    # jam at the seat (needle stuck closed): link tension with the servo at stall pushing the dog (-10 % spring).
    # v2.1: the bearing jam case is 7.4 V PLUS the pintle-rail regulator tolerance (LEAD); 8.2 V = Mechanical's case;
    # 8.4 V = regulator failed through (2S battery full), above the HV69 rating -> stall torque extrapolated (DERIVED).
    dx0 = m0.dxdphi(m0.phic)
    vmin, vtyp, vmax = RAIL['components']['Vout_V_min_typ_max']     # v2: includes the 0.1 % FB resistors (pintle_rail_v2.py)
    Vs = SV['V_rated']; Tk = [t_ * KGCM for t_ in SV['T_kgcm']]

    def ts_at(V):
        if V <= Vs[-1]:
            return float(np.interp(V, Vs, Tk))
        return Tk[-1] + (Tk[-1] - Tk[-2]) / (Vs[-1] - Vs[-2]) * (V - Vs[-1])
    jam = {}
    for lab, V in ((f'rail min {vmin:.3f} V', vmin), ('7.4 V (MECH basis)', 7.4), (f'rail typ {vtyp:.3f} V', vtyp),
                   (f'rail max {vmax:.3f} V (bearing jam design case, LEAD)', vmax), ('8.2 V (MECH case, HV69 rating)', 8.2),
                   ('8.4 V (regulator failed through, extrapolated)', 8.4)):
        Ts = ts_at(V)
        jam[lab] = {'V': round(V, 3), 'Ts_Nm': round(Ts, 4),
                    'link_tension_N': round((Ts - 0.9 * m0.T0) / (dx0 + m0.mup * m0.rp * m0.pin_factor(m0.phic)), 1)}
    out['jam_closed_link_tension_N'] = jam
    # opening margin = stall torque / max opening demand (+10 % spring) at the rail tolerance and at the servo plug
    I_ST, R_LEAD = 1.5, 0.030   # [ASSUMED] HV69 stall current (DERIVED bound 1.2-1.7 A, B-PNT-1); rail -> plug lead (sim.h)
    om = {}
    for mu in (MU_NOM, MU_DES):
        mo_ = Mech(+SPR['tolerance'], mu)
        dem = {key: max(mo_.torque(p, P, True)[0] for p in phis) for key, P in INP['pressures_Pa'].items()}
        rows = {}
        for lab, V in (('7.4 V (v1 nominal)', 7.4), (f'rail typ {vtyp:.3f} V', vtyp), (f'rail min {vmin:.3f} V', vmin),
                       (f'servo plug {vmin - R_LEAD * I_ST:.3f} V (rail min - 30 mOhm x 1.5 A)', vmin - R_LEAD * I_ST)):
            Ts = ts_at(V)
            rows[lab] = {'V': round(V, 3), 'Ts_Nm': round(Ts, 4), 'margin_bench': round(Ts / dem['bench'], 3),
                         'margin_flight_3p5': round(Ts / dem['P3.5MPa'], 3)}
        om[f'guide mu {mu:.2f}'] = {'open_demand_Nm': {k: round(v, 4) for k, v in dem.items()}, 'margins': rows}
    out['opening_margin_vs_rail'] = om
    out['rail_tolerance'] = {'source': os.path.basename(RAIL_JSON), 'Vout_min_typ_max_V': [vmin, vtyp, vmax],
                             'R_FB': [RAIL['components']['R_FB_UP_ohm'], RAIL['components']['R_FB_BT_ohm']],
                             'basis': 'TPS552882 VREF 1.188-1.212 V (DATASHEET) x divider incl. 0.1 % resistors (pintle_rail_v2); '
                                      'DC value - the jam is a static load'}
    # ---- 33 throttle steps, opening and closing, 7.4 V regulated rail, nominal spring and +/-10 %
    steps = [(0.125, 1.0), (0.2, 1.0), (0.25, 1.0), (0.2, 0.5), (0.5, 1.0), (0.5, 0.55), (0.95, 1.0),
             (1.0, 0.2), (1.0, 0.125), (0.5, 0.2), (0.55, 0.5)]
    cases = []
    for tag, tol, tau, mu_g, slew in (('guide mu 0.10 (PTFE nominal)', 0.0, TAU_M, MU_NOM, None),
                                      ('guide mu 0.20 (design case)', 0.0, TAU_M, MU_DES, None),
                                      ('spring -10 %, mu 0.20', -0.1, TAU_M, MU_DES, None),
                                      ('spring +10 %, mu 0.20', +0.1, TAU_M, MU_DES, None),
                                      ('spring +10 %, mu 0.10', +0.1, TAU_M, MU_NOM, None),
                                      ('tau_m 20 ms, mu 0.20', 0.0, 0.020, MU_DES, None),
                                      ('mu 0.20 + ECU 60 mm/s command slew', 0.0, TAU_M, MU_DES, 0.060)):
        m = Mech(tol, mu_g)
        sv = Servo(V_RAIL, tau)
        rec = {'case': tag, 'V': V_RAIL, 'spring_tol': tol, 'tau_m_s': tau, 'guide_mu': m.mug, 'ecu_slew_m_s': slew, 'steps': []}
        for P in (3.5e6, 5.0e6, 5.5e6):
            tm = ThrustMap(P)
            for f0, f1 in steps:
                r = step_metrics(m, sv, P, tm, f0, f1, ecu_slew=slew)
                r['P_tank_MPa'] = P / 1e6
                rec['steps'].append(r)
        S = rec['steps']
        rec['n_steps'] = len(S)
        rec['all_pass_gnc'] = all(s['pass_gnc'] for s in S)
        rec['all_pass_strict_0p15'] = all(s['pass_strict_0p15'] for s in S)
        for d in ('open', 'close'):
            sd = [s for s in S if s['dir'] == d]
            rec[f'{d}_max_t10_90_s'] = max(s['t10_90_s'] for s in sd)
            rec[f'{d}_min_margin'] = min(s['margin'] for s in sd if s['margin'] is not None)
            rec[f'{d}_worst'] = max(sd, key=lambda s: s['t10_90_s'])
        rec['assist_min_Nm'] = min(s['assist_min_Nm'] for s in S if s['assist_min_Nm'] is not None)
        cases.append(rec)
    out['steps'] = cases
    # ---- ENG-05 closing from 75 % and 100 % at 3.5 and 5.5 MPa
    eng05 = []
    for tag, tol, tau, mu_g in (('mu 0.10', 0.0, TAU_M, MU_NOM), ('mu 0.20', 0.0, TAU_M, MU_DES),
                                ('spring -10 %, mu 0.20', -0.1, TAU_M, MU_DES), ('spring +10 %, mu 0.20', +0.1, TAU_M, MU_DES),
                                ('spring -10 %, mu 0.20, tau_m 20 ms', -0.1, 0.020, MU_DES)):
        m = Mech(tol, mu_g); sv = Servo(V_RAIL, tau)
        for P in (3.5e6, 5.5e6):
            tm = ThrustMap(P)
            for frac in (0.75, 1.0):
                r = close_time(m, sv, P, tm, frac)
                r['case'] = tag
                eng05.append(r)
    out['eng05_close'] = eng05
    # ---- full strokes and the B-PNT-1 bench closing reference (needle load equivalent to 25 bar)
    fs = {}
    for tag, tol, mu_g in (('mu 0.10', 0.0, MU_NOM), ('mu 0.20', 0.0, MU_DES), ('spring -10 %, mu 0.20', -0.1, MU_DES),
                           ('spring +10 %, mu 0.20', 0.1, MU_DES)):
        m = Mech(tol, mu_g)
        fs[tag] = {'open_bench': full_stroke(m, sv74, P_AMB, True), 'open_MEOP': full_stroke(m, sv74, P_MEOP, True),
                   'close_bench': full_stroke(m, sv74, P_AMB, False), 'close_25bar_equiv': full_stroke(m, sv74, 25e5, False),
                   'close_MEOP': full_stroke(m, sv74, P_MEOP, False)}
    out['full_stroke'] = fs
    # ---- B-PNT-1 bench closing references (spring fitted, needle load equivalent to 25 bar, MECH convention)
    A_st, A_se = m0.A_st, m0.A_se
    tm35, tm55 = ThrustMap(3.5e6), ThrustMap(5.5e6)
    bpnt = {'needle_load_25bar_equiv_N': {'lifted_opening_N': round((25e5 - P_AMB) * A_st, 2),
                                          'seated_closing_N': round((25e5 - P_AMB) * (A_se - A_st), 2),
                                          'basis': 'MECH force model: upstream 25 bar, chamber ambient; lifted = P x A_stem (opening), '
                                                   'seated = P x (A_seat - A_stem) (closing)'}, 'cases': {}}
    bpnt['needle_load_MEOP_equiv_N'] = {'lifted_opening_N': round((P_MEOP - P_AMB) * A_st, 2),
                                        'seated_closing_N': round((P_MEOP - P_AMB) * (A_se - A_st), 2)}
    for tag, tol, mu_g in (('mu 0.10', 0.0, MU_NOM), ('mu 0.20', 0.0, MU_DES), ('spring -10 %, mu 0.20', -0.1, MU_DES),
                           ('spring +10 %, mu 0.20', 0.1, MU_DES)):
        m = Mech(tol, mu_g)
        bpnt['cases'][tag] = {
            'full_4mm_to_seat': bench_close(m, sv74, 25e5, 4.0e-3, 1e-7),
            'full_4mm_to_seat_MEOP_equiv': bench_close(m, sv74, P_MEOP, 4.0e-3, 1e-7),
            'F75_3p5_to_x10': bench_close(m, sv74, 25e5, tm35.lift(0.75), tm35.lift(0.10)),
            'F100_3p5_to_x10': bench_close(m, sv74, 25e5, tm35.lift(1.0), tm35.lift(0.10)),
            'F75_5p5_to_x10': bench_close(m, sv74, 25e5, tm55.lift(0.75), tm55.lift(0.10))}
    out['bpnt1_close_25bar_equiv'] = bpnt
    # ---- unpowered back-drive: the spring alone must close against the unpowered servo's drag
    out['backdrive'] = {'assist_min_MEOP_m10pct_Nm': stat['MEOP']['assist_min_m10pct_Nm'],
                        'assist_min_5p5_m10pct_Nm': stat['P5.5MPa']['assist_min_m10pct_Nm'],
                        'assist_min_MEOP_m10pct_guide_mu0p20_Nm': gsens['S3 spring, guide mu 0.20']['MEOP']['assist_min_m10pct_Nm'],
                        'target_Nm': 0.05, 'tag': 'LEAD 2026-10-12 performance target; B-PNT-1 measures it (unpowered servo, torque to turn the '
                        'output shaft slowly in the closing direction, and at ~2 rad/s); safety shutoff = NC isolation valve'}
    # ---- firmware v2.6 stall-monitor clearance: longest no-progress interval in normal operation (all simulated cases)
    allnp = [s_['noprog_max_s'] for c in cases for s_ in c['steps']] + [r['noprog_max_s'] for r in eng05] + \
            [v[k]['noprog_max_s'] for v in fs.values() for k in v]
    out['stall_monitor_clearance'] = {'noprog_max_s': max(allnp), 'n_records': len(allnp),
                                      'criteria': {'err_m': PROG_ERR, 'prog_min_m': PROG_MIN},
                                      'note': 'normal-operation maximum of the interval without a 20 um progress mark while |cmd - lift| > '
                                              '0.15 mm; firmware time path kPintleStallTime_s must exceed it with margin'}
    with open(os.path.join(OUT, 'pintle_dynamics_v2.json'), 'w') as f:
        json.dump(out, f, indent=1)
    write_txt(out)
    plot(out)


def write_txt(out):
    L = []
    p = L.append
    i = out['inputs']['mechanical']
    p(f'pintle_dynamics_v2 (Electronics 2026-10-12): MKS HV69 on the MECH in-line v3.4 baseline, regulated {V_RAIL:.3f} V rail '
      f"({out['inputs']['rail_json'][0]})")
    p(f"MECH {os.path.basename(i['path'])} {i['version']} sha {i['sha256_16']} ({i['note']}); config {i['baseline']}")
    p(f"spring used: T0 {SPR['T0_Nm_at_15deg']} N m + {SPR['k_Nm_per_rad']} N m/rad (+/-{int(round(100 * SPR['tolerance']))} %) - {SPR['source']}")
    p(f"combustion.json {out['inputs']['combustion.json'][0]}, gnc.json {out['inputs']['gnc.json'][0]}; servo {out['inputs']['servo']['id']}; "
      f"ASSUMED tau_m {TAU_M * 1e3:.0f} ms, pb {PB_DEG} deg, zeta {ZETA}, latency {LAT * 1e3:.0f} ms; thrust = quasi-steady map")
    cc = out['cross_check_vs_mech_profile']
    p(f"cross-check vs MECH baseline.profile (independent code): max |open T| {cc['open_T']} N m, |close assist| {cc['close_assist']} N m, "
      f"|link F| {cc['link_F']} N")
    g = out['geometry']
    p(f"geometry: stop {g['phi_stop_deg']} deg, command travel {g['travel_cmd_deg']} deg, nominal seat load {g['seat_load_nom_N']} N")
    p(f'static, guide mu {MU_DES} design case (opening +10 % spring / closing -10 % spring):')
    for k, v in out['static'].items():
        p(f"  {k:8s} open demand {v['open_demand_max_Nm']:.3f} N m (margin {v['margin_rail_typ']:.2f} at {V_RAIL:.3f} V)  min closing assist {v['assist_min_m10pct_Nm']:+.3f} N m")
    p(f"jam at the seat, servo at stall: link tension {out['jam_closed_link_tension_N']}")
    p(f'33 throttle steps (11 steps x 3.5/5.0/5.5 MPa), {V_RAIL:.3f} V; criterion GNC t10-90 <= max(0.15 s, 0.8 dF/1000 N/s) '
      '(LEAD: the acceptance criterion); strict <= 0.15 s (information):')
    for c in out['steps']:
        p(f"  {c['case']:38s} GNC all pass {str(c['all_pass_gnc']):5s} strict {str(c['all_pass_strict_0p15']):5s} | open max {c['open_max_t10_90_s']:.3f} s "
          f"(min margin {c['open_min_margin']:.2f}) | close max {c['close_max_t10_90_s']:.3f} s (min margin {c['close_min_margin']:.2f}) | "
          f"assist min {c['assist_min_Nm']:+.3f} N m")
    c = out['steps'][1]
    p(f"  {c['case']}, per step (t10-90 s / margin):")
    for s in c['steps']:
        p(f"    {s['P_tank_MPa']:.1f} MPa {s['from']:5.3f}->{s['to']:5.3f} {s['dir']:5s} {s['x0_mm']:.3f}->{s['x1_mm']:.3f} mm  t10-90 {s['t10_90_s']:.3f} "
          f"(req {s['t_req_s']:.3f}, margin {s['margin']:.2f})  peak Tm {s['peak_motor_torque_Nm']:.3f} N m  droop end {s['droop_end_N']:+.1f} N")
    p('ENG-05 closing (SHUTDOWN at 0.2 m/s command ramp; thrust < 50 N within 0.10 s):')
    for r in out['eng05_close']:
        p(f"  {r['case']:28s} {r['P_tank_MPa']:.1f} MPa from {int(100 * r['frac']):3d} % ({r['F0_N']:.0f} N, {r['x0_mm']:.3f} mm): "
          f"<10 % ({r['x10_mm']} mm) at {r['t_to_10pct_s']} s, seated {r['t_seated_s']} s  ENG-05 {'PASS' if r['pass_eng05'] else 'FAIL'}  "
          f"assist min {r['assist_min_Nm']:+.3f}")
    p(f'full strokes ({V_RAIL:.3f} V): t90 / t99 of the settled change [s], end droop [mm] (P-band of the servo; the Pc loop trims it in flight)')
    for k, v in out['full_stroke'].items():
        p(f"  {k:14s} " + ' | '.join(f"{n} {v[n]['t90_s']}/{v[n]['t99_s']} (droop {v[n]['droop_mm']:+.3f})"
                                     for n in ('open_bench', 'open_MEOP', 'close_bench', 'close_25bar_equiv', 'close_MEOP')))
    bp = out['bpnt1_close_25bar_equiv']
    nl = bp['needle_load_25bar_equiv_N']
    p(f"B-PNT-1 closing with the spring fitted, needle load equivalent to 25 bar ({nl['lifted_opening_N']} N opening when lifted, "
      f"{nl['seated_closing_N']} N closing when seated), SHUTDOWN profile, {V_RAIL:.3f} V:")
    for k, v in bp['cases'].items():
        p(f"  {k:28s} 4.0 mm -> seated {v['full_4mm_to_seat']['t_seated_s']} s (MEOP-equiv {v['full_4mm_to_seat_MEOP_equiv']['t_seated_s']} s) | 75 % 3.5 MPa {v['F75_3p5_to_x10']['x_from_mm']} -> "
          f"{v['F75_3p5_to_x10']['x_to_mm']} mm (10 %) {v['F75_3p5_to_x10']['t_to_x_s']} s | 100 % 3.5 MPa -> 10 % {v['F100_3p5_to_x10']['t_to_x_s']} s | "
          f"75 % 5.5 MPa -> 10 % {v['F75_5p5_to_x10']['t_to_x_s']} s")
    b = out['backdrive']
    p(f"unpowered back-drive: spring assist min {b['assist_min_MEOP_m10pct_Nm']} N m at MEOP (-10 % spring), {b['assist_min_5p5_m10pct_Nm']} N m at 5.5 MPa; "
      f"{b['assist_min_MEOP_m10pct_guide_mu0p20_Nm']} N m at MEOP with guide mu 0.20; B-PNT-1 target < {b['target_Nm']} N m")
    p('guide friction sensitivity (B-PNT-1 v2.1 addition):')
    for k, v in out['guide_mu_sensitivity'].items():
        p(f"  {k:52s} assist min bench/3.5/5.5/MEOP " + '/'.join(f"{v[q]['assist_min_m10pct_Nm']:+.3f}" for q in ('bench', 'P3.5MPa', 'P5.5MPa', 'MEOP')) +
          f" N m; opening margin bench {v['margin_bench_rail_typ']} at {V_RAIL:.3f} V")
    p(f"  MEOP-equivalent needle load for the closing demonstration: {bp['needle_load_MEOP_equiv_N']['lifted_opening_N']} N opening lifted, "
      f"{bp['needle_load_MEOP_equiv_N']['seated_closing_N']} N closing seated")
    rt = out['rail_tolerance']
    p(f"pintle rail output ({rt['source']}): min/typ/max {rt['Vout_min_typ_max_V']} V (VREF tolerance and 0.1 % FB resistors)")
    p('opening margin (stall torque / max opening demand, +10 % spring) vs rail voltage:')
    for g_, v in out['opening_margin_vs_rail'].items():
        d = v['open_demand_Nm']
        p(f"  {g_}: demand bench {d['bench']:.3f} / 3.5 MPa {d['P3.5MPa']:.3f} / 5.5 MPa {d['P5.5MPa']:.3f} / MEOP {d['MEOP']:.3f} N m")
        for lab, r in v['margins'].items():
            p(f"    {lab:52s} Ts {r['Ts_Nm']:.4f} N m: margin bench {r['margin_bench']:.3f}, flight (3.5 MPa) {r['margin_flight_3p5']:.3f}")
    p('jam at the seat (needle stuck closed), servo at stall, -10 % spring: link tension')
    for k, v in out['jam_closed_link_tension_N'].items():
        p(f"  {k:52s} Ts {v['Ts_Nm']:.4f} N m -> {v['link_tension_N']:.1f} N")
    sc = out['stall_monitor_clearance']
    p(f"stall-monitor clearance: longest no-progress interval in normal operation {sc['noprog_max_s']} s over {sc['n_records']} records "
      f"(|cmd - lift| > {sc['criteria']['err_m'] * 1e3} mm, mark = {sc['criteria']['prog_min_m'] * 1e6:.0f} um toward the command)")
    open(os.path.join(OUT, 'pintle_dynamics_v2.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def plot(out):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('WARNING: matplotlib not available; plot skipped (run with /opt/engine-venv/bin/python)')
        return
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    phis = np.linspace(Mech().phic, Mech().phistop, 200)
    for P, lab in ((P_AMB, 'bench'), (3.5e6, '3.5 MPa'), (5.5e6, '5.5 MPa'), (P_MEOP, 'MEOP 7.0 MPa')):
        mo, mc = Mech(0.1), Mech(-0.1)
        ax[0].plot([Mech().lift(p) * 1e3 for p in phis], [mo.torque(p, P, True)[0] for p in phis], label=f'open demand +10 % spring, {lab}')
        ax[0].plot([Mech().lift(p) * 1e3 for p in phis], [mc.torque(p, P, False)[0] for p in phis], ls='--', label=f'close assist -10 % spring, {lab}')
    ax[0].axhline(Servo(V_RAIL).Ts, color='k', lw=0.8, label=f'HV69 stall {V_RAIL:.2f} V')
    ax[0].axhline(Servo(V_RAIL).Ts / 1.5, color='k', ls=':', lw=0.8, label='stall / 1.5')
    ax[0].axhline(0.05, color='r', ls=':', lw=0.8, label='back-drive target 0.05 N m')
    ax[0].set_xlabel('needle lift [mm]'); ax[0].set_ylabel('torque at the dog [N m]'); ax[0].legend(fontsize=6); ax[0].grid(alpha=0.3)
    ax[0].set_title('MECH v3.4 baseline: opening demand and closing assist')
    m = Mech(0.0); sv = Servo(V_RAIL)
    for P in (3.5e6, 5.5e6):
        tm = ThrustMap(P)
        for f0, f1, ls in ((0.2, 1.0, '-'), (1.0, 0.2, '--')):
            x0, x1 = tm.lift(f0), tm.lift(f1)
            p0, p1 = m.phi_of(x0), m.phi_of(x1)
            t, X, PH, TM, FL, _ = simulate(m, sv, P, p0, lambda tt, a=p0, b=p1: a if tt < T_PRE else b, T_PRE + 0.5)
            sel = t >= T_PRE
            ax[1].plot(t[sel] - T_PRE, [tm.F_of(x) for x in X[sel]], ls=ls, label=f'{int(100 * f0)}->{int(100 * f1)} %, {P / 1e6:.1f} MPa')
    ax[1].set_xlabel('time from command [s]'); ax[1].set_ylabel('quasi-steady thrust [N]'); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=7)
    ax[1].set_title(f'HV69 {V_RAIL:.2f} V throttle steps (actuator-limited)')
    for tol, ls in ((-0.1, '--'), (0.0, '-')):
        m = Mech(tol)
        for P in (3.5e6, 5.5e6):
            tm = ThrustMap(P)
            for frac in (0.75, 1.0):
                x0 = tm.lift(frac); p0 = m.phi_of(x0)
                cmd = lambda tt, x0=x0, p0=p0, m=m: p0 if tt < T_PRE else (m.phi_of(max(0.0, x0 - 0.2 * (tt - T_PRE))) if x0 - 0.2 * (tt - T_PRE) > 0 else m.phicmd)
                t, X, PH, TM, FL, _ = simulate(m, sv, P, p0, cmd, T_PRE + 0.3)
                sel = t >= T_PRE
                ax[2].plot(t[sel] - T_PRE, [tm.F_of(x) for x in X[sel]], ls=ls, label=f'{int(100 * frac)} %, {P / 1e6:.1f} MPa, spring {int(100 * tol):+d} %')
    ax[2].axhline(F_ENG05, color='r', lw=0.8); ax[2].axvline(0.10, color='r', lw=0.8, label='ENG-05: < 50 N by 0.10 s')
    ax[2].set_xlabel('time from SHUTDOWN [s]'); ax[2].set_ylabel('quasi-steady thrust [N]'); ax[2].grid(alpha=0.3); ax[2].legend(fontsize=6)
    ax[2].set_title('MECO closing (no chamber tail-off)')
    fig.tight_layout()
    os.makedirs(os.path.join(OUT, 'plots'), exist_ok=True)
    fig.savefig(os.path.join(OUT, 'plots', 'pintle_dynamics_v2.png'), dpi=110)


if __name__ == '__main__':
    main()
