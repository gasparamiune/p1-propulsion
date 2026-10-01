"""Waterjet: cantidad de movimiento + bomba axial con característica fuera de diseño + motor.

Sistema (por unidad de peso, alturas en m):
    V_in  = V·(1 − w)                                   flujo que entra por la toma
    V_j   = Q/(C_c·A_n)                                 chorro en la vena contracta
    H_sys = (1 + K_n)·V_j²/2g − η_in·V_in²/2g + K_g·V_g²/2g + h_j
    T     = ρ·Q·(V_j − V_in)·(1 − t)                    empuje neto (t: deducción)
Bomba (impulsor axial, diámetro D, cubo ν·D):
    U = π·D·n ;  φ = Q/(A_an·U) ;  ψ = g·H/U²
    ψ(φ) = ψ_d·[1 + s·(1 − φ/φ_d)]        (s = ψ_cierre/ψ_d − 1)        [ESTIMADO: R12]
    η(φ) = η_d·[1 − c·(φ/φ_d − 1)²]                                       [ESTIMADO: R12]
    P_eje = ρ·g·Q·H/η ;  Ω_s = ω·√Q/(g·H)^¾
Cavitación (entrada del impulsor):
    NPSH_a = (p_atm − p_v)/(ρg) + h_sum + η_in·V_in²/2g − K_g·V_g²/2g
    S = ω·√Q/(g·NPSH_a)^¾  (velocidad específica de succión, adimensional) ≤ S_lim
    σ_punta = NPSH_a·2g/W_t² ,  W_t² = U² + c_m²
El impulsor se diseña (ángulos de álabe) para el punto de diseño (V_d, P_d, n_d): ver pump_design().
"""
from __future__ import annotations

import math

import numpy as np

G = 9.81


class JetGeometry:
    def __init__(self, inp: dict, D_imp_m: float, D_noz_m: float, h_sub_m: float = 0.0):
        j = inp["waterjet"]
        self.inp = inp
        self.D = D_imp_m
        self.nu_hub = j["hub_ratio"]
        self.A_an = math.pi / 4 * D_imp_m ** 2 * (1 - self.nu_hub ** 2)
        self.D_n = D_noz_m
        self.A_n = math.pi / 4 * D_noz_m ** 2
        self.Cc = j["nozzle_cc"]
        self.Kn = j["nozzle_loss_k"]
        self.eta_in = j["intake_eta"]
        self.Kg = j["grille_k"]
        self.A_g = j["grille_open_area_m2_per_Aimp"] * math.pi / 4 * D_imp_m ** 2
        self.h_j = j["nozzle_height_above_wl_m"]
        self.h_sub = h_sub_m                       # eje del impulsor bajo la flotación (estático)
        self.w = j["wake_fraction"]
        self.t = j["thrust_deduction"]
        w = inp["water"]
        self.rho = w["density_kg_m3"]
        self.p_atm = inp["air"]["pressure_pa"]
        self.p_v = w["vapor_pressure_pa"]

    def H_sys(self, Q, V):
        Vj = Q / (self.Cc * self.A_n)
        Vin = V * (1 - self.w)
        Vg = Q / self.A_g
        return (1 + self.Kn) * Vj ** 2 / (2 * G) - self.eta_in * Vin ** 2 / (2 * G) + self.Kg * Vg ** 2 / (2 * G) + self.h_j

    def thrust(self, Q, V):
        Vj = Q / (self.Cc * self.A_n)
        return self.rho * Q * (Vj - V * (1 - self.w)) * (1 - self.t)

    def npsh_a(self, Q, V):
        Vin = V * (1 - self.w)
        Vg = Q / self.A_g
        return ((self.p_atm - self.p_v) / (self.rho * G) + self.h_sub + self.eta_in * Vin ** 2 / (2 * G)
                - self.Kg * Vg ** 2 / (2 * G))

    def Q_for_hydraulic_power(self, P_h, V):
        """Caudal tal que ρ·g·Q·H_sys(Q) = P_h (monótona creciente en Q)."""
        lo, hi = 1e-6, 1.0
        for _ in range(80):
            q = 0.5 * (lo + hi)
            if self.rho * G * q * self.H_sys(q, V) < P_h:
                lo = q
            else:
                hi = q
        return 0.5 * (lo + hi)


class Pump:
    """Impulsor diseñado para el punto (V_d, P_eje_d, n_d) con la característica de JetGeometry."""

    def __init__(self, geo: JetGeometry, V_d: float, P_shaft_d: float, n_d_rps: float):
        j = geo.inp["waterjet"]["pump"]
        self.geo = geo
        self.eta_d = j["eta_design"]
        self.s = j["shutoff_slope"]
        self.c = j["eta_curvature"]
        self.eta_min = j["eta_min"]
        self.n_d = n_d_rps
        P_h = self.eta_d * P_shaft_d
        self.Q_d = geo.Q_for_hydraulic_power(P_h, V_d)
        self.H_d = geo.H_sys(self.Q_d, V_d)
        self.U_d = math.pi * geo.D * n_d_rps
        self.phi_d = self.Q_d / (geo.A_an * self.U_d)
        self.psi_d = G * self.H_d / self.U_d ** 2
        w = 2 * math.pi * n_d_rps
        self.omega_s = w * math.sqrt(self.Q_d) / (G * self.H_d) ** 0.75
        self.V_d, self.P_d = V_d, P_shaft_d

    def psi(self, phi):
        return self.psi_d * (1 + self.s * (1 - phi / self.phi_d))

    def eta(self, phi):
        return max(self.eta_d * (1 - self.c * (phi / self.phi_d - 1) ** 2), self.eta_min)

    def operate(self, n_rps: float, V: float) -> dict:
        """Punto de funcionamiento a n y V: intersección bomba–sistema."""
        g = self.geo
        U = math.pi * g.D * n_rps
        phi_max = self.phi_d * (1 + 1 / self.s)
        lo, hi = 1e-6, phi_max
        for _ in range(70):
            ph = 0.5 * (lo + hi)
            Q = ph * g.A_an * U
            if self.psi(ph) * U ** 2 / G > g.H_sys(Q, V):
                lo = ph
            else:
                hi = ph
        ph = 0.5 * (lo + hi)
        Q = ph * g.A_an * U
        H = self.psi(ph) * U ** 2 / G
        eta = self.eta(ph)
        P = g.rho * G * Q * H / eta
        w = 2 * math.pi * n_rps
        Vj = Q / (g.Cc * g.A_n)
        T = g.thrust(Q, V)
        npsh = g.npsh_a(Q, V)
        S = w * math.sqrt(Q) / (G * max(npsh, 1e-3)) ** 0.75
        cm = Q / g.A_an
        sig_tip = npsh * 2 * G / (U ** 2 + cm ** 2)
        Vin = V * (1 - g.w)
        P_thrust = T * V
        return {"n_rpm": n_rps * 60, "U_tip": U, "phi": ph, "psi": self.psi(ph), "eta_pump": eta,
                "Q_m3s": Q, "H_m": H, "P_shaft": P, "torque": P / w, "Vj": Vj, "T": T,
                "IVR": (Q / (g.A_an)) / max(V, 1e-6) if V > 0.1 else math.inf,
                "Vj_over_V": Vj / max(V, 1e-6), "NPSHa": npsh, "S": S, "sigma_tip": sig_tip,
                "eta_jet": P_thrust / P if P > 0 else 0.0, "V_in": Vin}

    def design_report(self) -> dict:
        """Triángulos de velocidad en cubo, medio y punta (torbellino libre, entrada sin giro)."""
        g = self.geo
        cm = self.Q_d / g.A_an
        dH = self.H_d / self.eta_d               # altura teórica (Euler)
        w = 2 * math.pi * self.n_d
        rows = {}
        for name, r in (("cubo", g.nu_hub * g.D / 2), ("medio", math.sqrt((1 + g.nu_hub ** 2) / 2) * g.D / 2),
                        ("punta", g.D / 2)):
            u = w * r
            cu2 = G * dH / u                         # torbellino libre: r·cu = cte
            b1 = math.degrees(math.atan2(cm, u))
            b2 = math.degrees(math.atan2(cm, u - cu2)) if u > cu2 else 90.0
            a2 = math.degrees(math.atan2(cm, cu2))   # ángulo de entrada al estator (desde tangencial)
            rows[name] = {"r_mm": r * 1000, "u": u, "cm": cm, "cu2": cu2, "beta1_deg": b1, "beta2_deg": b2,
                          "turning_deg": b2 - b1, "stator_inlet_deg": a2,
                          "de_haller": math.hypot(cm, u - cu2) / math.hypot(cm, u)}
        return {"Q_d": self.Q_d, "H_d": self.H_d, "phi_d": self.phi_d, "psi_d": self.psi_d,
                "omega_s": self.omega_s, "U_tip_d": self.U_d, "n_d_rpm": self.n_d * 60, "sections": rows}


class JetDrive:
    """Bomba + motor directo + límites del controlador y la batería."""

    def __init__(self, pump: Pump, motor, esc: dict, i_motor_lim: float, i_bat_lim: float,
                 eta_mech: float, duty_max: float):
        self.p, self.m, self.esc = pump, motor, esc
        self.i_lim, self.i_bat_lim = i_motor_lim, i_bat_lim
        self.eta_mech, self.duty_max = eta_mech, duty_max

    def at(self, n_rps, V, V_bat):
        pp = self.p.operate(n_rps, V)
        Qm = pp["torque"] / self.eta_mech
        op = self.m.op_point(n_rps, Qm, V_bat, self.esc["eta"])
        return pp, op

    def feasible(self, op, i_lim=None, p_bat_lim=None):
        i_lim = self.i_lim if i_lim is None else i_lim
        ok = op["duty"] <= self.duty_max and op["I_m"] <= i_lim and op["I_bat"] <= self.i_bat_lim
        if p_bat_lim is not None:
            ok = ok and op["P_bat"] <= p_bat_lim
        return ok

    def full_throttle(self, V, V_bat, i_lim=None, p_bat_lim=None, n_cap_rps=None):
        """Máximas rpm admisibles a velocidad V (límite de duty, corriente, potencia o rpm)."""
        lo, hi = 1.0, 250.0
        best = None
        for _ in range(50):
            n = 0.5 * (lo + hi)
            pp, op = self.at(n, V, V_bat)
            ok = self.feasible(op, i_lim, p_bat_lim) and (n_cap_rps is None or n <= n_cap_rps)
            if ok:
                lo, best = n, (pp, op)
            else:
                hi = n
        pp, op = best
        lim = []
        if op["duty"] > self.duty_max * 0.995:
            lim.append("tensión")
        if op["I_m"] > (self.i_lim if i_lim is None else i_lim) * 0.995:
            lim.append("corriente de motor")
        if op["I_bat"] > self.i_bat_lim * 0.995:
            lim.append("corriente de batería")
        if p_bat_lim is not None and op["P_bat"] > p_bat_lim * 0.995:
            lim.append("potencia")
        if n_cap_rps is not None and lo >= n_cap_rps * 0.995:
            lim.append("tope de rpm")
        return {**pp, **op, "V": V, "limiter": ", ".join(lim) or "—"}

    def for_thrust(self, T_req, V, V_bat):
        """rpm y consumo para dar T_req a velocidad V (crucero estacionario)."""
        lo, hi = 0.5, 250.0
        for _ in range(55):
            n = 0.5 * (lo + hi)
            if self.p.operate(n, V)["T"] < T_req:
                lo = n
            else:
                hi = n
        pp, op = self.at(hi, V, V_bat)
        return {**pp, **op, "V": V, "feasible": self.feasible(op)}
