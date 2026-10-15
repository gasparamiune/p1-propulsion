"""Prepare plume fields for the ARTISTIC Blender Cycles render (Combustion / 05-plume-cfd v2).

Resamples the axisymmetric CFD plume block (x >= 0) onto a uniform (x, r) grid and writes two 16-bit greyscale PNGs
read by blender_render.py inside Blender (Blender's Python has no numpy here):
  dens.png : soot-proxy emitter density  q = Z rho / rho_ref, encoded as sqrt(q / q_max)    (shape only, ASSUMED proxy)
  temp.png : temperature T_ab_cfd (CFD T + fast-chemistry afterburning increment, afterburn v3) / T_SCALE
and fields.json with extents, scalings and the nozzle/body outline (x, r in De) for the lathe mesh.
This render is ARTISTIC: emission model, colours and exposure are chosen for appearance. The traceable synthetic image
is synth_photo.py (forward Abel integration, labelled qualitative).
usage: python blender_prep.py RUN/final.npz AFTERBURN_v3.npz CONTOUR.csv OUTDIR [--xmax 30] [--rmax 4]
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from PIL import Image

T_SCALE = 3500.0


def main():
    run, ab, contour, out = sys.argv[1:5]
    opt = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
    xmax, rmax = opt('--xmax', 30.0), opt('--rmax', 4.0)
    os.makedirs(out, exist_ok=True)
    D = np.load(run, allow_pickle=False); A = np.load(ab, allow_pickle=False)
    meta = json.loads(str(D['meta'])); g = meta['grid']; Nn = g['Nn']; De = g['De']
    xD = D['xc'][Nn:, 0] / De; rD = D['rc'][Nn, :] / De
    Z = np.clip(D['Y'][Nn:], 0, 1); rho = D['rho'][Nn:]
    T = A['T_ab_cfd'][Nn:] if 'T_ab_cfd' in A.files else D['T'][Nn:]
    T = np.where(np.isfinite(T), T, D['T'][Nn:])
    q = Z * rho / 0.3
    nx, nr = 1500, 200
    xs = np.linspace(0.0, xmax, nx); rs = np.linspace(0.0, rmax, nr)
    XX, RR = np.meshgrid(xs, rs, indexing='ij')
    pts = np.stack([np.clip(XX, xD[0], xD[-1]), np.clip(RR, rD[0], rD[-1])], axis=-1)
    qi = RegularGridInterpolator((xD, rD), q, bounds_error=False, fill_value=0.0)(pts)
    Ti = RegularGridInterpolator((xD, rD), T, bounds_error=False, fill_value=288.0)(pts)
    qmax = float(np.percentile(qi, 99.9))
    dens = np.sqrt(np.clip(qi / qmax, 0, 1))
    tn = np.clip(Ti / T_SCALE, 0, 1)
    # image: width = x, height = r (row 0 = r 0 at the bottom -> flip for PNG top-down storage)
    for name, F in (('dens', dens), ('temp', tn)):
        im = (np.flipud(F.T) * 65535 + 0.5).astype(np.uint16)
        Image.fromarray(im).save(os.path.join(out, f'{name}.png'))      # uint16 array -> 16-bit greyscale PNG
    # nozzle inner contour (x from the exit plane, in De) and an illustrative outer body
    import pandas as pd
    c = pd.read_csv(contour, comment='#')
    x_exit = float(c['x_face_m'].max())
    inner = [((float(a) - x_exit) / De, float(b) / De) for a, b in zip(c['x_face_m'], c['r_m'])]
    info = dict(De_m=De, xmax_De=xmax, rmax_De=rmax, nx=nx, nr=nr, q_max=qmax, T_scale_K=T_SCALE,
                dens_encoding='sqrt(q/q_max), q = Z rho / 0.3 kg/m3', run=run, afterburn=ab, t_s=meta['t'],
                nozzle_inner_De=inner, body_outer_radius_De=0.022 / De, case_outer_radius_De=0.032 / De,
                note='ARTISTIC render inputs; outer body radii are illustrative (44 mm insert sleeve, ~64 mm case).')
    json.dump(info, open(os.path.join(out, 'fields.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in info.items() if k != 'nozzle_inner_De'}))


if __name__ == '__main__':
    main()
