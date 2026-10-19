"""Time-domain modal-superposition bound of the FA-1 equivalent pressure at the TC-01 nodes (Combustion v2.4b, 2026-10-19;
LEAD 2026-10-19 item 2, CHANGELOG 228 (c); companion of fa1_per_mode_peq_v2p4b.py, which evaluates the spectral sums as asked).

Why: for a stress functional with modal shares c_i (sum c_i + r = 1, FEA3D modal_v351ca2b_c71) under the gauge history g(t),
  sigma(t) / sigma_static = sum_i c_i q_i(t) + r q_res(t) = g(t) + sum_i c_i e_i(t) + r e_res(t),   e_i = q_i - g,
q_i the SDOF response (static gain 1, from rest).  Hence, with K the published modes and U the unpublished ones,
  Peq = p_amb + max_t sigma  <=  p_amb + max_t [g + sum_K c_i e_i]  +  sum_U |c_j| E_j  +  |r| E_res        (TH bound)
  Peq                        <=  p_amb + max_t g + sum_all |c_i| E_i + |r| E_res                             (E rule)
E_j = bound of max_t |e_j| (relative, 'dynamic increment' spectrum), E_res = max of E over T <= T_min / s.  Both are exact in the
static limit (e = 0 gives p_amb + max g); the spectral ABS sum is not (it returns sum |c_i| + |r| = 1.345 x P at J-FWD for a static
load) and neither is SRSS (0.55 x P).  The known modes are combined coherently in time (sampled at 16 points per 0.05 ms step); the
unpublished modes carry their bin's remaining absolute share with |c_j| <= the smallest published |c| (LP bound, as in
fa1_per_mode_peq_v2p4b.py); the residual is one lumped term as FEA3D defines it (its absolute content is not published).
E exactly: inside a 0.05 ms step g is linear (slope s), so e = -2 zeta s / omega + exp(-zeta omega tau) (C1 cos omega_d tau +
C2 sin omega_d tau) (exact recurrence at the knots); max |e| is taken at the step ends and at every stationary point inside the
step; after the record the history is held (s = 0) and the free decay's first two extrema are added (zeta 0: the sup over all
later time).
Inputs: 896 solver histories (fa1_histories_solver_v2p4b.npz 399bf43d1c09de24), head node, published convention max(b, c).
Tags: histories SIM (v2.4a construct, ASSUMED inputs); shares SIM (FEA3D, read only); bounds DERIVED; damping ASSUMED.
usage: python -I fa1_modal_th_bound_v2p4b.py NPZ SPECTRA_JSON FEA3D_MODAL_JSON FEA3D_BAND_JSON OUT_JSON OUT_CSV
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fa1_spectra_v2p4b as FS          # noqa: E402
import fa1_spectra_dense_v2p4b as FD    # noqa: E402
import fa1_per_mode_peq_v2p4b as PM     # noqa: E402  (share reading and LP bounds)

EXPECT = {'npz': '399bf43d1c09de24', 'spectra_json': '372b8078d7a90e75', 'modal_json': '9af80c657eed11ac', 'band_json': '794155b97167a784'}
EXPECT_SRC = {'fa1_spectra_v2p4b.py': 'bb510e33dec78405', 'fa1_spectra_dense_v2p4b.py': '910fdbf52a41918f', 'fa1_per_mode_peq_v2p4b.py': '688e4dd2e7affc8d'}
PA = FS.PA
DT = 5.0e-5
M_SUB = 16
ZETAS = (0.0, 0.02, 0.05)
SCALES = (1.00, 0.90, 0.85)
BASE, ALLG = 'vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'
GROUPS = (BASE, ALLG)
TC01 = [n for n in PM.NODES if n['part'] == 'TC-01']
SMOKE = int(os.environ.get('FA1_TH_SMOKE', '0'))
TWO_PI = 2.0 * math.pi


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def consts(periods, zetas):
    w = TWO_PI / np.asarray(periods, float)
    Z = np.asarray(zetas, float)[:, None]
    W = np.broadcast_to(w[None, :], (len(zetas), len(w))).copy()
    wd = W * np.sqrt(1.0 - Z * Z)
    return Z, W, wd, Z * W


def e_bound(G, periods, zetas):
    """Exact max_t |q - g| per row (rows, nz, np), gauge units of G.  Inside each step e(tau) = e_p + exp(-zeta w tau)
    (C1 cos wd tau + C2 sin wd tau) is evaluated at the step end and at every stationary point inside the step
    (tau_k = (x0 + k pi) / wd, tan(wd tau) = -P / Q); after the record (history held) at the first two stationary points of the
    free decay (for zeta 0 the second equals the amplitude, the sup over all later time)."""
    nr, nt = G.shape
    Z, W, wd, ZW = consts(periods, zetas)
    e1, c1, s1 = np.exp(-ZW * DT), np.cos(wd * DT), np.sin(wd * DT)
    K = int(np.max(np.floor(wd * DT / math.pi))) + 1
    u = np.zeros((nr,) + W.shape); v = np.zeros_like(u)
    Em = np.broadcast_to(np.abs(G[:, 0])[:, None, None], u.shape).copy()        # e(0) = 0 - g(0) (from rest)
    tz = (2.0 * Z / W)[None]
    ZWb, wdb = ZW[None], wd[None]
    for i in range(nt - 1):
        Fi = G[:, i][:, None, None]; sl = ((G[:, i + 1] - G[:, i]) / DT)[:, None, None]
        a = Fi - tz * sl
        C1 = u - a; C2 = (v - sl + ZWb * C1) / wdb
        P = -ZWb * C1 + wdb * C2; Q = -ZWb * C2 - wdb * C1
        x0 = np.mod(np.arctan2(-P, Q), math.pi)
        ep = -tz * sl
        for k in range(K):
            tau = (x0 + k * math.pi) / wdb
            ek = np.abs(ep + np.exp(-ZWb * tau) * (C1 * np.cos(wdb * tau) + C2 * np.sin(wdb * tau)))
            np.maximum(Em, np.where(tau <= DT, ek, 0.0), out=Em)
        un = a + sl * DT + e1[None] * (C1 * c1[None] + C2 * s1[None])
        v = sl + e1[None] * ((-ZWb * C1 + wdb * C2) * c1[None] + (-ZWb * C2 - wdb * C1) * s1[None])
        u = un
        np.maximum(Em, np.abs(un - G[:, i + 1][:, None, None]), out=Em)
    Fe = G[:, -1][:, None, None]
    C1 = u - Fe; C2 = (v + ZWb * C1) / wdb
    P = -ZWb * C1 + wdb * C2; Q = -ZWb * C2 - wdb * C1
    x0 = np.mod(np.arctan2(-P, Q), math.pi)
    for k in range(2):
        tau = (x0 + k * math.pi) / wdb
        np.maximum(Em, np.abs(np.exp(-ZWb * tau) * (C1 * np.cos(wdb * tau) + C2 * np.sin(wdb * tau))), out=Em)
    return Em


def th_known(G, periods, zetas, Wt, wsum):
    """Coherent sum per row: max_t [g (1 - wsum_k) + sum_j Wt[k, j] q_j] for each combination k (rows, nz, nk); also the
    post-record sup g_end + sum_j |Wt[k, j]| R_j,end.  Sampled at M_SUB points per step."""
    nr, nt = G.shape
    Z, W, wd, ZW = consts(periods, zetas)
    tau = DT * np.arange(1, M_SUB + 1) / M_SUB
    E = np.exp(-ZW[:, :, None] * tau[None, None, :]); Ec = E * np.cos(wd[:, :, None] * tau); Es = E * np.sin(wd[:, :, None] * tau)
    e1, c1, s1 = E[:, :, -1], np.cos(wd * DT), np.sin(wd * DT)
    nk = Wt.shape[0]
    u = np.zeros((nr,) + W.shape); v = np.zeros_like(u)
    best = np.full((nr, len(zetas), nk), -np.inf)
    one_minus = (1.0 - wsum)[None, None, :, None]
    for i in range(nt - 1):
        Fi = G[:, i][:, None, None]; sl = ((G[:, i + 1] - G[:, i]) / DT)[:, None, None]
        a = Fi - 2.0 * Z[None] * sl / W[None]
        C1 = u - a; C2 = (v - sl + ZW[None] * C1) / wd[None]
        q = a[..., None] + sl[..., None] * tau + C1[..., None] * Ec[None] + C2[..., None] * Es[None]      # (nr, nz, np, m)
        g = (G[:, i][:, None] + ((G[:, i + 1] - G[:, i]) / DT)[:, None] * tau[None, :])[:, None, None, :]  # (nr, 1, 1, m)
        s_k = np.einsum('kj,rzjm->rzkm', Wt, q) + one_minus * g
        np.maximum(best, s_k.max(axis=-1), out=best)
        u = q[..., -1]
        v = sl + e1[None] * ((-ZW[None] * C1 + wd[None] * C2) * c1[None] + (-ZW[None] * C2 - wd[None] * C1) * s1[None])
    Fe = G[:, -1][:, None, None]
    C1 = u - Fe; C2 = (v + ZW[None] * C1) / wd[None]
    R = np.hypot(C1, C2)                                                  # (nr, nz, np)
    post = G[:, -1][:, None, None] + np.einsum('kj,rzj->rzk', np.abs(Wt), R)
    return np.maximum(best, post), post


def main(npz_f, spec_json, modal_json, band_json, out_f, out_csv):
    t0w = time.time()
    for lab, f in (('npz', npz_f), ('spectra_json', spec_json), ('modal_json', modal_json), ('band_json', band_json)):
        assert sha16(f) == EXPECT[lab], (lab, sha16(f))
    for f, h in EXPECT_SRC.items():
        assert h is None or sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    SJ = json.load(open(spec_json)); MJ = json.load(open(modal_json)); BJ = json.load(open(band_json))
    assert MJ['run'] == 'modal_v351ca2b_c71' and MJ['n_modes'] == 60
    T_MIN = MJ['T_min_ms']
    f_fe = {m['mode']: m['f_Hz'] for m in MJ['modes']}
    SF = {(x['part'], x['node']): x for x in MJ['stress_functionals']}
    # ---- shares (principal functional), as fa1_per_mode_peq_v2p4b.py
    share = {}
    for nd in TC01:
        x = SF[(nd['part'], nd['node'])]
        bp = [n for n in BJ['points'][nd['band_point']]['nodes'] if n['node'] == nd['node']][0]['principal']
        K = {m: c for m, f, c in x['top_modes']}
        for m, f, c in bp['top_modes']:
            assert m not in K or abs(K[m] - c) < 1e-9
            K[m] = c
        for k, c in bp['mode_shares'].items():
            K[int(k.split('@')[0])] = c
        cap = min(abs(c) for m, f, c in bp['top_modes'])
        sub = {'11-19': bp['cum_share_below_2kHz'] - bp['s1.00']['slow_T_gt_1ms'],
               '20-34': bp['cum_share_below_3kHz'] - bp['cum_share_below_2kHz'],
               '35-60': 1.0 - bp['residual'] - bp['cum_share_below_3kHz']}
        share[nd['key']] = dict(K=K, r=x['residual_share'], cap=cap, bins=x['bins'], sub=sub)
    known_modes = sorted(set(m for v in share.values() for m in v['K']))
    # ---- histories (head node; rows b and, where unclipped, c)
    Zf = np.load(npz_f)
    keys = [str(k) for k in Zf['case_keys']]; off = Zf['offsets']
    assert len(keys) == 896 and keys == list(SJ['cases'].keys())
    sel_cases = [i for i in range(896) if not (SMOKE and i % SMOKE)]
    meta = {k: SJ['cases'][k] for k in keys}
    nt = int(np.diff(off).max())
    rows, row_case = [], []
    for i in sel_cases:
        a, b = int(off[i]), int(off[i + 1])
        ph = Zf['P_head_bar'][a:b].astype(float) * 1e5; pa = Zf['P_aft_bar'][a:b].astype(float) * 1e5
        cand = [np.maximum(ph - PA, 0.0)]
        if min(ph.min(), pa.min()) < PA:
            cand.append(ph - PA)
        for g in cand:
            gp = np.empty(nt); gp[:len(g)] = g; gp[len(g):] = g[-1]
            rows.append(gp); row_case.append(i)
    G = np.vstack(rows); row_case = np.array(row_case)
    print('rows', G.shape, round(time.time() - t0w, 1), 's', flush=True)

    def sel_rows(lab):
        init, ent, ofs, pool = lab.split('|')
        ok = set(i for i in sel_cases if (init == 'all' or meta[keys[i]]['init'] == init) and (ent == 'all' or meta[keys[i]]['entrance'] == ent)
                 and (ofs == 'incl_OF3-3.5' or meta[keys[i]]['OF'] in FD.FE.OFS_GRID) and (pool == 'all' or meta[keys[i]]['pool'] == pool))
        return np.array([j for j, i in enumerate(row_case) if i in ok])
    RS = {g: sel_rows(g) for g in GROUPS}
    # ---- checks of the method on synthetic and real rows (cheap)
    tchk = np.arange(nt) * DT
    ramp = np.clip(tchk / 0.05, 0.0, 1.0) * 80e5                                    # 50 ms ramp to 80 bar, then held
    syn = np.vstack([ramp])
    Psyn = np.array([1e3 / f_fe[m] for m in known_modes]) * 1e-3
    Wt_syn = np.full((1, len(Psyn)), 1.0 / len(Psyn) * 0.6)
    thr, _ = th_known(syn, Psyn, (0.0,), Wt_syn, Wt_syn.sum(axis=1))
    static_check = float(thr.max() / ramp.max() - 1.0)
    Eb = e_bound(G[:4], Psyn[:3], (0.0, 0.05))
    # sampled |e| on the same rows for the bound check
    Zc, Wc, wdc, ZWc = consts(Psyn[:3], (0.0, 0.05))
    tau = DT * np.arange(1, 65) / 64
    Ex = np.exp(-ZWc[:, :, None] * tau); Ecx = Ex * np.cos(wdc[:, :, None] * tau); Esx = Ex * np.sin(wdc[:, :, None] * tau)
    u = np.zeros((4,) + Wc.shape); v = np.zeros_like(u); es = np.zeros_like(u)
    for i in range(nt - 1):
        Fi = G[:4, i][:, None, None]; sl = ((G[:4, i + 1] - G[:4, i]) / DT)[:, None, None]
        a = Fi - 2.0 * Zc[None] * sl / Wc[None]; C1 = u - a; C2 = (v - sl + ZWc[None] * C1) / wdc[None]
        q = a[..., None] + sl[..., None] * tau + C1[..., None] * Ecx[None] + C2[..., None] * Esx[None]
        gg = (G[:4, i][:, None] + ((G[:4, i + 1] - G[:4, i]) / DT)[:, None] * tau[None, :])[:, None, None, :]
        es = np.maximum(es, np.abs(q - gg).max(axis=-1))
        u = q[..., -1]
        v = sl + Ex[:, :, -1][None] * ((-ZWc[None] * C1 + wdc[None] * C2) * np.cos(wdc * DT)[None]
                                       + (-ZWc[None] * C2 - wdc[None] * C1) * np.sin(wdc * DT)[None])
    bound_check = dict(min_exact_minus_sampled64_bar=round(float((Eb - es).min()) / 1e5, 5),
                       max_exact_minus_sampled64_bar=round(float((Eb - es).max()) / 1e5, 5))
    assert (Eb - es).min() > -1e-4 * 1e5 and (Eb - es).max() < 0.05 * 1e5, bound_check
    print('checks: static', static_check, bound_check, round(time.time() - t0w, 1), 's', flush=True)
    # ---- E at all modal periods (scaled) and on the dense grid
    Pd = list(FD.P_DENSE)
    Pm_all = [(m, s, 1e3 / (f_fe[m] * s)) for m in sorted(f_fe) for s in SCALES]
    Eall = e_bound(G, np.array([x[2] for x in Pm_all]) * 1e-3, ZETAS)          # (rows, nz, 180)
    print('E modal', round(time.time() - t0w, 1), 's', flush=True)
    jsplit = [j for j, T in enumerate(Pd) if T < 0.1]
    assert jsplit == list(range(len(jsplit)))
    Edense = np.concatenate([e_bound(G, np.array(Pd[:len(jsplit)]) * 1e-3, ZETAS),
                             e_bound(G, np.array(Pd[len(jsplit):]) * 1e-3, ZETAS)], axis=2)  # (rows, nz, 406)
    print('E dense', round(time.time() - t0w, 1), 's', flush=True)
    # ---- coherent known-mode sums: one column per (node, scale)
    Pk = [(m, s) for m in known_modes for s in SCALES]
    Wt = np.zeros((len(TC01) * len(SCALES), len(Pk)))
    combos = []
    for a_, nd in enumerate(TC01):
        for b_, s in enumerate(SCALES):
            k = a_ * len(SCALES) + b_; combos.append((nd['key'], s))
            for j, (m, s2) in enumerate(Pk):
                if s2 == s and m in share[nd['key']]['K']:
                    Wt[k, j] = share[nd['key']]['K'][m]
    TH, POST = th_known(G, np.array([1e3 / (f_fe[m] * s) for m, s in Pk]) * 1e-3, ZETAS, Wt, Wt.sum(axis=1))
    print('TH known', round(time.time() - t0w, 1), 's', flush=True)
    gpk = G.max(axis=1)
    # ---- envelopes and bounds
    bins_fe = {'1<T<=20ms': [m for m in f_fe if 1.0 < 1e3 / f_fe[m] <= 20.0], '0.1<T<=1ms': [m for m in f_fe if 0.1 < 1e3 / f_fe[m] <= 1.0]}
    res = {}
    for gname in GROUPS:
        R = RS[gname]
        Pg_peak = float(gpk[R].max()) / 1e5
        Em = Eall[R].max(axis=0) / 1e5                                          # (nz, 180) bar
        Ed = Edense[R].max(axis=0) / 1e5                                        # (nz, 406)
        THm = TH[R].max(axis=0) / 1e5; POSTm = POST[R].max(axis=0) / 1e5
        gres = dict(P_gauge_peak_bar=round(Pg_peak, 3), nodes={})
        for nd in TC01:
            sh = share[nd['key']]
            out_n = {}
            for iz, z in enumerate(ZETAS):
                for s in SCALES:
                    k = combos.index((nd['key'], s))
                    Ej = {m: Em[iz, Pm_all.index((m, s, 1e3 / (f_fe[m] * s)))] for m in f_fe}
                    sel_res = [j for j, T in enumerate(Pd) if T <= T_MIN / s + 1e-12]
                    jr = max(sel_res, key=lambda j: Ed[iz, j]); E_res = float(Ed[iz, jr])
                    U_hi = 0.0; U_lo = 0.0
                    for b, members in bins_fe.items():
                        kn = [m for m in members if m in sh['K']]; U = [m for m in members if m not in sh['K']]
                        A = sh['bins'][b]['abs_share'] - sum(abs(sh['K'][m]) for m in kn)
                        subs = []
                        if b == '0.1<T<=1ms':
                            for lab, (lo_, hi_) in (('11-19', (11, 19)), ('20-34', (20, 34)), ('35-60', (35, 60))):
                                subs.append((set(j for j, m in enumerate(U) if lo_ <= m <= hi_),
                                             sh['sub'][lab] - sum(sh['K'][m] for m in kn if lo_ <= m <= hi_)))
                        lo, hi = PM.abs_bounds([max(Ej[m], 1e-9) for m in U], sh['cap'], A, A, subs)
                        U_hi += hi; U_lo += lo
                    known_abs_E = sum(abs(c) * Ej[m] for m, c in sh['K'].items())
                    r = sh['r']
                    th_up = PA / 1e5 + float(THm[iz, k]) + U_hi + abs(r) * E_res
                    rule = PA / 1e5 + Pg_peak + known_abs_E + U_hi + abs(r) * E_res
                    out_n['zeta%g|s%.2f' % (z, s)] = dict(
                        known_coherent_bar_abs=round(PA / 1e5 + float(THm[iz, k]), 2),
                        known_post_record_sup_bar_abs=round(PA / 1e5 + float(POSTm[iz, k]), 2),
                        unpublished_bound_bar=[round(U_lo, 2), round(U_hi, 2)], E_res_bar=round(E_res, 3), E_res_at_ms=Pd[jr],
                        residual_term_bar=round(abs(r) * E_res, 2),
                        TH_upper_bar_abs=round(th_up, 2), E_rule_upper_bar_abs=round(rule, 2),
                        known_E={str(m): round(Ej[m], 3) for m in sorted(sh['K'])})
            gres['nodes'][nd['key']] = out_n
        gres['E_modal_bar'] = {'zeta%g' % z: {'%d|s%.2f' % (m, s): round(float(Em[iz, j]), 3) for j, (m, s, T) in enumerate(Pm_all)}
                               for iz, z in enumerate(ZETAS)}
        gres['E_dense_bar'] = {'zeta%g' % z: [round(float(x), 3) for x in Ed[iz]] for iz, z in enumerate(ZETAS)}
        res[gname] = gres
    # J-FWD margins (FEA3D FA1D yield / FA1U ultimate break-even, P x (1 + MS))
    cj = BJ['fa1_columns_at_JFWD']
    Pby, Pbu = cj['FA1D']['breakeven_bar_yield'], cj['FA1U']['breakeven_bar_ult']
    marg = {}
    for k, v in res[ALLG]['nodes']['TC-01_JFWD'].items():
        marg[k] = dict(TH=dict(MS_y=round(Pby / v['TH_upper_bar_abs'] - 1, 3), MS_u=round(Pbu / v['TH_upper_bar_abs'] - 1, 3)),
                       E_rule=dict(MS_y=round(Pby / v['E_rule_upper_bar_abs'] - 1, 3), MS_u=round(Pbu / v['E_rule_upper_bar_abs'] - 1, 3)),
                       known_coherent=dict(MS_y=round(Pby / v['known_coherent_bar_abs'] - 1, 3), MS_u=round(Pbu / v['known_coherent_bar_abs'] - 1, 3)))
    out = dict(
        version='v2.4b', date='2026-10-19', script='02-combustion/src/fa1_modal_th_bound_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
        smoke_test_subset=SMOKE, request='LEAD 2026-10-19 item 2 / CHANGELOG 228 (c): per-mode Peq at the TC-01 nodes',
        inputs=dict(npz=sha16(npz_f), spectra_json=sha16(spec_json), fea3d_modal_json=sha16(modal_json), fea3d_band_json=sha16(band_json),
                    code={f: sha16(os.path.join(HERE, f)) for f in EXPECT_SRC}),
        method=__doc__.split('Why: ')[1].split('Inputs:')[0].strip(),
        checks=dict(static_limit_rel_error=round(static_check, 6), e_bound_vs_sampled_64=bound_check, sampling=dict(points_per_step=M_SUB)),
        known_modes=known_modes, groups={BASE: 'baseline (168 cases)', ALLG: 'all cases (896)'}, periods_dense_ms=Pd,
        results=res, jfwd_breakeven=dict(yield_bar_abs=round(Pby, 2), ult_bar_abs=round(Pbu, 2)), jfwd_margins_all_case=marg,
        tags=dict(histories='SIM (v2.4a construct, ASSUMED inputs)', shares='SIM (FEA3D modal_v351ca2b_c71; read only)',
                  bounds='DERIVED', damping='ASSUMED (0.02 design, 0.05 sensitivity; 0 = bound)', status='not physical evidence'))
    json.dump(out, open(out_f, 'w'), indent=1)
    with open(out_csv, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['period_ms'] + ['E_head|%s|zeta%g' % (gl, z) for gl in ('baseline', 'all') for z in ZETAS])
        for j, T in enumerate(Pd):
            w.writerow([T] + [res[g]['E_dense_bar']['zeta%g' % z][j] for g in (BASE, ALLG) for z in ZETAS])
    print('wrote', out_f, sha16(out_f), out_csv, sha16(out_csv), round(time.time() - t0w, 1), 's')
    for k, v in res[ALLG]['nodes']['TC-01_JFWD'].items():
        print('JFWD', k, 'known', v['known_coherent_bar_abs'], 'U', v['unpublished_bound_bar'], 'res', v['residual_term_bar'],
              'TH_up', v['TH_upper_bar_abs'], 'E_rule', v['E_rule_upper_bar_abs'])
    for k, v in res[ALLG]['nodes']['TC-01_LC1'].items():
        print('LC1 ', k, 'known', v['known_coherent_bar_abs'], 'TH_up', v['TH_upper_bar_abs'], 'E_rule', v['E_rule_upper_bar_abs'])
    print('Pg_peak all', res[ALLG]['P_gauge_peak_bar'], 'base', res[BASE]['P_gauge_peak_bar'])


if __name__ == '__main__':
    main(*sys.argv[1:7])
