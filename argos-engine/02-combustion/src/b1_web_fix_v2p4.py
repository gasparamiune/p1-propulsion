"""B1 web burn-through fix study (Combustion v2.4, RC-07; 2026-10-13).

The (a, n) band on GNC's dispersed B1 85 m cycles burns the S230 web through in the high-regression corner
(a x1.5, n 0.35). The grain OD is fixed by the case (53.5 mm grain in a 1.6 mm liner, 6061 case ID 57.15 mm), and the
oxidiser-flux law makes the web consumption independent of the grain length, so the remaining lever inside the case is
the initial port diameter (more web, higher initial flux). This script reruns the B1 cycles at the corners for
D_port0 = 25 (baseline), 22 and 20 mm, same engine model and settings as run_dispersed_v2p4.py (throat growth reproduced
the same way for the _tg711 cycle), and records the web left, the burn-through time, the mean O/F and Isp.
Also records the axial uniformity of the port (D_min/D_max) at burn-through: under the oxidiser-flux law the straight
port regresses uniformly, so the model cannot locate the first burn-through point along the grain.
usage: python -I b1_web_fix_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, os, sys, time
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
import run_dc as RD

H = '/home/claude/work/shared-fallback/engine/01-systems-gnc/duty_cycles'
IDX = os.path.join(H, 'duty_cycles_index_v3.json')
KCF = '/home/claude/work/space/out/throat_growth/throat_growth.json'


def load(name, growth):
    d = pd.read_csv(os.path.join(H, name + '.csv'))
    meta = {e['name']: e for e in json.load(open(IDX))['cycles']}[name]
    dc = dict(t=d.t_s.values, F_cmd=d.F_cmd_N.values, a_axial=d.a_axial_specific_mps2.values)
    At_hist = None
    if growth:
        K = json.load(open(KCF))['k_cf']
        tt = d.t_s.values; Fc = d.F_cmd_N.values
        dtt = np.diff(tt, prepend=tt[0] - (tt[1] - tt[0]))
        J = np.cumsum(np.where(Fc > 0, (np.clip(Fc, 0, None) / 500.0) ** 0.68, 0.0) * dtt)
        g = meta['dispersions']['throat_g'] * np.minimum(1.0, J / meta['throat_jref'])
        kc = np.interp(np.clip(Fc, 0, None) / 500.0, K['thrust_frac'], K['v'])
        dc['F_cmd'] = np.where(Fc > 0, Fc * (1 + g) * (1 + kc * g), Fc)
        At0 = np.pi * Q.V['Dt0'] ** 2 / 4
        At_hist = lambda t, _t=tt, _g=g, _A=At0: _A * (1.0 + float(np.interp(t, _t, _g)))
    return d, meta, dc, At_hist


def run(name, growth, band, n, Dp):
    d, meta, dc, At_hist = load(name, growth)
    tk = RD.make_tank('neq', meta['tank_V_m3'], meta['m_n2o_kg'], float(d.T_tank_K.iloc[0]), 1e3)
    cfg = dict(a=1.0e-3 / 300.0 ** n * band, n=n, D_port0=Dp)
    snap = {}
    orig = Q.Engine.step

    def step(self, dt, a_axial=Q.G0):
        F = orig(self, dt, a_axial)
        if self.burnthrough is not None and 'D' not in snap:
            snap['D'] = self.D.copy(); snap['t'] = self.t
        return F
    Q.Engine.step = step
    try:
        t0 = time.time()
        rec, e = Q.simulate(dc, tk, cfg=cfg, init_running=bool(d.F_cmd_N.iloc[0] > 0), At_hist=At_hist)
    finally:
        Q.Engine.step = orig
    r = pd.DataFrame(rec)
    on = (r.mox > 1e-4) & (r.Pc > 1.5e5)
    out = dict(cycle=name, growth=growth, a_band=band, n=n, D_port0_m=Dp, initial_web_mm=(0.0535 - Dp) / 2 * 1e3,
               w_min_end_mm=float(r.w_min.values[-1] * 1e3), burnthrough_s=e.burnthrough, burn_s=float(on.sum() * 0.01),
               OF_mean=float((r.mox[on].sum()) / max(r.mf[on].sum(), 1e-9)), Isp_mean_s=float(np.nanmean(r.Isp[on])),
               fuel_used_kg=float(e.fuel_burnt), ox_used_kg=float(e.ox_used), grain_mass_kg=float(1000.0 * np.pi / 4 * (0.0535 ** 2 - Dp ** 2) * 0.23),
               wall_s=round(time.time() - t0, 1))
    if 'D' in snap:
        out['at_burnthrough'] = dict(t_s=snap['t'], D_min_mm=float(snap['D'].min() * 1e3), D_max_mm=float(snap['D'].max() * 1e3),
                                     cell_first_x_frac=float((np.argmax(snap['D']) + 0.5) / len(snap['D'])))
    return out


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    fn = os.path.join(outdir, 'b1_web_fix_v2p4.json')
    res = json.load(open(fn)) if os.path.exists(fn) else dict(version='v2.4', date='2026-10-13', script='02-combustion/src/b1_web_fix_v2p4.py',
                                                              note='SIM grain_q1d v2, re-anchored laws r(300 kg/m2s) = 1 mm/s, neq tank E 1e3 '
                                                                   '(GNC index tank), S230 OD 53.5 mm x 230 mm; growth as run_dispersed_v2p4', runs={})
    plan = []
    for Dp in (0.022, 0.020):
        for band, n in ((1.5, 0.35), (1.5, 0.5), (1.0, 0.35), (1.0, 0.5), (0.6, 0.68)):
            plan.append(('DC-B1_hop_85m_disp_p99_kest2_tg711_v3', True, band, n, Dp))
        plan.append(('DC-B1_hop_85m_disp_max_kest2_v3', False, 1.5, 0.35, Dp))
    plan.append(('DC-B1_hop_85m_disp_p99_kest2_tg711_v3', True, 1.5, 0.35, 0.025))
    for p in plan:
        key = f'{p[0]}|g{int(p[1])}|a{p[2]}|n{p[3]}|Dp{p[4]*1e3:.0f}mm'
        if key in res['runs']:
            continue
        o = run(*p)
        res['runs'][key] = o
        json.dump(res, open(fn, 'w'), indent=1, default=float)
        print(key, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in o.items() if k not in ('cycle',)}, default=float), flush=True)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])
