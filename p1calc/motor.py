"""Modelo DC equivalente del BLDC + ESC, punto de operación y térmico.

    KV_rad = KV·2π/60 [rad/s/V] ;  Kt = 1/KV_rad [N·m/A]
    I   = Q_m/Kt + I0
    V_m = ω_m/KV_rad + I·R
    P_elec = V_m·I ;  P_bat = P_elec/η_ESC ;  I_bat = P_bat/V_bat ; duty = V_m/V_bat

Térmico (1 nodo): T(t) = T_amb + R_th·P_loss·(1 − e^(−t/τ))
"""
from __future__ import annotations

import math


class Motor:
    def __init__(self, spec: dict, name: str = ""):
        self.name = name
        self.kv = spec["kv_rpm_v"]
        self.R = spec["r_ohm"] * spec.get("r_hot_factor", 1.0)   # resistencia en caliente (conservador)
        self.I0 = spec["i0_a"]
        self.i_max = spec["i_max_a"]
        self.p_max = spec["p_max_w"]
        self.mass = spec["mass_kg"]
        self.rth = spec["rth_k_w"]
        self.tau = spec["tau_th_s"]
        self.t_max = spec["t_winding_max_c"]
        self.kv_rad = self.kv * 2 * math.pi / 60
        self.kt = 1.0 / self.kv_rad

    def op_point(self, n_m_rps: float, Q_m: float, V_bat: float, eta_esc: float) -> dict:
        w = 2 * math.pi * n_m_rps
        I = Q_m / self.kt + self.I0 if Q_m > 0 else self.I0
        Vm = w / self.kv_rad + I * self.R
        Pmech = Q_m * w
        Pel = Vm * I
        Pbat = Pel / eta_esc
        return {
            "n_m_rpm": n_m_rps * 60, "Q_m": Q_m, "I_m": I, "V_m": Vm,
            "P_mech": Pmech, "P_elec": Pel, "P_bat": Pbat, "I_bat": Pbat / V_bat,
            "duty": Vm / V_bat, "eta_m": Pmech / Pel if Pel > 0 else 0.0,
            "P_loss_motor": Pel - Pmech, "P_loss_esc": Pbat - Pel,
        }

    def time_to_limit_s(self, P_loss: float, T_amb: float) -> float:
        """Tiempo hasta alcanzar t_winding_max desde T_amb (∞ si nunca llega)."""
        dT_inf = self.rth * P_loss
        lim = self.t_max - T_amb
        if dT_inf <= lim:
            return math.inf
        return -self.tau * math.log(1 - lim / dT_inf)

    def steady_temp(self, P_loss: float, T_amb: float) -> float:
        return T_amb + self.rth * P_loss
