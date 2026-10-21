"""REV-COMB-4 reviewer script: FA-1 equivalent-static-pressure spectra from the 896 v2.4b solver histories (own code).

Independent of the author's fa1_spectra_*_v2p4b.py (definitions taken from REPORT v2.4b section 16.2 only):
  S(T) = p_amb + max over t of x(t), x'' + w^2 x = w^2 g(t), x(0) = x'(0) = 0, w = 2 pi / T, undamped;
  g = gauge history (P - 101325 Pa), piecewise linear on the stored time grid; after the record the load is held at its last
  value (the free vibration about it is added); convention per case and node: max of (b) g clipped at 0 and (c) g unclipped.
Method: exact state recurrence per step; inside each step the continuous maximum is found from the closed form
  x(tau) = g_i + s tau + C cos(w tau) + D sin(w tau): candidate local maxima tau_k = (atan2(D, C) + asin(s / (R w)) + 2 pi k) / w,
  first and last k in the step, plus the step ends.
Cross-check (different numerics): scipy cont2discrete first-order hold + lfilter on a uniform resampled grid, at selected periods.
Periods: the 406 published periods, 0.005-0.015 ms, FE mode periods T = 1 / (s f_FE) for ca2b and ca2c (s 1.00 / 0.90 / 0.85), and
  long periods 50-2000 ms (beyond the published 50 ms).
Tags: histories SIM (author's v2.4a/b construct, ASSUMED inputs); spectra DERIVED by the reviewer.  Not physical evidence.
usage: python -I r4_fa1_spectrum.py NPZ PUBLISHED_CSV MODAL_CA2B_JSON MODAL_CA2C_JSON OUT_JSON OUT_NPZ
"""
import csv, hashlib, json, math, sys, time
import numpy as np
from scipy.signal import cont2discrete, lfilter

npz_f, pub_csv, mb_f, mc_f, out_f, out_npz = sys.argv[1:7]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
EXP = {npz_f: '399bf43d1c09de24', pub_csv: 'a2c380515cada638', mb_f: '9af80c657eed11ac', mc_f: '619272cd3b66072b'}
for f, h in EXP.items():
    assert H16(f) == h, (f, H16(f), h)
PA = 101325.0
TWO_PI = 2.0 * math.pi
t_start = time.time()

# ---- periods
pub = list(csv.DictReader(open(pub_csv)))
P_pub = [float(r['period_ms']) for r in pub]
MB = json.load(open(mb_f)); MC = json.load(open(mc_f))
fb = [float(m['f_Hz']) for m in MB['modes']]; fc = [float(m['f_Hz']) for m in MC['modes']]
assert len(fb) == 60 and len(fc) == 60
P_modal_b = [1e3 / (s * f) for f in fb for s in (1.00, 0.90, 0.85)]
P_modal_c = [1e3 / (s * f) for f in fc for s in (1.00, 0.90, 0.85)]
P_long = list(np.geomspace(50.0, 2000.0, 31)[1:])
P_short = [0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175]
P_all = sorted(set([round(x, 9) for x in P_pub + P_modal_b + P_modal_c + P_long + P_short]))
TP = np.array(P_all) * 1e-3
W = TWO_PI / TP
print('periods', len(P_all), flush=True)


def ramp_resp(t, t0, k, w):
    """Undamped response (static gain 1, at rest) to a ramp of slope k starting at t0: k [(t - t0) - sin(w (t - t0)) / w] for t > t0."""
    tau = np.maximum(t - t0, 0.0)
    return k * (tau - np.sin(w * tau) / w)


def selftest():
    """Analytic checks on the 0.05 ms grid (so the 'step' has a 0.05 ms linear rise): ramp-step, max = 1 + |sin(pi tr/T)| / (pi tr/T);
    trapezoid 0 -> 1 in 0.05 ms, held, 1 -> 0 over the last 0.05 ms before 4 ms: reference = max of the closed-form superposition of
    four ramp responses on a 0.1 us grid."""
    dt = 5e-5
    t = np.arange(0.0, 0.2 + 1e-12, dt)
    step = np.where(t > 0, 1.0, 0.0)
    rect = np.where((t > 0) & (t < 4e-3 - 1e-12), 1.0, 0.0)
    Tt = np.array([0.05e-3, 0.1e-3, 0.5e-3, 2e-3, 8e-3, 20e-3, 50e-3])
    x = np.pi * dt / Tt
    ref_step = 1.0 + np.abs(np.sin(x)) / x
    tf = np.arange(0.0, 0.3, 1e-7)
    t_fall0 = t[rect > 0][-1]
    ref_rect = []
    for T in Tt:
        w = TWO_PI / T
        xr = ramp_resp(tf, 0.0, 1 / dt, w) - ramp_resp(tf, dt, 1 / dt, w) - ramp_resp(tf, t_fall0, 1 / dt, w) + ramp_resp(tf, t_fall0 + dt, 1 / dt, w)
        ref_rect.append(float(xr.max()))
    out = {}
    for lab, g, ref in (('ramp_step', step, ref_step), ('trapezoid_4ms', rect, np.array(ref_rect))):
        m = exact_max(t[None, :], g[None, :], Tt)[0]
        out[lab] = dict(T_ms=(Tt * 1e3).tolist(), value=m.tolist(), analytic=ref.tolist(), max_rel_err=float(np.max(np.abs(m / ref - 1))))
    return out


def exact_max(tg, G, periods):
    """tg (rows, nt) times, G (rows, nt) loads; returns (rows, np) max of x over [0, inf) with the load held after the end."""
    w = TWO_PI / np.asarray(periods, float)[None, :]
    nr, nt = G.shape
    u = np.zeros((nr, w.shape[1])); v = np.zeros_like(u); um = np.zeros_like(u)
    for i in range(nt - 1):
        dt = (tg[:, i + 1] - tg[:, i])[:, None]
        g0 = G[:, i][:, None]; g1 = G[:, i + 1][:, None]
        s = np.where(dt > 0, (g1 - g0) / np.where(dt > 0, dt, 1.0), 0.0)
        C = u - g0; D = (v - s) / w
        R = np.sqrt(C * C + D * D)
        wdt = w * dt
        cw, sw = np.cos(wdt), np.sin(wdt)
        # end of step state
        u_n = g0 + s * dt + C * cw + D * sw
        v_n = s - C * w * sw + D * w * cw
        # interior maxima
        with np.errstate(divide='ignore', invalid='ignore'):
            q = np.where(R > 0, s / (R * w), 9.0)
        ok = np.abs(q) < 1.0
        qq = np.where(ok, q, 0.0)
        ph = np.arctan2(D, C) + np.arcsin(qq)            # w tau - 2 pi k at a maximum
        k0 = np.ceil(-ph / TWO_PI - 1e-12)               # first k with tau >= 0
        tau_first = (ph + TWO_PI * k0) / w
        k1 = np.floor((wdt - ph) / TWO_PI + 1e-12)       # last k with tau <= dt
        tau_last = (ph + TWO_PI * k1) / w
        amp = R * np.sqrt(1.0 - qq * qq)
        for tau in (tau_first, tau_last):
            good = ok & (tau >= 0) & (tau <= dt)
            val = g0 + s * tau + amp
            um = np.where(good, np.maximum(um, val), um)
        um = np.maximum(um, u_n)
        u, v = u_n, v_n
    ge = G[:, -1][:, None]
    um = np.maximum(um, ge + np.sqrt((u - ge) ** 2 + (v / w) ** 2))
    return um


def foh_max(t, g, T, t_stop):
    """Cross-check numerics (REV-COMB-3 style): uniform grid dt = min(T/80, 1.25e-5 s), FOH discretisation, lfilter, sampled max."""
    w = TWO_PI / T
    dt = min(T / 80.0, 1.25e-5)
    tt = np.arange(0.0, t_stop + dt / 2, dt)
    ff = np.interp(tt, t, g)                              # held at the last value beyond the record
    sysd = cont2discrete(([w * w], [1.0, 0.0, w * w]), dt, method='foh')
    b = np.atleast_1d(np.squeeze(sysd[0])); a = np.atleast_1d(np.squeeze(sysd[1]))
    return float(lfilter(b, a, ff).max())


ST = selftest()
print('selftest', {k: v['max_rel_err'] for k, v in ST.items()}, flush=True)
assert all(v['max_rel_err'] < 5e-5 for v in ST.values()), ST

Z = np.load(npz_f)
keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
assert len(keys) == 896
lens = np.diff(off); nt = int(lens.max())
rows_t, rows_g, row_case, row_node, row_conv = [], [], [], [], []
peak_head = np.zeros(896); peak_aft = np.zeros(896); t_end = np.zeros(896)
dt_dev = 0.0
for i in range(896):
    a, b = int(off[i]), int(off[i + 1])
    t = Z['t_s'][a:b].astype(float)
    ph = Z['P_head_bar'][a:b].astype(float) * 1e5; pa = Z['P_aft_bar'][a:b].astype(float) * 1e5
    peak_head[i] = ph.max() / 1e5; peak_aft[i] = pa.max() / 1e5; t_end[i] = t[-1]
    dt_dev = max(dt_dev, float(np.max(np.abs(t - 5e-5 * np.arange(b - a)))))
    cand = [('head', 'b', np.maximum(ph - PA, 0.0)), ('aft', 'b', np.maximum(pa - PA, 0.0))]
    if min(ph.min(), pa.min()) < PA:
        cand += [('head', 'c', ph - PA), ('aft', 'c', pa - PA)]
    tp = np.empty(nt); tp[:len(t)] = t; tp[len(t):] = t[-1] + 5e-5 * np.arange(1, nt - len(t) + 1)
    for n, cv, g in cand:
        gp = np.empty(nt); gp[:len(g)] = g; gp[len(g):] = g[-1]
        rows_t.append(tp); rows_g.append(gp); row_case.append(i); row_node.append(n); row_conv.append(cv)
TG = np.vstack(rows_t); GG = np.vstack(rows_g)
print('rows', GG.shape, 'max stored-grid deviation from k x 0.05 ms', dt_dev, flush=True)

# exact maxima, chunked over periods to keep memory small
U = np.zeros((GG.shape[0], len(P_all)))
CH = 64
for j0 in range(0, len(P_all), CH):
    U[:, j0:j0 + CH] = exact_max(TG, GG, TP[j0:j0 + CH])
    print('periods %d-%d done %.0f s' % (j0, min(j0 + CH, len(P_all)), time.time() - t_start), flush=True)
S = (PA + U) / 1e5
# per (case, node) envelope over the b / c conventions
Sh = np.zeros((896, len(P_all))); Sa = np.zeros((896, len(P_all)))
for r in range(S.shape[0]):
    tgt = Sh if row_node[r] == 'head' else Sa
    tgt[row_case[r]] = np.maximum(tgt[row_case[r]], S[r])

# groups (author's definitions: baseline = vapour_once | rounded_Cd1.0 | O/F grid 4-12 | both pools)
def parts(k):
    rd, ent, of, tf, tr, pool = k.split('|')
    return rd, ent, float(of[2:]), pool
base = [i for i, k in enumerate(keys) if parts(k)[0] == 'vapour_once' and parts(k)[1] == 'rounded_Cd1.0' and 4.0 <= parts(k)[2] <= 12.0]
groups = {'all': list(range(896)), 'baseline': base}
BANDS = (('T_le_0p1ms', 0.0, 0.1), ('T_0p1_to_1ms', 0.1, 1.0), ('T_1_to_20ms', 1.0, 20.0), ('T_20_to_50ms', 20.0, 50.0),
         ('T_50_to_2000ms', 50.0, 2000.0), ('T_lt_0p02ms', 0.0, 0.0199))
res = dict(script='r4_fa1_spectrum.py', script_sha16=H16(sys.argv[0]), inputs={k: v for k, v in EXP.items()},
           n_rows=int(S.shape[0]), n_periods=len(P_all), selftest=ST, stored_grid_max_dev_s=dt_dev,
           peak_head_bar_abs=dict(max=float(peak_head.max()), case=keys[int(np.argmax(peak_head))]),
           peak_aft_bar_abs=dict(max=float(peak_aft.max())),
           record_end_s=dict(min=float(t_end.min()), max=float(t_end.max())))
pub_cols = {('head', 'all'): 'head|all|zeta0', ('head', 'baseline'): 'head|baseline|zeta0',
            ('aft', 'all'): 'aft|all|zeta0', ('aft', 'baseline'): 'aft|baseline|zeta0'}
iP = {round(p, 9): j for j, p in enumerate(P_all)}
env = {}
for gname, sel in groups.items():
    for node, A in (('head', Sh), ('aft', Sa)):
        E = A[sel].max(axis=0); arg = np.array(sel)[A[sel].argmax(axis=0)]
        env[(node, gname)] = (E, arg)
        bands = {}
        for bl, lo, hi in BANDS:
            idx = [j for j, p in enumerate(P_all) if lo < p <= hi + 1e-12]
            if bl in ('T_le_0p1ms', 'T_0p1_to_1ms', 'T_1_to_20ms', 'T_20_to_50ms'):
                idx_pub = [j for j in idx if round(P_all[j], 9) in set(round(x, 9) for x in P_pub)]
            else:
                idx_pub = idx
            jj = max(idx_pub, key=lambda j: E[j]); ja = max(idx, key=lambda j: E[j])
            bands[bl] = dict(published_grid=dict(value=round(float(E[jj]), 3), period_ms=P_all[jj], case=keys[int(arg[jj])]),
                             all_periods=dict(value=round(float(E[ja]), 3), period_ms=P_all[ja], case=keys[int(arg[ja])]))
        # compare with the published zeta-0 column on the published grid
        col = pub_cols[(node, gname)]
        d = [float(E[iP[round(p, 9)]]) - float(r[col]) for p, r in zip(P_pub, pub)]
        res[f'{node}|{gname}'] = dict(n_cases=len(sel), bands=bands, max_over_all_periods=dict(value=round(float(E.max()), 3),
                                      period_ms=P_all[int(E.argmax())], case=keys[int(arg[int(E.argmax())])]),
                                      vs_published_zeta0=dict(max_diff_bar=round(max(d), 4), min_diff_bar=round(min(d), 4),
                                                              max_abs_diff_bar=round(max(abs(x) for x in d), 4)))
# FA1S check: every case, every period, both nodes
FA1S = 151.04
res['FA1S_check'] = dict(FA1S_bar_abs=FA1S,
                         head_max=round(float(Sh.max()), 3), aft_max=round(float(Sa.max()), 3),
                         head_argmax=dict(case=keys[int(np.unravel_index(Sh.argmax(), Sh.shape)[0])], period_ms=P_all[int(np.unravel_index(Sh.argmax(), Sh.shape)[1])]),
                         aft_argmax=dict(case=keys[int(np.unravel_index(Sa.argmax(), Sa.shape)[0])], period_ms=P_all[int(np.unravel_index(Sa.argmax(), Sa.shape)[1])]),
                         n_case_period_points_above_FA1S=int((Sh > FA1S).sum() + (Sa > FA1S).sum()),
                         margin_bar=round(FA1S - float(max(Sh.max(), Sa.max())), 3),
                         ratio_max_over_FA1S=round(float(max(Sh.max(), Sa.max())) / FA1S, 4))
# per-case band maxima of the head node and counts above thresholds
def bandmax(A, lo, hi):
    idx = [j for j, p in enumerate(P_all) if lo < p <= hi + 1e-12]
    return A[:, idx].max(axis=1)
cnt = {}
for lab, lo, hi in (('T_le_0p1ms', 0.0, 0.1), ('T_0p1_to_1ms', 0.1, 1.0), ('T_1_to_20ms', 1.0, 20.0), ('T_20_to_50ms', 20.0, 50.0)):
    bm = bandmax(Sh, lo, hi)
    cnt[lab] = {f'above_{v}': int((bm > v).sum()) for v in (90, 93, 94, 102, 116.3, 121, 125.8, 147, 151.04)}
res['head_case_band_counts'] = cnt
res['head_peak_counts'] = {f'above_{v}': int((peak_head > v).sum()) for v in (45.0, 60.0, 63.1, 67.5, 75.519, 80.0, 85.0, 88.0)}
res['aft_peak_counts'] = {f'above_{v}': int((peak_aft > v).sum()) for v in (60.0, 63.1, 75.519)}
# modal periods for TC-01 work: envelope values at the ca2b / ca2c modal periods
def at(ps, node='head', g='all'):
    E = env[(node, g)][0]
    return [round(float(E[iP[round(p, 9)]]), 3) for p in ps]
res['modal_periods'] = dict(ca2b=dict(f_Hz=fb, T_ms=[round(p, 6) for p in P_modal_b], head_all=at(P_modal_b)),
                            ca2c=dict(f_Hz=fc, T_ms=[round(p, 6) for p in P_modal_c], head_all=at(P_modal_c)))
# cross-check with independent numerics at selected periods, over the cases that govern the envelope there
xc = []
for Tms in (0.095, 0.705, 3.5, 21.1, 200.0):
    j = iP[round(Tms, 9)] if round(Tms, 9) in iP else int(np.argmin(np.abs(np.array(P_all) - Tms)))
    for node, A in (('head', Sh),):
        top = np.argsort(-A[:, j])[:3]
        for i in top:
            a, b = int(off[i]), int(off[i + 1])
            t = Z['t_s'][a:b].astype(float); p = (Z['P_head_bar'][a:b].astype(float) * 1e5)
            vals = []
            for g in (np.maximum(p - PA, 0.0), p - PA):
                vals.append((PA + foh_max(t, g, P_all[j] * 1e-3, t[-1] + 3.0 * P_all[j] * 1e-3)) / 1e5)
            xc.append(dict(T_ms=P_all[j], case=keys[int(i)], exact=round(float(A[i, j]), 4), foh_sampled=round(max(vals), 4),
                           diff=round(float(A[i, j]) - max(vals), 4)))
res['crosscheck_foh'] = xc
res['runtime_s'] = round(time.time() - t_start, 1)
json.dump(res, open(out_f, 'w'), indent=1)
np.savez_compressed(out_npz, periods_ms=np.array(P_all), S_head=Sh.astype(np.float32), S_aft=Sa.astype(np.float32),
                    peak_head=peak_head, peak_aft=peak_aft, keys=np.array(keys))
print('done', res['runtime_s'], 's', flush=True)
