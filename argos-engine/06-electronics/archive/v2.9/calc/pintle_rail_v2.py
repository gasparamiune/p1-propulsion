#!/usr/bin/env python3
"""Regulated pintle-servo rail, v2 (Electronics, 2026-10-12). v2 = LEAD decision 2026-10-12 on the S3 spring re-run: setpoint
raised ~1 % (FB 100k/19.1k, 7.48 V typ) so the HV69 opening margin stays >= 1.5 at the servo plug at the low end of the
tolerance (calc/pintle_dynamics_v2.py); the bearing jam case moves to the new upper tolerance (~603 N, within s0, MECH told).
Output tolerance now includes the 0.1 % FB resistors. v1 (19.3k, 7.42 V typ) kept as evidence (results/pintle_rail_v1.*).

LEAD 2026-10-12 (mini pintle servo decision, item 2): "Add a regulated pintle servo rail at 7.4 V nominal. That removes the
8.2 vs 8.4 V question, and it isolates throttle response from TVC stall sag. Size the regulator so it holds 7.4 V over the
whole battery range down to the 6.6 V TVC-sag case. Pick the topology yourself (buck-boost or otherwise), and list the part
and price as TO-QUOTE."

Design basis (every number tagged):
  input  = VBAT node after F101 and the shunt (2S Li-ion/LiPo): 8.4 V full charge, 6.6 V TVC-sag case (LEAD V_val at the
           TVC plug; the VBAT node sits ~0.2 V above it), 6.0 V design minimum (margin below V_val, BATT_LOW region)
  output = 7.4 V nominal (LEAD); MKS HV69 rated 8.2 V max (retailer copies of MKS data, three sources) -> 7.4 V + 1.2 %
           reference tolerance stays below 8.2 V
  load   = MKS HV69 stall current NOT PUBLISHED (B-PNT-1 measures it). Bound from the published stall torque and no-load
           speed: P_mech,max = Ts w_nl / 4 = 2.15 W at 7.4 V (DERIVED, pintle_mini_servo_v1); a DC motor at stall draws
           I_s = 4 P_max / (eta_g V) -> 1.2-1.7 A for gear efficiency 1.0-0.7 (ASSUMED) plus ~0.1 A electronics.
           Design: 4 A output current limit (>= 2.4 x the bound), 8 A average inductor current limit.
Topology: 4-switch synchronous buck-boost (the input range 6.0-8.4 V straddles 7.4 V, so neither a buck nor a boost alone
holds the output). Part: TI TPS552882 (DATASHEET SLVSF..., product page https://www.ti.com/product/TPS552882): 2.7-36 V in,
0.8-22 V out, VREF 1.2 V (1.188-1.212 V), FB divider (no I2C), programmable average inductor current limit up to 16 A,
optional output current limit 50 mV (48-52 mV) across ISP/ISN, fSW 200 kHz-2.2 MHz by RFSW, soft start 4 ms, VQFN-HR 4.0 x
3.5 mm, -40..125 C. Alternative considered: TI TPS63070 (2.0-16 V in, 2.5-9 V out, 3.6 A switch limit, 2 A output in boost
at 4 V -> 5 V; https://www.ti.com/product/TPS63070): smaller, but ~2.3 A available at 6 V -> 7.4 V leaves no margin against
an unpublished stall current.
Outputs: ../results/pintle_rail_v2.json and .txt
"""
from __future__ import annotations

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'results')

VREF = (1.188, 1.200, 1.212)       # [DATASHEET TPS552882] FB reference min/typ/max [V]
R_FB_UP = 100e3                    # [DATASHEET recommendation] top divider resistor
R_FB_BT = 19.1e3                   # [DESIGN, LEAD 2026-10-12] E96/E192 0.1 % -> 7.48 V typ (v1: 19.3k, 7.42 V)
R_TOL = 0.001                      # [DESIGN] FB divider resistors 0.1 % (thin film)
R_FSW = 49.9e3                     # [DATASHEET example] 400 kHz (RFSW ~ 20 kOhm MHz / fSW, three datasheet points)
F_SW = 20e3 * 1e6 / R_FSW          # [DERIVED] Hz (reconstructed relation, matches 100k->200k, 49.9k->400k, 9.09k->2.2M)
L_H = 4.7e-6                       # [DESIGN] 4.7 uH nominal (datasheet: 1-10 uH effective, L > 1.2/fSW)
VSNS = (0.048, 0.050, 0.052)       # [DATASHEET] output current-limit sense voltage
R_SNS = 0.012                      # [DESIGN] 12 mOhm -> 4.2 A typ output current limit
R_ILIM = 41.2e3                    # [DESIGN] ~8 A average inductor current limit: I_LIM ~ 330 A kOhm / R_ILIM, DERIVED from the
                                   #   two datasheet points (20 kOhm -> 16.5 A, 60 kOhm -> 5.5 A); TO-CONFIRM with Eq. 5
ETA = {'v': 0.92, 'range': [0.88, 0.95], 'tag': 'ASSUMED (datasheet: 97 % at 12 V -> 20 V, 3 A; lower at 7.4 V out)'}
VIN_CASES = {'full charge': 8.4, 'nominal': 7.6, 'TVC-sag case (LEAD 6.6 V at the TVC plug)': 6.8, 'V_val at VBAT node': 6.6,
             'design minimum': 6.0}
IOUT_CASES = {'hold / slow throttle': 0.4, 'stall bound (DERIVED 1.2-1.7 A)': 1.7, 'output current limit': 4.2}
I_STALL_BOUND = {'P_max_W_7.4V': 2.15, 'eta_gear': [0.7, 1.0], 'I_electronics_A': 0.1,
                 'tag': 'DERIVED from pintle_mini_servo_v1 (retailer copies of MKS data); B-PNT-1 measures it'}
RTHJA = (25.8, 47.5)               # [DATASHEET] VQFN-HR 26-pin, EVM 4-layer vs JEDEC (column mapping garbled in the extract)
T_AMB = 50.0                       # [DESIGN] ECU bay ambient


def main():
    v_out = [VREF[0] * (1 + R_FB_UP * (1 - R_TOL) / (R_FB_BT * (1 + R_TOL))), VREF[1] * (1 + R_FB_UP / R_FB_BT),
             VREF[2] * (1 + R_FB_UP * (1 + R_TOL) / (R_FB_BT * (1 - R_TOL)))]
    i_lim_out = [v / R_SNS for v in VSNS]
    rows = []
    for vn, vin in VIN_CASES.items():
        for iname, iout in IOUT_CASES.items():
            vo = v_out[1]
            p_out = vo * iout
            p_in = p_out / ETA['v']
            i_in = p_in / vin
            if vin < vo:     # boost region
                d = 1 - vin * ETA['v'] / vo
                il = iout / (1 - d)
                dil = vin * d / (L_H * F_SW)
                mode = 'boost'
            elif vin > vo * 1.05:
                d = vo / (vin * ETA['v'])
                il = iout
                dil = (vin - vo) * d / (L_H * F_SW)
                mode = 'buck'
            else:
                d = float('nan')
                il = iout * vo / vin
                dil = 0.3 * il
                mode = 'buck-boost'
            p_loss = p_in - p_out
            rows.append({'case': vn, 'Vin_V': vin, 'load': iname, 'Iout_A': iout, 'mode': mode,
                         'I_L_avg_A': round(il, 2), 'I_L_ripple_pp_A': round(dil, 2), 'I_L_peak_A': round(il + dil / 2, 2),
                         'I_in_A': round(i_in, 2), 'P_loss_W': round(p_loss, 2),
                         'Tj_C_range': [round(T_AMB + p_loss * RTHJA[0], 0), round(T_AMB + p_loss * RTHJA[1], 0)]})
    out = {
        'id': 'pintle_rail_v2', 'version': 'v2', 'date': '2026-10-12', 'owner': 'electronics',
        'requirement': {'v': 'regulated pintle servo rail ~7.49 V typ (v2, LEAD: +1 % so the opening margin >= 1.5 at the servo plug), '
                              'held over the battery range down to the 6.6 V TVC-sag case', 'tag': 'LEAD 2026-10-12'},
        'topology': '4-switch synchronous buck-boost (input 6.0-8.4 V straddles 7.4 V)',
        'part': {'pn': 'TI TPS552882RPMR (VQFN-HR 26, 4.0 x 3.5 mm)', 'src': 'https://www.ti.com/product/TPS552882',
                 'datasheet': 'https://www.ti.com/lit/ds/symlink/tps552882.pdf', 'tag': 'DATASHEET',
                 'price': 'TO-QUOTE Mouser Denmark / Digi-Key Denmark, ship to Sonderborg DK-6400 (TI page shows no price without login)'},
        'alternative': {'pn': 'TI TPS63070RNMR', 'src': 'https://www.ti.com/product/TPS63070',
                        'why_not': '3.6 A switch limit: ~2.3 A at 6 V -> 7.4 V, no margin against the unpublished HV69 stall current'},
        'components': {
            'R_FB_UP_ohm': R_FB_UP, 'R_FB_BT_ohm': R_FB_BT, 'Vout_V_min_typ_max': [round(v, 3) for v in v_out],
            'R_FSW_ohm': R_FSW, 'f_sw_Hz': round(F_SW), 'L_H': L_H,
            'L_requirements': 'Isat >= 8 A (above the 8 A average limit + ripple), Irms >= 6 A, DCR <= 20 mOhm; datasheet EVM uses '
                              'Coilcraft XAL1010-472ME (25.4 A sat, 17.5 A heating, 10 mOhm max, DATASHEET); a 6 x 6 mm XAL6060-class '
                              '4.7 uH part is the likely fit -> TO-CONFIRM against its datasheet, TO-QUOTE',
            'R_SNS_ohm': R_SNS, 'I_out_limit_A_min_typ_max': [round(i, 2) for i in i_lim_out],
            'R_ILIM_ohm': R_ILIM, 'I_L_avg_limit_A_approx': round(330e3 / R_ILIM, 1),
            'C_in': '4 x 10 uF X7R 25 V 1210 (datasheet range 4.7-22 uF total min) + the ECU VBAT bulk',
            'C_out': '4 x 22 uF X7R 16 V 1210 + 220 uF 16 V polymer at the servo connector (servo current steps)',
            'MODE': '0 Ohm to AGND: internal LDO, FPWM (fixed frequency: no audible PFM bursts, predictable EMI)',
            'EN': 'driven by the ARM-bus-derived PINTLE_RAIL_EN (rail off in SAFE unless the TVC/pintle bench test enables it); '
                  'EN/UVLO rising 1.23 V typ'},
        'vout_vs_servo_rating': {'Vout_max_V': round(v_out[2], 3), 'HV69_rating_V': 8.2,
                                 'margin_V': round(8.2 - v_out[2], 2), 'tag': 'DERIVED; HV69 8.2 V = retailer copies of MKS data'},
        'stall_current_bound': I_STALL_BOUND,
        'eta': ETA, 'operating_points': rows,
        'battery_side': {
            'pintle_hold_at_battery_A': round(7.42 * 0.4 / ETA['v'] / 6.8, 2),
            'note': 'calc/tvc_supply_budget_v1 I_other 1.0 A already carries ~0.45 A for the pintle servo; the regulated rail draws '
                    '~0.47 A at 6.8 V for a 0.4 A hold -> FM-PWR-01 constants unchanged'},
        'soft_start_s': {'v': 0.004, 'tag': 'DATASHEET 3-5 ms'},
        'open': ['HV69 stall current and current at 7.4 V under the needle load (B-PNT-1)',
                 'TPS552882 Eq. 5 (ILIM) and Eq. 6 (FB) confirmed against the original PDF (the extract was garbled)',
                 'inductor part number and price', 'layout: 4-layer ECU board, thermal pad vias, input loop < 10 mm',
                 'regulator efficiency at 7.4 V out measured on the bench (ASSUMED 0.92)'],
    }
    lines = ['pintle_rail_v2 (Electronics 2026-10-12): TPS552882 4-switch buck-boost, 7.48 V pintle servo rail (LEAD 2026-10-12, +1 % vs v1)',
             'Vout min/typ/max %.3f / %.3f / %.3f V (FB 100k/19.1k 0.1 %%, VREF 1.188-1.212 V); HV69 rated 8.2 V -> margin %.2f V'
             % (v_out[0], v_out[1], v_out[2], 8.2 - v_out[2]),
             'fSW %.0f kHz (RFSW 49.9k), L 4.7 uH, output current limit %.2f-%.2f A (12 mOhm), avg inductor limit ~%.1f A (RILIM 41.2k)'
             % (F_SW / 1e3, i_lim_out[0], i_lim_out[2], 330e3 / R_ILIM),
             '%-44s %5s %-30s %5s %-10s %6s %6s %6s %6s %6s %s' % ('input case', 'Vin', 'load', 'Iout', 'mode', 'IL_avg', 'IL_pp',
                                                                  'IL_pk', 'I_in', 'Ploss', 'Tj C (Rth 25.8/47.5)')]
    for r in rows:
        lines.append('%-44s %5.2f %-30s %5.2f %-10s %6.2f %6.2f %6.2f %6.2f %6.2f %s' % (
            r['case'][:44], r['Vin_V'], r['load'][:30], r['Iout_A'], r['mode'], r['I_L_avg_A'], r['I_L_ripple_pp_A'],
            r['I_L_peak_A'], r['I_in_A'], r['P_loss_W'], r['Tj_C_range']))
    lines.append('worst inductor peak %.2f A (< 8 A avg limit + ripple; inductor Isat >= 8 A); worst input current %.2f A at the '
                 '4.2 A output limit and 6.0 V' % (max(r['I_L_peak_A'] for r in rows), max(r['I_in_A'] for r in rows)))
    lines.append('stall-current bound (DERIVED, unpublished): 1.2-1.7 A + 0.1 A electronics; output limit 4.2 A = 2.4x the bound')
    lines.append('thermal: at the stall bound (1.7 A) Ploss ~1.1 W -> Tj 78-102 C at 50 C ambient (OK); a sustained stall AT the 4.2 A '
                 'limit (2.7 W) exceeds 125 C -> only a fault case (servo jammed): the pintle monitor aborts within 80 ms '
                 '(kPintleFaultTime_s) and the regulator thermal shutdown is the backstop')
    json.dump(out, open(os.path.join(OUT, 'pintle_rail_v2.json'), 'w'), indent=1)
    open(os.path.join(OUT, 'pintle_rail_v2.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
