#!/usr/bin/env python3
"""Flight Pc / P_feed / P_mid transducer RESELECTION, bridge conditioning and hardware-trip re-derivation (Electronics v2.11).

LEAD CHANGELOG line 205 (2026-10-13): the 070BG cannot meet a <= 1 ms transducer-path period on the v3.5.1 head; the flight Pc
transducer is reselected as a miniature seat-mounted unit (body within dia 12 x 30 mm above the 1/8-27 NPT seat, front dead volume
<= 20 mm3 (<= 60 mm3 with the CC-2 deeper seat), proof >= 1.1 x 102 = 112 bar abs, range covering the 45 bar MEOP with the 30 bar
abort and the 25 bar cap resolvable, operating >= 120 C plus a stated margin for the MISSING diaphragm gas-side transient,
bandwidth/rise time, N2O/O2 compatibility, vibration rating, output vs the ADC chain or the conditioning change, DATASHEET values,
mass, price TO-QUOTE delivered to Soenderborg DK-6400). LEAD CHANGELOG line 206 (3): miniature P_mid (BL-08) and P_feed (EL-11)
transducers alongside (proof >= 1.5 x the tank-side MEOP the transducer sees, N2O/O2 compatibility, operating temperature for the
location, DATASHEET mass and envelope, TO-QUOTE; one family for the three channels welcome).

Sections: A requirements (sources read, hashes); B candidates (DATASHEET extracts with URL and retrieval date; nothing recalled);
C requirement checks per candidate and channel; D passage period at each candidate's front dead volume (Mechanical's table);
E bridge conditioning (INA333) design, open-wire behaviour, noise and error budget; F hardware over-pressure comparator
(U330) re-derived for the new transfer function; G P_mid comparator (U570) re-derived; H mass; I generated SIL header
firmware/sil/ovp_hw_params.h (v3: v2.10 070BG chain kept in namespace ovp, the v2.11 chain in namespace ovp3).
Tags: DATASHEET (with source), DERIVED, DESIGN, ASSUMED, MISSING, TO-VERIFY, TO-QUOTE, SIM (Mechanical thermal), LEAD.
Nothing here is physical validation: the bench rows B-PC-1 / B-PF-1 / B-PM-1 (docs/bench_plan_v4.md) are the closures.
Usage: python3 calc/v2p11/pc_transducer_v3.py [--engine-root DIR] [--mech-root DIR] [--no-header]
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BAR = 1e5
P_STD = 101325.0
PSI = 6894.757
V_EXC = 5.0                                   # +5V_SNS nominal (LT1761-5), ratiometric excitation [DESIGN]
RETRIEVED = '2026-10-13'

E96 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62,
       1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67,
       2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42,
       4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
       7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]


def e96_all(lo, hi):
    out = []
    for dec in range(0, 8):
        for m in E96:
            v = m * 10 ** dec
            if lo <= v <= hi:
                out.append(round(v, 6))
    return out


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def tag(v, t, note=''):
    d = {'v': v, 'tag': t}
    if note:
        d['note'] = note
    return d


def cfg_const(text, name):
    m = re.search(r'constexpr\s+(?:float|double|int)\s+%s\s*=\s*([^;]+);' % re.escape(name), text)
    if not m:
        raise KeyError(name)
    expr = m.group(1).replace('f', '') if re.fullmatch(r'[-0-9.eE+f]+', m.group(1).strip()) else m.group(1)
    return expr


def num(text, name):
    s = cfg_const(text, name).strip()
    s = re.sub(r'(?<=[0-9.])f\b', '', s)
    return float(eval(s, {}, {}))  # only literal constants are read this way


# ---------------------------------------------------------------------------------------------------------------- B candidates
KULITE_XTL190 = {
    'id': 'C1', 'maker': 'Kulite Semiconductor Products', 'family': 'XTL-190 (M) series, miniature ruggedized IS (leadless silicon) bridge',
    'part_proposed': 'XTL-190SM-2000A (M5 x 0.8, short body, 0-2000 psia = 140 bar abs; ordering code TO-VERIFY with Kulite)',
    'source': 'Kulite XTL-190 (M) series datasheet (distributor copy https://loadcell.jp/products/files/XTL-190.pdf; the Kulite '
              'aeroexpo listing pdf.aeroexpo.online 170074-8955 is the same sheet); retrieved %s. Revision letter not visible in the '
              'extract: TO-VERIFY against the current kulite.com sheet before order.' % RETRIEVED,
    'ranges_bar': [0.7, 1.0, 1.7, 3.5, 7, 17, 35, 70, 140],
    'ranges_psi': [10, 15, 25, 50, 100, 250, 500, 1000, 2000],
    'modes': 'A, G, SG, D (DATASHEET; which modes exist at 2000 psi is TO-VERIFY)',
    'proof_rule': '2 x rated to 500 psi (35 bar), 1.5 x rated above 500 psi (DATASHEET "over pressure")',
    'burst_rule': '3 x rated to a maximum of 5000 psi (350 bar) (DATASHEET)',
    'excitation_V': {'rated': 10.0, 'max': 12.0},
    'input_impedance_ohm_min': 1000.0, 'output_impedance_ohm_nom': 1000.0,
    'fso_mV_at_rated': 100.0, 'residual_unbalance_mV_typ': 5.0,
    'nonlin_hyst_rep_pctFSO': {'typ_BFSL': 0.1, 'max': 0.5},
    'natural_frequency_kHz_no_screen_typ': [175, 200, 240, 300, 380, 550, 700, 1000, 1400],
    'accel_sens_pctFS_per_g_perp': [1.0e-3, 6.5e-4, 5.0e-4, 3.0e-4, 1.5e-4, 1.0e-4, 6.0e-5, 4.5e-5, 2.0e-5],
    'mapping_note': 'the extract lists the natural frequencies and accelerations in range order without row labels: mapping to the '
                    'ranges is DERIVED from the order (TO-VERIFY)',
    'operating_C': [-55.0, 175.0], 'compensated_C': [25.0, 80.0],
    'compensated_note': '"any 100 F range within the operating range is available on request" (DATASHEET)',
    'thermal_zero_pctFS_per_100F_typ': 1.0, 'thermal_sens_pct_per_100F_typ': 1.0,
    'steady_accel_g_max': 10000.0, 'vibration': '100 g max, 10-2000 Hz sine (DATASHEET)',
    'shock': 'MISSING in this sheet (steady acceleration 10 000 g max only)',
    'electrical': '4-conductor 30 AWG shielded cable, 36 in (914 mm); optional connector CMR-S1-E-04P',
    'wiring': 'red +input, black -input, green +output, white -output (XTEL-190 sheet; XTL-190 TO-VERIFY)',
    'mass_g_excl_cable': 4.0, 'cable_mass_g_per_m': None,
    'thread_options': {'190S': '10-32 UNF-2A, T 0.437 in (11.1 mm)', '190SM': 'M5 x 0.8, T 0.437 in (11.1 mm)',
                       '190L': '10-32 UNF-2A, T 0.760 in (19.3 mm)', '190LM': 'M5 x 0.8, T 0.760 in (19.3 mm)'},
    'hex_in': 0.375, 'dims_in': {'dia_0.148': 3.8, 'dia_0.190': 4.8, '0.40': 10.2, '0.15': 3.8, '0.17': 4.3, '0.630': 16.0},
    'dims_note': 'the extract gives the dimension values without their drawing positions: the 16.0 mm (0.630 in) height of hex + '
                 'strain relief above the thread is an INTERPRETATION (TO-VERIFY on the Kulite drawing)',
    'mounting_torque_Nm_max': 1.7, 'o_ring': 'silicone 4.5 ID x 1.0 CS (supplied)',
    'screens': 'B (standard), M (optional)',
    'wetted': '"will operate properly in any medium compatible with 15-5 SS or SiO2" + the supplied silicone O-ring (DATASHEET)',
    'media_note': 'pressure media: "consult factory; all media may not be suitable with the O-ring supplied" (DATASHEET)',
    'use_note': 'no flight-heritage statement in the sheet; Kulite publishes the series for test and R&D (XTEL sheet wording)',
}
KISTLER_4007D = {
    'id': 'C2', 'maker': 'Kistler Instrumente AG', 'family': '4007D high-temperature piezoresistive absolute pressure sensor, M5',
    'part_proposed': '4007D100FDS1-x (0-100 bar abs, fine thread, PiezoSmart digital compensation, PTFE cable; ordering code '
                     'pattern from the datasheet example 4007D050FDS1-2,0)',
    'source': 'Kistler data sheet 003-300e (https://assets.kistler.com.cn/SAPCommerce_Download_original/003-300e.pdf) and product '
              'page P0000218 (kistler.com), retrieved %s' % RETRIEVED,
    'ranges_bar': [5, 10, 20, 50, 100], 'overload_bar': [15, 30, 40, 100, 200],
    'modes': 'absolute', 'natural_frequency_kHz': '> 100',
    'accuracy': 'max pressure deviation <= +/-1 %FSO (incl. linearity, hysteresis, thermal effects, compensation model) with the '
                'Kistler amplifier compensation; linearity <= +/-0.2 %FSO (+/-0.4 % for >= 100 bar)',
    'accel_sens': '<= +/-0.1 mbar/g', 'operating_C': [-40.0, 200.0], 'compensated_C': [25.0, 180.0],
    'compensation_note': 'digital temperature compensation needs a Kistler amplifier 4665/4665B/4624A/4667A (power supply '
                         'integrated in the amplifier): an ECU-side implementation (constant-current excitation, bridge-voltage '
                         'temperature channel, PiezoSmart coefficients) is MISSING / TO-DESIGN',
    'thread': 'M5 x 0.5 (fine thread inlet); M14x1.25 adapter available', 'body_dia_mm': 6.2,
    'mass_g_excl_cable_connector': 3.0, 'torque_Nm': [1.5, 2.5], 'seal': 'copper seal 1145A1 (fluoropolymer 1145A2 to 200 C)',
    'cable': 'PTFE dia 3.0 mm -40..180 C, bend radius 22.5 mm fixed / 45 mm moving (Fig. 3; page 1 says 21/42: CONFLICT kept); '
             '5-pole Fischer connector',
    'media': 'compatible with most automotive fluids and gases; not water, hydrogen or helium (DATASHEET); N2O/O2 not stated',
    'vibration': 'MISSING (only acceleration sensitivity given)', 'ip': 'IP67',
}
ENDEVCO_8530B = {
    'id': 'C3', 'maker': 'Endevco (PCB Piezotronics / Amphenol)', 'family': '8530B piezoresistive absolute pressure transducer, 10-32',
    'part_proposed': '8530B-1000 (0-1000 psia = 68.95 bar abs)',
    'source': 'Endevco datasheet EDV-DS-8530B (https://buy.endevco.com/ContentStore/mktg/Downloads/EDV-DS-8530B_lowres.pdf), '
              'retrieved %s' % RETRIEVED,
    'ranges_psia': [200, 500, 1000, 2000], 'sens_mV_per_psi': [1.5, 0.6, 0.3, 0.3], 'fso_mV': 300.0,
    'resonance_Hz': [750000, 1000000, '>1000000', '>1000000'], 'burst_psia_min': [800, 2000, 4000, 4000],
    'case_pressure_psia_min': [1000, 5000, 5000, 5000],
    'nonlin_overrange': ['1.5 % of 3X FSO', '2 % of 3X FSO', '2.0 % at 2.5X FSO', '2.0 % at 1.5X FSO'],
    'proof_note': 'no proof value printed; for 1000 psia the sheet states the non-linearity at 2.5X FSO (2500 psia = 172 bar), '
                  'taken as the DERIVED usable over-range (TO-VERIFY as a proof rating)',
    'operating_C': [-54.0, 121.0], 'compensated_C': [-18.0, 93.0],
    'thermal_zero_pctFSO': 3.0, 'thermal_sens_pct': 4.0,
    'vibration': '1000 g pk', 'shock': '20 000 g, 100 us haversine', 'acceleration': '1000 g',
    'excitation_V': {'standard': 10.0, 'max': 18.0, '-D option': 5.0},
    'thread': '10-32 UNF-2A', 'case_length_mm': 11.12, 'mass_g': 2.3, 'cable_g_per_m': 9.0, 'dead_volume_mm3': 5.0,
    'wetted': '17-4 PH CRES case, epoxy internal seals, Parylene C, Viton O-ring; media: clean dry gas only (DATASHEET)',
    'hex_or_dia': 'MISSING in the sheet text (drawing not extracted)',
}
REJECTED = [
    {'part': 'Kulite XTL-190(M) 1000 psi (70 bar)', 'reason': 'proof 1.5 x 1000 psi = 103.4 bar < 112 bar abs (Pc) and < 105 bar '
     '(1.5 x tank MEOP for P_feed/P_mid) (DATASHEET rule)'},
    {'part': 'Kulite XTEL-190(M) (high-temperature variant, kulite.com/assets/media/2017/06/XTEL-190.pdf)',
     'reason': 'linear vibration 20 g peak 10-2000 Hz and shock 20 g / 11 ms only (DATASHEET); operating media to 273 C would '
               'otherwise suit'},
    {'part': 'TE MEAS XP5 (EXP5-10BS-C00008, te.com product 10221204-00)', 'reason': 'operating -40..120 C: 1.7 C above the B1 '
     'soak SIM, no margin for the diaphragm transient (DATASHEET page)'},
    {'part': 'KELLER Series M5 (keller-pressure.com)', 'reason': 'ranges 0..3 to 0..30 bar (DATASHEET page): does not cover the 45 '
     'bar MEOP'},
    {'part': 'Endevco 8530C', 'reason': 'ranges 15-100 psia only (DATASHEET EDV-DS-8530C)'},
    {'part': 'TE M3234-000005-070BG (current)', 'reason': 'body dia 19 x 60 mm class does not fit the dia 12 x 30 envelope (Mechanical '
     'pc_space_v1); every mounting found gives T > 1 ms (pc_line_period_v1); kept as the stand static-level reference'},
]


def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default=os.path.join(ROOT, '..', 'shared-fallback', 'engine'))
    ap.add_argument('--mech-root', default=os.path.join(ROOT, '..', 'mechanical', 'v351', 'pc'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'pc_transducer_v3.json'))
    ap.add_argument('--header', default=os.path.join(ROOT, 'firmware', 'sil', 'ovp_hw_params.h'))
    ap.add_argument('--no-header', action='store_true')
    a = ap.parse_args()

    # ------------------------------------------------------------------------------------------------------------ A inputs
    mech = {k: os.path.join(a.mech_root, k) for k in ('pc_line_period_v1.json', 'pc_space_v1.json', 'pc_transducer_temperature_v1.json')}
    want = {'pc_line_period_v1.json': '7f5d8950516d98f2', 'pc_space_v1.json': 'b336b6abf9821b68',
            'pc_transducer_temperature_v1.json': '774519536f26c762'}
    mech_hash = {k: sha16(p) for k, p in mech.items()}
    hash_ok = {k: mech_hash[k] == want[k] for k in want}
    lp = json.load(open(mech['pc_line_period_v1.json']))
    tt = json.load(open(mech['pc_transducer_temperature_v1.json']))
    comb_fn = os.path.join(a.engine_root, 'interfaces', 'combustion.json')
    comb = json.load(open(comb_fn))
    cfg_txt = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h')).read()
    eng_txt = open(os.path.join(ROOT, 'firmware', 'src', 'core', 'engine_params.h')).read()
    tank_meop = comb['operating_points']['tank_MEOP_Pa']['v']
    relief = comb['relief_v2p4a']['v']
    disc_hi = relief['secondary_disc']
    m = re.search(r'([0-9.]+)\s*MPa\s*\+/-\s*([0-9.]+)\s*%', disc_hi)
    disc_max = float(m.group(1)) * 1e6 * (1 + float(m.group(2)) / 100) if m else float('nan')
    fw_abort = num(eng_txt, 'kPcAbortAbs_Pa')
    meop = num(eng_txt, 'kPcMeopAbs_Pa')
    cap = num(eng_txt, 'kPcNormalCapAbs_Pa')
    b1_soak = tt['DC-B1v3p99_tg711_hi_SS316L_L2.5_v351_TB1GC']['series']['T1_head_top_bracket_foot']['max_soak_C']
    a1 = tt['DC-A1dispp99_tg711_hi_SS316L_L2.5_v351_TB1GC']['series']['T1_head_top_bracket_foot']
    pc_proof_req = 1.1 * 102e5                         # LEAD 205: proof >= 1.1 x 102 = 112 bar abs
    feed_proof_req = 1.5 * tank_meop                   # LEAD 206 (3): >= 1.5 x tank-side MEOP the transducer sees
    L = []
    out = {'script': 'calc/v2p11/pc_transducer_v3.py', 'version': 'v3 (Electronics v2.11)', 'date': RETRIEVED,
           'supersedes': 'calc/pc_transducer_v2.py for the flight Pc / P_feed / P_mid channels (v2 kept: it describes the v2.10 070BG '
                         'chain, which stays as the stand static-level reference and the v2.10 comparator in the SIL)',
           'inputs': {'mechanical_v351_pc': {k: {'sha256_16': mech_hash[k], 'expected': want[k], 'match': hash_ok[k]} for k in want},
                      'combustion_json': {'file': 'interfaces/combustion.json', 'sha256_16': sha16(comb_fn), 'version': comb.get('version')},
                      'config_h_sha256_16': sha16(os.path.join(ROOT, 'firmware', 'src', 'core', 'config.h')),
                      'engine_params_h_sha256_16': sha16(os.path.join(ROOT, 'firmware', 'src', 'core', 'engine_params.h'))}}
    out['A_requirements'] = {
        'pc': {
            'envelope': tag('body within dia 12 x 30 mm above the 1/8-27 NPT seat (Mechanical cuts the CC-2 head detail to the named '
                            'thread and body)', 'LEAD 205 / Mechanical pc_space_v1 (cyl_d12_h30 clear at neutral; nearest TC-04 1.0 mm)'),
            'front_dead_volume_mm3': tag({'CC-1': 20.0, 'CC-2': 60.0}, 'LEAD 205'),
            'proof_Pa_abs_min': tag(pc_proof_req, 'LEAD 205: 1.1 x 102 bar abs (FA-1 ultimate, period domain T <= 1 ms, line 194 (1))'),
            'range': tag('covers the 45 bar abs MEOP; 30 bar abort and 25 bar cap resolvable', 'LEAD 205'),
            'operating_temperature_C_min': tag(120.0, 'LEAD 205 (B1 soak %.1f C SIM, Mechanical pc_transducer_temperature_v1)' % b1_soak),
            'seat_temperature_SIM': tag({'A1_at_RELIGHT_C': a1['at_RELIGHT_C'], 'A1_soak_max_C': a1['max_soak_C'], 'B1_soak_max_C': b1_soak},
                                        'SIM (Mechanical v351 thermal, 20 C start ASSUMED); hot-day re-run at T0 = 40 C and a seat '
                                        'thermocouple are the closures (LEAD 205)'),
            'diaphragm_gas_side_transient': tag(None, 'MISSING (LEAD 205): see E.margin'),
            'other': tag('bandwidth and rise time stated; N2O/O2 compatibility; vibration rating; output vs ADC chain or conditioning '
                         'change; DATASHEET values; mass; price TO-QUOTE delivered to Soenderborg DK-6400', 'LEAD 205')},
        'p_feed_p_mid': {
            'proof_basis': tag(feed_proof_req, 'LEAD 206 (3): 1.5 x tank MEOP %.1f bar abs (combustion.json v2.4a operating_points.'
                                               'tank_MEOP_Pa, LEAD v0). Both channels see the tank-side pressure: P_feed always; '
                                               'P_mid whenever V1 is open with V2 closed (purge sequence step, V1 leak or stuck '
                                               'open)' % (tank_meop / BAR)),
            'credible_maximum_note': tag(disc_max, 'DERIVED: the feed segment is bounded by the secondary disc 9.5 MPa + 5 %% = %.2f bar '
                                                   '(combustion.json relief_v2p4a; Mechanical SEGP 99.75 bar). The proposed part '
                                                   'covers 1.5 x this too (see C).' % (disc_max / BAR)),
            'locations': tag({'BL-08 (P_mid)': 'port (12.58, 32.77), z 268 mm on the V1-V2 mid passage (mechanical.json v2.1 '
                                               'bleed topology)', 'EL-11 (P_feed)': 'CG (10.8, 8.91, 304.5) mm (massprops via '
                                               'mechanical.json v2.1; FD-01 port)'},
                             'mechanical.json v2.1; the v3.5.1 positions are Mechanical\'s'),
            'mass_carried': tag(0.05, 'Mechanical: 2 x 50 g ASSUMED; expects about -0.07 kg in total (LEAD 206 (3))')},
    }
    # ------------------------------------------------------------------------------------------------- D passage period table
    rows = [r for r in lp['rows'] if r['case'].startswith('CC-1')]
    v_end = [r['V_end_mm3'] for r in rows]
    gases = ['T_ms_N2O_vap_200K', 'T_ms_N2O_vap_250K', 'T_ms_N2O_vap_300K', 'T_ms_products_400K']

    def period(vol):
        return {g.replace('T_ms_', ''): round(interp(vol, v_end, [r[g] for r in rows]), 3) for g in gases}

    cc2 = {}
    for r in lp['rows']:
        if r['case'].startswith('CC-2'):
            cc2.setdefault(r['case'], []).append(r)

    # ----------------------------------------------------------------------------------------------- C checks per candidate
    c1 = KULITE_XTL190
    i140 = c1['ranges_bar'].index(140)
    c1_fs = c1['ranges_psi'][i140] * PSI                         # 2000 psia = 137.9 bar abs
    c1_proof = 1.5 * c1_fs                                        # 3000 psi = 206.8 bar
    c1_burst = min(3 * c1_fs, 5000 * PSI)
    c1_fn = c1['natural_frequency_kHz_no_screen_typ'][i140]
    c1_hex_ac = c1['hex_in'] * 25.4 / math.cos(math.radians(30))
    c4 = KISTLER_4007D
    c4_fs, c4_ovl = 100e5, 200e5
    c3 = ENDEVCO_8530B
    c3_fs = 1000 * PSI
    c3_overrange = 2.5 * c3_fs
    vol_c1 = 6.0            # ASSUMED B-screen cavity: dia 3.8 x ~0.5 mm (screen gap ASSUMED) -> 5.7 mm3; TO-VERIFY with Kulite
    vol_c4 = 3.0            # ASSUMED front-sealed flush diaphragm in an M5 bore; TO-VERIFY
    vol_c3 = c3['dead_volume_mm3']
    T_soak = b1_soak

    def chk(ok, why):
        return {'pass': ok, 'basis': why}

    cand = []
    cand.append({
        'id': 'C1', 'proposed': c1['part_proposed'], 'rank': 'PREFERRED (Pc, P_feed, P_mid: one family)',
        'range': tag({'FS_Pa_abs': round(c1_fs, 0), 'FS_bar': round(c1_fs / BAR, 2), 'mode': 'A (absolute)'},
                     'DATASHEET (2000 psi = 140 bar range code)'),
        'checks': {
            'proof_ge_112bar_abs': chk(c1_proof >= pc_proof_req, 'DATASHEET 1.5 x 2000 psi = %.1f bar >= %.1f' % (c1_proof / BAR, pc_proof_req / BAR)),
            'proof_ge_1p5_tank_MEOP': chk(c1_proof >= feed_proof_req, '%.1f >= %.1f bar' % (c1_proof / BAR, feed_proof_req / BAR)),
            'proof_ge_1p5_disc_max': chk(c1_proof >= 1.5 * disc_max, '%.1f >= %.1f bar (DERIVED bound)' % (c1_proof / BAR, 1.5 * disc_max / BAR)),
            'burst_bar': tag(round(c1_burst / BAR, 1), 'DATASHEET 3 x rated capped at 5000 psi'),
            'range_covers_MEOP': chk(c1_fs >= meop, '%.1f bar abs FS >= %.1f' % (c1_fs / BAR, meop / BAR)),
            'operating_temperature': chk(c1['operating_C'][1] >= 120.0, 'DATASHEET -55..+175 C; margin %.1f C over the B1 soak '
                                         '%.1f C SIM' % (c1['operating_C'][1] - T_soak, T_soak)),
            'envelope_dia12': chk(c1_hex_ac <= 12.0, 'hex 3/8 in = 9.53 mm A/F, %.2f mm across corners (DERIVED) <= 12; radial '
                                  'clearance %.2f mm' % (c1_hex_ac, (12.0 - c1_hex_ac) / 2)),
            'envelope_height30': chk(None, 'hex + strain relief 16.0 mm (0.630 in, INTERPRETATION of the extract) + cable bend: '
                                     '30 AWG 4-core shielded cable dia MISSING; with a 10 x dia bend radius the exit fits 30 mm only '
                                     'if the cable dia <= 1.4 mm (DERIVED) -> TO-VERIFY (Kulite drawing, Mechanical CC-2 detail)'),
            'thread': tag('M5 x 0.8 (190SM) or 10-32 UNF-2A (190S); proposal M5 x 0.8 SI; seal: replace the supplied silicone O-ring by '
                          'an FKM ring of the same size or a metal seal on the hex shoulder (Mechanical / oxidiser-compatibility '
                          'rule; Kulite to confirm)', 'DATASHEET / DESIGN'),
            'front_dead_volume': chk(vol_c1 <= 20.0, '%.0f mm3 ASSUMED (B screen cavity, MISSING in the sheet); M screen or no '
                                     'screen TO-VERIFY with Kulite' % vol_c1),
            'natural_frequency': tag({'kHz_no_screen_typ': c1_fn, 'rise_10_90_us_DERIVED': round(0.33 / (c1_fn * 1e3) * 1e6, 2)},
                                     'DATASHEET (range mapping by order, TO-VERIFY); with the B screen MISSING'),
            'accuracy': tag({'nonlin_hyst_rep_max_bar': round(0.005 * c1_fs / BAR, 2),
                             'thermal_zero_typ_bar_per_C': round(0.01 * c1_fs / BAR / (100 / 1.8), 4),
                             'thermal_sens_typ_pct_per_C': round(1.0 / (100 / 1.8), 4)}, 'DATASHEET (typ thermal values; max MISSING)'),
            'vibration': tag(c1['vibration'] + '; steady acceleration 10 000 g', 'DATASHEET; vehicle spectrum MISSING (no '
                             'qualification spectrum in the ICD yet)'),
            'n2o_o2': tag('wetted 15-5 SS and SiO2 per the sheet; silicone O-ring supplied (replace); oxygen cleaning (ASTM G93 '
                          'level) and N2O service statement TO-VERIFY / TO-QUOTE with Kulite', 'DATASHEET + TO-VERIFY'),
            'output': tag('passive bridge, 100 mV FSO at 10 V (nominal) -> 50 mV at the 5 V ratiometric excitation (DERIVED): needs '
                          'the bridge conditioning of section E', 'DATASHEET + DERIVED'),
            'mass_g': tag({'body': c1['mass_g_excl_cable'], 'cable_0p9m': None}, 'DATASHEET body; cable mass MISSING'),
            'price': tag('TO-QUOTE delivered to Soenderborg DK-6400 (Kulite Sensors Ltd, UK / Kulite GmbH, DE)', 'TO-QUOTE'),
        },
        'passage_period_ms_CC1_at_volume': period(vol_c1),
        'passage_period_ms_CC1_at_20mm3': period(20.0),
    })
    cand.append({
        'id': 'C2', 'proposed': c4['part_proposed'], 'rank': 'ALTERNATE (Pc), larger conditioning change',
        'range': tag({'FS_Pa_abs': c4_fs, 'FS_bar': 100.0, 'mode': 'absolute'}, 'DATASHEET'),
        'checks': {
            'proof_ge_112bar_abs': chk(c4_ovl >= pc_proof_req, 'DATASHEET overload 200 bar (100 bar range)'),
            'proof_ge_1p5_tank_MEOP': chk(c4_ovl >= feed_proof_req, '200 >= %.1f bar' % (feed_proof_req / BAR)),
            'range_covers_MEOP': chk(c4_fs >= meop, '100 bar abs FS'),
            'operating_temperature': chk(True, 'DATASHEET sensor -40/200 C; margin %.1f C over the B1 soak SIM' % (200 - T_soak)),
            'envelope_dia12': chk(True, 'body dia 6.2 mm (DATASHEET)'),
            'envelope_height30': chk(None, 'cable bend radius 22.5 mm fixed (DATASHEET Fig. 3; page 1 says 21 mm: CONFLICT) above the '
                                     'body: likely > 30 mm unless the cable leaves sideways through a channel: TO-VERIFY Mechanical'),
            'front_dead_volume': chk(vol_c4 <= 20.0, '%.0f mm3 ASSUMED front-sealed; TO-VERIFY' % vol_c4),
            'natural_frequency': tag('> 100 kHz', 'DATASHEET'),
            'accuracy': tag(c4['accuracy'], 'DATASHEET (with the Kistler amplifier compensation)'),
            'vibration': tag('MISSING (acceleration sensitivity <= 0.1 mbar/g only)', 'DATASHEET'),
            'n2o_o2': tag('not stated (automotive fluids and gases; not water/H2/He)', 'DATASHEET; TO-VERIFY'),
            'output': tag(c4['compensation_note'], 'DATASHEET + MISSING'),
            'mass_g': tag({'body': 3.0, 'cable_connector': None}, 'DATASHEET body; cable + Fischer connector MISSING'),
            'price': tag('TO-QUOTE delivered to Soenderborg DK-6400 (Kistler, Winterthur CH)', 'TO-QUOTE'),
        },
        'passage_period_ms_CC1_at_volume': period(vol_c4),
    })
    cand.append({
        'id': 'C3', 'proposed': c3['part_proposed'], 'rank': 'NOT FOR FLIGHT (temperature margin); stand / B-PC-1 comparison only',
        'range': tag({'FS_Pa_abs': round(c3_fs, 0), 'FS_bar': round(c3_fs / BAR, 2), 'mode': 'absolute (psia)'}, 'DATASHEET'),
        'checks': {
            'proof_ge_112bar_abs': chk(c3_overrange >= pc_proof_req, 'no proof value printed; non-linearity stated at 2.5X FSO = %.0f '
                                       'bar (DERIVED usable over-range, TO-VERIFY); burst 4000 psia = %.0f bar' % (c3_overrange / BAR, 4000 * PSI / BAR)),
            'range_covers_MEOP': chk(c3_fs >= meop, '%.2f bar abs FS' % (c3_fs / BAR)),
            'operating_temperature': chk(False, 'DATASHEET -54..+121 C: %.1f C over the B1 soak SIM; no margin for the MISSING '
                                         'diaphragm transient' % (121 - T_soak)),
            'front_dead_volume': chk(True, 'DATASHEET 0.005 cc = 5 mm3 (+ port)'),
            'natural_frequency': tag('> 1 MHz (1000 psia)', 'DATASHEET'),
            'vibration': tag('1000 g pk; shock 20 000 g 100 us', 'DATASHEET'),
            'n2o_o2': tag('clean dry gas only; epoxy, Parylene C, Viton wetted', 'DATASHEET: organic wetted materials, not preferred'),
            'mass_g': tag({'body': 2.3, 'cable_g_per_m': 9.0}, 'DATASHEET'),
            'price': tag('TO-QUOTE delivered to Soenderborg DK-6400', 'TO-QUOTE'),
        },
        'passage_period_ms_CC1_at_volume': period(vol_c3),
    })
    out['B_candidates_datasheet'] = {'C1': KULITE_XTL190, 'C2': KISTLER_4007D, 'C3': ENDEVCO_8530B, 'rejected': REJECTED}
    out['C_checks'] = cand
    out['D_passage_period'] = {
        'basis': 'Mechanical pc_line_period_v1.json (lossless 1-D acoustics, DERIVED; passage gas sound speed MISSING, bounded '
                 '222-400 m/s; Combustion gives it at the FA-1 instant). Linear interpolation in the CC-1 V_end rows.',
        'CC1_V_end_max_for_T_le_1ms': lp['V_end_max_mm3_for_T_le_1ms'],
        'C1_at_6mm3': period(vol_c1), 'C1_at_20mm3': period(20.0),
        'CC2_rows': {k: [{kk: r[kk] for kk in ['V_end_mm3'] + gases} for r in v] for k, v in cc2.items()},
        'finding': 'with CC-1 a 6 mm3 front volume keeps T <= 1 ms except for N2O vapour at 200 K (1.03 ms) and 20 mm3 exceeds 1 ms '
                   'below about 250 K; CC-2 (passage <= 30 mm) keeps T <= 0.86 ms up to 60 mm3 in every gas (DERIVED from '
                   'Mechanical\'s table): CC-2 is the robust route, as the lead\'s 60 mm3 allowance implies',
    }
    L.append('A. Pc proof req %.1f bar abs; P_feed/P_mid proof req %.1f bar (1.5 x tank MEOP %.1f); disc max %.2f bar; B1 soak %.1f C SIM; '
             'Mechanical hashes %s' % (pc_proof_req / BAR, feed_proof_req / BAR, tank_meop / BAR, disc_max / BAR, b1_soak,
                                       'match' if all(hash_ok.values()) else 'MISMATCH %s' % hash_ok))
    for c in cand:
        fails = [k for k, v in c['checks'].items() if isinstance(v, dict) and v.get('pass') is False]
        opens = [k for k, v in c['checks'].items() if isinstance(v, dict) and 'pass' in v and v.get('pass') is None]
        L.append('C. %s %s: %s; fails %s; open %s' % (c['id'], c['proposed'][:60], c['rank'], fails or 'none', opens or 'none'))
    L.append('D. C1 at 6 mm3 CC-1 period %s ms; at 20 mm3 %s' % (period(vol_c1), period(20.0)))

    # --------------------------------------------------------------------------------------------- E bridge conditioning
    fso_5v = c1['fso_mV_at_rated'] * 1e-3 * V_EXC / c1['excitation_V']['rated']        # 50 mV nominal at 5 V
    span_out = 0.8 * V_EXC                                                             # 4.0 V for 0 -> FS (0.5 -> 4.5 V)
    g_nom = span_out / fso_5v
    rg_nom = 100e3 / (g_nom - 1)
    rg_e96 = min(e96_all(100, 1e5), key=lambda r: abs(r - rg_nom))
    g_e96 = 1 + 100e3 / rg_e96
    # sensitivity spread of a passive bridge is not in the sheet ("100 mV nominal"): select-on-test RG from the calibration sheet
    sens_band = (0.75, 1.5)                                                            # ASSUMED bracket of FSO / nominal
    rg_range = [100e3 / (span_out / (fso_5v * s) - 1) for s in sens_band]
    bw_g100 = 3.5e3                                                                    # DATASHEET SBOS445C, G = 100
    bw = bw_g100 * 100.0 / g_e96                                                       # DERIVED (constant gain-bandwidth scaling)
    en = 50e-9                                                                         # DATASHEET 50 nV/rtHz (G >= 100)
    r_br = c1['output_impedance_ohm_nom']
    en_r = math.sqrt(4 * 1.380649e-23 * 300 * (2 * r_br + 2 * 1e3))                    # bridge + 2 x 1 k RFI resistors (DESIGN)
    f_aaf = 1 / (2 * math.pi * (12.7e3 * 4.02e3 / 16.72e3) * 22e-9)
    noise_rti = math.sqrt(en ** 2 + en_r ** 2) * math.sqrt(1.57 * f_aaf)
    noise_bar = noise_rti / fso_5v * c1_fs / BAR
    unb_5v = c1['residual_unbalance_mV_typ'] * 1e-3 * V_EXC / c1['excitation_V']['rated']
    r_bias = 10e6
    bias_off = 2 * (V_EXC / 2) / r_bias * r_br                                         # differential offset from the open-wire bias
    ref_nom = 0.1 * V_EXC
    trim_need = (unb_5v + bias_off) * g_e96
    out['E_conditioning'] = {
        'topology': tag('per channel (Pc, P_feed, P_mid): bridge excitation = +5V_SNS (ratiometric with the existing 0.5-4.5 V '
                        'scaling and the comparator references), RFI filter 2 x 1.00 k + 10 nF diff + 2 x 1 nF CM, TI INA333 '
                        '(zero-drift, rail-to-rail output) on +5V_SNS, gain set by a select-on-test RG, REF from a buffered '
                        'select-on-test divider of +5V_SNS (OPA2333 dual buffer per two channels), open-wire bias 10 M on each '
                        'signal line (SIG+ to GND, SIG- to +5V_SNS). INA output = the existing PC_SIG / PFEED_SIG / P_MID_SIG net: '
                        'divider, anti-alias RC, ADS131M04 and the U330 / U570 comparators are unchanged in topology.', 'DESIGN'),
        'transfer': tag({'zero_frac': 0.1, 'span_frac': 0.8, 'FS_Pa_abs': round(c1_fs, 0),
                         'equation': 'V_SIG = V_exc x (0.10 + 0.80 x p_abs / FS) after the select-on-test trims'}, 'DESIGN'),
        'bridge_fso_at_5V_mV': tag(round(fso_5v * 1e3, 2), 'DERIVED from the DATASHEET 100 mV at 10 V (ratiometric bridge)'),
        'gain': tag({'nominal': round(g_nom, 2), 'RG_nominal_ohm': round(rg_nom, 1), 'RG_E96_ohm': rg_e96, 'G_E96': round(g_e96, 2),
                     'RG_select_range_ohm': [round(r, 0) for r in rg_range], 'for_FSO_ratio': sens_band},
                    'DESIGN; FSO spread per unit ASSUMED 0.75-1.5 x nominal (the sheet gives the nominal only): RG chosen from '
                    'the unit calibration sheet, 0.1 % thin film'),
        'bandwidth_Hz': tag(round(bw, 0), 'DERIVED from DATASHEET INA333 3.5 kHz at G = 100 (SBOS445C), scaled by G'),
        'anti_alias_Hz': tag(round(f_aaf, 0), 'DESIGN (unchanged 12.7k || 4.02k x 22 nF)'),
        'noise': tag({'rti_uV_rms': round(noise_rti * 1e6, 3), 'bar_rms': round(noise_bar, 4)}, 'DERIVED (INA333 50 nV/rtHz '
                     'DATASHEET + resistor thermal noise, noise bandwidth 1.57 x the AAF corner); EMI pickup on the 50 mV cable '
                     'not modelled: the SIL keeps 3450 Pa rms ASSUMED and adds 2x as a sensitivity'),
        'resolution_bar_per_ADC_LSB': tag(round((1.2 / 2 ** 23) / 0.23822 / (span_out / c1_fs) / BAR, 7), 'DERIVED (24-bit, '
                                         '1.2 V FS, 0.23822 divider)'),
        'zero_trim': tag({'residual_unbalance_at_5V_mV_typ': round(unb_5v * 1e3, 2), 'bias_offset_mV': round(bias_off * 1e3, 3),
                          'output_trim_needed_V_typ': round(trim_need, 3), 'REF_nominal_V': ref_nom,
                          'REF_select_range_V': [round(ref_nom - 1.5 * trim_need, 3), round(ref_nom + 1.5 * trim_need, 3)]},
                         'DATASHEET unbalance (typ, max MISSING) + DESIGN: the REF divider bottom resistor is select-on-test at '
                         'B-PC-1 so the comparator trip (analogue) sees the trimmed zero; the firmware auto-zero handles the '
                         'remaining drift on the digital path'),
        'open_wire': tag({
            'SIG+ open': 'IN+ pulled to GND -> output at the low rail (0.05 V) < 0.25 V: PC_SENSOR LOW (DERIVED)',
            'SIG- open': 'IN- pulled to +5V_SNS -> output at the low rail: LOW (DERIVED)',
            'EXC+ open': 'both signals fall to ~0 V through the bridge arms; INA333 common-mode limit (V-) + 0.1 V violated: output '
                         'undefined (MISSING) - may read near zero pressure (not caught by the 0.25 V window). Firmware coverage: '
                         'the light rule never confirms (no E1/E2: abort with the gate reason); in RUN a step to ~0 bar abs trips '
                         'PC_BAND. B-PC-1 open-wire row measures it.',
            'EXC- open': 'both signals rise to ~5 V; INA333 CM limit (V+) - 0.1 V violated: output undefined (MISSING); if it reads '
                         'HIGH the comparator trips (HW_OVERPRESSURE) - the same class as the v2.10 070BG open-ground case. '
                         'B-PC-1 open-wire row.',
            'cable short SIG+ to SIG-': 'output = REF (reads the trimmed zero ~ 0 bar abs): same coverage as EXC+ open'},
            'DERIVED / MISSING (bench)'),
        'power': tag({'bridge_mA_max_each': round(V_EXC / c1['input_impedance_ohm_min'] * 1e3, 2), 'channels': 3,
                      'bridges_mA_max_total': round(3 * V_EXC / c1['input_impedance_ohm_min'] * 1e3, 1),
                      'ina333_uA_each': 50, 'LT1761_5_mA_rating': 100},
                     'DATASHEET (Kulite input impedance >= 1 k; INA333 50 uA typ; LT1761 100 mA); the +5V_SNS budget is re-summed '
                     'in ecu_design.py'),
        'margin_statement': tag({'rating_C': c1['operating_C'][1], 'B1_soak_SIM_C': b1_soak, 'A1_relight_seat_SIM_C': a1['at_RELIGHT_C'],
                                 'margin_C': round(c1['operating_C'][1] - b1_soak, 1),
                                 'compensated_range_C': c1['compensated_C']},
                                'DERIVED: 56.7 C between the DATASHEET operating limit and the SIM soak maximum is the margin held for '
                                'the MISSING diaphragm gas-side transient (adiabatic compression of the passage gas at the light and '
                                'hot products entering the passage). Outside 25-80 C the thermal errors are not compensated: the '
                                'compensated band should be ordered as 20-120 C (sheet: any 100 F band on request, TO-QUOTE). '
                                'Closures: seat thermocouple + post-burn zero check in B-PC-1 / static fire, hot-day re-run (LEAD 205).'),
    }
    # error budget at the decision levels (after the B-PC-1 trims, seat temperature change from trim to RELIGHT)
    dT = a1['at_RELIGHT_C'] - 20.0
    eb = {}
    for lvl, name in ((cap, 'cap_25bar'), (fw_abort, 'abort_30bar'), (meop, 'MEOP_45bar')):
        e_nl = 0.005 * c1_fs
        e_tz = 0.01 * c1_fs / (100 / 1.8) * dT
        e_ts = 0.01 / (100 / 1.8) * dT * lvl
        e_g = 50e-6 * dT * lvl                                                       # INA333 gain drift max (excl. RG)
        e_rg = 25e-6 * dT * lvl                                                      # RG thin film 25 ppm/C ASSUMED
        rss = math.sqrt(e_nl ** 2 + e_tz ** 2 + e_ts ** 2 + e_g ** 2 + e_rg ** 2)
        eb[name] = {'level_bar_abs': lvl / BAR, 'nonlin_hyst_rep_max_bar': round(e_nl / BAR, 3), 'thermal_zero_typ_bar': round(e_tz / BAR, 3),
                    'thermal_span_typ_bar': round(e_ts / BAR, 3), 'ina_gain_drift_bar': round(e_g / BAR, 4),
                    'rg_drift_bar': round(e_rg / BAR, 4), 'rss_bar': round(rss / BAR, 3), 'linear_sum_bar': round((e_nl + e_tz + e_ts + e_g + e_rg) / BAR, 3)}
    out['E_error_budget'] = tag({'dT_trim_to_relight_C': dT, 'levels': eb,
                                 'digital_path_note': 'the ARMED auto-zero and the coast re-zero remove the zero term on the '
                                                      'firmware path; the hardware comparator keeps it'},
                                'DERIVED (DATASHEET typ thermal terms; the max values are MISSING in the sheet)')
    L.append('E. INA333 G %.1f (RG %.0f E96), BW %.0f Hz, noise %.4f bar rms (DERIVED), REF trim range %s V; error RSS at 30 bar %.2f bar'
             % (g_e96, rg_e96, bw, noise_bar, out['E_conditioning']['zero_trim']['v']['REF_select_range_V'], eb['abort_30bar']['rss_bar']))

    # ----------------------------------------------------------------------- F hardware over-pressure comparator (U330)
    def vsig(p_abs):
        return V_EXC * (0.1 + 0.8 * p_abs / c1_fs)

    def p_of(v):
        return (v / V_EXC - 0.1) / 0.8 * c1_fs

    p_target = 3146517.6 + P_STD            # keep the v2.10 trip pressure (32.48 bar abs at sea level), now absolute at every altitude
    vio, iib = 9e-3, 400e-9                 # DATASHEET SLCS136V (LMV331) max -40..125 C at 5 V (as calc/pc_transducer_v2.py)
    best = None
    c330 = 220e-9
    for ra in e96_all(10e3, 200e3):
        rb = ra                              # tap 1/2 (DESIGN): doubles the comparator sensitivity vs the v2.10 0.2401 tap
        k_tap = rb / (ra + rb)
        rth = ra * rb / (ra + rb)
        tau = rth * c330
        if not (0.0050 <= tau <= 0.0056):
            continue
        for rd in (29.4e3,):
            for rc in e96_all(50e3, 500e3):
                k_ref = rd / (rc + rd)
                v_ref = V_EXC * k_ref
                v_trip = v_ref / k_tap
                p_trip = p_of(v_trip)
                sens = V_EXC * 0.8 / c1_fs * k_tap
                e_bias = iib * max(rth, rc * rd / (rc + rd))
                dp = (vio + e_bias + 2 * v_ref * 2e-3 * 0.5 * 2) / sens   # 0.1 % on both ratios (2 x 2 x 0.1 % x v_ref)
                score = abs(p_trip - p_target) / 1e3 + abs(tau - 0.005283) * 1e3   # trip first (kPa), then tau near as built (ms)
                if best is None or score < best[0]:
                    best = (score, ra, rb, rc, rd, k_tap, k_ref, v_trip, p_trip, dp, tau, rth)
    _, ra, rb, rc, rd, k_tap, k_ref, v_trip, p_trip, dp, tau, rth = best
    out['F_hw_comparator_U330'] = {
        'values': tag({'R330': ra, 'R331': rb, 'C330': c330, 'R332': rc, 'R333': rd}, 'DESIGN (E96 0.1 %; C330 220 nF C0G kept)'),
        'tap_ratio': tag(round(k_tap, 4), 'DESIGN 1/2 (v2.10: 0.2401): keeps the comparator sensitivity per bar of the 70 bar '
                                          'chain with the 140 bar span'),
        'tau_s': tag(round(tau, 6), 'DERIVED (R330 || R331) x C330 (v2.10: 0.005283 s)'),
        'pc_sig_trip_V': tag(round(v_trip, 4), 'DERIVED'),
        'trip_nominal_Pa_abs': tag(round(p_trip, 0), 'DERIVED (absolute at every altitude; v2.10: 31.47 bar g)'),
        'band_circuit_Pa': tag(round(dp, 0), 'DERIVED worst-case linear sum (LMV331 Vio 9 mV and Iib 400 nA max DATASHEET, 0.1 % ratios)'),
        'trip_range_abs_Pa': tag([round(p_trip - dp, 0), round(p_trip + dp, 0)], 'DERIVED circuit terms'),
        'hardware_low_end_above_firmware_30bar': tag(bool(p_trip - dp >= fw_abort), 'DERIVED (transducer error common to both paths)'),
        'margin_high_end_to_MEOP_Pa': tag(round(meop - (p_trip + dp), 0), 'DERIVED'),
        'transducer_error_common_bar': tag(eb['abort_30bar']['rss_bar'], 'DERIVED section E (after trims, A1 dT)'),
    }
    L.append('F. U330 tap %.3f (R330/R331 %.1fk), tau %.3f ms, R332 %.0fk / R333 %.1fk: trip %.2f bar abs, band +/- %.2f bar -> %.2f..%.2f '
             '(firmware %.1f, MEOP %.1f)' % (k_tap, ra / 1e3, tau * 1e3, rc / 1e3, rd / 1e3, p_trip / BAR, dp / BAR, (p_trip - dp) / BAR,
                                            (p_trip + dp) / BAR, fw_abort / BAR, meop / BAR))
    # --------------------------------------------------------------------------- G P_mid comparator (U570), absolute sensor
    pm_trip_target, pm_rel_target = 10.0e5 + P_STD, 9.0e5 + P_STD   # keep the v2.9 levels (gauge at sea level) as absolute levels
    v_t, v_r = vsig(pm_trip_target), vsig(pm_rel_target)
    # non-inverting hysteresis: input R573 (series), feedback R574 from the open-collector output (pull-up R575 to +5V_SNS)
    r573 = 4.75e3
    best = None
    for r574 in e96_all(100e3, 10e6):
        h = V_EXC * r573 / (r573 + r574)   # approx. hysteresis at the input referred to the pin swing (pull-up R575 << R574)
        if abs(h - (v_t - v_r)) / (v_t - v_r) < 0.03:
            best = r574 if best is None or abs(h - (v_t - v_r)) < abs(V_EXC * r573 / (r573 + best) - (v_t - v_r)) else best
    r574 = best
    vref_pm = v_t - (v_t - v_r) * 0.0     # threshold referred: rising trip happens when V_in reaches v_ref + (V_ref - 0) * R573/R574 ~
    # exact rising/falling with output low (0 V) / high (5 V): Vth_rise = Vref (1 + R573/R574); Vth_fall = Vref (1 + R573/R574) - 5 R573/R574
    kk = r573 / r574
    vref_needed = v_t / (1 + kk)
    best = None
    for r577 in (1.74e3, 1.78e3, 1.82e3, 1.87e3, 1.91e3, 1.96e3, 2.00e3, 2.05e3, 2.10e3):
        for r576 in e96_all(5e3, 20e3):
            v_ref = V_EXC * r577 / (r576 + r577)
            if best is None or abs(v_ref - vref_needed) < abs(best[2] - vref_needed):
                best = (r576, r577, v_ref)
    r576, r577, v_ref_pm = best
    v_rise = v_ref_pm * (1 + kk)
    v_fall = v_rise - V_EXC * kk
    out['G_pmid_comparator_U570'] = {
        'values': tag({'R573': r573, 'R574': r574, 'R576': r576, 'R577': r577}, 'DESIGN (E96)'),
        'trip_rise_Pa_abs': tag(round(p_of(v_rise), 0), 'DERIVED (v2.9 levels 10.0 / 9.0 bar g kept as 11.01 / 10.01 bar abs)'),
        'release_Pa_abs': tag(round(p_of(v_fall), 0), 'DERIVED'),
        'band_Pa': tag(round(vio / (V_EXC * 0.8 / c1_fs), 0), 'DERIVED comparator Vio only; the transducer zero (after trim) adds '
                                                             'the thermal term of section E at the BL-08 temperature (MISSING)'),
        'oi_bleed_detect_low_threshold_option': tag(
            'a threshold near 2.0 bar abs would separate a both-stuck-open bleed (P_mid 3-4 bar abs, Mechanical ESTIMATE) from a '
            'vented mid passage (~1 bar abs). With the 140 bar span: Vio band +/- %.2f bar plus the thermal zero %.3f bar/C typ '
            '(DATASHEET) x the MISSING BL-08 temperature excursion: for a 60 C excursion +/- %.1f bar. NOT adopted: the separation '
            'is not shown; candidate only (see the v2.11 OI-BLEED-DETECT entry)' % (vio / (V_EXC * 0.8 / c1_fs) / BAR,
                                                                                    0.01 * c1_fs / BAR / (100 / 1.8),
                                                                                    0.01 * c1_fs / BAR / (100 / 1.8) * 60),
            'DERIVED'),
    }
    L.append('G. U570 R574 %.0fk, R576/R577 %.2fk/%.2fk: rise %.2f bar abs, fall %.2f bar abs' % (r574 / 1e3, r576 / 1e3, r577 / 1e3,
                                                                                        p_of(v_rise) / BAR, p_of(v_fall) / BAR))
    # ---------------------------------------------------------------------------------------------------------- H mass
    cable_g_per_m = 10.0                    # ASSUMED (30 AWG 4-core shielded; the sheet gives no mass)
    each = c1['mass_g_excl_cable'] + 0.914 * cable_g_per_m
    out['H_mass'] = tag({'per_channel_g': round(each, 1), 'body_g': c1['mass_g_excl_cable'], 'cable_g': round(0.914 * cable_g_per_m, 1),
                         'P_feed_plus_P_mid_g': round(2 * each, 1), 'carried_g': 100.0, 'delta_kg': round((2 * each - 100.0) / 1000, 3),
                         'note': 'the ECU-side conditioning (2 x INA333 + RG/REF parts, < 1 g each, DERIVED) sits on the ECU '
                                 'board; the 0.9 m integral cable may be shortened to the harness break (TO-VERIFY with Kulite)'},
                        'DATASHEET body 4 g; cable ASSUMED 10 g/m (MISSING)')
    L.append('H. P_feed + P_mid %.1f g vs 100 g carried -> %+.3f kg (cable mass ASSUMED)' % (2 * each, (2 * each - 100.0) / 1000))
    out['summary'] = L
    # ------------------------------------------------------------------------------------------------- I SIL header
    hdr = (
        '// GENERATED by calc/v2p11/pc_transducer_v3.py - DO NOT EDIT. Pc measurement chains for the SIL hardware model. Units SI.\n'
        '// namespace ovp : the v2.10 chain (TE M3234-000005-070BG 0-70 bar g on the 0.30 m sense line; U330 tap 0.2401), values as\n'
        '//                 generated by calc/pc_transducer_v2.py (kept unchanged: v2.10 comparator runs and the stand static reference).\n'
        '// namespace ovp3: the v2.11 flight chain (LEAD CHANGELOG 205): %s on the seat passage,\n'
        '//                 INA333 bridge conditioning (DESIGN), U330 tap 1/2 re-derived for the 140 bar abs span.\n'
        '#pragma once\n'
        'namespace sil {\n'
        'namespace ovp {\n'
        'constexpr double kPcFs_Pa = 7000000.0;       // [DATASHEET] TE M3234-000005-070BG 0-70 bar g\n'
        'constexpr double kTripPa_g = 3146517.6;      // [DERIVED] nominal trip, gauge (32.48 bar abs at sea level)\n'
        'constexpr double kBandPa = 157925.8;         // [DERIVED] worst-case circuit band +/- (Vio, Iib, 0.1 %% resistors)\n'
        'constexpr double kTau_s = 0.005283;          // [DERIVED] tap RC (R330 || R331) x C330\n'
        '}  // namespace ovp\n'
        'namespace ovp3 {\n'
        'constexpr double kPcFsAbs_Pa = %.1f;    // [DATASHEET] Kulite XTL-190 2000 psia range = 137.9 bar abs (absolute)\n'
        'constexpr double kZeroFrac = 0.10, kSpanFrac = 0.80;   // [DESIGN] V_SIG = Vexc (0.10 + 0.80 p_abs / FS) after the trims\n'
        'constexpr double kTripPaAbs = %.1f;     // [DERIVED] U330 nominal trip, ABSOLUTE\n'
        'constexpr double kBandPa = %.1f;          // [DERIVED] worst-case circuit band +/-\n'
        'constexpr double kTau_s = %.6f;           // [DERIVED] (R330 || R331) x C330 = %.0f x %.0f nF\n'
        'constexpr double kInaFc_Hz = %.1f;          // [DERIVED] INA333 bandwidth at G %.1f (DATASHEET 3.5 kHz at G = 100)\n'
        'constexpr double kVsat_V = 4.95;              // [DATASHEET] INA333 output swing (V+) - 0.05 V at 5 V\n'
        'constexpr double kAafFc_Hz = %.1f;          // [DESIGN] 12.7k || 4.02k x 22 nF anti-alias (unchanged)\n'
        'constexpr double kPmidTripAbs_Pa = %.1f, kPmidRelAbs_Pa = %.1f;   // [DERIVED] U570 rise / fall, ABSOLUTE\n'
        '}  // namespace ovp3\n'
        '}  // namespace sil\n' % (c1['part_proposed'][:40], c1_fs, p_trip, dp, tau, rth, c330 * 1e9, bw, g_e96, f_aaf,
                                   p_of(v_rise), p_of(v_fall)))
    out['I_header'] = {'file': os.path.relpath(a.header, ROOT)}
    if not a.no_header:
        open(a.header, 'w').write(hdr)
        out['I_header']['sha256_16'] = sha16(a.header)
    json.dump(out, open(a.out, 'w'), indent=1)
    txt = a.out.replace('.json', '.txt')
    open(txt, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print('wrote', os.path.relpath(a.out, ROOT), sha16(a.out), 'header', out['I_header'])


if __name__ == '__main__':
    main()
