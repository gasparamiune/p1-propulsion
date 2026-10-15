"""Quasi-1D space-time hybrid engine model (Combustion v2, brief task 4.4-4.5).

Couples: N2O tank (equilibrium or Zilliac-Karabeyoglu non-equilibrium) -> feed-line loss -> pintle injector (Dyer
NHNE, table) -> chamber (filling ODE, CEA c*(Pc,O/F) x eta_c*) -> quasi-1D port (N axial cells: port diameter D(x),
oxidiser flux G_ox(x), total flux G(x), cumulative fuel flow, local O/F(x)) -> nozzle (CEA Cf with Schmucker separation,
eta_cf) and, optionally, a throat-area history from the erosion model.
Port physics: r(x) = F_helix * a * G^n (law 'ox': G = G_ox; law 'total': G = G_ox + G_fuel,cum(x)); fuel-regression
response lags the quasi-steady law with the solid-phase thermal time tau_s = kappa_s / r^2 (first-order, ASSUMED form;
Karabeyoglu et al. JPP 21(6) 2005 for the thermal-lag physics).  Web: helical port centreline offset r_h -> minimum web
w_min(x) = R_grain - r_h - D(x)/2 ; burn-through when w_min <= 0 (liner exposed).
Control: feed-forward inversion of the quasi-steady map every control period (default 10 ms) to the lift that gives the
commanded thrust, limited by the injector-stiffness ceiling Pc <= P1/(1 + dP/Pc_min) and by the 4 mm stroke; the
actuator follows at <= 50 mm/s (80 ms full stroke, combustion.json v1) with a 10 ms first-order lag.  Start: torch
on, main pintle opens 0.10 s after the start command to the commanded lift; shutdown: pintle closes at the rate limit.
All inputs tagged in CFG.  Usage: see run_dc.py.
"""
from __future__ import annotations
import math, os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from perf_tables import Perf, PA_SL, G0
import injector as INJ

CFG = dict(
    L_grain=(0.230, 'DERIVED v2 baseline (grain trade 2026-10-12; v1 0.200) [m]'), D_grain=(0.0535, 'combustion.json v1 [m]'),
    D_port0=(0.025, 'combustion.json v1 [m]'), r_helix=(0.0, 'v2 centred straight port (lead decision 2026-10-12); v1 helix 0.004 [m]'),
    L_pre=(0.030, 'v1 [m]'), L_post=(0.040, 'v1 [m]'), D_ch=(0.0539, 'v1 gas-side chamber diameter [m]'),
    V_conv=(1.2e-5, 'DERIVED convergent volume from the contour CSV [m3]'),
    Dt0=(0.013724, 'v1 [m]'), eps0=(2.0, 'v1'),
    rho_f=(1000.0, 'ASSUMED printed ABS [kg/m3]'),
    a=(0.0577e-3, 'ASSUMED band x0.6-1.5 [m/s (kg/m2/s)^-n]'), n=(0.5, 'ASSUMED band 0.35-0.68'),
    F_helix=(1.0, 'v2 straight port: no helix amplification (v1 helix: ASSUMED 1.5, band 1.0-2.5)'), law=('ox', 'ASSUMED oxidiser-flux law (total-flux variant = sensitivity)'),
    kappa_s=(1.2e-7, 'LITERATURE-UNVERIFIED ABS thermal diffusivity k/(rho c) ~0.17/(1040*1400) [m2/s]'),
    eta_cstar=(0.92, 'ASSUMED (band 0.85-0.96)'), eta_cf=(0.975, 'ASSUMED (15 deg cone 0.983 x 0.992)'),
    Cd=(0.70, 'ASSUMED pintle Cd (0.6-0.8)'), dp_line_ref=(2.5e5, 'ASSUMED line loss at 0.25 kg/s, ~mdot^2 [Pa]'),
    dpc_min=(0.25, 'DERIVED stiffness rule dP_inj/Pc >= 0.25'),
    h_rate=(0.05, 'DERIVED actuator rate [m/s] (4 mm in 80 ms)'), tau_act=(0.010, 'ASSUMED servo lag [s]'),
    t_open_delay=(0.10, 'DERIVED torch-to-main delay [s]'), r_ign_frac=(0.3, 'ASSUMED preheated fraction of the quasi-steady regression at main-flow arrival'),
    N=(40, 'axial cells'),
    P_star0=(1.0, 'initial burning-perimeter factor of a printed star port relative to a circle of the same area (1 = round)'),
    dr_star=(0.004, 'regression distance over which the star rounds out [m] (ASSUMED ~ lobe height)'),
    h_lobe=(0.0, 'star lobe tip height beyond the equivalent-circle radius [m] (web penalty, decays with dr_star)'),
)
V = {k: v[0] for k, v in CFG.items()}
# named grain variants (v2 grain trade); {} = v2 baseline S230
VARIANTS = {'v1_helix_L200': dict(r_helix=0.004, F_helix=1.5, L_grain=0.200),
            'S200_straight_L200': dict(r_helix=0.0, F_helix=1.0, L_grain=0.200),
            'v2_S230_straight_L230': {},
            'S260_straight_L260': dict(r_helix=0.0, F_helix=1.0, L_grain=0.260)}

_PERF = None
_GT = None


def perf():
    global _PERF
    if _PERF is None:
        _PERF = Perf(os.path.join(HERE, '..', 'data', 'perf_table_ABS_TYP_v1_shifting_v1.json'))
    return _PERF


def gtab():
    global _GT
    if _GT is None:
        _GT = INJ.GTable()
    return _GT


def Gamma(g):
    return math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))


class Engine:
    def __init__(self, tank, cfg=None, At_hist=None):
        self.c = dict(V); self.c.update(cfg or {})
        c = self.c
        self.P = perf(); self.GT = gtab()
        self.tank = tank
        N = int(c['N']); self.N = N
        self.dx = c['L_grain'] / N
        self.x = (np.arange(N) + 0.5) * self.dx
        self.D = np.full(N, c['D_port0'])
        self.r_eff = np.zeros(N)
        self.At0 = math.pi * c['Dt0'] ** 2 / 4; self.At = self.At0; self.Ae = self.At0 * c['eps0']
        self.At_hist = At_hist        # callable t -> At, or None
        self.h = 0.0; self.h_cmd = 0.0; self.h_target = 0.0
        self.Pc = PA_SL; self.on = False; self.t_on = -1.0; self.state = 'off'
        self.OF = 3.0; self.mox = 0.0; self.mf = 0.0
        self.V_fixed = math.pi / 4 * c['D_ch'] ** 2 * (c['L_pre'] + c['L_post']) + c['V_conv']
        self.fuel_burnt = 0.0; self.ox_used = 0.0; self.impulse = 0.0
        self.burnthrough = None

    # ---------------- sub-models ----------------
    def Vc(self):
        return self.V_fixed + float(np.sum(math.pi / 4 * self.D ** 2) * self.dx)

    def dp_line(self, mox):
        return self.c['dp_line_ref'] * (mox / 0.25) ** 2

    def mox_inj(self, h, Pc):
        """Oxidiser flow through the pintle for lift h at chamber pressure Pc (feed-line loss iterated)."""
        if h <= 1e-7:
            return 0.0, self.tank.P
        tk = self.tank
        CdA = self.c['Cd'] * INJ.pintle_area(h)
        T1 = tk.T_L if hasattr(tk, 'T_L') else tk.T
        m = 0.0; P1 = tk.P
        for _ in range(3):
            P1 = tk.P - self.dp_line(m)
            if P1 <= Pc * 1.001:
                return 0.0, P1
            m = CdA * self.GT.G(P1, T1, Pc)
        return m, P1

    def regression(self, mox, D=None):
        """Quasi-steady regression r(x), cumulative fuel flow, local O/F along the port."""
        c = self.c; D = self.D if D is None else D
        Ap = math.pi / 4 * D ** 2
        frac = self.burn_frac(D) * self.perim(D)
        if c['law'] == 'ox':
            G = mox / Ap
            r = c['F_helix'] * c['a'] * G ** c['n']
            mfx = c['rho_f'] * math.pi * D * r * self.dx * frac
            mcum = np.cumsum(mfx)
        else:
            r = np.zeros(self.N); mcum = np.zeros(self.N); acc = 0.0
            for i in range(self.N):
                G = (mox + acc) / Ap[i]
                r[i] = c['F_helix'] * c['a'] * G ** c['n']
                acc += c['rho_f'] * math.pi * D[i] * r[i] * self.dx * frac[i]
                mcum[i] = acc
        return r, mcum

    def perim(self, D):
        c = self.c
        if c['P_star0'] <= 1.0:
            return 1.0
        dr = np.maximum((D - c['D_port0']) / 2, 0.0)
        return 1.0 + (c['P_star0'] - 1.0) * np.clip(1 - dr / c['dr_star'], 0.0, 1.0)

    def lobe(self, D):
        c = self.c
        if c['h_lobe'] <= 0:
            return 0.0
        dr = np.maximum((D - c['D_port0']) / 2, 0.0)
        return c['h_lobe'] * np.clip(1 - dr / c['dr_star'], 0.0, 1.0)

    def burn_frac(self, D):
        c = self.c
        R = c['D_grain'] / 2; rh = c['r_helix']; rout = D / 2 + self.lobe(D)
        if rh <= 0:
            return np.where(rout < R, 1.0, 0.0)
        return np.clip((R + rh - rout) / (2 * rh), 0.0, 1.0)

    def wmin(self):
        return self.c['D_grain'] / 2 - self.c['r_helix'] - (self.D / 2 + self.lobe(self.D))

    def cstar(self, Pc, OF):
        return self.P.cstar(Pc, OF) * self.c['eta_cstar']

    def thrust(self, Pc, OF, At=None):
        At = self.At if At is None else At
        eps = self.Ae / At
        if Pc < 1.3 * PA_SL:
            return 0.0, None, 0.0
        cf, es, pepa = self.P.cf_amb(Pc, OF, eps)
        e = es if es else eps
        F = (self.c['eta_cf'] * self.P.cf_vac(Pc, OF, e) - e * PA_SL / Pc) * Pc * At
        return max(F, 0.0), es, pepa

    def steady(self, h, D=None, At=None):
        """Quasi-steady operating point for lift h at the current port/tank state."""
        At = self.At if At is None else At
        Pc = max(self.Pc, 3e5)
        for _ in range(60):
            mox, P1 = self.mox_inj(h, Pc)
            if mox <= 0:
                return None
            r, mcum = self.regression(mox, D)
            mf = mcum[-1]; OF = mox / mf
            Pn = (mox + mf) * self.cstar(Pc, OF) / At
            if abs(Pn - Pc) < 50.0:
                Pc = Pn; break
            Pc = 0.5 * Pc + 0.5 * Pn
        F, es, pepa = self.thrust(Pc, OF, At)
        return dict(h=h, Pc=Pc, mox=mox, mf=mf, OF=OF, P1=P1, F=F, es=es, pepa=pepa,
                    dpc=(P1 - Pc) / Pc, Isp=F / ((mox + mf) * G0))

    def ceiling(self):
        """Highest thrust allowed by the stiffness rule (Pc <= P1/(1+dpc_min)) and the stroke."""
        from scipy.optimize import brentq
        hmax = INJ.STROKE
        smax = self.steady(hmax)
        if smax is None:
            return None
        if smax['dpc'] >= self.c['dpc_min']:
            smax['limit'] = 'stroke'; return smax
        f = lambda h: self.steady(h)['dpc'] - self.c['dpc_min']
        try:
            hc = brentq(f, 2e-5, hmax, xtol=2e-7)
        except ValueError:
            return None
        s = self.steady(hc); s['limit'] = 'dP/Pc'
        return s

    def lift_for_thrust(self, F_cmd, h_guess=None, cei=None):
        """Lift giving F_cmd at the current state (secant from h_guess, Brent fallback); saturates at the ceiling."""
        from scipy.optimize import brentq
        cei = cei or self.ceiling()
        if cei is None:
            return 0.0, None
        if F_cmd >= cei['F']:
            return cei['h'], cei
        lo = 1e-5
        if h_guess is not None and 2 * lo < h_guess < cei['h']:
            h0, h1 = h_guess, min(h_guess * 1.03, cei['h'])
            s0 = self.steady(h0); s1 = self.steady(h1)
            if s0 is not None and s1 is not None:
                f0, f1 = s0['F'] - F_cmd, s1['F'] - F_cmd
                for _ in range(8):
                    if abs(f1) < 1e-3 * max(F_cmd, 10.0) or f1 == f0:
                        break
                    h2 = h1 - f1 * (h1 - h0) / (f1 - f0)
                    h2 = min(max(h2, lo), cei['h'])
                    s2 = self.steady(h2)
                    if s2 is None:
                        break
                    h0, f0, h1, f1 = h1, f1, h2, s2['F'] - F_cmd
                if abs(f1) < 2e-3 * max(F_cmd, 10.0):
                    return h1, cei
        flo = self.steady(lo)
        if flo is None or flo['F'] > F_cmd:
            return lo, cei
        try:
            h = brentq(lambda h: self.steady(h)['F'] - F_cmd, lo, cei['h'], xtol=2e-7)
        except ValueError:
            h = cei['h']
        return h, cei

    # ---------------- dynamics ----------------
    def step(self, dt, a_axial=G0):
        c = self.c
        # actuator
        hc = self.h_target if self.state in ('run',) or (self.state == 'start' and self.t_on >= c['t_open_delay']) else 0.0
        if self.state == 'shutdown':
            hc = 0.0
        dh = (hc - self.h_cmd)
        self.h_cmd += float(np.clip(dh, -c['h_rate'] * dt, c['h_rate'] * dt))
        self.h += (self.h_cmd - self.h) * min(1.0, dt / c['tau_act'])
        # oxidiser flow
        mox, P1 = self.mox_inj(self.h, self.Pc) if self.tank.liquid else (0.0, self.tank.P)
        if not self.tank.liquid and self.h > 1e-7:
            # vapour-phase flow after liquid depletion: SPI on vapour density (choked approximation ignored) - end of useful burn
            rho_v = self.tank.rho_V if hasattr(self.tank, 'rho_V') else self.tank.rho_v
            mox = c['Cd'] * INJ.pintle_area(self.h) * math.sqrt(max(2 * rho_v * (self.tank.P - self.Pc), 0.0))
        self.mox = mox
        # regression with thermal lag
        r_qs, _ = self.regression(mox) if mox > 0 else (np.zeros(self.N), None)
        if self.state in ('start', 'run') and mox > 0:
            if self.r_eff.max() <= 0.0:
                self.r_eff = c['r_ign_frac'] * r_qs
            tau = np.clip(c['kappa_s'] / np.maximum(np.maximum(self.r_eff, r_qs), 1e-5) ** 2, 0.02, 2.0)
            self.r_eff += (r_qs - self.r_eff) * np.minimum(1.0, dt / tau)
        else:
            # after shutdown the surface cools; the pyrolysis decays in ~tau (ASSUMED), no regression credit
            self.r_eff *= math.exp(-dt / 0.05)
        # burnt-through cells: the remaining sliver (offset helix) shrinks from D/2 = R-r_h to R+r_h
        frac = self.burn_frac(self.D)
        mfx = c['rho_f'] * math.pi * self.D * self.r_eff * self.dx * frac * self.perim(self.D)
        mf = float(mfx.sum()); self.mf = mf
        self.D += 2 * self.r_eff * dt * (frac > 0)
        # chamber (implicit in Pc)
        OF = mox / mf if mf > 1e-9 else 50.0
        OF = min(max(OF, 1.0), 14.0)
        self.OF = OF
        if self.At_hist is not None:
            self.At = self.At_hist(self.t)
        cs = self.cstar(max(self.Pc, 1.5e5), OF) if (mox + mf) > 0 else self.cstar(3e5, 3.0)
        g = self.P.gamma(max(self.Pc, 1.5e5), OF)
        RT = (cs * Gamma(g)) ** 2
        Vc = self.Vc()
        dV = float(np.sum(math.pi * self.D * self.r_eff) * self.dx)
        comb = (mox + mf) > 0 and self.state in ('start', 'run', 'shutdown')
        if comb:
            a1 = dt * RT / Vc
            self.Pc = (self.Pc + a1 * (mox + mf)) / (1 + a1 * self.At / cs + dt * dV / Vc)
        else:
            # cold blow-down of the chamber through the throat (approx. isothermal, gas at RT of cold N2O/products ignored)
            self.Pc = PA_SL + (self.Pc - PA_SL) * math.exp(-dt / 0.003)
        self.Pc = max(self.Pc, PA_SL)
        F, es, pepa = self.thrust(self.Pc, OF)
        self.F = F; self.es = es; self.P1 = P1
        # tank
        self.tank.step(mox, dt, a_axial) if hasattr(self.tank, 'T_L') else self.tank.step(mox, dt)
        # bookkeeping
        self.fuel_burnt += mf * dt; self.ox_used += mox * dt; self.impulse += F * dt
        wmin = self.wmin()
        if self.burnthrough is None and wmin.min() <= 0:
            self.burnthrough = self.t
        if self.state == 'start':
            self.t_on += dt
            if self.t_on >= c['t_open_delay'] and self.h > 0.9 * self.h_target:
                self.state = 'run'
        if self.state == 'shutdown' and self.h <= 1e-7 and self.Pc < 1.2 * PA_SL:
            self.state = 'off'; self.r_eff[:] = 0.0
        return F

    def init_steady(self, F_cmd):
        """Start already running in steady state at F_cmd (e.g. a record that begins at liftoff)."""
        h, cei = self.lift_for_thrust(F_cmd)
        s = self.steady(h)
        self.h = self.h_cmd = self.h_target = h
        self.Pc = s['Pc']
        r, _ = self.regression(s['mox']); self.r_eff = r.copy()
        self.state = 'run'
        return s


def simulate(dc, tank, cfg=None, dt=1e-3, ctrl_dt=0.01, init_running=False, At_hist=None, record_dt=0.01,
             t_extra=0.5, verbose=False, cei_dt=0.1):
    """dc: dict with arrays t, F_cmd, a_axial (NaN -> g0). Returns (records list, engine)."""
    e = Engine(tank, cfg, At_hist)
    t_arr = np.asarray(dc['t']); Fc = np.asarray(dc['F_cmd']); aa = np.asarray(dc.get('a_axial', np.full_like(t_arr, G0)))
    aa = np.where(np.isfinite(aa), aa, G0)
    t = t_arr[0]; e.t = t
    if init_running and Fc[0] > 0:
        e.init_steady(Fc[0])
    rec = []; next_ctrl = t; next_rec = t; cei = None; next_cei = t
    t_end = t_arr[-1] + t_extra
    while t <= t_end:
        e.t = t
        F_cmd = float(np.interp(t, t_arr, Fc)) if t <= t_arr[-1] else 0.0
        a_ax = float(np.interp(t, t_arr, aa)) if t <= t_arr[-1] else G0
        if t >= next_ctrl:
            if F_cmd > 0 and e.state in ('off', 'shutdown') and e.tank.liquid:
                e.state = 'start'; e.t_on = 0.0
            if F_cmd <= 0 and e.state in ('start', 'run'):
                e.state = 'shutdown'
            if e.state in ('start', 'run') and e.tank.liquid:
                if cei is None or t >= next_cei:
                    cei = e.ceiling(); next_cei = t + cei_dt
                h, cei = e.lift_for_thrust(F_cmd, h_guess=e.h_target if e.h_target > 0 else None, cei=cei)
                e.h_target = h
            next_ctrl += ctrl_dt
        F = e.step(dt, a_ax)
        if t >= next_rec - 1e-9:
            wmin = e.wmin()
            rec.append(dict(t=t, F_cmd=F_cmd, F=F, Pc=e.Pc, mox=e.mox, mf=e.mf, OF=e.OF if e.mf > 0 else float('nan'),
                            Isp=F / ((e.mox + e.mf) * G0) if (e.mox + e.mf) > 1e-6 and F > 0 else float('nan'),
                            h=e.h, P1=e.P1, dpc=(e.P1 - e.Pc) / e.Pc if e.mox > 0 else float('nan'),
                            P_tank=e.tank.P, T_tank=getattr(e.tank, 'T_L', e.tank.T), m_liq=e.tank.m_l,
                            fill=getattr(e.tank, 'fill', float('nan')), D_min=float(e.D.min()), D_max=float(e.D.max()),
                            w_min=float(wmin.min()), At=e.At, sep_eps=e.es if e.es else float('nan'),
                            F_ceiling=cei['F'] if (cei is not None and e.state == 'run') else float('nan'),
                            state=e.state, a_axial=a_ax))
            next_rec += record_dt
        t += dt
    return rec, e
