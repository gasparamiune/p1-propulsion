"""REV-COMB-4 reviewer script: P4c lit-side window statistics at the 0.21776 mm start lift (CHANGELOG 230 (5); handback P4c).

Recomputes, from the author's per-corner lit thrust histories (start_level_lit_thrust_0p21776mm_v2p4b.csv, t from the light,
0.5 ms) and the per-corner E2 (start_level_lit_thrust_0p21776mm_v2p4b.json corners[i]['torch0.0'|'torch0.3']['E2_s']):
  F_min over corners of F in [E2, E2 + W] (W = 0.5 / 0.8 s), the corners that never reach 37.16 N in each window, the latest first
  crossing after E2, and, for each never-corner, whether F reaches 37.16 N later in the stored record (to 1.0 s from the light) or
  before E2 (between the light and E2).
Tags: histories SIM (grain_q1d v2 on ASSUMED laws and bands); statistics DERIVED; corner fractions are not probabilities.
usage: python -I r4_p4c_check.py CSV JSON P4C_JSON OUT_JSON
"""
import hashlib, json, sys
import numpy as np

csv_f, js_f, p4c_f, out_f = sys.argv[1:5]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(csv_f) == 'c073d4f993f8c412' and H16(js_f) == '10cdc03154b95216'
TH = 37.16
hdr = open(csv_f).readline().strip().split(',')
A = np.genfromtxt(csv_f, delimiter=',', skip_header=1)
t = A[:, 0]
cols = {h[4:]: j for j, h in enumerate(hdr) if h.startswith('F_N|')}
J = json.load(open(js_f)); P = json.load(open(p4c_f))
res = dict(script='r4_p4c_check.py', script_sha16=H16(sys.argv[0]), csv=H16(csv_f), json=H16(js_f), p4c_json=H16(p4c_f),
           threshold_N=TH, dt_s=float(np.median(np.diff(t))), t_last_s=float(t[-1]), n_corners=len(cols), torch={})
for tk in ('torch0.0', 'torch0.3'):
    R = {}
    rows = []
    for c in J['corners']:
        name = c['corner']; F = A[:, cols[name]]; e2 = float(c[tk]['E2_s'])
        r = dict(corner=name, E2_s=e2)
        for W in (0.5, 0.8):
            m = (t >= e2 - 1e-9) & (t <= e2 + W + 1e-9)
            fw = F[m]; tw = t[m]
            idx = np.nonzero(fw >= TH)[0]
            r[f'W{W}'] = dict(F_min=float(fw.min()), F_max=float(fw.max()), F_mean=float(fw.mean()),
                              first_cross_after_E2_s=(None if len(idx) == 0 else float(tw[idx[0]] - e2)),
                              share_ge_TH=float((fw >= TH).mean()))
        pre = F[t < e2 - 1e-9]; post = F[t > e2 + 0.8 + 1e-9]
        r['max_before_E2'] = float(pre.max()) if len(pre) else None
        r['max_after_window_0p8_to_end'] = float(post.max()) if len(post) else None
        idx_post = np.nonzero((t > e2 + 0.8 + 1e-9) & (F >= TH))[0]
        r['first_cross_after_window_0p8_s_from_light'] = float(t[idx_post[0]]) if len(idx_post) else None
        r['F_at_last_stored_N'] = float(F[-1])
        rows.append(r)
    for W in (0.5, 0.8):
        never = [r for r in rows if r[f'W{W}']['first_cross_after_E2_s'] is None]
        cross = [r[f'W{W}']['first_cross_after_E2_s'] for r in rows if r[f'W{W}']['first_cross_after_E2_s'] is not None]
        R[f'window_{W}s'] = dict(F_min_over_corners_N=round(min(r[f'W{W}']['F_min'] for r in rows), 3),
                                 n_corners_never=len(never),
                                 never=[dict(corner=r['corner'], E2_s=r['E2_s'], F_window_max=round(r[f'W{W}']['F_max'], 3),
                                             max_before_E2=(None if r['max_before_E2'] is None else round(r['max_before_E2'], 3)),
                                             max_after_window_0p8_to_end=(None if r['max_after_window_0p8_to_end'] is None
                                                                          else round(r['max_after_window_0p8_to_end'], 3)),
                                             first_cross_after_window_0p8_s_from_light=r['first_cross_after_window_0p8_s_from_light'],
                                             F_at_last_stored_N=round(r['F_at_last_stored_N'], 3)) for r in never],
                                 latest_first_crossing_after_E2_s=(max(cross) if cross else None))
    R['E2_s_range'] = [min(r['E2_s'] for r in rows), max(r['E2_s'] for r in rows)]
    R['corners_below_TH_at_every_stored_time'] = [r['corner'] for r in rows
                                                 if (r['max_before_E2'] is None or r['max_before_E2'] < TH)
                                                 and r['W0.8']['F_max'] < TH
                                                 and (r['max_after_window_0p8_to_end'] is None or r['max_after_window_0p8_to_end'] < TH)]
    a = P['lit_side']['lift_0p21776mm'][tk]
    R['author'] = {w: dict(F_min=a[w]['F_min_over_corners_N'], n_never=a[w]['thresholds']['37.16 N']['n_corners_never'],
                           latest=a[w]['thresholds']['37.16 N']['latest_first_crossing_after_E2_s']) for w in ('window_0.5s', 'window_0.8s')}
    R['author']['E2_s_range'] = a['E2_s_range']
    res['torch'][tk] = R
res['author_corners_below_37p16N_at_every_stored_time_to_1s'] = P['lit_side']['lift_0p21776mm']['corners_below_37p16N_at_every_stored_time_to_1s']
json.dump(res, open(out_f, 'w'), indent=1)
print(json.dumps(res, indent=1)[:6000])
