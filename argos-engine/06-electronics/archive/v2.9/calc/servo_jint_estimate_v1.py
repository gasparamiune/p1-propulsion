#!/usr/bin/env python3
"""Output-referred rotor inertia J_int of the TVC servo, v1 (Electronics, 2026-10-12).

LEAD 2026-10-12 (GNC n 4.8 verdict): new provisional requirement ENG-07c, J_int <= 1e-3 kg m2 at the servo output
(the SIL used 2e-3 ASSUMED; at that value GNC's 6-DOF shows saturated ~7 Hz limit cycles lasting up to 3.8 s).
Task: estimate the Savox SB-2292SG J_int as motor rotor inertia x gear ratio squared, using data of a similar-class
motor, with the method stated; if above 1e-3, name a candidate that meets it.

Method (two routes, same physics)
  B (as asked)  J_int = J_rotor N^2 (+ gear-train inertia, neglected: < ~10 % for a spur train behind the motor
                pinion). Neither J_rotor nor N is published for any RC servo, so N is bounded from the output
                no-load speed and a motor speed range, J_rotor from 22 mm BLDC datasheets.
  A (preferred) for a DC/BLDC motor tau_m = J_rotor w_m,nl / T_m,stall (mechanical time constant, a motor datasheet
                value independent of the winding). With T_s,out = eta N T_m,stall and w_nl,out = w_m,nl / N:
                    J_int = J_rotor N^2 = tau_m T_s,out / (eta w_nl,out)
                i.e. the gear ratio cancels: J_int follows from the servo's PUBLISHED stall torque and no-load speed
                plus the motor tau_m and the gear efficiency.
  Engine side   J_int n^2 for the n 4.8 linkage, compared with the gimballed engine inertia (mechanical.json).
Caveats: RC servo electronics may current-limit (published stall torque below the motor's -> route A low), and the
published 60 deg time may include the acceleration (published w_nl low -> route A high). Only B-TVC-1 settles it.
Outputs: results/servo_jint_estimate_v1.{json,txt}
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts_db as pdb  # noqa: E402

OUT = os.path.join(HERE, '..', 'results')
ENGINE_ROOT = os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine')
KG = pdb.KGCM_TO_NM
J_REQ = 1.0e-3                    # [LEAD 2026-10-12 ENG-07c provisional]
N_LINK = 4.8                      # [LEAD 2026-10-12 provisional n 4.8, GNC verdict PASS]

MOTORS = [   # similar-class motors with datasheet rotor inertia and mechanical time constant (accessed 2026-10-12)
    {'id': 'maxon ECX 22 M (ECXZ22M1KN50K1ST1D538B), 22 mm BLDC', 'J_rotor_gcm2': 1.91, 'tau_m_ms': 3.02,
     'no_load_rpm': 54700, 'stall_mNm': 363.0, 'V': 48.0,
     'src': 'https://www.maxongroup.com/maxon/view/product/motor/ecmotor/ECX/ECX22/ECXZ22M1KN50K1ST1D538B', 'tag': 'DATASHEET'},
    {'id': 'Orbray BMS22-2113, 22 mm slotless BLDC', 'J_rotor_gcm2': 1.90, 'tau_m_ms': 7.9,
     'no_load_rpm': 12000, 'stall_mNm': 32.3, 'V': 24.0,
     'src': 'https://orbray.com/en/product/dccorelessmotor/brushless_ca_bms22-2113.html', 'tag': 'DATASHEET'},
]
ETA = {'v': 0.70, 'range': [0.60, 0.80], 'tag': 'ASSUMED multi-stage steel spur train (0.90-0.95 per stage, 4-5 stages)'}
TAU = {'range_ms': [3.0, 8.0], 'central_ms': 5.5, 'tag': 'DATASHEET range of the two 22 mm BLDC motors above; the '
       'SB-2292SG motor is unidentified (no teardown found) -> its tau_m may lie outside this range'}


def servo_tw(sv, V):
    T = sv['torque_kgcm']['v'][f'{V:.1f}'] * KG
    w = math.radians(60.0) / sv['speed_s_per_60deg']['v'][f'{V:.1f}']
    return T, w


def route_a(T, w, tau_ms, eta):
    return tau_ms * 1e-3 * T / (eta * w)


def main():
    out = {'id': 'servo_jint_estimate_v1', 'version': 'v1', 'date': '2026-10-12', 'owner': 'electronics',
           'requirement': {'J_int_max_kgm2': J_REQ, 'tag': 'LEAD 2026-10-12 ENG-07c (provisional)'},
           'motors': MOTORS, 'eta_gear': ETA, 'tau_m': TAU, 'servos': {}}
    mech = json.load(open(os.path.join(ENGINE_ROOT, 'interfaces', 'mechanical.json')))
    I_eng = None
    try:
        I_eng = mech['gimballed_mass_properties']['I_pivot_kgm2']['v']
    except Exception:
        pass
    out['engine_inertia_note'] = ('gimballed engine inertia about the pivot 0.047 kg m2 (LEAD B-TVC-1 dummy value; '
                                  'mechanical.json v1 0.044-0.047)')
    lines = ['servo_jint_estimate_v1 (Electronics 2026-10-12): J_int = tau_m T_s / (eta w_nl)  [route A], J_rotor N^2 [route B]',
             'requirement ENG-07c J_int <= %.1e kg m2 (LEAD provisional); linkage n %.1f -> engine-side J_int n^2' % (J_REQ, N_LINK), '']
    for key, sv in (('SB-2292SG', pdb.SB2292SG), ('SB-2290SG', pdb.SB2290SG), ('SB-2274SG', pdb.SB2274SG)):
        rec = {'model': sv['model'], 'by_voltage': {}}
        for V in (6.0, 7.4, 8.4):
            try:
                T, w = servo_tw(sv, V)
            except KeyError:
                continue
            ratio = T / w
            lo = route_a(T, w, TAU['range_ms'][0], ETA['range'][1])
            hi = route_a(T, w, TAU['range_ms'][1], ETA['range'][0])
            c = route_a(T, w, TAU['central_ms'], ETA['v'])
            tau_max = J_REQ * ETA['v'] * w / T * 1e3
            rec['by_voltage'][f'{V:.1f}'] = {'T_s_Nm': round(T, 3), 'w_nl_rad_s': round(w, 2), 'T_over_w_Nms': round(ratio, 4),
                                             'J_int_central_kgm2': round(c, 6), 'J_int_range_kgm2': [round(lo, 6), round(hi, 6)],
                                             'tau_m_max_for_req_ms (eta 0.7)': round(tau_max, 2),
                                             'engine_side_central_kgm2': round(c * N_LINK ** 2, 4)}
        out['servos'][key] = rec
        lines.append(f'{key}: ' + sv['model'])
        for V, r in rec['by_voltage'].items():
            lines.append('  %s V  Ts %.2f N m  w_nl %.2f rad/s  Ts/w %.4f N m s  J_int central %.2e  range %.2e..%.2e kg m2  '
                         'meets 1e-3 only if tau_m <= %.1f ms (eta 0.7)  engine side %.3f kg m2'
                         % (V, r['T_s_Nm'], r['w_nl_rad_s'], r['T_over_w_Nms'], r['J_int_central_kgm2'],
                            r['J_int_range_kgm2'][0], r['J_int_range_kgm2'][1], r['tau_m_max_for_req_ms (eta 0.7)'],
                            r['engine_side_central_kgm2']))
    # route B cross-check for the SB-2292SG at 7.4 V
    T, w = servo_tw(pdb.SB2292SG, 7.4)
    rpm_out = w * 60 / (2 * math.pi)
    rb = []
    for J_r in (1.0, 1.9):
        for kv_rpm_per_V in (1500.0, 2000.0, 3000.0):
            N = kv_rpm_per_V * 7.4 / rpm_out
            rb.append({'J_rotor_gcm2': J_r, 'Kv_rpm_per_V_ASSUMED': kv_rpm_per_V, 'N': round(N, 1),
                       'J_int_kgm2': round(J_r * 1e-7 * N ** 2, 6)})
    out['route_B_SB2292SG_7.4V'] = {'output_no_load_rpm': round(rpm_out, 1), 'rows': rb,
                                    'note': 'motor Kv and rotor inertia of the SB-2292SG are unpublished; ASSUMED Kv range; '
                                            'route B spans ~x15 and only brackets route A'}
    N_c = math.sqrt(route_a(T, w, TAU['central_ms'], ETA['v']) / 1.9e-7)
    out['route_B_consistency'] = {'N_implied_by_route_A_central_with_1.9gcm2': round(N_c, 1),
                                  'motor_no_load_rpm_implied': round(N_c * rpm_out, 0),
                                  'Kv_implied_rpm_per_V': round(N_c * rpm_out / 7.4, 0)}
    lines += ['', 'route B (J_rotor N^2) for SB-2292SG at 7.4 V, output no-load %.1f rpm:' % rpm_out]
    for r in rb:
        lines.append('  J_rotor %.1f g cm2, Kv %.0f rpm/V (ASSUMED) -> N %.0f -> J_int %.2e kg m2' % (
            r['J_rotor_gcm2'], r['Kv_rpm_per_V_ASSUMED'], r['N'], r['J_int_kgm2']))
    lines.append('  route A central implies N %.0f with a 1.9 g cm2 rotor (motor %.0f rpm no-load, Kv %.0f rpm/V): plausible' % (
        N_c, N_c * rpm_out, N_c * rpm_out / 7.4))
    # what meets ENG-07c by construction: a datasheet motor + planetary head with a known ratio
    Jr = MOTORS[0]['J_rotor_gcm2'] * 1e-7
    N_max = math.sqrt(J_REQ / Jr)
    out['meets_by_construction'] = {
        'concept': 'catalogue BLDC with published rotor inertia (maxon ECX 22 class, 1.91 g cm2, tau_m 3.0 ms) + planetary '
                   'gearhead + driver + the existing AS5048A loop',
        'N_max_for_req': round(N_max, 1), 'J_int_at_N_max_kgm2_excl_gearhead': J_REQ,
        'open': 'gearhead torque rating at ~2.5-3.3 N m output, low-voltage (8 V) winding torque/speed, gearhead inertia, '
                'mass/envelope, driver -> maxon catalogue + quote (TO-QUOTE maxon, ship to DK-6400); a TVC architecture '
                'change, so only if B-TVC-1 shows the SB-2292SG above 1e-3'}
    lines += ['', 'by construction: J_rotor 1.91 g cm2 (maxon ECX 22) needs N <= %.0f for J_int <= 1e-3 (gearhead inertia extra)' % N_max]
    lines += ['', 'physics note: J_int n^2 = (tau_m/eta) x (T_e/w_e) at the engine, independent of the gear and linkage ratios:',
              'for the torque-speed the TVC needs, only the motor time constant (and gear efficiency) can lower it.']
    json.dump(out, open(os.path.join(OUT, 'servo_jint_estimate_v1.json'), 'w'), indent=1)
    open(os.path.join(OUT, 'servo_jint_estimate_v1.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
