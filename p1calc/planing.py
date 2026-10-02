"""Resistencia al avance del jet boat: desplazamiento → joroba → planeo.

Tramos (Fn∇ = V/√(g·∇^⅓)):
  • Planeo (Fn∇ ≥ fn_planing): Savitsky 1964 con `openplaning` (equilibrio de trimado,
    fricción ITTC-57 + rugosidad, aire). Verificado contra R10b §4.4 / R12 §6.2.
    Validez de cada punto [VERIFICADO: R12 §6, avisos de openplaning]: 2° ≤ τ ≤ 15°, λ ≤ 4,
    0,60 ≤ C_V ≤ 13, y además L_K ≤ L_wl (la eslora mojada en la quilla no puede superar el fondo
    del casco; Savitsky supone un prisma más largo que la zona mojada).
  • Si el equilibrio libre de Savitsky da L_K > L_wl (casco corto para el peso), el punto NO es
    válido. En su lugar se usa el "Savitsky limitado por eslora" [ESTIMADO: método propio, sin
    validar]: equilibrio vertical con L_K = L_wl (las mismas ecuaciones de Savitsky/openplaning con
    el trimado que hace falta para sostener el peso con esa eslora). El momento de cabeceo no cierra:
    el residuo (proa abajo) lo tomaría la proa mojándose, que no está modelada. La banda en esos
    puntos se ensancha: baja = Savitsky libre × planing_band.low (optimista: casco "más largo"),
    nominal = limitado por eslora, alta = limitado por eslora × planing_band.high.
  • Desplazamiento y joroba (Fn∇ ≤ fn_hump): R/Δ = r_hump·(Fn∇/fn_hump)^k  [ESTIMADO:
    banda de Savitsky 2003 ×1–2 para cascos rechonchos, R10b §4.4].
  • Transición (fn_hump < Fn∇ < fn_planing): interpolación monótona (PCHIP) entre la joroba
    y el primer punto de planeo (el corte fn_planing es [ESTIMADO] y mueve el resultado: va en la
    sensibilidad).
  • Planeo pleno (v_full): primer nodo en que la limitación de eslora deja de pesar (Savitsky libre
    válido, o limitado y libre a menos de full_planing_tol). Hasta ahí se exige el margen de empuje.
La incertidumbre se lleva como bandas (low / nominal / high) sobre r_hump y sobre el planeo.
"""
from __future__ import annotations

import math
import warnings
from functools import lru_cache

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

G = 9.81
TAU_RANGE = (2.0, 15.0)        # [VERIFICADO: R12 §6 / openplaning l. 497–501 — validez de la sustentación]
LAMBDA_MAX = 4.0               # [VERIFICADO: ídem]
CV_RANGE = (0.60, 13.0)        # [VERIFICADO: ídem]


def fn_vol(V, mass_kg, rho):
    vol = mass_kg / rho
    return np.asarray(V) / math.sqrt(G * vol ** (1 / 3))


def _boat(V, mass_kg, b, lcg, vcg, r_g, beta, vT, rho, nu, l_air, h_air, b_air, cd_air, ahr):
    from openplaning import PlaningBoat
    return PlaningBoat(V, mass_kg * G, b, lcg, vcg, r_g, beta, 0.0, vT, 0.0, ahr=ahr,
                       l_air=l_air, h_air=h_air, b_air=b_air, C_shape=1.0, C_D=cd_air,
                       rho=rho, nu=nu)


def _pack(boat, V, b, L_wl):
    R = float(boat.net_force[0])
    tau, lam, LK = float(boat.tau), float(boat.lambda_W), float(boat.L_K)
    cv = V / math.sqrt(G * b)
    flags = {"ok_tau": TAU_RANGE[0] <= tau <= TAU_RANGE[1], "ok_lambda": lam <= LAMBDA_MAX,
             "ok_cv": CV_RANGE[0] <= cv <= CV_RANGE[1], "ok_LK": LK <= L_wl + 1e-6, "ok_R": R > 0}
    return {"R": R, "tau_deg": tau, "R_pressure": float(boat.hydrodynamic_force[0]),
            "R_friction": float(boat.skin_friction[0]), "R_air": float(boat.air_resistance[0]),
            "L_K": LK, "L_C": float(boat.L_C), "lambda": lam, "C_V": cv,
            "T_transom": float(boat.T), "M_residual": float(boat.net_force[2]),
            **flags, "valid": all(flags.values())}


@lru_cache(maxsize=4096)
def _savitsky(V, mass_kg, b, lcg, vcg, r_g, beta, vT, rho, nu, l_air, h_air, b_air, cd_air, ahr, L_wl):
    """Equilibrio libre de Savitsky (fuerza vertical y momento) con openplaning."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        boat = _boat(V, mass_kg, b, lcg, vcg, r_g, beta, vT, rho, nu, l_air, h_air, b_air, cd_air, ahr)
        boat.get_steady_trim()
        boat.get_forces()
    out = _pack(boat, V, b, L_wl)
    out["converged"] = 0.5 < out["tau_deg"] < 34.5 and out["R"] > 0
    return out


@lru_cache(maxsize=4096)
def _savitsky_length_limited(V, mass_kg, b, lcg, vcg, r_g, beta, vT, rho, nu, l_air, h_air, b_air, cd_air,
                             ahr, L_wl):
    """Savitsky con la eslora mojada en la quilla fija en L_wl: se busca el trimado τ que da equilibrio
    vertical (sustentación + componente del empuje = peso); z_wl sale de L_K = L_wl (Faltinsen ec. 9.50,
    la misma que usa openplaning). El momento queda sin cerrar (M_residual) [ESTIMADO: método propio]."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        boat = _boat(V, mass_kg, b, lcg, vcg, r_g, beta, vT, rho, nu, l_air, h_air, b_air, cd_air, ahr)

        def fz(tau):
            t = math.radians(tau)
            boat.tau = tau
            boat.z_wl = (lcg + vcg / math.tan(t) - L_wl) * math.sin(t)
            boat.get_forces()
            return boat.net_force[1]

        try:
            tau = brentq(fz, 1.0, 30.0, xtol=1e-6)
        except ValueError:
            return None
        fz(tau)
    out = _pack(boat, V, b, L_wl)
    out["converged"] = out["R"] > 0
    return out


def _args(inp, mass_kg, lcg_m, vcg_m, V):
    h, w, r = inp["boat"], inp["water"], inp["resistance"]
    return (round(float(V), 4), round(mass_kg, 2), h["planing_beam_m"], round(lcg_m, 4),
            round(vcg_m, 4), r["radius_gyration_m"], h["deadrise_deg"], r["thrust_height_m"],
            w["density_kg_m3"], w["kinematic_viscosity_m2_s"], r["air_center_m"],
            r["air_height_m"], r["air_width_m"], r["air_cd"], r["hull_roughness_m"], h["lwl_m"])


def savitsky(inp: dict, mass_kg: float, lcg_m: float, vcg_m: float, V: float) -> dict:
    return _savitsky(*_args(inp, mass_kg, lcg_m, vcg_m, V))


def savitsky_length_limited(inp: dict, mass_kg: float, lcg_m: float, vcg_m: float, V: float):
    return _savitsky_length_limited(*_args(inp, mass_kg, lcg_m, vcg_m, V))


def planing_point(inp: dict, mass_kg: float, lcg_m: float, vcg_m: float, V: float) -> dict | None:
    """Punto de planeo usado por el modelo: Savitsky libre si es válido; si no, limitado por eslora
    (si ese es válido salvo por L_K, que ahí vale L_wl por construcción). None si no hay ninguno."""
    free = savitsky(inp, mass_kg, lcg_m, vcg_m, V)
    if free["valid"]:
        return {**free, "method": "Savitsky 1964", "R_free": free["R"], "free_valid": True,
                "L_K_free": free["L_K"], "tau_free": free["tau_deg"], "lambda_free": free["lambda"]}
    ll = savitsky_length_limited(inp, mass_kg, lcg_m, vcg_m, V)
    if ll is None or not (ll["ok_tau"] and ll["ok_lambda"] and ll["ok_cv"] and ll["ok_R"]):
        return None
    return {**ll, "method": "Savitsky limitado por eslora", "R_free": free["R"] if free["converged"] else None,
            "free_valid": False, "L_K_free": free["L_K"], "tau_free": free["tau_deg"], "lambda_free": free["lambda"],
            "valid": False}


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
        f_cal = r["planing_factor"]                     # factor de calibración sobre todas las bandas (1 hasta T4)
        self.pl_band = {k: v * f_cal for k, v in r["planing_band"].items()}   # low/nominal/high
        # puntos de planeo desde fn_planing hasta la velocidad máxima de interés
        v0, v1 = self.fn_p * self.vref, max(r["v_max_eval_ms"], self.fn_p * self.vref * 1.5)
        Vp = np.linspace(v0, v1, max(14, int(math.ceil((v1 - v0) / r["planing_node_step_ms"])) + 1))
        pts = [(float(v), planing_point(inp, mass_kg, lcg_m, vcg_m, float(v))) for v in Vp]
        pts = [(v, p) for v, p in pts if p is not None]
        if not pts:
            raise RuntimeError("Savitsky sin solución válida (ni libre ni limitada por eslora) en el rango de planeo")
        self.Vp = np.array([v for v, _ in pts])
        self.planing = [p for _, p in pts]
        self.Rp = np.array([p["R"] for p in self.planing])
        self.tau = np.array([p["tau_deg"] for p in self.planing])
        # banda por punto: en los puntos limitados por eslora la baja es el Savitsky libre (optimista)
        self.Rp_band = {
            "low": np.array([(p["R_free"] if (not p["free_valid"] and p["R_free"]) else p["R"]) * self.pl_band["low"]
                             for p in self.planing]),
            "nominal": self.Rp * self.pl_band["nominal"],
            "high": self.Rp * self.pl_band["high"]}
        self.n_valid = sum(1 for p in self.planing if p["free_valid"])
        vv = [v for v, p in zip(self.Vp, self.planing) if p["free_valid"]]
        self.v_first_valid = float(vv[0]) if vv else None
        # planeo pleno: primer nodo donde la limitación de eslora ya no pesa (Savitsky libre válido, o el
        # limitado difiere del libre en menos de full_planing_tol); si no hay, el último nodo
        tol = r["full_planing_tol"]
        vf = [v for v, p in zip(self.Vp, self.planing)
              if p["free_valid"] or (p["R_free"] and abs(p["R"] - p["R_free"]) / p["R_free"] < tol)]
        self.v_full = float(vf[0]) if vf else float(self.Vp[-1])
        self._interp = {}

    def _curve(self, band: str):
        if band in self._interp:
            return self._interp[band]
        Vh = self.fn_h * self.vref
        Rh = self.r_hump[band] * self.W
        Vlow = np.linspace(0.0, Vh, 12)
        Rlow = Rh * (Vlow / Vh) ** self.k
        V = np.concatenate([Vlow, self.Vp])
        R = np.concatenate([Rlow, self.Rp_band[band]])
        f = PchipInterpolator(V, R, extrapolate=True)
        self._interp[band] = f
        return f

    def __call__(self, V, band: str = "nominal"):
        V = np.asarray(V, dtype=float)
        return np.maximum(self._curve(band)(V), 0.0)

    def regime(self, V: float) -> str:
        fn = V / self.vref
        return "desplazamiento/joroba" if fn <= self.fn_h else ("transición" if fn < self.fn_p else "planeo")

    def h_sub(self, V: float, h_static: float, x_imp_m: float, z_axis_m: float) -> float:
        """Inmersión del eje del impulsor bajo la superficie libre a velocidad V [ESTIMADO]:
        estática hasta la joroba; en planeo, calado del espejo de Savitsky (L_K·sen τ) menos la subida de
        la quilla hasta la cara del impulsor (x·tan τ) menos la altura del eje (z·cos τ); lineal en el medio."""
        Vh = self.fn_h * self.vref
        hs = [p["T_transom"] - x_imp_m * math.tan(math.radians(p["tau_deg"]))
              - z_axis_m * math.cos(math.radians(p["tau_deg"])) for p in self.planing]
        if V <= Vh:
            return h_static
        if V >= self.Vp[0]:
            return float(np.interp(V, self.Vp, hs))
        f = (V - Vh) / (self.Vp[0] - Vh)
        return h_static + f * (hs[0] - h_static)
