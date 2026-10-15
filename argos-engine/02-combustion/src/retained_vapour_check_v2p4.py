"""Retained-vapour requirement (<= 19 cm3 at RELIGHT, LEAD 2026-10-13) against GNC's A1 coast specific force (Combustion v2.4).

Inputs
  * GNC staging_v3.1 results/a1_coast_accel/coast_accel_a1_v1.json (SIM sim6, 500 runs): body-axis specific force at the seat
    and MV stations from MECO to the relight command; f_z > 0 = apparent gravity toward the engine end (vapour driven forward,
    toward the MV and S1). MV station ASSUMED by GNC; drogue opening transient and line fluid dynamics not modelled (GNC).
  * Head-end trap 8.06 cm3 = manifold 4.51 + block 0.25 + riser 3.30 cm3 (Mechanical figures relayed by the lead; ESTIMATE until
    the v3.4 solids): a local high point under f_z > 0 that keeps its vapour.
  * Requirement 19 cm3 (LEAD) = the largest pocket with no abort in 200 000 samples at W 0.65 s (post_abort_pocket_v2p4).
Model (DERIVED; correlations LITERATURE, AS RECALLED, TO-VERIFY):
  * pocket volume per joule at the A1 relight state = 1 / (rho_v h_fg) (CoolProp HEOS); the 0.68 K subcooling credit (S1 crack
    0.07 MPa) is reported separately and not used in the bound;
  * Taylor-bubble drift in a liquid-filled tube: U = Fr sqrt(g' D (rho_l - rho_v) / rho_l), Fr = 0.345 (1 - exp(-0.01 N_f / 0.345))
    (1 - exp((3.37 - Eo) / m)), m = 10 (Wallis 1969 / White & Beardmore 1962 form), Eo = (rho_l - rho_v) g' D^2 / sigma; a bubble
    does not drift for Eo < 3.37. The viscous factor is evaluated with mu_l <= 1e-3 Pa s (bound; CoolProp has no N2O viscosity model);
    inclined runs drift up to ~1.5 x faster than vertical at 30-60 deg and much slower near horizontal (Bendiksen 1984, AS RECALLED),
    so an effective Fr of 0.10 is carried as the slow case for a coil with near-horizontal turns;
  * bound at the relight command: V_ret <= V_trap + V_coil_traps + (1 / rho_v h_fg) * Q * t_tr, valid only if t_tr is shorter than
    the settled time before relight (vapour formed during the coast-up must cross the whole route during the descent);
    otherwise the no-venting bound applies: Q_mean <= (V_req / (1 / rho_v h_fg) [+ sensible]) / window.
usage: python -I retained_vapour_check_v2p4.py GNC_COAST_JSON OUTDIR
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import CoolProp.CoolProp as CP

T_A1 = 286.7            # K, A1 relight state (combustion.json v2.3 relight_states)
V_REQ = 19.0            # cm3, LEAD requirement
V_TRAP = 4.51 + 0.25 + 3.30   # cm3, head-end trap (Mechanical figures via the lead, ESTIMATE)
SEG_LIQ_G = 36.528      # g, 44 cm3 liquid at the A1 state (segment_recheck_v2p4)
SUBCOOL_K = 0.6798      # K, S1 crack 0.07 MPa above P_tank (segment_recheck_v2p4)
MU_BOUND = 1.0e-3       # Pa s, upper bound used only for the viscous factor
D_LIST_MM = (4.6, 6.0, 7.75)   # tube IDs: 1/4 in, ~6 mm, 3/8 in x 0.035 in wall (ASSUMED; Mechanical gives the route)
L_LIST_M = (0.3, 0.5, 0.75, 1.0)
FR_CASES = {'vertical_or_inclined_ge_20deg': None, 'slow_near_horizontal_coil': 0.10}


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def drift(gp, D, rl, rv, sig):
    eo = (rl - rv) * gp * D * D / sig
    nf = rl * math.sqrt(gp * D ** 3 * (rl - rv) / rl) / MU_BOUND
    fr = 0.345 * (1 - math.exp(-0.01 * nf / 0.345)) * (1 - math.exp((3.37 - eo) / 10.0)) if eo > 3.37 else 0.0
    return fr * math.sqrt(gp * D * (rl - rv) / rl), fr, eo, nf


def main(gnc_json, outdir):
    G = json.load(open(gnc_json))
    disp = G['dispersed']
    rl = CP.PropsSI('D', 'T', T_A1, 'Q', 0, 'NitrousOxide'); rv = CP.PropsSI('D', 'T', T_A1, 'Q', 1, 'NitrousOxide')
    hfg = CP.PropsSI('H', 'T', T_A1, 'Q', 1, 'NitrousOxide') - CP.PropsSI('H', 'T', T_A1, 'Q', 0, 'NitrousOxide')
    cp_l = CP.PropsSI('C', 'T', T_A1 - 0.5, 'P', CP.PropsSI('P', 'T', T_A1, 'Q', 0, 'NitrousOxide') + 7e4, 'NitrousOxide')
    sig = CP.PropsSI('I', 'T', T_A1, 'Q', 0, 'NitrousOxide')
    cm3_per_J = 1e6 / (rv * hfg)
    e_sens = SEG_LIQ_G * 1e-3 * cp_l * SUBCOOL_K
    t_settled_min = disp['settled_before_relight_s']['min']; t_settled_p01 = disp['settled_before_relight_s']['p01']
    t_half_g_min = disp['above_half_g_before_relight_s']['min']
    win_max = disp['window_s']['max']; win_p99 = disp['window_s']['p99']
    g_desc = {'p01': disp['fz_seat_descent_mean_mps2']['p01'], 'p50': disp['fz_seat_descent_mean_mps2']['p50'], 'min': disp['fz_seat_descent_mean_mps2']['min']}
    g_up = {'mean_p50': -disp['fz_seat_coast_up_mean_mps2']['p50'], 'min_p01': -disp['fz_seat_coast_up_min_mps2']['p01']}
    tilt = {'descent_typical_deg_p99': math.degrees(math.atan2(disp['flat_seat_max_mps2']['p99'], g_desc['p01'])),
            'descent_typical_deg_max': math.degrees(math.atan2(disp['flat_seat_max_mps2']['max'], g_desc['min'])),
            'any_time_fz_gt_0p1g_deg_p50_p99_max': [disp['lateral_angle_max_deg_when_fz_gt_0p1g'][k] for k in ('p50', 'p99', 'max')],
            'note': 'atan(max lateral at the seat / descent mean f_z) is a representative tilt during the settled descent '
                    '(DERIVED from GNC p99/max values that need not coincide in time); the 49-71 deg values occur at low f_z near turnover'}
    drift_tab = {}
    for D in D_LIST_MM:
        row = {}
        for lab, gp in (('descent_p01_%.2f' % g_desc['p01'], g_desc['p01']), ('descent_p50_%.2f' % g_desc['p50'], g_desc['p50']),
                        ('coast_up_mean_p50_%.2f_inverted' % g_up['mean_p50'], g_up['mean_p50']),
                        ('coast_up_min_p01_%.2f_inverted' % g_up['min_p01'], g_up['min_p01']), ('stand_1g_9.81', 9.80665)):
            U, fr, eo, nf = drift(gp, D * 1e-3, rl, rv, sig)
            row[lab] = dict(U_m_s=U, Fr=fr, Eo=eo, N_f_lower_bound=nf, drifts=eo > 3.37)
        drift_tab[f'D{D:g}mm'] = row
    budget_Ws = (V_REQ - V_TRAP) / cm3_per_J
    allow = {}
    for D in D_LIST_MM:
        U0, fr0, eo0, _ = drift(g_desc['p01'], D * 1e-3, rl, rv, sig)
        for fl, frx in FR_CASES.items():
            U = U0 if frx is None else U0 * frx / max(fr0, 1e-9)
            for L in L_LIST_M:
                ttr = L / U if U > 0 else float('inf')
                ok = ttr <= t_half_g_min
                allow[f'D{D:g}mm|{fl}|L{L:g}m'] = dict(U_m_s=U, t_transit_s=ttr, transit_within_min_time_above_half_g=ok,
                                                       Q_allow_W=(budget_Ws / ttr if ok else None),
                                                       note=None if ok else 'transit longer than the settled time: no-venting bound applies')
    q_novent = {'with_subcooling_credit_W': (V_REQ / cm3_per_J + e_sens) / win_max, 'without_credit_W': (V_REQ / cm3_per_J) / win_max,
                'window_s': win_max, 'window_basis': 'GNC dispersed MECO -> relight command, max of 500 runs'}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/retained_vapour_check_v2p4.py',
               inputs=dict(gnc_coast_json=os.path.abspath(gnc_json), gnc_coast_json_sha256_16=sha16(gnc_json), gnc_version=G.get('version'),
                           gnc_mc_case=G.get('mc_case'), stations=G.get('stations'), V_req_cm3=V_REQ, V_trap_head_end_cm3=V_TRAP,
                           tags=dict(gnc='SIM (sim6 v2.7.1-dev, 500 runs; MV station ASSUMED; no drogue opening transient; no line fluid dynamics)',
                                     trap='Mechanical figures via the lead (ESTIMATE)', requirement='LEAD 2026-10-13',
                                     drift='LITERATURE, AS RECALLED (Wallis 1969; White & Beardmore 1962; Bendiksen 1984), TO-VERIFY',
                                     props='CoolProp HEOS (DERIVED); viscosity bounded at 1e-3 Pa s (no CoolProp model for N2O)')),
               props_A1=dict(T_K=T_A1, rho_l=rl, rho_v=rv, h_fg_J_kg=hfg, sigma_N_m=sig, cp_l_J_kgK=cp_l, pocket_cm3_per_J=cm3_per_J,
                             sensible_credit_J=e_sens),
               gnc_time_budget=dict(settled_before_relight_s_min=t_settled_min, settled_before_relight_s_p01=t_settled_p01,
                                    above_half_g_before_relight_s_min=t_half_g_min, window_s_p99=win_p99, window_s_max=win_max,
                                    descent_mean_fz_mps2=g_desc, coast_up_fz_mps2=g_up,
                                    turnover_fz_le_0_s_max=disp['descent_time_fz_below_0_s']['max'],
                                    turnover_fz_min_mps2=disp['fz_seat_descent_min_mps2']['min'], tilt=tilt,
                                    rate_max_dps_p99_max=[disp['rate_max_dps']['p99'], disp['rate_max_dps']['max']],
                                    mv_minus_seat_fz_maxabs_p99_mps2=disp['mv_minus_seat_fz_maxabs_mps2']['p99']),
               drift=drift_tab,
               heat_transit_budget_Ws=budget_Ws,
               allowable_Q_vs_route=allow,
               no_venting_bound=q_novent,
               stand_scaling=dict(drift_ratio_flight_over_1g=[math.sqrt(g_desc['min'] / 9.80665), math.sqrt(g_desc['p50'] / 9.80665)],
                                  note='U ~ sqrt(g\'): a 1 g stand test with the flight route and orientation drifts 7-12 % faster than the descent (DERIVED)'),
               closure_criterion=('V_trap_head + sum V_trap_i(tilt <= 20 deg) + pocket_cm3_per_J * integral of Q over the last t_tr before the relight '
                                  'command <= 19 cm3, with t_tr = sum L_i / U_i <= the minimum time above 0.5 g before relight; otherwise the '
                                  'no-venting bound on the mean heat input from MECO to relight applies'),
               tag='DERIVED (bounds; not a two-phase flow simulation)')
    fn = os.path.join(outdir, 'retained_vapour_check_v2p4.json')
    json.dump(out, open(fn, 'w'), indent=1)
    print('pocket cm3/J %.5f; budget Q*t_tr %.0f W s; no-vent Q <= %.1f W (%.1f W with credit) over %.2f s' %
          (cm3_per_J, budget_Ws, q_novent['without_credit_W'], q_novent['with_subcooling_credit_W'], win_max))
    for D, row in drift_tab.items():
        print(D, {k: (round(v['U_m_s'], 4), round(v['Eo'], 1)) for k, v in row.items()})
    for k, v in allow.items():
        print(k, 't_tr %.1f s' % v['t_transit_s'], 'Q_allow', None if v['Q_allow_W'] is None else round(v['Q_allow_W'], 1))
    print('tilt', tilt)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '.')
