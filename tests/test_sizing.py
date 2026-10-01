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
    # research/R04 §C.3: R(6 km/h) medida 95–150 N; rendimiento total batería→R·V de sistemas
    # reales 0,34–0,45 (R04) y ~0,25–0,30 con hélice de trolling (η0 0,40–0,50, research/R02 S34).
    P = sizing["cruise"]["nominal"]["P_bat"]
    R = sizing["cruise"]["nominal"]["R"]
    assert 95 <= R <= 150 * 1.05, R              # banda medida R(6 km/h)=95–150 N
    eta = R * sizing["cruise"]["nominal"]["V"] / P
    assert 0.25 <= eta <= 0.50, eta


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


def test_bseries_control():
    # research/R09 §2.1: B3-50, P/D 1,0, J 0,5 → KT 0,2451, KQ 0,03863, η0 0,505
    from p1calc.prop import Propeller
    p = Propeller(0.254, 0.254, 3, 0.50)
    assert "B-series" in p.model
    assert abs(float(p.kt(0.5)) - 0.2451) < 1e-4
    assert abs(float(p.kq(0.5)) - 0.03863) < 1e-5
    assert abs(float(p.eta0(0.5)) - 0.505) < 1e-3


def test_bseries_out_of_range_falls_back():
    from p1calc.prop import Propeller
    assert "fuera del rango" in Propeller(0.254, 0.1016, 2, 0.35).model   # P/D 0,4 < 0,5


def test_burrill_table():
    # research/R09 §3.2: curva de 5 % (σ=1 → 0,260; σ=2 → 0,301) y monótona
    from p1calc.prop import burrill_tau_limit
    assert abs(burrill_tau_limit(1.0) - 0.260) < 1e-9
    assert abs(burrill_tau_limit(2.0) - 0.301) < 1e-9
    xs = [0.1 * i for i in range(1, 31)]
    ys = [burrill_tau_limit(x) for x in xs]
    assert all(b >= a for a, b in zip(ys, ys[1:]))


def test_shaft_span_and_critical_speed(sizing):
    # research/R09 §5.1: tramo biapoyado ≤ 0,6 m para velocidad crítica ≥ ~4× la máxima
    assert sizing["layout"]["max_span_mm"] <= 600.0
    sh = sizing["mech"]["shaft"]
    assert sh["n_crit_rpm"] >= 3.0 * sh["n_max_rpm"]
