#!/usr/bin/env python3
"""Mini pintle servo search for the in-line crank-slider, v1 (Electronics, 2026-10-12).

LEAD request 2026-10-12: find a mini pintle servo so that the in-line crank-slider can stay (fallback: centred
servo + jackshaft + fork, more backlash). Requirements as stated by the lead:
  R1 body envelope <= 31 (L) x 16 (W) x 30 (H, along the shaft) mm          [LEAD/MECH]
  R2 torque >= 1 N m (screening number)                                       [LEAD]
  R3 enough torque for the peak needle force through the crank, with margin   [LEAD; loads MECH 2026-10-12]
  R4 speed and bandwidth for the throttle loop, checked against gnc.json      [LEAD -> gnc.json v1 requirements.throttle]
  R5 resolution for the 10 um backlash / positioning target                   [LEAD; COMB v2 position_resolution]
  R6 runs on the available rail (2S direct: 6.6 V BATT_LOW .. 8.4 V full)     [electronics v2.3]
  R7 tolerates the head-top temperature incl. soak-back after shutdown        [LEAD; combustion.json thermal_and_loads]
  R8 datasheet-level evidence; price TO-QUOTE (shipping to DK-6400)           [LEAD]
Inputs read (not hard-coded) where an interface carries them:
  interfaces/combustion.json v2 : valves_and_actuators.pintle_actuator, plant_model_valve_to_Pc, operating_points
                                  (tank MEOP, tank pressure range, throttle_map_csv), gas_path.injector seat diameter,
                                  thermal_and_loads (searched for a head-top temperature)
  interfaces/gnc.json v1        : requirements.throttle (t10_90_s, slew_min_Fmax_per_s, resolution_frac,
                                  pc_loop_bandwidth_Hz)
  MECH message 2026-10-12       : stem 4.0 mm, seal friction 25 N (ASSUMED), closing spring F0 121.7 N + 5 N/mm
                                  (Electronics pintle_linkage_v2 sizing), 28 mm link, case limit 50 C, design 1.5 x 224 N
Model (analysis only; no hardware data exists for any of these parts in this design):
  crank-slider : exact in-line kinematics (crank r, link L, angle phi from top dead centre); TOG = closed at phi_c
                 near the dead centre with 5 deg lost motion below it (tension link in a slot), SYM = stroke centred on
                 the 90 deg position
  needle loads : closing spring + pressure (seated -> stem force blended over the first 0.1 mm, as pintle_linkage_v2)
                 + Coulomb seal friction; crank efficiency 0.90 ASSUMED
  servo        : DC-motor model: torque = Ts (u - w/w_nl), Ts = listed stall torque, w_nl = listed no-load speed
                 (linear torque-speed line ASSUMED), output inertia from an ASSUMED 10 ms mechanical time constant at
                 7.4 V (5-20 ms sensitivity), PD position loop with an ASSUMED 2 deg proportional band and zeta 0.7,
                 4 ms command latency (333 Hz frame + 1 ms ASSUMED)
  thrust       : quasi-steady throttle map F(lift, P_tank) of Combustion (SIM), no chamber or fuel-mode lag
GNC criterion for a thrust step dF: actuator-limited t10-90 <= max(t10_90_s, 0.8 |dF| / (slew_min_Fmax_per_s * 500 N))
(first-order + rate-limit reading of gnc.json: t10-90 for small steps, slew >= 2 F_max/s for large ones).
Outputs: results/pintle_mini_servo_v1.{json,txt} and results/plots/pintle_mini_servo_v1.png
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts_db as pdb  # noqa: E402

ENGINE_ROOT = os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine')
COMB = os.path.join(ENGINE_ROOT, 'interfaces', 'combustion.json')
GNCF = os.path.join(ENGINE_ROOT, 'interfaces', 'gnc.json')
OUT = os.path.join(HERE, '..', 'results')
ACCESS = '2026-10-12'
KGCM = pdb.KGCM_TO_NM
P_AMB = 101325.0
F_MAX = 500.0                      # [REQ] throttle_frac = F / 500 N (gnc.json conventions)


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


def resolve(path):
    if os.path.exists(path):
        return path, 'interface path'
    alt = path.replace('/home/claude/work/shared-fallback/engine/02-combustion/', '/home/claude/work/combustion/')
    if os.path.exists(alt):
        return alt, ('FALLBACK: the path named in combustion.json is missing in the hub; Combustion work-dir copy '
                     'read as data (open interface issue: publish 02-combustion/data/v2 to the hub)')
    raise FileNotFoundError(path)


# ------------------------------------------------------------------------------------------------ inputs
C = json.load(open(COMB))
G = json.load(open(GNCF))
PA = C['valves_and_actuators']['pintle_actuator']
STROKE = PA['stroke_m']['v']
T_FULL_REQ = PA['full_stroke_time_s']['v']
X_RES_REQ = PA['position_resolution_m']['v']
P_MEOP = C['operating_points']['tank_MEOP_Pa']['v']
P_RANGE = C['operating_points']['tank_pressure_range_Pa']['v']
D_SEAT = C['gas_path']['injector']['seat_diameter_m']['v']
GT = G['requirements']['throttle']
T1090 = GT['t10_90_s']['v']
SLEW = GT['slew_min_Fmax_per_s']['v'] * F_MAX
RES_FRAC = GT['resolution_frac']['v']
PC_BW = GT['pc_loop_bandwidth_Hz']['v']
SMALL_BW = 8.0                     # [COMB v1 via gnc.json note] pintle actuator small-signal bandwidth >= 8 Hz
MAP_PATH, MAP_NOTE = resolve(C['operating_points']['throttle_map_csv'])
THERMAL_KEYS = list(C['thermal_and_loads'].keys())
HEAD_T = [k for k in THERMAL_KEYS if 'head' in k.lower() or 'servo' in k.lower() or 'injector' in k.lower()]

MECH = {
    'stem_d_m': {'v': 4.0e-3, 'tag': 'MECH msg 2026-10-12 (stem through the seal)'},
    'F_seal_N': {'v': 25.0, 'tag': 'MECH msg 2026-10-12, ASSUMED Coulomb seal friction'},
    'F0_N': {'v': 121.7, 'tag': 'MECH msg 2026-10-12 = Electronics pintle_linkage_v2 (F0 >= |stem force at MEOP| + friction + 10 N)'},
    'k_N_per_m': {'v': 5000.0, 'tag': 'MECH msg 2026-10-12 / pintle_linkage_v2 ASSUMED 5 N/mm'},
    'link_m': {'v': 28.0e-3, 'tag': 'MECH mechanical.json v1 REQUEST (28 mm link)'},
    'x_stop_m': {'v': 4.2e-3, 'tag': 'DESIGN open stop 0.2 mm beyond the stroke (SIL PintleMechParams)'},
    'F_crack_meop_N': {'v': 224.0, 'tag': 'MECH msg 2026-10-12 (peak opening force, crack-open at MEOP)'},
    'F_design_N': {'v': 336.0, 'tag': 'MECH msg 2026-10-12 proposal 1.5 x 224 N'},
    'envelope_mm': {'v': [31.0, 16.0, 30.0], 'tag': 'LEAD/MECH 2026-10-12 L x W x H (H along the shaft)'},
    'case_limit_C': {'v': 50.0, 'tag': 'MECH msg 2026-10-12 (unless the part says otherwise)'},
    'link_plane_offset_m': {'v': 6.7e-3, 'tag': 'MECH msg 2026-10-12 (link plane ~6.7 mm beyond the spline face)'},
}
ETA = 0.90                         # [ASSUMED] crank + pins efficiency
LOST_DEG = 5.0                     # [DESIGN] lost motion below phi_c (tension link in a slot)
V_NOM, V_DEG, V_MAX = 7.4, 6.6, 8.4    # [DESIGN] pintle plug voltage nominal / BATT_LOW degraded / 2S full charge
TAU_M = 0.010                      # [ASSUMED] servo mechanical time constant at 7.4 V (SIL basis 9.8 ms SB-2292SG)
PB_DEG = 2.0                       # [ASSUMED] proportional band
ZETA = 0.7                         # [ASSUMED]
LAT = 0.004                        # [DATASHEET 333 Hz frame 3.0 ms + ASSUMED 1 ms]
US_PER_DEG_ASSUMED = 10.0          # [ASSUMED] where the travel per pulse is not published (range 8-12)

# ------------------------------------------------------------------------------------------------ candidates
SRC = {
    'HV69_LIND': 'https://lindinger.at/en/RC-ELECTRONICS/Servos-Accessories/Servos-Digital-High-Voltage/MKS-HV69-Digital-Servo/9788343',
    'HV69_EXF': 'https://extremeflightrc.com/products/mks-hv69-high-torque-micro-servo',
    'HV69_ALOFT': 'https://alofthobbies.com/products/mks-hv69-wing-servo-10-2-kg-141-7-oz-in-0-10-sec-wide-voltage',
    'HV69_GATOR': 'https://gator-rc.com/mks-hv69-mini-digital-super-torque-high-voltage-servo-with-metal-gears',
    'HV69_SDB': 'https://servodatabase.com/servo/mks/hv69',
    'HV6130H_SDB': 'https://servodatabase.com/servo/mks/hv6130h',
    'SPM_CHART': 'https://www.horizonhobby.com/on/demandware.static/-/Sites-horizon-master/default/Manuals/SPM%20Servo%20Chart%20-%20Updated.pdf',
    'CLS2875H_GATOR': 'https://gator-rc.com/kingmax-mini-metal-gear-servo-digital-hv-cls2875h',
    'S30M_GATOR': 'https://www.gator-rc.com/products/kingmax-coreless-mini-servo-digital-steel-gears-50g-30kg-cm-s30m',
    'SV1260_MH': 'https://modelhelicopters.co.uk/products/savox-hv-digital-mini-tail-servo-15kg-0-048s-8-4v-sav-sv1260mg',
    'X151208_OE': 'https://openelab.io/es/products/kst-x151208-mini-corelss-servo',
    'HV120_LIND': 'https://lindinger.at/en/RC-ELECTRONICS/Servos-Accessories/Servos-Digital-Brushless-Low-High-Voltage/CHASERVO-HV120-12mm-Servo-HV-28kg-Brushless-Servo/9801475',
    'HV120H_LIND': 'https://lindinger.at/en/RC-ELECTRONICS/Servos-Accessories/Servos-Digital-Brushless-Low-High-Voltage/CHASERVO-HV120H-12mm-Servo-HV-28kg-Brushless-Servo/9801476',
    'HV150_LIND': 'https://lindinger.at/en/RC-ELECTRONICS/Servos-Accessories/Servos-Digital-Brushless-Low-High-Voltage/CHASERVO-HV150-15mm-24kg-HV-Brushless-Servo/9801478',
}
OZIN = 0.00706155                  # N m per oz-in

CANDS = [
    {'id': 'MKS HV69', 'pn': 'MKS HV69, MKS no. S0022012 (Lindinger item 9788343)', 'motor': 'coreless',
     'dims_mm': [29.0, 13.0, 28.7], 'mass_g': 21.0,
     'V': [4.8, 6.0, 7.4, 8.2], 'T_kgcm': [6.0, 7.5, 9.2, 10.2], 's60': [0.17, 0.13, 0.11, 0.10],
     'torque_kind': 'stall torque (Extreme Flight, Aloft: "Stall Torque"); speed at no load',
     'V_range': [4.8, 8.2], 'V_note': 'CONFLICT: 3.7-8.2 V (Extreme Flight, Aloft), 4.8-8.2 V (Gator) vs 4.8-8.4 V table / 3.8-8.4 V text (Lindinger) and 3.7-8.4 V (servodatabase); Extreme Flight/Aloft also label the top torque point 8.4 V. Design uses the 8.2 V rating -> TO-CONFIRM with MKS',
     'T_op_C': [-10.0, 60.0], 'T_note': 'Extreme Flight, Aloft and servodatabase (retailer copies of MKS data); TO-CONFIRM with MKS',
     'deadband_us': 1.0, 'us_per_deg': None, 'travel': 'not published (TO-CONFIRM)', 'pulse': '1520 us neutral, 333 Hz',
     'spline': '6 mm, 25 T (Extreme Flight, Aloft; Gator: 25-tooth arm)', 'stall_A': None,
     'case': 'not stated by MKS retailers (servodatabase: plastic)', 'gears': 'metal alloy (servodatabase: steel)',
     'pot': 'direct-drive potentiometer', 'ears': 'not published in any listing (wing brackets included) -> MKS drawing or measured sample',
     'price': [{'vendor': 'Lindinger (AT)', 'v': 62.99, 'cur': 'EUR', 'note': 'catalogue incl. 20 % AT VAT, plus shipping; in stock 2026-10-12; NOT a DK-6400 quote'},
               {'vendor': 'Aloft Hobbies / Extreme Flight (US)', 'v': 62.50, 'cur': 'USD', 'note': 'listed sold out 2026-10-12'}],
     'src': [SRC['HV69_LIND'], SRC['HV69_EXF'], SRC['HV69_ALOFT'], SRC['HV69_GATOR'], SRC['HV69_SDB']]},
    {'id': 'MKS HV6130H', 'pn': 'MKS HV6130H (MKS no. S0022010)', 'motor': 'coreless',
     'dims_mm': [round(1.181 * 25.4, 1), round(0.394 * 25.4, 1), round(1.173 * 25.4, 1)], 'mass_g': round(0.81 * 28.35, 1),
     'V': [6.0, 7.4, 8.4], 'T_kgcm': [round(83.0 * OZIN / KGCM, 2), round(105.5 * OZIN / KGCM, 2), round(112.5 * OZIN / KGCM, 2)],
     's60': [0.14, 0.11, 0.10], 'torque_kind': 'listed torque (servodatabase)', 'V_range': [6.0, 8.4], 'V_note': 'servodatabase',
     'T_op_C': None, 'T_note': 'not listed', 'deadband_us': 1.0, 'us_per_deg': None, 'travel': 'not listed',
     'pulse': '1520 us neutral, 333 Hz', 'spline': '24 T', 'stall_A': [1.9, 2.7], 'case': 'aluminium', 'gears': 'steel',
     'pot': 'potentiometer', 'ears': 'not listed', 'price': [], 'src': [SRC['HV6130H_SDB']]},
    {'id': 'Spektrum A4030', 'pn': 'SPMSA4030', 'motor': 'coreless brushed',
     'dims_mm': [28.0, 12.7, 27.4], 'mass_g': 20.0, 'V': [6.0], 'T_kgcm': [6.0], 's60': [0.10],
     'torque_kind': 'listed torque at 6.0 V only', 'V_range': None, 'V_note': 'voltage range not stated in the chart',
     'T_op_C': None, 'T_note': 'not listed', 'deadband_us': None, 'us_per_deg': None, 'travel': 'not listed', 'pulse': '',
     'spline': '23 T', 'stall_A': None, 'case': '', 'gears': 'metal', 'pot': '', 'ears': '', 'price': [], 'src': [SRC['SPM_CHART']]},
    {'id': 'Chaservo HV120', 'pn': 'Chaservo HV120 / HV120H (CHA-HV120, Lindinger 9801475/9801476)', 'motor': '4-pole brushless',
     'dims_mm': [30.0, 12.0, 35.0], 'mass_g': 37.0, 'V': [4.8, 6.0, 7.4, 8.4], 'T_kgcm': [18.0, 22.0, 25.0, 28.0],
     's60': [0.16, 0.13, 0.11, 0.09],
     'torque_kind': 'listed "holding" torque; the same pages also list "output torque" 10-18 kg cm (15.0 at 7.4 V), unexplained -> conservative variant evaluated',
     'T_kgcm_conservative': {'7.4': 15.0, '8.4': 18.0}, 'V_range': [4.8, 8.4], 'V_note': 'Lindinger',
     'T_op_C': None, 'T_note': 'not listed', 'deadband_us': None, 'us_per_deg': None, 'travel': 'not listed (pulse 500-2500 us)',
     'pulse': '1520 us / 333 Hz, 500-2500 us', 'spline': '6.0 mm, 25 T', 'stall_A': None, 'case': 'aluminium (HV120H page)',
     'gears': 'metal', 'pot': 'potentiometer', 'ears': 'not listed',
     'price': [{'vendor': 'Lindinger (AT)', 'v': 99.99, 'cur': 'EUR', 'note': 'catalogue incl. VAT plus shipping; NOT a DK-6400 quote'}],
     'src': [SRC['HV120_LIND'], SRC['HV120H_LIND']]},
    {'id': 'KingMax CLS2875H', 'pn': 'KingMax CLS2875H', 'motor': 'coreless', 'dims_mm': [35.0, 15.0, 29.0], 'mass_g': 28.0,
     'V': [5.0, 6.0, 7.4, 8.4], 'T_kgcm': [7.6, 8.4, 10.0, 11.0], 's60': [0.12, 0.10, 0.08, 0.07], 'torque_kind': 'listed torque',
     'V_range': [5.0, 8.4], 'V_note': 'Gator', 'T_op_C': [-10.0, 50.0], 'T_note': 'Gator', 'deadband_us': 2.0,
     'us_per_deg': 1400.0 / 126.0, 'travel': '+/-63 deg at 800-2200 us', 'pulse': '1520 us / 330 Hz', 'spline': '25 T',
     'stall_A': None, 'case': 'CNC aluminium centre', 'gears': 'metal', 'pot': '', 'ears': '',
     'price': [{'vendor': 'Gator RC (US)', 'v': 36.95, 'cur': 'USD', 'note': 'listing'}], 'src': [SRC['CLS2875H_GATOR']]},
    {'id': 'Savox SV-1260MG', 'pn': 'Savox SV-1260MG', 'motor': 'coreless', 'dims_mm': [35.0, 15.0, 30.7], 'mass_g': 40.0,
     'V': [6.0, 7.4, 8.4], 'T_kgcm': [8.0, 12.0, 15.0], 's60': [0.065, 0.055, 0.048], 'torque_kind': 'listed torque',
     'V_range': [6.0, 8.4], 'V_note': 'modelhelicopters.co.uk', 'T_op_C': [-10.0, 50.0], 'T_note': 'listing',
     'deadband_us': 4.0, 'us_per_deg': 10.0, 'travel': '100 deg at 1000-2000 us, ~165 deg at 800-2200 us', 'pulse': '1500 us, 333 Hz',
     'spline': '25 T (6 mm)', 'stall_A': [4.0, 4.9, 5.6], 'case': 'aluminium', 'gears': 'metal', 'pot': '', 'ears': '',
     'price': [{'vendor': 'modelhelicopters.co.uk (UK)', 'v': 75.99, 'cur': 'GBP', 'note': 'listing'}], 'src': [SRC['SV1260_MH']]},
    {'id': 'KST X15-1208', 'pn': 'KST X15-1208', 'motor': 'coreless', 'dims_mm': [35.5, 15.0, 32.5], 'mass_g': 40.0,
     'V': [6.0, 7.4, 8.4], 'T_kgcm': [9.8, 12.0, 13.5], 's60': [0.10, 0.08, 0.07], 'torque_kind': 'listed torque',
     'V_range': [6.0, 8.4], 'V_note': 'openelab', 'T_op_C': [-10.0, 65.0], 'T_note': 'openelab', 'deadband_us': None,
     'us_per_deg': 12.0, 'travel': '+/-50 deg at 900-2100 us', 'pulse': '1520 us / 333 Hz', 'spline': '6 mm, 25 T',
     'stall_A': None, 'case': 'aluminium', 'gears': 'hardened steel', 'pot': 'potentiometer', 'ears': '',
     'price': [{'vendor': 'openelab (ships from CN)', 'v': 115.95, 'cur': 'EUR', 'note': 'incl. VAT, out of stock EU'}],
     'src': [SRC['X151208_OE']]},
    {'id': 'KingMax S30M', 'pn': 'KingMax S30M', 'motor': 'coreless', 'dims_mm': [36.0, 15.0, 33.0], 'mass_g': 50.5,
     'V': [5.0, 6.0, 7.4, 8.4], 'T_kgcm': [8.8, 9.3, 11.0, 12.0], 's60': [0.15, 0.13, 0.10, 0.09],
     'torque_kind': 'listed rated torque (stall 30 kg cm and max working 15.2 kg cm at 7.4 V also listed)',
     'V_range': [5.0, 8.4], 'V_note': 'Gator', 'T_op_C': [-10.0, 50.0], 'T_note': 'Gator', 'deadband_us': 2.0,
     'us_per_deg': 1400.0 / 126.0, 'travel': '+/-63 deg at 800-2200 us', 'pulse': '', 'spline': '25 T', 'stall_A': None,
     'case': 'CNC aluminium', 'gears': 'steel', 'pot': '', 'ears': '',
     'price': [{'vendor': 'Gator RC (US)', 'v': 75.95, 'cur': 'USD', 'note': 'listing'}], 'src': [SRC['S30M_GATOR']]},
    {'id': 'Chaservo HV150', 'pn': 'Chaservo HV150 (CHA-HV150, Lindinger 9801478)', 'motor': '4-pole brushless',
     'dims_mm': [35.5, 15.0, 30.0], 'mass_g': 51.0, 'V': [4.8, 6.0, 7.4, 8.4], 'T_kgcm': [20.0, 25.0, 30.0, 33.0],
     's60': [0.15, 0.12, 0.10, 0.09], 'torque_kind': 'listed torque; page also lists "output torque" 12-20 kg cm, unexplained',
     'V_range': [4.8, 8.4], 'V_note': 'Lindinger', 'T_op_C': None, 'T_note': 'not listed', 'deadband_us': None,
     'us_per_deg': None, 'travel': 'not listed', 'pulse': '', 'spline': '6.0 mm, 25 T', 'stall_A': None, 'case': '',
     'gears': 'metal', 'pot': '', 'ears': '',
     'price': [{'vendor': 'Lindinger (AT)', 'v': 109.99, 'cur': 'EUR', 'note': 'catalogue incl. VAT'}], 'src': [SRC['HV150_LIND']]},
]
BASE = pdb.SB2292SG
CANDS.append({'id': 'Savox SB-2292SG (current baseline)', 'pn': 'Savox SB-2292SG', 'motor': 'brushless',
              'dims_mm': BASE['dims_mm']['v'], 'mass_g': BASE['mass_kg']['v'] * 1e3, 'V': [6.0, 7.4, 8.4],
              'T_kgcm': [BASE['torque_kgcm']['v'][k] for k in ('6.0', '7.4', '8.4')],
              's60': [BASE['speed_s_per_60deg']['v'][k] for k in ('6.0', '7.4', '8.4')], 'torque_kind': 'parts_db (lower set)',
              'V_range': BASE['voltage_V']['v'], 'V_note': 'parts_db', 'T_op_C': BASE['op_temp_C']['v'], 'T_note': 'parts_db',
              'deadband_us': 1.0, 'us_per_deg': 10.0, 'travel': '100 deg at 1000-2000 us', 'pulse': '', 'spline': '25 T',
              'stall_A': [7.5, 9.2], 'case': 'aluminium', 'gears': 'steel', 'pot': '', 'ears': 'standard flange',
              'price': [{'vendor': 'Lindinger (AT)', 'v': 119.99, 'cur': 'EUR', 'note': 'parts_db'}], 'src': ['parts_db.py']})


def servo_pts(c, V, conservative=False):
    Vs = c['V']
    T = [t * KGCM for t in c['T_kgcm']]
    if conservative and 'T_kgcm_conservative' in c:
        cv = c['T_kgcm_conservative']
        T = [float(cv.get(f'{v:.1f}', t / KGCM * (15.0 / 25.0))) * KGCM for v, t in zip(Vs, T)]
    w = [math.radians(60.0) / s for s in c['s60']]
    Vc = min(max(V, Vs[0]), Vs[-1])          # no extrapolation beyond the listed points
    return float(np.interp(Vc, Vs, T)), float(np.interp(Vc, Vs, w))


def pmax(c, V, conservative=False):
    Ts, w = servo_pts(c, V, conservative)
    return Ts * w / 4.0


# ------------------------------------------------------------------------------------------------ throttle map
def load_map():
    rows = list(csv.DictReader(l for l in open(MAP_PATH) if not l.startswith('#')))
    by = {}
    for r in rows:
        if r['lift_m'] in ('', None):
            continue
        P = float(r['P_tank_Pa'])
        if abs(float(r['D_port_m']) - 0.025) > 1e-6:     # lift map is independent of the port diameter in v2
            continue
        by.setdefault(P, []).append((float(r['lift_m']), float(r['F_N']), float(r['frac'])))
    for P in by:
        by[P].sort()
    return by


MAP = load_map()
PGRID = sorted(MAP)


class ThrustMap:
    def __init__(s, P):
        pts = MAP[P]
        s.P = P
        s.h = np.array([0.0] + [p[0] for p in pts])
        s.F = np.array([0.0] + [p[1] for p in pts])
        s.frac = {round(p[2], 4): p[0] for p in pts}

    def F_of(s, h):
        if h <= s.h[-1]:
            return float(np.interp(h, s.h, s.F))
        sl = (s.F[-1] - s.F[-2]) / (s.h[-1] - s.h[-2])
        return float(s.F[-1] + sl * (h - s.h[-1]))

    def dFdh(s, h):
        i = int(np.clip(np.searchsorted(s.h, h) - 1, 0, len(s.h) - 2))
        return float((s.F[i + 1] - s.F[i]) / (s.h[i + 1] - s.h[i]))

    def lift(s, frac):
        k = round(frac, 4)
        if k in s.frac:
            return s.frac[k]
        return float(np.interp(frac * F_MAX, s.F, s.h))     # between map points: linear in thrust


# ------------------------------------------------------------------------------------------------ kinematics
class Crank:
    """In-line crank-slider: s(phi) = r cos(phi) + sqrt(L^2 - r^2 sin^2 phi), phi from top dead centre.
    Lift x = s(phi0) - s(phi) for phi >= phi0 (needle pulled open by a tension link); below phi0 lost motion."""

    def __init__(s, law, r, phi0_deg, L):
        s.law, s.r, s.L = law, r, L
        s.phi0 = math.radians(phi0_deg)
        s.s0 = s._s(s.phi0)
        s.name = (f'TOG r={r * 1e3:.1f}mm phi_c={phi0_deg:.0f}deg' if law == 'TOG'
                  else f'SYM r={r * 1e3:.2f}mm +/-{90 - phi0_deg:.0f}deg')

    def _s(s, phi):
        return s.r * math.cos(phi) + math.sqrt(s.L ** 2 - (s.r * math.sin(phi)) ** 2)

    def x(s, phi):
        return max(0.0, s.s0 - s._s(phi)) if phi > s.phi0 else 0.0

    def dxdphi(s, phi):
        if phi <= s.phi0:
            return 0.0
        q = math.sqrt(s.L ** 2 - (s.r * math.sin(phi)) ** 2)
        return s.r * math.sin(phi) * (1.0 + s.r * math.cos(phi) / q)

    def phi_of(s, x):
        if x <= 0:
            return s.phi0
        lo, hi = s.phi0, math.pi
        if s.x(hi) < x:
            return float('nan')
        for _ in range(60):
            m = 0.5 * (lo + hi)
            if s.x(m) < x:
                lo = m
            else:
                hi = m
        return 0.5 * (lo + hi)

    def travel_deg(s, x):
        return math.degrees(s.phi_of(x) - s.phi0) + LOST_DEG


def make_cranks():
    L = MECH['link_m']['v']
    out = []
    for r in (2.5e-3, 3.0e-3, 3.5e-3, 4.0e-3, 4.5e-3, 5.0e-3):
        for pc in (5.0, 10.0, 15.0, 20.0):
            c = Crank('TOG', r, pc, L)
            if not math.isnan(c.phi_of(STROKE)):
                out.append(c)
    for h in (30.0, 40.0, 50.0):
        out.append(Crank('SYM', STROKE / (2 * math.sin(math.radians(h))), 90.0 - h, L))
    return out


# ------------------------------------------------------------------------------------------------ loads
A_STEM = math.pi / 4 * MECH['stem_d_m']['v'] ** 2
A_SEAT = math.pi / 4 * D_SEAT ** 2


def needle_force(x, P_tank, vdir):
    """Force on the needle the link must overcome; + = closing. vdir: +1 opening, -1 closing, 0 static (no friction)."""
    dp = max(0.0, P_tank - P_AMB)
    f_seat = dp * (A_SEAT - A_STEM)
    f_open = -dp * A_STEM
    w = min(1.0, x / 1e-4)
    return (1 - w) * f_seat + w * f_open + MECH['F0_N']['v'] + MECH['k_N_per_m']['v'] * x + MECH['F_seal_N']['v'] * vdir


def torque_profile(cr, P, vdir=+1, x_hi=STROKE, n=400):
    xs = np.linspace(1e-6, x_hi, n)
    T = []
    for x in xs:
        phi = cr.phi_of(x)
        F = needle_force(x, P, vdir)
        T.append(F * cr.dxdphi(phi) / ETA if F * vdir >= 0 else F * cr.dxdphi(phi) * ETA)
    return xs, np.array(T)


def work(P, x0, x1, n=400):
    xs = np.linspace(x0, x1, n)
    F = np.array([needle_force(x, P, +1 if x1 > x0 else -1) for x in xs])
    return float(np.trapezoid(F, xs) / ETA) if x1 > x0 else float(-np.trapezoid(F, xs))


# ------------------------------------------------------------------------------------------------ servo dynamics
class Servo:
    def __init__(s, c, V, tau_m=TAU_M, pb_deg=PB_DEG, conservative=False):
        s.Ts, s.wnl = servo_pts(c, V, conservative)
        T74, w74 = servo_pts(c, 7.4, conservative)
        s.J = tau_m * T74 / w74
        s.pb = math.radians(pb_deg)
        wn = math.sqrt(s.Ts / (s.pb * s.J))
        s.kd = max(0.0, 2 * ZETA * wn * s.J / s.Ts - 1.0 / s.wnl)


def simulate(cr, sv, P, phi_start, cmd, tmax, dt=1e-4, x_stop=MECH['x_stop_m']['v']):
    """cmd(t) -> target crank angle (applied after LAT). Returns arrays t, x, phi, Tm."""
    n = int(tmax / dt)
    t = np.arange(n) * dt
    X = np.zeros(n); PH = np.zeros(n); TM = np.zeros(n)
    phi, om = phi_start, 0.0
    phi_stop = cr.phi_of(x_stop) if not math.isnan(cr.phi_of(x_stop)) else math.pi
    for i in range(n):
        tgt = cmd(max(0.0, t[i] - LAT))
        u = float(np.clip((tgt - phi) / sv.pb - sv.kd * om, -1.0, 1.0))
        Tm = sv.Ts * (u - om / sv.wnl)
        x = cr.x(phi)
        d = cr.dxdphi(phi)
        v = d * om
        if x > 0:
            F = needle_force(x, P, 0) + MECH['F_seal_N']['v'] * math.tanh(v / 1e-3)
            Text = F * d
            Tl = Text / ETA if Text * om >= 0 else Text * ETA
        else:
            Tl = 0.0
        om += (Tm - Tl) / sv.J * dt
        phi += om * dt
        if phi >= phi_stop and om > 0:
            phi, om = phi_stop, 0.0
        if phi <= cr.phi0 - math.radians(LOST_DEG + 3.0) and om < 0:   # servo end stop beyond the lost motion (ASSUMED)
            phi, om = cr.phi0 - math.radians(LOST_DEG + 3.0), 0.0
        X[i], PH[i], TM[i] = cr.x(phi), phi, Tm
    return t, X, PH, TM


T_PRE = 0.30                        # [s] settle at the start point before the step (servo holds its load with droop)


def step_metrics(cr, sv, P, tm, f0, f1, tmax=0.6):
    """Thrust step through the quasi-steady map. The servo first settles at the start lift (it holds the needle load
    with a proportional-band droop), then the command steps. t10-90 is taken between the settled start and end
    thrust (the static droop is a gain error the closed Pc loop removes; reported separately)."""
    x0, x1 = tm.lift(f0), tm.lift(f1)
    p0, p1 = cr.phi_of(x0), cr.phi_of(x1)
    t, X, PH, TM = simulate(cr, sv, P, p0, lambda tt: p0 if tt < T_PRE else p1, T_PRE + tmax)
    F = np.array([tm.F_of(x) for x in X])
    k0 = int(np.argmax(t >= T_PRE + LAT)) - 1           # last sample before the actuator sees the step
    Fa = float(F[k0])
    Fb = float(np.mean(F[t >= t[-1] - 0.05]))
    dF = Fb - Fa
    tt = t[k0:] - T_PRE                                  # time from the command
    g = (F[k0:] - Fa) / dF if abs(dF) > 1e-9 else np.zeros_like(tt)
    if np.any(g >= 0.1) and np.any(g >= 0.9):
        t10, t90 = float(tt[np.argmax(g >= 0.1)]), float(tt[np.argmax(g >= 0.9)])
    else:
        t10 = t90 = float('nan')
    t1090 = t90 - t10
    dF_cmd = tm.F_of(x1) - tm.F_of(x0)
    treq = max(T1090, 0.8 * abs(dF_cmd) / SLEW)
    ok = bool(t1090 == t1090 and t1090 <= treq)
    return {'from': f0, 'to': f1, 'dF_cmd_N': round(dF_cmd, 1), 'dF_act_N': round(dF, 1),
            'x0_mm': round(x0 * 1e3, 3), 'x1_mm': round(x1 * 1e3, 3),
            'droop_start_N': round(Fa - tm.F_of(x0), 1), 'droop_end_N': round(Fb - tm.F_of(x1), 1),
            't10_s': round(t10, 4), 't90_from_cmd_s': round(t90, 4), 't10_90_s': round(t1090, 4),
            'slew_avg_N_s': round(0.8 * abs(dF) / t1090, 0) if t1090 > 0 else None,
            't_req_s': round(treq, 4), 'margin': round(treq / t1090, 2) if t1090 > 0 else None,
            'pass': ok, 'peak_motor_torque_Nm': round(float(np.max(np.abs(TM[k0:]))), 3)}


def full_stroke(cr, sv, P, opening=True, tmax=1.2):
    """Full stroke from the seated (lost-motion) position to the 4.0 mm command, or back. Time from the command to
    99 % of the travel actually reached (settled), plus the settled lift (droop below 4.0 mm under load)."""
    pa = cr.phi0 - math.radians(LOST_DEG) if opening else cr.phi_of(STROKE)
    pb = cr.phi_of(STROKE) if opening else cr.phi0 - math.radians(LOST_DEG)
    t, X, PH, TM = simulate(cr, sv, P, pa, lambda tt: pa if tt < T_PRE else pb, T_PRE + tmax)
    k0 = int(np.argmax(t >= T_PRE)) - 1
    xa = float(X[k0]); xb = float(np.mean(X[t >= t[-1] - 0.05]))
    g = (X[k0:] - xa) / (xb - xa) if abs(xb - xa) > 1e-9 else np.zeros(len(X) - k0)
    i = int(np.argmax(g >= 0.99))
    return {'t_s': round(float(t[k0 + i] - T_PRE), 4) if g[i] >= 0.99 else None, 'x_end_mm': round(xb * 1e3, 3)}


def sine_response(cr, sv, P, tm, frac, ampl_frac, f_hz, cycles=6):
    """Needle response to a sinusoidal thrust demand (via the quasi-static map). Returns gain, phase [deg]."""
    h0 = tm.lift(frac)
    dFdh = tm.dFdh(h0)
    Ax = ampl_frac * F_MAX / dFdh
    p0 = cr.phi_of(h0)
    tmax = cycles / f_hz
    cmd = lambda tt: p0 if tt < T_PRE else cr.phi_of(max(1e-6, h0 + Ax * math.sin(2 * math.pi * f_hz * (tt - T_PRE))))
    t, X, PH, TM = simulate(cr, sv, P, p0, cmd, T_PRE + tmax, dt=1e-4)
    t = t - T_PRE
    sel = t >= (cycles - 3) / f_hz
    tt = t[sel]; xx = X[sel] - np.mean(X[sel])
    s_ = np.sin(2 * math.pi * f_hz * tt); c_ = np.cos(2 * math.pi * f_hz * tt)
    a = 2 * np.mean(xx * s_); b = 2 * np.mean(xx * c_)
    return {'frac': frac, 'ampl_frac_of_Fmax': ampl_frac, 'f_Hz': f_hz, 'needle_ampl_um': round(Ax * 1e6, 1),
            'gain': round(float(math.hypot(a, b) / Ax), 3), 'phase_deg': round(float(math.degrees(math.atan2(b, a))), 1)}


# ------------------------------------------------------------------------------------------------ evaluation
def static_checks(c, cr):
    res = {'crank': cr.name, 'travel_deg': round(cr.travel_deg(STROKE), 1)}
    cases = {'bench_P0': P_AMB, 'P3.5MPa': 3.5e6, 'P5.0MPa': 5.0e6, 'P5.65MPa': P_RANGE[1], 'MEOP': P_MEOP}
    Tpk = {}
    for k, P in cases.items():
        xs, T = torque_profile(cr, P, +1)
        Tpk[k] = round(float(T.max()), 3)
    res['T_peak_open_Nm'] = Tpk
    Tflight = max(Tpk['P3.5MPa'], Tpk['P5.0MPa'], Tpk['P5.65MPa'], Tpk['MEOP'])
    res['T_design_Nm'] = round(max(Tflight, Tpk['bench_P0']), 3)
    for V in (V_DEG, V_NOM, V_MAX):
        Ts, _ = servo_pts(c, V)
        res[f'margin_flight_{V}V'] = round(Ts / Tflight, 2)
        res[f'margin_bench_{V}V'] = round(Ts / Tpk['bench_P0'], 2)
    # crack-open torque at the MECH 336 N design force
    phi_c = cr.phi_of(1e-5)
    res['T_at_336N_crack_Nm'] = round(MECH['F_design_N']['v'] * cr.dxdphi(phi_c) / ETA, 3)
    # runaway into the open stop and the stall force available at the needle at the stop (structural design input)
    pst = cr.phi_of(MECH['x_stop_m']['v'])
    Ts84, _ = servo_pts(c, V_MAX)
    res['F_link_runaway_at_stop_N'] = round(Ts84 / cr.dxdphi(pst) + 0.0, 0) if not math.isnan(pst) else None
    # resolution
    usd = c['us_per_deg'] or US_PER_DEG_ASSUMED
    db = c['deadband_us'] if c['deadband_us'] is not None else 3.0
    dphi = math.radians(db / usd)
    rows = []
    for P in (3.5e6, 5.0e6, 5.5e6):
        tm = ThrustMap(P)
        for f in (0.125, 0.2, 0.5, 1.0):
            h = tm.lift(f)
            dx = cr.dxdphi(cr.phi_of(h)) * dphi
            rows.append({'P_tank_MPa': P / 1e6, 'frac': f, 'lift_mm': round(h * 1e3, 3), 'dx_um': round(dx * 1e6, 2),
                         'dF_N': round(tm.dFdh(h) * dx, 2), 'dF_frac_of_local': round(tm.dFdh(h) * dx / (f * F_MAX), 4)})
    res['resolution'] = {'deadband_us': db, 'us_per_deg': round(usd, 2),
                         'basis': 'listed' if c['us_per_deg'] else f'ASSUMED {US_PER_DEG_ASSUMED} us/deg',
                         'rows': rows,
                         'max_dx_um': max(r['dx_um'] for r in rows), 'max_dF_N': max(r['dF_N'] for r in rows)}
    # backlash preload: net closing load on the link never reverses (closing motion, friction against the spring)
    xs = np.linspace(0, STROKE, 200)
    net_min = min(needle_force(x, P_MEOP, -1) for x in xs)
    res['net_closing_load_min_N'] = round(net_min, 1)
    # side (radial) load on the servo output: the link tension, which in the in-line crank-slider is the needle force
    # divided by cos(beta), beta = link angle (<= asin(r/L)); it acts at the link plane beyond the spline face.
    # No candidate publishes an output-shaft radial rating -> UNKNOWN; outboard bearing or measured rating needed.
    f_op = 0.0
    for P in cases.values():
        for x in np.linspace(0.0, STROKE, 200):
            phi = cr.phi_of(x)
            beta = math.asin(min(1.0, cr.r * math.sin(phi) / cr.L))
            f_op = max(f_op, needle_force(x, P, +1) / math.cos(beta))
    off = MECH['link_plane_offset_m']['v']
    f_st = res['F_link_runaway_at_stop_N']
    res['servo_side_load'] = {
        'F_link_max_operating_N': round(f_op, 1), 'M_at_spline_face_operating_Nm': round(f_op * off, 2),
        'F_link_stall_into_stop_N': f_st, 'M_at_spline_face_stall_Nm': round(f_st * off, 2) if f_st else None,
        'overhang_m': off, 'tag': 'DERIVED from MECH loads; overhang MECH',
        'rating': 'no output-shaft radial-load rating published for any candidate (UNKNOWN): support the crank on its '
                  'own bearings (torque-only coupling to the spline) or measure a rating'}
    if cr.law == 'TOG':
        # the slider can move towards the seat by at most s(0) - s(phi_c) (top dead centre): a lost-motion slot longer
        # than this means the servo can never load the seat, whatever the closed command within +/-phi_c of TDC
        res['tdc_push_limit_mm'] = round((cr._s(0.0) - cr.s0) * 1e3, 3)
    return res


def evaluate():
    out = {'id': 'pintle_mini_servo_v1', 'version': 'v1', 'date': ACCESS, 'owner': 'electronics',
           'inputs': {'combustion.json': {'version': C['version'], 'sha256_16': sha(COMB)},
                      'gnc.json': {'version': G['version'], 'sha256_16': sha(GNCF)},
                      'throttle_map': {'path': MAP_PATH, 'note': MAP_NOTE, 'sha256_16': sha(MAP_PATH)},
                      'MECH': MECH},
           'requirements': {
               'R1_envelope_mm': MECH['envelope_mm'],
               'R2_torque_Nm': {'v': 1.0, 'tag': 'LEAD screening number'},
               'R3_torque_margin': {'v': {'flight_7.4V': 1.5, 'flight_6.6V': 1.2, 'bench_7.4V': 1.2},
                                    'tag': 'DESIGN (Electronics): stall torque / peak quasi-static demand over the stroke'},
               'R4_gnc': {'t10_90_s': T1090, 'slew_N_s': SLEW, 'pc_loop_bandwidth_Hz': PC_BW,
                          'tag': 'gnc.json v1 requirements.throttle', 'criterion': 't10-90 <= max(t10_90_s, 0.8 dF / slew)'},
               'R4_comb_full_stroke_s': {'v': T_FULL_REQ, 'tag': 'combustion.json v2 pintle_actuator (tag v1, 50 mm/s)'},
               'R4_comb_small_signal_Hz': {'v': SMALL_BW, 'tag': 'combustion.json v1 via gnc.json note'},
               'R5_resolution_m': {'v': X_RES_REQ, 'tag': 'combustion.json v2 position_resolution (10 um)'},
               'R5_gnc_resolution_N': {'v': RES_FRAC * F_MAX, 'tag': 'gnc.json resolution_frac x 500 N'},
               'R6_rail_V': {'v': [V_DEG, V_MAX], 'tag': 'electronics v2.3 2S direct (BATT_LOW .. full charge)'},
               'R7_temperature': {'v': 'head top incl. soak-back', 'combustion_thermal_keys_with_head_or_servo': HEAD_T,
                                  'tag': 'combustion.json v2 thermal_and_loads has no head-top / servo-mount temperature -> UNKNOWN'},
           },
           'energy_bound': {}, 'candidates': []}
    # energy bound: minimum time for any linkage = stroke work / max mechanical power (linear torque-speed line)
    tm5 = ThrustMap(5.0e6)
    W = {'full_0_4mm_bench': work(P_AMB, 0.0, STROKE), 'full_0_4mm_MEOP': work(P_MEOP, 0.0, STROKE),
         'full_0_4mm_P5MPa': work(5.0e6, 0.0, STROKE), 'full_0_4mm_P3.5MPa': work(3.5e6, 0.0, STROKE),
         '20_100pct_P5MPa': work(5.0e6, tm5.lift(0.2), tm5.lift(1.0)),
         '20_100pct_P3.5MPa': work(3.5e6, ThrustMap(3.5e6).lift(0.2), ThrustMap(3.5e6).lift(1.0))}
    out['energy_bound']['stroke_work_J'] = {k: round(v, 4) for k, v in W.items()}
    out['energy_bound']['note'] = ('P_max = Ts w_nl / 4 is the peak shaft power of a DC motor with a linear torque-speed '
                                   'line; no linkage can make a stroke faster than W / P_max (servodatabase quotes the '
                                   'same shaft power, e.g. HV69 0.91-2.62 W)')
    for c in CANDS:
        L, Wd, H = c['dims_mm']
        env = [L <= 31.0, Wd <= 16.0, H <= 30.0]
        e = {'id': c['id'], 'pn': c['pn'], 'motor': c['motor'], 'dims_mm': c['dims_mm'], 'mass_g': c['mass_g'],
             'envelope_pass': all(env), 'envelope_excess_mm': [round(max(0, a - b), 1) for a, b in zip(c['dims_mm'], (31, 16, 30))],
             'torque_kind': c['torque_kind'], 'V_rated': c['V'], 'T_kgcm': c['T_kgcm'], 's60': c['s60'],
             'V_range': c['V_range'], 'V_note': c['V_note'], 'T_op_C': c['T_op_C'], 'T_note': c['T_note'],
             'deadband_us': c['deadband_us'], 'travel': c['travel'], 'spline': c['spline'], 'stall_A': c['stall_A'],
             'case': c['case'], 'gears': c['gears'], 'ears': c['ears'], 'price': c['price'], 'src': c['src'],
             'tag': 'DATASHEET (vendor listings of manufacturer data, accessed 2026-10-12)'}
        Ts74, w74 = servo_pts(c, 7.4)
        e['Ts_7.4V_Nm'] = round(Ts74, 3)
        e['R2_ge_1Nm'] = {f'{V}V': round(servo_pts(c, V)[0], 3) for V in (V_DEG, V_NOM, V_MAX)}
        e['Pmax_W'] = {f'{V}V': round(pmax(c, V), 2) for V in (V_DEG, V_NOM, V_MAX)}
        e['t_min_bound_s'] = {k: round(W[k] / pmax(c, V_NOM), 3) for k in W}
        e['rail_ok'] = (c['V_range'] is not None and c['V_range'][0] <= V_DEG and c['V_range'][1] >= V_MAX)
        e['temp_rating_ok_vs_50C'] = (c['T_op_C'] is not None and c['T_op_C'][1] >= MECH['case_limit_C']['v'])
        out['candidates'].append(e)
    return out


def detailed(c, out_c, conservative=False, tau_list=(TAU_M,)):
    """Crank sweep + dynamics for one candidate."""
    rows = []
    for cr in make_cranks():
        st = static_checks(c, cr)
        rows.append(st)
    # pick: torque margins met, travel <= 120 deg (TO-CONFIRM), then the best GNC margin (evaluated below)
    feas = [r for r in rows if r['margin_flight_7.4V'] >= 1.5 and r['margin_flight_6.6V'] >= 1.2
            and r['margin_bench_7.4V'] >= 1.2 and r['travel_deg'] <= 120.0]
    out_c['crank_sweep'] = rows
    out_c['crank_feasible'] = [r['crank'] for r in feas]
    cranks = {cr.name: cr for cr in make_cranks()}
    steps = [(0.125, 1.0), (0.2, 1.0), (0.25, 1.0), (0.2, 0.5), (0.5, 1.0), (0.5, 0.55), (0.95, 1.0),
             (1.0, 0.2), (1.0, 0.125), (0.5, 0.2), (0.55, 0.5)]
    dyn = []
    out_c['crank_dyn'] = [n for n in out_c['crank_feasible'] if ('phi_c=10deg' in n or 'phi_c=15deg' in n or n.startswith('SYM'))]
    for name in out_c['crank_dyn']:
        cr = cranks[name]
        for V in (V_NOM, V_DEG):
            sv = Servo(c, V, conservative=conservative)
            rec = {'crank': name, 'V': V, 'steps': []}
            for P in (3.5e6, 5.0e6, 5.5e6):
                tm = ThrustMap(P)
                for f0, f1 in steps:
                    m = step_metrics(cr, sv, P, tm, f0, f1)
                    m['P_tank_MPa'] = P / 1e6
                    rec['steps'].append(m)
            rec['all_steps_pass'] = all(s['pass'] for s in rec['steps'])
            rec['min_margin'] = min(s['margin'] for s in rec['steps'] if s['margin'] is not None)
            rec['worst_step'] = min(rec['steps'], key=lambda s: s['margin'] if s['margin'] is not None else 0)
            rec['full_open'] = {k: full_stroke(cr, sv, P, True) for k, P in
                                  (('MEOP', P_MEOP), ('P5.0MPa', 5.0e6), ('P3.5MPa', 3.5e6), ('bench', P_AMB))}
            rec['full_close'] = {k: full_stroke(cr, sv, P, False) for k, P in (('MEOP', P_MEOP), ('bench', P_AMB))}
            dyn.append(rec)
    out_c['dynamics'] = dyn
    return out_c


def main():
    os.makedirs(os.path.join(OUT, 'plots'), exist_ok=True)
    out = evaluate()
    byid = {c['id']: c for c in CANDS}
    detail_ids = ['MKS HV69', 'Chaservo HV120', 'KingMax CLS2875H']
    for e in out['candidates']:
        if e['id'] in detail_ids:
            detailed(byid[e['id']], e)
    # HV120 with the conservative "output torque" reading
    hv120c = {'id': 'Chaservo HV120 (output-torque reading)'}
    out['hv120_conservative'] = detailed(byid['Chaservo HV120'], hv120c, conservative=True)

    # select the HV69 crank (DESIGN rule): travel <= 100 deg (servo travel unpublished -> keep it moderate), all GNC
    # steps pass at 6.6 V (slew reading), t10-90 <= 0.15 s for every step at 7.4 V (strict reading of t10_90_s);
    # among those the largest bench torque margin (smallest radius, finest resolution)
    hv = next(e for e in out['candidates'] if e['id'] == 'MKS HV69')
    best = None
    for name in hv['crank_dyn']:
        d74 = next(d for d in hv['dynamics'] if d['crank'] == name and d['V'] == V_NOM)
        d66 = next(d for d in hv['dynamics'] if d['crank'] == name and d['V'] == V_DEG)
        st = next(r for r in hv['crank_sweep'] if r['crank'] == name)
        strict74 = all(x['t10_90_s'] <= T1090 for x in d74['steps'])
        d74['strict_all_steps_le_t1090'] = strict74
        d66['strict_all_steps_le_t1090'] = all(x['t10_90_s'] <= T1090 for x in d66['steps'])
        ok = (st['travel_deg'] <= 100.0 and d66['all_steps_pass'] and strict74)
        key = (ok, st['margin_bench_7.4V'], -st['resolution']['max_dx_um'])
        if best is None or key > best[0]:
            best = (key, name)
    hv['selected_crank'] = best[1] if best else None
    hv['selection_rule'] = ('DESIGN: travel <= 100 deg (servo travel unpublished), all GNC steps pass at 6.6 V, every '
                            'step t10-90 <= 0.15 s at 7.4 V (strict reading); then the largest bench torque margin')

    # sensitivity of the selected HV69 option: tau_m, pressure terms, torque/speed scatter
    if best:
        cr = {c_.name: c_ for c_ in make_cranks()}[best[1]]
        sens = []
        for tau in (0.005, 0.010, 0.020):
            for V in (V_NOM, V_DEG):
                sv = Servo(byid['MKS HV69'], V, tau_m=tau)
                worst = None
                for P in (3.5e6, 5.0e6, 5.5e6):
                    tm = ThrustMap(P)
                    for f0, f1 in ((0.2, 1.0), (0.125, 1.0), (0.5, 0.55), (1.0, 0.2)):
                        m = step_metrics(cr, sv, P, tm, f0, f1)
                        if worst is None or (m['margin'] or 0) < (worst['margin'] or 0):
                            worst = dict(m, P_tank_MPa=P / 1e6)
                sens.append({'tau_m_s': tau, 'V': V, 'worst': worst})
        hv['sensitivity_tau_m'] = sens
        sv = Servo(byid['MKS HV69'], V_NOM)
        sines = []
        for P, frac in ((5.0e6, 1.0), (5.0e6, 0.5), (5.0e6, 0.2), (3.5e6, 1.0)):
            tm = ThrustMap(P)
            for amp in (0.02, 0.05):
                for f in (PC_BW, 5.0, SMALL_BW):
                    r_ = sine_response(cr, sv, P, tm, frac, amp, f)
                    r_['P_tank_MPa'] = P / 1e6
                    sines.append(r_)
        hv['small_signal'] = sines

    # verdict per requirement for the in-envelope candidates
    verdict = []
    for e in out['candidates']:
        v = {'id': e['id'], 'R1_envelope': e['envelope_pass'], 'R2_ge_1Nm_at_7.4V': e['R2_ge_1Nm'][f'{V_NOM}V'] >= 1.0}
        if 'dynamics' in e and e.get('crank_dyn'):
            sel = e.get('selected_crank') or e['crank_dyn'][0]
            if e['id'] != 'MKS HV69':
                # best crank by min margin at 7.4 V
                sel = max(e['crank_dyn'], key=lambda n: next(d for d in e['dynamics'] if d['crank'] == n and d['V'] == V_NOM)['min_margin'])
            d74 = next(d for d in e['dynamics'] if d['crank'] == sel and d['V'] == V_NOM)
            d66 = next(d for d in e['dynamics'] if d['crank'] == sel and d['V'] == V_DEG)
            st = next(r for r in e['crank_sweep'] if r['crank'] == sel)
            v.update({'crank': sel, 'R3_torque_margin_flight_7.4V': st['margin_flight_7.4V'],
                      'R3_torque_margin_bench_7.4V': st['margin_bench_7.4V'], 'R3_pass': True,
                      'R4_gnc_all_steps_7.4V': d74['all_steps_pass'], 'R4_gnc_min_margin_7.4V': d74['min_margin'],
                      'R4_gnc_all_steps_6.6V': d66['all_steps_pass'], 'R4_gnc_min_margin_6.6V': d66['min_margin'],
                      'R4_comb_full_open_MEOP_s': d74['full_open']['MEOP']['t_s'], 'R4_comb_full_open_P3.5_s': d74['full_open']['P3.5MPa']['t_s'],
                      'R4_comb_full_stroke_pass': (d74['full_open']['MEOP']['t_s'] or 9) <= T_FULL_REQ,
                      'R5_max_dx_um': st['resolution']['max_dx_um'], 'R5_pass': st['resolution']['max_dx_um'] <= X_RES_REQ * 1e6,
                      'R5_max_dF_N': st['resolution']['max_dF_N']})
        elif 'crank_sweep' in e:
            v.update({'crank': None, 'R3_pass': False, 'note': 'no crank meets the torque margins within 120 deg travel'})
        v['R6_rail_6.6_8.4V'] = e['rail_ok']
        v['R7_rated_ge_50C'] = e['temp_rating_ok_vs_50C']
        v['R7_head_top_environment'] = 'UNKNOWN (no head-top temperature in combustion.json v2)'
        verdict.append(v)
    out['verdict'] = verdict

    json.dump(out, open(os.path.join(OUT, 'pintle_mini_servo_v1.json'), 'w'), indent=1, default=float)
    write_txt(out)
    plot(out, byid)


def write_txt(out):
    L = []
    p = L.append
    p('pintle_mini_servo_v1  (Electronics 2026-10-12)  combustion.json %s  gnc.json %s' % (C['version'], G['version']))
    p('throttle map: %s' % MAP_NOTE)
    p('MECH loads: F0 %.1f N + %.0f N/mm, seal %.0f N, stem %.1f mm, seat %.1f mm (combustion.json); MEOP %.1f MPa'
      % (MECH['F0_N']['v'], MECH['k_N_per_m']['v'] / 1e3, MECH['F_seal_N']['v'], MECH['stem_d_m']['v'] * 1e3, D_SEAT * 1e3, P_MEOP / 1e6))
    p('GNC: t10-90 <= %.2f s, slew >= %.0f N/s, Pc loop >= %.1f Hz | COMB: full stroke %.2f s, %.0f um, small-signal %.0f Hz'
      % (T1090, SLEW, PC_BW, T_FULL_REQ, X_RES_REQ * 1e6, SMALL_BW))
    p('stroke work [J]: ' + ', '.join(f'{k} {v}' for k, v in out['energy_bound']['stroke_work_J'].items()))
    p('')
    p('%-36s %-18s %-5s %7s %7s %7s %-7s %-12s %s' % ('candidate', 'L x W x H mm', 'env', 'Ts7.4', 'Pmax7.4', 'tmin_full', 'rail', 'T_op C', 'price'))
    for e in out['candidates']:
        pr = '; '.join(f"{q['v']} {q['cur']} {q['vendor']}" for q in e['price']) or 'not retrieved'
        p('%-36s %-18s %-5s %7.3f %7.2f %7.3f %-7s %-12s %s' % (
            e['id'][:36], 'x'.join(f'{d:g}' for d in e['dims_mm']), 'OK' if e['envelope_pass'] else 'FAIL',
            e['Ts_7.4V_Nm'], e['Pmax_W'][f'{V_NOM}V'], e['t_min_bound_s']['full_0_4mm_MEOP'],
            'OK' if e['rail_ok'] else 'CHECK', str(e['T_op_C']), pr))
    for e in out['candidates']:
        if 'crank_sweep' not in e:
            continue
        p('')
        p(f"== {e['id']}  crank sweep (travel incl. {LOST_DEG:.0f} deg lost motion; torque margins = stall / peak demand)")
        p('%-30s %6s %8s %8s %8s %8s %8s %8s %9s' % ('crank', 'trav', 'Tbench', 'TMEOP', 'm_fl7.4', 'm_fl6.6', 'm_bn7.4', 'dx_um', 'F_stop_N'))
        for r in e['crank_sweep']:
            p('%-30s %6.1f %8.3f %8.3f %8.2f %8.2f %8.2f %8.2f %9s' % (
                r['crank'], r['travel_deg'], r['T_peak_open_Nm']['bench_P0'], r['T_peak_open_Nm']['MEOP'],
                r['margin_flight_7.4V'], r['margin_flight_6.6V'], r['margin_bench_7.4V'], r['resolution']['max_dx_um'],
                r['F_link_runaway_at_stop_N']))
        if e.get('dynamics'):
            p('dynamics (feasible cranks): GNC steps at P_tank 3.5/5.0/5.5 MPa, worst margin = t_req / t10-90')
            for d in e['dynamics']:
                w = d['worst_step']
                fo = d['full_open']
                p('  %-30s %.1f V all_pass=%-5s min_margin %.2f worst %s->%s @%.1f MPa t10-90 %.3f s (req %.3f) | full open MEOP %s s, P3.5 %s s, bench %s s (end %.2f mm) | close MEOP %s s'
                  % (d['crank'], d['V'], d['all_steps_pass'], d['min_margin'], w['from'], w['to'], w['P_tank_MPa'],
                     w['t10_90_s'], w['t_req_s'], fo['MEOP']['t_s'], fo['P3.5MPa']['t_s'], fo['bench']['t_s'],
                     fo['bench']['x_end_mm'], d['full_close']['MEOP']['t_s']))
    hv = next(e for e in out['candidates'] if e['id'] == 'MKS HV69')
    p('')
    p('HV69 selected crank: %s' % hv.get('selected_crank'))
    if hv.get('selected_crank'):
        d = next(d for d in hv['dynamics'] if d['crank'] == hv['selected_crank'] and d['V'] == V_NOM)
        st = next(r for r in hv['crank_sweep'] if r['crank'] == hv['selected_crank'])
        sl = st['servo_side_load']
        p('  static: travel %.1f deg incl. %.0f deg lost motion; peak opening torque bench %.3f / MEOP %.3f N m; crank torque at the '
          '336 N crack load %.3f N m; min net closing load %.1f N (link never reverses)'
          % (st['travel_deg'], LOST_DEG, st['T_peak_open_Nm']['bench_P0'], st['T_peak_open_Nm']['MEOP'],
             st['T_at_336N_crack_Nm'], st['net_closing_load_min_N']))
        p('  servo side load (link tension at %.1f mm beyond the spline face): operating max %.1f N -> %.2f N m; stall into the '
          '4.2 mm stop %s N -> %s N m; rating UNKNOWN (not published)'
          % (sl['overhang_m'] * 1e3, sl['F_link_max_operating_N'], sl['M_at_spline_face_operating_Nm'],
             sl['F_link_stall_into_stop_N'], sl['M_at_spline_face_stall_Nm']))
        if 'tdc_push_limit_mm' in st:
            p('  TDC push limit %.3f mm: a lost-motion slot longer than this (DESIGN >= 0.15 mm) keeps the servo off the seat'
              % st['tdc_push_limit_mm'])
        p('  steps at 7.4 V:')
        for s in d['steps']:
            p('   P %.1f MPa %5.3f->%5.3f dF %6.1f N  t10-90 %.3f s  req %.3f  margin %5.2f  %s  avg slew %s N/s  droop %+.1f/%+.1f N'
              % (s['P_tank_MPa'], s['from'], s['to'], s['dF_cmd_N'], s['t10_90_s'], s['t_req_s'], s['margin'] or 0,
                 'PASS' if s['pass'] else 'FAIL', s['slew_avg_N_s'], s['droop_start_N'], s['droop_end_N']))
        p('  sensitivity tau_m:')
        for s in hv.get('sensitivity_tau_m', []):
            w = s['worst']
            p('   tau_m %.3f s  %.1f V  worst %s->%s @%.1f MPa t10-90 %.3f (req %.3f) margin %.2f' % (
                s['tau_m_s'], s['V'], w['from'], w['to'], w['P_tank_MPa'], w['t10_90_s'], w['t_req_s'], w['margin'] or 0))
        p('  small-signal (needle gain/phase to a sinusoidal thrust demand, model-internal servo loop ASSUMED):')
        for s in hv.get('small_signal', []):
            p('   P %.1f MPa frac %.3f +/-%.0f %%  %.1f Hz  needle %.0f um  gain %.2f  phase %.0f deg' % (
                s['P_tank_MPa'], s['frac'], s['ampl_frac_of_Fmax'] * 100, s['f_Hz'], s['needle_ampl_um'], s['gain'], s['phase_deg']))
    hc = out['hv120_conservative']
    p('')
    p('Chaservo HV120 with the "output torque" reading (15 kg cm at 7.4 V): feasible cranks %s' % hc.get('crank_feasible'))
    for d in hc.get('dynamics', []):
        p('  %-30s %.1f V all_pass=%-5s min_margin %.2f | full open MEOP %s s' % (d['crank'], d['V'], d['all_steps_pass'], d['min_margin'], d['full_open']['MEOP']['t_s']))
    p('')
    p('VERDICT per requirement')
    for v in out['verdict']:
        p('  ' + json.dumps(v))
    open(os.path.join(OUT, 'pintle_mini_servo_v1.txt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def plot(out, byid):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('WARNING: matplotlib not available in this interpreter; plot skipped (run with /opt/engine-venv/bin/python)')
        return
    hv = next(e for e in out['candidates'] if e['id'] == 'MKS HV69')
    if not hv.get('selected_crank'):
        return
    cr = {c_.name: c_ for c_ in make_cranks()}[hv['selected_crank']]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for P, lab in ((P_AMB, 'bench (no pressure)'), (3.5e6, '3.5 MPa'), (5.0e6, '5.0 MPa'), (P_MEOP, 'MEOP 7.0 MPa')):
        xs, T = torque_profile(cr, P, +1)
        ax[0].plot(xs * 1e3, T, label=lab)
    for V, ls in ((V_NOM, '-'), (V_DEG, '--')):
        ax[0].axhline(servo_pts(byid['MKS HV69'], V)[0], color='k', ls=ls, lw=0.8, label=f'HV69 stall {V} V')
    ax[0].set_xlabel('needle lift [mm]'); ax[0].set_ylabel('servo torque demand, opening [N m]')
    ax[0].set_title('HV69 + ' + cr.name); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
    for P in (3.5e6, 5.0e6):
        tm = ThrustMap(P)
        for V, ls in ((V_NOM, '-'), (V_DEG, '--')):
            sv = Servo(byid['MKS HV69'], V)
            x0, x1 = tm.lift(0.2), tm.lift(1.0)
            p0_, p1_ = cr.phi_of(x0), cr.phi_of(x1)
            t, X, PH, TM = simulate(cr, sv, P, p0_, lambda tt, a=p0_, b=p1_: a if tt < T_PRE else b, T_PRE + 0.5)
            sel = t >= T_PRE
            ax[1].plot(t[sel] - T_PRE, [tm.F_of(x) for x in X[sel]], ls=ls, label=f'20->100 %, {P / 1e6:.1f} MPa, {V} V')
    tt = np.linspace(0, 0.5, 200)
    ax[1].plot(tt, np.clip(100 + SLEW * (tt - LAT), 100, 500), 'k:', lw=1, label='GNC min slew 1000 N/s')
    ax[1].set_xlabel('time from command [s]'); ax[1].set_ylabel('quasi-steady thrust [N]'); ax[1].legend(fontsize=7)
    ax[1].grid(alpha=0.3); ax[1].set_title('actuator-limited thrust step (no fuel-mode lag)')
    names = [e['id'] for e in out['candidates']]
    pm = [e['Pmax_W'][f'{V_NOM}V'] for e in out['candidates']]
    cols = ['tab:green' if e['envelope_pass'] else 'tab:gray' for e in out['candidates']]
    ax[2].barh(range(len(names)), pm, color=cols)
    W = out['energy_bound']['stroke_work_J']['full_0_4mm_MEOP']
    ax[2].axvline(W / T_FULL_REQ, color='r', ls='--', lw=1, label=f'needed for 0-4 mm in {T_FULL_REQ} s at MEOP ({W / T_FULL_REQ:.1f} W)')
    ax[2].set_yticks(range(len(names))); ax[2].set_yticklabels(names, fontsize=7)
    ax[2].set_xlabel('peak shaft power Ts w_nl/4 at 7.4 V [W]; green: fits 31x16x30 mm'); ax[2].legend(fontsize=7)
    ax[2].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'plots', 'pintle_mini_servo_v1.png'), dpi=110)


if __name__ == '__main__':
    main()
