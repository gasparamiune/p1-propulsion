"""RC-09: eta_cf band and the Pc needed for 500 N at the 25 bar cap (Combustion v2.4, 2026-10-13).

Method (DERIVED): at fixed O/F and eps the sea-level thrust is F = eta_cf (Cf_vac Pc - eps pa) At. Cf_vac is backed out of the
published design point (500 N at Pc 25.01 bar with eta_cf 0.975, At 1.4793e-4 m2, eps 2.0; Table 4.2, CEA) and held fixed;
Pc for 500 N and F at the 25 bar cap then follow for each eta_cf. Shifting-equilibrium changes of Cf_vac with Pc over
25.0-25.7 bar are neglected (< 0.1 %, CEA tables).
Band: 0.975 (own inviscid CFD, slip walls) to 0.95 (OpenFOAM no-slip coarse, review RC-09; -1 % viscous from slip to no-slip).
usage: python -I rc09_etacf_band_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True

AT = 1.479283e-4      # m2, Dt 13.724 mm (combustion.json)
EPS = 2.0
PA = 101325.0
PC0, F0, ETA0 = 25.01e5, 500.0, 0.975


def main(outdir):
    cfv = (F0 / (ETA0 * AT) + EPS * PA) / PC0
    rows = {}
    for eta in (0.975, 0.97, 0.965, 0.96, 0.955, 0.95):
        pc500 = (F0 / (eta * AT) + EPS * PA) / cfv
        f25 = eta * (cfv * 25e5 - EPS * PA) * AT
        rows[f'{eta:.3f}'] = dict(Pc_for_500N_bar=pc500 / 1e5, F_at_25bar_N=f25, margin_to_cap_bar=25.0 - pc500 / 1e5)
        print(f'eta_cf {eta:.3f}: Pc(500 N) {pc500/1e5:.2f} bar, F(25 bar) {f25:.1f} N')
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/rc09_etacf_band_v2p4.py', closes='REVIEW-COMBUSTION RC-09',
               Cf_vac_backed_out=cfv, inputs=dict(At_m2=AT, eps=EPS, pa_Pa=PA, design_point='500 N at 25.01 bar, eta_cf 0.975 (Table 4.2)'),
               band=dict(v=[0.95, 0.975], tag='ASSUMED from CFD: own solver slip 0.9755; OpenFOAM slip 0.962, no-slip SST 0.9525 (review RC-09); T1 measures'),
               rows=rows, tag='DERIVED')
    fn = os.path.join(outdir, 'rc09_etacf_band_v2p4.json')
    json.dump(out, open(fn, 'w'), indent=1)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
