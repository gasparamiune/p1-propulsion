"""Driver for plume2s (Combustion / 05-plume-cfd v1).

usage: python run_plume.py OUTDIR --level {0.5,1,2} [--single] [--inviscid] [--frac 1.0] [--tend 1.5e-3]
                           [--frame 2e-5] [--init FILE.npz] [--ramp 'frac0:frac1:t0:t1,...'] [--Cl 0.071] [--nophi]
                           [--cfl 0.5] [--maxsteps N]
Writes OUTDIR/history.csv (t, dt, mdot_throat, mdot_exit, thrust_exit, p_base_force, centreline probes),
OUTDIR/frame_XXXX.npz (float32 subset for animation), OUTDIR/final.npz (full state), OUTDIR/run.json.
Throttle ramps change the inlet total pressure/temperature and the exhaust calibration (gamma_e, R_e)
linearly in time between CEA-calibrated operating points (quasi-steady, time-compressed: labelled).
"""
from __future__ import annotations
import argparse, json, math, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plume2s as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--level', type=float, default=0.5)
    ap.add_argument('--single', action='store_true')
    ap.add_argument('--inviscid', action='store_true')
    ap.add_argument('--frac', type=float, default=1.0)
    ap.add_argument('--tend', type=float, default=1.5e-3)
    ap.add_argument('--frame', type=float, default=0.0)
    ap.add_argument('--init', default=None)
    ap.add_argument('--ramp', default=None, help="comma list of segments 'f0:f1:t0:t1' (fractions, absolute times)")
    ap.add_argument('--Cl', type=float, default=0.071)
    ap.add_argument('--nophi', action='store_true')
    ap.add_argument('--cfl', type=float, default=0.5)
    ap.add_argument('--maxsteps', type=int, default=10 ** 9)
    ap.add_argument('--keep_time', action='store_true', help='continue the time of the init file')
    ap.add_argument('--lts', type=int, default=0, help='steady state: N local-time-stepping iterations')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    J, pts, Rbody = P.load_geometry()
    grid = P.Grid(pts, Rbody, level=a.level)
    fracs = {a.frac}
    segs = []
    if a.ramp:
        for s in a.ramp.split(','):
            f0, f1, t0, t1 = [float(x) for x in s.split(':')]
            segs.append((f0, f1, t0, t1)); fracs |= {f0, f1}
    gases = {f: P.chamber_gas(f, J) for f in sorted(fracs)}
    S = P.Solver(grid, gases[a.frac], single=a.single, turbulent=not a.inviscid, Cl=a.Cl, use_phi=not a.nophi, CFL=a.cfl)
    if a.init:
        S.init_from(a.init)
        if a.keep_time:
            m = json.loads(str(np.load(a.init)['meta'])); S.t = m['t']
    info = dict(args=vars(a), grid=grid.summary(), gases={str(k): v for k, v in gases.items()},
                oppoints_source=J.get('_oppoints_source', 'cfd/inputs/combustion_v1.json (default)'))
    json.dump(info, open(os.path.join(a.out, 'run.json'), 'w'), indent=1, default=float)

    def gas_at(t):
        for f0, f1, t0, t1 in segs:
            if t0 <= t <= t1:
                w = (t - t0) / (t1 - t0)
                g0, g1 = gases[f0], gases[f1]
                return {k: (1 - w) * g0[k] + w * g1[k] if isinstance(g0[k], float) else g0[k] for k in g0}, (1 - w) * f0 + w * f1
        if segs and t > segs[-1][3]:
            return gases[segs[-1][1]], segs[-1][1]
        if segs and t < segs[0][2]:
            return gases[segs[0][0]], segs[0][0]
        return gases[a.frac], a.frac

    if a.lts > 0:
        run_lts(S, a, grid)
        return
    # probes: centreline cells
    jc0 = 0
    hist = open(os.path.join(a.out, 'history.csv'), 'w')
    hist.write('t_s,dt_s,frac,p0_Pa,mdot_throat_kgs,mdot_exit_kgs,thrust_exit_N,base_force_N,p_axis_x1De_Pa,M_axis_x2De,'
               'cputime_s\n')
    g = grid
    i1 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 1.0 * g.De)))
    i2 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 2.0 * g.De)))
    t_wall0 = time.time(); next_frame = S.t; kf = 0; nstep0 = S.nstep
    t_hist = 0.0
    while S.t < a.tend and S.nstep - nstep0 < a.maxsteps:
        if segs:
            gs, fr = gas_at(S.t)
            S.set_gas(gs)
        else:
            fr = a.frac
        dt = S.step()
        if not np.isfinite(dt) or not np.isfinite(S.U[P.G:-P.G, P.G:-P.G]).all():
            print('NaN at step', S.nstep, 't', S.t); S.save(os.path.join(a.out, 'crash.npz')); sys.exit(3)
        if S.nstep % 20 == 0:
            mt = S.throat_mdot(); me, Fe = S.exit_plane()
            # base force (p - pa) on the annulus Re..Rbody at x = 0, + is thrust
            Fb = 0.0
            for j in range(g.jc, g.js):
                Fb += (S.W[g.Nn + P.G, j + P.G, 3] - P.PA) * g.AI[g.Nn, j] * 2 * math.pi
            W = S.W
            pax = W[i1 + P.G, P.G, 3]
            c = math.sqrt(S.Gam[i2 + P.G, P.G] * W[i2 + P.G, P.G, 3] / W[i2 + P.G, P.G, 0])
            Max = abs(W[i2 + P.G, P.G, 1]) / c
            hist.write(f'{S.t:.9e},{dt:.4e},{fr:.4f},{S.p0:.1f},{mt:.6f},{me:.6f},{Fe:.3f},{Fb:.3f},{pax:.1f},{Max:.4f},'
                       f'{time.time() - t_wall0:.1f}\n')
        if S.nstep % 500 == 0:
            hist.flush()
            print(f'step {S.nstep} t={S.t*1e3:.4f} ms dt={dt:.3e} mdot_t={S.throat_mdot():.5f} F_e={S.exit_plane()[1]:.1f} '
                  f'wall={time.time()-t_wall0:.0f}s', flush=True)
        if a.frame > 0 and S.t >= next_frame:
            F = S.fields()
            np.savez_compressed(os.path.join(a.out, f'frame_{kf:04d}.npz'), t=S.t, frac=fr,
                                **{k: F[k].astype(np.float32) for k in ('rho', 'p', 'T', 'Y', 'M', 'u', 'v')})
            kf += 1; next_frame += a.frame
    hist.close()
    S.save(os.path.join(a.out, 'final.npz'), extra=dict(wall_s=time.time() - t_wall0, frames=kf))
    me, Fe = S.exit_plane()
    print(json.dumps(dict(t=S.t, nstep=S.nstep, mdot_throat=S.throat_mdot(), mdot_exit=me, thrust_exit=Fe,
                          wall_s=time.time() - t_wall0)))


def run_lts(S, a, g):
    """Steady state by SSP-RK2 local time stepping; logs residual, mass flow, thrust and axis probes."""
    i1 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 2.0 * g.De)))
    i5 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 5.0 * g.De)))
    i10 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 10.0 * g.De)))
    i20 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 20.0 * g.De)))
    i40 = g.Nn + int(np.argmin(np.abs(g.xc[g.Nn:, 0] - 40.0 * g.De)))
    hist = open(os.path.join(a.out, 'history_lts.csv'), 'w')
    hist.write('iter,res_rho,mdot_throat,mdot_exit,thrust_exit,base_force,u_ax_2De,u_ax_5De,u_ax_10De,u_ax_20De,Y_ax_20De,'
               'u_ax_40De,cputime_s\n')
    t0 = time.time(); r0 = None
    for it in range(1, a.lts + 1):
        r = S.step_lts()
        if r0 is None:
            r0 = r
        if not np.isfinite(r):
            print('NaN at iteration', it); S.save(os.path.join(a.out, 'crash.npz')); sys.exit(3)
        if it % 50 == 0:
            mt = S.throat_mdot(); me, Fe = S.exit_plane()
            Fb = 0.0
            for j in range(g.jc, g.js):
                Fb += (S.W[g.Nn + P.G, j + P.G, 3] - P.PA) * g.AI[g.Nn, j] * 2 * math.pi
            W = S.W
            hist.write(f'{it},{r:.5e},{mt:.6f},{me:.6f},{Fe:.3f},{Fb:.3f},' +
                       ','.join(f'{W[i + P.G, P.G, 1]:.2f}' for i in (i1, i5, i10, i20)) +
                       f',{W[i20 + P.G, P.G, 4]:.4f},{W[i40 + P.G, P.G, 1]:.2f},{time.time() - t0:.1f}\n')
        if it % 1000 == 0:
            hist.flush()
            print(f'it {it} res {r:.3e} ({r / r0:.2e}) F_e={S.exit_plane()[1]:.1f} wall={time.time()-t0:.0f}s', flush=True)
        if it % 10000 == 0:
            S.save(os.path.join(a.out, 'checkpoint.npz'))
    hist.close()
    S.save(os.path.join(a.out, 'final.npz'), extra=dict(wall_s=time.time() - t0, lts_iterations=a.lts))
    me, Fe = S.exit_plane()
    print(json.dumps(dict(iterations=a.lts, mdot_throat=S.throat_mdot(), mdot_exit=me, thrust_exit=Fe,
                          wall_s=time.time() - t0)))


if __name__ == '__main__':
    main()
