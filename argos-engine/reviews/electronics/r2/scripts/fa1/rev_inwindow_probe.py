#!/usr/bin/env python3
"""REV-ELEC-2 probe for LEAD 203 (1)(b): what a relight-window ride-through costs on GENUINE in-window over-pressure events.
Synthetic head-pressure histories (DESIGN of this probe, not Combustion data) through the reviewer chain of rev_fa1_chain.py
(no sense line, transducer lag 0.9 ms, v_sat 4.95 V, instantaneous ADC, worst of 4 ADC phases). For each event the first detection
time is computed for the as-built set (filtered 30 bar abs for 5 ms, comparator RC 5.283 ms nominal trip, a single 1 kHz reading
>= 4.75 V in IGNITION) and for ride-through sets that lengthen the persistence (13 / 15 ms), the comparator RC (10 / 12.5 ms) and the
over-range rule (N consecutive readings >= 4.75 V). The head time above 45 bar abs from the light to detection + t_close is reported
with t_close = 0.038 s [ASSUMED: S6 throat_blocked_70pct_RUN abort -> MV closed 0.055 - 0.017 s, SIL]; after the closure the probe
does not model the decay. SIM on synthetic inputs; not hardware evidence, not physical approval.
Usage: python -I rev_inwindow_probe.py <rev_fa1_chain.py> <fa1_envelope_v2p4a.json> <out_json>"""
import importlib.util
import json
import sys

import numpy as np
from scipy import signal

spec = importlib.util.spec_from_file_location('rc', sys.argv[1])
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

T, I0, DT = rc.T, rc.I0, rc.DT
T_CLOSE = 0.038


def hist(kind, d):
    p0 = d['state']['P0_cold_flow_Pa']
    t = np.clip(T, 0.0, None)
    if kind == 'step50_sustained':          # blocked throat / sustained hard start in the light window: 50 bar abs from 3 ms
        p = p0 + (50e5 - p0) * np.clip((t - 0.001) / 0.002, 0, 1)
    elif kind == 'step40_sustained':
        p = p0 + (40e5 - p0) * np.clip((t - 0.001) / 0.002, 0, 1)
    elif kind == 'ramp_to_60_in_30ms':      # runaway in the window
        p = p0 + (60e5 - p0) * np.clip(t / 0.030, 0, 1)
    elif kind in ('fa1_worst_then_35', 'fa1_worst_then_47'):   # the worst FA-1 head history, then a sustained plateau from 25 ms
        keys = list(d['cases'].keys())
        pk = [d['cases'][k]['peak_head_bar'] for k in keys]
        h = np.maximum(np.array(d['cases'][keys[int(np.argmax(pk))]]['P_head_hist_bar']) * 1e5, p0)
        grid = np.array(d['history_grid_ms']) * 1e-3
        p = np.interp(np.clip(t, 0, grid[-1]), grid, h)
        lvl = 35e5 if kind.endswith('35') else 47e5
        p = np.where(t > grid[-1], lvl, p)
        p = np.where((t > 0.020) & (t <= grid[-1]), np.maximum(p, lvl * (t - 0.020) / 0.005), p)
    elif kind == 'fa1_worst_only':
        keys = list(d['cases'].keys())
        pk = [d['cases'][k]['peak_head_bar'] for k in keys]
        h = np.maximum(np.array(d['cases'][keys[int(np.argmax(pk))]]['P_head_hist_bar']) * 1e5, p0)
        grid = np.array(d['history_grid_ms']) * 1e-3
        p = np.interp(np.clip(t, 0, grid[-1]), grid, h)
    else:
        raise ValueError(kind)
    p = np.where(T < 0, p0, p)
    return p


def detect(P, pers_ticks, tau_cmp, n_over):
    """first detection time (s from the light) over 4 ADC phases (earliest) for one history"""
    x = rc.foh_lag(P[None, :], 0.0009, P[:1])[0]
    v = np.clip(0.5 + 4.0 * (x - rc.PAMB) / rc.FS_PA, 0.0, 4.95)
    vc = rc.foh_lag(v[None, :], tau_cmp, v[:1])[0]
    a = np.nonzero(vc[I0:] > rc.V_NOM)[0]
    t_cmp = T[I0 + a[0]] if len(a) else np.inf
    s = np.minimum(v, rc.ADC_MAX)
    b, aa = signal.butter(2, 50.0, fs=1000.0)
    best = (np.inf, 'none')
    for ph in range(4):
        first = I0 + ph * rc.SUB - (rc.N_PRE // rc.TICK) * rc.TICK
        while first - 3 * rc.SUB < 0:
            first += rc.TICK
        ticks = np.arange(first, len(T), rc.TICK)
        rd = (s[ticks] + s[ticks - rc.SUB] + s[ticks - 2 * rc.SUB] + s[ticks - 3 * rc.SUB]) / 4.0
        tt = T[ticks]
        raw_g = (rd - 0.5) / 4.0 * rc.FS_PA
        zi = signal.lfilter_zi(b, aa) * raw_g[0]
        fg, _ = signal.lfilter(b, aa, raw_g, zi=zi)
        fabs = fg + rc.PAMB
        run30 = 0
        runhi = 0
        t_fw = np.inf
        t_hi = np.inf
        for k in np.nonzero(tt >= 0)[0]:
            run30 = run30 + 1 if fabs[k] > rc.P30 else 0
            if run30 >= pers_ticks and t_fw == np.inf:
                t_fw = tt[k]
            runhi = runhi + 1 if rd[k] >= rc.V_HI else 0
            if runhi >= n_over and t_hi == np.inf:
                t_hi = tt[k]
        for tv, lab in ((t_fw, 'firmware'), (t_hi, 'over-range'), (t_cmp, 'comparator')):
            if tv < best[0]:
                best = (tv, lab)
    return best


def above45(P, t_end):
    m = (T >= 0) & (T <= t_end)
    return float(((P[m] > 45e5).sum()) * DT)


def main():
    d = json.load(open(sys.argv[2]))
    sets = [('as_built', 5, 0.005283, 1), ('ride_13ms_rc10_n13', 13, 0.010, 13), ('ride_15ms_rc12p5_n15', 15, 0.0125, 15)]
    out = {'id': 'rev_elec2_inwindow_probe', 'tags': 'SIM on synthetic inputs (reviewer); t_close 0.038 s ASSUMED', 'events': []}
    for kind in ('fa1_worst_only', 'step40_sustained', 'step50_sustained', 'ramp_to_60_in_30ms', 'fa1_worst_then_35', 'fa1_worst_then_47'):
        P = hist(kind, d)
        row = {'event': kind, 'peak_bar_abs': round(float(P[I0:].max()) / 1e5, 2)}
        for name, pers, tau, nover in sets:
            td, lab = detect(P, pers, tau, nover)
            t45 = above45(P, (td if np.isfinite(td) else 0.1) + T_CLOSE)
            row[name] = {'first_detection_ms': None if not np.isfinite(td) else round(td * 1e3, 2), 'path': lab,
                         'head_time_above_45bar_to_detection_plus_close_ms': round(t45 * 1e3, 2)}
        out['events'].append(row)
        print(json.dumps(row))
    json.dump(out, open(sys.argv[3], 'w'), indent=1)


if __name__ == '__main__':
    main()
