"""Throat-insert soak-back: sensitivity to the retainer / retention-lip heat sink (Combustion v2, 2026-10-12).

Why: Mechanical CAD v3.1 retains the graphite insert with a 6 mm lip bearing on an insert shoulder, T_allow 240 C
(CHANGELOG 2026-10-12). soakback.py v2 used a 0.15 kg lumped retainer (ASSUMED). The v3.1 lip mass, material and the
insulation between graphite and metal are not yet defined, so this script brackets them instead of inventing them:
  retainer (lumped) mass 0.15 / 0.30 / 0.60 kg, aluminium (c 900 J/kgK) or steel (c 500 J/kgK),
  graphite -> retainer conductance hc 2000 (bare contact) / 500 / 150 W/m2K (about 2 mm phenolic or ceramic paper).
Model: identical to soakback.py (nozzle.ThroatInsert through the duty-cycle history, then 900 s soak with bore radiation
eps*F 0.25 and retainer losses h 15 W/m2K over 6.3e-3 m2, all ASSUMED). The insert is the 0.081 kg throat slice of the
44 mm OD x 32 mm v3.0 envelope; the v3.1 spigot adds graphite mass and is NOT represented (it stores more heat).
Duty cycles: GNC duty_cycles v2 working copy (snapshot 2026-10-12T19:15Z, PREVIEW) run through grain_q1d v2 (S230).
Outputs: data/v2/soakback_sens_v2.json and .csv. SIM (lumped/1-D sizing check; thermal FEA by Mechanical supersedes).
usage: python soakback_sens.py DC_DIR OUTDIR file1.csv [file2.csv ...]
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nozzle as N
from soakback import insert_soak, TA


def run(dcdir, outdir, files):
    TP = N.ThroatProps()
    rows = []
    for fn in files:
        r = pd.read_csv(os.path.join(dcdir, fn))
        t = r.t.values; Pc = r.Pc.values; OF = r.OF.values; on = (r.mox.values > 1e-4) & (Pc > 1.5e5)
        i_last = int(np.where(on)[0][-1]) if on.any() else len(t) - 1
        t_end = t[min(i_last + 2, len(t) - 1)]
        for mat, csl in (('Al', 900.0), ('steel', 500.0)):
            for msl in (0.15, 0.30, 0.60):
                for hc in (2000.0, 500.0, 150.0):
                    ins = N.ThroatInsert(T0=TA, hc=hc, m_sleeve=msl, c_sleeve=csl)
                    tn = t[0]; dtb = 5e-3
                    while tn <= t_end:
                        i = min(np.searchsorted(t, tn), len(t) - 1)
                        ins.step(dtb, float(Pc[i]), float(OF[i]) if np.isfinite(OF[i]) else 5.0, TP, bool(on[i]))
                        tn += dtb
                    Ts_sd = ins.Ts; Tavg = float(ins.T.mean())
                    hist = insert_soak(ins)
                    pk = max(hist, key=lambda h: h['T_retainer'])
                    row = dict(duty_cycle=fn.replace('.csv', ''), retainer_material=mat, retainer_mass_kg=msl, hc_W_m2K=hc,
                               t_last_shutdown_s=float(t_end), T_insert_mean_at_shutdown_K=Tavg,
                               T_retainer_at_shutdown_K=float(Ts_sd), T_retainer_peak_K=float(pk['T_retainer']),
                               t_peak_after_shutdown_s=float(pk['t_after_shutdown']),
                               T_retainer_900s_K=float(hist[-1]['T_retainer']))
                    rows.append(row)
                    print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    df = pd.DataFrame(rows)
    hdr = ('# Throat-insert soak-back sensitivity to the retainer heat sink (SIM, lumped/1-D; Combustion v2 2026-10-12). '
           'Duty cycles = GNC v2 working-copy PREVIEW through grain_q1d v2 (S230). Retainer mass, material and hc are '
           'BRACKETS, not design values. 240 C = 513 K (Mechanical v3.1 lip T_allow). SI.\n')
    with open(os.path.join(outdir, 'soakback_sens_v2.csv'), 'w') as f:
        f.write(hdr); df.to_csv(f, index=False, float_format='%.5g')
    summ = {}
    for (dc, mat), g in df.groupby(['duty_cycle', 'retainer_material']):
        summ[f'{dc}|{mat}'] = dict(T_retainer_peak_K_min=float(g.T_retainer_peak_K.min()),
                                   T_retainer_peak_K_max=float(g.T_retainer_peak_K.max()),
                                   cases_below_513K=int((g.T_retainer_peak_K < 513.15).sum()), cases=int(len(g)))
    json.dump(dict(version='v2', date='2026-10-12', tool='soakback_sens.py', limit_K=513.15,
                   limit_source='mechanical CAD v3.1 retention lip T_allow 240 C (interfaces CHANGELOG 2026-10-12)',
                   summary=summ, rows=rows), open(os.path.join(outdir, 'soakback_sens_v2.json'), 'w'), indent=1)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], sys.argv[3:])
