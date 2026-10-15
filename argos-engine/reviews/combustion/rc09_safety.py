"""RC-09 N2O safety numbers (reviewer, not the author).  Small checks only; every input is tagged in the output.

(a) Table 2.7 check: isentropic compression of a gas pocket from 1.0 bar, 293.15 K to 45 / 52 / 60 bar (author's levels)
    and to 63.1 bar (Psat at 30 C) and 70 bar (tank MEOP): N2 ideal (gamma 1.4), N2 and N2O vapour with CoolProp.
(b) Hard start: inventory admitted at the ignition lift (reviewer's rc03 cold flows), flash quality into 1.0-1.5 bar,
    constant-volume decomposition bound of the retained N2O in the chamber free volume (Cantera GRI-3.0 thermo, UV
    equilibrium with 1 bar air), and the gas vent time constant of the chamber through the throat.
(c) Stored decomposition energy and TNT equivalent (4.184 MJ/kg) of the flight load, the A1 post-landing residual and the
    author's ASSUMED 15 L ground tank.  1 psi (6.9 kPa) overpressure distance R = 17.9 m W^(1/3) [AS RECALLED,
    hemispherical surface burst scaled distance ~45 ft/lb^(1/3); order of magnitude only, not a safety distance].
(d) Trapped liquid: isochoric (dP/dT)_rho of liquid N2O, temperature rise to 7.5 MPa, supercritical pressure along the
    isochore, and the mass fraction a 7.5 MPa relief must expel at 40-150 C (soak-back band in REPORT §6).
(e) Residual tank after an A1 landing: P(T) at the residual mean density.
Usage: python -I rc09_safety.py -> rc09_safety.json
"""
import json, math, os, warnings
warnings.filterwarnings('ignore')
import CoolProp.CoolProp as CP
import cantera as ct
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
FL = 'NitrousOxide'
TNT = 4.184e6


def comp(fluid, P1, T1, P2):
    s = CP.PropsSI('S', 'P', P1, 'T', T1, fluid)
    return CP.PropsSI('T', 'P', P2, 'S', s, fluid)


def main():
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12')
    # (a)
    a = {}
    for pb in (45.0, 52.0, 60.0, 63.1, 70.0):
        P2 = pb * 1e5
        a[str(pb)] = dict(N2_ideal_K=293.15 * (P2 / 1e5) ** (0.4 / 1.4), N2_CoolProp_K=comp('Nitrogen', 1e5, 293.15, P2),
                          N2O_vap_CoolProp_K=comp(FL, 1e5, 293.15, P2))
        r = a[str(pb)]
        print(f"(a) {pb:5.1f} bar: N2 ideal {r['N2_ideal_K']:.0f} K, N2 CP {r['N2_CoolProp_K']:.0f} K, N2O vap {r['N2O_vap_CoolProp_K']:.0f} K")
    a['author_table_2_7'] = {'45': [870, 847, 614], '52': [907, 879, 630], '60': [944, 913, 646]}
    out['adiabatic_compression'] = a
    # (b)
    inj = json.load(open(os.path.join(HERE, 'rc03_injector.json')))
    cold = inj['cold_ignition_lift']
    h1 = CP.PropsSI('H', 'T', 293.15, 'Q', 0, FL)
    flash = {}
    for pb in (1.0, 1.5):
        hl = CP.PropsSI('H', 'P', pb * 1e5, 'Q', 0, FL); hv = CP.PropsSI('H', 'P', pb * 1e5, 'Q', 1, FL)
        flash[str(pb)] = dict(quality=(h1 - hl) / (hv - hl), T_K=CP.PropsSI('T', 'P', pb * 1e5, 'Q', 0, FL),
                              h_fg_kJ_kg=(hv - hl) / 1e3)
    # Cantera: N2O ideal-gas reference; liquid-state energy = gas(293.15) - [h_gas_CP(293.15, 1 kPa) - h_state_CP]
    hg_cp = CP.PropsSI('H', 'T', 293.15, 'P', 1e3, FL)
    g = ct.Solution('gri30.yaml')
    g.TPY = 293.15, 1e3, 'N2O:1'
    u_g_ct, h_g_ct = g.int_energy_mass, g.enthalpy_mass
    g.TPX = 298.15, 1e5, 'N2O:1'; h298 = g.enthalpy_mass
    g.TPX = 298.15, 1e5, 'N2:1,O2:0.5'; hp298 = g.enthalpy_mass
    dh_dec_gas = h298 - hp298
    ug_cp = CP.PropsSI('U', 'T', 293.15, 'P', 1e3, FL)
    states = {'gas_293K': u_g_ct,
              'sat_liquid_293K': u_g_ct - (ug_cp - CP.PropsSI('U', 'T', 293.15, 'Q', 0, FL)),
              'liquid_after_flash_1p5bar': u_g_ct - (ug_cp - CP.PropsSI('U', 'P', 1.5e5, 'Q', 0, FL))}
    hs = {}
    vt = {}
    for V_lab, V in (('author_284.6cm3', 284.6e-6), ('reviewer_300.9cm3', 300.9e-6)):
        for m_lab, m in (('8.74g_author_12.5pct', 8.74e-3), ('12.1g_reviewer_20pct', cold['20pct']['admitted_0p23s_g'] * 1e-3),
                         ('15g_20pct_plus_close', 15e-3)):
            for s_lab, u_n2o in states.items():
                air = ct.Solution('gri30.yaml'); air.TPX = 293.15, 1e5, 'O2:0.21,N2:0.79'
                m_air = air.density * V
                u_mix = (m * u_n2o + m_air * air.int_energy_mass) / (m + m_air)
                # same elements, written as N2O -> N2 + 1/2 O2 so a frozen start state with the target U exists
                fN2 = 28.0134 / 44.0128
                Y = {'N2': (fN2 * m + 0.767 * m_air) / (m + m_air), 'O2': ((1 - fN2) * m + 0.233 * m_air) / (m + m_air)}
                gg = ct.Solution('gri30.yaml')
                rho_mix = (m + m_air) / V

                def fu(T):
                    gg.TDY = T, rho_mix, Y
                    return gg.int_energy_mass - u_mix
                brentq(fu, 200.0, 6000.0)         # frozen product-composition state with the target U and V
                gg.equilibrate('UV')
                hs[f'{V_lab}|{m_lab}|{s_lab}'] = dict(T_K=gg.T, P_bar=gg.P / 1e5)
        # vent time constant for hot decomposition products, gamma ~1.3, choked through At
        At = math.pi / 4 * 0.013724 ** 2
        for T in (1500.0, 2000.0):
            gam, Rg = 1.3, 8314.46 / 29.34
            Gam = math.sqrt(gam) * (2 / (gam + 1)) ** ((gam + 1) / (2 * (gam - 1)))
            vt[f'{V_lab}|T{int(T)}'] = V / (Gam * At * math.sqrt(Rg * T))
    for k, v in hs.items():
        print(f"(b) {k:58s} T {v['T_K']:.0f} K  P {v['P_bar']:.0f} bar")
    for k, v in vt.items():
        print(f"(b) vent time constant {k}: {v*1e3:.2f} ms")
    out['hard_start'] = dict(cold_inventory=cold, flash=flash, cv_decomposition_bound=hs, vent_tau_s=vt,
                             author_inventory_g=8.74, MEOP_bar=45.0, proof_bar=67.5,
                             evaporation_energy_kJ_12g_at_1atm=12.1e-3 * CP.PropsSI('H', 'P', 101325, 'Q', 1, FL) / 1e3
                             - 12.1e-3 * CP.PropsSI('H', 'P', 101325, 'Q', 0, FL) / 1e3)
    print('(b) flash', flash)
    # (c)
    dh_liq = dh_dec_gas - (hg_cp - h1)
    rhoL = CP.PropsSI('D', 'T', 293.15, 'Q', 0, FL); rhoV = CP.PropsSI('D', 'T', 293.15, 'Q', 1, FL)
    m15 = 0.015 * (0.85 * rhoL + 0.15 * rhoV)
    masses = {'flight_load_2.00kg': 2.00, 'A1_residual_after_landing_nominal': 2.00 - 1.738 / 1.25,
              'ground_tank_15L_ASSUMED_85pct_20C': m15}
    te = {}
    for k, m in masses.items():
        E = [m * dh_liq, m * dh_dec_gas]
        W = [e / TNT for e in E]
        te[k] = dict(mass_kg=m, energy_MJ=[e / 1e6 for e in E], TNT_kg=W, R_1psi_m=[17.9 * w ** (1 / 3) for w in W])
        print(f"(c) {k:40s} m {m:.2f} kg  E {E[0]/1e6:.2f}-{E[1]/1e6:.2f} MJ  TNT {W[0]:.2f}-{W[1]:.2f} kg  R(1 psi) {17.9*W[0]**(1/3):.0f}-{17.9*W[1]**(1/3):.0f} m")
    out['stored_energy'] = dict(dh_dec_gas_MJ_kg=dh_dec_gas / 1e6, dh_dec_sat_liquid_293K_MJ_kg=dh_liq / 1e6, cases=te)
    # (d)
    tl = {}
    for TC in (15.0, 20.0, 25.0):
        T = 273.15 + TC
        rho = CP.PropsSI('D', 'T', T, 'Q', 0, FL) * 1.0005
        dpdt = (CP.PropsSI('P', 'T', T + 0.05, 'D', rho, FL) - CP.PropsSI('P', 'T', T - 0.05, 'D', rho, FL)) / 0.1
        T75 = brentq(lambda x: CP.PropsSI('P', 'T', x, 'D', rho, FL) - 7.5e6, T, T + 30)
        sup = {}
        for TT in (40.0, 60.0, 90.0, 150.0):
            P_iso = CP.PropsSI('P', 'T', 273.15 + TT, 'D', rho, FL)
            rho75 = CP.PropsSI('D', 'T', 273.15 + TT, 'P', 7.5e6, FL)
            sup[str(TT)] = dict(P_isochore_MPa=P_iso / 1e6, rho_at_7p5MPa=rho75, mass_fraction_expelled=1 - rho75 / rho)
        tl[str(TC)] = dict(rho=rho, Psat_MPa=CP.PropsSI('P', 'T', T, 'Q', 0, FL) / 1e6, dPdT_MPa_K=dpdt / 1e6,
                           dT_to_7p5MPa_K=T75 - T, supercritical=sup)
        print(f"(d) liquid-full from {TC:.0f} C: rho {rho:.0f}, dP/dT|rho {dpdt/1e6:.2f} MPa/K, reaches 7.5 MPa after +{T75-T:.2f} K; "
              + ', '.join(f"{k} C: {v['P_isochore_MPa']:.0f} MPa (relief expels {100*v['mass_fraction_expelled']:.0f} %)" for k, v in sup.items()))
    out['trapped_liquid'] = dict(cases=tl, Tcrit_K=CP.PropsSI('Tcrit', FL), Pcrit_MPa=CP.PropsSI('pcrit', FL) / 1e6)
    # (e)
    m_res = masses['A1_residual_after_landing_nominal']
    rho_res = m_res / 3.17e-3
    rt = {}
    for TC in (20.0, 30.0, 35.0, 40.0, 50.0, 60.0):
        rt[str(TC)] = CP.PropsSI('P', 'T', 273.15 + TC, 'D', rho_res, FL) / 1e6
    out['residual_tank'] = dict(mass_kg=m_res, rho_mean=rho_res, P_MPa_vs_T_C=rt, note='mass DERIVED from REQUIREMENTS rev 2 table: 2.00 - 1.738/1.25')
    print('(e) residual tank', round(m_res, 3), 'kg, rho', round(rho_res, 1), {k: round(v, 2) for k, v in rt.items()})
    json.dump(out, open(os.path.join(HERE, 'rc09_safety.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
