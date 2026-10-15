"""RC-10 independent re-evaluation of the CFD grid study and of the nozzle-efficiency evidence (reviewer, not the author).

(1) GCI per Celik et al., J. Fluids Eng. 130 (2008) 078001 / Roache, constant refinement ratio r = 2 (cells 20,008 /
    80,032 / 320,128 in 2-D): e21 = f2 - f1, e32 = f3 - f2 (1 = fine), convergence ratio R = e21/e32;
    0 < R < 1 monotone convergence, R > 1 monotone divergence, R < 0 oscillatory.  p = ln|e32/e21| / ln r,
    f_ext = (r^p f1 - f2)/(r^p - 1), GCI_fine = 1.25 |e21/f1| / (r^p - 1).  GCI is defined only for 0 < R < 1.
    Inputs: the author's three-level values in validation_v2.json (data); the fine level started from the medium state
    at 3.0 ms and ran 0.25 ms (run.json files).
(2) Implied nozzle thrust efficiency: CFD thrust at fixed Pc against the 1-D ideal at the same Pc/gas (validation_v2.json),
    own inviscid (slip wall) vs OpenFOAM inviscid (slip) and OpenFOAM SST (no-slip nozzle wall, coarse, 1.15 ms).
    Then the Pc needed for 500 N at the v2.3 point for eta_cf 0.95 / 0.96 / 0.975 with the reviewer's RocketCEA Cf_vac.
Usage: python -I rc10_gci.py -> rc10_gci.json
"""
import json, math, os
from scipy.optimize import brentq
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, '..', '..'))
R = 2.0


def gci(f1, f2, f3):
    e21, e32 = f2 - f1, f3 - f2
    out = dict(fine=f1, medium=f2, coarse=f3, e21=e21, e32=e32)
    if e32 == 0 or e21 == 0:
        out.update(R=None, regime='degenerate (identical levels)', p=None, f_ext=None, gci_fine_pct=None)
        return out
    Rr = e21 / e32
    out['R'] = Rr
    p = math.log(abs(e32 / e21)) / math.log(R)
    out['p'] = p
    if 0 < Rr < 1:
        fext = (R ** p * f1 - f2) / (R ** p - 1)
        out.update(regime='monotone convergence', f_ext=fext, gci_fine_pct=100 * 1.25 * abs(e21 / f1) / (R ** p - 1))
    elif Rr >= 1:
        out.update(regime='monotone DIVERGENCE: GCI not applicable', f_ext=None, gci_fine_pct=None,
                   max_level_spread_pct=100 * (max(f1, f2, f3) - min(f1, f2, f3)) / f1)
    else:
        out.update(regime='oscillatory: GCI not applicable', f_ext=None, gci_fine_pct=None,
                   max_level_spread_pct=100 * (max(f1, f2, f3) - min(f1, f2, f3)) / f1)
    return out


def main():
    val = json.load(open(os.path.join(HUB, '05-plume-cfd/validation/results/validation_v2.json')))
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', gci={})
    for k, v in val['gci'].items():
        if not isinstance(v, dict) or 'fine' not in v:
            continue
        try:
            r = gci(float(v['fine']), float(v['medium']), float(v['coarse']))
        except (TypeError, ValueError):
            continue
        r['author'] = dict(p=v.get('p'), gci_fine_pct=v.get('gci_fine_pct'), note=v.get('note'))
        out['gci'][k] = r
        print(f"{k:28s} f {r['fine']:.6g}/{r['medium']:.6g}/{r['coarse']:.6g}  R {r['R'] if r['R'] is None else round(r['R'],3)}  "
              f"p {None if r['p'] is None else round(r['p'],2)}  {r['regime']}  GCI {r.get('gci_fine_pct')}  | author p {v.get('p')} GCI {v.get('gci_fine_pct')}")
    # (2) efficiency evidence
    od = val['one_d']
    rows = {'own_fine_slip': 500.8162, 'own_coarse_slip': 500.329, 'OF_inviscid_slip_1ms': 493.9567462116203,
            'OF_SST_noslip_1.15ms': 488.9884147410799, 'own_coarse_v2op_slip': val['v2op_vs_v1']['thrust_exit_N']['a']}
    eff = {}
    for k, F in rows.items():
        Fi = val['v2op']['one_d']['F_ideal_N'] if 'v2op' in k else od['F_ideal_N']
        eff[k] = dict(F=F, F_over_F_ideal_1D=F / Fi)
    out['thrust_ratio_vs_ideal_1D'] = eff
    for k, v in eff.items():
        print(f"{k:24s} F {v['F']:.2f} N, F/F_ideal(1-D, same Pc) {v['F_over_F_ideal_1D']:.4f}")
    xA, xB, xS = 0.24, 0.185, 0.575
    C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
    M = C * 12.011 + H * 1.008 + N * 14.007
    add_new_fuel('RV10_ABS', f"fuel RV10_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={476.4 * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
    cea = CEA_Obj(oxName='N2O', fuelName='RV10_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K', isp_units='sec')
    At = math.pi / 4 * 0.013724 ** 2

    def F(pc, eta):
        isp, cs, _ = cea.get_IvacCstrTc(Pc=pc, MR=10.435, eps=2.0)
        cfv = isp * 9.80665 / cs
        return (eta * cfv - 2.0 * 1.01325 / pc) * pc * 1e5 * At
    need = {}
    for eta in (0.95, 0.96, 0.965, 0.975):
        need[str(eta)] = dict(F_at_25bar=F(25.0, eta), Pc_for_500N_bar=brentq(lambda p: F(p, eta) - 500.0, 20.0, 30.0))
        print(f"eta_cf {eta}: F(25 bar) {need[str(eta)]['F_at_25bar']:.1f} N, Pc for 500 N {need[str(eta)]['Pc_for_500N_bar']:.2f} bar (cap 25)")
    out['eta_cf_vs_ENG01_cap'] = need
    json.dump(out, open(os.path.join(HERE, 'rc10_gci.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
