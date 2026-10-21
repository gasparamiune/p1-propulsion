"""REV-COMB-4 reviewer script: Pc-transducer face pressure in the Pc port passage during FA-1 (REV-COMB-4 item (f)(i): Electronics
fa1_chain_v2p11 head-face peaks 104.5 / 121.6 / 125.1 bar abs for CC-1 at c 222 / 400 m/s and CC-2 at c 222 m/s).

Model (DERIVED by the reviewer; linear LOSSLESS 1-D acoustics, ASSUMED): a uniform duct of the Electronics geometry (ID 2.044 mm;
CC-1 L 56.17 mm, CC-2 L 32 mm; front dead volume 6 mm3, 20 mm3 bound, taken as a length V / A at the closed end; open-end correction
0.6 r at the chamber), driven at the open end by the chamber head gauge pressure of each of the 896 FA-1 solver histories
(fa1_histories_solver_v2p4b.npz; from rest; held at the last value after the record; clipped and unclipped conventions, max of the
two), rigid closed end at the transducer face.  Exact closed-end response of the lossless duct: p_c(t) = 2 g(t - tau) - p_c(t - 2 tau),
tau = L_eff / c (image series), sampled at h <= 1 us (2 tau / h integer; the input is piecewise linear, so the sampled maximum is
low by at most slope x h, about 0.1 bar).  No friction, no heat transfer, no strong-wave effects: the lossless duct bounds a linear
model with friction (Electronics' laminar ladder) from above at the same L_eff and c, and is NOT bounded by the SDOF spectrum at its
quarter-wave period (a duct reflects a fast rise as a step: up to 2x the jump).
Compared with: the reviewer's undamped SDOF head spectrum (all cases) at the quarter-wave period 4 L_eff / c (r4_fa1_spectrum_cases.npz)
and FA1S 151.04 bar abs.
Tags: histories SIM (ASSUMED construct); geometry Electronics harness (Mechanical passage volume, ASSUMED dead volume); response DERIVED.
usage: python -I r4_pc_port_face.py NPZ CASES_NPZ OUT_JSON
"""
import hashlib, json, math, sys, time
import numpy as np

npz_f, cases_f, out_f = sys.argv[1:4]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(npz_f) == '399bf43d1c09de24'
PA = 101325.0; FA1S = 151.04
t0 = time.time()
Z = np.load(npz_f); C = np.load(cases_f)
keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
per = C['periods_ms'].astype(float); Senv = C['S_head'].astype(float).max(axis=0)
ID = 2.044e-3; A = math.pi * ID ** 2 / 4; ROPEN = 0.6 * ID / 2
GEOM = {'CC-1_v6': (56.17e-3, 6.0), 'CC-1_v20': (56.17e-3, 20.0), 'CC-2_v6': (32.0e-3, 6.0)}
CS = (150, 181, 202, 222, 250, 280, 320, 360, 400, 450, 500, 600, 700, 800, 900, 1000, 1049, 1100, 1136, 1200)
ELEC = {('CC-1_v6', 222): 104.49, ('CC-1_v6', 400): 121.59, ('CC-1_v20', 222): 108.872, ('CC-2_v6', 222): 125.139}
# histories: per-case (t, gauge) arrays
H = []
for i in range(len(keys)):
    a, b = int(off[i]), int(off[i + 1])
    t = Z['t_s'][a:b].astype(float); g = Z['P_head_bar'][a:b].astype(float) * 1e5 - PA
    H.append((t, g))
t_end = max(h[0][-1] for h in H)


def selftest():
    """ramp-to-step input through a duct with tau 0.1 ms: closed end must reach 2x for a rise <= 2 tau and 1 + (2 tau / tr) ... check
    the image series against a direct sum at a few points"""
    tau = 1e-4; m = 200; h = 2 * tau / m; n = 4000
    tt = np.arange(n) * h
    g = lambda x: np.clip(x / 0.15e-3, 0, 1) * (x > 0)
    pc = np.zeros(n)
    gs = g(tt - tau)
    for k in range(n):
        pc[k] = 2 * gs[k] - (pc[k - m] if k >= m else 0.0)
    direct = np.array([2 * sum((-1) ** j * g(x - (2 * j + 1) * tau) for j in range(int(x / (2 * tau)) + 2)) for x in tt[::97]])
    return float(np.max(np.abs(pc[::97] - direct))), float(pc.max())


st_err, st_max = selftest()
res = dict(script='r4_pc_port_face.py', script_sha16=H16(sys.argv[0]), npz=H16(npz_f), cases_npz=H16(cases_f),
           selftest=dict(max_abs_err_image_series=st_err, ramp_0p15ms_tau_0p1ms_peak_ratio=st_max), FA1S_bar_abs=FA1S, geometries={})
for gname, (L, V) in GEOM.items():
    Leff = L + V * 1e-9 / A + ROPEN
    rows = {}
    for c in CS:
        tau = Leff / c
        m = int(math.ceil(2 * tau / 1e-6)); h = 2 * tau / m
        T_run = t_end + 8 * tau
        n = int(math.ceil(T_run / h)) + 1
        tt = np.arange(n) * h
        best = np.full(len(H), -np.inf)
        for clip in (True, False):
            for j0 in range(0, len(H), 128):
                idx = range(j0, min(len(H), j0 + 128))
                Gs = np.zeros((len(idx), n))
                for r, i in enumerate(idx):
                    t, g = H[i]
                    gg = np.maximum(g, 0.0) if clip else g
                    x = tt - tau
                    v = np.interp(x, t, gg, left=0.0, right=gg[-1])
                    v[x < 0] = 0.0
                    Gs[r] = v
                pc = np.zeros_like(Gs)
                pc[:, :m] = 2 * Gs[:, :m]
                for k in range(m, n, m):
                    k1 = min(n, k + m)
                    pc[:, k:k1] = 2 * Gs[:, k:k1] - pc[:, k - m:k1 - m]
                mx = pc.max(axis=1)
                for r, i in enumerate(idx):
                    best[i] = max(best[i], mx[r])
        face = (PA + best) / 1e5
        T_qw_ms = 4 * tau * 1e3
        S_at = float(np.interp(T_qw_ms, per, Senv))
        im = int(np.argmax(face))
        rows[f'{c}'] = dict(L_eff_mm=round(Leff * 1e3, 3), tau_ms=round(tau * 1e3, 5), quarter_wave_period_ms=round(T_qw_ms, 4),
                            face_max_bar_abs=round(float(face.max()), 3), case=keys[im],
                            sdof_spectrum_at_period_bar_abs=round(S_at, 3),
                            face_over_sdof=round(float(face.max()) / S_at, 4),
                            n_cases_above={'102': int((face > 102).sum()), '121': int((face > 121).sum()),
                                           '137.9': int((face > 137.9).sum()), 'FA1S_151.04': int((face > FA1S).sum())},
                            electronics_face_peak_bar_abs=ELEC.get((gname, c)))
        print(gname, c, rows[f'{c}'], round(time.time() - t0, 1), 's', flush=True)
    res['geometries'][gname] = dict(L_mm=L * 1e3, V_end_mm3=V, rows=rows,
                                    max_over_c=max(r['face_max_bar_abs'] for r in rows.values()))
res['runtime_s'] = round(time.time() - t0, 1)
json.dump(res, open(out_f, 'w'), indent=1)
print('done', res['runtime_s'])
