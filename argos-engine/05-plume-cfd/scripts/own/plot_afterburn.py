"""Afterburning-temperature figures and statistics from afterburn.py v3 output (Combustion / 05-plume-cfd v3).

Fields (fast-chemistry ASSUMPTION, labelled on every figure):
  T_eq     : HP equilibrium of the local exhaust/air mixture (complete afterburning, upper bound of the kinetics);
  dT_ab    : T_eq - T_inert, afterburning temperature rise (reference: exhaust in local equilibrium, air inert);
  T_ab_cfd : CFD temperature + dT_ab;  X_CO, X_OH (equilibrium).  The stoichiometric contour Z_st is overlaid.
usage: python plot_afterburn.py RUN/final.npz AFTERBURN.npz OUTDIR TAG
"""
from __future__ import annotations
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import post_plume as PP


def main(run_npz, ab_npz, outdir, tag):
    os.makedirs(outdir, exist_ok=True)
    D = PP.load_own(run_npz)
    A = np.load(ab_npz, allow_pickle=False)
    info = json.loads(str(A['info']))
    De = D['De']; solid = D['region'] == 3
    fin = lambda k: np.where(np.isfinite(A[k]), A[k], np.nan)
    Teq, Tin, dT, Tab, TeqB = fin('T_eq'), fin('T_inert'), fin('dT_ab'), fin('T_ab_cfd'), fin('T_eqB')
    Zst = info.get('Z_st', float('nan'))
    ttl = (f"{tag}: t = {D['meta']['t'] * 1e3:.2f} ms, O/F {info.get('OF', float('nan')):.2f}, Z_st = {Zst:.3f} (white line). "
           f"Afterburning by FAST-CHEMISTRY post-processing\n(Cantera GRI-3.0 thermo, HP equilibrium of the local "
           f"exhaust/air mixture; exhaust energy matched to the CFD exit plane; mean Z, no finite-rate kinetics)")
    zmask = D['Y'] > 2e-3
    specs = [('Teq', np.where(zmask, Teq, np.nan), 'inferno', colors.Normalize(250, max(3000.0, float(np.nanmax(Teq)))),
              'T_eq [K] (complete afterburning)'),
             ('dTab', np.where(zmask, dT, np.nan), 'YlOrRd', colors.Normalize(0.0, max(300.0, float(np.nanmax(dT)))),
              'dT_ab = T_eq - T_inert [K]'),
             ('Tcfd_ab', Tab, 'inferno', colors.Normalize(250, max(3000.0, float(np.nanmax(Tab)))),
              'T_cfd + dT_ab [K]'),
             ('XCO', A['X_CO'], 'viridis', colors.Normalize(0, max(0.02, float(np.nanmax(A['X_CO'])))), 'X_CO (equilibrium)'),
             ('XOH', A['X_OH'], 'plasma', colors.Normalize(0, max(1e-3, float(np.nanmax(A['X_OH'])))), 'X_OH (equilibrium)')]
    files = []
    X = D['xc'] / De; R = D['rc'] / De
    for name, F, cm, nm, lab in specs:
        for zoom, xl, rl, fs in (('near', (-1.5, 15), 3.0, (10, 4.4)), ('full', (-4, 45), 12.0, (12, 6.6))):
            fig, ax = plt.subplots(figsize=fs)
            PP.plot_field(ax, D, np.ma.masked_invalid(F), cm, nm, xlim=xl, rlim=rl, label=lab)
            if np.isfinite(Zst):
                Zm = np.ma.masked_where(solid, D['Y'])
                for s in (1, -1):
                    ax.contour(X, s * R, Zm, levels=[Zst], colors='w', linewidths=0.7)
            ax.set_title(ttl, loc='left', fontsize=7)
            fn = os.path.join(outdir, f'{tag}_{name}_{zoom}.png')
            fig.savefig(fn, bbox_inches='tight'); plt.close(fig); files.append(fn)
    # statistics
    fluid = (~solid) & np.isfinite(Teq) & zmask
    plume = fluid & (X > 0)
    i = np.nanargmax(np.where(plume, Teq, -1))
    k = np.nanargmax(np.where(plume, dT, -1e9))
    st = dict(run=run_npz, afterburn=ab_npz, model='afterburn v3 (equilibrium-inert reference)', Z_st=Zst,
              OF=info.get('OF'), Pc_Pa=info.get('Pc'), Tc_cea_K=info.get('Tc_cea'), Te_cea_K=info.get('Te_cea'),
              cells_processed=info.get('cells_processed'), cells_failed=info.get('cells_failed'),
              inert_solver_clamped_cells=info.get('inert_solver_clamped_cells'),
              Teq_max_plume_K=float(Teq.flat[i]), Teq_max_x_De=float(X.flat[i]), Teq_max_r_De=float(R.flat[i]),
              dTab_max_K=float(dT.flat[k]), dTab_max_x_De=float(X.flat[k]), dTab_max_r_De=float(R.flat[k]),
              dTab_max_Z=float(D['Y'].flat[k]),
              dTab_min_K=float(np.nanmin(np.where(plume, dT, np.nan))),
              Tcfd_max_plume_K=float(np.nanmax(np.where(plume, D['T'], np.nan))),
              Tab_cfd_max_plume_K=float(np.nanmax(np.where(plume, Tab, np.nan))),
              TeqB_upper_bound_max_plume_K=float(np.nanmax(np.where(plume, TeqB, np.nan))),
              check_Teq_minus_Tinert_core_K=info.get('check_Teq_minus_Tinert_core_K'),
              gas_model_check_Tinert_minus_Tcfd_K=info.get('gas_model_check_Tinert_minus_Tcfd_K'),
              h0_exhaust_A_eq=info.get('h0_exhaust_A_eq'), h0_exhaust_A_frozen_v2=info.get('h0_exhaust_A_frozen_v2'),
              h0_exhaust_B_full=info.get('h0_exhaust_B_full'))
    for thr in (50.0, 100.0, 200.0, 300.0):
        m = plume & (dT > thr)
        st[f'x_extent_dTab_gt_{int(thr)}K_De'] = [float(X[m].min()), float(X[m].max())] if m.any() else None
    for xv in (5.0, 10.0, 20.0, 30.0, 40.0):
        j = int(np.argmin(np.abs(X[:, 0] - xv)))
        st[f'axis_{int(xv)}De'] = dict(T_cfd=float(D['T'][j, 0]), T_inert=float(Tin[j, 0]), T_eq=float(Teq[j, 0]),
                                       T_ab_cfd=float(Tab[j, 0]), Z=float(D['Y'][j, 0]))
        rad = np.where(fluid[j], dT[j], np.nan)
        st[f'radial_max_dTab_{int(xv)}De'] = float(np.nanmax(rad)) if np.isfinite(rad).any() else None
    # axis profile
    c0 = dict(x_De=X[:, 0].tolist(), Teq=Teq[:, 0].tolist(), Tinert=Tin[:, 0].tolist(), Tab_cfd=Tab[:, 0].tolist(),
              Tcfd=D['T'][:, 0].tolist(), Z=D['Y'][:, 0].tolist())
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(X[:, 0], D['T'][:, 0], 'k-', lw=0.9, label='CFD T (two-species frozen, perfect gas)')
    ax.plot(X[:, 0], Tin[:, 0], 'b--', lw=0.9, label='T_inert (exhaust equilibrium, air inert)')
    ax.plot(X[:, 0], Teq[:, 0], 'r-', lw=0.9, label='T_eq (fast chemistry, complete afterburning)')
    ax.plot(X[:, 0], Tab[:, 0], color='darkorange', ls=':', lw=1.2, label='CFD T + dT_ab')
    ax2 = ax.twinx(); ax2.plot(X[:, 0], D['Y'][:, 0], 'm--', lw=0.7); ax2.set_ylabel('Z (axis)', color='m')
    ax2.axhline(Zst, color='m', lw=0.5, ls=':')
    ax.set_xlim(-2, 45); ax.set_xlabel('x / De'); ax.set_ylabel('T on axis [K]'); ax.grid(alpha=0.3); ax.legend(fontsize=7)
    ax.set_title(f'{tag}: axis temperature with and without afterburning (fast-chemistry assumption); '
                 f'magenta dotted: Z_st', fontsize=8, loc='left')
    fn = os.path.join(outdir, f'{tag}_afterburn_axis.png'); fig.savefig(fn, bbox_inches='tight', dpi=200); plt.close(fig)
    files.append(fn)
    # radial profiles of dT_ab
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for xv, col in ((5, 'tab:blue'), (10, 'tab:green'), (20, 'tab:orange'), (30, 'tab:red'), (40, 'k')):
        j = int(np.argmin(np.abs(X[:, 0] - xv)))
        ax.plot(R[j], np.where(fluid[j], dT[j], np.nan), color=col, lw=1, label=f'x = {xv} De')
    ax.set_xlim(0, 6); ax.set_xlabel('r / De'); ax.set_ylabel('dT_ab [K]'); ax.grid(alpha=0.3); ax.legend(fontsize=7)
    ax.set_title(f'{tag}: radial afterburning temperature rise (fast chemistry)', fontsize=8, loc='left')
    fn = os.path.join(outdir, f'{tag}_afterburn_radial.png'); fig.savefig(fn, bbox_inches='tight', dpi=200); plt.close(fig)
    files.append(fn)
    json.dump(dict(stats=st, axis=c0, figures=files), open(os.path.join(outdir, f'{tag}_afterburn_stats.json'), 'w'),
              indent=1, default=float)
    print(json.dumps(st, indent=1, default=float))


if __name__ == '__main__':
    main(*sys.argv[1:5])
