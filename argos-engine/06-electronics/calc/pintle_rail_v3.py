#!/usr/bin/env python3
"""Pintle servo rail, v3 (Electronics, 2026-10-13): worst-case UPPER voltage for the HV69 jam-load sizing, the lower bound for
the opening margin, transient envelopes and the regulator fail-high case. Supersedes pintle_rail_v2 for these bounds; v2
(regulator selection, operating points, thermal) stays valid and is kept as evidence (results/pintle_rail_v2.*).

Lead question 2026-10-13 (Mechanical pintle v2.3): "what is the pintle rail's worst-case upper voltage (regulator setpoint
tolerance + load-step overshoot + temperature), nominal about 7.49 V? Mechanical sized the HV69 jam load at 7.6 V: 817 N.
If your worst case exceeds 7.6 V, say by how much; otherwise confirm 7.6 V as the bound and publish it in electronics.json."

Method (every number tagged):
  static (DC regulation; this is what a STALLED servo sees, the jam is a steady load):
    Vout = VREF (1 + Rup/Rbt) + I_FB_sink * Rup
    terms: VREF 1.188-1.212 V over TJ -40..125 C [DATASHEET, includes temperature]; divider tolerance; resistor TCR, not
    tracking, over the board range; resistor drift; FB leakage 100 nA (sign not given -> +/-) [DATASHEET]; FB sinking
    current of the cable-droop block with CDC floating: MIN 0 / TYP 0.3 uA, NO MAX printed [DATASHEET] -> bound 2 x typ
    [ASSUMED]; output ripple (peak). Worst case = linear sum; RSS shown for information (bias terms added linearly).
  transient (not static loads):
    load release dV ~ dI / (2 pi f_c C_eff) [standard first-order estimate]; f_c <= f_RHPZ / 5 at the boost worst case.
    A load release happens when the servo current FALLS (servo stops or reverses), i.e. NOT while it is stalled.
    line step during a stall (TVC servos releasing, VBAT recovering 6.6 -> 8.4 V): no datasheet number (only a waveform,
    Fig. 8-10) -> 1 % allowance [ASSUMED] until B-PWR-2 measures it.
  failure (regulator fails high): FB top resistor open or FB pin open -> the converter regulates up to its own output
    over-voltage protection, 22.5-24.5 V [DATASHEET]; a shorted buck high-side FET passes VBAT (<= 8.4 V). Proposed
    mitigation: independent OV disconnect (LTC4365, OV threshold 492.5-507.5 mV over temperature, fault delay 1-2 us,
    gate fast turn-off 2-4 us [DATASHEET]) between the regulator and the servo connector.
  jam load mapping: Mechanical's table (hub 03-cad/calcs/pintle_inline_v34_v2p3.json, jam.by_rail_voltage, F_link at pin
    friction 0) interpolated linearly in V (read from the file, not copied).
Outputs: ../results/pintle_rail_v3.json and .txt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'results')

TPS = {  # TI TPS552882 datasheet, https://www.ti.com/lit/ds/symlink/tps552882.pdf (read 2026-10-13 via WebFetch)
    'VREF_V': (1.188, 1.200, 1.212), 'VREF_cond': 'TJ = -40..125 C (typ at 25 C)',
    'IFB_LKG_A': 100e-9, 'IFB_LKG_cond': 'TJ up to 125 C, single value printed (treated as +/- bound)',
    'IFB_CDC_float_typ_A': 0.3e-6, 'IFB_CDC_float_cond': 'external feedback, RCDC floating, VISP-VISN 50 mV: MIN 0, TYP 0.3 uA, no MAX printed',
    'IFB_CDC_eq': 'IFB_CDC = 3 (VISP-VISN) / RCDC (consistent with the 7.23-7.87 uA row at RCDC 20k, 50 mV); dVout = IFB_CDC * Rup',
    'VSNS_V': (0.048, 0.050, 0.052), 'OVP_V': (22.5, 23.5, 24.5), 'tSS_s': (0.003, 0.004, 0.005),
    'MODE_FPWM': 'MODE 0 Ohm to AGND = internal VCC, PWM; in FPWM the power flow can reverse (output to input): servo '
                 'regeneration is returned to VBAT; no reverse-current limit is printed',
    'tag': 'DATASHEET',
}
LTC = {  # ADI LTC4365 datasheet Rev B, https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4365.pdf
    'VOV_V': (0.4925, 0.500, 0.5075), 'VOV_cond': 'full operating temperature range (H grade -40..125 C)',
    'ILEAK_A': 10e-9, 't_fault_s': 2e-6, 't_gate_fast_s': 4e-6, 'recovery_s': (0.026, 0.036, 0.049),
    'VIN_op_V': (2.5, 34.0), 'gate_drive_V_at_5V': (3.0, 3.6, 4.2),
    'price': 'ADI page "Starting From $2.29" 1ku list (a "from" price: NOT a quote) -> TO-QUOTE Mouser DK / Digi-Key DK, ship to DK-6400',
    'tag': 'DATASHEET',
}
DIVIDERS = {
    'A_v2_baseline_100k_19k1': {'Rup': 100e3, 'Rbt': 19.1e3, 'tol': 0.001, 'tcr': 25e-6,
                                'tag': 'DESIGN v2 (LEAD 2026-10-12 +1 % setpoint); TCR 25 ppm/K ASSUMED for the 0.1 % thin-film class'},
    'B_v3_proposed_24k9_4k75': {'Rup': 24.9e3, 'Rbt': 4.75e3, 'tol': 0.001, 'tcr': 10e-6,
                                'tag': 'DESIGN v3 proposal: same setpoint (+0.1 %), FB-current terms / 4; 0.1 %, 10 ppm/K thin film '
                                       '(part number TO-CONFIRM, e.g. Susumu RG / Panasonic ERA-xAR class)'},
    'C_v1_setpoint_24k9_4k81': {'Rup': 24.9e3, 'Rbt': 4.81e3, 'tol': 0.001, 'tcr': 10e-6,
                                'tag': 'option (lead decision needed): the v1 setpoint (~7.41 V) with the v3 divider class'},
}
DT_RES_K = 60.0          # [DESIGN] FB resistors: board range -35..+85 C -> |T - 25 C| <= 60 K
DRIFT = 0.0005           # [ASSUMED] 0.05 % per resistor over life (thin film load life; maker data TO-CONFIRM), not tracking
IFB_CDC_BOUND_A = 2 * TPS['IFB_CDC_float_typ_A']   # [ASSUMED] 2 x the printed typical (no maximum printed); B-PWR-1 measures
L_H = 4.7e-6             # [DESIGN v2]
F_SW = 400.8e3           # [DERIVED v2] RFSW 49.9k
R_SNS = 0.012            # [DESIGN v2]
I_STALL_BOUND_A = 1.7    # [DERIVED v2] HV69 stall 1.2-1.7 A + 0.1 A electronics; unpublished, B-PNT-1 measures
VIN_MIN = 6.0            # [DESIGN v2] regulator design minimum input
ETA = 0.92               # [ASSUMED v2]
C_CER_NOM = 4 * 22e-6    # [DESIGN v2] 4 x 22 uF X7R 16 V 1210
CER_BIAS_DERATE = 0.50   # [ASSUMED] X7R 16 V 1210 at 7.5 V DC bias keeps ~50 % (maker DC-bias curve TO-CONFIRM)
C_POLY = 220e-6          # [DESIGN v2] polymer at the servo connector
POLY_TOL = 0.80          # [ASSUMED] -20 % capacitance tolerance
F_C_TARGET = 5.0e3       # [DESIGN target] loop crossover (COMP network to be designed; B-PWR-2 measures)
LINE_STEP_FRAC = 0.01    # [ASSUMED] line-step deviation allowance (no datasheet number), B-PWR-2
HV69_RATING_V = 8.2      # [retailer copies of MKS data, TO-CONFIRM with MKS]
OV_RUP, OV_RBT = 154e3, 10.0e3   # [DESIGN] LTC4365 OV divider: 0.5 V x (1 + 15.4) = 8.20 V nominal


def vout(vref, rup, rbt, i_sink=0.0):
    return vref * (1.0 + rup / rbt) + i_sink * rup


def interp(xs, ys, x):
    pts = sorted(zip(xs, ys))
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        if x <= x1 or (x1, y1) == pts[-1]:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    a = ap.parse_args()
    mpath = os.path.join(a.engine_root, '03-cad', 'calcs', 'pintle_inline_v34_v2p3.json')
    mraw = open(mpath, 'rb').read()
    mech = json.loads(mraw)
    jt = mech['jam']['by_rail_voltage']
    jv = [float(k.rstrip('V')) for k in jt]
    jf = [jt[k]['F_link_N_mu_p_0'] for k in jt]
    jT = [jt[k]['T_stall_Nm'] for k in jt]
    jam_design = mech['jam']['design_F_link_N']
    c2_margin = min(mech['baseline']['C2_L1']['margin_7V4'], mech['baseline']['C2_L2']['margin_7V4'])
    stall_tab = mech['inputs']['HV69']['stall_Nm']          # retailer copies (Electronics msg), V -> N m
    sv = sorted((float(k), v) for k, v in stall_tab.items())

    def t_stall(v):
        return interp([p[0] for p in sv], [p[1] for p in sv], v)

    def f_jam(v):
        return interp(jv, jf, v)

    # ---- capacitance, ripple, crossover limit
    c_eff1 = C_CER_NOM * CER_BIAS_DERATE + C_POLY * POLY_TOL
    c_eff2 = c_eff1 + C_POLY * POLY_TOL
    i_lim_max = TPS['VSNS_V'][2] / R_SNS
    res = {}
    for name, d in DIVIDERS.items():
        rup, rbt, tol, tcr = d['Rup'], d['Rbt'], d['tol'], d['tcr']
        k = rup / rbt
        sens = k / (1 + k)                       # dVout/Vout per unit change of Rup/Rbt
        v_typ = vout(TPS['VREF_V'][1], rup, rbt)
        v_dc_max = TPS['VREF_V'][2] * (1 + k * (1 + tol) / (1 - tol))
        v_dc_min = TPS['VREF_V'][0] * (1 + k * (1 - tol) / (1 + tol))
        d_tcr = v_typ * sens * (2 * tcr * DT_RES_K)
        d_drift = v_typ * sens * (2 * DRIFT)
        d_lkg = TPS['IFB_LKG_A'] * rup
        d_cdc = IFB_CDC_BOUND_A * rup
        d_cdc_typ = TPS['IFB_CDC_float_typ_A'] * rup
        # boost worst case at VIN_MIN: duty and ripple at the current limit and at the stall bound
        dty = 1 - VIN_MIN * ETA / v_typ
        rip_pk = {f'{i:.2f}A': 0.5 * i * dty / (F_SW * c_eff1) for i in (I_STALL_BOUND_A, i_lim_max)}
        rip = max(rip_pk.values())
        up_terms = {'VREF+divider tolerance (DC, incl. temperature of VREF)': v_dc_max - v_typ,
                    'resistor TCR, not tracking, |dT| 60 K': d_tcr, 'resistor drift 0.05 % each': d_drift,
                    'FB leakage 100 nA x Rup': d_lkg, 'CDC floating FB sink (2 x 0.3 uA typ) x Rup': d_cdc,
                    'output ripple (peak, boost at 6.0 V, 4.33 A)': rip}
        v_static_max = v_typ + sum(up_terms.values())
        # RSS of the random terms (VREF and tolerance treated as one), biases linear
        v_rand = math.sqrt((v_dc_max - v_typ) ** 2 + d_tcr ** 2 + d_drift ** 2 + d_lkg ** 2)
        v_static_rss = v_typ + v_rand + d_cdc + rip
        lo_terms = {'VREF+divider tolerance': v_dc_min - v_typ, 'TCR': -d_tcr, 'drift': -d_drift, 'FB leakage': -d_lkg,
                    'ripple': -rip}
        v_static_min = v_typ + sum(lo_terms.values())      # CDC sink only raises Vout: no credit taken at the low end
        # transients
        r_l = v_typ / i_lim_max
        dprime = VIN_MIN / v_typ
        f_rhpz = dprime ** 2 * r_l / (2 * math.pi * L_H)
        f_c_max = f_rhpz / 5
        f_c = min(F_C_TARGET, f_c_max)
        rel = {}
        for cname, ce in (('C_eff 220 uF (v2: 4x22 uF + 1x220 uF)', c_eff1), ('C_eff 396 uF (v3: + 2nd 220 uF polymer)', c_eff2)):
            rel[cname] = {f'{i:.2f}A': i / (2 * math.pi * f_c * ce) for i in (I_STALL_BOUND_A, i_lim_max)}
        v_line = v_static_max * (1 + LINE_STEP_FRAC)
        res[name] = {
            'divider': d, 'Vout_typ_V': round(v_typ, 4), 'Vout_DC_min_max_V': [round(v_dc_min, 4), round(v_dc_max, 4)],
            'upper_terms_V': {kk: round(vv, 4) for kk, vv in up_terms.items()},
            'static_upper_worst_V': round(v_static_max, 4), 'static_upper_rss_V': round(v_static_rss, 4),
            'static_lower_worst_V': round(v_static_min, 4), 'lower_terms_V': {kk: round(vv, 4) for kk, vv in lo_terms.items()},
            'cdc_typ_shift_V': round(d_cdc_typ, 4),
            'jam_F_link_N_at_static_upper': round(f_jam(v_static_max), 1),
            'jam_F_link_N_at_static_rss': round(f_jam(v_static_rss), 1),
            'line_step_during_stall': {'V_peak': round(v_line, 4), 'F_link_N': round(f_jam(v_line), 1),
                                       'note': '<= ~1 ms (current-loop recovery), 1 % ASSUMED: not a static load'},
            'load_release': {'f_RHPZ_Hz_boost_6V0_4A33': round(f_rhpz), 'f_c_used_Hz': round(f_c),
                             'dV_V': {c: {i: round(v, 3) for i, v in r.items()} for c, r in rel.items()},
                             'V_peak_V': {c: round(v_static_max + max(r.values()), 3) for c, r in rel.items()},
                             'coincident_with_stall': False},
            'opening_margin_at_static_lower': {
                'T_stall_Nm': round(t_stall(v_static_min), 4),
                'C2_margin': round(c2_margin * t_stall(v_static_min) / t_stall(7.4), 3),
                'basis': f'Mechanical v2.3 C2 margin {c2_margin} at 7.4 V scaled by the HV69 stall-torque table (rail value, '
                         'before the harness drop at the opening current)'},
        }
    # ---- failure case and the OV disconnect
    ov_nom = LTC['VOV_V'][1] * (1 + OV_RUP / OV_RBT)
    ov_lo = LTC['VOV_V'][0] * (1 + OV_RUP * 0.999 / (OV_RBT * 1.001))
    ov_hi = LTC['VOV_V'][2] * (1 + OV_RUP * 1.001 / (OV_RBT * 0.999))
    i_l_lim = 330e3 / 41.2e3          # [DERIVED v2] ~8 A average inductor current limit
    dvdt = i_l_lim / c_eff2           # failed regulator charging the output at its current limit
    t_resp = LTC['t_fault_s'] + LTC['t_gate_fast_s']
    fail = {
        'modes': {'FB top resistor open / FB pin open': f'Vout -> regulator OVP {TPS["OVP_V"][0]}-{TPS["OVP_V"][2]} V [DATASHEET]',
                  'FB bottom resistor open': 'Vout -> ~VREF (1.2 V): servo weak, spring closes (fail-safe direction)',
                  'buck high-side FET short': 'Vout ~ VBAT <= 8.4 V (Mechanical row "regulator failed through")'},
        'without_OV_disconnect_V': TPS['OVP_V'][2],
        'OV_disconnect': {'part': 'ADI LTC4365HTS8 (TSOT-23-8, -40..125 C) + 1 N-MOSFET (30 V logic-level, TO-SELECT), OV divider '
                                  '154k / 10.0k 0.1 %', 'trip_V_min_nom_max': [round(ov_lo, 3), round(ov_nom, 3), round(ov_hi, 3)],
                          'response_s': t_resp, 'dVdt_V_per_s': round(dvdt), 'overshoot_during_response_V': round(dvdt * t_resp, 3),
                          'peak_V': round(ov_hi + dvdt * t_resp, 3), 'after_trip': 'servo unpowered -> spring closes the needle '
                          '(PINTLE_FAULT / PC_BAND abort path); auto-retry after 26-49 ms only if the rail is back in the window',
                          'price': LTC['price']},
        'nuisance_trip_margin_V': {c: round(ov_lo - v, 3) for c, v in res['B_v3_proposed_24k9_4k75']['load_release']['V_peak_V'].items()},
    }
    pick = res['B_v3_proposed_24k9_4k75']
    base = res['A_v2_baseline_100k_19k1']
    c2k = 'C_eff 396 uF (v3: + 2nd 220 uF polymer)'
    up = lambda v: math.ceil(v * 100 - 1e-9) / 100          # round UP to 10 mV
    ov = fail['OV_disconnect']
    publish = {
        'configuration': 'v3 recommended: divider B 24.9k/4.75k 0.1 %% 10 ppm/K, CDC floating, FPWM, 2nd 220 uF polymer, LTC4365 OV '
                         'disconnect 8.2 V nominal (present v2 divider A gives %.3f V static worst)' % base['static_upper_worst_V'],
        'V_rail_max_static_V': {'v': up(pick['static_upper_worst_V']),
                                'tag': 'DERIVED pintle_rail_v3, linear worst case %.3f V (RSS %.3f V); applies to a STALLED servo'
                                       % (pick['static_upper_worst_V'], pick['static_upper_rss_V'])},
        'jam_F_link_N_at_V_rail_max_static': {'v': round(f_jam(up(pick['static_upper_worst_V'])), 1),
                                              'tag': 'DERIVED from Mechanical pintle v2.3 jam table (pin friction 0, -10 % spring)'},
        'V_rail_line_step_during_stall_V': {'v': up(pick['line_step_during_stall']['V_peak']),
                                            'tag': 'ASSUMED 1 %% allowance (no datasheet number), <= ~1 ms, B-PWR-2 measures; jam %.1f N'
                                                   % f_jam(up(pick['line_step_during_stall']['V_peak']))},
        'V_rail_peak_load_release_V': {'v': up(pick['load_release']['V_peak_V'][c2k]),
                                       'tag': 'DERIVED, 4.33 A release, f_c 5 kHz, C_eff 396 uF; current falling = not coincident '
                                              'with a stall; B-PWR-2'},
        'V_rail_failure_static_max_V': {'v': up(ov['trip_V_min_nom_max'][2]),
                                        'tag': 'DERIVED: LTC4365 OV trip max (a failure can park the rail just below it); '
                                               'without the disconnect the regulator OVP allows %.1f V' % TPS['OVP_V'][2]},
        'V_rail_failure_peak_V': {'v': ov['peak_V'], 'tag': 'DERIVED, <= 6 us, then the servo is unpowered'},
        'V_rail_min_static_V': {'v': math.floor(pick['static_lower_worst_V'] * 100) / 100,
                                'tag': 'DERIVED (C2 margin %.3f at the rail, before the harness drop)'
                                       % pick['opening_margin_at_static_lower']['C2_margin']},
        'jam_detection': {'v': 'stall time path 0.10 s after the last progress mark (current path 0.02 + 0.05 s when the pintle '
                               'current sense is fitted); back-off command the same 1 ms tick; in ABORT a further 0.10 s without '
                               'closing progress releases the ARM bus (servo unpowered)', 'tag': 'DESIGN firmware v2.6 config.h'},
    }
    out = {'id': 'pintle_rail_v3', 'version': 'v3', 'date': '2026-10-13', 'owner': 'electronics',
           'question': 'LEAD 2026-10-13: worst-case upper pintle-rail voltage vs the 7.6 V jam sizing (Mechanical pintle v2.3)',
           'inputs_read': {'mechanical_pintle_v2p3': {'path': mpath, 'sha256_16': hashlib.sha256(mraw).hexdigest()[:16],
                                                      'jam_design_F_link_N': jam_design, 'C2_margin_7V4': c2_margin}},
           'tps552882': TPS, 'ltc4365': LTC,
           'assumptions': {'dT_res_K': DT_RES_K, 'drift_each': DRIFT, 'IFB_CDC_bound_A': IFB_CDC_BOUND_A,
                           'C_eff_F': [c_eff1, c_eff2], 'cer_bias_derate': CER_BIAS_DERATE, 'f_c_target_Hz': F_C_TARGET,
                           'line_step_frac': LINE_STEP_FRAC, 'I_stall_bound_A': I_STALL_BOUND_A, 'I_out_limit_max_A': i_lim_max},
           'dividers': res, 'failure': fail, 'publish': publish,
           'design_actions': ['CDC pin floating (cable-droop compensation off); MODE 0 Ohm = FPWM (regeneration returned to VBAT)',
                              'FB divider 24.9k / 4.75k 0.1 % 10 ppm/K (B): FB-current offsets / 4, setpoint unchanged (7.49 V typ)',
                              'second 220 uF 16 V polymer at the servo connector (load-release peak below the OV trip)',
                              'LTC4365 OV disconnect at 8.2 V nominal between TPS552882 and J_PINTLE (regulator fail-high)',
                              'COMP network designed for f_c ~5 kHz at VIN 6.0 V / 4.33 A (f_RHPZ/5), verified in B-PWR-2'],
           'bench': ['B-PWR-1: Vout at 0 / 1.7 / 4 A and -20 / 25 / 70 C board (static terms, CDC-floating offset)',
                     'B-PWR-2: load release 4.3 A -> 0 and line step 6.6 -> 8.4 V (< 100 us) with the HV69 stalled; pass: '
                     'static <= 7.65 V, transient < OV trip min, no LTC4365 trip; LTC4365 trip and fail-high injection (FB open) '
                     'on a dummy load, not the servo'],
           }
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, 'pintle_rail_v3.json'), 'w'), indent=1)
    L = ['pintle_rail_v3 (Electronics 2026-10-13): worst-case pintle-rail voltage for the HV69 jam sizing (LEAD question, MECH v2.3)',
         f'Mechanical input: {mpath} sha256/16 {hashlib.sha256(mraw).hexdigest()[:16]} (jam {jam_design} N at 7.6 V, C2 {c2_margin} at 7.4 V)',
         'TPS552882: VREF 1.188-1.212 V over TJ -40..125 C; FB leakage 100 nA; CDC-floating FB sink typ 0.3 uA (no max printed -> 0.6 uA)']
    for name, r in res.items():
        L.append(f'--- divider {name}: typ {r["Vout_typ_V"]:.3f} V, DC {r["Vout_DC_min_max_V"][0]:.3f}-{r["Vout_DC_min_max_V"][1]:.3f} V')
        for kk, vv in r['upper_terms_V'].items():
            L.append(f'      + {kk:58s} {vv * 1000:7.1f} mV')
        L.append(f'    STATIC upper worst {r["static_upper_worst_V"]:.3f} V (RSS {r["static_upper_rss_V"]:.3f} V) -> jam F_link '
                 f'{r["jam_F_link_N_at_static_upper"]} N ({r["jam_F_link_N_at_static_rss"]} N RSS); static lower '
                 f'{r["static_lower_worst_V"]:.3f} V -> C2 margin {r["opening_margin_at_static_lower"]["C2_margin"]}')
        lr = r['load_release']
        L.append(f'    load release (f_RHPZ {lr["f_RHPZ_Hz_boost_6V0_4A33"]} Hz, f_c {lr["f_c_used_Hz"]} Hz): ' +
                 '; '.join(f'{c}: {lr["dV_V"][c]} -> peak {lr["V_peak_V"][c]} V' for c in lr['dV_V']))
        L.append(f'    line step during a stall (1 % ASSUMED): {r["line_step_during_stall"]["V_peak"]:.3f} V -> '
                 f'{r["line_step_during_stall"]["F_link_N"]} N (<= ~1 ms)')
    od = fail['OV_disconnect']
    L.append(f'FAILURE: FB open -> regulator OVP {TPS["OVP_V"][0]}-{TPS["OVP_V"][2]} V (no protection today); LTC4365 OV disconnect '
             f'trip {od["trip_V_min_nom_max"]} V, response {od["response_s"] * 1e6:.0f} us at {od["dVdt_V_per_s"] / 1000:.0f} V/ms -> peak '
             f'{od["peak_V"]} V then 0 V; nuisance-trip margin {fail["nuisance_trip_margin_V"]}')
    L.append('PUBLISH (' + publish['configuration'] + '):')
    for k, v in publish.items():
        if k != 'configuration':
            L.append(f'    {k}: {v["v"]}  [{v["tag"]}]')
    open(os.path.join(OUT, 'pintle_rail_v3.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
