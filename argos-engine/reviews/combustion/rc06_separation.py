"""RC-06 independent nozzle-separation check at the throttle floor, eps 2.0 (reviewer, not the author).

pe from RocketCEA (shifting and frozen-at-throat) with the reviewer's ABS card at the author's operating points
(Table 4.2: Pc, O/F at 12.5 / 15 / 20 / 25 / 100 %).  Criteria:
  Summerfield: separation when p_wall < k_S pa, k_S = 0.4 (classic; 0.25-0.4 quoted)  [LITERATURE-UNVERIFIED constants]
  Schmucker:   p_sep / pa = (1.88 M - 1)^-0.64 evaluated with the local wall Mach number [LITERATURE-UNVERIFIED form]
If separated, the area ratio at which the criterion is met is found on the isentropic (shifting) expansion.
Usage: python -I rc06_separation.py -> rc06_separation.json
"""
import json, math, os
from scipy.optimize import brentq
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
PA = 101325.0
xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
M = C * 12.011 + H * 1.008 + N * 14.007
add_new_fuel('RV6_ABS', f"fuel RV6_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={476.4 * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
CEA = CEA_Obj(oxName='N2O', fuelName='RV6_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K', isp_units='sec')
POINTS = [('100', 25.01, 10.435), ('25', 7.33, 5.32), ('20', 6.16, 4.85), ('15', 4.98, 4.34), ('12.5', 4.37, 4.06),
          ('12.5_eroded_eps1.8', 4.37 * 0.9, 4.06)]


def state(pc, of, eps, frozen):
    kw = dict(frozen=1, frozenAtThroat=1) if frozen else {}
    pcpe = CEA.get_PcOvPe(Pc=pc, MR=of, eps=eps, **kw)
    mach = CEA.get_MachNumber(Pc=pc, MR=of, eps=eps, **kw)
    return pc * 1e5 / pcpe, mach


def schmucker(m):
    return (1.88 * m - 1.0) ** (-0.64)


out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', points={})
for name, pc, of in POINTS:
    eps = 1.8 if 'eroded' in name else 2.0
    row = {}
    for fr in (False, True):
        pe, me = state(pc, of, eps, fr)
        k = 'frozen' if fr else 'shifting'
        ratio = pe / PA
        sch = schmucker(me)
        sep_sch = ratio < sch
        sep_sum = ratio < 0.4
        eps_sep = None
        if sep_sch:
            f = lambda e: state(pc, of, e, fr)[0] / PA - schmucker(state(pc, of, e, fr)[1])
            try:
                eps_sep = brentq(f, 1.2, eps, xtol=1e-3)
            except ValueError:
                eps_sep = None
        row[k] = dict(pe_over_pa=ratio, Me=me, schmucker_psep_over_pa=sch, separated_schmucker=sep_sch,
                      separated_summerfield_0p4=sep_sum, eps_sep_schmucker=eps_sep,
                      margin_to_schmucker_pct=100 * (ratio / sch - 1))
        print(f"{name:20s} {k:8s} Pc {pc:5.2f} O/F {of:5.2f} eps {eps}: pe/pa {ratio:.3f} Me {me:.3f} | Schmucker psep/pa {sch:.3f} "
              f"-> {'SEPARATED' if sep_sch else 'attached'} (margin {100*(ratio/sch-1):+.1f} %, eps_sep {eps_sep}) | Summerfield 0.4: {'SEP' if sep_sum else 'attached'}")
    out['points'][name] = row
json.dump(out, open(os.path.join(HERE, 'rc06_separation.json'), 'w'), indent=1, default=float)
