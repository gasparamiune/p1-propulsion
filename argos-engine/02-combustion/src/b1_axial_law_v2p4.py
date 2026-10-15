"""Where does the B1 web burn through first? Axial-law sensitivity (Combustion v2.4, RC-07; 2026-10-13).

The baseline law r = a G_ox^n regresses a straight port uniformly (G_ox does not vary along the port), so the baseline
model cannot say where the liner is exposed first. This script reruns the B1 sizing cycle (GNC v3 dispersed p99 with
throat growth, the RC-07 governing case) with grain_q1d's total-mass-flux variant r = a (G_ox + G_fuel,cum(x))^n, same a
and n (so the head-end rate equals the baseline and the rate grows downstream), and records the port diameter profile at
the first burn-through and at the end of the cycle. Two laws are not a bracket of reality: head-end enhancement from the
pintle spray impingement (no model here) acts at the other end of the grain.
usage: python -I b1_axial_law_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, os, sys, time
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
import run_dc as RD
import b1_web_fix_v2p4 as W


def run(name, growth, band, n, law, Dp=0.025):
    d, meta, dc, At_hist = W.load(name, growth)
    tk = RD.make_tank('neq', meta['tank_V_m3'], meta['m_n2o_kg'], float(d.T_tank_K.iloc[0]), 1e3)
    cfg = dict(a=1.0e-3 / 300.0 ** n * band, n=n, D_port0=Dp, law=law)
    snap = {}
    orig = Q.Engine.step

    def step(self, dt, a_axial=Q.G0):
        F = orig(self, dt, a_axial)
        if self.burnthrough is not None and 'D' not in snap:
            snap['D'] = self.D.copy(); snap['t'] = self.t
        snap['D_last'] = self.D
        return F
    Q.Engine.step = step
    try:
        t0 = time.time()
        rec, e = Q.simulate(dc, tk, cfg=cfg, init_running=bool(d.F_cmd_N.iloc[0] > 0), At_hist=At_hist)
    finally:
        Q.Engine.step = orig
    r = pd.DataFrame(rec)
    on = (r.mox > 1e-4) & (r.Pc > 1.5e5)
    Nc = len(e.D); x = (np.arange(Nc) + 0.5) / Nc
    Dend = np.array(e.D)
    out = dict(cycle=name, growth=growth, a_band=band, n=n, law=law, D_port0_m=Dp, burnthrough_s=e.burnthrough,
               w_min_end_mm=float(r.w_min.values[-1] * 1e3), burn_s=float(on.sum() * 0.01),
               OF_mean=float(r.mox[on].sum() / max(r.mf[on].sum(), 1e-9)), fuel_used_kg=float(e.fuel_burnt),
               D_end_profile_mm={f'{xx:.3f}': round(float(dd) * 1e3, 3) for xx, dd in zip(x[::4], Dend[::4])},
               D_end_head_mm=float(Dend[0] * 1e3), D_end_aft_mm=float(Dend[-1] * 1e3), wall_s=round(time.time() - t0, 1))
    if 'D' in snap:
        D = snap['D']; first = int(np.argmax(D))
        out['at_burnthrough'] = dict(t_s=float(snap['t']), x_over_L_first=float(x[first]), D_head_mm=float(D[0] * 1e3),
                                     D_aft_mm=float(D[-1] * 1e3), D_min_mm=float(D.min() * 1e3), D_max_mm=float(D.max() * 1e3),
                                     cells_exposed=int(np.sum(D >= Q.V['D_grain'] - 1e-9)))
    return out


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    fn = os.path.join(outdir, 'b1_axial_law_v2p4.json')
    res = json.load(open(fn)) if os.path.exists(fn) else dict(
        version='v2.4', date='2026-10-13', script='02-combustion/src/b1_axial_law_v2p4.py',
        note='SIM grain_q1d v2 total-mass-flux law variant (sensitivity, not a calibrated law); same a, n as the oxidiser-flux '
             'law re-anchored at r(300 kg/m2s) = 1 mm/s x band; GNC v3 B1 dispersed p99 with throat growth (tg711); S230 25 mm port', runs={})
    for band, n in ((1.0, 0.5), (1.5, 0.35), (1.0, 0.35)):
        key = f'B1p99tg|total|a{band}|n{n}'
        if key in res['runs']:
            continue
        o = run('DC-B1_hop_85m_disp_p99_kest2_tg711_v3', True, band, n, 'total')
        res['runs'][key] = o
        json.dump(res, open(fn, 'w'), indent=1, default=float)
        print(key, json.dumps(o, default=float)[:900], flush=True)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])
