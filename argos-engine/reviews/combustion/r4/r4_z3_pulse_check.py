"""REV-COMB-4 reviewer script: equivalent static pressure of pulses admitted by the LC-TB70 Z3 shape limits (REV-COMB-4 (f)(ii)).

Z3 (Mechanical lc_tb70_envelope_v1): peak <= 75.519 bar abs, time above 63.1 bar abs <= 3.0 ms, 10-90 % rise >= 0.8 ms.  Question: if
the Z3 ceiling were simply raised to cover the FA-1 grid peak (88.02 -> 88.1 bar abs) with the same time and rise limits, what is the
largest undamped SDOF equivalent static pressure a pulse inside those limits can produce, against FA1S 151.04 bar abs?
Pulse family (ASSUMED, one admissible shape, not a supremum over all shapes): symmetric trapezoid from ambient, linear rise and fall
with 10-90 % = 0.8 ms (full ramp 1.0 ms), hold chosen so the time above 63.1 bar abs equals the limit (3.0 / 1.7 / 1.0 ms; 1.7 ms is
the grid's longest time above 63.1, 1.669 ms).  Undamped SDOF from rest, static gain 1, exact piecewise-linear recurrence on a 2 us
grid, free vibration after the pulse included (amplitude), periods 0.1-50 ms (120 log-spaced).
Tags: pulse ASSUMED; response DERIVED.  Not physical evidence.
usage: python -I r4_z3_pulse_check.py OUT_JSON
"""
import hashlib, json, sys
import numpy as np

out_f = sys.argv[1]
PA = 1.01325
TS = np.geomspace(0.1e-3, 50e-3, 120)


def trap(peak, tr, t_above_lim, lev=63.1, dt=2e-6, tail=0.05):
    frac = (lev - PA) / (peak - PA)
    t_ramp_above = (1 - frac) * tr
    hold = max(t_above_lim - 2 * t_ramp_above, 0.0)
    t = np.arange(0, 2 * tr + hold + tail, dt)
    g = np.interp(t, [0, tr, tr + hold, 2 * tr + hold], [0, peak - PA, peak - PA, 0])
    return t, g, hold


def sdof_max(t, g):
    w = 2 * np.pi / TS; dt = t[1] - t[0]; c = np.cos(w * dt); s = np.sin(w * dt)
    u = np.zeros_like(TS); v = np.zeros_like(TS); um = np.zeros_like(TS)
    for i in range(len(t) - 1):
        g0 = g[i]; sl = (g[i + 1] - g[i]) / dt
        C = u - g0; D = (v - sl) / w
        u, v = g0 + sl * dt + C * c + D * s, sl - C * w * s + D * w * c
        np.maximum(um, u, out=um)
    gl = g[-1]
    um = np.maximum(um, gl + np.sqrt((u - gl) ** 2 + (v / w) ** 2))
    return um


res = dict(script='r4_z3_pulse_check.py', script_sha16=hashlib.sha256(open(sys.argv[0], 'rb').read()).hexdigest()[:16],
           FA1S_bar_abs=151.04, cases={})
for peak, lim in ((75.519, 3.0e-3), (88.1, 3.0e-3), (88.1, 1.7e-3), (88.1, 1.0e-3)):
    t, g, hold = trap(peak, 1.0e-3, lim)
    um = sdof_max(t, g)
    j = int(np.argmax(um))
    res['cases'][f'peak{peak}_tabove63p1_{lim * 1e3:.1f}ms'] = dict(hold_ms=round(hold * 1e3, 4), max_ESP_bar_abs=round(PA + float(um[j]), 2),
                                                                  at_T_ms=round(float(TS[j]) * 1e3, 3),
                                                                  DLF=round(float(um[j]) / (peak - PA), 3),
                                                                  above_FA1S=bool(PA + float(um[j]) > 151.04))
json.dump(res, open(out_f, 'w'), indent=1)
print(json.dumps(res, indent=1))
