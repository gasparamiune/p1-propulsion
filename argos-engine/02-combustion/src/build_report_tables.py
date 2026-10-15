"""Markdown tables for 02-combustion/REPORT.md generated from the v2 data files (Combustion v2, 2026-10-12).

Every number in a table comes from a data file named in the table caption; nothing is typed by hand.
usage: python build_report_tables.py DATADIR [name ...]
  Prints the named tables (all when no name is given) to stdout, so the tables in the REPORT text can be checked against
  the data. (The 2026-10-12 version also filled a report template; subagents do not write report files, so the lead saves
  the report text and this script only prints.)
"""
from __future__ import annotations
import csv, glob, json, math, os, re, sys
import numpy as np, pandas as pd


def f(v, nd=2):
    if v is None:
        return 'n/a'
    if isinstance(v, str):
        return v
    try:
        if not np.isfinite(v):
            return 'n/a'
    except TypeError:
        return str(v)
    if nd == 0:
        return f'{v:.0f}'
    return f'{v:.{nd}f}'


def md(header, rows, caption):
    out = [f'*{caption}*', '', '| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    for r in rows:
        out.append('| ' + ' | '.join(str(x) for x in r) + ' |')
    return '\n'.join(out) + '\n'


def J(path):
    return json.load(open(path))


def build(D):
    T = {}
    v2 = os.path.join(D, 'v2')
    # ---------------- operating points (S230, 20 C, initial port) ----------------
    npf = J(os.path.join(v2, 'nozzle_perf_v2.json'))
    ops = npf['grains']['v2_S230_straight_L230']['ops']
    cps = J(os.path.join(v2, 'chamber_port_state_v2.json'))['states'] if os.path.exists(os.path.join(v2, 'chamber_port_state_v2.json')) else {}
    tm = pd.read_csv(os.path.join(v2, 'engine_S230', 'throttle_map_v2.csv'), comment='#')
    rows = []
    for o in ops:
        sel = tm[(np.isclose(tm.P_tank_Pa, 5.0e6)) & (np.isclose(tm.D_port_m, 0.025)) & (np.isclose(tm.frac, o['frac']))]
        lift = sel.lift_m.iloc[0] * 1e3 if len(sel) else float('nan')
        dpc = sel.dP_over_Pc.iloc[0] if len(sel) else float('nan')
        cs = cps.get(str(o['frac'])) or cps.get(o['frac']) or {}
        rows.append([f(o['frac'] * 100, 1), f(o['F'], 1), f(o['Pc'] / 1e5, 2), f(o['OF'], 2), f(o['mox'] * 1e3, 1), f(o['mf'] * 1e3, 1),
                     f(o['Isp'], 1), f(lift, 3), f(dpc, 2), f(cs.get('Tc_K'), 0), f(cs.get('T0_delivered_K'), 0)])
    T['opoints'] = md(['throttle %', 'F [N]', 'Pc [bar]', 'O/F', 'mdot_ox [g/s]', 'mdot_f [g/s]', 'Isp_SL [s]', 'pintle lift [mm]',
                       'dP_inj/Pc', 'Tc CEA [K]', 'T0 del. [K]'], rows,
                      'S230 operating points, 20 C saturated tank (50.5 bar), initial port 25 mm (SIM grain_q1d v2; data/v2/nozzle_perf_v2.json, '
                      'engine_S230/throttle_map_v2.csv, chamber_port_state_v2.json). Lift and dP/Pc from the throttle-map row at P_tank 50 bar '
                      '(nearest map row); T0 del. = eta_c*^2 Tc with eta_c* 0.92 ASSUMED.')
    # ---------------- thermochemistry ----------------
    th = pd.read_csv(os.path.join(D, 'thermo', 'ABS_TYP_v1_shifting_v1.csv'), comment='#')
    rows = []
    for of in (3.0, 4.0, 5.0, 5.5, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0):
        s = th[(np.isclose(th.Pc_bar, 25.0)) & (np.isclose(th.OF, of))]
        if len(s):
            r = s.iloc[0]
            rows.append([f(of, 2), f(r.cstar_m_s, 0), f(r.Tc_K, 0), f(r.MW_c, 2), f(r.gamma_c, 4), f(r['Isp_vac_eps2.0_s'], 1),
                         f(r['Isp_SL_eps2.0_s'], 1), f(r['pe_eps2.0_Pa'] / 101325, 2)])
    T['thermo_of'] = md(['O/F', 'c* [m/s]', 'Tc [K]', 'MW', 'gamma_c', 'Isp_vac eps 2 [s]', 'Isp_SL eps 2 [s]', 'pe/pa eps 2'], rows,
                        'N2O/ABS_TYP_v1 at Pc 25 bar, CEA shifting equilibrium, ideal (no efficiencies), gas-phase N2O at 298 K '
                        '(data/thermo/ABS_TYP_v1_shifting_v1.csv; CEA)')
    hs = pd.read_csv(os.path.join(D, 'thermo', 'hf_sensitivity_v1.csv'), comment='#')
    rows = []
    for _, r in hs.iterrows():
        rows.append([r.card, f(r.Pc_bar, 2), f(r.cstar_peak_m_s, 0), f(r.OF_at_peak, 2), f(r['cstar_OF5.0'], 0), f(r['cstar_OF7.76'], 0)])
    T['hfsens'] = md(['card', 'Pc [bar]', 'c* peak [m/s]', 'O/F at peak', 'c* at O/F 5 [m/s]', 'c* at O/F 7.76 [m/s]'], rows,
                     'c* sensitivity to fuel composition and enthalpy-of-formation sources (data/thermo/hf_sensitivity_v1.csv; CEA; '
                     'card definitions and citations in src/cea_cards.py)')
    lc = J(os.path.join(D, 'thermo', 'n2o_liquid_correction_v1.json'))
    rows = [[f(p['Pc_bar'], 2), f(p['OF'], 2), f(p['cstar_gas'], 0), f(p['cstar_liq'], 0), f(p['dcstar_pct'], 2), f(p['Tc_gas'], 0),
             f(p['Tc_liq'], 0)] for p in lc['points']]
    T['n2o_liq'] = md(['Pc [bar]', 'O/F', 'c* gas N2O [m/s]', 'c* liquid N2O 20 C [m/s]', 'dc* [%]', 'Tc gas [K]', 'Tc liquid [K]'], rows,
                      f"Effect of injecting liquid N2O at 20 C instead of gas at 298 K (hf effective {lc['hf_effective_liquid_kJ_mol']:.2f} kJ/mol; "
                      'data/thermo/n2o_liquid_correction_v1.json; CEA + CoolProp)')
    # ---------------- N2O property validation ----------------
    nv = J(os.path.join(v2, 'n2o_validation_v2.json'))
    rows = [[band, f(d.get('P'), 2), f(d.get('rho_l'), 2), f(d.get('rho_v'), 2), f(d.get('h_fg'), 2)] for band, d in nv['max_abs_dev_pct'].items()]
    T['n2o_val'] = md(['T band', 'P_sat', 'rho_l', 'rho_v', 'h_fg'], rows,
                      'Maximum absolute deviation [%] CoolProp 8.0 (Lemmon & Span EOS) vs the ESDU 91022 correlations '
                      '(data/v2/n2o_validation_v2.json; LITERATURE vs LITERATURE)')
    # ---------------- ceiling vs time ----------------
    for name, fn, cap in (('ceiling_A1', 'ceiling_vs_time_v2.csv', 'A1 tank of gnc.json v1 (2.06 L, 1.30 kg)'),
                          ('ceiling_BL', 'ceiling_vs_time_BLtank_v2.csv', 'baseline tank of the lead decision 2026-10-12 (3.17 L, 2.00 kg)')):
        p = os.path.join(v2, fn)
        if not os.path.exists(p):
            T[name] = f'*{cap}: not available (run pending)*\n'
            continue
        c = pd.read_csv(p)
        rows = [[r.tank_model, f(r.T0_C, 0), f(r.F_ceiling_at_0s_N, 0), f(r.t_500N_held_s, 2), f(r.t_liquid_depletion_s, 2),
                 f(r.F_ceiling_at_liquid_end_N, 0), f(r.P_tank_at_liquid_end_bar, 1), f(r.ox_used_to_liquid_end_kg, 3),
                 f(r.impulse_to_liquid_depletion_Ns, 0)] for _, r in c.iterrows()]
        T[name] = md(['tank model', 'T0 [C]', 'ceiling t=0 [N]', '500 N held [s]', 'liquid end [s]', 'ceiling at liquid end [N]',
                      'P_tank at liquid end [bar]', 'N2O used [kg]', 'impulse to liquid end [N s]'], rows,
                     f'Continuous 500 N command from t = 0, {cap}, S230 grain, Dyer pintle Cd 0.70 (data/v2/{fn}; SIM). '
                     'eq = equilibrium tank; neqE1e+03/E1e+02 = non-equilibrium two-CV tank with evaporation coefficient E (ZK-type band)')
    sc = J(os.path.join(v2, 'supercharge_trade_v2.json'))
    rows = [[k, f(v.get('P_start_bar'), 1), f(v.get('P_at_MECO_bar'), 1), f(v.get('P_at_relight_bar'), 1), f(v.get('P_end_bar'), 1),
             v.get('note', '')] for k, v in sc.items() if isinstance(v, dict)]
    T['supercharge'] = md(['option', 'P start [bar]', 'P at MECO [bar]', 'P at relight [bar]', 'P end [bar]', 'note'], rows,
                          'Supercharge trade on the DC-A1 v1 profile and tank (data/v2/supercharge_trade_v2.json; SIM, equilibrium tank, '
                          'N2 insoluble ASSUMPTION)')
    rows = []
    for fn, lab in (('settling_v2.json', 'gnc.json v1'), ('settling_v2wip_preview.json', 'gnc.json v2')):
        if not os.path.exists(os.path.join(v2, fn)):
            continue
        for k, v in J(os.path.join(v2, fn)).items():
            if isinstance(v, dict):
                rows.append([k.split('_')[0] + f' ({lab})', f(v.get('coast_s'), 2), f(v.get('a_min_mps2'), 2), f(v.get('time_negative_s'), 2),
                             f(v.get('settled_interval_before_relight_s'), 2), f(v.get('a_mean_last_0p5s_mps2'), 2), f(v.get('Bond'), 0),
                             f(v.get('t_settle_estimate_s', v.get('t_settle_s')), 2)])
    T['settling'] = md(['duty cycle', 'coast [s]', 'a_min [m/s2]', 'time a<0 [s]', 'settled before relight [s]', 'a mean last 0.5 s [m/s2]',
                        'Bond', 't_settle [s]'], rows, 'Propellant settling before relight (data/v2/settling_v2.json, settling_v2wip_preview.json; '
                        'DERIVED from the GNC acceleration histories; coast = first engine-off window; the gnc.json v2 rows were computed on '
                        'the 19:15Z working-copy snapshot, acceleration differences to the published files <= 1e-4 m/s2)')
    # ---------------- injector ----------------
    ic = J(os.path.join(v2, 'injector_compare_v2.json'))
    rows = []
    for r in ic['ceiling_vs_Cd']:
        rows.append([f(r['T_tank_C'], 0), r.get('model', 'Dyer'), f(r['Cd'], 2), f(r['F_ceiling_N'], 0), r['limit'], f(r.get('lift_mm'), 2),
                     f(r['Pc_Pa'] / 1e5, 2), f(r['dP_over_Pc'], 2)])
    T['inj_ceiling'] = md(['T [C]', 'model', 'Cd', 'ceiling [N]', 'limit', 'lift [mm]', 'Pc [bar]', 'dP/Pc'], rows,
                          'Thrust ceiling vs discharge coefficient (data/v2/injector_compare_v2.json ceiling_vs_Cd; SIM)')
    rows = []
    for r in ic['ceiling_worst_model']['rows']:
        rows.append([f(r['T_tank_C'], 0), r['model'], f(r['Cd_nominal'], 2), f(r['G_ratio_to_Dyer'], 3), f(r['Cd_eff_vs_Dyer'], 3),
                     f(r['F_ceiling_N'], 1), r.get('limit', '')])
    extra = ic['ceiling_worst_model'].get('min_Cd_eff_for_500N') or ic['ceiling_worst_model'].get('Cd_eff_min_for_500N')
    T['inj_worst'] = md(['T [C]', 'model', 'Cd', 'G_model/G_Dyer', 'Cd_eff vs Dyer', 'ceiling [N]', 'limit'], rows,
                        'Injector model spread at the max-thrust point: SPI and HEM expressed as an effective Dyer Cd '
                        f'(data/v2/injector_compare_v2.json ceiling_worst_model; minimum Cd_eff for 500 N: ' + ', '.join(f'{v:.3f} at {k[:-1]} C' for k, v in extra.items()) + ')')
    # ---------------- feed line ----------------
    fl = J(os.path.join(v2, 'feed_line_checks_v2.json'))
    bv = fl['budget_verdict']
    T['feed_budget'] = md(['item', 'value'], [
        ['total dp, Cv 3 isolation valve + Cv 2.2 filter [kPa]', f(bv['total_dp_Cv3_valve_Cv2p2_filter_Pa'] / 1e3, 1)],
        ['total dp, Cv 1.5 valve + Cv 1.0 filter [kPa]', f(bv['total_dp_Cv1p5_valve_Cv1_filter_Pa'] / 1e3, 1)],
        ['line-loss budget used by the simulations at 0.26 kg/s [kPa]', f(bv['budget_at_0p26_Pa'] / 1e3, 1)],
        ['requirement', bv['requirement']]], 'Feed-line pressure-drop budget at 0.26 kg/s, 20 C (data/v2/feed_line_checks_v2.json; DERIVED)')
    rows = [[f(r['P_tank_Pa'] / 1e5, 0), f(r['T_N2_ideal_isentropic_K'], 0), f(r['T_N2_CoolProp_isentropic_K'], 0),
             f(r['T_N2O_vapour_CoolProp_isentropic_K'], 0)] for r in fl['priming']['rows']]
    T['priming'] = md(['P_tank [bar]', 'N2 ideal [K]', 'N2 CoolProp [K]', 'N2O vapour CoolProp [K]'], rows,
                      'Upper-bound gas temperature for adiabatic compression of gas trapped in a dead-ended line when the isolation valve '
                      'opens fast (data/v2/feed_line_checks_v2.json priming; DERIVED)')
    rows = [[r['gas'], f(r['P_Pa'] / 1e5, 1), f(r['L_m'], 2), f(r['V_transducer_m3'] * 1e6, 2), f(r['f_n_Hz'], 0), f(r['zeta'], 3),
             f(r['phase_lag_deg_at_20Hz'], 2), f(r['phase_lag_deg_at_50Hz'], 2)]
            for r in fl['sense_line'] if r['L_m'] <= 0.45 + 1e-9 and r['P_Pa'] < 1.0e6]
    T['sense'] = md(['gas', 'mean P [bar]', 'L [m]', 'V_t [cm3]', 'f_n [Hz]', 'zeta', 'phase lag 20 Hz [deg]', 'phase lag 50 Hz [deg]'], rows,
                    'Pc sense line, 1/8 in tube (1.6 mm ID), at the 12.5 % floor pressure (frequencies are pressure-independent, damping is lower at 25 bar; lengths 0.6 m and the 25 bar rows are in the JSON) (data/v2/feed_line_checks_v2.json sense_line; DERIVED, Bergh-Tijdeman-type lumped model)')
    # ---------------- throttle / plant / failure ----------------
    tt = J(os.path.join(v2, 'throttle_trade_v2.json'))
    rows = [[f(r['frac'] * 100, 1), f(r['Pc_Pa'] / 1e5, 2), f(r['mdot_ox'] * 1e3, 1), f(r['b_lift_m'] * 1e3, 3), f(r['b_dP_over_Pc'], 2),
             f(r['b_dF_dh_N_per_mm'], 0), f(r['ac_quality_x'], 3), f(r['ac_dP_over_Pc'], 2), f(r['a_manifold_tau_s'] * 1e3, 1),
             f(r['c_manifold_tau_s'] * 1e3, 1)] for r in tt['rows']]
    T['throttle_trade'] = md(['throttle %', 'Pc [bar]', 'mdot_ox [g/s]', '(b) pintle lift [mm]', '(b) dP/Pc', '(b) dF/dh [N/mm]',
                              '(a,c) quality after valve', '(a,c) dP/Pc', '(a) manifold tau [ms]', '(c) manifold tau [ms]'], rows,
                             'Throttle architectures: (a) V-ball upstream + fixed injector, (b) variable-area pintle, (c) valve + showerhead, '
                             'evaluated at the v1-grain operating points (O/F 7.76 at 100 %; the S230 points need +6 % oxidiser flow at 100 %, '
                             'which does not change the ranking) (data/v2/throttle_trade_v2.json; SIM/DERIVED)')
    pl = J(os.path.join(v2, 'engine_S230', 'summary_v2.json'))['plant']
    rows = [[f(r['frac'] * 100, 1), f(r['h0_m'] * 1e3, 3), f(r['Pc0_Pa'] / 1e5, 2), f(r['K_h_Pa_per_m'] / 1e8, 2), f(r['dF_dh_N_per_m'] / 1e3, 0),
             f(r['tau_c_s'] * 1e3, 1), f(r['tau_f_s'] * 1e3, 0), f(r['phi'], 3)] for r in pl]
    T['plant'] = md(['throttle %', 'lift h0 [mm]', 'Pc0 [bar]', 'K_h [bar/mm]', 'dF/dh [N/mm]', 'tau_c [ms]', 'tau_f [ms]', 'phi'], rows,
                    'Valve-lift to Pc plant: Pc(s)/h(s) = K_h [(1 - phi)/(1 + tau_c s) + phi/(1 + tau_f s)] (fast chamber filling + slow fuel/thermal-lag mode), fitted to +3 % lift step responses of the '
                    'quasi-1D model (data/v2/engine_S230/summary_v2.json plant; SIM). K_h [bar/mm] = K_h [Pa/m] x 1e-8.')
    fc = J(os.path.join(v2, 'full_stroke_failure_case_v2.json'))
    rows = [[r['grain'], f(r['T_tank_C'], 0), f(r['Pv_bar'], 1), f(r['Cd'], 2), f(r['Pc_full_stroke_bar'], 1), f(r['F_N'], 0), f(r['OF'], 2),
             f(r['dP_over_Pc'], 3)] for r in fc['rows'] if 'S230' in r['grain'] or r['grain'].startswith('v2')]
    if not rows:
        rows = [[r['grain'], f(r['T_tank_C'], 0), f(r['Pv_bar'], 1), f(r['Cd'], 2), f(r['Pc_full_stroke_bar'], 1), f(r['F_N'], 0), f(r['OF'], 2),
                 f(r['dP_over_Pc'], 3)] for r in fc['rows']]
    T['failure'] = md(['grain', 'T [C]', 'P_v [bar]', 'Cd', 'Pc at full stroke [bar]', 'F [N]', 'O/F', 'dP/Pc'], rows,
                      'Pintle stuck at full stroke (4 mm), initial port (data/v2/full_stroke_failure_case_v2.json; SIM). Basis of the lead '
                      'decision: MEOP 45 bar, proof 67.5 bar, software cap Pc <= 25 bar, over-pressure abort ~30 bar.')
    # ---------------- grain / duty cycles ----------------
    gt = pd.read_csv(os.path.join(v2, 'grain_trade_v2.csv'), comment='#')
    g = gt[gt.variant.str.contains('S230')].sort_values(['duty_cycle', 'regression_scale'])
    rows = [[r.duty_cycle, f(r.regression_scale, 1), f(r.burn_s, 2), f(r.impulse_Ns, 0), f(r.N2O_used_kg, 3), f(r.fuel_used_kg, 3), f(r.OF_mean, 2),
             f(r.Isp_mean_s, 1), f(r.web_end_mm, 2), f(r.liquid_N2O_left_kg, 3), f(r.min_ceiling_N, 0), f(r.min_dP_over_Pc, 2),
             f(r.tracking_rms_N, 2)] for _, r in g.iterrows()]
    T['dc_v1'] = md(['DC', 'regr. x', 'burn [s]', 'impulse [N s]', 'N2O [kg]', 'fuel [kg]', 'O/F mean', 'Isp mean [s]', 'web end [mm]',
                     'liquid left [kg]', 'min ceiling [N]', 'min dP/Pc', 'tracking rms [N]'], rows,
                    'S230 grain over the gnc.json v1 duty cycles (data/v2/grain_trade_v2.csv; SIM grain_q1d v2, non-equilibrium tank E 1000 '
                    'for flight, ASSUMED 15 L ground tank for C/D). Regression x = multiplier on the ASSUMED law.')
    p = os.path.join(v2, 'dc_gncv2wip', 'summary_v2.json')
    if os.path.exists(p):
        S = J(p)
        rows = []
        for k, r in S.items():
            if not isinstance(r, dict) or 'burn_s' not in r:
                continue
            rows.append([k.split('-S230')[0], f(r['regression_scale'], 1), (lambda tk: f"{float(tk.split('V=')[1].split(' L')[0]):.2f} L / {float(tk.split('m=')[1].split(' kg')[0]):.2f} kg" if 'V=' in tk and 'm=' in tk else tk)(r['tank']),
                         f(r['burn_s'], 2), f(r.get('gnc_burn_s'), 2), f(r['impulse_Ns'], 0), f(r.get('gnc_impulse_Ns'), 0), f(r['ox_used_kg'], 3),
                         f(r['fuel_used_kg'], 3), f(r['OF_mean'], 2), f(r['w_min_end_mm'], 2), f(r['m_liq_end_kg'], 3), f(r['min_F_ceiling_N'], 0),
                         f(r['ceiling_limited_s'], 2), f(r['tracking_rms_N'], 2)])
        T['dc_v2wip'] = md(['DC', 'regr. x', 'tank', 'burn [s]', 'GNC burn [s]', 'impulse [N s]', 'GNC impulse [N s]', 'N2O [kg]', 'fuel [kg]',
                            'O/F mean', 'web end [mm]', 'liquid left [kg]', 'min ceiling [N]', 'ceiling-limited [s]', 'tracking rms [N]'], rows,
                           'S230 grain over the gnc.json v2 duty cycles (published 2026-10-12 20:34Z; run on the 19:15Z working-copy '
                           'snapshot inputs/snap_gnc_v2wip_20261012T1915, whose F_N/F_cmd_N histories are identical to the published '
                           'files: inputs/gnc_v2_published_20261012T2034/MANIFEST.txt; data/v2/dc_gncv2wip/summary_v2.json; SIM). '
                           'Regression x = multiplier on the ASSUMED law; tank = the volume/load each GNC v2 cycle sizes.')
    else:
        T['dc_v2wip'] = '*GNC v2 preview runs not available*\n'
    G = J(os.path.join(v2, 'engine_S230', 'summary_v2.json'))
    rows = []
    for k in ('DC-C-S230_ground_reg1', 'DC-D-S230_ground_reg1'):
        r = G.get(k)
        if r:
            rows.append([k.split('-S230')[0], f(r['burn_s'], 1), f(r['impulse_Ns'], 0), f(r['ox_used_kg'], 2), f(r['fuel_used_kg'], 3),
                         f(r['w_min_end_mm'], 2), f(r['burnthrough_s'], 1) if r['burnthrough_s'] else 'none'])
    T['dc_ground'] = md(['DC', 'burn [s]', 'impulse [N s]', 'N2O [kg]', 'fuel [kg]', 'web end [mm]', 'burn-through at [s]'], rows,
                        'Ground duty cycles with ONE S230 grain (data/v2/engine_S230/summary_v2.json; SIM). Negative web = burn-through: '
                        'the test plan splits C into 2 and D into 3 grain loads.')
    # ---------------- nozzle ----------------
    e = npf['eps_trade']['v2_S230_straight_L230']
    rows = []
    for r in e:
        rows.append([f(r['frac'] * 100, 1), f(r['Pc_Pa'] / 1e5, 2), f(r['OF'], 2)] + [f(r.get(f'Isp_SL_eps{x:.2f}'), 1) for x in (1.5, 2.0, 2.5, 3.0, 4.0)])
    T['eps_trade'] = md(['throttle %', 'Pc [bar]', 'O/F', 'eps 1.5', 'eps 2.0', 'eps 2.5', 'eps 3.0', 'eps 4.0'], rows,
                        'Ideal sea-level Isp [s] vs expansion ratio with Schmucker separation (data/v2/nozzle_perf_v2.json eps_trade; CEA/DERIVED)')
    sp = pd.read_csv(os.path.join(v2, 'nozzle_perf_v2.csv'), comment='#')
    s = sp[sp.grain.str.contains('S230') & (np.isclose(sp.eps, 2.0) | np.isclose(sp.eps, 3.0) | np.isclose(sp.eps, 1.8))]
    rows = [[f(r.frac * 100, 1), f(r.eps, 1), f(r.Pc_Pa / 1e5, 2), f(r.pe_over_pa, 3), f(r.schmucker_psep_over_pa, 3), 'yes' if r.summerfield_sep else 'no',
             'yes' if r.schmucker_sep else 'no', f(r.eps_sep, 2), f(r.side_load_bound_N, 1), f(r.Isp_ideal_SL_s, 1)] for _, r in s.iterrows()]
    T['separation'] = md(['throttle %', 'eps', 'Pc [bar]', 'pe/pa', 'Schmucker psep/pa', 'Summerfield sep.', 'Schmucker sep.', 'eps_sep',
                          'side-load bound [N]', 'Isp_SL ideal [s]'], rows,
                         'Flow separation and side-load bound, S230 points, eps 2.0 (baseline), 1.8 (throat eroded 11 %) and 3.0 (v0) (data/v2/nozzle_perf_v2.csv; DERIVED). Side-load bound = half the '
                         'circumference attached, half separated over the separated band (upper bound).')
    # ---------------- erosion ----------------
    er = J(os.path.join(v2, 'erosion_S230', 'erosion_dc_v2.json'))
    rows = []
    for k, v in er.items():
        if not isinstance(v, dict) or 'nominal' not in v:
            continue
        nm = k.replace('_neqE1e+03', '').replace('.csv', '')
        row = [nm]
        for var in ('nominal', 'conservative'):
            d = v.get(var, {})
            row += [f(d.get('recession_mm'), 3), f(d.get('dAt_over_At_pct'), 2), f(d.get('Tw_max_K'), 0)]
        lit = v.get('literature_scaled_mm')
        row += [f'{lit[0]:.3f}-{lit[1]:.3f}' if isinstance(lit, list) and len(lit) == 2 else 'n/a']
        row += [f(v['nominal'].get('q_in_max_MW_m2'), 1)]
        rows.append(row)
    T['erosion'] = md(['duty cycle', 'nominal recession [mm]', 'nominal dAt/At [%]', 'nominal Tw max [K]', 'conservative recession [mm]',
                       'conservative dAt/At [%]', 'conservative Tw max [K]', 'literature-scaled [mm]', 'q_in max [MW/m2]'], rows,
                      'Graphite throat recession per flight (data/v2/erosion_S230/erosion_dc_v2.json; SIM, semi-global kinetics after '
                      'Rotondi et al. 2024 + NSC; nominal = delivered composition, conservative = CEA ideal composition at T0 = Tc)')
    # ---------------- thermal ----------------
    tb = J(os.path.join(v2, 'thermal_bc_summary_v2.json'))
    rows = [[k, f(p['frac'] * 100, 1), f(p['Pc_Pa'] / 1e5, 2), f(p['OF'], 2), f(p['T0_delivered_K'], 0), f(p['peak_q_conv_Tw600_W_m2'] / 1e6, 2),
             f(p['peak_h_g_Tw600_W_m2K'], 0), f(p['peak_x_throat_m'] * 1e3, 1), f(p['T_aw_at_peak_K'], 0), p['file']] for k, p in tb['points'].items()]
    T['thermal_bc'] = md(['point', 'throttle %', 'Pc [bar]', 'O/F', 'T0 del. [K]', 'peak q (Tw 600 K) [MW/m2]', 'peak h_g [W/m2K]',
                          'x of peak from throat [mm]', 'T_aw at peak [K]', 'CSV'], rows,
                         'Gas-side boundary conditions for FEA (Bartz 1957 with CEA transport, data/v2/thermal_bc_summary_v2.json; DERIVED)')
    sb = J(os.path.join(v2, 'soakback_v2.json'))
    rows = []
    for k, v in sb['insert'].items():
        dc, hc, mat = k.split('|')
        rows.append([dc.split('-S230')[0], hc.replace('hc', ''), mat, f(v['t_burn_end_s'], 1), f(v['Tw_at_shutdown_K'], 0),
                     f(v['T_insert_mean_at_shutdown_K'], 0), f(v['T_retainer_at_shutdown_K'], 0), f(v['T_retainer_peak_K'], 0),
                     f(v['t_peak_after_shutdown_s'], 0), f(v['T_retainer_900s_K'], 0)])
    T['soak_insert'] = md(['DC', 'contact h [W/m2K]', 'retainer', 'last shutdown [s]', 'Tw at shutdown [K]', 'insert mean [K]',
                           'retainer at shutdown [K]', 'retainer peak [K]', 'peak after shutdown [s]', 'retainer at 900 s [K]'], rows,
                          'Throat-insert soak-back into a lumped 0.15 kg retainer (data/v2/soakback_v2.json; DERIVED lumped/1-D model, '
                          'insert 0.081 kg = v3.0 geometry; Mechanical v3.1 insert is larger: FEA required)')
    sw = J(os.path.join(v2, 'soakback_wall_v2.json'))
    rows = []
    for k, v in sw['cases'].items():
        dc, lin, hg = k.split('|')
        rows.append([dc.split('-S230')[0], lin.replace('liner', ''), hg.replace('hg', ''), f(v['T_case_peak_K'], 0), f(v['T_case_peak_K'] - 273.15, 0),
                     f(v['t_peak_s'], 0), f(v['t_last_burn_s'], 1), f(v['T_case_at_last_shutdown_K'], 0), f(v['T_phenolic_surface_max_K'], 0)])
    T['soak_wall'] = md(['DC', 'phenolic liner', 'h_g', 'case peak [K]', 'case peak [C]', 'time of peak [s]', 'last burn ends [s]',
                         'case at last shutdown [K]', 'liner surface max [K]'], rows,
                        'Post-chamber wall stack phenolic + 3.175 mm 6061 (data/v2/soakback_wall_v2.json; DERIVED 1-D, no char/ablation, '
                        'no axial conduction: conservative)')
    # ---------------- ignition ----------------
    ig = J(os.path.join(v2, 'ignition_v2.json'))
    sz = ig['torch']['sizing']
    rows = [[k, f(v, 6) if isinstance(v, float) and abs(v) < 1e-2 else (f(v, 3) if isinstance(v, float) else str(v))]
            for k, v in sz.items() if not isinstance(v, (list, dict)) and k != 'note']
    rows.append(['N2O orifice diameter [mm] (Dyer, Cd 0.65)', ', '.join(f"{x['d_orifice_mm']:.3f} at {x['T_C']:.0f} C" for x in sz['n2o_orifice'])])
    rows.append(['propane flow through 0.30 mm [g/s] (Cd 0.80)', ', '.join(f"{x['mdot_through_0p30mm_gps']:.3f} at {x['T_C']:.0f} C ({'choked' if x['choked'] else 'unchoked'}, Psat {x['Psat_bar']:.1f} bar)" for x in sz['propane'])])
    rows.append(['note', sz.get('note', '')])
    T['torch'] = md(['torch sizing item', 'value'], rows, 'Spark-ignited N2O/propane torch sizing (data/v2/ignition_v2.json torch.sizing; DERIVED/CEA)')
    rows = [[k, f(v, 3)] for k, v in ig['weighted_scores'].items()]
    T['ign_trade'] = md(['option', 'weighted score (0-1)'], rows, 'Igniter trade, weighted scores (data/v2/ignition_v2.json; engineering judgement, criteria in the file)')
    # ---------------- stability ----------------
    sb = J(os.path.join(v2, 'stability_v2.json'))
    rows = [[f(r['D_port_m'] * 1e3, 0), f(r['frac'] * 100, 1), f(r['Pc_Pa'] / 1e5, 2), f(r['OF'], 2), f(r['dP_over_Pc'], 2), f(r['GM_tau1ms'], 1),
             f(r['GM_tau10ms'], 1), 'inf' if not np.isfinite(r['tau_crit_s']) else f(r['tau_crit_s'] * 1e3, 1), f(r['tau_thermal_lag_s'] * 1e3, 0),
             f(r['f_thermal_lag_Hz'], 1), f(r['f_Helmholtz_pre_post_Hz'], 0), f(r['f_1L_Hz'], 0), f(r['f_1T_chamber_Hz'], 0)] for r in sb]
    T['stability'] = md(['port [mm]', 'throttle %', 'Pc [bar]', 'O/F', 'dP/Pc', 'gain margin (tau 1 ms)', 'gain margin (tau 10 ms)', 'tau_crit [ms]',
                         'thermal lag [ms]', 'f thermal lag [Hz]', 'f Helmholtz [Hz]', 'f 1L [Hz]', 'f 1T [Hz]'], rows,
                        'Feed-coupled (chug) stability and acoustic frequencies (data/v2/stability_v2.json; DERIVED double-time-lag model with the '
                        'hybrid fuel path; Karabeyoglu-type low-frequency hybrid modes NOT modelled: test requirement)')
    return T


def main():
    D = sys.argv[1]
    T = build(D)
    names = sys.argv[2:] or sorted(T)
    unknown = [n for n in names if n not in T]
    if unknown:
        raise SystemExit(f'unknown tables: {unknown}; available: {sorted(T)}')
    for n in names:
        print(f'<!-- table {n} -->'); print(T[n])


if __name__ == '__main__':
    main()
