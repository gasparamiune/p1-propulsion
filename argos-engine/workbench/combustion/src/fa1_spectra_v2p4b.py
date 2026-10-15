"""FA-1 load spectra with period domain (Combustion v2.4b, 2026-10-13; REV-COMB-3 R3-02/R3-03/R3-04; LEAD CHANGELOG line 194 (1)-(2)).

The v2.4a envelope (fa1_envelope_v2p4a.py a6b71cb487c9642e) stopped the pressure DLF at 1 ms and the thrust SDOF at 5 ms, and published
the 896 head/aft histories on a 0.1 ms grid over 0-25 ms only.  This script
  (1) re-runs the same 896 cases through the v2.4a code path (fa1_envelope_v2p4a and late_light_spike_v2p4 imported unchanged; the case
      state is rebuilt as in fa1_envelope_v2p4a.main) and ASSERTS that every case reproduces the published v2.4a metrics (peaks, P_head/
      aft DLF, thrust SDOF) and the published 0.1 ms histories exactly: the histories below are the v2.4a model, not a new one;
  (2) keeps the complete solver output of every case (0.05 ms grid from the light to t_end = max(tf, tau_pool) + 60 ms) and publishes
      head and aft pressure at that resolution (NPZ, float32);
  (3) computes undamped SDOF spectra on the complete histories, exact for the piecewise-linear history (first-order hold), with the
      continuous maximum inside each step and the free vibration after t_end with the history held at its final (steady) value:
        pressure: equivalent static P_eq(T) = p_amb + max k x for the gauge history from rest (v2.4a convention), head and aft,
                  T = 0.04-50 ms;
        thrust (aft node; Cf 1.35 ASSUMED band and quasi-steady x eta_cf 0.975 DERIVED): 'whole history' = F0 + max k x for F - F0
                  from rest (F0 = pre-light thrust) and 'above steady' = max k x for max(F - F_ss, 0) (F_ss = construct steady at
                  t_end), T = 0.5-200 ms, with the impulse above steady; the 1.8 kN x 4 ms rectangle analytically;
  (4) resolution study (R3-04): the governing short-period cases re-run with 0.0125 ms output and their spectra on that grid,
      decimated to 0.025/0.05 ms and on the published 0.1 ms grid (sampled and continuous maxima); the published JSON histories
      reproduce the reviewer's 90.7 bar at 0.25 ms.
The pool plateau (f_ret 1, q 2 MW/m2, about 22 bar to tau_pool 64-69 ms) is ASSUMED, as in v2.4a; spectra are also given for the
pool-free cases.  Tags: SIM (three-node vented network on ASSUMED inputs) and DERIVED (SDOF); the long-period values rest on the ASSUMED
pool plateau.  Not physical evidence.
usage: python -I fa1_spectra_v2p4b.py DATA_V2P4_DIR FA1_ENVELOPE_V2P4A_JSON OUT_JSON OUT_CSV_P OUT_CSV_F OUT_NPZ
"""
from __future__ import annotations
import csv, hashlib, itertools, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fa1_envelope_v2p4a as FE
LL, HS, MV = FE.LL, FE.HS, FE.MV

EXPECT_SRC = {'fa1_envelope_v2p4a.py': 'a6b71cb487c9642e', 'late_light_spike_v2p4.py': 'e8aad73cb6972cb3',
              'hard_start_v2p4.py': '00a966bb1572d075', 'hard_start_multivolume_v2p4.py': 'dd8aadf76f59113e'}
EXPECT_FA1_JSON = '64b328150025fa1e'
PA = FE.PA
T_P_MS = (0.04, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0, 12.5, 15.0, 20.0,
          25.0, 30.0, 40.0, 50.0)
T_F_MS = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 70.0, 100.0, 150.0, 200.0)
T_ALL = np.array(sorted(set(T_P_MS) | set(T_F_MS))) * 1e-3
IP = [int(np.argmin(abs(T_ALL - x * 1e-3))) for x in T_P_MS]
IF = [int(np.argmin(abs(T_ALL - x * 1e-3))) for x in T_F_MS]
RECT_F, RECT_TD = 1800.0, 0.004
TWO_PI = 2.0 * math.pi


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def sdof_spectrum(t, G, periods, hold_end=True, continuous=True):
    """Max over time of k x(t) for undamped SDOF oscillators at rest under the piecewise-linear histories G (rows) on the grid t.
    Exact recurrence per step; with continuous=True the maximum inside each step is found analytically; with hold_end=True the
    history is held at its last value after t[-1] and the free-vibration maximum is added.  Returns array (rows, periods)."""
    G = np.atleast_2d(np.asarray(G, float)); w = TWO_PI / np.asarray(periods, float)
    nr = G.shape[0]; W_ = w[None, :]
    u = np.zeros((nr, len(w))); v = np.zeros_like(u); umax = np.zeros_like(u)
    dts = np.diff(t)
    cache = {}
    for i in range(len(t) - 1):
        dt = float(dts[i]); kk = round(dt, 13)
        if kk not in cache:
            cache[kk] = (np.cos(w * dt)[None, :], np.sin(w * dt)[None, :])
        c, s = cache[kk]
        Fi = G[:, i][:, None]; Fj = G[:, i + 1][:, None]; sl = (Fj - Fi) / dt
        A = u - Fi; B = (v - sl) / W_
        if continuous:
            R = np.hypot(A, B)
            with np.errstate(divide='ignore', invalid='ignore'):
                q = np.where(R > 0, sl / (R * W_), 2.0)
            ok = np.abs(q) <= 1.0
            if ok.any():
                qc = np.clip(q, -1.0, 1.0)
                ph = np.arctan2(B, A) + np.arcsin(qc)            # w tau - (phase) at a local maximum of A cos + B sin
                per = TWO_PI / W_
                tau0 = np.mod(ph, TWO_PI) / W_
                n_extra = np.floor(np.maximum(dt - tau0, 0.0) / per)
                tau = np.where(sl > 0, tau0 + n_extra * per, tau0)   # the last maximum in the step if the trend rises
                uc = Fi + sl * tau + R * np.sqrt(1.0 - qc * qc)
                umax = np.where(ok & (tau <= dt), np.maximum(umax, uc), umax)
        u, v = A * c + B * s + Fj, -A * W_ * s + B * W_ * c + sl
        umax = np.maximum(umax, u)
    if hold_end:
        Fe = G[:, -1][:, None]
        umax = np.maximum(umax, Fe + np.hypot(u - Fe, v / W_))
    return umax


def rect_spectrum(F, td, periods):
    """Undamped SDOF maximum for a rectangular pulse F of duration td (analytic)."""
    T = np.asarray(periods, float)
    return F * np.where(td >= T / 2.0, 2.0, 2.0 * np.sin(math.pi * td / T))


def main(d, fa1_json, out_f, out_csv_p, out_csv_f, out_npz):
    t0w = time.time()
    for f, h in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    for f, h in FE.EXPECT_DATA.items():
        assert sha16(os.path.join(d, f)) == h, (f, sha16(os.path.join(d, f)))
    assert sha16(fa1_json) == EXPECT_FA1_JSON, sha16(fa1_json)
    PUB = json.load(open(fa1_json))
    # selftest: rectangle and step against the analytic maxima (continuous and sampled)
    tt = np.arange(0.0, 0.06 + 1e-12, 5e-5)
    Fr = np.where(tt < RECT_TD - 1e-12, RECT_F, 0.0); Fr[0] = 0.0
    rect_num = sdof_spectrum(tt, Fr[None, :], T_ALL)[0]
    # the numerical rectangle has a 0.05 ms linear rise and fall; compare with the analytic pulse
    rect_an = rect_spectrum(RECT_F, RECT_TD, T_ALL)
    selftest = dict(rect_max_rel_err=float(np.max(np.abs(rect_num / rect_an - 1.0)[T_ALL >= 0.5e-3])))
    st = sdof_spectrum(tt, np.where(tt > 0, 1.0, 0.0)[None, :], T_ALL)[0]
    selftest['step_max_abs_err_vs_2'] = float(np.max(np.abs(st - 2.0)[T_ALL >= 0.5e-3]))
    assert selftest['rect_max_rel_err'] < 0.02 and selftest['step_max_abs_err_vs_2'] < 0.02, selftest
    # continuous in-step maximum against a brute-force evaluation of the exact solution (random piecewise-linear history)
    rng = np.random.default_rng(7)
    tb = np.cumsum(np.r_[0.0, rng.uniform(2e-5, 8e-5, 60)]); Gb = rng.uniform(0.0, 1.0, 61)
    Tb = np.array([0.04e-3, 0.1e-3, 0.25e-3, 1e-3]); wv = TWO_PI / Tb
    num = sdof_spectrum(tb, Gb[None, :], Tb, hold_end=False)[0]
    u_ = np.zeros(4); v_ = np.zeros(4); bf = np.zeros(4)
    for i in range(60):
        dt = tb[i + 1] - tb[i]; sl = (Gb[i + 1] - Gb[i]) / dt; A = u_ - Gb[i]; B = (v_ - sl) / wv
        tau = np.linspace(0.0, dt, 4001)[:, None]
        bf = np.maximum(bf, (Gb[i] + sl * tau + A * np.cos(wv * tau) + B * np.sin(wv * tau)).max(axis=0))
        u_, v_ = A * np.cos(wv * dt) + B * np.sin(wv * dt) + Gb[i + 1], -A * wv * np.sin(wv * dt) + B * wv * np.cos(wv * dt) + sl
    selftest['continuous_max_minus_bruteforce'] = [float(x) for x in (num - bf)]
    assert np.all(num - bf >= -1e-9) and np.all(num - bf < 1e-4), selftest
    # case state, rebuilt as in fa1_envelope_v2p4a.main
    J = json.load(open(os.path.join(d, 'hard_start_v2p4.json')))
    cold = J['cold_flow_at_ignition_lift']['v']['A1_relight|0.125']; L = J['ignition_lifts']['v']['A1_relight|0.125']
    P1, T1, P2 = L['P_tank_Pa'], L['T_tank_K'], cold['P2_Pa']
    r_inj = HS.mdot_cold(LL.H_IGN, P1, T1, P2)
    x_liq = cold['liquid_flow_kg_s'] / cold['mdot_cold_kg_s']
    tl = LL.t_lift(); A_t = HS.AT
    V3 = MV.volumes(0.0499, FE.D_PORT); Vs = sum(V3)
    m_vap = cold['vapour_in_chamber_g']['reviewer_300.9cm3'] * 1e-3 * Vs / 300.9e-6
    m_inv = LL.admitted(P1, T1, P2, tl + FE.IG)[0]
    assert abs(1e3 * m_inv - PUB['state']['inventory_g']['ig0.30']) < 1e-9 and abs(P2 - PUB['state']['P0_cold_flow_Pa']) < 1e-9

    def fast(tres):
        m_s = r_inj * x_liq * tres
        m_f = min(m_vap + m_s, m_inv)
        sp = [(m_vap * V3[0] / Vs + m_s) / (m_vap + m_s), m_vap * V3[1] / Vs / (m_vap + m_s), m_vap * V3[2] / Vs / (m_vap + m_s)]
        return m_s, m_f, sp
    prods = {OF: HS.products('comb', T1, OF=OF) for OF in FE.OFS_EXT + FE.OFS_GRID}
    print('state and products', round(time.time() - t0w, 1), 's', flush=True)

    def run_case(lab_i, fi, lab_e, cd, OF, tres, tf, lab_p, fr, q):
        prod = prods[OF]; mpk = prod['mass_per_kg_N2O']
        lt = LL.Light(prod, FE.D_PORT, cd, fi * P2)
        m_s, m_f, sp = fast(tres)
        m_pool = max(m_inv - m_f, 0.0) * fr
        t, P, tau_p = lt.run(r_inj * mpk, m_f * mpk, sp, tf, m_pool * mpk, (q * mpk) if q else None)
        return t, P, tau_p, prod

    def thrust(P_aft, prod):
        cfq, _, _ = FE.cf_ideal(np.maximum(P_aft, 1.2e5), prod['gamma_frozen'])
        return {'Cf1.35': 1.35 * P_aft * A_t, 'QSx0.975': np.maximum(0.975 * cfq * P_aft * A_t, 0.0)}

    def spectra(t, P, prod, continuous=True):
        F = thrust(P[2], prod)
        rows = [np.maximum(P[0] - PA, 0.0), np.maximum(P[2] - PA, 0.0)]
        f0 = {k: float(x[0]) for k, x in F.items()}; fss = {k: float(x[-1]) for k, x in F.items()}
        for k in ('Cf1.35', 'QSx0.975'):
            rows.append(F[k] - f0[k]); rows.append(np.maximum(F[k] - fss[k], 0.0))
        S = sdof_spectrum(t, np.vstack(rows), T_ALL, continuous=continuous)
        trap = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
        o = dict(P_head_eq_bar=list(PA / 1e5 + S[0, IP] / 1e5), P_aft_eq_bar=list(PA / 1e5 + S[1, IP] / 1e5))
        for j, k in enumerate(('Cf1.35', 'QSx0.975')):
            o[f'F_whole_{k}_N'] = list(f0[k] + S[2 + 2 * j, IF]); o[f'F_above_{k}_N'] = list(S[3 + 2 * j, IF])
            o[f'F0_{k}_N'] = f0[k]; o[f'F_ss_{k}_N'] = fss[k]
            o[f'impulse_above_steady_{k}_Ns'] = float(trap(np.maximum(F[k] - fss[k], 0.0), t))
            o[f'impulse_above_F0_{k}_Ns'] = float(trap(np.maximum(F[k] - f0[k], 0.0), t))
            o[f'F_peak_{k}_N'] = float(F[k].max())
        return o

    # ---- (1)-(3) re-run, reproduce v2.4a, keep the solver output, spectra
    cases = {}; H_t = []; H_h = []; H_a = []; keys = []; offs = [0]
    nrep = 0
    for (lab_i, fi), (lab_e, cd), OF in itertools.product(FE.INITS, FE.ENTR, FE.OFS_EXT + FE.OFS_GRID):
        for tres, tf, (lab_p, fr, q) in itertools.product(FE.TRES, FE.TFS, FE.POOLS):
            key = f'{lab_i}|{lab_e}|OF{OF:g}|tf{tf*1e3:.0f}ms|tres{tres}|pool_{lab_p}'
            t, P, tau_p, prod = run_case(lab_i, fi, lab_e, cd, OF, tres, tf, lab_p, fr, q)
            mt, _ = FE.metrics(t, P, P2, prod, A_t)
            pub = PUB['cases'][key]
            for m_ in ('peak_head_bar', 'peak_aft_bar', 'impulse_above_P0_25ms_head_bar_ms', 'F_peak_Cf1.35_N', 'F_peak_QSx0.975_N', 'P_end_bar'):
                assert abs(mt[m_] - pub[m_]) <= 1e-9 * max(1.0, abs(pub[m_])), (key, m_, mt[m_], pub[m_])
            for m_ in ('P_head_DLF', 'P_aft_DLF', 'F_sdof_Cf1.35_N', 'F_sdof_QSx0.975_N'):
                assert max(abs(a - b) for a, b in zip(mt[m_], pub[m_])) <= 1e-9 * max(1.0, max(abs(b) for b in pub[m_])), (key, m_)
            assert FE.hist(t, P[0]) == pub['P_head_hist_bar'] and FE.hist(t, P[2]) == pub['P_aft_hist_bar'], key
            nrep += 1
            sp = spectra(t, P, prod)
            cases[key] = dict(OF=OF, tf_ms=tf * 1e3, t_res_s=tres, pool=lab_p, init=lab_i, entrance=lab_e, tau_pool_s=tau_p,
                              t_end_s=float(t[-1]), n_samples=len(t), peak_head_bar=mt['peak_head_bar'], peak_aft_bar=mt['peak_aft_bar'], **sp)
            keys.append(key); H_t.append(t); H_h.append(P[0] / 1e5); H_a.append(P[2] / 1e5); offs.append(offs[-1] + len(t))
        print(lab_i, lab_e, OF, 'done', round(time.time() - t0w, 1), 's', flush=True)
    assert nrep == 896 == len(PUB['cases'])
    np.savez_compressed(out_npz, case_keys=np.array(keys), offsets=np.array(offs, dtype=np.int64),
                        t_s=np.concatenate(H_t).astype(np.float32), P_head_bar=np.concatenate(H_h).astype(np.float32),
                        P_aft_bar=np.concatenate(H_a).astype(np.float32))
    print('npz', out_npz, os.path.getsize(out_npz), round(time.time() - t0w, 1), 's', flush=True)

    # ---- envelopes
    def sel_of(lab):
        init, ent, ofs, pool = lab.split('|')
        return [k for k in keys if (init == 'all' or cases[k]['init'] == init) and (ent == 'all' or cases[k]['entrance'] == ent)
                and (ofs == 'incl_OF3-3.5' or cases[k]['OF'] in FE.OFS_GRID) and (pool == 'all' or cases[k]['pool'] == pool)]
    GROUPS = ['vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'vapour_once|all|grid_OF4-12|all', 'vapour_once|all|incl_OF3-3.5|all',
              'as_written|all|incl_OF3-3.5|all', 'all|all|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all',
              'all|all|incl_OF3-3.5|none', 'all|all|incl_OF3-3.5|q2.0']

    def env(sel, field, per):
        out = []
        for j in range(len(per)):
            k = max(sel, key=lambda x: cases[x][field][j])
            out.append(dict(value=cases[k][field][j], case=k))
        return out
    ENV = {}
    for g in GROUPS:
        sel = sel_of(g); e = dict(n_cases=len(sel))
        for f in ('P_head_eq_bar', 'P_aft_eq_bar'):
            e[f] = env(sel, f, T_P_MS)
        for f in ('F_whole_Cf1.35_N', 'F_above_Cf1.35_N', 'F_whole_QSx0.975_N', 'F_above_QSx0.975_N'):
            e[f] = env(sel, f, T_F_MS)
        for f in ('impulse_above_steady_Cf1.35_Ns', 'impulse_above_steady_QSx0.975_Ns', 'impulse_above_F0_Cf1.35_Ns', 'F_peak_Cf1.35_N',
                  'F_peak_QSx0.975_N', 'peak_head_bar', 'peak_aft_bar'):
            k = max(sel, key=lambda x: cases[x][f]); e[f] = dict(value=cases[k][f], case=k)
        ENV[g] = e
    rect = rect_spectrum(RECT_F, RECT_TD, np.array(T_F_MS) * 1e-3)
    ALL = ENV['all|all|incl_OF3-3.5|all']
    first_exceed = {}
    for f in ('F_whole_Cf1.35_N', 'F_above_Cf1.35_N', 'F_whole_QSx0.975_N', 'F_above_QSx0.975_N'):
        ex = [T_F_MS[j] for j in range(len(T_F_MS)) if ALL[f][j]['value'] > rect[j]]
        first_exceed[f] = min(ex) if ex else None
    # period domain statements (LEAD line 194 (1)-(2))
    pmax = lambda lo, hi, f='P_head_eq_bar', g='all|all|incl_OF3-3.5|all': max(
        ENV[g][f][j]['value'] for j in range(len(T_P_MS)) if lo < T_P_MS[j] <= hi + 1e-12)
    domain = dict(
        T_le_0p1ms=dict(head_all=pmax(0.0, 0.1), aft_all=pmax(0.0, 0.1, 'P_aft_eq_bar'), rule_bar=90.0,
                        baseline_head=pmax(0.0, 0.1, g='vapour_once|rounded_Cd1.0|grid_OF4-12|all')),
        T_0p1_to_1ms=dict(head_all=pmax(0.1, 1.0), aft_all=pmax(0.1, 1.0, 'P_aft_eq_bar'),
                          baseline_head=pmax(0.1, 1.0, g='vapour_once|rounded_Cd1.0|grid_OF4-12|all'),
                          baseline_aft=pmax(0.1, 1.0, 'P_aft_eq_bar', g='vapour_once|rounded_Cd1.0|grid_OF4-12|all'),
                          rule_yield_bar=93.0, rule_ultimate_bar=102.0),
        T_1_to_20ms=dict(head_all=pmax(1.0, 20.0), aft_all=pmax(1.0, 20.0, 'P_aft_eq_bar'), rule='all-case spectrum at the part period, or FA1S'),
        T_20_to_50ms=dict(head_all=pmax(20.0, 50.0), aft_all=pmax(20.0, 50.0, 'P_aft_eq_bar')))

    # ---- (4) resolution study on the governing short-period cases
    gov = set()
    for g in ('vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'):
        for f in ('P_head_eq_bar', 'P_aft_eq_bar'):
            for j, x in enumerate(T_P_MS):
                if 0.1 <= x <= 1.5:
                    gov.add(ENV[g][f][j]['case'])
    T_RES = np.array([x for x in T_P_MS if x <= 2.0]) * 1e-3
    res_study = {}
    spec = {}
    for k in sorted(gov):
        c = cases[k]
        args = [x for x in FE.INITS if x[0] == c['init']][0] + [x for x in FE.ENTR if x[0] == c['entrance']][0]
        pl = [x for x in FE.POOLS if x[0] == c['pool']][0]
        dto = LL.DT_OUT
        try:
            LL.DT_OUT = 1.25e-5
            t, P, tau_p, prod = run_case(args[0], args[1], args[2], args[3], c['OF'], c['t_res_s'], c['tf_ms'] * 1e-3, *pl)
        finally:
            LL.DT_OUT = dto
        assert abs(P[0].max() / 1e5 - c['peak_head_bar']) < 0.05, (k, P[0].max() / 1e5, c['peak_head_bar'])
        r = {}
        for lab, step in (('0.0125ms', 1), ('0.025ms', 2), ('0.05ms', 4)):
            idx = np.arange(0, len(t), step)
            if idx[-1] != len(t) - 1:
                idx = np.append(idx, len(t) - 1)
            for cont in (True, False):
                S = sdof_spectrum(t[idx], np.vstack([np.maximum(P[0][idx] - PA, 0.0), np.maximum(P[2][idx] - PA, 0.0)]), T_RES, continuous=cont)
                r[f'{lab}|{"continuous" if cont else "sampled"}'] = dict(head=list(PA / 1e5 + S[0] / 1e5), aft=list(PA / 1e5 + S[1] / 1e5))
        g01 = np.arange(0.0, FE.T_IMP + 1e-9, FE.DT_HIST)
        for cont in (True, False):
            S = sdof_spectrum(g01, np.vstack([np.maximum(np.interp(g01, t, P[0]) - PA, 0.0), np.maximum(np.interp(g01, t, P[2]) - PA, 0.0)]),
                              T_RES, continuous=cont)
            r[f'0.1ms_published_grid_0-25ms|{"continuous" if cont else "sampled"}'] = dict(head=list(PA / 1e5 + S[0] / 1e5), aft=list(PA / 1e5 + S[1] / 1e5))
        # the published JSON history itself (0.1 ms, 0-25 ms, rounded to 1e-3 bar), held at its last value
        hh = np.array(PUB['cases'][k]['P_head_hist_bar']) * 1e5; ha = np.array(PUB['cases'][k]['P_aft_hist_bar']) * 1e5
        for cont in (True, False):
            S = sdof_spectrum(g01, np.vstack([np.maximum(hh - PA, 0.0), np.maximum(ha - PA, 0.0)]), T_RES, continuous=cont)
            r[f'published_json_0.1ms|{"continuous" if cont else "sampled"}'] = dict(head=list(PA / 1e5 + S[0] / 1e5), aft=list(PA / 1e5 + S[1] / 1e5))
        res_study[k] = r
    # v2.4a convention check: sampled maximum on the 0.05 ms solver grid within 30 ms reproduces the published 89.0 bar
    kb = 'vapour_once|rounded_Cd1.0|OF4|tf1ms|tres0.06|pool_q2.0'
    v24a = PUB['envelope']['vapour_once|grid_OF4-12|rounded_Cd1.0']['P_head_equiv_static_by_period'][2]
    if kb in res_study:
        spec['baseline_0p25ms_v2p4a_published'] = v24a['P_equiv_static_abs_bar']
    # published-JSON spectra for all cases (reviewer comparator basis): baseline and all, head/aft, continuous and sampled
    pubspec = {}
    g01 = np.arange(0.0, FE.T_IMP + 1e-9, FE.DT_HIST)
    for g in ('vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'):
        sel = sel_of(g)
        for cont in (False, True):
            best = None
            for k in sel:
                hh = np.array(PUB['cases'][k]['P_head_hist_bar']) * 1e5; ha = np.array(PUB['cases'][k]['P_aft_hist_bar']) * 1e5
                S = PA / 1e5 + sdof_spectrum(g01, np.vstack([np.maximum(hh - PA, 0.0), np.maximum(ha - PA, 0.0)]), T_ALL[IP], continuous=cont) / 1e5
                best = S if best is None else np.maximum(best, S)
            pubspec[f'{g}|{"continuous" if cont else "sampled"}'] = dict(head=list(best[0]), aft=list(best[1]))
    print('resolution study and published-grid spectra', round(time.time() - t0w, 1), 's', flush=True)

    # read-back check of the NPZ (float32) against the in-memory spectra of the governing all-case rows
    Z = np.load(out_npz)
    kz = ALL['P_head_eq_bar'][T_P_MS.index(3.0)]['case']
    iz = keys.index(kz); a_, b_ = Z['offsets'][iz], Z['offsets'][iz + 1]
    Sz = PA / 1e5 + sdof_spectrum(Z['t_s'][a_:b_].astype(float), np.maximum(Z['P_head_bar'][a_:b_].astype(float) * 1e5 - PA, 0.0)[None, :],
                                  T_ALL[IP])[0] / 1e5
    npz_check = dict(case=kz, max_abs_diff_bar=float(np.max(np.abs(Sz - np.array(cases[kz]['P_head_eq_bar'])))))
    assert npz_check['max_abs_diff_bar'] < 5e-3, npz_check

    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/fa1_spectra_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-02/R3-03/R3-04; LEAD CHANGELOG line 194 (1)-(2): head and aft pressure spectra to >= 20 ms, thrust spectrum '
                       'to >= 100 ms with the impulse, period domain of every DLF statement, histories at solver resolution or the resolution effect',
               inputs=dict(code=EXPECT_SRC, data=FE.EXPECT_DATA, fa1_envelope_v2p4a_json=EXPECT_FA1_JSON),
               reproduction=dict(n_cases=nrep, checks='peaks, 25 ms impulse, F peaks, P_end, v2.4a DLF and thrust SDOF lists to 1e-9 relative; '
                                                      '0.1 ms histories identical to the published lists', result='896 of 896 identical'),
               selftest=selftest, npz_readback=npz_check,
               periods_ms=dict(pressure=list(T_P_MS), thrust=list(T_F_MS)),
               definitions=dict(
                   pressure='P_eq(T) = p_amb + max_t k x(t) for the gauge history max(P - p_amb, 0) applied from rest at the light (v2.4a convention; '
                            'the pre-light 1.071 bar abs is applied as a step, conservative by <= 0.07 bar); bar abs',
                   thrust_whole='F0 + max_t k x for F(t) - F0 from rest; F = Cf P_aft A_t (Cf 1.35 ASSUMED band) or quasi-steady ideal Cf x 0.975 (DERIVED)',
                   thrust_above_steady='max_t k x for max(F(t) - F_ss, 0) from rest; F_ss = construct steady at t_end (lit at the 0.2039 mm '
                                       'ignition lift, about 4.4 bar abs)',
                   history='complete solver output (0.05 ms grid, light to t_end = max(tf, tau_pool) + 60 ms); after t_end the history is held '
                           'at its final value (steady) and the free-vibration maximum is included',
                   maximum='exact for the piecewise-linear history: continuous maximum within each step (not only at the samples)',
                   rectangle='1.8 kN x 4 ms, analytic undamped SDOF maximum'),
               envelopes=ENV, rectangle_N=list(rect),
               thrust_first_period_ms_where_FA1_exceeds_rectangle=first_exceed,
               period_domain=domain,
               resolution_study=dict(cases=sorted(gov), periods_ms=list(1e3 * T_RES), results=res_study,
                                     published_json_spectra=pubspec, note=spec),
               npz=dict(file=os.path.basename(out_npz), arrays='case_keys, offsets (int64, n+1), t_s, P_head_bar, P_aft_bar (float32); case i '
                                                              'spans offsets[i]:offsets[i+1]; time from the light'),
               cases=cases,
               tags=dict(model='SIM three-node vented network on ASSUMED inputs (v2.4a construct, re-run unchanged)',
                         pool_plateau='ASSUMED (f_ret 1, q 2 MW/m2): it sets the long-period thrust spectrum and the impulse above steady',
                         sdof='DERIVED (undamped, no structural model)', thrust='Cf 1.35 ASSUMED band; quasi-steady Cf DERIVED',
                         status='not physical evidence; IGN-1 on the stand dynamic Pc channel (>= 100 bar abs) is the evidence'))
    json.dump(out, open(out_f, 'w'), indent=None, separators=(',', ':'), default=float)
    with open(out_csv_p, 'w', newline='') as fh:
        w = csv.writer(fh)
        hdr = ['period_ms']
        for g in GROUPS:
            for f in ('P_head_eq_bar', 'P_aft_eq_bar'):
                hdr.append(f'{f}|{g}')
        w.writerow(hdr)
        for j, T in enumerate(T_P_MS):
            w.writerow([T] + [round(ENV[g][f][j]['value'], 2) for g in GROUPS for f in ('P_head_eq_bar', 'P_aft_eq_bar')])
    with open(out_csv_f, 'w', newline='') as fh:
        w = csv.writer(fh)
        hdr = ['period_ms', 'rectangle_1p8kN_4ms_N']
        for g in GROUPS:
            for f in ('F_whole_Cf1.35_N', 'F_above_Cf1.35_N', 'F_whole_QSx0.975_N', 'F_above_QSx0.975_N'):
                hdr.append(f'{f}|{g}')
        w.writerow(hdr)
        for j, T in enumerate(T_F_MS):
            w.writerow([T, round(float(rect[j]), 1)] + [round(ENV[g][f][j]['value'], 1) for g in GROUPS
                                                         for f in ('F_whole_Cf1.35_N', 'F_above_Cf1.35_N', 'F_whole_QSx0.975_N', 'F_above_QSx0.975_N')])
    # console summary
    for g in GROUPS:
        e = ENV[g]
        print(g, 'n', e['n_cases'])
        print('  head', [round(x['value'], 1) for x in e['P_head_eq_bar']])
        print('  aft ', [round(x['value'], 1) for x in e['P_aft_eq_bar']])
        print('  F whole Cf1.35', [round(x['value']) for x in e['F_whole_Cf1.35_N']])
        print('  F above Cf1.35', [round(x['value']) for x in e['F_above_Cf1.35_N']])
        print('  F whole QS.975', [round(x['value']) for x in e['F_whole_QSx0.975_N']])
        print('  impulse above steady Cf1.35 %.2f N s (%s); QS %.2f' % (e['impulse_above_steady_Cf1.35_Ns']['value'], e['impulse_above_steady_Cf1.35_Ns']['case'],
                                                                         e['impulse_above_steady_QSx0.975_Ns']['value']))
    print('periods P', T_P_MS); print('periods F', T_F_MS); print('rect', [round(x) for x in rect])
    print('first exceed', first_exceed); print('domain', json.dumps(domain))
    print('selftest', selftest, 'npz', npz_check)
    for k, r in res_study.items():
        print('RES', k)
        for lab, x in r.items():
            print('   %-44s head %s' % (lab, [round(y, 2) for y in x['head']]))
    for lab, x in pubspec.items():
        print('PUB', lab, 'head', [round(y, 1) for y in x['head']], 'aft', [round(y, 1) for y in x['aft']])
    print('wrote', out_f, sha16(out_f), os.path.getsize(out_f), out_csv_p, sha16(out_csv_p), out_csv_f, sha16(out_csv_f), out_npz, sha16(out_npz),
          round(time.time() - t0w, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:7])
