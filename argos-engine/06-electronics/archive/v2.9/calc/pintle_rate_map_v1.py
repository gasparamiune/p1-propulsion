#!/usr/bin/env python3
"""Pintle thrust-rate map for the GNC 6-DOF: achievable dF/dt vs tank pressure and thrust (Electronics, 2026-10-13, v1).

Request (coordinator 2026-10-13, ENG-03 provisional decision, LEAD): GNC flies the achievable-rate model in the 6-DOF. Publish the
achievable dF/dt opening and closing vs P_tank 3.5-5.5 MPa and the current thrust (or lift), for the corner (spring +10 % opening /
-10 % closing, servo plug at the rail static minimum) and the nominal (spring nominal, rail typ), with the servo time constant used,
so GNC can model a state-dependent rate limit plus lag. Follow-up: would less spring torque at full lift change the result (the only
hard constraint: unpowered closing at the MEOP-equivalent load)?

Inputs (read and hashed; nothing typed in from other teams; the model is calc/pintle_dynamics_v3.py, imported, not changed):
  Combustion  throttle_map_v2.csv (thrust vs lift at each P_tank, SIM); needle_force_v2p3 csv (L0/L1/L2 hot-fire needle force, DERIVED)
  Mechanical  pintle_inline_v34_v2p4.json (crank, spring T0/k/tol, friction, C1 criterion text: MECH); pintle_crank_table_v1.json
              (45 hot-fire rows, used as a cross-check of the opening torque)
  Electronics pintle_mini_servo_v1.json (HV69 stall torque and no-load speed vs V: retailer copies of MKS data, TO-CONFIRM);
              pintle_rail_v3.json (rail static minimum / typ, DERIVED); eng03_slew_check_v1.json (dynamic 2500 N/s ramp evidence)
Model:
  rate map, quasi-static, per state and needle-force law L0 / L1 / L2 (envelope = minimum over the three laws):
    R_open  = |dF/dx| dx/dphi w_nl(V) max(0, 1 - T_open / T_stall(V))
    R_close = |dF/dx| dx/dphi w_nl(V) min(1, max(0, 1 + T_assist / T_stall(V)))   spring assist NOT credited, a resisting load debited
    (linear torque-speed line between stall and no-load: ASSUMED; dF/dx: central difference +/- 0.02 mm on the Combustion map,
    which is piecewise linear in lift, so dF/dx is piecewise constant between map rows)
  lag (servo model of pintle_dynamics_v3, ASSUMED): command latency 4 ms; inside the 2 deg proportional band the position loop is
    second order, w_n = sqrt(T_stall / (PB J)), zeta 0.7, J = tau_m T_stall(7.4 V) / w_nl(7.4 V), tau_m 10 ms;
    first-order equivalent tau_eq = 2 zeta / w_n (the ramp-following lag of that loop)
  reduced model offered to GNC:  dF/dt = clip((F_cmd(t - T_lat) - F) / tau_eq, -R_close(P_tank, F), +R_open(P_tank, F))
  validation: reduced model vs the nonlinear drive simulation (pintle_dynamics_v3.run_profile: servo PD + torque-speed line +
    load torque tables + friction hysteresis) on large and small steps and on 2500 N/s ramps, per law, both cases
  spring follow-up: the spring torque the closing constraints actually need at each crank angle (MECH C1 L0 targets, -10 % spring,
    plus unpowered closing along the hot-fire line), a constant-torque variant (k = 0, seat preload T0 kept) and that floor profile
Outputs: results/pintle_rate_map_v1.{json,csv,txt}. Analysis on SIM / DERIVED / ASSUMED inputs, not a measurement; B-PNT-1 measures.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results')
F_MAX = 500.0                 # [REQ] F_max (sea level)
RAMP_REQ = 5.0 * F_MAX        # [REQ ENG-03 amended 2026-10-13] 2500 N/s under load
FRACS = [0.125] + [round(0.15 + 0.05 * i, 2) for i in range(18)]        # [DESIGN] 12.5 % and 15-100 % in 5 % steps (19 levels)
DL = 0.02e-3                  # [DESIGN] central-difference half step for dF/dx (as eng03_slew_check_v1)
VAL_P = (3.5, 4.5, 5.5)       # [DESIGN] validation tank pressures
VAL_PROFILES = [('step', 0.25, 1.0), ('step', 1.0, 0.25), ('step', 0.5, 0.55), ('step', 0.55, 0.5),
                ('ramp', 0.125, 1.0), ('ramp', 1.0, 0.125)]


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


def load_pd3(er):
    """Import calc/pintle_dynamics_v3.py as a module (its argparse reads sys.argv at import: give it only --engine-root)."""
    argv0 = sys.argv
    sys.argv = [argv0[0], '--engine-root', er]
    try:
        spec = importlib.util.spec_from_file_location('pd3', os.path.join(HERE, 'pintle_dynamics_v3.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv0
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    ap.add_argument('--quick', action='store_true', help='validation on one pressure only (development)')
    a = ap.parse_args()
    er = a.engine_root
    pd3 = load_pd3(er)
    tol = pd3.BCFG['tol']
    mech_tab = next(p for p in (os.path.join(er, '03-cad', 'calcs', 'pintle_crank_table_v1.json'),
                                os.path.join(er, '03-cad', 'src', 'calcs', 'pintle_crank_table_v1.json')) if os.path.exists(p))
    MT = json.load(open(mech_tab, encoding='utf-8'))
    rows45 = MT['hot_fire_line_rows']
    P_LIST = sorted({r['P_tank_MPa'] for r in rows45})
    eng03_p = os.path.join(RES, 'eng03_slew_check_v1.json')
    E3 = json.load(open(eng03_p, encoding='utf-8'))

    CASES = {
        'corner': {'label': 'spring +10 % opening / -10 % closing, servo plug at the rail static minimum', 'V': pd3.V_SLOW,
                   'tol_open': +tol, 'tol_close': -tol, 'mech_kw': {}, 'role': 'design / dispersion bound'},
        'nominal': {'label': 'spring nominal, rail typ', 'V': pd3.V_TYP, 'tol_open': 0.0, 'tol_close': 0.0, 'mech_kw': {},
                    'role': 'nominal'},
        'corner_friction_sens': {'label': 'corner + MECH guide-friction sensitivity (mu_g 0.02, S 5 N)', 'V': pd3.V_SLOW,
                                 'tol_open': +tol, 'tol_close': -tol, 'mech_kw': {'mu_g': 0.02, 'S': 5.0},
                                 'role': 'sensitivity only (MECH v2.4 sensitivity row), not a design case'},
    }
    maps = {P: pd3.ThrustMap(P * 1e6) for P in P_LIST}
    _tb = {}

    def tables(tol_, P, law, mech_kw=None, mech=None, key=None):
        k = (key or tol_, P, law, json.dumps(mech_kw or {}, sort_keys=True))
        if k not in _tb:
            m = mech if mech is not None else pd3.Mech(tol_, **(mech_kw or {}))
            _tb[k] = pd3.Tables(m, pd3.HotForce(P * 1e6, law))
        return _tb[k]

    def servo_info(V):
        sv = pd3.Servo(V)
        wn = math.sqrt(sv.Ts / (sv.pb * sv.J))
        two_zw = sv.Ts * (sv.kd + 1.0 / sv.wnl) / sv.J
        zeta = two_zw / (2.0 * wn)
        return sv, {'V_plug': round(V, 4), 'T_stall_Nm': round(sv.Ts, 4), 'w_noload_rad_s': round(sv.wnl, 3),
                    'J_output_kgm2': float(f'{sv.J:.4g}'), 'tau_m_s': sv.tau_m, 'PB_deg': pd3.PB_DEG, 'zeta': round(zeta, 3),
                    'w_n_rad_s': round(wn, 1), 'f_n_Hz': round(wn / (2 * math.pi), 2), 'tau_eq_s': round(2 * zeta / wn, 5),
                    'latency_s': pd3.LAT, 'kd_s': float(f'{sv.kd:.4g}'),
                    'tags': {'T_stall_Nm': 'DATASHEET (retailer copy of MKS data, TO-CONFIRM) interpolated at V_plug',
                             'w_noload_rad_s': 'DATASHEET (s/60 deg at no load, retailer copy, TO-CONFIRM) interpolated',
                             'tau_m_s': 'ASSUMED', 'PB_deg': 'ASSUMED', 'zeta': 'ASSUMED (0.7 design target of the servo model)',
                             'latency_s': 'ASSUMED (servo frame + internal processing; B-PNT-1 measures)',
                             'J_output_kgm2': 'DERIVED from tau_m and the 7.4 V line', 'w_n_rad_s': 'DERIVED', 'tau_eq_s': 'DERIVED'}}

    # ------------------------------------------------------------------ rate map on the grid
    def state(P, frac):
        tm = maps[P]
        x = float(tm.lift(frac))
        F = float(tm.F_vec(x))
        xl = max(0.0, x - DL)
        dFdx = float((tm.F_vec(x + DL) - tm.F_vec(xl)) / (x + DL - xl))
        return tm, x, F, dFdx

    def rates(case, P, frac, sv, spring_override=None):
        """Per-law opening / closing rate at one state. spring_override: (mech_open, mech_close, key) for the spring study."""
        c = CASES[case]
        tm, x, F, dFdx = state(P, frac)
        if spring_override is None:
            mo = pd3.Mech(c['tol_open'], **c['mech_kw']); mc = pd3.Mech(c['tol_close'], **c['mech_kw'])
            ko, kc = None, None
        else:
            mo, mc, key = spring_override
            ko, kc = key + '_open', key + '_close'
        phi = mo.phi_of(x)
        dxdphi = mo.dxdphi(phi)
        gain = abs(dFdx) * dxdphi                      # N per rad of crank (dog) angle
        rec = {'P_tank_MPa': P, 'frac': frac, 'F_N': round(F, 2), 'lift_mm': round(x * 1e3, 4), 'phi_deg': round(math.degrees(phi), 3),
               'dF_dx_N_per_mm': round(dFdx * 1e-3, 2), 'dx_dphi_mm_per_rad': round(dxdphi * 1e3, 4), 'by_law': {}}
        for law in ('L0', 'L1', 'L2'):
            tbo = tables(c['tol_open'], P, law, c['mech_kw'], mech=mo if spring_override else None, key=ko)
            tbc = tables(c['tol_close'], P, law, c['mech_kw'], mech=mc if spring_override else None, key=kc)
            To = float(np.interp(phi, tbo.ph, tbo.To))
            Tc = float(np.interp(phi, tbc.ph, tbc.Tc))
            ro = gain * sv.wnl * max(0.0, 1.0 - To / sv.Ts)
            rc = gain * sv.wnl * min(1.0, max(0.0, 1.0 + Tc / sv.Ts))
            rca = gain * sv.wnl * max(0.0, 1.0 + Tc / sv.Ts)
            rec['by_law'][law] = {'T_open_Nm': round(To, 4), 'T_assist_close_Nm': round(Tc, 4), 'R_open_N_per_s': round(ro, 1),
                                  'R_close_N_per_s': round(rc, 1), 'R_close_assist_credited_N_per_s': round(rca, 1)}
        rec['R_open_N_per_s'] = min(v['R_open_N_per_s'] for v in rec['by_law'].values())
        rec['R_close_N_per_s'] = min(v['R_close_N_per_s'] for v in rec['by_law'].values())
        rec['worst_law_open'] = min(rec['by_law'], key=lambda l: rec['by_law'][l]['R_open_N_per_s'])
        rec['worst_law_close'] = min(rec['by_law'], key=lambda l: rec['by_law'][l]['R_close_N_per_s'])
        rec['R_noload_bound_N_per_s'] = round(gain * sv.wnl, 1)
        return rec

    servo = {}
    grid = {}
    for case, c in CASES.items():
        sv, info = servo_info(c['V'])
        servo[case] = (sv, info)
        grid[case] = [[rates(case, P, f, sv) for f in FRACS] for P in P_LIST]
        print(f'grid {case}: done', flush=True)

    # ------------------------------------------------------------------ cross-check vs the Mechanical 45-row table (+10 % spring opening torque)
    dev = []
    for r in rows45:
        P = r['P_tank_MPa']
        m = pd3.Mech(+tol)
        phi = m.phi_of(r['lift_mm'] * 1e-3)
        for law in ('L0', 'L1', 'L2'):
            tb = tables(+tol, P, law, {})
            dev.append(abs(float(np.interp(phi, tb.ph, tb.To)) - r[f'Topen_{law}_Nm']))
    xcheck = {'rows': len(rows45), 'max_abs_dev_T_open_Nm': round(max(dev), 4), 'tolerance_Nm': 0.005,
              'pass': bool(max(dev) <= 0.005), 'what': 'pintle_dynamics_v3 Tables (+10 % spring, L0/L1/L2) vs MECH pintle_crank_table_v1 '
                                                   'Topen columns at the 45 hot-fire rows'}
    # eng03 Part A reproduced at the 9 map levels (same formula)?
    e3a = {(q['P_tank_MPa'], q['frac']): q for q in E3['A_quasi_static']}
    d3 = []
    for i, P in enumerate(P_LIST):
        for j, f in enumerate(FRACS):
            q = e3a.get((P, f))
            if q:
                d3.append(abs(grid['corner'][i][j]['R_open_N_per_s'] - q['open_worst_plug_rail_min_N_per_s']) / q['open_worst_plug_rail_min_N_per_s'])
    xcheck['eng03_partA_open_corner_max_rel_dev'] = round(max(d3), 4) if d3 else None
    xcheck['eng03_partA_points'] = len(d3)
    print('cross-check', xcheck, flush=True)

    # ------------------------------------------------------------------ validation: reduced models vs nonlinear drive simulation
    def reduced_sim(t, Fc_lat, F0, Fgrid, Rog, Rcg, tau_p, tau_v):
        """Rate-limited position loop: v_cmd = clip((F_cmd(t - T_lat) - F) / tau_p, -R_close(F), +R_open(F));
        tau_v dv/dt = v_cmd - v (tau_v = 0: v = v_cmd, the first-order model); dF/dt = v. Explicit Euler at the sim step."""
        dt = t[1] - t[0]
        out = np.empty(len(t))
        F, v = F0, 0.0
        a_ = dt / tau_v if tau_v > 0 else 1.0
        for i in range(len(t)):
            vc = (Fc_lat[i] - F) / tau_p
            if vc > 0:
                r = float(np.interp(F, Fgrid, Rog))
                vc = vc if vc < r else r
            else:
                r = float(np.interp(F, Fgrid, Rcg))
                vc = vc if vc > -r else -r
            v += (vc - v) * a_
            F += v * dt
            out[i] = F
        return out

    def times(t, g, levels=(0.1, 0.5, 0.9)):
        res = []
        for lev in levels:
            idx = np.where(g >= lev)[0]
            res.append(float(t[idx[0]]) if len(idx) else float('nan'))
        return res

    # 1) nonlinear simulations (pintle_dynamics_v3), stored once
    sims = []
    vp = VAL_P[:1] if a.quick else VAL_P
    for case in ('corner', 'nominal'):
        c = CASES[case]
        sv, info = servo[case]
        for P in vp:
            iP = P_LIST.index(P)
            tm = maps[P]
            Fg = np.array([q['F_N'] for q in grid[case][iP]])
            for kind, f0, f1 in VAL_PROFILES:
                opening = f1 > f0
                x0, x1 = float(tm.lift(f0)), float(tm.lift(f1))
                F0, F1 = float(tm.F_vec(x0)), float(tm.F_vec(x1))
                if kind == 'step':
                    tmax = pd3.T_PRE + 0.35

                    def cmdx(tt, x0=x0, x1=x1):
                        return np.where(tt < pd3.T_PRE, x0, x1)

                    def cmdF(tt, F0=F0, F1=F1):
                        return np.where(tt < pd3.T_PRE, F0, F1)
                else:
                    T_r = abs(F1 - F0) / RAMP_REQ
                    tmax = pd3.T_PRE + T_r + 0.25
                    Fs, hs = np.asarray(tm.F), np.asarray(tm.h)

                    def cmdF(tt, F0=F0, F1=F1):
                        Fc = F0 + math.copysign(RAMP_REQ, F1 - F0) * np.maximum(0.0, tt - pd3.T_PRE)
                        return np.minimum(Fc, F1) if F1 > F0 else np.maximum(Fc, F1)

                    def cmdx(tt, cmdF=cmdF, Fs=Fs, hs=hs):
                        return np.interp(cmdF(tt), Fs, hs)
                for law in ('L0', 'L1', 'L2'):
                    tb = tables(c['tol_open'] if opening else c['tol_close'], P, law, c['mech_kw'])
                    t, X, PH, TM, amin, xcmd = pd3.run_profile(tb, sv, tb.m.phi_of(x0), cmdx, tmax)
                    Fp = tm.F_vec(X)
                    sel = t >= pd3.T_PRE
                    k0 = int(np.argmax(sel))
                    tail = t >= t[-1] - 0.05
                    pa, pb = float(Fp[k0]), float(np.mean(Fp[tail]))
                    gp = (Fp[sel] - pa) / (pb - pa)
                    ts = t[sel] - pd3.T_PRE
                    rq = grid[case][iP]
                    sims.append({'case': case, 'P': P, 'kind': kind, 'f0': f0, 'f1': f1, 'law': law, 'F0': F0, 'F1': F1, 't': t,
                                 'Fc_lat': cmdF(np.maximum(0.0, t - pd3.LAT)), 'Fg': Fg, 'sel': sel, 'k0': k0, 'tail': tail, 'gp': gp,
                                 'ts': ts, 'tp': times(ts, gp), 'pa': pa, 'pb': pb, 'opening': opening,
                                 'Rog': np.array([q['by_law'][law]['R_open_N_per_s'] for q in rq]),
                                 'Rcg': np.array([q['by_law'][law]['R_close_N_per_s'] for q in rq]),
                                 'Rca': np.array([q['by_law'][law]['R_close_assist_credited_N_per_s'] for q in rq])})
            print(f'validation sims {case} {P} MPa: done', flush=True)

    def compare(sm, tau_p, tau_v, assist):
        Fr = reduced_sim(sm['t'], sm['Fc_lat'], sm['F0'], sm['Fg'], sm['Rog'], sm['Rca'] if assist else sm['Rcg'], tau_p, tau_v)
        ra, rb = float(Fr[sm['k0']]), float(np.mean(Fr[sm['tail']]))
        gr = (Fr[sm['sel']] - ra) / (rb - ra)
        tr = times(sm['ts'], gr)
        rec = {'t10_t50_t90_ms_reduced': [round(v * 1e3, 1) for v in tr], 'dt90_ms': round((tr[2] - sm['tp'][2]) * 1e3, 1),
               'dt10_ms': round((tr[0] - sm['tp'][0]) * 1e3, 1),
               'max_shape_err_N': round(float(np.max(np.abs(sm['gp'] - gr))) * abs(sm['F1'] - sm['F0']), 1)}
        if sm['kind'] == 'ramp':
            rec['slope_10_90_N_per_s_reduced'] = round(0.8 * abs(rb - ra) / (tr[2] - tr[0]), 0) if tr[2] > tr[0] else None
        return rec

    def score(recs):
        ok = [r for r in recs if r['dt90_ms'] == r['dt90_ms']]
        return {'n': len(recs), 'n_nan': len(recs) - len(ok), 'max_shape_err_N': max(r['max_shape_err_N'] for r in recs),
                'max_abs_dt90_ms': max((abs(r['dt90_ms']) for r in ok), default=None),
                'max_abs_dt10_ms': max((abs(r['dt10_ms']) for r in ok if r['dt10_ms'] == r['dt10_ms']), default=None)}

    # 2) model A: first order (tau_p = tau_eq of the servo loop, no velocity state), closing conservative and assist credited
    # 3) model B: two-state, (tau_p, tau_v) FIT on the 3.5 MPa runs (min of the max shape error, assist credited), checked on 4.5 / 5.5 MPa
    TAU_P_GRID = (0.004, 0.006, 0.0085, 0.010)                 # [DESIGN] fit grid
    TAU_V_GRID = (0.002, 0.004, 0.006, 0.008, 0.010)           # [DESIGN] fit grid
    fit_set = [sm for sm in sims if sm['P'] == vp[0]]
    best = None
    for tp_ in TAU_P_GRID:
        for tv_ in TAU_V_GRID:
            sc = score([compare(sm, tp_, tv_, True) for sm in fit_set])
            key = (sc['max_shape_err_N'], sc['max_abs_dt90_ms'] or 0.0)
            if best is None or key < best[0]:
                best = (key, tp_, tv_, sc)
    TAU_P_B, TAU_V_B = best[1], best[2]
    print(f'model B fit: tau_p {TAU_P_B * 1e3:.1f} ms, tau_v {TAU_V_B * 1e3:.1f} ms, fit-set score {best[3]}', flush=True)
    val = []
    for sm in sims:
        tau_eq = servo[sm['case']][1]['tau_eq_s']
        rec = {'case': sm['case'], 'P_tank_MPa': sm['P'], 'profile': sm['kind'], 'from': sm['f0'], 'to': sm['f1'], 'law': sm['law'],
               'dF_N': round(sm['F1'] - sm['F0'], 1), 't10_t50_t90_ms_sim': [round(v * 1e3, 1) for v in sm['tp']],
               'sim_static_offset_end_N': round(sm['pb'] - sm['F1'], 2),
               'A_first_order': compare(sm, tau_eq, 0.0, False),
               'B_two_state_assist_credited': compare(sm, TAU_P_B, TAU_V_B, True)}
        if not sm['opening']:
            rec['A_first_order_assist_credited'] = compare(sm, tau_eq, 0.0, True)
            rec['B_two_state_conservative_close'] = compare(sm, TAU_P_B, TAU_V_B, False)
        if sm['kind'] == 'ramp':
            rec['slope_10_90_N_per_s_sim'] = round(0.8 * abs(sm['pb'] - sm['pa']) / (sm['tp'][2] - sm['tp'][0]), 0)
        val.append(rec)

    def vsum(model, sel):
        v = [r[model] for r in val if model in r and sel(r)]
        return score(v) if v else None
    groups = {'large_steps': lambda r: r['profile'] == 'step' and abs(r['dF_N']) > 100,
              'small_steps': lambda r: r['profile'] == 'step' and abs(r['dF_N']) <= 100,
              'ramps_2500': lambda r: r['profile'] == 'ramp',
              'holdout_P_not_fit': lambda r: r['P_tank_MPa'] != vp[0]}
    vsummary = {m: {g: vsum(m, f) for g, f in groups.items()} for m in ('A_first_order', 'A_first_order_assist_credited',
                                                                     'B_two_state_assist_credited', 'B_two_state_conservative_close')}

    # ------------------------------------------------------------------ spring follow-up
    mlo = pd3.Mech(-tol)
    phis = np.linspace(mlo.phic, mlo.phistop, 400)
    crit = pd3.M['criteria']['C1']
    mt = re.search(r'targets\s+([0-9.]+)\s+at MEOP,\s+([0-9.]+)\s+at 5\.5 MPa', crit)
    if not mt:
        raise SystemExit('MECH C1 criterion text: targets not found')
    tgt = {k: (float(mt.group(1)) if k == 'MEOP' else (float(mt.group(2)) if k == 'P5.5MPa' else 0.0)) for k in pd3.C1_P}
    # G = spring_m10 - assist: the closing demand the spring must cover at each angle (the assist is linear in the spring torque)
    G_c1 = {}
    for k, Pp in pd3.C1_P.items():
        G_c1[k] = np.array([mlo.spring(p) - mlo.torque(p, pd3.F_L0(mlo.lift(p), Pp), False)[0] for p in phis])
    # unpowered closing along the hot-fire line (assist >= 0, -10 % spring, every law, lifts inside each P_tank's 12.5-100 % range)
    lifts = mlo.lift_vec(phis)
    spring_m10 = np.array([mlo.spring(p) for p in phis])
    hot_G = []                                                  # (mask, demand G) per P_tank and law
    req_hot = np.full(len(phis), -1e9)
    for P in P_LIST:
        tm = maps[P]
        mask = (lifts >= float(tm.lift(FRACS[0]))) & (lifts <= float(tm.lift(1.0)))
        for law in ('L0', 'L1', 'L2'):
            tb = tables(-tol, P, law, {})
            G = spring_m10 - np.interp(phis, tb.ph, tb.Tc)
            hot_G.append((mask, G))
            req_hot = np.where(mask, np.maximum(req_hot, G), req_hot)

    def floor_profile(targets):
        """Nominal-spring torque profile that just meets the C1 targets (-10 % spring, L0) and the hot-line assist >= 0."""
        req = np.maximum(np.max([G_c1[k] + targets[k] for k in G_c1], axis=0), req_hot)
        return np.maximum(req / (1.0 - tol), 0.0), req          # a spring cannot push open

    zero = {k: 0.0 for k in tgt}
    floor_nom, req_m10 = floor_profile(tgt)
    floor0_nom, req0_m10 = floor_profile(zero)
    m0 = pd3.Mech(0.0)
    base_nom = np.array([m0.spring(p) for p in phis])
    T0 = m0.T0

    class ProfileMech(pd3.Mech):
        def __init__(s, tol_, pp, pT):
            super().__init__(tol_)
            s.pp, s.pT = pp, pT

        def spring(s, p):
            return (1.0 + s.tol) * float(np.interp(p, s.pp, s.pT))

    def pm(tol_, prof):
        return ProfileMech(tol_, phis, prof)

    # variant -> (open mech, close mech, key) for the corner and for the nominal
    variants = {
        'baseline (T0 0.25 N m, k 0.12 N m/rad)': (None, None),
        'constant torque k = 0 (T0 kept)': ((pd3.Mech(+tol, k=0.0), pd3.Mech(-tol, k=0.0), 'k0'), (pd3.Mech(0.0, k=0.0), pd3.Mech(0.0, k=0.0), 'k0n')),
        'floor profile, MECH C1 targets (bound)': ((pm(+tol, floor_nom), pm(-tol, floor_nom), 'fl'), (pm(0.0, floor_nom), pm(0.0, floor_nom), 'fln')),
        'floor profile, zero margin (hard constraint only, bound)': ((pm(+tol, floor0_nom), pm(-tol, floor0_nom), 'f0'),
                                                                    (pm(0.0, floor0_nom), pm(0.0, floor0_nom), 'f0n'))}
    spring_res = {}
    sv_c = servo['corner'][0]
    sv_n = servo['nominal'][0]
    i35, i55 = P_LIST.index(3.5), P_LIST.index(5.5)
    for vlab, (ovc, ovn) in variants.items():
        mlo_v = ovc[1] if ovc else mlo
        c1 = {k: round(float(min(mlo_v.torque(p, pd3.F_L0(mlo_v.lift(p), Pp), False)[0] for p in phis)), 4) for k, Pp in pd3.C1_P.items()}
        sp_v = np.array([mlo_v.spring(p) for p in phis])
        hot_min = float(min(np.min((sp_v - G)[mask]) for mask, G in hot_G if np.any(mask)))
        hard_ok = all(c1[k] >= -1e-4 for k in c1) and hot_min >= -1e-4
        tgt_ok = hard_ok and all(c1[k] >= tgt[k] - 1e-4 for k in c1)
        rc = [[rates('corner', P, f, sv_c, spring_override=ovc) for f in FRACS] for P in P_LIST] if ovc else grid['corner']
        rn = [[rates('nominal', P, f, sv_n, spring_override=ovn) for f in FRACS] for P in P_LIST] if ovn else grid['nominal']
        phi_hf = math.radians(rc[i35][-1]['phi_deg'])
        spring_res[vlab] = {
            'C1_assist_min_m10_Nm': c1, 'C1_targets_Nm': tgt, 'hot_line_unpowered_assist_min_m10_Nm': round(hot_min, 4),
            'hard_constraint_met': bool(hard_ok), 'mech_targets_met': bool(tgt_ok),
            'spring_nom_at_full_thrust_3p5MPa_Nm': round(float(ovn[0].spring(phi_hf) if ovn else m0.spring(phi_hf)), 4),
            'spring_nom_at_closed_Nm': round(float(ovn[0].spring(m0.phic) if ovn else m0.spring(m0.phic)), 4),
            'corner_open_min_N_per_s': min(q['R_open_N_per_s'] for row in rc for q in row),
            'corner_open_3p5MPa_500N_N_per_s': rc[i35][-1]['R_open_N_per_s'],
            'corner_open_5p5MPa_500N_N_per_s': rc[i55][-1]['R_open_N_per_s'],
            'corner_states_open_ge_2500': f"{sum(q['R_open_N_per_s'] >= RAMP_REQ for row in rc for q in row)}/{len(P_LIST) * len(FRACS)}",
            'nominal_open_min_N_per_s': min(q['R_open_N_per_s'] for row in rn for q in row),
            'nominal_states_open_ge_2500': f"{sum(q['R_open_N_per_s'] >= RAMP_REQ for row in rn for q in row)}/{len(P_LIST) * len(FRACS)}",
            'noload_bound_3p5MPa_500N_N_per_s': rc[i35][-1]['R_noload_bound_N_per_s']}
        print('spring', vlab, spring_res[vlab], flush=True)
    i_hf = int(np.argmin(np.abs(phis - math.radians(grid['corner'][i35][-1]['phi_deg']))))
    spring_prof = {'phi_deg': [round(math.degrees(p), 2) for p in phis[::20]],
                   'baseline_nominal_Nm': [round(float(v), 4) for v in base_nom[::20]],
                   'required_m10_with_targets_Nm': [round(float(v), 4) for v in req_m10[::20]],
                   'floor_nominal_with_targets_Nm': [round(float(v), 4) for v in floor_nom[::20]],
                   'floor_nominal_zero_margin_Nm': [round(float(v), 4) for v in floor0_nom[::20]],
                   'seat_preload_T0_nominal_Nm': T0,
                   'floor_at_closed_angle_nominal_Nm': round(float(floor_nom[0]), 4),
                   'max_floor_minus_baseline_Nm': round(float(np.max(floor_nom - base_nom)), 4),
                   'binding_constraint_at_3p5MPa_full_thrust': ('hot line' if req_hot[i_hf] >= max(G_c1[k][i_hf] + tgt[k] for k in G_c1)
                                                                else 'C1 ' + max(G_c1, key=lambda k: G_c1[k][i_hf] + tgt[k])),
                   'at_3p5MPa_full_thrust': {'phi_deg': round(math.degrees(phis[i_hf]), 2), 'baseline_nominal_Nm': round(float(base_nom[i_hf]), 4),
                                             'floor_nominal_with_targets_Nm': round(float(floor_nom[i_hf]), 4),
                                             'floor_nominal_zero_margin_Nm': round(float(floor0_nom[i_hf]), 4)}}

    # ------------------------------------------------------------------ B-PNT-1 torque-speed test points (3.5 / 5.5 MPa load)
    bpnt = []
    for P in (3.5, 5.5):
        iP = P_LIST.index(P)
        for q in grid['corner'][iP]:
            if q['frac'] in (0.25, 0.5, 0.75, 1.0):
                wl = q['worst_law_open']
                To = q['by_law'][wl]['T_open_Nm']
                for case in ('corner', 'nominal'):
                    sv, info = servo[case]
                    bpnt.append({'P_tank_MPa': P, 'frac': q['frac'], 'F_N': q['F_N'], 'law': wl, 'case': case, 'V_plug': info['V_plug'],
                                 'load_torque_Nm': round(To, 3) if case == 'corner' else
                                 grid['nominal'][iP][FRACS.index(q['frac'])]['by_law'][wl]['T_open_Nm'],
                                 'model_speed_rad_s': round(sv.wnl * max(0.0, 1.0 - (To if case == 'corner' else
                                                            grid['nominal'][iP][FRACS.index(q['frac'])]['by_law'][wl]['T_open_Nm']) / sv.Ts), 3)})

    # ------------------------------------------------------------------ dynamic evidence pointer (eng03 Part B)
    dyn = {}
    for b in E3['B_ramps']:
        key = f"{'corner' if b['case'].startswith('spring +10') else 'nominal'} {b['P_tank_MPa']} MPa {b['dir']}"
        cur = dyn.get(key)
        if cur is None or b['slope_10_90_N_per_s'] < cur['min_slope_N_per_s']:
            dyn[key] = {'min_slope_N_per_s': b['slope_10_90_N_per_s'], 'ramp': f"{b['from']}->{b['to']}", 'law': b['worst_law'],
                        'lag_growth_ms': b['lag_growth_ms'], 'followed': b['follows_2500']}

    # ------------------------------------------------------------------ assemble
    def mat(case, key):
        return [[q[key] for q in row] for row in grid[case]]

    rate_map = {}
    for case in CASES:
        rate_map[case] = {'label': CASES[case]['label'], 'role': CASES[case]['role'], 'V_plug': round(CASES[case]['V'], 4),
                          'spring_tol_open': CASES[case]['tol_open'], 'spring_tol_close': CASES[case]['tol_close'],
                          'friction_override': CASES[case]['mech_kw'] or None,
                          'F_N': mat(case, 'F_N'), 'lift_mm': mat(case, 'lift_mm'),
                          'R_open_N_per_s': mat(case, 'R_open_N_per_s'), 'R_close_N_per_s': mat(case, 'R_close_N_per_s'),
                          'R_noload_bound_N_per_s': mat(case, 'R_noload_bound_N_per_s'),
                          'worst_law_open': mat(case, 'worst_law_open'), 'worst_law_close': mat(case, 'worst_law_close'),
                          'by_law': {law: {k: [[q['by_law'][law][k] for q in row] for row in grid[case]]
                                           for k in ('R_open_N_per_s', 'R_close_N_per_s', 'R_close_assist_credited_N_per_s', 'T_open_Nm',
                                                     'T_assist_close_Nm')} for law in ('L0', 'L1', 'L2')}}

    def csum(case):
        g = [q for row in grid[case] for q in row]
        wo = min(g, key=lambda q: q['R_open_N_per_s']); wc = min(g, key=lambda q: q['R_close_N_per_s'])
        return {'open_min_N_per_s': wo['R_open_N_per_s'], 'open_min_at': {k: wo[k] for k in ('P_tank_MPa', 'frac', 'F_N', 'lift_mm')},
                'close_min_N_per_s': wc['R_close_N_per_s'], 'close_min_at': {k: wc[k] for k in ('P_tank_MPa', 'frac', 'F_N', 'lift_mm')},
                'states_open_ge_2500': f"{sum(q['R_open_N_per_s'] >= RAMP_REQ for q in g)}/{len(g)}",
                'states_close_ge_2500': f"{sum(q['R_close_N_per_s'] >= RAMP_REQ for q in g)}/{len(g)}",
                'open_ge_2500_below_frac_by_P': {str(P): max((q['frac'] for q in row if all(r['R_open_N_per_s'] >= RAMP_REQ for r in row
                                                                                             if r['frac'] <= q['frac'])), default=None)
                                                 for P, row in zip(P_LIST, grid[case])},
                'closing_load_resisting_states': sum(1 for q in g for l in q['by_law'].values() if l['T_assist_close_Nm'] < 0)}
    summary = {case: csum(case) for case in CASES}
    out = {'id': 'pintle_rate_map', 'version': 'v1', 'date': '2026-10-13', 'owner': 'Electronics', 'script': 'calc/pintle_rate_map_v1.py',
           'status': 'DERIVED analysis on SIM (Combustion map) / DERIVED (needle force, rail) / MECH (crank, spring, friction) / DATASHEET '
                     '(HV69, retailer copies, TO-CONFIRM) / ASSUMED (servo line and loop) inputs; not a measurement; B-PNT-1 measures',
           'request': 'coordinator 2026-10-13 (ENG-03 provisional decision): achievable dF/dt opening and closing vs P_tank 3.5-5.5 MPa and '
                      'thrust / lift, corner and nominal, with the servo time constant, for a state-dependent rate limit plus lag in the 6-DOF',
           'requirement_reference': {'ENG-03_ramp_N_per_s': RAMP_REQ, 'tag': 'REQ (00-requirements ENG-03 amended 2026-10-13)'},
           'grid': {'P_tank_MPa': P_LIST, 'frac': FRACS, 'F_definition': 'thrust = frac x 500 N on the Combustion throttle map at each '
                    'P_tank (lift from the map); arrays are [P_tank index][frac index]',
                    'range': 'covered 62.5-500 N per P_tank 3.5-5.5 MPa; outside: not covered (GNC: hold the edge value and flag)'},
           'units': {'rates': 'N/s (thrust rate magnitude)', 'lift': 'mm', 'torque': 'N m', 'time': 's'},
           'servo_model': {case: servo[case][1] for case in ('corner', 'nominal')},
           'reduced_model_for_gnc': {
               'A_first_order': {'equation': 'dF/dt = clip((F_cmd(t - latency_s) - F) / tau_eq_s, -R_close(P_tank, F), +R_open(P_tank, F))',
                                 'parameters': {case: {'latency_s': servo[case][1]['latency_s'], 'tau_eq_s': servo[case][1]['tau_eq_s']}
                                                for case in ('corner', 'nominal')},
                                 'tags': 'latency ASSUMED; tau_eq DERIVED (2 zeta / w_n of the ASSUMED servo loop)'},
               'B_two_state': {'equation': 'v_cmd = clip((F_cmd(t - latency_s) - F) / tau_p_s, -R_close(P_tank, F), +R_open(P_tank, F)); '
                                           'tau_v_s dv/dt = v_cmd - v; dF/dt = v',
                               'parameters': {'latency_s': pd3.LAT, 'tau_p_s': TAU_P_B, 'tau_v_s': TAU_V_B,
                                              'closing_rate_table': 'R_close_assist_credited (by_law) for fidelity; R_close for the bound'},
                               'tags': 'latency ASSUMED; tau_p, tau_v FIT to the nonlinear drive simulation (3.5 MPa runs, grid '
                                       f'tau_p {list(TAU_P_GRID)} s x tau_v {list(TAU_V_GRID)} s, minimum of the maximum shape error), checked '
                                       'on 4.5 / 5.5 MPa (holdout_P_not_fit)'},
               'recommended': 'B_two_state with the envelope tables (R_open; R_close for robustness runs, the assist-credited closing for '
                              'nominal trajectories); A_first_order is the simplest form and leads the simulation by up to the '
                              'validation dt10 at the start of large steps',
               'second_order_small_signal': {case: {'w_n_rad_s': servo[case][1]['w_n_rad_s'], 'zeta': servo[case][1]['zeta']}
                                             for case in ('corner', 'nominal')},
               'rate_tables': 'rate_map.<case>.R_open_N_per_s / R_close_N_per_s (envelope = minimum over L0/L1/L2); bilinear in '
                              '(P_tank, F); F from the [P][frac] F_N array',
               'includes': 'HV69 torque-speed line under the needle-force + spring + friction load, crank kinematics, thrust-map gain, '
                           'servo latency and loop lag (pintle_dynamics_v3 model)',
               'excludes': ['ECU Pc loop (PI) and its static-droop removal; the drive alone holds a static offset (validation '
                            'sim_static_offset_end_N) that the Pc loop integrates out',
                            'chamber filling and fuel thermal lag (Combustion)', 'FC_THRUST -> CAN -> ECU latency (RG-19 budget, Electronics, open)',
                            'start transient (IGNITION -> RUN is capped by kStartRamp_Nps in firmware) and shutdown (kPintleCloseRate_mps)'],
               'closed_loop_reference': 'SIL v2.8.2 S4 (ECU firmware + ASSUMED plant): 150 +/- 25 N sine at 1 Hz -> gain 1.024, phase -8.7 deg '
                                        '(about 24 ms equivalent delay end to end, SIL)'},
           'rate_map': rate_map, 'summary': summary,
           'validation_vs_nonlinear_drive_sim': {'summary': vsummary, 'model_B_fit': {'tau_p_s': TAU_P_B, 'tau_v_s': TAU_V_B, 'fit_set_score': best[3]},
                                                 'runs': val,
                                                 'method': 'normalized responses (pre-step value to final mean) compared at 10/50/90 %; '
                                                           'shape error = max |g_sim - g_reduced| x |dF|; per law with that law\'s rate table'},
           'cross_check': xcheck,
           'dynamic_evidence_eng03_partB': {'source': ['results/eng03_slew_check_v1.json', sha(eng03_p)], 'min_slope_by_case_P_dir': dyn},
           'spring_follow_up': {'question': 'would less spring torque at full lift change the result? hard constraint: unpowered closing at '
                                            'the MEOP-equivalent load',
                                'constraints_used': {'C1': crit + ' (MECH pintle_inline_v34_v2p4 criteria; targets parsed)',
                                                     'hot_line': 'unpowered closing assist >= 0 at -10 % spring along the hot-fire grid '
                                                                 '(L0/L1/L2, 3.5-5.5 MPa) [DESIGN, Electronics]',
                                                     'seat': 'seat preload T0 at the closed angle unchanged (seat leak specification)'},
                                'variants': spring_res, 'profile': spring_prof,
                                'note': 'the floor profile is a bound, not a spring design (a falling-rate spring is a Mechanical design '
                                        'item); the unpowered closing time grows as the assist falls (B-PNT-1 kPintleUnpoweredClose_s/3 rule)'},
           'b_pnt_1_torque_speed_points': {'points': bpnt,
                                           'rule': 'B-PNT-1 adds: HV69 output speed under a steady load torque at the listed points (3.5 and '
                                                   '5.5 MPa throttle-line opening torque, worst law, +10 % spring for the corner) at the '
                                                   'corner and nominal plug voltages; pass when the measured speed >= model_speed_rad_s; '
                                                   'otherwise this rate map is re-run with the measured line (ASSUMED linear line replaced)'},
           'limitations': ['HV69 torque-speed line from retailer copies of MKS data (stall torque, s/60 deg at no load); linear line ASSUMED; '
                           'not measured under load (B-PNT-1)',
                           'needle-force laws L0/L1/L2 bound an unknown true law; the envelope takes the worst; friction MECH baseline (ASSUMED '
                           'coefficients), sensitivity case given',
                           'the thrust map is piecewise linear in lift between 9 Combustion rows per P_tank: dF/dx and the rates step between '
                           'rows; the true curve is smooth (Combustion SIM)',
                           'the quasi-static rate omits the acceleration time (tau_m 10 ms ASSUMED) and the servo saturation entry; the '
                           'reduced model validation quantifies the combined effect against the nonlinear simulation, which itself rests on '
                           'the same ASSUMED servo model',
                           'eng03_slew_check_v1 Part A closing used the no-load speed (assist neglected); this map debits a resisting closing '
                           'load (count in summary.closing_load_resisting_states)']}
    out['inputs'] = {'pintle_dynamics_v3_py': ['calc/pintle_dynamics_v3.py', sha(os.path.join(HERE, 'pintle_dynamics_v3.py'))],
                     'mechanical_pintle_inline_v2p4': [os.path.relpath(pd3.MECH_PATH, er), sha(pd3.MECH_PATH), pd3.M.get('version')],
                     'mechanical_crank_table': [os.path.relpath(mech_tab, er), sha(mech_tab), MT.get('version')],
                     'throttle_map': [os.path.relpath(pd3.MAP_PATH, er), sha(pd3.MAP_PATH)],
                     'needle_force_csv': [os.path.relpath(pd3.NF_CSV, er), sha(pd3.NF_CSV)],
                     'combustion_json': ['interfaces/combustion.json', sha(pd3.COMB_PATH), pd3.C.get('version')],
                     'servo': ['results/pintle_mini_servo_v1.json', sha(pd3.SERVO_PATH), {'V': pd3.SV['V_rated'], 'T_kgcm': pd3.SV['T_kgcm'],
                                                                                          's60': pd3.SV['s60']}],
                     'rail': ['results/pintle_rail_v3.json', sha(pd3.RAIL_PATH), {'V_plug_corner': round(pd3.V_SLOW, 4), 'V_typ': pd3.V_TYP}],
                     'eng03': ['results/eng03_slew_check_v1.json', sha(eng03_p)]}
    body = json.dumps(out, sort_keys=True, separators=(',', ':'))
    out['payload_sha256_16'] = hashlib.sha256(body.encode()).hexdigest()[:16]
    out['payload_hash_rule'] = 'sha256/16 of json.dumps(file without payload_sha256_16 and payload_hash_rule, sort_keys, separators (",", ":"))'
    os.makedirs(RES, exist_ok=True)
    jp = os.path.join(RES, 'pintle_rate_map_v1.json')
    with open(jp, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    cp = os.path.join(RES, 'pintle_rate_map_v1.csv')
    with open(cp, 'w', encoding='utf-8', newline='') as f:
        f.write('# pintle_rate_map_v1 (Electronics 2026-10-13): achievable thrust rate [N/s] vs P_tank and thrust; DERIVED on SIM/MECH/DATASHEET/'
                'ASSUMED inputs; envelope = min over needle-force laws L0/L1/L2; see pintle_rate_map_v1.json for the lag model and tags\n')
        w = csv.writer(f)
        w.writerow(['case', 'P_tank_MPa', 'frac', 'F_N', 'lift_mm', 'R_open_N_per_s', 'R_close_N_per_s', 'worst_law_open', 'worst_law_close',
                    'R_open_L0', 'R_open_L1', 'R_open_L2', 'R_close_L0', 'R_close_L1', 'R_close_L2', 'R_noload_bound_N_per_s'])
        for case in CASES:
            for row in grid[case]:
                for q in row:
                    w.writerow([case, q['P_tank_MPa'], q['frac'], q['F_N'], q['lift_mm'], q['R_open_N_per_s'], q['R_close_N_per_s'],
                                q['worst_law_open'], q['worst_law_close']] +
                               [q['by_law'][l]['R_open_N_per_s'] for l in ('L0', 'L1', 'L2')] +
                               [q['by_law'][l]['R_close_N_per_s'] for l in ('L0', 'L1', 'L2')] + [q['R_noload_bound_N_per_s']])
    L = [f'pintle_rate_map_v1 (2026-10-13): achievable thrust rate of the HV69 pintle drive vs P_tank and thrust; json sha256/16 {sha(jp)}, '
         f'payload {out["payload_sha256_16"]}, csv {sha(cp)}']
    for case in ('corner', 'nominal'):
        si = servo[case][1]
        L.append(f"servo {case}: V_plug {si['V_plug']:.3f} V, T_stall {si['T_stall_Nm']:.3f} N m, w_nl {si['w_noload_rad_s']:.2f} rad/s, "
                 f"w_n {si['w_n_rad_s']:.0f} rad/s zeta {si['zeta']:.2f} -> tau_eq {si['tau_eq_s'] * 1e3:.1f} ms, latency {si['latency_s'] * 1e3:.0f} ms")
    for case in CASES:
        s = summary[case]
        L.append(f"{case}: opening min {s['open_min_N_per_s']:.0f} N/s at {s['open_min_at']}, states >= 2500 {s['states_open_ge_2500']}; "
                 f"closing min {s['close_min_N_per_s']:.0f} N/s at {s['close_min_at']}, states >= 2500 {s['states_close_ge_2500']}; "
                 f"resisting closing-load points {s['closing_load_resisting_states']}")
        L.append(f"    opening >= 2500 N/s up to frac (by P_tank): {s['open_ge_2500_below_frac_by_P']}")
    for case in ('corner', 'nominal'):
        L.append(f'  {case} opening rate [N/s] (rows P_tank, columns frac {FRACS[0]}, {FRACS[2]}, ..., 1.0 every 0.10):')
        for P, row in zip(P_LIST, grid[case]):
            L.append(f'    {P:.1f} MPa: ' + ' '.join(f"{q['R_open_N_per_s']:5.0f}" for q in row if q['frac'] in (0.125,) or
                                                    abs((q['frac'] * 100) % 10) < 1e-6))
        L.append(f'  {case} closing rate [N/s]:')
        for P, row in zip(P_LIST, grid[case]):
            L.append(f'    {P:.1f} MPa: ' + ' '.join(f"{q['R_close_N_per_s']:5.0f}" for q in row if q['frac'] in (0.125,) or
                                                    abs((q['frac'] * 100) % 10) < 1e-6))
    L.append(f"cross-check: {xcheck}")
    L.append(f"model B fit (3.5 MPa runs): tau_p {TAU_P_B * 1e3:.1f} ms, tau_v {TAU_V_B * 1e3:.1f} ms")
    for m_, gs in vsummary.items():
        L.append(f"validation {m_}: " + '; '.join(f"{g} n {v['n']} shape max {v['max_shape_err_N']:.1f} N |dt10| {v['max_abs_dt10_ms']} ms |dt90| "
                                                  f"{v['max_abs_dt90_ms']} ms" for g, v in gs.items() if v))
    for vlab, r in spring_res.items():
        L.append(f"spring {vlab}: hard constraint met {r['hard_constraint_met']}, MECH targets met {r['mech_targets_met']} (C1 assist {r['C1_assist_min_m10_Nm']}, hot-line min "
                 f"{r['hot_line_unpowered_assist_min_m10_Nm']}); spring nom at 3.5 MPa full thrust {r['spring_nom_at_full_thrust_3p5MPa_Nm']} N m; "
                 f"corner opening 3.5 MPa/500 N {r['corner_open_3p5MPa_500N_N_per_s']:.0f} N/s, min {r['corner_open_min_N_per_s']:.0f}, states >= 2500 "
                 f"{r['corner_states_open_ge_2500']}; nominal min {r['nominal_open_min_N_per_s']:.0f}, states >= 2500 {r['nominal_states_open_ge_2500']}; "
                 f"no-load bound {r['noload_bound_3p5MPa_500N_N_per_s']:.0f}")
    L.append('B-PNT-1 torque-speed points: ' + '; '.join(f"{b['P_tank_MPa']} MPa {b['frac']} {b['case']} {b['V_plug']} V: {b['load_torque_Nm']} N m -> "
                                                          f"{b['model_speed_rad_s']} rad/s" for b in bpnt))
    txt = '\n'.join(L)
    with open(os.path.join(RES, 'pintle_rate_map_v1.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
