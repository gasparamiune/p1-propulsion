"""REV-COMB-4 reviewer script: torch-passage pressure during FA-1 (P_torch question of CHANGELOG 245 (5), Mechanical tap wall row).

Model (DERIVED by the reviewer; linear lossless 1-D acoustics, ASSUMED): the TC-02 torch passage of CAD v3.5.2 parts_engine.py as a
two-segment duct, open into the chamber head at the injector face and closed at the torch seat (the torch throat d 2 mm is 15 % of
the 5.2 mm passage area and is treated as a rigid end: the torch chamber compliance is not modelled):
  segment 1: 3.0 mm outlet, 30 deg inward/aft, face exit to the knee, L1 = 8 / cos 30 deg = 9.238 mm (+ open-end correction 0.6 r);
  segment 2: 5.2 mm passage, knee (r 21.5, z 111.513) to the torch seat (r 25, z 160.013), L2 = 48.626 mm;
  J-FWD tap station (Mechanical tapwall v1: passage z 127.357): 15.886 mm along segment 2 from the knee.
Drive: the chamber head gauge pressure of each of the 896 FA-1 solver histories (fa1_histories_solver_v2p4b.npz), held at the last
value after the record (as the spectra), both the clipped and unclipped conventions.
Numerics: digital waveguide (exact for a lossless duct when the segment delays are whole steps; step dx = c dt = 0.5 mm, segment lengths
rounded to whole steps, the rounding stated), scattering junction from pressure and volume-flow continuity, rigid reflection at the
closed end, imposed pressure at the open end.  Self-tests: (1) uniform duct against the analytic image series
p_closed = 2 sum (-1)^n g(t - (2n+1) L / c); (2) fundamental period against tan(k L1) tan(k L2) = A1 / A2.
Sound speed bracket: the passage gas at the FA-1 peak is chamber-head gas pushed in by the 30-70x compression (the initial torch gas is
squeezed into the last few mm); c from 150 m/s (below the 181 m/s near-critical N2O vapour bound of REPORT 15.8) to 1200 m/s (above the
1049-1136 m/s products); every c reported.  Strong-wave (shock) effects, wall heat transfer and friction are NOT modelled.
Tags: histories SIM (ASSUMED construct); geometry DESIGN (CAD v3.5.2); duct response DERIVED (linear model ASSUMED).  Not physical evidence.
usage: python -I r4_torch_passage.py NPZ OUT_JSON
"""
import hashlib, json, math, sys, time
import numpy as np

npz_f, out_f = sys.argv[1:3]
H16 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert H16(npz_f) == '399bf43d1c09de24', H16(npz_f)
PA = 101325.0
t0w = time.time()

D1, D2 = 3.0e-3, 5.2e-3
A1, A2 = math.pi * D1 ** 2 / 4, math.pi * D2 ** 2 / 4
L1_geom = 8.0e-3 / math.cos(math.radians(30.0))
L2 = math.hypot(25.0 - 21.5, 160.013 - 111.513) * 1e-3
END_CORR = 0.6 * D1 / 2
X_TAP_IN_SEG2 = (127.357 - 111.513) / (160.013 - 111.513) * L2


def waveguide(Gfun, nc, nsteps, N1, N2, Y1, Y2, st1, st2, chunk=4000):
    """Run the two-segment duct; Gfun(n0, n1) -> (n1 - n0, nc) open-end gauge pressure.  st1 / st2: station sample indices from the open
    end (segment 1) and from the junction (segment 2).  Returns the per-case maximum over time and its step at the junction, the closed
    end and every station."""
    M1, M2 = N1 + 1, N2 + 1
    a1 = np.zeros((M1, nc)); b1 = np.zeros((M1, nc)); a2 = np.zeros((M2, nc)); b2 = np.zeros((M2, nc))
    names = ['junction', 'closed'] + [f'seg1_{s}' for s in st1] + [f'seg2_{s}' for s in st2]
    s1 = np.array(st1, dtype=int); s2 = np.array(st2, dtype=int)
    PK = np.full((len(names), nc), -1e30); TPK = np.zeros((len(names), nc))
    V = np.zeros((len(names), nc))
    cJ1 = 2 * Y1 / (Y1 + Y2); cJ2 = 2 * Y2 / (Y1 + Y2)
    n1s, n2s = len(st1), len(st2)
    for n0 in range(0, nsteps, chunk):
        G = Gfun(n0, min(nsteps, n0 + chunk))
        for j in range(G.shape[0]):
            n = n0 + j
            i1 = n % M1; i2 = n % M2
            r1 = (n - N1) % M1; r2 = (n - N2) % M2
            a1_arr = a1[r1]; b1_arr = b1[r1]; a2_arr = a2[r2]; b2_arr = b2[r2]
            pJ = cJ1 * a1_arr + cJ2 * b2_arr
            a1[i1] = G[j] - b1_arr
            b1[i1] = pJ - a1_arr
            a2[i2] = pJ - b2_arr
            b2[i2] = a2_arr
            V[0] = pJ; V[1] = 2.0 * a2_arr
            if n1s:
                V[2:2 + n1s] = a1[(n - s1) % M1] + b1[(n - N1 + s1) % M1]
            if n2s:
                V[2 + n1s:] = a2[(n - s2) % M2] + b2[(n - N2 + s2) % M2]
            upd = V > PK
            np.maximum(PK, V, out=PK)
            TPK[upd] = n
    pk = {k: PK[i] for i, k in enumerate(names)}; tpk = {k: TPK[i] for i, k in enumerate(names)}
    return pk, tpk


def selftests():
    out = {}
    # (1) uniform duct (A1 = A2), ramp-step input, against the analytic image series at the closed end
    c = 400.0; dt = 0.2e-3 / c
    L = 0.05; N = int(round(L / (c * dt))); Lr = N * c * dt
    nsteps = 40000; tr = 0.3e-3
    tt = np.arange(nsteps) * dt
    g = np.clip(tt / tr, 0, 1) * 1e5
    Gf = lambda a, b: g[a:b, None]
    # split the uniform duct in two equal-area segments of N/5 and 4N/5 samples
    pk, tpk = waveguide(Gf, 1, nsteps, N // 5, N - N // 5, 1.0, 1.0, [], [])
    tau = Lr / c
    ana = np.zeros(nsteps)
    for k in range(0, int(tt[-1] / (2 * tau)) + 2):
        ana += 2 * (-1) ** k * np.interp(tt - (2 * k + 1) * tau, tt, g, left=0.0)
    out['uniform_duct_closed_end_peak'] = dict(waveguide=float(pk['closed'][0]), analytic=float(ana.max()),
                                               rel_err=float(abs(pk['closed'][0] / ana.max() - 1)))
    # (2) fundamental period of the two-segment duct (geometry of this passage) vs tan(k L1) tan(k L2) = A1 / A2
    c = 300.0; dt = 0.1e-3 / c
    N1 = int(round((L1_geom + END_CORR) / (c * dt))); N2 = int(round(L2 / (c * dt)))
    L1r, L2r = N1 * c * dt, N2 * c * dt
    nsteps = 200000
    tg = np.arange(nsteps) * dt; g = np.exp(-0.5 * ((tg - 0.5e-3) / 0.1e-3) ** 2)   # Gaussian pulse (sigma 0.1 ms): weights the fundamental
    rec = []
    a1 = np.zeros(N1 + 1); b1 = np.zeros(N1 + 1); a2 = np.zeros(N2 + 1); b2 = np.zeros(N2 + 1)
    cJ1 = 2 * A1 / (A1 + A2); cJ2 = 2 * A2 / (A1 + A2)
    for n in range(nsteps):
        i1 = n % (N1 + 1); i2 = n % (N2 + 1)
        a1a = a1[(n - N1) % (N1 + 1)]; b1a = b1[(n - N1) % (N1 + 1)]; a2a = a2[(n - N2) % (N2 + 1)]; b2a = b2[(n - N2) % (N2 + 1)]
        pJ = cJ1 * a1a + cJ2 * b2a
        a1[i1] = g[n] - b1a; b1[i1] = pJ - a1a; a2[i2] = pJ - b2a; b2[i2] = a2a
        rec.append(2 * a2a)
    rec = np.array(rec)
    F = np.abs(np.fft.rfft(rec * np.hanning(nsteps))); fr = np.fft.rfftfreq(nsteps, dt)
    j = np.argmax(F[1:]) + 1
    # refine by parabolic interpolation
    y0, y1, y2 = F[j - 1], F[j], F[j + 1]; dj = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    f_fft = (j + dj) * (fr[1] - fr[0])
    from scipy.optimize import brentq
    fun = lambda k: math.tan(k * L1r) * math.tan(k * L2r) - A1 / A2
    k1 = brentq(fun, 1e-3, (math.pi / 2 - 1e-9) / max(L1r, L2r))
    f_an = k1 * c / (2 * math.pi)
    out['two_segment_fundamental'] = dict(c=c, f_fft_Hz=float(f_fft), f_analytic_Hz=float(f_an), rel_err=float(abs(f_fft / f_an - 1)),
                                          L_eq_quarter_wave_mm=float(math.pi / (2 * k1) * 1e3))
    return out


ST = selftests()
print('selftests', json.dumps(ST), flush=True)
assert ST['uniform_duct_closed_end_peak']['rel_err'] < 1e-9 and ST['two_segment_fundamental']['rel_err'] < 5e-3, ST

Z = np.load(npz_f)
keys = [str(k) for k in Z['case_keys']]; off = Z['offsets']
nc = len(keys)
tmax = float(Z['t_s'].max())
# drive arrays on the 0.05 ms grid, padded with the last value; both conventions as extra columns
lens = np.diff(off); nt = int(lens.max())
Gc = np.zeros((nt, nc)); Gb = np.zeros((nt, nc)); peak_head = np.zeros(nc)
for i in range(nc):
    a, b = int(off[i]), int(off[i + 1])
    ph = Z['P_head_bar'][a:b].astype(float) * 1e5
    peak_head[i] = ph.max() / 1e5
    g = ph - PA
    Gc[:len(g), i] = g; Gc[len(g):, i] = g[-1]
    Gb[:, i] = np.maximum(Gc[:, i], 0.0)
G2 = np.concatenate([Gb, Gc], axis=1)       # columns: clipped (0..895), unclipped (896..1791)
DT0 = 5e-5
T_TAIL = 10e-3
t_total = (nt - 1) * DT0 + T_TAIL

C_LIST = [150.0, 181.0, 202.0, 222.0, 250.0, 280.0, 320.0, 360.0, 400.0, 450.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1049.0,
          1100.0, 1136.0, 1200.0]
res = dict(script='r4_torch_passage.py', script_sha16=H16(sys.argv[0]), inputs=dict(npz=H16(npz_f)), selftests=ST,
           geometry_mm=dict(D1=D1 * 1e3, L1=L1_geom * 1e3, end_correction=END_CORR * 1e3, D2=D2 * 1e3, L2=L2 * 1e3,
                            tap_station_from_knee=X_TAP_IN_SEG2 * 1e3, area_ratio_A1_A2=A1 / A2,
                            source='03-cad/v3.5.2/src/parts_engine.py TC-02 torch seat / passage / outlet; Mechanical jfwd_tapwall_v352_v1 passage z 127.357'),
           peak_head_bar_abs_max=float(peak_head.max()), runs=[])
for c in C_LIST:
    dt = 0.5e-3 / c
    N1 = max(2, int(round((L1_geom + END_CORR) / (c * dt)))); N2 = max(4, int(round(L2 / (c * dt))))
    s_tap = int(round(X_TAP_IN_SEG2 / (c * dt)))
    st1 = sorted(set([0, N1 // 2]))
    st2 = sorted(set([int(round(f * N2)) for f in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)] + [s_tap]))
    nsteps = int(t_total / dt) + 1

    def Gfun(a, b, dt=dt):
        t = np.arange(a, b) * dt
        k = np.minimum((t / DT0).astype(int), nt - 2)
        w = np.clip((t - k * DT0) / DT0, 0.0, 1.0)[:, None]
        return G2[k] * (1 - w) + G2[k + 1] * w
    pk, tpk = waveguide(Gfun, 2 * nc, nsteps, N1, N2, A1, A2, st1, st2)
    from scipy.optimize import brentq
    L1r, L2r = N1 * c * dt, N2 * c * dt
    k1 = brentq(lambda k: math.tan(k * L1r) * math.tan(k * L2r) - A1 / A2, 1e-3, (math.pi / 2 - 1e-9) / max(L1r, L2r))
    T1 = 2 * math.pi / (k1 * c)
    row = dict(c_m_s=c, dt_us=dt * 1e6, N1=N1, N2=N2, L1_used_mm=L1r * 1e3, L2_used_mm=L2r * 1e3,
               tap_station_used_mm_from_knee=s_tap * c * dt * 1e3, fundamental_period_ms=T1 * 1e3)
    prof = []
    for k in pk:
        v = np.maximum(pk[k][:nc], pk[k][nc:])
        i = int(np.argmax(v))
        if k == 'junction':
            x = L1r
        elif k == 'closed':
            x = L1r + L2r
        elif k.startswith('seg1_'):
            x = int(k[5:]) * c * dt
        else:
            x = L1r + int(k[5:]) * c * dt
        d = dict(x_from_open_end_mm=round(x * 1e3, 3), max_bar_abs=round((PA + float(v.max())) / 1e5, 3), case=keys[i],
                 t_peak_ms=round(float(max(tpk[k][i], tpk[k][i + nc])) * dt * 1e3, 3),
                 n_cases_above_102=int(((PA + v) / 1e5 > 102.0).sum()), n_cases_above_121=int(((PA + v) / 1e5 > 121.0).sum()),
                 n_cases_above_151p04=int(((PA + v) / 1e5 > 151.04).sum()),
                 p99_bar_abs=round(float(np.percentile((PA + v) / 1e5, 99)), 3), p50_bar_abs=round(float(np.percentile((PA + v) / 1e5, 50)), 3))
        prof.append(d)
        if k == 'junction':
            row['knee'] = d
        if k == 'closed':
            row['closed_end_torch_seat'] = d
        if k == f'seg2_{s_tap}':
            row['tap_station'] = d
    row['profile_along_passage'] = sorted(prof, key=lambda d: d['x_from_open_end_mm'])
    res['runs'].append(row)
    print('c %.0f done: tap %.2f closed %.2f bar abs (T1 %.3f ms) %.0f s' % (c, row['tap_station']['max_bar_abs'],
          row['closed_end_torch_seat']['max_bar_abs'], T1 * 1e3, time.time() - t0w), flush=True)
    json.dump(res, open(out_f, 'w'), indent=1)
best = max(res['runs'], key=lambda r: r['closed_end_torch_seat']['max_bar_abs'])
bt = max(res['runs'], key=lambda r: r['tap_station']['max_bar_abs'])
res['summary'] = dict(closed_end_max_bar_abs=best['closed_end_torch_seat']['max_bar_abs'], at_c=best['c_m_s'],
                      tap_station_max_bar_abs=bt['tap_station']['max_bar_abs'], tap_at_c=bt['c_m_s'],
                      knee_max_bar_abs=max(r['knee']['max_bar_abs'] for r in res['runs']))
res['runtime_s'] = round(time.time() - t0w, 1)
json.dump(res, open(out_f, 'w'), indent=1)
print('done', json.dumps(res['summary']), res['runtime_s'], flush=True)
