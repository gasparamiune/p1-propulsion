"""Drogue-release hold check (Combustion v2.4, 2026-10-13; coordinator one-line check).

Rule under check (lead/GNC): drogue release = E2 AND [Pc >= 3.0 bar abs OR a rise >= 0.8 bar above the pre-lift baseline
held continuously until E2 + 0.10 s].  E2 = light confirmed by the adopted relative rule (rise >= 0.8 bar over the pre-lift
baseline for 10 ms; here on the measured channel with the 2.3 ms latency of start_latency_v2p4).

Lit side: the plant of ignition_detect_v2p4 part B (grain_q1d v2, pintle held at the v2.8 ignition lift 0.2039 mm, no throttle
ramp: Pc then stays at its lowest level, the ramp only raises it), over states A1 relight / pad 15, 20, 24 C, Cd 0.65 / 0.70 /
0.75, regression law (a x0.6 n 0.68; a x1.0 n 0.50; a x1.5 n 0.35), preheated fraction at main ignition 0 (fuel from zero:
the fuel-starved plateau), 0.15, 0.3, 0.6, eta_c* 0.85 / 0.92.  For each corner: E2, and the minimum rise over [E2, E2 + 0.10 s]
on the true and on the measured channel, with the torch contribution to the pre-lift baseline dP_torch = 0 and 0.3 bar (B-PC-1
target) taken as absent from the lit pressure (torch off or not adding after E2: worst case).  The plant is quasi-steady:
combustion roughness is not modelled; the margin above 0.8 bar is the zero-to-peak roughness the hold tolerates.
Unlit side: ignition_detect_v2p4 part D bounds (gas-phase 190-600 K and the SIL cold model) at the ignition flows.
usage: python -I drogue_hold_check_v2p4.py DATA_V2P4_DIR OUT_JSON
"""
from __future__ import annotations
import hashlib, itertools, json, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ignition_detect_v2p4 as ID
import start_latency_v2p4 as SL

THR = 0.8e5
HOLD = 0.10
TORCH = (0.0, 0.3e5)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def trace(state, Cd, af, n, ri, eta, t_end=0.40, dt=5e-4):
    cfg = dict(SL.law(n, af)); cfg.update(r_ign_frac=ri, eta_cstar=eta, Cd=Cd, t_open_delay=0.0, h_rate=SL.V_PINTLE)
    e = ID.engine(state, cfg)
    e.h = e.h_cmd = e.h_target = ID.H_V28; e.state = 'start'; e.t_on = 0.0; e.Pc = 1.1e5; e.F = 0.0
    if ri <= 0.0:
        e.r_eff[:] = 1e-12
    ts, Ps, OF, mo = [], [], [], []
    t = 0.0
    while t < t_end - 1e-12:
        e.t = t; e.step(dt); t += dt
        ts.append(t); Ps.append(e.Pc); OF.append(e.OF); mo.append(e.mox)
    return np.array(ts), np.array(Ps), np.array(OF), np.array(mo)


def check(ts, Ps, dt=5e-4):
    k_lat = int(round(SL.PC_LAT / dt))
    Pm = np.concatenate([np.full(k_lat, 1.1e5), Ps[:-k_lat]]) if k_lat > 0 else Ps.copy()
    out = {}
    for dpt in TORCH:
        # baseline = PA + dP_torch; lit pressure without the torch term (worst): rise = Pc - PA - dP_torch
        rise_m = Pm - ID.PA - dpt; rise_t = Ps - ID.PA - dpt
        above = None; t2 = None
        for i, t in enumerate(ts):
            if rise_m[i] >= THR:
                above = t if above is None else above
                if t - above >= SL.T_PERSIST:
                    t2 = t; break
            else:
                above = None
        if t2 is None:
            out[f'torch{dpt/1e5:.1f}'] = dict(E2_s=None); continue
        w = (ts >= t2) & (ts <= t2 + HOLD)
        out[f'torch{dpt/1e5:.1f}'] = dict(E2_s=float(t2), rise_min_true_bar=float(rise_t[w].min()) / 1e5, rise_min_measured_bar=float(rise_m[w].min()) / 1e5,
                                          margin_bar=float(min(rise_t[w].min(), rise_m[w].min()) - THR) / 1e5,
                                          Pc_min_abs_bar=float(Ps[w].min()) / 1e5, Pc_at_E2_abs_bar=float(np.interp(t2, ts, Ps)) / 1e5,
                                          hold_ok=bool(min(rise_t[w].min(), rise_m[w].min()) >= THR))
    return out


def main(d, out_f):
    IDJ = json.load(open(os.path.join(d, 'ignition_detect_v2p4.json')))
    laws = ((0.6, 0.68), (1.0, 0.5), (1.5, 0.35))
    rows = []
    for state, Cd, (af, n), ri, eta in itertools.product(('A1_relight', 'pad_15C', 'pad_20C', 'pad_24C'), (0.65, 0.70, 0.75), laws,
                                                          (0.0, 0.15, 0.3, 0.6), (0.85, 0.92)):
        ts, Ps, OF, mo = trace(state, Cd, af, n, ri, eta)
        r = dict(state=state, Cd=Cd, a_fac=af, n=n, r_ign=ri, eta=eta, mox_g_s=1e3 * float(np.mean(mo[-20:])), OF_at_100ms=float(np.interp(0.1, ts, OF)))
        r.update(check(ts, Ps))
        rows.append(r)
    summ = {}
    for dpt in TORCH:
        k = f'torch{dpt/1e5:.1f}'
        ok = [r for r in rows if r[k].get('E2_s') is not None]
        worst = min(ok, key=lambda r: r[k]['margin_bar'])
        summ[k] = dict(n_corners=len(rows), n_E2=len(ok), n_hold_ok=sum(r[k]['hold_ok'] for r in ok),
                       margin_min_bar=worst[k]['margin_bar'], worst_corner={kk: worst[kk] for kk in ('state', 'Cd', 'a_fac', 'n', 'r_ign', 'eta', 'mox_g_s')},
                       worst_rise_min_true_bar=worst[k]['rise_min_true_bar'], worst_Pc_min_abs_bar=worst[k]['Pc_min_abs_bar'],
                       E2_s_range=[min(r[k]['E2_s'] for r in ok), max(r[k]['E2_s'] for r in ok)],
                       margin_pct_of_Pc_at_worst=100.0 * worst[k]['margin_bar'] / worst[k]['Pc_min_abs_bar'],
                       fuel_starved_r0_margin_min_bar=min(r[k]['margin_bar'] for r in ok if r['r_ign'] == 0.0))
    unlit = IDJ['D_unlit']
    unlit_max = max(v['rise_bar'] for mk, mv in unlit.items() if mk.startswith('mox_') for v in mv.values())
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/drogue_hold_check_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={'ignition_detect_v2p4.json': sha16(os.path.join(d, 'ignition_detect_v2p4.json'))},
               rule='E2 AND [Pc >= 3.0 bar abs OR rise >= 0.8 bar held continuously to E2 + 0.10 s]', threshold_bar=THR / 1e5, hold_s=HOLD,
               summary=summ, unlit_rise_max_bar=unlit_max, unlit_bounds=unlit, rows=rows,
               tags=dict(lit='SIM grain_q1d v2 on ASSUMED laws/bands (quasi-steady; roughness not modelled)', unlit='DERIVED gas-phase bound / SIL cold model (Electronics ASSUMED)'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps(summ, indent=1, default=float))
    print('unlit rise max (any bound, 29-42 g/s) %.3f bar' % unlit_max)
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])
