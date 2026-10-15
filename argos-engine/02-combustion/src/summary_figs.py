"""Summary tables and figures (Combustion v2): thrust ceiling vs time (max-thrust runs at 15/20/25 C) and the grain
trade over the flight duty cycles.  usage: python summary_figs.py DATADIR FIGDIR
Inputs: DATADIR/engine_S230/maxthrust_*.csv, DATADIR/{dc,dc_g2,dc_g3,engine_S230}/summary_v2.json
Outputs: DATADIR/ceiling_vs_time_v2.csv/.json, DATADIR/grain_trade_v2.csv, FIGDIR/ceiling_vs_time_v2.png, FIGDIR/grain_trade_v2.png
"""
from __future__ import annotations
import glob, json, os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RESID = 0.011   # kg: NonEqTank keeps a 0.01 kg liquid residual; below this the tank is in vapour blowdown


def ceiling(datadir, figdir, sub='engine_S230', label='A1tank', tank_txt='A1 tank 2.06 L / 1.3 kg', out='ceiling_vs_time_v2'):
    fs = sorted(glob.glob(os.path.join(datadir, sub, f'maxthrust_{label}_*.csv')))
    rows = []; fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
    cols = {'15': 'tab:blue', '20': 'tab:green', '25': 'tab:red'}
    for fn in fs:
        d = pd.read_csv(fn)
        tag = os.path.basename(fn).replace(f'maxthrust_{label}_', '').replace('.csv', '')
        kind, T = tag.split('_T')
        T = T.replace('C', '')
        liq = d.m_liq > RESID
        t_liq = float(d.t[liq].iloc[-1]) if liq.any() else float('nan')
        ok = (d.F >= 0.99 * 500) & liq
        t500 = float(d.t[ok].iloc[-1]) if ok.any() else 0.0
        dl = d[liq]
        imp = float(np.trapezoid(dl.F, dl.t)) if len(dl) > 1 else float('nan')
        rows.append(dict(case=tag, tank_model=kind, T0_C=float(T), t_500N_held_s=t500, t_liquid_depletion_s=t_liq,
                         impulse_to_liquid_depletion_Ns=imp, F_ceiling_at_0s_N=float(d.F_ceiling.iloc[1]),
                         F_ceiling_at_liquid_end_N=float(dl.F_ceiling.iloc[-1]) if len(dl) else float('nan'),
                         P_tank_at_liquid_end_bar=float(dl.P_tank.iloc[-1]) / 1e5 if len(dl) else float('nan'),
                         ox_used_to_liquid_end_kg=float(np.trapezoid(dl.mox, dl.t)) if len(dl) > 1 else float('nan')))
        ls = {'eq': ':', 'neqE1e+03': '-', 'neqE1e+02': '--'}.get(kind, '-')
        c = cols.get(T, 'k')
        axs[0].plot(dl.t, dl.F_ceiling, ls, color=c, lw=1.2, label=f'{T} C, {kind}')
        axs[0].plot(dl.t, dl.F, ls, color=c, lw=0.6, alpha=0.6)
        axs[1].plot(dl.t, dl.P_tank / 1e5, ls, color=c, lw=1.2)
        axs[1].plot(dl.t, dl.Pc / 1e5, ls, color=c, lw=0.7, alpha=0.7)
        axs[2].plot(dl.t, dl.T_tank - 273.15, ls, color=c, lw=1.2)
    axs[0].axhline(500, color='k', lw=0.6)
    axs[0].set_xlabel('t [s] (500 N commanded from t = 0)'); axs[0].set_ylabel('thrust ceiling (thick) and thrust (thin) [N]')
    axs[0].set_title(f'Thrust ceiling vs time, {tank_txt}, v2 grain S230\n(ceiling = min(stroke, dP/Pc >= 0.25); dotted eq, solid E 1000, dashed E 100)', fontsize=8)
    axs[0].legend(fontsize=6.5, ncol=3); axs[0].grid(alpha=0.3)
    axs[1].set_xlabel('t [s]'); axs[1].set_ylabel('P_tank (thick), Pc (thin) [bar]'); axs[1].grid(alpha=0.3)
    axs[2].set_xlabel('t [s]'); axs[2].set_ylabel('liquid / tank temperature [C]'); axs[2].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(figdir, out + '.png'), dpi=130); plt.close(fig)
    pd.DataFrame(rows).to_csv(os.path.join(datadir, out + '.csv'), index=False, float_format='%.4g')
    return rows


def grain_trade(datadir, figdir):
    rows = []
    for sub, var in (('dc', 'v1 helix L200'), ('dc_g2', 'S200'), ('dc_g3', None), ('engine_S230', None)):
        fn = os.path.join(datadir, sub, 'summary_v2.json')
        if not os.path.exists(fn):
            continue
        for k, r in json.load(open(fn)).items():
            if not isinstance(r, dict) or 'burn_s' not in r:
                continue
            if 'neqE1e+03' not in k and 'ground' not in k:
                continue
            dc = k.split('_')[0]
            parts = dc.split('-')
            base = '-'.join(parts[:2]); v = var or ('S230 (v2)' if 'S230' in dc else 'S260' if 'S260' in dc else '?')
            if var is None and len(parts) < 3:
                continue
            if var == 'S200' and 'G2' not in dc:
                continue
            reg = float(k.split('reg')[1])
            rows.append(dict(variant=v, duty_cycle=base, regression_scale=reg, burn_s=r['burn_s'], impulse_Ns=r['impulse_Ns'],
                             N2O_used_kg=r['ox_used_kg'], fuel_used_kg=r['fuel_used_kg'], OF_mean=r['OF_mean'],
                             Isp_mean_s=r['Isp_mean_s'], web_end_mm=r['w_min_end_mm'], burnthrough_s=r['burnthrough_s'],
                             liquid_N2O_left_kg=r['m_liq_end_kg'], min_ceiling_N=r['min_F_ceiling_N'], min_dP_over_Pc=r['dpc_min'],
                             tracking_rms_N=r['tracking_rms_N']))
    df = pd.DataFrame(rows).sort_values(['duty_cycle', 'variant', 'regression_scale'])
    with open(os.path.join(datadir, 'grain_trade_v2.csv'), 'w') as f:
        f.write('# Grain trade over the gnc.json v1 duty cycles (SIM grain_q1d v2, non-equilibrium tank E 1000 for flight, '
                'ASSUMED ground tank for C/D). regression_scale multiplies the ASSUMED law r = a G^0.5 (band 0.6-1.5). '
                'Negative web_end = burn-through. SI.\n')
        df.to_csv(f, index=False, float_format='%.4g')
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    nom = df[df.regression_scale == 1.0]
    order = ['v1 helix L200', 'S200', 'S230 (v2)', 'S260']
    for ax, col, lab in ((axs[0], 'N2O_used_kg', 'N2O used [kg]'), (axs[1], 'Isp_mean_s', 'mean delivered Isp [s]'),
                         (axs[2], 'web_end_mm', 'minimum web at end [mm] (x1.0 bar, x1.5 marker)')):
        dcs = ['DC-A1', 'DC-A2', 'DC-B1', 'DC-B2']
        w = 0.2
        for i, v in enumerate(order):
            vals = [nom[(nom.variant == v) & (nom.duty_cycle == d)][col].mean() for d in dcs]
            ax.bar(np.arange(len(dcs)) + (i - 1.5) * w, vals, w, label=v)
            if col == 'web_end_mm':
                hi = df[(df.regression_scale == 1.5) & (df.variant == v)]
                vv = [hi[hi.duty_cycle == d][col].mean() for d in dcs]
                ax.plot(np.arange(len(dcs)) + (i - 1.5) * w, vv, 'kv', ms=4)
        ax.set_xticks(range(len(dcs))); ax.set_xticklabels(dcs); ax.set_ylabel(lab); ax.grid(alpha=0.3, axis='y')
    axs[2].axhline(0, color='k', lw=0.8); axs[0].legend(fontsize=8)
    fig.suptitle('Grain trade (nominal regression; x1.5 web as triangles)', fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(figdir, 'grain_trade_v2.png'), dpi=130); plt.close(fig)
    return df


if __name__ == '__main__':
    datadir, figdir = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == 'BL':
        r = ceiling(datadir, figdir, sub='engine_S230_BL', label='BLtank',
                    tank_txt='baseline tank 3.17 L / 2.00 kg (lead 2026-10-12)', out='ceiling_vs_time_BLtank_v2')
        for x in r:
            print(x)
        sys.exit(0)
    r = ceiling(datadir, figdir)
    for x in r:
        print(x)
    df = grain_trade(datadir, figdir)
    print(df.to_string())
