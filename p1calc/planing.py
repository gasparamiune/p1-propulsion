"""Resistencia al avance del jet boat: desplazamiento → joroba → planeo.

Tramos (Fn∇ = V/√(g·∇^⅓)):
  • Planeo (Fn∇ ≥ fn_planing): Savitsky 1964 con `openplaning` (equilibrio de trimado,
    fricción ITTC-57 + rugosidad, aire). Verificado contra R10b §4.4.
  • Desplazamiento y joroba (Fn∇ ≤ fn_hump): R/Δ = r_hump·(Fn∇/fn_hump)^k  [ESTIMADO:
    banda de Savitsky 2003 ×1–2 para cascos rechonchos, R10b §4.4].
  • Transición (fn_hump < Fn∇ < fn_planing): interpolación monótona (PCHIP) entre la joroba
    y el primer punto de planeo.
La incertidumbre se lleva como bandas (low / nominal / high) sobre r_hump y sobre el planeo.
"""
from __future__ import annotations

import math
import warnings
from functools import lru_cache

import numpy as np
from scipy.interpolate import PchipInterpolator

G = 9.81


def fn_vol(V, mass_kg, rho):
    vol = mass_kg / rho
    return np.asarray(V) / math.sqrt(G * vol ** (1 / 3))


@lru_cache(maxsize=4096)
def _savitsky(V, mass_kg, b, lcg, vcg, r_g, beta, vT, rho, nu, l_air, h_air, b_air, cd_air, ahr):
    from openplaning import PlaningBoat
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        boat = PlaningBoat(V, mass_kg * G, b, lcg, vcg, r_g, beta, 0.0, vT, 0.0, ahr=ahr,
                           l_air=l_air, h_air=h_air, b_air=b_air, C_shape=1.0, C_D=cd_air,
                           rho=rho, nu=nu)
        boat.get_steady_trim()
        boat.get_forces()
    R = float(boat.net_force[0])
    return {"R": R, "tau_deg": float(boat.tau), "R_pressure": float(boat.hydrodynamic_force[0]),
            "R_friction": float(boat.skin_friction[0]), "R_air": float(boat.air_resistance[0]),
            "valid": 0.5 < boat.tau < 34.5 and R > 0}


def savitsky(inp: dict, mass_kg: float, lcg_m: float, vcg_m: float, V: float) -> dict:
    h, w, r = inp["boat"], inp["water"], inp["resistance"]
    return _savitsky(round(float(V), 4), round(mass_kg, 2), h["planing_beam_m"], round(lcg_m, 4),
                     round(vcg_m, 4), r["radius_gyration_m"], h["deadrise_deg"], r["thrust_height_m"],
                     w["density_kg_m3"], w["kinematic_viscosity_m2_s"], r["air_center_m"],
                     r["air_height_m"], r["air_width_m"], r["air_cd"], r["hull_roughness_m"])


class Resistance:
    """R(V) para una masa y un centro de gravedad dados. Llamable con V [m/s] y banda."""

    def __init__(self, inp: dict, mass_kg: float, lcg_m: float, vcg_m: float):
        self.inp, self.m, self.lcg, self.vcg = inp, mass_kg, lcg_m, vcg_m
        r = inp["resistance"]
        self.rho = inp["water"]["density_kg_m3"]
        self.W = mass_kg * G
        self.vref = math.sqrt(G * (mass_kg / self.rho) ** (1 / 3))     # V para Fn∇ = 1
        self.fn_h, self.fn_p, self.k = r["fn_hump"], r["fn_planing"], r["hump_exponent"]
        self.r_hump = r["r_hump"]                       # dict low/nominal/high
        self.pl_band = r["planing_band"]                # dict low/nominal/high (factor)
        # puntos de planeo (nominal) desde fn_planing hasta la velocidad máxima de interés
        Vp = np.linspace(self.fn_p * self.vref, max(r["v_max_eval_ms"], self.fn_p * self.vref * 1.5), 14)
        pts = [savitsky(inp, mass_kg, lcg_m, vcg_m, float(v)) for v in Vp]
        ok = [i for i, p in enumerate(pts) if p["valid"]]
        if not ok:
            raise RuntimeError("Savitsky sin solución válida en el rango de planeo")
        self.Vp = Vp[ok[0]:]
        self.Rp = np.array([pts[i]["R"] for i in range(ok[0], len(pts))])
        self.tau = np.array([pts[i]["tau_deg"] for i in range(ok[0], len(pts))])
        self.planing = [pts[i] for i in range(ok[0], len(pts))]
        self._interp = {}

    def _curve(self, band: str):
        if band in self._interp:
            return self._interp[band]
        Vh = self.fn_h * self.vref
        Rh = self.r_hump[band] * self.W
        Vlow = np.linspace(0.0, Vh, 12)
        Rlow = Rh * (Vlow / Vh) ** self.k
        Vpl = self.Vp
        Rpl = self.Rp * self.pl_band[band]
        # la transición no puede bajar de lo que da el planeo al inicio: tomamos máx. (joroba ≥ planeo)
        V = np.concatenate([Vlow, Vpl])
        R = np.concatenate([Rlow, Rpl])
        f = PchipInterpolator(V, R, extrapolate=True)
        self._interp[band] = f
        return f

    def __call__(self, V, band: str = "nominal"):
        V = np.asarray(V, dtype=float)
        return np.maximum(self._curve(band)(V), 0.0)

    def regime(self, V: float) -> str:
        fn = V / self.vref
        return "desplazamiento/joroba" if fn <= self.fn_h else ("transición" if fn < self.fn_p else "planeo")
