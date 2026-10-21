# v2.13 ITEM 2 (LEAD 16:11Z): worst-case hold-end gap g0 = |T_sensor(hold end) - T_sensor(hold start)| (T_c frozen over the hold)
# against the 3 K rate trip, on the Mechanical SIM seat histories (Electronics v2.12 results/v2p12/seat_hist, TC4 sensor node dT_sensor_K).
# Tags: inputs SIM (Mechanical seat histories), hold durations DERIVED from config.h / the SIL timing, results DERIVED.
import csv, json, sys, hashlib
D = sys.argv[1]; OUT = sys.argv[2]
def load(fn):
    t, y = [], []
    with open(fn) as f:
        r = csv.DictReader(f)
        for row in r: t.append(float(row['t_s'])); y.append(float(row['dT_sensor_K']))
    return t, y
def interp(t, y, x):
    if x <= t[0]: return y[0]
    if x >= t[-1]: return y[-1]
    lo, hi = 0, len(t) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if t[m] <= x: lo = m
        else: hi = m
    f = (x - t[lo]) / (t[hi] - t[lo]); return y[lo] + f * (y[hi] - y[lo])
def maxdelta(t, y, a, b, dur, step=0.005):
    # largest |T(s + dur) - T(s)| for hold starts s in [a, b]
    best, at = 0.0, a; s = a
    while s <= b + 1e-12:
        g = abs(interp(t, y, s + dur) - interp(t, y, s))
        if g > best: best, at = g, s
        s += step
    return best, at
def maxrate(t, y, a, b, w=0.1, step=0.005):
    best, at = 0.0, a; s = a
    while s <= b + 1e-12:
        g = abs(interp(t, y, s + w) - interp(t, y, s)) / w
        if g > best: best, at = g, s
        s += step
    return best, at
# hold durations (DERIVED): IGNITION entry -> E1 0.045-0.051 s (SIL first start / relight; legal >= 0.045 s), + the light window
# (kIgnWindow: flight relight 0.65 s, pad 0.40 s, stand 0.35 s), + kPcSeatHoldPostE2_s 0.45 s (E2 at the window end = longest legal hold)
HOLD = {'A1_flight_relight': 0.048 + 0.65 + 0.45, 'A1_pad_first': 0.048 + 0.40 + 0.45, 'stand_first': 0.048 + 0.35 + 0.45,
        'stand_relight': 0.051 + 0.35 + 0.45}
files = {'A1': 'seat_hist_A1_NF2b.csv', 'GVHI': 'seat_hist_B1_R4_GVHI.csv', 'GVLO': 'seat_hist_B1_R4_GVLO.csv'}
MECO = {'A1': 3.541, 'GVHI': 21.651, 'GVLO': 21.651}   # Mechanical burn ends (S13T seatMechT)
E0 = {'A1': 22.211, 'GVHI': 21.651 + 18.670, 'GVLO': 21.651 + 18.670}   # relight times (S13T: A1 22.211 s; stand S + 18.67 s)
res = {'tag': 'DERIVED on SIM (Mechanical seat histories, TC4 sensor node dT_sensor_K); hold durations DERIVED (config.h windows + 0.45 s)',
       'trip_K': 3.0, 'slew_Kps': 5.0, 'hold_s': HOLD, 'inputs': {}, 'cases': {}}
for k, fn in files.items():
    p = D + '/' + fn; res['inputs'][fn] = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
    t, y = load(p)
    first = 'A1_pad_first' if k == 'A1' else 'stand_first'
    rel = 'A1_flight_relight' if k == 'A1' else 'stand_relight'
    c = {}
    g, at = maxdelta(t, y, 0.0, 0.0, HOLD[first]); c['first_start_nominal'] = {'hold_s': HOLD[first], 'g0_K': round(g, 4)}
    g, at = maxdelta(t, y, E0[k] - 0.2, E0[k] + 0.2, HOLD[rel]); r, rat = maxrate(t, y, E0[k] - 0.2, E0[k] + 0.2 + HOLD[rel])
    c['relight_nominal_E0'] = {'E0_mech_s': E0[k], 'hold_s': HOLD[rel], 'g0_K': round(g, 4), 'at_hold_start_s': round(at, 3),
                               'max_rate_0p1s_in_hold_Kps': round(r, 4), 'margin_vs_3K': round(3.0 / g, 2) if g > 0 else None}
    g, at = maxdelta(t, y, MECO[k], t[-1] - HOLD[rel], HOLD[rel], 0.01); r, rat = maxrate(t, y, MECO[k], t[-1] - 0.1, 0.1, 0.01)
    c['relight_any_time_after_burn1'] = {'hold_s': HOLD[rel], 'g0_K': round(g, 4), 'at_hold_start_s': round(at, 3),
                                         'max_rate_0p1s_Kps': round(r, 4), 'at_s': round(rat, 3), 'margin_vs_3K': round(3.0 / g, 2),
                                         'margin_catchup_bound_5Kps_x_hold': round(5.0 / (g / HOLD[rel]), 2)}
    res['cases'][k] = c
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps(res['cases'], indent=1))
# A1 (brief) hold cost re-derivation: the seat drift the held compensation does not follow over IGNITION entry -> E2 (the light
# detection part; E2 at the window end = longest legal) and over the whole hold, x coef (k = 1: 0.0248 bar/K, k = 3: 0.0744 bar/K;
# sim.h seat_c_PaK x seat_k, SIM basis)
D_E2 = {'A1_flight_relight': 0.048 + 0.65, 'A1_pad_first': 0.048 + 0.40, 'stand_first': 0.048 + 0.35, 'stand_relight': 0.051 + 0.35}
cost = {'tag': 'DERIVED on SIM (Mechanical seat histories); coef k = 1 0.0248 bar/K, k = 3 0.0744 bar/K (sim.h seat_c_PaK)', 'D_entry_to_E2_s': D_E2, 'cases': {}}
for k, fn in files.items():
    t, y = load(D + '/' + fn)
    first = 'A1_pad_first' if k == 'A1' else 'stand_first'
    rel = 'A1_flight_relight' if k == 'A1' else 'stand_relight'
    c = {}
    for lab, typ, a, b in (('first_start', first, 0.0, 0.0), ('relight_nominal', rel, E0[k] - 0.2, E0[k] + 0.2),
                           ('relight_any_time', rel, MECO[k], t[-1] - HOLD[rel])):
        g1, _ = maxdelta(t, y, a, b, D_E2[typ], 0.01); g2, _ = maxdelta(t, y, a, b, HOLD[typ], 0.01)
        c[lab] = {'drift_entry_to_E2_K': round(g1, 4), 'bar_k1': round(g1 * 0.0248, 4), 'bar_k3': round(g1 * 0.0744, 4),
                  'drift_whole_hold_K': round(g2, 4), 'whole_hold_bar_k3': round(g2 * 0.0744, 4)}
    cost['cases'][k] = c
res['hold_cost'] = cost
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps(cost['cases'], indent=1))
