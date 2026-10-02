"""Modelo DC equivalente del BLDC + ESC, punto de operación y térmico.

    KV_rad = KV·2π/60 [rad/s/V] ;  Kt = 1/KV_rad [N·m/A]  (corriente de CC equivalente)
    I   = Q_m/Kt + I0
    FOC (VESC): el límite l_current_max es sobre la amplitud de I_q; par = 1,5·pp·λ·I_q.
      Convención "bus_foc" [SUPUESTO]: KV de catálogo referido a la tensión de bus (rpm en vacío =
      KV·V_bus) → λ·pp = 1/(√3·KV_rad) → Kt_FOC = (√3/2)/KV_rad ; I_q = I·Kt/Kt_FOC = I/0,866.
      Convención "dc": Kt_FOC = Kt (I_q = I). Si la opción del motor trae `flux_linkage_wb` (λ medido
      con VESC Tool), Kt_FOC = 1,5·pp·λ y manda sobre la convención.
    V_m = ω_m/KV_rad + I·R
    P_elec = V_m·I ;  P_bat = P_elec/η_ESC ;  I_bat = P_bat/V_bat ; duty = V_m/V_bat

Térmico (1 nodo): T(t) = T_amb + R_th·P_loss·(1 − e^(−t/τ))
"""
from __future__ import annotations

import math


class Motor:
    def __init__(self, spec: dict, name: str = "", kt_convention: str = "bus_foc"):
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
        self.pole_pairs = spec.get("pole_pairs")
        lam = spec.get("flux_linkage_wb")
        if lam and self.pole_pairs:
            self.kt_foc, self.kt_basis = 1.5 * self.pole_pairs * lam, "λ medido (1,5·pp·λ)"
        elif kt_convention == "bus_foc":
            self.kt_foc, self.kt_basis = (math.sqrt(3) / 2) / self.kv_rad, "KV referido al bus: (√3/2)/KV_rad"
        elif kt_convention == "dc":
            self.kt_foc, self.kt_basis = self.kt, "KV de CC equivalente: 1/KV_rad"
        else:
            raise ValueError(f"kt_convention desconocida: {kt_convention}")
        self.iq_factor = self.kt / self.kt_foc

    def op_point(self, n_m_rps: float, Q_m: float, V_bat: float, eta_esc: float) -> dict:
        w = 2 * math.pi * n_m_rps
        I = Q_m / self.kt + self.I0 if Q_m > 0 else self.I0
        Vm = w / self.kv_rad + I * self.R
        Pmech = Q_m * w
        Pel = Vm * I
        Pbat = Pel / eta_esc
        return {
            "n_m_rpm": n_m_rps * 60, "Q_m": Q_m, "I_m": I, "I_q": I * self.iq_factor, "V_m": Vm,
            "P_mech": Pmech, "P_elec": Pel, "P_bat": Pbat, "I_bat": Pbat / V_bat,
            "duty": Vm / V_bat, "eta_m": Pmech / Pel if Pel > 0 else 0.0,
            "P_loss_motor": Pel - Pmech, "P_loss_esc": Pbat - Pel,
        }

    def time_to_limit_s(self, P_loss: float, T_amb: float, T0: float | None = None) -> float:
        """Tiempo hasta alcanzar t_winding_max partiendo de T0 (por defecto T_amb); ∞ si nunca llega.
        Modelo de un nodo: T(t) = T∞ + (T0 − T∞)·e^(−t/τ), T∞ = T_amb + R_th·P."""
        T0 = T_amb if T0 is None else T0
        T_inf = T_amb + self.rth * P_loss
        if T_inf <= self.t_max:
            return math.inf
        if T0 >= self.t_max:
            return 0.0
        return -self.tau * math.log((T_inf - self.t_max) / (T_inf - T0))

    def steady_temp(self, P_loss: float, T_amb: float) -> float:
        return T_amb + self.rth * P_loss
