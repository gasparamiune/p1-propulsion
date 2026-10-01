"""Cadena de propulsión completa: R(v) → empuje → hélice → correa → motor → ESC → batería."""
from __future__ import annotations

import math

import numpy as np

from . import hydro
from .motor import Motor
from .prop import Propeller

DUTY_MAX = 0.95          # [ESTIMADO: ciclo útil máximo práctico del VESC]


class Drive:
    """Selección concreta de componentes."""

    def __init__(self, inp: dict, z_motor: int, z_shaft: int, battery_key: str,
                 prop_key: str | None = None):
        self.inp = inp
        pk = prop_key or inp["propeller"]["chosen"]
        p = inp["propeller"]["options"][pk]
        self.prop = Propeller(p["D_mm"] / 1000, p["P_mm"] / 1000, p["Z"], p["BAR"], pk,
                              inp["propeller"].get("efficiency_factor", 1.0))
        mk = inp["motor"]["chosen"]
        self.motor = Motor(inp["motor"]["options"][mk], mk)
        ek = inp["esc"]["chosen"]
        self.esc = inp["esc"]["options"][ek]
        self.bat_key = battery_key
        self.bat = inp["battery"]["options"][battery_key]
        self.z_motor, self.z_shaft = z_motor, z_shaft
        self.ratio = z_shaft / z_motor
        dt = inp["drivetrain"]
        self.eta_tr = dt["eta_belt"] * dt["eta_bearings"]
        self.theta = math.radians(inp["architecture"]["shaft_angle_deg"])
        pr = inp["propeller"]
        self.w, self.t = pr["wake_fraction"], pr["thrust_deduction"]
        self.guard_loss = pr["guard"]["thrust_loss_frac"]
        self.rho = inp["water"]["density_kg_m3"]
        self.i_lim = inp["motor"]["current_limit_a"]
        self.i_bat_lim = min(self.bat["i_cont_a"], self.esc["i_cont_a"])

    # ------------------------------------------------------------------
    def shaft_thrust_required(self, R: float) -> float:
        """Empuje a lo largo del eje para vencer R (incl. deducción, ángulo, protector)."""
        return R / ((1 - self.t) * math.cos(self.theta) * (1 - self.guard_loss))

    def at_speed(self, V: float, R: float, V_bat: float) -> dict:
        Ts = self.shaft_thrust_required(R)
        Va = V * (1 - self.w) * math.cos(self.theta)
        pp = self.prop.solve_for_thrust(Ts, Va, self.rho)
        n_m = pp["n"] * self.ratio
        Q_m = pp["Q"] / (self.ratio * self.eta_tr)
        op = self.motor.op_point(n_m, Q_m, V_bat, self.esc["eta"])
        ok = self.feasible(op)
        return {"V": V, "R": R, "T_shaft": Ts, "Va": Va, "prop": pp, **op,
                "P_eff": R * V, "eta_total": (R * V / op["P_bat"]) if op["P_bat"] > 0 else 0,
                "feasible": ok}

    def feasible(self, op: dict) -> bool:
        return (op["duty"] <= DUTY_MAX and op["I_m"] <= self.i_lim
                and op["I_bat"] <= self.i_bat_lim and op["P_mech"] <= self.motor.p_max)

    def limiter(self, op: dict) -> str:
        lim = []
        if op["duty"] > DUTY_MAX:
            lim.append("tensión (duty)")
        if op["I_m"] > self.i_lim:
            lim.append("corriente de motor")
        if op["I_bat"] > self.i_bat_lim:
            lim.append("corriente de batería/ESC")
        if op["P_mech"] > self.motor.p_max:
            lim.append("potencia del motor")
        return ", ".join(lim) or "—"

    def bollard(self, V_bat: float, current_frac: float = 1.0) -> dict:
        """Empuje estático máximo: aumenta rpm hasta que se activa un límite."""
        i_lim = self.i_lim * current_frac
        lo, hi = 1.0, 80.0
        best = None
        for _ in range(45):
            n = 0.5 * (lo + hi)
            pp = self.prop.at_rpm(n, 0.0, self.rho)
            op = self.motor.op_point(n * self.ratio, pp["Q"] / (self.ratio * self.eta_tr),
                                     V_bat, self.esc["eta"])
            ok = (op["duty"] <= DUTY_MAX and op["I_m"] <= i_lim
                  and op["I_bat"] <= self.i_bat_lim and op["P_mech"] <= self.motor.p_max)
            if ok:
                lo, best = n, (pp, op)
            else:
                hi = n
        pp, op = best
        T_h = pp["T"] * math.cos(self.theta)            # componente horizontal
        return {"T_shaft": pp["T"], "T_horiz": T_h, "n_prop_rpm": pp["n"] * 60,
                "Q_prop": pp["Q"], **op, "limiter": self.limiter_relaxed(op, i_lim)}

    def limiter_relaxed(self, op, i_lim):
        tags = []
        if op["duty"] > DUTY_MAX * 0.99:
            tags.append("tensión (duty)")
        if op["I_m"] > i_lim * 0.99:
            tags.append("corriente de motor")
        if op["I_bat"] > self.i_bat_lim * 0.99:
            tags.append("corriente de batería/ESC")
        if op["P_mech"] > self.motor.p_max * 0.99:
            tags.append("potencia del motor")
        return ", ".join(tags) or "—"

    def max_speed(self, mass: float, V_bat: float, band: str = "design", **kw) -> dict:
        """Velocidad máxima alcanzable (búsqueda en V)."""
        lo, hi = 0.3, 6.0
        best = None
        for _ in range(32):
            V = 0.5 * (lo + hi)
            R = _R(self.inp, mass, V, band, **kw)
            try:
                st = self.at_speed(V, R, V_bat)
            except ValueError:
                hi = V
                continue
            if st["feasible"]:
                lo, best = V, st
            else:
                hi = V
        if best is None:
            return {"V": 0.0, "feasible": False}
        # limitante al pasar apenas por encima
        V2 = best["V"] * 1.01
        st2 = self.at_speed(V2, _R(self.inp, mass, V2, band, **kw), V_bat)
        best["limiter"] = self.limiter(st2)
        return best


def _R(inp, mass, V, band, **kw):
    res = hydro.resistance(inp, mass, V, **kw)
    key = {"high": "R_high", "low": "R_low", "nominal": "R",
           "design": {"high": "R_high", "low": "R_low", "nominal": "R"}[inp["resistance"]["design_band"]]}[band]
    return float(res[key][0])


R_at = _R
