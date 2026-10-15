"""Chamber over-pressure (OVP) thresholds and Pc transducer range check. ARGOS H1 engine ECU, 06-electronics.

v1 2026-10-12. Lead decision 2026-10-12: chamber MEOP 45 bar; pintle full-stroke failure 32-44 bar; blocked nozzle up to
~63 bar at 30 C (tank pressure); normal command cap Pc <= 25 bar; ECU over-pressure abort at about 30 bar, firmware AND
hardware. This script:
  A. checks that the Pc transducer covers the failure cases without saturating (v1 0-500 psig vs v2.1 0-1000 psig),
  B. computes the hardware trip point from the schematic values (reads hardware/kicad_gen/ecu_design.py, the single
     source of the KiCad project) with a worst-case tolerance band,
  C. states the firmware threshold (src/core/config.h) for comparison.
Tags: DATASHEET (document), LEAD (lead decision), DESIGN (Electronics choice), DERIVED (computed here), ASSUMED.
Usage: python3 ovp_threshold_v1.py [--out ../results/ovp_threshold_v1.json]
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

PSI = 6894.757                       # Pa per psi (exact definition 0.45359237 kgf / in2)
BAR = 1e5
P_AMB = 101325.0                     # Pa, pad ambient (sea level); ACEMA site altitude shifts this by < 0.1 bar
V_EXC = 5.0                          # V, +5V_SNS nominal (LT1761-5); thresholds are ratiometric, so it cancels


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
    v = part(ref)['value']
    m = re.search(r'([0-9.]+)%', v)
    return float(m.group(1)) / 100 if m else 0.01


def v_sig(p_g, fs):
    """M3200 ratiometric output (code 3): 10 % .. 90 % of the supply over 0 .. FS [DATASHEET TE M3200 08/2018]."""
    return V_EXC * (0.1 + 0.8 * p_g / fs)


def p_of_vsig(v, fs):
    return (v / V_EXC - 0.1) / 0.8 * fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'ovp_threshold_v1.json'))
    a = ap.parse_args()
    L = []
    out = {'script': 'calc/ovp_threshold_v1.py v1', 'date': '2026-10-12',
           'inputs': {
               'chamber_MEOP_Pa': tag(45e5, 'LEAD 2026-10-12 (was 31 bar, combustion.json v1)'),
               'pintle_full_stroke_failure_Pa': tag([32e5, 44e5], 'LEAD 2026-10-12 quoting Combustion v2 failure analysis'),
               'blocked_nozzle_bound_Pa': tag(63e5, 'LEAD 2026-10-12: ~tank pressure at 30 C'),
               'chamber_proof_Pa': tag(67.5e5, 'LEAD changelog 2026-10-12: 1.5 x MEOP'),
               'normal_command_cap_Pa': tag(25e5, 'LEAD'),
               'firmware_ovp_abs_Pa': tag(30e5, 'LEAD "about 30 bar"; DESIGN 30.0 bar abs, 3 ms persistence (config.h)'),
           }}
    # ------------------------------------------------------------------ A. transducer range
    fs_old, fs_new = 500 * PSI, 1000 * PSI
    L.append('A. Pc transducer range (TE M3200 ratiometric 0.5-4.5 V at 5 V; firmware sensor-fault window 0.25-4.75 V)')
    rows = []
    for name, p in [('normal max (cap)', 25e5), ('firmware OVP', 30e5 - P_AMB), ('pintle failure low', 32e5 - P_AMB),
                    ('pintle failure high', 44e5 - P_AMB), ('MEOP', 45e5 - P_AMB), ('blocked nozzle 30 C', 63e5 - P_AMB),
                    ('chamber proof', 67.5e5 - P_AMB)]:
        r = {'case': name, 'p_gauge_bar': round(p / BAR, 2)}
        for lab, fs in (('v1_0_500psig', fs_old), ('v2_0_1000psig', fs_new)):
            v = v_sig(p, fs)
            r[lab + '_V'] = round(v, 3)
            r[lab + '_status'] = 'in range' if v <= 4.5 + 1e-9 else ('above FS, output not specified; > 4.75 V = sensor fault' if v > 4.75 else 'above FS')
        rows.append(r)
        L.append('  %-22s %6.2f bar g   0-500 psig: %5.2f V %-8s   0-1000 psig: %5.3f V %s' % (
            name, p / BAR, r['v1_0_500psig_V'], 'SATURATES' if r['v1_0_500psig_V'] > 4.5 else 'ok', r['v2_0_1000psig_V'],
            'ok' if r['v2_0_1000psig_V'] <= 4.5 else 'ABOVE FS'))
    adc_ratio = ohms('R611') / (ohms('R610') + ohms('R611'))
    out['A_transducer_range'] = {
        'selected': 'TE M3234-000005-01KPG (0-1000 psig = 0-68.95 bar gauge), same part as P_feed and P_tank',
        'fs_Pa': tag(round(fs_new, 1), 'DATASHEET TE M3200 range code 01KPG = 1000 psi'),
        'rows': rows,
        'proof_Pa': tag(round(2 * fs_new, 0), 'DATASHEET M3200 proof 2 x rated'),
        'burst_Pa': tag(round(5 * fs_new, 0), 'DATASHEET M3200 burst 5 x rated'),
        'sensor_fault_high_equiv_Pa_g': tag(round(p_of_vsig(4.75, fs_new), 0), 'DERIVED from the 4.75 V firmware fault limit'),
        'adc_divider_ratio': tag(round(adc_ratio, 5), 'DERIVED R610/R611'),
        'adc_input_at_4V5_V': tag(round(4.5 * adc_ratio, 4), 'DERIVED; ADS131M04 FS +/-1.2 V at gain 1 (DATASHEET SBAS890)'),
        'sensitivity_V_per_bar': tag(round(V_EXC * 0.8 / (fs_new / BAR), 5), 'DERIVED (was %.5f V/bar with 0-500 psig)' % (V_EXC * 0.8 / (fs_old / BAR))),
        'teb_Pa': tag(round(0.015 * fs_new, 0), 'DATASHEET M3200 TEB 1.5 % FS (-20..85 C); common to firmware and hardware paths'),
    }
    L.append('  proof 2 x FS = %.1f bar, burst 5 x FS = %.0f bar (DATASHEET); the transducer can stay fitted for the 67.5 bar chamber proof.'
             % (2 * fs_new / BAR, 5 * fs_new / BAR))
    L.append('  4.75 V fault limit = %.1f bar g; ADC input at 4.5 V = %.3f V of 1.2 V FS.' % (p_of_vsig(4.75, fs_new) / BAR, 4.5 * adc_ratio))
    L.append('  Cost of the wider range: sensitivity halves (%.1f -> %.1f mV/bar); 2 %% of the deep-throttle Pc 4.36 bar = %.2f mV.'
             % (V_EXC * 0.8 / (fs_old / BAR) * 1e3, V_EXC * 0.8 / (fs_new / BAR) * 1e3, 0.02 * 4.36 * V_EXC * 0.8 / (fs_new / BAR) * 1e3))
    # ------------------------------------------------------------------ B. hardware trip
    Ra, Rb, Ca = ohms('R330'), ohms('R331'), farads('C330')
    Rc, Rd, Cr = ohms('R332'), ohms('R333'), farads('C331')
    k_tap = Rb / (Ra + Rb)
    k_ref = Rd / (Rc + Rd)
    rth_tap = Ra * Rb / (Ra + Rb)
    rth_ref = Rc * Rd / (Rc + Rd)
    v_ref = V_EXC * k_ref
    vsig_trip = v_ref / k_tap
    p_trip = p_of_vsig(vsig_trip, fs_new)
    sens_cmp = V_EXC * 0.8 / fs_new * k_tap              # V at the comparator input per Pa
    # worst-case error terms at the comparator input [V]
    vio = 9e-3                                            # DATASHEET SLCS136V Vio max -40..125 C at 5 V
    iib = 400e-9                                          # DATASHEET SLCS136V Iib max -40..125 C
    e_bias = iib * max(rth_tap, rth_ref)                  # DERIVED bound: one input at max bias, the other at 0
    t_res = max(tol(x) for x in ('R330', 'R331', 'R332', 'R333'))
    e_ktap = v_ref * 2 * t_res                            # ratio error <= 2 x tolerance (worst case, both resistors)
    e_kref = v_ref * 2 * t_res
    e_tot = vio + e_bias + e_ktap + e_kref
    dp = e_tot / sens_cmp
    teb = 0.015 * fs_new
    out['B_hardware_trip'] = {
        'circuit': 'PC_SIG -> R330/R331 tap + C330 -> LMV331 IN-; +5V_SNS -> R332/R333 + C331 -> IN+; open-collector out (R334 to +3V3) -> '
                   'SN74LVC1G175 /CLR; Q = OVP_OK -> SN74LVC1G11 ARM AND + Teensy pin 29',
        'values': {'R330': Ra, 'R331': Rb, 'C330': Ca, 'R332': Rc, 'R333': Rd, 'C331': Cr, 'resistor_tol': t_res},
        'k_tap': tag(round(k_tap, 6), 'DERIVED'), 'k_ref': tag(round(k_ref, 6), 'DERIVED'),
        'v_ref_V': tag(round(v_ref, 5), 'DERIVED at +5V_SNS = 5.000 V (ratiometric: tracks the transducer supply)'),
        'pc_sig_trip_V': tag(round(vsig_trip, 4), 'DERIVED'),
        'trip_nominal_Pa_g': tag(round(p_trip, 0), 'DERIVED'),
        'trip_nominal_Pa_abs_sea_level': tag(round(p_trip + P_AMB, 0), 'DERIVED'),
        'error_terms_V': {'Vio': tag(vio, 'DATASHEET SLCS136V max -40..125 C'),
                          'bias': tag(round(e_bias, 5), 'DERIVED Iib 400 nA (SLCS136V) x max Rth'),
                          'tap_ratio': tag(round(e_ktap, 5), 'DERIVED 2 x %.2f %%' % (t_res * 100)),
                          'ref_ratio': tag(round(e_kref, 5), 'DERIVED 2 x %.2f %%' % (t_res * 100))},
        'band_circuit_Pa': tag(round(dp, 0), 'DERIVED worst-case linear sum of the circuit terms'),
        'band_with_transducer_Pa': tag(round(dp + teb, 0), 'DERIVED adds M3200 TEB 1.5 % FS (also shifts the firmware threshold)'),
        'trip_range_abs_Pa': tag([round(p_trip + P_AMB - dp, 0), round(p_trip + P_AMB + dp, 0)], 'DERIVED, circuit terms only'),
        'rc_tap_s': tag(round(rth_tap * Ca, 6), 'DERIVED'), 'rc_ref_s': tag(round(rth_ref * Cr, 6), 'DERIVED'),
        'comparator_input_max_V': tag(round(5.0 * k_tap, 3), 'DERIVED at PC_SIG = 5 V; VICR -0.1..4.2 V at 5 V (SLCS136V)'),
        'response_chain': 'comparator tPHL <= 1 us (SLCS136V) -> latch /CLR to Q <= 6.8 ns (SCES560G) -> AND <= 4.9 ns (SCES487I) -> '
                          'Q302 -> ARM switch turn-off ~6 ms (C301 Miller estimate, bench verify) -> MV holding magnet releases, '
                          'pintle servo unpowered (closing spring back-drives it)',
    }
    L.append('')
    L.append('B. Hardware trip (values read from hardware/kicad_gen/ecu_design.py)')
    L.append('  tap %.0f/%.0f (k %.5f, Rth %.1f k, tau %.2f ms); reference %.0f/%.0f from +5V_SNS (k %.5f, Rth %.1f k, tau %.2f ms)'
             % (Ra, Rb, k_tap, rth_tap / 1e3, rth_tap * Ca * 1e3, Rc, Rd, k_ref, rth_ref / 1e3, rth_ref * Cr * 1e3))
    L.append('  V_ref %.4f V -> PC_SIG %.4f V -> trip %.2f bar g = %.2f bar abs at sea level' % (v_ref, vsig_trip, p_trip / BAR, (p_trip + P_AMB) / BAR))
    L.append('  worst-case circuit band +/- %.2f bar (Vio %.1f mV, bias %.1f mV, ratios %.2f + %.2f mV at %.2f mV/bar) -> %.2f..%.2f bar abs'
             % (dp / BAR, vio * 1e3, e_bias * 1e3, e_ktap * 1e3, e_kref * 1e3, sens_cmp * BAR * 1e3, (p_trip + P_AMB - dp) / BAR, (p_trip + P_AMB + dp) / BAR))
    L.append('  plus transducer TEB +/- %.2f bar (common to both paths)' % (teb / BAR))
    # ------------------------------------------------------------------ C. comparison with firmware and limits
    fw = 30e5
    sep = p_trip + P_AMB - fw
    out['C_summary'] = {
        'firmware_trip_abs_Pa': tag(fw, 'DESIGN config.h kPcOverPressureAbs_Pa (LEAD ~30 bar)'),
        'hardware_minus_firmware_nominal_Pa': tag(round(sep, 0), 'DERIVED'),
        'hardware_never_below_firmware_in_band': tag(bool(sep - dp >= 0), 'DERIVED (circuit band; transducer error is common)'),
        'margin_hw_max_to_MEOP_Pa': tag(round(45e5 - (p_trip + P_AMB + dp), 0), 'DERIVED'),
        'margin_normal_max_to_fw_Pa': tag(round(fw - 26.64e5, 0), 'DERIVED: SIL S5 MC worst Pc 26.64 bar abs (v2.1 run, 300 cases)'),
    }
    L.append('')
    L.append('C. Firmware 30.00 bar abs; hardware nominal %.2f bar abs (+%.2f bar); hardware band low end %.2f bar abs (%s firmware); '
             'hardware band high end %.2f bar abs = %.1f bar below MEOP 45 bar' % ((p_trip + P_AMB) / BAR, sep / BAR, (p_trip + P_AMB - dp) / BAR,
                                                                                 '>=' if sep - dp >= 0 else '<', (p_trip + P_AMB + dp) / BAR,
                                                                                 (45e5 - p_trip - P_AMB - dp) / BAR))
    # SIL header: the hardware trip model in firmware/sil/sim.cpp uses these numbers (no hand copy)
    hdr = os.path.join(ROOT, 'firmware', 'sil', 'ovp_hw_params.h')
    open(hdr, 'w').write(
        '// GENERATED by calc/ovp_threshold_v1.py - DO NOT EDIT. Hardware chamber over-pressure trip (U330 LMV331 + U331 latch)\n'
        '// as drawn in hardware/kicad_gen/ecu_design.py, for the SIL hardware model. Units SI.\n'
        '#pragma once\n'
        'namespace sil {\nnamespace ovp {\n'
        'constexpr double kPcFs_Pa = %.1f;       // [DATASHEET] TE M3234-000005-01KPG 0-1000 psig\n'
        'constexpr double kTripPa_g = %.1f;      // [DERIVED] nominal trip, gauge (%.2f bar abs at sea level)\n'
        'constexpr double kBandPa = %.1f;         // [DERIVED] worst-case circuit band +/- (Vio, Iib, 0.1 %% resistors)\n'
        'constexpr double kTau_s = %.6f;          // [DERIVED] tap RC (R330 || R331) x C330\n'
        '}  // namespace ovp\n}  // namespace sil\n' % (fs_new, p_trip, (p_trip + P_AMB) / BAR, dp, rth_tap * Ca))
    out['sil_header'] = 'firmware/sil/ovp_hw_params.h'
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, 'w'), indent=1)
    txt = os.path.splitext(a.out)[0] + '.txt'
    open(txt, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
