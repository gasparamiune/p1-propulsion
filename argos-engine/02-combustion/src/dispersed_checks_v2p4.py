"""Checks on the six dispersed-cycle outputs (Combustion v2.4, 2026-10-13): this model's Pc against GNC's Pc_Pa, burn
time against the GNC CSV and index, end web, and a head-end heat-load INDEX per BC file so that Mechanical can see which
member of each growth pair loads the head end more. The index is a ranking aid only (DERIVED): the FEA decides.
  Q_conv = int h_g (T_aw - 600 K) dt over burning rows  [J/m2]   (T_aw upper bound; 600 K reference wall, ASSUMED)
  Q_rad  = int q_rad_hi dt                                 [J/m2]
usage: python -I dispersed_checks_v2p4.py DATA_V2_DIR GNC_DC_DIR
"""
from __future__ import annotations
import json, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

CASES = [('DC-B1v3p99', 'DC-B1_hop_85m_disp_p99_kest2_v3'), ('DC-B1v3p99_tg711', 'DC-B1_hop_85m_disp_p99_kest2_tg711_v3'),
         ('DC-B1v3max', 'DC-B1_hop_85m_disp_max_kest2_v3'), ('DC-B1v3max_tg711', 'DC-B1_hop_85m_disp_max_kest2_tg711_v3'),
         ('DC-A1dispp99', 'DC-A1_full_flight_disp_p99_kest2_v3'), ('DC-A1dispp99_tg711', 'DC-A1_full_flight_disp_p99_kest2_tg711_v3')]
T_REF = 600.0


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def main(out, gdir):
    idx = json.load(open(os.path.join(gdir, 'duty_cycles_index_v3.json')))
    meta = {e['name']: e for e in idx['cycles']}
    S = json.load(open(os.path.join(out, 'dc_gncv3', 'summary_v2p4.json')))
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/dispersed_checks_v2p4.py', T_ref_K=T_REF,
               note='Pc ratio: this model (nominal engine, no thrust/Isp dispersion) over GNC Pc_Pa where both burn above 3 bar. '
                    'Heat-load index: ranking aid for the pair choice, not a thermal result (DERIVED).', cases={})
    for tag, name in CASES:
        hist = os.path.join(out, 'dc_gncv3', f'{tag}-S230_neqE1e+03_reg1.csv')
        bc = os.path.join(out, f'headend_bc_{tag}_v2.csv')
        if not (os.path.exists(hist) and os.path.exists(bc)):
            res['cases'][tag] = dict(missing=True); continue
        h = pd.read_csv(hist); g = pd.read_csv(os.path.join(gdir, name + '.csv')); b = pd.read_csv(bc, comment='#')
        gp = np.interp(h.t.values, g.t_s.values, g.Pc_Pa.values); gF = np.interp(h.t.values, g.t_s.values, g.F_cmd_N.values)
        m = (gF > 0) & (gp > 3e5) & (h.Pc.values > 3e5) & (h.t.values <= g.t_s.values[-1])
        r = h.Pc.values[m] / gp[m]
        dtb = np.diff(b.t_s.values, append=b.t_s.values[-1])
        on = b.burning.values > 0
        qc = float(np.sum((b.h_g_face_W_m2K.values * np.clip(b.T_aw_upper_K.values - T_REF, 0, None) * dtb)[on]))
        qr = float(np.sum((b.q_rad_hi_W_m2.values * dtb)[on]))
        e = meta.get(name, {})
        dtg = np.diff(g.t_s.values, append=g.t_s.values[-1])
        s = S.get(f'{tag}-S230_neqE1e+03_reg1', {})
        res['cases'][tag] = dict(
            gnc_file=name + '.csv', gnc_sha256_16=sha16(os.path.join(gdir, name + '.csv')), gnc_index_sha256=e.get('sha256'),
            burn_this_model_s=float(np.sum(dtb[on])), burn_gnc_csv_F_gt_1N_s=float(np.sum(dtg[g.F_N.values > 1.0])),
            burn_gnc_index_s=e.get('burn_time_s'),
            Pc_over_GNC=dict(n=int(m.sum()), p05=float(np.percentile(r, 5)), median=float(np.median(r)), p95=float(np.percentile(r, 95))),
            Pc_max_bar=float(h.Pc.max() / 1e5), w_min_end_mm=float(h.w_min.values[-1] * 1e3), D_port_end_mm=float(h.D_max.values[-1] * 1e3),
            ox_used_kg=s.get('ox_used_kg'), m_liq_end_kg=s.get('m_liq_end_kg'), At_end_over_At0=float(h.At.values[-1] / h.At.values[0]),
            heat_index_conv_MJ_m2=qc / 1e6, heat_index_rad_hi_MJ_m2=qr / 1e6, heat_index_total_MJ_m2=(qc + qr) / 1e6,
            history_csv=os.path.relpath(hist, out), history_sha256_16=sha16(hist), headend_bc_csv=os.path.basename(bc), headend_bc_sha256_16=sha16(bc),
            throat_growth=s.get('throat_growth'))
    for a, bb in (('DC-B1v3p99', 'DC-B1v3p99_tg711'), ('DC-B1v3max', 'DC-B1v3max_tg711'), ('DC-A1dispp99', 'DC-A1dispp99_tg711')):
        ca, cb = res['cases'].get(a, {}), res['cases'].get(bb, {})
        if 'heat_index_total_MJ_m2' in ca and 'heat_index_total_MJ_m2' in cb:
            res.setdefault('pairs', {})[a] = dict(no_growth=ca['heat_index_total_MJ_m2'], growth=cb['heat_index_total_MJ_m2'],
                                                  higher=a if ca['heat_index_total_MJ_m2'] >= cb['heat_index_total_MJ_m2'] else bb)
    fn = os.path.join(out, 'dc_gncv3', 'dispersed_checks_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    for k, v in res['cases'].items():
        print(k, json.dumps({kk: vv for kk, vv in v.items() if kk not in ('throat_growth',)}, default=float)[:900])
    print(json.dumps(res.get('pairs'), default=float))
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
