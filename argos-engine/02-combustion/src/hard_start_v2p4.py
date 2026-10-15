"""Hard-start inventory and vented peak-pressure bound (Combustion v2.4, closes review RC-02; feeds RC-01 and RC-13g).

Questions (REVIEW-COMBUSTION.md RC-02, lead request 2026-10-13):
  1. N2O admitted into an unlit chamber against ignition lift and abort deadline (inventory table), not only at the
     12.5 % lift: lifts for 12.5 / 15 / 20 % of 500 N at the tank state, Dyer cold flow, servo opening and closing
     travel, abort latency, tank 15 / 20 / 25 C and the A1 relight state; warm-line (vapour purge) and double-fault
     rows.
  2. Peak chamber pressure of a reacting inventory in the VENTED chamber (0-D mass + energy balance, choked throat)
     against the reaction time tau_r, for N2O decomposition (liquid basis) and N2O/ABS combustion (sensitivity);
     the constant-volume limit is cross-checked with Cantera UV equilibrium (GRI-3.0). Thresholds tau_r at which the
     peak reaches MEOP 45 bar and proof 67.5 bar.
  3. A two-component ESTIMATE of the credible case (fast vapour + suspended spray; slow wall/pool liquid limited by
     evaporation). ESTIMATE only: inputs are ASSUMED; it is not acceptance evidence.
Model notes:
  * 0-D chamber: dm/dt = mr - mo; d(m cv T)/dt = mr cp T_HP - mo cp T; P = m R T / V; mo = isentropic orifice
    (choked or not) through At with Cd_t 1.0. Products: constant R and frozen gamma at the HP equilibrium state;
    cv_eff = cp / kappa with kappa = T_UV / T_HP from Cantera, so the instantaneous limit reproduces the Cantera
    UV temperature and the slow limit the HP temperature. Initial gas 1.1 bar, 190 K.
  * Release shapes: top-hat (m0 / tau_r over tau_r) and exponential ((m0 / tau_r) exp(-t / tau_r)).
  * Every admitted gram is assumed retained (no drainage through the throat, no venting before the reaction):
    conservative, as in the review.
usage: python -I hard_start_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
import cantera as ct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import injector as INJ
import grain_q1d as Q
from tank import EquilibriumTank

FL = 'NitrousOxide'
PAMB = 101325.0
AT = math.pi / 4 * 0.013724 ** 2                  # combustion.json v2.3 throat
MEOP, PROOF = 45e5, 67.5e5                         # LEAD (ENG-09)
V_CH = {'author_284.6cm3': 284.6e-6, 'reviewer_300.9cm3': 300.9e-6}   # REPORT v2.3 Table 2.x / review RC-16
CD = 0.70                                          # ASSUMED pintle Cd (v2.3 baseline)
V_PINTLE = 0.004 / 0.24                            # HV69 at MEOP, 0.24 s full stroke (CHANGELOG 2026-10-12 pintle drive)
TAU_LAG = 0.010                                    # ASSUMED servo lag (grain_q1d)
T_CMD = 0.005 + 0.0015                             # electronics.json v1 latency: ecu_to_servo_pwm_max + servo_internal
T_VALVE_CLOSE = 0.10                               # electronics.json v1 main_valve.close_time_s (ASSUMED requirement)
TC_PURGE = {'valve_at_coil_end': 0.31, 'valve_at_zone_top': 0.48, 'v2_reference': 0.25}  # low_inlet_check_v2p3 (C7)
SEG_LIQ_G = {'valve_at_coil_end': (16.0, 21.4), 'valve_at_zone_top': (24.0, 33.0)}       # g, cm3 valve->seat (C6)


# ----------------------------------------------------------------------------------------------- N2O properties
def h_liq(T):
    return CP.PropsSI('H', 'T', T, 'Q', 0, FL)


def flash(P, h):
    """Quality and temperature of N2O at pressure P with enthalpy h (isenthalpic flash of the injected liquid)."""
    return CP.PropsSI('Q', 'P', P, 'H', h, FL), CP.PropsSI('T', 'P', P, 'H', h, FL)


def throat_flux(P0, h0, Pb=PAMB, n=80):
    """HEM isentropic mass flux through the throat from a two-phase stagnation state (P0, h0) to back pressure Pb
    (maximum along the isentrope = choking)."""
    s0 = CP.PropsSI('S', 'P', P0, 'H', h0, FL)
    best = 0.0
    for p in np.linspace(max(Pb, 0.2 * P0), P0 * 0.9999, n):
        rho = CP.PropsSI('D', 'P', p, 'S', s0, FL); h = CP.PropsSI('H', 'P', p, 'S', s0, FL)
        g = rho * math.sqrt(max(2 * (h0 - h), 0.0))
        best = max(best, g)
    return best


def cold_chamber(mdot, T1):
    """Chamber pressure of an unlit chamber fed with mdot of flashing N2O (HEM throat, Cd_t 1.0)."""
    h0 = h_liq(T1)
    lo, hi = PAMB * 1.0005, 6e5
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if AT * throat_flux(mid, h0) > mdot:
            hi = mid
        else:
            lo = mid
    P2 = 0.5 * (lo + hi)
    x, T = flash(P2, h0)
    rho_v = CP.PropsSI('D', 'P', P2, 'Q', 1, FL)
    return dict(P2_Pa=P2, quality=x, T_K=T, rho_vapour=rho_v)


# ----------------------------------------------------------------------------------------------- tank / lifts
GT = INJ.GTable()


def mdot_cold(h, P1, T1, P2):
    return CD * INJ.pintle_area(h) * GT.G(P1, T1, P2)


def lift_for_fraction(frac, tank, D_port=None):
    e = Q.Engine(tank)
    if D_port is not None:
        e.D[:] = D_port
    h, cei = e.lift_for_thrust(frac * 500.0)
    s = e.steady(h)
    return h, s


def tank_state(label):
    if label == 'A1_relight':      # Combustion A1 v2 run at the relight command (DC-A1-S230v2wip_neqE1e+03_reg1.csv, t 24.08 s)
        return EquilibriumTank(3.17e-3, 0.98 + 0.18, 286.70), 0.032213
    T = {'15C': 288.15, '20C': 293.15, '25C': 298.15}[label]
    return EquilibriumTank(3.17e-3, 2.0, T), None


def servo_history(h_ign, t_deadline, dt=2e-4, t_end=None):
    """Lift history: lift command at t=0 (seat -> h_ign at V_PINTLE behind a TAU_LAG first-order lag); abort decision at
    t_deadline (measured from the lift command); close command reaches the servo T_CMD later."""
    t_end = t_end or t_deadline + 0.2
    t = np.arange(0.0, t_end, dt); hc = 0.0; h = 0.0; H = np.empty_like(t)
    for i, ti in enumerate(t):
        target = h_ign if ti < t_deadline + T_CMD else 0.0
        hc += float(np.clip(target - hc, -V_PINTLE * dt, V_PINTLE * dt))
        h += (hc - h) * min(1.0, dt / TAU_LAG)
        H[i] = h
    return t, H


def inventory(h_ign, P1, T1, P2, t_deadline):
    t, H = servo_history(h_ign, t_deadline)
    m = np.array([mdot_cold(hh, P1, T1, P2) if hh > 1e-8 else 0.0 for hh in H])
    tr = np.trapezoid(m, t) if hasattr(np, 'trapezoid') else np.trapz(m, t)
    reach = float(t[np.argmax(H >= 0.98 * h_ign)])
    closed = t[(t > t_deadline) & (H < 0.02 * h_ign)]
    return float(tr), reach, float(closed[0] - t_deadline) if len(closed) else float('nan')


# ----------------------------------------------------------------------------------------------- products (Cantera)
def _gas():
    g = ct.Solution('gri30.yaml'); return g


def dh_liquid_basis(T):
    """Ideal-gas minus saturated-liquid enthalpy of N2O at T (CoolProp; ideal-gas limit at 1 Pa)."""
    return CP.PropsSI('H', 'T', T, 'P', 1.0, FL) - h_liq(T)


def _reactants(kind, T_tank, OF):
    g = _gas()
    g.TPX = T_tank, 45e5, 'N2O:1'
    h_n2o = g.enthalpy_mass - dh_liquid_basis(T_tank)          # liquid basis in Cantera's reference frame
    if kind == 'dec':
        return 'N2O:1', h_n2o, 1.0
    # ABS_TYP (cea_cards.py): C6.06 H6.43 N0.24 per 82.63 g, hf +476.4 kJ/kg (solid, 298 K). Elemental surrogate in
    # GRI-3.0: 3.03 C2H2 + 0.185 H2 + 0.12 N2 per ABS unit; only elements + enthalpy matter for equilibrium.
    X = {'N2O': OF * 82.63 / 44.013, 'C2H2': 3.03, 'H2': 0.185, 'N2': 0.12}
    return X, (OF * h_n2o + 476.4e3) / (1.0 + OF), 1.0 + 1.0 / OF


def _eq(X, h, P=None, v=None):
    """Equilibrium at (h, P) or (u = h, v): start from a TP equilibrium at 2500 K (elements preserved) so that the
    frozen state at the target energy has a valid temperature."""
    g = _gas()
    g.TPX = 2500.0, 45e5, X
    g.equilibrate('TP')
    if P is not None:
        g.HP = h, P; g.equilibrate('HP')
    else:
        g.UV = h, v; g.equilibrate('UV')
    return g


def products(kind, T_tank=293.15, OF=None, P_hp=45e5, rho_uv=40.0):
    """HP and UV equilibrium of the reacting mixture (liquid N2O at T_tank (+ ABS solid at 298 K for 'comb'))."""
    X, h_mix, mpk = _reactants(kind, T_tank, OF)
    g = _eq(X, h_mix, P=P_hp)
    T_hp = g.T; R = ct.gas_constant / g.mean_molecular_weight; gam = g.cp_mass / g.cv_mass
    G = math.sqrt(gam) * (2 / (gam + 1)) ** ((gam + 1) / (2 * (gam - 1)))
    cstar = math.sqrt(R * T_hp) / G
    MW = g.mean_molecular_weight
    g = _eq(X, h_mix, v=1.0 / rho_uv)          # constant-volume (instantaneous) limit: u_final = h_reactants
    return dict(kind=kind, OF=OF, T_tank_K=T_tank, T_HP_K=T_hp, R=R, MW=MW, gamma_frozen=gam, cstar_th_m_s=cstar,
                T_UV_K=g.T, kappa=g.T / T_hp, P_UV_at_rho_Pa=g.P, rho_uv=rho_uv, mass_per_kg_N2O=mpk)


def cantera_cv(kind, m_n2o, V, T_tank=293.15, OF=None):
    """Constant-volume equilibrium pressure for m_n2o (+ fuel) reacting in V (no venting, no initial gas)."""
    X, h_mix, mpk = _reactants(kind, T_tank, OF)
    g = _eq(X, h_mix, v=V / (m_n2o * mpk))
    return g.P, g.T


# ----------------------------------------------------------------------------------------------- vented 0-D model
def _rhs_factory(prod, V, A_bd=0.0, P_bd=None):
    """Outflow law; optional burst disc of area A_bd [m2] that opens (and stays open) once P exceeds P_bd."""
    R, gam, Thp, kap = prod['R'], prod['gamma_frozen'], prod['T_HP_K'], prod['kappa']
    state = {'open': False}
    cp = gam * R / (gam - 1); cv = cp / kap
    Gc = math.sqrt(gam) * (2 / (gam + 1)) ** ((gam + 1) / (2 * (gam - 1)))
    crit = (2 / (gam + 1)) ** (gam / (gam - 1))

    def outflow(m, E):
        T = E / (m * cv); P = m * R * T / V
        if P_bd is not None and P >= P_bd:
            state['open'] = True
        A = AT + (A_bd if state['open'] else 0.0)
        if P <= PAMB:
            return 0.0, T, P
        pr = PAMB / P
        if pr < crit:
            return A * P * Gc / math.sqrt(R * T), T, P
        return A * P * math.sqrt(max(2 * gam / ((gam - 1) * R * T) * (pr ** (2 / gam) - pr ** ((gam + 1) / gam)), 0.0)), T, P
    return outflow, cp, cv, Thp


def vented_peak1(m0, tau, shape, V, prod, P0=1.1e5, T0=190.0, m_fast=0.0, tau_fast=1e-3, A_bd=0.0, P_bd=None):
    """Peak chamber pressure [Pa] for one release. Release = slow part m0 over tau ('tophat' or 'exp') plus an optional
    fast top-hat part m_fast over tau_fast. Classical RK4 with a step of min(release time, vent time constant) / 60;
    the integration stops once the release is over (or < 1e-4 of its start rate) and P has fallen below 60 % of the
    running peak."""
    outflow, cp, cv, Thp = _rhs_factory(prod, V, A_bd, P_bd)
    R = prod['R']; gam = prod['gamma_frozen']
    Gc = math.sqrt(gam) * (2 / (gam + 1)) ** ((gam + 1) / (2 * (gam - 1)))
    tau_v = V * math.sqrt(R * Thp) / (R * Thp * Gc * AT)
    expo = (shape == 'exp')

    def mr(t):
        r = (m0 / tau) * math.exp(-t / tau) if expo else (m0 / tau if t < tau else 0.0)
        if m_fast > 0 and t < tau_fast:
            r += m_fast / tau_fast
        return r

    def f(t, m, E):
        mo, T, P = outflow(m, E)
        r = mr(t)
        return r - mo, r * cp * Thp - mo * cp * T

    m = P0 * V / (R * T0); E = m * cv * T0; Pk = P0; t = 0.0
    scales = [tau_v] + ([tau] if m0 > 0 else []) + ([tau_fast] if m_fast > 0 else [])
    dt = min(scales) / 60.0
    t_rel = (12.0 * tau if expo else tau) if m0 > 0 else 0.0
    t_rel = max(t_rel, tau_fast if m_fast > 0 else 0.0)
    t_max = t_rel + 20 * tau_v
    while t < t_max:
        # step refinement near the top-hat discontinuities
        h = dt
        for tb in ((tau,) if (not expo and m0 > 0) else ()) + ((tau_fast,) if m_fast > 0 else ()):
            if t < tb < t + h:
                h = tb - t
        h = max(h, 1e-9)
        k1m, k1e = f(t, m, E)
        k2m, k2e = f(t + h / 2, m + h / 2 * k1m, E + h / 2 * k1e)
        k3m, k3e = f(t + h / 2, m + h / 2 * k2m, E + h / 2 * k2e)
        k4m, k4e = f(t + h, m + h * k3m, E + h * k3e)
        m += h / 6 * (k1m + 2 * k2m + 2 * k3m + k4m); E += h / 6 * (k1e + 2 * k2e + 2 * k3e + k4e)
        t += h
        _, T, P = outflow(m, E)
        if P > Pk:
            Pk = P
        if t > t_rel and P < 0.6 * Pk:
            break
        # after the fast part and early in a long release the step may grow to tau_v/60 or tau/60
        if t > (tau_fast if m_fast > 0 else 0.0):
            dt = min(tau_v, tau if m0 > 0 else tau_v) / 60.0
    return Pk


def vented_peak(m0, tau, shape, V, prod, **kw):
    m0 = np.atleast_1d(np.asarray(m0, float)); tau = np.atleast_1d(np.asarray(tau, float))
    return np.array([vented_peak1(float(a), float(b), shape, V, prod, **kw) for a, b in zip(m0, tau)])


def tau_threshold(m0_g, P_lim, V, prod, shape, lo=1e-5, hi=1.0):
    """Reaction time below which the vented peak exceeds P_lim (bisection in log tau)."""
    m = m0_g * 1e-3 * prod['mass_per_kg_N2O']
    if vented_peak1(m, lo, shape, V, prod) < P_lim:
        return 0.0
    if vented_peak1(m, hi, shape, V, prod) > P_lim:
        return float('inf')
    a, b = math.log(lo), math.log(hi)
    for _ in range(18):
        c = 0.5 * (a + b)
        if vented_peak1(m, math.exp(c), shape, V, prod) > P_lim:
            a = c
        else:
            b = c
    return math.exp(0.5 * (a + b))


# ----------------------------------------------------------------------------------------------- main
def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/hard_start_v2p4.py',
               closes='REVIEW-COMBUSTION RC-02 (hard start), inputs to RC-01 (abort deadline) and RC-13(g) (leak ceiling)',
               inputs=dict(At_m2=AT, V_chamber_m3=V_CH, MEOP_Pa=MEOP, proof_Pa=PROOF, Cd_pintle=CD,
                           pintle_speed_m_s=V_PINTLE, servo_lag_s=TAU_LAG, abort_cmd_latency_s=T_CMD,
                           main_valve_close_s=T_VALVE_CLOSE, purge_time_s=TC_PURGE, segment_liquid_g_cm3=SEG_LIQ_G,
                           tags=dict(At='combustion.json v2.3', V_chamber='DERIVED REPORT v2.3 (284.6) / review RC-16 (300.9)',
                                     Cd='ASSUMED', pintle_speed='DERIVED HV69 0.24 s full stroke at MEOP (CHANGELOG 2026-10-12)',
                                     servo_lag='ASSUMED', abort_cmd_latency='DERIVED electronics.json v1 loop_rates_and_latency',
                                     main_valve_close='ASSUMED requirement electronics.json v1', purge='SIM low_inlet_check_v2p3 (C7)',
                                     segment='SIM low_inlet_check_v2p3 (C6)')))
    # ---- 1. cold flow and lifts
    lifts = {}; cold = {}
    for lab in ('15C', '20C', '25C', 'A1_relight'):
        tk, Dp = tank_state(lab)
        P1, T1 = tk.P, tk.T
        for fr in (0.125, 0.15, 0.20):
            h, s = lift_for_fraction(fr, tank_state(lab)[0], Dp)
            m_guess = mdot_cold(h, P1, T1, 1.3e5)
            cc = cold_chamber(m_guess, T1)
            m1 = mdot_cold(h, P1 - 2.5e5 * (m_guess / 0.25) ** 2, T1, cc['P2_Pa'])
            cc = cold_chamber(m1, T1)
            key = f'{lab}|{fr:.3f}'
            lifts[key] = dict(tank=lab, frac=fr, P_tank_Pa=P1, T_tank_K=T1, D_port_m=Dp or 0.025, lift_m=h,
                              lit_Pc_Pa=s['Pc'], lit_mox_kg_s=s['mox'], lit_F_N=s['F'])
            cold[key] = dict(mdot_cold_kg_s=m1, **cc,
                             vapour_in_chamber_g={k: 1e3 * cc['P2_Pa'] * v / (CP.PropsSI('Z', 'P', cc['P2_Pa'], 'Q', 1, FL) *
                                                  8.314462 / 0.044013 * cc['T_K']) for k, v in V_CH.items()},
                             liquid_flow_kg_s=m1 * (1 - cc['quality']))
    res['ignition_lifts'] = dict(v=lifts, tag='SIM grain_q1d v2 steady (initial port; A1 relight port 32.2 mm), lit point at the lift')
    res['cold_flow_at_ignition_lift'] = dict(v=cold, tag='DERIVED Dyer NHNE Cd 0.70 (ASSUMED) into an unlit chamber; chamber pressure from '
                                             'HEM two-phase throat flow (CoolProp), isenthalpic flash of the injected liquid')
    # ---- 2. inventory table (window from the ignition-lift command to the abort decision)
    windows = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60)
    inv = {}
    for key, L in lifts.items():
        c = cold[key]
        row = {}
        for W in windows:
            m, t_reach, t_cl = inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)
            row[f'{W:.2f}'] = dict(N2O_g=1e3 * m, t_reach_lift_s=t_reach, t_closed_after_decision_s=t_cl)
        inv[key] = row
    res['inventory_g'] = dict(v=inv, tag='DERIVED: integral of the cold flow over the servo history (lift command at 0, rate '
                              f'{V_PINTLE*1e3:.1f} mm/s behind a 10 ms lag; abort decision at the window; close command '
                              f'{T_CMD*1e3:.1f} ms later), primed liquid-full line, no ignition; single fault (the pintle closes)')
    # warm-line and double-fault rows at the A1 relight state and 20 C
    extra = {}
    for key in ('A1_relight|0.125', '20C|0.125', '20C|0.200'):
        L = lifts[key]; c = cold[key]; md = c['mdot_cold_kg_s']
        rows = {}
        for W in (0.20, 0.25, 0.30):
            m_cold, _, _ = inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'], W)
            rows[f'{W:.2f}'] = dict(
                cold_line_g=1e3 * m_cold,
                warm_line_deadline_extended_by_purge_coil_end_g=1e3 * inventory(L['lift_m'], L['P_tank_Pa'], L['T_tank_K'], c['P2_Pa'],
                                                                                W + TC_PURGE['valve_at_coil_end'])[0],
                double_fault_pintle_stuck_at_lift_valve_closes_g=[1e3 * (md * (W + T_CMD + T_VALVE_CLOSE)) + SEG_LIQ_G['valve_at_coil_end'][0],
                                                                  1e3 * (md * (W + T_CMD + T_VALVE_CLOSE)) + SEG_LIQ_G['valve_at_zone_top'][0]])
        extra[key] = rows
    res['inventory_special_cases_g'] = dict(v=extra, tag='DERIVED: warm line = the deadline extended by the C7 purge time but the line '
                                            'turns out liquid-full (worst case of a fixed extension); double fault = no light AND the pintle '
                                            'does not close: the NC valve closes in 0.10 s and the valve->seat segment (C6: 16 g at the coil '
                                            'end, 24 g at the zone top, liquid) drains into the chamber')
    # ---- 3. products and constant-volume cross-check
    prods = {'dec_15C': products('dec', 288.15), 'dec_20C': products('dec', 293.15), 'dec_25C': products('dec', 298.15)}
    for of in (4.0, 6.0, 8.0, 10.0):
        prods[f'comb_OF{of:.0f}'] = products('comb', 293.15, of)
    res['products'] = dict(v=prods, tag='DERIVED Cantera 3.2 GRI-3.0 HP/UV equilibrium; N2O on the saturated-liquid basis (CoolProp '
                           'ideal-gas minus liquid enthalpy); ABS card ABS_TYP (cea_cards.py, hf +476.4 kJ/kg) by elemental surrogate')
    cv = {}
    for mg in (2.0, 3.0, 5.0, 8.74, 12.1, 15.0, 20.0):
        for vk, V in V_CH.items():
            P, T = cantera_cv('dec', mg * 1e-3, V)
            cv[f'dec|{mg}|{vk}'] = dict(P_Pa=P, T_K=T)
            P, T = cantera_cv('comb', mg * 1e-3, V, OF=8.0)
            cv[f'comb_OF8|{mg}|{vk}'] = dict(P_Pa=P, T_K=T)
    res['constant_volume_cantera'] = dict(v=cv, tag='DERIVED Cantera UV equilibrium, reactants only (no initial gas); the review used 1 bar air')
    # ---- 4. vented peak grid and thresholds
    masses = (1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0)
    taus = (1e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2, 1e-1, 2e-1)
    grid = {}; thr = {}
    for pk_ in ('dec_20C', 'comb_OF8'):
        prod = prods[pk_]
        for vk, V in V_CH.items():
            for shape in ('tophat', 'exp'):
                M, T_ = np.meshgrid(np.array(masses) * 1e-3 * prod['mass_per_kg_N2O'], np.array(taus), indexing='ij')
                pk = vented_peak(M.ravel(), T_.ravel(), shape, V, prod).reshape(M.shape)
                grid[f'{pk_}|{vk}|{shape}'] = dict(masses_g=list(masses), tau_s=list(taus), P_peak_bar=(pk / 1e5).round(2).tolist())
                for mg in masses:
                    tm = tau_threshold(mg, MEOP, V, prod, shape)
                    tp = tau_threshold(mg, PROOF, V, prod, shape)
                    thr[f'{pk_}|{vk}|{shape}|{mg}'] = dict(tau_MEOP_s=tm, tau_proof_s=tp)
    res['vented_peak'] = dict(v=grid, tag='SIM 0-D vented chamber (this script), all admitted N2O retained and reacting with the given '
                              'shape; tau_r is unknown (no data; the review: not to be tested deliberately)')
    res['tau_thresholds'] = dict(v=thr, tag='SIM: reaction time below which the vented peak exceeds MEOP 45 bar / proof 67.5 bar '
                                 '(0 = never exceeded even instantaneously)')
    # ---- 5. two-component credible-case ESTIMATE
    est = {}
    prod = prods['dec_20C']
    for key in ('20C|0.125', '20C|0.150', '20C|0.200', 'A1_relight|0.125'):
        c = cold[key]
        for W in (0.20, 0.25, 0.30):
            m_inv = inv[key][f'{W:.2f}']['N2O_g'] * 1e-3
            for vk, V in V_CH.items():
                m_vap = c['vapour_in_chamber_g'][vk] * 1e-3
                for t_res in (0.02, 0.06):
                    m_susp = c['liquid_flow_kg_s'] * t_res
                    m_fast = min(m_vap + m_susp, m_inv)
                    m_pool = max(m_inv - m_fast, 0.0)
                    for q in (0.5e6, 2.0e6):
                        A_wet = math.pi * 0.025 * 0.230 + math.pi / 4 * 0.054 ** 2
                        h_ev = 375e3
                        tau_pool = max(m_pool * h_ev / (q * A_wet), 1e-3)
                        for tf in (1e-3, 5e-3):
                            pk = vented_peak1(m_pool, tau_pool, 'tophat', V, prod, m_fast=m_fast, tau_fast=tf)
                            est[f'{key}|W{W:.2f}|{vk}|tres{t_res}|q{q/1e6:.1f}|tf{tf*1e3:.0f}ms'] = dict(
                                inventory_g=m_inv * 1e3, m_fast_g=m_fast * 1e3, m_pool_g=m_pool * 1e3, tau_pool_s=tau_pool,
                                P_peak_bar=pk / 1e5)
    res['credible_case_estimate'] = dict(v=est, tag='ESTIMATE (ASSUMED inputs: droplet residence 20-60 ms, wall heat flux to the pooled '
                                         'liquid 0.5-2 MW/m2 over the port + head area 0.0204 m2, latent heat 375 kJ/kg, fast reaction 1-5 ms); '
                                         'decomposition products; not acceptance evidence')
    # ---- 6. fast part with combustion products (fuel vapour present) and a stand-side burst disc (T1 test article)
    fastc = {}
    pc8 = prods['comb_OF8']
    for key in ('20C|0.125', 'A1_relight|0.125', '20C|0.200'):
        c = cold[key]
        for vk, V in V_CH.items():
            m_vap = c['vapour_in_chamber_g'][vk] * 1e-3
            for t_res in (0.02, 0.06):
                m_fast = m_vap + c['liquid_flow_kg_s'] * t_res
                for tf in (1e-3, 5e-3, 1e-2):
                    pk = vented_peak1(m_fast * pc8['mass_per_kg_N2O'], tf, 'tophat', V, pc8)
                    fastc[f'{key}|{vk}|tres{t_res}|tf{tf*1e3:.0f}ms'] = dict(m_fast_N2O_g=m_fast * 1e3, P_peak_bar=pk / 1e5)
    res['fast_part_with_fuel_estimate'] = dict(v=fastc, tag='ESTIMATE: the fast part (vapour + suspended spray) reacting with fuel '
                                              'vapour at O/F 8 (fuel not limited), top-hat over 1-10 ms; slow part omitted')
    bd = {}
    prod = prods['dec_20C']
    for mg in (9.6, 12.0, 20.0):
        for d_mm in (0.0, 8.0, 12.0, 16.0, 20.0):
            for tau in (2e-3, 5e-3, 1e-2, 2e-2):
                A = math.pi / 4 * (d_mm * 1e-3) ** 2
                pk = vented_peak1(mg * 1e-3 * prod['mass_per_kg_N2O'], tau, 'tophat', V_CH['author_284.6cm3'], prod, A_bd=A,
                                  P_bd=55e5 if d_mm > 0 else None)
                bd[f'{mg}g|bd{d_mm:g}mm|tau{tau*1e3:g}ms'] = pk / 1e5
    res['burst_disc_effect_bar'] = dict(v=bd, tag='SIM: decomposition, V 284.6 cm3, top-hat; burst disc (stand-side, T1 test article) of the '
                                        'given diameter opening at 55 bar (between MEOP 45 and proof 67.5), Cd 1')
    fn = os.path.join(outdir, 'hard_start_v2p4.json')
    with open(fn, 'w') as f:
        json.dump(res, f, indent=1, default=float)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'data', 'v2'))
