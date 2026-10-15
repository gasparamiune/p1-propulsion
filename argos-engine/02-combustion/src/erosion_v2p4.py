"""Throat-insert life on the current duty cycles (Combustion v2.4, RC-06; 2026-10-13).

Applies the three erosion estimates of erosion_dc.py (v2, unchanged methods) to the grain_q1d v2 histories of the GNC v3
dispersed cycles (lead decision 2026-10-13: B1 sizing = DC-B1 v3 dispersed p99, max run as a check; A1 sizing = DC-A1
dispersed p99; _tg711 = the same cycles with GNC's throat-growth model) and of the (a, n) band runs:
  nominal      : coupled kinetics + film diffusion, delivered-state edge composition, Bartz with delivered T0      [SIM]
  conservative : coupled, CEA-ideal throat composition, T0 = Tc for the heat transfer                             [SIM]
  literature   : N2O/HDPE graphite rates (Rotondi et al. JPP 2024, as used in v2) scaled (Pc/35 bar)^0.68, binned
                 by O/F (>= 7: 0.098-0.139 mm/s; 4.8-7: 0.018-0.048 mm/s; < 4.8: 0) after a 1.5 s cumulative onset   [LITERATURE-scaled]
Life rule: insert replaced at dAt/At = 5 % (ENG-06) -> recession limit Rt0 (sqrt(1.05) - 1) = 0.1695 mm (Dt0 13.724 mm).
Flights per insert = limit / recession per flight (one cycle = one flight). The literature method carries the onset per
flight (a fresh insert would not need the onset again on later flights if the onset is a surface-conditioning effect;
counting it per flight is the optimistic reading and is stated).
usage: python -I erosion_v2p4.py OUTDIR [--coupled] label=path.csv ...
"""
from __future__ import annotations
import hashlib, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nozzle as N
import erosion_dc as E

RT0 = 0.013724 / 2
DELTA_LIM = RT0 * (math.sqrt(1.05) - 1.0)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def literature_no_onset_repeat(t, Pc, OF, on):
    """Literature method with the 1.5 s onset applied only once per insert life (pessimistic reading): rates from t = 0."""
    lo = hi = 0.0
    for k in range(1, len(t)):
        dt = t[k] - t[k - 1]
        if not on[k] or not np.isfinite(OF[k]):
            continue
        sc = (Pc[k] / 35e5) ** 0.68
        if OF[k] >= 7.0:
            lo += 0.098e-3 * sc * dt; hi += 0.139e-3 * sc * dt
        elif OF[k] >= 4.8:
            lo += 0.018e-3 * sc * dt; hi += 0.048e-3 * sc * dt
    return lo, hi


def one(label, fn, coupled, TP):
    r = pd.read_csv(fn)
    t = r.t.values; Pc = r.Pc.values; OF = r.OF.values; on = (r.mox.values > 1e-4) & (Pc > 1.5e5)
    dt = np.diff(t, prepend=t[0])
    burn = float(dt[on].sum())
    of_bins = dict(ge7=float(dt[on & (OF >= 7.0)].sum()), b48_7=float(dt[on & (OF >= 4.8) & (OF < 7.0)].sum()),
                   lt48=float(dt[on & (OF < 4.8)].sum()))
    out = dict(history=os.path.relpath(fn, os.path.join(HERE, '..')), history_sha256_16=sha16(fn), burn_s=round(burn, 3),
               time_in_OF_bins_s={k: round(v, 3) for k, v in of_bins.items()},
               Pc_time_mean_bar=round(float((Pc[on] * dt[on]).sum() / max(burn, 1e-9) / 1e5), 3))
    lo, hi = E.literature(t, Pc, OF, on)
    lo2, hi2 = literature_no_onset_repeat(t, Pc, OF, on)
    out['literature'] = dict(recession_mm=[round(lo * 1e3, 4), round(hi * 1e3, 4)],
                             dAt_over_At_pct=[round(100 * ((1 + lo / RT0) ** 2 - 1), 3), round(100 * ((1 + hi / RT0) ** 2 - 1), 3)],
                             flights_per_insert=[round(DELTA_LIM / hi, 3) if hi > 0 else None, round(DELTA_LIM / lo, 3) if lo > 0 else None],
                             no_onset_repeat=dict(recession_mm=[round(lo2 * 1e3, 4), round(hi2 * 1e3, 4)],
                                                  flights_per_insert=[round(DELTA_LIM / hi2, 3) if hi2 > 0 else None,
                                                                      round(DELTA_LIM / lo2, 3) if lo2 > 0 else None]))
    if coupled:
        for lab, kw in (('nominal', dict(comp='delivered', eta_T=0.92)), ('conservative', dict(comp='ideal', eta_T=1.0))):
            t0 = time.time()
            ins, hist = N.run_history(t, Pc, OF, on, TP, dt=5e-3, record=0.1, **kw)
            h = pd.DataFrame(hist)
            rec = ins.recession
            out[lab] = dict(recession_mm=round(rec * 1e3, 4), dAt_over_At_pct=round(100 * ((ins.Rt / ins.Rt0) ** 2 - 1), 3),
                            flights_per_insert=round(DELTA_LIM / rec, 3) if rec > 0 else None,
                            Tw_max_K=round(float(h.Tw.max()), 0), q_in_max_MW_m2=round(float(h.q_in.max()) / 1e6, 2), wall_s=round(time.time() - t0, 1))
    return out


def main(argv):
    outdir = argv[0]; coupled = '--coupled' in argv
    items = [a.split('=', 1) for a in argv[1:] if '=' in a]
    os.makedirs(outdir, exist_ok=True)
    fn = os.path.join(outdir, 'erosion_v2p4.json')
    res = json.load(open(fn)) if os.path.exists(fn) else dict(
        version='v2.4', date='2026-10-13', script='02-combustion/src/erosion_v2p4.py', methods_from='02-combustion/src/erosion_dc.py (v2)',
        life_rule=dict(dAt_over_At_limit=0.05, Rt0_m=RT0, recession_limit_mm=round(DELTA_LIM * 1e3, 5), tag='REQ ENG-06 (5 %); DERIVED limit'),
        tags=dict(nominal='SIM', conservative='SIM', literature='LITERATURE-scaled (Rotondi et al. JPP 2024 N2O/HDPE, as used in v2; '
                  'rates not re-verified in this revision)'), runs={})
    TP = N.ThroatProps()
    for label, path in items:
        key = label + ('|coupled' if coupled else '|lit')
        if key in res['runs'] or (not coupled and (label + '|coupled') in res['runs']):
            continue
        o = one(label, path, coupled, TP)
        res['runs'][key] = o
        json.dump(res, open(fn, 'w'), indent=1)
        print(key, json.dumps({k: v for k, v in o.items() if k not in ('history',)}), flush=True)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1:])
