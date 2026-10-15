"""REV-COMB-3 reviewer script: FA-1 envelope tables and the LEAD line 173 load rule (independent of fa1_tables_v2p4a.py).

From the 896 stored cases of data/v2p4a/fa1_envelope_v2p4a.json (64b328150025fa1e; SIM on an ASSUMED construct, author's):
 (1) re-derive Table 7.6a (maxima by reading x entrance over O/F 4-12, tf 1-7 ms, residence, pool) and Table 7.6b (head peak by O/F x tf,
     max over residence and pool) and compare with REPORT v2.4a;
 (2) pressure SDOF spectrum (undamped, at rest, first-order-hold discretisation, unit-tested) of the head and aft gauge histories
     (P - 1.01325 bar) at periods 0.04-20 ms: equivalent static = 1.01325 + max k x.  Against line 173: 90 bar QS for every part;
     92 / 102 bar for parts with periods 0.25-1 ms.
     Histories beyond the stored 25 ms (reviewer extension, stated): the author's model adds the pool products at a constant rate over
     [0, tau_pool] (late_light_spike_v2p4.run), so the 25 ms value is held to tau_pool (an overestimate: the stored slope at 25 ms is
     -0.016 to -0.10 bar/ms), then decays to P_end with the post-spike time constant fitted on the stored histories (3.2-4.1 ms; 4.1 ms
     used).  Cases without a pool decay from the 25 ms value at once.  Bracket: the first-pass extension (25 ms value held to t_end,
     then a step to P_end) is kept as an upper bound;
 (3) thrust SDOF spectrum at periods 0.25-100 ms, F = Cf 1.35 x P_aft x A_t (the author's Cf band top), whole history and the part above
     the start-level steady thrust, against the interim rectangle 1.8 kN x 4 ms (analytic: 2F for T <= 2 t_d, else 2F sin(pi t_d / T)).
usage: python -I r3_fa1_check.py FA1_ENVELOPE_JSON OUT_JSON
"""
import hashlib, json, math, sys
import numpy as np
from scipy.signal import cont2discrete, lfilter

fj, out = sys.argv[1:3]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(fj) == '64b328150025fa1e', H16(fj)
D = json.load(open(fj)); C = D['cases']
tg = np.array(D['history_grid_ms']) * 1e-3
At = D['state']['A_t_m2']; PA = 1.01325
CF = 1.35


def sdof_max(t, f, T, t_stop):
    """Undamped SDOF x'' + w^2 x = w^2 f(t), at rest at t = 0, f linear between samples; returns max of x over [0, t_stop].
    Uniform grid dt = min(T/60, 2e-5 s) (f re-interpolated linearly), first-order-hold (ramp-invariant) discretisation, lfilter."""
    w = 2.0 * math.pi / T
    dt = min(T / 60.0, 2e-5)
    tt = np.arange(0.0, t_stop + dt / 2, dt)
    ff = np.interp(tt, t, f)
    sysd = cont2discrete(([w * w], [1.0, 0.0, w * w]), dt, method='foh')
    b = np.atleast_1d(np.squeeze(sysd[0])); a = np.atleast_1d(np.squeeze(sysd[1]))
    x = lfilter(b, a, ff)
    return float(x.max())


# self-test against the analytic undamped responses: unit rectangle of 4 ms (2 for T <= 8 ms, else 2 sin(pi td / T)) and a unit step (2)
SELFTEST = []
for T_, ref in ((2e-3, 2.0), (8e-3, 2.0), (20e-3, 2 * math.sin(math.pi * 4 / 20)), (50e-3, 2 * math.sin(math.pi * 4 / 50))):
    v_ = sdof_max(np.array([0.0, 1e-9, 4e-3, 4e-3 + 1e-9, 1.0]), np.array([0.0, 1.0, 1.0, 0.0, 0.0]), T_, 4e-3 + 2.5 * T_)
    SELFTEST.append(dict(T_s=T_, sdof=v_, analytic=ref)); assert abs(v_ / ref - 1.0) < 5e-3, (T_, v_, ref)
v_ = sdof_max(np.array([0.0, 1e-9, 1.0]), np.array([0.0, 1.0, 1.0]), 5e-3, 0.05)
SELFTEST.append(dict(T_s=5e-3, sdof_step=v_, analytic=2.0)); assert abs(v_ / 2.0 - 1.0) < 5e-3, v_


TAU_D = 4.1e-3      # largest post-spike decay time constant fitted on the 896 stored histories (3.2-4.1 ms)


def extended(case, node, mode='pool_end'):
    h = np.array(case[f'P_{node}_hist_bar'])
    t_end = case['t_end_ms'] * 1e-3; p_end = case['P_end_bar']
    if mode == 'hold_to_t_end':                         # first-pass bracket (upper bound)
        t = np.concatenate([tg, [max(t_end, tg[-1] + 1e-4), max(t_end, tg[-1] + 1e-4) + 1e-4, 0.40]])
        p = np.concatenate([h, [h[-1], p_end, p_end]])
        return t, p
    t0 = max(case['tau_pool_s'], tg[-1])                # end of the pool source (author's run()), or 25 ms without a pool
    tt = np.arange(tg[-1] + 1e-4, 0.40 + 5e-5, 1e-4)
    p = np.where(tt <= t0, h[-1], p_end + (h[-1] - p_end) * np.exp(-(tt - t0) / TAU_D))
    return np.concatenate([tg, tt]), np.concatenate([h, p])


def load_end(case):
    return max(case['tau_pool_s'], tg[-1]) + 10 * TAU_D


res = dict(script='r3_fa1_check.py', input=dict(fa1_envelope_v2p4a_json=H16(fj)), n_cases=len(C), sdof_selftest=SELFTEST)
# ---- (1) tables
def key_parts(k):
    rd, ent, of, tf, tr, pool = k.split('|')
    return rd, ent, float(of[2:]), float(tf[2:-2]), float(tr[4:]), pool
groups = {}
for k, c in C.items():
    rd, ent, of, tf, tr, pool = key_parts(k)
    if of < 4.0:
        continue
    g = groups.setdefault((rd, ent), dict(head=0, aft=0, a45=0, a45c=0, a675=0, a90=0, imp=0, rmin=9, rmax=0))
    g['head'] = max(g['head'], c['peak_head_bar']); g['aft'] = max(g['aft'], c['peak_aft_bar'])
    g['a45'] = max(g['a45'], c['above45_head_total_ms']); g['a45c'] = max(g['a45c'], c['above45_head_cont_ms'])
    g['a675'] = max(g['a675'], c['above67p5_head_total_ms']); g['a90'] = max(g['a90'], c['above90_head_total_ms'])
    g['imp'] = max(g['imp'], c['impulse_above_P0_25ms_head_bar_ms'])
    g['rmin'] = min(g['rmin'], c['aft_over_head_peak']); g['rmax'] = max(g['rmax'], c['aft_over_head_peak'])
res['table_7_6a'] = {f'{a}|{b}': v for (a, b), v in groups.items()}
t76b = {}
for k, c in C.items():
    rd, ent, of, tf, tr, pool = key_parts(k)
    if (rd, ent) in (('vapour_once', 'rounded_Cd1.0'), ('as_written', 'sharp_Cd0.65')):
        kk = f'OF{of:g}|tf{tf:g}'
        t76b.setdefault(kk, {}); lab = 'baseline' if rd == 'vapour_once' else 'upper'
        t76b[kk][lab] = max(t76b[kk].get(lab, 0.0), c['peak_head_bar'])
res['table_7_6b'] = t76b

# ---- (2) pressure SDOF spectrum on the governing cases (the 16 highest head peaks per reading x entrance, plus every tf 1 ms, 5 ms case at O/F 3.5-5)
PER_P = [0.04, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0]
sel = set()
for (rd, ent) in groups:
    ks = sorted([k for k in C if k.startswith(f'{rd}|{ent}|')], key=lambda k: -C[k]['peak_head_bar'])[:16]
    sel.update(ks)
for k in C:
    rd, ent, of, tf, tr, pool = key_parts(k)
    if 3.5 <= of <= 5 and tf in (1.0, 2.0, 3.0, 5.0) and tr == 0.06 and pool != 'none':
        sel.add(k)
spec = {}
for k in sorted(sel):
    c = C[k]; row = {}
    for node in ('head', 'aft'):
        t, p = extended(c, node)
        g = p - PA
        row[node] = [PA + sdof_max(t, g, T * 1e-3, load_end(c) + 2.5 * T * 1e-3) for T in PER_P]
        tb, pb = extended(c, node, 'hold_to_t_end')
        row[node + '_hold_bracket'] = [PA + sdof_max(tb, pb - PA, T * 1e-3, c['t_end_ms'] * 1e-3 + 2.5 * T * 1e-3) for T in PER_P]
    spec[k] = row
res['pressure_equiv_static_bar'] = dict(periods_ms=PER_P, cases=spec)
env = {}
for rd_ent in [f'{a}|{b}' for (a, b) in groups] + ['all']:
    ks = [k for k in spec if rd_ent == 'all' or k.startswith(rd_ent + '|')]
    for node in ('head', 'aft', 'head_hold_bracket', 'aft_hold_bracket'):
        env[f'{rd_ent}|{node}'] = [max(spec[k][node][i] for k in ks) for i in range(len(PER_P))]
res['pressure_equiv_static_envelope_bar'] = env

# ---- (3) thrust SDOF spectrum
PER_F = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 70.0, 100.0]
rect = lambda T: 2 * 1800.0 * (1.0 if T <= 8.0 else math.sin(math.pi * 4.0 / T))
F_steady = CF * C[next(iter(C))]['P_end_bar'] * 1e5 * At
fspec = {}
for k in sorted(sel):
    c = C[k]
    Fs = CF * c['P_end_bar'] * 1e5 * At
    t, p = extended(c, 'aft')
    F = CF * p * 1e5 * At
    ts = lambda T: load_end(c) + 2.5 * T * 1e-3
    tb, pb = extended(c, 'aft', 'hold_to_t_end')
    Fb = CF * pb * 1e5 * At
    tsb = lambda T: c['t_end_ms'] * 1e-3 + 2.5 * T * 1e-3
    fspec[k] = dict(whole=[sdof_max(t, F, T * 1e-3, ts(T)) for T in PER_F],
                    above_steady=[sdof_max(t, F - Fs, T * 1e-3, ts(T)) for T in PER_F],
                    impulse_above_steady_Ns=float(np.trapezoid(F - Fs, t)),
                    whole_hold_bracket=[sdof_max(tb, Fb, T * 1e-3, tsb(T)) for T in PER_F],
                    above_steady_hold_bracket=[sdof_max(tb, Fb - Fs, T * 1e-3, tsb(T)) for T in PER_F],
                    impulse_above_steady_hold_bracket_Ns=float(np.trapezoid(Fb - Fs, tb)))
mx = lambda key: [max(fspec[k][key][i] for k in fspec) for i in range(len(PER_F))]
fenv = dict(periods_ms=PER_F, rect_N=[rect(T) for T in PER_F],
            whole_max_N=mx('whole'), above_steady_max_N=mx('above_steady'),
            whole_hold_bracket_max_N=mx('whole_hold_bracket'), above_steady_hold_bracket_max_N=mx('above_steady_hold_bracket'),
            arg_whole=[max(fspec, key=lambda k: fspec[k]['whole'][i]) for i in range(len(PER_F))],
            impulse_above_steady_max_Ns=max(v['impulse_above_steady_Ns'] for v in fspec.values()),
            impulse_above_steady_hold_bracket_max_Ns=max(v['impulse_above_steady_hold_bracket_Ns'] for v in fspec.values()),
            rect_impulse_Ns=1800.0 * 4e-3, F_steady_N=F_steady, tau_decay_s=TAU_D)
fenv['first_period_where_FA1_exceeds_rect_ms'] = next((T for T, a, r in zip(PER_F, fenv['whole_max_N'], fenv['rect_N']) if a > r), None)
fenv['first_period_where_FA1_above_steady_exceeds_rect_ms'] = next(
    (T for T, a, r in zip(PER_F, fenv['above_steady_max_N'], fenv['rect_N']) if a > r), None)
res['thrust_sdof'] = fenv
res['thrust_sdof_cases'] = fspec
# check against the author's stored SDOF values (periods 0.5-5 ms, window 0-30 ms)
au = {k: C[k]['F_sdof_Cf1.35_N'] for k in fspec}
mine05 = {}
for k in list(fspec)[:12]:
    t, p = extended(C[k], 'aft')
    mine05[k] = [sdof_max(t, CF * p * 1e5 * At, T * 1e-3, 0.030) for T in (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)]
res['author_sdof_check_max_rel'] = max(abs(m / a - 1.0) for k in mine05 for m, a in zip(mine05[k], au[k]))
json.dump(res, open(out, 'w'), indent=1)
print('Table 7.6a re-derived:')
for k, v in res['table_7_6a'].items():
    print('  %-28s head %.1f aft %.1f >45 %.2f (%.2f) >67.5 %.2f >90 %.2f imp %.0f aft/head %.3f-%.3f' % (
        k, v['head'], v['aft'], v['a45'], v['a45c'], v['a675'], v['a90'], v['imp'], v['rmin'], v['rmax']))
print('Table 7.6b re-derived (baseline / upper):')
for of in (3, 3.5, 4, 5, 6, 8, 10, 12):
    print('  OF %-4g' % of, ' '.join('%5.1f/%5.1f' % (t76b[f'OF{of:g}|tf{tf:g}']['baseline'], t76b[f'OF{of:g}|tf{tf:g}']['upper']) for tf in range(1, 8)))
print('pressure equivalent static [bar abs], periods', PER_P)
for k, v in env.items():
    print('  %-34s' % k, ' '.join('%6.1f' % x for x in v))
print('thrust SDOF [N], periods', PER_F)
print('  rect           ', ' '.join('%6.0f' % x for x in fenv['rect_N']))
print('  FA-1 whole     ', ' '.join('%6.0f' % x for x in fenv['whole_max_N']))
print('  FA-1 >stdy     ', ' '.join('%6.0f' % x for x in fenv['above_steady_max_N']))
print('  bracket whole  ', ' '.join('%6.0f' % x for x in fenv['whole_hold_bracket_max_N']))
print('  bracket >stdy  ', ' '.join('%6.0f' % x for x in fenv['above_steady_hold_bracket_max_N']))
print('  first period where FA-1 > rectangle: whole', fenv['first_period_where_FA1_exceeds_rect_ms'], 'ms, above steady',
      fenv['first_period_where_FA1_above_steady_exceeds_rect_ms'], 'ms; impulse above steady max %.1f N s (bracket %.1f; rect 7.2); F_steady %.1f N'
      % (fenv['impulse_above_steady_max_Ns'], fenv['impulse_above_steady_hold_bracket_max_Ns'], F_steady))
print('  governing cases:', fenv['arg_whole'])
print('author SDOF (0.5-5 ms, 30 ms window) reproduced, max rel diff %.2e' % res['author_sdof_check_max_rel'])
print('wrote', out, H16(out))
