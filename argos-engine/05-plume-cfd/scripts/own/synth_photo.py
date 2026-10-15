"""Synthetic photo-like side view of the plume by line-of-sight (forward Abel) integration of an emission model.
QUALITATIVE (labelled): soot-proxy grey-body emission, not a validated radiation model. (Combustion / 05-plume-cfd v1)

Emission/absorption per unit volume at wavelength L (Rayleigh-limit soot, e.g. Modest, Radiative Heat Transfer):
   kappa_L = C_abs * f_v / L,   j_L = kappa_L * B_L(T),   f_v = f_v0 * Z * rho / rho_ref   (soot carried with exhaust)
   f_v0 = 1e-7 (ASSUMED order of magnitude for a sooty ABS hybrid exhaust; it only scales brightness/opacity),
   C_abs = 4.9 (~6 pi E(m), E(m) ~ 0.26, ASSUMED), T = CFD T + fast-chemistry afterburning increment dT_ab
   (afterburn v3 field T_ab_cfd; T_eq for older files) or the frozen CFD T.
Line of sight along z (orthographic side view): r = sqrt(y^2 + z^2); radiative transfer integrated along each ray
   I = sum j * exp(-tau_to_camera) ds.  Three wavelengths (630, 550, 460 nm) -> linear RGB -> exposure -> sRGB.
usage: python synth_photo.py RUN/final.npz AFTERBURN.npz OUT.png [--title ...] [--xmax 30] [--ymax 3]
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

H, C, KB = 6.62607015e-34, 2.99792458e8, 1.380649e-23


def planck(L, T):
    with np.errstate(over='ignore'):
        return 2 * H * C ** 2 / L ** 5 / np.expm1(H * C / (L * KB * np.maximum(T, 1.0)))


def emission_maps(D, A=None, fv0=1e-7, Cabs=4.9, use_ab=True):
    """Return plume-block (x, r) axes and fields kappa/j for 3 wavelengths."""
    Nn = int(json.loads(str(D['meta']))['grid']['Nn'])
    De = json.loads(str(D['meta']))['grid']['De']
    xc = D['xc'][Nn:, 0]; rc = D['rc'][Nn, :]
    Z = np.clip(D['Y'][Nn:], 0, 1); rho = D['rho'][Nn:]
    T = D['T'][Nn:]
    if A is not None and use_ab:
        key = 'T_ab_cfd' if 'T_ab_cfd' in A.files else 'T_eq'     # v3: CFD T + afterburning increment
        Teq = A[key][Nn:]
        T = np.where(np.isfinite(Teq) & (Z > 2e-3), Teq, T)
    fv = fv0 * Z * rho / 0.3
    out = {}
    for name, L in (('R', 630e-9), ('G', 550e-9), ('B', 460e-9)):
        kap = Cabs * fv / L
        out[name] = (kap, kap * planck(L, T))
    return xc / De, rc / De, De, out, T


def render(D, A, out_png, title='', xmax=30.0, ymax=3.0, nx=1400, ny=300, nz=400, exposure=None, use_ab=True):
    xD, rD, De, maps, T = emission_maps(D, A, use_ab=use_ab)
    xs = np.linspace(-1.0, xmax, nx); ys = np.linspace(-ymax, ymax, ny)
    zs = np.linspace(-ymax, ymax, nz); dz = (zs[1] - zs[0]) * De
    img = np.zeros((nx, ny, 3))
    interp = {}
    for name in ('R', 'G', 'B'):
        kap, j = maps[name]
        interp[name] = (RegularGridInterpolator((xD, rD), kap, bounds_error=False, fill_value=0.0),
                        RegularGridInterpolator((xD, rD), j, bounds_error=False, fill_value=0.0))
    YY, ZZ = np.meshgrid(ys, zs, indexing='ij')
    RR = np.sqrt(YY ** 2 + ZZ ** 2)
    for i0 in range(0, nx, 40):                              # chunks along x keep memory < 0.3 GB
        xc = xs[i0:i0 + 40]
        XX = np.broadcast_to(xc[:, None, None], (len(xc),) + RR.shape)
        R3 = np.broadcast_to(RR[None], XX.shape)
        inside = (XX >= xD[0]) & (XX <= xD[-1]) & (R3 <= rD[-1])
        pts = np.stack([np.clip(XX, xD[0], xD[-1]), np.clip(R3, rD[0], rD[-1])], axis=-1)
        for c, name in enumerate(('R', 'G', 'B')):
            fk, fj = interp[name]
            K = np.where(inside, fk(pts), 0.0); Jm = np.where(inside, fj(pts), 0.0)
            tau = np.cumsum(K[..., ::-1], axis=-1)[..., ::-1] * dz      # camera at z = +inf
            img[i0:i0 + 40, :, c] = np.sum(Jm * np.exp(-tau) * dz, axis=-1)
    lum = 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]
    if exposure is None:
        exposure = 1.0 / max(np.percentile(lum, 99.7), 1e-30)
    x = img * exposure
    x = x / (1.0 + x)                                    # Reinhard tone map
    srgb = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)
    srgb = np.clip(srgb, 0, 1)
    fig, ax = plt.subplots(figsize=(12, 12 * 2 * ymax / (xmax + 1) + 0.9), facecolor='black')
    ax.imshow(np.transpose(srgb, (1, 0, 2)), extent=[xs[0], xs[-1], ys[0], ys[-1]], origin='lower', interpolation='bilinear')
    # nozzle silhouette (exit at x = 0): conical/body outline from the solver grid
    meta = json.loads(str(D['meta']))
    Nn = meta['grid']['Nn']; js = meta['grid']['js']; jc = meta['grid']['jc']
    xb = D['X'][:Nn + 1, js] / De; rb = D['R'][:Nn + 1, js] / De
    ax.fill_between(xb, -rb, rb, color='#2b2b2b', ec='#555555', lw=0.6)
    ax.set_facecolor('black')
    ax.set_xlim(-1.0, xmax); ax.set_ylim(-ymax, ymax); ax.set_aspect('equal')
    ax.tick_params(colors='0.7'); [s.set_color('0.5') for s in ax.spines.values()]
    ax.set_xlabel('x / De', color='0.8'); ax.set_ylabel('y / De', color='0.8')
    ax.set_title(title + '\nQUALITATIVE synthetic image: soot-proxy grey-body emission (f_v ~ Z rho), '
                 + ('CFD T + fast-chemistry afterburning increment' if use_ab else 'frozen CFD T (no afterburning)')
                 + ', line-of-sight integration',
                 color='0.85', fontsize=8, loc='left')
    fig.savefig(out_png, dpi=200, bbox_inches='tight', facecolor='black'); plt.close(fig)
    return dict(exposure=exposure, png=out_png)


if __name__ == '__main__':
    D = np.load(sys.argv[1], allow_pickle=False)
    A = np.load(sys.argv[2], allow_pickle=False) if sys.argv[2] != 'none' else None
    title = sys.argv[sys.argv.index('--title') + 1] if '--title' in sys.argv else ''
    xmax = float(sys.argv[sys.argv.index('--xmax') + 1]) if '--xmax' in sys.argv else 30.0
    ymax = float(sys.argv[sys.argv.index('--ymax') + 1]) if '--ymax' in sys.argv else 3.0
    print(render(D, A, sys.argv[3], title=title, xmax=xmax, ymax=ymax, use_ab=A is not None))
