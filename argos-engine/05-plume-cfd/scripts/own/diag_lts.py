import sys, os, json, math, numpy as np
sys.path.insert(0, '/home/claude/work/combustion/cfd/own')
import plume2s as P
J, pts, Rbody = P.load_geometry()
g = P.Grid(pts, Rbody, level=float(sys.argv[2]))
S = P.Solver(g, P.chamber_gas(1.0, J), single=False, turbulent=True)
S.init_from(sys.argv[1])
out = sys.argv[3]; n = int(sys.argv[4])
acc = np.zeros((g.NI, g.NJ))
for it in range(n):
    r = S.step_lts()
    rr = np.abs(S.res[..., 0] / g.V); rr[g.region == 3] = 0
    acc = np.maximum(acc, rr)
    if it % 200 == 0:
        W = S.W[P.G:-P.G, P.G:-P.G]
        fl = g.region != 3
        i, j = np.unravel_index(np.argmax(np.where(fl, rr, 0)), rr.shape)
        print(it, f'res {r:.3e}', 'max at', i, j, f'x/De={g.xc[i,j]/g.De:.2f} r/De={g.rc[i,j]/g.De:.2f}',
              f'rho_min {W[...,0][fl].min():.3e} p_min {W[...,3][fl].min():.1f} T_min {S.Tg[P.G:-P.G,P.G:-P.G][fl].min():.1f}',
              f'mut_max {S.mut.max():.3e}', flush=True)
np.savez(out, acc=acc, xc=g.xc, rc=g.rc, region=g.region)
S.save(out.replace('.npz', '_state.npz'))
