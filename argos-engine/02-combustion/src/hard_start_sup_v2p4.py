"""Hard-start supplements for the v2.4 sequence (Combustion v2.4, RC-01 / RC-02 / RC-13g; 2026-10-13).

Re-uses hard_start_v2p4 (same models; its JSON for the lifts and cold-flow states) and adds:
  1. inventory and two-component credible-case ESTIMATE at the deadlines W 0.40 s (liquid segment), 0.75 s and 0.85 s
     (gas or vapour possible in the segment; 0.85 s adopted in v2.4; evaluated as if the line turns out liquid-full, which
     is the inventory worst case), 12.5 % lift, 20 C and the A1 relight state;
     decomposition products; inputs as hard_start_v2p4 section 5 (ASSUMED);
  2. fuel available to the fast part at a cold pad start: torch propane only (combustion.json v2.3 torch sizing) and the
     N2O mass it can burn at stoichiometry (N2O/C3H8 O/F_st 9.98, DERIVED);
  3. cold-flow (unlit) chamber pressure against lift up to 100 % flow, for the flame-out rule (lit / cold ratio);
  4. liquid left in the chamber after a no-light and two evaporation-time ESTIMATES for the post-no-light wait
     (wall conduction from the ABS port surface into a 186 K film; N2 purge sensible-heat bound);
  5. coast leak ceiling (RC-13g) on the v2.4 basis.
usage: python -I hard_start_sup_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hard_start_v2p4 as HS
import grain_q1d as Q

FL = 'NitrousOxide'


def cold_chamber_wide(mdot, T1, hi=40e5):
    h0 = HS.h_liq(T1)
    lo = HS.PAMB * 1.0005
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if HS.AT * HS.throat_flux(mid, h0) > mdot:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def credible(key, lifts, cold, W, prod):
    L = lifts[key]; c = cold[key]
    m_inv = HS.inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]
    rows = []
    V = HS.V_CH['author_284.6cm3']
    m_vap = c['vapour_in_chamber_g']['author_284.6cm3'] * 1e-3
    for t_res in (0.02, 0.06):
        m_fast = min(m_vap + c['liquid_flow_kg_s'] * t_res, m_inv)
        m_pool = max(m_inv - m_fast, 0.0)
        for q in (0.5e6, 2.0e6):
            A_wet = math.pi * 0.025 * 0.230 + math.pi / 4 * 0.054 ** 2
            tau_pool = max(m_pool * 375e3 / (q * A_wet), 1e-3)
            for tf in (1e-3, 5e-3):
                pk = HS.vented_peak1(m_pool, tau_pool, 'tophat', V, prod, m_fast=m_fast, tau_fast=tf)
                rows.append(dict(t_res_s=t_res, q_W_m2=q, tau_fast_s=tf, m_fast_g=1e3 * m_fast, m_pool_g=1e3 * m_pool,
                                 tau_pool_s=tau_pool, P_peak_bar=pk / 1e5))
    return dict(inventory_g=1e3 * m_inv, rows=rows, P_peak_range_bar=[min(r['P_peak_bar'] for r in rows), max(r['P_peak_bar'] for r in rows)])


def main(d):
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    lifts = J['ignition_lifts']['v']; cold = J['cold_flow_at_ignition_lift']['v']
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/hard_start_sup_v2p4.py', base='hard_start_v2p4.json')
    prod = HS.products('dec', 293.15)
    # 1. credible case at the adopted deadlines
    cc = {}
    for key in ('20C|0.125', 'A1_relight|0.125'):
        for W in (0.40, 0.75, 0.85):
            cc[f'{key}|W{W:.2f}'] = credible(key, lifts, cold, W, prod)
    res['credible_case_at_adopted_W'] = dict(v=cc, tag='ESTIMATE (inputs ASSUMED as hard_start_v2p4 section 5); decomposition products; '
                                             'W counted from the ignition-lift command (E1); 284.6 cm3')
    # 2. fuel available at a cold pad start
    mf_torch = 9.1e-5          # kg/s propane (combustion.json v2.3 igniter.torch_sizing, DERIVED/CEA)
    OF_st = (10 * 44.013) / 44.097
    fu = {}
    for hold in (0.15, 0.30, 0.45):
        mfu = mf_torch * hold
        fu[f'{hold:.2f}s'] = dict(propane_g=1e3 * mfu, N2O_burnable_at_stoich_g=1e3 * mfu * OF_st)
    res['fuel_for_fast_part_cold_pad'] = dict(v=fu, OF_stoich_N2O_C3H8=OF_st, tag='DERIVED: torch propane flow 0.091 g/s over the torch-on time '
                                              'before Pc confirmation; grain pyrolysis before main ignition not credited (unknown)')
    # 3. cold-flow chamber pressure against thrust fraction (20 C, initial port)
    tk = HS.tank_state('20C')[0]
    cp = {}
    for fr in (0.125, 0.20, 0.35, 0.50, 0.75, 1.00):
        h, s = HS.lift_for_fraction(fr, HS.tank_state('20C')[0])
        P1 = tk.P - 2.5e5 * (s['mox'] / 0.25) ** 2
        m = HS.mdot_cold(h, P1, tk.T, 1.3e5)
        Pc_cold = cold_chamber_wide(m, tk.T)
        m = HS.mdot_cold(h, P1, tk.T, Pc_cold); Pc_cold = cold_chamber_wide(m, tk.T)
        cp[f'{fr:.3f}'] = dict(lift_m=h, lit_Pc_Pa=s['Pc'], cold_mdot_kg_s=m, cold_Pc_Pa=Pc_cold, ratio_cold_to_lit=Pc_cold / s['Pc'])
    res['cold_vs_lit_Pc'] = dict(v=cp, tag='DERIVED: unlit chamber fed by Dyer cold flow at the lit lift (Cd 0.70 ASSUMED), HEM throat, '
                                 'line loss 2.5 bar at 0.25 kg/s (v2 basis); 20 C, initial port')
    # 4. post-no-light liquid and evaporation ESTIMATES
    ev = {}
    k_abs, rho_abs, c_abs = 0.17, 1050.0, 1400.0         # ABS (ASSUMED handbook class values)
    alpha = k_abs / (rho_abs * c_abs)
    A_port = math.pi * 0.025 * 0.230
    for key in ('20C|0.125', 'A1_relight|0.125'):
        c = cold[key]; L = lifts[key]
        T_film = c['T_K']; dT = 293.15 - T_film
        hfg = CP.PropsSI('H', 'P', c['P2_Pa'], 'Q', 1, FL) - CP.PropsSI('H', 'P', c['P2_Pa'], 'Q', 0, FL)
        for W in (0.40, 0.75, 0.85):
            m_inv = HS.inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)[0]
            m_liq = m_inv * (1 - c['quality'])
            E = m_liq * hfg
            # semi-infinite wall: Q(t) = 2 k dT sqrt(t / (pi alpha)) per m2 over the port area, film spread over the port (best case)
            t_cond = (E / (A_port * 2 * k_abs * dT / math.sqrt(math.pi * alpha))) ** 2
            # N2 purge at 10 g/s, 293 K in, leaving at the film temperature (100 % effectiveness bound) and at 20 % effectiveness
            mdN2 = 0.010; cpN2 = 1040.0
            t_n2_ideal = E / (mdN2 * cpN2 * dT); t_n2_20 = t_n2_ideal / 0.2
            ev[f'{key}|W{W:.2f}'] = dict(inventory_g=1e3 * m_inv, flash_quality=c['quality'], liquid_left_g=1e3 * m_liq, h_fg_J_kg=hfg,
                                         energy_to_evaporate_J=E, t_wall_conduction_film_s=t_cond, t_N2_purge_10g_s_ideal_s=t_n2_ideal,
                                         t_N2_purge_10g_s_eff20pct_s=t_n2_20)
    res['post_no_light_evaporation'] = dict(v=ev, tag='ESTIMATE: liquid left = inventory x (1 - flash quality) with no drainage (horizontal '
                                            'bound); wall conduction assumes the film spread over the port (lower bound on time); N2 purge 10 g/s '
                                            '(ASSUMED stand capability), effectiveness 100 % (bound) and 20 % (ASSUMED); ABS k 0.17, rho 1050, '
                                            'c 1400 (ASSUMED). A pool (not a film) evaporates far slower: a 20 cm3 pool below a horizontal throat '
                                            'lip (review RC-02) is excluded by firing vertical, nozzle down')
    # 5. coast leak ceiling (RC-13g)
    fast = [cold[k]['vapour_in_chamber_g']['author_284.6cm3'] + 1e3 * cold[k]['liquid_flow_kg_s'] * t
            for k in ('20C|0.125', 'A1_relight|0.125') for t in (0.02, 0.06)]
    coast = 22.21
    res['coast_leak_ceiling'] = dict(fast_part_g=[min(fast), max(fast)], longest_A1_coast_s=coast,
                                     ceiling_g_s=0.10 * min(fast) / coast,
                                     rule='accumulated seat leak over the longest A1 coast <= 10 % of the smallest credible fast part',
                                     tag='DERIVED (v2.3 used 10 % of the 8.74 g single-lift inventory over 22.2 s = 0.039 g/s; RC-02 '
                                         'changed the basis); coast 22.21 s = A1 v2 cycle (dispersed p99 v3: 19.1 s)')
    fn = os.path.join(d, 'hard_start_sup_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    for k, v in cc.items():
        print('credible', k, round(v['inventory_g'], 2), 'g', [round(x, 1) for x in v['P_peak_range_bar']])
    print('fuel', json.dumps(fu))
    for k, v in cp.items():
        print('cold/lit', k, round(v['lit_Pc_Pa'] / 1e5, 2), round(v['cold_Pc_Pa'] / 1e5, 2), round(v['ratio_cold_to_lit'], 3), round(v['cold_mdot_kg_s'], 4))
    for k, v in ev.items():
        print('evap', k, {kk: round(vv, 2) for kk, vv in v.items()})
    print('leak', json.dumps(res['coast_leak_ceiling'])[:400])
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])
