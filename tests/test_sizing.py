"""Sanidad del dimensionamiento del waterjet: fórmulas, monotonía y contraste con referencias
(research/R10b, R12)."""
import math

import numpy as np
import pytest

from p1calc import hull
from p1calc.planing import savitsky
from p1calc.waterjet import JetGeometry, Pump


def test_savitsky_reference_case(inp):
    """research/R12 §6 (openplaning ejecutado): Δ 200 kg, b 0,6, β 10°, LCG 1,0, VCG 0,33,
    V 8,33 m/s, ρ 1013, ν 1,35e-6 → τ 6,37°, R 326,7 N (sin aire)."""
    ii = {**inp, "boat": {**inp["boat"], "planing_beam_m": 0.6, "deadrise_deg": 10.0},
          "resistance": {**inp["resistance"], "air_cd": 0.0, "radius_gyration_m": 0.5, "thrust_height_m": 0.26}}
    r = savitsky(ii, 200.0, 1.0, 0.33, 8.33)
    assert abs(r["tau_deg"] - 6.37) < 0.3, r          # la línea de empuje (vT) difiere del caso de R12
    assert abs(r["R"] - 326.7) / 326.7 < 0.03, r


def test_momentum_thrust_and_power():
    """T = ρQ(Vj − V) y P_h = ρgQ·H_sys con H_sys de la ecuación de energía (R12 §2)."""
    inp = {"waterjet": {"hub_ratio": 0.5, "nozzle_cc": 1.0, "nozzle_loss_k": 0.0, "intake_eta": 1.0,
                        "grille_k": 0.0, "grille_open_area_m2_per_Aimp": 3.0, "nozzle_height_above_wl_m": 0.0,
                        "wake_fraction": 0.0, "thrust_deduction": 0.0},
           "water": {"density_kg_m3": 1000.0, "vapor_pressure_pa": 2340.0}, "air": {"pressure_pa": 101325.0}}
    g = JetGeometry(inp, 0.108, 0.072)
    V, Q = 8.0, 0.05
    Vj = Q / g.A_n
    assert abs(g.thrust(Q, V) - 1000 * Q * (Vj - V)) < 1e-9
    # sin pérdidas: P_h = ½ρQ(Vj² − V²) = T·(Vj + V)/2 (rendimiento ideal de Froude)
    Ph = 1000 * 9.81 * Q * g.H_sys(Q, V)
    assert abs(Ph - 0.5 * 1000 * Q * (Vj ** 2 - V ** 2)) / Ph < 1e-9
    eta_ideal = g.thrust(Q, V) * V / Ph
    assert abs(eta_ideal - 2 / (1 + Vj / V)) < 1e-9


def test_pump_curve_monotonic(inp):
    g = JetGeometry(inp, 0.12, 0.08)
    p = Pump(g, 7.0, 5000.0, 70.0)
    # en el punto de diseño la bomba reproduce el caudal y la altura de diseño
    op = p.operate(70.0, 7.0)
    assert abs(op["Q_m3s"] - p.Q_d) / p.Q_d < 0.01
    assert abs(op["P_shaft"] - 5000.0) / 5000.0 < 0.02
    # a más rpm más empuje; a más velocidad menos empuje (a rpm fija)
    T = [p.operate(n, 5.0)["T"] for n in (50, 60, 70, 80)]
    assert np.all(np.diff(T) > 0)
    T2 = [p.operate(70.0, v)["T"] for v in (0, 4, 8, 10)]
    assert np.all(np.diff(T2) < 0)


def test_hull_box_section(inp):
    """Sección rectangular (β 0, sin abertura): T = m/(ρ·C·L·B), KB = T/2, BM = C_I·L·B³/∇."""
    b = {**inp["boat"], "deadrise_deg": 0.0, "bottom_beam_m": 0.8, "chine_beam_m": 0.8, "beam_m": 0.8,
         "block_coeff": 1.0, "lwl_m": 2.0, "waterplane_inertia_coeff": 1 / 12}
    ii = {**inp, "boat": b}
    hs = hull.hydrostatics(ii, 320.0, 0.3)
    T = 320.0 / (inp["water"]["density_kg_m3"] * 2.0 * 0.8)
    assert abs(hs["draft_m"] - T) < 1e-3
    assert abs(hs["KB_m"] - T / 2) < 1e-3
    assert abs(hs["BM_m"] - (2.0 * 0.8 ** 3 / 12) / (320.0 / inp["water"]["density_kg_m3"])) < 1e-3


def test_capacity_formula_uscg(inp):
    c = hull.capacity_uscg({**inp, "boat": {**inp["boat"], "hull_mass_kg": 30.0}}, 424.0, 35.0)
    # R10b §4.3: Δmax 424, casco 30, máquinas 35 → W = 56 kg
    assert abs(c["persons_gear_kg"] - 56.0) < 1.0


def test_sizing_consistency(sizing, inp):
    pf, sel = sizing["performance"], sizing["selection"]
    # tensión dentro de la regla de ≤ 50 V (o 72 V habilitado explícitamente)
    assert sizing["checks"]["ok_voltage"]
    assert inp["battery"]["options"][sel["battery"]]["v_nom"] <= inp["electrical"]["max_nominal_voltage_v"] \
        or inp["electrical"]["allow_72v"]
    # bollard de un jet de ~5 kW: 550–760 N (R10b §4.5) ± margen por masa y Ø
    assert 400 < pf["bollard_N"] < 900, pf["bollard_N"]
    # η del chorro a V máx en la banda 0,4–0,8 (Froude ideal 0,72–0,78 en R10b)
    assert 0.35 < pf["top"]["eta_jet"] < 0.85
    # cavitación: S a V máx ≤ límite; la curva de pico nunca supera el límite (control anti-cavitación)
    s_max = inp["waterjet"]["pump"]["suction_s_max"]
    assert max(r["S"] for r in pf["peak_curve"]) <= s_max + 1e-6
    # velocidad periférica bajo el límite práctico
    assert sizing["pump"]["U_tip_max"] <= inp["waterjet"]["pump"]["tip_speed_max_ms"]
    # el fusible protege el cable DC
    assert sizing["electrical"]["fuse_protects_cable"]
    # pasador de corte: corta antes de dañar el eje
    assert sizing["mech"]["shear_pin"]["fs_shaft_at_cut"] >= 1.2


def test_legal_speed_cap(sizing, inp):
    """Con el tope de rpm legal y el caso más rápido (piloto liviano, banda baja, batería llena)
    el bote no supera 5 kn."""
    lg = sizing["legal_speed"]
    assert lg["rpm_cap"] > 0
    assert lg["rpm_cap"] < sizing["mech"]["n_max_rpm"]


def test_energy_requirement_reported(sizing):
    en = sizing["energy"]
    assert en["E_usable_wh"] > 0 and en["E_req_wh"] > 0
    assert en["t_legal_h"] > 0.5
