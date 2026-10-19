"""Per-mode FA-1 equivalent pressure at FEA3D stress nodes from the published modal shares (Combustion v2.4b, 2026-10-19;
LEAD CHANGELOG 228 (c), lead request 2026-10-19 item 2).

Requested: Peq = sum_i share_i x S(T_i) at the TC-01 J-FWD node and the TC-01 LC1 node, all-case head spectrum, zeta 0 and a
justified damping, absolute sum and SRSS, frequency factors x0.85 / 0.90 / 1.00, residual (T < 0.195 ms) at the spectrum maximum
below 0.195 ms; TC-02 / TC-09 / NZ-01 governing nodes if cheap; say exactly what is missing.

Definitions (structural response linear in the gauge pressure g(t); shares c_i of the static unit-pressure stress, sum c_i + r = 1,
FEA3D modal_v351ca2b_c71; S_g = S - p_amb from fa1_spectra_damped_v2p4b.json, bar):
  signed  Peq = p_amb + sum_i c_i S_g(T_i/s) + r S_g,res(s)          (the formula as written: every modal peak simultaneous, with sign)
  ABS     Peq = p_amb + sum_i |c_i| S_g(T_i/s) + |r| S_g,res(s)      (rigorous upper bound of the linear modal response, given S)
  SRSS    Peq = p_amb + sqrt(sum_i (c_i S_g(T_i/s))^2 + (r S_g,res)^2)  (random-phase estimate; not a bound)
  S_g,res(s) = max of S_g over T <= T_min/s (T_min = 0.194914 ms, the period of the highest computed mode).
What FEA3D publishes per node (read only): residual share, signed and absolute share sums in the bins T > 20 / 1-20 / 0.1-1 /
<= 0.1 ms (FE periods), the 5 largest |c_i| (modal JSON) and, for the two TC-01 points, the 6 largest, modes 11-13 and the signed
cumulative shares below 2 kHz and 3 kHz (fa1_band_sensitivity.json).  The other c_i (51-55 of 60 per node) are NOT published, so
each combination is given as a rigorous interval: the unknown modes of a bin carry the bin's remaining absolute share A and signed
share C, each |c_j| <= the smallest published top-list |c| (cap); LP (HiGHS) bounds for the signed and absolute sums (sub-bin signed
sums used where published), vertex/water-filling bounds for the sum of squares.  No share is invented; the interval collapses to
a number when FEA3D publishes the full signed vector.
usage: python -I fa1_per_mode_peq_v2p4b.py DAMPED_JSON FEA3D_MODAL_JSON FEA3D_BAND_JSON OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, re, sys
import numpy as np
from scipy.optimize import linprog

EXPECT = {'damped_json': '3a84a905052d5364', 'modal_json': '9af80c657eed11ac', 'band_json': '794155b97167a784'}
P_AMB = 1.01325                       # bar (101325 Pa, the constant of fa1_envelope_v2p4a.PA)
ZETAS = (0.0, 0.02, 0.05)
SCALES = (1.00, 0.90, 0.85)
SPECTRA = ('head|all', 'aft|all', 'head|baseline')
BASIS = 'head|all'
NODES = [
    dict(key='TC-01_JFWD', part='TC-01', node=2785, band_point='TC-01 J-FWD (FA-1 governing, L1 node 8314)',
         role='TC-01 J-FWD, FA-1 governing (nearest L2 node, 0.55 mm from L1 node 8314)'),
    dict(key='TC-01_LC1', part='TC-01', node=2800, band_point='TC-01 LC1 governing (L1 node 8843, B1_21.65)',
         role='TC-01 LC1 governing B1_21.65 (nearest L2 node, 0.78 mm from L1 node 8843)'),
    dict(key='TC-02_FA1', part='TC-02', node=14242, role='TC-02 node carrying the FA-1 tags (FA1Q/D/U/S)'),
    dict(key='TC-02_LC1', part='TC-02', node=8035, role='TC-02 LC1 governing node'),
    dict(key='TC-09_FA1', part='TC-09', node=25719, role='TC-09 node carrying the FA-1 tags'),
    dict(key='TC-09_LC1_B1_2', part='TC-09', node=25238, role='TC-09 LC1 node (B1_2 / B1_1)'),
    dict(key='TC-09_LC1_B1_21', part='TC-09', node=26534, role='TC-09 LC1 node (B1_21.65 / B1_19)'),
    dict(key='NZ-01_FA1', part='NZ-01', node=32380, role='NZ-01 node carrying the FA1Q/D/U tags'),
    dict(key='NZ-01_LC1_FA1S', part='NZ-01', node=30938, role='NZ-01 LC1 B1_21.65 node (also FA1S tag)'),
    dict(key='NZ-01_LC1', part='NZ-01', node=32601, role='NZ-01 LC1 node (B1_19 / B1_2 / B1_1)'),
]
COLS = {'FA1Q': 90.0, 'FA1D': 93.0, 'FA1U': 102.0, 'FA1S': 151.04}


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def lp(cvec, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None):
    r = linprog(cvec, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    assert r.status == 0, r.message
    return r.fun


def abs_bounds(S, cap, A_lo, A_hi, subs):
    """min / max of sum a_j S_j, 0 <= a_j <= cap, A_lo <= sum a_j <= A_hi, sum over sub-bin k of a_j >= |D_k|."""
    n = len(S)
    if n == 0:
        return 0.0, 0.0
    A_ub = [[1.0] * n, [-1.0] * n]; b_ub = [A_hi, -A_lo]
    for idx, D in subs:
        A_ub.append([-1.0 if j in idx else 0.0 for j in range(n)]); b_ub.append(-abs(D))
    bnd = [(0.0, cap)] * n
    lo = lp(np.asarray(S), A_ub, b_ub, bounds=bnd)
    hi = -lp(-np.asarray(S), A_ub, b_ub, bounds=bnd)
    return lo, hi


def signed_bounds(S, cap, A_lo, A_hi, C, subs):
    """min / max of sum (p_j - n_j) S_j with p, n >= 0, p_j + n_j <= cap, A_lo <= sum (p + n) <= A_hi, sum (p - n) = C,
    sub-bin signed sums fixed (relaxation of |c_j| = p_j + n_j: a valid outer bound)."""
    n = len(S)
    if n == 0:
        return 0.0, 0.0
    S = np.asarray(S)
    cvec = np.concatenate([S, -S])
    A_ub = [list(np.ones(2 * n)), list(-np.ones(2 * n))]; b_ub = [A_hi, -A_lo]
    for j in range(n):
        row = np.zeros(2 * n); row[j] = 1.0; row[n + j] = 1.0
        A_ub.append(list(row)); b_ub.append(cap)
    A_eq = [list(np.concatenate([np.ones(n), -np.ones(n)]))]; b_eq = [C]
    for idx, D in subs:
        row = np.zeros(2 * n)
        for j in idx:
            row[j] = 1.0; row[n + j] = -1.0
        A_eq.append(list(row)); b_eq.append(D)
    bnd = [(0.0, None)] * (2 * n)
    lo = lp(cvec, A_ub, b_ub, A_eq, b_eq, bnd)
    hi = -lp(-cvec, A_ub, b_ub, A_eq, b_eq, bnd)
    return lo, hi


def sq_bounds(S, cap, A_lo, A_hi):
    """min / max of sum (a_j S_j)^2 with 0 <= a_j <= cap and A_lo <= sum a_j <= A_hi (sub-bin constraints dropped: valid bounds)."""
    S = np.asarray(sorted(S, reverse=True), float)
    n = len(S)
    if n == 0:
        return 0.0, 0.0
    A = min(A_hi, n * cap)
    hi, rem = 0.0, A
    for s in S:                                   # convex maximum at a vertex: caps on the largest S, remainder on the next
        a = min(cap, rem); hi += (a * s) ** 2; rem -= a
        if rem <= 0:
            break
    A = A_lo                                      # convex minimum: a_j = min(cap, lam / S_j^2), sum a_j = A_lo
    if A <= 0:
        return 0.0, hi
    w = 1.0 / S ** 2
    lo_l, hi_l = 0.0, cap / w.min() * 10 + 1.0
    for _ in range(200):
        lam = 0.5 * (lo_l + hi_l)
        if np.minimum(cap, lam * w).sum() < A:
            lo_l = lam
        else:
            hi_l = lam
    a = np.minimum(cap, hi_l * w)
    return float(((a * S) ** 2).sum()), hi


def parse_tags(tags):
    out = {}
    for t in tags:
        m = re.match(r'(FA1[QDUST])@A1_22\.2 MS (-?[0-9.]+)', t)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def main(damped_f, modal_f, band_f, out_f):
    got = {'damped_json': sha16(damped_f), 'modal_json': sha16(modal_f), 'band_json': sha16(band_f)}
    for k, v in EXPECT.items():
        assert v is None or got[k] == v, (k, got[k], v)
    DJ = json.load(open(damped_f)); MJ = json.load(open(modal_f)); BJ = json.load(open(band_f))
    assert MJ['run'] == 'modal_v351ca2b_c71' and BJ['run'] == 'modal_v351ca2b_c71' and MJ['n_modes'] == 60
    assert DJ['smoke_test_subset'] == 0, 'smoke-test spectra are never used'
    T_MIN = MJ['T_min_ms']
    f_fe = {m['mode']: m['f_Hz'] for m in MJ['modes']}
    T_fe = {m: 1e3 / f for m, f in f_fe.items()}
    bins_fe = {'1<T<=20ms': [m for m in f_fe if 1.0 < T_fe[m] <= 20.0], '0.1<T<=1ms': [m for m in f_fe if 0.1 < T_fe[m] <= 1.0]}
    assert all(T_fe[m] <= 20.0 for m in f_fe) and all(T_fe[m] > 0.1 for m in f_fe)
    # spectrum values at the modal periods, and the residual band maxima
    rows = {(r['mode'], r['scale']): r for r in DJ['modal_periods']}
    for (m, s), r in rows.items():
        assert abs(r['T_ms'] - 1e3 / (f_fe[m] * s)) < 1e-5
    resband = {}
    for s in SCALES:
        key = [k for k in DJ['band_maxima'] if k.endswith('_residual_s%.2f' % s)]
        assert len(key) == 1, key
        resband[s] = DJ['band_maxima'][key[0]]
    SF = {(x['part'], x['node']): x for x in MJ['stress_functionals']}
    nodes_out = {}
    for nd in NODES:
        x = SF[(nd['part'], nd['node'])]
        funcs = {}
        # principal functional: modal JSON record (bins with absolute sums, top 5) + band file extras for the TC-01 points
        known = {m: c for m, f, c in x['top_modes']}
        top_list = [abs(c) for m, f, c in x['top_modes']]
        sub_signed = None; extra_src = 'modal JSON stress_functionals: residual, 4 bins (signed, absolute), top 5'
        bp = None
        if 'band_point' in nd:
            bp = [n for n in BJ['points'][nd['band_point']]['nodes'] if n['node'] == nd['node']]
            assert len(bp) == 1 and bp[0]['nearest']
            bp = bp[0]
        if bp is not None:
            pr = bp['principal']
            assert abs(pr['residual'] - x['residual_share']) < 1e-9
            assert abs(pr['s1.00']['slow_T_gt_1ms'] - x['bins']['1<T<=20ms']['share']) < 1e-9
            assert abs(pr['s1.00']['abs_slow'] - x['bins']['1<T<=20ms']['abs_share']) < 1e-9
            assert abs(pr['s1.00']['mid_0p1_1ms'] - x['bins']['0.1<T<=1ms']['share']) < 1e-9
            for m, f, c in pr['top_modes']:
                if m in known:
                    assert abs(known[m] - c) < 1e-9
                known[m] = c
            for k, c in pr['mode_shares'].items():
                known[int(k.split('@')[0])] = c
            top_list = [abs(c) for m, f, c in pr['top_modes']]
            sub_signed = {'11-19': pr['cum_share_below_2kHz'] - pr['s1.00']['slow_T_gt_1ms'],
                          '20-34': pr['cum_share_below_3kHz'] - pr['cum_share_below_2kHz'],
                          '35-60': 1.0 - pr['residual'] - pr['cum_share_below_3kHz']}
            assert max(f_fe[m] for m in range(11, 20)) < 2000.0 < f_fe[20] and f_fe[34] < 3000.0 < f_fe[35]
            extra_src += '; fa1_band_sensitivity.json: top 6, modes 11-13, cumulative signed shares below 2 / 3 kHz'
        cap = min(top_list)
        tens = None
        if bp is not None:
            te = bp['tensor']
            tk = {m: c for m, f, c in te['top_modes']}
            for k, c in te['mode_shares'].items():
                tk[int(k.split('@')[0])] = c
            tens = dict(residual=te['residual'], known=tk, cap=min(abs(c) for m, f, c in te['top_modes']),
                        bins={'1<T<=20ms': dict(share=te['s1.00']['slow_T_gt_1ms'], abs_lo=te['s1.00']['abs_slow'],
                                                abs_hi=te['s1.00']['abs_slow']),
                              '0.1<T<=1ms': dict(share=te['s1.00']['mid_0p1_1ms'], abs_lo=None, abs_hi=None)},
                        sub_signed={'11-19': te['cum_share_below_2kHz'] - te['s1.00']['slow_T_gt_1ms'],
                                    '20-34': te['cum_share_below_3kHz'] - te['cum_share_below_2kHz'],
                                    '35-60': 1.0 - te['residual'] - te['cum_share_below_3kHz']},
                        source='fa1_band_sensitivity.json tensor functional: residual, slow (signed, absolute), mid (signed only: '
                               'absolute 0.1-1 ms sum NOT published -> bounded by the caps), top 6, modes 11-13, cumulative <2 / <3 kHz')
        prin = dict(residual=x['residual_share'], known=known, cap=cap,
                    bins={b: dict(share=x['bins'][b]['share'], abs_lo=x['bins'][b]['abs_share'], abs_hi=x['bins'][b]['abs_share'])
                          for b in bins_fe},
                    sub_signed=sub_signed, source=extra_src)
        funcs['principal'] = prin
        if tens is not None:
            funcs['tensor'] = tens
        node_res = dict(part=nd['part'], node=nd['node'], role=nd['role'], tags=x['tags'], static_MPa_per_MPa=x['static'],
                        functionals={})
        for fname, F in funcs.items():
            r = F['residual']; K = F['known']
            sum_known = sum(K.values())
            fres = dict(source=F['source'], residual_share=r, cap_abs_share_unpublished=F['cap'], known_modes={str(m): c for m, c in sorted(K.items())},
                        bins={}, results={})
            unk = {}
            for b, members in bins_fe.items():
                kn = [m for m in members if m in K]; U = [m for m in members if m not in K]
                C = F['bins'][b]['share'] - sum(K[m] for m in kn)
                if F['bins'][b]['abs_lo'] is None:
                    A_lo, A_hi = abs(C), len(U) * F['cap']
                    if F['sub_signed'] is not None and b == '0.1<T<=1ms':
                        A_lo = max(A_lo, sum(abs(F['sub_signed'][k] - sum(K[m] for m in kn if lo_ <= m <= hi_)) for k, (lo_, hi_) in
                                             (('11-19', (11, 19)), ('20-34', (20, 34)), ('35-60', (35, 60)))))
                else:
                    A_lo = A_hi = F['bins'][b]['abs_lo'] - sum(abs(K[m]) for m in kn)
                assert A_hi >= abs(C) - 1e-9 and A_lo <= len(U) * F['cap'] + 1e-9, (nd['key'], fname, b, A_lo, A_hi, C, len(U), F['cap'])
                subs = []
                if F['sub_signed'] is not None and b == '0.1<T<=1ms':
                    for k, (lo_, hi_) in (('11-19', (11, 19)), ('20-34', (20, 34)), ('35-60', (35, 60))):
                        idx = [j for j, m in enumerate(U) if lo_ <= m <= hi_]
                        D = F['sub_signed'][k] - sum(K[m] for m in kn if lo_ <= m <= hi_)
                        subs.append((set(idx), D))
                unk[b] = dict(U=U, C=C, A_lo=A_lo, A_hi=A_hi, subs=subs)
                fres['bins'][b] = dict(modes_in_bin=len(members), known=kn, n_unpublished=len(U), signed_unpublished=round(C, 6),
                                       abs_unpublished=[round(A_lo, 6), round(A_hi, 6)],
                                       sub_bin_signed_unpublished=({k: round(D, 6) for k, (_, D) in zip(('11-19', '20-34', '35-60'), subs)}
                                                                   if subs else None))
            assert abs(sum_known + sum(u['C'] for u in unk.values()) + r - 1.0) < 1e-6
            for spec in SPECTRA:
                for z in ZETAS:
                    for s in SCALES:
                        Sg = {m: rows[(m, s)]['%s|zeta%g' % (spec, z)] - P_AMB for m in f_fe}
                        rb = resband[s]['%s|zeta%g' % (spec, z)]
                        Sres = rb['value_bar'] - P_AMB
                        Ks = sum(c * Sg[m] for m, c in K.items()); Ka = sum(abs(c) * Sg[m] for m, c in K.items())
                        Kq = sum((c * Sg[m]) ** 2 for m, c in K.items())
                        sg = [0.0, 0.0]; ab = [0.0, 0.0]; sq = [0.0, 0.0]
                        for b, u in unk.items():
                            SU = [Sg[m] for m in u['U']]
                            assert min(SU) > 0
                            lo, hi = signed_bounds(SU, F['cap'], u['A_lo'], u['A_hi'], u['C'], u['subs']); sg[0] += lo; sg[1] += hi
                            lo, hi = abs_bounds(SU, F['cap'], u['A_lo'], u['A_hi'], u['subs']); ab[0] += lo; ab[1] += hi
                            lo, hi = sq_bounds(SU, F['cap'], u['A_lo'], u['A_hi']); sq[0] += lo; sq[1] += hi
                        res = dict(
                            S_res_bar_abs=rb['value_bar'], S_res_at_ms=rb['period_ms'],
                            known_part_bar=dict(signed=round(Ks, 3), abs=round(Ka, 3), srss_sq=round(Kq, 3)),
                            signed=[round(P_AMB + Ks + sg[0] + r * Sres, 2), round(P_AMB + Ks + sg[1] + r * Sres, 2)],
                            ABS=[round(P_AMB + Ka + ab[0] + abs(r) * Sres, 2), round(P_AMB + Ka + ab[1] + abs(r) * Sres, 2)],
                            SRSS=[round(P_AMB + math.sqrt(Kq + sq[0] + (r * Sres) ** 2), 2),
                                  round(P_AMB + math.sqrt(Kq + sq[1] + (r * Sres) ** 2), 2)])
                        fres['results']['%s|zeta%g|s%.2f' % (spec, z, s)] = res
            node_res['functionals'][fname] = fres
        # break-even pressures (FEA3D tags; MS = yield margin, as verified on the J-FWD node against fa1_columns_at_JFWD)
        ms = parse_tags(x['tags'])
        be = {c: round(COLS[c] * (1.0 + v), 2) for c, v in ms.items() if c in COLS}
        node_res['breakeven_bar_abs_from_tags'] = be or None
        nodes_out[nd['key']] = node_res
    # J-FWD margins at the FEA3D break-even values (lead: compare with 116.3 / 125.8 bar)
    cj = BJ['fa1_columns_at_JFWD']
    Pby, Pbu = cj['FA1D']['breakeven_bar_yield'], cj['FA1U']['breakeven_bar_ult']
    spread_y = [min(v['breakeven_bar_yield'] for v in cj.values()), max(v['breakeven_bar_yield'] for v in cj.values())]
    spread_u = [min(v['breakeven_bar_ult'] for v in cj.values()), max(v['breakeven_bar_ult'] for v in cj.values())]
    jf = nodes_out['TC-01_JFWD']['functionals']['principal']['results']
    margins = {}
    for k, v in jf.items():
        margins[k] = {comb: dict(MS_y=[round(Pby / v[comb][1] - 1.0, 3), round(Pby / v[comb][0] - 1.0, 3)],
                                 MS_u=[round(Pbu / v[comb][1] - 1.0, 3), round(Pbu / v[comb][0] - 1.0, 3)]) for comb in ('signed', 'ABS', 'SRSS')}
    # closely spaced modes 22 / 23: CQC correlation (Der Kiureghian form, equal damping)
    rr = f_fe[22] / f_fe[23]
    cqc = {('zeta%g' % z): (round(8 * z * z * (1 + rr) * rr ** 1.5 / ((1 - rr * rr) ** 2 + 4 * z * z * rr * (1 + rr) ** 2), 3) if z > 0 else 0.0)
           for z in ZETAS}
    out = dict(
        version='v2.4b', date='2026-10-19', script='02-combustion/src/fa1_per_mode_peq_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
        request='LEAD 2026-10-19 item 2 / CHANGELOG 228 (c)',
        inputs=dict(damped_json='data/v2p4b/fa1_spectra_damped_v2p4b.json %s' % got['damped_json'],
                    fea3d_modal_json='04-fea/assembly3d/results/modal_modal_v351ca2b_c71.json %s' % got['modal_json'],
                    fea3d_band_json='04-fea/assembly3d/results/fa1_band_sensitivity.json %s' % got['band_json']),
        definitions=__doc__.split('Definitions')[1].split('usage:')[0].strip(),
        basis=dict(spectrum=BASIS, others=[s for s in SPECTRA if s != BASIS], zetas=ZETAS, scales=SCALES, p_amb_bar=P_AMB, T_min_FE_ms=T_MIN,
                   bins_FE=dict((b, [min(v), max(v)]) for b, v in bins_fe.items())),
        nodes=nodes_out,
        jfwd_breakeven=dict(yield_bar_abs=round(Pby, 2), ult_bar_abs=round(Pbu, 2), source='fa1_columns_at_JFWD FA1D (yield) / FA1U (ultimate), '
                            'P x (1 + MS)', spread_over_columns=dict(yield_=[round(x, 2) for x in spread_y], ult=[round(x, 2) for x in spread_u]),
                            margins_at_Peq_interval=margins, note='MS = P_be / Peq - 1 (stress proportional to pressure, FEA3D 9A method); '
                            'interval ends ordered [at the upper Peq, at the lower Peq]'),
        cqc_rho_modes_22_23=dict(f_ratio=round(rr, 5), rho=cqc, note='correlation of the 2134 / 2157 Hz pair: near 1 for zeta >= 0.02, so '
                                 'SRSS under-combines this pair; the grouped (absolute) sum of 22 + 23 is the defensible estimate'),
        missing=dict(item='FEA3D: the full signed share vector c_i (60 modes) of the principal functional (and of the tensor functional, plus '
                          'its 0.1-1 ms absolute sum) at every assessed node, run modal_v351ca2b_c71 (fa1_band_sensitivity.py already forms it); '
                          'without it the per-mode Peq is an interval, not a number', owner='FEA3D (Mechanical)'),
        tags=dict(spectra='DERIVED (SDOF) from SIM histories (v2.4a construct, ASSUMED inputs)',
                  shares='SIM (FEA3D modal_v351ca2b_c71, coarsened all-L2, unstressed, rigid airframe; read only)',
                  damping='ASSUMED (0.02 design value, 0.05 sensitivity; 0 = bound); no modal test', bounds='DERIVED (LP / vertex bounds)',
                  breakeven='SIM (FEA3D columns; tags read as yield MS, verified at J-FWD only)', status='not physical evidence'))
    json.dump(out, open(out_f, 'w'), indent=1)
    print('wrote', out_f, sha16(out_f))
    for key in ('TC-01_JFWD', 'TC-01_LC1'):
        for fn in nodes_out[key]['functionals']:
            for z in ZETAS:
                for s in SCALES:
                    v = nodes_out[key]['functionals'][fn]['results']['%s|zeta%g|s%.2f' % (BASIS, z, s)]
                    print(key, fn, 'z', z, 's', s, 'signed', v['signed'], 'ABS', v['ABS'], 'SRSS', v['SRSS'], 'Sres', v['S_res_bar_abs'])


if __name__ == '__main__':
    main(*sys.argv[1:5])
