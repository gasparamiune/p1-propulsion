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
    spec, qty = item["spec"], item["qty"]
    link = item["link"]
    usd, dkk = inp["meta"]["usd_to_eur"], inp["meta"]["eur_to_dkk"]
    if "price_dkk" in item:
        price = item["price_dkk"] / dkk
    elif "price_usd" in item:
        price = item["price_usd"] * usd
    else:
        price = item["price_eur"]
    unit = "u"
    s = str(spec)
    bat = inp["battery"]["options"][sel["battery"]]
    if s == "auto:esc":
        e = inp["esc"]["options"][sel["esc"]]
        spec = (f"{e['desc']}: {e['v_max']:.0f} V máx, {e['i_cont_a']:.0f} A continuos, entrada PPM/ADC, "
                f"timeout de señal, BEC 5 V; FW ≥ 5.03 con filtro de fase APAGADO (research/R08a)")
    elif s == "auto:esc_lid":
        Li, Wi, _ = inp["geometry"]["esc_box_inner_mm"]
        spec = f"≥ {Li + 36 + 4:.0f} × {Wi + 36 + 4:.0f} × 4 mm (plano 04_diseno/planos/P1-ELE-02)"
    elif s == "auto:heatsink":
        r = sz["thermal_esc"]["heatsink"]["R_hs_required_K_W"]
        Li, Wi, _ = inp["geometry"]["esc_box_inner_mm"]
        spec = (f"R_th ≤ {r:.2f} K/W en convección natural (dato del fabricante), base ≤ {Li + 36:.0f} × {Wi + 36:.0f} mm, "
                f"base ≥ 5 mm para roscar M4 ciegos")
    elif s == "auto:battery_boxes":
        qty = bat["series_units"]
        spec = f"{bat['series_units']} caja(s), una por batería ({bat['desc']}); medir la batería real antes de comprar"
    elif s == "auto:motor":
        mo = inp["motor"]["options"][sel["motor"]]
        spec = (f"{mo['desc']}: {mo['kv_rpm_v']:.0f} KV, ≥ {mo['p_max_w']:.0f} W, ≥ {mo['i_max_a']:.0f} A, "
                f"eje Ø{mo['shaft_d_mm']:.0f} con saliente ≥ {mo['shaft_protrusion_mm']:.0f} mm, sensor de temperatura")
    elif s == "auto:battery":
        b = inp["battery"]["options"][sel["battery"]]
        spec = (f"{b['desc']} — {b['v_nom']} V nominal, {b['ah']:.0f} Ah, BMS ≥ {b['i_cont_a']:.0f} A continuos, "
                f"≤ {b['mass_kg']} kg, IP65+, fabricante permite serie")
    elif s == "auto:charger":
        ncell = round(bat["v_nom"] / 3.2)
        spec = f"{bat['charger']['desc']} — LiFePO4 {ncell}S: {ncell * 3.65:.1f} V CC/CV, con corte automático"
        price = bat["charger"]["price_eur"]
        link = bat["charger"]["link"]
    elif s == "auto:prop":
        p = inp["propeller"]["options"][sel["propeller"]]
        spec = (f"{p['desc']}: D {p['D_mm']:.0f} mm, paso {p['P_mm']:.0f} mm, {p['Z']} palas, AE/A0 ≥ {p['BAR']}, "
                f"bore {p['bore_mm']:.0f} mm con ranura de pasador")
    elif s == "auto:shear_pin":
        sp = m["shear_pin"]
        spec = (f"Ø{sp['d_std_mm']} mm {sp['material']} (corta a {sp['Q_shear_Nm']:.1f} N·m), "
                f"largo = Ø asiento de hélice + 6 mm; calibrar con el ensayo P1.9")
    elif s == "auto:pulley_motor":
        spec = f"HTD-5M {sel['z_motor']} dientes, correa 15 mm, bore 8 H7 con prisioneros (eje del motor Ø8 con plano)"
        price = inp["drivetrain"]["pulley_price_eur"][sel["z_motor"]]
    elif s == "auto:pulley_shaft":
        spec = (f"HTD-5M {sel['z_shaft']} dientes, correa 15 mm, bore de fábrica ≤ 14 → re-mandrinar a "
                f"Ø{inp['shaft']['d_bearing_mm']:g} H7; 2 prisioneros a 90°")
        price = inp["drivetrain"]["pulley_price_eur"][sel["z_shaft"]]
    elif s == "auto:belt":
        b = m["belt"]
        spec = (f"HTD-5M {b['length_std_mm']:.0f} mm ({b['teeth']} dientes) × 15 mm, fibra de vidrio; "
                f"centros reales {b['center_actual_mm']:.1f} mm (colisos ±{inp['drivetrain']['center_adjust_mm']:g})")
    elif s == "auto:shaft_bar":
        spec = f"AISI 316 Ø16 h9, largo ≥ {lay['shaft_length_mm'] + 40:.0f} mm (comprar 1,5 m)"
    elif s == "auto:tube":
        spec = (f"Al 6061-T6 (o 6082-T6) Ø{inp['shaft']['tube_od_mm']:.0f}×{inp['shaft']['tube_wall_mm']:.0f}, "
                f"largo {lay['tube_length_mm']:.0f} mm, anodizado preferido")
    elif s == "auto:fuse":
        r = sz['fuse']['rating_a']
        spec = (f"{r} A MIDI (IMAXX midiOTO o equivalente), ≥ {inp['electrical']['fuse_voltage_min_v']:.0f} V DC, "
                f"a ≤ 178 mm del borne + (ABYC E-11, research/R06)")
        links = {80: "https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_80a_58vdc_white-229133",
                 100: "https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_100a_58vdc_blue-229134"}
        link = links.get(r, f"buscar: midiOTO {r}A 58V")
    elif s == "auto:cable_dc":
        c = sz["cables"]["dc"]
        spec = f"{c['section_mm2']} mm² cobre estañado, aislación 105 °C (caída {c['drop_frac']*100:.1f} % a {c['I_a']:.0f} A)"
        qty = round(2 * c["length_m"] * 1.25, 1)
        unit = "m"
        price = inp["electrical"]["cable_price_dkk_m"][c["section_mm2"]] / dkk
    elif s == "auto:cable_ph":
        c = sz["cables"]["phase"]
        spec = f"{c['section_mm2']} mm² cobre estañado, 3 conductores (caída {c['drop_frac']*100:.1f} % a {c['I_a']:.0f} A)"
        qty = round(3 * c["length_m"] * 1.25, 1)
        unit = "m"
        price = inp["electrical"]["cable_price_dkk_m"][c["section_mm2"]] / dkk
    elif s == "auto:clamp_screw":
        tr = inp["boat"]["transom"]
        gap = tr["thickness_range_mm"][1] + 6.0
        L = gap - tr["thickness_range_mm"][0] + inp["mount"]["clamp_leg_t_mm"] + 12 + 40   # carrera + pata + zapata + manija
        L = int(math.ceil(L / 10.0) * 10)
        spec = (f"M12 A4-70, largo ≥ {L} mm (espejos {tr['thickness_range_mm'][0]}–{tr['thickness_range_mm'][1]} mm), "
                f"apriete ≤ {inp['mount']['clamp_screw_torque_nm']} N·m; placa de reparto A4 40×40×4 tras la tuerca")
    elif s == "auto:plunger":
        spec = f"M12 inox, bola, fuerza de punta ≥ {m['detent']['Fs_per_plunger_N']:.0f} N (o resorte + bola Ø10 ajustable)"
    elif s == "auto:filament":
        kg = man["totals"]["printed_mass_g"] * 1.30 / 1000      # +30 % purga, probetas, reimpresiones
        qty = math.ceil(kg)
        spec = f"PETG 1,75 mm; masa impresa {man['totals']['printed_mass_g']/1000:.2f} kg + 30 % (probetas, fallas)"
        unit = "kg"
    # precios automáticos
    src = {"B-MOT": inp["motor"]["options"][sel["motor"]], "B-ESC": inp["esc"]["options"][sel["esc"]],
           "B-BAT": bat, "B-PROP": inp["propeller"]["options"][sel["propeller"]]}.get(item["id"])
    if price == "auto" and src is not None:
        price = src["price_eur"]
    if link == "auto" and src is not None:
        link = src.get("link", "buscar: " + src.get("desc", ""))
    return spec, float(price), float(qty), unit, link


def main():
    inp = load_inputs()
    sz = load_json("sizing.json")
    man = load_json("manifest.json")
    date = inp["bom"]["date"]
    rows = []
    for it in inp["bom"]["items"]:
        spec, price, qty, unit, link = resolve(it, inp, sz, man)
        if qty == 0:
            continue
        rows.append({"ID": it["id"], "categoria": it["cat"], "descripcion": it["desc"],
                     "especificacion_minima": spec, "cantidad": qty, "unidad": unit,
                     "proveedor_envio_DK": it["supplier"], "link_o_busqueda": link,
                     "precio_unit_EUR": round(price, 2), "precio_total_EUR": round(price * qty, 2),
                     "envio": it.get("ship", "eu"), "alcance": it.get("scope", "sistema"),
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
                         "envio": "—", "alcance": "sistema",
                         "etiqueta": "[CALCULADO] costo en B-PETG / barras", "fecha": date})
    c = inp["costs"]
    sys_rows = [r for r in rows if r["alcance"] == "sistema"]
    op_rows = [r for r in rows if r["alcance"] != "sistema"]
    sub = sum(r["precio_total_EUR"] for r in sys_rows)
    sub_cn = sum(r["precio_total_EUR"] for r in sys_rows if r["envio"] == "cn")
    sub_eu = sum(r["precio_total_EUR"] for r in sys_rows if r["envio"] == "eu")
    ship = sub_eu * c["shipping_frac"]
    imp = (c["cn_shipping_eur"] + c["import_vat_frac"] * (sub_cn + c["cn_shipping_eur"])) if sub_cn > 0 else 0.0
    cont = sub * c["contingency_frac"]
    total = sub + ship + imp + cont
    sub_op = sum(r["precio_total_EUR"] for r in op_rows)
    total_op = sub_op * (1 + c["shipping_frac"])
    dkk = inp["meta"]["eur_to_dkk"]
    with open(ROOT / "bom.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
        for label, val in (("SUBTOTAL compras del sistema", sub),
                           (f"Envío UE ({c['shipping_frac']*100:.0f} % de ítems sin envío incluido)", ship),
                           (f"Importación China: envío {c['cn_shipping_eur']:.0f} € [ESTIMADO] + IVA {c['import_vat_frac']*100:.0f} %", imp),
                           (f"Imprevistos ({c['contingency_frac']*100:.0f} %)", cont),
                           ("TOTAL SISTEMA EUR", total), ("TOTAL SISTEMA DKK", total * dkk),
                           ("Equipo de seguridad de operación (aparte, con envío)", total_op),
                           ("TOTAL CON EQUIPO DE OPERACIÓN EUR", total + total_op)):
            w.writerow({"ID": "", "descripcion": label, "precio_total_EUR": round(val, 2),
                        "etiqueta": "[CALCULADO]", "fecha": date})
    bopt = inp["battery"]["options"][sz["selection"]["battery"]]
    bat_price = bopt["price_eur"] + bopt["charger"]["price_eur"]
    by_cat = {}
    for r in rows:
        by_cat[r["categoria"]] = by_cat.get(r["categoria"], 0) + r["precio_total_EUR"]
    n_ver = sum(1 for r in sys_rows if r["etiqueta"].startswith("[VERIFICADO") and r["precio_total_EUR"] > 0)
    eur_ver = sum(r["precio_total_EUR"] for r in sys_rows if r["etiqueta"].startswith("[VERIFICADO"))
    summ = {"subtotal_eur": sub, "shipping_eur": ship, "import_cn_eur": imp, "contingency_eur": cont,
            "total_eur": total, "total_dkk": total * dkk, "battery_eur": bopt["price_eur"],
            "battery_charger_eur": bat_price,
            "operation_gear_eur": total_op, "total_with_gear_eur": total + total_op,
            "verified_rows": n_ver, "verified_frac_of_subtotal": eur_ver / sub if sub else 0.0,
            "fixed_excl_battery_eur": (sub - bat_price) * (1 + c["contingency_frac"]) + ship + imp,
            "by_category": by_cat, "n_rows": len(rows), "date": date}
    with open(RESULTS_DIR / "bom_resumen.json", "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    cost_curves(inp, sz, summ)
    print(f"BOM: {len(rows)} filas; subtotal {sub:.0f} €, importación CN {imp:.0f} €, total sistema {total:.0f} € "
          f"({total*dkk:.0f} DKK); equipo de operación {total_op:.0f} €; "
          f"{summ['verified_frac_of_subtotal']*100:.0f} % del subtotal con precio verificado")
    return 0


def cost_curves(inp, sz, summ):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG_DIR.mkdir(exist_ok=True)
    sel = sz["selection"]
    fixed = summ["fixed_excl_battery_eur"]
    k = 1 + inp["costs"]["contingency_frac"]
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
        pts.append((key, fixed + (b["price_eur"] + b["charger"]["price_eur"]) * (1 + inp["costs"]["contingency_frac"]),
                    out["nominal"], out["design"], b["mass_kg"]))
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
