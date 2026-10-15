"""Quasi-static F(lift) of the Combustion shutdown traces (actuator_rate_check_v2, 0.25 s stroke) by de-lagging F(t)."""
import json, sys, numpy as np
P = sys.argv[1]
d = json.load(open(P))
tr = [s for s in d['shutdown'] if abs(s['full_stroke_s'] - 0.25) < 1e-6]
for tau in (0.0, 0.004, 0.006, 0.008):
    print("tau_c", tau)
    for s in tr:
        t = np.array(s['trace']['t']); F = np.array(s['trace']['F']); h = np.array(s['trace']['h_mm'])
        dF = np.gradient(F, t)
        Fq = F + tau * dF
        out = []
        for hh in (1.75, 1.5, 1.25, 1.0, 0.753, 0.6, 0.5, 0.4, 0.366, 0.3, 0.206, 0.15, 0.1, 0.07, 0.05, 0.03):
            if hh > s['lift_before_mm']: continue
            i = np.where(h <= hh)[0]
            i = i[i > 20]
            if len(i) == 0: continue
            j = i[0]
            # interpolate between j-1 and j
            a = (hh - h[j]) / (h[j-1] - h[j]) if h[j-1] != h[j] else 0
            out.append(f"{hh:.3f}:{Fq[j] + a*(Fq[j-1]-Fq[j]):.1f}")
        print(f"  F0 {s['F_before_N']:.0f} l0 {s['lift_before_mm']:.3f} | " + " ".join(out))
