"""Sanidad del dimensionamiento del waterjet: fórmulas, monotonía y contraste con referencias
(research/R10b, R12)."""
import hashlib
import math

import numpy as np
import pytest

from p1calc import hull
from p1calc.planing import savitsky, savitsky_length_limited
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
                        "wake_fraction": 0.0, "thrust_deduction": 0.0, "throat_d_ratio": 1.11},
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
    # bollard de un jet de ~5 kW: 550–760 N (R10b §4.5); acá ~6,5 kW al eje → 550–900 N
    assert 550 < pf["bollard_N"] < 900, pf["bollard_N"]
    # contraste a mano (cantidad de movimiento a V = 0, sin rejilla): P_h = (1 + K_n)·ρ·A_j·V_j³/2, T = ρ·A_j·V_j²
    b0, j = pf["peak_curve"][0], inp["waterjet"]
    rho = inp["water"]["density_kg_m3"]
    A_j = j["nozzle_cc"] * math.pi / 4 * (sel["D_noz_mm"] / 1000) ** 2
    Vj = (2 * b0["eta_pump"] * b0["P_shaft"] / ((1 + j["nozzle_loss_k"]) * rho * A_j)) ** (1 / 3)
    T_hand = rho * A_j * Vj ** 2
    assert 0.93 * T_hand <= pf["bollard_N"] <= T_hand * 1.001, (pf["bollard_N"], T_hand)
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
    el bote no supera 5 kn: T(n_tope, V) < R_liviano,baja(V) para toda V > 5 kn."""
    lg = sizing["legal_speed"]
    v_leg = inp["operation"]["legal_speed_limit_kmh"]
    assert lg["rpm_cap"] > 0
    assert lg["rpm_cap"] < sizing["mech"]["n_max_rpm"]
    assert lg["cap_holds_above_limit"] and lg["excess_above_limit_max_N"] < 0, lg["excess_above_limit_max_N"]
    c = lg["costa"]
    assert abs(c["light_low"]["V_kmh"] - v_leg) < 0.1, c["light_low"]      # el tope se calcula para ese caso
    assert c["design_high"]["V_kmh"] <= c["design_nominal"]["V_kmh"] <= c["light_low"]["V_kmh"] + 1e-6
    # la P "a 5 kn" del piloto de diseño pide más rpm que el tope: el documento tiene que decirlo
    assert lg["legal_rpm_reachable_in_costa"] == (lg["n_legal_rpm"] <= lg["rpm_cap"] + 1e-6)


def test_energy_requirement_reported(sizing):
    en = sizing["energy"]
    assert en["E_usable_wh"] > 0 and en["E_req_wh"] > 0
    assert en["t_legal_h"] > 0.5


def test_savitsky_validity_flags(inp):
    """Savitsky libre con la masa de diseño a 20 km/h: la eslora mojada en la quilla supera el fondo
    (auditoría A1) → punto no válido; el limitado por eslora la fija en L_wl con τ en rango."""
    L = inp["boat"]["lwl_m"]
    free = savitsky(inp, 217.2, 1.116, 0.340, 20 / 3.6)
    assert free["L_K"] > L and not free["ok_LK"] and not free["valid"]
    ll = savitsky_length_limited(inp, 217.2, 1.116, 0.340, 20 / 3.6)
    assert abs(ll["L_K"] - L) < 1e-3 and ll["ok_tau"] and ll["ok_lambda"]
    assert ll["tau_deg"] > free["tau_deg"] and ll["R"] > free["R"]       # más trimado, más resistencia


def test_savitsky_points_exported(sizing):
    """Cada punto de planeo exporta L_K, λ, τ y su validez; ninguno usado como 'Savitsky 1964' viola el rango."""
    rs = sizing["resistance"]
    L = rs["lwl_m"]
    assert rs["savitsky"], "sin puntos de planeo"
    for p in rs["savitsky"]:
        for k in ("L_K", "lambda", "tau_deg", "valid", "ok_LK", "ok_lambda", "ok_tau", "method"):
            assert k in p, k
        assert p["L_K"] <= L + 1e-3 and p["lambda"] <= 4.0 and 2.0 <= p["tau_deg"] <= 15.0, p
        if p["method"] == "Savitsky 1964":
            assert p["valid"]
    assert rs["n_valid_free"] == sum(1 for p in rs["savitsky"] if p["free_valid"])


def test_hump_ok_reported(sizing, inp):
    """La restricción dura del planeo es hump_ok (margen ≥ plane_margin_frac), no solo 'cruza'."""
    pf, tgt = sizing["performance"], inp["operation"]["plane_margin_frac"]
    assert pf["hump_ok"] == (pf["hump_margin_min"] >= tgt and pf["planes"])
    assert sizing["checks"]["ok_planes"] == pf["hump_ok"]
    sn = sizing["sensitivity"]
    fails = {r["label"] for r in sn["rows"]
             for e in ("lo", "hi") if r[e]["hump"] < tgt or not r[e]["planes"]}
    assert set(sn["any_hump_fail"]) == fails


def test_sensitivity_entries_change_outputs(sizing):
    """Cada entrada de la sensibilidad tiene que mover al menos una salida (auditoría A2) y las de la
    resistencia de planeo tienen que mover el margen 0–planeo pleno (auditoría R2-C02: la fila de planeo
    movía solo la banda nominal y el margen se calcula con la alta)."""
    for r in sizing["sensitivity"]["rows"]:
        lo, hi = r["lo"], r["hi"]
        moved = (abs(lo["vmax"] - hi["vmax"]) > 0.05 or abs(lo["hump"] - hi["hump"]) > 0.002
                 or abs(lo["P_leg"] - hi["P_leg"]) > 1.0 or abs(lo["bollard"] - hi["bollard"]) > 1.0)
        assert moved, r["label"]
        if r["param"] in ("resistance.planing_factor", "resistance.planing_band.high", "resistance.fn_planing"):
            assert abs(lo["hump"] - hi["hump"]) > 0.002, r["label"]


def test_status_matches_hard_constraints(sizing):
    op = sizing["optimization"]
    assert (sizing["status"] == "sin_solucion_dura") == (op["n_hard_ok"] == 0)
    assert op["n_hard_ok"] == sum(1 for r in op["rows"] if r.get("hard_ok"))


def test_margin_window_reaches_full_planing(sizing, inp):
    """El margen se busca de 0 hasta el planeo pleno (no se corta en el primer nodo de Savitsky, R2-C01) y
    es el mínimo de (T − R)/R de la curva de pico en esa ventana."""
    pf, rs = sizing["performance"], sizing["resistance"]
    v_end = pf["V_window_end_kmh"]
    vmax_grid = pf["peak_curve"][-1]["V"] * 3.6
    assert v_end >= min(rs["v_full_planing_kmh"], vmax_grid) - 1e-6
    assert v_end >= rs["v_planing_kmh"] - 1e-6
    rel = [(r["T"] - r["R"]) / max(r["R"], 1e-6) for r in pf["peak_curve"] if 0.3 < r["V"] and r["V"] * 3.6 <= v_end + 1e-6]
    assert abs(min(rel) - pf["hump_margin_min"]) < 1e-9
    # si el bote "llega a planeo pleno", el equilibrio a fondo está más allá de la ventana
    if pf["planes"]:
        assert pf["V_eq_peak_design_band_kmh"] >= v_end - 1e-6


def test_pump_design_speed_not_clipped(sizing):
    """V_d = la V más alta con T(P_d) = R nominal, sin tope de grilla (R2-C03)."""
    pm, rs = sizing["pump"], sizing["resistance"]
    assert not pm["V_design_at_edge"]
    assert pm["V_design_kmh"] < max(rs["V_kmh"][-1], rs["savitsky"][-1]["V_kmh"]) + 1e-6 or not pm["V_design_at_edge"]
    assert abs(pm["V_design_kmh"] - 39.6) > 0.05                     # ya no el borde de la grilla vieja


def test_vmax_by_battery_coherent(sizing):
    """La V máx. por batería usa la misma banda para planear y para la V máx. (R2-C04)."""
    v_pl = sizing["resistance"]["v_planing_kmh"]
    for k, r in sizing["performance"]["vmax_by_battery"].items():
        assert r["sustains_planing_cont_nominal"] == (r["vmax_cont_kmh"] >= v_pl - 1e-6), k
        if not r["planes_nominal"]:
            assert not r["sustains_planing_cont_nominal"], k


def test_verdict_keys(sizing):
    vd = sizing["verdict"]
    for k in ("optimizer_status", "planes_high_band", "planes_nominal_band", "reaches_planing_high",
              "hump_margin_min_high", "hump_ok", "sustains_planing_cont_high", "sustains_planing_cont_nominal",
              "recovery_mass_text", "recovery_lwl_text", "V_full_planing_kmh"):
        assert k in vd, k
    assert vd["hump_ok"] == sizing["performance"]["hump_ok"]
    assert vd["optimizer_status"] == sizing["status"]


def test_sizing_json_matches_inputs(sizing, root):
    """resultados/sizing.json tiene que venir de este inputs.yaml (auditoría A7)."""
    h = hashlib.sha256((root / "inputs.yaml").read_bytes()).hexdigest()
    assert sizing.get("inputs_sha256") == h, "sizing.json desactualizado respecto de inputs.yaml: correr `python run_all.py`"


def test_motor_iq_margin(sizing, inp):
    """FOC: I_q = I_CC·K_t/K_t,FOC y el pico de I_q no supera l_current_max (auditoría A6)."""
    mc = sizing["motor_current"]
    assert mc["kt_convention"] == inp["motor"]["kt_convention"]
    if mc["kt_convention"] == "bus_foc":
        assert abs(mc["iq_over_idc"] - 2 / math.sqrt(3)) < 1e-9
    assert mc["I_q_max_A"] <= mc["l_current_max_A"] * 1.001
    assert all(r["I_q"] <= mc["l_current_max_A"] * 1.001 for r in sizing["performance"]["peak_curve"])


def test_cavitation_cap_exported(sizing, inp):
    """Tope de rpm por cavitación del perfil abierto (02 §4.6): lo consume la electrónica. A punto fijo la curva
    de pico está limitada por S justo en el tope, el ERPM usa los pares de polos de inputs, y el tope no
    sube la V máx. por ratos."""
    cc = sizing["cavitation_cap"]
    sel = sizing["selection"]
    pp = inp["motor"]["options"][sel["motor"]]["pole_pairs"]
    assert cc["pole_pairs"] == pp and cc["erpm"] == pytest.approx(cc["rpm"] * pp)
    b0 = sizing["performance"]["peak_curve"][0]
    if b0["limiter"].startswith("cavitación"):
        assert abs(b0["n_rpm"] - cc["rpm"]) < 2.0 and abs(b0["S"] - cc["S_lim"]) < 0.01
    else:                                   # otro límite manda antes: el tope no se alcanza a punto fijo
        assert b0["n_rpm"] < cc["rpm"] and b0["S"] < cc["S_lim"]
    assert cc["vmax_peak_capped_kmh"] <= sizing["performance"]["vmax_peak_kmh"] + 1e-6
