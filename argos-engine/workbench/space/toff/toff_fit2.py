"""Fit the GNC reduced tail-off model (lift ramp + actuator lag + table + chamber lag) to the Combustion
actuator_rate_check_v2 0.25 s shutdown cases (t10, impulse). Usage: toff_fit2.py <actuator_rate_check_v2.json>"""
import json, sys, numpy as np
d = json.load(open(sys.argv[1]))
S = sorted([s for s in d['shutdown'] if abs(s['full_stroke_s'] - 0.25) < 1e-6], key=lambda s: s['F_before_N'])
vs = 4.0 / 0.25 if False else S[0]['lift_before_mm'] * 0  # placeholder
full = [x for x in d['start_rule'] if abs(x['full_stroke_s'] - 0.25) < 1e-6][0]
vs = full['speed_mm_s']
tl0 = [s['lift_before_mm'] for s in S]; tf0 = [s['F_before_N'] for s in S]

def model(F0, lc, lag_a, lag_c, dt=1e-3):
    tl = np.array([lc] + tl0); tf = np.array([0.0] + tf0)
    l_r = np.interp(F0, tf, tl); l_a = l_r; Fa = F0; imp = 0.0; t = 0.0; t10 = None
    for k in range(2000):
        l_r = max(0.0, l_r - vs * dt)
        l_a += (l_r - l_a) * dt / max(lag_a, dt)
        Fq = np.interp(l_a, tl, tf)
        Fa += (Fq - Fa) * dt / max(lag_c, dt)
        t += dt
        if Fa < 0.5:
            Fa = 0.0
        imp += Fa * dt
        if t10 is None and Fa < 0.1 * F0:
            t10 = t
        if Fa == 0.0:
            break
    return t10, imp

best = None
for lc in np.arange(0.0, 0.101, 0.005):
    for lag_c in np.arange(0.002, 0.0201, 0.001):
        err = 0.0
        for s in S:
            t10, imp = model(s['F_before_N'], lc, 0.010, lag_c)
            err += ((imp - s['tailoff_impulse_Ns']) / max(s['tailoff_impulse_Ns'], 1.0)) ** 2 \
                + ((t10 - s['t_to_10pct_of_F_before_s']) / 0.01) ** 2 * 0.25
        if best is None or err < best[0]:
            best = (err, lc, lag_c)
print("vs", vs, "mm/s; best (err, l_cut mm, lag_c s):", best)
for lc, lag_c in [(0.0, 0.004), (best[1], best[2])]:
    print(f"l_cut {lc:.3f} lag_a 0.010 lag_c {lag_c:.3f}")
    for s in S:
        t10, imp = model(s['F_before_N'], lc, 0.010, lag_c)
        print(f"   F0 {s['F_before_N']:6.1f}: t10 {t10:.3f} (comb {s['t_to_10pct_of_F_before_s']:.3f})  imp {imp:6.2f} (comb {s['tailoff_impulse_Ns']:6.2f})")

print("\n3-parameter fit (lag_a, lag_c, l_cut), weights: impulse rel. error + t10 error / 5 ms")
best = None
for lc in np.arange(0.0, 0.0601, 0.005):
    for lag_a in np.arange(0.0, 0.0121, 0.001):
        for lag_c in np.arange(0.001, 0.0061, 0.001):
            err = 0.0
            for s in S:
                t10, imp = model(s['F_before_N'], lc, lag_a, lag_c)
                w = 2.0 if s['F_before_N'] > 300 else 1.0
                err += w * (((imp - s['tailoff_impulse_Ns']) / max(s['tailoff_impulse_Ns'], 1.0)) ** 2
                            + ((t10 - s['t_to_10pct_of_F_before_s']) / 0.005) ** 2 * 0.25)
            if best is None or err < best[0]:
                best = (err, lc, lag_a, lag_c)
print("best (err, l_cut, lag_a, lag_c):", best)
for s in S:
    t10, imp = model(s['F_before_N'], best[1], best[2], best[3])
    print(f"   F0 {s['F_before_N']:6.1f}: t10 {t10:.3f} (comb {s['t_to_10pct_of_F_before_s']:.3f})  imp {imp:6.2f} (comb {s['tailoff_impulse_Ns']:6.2f}) err {100*(imp/s['tailoff_impulse_Ns']-1):+.1f} %")
for F0 in (159.0, 175.0):
    print("   landing F0", F0, model(F0, best[1], best[2], best[3]))
