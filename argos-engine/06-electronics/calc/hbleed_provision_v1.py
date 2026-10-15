#!/usr/bin/env python3
"""Head-end bleed PROVISION - ECU side (Electronics, 2026-10-13, v1).

Covers: (1) the MV switch + P_mid resistor ladder on Teensy pin 23 (A9) - values, worst-case code windows, decode thresholds (writes
firmware/src/core/mv_ladder_table.h); (2) the P_mid comparator (TE M3234 170BG -> LMV331 with hysteresis, ratiometric reference);
(3) P_mid vent-time estimate after V1 closes (mid volume <= 0.5 cm3, ICD) against kHbleedCloseConfirm_s with the datasheet valve times;
(4) coil drive budget; (5) why the ECU cannot see the bleed through P_feed (0.016 bar) - restated from config.h.

Tags: DESIGN (chosen values), DATASHEET (cited; the Burkert 6027 numbers come from a WebFetch summary of ds6027-standard-eu-en.pdf and
must be checked against the PDF - column mapping of the coil table was ambiguous), ASSUMED, DERIVED. Not a hardware validation: B-BLEED-1
(bench) measures the vent time, the comparator thresholds and the ladder codes on the built harness.
"""
from __future__ import annotations

import itertools
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))

E96 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65,
       1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80,
       2.87, 2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53, 4.64, 4.75,
       4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06,
       8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]


def par(*rs):
    g = sum(1.0 / r for r in rs if r is not None)
    return math.inf if g == 0 else 1.0 / g


# ------------------------------------------------------------------ (1) ladder: node at pin 23, Rtop to +3.3 V (= ADC reference, ratiometric)
# Branches to GND: R0 end-of-line resistor AT THE MV SWITCH CONNECTOR (always present when the harness is connected), R1 through the MV
# OPEN switch, R2 through the MV CLOSED switch (both at the valve), R3 through the on-board 2N7002 driven by the P_mid comparator.
TOL = 0.01          # [DESIGN] 1 % thin-film resistors (worst case, all resistors at their limits)
ADC_ERR = 0.004     # [ASSUMED] Teensy 4.1 ADC gain/offset/INL as a ratio of full scale (~16 LSB of 4096); B-BLEED-1 measures it
FET_RON = 7.5       # [DATASHEET 2N7002 max R_DS(on) at V_GS 5 V, ohm] in series with R3 (worst case)
SW_R = 0.5          # [ASSUMED] switch + harness resistance in series with R1 / R2 [ohm]


def codes(rt, r0, r1, r2, r3):
    out = []
    for o, c, p in itertools.product((0, 1), repeat=3):
        out.append(((o, c, p, 1), (r0, r1 if o else None, r2 if c else None, r3 if p else None)))
    out.append(((0, 0, 0, 0), (None,)))                 # harness open, comparator low
    out.append(((0, 0, 1, 0), (r3,)))                   # harness open, comparator high
    lst = []
    for bits, rs in out:
        rs = [r for r in rs if r is not None]
        lo = hi = None
        for signs in itertools.product((-1, 1), repeat=len(rs) + 1):
            rtt = rt * (1 + signs[0] * TOL)
            rr = []
            for k, r in enumerate(rs):
                x = r * (1 + signs[k + 1] * TOL)
                if r == r3:
                    x += FET_RON if signs[k + 1] > 0 else 0.0
                elif r in (r1, r2):
                    x += SW_R if signs[k + 1] > 0 else 0.0
                rr.append(x)
            rp = par(*rr)
            ratio = 1.0 if math.isinf(rp) else rp / (rtt + rp)
            lo = ratio if lo is None else min(lo, ratio)
            hi = ratio if hi is None else max(hi, ratio)
        rp = par(*rs)
        nom = 1.0 if math.isinf(rp) else rp / (rt + rp)
        lst.append({'bits': bits, 'nom': nom, 'lo': lo - ADC_ERR, 'hi': hi + ADC_ERR})
    return lst


def gap(lst):
    s = sorted(lst, key=lambda d: d['nom'])
    g = min(b['lo'] - a['hi'] for a, b in zip(s, s[1:]))
    return min(g, s[0]['lo'] - 0.02, 0.98 - s[-1]['hi'] if s[-1]['nom'] < 0.999 else 1.0), s   # short-to-GND window below 0.02


def e96(dec):
    return [v * 10 ** dec for v in E96]


best = None
RT = 10.0e3        # [DESIGN] pull-up
for r1 in e96(3)[::2]:
    for r2 in [x for x in e96(3) + e96(4) if 1.6 * r1 <= x <= 2.6 * r1][::2]:
        for r3 in [x for x in e96(4) + e96(5) if 1.6 * r2 <= x <= 2.6 * r2][::2]:
            for r0 in [x for x in e96(4) + e96(5) if 1.6 * r3 <= x <= 2.6 * r3][::2]:
                g, s = gap(codes(RT, r0, r1, r2, r3))
                if best is None or g > best[0]:
                    best = (g, (r0, r1, r2, r3), s)
g, (R0, R1, R2, R3), table = best
th = []
for a, b in zip(table, table[1:]):
    th.append(0.5 * (a['hi'] + b['lo']))
ladder = {'R_top_ohm': RT, 'R0_eol_ohm': R0, 'R1_mv_open_ohm': R1, 'R2_mv_closed_ohm': R2, 'R3_pmid_ohm': R3, 'tolerance': TOL,
          'adc_error_ratio': ADC_ERR, 'min_window_gap_ratio': g,
          'codes_sorted': [{'open_sw': d['bits'][0], 'closed_sw': d['bits'][1], 'pmid_hi': d['bits'][2], 'valid': d['bits'][3],
                            'ratio_nom': round(d['nom'], 5), 'ratio_lo': round(d['lo'], 5), 'ratio_hi': round(d['hi'], 5)} for d in table],
          'thresholds_ratio': [round(x, 5) for x in th], 'short_below_ratio': 0.02,
          'tag': 'DESIGN (values) / DERIVED (windows: 1 % resistors worst case + ADC 0.4 % FS ASSUMED + 2N7002 R_on 7.5 ohm DATASHEET)'}
assert g > 0.0, 'ladder windows overlap'

# header for the firmware (sensor_scale mvLadderDecode)
hdr = ['// GENERATED by calc/hbleed_provision_v1.py (v1, 2026-10-13) - do not edit. MV switch + P_mid ladder on Teensy pin 23 (A9):',
       '// ratio = V_pin / V_ref (pull-up on the ADC reference, ratiometric). Codes sorted by ratio; a reading in window k decodes to',
       '// kLadderBits[k] (b0 MV OPEN switch, b1 MV CLOSED switch, b2 P_mid high, b3 valid). Below kLadderShortRatio = short to GND (invalid).',
       '// R_top %.0f, R0 (EOL at the MV connector) %.0f, R1 (OPEN) %.0f, R2 (CLOSED) %.0f, R3 (P_mid FET) %.0f ohm; min window gap %.4f.' % (RT, R0, R1, R2, R3, g),
       '#pragma once', '#include <cstdint>', 'namespace ecu {', 'namespace ladder {',
       'constexpr int kLadderN = %d;' % len(table),
       'constexpr float kLadderShortRatio = 0.02f;',
       'constexpr float kLadderThr[kLadderN - 1] = {%s};' % ', '.join('%.5ff' % x for x in th),
       'constexpr uint8_t kLadderBits[kLadderN] = {%s};' % ', '.join(str(d['bits'][0] | d['bits'][1] << 1 | d['bits'][2] << 2 | d['bits'][3] << 3) for d in table),
       'constexpr float kLadderNom[kLadderN] = {%s};   // nominal ratios (tests)' % ', '.join('%.5ff' % d['nom'] for d in table),
       '}  // namespace ladder', '}  // namespace ecu', '']
open(os.path.join(ROOT, 'firmware', 'src', 'core', 'mv_ladder_table.h'), 'w').write('\n'.join(hdr))

# ------------------------------------------------------------------ (2) P_mid comparator
FS = 170e5          # [DATASHEET-class] TE M3234 range code 170BG, 0-170 bar g (range-code availability TO-VERIFY at quote)
P_HI, P_LO = 10e5, 9e5   # [DESIGN] firmware kHbleedPmidHi / release (config.h)
VEXC = 5.0          # +5V_SNS (ratiometric: the reference divider is on the same rail)
vs = lambda p: VEXC * (0.1 + 0.8 * p / FS)
RIN, RF, VPU = 4.75e3, 1.0e6, 5.0     # [DESIGN] input resistor, feedback, output pull-up to +5V_SNS (non-inverting with hysteresis)
vr_need = vs(P_HI) * RF / (RIN + RF)
best_r = None
for rb in e96(3):
    for rt in e96(3) + e96(4):
        v = VEXC * rb / (rb + rt)
        if best_r is None or abs(v - vr_need) < abs(best_r[2] - vr_need):
            best_r = (rt, rb, v)
rt_ref, rb_ref, vref = best_r
v_rise = vref * (RIN + RF) / RF
v_fall = (vref * (RIN + RF) - VPU * RIN) / RF
p_of = lambda v: (v / VEXC - 0.1) / 0.8 * FS
comp = {'transducer': 'TE M3234-000005-170BG class (0.5-4.5 V ratiometric on +5V_SNS)', 'p_rise_target_Pa_g': P_HI, 'p_fall_target_Pa_g': P_LO,
        'R_in_ohm': RIN, 'R_f_ohm': RF, 'pullup_V': VPU, 'ref_divider_top_ohm': rt_ref, 'ref_divider_bot_ohm': rb_ref, 'V_ref': vref,
        'p_rise_Pa_g': p_of(v_rise), 'p_fall_Pa_g': p_of(v_fall), 'hysteresis_Pa': p_of(v_rise) - p_of(v_fall),
        'transducer_TEB_Pa': 2.55e5, 'note': 'thresholds +/- TEB 2.55 bar: still far from both states (vented ~0 bar g, feed 40-55 bar g)',
        'tag': 'DESIGN / DERIVED; TEB from config.h (170BG class)'}

# ------------------------------------------------------------------ (3) vent time after V1 closes (V2 open, orifice downstream of V2)
V_MID = 0.5e-6          # [ICD requirement on Mechanical] mid volume <= 0.5 cm3
RHO_L = 780.0           # [LITERATURE] sat. liquid N2O density near 287 K, kg/m3 (approx.)
MDOT_LIQ_1MM = 31.3e-3  # [SIM, S12 v2.9] liquid bleed flow at 1.0 mm (in-burn stuck-open case), kg/s
R_N2O, GAM, T = 188.9, 1.27, 287.0
d, CD = 1.0e-3, 0.70    # [MECH >= 0.8-1.0 mm] / [ASSUMED]
A = math.pi / 4 * d * d
t_liq = RHO_L * V_MID / MDOT_LIQ_1MM
cstar = math.sqrt(GAM * R_N2O * T) * (2 / (GAM + 1)) ** ((GAM + 1) / (2 * (GAM - 1)))
tau_v = V_MID / (CD * A * cstar)            # ideal-gas choked blowdown time constant
t_vap = tau_v * math.log(45.0 / 10.0)       # 45 bar -> 9 bar g (abs ~10 bar)
CLOSE_DS = (0.050, 0.080)                   # [DATASHEET 6027 DC closing 50-80 ms at 6 bar] (WebFetch summary; TO-VERIFY at 45 bar N2O)
CONF_N = 5e-3                               # kHbleedConfirmN ticks
LIMIT = 0.15                                # kHbleedCloseConfirm_s
t_conf = [c + t_liq + t_vap + CONF_N for c in CLOSE_DS]
vent = {'V_mid_m3': V_MID, 't_liquid_expulsion_s': t_liq, 'tau_vapour_blowdown_s': tau_v, 't_vapour_45_to_10bar_s': t_vap,
        'valve_close_s_datasheet': CLOSE_DS, 'E0_to_confirm_s': t_conf, 'limit_s': LIMIT, 'margin_s': [LIMIT - x for x in t_conf],
        'note': 'ideal-gas blowdown; real-gas, flashing cooling and the transducer port dead volume TO-VERIFY on B-BLEED-1',
        'tag': 'DERIVED (LITERATURE density, SIM flow, ASSUMED Cd, DATASHEET valve time)'}

# ------------------------------------------------------------------ (4) coil drive
coil = {'valve': 'Burkert 6027 HP (stainless, G1/4, PEEK/FKM seat, NC, orifice 1.0 mm: 0-250 bar DC air/water) - DATASHEET via WebFetch summary',
        'coil_42K_DC_W_cold_warm': [16.0, 21.0], 'coil_note': 'column mapping of the coil table ambiguous in the summary: TO-VERIFY on the PDF',
        'coil_voltages_listed': '24 V DC, 230 V AC on the product page; 12 V DC TO-VERIFY (the ECU valve rail is +12V_ARM)',
        'kick_and_drop_option': 'exists (DATASHEET mentions Kick-and-Drop coils, max ambient 70 C); holding power TO-VERIFY',
        'purge_current_12V_two_valves_A': 2 * 16.0 / 12.0, 'purge_energy_J_2p6s_two_valves': 2 * 16.0 * 2.6,
        'medium_T_HP_PEEK_FKM_C': [-10, 80], 'switching_DC_ms': {'open': [20, 30], 'close': [50, 80]}, 'mass': 'not stated: TO-VERIFY',
        'open_issue': 'coil voltage vs +12V_ARM and the +2.7 A purge load on the ARM rail budget; alternative HP valves with low-power coils TO-QUOTE'}

# ------------------------------------------------------------------ (5) visibility through P_feed (restated, config.h)
vis = {'pfeed_change_at_20g_s_bar': 0.016, 'xdcr_TEB_bar': 2.55, 'conclusion': 'invisible on P_feed and Pc; only P_mid shows the bleed'}

out = {'id': 'hbleed_provision_v1', 'version': 'v1', 'date': '2026-10-13', 'owner': 'electronics', 'script': 'calc/hbleed_provision_v1.py',
       'ladder': ladder, 'pmid_comparator': comp, 'vent_time': vent, 'coil': coil, 'visibility': vis}
json.dump(out, open(os.path.join(ROOT, 'results', 'hbleed_provision_v1.json'), 'w'), indent=1)
txt = ['hbleed_provision_v1 (2026-10-13)',
       'ladder: Rtop %.0f R0 %.0f R1 %.0f R2 %.0f R3 %.0f ohm, min window gap %.4f (ratio)' % (RT, R0, R1, R2, R3, g)]
for dd in ladder['codes_sorted']:
    txt.append('  open %d closed %d pmid %d valid %d: ratio %.4f [%.4f, %.4f]' % (dd['open_sw'], dd['closed_sw'], dd['pmid_hi'], dd['valid'], dd['ratio_nom'], dd['ratio_lo'], dd['ratio_hi']))
txt.append('comparator: ref %.0f/%.0f -> %.4f V; rise %.2f bar g, fall %.2f bar g (hyst %.2f bar)' % (rt_ref, rb_ref, vref, comp['p_rise_Pa_g'] / 1e5, comp['p_fall_Pa_g'] / 1e5, comp['hysteresis_Pa'] / 1e5))
txt.append('vent: liquid %.1f ms + vapour %.1f ms; E0->confirm %.0f-%.0f ms vs %.0f ms (margin %.0f-%.0f ms)' % (t_liq * 1e3, t_vap * 1e3, t_conf[0] * 1e3, t_conf[1] * 1e3, LIMIT * 1e3, (LIMIT - t_conf[1]) * 1e3, (LIMIT - t_conf[0]) * 1e3))
txt.append('coil: 2 x 16 W (cold, 42 K coil, TO-VERIFY) -> %.2f A at 12 V, %.0f J per purge; 12 V coil availability TO-VERIFY' % (coil['purge_current_12V_two_valves_A'], coil['purge_energy_J_2p6s_two_valves']))
open(os.path.join(ROOT, 'results', 'hbleed_provision_v1.txt'), 'w').write('\n'.join(txt) + '\n')
print('\n'.join(txt))
