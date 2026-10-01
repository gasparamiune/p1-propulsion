"""Modelo de hélice de paso fijo + cavitación.

Dos niveles:
  1. `Propeller` — curvas KT(J), KQ(J) de la hélice concreta (comprada). Dentro del rango de
     valididad (2 ≤ Z ≤ 7, 0,30 ≤ AE/A0 ≤ 1,05, 0,5 ≤ P/D ≤ 1,4) se usan los polinomios
     Wageningen B-series de `p1calc/bseries_coeffs.json` (Oosterveld & van Oossanen,
     transcritos de Bernitsas, Ray & Kinley 1981 y verificados término a término en
     research/R09 §2.1). Fuera de rango (p. ej. hélices de trolling con P/D ≈ 0,4) se usa una
     aproximación lineal calibrada contra esos polinomios (research/R09 §2.1) [ESTIMADO]:
         KT = KT0·(1 − J/J_T0) ,  KQ = KQ0·(1 − J/J_Q0)
         KT0 = 0,40·(P/D),  J_T0 = 1,10·P/D,  J_Q0 = 1,20·P/D
         KQ0 = KT0^1.5 / (√(π/2)·2π·FOM_b),  FOM_b = 0,72 − 0,18·P/D (0,63 a P/D 0,6 … 0,50 a 1,2)
     En ambos casos η0 efectivo = efficiency_factor·η0 (Rn real 6–8·10⁵ < 2·10⁶ y rugosidad:
     0,93–0,98 según la corrección ITTC-78 de Holtrop, research/R09 §2.2).
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

A_T_LINEAR = 0.40        # [VERIFICADO: research/R09 §2.1 — KT0/(P/D) = 0,389–0,406 en B3-50]
JT0_LINEAR = 1.10        # [VERIFICADO: research/R09 §2.1 — KT = 0 en J ≈ 1,08–1,125·P/D]
JQ0_LINEAR = 1.20        # [ESTIMADO: KQ se anula algo después que KT]


def fom_bollard(pd: float) -> float:
    """Figura de mérito en punto fijo de B3-50 en función de P/D [ajuste lineal de research/R09 §2.1]."""
    return 0.72 - 0.18 * pd


def bseries_valid(Z, BAR, PD, coef) -> bool:
    v = coef.get("validity", {"Z": [2, 7], "BAR": [0.30, 1.05], "PD": [0.5, 1.4]})
    return v["Z"][0] <= Z <= v["Z"][1] and v["BAR"][0] <= BAR <= v["BAR"][1] and v["PD"][0] <= PD <= v["PD"][1]


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
                coef = json.load(f)
            if bseries_valid(Z, BAR, self.PD, coef):
                self._bs = coef
        self.model = ("B-series (Oosterveld & van Oossanen) [VERIFICADO: research/R09]" if self._bs else
                      "lineal calibrada a B-series, fuera del rango de la serie [ESTIMADO]")
        # parámetros del modelo lineal
        self.KT0 = A_T_LINEAR * self.PD
        self.JT0 = JT0_LINEAR * self.PD
        self.JQ0 = JQ0_LINEAR * self.PD
        self.KQ0 = self.KT0**1.5 / (math.sqrt(math.pi / 2) * 2 * math.pi * fom_bollard(self.PD))

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


BURRILL_SIGMA = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00, 1.50, 2.00, 3.00]
BURRILL_TAU_5 = [0.066, 0.118, 0.155, 0.181, 0.201, 0.218, 0.243, 0.260, 0.286, 0.301, 0.320]
# [VERIFICADO: research/R09 §3.2 — curva de 5 % de cavitación en la cara de succión, digitalizada de
#  Carlton (2012) fig. 9.21 en el repositorio NAVALARCHITECTURE-POP]


def burrill_tau_limit(sigma: float) -> float:
    """Límite de Burrill (5 % de cavitación en la cara de succión) por interpolación de la
    curva digitalizada; fuera de la tabla se toma el extremo (conservador para σ > 3)."""
    return float(np.interp(sigma, BURRILL_SIGMA, BURRILL_TAU_5))


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
