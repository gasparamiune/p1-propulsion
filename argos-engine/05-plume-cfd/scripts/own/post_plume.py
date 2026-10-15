"""Post-processing for plume2s and OpenFOAM plume runs (Combustion / 05-plume-cfd v1).

Functions return plain numpy data; figures use physical axes in exit diameters (x/De from the exit plane,
r/De from the axis), the jet mirrored about the axis.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors

PA, TA = 101325.0, 288.15
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 9, 'axes.labelsize': 9, 'figure.dpi': 150,
                     'savefig.dpi': 220, 'font.family': 'DejaVu Sans'})


def load_own(fn):
    d = np.load(fn, allow_pickle=False)
    out = {k: d[k] for k in d.files if k not in ('meta', 'U')}
    out['meta'] = json.loads(str(d['meta']))
    out['De'] = out['meta']['grid']['De']
    out['Nn'] = out['meta']['grid']['Nn']
    return out


def gradient_xr(X_c, R_c, F):
    """d/dx, d/dr of a cell field on a structured (possibly curvilinear) grid via the index-space Jacobian."""
    Fi, Fj = np.gradient(F)
    xi, xj = np.gradient(X_c)
    ri, rj = np.gradient(R_c)
    J = xi * rj - xj * ri
    J = np.where(np.abs(J) < 1e-30, 1e-30, J)
    Fx = (Fi * rj - Fj * ri) / J
    Fr = (Fj * xi - Fi * xj) / J
    return Fx, Fr


def schlieren(D):
    rx, rr = gradient_xr(D['xc'], D['rc'], D['rho'])
    g = np.hypot(rx, rr)
    g[D['region'] == 3] = 0.0
    return g


def plot_field(ax, D, F, cmap, norm=None, mirror=True, xlim=(-1.2, 15), rlim=3.0, label=None, cb=True,
               mask_solid=True):
    De = D['De']
    X = D['X'] / De; R = D['R'] / De
    Fm = np.ma.masked_where(D['region'] == 3, F) if mask_solid else F
    im = ax.pcolormesh(X, R, Fm, cmap=cmap, norm=norm, shading='flat', rasterized=True)
    if mirror:
        ax.pcolormesh(X, -R, Fm, cmap=cmap, norm=norm, shading='flat', rasterized=True)
    # nozzle wall + base outline
    Nn = D['Nn']; jc = D['meta']['grid']['jc']; js = D['meta']['grid']['js']
    xw = D['X'][:Nn + 1, jc] / De; rw = D['R'][:Nn + 1, jc] / De
    xb = D['X'][:Nn + 1, js] / De; rb = D['R'][:Nn + 1, js] / De
    for s in (1, -1):
        ax.fill(np.concatenate([xw, xb[::-1]]), s * np.concatenate([rw, rb[::-1]]), color='0.55', lw=0.4, ec='k')
    ax.set_xlim(*xlim); ax.set_ylim(-rlim if mirror else 0, rlim)
    ax.set_aspect('equal')
    ax.set_xlabel('x / De  (from nozzle exit plane)'); ax.set_ylabel('r / De')
    if cb:
        c = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
        if label:
            c.set_label(label)
    return im


def centreline(D):
    """Axis profiles (first cell row j=0) for nozzle + plume."""
    x = D['xc'][:, 0] / D['De']
    out = dict(x_De=x, M=D['M'][:, 0], p_pa=D['p'][:, 0] / PA, T=D['T'][:, 0], Y=D['Y'][:, 0], u=D['u'][:, 0],
               rho=D['rho'][:, 0])
    return out


def shock_cells(D, x_max=40.0):
    """Shock-cell structure from the centreline pressure: local maxima of p (compression peaks) in the plume.
    Returns peak positions (x/De), spacing, and Mach-disk diagnostics in the first cell."""
    c = centreline(D)
    x = c['x_De']; p = c['p_pa']; M = c['M']
    sel = (x > 0.05) & (x < x_max)
    xs, ps, Ms = x[sel], p[sel], M[sel]
    # smooth lightly to avoid single-cell wiggles
    k = np.ones(3) / 3
    pss = np.convolve(ps, k, mode='same')
    peaks = [i for i in range(2, len(pss) - 2) if pss[i] > pss[i - 1] and pss[i] >= pss[i + 1] and
             pss[i] > 1.02 * min(pss[max(0, i - 20):i + 1].min(), 10)]
    # keep significant peaks: prominence above 10 % of local swing
    sig = []
    for i in peaks:
        lo = max(0, i - 40); hi = min(len(pss), i + 40)
        prom = pss[i] - max(pss[lo:i].min(), pss[i:hi].min())
        if prom > 0.05:
            sig.append((xs[i], pss[i], prom))
    xpk = np.array([s[0] for s in sig])
    # Mach disk: strongest single-step drop of M from >1 to <1 before the first pressure peak
    md = None
    i_end = np.searchsorted(xs, xpk[0]) if len(xpk) else len(xs)
    dM = np.diff(Ms[:i_end + 2])
    if len(dM):
        i = int(np.argmin(dM))
        if Ms[i] > 1.0 and Ms[i + 1] < 1.0:
            md = dict(x_De=float(0.5 * (xs[i] + xs[i + 1])), M_before=float(Ms[i]), M_after=float(Ms[i + 1]))
    # Mach disk radius: radial extent of the subsonic pocket just downstream of the disk
    md_r = None
    if md is not None:
        ii = np.where(np.abs(D['xc'][:, 0] / D['De'] - md['x_De']) < 1e-9 + 0.5 * np.diff(D['xc'][:, 0] / D['De']).max())[0]
        i0 = int(np.argmin(np.abs(D['xc'][:, 0] / D['De'] - md['x_De'])))
        # first cell row after the disk: count contiguous subsonic cells from the axis
        for di in (1, 2, 3):
            col = D['M'][i0 + di, :]
            js = np.where(col >= 1.0)[0]
            if len(js) and js[0] > 0:
                md_r = float(D['rc'][i0 + di, js[0] - 1] / D['De'])
                break
        md['r_De'] = md_r
    return dict(peaks_x_De=xpk.tolist(), spacing_De=np.diff(xpk).tolist(), mach_disk=md,
                peaks=[dict(x_De=float(a), p_pa=float(b), prominence=float(c)) for a, b, c in sig])


def jet_boundary(D, Yb=0.5):
    """Radius of the Y = Yb iso-line vs x (plume columns)."""
    Nn = D['Nn']
    xs = D['xc'][Nn:, 0] / D['De']; rb = []
    for i in range(Nn, D['Y'].shape[0]):
        col = D['Y'][i]; r = D['rc'][i] / D['De']
        js = np.where(col < Yb)[0]
        rb.append(r[js[0]] if len(js) else np.nan)
    return xs, np.array(rb)


def standard_figures(D, outdir, tag, title_extra=''):
    os.makedirs(outdir, exist_ok=True)
    meta = D['meta']
    ttl = f"{tag}: {'single-gas' if meta['single'] else 'two-species'}, " \
          f"{'mixing-length RANS' if meta['turbulent'] else 'inviscid'}, level {meta['level']}, t = {meta['t']*1e3:.2f} ms" + title_extra
    files = []
    specs = [
        ('mach', D['M'], 'turbo', colors.Normalize(0, max(3.5, float(np.nanmax(D['M'])))), 'Mach number'),
        ('p_pa', D['p'] / PA, 'RdBu_r', colors.LogNorm(0.2, 30), 'p / p_a (log)'),
        ('T', D['T'], 'inferno', colors.Normalize(250, max(3000, float(D['T'].max()))), 'T [K] (frozen, no afterburning)'),
        ('rho', D['rho'], 'cividis', colors.LogNorm(0.05, 30), 'density [kg/m^3] (log)'),
        ('Z', D['Y'], 'magma', colors.Normalize(0, 1), 'mixture fraction Z (exhaust mass fraction)'),
    ]
    S = schlieren(D)
    sch = np.exp(-12.0 * S / max(np.percentile(S[D['region'] != 3], 99.7), 1e-9))
    specs.append(('schlieren', sch, 'gray', colors.Normalize(0, 1), 'numerical schlieren exp(-k|grad rho|/max)'))
    for name, F, cm, nm, lab in specs:
        for zoom, xl, rl, fs in (('near', (-1.5, 15), 3.0, (10, 4.4)), ('full', (-4, 45), 12.0, (12, 6.6))):
            fig, ax = plt.subplots(figsize=fs)
            plot_field(ax, D, F, cm, nm, xlim=xl, rlim=rl, label=lab)
            ax.set_title(ttl, loc='left')
            fn = os.path.join(outdir, f'{tag}_{name}_{zoom}.png')
            fig.savefig(fn, bbox_inches='tight'); plt.close(fig); files.append(fn)
    # centreline
    c = centreline(D)
    fig, axs = plt.subplots(4, 1, figsize=(9, 8), sharex=True)
    axs[0].plot(c['x_De'], c['M'], 'k-', lw=1); axs[0].set_ylabel('Mach (axis)')
    axs[1].semilogy(c['x_De'], c['p_pa'], 'b-', lw=1); axs[1].set_ylabel('p / p_a (axis)')
    axs[2].plot(c['x_De'], c['T'], 'r-', lw=1); axs[2].set_ylabel('T [K] (axis)')
    axs[3].plot(c['x_De'], c['Y'], 'm-', lw=1); axs[3].set_ylabel('Z (axis)'); axs[3].set_xlabel('x / De')
    for a in axs:
        a.grid(alpha=0.3); a.axvline(0, color='0.5', lw=0.6)
    axs[0].set_title(ttl, loc='left')
    fn = os.path.join(outdir, f'{tag}_centreline.png'); fig.savefig(fn, bbox_inches='tight'); plt.close(fig); files.append(fn)
    return files


if __name__ == '__main__':
    D = load_own(sys.argv[1])
    fl = standard_figures(D, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'run')
    sc = shock_cells(D)
    print(json.dumps(sc, indent=1))
    print(json.dumps({k: D['meta'][k] for k in ('t', 'mdot_exit', 'thrust_exit', 'mdot_throat')}, indent=1))
