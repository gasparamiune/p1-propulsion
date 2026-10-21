"""REV-COMB-4 reviewer script: containment check of the author's TC-01 J-FWD per-mode Peq intervals (REPORT Table 16.4a; handback
signed 101.5-109.4, absolute 137.3-147.9 bar abs at zeta 0) and the ca2b -> ca2c effect (REV-COMB-4 item (d)).

A crude but rigorous interval from the published BIN data only (no top-mode detail, no caps): for each FE-period bin b (0.1-1 ms,
1-20 ms) with signed share C_b and absolute share A_b, the positive part P_b = (A_b + C_b) / 2 and negative part N_b = (A_b - C_b) / 2
sit anywhere in the bin's true-period range [T_lo / s, T_hi / s], so
  signed in [p_amb + sum_b (P_b Smin_b - N_b Smax_b) + r S_res,  p_amb + sum_b (P_b Smax_b - N_b Smin_b) + r S_res]
  absolute <= p_amb + sum_b A_b Smax_b + |r| S_res
with S_g = S - p_amb the reviewer's exact undamped all-case head envelope (r4_fa1_spectrum_cases.npz, 790 periods, reproduces the
published zeta-0 column to 0.0005 bar) and S_res = max S_g over T <= T_min / s (the author's residual rule).  The author's LP intervals
use more information and must lie INSIDE these.  Frequency factors s = 1.00 / 0.90 / 0.85 (T_true = T_FE / s).
Tags: shares SIM (FEA3D, read only); spectrum DERIVED; intervals DERIVED.
usage: python -I r4_per_mode_crude.py CASES_NPZ MODAL_CA2B_JSON MODAL_CA2C_JSON OUT_JSON
"""
import hashlib, json, sys
import numpy as np

cases_f, b_f, c_f, out_f = sys.argv[1:5]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(b_f) == '9af80c657eed11ac' and H16(c_f) == '619272cd3b66072b'
PAMB = 1.01325
C = np.load(cases_f)
per = C['periods_ms'].astype(float); Sg = C['S_head'].astype(float).max(axis=0) - PAMB


def smax(lo, hi):
    m = (per >= lo - 1e-12) & (per <= hi + 1e-12)
    return float(Sg[m].max()), float(Sg[m].min())


AUTHOR = {'1.00': dict(signed=(101.5, 106.5), abs=(137.3, 143.5)), '0.90': dict(signed=(101.6, 106.9), abs=(138.9, 145.2)),
          '0.85': dict(signed=(103.7, 109.4), abs=(141.3, 147.9))}
res = dict(script='r4_per_mode_crude.py', script_sha16=H16(sys.argv[0]), cases_npz=H16(cases_f), modal_ca2b=H16(b_f), modal_ca2c=H16(c_f),
           p_amb_bar=PAMB, runs={})
for lab, f in (('ca2b', b_f), ('ca2c', c_f)):
    M = json.load(open(f))
    node = [n for n in M['stress_functionals'] if n['node'] == 2785][0]
    Tmin = float(M['T_min_ms']); r = float(node['residual_share'])
    bins = {k: (float(v['share']), float(v['abs_share'])) for k, v in node['bins'].items()}
    out = dict(run=M['run'], T_min_ms=Tmin, residual=r, bins=bins, by_s={})
    for s in (1.00, 0.90, 0.85):
        Sres, _ = smax(per.min(), Tmin / s)
        lo = hi = PAMB + r * Sres; ab = PAMB + abs(r) * Sres
        for k, (Cb, Ab) in bins.items():
            if Ab == 0.0:
                continue
            Tlo, Thi = {'0.1<T<=1ms': (0.1, 1.0), '1<T<=20ms': (1.0, 20.0)}[k]
            mx, mn = smax(Tlo / s, Thi / s)
            Pb, Nb = (Ab + Cb) / 2, (Ab - Cb) / 2
            lo += Pb * mn - Nb * mx; hi += Pb * mx - Nb * mn; ab += Ab * mx
        a = AUTHOR[f'{s:.2f}']
        out['by_s'][f'{s:.2f}'] = dict(S_res_g_bar=round(Sres, 3), signed_crude=[round(lo, 2), round(hi, 2)], abs_crude_upper=round(ab, 2),
                                      author_signed=a['signed'], author_abs=a['abs'],
                                      author_inside=bool(lo <= a['signed'][0] and a['signed'][1] <= hi and a['abs'][1] <= ab))
    res['runs'][lab] = out
d = {}
for s in ('1.00', '0.90', '0.85'):
    b = res['runs']['ca2b']['by_s'][s]; c = res['runs']['ca2c']['by_s'][s]
    d[s] = dict(signed_lo=round(c['signed_crude'][0] - b['signed_crude'][0], 3), signed_hi=round(c['signed_crude'][1] - b['signed_crude'][1], 3),
                abs_upper=round(c['abs_crude_upper'] - b['abs_crude_upper'], 3))
res['ca2c_minus_ca2b_crude_bar'] = d
json.dump(res, open(out_f, 'w'), indent=1)
print(json.dumps(res, indent=1))
