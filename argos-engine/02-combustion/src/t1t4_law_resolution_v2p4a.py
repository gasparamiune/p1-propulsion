"""Combustion v2.4a (REV-COMB-2 R2-04; LEAD CHANGELOG line 172 (3)): resolving power of the T1-T4 regression-law test
and the 'errs safe' check of the B1 grain gate against the B1 O/F histories. DERIVED from published SIM histories;
no grain grid is re-run.

Part A (law test). Total-flux signature between a law station x/L 0.80 / 0.85 / 0.90 (and 0.97) and a head reference
x/L 0.10 / 0.30, regression-weighted over each calibration firing:
    T1_100  100 % for 4.0 s          T1_50   50 % for 4.0 s
    T2      100 % 2 s, 50 % 2 s, 25 % 2 s
    T3_20   20 % for 4.0 s           T3_12p5 12.5 % for 4.0 s
    T4_DCD  the DC-D ground duty cycle on the S230 grain (mox(t) of the 'run' rows of data/v2/engine_S230/DC-D-S230_ground_reg1.csv)
  (durations ASSUMED; the founders' as-fired histories replace them). For each (a, n) of the band: the probability of
  positively showing the oxidiser-flux law when it is true, at sigma(ratio) = 1.5 % (LEAD) with a one-sided 95 % bound,
  P = Phi(delta/sigma - 1.645); the sigma that gives 95 % power, delta/3.29; and the repeats N = ceil(s1^2/(st^2 - ss^2))
  for an ASSUMED single-firing random scatter s1 and residual systematic ss.
Part B (errs safe). E = regression-weighted total-flux enhancement at the gate station x/L 0.97,
    E = sum(r e) / sum(r),  e = (1 + x/OF)^n,
  over each B1 record (gnc.json v3 85 m cycles and the v3.1 62 m records, Combustion grain_q1d histories; weights = web
  consumption rate from the port-diameter history) and over each calibration firing at the same (a, n). If the truth is
  total-flux, a_meas = E_cal x a_true and the B1 aft regression is E_B1 x the oxidiser-flux prediction, so the gate with
  k_a = 1.1 a_meas errs safe with the full 1.1 kept for measurement error iff rho = E_B1 / E_cal <= 1; the allowance left
  is 1.1/rho - 1. Low-O/F phases: share of the B1 web consumption below the calibration firing's lowest O/F.
Model: e(x) assumes fuel added uniformly along the port (first order). Calibration firings use the quasi-steady
port-average law r = a x 1 mm/s x (G_ox/300)^n (grain_q1d anchoring, rho_f 1000 kg/m3 ASSUMED, L 0.230 m, D0 25 mm);
mox per throttle step from engine_S230/throttle_map_v2.csv (P_tank 4.5 MPa, D 25 mm), held constant in a step (the Pc
loop holds thrust). The analytic model is checked against the grain_q1d DC-D history at a x1.0, n 0.5.
usage: python -I t1t4_law_resolution_v2p4a.py DATA_V2_DIR OUT_JSON
"""
import csv, glob, hashlib, json, math, os, sys
from statistics import NormalDist

d, out = sys.argv[1:3]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
RHO_F, L_G, D0, R0 = 1000.0, 0.230, 0.025, 1.0e-3
X_GATE, X_LAW, X_REF = 0.97, (0.80, 0.85, 0.90), (0.10, 0.30)
SIG_T = 0.015                                    # LEAD line 172 (3)
Z = NormalDist().inv_cdf(0.95)                   # one-sided 95 %
NS = (0.35, 0.5, 0.68)

# ---- inputs
tm_path = os.path.join(d, 'engine_S230', 'throttle_map_v2.csv')
dcd_path = os.path.join(d, 'engine_S230', 'DC-D-S230_ground_reg1.csv')
b1_paths = sorted(glob.glob(os.path.join(d, 'dc_gncv3_band', 'DC-B1v3*.csv'))) + \
    sorted(glob.glob(os.path.join(d, 'dc_gncv31_62m', 'lane*', 'DC-B1v31_62m_*.csv')))
inputs = {os.path.relpath(p, d): sha(p)[:16] for p in [tm_path, dcd_path] + b1_paths}
manifest16 = hashlib.sha256(''.join(f'{k}{v}' for k, v in sorted(inputs.items())).encode()).hexdigest()[:16]

rows = [r for r in csv.reader(open(tm_path)) if r and not r[0].startswith('#')]
TM = [dict(zip(rows[0], r)) for r in rows[1:]]
MOX = {float(r['frac']): float(r['mdot_ox']) for r in TM
       if abs(float(r['D_port_m']) - 0.025) < 1e-9 and abs(float(r['P_tank_Pa']) - 4.5e6) < 1.0}
assert all(f in MOX for f in (1.0, 0.5, 0.25, 0.2, 0.125)), MOX

def read_hist(p, states=('run',)):
    out = []
    for r in csv.DictReader(open(p)):
        if r['state'] not in states:
            continue
        mox = float(r['mox'])
        if mox <= 0:
            continue
        mf = float(r['mf'])
        out.append((float(r['t']), mox, mf, 0.5 * (float(r['D_min']) + float(r['D_max']))))
    return out

DCD = read_hist(dcd_path)
DT_DCD = DCD[1][0] - DCD[0][0]

def schedule(name):
    if name == 'T1_100': return [(MOX[1.0], 4.0)]
    if name == 'T1_50': return [(MOX[0.5], 4.0)]
    if name == 'T2': return [(MOX[1.0], 2.0), (MOX[0.5], 2.0), (MOX[0.25], 2.0)]
    if name == 'T3_20': return [(MOX[0.2], 4.0)]
    if name == 'T3_12p5': return [(MOX[0.125], 4.0)]
    if name == 'T4_DCD': return [(m, DT_DCD) for (_, m, _, _) in DCD]
    raise KeyError(name)
CAL = ('T1_100', 'T1_50', 'T2', 'T3_20', 'T3_12p5', 'T4_DCD')

def analytic(a, n, sched, dt=0.01):
    """quasi-steady port-average history: list of (r [m/s], OF) per step of dt"""
    D = D0; h = []
    D_END = 0.0535
    for mox, dur in sched:
        k = max(int(round(dur / dt)), 1); ds = dur / k
        for _ in range(k):
            if D >= D_END - 1e-12:
                break                      # web consumed (S230: D 25 -> 53.5 mm); grain_q1d stops regressing there too
            G = 4.0 * mox / (math.pi * D * D)
            r = a * R0 * (G / 300.0) ** n
            mf = RHO_F * math.pi * D * L_G * r
            dD = min(2.0 * r * ds, D_END - D)
            h.append((0.5 * dD, mox / mf))
            D = D + dD
    return h

def wmean_e(h, x, n):
    """regression-weighted mean of e = (1 + x/OF)^n; h = [(weight, OF)]"""
    sw = sum(w for w, _ in h)
    return sum(w * (1.0 + x / of) ** n for w, of in h if of > 0) / sw

def sig(h, x, xr, n):
    """total-flux ratio of integrated regression at x over xr"""
    return wmean_e(h, x, n) / wmean_e(h, xr, n)

# ---- model check: analytic DC-D vs grain_q1d DC-D at a 1.0, n 0.5
h_q1d = []
for i in range(1, len(DCD)):
    t0, m0, f0, D0_ = DCD[i - 1]; t1, m1, f1, D1_ = DCD[i]
    dw = max(D1_ - D0_, 0.0) * 0.5
    if dw > 0 and f1 > 0:
        h_q1d.append((dw, m1 / f1))
h_an = analytic(1.0, 0.5, schedule('T4_DCD'))
check = dict(E097_q1d=round(wmean_e(h_q1d, X_GATE, 0.5), 4), E097_analytic=round(wmean_e(h_an, X_GATE, 0.5), 4),
             web_q1d_mm=round(1e3 * sum(w for w, _ in h_q1d), 3), web_analytic_mm=round(1e3 * sum(w for w, _ in h_an), 3),
             OF_wmean_q1d=round(sum(w * of for w, of in h_q1d) / sum(w for w, _ in h_q1d), 2),
             OF_wmean_analytic=round(sum(w * of for w, of in h_an) / sum(w for w, _ in h_an), 2))

# ---- Part A: signatures and power at the calibration firings
A = {}
for a in (0.6, 1.0, 1.5):
    for n in NS:
        for c in CAL:
            h = analytic(a, n, schedule(c))
            ofs = [of for _, of in h]
            row = dict(OF_wmean=round(sum(w * of for w, of in h) / sum(w for w, _ in h), 2), OF_min=round(min(ofs), 2),
                       OF_max=round(max(ofs), 2), web_mm=round(1e3 * sum(w for w, _ in h), 2), sig={})
            for x in X_LAW + (X_GATE,):
                for xr in X_REF:
                    s = sig(h, x, xr, n); dl = s - 1.0
                    row['sig'][f'{x:.2f}/{xr:.2f}'] = dict(ratio=round(s, 4), P_show_ox_at_1p5pct=round(NormalDist().cdf(dl / SIG_T - Z), 3),
                                                           sigma_for_95pct_power_pct=round(100 * dl / (2 * Z), 2))
            row['E_gate'] = round(wmean_e(h, X_GATE, n), 4)
            A[f'a{a:g}|n{n:g}|{c}'] = row

# ---- repeats for the sigma target
REP = {}
for s1 in (0.010, 0.020, 0.030):
    for ss in (0.005, 0.010, 0.014):
        den = SIG_T ** 2 - ss ** 2
        REP[f's1_{100*s1:.0f}pct|ss_{100*ss:.1f}pct'] = (math.ceil(s1 ** 2 / den - 1e-12) if den > 0 else None)

# ---- Part B: B1 records against calibration firings
def parse(p):
    b = os.path.basename(p)[:-4]
    a = float(b.split('_reg')[1].split('_')[0]); n = float(b.split('_n')[-1].split('_')[0])
    law = 'total' if b.endswith('_lawtotal') else 'ox'
    return b, a, n, law
def web_hist(H):
    h = []
    for i in range(1, len(H)):
        dw = max(H[i][3] - H[i - 1][3], 0.0) * 0.5
        mf = H[i][2]
        if dw > 0 and mf > 0:
            h.append((dw, H[i][1] / mf))
    return h
B = {}
for p in b1_paths:
    b, a, n, law = parse(p)
    h = web_hist(read_hist(p, ('run', 'start')))        # the record as flown, start transients included (larger E: conservative)
    h_run = web_hist(read_hist(p, ('run',)))
    if not h:
        continue
    web = sum(w for w, _ in h)
    E = wmean_e(h, X_GATE, n)
    ofw = sorted(h, key=lambda z: z[1]); acc = 0.0; of05 = None
    for w, of in ofw:
        acc += w
        if acc >= 0.05 * web:
            of05 = of; break
    row = dict(a=a, n=n, law=law, web_mm=round(1e3 * web, 2), OF_wmean=round(sum(w * of for w, of in h) / web, 2),
               OF_p05_by_web=round(of05, 2), OF_min=round(min(of for _, of in h), 2), E097=round(E, 4),
               e097_max=round(max((1 + X_GATE / of) ** n for _, of in h), 4),
               E097_run_rows_only=round(wmean_e(h_run, X_GATE, n), 4) if h_run else None, vs_cal={})
    for c in CAL:
        hc = analytic(a, n, schedule(c))
        Ec = wmean_e(hc, X_GATE, n); ofmin_c = min(of for _, of in hc)
        rho = E / Ec
        low = sum(w for w, of in h if of < ofmin_c) / web
        row['vs_cal'][c] = dict(E_cal=round(Ec, 4), rho=round(rho, 4), allowance_left=round(1.1 / rho - 1.0, 4),
                                share_web_below_cal_OFmin=round(low, 3), cal_OF_min=round(ofmin_c, 2))
    B[b] = row

def summ(c, recs):
    rr = [B[k]['vs_cal'][c] for k in recs]
    i = max(range(len(rr)), key=lambda j: rr[j]['rho'])
    return dict(n_records=len(rr), rho_max=rr[i]['rho'], record=recs[i], allowance_left_min=rr[i]['allowance_left'],
                rho_min=min(x['rho'] for x in rr), share_web_below_cal_OFmin_max=max(x['share_web_below_cal_OFmin'] for x in rr))
groups = dict(all=sorted(B), m85=sorted(k for k in B if k.startswith('DC-B1v3') and not k.startswith('DC-B1v31')), m62=sorted(k for k in B if k.startswith('DC-B1v31_62m')))
SUM = {g: {c: summ(c, ks) for c in CAL} for g, ks in groups.items() if ks}
res = dict(version='v2.4a', date='2026-10-13', script='02-combustion/src/t1t4_law_resolution_v2p4a.py',
           request='REV-COMB-2 R2-04; LEAD CHANGELOG line 172 (3)', inputs_manifest_sha16=manifest16, inputs=inputs,
           constants=dict(rho_f=RHO_F, L_grain_m=L_G, D0_m=D0, r_anchor='a x 1 mm/s at G_ox 300 kg/m2s', x_gate=X_GATE,
                          x_law=X_LAW, x_ref=X_REF, sigma_target=SIG_T, z_one_sided_95=round(Z, 4),
                          mox_by_throttle_kg_s={str(k): v for k, v in sorted(MOX.items())}),
           calibration_firings={c: ('DC-D duty cycle mox(t)' if c == 'T4_DCD' else schedule(c)) for c in CAL},
           model_check_DCD_a1_n0p5=check, partA=A, repeats=REP, partB_records=B, partB_summary=SUM,
           tags=dict(model='DERIVED first-order local total-flux factor (1 + x/OF)^n; calibration histories quasi-steady analytic (ASSUMED durations); B1 histories SIM grain_q1d on gnc.json v3 / v3.1 cycles',
                     sigma_terms='s1 and ss ASSUMED bands; the founders measure s1 (repeat firings) and bound ss (section 5 of the spec)'))
json.dump(res, open(out, 'w'), indent=1)
print('model check DC-D a1 n0.5:', check)
for g, sm in SUM.items():
    print('group', g)
    for c, v in sm.items():
        print(f"  {c:8s} rho_max {v['rho_max']:.4f} allowance_left_min {v['allowance_left_min']:+.4f} rho_min {v['rho_min']:.4f} share_below_calOFmin_max {v['share_web_below_cal_OFmin_max']:.3f} ({v['record']})")
for k in ('a1|n0.35|T1_100', 'a1|n0.5|T1_100', 'a1|n0.68|T1_100', 'a1|n0.35|T2', 'a1|n0.5|T2', 'a1|n0.35|T3_20', 'a1|n0.5|T3_20', 'a1|n0.35|T4_DCD', 'a1|n0.5|T4_DCD', 'a1.5|n0.35|T3_20', 'a0.6|n0.35|T3_20'):
    v = A[k]; s = v['sig']
    print(k, 'OF', v['OF_wmean'], v['OF_min'], v['OF_max'], 'E', v['E_gate'], '| 0.85/0.10', s['0.85/0.10'], '| 0.97/0.10', s['0.97/0.10']['ratio'])
print('repeats', REP)
