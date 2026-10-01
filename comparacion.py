#!/usr/bin/env python3
"""comparacion.py — P1 frente a comprar un motor (README, 03 §4.3).

Lee inputs.yaml (bloque comparison), resultados/bom_resumen.json y resultados/sizing.json.
Escribe resultados/comparacion.json (marcadores <!--V:cmp.…-->).

    F tal cual   = (trolling + ½ pack de baterías + cargador 12 V + protecciones)·(1 + imprevistos)
    Plan B       = (F sin imprevistos + impresos/herrajes)·(1 + imprevistos)
    V máx troll. = V tal que R(V)·V = P_troll·η_total, banda nominal, masa de diseño de P1
"""
from __future__ import annotations

import json

import numpy as np

from p1calc import hydro
from p1calc.io import RESULTS_DIR, load_inputs


def _v_at_power(inp, mass, P_eff):
    vs = np.linspace(0.3, 4.0, 400)
    Pv = np.array([hydro.resistance(inp, mass, v)["R"][0] * v for v in vs])
    i = int(np.searchsorted(Pv, P_eff))
    return float(vs[min(i, len(vs) - 1)])


def run(inp: dict) -> dict:
    c = inp["comparison"]
    dkk = inp["meta"]["eur_to_dkk"]
    cont = 1 + inp["costs"]["contingency_frac"]
    bom = json.loads((RESULTS_DIR / "bom_resumen.json").read_text(encoding="utf-8"))
    sz = json.loads((RESULTS_DIR / "sizing.json").read_text(encoding="utf-8"))
    p1 = bom["total_eur"]

    bat = inp["battery"]["options"]["LFP12_100x2"]["price_eur"] * c["trolling_battery_eur_frac_of_pack"]
    f_base = c["trolling_dkk"] / dkk + bat + c["trolling_charger_eur"] + c["trolling_protections_eur"]
    f_eur = f_base * cont
    pb = [(f_base + x) * cont for x in c["planb_printed_eur"]]
    ob_dk = c["outboard_dk_dkk"] / dkk
    ob_2bat = (c["outboard_dk_dkk"] + c["outboard_battery_dkk"]) / dkk

    mass = sz["masses"]["total_kg"]
    v_tr = [_v_at_power(inp, mass, c["trolling_power_w"] * e) * 3.6 for e in c["trolling_eta_total"]]
    dod = inp["battery"]["usable_dod"]
    t_full_h = c["trolling_battery_wh"] * dod / c["trolling_power_w"]

    out = {
        "p1_eur": p1, "p1_dkk": p1 * dkk,
        "trolling_eur": c["trolling_dkk"] / dkk, "trolling_battery_eur": bat,
        "F_eur": f_eur, "F_dkk": f_eur * dkk,
        "planB_eur_min": pb[0], "planB_eur_max": pb[1],
        "planB_dkk_min": pb[0] * dkk, "planB_dkk_max": pb[1] * dkk,
        "outboard_dk_eur": ob_dk, "outboard_dk_dkk": c["outboard_dk_dkk"],
        "outboard_de_eur": c["outboard_de_eur"], "outboard_de_dkk": c["outboard_de_eur"] * dkk,
        "outboard_2bat_eur": ob_2bat, "outboard_2bat_dkk": ob_2bat * dkk,
        "ratio_p1_F": p1 / f_eur,
        "ratio_p1_planB_min": p1 / pb[1], "ratio_p1_planB_max": p1 / pb[0],
        "p1_below_outboard_dk_frac": 1 - p1 / ob_dk,
        "p1_below_outboard_de_frac": 1 - p1 / c["outboard_de_eur"],
        "p1_below_outboard_2bat_frac": 1 - p1 / ob_2bat,
        "trolling_vmax_kmh_min": v_tr[0], "trolling_vmax_kmh_max": v_tr[1],
        "trolling_full_throttle_h": t_full_h,
        "outboard_vmax_kmh_min": c["outboard_vmax_kmh"][0], "outboard_vmax_kmh_max": c["outboard_vmax_kmh"][1],
        "energy_ratio_p1_outboard": sz["battery"]["E_nom_wh"] / c["outboard_battery_wh"],
        "mass_kg_used": mass,
        "_etiquetas": {
            "F_eur": "[CALCULADO: precios VERIFICADOS (R04 S42, R08a §3–§6) + mitad del pack ESTIMADO + imprevistos]",
            "trolling_vmax": "[CALCULADO: R(V)·V = 620 W·η_total, η 0,30–0,40 ESTIMADO, banda nominal, masa de diseño de P1]",
        },
    }
    (RESULTS_DIR / "comparacion.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main():
    o = run(load_inputs())
    print(f"P1 {o['p1_eur']:.0f} € | F {o['F_eur']:.0f} € | plan B {o['planB_eur_min']:.0f}–{o['planB_eur_max']:.0f} € | "
          f"fueraborda DK {o['outboard_dk_eur']:.0f} € → P1 {o['p1_below_outboard_dk_frac']:.0%} menos | "
          f"trolling V máx {o['trolling_vmax_kmh_min']:.1f}–{o['trolling_vmax_kmh_max']:.1f} km/h")


if __name__ == "__main__":
    main()
