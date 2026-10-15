"""Two-control-volume non-equilibrium N2O run tank (Zilliac & Karabeyoglu type) - Combustion v2.

Reference formulation: G. Zilliac, M.A. Karabeyoglu, 'Modeling of Propellant Tank Pressurization', AIAA 2005-3549;
evaluated against equilibrium models in B. Zimmerman, S. Waxman, B. Cantwell, G. Zilliac, 'Review and Evaluation of
Models for Self-Pressurizing Propellant Tank Dynamics', AIAA 2013-4045.  (Formulation re-derived here, not copied.)

Control volumes: liquid (L) and ullage vapour (V), common pressure P; massless liquid surface at Ts = Tsat(P).
  Liquid  : saturated-liquid properties at its own temperature T_L (incompressible approximation, v_l(T_L), u_l(T_L)).
            Energy balance reduces exactly to  m_L (du_l/dT + P dv_l/dT) dT_L/dt = Q_wL - Q_Ls
            (outflow and evaporation remove mass at the liquid's own enthalpy).
  Surface : m_evap = (Q_Ls - Q_sV) / (h_g(Ts) - h_l(T_L))     (negative = condensation)
  Vapour  : dm_V/dt = m_evap - m_out,V ;  dU_V/dt = m_evap h_g(Ts) + Q_sV + Q_wV - P dV_V/dt - m_out,V h_V
            state from a CoolProp (rho, u) flash (inside the dome = ullage fog, P = Psat(T_V)).
  Wall    : lumped node, m_w c_w dT_w/dt = -Q_wL - Q_wV (outer surface adiabatic).
Heat-transfer closure (Z&K): Q = E * C (k/L) (Gr Pr)^(1/3) A dT, C = 0.15, L = tank diameter, g = vehicle axial specific
  force (floored at 0.05 g0; free fall -> natural convection collapses).  E = empirical enhancement factor standing for
  bulk nucleate boiling in the superheated liquid; NOT calibrated for this tank -> run as a band.  E -> infinity
  approaches the equilibrium model (tank.EquilibriumTank).  Wall-side: vertical-plate Nu = 0.1 (Gr Pr)^(1/3), E = 1.
Transport properties: CoolProp 8 has none for N2O -> CO2 (CoolProp) at the same reduced temperature (ASSUMED surrogate).
"""
from __future__ import annotations
import math
import numpy as np
import CoolProp.CoolProp as CP

F = 'NitrousOxide'
TC = CP.PropsSI('Tcrit', F); TC_CO2 = CP.PropsSI('Tcrit', 'CO2')
G0 = 9.80665
_AS = CP.AbstractState('HEOS', F)
_CO2 = CP.AbstractState('HEOS', 'CO2')


def _build_table():
    T = np.arange(200.0, 308.0, 0.05)
    cols = {k: [] for k in ('p', 'vl', 'ul', 'hl', 'vv', 'uv', 'hv', 'cpl', 'cpv', 'mul', 'kl', 'muv', 'kv')}
    for t in T:
        _AS.update(CP.QT_INPUTS, 0.0, t)
        cols['p'].append(_AS.p()); cols['vl'].append(1 / _AS.rhomass()); cols['ul'].append(_AS.umass())
        cols['hl'].append(_AS.hmass()); cols['cpl'].append(_AS.cpmass())
        _AS.update(CP.QT_INPUTS, 1.0, t)
        cols['vv'].append(1 / _AS.rhomass()); cols['uv'].append(_AS.umass()); cols['hv'].append(_AS.hmass())
        cols['cpv'].append(_AS.cpmass())
        tc = t / TC * TC_CO2
        _CO2.update(CP.QT_INPUTS, 0.0, tc); cols['mul'].append(_CO2.viscosity()); cols['kl'].append(_CO2.conductivity())
        _CO2.update(CP.QT_INPUTS, 1.0, tc); cols['muv'].append(_CO2.viscosity()); cols['kv'].append(_CO2.conductivity())
    tab = {k: np.array(v) for k, v in cols.items()}
    tab['T'] = T
    tab['dul'] = np.gradient(tab['ul'], T); tab['dvl'] = np.gradient(tab['vl'], T)
    tab['betal'] = tab['dvl'] / tab['vl']
    return tab


TAB = _build_table()


def sat(T, k):
    return float(np.interp(T, TAB['T'], TAB[k]))


def tsat(P):
    return float(np.interp(P, TAB['p'], TAB['T']))


def _h_nat(k, mu, rho, cp, beta, dT, L, g, C=0.15):
    if dT == 0.0:
        return 0.0
    nu = mu / rho; a = k / (rho * cp)
    ra = g * abs(beta) * abs(dT) * L ** 3 / (nu * a)
    return C * k / L * ra ** (1.0 / 3.0)


class NonEqTank:
    def __init__(self, V, m_n2o, T0, D=0.100, E=1.0e3, m_wall=1.0, c_wall=900.0, liquid_residual=0.01):
        self.V = V; self.D = D; self.A_s = math.pi * D * D / 4; self.Lt = V / self.A_s
        self.E = E; self.m_w = m_wall; self.c_w = c_wall; self.res = liquid_residual
        vl, vv = sat(T0, 'vl'), sat(T0, 'vv')
        x = (V / m_n2o - vl) / (vv - vl)
        if not 0 < x < 1:
            raise ValueError('initial state not two-phase')
        self.m_L = m_n2o * (1 - x); self.T_L = T0
        self.m_V = m_n2o * x; self.U_V = self.m_V * sat(T0, 'uv')
        self.T_w = T0
        self.liquid = True
        self.mevap = 0.0
        self._state()

    # ------------------------------------------------------------------
    def _state(self):
        V_L = self.m_L * sat(self.T_L, 'vl') if self.liquid else 0.0
        V_V = self.V - V_L
        rho = self.m_V / V_V; u = self.U_V / self.m_V
        _AS.update(CP.DmassUmass_INPUTS, rho, u)
        self.P = _AS.p(); self.T_V = _AS.T(); self.q_V = _AS.Q(); self.h_V = _AS.hmass()
        self.cp_V = _AS.cpmass() if not (0 <= self.q_V <= 1) else sat(self.T_V, 'cpv')
        self.V_L = V_L; self.V_V = V_V; self.rho_V = rho
        self.T_s = tsat(self.P)
        self.m = self.m_L + self.m_V
        self.T = self.T_L if self.liquid else self.T_V
        self.m_l = self.m_L
        self.fill = V_L / self.V

    def _fluxes(self, g):
        g = max(abs(g), 0.05 * G0)
        L = self.D; A = self.A_s
        if self.liquid:
            TL, Ts = self.T_L, self.T_s
            hl = _h_nat(sat(TL, 'kl'), sat(TL, 'mul'), 1 / sat(TL, 'vl'), sat(TL, 'cpl'), sat(TL, 'betal'), TL - Ts, L, g)
            Q_Ls = self.E * hl * A * (TL - Ts)
            Tv = self.T_V
            beta_v = 1.0 / max(Tv, 1.0)
            kv, muv = sat(min(Tv, 307.9), 'kv'), sat(min(Tv, 307.9), 'muv')
            hv = _h_nat(kv, muv, self.rho_V, max(self.cp_V, 500.0), beta_v, Ts - Tv, L, g)
            Q_sV = self.E * hv * A * (Ts - Tv)
            dh = sat(Ts, 'hv') - sat(TL, 'hl')
            mevap = (Q_Ls - Q_sV) / dh
            # wall: vertical natural convection, wetted height H_L
            H_L = self.V_L / A; H_V = self.Lt - H_L
            hwl = _h_nat(sat(TL, 'kl'), sat(TL, 'mul'), 1 / sat(TL, 'vl'), sat(TL, 'cpl'), sat(TL, 'betal'),
                         self.T_w - TL, max(H_L, 1e-3), g, C=0.1)
            Q_wL = hwl * (math.pi * self.D * H_L + A) * (self.T_w - TL)
        else:
            Q_Ls = Q_sV = mevap = Q_wL = 0.0; H_V = self.Lt; Tv = self.T_V
            kv, muv = sat(min(Tv, 307.9), 'kv'), sat(min(Tv, 307.9), 'muv')
        hwv = _h_nat(kv, muv, self.rho_V, max(self.cp_V, 500.0), 1.0 / max(Tv, 1.0), self.T_w - Tv, max(H_V, 1e-3), g, C=0.1)
        Q_wV = hwv * (math.pi * self.D * H_V + (0 if self.liquid else self.A_s)) * (self.T_w - Tv)
        return Q_Ls, Q_sV, mevap, Q_wL, Q_wV

    def _rhs(self, mdot, g):
        Q_Ls, Q_sV, mevap, Q_wL, Q_wV = self._fluxes(g)
        P = self.P
        if self.liquid:
            TL = self.T_L
            cstar = sat(TL, 'dul') + P * sat(TL, 'dvl')
            dTL = (Q_wL - Q_Ls) / (self.m_L * cstar)
            dmL = -mdot - mevap
            dVL = sat(TL, 'vl') * dmL + self.m_L * sat(TL, 'dvl') * dTL
            dmV = mevap
            dUV = mevap * sat(self.T_s, 'hv') + Q_sV + Q_wV + P * dVL
        else:
            dTL = dmL = 0.0
            dmV = -mdot
            dUV = -mdot * self.h_V + Q_wV
        dTw = -(Q_wL + Q_wV) / (self.m_w * self.c_w)
        self.mevap = mevap
        return np.array([dmL, dTL, dmV, dUV, dTw])

    def _get(self):
        return np.array([self.m_L, self.T_L, self.m_V, self.U_V, self.T_w])

    def _set(self, y):
        self.m_L, self.T_L, self.m_V, self.U_V, self.T_w = y
        if self.liquid and self.m_L <= self.res:
            # liquid depleted: residual liquid assumed flashed into the vapour CV (energy conserved)
            self.U_V += self.m_L * sat(self.T_L, 'ul'); self.m_V += self.m_L; self.m_L = 0.0; self.liquid = False
        self._state()

    def step(self, mdot, dt, a_axial=G0):
        """Advance by dt with outflow mdot [kg/s] (liquid while present) under axial specific force a_axial."""
        t = 0.0
        while t < dt - 1e-12:
            h = min(dt - t, self._dt_stable(a_axial))
            y0 = self._get()
            k1 = self._rhs(mdot, a_axial)
            self._set(y0 + h * k1)
            k2 = self._rhs(mdot, a_axial)
            self._set(y0 + 0.5 * h * (k1 + k2))
            t += h
        return self.P

    def _dt_stable(self, g):
        if not self.liquid:
            return 5e-3
        eps = 0.05
        Q0 = self._fluxes(g)[0]
        TL0 = self.T_L
        self.T_L = TL0 + eps
        Q1 = self._fluxes(g)[0]
        self.T_L = TL0
        dQdT = max((Q1 - Q0) / eps, 1e-9)
        tau = self.m_L * sat(TL0, 'cpl') / dQdT
        return float(np.clip(0.25 * tau, 2e-4, 5e-3))


if __name__ == '__main__':
    import sys, time
    from tank import EquilibriumTank
    for E in (1e2, 1e3, 1e4):
        tk = NonEqTank(2.059e-3, 1.3, 293.15, E=E)
        eq = EquilibriumTank(2.059e-3, 1.3, 293.15)
        t0 = time.time(); t = 0
        while t < 6.0 and tk.liquid:
            tk.step(0.22, 0.01); eq.step(0.22, 0.01) if eq.liquid else None; t += 0.01
        print(f'E={E:.0e} t={t:.2f} P_neq={tk.P/1e5:.2f} P_eq={eq.P/1e5:.2f} TL={tk.T_L-273.15:.2f} Ts={tk.T_s-273.15:.2f} '
              f'TV={tk.T_V-273.15:.2f} qV={tk.q_V:.3f} mL={tk.m_L:.3f} wall {time.time()-t0:.1f}s')
