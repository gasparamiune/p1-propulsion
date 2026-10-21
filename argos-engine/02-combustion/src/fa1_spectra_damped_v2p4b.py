"""Damped FA-1 equivalent-static-pressure spectra for publication (Combustion v2.4b final, 2026-10-19; LEAD CHANGELOG lines 194 (1),
223 (3), 228 (c); lead request 2026-10-19 item 1).

What it computes (no grid re-run; the 896 solver histories of fa1_histories_solver_v2p4b.npz, 399bf43d1c09de24, float32 at 0.05 ms):
  (1) head and aft equivalent static pressure S(T) = p_amb + max_t k x(t) of SDOF oscillators at rest (static gain 1) under the
      gauge pressure histories, at zeta 0 / 0.02 / 0.05, on the dense period grid of fa1_spectra_dense_v2p4b.py (0.02-50 ms, 406
      periods) and at the 60 FE mode periods of FEA3D's modal run modal_v351ca2b_c71 (hub 04-fea/assembly3d) divided by the
      frequency factors 1.00 / 0.90 / 0.85 (T = T_FE / s);
  (2) envelopes over the baseline group (vapour_once | rounded Cd 1.0 | O/F 4-12 grid | both pool forms: 168 cases) and over all
      896 cases, in the published convention env = max(b, c) (b: gauge history clipped at 0; c: unclipped; they differ only in the
      vapour_once cases), with the governing case per period;
  (3) band maxima per period domain (T <= 0.1, 0.1-1, 1-20, 20-50 ms) and below 0.195 ms / 0.195/s ms (the FE residual band);
  (4) checks: the zeta-0 sampled spectrum against the exact continuous zeta-0 maximum (fa1_spectra_v2p4b.sdof_spectrum) on every
      dense period (envelope level) and at the modal periods (per case), i.e. the sampling error of the damped figures.
Method for zeta > 0: exact damped recurrence for the piecewise-linear history; inside each 0.05 ms step the closed-form response
is evaluated at m equally spaced points (m = 2^k with step/m <= T/64 for T >= 0.1 ms and <= T/16 below, m <= 64); after the record
the history is held and the first damped peak of the free decay is added analytically.  zeta 0 published values are the exact
continuous maxima (dense: fa1_spectra_dense_v2p4b.json envelopes; modal periods: computed here with sdof_spectrum).
Tags: histories SIM (v2.4a three-node vented construct, ASSUMED inputs, pool plateau ASSUMED); spectra DERIVED (SDOF, no
structural model); damping values ASSUMED.  Not physical evidence.
usage: python -I fa1_spectra_damped_v2p4b.py NPZ SPECTRA_JSON DENSE_JSON FEA3D_MODAL_JSON OUT_JSON OUT_CSV_DENSE OUT_CSV_MODAL
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fa1_spectra_v2p4b as FS          # noqa: E402
import fa1_spectra_dense_v2p4b as FD    # noqa: E402

EXPECT = {'npz': '399bf43d1c09de24', 'spectra_json': '372b8078d7a90e75', 'dense_json': '7468996959538d0f',
          'fea3d_modal_json': None}
EXPECT_SRC = {'fa1_spectra_v2p4b.py': 'bb510e33dec78405', 'fa1_spectra_dense_v2p4b.py': '910fdbf52a41918f'}
PA = FS.PA
DT = 5.0e-5
ZETAS = (0.0, 0.02, 0.05)
SCALES = (1.00, 0.90, 0.85)
BASE, ALLG = 'vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'
GROUPS = (BASE, ALLG)
BANDS = (('T_le_0p1ms', 0.0, 0.1), ('T_0p1_to_1ms', 0.1, 1.0), ('T_1_to_20ms', 1.0, 20.0), ('T_20_to_50ms', 20.0, 50.0))
SMOKE = int(os.environ.get('FA1_DAMPED_SMOKE', '0'))     # > 0: every SMOKE-th case only (code test; never published)
TWO_PI = 2.0 * math.pi


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def m_of(T):
    K = 64.0 if T >= 1e-4 else 16.0
    need = max(1.0, K * DT / T)
    return int(min(64, 2 ** math.ceil(math.log2(need) - 1e-12)))


def damped_sampled(G, periods, zetas):
    """G: (rows, nt) gauge histories on the uniform DT grid (padded with the last value).  Returns umax (rows, nz, np)."""
    nr, nt = G.shape
    periods = np.asarray(periods, float)
    out = np.zeros((nr, len(zetas), len(periods)))
    ms = np.array([m_of(T) for T in periods])
    Z = np.asarray(zetas, float)[:, None]
    for m in sorted(set(ms.tolist())):
        idx = np.nonzero(ms == m)[0]
        w = TWO_PI / periods[idx]
        W = np.broadcast_to(w[None, :], (len(zetas), len(w))).copy()
        wd = W * np.sqrt(1.0 - Z * Z)
        tau = DT * np.arange(1, m + 1) / m                                   # sample points inside the step (last = DT)
        E = np.exp(-(Z * W)[:, :, None] * tau[None, None, :])               # (nz, ng, m)
        Ec = E * np.cos(wd[:, :, None] * tau); Es = E * np.sin(wd[:, :, None] * tau)
        e1, c1, s1 = E[:, :, -1], np.cos(wd * DT), np.sin(wd * DT)
        ZW = Z * W
        u = np.zeros((nr, len(zetas), len(idx))); v = np.zeros_like(u); umax = np.zeros_like(u)
        for i in range(nt - 1):
            Fi = G[:, i][:, None, None]; sl = ((G[:, i + 1] - G[:, i]) / DT)[:, None, None]
            a = Fi - 2.0 * Z[None] * sl / W[None]
            C1 = u - a; C2 = (v - sl + ZW[None] * C1) / wd[None]
            us = a[..., None] + sl[..., None] * tau + C1[..., None] * Ec[None] + C2[..., None] * Es[None]
            umax = np.maximum(umax, us.max(axis=-1))
            u = us[..., -1]
            v = sl + e1[None] * ((-ZW[None] * C1 + wd[None] * C2) * c1[None] + (-ZW[None] * C2 - wd[None] * C1) * s1[None])
        # free decay after the record, history held at its last value: first damped peak (analytic)
        Fe = G[:, -1][:, None, None]
        C1 = u - Fe; C2 = (v + ZW[None] * C1) / wd[None]
        R = np.hypot(C1, C2); th = np.arctan2(C2, C1)
        ps = np.arcsin(Z)[None]
        ts = np.mod(th - ps, TWO_PI) / wd[None]
        peak = Fe + R * np.sqrt(1.0 - Z[None] ** 2) * np.exp(-ZW[None] * ts)
        umax = np.maximum(umax, peak)
        out[:, :, idx] = umax
        print('  group m=%d periods=%d done' % (m, len(idx)), flush=True)
    return out


def main(npz_f, spec_json, dense_json, modal_json, out_f, out_csv_d, out_csv_m):
    t0w = time.time()
    for lab, f in (('npz', npz_f), ('spectra_json', spec_json), ('dense_json', dense_json)):
        assert sha16(f) == EXPECT[lab], (lab, sha16(f))
    for f, h in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    SJ = json.load(open(spec_json)); DJ = json.load(open(dense_json)); MJ = json.load(open(modal_json))
    assert DJ['script_sha256_16'] == EXPECT_SRC['fa1_spectra_dense_v2p4b.py']
    assert MJ['run'] == 'modal_v351ca2b_c71' and MJ['n_modes'] == 60
    Pd = list(FD.P_DENSE); assert Pd == DJ['periods_ms']['pressure'] and len(Pd) == 406
    modes = [(int(r['mode']), float(r['f_Hz'])) for r in MJ['modes']]
    Pm = sorted(set(round(1e3 / (f * s), 6) for _, f in modes for s in SCALES))
    Pall = sorted(set(Pd) | set(Pm))
    Z = np.load(npz_f)
    keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
    assert len(keys) == 896 and keys == list(SJ['cases'].keys())
    sel_cases = [i for i in range(896) if not (SMOKE and i % SMOKE)]
    meta = {k: SJ['cases'][k] for k in keys}
    lens = np.diff(off); nt = int(lens.max())
    rows, row_case, row_node, row_conv = [], [], [], []
    tmax_err = 0.0
    stored = []                                                     # (t_stored, rows) per case for the exact zeta-0 check
    for i in sel_cases:
        a, b = int(off[i]), int(off[i + 1])
        t = Z['t_s'][a:b].astype(float)
        tmax_err = max(tmax_err, float(np.max(np.abs(t - DT * np.arange(b - a)))))
        ph = Z['P_head_bar'][a:b].astype(float) * 1e5; pa = Z['P_aft_bar'][a:b].astype(float) * 1e5
        unclipped = bool(min(ph.min(), pa.min()) < PA)
        cand = [('head', 'b', np.maximum(ph - PA, 0.0)), ('aft', 'b', np.maximum(pa - PA, 0.0))]
        if unclipped:
            cand += [('head', 'c', ph - PA), ('aft', 'c', pa - PA)]
        for n, cv, g in cand:
            gp = np.empty(nt); gp[:len(g)] = g; gp[len(g):] = g[-1]
            rows.append(gp); row_case.append(i); row_node.append(n); row_conv.append(cv)
        stored.append((t, np.vstack([g for _, _, g in cand])))
    # the stored float32 time vectors drift from k x 0.05 ms by up to ~1.9e-5 s at the record end (accumulated float32 rounding,
    # <= 0.015 % of the record); the sampled recurrence uses the uniform grid, the exact zeta-0 check uses the stored grid
    assert tmax_err < 2.5e-5, tmax_err
    G = np.vstack(rows)
    print('rows', G.shape, 'cases', len(sel_cases), round(time.time() - t0w, 1), 's', flush=True)
    U = damped_sampled(G, np.array(Pall) * 1e-3, ZETAS)             # (rows, nz, np), gauge Pa
    print('sampled done', round(time.time() - t0w, 1), 's', flush=True)
    # exact continuous zeta 0 at the modal periods (per case) and per-case comparison
    im = [Pall.index(x) for x in Pm]
    U0m = np.zeros((G.shape[0], len(Pm)))
    r0 = 0
    for t_c, g_c in stored:
        U0m[r0:r0 + g_c.shape[0]] = FS.sdof_spectrum(t_c, g_c, np.array(Pm) * 1e-3)
        r0 += g_c.shape[0]
    assert r0 == G.shape[0]
    err_modal = float(np.max(U0m - U[:, 0, im])) / 1e5
    neg_modal = float(np.min(U0m - U[:, 0, im])) / 1e5
    print('exact zeta0 at modal periods done', round(time.time() - t0w, 1), 's; sampled shortfall max %.4f bar, min %.4f bar'
          % (err_modal, neg_modal), flush=True)
    # per (case, node): env convention = max over b, c rows
    nodes = ('head', 'aft')
    caseval = {}                                                    # (i, node) -> (nz, np) abs bar
    caseval0m = {}
    for r in range(G.shape[0]):
        k = (row_case[r], row_node[r])
        val = (PA + U[r]) / 1e5; val0 = (PA + U0m[r]) / 1e5
        caseval[k] = val if k not in caseval else np.maximum(caseval[k], val)
        caseval0m[k] = val0 if k not in caseval0m else np.maximum(caseval0m[k], val0)

    def sel_of(lab):
        init, ent, ofs, pool = lab.split('|')
        return [i for i in sel_cases if (init == 'all' or meta[keys[i]]['init'] == init) and (ent == 'all' or meta[keys[i]]['entrance'] == ent)
                and (ofs == 'incl_OF3-3.5' or meta[keys[i]]['OF'] in FD.FE.OFS_GRID) and (pool == 'all' or meta[keys[i]]['pool'] == pool)]
    ENV = {}
    for gname in GROUPS:
        sel = sel_of(gname)
        e = dict(n_cases=len(sel))
        for n in nodes:
            A = np.stack([caseval[(i, n)] for i in sel])              # (ns, nz, np)
            j = np.argmax(A, axis=0)
            vals = np.take_along_axis(A, j[None], axis=0)[0]
            A0m = np.stack([caseval0m[(i, n)] for i in sel])          # (ns, nmodal)
            j0m = np.argmax(A0m, axis=0)
            for iz, z in enumerate(ZETAS):
                v = vals[iz].copy(); gov = [keys[sel[x]] for x in j[iz]]
                lab = 'zeta%g' % z
                if z == 0.0:
                    # publish the exact continuous maxima: dense grid from fa1_spectra_dense, modal periods computed here
                    dens = DJ['envelopes'][gname]['P_%s_eq_bar|env' % n]
                    sampled = v.copy()
                    for jj, T in enumerate(Pall):
                        if T in Pm:
                            mi = Pm.index(T); v[jj] = A0m[j0m[mi], mi]; gov[jj] = keys[sel[j0m[mi]]]
                        else:
                            di = Pd.index(T); v[jj] = dens['value'][di]; gov[jj] = dens['case'][di]
                    if not SMOKE:
                        dd = [(v[jj] - sampled[jj], T) for jj, T in enumerate(Pall)]
                        e['P_%s|zeta0_exact_minus_sampled_bar' % n] = dict(max=round(max(dd)[0], 4), at_ms=max(dd)[1],
                                                                          min=round(min(dd)[0], 4), at_ms_min=min(dd)[1])
                e['P_%s|%s' % (n, lab)] = dict(value=[round(float(x), 3) for x in v], case=gov)
        ENV[gname] = e
    print('envelopes', round(time.time() - t0w, 1), 's', flush=True)

    def band_max(gname, n, z, lo, hi):
        v = ENV[gname]['P_%s|zeta%g' % (n, z)]['value']; cs = ENV[gname]['P_%s|zeta%g' % (n, z)]['case']
        idx = [j for j, T in enumerate(Pall) if lo < T <= hi + 1e-12 and T in Pd]
        j = max(idx, key=lambda x: v[x])
        return dict(value_bar=v[j], period_ms=Pall[j], case=cs[j])
    domains = {}
    for bl, lo, hi in BANDS + tuple(('T_le_%gms_residual_s%.2f' % (round(0.194914 / s, 4), s), 0.0, 0.194914 / s) for s in SCALES):
        domains[bl] = {'%s|%s|zeta%g' % (n, g_, z): band_max(gn, n, z, lo, hi) for n in nodes for g_, gn in (('baseline', BASE), ('all', ALLG))
                       for z in ZETAS}
    modal_rows = []
    for mode, f in modes:
        for s in SCALES:
            T = round(1e3 / (f * s), 6); j = Pall.index(T)
            r = dict(mode=mode, f_FE_Hz=f, scale=s, T_ms=T)
            for n in nodes:
                for g_, gn in (('baseline', BASE), ('all', ALLG)):
                    for z in ZETAS:
                        r['%s|%s|zeta%g' % (n, g_, z)] = ENV[gn]['P_%s|zeta%g' % (n, z)]['value'][j]
            modal_rows.append(r)
    out = dict(
        version='v2.4b', date='2026-10-19', script='02-combustion/src/fa1_spectra_damped_v2p4b.py',
        script_sha256_16=sha16(os.path.abspath(__file__)), smoke_test_subset=SMOKE,
        request=('LEAD 2026-10-19 item 1: head and aft equivalent-static-pressure spectra S(T), dense, T 0.02-50 ms, zeta 0 / 0.02 / 0.05, '
                 'baseline and all-case, as data; item 2 / line 228 (c): S at the FE mode periods with the frequency factors x0.85 / 0.90 / 1.00'),
        inputs=dict(npz=sha16(npz_f), spectra_json=sha16(spec_json), dense_json=sha16(dense_json),
                    fea3d_modal_json='04-fea/assembly3d/results/modal_modal_v351ca2b_c71.json %s' % sha16(modal_json),
                    code={f: sha16(os.path.join(HERE, f)) for f in EXPECT_SRC}),
        conventions=dict(S='equivalent static pressure, bar abs = p_amb + max over time of the SDOF response (static gain 1, from rest)',
                         env='published = max(b, c): b gauge clipped at 0 (v2.4a), c unclipped (reviewer r3); differ only in vapour_once',
                         zeta0='exact continuous maximum (dense grid: fa1_spectra_dense_v2p4b.json; modal periods: computed here)',
                         zeta_gt_0='closed-form damped response sampled at m points per 0.05 ms step (step/m <= T/64 for T >= 0.1 ms, <= T/16 below, '
                                   'm <= 64); first free-decay peak added analytically after the record',
                         modal_period='T = 1 / (s f_FE), s = FE frequency factor (true f = s x f_FE); f_FE from modal_v351ca2b_c71 (60 modes)',
                         groups={BASE: 'baseline (168 cases)', ALLG: 'all cases (896)'}),
        periods_ms=dict(all=Pall, dense=Pd, modal=Pm),
        checks=dict(time_grid_max_dev_s=tmax_err, time_grid_note='stored float32 time vectors drift from k x 0.05 ms by <= %.2e s (accumulated '
                    'rounding); damped figures use the uniform grid; the zeta-0 checks compare with the exact maximum on the stored grid' % tmax_err,
                    zeta0_modal_exact_minus_sampled_bar=dict(max=round(err_modal, 4), min=round(neg_modal, 4),
                                                             note='per case and node at the 180 modal periods; positive = sampling shortfall')),
        envelopes=ENV, band_maxima=domains, modal_periods=modal_rows,
        thrust_spectrum=dict(file='fa1_thrust_spectra_dense_v2p4b.csv', sha256_16=None, periods_ms=[0.5, 200.0], zeta=0.0,
                             note='thrust spectra to 200 ms (Cf 1.35 and QS x 0.975, whole and above steady) as published by '
                                  'fa1_spectra_dense_v2p4b.py; not recomputed here'),
        tags=dict(histories='SIM v2.4a construct (three-node vented network, ASSUMED inputs; pool plateau ASSUMED)',
                  spectra='DERIVED (SDOF; no structural model)', damping='ASSUMED values (0.02, 0.05); 0 is the bound',
                  modal='SIM (FEA3D modal_v351ca2b_c71, coarsened all-L2, unstressed, rigid airframe; read only)',
                  status='not physical evidence'))
    json.dump(out, open(out_f, 'w'), indent=1)
    hdr = ['period_ms'] + ['%s|%s|zeta%g' % (n, g_, z) for n in nodes for g_ in ('baseline', 'all') for z in ZETAS]
    with open(out_csv_d, 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(hdr)
        for j, T in enumerate(Pall):
            if T not in Pd:
                continue
            w.writerow([T] + [ENV[BASE if g_ == 'baseline' else ALLG]['P_%s|zeta%g' % (n, z)]['value'][j]
                              for n in nodes for g_ in ('baseline', 'all') for z in ZETAS])
    with open(out_csv_m, 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['mode', 'f_FE_Hz', 'scale', 'T_ms'] + hdr[1:])
        for r in modal_rows:
            w.writerow([r['mode'], r['f_FE_Hz'], r['scale'], r['T_ms']] + [r[h] for h in hdr[1:]])
    print('wrote', out_f, sha16(out_f), out_csv_d, sha16(out_csv_d), out_csv_m, sha16(out_csv_m), round(time.time() - t0w, 1), 's')
    for bl in ('T_le_0p1ms', 'T_0p1_to_1ms', 'T_1_to_20ms'):
        print(bl, {k: (v['value_bar'], v['period_ms']) for k, v in domains[bl].items() if k.startswith('head|all') or k.startswith('head|baseline')})


if __name__ == '__main__':
    main(*sys.argv[1:8])
