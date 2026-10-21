"""LC-TB70 envelope v2 in pressure-time form (Mechanical, 2026-10-21): lead brief 2026-10-21T08:05:00Z F6 + F3 (REV-COMB-4 interim (f)(ii),
MAJOR) and F4, and the lead's 08:39:41Z items 2 and 3 (REV-COMB-4 final, REVIEW-COMBUSTION-R4.md 2908321d7f75d439: R4-02 MAJOR, R4-10 and
section 5 (f)(ii)).  v1 (855ebe04dfe5dbd0, json 6f710726e4787134) is kept as lc_tb70_envelope_v1.py.  DERIVED from the analysed cases and
the Combustion v2.4b FA-1 grid (SIM on an ASSUMED construct; grid counts are not probabilities; the grid data are unchanged in v2.4c,
interfaces/combustion.json 661db0a593462382, whose fa1_grid_statistics_v2p4c records Z3' as OPEN and fa1_p_torch_v2p4c the R4-01 text);
margins are the published tables (negatives SHOWN AS FOUND).  Not physical approval.  Import-safe: inside_v2() and esp_max() can be
imported without running the checks.

WHAT CHANGES IN v2
(1) Z3 RESTATED (R4-02).  The FA-1 head peaks above the v1 ceiling 75.519 bar abs are physical SIM bracket cases (46 of 896, maximum 88.02;
    REV-COMB-4).  A higher ceiling with the v1 shape limits does not bound the structure (88.1 with <= 3.0 ms above 63.1 and a >= 0.8 ms rise
    admits ESP 171.45 bar abs > FA1S 151.04), and no tighter time / rise / ceiling limits both admit the grid and bound the ESP (option 2
    below, with numbers).  Z3 v2 is REV-COMB-4's Z3' AS WRITTEN plus the two v1 shape conditions kept as the FA-1 class:
      Z3 v2:  63.1 < P_head <= 88.1 bar abs, AND
              S(T) <= 151.04 bar abs (FA1S) at every period T in 0.02-50 ms (the published 406-period grid), AND
              the window from the first to the last crossing of 63.1 bar abs <= 3.0 ms, AND the 10-90 % rise of the first rise to the
              peak >= 0.8 ms (both kept from v1; every grid case meets them, so the grid classification equals Z3' exactly).
    S(T) = 1.01325 + max_t x(t), x'' + (2 pi / T)^2 x = (2 pi / T)^2 g(t), undamped, x = x' = 0 at the record start (before the light,
    chamber at ambient or below), g = P_head - 1.01325 bar piecewise linear between samples and held at its last value after the record
    (its free vibration added); S = the larger of g clipped at 0 and g unclipped: the Combustion v2.4b 16.2 / REV-COMB-4 convention,
    reproduced here on the 896 grid histories.
    THE RECORD (what a post-run check evaluates; the grid's own form): one light's head-end pressure from before the light (first sample
    at or below 2.0 bar abs; grid records start at 0.05-1.07 bar abs; a start above ambient adds at most 2 (P0 - 1.01325) bar, conservative)
    with S evaluated on the LIGHT WINDOW, from the record start to 150 ms after the first crossing of 8 bar abs (the LIGHT_SPIKE start),
    held after it.  Every grid record ends 61-129 ms after that crossing, so the grid evaluation is the published convention exactly; the
    window keeps an undamped SDOF from integrating a whole burn's sustained oscillation (an undamped resonance grows without bound over a
    long record).  Z3 exists only inside the light window: the FA1S rows are solved at the FA-1 thermal state of a light (45.6 C); a head
    above 63.1 bar abs later in a run is outside the envelope.  Sample step <= 0.05 ms (the grid's own) over the window.
    Period domain 0.02-50 ms (REV-COMB-4's, ADOPTED; not the brief's 0.005-2000 ms) because it is the domain a post-run check can
    evaluate and the only one where the bound can bind (numbers in 'grid_reproduction' and 'Z3_v2'): (a) the grid comes within 50 bar of
    FA1S only inside 0.02-50 ms (periods listed); (b) below 0.02 ms S -> the peak (quasi-static limit; the excess over the 88.02 peak is the
    unclipped from-rest start below ambient), bounded by the 88.1 ceiling; (c) above 50 ms S tends to 1.01325 + 2 x (the level held) plus
    the pulse impulse term, which the zone rules bound (grid and plateau / burn-on families in this file, far below FA1S); (d) the
    signal: B-DPC-1 (stand, 51.2 kS/s, flat to >= 10 kHz incl. the mount, AC coupled -3 dB 0.5 Hz) resolves T >= 0.1 ms and, DC-restored
    with C1 (the first-order coupling inverted, pre-light level from C1), the long end; 0.02-0.1 ms is beyond its flat band and is
    evaluated as recorded (piecewise linear), which does not bind (grid well below FA1S there, the >= 0.8 ms 10-90 % rise keeping the
    dynamic factor there <= 1.032 for a linear rise); SIL plant traces (25 us step) resolve all of it; the flight 1 kHz record cannot
    (Z3 v2 NOT EVALUATED in flight: the LIGHT_SPIKE raw peak is a lower bound).
    MEASURED TRACES: an undamped oscillator has no loss, so on a measured trace S integrates the trace noise over the window (a coherent
    tone of amplitude a at the period T adds about a pi N, N the cycles of T in the window: 135 a at 3.5 ms and 942 a at 0.5 ms over
    150 ms; white noise adds a response growing with the square root of the window; 'noise_sensitivity_measured_traces').  The test is
    exact on SIM traces (the grid, the SIL S6R / N-04 plant traces) and conservative on measured ones: the stand use needs a no-event
    B-DPC-1 record through inside_v2 first (TO-VERIFY); a damped variant (published v2.4b head|all|zeta0.02 envelope 142.62 bar abs at
    3.425 ms against 146.88 undamped) needs the structure's damping shown (MISSING) and is OPEN for the lead, not adopted.
(2) J-FWD REPLACE RULE RESTATED (F3, R4-10, 5 (f)(ii)).  The level stays 60.0 bar abs; the quantity and its basis change:
      quantity  Q_JFWD = max(the head peak over the record, max over T in 0.2-0.5 ms of S(T) on the light window and on each
                excursion window: 50 ms before to 150 ms after an upward crossing of 45 bar abs later in the run, SDOF from
                equilibrium at its start): the J-FWD sees the peak quasi-statically through the parts and the J-FWD band dynamically
                through the screws (TC-02 head on its screws 0.272-0.385 ms, v3.5 S-AX modal, mechanical.json /fa1/periods_and_dlf,
                CHANGELOG 176; the v3.5.2 ten IN718 screws shorten it by about 13 %: band 0.2-0.5 ms ASSUMED, TO-VERIFY);
      level     60.0 bar abs: the highest head pressure at which every J-FWD row meets the nominal factors at the LC2 thermal state
                (78.6 C) on an FE state: the yield slot 1.5 x 6.0 = 9.0 MPa IS js5b LC2U (SF 1.0 on the factored state, lead R7 form),
                every row positive (TC-01 +0.328, TC-02 +1.362, screw +1.583); the ultimate slot 2.0 x 6.0 = 12.0 MPa is FA1D 12.1 MPa
                (45.6 C, +0.355) and, at 78.6 C, the TC-01 ligament trend +0.312 [DERIVED]; above 60 bar abs the J-FWD has only SF 1.0
                rows (FA1D / FA1U / FA1S: the line-231 one-off abnormal basis, Neuber local strain, 233 (4) replace);
      duration  none: one exceedance at any time in the run;
      count     298 of the 896 FA-1 grid cases (the peak alone, the v1 quantity and LEAD 256 (4): 185; the 113 added cases peak at
                49.8-60.0 bar abs with J-FWD-band ESP above 60) [SIM grid counts on an ASSUMED construct, not rates of normal lights];
      signal    stand: B-DPC-1 DC-restored with C1 (step <= 0.05 ms in the windows), C1 for the peak elsewhere; SIL: the plant head
                pressure; flight: the C1 LIGHT_SPIKE raw peak (1 kHz) is a lower bound, so Electronics states the flight threshold from
                its C1 chain model on the 896 grid (TO-VERIFY), this file giving the ideal-sampler bound.
    NOT meant for normal-light transients: a normal light stays in Z0 (head <= MEOP 45 bar abs, the LC2 basis) and a smooth rise to
    45 bar abs gives Q_JFWD far below 60 (numbers in 'jfwd_rule_v2'); Q_JFWD > 60 marks a light that loaded the J-FWD beyond its 60 bar
    abs basis, an abnormal event by the structural basis whatever its cause.  The grid counts are FA-1 hard-start bracket cases (A1
    fuel-assisted relight), SIM on an ASSUMED construct, not a rate of normal lights (R4-10).
(3) F4: the TB-state abort set HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START is CONFIRMED, with PC_SENSOR raised on the HIGH side and
    OVER_TEMP (F-14) beside it; the trace rule (2) covers the ridden-through events (block 'F4_abort_set').
(4) The v1 cases are re-checked with inside_v2(); the v3.5.2 margin matrix (rows v8 publication) replaces the v3.5.1 per-zone record
    (kept beside).
inside_v2(t_s, p_bar_abs) is the post-run classifier (one light's record from before the light to the end of that burn); it is
import-safe and cross-checked here on grid cases against the vectorised grid evaluation.
UNCHANGED from v1: Z0 (<= 45, LC2, SF 1.5 / 2.0), Z1 (45-58.1, LC-TB70, 1.5 / 2.0), Z2 (58.1-63.1, LC-TB-S, abnormal 1.0 / 1.5),
P <= 45 bar abs later than 300 ms after the first crossing of 45, the purge tail, the quasi-static basis of Z0-Z2.
"""
import csv, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np

PA = 1.01325                                   # bar abs, the gauge reference of the convention
MEOP, P_TB70, P_TBS = 45.0, 58.1, 63.1
P_FA1_V1, P_Z3 = 75.519, 88.1                  # v1 Z3 ceiling; v2 ceiling (grid peak 88.02 rounded up, REV-COMB-4 Z3')
P_FA1S = 151.04                                # FA1S = DLF 2.0 x 75.519 (FEA3D step 15.104 MPa), the bound for every period (230 (2))
T_EVENT, T_WIN63, TR_FA1 = 0.300, 0.0030, 0.0008
P_JFWD_RULE = 60.0
JFWD_BAND_MS = (0.2, 0.5)
Z3_DOMAIN_MS = (0.02, 50.0)
DT_MAX_S = 5.0e-5                              # a trace qualifies for the Z3 ESP test with a sample step <= 0.05 ms
DT_TOL = 1.001                                 # +0.1 % on the step check (float32-stored times: grid steps 0.04998-0.05001 ms)
P_PRE, P_LIGHT = 2.0, 8.0                      # record start at or below 2.0 bar abs (before the light); the light = first crossing of 8 bar abs (LIGHT_SPIKE start)
T_LIGHT_WIN = 0.150                            # light window: record start to 150 ms after the light (grid records end 61-129 ms after it)
T_EXC_PRE, T_EXC_POST = 0.050, 0.150           # excursion window around a later upward crossing of 45 bar abs (Q_JFWD only)
TWO_PI = 2.0 * math.pi


def periods_z3_ms():
    """The published 406-period grid 0.02-50 ms (fa1_pressure_spectra_published_v2p4b.csv), generated."""
    a = np.round(np.arange(0.02, 1.0 + 1e-9, 0.005), 6)
    b = np.round(np.arange(1.0, 5.0 + 1e-9, 0.025), 6)
    c = np.round(5.0 * 10.0 ** (np.arange(41) / 40.0), 4)
    d = np.array([6.0, 7.5, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0])
    return np.unique(np.concatenate([a, b, c, d]))


def esp_max(t, G, periods_ms, u0=None):
    """Exact maximum response.  t (nt,) common sample times [s] or (nr, nt) per-row times, strictly increasing; G (nr, nt) loads [bar];
    periods [ms].  x'' + w^2 x = w^2 g, undamped, g piecewise linear between samples and held at G[:, -1] after the last one; x(t0) = u0
    (default 0), x'(t0) = 0.  Inside a step x(tau) = g0 + s tau + R cos(w tau - phi); its interior maxima are at
    w tau = phi + asin(s / (R w)) + 2 pi k (the first and last k in the step are evaluated, s tau being monotone); after the record
    x <= g_end + sqrt((x - g_end)^2 + (x'/w)^2).  Returns (nr, np) max over [t0, inf) of x (the start value included)."""
    t = np.asarray(t, float); G = np.asarray(G, float)
    w = TWO_PI / (np.asarray(periods_ms, float) * 1e-3)[None, :]
    nr, nt = G.shape
    u = np.zeros((nr, w.shape[1])) if u0 is None else np.repeat(np.asarray(u0, float).reshape(nr, 1), w.shape[1], axis=1)
    v = np.zeros_like(u)
    um = u.copy()
    per_row = t.ndim == 2
    if per_row:
        assert t.shape == G.shape
        dts = np.diff(t, axis=1)
    else:
        dts = np.diff(t)
    assert np.all(dts > 0)
    last = None
    for i in range(nt - 1):
        if per_row:
            dt = dts[:, i:i + 1]
            wdt = w * dt
            cw, sw = np.cos(wdt), np.sin(wdt)
        else:
            dt = float(dts[i])
            if last is None or dt != last[0]:
                wdt = w * dt
                last = (dt, wdt, np.cos(wdt), np.sin(wdt))
            _, wdt, cw, sw = last
        g0 = G[:, i:i + 1]
        s = (G[:, i + 1:i + 2] - g0) / dt
        C = u - g0
        D = (v - s) / w
        u_n = g0 + s * dt + C * cw + D * sw
        v_n = s + w * (D * cw - C * sw)
        R = np.hypot(C, D)
        with np.errstate(divide="ignore", invalid="ignore"):
            q = s / (R * w)
        ok = np.isfinite(q) & (np.abs(q) < 1.0)
        qq = np.where(ok, q, 0.0)
        ph = np.arctan2(D, C) + np.arcsin(qq)
        amp = R * np.sqrt(1.0 - qq * qq)
        for k in (np.ceil(-ph / TWO_PI - 1e-12), np.floor((wdt - ph) / TWO_PI + 1e-12)):
            tau = (ph + TWO_PI * k) / w
            good = ok & (tau >= 0.0) & (tau <= dt)
            np.maximum(um, np.where(good, g0 + s * tau + amp, -np.inf), out=um)
        np.maximum(um, u_n, out=um)
        u, v = u_n, v_n
    ge = G[:, -1:]
    np.maximum(um, ge + np.sqrt((u - ge) ** 2 + (v / w) ** 2), out=um)
    return um


def esp_spectrum(t, p, periods_ms, x0="rest"):
    """S(T) [bar abs] of one record by the convention: larger of g clipped at 0 and g unclipped; x0 'rest' (x = 0 at the record start,
    the published convention, for a record from before the light) or 'equilibrium' (x = g(t0): a window cut from a steady state)."""
    p = np.asarray(p, float)
    rows = [np.maximum(p - PA, 0.0)]
    if p.min() < PA:
        rows.append(p - PA)
    G = np.vstack(rows)
    u0 = G[:, 0] if x0 == "equilibrium" else None
    return PA + esp_max(t, G, periods_ms, u0=u0).max(axis=0)


def _cross_first(t, p, lev, i_end):
    idx = np.nonzero(p[:i_end + 1] >= lev)[0]
    if len(idx) == 0:
        return None
    j = int(idx[0])
    if j == 0:
        return float(t[0])
    return float(t[j - 1] + (lev - p[j - 1]) / (p[j] - p[j - 1]) * (t[j] - t[j - 1]))


def rise_10_90_s(t, p):
    """10-90 % rise of the first rise to the peak, levels between p(t0) and the peak, first crossings interpolated (REV-COMB-4
    r4_fa1_envelope_stats definition)."""
    ip = int(np.argmax(p)); pk = float(p[ip]); p0 = float(p[0])
    if pk <= p0:
        return None
    t10, t90 = _cross_first(t, p, p0 + 0.1 * (pk - p0), ip), _cross_first(t, p, p0 + 0.9 * (pk - p0), ip)
    return t90 - t10


def time_above_s(t, p, lev):
    """total time with p > lev, crossings interpolated (REV-COMB-4 definition)"""
    a = np.asarray(p, float) - lev
    a0, a1, dt = a[:-1], a[1:], np.diff(t)
    tot = dt[(a0 > 0) & (a1 > 0)].sum()
    dn = (a0 > 0) & (a1 <= 0); up = (a1 > 0) & (a0 <= 0)
    tot += (dt[dn] * a0[dn] / (a0[dn] - a1[dn])).sum() + (dt[up] * a1[up] / (a1[up] - a0[up])).sum()
    return float(tot)


def window_above_s(t, p, lev):
    """v1 measure: from the first to the last crossing of lev (interpolated); 0 if never above"""
    p = np.asarray(p, float); t = np.asarray(t, float)
    idx = np.nonzero(p > lev)[0]
    if len(idx) == 0:
        return 0.0
    i0, i1 = int(idx[0]), int(idx[-1])
    ta = t[i0] if i0 == 0 else t[i0 - 1] + (lev - p[i0 - 1]) / (p[i0] - p[i0 - 1]) * (t[i0] - t[i0 - 1])
    tb = t[i1] if i1 == len(p) - 1 else t[i1] + (p[i1] - lev) / (p[i1] - p[i1 + 1]) * (t[i1 + 1] - t[i1])
    return float(tb - ta)


def _cut(t, p, ta, tb):
    """the record on [ta, tb], end points interpolated; tb beyond the record holds the last value (as the ESP engine does)"""
    m = (t > ta) & (t < tb)
    tw = np.concatenate([[ta], t[m], [tb]])
    pw = np.concatenate([[float(np.interp(ta, t, p))], p[m], [float(np.interp(tb, t, p))]])
    keep = np.concatenate([[True], np.diff(tw) > 1e-15])
    return tw[keep], pw[keep]


def _up_crossings(t, p, lev):
    """interpolated times of the upward crossings of lev (p[i-1] <= lev < p[i])"""
    i = np.nonzero((p[:-1] <= lev) & (p[1:] > lev))[0] + 1
    return t[i - 1] + (lev - p[i - 1]) / (p[i] - p[i - 1]) * (t[i] - t[i - 1])


def _resolves(t, ta, tb):
    m = (t >= ta - 1e-12) & (t <= tb + 1e-12)
    tt = t[m]
    if len(tt) < 2:
        return False
    return float(np.max(np.diff(tt))) <= DT_MAX_S * DT_TOL and tt[0] <= ta + DT_MAX_S * DT_TOL and (tt[-1] >= min(tb, t[-1]) - DT_MAX_S * DT_TOL)


def inside_v2(t, p):
    """LC-TB70 v2 classification of one light's head-end pressure record: t [s], p [bar abs], from before the light (first sample at or
    below P_PRE 2.0 bar abs) to the end of that burn.  Rules (module docstring, LC-TB70 v2):
      zones Z0-Z2 and the 300 ms rule as v1 (P > 45 bar abs later than 300 ms after the record's first crossing of 45 is outside);
      Z3: 63.1 < P <= 88.1 bar abs only inside the LIGHT WINDOW (record start to 150 ms after the first crossing of 8 bar abs), the
          window from the first to the last crossing of 63.1 <= 3.0 ms, the 10-90 % rise of the first rise to the peak >= 0.8 ms, and
          S(T) <= 151.04 bar abs at the 406 periods 0.02-50 ms, S on the light window from rest at the record start, held after it;
      Q_JFWD = max(the record's peak, S(T) at 0.2-0.5 ms on the light window and on each EXCURSION WINDOW: 50 ms before to 150 ms after
          an upward crossing of 45 bar abs later than the light window, from equilibrium at its start); the J-FWD rule flag is
          Q_JFWD > 60.0 bar abs.
    A window needs a sample step <= 0.05 ms; where it has not, the ESP is not evaluated: a Z3 record returns inside None (unless another
    rule fails) and Q_JFWD only its lower bound (the peak).  Returns a dict (inside, zone_max, reasons, ESP maximum and period, Q_JFWD,
    jfwd_rule_triggered and the window details)."""
    t = np.asarray(t, float); p = np.asarray(p, float)
    assert t.ndim == 1 and t.shape == p.shape and np.all(np.diff(t) > 0)
    reasons, out = [], {}
    pk = float(p.max())
    zone = 3 if pk > P_TBS else 2 if pk > P_TB70 else 1 if pk > MEOP else 0
    out.update({"zone_max": zone, "peak_bar_abs": round(pk, 3)})
    a45 = np.nonzero(p > MEOP)[0]
    if len(a45):
        t0 = t[a45[0]]
        late = np.nonzero((p > MEOP) & (t - t0 > T_EVENT))[0]
        if len(late):
            reasons.append(f"P {p[late[0]]:.2f} > MEOP {MEOP} bar abs at tau {(t[late[0]] - t0) * 1e3:.1f} ms > {T_EVENT * 1e3:.0f} ms")
    if pk > P_Z3:
        reasons.append(f"peak {pk:.2f} > {P_Z3} bar abs (Z3 v2 ceiling)")
    starts_before_light = float(p[0]) <= P_PRE
    out["record_starts_before_light"] = starts_before_light
    j8 = np.nonzero(p >= P_LIGHT)[0]
    if len(j8) == 0:
        t8 = None; tw_end = float(t[-1])
    else:
        k = int(j8[0])
        t8 = float(t[0]) if k == 0 else float(t[k - 1] + (P_LIGHT - p[k - 1]) / (p[k] - p[k - 1]) * (t[k] - t[k - 1]))
        tw_end = t8 + T_LIGHT_WIN
    out["light_window_s"] = [float(t[0]), round(tw_end, 6)]
    if zone == 3:
        if np.any((p > P_TBS) & (t > tw_end)):
            reasons.append(f"head above {P_TBS} bar abs later than {T_LIGHT_WIN * 1e3:.0f} ms after the light (no Z3 basis outside the light window)")
        win = window_above_s(t, p, P_TBS)
        out["window_above_63p1_ms"] = round(win * 1e3, 4)
        if win > T_WIN63 + 1e-12:
            reasons.append(f"window above {P_TBS} bar abs {win * 1e3:.3f} ms > {T_WIN63 * 1e3:.1f} ms")
        r = rise_10_90_s(t, p)
        out["rise_10_90_ms"] = None if r is None else round(r * 1e3, 4)
        if r is not None and r < TR_FA1 - 1e-12:
            reasons.append(f"Z3 10-90 % rise {r * 1e3:.3f} ms < {TR_FA1 * 1e3:.1f} ms")
    PZ = periods_z3_ms()
    band = (PZ >= JFWD_BAND_MS[0] - 1e-9) & (PZ <= JFWD_BAND_MS[1] + 1e-9)
    light_ok = starts_before_light and _resolves(t, float(t[0]), tw_end)
    out["light_window_evaluable"] = light_ok
    q_parts, q_known = [pk], True
    if light_ok:
        tw, pw = _cut(t, p, float(t[0]), tw_end)
        S = esp_spectrum(tw, pw, PZ, x0="rest")
        j = int(np.argmax(S))
        out["S_max_0p02_50ms_bar_abs"] = round(float(S[j]), 3); out["S_max_at_T_ms"] = float(PZ[j])
        q_parts.append(float(S[band].max()))
        if zone == 3 and S[j] > P_FA1S:
            reasons.append(f"Z3 ESP {S[j]:.2f} > FA1S {P_FA1S} bar abs at T {PZ[j]} ms")
    else:
        q_known = False
        if not starts_before_light:
            out["light_window_note"] = f"record starts at {float(p[0]):.2f} bar abs > {P_PRE} (not from before the light): ESP not evaluated"
    exc = []
    for tc in _up_crossings(t, p, MEOP):
        if tc <= tw_end:
            continue
        ta, tb = max(float(t[0]), tc - T_EXC_PRE), tc + T_EXC_POST
        if _resolves(t, ta, tb):
            tw, pw = _cut(t, p, ta, tb)
            Sb = esp_spectrum(tw, pw, PZ[band], x0="equilibrium")
            exc.append({"t_cross_s": round(float(tc), 6), "S_band_max_bar_abs": round(float(Sb.max()), 3)})
            q_parts.append(float(Sb.max()))
        else:
            exc.append({"t_cross_s": round(float(tc), 6), "S_band_max_bar_abs": None})
            q_known = False
    out["excursion_windows"] = exc
    q = max(q_parts)
    if q_known:
        out["Q_JFWD_bar_abs"] = round(q, 3); out["jfwd_rule_triggered"] = bool(q > P_JFWD_RULE)
    else:
        out["Q_JFWD_bar_abs"] = None; out["Q_JFWD_lower_bound_bar_abs"] = round(q, 3)
        out["jfwd_rule_triggered"] = True if q > P_JFWD_RULE else None
    z3_needs_esp = zone == 3 and not light_ok
    inside = (False if reasons else None) if z3_needs_esp else (not reasons)
    out.update({"inside": inside, "reasons": reasons})
    return out


# ============================================================================================================== checks and results
def main():
    T_START = time.time()
    HUBE = Path("/home/claude/work/shared-fallback/engine")
    MECH = Path("/home/claude/work/mechanical/v352")
    TB = MECH / "tb70"
    OUT = TB / "lc_tb70_envelope_v2.json"
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    R4D = HUBE / "reviews/combustion/r4"
    INP = {"fa1_histories_npz": (HUBE / "02-combustion/data/v2p4b/fa1_histories_solver_v2p4b.npz", "399bf43d1c09de24"),
           "fa1_spectra_published_csv": (HUBE / "02-combustion/data/v2p4b/fa1_pressure_spectra_published_v2p4b.csv", "a2c380515cada638"),
           "REVIEW-COMBUSTION-R4": (HUBE / "reviews/REVIEW-COMBUSTION-R4.md", "2908321d7f75d439"),
           "MANIFEST_REV-COMB-4": (R4D / "MANIFEST_REV-COMB-4.sha256", "996475830cae731f"),
           "r4_fa1_spectrum_json": (R4D / "r4_fa1_spectrum.json", "403efc7d3788a903"),
           "r4_fa1_envelope_stats_json": (R4D / "r4_fa1_envelope_stats.json", "9a4f010f2fd37049"),
           "r4_z3_pulse_check_json": (R4D / "r4_z3_pulse_check.json", "8807b744c7e3b74b"),
           "js5b_rows": (HUBE / "04-fea/assembly3d_v352/results/v352/jfwd_js5b_rows_v352.json", "91278d6b039c5b27"),
           "rows_v8": (MECH / "jfwd/jfwd_in718_rows_v352_v8.json", "af072cc2e70711ca"),
           "fix_v2": (MECH / "jfwd/jfwd_fix_v352_v2.json", "760d6c6f2d7d46d5"),
           "tapwall_v3": (MECH / "jfwd/jfwd_tapwall_v352_v3.json", "ef70572ec92b05b0"),
           "envelope_v1_json": (TB / "lc_tb70_envelope_v1.json", "6f710726e4787134"),
           "envelope_v1_py": (TB / "lc_tb70_envelope_v1.py", "855ebe04dfe5dbd0"),
           "margin_matrix_v352": (HUBE / "04-fea/assembly3d_v352_rows_v8/tables/margin_matrix_v352.json", "6c694fa7147fb511"),
           "sax_v351_L1_csv": (HUBE / "04-fea/structural/results/sax_margin_table_L1_thv351_TB1GC_cad351_v1.csv", "eb16a0d8ed8a2455"),
           "engmat": (MECH / "engine/04-fea/src/engmat.py", "d41807bf675951b1"),
           "electronics_json": (HUBE / "interfaces/electronics.json", "11f7896ad0d0613b"),
           "combustion_json_v2p4c": (HUBE / "interfaces/combustion.json", "661db0a593462382")}
    for k, (p, s16) in INP.items():
        assert sha(p) == s16, (k, p, sha(p))
    HUBCOPY = {"rows_v8": HUBE / "04-fea/v352/jfwd_in718_rows_v352_v8.json", "fix_v2": HUBE / "04-fea/v352/jfwd_fix_v352_v2.json",
               "envelope_v1_json": HUBE / "04-fea/v352/lc_tb70_envelope_v1.json", "envelope_v1_py": HUBE / "04-fea/v352/lc_tb70_envelope.py"}
    for k, hp in HUBCOPY.items():
        assert sha(hp) == INP[k][1], ("hub copy differs", k)
    sys.path.insert(0, str(MECH / "engine/04-fea/src"))
    import engmat
    al = lambda key, T: engmat.prop("AL6061-T6", key, T) / 1e6
    V1 = json.loads(INP["envelope_v1_json"][0].read_text())
    R4S = json.loads(INP["r4_fa1_spectrum_json"][0].read_text())
    R4E = json.loads(INP["r4_fa1_envelope_stats_json"][0].read_text())
    R4Z = json.loads(INP["r4_z3_pulse_check_json"][0].read_text())
    JS = json.loads(INP["js5b_rows"][0].read_text())
    R8 = json.loads(INP["rows_v8"][0].read_text())
    FX = json.loads(INP["fix_v2"][0].read_text())
    TW3 = json.loads(INP["tapwall_v3"][0].read_text())
    MM = json.loads(INP["margin_matrix_v352"][0].read_text())
    EL = json.loads(INP["electronics_json"][0].read_text())
    assert V1["version"] == "v1" and R8["version"] == "v8" and FX["version"] == "v2" and TW3["version"] == "v3"
    CB = json.loads(INP["combustion_json_v2p4c"][0].read_text())
    Z3P = ("Z3': head peak <= 88.1 bar abs AND undamped SDOF ESP of the head history <= 151.04 bar abs at every period 0.02-50 ms "
           "(every FA-1 grid case meets it: max 146.88 at 3.5 ms)")
    assert CB["version"] == "v2.4c" and CB["fa1_grid_statistics_v2p4c"]["v"]["proposed_Z3_prime"] == Z3P
    assert CB["fa1_grid_statistics_v2p4c"]["v"]["cases_above_all_896"] == [46, 141, 185] and CB["fa1_grid_statistics_v2p4c"]["v"]["status"].startswith("OPEN")
    assert CB["fa1_p_torch_v2p4c"]["v"]["design_case"] == TW3["R4-01_additions"]["(c)_P_torch_statement_verbatim_REV-COMB-4"].rstrip(".")   # v2.4c without the final stop
    res = {"id": "lc_tb70_envelope", "version": "v2", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
           "status": "DERIVED from the analysed structural cases and the Combustion v2.4b FA-1 grid (SIM on an ASSUMED construct; grid counts are not probabilities); margins are the published tables, negatives SHOWN AS FOUND; not physical approval",
           "inputs": {k: {"path": str(p), "sha256_16": s16} for k, (p, s16) in INP.items()},
           "supersedes": "lc_tb70_envelope_v1.json 6f710726e4787134 (script 855ebe04dfe5dbd0, kept as lc_tb70_envelope_v1.py)"}

    # ---------------------------------------------------------------------------------------------- 1. self-tests of the SDOF engine
    st = {}
    dtt = 5e-5
    tt = np.arange(0.0, 0.2 + 1e-12, dtt)
    Tt = np.array([0.05, 0.1, 0.5, 2.0, 8.0, 20.0, 50.0])
    step = np.where(tt > 0, 1.0, 0.0)[None, :]
    m = esp_max(tt, step, Tt)[0]
    xr = np.pi * dtt / (Tt * 1e-3)
    ref = 1.0 + np.abs(np.sin(xr)) / xr
    st["ramp_step_0.05ms_rise"] = {"T_ms": Tt.tolist(), "value": m.round(6).tolist(), "analytic_1_plus_abs_sin_x_over_x": ref.round(6).tolist(),
                                   "max_rel_err": float(np.max(np.abs(m / ref - 1.0)))}

    def ramp_resp(tg, t0, k, w):
        tau = np.maximum(tg - t0, 0.0)
        return k * (tau - np.sin(w * tau) / w)
    tb = np.array([0.0, 0.7e-3, 3.1e-3, 4.3e-3])                      # trapezoid 0 -> 1 in 0.7 ms, hold, 1 -> 0 in 1.2 ms, then held at 0
    gb = np.array([[0.0, 1.0, 1.0, 0.0]])
    Tq = np.array([0.03, 0.2, 0.9, 2.5, 6.0, 15.0, 40.0])
    mq = esp_max(tb, gb, Tq)[0]
    tf = np.arange(0.0, 0.12, 2e-7)
    refq = []
    for T in Tq:
        w = TWO_PI / (T * 1e-3)
        x = (ramp_resp(tf, 0.0, 1 / 0.7e-3, w) - ramp_resp(tf, 0.7e-3, 1 / 0.7e-3, w) - ramp_resp(tf, 3.1e-3, 1 / 1.2e-3, w)
             + ramp_resp(tf, 4.3e-3, 1 / 1.2e-3, w))
        refq.append(float(x.max()))
    refq = np.array(refq)
    st["trapezoid_breakpoints_only_vs_superposition_on_0.2us"] = {"T_ms": Tq.tolist(), "value": mq.round(6).tolist(), "reference": refq.round(6).tolist(),
                                                                  "max_rel_err": float(np.max(np.abs(mq / refq - 1.0)))}
    assert st["ramp_step_0.05ms_rise"]["max_rel_err"] < 1e-9, st
    assert st["trapezoid_breakpoints_only_vs_superposition_on_0.2us"]["max_rel_err"] < 2e-5, st
    res["selftest"] = st
    print("selftest", {k: v["max_rel_err"] for k, v in st.items()}, flush=True)

    # ---------------------------------------------------------------------------------------------- 2. the 896 grid histories
    PZ = periods_z3_ms()
    pub = list(csv.DictReader(open(INP["fa1_spectra_published_csv"][0])))
    P_pub = np.array([float(r["period_ms"]) for r in pub])
    assert len(PZ) == 406 and np.allclose(PZ, P_pub, atol=5e-5), "generated period grid != published"
    P_short = np.array([0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175])
    P_long = np.geomspace(50.0, 2000.0, 31)[1:]
    P_ALL = np.concatenate([P_short, P_pub, P_long])
    iZ = np.arange(len(P_short), len(P_short) + len(P_pub))
    iS, iL = np.arange(len(P_short)), np.arange(len(P_short) + len(P_pub), len(P_ALL))
    band = iZ[(P_pub >= JFWD_BAND_MS[0] - 1e-9) & (P_pub <= JFWD_BAND_MS[1] + 1e-9)]
    band01 = iZ[(P_pub >= 0.1 - 1e-9) & (P_pub <= 1.0 + 1e-9)]
    Z = np.load(INP["fa1_histories_npz"][0])
    keys = [str(k) for k in Z["case_keys"]]; off = Z["offsets"]
    assert len(keys) == 896
    nt = int(np.diff(off).max())
    rows_t, rows_g, row_case = [], [], []
    per = []
    dt_dev = 0.0
    for i, k in enumerate(keys):
        a, b = int(off[i]), int(off[i + 1])
        t = Z["t_s"][a:b].astype(float); p = Z["P_head_bar"][a:b].astype(float)
        dt_dev = max(dt_dev, float(np.max(np.abs(t - 5e-5 * np.arange(b - a)))))
        assert np.all(np.diff(t) > 0) and np.max(np.diff(t)) <= DT_MAX_S * DT_TOL
        tp = np.empty(nt); tp[:len(t)] = t; tp[len(t):] = t[-1] + 5e-5 * np.arange(1, nt - len(t) + 1)   # padding held (as REV-COMB-4)
        cand = [np.maximum(p - PA, 0.0)] + ([p - PA] if p.min() < PA else [])
        for g in cand:
            gp = np.empty(nt); gp[:len(g)] = g; gp[len(g):] = g[-1]
            rows_t.append(tp); rows_g.append(gp); row_case.append(i)
        ip = int(np.argmax(p))
        r = rise_10_90_s(t, p)
        s1k = [float(p[ph::20].max()) for ph in range(20)]
        rd, ent, of, tf_, tr_, pool = k.split("|")
        per.append({"case": k, "peak": float(p[ip]), "t_peak_ms": float(t[ip] * 1e3), "p0": float(p[0]), "rise_10_90_ms": r * 1e3,
                    "ms_above": {f"{lev}": time_above_s(t, p, lev) * 1e3 for lev in (45.0, 58.1, 60.0, 63.1, 75.519, 88.1)},
                    "window_above_63p1_ms": window_above_s(t, p, P_TBS) * 1e3,
                    "ideal_1kHz_sampled_max_worst_phase": min(s1k), "ideal_1kHz_sampled_max_best_phase": max(s1k),
                    "baseline": rd == "vapour_once" and ent == "rounded_Cd1.0" and int(float(of[2:])) >= 4, "as_written": rd == "as_written", "OF": of})
    TG = np.vstack(rows_t); GG = np.vstack(rows_g); row_case = np.array(row_case)
    print("grid rows", GG.shape, "periods", len(P_ALL), "max stored-time deviation from k x 0.05 ms", dt_dev, flush=True)
    U = np.zeros((GG.shape[0], len(P_ALL)))
    CH = 64
    for j0 in range(0, len(P_ALL), CH):
        U[:, j0:j0 + CH] = esp_max(TG, GG, P_ALL[j0:j0 + CH])
        print(f"  periods {j0}-{min(j0 + CH, len(P_ALL))} {time.time() - T_START:.0f} s", flush=True)
    S = np.full((896, len(P_ALL)), -np.inf)
    for r_, i in enumerate(row_case):
        S[i] = np.maximum(S[i], PA + U[r_])
    env = S.max(axis=0); arg = S.argmax(axis=0)
    jz = iZ[int(np.argmax(env[iZ]))]
    d_pub = env[iZ] - np.array([float(r["head|all|zeta0"]) for r in pub])
    base_idx = [i for i, c in enumerate(per) if c["baseline"]]
    d_pub_b = S[base_idx][:, iZ].max(axis=0) - np.array([float(r["head|baseline|zeta0"]) for r in pub])
    rep = {"published_head_all_zeta0_max_abs_diff_bar": round(float(np.max(np.abs(d_pub))), 4),
           "published_head_baseline_zeta0_max_abs_diff_bar": round(float(np.max(np.abs(d_pub_b))), 4),
           "grid_max_0p02_50ms": {"S_bar_abs": round(float(env[jz]), 3), "T_ms": float(P_ALL[jz]), "case": keys[int(arg[jz])]},
           "reviewer_r4_fa1_spectrum": {"head_max": R4S["FA1S_check"]["head_max"], "argmax": R4S["FA1S_check"]["head_argmax"]},
           "below_0p02ms_max": round(float(env[iS].max()), 3), "T_50_2000ms_max": round(float(env[iL].max()), 3),
           "stored_time_max_deviation_from_k_x_0p05ms_s": dt_dev, "time_base": "the stored per-case times (as REV-COMB-4 r4_fa1_spectrum.py), padded at 0.05 ms with the last value held",
           "T_le_0p1ms_max_published_grid": round(float(env[iZ][P_pub <= 0.1 + 1e-9].max()), 3),
           "periods_where_grid_within_50bar_of_FA1S_ms": [float(P_pub[env[iZ] >= P_FA1S - 50.0].min()), float(P_pub[env[iZ] >= P_FA1S - 50.0].max())] if np.any(env[iZ] >= P_FA1S - 50.0) else None,
           "periods_where_grid_within_25bar_of_FA1S_ms": [float(P_pub[env[iZ] >= P_FA1S - 25.0].min()), float(P_pub[env[iZ] >= P_FA1S - 25.0].max())] if np.any(env[iZ] >= P_FA1S - 25.0) else None}
    assert rep["published_head_all_zeta0_max_abs_diff_bar"] < 0.01 and rep["published_head_baseline_zeta0_max_abs_diff_bar"] < 0.01, rep
    assert abs(rep["grid_max_0p02_50ms"]["S_bar_abs"] - R4S["FA1S_check"]["head_max"]) < 0.005 and rep["grid_max_0p02_50ms"]["T_ms"] == 3.5
    res["grid_reproduction"] = rep
    print("reproduction", json.dumps(rep), flush=True)

    # per-case results
    for i, c in enumerate(per):
        sz = S[i, iZ]; jj = int(np.argmax(sz))
        c["S_max_0p02_50ms"] = float(sz[jj]); c["S_max_T_ms"] = float(P_pub[jj])
        c["S_max_below_0p02ms"] = float(S[i, iS].max()); c["S_max_50_2000ms"] = float(S[i, iL].max())
        c["S_jfwd_band_0p2_0p5ms"] = float(S[i, band].max()); c["S_band_0p1_1ms"] = float(S[i, band01].max())
        c["Q_JFWD"] = max(c["peak"], c["S_jfwd_band_0p2_0p5ms"])
        c["v1_inside"] = not (c["peak"] > P_FA1_V1 or (c["peak"] > P_TBS and (c["window_above_63p1_ms"] > 3.0 or c["rise_10_90_ms"] < 0.8)))
        c["z3prime_inside"] = c["peak"] <= P_Z3 and c["S_max_0p02_50ms"] <= P_FA1S
        c["v2_inside"] = c["z3prime_inside"] and not (c["peak"] > P_TBS and (c["window_above_63p1_ms"] > 3.0 or c["rise_10_90_ms"] < 0.8))
    # reviewer's statistics reproduced (same definitions)
    A = [c for c in per]
    ab63 = [c for c in A if c["peak"] > P_TBS]; ab75 = [c for c in A if c["peak"] > P_FA1_V1]; ab60 = [c for c in A if c["peak"] > 60.0]
    stats = {"n_peak_above_75.519_63.1_60": [len(ab75), len(ab63), len(ab60)],
             "reviewer_r4": [R4E["all"]["n_peak_above_75.519"], R4E["all"]["n_peak_above_63.1"], R4E["all"]["n_peak_above_60.0"]],
             "above_63p1_ms_above_63p1_max_total": round(max(c["ms_above"]["63.1"] for c in ab63), 4),
             "above_63p1_window_63p1_max_v1_measure": round(max(c["window_above_63p1_ms"] for c in ab63), 4),
             "above_63p1_rise_10_90_min_ms": round(min(c["rise_10_90_ms"] for c in ab63), 4),
             "above_75p519_ms_above_75p519_max": round(max(c["ms_above"]["75.519"] for c in ab75), 4),
             "peak_max": round(max(c["peak"] for c in A), 3),
             "reviewer_r4_values": {"ms_above_63p1_max": R4E["all"]["above_63.1"]["ms_above_63p1_max"], "rise_min": R4E["all"]["above_63.1"]["rise_10_90_ms_min"],
                                    "ms_above_75p519_max": R4E["all"]["above_75.519"]["ms_above_75p519_max"], "peak_max": R4E["all"]["peak_max"]}}
    assert stats["n_peak_above_75.519_63.1_60"] == stats["reviewer_r4"] == [46, 141, 185], stats
    assert abs(max(c["ms_above"]["63.1"] for c in ab63) - R4E["all"]["above_63.1"]["ms_above_63p1_max"]) < 1e-6
    assert abs(min(c["rise_10_90_ms"] for c in ab63) - R4E["all"]["above_63.1"]["rise_10_90_ms_min"]) < 1e-6
    assert abs(max(c["ms_above"]["75.519"] for c in ab75) - R4E["all"]["above_75.519"]["ms_above_75p519_max"]) < 1e-6
    res["grid_statistics_reproduced"] = stats
    # inside_v2 (the post-run classifier Electronics imports) against the vectorised grid evaluation
    sel = sorted(set([i for i, c in enumerate(per) if c["peak"] > P_FA1_V1]
                     + [int(i) for i in np.argsort([-c["S_max_0p02_50ms"] for c in per])[:8]] + list(range(0, 896, 89))))
    xc_max = {"S": 0.0, "Q": 0.0}
    for i in sel:
        a, b = int(off[i]), int(off[i + 1])
        o = inside_v2(Z["t_s"][a:b].astype(float), Z["P_head_bar"][a:b].astype(float))
        c = per[i]
        assert o["light_window_evaluable"] and o["record_starts_before_light"] and not o["excursion_windows"], (c["case"], o)
        dS, dQ = abs(o["S_max_0p02_50ms_bar_abs"] - c["S_max_0p02_50ms"]), abs(o["Q_JFWD_bar_abs"] - c["Q_JFWD"])
        xc_max["S"], xc_max["Q"] = max(xc_max["S"], dS), max(xc_max["Q"], dQ)
        assert dS < 1.5e-3 and dQ < 1.5e-3 and o["inside"] == c["v2_inside"] and o["jfwd_rule_triggered"] == (c["Q_JFWD"] > P_JFWD_RULE), (c["case"], o, dS, dQ)
        assert o["light_window_s"][1] >= float(Z["t_s"][b - 1]) - 1e-9          # the light window covers the whole grid record
    res["inside_v2_cross_check_on_grid"] = {"n_cases": len(sel), "selection": "the 46 cases above 75.519, the 8 highest ESP, every 89th case",
                                            "max_abs_diff_S_bar": round(xc_max["S"], 5), "max_abs_diff_Q_JFWD_bar": round(xc_max["Q"], 5),
                                            "inside_and_jfwd_flag_agree": True}
    print("inside_v2 cross-check", json.dumps(res["inside_v2_cross_check_on_grid"]), flush=True)

    def grp(sel):
        n = len(sel)
        return {"n": n, "peak_max": round(max(c["peak"] for c in sel), 3), "S_max_0p02_50ms": round(max(c["S_max_0p02_50ms"] for c in sel), 3),
                "n_v1_inside": sum(c["v1_inside"] for c in sel), "n_z3prime_inside": sum(c["z3prime_inside"] for c in sel),
                "n_v2_inside": sum(c["v2_inside"] for c in sel),
                "n_Q_JFWD_above_60": sum(c["Q_JFWD"] > 60.0 for c in sel), "n_peak_above_60": sum(c["peak"] > 60.0 for c in sel),
                "n_S_band_above_60": sum(c["S_jfwd_band_0p2_0p5ms"] > 60.0 for c in sel)}
    groups = {"all": grp(A), "baseline": grp([c for c in A if c["baseline"]]), "as_written": grp([c for c in A if c["as_written"]]),
              "vapour_once": grp([c for c in A if not c["as_written"]])}
    print("groups", json.dumps(groups), flush=True)

    # ---------------------------------------------------------------------------------------------- 3. Z3 v2 against the grid
    margin = P_FA1S - max(c["S_max_0p02_50ms"] for c in A)
    pos = sorted(A, key=lambda c: -c["S_max_0p02_50ms"])[:8]
    res["Z3_v2"] = {
        "criterion": {"zone": [P_TBS, P_Z3], "ceiling_bar_abs": P_Z3, "ESP_bound_bar_abs": P_FA1S, "period_domain_ms": list(Z3_DOMAIN_MS),
                      "period_grid": "the published 406 periods (periods_z3_ms(): 0.02-1.0 step 0.005, 1.0-5.0 step 0.025, 5-50 at 40 per decade plus 6 / 7.5 / 10 / 12.5 / 15 / 20 / 25 / 30 / 40 / 50)",
                      "window_above_63p1_max_ms": T_WIN63 * 1e3, "rise_10_90_min_ms": TR_FA1 * 1e3,
                      "convention": "S(T) = 1.01325 + max x, undamped SDOF from rest at the record start (before the light), g = P - 1.01325 bar piecewise linear between samples, held at its last value after the record (free vibration added), the larger of g clipped at 0 and g unclipped (Combustion v2.4b 16.2 / REV-COMB-4)",
                      "record": "one light's head-end pressure from before the light (first sample at or below 2.0 bar abs) to the end of that burn; S on the LIGHT WINDOW (record start to 150 ms after the first crossing of 8 bar abs), from rest at the record start, held after the window; Z3 only inside the light window (a head above 63.1 bar abs later in a run is outside the envelope: the FA1S rows are solved at the FA-1 thermal state of a light, 45.6 C); every grid record ends 61-129 ms after the light, so the grid evaluation is the published convention exactly",
                      "trace_requirement": "sample step <= 0.05 ms over the light window: B-DPC-1 (51.2 kS/s, DC-restored with C1) on the stand; the SIL plant head pressure (25 us) for S6R / N-04; the flight 1 kHz record does not qualify (NOT EVALUATED); exact on SIM traces, conservative on measured ones, where the undamped test integrates the trace noise (noise_sensitivity_measured_traces: a no-event stand record is checked first, TO-VERIFY)",
                      "why_a_window": "an undamped SDOF integrates without loss: over a whole burn a sustained oscillation at a structural period (for example a chamber acoustic mode in the 0.2-0.5 ms J-FWD band) grows without bound in the computed response, which a structure with any damping does not do; the window keeps the evaluation to the light transient, the form in which the grid and FA1S were set",
                      "adoption": "REV-COMB-4 Z3' ADOPTED AS WRITTEN (ceiling 88.1, ESP <= 151.04 at 0.02-50 ms) plus the v1 window (<= 3.0 ms above 63.1) and rise (>= 0.8 ms) conditions KEPT as the FA-1 class; every grid case meets both kept conditions, so the grid classification equals Z3' exactly"},
        "why_the_kept_conditions": {"rise_10_90_ge_0p8ms": f"the stand trace (B-DPC-1, flat to >= 10 kHz) does not resolve 0.02-0.1 ms, where the S-AX modal bands sit (TC-01 shell breathing 0.053-0.075 ms, TC-04 bonnet 0.044-0.062 ms; mechanical.json /fa1/periods_and_dlf, v3.5 S-AX modal); for a linear rise of >= 1.0 ms (10-90 % >= 0.8 ms) the dynamic factor there is <= 1 + T / (pi t_r) <= 1.032, so the unresolved band stays near the peak (grid <= {rep['T_le_0p1ms_max_published_grid']} bar abs at T <= 0.1 ms) [DERIVED]",
                                    "window_63p1_le_3p0ms": "keeps a Z3 event a pulse at a light: the FA1S rows (J-FWD included) are solved at the FA-1 thermal state (45.6 C) for a one-off pulse (line 231 (1)); a sustained Z3 level passes the ESP test (e.g. 70 bar abs held: S about 139 bar abs) but is not an analysed thermal / strain state"},
        "grid": {"n_inside_v2": groups["all"]["n_v2_inside"], "n_inside_z3prime": groups["all"]["n_z3prime_inside"], "n_inside_v1": groups["all"]["n_v1_inside"],
                 "S_max_bar_abs": round(max(c["S_max_0p02_50ms"] for c in A), 3), "margin_to_FA1S_bar": round(margin, 3),
                 "worst_cases": [{"case": c["case"], "S_max": round(c["S_max_0p02_50ms"], 3), "T_ms": c["S_max_T_ms"], "peak": round(c["peak"], 3)} for c in pos],
                 "window_above_63p1_max_ms": stats["above_63p1_window_63p1_max_v1_measure"], "rise_10_90_min_ms": stats["above_63p1_rise_10_90_min_ms"],
                 "below_0p02ms_max": rep["below_0p02ms_max"], "T_50_2000ms_max": rep["T_50_2000ms_max"], "groups": groups,
                 "tag": "DERIVED on the SIM grid (ASSUMED construct); counts are grid counts, not probabilities"}}
    assert groups["all"]["n_v2_inside"] == groups["all"]["n_z3prime_inside"] == 896

    # ---------------------------------------------------------------------------------------------- 4. option 2: shape limits (families)
    PD = np.unique(np.concatenate([np.geomspace(0.02, 50.0, 2400), P_pub]))
    PDL = np.geomspace(50.0, 2000.0, 61)

    def trap(peak, tr_full, t_above, lev=P_TBS):
        A_ = peak - PA
        frac = (lev - PA) / A_
        hold = max(t_above - 2.0 * (1.0 - frac) * tr_full, 0.0)
        if hold < 1e-9:
            return np.array([0.0, tr_full, 2 * tr_full]), np.array([[0.0, A_, 0.0]]), 0.0
        return np.array([0.0, tr_full, tr_full + hold, 2 * tr_full + hold]), np.array([[0.0, A_, A_, 0.0]]), hold

    def smax(t, G, periods=PD):
        m = PA + esp_max(t, G, periods)[0]
        j = int(np.argmax(m))
        return float(m[j]), float(periods[j])

    fam = {}
    for pk, lim in ((P_FA1_V1, 3.0e-3), (P_Z3, 3.0e-3), (P_Z3, 1.7e-3), (P_Z3, 1.0e-3)):
        t, G, hold = trap(pk, 1.0e-3, lim)
        v, Tm = smax(t, G)
        rv = R4Z["cases"][f"peak{pk}_tabove63p1_{lim * 1e3:.1f}ms"]
        fam[f"peak{pk}_tabove63p1_{lim * 1e3:.1f}ms_rise0.8"] = {"hold_ms": round(hold * 1e3, 4), "ESP_max_bar_abs": round(v, 2), "at_T_ms": round(Tm, 3),
                                                                 "reviewer_r4_z3_pulse_check": rv["max_ESP_bar_abs"], "above_FA1S": v > P_FA1S}
        assert v >= rv["max_ESP_bar_abs"] - 0.02, (pk, lim, v, rv)        # a denser period grid can only find a higher maximum
    # (a) time-above-63.1 limit at the 88.1 ceiling and a 0.8 ms (10-90) rise that keeps the trapezoid at FA1S
    def f_time(ta):
        t, G, _ = trap(P_Z3, 1.0e-3, ta)
        return smax(t, G)[0]
    lo, hi = 2.0 * (1.0 - (P_TBS - PA) / (P_Z3 - PA)) * 1.0e-3, 3.0e-3
    v_lo = f_time(lo)
    if v_lo > P_FA1S:
        ta_lim = None
    else:
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if f_time(mid) <= P_FA1S else (lo, mid)
        ta_lim = lo
    # (b) ceiling at the v1 shape limits (3.0 ms above 63.1, 0.8 ms rise) that keeps the trapezoid at FA1S
    def f_peak(pk):
        t, G, _ = trap(pk, 1.0e-3, 3.0e-3)
        return smax(t, G)[0]
    lo2, hi2 = 63.2, P_Z3
    for _ in range(40):
        mid = 0.5 * (lo2 + hi2)
        lo2, hi2 = (mid, hi2) if f_peak(mid) <= P_FA1S else (lo2, mid)
    # (c) at the grid's own extremes (peak 88.02, 1.669 ms above 63.1): every admissible rise
    pk_g, ta_g, r_g = stats["peak_max"], stats["above_63p1_ms_above_63p1_max_total"] * 1e-3, stats["above_63p1_rise_10_90_min_ms"] * 1e-3
    tr_max = ta_g / (2.0 * (1.0 - (P_TBS - PA) / (pk_g - PA)))           # zero hold
    rise_scan = []
    for tr10 in np.linspace(r_g, 0.8 * tr_max, 12):
        t, G, hold = trap(pk_g, tr10 / 0.8, ta_g)
        v, Tm = smax(t, G)
        rise_scan.append({"rise_10_90_ms": round(tr10 * 1e3, 4), "hold_ms": round(hold * 1e3, 4), "ESP_max": round(v, 2), "T_ms": round(Tm, 3)})
    corner_v, corner_T = smax(*trap(pk_g, r_g / 0.8, ta_g)[:2])
    # the 10-90 % rise a trapezoid at the grid's peak and time above would need to stay within FA1S (information)
    def f_rise(tr10):
        t, G, _ = trap(pk_g, tr10 / 0.8, ta_g)
        return smax(t, G)[0]
    rlo, rhi = r_g, 0.8 * tr_max
    if f_rise(rhi) > P_FA1S:
        rise_needed = None
    else:
        for _ in range(40):
            mid = 0.5 * (rlo + rhi)
            rlo, rhi = (rlo, mid) if f_rise(mid) <= P_FA1S else (mid, rhi)
        rise_needed = rhi
    opt2 = {"trapezoid_family_reviewer_reproduced": fam,
            "smallest_shape_limit_box_admitting_the_grid": {"ceiling_bar_abs": pk_g, "time_above_63p1_max_ms": round(ta_g * 1e3, 4), "rise_10_90_min_ms": round(r_g * 1e3, 4)},
            "corner_trapezoid_ESP_bar_abs": round(corner_v, 2), "corner_trapezoid_at_T_ms": round(corner_T, 3),
            "time_limit_at_88.1_rise0.8_for_FA1S": None if ta_lim is None else round(ta_lim * 1e3, 4),
            "time_limit_note": "zero-hold triangle already above FA1S" if ta_lim is None else "a time-above-63.1 limit at or below this value keeps every symmetric trapezoid at 88.1 / 0.8 ms rise within FA1S",
            "grid_needs_time_above_63p1_ms": stats["above_63p1_ms_above_63p1_max_total"],
            "ceiling_at_v1_shape_limits_for_FA1S_bar_abs": round(lo2, 3), "grid_needs_ceiling_bar_abs": stats["peak_max"],
            "rise_needed_at_grid_peak_and_time_above_ms": None if rise_needed is None else round(rise_needed * 1e3, 4), "grid_has_rise_down_to_ms": round(r_g * 1e3, 4),
            "rise_scan_at_grid_extremes_peak_88.02_1.669ms_above_63.1": rise_scan,
            "verdict": None}
    assert corner_v > P_FA1S
    opt2["verdict"] = (f"OPTION 2 DOES NOT WORK: the smallest time / rise / ceiling box that admits every grid case (ceiling {pk_g}, time above 63.1 bar abs <= "
                       f"{round(ta_g * 1e3, 3)} ms, 10-90 % rise >= {round(r_g * 1e3, 3)} ms) admits the symmetric trapezoid at its corner with ESP {round(corner_v, 2)} bar abs "
                       f"(T {round(corner_T, 3)} ms) > FA1S 151.04; keeping trapezoids within FA1S needs a time above 63.1 of at most "
                       f"{opt2['time_limit_at_88.1_rise0.8_for_FA1S']} ms at 88.1 / 0.8 ms (the grid needs {opt2['grid_needs_time_above_63p1_ms']}), or a ceiling of "
                       f"{opt2['ceiling_at_v1_shape_limits_for_FA1S_bar_abs']} bar abs at the v1 limits (the grid needs {opt2['grid_needs_ceiling_bar_abs']}), or a 10-90 % rise of at least "
                       f"{opt2['rise_needed_at_grid_peak_and_time_above_ms']} ms at the grid's peak and time above (the grid has {round(r_g * 1e3, 3)} ms); the grid passes only because its "
                       f"shapes are not trapezoids, which the ESP test states directly [DERIVED; trapezoid family ASSUMED as one admissible shape]")
    res["option_2_shape_limits"] = opt2
    res["option_3_higher_FA1S"] = {"needed_for_the_88.1_v1_shape_trapezoid_bar_abs": fam[f"peak{P_Z3}_tabove63p1_3.0ms_rise0.8"]["ESP_max_bar_abs"],
                                   "status": "NOT IN THIS PACKAGE: a higher FA1S needs a new FE step set (no new FE run in this brief); not proposed"}
    print("option 2", json.dumps({k: v for k, v in opt2.items() if k not in ("rise_scan_at_grid_extremes_peak_88.02_1.669ms_above_63.1", "trapezoid_family_reviewer_reproduced")}), flush=True)

    # ---------------------------------------------------------------------------------------------- 5. plateau / burn-on families (v1 admitted)
    def v1_pulse(peak, t_on=0.0, dt=1e-5):
        q = (MEOP - PA) / (peak - PA)
        tr = TR_FA1 / 0.8
        tau = (T_WIN63 - tr * (1.0 - q)) / (-math.log(q))                 # v1 fa1_pulse: 3.0 ms above 45 bar abs
        n = int(round(0.06 / dt))
        t = t_on + dt * np.arange(n)
        x = np.where(t - t_on <= tr, (t - t_on) / tr, np.exp(-(t - t_on - tr) / tau))
        return t, PA + (peak - PA) * x, tr, tau

    def build(peak, plateau, t_plat_end, after, ramp=1e-3):
        """pulse from ambient (v1 fa1_pulse shape); with a plateau: max(pulse, plateau) after the peak, the plateau ending so that a linear
        'ramp' reaches 'after' 0.1 ms before tau = t_plat_end (tau from the first 45 bar abs crossing); burn-on (plateau None): the pulse
        decays to 'after'.  The record ends there and is held at its last value (the ESP engine holds it and adds the free vibration)."""
        t, p, tr, tau = v1_pulse(peak)
        t45 = tr * (MEOP - PA) / (peak - PA)
        ip = int(np.argmax(p))
        if plateau is not None:
            p = np.where(np.arange(len(p)) > ip, np.maximum(p, plateau), p)
            te = t45 + t_plat_end - ramp - 1e-4
            assert te > t[-1] and abs(p[-1] - plateau) < 1e-9
            keep = t < te
            t = np.concatenate([t[keep], [te, te + ramp]]); p = np.concatenate([p[keep], [plateau, after]])
        else:
            assert np.any(p[ip:] <= after) and after < p[ip]
            j = ip + int(np.argmax(p[ip:] <= after))                     # first sample after the peak at or below the burn-on level
            tc = t[j - 1] + (p[j - 1] - after) / (p[j - 1] - p[j]) * (t[j] - t[j - 1])
            t, p = np.concatenate([t[:j], [tc]]), np.concatenate([p[:j], [after]])   # the rise from ambient kept; the decay ends at the level
        assert abs(p[0] - PA) < 1e-12
        return t, p

    def resample(t, p, dt=DT_MAX_S):
        tr_ = np.arange(0.0, t[-1] + 1e-12, dt)
        if tr_[-1] < t[-1] - 1e-12:
            tr_ = np.append(tr_, t[-1])
        return tr_, np.interp(tr_, t, p)

    pf = {}
    for name, pk, plat, tend, after in (("v1 pulse 75.519 + Z2 plateau 63.1 to tau 300 ms + MEOP 45 held", P_FA1_V1, P_TBS, T_EVENT, MEOP),
                                        ("pulse 88.1 + Z2 plateau 63.1 to tau 300 ms + MEOP 45 held", P_Z3, P_TBS, T_EVENT, MEOP),
                                        ("v1 pulse 75.519 + 48 bar plateau to tau 200 ms + 40 held (v1 S6 family)", P_FA1_V1, 48.0, 0.200, 40.0),
                                        ("pulse 88.1 + burn-on at MEOP 45 held (N-04 bound)", P_Z3, None, None, MEOP),
                                        ("pulse 88.1 + burn-on at 30 bar abs held (N-04 at the 30 bar abort level)", P_Z3, None, None, 30.0)):
        t, p = build(pk, plat, tend, after)
        ins = inside_v2(*resample(t, p))
        G = np.vstack([np.maximum(p - PA, 0.0)])
        mz = PA + esp_max(t, G, PD)[0]; ml = PA + esp_max(t, G, PDL)[0]
        jz_, jl_ = int(np.argmax(mz)), int(np.argmax(ml))
        bnd = (PD >= 0.2 - 1e-9) & (PD <= 0.5 + 1e-9)
        pf[name] = {"peak": round(float(p.max()), 3), "ESP_max_0p02_50ms": round(float(mz[jz_]), 2), "at_T_ms": round(float(PD[jz_]), 3),
                    "ESP_max_50_2000ms": round(float(ml[jl_]), 2), "at_T_long_ms": round(float(PDL[jl_]), 1),
                    "Q_JFWD": round(max(float(p.max()), float(mz[bnd].max())), 2),
                    "v1_inside": None, "v2_inside": ins["inside"], "v2_reasons": ins["reasons"],
                    "v2_on_0p05ms_resample": {k: ins.get(k) for k in ("S_max_0p02_50ms_bar_abs", "S_max_at_T_ms", "Q_JFWD_bar_abs", "jfwd_rule_triggered", "window_above_63p1_ms", "rise_10_90_ms")}}
        # v1 classification with the v1 function (copied semantics: v1 inside())
        rs = []
        a45 = np.nonzero(p > MEOP)[0]; t0 = t[a45[0]]
        if p.max() > P_FA1_V1 + 1e-9: rs.append("peak > 75.519")
        if np.any((p > MEOP) & (t - t0 > T_EVENT)): rs.append("P > 45 after 300 ms")
        th = t[p > P_TBS]
        if len(th) and th[-1] - th[0] > T_WIN63: rs.append("> 63.1 for more than 3.0 ms")
        pf[name]["v1_inside"] = not rs; pf[name]["v1_reasons"] = rs
    res["plateau_and_burn_on_families"] = {"construction": "v1 fa1_pulse shape (linear rise 1.0 ms from ambient = 0.8 ms 10-90, exponential decay with 3.0 ms above 45 bar abs at the v1 peak construction), "
                                           "then max(pulse, plateau) after the peak, a 1 ms ramp reaching the level after 0.1 ms before tau = the plateau end (tau from the first 45 bar abs crossing), held (burn-on: the pulse decays to the level, held); "
                                           "sampled at 10 us, ESP on 2400 log periods 0.02-50 ms plus the published 406 and 61 log periods 50-2000 ms; inside_v2 on the 0.05 ms resample; ESP clipped convention from rest [ASSUMED shapes, DERIVED response]",
                                           "cases": pf,
                                           "reading": None}
    for name, v in pf.items():
        s_res = v["v2_on_0p05ms_resample"]["S_max_0p02_50ms_bar_abs"]
        assert s_res is not None and s_res <= v["ESP_max_0p02_50ms"] + 0.05, (name, v)        # published 406 periods on the resample <= the dense grid
    _rd = []
    for name, v in pf.items():
        _rd.append(f"{name}: ESP {v['ESP_max_0p02_50ms']} bar abs at {v['at_T_ms']} ms ({'<=' if v['ESP_max_0p02_50ms'] <= P_FA1S else '>'} FA1S), "
                   f"50-2000 ms {v['ESP_max_50_2000ms']}, Q_JFWD {v['Q_JFWD']}; v1 {'inside' if v['v1_inside'] else 'outside (' + '; '.join(v['v1_reasons']) + ')'}, "
                   f"v2 {'inside' if v['v2_inside'] else 'outside (' + '; '.join(v['v2_reasons']) + ')' if v['v2_inside'] is False else 'not evaluated'}")
    res["plateau_and_burn_on_families"]["reading"] = (" | ".join(_rd) + ". The long-period ESP is the held level's step factor about 2 plus the pulse; every family stays "
                                                     + ("below" if all(v["ESP_max_0p02_50ms"] <= P_FA1S for v in pf.values()) else "NOT below") + " FA1S at 0.02-50 ms [ASSUMED shapes, DERIVED response]")
    print("families", json.dumps({k: (v["ESP_max_0p02_50ms"], v["ESP_max_50_2000ms"], v["Q_JFWD"], v["v1_inside"], v["v2_inside"]) for k, v in pf.items()}), flush=True)

    # ---------------------------------------------------------------------------------------------- 6. v1 cases re-checked with inside_v2
    def square(p_peak, t_above, dt=0.0005):
        t, p, k = [], [], 0
        while k * dt <= t_above + 0.002:
            tt_ = k * dt
            if tt_ < 0.0005:
                pp = MEOP + (p_peak - MEOP) * tt_ / 0.0005
            elif tt_ <= t_above - 0.0005:
                pp = p_peak
            elif tt_ <= t_above:
                pp = p_peak - (p_peak - MEOP) * (tt_ - (t_above - 0.0005)) / 0.0005
            else:
                pp = 40.0
            t.append(tt_); p.append(pp); k += 1
        return np.array(t), np.array(p)

    v1c = []
    pre_t = np.array([0.0, 0.05, 0.5])                                   # ASSUMED in-burn prefix: light to 30 bar abs in 50 ms, held to 0.5 s
    pre_p = np.array([PA, 30.0, 30.0])
    for c in V1["cases_checked"]:
        nm = c["case"]
        if nm.startswith("S6"):
            t, p = square(c["peak_bar_abs"], c["t_above_MEOP_ms"] / 1e3)
            t = np.concatenate([pre_t, 0.5 + 0.0005 + t]); p = np.concatenate([pre_p, p])
            # resample to 0.05 ms (piecewise linear) so that the trace qualifies for the ESP test
            tr_ = np.arange(0.0, t[-1] + 1e-12, 5e-5); pr_ = np.interp(tr_, t, p)
            o = inside_v2(tr_, pr_)
        else:
            continue
        v1c.append({"case": nm, "v1": {"inside": c["inside"], "zone": c["zone_max"], "jfwd_rule": c["jfwd_rule_triggered"]},
                    "v2": {k: o.get(k) for k in ("inside", "zone_max", "reasons", "S_max_0p02_50ms_bar_abs", "S_max_at_T_ms", "Q_JFWD_bar_abs", "jfwd_rule_triggered", "excursion_windows")}})
    res["v1_cases_rechecked"] = {"note": "S6 squares as v1 (0.5 ms ramps from 45 bar abs) after an ASSUMED in-burn prefix (ambient -> 30 bar abs in 50 ms, held to 0.5 s), resampled at 0.05 ms; the FA-1 pulse cases are in plateau_and_burn_on_families",
                                 "cases": v1c}
    print("v1 cases", json.dumps([(c["case"][:40], c["v1"]["inside"], c["v2"]["inside"], c["v2"]["Q_JFWD_bar_abs"], c["v2"]["jfwd_rule_triggered"]) for c in v1c]), flush=True)

    # ---------------------------------------------------------------------------------------------- 7. the J-FWD rule (F3)
    stj = JS["states"]
    LC2U, LC2Y, LC2N, FA1D, FA1U = (stj[k] for k in ("LC2U", "LC2Y", "LC2N", "FA1D", "FA1U"))
    assert "9.0 MPa, 78.6 C" in LC2U["label"] and "6.75 MPa, 78.6 C" in LC2Y["label"] and "4.5 MPa abs x1.0, 78.6 C" in LC2N["label"]
    assert "121 bar abs, 45.6 C" in FA1D["label"] and "147 bar abs, 45.6 C" in FA1U["label"]
    pm = {k: stj[k]["TC-01"]["ligament_half_avg"]["PmPb"] for k in ("LC2N", "LC2Y", "LC2U")}
    xs = np.array([4.5, 6.75, 9.0]); ys = np.array([pm["LC2N"], pm["LC2Y"], pm["LC2U"]])
    slope, icpt = np.polyfit(xs, ys, 1)
    fit_res = float(np.max(np.abs(icpt + slope * xs - ys)))
    P_RULE_MPA = P_JFWD_RULE / 10.0
    y_slot, u_slot = 1.5 * P_RULE_MPA, 2.0 * P_RULE_MPA
    assert abs(y_slot - 9.0) < 1e-12
    pm_u = icpt + slope * u_slot
    T_LC2 = LC2U["TC-01"]["info_band_elastic"]["T_C"]
    assert T_LC2 == 78.6
    fty, ftu = al("Fty", T_LC2), al("Ftu", T_LC2)
    assert abs(fty / LC2U["TC-01"]["ligament_half_avg"]["PmPb"] - 1.0 - LC2U["TC-01"]["ligament_half_avg"]["MS_y_PmPb"]) < 6e-3
    # CALC TC-01 rows of fix v2 (FA1S, drawing-limit wall), V proportional to the absolute head pressure (V = P A_seal / 10)
    fxr = FX["options"]["IN718 M5 x10"]["TC01"]["drawing_limit_wall"]; fal = FX["inputs"]["Al_allowables_MPa"]
    assert FX["inputs"]["T_C"] == 45.6 and abs(FX["inputs"]["V_abs_N"] - 3888.1) < 1e-9
    kY, kU = al("Fty", T_LC2) / fal["Fty"], al("Ftu", T_LC2) / fal["Ftu"]
    calc = {}
    for nm_, sk, ay, au in (("hole_bearing", "sigma_MPa", "Fbry", "Fbru"), ("shear_out", "tau_MPa", "Fsy", "Fsu")):
        s0 = fxr[nm_][sk]
        sy, su = s0 * y_slot / 15.104, s0 * u_slot / 15.104
        calc[nm_] = {"FA1S_row": fxr[nm_], "at_yield_slot_9.0MPa": round(sy, 1), "at_ult_slot_12.0MPa": round(su, 1),
                     "allow_78.6C_MPa": [round(fal[ay] * kY, 1), round(fal[au] * kU, 1)],
                     "MS_y": round(fal[ay] * kY / sy - 1.0, 3), "MS_u": round(fal[au] * kU / su - 1.0, 3)}
    temps = {}
    for T in (78.6, 100.0, 118.6, 140.3, 150.0):
        temps[f"{T}"] = {"Fty": round(al("Fty", T), 1), "Ftu": round(al("Ftu", T), 1),
                         "TC01_ligament_MS_y_at_9.0MPa": round(al("Fty", T) / pm["LC2U"] - 1.0, 3),
                         "TC01_ligament_MS_u_at_12.0MPa_trend": round(al("Ftu", T) / pm_u - 1.0, 3)}
    basis = {
        "level_bar_abs": P_JFWD_RULE,
        "rule_form": "lead R7: external load factored, preload not; yield slot = the FE state at 1.5 x P, ultimate slot = 2.0 x P, SF 1.0 on the factored state (as the rows v8 LC2 criterion cells)",
        "yield_slot_9.0MPa_is_js5b_LC2U_78.6C": {"TC-01_cell": LC2U["TC-01"]["cell"], "TC-01_ligament_PmPb_MPa": pm["LC2U"], "TC-01_hole_bearing_FE": LC2U["TC-01"]["hole_bearing_t2.688"],
                                                 "TC-02_cell_ruled": {k: LC2U["TC-02"]["cell_ruled"][k] for k in ("MS_y", "MS_u", "governs")},
                                                 "TC-02_tap_bearing": LC2U["TC-02"]["tap_bearing"],
                                                 "SCREW": {k: LC2U["SCREW"][k] for k in ("MS_y", "MS_u", "form", "T_C")}, "tag": "SIM (FEA3D-2 js5b) / DERIVED margins"},
        "ultimate_slot_12.0MPa": {"FA1D_12.1MPa_45.6C_FE": {"TC-01_cell": FA1D["TC-01"]["cell"], "TC-02_cell_ruled": {k: FA1D["TC-02"]["cell_ruled"][k] for k in ("MS_y", "MS_u")},
                                                           "SCREW": {k: FA1D["SCREW"][k] for k in ("MS_y", "MS_u", "form")}},
                                  "TC01_ligament_trend_78.6C": {"fit": f"PmPb = {icpt:.2f} + {slope:.4f} P_MPa through LC2N / LC2Y / LC2U (max residual {fit_res:.2f} MPa)",
                                                                "PmPb_at_12.0MPa": round(pm_u, 1), "Ftu_78.6C": round(ftu, 1), "MS_u": round(ftu / pm_u - 1.0, 3),
                                                                "check_at_12.1MPa_vs_FA1D_FE_45.6C": {"trend": round(icpt + slope * 12.1, 1), "FE": FA1D["TC-01"]["ligament_half_avg"]["PmPb"]},
                                                                "tag": "DERIVED (extrapolation 3.0 MPa beyond LC2U, TO-VERIFY by an FE LC2 x2.0 at 6.0 MPa)"}},
        "CALC_rows_scaled_V_proportional_to_P": calc,
        "temperature_sensitivity_TC01_ligament": {"rows": temps, "note": "allowables at T on the 78.6 C stresses (ASSUMED unchanged); 118.6 C = the TC-01 burn maximum GVHI (rows v8), 140.3 C = rev3 merged perfect contact (information), 150 C = the case-TC OVER_TEMP abort (ASSUMED to bound the TC-01 at the J-FWD while pressurised)"},
        "above_the_level": "no J-FWD row at the nominal factors: FA1D 121 / FA1U 147 / FA1S 151.04 bar abs at SF 1.0 only (rows v8 FA1U / FA1D criterion 231 (1), bounded by FA1S): the line-231 one-off abnormal basis (Neuber local strain, screw yield shear-only on A_3 with the 233 (4) replace rule)",
        "v1_basis_superseded": "v1 jfwd_v352 line 207 (local yield at the TC-02 tap mouth about 66 bar abs, A4-80) and jfwd_preload_v352 (A4-80 combined check at 60 bar abs): superseded by the IN718 rows v8; the level is kept on the rows v8 basis above"}
    minr = min([("TC-01 ligament (LC2U)", LC2U["TC-01"]["cell"]["MS_y_primary_bearing"]), ("TC-02 (LC2U)", LC2U["TC-02"]["cell_ruled"]["MS_y"]),
                ("screw (LC2U)", LC2U["SCREW"]["MS_y"]), ("TC-01 hole bearing CALC", calc["hole_bearing"]["MS_y"])], key=lambda x: x[1])
    minu = min([("TC-01 ligament trend 78.6 C", round(ftu / pm_u - 1.0, 3)), ("TC-01 cell FA1D", FA1D["TC-01"]["cell"]["MS_u_primary_bearing"]),
                ("TC-02 FA1D", FA1D["TC-02"]["cell_ruled"]["MS_u"]), ("screw FA1D", FA1D["SCREW"]["MS_u"]), ("TC-01 hole bearing CALC", calc["hole_bearing"]["MS_u"])], key=lambda x: x[1])
    basis["minimum_at_60bar_nominal_factors"] = {"MS_y": minr, "MS_u": minu}
    assert minr[1] > 0 and minu[1] > 0
    # grid: the quantity, and the flight equivalent of the ideal sampler
    trig = [c for c in A if c["Q_JFWD"] > P_JFWD_RULE]
    notrig = [c for c in A if c["Q_JFWD"] <= P_JFWD_RULE]
    g_jfwd = {"n_Q_JFWD_above_60_of_896": len(trig), "n_peak_above_60_of_896": len(ab60),
              "n_S_band_above_60": groups["all"]["n_S_band_above_60"],
              "n_Q_above_60_with_peak_le_60": sum(c["peak"] <= 60.0 for c in trig),
              "lowest_peak_with_Q_above_60_bar_abs": round(min(c["peak"] for c in trig), 3),
              "Q_over_peak_gauge_ratio_max": round(max((c["Q_JFWD"] - PA) / (c["peak"] - PA) for c in A), 4),
              "S_band_max_bar_abs": round(max(c["S_jfwd_band_0p2_0p5ms"] for c in A), 3),
              "ideal_1kHz_worst_phase_min_among_Q_above_60": round(min(c["ideal_1kHz_sampled_max_worst_phase"] for c in trig), 3),
              "ideal_1kHz_worst_phase_max_among_Q_le_60": round(max(c["ideal_1kHz_sampled_max_worst_phase"] for c in notrig), 3),
              "ideal_1kHz_best_phase_max_among_Q_le_60": round(max(c["ideal_1kHz_sampled_max_best_phase"] for c in notrig), 3),
              "by_group": {g: groups[g]["n_Q_JFWD_above_60"] for g in groups},
              "band_sensitivity_0p1_1ms_n_above_60": sum(max(c["peak"], c["S_band_0p1_1ms"]) > 60.0 for c in A),
              "tag": "DERIVED on the SIM grid; ideal sampler = the head history at 1 kHz without the C1 seat passage, INA333 or anti-alias filter (NOT MODELLED: Electronics' fa1_chain)"}
    # a normal light at the MEOP: linear rise from ambient to 45 bar abs, held (10-90 % = 0.8 x the full rise)
    PB = np.unique(np.concatenate([np.linspace(0.2, 0.5, 601), P_pub[(P_pub >= 0.2 - 1e-9) & (P_pub <= 0.5 + 1e-9)]]))
    nl = {}
    for trf in (0.5e-3, 1.0e-3, 2.0e-3, 5.0e-3):
        qq_ = PA + esp_max(np.array([0.0, trf]), np.array([[0.0, MEOP - PA]]), PB)[0]
        nl[f"rise_full_{trf * 1e3:.1f}ms_10-90_{0.8 * trf * 1e3:.2f}ms"] = round(max(MEOP, float(qq_.max())), 3)
    g_jfwd["normal_light_at_MEOP_linear_rise_Q_JFWD_bar_abs"] = nl

    def q_lin(trf, lev=MEOP):
        return max(lev, PA + float(esp_max(np.array([0.0, trf]), np.array([[0.0, lev - PA]]), PB)[0].max()))
    lo3, hi3 = 0.02e-3, 0.5e-3
    assert q_lin(lo3) > P_JFWD_RULE > q_lin(hi3)
    for _ in range(50):
        mid = 0.5 * (lo3 + hi3)
        lo3, hi3 = (mid, hi3) if q_lin(mid) > P_JFWD_RULE else (lo3, mid)
    g_jfwd["linear_rise_to_MEOP_held_trips_the_rule_below"] = {"full_rise_ms": round(hi3 * 1e3, 4), "rise_10_90_ms": round(0.8 * hi3 * 1e3, 4),
                                                               "commanded_start_for_comparison": "thrust ramp <= 2500 N/s after the light at the start lift: 62.5 -> 500 N t10-90 0.140 s (combustion v2.4c /firmware_constant_sources_v2p4b/v/constants/kStartRamp_Nps = 2500 N/s, DESIGN)",
                                                               "tag": "DERIVED (linear rise from ambient, held, undamped SDOF at 0.2-0.5 ms)"}
    g_jfwd["band_sensitivity_0p02_0p5ms_n_above_60"] = sum(max(c["peak"], float(S[i][iZ][(P_pub >= 0.02 - 1e-9) & (P_pub <= 0.5 + 1e-9)].max())) > 60.0 for i, c in enumerate(per))
    g_jfwd["n_Q_above_60_with_peak_le_45"] = sum(c["peak"] <= MEOP for c in trig)
    X_ideal = g_jfwd["ideal_1kHz_worst_phase_min_among_Q_above_60"]
    g_jfwd["ideal_1kHz_threshold_flagging_every_Q_above_60"] = X_ideal
    g_jfwd["n_Q_le_60_flagged_by_that_threshold_best_phase"] = sum(c["ideal_1kHz_sampled_max_best_phase"] >= X_ideal for c in notrig)

    # ---------------------------------------------------------------------------------------------- 7b. measured traces: the undamped ESP integrates noise
    t_w = T_LIGHT_WIN
    tn = np.arange(0.0, 0.25 + 1e-12, DT_MAX_S)
    t_on, t_rise = 0.010, 5.0e-3
    base = np.interp(tn, [0.0, t_on, t_on + t_rise, 1.0], [PA, PA, MEOP, MEOP])          # a smooth light to MEOP, held (ASSUMED shape)
    t8b = t_on + t_rise * (P_LIGHT - PA) / (MEOP - PA)
    win = lambda pp: _cut(tn, pp, 0.0, t8b + T_LIGHT_WIN)
    S0 = esp_spectrum(*win(base), PZ, x0="rest")
    Q0 = max(MEOP, float(S0[(PZ >= 0.2 - 1e-9) & (PZ <= 0.5 + 1e-9)].max()))
    tone_chk = []
    for T_ms, a in ((0.2, 0.005), (0.405, 0.01), (0.5, 0.01), (3.5, 0.02)):
        tone = np.where(tn > t_on, a * np.sin(TWO_PI * (tn - t_on) / (T_ms * 1e-3)), 0.0)
        S1 = esp_spectrum(*win(base + tone), PZ, x0="rest")
        St = esp_spectrum(*win(PA + tone), PZ, x0="rest") - PA               # the tone alone (its unclipped row), from rest over the same window
        jT = int(np.argmin(np.abs(PZ - T_ms)))
        n_cyc = (t8b + T_LIGHT_WIN - t_on) / (T_ms * 1e-3)
        xs_ = 1.0 / (T_ms * 1e-3 / DT_MAX_S)
        f_s = (math.sin(math.pi * xs_) / (math.pi * xs_)) ** 2              # fundamental of the piecewise-linear sampled tone (sinc^2)
        tone_chk.append({"T_ms": float(PZ[jT]), "tone_amplitude_bar": a, "tone_alone_response_bar": round(float(St[jT]), 3),
                         "analytic_a_pi_N_bar": round(a * math.pi * n_cyc, 3), "sampling_factor_sinc2": round(f_s, 4), "cycles_in_window": round(n_cyc, 1),
                         "S_increase_on_the_light_record_bar": round(float(S1[jT] - S0[jT]), 3),
                         "note": "the increase on the light record depends on the phase between the tone and the light's own response at T (here a 5 ms rise); a noise phase is not chosen, so the tone-alone value is the one to use"})
        assert 0.95 * f_s * a * math.pi * n_cyc < St[jT] < 1.05 * a * math.pi * n_cyc + 0.05, tone_chk[-1]
        assert S1[jT] - S0[jT] <= St[jT] + 0.05, tone_chk[-1]
    rng = np.random.default_rng(20261021)
    r_bb = 0.05
    nz = np.where(tn > t_on, r_bb * rng.standard_normal(len(tn)), 0.0)
    S2 = esp_spectrum(*win(base + nz), PZ, x0="rest")
    bnd_ = (PZ >= 0.2 - 1e-9) & (PZ <= 0.5 + 1e-9)
    B_hz = 0.5 / DT_MAX_S
    sig = lambda T_ms, r, tt: (TWO_PI / (T_ms * 1e-3)) * r * math.sqrt(tt / B_hz) / 2.0
    marg_n = P_JFWD_RULE - Q0
    marg_z3 = P_FA1S - max(c["S_max_0p02_50ms"] for c in A)
    pubd = {col: np.array([float(r[col]) for r in pub]) for col in ("head|all|zeta0", "head|all|zeta0.02", "head|all|zeta0.05")}
    bpub = (P_pub >= 0.2 - 1e-9) & (P_pub <= 0.5 + 1e-9)
    res["noise_sensitivity_measured_traces"] = {
        "statement": ("an undamped oscillator has no loss: on a measured trace S(T) integrates the trace's noise over the window. A coherent tone of amplitude a at the period T "
                      "adds about a pi N (N = cycles of T in the window; 150 ms: 135 a at 3.5 ms, 942 a at 0.5 ms, 2356 a at 0.2 ms); white noise of rms r over a bandwidth B adds a "
                      "response of rms (2 pi / T) r sqrt(t_w / B) / 2. The Z3 v2 test and Q_JFWD are exact on SIM traces (the FA-1 grid, the SIL S6R / N-04 plant traces) and "
                      "conservative on measured ones, where noise alone can trip them"),
        "smooth_light_to_MEOP_held_Q_JFWD_bar_abs": round(Q0, 3), "rise_ms": t_rise * 1e3,
        "tone_checks_light_window": tone_chk,
        "tone_amplitude_that_trips_the_rule_on_that_light_bar": {f"T {T} ms": round(marg_n / (math.pi * t_w / (T * 1e-3)), 4) for T in (0.2, 0.405, 0.5)},
        "tone_amplitude_that_takes_the_worst_grid_case_past_FA1S_at_3.5ms_bar": round(marg_z3 / (math.pi * t_w / 3.5e-3), 4),
        "white_noise_example": {"rms_bar": r_bb, "bandwidth_Hz": B_hz, "seed": 20261021, "band_S_max_increase_bar": round(float((S2 - S0)[bnd_].max()), 3),
                                "formula_rms_at_0.405ms_bar": round(sig(0.405, r_bb, t_w), 3),
                                "white_rms_that_puts_4_sigma_at_the_rule_margin_at_0.5ms_bar": round(marg_n / (4.0 * sig(0.5, 1.0, t_w)), 4)},
        "damped_alternative_information": {"published_v2p4b_head_all_max_bar_abs": {k: round(float(v.max()), 3) for k, v in pubd.items()},
                                           "published_v2p4b_head_all_band_0p2_0p5ms_max_bar_abs": {k: round(float(v[bpub].max()), 3) for k, v in pubd.items()},
                                           "steady_tone_gain_cap": "1 / (2 zeta): 25 at zeta 0.02, 10 at 0.05 (undamped: unbounded, growing with the window)",
                                           "status": "NOT ADOPTED: a damped ESP needs the structure's damping shown (J-FWD / case modal damping not measured: MISSING); OPEN for the lead for the stand use"},
        "stand_use": ("before the first hot run, the B-DPC-1 noise floor over 0.02-50 ms is measured on a record with no event (cold flow or ignition-only, DC-restored as for a hot run) and run "
                      "through inside_v2: the check is usable on the stand where that record's band ESP stays below the levels above (TO-VERIFY, Electronics B-DPC-1); otherwise the lead "
                      "chooses between a damped variant and the peak alone for the stand"),
        "tag": "DERIVED (undamped SDOF engine of this file on ASSUMED synthetic traces); no stand noise data in this package (MISSING)"}
    print("noise", json.dumps({k: v for k, v in res["noise_sensitivity_measured_traces"].items() if k not in ("statement", "stand_use")}), flush=True)
    res["jfwd_rule_v2"] = {
        "rule": (f"J-FWD REPLACE RULE (LC-TB70 v2): when Q_JFWD of a run's head-end pressure exceeds {P_JFWD_RULE} bar abs at any time, the joint counts as used: "
                 f"before the next run the line-231 J-FWD inspection (C6 (2) list: the ten ENG-HW-101-IN718 screws and their HW-170 springs replaced, new, single-use; the TC-01 holes "
                 f"gauged with the pins GO 5.50 / NO-GO 5.62, a hole that takes the 5.62 pin rejected; hole edges and the bore within 3 mm of a hole at 10x; S01 / S02 replaced; "
                 f"the removed screws inspected per C6 (3)) and the TC-02 taps gauged (M5-6H GO / NO-GO)"),
        "action_source": "the published HW-101 action (mechanical.json v2.3 /jfwd_v352/hardware/HW-101/action: 'after any Pc above 60 bar abs the line-231 J-FWD inspection (C6 (2) list)') and the v1 envelope rule (screws replaced, TC-01 holes / TC-02 taps gauged), merged; no new inspection item",
        "quantity": ("Q_JFWD = max(the head peak over the record, max over T in 0.2-0.5 ms of S(T) on the light window (record start before the light to 150 ms after the first "
                     "crossing of 8 bar abs, from rest, held after it) and on each excursion window (50 ms before to 150 ms after an upward crossing of 45 bar abs later than the "
                     "light window, from equilibrium at its start)); S(T) the undamped SDOF ESP of Z3 v2; sample step <= 0.05 ms in the windows, else Q_JFWD is a lower bound (the peak)"),
        "level_bar_abs": P_JFWD_RULE, "duration": "none: one exceedance at any time in the run",
        "signal": {"SIL": "the plant head-end pressure at the 25 us plant step, from before the light (S6R / N-04 re-classification): exact",
                   "stand": "B-DPC-1 (PCB 113B22 head flush at the C1 seat, NI 9234 51.2 kS/s, AC coupled -3 dB 0.5 Hz) DC-restored with the C1 channel (pre-light level and the first-order coupling inverted), the whole run from before the light; Q_JFWD computed post-run; usable once the record-with-no-event noise check of 'noise_sensitivity_measured_traces' passes (TO-VERIFY)",
                   "flight": f"the C1 LIGHT_SPIKE raw peak (1 kHz record, a LOWER BOUND of the head event): Electronics states the flight threshold from its C1 chain model on the 896 grid so that every grid case with Q_JFWD > 60 is flagged (TO-VERIFY), and above the normal-light LIGHT_SPIKE raw peak; the ideal sampler without the chain gives {X_ideal} bar abs, below MEOP, so it can only be a light-window threshold (DERIVED, information)",
                   "flight_consequence": "in flight the joint cannot be replaced before the relight: a flagged first light leaves the relight on a used joint, and the line-231 one-off basis does not cover a second FA-1-class event on one assembly (OPEN, lead)"},
        "normal_lights": (f"NOT meant for normal-light transients. A normal light stays in Z0 (head <= MEOP 45 bar abs, the LC2 basis): a linear rise from ambient to 45 bar abs held gives Q_JFWD "
                          f"{nl['rise_full_1.0ms_10-90_0.80ms']} bar abs at a 0.8 ms 10-90 % rise and {nl['rise_full_0.5ms_10-90_0.40ms']} at 0.4 ms, and reaches 60 only with a 10-90 % rise below "
                          f"{g_jfwd['linear_rise_to_MEOP_held_trips_the_rule_below']['rise_10_90_ms']} ms [DERIVED]; the commanded start ramps thrust at <= 2500 N/s after the light (t10-90 0.140 s, "
                          f"kStartRamp_Nps, combustion v2.4c). No FA-1 grid case with a head peak at or below {g_jfwd['lowest_peak_with_Q_above_60_bar_abs']} bar abs exceeds 60 "
                          f"({g_jfwd['n_Q_above_60_with_peak_le_60']} of the {len(trig)} triggering cases peak at or below 60.0) [DERIVED on SIM]. Q_JFWD > 60 therefore marks a light that loaded "
                          f"the J-FWD beyond its 60 bar abs basis (a peak above 60, or a peak near it with fast J-FWD-band content): an abnormal event by the structural basis, whatever its "
                          f"cause (Z2 above 60.0, Z3). On a measured trace noise in the band can also trip it ('noise_sensitivity_measured_traces')"),
        "peak_only_alternative_for_the_lead": (f"the head peak alone (the v1 quantity and LEAD 256 (4)) flags {len(ab60)} of the 896 grid cases; Q_JFWD adds "
                                               f"{g_jfwd['n_Q_above_60_with_peak_le_60']} cases whose peak is {g_jfwd['lowest_peak_with_Q_above_60_bar_abs']}-60.0 bar abs but whose J-FWD-band ESP exceeds 60 (Q / peak in gauge up to "
                                               f"{g_jfwd['Q_over_peak_gauge_ratio_max']}); the peak alone does not see the J-FWD's dynamic load and is not adopted; it is robust to trace noise"),
        "grid": g_jfwd, "basis_in_the_jfwd_rows": basis,
        "jfwd_band": {"band_ms": list(JFWD_BAND_MS), "source": "CHANGELOG 176: TC-02 head on its screws 0.27-0.39 ms (v3.5.1, eight A4-70); v3.5.2 ten IN718 M5: stiffness x (10/8) x (E_IN718 / E_A4) about 1.32, period about x 0.87 -> 0.235-0.34 ms; band 0.2-0.5 ms ASSUMED (no v3.5.2 J-FWD modal in this package: TO-VERIFY)"}}
    print("jfwd rule", json.dumps(g_jfwd), json.dumps(basis["minimum_at_60bar_nominal_factors"]), flush=True)

    # ---------------------------------------------------------------------------------------------- 8. F4 abort set
    causes = {c["cause"]: c["trigger"] for c in EL["abort_matrix"]["causes"]}
    for nm_ in ("HW_OVERPRESSURE", "PC_OVERPRESSURE", "HARD_START", "PC_SENSOR", "OVER_TEMP", "OVER_THRUST"):
        assert nm_ in causes, nm_
    res["F4_abort_set"] = {
        "lead_provisional": "HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START (253 (8)); the case-TC OVER_TEMP abort in F-14",
        "verdict": "CONFIRMED, with one addition: PC_SENSOR raised on the HIGH side (transducer output >= 4.75 V = 146.5 bar abs: the stand latches and aborts; in flight the non-sticky over-range bit, log v12 ovr_flags b0)",
        "reasons": {"HW_OVERPRESSURE": "comparator U330 on the C1 chain (trip 32.59 bar abs): a head over-pressure in any state; KEEP",
                    "PC_OVERPRESSURE": "filtered Pc > 30 bar abs for 5 ms outside the ignition phase: the throat-blocked (TB) over-pressure in RUN; KEEP",
                    "HARD_START": "filtered Pc > 30 bar abs for 5 ms in IGNITION / early RUN, or >= 4.75 V in IGNITION (and the ride-through T45 guard): the FA-1-class light; KEEP (it may also fire on lights below 60 bar abs: conservative)",
                    "PC_SENSOR_HIGH": "a reading at or above 4.75 V (146.5 bar abs) is either a real head pressure far above 60 bar abs or a fault the record cannot tell from it (electronics.json open-wire rows: EXC- open drives the INA333 out of its common-mode range, output undefined, MISSING, B-PC-1): ADD the HIGH side; the LOW side (below 0.25 V: open wire, cable short) is not a pressure state and is not added",
                    "OVER_TEMP": "already in F-14 (case TC > 150 C for 200 ms)",
                    "OVER_THRUST": "flight only (FC_THRUST > 650 N on 3 frames): a pressure observable when Pc is invalid; NOT added as an abort type, because the trace rule covers it when the head trace resolves the event and the flight joint is not re-used before inspection; information for the lead",
                    "others": "CMD, NO_IGNITION, FLAMEOUT, PC_BAND (a RUN band deviation for 150 ms: a high-side excursion above 30 bar abs is caught first by PC_OVERPRESSURE, 5 ms), TANK_OVERPRESSURE (never aborts a burn), GIMBAL_FAULT, PINTLE_FAULT, LINK_LOST, PREPRESS_FAIL, BATT_LOW, MV_FAULT, ARM_LOST, WATCHDOG, TVC_SUPPLY, OVERCURRENT, MAINT_JAM, TORCH_FAULT, RELIGHT_LOCKOUT, MODE_MISMATCH, BAY_HOT, TANK_HOT, BLEED_FAULT, TORCH_LOST, TANK_COLD, CASE_WARM_STAND: no head over-pressure and no TB thermal state by themselves; not added"},
        "beside_the_abort_set": "the J-FWD replace rule (Q_JFWD > 60 bar abs) applies to every run whatever its end: it covers the ridden-through FA-1 pulses (flight ride-through, no abort) and any Z2 / Z3 excursion without an abort",
        "observation_for_the_lead": "the founder rule's reason is the post-abort soak from a hot (TB) case; a shutdown of any cause from a case hotter than the rows' soak basis is outside the rows too; a case-TC-at-shutdown limit would state it directly (not derived here: OPEN, Mechanical, next round)",
        "electronics_source": {"path": str(INP["electronics_json"][0]), "sha256_16": INP["electronics_json"][1], "causes_read": sorted(causes)}}
    _txt = json.dumps(res["F4_abort_set"]["reasons"])
    assert not [c for c in causes if c not in _txt], [c for c in causes if c not in _txt]

    # ---------------------------------------------------------------------------------------------- 9. zones, margins, rules
    cols = {"Z0": ["LC2"], "Z1": ["TB70"], "Z2": ["TBS"], "Z3": ["FA1S", "FA1U", "FA1D", "FA1Q"], "J-FWD": ["J-FWD"]}
    zm = {}
    for z, cl in cols.items():
        zm[z] = {}
        for col in cl:
            neg, n, mins = [], 0, [None, None]
            for r in MM["rows"]:
                cell = r["cells"].get(col)
                if not cell or not cell.get("value"):
                    continue
                n += 1
                vy, vu = cell["value"]
                for ii, vv in enumerate((vy, vu)):
                    if vv is not None and (mins[ii] is None or vv < mins[ii][1]):
                        mins[ii] = (r["part"], vv)
                if any(vv is not None and vv < 0 for vv in (vy, vu)):
                    neg.append({"part": r["part"], "MS_y_MS_u": [vy, vu], "class": cell.get("class"), "closure": (cell.get("closure") or "")[:200]})
            zm[z][col] = {"n_parts": n, "column_doc": MM["column_doc"].get(col), "min_MS_y": mins[0], "min_MS_u": mins[1], "negatives_SHOWN_AS_FOUND": neg}
    res["v352_margin_matrix_per_zone"] = {"source": {"path": str(INP["margin_matrix_v352"][0]), "sha256_16": INP["margin_matrix_v352"][1]}, "zones": zm,
                                          "note": "regular node set cells as published (rows v8 publication, lead-verified CHANGELOG 255); classes and closures as the matrix states them; v3.5.1 record beside"}
    res["v351_min_margins_regular_set_record"] = V1["v351_min_margins_regular_set"]
    res["zones"] = {"Z0": {"P_bar_abs": [None, MEOP], "tau_s": [0, None], "case": "LC2 (MEOP)", "SF": "1.5 / 2.0 (188 (9))", "change": "none"},
                    "Z1": {"P_bar_abs": [MEOP, P_TB70], "tau_s": [0, T_EVENT], "case": "LC-TB70", "SF": "1.5 / 2.0", "change": "none"},
                    "Z2": {"P_bar_abs": [P_TB70, P_TBS], "tau_s": [0, T_EVENT], "case": "LC-TB-S", "SF": "1.0 / 1.5 (abnormal)", "change": "none"},
                    "Z3": {"P_bar_abs": [P_TBS, P_Z3], "case": "FA-1 class (structure at FA1S 151.04 bar abs, every period)", "SF": "1.0 (FA-1 rule)",
                           "extra": f"ESP <= {P_FA1S} bar abs at 0.02-50 ms; window above {P_TBS} bar abs <= {T_WIN63 * 1e3:.1f} ms; 10-90 % rise >= {TR_FA1 * 1e3:.1f} ms",
                           "change": "RESTATED: ceiling 75.519 -> 88.1 with the ESP test added (REV-COMB-4 Z3' adopted); the v1 window and rise kept"}}
    res["rules"] = [res["jfwd_rule_v2"]["rule"] + "; Q_JFWD = max(head peak, ESP at 0.2-0.5 ms), no minimum duration (jfwd_rule_v2)",
                    "an event that leaves the envelope is outside the structural basis: no margin claim, engine quarantined for inspection (v1, kept)",
                    "one Z3 event per J-FWD assembly: the line-231 basis is a one-off abnormal event; a second Z3 excursion before the replacement is outside the envelope (stated in v2; OPEN for the lead where it bears on the flight relight)"]
    res["Z3_v2_text"] = (f"Z3 (LC-TB70 v2): 63.1 < P_head <= {P_Z3} bar abs inside the light window (record start before the light to 150 ms after the first crossing of 8 bar abs), "
                         f"with the undamped SDOF ESP of the head-end pressure on that window <= {P_FA1S} bar abs (FA1S) at every period 0.02-50 ms (the published 406-period grid; "
                         f"from rest at the record start, g = P - 1.01325 bar piecewise linear and held after the window, the larger of g clipped at 0 and unclipped; sample step <= 0.05 ms), "
                         f"the window above 63.1 bar abs <= 3.0 ms and the 10-90 % rise >= 0.8 ms; REV-COMB-4 Z3' adopted as written with the two v1 shape conditions kept; exact on SIM traces, "
                         f"conservative on measured traces (the undamped test integrates noise: a no-event stand record is checked first, TO-VERIFY); "
                         f"896 of 896 FA-1 grid cases inside (ESP max {res['Z3_v2']['grid']['S_max_bar_abs']} at 3.5 ms, margin {res['Z3_v2']['grid']['margin_to_FA1S_bar']} bar; peak max 88.02; window max "
                         f"{stats['above_63p1_window_63p1_max_v1_measure']} ms; rise min {stats['above_63p1_rise_10_90_min_ms']} ms) [DERIVED on SIM]")
    res["jfwd_rule_v2_text"] = (f"J-FWD replace rule (LC-TB70 v2): Q_JFWD > {P_JFWD_RULE} bar abs at any time in a run (Q_JFWD = the larger of the head peak and the head ESP at the J-FWD "
                                f"periods 0.2-0.5 ms; no minimum duration): the joint counts as used; before the next run the line-231 J-FWD inspection (C6 (2) list: the ten ENG-HW-101-IN718 screws "
                                f"and their HW-170 springs replaced, the TC-01 holes pin-gauged GO 5.50 / NO-GO 5.62, hole edges and bore at 10x, S01 / S02 replaced, removed screws per C6 (3)) "
                                f"and the TC-02 taps gauged (M5-6H GO / NO-GO). Basis: at {P_JFWD_RULE} bar abs every J-FWD row meets the nominal factors at 78.6 C (yield slot 9.0 MPa = "
                                f"js5b LC2U, minimum MS_y {minr[1]:+.3f} {minr[0]}; ultimate slot 12.0 MPa minimum MS_u {minu[1]:+.3f} {minu[0]}); above it only the SF 1.0 FA-1 rows (line-231 "
                                f"one-off). Not meant for normal lights (Z0, <= 45 bar abs: a rise to 45 bar abs trips it only below a "
                                f"{g_jfwd['linear_rise_to_MEOP_held_trips_the_rule_below']['rise_10_90_ms']} ms 10-90 % rise); {len(trig)} of the 896 FA-1 hard-start bracket cases exceed it "
                                f"({len(ab60)} by the peak alone) [SIM grid count on an ASSUMED construct, not a rate of normal lights]. Signal: SIL plant head pressure (exact); stand B-DPC-1 "
                                f"DC-restored with C1 (after a no-event noise check, TO-VERIFY); flight C1 LIGHT_SPIKE raw peak (lower bound) against Electronics' chain-model threshold "
                                f"(TO-VERIFY; ideal sampler {X_ideal} bar abs).")
    res["how_to_use"] = ("Electronics: for each light, its head-end pressure record from before the light (first sample at or below 2.0 bar abs) to the end of that burn (S6R / N-04: "
                         "the SIL plant head pressure at the 25 us plant step, from before the relight; stand: B-DPC-1 DC-restored with C1; sample step <= 0.05 ms at least over the light "
                         "window, record start to 150 ms after the first crossing of 8 bar abs, and over each excursion window, 50 ms before to 150 ms after a later upward crossing of 45 bar abs) "
                         "goes to inside_v2(t_s, p_bar_abs) in lc_tb70_envelope.py (import with python3 -B -I; main() does not run on import); it returns inside (None when a Z3 record "
                         "cannot evaluate the ESP), the zone, the reasons, the ESP maximum and its period, Q_JFWD and the J-FWD rule flag. The 10 S6R runs (fa1rep max_face alone / "
                         "then 50 bar abs, five builds each) and the 29-33 N-04 burn-on cases are re-classified this way. A record whose step is coarser than 0.05 ms in a window "
                         "(the flight 1 kHz log) returns the ESP not evaluated and Q_JFWD as a lower bound. On a measured stand trace the undamped ESP integrates the trace noise: run a record with no "
                         "event (cold flow or ignition-only) through inside_v2 first ('noise_sensitivity_measured_traces').")
    res["purge_tail"] = V1["purge_tail"]
    res["tapwall_v3_reference"] = {"path": str(INP["tapwall_v3"][0]), "sha256_16": INP["tapwall_v3"][1],
                                   "P_torch_statement": TW3["R4-01_additions"]["(c)_P_torch_statement_verbatim_REV-COMB-4"]}
    # compact per-case table
    hdr = ["case", "peak", "rise_10_90_ms", "window_above_63p1_ms", "ms_above_63p1", "S_max_0p02_50ms", "S_max_T_ms", "S_jfwd_band_0p2_0p5ms", "Q_JFWD",
           "ideal_1kHz_worst", "ideal_1kHz_best", "S_below_0p02", "S_50_2000", "v1_inside", "v2_inside"]
    res["grid_per_case"] = {"header": hdr, "rows": [[c["case"], round(c["peak"], 3), round(c["rise_10_90_ms"], 4), round(c["window_above_63p1_ms"], 4), round(c["ms_above"]["63.1"], 4),
                                                     round(c["S_max_0p02_50ms"], 3), c["S_max_T_ms"], round(c["S_jfwd_band_0p2_0p5ms"], 3), round(c["Q_JFWD"], 3),
                                                     round(c["ideal_1kHz_sampled_max_worst_phase"], 3), round(c["ideal_1kHz_sampled_max_best_phase"], 3),
                                                     round(c["S_max_below_0p02ms"], 3), round(c["S_max_50_2000ms"], 3), c["v1_inside"], c["v2_inside"]] for c in per]}
    res["grid_envelope_head_all"] = {"periods_ms": [round(float(x), 6) for x in P_ALL], "S_bar_abs": [round(float(x), 3) for x in env]}
    # the numbers the module docstring quotes, asserted against this run
    assert (LC2U["TC-01"]["cell"]["MS_y_primary_bearing"], LC2U["TC-02"]["cell_ruled"]["MS_y"], LC2U["SCREW"]["MS_y"]) == (0.328, 1.362, 1.583)
    assert FA1D["TC-01"]["cell"]["MS_u_primary_bearing"] == 0.355 and round(ftu / pm_u - 1.0, 3) == 0.312
    assert (len(trig), len(ab60), g_jfwd["n_Q_above_60_with_peak_le_60"], round(g_jfwd["lowest_peak_with_Q_above_60_bar_abs"], 1)) == (298, 185, 113, 49.8)
    assert round(math.pi * T_LIGHT_WIN / 3.5e-3) == 135 and round(math.pi * T_LIGHT_WIN / 0.5e-3) == 942
    assert round(float(pubd["head|all|zeta0.02"].max()), 2) == 142.62 and round(float(pubd["head|all|zeta0"].max()), 2) == 146.88
    assert rep["periods_where_grid_within_50bar_of_FA1S_ms"] == [0.22, 16.7483] and stats["peak_max"] == 88.019
    res["t_run_s"] = round(time.time() - T_START, 1)
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], len(s), res["t_run_s"], flush=True)
    print(res["Z3_v2_text"]); print(res["jfwd_rule_v2_text"])


if __name__ == "__main__":
    main()
