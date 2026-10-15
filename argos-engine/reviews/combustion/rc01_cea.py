"""RC-01 independent thermochemistry check (reviewer, not the author).

Recomputes c*, Tc (T0), gamma, MW, Isp_vac and Isp_SL at Pc 25 bar, eps 2.0, O/F 8.9 / 10.4 / 10.435
for the ABS design card, two ways:
  (a) NASA CEA via RocketCEA, with a fuel card written here from the stated ABS composition
      (molar A/B/S 0.24/0.185/0.575 -> C 6.06 H 6.43 N 0.24 per mol of monomer units) and the author's
      design hf (+476 kJ/kg); plus sensitivity cards (lead v0 C15H17N +62.6 kJ/mol; hf +42 kJ/kg).
  (b) Cantera 3.2 equilibrium (GRI-3.0 and NASA-9 'nasa_gas' thermo), own nozzle integration:
      HP equilibrium in the chamber; shifting (SP-equilibrium) and frozen isentropic expansion;
      throat = maximum mass flux; exit = supersonic state with A/At = 2.0.
Oxidiser: N2O gas at 298.15 K (same convention as the author's CEA card).
Outputs JSON to rc01_cea.json.  Usage: python -I rc01_cea.py
"""
import json, math, os
import numpy as np
import cantera as ct
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
G0 = 9.80665
PA = 101325.0
PC = 25.0e5
EPS = 2.0
OFS = [8.9, 10.4, 10.435]

# ---- fuel cards built by the reviewer from the stated composition ----
xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS
H = 3 * xA + 6 * xB + 8 * xS
N = xA
M = C * 12.011 + H * 1.008 + N * 14.007          # g/mol of monomer units
HF_DESIGN_KJKG = 476.4                            # author's design-card value (Table 1.1), used as given
cards = {
    'RV_ABS_TYP': (C, H, N, HF_DESIGN_KJKG * M / 1000.0),
    'RV_ABS_LEADV0': (15.0, 17.0, 1.0, 62.6),       # lead v0 card (ASSUMED in ENGINE-BASELINE)
    'RV_ABS_LOWHF': (C, H, N, 42.0 * M / 1000.0),   # low end of the author's hf spread (+42 kJ/kg)
}
for name, (c_, h_, n_, hf) in cards.items():
    add_new_fuel(name, f"fuel {name} C {c_:.5f} H {h_:.5f} N {n_:.5f} wt%=100.00 h,kj/mol={hf:.4f} t(k)=298.15 rho=1.04\n")


def cea_point(fuel, of):
    cea = CEA_Obj(oxName='N2O', fuelName=fuel, pressure_units='bar', cstar_units='m/s', temperature_units='K',
                  isp_units='sec', specific_heat_units='kJ/kg-K', viscosity_units='millipoise',
                  thermal_cond_units='W/cm-degC')
    pc = PC / 1e5
    isp_v, cstar, tc = cea.get_IvacCstrTc(Pc=pc, MR=of, eps=EPS)
    mw_c, g_c = cea.get_Chamber_MolWt_gamma(Pc=pc, MR=of, eps=EPS)
    mw_t, g_t = cea.get_Throat_MolWt_gamma(Pc=pc, MR=of, eps=EPS)
    mw_e, g_e = cea.get_exit_MolWt_gamma(Pc=pc, MR=of, eps=EPS)
    pcpe = cea.get_PcOvPe(Pc=pc, MR=of, eps=EPS)
    pe = PC / pcpe
    isp_sl = isp_v - PA * EPS * cstar / (PC * G0)
    isp_amb, mode = cea.estimate_Ambient_Isp(Pc=pc, MR=of, eps=EPS, Pamb=PA / 1e5)
    # frozen at throat
    isp_v_fr = cea.get_Isp(Pc=pc, MR=of, eps=EPS, frozen=1, frozenAtThroat=1)
    pcpe_fr = cea.get_PcOvPe(Pc=pc, MR=of, eps=EPS, frozen=1, frozenAtThroat=1)
    isp_sl_fr = isp_v_fr - PA * EPS * cstar / (PC * G0)
    mach_e = cea.get_MachNumber(Pc=pc, MR=of, eps=EPS)
    cp_c, mu_c, k_c, pr_c = cea.get_Chamber_Transport(Pc=pc, MR=of, eps=EPS, frozen=1)
    return dict(fuel=fuel, OF=of, cstar_ideal=cstar, Tc_K=tc, MW_chamber=mw_c, gamma_chamber=g_c,
                gamma_throat=g_t, gamma_exit=g_e, MW_exit=mw_e, Isp_vac_shift=isp_v, Isp_SL_shift=isp_sl,
                Isp_SL_cea_estimate=isp_amb, cea_mode=mode, pe_over_pa_shift=pe / PA, Me_shift=mach_e,
                Isp_vac_frozen_throat=isp_v_fr, Isp_SL_frozen_throat=isp_sl_fr, pe_over_pa_frozen=PC / pcpe_fr / PA,
                cp_frozen_chamber_kJkgK=cp_c, mu_chamber_Pas=mu_c * 1e-4, Pr_frozen_chamber=pr_c)


def delivered_isp_sl(p):
    """Delivered SL Isp with eta_cf applied to the vacuum Cf only (F = (eta_cf Cf_vac - eps pa/Pc) Pc At),
    and mdot = Pc At / (eta_c* c*):  Isp = eta_c* c* (eta_cf Cf_vac - eps pa/Pc) / g0."""
    cf_vac = p['Isp_vac_shift'] * G0 / p['cstar_ideal']
    a = 0.92 * p['cstar_ideal'] * (0.975 * cf_vac - EPS * PA / PC) / G0
    b = 0.92 * 0.975 * p['Isp_SL_shift']   # eta applied to Cf_SL (common simplification)
    return a, b, cf_vac


# ---------------- Cantera independent route ----------------
HF_N2O_GAS = None


NASA_SPECIES = ['N2', 'O2', 'CO2', 'CO', 'H2O', 'OH', 'H2', 'H', 'O', 'N', 'NO', 'NO2', 'N2O', 'HO2', 'H2O2', 'O3',
                'CN', 'HCN', 'HNCO', 'NCO', 'NH', 'NH2', 'NH3', 'HNO', 'HNO2', 'HNO3', 'C', 'C2', 'CH4', 'CHO', 'CH2O', 'C2H2,acetylene']


def make_gas(mech):
    if mech == 'nasa_gas.yaml':
        lib = {sp.name: sp for sp in ct.Species.list_from_file('nasa_gas.yaml')}
        sel = [lib[n] for n in NASA_SPECIES if n in lib]
        return ct.Solution(thermo='ideal-gas', species=sel)
    return ct.Solution(mech)


def cantera_point(mech, of, hf_fuel_kjkg=HF_DESIGN_KJKG, fuelCHN=(C, H, N), Mf=M):
    gas = make_gas(mech)
    # reactant enthalpy (per kg mixture) on the standard-element basis
    gas.TPX = 298.15, ct.one_atm, 'N2O:1'
    h_n2o = gas.enthalpy_mass
    h_mix = (of * h_n2o + hf_fuel_kjkg * 1e3) / (1.0 + of)
    # element moles per kg of mixture
    n_ox = of / (1 + of) / 0.044013          # mol N2O per kg
    n_fu = 1.0 / (1 + of) / (Mf / 1000.0)     # mol fuel units per kg
    nC = n_fu * fuelCHN[0]; nH = n_fu * fuelCHN[1]; nN = n_fu * fuelCHN[2] + 2 * n_ox; nO = n_ox
    # seed composition holding these elements (major products), then HP equilibrium
    x = {'CO2': nC, 'H2O': nH / 2, 'N2': nN / 2}
    o_left = nO - 2 * nC - nH / 2
    if o_left > 0:
        x['O2'] = o_left / 2
    else:
        x['CO'] = -o_left; x['CO2'] = nC + o_left
    gas.TPX = 2500.0, PC, x
    # check elements
    gas.HP = h_mix, PC
    gas.equilibrate('HP')
    T0, s0, h0 = gas.T, gas.entropy_mass, gas.enthalpy_mass
    mw_c = gas.mean_molecular_weight
    Xc = gas.X.copy()
    # equilibrium gamma (CEA definition gamma_s = -cp/cv / (dlnV/dlnP)_T ...) approximated by isentropic exponent
    def isen_exp(g):
        p1, rho1 = g.P, g.density
        s = g.entropy_mass
        g.SP = s, p1 * 0.99
        g.equilibrate('SP')
        n = math.log(0.99) / math.log(g.density / rho1)
        g.SP = s, p1
        g.equilibrate('SP')
        return n
    gam_eq = isen_exp(gas)
    gas_fr = make_gas(mech)
    gas_fr.TPX = T0, PC, Xc
    gam_fr = gas_fr.cp_mass / gas_fr.cv_mass
    out = dict(mech=mech, OF=of, T0=T0, MW_chamber=mw_c, gamma_eq_isentropic=gam_eq, gamma_frozen=gam_fr)
    for mode in ('shifting', 'frozen'):
        g = make_gas(mech)
        g.TPX = T0, PC, Xc
        ps = np.geomspace(PC * 0.95, PC * 0.002, 900)
        G, V, RHO, PP = [], [], [], []
        for p in ps:
            if mode == 'shifting':
                g.SP = s0, p
                g.equilibrate('SP')
            else:
                g.SPX = s0, p, Xc
            dh = h0 - g.enthalpy_mass
            if dh <= 0:
                continue
            v = math.sqrt(2 * dh)
            G.append(g.density * v); V.append(v); RHO.append(g.density); PP.append(p)
        G = np.array(G); V = np.array(V); RHO = np.array(RHO); PP = np.array(PP)
        it = int(np.argmax(G))
        # refine throat with a parabola
        Gt = G[it]
        cstar = PC / Gt
        # exit: supersonic branch where G = Gt/EPS
        sup = np.arange(it, len(G))
        Gs = G[sup]
        k = np.where(Gs <= Gt / EPS)[0][0]
        i1, i2 = sup[k - 1], sup[k]
        f = (Gt / EPS - G[i1]) / (G[i2] - G[i1])
        pe = PP[i1] + f * (PP[i2] - PP[i1]); ve = V[i1] + f * (V[i2] - V[i1])
        rhoe = RHO[i1] + f * (RHO[i2] - RHO[i1])
        ae_over_m = 1.0 / (rhoe * ve)
        isp_vac = (ve + pe * ae_over_m) / G0
        isp_sl = (ve + (pe - PA) * ae_over_m) / G0
        out[mode] = dict(cstar=cstar, pt_over_pc=PP[it] / PC, Isp_vac=isp_vac, Isp_SL=isp_sl, pe_over_pa=pe / PA)
    return out


def main():
    res = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12',
               card=dict(C=C, H=H, N=N, M_g_mol=M, hf_kJ_kg=HF_DESIGN_KJKG,
                         note='formula from the stated molar composition; hf = author design-card value (Table 1.1)'),
               cea={}, cantera={})
    for name in cards:
        for of in OFS:
            p = cea_point(name, of)
            a, b, cfv = delivered_isp_sl(p)
            p['delivered'] = dict(cstar=0.92 * p['cstar_ideal'], T0_eta2=0.92 ** 2 * p['Tc_K'],
                                  Isp_SL_eta_on_Cfvac=a, Isp_SL_eta_on_CfSL=b, Cf_vac_ideal=cfv)
            res['cea'][f'{name}|{of}'] = p
    for mech in ('gri30.yaml', 'nasa_gas.yaml'):
        for of in OFS:
            try:
                res['cantera'][f'{mech}|{of}'] = cantera_point(mech, of)
            except Exception as ex:   # keep failures as evidence
                res['cantera'][f'{mech}|{of}'] = dict(error=repr(ex))
    json.dump(res, open(os.path.join(HERE, 'rc01_cea.json'), 'w'), indent=1, default=float)
    # print compact table
    for k, p in res['cea'].items():
        d = p['delivered']
        print(f"CEA {k:22s} c* {p['cstar_ideal']:7.1f} Tc {p['Tc_K']:6.0f} g_c {p['gamma_chamber']:.4f} MW {p['MW_chamber']:.2f} "
              f"Ivac {p['Isp_vac_shift']:.1f} ISL {p['Isp_SL_shift']:.1f} (cea {p['Isp_SL_cea_estimate']:.1f}) pe/pa {p['pe_over_pa_shift']:.3f} "
              f"Me {p['Me_shift']:.3f} g_e {p['gamma_exit']:.4f} | fr ISL {p['Isp_SL_frozen_throat']:.1f} pe/pa_fr {p['pe_over_pa_frozen']:.3f} "
              f"| del c* {d['cstar']:.1f} T0 {d['T0_eta2']:.0f} ISL {d['Isp_SL_eta_on_Cfvac']:.1f}/{d['Isp_SL_eta_on_CfSL']:.1f}")
    for k, p in res['cantera'].items():
        if 'error' in p:
            print('CT', k, p['error']); continue
        print(f"CT  {k:22s} T0 {p['T0']:6.0f} MW {p['MW_chamber']:.2f} g_eq {p['gamma_eq_isentropic']:.4f} g_fr {p['gamma_frozen']:.4f} "
              f"| shift c* {p['shifting']['cstar']:.1f} Ivac {p['shifting']['Isp_vac']:.1f} ISL {p['shifting']['Isp_SL']:.1f} pe/pa {p['shifting']['pe_over_pa']:.3f} "
              f"| frozen c* {p['frozen']['cstar']:.1f} ISL {p['frozen']['Isp_SL']:.1f} pe/pa {p['frozen']['pe_over_pa']:.3f}")


if __name__ == '__main__':
    main()
