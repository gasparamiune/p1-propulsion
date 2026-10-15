#!/usr/bin/env python3
"""Pressure transducer ranges, ADC chain and the hardware chamber over-pressure trip. ARGOS H1 engine ECU, 06-electronics.

v2 2026-10-13 (supersedes calc/ovp_threshold_v1.py, archived in calc/archive/ with its results kept as evidence).
  - OI-6 closure (lead, 2026-10-12): Pc transducer TE M3234-000005-070BG (0-70 bar g) instead of 01KPG (0-1000 psig = 68.95 bar g).
    The v1 script and the SIL header ovp_hw_params.h still carried the 01KPG full scale; this script regenerates the header.
  - v2.7 review fold-in: the torch chamber pressure P_torch (RC-01 flame gate) uses the same 070BG part on ADC2 CH0.
  - Feed and tank channels re-checked against the tank MEOP and the trapped-liquid relief (both read from combustion.json).
Sections: A. range per channel; B. ADC chain (the numbers firmware/src/core/sensor_scale.cpp implements); C. hardware trip from the
schematic values; D. firmware/hardware/limit comparison; E. generated SIL header.
Inputs read (no hand copies): ../../shared-fallback/engine/interfaces/combustion.json (or --engine-root), hardware/kicad_gen/
ecu_design.py, firmware/src/core/config.h. Tags: DATASHEET, LEAD (via combustion.json), DESIGN, DERIVED, ASSUMED, ESTIMATE.
Usage: python3 pc_transducer_v2.py [--engine-root DIR] [--out ../results/pc_transducer_v2.json]
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'hardware', 'kicad_gen'))
import ecu_design as D  # noqa: E402

BAR = 1e5
P_AMB = 101325.0                     # Pa, pad ambient (sea level)
V_EXC = 5.0                          # V, +5V_SNS nominal; the trip and the readings are ratiometric
M3200_DS = 'TE M3200 datasheet 08/2018, https://www.farnell.com/datasheets/3007269.pdf'
# [DATASHEET M3200] standard range codes (ordering table): bar codes 007B 017B 035B 070B 170B 350B 500B 700B; "Pressure Ranges between
# 100-10000psi (7-700bar) are all available" (a non-standard full scale, e.g. 100 bar, is a factory request - not assumed here)
RANGES = {'070BG': 70e5, '170BG': 170e5, '01KPG': 1000 * 6894.757}
TEB = 0.015                          # [DATASHEET] total error band 1.5 % FS over -20..85 C
BFSL = 0.0025                        # [DATASHEET] 0.25 % FS
PROOF_X, BURST_X = 2.0, 5.0          # [DATASHEET] proof 2 x rated, burst 5 x rated (<= 20 kpsi)


def tag(v, t, note=''):
    d = {'v': v, 'tag': t}
    if note:
        d['note'] = note
    return d


def part(ref):
    for _, _, _, fn in D.SHEETS:
        for _, parts in fn():
            for p in parts:
                if p['ref'] == ref:
                    return p
    raise KeyError(ref)


def ohms(ref):
    s = part(ref)['value'].split()[0]
    m = re.match(r'^([0-9.]+)([kM]?)$', s)
    return float(m.group(1)) * {'': 1.0, 'k': 1e3, 'M': 1e6}[m.group(2)]


def farads(ref):
    s = part(ref)['value'].split('/')[0]
    m = re.match(r'^([0-9.]+)([pnu])F$', s)
    return float(m.group(1)) * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6}[m.group(2)]


def tol(ref):
    m = re.search(r'([0-9.]+)%', part(ref)['value'])
    return float(m.group(1)) / 100 if m else 0.01


def cfg_const(text, name):
    m = re.search(r'constexpr\s+(?:float|double|int)\s+' + name + r'\s*=\s*([-+0-9.eE]+)f?\s*;', text)
    if not m:
        raise KeyError(name)
    return float(m.group(1))


def jv(d, *path):
    for k in path:
        d = d[k]
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def v_sig(p_g, fs):
    """M3200 ratiometric output code 3: 10 % .. 90 % of the excitation over 0 .. FS [DATASHEET]."""
    return V_EXC * (0.1 + 0.8 * p_g / fs)


def p_of_vsig(v, fs):
    return (v / V_EXC - 0.1) / 0.8 * fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.path.join(ROOT, '..', 'shared-fallback', 'engine'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'pc_transducer_v2.json'))
    a = ap.parse_args()
    comb_fn = os.path.join(a.engine_root, 'interfaces', 'combustion.json')
    comb = json.load(open(comb_fn))
    cfg_txt = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h')).read()
    eng_txt = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'engine_params.h')).read()

    meop = jv(comb, 'decisions', 'chamber_MEOP_Pa')
    proof = jv(comb, 'decisions', 'proof_pressure_Pa')
    abort_lead = jv(comb, 'decisions', 'ecu_overpressure_abort_Pa')
    blocked = jv(comb, 'operating_points', 'pressure_limits', 'blocked_nozzle_bound_Pa')
    tank_meop = jv(comb, 'operating_points', 'tank_MEOP_Pa')
    relief_txt = jv(comb, 'valves_and_actuators', 'isolation_valve', 'trapped_liquid_relief')
    m = re.search(r'([0-9.]+)\s*MPa', relief_txt)
    relief = float(m.group(1)) * 1e6 if m else float('nan')
    fw_abort = cfg_const(eng_txt, 'kPcAbortAbs_Pa')
    cap = cfg_const(eng_txt, 'kPcNormalCapAbs_Pa')
    fs_fw = cfg_const(cfg_txt, 'kPcXdcrFs_Pa')
    tank_ovp = cfg_const(cfg_txt, 'kTankOverPressure_Pa')
    s_max = cfg_const(cfg_txt, 'kPcSensorMax_V')
    torch_lit = cfg_const(cfg_txt, 'kTorchLitAbs_Pa')
    L = []
    out = {'script': 'calc/pc_transducer_v2.py v2', 'date': '2026-10-13', 'supersedes': 'calc/archive/ovp_threshold_v1.py (01KPG full scale)',
           'inputs': {
               'chamber_MEOP_Pa': tag(meop, 'LEAD via combustion.json decisions'),
               'proof_Pa': tag(proof, 'LEAD via combustion.json decisions'),
               'ecu_abort_lead_Pa': tag(abort_lead, 'LEAD via combustion.json decisions (~30 bar)'),
               'blocked_nozzle_bound_Pa': tag(blocked, 'combustion.json (CoolProp Psat 30 C)'),
               'tank_MEOP_Pa': tag(tank_meop, 'combustion.json operating_points (LEAD v0)'),
               'trapped_liquid_relief_max_Pa': tag(relief, 'combustion.json isolation_valve: "%s"' % relief_txt),
               'firmware_abort_abs_Pa': tag(fw_abort, 'engine_params.h kPcAbortAbs_Pa (generated from combustion.json)'),
               'firmware_cmd_cap_abs_Pa': tag(cap, 'engine_params.h kPcNormalCapAbs_Pa (config.h kPcCmdCapAbs_Pa)'),
               'firmware_pc_fs_Pa': tag(fs_fw, 'config.h kPcXdcrFs_Pa'),
               'firmware_tank_overpressure_gauge_Pa': tag(tank_ovp, 'config.h kTankOverPressure_Pa'),
               'firmware_sensor_fault_high_V': tag(s_max, 'config.h kPcSensorMax_V'),
               'torch_lit_threshold_abs_Pa': tag(torch_lit, 'config.h kTorchLitAbs_Pa (ESTIMATE until IGN-1)'),
               'm3200': tag({'standard_bar_codes': ['007B', '017B', '035B', '070B', '170B', '350B', '500B', '700B'], 'TEB_pct_FS': TEB * 100,
                             'BFSL_pct_FS': BFSL * 100, 'proof_x': PROOF_X, 'burst_x': BURST_X}, 'DATASHEET ' + M3200_DS),
           }}
    assert abs(fs_fw - RANGES['070BG']) < 1.0, 'config.h kPcXdcrFs_Pa is not the 070BG full scale'

    # ------------------------------------------------------------------ A. ranges
    L.append('A. Transducer range per channel (M3200 0.5-4.5 V on +5V_SNS; firmware fault window 0.25-%.2f V)' % s_max)
    chans = [
        ('PC (J601)', '070BG', [('normal command cap', cap - P_AMB), ('firmware abort', fw_abort - P_AMB), ('MEOP', meop - P_AMB),
                                ('blocked nozzle 30 C', blocked - P_AMB), ('proof (hydro test, if fitted)', proof - P_AMB)]),
        ('P_TORCH (J610, v2.7)', '070BG', [('lit threshold %.1f bar abs' % (torch_lit / BAR), torch_lit - P_AMB),
                                           ('chamber MEOP via the torch port', meop - P_AMB), ('proof', proof - P_AMB)]),
        ('P_FEED (J602)', '070BG', [('tank MEOP', tank_meop - P_AMB), ('trapped-liquid relief max', relief - P_AMB)]),
        ('P_FEED (J602) option', '170BG', [('tank MEOP', tank_meop - P_AMB), ('trapped-liquid relief max', relief - P_AMB)]),
        ('P_TANK (J603)', '070BG', [('firmware tank over-pressure', tank_ovp), ('tank MEOP', tank_meop - P_AMB), ('relief max', relief - P_AMB)]),
        ('P_TANK (J603) option', '170BG', [('firmware tank over-pressure', tank_ovp), ('tank MEOP', tank_meop - P_AMB), ('relief max', relief - P_AMB)]),
    ]
    rows = []
    for ch, code, cases in chans:
        fs = RANGES[code]
        for name, p in cases:
            v = v_sig(p, fs)
            st = 'in range' if v <= 4.5 + 1e-9 else ('ABOVE FS: output not specified, > %.2f V = sensor fault' % s_max if v > s_max else 'ABOVE FS: output not specified')
            rows.append({'channel': ch, 'code': code, 'case': name, 'p_gauge_bar': round(p / BAR, 2), 'v_sig_V': round(v, 3), 'status': st,
                         'teb_bar': round(TEB * fs / BAR, 2)})
            L.append('  %-22s %-6s %-34s %6.2f bar g -> %5.3f V  %s' % (ch, code, name, p / BAR, v, st))
    out['A_ranges'] = {'rows': rows,
                       'decision': tag({'PC': 'M3234-000005-070BG', 'P_TORCH': 'M3234-000005-070BG',
                                        'P_FEED': 'M3234-000005-170BG', 'P_TANK': 'M3234-000005-170BG'},
                                       'DESIGN v2.7: the 070BG reaches its full scale at the tank MEOP (70 bar g) and the trapped-liquid relief '
                                       '(<= 75 bar) lies above it (output not specified there); the standard 170B code covers both with proof '
                                       '340 bar. Cost: TEB 2.55 bar instead of 1.05 bar on the two feed-side channels (ratio checks and the 65 bar '
                                       'tank threshold tolerate it). Combustion/lead to confirm the relief-cycle monitoring need (RC-04)'),
                       'sensitivity_mV_per_bar': {k: tag(round(V_EXC * 0.8 / (fs / BAR) * 1e3, 3), 'DERIVED') for k, fs in RANGES.items()}}
    L.append('  -> DESIGN v2.7: Pc and P_torch 070BG; P_feed and P_tank 170BG (tank MEOP at FS and relief above FS with 070BG).')

    # ------------------------------------------------------------------ B. ADC chain (sensor_scale.cpp)
    r_top, r_bot = ohms('R610'), ohms('R611')
    zin = cfg_const(cfg_txt, 'kAdcZin_ohm')
    vref = cfg_const(cfg_txt, 'kAdcVref_V')
    code_fs = cfg_const(cfg_txt, 'kAdcCodeFs')
    assert abs(r_top - cfg_const(cfg_txt, 'kXdcrDivRtop_ohm')) < 1 and abs(r_bot - cfg_const(cfg_txt, 'kXdcrDivRbot_ohm')) < 1, \
        'config.h divider constants differ from the schematic'
    rb_eff = r_bot * zin / (r_bot + zin)
    k_div = rb_eff / (r_top + rb_eff)
    lsb_v = vref / code_fs
    chain = {}
    for code, fs in RANGES.items():
        pa_per_count = lsb_v / k_div / (V_EXC * 0.8) * fs
        chain[code] = {'pa_per_count': tag(round(pa_per_count, 4), 'DERIVED'),
                       'adc_at_4p5V_V': tag(round(4.5 * k_div, 4), 'DERIVED (ADC FS 1.2 V)'),
                       'adc_at_fault_high_V': tag(round(s_max * k_div, 4), 'DERIVED')}
    out['B_adc_chain'] = {'k_div_loaded': tag(round(k_div, 6), 'DERIVED R610/R611 loaded by Zin %.0f k (config.h; datasheet conflict kept there)' % (zin / 1e3)),
                          'lsb_V': tag(lsb_v, 'DATASHEET ADS131M04 gain 1'), 'per_range': chain,
                          'torch_threshold_v_sig_V': tag(round(v_sig(torch_lit - P_AMB, RANGES['070BG']), 4),
                                                         'DERIVED: 2.0 bar abs on the 070BG = 0.99 bar g -> %.1f mV above zero' % (V_EXC * 0.8 * (torch_lit - P_AMB) / RANGES['070BG'] * 1e3)),
                          'torch_threshold_vs_teb': tag(round((torch_lit - P_AMB) / (TEB * RANGES['070BG']), 3),
                                                        'DERIVED: the 0.99 bar g threshold is only %.2f x the 070BG TEB (1.05 bar): the ARMED auto-zero must '
                                                        'also zero P_torch (HAL, same as Pc) and IGN-1 sets the threshold (ESTIMATE until then)'
                                                        % ((torch_lit - P_AMB) / (TEB * RANGES['070BG'])))}
    L.append('')
    L.append('B. ADC chain: divider %.1fk/%.2fk loaded by %.0f k -> k %.5f; LSB %.3g V; Pa/count: %s' % (
        r_top / 1e3, r_bot / 1e3, zin / 1e3, k_div, lsb_v, ', '.join('%s %.3f' % (c, chain[c]['pa_per_count']['v']) for c in chain)))
    L.append('  torch threshold %.1f bar abs = %.2f bar g = %.0f mV above zero on the 070BG; TEB 1.05 bar -> auto-zero of P_torch required '
             '(ratio %.2f)' % (torch_lit / BAR, (torch_lit - P_AMB) / BAR, V_EXC * 0.8 * (torch_lit - P_AMB) / RANGES['070BG'] * 1e3,
                               out['B_adc_chain']['torch_threshold_vs_teb']['v']))

    # ------------------------------------------------------------------ C. hardware trip (070BG)
    fs = RANGES['070BG']
    Ra, Rb, Ca = ohms('R330'), ohms('R331'), farads('C330')
    Rc, Rd, Cr = ohms('R332'), ohms('R333'), farads('C331')
    k_tap, k_ref = Rb / (Ra + Rb), Rd / (Rc + Rd)
    rth_tap, rth_ref = Ra * Rb / (Ra + Rb), Rc * Rd / (Rc + Rd)
    v_ref = V_EXC * k_ref
    vsig_trip = v_ref / k_tap
    p_trip = p_of_vsig(vsig_trip, fs)
    sens_cmp = V_EXC * 0.8 / fs * k_tap
    vio, iib = 9e-3, 400e-9                               # DATASHEET SLCS136V (LMV331) max -40..125 C at 5 V
    e_bias = iib * max(rth_tap, rth_ref)
    t_res = max(tol(x) for x in ('R330', 'R331', 'R332', 'R333'))
    e_ktap = v_ref * 2 * t_res
    e_kref = v_ref * 2 * t_res
    dp = (vio + e_bias + e_ktap + e_kref) / sens_cmp
    teb = TEB * fs
    out['C_hardware_trip'] = {
        'transducer': 'M3234-000005-070BG (OI-6)',
        'values': {'R330': Ra, 'R331': Rb, 'C330': Ca, 'R332': Rc, 'R333': Rd, 'C331': Cr, 'resistor_tol': t_res},
        'pc_sig_trip_V': tag(round(vsig_trip, 4), 'DERIVED (unchanged by the range: a fixed PC_SIG voltage)'),
        'trip_nominal_Pa_g': tag(round(p_trip, 1), 'DERIVED'),
        'trip_nominal_Pa_abs_sea_level': tag(round(p_trip + P_AMB, 0), 'DERIVED'),
        'band_circuit_Pa': tag(round(dp, 1), 'DERIVED worst-case linear sum (Vio, Iib, 0.1 % ratios)'),
        'band_with_transducer_Pa': tag(round(dp + teb, 0), 'DERIVED + M3200 TEB 1.5 % FS (common to the firmware path)'),
        'trip_range_abs_Pa': tag([round(p_trip + P_AMB - dp, 0), round(p_trip + P_AMB + dp, 0)], 'DERIVED, circuit terms'),
        'rc_tap_s': tag(round(rth_tap * Ca, 6), 'DERIVED'),
        'v1_01KPG_trip_abs_Pa': tag(round(p_of_vsig(vsig_trip, RANGES['01KPG']) + P_AMB, 0), 'DERIVED v1 basis (superseded)'),
    }
    L.append('')
    L.append('C. Hardware trip (070BG): PC_SIG %.4f V -> %.2f bar g = %.2f bar abs; circuit band +/- %.2f bar -> %.2f..%.2f bar abs '
             '(01KPG basis was %.2f bar abs); + TEB +/- %.2f bar common' % (vsig_trip, p_trip / BAR, (p_trip + P_AMB) / BAR, dp / BAR,
                                                                         (p_trip + P_AMB - dp) / BAR, (p_trip + P_AMB + dp) / BAR,
                                                                         (p_of_vsig(vsig_trip, RANGES['01KPG']) + P_AMB) / BAR, teb / BAR))
    # ------------------------------------------------------------------ D. comparison
    sep = p_trip + P_AMB - fw_abort
    out['D_summary'] = {
        'hardware_minus_firmware_nominal_Pa': tag(round(sep, 0), 'DERIVED'),
        'hardware_low_end_above_firmware': tag(bool(sep - dp >= 0), 'DERIVED (circuit band; the transducer error is common to both)'),
        'margin_hw_high_end_to_MEOP_Pa': tag(round(meop - (p_trip + P_AMB + dp), 0), 'DERIVED'),
        'fault_high_equiv_Pa_g_070BG': tag(round(p_of_vsig(s_max, fs), 0), 'DERIVED'),
    }
    L.append('')
    L.append('D. firmware %.2f bar abs; hardware nominal %.2f bar abs (+%.2f), band low end %.2f (%s firmware), high end %.2f = %.2f bar '
             'below MEOP %.1f bar; 4.75 V fault = %.1f bar g' % (fw_abort / BAR, (p_trip + P_AMB) / BAR, sep / BAR, (p_trip + P_AMB - dp) / BAR,
                                                                 '>=' if sep - dp >= 0 else '<', (p_trip + P_AMB + dp) / BAR,
                                                                 (meop - p_trip - P_AMB - dp) / BAR, meop / BAR, p_of_vsig(s_max, fs) / BAR))
    # ------------------------------------------------------------------ E. SIL header
    hdr = os.path.join(ROOT, 'firmware', 'sil', 'ovp_hw_params.h')
    open(hdr, 'w').write(
        '// GENERATED by calc/pc_transducer_v2.py - DO NOT EDIT. Hardware chamber over-pressure trip (U330 LMV331 + U331 latch)\n'
        '// as drawn in hardware/kicad_gen/ecu_design.py, for the SIL hardware model. Units SI. v2 2026-10-13: 070BG full scale (OI-6);\n'
        '// v1 (calc/archive/ovp_threshold_v1.py) carried the 01KPG 68.95 bar g full scale.\n'
        '#pragma once\n'
        'namespace sil {\nnamespace ovp {\n'
        'constexpr double kPcFs_Pa = %.1f;       // [DATASHEET] TE M3234-000005-070BG 0-70 bar g\n'
        'constexpr double kTripPa_g = %.1f;      // [DERIVED] nominal trip, gauge (%.2f bar abs at sea level)\n'
        'constexpr double kBandPa = %.1f;         // [DERIVED] worst-case circuit band +/- (Vio, Iib, 0.1 %% resistors)\n'
        'constexpr double kTau_s = %.6f;          // [DERIVED] tap RC (R330 || R331) x C330\n'
        '}  // namespace ovp\n}  // namespace sil\n' % (fs, p_trip, (p_trip + P_AMB) / BAR, dp, rth_tap * Ca))
    out['sil_header'] = 'firmware/sil/ovp_hw_params.h'
    out['engine_root'] = os.path.relpath(a.engine_root, ROOT)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, 'w'), indent=1)
    open(os.path.splitext(a.out)[0] + '.txt', 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
