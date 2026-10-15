"""Throat erosion and insert thermal history over the duty cycles (Combustion v2).
usage: python erosion_dc.py DC_DIR OUTDIR case1.csv case2.csv ...
Three estimates per duty cycle:
  nominal      : coupled kinetics + film diffusion, delivered-state edge composition (Cantera equilibrium at eta_c*^2 Tc),
                 Bartz with delivered T0 (eta_c* = 0.92)                                    [SIM]
  conservative : coupled, CEA-ideal throat composition, T0 = Tc (eta = 1) for the heat transfer [SIM]
  literature   : measured N2O/HDPE graphite rates (Rotondi et al. JPP 2024) scaled with (Pc/35 bar)^0.68 and binned by O/F
                 (>= 7: 0.098-0.139 mm/s; 4.8-7: 0.018-0.048 mm/s; < 4.8: 0), applied after a 1.5 s cumulative onset
                 (lower bound of the measured 1.5-4 s)                                      [LITERATURE-scaled]
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nozzle as N


def literature(t, Pc, OF, on):
    lo = hi = 0.0; cum = 0.0
    for k in range(1, len(t)):
        dt = t[k] - t[k - 1]
        if not on[k]:
            continue
        cum += dt
        if cum < 1.5:
            continue
        sc = (Pc[k] / 35e5) ** 0.68
        of = OF[k]
        if not np.isfinite(of):
            continue
        if of >= 7.0:
            lo += 0.098e-3 * sc * dt; hi += 0.139e-3 * sc * dt
        elif of >= 4.8:
            lo += 0.018e-3 * sc * dt; hi += 0.048e-3 * sc * dt
    return lo, hi


def main(dcdir, outdir, files):
    TP = N.ThroatProps()
    res = {}
    for fn in files:
        r = pd.read_csv(os.path.join(dcdir, fn))
        t = r.t.values; Pc = r.Pc.values; OF = r.OF.values; on = (r.mox.values > 1e-4) & (Pc > 1.5e5)
        out = {}
        for lab, kw in (('nominal', dict(comp='delivered', eta_T=0.92)), ('conservative', dict(comp='ideal', eta_T=1.0))):
            ins, hist = N.run_history(t, Pc, OF, on, TP, dt=5e-3, record=0.1, **kw)
            h = pd.DataFrame(hist)
            h.to_csv(os.path.join(outdir, fn.replace('.csv', f'_throat_{lab}.csv')), index=False, float_format='%.6g')
            out[lab] = dict(recession_mm=round(ins.recession * 1e3, 4), Tw_max_K=round(float(h.Tw.max()), 0),
                            T_sleeve_max_K=round(float(h.T_sleeve.max()), 0), q_in_max_MW_m2=round(float(h.q_in.max()) / 1e6, 2),
                            dAt_over_At_pct=round(100 * ((ins.Rt / ins.Rt0) ** 2 - 1), 3))
        lo, hi = literature(t, Pc, OF, on)
        out['literature_scaled_mm'] = [round(lo * 1e3, 4), round(hi * 1e3, 4)]
        res[fn] = out
        print(fn, json.dumps(out), flush=True)
    json.dump(res, open(os.path.join(outdir, 'erosion_dc_v2.json'), 'w'), indent=1)
    return res


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
