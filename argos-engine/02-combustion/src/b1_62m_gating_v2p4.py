"""B1 62 m gating-rule check (Combustion v2.4, RC-07; 2026-10-13). DERIVED from SIM histories + GNC MC tables.

Gating rule (LEAD adopted 2026-10-13): B1 flies only after the T1-T4 regression law; burn limit t_L = t(w_min = 1 mm)
computed with 1.1 x measured a; grain change if a >= 1.25 x nominal with n <= 0.4.
This script, for the GNC v3.1 62 m records (staging_v3.1/duty_cycles, index duty_cycles_records_b1_62m_v3.1.json):
  1. merges the lane summaries of run_dispersed_v2p4 (lanes A-D) and b1_62m_axial_v2p4 (lanes TC, TD) into
     dc_gncv31_62m/summary_v2p4.json (lane recorded per entry);
  2. from each history CSV: t(w_min = 1 mm), t(w_min = 0.5 mm), burn-through time, oxidiser mass and int Pc dt at
     w = 1 mm, oxidiser-flux range and the share of the consumed web burnt below G_ox = 100 kg/m2s;
  3. the rule's limits per record: t_L for measured a = 1.0 (run at a x1.1, n 0.35), measured a just below 1.25 with
     n 0.35 (run at a x1.375) and measured a = 1.5 with n 0.5 (run at a x1.65); the web left at t_L when the true law
     equals the measured one (a x1.25 n 0.35; a x1.5 n 0.5; a x1.0 n 0.35); the same with the total-flux axial law;
  4. the fraction of the GNC 62 m Monte Carlo runs whose thrust-on time exceeds each t_L and each a x1.5 n 0.35
     burn-through time. Thrust-on = GNC burn_time counter + offset; the offset is DERIVED per MC file as
     (max-record thrust-on from the record index) - max(burn_time).
usage: python -I b1_62m_gating_v2p4.py DATA_V2_DIR MC_NONE_CSV_GZ MC_PC_CSV_GZ GNC_RECORD_INDEX OUT_JSON
"""
from __future__ import annotations
import json, os, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

SUB = 'dc_gncv31_62m'
LANES = ['laneA', 'laneB', 'laneC', 'laneD', 'laneTC', 'laneTD']
RECS = {'p99': 'DC-B1v31_62m_p99', 'max': 'DC-B1v31_62m_max',
        'p99_tg711': 'DC-B1v31_62m_p99_tg711', 'max_tg711': 'DC-B1v31_62m_max_tg711'}
MC_OF_REC = {'p99': 'none', 'max': 'none', 'p99_tg711': 'pc', 'max_tg711': 'pc'}


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def t_at_web(t, w, target):
    idx = np.where(w <= target)[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    if i == 0:
        return float(t[0])
    return float(t[i - 1] + (target - w[i - 1]) * (t[i] - t[i - 1]) / (w[i] - w[i - 1]))


def key(rec, band, n, law=None):
    base = f'{RECS[rec]}-S230_neqE1e+03_reg{band:g}_n{n:g}'
    return base if law in (None, 'oxRD') else base + f'_law{law}'


def hist_metrics(data_v2, s):
    fn = os.path.join(data_v2, s['history_csv'])
    h = pd.read_csv(fn)
    t = h.t.values; w = h.w_min.values; dt = np.diff(t, prepend=t[0])
    on = (h.mox.values > 1e-4) & (h.Pc.values > 1.5e5)
    out = dict(history_sha256_16_check=sha16(fn) == s['history_sha256_16'])
    out['t_w1mm_s'] = t_at_web(t, w, 1.0e-3); out['t_w0p5mm_s'] = t_at_web(t, w, 0.5e-3); out['t_w0_s'] = t_at_web(t, w, 0.0)
    if out['t_w1mm_s'] is not None:
        k = t <= out['t_w1mm_s']
        out['m_ox_at_w1mm_kg'] = float(np.sum(h.mox.values[k] * dt[k]))
        out['intPc_at_w1mm_MPa_s'] = float(np.sum(h.Pc.values[k] * dt[k]) / 1e6)
    D = h.D_max.values
    G = np.where(on, h.mox.values / (np.pi / 4 * D ** 2), np.nan)
    out['G_ox_range_kg_m2s'] = [float(np.nanmin(G)), float(np.nanmax(G))]
    dw = np.clip(-np.diff(w, prepend=w[0]), 0, None)
    tot = float(dw[on].sum())
    out['web_consumed_mm'] = tot * 1e3
    out['share_of_web_burnt_below_G100'] = float(dw[on & (G < 100)].sum() / tot) if tot > 0 else None
    out['share_of_web_burnt_below_G50'] = float(dw[on & (G < 50)].sum() / tot) if tot > 0 else None
    return out, h


def web_at(h, t):
    return float(np.interp(t, h.t.values, h.w_min.values) * 1e3)


def main(data_v2, mc_none, mc_pc, rec_index, out_json):
    merged = {}
    for L in LANES:
        sf = os.path.join(data_v2, SUB, L, 'summary_v2p4.json')
        if not os.path.exists(sf):
            continue
        for k, v in json.load(open(sf)).items():
            if k in merged:
                raise SystemExit(f'duplicate case {k} in {L} and {merged[k]["lane"]}')
            v = dict(v); v['lane'] = L
            merged[k] = v
    json.dump(merged, open(os.path.join(data_v2, SUB, 'summary_v2p4.json'), 'w'), indent=1, default=float)
    cases = {}; H = {}
    for k, v in merged.items():
        m, h = hist_metrics(data_v2, v)
        H[k] = h
        cases[k] = dict(record=next((r for r, nm in RECS.items() if k.startswith(nm + '-')), None), a_band=v['regression_scale'],
                        n=v['n'], law=v.get('law', 'ox'), lane=v['lane'], burn_s=v['burn_s'], gnc_thrust_on_s=v['gnc_burn_s'],
                        burnthrough_s=v['burnthrough_s'], w_min_end_mm=v['w_min_end_mm'], m_liq_end_kg=v['m_liq_end_kg'],
                        fuel_used_kg=v.get('fuel_used_kg'), OF_mean=v.get('OF_mean'), Pc_over_GNC_Pc_median=(v.get('Pc_over_GNC_Pc') or {}).get('median'),
                        history_csv=v['history_csv'], **m)
    # reproduction check: law 'ox' through b1_62m_axial_v2p4 against run_dispersed_v2p4 (same record, band, n)
    checks = {}
    for k, v in cases.items():
        if v['law'] == 'ox' and v['lane'].startswith('laneT'):
            ref = k.replace('_lawox', '')
            if ref in H:
                a, b = H[k], H[ref]
                nmin = min(len(a), len(b))
                checks[k] = dict(reference=ref, max_abs_dw_mm=float(np.max(np.abs(a.w_min.values[:nmin] - b.w_min.values[:nmin])) * 1e3),
                                 max_abs_dPc_Pa=float(np.max(np.abs(a.Pc.values[:nmin] - b.Pc.values[:nmin]))),
                                 burnthrough_s=[v['burnthrough_s'], cases[ref]['burnthrough_s']], rows=[len(a), len(b)])
    # MC exceedance
    idx = json.load(open(rec_index))
    recs = {e.get('name'): e for e in idx.get('records', [])}
    mc = {}
    for lab, fn in (('none', mc_none), ('pc', mc_pc)):
        df = pd.read_csv(fn)
        bt = df.burn_time.values.astype(float)
        mrec = 'DC-B1_hop_62m_disp_max_kest2_v3' if lab == 'none' else 'DC-B1_hop_62m_disp_max_kest2_tg711_v3'
        rec_max = float((recs.get(mrec) or {}).get('burn_time_s') or np.nan)
        off = rec_max - float(np.max(bt))
        ton = bt + off
        mc[lab] = dict(file=fn, sha256_16=sha16(fn), n_runs=int(len(bt)), max_record=mrec, max_record_thrust_on_s=rec_max,
                       offset_s=off, thrust_on_p50_p90_p99_max=[float(np.percentile(ton, q)) for q in (50, 90, 99)] + [float(ton.max())],
                       _ton=ton)

    def frac(lab, t):
        ton = mc[lab]['_ton']
        return float(np.mean(ton > t))
    # gating table per record
    gate = {}
    for r in RECS:
        lab = MC_OF_REC[r]; g = {}
        rows = [('nominal_measured_a1.0_n0.35', (1.1, 0.35), (1.0, 0.35)),
                ('measured_a_just_below_1.25_n0.35', (1.375, 0.35), (1.25, 0.35)),
                ('measured_a1.5_n0.5', (1.65, 0.5), (1.5, 0.5))]
        for name, lim, true in rows:
            kL = key(r, *lim); kT = key(r, *true)
            ent = dict(limit_case=kL, true_law_case=kT)
            if kL in cases:
                tL = cases[kL]['t_w1mm_s']
                ent['t_L_s'] = tL
                ent['m_ox_at_t_L_kg'] = cases[kL].get('m_ox_at_w1mm_kg'); ent['intPc_at_t_L_MPa_s'] = cases[kL].get('intPc_at_w1mm_MPa_s')
                ent['record_thrust_on_s'] = cases[kL]['gnc_thrust_on_s']
                if tL is not None:
                    ent['record_exceeds_t_L'] = bool(cases[kL]['gnc_thrust_on_s'] > tL)
                    ent['mc_fraction_thrust_on_gt_t_L'] = frac(lab, tL)
                    if kT in H:
                        ent['web_at_t_L_true_law_mm'] = web_at(H[kT], tL)
                else:
                    ent['note'] = 'w_min stays above 1 mm for the whole record: the limit does not bind on this record'
                    ent['web_end_limit_case_mm'] = cases[kL]['w_min_end_mm']
            for law in ('total',):
                kLt = key(r, *lim, law=law)
                if kLt in cases:
                    ent[f't_L_{law}_law_s'] = cases[kLt]['t_w1mm_s']
                    ent[f'burnthrough_{law}_law_s'] = cases[kLt]['burnthrough_s']
                    if cases[kLt]['t_w1mm_s'] is not None:
                        ent[f'mc_fraction_thrust_on_gt_t_L_{law}_law'] = frac(lab, cases[kLt]['t_w1mm_s'])
                    if 't_L_s' in ent and ent['t_L_s'] is not None and cases[kLt]['t_w1mm_s'] is not None:
                        ent[f'web_at_ox_law_t_L_if_{law}_law_true_mm'] = web_at(H[kLt], ent['t_L_s'])
            g[name] = ent
        k15 = key(r, 1.5, 0.35)
        if k15 in cases and cases[k15]['burnthrough_s'] is not None:
            g['corner_a1.5_n0.35_burnthrough'] = dict(case=k15, burnthrough_s=cases[k15]['burnthrough_s'],
                                                      mc_fraction_thrust_on_gt_burnthrough=frac(lab, cases[k15]['burnthrough_s']),
                                                      covered_by='grain-change branch (a >= 1.25 x nominal with n <= 0.4): this grain does not fly')
        gate[r] = g
    for lab in mc:
        mc[lab].pop('_ton')
    thr = {}
    for lab in ('none', 'pc'):
        df = pd.read_csv(mc[lab]['file']); ton = df.burn_time.values.astype(float) + mc[lab]['offset_s']
        thr[lab] = {f'{x:.1f}': float(np.mean(ton > x)) for x in np.arange(15.0, 21.01, 0.5)}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/b1_62m_gating_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               tag='DERIVED (from SIM grain_q1d v2 histories driven by GNC v3.1 62 m records, and GNC SIM MC tables)',
               rule='B1 flies only after the T1-T4 regression law; burn limit at t(w_min = 1 mm) using 1.1 x measured a; grain change if '
                    'a >= 1.25 x nominal with n <= 0.4 (LEAD adopted 2026-10-13)',
               inputs=dict(gnc_record_index=rec_index, gnc_record_index_sha256_16=sha16(rec_index)),
               mc=mc, mc_fraction_thrust_on_gt_t=thr, reproduction_checks=checks, gating=gate, cases=cases,
               notes=['Regression laws re-anchored at r(300 kg/m2s) = band x 1 mm/s (as v2.4 RC-07); oxidiser-flux law unless law total',
                      'Throat growth (tg711) per run_dispersed_v2p4 --throat-growth (GNC sim6 v2.7 Pc-hold reproduction); MC pc_k2 pairs with tg711 records',
                      'Thrust-on offset DERIVED from the max records only; a per-run thrust history is not available, so t_L from the p99 and max '
                      'records brackets the limit for other histories (compare m_ox and int Pc at w = 1 mm across records)',
                      'The 1.1 factor on measured a is the rule\'s measurement allowance (ASSUMED adequate until T1-T4 scatter is known)'])
    json.dump(out, open(out_json, 'w'), indent=1, default=float)
    print(json.dumps(dict(gating=gate, mc={k: {kk: vv for kk, vv in v.items() if kk != 'file'} for k, v in mc.items()},
                          checks=checks), indent=1, default=float))


if __name__ == '__main__':
    main(*sys.argv[1:6])
