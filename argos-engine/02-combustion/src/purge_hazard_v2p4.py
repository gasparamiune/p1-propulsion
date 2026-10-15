"""Hazard numbers for the A1 forced-purge provision (Combustion v2.4, 2026-10-13; coordinator ask (a), hazard part).

PURGE (LEAD 2026-10-13): MV open with the pintle seated and the bleed taps (T4 crown and FD-01 radial, 0.8 or 1.0 mm, two NC
valves in series per tap) open for Tp, ending before E1 (bleeds confirmed closed before the lift; here 0.05 s before E0). Questions: (1) seat leak at the B-PNT-1
acceptance (<= 10 sccm GN2 at 56 bar); (2) N2O decomposition on hot surfaces up to the TC-03 exit lip at 819.5 C (Mechanical
tc03_in718_check_v1, A1 peak); (3) unplanned-light paths.

Computes (all DERIVED unless tagged):
  - leak masses over the coast and over the MV-open exposure with and without PURGE;
  - adiabatic induction (thermal-explosion) times of pure N2O vapour at the coast state (46.45 bar) and at 1 bar, constant
    pressure, GRI-Mech 3.0 through Cantera (SIM; GRI-3.0 is not validated for high-pressure N2O decomposition: order of
    magnitude only), and conduction loss times r^2/(lambda1 alpha) of 1-5 mm passages (CO2 transport surrogate, ASSUMED,
    as in report section 2.1), for a Semenov-type comparison;
  - constant-volume (UV) equilibrium pressure of the leak inventory reacting in the 300.9 cm3 chamber, without and with a
    fuel surrogate (C2H4 at O/F 8, ASSUMED surrogate for ABS pyrolysis vapour): an upper bound with no venting;
  - closure surge of the bleed flow (Joukowsky), bleed jet reaction and stuck-open flows per orifice and tap set.
usage: python -I purge_hazard_v2p4.py RETAINED_VAPOUR_V341_JSON OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import cantera as ct
import CoolProp.CoolProp as CP


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def t_ind(T, P, X='N2O:1', tend=200.0, dT=400.0):
    g = ct.Solution('gri30.yaml')
    g.TPX = T, P, X
    r = ct.IdealGasConstPressureReactor(g, energy='on', clone=False)
    net = ct.ReactorNet([r])
    t = 0.0
    while t < tend:
        t = net.step()
        if r.T > T + dT:
            return t
    return None


def uv_bound(m_n2o, V, T_gas, m_fuel=0.0):
    """N2O (and fuel) added to a chamber of volume V holding air at 1 bar and T_gas; react at constant U and V."""
    g = ct.Solution('gri30.yaml')
    g.TPX = T_gas, 101325.0, 'O2:0.21, N2:0.79'
    m_air = g.density * V
    # mix at T_gas (N2O and fuel taken at T_gas: the added sensible heat is small against the reaction heat)
    W = g.molecular_weights; i = {k: g.species_index(k) for k in ('N2O', 'O2', 'N2', 'C2H4')}
    Y = np.zeros(g.n_species)
    m_tot = m_air + m_n2o + m_fuel
    Y[i['O2']] = 0.233 * m_air / m_tot; Y[i['N2']] = 0.767 * m_air / m_tot
    Y[i['N2O']] = m_n2o / m_tot; Y[i['C2H4']] = m_fuel / m_tot
    g.TDY = T_gas, m_tot / V, Y
    p0 = g.P
    g.equilibrate('UV')
    return dict(P_bar_abs=g.P / 1e5, T_K=g.T, P0_bar_abs=p0 / 1e5)


def main(trade_f, out_f):
    TR = json.load(open(trade_f)); fl = TR['flows']
    P_coast = 46.45e5
    TPS = (1.0, 1.5, 2.0, 2.5, 3.0)
    # (1) seat leak at the acceptance (report section 3.5): 10 sccm GN2 at 56 bar -> liquid N2O factor x4.6 (laminar) to x6.5 (orifice)
    rho_n2_std = 1.2506                                       # kg/m3 at 0 C, 1 atm
    m_n2 = 10e-6 / 60 * rho_n2_std                            # kg/s
    leak_acc = [m_n2 * 4.6, m_n2 * 6.5]
    leak_fault = [13.5e-6, 82e-6]                             # Mechanical Class V-scaled and 15 um particle cases (report section 3.5)
    coast_s = 22.21                                            # longest A1 coast in the leak-ceiling basis (report section 3.5)
    exp_base = [0.09, 0.16]                                    # E0 -> E1, MV ramping (v2.8, no purge)
    # with the PURGE the MV is open with the pintle seated from the PURGE command: MV opening 0.35 s, purge Tp, close and confirm
    # 0.05 s, then E0 -> E1 (gate 0.09-0.16 s)
    exp_purge = {f'Tp{Tp}': [0.35 + Tp + 0.05 + 0.09, 0.35 + Tp + 0.05 + 0.16] for Tp in TPS}
    leak = dict(acceptance_kg_s=leak_acc, fault_kg_s=leak_fault,  # kg/s (run of 08:56 mislabelled these g_s; values unchanged)
                coast_g=dict(acceptance=[x * coast_s * 1e3 for x in leak_acc], fault=[x * coast_s * 1e3 for x in leak_fault]),
                exposure_MV_open_pintle_seated_s=dict(v2p8_no_purge=exp_base, **exp_purge),
                purge_exposure_g={k: dict(acceptance=[leak_acc[0] * v[0] * 1e3, leak_acc[1] * v[1] * 1e3], fault=[leak_fault[0] * v[0] * 1e3, leak_fault[1] * v[1] * 1e3])
                                  for k, v in exp_purge.items()},
                note='the segment is at P_tank through the coast (S1) whether the MV is open or not, so the leak rate does not change with the PURGE; '
                     'the PURGE changes only what backs the leak (tank instead of the segment)')
    leak['G_ox_kg_m2s'] = dict(acceptance=[x / 491e-6 for x in leak_acc], fault=[x / 491e-6 for x in leak_fault], floor_12p5pct_min=25.0)
    # (2) decomposition: adiabatic induction times and conduction times
    Ts = (700.0, 800.0, 850.0, 900.0, 950.0, 1000.0, 1050.0, 1092.65, 1150.0, 1200.0)
    ind = {}
    for P in (P_coast, 101325.0):
        for T in Ts:
            ind[f'{P/1e5:.2f}bar|{T:.0f}K'] = t_ind(T, P)
    cond = {}
    for T in (900.0, 1000.0, 1092.65):
        rho = P_coast * 0.044013 / (8.314462 * T)
        cp = CP.PropsSI('C', 'T', T, 'P', P_coast, 'CO2')     # surrogate (ASSUMED)
        k = CP.PropsSI('L', 'T', T, 'P', P_coast, 'CO2')
        a = k / (rho * cp)
        cond[f'{T:.0f}K'] = dict(alpha_m2_s=a, k_W_mK=k, rho_kg_m3=rho,
                                 slab_halfwidth_1mm_s=(1e-3) ** 2 / (2.4674 * a),
                                 cylinder_r2p75mm_s=(2.75e-3) ** 2 / (5.7832 * a),
                                 cylinder_r5mm_s=(5e-3) ** 2 / (5.7832 * a))
    # (3) constant-volume bounds in the chamber
    V = 300.9e-6
    uv = {}
    for lab, m in (('acceptance_purge_Tp3', leak['purge_exposure_g']['Tp3.0']['acceptance'][1]),
                   ('fault_purge_Tp3', leak['purge_exposure_g']['Tp3.0']['fault'][1]),
                   ('fault_coast', leak['coast_g']['fault'][1]),
                   ('pintle_fault_2g', 2.0), ('pintle_fault_5g', 5.0)):
        for Tg in (300.0, 800.0):
            uv[f'{lab}|{m:.3f}g|N2O_only|gas{Tg:.0f}K'] = uv_bound(m * 1e-3, V, Tg)
            uv[f'{lab}|{m:.3f}g|fuel_OF8|gas{Tg:.0f}K'] = uv_bound(m * 1e-3, V, Tg, m_fuel=m * 1e-3 / 8.0)
    # (4) bleed closure surge, jet reaction, stuck-open flows
    rho_l = 811.7
    a_l = CP.PropsSI('A', 'T', 289.48, 'Q', 0, 'NitrousOxide')
    L_col = (278.75 + 180.25 + 67.03) * 1e-3                   # MV to FD-01: wall line + hose + riser (v3.4.1)
    surge, jet, stuck = {}, {}, {}
    dp = P_coast - 101325.0
    for key, f_ in fl.items():
        nt = f_['n_taps']; Ql = f_['Q_liquid_cm3_s_per_tap'] * 1e-6
        o = float(key.split('|')[0]); A = math.pi / 4 * (o * 1e-3) ** 2
        for lab, D in (('hose_ID10.59', 10.59e-3), ('wall_line_7.747', 7.747e-3)):
            u = nt * Ql / (math.pi / 4 * D ** 2)
            dpj = rho_l * a_l * u / 1e5
            surge[f'{key}|{lab}'] = dict(u_m_s=u, joukowsky_instant_bar=dpj, two_L_over_a_ms=2 * L_col / a_l * 1e3,
                                         slow_closure_bar={f'tc{tc*1e3:.0f}ms': dpj * min(1.0, 2 * L_col / (a_l * tc)) for tc in (0.01, 0.02, 0.03)})
        md = f_['mdot_liquid_g_s_per_tap'] * 1e-3
        jet[key] = dict(per_tap_N=[md * math.sqrt(2 * dp / rho_l), 2 * 0.70 * A * dp], all_taps_same_direction_N=[nt * md * math.sqrt(2 * dp / rho_l), nt * 2 * 0.70 * A * dp],
                        note='range: mdot x sqrt(2 dp / rho_l) (liquid-velocity momentum) to 2 Cd A dp (incompressible jet with vena contracta); flashing jet within, TO-VERIFY')
        stuck[key] = dict(one_valve_stuck_open_g_s=0.0, both_valves_of_one_tap_g_s=f_['mdot_liquid_g_s_per_tap'],
                          fraction_of_100pct=f_['mdot_liquid_g_s_per_tap'] / 264.08)
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/purge_hazard_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={'retained_vapour_v341_v2p4.json': sha16(trade_f)}, cantera=ct.__version__, mechanism='gri30.yaml',
               leak=leak, induction_s=ind, conduction_s=cond, uv_bounds=uv, closure_surge=surge, jet_reaction=jet, stuck_open=stuck,
               liquid_sound_speed_m_s=a_l, column_length_m=L_col,
               tags=dict(leak='DERIVED (acceptance LEAD; fault leaks Mechanical ESTIMATE)', induction='SIM (Cantera GRI-3.0; not validated for this regime, order of magnitude)',
                         conduction='DERIVED (CO2 transport surrogate ASSUMED)', uv='SIM (Cantera UV equilibrium; C2H4 fuel surrogate ASSUMED); no venting, upper bound',
                         surge='DERIVED (Joukowsky, CoolProp saturated-liquid sound speed, rigid pipe: upper bound; hose compliance lowers it)',
                         jet='DERIVED bounds', stuck='DERIVED (two NC valves in series per tap)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print('leak acceptance kg/s', ['%.2e' % x for x in leak_acc], 'coast g', ['%.4f' % x for x in leak['coast_g']['acceptance']], 'fault coast g', ['%.3f' % x for x in leak['coast_g']['fault']])
    for k, v in leak['purge_exposure_g'].items():
        print('purge', k, 'exposure s', exp_purge[k], 'acc g %.4f-%.4f' % tuple(v['acceptance']), 'fault g %.3f-%.3f' % tuple(v['fault']))
    print('G_ox', leak['G_ox_kg_m2s'])
    for k, v in ind.items():
        print('t_ind', k, v)
    for k, v in cond.items():
        print('cond', k, json.dumps(v))
    for k, v in uv.items():
        print('UV', k, '%.2f bar abs, %.0f K (P0 %.2f)' % (v['P_bar_abs'], v['T_K'], v['P0_bar_abs']))
    for k, v in surge.items():
        print('surge', k, json.dumps(v))
    for k, v in jet.items():
        print('jet', k, json.dumps(v))
    print('sound speed', a_l)
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
