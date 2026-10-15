"""MEOP basis across line-loss law, eta_c* and tank temperature (Combustion v2.4, RC-08; 2026-10-13).

Steady chamber pressure with the pintle stuck at full stroke (4 mm), S230 initial port (the highest-Pc state: tank at its
initial pressure, smallest port), saturated tank at T (failure_cases.py v2 method, grain_q1d v2), over:
  line loss : 'author'   2.5 bar x (mdot/0.25)^2   (simulation law used for the v2.3 basis, 42.85 bar)
              'hardware' 117 kPa at 0.26 kg/s x (mdot/0.26)^2 (Cv 3 valve + Cv 2.2 filter, REPORT v2.3 Table 2.6; review RC-08)
              'zero'     no line loss (bound)
  eta_c*    : 0.92 (design), 0.96 (top of the 0.85-0.96 band)
  Cd        : 0.70, 0.80
  T_tank    : 15, 20, 25, 30 C (25 C = ARM limit, ENG-01/ENG-12; 30 C = v2.3 basis)
and, at Cd 0.80 / eta_c* 0.96 with the hardware and zero line losses at 25 and 30 C, the regression band corners
(a x0.6-1.5, n 0.35-0.68, re-anchored at r(300) = 1 mm/s as in RC-07): more fuel at full stroke changes O/F and Pc.
usage: python -I meop_basis_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q, injector as INJ
from run_dc import _FixedTank

LAWS = {'author': 2.5e5, 'hardware': 117e3 * (0.25 / 0.26) ** 2, 'zero': 0.0}


def main(outdir):
    rows = []
    for law, dpref in LAWS.items():
        for eta in (0.92, 0.96):
            for cd in (0.70, 0.80):
                for Tc in (15.0, 20.0, 25.0, 30.0):
                    T = Tc + 273.15; pv = INJ.psat(T)
                    e = Q.Engine(_FixedTank(pv, T), cfg=dict(Cd=cd, eta_cstar=eta, dp_line_ref=dpref))
                    s = e.steady(INJ.STROKE)
                    rows.append(dict(line_loss=law, eta_cstar=eta, Cd=cd, T_tank_C=Tc, Pv_bar=round(pv / 1e5, 3),
                                     Pc_bar=round(float(s['Pc']) / 1e5, 2), mox_kg_s=round(float(s['mox']), 4),
                                     dp_line_bar=round(float(pv - s['P1']) / 1e5, 3), OF=round(float(s['OF']), 2), F_N=round(float(s['F']), 1)))
                    print(rows[-1], flush=True)
    # regression band at the worst combination (the v2.3 basis used the nominal law): more fuel at full stroke raises Pc
    band = []
    for law in ('hardware', 'zero'):
        for Tc in (25.0, 30.0):
            T = Tc + 273.15; pv = INJ.psat(T)
            for ab, n in ((1.0, 0.5), (0.6, 0.35), (0.6, 0.68), (1.0, 0.35), (1.0, 0.68), (1.5, 0.35), (1.5, 0.5), (1.5, 0.68)):
                e = Q.Engine(_FixedTank(pv, T), cfg=dict(Cd=0.80, eta_cstar=0.96, dp_line_ref=LAWS[law], a=1.0e-3 / 300.0 ** n * ab, n=n))
                s = e.steady(INJ.STROKE)
                band.append(dict(line_loss=law, eta_cstar=0.96, Cd=0.80, T_tank_C=Tc, a_band=ab, n=n, Pc_bar=round(float(s['Pc']) / 1e5, 2),
                                 OF=round(float(s['OF']), 2), mox_kg_s=round(float(s['mox']), 4), F_N=round(float(s['F']), 1)))
                print('band', band[-1], flush=True)
    # ARM-limit scan: worst regression-band corner against tank temperature (Cd 0.80, eta_c* 0.96, hardware and zero line loss)
    scan = []
    for law in ('hardware', 'zero'):
        for Tc in (18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0):
            T = Tc + 273.15; pv = INJ.psat(T)
            worst = None
            for ab, n in ((1.0, 0.5), (1.0, 0.68), (1.5, 0.35), (1.5, 0.5), (1.5, 0.68)):
                e = Q.Engine(_FixedTank(pv, T), cfg=dict(Cd=0.80, eta_cstar=0.96, dp_line_ref=LAWS[law], a=1.0e-3 / 300.0 ** n * ab, n=n))
                s = e.steady(INJ.STROKE)
                r = dict(a_band=ab, n=n, Pc_bar=round(float(s['Pc']) / 1e5, 2))
                if worst is None or r['Pc_bar'] > worst['Pc_bar']:
                    worst = r
            scan.append(dict(line_loss=law, T_tank_C=Tc, Pv_bar=round(pv / 1e5, 3), worst_corner=worst))
            print('scan', scan[-1], flush=True)
    mx = {}
    for Tlim in (25.0, 30.0):
        sub = [r for r in rows if r['T_tank_C'] <= Tlim]
        top = max(sub, key=lambda r: r['Pc_bar'])
        mx[f'max_T_le_{Tlim:.0f}C'] = top
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/meop_basis_v2p4.py', closes='REVIEW-COMBUSTION RC-08',
               note='SIM grain_q1d v2 steady, pintle stuck at full stroke 4 mm, S230 initial port, saturated tank (fixed P, T); '
                    'the v2.3 basis 42.85 bar = author law, eta 0.92, Cd 0.8, 30 C over the burn (full_stroke_failure_case_v2.json)',
               tags=dict(line_loss='author: ASSUMED simulation law; hardware: DERIVED REPORT v2.3 Table 2.6; zero: bound',
                         eta_cstar='ASSUMED band 0.85-0.96', Cd='ASSUMED 0.6-0.8', T_tank='REQ ENG-01/ENG-12 15-25 C at ARM'),
               rows=rows, maxima=mx, regression_band_worst_combination=band, arm_limit_scan=scan,
               regression_band_note='laws re-anchored at r(300 kg/m2s) = 1 mm/s x band (as RC-07); Cd 0.80, eta_c* 0.96')
    fn = os.path.join(outdir, 'meop_basis_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1)
    print(json.dumps(mx, indent=1)); print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])
