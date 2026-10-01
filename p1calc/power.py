"""Batería, cables y protecciones."""
from __future__ import annotations

import math


def battery_energy_wh(b: dict) -> float:
    return b["v_nom"] * b["ah"]


def required_energy_wh(inp: dict, P_bat_cruise_w: float) -> float:
    op = inp["operation"]
    return P_bat_cruise_w * op["cruise_time_h"] * (1 + op["reserve_frac"]) / inp["battery"]["usable_dod"]


def select_battery(inp: dict, E_req_wh: float, I_bat_max_a: float) -> tuple[str, list]:
    """Elige la opción más barata que cumple energía y corriente. Devuelve (clave, tabla)."""
    rows = []
    for k, b in inp["battery"]["options"].items():
        E = battery_energy_wh(b)
        ok_E = E >= E_req_wh
        ok_I = b["i_cont_a"] >= I_bat_max_a
        rows.append({"key": k, "desc": b["desc"], "E_wh": E, "mass_kg": b["mass_kg"],
                     "price_eur": b["price_eur"], "i_cont_a": b["i_cont_a"],
                     "ok_energy": ok_E, "ok_current": ok_I, "ok": ok_E and ok_I,
                     "eur_per_wh": b["price_eur"] / E})
    ok = [r for r in rows if r["ok"]]
    if not ok:
        best = max(rows, key=lambda r: r["E_wh"])
        return best["key"], rows
    best = min(ok, key=lambda r: (r["price_eur"], r["mass_kg"]))
    return best["key"], rows


def cable(inp: dict, I_a: float, length_one_way_m: float, V_sys: float, n_cond: int = 2) -> dict:
    """Sección mínima por caída de tensión (ida y vuelta) y ampacidad."""
    e = inp["electrical"]
    rho = e["rho_cu_ohm_m"]
    L = length_one_way_m * n_cond
    A_drop = rho * L * I_a / (e["max_drop_frac"] * V_sys) * 1e6   # mm²
    sec = e["cable_sections_mm2"]
    amp = e["ampacity_a"]
    choice = None
    for s, a in zip(sec, amp):
        if s >= A_drop and a >= I_a:
            choice = (s, a)
            break
    if choice is None:
        choice = (sec[-1], amp[-1])
    s, a = choice
    drop = rho * L * I_a / (s * 1e-6)
    return {"I_a": I_a, "length_m": length_one_way_m, "A_min_drop_mm2": A_drop,
            "section_mm2": s, "ampacity_a": a, "drop_v": drop, "drop_frac": drop / V_sys}


def fuse(inp: dict, I_cont: float, cable_ampacity: float) -> dict:
    e = inp["electrical"]
    need = I_cont * e["fuse_factor"]
    rating = next((r for r in e["fuse_ratings_a"] if r >= need), e["fuse_ratings_a"][-1])
    return {"I_cont_a": I_cont, "rating_min_a": need, "rating_a": rating,
            "cable_ampacity_a": cable_ampacity, "protects_cable": rating <= cable_ampacity}
