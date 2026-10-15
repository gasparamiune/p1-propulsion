"""B1 62 m: regression-law runs for the gating-rule check with a selectable axial law (Combustion v2.4, RC-07; 2026-10-13).

Same engine, tank, cycle handling and throat-growth reproduction as run_dispersed_v2p4 v2.4c (imported: find_meta, sha16,
KCF_DEFAULT; the growth block below is the same arithmetic), plus grain_q1d's law option:
  law 'ox'    r = a G_ox^n                       (baseline; must reproduce run_dispersed_v2p4 -> check run)
  law 'total' r = a (G_ox + G_fuel,cum(x))^n     (same a and n: equal head-end rate, faster downstream; SENSITIVITY,
                                                   not a calibrated law; head-end spray enhancement is not modelled)
a = 1 mm/s x band / 300^n (re-anchored at r(300 kg/m2s) = band x 1 mm/s), as run_dispersed_v2p4 --n.
Writes the grain_q1d history CSV (same columns as run_dispersed_v2p4) and a summary entry with t(w_min = 1 mm), the
oxidiser mass and int Pc dt at that time, the port profile at the end, and where the minimum web sits.
usage: python -I b1_62m_axial_v2p4.py --dc PATH --tag TAG --index PATH --band A --n N --law total|ox --out DATA_V2_DIR
       --sub SUBDIR [--throat-growth [--kcf PATH]]
"""
from __future__ import annotations
import argparse, json, os, sys, time
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
import run_dc as RD
import run_dispersed_v2p4 as RDV


def t_at_web(t, w, target):
    """First time the minimum web reaches target (linear interpolation); None if never."""
    idx = np.where(w <= target)[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    if i == 0:
        return float(t[0])
    return float(t[i - 1] + (target - w[i - 1]) * (t[i] - t[i - 1]) / (w[i] - w[i - 1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dc', required=True); ap.add_argument('--tag', required=True); ap.add_argument('--index', required=True)
    ap.add_argument('--band', type=float, required=True); ap.add_argument('--n', type=float, required=True)
    ap.add_argument('--law', choices=['ox', 'total'], required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--sub', required=True)
    ap.add_argument('--throat-growth', action='store_true'); ap.add_argument('--kcf', default=RDV.KCF_DEFAULT)
    a = ap.parse_args()
    out_hist = os.path.join(a.out, a.sub); os.makedirs(out_hist, exist_ok=True)
    d = pd.read_csv(a.dc, comment='#')
    dc = dict(t=d.t_s.values, F_cmd=d.F_cmd_N.values, a_axial=d.a_axial_specific_mps2.values)
    meta, idxf = RDV.find_meta(a.dc, a.index)
    if not meta:
        raise SystemExit('no index entry for ' + a.dc)
    At_hist = None; tg = None
    if a.throat_growth:   # identical arithmetic to run_dispersed_v2p4 v2.4c --throat-growth
        g_end = float((meta.get('dispersions') or {}).get('throat_g') or 0.0)
        jref = float(meta.get('throat_jref') or (meta.get('config') or {}).get('throat_jref') or 0.0)
        if g_end <= 0 or jref <= 0 or int((meta.get('config') or {}).get('throat_loop', 1)) != 1:
            raise SystemExit('--throat-growth needs throat_g > 0, throat_jref > 0, throat_loop 1')
        K = json.load(open(a.kcf))['k_cf']
        tt = d.t_s.values; Fc = d.F_cmd_N.values
        dtt = np.diff(tt, prepend=tt[0] - (tt[1] - tt[0]))
        J = np.cumsum(np.where(Fc > 0, (np.clip(Fc, 0, None) / 500.0) ** 0.68, 0.0) * dtt)
        g = g_end * np.minimum(1.0, J / jref)
        kc = np.interp(np.clip(Fc, 0, None) / 500.0, K['thrust_frac'], K['v'])
        dc['F_cmd'] = np.where(Fc > 0, Fc * (1 + g) * (1 + kc * g), Fc)
        At0 = np.pi * Q.V['Dt0'] ** 2 / 4
        At_hist = lambda t, _t=tt, _g=g, _A=At0: _A * (1.0 + float(np.interp(t, _t, _g)))
        tg = dict(throat_g=g_end, J_ref=jref, J_end=float(J[-1]))
    V, m = meta['tank_V_m3'], meta['m_n2o_kg']
    T0 = float(d.T_tank_K.iloc[0])
    tk = RD.make_tank('neq', V, m, T0, 1e3)
    cfg = dict(a=1.0e-3 / 300.0 ** a.n * a.band, n=a.n, law=a.law)
    t0 = time.time()
    rec, e = Q.simulate(dc, tk, cfg=cfg, init_running=bool(d.F_cmd_N.iloc[0] > 0), At_hist=At_hist)
    if tg is not None:
        for r in rec:
            r['F_cmd'] = float(np.interp(r['t'], d.t_s.values, d.F_cmd_N.values)) if r['t'] <= d.t_s.values[-1] else 0.0
    tag = f'{a.tag}-S230_neqE1e+03_reg{a.band:g}_n{a.n:g}_law{a.law}'
    s = RD.summarize(rec, e, tag, dict(tank=f'neq E=1000 V={V*1e3:.3f} L m={m} kg (GNC index {os.path.basename(idxf)})',
                                        regression_scale=a.band, n=a.n, law=a.law, wall_s=round(time.time() - t0, 1),
                                        gnc_burn_s=meta.get('burn_time_s'), source_dc=os.path.abspath(a.dc),
                                        source_dc_sha256_16=RDV.sha16(a.dc), T0_K=T0,
                                        script_sha256_16=RDV.sha16(os.path.abspath(__file__))))
    if tg is not None:
        s['throat_growth'] = tg
    r = pd.DataFrame(rec)
    t = r.t.values; w = r.w_min.values
    dt = np.diff(t, prepend=t[0])
    t1 = t_at_web(t, w, 1.0e-3)
    s['t_w1mm_s'] = t1
    if t1 is not None:
        k = t <= t1
        s['m_ox_at_w1mm_kg'] = float(np.sum(r.mox.values[k] * dt[k]))
        s['intPc_at_w1mm_Pa_s'] = float(np.sum(r.Pc.values[k] * dt[k]))
    Nc = len(e.D); x = (np.arange(Nc) + 0.5) / Nc; Dend = np.array(e.D)
    s['D_end_head_mm'] = float(Dend[0] * 1e3); s['D_end_aft_mm'] = float(Dend[-1] * 1e3)
    s['x_over_L_of_max_D_end'] = float(x[int(np.argmax(Dend))])
    hist = os.path.join(out_hist, tag + '.csv')
    r.to_csv(hist, index=False, float_format='%.6g')
    s['history_csv'] = os.path.relpath(hist, a.out); s['history_sha256_16'] = RDV.sha16(hist)
    sf = os.path.join(out_hist, 'summary_v2p4.json')
    S = json.load(open(sf)) if os.path.exists(sf) else {}
    S[tag] = s
    json.dump(S, open(sf, 'w'), indent=1, default=float)
    print(json.dumps(s, default=float), flush=True)


if __name__ == '__main__':
    main()
