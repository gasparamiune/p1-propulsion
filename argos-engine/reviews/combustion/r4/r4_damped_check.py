"""REV-COMB-4 reviewer script: damped FA-1 head spectrum in the 0.1-1 ms band (author: 115.4 bar abs at zeta 0.02, head, all cases).

Exact first-order-hold recurrence of a damped SDOF (static gain 1, from rest) on the stored piecewise-linear gauge history, evaluated at
16 sub-points per 0.05 ms step (the input is linear inside a step, so the sub-point values are exact; the maximum between sub-points is
missed by at most about 0.05 bar at these periods), load held after the record with the free decay added (sub-sampled for 3 periods).
Both conventions (gauge clipped at 0 and unclipped), max of the two.  Case pre-selection: the 120 cases with the highest undamped
0.1-1 ms band value in the reviewer's exact undamped run (r4_fa1_spectrum_cases.npz; damping only lowers a value, and the damped band
maximum is checked to sit below the 120th undamped value).  Periods: the published grid inside 0.1 < T <= 1 ms.
Tags: histories SIM; spectra DERIVED.
usage: python -I r4_damped_check.py NPZ CASES_NPZ PUBLISHED_CSV OUT_JSON
"""
import hashlib, json, sys, time
import numpy as np

npz_f, cases_f, pub_f, out_f = sys.argv[1:5]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(npz_f) == '399bf43d1c09de24' and H16(pub_f) == 'a2c380515cada638'
PA = 101325.0
t0 = time.time()
Z = np.load(npz_f); C = np.load(cases_f)
keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
per = C['periods_ms'].astype(float); Sh = C['S_head'].astype(float)        # (n_case, n_period) undamped, bar abs
pub = np.genfromtxt(pub_f, delimiter=',', names=True)
Tp = np.array(pub[pub.dtype.names[0]], float)
band = Tp[(Tp > 0.1) & (Tp <= 1.0)]
jb = [int(np.argmin(np.abs(per - T))) for T in band]
assert np.max(np.abs(per[jb] - band)) < 1e-6
und_band = Sh[:, jb].max(axis=1)
order = np.argsort(-und_band)
sel = order[:120]
cut = float(und_band[order[119]])
DT = 5e-5; NS = 16; h = DT / NS
lens = np.diff(off); nt = int(lens.max())
G = np.zeros((len(sel), nt))
for r, i in enumerate(sel):
    a, b = int(off[i]), int(off[i + 1])
    g = Z['P_head_bar'][a:b].astype(float) * 1e5 - PA
    G[r, :len(g)] = g; G[r, len(g):] = g[-1]
G2 = np.concatenate([np.maximum(G, 0.0), G], axis=0)           # clipped, unclipped
res = dict(script='r4_damped_check.py', script_sha16=H16(sys.argv[0]), npz=H16(npz_f), cases_npz=H16(cases_f), n_selected=len(sel),
           undamped_band_value_of_last_selected=cut, band_periods=len(band), zetas={})
for zeta in (0.0, 0.02, 0.05):
    w = 2 * np.pi / (band * 1e-3); wd = w * np.sqrt(1 - zeta ** 2)
    # exact discrete FOH for x'' + 2 z w x' + w^2 x = w^2 g, g linear over h: state (x, v); use the particular solution x_p = g - 2 z s / w
    e = np.exp(-zeta * w * h); c = np.cos(wd * h); s = np.sin(wd * h)
    x = np.zeros((G2.shape[0], len(band))); v = np.zeros_like(x); best = np.full_like(x, -np.inf)
    for i in range(nt - 1):
        g0 = G2[:, i][:, None]; sl = ((G2[:, i + 1] - G2[:, i]) / DT)[:, None]
        for k in range(NS):
            gk = g0 + sl * (k * h)
            ap = gk - 2 * zeta * sl / w                     # particular x at the sub-step start
            C1 = x - ap; C2 = (v - sl + zeta * w * C1) / wd
            x = ap + sl * h + e * (C1 * c + C2 * s)
            v = sl + e * ((-zeta * w * C1 + wd * C2) * c + (-zeta * w * C2 - wd * C1) * s)
            np.maximum(best, x, out=best)
    # held load after the record: free (decaying) vibration about the last value, sampled over 3 periods
    ge = G2[:, -1][:, None]
    C1 = x - ge; C2 = (v + zeta * w * C1) / wd
    for frac in np.linspace(0, 3, 241):
        tt = frac * (band * 1e-3)
        xx = ge + np.exp(-zeta * w * tt) * (C1 * np.cos(wd * tt) + C2 * np.sin(wd * tt))
        np.maximum(best, xx, out=best)
    m = np.maximum(best[:len(sel)], best[len(sel):])                 # max of the two conventions
    S = (PA + m) / 1e5
    jj = np.unravel_index(np.argmax(S), S.shape)
    # a non-selected case has undamped band value <= cut; with damped <= undamped (holds for these pulse histories, not a theorem)
    # the selection is sufficient when cut <= the damped band maximum found
    col = {0.0: 'headallzeta0', 0.02: 'headallzeta002', 0.05: 'headallzeta005'}[zeta]
    pb = np.array(pub[col], float)[(Tp > 0.1) & (Tp <= 1.0)]
    res['zetas'][f'{zeta}'] = dict(band_max_bar_abs=round(float(S.max()), 3), case=keys[sel[jj[0]]], period_ms=float(band[jj[1]]),
                                   selection_sufficient_cut_below_band_max=bool(cut <= S.max()),
                                   published_column=col, published_band_max_bar_abs=round(float(pb.max()), 3),
                                   published_period_ms=float(band[int(np.argmax(pb))]),
                                   reviewer_minus_published_bar=round(float(S.max() - pb.max()), 4))
    print('zeta', zeta, res['zetas'][f'{zeta}'], round(time.time() - t0, 1), 's', flush=True)
res['undamped_check_vs_exact_run'] = dict(reviewer_exact=float(und_band.max()), this_run_zeta0=res['zetas']['0.0']['band_max_bar_abs'])
res['runtime_s'] = round(time.time() - t0, 1)
json.dump(res, open(out_f, 'w'), indent=1)
print('done', res['runtime_s'])
