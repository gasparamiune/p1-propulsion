"""Processed duty-cycle history + head-end BC series for a new GNC duty cycle (Combustion v2.4, 2026-10-13).

Lead request 2026-10-13: Mechanical's thermal FEA needs, for GNC's dispersed cycles (DC-B1 v3 p99, DC-B1 v3 max,
DC-A1 dispersed p99), exactly the v2 file formats:
  * the processed DC history (layout of data/v2/dc_gncv2wip/DC-*-S230v2wip_neqE1e+03_reg1.csv: grain_q1d v2 record with
    port diameters D_min/D_max, web w_min, Pc, mox, mf, tank state ...), and
  * headend_bc_<TAG>_v2.csv (h_g, T_aw upper bound, q_rad band, N2O-side h_c, burning flag), written by the same code
    path as headend_thermal_v2.py (BC class, phases, n2o_hc; thermal_bc_*_v2.csv rows at x_face 0).
Engine model and settings identical to the v2 runs: S230 grain, non-equilibrium tank E 1e3, nominal regression law
(a x band, n 0.5 unless --n is given, re-anchored at r(300) = 1 mm/s), eta_c* 0.92, Cd 0.70, combustion.json v2.3.
Tank: from the GNC index entry when one is given/found (tank_V_m3, m_n2o_kg), else the baseline 3.17 L / 2.0018 kg
(LEAD) with the CSV's first T_tank_K.
usage: python -I run_dispersed_v2p4.py --dc PATH --tag TAG [--index PATH] [--band 1.0] [--n 0.5] [--out DATA_V2_DIR]
       [--no-bc] [--throat-growth [--kcf PATH]]
--throat-growth (v2.4b, for GNC's _tg711 cycles): reproduces GNC sim6 v2.7's in-flight throat growth with the ECU Pc loop
holding Pc on the nominal map (throat_loop 1): At = At0 (1 + g), g = throat_g min(1, J/J_ref), J = int (F_cmd/500)^0.68 dt
while F_cmd > 0 (GNC integrates F/tsc, the Pc-equivalent thrust; the F_cmd form reproduces GNC's J_end within 0.6 %),
throat_g and J_ref from the index entry; the engine is driven with the Pc-hold-equivalent thrust
F_cmd (1 + g)(1 + k_cf g) (k_cf from GNC throat_growth.json, 1-D nozzle) so that Pc follows the nominal map while the
throat grows; the recorded F_cmd column is GNC's command. Pc / GNC Pc_Pa is reported for every run as a check.
v2.4c (2026-10-13, B1 62 m records): find_meta also searches an index's 'records' list (GNC duty_cycles_records_b1_62m_v3.1
names its entries there and gives 'file' as a hub path) after 'cycles', so earlier runs resolve to the same entries; J_ref
falls back to config.throat_jref when the entry has no top-level throat_jref. No model change.
"""
from __future__ import annotations
import argparse, csv, json, os, sys, time, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
import run_dc as RD
import headend_thermal_v2 as HT

BASE_TANK = dict(V=3.169952601830201e-3, m=2.0018029785156246, tag='LEAD baseline 2.00 kg / 3.17 L (no index entry found)')
KCF_DEFAULT = '/home/claude/work/space/out/throat_growth/throat_growth.json'   # GNC m2_throat_mc v1 (k_cf, j_ref)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def find_meta(dc_path, index_path=None):
    name = os.path.splitext(os.path.basename(dc_path))[0]
    cands = [index_path] if index_path else [os.path.join(os.path.dirname(dc_path), f) for f in sorted(os.listdir(os.path.dirname(dc_path)))
                                              if f.startswith('duty_cycles_index') and f.endswith('.json')]
    for c in cands:
        if not c or not os.path.exists(c):
            continue
        try:
            idx = json.load(open(c))
        except Exception:
            continue
        for e in list(idx.get('cycles', [])) + list(idx.get('records', [])):   # v2.4c: GNC record indexes use 'records'
            if e.get('name') == name or os.path.basename(str(e.get('file'))) == os.path.basename(dc_path):
                return e, c
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dc', required=True); ap.add_argument('--tag', required=True); ap.add_argument('--index')
    ap.add_argument('--band', type=float, default=1.0); ap.add_argument('--n', type=float, default=None)
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'data', 'v2')); ap.add_argument('--sub', default='dc_gncv3')
    ap.add_argument('--no-bc', action='store_true'); ap.add_argument('--throat-growth', action='store_true')
    ap.add_argument('--kcf', default=KCF_DEFAULT)
    a = ap.parse_args()
    out_hist = os.path.join(a.out, a.sub); os.makedirs(out_hist, exist_ok=True)
    d = pd.read_csv(a.dc, comment='#')
    dc = dict(t=d.t_s.values, F_cmd=d.F_cmd_N.values, a_axial=d.a_axial_specific_mps2.values)
    meta, idxf = find_meta(a.dc, a.index)
    tg = None; At_hist = None
    if a.throat_growth:
        g_end = float(((meta or {}).get('dispersions') or {}).get('throat_g') or 0.0)
        jref = float((meta or {}).get('throat_jref') or ((meta or {}).get('config') or {}).get('throat_jref') or 0.0)   # v2.4c fallback
        loop = int(((meta or {}).get('config') or {}).get('throat_loop', 1))
        if g_end <= 0 or jref <= 0 or loop != 1:
            raise SystemExit(f'--throat-growth needs an index entry with throat_g > 0, throat_jref > 0 and throat_loop 1 '
                             f'(got g {g_end}, J_ref {jref}, loop {loop})')
        K = json.load(open(a.kcf))['k_cf']
        tt = d.t_s.values; Fc = d.F_cmd_N.values
        dtt = np.diff(tt, prepend=tt[0] - (tt[1] - tt[0]))
        J = np.cumsum(np.where(Fc > 0, (np.clip(Fc, 0, None) / 500.0) ** 0.68, 0.0) * dtt)
        g = g_end * np.minimum(1.0, J / jref)
        kc = np.interp(np.clip(Fc, 0, None) / 500.0, K['thrust_frac'], K['v'])
        F_eff = np.where(Fc > 0, Fc * (1 + g) * (1 + kc * g), Fc)
        At0 = np.pi * Q.V['Dt0'] ** 2 / 4
        At_hist = lambda t, _t=tt, _g=g, _A=At0: _A * (1.0 + float(np.interp(t, _t, _g)))
        dc['F_cmd'] = F_eff
        tg = dict(method='GNC sim6 v2.7 throat_loop 1 (Pc held on the nominal map) reproduced: At = At0 (1 + g), '
                         'g = throat_g min(1, J/J_ref), J = int (F_cmd/500)^0.68 dt, engine driven with F_cmd (1+g)(1+k_cf g)',
                  throat_g=g_end, J_ref=jref, J_end=float(J[-1]), J_end_gnc=((meta or {}).get('summary') or {}).get('throat_J'),
                  g_end_gnc=((meta or {}).get('summary') or {}).get('throat_g_end'), t_g_saturates_s=(float(tt[np.argmax(J >= jref)]) if J[-1] >= jref else None),
                  k_cf=K, k_cf_source=os.path.abspath(a.kcf), k_cf_source_sha256_16=sha16(a.kcf), tag='DERIVED from GNC SIM inputs')
    if meta and 'tank_V_m3' in meta and 'm_n2o_kg' in meta:
        V, m, ttag = meta['tank_V_m3'], meta['m_n2o_kg'], f'GNC index {os.path.basename(idxf)}'
    else:
        V, m, ttag = BASE_TANK['V'], BASE_TANK['m'], BASE_TANK['tag']
    T0 = float(d.T_tank_K.iloc[0]) if 'T_tank_K' in d and np.isfinite(d.T_tank_K.iloc[0]) else 293.15
    tk = RD.make_tank('neq', V, m, T0, 1e3)
    cfg = {}
    if a.n is None:
        cfg['a'] = Q.V['a'] * a.band
    else:
        cfg['a'] = 1.0e-3 / 300.0 ** a.n * a.band; cfg['n'] = a.n
    init_run = bool(d.F_cmd_N.iloc[0] > 0)
    t0 = time.time()
    rec, e = Q.simulate(dc, tk, cfg=cfg, init_running=init_run, At_hist=At_hist)
    if tg is not None:   # recorded F_cmd = GNC's command (the engine was driven with the Pc-hold-equivalent thrust)
        for r in rec:
            r['F_cmd'] = float(np.interp(r['t'], d.t_s.values, d.F_cmd_N.values)) if r['t'] <= d.t_s.values[-1] else 0.0
    ntag = '' if a.n is None else f'_n{a.n:g}'
    tag = f'{a.tag}-S230_neqE1e+03_reg{a.band:g}{ntag}'
    s = RD.summarize(rec, e, tag, dict(tank=f'neq E=1000 V={V*1e3:.3f} L m={m} kg ({ttag})', regression_scale=a.band,
                                        n=a.n if a.n is not None else 0.5, wall_s=round(time.time() - t0, 1),
                                        gnc_burn_s=(meta or {}).get('burn_time_s'), source_dc=os.path.abspath(a.dc),
                                        source_dc_sha256_16=sha16(a.dc), T0_K=T0,
                                        script_sha256_16=sha16(os.path.abspath(__file__))))
    if tg is not None:
        s['throat_growth'] = tg; s['At_end_over_At0'] = float(rec[-1]['At'] / (np.pi * Q.V['Dt0'] ** 2 / 4))
    # check: this model's Pc against GNC's Pc_Pa (combustion.json v2.3 map) where both burn
    try:
        rt = np.array([r['t'] for r in rec]); rp = np.array([r['Pc'] for r in rec])
        gp = np.interp(rt, d.t_s.values, d.Pc_Pa.values); gF = np.interp(rt, d.t_s.values, d.F_cmd_N.values)
        msk = (gF > 0) & (gp > 3e5) & (rp > 3e5) & (rt <= d.t_s.values[-1])
        ratio = rp[msk] / gp[msk]
        s['Pc_over_GNC_Pc'] = dict(n=int(msk.sum()), p05=float(np.percentile(ratio, 5)), median=float(np.median(ratio)),
                                   p95=float(np.percentile(ratio, 95)), note='GNC Pc_Pa includes its thrust_scale / isp_scale '
                                   'dispersions and actuator dynamics; this model uses the nominal engine (DERIVED check)')
    except Exception as ex:
        s['Pc_over_GNC_Pc'] = dict(error=str(ex))
    hist = os.path.join(out_hist, tag + '.csv')
    pd.DataFrame(rec).to_csv(hist, index=False, float_format='%.6g')
    s['history_csv'] = os.path.relpath(hist, a.out); s['history_sha256_16'] = sha16(hist)
    if not a.no_bc and a.band == 1.0 and a.n is None:
        rows = HT.bc_points(a.out); bcf = HT.BC(rows); At0_bc = np.pi * Q.V['Dt0'] ** 2 / 4
        dd = pd.read_csv(hist, comment='#')
        t = dd.t.values; Pc = dd.Pc.values; mox = dd.mox.values
        burning, segs = HT.phases(t, Pc, mox)
        bc_rows = []
        for i in range(0, len(t), 1 if len(t) < 6000 else 2):
            on = bool(burning[i])
            h, Taw, qlo, qhi = bcf(Pc[i]) if on else (0.0, float('nan'), 0.0, 0.0)
            if tg is not None and on:   # grown throat at the same Pc: face mass flux x (1+g), h_g ~ G^0.8
                h *= (float(dd.At.values[i]) / At0_bc) ** 0.8
            hc = HT.n2o_hc(float(dd.T_tank.values[i]), float(mox[i]))[0] if mox[i] > 1e-4 else float('nan')
            bc_rows.append(dict(t_s=t[i], burning=int(on), Pc_Pa=Pc[i], mdot_ox_kg_s=mox[i], T_N2O_liquid_K=dd.T_tank.values[i],
                                h_g_face_W_m2K=h, T_aw_upper_K=Taw, q_rad_lo_W_m2=qlo, q_rad_hi_W_m2=qhi, h_c_N2O_W_m2K=hc))
        out_csv = os.path.join(a.out, f'headend_bc_{a.tag}_v2.csv')
        with open(out_csv, 'w', newline='') as f:
            f.write('# Head-end BC time series v2.2b (x1; apply x0.5-2 to h_g, q_rad picks lo/hi): injector face and pre-chamber '
                    'wall gas side while burning (Bartz at x_face 0 from thermal_bc_*_v2.csv, T_aw = delivered T0 = UPPER '
                    'BOUND; gas radiation = incident term), plus radiative exchange face<->insulator F 0.65 / face<->grain end F 0.35, '
                    'emissivity 0.8, grain 750 K burning; N2O-side h_c on the CAD v3.2 manifold annulus (10/6 mm) during flow; '
                    'outside burns see headend_thermal_v2.json (coast: h_nc 10 W/m2K to the insulator temperature + the same '
                    'radiative exchange, grain 700 K at shutdown decaying 1 s; soak: no N2O credit). Source DC: '
                    + os.path.relpath(hist, a.out)
                    + ('' if tg is None else f' (in-flight throat growth to g {tg["throat_g"]:.4f} per GNC sim6 v2.7, Pc held on '
                       'the nominal map; face mass flux x (1+g) at the same Pc, so h_g = Bartz face value at Pc x (At/At0)^0.8, '
                       'DERIVED; T_aw and q_rad unchanged at the same Pc and O/F)')
                    + '. SI units. DERIVED.\n')
            w = csv.DictWriter(f, fieldnames=list(bc_rows[0].keys())); w.writeheader(); w.writerows(bc_rows)
        s['headend_bc_csv'] = os.path.basename(out_csv); s['headend_bc_sha256_16'] = sha16(out_csv)
        s['burn_segments_s'] = [[float(t[i0]), float(t[i1])] for i0, i1 in segs]
    sf = os.path.join(out_hist, 'summary_v2p4.json')
    S = json.load(open(sf)) if os.path.exists(sf) else {}
    S[tag] = s
    json.dump(S, open(sf, 'w'), indent=1, default=float)
    print(json.dumps(s, default=float), flush=True)


if __name__ == '__main__':
    main()
