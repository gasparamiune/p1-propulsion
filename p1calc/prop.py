"""Modelo de hélice de paso fijo + cavitación.

Dos niveles:
  1. `Propeller` — curvas KT(J), KQ(J) de la hélice concreta (comprada). Si existe
     `p1calc/bseries_coeffs.json` (polinomios Wageningen B-series de Oosterveld &
     van Oossanen 1975, verificados), se usan; si no, una aproximación lineal
     calibrada a valores típicos B-series de 3 palas [ESTIMADO]:
         KT = KT0·(1 − J/J_T0) ,  KQ = KQ0·(1 − J/J_Q0)
         KT0 = a_T·(P/D),  J_T0 = 1.05·P/D,  J_Q0 = 1.15·P/D
         KQ0 = KT0^1.5 / (√(π/2)·2π·FOM_b)    (FOM_b = figura de mérito en bollard)
  2. Disco actuador (momento) para el límite ideal y para comparar arquitecturas:
         η_i = 2 / (1 + √(1 + C_T)),  C_T = T / (½ ρ Va² A0)

Convenciones: n [rev/s], D [m], Va velocidad de avance [m/s], T [N], Q [N·m].
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

_COEF = Path(__file__).with_name("bseries_coeffs.json")

A_T_LINEAR = 0.38        # [ESTIMADO: KT0 ≈ 0.38·P/D para B3 con AE/A0≈0.45–0.5]
FOM_BOLLARD = 0.60       # [ESTIMADO: figura de mérito típica de hélice abierta en bollard]


class Propeller:
    def __init__(self, D_m: float, P_m: float, Z: int, BAR: float, name: str = "",
                 efficiency_factor: float = 1.0):
        self.D, self.P, self.Z, self.BAR, self.name = D_m, P_m, Z, BAR, name
        self.k_eta = efficiency_factor      # η0 efectivo = k_eta·η0 (KQ / k_eta)
        self.PD = P_m / D_m
        self.A0 = math.pi * D_m**2 / 4
        self._bs = None
        if _COEF.exists():
            with open(_COEF) as f:
                self._bs = json.load(f)
        self.model = "B-series (Oosterveld & van Oossanen 1975)" if self._bs else "lineal aproximada [ESTIMADO]"
        # parámetros del modelo lineal
        self.KT0 = A_T_LINEAR * self.PD
        self.JT0 = 1.05 * self.PD
        self.JQ0 = 1.15 * self.PD
        self.KQ0 = self.KT0**1.5 / (math.sqrt(math.pi / 2) * 2 * math.pi * FOM_BOLLARD)

    # --- coeficientes ---------------------------------------------------------
    def kt(self, J):
        J = np.asarray(J, dtype=float)
        if self._bs:
            return np.maximum(_poly(self._bs["KT"], J, self.PD, self.BAR, self.Z), 0.0)
        return np.maximum(self.KT0 * (1 - J / self.JT0), 0.0)

    def kq(self, J):
        J = np.asarray(J, dtype=float)
        if self._bs:
            return np.maximum(_poly(self._bs["KQ"], J, self.PD, self.BAR, self.Z), 1e-6) / self.k_eta
        return np.maximum(self.KQ0 * (1 - J / self.JQ0), 1e-6) / self.k_eta

    def eta0(self, J):
        J = np.asarray(J, dtype=float)
        return J * self.kt(J) / (2 * math.pi * self.kq(J))

    # --- punto de operación -----------------------------------------------------
    def solve_for_thrust(self, T_req: float, Va: float, rho: float) -> dict:
        """Busca n tal que T(n, Va) = T_req. Devuelve n, J, Q, P_D, η0."""
        D = self.D
        if T_req <= 0:
            return {"n": 0.0, "J": 0.0, "T": 0.0, "Q": 0.0, "PD": 0.0, "eta0": 0.0}

        def thrust(n):
            J = Va / (n * D)
            return float(self.kt(J)) * rho * n**2 * D**4

        lo = max(Va / (self.JT0 * D) * 1.0001, 0.05) if Va > 0 else 0.05
        hi = lo * 2 + 5
        while thrust(hi) < T_req:
            hi *= 1.5
            if hi > 500:
                raise ValueError("hélice: empuje inalcanzable")
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            if thrust(mid) < T_req:
                lo = mid
            else:
                hi = mid
        n = 0.5 * (lo + hi)
        J = Va / (n * D)
        Q = float(self.kq(J)) * rho * n**2 * D**5
        PD = 2 * math.pi * n * Q
        return {"n": n, "J": J, "T": T_req, "Q": Q, "PD": PD,
                "eta0": (T_req * Va / PD) if PD > 0 else 0.0}

    def at_rpm(self, n: float, Va: float, rho: float) -> dict:
        D = self.D
        J = Va / (n * D) if n > 0 else 0.0
        T = float(self.kt(J)) * rho * n**2 * D**4
        Q = float(self.kq(J)) * rho * n**2 * D**5
        return {"n": n, "J": J, "T": T, "Q": Q, "PD": 2 * math.pi * n * Q}

    # --- cavitación -------------------------------------------------------------
    def keller_min_bar(self, T: float, h_shaft_m: float, water: dict, K: float = 0.2) -> float:
        """Área expandida mínima (Keller): AE/A0 = (1.3+0.3Z)·T/((p0+ρgh−pv)·D²) + K."""
        rho = water["density_kg_m3"]
        p = water["p_atm_pa"] + rho * 9.81 * h_shaft_m - water["vapor_pressure_pa"]
        return (1.3 + 0.3 * self.Z) * T / (p * self.D**2) + K

    def burrill(self, T: float, n: float, Va: float, h_shaft_m: float, water: dict) -> dict:
        """Índices de Burrill: σ_0.7R y τ_c (carga de empuje sobre área proyectada)."""
        rho = water["density_kg_m3"]
        p = water["p_atm_pa"] + rho * 9.81 * h_shaft_m - water["vapor_pressure_pa"]
        VR2 = Va**2 + (0.7 * math.pi * n * self.D) ** 2
        sigma = p / (0.5 * rho * VR2)
        AD = self.BAR * self.A0
        AP = AD * (1.067 - 0.229 * self.PD)
        tau = T / (0.5 * rho * VR2 * AP)
        return {"sigma07": sigma, "tau_c": tau, "AP_m2": AP}


def burrill_tau_limit(sigma: float) -> float:
    """Límite de Burrill para ~2.5 % de cavitación en la cara de succión (buques
    mercantes). Ajuste τ_c,lim = 0.3·σ^0.6 válido aprox. para 0.2 < σ < 2.
    [ESTIMADO: ajuste aproximado del diagrama; ver 02_calculos.md, a verificar]"""
    return 0.3 * max(sigma, 1e-6) ** 0.6


def actuator_disk_eta(T: float, Va: float, D: float, rho: float) -> float:
    A = math.pi * D**2 / 4
    if Va <= 0:
        return 0.0
    CT = T / (0.5 * rho * Va**2 * A)
    return 2.0 / (1.0 + math.sqrt(1.0 + CT))


def actuator_disk_bollard_power(T: float, D: float, rho: float) -> float:
    """Potencia ideal en bollard: P = T^1.5 / √(2ρA)."""
    A = math.pi * D**2 / 4
    return T**1.5 / math.sqrt(2 * rho * A)


def _poly(terms, J, PD, BAR, Z):
    """Σ C·J^s·(P/D)^t·(AE/A0)^u·Z^v  — formato [[C, s, t, u, v], ...]."""
    out = np.zeros_like(np.asarray(J, dtype=float))
    for C, s, t, u, v in terms:
        out = out + C * J**s * PD**t * BAR**u * Z**v
    return out
