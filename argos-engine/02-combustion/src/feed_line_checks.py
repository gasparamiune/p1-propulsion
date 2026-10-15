"""Feed-line, priming and instrumentation checks v2 (Combustion, 2026-10-12).

Answers Mechanical's requests (mechanical.json v1) and closes ASSUMED feed values used by grain_q1d:
 1) -6 hose (7.9 mm ID, 0.26 m free length, mechanical.json v1) at the v2 maximum oxidiser flow: velocity,
    Reynolds number, Haaland friction, fittings.
 2) line-loss budget: grain_q1d.py assumes dp_line = 2.5 bar at 0.25 kg/s (~mdot^2, ASSUMED); component Cv
    values that keep the real line inside that budget.
 3) surge on valve closure: slow-closure rho L dv/dt and the Joukowsky (instantaneous) bound.
 4) line priming: adiabatic compression of the gas trapped between the isolation valve and a seated pintle
    (N2O decomposition initiation hazard) -> start-sequence requirement.
 5) Pc sense line (1/8 in tube across the gimbal): lumped natural frequency and damping
    (quarter-wave / Helmholtz blend, Poiseuille resistance) -> usable bandwidth for the Pc loop.
Every input is tagged; nothing here is a measurement.
usage: python feed_line_checks.py OUTDIR
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import CoolProp.CoolProp as CP

FL = 'NitrousOxide'


def mu_liq_esdu(T):
    """N2O saturated-liquid viscosity [Pa s], ESDU 91022 correlation as reproduced in the hybrid literature
    (LITERATURE, secondary source; valid ~230 K to near Tc).  Used with a +/-30 % band."""
    Tc = 309.57
    th = (Tc - 5.24) / (T - 5.24)
    return 0.0293423e-3 * math.exp(1.6089 * (th - 1) ** (1 / 3) + 2.0439 * (th - 1) ** (4 / 3))


def haaland(Re, rel_rough):
    return (-1.8 * math.log10((rel_rough / 3.7) ** 1.11 + 6.9 / Re)) ** -2


def hose_and_budget(mdot, T):
    rho = CP.PropsSI('D', 'T', T, 'Q', 0, FL); Ps = CP.PropsSI('P', 'T', T, 'Q', 0, FL)
    a_liq = CP.PropsSI('A', 'T', T, 'Q', 0, FL)
    D = 0.0079; L_hose = 0.26; A = math.pi / 4 * D ** 2
    v = mdot / (rho * A)
    q = 0.5 * rho * v ** 2
    out = dict(T_K=T, mdot_kg_s=mdot, rho_liq_kg_m3=rho, Psat_Pa=Ps, a_liq_CoolProp_m_s=a_liq, v_m_s=v, q_dyn_Pa=q)
    res = {}
    for tag, mu in (('mu_lo', 0.7 * mu_liq_esdu(T)), ('mu_nom', mu_liq_esdu(T)), ('mu_hi', 1.3 * mu_liq_esdu(T))):
        Re = rho * v * D / mu
        for rr_tag, rough in (('smooth_PTFE_1p5um', 1.5e-6), ('rough_25um', 25e-6)):
            f = haaland(Re, rough / D)
            res[f'{tag}_{rr_tag}'] = dict(mu_Pa_s=mu, Re=Re, f_Darcy=f, dp_hose_Pa=f * L_hose / D * q)
    out['hose_friction'] = res
    # minor losses (ASSUMED K values, Idelchik/Crane-type handbook ranges): tank outlet 0.5, tee run 0.3,
    # 2 JIC/AN hose ends 2 x 0.3, forged JIC 90 deg elbow 1.0, bonnet inlet/manifold turn 1.0
    K = dict(tank_outlet=0.5, tee_run=0.3, hose_ends=0.6, elbow_90=1.0, bonnet_inlet_turn=1.0)
    out['K_minor_ASSUMED'] = K
    out['dp_minor_Pa'] = sum(K.values()) * q
    # valve and filter by Cv (US units: dp[psi] = SG (Q[gpm]/Cv)^2)
    Q_gpm = mdot / rho * 15850.32
    SG = rho / 999.0
    out['Q_gpm'] = Q_gpm
    out['dp_iso_valve_Pa'] = {f'Cv_{cv}': SG * (Q_gpm / cv) ** 2 * 6894.76 for cv in (1.5, 3.0, 6.0)}
    out['dp_filter_Pa'] = {f'Cv_{cv}': SG * (Q_gpm / cv) ** 2 * 6894.76 for cv in (1.0, 2.2, 4.0)}
    return out


def surge(mdot, T, L_line=(0.4, 0.5, 0.8), t_close=(0.04, 0.08, 0.15)):
    rho = CP.PropsSI('D', 'T', T, 'Q', 0, FL); a = CP.PropsSI('A', 'T', T, 'Q', 0, FL)
    D = 0.0079; v = mdot / (rho * math.pi / 4 * D ** 2)
    rows = []
    for L in L_line:
        for tc in t_close:
            T_wave = 2 * L / a
            rows.append(dict(L_line_m=L, t_close_s=tc, wave_period_2L_over_a_s=T_wave,
                             slow_closure=tc > 5 * T_wave, dp_rhoLdvdt_Pa=rho * L * v / tc))
    return dict(v_m_s=v, a_liq_rigid_m_s=a, dp_joukowsky_rigid_bound_Pa=rho * a * v,
                note='Joukowsky applies only to closure faster than 2L/a (~3 ms); hose compliance and two-phase '
                     'content lower the wave speed and the bound further. Closure is 40-150 ms (pintle at 50 mm/s, '
                     'spring-return isolation valve <= 100 ms), so the slow-closure rows apply.', rows=rows)


def priming(P_tank_list=(45e5, 52e5, 60e5), P0=1.0e5, T0=293.15):
    """Gas trapped between the isolation valve and a seated pintle, compressed by the inrushing liquid."""
    rows = []
    for Pt in P_tank_list:
        r = dict(P_tank_Pa=Pt)
        g = 1.4
        r['T_N2_ideal_isentropic_K'] = T0 * (Pt / P0) ** ((g - 1) / g)
        s_n2 = CP.PropsSI('S', 'T', T0, 'P', P0, 'Nitrogen')
        r['T_N2_CoolProp_isentropic_K'] = CP.PropsSI('T', 'P', Pt, 'S', s_n2, 'Nitrogen')
        s_n2o = CP.PropsSI('S', 'T', T0, 'P', P0, FL)
        try:
            r['T_N2O_vapour_CoolProp_isentropic_K'] = CP.PropsSI('T', 'P', Pt, 'S', s_n2o, FL)
        except Exception as e:  # pragma: no cover
            r['T_N2O_vapour_CoolProp_isentropic_K'] = float('nan'); r['err'] = str(e)
        rows.append(r)
    return dict(rows=rows, P0_Pa=P0, T0_K=T0,
                basis='isentropic compression of the line gas (N2 after a purge, or N2O vapour) from P0 to tank '
                      'pressure: an UPPER bound on gas temperature (real fills lose heat to the wall and mix with '
                      'flashing liquid). Literature treats adiabatic compression of N2O vapour as a decomposition '
                      'initiation mechanism (e.g. Karabeyoglu et al., AIAA 2008-4933; charter N2O rules); a safe '
                      'temperature threshold is NOT established here, so the hazard is designed out instead.',
                requirement=['first start of a flight/test (P_feed < 0.5 P_tank): pintle to a bleed lift (0.10 mm) '
                             'BEFORE the isolation valve moves, so the line is vented through the injector (flow-'
                             'through, no dead end); isolation valve opening ramp >= 0.3 s',
                             'relights with the line primed (P_feed >= 0.5 P_tank, trapped liquid or valve left open): '
                             'normal sequence',
                             'trapped-liquid relief between the isolation valve and the pintle stays (mechanical.json '
                             'v1: <= 7.5 MPa)'])


def sense_line(L_list=(0.2, 0.3, 0.45, 0.6), d=1.6e-3, Vt_list=(0.1e-6, 0.3e-6, 0.5e-6), T=300.0):
    """1/8 in OD PTFE tube, 1.6 mm ID (ASSUMED common size).  Lumped line + transducer cavity (Hougen-type blend
    between the quarter-wave and Helmholtz limits); Poiseuille resistance for damping."""
    gases = dict(N2O_CO2_like=dict(R=8.314 / 0.044, g=1.30, mu=1.5e-5), N2_like=dict(R=8.314 / 0.028, g=1.40, mu=1.8e-5))
    rows = []
    A = math.pi / 4 * d ** 2
    for gname, gp in gases.items():
        c = math.sqrt(gp['g'] * gp['R'] * T)
        for P in (4.4e5, 25e5):
            rho = P / (gp['R'] * T)
            for L in L_list:
                Vl = A * L
                for Vt in Vt_list:
                    f_n = c / (2 * math.pi * L) / math.sqrt(0.5 + Vt / Vl)
                    I = rho * L / A; Rres = 128 * gp['mu'] * L / (math.pi * d ** 4); C = (Vt + Vl / 2) / (rho * c ** 2)
                    zeta = Rres / 2 * math.sqrt(C / I)
                    # phase lag at the Pc-loop frequencies of interest
                    ph = {}
                    for fr in (10.0, 20.0, 50.0):
                        x = fr / f_n
                        ph[f'phase_lag_deg_at_{int(fr)}Hz'] = math.degrees(math.atan2(2 * zeta * x, 1 - x ** 2))
                    rows.append(dict(gas=gname, c_m_s=c, P_Pa=P, L_m=L, d_m=d, V_transducer_m3=Vt,
                                     f_quarter_wave_Hz=c / (4 * L), f_n_Hz=f_n, zeta=zeta, **ph))
    return rows


def main(out):
    os.makedirs(out, exist_ok=True)
    J = dict(version='v2', date='2026-10-12', tool='feed_line_checks.py',
             inputs=dict(mdot_design_max_kg_s=(0.260, 'SIM: max over the S230 flight duty cycles incl. x0.6 regression '
                                                       '(0.241 nominal)'),
                         hose=('-6 PTFE-lined braided, 7.9 mm ID, 0.26 m free length', 'mechanical.json v1'),
                         line_loss_budget_Pa=(2.5e5, 'grain_q1d ASSUMED dp_line at 0.25 kg/s'),
                         tank_T_K=((288.15, 293.15, 298.15), 'REQ conditioning 15-25 C')))
    J['hose_and_budget'] = {f'{T - 273.15:.0f}C': hose_and_budget(0.260, T) for T in (288.15, 293.15, 298.15)}
    J['hose_and_budget_nominal_0p241'] = hose_and_budget(0.241, 293.15)
    J['surge'] = surge(0.260, 293.15)
    J['priming'] = priming()
    J['sense_line'] = sense_line()
    # budget verdict at 20 C, 0.26 kg/s, nominal viscosity, smooth hose, Cv 3 valve, Cv 2.2 filter
    h = J['hose_and_budget']['20C']
    tot = (h['hose_friction']['mu_nom_smooth_PTFE_1p5um']['dp_hose_Pa'] + h['dp_minor_Pa'] + h['dp_iso_valve_Pa']['Cv_3.0']
           + h['dp_filter_Pa']['Cv_2.2'])
    tot_v1 = (h['hose_friction']['mu_nom_smooth_PTFE_1p5um']['dp_hose_Pa'] + h['dp_minor_Pa'] + h['dp_iso_valve_Pa']['Cv_1.5']
              + h['dp_filter_Pa']['Cv_1.0'])
    J['budget_verdict'] = dict(total_dp_Cv3_valve_Cv2p2_filter_Pa=tot, total_dp_Cv1p5_valve_Cv1_filter_Pa=tot_v1,
                               budget_at_0p26_Pa=2.5e5 * (0.26 / 0.25) ** 2,
                               requirement='isolation valve Cv >= 3 (v1 said >= 1.5) and 15 um filter Cv >= 2.2 keep the '
                                           'line inside the 2.5 bar (at 0.25 kg/s) budget used by all v2 simulations; '
                                           'with Cv 1.5 + Cv 1.0 the line exceeds it and the thrust ceiling drops')
    json.dump(J, open(os.path.join(out, 'feed_line_checks_v2.json'), 'w'), indent=1, default=float)
    print(json.dumps(J['budget_verdict'], indent=1, default=float))
    print('20C hose', {k: round(v['dp_hose_Pa']) for k, v in h['hose_friction'].items()}, 'v', round(h['v_m_s'], 2),
          'minor', round(h['dp_minor_Pa']), 'valve', {k: round(v) for k, v in h['dp_iso_valve_Pa'].items()},
          'filter', {k: round(v) for k, v in h['dp_filter_Pa'].items()})
    print('surge', round(J['surge']['dp_joukowsky_rigid_bound_Pa']), [(r['L_line_m'], r['t_close_s'], round(r['dp_rhoLdvdt_Pa']))
                                                                     for r in J['surge']['rows']])
    print('priming', [{k: round(v, 1) for k, v in r.items() if isinstance(v, float)} for r in J['priming']['rows']])
    for r in J['sense_line']:
        if r['V_transducer_m3'] == 0.3e-6 and r['L_m'] in (0.3, 0.6):
            print('sense', r['gas'], r['P_Pa'], r['L_m'], round(r['f_n_Hz']), round(r['zeta'], 3),
                  round(r['phase_lag_deg_at_20Hz'], 1))


if __name__ == '__main__':
    main(sys.argv[1])
