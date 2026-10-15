"""Nozzle expansion-ratio trade, separation at the throttle points and a side-load bound (Combustion v2, task 5).

1. Operating points (20 C saturated tank, initial port) for the v1 helical grain and the v2 straight-port candidates.
2. For eps 2.0 (new), 1.9 / 1.8 (throat eroded): pe/pa, exit Mach, Summerfield (pe/pa < 0.4) and Schmucker
   (pe/pa < (1.88 Me - 1)^-0.64) separation flags, eps_sep, Isp_SL with and without separation credit.
3. Isp penalty of eps 2 at maximum thrust versus the sea-level optimum eps (pe = pa) and versus eps 1.5/2.5/3.0.
4. Side-load upper bound when separation sits inside the nozzle: half the circumference attached, half separated
   (wall pressure = pa); F_side <= int_{x_sep}^{x_e} (pa - p_w(x)) 2 r(x) cos(theta_w) dx with the isentropic
   wall pressure of the equilibrium-shifting CEA expansion. This is a geometric bound (DERIVED), not a model of
   the dynamic side load (Schmucker / Dumnov / Pekkari models need calibration data that do not exist here).
Outputs: data/v2/nozzle_perf_v2.{csv,json}; figs/v2/nozzle_eps_trade_v2.png.
usage: python nozzle_perf.py OUTDIR FIGDIR
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grain_q1d as Q
import injector as INJ
from run_dc import _FixedTank

PA = 101325.0
FRACS = (1.0, 0.75, 0.5, 0.4, 0.25, 0.20, 0.15, 0.125)
GRAINS = Q.VARIANTS
HERE = os.path.dirname(os.path.abspath(__file__))


def contour():
    d = np.genfromtxt(os.path.join(HERE, '..', 'data', 'nozzle_contour_v1.csv'), delimiter=',', skip_header=2,
                      usecols=(1, 2))
    x, r = d[:, 0], d[:, 1]
    m = x >= 0
    return x[m], r[m]


def op_points(grain_cfg):
    T = 293.15; pv = INJ.psat(T)
    e = Q.Engine(_FixedTank(pv, T), cfg=dict(Q.V, **grain_cfg))
    cei = e.ceiling(); rows = []
    for fr in FRACS:
        h, _ = e.lift_for_thrust(500 * fr, cei=cei); s = e.steady(h)
        rows.append(dict(frac=fr, F=s['F'], Pc=s['Pc'], OF=s['OF'], mox=s['mox'], mf=s['mf'], Isp=s['Isp']))
    return e, rows


def wall_for_eps(xs, rs, eps_e):
    """Divergent wall for exit area ratio eps_e: the v1 contour (eps 2) is cut or extended along its last cone."""
    Rt = rs[0]
    Re = Rt * math.sqrt(eps_e)
    if Re <= rs[-1] + 1e-12:
        m = rs <= Re + 1e-12
        return xs[m], rs[m]
    slope = (rs[-1] - rs[-2]) / (xs[-1] - xs[-2])
    xe = xs[-1] + (Re - rs[-1]) / slope
    xa = np.linspace(xs[-1], xe, 40)[1:]
    return np.concatenate([xs, xa]), np.concatenate([rs, rs[-1] + slope * (xa - xs[-1])])


def side_load_bound(P, Pc, OF, eps_e, eps_sep, xs, rs, Rt=None):
    """Upper bound of the lateral force for a fully asymmetric separation between eps_sep and the exit.
    Rt: effective throat radius (eroded throat: Rt = Re / sqrt(eps_e) with the same divergent wall)."""
    Rt = rs[0] if Rt is None else Rt
    eps_x = (rs / Rt) ** 2
    m = (eps_x >= eps_sep) & (eps_x <= eps_e * 1.0001)
    if m.sum() < 2:
        return 0.0
    xx, rr, ee = xs[m], rs[m], eps_x[m]
    pw = np.array([P.pe_pc(Pc, OF, e) * Pc for e in ee])
    dr = np.gradient(rr, xx); cth = 1 / np.sqrt(1 + dr ** 2)
    f = np.clip(PA - pw, 0, None) * 2 * rr * cth
    return float(np.trapezoid(f, xx))


def main(outdir, figdir):
    xs, rs = contour()
    out = dict(version='v2', date='2026-10-12', grains={}, eps_trade={}, notes=[])
    rows_all = []
    for gname, gcfg in GRAINS.items():
        e, ops = op_points(gcfg)
        P = e.P
        for o in ops:
            for eps in (3.0, 2.5, 2.0, 1.9, 1.8):
                pe = P.pe_pc(o['Pc'], o['OF'], eps) * o['Pc']
                Me = P.mach(o['Pc'], o['OF'], eps)
                sch = (1.88 * Me - 1) ** -0.64
                cf, es, pepa = P.cf_amb(o['Pc'], o['OF'], eps)
                cf_nosep = P.cf_vac(o['Pc'], o['OF'], eps) - eps * PA / o['Pc']
                cs = P.cstar(o['Pc'], o['OF'])
                r = dict(grain=gname, frac=o['frac'], Pc_Pa=o['Pc'], OF=o['OF'], eps=eps, pe_over_pa=pe / PA, Me=Me,
                         schmucker_psep_over_pa=sch, summerfield_sep=bool(pe / PA < 0.4), schmucker_sep=bool(pe / PA < sch),
                         eps_sep=es if es else '', Cf_ideal_sep=cf, Cf_ideal_nosep=cf_nosep,
                         Isp_ideal_SL_s=cf * cs / 9.80665, cstar_ideal=cs)
                if eps >= 2.0:      # new nozzle with exit ratio eps (v1 wall cut/extended along its cone)
                    xw, rw = wall_for_eps(xs, rs, eps); Rt_eff = rs[0]
                else:               # eps 2 nozzle with an eroded throat: same wall, larger throat
                    xw, rw = xs, rs; Rt_eff = rs[-1] / math.sqrt(eps)
                r['side_load_bound_N'] = side_load_bound(P, o['Pc'], o['OF'], eps, es, xw, rw, Rt_eff) if es else 0.0
                r['F_N'] = o['F'] if eps == 2.0 else ''
                rows_all.append(r)
        out['grains'][gname] = dict(cfg=gcfg, ops=ops, ceiling_N=e.ceiling()['F'])
    # eps trade at the max-thrust and floor points of each grain
    for gname, gcfg in GRAINS.items():
        e, ops = op_points(gcfg); P = e.P
        tr = []
        for o in (ops[0], ops[2], ops[5], ops[-1]):
            cs = P.cstar(o['Pc'], o['OF'])
            row = dict(frac=o['frac'], Pc_Pa=o['Pc'], OF=o['OF'])
            best = (0, None)
            for eps in np.round(np.arange(1.2, 4.01, 0.05), 3):
                cf, es, _ = P.cf_amb(o['Pc'], o['OF'], eps)
                if cf > best[0]:
                    best = (cf, eps)
                row[f'Isp_SL_eps{eps:.2f}'] = cf * cs / 9.80665
            row['eps_opt_SL'] = best[1]; row['Isp_SL_opt'] = best[0] * cs / 9.80665
            row['Isp_SL_eps2'] = row['Isp_SL_eps2.00']
            row['penalty_eps2_vs_opt_pct'] = 100 * (1 - row['Isp_SL_eps2'] / row['Isp_SL_opt'])
            tr.append(row)
        out['eps_trade'][gname] = tr
    fn = os.path.join(outdir, 'nozzle_perf_v2.csv')
    keys = list(rows_all[0].keys())
    with open(fn, 'w', newline='') as f:
        f.write('# Separation and side-load bound at the throttle points (20 C saturated tank, initial port). Ideal CEA '
                'shifting expansion (perf_tables v1 grid); Schmucker and Summerfield criteria; side-load bound = half '
                'attached / half separated (DERIVED upper bound). eps 1.9/1.8 = throat eroded. SIM/DERIVED. SI.\n')
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows_all)
    out['separation_rows_csv'] = fn
    out['notes'] = [
        'Separation flags use the ideal (CEA shifting) wall pressure; eta_cf losses and boundary-layer displacement are not '
        'included, both of which move separation slightly downstream (pe slightly higher).',
        'Side-load bound: lateral pressure imbalance over the wall band between eps_sep and the exit with one half of the '
        'circumference attached and the other at ambient pressure; a dynamic load factor is not applied.',
    ]
    json.dump(out, open(os.path.join(outdir, 'nozzle_perf_v2.json'), 'w'), indent=1, default=float)
    # figure: Isp_SL vs eps for 4 throttle points (v1 grain) + separation map
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
    ax = axs[0]
    for gname, ls in (('v1_helix_L200', '-'), ('v2_S230_straight_L230', '--')):
        for row, c in zip(out['eps_trade'][gname], ('tab:red', 'tab:orange', 'tab:green', 'tab:blue')):
            ee = [float(k.split('eps')[1].split('_')[0]) for k in row if k.startswith('Isp_SL_eps') and k != 'Isp_SL_eps2']
            ii = [row[k] for k in row if k.startswith('Isp_SL_eps') and k != 'Isp_SL_eps2']
            ax.plot(ee, ii, ls, color=c, label=f'{gname.split("_")[0]} {row["frac"]*100:.1f} % (Pc {row["Pc_Pa"]/1e5:.1f} bar, O/F {row["OF"]:.1f})')
    ax.axvline(2.0, color='k', lw=0.8)
    ax.set_xlabel('expansion ratio eps'); ax.set_ylabel('ideal sea-level Isp, Schmucker separation [s]')
    ax.set_title('Expansion-ratio trade (ideal, before eta_c*, eta_cf)', fontsize=9)
    ax.grid(alpha=0.3); ax.legend(fontsize=6.5)
    ax = axs[1]
    for gname, mk in (('v1_helix_L200', 'o'), ('v2_S230_straight_L230', 's')):
        for eps, c in ((2.0, 'k'), (1.9, '0.4'), (1.8, '0.7')):
            rr = [r for r in rows_all if r['grain'] == gname and r['eps'] == eps]
            ax.plot([r['frac'] * 100 for r in rr], [r['pe_over_pa'] for r in rr], mk + '-', color=c, ms=4,
                    label=f'{gname.split("_")[0]} pe/pa, eps {eps}')
        rr = [r for r in rows_all if r['grain'] == gname and r['eps'] == 2.0]
        ax.plot([r['frac'] * 100 for r in rr], [r['schmucker_psep_over_pa'] for r in rr], mk + ':', color='tab:red', ms=4,
                label=f'{gname.split("_")[0]} Schmucker psep/pa (eps 2)')
    ax.axhline(0.4, color='tab:purple', lw=0.8, ls='--'); ax.text(60, 0.41, 'Summerfield 0.4', fontsize=8, color='tab:purple')
    ax.set_xlabel('thrust [% of 500 N]'); ax.set_ylabel('p / p_a')
    ax.set_title('Exit pressure vs separation pressure (separation where pe/pa < criterion)', fontsize=9)
    ax.grid(alpha=0.3); ax.legend(fontsize=6.5)
    fig.tight_layout(); f2 = os.path.join(figdir, 'nozzle_eps_trade_v2.png'); fig.savefig(f2, dpi=130); plt.close(fig)
    return out, rows_all


if __name__ == '__main__':
    o, rows = main(sys.argv[1], sys.argv[2])
    for r in rows:
        if r['eps'] == 2.0 or (r['eps_sep'] != '' and r['frac'] >= 0.125):
            print(r['grain'][:4], r['frac'], round(r['Pc_Pa'] / 1e5, 2), round(r['OF'], 2), r['eps'], round(r['pe_over_pa'], 3),
                  round(r['schmucker_psep_over_pa'], 3), r['summerfield_sep'], r['schmucker_sep'], r['eps_sep'] and round(r['eps_sep'], 3),
                  round(r['Isp_ideal_SL_s'], 1), round(r['side_load_bound_N'], 2))
    for g, tr in o['eps_trade'].items():
        for row in tr:
            print(g, row['frac'], round(row['OF'], 2), 'eps_opt', row['eps_opt_SL'], round(row['Isp_SL_opt'], 1), 'eps2', round(row['Isp_SL_eps2'], 1),
                  'pen %', round(row['penalty_eps2_vs_opt_pct'], 2), 'eps1.5', round(row['Isp_SL_eps1.50'], 1), 'eps3', round(row['Isp_SL_eps3.00'], 1))
