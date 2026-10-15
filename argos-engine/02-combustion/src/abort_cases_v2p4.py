"""Abort transients of the v2.4 sequence (Combustion v2.4; RC-01 abort matrix latencies, RC-04 segment behaviour, cross-check
of GNC's abort tail-off, CHANGELOG 2026-10-13).

Cases (grain_q1d v2, S230 initial port, equilibrium tank 2.00 kg / 3.17 L at 20 C unless stated, nominal law, eta_c* 0.92,
Cd 0.70; pintle 16.7 mm/s (HV69 at MEOP) behind a 10 ms lag; abort command reaches the servo 6.5 ms after the decision):
  A. abort tail-off from steady 100 % (1.92 mm):
     A1 pintle only (valve stays open)                       - GNC 'pintle-only' case
     A2 pintle + NC valve de-energised, valve area ramps to zero in 0.10 s (ASSUMED), NO segment capacitance
     A3 as A2 but the valve-to-seat segment (21.4 cm3, 16 g liquid at 20 C; C6, NC valve at the coil end) is a flashing
        capacitance between the valve and the pintle (mass + energy balance, CoolProp equilibrium)
     A4 as A3 with the 33.0 cm3 segment (valve at the zone top)
     reported: impulse after the abort decision, time to 10 % of the pre-abort thrust, time to < 1 bar gauge Pc,
     N2O through the pintle after the decision, segment pressure history end.
  B. pintle runaway toward full stroke (4 mm) at the servo speed from steady 100 %, over-pressure abort at Pc > 30 bar
     (measured: 2.3 ms latency + 5 ms persistence); the pintle does NOT respond (it is the failed part); the valve closes
     as in A2/A3. Tank 20 C and 30 C (MEOP basis), Cd 0.70 and 0.80. Reported: peak Pc, time above 30 bar and 45 bar.
Valve model: series orifice with CdA_v(t) = CdA_full * max(0, 1 - (t - t_dec)/0.10); CdA_full from Cv 3 (51 mm2,
DERIVED, water-equivalent). Linear area ramp in time is ASSUMED (a ball valve closes with a non-linear area law).
usage: python -I abort_cases_v2p4.py OUTDIR
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
V_P = 0.004 / 0.24; LAG = 0.010; T_CMD = 0.0065
PC_LAT = 0.0023; PERSIST = 0.005; P_ABORT = 30e5
CDA_V_FULL = 3.0 * 0.865 / 3600.0 / math.sqrt(2 * 1e5 / 1000.0)    # Cv 3 -> Kv 2.6 m3/h -> CdA (water) [m2]
T_V = 0.10


class Segment:
    """Liquid/vapour N2O between the NC valve and the pintle seat: rigid volume, homogeneous equilibrium state."""
    def __init__(self, V, T):
        self.V = V
        rho = CP.PropsSI('D', 'T', T, 'Q', 0, FL)
        self.m = rho * V; self.U = self.m * CP.PropsSI('U', 'T', T, 'Q', 0, FL)
        self.update()

    def update(self):
        rho = self.m / self.V; u = self.U / self.m
        try:
            self.P = CP.PropsSI('P', 'D', rho, 'U', u, FL); self.T = CP.PropsSI('T', 'D', rho, 'U', u, FL)
            self.x = CP.PropsSI('Q', 'D', rho, 'U', u, FL)
        except ValueError:
            self.x = 1.0
        hl = CP.PropsSI('H', 'T', self.T, 'Q', 0, FL) if 0 <= self.x < 1 else CP.PropsSI('H', 'D', rho, 'U', u, FL)
        self.h_out = hl
        rho_l = CP.PropsSI('D', 'T', self.T, 'Q', 0, FL) if 0 <= self.x < 1 else rho
        self.liq_vol_frac = (1 - self.x) * self.m / rho_l / self.V if 0 <= self.x < 1 else 0.0


class AbortEngine(Q.Engine):
    def setup_abort(self, t_dec, valve=True, seg_V=None, pintle_responds=True, runaway=False):
        self.t_dec = t_dec; self.valve = valve; self.pintle_responds = pintle_responds; self.runaway = runaway
        self.seg = Segment(seg_V, self.tank.T) if seg_V else None
        self.seg_hist = []

    def cda_valve(self, t):
        if not self.valve or self.t_dec is None or t < self.t_dec:
            return CDA_V_FULL
        return CDA_V_FULL * max(0.0, 1.0 - (t - self.t_dec) / T_V)

    def mox_inj(self, h, Pc):
        if h <= 1e-7:
            return 0.0, self.tank.P
        tk = self.tank; T1 = tk.T
        CdA = self.c['Cd'] * INJ.pintle_area(h)
        cav = self.cda_valve(self.t)
        rho_l = CP.PropsSI('D', 'T', T1, 'Q', 0, FL)
        if self.seg is None:
            m = 0.0; P1 = tk.P
            for _ in range(30):
                dpv = (m / max(cav, 1e-12)) ** 2 / (2 * rho_l) if cav > 0 else float('inf')
                P1 = tk.P - self.dp_line(m) - dpv
                if P1 <= Pc * 1.001:
                    return 0.0, P1
                m_new = CdA * self.GT.G(P1, T1, Pc)
                if abs(m_new - m) < 1e-6:
                    m = m_new; break
                m = 0.5 * m + 0.5 * m_new
            return m, P1
        # segment present: pintle fed from the segment pressure (liquid at the segment temperature)
        s = self.seg
        if s.liq_vol_frac <= 0.02:
            return 0.0, s.P
        P1 = s.P - self.dp_line(self.mox if self.mox > 0 else 0.0) * 0.3        # ~30 % of the line loss is downstream of the valve (ASSUMED)
        if P1 <= Pc * 1.001:
            return 0.0, P1
        return CdA * self.GT.G(P1, s.T, Pc), P1

    def step(self, dt, a_axial=Q.G0):
        if self.seg is not None:
            s = self.seg; cav = self.cda_valve(self.t)
            rho_l = CP.PropsSI('D', 'T', self.tank.T, 'Q', 0, FL)
            dp = max(self.tank.P - s.P, 0.0)
            m_in = cav * math.sqrt(2 * rho_l * dp) if cav > 0 else 0.0
            # quasi-steady when the valve is open: the segment follows the tank (in = out), else integrate
            F = super().step(dt, a_axial)
            m_out = self.mox
            if cav > 0.2 * CDA_V_FULL:
                s.m = s.m; s.update()
                # keep the segment at the liquid-full feed state while the valve is substantially open
                s.P = self.tank.P - self.dp_line(m_out) * 0.7
            else:
                h_in = CP.PropsSI('H', 'T', self.tank.T, 'Q', 0, FL)
                s.m += (m_in - m_out) * dt; s.U += (m_in * h_in - m_out * s.h_out) * dt
                s.update()
            self.seg_hist.append((self.t, s.P, s.x, s.liq_vol_frac, m_in, m_out))
            return F
        return super().step(dt, a_axial)


def run(case, T=293.15, Cd=0.70, seg_V=None, valve=True, runaway=False, t_end=0.6, dt=2e-4):
    e = AbortEngine(EquilibriumTank(3.17e-3, 2.0, T), dict(Cd=Cd, h_rate=V_P, tau_act=LAG))
    e.t = 0.0; e.setup_abort(None, valve=valve, seg_V=None)      # steady init: valve fully open, no segment yet
    s0 = e.init_steady(500.0)
    F0 = s0['F']; e.F = F0
    e.t = 0.0
    e.setup_abort(None if runaway else 0.05, valve=valve, seg_V=seg_V, runaway=runaway)
    t = 0.0; rec = []; hist = []; t_dec = None if runaway else 0.05; above = None
    while t < t_end:
        e.t = t
        if runaway:
            if t >= 0.05:
                e.h_target = Q.INJ.STROKE if hasattr(Q, 'INJ') else 0.004
                e.state = 'run'
            Pm = hist[-1 - int(PC_LAT / dt)] if len(hist) > int(PC_LAT / dt) else e.Pc
            if t_dec is None:
                if Pm > P_ABORT:
                    above = t if above is None else above
                    if t - above >= PERSIST:
                        t_dec = t; e.t_dec = t
                else:
                    above = None
        else:
            if t >= t_dec + T_CMD:
                e.state = 'shutdown'
        F = e.step(dt)
        hist.append(e.Pc)
        rec.append((t, F, e.Pc, e.mox, e.h, e.P1))
        t += dt
    r = np.array(rec)
    out = dict(case=case, T_tank_K=T, Cd=Cd, seg_V_m3=seg_V, valve=valve, F_before_N=F0, t_decision_s=t_dec)
    tt, FF, PP, MM = r[:, 0], r[:, 1], r[:, 2], r[:, 3]
    if not runaway:
        k = tt >= t_dec
        imp = float(np.trapezoid(FF[k], tt[k]) if hasattr(np, 'trapezoid') else np.trapz(FF[k], tt[k]))
        b10 = np.where(k & (FF < 0.1 * F0))[0]; b1 = np.where(k & (PP < 1.0e5 + PAMB_G))[0]
        out.update(impulse_after_decision_Ns=imp, t10_after_decision_s=float(tt[b10[0]] - t_dec) if len(b10) else None,
                   t_Pc_below_1bar_gauge_s=float(tt[b1[0]] - t_dec) if len(b1) else None,
                   N2O_after_decision_g=1e3 * float(np.trapezoid(MM[k], tt[k]) if hasattr(np, 'trapezoid') else np.trapz(MM[k], tt[k])))
    else:
        out.update(Pc_peak_Pa=float(PP.max()), t_peak_s=float(tt[PP.argmax()]),
                   time_above_30bar_s=float(np.sum(PP > 30e5) * dt), time_above_45bar_s=float(np.sum(PP > 45e5) * dt),
                   lift_at_decision_mm=float(np.interp(t_dec, tt, r[:, 4])) * 1e3 if t_dec else None)
    if e.seg is not None and e.seg_hist:
        sh = np.array(e.seg_hist)
        out['segment_end'] = dict(P_Pa=float(sh[-1, 1]), quality=float(sh[-1, 2]), liquid_volume_fraction=float(sh[-1, 3]))
    out['trace'] = dict(t=r[::25, 0].round(4).tolist(), F_N=r[::25, 1].round(1).tolist(), Pc_bar=(r[::25, 2] / 1e5).round(2).tolist(),
                        h_mm=(r[::25, 4] * 1e3).round(3).tolist())
    return out


PAMB_G = 101325.0


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/abort_cases_v2p4.py',
               note='SIM grain_q1d v2 + series valve orifice + flashing segment capacitance; valve area ramp ASSUMED linear in 0.10 s '
                    '(electronics.json v1 close_time ASSUMED); pintle 16.7 mm/s, 10 ms lag, 6.5 ms command latency (DERIVED)',
               CdA_valve_full_m2=CDA_V_FULL, tailoff={}, runaway={})
    for name, kw in (('A1_pintle_only', dict(valve=False)), ('A2_valve_cut_no_segment', dict(valve=True)),
                     ('A3_valve_cut_segment_21p4cm3', dict(valve=True, seg_V=21.4e-6)),
                     ('A4_valve_cut_segment_33p0cm3', dict(valve=True, seg_V=33.0e-6))):
        r = run(name, **kw); res['tailoff'][name] = r
        print(name, {k: v for k, v in r.items() if k != 'trace'}, flush=True)
    for T, Cd in ((293.15, 0.70), (303.15, 0.80)):
        for name, kw in (('B_runaway_valve_cut_no_segment', dict(valve=True)), ('B_runaway_valve_cut_segment_21p4cm3', dict(valve=True, seg_V=21.4e-6)),
                         ('B_runaway_no_valve', dict(valve=False))):
            key = f'{name}|T{T-273.15:.0f}C|Cd{Cd}'
            r = run(key, T=T, Cd=Cd, runaway=True, t_end=0.5, **kw); res['runaway'][key] = r
            print(key, {k: v for k, v in r.items() if k != 'trace'}, flush=True)
    fn = os.path.join(outdir, 'abort_cases_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'data', 'v2', 'v2p4'))
