"""Sanidad del dimensionamiento: fórmulas, monotonía y contraste con datos medidos (research/R04)."""
import math

import numpy as np

from p1calc import hydro


def test_ittc57_formula():
    # C_F(Re=1e7) = 0.075/(7−2)² = 0.003
    Re = 1e7
    assert abs(0.075 / (math.log10(Re) - 2) ** 2 - 0.003) < 1e-12


def test_hull_speed(inp):
    hs = hydro.hull_speed(inp)
    L = inp["boat"]["lwl_m"]
    assert abs(hs["v_hull_kn"] - 1.34 * math.sqrt(L / 0.3048)) < 1e-9
    assert 0.39 < hs["fr_hull"] < 0.41          # 1.34·√L[ft] kn ≡ Fr ≈ 0.40


def test_resistance_monotonic(inp):
    v = np.linspace(0.3, 3.5, 40)
    r = hydro.resistance(inp, 290.0, v)["R"]
    assert np.all(np.diff(r) > 0)


def test_holtrop_transom_limits(inp):
    # c6 = 0.2(1−0.2 F_nT) para F_nT<5 → a V→0 la componente tiende a 0 y es ≥ 0
    r = hydro.resistance(inp, 290.0, np.array([0.01, 1.0, 3.0]))
    assert np.all(r["RTR"] >= 0)


def test_cruise_power_in_measured_band(sizing):
    # research/R04 §C.3: P_bat a 6 km/h 352–735 W según η (0.45–0.34)
    P = sizing["cruise"]["nominal"]["P_bat"]
    assert 300 < P < 760, P
    R = sizing["cruise"]["nominal"]["R"]
    assert 95 <= R <= 150 * 1.05, R              # banda medida R(6 km/h)=95–150 N


def test_bollard_vs_commercial(sizing):
    # Torqeedo 1103 / ePropulsion medidos: 290–310 N a ~1 kW (research/R04 §B.2)
    T = sizing["bollard_fwd"]["T_horiz"]
    assert 230 < T < 380, T


def test_energy_and_limits(sizing, inp):
    b = sizing["battery"]
    assert b["E_usable_wh"] >= inp["operation"]["cruise_time_h"] * (1 + inp["operation"]["reserve_frac"]) * \
        sizing["cruise"]["design"]["P_bat"] - 1
    assert sizing["requirements_met"] is True
    assert sizing["esc"]["margin_frac"] >= inp["esc"]["margin_min_frac"]
    assert sizing["cables"]["dc"]["drop_frac"] <= inp["electrical"]["max_drop_frac"] + 1e-9
    assert sizing["cables"]["phase"]["drop_frac"] <= inp["electrical"]["max_drop_frac"] + 1e-9
    assert sizing["fuse"]["protects_cable"]
    bat = inp["battery"]["options"][sizing["selection"]["battery"]]
    assert bat["v_nom"] <= inp["electrical"]["max_nominal_voltage_v"]


def test_shaft_and_kickup(sizing):
    s = sizing["mech"]["shaft"]
    assert s["fs_static"] >= 2 and s["fs_fatigue_goodman"] >= 2
    assert s["crit_ratio"] >= 2
    k = sizing["mech"]["kickup"]
    assert k["fs_reverse_hold"] >= 1.5          # marcha atrás no levanta la cola
    assert k["F_release_at_skeg_fwd_N"] < sizing["mech"]["impact"]["F_peak_N"]


def test_cavitation_margin(sizing):
    for k, c in sizing["cavitation"].items():
        assert c["keller_min_BAR"] <= c["BAR"] + 1e-9, k


def test_max_speed_physics(sizing):
    # techo físico de ~1 kW en casco de 2.4–2.75 m: 7.6–8.0 km/h medidos (research/R04 §C.2)
    v = sizing["vmax"]["nominal_vnom"]["V_kmh"]
    assert 6.5 < v < 9.5
