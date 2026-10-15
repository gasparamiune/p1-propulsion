#!/usr/bin/env python3
"""Values of the blocks added in the ECU schematic v2.3. ARGOS H1 engine ECU, 06-electronics, v1 2026-10-13.

Reads the schematic source hardware/kicad_gen/ecu_design.py (part values are parsed from it, so the schematic and this
calculation cannot drift apart) and derives or checks:
  A. mode strap J620 levels, HAL thresholds and margins (1 % resistors, ratiometric to +3V3);
  B. TPS552882 pintle rail: output setpoint from FB, EN/UVLO thresholds, output current limit, boost right-half-plane zero,
     COMP network (datasheet Eq. 22, 24-26), crossover with the fitted E-series values, and losses of the EXTERNAL buck-leg
     MOSFETs that pintle_rail_v1/v2 did not list;
  C. LTC4365 OV/UV disconnect thresholds and the OV filter (pintle_rail_ovtrip_v1 choice);
  D. ADC2 scalings: PRAIL/PREG dividers (loaded by the ADS131M04 input impedance), pintle current, P_torch;
  E. GSE heater interlock drive levels; F. CS decoder map and timing; G. regression of the v2.2 values that other scripts and
     the firmware read (pc_transducer_v2: R330-R333, R610/R611); H. +5V_SNS load with the fourth transducer.
Tags: DATASHEET (document named), LEAD, DESIGN (chosen here), DERIVED (computed here), ASSUMED (placeholder, range stated).
Every result is a calculation from datasheet or assumed values: nothing here is a measurement (bench B-PWR-1/2, B-PNT-1).
Usage: python3 ecu_v2p3_values_v1.py [--out ../results/ecu_v2p3_values_v1.json]
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'hardware', 'kicad_gen'))
import ecu_design as D  # noqa: E402

TPS_DS = 'TI TPS552882 datasheet (https://www.ti.com/lit/ds/symlink/tps552882.pdf, read with WebFetch 2026-10-12/13)'
LTC_DS = 'ADI LTC4365 datasheet Rev B (values as read for calc/pintle_rail_v3.py)'
CSD_DS = 'TI CSD17578Q5A datasheet SLPS526 (March 2015, WebFetch 2026-10-13)'
LVC138_DS = 'TI SN74LVC138A datasheet SCAS291W'
SBAS890 = 'TI ADS131M04 datasheet SBAS890 (D)'

# ------------------------------------------------------------------ datasheet / lead / assumed inputs (tagged)
TPS = {
    'VREF_V': ((1.188, 1.200, 1.212), 'DATASHEET ' + TPS_DS + ': FB reference over TJ -40..125 C'),
    'VSNS_V': ((0.048, 0.050, 0.052), 'DATASHEET: ISP-ISN current loop regulation voltage'),
    'VUVLO_V': ((1.20, 1.23, 1.26), 'DATASHEET: EN/UVLO rising threshold'),
    'VUVLO_HYS_V': ((0.008, 0.014, 0.020), 'DATASHEET: EN/UVLO threshold hysteresis'),
    'IUVLO_HYS_A': ((4.5e-6, 5.0e-6, 5.5e-6), 'DATASHEET: hysteresis current sourced out of EN/UVLO above the threshold'),
    'GEA_S': (190e-6, 'DATASHEET: error amplifier transconductance, typical only (no min/max printed)'),
    'RSENSE_eq_ohm': (0.055, 'DATASHEET: equivalent internal current-sense resistance used in Eq. 19-24'),
    'fsw_Hz': (400e3, 'DATASHEET: 49.9 kOhm FSW resistor = 400 kHz'),
    'VCC_V': ((5.0, 5.2, 5.4), 'DATASHEET: VCC at 50 mA (DR1L driver supply; DR1H from BOOT1)'),
    'gate_drive_A': ((1.0, 1.8), 'DATASHEET: gate drivers source 1 A / sink 1.8 A peak'),
    'eq_note': 'Eq. 22 f_RHPZ = R_LOAD (1-D)^2 / (2 pi L); Eq. 24 R_C = 2 pi V_OUT R_SENSE C_OUT f_C / ((1-D) V_REF G_EA); '
               'Eq. 25 C_C = R_LOAD C_OUT / (2 R_C); Eq. 26 C_P = R_COUT C_OUT / R_C (open below 10 pF). The PDF text extraction '
               'garbled the fraction bars: the forms above are re-typed and TO-VERIFY against the PDF; f_C <= min(f_SW/10, f_RHPZ/5)',
}
LTC = {
    'VOV_V': ((0.4925, 0.500, 0.5075), 'DATASHEET ' + LTC_DS + ': OV pin threshold, H grade -40..125 C'),
    'VUV_V': ((0.4925, 0.500, 0.5075), 'ASSUMED equal to the OV threshold (UV-pin row not re-read; analog.com blocked at the proxy) - TO-CONFIRM'),
    'gate_drive_at_VIN5_V': ((3.0, 3.6, 4.2), 'DATASHEET (pintle_rail_v3 record): gate drive above VOUT at VIN 5 V; value at 7.5 V not read'),
}
CSD = {
    'VDS_V': (30.0, 'DATASHEET ' + CSD_DS),
    'RDS_on_4V5_max_ohm': (9.3e-3, 'DATASHEET: max at VGS 4.5 V, ID 10 A, 25 C'),
    'Qg_4V5_typ_C': (7.9e-9, 'DATASHEET'),
    'Qgd_typ_C': (2.0e-9, 'DATASHEET'),
    'RthJA_KpW': (50.0, 'DATASHEET: 1 in2 2 oz Cu pad (140 K/W on a minimum pad)'),
    'hot_factor': (1.5, 'ASSUMED RDS(on) at TJ ~125 C / 25 C (datasheet curve not read; typical NexFET class 1.4-1.6)'),
    't_sw_s': (10e-9, 'ASSUMED rise + fall per edge pair at 1 A / 1.8 A drive and Qgd 2 nC (order estimate; bench measures)'),
}
OP = {
    'VIN_V': ((6.0, 8.4), 'LEAD basis: 2S pack 6.0 (TVC-sag case) to 8.4 V full'),
    'VOUT_V': (7.49, 'LEAD 2026-10-13 adopted setpoint (pintle_rail_v3 divider B)'),
    'IOUT_limit_A': (4.333, 'DERIVED pintle_rail_v2: 52 mV / 12 mOhm (max of the output limit)'),
    'eta': (0.92, 'ASSUMED converter efficiency at 7.49 V out (pintle_rail_v2 open item: bench)'),
    'C_eff_F': (396e-6, 'DERIVED pintle_rail_v3: effective output capacitance with the second 220 uF polymer'),
    'ESR_pair_ohm': (7.0e-3, 'ASSUMED pintle_rail_ovtrip_v1 nominal ESR of the 2 x 220 uF polymer pair'),
    'L_H': (4.7e-6, 'DATASHEET application inductor 4.7 uH'),
    'f_c_target_Hz': (5.0e3, 'DESIGN pintle_rail_v3 crossover target (f_RHPZ/5 at 6.0 V in, 4.33 A)'),
    'I_stall_A': ((1.2, 1.7), 'DERIVED pintle_rail_v2/v3: HV69 stall current bound at 7.4 V (unmeasured, B-PNT-1)'),
}
ADC = {
    'Zin_ohm': (330e3, 'DATASHEET ' + SBAS890 + ' 8.3.3 at gain 1 (the electrical table says 300 kOhm: conflict kept, firmware config.h)'),
    'FS_V': (1.2, 'DATASHEET: +/-1.2 V at gain 1'),
    'abs_max_note': 'analog input absolute maximum AVDD + 0.3 V = 3.6 V: TO-CONFIRM on SBAS890 (not re-read this session)',
}
INA_GAIN = {'INA181A1IDBVR': 20.0, 'INA181A2IDBVR': 50.0, 'INA181A3IDBVR': 100.0, 'INA181A4IDBVR': 200.0}   # DATASHEET INA181 family
INA_SWING_V = (4.98, 'ASSUMED output swing to V+ - 20 mV at V+ = 5 V (INA181 datasheet row not re-read)')
XDCR_I_A = (5e-3, 'v2.2 design note "3 x 5 mA transducers" (TE M3200 supply current TO-CONFIRM)')
LT1761_I_A = (0.100, 'DATASHEET LT1761 class: 100 mA output (v2.2 spec field)')
DMN6075S = {'Vds_V': 60.0, 'Id_A': 2.0, 'Rds_4V5_ohm': 0.120, 'tag': 'DATASHEET Diodes DS37023 Rev6-2'}
TWO_N7002_VGS_TH_MAX_V = (2.5, 'DATASHEET 2N7002 class VGS(th) max (part datasheet not re-read)')
VBAT_V = (6.6, 8.4)
GSE_COIL_MAX = {'V': 28.0, 'A': 1.0, 'tag': 'DESIGN interface limit stated on J616 (GSE side to comply)'}
SMAJ33A_STANDOFF_V = (33.0, 'DATASHEET SMAJ series naming: reverse standoff 33 V (clamp voltage TO-CONFIRM)')


def num(s):
    """'28.0k 1%' -> 28000.0; '12m 1% 1W' -> 0.012; '12nF/50V C0G' -> 1.2e-8; '0R' -> 0."""
    t = s.split()[0].split('/')[0]
    if t.upper() in ('0R', '0'):
        return 0.0
    m = re.match(r'^([0-9.]+)\s*([pnumkM]?)(F|H|R)?$', t)
    if not m:
        raise ValueError('cannot parse value %r' % s)
    mult = {'': 1.0, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'M': 1e6}[m.group(2)]
    return float(m.group(1)) * mult


def tol(s, default=0.01):
    m = re.search(r'([0-9.]+)%', s)
    return float(m.group(1)) / 100 if m else default


PARTS = {}
for _name, _fn, _title, _builder in D.SHEETS:
    for _t, _parts in _builder():
        for _p in _parts:
            PARTS[_p['ref']] = dict(_p, sheet=_name)


def val(ref):
    return num(PARTS[ref]['value'])


def tv(v, t, note=''):
    d = {'v': v, 'tag': t}
    if note:
        d['note'] = note
    return d


def r3(x):
    return round(x, 4) if isinstance(x, float) else x


def divider_band(vref, rt_ref, rb_ref):
    rt, rb = val(rt_ref), val(rb_ref)
    tt, tb = tol(PARTS[rt_ref]['value']), tol(PARTS[rb_ref]['value'])
    nom = vref[1] * (1 + rt / rb)
    lo = vref[0] * (1 + rt * (1 - tt) / (rb * (1 + tb)))
    hi = vref[2] * (1 + rt * (1 + tt) / (rb * (1 - tb)))
    return lo, nom, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'ecu_v2p3_values_v1.json'))
    a = ap.parse_args()
    src = os.path.join(ROOT, 'hardware', 'kicad_gen', 'ecu_design.py')
    out = {'id': 'ecu_v2p3_values', 'version': 'v1', 'date': '2026-10-13', 'owner': 'electronics (06-electronics)',
           'tool': 'calc/ecu_v2p3_values_v1.py',
           'reads': {'ecu_design.py': hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16]},
           'status': 'DERIVED from datasheet, LEAD and ASSUMED inputs; not a measurement. Bench: B-PWR-1, B-PWR-2, B-PNT-1, B-ECU-1.'}
    L = ['ecu_v2p3_values_v1 (Electronics 2026-10-13): values of the ECU schematic v2.3 additions; reads ecu_design.py sha256/16 %s'
         % out['reads']['ecu_design.py']]
    fails = []

    # ------------------------------------------------------------------ A. mode strap
    vcc = 3.3
    ru, ra, rb = val('R694'), val('R695'), val('R696')
    t = tol(PARTS['R694']['value'])

    def strap(a_low, b_low, ru_, ra_, rb_):
        g = 1 / ru_
        gl = (1 / ra_ if a_low else 0) + (1 / rb_ if b_low else 0)
        return vcc * (1 / gl) / (1 / gl + ru_) if gl else vcc

    states = {'OPEN (INVALID)': (False, False), 'FLIGHT (B low)': (False, True), 'STAND (A low)': (True, False),
              'BOTH LOW (INVALID)': (True, True)}
    lev = {}
    for k, (al, bl) in states.items():
        vals = []
        for su in (1 - t, 1 + t):
            for sa in (1 - t, 1 + t):
                for sb in (1 - t, 1 + t):
                    vals.append(strap(al, bl, ru * su, ra * sa, rb * sb))
        lev[k] = (min(vals), strap(al, bl, ru, ra, rb), max(vals))
    order = ['OPEN (INVALID)', 'FLIGHT (B low)', 'STAND (A low)', 'BOTH LOW (INVALID)']
    thr = [(lev[order[i]][1] + lev[order[i + 1]][1]) / 2 for i in range(3)]
    margins = []
    for i in range(3):
        upper_lo = lev[order[i]][0]
        lower_hi = lev[order[i + 1]][2]
        margins.append(min(upper_lo - thr[i], thr[i] - lower_hi))
    out['mode_strap'] = {
        'levels_V_min_nom_max': {k: [r3(x) for x in v] for k, v in lev.items()},
        'hal_thresholds_V': tv([round(x, 3) for x in thr], 'DERIVED midpoints between adjacent nominal levels'),
        'worst_margin_to_threshold_V': tv(round(min(margins), 3), 'DERIVED 1 % resistors, ratiometric (supply cancels)'),
        'decode': 'V > %.2f: OPEN -> INVALID; %.2f < V <= %.2f: FLIGHT; %.2f < V <= %.2f: STAND; V <= %.2f: BOTH -> INVALID '
                  '(firmware strap:: codes 1 FLIGHT, 2 STAND, 0 INVALID)' % (thr[0], thr[1], thr[0], thr[2], thr[1], thr[2]),
        'adc_codes_12bit': {k: round(v[1] / vcc * 4095) for k, v in lev.items()},
    }
    L.append('A. mode strap (R694 %s / R695 %s / R696 %s, 1 %%): %s; thresholds %s V; worst margin %.3f V'
             % (PARTS['R694']['value'], PARTS['R695']['value'], PARTS['R696']['value'],
                ', '.join('%s %.3f V' % (k, v[1]) for k, v in lev.items()), ', '.join('%.3f' % x for x in thr), min(margins)))
    if min(margins) < 0.05:
        fails.append('mode strap margin below 50 mV')

    # ------------------------------------------------------------------ B. TPS552882
    vout = divider_band(TPS['VREF_V'][0], 'R808', 'R809')
    en_r = divider_band(TPS['VUVLO_V'][0], 'R804', 'R805')
    hys_i = [TPS['IUVLO_HYS_A'][0][i] * val('R804') for i in range(3)]
    hys_v = [TPS['VUVLO_HYS_V'][0][i] * (1 + val('R804') / val('R805')) for i in range(3)]
    en_fall = (en_r[0] - hys_i[2] - hys_v[2], en_r[1] - hys_i[1] - hys_v[1], en_r[2] - hys_i[0] - hys_v[0])
    rs = val('R807')
    ilim = [x / rs for x in TPS['VSNS_V'][0]]
    vin_min = OP['VIN_V'][0][0]
    vo = OP['VOUT_V'][0]
    io = OP['IOUT_limit_A'][0]
    d_boost = 1 - vin_min / vo
    rload = vo / io
    L_H = OP['L_H'][0]
    f_rhpz = rload * (1 - d_boost) ** 2 / (2 * math.pi * L_H)
    fc = OP['f_c_target_Hz'][0]
    cout = OP['C_eff_F'][0]
    gea, rse, vref = TPS['GEA_S'][0], TPS['RSENSE_eq_ohm'][0], TPS['VREF_V'][0][1]
    rc = 2 * math.pi * vo * rse * cout * fc / ((1 - d_boost) * vref * gea)
    cc = rload * cout / (2 * rc)
    cp = OP['ESR_pair_ohm'][0] * cout / rc
    rc_fit, cc_fit, cp_fit = val('R806'), val('C812'), val('C813')
    fc_fit_boost = rc_fit * (1 - d_boost) * vref * gea / (2 * math.pi * vo * rse * cout)
    fc_fit_buck = rc_fit * 1.0 * vref * gea / (2 * math.pi * vo * rse * cout)
    f_zero = 1 / (2 * math.pi * rc_fit * cc_fit)
    f_pole = 1 / (2 * math.pi * rc_fit * cp_fit)
    fc_lim = min(TPS['fsw_Hz'][0] / 10, f_rhpz / 5)
    out['tps552882'] = {
        'vout_V_min_nom_max_DC_divider_and_VREF_only': tv([round(x, 3) for x in vout], 'DERIVED (CDC/FB-leakage terms: pintle_rail_v3, static worst 7.62 V)'),
        'en_uvlo_rising_V': tv([round(x, 3) for x in en_r], 'DERIVED R804/R805 with VUVLO 1.20-1.26 V, 1 % resistors'),
        'en_uvlo_falling_V': tv([round(x, 3) for x in en_fall], 'DERIVED: rising - IUVLO_HYS x R804 - VUVLO_HYS x (1 + R804/R805)'),
        'iout_limit_A': tv([round(x, 3) for x in ilim], 'DERIVED VSNS 48-52 mV / R807'),
        'boost_worst': {'VIN_V': vin_min, 'D': round(d_boost, 4), 'R_LOAD_ohm': round(rload, 4),
                        'f_RHPZ_Hz': tv(round(f_rhpz), 'DERIVED Eq. 22 (pintle_rail_v3 37.6 kHz)'),
                        'f_c_limit_Hz': tv(round(fc_lim), 'DATASHEET rule min(f_SW/10, f_RHPZ/5)')},
        'comp_computed': {'R_C_ohm': tv(round(rc), 'DERIVED Eq. 24, f_C %.0f Hz, C_OUT %.0f uF, G_EA typ' % (fc, cout * 1e6)),
                          'C_C_F': tv(cc, 'DERIVED Eq. 25'), 'C_P_F': tv(cp, 'DERIVED Eq. 26 with %.1f mOhm ESR' % (OP['ESR_pair_ohm'][0] * 1e3))},
        'comp_fitted': {'R806_ohm': rc_fit, 'C812_F': cc_fit, 'C813_F': cp_fit,
                        'f_c_boost_6V0_Hz': tv(round(fc_fit_boost), 'DERIVED with the fitted R806 (G_EA typical: no min/max printed)'),
                        'f_c_buck_8V4_Hz': tv(round(fc_fit_buck), 'DERIVED (1-D) -> 1 in buck mode'),
                        'zero_Hz': round(f_zero), 'hf_pole_Hz': round(f_pole)},
        'verification': 'B-PWR-2 load step / Bode: phase margin >= 45 deg at 6.0 and 8.4 V in, 0.1-4.3 A (G_EA spread unknown)',
    }
    if fc_fit_boost > fc_lim:
        fails.append('crossover above the datasheet limit')
    # external buck-leg MOSFET losses (the pintle_rail_v1/v2 gap)
    rds = CSD['RDS_on_4V5_max_ohm'][0] * CSD['hot_factor'][0]
    pin_boost = vo * io / OP['eta'][0]
    iin_boost = pin_boost / vin_min
    p_hs_boost = iin_boost ** 2 * rds            # high-side buck FET on 100 % in boost mode
    vin_max = OP['VIN_V'][0][1]
    d_buck = vo / vin_max
    p_hs_buck = io ** 2 * d_buck * rds + 0.5 * vin_max * io * CSD['t_sw_s'][0] * TPS['fsw_Hz'][0]
    p_ls_buck = io ** 2 * (1 - d_buck) * rds
    p_q803 = io ** 2 * rds
    i_stall_hi = OP['I_stall_A'][0][1]
    p_hs_boost_stall = (vo * i_stall_hi / OP['eta'][0] / vin_min) ** 2 * rds
    p_r807 = io ** 2 * rs
    out['external_fets'] = {
        'finding': 'TPS552882 integrates only the boost-leg MOSFETs; the buck leg needs two external N-MOSFETs driven by DR1H/DR1L. '
                   'pintle_rail_v1/v2 listed neither the parts nor their losses (eta 0.92 ASSUMED covered the converter as if fully integrated).',
        'candidate': 'TI CSD17578Q5A (30 V, 9.3 mOhm max at 4.5 V, SON 5x6) for Q801/Q802 and the LTC4365 switch Q803',
        'P_Q801_boost_6V0_at_limit_W': tv(round(p_hs_boost, 3), 'DERIVED I_in %.2f A (eta %.2f ASSUMED), RDS x %.1f hot ASSUMED' % (iin_boost, OP['eta'][0], CSD['hot_factor'][0])),
        'P_Q801_boost_6V0_at_stall_W': tv(round(p_hs_boost_stall, 3), 'DERIVED at %.1f A HV69 stall bound' % i_stall_hi),
        'P_Q801_buck_8V4_at_limit_W': tv(round(p_hs_buck, 3), 'DERIVED conduction + switching (t_sw ASSUMED %.0f ns)' % (CSD['t_sw_s'][0] * 1e9)),
        'P_Q802_buck_8V4_at_limit_W': tv(round(p_ls_buck, 3), 'DERIVED conduction (dead-time body-diode loss not modelled)'),
        'P_Q803_at_limit_W': tv(round(p_q803, 3), 'DERIVED if fully enhanced (VGS >= 4.5 V); at the 3.0 V gate drive class RDS(on) is not printed: TO-CONFIRM'),
        'dT_junction_K_worst': tv(round(max(p_hs_boost, p_hs_buck) * CSD['RthJA_KpW'][0], 1), 'DERIVED with RthJA 50 K/W (1 in2 2 oz pad, DATASHEET)'),
        'P_R807_at_limit_W': tv(round(p_r807, 3), 'DERIVED: 2512 1 W part'),
        'duty_note': 'the 4.33 A limit is reached only in a fault or a jam; the HV69 stall bound is 1.2-1.7 A (DERIVED, unmeasured)',
    }
    L.append('B. TPS552882: VOUT %.3f/%.3f/%.3f V (DC, divider + VREF); EN rising %.2f/%.2f/%.2f V, falling %.2f V nom; I_limit %.2f-%.2f A; '
             'f_RHPZ %.0f Hz; COMP computed R_C %.0f ohm, C_C %.2f nF, C_P %.0f pF -> fitted %s / %s / %s: f_c %.0f Hz boost 6.0 V, %.0f Hz buck '
             '(limit %.0f Hz), zero %.0f Hz, pole %.0f kHz'
             % (vout[0], vout[1], vout[2], en_r[0], en_r[1], en_r[2], en_fall[1], ilim[0], ilim[2], f_rhpz, rc, cc * 1e9, cp * 1e12,
                PARTS['R806']['value'], PARTS['C812']['value'], PARTS['C813']['value'], fc_fit_boost, fc_fit_buck, fc_lim, f_zero,
                f_pole / 1e3))
    L.append('   external buck-leg FETs (gap in pintle_rail_v1/v2): Q801 %.2f W boost at the 4.33 A limit (%.2f W at the 1.7 A stall), '
             '%.2f W buck; Q802 %.3f W; Q803 %.2f W if enhanced; dT_j <= %.0f K at 50 K/W; R807 %.2f W'
             % (p_hs_boost, p_hs_boost_stall, p_hs_buck, p_ls_buck, p_q803, max(p_hs_boost, p_hs_buck) * 50, p_r807))

    # ------------------------------------------------------------------ C. LTC4365
    ov = divider_band(LTC['VOV_V'][0], 'R812', 'R813')
    uv = divider_band(LTC['VUV_V'][0], 'R814', 'R815')
    rth = val('R812') * val('R813') / (val('R812') + val('R813'))
    tau = rth * val('C814')
    out['ltc4365'] = {
        'ov_trip_V': tv([round(x, 3) for x in ov], 'DERIVED VOV and 0.1 % divider (pintle_rail_v3: 8.062/8.2/8.339 V without divider tolerance)'),
        'uv_trip_V': tv([round(x, 3) for x in uv], 'DERIVED with VUV ASSUMED = VOV (TO-CONFIRM) and 1 % divider; firmware PRAIL lost < 5.5 V'),
        'ov_filter_tau_s': tv(tau, 'DESIGN pintle_rail_ovtrip_v1 choice 10 us (1.0 nF at Rth %.2f kOhm)' % (rth / 1e3)),
        'fault_to_mv': 'LTC4365 /FAULT (open drain, R817 10k to +5V_ARM) = PRAIL_OK -> U306 AND -> MV holding magnet gate: an OV '
                       'or UV disconnect releases the MV latch in hardware; firmware sees PRAIL < 5.5 V on ADC2 CH1 (PINTLE_FAULT)',
        'not_covered': 'a regulator collapse below the LTC4365 operating minimum (2.5 V VIN) leaves /FAULT undriven (pulled high): the '
                       'firmware PRAIL path covers it',
    }
    L.append('C. LTC4365: OV %.3f/%.3f/%.3f V; UV %.2f/%.2f/%.2f V (VUV ASSUMED = VOV); OV filter tau %.2f us'
             % (ov[0], ov[1], ov[2], uv[0], uv[1], uv[2], tau * 1e6))
    if not (7.62 < ov[0]):
        fails.append('OV trip minimum below the 7.62 V static rail maximum')

    # ------------------------------------------------------------------ D. ADC2 scalings
    zin = ADC['Zin_ohm'][0]

    def ratio(rt_ref, rb_ref, loaded=True):
        rt, rb = val(rt_ref), val(rb_ref)
        rbe = rb * zin / (rb + zin) if loaded else rb
        return rbe / (rt + rbe)

    k_rail = ratio('R920', 'R921')
    k_rail_u = ratio('R920', 'R921', loaded=False)
    gain = INA_GAIN[PARTS['U803']['value']]
    k_i = gain * rs * ratio('R930', 'R931')
    out['adc2'] = {
        'PRAIL_PREG_divider': {'ratio_unloaded': tv(round(k_rail_u, 6), 'DERIVED R920/R921'),
                               'ratio_loaded': tv(round(k_rail, 6), 'DERIVED with Zin %.0f kOhm (%s)' % (zin / 1e3, ADC['Zin_ohm'][1])),
                               'FS_V': round(ADC['FS_V'][0] / k_rail, 3),
                               'at_7V49_V': round(7.49 * k_rail, 4),
                               'at_5V5_lost_threshold_V': round(5.5 * k_rail, 4),
                               'at_24V5_fail_high_pin_V': tv(round(24.5 * k_rail_u, 3), 'DERIVED; ' + ADC['abs_max_note'])},
        'IPINT': {'V_per_A_at_ADC': tv(round(k_i, 5), 'DERIVED INA181 gain %.0f x %.0f mOhm x divider (loaded)' % (gain, rs * 1e3)),
                  'FS_A': round(ADC['FS_V'][0] / k_i, 2),
                  'INA_output_limit_A': tv(round(INA_SWING_V[0] / (gain * rs), 2), INA_SWING_V[1]),
                  'stall_threshold_1A_V': round(1.0 * k_i, 4)},
        'P_TORCH': 'same transducer (070BG), divider (12.7k/4.02k) and filter as Pc: scaling in calc/pc_transducer_v2.py (its label '
                   '"J610" for P_torch is wrong: the connector is J901)',
        'sampling': 'ADC2 OSR 4096 -> 1 kSPS (DESIGN), read once per 1 ms tick; firmware kPrailLostTime_s 2 ms = 2 frames',
    }
    L.append('D. ADC2: PRAIL/PREG ratio %.5f loaded (%.5f unloaded): FS %.2f V, 7.49 V -> %.4f V, 5.5 V -> %.4f V, 24.5 V -> %.2f V at the pin; '
             'IPINT %.4f V/A, FS %.2f A, INA181 output limit %.2f A'
             % (k_rail, k_rail_u, ADC['FS_V'][0] / k_rail, 7.49 * k_rail, 5.5 * k_rail, 24.5 * k_rail_u, k_i, ADC['FS_V'][0] / k_i,
                INA_SWING_V[0] / (gain * rs)))
    if ADC['FS_V'][0] / k_i < OP['IOUT_limit_A'][0]:
        fails.append('IPINT full scale below the regulator current limit')

    # ------------------------------------------------------------------ E. heater interlock
    k_inh = val('R657') / (val('R656') + val('R657'))
    vgs_inh = [v * k_inh for v in VBAT_V]
    k_drv = val('R655') / (val('R654') + val('R655'))
    vgs_on = 5.0 * k_drv
    out['heater_interlock'] = {
        'inhibit_VGS_V_at_VBAT_6V6_8V4': tv([round(x, 2) for x in vgs_inh], 'DERIVED; 2N7002 VGS(th) <= %.1f V (%s)' % TWO_N7002_VGS_TH_MAX_V),
        'Q616_VGS_on_V': tv(round(vgs_on, 2), 'DERIVED U305 5 V output through R654/R655 (DMN6075S RDS(on) specified at 4.5 V)'),
        'Q616_P_at_1A_W': tv(round(GSE_COIL_MAX['A'] ** 2 * DMN6075S['Rds_4V5_ohm'], 3), 'DERIVED ' + DMN6075S['tag']),
        'gse_limits': tv('coil supply <= %.0f V DC, coil current <= %.1f A, flyback diode in the GSE' % (GSE_COIL_MAX['V'], GSE_COIL_MAX['A']),
                         GSE_COIL_MAX['tag']),
        'clamp': tv('SMAJ33A standoff %.0f V >= %.0f V GSE supply; clamp below the 60 V switch rating TO-CONFIRM' % (SMAJ33A_STANDOFF_V[0], GSE_COIL_MAX['V']),
                    SMAJ33A_STANDOFF_V[1]),
        'logic': 'closed = HTR_PERMIT_CMD (firmware: SAFE only, tank below the cut pressure) AND watchdog OK (U305 /OE) AND arming plug '
                 'out (Q617) AND ARM bus off (Q618); ECU unpowered = open',
    }
    L.append('E. heater interlock: inhibit VGS %.2f-%.2f V; Q616 VGS on %.2f V; Q616 %.3f W at 1 A'
             % (vgs_inh[0], vgs_inh[1], vgs_on, GSE_COIL_MAX['A'] ** 2 * DMN6075S['Rds_4V5_ohm']))
    if vgs_inh[0] < 2 * TWO_N7002_VGS_TH_MAX_V[0] * 0.8:
        fails.append('heater inhibit gate drive marginal')

    # ------------------------------------------------------------------ F. CS decoder
    u = PARTS['U203']['nets']
    ymap = {'15': 0, '14': 1, '13': 2, '12': 3, '11': 4, '10': 5, '9': 6, '7': 7}
    cs_map = {('%d%d%d' % ((n >> 2) & 1, (n >> 1) & 1, n & 1)): u[p] for p, n in sorted(ymap.items(), key=lambda kv: kv[1])}
    out['cs_decoder'] = {'address_C_B_A_to_net': cs_map,
                         'enable': 'G1 = +3V3, G2B = GND, G2A = CS_EN_N (Teensy pin 20, 10k pull-up)',
                         'timing': tv('tpd A/B/C->Y <= 6.7 ns, G2A->Y <= 6.5 ns at 3.3 V; HAL waits >= 1 us after CS_EN_N low',
                                      'DATASHEET ' + LVC138_DS + ' + DESIGN'),
                         'hal_rule': 'set the address with CS_EN_N high; no address change while enabled'}
    L.append('F. CS decoder: ' + ', '.join('%s -> %s' % kv for kv in cs_map.items()))

    # ------------------------------------------------------------------ G. regression of values read elsewhere
    reg = {}
    for ref, want in (('R330', '100k 0.1%'), ('R331', '31.6k 0.1%'), ('C330', '220nF/50V C0G'), ('R332', '237k 0.1%'),
                      ('R333', '29.4k 0.1%'), ('C331', '100nF/50V X7R'), ('R610', '12.7k 0.1%'), ('R611', '4.02k 0.1%')):
        ok = PARTS[ref]['value'] == want
        reg[ref] = {'value': PARTS[ref]['value'], 'v2p2': want, 'unchanged': ok}
        if not ok:
            fails.append('%s changed (read by calc/pc_transducer_v2.py and the generated SIL header)' % ref)
    reg['F401_deleted'] = 'F401' not in PARTS
    reg['J403_pin2'] = PARTS['J403']['nets']['2']
    reg['TVC_switches'] = [r for r in ('Q401', 'Q403') if r in PARTS]
    if not reg['F401_deleted'] or reg['J403_pin2'] != 'PRAIL' or len(reg['TVC_switches']) != 2:
        fails.append('LEAD-approved v2.3 chain not as drawn')
    out['regression'] = reg
    L.append('G. regression: R330-R333, C330, C331, R610, R611 unchanged = %s; F401 deleted %s; J403 pin 2 = %s; TVC switches %s'
             % (all(v['unchanged'] for k, v in reg.items() if isinstance(v, dict)), reg['F401_deleted'], reg['J403_pin2'], reg['TVC_switches']))

    # ------------------------------------------------------------------ H. +5V_SNS load
    n_x = sum(1 for p in PARTS.values() if p['ref'].startswith('J') and p['nets'].get('1') == '+5V_SNS')
    i_x = n_x * XDCR_I_A[0]
    out['v5sns_budget'] = {'transducers': n_x, 'I_A': tv(i_x, 'DERIVED %d x %.0f mA (%s)' % (n_x, XDCR_I_A[0] * 1e3, XDCR_I_A[1])),
                           'LDO_A': tv(LT1761_I_A[0], LT1761_I_A[1]), 'margin_A': round(LT1761_I_A[0] - i_x, 4)}
    L.append('H. +5V_SNS: %d transducers x 5 mA = %.0f mA of %.0f mA' % (n_x, i_x * 1e3, LT1761_I_A[0] * 1e3))

    out['inputs'] = {'TPS552882': {k: v for k, v in TPS.items()}, 'LTC4365': LTC, 'CSD17578Q5A': CSD, 'operating_point': OP, 'ADS131M04': ADC}
    out['checks_failed'] = fails
    L.append('CHECKS FAILED: %s' % (fails if fails else 'none'))
    body = json.dumps(out, sort_keys=True, separators=(',', ':'), default=str)
    out['record_sha256_16'] = hashlib.sha256(body.encode()).hexdigest()[:16]
    with open(a.out, 'w') as f:
        json.dump(out, f, indent=1, default=str)
    txt = os.path.splitext(a.out)[0] + '.txt'
    with open(txt, 'w') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
