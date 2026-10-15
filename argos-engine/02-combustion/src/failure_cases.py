"""Pintle full-stroke (servo runaway / stuck-open) failure case: steady chamber pressure at 4 mm lift
(Combustion v2; sets the chamber MEOP; lead decision 2026-10-12: MEOP 45 bar, proof 67.5 bar).
usage: python failure_cases.py OUTDIR    -> OUTDIR/full_stroke_failure_case_v2.json   (SIM grain_q1d v2)"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grain_q1d as Q, injector as INJ
from run_dc import _FixedTank

rows = []
for gname, g in Q.VARIANTS.items():
    for Tc in (15.0, 20.0, 25.0, 30.0):
        T = Tc + 273.15; pv = INJ.psat(T)
        for cd in (0.6, 0.7, 0.8):
            e = Q.Engine(_FixedTank(pv, T), cfg=dict(Q.V, Cd=cd, **g))
            s = e.steady(INJ.STROKE)
            rows.append(dict(grain=gname, T_tank_C=Tc, Pv_bar=round(pv / 1e5, 2), Cd=cd, Pc_full_stroke_bar=round(float(s['Pc']) / 1e5, 2),
                             F_N=round(float(s['F']), 1), OF=round(float(s['OF']), 2), dP_over_Pc=round(float(s['dpc']), 3)))
            print(rows[-1], flush=True)
json.dump(dict(version='v2', date='2026-10-12', note='Steady chamber pressure with the pintle at full stroke (4 mm): servo-runaway / '
               'stuck-open failure case at the initial port, saturated tank at T (SIM grain_q1d v2, Dyer x Cd). Basis of the '
               'chamber MEOP 45 bar (lead decision 2026-10-12). Blocked-nozzle bound = tank pressure (63 bar at 30 C).',
               rows=rows), open(os.path.join(sys.argv[1], 'full_stroke_failure_case_v2.json'), 'w'), indent=1)
