"""RC-04 independent Bartz throat heat-flux check (reviewer, not the author).

Bartz (1957) closed form, SI:
  h_g = 0.026/Dt^0.2 * (mu^0.2 cp / Pr^0.6)_0 * (Pc/c*)^0.8 * (Dt/Rc)^0.1 * (At/A)^0.9 * sigma
  sigma = [0.5 (Tw/T0)(1+(g-1)/2 M^2) + 0.5]^-(0.8-w/5) * [1+(g-1)/2 M^2]^-(w/5),  w = 0.6, M = 1 at the throat
  T_aw = T0 [1 + r (g-1)/2] / [1 + (g-1)/2],  r = Pr^(1/3);  q = h_g (T_aw - Tw)
Max-thrust point: Pc 25.01 bar, O/F 10.435, Dt 13.724 mm, Tw 600 K.
Property sets (reviewer's choices):
  P1 'author-like': RocketCEA frozen chamber transport at the ideal Tc, T0 = delivered 2757 K, c* = 0.92 c*_ideal
  P2 'delivered state': Cantera GRI-3.0 equilibrium composition at (2757 K, Pc), mixture-averaged transport
  P3 'ideal combustion': Cantera at the ideal T0 (HP equilibrium), c*_ideal -> upper bound (no eta_c* credit)
Throat radius of curvature: upstream 1.5 Rt (author), mean of up/down (1.5/0.382 Rt), downstream 0.382 Rt.
Usage: python -I rc04_bartz.py -> rc04_bartz.json
"""
import json, math, os, warnings
warnings.filterwarnings('ignore')
import cantera as ct
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
PC, OF, DT, TW = 25.01e5, 10.435, 0.013724, 600.0
RT = DT / 2
xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
M = C * 12.011 + H * 1.008 + N * 14.007
HF = 476.4
add_new_fuel('RV4_ABS', f"fuel RV4_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={HF * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
cea = CEA_Obj(oxName='N2O', fuelName='RV4_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K',
              isp_units='sec', specific_heat_units='J/kg-K', viscosity_units='millipoise', thermal_cond_units='W/cm-degC')


def bartz(mu, cp, pr, gam, T0, cstar, Rc):
    w = 0.6
    s = (0.5 * (TW / T0) * (1 + (gam - 1) / 2) + 0.5) ** (-(0.8 - w / 5)) * (1 + (gam - 1) / 2) ** (-w / 5)
    h = 0.026 / DT ** 0.2 * (mu ** 0.2 * cp / pr ** 0.6) * (PC / cstar) ** 0.8 * (DT / Rc) ** 0.1 * s
    r = pr ** (1 / 3)
    taw = T0 * (1 + r * (gam - 1) / 2) / (1 + (gam - 1) / 2)
    return h, taw, h * (taw - TW), s


def cantera_state(T=None):
    g = ct.Solution('gri30.yaml')
    g.TPX = 298.15, ct.one_atm, 'N2O:1'
    h_n2o = g.enthalpy_mass
    h_mix = (OF * h_n2o + HF * 1e3) / (1 + OF)
    n_ox = OF / (1 + OF) / 0.044013; n_fu = 1 / (1 + OF) / (M / 1000)
    nC, nH, nN, nO = n_fu * C, n_fu * H, n_fu * N + 2 * n_ox, n_ox
    x = {'CO2': nC, 'H2O': nH / 2, 'N2': nN / 2, 'O2': (nO - 2 * nC - nH / 2) / 2}
    g.TPX = 2500, PC, x
    g.HP = h_mix, PC
    g.equilibrate('HP')
    if T is not None:
        g.TP = T, PC
        g.equilibrate('TP')
    gam_fr = g.cp_mass / g.cv_mass
    return dict(T=g.T, mu=g.viscosity, k=g.thermal_conductivity, cp_fr=g.cp_mass,
                Pr=g.viscosity * g.cp_mass / g.thermal_conductivity, gamma_fr=gam_fr, MW=g.mean_molecular_weight)


def main():
    isp, cstar_id, tc = cea.get_IvacCstrTc(Pc=PC / 1e5, MR=OF, eps=2.0)
    _, g_throat = cea.get_Throat_MolWt_gamma(Pc=PC / 1e5, MR=OF, eps=2.0)
    cp_c, mu_c, k_c, pr_c = cea.get_Chamber_Transport(Pc=PC / 1e5, MR=OF, eps=2.0, frozen=1)
    cp_t, mu_t, k_t, pr_t = cea.get_Throat_Transport(Pc=PC / 1e5, MR=OF, eps=2.0, frozen=1)
    T0_del = 0.92 ** 2 * tc
    sets = {
        'P1_author_like_CEA_frozen_chamber': dict(mu=mu_c * 1e-4, cp=cp_c, Pr=pr_c, T0=T0_del, cstar=0.92 * cstar_id, gam=g_throat),
        'P1b_CEA_frozen_throat_props': dict(mu=mu_t * 1e-4, cp=cp_t, Pr=pr_t, T0=T0_del, cstar=0.92 * cstar_id, gam=g_throat),
    }
    cs_del = cantera_state(T0_del)
    sets['P2_delivered_state_cantera'] = dict(mu=cs_del['mu'], cp=cs_del['cp_fr'], Pr=cs_del['Pr'], T0=T0_del,
                                              cstar=0.92 * cstar_id, gam=g_throat)
    cs_id = cantera_state(None)
    sets['P3_ideal_combustion_cantera'] = dict(mu=cs_id['mu'], cp=cs_id['cp_fr'], Pr=cs_id['Pr'], T0=cs_id['T'],
                                               cstar=cstar_id, gam=g_throat)
    rcs = {'Rc_up_1.5Rt': 1.5 * RT, 'Rc_mean': 0.5 * (1.5 + 0.382) * RT, 'Rc_down_0.382Rt': 0.382 * RT}
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12',
               inputs=dict(Pc=PC, OF=OF, Dt=DT, Tw=TW, cstar_ideal=cstar_id, Tc_ideal=tc, gamma_throat_eq=g_throat),
               author=dict(q_MW_m2=21.92, h_g=10259, T_aw=2737), results={})
    for sn, p in sets.items():
        for rn, rc in rcs.items():
            h, taw, q, s = bartz(p['mu'], p['cp'], p['Pr'], p['gam'], p['T0'], p['cstar'], rc)
            out['results'][f'{sn}|{rn}'] = dict(props=p, Rc_m=rc, h_g=h, T_aw=taw, q_MW_m2=q / 1e6, sigma=s,
                                                d_vs_author_pct=100 * (q / 1e6 / 21.92 - 1))
            print(f"{sn:38s} {rn:16s} mu {p['mu']*1e5:.3f}e-5 cp {p['cp']:.0f} Pr {p['Pr']:.3f} T0 {p['T0']:.0f} | "
                  f"h_g {h:8.0f} T_aw {taw:6.0f} q {q/1e6:6.2f} MW/m2 ({100*(q/1e6/21.92-1):+.1f} % vs 21.92)")
    json.dump(out, open(os.path.join(HERE, 'rc04_bartz.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
