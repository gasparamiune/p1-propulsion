"""Self-pressurised N2O run-tank models (Combustion v1).

EquilibriumTank: homogeneous saturated liquid + vapour in thermodynamic equilibrium, liquid
  draining from the bottom (or vapour once the liquid is gone), optional lumped tank-wall heat
  capacity coupled with a convective coefficient, optional N2 pad treated as an ideal gas sharing
  the ullage (Dalton) -> 'supercharged' variant. Mass and internal-energy balance:
      dm/dt = -mdot_out ;  dU/dt = -mdot_out*h_out + Q_wall
  State (T) recovered from (m, U, V) with a 1D root solve on saturation properties (CoolProp).
  Reference formulation: S.A. Whitmore & S.N. Chandler, "Engineering Model for Self-Pressurizing
  Saturated-N2O-Propellant Feed Systems", JPP 26(4) 2010, 706-714; B. Zimmerman et al. AIAA 2013-4045
  (equilibrium vs non-equilibrium comparison).
NonEquilibriumTank (Zilliac & Karabeyoglu type) is in tank_nheq.py.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq
import CoolProp.CoolProp as CP
from n2o import FLUID, T_CRIT, sat_props

_AS = CP.AbstractState('HEOS', FLUID)
R_N2 = 296.8      # J/kg/K
CV_N2 = 743.0     # J/kg/K (ideal gas, 300 K)


def _sat(T):
    _AS.update(CP.QT_INPUTS, 0.0, T)
    p = _AS.p(); vl = 1 / _AS.rhomass(); ul = _AS.umass(); hl = _AS.hmass()
    _AS.update(CP.QT_INPUTS, 1.0, T)
    vv = 1 / _AS.rhomass(); uv = _AS.umass(); hv = _AS.hmass()
    return p, vl, vv, ul, uv, hl, hv


class EquilibriumTank:
    def __init__(self, V, m_n2o, T0, m_wall=0.0, c_wall=896.0, hA_wall=0.0, m_n2=0.0):
        """V tank volume [m3]; m_n2o load [kg]; T0 [K]; wall mass/cp for lumped wall heat;
        hA_wall [W/K] internal convective conductance (0 = adiabatic); m_n2 N2 pad mass [kg]."""
        self.V = V; self.m = m_n2o; self.m_wall = m_wall; self.c_wall = c_wall; self.hA = hA_wall
        self.m_n2 = m_n2
        p, vl, vv, ul, uv, hl, hv = _sat(T0)
        x = self._quality(T0)
        # total internal energy of the tank contents (N2O liquid+vapour + N2 pad, common temperature)
        self.U = self.m * (ul + x * (uv - ul)) + self.m_n2 * CV_N2 * T0
        self.T = T0; self.T_wall = T0
        self.update_state()

    def _vol_n2o_avail(self, T, x):
        return self.V

    def _quality(self, T):
        """Vapour mass fraction of the N2O for given T, with optional N2 sharing the ullage.
        With N2 present the N2O vapour + N2 share the ullage volume (Dalton); N2O vapour at Psat(T)."""
        p, vl, vv, ul, uv, hl, hv = _sat(T)
        v = self.V / self.m
        x = (v - vl) / (vv - vl)
        return x

    def _n2o_state_DT(self, rho, T):
        _AS.update(CP.DmassT_INPUTS, rho, T)
        return _AS.umass(), _AS.p(), _AS.Q()

    def update_state(self):
        """Recover T, P, phase split from (m, U, V). N2O state from a (rho, T) flash, which is
        valid both two-phase and superheated (after liquid depletion); N2 pad (ideal gas, assumed
        insoluble) shares T. Total U = m*u_n2o(rho,T) + m_n2*cv*T."""
        rho = self.m / self.V
        def f(T):
            u, p, q = self._n2o_state_DT(rho, T)
            return self.m * u + self.m_n2 * CV_N2 * T - self.U
        lo, hi = 190.0, 420.0
        T = brentq(f, lo, hi, xtol=1e-7)
        u, p, q = self._n2o_state_DT(rho, T)
        self.T = T
        two_phase = 0.0 <= q <= 1.0
        if two_phase:
            p_s, vl, vv, ul, uv, hl, hv = _sat(T)
            x = q
            self.h_l, self.h_v, self.rho_l, self.rho_v = hl, hv, 1 / vl, 1 / vv
            self.m_l = self.m * (1 - x); self.m_v = self.m * x
            self.V_l = self.m_l * vl
        else:
            _AS.update(CP.DmassT_INPUTS, rho, T)
            x = 1.0 if rho < 452.0 else 0.0
            self.h_v = _AS.hmass(); self.h_l = _AS.hmass(); self.rho_v = rho; self.rho_l = rho
            self.m_l = 0.0 if x == 1.0 else self.m; self.m_v = self.m if x == 1.0 else 0.0
            self.V_l = 0.0 if x == 1.0 else self.V
        self.x = x
        self.V_ull = self.V - self.V_l
        p_n2 = self.m_n2 * R_N2 * T / max(self.V_ull, 1e-9) if self.m_n2 > 0 else 0.0
        self.Pv = p
        self.P = p + p_n2
        self.liquid = two_phase and self.m_l > 1e-4
        return self.P

    def step(self, mdot, dt):
        """Drain mdot [kg/s] for dt from the bottom outlet (liquid while present, else vapour)."""
        h_out = self.h_l if self.liquid else self.h_v
        # wall heat
        Q = self.hA * (self.T_wall - self.T)
        if self.m_wall > 0:
            self.T_wall -= Q * dt / (self.m_wall * self.c_wall)
        self.m -= mdot * dt
        self.U += (-mdot * h_out + Q) * dt
        if self.m <= 1e-3:
            self.m = 1e-3
        if self.liquid is False and self.m_n2 > 0:
            pass  # vapour+N2 outflow composition not modelled (end of useful burn)
        self.update_state()
        return self.P


if __name__ == '__main__':
    tk = EquilibriumTank(V=2.5e-3, m_n2o=1.6, T0=293.15)
    print(f"t=0 P={tk.P/1e5:.2f} bar T={tk.T-273.15:.2f} C fill(liq vol frac)={tk.V_l/tk.V:.3f} m_l={tk.m_l:.3f}")
    dt = 0.01; t = 0
    while tk.liquid and t < 20:
        tk.step(0.22, dt); t += dt
        if abs(t - round(t)) < dt / 2:
            print(f"t={t:4.1f} P={tk.P/1e5:6.2f} bar T={tk.T-273.15:6.2f} C m={tk.m:5.3f} m_l={tk.m_l:5.3f}")
    print(f"liquid depletion at t={t:.2f} s, P={tk.P/1e5:.2f} bar, residual vapour {tk.m:.3f} kg")
