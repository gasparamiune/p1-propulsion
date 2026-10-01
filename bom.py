#!/usr/bin/env python3
"""bom.py — Lista de materiales (bom.csv) y curva costo–autonomía.

Lee inputs.yaml (catálogo `bom`), resultados/sizing.json (selección y dimensionamiento) y
resultados/manifest.json (masas y horas de impresión del CAD).
Salidas: bom.csv, resultados/bom_resumen.json, figuras/costo_autonomia.png,
         figuras/velocidad_autonomia_costo.png
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from p1calc import hydro, power  # noqa: E402
from p1calc.io import FIG_DIR, RESULTS_DIR, load_inputs, load_json  # noqa: E402
from p1calc.system import Drive, R_at  # noqa: E402


def resolve(item, inp, sz, man):
    sel = sz["selection"]
    m = sz["mech"]
    lay = sz["layout"]
    spec, price, qty = item["spec"], item["price_eur"], item["qty"]
    unit = "u"
    s = str(spec)
    if s == "auto:motor":
        mo = inp["motor"]["options"][sel["motor"]]
        spec = (f"{mo['desc']}: {mo['kv_rpm_v']:.0f} KV, ≥ {mo['p_max_w']:.0f} W, ≥ {mo['i_max_a']:.0f} A, "
                f"eje Ø{mo['shaft_d_mm']:.0f} con saliente ≥ {mo['shaft_protrusion_mm']:.0f} mm, sensor de temperatura")
    elif s == "auto:battery":
        b = inp["battery"]["options"][sel["battery"]]
        spec = (f"{b['desc']} — {b['v_nom']} V nominal, {b['ah']:.0f} Ah, BMS ≥ {b['i_cont_a']:.0f} A continuos, "
                f"≤ {b['mass_kg']} kg, IP65+, fabricante permite serie")
    elif s == "auto:charger":
        b = inp["battery"]["options"][sel["battery"]]
        ncell = round(b["v_nom"] / 3.2)
        spec = f"LiFePO4 {ncell}S: {ncell * 3.65:.1f} V CC/CV, ≥ 10 A, con corte automático"
    elif s == "auto:prop":
        p = inp["propeller"]["options"][sel["propeller"]]
        spec = (f"{p['desc']}: D {p['D_mm']:.0f} mm, paso {p['P_mm']:.0f} mm, {p['Z']} palas, AE/A0 ≥ {p['BAR']}, "
                f"bore {p['bore_mm']:.0f} mm con ranura de pasador")
    elif s == "auto:shear_pin":
        sp = m["shear_pin"]
        spec = f"Ø{sp['d_std_mm']} mm {sp['material']} (corta a {sp['Q_shear_Nm']:.1f} N·m), largo = Ø eje + 6 mm"
    elif s == "auto:pulley_motor":
        spec = f"HTD-5M {sel['z_motor']} dientes, correa 15 mm, bore 8 mm con prisioneros + chavetero o plano"
    elif s == "auto:pulley_shaft":
        spec = f"HTD-5M {sel['z_shaft']} dientes, correa 15 mm, bore 16 mm con 2 prisioneros a 90°"
    elif s == "auto:belt":
        b = m["belt"]
        spec = f"HTD-5M {b['length_std_mm']:.0f} mm ({b['teeth']} dientes) × 15 mm, refuerzo de fibra de vidrio (1 de repuesto)"
    elif s == "auto:shaft_bar":
        spec = f"AISI 316 Ø16 h9, largo ≥ {lay['shaft_length_mm'] + 40:.0f} mm (comprar 1,5 m)"
    elif s == "auto:tube":
        spec = (f"Al 6061-T6 (o 6082-T6) Ø{inp['shaft']['tube_od_mm']:.0f}×{inp['shaft']['tube_wall_mm']:.0f}, "
                f"largo {lay['tube_length_mm']:.0f} mm, anodizado preferido")
    elif s == "auto:fuse":
        spec = f"{sz['fuse']['rating_a']} A (MIDI/ANL), ≥ 32 V DC, portafusible estanco a ≤ 18 cm del borne +"
    elif s == "auto:cable_dc":
        c = sz["cables"]["dc"]
        spec = f"{c['section_mm2']} mm² cobre estañado, aislación 105 °C (caída {c['drop_frac']*100:.1f} % a {c['I_a']:.0f} A)"
        qty = round(2 * c["length_m"] * 1.25, 1)
        unit = "m"
    elif s == "auto:cable_ph":
        c = sz["cables"]["phase"]
        spec = f"{c['section_mm2']} mm² cobre estañado, 3 conductores (caída {c['drop_frac']*100:.1f} % a {c['I_a']:.0f} A)"
        qty = round(3 * c["length_m"] * 1.25, 1)
        unit = "m"
    elif s == "auto:plunger":
        spec = f"M12 inox, bola, fuerza de punta ≥ {m['detent']['Fs_per_plunger_N']:.0f} N (o resorte + bola Ø10 ajustable)"
    elif s == "auto:filament":
        kg = man["totals"]["printed_mass_g"] * 1.30 / 1000      # +30 % purga, probetas, reimpresiones
        qty = math.ceil(kg)
        spec = f"PETG 1,75 mm; masa impresa {man['totals']['printed_mass_g']/1000:.2f} kg + 30 % (probetas, fallas)"
        unit = "kg"
    # precios automáticos
    if price == "auto":
        if item["id"] == "B-MOT":
            price = inp["motor"]["options"][sel["motor"]]["price_eur"]
        elif item["id"] == "B-ESC":
            price = inp["esc"]["options"][sel["esc"]]["price_eur"]
        elif item["id"] == "B-BAT":
            price = inp["battery"]["options"][sel["battery"]]["price_eur"]
        elif item["id"] == "B-PROP":
            price = inp["propeller"]["options"][sel["propeller"]]["price_eur"]
    return spec, float(price), float(qty), unit


def main():
    inp = load_inputs()
    sz = load_json("sizing.json")
    man = load_json("manifest.json")
    date = inp["bom"]["date"]
    rows = []
    for it in inp["bom"]["items"]:
        spec, price, qty, unit = resolve(it, inp, sz, man)
        if qty == 0:
            continue
        rows.append({"ID": it["id"], "categoria": it["cat"], "descripcion": it["desc"],
                     "especificacion_minima": spec, "cantidad": qty, "unidad": unit,
                     "proveedor_envio_DK": it["supplier"], "link_o_busqueda": it["link"],
                     "precio_unit_EUR": round(price, 2), "precio_total_EUR": round(price * qty, 2),
                     "etiqueta": it["tag"], "fecha": date})
    # piezas impresas (costo incluido en el filamento) y torneadas (material incluido en barras)
    for r in man["parts"]:
        if r["process"] in ("impresa", "torneada"):
            rows.append({"ID": r["id"], "categoria": "Pieza " + r["process"],
                         "descripcion": f"{r['id']}_{r['name']} — {r['desc']}",
                         "especificacion_minima": (f"{r['material']}; {r['mass_g_each']:.0f} g c/u; "
                                                   f"{r.get('print_hours_each', 0):.1f} h c/u; {r['orientation']}"
                                                   if r["process"] == "impresa" else f"{r['material']}; plano en 04_diseno/planos/"),
                         "cantidad": r["qty"], "unidad": "u", "proveedor_envio_DK": "fabricación propia",
                         "link_o_busqueda": r["files"][0], "precio_unit_EUR": 0.0, "precio_total_EUR": 0.0,
                         "etiqueta": "[CALCULADO] costo en B-PETG / barras", "fecha": date})
    sub = sum(r["precio_total_EUR"] for r in rows)
    ship = sub * inp["costs"]["shipping_frac"]
    cont = sub * inp["costs"]["contingency_frac"]
    total = sub + ship + cont
    dkk = inp["meta"]["eur_to_dkk"]
    with open(ROOT / "bom.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
        for label, val in (("SUBTOTAL compras", sub), (f"Envío ({inp['costs']['shipping_frac']*100:.0f} %)", ship),
                           (f"Imprevistos ({inp['costs']['contingency_frac']*100:.0f} %)", cont),
                           ("TOTAL EUR", total), ("TOTAL DKK", total * dkk)):
            w.writerow({"ID": "", "descripcion": label, "precio_total_EUR": round(val, 2),
                        "etiqueta": "[CALCULADO]", "fecha": date})
    bat_price = inp["battery"]["options"][sz["selection"]["battery"]]["price_eur"]
    by_cat = {}
    for r in rows:
        by_cat[r["categoria"]] = by_cat.get(r["categoria"], 0) + r["precio_total_EUR"]
    summ = {"subtotal_eur": sub, "shipping_eur": ship, "contingency_eur": cont, "total_eur": total,
            "total_dkk": total * dkk, "battery_eur": bat_price,
            "fixed_excl_battery_eur": (sub - bat_price) * (1 + inp["costs"]["shipping_frac"] + inp["costs"]["contingency_frac"]),
            "by_category": by_cat, "n_rows": len(rows), "date": date}
    with open(RESULTS_DIR / "bom_resumen.json", "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    cost_curves(inp, sz, summ)
    print(f"BOM: {len(rows)} filas; subtotal {sub:.0f} €, total {total:.0f} € ({total*dkk:.0f} DKK)")
    return 0


def cost_curves(inp, sz, summ):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG_DIR.mkdir(exist_ok=True)
    sel = sz["selection"]
    fixed = summ["fixed_excl_battery_eur"]
    k = 1 + inp["costs"]["shipping_frac"] + inp["costs"]["contingency_frac"]
    v_cr = inp["operation"]["cruise_speed_kmh"] / 3.6
    pts = []
    for key, b in inp["battery"]["options"].items():
        if b["v_nom"] > inp["electrical"]["max_nominal_voltage_v"]:
            continue
        mass = hydro.masses(inp, b["mass_kg"], inp["architecture"]["unit_mass_estimate_kg"])["total_kg"]
        drv = Drive(inp, sel["z_motor"], sel["z_shaft"], key, sel["propeller"])
        ii = dict(inp)
        E = power.battery_energy_wh(b) * inp["battery"]["usable_dod"]
        out = {}
        for band in ("nominal", "design"):
            st = drv.at_speed(v_cr, R_at(inp, mass, v_cr, band), b["v_nom"])
            out[band] = E / st["P_bat"]
        pts.append((key, fixed + b["price_eur"] * k, out["nominal"], out["design"], b["mass_kg"]))
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for key, c, an, ad, mkg in pts:
        ax.plot([ad, an], [c, c], "-", color="#9ecae1", lw=4)
        ax.plot(ad, c, "ko"); ax.plot(an, c, "o", color="#3182bd")
        ax.annotate(f"{key}\n{mkg:.0f} kg", (an, c), textcoords="offset points", xytext=(6, -4), fontsize=7)
    ax.axvline(inp["operation"]["cruise_time_h"] * (1 + inp["operation"]["reserve_frac"]), color="red", ls=":",
               label="2 h + 20 % reserva")
    ax.set_xlabel(f"Autonomía a {inp['operation']['cruise_speed_kmh']} km/h [h]  (● diseño — ● nominal)")
    ax.set_ylabel("Costo total del sistema [EUR]")
    ax.set_title("Costo vs autonomía por opción de batería (≤ 48 V)")
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "costo_autonomia.png", dpi=130); plt.close(fig)

    # velocidad – autonomía – costo (continuo, €/Wh)
    import numpy as np
    eur_wh = inp["battery"]["energy_price_eur_per_wh"]
    kg_wh = inp["battery"]["energy_mass_kg_per_wh"]
    bkey = sel["battery"]
    b = inp["battery"]["options"][bkey]
    drv = Drive(inp, sel["z_motor"], sel["z_shaft"], bkey, sel["propeller"])
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    speeds = np.arange(3.0, 8.01, 0.25)
    for hours, col in ((1.0, "C0"), (2.0, "C3"), (3.0, "C2")):
        costs = []
        for vk in speeds:
            V = vk / 3.6
            Pb = None
            Ewh = 1000.0
            for _ in range(4):
                mass = hydro.masses(inp, Ewh * kg_wh, inp["architecture"]["unit_mass_estimate_kg"])["total_kg"]
                st = drv.at_speed(V, R_at(inp, mass, V, "design"), b["v_nom"])
                Pb = st["P_bat"] if st["feasible"] else float("nan")
                Ewh = Pb * hours * (1 + inp["operation"]["reserve_frac"]) / inp["battery"]["usable_dod"]
            costs.append(fixed + Ewh * eur_wh * k)
        ax.plot(speeds, costs, color=col, label=f"{hours:.0f} h + 20 % (banda de diseño)")
    ax.axvline(inp["operation"]["cruise_speed_kmh"], color="k", ls=":", label="Crucero elegido")
    ax.axvline(sz["hull_speed"]["v_hull_kmh"], color="gray", ls="--", label="Velocidad de casco")
    ax.set_xlabel("Velocidad de crucero [km/h]"); ax.set_ylabel("Costo total con batería a medida [EUR]")
    ax.set_title(f"Compromiso velocidad–autonomía–costo ({eur_wh:.2f} €/Wh LiFePO4)")
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "velocidad_autonomia_costo.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
