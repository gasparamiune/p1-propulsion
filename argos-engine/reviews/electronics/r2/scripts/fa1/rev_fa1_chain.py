#!/usr/bin/env python3
"""REV-ELEC-2 reviewer chain for the FA-1 over-range question (LEAD 194 (7), 203 (1)). Reviewer code, written independently of
06-electronics/calc/v2p10/fa1_overrange_chain.cpp; it reads Combustion's envelope directly (not the author's extracted text files).

Model (each element is stated so a reader can compare it with the author's chain):
  P_head(t)  : fa1_envelope_v2p4a.json P_head_hist_bar (0.1 ms grid, 0-25 ms after the light), linear between grid points; each sample
               limited below at state.P0_cold_flow_Pa (as the author; the vapour_once first sample is the construct's initial gas);
               50 ms before the light at the first (limited) sample; after 25 ms the 25 ms value is held (as the author; ASSUMED).
  transducer : first-order lag tau_x, solved exactly for a piecewise-linear input on a 5 us grid; output v = 0.5 + 4 (P - 101325) / 7e6
               limited to [0, v_sat]. No sense line (the author's line rows are a sensitivity only; not reproduced here).
  comparator : RC 5.283 ms on v (exact first-order solution), trip 2.29801 V nominal / 2.20777 V low band edge (ovp_hw_params.h values).
               Sensitivity: RC 7.5 / 10 / 12.5 / 15 / 20 ms at the low band edge.
  ADC        : variant 'inst' = instantaneous 4 kSPS samples, limited at 4.99 V (ADC range at PC_SIG), 4:1 average to the 1 kHz reading;
               variant 'inst_noclip_none' = as 'inst' but with no ADC limit when v_sat = none (this is what the author's harness does);
               variant 'sinc3' = RC 2.37 kHz (3.05 kOhm x 22 nF = 67.1 us) on v, limited at 4.99 V, sinc3 (three cascaded 0.25 ms
               boxcars) sampled at 4 kSPS, 4:1 average. The 1 kHz reading at tick t averages the 4 samples at t - 0.75 .. t ms.
               Four ADC phases (0, 0.25, 0.5, 0.75 ms); per case the worst over phases is kept (max of peaks, earliest times, OR of trips).
  firmware   : reading >= 4.75 V counted (before E2 = IGNITION, HARD_START in v2.10); 2nd-order Butterworth 50 Hz at 1 kHz (scipy butter,
               bilinear with prewarp; filter started in steady state at the pre-light reading) on gauge Pa; 30 bar abs abort when the filtered
               absolute value is > 30e5 Pa on N consecutive ticks (N = 5 as built; 10 / 15 / 20 sensitivity); the longest consecutive run
               above 30 bar abs is recorded to size a ride-through.
  E2         : reference = mean of the pre-light readings in the last 20 ms; E2 at the 10th consecutive tick with filtered AND raw rise
               >= 0.8 bar and filtered AND raw >= 1.8 bar abs (config.h kIgnRise_Pa, kIgnFloorAbs_Pa base build, kIgnConfirmRelN).
Tags: SIM (reviewer chain) on COMB SIM histories. Not hardware evidence, not physical approval.
Usage: python -I rev_fa1_chain.py <fa1_envelope_v2p4a.json> <out_dir>
"""
import csv
import hashlib
import json
import os
import sys

import numpy as np
from scipy import signal

PAMB = 101325.0
FS_PA = 7.0e6
V_NOM = 0.5 + 4.0 * 3146517.6 / FS_PA
V_LO = 0.5 + 4.0 * (3146517.6 - 157925.8) / FS_PA
TAU_CMP = 0.005283
ADC_MAX = 4.99
V_HI = 4.75
P30 = 30.0e5
DT = 5e-6
PRE_S, END_S = 0.050, 0.100
N_PRE, N_END = int(round(PRE_S / DT)), int(round(END_S / DT))
T = np.arange(-N_PRE, N_END + 1) * DT
I0 = N_PRE                                    # index of t = 0
SUB = int(round(0.00025 / DT))                # 50 fine steps per ADC sample
TICK = 4 * SUB                                # 200 fine steps per 1 kHz tick
TAU_AA = 3.05e3 * 22e-9
CMP_SENS = (0.0075, 0.010, 0.0125, 0.015, 0.020)
PERS = (5, 10, 15, 20)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def foh_lag(u, tau, y0):
    """Exact first-order lag for an input that is linear between grid points; u shape (n_case, n_t)."""
    a = np.exp(-DT / tau)
    c = (tau / DT) * (1.0 - a)
    b = np.array([1.0 - c, c - a])
    den = np.array([1.0, -a])
    zi = signal.lfilter_zi(b, den)[None, :] * y0[:, None]
    y, _ = signal.lfilter(b, den, u, axis=1, zi=zi)
    return y


def boxcar_end(x, n):
    """Mean over the n samples ending at each index (first n-1 use the initial value)."""
    pad = np.concatenate([np.repeat(x[:, :1], n - 1, axis=1), x], axis=1)
    cs = np.cumsum(pad, axis=1)
    out = (cs[:, n - 1:] - np.concatenate([np.zeros((x.shape[0], 1)), cs[:, :-n]], axis=1)) / n
    return out


def run_chunk(P, tau_x, vsat, adc):
    """P: (n, nt) head pressure Pa abs on the fine grid. Returns per-phase dicts of per-case arrays."""
    n = P.shape[0]
    x = foh_lag(P, tau_x, P[:, 0])
    vraw = 0.5 + 4.0 * (x - PAMB) / FS_PA
    v = np.clip(vraw, 0.0, vsat) if np.isfinite(vsat) else np.maximum(vraw, 0.0)
    vc = foh_lag(v, TAU_CMP, v[:, 0])
    post = slice(I0, None)
    cmp_vmax = vc[:, post].max(axis=1)
    above_nom = vc[:, post] > V_NOM
    cmp_nom = above_nom.any(axis=1)
    t_cmp = np.where(cmp_nom, T[I0 + above_nom.argmax(axis=1)], np.nan)
    cmp_lo = (vc[:, post] > V_LO).any(axis=1)
    cmp_sens = {}
    for tr in CMP_SENS:
        vcs = foh_lag(v, tr, v[:, 0])
        cmp_sens[tr] = (vcs[:, post] > V_LO).any(axis=1)
    # ADC input
    if adc == 'sinc3':
        va = foh_lag(v, TAU_AA, v[:, 0])
        va = np.minimum(va, ADC_MAX)
        s = boxcar_end(boxcar_end(boxcar_end(va, SUB), SUB), SUB)
    elif adc == 'inst':
        s = np.minimum(v, ADC_MAX)
    elif adc == 'inst_noclip_none':
        s = v if not np.isfinite(vsat) else np.minimum(v, ADC_MAX)
    else:
        raise ValueError(adc)
    b, a = signal.butter(2, 50.0, fs=1000.0)
    res = []
    for ph in range(4):
        # 1 kHz ticks at t = ph*0.25 ms + j ms; reading = mean of samples at tick - 0.75, -0.5, -0.25, 0 ms
        first_tick = I0 + ph * SUB - (N_PRE // TICK) * TICK
        while first_tick - 3 * SUB < 0:
            first_tick += TICK
        ticks = np.arange(first_tick, len(T), TICK)
        rd = (s[:, ticks] + s[:, ticks - SUB] + s[:, ticks - 2 * SUB] + s[:, ticks - 3 * SUB]) / 4.0
        tt = T[ticks]
        raw_g = (rd - 0.5) / 4.0 * FS_PA
        zi = signal.lfilter_zi(b, a)[None, :] * raw_g[:, :1]
        filt_g, _ = signal.lfilter(b, a, raw_g, axis=1, zi=zi)
        raw_abs, filt_abs = raw_g + PAMB, filt_g + PAMB
        pre = (tt < 0) & (tt >= -0.0205)
        ref_r = raw_g[:, pre].mean(axis=1)
        ref_f = filt_g[:, pre].mean(axis=1)
        postk = tt >= 0
        ok = ((filt_g - ref_f[:, None]) >= 0.8e5) & ((raw_g - ref_r[:, None]) >= 0.8e5) & (filt_abs >= 1.8e5) & (raw_abs >= 1.8e5)
        ok &= postk[None, :]
        # E2 at the 10th consecutive ok tick
        cnt = np.zeros(n, dtype=int)
        e2_idx = np.full(n, -1)
        hi = (rd >= V_HI) & postk[None, :]
        n475 = hi.sum(axis=1)
        n475_ign = np.zeros(n, dtype=int)
        lit = np.zeros(n, dtype=bool)
        run30 = np.zeros(n, dtype=int)
        maxrun30 = np.zeros(n, dtype=int)
        t30 = np.zeros(n)
        tfw = {p: np.full(n, np.nan) for p in PERS}
        tlast30 = np.full(n, np.nan)
        for k in np.nonzero(postk)[0]:
            n475_ign += (hi[:, k] & ~lit)
            cnt = np.where(ok[:, k] & ~lit, cnt + 1, np.where(lit, cnt, 0))
            newly = (~lit) & (cnt >= 10)
            e2_idx = np.where(newly, k, e2_idx)
            lit |= newly
            a30 = filt_abs[:, k] > P30
            t30 += a30 * 1e-3
            tlast30 = np.where(a30, tt[k], tlast30)
            run30 = np.where(a30, run30 + 1, 0)
            maxrun30 = np.maximum(maxrun30, run30)
            for p in PERS:
                trip = (run30 >= p) & np.isnan(tfw[p])
                tfw[p] = np.where(trip, tt[k], tfw[p])
        t475 = np.where(n475 > 0, tt[np.argmax(hi, axis=1)], np.nan)
        tE2 = np.where(e2_idx >= 0, tt[np.clip(e2_idx, 0, None)], np.nan)
        res.append(dict(vmax=np.where(postk[None, :], rd, -np.inf).max(axis=1), n475=n475, n475_ign=n475_ign, t475=t475, tE2=tE2,
                        raw_pk=np.where(postk[None, :], raw_abs, -np.inf).max(axis=1),
                        filt_pk=np.where(postk[None, :], filt_abs, -np.inf).max(axis=1), t30f=t30, maxrun30=maxrun30, tlast30=tlast30,
                        **{'tfw%d' % p: tfw[p] for p in PERS}))
    # worst over phases
    w = {}
    for key in res[0]:
        arr = np.stack([r[key] for r in res])
        if key == 'tlast30':
            w[key] = np.nanmax(np.where(np.isnan(arr), -np.inf, arr), axis=0)
            w[key] = np.where(np.isinf(w[key]), np.nan, w[key])
        elif key.startswith('t') and key not in ('t30f',):
            w[key] = np.nanmin(np.where(np.isnan(arr), np.inf, arr), axis=0)
            w[key] = np.where(np.isinf(w[key]), np.nan, w[key])
        else:
            w[key] = arr.max(axis=0)
    w.update(cmp_vmax=cmp_vmax, cmp_nom=cmp_nom, t_cmp=t_cmp, cmp_lo=cmp_lo, port_pk=P[:, I0:].max(axis=1))
    for tr in CMP_SENS:
        w['cmp_lo_rc%g' % (tr * 1e3)] = cmp_sens[tr]
    return w


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(src))
    p0 = d['state']['P0_cold_flow_Pa']
    grid = np.array(d['history_grid_ms']) * 1e-3
    keys = list(d['cases'].keys())
    H = np.array([d['cases'][k]['P_head_hist_bar'] for k in keys]) * 1e5
    n_clip = int((H < p0).sum())
    H = np.maximum(H, p0)
    above45 = np.array([d['cases'][k]['above45_head_total_ms'] for k in keys])
    above45c = np.array([d['cases'][k]['above45_head_cont_ms'] for k in keys])
    peak = np.array([d['cases'][k]['peak_head_bar'] for k in keys])
    # fine-grid pressure
    tpos = np.clip(T, 0.0, grid[-1])
    P = np.empty((len(keys), len(T)))
    for i in range(len(keys)):
        P[i] = np.interp(tpos, grid, H[i])
    P[:, :I0] = H[:, :1]
    cfgs = []
    for tau in (0.0009, 0.0001):
        for vsat in (4.95, 4.74, 4.50, np.inf):
            for adc in ('inst', 'sinc3') + (('inst_noclip_none',) if not np.isfinite(vsat) else ()):
                cfgs.append((tau, vsat, adc))
    rows = []
    summary = []
    for tau, vsat, adc in cfgs:
        parts = []
        for c0 in range(0, len(keys), 112):
            parts.append(run_chunk(P[c0:c0 + 112], tau, vsat, adc))
        w = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        vs = 'none' if not np.isfinite(vsat) else '%.2f' % vsat
        fw5 = ~np.isnan(w['tfw5'])
        ign = w['n475_ign'] > 0
        anyab = ign | fw5 | w['cmp_nom']
        anylo = ign | fw5 | w['cmp_lo']
        first = []
        for i in range(len(keys)):
            c = []
            if ign[i]:
                c.append((w['t475'][i], 'over-range'))
            if w['cmp_nom'][i]:
                c.append((w['t_cmp'][i], 'comparator'))
            if fw5[i]:
                c.append((w['tfw5'][i], 'firmware'))
            first.append(min(c)[1] if c else 'none')
        fc = {k: first.count(k) for k in ('firmware', 'comparator', 'over-range', 'none')}
        s = dict(tau_x_ms=tau * 1e3, vsat=vs, adc=adc, n=len(keys), any_abort_nominal=int(anyab.sum()), any_abort_low_band=int(anylo.sum()),
                 first_path=fc, fw30_5ms=int(fw5.sum()), fw30_10ms=int((~np.isnan(w['tfw10'])).sum()),
                 fw30_15ms=int((~np.isnan(w['tfw15'])).sum()), fw30_20ms=int((~np.isnan(w['tfw20'])).sum()),
                 cmp_nom=int(w['cmp_nom'].sum()), cmp_lo=int(w['cmp_lo'].sum()),
                 **{'cmp_lo_rc%gms' % (tr * 1e3): int(w['cmp_lo_rc%g' % (tr * 1e3)].sum()) for tr in CMP_SENS},
                 reading_ge_4p75=int((w['n475'] > 0).sum()), reading_ge_4p75_before_E2=int(ign.sum()),
                 max_consecutive_readings_ge_4p75=int(w['n475'].max()),
                 vmax_V=round(float(w['vmax'].max()), 4), raw_pk_max_bar=round(float(w['raw_pk'].max()) / 1e5, 3),
                 filt_pk_max_bar=round(float(w['filt_pk'].max()) / 1e5, 3), filt_t30_total_ms_max=round(float(w['t30f'].max()) * 1e3, 1),
                 filt_t30_longest_run_ms_max=int(w['maxrun30'].max()), cmp_vmax_V=round(float(w['cmp_vmax'].max()), 4),
                 E2_ms_range=[round(float(np.nanmin(w['tE2'])) * 1e3, 2), round(float(np.nanmax(w['tE2'])) * 1e3, 2)],
                 no_E2=int(np.isnan(w['tE2']).sum()),
                 overrange_after_E2=int(((w['n475'] > 0) & ~ign).sum()),
                 fw30_trip_after_E2=int(np.nansum((w['tfw5'] > w['tE2']))),
                 t_last_filt_above30_ms_max=round(float(np.nanmax(w['tlast30'])) * 1e3, 1),
                 t_last_filt_above30_minus_E2_ms_max=round(float(np.nanmax(w['tlast30'] - w['tE2'])) * 1e3, 1))
        summary.append(s)
        for i in range(len(keys)):
            rows.append([i, keys[i], '%g' % (tau * 1e3), vs, adc, '%.4f' % (w['port_pk'][i] / 1e5), '%.4f' % w['vmax'][i], int(w['n475'][i]),
                         int(w['n475_ign'][i]), '%.2f' % (w['tE2'][i] * 1e3) if not np.isnan(w['tE2'][i]) else '-1',
                         '%.4f' % (w['raw_pk'][i] / 1e5), '%.4f' % (w['filt_pk'][i] / 1e5), '%.1f' % (w['t30f'][i] * 1e3), int(w['maxrun30'][i]),
                         int(fw5[i]), int(not np.isnan(w['tfw10'][i])), int(not np.isnan(w['tfw15'][i])), '%.4f' % w['cmp_vmax'][i],
                         int(w['cmp_nom'][i]), int(w['cmp_lo'][i]), int(w['cmp_lo_rc10'][i]), int(w['cmp_lo_rc20'][i]), first[i],
                         '%.3f' % above45[i], '%.3f' % above45c[i], '%.3f' % peak[i],
                         '%.1f' % (w['tfw5'][i] * 1e3) if not np.isnan(w['tfw5'][i]) else '-1', '%.1f' % (w['tlast30'][i] * 1e3) if not np.isnan(w['tlast30'][i]) else '-1'])
        print('tau %.1f ms vsat %-4s adc %-16s any %3d/%3d first %s | fw5/10/15/20 %3d/%3d/%3d/%3d | >=4.75 %3d (ign %3d) | cmp nom/lo %3d/%3d '
              'lo RC7.5/10/12.5/15/20 %s | filt pk %.2f t30 %.1f run %d | raw pk %.2f vmax %.3f | E2 %s' % (
                  tau * 1e3, vs, adc, s['any_abort_nominal'], s['any_abort_low_band'], fc, s['fw30_5ms'], s['fw30_10ms'], s['fw30_15ms'],
                  s['fw30_20ms'], s['reading_ge_4p75'], s['reading_ge_4p75_before_E2'], s['cmp_nom'], s['cmp_lo'],
                  [s['cmp_lo_rc%gms' % (tr * 1e3)] for tr in CMP_SENS], s['filt_pk_max_bar'], s['filt_t30_total_ms_max'],
                  s['filt_t30_longest_run_ms_max'], s['raw_pk_max_bar'], s['vmax_V'], s['E2_ms_range']), flush=True)
    with open(os.path.join(out, 'rev_fa1_cases.csv'), 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['i', 'key', 'tau_x_ms', 'vsat', 'adc', 'head_pk_bar', 'vmax_V', 'n475', 'n475_ign', 'tE2_ms', 'raw_pk_bar', 'filt_pk_bar',
                     't30f_ms', 'longest_run30_ms', 'fw30_5', 'fw30_10', 'fw30_15', 'cmp_vmax', 'cmp_nom', 'cmp_lo', 'cmp_lo_rc10',
                     'cmp_lo_rc20', 'first_path', 'above45_head_total_ms', 'above45_head_cont_ms', 'peak_head_bar', 't_fw30_5ms_trip_ms', 't_last_filt_above30_ms'])
        wr.writerows(rows)
    meta = dict(id='rev_elec2_fa1_chain', reviewer='REV-ELEC-2', source=src, source_sha256_16=sha16(src), P0_cold_flow_Pa=p0,
                samples_limited_to_P0=n_clip, n_cases=len(keys), script_sha256_16=sha16(os.path.abspath(__file__)),
                above45_head_total_ms_max=float(above45.max()), above45_head_cont_ms_max=float(above45c.max()),
                tags='SIM (reviewer chain) on COMB SIM histories; not hardware evidence, not physical approval', summary=summary)
    json.dump(meta, open(os.path.join(out, 'rev_fa1_summary.json'), 'w'), indent=1)
    print('samples limited to P0:', n_clip, '| above45 head total max %.3f ms, cont max %.3f ms' % (above45.max(), above45c.max()))


if __name__ == '__main__':
    main()
