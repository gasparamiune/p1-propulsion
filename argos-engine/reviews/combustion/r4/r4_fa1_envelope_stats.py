"""REV-COMB-4 reviewer script: FA-1 grid head-pressure statistics against the LC-TB70 zones (Mechanical lc_tb70_envelope_v1).

For each of the 896 v2.4b FA-1 solver histories (fa1_histories_solver_v2p4b.npz, SIM on an ASSUMED construct; histories identical
to v2.4a by the author's 1e-9 reproduction): head peak, total time above 45 / 58.1 / 60 / 63.1 / 75.519 bar abs (linear
interpolation of the crossings on the stored grid), the 10-90 % rise time of the first rise to the peak (levels between the
pre-rise value p0 = P_head at t = 0 and the peak), counts by group (baseline = vapour_once | rounded_Cd1.0 | O/F 4-12, as the
author's Table 7.6b; 'as_written' = the v2.4 double count, upper bracket), and the cases outside Z3 as written (peak > 75.519 bar abs,
or time above 63.1 bar abs > 3.0 ms, or a 10-90 % rise < 0.8 ms with the peak above 63.1).
Tags: histories SIM; statistics DERIVED; grid fractions are not probabilities.
usage: python -I r4_fa1_envelope_stats.py NPZ OUT_JSON
"""
import hashlib, json, sys
import numpy as np

npz_f, out_f = sys.argv[1:3]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(npz_f) == '399bf43d1c09de24'
Z = np.load(npz_f)
keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
LEV = (45.0, 58.1, 60.0, 63.1, 75.519, 80.0, 85.0)


def t_above(t, p, lev):
    """total time with p > lev, crossings linearly interpolated"""
    a = p - lev
    a0, a1 = a[:-1], a[1:]; dt = np.diff(t)
    both = (a0 > 0) & (a1 > 0)
    down = (a0 > 0) & (a1 <= 0)
    up = (a1 > 0) & (a0 <= 0)
    tot = dt[both].sum()
    tot += (dt[down] * a0[down] / (a0[down] - a1[down])).sum()
    tot += (dt[up] * a1[up] / (a1[up] - a0[up])).sum()
    return float(tot)


def cross_t(t, p, lev, i_end):
    """first time p reaches lev on [0, i_end] (linear interpolation)"""
    idx = np.nonzero(p[:i_end + 1] >= lev)[0]
    if len(idx) == 0:
        return None
    j = int(idx[0])
    if j == 0:
        return float(t[0])
    return float(t[j - 1] + (lev - p[j - 1]) / (p[j] - p[j - 1]) * (t[j] - t[j - 1]))


rows = []
for i, k in enumerate(keys):
    a, b = int(off[i]), int(off[i + 1])
    t = Z['t_s'][a:b].astype(float); p = Z['P_head_bar'][a:b].astype(float)
    ip = int(np.argmax(p)); pk = float(p[ip]); p0 = float(p[0])
    t10 = cross_t(t, p, p0 + 0.1 * (pk - p0), ip); t90 = cross_t(t, p, p0 + 0.9 * (pk - p0), ip)
    r = dict(case=k, peak=pk, t_peak_ms=float(t[ip] * 1e3), p0=p0, rise_10_90_ms=(t90 - t10) * 1e3,
             group=('baseline' if (k.startswith('vapour_once|rounded_Cd1.0|') and int(float(k.split('|')[2][2:])) >= 4) else 'other'),
             as_written=k.startswith('as_written'))
    for lev in LEV:
        r[f'ms_above_{lev}'] = t_above(t, p, lev) * 1e3
    rows.append(r)


def summ(sel, name):
    s = dict(n=len(sel))
    pk = np.array([r['peak'] for r in sel])
    s['peak_max'] = float(pk.max()) if len(sel) else None
    for lev in LEV:
        s[f'n_peak_above_{lev}'] = int((pk > lev).sum())
    ab = [r for r in sel if r['peak'] > 63.1]
    s['above_63.1'] = dict(n=len(ab),
                           ms_above_63p1_max=max((r['ms_above_63.1'] for r in ab), default=None),
                           n_ms_above_63p1_gt_3ms=sum(r['ms_above_63.1'] > 3.0 for r in ab),
                           rise_10_90_ms_min=min((r['rise_10_90_ms'] for r in ab), default=None),
                           n_rise_lt_0p8ms=sum(r['rise_10_90_ms'] < 0.8 for r in ab))
    ab3 = [r for r in sel if r['peak'] > 75.519]
    s['above_75.519'] = dict(n=len(ab3), ms_above_75p519_max=max((r['ms_above_75.519'] for r in ab3), default=None),
                             ms_above_63p1_max=max((r['ms_above_63.1'] for r in ab3), default=None),
                             rise_10_90_ms_min=min((r['rise_10_90_ms'] for r in ab3), default=None))
    a60 = [r for r in sel if r['peak'] > 60.0]
    s['above_60'] = dict(n=len(a60), ms_above_60_max=max((r['ms_above_60.0'] for r in a60), default=None),
                         ms_above_58p1_max=max((r['ms_above_58.1'] for r in a60), default=None),
                         ms_above_45_max=max((r['ms_above_45.0'] for r in a60), default=None))
    out_z3 = [r for r in sel if r['peak'] > 75.519 or r['ms_above_63.1'] > 3.0 or (r['peak'] > 63.1 and r['rise_10_90_ms'] < 0.8)]
    s['outside_Z3_as_written'] = dict(n=len(out_z3), n_by_peak=sum(r['peak'] > 75.519 for r in out_z3),
                                      n_by_time_above_63p1=sum(r['ms_above_63.1'] > 3.0 for r in out_z3),
                                      n_by_rise=sum(r['peak'] > 63.1 and r['rise_10_90_ms'] < 0.8 for r in out_z3))
    s['ms_above_45_max_all'] = float(max(r['ms_above_45.0'] for r in sel))
    return s


res = dict(script='r4_fa1_envelope_stats.py', script_sha16=H16(sys.argv[0]), npz=H16(npz_f),
           all=summ(rows, 'all'), baseline=summ([r for r in rows if r['group'] == 'baseline'], 'baseline'),
           as_written=summ([r for r in rows if r['as_written']], 'as_written'),
           vapour_once=summ([r for r in rows if not r['as_written']], 'vapour_once'),
           by_OF={}, worst=sorted(rows, key=lambda r: -r['peak'])[:12])
for of in sorted(set(r['case'].split('|')[2] for r in rows), key=lambda x: float(x[2:])):
    sel = [r for r in rows if r['case'].split('|')[2] == of]
    res['by_OF'][of] = dict(n=len(sel), peak_max=max(r['peak'] for r in sel), n_above_60=sum(r['peak'] > 60 for r in sel),
                            n_above_63p1=sum(r['peak'] > 63.1 for r in sel), n_above_75p519=sum(r['peak'] > 75.519 for r in sel))
json.dump(res, open(out_f, 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('all', 'baseline', 'as_written', 'vapour_once')}, indent=1))
print(json.dumps(res['by_OF']))
