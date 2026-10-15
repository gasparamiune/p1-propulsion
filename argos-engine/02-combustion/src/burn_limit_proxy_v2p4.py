"""Web-against-time law for GNC's burn limit (Combustion v2.4; REV-GNC-1 RG-03 item 2 relayed by the lead, 2026-10-13).

Lead rule (2026-10-13): B1 flies only after the T1-T4 regression law; burn limit at t(web = 1 mm) using 1.1 x measured a;
grain change if a >= 1.25 x nominal with n <= 0.4. GNC needs a web state to integrate in sim6 and the FSW.

Proxy given to GNC (uniform regression of the centred straight port, oxidiser-flux law re-anchored at 300 kg/m2s):
    D(0) = 25.0 mm,   dD/dt = 2 r,   r = k_a x 1.0e-3 m/s x (G_ox / 300)^n,   G_ox = 4 mdot_ox / (pi D^2)  [kg/m2s]
    web w = (53.5 mm - D) / 2;  t_L = first time with w <= 1.0 mm;  no regression while mdot_ox = 0.
    k_a = 1.1 x a_meas / a_ref, where a_ref gives 1 mm/s at 300 kg/m2s (a_meas re-anchored the same way), n = n_meas.
Verification here: the proxy is integrated with mdot_ox(t) of each grain_q1d v2.4 history of the GNC v3.1 62 m records (same
band and n) and compared with the model's minimum web w_min(t) (the differences are the solid thermal lag, the start preheat and
the axial distribution). For the total-flux sensitivity runs (law 'total', same a and n), the factor k on a that makes the
ox-law proxy reach w = 1 mm at the same time is found by bisection: the allowance needed if a were calibrated where the
regression is lowest (head end).
usage: python -I burn_limit_proxy_v2p4.py DC_GNCV31_62M_DIR OUT_JSON
"""
from __future__ import annotations
import glob, json, math, os, re, sys, hashlib
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

D0, DOUT, W_LIM = 0.025, 0.0535, 1.0e-3
PAT = re.compile(r'(?P<rec>DC-B1v31_62m_[a-z0-9_]+)-S230_neqE1e\+03_reg(?P<a>[0-9.]+)_n(?P<n>[0-9.]+)(_law(?P<law>ox|total))?\.csv$')


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


def proxy(t, mox, ka, n, sub=4):
    """Uniform-regression web [m] at the history's time points (RK2 with mox linear in each interval)."""
    D = np.empty_like(t); D[0] = D0; d = D0
    def rate(m, dd):
        if m <= 1e-6:
            return 0.0
        G = 4.0 * m / (math.pi * dd * dd)
        return 2.0 * ka * 1.0e-3 * (G / 300.0) ** n
    for k in range(1, len(t)):
        h = (t[k] - t[k - 1]) / sub
        for j in range(sub):
            m0 = mox[k - 1] + (mox[k] - mox[k - 1]) * j / sub; m1 = mox[k - 1] + (mox[k] - mox[k - 1]) * (j + 1) / sub
            k1 = rate(m0, d); k2 = rate(m1, min(d + h * k1, DOUT))
            d = min(d + 0.5 * h * (k1 + k2), DOUT)
        D[k] = d
    return (DOUT - D) / 2.0


def proxy_lag(t, mox, ka, n, kappa=1.2e-7, r_ign=0.3, sub=4):
    """As proxy(), plus grain_q1d's solid thermal lag: r_eff -> r_qs with tau = kappa/max(r_eff, r_qs)^2 clipped to
    [0.02, 2] s, r_eff = 0.3 r_qs at the first flow, and r_eff decaying with 0.05 s while mdot_ox = 0 (grain_q1d v2 step())."""
    D = np.empty_like(t); D[0] = D0; d = D0; re_ = 0.0
    for k in range(1, len(t)):
        h = (t[k] - t[k - 1]) / sub
        for j in range(sub):
            m = mox[k - 1] + (mox[k] - mox[k - 1]) * (j + 0.5) / sub
            if m > 1e-6:
                rq = ka * 1.0e-3 * ((4.0 * m / (math.pi * d * d)) / 300.0) ** n
                if re_ <= 0.0:
                    re_ = r_ign * rq
                tau = min(max(kappa / max(re_, rq, 1e-5) ** 2, 0.02), 2.0)
                re_ += (rq - re_) * min(1.0, h / tau)
            else:
                re_ *= math.exp(-h / 0.05)
            d = min(d + 2.0 * re_ * h, DOUT)
        D[k] = d
    return (DOUT - D) / 2.0


def t_at(t, w, target):
    i = np.where(w <= target)[0]
    if len(i) == 0:
        return None
    i = int(i[0])
    if i == 0:
        return float(t[0])
    return float(t[i - 1] + (target - w[i - 1]) * (t[i] - t[i - 1]) / (w[i] - w[i - 1]))


def main(d, out_f):
    rows = {}; files = sorted(glob.glob(os.path.join(d, 'lane*', '*.csv')))
    for f in files:
        m = PAT.search(os.path.basename(f))
        if not m:
            continue
        a, n, law = float(m.group('a')), float(m.group('n')), (m.group('law') or 'ox')
        r = pd.read_csv(f); t = r.t.values; mox = np.clip(r.mox.values, 0, None); w = r.w_min.values
        wp = proxy(t, mox, a, n); wl = proxy_lag(t, mox, a, n)
        live = w > 0
        key = os.path.relpath(f, d)
        row = dict(record=m.group('rec').replace('DC-B1v31_62m_', ''), a_band=a, n=n, law=law, history=key, history_sha256_16=sha16(f),
                   max_abs_dw_mm=float(1e3 * np.max(np.abs(wp[live] - w[live]))) if live.any() else None,
                   max_dw_proxy_minus_model_mm=float(1e3 * np.max(wp[live] - w[live])) if live.any() else None,
                   max_abs_dw_lagged_mm=float(1e3 * np.max(np.abs(wl[live] - w[live]))) if live.any() else None,
                   t_w1_lagged_s=t_at(t, wl, W_LIM),
                   dw_end_mm=float(1e3 * (wp[-1] - w[-1])),
                   t_w1_model_s=t_at(t, w, W_LIM), t_w1_proxy_s=t_at(t, wp, W_LIM),
                   t_w0_model_s=t_at(t, w, 0.0), t_w0_proxy_s=t_at(t, wp, 0.0), w_end_model_mm=float(1e3 * w[-1]), w_end_proxy_mm=float(1e3 * wp[-1]))
        if row['t_w1_model_s'] is not None and row['t_w1_proxy_s'] is not None:
            row['dt_w1_proxy_minus_model_s'] = row['t_w1_proxy_s'] - row['t_w1_model_s']
        if row['t_w1_model_s'] is not None and row['t_w1_lagged_s'] is not None:
            row['dt_w1_lagged_minus_model_s'] = row['t_w1_lagged_s'] - row['t_w1_model_s']
        if law == 'ox' and row['t_w1_model_s'] is not None:
            lo, hi = 0.9, 1.3
            for _ in range(40):
                mid = 0.5 * (lo + hi); tp = t_at(t, proxy(t, mox, a * mid, n), W_LIM)
                if tp is None or tp > row['t_w1_model_s']:
                    lo = mid
                else:
                    hi = mid
            row['k_on_a_for_quasi_steady_proxy_to_match_model_t_w1'] = 0.5 * (lo + hi)
        if law == 'total' and row['t_w1_model_s'] is not None:
            lo, hi = 0.9, 1.6
            for _ in range(40):
                mid = 0.5 * (lo + hi); tp = t_at(t, proxy(t, mox, a * mid, n), W_LIM)
                if tp is None or tp > row['t_w1_model_s']:
                    lo = mid
                else:
                    hi = mid
            row['k_on_a_for_ox_proxy_to_match_total_law_t_w1'] = 0.5 * (lo + hi)
        rows[key] = row
        print('%-60s dw max %6.3f mm  t_w1 model %s proxy %s  %s' % (key, row['max_abs_dw_mm'] or float('nan'),
              None if row['t_w1_model_s'] is None else round(row['t_w1_model_s'], 3), None if row['t_w1_proxy_s'] is None else round(row['t_w1_proxy_s'], 3),
              ('k=%.4f' % row['k_on_a_for_ox_proxy_to_match_total_law_t_w1']) if 'k_on_a_for_ox_proxy_to_match_total_law_t_w1' in row else ''))
    ox = [r for r in rows.values() if r['law'] == 'ox']
    dts = [r['dt_w1_proxy_minus_model_s'] for r in ox if 'dt_w1_proxy_minus_model_s' in r]
    ks = [r['k_on_a_for_ox_proxy_to_match_total_law_t_w1'] for r in rows.values() if 'k_on_a_for_ox_proxy_to_match_total_law_t_w1' in r]
    kq = [r['k_on_a_for_quasi_steady_proxy_to_match_model_t_w1'] for r in ox if 'k_on_a_for_quasi_steady_proxy_to_match_model_t_w1' in r]
    dtl = [r['dt_w1_lagged_minus_model_s'] for r in ox if 'dt_w1_lagged_minus_model_s' in r]
    summary = dict(n_ox_histories=len(ox), max_abs_dw_mm_ox=max(r['max_abs_dw_mm'] for r in ox if r['max_abs_dw_mm'] is not None),
                   max_dw_proxy_minus_model_mm_ox=max(r['max_dw_proxy_minus_model_mm'] for r in ox if r['max_dw_proxy_minus_model_mm'] is not None),
                   max_abs_dw_lagged_mm_ox=max(r['max_abs_dw_lagged_mm'] for r in ox if r['max_abs_dw_lagged_mm'] is not None),
                   dt_w1_lagged_minus_model_s_range=[min(dtl), max(dtl)] if dtl else None,
                   k_quasi_steady_range=[min(kq), max(kq)] if kq else None,
                   dt_w1_proxy_minus_model_s_range=[min(dts), max(dts)] if dts else None, n_dt=len(dts),
                   k_total_law_range=[min(ks), max(ks)] if ks else None)
    law = dict(state='port diameter D (uniform along the grain)', D0_m=D0, D_outer_m=DOUT, web='w = (D_outer - D)/2', limit_web_m=W_LIM,
               rate='dD/dt = 2 k_a 1.0e-3 (G_ox/300)^n  [m/s],  G_ox = 4 mdot_ox / (pi D^2)  [kg/m2s]',
               k_a='1.1 x a_meas/a_ref (lead rule); a_meas re-anchored at r(300 kg/m2s) and taken at the station of largest local regression',
               n='n_meas; evaluate both ends of its T1-T4 confidence band and keep the earlier t_L',
               coast='no regression while mdot_ox = 0',
               lagged_variant='optional second state r_eff: first-order lag to r_qs with tau = 1.2e-7/max(r_eff, r_qs)^2 s clipped to [0.02, 2] s, r_eff = 0.3 r_qs at the first flow, decay 0.05 s when mdot_ox = 0 (reproduces grain_q1d)',
               tags='DERIVED proxy of SIM grain_q1d v2.4 (oxidiser-flux law); ASSUMED until T1-T4')
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/burn_limit_proxy_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               law_for_gnc=law, verification=rows, summary=summary)
    json.dump(out, open(out_f, 'w'), indent=1)
    print(json.dumps(summary, indent=1)); print('wrote', out_f)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
