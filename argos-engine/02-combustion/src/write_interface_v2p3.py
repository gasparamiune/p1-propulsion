"""combustion.json v2.3 = v2.2 as published + the pintle needle-force / seat / seal review (lead requests 2026-10-12).

Lead requests: (1) confirm Mechanical pintle v2 (3 mm stem): (a) injector/throttle map unchanged? (b) seat load acceptable for material and
leak-tightness (polymer creep/extrusion if a polymer)? (c) spring-energised seal for a 3 mm rod in N2O at MEOP; (2) the same at the S3 spring
baseline (lead decision: S3_PTFE15mu20, T0 0.30 N m, k 0.10 N m/rad; Mechanical pintle_inline_v34_v2p2.json seat loads 350/385/500 N).
Only the keys in CHANGED are added or edited; every other value is the v2.2 content (asserted below).
usage: python write_interface_v2p3.py <v2.2 as-published json> <needle_force_bounds_v2p3.json> <pintle_spring_window_v2p3.json>
                                      <mechanical pintle_inline_v34_v2p2.json> <out>
"""
from __future__ import annotations
import sys, os, json, math, hashlib, copy

V22, NF, WIN, MECH, OUT = sys.argv[1:6]
raw22 = open(V22, 'rb').read()
assert hashlib.sha256(raw22).hexdigest()[:16] == '660df2c526025ede', 'v2.2 as-published file changed'
J = json.loads(raw22)
J0 = copy.deepcopy(J)
nf = json.load(open(NF))
win = json.load(open(WIN))
mraw = open(MECH, 'rb').read()
mech = json.loads(mraw)
sha = lambda b: hashlib.sha256(b).hexdigest()[:16]
assert mech['baseline']['config'] == 'S3_PTFE15mu20_plainpins'


def T(v, tag, **kw):
    d = {'v': v, 'tag': tag}
    d.update(kw)
    return d


def _find(o, key):
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


from CoolProp.CoolProp import PropsSI
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import injector as INJ                                                   # own module: pintle_area(h)

# ------------------------------------------------------------------ inputs and derived constants
TB_N2O = PropsSI('T', 'P', 101325.0, 'Q', 0, 'NitrousOxide')            # K (CoolProp)
_he = json.load(open(os.path.join(os.path.dirname(os.path.abspath(V22)), 'headend_thermal_v2.json')))
_rows = [(cn, vn, v['T_head']['soak_peak_K']) for cn, c in _he['cases'].items() for vn, v in c['variants'].items() if v.get('T_head')]
_flight = [r for r in _rows if 'ground' not in r[0]]
_ground = [r for r in _rows if 'ground' in r[0]]
TH_CAD = [r[2] for r in _flight if 'disc2mm' in r[1] and 'hg_x1|' in r[1] and 'head_0.44kg' in r[1]]
TH_D2 = [r[2] for r in _flight if 'disc2mm' in r[1]]
TH_BARE = [r[2] for r in _flight if 'bare' in r[1]]
TH_G_CAD = [r[2] for r in _ground if 'disc2mm' in r[1] and 'hg_x1|' in r[1] and 'head_0.44kg' in r[1]]
TH_G_D2 = [r[2] for r in _ground if 'disc2mm' in r[1]]
TH_G_BARE = [r[2] for r in _ground if 'bare' in r[1]]
A_STOP = INJ.pintle_area(4.2e-3) * 1e6
A_SEAT_MM2 = math.pi / 4 * 5.5 ** 2
DV_BONNET = math.pi / 4 * (4.0 ** 2 - 3.0 ** 2) * 26.0 / 1e3
G22 = J['thermal_and_loads']['head_end_bc']['v']['pintle_needle']['stem_conductance_W_K']
G3 = G22 * (3.0 / 4.0) ** 2
P_TANK_MEOP = J['operating_points']['tank_MEOP_Pa']['v']
RELIEF = 7.5e6                                                           # trapped-liquid relief set (combustion.json v2.2 / mechanical.json v1)
PROOF = 1.5 * P_TANK_MEOP                                                # ASSUMED proof factor 1.5 (as for the chamber)
ALPHA = math.radians(15.0)
DS, LAND = 5.5, 0.3                                                      # mm (CAD TC-03)
A_band = math.pi * DS * LAND
FTY = 724.0                                                              # MPa 17-4PH H1150 (Mechanical 'engmat')
FTY_HOT_FRAC = 0.85                                                      # Fty(316 C)/Fty(RT) AS RECALLED, TO-VERIFY (MMPDS / maker)
A_net = (math.pi / 4 * (5.5 ** 2 - 3.0 ** 2)) * 1e-6                     # m2 seated pressure area, 3 mm stem
Fp = lambda P: (P - 101325.0) * A_net
dx0 = mech['crank_law'][0]['dx_dphi_mm_per_rad'] * 1e-3
sl = mech['baseline']['seat_load']
loads = {'minus10_bench_N': round(0.9 * sl['nominal_N'], 1), 'nominal_N': sl['nominal_N'], 'plus10_N': sl['plus10_N'],
         'plus10_MEOP_N': sl['plus10_plus_MEOP_seated_pressure_N'], 'plus10_relief_7p5MPa_N': round(sl['plus10_N'] + Fp(RELIEF), 1),
         'plus10_proof_ASSUMED_N': round(sl['plus10_N'] + Fp(PROOF), 1)}
wedge = {mu: 1.0 / (math.sin(ALPHA) + mu * math.cos(ALPHA)) for mu in (0.0, 0.3)}
contact = {k: {f'mu_{mu}': round(F * w / A_band, 1) for mu, w in wedge.items()} for k, F in loads.items()}
op_keys = [k for k in loads if 'proof' not in k]
pmin = min(contact[k]['mu_0.3'] for k in op_keys); pmax = max(contact[k]['mu_0.0'] for k in op_keys)
p_proof = contact['plus10_proof_ASSUMED_N']['mu_0.0']
line_load = {k: round(F / (math.pi * DS), 1) for k, F in loads.items()}
T0_ADOPT, K_ADOPT = 0.25, 0.12                                          # lead decision 2026-10-12 (rolling guide), Combustion recommendation
loads_adopt = {'minus10_bench_N': round(0.9 * T0_ADOPT / dx0, 1), 'nominal_N': round(T0_ADOPT / dx0, 1), 'plus10_N': round(1.1 * T0_ADOPT / dx0, 1),
               'plus10_MEOP_N': round(1.1 * T0_ADOPT / dx0 + Fp(P_TANK_MEOP), 1), 'plus10_relief_7p5MPa_N': round(1.1 * T0_ADOPT / dx0 + Fp(RELIEF), 1),
               'plus10_proof_ASSUMED_N': round(1.1 * T0_ADOPT / dx0 + Fp(PROOF), 1)}
contact_adopt = {k: {f'mu_{mu}': round(F * w / A_band, 1) for mu, w in wedge.items()} for k, F in loads_adopt.items()}
pmax_adopt = max(contact_adopt[k]['mu_0.0'] for k in loads_adopt if 'proof' not in k)
band = {f'{w}mm': round(loads['plus10_relief_7p5MPa_N'] * wedge[0.0] / (math.pi * DS * w), 0) for w in (0.15, 0.24)}
coast_max = max(v['coast_s'] for v in J['thermal_and_loads']['relight_after_coast']['v']['duty_cycles'].values() if v.get('coast_s') is not None)
_hs = _find(J['valves_and_actuators']['pintle_actuator'], 'hard_start_N2O_admitted_g')
assert _hs is not None
hs_g = max(_hs['v'].values())
leak_ceiling_gps = 0.1 * hs_g / coast_max
E_174PH, L_FREE = 197e3, 40.0                                            # MPa AS RECALLED; mm ASSUMED free length
P_euler = math.pi ** 2 * E_174PH * (math.pi * 3.0 ** 4 / 64) / L_FREE ** 2
alpha_mis = 16.0e-6 - 10.8e-6                                            # 1/K Nitronic 60 vs 17-4PH, AS RECALLED
shift_um = 5.5e3 * alpha_mis * 300.0 / (2 * math.tan(ALPHA))             # lift-equivalent seat-line shift per 300 K

res = nf['mechanical_C1_C2_rerun']['results']
part = nf['partial_stroke_unlit_C2']
fl = nf['flight_line_C2']['results']
bo = nf['seat_breakout_C2']['results']
B = 'S3mu20_T0.30_baseline'
_u70 = nf['unlit_opening_force_vs_lift']['P1_70.0bar_ambient']
SEATED = {k: _u70[0][f'{k}_L0_L1_L2_N'][0] for k in ('3mm', '4mm')}
OPENB = {k: _u70[1][f'{k}_L0_L1_L2_N'][0] for k in ('3mm', '4mm')}
dF = round(SEATED['3mm'] - OPENB['3mm'], 1)
mg = lambda key: part[key]['margin_vs_stall_7V4']
start = {f'{p}bar': {l: mg(f'{B}|start_to_ignition_lift_0p3mm_torch|P1_{p}bar|{l}') for l in ('L1', 'L2')} for p in ('50.5', '70.0')}
cold100 = {f'{p}bar': {l: mg(f'{B}|coldflow_to_100pct_lift_1p92mm_ambient|P1_{p}bar|{l}') for l in ('L1', 'L2')} for p in ('50.5', '70.0')}
hotl = {l: fl[B][l]['margin_vs_stall_7V4'] for l in ('L1', 'L2')}
wr = win['results']
wsum = {c: {l: {k: wr[c][l][k] for k in ('n_feasible', 'n_targets_met', 'T0_range_Nm', 'seat_load_nom_range_N', 'lead_baseline_T0.30_k0.10_inside')}
            for l in ('L1', 'L2')} for c in wr}
pick = lambda c, l, T0, k: next((r for r in wr[c][l]['feasible'] if abs(r['T0_Nm'] - T0) < 1e-9 and abs(r['k_Nm_per_rad'] - k) < 1e-9), None)
roll = 'S3_rolling_plainpins (hypothetical)'
r30 = {l: pick(roll, l, 0.30, 0.10) for l in ('L1', 'L2')}
r25 = {l: pick(roll, l, 0.25, 0.12) for l in ('L1', 'L2')}
bo_rows = lambda name, P: {f"mu_{r['mu_seat']}": r['margin_7V4'] for r in bo[name][P]['rows']}
bo_B70, bo_B50 = bo_rows(B, 'P1_70.0bar'), bo_rows(B, 'P1_50.5bar')
bo_R25 = bo_rows('S3_rolling_plainpins_T0.25_k0.12 (hypothetical)', 'P1_70.0bar')

needle_force = T({
    'question': ('lead 2026-10-12: Mechanical pintle v2 3 mm stem (pintle_inline_v34_v2.json) and the S3 spring baseline (v2p2: S3_PTFE15mu20, '
                 'T0 0.30 N m, k 0.10 N m/rad, +/-10 %)'),
    'a_flow_model': (f'PASS: the injector flow model (Dyer pintle, Cd 0.70 ASSUMED, A(h) = pi s (Ds - s cos 15 deg), s = h sin 15 deg; A = {A_STOP:.1f} mm2 '
                     f'at the 4.2 mm stop < A_seat {A_SEAT_MM2:.2f} mm2) contains no stem term: throttle_map_v2.csv, the plant fit, ignition and speed '
                     f'checks are unchanged. Side effects: wetted bonnet annulus pi/4 (4^2 - 3^2) x 26 mm = +{DV_BONNET:.2f} cm3; head-end N2O-side BC '
                     f'unchanged; stem conductance {G3:.1e} W/K (was {G22:.1e}).'),
    'sign': '+ closing (needle into the seat)',
    'formula': 'F = (P1 - P_down) A_eff(h) - (P1 - Pa) A_stem; P1 manifold, P_down pressure on the cone downstream of the metering gap',
    'laws': {'seated': 'A_eff = A_seat (pi/4 5.5^2 = 23.76 mm2)',
             'L0_lower_bound': 'Mechanical/Electronics blend: A_eff -> 0 after 0.1 mm (whole cone at P1): F = -(P1 - Pa) A_stem. Use for C1 (spring close).',
             'L1_central': 'geometric throat: A_eff = pi (2.75 mm - h sin15 cos15)^2 (cone upstream of the gap at P1, downstream at P_down). Use for C2.',
             'L2_upper_bound': 'A_eff = A_seat at every lift (approach-flow depression over the cone inside the seat edge). C2 sensitivity.',
             'not_modelled': 'jet momentum (flow force), approach velocity, flashing/choking at the gap (moves F toward L0); B-PNT-1 measures F(h, P)'},
    'seated_at_tank_MEOP_7MPa_ambient_N': {'3mm': SEATED['3mm'], '4mm': SEATED['4mm'], 'open_bound_L0_3mm': OPENB['3mm'], 'open_bound_L0_4mm': OPENB['4mm']},
    'unlit_70bar_ambient_3mm_L1_N_by_lift_mm': {str(e['lift_mm']): e['3mm_L0_L1_L2_N'][1] for e in _u70},
    'hot_fire_envelope_3mm_N': nf['hot_fire_envelope_all_rows_N']['3mm'],
    'C2_rerun_S3_baseline': {
        'model': 'Mechanical pintle_inline_v34.py servo_torque (+10 % spring, ASSUMED frictions incl. seal 18.75 N, guide mu 0.20) with F_po replaced; '
                 'L0 reproduces Mechanical v2.2 (0.597 bench, 0.537 flight, 0.047/0.094 N m assist)',
        'criterion': 'margin = HV69 stall 0.90 N m (7.4 V) / max opening torque >= 1.5',
        'flight_hot_fire_line_margin': hotl, 'start_to_ignition_lift_0p3mm_torch_margin': start,
        'unlit_to_100pct_lift_ambient_margin': cold100,
        'unlit_full_stroke_ambient_margin': {k: {l: res[B][l][k]['margin_vs_stall_7V4'] for l in ('L0', 'L1', 'L2')} for k in ('P3.5MPa', 'P5.5MPa', 'MEOP')},
        'C1_close_assist_L0_Nm': {k: res[B]['L0'][k]['close_assist_min_Nm(-10% spring)'] for k in ('P3.5MPa', 'P5.5MPa', 'MEOP')}},
    'C2_rerun_history': {'v2_T0.18_k0.175_PTFE18': {'hot_line': {l: fl['v2_baseline'][l]['margin_vs_stall_7V4'] for l in ('L1', 'L2')}},
                         'v2p1_T0.19_k0.17_PTFE15_mu0.10': {'hot_line': {l: fl['v2p1_baseline'][l]['margin_vs_stall_7V4'] for l in ('L1', 'L2')}}},
    'spring_window': {'definition': win['criteria'], 'summary': wsum,
                      'rolling_plainpins_T0.30_k0.10': r30, 'rolling_plainpins_T0.25_k0.12': r25,
                      'file': 'data/v2/pintle_spring_window_v2p3.json (src/pintle_spring_window_v2p3.py)'},
    'verdict': (f'3 mm stem PASS for the flow model. With the S3 spring on the PTFE guide at mu 0.20, flight C2 FAILS under the central law L1 '
                f'(hot-fire line {hotl["L1"]}, start at 70 bar {start["70.0bar"]["L1"]}, at 50.5 bar {start["50.5bar"]["L1"]}) and L2 '
                f'({hotl["L2"]}, {start["70.0bar"]["L2"]}); only L0 passes. No linear spring meets C1 (L0) and flight C2 (L1) robustly on that guide '
                f'({wsum["S3_PTFE15mu20 (lead baseline friction)"]["L1"]["n_feasible"]} spring with ~0 MEOP assist; none under L2). A rolling guide '
                f'(mu 0.005, hypothetical, plain pins) opens T0 {wsum[roll]["L1"]["T0_range_Nm"][0]}-{wsum[roll]["L1"]["T0_range_Nm"][1]} N m; '
                f'0.30/0.10 passes ({r30["L1"]["margin_7V4"]}/{r30["L2"]["margin_7V4"]}, MEOP assist {r30["L1"]["assist_MEOP"]}); a lower preload '
                f'0.25/0.12 gives {r25["L1"]["margin_7V4"]}/{r25["L2"]["margin_7V4"]} with assist {r25["L1"]["assist_MEOP"]}: Combustion supports the '
                'rolling-guide fallback. Unlit opening beyond the ignition lift at tank pressure is below 1.5 for every configuration (procedure).'),
    'conditions': ['C1 on L0, C2 on L1 with L2 as sensitivity until B-PNT-1 measures needle force vs lift at 3.5/5.5/7.0 MPa (N2 then N2O; stem load '
                   'cell or servo current)',
                   'N2O cold flows into a back-pressured catch volume (P_down at the hot-fire Pc for the tested lift) or N2 at <= 3.5 MPa for full-stroke '
                   'checks; ignition logic: no opening beyond the ignition lift before Pc confirms light; a no-light abort closes']},
    'DERIVED data/v2/needle_force_bounds_v2p3.json (src/needle_force_v2p3.py; Mechanical pintle_inline_v34.py friction/spring model re-run with '
    'L1/L2, sha256 ' + nf['inputs']['mechanical_script_sha256_16'] + '); bounds, not a prediction', csv='data/v2/needle_force_bounds_v2p3.csv')

seat_seal = T({
    'b_seat': {
        'seat_type': 'metal-to-metal: 17-4PH H1150 needle cone (15 deg half-angle) on a 17-4PH H1150 5.5 mm sharp-edge seat with a 0.3 mm lapped land '
                     '(CAD TC-03/TC-05); not a polymer',
        'axial_seat_load_N': loads,
        'load_sources': (f'Mechanical pintle_inline_v34_v2p2.json (S3 T0 0.30 N m / dx/dphi {dx0*1e3:.3f} mm/rad); relief {RELIEF/1e6:.1f} MPa (trapped-liquid '
                         f'relief, combustion.json v2.2); proof {PROOF/1e6:.1f} MPa ASSUMED 1.5 x tank MEOP; seated pressure area pi/4 (5.5^2 - 3^2) mm2'),
        'wedge_normal_factor': {f'mu_{k}': round(v, 3) for k, v in wedge.items()},
        'land_area_mm2': round(A_band, 3),
        'contact_pressure_MPa': contact, 'operating_range_MPa': [pmin, pmax], 'fraction_of_Fty_724MPa': [round(pmin / FTY, 2), round(pmax / FTY, 2)],
        'proof_MPa_mu0': p_proof,
        'axial_line_load_N_per_mm': line_load,
        'hot_soak': (f'lumped head bound (headend_thermal_v2.json, seat insert = head node): CAD baseline (disc2mm, 0.44 kg, hg x1) {min(TH_CAD):.0f}-{max(TH_CAD):.0f} K '
                     f'flight, {min(TH_G_CAD):.0f} K ground; disc2mm band {min(TH_D2):.0f}-{max(TH_D2):.0f} K flight, {min(TH_G_D2):.0f}-{max(TH_G_D2):.0f} K ground; '
                     f'bare face {max(TH_BARE):.0f} K flight / {max(TH_G_BARE):.0f} K ground. Fty(316 C) ~{FTY_HOT_FRAC} x RT AS RECALLED -> {pmax:.0f} MPa = '
                     f'{100*pmax/(FTY*FTY_HOT_FRAC):.0f} % of the hot Fty: elastic. Creep of the land negligible below ~370 C for a 1 h soak (AS RECALLED; '
                     'TO-VERIFY MMPDS/maker data); a bare-face soak exceeds the H1150 ageing temperature (894 K): inspect/re-harden after any face-disc loss'),
        'material_verdict': f'ACCEPTABLE: elastic, {100*pmin/FTY:.0f}-{100*pmax/FTY:.0f} % of RT Fty in operation, {100*p_proof/FTY:.0f} % at proof',
        'adopted_T0.25_k0.12_loads_N': loads_adopt, 'adopted_contact_pressure_MPa': contact_adopt,
        'adopted_note': f'adopted spring (lead decision 2026-10-12): max operating land pressure {pmax_adopt:.0f} MPa ({100*pmax_adopt/FTY:.0f} % of RT Fty); the S3 values above bound it',
        'conditions': [f'lapped contact band >= 0.24 mm (80 % of the land) over 360 deg by bluing: a 0.15 mm band reaches {band["0.15mm"]:.0f} MPa at the relief '
                       f'load (> Fty, coins); 0.24 mm gives {band["0.24mm"]:.0f} MPa',
                       'galling: same alloy and temper today; use needle+stem H900 (harder seal counterface) with the seat in H1150 (hardness differential), TO-VERIFY',
                       f'keep both parts 17-4PH: a Nitronic 60 seat would shift the seat line ~{shift_um:.0f} um of lift per 300 K (alpha AS RECALLED) and its '
                       'annealed Fty (~414 MPa AS RECALLED) is close to the land pressure'],
        'self_locking_wedge': {
            'note': ('tan 15 deg = 0.268: for mu_seat > 0.268 the seated cone wedges; break-out = F_seat (mu cos a - sin a)/(sin a + mu cos a); crack-open '
                     'margin at 7.4 V with Mechanical\'s servo_torque (guide amplification included)'),
            'S3_mu_g0.20_MEOP': bo_B70, 'S3_mu_g0.20_50p5bar': bo_B50, 'rolling_T0.25_k0.12_MEOP': bo_R25,
            'action': 'B-PNT-1: break-out torque after a dwell closed at MEOP; option PFPE film on the land (mu < 0.27); lower preload + rolling guide'},
        'leak_tightness': (f'cannot be predicted for a lapped metal seat; pressure-assisted seat, so LOW pressure governs (spring only, {loads["minus10_bench_N"]} N, '
                           f'{line_load["minus10_bench_N"]} N/mm). N2 leak test at 5 and 70 bar before/after the B-PNT-1 cycle count and after a soak, then N2O. '
                           'Proposed acceptance <= 1 scc/min N2 (TO-AGREE). Combustion ceiling for a coast: 10 % of the '
                           f'{hs_g} g hard-start inventory over {coast_max:.1f} s = {leak_ceiling_gps:.3f} g/s; until measured close the NC valve during coasts '
                           '(trapped-liquid relief stays)'),
        'polymer_check': ('not applicable to the baseline; a polymer seat is not feasible here: land pressure '
                          f'{pmin:.0f}-{pmax:.0f} MPa vs compressive strength PTFE ~10-15, PCTFE ~30-50, PEEK ~120 MPa (AS RECALLED) -> extrusion/creep; '
                          f'PCTFE service limit ~150 C (AS RECALLED) vs the soak band {min(TH_D2):.0f}-{max(TH_D2):.0f} K; a soft seat needs a new geometry')},
    'c_seal': {
        'verdict': (f'SUITABLE in principle: spring-energised PTFE-family rod seal, 3 mm rod, N2O at {P_TANK_MEOP/1e6:.1f} MPa tank MEOP / {PROOF/1e6:.1f} MPa proof '
                    f'(ASSUMED factor 1.5) (TO-VERIFY per part); from the N2O normal boiling point {TB_N2O - 273.15:.1f} C (venting, CoolProp) to the bonnet '
                    'temperature from Mechanical FEA (PTFE jacket limit ~260 C AS RECALLED)'),
        'vendor_classes_TO_VERIFY': ['Trelleborg Turcon Variseal M2 (rod, small-diameter series)', 'Saint-Gobain OmniSeal 103A rod seal class',
                                     'Parker FlexiSeal rod seal class', 'Bal Seal canted-coil spring-energised rod seal'],
        'specification': ('jacket virgin PTFE or an oxygen-compatible filled grade (no glass fill on a soft rod); spring Elgiloy / Hastelloy / 17-7PH; '
                          'oxygen-cleaned, PFPE (Krytox class) lubricant only; extrusion gap per maker at proof; split or open gland for a 3 mm seal; '
                          'rod Ra 0.1-0.2 um, hard rod (H900) per maker'),
        'friction': ('DERIVED order of magnitude 1-5 N (mu 0.05-0.1 on 7 MPa x pi x 3 mm x 0.3 mm = 20 N normal + energiser); Mechanical 18.75 N ASSUMED '
                     'is conservative for C1 and C2; break-away after dwell from the maker'),
        'price': 'TO-QUOTE (Sonderborg DK-6400)'},
    'stem_buckling': (f"link compression <= {loads['plus10_N']} N (+10 % spring; the pressure load reacts below the seal) on 3 mm: "
                      f"{loads['plus10_N'] / (math.pi / 4 * 9):.0f} MPa; Euler pinned-pinned over {L_FREE:.0f} mm (ASSUMED) {P_euler/1e3:.1f} kN (margin "
                      f"{P_euler / loads['plus10_N']:.0f}; E {E_174PH/1e3:.0f} GPa AS RECALLED); Mechanical confirms the free length")},
    'DERIVED (Combustion review of Mechanical CAD/calcs v2-v2.2; vendor and material items TO-VERIFY)')

pa = J['valves_and_actuators']['pintle_actuator']
pa['lead_decision_v2p3'] = T({'adopted': (f'rolling-guide carriage, spring {T0_ADOPT} N m at closed + {K_ADOPT} N m/rad (+/-10 %); C2 checked under L1 and L2, '
                                          'C1 under L0; seat 17-4PH, needle+stem H900 / seat H1150, lapped land with blued contact >= 0.24 mm all round, '
                                          'PFPE film on the land; spring-energised PTFE-class rod seal'),
                              'combustion_check_of_adopted': {'flight_C2_margin_L1_L2': [r25['L1']['margin_7V4'], r25['L2']['margin_7V4']],
                                                              'C1_MEOP_assist_L0_Nm': r25['L1']['assist_MEOP'],
                                                              'crack_open_margin_MEOP_by_mu_seat': bo_R25,
                                                              'max_operating_land_pressure_MPa': pmax_adopt,
                                                              'basis': 'hypothetical rolling_18mm guide with plain pins in pintle_spring_window_v2p3 / needle_force_v2p3; Mechanical v2.3 re-runs with its final guide/pins'},
                              'operating_rules': ['ignition lift held until Pc confirms light (no further opening before; a no-light abort closes)',
                                                  'N2O cold flows into a back-pressured catch volume; full-stroke checks with N2 at <= 3.5 MPa',
                                                  'NC isolation valve closed during coasts until the seat leak rate is measured (trapped-liquid relief stays)'],
                              'routing': 'operating rules to Electronics and GNC; OI-7 screen to Mechanical (CAD v3.4: <= 15 um at Cv >= 2.2 or an in-line filter housing)'},
                             'LEAD decision 2026-10-12 (CHANGELOG), on the Combustion v2.3 recommendation')
pa['needle_force_v2p3'] = needle_force
pa['seat_and_seal_review_v2p3'] = seat_seal
pa['force_basis_note'] = pa['force_basis_note'] + ' v2.3: superseded by needle_force_v2p3 (3 mm stem, laws L0/L1/L2, Mechanical C1/C2 re-run).'
J['thermal_and_loads']['head_end_bc']['v']['pintle_needle']['note_v2p3'] = (
    f'Mechanical pintle v2: 3 mm stem through the bonnet seal (was 4 mm): conductance {G3:.1e} W/K over 0.10 m; the 6 mm needle body in the 10 mm wetted '
    'bore is unchanged, so the N2O-side BC is unchanged')
for oi in J['open_interface_issues']:
    if oi['id'] == 'OI-11':
        oi['issue'] += (' v2.3: Mechanical pintle v2/v2.2 force law blends to the opening bound -dp A_stem after 0.1 mm lift: conservative for C1, not for C2 '
                        '(the closing pressure force persists while the gap meters). S3 spring (0.30/0.10) on the PTFE mu 0.20 guide fails flight C2 under L1; '
                        'the S3 seat load also makes a dry 15 deg seat self-lock (mu_seat > 0.27).')
        oi['action'] += (f' v2.3: C1 on L0, C2 on L1 (L2 sensitivity), see needle_force_v2p3 and spring_window; rolling guide supported (S3 0.30/0.10 '
                         f'{r30["L1"]["margin_7V4"]}, 0.25/0.12 {r25["L1"]["margin_7V4"]}); B-PNT-1 measures force vs lift and break-out after a dwell at MEOP. LEAD decision 2026-10-12: rolling guide + spring 0.25/0.12 adopted, rule C1 on L0 / C2 on L1 and L2; Mechanical pintle_inline_v34 v2.3 carries L1/L2 natively.')
    if oi['id'] == 'OI-7':
        oi['issue'] += (' v2.3: CAD v3.3/v3.4 TC-04 still shows a 40 um sintered screen 10 x 2.5 mm under the inlet; <= 15 um (1/3 of the 54 um floor gap) '
                        'with Cv >= 2.2 stands; screen area/Cv to be checked against the 2.7 bar line budget. Mechanical (2026-10-12): TC-04 screen to <= 15 um '
                        'at Cv >= 2.2 in CAD v3.4, or an in-line filter housing if the element cannot reach Cv 2.2 inside the -6 port.')
J['unknowns_and_open_items'].append(f'Needle pressure force vs lift (bounds L0-L2 differ by up to {dF} N at MEOP above 0.1 mm lift): B-PNT-1 load cell or '
                                    'servo current at 3.5/5.5/7.0 MPa, N2 then N2O.')
J['unknowns_and_open_items'].append('Pintle seat friction, break-out after a dwell at MEOP, and leak rate (metal lapped 15 deg seat): B-PNT-1 and N2 leak '
                                    'tests at 5 and 70 bar before/after cycling and after a soak, then N2O.')
J['inputs_read']['pintle_inline_v34_v2p2.json'] = (f'Mechanical v2.2 2026-10-12 (sha256 {sha(mraw)}): S3_PTFE15mu20 spring 0.30/0.10, seat loads, crank law; '
                                                   'v2/v2.1 read for history (needle_force_bounds_v2p3.json inputs)')
J['revision_history'].insert(0, J['revision_note'])
J['version'] = 'v2.3'
J['revision_note'] = ('v2.3 (2026-10-12, lead requests on Mechanical pintle v2 3 mm stem and the S3 spring baseline): valves_and_actuators.pintle_actuator.'
                      'needle_force_v2p3 (stem not in the flow model: throttle map unchanged; force laws L0/L1/L2; Mechanical C1/C2 re-run: S3 on the PTFE '
                      'mu 0.20 guide fails flight C2 under L1, rolling guide passes; spring window) and seat_and_seal_review_v2p3 (metal seat '
                      f'{pmin:.0f}-{pmax:.0f} MPa elastic at the S3 loads incl. relief; hot soak; polymer not feasible; galling and lap conditions; self-locking '
                      'wedge break-out; leak test; spring-energised seal classes TO-VERIFY); OI-7 (40 um CAD screen) and OI-11 updated; head-end stem note; two '
                      'unknowns added. Everything else unchanged from v2.2 (sha256 660df2c526025ede).')
CHANGED = {('version',), ('revision_note',), ('revision_history',), ('inputs_read',), ('unknowns_and_open_items',), ('open_interface_issues',),
           ('valves_and_actuators', 'pintle_actuator'), ('thermal_and_loads', 'head_end_bc')}
for k in J0:
    if (k,) in CHANGED:
        continue
    if isinstance(J0[k], dict):
        for kk in J0[k]:
            if (k, kk) in CHANGED:
                continue
            assert J0[k][kk] == J[k][kk], (k, kk)
    else:
        assert J0[k] == J[k], k
assert set(J0) == set(J)
json.dump(J, open(OUT, 'w'), indent=1, ensure_ascii=False, default=float)
print('wrote', OUT, os.path.getsize(OUT), 'bytes; contact', pmin, pmax, 'proof', p_proof, 'band', band, 'hot frac', round(pmax / (FTY * FTY_HOT_FRAC), 2),
      'shift_um', round(shift_um, 1), 'Euler kN', round(P_euler / 1e3, 2), 'TH_CAD', [round(x) for x in TH_CAD], 'TH_D2', round(min(TH_D2)), round(max(TH_D2)))
