"""RC-02 independent throat / exit sizing (reviewer, not the author).

500 N at sea level, Pc 25.0 bar, eps 2.0, eta_c* 0.92, eta_cf 0.975 (both ASSUMED by the author).
Thrust model: F = (eta_cf * Cf_vac - eps * pa / Pc) * Pc * At   (losses on the vacuum term), and the
common alternative F = eta_cf * Cf_SL * Pc * At.  Cf_vac, c* from RocketCEA (shifting) with the reviewer's
ABS card (rc01_cea.py).  Usage: python -I rc02_sizing.py  -> rc02_sizing.json
"""
import json, math, os
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
G0, PA, EPS, F = 9.80665, 101325.0, 2.0, 500.0
xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
M = C * 12.011 + H * 1.008 + N * 14.007
add_new_fuel('RV2_ABS', f"fuel RV2_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={476.4 * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
cea = CEA_Obj(oxName='N2O', fuelName='RV2_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K', isp_units='sec')

AUTHOR = dict(Dt_mm=13.724, De_mm=19.409, mdot_kg_s=0.26408, Pc_bar=25.01)
out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', cases=[])
for of, pc in [(10.4, 25.0), (10.435, 25.0), (10.435, 25.01), (7.76, 24.99), (8.9, 25.0)]:
    isp_v, cstar, tc = cea.get_IvacCstrTc(Pc=pc, MR=of, eps=EPS)
    cf_vac = isp_v * G0 / cstar
    Pc = pc * 1e5
    cf_del_a = 0.975 * cf_vac - EPS * PA / Pc
    cf_del_b = 0.975 * (cf_vac - EPS * PA / Pc)
    res = dict(OF=of, Pc_bar=pc, cstar_ideal=cstar, Cf_vac_ideal=cf_vac, Cf_SL_ideal=cf_vac - EPS * PA / Pc)
    for tag, cf in (('eta_on_Cfvac', cf_del_a), ('eta_on_CfSL', cf_del_b)):
        At = F / (cf * Pc)
        Dt = math.sqrt(4 * At / math.pi)
        De = Dt * math.sqrt(EPS)
        mdot = Pc * At / (0.92 * cstar)
        res[tag] = dict(Cf_delivered=cf, At_m2=At, Dt_mm=Dt * 1e3, De_mm=De * 1e3, mdot_kg_s=mdot,
                        Isp_SL_s=F / (mdot * G0),
                        dDt_vs_author_pct=100 * (Dt * 1e3 / AUTHOR['Dt_mm'] - 1),
                        dDe_vs_author_pct=100 * (De * 1e3 / AUTHOR['De_mm'] - 1),
                        dmdot_vs_author_pct=100 * (mdot / AUTHOR['mdot_kg_s'] - 1))
    # Pc needed with the author's fixed throat for 500 N
    At_a = math.pi / 4 * (AUTHOR['Dt_mm'] * 1e-3) ** 2
    res['Pc_for_500N_with_author_throat_bar'] = (F / At_a + EPS * PA) / (0.975 * cf_vac) / 1e5
    out['cases'].append(res)
    a = res['eta_on_Cfvac']; b = res['eta_on_CfSL']
    print(f"O/F {of:6.3f} Pc {pc:5.2f}: Cf_vac {cf_vac:.4f} | Dt {a['Dt_mm']:.3f} mm ({a['dDt_vs_author_pct']:+.2f} %), De {a['De_mm']:.3f} mm "
          f"({a['dDe_vs_author_pct']:+.2f} %), mdot {a['mdot_kg_s']:.4f} ({a['dmdot_vs_author_pct']:+.2f} %), Isp {a['Isp_SL_s']:.1f} | "
          f"alt Dt {b['Dt_mm']:.3f} | Pc(author throat) {res['Pc_for_500N_with_author_throat_bar']:.2f} bar")
json.dump(out, open(os.path.join(HERE, 'rc02_sizing.json'), 'w'), indent=1)
