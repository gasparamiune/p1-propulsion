#!/usr/bin/env python3
"""ENG-03 thrust-slew check of the HV69 pintle drive under load (Electronics, 2026-10-13, v1).

Requirement (00-requirements/REQUIREMENTS.md ENG-03, amended 2026-10-13 on REV-GNC-1 RG-05, LEAD): "Ramp >= 5 F_max/s, i.e.
>= 2500 N/s under load" (every 6-DOF result flies 5 F_max/s); t10-90 <= max(0.15 s, 0.8 dF / 1000 N/s) unchanged. B-PNT-1 measures
the opening and closing slew under the L0/L1/L2 load laws. A lower measured value needs an explicit lead decision.

Question (coordinator 2026-10-13): can the MKS HV69 on the 7.49 V pintle rail, through the toggle crank, open and close at that rate
against the L1/L2 opening and L0 closing load laws? Give the margin or the rate actually reached.

Inputs (read and hashed, nothing typed in from other teams):
  Mechanical  03-cad/calcs/pintle_crank_table_v1.json (+ .csv): 45 hot-fire throttle-line states (P_tank 3.5-5.5 MPa x 9 levels):
              lift, crank angle, dx/dphi, opening servo torque under L0/L1/L2 with the spring +10 %, closing spring surplus with the
              spring -10 % (DERIVED; guide/pin friction ASSUMED, B-PNT-1 measures)
  Combustion  throttle_map_v2.csv (combustion.json operating_points.throttle_map_csv): thrust and Pc vs lift (SIM)
  Electronics results/pintle_mini_servo_v1.json: HV69 stall torque and no-load speed vs voltage (retailer copies of MKS data,
              TO-CONFIRM); results/pintle_rail_v3.json: rail static min / typ (DERIVED); calc/pintle_dynamics_v3.py (imported, not
              changed): drive dynamics with the Combustion needle-force laws (servo PD + linear torque-speed line, tau_m 10 ms,
              2 deg band, 4 ms latency: ASSUMED); firmware config.h command slew limits (parsed)
Method:
  A  quasi-static capability per state: dF/dt_max = |dF/dx| (map, central difference) x dx/dphi (MECH) x omega, with
     omega_open = omega_nl(V) (1 - T_open / T_stall(V)) (linear torque-speed line, ASSUMED) and omega_close = omega_nl(V) (the spring
     surplus would speed the closing; neglected = conservative). V = servo plug at the rail static minimum (slow case) and rail typ.
  B  dynamic: thrust command ramps at exactly 2500 N/s (lift command = map inverse), drive simulated with pintle_dynamics_v3 under
     L0, L1 and L2 (worst reported), spring +10 % opening / -10 % closing, plug at the rail minimum; achieved slope over 10-90 % of
     the response and the growth of the lag behind the command (a drive that keeps up holds a constant lag).
  C  large steps (results/pintle_dynamics_v3.json): average slew 0.8 |dF| / t10-90 = the rate the drive reaches when the command
     is not rate-limited.
  D  firmware command limits converted to thrust rate (Pc setpoint slew, pintle command slew) along the throttle line.
Outputs: results/eng03_slew_check_v1.{json,txt}. Analysis on SIM / DERIVED / ASSUMED inputs, not a measurement; B-PNT-1 measures.
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
CFG_H = os.path.join(HERE, '..', 'firmware', 'src', 'core', 'config.h')
F_MAX = 500.0                 # [REQ] F_max (sea level)
RAMP_REQ = 5.0 * F_MAX        # [REQ ENG-03 amended 2026-10-13] 2500 N/s under load
LAG_GROWTH_MAX_S = 0.005      # [DESIGN] a 2500 N/s ramp is "followed" when the lag behind the command grows by <= 5 ms between the 10 % and
                              #   the 90 % points (a drive that keeps pace holds a constant latency + servo lag; run 1 of this script used
                              #   slope >= 97 % of 2500 N/s, which failed a 75 ms ramp on its start transient alone: 2408 N/s, 2.3 ms growth)
KGCM = 0.0980665


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


def cfg_float(name):
    m = re.search(r'constexpr\s+float\s+' + re.escape(name) + r'\s*=\s*([0-9.eE+-]+)f?\s*;', open(CFG_H, encoding='utf-8').read())
    if not m:
        raise SystemExit(f'config.h: {name} not found')
    return float(m.group(1))


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
    ap.add_argument('--quick', action='store_true')
    a = ap.parse_args()
    er = a.engine_root
    mech_json = next(p for p in (os.path.join(er, '03-cad', 'calcs', 'pintle_crank_table_v1.json'),
                                 os.path.join(er, '03-cad', 'src', 'calcs', 'pintle_crank_table_v1.json')) if os.path.exists(p))
    mech_csv = mech_json[:-5] + '.csv'
    MJ = json.load(open(mech_json, encoding='utf-8'))
    rows = MJ['hot_fire_line_rows']
    pd3 = load_pd3(er)
    V_SLOW, V_TYP = pd3.V_SLOW, pd3.V_TYP
    tol = pd3.BCFG['tol']

    def servo_line(V):
        sv = pd3.Servo(V)
        return sv.Ts, sv.wnl

    # ------------------------------------------------------------------ A: quasi-static capability along the hot-fire line
    maps = {}
    capA = []
    for r in rows:
        P = r['P_tank_MPa'] * 1e6
        if P not in maps:
            maps[P] = pd3.ThrustMap(P)
        tm = maps[P]
        x = r['lift_mm'] * 1e-3
        dl = 0.02e-3
        dFdx = float((tm.F_vec(x + dl) - tm.F_vec(max(0.0, x - dl))) / (x + dl - max(0.0, x - dl)))   # N/m
        dxdphi = r['dx_dphi_mm_per_rad'] * 1e-3
        rec = {'P_tank_MPa': r['P_tank_MPa'], 'frac': r['frac'], 'F_N': r['F_thrust_N'], 'lift_mm': r['lift_mm'], 'phi_deg': r['phi_deg'],
               'dF_dx_N_per_mm': round(dFdx * 1e-3, 1), 'dx_dphi_mm_per_rad': r['dx_dphi_mm_per_rad']}
        for vlab, V in (('plug_rail_min', V_SLOW), ('rail_typ', V_TYP)):
            Ts, wnl = servo_line(V)
            for law in ('L0', 'L1', 'L2'):
                To = r[f'Topen_{law}_Nm']
                w = wnl * max(0.0, 1.0 - To / Ts)
                rec[f'open_{law}_{vlab}_N_per_s'] = round(abs(dFdx) * dxdphi * w, 0)
            rec[f'close_{vlab}_N_per_s'] = round(abs(dFdx) * dxdphi * wnl, 0)
        rec['open_worst_plug_rail_min_N_per_s'] = min(rec[f'open_{l}_plug_rail_min_N_per_s'] for l in ('L0', 'L1', 'L2'))
        capA.append(rec)
    worstA_open = min(capA, key=lambda q: q['open_worst_plug_rail_min_N_per_s'])
    worstA_close = min(capA, key=lambda q: q['close_plug_rail_min_N_per_s'])
    passA_open = sum(1 for q in capA if q['open_worst_plug_rail_min_N_per_s'] >= RAMP_REQ)
    passA_close = sum(1 for q in capA if q['close_plug_rail_min_N_per_s'] >= RAMP_REQ)

    # ------------------------------------------------------------------ B: commanded 2500 N/s ramps, drive dynamics (pintle_dynamics_v3)
    ramps = [(0.125, 1.0), (0.25, 1.0), (0.5, 1.0), (0.125, 0.5), (1.0, 0.125), (1.0, 0.25), (0.5, 0.125)]
    Ps = sorted({r['P_tank_MPa'] for r in rows})
    if a.quick:
        Ps, ramps = Ps[:1], ramps[:2]
    cases = [('spring +10 % opening / -10 % closing, servo plug at rail min', V_SLOW, True),
             ('nominal spring, rail typ', V_TYP, False)]
    resB = []
    for clab, V, worst_spring in cases:
        sv = pd3.Servo(V)
        for Pm in Ps:
            P = Pm * 1e6
            tm = maps.get(P) or pd3.ThrustMap(P)
            for f0, f1 in ramps:
                opening = f1 > f0
                m = pd3.Mech((+tol if opening else -tol) if worst_spring else 0.0)
                F0, F1 = float(tm.F_vec(tm.lift(f0))), float(tm.F_vec(tm.lift(f1)))
                T_r = abs(F1 - F0) / RAMP_REQ
                Fs = np.asarray(tm.F); hs = np.asarray(tm.h)

                def cmdf(t, F0=F0, F1=F1, Fs=Fs, hs=hs):
                    Fc = F0 + math.copysign(RAMP_REQ, F1 - F0) * np.maximum(0.0, t - pd3.T_PRE)
                    Fc = np.minimum(Fc, F1) if F1 > F0 else np.maximum(Fc, F1)
                    return np.interp(Fc, Fs, hs)
                per = {}
                for law in ('L0', 'L1', 'L2'):
                    tb = pd3.Tables(m, pd3.HotForce(P, law))
                    t, X, PH, TM, amin, xcmd = pd3.run_profile(tb, sv, tb.m.phi_of(tm.lift(f0)), cmdf, pd3.T_PRE + T_r + 0.25)
                    F = tm.F_vec(X)
                    Fc = tm.F_vec(xcmd)
                    g = (F - F0) / (F1 - F0)
                    gc = (Fc - F0) / (F1 - F0)
                    sel = t >= pd3.T_PRE

                    def first(arr, lev):
                        idx = np.where(sel & (arr >= lev))[0]
                        return float(t[idx[0]]) if len(idx) else float('nan')
                    t10, t50, t90 = first(g, 0.1), first(g, 0.5), first(g, 0.9)
                    c10, c50, c90 = first(gc, 0.1), first(gc, 0.5), first(gc, 0.9)
                    slope = 0.8 * abs(F1 - F0) / (t90 - t10) if t90 > t10 else float('nan')
                    per[law] = {'slope_10_90_N_per_s': round(slope, 0), 'lag_10_ms': round((t10 - c10) * 1e3, 1),
                                'lag_50_ms': round((t50 - c50) * 1e3, 1), 'lag_90_ms': round((t90 - c90) * 1e3, 1),
                                'lag_growth_ms': round((t90 - c90 - (t10 - c10)) * 1e3, 1),
                                'peak_motor_torque_Nm': round(float(np.max(np.abs(TM[sel]))), 3)}
                wl = max(per, key=lambda l: per[l]['lag_growth_ms'] if per[l]['lag_growth_ms'] == per[l]['lag_growth_ms'] else 1e9)
                w = per[wl]
                resB.append({'case': clab, 'V': round(V, 4), 'P_tank_MPa': Pm, 'from': f0, 'to': f1, 'dir': 'open' if opening else 'close',
                             'F0_N': round(F0, 1), 'F1_N': round(F1, 1), 'ramp_s': round(T_r, 4), 'worst_law': wl, 'by_law': per,
                             'slope_10_90_N_per_s': w['slope_10_90_N_per_s'], 'lag_growth_ms': w['lag_growth_ms'],
                             'follows_2500': bool(w['lag_growth_ms'] <= LAG_GROWTH_MAX_S * 1e3)})
                print(f"B {clab[:28]:28s} {Pm:.1f} MPa {f0:5.3f}->{f1:5.3f} worst {wl}: slope {w['slope_10_90_N_per_s']:6.0f} N/s, lag growth "
                      f"{w['lag_growth_ms']:6.1f} ms", flush=True)

    # ------------------------------------------------------------------ C: large steps from pintle_dynamics_v3 (rate reached, unlimited command)
    v3p = os.path.join(RES, 'pintle_dynamics_v3.json')
    V3 = json.load(open(v3p, encoding='utf-8'))
    resC = []
    for cs in V3['steps']:
        for s in cs['steps']:
            for law, t1090 in s['t10_90_by_law_s'].items():
                if t1090 and t1090 == t1090 and abs(s['dF_cmd_N']) >= 100.0:
                    resC.append({'case': cs['case'], 'P_tank_MPa': s['P_tank_MPa'], 'from': s['from'], 'to': s['to'], 'dir': s['dir'], 'law': law,
                                 'dF_N': s['dF_cmd_N'], 't10_90_s': t1090, 'slew_avg_N_per_s': round(0.8 * abs(s['dF_cmd_N']) / t1090, 0)})
    keyC = [c for c in resC if c['case'].startswith('spring +10 %, plug at rail min') or c['case'].startswith('spring -10 %, plug at rail min')]
    worstC_open = min((c for c in keyC if c['dir'] == 'open'), key=lambda c: c['slew_avg_N_per_s'])
    worstC_close = min((c for c in keyC if c['dir'] == 'close'), key=lambda c: c['slew_avg_N_per_s'])

    # ------------------------------------------------------------------ D: firmware command limits as thrust rate along the map
    sp_rate = cfg_float('kPcSpRateLimit_Paps')
    x_rate = cfg_float('kPintleRateCmd_mps')
    resD = []
    mp = pd3.MAP_PATH
    mrows = [r for r in csv.DictReader(l for l in open(mp) if not l.startswith('#'))
             if r['lift_m'] not in ('', None) and abs(float(r['D_port_m']) - 0.025) < 1e-6]
    for Pm in Ps:
        rr = sorted((float(r['lift_m']), float(r['F_N']), float(r['Pc_Pa'])) for r in mrows if abs(float(r['P_tank_Pa']) - Pm * 1e6) < 1.0)
        for k in range(len(rr) - 1):
            (x0, F0, p0), (x1, F1, p1) = rr[k], rr[k + 1]
            resD.append({'P_tank_MPa': Pm, 'F_N': [round(F0, 1), round(F1, 1)],
                         'pc_slew_limit_as_N_per_s': round(sp_rate * (F1 - F0) / (p1 - p0), 0),
                         'lift_slew_limit_as_N_per_s': round(x_rate * (F1 - F0) / (x1 - x0), 0)})
    minD_pc = min(d['pc_slew_limit_as_N_per_s'] for d in resD)
    minD_x = min(d['lift_slew_limit_as_N_per_s'] for d in resD)

    # ------------------------------------------------------------------ verdict
    B_bad = [b for b in resB if not b['follows_2500']]
    B_slow = [b for b in resB if b['case'].startswith('spring +10')]
    verdict = {
        'A_quasi_static': {'open_states_meeting_2500': f'{passA_open}/{len(capA)}', 'close_states_meeting_2500': f'{passA_close}/{len(capA)}',
                           'open_min_N_per_s': worstA_open['open_worst_plug_rail_min_N_per_s'],
                           'open_min_at': {k: worstA_open[k] for k in ('P_tank_MPa', 'frac', 'F_N', 'lift_mm')},
                           'close_min_N_per_s': worstA_close['close_plug_rail_min_N_per_s'],
                           'close_min_at': {k: worstA_close[k] for k in ('P_tank_MPa', 'frac', 'F_N', 'lift_mm')}},
        'B_ramps_2500': {'followed': f'{len(resB) - len(B_bad)}/{len(resB)}',
                         'slow_case_min_slope_open_N_per_s': min((b['slope_10_90_N_per_s'] for b in B_slow if b['dir'] == 'open'), default=float('nan')),
                         'slow_case_min_slope_close_N_per_s': min((b['slope_10_90_N_per_s'] for b in B_slow if b['dir'] == 'close'), default=float('nan')),
                         'not_followed': [f"{b['case'][:24]} {b['P_tank_MPa']} MPa {b['from']}->{b['to']} {b['worst_law']}: {b['slope_10_90_N_per_s']:.0f} N/s"
                                          for b in B_bad]},
        'C_steps_rate_reached': {'open_min': worstC_open, 'close_min': worstC_close},
        'D_firmware_limits': {'pc_setpoint_slew_min_N_per_s': minD_pc, 'pintle_command_slew_min_N_per_s': minD_x,
                              'note': 'both above 2500 N/s: the firmware does not cap the ramp (the start ramp kStartRamp_Nps 2500 N/s is the '
                                      'COMB start cap, active only from RUN entry until the command is first met)'},
    }
    out = {'id': 'eng03_slew_check', 'version': 'v1', 'date': '2026-10-13', 'owner': 'Electronics', 'script': 'calc/eng03_slew_check_v1.py',
           'requirement': {'ENG-03_ramp_N_per_s': RAMP_REQ, 'source': '00-requirements/REQUIREMENTS.md ENG-03 (amended 2026-10-13, REV-GNC-1 RG-05)',
                           'follow_criterion': f'lag behind the 2500 N/s command grows <= {LAG_GROWTH_MAX_S * 1e3:.0f} ms from the 10 % to the 90 % point [DESIGN]'},
           'inputs': {'mechanical_crank_table': [os.path.relpath(mech_json, er), sha(mech_json), MJ.get('version'), MJ.get('tag')],
                      'mechanical_crank_csv': [os.path.relpath(mech_csv, er), sha(mech_csv)],
                      'throttle_map': [os.path.relpath(pd3.MAP_PATH, er), sha(pd3.MAP_PATH)],
                      'needle_force_csv': [os.path.relpath(pd3.NF_CSV, er), sha(pd3.NF_CSV)],
                      'pintle_dynamics_v3_json': ['results/pintle_dynamics_v3.json', sha(v3p)],
                      'servo': {'id': pd3.SV['id'], 'V': pd3.SV['V_rated'], 'T_kgcm': pd3.SV['T_kgcm'], 's60': pd3.SV['s60'],
                                'tag': 'retailer copies of MKS data (TO-CONFIRM)'},
                      'rail_V': {'plug_at_rail_min': round(V_SLOW, 4), 'rail_typ': V_TYP, 'source': 'results/pintle_rail_v3.json (DERIVED)'},
                      'config_h': {'kPcSpRateLimit_Paps': sp_rate, 'kPintleRateCmd_mps': x_rate, 'sha256_16': sha(CFG_H)},
                      'assumed': {'servo_line': 'linear torque-speed (stall, no-load) per voltage', 'tau_m_s': pd3.TAU_M, 'pb_deg': pd3.PB_DEG,
                                  'zeta': pd3.ZETA, 'latency_s': pd3.LAT, 'thrust': 'quasi-steady map (no chamber / fuel lag)'}},
           'A_quasi_static': capA, 'B_ramps': resB, 'C_steps': resC, 'D_firmware_limits': resD, 'verdict': verdict,
           'limitations': ['HV69 torque-speed line from retailer copies of MKS data (stall torque, s/60 deg at no load); linear line ASSUMED; '
                           'B-PNT-1 measures speed under load and the opening/closing slew under the L0/L1/L2 load laws',
                           'friction ASSUMED (Mechanical baseline); the guide mu 0.02 + S 5 N sensitivity of pintle_dynamics_v3 slows the opening',
                           'quasi-steady thrust map: the chamber filling and fuel thermal lag (Combustion) add to the thrust response, not to the '
                           'drive rate',
                           'the thrust rate in 6-DOF terms (GNC) is a command-rate limit; this check is the actuator capability under load']}
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, 'eng03_slew_check_v1.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    L = [f'eng03_slew_check_v1 (2026-10-13): ENG-03 ramp >= {RAMP_REQ:.0f} N/s under load; HV69 on the pintle rail (plug at rail min {V_SLOW:.3f} V, '
         f'typ {V_TYP:.3f} V) through the toggle crank (MECH pintle_crank_table_v1 {sha(mech_json)})',
         f'A quasi-static capability (|dF/dx| x dx/dphi x omega under load), 45 hot-fire states, plug at rail min:',
         f'  opening (worst of L0/L1/L2, spring +10 %): {passA_open}/{len(capA)} states >= 2500 N/s; minimum {worstA_open["open_worst_plug_rail_min_N_per_s"]:.0f} N/s at '
         f'{worstA_open["P_tank_MPa"]} MPa {worstA_open["frac"]} ({worstA_open["F_N"]:.0f} N, {worstA_open["lift_mm"]:.2f} mm)',
         f'  closing (no-load speed, spring assist neglected): {passA_close}/{len(capA)} states >= 2500 N/s; minimum {worstA_close["close_plug_rail_min_N_per_s"]:.0f} N/s at '
         f'{worstA_close["P_tank_MPa"]} MPa {worstA_close["frac"]} ({worstA_close["F_N"]:.0f} N, {worstA_close["lift_mm"]:.2f} mm)']
    for q in capA:
        if q['frac'] in (0.125, 0.5, 0.75, 1.0):
            L.append(f"    {q['P_tank_MPa']:.1f} MPa {q['frac']:5.3f} {q['F_N']:5.0f} N lift {q['lift_mm']:.3f} mm dF/dx {q['dF_dx_N_per_mm']:6.1f} N/mm dx/dphi "
                     f"{q['dx_dphi_mm_per_rad']:.3f}: open L0/L1/L2 {q['open_L0_plug_rail_min_N_per_s']:.0f}/{q['open_L1_plug_rail_min_N_per_s']:.0f}/"
                     f"{q['open_L2_plug_rail_min_N_per_s']:.0f} N/s, close {q['close_plug_rail_min_N_per_s']:.0f} N/s")
    L.append(f"B commanded 2500 N/s ramps (drive dynamics, worst law): followed {verdict['B_ramps_2500']['followed']}; slow case min slope open "
             f"{verdict['B_ramps_2500']['slow_case_min_slope_open_N_per_s']:.0f} N/s, close {verdict['B_ramps_2500']['slow_case_min_slope_close_N_per_s']:.0f} N/s")
    for b in resB:
        L.append(f"    {b['case'][:44]:44s} {b['P_tank_MPa']:.1f} MPa {b['from']:5.3f}->{b['to']:5.3f} ({b['F0_N']:.0f}->{b['F1_N']:.0f} N, ramp {b['ramp_s']*1e3:.0f} ms): "
                 f"worst {b['worst_law']} slope {b['slope_10_90_N_per_s']:.0f} N/s, lag growth {b['lag_growth_ms']:.1f} ms {'OK' if b['follows_2500'] else 'NOT FOLLOWED'}")
    for clab, _, _ in cases:
        for Pm in Ps:
            bb = [b for b in resB if b['case'] == clab and b['P_tank_MPa'] == Pm]
            op = [b for b in bb if b['dir'] == 'open']; cl = [b for b in bb if b['dir'] == 'close']
            L.append(f"  summary {clab[:44]:44s} {Pm:.1f} MPa: opening ramps followed {sum(b['follows_2500'] for b in op)}/{len(op)} (slope min "
                     f"{min(b['slope_10_90_N_per_s'] for b in op):.0f} N/s), closing followed {sum(b['follows_2500'] for b in cl)}/{len(cl)} (slope min "
                     f"{min(b['slope_10_90_N_per_s'] for b in cl):.0f} N/s)")
    L.append(f"C rate reached on unlimited steps (pintle_dynamics_v3, spring +/-10 %, plug at rail min, |dF| >= 100 N): opening min "
             f"{worstC_open['slew_avg_N_per_s']:.0f} N/s ({worstC_open['P_tank_MPa']} MPa {worstC_open['from']}->{worstC_open['to']} {worstC_open['law']}), closing min "
             f"{worstC_close['slew_avg_N_per_s']:.0f} N/s ({worstC_close['P_tank_MPa']} MPa {worstC_close['from']}->{worstC_close['to']} {worstC_close['law']})")
    L.append(f"D firmware command limits as thrust rate: Pc setpoint slew >= {minD_pc:.0f} N/s, pintle command slew >= {minD_x:.0f} N/s (both > 2500 N/s)")
    txt = '\n'.join(L)
    with open(os.path.join(RES, 'eng03_slew_check_v1.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
