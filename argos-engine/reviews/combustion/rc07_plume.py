"""RC-07 independent plume-structure check (reviewer, not the author).

Correlations evaluated with (a) the CFD calibrated exhaust gas read from the author's run.json files (data, not results)
and (b) the reviewer's own RocketCEA exit state (shifting and frozen) at the v2.3 point:
  Lewis & Carlson (1964):  x_M / De = 0.69 Me sqrt(gamma pe/pa)                      [LITERATURE, form as recalled]
  Fully expanded jet: Mj from p0/pa at the same total state; Dj/De from mass conservation at the same p0, T0.
  Prandtl-Pack (Tam vortex-sheet): L_s = 1.306 beta Dj, beta = sqrt(Mj^2 - 1)           [LITERATURE-UNVERIFIED constant]
  Harper-Bourne & Fisher (1973) average cell spacing: L_s ~ 1.1 beta Dj                  [AS RECALLED, unverified]
CFD values compared: validation_v2.json (author) fine/medium/coarse and v2op.
Usage: python -I rc07_plume.py -> rc07_plume.json
"""
import json, math, os
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, '..', '..'))
PA = 101325.0
xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
M = C * 12.011 + H * 1.008 + N * 14.007
add_new_fuel('RV7_ABS', f"fuel RV7_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={476.4 * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
CEA = CEA_Obj(oxName='N2O', fuelName='RV7_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K', isp_units='sec')


def area_ratio(Mach, g):
    return (1 / Mach) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * Mach ** 2)) ** ((g + 1) / (2 * (g - 1)))


def jet(g, Me, pe):
    # total pressure from the exit state, then expand to pa
    p0 = pe * (1 + (g - 1) / 2 * Me ** 2) ** (g / (g - 1))
    Mj = math.sqrt(2 / (g - 1) * ((p0 / PA) ** ((g - 1) / g) - 1))
    DjDe = math.sqrt(area_ratio(Mj, g) / area_ratio(Me, g))
    beta = math.sqrt(Mj ** 2 - 1)
    return dict(gamma=g, Me=Me, pe_over_pa=pe / PA, x_LC_De=0.69 * Me * math.sqrt(g * pe / PA), Mj=Mj, Dj_over_De=DjDe,
                beta=beta, Ls_PP_Tam_De=1.306 * beta * DjDe, Ls_HBF_De=1.1 * beta * DjDe)


def main():
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', cases={})
    for tag, run in (('v1_point_CFD_gas', 'c_2s_100'), ('v2_point_CFD_gas', 'c_2s_100_v2op')):
        rj = json.load(open(os.path.join(HUB, '05-plume-cfd/ownruns', run, 'run.json')))
        gs = rj['gases']['1.0']
        out['cases'][tag] = jet(gs['gamma_e'], gs['Me'], gs['pe'])
    for fr in (False, True):
        kw = dict(frozen=1, frozenAtThroat=1) if fr else {}
        pc, of = 25.01, 10.435
        pe = pc * 1e5 / CEA.get_PcOvPe(Pc=pc, MR=of, eps=2.0, **kw)
        me = CEA.get_MachNumber(Pc=pc, MR=of, eps=2.0, **kw)
        _, ge = CEA.get_exit_MolWt_gamma(Pc=pc, MR=of, eps=2.0, **kw)
        out['cases'][f"v2_point_CEA_{'frozen' if fr else 'shifting'}"] = jet(ge, me, pe)
    val = json.load(open(os.path.join(HUB, '05-plume-cfd/validation/results/validation_v2.json')))
    g = val['gci']
    out['cfd'] = dict(x_md_De=dict(fine=g['x_mach_disk_De']['fine'], medium=g['x_mach_disk_De']['medium'],
                                   coarse=g['x_mach_disk_De']['coarse'], v2op_coarse=val['v2op']['x_md_cfd']),
                      spacing_first_De=dict(fine=g['spacing_first_De']['fine'], medium=g['spacing_first_De']['medium'],
                                            coarse=g['spacing_first_De']['coarse']),
                      medium_temporal_band_x_md_De=[2.58, 2.74], coarse_temporal_band_x_md_De=[2.64, 2.77])
    for k, c in out['cases'].items():
        print(f"{k:24s} g {c['gamma']:.4f} Me {c['Me']:.4f} pe/pa {c['pe_over_pa']:.3f} | x_LC {c['x_LC_De']:.3f} De | Mj {c['Mj']:.3f} "
              f"Dj/De {c['Dj_over_De']:.4f} | L_PP {c['Ls_PP_Tam_De']:.3f} L_HBF {c['Ls_HBF_De']:.3f} De")
    v1 = out['cases']['v1_point_CFD_gas']; v2 = out['cases']['v2_point_CFD_gas']
    c = out['cfd']
    out['comparison'] = dict(
        v1_fine_vs_LC_pct=100 * (c['x_md_De']['fine'] / v1['x_LC_De'] - 1),
        v1_coarse_vs_LC_pct=100 * (c['x_md_De']['coarse'] / v1['x_LC_De'] - 1),
        v2op_coarse_vs_LC_pct=100 * (c['x_md_De']['v2op_coarse'] / v2['x_LC_De'] - 1),
        v1_fine_spacing_vs_HBF_pct=100 * (c['spacing_first_De']['fine'] / v1['Ls_HBF_De'] - 1),
        v1_fine_spacing_vs_PP_pct=100 * (c['spacing_first_De']['fine'] / v1['Ls_PP_Tam_De'] - 1))
    print(json.dumps(out['comparison'], indent=1))
    json.dump(out, open(os.path.join(HERE, 'rc07_plume.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
