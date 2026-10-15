"""Throat-block abort transient (Electronics S6 / abort action A4) and abort tail-off with the balanced-poppet main valve MV-P
(Combustion v2.4; lead requests 2026-10-13: S6 70 % throat block, MV-P Cv 3.6 closing in about 30 ms, 0.10 s kept as the
bounding case until bench test B-MV-1 measures it; Mechanical segment 32.6 cm3).

Question: during a partial throat block the chamber pressure rises towards the feed pressure. Is the excursion acceptable
against MEOP 45 bar / proof 67.5 bar, what sets its peak and its duration, and what must be faster (valve, pintle, threshold)?

Model (SIM, grain_q1d v2 engine, S230 initial port, equilibrium tank 2.00 kg / 3.17 L at the stated temperature):
  * throat area steps to (1 - f) A_t at t_b = 0.05 s (f = blocked fraction; the nozzle Cf is evaluated at the design
    expansion ratio on the open area, thrust is indicative only);
  * detection and actuation on the S6 timeline (Electronics v2.8, relayed by the lead): hardware OVP trip at t_b + 5.7 ms,
    ARM line off at t_b + 12 ms; at ARM-off the main valve starts to close (linear area ramp over t_close: 0.030 s MV-P
    design, 0.10 s bounding) and the pintle is commanded to the seat (servo 16.7 mm/s at MEOP, 10 ms lag; x2 and x4 rate
    variants are hypothetical faster closures);
  * main valve MV-P: CdA from Cv 3.6 (water-equivalent, 61.2 mm2) in series; valve-to-pintle segment 32.6 cm3 (Mechanical,
    CHANGELOG 2026-10-13) as a flashing capacitance (mass + energy balance, CoolProp HEOS equilibrium) once the valve area
    is below 20 % (quasi-steady at tank pressure minus line and valve losses before that); 'no segment' = valve at the pintle;
  * no combustion delay; Pc from the grain_q1d implicit chamber balance.
Also: (i) the static bound (no abort, the pintle held): the plateau the blocked chamber reaches; (ii) the RC-01 abort
tail-off from steady 500 N with MV-P (30 ms) and with the 0.10 s bound; (iii) the feed-line budget with the MV-P Cv 3.6.
usage: python -I throat_block_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
import injector as INJ
from tank import EquilibriumTank

FL = 'NitrousOxide'
V_P = 0.004 / 0.24; LAG = 0.010
T_B = 0.05; T_TRIP = 0.0057; T_ARM = 0.012
MEOP, PROOF = 45e5, 67.5e5
PAMB = 101325.0


def cda_from_cv(cv):
    return cv * 0.865 / 3600.0 / math.sqrt(2 * 1e5 / 1000.0)


CDA_MVP = cda_from_cv(3.6)
_AS = CP.AbstractState('HEOS', FL)


class Segment:
    """N2O between the main valve and the pintle seat: rigid volume, homogeneous equilibrium (robust update)."""
    def __init__(self, V, T):
        self.V = V
        _AS.update(CP.QT_INPUTS, 0.0, T)
        self.m = _AS.rhomass() * V; self.U = self.m * _AS.umass()
        self.P = _AS.p(); self.T = T; self.x = 0.0; self.h_out = _AS.hmass(); self.liq_vol_frac = 1.0
        self.fail = 0

    def update(self):
        rho = self.m / self.V; u = self.U / self.m
        try:
            _AS.update(CP.DmassUmass_INPUTS, rho, u)
            P, T, x = _AS.p(), _AS.T(), _AS.Q()
        except ValueError:
            self.fail += 1
            return
        self.P, self.T = P, T
        if 0.0 <= x <= 1.0:
            self.x = x
            _AS.update(CP.QT_INPUTS, 0.0, T); rho_l = _AS.rhomass(); self.h_out = _AS.hmass()
            self.liq_vol_frac = (1 - x) * self.m / rho_l / self.V
        else:   # single phase (compressed liquid if dense)
            self.x = 0.0 if rho > 400 else 1.0
            _AS.update(CP.DmassUmass_INPUTS, rho, u); self.h_out = _AS.hmass()
            self.liq_vol_frac = 1.0 if rho > 400 else 0.0


class TBEngine(Q.Engine):
    def configure(self, cdav_full=CDA_MVP, t_close=0.030, seg_V=32.6e-6, f_block=0.0, t_b=T_B):
        self.cdav_full = cdav_full; self.t_close = t_close; self.t_valve = None
        self.seg = Segment(seg_V, self.tank.T) if seg_V else None
        self.f_block = f_block; self.t_b = t_b
        self.seg_hist = []

    def cda_valve(self, t):
        if self.t_valve is None or t < self.t_valve or self.t_close is None:
            return self.cdav_full
        return self.cdav_full * max(0.0, 1.0 - (t - self.t_valve) / self.t_close)

    def thrust(self, Pc, OF, At=None):
        At = self.At if At is None else At
        Ae0 = self.Ae; self.Ae = self.c['eps0'] * At
        try:
            return super().thrust(Pc, OF, At)
        finally:
            self.Ae = Ae0

    def mox_inj(self, h, Pc):
        if h <= 1e-7:
            return 0.0, self.tank.P
        tk = self.tank; T1 = tk.T
        CdA = self.c['Cd'] * INJ.pintle_area(h)
        cav = self.cda_valve(self.t)
        _AS.update(CP.QT_INPUTS, 0.0, T1); rho_l = _AS.rhomass()
        if self.seg is None or cav > 0.2 * self.cdav_full:
            m = 0.0; P1 = tk.P
            for _ in range(40):
                dpv = (m / max(cav, 1e-12)) ** 2 / (2 * rho_l) if cav > 0 else float('inf')
                P1 = tk.P - self.dp_line(m) - dpv
                if P1 <= Pc * 1.001:
                    return 0.0, P1
                m_new = CdA * self.GT.G(P1, T1, Pc)
                if abs(m_new - m) < 1e-7:
                    m = m_new; break
                m = 0.5 * m + 0.5 * m_new
            return m, P1
        s = self.seg
        if s.liq_vol_frac <= 0.02:
            return 0.0, s.P
        P1 = s.P - self.dp_line(self.mox if self.mox > 0 else 0.0) * 0.3       # ~30 % of the line loss downstream of the valve (ASSUMED)
        if P1 <= Pc * 1.001:
            return 0.0, P1
        return CdA * self.GT.G(P1, s.T, Pc), P1

    def step(self, dt, a_axial=Q.G0):
        if self.seg is None:
            return super().step(dt, a_axial)
        s = self.seg; cav = self.cda_valve(self.t)
        _AS.update(CP.QT_INPUTS, 0.0, self.tank.T); rho_l = _AS.rhomass(); h_in = _AS.hmass()
        F = super().step(dt, a_axial)
        m_out = self.mox
        if cav > 0.2 * self.cdav_full:
            dpv = (m_out / cav) ** 2 / (2 * rho_l)
            s.P = self.tank.P - self.dp_line(m_out) * 0.7 - dpv; m_in = m_out
        else:
            dp = max(self.tank.P - s.P, 0.0)
            m_in = cav * math.sqrt(2 * rho_l * dp) if cav > 0 else 0.0
            s.m += (m_in - m_out) * dt; s.U += (m_in * h_in - m_out * s.h_out) * dt
            s.update()
        self.seg_hist.append((self.t, s.P, s.x, s.liq_vol_frac, m_in, m_out))
        return F


def make(T, Cd, f_block, t_close, seg_V, rate_mult, F0=500.0, cv=3.6):
    e = TBEngine(EquilibriumTank(3.17e-3, 2.0, T), dict(Cd=Cd, h_rate=V_P * rate_mult, tau_act=LAG),
                 At_hist=None)
    e.t = 0.0
    e.configure(cdav_full=cda_from_cv(cv), t_close=t_close, seg_V=None, f_block=f_block)
    s0 = e.init_steady(F0)
    e.F = s0['F']
    e.configure(cdav_full=cda_from_cv(cv), t_close=t_close, seg_V=seg_V, f_block=f_block)
    At0 = e.At0
    e.At_hist = (lambda t, At0=At0, f=f_block, tb=T_B: At0 * (1.0 - f) if t >= tb else At0)
    return e, s0


def run_block(T=303.15, Cd=0.80, f_block=0.70, t_close=0.030, seg_V=32.6e-6, rate_mult=1.0, F0=500.0, abort=True,
              t_end=0.45, dt=2e-4, cv=3.6):
    e, s0 = make(T, Cd, f_block, t_close, seg_V, rate_mult, F0, cv)
    t = 0.0; rec = []
    t_arm = T_B + T_ARM
    while t < t_end:
        e.t = t
        if abort and t >= t_arm:
            e.state = 'shutdown'
            if e.t_valve is None and t_close is not None:
                e.t_valve = t_arm
        F = e.step(dt)
        rec.append((t, F, e.Pc, e.mox, e.h, e.P1, e.seg.P if e.seg else e.P1))
        t += dt
    r = np.array(rec); tt, FF, PP = r[:, 0], r[:, 1], r[:, 2]
    k = tt >= T_B
    pk = float(PP.max())

    def dur(lim):
        return float(np.sum(PP > lim) * dt)

    def last(lim):
        w = np.where(PP > lim)[0]
        return float(tt[w[-1]] - T_B) if len(w) else None
    b10 = np.where(k & (tt > T_B + T_ARM) & (FF < 0.1 * s0['F']))[0]
    out = dict(T_tank_C=T - 273.15, Cd=Cd, f_block=f_block, F0_N=s0['F'], Pc0_bar=s0['Pc'] / 1e5, h0_mm=s0['h'] * 1e3,
               mv_close_s=t_close, seg_V_cm3=(seg_V or 0) * 1e6, pintle_rate_x=rate_mult, abort=abort,
               P_tank_bar=float(e.tank.P) / 1e5,
               Pc_peak_bar=pk / 1e5, t_peak_after_block_s=float(tt[PP.argmax()] - T_B),
               time_above_MEOP_s=dur(MEOP), time_above_30bar_s=dur(30e5),
               last_above_MEOP_after_block_s=last(MEOP), last_above_30bar_after_block_s=last(30e5),
               t_F_below_10pct_after_block_s=float(tt[b10[0]] - T_B) if len(b10) else None,
               segment_P_end_bar=float(r[-1, 6]) / 1e5, segment_fail_updates=e.seg.fail if e.seg else 0)
    out['trace'] = dict(t=r[::10, 0].round(4).tolist(), Pc_bar=(r[::10, 2] / 1e5).round(2).tolist(),
                        h_mm=(r[::10, 4] * 1e3).round(3).tolist(), P_feed_bar=(r[::10, 6] / 1e5).round(2).tolist(),
                        mox_kg_s=r[::10, 3].round(4).tolist())
    return out


def run_tailoff(T=293.15, Cd=0.70, t_close=0.030, seg_V=32.6e-6, F0=500.0, t_end=0.6, dt=2e-4, cv=3.6, valve=True):
    """RC-01 abort from steady F0: decision at 0.05 s, pintle command 6.5 ms later, valve de-energised at the decision."""
    e, s0 = make(T, Cd, 0.0, t_close, seg_V, 1.0, F0, cv)
    e.At_hist = None
    t_dec = 0.05; t = 0.0; rec = []
    while t < t_end:
        e.t = t
        if t >= t_dec + 0.0065:
            e.state = 'shutdown'
        if valve and t >= t_dec and e.t_valve is None:
            e.t_valve = t_dec
        F = e.step(dt)
        rec.append((t, F, e.Pc, e.mox))
        t += dt
    r = np.array(rec); tt, FF, PP, MM = r.T
    k = tt >= t_dec
    tr = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
    b10 = np.where(k & (FF < 0.1 * s0['F']))[0]; b1 = np.where(k & (PP < 1e5 + PAMB))[0]
    return dict(T_tank_C=T - 273.15, Cd=Cd, mv_close_s=t_close if valve else None, seg_V_cm3=(seg_V or 0) * 1e6, F0_N=s0['F'],
                impulse_after_decision_Ns=float(tr(FF[k], tt[k])), t10_after_decision_s=float(tt[b10[0]] - t_dec) if len(b10) else None,
                t_Pc_below_1bar_gauge_s=float(tt[b1[0]] - t_dec) if len(b1) else None,
                N2O_after_decision_g=1e3 * float(tr(MM[k], tt[k])), segment_fail_updates=e.seg.fail if e.seg else 0)


def feed_budget(d_v2):
    """Feed budget at 0.26 kg/s with the MV-P Cv 3.6 (REPORT v2.3 Table 2.6 items; valve term rescaled as (3/3.6)^2)."""
    F = json.load(open(os.path.join(d_v2, 'feed_line_checks_v2.json')))
    out = {}
    for Tl in ('15C', '20C', '25C'):
        b = F['hose_and_budget'][Tl]
        hose = b['hose_friction']['mu_nom_smooth_PTFE_1p5um']['dp_hose_Pa']; hose_r = b['hose_friction']['mu_nom_rough_25um']['dp_hose_Pa']
        minor = b['dp_minor_Pa']; v3 = b['dp_iso_valve_Pa']['Cv_3.0']; filt = b['dp_filter_Pa']['Cv_2.2']
        v36 = v3 * (3.0 / 3.6) ** 2
        out[Tl] = dict(dp_valve_Cv3_Pa=v3, dp_valve_Cv3p6_Pa=v36, dp_filter_Cv2p2_Pa=filt, dp_minor_Pa=minor,
                       dp_hose_smooth_Pa=hose, dp_hose_rough_Pa=hose_r,
                       total_Cv3_smooth_Pa=hose + minor + v3 + filt, total_Cv3p6_smooth_Pa=hose + minor + v36 + filt,
                       total_Cv3p6_rough_Pa=hose_r + minor + v36 + filt, simulation_budget_Pa=2.5e5 * (0.26 / 0.25) ** 2)
    return out


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/throat_block_v2p4.py',
               request='LEAD 2026-10-13: S6 throat block (Electronics v2.8), A4 response; MV-P balanced poppet Cv 3.6, ~30 ms close '
                       '(Mechanical mv_actuator_v1), 0.10 s bounding until B-MV-1; segment 32.6 cm3 (Mechanical)',
               note='SIM grain_q1d v2 engine (no combustion delay) + series valve + flashing segment; S6 timeline (trip +5.7 ms, ARM off '
                    '+12 ms) from Electronics; servo 16.7 mm/s (DERIVED HV69 at MEOP) behind 10 ms lag (ASSUMED); valve area ramp '
                    'linear in time (ASSUMED); Cv 3.6 water-equivalent CdA 61.2 mm2 (DERIVED from Mechanical Cv)',
               CdA_MVP_m2=CDA_MVP, feed_budget_MVP=feed_budget(os.path.join(HERE, '..', 'data', 'v2')))
    print('feed', json.dumps(res['feed_budget_MVP']['20C']), flush=True)
    blk = {}
    # S6 replica first (30 C, Cd 0.8, 70 %, 500 N), then the matrix
    cases = []
    for T in (303.15, 298.15):
        for f in (0.5, 0.7, 0.9):
            for tc in (0.030, 0.10, None):
                for rm in (1.0, 2.0, 4.0):
                    cases.append(dict(T=T, Cd=0.80, f_block=f, t_close=tc, rate_mult=rm))
        cases.append(dict(T=T, Cd=0.80, f_block=0.7, t_close=0.030, rate_mult=1.0, F0=300.0))
        cases.append(dict(T=T, Cd=0.80, f_block=0.7, t_close=0.10, rate_mult=1.0, F0=300.0))
        cases.append(dict(T=T, Cd=0.70, f_block=0.7, t_close=0.030, rate_mult=1.0))
        cases.append(dict(T=T, Cd=0.80, f_block=0.7, t_close=0.030, rate_mult=1.0, seg_V=None))
        cases.append(dict(T=T, Cd=0.80, f_block=0.7, t_close=0.030, rate_mult=1.0, seg_V=21.42e-6))
        for f in (0.7, 0.99):    # 0.99 = near-full block (a fully closed throat divides the Cf model by zero; plateau = feed pressure)
            cases.append(dict(T=T, Cd=0.80, f_block=f, t_close=None, rate_mult=1.0, abort=False, t_end=0.35))
    cases.insert(0, cases.pop(cases.index(dict(T=303.15, Cd=0.80, f_block=0.7, t_close=0.10, rate_mult=1.0))))
    for kw in cases:
        r = run_block(**kw)
        mv = 'none' if r['mv_close_s'] is None else f"{r['mv_close_s'] * 1e3:.0f}ms"
        key = (f"T{r['T_tank_C']:.0f}C|Cd{r['Cd']}|f{r['f_block']}|F{kw.get('F0', 500.0):.0f}|MV{mv}"
               f"|seg{r['seg_V_cm3']:.1f}|rate_x{r['pintle_rate_x']:g}|{'abort' if r['abort'] else 'no_abort'}")
        blk[key] = r
        print(key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != 'trace'}, flush=True)
    res['throat_block'] = blk
    tl = {}
    for T in (293.15, 303.15):
        for tc, valve in ((0.030, True), (0.10, True), (None, False)):
            for sv in (32.6e-6, None):
                r = run_tailoff(T=T, t_close=tc, seg_V=sv, valve=valve)
                key = f"T{T-273.15:.0f}C|MV{'none' if not valve else f'{tc*1e3:.0f}ms'}|seg{(sv or 0)*1e6:.1f}"
                tl[key] = r
                print('tailoff', key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    res['tailoff_RC01'] = tl
    fn = os.path.join(outdir, 'throat_block_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


def main_seg(outdir, seg_cm3=44.0):
    """Zone-top MV-P (LEAD 2026-10-13, option A): MV-to-seat segment ~44 cm3. Re-runs the governing throat-block cases (S6, 25/30 C,
    70/90 % block, MV 30 ms and 0.10 s, pintle x1) and the RC-01 tail-off (20/30 C) at that segment volume."""
    sv = seg_cm3 * 1e-6
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/throat_block_v2p4.py (main_seg)', segment_cm3=seg_cm3,
               request='LEAD 2026-10-13: zone-top MV-P, segment ~44 cm3; re-check of throat block / tail-off at that volume',
               note='as throat_block_v2p4.json; only the segment volume changes (ESTIMATE until Mechanical measures the v3.4 solids)')
    blk = {}
    for T in (303.15, 298.15):
        for f in (0.7, 0.9):
            for tc in (0.030, 0.10):
                r = run_block(T=T, Cd=0.80, f_block=f, t_close=tc, seg_V=sv, rate_mult=1.0)
                key = f"T{r['T_tank_C']:.0f}C|Cd0.8|f{f}|F500|MV{tc * 1e3:.0f}ms|seg{seg_cm3:.1f}|rate_x1|abort"
                r.pop('trace', None); blk[key] = r
                print(key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    res['throat_block'] = blk
    tl = {}
    for T in (293.15, 303.15):
        for tc in (0.030, 0.10):
            r = run_tailoff(T=T, t_close=tc, seg_V=sv, valve=True)
            key = f"T{T-273.15:.0f}C|MV{tc*1e3:.0f}ms|seg{seg_cm3:.1f}"
            tl[key] = r
            print('tailoff', key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    res['tailoff_RC01'] = tl
    fn = os.path.join(outdir, f'throat_block_seg{seg_cm3:g}_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2].startswith('seg'):
        main_seg(sys.argv[1], float(sys.argv[2][3:]))
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'data', 'v2', 'v2p4'))
