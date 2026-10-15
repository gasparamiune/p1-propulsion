"""Pintle needle pressure-force bounds v2.3 (Combustion, 2026-10-12) - answer to the lead's check of Mechanical's pintle v2 (3 mm stem).

Question: does the 3 mm stem (Mechanical 03-cad/src/calcs/pintle_inline_v34_v2.json) change the injector/throttle map, and is the
needle force law Mechanical uses for the servo checks (C1 spring close, C2 servo opening) consistent with the injector?

Sign: + = CLOSING (needle pushed into the seat) in this file; Mechanical's F_po uses + = OPENING (converted where compared).

Pressure force on the needle (axisymmetric, needle body 6 mm in the wetted manifold at P1, stem through the bonnet seal to ambient Pa,
cone tip (half-angle 15 deg) in the seat orifice; the pressure downstream of the metering gap on the cone is P_down):
    F = (P1 - P_down) * A_eff(h) - (P1 - Pa) * A_stem
  seated (h = 0):            A_eff = A_seat = pi/4 Ds^2 (Ds 5.5 mm)  -> Mechanical/Electronics seated value (115.1 N at MEOP, 3 mm stem)
  lifted, L1 'geometric throat': A_eff = pi r_th^2, r_th = Ds/2 - h sin(a) cos(a)  (cone point nearest the seat edge; cone upstream of it
                             at P1, downstream at P_down).  Central estimate.  DERIVED (no flow-force / approach-velocity / flashing terms).
  lifted, L2 'seated area persists': A_eff = A_seat (approach-flow depression over the cone inside the seat-edge radius).  Upper bound
                             on the closing force (most demanding for opening).
  lifted, L0 Mechanical/Electronics: A_eff -> 0 after 0.1 mm (cone tip at P1) -> F = -(P1 - Pa) A_stem.  Lower bound (most opening):
                             conservative for C1 (spring close), NOT conservative for C2 (servo opening demand).
Two-phase effects: if the gap flow flashes/chokes the cone downstream of the throat can see up to ~P_sat, moving F from L1 toward L0;
the measured force vs lift and pressure (B-PNT-1 load cell, N2 then N2O) replaces all three laws.

The flow model (Dyer pintle, Cd 0.70, A(h) = pi s (Ds - s cos a), s = h sin a) does NOT contain the stem: the throttle map is unchanged.

Inputs (read-only): data/v2/engine_S230/throttle_map_v2.csv (SIM grain_q1d.py v2), Mechanical's pintle_inline_v34.py (imported read-only,
no bytecode written; sha256 recorded) for its crank law / friction / spring model, re-run here with L1 and L2.
Outputs: data/v2/needle_force_bounds_v2p3.csv, data/v2/needle_force_bounds_v2p3.json.
"""
from __future__ import annotations
import sys, json, math, hashlib, importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
MECH = Path('/home/claude/work/mechanical/engine/03-cad/src/calcs/pintle_inline_v34.py')
MECH_V21 = MECH.with_name('pintle_inline_v34_v2p1.json')     # Mechanical v2.1 (current baseline, 15 mm bushings, spring 0.19/0.17)
MECH_V2 = MECH.with_name('pintle_inline_v34_v2.json')       # Mechanical v2 (the numbers in the lead's request)
MECH_V22 = MECH.with_name('pintle_inline_v34_v2p2.json')    # Mechanical v2.2 = lead baseline S3_PTFE15mu20 (T0 0.30, k 0.10)
TMAP = ROOT / 'data/v2/engine_S230/throttle_map_v2.csv'
OUT_CSV = ROOT / 'data/v2/needle_force_bounds_v2p3.csv'
OUT_JSON = ROOT / 'data/v2/needle_force_bounds_v2p3.json'

PA = 101325.0
DS = 5.5e-3                     # m, seat (combustion.json v1/v2)
ALPHA = math.radians(15.0)      # cone half-angle (injector.py)
A_SEAT = math.pi / 4 * DS ** 2
STEMS = {'3mm': 3.0e-3, '4mm': 4.0e-3}
P_TORCH = 1.5e5                 # Pa, chamber before main ignition with the torch lit (ignition_v2.json order of magnitude, ASSUMED)


def a_stem(d):
    return math.pi / 4 * d ** 2


def r_throat(h):
    return DS / 2 - h * math.sin(ALPHA) * math.cos(ALPHA)


def a_throat(h):
    return math.pi * r_throat(h) ** 2


def F_bounds(P1, Pdown, h, d_stem):
    """(+ closing) L0 lower, L1 central, L2 upper; seated value if h == 0."""
    As = a_stem(d_stem)
    if h <= 0.0:
        f = (P1 - Pdown) * A_SEAT - (P1 - PA) * As
        return f, f, f
    L0 = -(P1 - PA) * As
    L1 = (P1 - Pdown) * a_throat(h) - (P1 - PA) * As
    L2 = (P1 - Pdown) * A_SEAT - (P1 - PA) * As
    return L0, L1, L2


def load_mech():
    spec = importlib.util.spec_from_file_location('pintle_inline_v34_ro', MECH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def mech_eval(m, law, cfg_name, spring=(0.18, 0.175), pressures=None, Pdown=PA, y_use=11):
    """Re-run Mechanical's servo_torque with a replaced F_po (their sign: + opening). law in {'L0','L1','L2'}."""
    c = m.CONFIGS[cfg_name]
    m.set_config(c)
    orig = m.F_po
    d = c['stem_d'] * 1e-3

    def F_po_alt(x_mm, P):
        if law == 'L0':
            return orig(x_mm, P)
        h = max(0.0, x_mm) * 1e-3
        l0, l1, l2 = F_bounds(max(P, PA), Pdown if P > PA else PA, h, d)
        f = l1 if law == 'L1' else l2
        return -f                                  # to Mechanical's + opening
    m.F_po = F_po_alt
    try:
        g = m.GUIDE_OPTIONS[c['guide']]
        T0, kk = spring
        phis = list(np.linspace(m.CRANK['phi_closed'], m.phi_at_lift(m.CRANK['x_stop']), 200))
        Tn = lambda p: T0 + kk * math.radians(p - m.CRANK['phi_closed'])
        P = pressures or m.PRESSURES
        res = {}
        for nm, Pv in P.items():
            op = [(m.servo_torque(p, 1.1 * Tn(p), Pv, True, g, y_use, c['f_seal'])[0], p) for p in phis]
            cl = [(m.servo_torque(p, 0.9 * Tn(p), Pv, False, g, y_use, c['f_seal'])[0], p) for p in phis]
            omax = max(op); cmin = min(cl)
            res[nm] = {'open_demand_max_Nm': round(omax[0], 3), 'at_lift_mm': round(m.lift(omax[1]), 3),
                       'margin_vs_stall_7V4': round(m.HV69['stall_Nm']['7.4'] / omax[0], 2),
                       'C2_pass(<=stall/1.5=0.60)': bool(omax[0] <= m.HV69['stall_Nm']['7.4'] / 1.5 + 1e-9),
                       'close_assist_min_Nm(-10% spring)': round(cmin[0], 3), 'assist_at_lift_mm': round(m.lift(cmin[1]), 3)}
        return res
    finally:
        m.F_po = orig


def main():
    out = {'version': 'v2.3', 'date': '2026-10-12', 'script': '02-combustion/src/needle_force_v2p3.py',
           'sign': '+ closing (needle into the seat)', 'inputs': {}, 'tags': {}}
    out['inputs'] = {'seat_D_m': DS, 'cone_half_angle_deg': 15.0, 'A_seat_m2': A_SEAT, 'A_stem_m2': {k: a_stem(v) for k, v in STEMS.items()},
                     'Pa_Pa': PA, 'throttle_map': str(TMAP.relative_to(ROOT)),
                     'throttle_map_sha256_16': hashlib.sha256(TMAP.read_bytes()).hexdigest()[:16],
                     'mechanical_script': str(MECH), 'mechanical_script_sha256_16': hashlib.sha256(MECH.read_bytes()).hexdigest()[:16]}
    out['tags'] = {'laws': 'DERIVED (static pressure-area; no flow-momentum, approach-velocity or flashing terms) - bounds, not a prediction',
                   'throttle_map': 'SIM grain_q1d.py v2 (S230, nominal ASSUMED regression law, Dyer pintle Cd 0.70); P1 = Pc (1 + dP/Pc) as simulated',
                   'mechanical_model': 'Mechanical pintle_inline_v34.py v2 friction/spring/crank model (ASSUMED frictions), re-run with replaced F_po only'}
    # 1. throttle-map states (hot fire, P_down = Pc)
    tm = pd.read_csv(TMAP, comment='#')
    rows = []
    for r in tm.itertuples():
        if not np.isfinite(r.lift_m) or r.mdot_ox <= 0:
            continue
        P1 = r.Pc_Pa * (1 + r.dP_over_Pc)
        row = {'P_tank_Pa': r.P_tank_Pa, 'D_port_m': r.D_port_m, 'frac': r.frac, 'F_N': r.F_N, 'Pc_Pa': r.Pc_Pa, 'P1_Pa': round(P1, 0),
               'lift_mm': round(r.lift_m * 1e3, 4)}
        for k, d in STEMS.items():
            l0, l1, l2 = F_bounds(P1, r.Pc_Pa, r.lift_m, d)
            row[f'F_L0_{k}_N'] = round(l0, 2); row[f'F_L1_{k}_N'] = round(l1, 2); row[f'F_L2_{k}_N'] = round(l2, 2)
        rows.append(row)
    df = pd.DataFrame(rows)
    with open(OUT_CSV, 'w') as fh:
        fh.write('# Needle pressure-force bounds v2.3 over throttle_map_v2 (S230) states; + = closing; L0 Mechanical open branch (lower), '
                 'L1 geometric throat (central), L2 seated area persists (upper); DERIVED from SIM states; SI except lift_mm, forces N\n')
        df.to_csv(fh, index=False)
    sel = df[(df.D_port_m == 0.025)]
    out['hot_fire_D25_summary'] = {}
    for Pt in sorted(sel.P_tank_Pa.unique()):
        s = sel[sel.P_tank_Pa == Pt].sort_values('frac')
        out['hot_fire_D25_summary'][f'{Pt/1e5:.0f}bar'] = [
            {'frac': float(x.frac), 'lift_mm': float(x.lift_mm), 'P1_bar': round(x.P1_Pa / 1e5, 2), 'Pc_bar': round(x.Pc_Pa / 1e5, 2),
             'F_3mm_L0_L1_L2_N': [x.F_L0_3mm_N, x.F_L1_3mm_N, x.F_L2_3mm_N], 'F_4mm_L0_L1_L2_N': [x.F_L0_4mm_N, x.F_L1_4mm_N, x.F_L2_4mm_N]}
            for x in s.itertuples()]
    out['hot_fire_envelope_all_rows_N'] = {k: {'L0_min': float(df[f'F_L0_{k}_N'].min()), 'L1_min': float(df[f'F_L1_{k}_N'].min()),
                                               'L1_max': float(df[f'F_L1_{k}_N'].max()), 'L2_max': float(df[f'F_L2_{k}_N'].max())} for k in STEMS}
    # 2. unlit opening (cold flow / start before main ignition): P_down = Pa or torch 1.5 bar, P1 = tank (no flow loss at crack)
    lifts = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0, 4.0, 4.2]
    unlit = {}
    for P1 in (3.5e6, 5.05e6, 5.5e6, 7.0e6):
        for Pd_nm, Pd in (('ambient', PA), ('torch_1p5bar', P_TORCH)):
            key = f'P1_{P1/1e5:.1f}bar_{Pd_nm}'
            unlit[key] = []
            for hmm in lifts:
                h = hmm * 1e-3
                e = {'lift_mm': hmm, 'r_throat_mm': round(r_throat(h) * 1e3, 3)}
                for k, d in STEMS.items():
                    l0, l1, l2 = F_bounds(P1, Pd, h, d)
                    e[f'{k}_L0_L1_L2_N'] = [round(l0, 1), round(l1, 1), round(l2, 1)]
                unlit[key].append(e)
    out['unlit_opening_force_vs_lift'] = unlit
    out['unlit_note'] = ('P1 = tank pressure (no line loss at crack; with full-stroke flow the line loss lowers P1); 5.05 MPa = saturated N2O at '
                         '20 C (CoolProp, combustion.json), 7.0 MPa = tank MEOP (LEAD v0). Cold flow and the start before Pc rises are these cases.')
    # 3. Mechanical C1/C2 re-run with L0 (as published), L1, L2 at P_down = ambient (cold flow / unlit full stroke = worst case for C2)
    m = load_mech()
    jv21 = json.loads(MECH_V21.read_bytes()); jv2 = json.loads(MECH_V2.read_bytes())
    y_use = jv21['inputs']['y_link_plane_mm']
    sp = lambda b: (b['spring_law']['T0_Nm_at_15deg'], b['spring_law']['k_Nm_per_rad'])
    s4c = jv21['designs']['S4_rolling_ballpins']['choice']
    s3m20 = jv21['designs']['S3_PTFE15mu20_plainpins']['choice']        # lead decision 2026-10-12 (CHANGELOG): new baseline T0 0.30 / k 0.10
    jv22 = json.loads(MECH_V22.read_bytes())
    assert jv22['baseline']['config'] == 'S3_PTFE15mu20_plainpins'
    assert abs(jv22['baseline']['spring_law']['T0_Nm_at_15deg'] - s3m20['T0_Nm']) < 1e-9 and abs(jv22['baseline']['spring_law']['k_Nm_per_rad'] - s3m20['k_Nm_per_rad']) < 1e-9
    CASES = {'S3mu20_T0.30_baseline': ('S3_PTFE15mu20_plainpins', (s3m20['T0_Nm'], s3m20['k_Nm_per_rad'])),
             'S3mu10_T0.30': ('S3_PTFE15_plainpins', (s3m20['T0_Nm'], s3m20['k_Nm_per_rad'])),
             'v2p1_baseline': (jv21['baseline']['config'], sp(jv21['baseline'])),
             'v2_baseline': (jv2['baseline']['config'], sp(jv2['baseline'])),
             'S4_rolling_own_spring': ('S4_rolling_ballpins', (s4c['T0_Nm'], s4c['k_Nm_per_rad'])),
             'S4_PTFE18_with_v2p1_spring': ('S4_PTFE18_plainpins', sp(jv21['baseline']))}
    out['inputs']['mechanical_json'] = {'v2p2': [str(MECH_V22), hashlib.sha256(MECH_V22.read_bytes()).hexdigest()[:16]],
                                        'v2p1': [str(MECH_V21), hashlib.sha256(MECH_V21.read_bytes()).hexdigest()[:16]],
                                        'v2': [str(MECH_V2), hashlib.sha256(MECH_V2.read_bytes()).hexdigest()[:16]]}
    out['cases'] = {k: {'config': v[0], 'spring_T0_Nm': v[1][0], 'spring_k_Nm_per_rad': v[1][1]} for k, v in CASES.items()}
    mech = {k: {law: mech_eval(m, law, cfg, spring=spr, y_use=y_use) for law in ('L0', 'L1', 'L2')} for k, (cfg, spr) in CASES.items()}
    repro = {}
    for k, jj in (('v2p1_baseline', jv21), ('v2_baseline', jv2)):
        b = jj['baseline']
        repro[k] = {'bench_open_Nm': [mech[k]['L0']['bench']['open_demand_max_Nm'], b['open_demand_bench_Nm']],
                    'MEOP_assist_Nm': [mech[k]['L0']['MEOP']['close_assist_min_Nm(-10% spring)'], b['assist_min_Nm']['MEOP']],
                    'P5.5_assist_Nm': [mech[k]['L0']['P5.5MPa']['close_assist_min_Nm(-10% spring)'], b['assist_min_Nm']['P5.5MPa']]}
        for q, (a_, b_) in repro[k].items():
            assert abs(a_ - b_) <= 0.0015, ('L0 does not reproduce Mechanical', k, q, a_, b_)
    # new baseline: Mechanical's design table (30-point phi grid) vs our 200-point grid
    repro['S3mu20_T0.30_baseline'] = {'open_max_all_P_Nm': [max(mech['S3mu20_T0.30_baseline']['L0'][q]['open_demand_max_Nm'] for q in mech['S3mu20_T0.30_baseline']['L0']),
                                                            s3m20['open_demand_max_Nm']],
                                      'MEOP_assist_Nm': [mech['S3mu20_T0.30_baseline']['L0']['MEOP']['close_assist_min_Nm(-10% spring)'], s3m20['assist_min_MEOP_Nm']],
                                      'P5.5_assist_Nm': [mech['S3mu20_T0.30_baseline']['L0']['P5.5MPa']['close_assist_min_Nm(-10% spring)'], s3m20['assist_min_5p5_Nm']]}
    repro['S3mu20_T0.30_baseline']['v2p2_flight_open_Nm'] = [max(mech['S3mu20_T0.30_baseline']['L0'][q]['open_demand_max_Nm'] for q in ('P3.5MPa', 'P5.5MPa', 'MEOP')),
                                                              jv22['baseline']['open_demand_flight_Nm']]
    for q, (a_, b_) in repro['S3mu20_T0.30_baseline'].items():
        assert abs(a_ - b_) <= 0.004, ('L0 does not reproduce Mechanical design table', q, a_, b_)
    out['mechanical_C1_C2_rerun'] = {
        'P_down': 'ambient (cold flow / unlit full stroke to the 4.2 mm stop); hot fire lowers the closing force (P_down = Pc), see flight_line_C2',
        'results': mech, 'L0_reproduces_published [ours, Mechanical]': repro}
    # 4. flight line: servo opening torque at each hot-fire throttle state (P_down = Pc, P1 from the map), D_port 25 mm
    flight, part = {}, {}
    for cname, (cfg, spring) in CASES.items():
        c = m.CONFIGS[cfg]; m.set_config(c); g = m.GUIDE_OPTIONS[c['guide']]; d = c['stem_d'] * 1e-3
        T0, kk = spring
        Tn = lambda p, T0=T0, kk=kk: T0 + kk * math.radians(p - m.CRANK['phi_closed'])
        orig = m.F_po
        res = {}
        try:
            for law in ('L1', 'L2'):
                worst = None
                for x in df[df.D_port_m == 0.025].itertuples():
                    h = x.lift_mm * 1e-3
                    l0, l1, l2 = F_bounds(x.P1_Pa, x.Pc_Pa, h, d)
                    f = l1 if law == 'L1' else l2
                    m.F_po = (lambda fv: (lambda x_mm, P: -fv))(f)
                    phi = m.phi_at_lift(x.lift_mm)
                    t = m.servo_torque(phi, 1.1 * Tn(phi), x.P1_Pa, True, g, y_use, c['f_seal'])[0]
                    if worst is None or t > worst[0]:
                        worst = (t, float(x.P_tank_Pa), float(x.frac), float(x.lift_mm), round(f, 1))
                res[law] = {'open_demand_max_Nm': round(worst[0], 3), 'margin_vs_stall_7V4': round(m.HV69['stall_Nm']['7.4'] / worst[0], 2),
                            'at': {'P_tank_bar': worst[1] / 1e5, 'frac': worst[2], 'lift_mm': worst[3], 'F_closing_N': worst[4]}}
            flight[cname] = res
            # 5. partial-stroke unlit cases: start to the ignition lift (<= 0.3 mm, torch 1.5 bar) and cold flow to the 100 % lift (1.92 mm at 50.5 bar)
            for case, xmax, Pd in (('start_to_ignition_lift_0p3mm_torch', 0.3, P_TORCH), ('coldflow_to_100pct_lift_1p92mm_ambient', 1.92, PA)):
                for P1 in (5.05e6, 7.0e6):
                    for law in ('L1', 'L2'):
                        def fpo(x_mm, P, law=law, P1=P1, Pd=Pd, d=d):
                            l0, l1, l2 = F_bounds(P1, Pd, max(0.0, x_mm) * 1e-3, d)
                            return -(l1 if law == 'L1' else l2)
                        m.F_po = fpo
                        phis = list(np.linspace(m.CRANK['phi_closed'], m.phi_at_lift(xmax), 120))
                        t = max((m.servo_torque(p, 1.1 * Tn(p), P1, True, g, y_use, c['f_seal'])[0], m.lift(p)) for p in phis)
                        part[f'{cname}|{case}|P1_{P1/1e5:.1f}bar|{law}'] = {'open_demand_max_Nm': round(t[0], 3), 'at_lift_mm': round(t[1], 3),
                                                                             'margin_vs_stall_7V4': round(m.HV69['stall_Nm']['7.4'] / t[0], 2)}
        finally:
            m.F_po = orig
    out['flight_line_C2'] = {'note': 'servo opening torque (+10 % spring, Mechanical friction model) at each throttle_map_v2 state, D_port 25 mm, '
                                     'P_tank 35-55 bar; the start before Pc rises is the unlit case at the ignition lift (<= 0.3 mm)', 'results': flight}
    out['partial_stroke_unlit_C2'] = part
    # 6. self-locking wedge at the seat: break-out at crack-open (tan 15 deg = 0.268; for mu_seat > 0.268 the seated cone wedges)
    #    extra axial force = F_seat (mu cos a - sin a) / (sin a + mu cos a), F_seat = +10 % spring through the toggle + seated pressure force
    bo = {}
    phi_c = m.CRANK['phi_closed']; dx0 = m.dxdphi(phi_c) * 1e-3
    hyp = {'S3_rolling_plainpins_T0.30_k0.10 (hypothetical)': ({'stem_d': 3.0, 'f_seal': 18.75, 'guide': 'rolling_18mm', 'pin_mu': 0.15}, (0.30, 0.10)),
           'S3_rolling_plainpins_T0.25_k0.12 (hypothetical)': ({'stem_d': 3.0, 'f_seal': 18.75, 'guide': 'rolling_18mm', 'pin_mu': 0.15}, (0.25, 0.12))}
    allc = {k: (dict(m.CONFIGS[v[0]]), v[1]) for k, v in CASES.items() if k in ('S3mu20_T0.30_baseline', 'S3mu10_T0.30', 'v2p1_baseline')}
    allc.update(hyp)
    orig = m.F_po
    try:
        for name, (c, (T0, kk)) in allc.items():
            m.set_config(c); g = m.GUIDE_OPTIONS[c['guide']]
            bo[name] = {}
            for P1 in (5.05e6, 7.0e6):
                Fp = F_bounds(P1, PA, 0.0, c['stem_d'] * 1e-3)[0]
                Fseat = 1.1 * T0 / dx0 + Fp
                rows = []
                for mu in (0.0, 0.3, 0.4, 0.5, 0.6):
                    extra = max(0.0, Fseat * (mu * math.cos(ALPHA) - math.sin(ALPHA)) / (math.sin(ALPHA) + mu * math.cos(ALPHA)))
                    m.F_po = (lambda v: (lambda x_mm, P: v))(-(Fp + extra))
                    t = m.servo_torque(phi_c, 1.1 * T0, P1, True, g, y_use, c['f_seal'])[0]
                    rows.append({'mu_seat': mu, 'extra_N': round(extra, 1), 'crack_T_Nm': round(t, 3), 'margin_7V4': round(m.HV69['stall_Nm']['7.4'] / t, 2)})
                bo[name][f'P1_{P1/1e5:.1f}bar'] = {'seat_load_N': round(Fseat, 1), 'rows': rows}
    finally:
        m.F_po = orig
    out['seat_breakout_C2'] = {'note': 'crack-open torque (+10 % spring, Mechanical friction model incl. guide amplification) with the wedge break-out of a '
                                       'self-locking 15 deg seat; mu_seat ASSUMED range (dry 17-4PH self-mated ~0.4-0.6 AS RECALLED; PFPE-lubricated lower)',
                               'results': bo}
    OUT_JSON.write_text(json.dumps(out, indent=1, default=float))
    # console digest
    print('A_seat mm2', round(A_SEAT * 1e6, 3), 'A_stem', {k: round(a_stem(v) * 1e6, 3) for k, v in STEMS.items()})
    for key in ('P1_70.0bar_ambient', 'P1_50.5bar_ambient', 'P1_50.5bar_torch_1p5bar'):
        print(key)
        for e in unlit[key]:
            print('  ', e)
    print('hot-fire envelope', json.dumps(out['hot_fire_envelope_all_rows_N']))
    for Pt, lst in out['hot_fire_D25_summary'].items():
        print(Pt, [(x['frac'], x['lift_mm'], x['P1_bar'], x['Pc_bar'], x['F_3mm_L0_L1_L2_N']) for x in lst])
    for cfg, v in mech.items():
        for law, rr in v.items():
            print(cfg, law, json.dumps({k: (rr[k]['open_demand_max_Nm'], rr[k]['margin_vs_stall_7V4'], rr[k]['at_lift_mm'],
                                           rr[k]['close_assist_min_Nm(-10% spring)']) for k in rr}))
    print('flight line', json.dumps(out['flight_line_C2']['results']))
    for k, v in out['partial_stroke_unlit_C2'].items():
        print(k, v)
    for k, v in out['seat_breakout_C2']['results'].items():
        print('BREAKOUT', k, json.dumps(v))


if __name__ == '__main__':
    main()
