"""REV-COMB-2 reviewer check: closure of the stuck-pintle MEOP rows Pc = eta_c* x c*_eq(O/F, Pc) x mdot_ox (1 + 1/OF) / At
with an independent equilibrium c* (RocketCEA; reviewer cards: ABS C6.06 H6.43 N0.24, hf +476.4 kJ/kg as the project's ABS_TYP;
N2O liquid at 25 C from Cantera hf minus the CoolProp ideal-gas-to-liquid enthalpy).  Also the eta_cf cap arithmetic (OI-28).
usage: python -I r2_meop_cstar.py OUT_JSON
"""
import json, math, sys
from rocketcea.cea_obj import CEA_Obj, add_new_fuel, add_new_oxidizer
import cantera as ct
import CoolProp.CoolProp as CP
out = sys.argv[1]
gas = ct.Solution('gri30.yaml'); gas.TPX = 298.15, 1e5, 'N2O:1'
hf_gas = gas.enthalpy_mole / 1e6          # kJ/mol
d = (CP.PropsSI('H', 'T', 298.15, 'P', 5.0, 'N2O') - CP.PropsSI('H', 'T', 298.15, 'Q', 0, 'N2O')) * 44.0128e-3 / 1e3
add_new_oxidizer('N2Or2', f"oxid N2Or2  N 2 O 1  wt%=100.00\nh,kj/mol={hf_gas - d:.3f}  t(k)=298.15\n")
add_new_fuel('ABSr2', f"fuel ABSr2  C 6.06 H 6.43 N 0.24  wt%=100.00\nh,kj/mol={476.4 * 0.08263:.3f}  t(k)=298.15\n")
C = CEA_Obj(oxName='N2Or2', fuelName='ABSr2')
AT = math.pi / 4 * 0.013724 ** 2
rows = [('hardware_Cv3_25C_a1.5_n0.68', 45.01, 0.3859, 7.40), ('zero_25C_a1.5_n0.68', 46.27, 0.3974, 7.47),
        ('hardware_Cv3_25C_a1.5_n0.5', 44.26, 0.3942, 8.89), ('zero_25C_a1.0_n0.5', 43.96, 0.4289, 13.92)]
res = dict(hf_N2O_liq_kJ_mol=hf_gas - d, rows=[])
for lab, pc, mox, of in rows:
    psia = pc * 14.5038
    cs = C.get_Cstar(Pc=psia, MR=of) * 0.3048       # ft/s -> m/s
    pc_chk = 0.96 * cs * mox * (1 + 1 / of) / AT / 1e5
    res['rows'].append(dict(row=lab, author_Pc_bar=pc, mox=mox, OF=of, cstar_eq_m_s=cs, Pc_reviewer_bar=pc_chk, diff_pct=100 * (pc_chk / pc - 1)))
# OI-28 arithmetic: Pc for 500 N at eta_cf 0.95 if 25.01 bar gives 499.8 N at 0.975 (Pc ~ 1/eta_cf, Cf(Pc) ignored)
res['OI28'] = dict(Pc_needed_bar=25.01 * 0.975 / 0.95, F_at_25bar_low_end_N=499.8 * 0.95 / 0.975)
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps(res, indent=1))
