"""Gas-side thermal boundary conditions v2 (Combustion, brief task 5): Bartz h_g(x), T_aw(x), p(x), radiation band along
the v2 gas path (S230 straight-port grain: grain 30 mm longer than v1, nozzle contour shifted +30 mm in x_face; throat,
exit and nozzle shape unchanged) at 100 / 75 / 50 / 20 / 12.5 % thrust (20 C saturated tank, initial port).
Re-uses m1_design.thermal_bc (Bartz 1957 closed form, see heat.py).  Outputs:
  data/v2/thermal_bc_<label>_v2.csv, data/v2/nozzle_contour_v2.csv, data/v2/thermal_bc_summary_v2.json
usage: python thermal_bc_v2.py OUTDIR
"""
from __future__ import annotations
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1_design as M
import grain_q1d as Q
import injector as INJ
from run_dc import _FixedTank


def main(out):
    d_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    P = M.load_perf(d_data)
    noz = M.size_nozzle(P)
    L_grain = Q.V['L_grain']
    x_grain0 = M.V['L_pre']; x_grain1 = M.V['L_pre'] + L_grain; x_conv0 = x_grain1 + M.V['L_post']
    Rc = M.V['D_grain'] / 2 + 0.0002
    contour, st = M.nozzle_contour(noz['Dt'], M.V['eps'], x_conv0, Rc)
    with open(os.path.join(out, 'nozzle_contour_v2.csv'), 'w', newline='') as f:
        f.write(f'# Gas-path contour v2 (Combustion, 2026-10-12): v1 nozzle shape, grain {L_grain*1e3:.0f} mm (v1 200 mm) so all '
                f'x_face values are +{(L_grain-0.2)*1e3:.0f} mm vs v1. x_face_m from the injector face toward the exit; x_throat_m '
                f'from the throat; r_m radius. Upstream of the first row: post-chamber cylinder r = {Rc:.5f} m. CAD +Z forward => '
                f'z = x_exit_face - x_face.\n')
        w = csv.writer(f); w.writerow(['x_face_m', 'x_throat_m', 'r_m', 'region'])
        for r in contour:
            w.writerow([round(r['x_face'], 7), round(r['x_throat'], 7), round(r['r'], 7), r['region']])
    T = 293.15; pv = INJ.psat(T)
    e = Q.Engine(_FixedTank(pv, T)); cei = e.ceiling()
    summ = dict(version='v2', date='2026-10-12', grain='v2 S230 straight port', x_face_throat_m=st['x_throat_face'],
                x_face_exit_m=st['x_exit_face'], gas_path_length_m=st['x_exit_face'], points={})
    for lab, fr in (('max', 1.0), ('75pct', 0.75), ('50pct', 0.5), ('20pct', 0.2), ('floor12p5', 0.125)):
        h, _ = e.lift_for_thrust(500 * fr, cei=cei); s = e.steady(h)
        fn, peak, props = M.thermal_bc(P, noz, contour, st, s['Pc'], s['OF'], lab, out, x_grain0, x_grain1)
        txt = open(fn).read().replace('# Thermal BC v1', '# Thermal BC v2 (S230 grain; contour +30 mm vs v1)').replace(
            'SIM m1_design.py.', 'SIM thermal_bc_v2.py (m1_design.thermal_bc).')
        fn2 = fn.replace('_v1.csv', '_v2.csv')
        open(fn2, 'w').write(txt); os.remove(fn)
        summ['points'][lab] = dict(file=os.path.basename(fn2), frac=fr, Pc_Pa=s['Pc'], OF=s['OF'], T0_delivered_K=props['T0'],
                                   peak_q_conv_Tw600_W_m2=peak['q_conv_Tw600_W_m2'], peak_h_g_Tw600_W_m2K=peak['h_g_Tw600_W_m2K'],
                                   peak_x_throat_m=peak['x_throat_m'], T_aw_at_peak_K=peak['T_aw_K'])
        print(lab, json.dumps(summ['points'][lab], default=float))
    json.dump(summ, open(os.path.join(out, 'thermal_bc_summary_v2.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main(sys.argv[1])
