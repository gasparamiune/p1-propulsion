"""Afterburning increment on three grids at the SAME physical time, with a temporal band (Combustion / 05-plume-cfd,
validation v2.2, 2026-10-12).

Why: the first three-level comparison of the fast-chemistry afterburning rise dT_ab (afterburn.py v3) used each run's
final state: coarse at 4.0 ms, medium at 3.0 ms, fine at 3.25 ms (dT_ab max 174.1 / 177.3 / 179.2 K). The plume is
unsteady (validation_v2.json temporal_band), so levels must be compared at one time and against the temporal scatter,
as for the flow quantities in validation v2.1a.
What: v1 operating point (O/F 7.76, Pc 24.99 bar; the v2 point O/F 10.435 has dT_ab ~ 0, see c2s_v2op_afterburn_stats).
  coarse 20k : frames at 2.50 / 2.75 / 3.00 / 3.25 ms (frame_snapshot.py; 3.00 and 3.25 ms snapshots reused)
  medium 80k : frames at 2.50 / 2.75 ms, final at 3.00 ms (afterburn_v3.npz reused), continuation m_2s_100_c325 at 3.25 ms
  fine 320k  : final at 3.25 ms (afterburn_v3.npz from lane job 095)
  plus the two time-mismatched finals (coarse 4.0 ms, medium 3.0 ms) for the record.
Metrics per state (same definitions as plot_afterburn.py: plume = fluid, x > 0, Z > 2e-3, finite T_eq):
  dT_ab max and its (x, r, Z); radial max of dT_ab at x = 5/10/20/30/40 De; volume (2 pi r dA) with dT_ab > 100 K for
  0 < x < 40 De; volume-weighted mean dT_ab over the mixing layer 0.05 < Z < 0.999, 0 < x < 40 De.
GCI per validate_plume.gci (Roache; oscillatory or p < 0.5 -> 3 x max-deviation bound) at 3.25 ms; resolvability: a
grid difference counts only if it exceeds 2 sigma of the temporal scatter of the coarse and medium levels (as v2.1a).
Fast-chemistry ASSUMPTION throughout (afterburn.py docstring): this is a bound on the afterburning, not a prediction.
usage: python afterburn_timegrid.py OUT_JSON OUT_PNG
"""
from __future__ import annotations
import json, math, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import post_plume as PP
import frame_snapshot as FS
import validate_plume as VP

ROOT = os.path.abspath(os.path.join(HERE, '..', 'ownruns'))
STATES = [  # level, t label, run npz (fields), afterburn npz, how
    ('coarse', 2.50, 'c_2s_100/snap_t2p50ms.npz', 'c_2s_100/afterburn_v3_t2p50ms.npz', ('c_2s_100', 50)),
    ('coarse', 2.75, 'c_2s_100/snap_t2p75ms.npz', 'c_2s_100/afterburn_v3_t2p75ms.npz', ('c_2s_100', 55)),
    ('coarse', 3.00, 'c_2s_100/snap_t3p00ms.npz', 'c_2s_100/afterburn_v3_t3p00ms.npz', ('c_2s_100', 60)),
    ('coarse', 3.25, 'c_2s_100/snap_t3p25ms.npz', 'c_2s_100/afterburn_v3_t3p25ms.npz', ('c_2s_100', 65)),
    ('medium', 2.50, 'm_2s_100/snap_t2p50ms.npz', 'm_2s_100/afterburn_v3_t2p50ms.npz', ('m_2s_100', 50)),
    ('medium', 2.75, 'm_2s_100/snap_t2p75ms.npz', 'm_2s_100/afterburn_v3_t2p75ms.npz', ('m_2s_100', 55)),
    ('medium', 3.00, 'm_2s_100/final.npz', 'm_2s_100/afterburn_v3.npz', None),
    ('medium', 3.25, 'm_2s_100_c325/final.npz', 'm_2s_100_c325/afterburn_v3.npz', None),
    ('fine', 3.25, 'f_2s_100/final.npz', 'f_2s_100/afterburn_v3.npz', None),
    ('coarse_final_4ms', 4.00, 'c_2s_100/final.npz', 'c_2s_100/afterburn_v3.npz', None),
]
XS = (5.0, 10.0, 20.0, 30.0, 40.0)


def cell_area(Xn, Rn):
    """Quadrilateral cell areas from node arrays (NI+1, NJ+1) by the shoelace formula."""
    x1, x2, x3, x4 = Xn[:-1, :-1], Xn[1:, :-1], Xn[1:, 1:], Xn[:-1, 1:]
    r1, r2, r3, r4 = Rn[:-1, :-1], Rn[1:, :-1], Rn[1:, 1:], Rn[:-1, 1:]
    return 0.5 * np.abs((x1 * r2 - x2 * r1) + (x2 * r3 - x3 * r2) + (x3 * r4 - x4 * r3) + (x4 * r1 - x1 * r4))


def metrics(run_npz, ab_npz):
    D = PP.load_own(run_npz)
    A = np.load(ab_npz, allow_pickle=False)
    De = D['De']; solid = D['region'] == 3
    Teq = np.where(np.isfinite(A['T_eq']), A['T_eq'], np.nan)
    dT = np.where(np.isfinite(A['dT_ab']), A['dT_ab'], np.nan)
    X = D['xc'] / De; R = D['rc'] / De
    zmask = D['Y'] > 2e-3
    fluid = (~solid) & np.isfinite(Teq) & zmask
    plume = fluid & (X > 0)
    k = int(np.nanargmax(np.where(plume, dT, -1e9)))
    out = dict(t_ms=float(D['meta']['t']) * 1e3, cells_incl_solid=int(D['xc'].size), cells_fluid=int((~solid).sum()), dTab_max_K=float(dT.flat[k]),
               dTab_max_x_De=float(X.flat[k]), dTab_max_r_De=float(R.flat[k]), dTab_max_Z=float(D['Y'].flat[k]))
    for xv in XS:
        j = int(np.argmin(np.abs(X[:, 0] - xv)))
        rad = np.where(fluid[j], dT[j], np.nan)
        out[f'radial_max_dTab_{int(xv)}De_K'] = float(np.nanmax(rad)) if np.isfinite(rad).any() else float('nan')
    Ac = cell_area(D['X'], D['R'])
    if Ac.shape != D['xc'].shape:
        raise SystemExit(f'node/cell shape mismatch {Ac.shape} vs {D["xc"].shape}')
    V = 2.0 * math.pi * D['rc'] * Ac
    box = plume & (X < 40.0)
    hot = box & (dT > 100.0)
    out['V_dTab_gt_100K_m3'] = float(V[hot].sum())
    mix = box & (D['Y'] > 0.05) & (D['Y'] < 0.999) & np.isfinite(dT)
    out['mean_dTab_mixing_layer_K'] = float((V[mix] * dT[mix]).sum() / V[mix].sum()) if mix.any() else float('nan')
    info = json.loads(str(A['info']))
    out['OF'] = info.get('OF'); out['cells_failed'] = info.get('cells_failed')
    return out


def ensure(level, t, run_rel, ab_rel, snap):
    import afterburn as AB
    run = os.path.join(ROOT, run_rel); ab = os.path.join(ROOT, ab_rel)
    made = []
    if not os.path.exists(run):
        if snap is None:
            raise SystemExit(f'missing {run}')
        FS.main(os.path.join(ROOT, snap[0]), snap[1], run); made.append('snapshot')
    if not os.path.exists(ab):
        t0 = time.time()
        AB.process(run, ab, 1.0); made.append(f'afterburn {time.time() - t0:.0f} s')
    return made


def main(out_json, out_png):
    rows = []
    for level, t, run_rel, ab_rel, snap in STATES:
        made = ensure(level, t, run_rel, ab_rel, snap)
        m = metrics(os.path.join(ROOT, run_rel), os.path.join(ROOT, ab_rel))
        m.update(level=level, t_label_ms=t, run=run_rel, afterburn=ab_rel, computed_now=made)
        rows.append(m); print(level, t, round(m['t_ms'], 4), round(m['dTab_max_K'], 2), made, flush=True)
    keys = ['dTab_max_K', 'dTab_max_x_De', 'dTab_max_r_De', 'V_dTab_gt_100K_m3', 'mean_dTab_mixing_layer_K'] + \
           [f'radial_max_dTab_{int(x)}De_K' for x in XS]
    pick = lambda lev, t: next(r for r in rows if r['level'] == lev and abs(r['t_label_ms'] - t) < 1e-9)
    f, m_, c = pick('fine', 3.25), pick('medium', 3.25), pick('coarse', 3.25)
    band = {}
    for lev in ('coarse', 'medium'):
        rr = [r for r in rows if r['level'] == lev]
        band[lev] = {k: dict(mean=float(np.mean([r[k] for r in rr])), std=float(np.std([r[k] for r in rr], ddof=1)),
                             min=float(np.min([r[k] for r in rr])), max=float(np.max([r[k] for r in rr])), n=len(rr),
                             t_ms=[r['t_label_ms'] for r in rr]) for k in keys}
    G, RES = {}, {}
    for k in keys:
        G[k] = VP.gci(f[k], m_[k], c[k]); G[k].update(fine=f[k], medium=m_[k], coarse=c[k])
        dfm, dmc = f[k] - m_[k], m_[k] - c[k]
        s = max(band['coarse'][k]['std'], band['medium'][k]['std'])
        res = (abs(dfm) > 2 * s) or (abs(dmc) > 2 * s)
        RES[k] = dict(fine_minus_medium=dfm, medium_minus_coarse=dmc, std_coarse=band['coarse'][k]['std'],
                      std_medium=band['medium'][k]['std'], resolvable=bool(res),
                      verdict=('grid effect resolved above the temporal scatter' if res else
                               'grid differences within 2 sigma of the temporal scatter: GCI not meaningful; report the band'))
    mism = dict(coarse_4p0ms=pick('coarse_final_4ms', 4.0)['dTab_max_K'], medium_3p0ms=pick('medium', 3.0)['dTab_max_K'],
                fine_3p25ms=f['dTab_max_K'],
                note='first comparison (each run final state, different times): kept as evidence; superseded by the 3.25 ms set')
    res = dict(version='v2.2', date='2026-10-12', script='cfd/own/afterburn_timegrid.py',
               operating_point='v1 point O/F 7.76, Pc 24.99 bar, T0 2844.9 K (the CFD runs c/m/f_2s_100); fast-chemistry ASSUMPTION',
               states=rows, temporal_band_2p50_3p25ms=band, gci_3p25ms=G, resolvability=RES, time_mismatched_first_comparison=mism,
               note=('dT_ab = T_eq - T_inert (afterburn.py v3). Bound on the afterburning (fast chemistry, mean Z, no '
                     'finite-rate kinetics, no turbulence-chemistry interaction); the v2 operating point O/F 10.435 gives '
                     'dT_ab <= 0.44 K (c2s_v2op_afterburn_stats.json), the 12.5 % floor O/F 3.1-4.1 gives 1322-1476 K (coarse)'))
    json.dump(res, open(out_json, 'w'), indent=1, default=float)
    # figure
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    for lev, col, mk in (('coarse', 'tab:blue', 'o'), ('medium', 'tab:orange', 's'), ('fine', 'tab:green', 'D')):
        rr = sorted([r for r in rows if r['level'] == lev], key=lambda r: r['t_ms'])
        ax[0].plot([r['t_ms'] for r in rr], [r['dTab_max_K'] for r in rr], marker=mk, color=col, label=f'{lev} ({rr[0]["cells_fluid"]} fluid cells)')
        ax[1].plot([r['t_ms'] for r in rr], [r['V_dTab_gt_100K_m3'] * 1e6 for r in rr], marker=mk, color=col, label=lev)
    r4 = pick('coarse_final_4ms', 4.0)
    ax[0].plot([r4['t_ms']], [r4['dTab_max_K']], 'o', mfc='none', color='tab:blue', label='coarse final 4.0 ms (first comparison)')
    ax[0].set_xlabel('t [ms]'); ax[0].set_ylabel('max dT_ab in the plume [K]'); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=7)
    ax[1].set_xlabel('t [ms]'); ax[1].set_ylabel('volume with dT_ab > 100 K, x < 40 De [cm3]'); ax[1].grid(alpha=0.3)
    ax[1].legend(fontsize=7)
    fig.suptitle('Afterburning rise (fast-chemistry bound), v1 point O/F 7.76: grid levels at the same times, '
                 '2.50-3.25 ms (afterburn_timegrid.py)', fontsize=9)
    fig.savefig(out_png, bbox_inches='tight', dpi=170); plt.close(fig)
    for k in ('dTab_max_K', 'V_dTab_gt_100K_m3', 'mean_dTab_mixing_layer_K', 'radial_max_dTab_20De_K'):
        print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in G[k].items()}, RES[k]['verdict'])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
