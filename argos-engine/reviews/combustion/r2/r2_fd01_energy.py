"""REV-COMB-2 reviewer checks (independent implementation; the author's code is not imported).

(1) FD-01 leg deficit: 0.707 mm restrictor (Cd 0.70 ASSUMED -> Cd.A 0.2748 mm2) behind Mechanical's inline element
    (Cd.A 1.57 mm2), coast state saturated at 289.5 K, discharge to 1.0 bar.  Readings: (a) incompressible series;
    (b) metastable liquid through the element, Dyer restrictor at the reduced inlet pressure; (c) equilibrium flashing in
    the element (isenthalpic), restrictor inlet two-phase: Dyer kappa = 1 with SPI on the homogeneous inlet density and HEM
    from the two-phase inlet; (d) saturated vapour, choked restrictor (HEM = isentropic vapour) with the element dP on the
    vapour density.  Element modelled as an orifice of the stated Cd.A (a sintered/mesh element is not an orifice: its dP law
    is closer to linear-in-flow (Darcy) plus inertial; the orifice reading is the reviewer's choice, ASSUMED).
(2) Decomposition energy per kg (Cantera GRI-3.0 formation enthalpies + CoolProp phase change) and isentropic expansion
    energy of the tank contents (CoolProp HEOS, expansion to 1 atm at constant entropy, work = m (u1 - u2s)).
usage: python -I r2_fd01_energy.py OUT_JSON
"""
import json, math, sys
import numpy as np
import cantera as ct
import CoolProp.CoolProp as CP

OUT = sys.argv[1]
AS = CP.AbstractState('HEOS', 'NitrousOxide')
T0 = 289.5; P2 = 1.0e5
A_R = 0.70 * math.pi / 4 * 0.707e-3 ** 2
A_E = 1.57e-6
res = {}


def ph(p, h):
    AS.update(CP.HmassP_INPUTS, float(h), float(p)); return AS.rhomass(), AS.smass(), AS.Q()


def hem(p1, h1, p2=P2, n=160):
    _, s1, _ = ph(p1, h1); best = 0.0
    for p in np.linspace(max(p2, 1.5e5), p1 * 0.99995, n):
        AS.update(CP.PSmass_INPUTS, float(p), float(s1))
        dh = h1 - AS.hmass()
        if dh > 0:
            best = max(best, AS.rhomass() * math.sqrt(2 * dh))
    return best


AS.update(CP.QT_INPUTS, 0.0, T0); Pv = AS.p(); hl = AS.hmass(); rl = AS.rhomass()
AS.update(CP.QT_INPUTS, 1.0, T0); hg = AS.hmass(); rg = AS.rhomass()
res['coast_state'] = dict(T_K=T0, Psat_bar=Pv / 1e5, rho_l=rl, rho_g=rg)


def dyer(p1, pv, rho_spi, h1):
    k = math.sqrt(max(p1 - P2, 0) / max(pv - P2, 1e-9))
    g_spi = math.sqrt(2 * rho_spi * max(p1 - P2, 0)); g_hem = hem(p1, h1)
    return (k / (1 + k)) * g_spi + (1 / (1 + k)) * g_hem


G0 = dyer(Pv, Pv, rl, hl); m0 = A_R * G0
res['liquid_no_element'] = dict(G_kg_m2s=G0, mdot_g_s=1e3 * m0)
# (a) incompressible series
aeff = 1 / math.sqrt(1 / A_R ** 2 + 1 / A_E ** 2)
res['a_incompressible_deficit_pct'] = 100 * (1 - aeff / A_R)


# (b) metastable liquid through the element (rho_l), restrictor Dyer at p_mid with Pv unchanged (kappa < 1)
def solve(fun_mdot_restrictor, dp_element):
    lo, hi = 0.0, 3.0 * m0
    for _ in range(60):
        m = 0.5 * (lo + hi)
        pm = Pv - dp_element(m)
        if fun_mdot_restrictor(pm) > m:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


mb = solve(lambda pm: A_R * dyer(pm, Pv, rl, hl), lambda m: (m / A_E) ** 2 / (2 * rl))
res['b_metastable_deficit_pct'] = 100 * (1 - mb / m0)


# (c) equilibrium flashing in the element: isenthalpic to p_mid, homogeneous density; restrictor Dyer kappa 1, SPI on rho_h
def restr_c(pm):
    r_h, _, _ = ph(pm, hl)
    return A_R * (0.5 * math.sqrt(2 * r_h * (pm - P2)) + 0.5 * hem(pm, hl))


def dp_c(m):
    # element dP on the outlet homogeneous density: fixed-point
    dp = (m / A_E) ** 2 / (2 * rl)
    for _ in range(20):
        r_h, _, _ = ph(Pv - dp, hl)
        dp = (m / A_E) ** 2 / (2 * r_h)
    return dp


mc = solve(restr_c, dp_c)
pm_c = Pv - dp_c(mc)
res['c_flashing_deficit_pct'] = 100 * (1 - mc / m0)
res['c_flashing_restrictor_inlet'] = dict(p_mid_bar=pm_c / 1e5, quality=ph(pm_c, hl)[2])
# reference for (c): the same two-phase restrictor law with no element (p_mid = Pv): Dyer kappa 1 at saturated liquid
res['c_reference_same_law_no_element_g_s'] = 1e3 * restr_c(Pv * 0.999999)
res['c_flashing_deficit_vs_same_law_pct'] = 100 * (1 - mc / restr_c(Pv * 0.999999))
# (d) saturated vapour: choked isentropic restrictor flux proportional to inlet pressure; element dP on vapour density
gv = hem(Pv, hg); mv0 = A_R * gv


def restr_d(pm):
    return A_R * hem(pm, hg)          # element isenthalpic: restrictor inlet at (pm, h_g)


md = solve(restr_d, lambda m: (m / A_E) ** 2 / (2 * rg))
res['d_vapour'] = dict(mdot_no_element_g_s=1e3 * mv0, deficit_pct=100 * (1 - md / mv0))

# (2) decomposition energy and expansion energy
gas = ct.Solution('gri30.yaml')
gas.TPX = 298.15, 1e5, 'N2O:1'; h_r = gas.enthalpy_mass
gas.TPX = 298.15, 1e5, 'N2:1, O2:0.5'; h_p = gas.enthalpy_mass
dH_gas = h_r - h_p
out = dict(dH_dec_gas_298K_MJ_kg=dH_gas / 1e6)
for Tc in (15, 20, 25, 35):
    T = Tc + 273.15
    AS.update(CP.QT_INPUTS, 0.0, T); hl_ = AS.hmass()
    AS.update(CP.QT_INPUTS, 1.0, T); hg_ = AS.hmass()
    # gas at T relative to gas at 298 on the ideal-gas reference ~ the same within cp*dT; liquid basis subtracts h_fg(T) plus the
    # departure; here dH_liq(T) = dH_gas(298) - [h_ig(298) - h_liq(T)] using CoolProp near-ideal gas at 298 K, 5 Pa
    h_ig298 = CP.PropsSI('H', 'T', 298.15, 'P', 5.0, 'N2O')
    out[f'dH_dec_liquid_{Tc}C_MJ_kg'] = (dH_gas - (h_ig298 - hl_)) / 1e6
    out[f'h_fg_{Tc}C_kJ_kg'] = (hg_ - hl_) / 1e3
res['decomposition_energy'] = out


def expansion(m, V, T):
    rho = m / V
    AS.update(CP.DmassT_INPUTS, rho, T); u1 = AS.umass(); s1 = AS.smass(); p1 = AS.p(); q1 = AS.Q()
    AS.update(CP.PSmass_INPUTS, 101325.0, s1); u2 = AS.umass(); q2 = AS.Q()
    W = m * (u1 - u2)
    return dict(m_kg=m, V_L=V * 1e3, T_K=T, P1_bar=p1 / 1e5, Q1=q1, Q2_isentropic=q2, W_kJ=W / 1e3, TNT_kg=W / 4.184e6,
                R_6p9kPa_m=17.9 * (W / 4.184e6) ** (1 / 3))


res['expansion'] = dict(flight_20C=expansion(2.00, 3.17e-3, 293.15), flight_35C=expansion(2.00, 3.17e-3, 308.15),
                        A1_residual_20C=expansion(0.61, 3.17e-3, 293.15), A1_residual_50C=expansion(0.61, 3.17e-3, 323.15))
# decomposition TNT check for the flight tank (liquid + vapour split at 20 C)
AS.update(CP.DmassT_INPUTS, 2.00 / 3.17e-3, 293.15); q = AS.Q()
E = 2.00 * ((1 - q) * out['dH_dec_liquid_20C_MJ_kg'] + q * (dH_gas / 1e6)) * 1e6
res['decomposition_flight_20C'] = dict(vapour_mass_fraction=q, E_MJ=E / 1e6, TNT_kg=E / 4.184e6, R_6p9kPa_m=17.9 * (E / 4.184e6) ** (1 / 3))
# (3) capillary barrier of a wetted 15 um element against the purge pressure difference (bubble point 4 sigma / d, theta 0)
try:
    sig = CP.PropsSI('I', 'T', T0, 'Q', 0, 'NitrousOxide')
except Exception as e:           # surface tension not available in this CoolProp build
    sig = None
res['capillary_barrier'] = dict(sigma_N_m=sig, pore_m=15e-6, bubble_point_Pa=(4 * sig / 15e-6) if sig else None,
                                purge_dp_Pa=Pv - P2, ratio=((4 * sig / 15e-6) / (Pv - P2)) if sig else None)
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps(res, indent=1))
