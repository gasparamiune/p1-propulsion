"""Read OpenFOAM rhoCentralFoam wedge results (pyvista/VTK OpenFOAM reader) and map them onto the plume2s grid
so that both solvers are post-processed by the same code. (Combustion / 05-plume-cfd v1)

Single-gas OpenFOAM model: the mixture fraction is not transported (function objects crash in this build,
FAILURE-CFD-01); it is reconstructed from total enthalpy, Z_T = (cp T + |U|^2/2 - cp Ta) / (cp T0 - cp Ta),
which equals the transported scalar only for unit turbulent Prandtl/Schmidt numbers (OpenFOAM SST here: Prt 0.85;
inviscid: numerical diffusion only) -> labelled 'Z_T (total-enthalpy analogue)'.
usage: python of_post.py CASE TIME LEVEL OUT.npz
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import pyvista as pv
from scipy.interpolate import griddata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plume2s as P

PA, TA = 101325.0, 288.15


def read_case(case, t=None):
    fn = os.path.join(case, 'case.foam')
    if not os.path.exists(fn):
        open(fn, 'w').close()
    r = pv.POpenFOAMReader(fn)
    times = list(r.time_values)
    if t is None:
        t = times[-1]
    tt = min(times, key=lambda v: abs(v - t))
    r.set_active_time_value(tt)
    r.enable_all_cell_arrays() if hasattr(r, 'enable_all_cell_arrays') else None
    m = r.read()['internalMesh']
    cc = m.cell_centers().points
    x = cc[:, 0]; rr = np.hypot(cc[:, 1], cc[:, 2])
    d = {k: np.asarray(m.cell_data[k]) for k in m.cell_data.keys()}
    return tt, times, x, rr, d


def to_grid(case, t, level):
    tt, times, x, r, d = read_case(case, t)
    meta = json.load(open(os.path.join(case, 'case_meta.json')))
    cs = meta['chamber']
    cp = cs['cp_eff']; R = cs['R_eff']; g = cs['gamma_eff']; T0 = cs['T0']
    J, pts, Rbody = P.load_geometry()
    G = P.Grid(pts, Rbody, level=level)
    q = np.stack([G.xc.ravel(), G.rc.ravel()], axis=1)
    src = np.stack([x, r], axis=1)
    U = d['U']
    fields = dict(p=d['p'], T=d['T'], u=U[:, 0], v=np.hypot(U[:, 1], U[:, 2]) * np.sign(U[:, 1] + 1e-30),
                  rho=d['rho'] if 'rho' in d else d['p'] / (R * d['T']))
    if 'nut' in d:
        fields['nut'] = d['nut']
    out = {}
    for k, v in fields.items():
        a = griddata(src, v, q, method='linear')
        bad = ~np.isfinite(a)
        if bad.any():
            a[bad] = griddata(src, v, q[bad], method='nearest')
        out[k] = a.reshape(G.xc.shape)
    c = np.sqrt(g * out['p'] / out['rho'])
    out['M'] = np.hypot(out['u'], out['v']) / c
    out['Y'] = np.clip((cp * out['T'] + 0.5 * (out['u'] ** 2 + out['v'] ** 2) - cp * TA) / (cp * T0 - cp * TA), 0, 1)
    out['gamma'] = np.full(G.xc.shape, g)
    out['mut'] = out.get('nut', np.zeros(G.xc.shape)) * out['rho']
    # exit-plane integrals on a fine radial line just inside the exit plane
    rl = np.linspace(0, G.Re, 401)[1:-1]; xl = np.full_like(rl, -1e-5)
    s = {k: griddata(src, fields[k], np.stack([xl, rl], 1), method='linear') for k in ('p', 'u', 'rho')}
    integ = lambda f: float(np.trapezoid(f * 2 * np.pi * rl, rl))
    mdot = integ(s['rho'] * s['u']); F = integ(s['rho'] * s['u'] ** 2 + s['p'] - PA)
    rt = np.linspace(0, G.Rt, 401)[1:-1]
    st = {k: griddata(src, fields[k], np.stack([np.full_like(rt, G.x_t), rt], 1), method='linear') for k in ('u', 'rho')}
    mdot_t = float(np.trapezoid(st['rho'] * st['u'] * 2 * np.pi * rt, rt))
    m2 = dict(t=tt, nstep=-1, single=True, turbulent='nut' in d, level=level, mdot_exit=mdot, thrust_exit=F,
              mdot_throat=mdot_t, gas=dict(gamma_e=g, R_e=R, p0=cs['Pc'], T0=T0), grid=G.summary(), source='OpenFOAM ' + case,
              times=times)
    return G, out, m2


if __name__ == '__main__':
    case, t, level, outfn = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    G, out, m = to_grid(case, t, level)
    np.savez_compressed(outfn, xc=G.xc, rc=G.rc, X=G.X, R=G.R, region=G.region, meta=json.dumps(m, default=float), **out)
    print(json.dumps({k: m[k] for k in ('t', 'mdot_exit', 'thrust_exit', 'mdot_throat')}))
