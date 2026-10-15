"""Plume CFD validation (Combustion / 05-plume-cfd v2).

Collects every available run (own solver plume2s and OpenFOAM rhoCentralFoam mapped onto the own grid), extracts the
comparison quantities and writes:
  results/key_results_v2.csv          one row per run: thrust, mass flow, Mach disk, shock cells, core length, ...
  results/centreline_<run>_v2.csv     axis profiles x/De, M, p/pa, T, Z, u on a common x grid
  results/validation_v2.json          grid convergence (Roache GCI), code-to-code, single-gas error, 1-D thrust,
                                      Prandtl-Pack / Tam shock-cell spacing, Lewis-Carlson Mach-disk location
  figs/validation_*.png
usage: python validate_plume.py OUTDIR
Quantities and methods
  Mach disk: strongest single-cell drop of the axis Mach number from > 1 to < 1 within 0 < x/De < 8 (v1 searched only
    upstream of the first pressure peak and missed the disk behind the weak exit-lip compression: fixed here).
  Shock cells (v2 primary): axis Mach maxima (3-point smoothed) downstream of the Mach disk with prominence > 0.15;
    spacing_first = 2nd - 1st maximum, spacing_mean_3 = (4th - 1st)/3. The v1 metric (axis pressure maxima, prominence
    > 0.05 p_a) is kept in the tables but picks reflected-shock wiggles right behind the disk on the medium grid.
  Thrust: solver exit-plane integral; for OpenFOAM fields mapped on the own grid the same integral is evaluated from
    the mapped exit-column fields (thrust_exit_fields_N) because the mapped files carry no solver integral.
  1-D thrust: same calibrated perfect gas as the CFD (gamma_eff, R_eff, T0, Pc), ideal conical nozzle with divergence
    factor lambda = (1 + cos 15 deg)/2; no boundary layer in either.
  Prandtl-Pack (Pack 1950) / Tam & Tanna (1982) vortex-sheet spacing: L_s = 1.306 sqrt(M_j^2 - 1) D_j with M_j, D_j the
    fully expanded jet Mach number and diameter; derived for moderately imperfect expansion (no Mach disk).
  Lewis & Carlson (AIAA J 2(4) 1964) Mach-disk location: x_md/De = 0.69 Me sqrt(gamma pe/pa) (LITERATURE, quoted from
    memory: TO-VERIFY against the paper).
  GCI: Roache (1998), three levels with refinement ratio 2, Fs = 1.25.
v2.1 (2026-10-12): levels and sensitivities at the same physical time (GCI at 3.25 ms: fine run, medium continued to
  3.25 ms, coarse frame at 3.25 ms; sensitivities at 3.0 ms against the coarse frame at 3.0 ms); temporal bands from the
  frames (the plume is unsteady); a grid difference is called resolved only if it exceeds 2 sigma of the temporal
  scatter; oscillatory GCI bound 3 x max deviation; GCI also with the observed order capped at 2; the v2.1 S230
  operating-point run (own_c_2s_v2op) against its own 1-D reference. Adds figs/validation_unsteady_v2.png and
  figs/validation_v2op_v2.png.
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import post_plume as PP

PA, TA = 101325.0, 288.15
ROOT = os.path.abspath(os.path.join(HERE, '..'))
RUNS = [  # name, kind, path, description
    ('own_c_2s_rans', 'own', 'ownruns/c_2s_100/final.npz', 'own, coarse (20k), two-species, mixing-length RANS, t 4 ms'),
    ('own_m_2s_rans', 'own', 'ownruns/m_2s_100/final.npz', 'own, medium (80k), two-species, mixing-length RANS'),
    ('own_f_2s_rans', 'own', 'ownruns/f_2s_100/final.npz', 'own, fine (320k), two-species, mixing-length RANS'),
    ('own_c_1s_rans', 'own', 'ownruns/c_1s_100/final.npz', 'own, coarse, single gas (exhaust everywhere), RANS'),
    ('own_c_1s_inv', 'own', 'ownruns/c_1s_inv_100/final.npz', 'own, coarse, single gas, inviscid, t 1 ms'),
    ('own_c_2s_nu05', 'own', 'ownruns/c_2s_100_nu05/final.npz', 'own, coarse, two-species, eddy viscosity x0.5'),
    ('own_c_2s_nu2', 'own', 'ownruns/c_2s_100_nu2/final.npz', 'own, coarse, two-species, eddy viscosity x2'),
    ('own_c_2s_nophi', 'own', 'ownruns/c_2s_100_nophi/final.npz', 'own, coarse, two-species, no compressibility factor'),
    # v2.1 (2026-10-12): time-matched levels. The coarse frames show an unsteady plume (Mach-disk cell, first Mach
    # maximum, axis T at 10 De change between 3.0, 3.25 and 4.0 ms), so levels and sensitivities are compared at the
    # same physical time and a temporal band is reported per level.
    ('own_c_2s_rans_t3', 'own', 'ownruns/c_2s_100/snap_t3p00ms.npz', 'own, coarse, two-species RANS, frame at t 3.0 ms (time-matched reference of the 3 ms runs)'),
    ('own_c_2s_rans_t3p25', 'own', 'ownruns/c_2s_100/snap_t3p25ms.npz', 'own, coarse, two-species RANS, frame at t 3.25 ms (GCI level)'),
    ('own_m_2s_rans_t3p25', 'own', 'ownruns/m_2s_100_c325/final.npz', 'own, medium, continued 3.0 -> 3.25 ms (GCI level)'),
    ('own_c_2s_v2op', 'own', 'ownruns/c_2s_100_v2op/final.npz', 'own, coarse, two-species RANS at the combustion.json v2.1 S230 point (O/F 10.435, T0 2757 K), t 4 ms'),
    ('of_c_1s_inv', 'of', 'ownruns/of_c100_inv_t1ms.npz', 'OpenFOAM rhoCentralFoam, coarse wedge (17k), single gas, inviscid, t 1 ms'),
    ('of_c_1s_sst', 'of', 'ownruns/of_c100_sst_t1p15ms.npz', 'OpenFOAM rhoCentralFoam, coarse wedge, single gas, k-omega SST, t 1.15 ms (stopped at the 2 h limit)'),
]
XGRID = np.round(np.arange(-1.0, 45.0001, 0.05), 3)


def mach_disk(D, xmax=8.0):
    c = PP.centreline(D)
    x, M = c['x_De'], c['M']
    sel = np.where((x > 0.0) & (x < xmax))[0]
    best = None
    for k in sel[:-1]:
        if M[k] > 1.0 and M[k + 1] < 1.0:
            drop = M[k] - M[k + 1]
            if best is None or drop > best[0]:
                best = (drop, k)
    if best is None:
        return None
    k = best[1]
    out = dict(x_De=float(0.5 * (x[k] + x[k + 1])), M_before=float(M[k]), M_after=float(M[k + 1]),
               p_before_pa=float(c['p_pa'][k]), dx_cell_De=float(x[k + 1] - x[k]))
    # radius: contiguous subsonic cells from the axis in the first column behind the disk
    for di in (1, 2, 3):
        col = D['M'][k + 1 + di - 1, :]
        js = np.where(col >= 1.0)[0]
        if len(js) and js[0] > 0:
            out['r_De'] = float(D['rc'][k + di, js[0] - 1] / D['De'])
            break
    return out


def cells(D, x_from, xmax=40.0):
    c = PP.centreline(D)
    x, p = c['x_De'], c['p_pa']
    sel = (x > x_from) & (x < xmax)
    xs, ps = x[sel], np.convolve(p[sel], np.ones(3) / 3, mode='same')
    pk = []
    for i in range(2, len(ps) - 2):
        if ps[i] > ps[i - 1] and ps[i] >= ps[i + 1]:
            lo = max(0, i - 40); hi = min(len(ps), i + 40)
            prom = ps[i] - max(ps[lo:i].min(), ps[i:hi].min())
            if prom > 0.05:
                pk.append(float(xs[i]))
    return pk


def axis_at(c, key, xv):
    return float(np.interp(xv, c['x_De'], c[key]))


def core_length(c, level):
    x, Y = c['x_De'], c['Y']
    m = np.where((x > 0) & (Y < level))[0]
    return float(x[m[0]]) if len(m) else float('nan')


def cells_mach(D, x_from, xmax=30.0, prom_min=0.15):
    """v2 robust shock-cell metric: local maxima of the axis Mach number (3-point smoothed) downstream of the Mach
    disk with a prominence > prom_min in Mach number (the pressure-peak metric picks up the reflected-shock wiggles
    right behind the disk on finer grids)."""
    c = PP.centreline(D)
    x, M = c['x_De'], c['M']
    sel = (x > x_from) & (x < xmax)
    xs, Ms = x[sel], np.convolve(M[sel], np.ones(3) / 3, mode='same')
    pk = []
    for i in range(2, len(Ms) - 2):
        if Ms[i] > Ms[i - 1] and Ms[i] >= Ms[i + 1]:
            lo = max(0, i - 60); hi = min(len(Ms), i + 60)
            prom = Ms[i] - max(Ms[lo:i].min(), Ms[i:hi].min())
            if prom > prom_min:
                pk.append(float(xs[i]))
    return pk


def exit_plane_integrals(D):
    """Thrust (momentum + pressure) and mass flow through the last nozzle cell column from the fields (works for the
    own runs and for OpenFOAM fields mapped on the own grid, whose meta has no thrust)."""
    # v2.1: the last cell column (i = Nn-1) lies between node columns Nn-1 and Nn (= exit plane). The integral is taken
    # on the cell-centre plane (radii averaged between the two node columns) and the impulse is carried to the exit
    # plane with the quasi-1-D relation dI = p dA. (v2.0 used the node radii of column Nn-1, one full cell upstream,
    # and under-read the coarse-grid thrust by 2.6 %: kept as evidence in the REPORT.)
    g = D['meta']['grid']; i = g['Nn'] - 1; jc = g['jc']
    I = mdot = Ae = 0.0
    for j in range(jc):
        rc0 = 0.5 * float(D['R'][i, j] + D['R'][i + 1, j]); rc1 = 0.5 * float(D['R'][i, j + 1] + D['R'][i + 1, j + 1])
        re0 = float(D['R'][i + 1, j]); re1 = float(D['R'][i + 1, j + 1])
        dAc = math.pi * (rc1 ** 2 - rc0 ** 2); dAe = math.pi * (re1 ** 2 - re0 ** 2)
        rho, u, p = float(D['rho'][i, j]), float(D['u'][i, j]), float(D['p'][i, j])
        if not all(np.isfinite([rho, u, p])):
            return float('nan'), float('nan')
        I += (rho * u * u + p) * dAc + p * (dAe - dAc); mdot += rho * u * dAc; Ae += dAe
    return I - PA * Ae, mdot


def half_radius(D, xv, Yb=0.5):
    i = int(np.argmin(np.abs(D['xc'][:, 0] / D['De'] - xv)))
    col = D['Y'][i]; r = D['rc'][i] / D['De']
    js = np.where(col < Yb)[0]
    return float(r[js[0]]) if len(js) else float('nan')


def one_d_thrust(gas, De, Rt, lam=(1 + math.cos(math.radians(15))) / 2):
    g, R, T0, p0 = gas['gamma_e'], gas['R_e'], gas['T0'], gas['p0']
    At = math.pi * Rt ** 2; Ae = math.pi * (De / 2) ** 2; eps = Ae / At
    from scipy.optimize import brentq
    f = lambda M: (1 / M) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * M * M)) ** ((g + 1) / (2 * (g - 1))) - eps
    Me = brentq(f, 1.0001, 6)
    pe = p0 * (1 + (g - 1) / 2 * Me ** 2) ** (-g / (g - 1))
    Te = T0 / (1 + (g - 1) / 2 * Me ** 2)
    ue = Me * math.sqrt(g * R * Te)
    Gam = math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
    mdot = p0 * At * Gam / math.sqrt(R * T0)
    F_ideal = mdot * ue + (pe - PA) * Ae
    F_lam = lam * mdot * ue + (pe - PA) * Ae
    # fully expanded jet
    Mj = math.sqrt(2 / (g - 1) * ((p0 / PA) ** ((g - 1) / g) - 1))
    ar = lambda M: (1 / M) * ((2 / (g + 1)) * (1 + (g - 1) / 2 * M * M)) ** ((g + 1) / (2 * (g - 1)))
    Dj = De * math.sqrt(ar(Mj) / eps)
    Ls_pp = 1.306 * math.sqrt(Mj ** 2 - 1) * Dj
    x_md_lc = 0.69 * Me * math.sqrt(g * pe / PA) * De
    return dict(Me=Me, pe_Pa=pe, pe_over_pa=pe / PA, ue=ue, mdot=mdot, F_ideal_N=F_ideal, F_ideal_lambda_N=F_lam, lam=lam,
                Mj=Mj, Dj_over_De=Dj / De, Ls_prandtl_pack_tam_De=Ls_pp / De, x_md_lewis_carlson_De=x_md_lc / De)


def gci(f1, f2, f3, r=2.0, Fs=1.25):
    """f1 fine, f2 medium, f3 coarse."""
    e32 = f3 - f2; e21 = f2 - f1
    if any(not np.isfinite(v) for v in (f1, f2, f3)):
        return None
    if abs(e21) < 1e-14:
        return dict(p=float('nan'), gci_fine_pct=0.0, f_ext=f1, note='fine = medium')
    ratio = e32 / e21
    if ratio <= 0:
        # oscillatory convergence: bound = 3 x the larger level difference (v2.1: v2.0 commented Fs = 3 but applied the
        # monotone Fs 1.25; fixed and kept as evidence)
        unc = 3.0 * max(abs(e21), abs(e32)) / abs(f1) * 100
        return dict(p=float('nan'), gci_fine_pct=unc, f_ext=float('nan'), note='oscillatory: 3 x max-deviation bound')
    p = math.log(ratio) / math.log(r)
    if p < 0.5:
        # v2.1a (2026-10-12): monotone level differences that do not shrink (p < 0.5, incl. p < 0 = growing differences)
        # show no observed convergence; the Richardson GCI is then meaningless (negative for p < 0: the first v2.1 run
        # reported -0.77 % for the thrust). Bound = 3 x the larger level difference, as for oscillatory data.
        unc = 3.0 * max(abs(e21), abs(e32)) / abs(f1) * 100
        return dict(p=p, gci_fine_pct=unc, f_ext=float('nan'),
                    note='monotone without observed convergence (p < 0.5): 3 x max-deviation bound')
    f_ext = f1 - e21 / (r ** p - 1)          # Richardson: f1 + (f1 - f2)/(r^p - 1)
    g = Fs * abs(e21 / f1) / (r ** p - 1) * 100
    # v2.1: observed order above the formal order (2, MUSCL; lower with the limiter) is not credited: the GCI is also
    # given with p capped at 2 (larger, conservative); p < 0.5 or p > 4 flags 'asymptotic range not shown'
    p_c = min(p, 2.0)
    g_c = Fs * abs(e21 / f1) / (r ** p_c - 1) * 100
    note = 'monotone' + ('' if 0.5 <= p <= 4.0 else ' (observed order outside 0.5-4: asymptotic range not shown)')
    return dict(p=p, gci_fine_pct=g, gci_fine_pct_p_capped_2=g_c, f_ext=f_ext, note=note)


def ensure_openfoam(outnpz):
    """Map the OpenFOAM cases onto the own coarse grid (of_post.py) if not done yet."""
    import subprocess
    jobs = [(os.path.join(ROOT, 'runs', 'of_c100_inv'), 1.0e-3, os.path.join(ROOT, 'ownruns', 'of_c100_inv_t1ms.npz')),
            (os.path.join(ROOT, 'runs', 'of_c100_sst'), 1.15e-3, os.path.join(ROOT, 'ownruns', 'of_c100_sst_t1p15ms.npz'))]
    for case, t, fn in jobs:
        if not os.path.exists(fn) and os.path.isdir(case):
            subprocess.run([sys.executable, os.path.join(HERE, 'of_post.py'), case, str(t), '0.5', fn], check=False)


def analyse(name, kind, path, desc):
    fn = os.path.join(ROOT, path)
    if not os.path.exists(fn):
        return None, None
    D = PP.load_own(fn)
    return row_from(name, desc, D)


def frame_D(run_rel, k, grid_from=None):
    """v2.1: a frame of an own run as an analysis dict (grid/meta from final.npz of grid_from or the run itself, fields
    from frame_NNNN.npz, meta t / thrust / mdot interpolated from history.csv at the frame time). None if missing."""
    run = os.path.join(ROOT, run_rel)
    ffn = os.path.join(run, f'frame_{k:04d}.npz')
    gfn = os.path.join(ROOT, grid_from or run_rel, 'final.npz')
    if not (os.path.exists(ffn) and os.path.exists(gfn)):
        return None
    f = np.load(gfn, allow_pickle=False); fr = np.load(ffn, allow_pickle=False)
    D = {key: f[key] for key in ('xc', 'rc', 'X', 'R', 'region')}
    D.update({key: fr[key] for key in ('rho', 'p', 'T', 'Y', 'M', 'u', 'v')})
    meta = json.loads(str(f['meta'])); t = float(fr['t']); meta['t'] = t
    hfn = os.path.join(run, 'history.csv')
    if os.path.exists(hfn):
        rows = list(csv.DictReader(open(hfn)))
        th = np.array([float(r['t_s']) for r in rows])
        for key, col in (('thrust_exit', 'thrust_exit_N'), ('mdot_exit', 'mdot_exit_kgs'), ('mdot_throat', 'mdot_throat_kgs')):
            meta[key] = float(np.interp(t, th, np.array([float(r[col]) for r in rows])))
    D['meta'] = meta; D['De'] = meta['grid']['De']; D['Nn'] = meta['grid']['Nn']
    return D


def row_from(name, desc, D):
    m = D['meta']
    c = PP.centreline(D)
    md = mach_disk(D)
    pk = cells(D, md['x_De'] if md else 0.3)
    mk = cells_mach(D, (md['x_De'] + 0.5) if md else 0.5)
    Ff, mf = exit_plane_integrals(D)
    xa = c['x_De']
    Mmax_pre = float(np.nanmax(c['M'][(xa > 0) & (xa < md['x_De'])])) if md else float('nan')
    gas = m['gas'] if 'gas' in m and isinstance(m['gas'], dict) and 'gamma_e' in m['gas'] else None
    row = dict(run=name, description=desc, t_ms=m['t'] * 1e3, level=m.get('level'), cells=m['grid']['cells'] if 'cells' in m['grid'] else '',
               thrust_exit_N=m['thrust_exit'], mdot_exit_kg_s=m['mdot_exit'], mdot_throat_kg_s=m['mdot_throat'],
               thrust_exit_fields_N=Ff, mdot_exit_fields_kg_s=mf,
               x_mach_disk_De=md['x_De'] if md else float('nan'), r_mach_disk_De=md.get('r_De', float('nan')) if md else float('nan'),
               dx_axis_at_md_De=md['dx_cell_De'] if md else float('nan'),
               M_before_disk=md['M_before'] if md else float('nan'), M_max_before_disk=Mmax_pre,
               machpk1_x_De=mk[0] if len(mk) > 0 else float('nan'), machpk2_x_De=mk[1] if len(mk) > 1 else float('nan'),
               machpk3_x_De=mk[2] if len(mk) > 2 else float('nan'), machpk4_x_De=mk[3] if len(mk) > 3 else float('nan'),
               spacing_first_De=(mk[1] - mk[0]) if len(mk) > 1 else float('nan'),
               spacing_mean_3_De=((mk[3] - mk[0]) / 3) if len(mk) > 3 else float('nan'),
               peak1_x_De=pk[0] if len(pk) > 0 else float('nan'), peak2_x_De=pk[1] if len(pk) > 1 else float('nan'),
               peak3_x_De=pk[2] if len(pk) > 2 else float('nan'), peak4_x_De=pk[3] if len(pk) > 3 else float('nan'),
               cell_spacing_mean_1_4_De=float(np.mean(np.diff(pk[:4]))) if len(pk) >= 4 else float('nan'),
               n_cells_to_40De=len(pk),
               core_length_Z095_De=core_length(c, 0.95), Z_axis_0p5_at_De=core_length(c, 0.5),
               T_axis_10De_K=axis_at(c, 'T', 10.0), T_axis_20De_K=axis_at(c, 'T', 20.0), T_axis_40De_K=axis_at(c, 'T', 40.0),
               u_axis_20De=axis_at(c, 'u', 20.0), Z_axis_20De=axis_at(c, 'Y', 20.0), Z_axis_40De=axis_at(c, 'Y', 40.0),
               r_half_Z_10De=half_radius(D, 10.0), r_half_Z_20De=half_radius(D, 20.0), r_half_Z_30De=half_radius(D, 30.0))
    prof = {k: np.interp(XGRID, c['x_De'], c[k], left=np.nan, right=np.nan) for k in ('M', 'p_pa', 'T', 'Y', 'u')}
    return row, dict(D=D, c=c, prof=prof, md=md, peaks=pk, gas=gas)


def main(outdir):
    rdir = os.path.join(outdir, 'results'); fdir = os.path.join(outdir, 'figs'); os.makedirs(rdir, exist_ok=True); os.makedirs(fdir, exist_ok=True)
    ensure_openfoam(None)
    rows, data = [], {}
    for name, kind, path, desc in RUNS:
        r, d = analyse(name, kind, path, desc)
        if r is None:
            print('missing', name); continue
        rows.append(r); data[name] = d
        with open(os.path.join(rdir, f'centreline_{name}_v2.csv'), 'w', newline='') as f:
            f.write(f'# Axis profiles, {desc}. x/De from the nozzle exit plane (De = 19.41 mm), first cell row (r ~ 0). '
                    'Z = exhaust mass fraction (single-gas OpenFOAM: total-enthalpy analogue Z_T). SIM.\n')
            w = csv.writer(f); w.writerow(['x_over_De', 'Mach', 'p_over_pa', 'T_K', 'Z', 'u_m_s'])
            for i, xv in enumerate(XGRID):
                v = [d['prof'][k][i] for k in ('M', 'p_pa', 'T', 'Y', 'u')]
                if np.isfinite(v[0]):
                    w.writerow([f'{xv:.3f}'] + [f'{a:.5g}' for a in v])
        print(name, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k not in ('description',)}))
    keys = list(rows[0].keys())
    with open(os.path.join(rdir, 'key_results_v2.csv'), 'w', newline='') as f:
        f.write('# Plume CFD key results v2.1 (100 % thrust, eps 2, sea level; v1 point Pc 24.99 bar, O/F 7.76 except '
                'own_c_2s_v2op = combustion.json v2.1 S230 point Pc 25.01 bar, O/F 10.435; snapshot rows *_t3, *_t3p25 are '
                'frames of the coarse run at 3.0/3.25 ms). Thrust = momentum + '
                'pressure integral over the nozzle exit plane; Mach disk from the axis Mach drop; peaks = axis pressure '
                'maxima downstream of the Mach disk (v1 metric); machpk = axis Mach maxima (v2 metric). SIM. SI except x/De, r/De.\n')
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    R = {r['run']: r for r in rows}
    val = dict(version='v2.1a', date='2026-10-12', runs=[r['run'] for r in rows],
               revision_note=('v2.1: levels and sensitivities compared at the same physical time (v2.0 compared the coarse '
                              'run at 4 ms with medium/sensitivity runs at 3 ms and the fine run at 3.25 ms; v2.0 file kept '
                              'as validation_v2_2level.json); temporal bands per level from the frames; oscillatory GCI '
                              'bound uses 3 x max deviation; GCI also with the observed order capped at 2; v2.1 S230 '
                              'operating-point run compared with its own 1-D reference. v2.1a: monotone data with observed order '
                              '< 0.5 (no observed convergence; the thrust had p -0.12 and a negative GCI in the first v2.1 run) '
                              'now get the 3 x max-deviation bound'))
    # 1-D reference (v1 operating point; the v2op run gets its own below)
    g0 = next((d['gas'] for k, d in data.items() if d['gas'] and k != 'own_c_2s_v2op'), None)
    D0 = next(iter(data.values()))['D']
    oned = one_d_thrust(g0, D0['De'], D0['meta']['grid']['Rt'])
    val['one_d'] = oned
    if 'own_c_2s_v2op' in data and data['own_c_2s_v2op']['gas']:
        o2 = one_d_thrust(data['own_c_2s_v2op']['gas'], D0['De'], D0['meta']['grid']['Rt'])
        r2 = R['own_c_2s_v2op']
        val['v2op'] = dict(
            one_d=o2, gas=data['own_c_2s_v2op']['gas'],
            thrust_dev_vs_ideal_lambda_pct=100 * (r2['thrust_exit_N'] / o2['F_ideal_lambda_N'] - 1),
            mdot_dev_pct=100 * (r2['mdot_throat_kg_s'] / o2['mdot'] - 1),
            x_md_cfd=r2['x_mach_disk_De'], x_md_lewis_carlson=o2['x_md_lewis_carlson_De'],
            x_md_dev_pct=100 * (r2['x_mach_disk_De'] / o2['x_md_lewis_carlson_De'] - 1),
            spacing_pp_tam=o2['Ls_prandtl_pack_tam_De'], spacing_mean3_mach=r2['spacing_mean_3_De'],
            spacing_mean3_dev_pct=100 * (r2['spacing_mean_3_De'] / o2['Ls_prandtl_pack_tam_De'] - 1),
            note='same coarse grid and models as own_c_2s_rans (v1 point O/F 7.76); v2 - v1 differences in v2op_vs_v1 '
                 'carry no grid error but do carry the temporal band of the coarse level')

    def pick(r, a, b):
        v = r.get(a, float('nan'))
        return v if isinstance(v, (int, float)) and np.isfinite(v) else r.get(b, float('nan'))
    for k in ('own_c_2s_rans', 'own_m_2s_rans', 'own_f_2s_rans', 'own_m_2s_rans_t3p25', 'own_c_2s_rans_t3p25',
              'own_c_1s_inv', 'own_c_1s_rans', 'of_c_1s_inv', 'of_c_1s_sst'):
        if k in R:
            F = pick(R[k], 'thrust_exit_N', 'thrust_exit_fields_N'); md_ = pick(R[k], 'mdot_throat_kg_s', 'mdot_exit_fields_kg_s')
            val.setdefault('thrust_vs_1d', {})[k] = dict(
                F_cfd=F, F_source='solver exit integral' if np.isfinite(R[k]['thrust_exit_N']) else 'exit-plane fields (mapped)',
                F_exit_fields=R[k]['thrust_exit_fields_N'],
                dev_vs_ideal_lambda_pct=100 * (F / oned['F_ideal_lambda_N'] - 1),
                mdot_cfd=md_, mdot_dev_pct=100 * (md_ / oned['mdot'] - 1))
    # Mach disk + shock cells vs correlations (v2: Mach-maximum cell metric; pressure-peak metric kept for the record)
    Ls = oned['Ls_prandtl_pack_tam_De']
    for k in R:
        val.setdefault('correlations', {})[k] = dict(
            x_md_cfd=R[k]['x_mach_disk_De'], x_md_lewis_carlson=oned['x_md_lewis_carlson_De'],
            x_md_dev_pct=100 * (R[k]['x_mach_disk_De'] / oned['x_md_lewis_carlson_De'] - 1),
            spacing_pp_tam=Ls,
            machpk1_x=R[k]['machpk1_x_De'], spacing_first_mach=R[k]['spacing_first_De'],
            spacing_first_dev_pct=100 * (R[k]['spacing_first_De'] / Ls - 1),
            spacing_mean3_mach=R[k]['spacing_mean_3_De'], spacing_mean3_dev_pct=100 * (R[k]['spacing_mean_3_De'] / Ls - 1),
            spacing_pressure_metric_mean_1_4=R[k]['cell_spacing_mean_1_4_De'],
            spacing_pressure_metric_dev_pct=100 * (R[k]['cell_spacing_mean_1_4_De'] / Ls - 1))
    # GCI (v2.1: all three levels at t = 3.25 ms; the fine run started from the medium solution at 3.0 ms)
    lv = ('own_f_2s_rans', 'own_m_2s_rans_t3p25', 'own_c_2s_rans_t3p25')
    GQ = ('thrust_exit_N', 'mdot_throat_kg_s', 'x_mach_disk_De', 'r_mach_disk_De', 'M_max_before_disk', 'machpk1_x_De',
          'spacing_first_De', 'spacing_mean_3_De', 'T_axis_10De_K', 'T_axis_20De_K', 'core_length_Z095_De')
    if all(k in R for k in lv):
        val['gci'] = {q: (gci(*(R[k][q] for k in lv)) or {'note': 'not computable (missing value)'})
                      | {'fine': R[lv[0]][q], 'medium': R[lv[1]][q], 'coarse': R[lv[2]][q],
                         't_ms': [R[k]['t_ms'] for k in lv]} for q in GQ}
        val['gci_mach_disk_cell_size_De'] = {k: R[k]['dx_axis_at_md_De'] for k in lv}
    lv2 = ('own_m_2s_rans', 'own_c_2s_rans_t3')       # both at 3.0 ms
    if all(k in R for k in lv2):
        val['grid_two_level'] = {q: dict(medium=R[lv2[0]][q], coarse=R[lv2[1]][q], t_ms=[R[k]['t_ms'] for k in lv2],
                                         diff_pct=100 * (R[lv2[1]][q] / R[lv2[0]][q] - 1) if R[lv2[0]][q] else float('nan'))
                                 for q in GQ}
    lv3 = ('own_m_2s_rans', 'own_c_2s_rans')          # v2.0 pairing, medium 3.0 ms vs coarse 4.0 ms (record only)
    if all(k in R for k in lv3):
        val['grid_two_level_time_mismatched_v2p0'] = {
            q: dict(medium=R[lv3[0]][q], coarse=R[lv3[1]][q], t_ms=[R[k]['t_ms'] for k in lv3],
                    diff_pct=100 * (R[lv3[1]][q] / R[lv3[0]][q] - 1) if R[lv3[0]][q] else float('nan')) for q in GQ}
    # code-to-code and model differences
    def diff(a, b, qs):
        if a in R and b in R:
            return {q: dict(a=R[a][q], b=R[b][q], diff=R[a][q] - R[b][q],
                            diff_pct=100 * (R[a][q] / R[b][q] - 1) if R[b][q] else float('nan')) for q in qs}
        return None
    QS = ('thrust_exit_N', 'thrust_exit_fields_N', 'mdot_throat_kg_s', 'mdot_exit_fields_kg_s', 'x_mach_disk_De',
          'r_mach_disk_De', 'M_before_disk', 'M_max_before_disk', 'machpk1_x_De', 'spacing_first_De', 'spacing_mean_3_De',
          'peak1_x_De', 'peak2_x_De', 'cell_spacing_mean_1_4_De', 'T_axis_10De_K', 'T_axis_20De_K', 'Z_axis_20De')
    val['own_vs_openfoam_inviscid'] = diff('own_c_1s_inv', 'of_c_1s_inv', QS)
    val['own_rans_vs_openfoam_sst'] = diff('own_c_1s_rans', 'of_c_1s_sst', QS)
    val['single_gas_error'] = diff('own_c_1s_rans', 'own_c_2s_rans', QS + ('T_axis_40De_K', 'core_length_Z095_De', 'r_half_Z_20De'))
    # v2.1: the 3 ms sensitivity runs against the coarse reference at 3.0 ms (v2.0 used the 4 ms final: kept in
    # validation_v2_2level.json)
    QX = QS + ('T_axis_40De_K', 'core_length_Z095_De', 'r_half_Z_20De')
    val['turbulence_x0p5'] = diff('own_c_2s_nu05', 'own_c_2s_rans_t3', QX)
    val['turbulence_x2'] = diff('own_c_2s_nu2', 'own_c_2s_rans_t3', QX)
    val['no_compressibility_factor'] = diff('own_c_2s_nophi', 'own_c_2s_rans_t3', QX)
    val['v2op_vs_v1'] = diff('own_c_2s_v2op', 'own_c_2s_rans', QX)
    # v2.1 temporal bands from the frames (window 2.5-3.25 ms common to coarse and medium; coarse also 3.25-4.0 ms)
    TB_Q = ('thrust_exit_N', 'mdot_throat_kg_s', 'x_mach_disk_De', 'M_max_before_disk', 'machpk1_x_De', 'spacing_first_De',
            'spacing_mean_3_De', 'T_axis_10De_K', 'T_axis_20De_K', 'T_axis_40De_K', 'core_length_Z095_De', 'r_half_Z_20De')
    series = {}
    def add_series(label, items):
        out = []
        for run_rel, k, grid_from in items:
            Dk = frame_D(run_rel, k, grid_from)
            if Dk is None:
                continue
            rk, _ = row_from(label, '', Dk)
            out.append({q: rk[q] for q in ('t_ms',) + TB_Q})
        if out:
            series[label] = out
    add_series('coarse_v1', [('ownruns/c_2s_100', k, None) for k in range(40, 81)])
    add_series('medium_v1', [('ownruns/m_2s_100', k, None) for k in range(40, 61)] +
               [('ownruns/m_2s_100_c325', k, 'ownruns/m_2s_100') for k in range(1, 6)])
    add_series('coarse_v2op', [('ownruns/c_2s_100_v2op', k, None) for k in range(40, 81)])
    def band(label, t0, t1):
        s = [r for r in series.get(label, []) if t0 - 1e-6 <= r['t_ms'] <= t1 + 1e-6]
        if len(s) < 3:
            return None
        o = dict(n=len(s), t_ms=[t0, t1])
        for q in TB_Q:
            v = np.array([r[q] for r in s], dtype=float); v = v[np.isfinite(v)]
            if len(v):
                o[q] = dict(mean=float(v.mean()), std=float(v.std(ddof=1)) if len(v) > 1 else 0.0,
                            min=float(v.min()), max=float(v.max()))
        return o
    val['temporal_band'] = {f'{lab}_{a:.2f}_{b:.2f}ms': band(lab, a, b) for lab, a, b in
                            (('coarse_v1', 2.5, 3.25), ('medium_v1', 2.5, 3.25), ('coarse_v1', 3.25, 4.0),
                             ('coarse_v2op', 2.5, 3.25), ('coarse_v2op', 3.25, 4.0))}
    val['temporal_series'] = series
    # resolvability: a grid difference is only meaningful if it exceeds the temporal scatter of the levels involved
    if 'gci' in val:
        bc = val['temporal_band'].get('coarse_v1_2.50_3.25ms') or {}
        bm = val['temporal_band'].get('medium_v1_2.50_3.25ms') or {}
        res = {}
        for q in GQ:
            if q not in bc or q not in bm:
                continue
            g = val['gci'][q]
            sig = max(bc[q]['std'], bm[q]['std'])
            d21 = abs(g['medium'] - g['fine']); d32 = abs(g['coarse'] - g['medium'])
            res[q] = dict(fine_minus_medium=d21, medium_minus_coarse=d32, std_coarse=bc[q]['std'], std_medium=bm[q]['std'],
                          resolvable=bool(d21 > 2 * sig and d32 > 2 * sig),
                          verdict=('grid effect resolved above the temporal scatter' if d21 > 2 * sig and d32 > 2 * sig else
                                   'grid differences within 2 sigma of the temporal scatter: GCI not meaningful; '
                                   'report the band'))
        val['gci_resolvability'] = res
    # starting-jet front = last axis station with T > 600 K. The OpenFOAM runs stopped at the 2 h wall-clock limit
    # (t 1.0 ms inviscid, 1.15 ms SST), so far-field axis values of those runs belong to a starting jet (added 2026-10-12).
    fr = {}
    for k, d in data.items():
        Tp = np.asarray(d['prof']['T'], dtype=float); ok = np.isfinite(Tp) & (Tp > 600.0)
        fr[k] = float(XGRID[ok].max()) if ok.any() else float('nan')
    val['jet_front_x_De'] = fr
    own_fr = [v for k, v in fr.items() if k.startswith('own_') and np.isfinite(v)]
    if 'of_c_1s_inv' in fr and 'of_c_1s_sst' in fr and own_fr:
        val['openfoam_validity_note'] = (
            f"OpenFOAM runs stopped at the 2 h wall-clock limit (inviscid t 1.0 ms, SST t 1.15 ms). The hot starting-jet front "
            f"(axis T > 600 K) had reached x = {fr['of_c_1s_inv']:.1f} De (OpenFOAM inviscid) and {fr['of_c_1s_sst']:.1f} De "
            f"(OpenFOAM SST). The own inviscid run was stopped at the same 1.0 ms (front {fr.get('own_c_1s_inv', float('nan')):.1f} De: "
            "the starting transients differ); the own RANS runs ran 3-4 ms (front at the domain end). Code-to-code differences are "
            "meaningful upstream of about 8 De only (exit plane, Mach disk, first shock cells); OpenFOAM axis values at 10-20 De "
            "(T_axis_10De_K, T_axis_20De_K, Z_axis_20De, peak2) belong to a starting jet and are not a measure of steady-plume "
            "disagreement.")
    # profile RMS differences (axis Mach, x/De 0..8, 0..15 and 0..40)
    def prms(a, b, key, x0, x1):
        if a not in data or b not in data:
            return None
        m = (XGRID >= x0) & (XGRID <= x1)
        pa, pb = data[a]['prof'][key][m], data[b]['prof'][key][m]
        ok = np.isfinite(pa) & np.isfinite(pb)
        return float(np.sqrt(np.mean((pa[ok] - pb[ok]) ** 2)))
    val['axis_rms'] = {f'{a}__{b}': {f'{k}_{x0}_{x1}': prms(a, b, k, x0, x1) for k in ('M', 'p_pa', 'T') for x0, x1 in ((0, 8), (0, 15), (0, 40))}
                       for a, b in (('own_c_1s_inv', 'of_c_1s_inv'), ('own_c_1s_rans', 'of_c_1s_sst'),
                                    ('own_m_2s_rans', 'own_c_2s_rans_t3'), ('own_f_2s_rans', 'own_m_2s_rans_t3p25'),
                                    ('own_m_2s_rans_t3p25', 'own_c_2s_rans_t3p25'), ('own_c_1s_rans', 'own_c_2s_rans'),
                                    ('own_c_2s_v2op', 'own_c_2s_rans'))}
    json.dump(val, open(os.path.join(rdir, 'validation_v2.json'), 'w'), indent=1, default=float)
    figures(data, fdir, oned, R)
    fig_temporal(series, R, fdir)
    return rows, val


def fig_temporal(series, R, fdir):
    """v2.1: time histories of the validation quantities per level (frames), with the fine-run value at 3.25 ms."""
    qs = (('x_mach_disk_De', 'Mach disk x/De'), ('machpk1_x_De', 'first Mach max x/De'), ('T_axis_10De_K', 'axis T at 10 De [K]'),
          ('T_axis_20De_K', 'axis T at 20 De [K]'), ('core_length_Z095_De', 'core length Z 0.95 [De]'), ('thrust_exit_N', 'thrust [N]'))
    if not series:
        return
    fig, axs = plt.subplots(3, 2, figsize=(11, 9), sharex=True)
    sty = {'coarse_v1': ('tab:blue', 'coarse 20k (v1 point)'), 'medium_v1': ('tab:orange', 'medium 80k (v1 point)'),
           'coarse_v2op': ('tab:green', 'coarse 20k (v2.1 point, O/F 10.4)')}
    for ax, (q, lab) in zip(axs.flat, qs):
        for s, rows in series.items():
            col, name = sty.get(s, ('0.5', s))
            ax.plot([r['t_ms'] for r in rows], [r[q] for r in rows], '.-', color=col, lw=0.8, ms=3, label=name)
        if 'own_f_2s_rans' in R:
            ax.plot([R['own_f_2s_rans']['t_ms']], [R['own_f_2s_rans'][q]], 'k*', ms=10, label='fine 320k (3.25 ms, single state)')
        ax.set_ylabel(lab, fontsize=8); ax.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=7)
    for ax in axs[-1]:
        ax.set_xlabel('t [ms]')
    fig.suptitle('Plume unsteadiness per grid level (own solver, two-species RANS, 100 %): validation_plume v2.1', fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(fdir, 'validation_unsteady_v2.png'), dpi=130); plt.close(fig)


def figures(data, fdir, oned, R):
    ref = next((k for k in ('own_m_2s_rans', 'own_c_2s_rans') if k in R and np.isfinite(R[k]['machpk1_x_De'])), None)
    x0 = R[ref]['machpk1_x_De'] if ref else oned['x_md_lewis_carlson_De'] + 0.5 * oned['Ls_prandtl_pack_tam_De']
    sets = [
        ('validation_grid_v2.png', 'Grid levels at t = 3.25 ms (own solver, two-species RANS; v2.1 time-matched)',
         [('own_c_2s_rans_t3p25', 'coarse 20k, 3.25 ms', 'tab:blue'), ('own_m_2s_rans_t3p25', 'medium 80k, 3.25 ms', 'tab:orange'),
          ('own_f_2s_rans', 'fine 320k, 3.25 ms', 'k')]),
        ('validation_v2op_v2.png', 'Operating point: v1 (O/F 7.76) vs combustion.json v2.1 S230 (O/F 10.435), coarse, t 4 ms',
         [('own_c_2s_rans', 'v1 point, O/F 7.76', 'tab:blue'), ('own_c_2s_v2op', 'v2.1 point, O/F 10.435', 'tab:green')]),
        ('validation_codes_v2.png', 'Code-to-code: own solver vs OpenFOAM rhoCentralFoam (single gas)',
         [('own_c_1s_inv', 'own inviscid', 'tab:blue'), ('of_c_1s_inv', 'OpenFOAM inviscid', 'tab:cyan'),
          ('own_c_1s_rans', 'own mixing-length RANS', 'tab:red'), ('of_c_1s_sst', 'OpenFOAM k-omega SST (1.15 ms)', 'tab:pink')]),
        ('validation_models_v2.png', 'Model sensitivity (own solver, coarse; all at 3.0 ms except single gas: 4.0 ms)',
         [('own_c_2s_rans_t3', 'two-species (reference, 3.0 ms)', 'k'),
          ('own_c_2s_rans', 'two-species at 4.0 ms (reference of single gas)', '0.6'), ('own_c_1s_rans', 'single gas (4.0 ms)', 'tab:red'),
          ('own_c_2s_nu05', 'eddy viscosity x0.5', 'tab:green'), ('own_c_2s_nu2', 'eddy viscosity x2', 'tab:purple'),
          ('own_c_2s_nophi', 'no compressibility factor', 'tab:olive')]),
    ]
    for fn, ttl, runs in sets:
        runs = [r for r in runs if r[0] in data]
        if not runs:
            continue
        fig, axs = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
        for name, lab, col in runs:
            p = data[name]['prof']
            axs[0].plot(XGRID, p['M'], color=col, lw=1, label=lab)
            axs[1].semilogy(XGRID, p['p_pa'], color=col, lw=1)
            axs[2].plot(XGRID, p['T'], color=col, lw=1)
        axs[0].axvline(oned['x_md_lewis_carlson_De'], color='0.4', ls='--', lw=0.8)
        axs[0].text(oned['x_md_lewis_carlson_De'] + 0.2, 3.6, 'Lewis-Carlson Mach disk', fontsize=7, color='0.3')
        for k in range(0, 8):
            xv = x0 + k * oned['Ls_prandtl_pack_tam_De']
            if xv < 40:
                axs[0].axvline(xv, color='0.75', lw=0.6, ls=':')
        axs[0].text(x0 + 0.2, 0.3, f"dotted: Prandtl-Pack/Tam spacing {oned['Ls_prandtl_pack_tam_De']:.2f} De from the first "
                    f"Mach maximum of {ref or 'Lewis-Carlson + Ls/2'}", fontsize=7, color='0.3')
        axs[0].set_ylabel('axis Mach'); axs[1].set_ylabel('axis p / p_a'); axs[2].set_ylabel('axis T [K] (frozen)')
        axs[2].set_xlabel('x / De from the nozzle exit plane')
        axs[0].legend(fontsize=8); axs[0].set_title(ttl, loc='left')
        for a in axs:
            a.grid(alpha=0.3); a.set_xlim(-1, 40)
        fig.tight_layout(); fig.savefig(os.path.join(fdir, fn), dpi=130); plt.close(fig)


if __name__ == '__main__':
    rows, val = main(sys.argv[1])
    print(json.dumps({k: v for k, v in val.items() if k in ('one_d', 'thrust_vs_1d', 'gci', 'grid_two_level')}, indent=1, default=float)[:6000])
