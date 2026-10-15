#!/usr/bin/env python3
"""Pintle rail OV disconnect: false-trip margin and trip filter (Electronics, 2026-10-13, v1). Lead request after the
pintle_rail_v3 decisions: "The 7.97 V load-release peak sits 90 mV under the 8.06 V minimum trip. Show the false-trip margin
with tolerance on the capacitor ESR/capacitance (and ageing at temperature), or add a short trip filter that still protects
the HV69; B-PWR-2 measures the real peak."

Model (SIM, averaged, not a switching model; every input tagged):
  - 4-switch buck-boost in average current mode: inner current loop as a proportional duty correction with bandwidth f_i
    [ASSUMED fsw/10 = 40 kHz, and 20 kHz as the slow case]; outer PI voltage loop designed at the NOMINAL output capacitance
    for crossover f_c 5 kHz [DESIGN target, <= f_RHPZ/5] with the PI zero at f_c/5 [DESIGN]; boost mode at VIN 6.0 V (the
    right-half-plane zero appears by itself in the averaged model: d' * i_L jumps when the loop lowers i_L) and buck mode at
    VIN 8.4 V.
  - output node: ceramics + polymers as one capacitance with the polymers' parallel ESR in series (conservative: the ceramics
    shunt the ESR at high frequency).
  - load release: HV69 current step I0 -> 0 (instantaneous = worst; the motor L/R makes it slower in reality).
  - tolerance stack: polymer Panasonic OS-CON 16SVPG220M [DATASHEET Farnell 4423905: 220 uF +/-20 %, ESR <= 14 mOhm at
    100-300 kHz / 20 C, endurance 5000 h at 105 C: capacitance within +/-20 % of initial, tan d <= 150 % of the initial limit];
    ESR at end of life x1.5 [DERIVED from the tan d limit] and x2 at -35 C [ASSUMED, no low-temperature curve read];
    polymer capacitance -10 % at -35 C [ASSUMED]; ceramics 4 x 22 uF X7R 16 V 1210: -10 % tolerance, DC bias at 7.6 V
    keeps 40-50 % [ASSUMED, maker curve TO-CONFIRM], -15 % temperature, -10 % ageing over 4 decades of hours [ASSUMED 2.5 %
    per decade, X7R class].
  - OV comparator: LTC4365 [DATASHEET Rev B: OV 492.5-507.5 mV over temperature, fault delay <= 2 us, gate fast turn-off
    <= 4 us]; divider 154k / 10.0k [DESIGN] with an optional capacitor at the OV pin (first-order filter, tau = R_th C_f).
  - fail-high: the regulator loses its feedback and holds the 8 A average inductor current limit [DESIGN v2 RILIM 41.2k];
    the rail ramps until the (filtered) comparator trips, then 6 us until the FET is off.
Inputs read: ../results/pintle_rail_v3.json (static upper bound, trip band). Outputs: ../results/pintle_rail_ovtrip_v1.json/.txt
"""
from __future__ import annotations

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results')

L_H = 4.7e-6
F_I = (40e3, 20e3)                  # [ASSUMED] inner current-loop bandwidth: fsw/10 nominal, fsw/20 slow
F_C = 5e3                           # [DESIGN target]
V_SET = 7.490                       # [DESIGN v3 divider B typical]
I_LIM_L = 330e3 / 41.2e3            # [DERIVED v2] ~8 A average inductor current limit
I_LOAD_SERVO_HOLD = 0.4             # [DESIGN v2] hold current during a fail-high ramp
POLY = {'C': 220e-6, 'tol': 0.20, 'eol': 0.20, 'cold': 0.10, 'esr': 0.014, 'esr_eol': 1.5, 'esr_cold': 2.0, 'n': 2}
CER = {'C': 4 * 22e-6, 'tol': 0.10, 'bias_nom': 0.50, 'bias_min': 0.40, 'temp': 0.15, 'age': 0.10}
TAUS = (0.0, 5e-6, 10e-6, 22e-6, 47e-6)
PEAKING = 1.3                       # [ASSUMED] closed-loop peaking allowance (phase margin 45 deg instead of the model's ~75 deg)
SPIKE_V = 0.030                     # [ASSUMED] ESL / switching-ripple spike not in the averaged model (sub-us to few us)
SPIKE_W_S = 2e-6                    # [ASSUMED] spike width for the filter attenuation
T_RESP = 2e-6 + 4e-6                # [DATASHEET LTC4365] fault delay + gate fast turn-off (max values)


def c_and_esr(case):
    if case == 'nominal':
        c = CER['C'] * CER['bias_nom'] + POLY['n'] * POLY['C']
        esr = POLY['esr'] / POLY['n']
    elif case == 'worst_cold_eol':
        c = CER['C'] * (1 - CER['tol']) * CER['bias_min'] * (1 - CER['temp']) * (1 - CER['age']) + \
            POLY['n'] * POLY['C'] * (1 - POLY['tol']) * (1 - POLY['eol']) * (1 - POLY['cold'])
        esr = POLY['esr'] * POLY['esr_eol'] * POLY['esr_cold'] / POLY['n']
    elif case == 'worst_hot_eol':   # hot: ESR not raised by cold, capacitance at the low tolerance and end of life
        c = CER['C'] * (1 - CER['tol']) * CER['bias_min'] * (1 - CER['temp']) * (1 - CER['age']) + \
            POLY['n'] * POLY['C'] * (1 - POLY['tol']) * (1 - POLY['eol'])
        esr = POLY['esr'] * POLY['esr_eol'] / POLY['n']
    else:
        raise ValueError(case)
    return c, esr


def simulate(mode, vin, i0, c, esr, c_design, f_i, taus, dt=0.1e-6, t_end=1.5e-3, fail_high=False, slew_s=0.0):
    """Averaged model. Returns the peak v_out and the peak of each filtered OV-sense trace (in output volts)."""
    v = V_SET
    d0 = vin / V_SET if mode == 'boost' else 1.0                       # boost: d' at steady state; buck: transfer = 1
    kp = 2 * math.pi * F_C * c_design / d0
    ki = kp * 2 * math.pi * F_C / 5
    i_l = i0 / d0 if mode == 'boost' else i0
    integ = i_l                                                         # integrator holds the steady-state reference
    vc = V_SET
    filt = [V_SET for _ in taus]
    peak = V_SET
    fpk = [V_SET for _ in taus]
    k_i = 2 * math.pi * f_i * L_H / V_SET
    n = int(t_end / dt)
    trace = []
    for k in range(n):
        t = k * dt
        i_load = i0 if t < 0 else (max(0.0, i0 * (1 - t / slew_s)) if slew_s > 0 else 0.0)
        if fail_high:
            i_load = I_LOAD_SERVO_HOLD
        v_out_est = vc   # controller senses v_out (with ESR term below)
        if mode == 'boost':
            i_ref = I_LIM_L if fail_high else min(max(integ + kp * (V_SET - v), 0.0), I_LIM_L)
            dp = min(max(vin / V_SET + k_i * (i_l - i_ref), 0.05), 1.0)  # d' = 1 - D_boost (feedforward + current loop)
            di = (vin - dp * vc) / L_H
            i_out = dp * i_l
        else:
            i_ref = I_LIM_L if fail_high else min(max(integ + kp * (V_SET - v), 0.0), I_LIM_L)
            dd = min(max(V_SET / vin - k_i * V_SET / vin * (i_l - i_ref), 0.0), 1.0)
            di = (dd * vin - vc) / L_H
            i_out = i_l
        i_c = i_out - i_load
        vc += i_c / c * dt
        i_l += di * dt
        v = vc + esr * i_c
        if not fail_high:
            integ += ki * (V_SET - v) * dt
        peak = max(peak, v)
        for j, tau in enumerate(taus):
            filt[j] = v if tau == 0 else filt[j] + (v - filt[j]) * dt / tau
            fpk[j] = max(fpk[j], filt[j])
        if fail_high:
            trace.append((t, v, list(filt)))
            if v > 12.0:
                break
    return peak, fpk, trace


def main():
    v3 = json.load(open(os.path.join(RES, 'pintle_rail_v3.json')))
    b = v3['dividers']['B_v3_proposed_24k9_4k75']
    v_static = b['static_upper_worst_V']
    trip_lo, trip_nom, trip_hi = v3['failure']['OV_disconnect']['trip_V_min_nom_max']
    c_design, _ = c_and_esr('nominal')
    rows = []
    for mode, vin in (('boost', 6.0), ('buck', 8.4)):
        for case in ('nominal', 'worst_hot_eol', 'worst_cold_eol'):
            c, esr = c_and_esr(case)
            for f_i in F_I:
                for i0 in (1.7, 4.33):
                    pk, fpk, _ = simulate(mode, vin, i0, c, esr, c_design, f_i, TAUS)
                    dv = pk - V_SET
                    rows.append({'mode': mode, 'vin': vin, 'case': case, 'C_uF': round(c * 1e6, 1), 'ESR_mOhm': round(esr * 1e3, 1),
                                 'f_i_kHz': f_i / 1e3, 'I0_A': i0, 'dV_peak_V': round(dv, 3),
                                 'peak_at_static_max_V': round(v_static + dv, 3),
                                 'filtered_dV_V': {f'{tau * 1e6:.0f}us': round(fp - V_SET, 3) for tau, fp in zip(TAUS, fpk)},
                                 'margin_to_trip_min_V': {f'{tau * 1e6:.0f}us': round(trip_lo - (v_static + fp - V_SET), 3)
                                                          for tau, fp in zip(TAUS, fpk)}})
    # fail-high: fastest ramp = lowest capacitance; trip on the filtered trace at the HIGHEST trip point, then 6 us
    fails = []
    for mode, vin in (('boost', 6.0), ('buck', 8.4)):
        for case in ('worst_hot_eol', 'nominal'):
            c, esr = c_and_esr(case)
            _, _, tr = simulate(mode, vin, 0.4, c, esr, c_design, F_I[0], TAUS, fail_high=True, t_end=3e-3)
            out = {}
            for j, tau in enumerate(TAUS):
                t_trip = next((t for t, v, f in tr if f[j] >= trip_hi), None)
                if t_trip is None:
                    out[f'{tau * 1e6:.0f}us'] = None
                    continue
                t_off = t_trip + T_RESP
                v_off = next((v for t, v, f in tr if t >= t_off), tr[-1][1])
                t_above_82 = t_off - next((t for t, v, f in tr if v >= 8.2), t_off)
                out[f'{tau * 1e6:.0f}us'] = {'t_trip_us': round(t_trip * 1e6, 1), 'V_peak_at_FET_off': round(v_off, 3),
                                             'time_above_8V2_us': round(t_above_82 * 1e6, 1)}
            t78 = next(t for t, v, f in tr if v >= 7.8)
            t82 = next(t for t, v, f in tr if v >= 8.2)
            dvdt = 0.4 / (t82 - t78)
            fails.append({'mode': mode, 'vin': vin, 'case': case, 'C_uF': round(c * 1e6, 1), 'dVdt_V_per_ms': round(dvdt / 1e3, 1),
                          'by_filter': out})
    # verdict per filter: worst nuisance margin over every row; worst fail-high peak
    verdict = {}
    for tau in TAUS:
        key = f'{tau * 1e6:.0f}us'
        m = min(r['margin_to_trip_min_V'][key] for r in rows)
        m43 = min(r['margin_to_trip_min_V'][key] for r in rows if r['I0_A'] == 4.33)
        m17 = min(r['margin_to_trip_min_V'][key] for r in rows if r['I0_A'] == 1.7)
        fp = max(f['by_filter'][key]['V_peak_at_FET_off'] for f in fails if f['by_filter'][key])
        ta = max(f['by_filter'][key]['time_above_8V2_us'] for f in fails if f['by_filter'][key])
        # allowances: peaking on the loop deviation, plus the spike attenuated by the filter (first order, width SPIKE_W_S)
        spike = SPIKE_V * (1.0 if tau == 0 else (1 - math.exp(-SPIKE_W_S / tau)))
        m_allow = min(trip_lo - (v_static + PEAKING * r['filtered_dV_V'][key] + spike) for r in rows)
        verdict[key] = {'worst_margin_with_allowances_V': round(m_allow, 3), 'spike_at_comparator_V': round(spike, 4),
                        'C_f_nF_at_Rth_9k39': round(tau / (154e3 * 10e3 / 164e3) * 1e9, 2) if tau else 0.0,
                        'worst_nuisance_margin_V_all': round(m, 3), 'worst_margin_4A33_V': round(m43, 3),
                        'worst_margin_1A7_V': round(m17, 3), 'fail_high_peak_V': fp, 'fail_high_time_above_8V2_us': ta}
    out = {'id': 'pintle_rail_ovtrip_v1', 'version': 'v1', 'date': '2026-10-13', 'owner': 'electronics',
           'inputs_read': {'pintle_rail_v3': {'static_upper_V': v_static, 'trip_V': [trip_lo, trip_nom, trip_hi]}},
           'model': 'SIM averaged buck-boost (see docstring); every tolerance tagged; B-PWR-2 measures the real peak',
           'capacitance_cases': {k: {'C_uF': round(c_and_esr(k)[0] * 1e6, 1), 'ESR_mOhm': round(c_and_esr(k)[1] * 1e3, 1)}
                                 for k in ('nominal', 'worst_hot_eol', 'worst_cold_eol')},
           'load_release_rows': rows, 'fail_high_rows': fails, 'filter_verdict': verdict}
    json.dump(out, open(os.path.join(RES, 'pintle_rail_ovtrip_v1.json'), 'w'), indent=1)
    L = ['pintle_rail_ovtrip_v1 (Electronics 2026-10-13): OV-disconnect false-trip margin with capacitor tolerance, ageing and '
         'temperature; trip filter',
         f'static upper (divider B) {v_static} V; LTC4365 trip {trip_lo}/{trip_nom}/{trip_hi} V; f_c {F_C / 1e3:.0f} kHz designed at '
         f'C {c_design * 1e6:.0f} uF; capacitance cases ' + ', '.join(f'{k} {v["C_uF"]} uF / {v["ESR_mOhm"]} mOhm'
                                                                     for k, v in out['capacitance_cases'].items()),
         '%-6s %4s %-15s %6s %5s %4s %5s %7s | filtered dV (0/5/10/22/47 us) -> margin to the 8.06 V minimum trip' % (
             'mode', 'Vin', 'case', 'C_uF', 'ESR', 'f_i', 'I0', 'dVpk')]
    for r in rows:
        L.append('%-6s %4.1f %-15s %6.1f %5.1f %4.0f %5.2f %7.3f | %s -> %s' % (
            r['mode'], r['vin'], r['case'], r['C_uF'], r['ESR_mOhm'], r['f_i_kHz'], r['I0_A'], r['dV_peak_V'],
            ' '.join(f'{v:6.3f}' for v in r['filtered_dV_V'].values()), ' '.join(f'{v:6.3f}' for v in r['margin_to_trip_min_V'].values())))
    L.append('fail-high (regulator at its 8 A inductor limit, trip at the 8.34 V maximum threshold, +6 us to FET off):')
    for f in fails:
        L.append(f'  {f["mode"]} {f["vin"]} V {f["case"]} C {f["C_uF"]} uF ramp {f["dVdt_V_per_ms"]} V/ms: ' +
                 '; '.join(f'{k}: peak {v["V_peak_at_FET_off"]} V, {v["time_above_8V2_us"]} us > 8.2 V' for k, v in f['by_filter'].items() if v))
    L.append('verdict per OV-pin filter tau:')
    for k, v in verdict.items():
        L.append(f'  tau {k:>5s} (C_f {v["C_f_nF_at_Rth_9k39"]} nF): margin with x{PEAKING} peaking + {SPIKE_V * 1e3:.0f} mV spike '
                 f'{v["worst_margin_with_allowances_V"]} V; model-only worst margin {v["worst_nuisance_margin_V_all"]} V '
                 f'(4.33 A {v["worst_margin_4A33_V"]}, 1.7 A {v["worst_margin_1A7_V"]}); fail-high peak {v["fail_high_peak_V"]} V, '
                 f'{v["fail_high_time_above_8V2_us"]} us above 8.2 V')
    open(os.path.join(RES, 'pintle_rail_ovtrip_v1.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
