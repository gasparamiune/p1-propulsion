"""Dense-period FA-1 spectra from the stored solver histories (Combustion v2.4b, 2026-10-13; REV-COMB-3 R3-02/R3-03/R3-04;
LEAD CHANGELOG line 194 (1)-(2)).

fa1_spectra_v2p4b.py (372b8078d7a90e75 output) sampled the undamped spectra at 28 pressure periods.  Between those periods the
undamped spectrum has narrow lobes (0.3 / 0.4 / 0.6 / 0.75 ms), so the band maxima need a dense period grid.  No grid re-run: this
script reads the complete solver histories of the 896 cases from fa1_histories_solver_v2p4b.npz (399bf43d1c09de24; float32, 0.05 ms)
and computes, with the same exact first-order-hold recurrence and continuous in-step maximum (fa1_spectra_v2p4b.sdof_spectrum):
  (1) head and aft equivalent static pressure at 0.02-1 ms every 0.005 ms, 1-5 ms every 0.025 ms and 5-50 ms (41 log points plus the
      coarse periods), in two gauge conventions:
        (b) v2.4a/v2.4b: gauge history max(P - p_amb, 0) from rest;
        (c) reviewer (r3_fa1_check.py): gauge history P - p_amb, not clipped, from rest.  They differ only in the 'vapour_once' cases,
            whose construct history starts at 0.054 bar abs (5 % initial-gas numerical floor); (c) then carries a free oscillation of
            up to +-0.96 bar.  The published value is the envelope max((b), (c)); (b) is kept for continuity;
  (2) thrust spectra (Cf 1.35 and quasi-steady ideal Cf x 0.975; whole history and above steady) at 0.5-200 ms (100 log points plus
      the coarse periods and 20-30 ms every 0.25 ms) against the 1.8 kN x 4 ms rectangle;
  (3) band maxima with governing cases for T <= 0.1 ms, 0.1 < T <= 1 ms, 1 < T <= 20 ms, 20 < T <= 50 ms and for the modal bands of
      mechanical.json v2.1 fa1.periods_and_dlf (TC-02 / closure screws 0.272-0.385 ms head; TC-09 0.33-0.467 ms aft; TC-01
      0.053-0.075 ms both nodes; TC-04 0.044-0.062 ms head);
  (4) damping sensitivity (zeta 0 / 0.02 / 0.05; exact damped recurrence for the piecewise-linear history, maximum sampled on 20 sub-steps
      per 0.05 ms step) on the governing cases of (3) at 0.05-5 ms;
  (5) an independent check of the recurrence: scipy solve_ivp (DOP853) on two governing cases at 0.4 and 0.75 ms;
  (6) the ringing content of the governing head histories (detrended periodogram, 0-30 ms), to show where the lobes come from;
  (7) consistency: the dense values at the 28/19 coarse periods equal the fa1_spectra_v2p4b.json per-case values (float32 storage);
      the reviewer's 90.7 bar (baseline, 0.25 ms, published 0.1 ms grid) is reproduced with convention (c).
The pool plateau (about 22 bar to tau_pool 64-69 ms) is ASSUMED as in v2.4a.  Tags: SIM histories (three-node vented network on ASSUMED
inputs) and DERIVED spectra (undamped unless stated; no structural model).  Not physical evidence.
usage: python -I fa1_spectra_dense_v2p4b.py DATA_V2P4_DIR FA1_ENVELOPE_V2P4A_JSON FA1_SPECTRA_V2P4B_JSON HISTORIES_NPZ MECHANICAL_JSON
       OUT_JSON OUT_CSV_P OUT_CSV_F
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fa1_spectra_v2p4b as FS
FE, HS = FS.FE, FS.HS

EXPECT_DATA = {'npz': '399bf43d1c09de24', 'spectra_json': '372b8078d7a90e75', 'fa1_v2p4a_json': '64b328150025fa1e',
               'mechanical_json': 'e4d3e7c9df529171'}
PA = FS.PA
P_DENSE = sorted(set([round(x, 4) for x in np.arange(0.02, 1.0 + 1e-9, 0.005)] + [round(x, 4) for x in np.arange(1.025, 5.0 + 1e-9, 0.025)]
                     + [round(x, 4) for x in np.geomspace(5.0, 50.0, 41)] + list(FS.T_P_MS)))
F_DENSE = sorted(set([round(x, 4) for x in np.geomspace(0.5, 200.0, 100)] + [round(x, 4) for x in np.arange(20.0, 30.0 + 1e-9, 0.25)]
                     + list(FS.T_F_MS)))
BANDS = (('T_le_0p1ms', 0.0, 0.1), ('T_0p1_to_1ms', 0.1, 1.0), ('T_1_to_20ms', 1.0, 20.0), ('T_20_to_50ms', 20.0, 50.0))
ZETAS = (0.0, 0.02, 0.05)
M_SUB = 20
TWO_PI = 2.0 * math.pi
SMOKE = int(os.environ.get('FA1_DENSE_SMOKE', '0'))      # > 0: every SMOKE-th case only (code test; never published)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def damped_sampled(t, G, periods, zetas, m=M_SUB, hold_cycles=3.0):
    """Max over time of k x for damped SDOF oscillators at rest under the piecewise-linear histories G (rows), each row with every zeta.
    Exact recurrence for linear forcing on m sub-steps per step; maximum sampled at the sub-steps; after t[-1] the history is held for
    hold_cycles x the longest period.  Returns array (rows, zetas, periods)."""
    G = np.atleast_2d(np.asarray(G, float)); w = TWO_PI / np.asarray(periods, float)
    Z = np.asarray(zetas, float)[:, None]
    W = np.broadcast_to(w[None, :], (len(zetas), len(w)))
    wd = W * np.sqrt(1.0 - Z * Z)
    nr = G.shape[0]
    u = np.zeros((nr, len(zetas), len(w))); v = np.zeros_like(u); umax = np.zeros_like(u)

    def adv(u, v, Fi, sl, h):
        E = np.exp(-Z * W * h); cd = np.cos(wd * h); sd = np.sin(wd * h)
        a = Fi - 2.0 * Z * sl / W
        C1 = u - a; C2 = (v - sl + Z * W * C1) / wd
        un = a + sl * h + E * (C1 * cd + C2 * sd)
        vn = sl + E * ((-Z * W * C1 + wd * C2) * cd + (-Z * W * C2 - wd * C1) * sd)
        return un, vn
    for i in range(len(t) - 1):
        dt = float(t[i + 1] - t[i]); h = dt / m
        Fi = G[:, i][:, None, None]; sl = ((G[:, i + 1] - G[:, i]) / dt)[:, None, None]
        for j in range(m):
            u, v = adv(u, v, Fi + sl * (j * h), sl, h)
            umax = np.maximum(umax, u)
    Fe = G[:, -1][:, None, None]; zero = np.zeros_like(Fe)
    Tmax = float(np.max(periods)); h = min(float(np.min(periods)) / 40.0, 5e-6)
    n_hold = int(math.ceil(hold_cycles * Tmax / h))
    for j in range(n_hold):
        u, v = adv(u, v, Fe, zero, h)
        umax = np.maximum(umax, u)
    return umax


def main(d, fa1_json, spec_json, npz_f, mech_f, out_f, out_csv_p, out_csv_f):
    t0w = time.time()
    for lab, f in (('npz', npz_f), ('spectra_json', spec_json), ('fa1_v2p4a_json', fa1_json), ('mechanical_json', mech_f)):
        assert sha16(f) == EXPECT_DATA[lab], (lab, sha16(f))
    SJ = json.load(open(spec_json))
    assert SJ['script_sha256_16'] == sha16(os.path.join(HERE, 'fa1_spectra_v2p4b.py')), 'fa1_spectra_v2p4b.py differs from the published run'
    for f, h in FS.EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    PUB = json.load(open(fa1_json))
    A_t = PUB['state']['A_t_m2']
    assert abs(A_t - HS.AT) < 1e-15, (A_t, HS.AT)
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    T1 = J['ignition_lifts']['v']['A1_relight|0.125']['T_tank_K']
    prods = {OF: HS.products('comb', T1, OF=OF) for OF in FE.OFS_EXT + FE.OFS_GRID}
    MJ = json.load(open(mech_f))
    modal = MJ['fa1']['periods_and_dlf']['rows']
    Z = np.load(npz_f)
    keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
    assert len(keys) == 896 and keys == list(SJ['cases'].keys())
    TP = np.array(P_DENSE) * 1e-3; TF = np.array(F_DENSE) * 1e-3
    ip_coarse = [P_DENSE.index(x) for x in FS.T_P_MS]; if_coarse = [F_DENSE.index(x) for x in FS.T_F_MS]
    nP, nF = len(TP), len(TF)
    Pb = {n: np.zeros((896, nP)) for n in ('head', 'aft')}; Pc = {n: np.zeros((896, nP)) for n in ('head', 'aft')}
    FK = ('F_whole_Cf1.35_N', 'F_above_Cf1.35_N', 'F_whole_QSx0.975_N', 'F_above_QSx0.975_N')
    FD = {k: np.zeros((896, nF)) for k in FK}
    meta = {}
    worst_coarse = dict(P=0.0, F=0.0)
    for i, k in enumerate(keys):
        c = SJ['cases'][k]
        meta[k] = dict(init=c['init'], entrance=c['entrance'], OF=c['OF'], pool=c['pool'])
        if SMOKE and i % SMOKE:
            continue
        a, b = int(off[i]), int(off[i + 1])
        t = Z['t_s'][a:b].astype(float); ph = Z['P_head_bar'][a:b].astype(float) * 1e5; pa = Z['P_aft_bar'][a:b].astype(float) * 1e5
        rows = [np.maximum(ph - PA, 0.0), np.maximum(pa - PA, 0.0)]
        unclipped = bool(min(ph.min(), pa.min()) < PA)
        if unclipped:
            rows += [ph - PA, pa - PA]
        S = FS.sdof_spectrum(t, np.vstack(rows), TP)
        Pb['head'][i] = (PA + S[0]) / 1e5; Pb['aft'][i] = (PA + S[1]) / 1e5
        Pc['head'][i] = (PA + S[2]) / 1e5 if unclipped else Pb['head'][i]
        Pc['aft'][i] = (PA + S[3]) / 1e5 if unclipped else Pb['aft'][i]
        g = prods[c['OF']]['gamma_frozen']
        cfq, _, _ = FE.cf_ideal(np.maximum(pa, 1.2e5), g)
        F = {'Cf1.35': 1.35 * pa * A_t, 'QSx0.975': np.maximum(0.975 * cfq * pa * A_t, 0.0)}
        fr = []
        for kk in ('Cf1.35', 'QSx0.975'):
            fr.append(F[kk] - F[kk][0]); fr.append(np.maximum(F[kk] - F[kk][-1], 0.0))
        SF = FS.sdof_spectrum(t, np.vstack(fr), TF)
        FD['F_whole_Cf1.35_N'][i] = F['Cf1.35'][0] + SF[0]; FD['F_above_Cf1.35_N'][i] = SF[1]
        FD['F_whole_QSx0.975_N'][i] = F['QSx0.975'][0] + SF[2]; FD['F_above_QSx0.975_N'][i] = SF[3]
        # consistency with the published per-case coarse spectra (float32 storage of the histories)
        worst_coarse['P'] = max(worst_coarse['P'], float(np.max(np.abs(Pb['head'][i][ip_coarse] - np.array(c['P_head_eq_bar'])))),
                                float(np.max(np.abs(Pb['aft'][i][ip_coarse] - np.array(c['P_aft_eq_bar'])))))
        for kk in FK:
            worst_coarse['F'] = max(worst_coarse['F'], float(np.max(np.abs(FD[kk][i][if_coarse] - np.array(c[kk])))))
        if i % 56 == 55:
            print(i + 1, 'cases', round(time.time() - t0w, 1), 's', 'coarse diff', worst_coarse, flush=True)
    assert worst_coarse['P'] < 5e-3 and worst_coarse['F'] < 0.5, worst_coarse
    Penv = {n: np.maximum(Pb[n], Pc[n]) for n in ('head', 'aft')}

    def sel_of(lab):
        init, ent, ofs, pool = lab.split('|')
        return [i for i, k in enumerate(keys) if (init == 'all' or meta[k]['init'] == init) and (ent == 'all' or meta[k]['entrance'] == ent)
                and (ofs == 'incl_OF3-3.5' or meta[k]['OF'] in FE.OFS_GRID) and (pool == 'all' or meta[k]['pool'] == pool)]
    GROUPS = ['vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'vapour_once|all|incl_OF3-3.5|all', 'as_written|all|incl_OF3-3.5|all',
              'all|all|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all', 'all|all|incl_OF3-3.5|none']
    BASE, ALLG = GROUPS[0], 'all|all|incl_OF3-3.5|all'

    def env(arr, sel):
        sub = arr[sel]; j = np.argmax(sub, axis=0)
        return sub[j, np.arange(sub.shape[1])], [keys[sel[x]] for x in j]
    ENV = {}
    for gname in GROUPS:
        sel = sel_of(gname); e = dict(n_cases=len(sel))
        for n in ('head', 'aft'):
            for lab, arr in (('env', Penv[n]), ('b', Pb[n]), ('c', Pc[n])):
                vals, cs = env(arr, sel)
                e[f'P_{n}_eq_bar|{lab}'] = dict(value=[round(float(x), 3) for x in vals], case=cs if lab == 'env' else None)
        for kk in FK:
            vals, cs = env(FD[kk], sel)
            e[kk] = dict(value=[round(float(x), 1) for x in vals], case=cs)
        ENV[gname] = e

    def band_max(gname, n, lo, hi, lab='env'):
        v = np.array(ENV[gname][f'P_{n}_eq_bar|{lab}']['value']); idx = [j for j, T in enumerate(P_DENSE) if lo < T <= hi + 1e-12]
        j = max(idx, key=lambda x: v[x])
        cs = ENV[gname][f'P_{n}_eq_bar|env']['case']
        return dict(value_bar=float(v[j]), period_ms=P_DENSE[j], case=cs[j] if cs else None)
    domain = {}
    for bl, lo, hi in BANDS:
        domain[bl] = {f'{n}|{g_}': band_max(gn, n, lo, hi) for n in ('head', 'aft') for g_, gn in (('baseline', BASE), ('all', ALLG))}
        domain[bl].update({f'{n}|{g_}|convention_b_only': band_max(gn, n, lo, hi, 'b')['value_bar'] for n in ('head', 'aft')
                           for g_, gn in (('baseline', BASE), ('all', ALLG))})
    domain['T_le_0p1ms']['rule_LEAD_194_1'] = '90 bar abs quasi-static'
    domain['T_0p1_to_1ms']['rule_LEAD_194_1'] = 'yield 93 bar abs, ultimate 102 bar abs'
    domain['T_1_to_20ms']['rule_LEAD_194_1'] = 'all-case spectrum at the part period, or FA1S (DLF 2.0, about 151 bar abs)'
    # modal bands of mechanical.json v2.1
    node_of = {'ENG-TC-02': ('head',), 'ENG-TC-09': ('aft',), 'ENG-TC-01': ('head', 'aft'), 'ENG-TC-04': ('head',)}
    parts = []
    for r in modal:
        lo, hi = r['T_ms_band']; nodes = node_of.get(r['dominant_part'], ('head', 'aft'))
        o = dict(item=r['item'], dominant_part=r['dominant_part'], f_model_Hz=r['f_model_Hz'], T_ms_band=[lo, hi], nodes=list(nodes),
                 mechanical_load_cases=r.get('load_cases'))
        for g_, gn in (('baseline', BASE), ('all', ALLG)):
            best = None
            for n in nodes:
                bm = band_max(gn, n, lo - 1e-9, hi)
                if best is None or bm['value_bar'] > best['value_bar']:
                    best = dict(bm, node=n)
            o[f'max_in_band_{g_}'] = best
        o['note'] = ('the band maximum on the dense grid (0.005 ms steps below 1 ms; nearest grid points inside the band); the 0.272 ms '
                     'and 0.33 ms band edges are inside the 0.005 ms grid to +-0.0025 ms')
        parts.append(o)
    rect = FS.rect_spectrum(FS.RECT_F, FS.RECT_TD, TF)
    first_exceed = {}
    for kk in FK:
        v = np.array(ENV[ALLG][kk]['value']); ex = [F_DENSE[j] for j in range(nF) if v[j] > rect[j]]
        first_exceed[kk] = min(ex) if ex else None
    rect_bounds_le_20ms = {kk: bool(all(ENV[ALLG][kk]['value'][j] <= rect[j] for j in range(nF) if F_DENSE[j] <= 20.0 + 1e-9)) for kk in FK}
    margin_le_20 = {kk: float(min(rect[j] / ENV[ALLG][kk]['value'][j] for j in range(nF) if F_DENSE[j] <= 20.0 + 1e-9)) for kk in FK}
    print('envelopes', round(time.time() - t0w, 1), 's', flush=True)

    # (4) damping sensitivity on the governing cases
    gov = {}
    for bl, lo, hi in BANDS[:3]:
        for kk_, v in domain[bl].items():
            if isinstance(v, dict) and v.get('case'):
                gov.setdefault(v['case'], set()).add(kk_.split('|')[0])
    for p in parts:
        for g_ in ('baseline', 'all'):
            gov.setdefault(p[f'max_in_band_{g_}']['case'], set()).add(p[f'max_in_band_{g_}']['node'])
    TD = np.array([x for x in P_DENSE if 0.05 - 1e-9 <= x <= 5.0 + 1e-9]) * 1e-3
    damp = {}
    for k in sorted(gov):
        i = keys.index(k); a, b = int(off[i]), int(off[i + 1])
        t = Z['t_s'][a:b].astype(float); ph = Z['P_head_bar'][a:b].astype(float) * 1e5; pa = Z['P_aft_bar'][a:b].astype(float) * 1e5
        D = damped_sampled(t, np.vstack([np.maximum(ph - PA, 0.0), np.maximum(pa - PA, 0.0)]), TD, ZETAS)
        r = dict(nodes_governed=sorted(gov[k]))
        for jn, n in enumerate(('head', 'aft')):
            for jz, z in enumerate(ZETAS):
                r[f'{n}|zeta{z:g}'] = [round(float(x), 3) for x in (PA + D[jn, jz]) / 1e5]
            # zeta 0 sampled on 20 sub-steps against the exact continuous maximum: sampling error of the damped figures
            jj = [P_DENSE.index(round(1e3 * x, 4)) for x in TD]
            r[f'{n}|zeta0_minus_continuous_max_bar'] = float(np.max(np.abs((PA + D[jn, 0]) / 1e5 - Pb[n][i][jj])))
        damp[k] = r
        print('damped', k, round(time.time() - t0w, 1), 's', flush=True)
    damp_summary = {}
    for bl, lo, hi in (('T_0p1_to_1ms', 0.1, 1.0), ('T_1_to_5ms', 1.0, 5.0)):
        for n in ('head', 'aft'):
            for z in ZETAS:
                vals = [max(v for T_, v in zip(TD * 1e3, damp[k][f'{n}|zeta{z:g}']) if lo < T_ <= hi + 1e-12) for k in damp]
                damp_summary[f'{bl}|{n}|zeta{z:g}|max_over_governing_cases_bar'] = round(max(vals), 2)
    for p in parts:
        lo, hi = p['T_ms_band']
        for z in ZETAS:
            vals = []
            for k in damp:
                for n in p['nodes']:
                    vals.append(max(v for T_, v in zip(TD * 1e3, damp[k][f'{n}|zeta{z:g}']) if lo - 1e-9 <= T_ <= hi + 1e-12))
            p[f'max_in_band_governing_cases_zeta{z:g}_bar'] = round(max(vals), 2)

    # (5) independent check with solve_ivp
    from scipy.integrate import solve_ivp
    ode = []
    for gname in (BASE, ALLG):
        for T_ms in (0.4, 0.75):
            j = P_DENSE.index(T_ms); k = ENV[gname]['P_head_eq_bar|env']['case'][j]; i = keys.index(k)
            a, b = int(off[i]), int(off[i + 1])
            t = Z['t_s'][a:b].astype(float); gh = np.maximum(Z['P_head_bar'][a:b].astype(float) * 1e5 - PA, 0.0) / 1e5
            w = TWO_PI / (T_ms * 1e-3)
            t_stop = t[-1] + 3 * T_ms * 1e-3
            fun = lambda tt, y: [y[1], w * w * (np.interp(tt, t, gh) - y[0])]
            sol = solve_ivp(fun, (0.0, t_stop), [0.0, 0.0], method='DOP853', rtol=1e-10, atol=1e-10, max_step=T_ms * 1e-3 / 40.0, dense_output=True)
            te = np.arange(0.0, t_stop, T_ms * 1e-3 / 400.0)
            m_ode = float(PA / 1e5 + sol.sol(te)[0].max())
            ode.append(dict(group=gname, case=k, period_ms=T_ms, recurrence_bar=float(Pb['head'][i][j]), solve_ivp_bar=m_ode,
                            diff_bar=m_ode - float(Pb['head'][i][j]), nfev=int(sol.nfev)))
            print('ode', ode[-1], flush=True)
    assert all(abs(o['diff_bar']) < 0.02 for o in ode), ode

    # (6) ringing content of the governing head histories (0-30 ms)
    from scipy.signal import savgol_filter
    ring = {}
    for k in sorted({ENV[ALLG]['P_head_eq_bar|env']['case'][P_DENSE.index(x)] for x in (0.3, 0.4, 0.6, 0.75)}
                    | {ENV[BASE]['P_head_eq_bar|env']['case'][P_DENSE.index(x)] for x in (0.3, 0.4, 0.75)}):
        i = keys.index(k); a, b = int(off[i]), int(off[i + 1])
        t = Z['t_s'][a:b].astype(float); ph = Z['P_head_bar'][a:b].astype(float); pa = Z['P_aft_bar'][a:b].astype(float)
        tg = np.arange(0.0, min(0.030, t[-1]), 5e-5)
        o = {}
        for n, x in (('head', ph), ('aft', pa)):
            y = np.interp(tg, t, x); y = y - savgol_filter(y, 61, 2)
            nfft = 1 << 16
            S = np.abs(np.fft.rfft(y * np.hanning(len(y)), nfft)); f = np.fft.rfftfreq(nfft, 5e-5)
            msk = (f >= 300.0) & (f <= 9000.0)
            fi, Si = f[msk], S[msk]
            pk = [j for j in range(1, len(Si) - 1) if Si[j] >= Si[j - 1] and Si[j] >= Si[j + 1]]
            pk = sorted(pk, key=lambda j: -Si[j])[:4]
            o[n] = [dict(f_Hz=round(float(fi[j]), 1), T_ms=round(1e3 / float(fi[j]), 4), rel_amplitude=round(float(Si[j] / Si[pk[0]]), 3)) for j in pk]
        ring[k] = o

    # (7) the reviewer's 90.7 bar: published 0.1 ms history, convention (c)
    kb = 'vapour_once|rounded_Cd1.0|OF4|tf1ms|tres0.06|pool_q2.0'
    g01 = np.array(PUB['history_grid_ms']) * 1e-3
    hh = np.array(PUB['cases'][kb]['P_head_hist_bar']) * 1e5
    rv = {}
    for lab, G in (('b_clipped', np.maximum(hh - PA, 0.0)), ('c_unclipped', hh - PA)):
        rv[lab] = float(PA / 1e5 + FS.sdof_spectrum(g01, G[None, :], np.array([0.25e-3]))[0, 0] / 1e5)
    i = keys.index(kb); j = P_DENSE.index(0.25)
    decomposition = dict(case=kb, period_ms=0.25,
                         v2p4a_published_sampled_0p05ms_30ms_window_b=SJ['resolution_study']['note'].get('baseline_0p25ms_v2p4a_published'),
                         continuous_0p05ms_solver_b=float(Pb['head'][i][j]), continuous_0p05ms_solver_c=float(Pc['head'][i][j]),
                         continuous_published_0p1ms_b=rv['b_clipped'], continuous_published_0p1ms_c_reviewer=rv['c_unclipped'],
                         continuous_0p0125ms_solver_b=SJ['resolution_study']['results'][kb]['0.0125ms|continuous']['head'][4],
                         reviewer_r3_fa1_check=90.66)
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/fa1_spectra_dense_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               smoke_test_subset=SMOKE,
               request='REV-COMB-3 R3-02/R3-03/R3-04; LEAD CHANGELOG line 194 (1)-(2): band maxima on a dense period grid, period domain of each '
                       'DLF statement, convention and resolution effects',
               inputs=dict(npz=sha16(npz_f), fa1_spectra_v2p4b_json=sha16(spec_json), fa1_envelope_v2p4a_json=sha16(fa1_json),
                           mechanical_json_v2p1=sha16(mech_f), spectra_code=SJ['script_sha256_16']),
               periods_ms=dict(pressure=P_DENSE, thrust=F_DENSE),
               conventions=dict(b='gauge history max(P - p_amb, 0) from rest (v2.4a)', c='gauge history P - p_amb from rest (reviewer r3_fa1_check.py)',
                                env='published value = max(b, c); b and c differ only in the vapour_once cases (construct start 0.054 bar abs), '
                                    'by up to +-0.96 bar'),
               consistency=dict(max_abs_diff_vs_coarse_P_bar=worst_coarse['P'], max_abs_diff_vs_coarse_F_N=worst_coarse['F'],
                                note='dense values at the coarse periods against fa1_spectra_v2p4b.json per-case values (float32 histories)'),
               decomposition_90p7_vs_89p0=decomposition,
               envelopes=ENV, period_domain=domain, mechanical_modal_bands=parts,
               thrust=dict(rectangle_N=[round(float(x), 1) for x in rect], first_period_ms_FA1_exceeds_rectangle=first_exceed,
                           rectangle_bounds_FA1_for_T_le_20ms=rect_bounds_le_20ms, min_rectangle_over_FA1_T_le_20ms=margin_le_20),
               damping=dict(zetas=list(ZETAS), sub_steps=M_SUB, periods_ms=[round(1e3 * x, 4) for x in TD], cases=damp, summary=damp_summary,
                            note='exact damped recurrence for the piecewise-linear history; maximum sampled on 20 sub-steps per 0.05 ms step; '
                                 'zeta0_minus_continuous_max_bar is the sampling error of these figures'),
               ode_check=ode, ringing=ring,
               tags=dict(histories='SIM v2.4a construct (three-node vented network, ASSUMED inputs; pool plateau ASSUMED)',
                         spectra='DERIVED (SDOF; undamped unless stated; no structural model)', status='not physical evidence'))
    json.dump(out, open(out_f, 'w'), indent=None, separators=(',', ':'), default=float)
    with open(out_csv_p, 'w', newline='') as fh:
        w = csv.writer(fh)
        hdr = ['period_ms']
        for gname in GROUPS:
            for n in ('head', 'aft'):
                hdr += [f'P_{n}_eq_bar_env|{gname}', f'P_{n}_eq_bar_b|{gname}']
        w.writerow(hdr)
        for j, T in enumerate(P_DENSE):
            row = [T]
            for gname in GROUPS:
                for n in ('head', 'aft'):
                    row += [ENV[gname][f'P_{n}_eq_bar|env']['value'][j], ENV[gname][f'P_{n}_eq_bar|b']['value'][j]]
            w.writerow(row)
    with open(out_csv_f, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['period_ms', 'rectangle_1p8kN_4ms_N'] + [f'{kk}|{gname}' for gname in GROUPS for kk in FK])
        for j, T in enumerate(F_DENSE):
            w.writerow([T, round(float(rect[j]), 1)] + [ENV[gname][kk]['value'][j] for gname in GROUPS for kk in FK])
    print(json.dumps(dict(domain=domain, first_exceed=first_exceed, rect_bounds_le_20ms=rect_bounds_le_20ms, margin_le_20=margin_le_20,
                          damp_summary=damp_summary, decomposition=decomposition, consistency=worst_coarse), indent=1, default=float))
    for p in parts:
        print('PART', p['dominant_part'], p['T_ms_band'], p['nodes'], 'baseline', p['max_in_band_baseline'], 'all', p['max_in_band_all'],
              {z: p[f'max_in_band_governing_cases_zeta{z:g}_bar'] for z in ZETAS})
    for k, o in ring.items():
        print('RING', k, json.dumps(o))
    print('wrote', out_f, sha16(out_f), os.path.getsize(out_f), out_csv_p, sha16(out_csv_p), out_csv_f, sha16(out_csv_f),
          round(time.time() - t0w, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:9])
