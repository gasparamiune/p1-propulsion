#!/usr/bin/env python3
"""bom.py — Lista de materiales del waterjet P1-J (bom.csv) y curva costo–energía de la batería.

Lee inputs.yaml (bloque `bom` + opciones de motor/ESC/batería, costs, meta), resultados/sizing.json
(selección, eléctrico, mecánico, refrigeración, optimización) y resultados/manifest.json (todas las
piezas del CAD: proceso, material, bbox, masa, parámetros).

Reglas:
  - Toda pieza "comprada" del manifest tiene que estar en el `covers` de algún ítem.
  - Toda pieza "torneada" (= mecanizada) tiene su materia prima (MP-*, generada desde el bbox con
    sobremedida, agrupada por material y Ø/espesor) o la provee un servicio (by_service), y si no
    sale del torno manual del usuario (Ø > lathe_max_d_mm, CNC, láser, soldadura, fresado) tiene
    una línea de servicio (S-*) que la cubre.
  - Piezas impresas → filamento automático (masa del manifest + probetas + margen).
  - Ítems eléctricos con `rating` se comparan con la corriente y la tensión de la selección.

Salidas: bom.csv, resultados/bom_resumen.json, figuras/costo_autonomia.png
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from p1calc.io import FIG_DIR, RESULTS_DIR, load_inputs, load_json  # noqa: E402

FIELDS = ["ID", "categoria", "descripcion", "especificacion_minima", "cantidad", "unidad",
          "proveedor_envio_DK", "link_o_busqueda", "precio_unit_EUR", "precio_total_EUR", "envio",
          "alcance", "etiqueta", "verificado", "cubre", "fecha"]
CAT_SERVICE = "Servicio de fabricación"
CAT_MP = "Materia prima (mecanizado)"
MAT_CODE = {"AISI 316": "316", "Al 6061-T6": "6061", "Al 5052/6082": "6082", "Al 5083": "5083", "POM-C": "POM"}
WARN: list[str] = []


def warn(msg):
    WARN.append(msg)
    print("AVISO BOM:", msg)


def _f(x, nd=1):
    """Número con coma decimal (estilo del proyecto)."""
    return f"{x:.{nd}f}".replace(".", ",")


# ------------------------------------------------------------------------------------------------
# Ítems del catálogo (inputs.yaml bom.items)
# ------------------------------------------------------------------------------------------------
def cable_price(inp, mm2):
    """€/m y etiqueta del cable estañado: verificado en 16/25 mm² (R08a §7), resto extrapolado."""
    tab = {float(k): float(v) for k, v in inp["bom"]["cable_dkk_dm"].items()}
    dkk = inp["meta"]["eur_to_dkk"]
    if float(mm2) in tab:
        return tab[float(mm2)] * 10 / dkk, f"[VERIFICADO: research/R08a §7 — {_f(tab[float(mm2)], 0)} kr/dm]"
    (s1, p1), (s2, p2) = sorted(tab.items())[:2]
    p = p1 + (p2 - p1) / (s2 - s1) * (mm2 - s1)
    return p * 10 / dkk, (f"[ESTIMADO: extrapolación lineal de research/R08a §7 ({_f(s1, 0)} mm² {_f(p1, 0)} kr/dm, "
                          f"{_f(s2, 0)} mm² {_f(p2, 0)} kr/dm) → {_f(p, 1)} kr/dm]")


def oring_cord(man):
    p = man["params"]
    w = p.get("pmp_gl_width", 4.73)
    parts = []
    if "pmp_gl_r_in" in p:
        parts.append(("2 bridas de la bomba", 2 * 2 * math.pi * (p["pmp_gl_r_in"] + w / 2)))
    if "pmp_land_R" in p:
        parts.append(("placa de espejo (radial)", 2 * math.pi * p["pmp_land_R"]))
    if "toma_plate_x0" in p and "toma_groove_y" in p:
        parts.append(("brida inferior de la toma", 2 * (p["toma_plate_x1"] - p["toma_plate_x0"]) + 4 * p["toma_groove_y"]))
    if "toma_chim_id" in p:
        parts.append(("tapa de inspección", math.pi * (p["toma_chim_id"] + 16.0)))
    L = sum(v for _, v in parts) / 1000 * 1.15
    L = math.ceil(L * 2) / 2
    txt = " + ".join(f"{n} {_f(v / 1000, 2)} m" for n, v in parts)
    return L, (f"NBR70 Ø{_f(p.get('oring_cs', 3.53), 2)} ±0,10, empalme a tope con cianoacrilato: {txt} "
               f"(+15 % empalmes) = {_f(L, 1)} m")


def filament(inp, man):
    fcfg = inp["bom"]["filament"]
    printed = sum(r["mass_g_each"] * r["qty"] for r in man["parts"] if r["process"] == "impresa")
    prob, src = fcfg["probetas_fallback_g"], "[ESTIMADO: inputs bom.filament.probetas_fallback_g]"
    pf = ROOT / "04_diseno" / "probetas" / "probetas_manifest.json"
    try:
        pm = json.loads(pf.read_text(encoding="utf-8"))
        if str(pm.get("inputs_version")) == str(man.get("inputs_version")):
            prob, src = pm["totals"]["mass_g"], "[CALCULADO: probetas_manifest.json]"
        else:
            src += f" (probetas_manifest.json es de inputs {pm.get('inputs_version')}, no del waterjet)"
    except (OSError, KeyError, ValueError):
        pass
    kg = (printed + prob) * (1 + fcfg["margin_frac"]) / 1000
    spec = (f"PETG 1,75 mm HDT ≥ 70 °C; piezas {_f(printed / 1000, 2)} kg (manifest) + probetas {_f(prob / 1000, 2)} kg "
            f"{src} + {fcfg['margin_frac'] * 100:.0f} % = {_f(kg, 2)} kg")
    return math.ceil(kg), spec


def resolve(item, inp, sz, man):
    """Devuelve (spec, precio_unit_EUR, qty, unidad, link, etiqueta)."""
    sel, el, mech = sz["selection"], sz["electrical"], sz["mech"]
    usd, dkk = inp["meta"]["usd_to_eur"], inp["meta"]["eur_to_dkk"]
    p = man.get("params", {})
    spec, qty, unit = str(item["spec"]), item["qty"], item.get("unit", "u")
    link, tag = item["link"], item["tag"]
    price = item.get("price_eur")
    if "price_dkk" in item:
        price = item["price_dkk"] / dkk
    elif "price_usd" in item:
        price = item["price_usd"] * usd
    bat = inp["battery"]["options"][sel["battery"]]
    mo = inp["motor"]["options"][sel["motor"]]
    es = inp["esc"]["options"][sel["esc"]]
    s = spec
    if s == "auto:motor":
        spec = (f"{mo['desc']}: {mo['kv_rpm_v']:.0f} KV, {mo['cells_max']}S máx., {mo['i_max_a']:.0f} A máx., "
                f"Ø{mo['size_mm'][0]:.0f} × {mo['size_mm'][1]:.0f}, eje Ø{mo['shaft_d_mm']:.0f} con chavetero 5 mm, "
                f"refrigeración por {mo['cooling']}; n máx. de diseño {mech['n_max_rpm']:.0f} rpm; precio con 25 % IVA de importación")
        price = mo["price_eur"]
    elif s == "auto:esc":
        spec = (f"{es['desc']}: {es['v_max']:.0f} V máx. (≥ {_f(bat['v_max'])} V), {es['i_cont_a']:.0f} A continuos "
                f"(≥ 1,2 × {el['I_phase_limit_A']:.0f} A de fase configurados), FW ≥ 5.03, entradas PPM + ADC2; "
                f"caja de agua en el circuito de refrigeración; precio con 25 % IVA de importación")
        price = es["price_eur"]
    elif s == "auto:battery":
        spec = (f"{bat['desc']} — {_f(bat['v_nom'])} V nom. / {_f(bat['v_max'])} V máx. (≤ 50 V CC), {bat['ah']:.0f} Ah "
                f"({bat['v_nom'] * bat['ah'] / 1000:.2f} kWh), BMS {bat['i_cont_a']:.0f} A ≥ {el['I_bat_peak_A']:.0f} A pico, "
                f"≈ {_f(bat['mass_kg'])} kg")
        price = bat["price_eur"]
    elif s == "auto:charger":
        spec = f"{bat['charger']['desc']} — LiFePO4 {bat['cells']}S: {_f(bat['v_max'])} V CC/CV, corte automático"
        price = bat["charger"]["price_eur"]
    elif s == "auto:fuse":
        spec = (f"Blue Sea MRBF {el['fuse_a']} A, 58 V CC (≥ {_f(bat['v_max'])} V), corte 10 kA; "
                f"≥ {_f(inp['electrical']['fuse_factor'], 2)} × {el['I_bat_top_A']:.0f} A a fondo y protege el cable de "
                f"{el['cable_dc']['section_mm2']} mm² ({el['cable_dc']['ampacity_a']} A); a ≤ 178 mm del borne + (ABYC E-11, R06 §5.1)")
    elif s == "auto:contactor":
        spec = (f"NA monoestable (sin enclavamiento magnético), ≥ {el['fuse_a']} A continuos (I bat pico {el['I_bat_peak_A']:.0f} A), "
                f"corte bajo carga ≥ {_f(bat['v_max'])} V CC, bobina 48 V continua que cierre con ≤ {_f(bat['v_min'])} V, "
                f"supresor diodo+R/TVS, IP66 o en caja; el SW80 de R06 (100 A) NO alcanza")
    elif s in ("auto:cable_dc", "auto:cable_ph"):
        c = el["cable_dc"] if s == "auto:cable_dc" else el["cable_phase"]
        n = 2 if s == "auto:cable_dc" else 3
        qty = round(n * c["length_m"] * 1.25 + (0.5 if s == "auto:cable_dc" else 0.0), 1)   # +0,5 m: puentes F1–S1–K1
        unit = "m"
        price, tag = cable_price(inp, c["section_mm2"])
        ok = c["ampacity_a"] >= c["I_a"]
        spec = (f"{c['section_mm2']} mm² cobre estañado 105 °C ({c['ampacity_a']} A {'≥' if ok else '<'} {c['I_a']:.0f} A"
                + ("" if ok else " ⚠ pico de fase sobre la tabla de ampacidad: solo transitorio, verificar") + "), "
                f"caída {_f(c['drop_frac'] * 100, 2)} % en {_f(c['length_m'])} m; {n} conductores × {_f(c['length_m'])} m × 1,25"
                + (" + 0,5 m de puentes" if n == 2 else ""))
    elif s == "auto:seal":
        d = p.get("drv_seal", {})
        spec = (f"{d.get('name', 'MG1 Ø20')}: {d.get('p_max_bar', 12):g} bar, {d.get('v_max_ms', 10):g} m/s "
                f"(≥ {_f(mech['seal_speed_ms'])} m/s del eje a {mech['n_max_rpm']:.0f} rpm); pedir carbón/SiC")
    elif s == "auto:bearing":
        d = p.get("drv_bearing", {})
        spec = (f"{d.get('name', '7204 BEP')} 20 × 47 × 14, C = {d.get('C_n', 0) / 1000:.1f} kN, C0 = {d.get('C0_n', 0) / 1000:.2f} kN "
                f"≫ empuje {mech['Fa_max_N']:.0f} N; montaje en O con KM4/MB4, lado seco")
    elif s == "auto:coupling":
        d = p.get("drv_coupling", {})
        spc = mech["shear_pin"]
        spec = (f"{d.get('name', 'Rotex 24')} Ø{d.get('D', 55):g}, estrella 92 ShA: T_KN {d.get('T_KN_Nm', 35):g} N·m "
                f"≥ par de corte del pasador {_f(spc['T_cut_Nm'])} N·m ≥ T máx {_f(mech['T_max_Nm'])} N·m; "
                f"agujerear Ø20 H7 + chaveta 6 (eje) y Ø{mo['shaft_d_mm']:.0f} H7 + chaveta 5 (motor) en el torno")
    elif s == "auto:cooling_hose":
        c, h = sz["cooling"], p.get("cool_hose", [6.0, 8.0])
        spec = (f"Ø{h[0]:g} × {h[1]:g} PVC armada o silicona, ≥ 2 bar, 60 °C; caudal a fondo {_f(c['Q_l_min_top'])} L/min "
                f"(calor {c['P_heat_W']:.0f} W, ΔT agua {_f(c['dT_water_K'])} K); recorrido medido en el bote + 20 %")
    elif s == "auto:oring_cord":
        qty, spec = oring_cord(man)
        unit = "m"
    elif s == "auto:filament":
        qty, spec = filament(inp, man)
        unit = "kg"
    elif s == "auto:pfd":
        qty = inp["operation"]["n_persons"]
        spec = (f"ISO 12402-3 (150 N) con cuello, {qty} por persona a bordo (operation.n_persons), rango de peso ≥ 100 kg; "
                "puesto y con el cordón del kill switch enganchado (research/R07)")
    elif s == "auto:imd":
        hv = sel.get("v_class", 48) >= 72
        qty = 1 if hv else 0
        price = inp["electrical"]["extra_72v_eur"]
        spec = ("IMD para sistema flotante > 50 V CC (R10b H8, R13 §4)" if hv
                else "No requerido: la selección es ≤ 50 V CC (qty 0)")
    elif s == "auto:hull_cut":
        x0, x1, py, rim = p.get("toma_plate_x0", 0), p.get("toma_plate_x1", 0), p.get("toma_plate_y", 0), p.get("toma_rim_w", 25)
        spec = (f"Recorte ≈ {x1 - x0 - 2 * rim:.0f} × {2 * py - 2 * rim:.0f} mm (cuerpo enrasado de P1-INT-02 = placa "
                f"{x1 - x0:.0f} × {2 * py:.0f} − ala de {rim:g} mm), en crujía de {x0:.0f} a {x1:.0f} mm a proa del espejo; "
                f"abertura hidráulica {p.get('L_open', 0):.0f} × {p.get('W_open', 0):.0f}; replantear sobre el casco medido")
    elif s == "auto:hull_transom":
        d = p.get("transom_hole_d", 160.0)
        spec = (f"Ø{_f(d)} mm en el espejo, centro en el eje de la tobera a z = {p.get('z_noz', 0):.0f} mm sobre la quilla "
                f"(plano P1-PMP-09); sierra de copa Ø{int(math.ceil(d / 5) * 5)} o calar + lima")
    if item.get("cable_mm2") is not None and str(item["cable_mm2"]).isdigit():
        price, tag = cable_price(inp, int(item["cable_mm2"]))
    if price == "auto" or price is None:
        raise ValueError(f"{item['id']}: precio auto sin resolver")
    if qty == "auto":
        raise ValueError(f"{item['id']}: cantidad auto sin resolver")
    return spec, float(price), float(qty), unit, link, tag


def check_rating(item, spec, sz, inp, flags):
    r = item.get("rating")
    if not r:
        return spec
    bat = inp["battery"]["options"][sz["selection"]["battery"]]
    I, V = sz["electrical"]["I_bat_peak_A"], bat["v_max"]
    bad = []
    if r.get("v") is not None and r["v"] < V:
        bad.append(f"{r['v']:g} V < {_f(V)} V de batería cargada")
    if r.get("role") == "power" and r.get("a") is not None and r["a"] < I:
        bad.append(f"{r['a']:g} A < {I:.0f} A de batería pico")
    if bad:
        flags.append({"ID": item["id"], "falla": "; ".join(bad), "qty": item["qty"]})
        return spec + " ⚠ NO CUMPLE: " + "; ".join(bad) + (" (por eso qty 0)" if item["qty"] == 0 else "")
    return spec + (f" ✔ {r.get('a', '—')} A / {r.get('v', '—')} V vs {I:.0f} A / {_f(V)} V" if r.get("role") == "power"
                   else f" ✔ {r.get('v')} V ≥ {_f(V)} V")


# ------------------------------------------------------------------------------------------------
# Materia prima de piezas mecanizadas
# ------------------------------------------------------------------------------------------------
def _std(v, lst):
    for x in lst:
        if x >= v - 1e-9:
            return float(x)
    return float(math.ceil(v / 10) * 10)


def classify(part, st):
    """Forma de compra de una pieza mecanizada según su bbox (o el override)."""
    ov = st.get("overrides", {}).get(part["id"], {})
    al = st["allowance"]
    bb = [float(x) for x in part["bbox_mm"]]
    if "by_service" in ov:
        return {"form": "service", "service": ov["by_service"]}
    if ov.get("form") == "weld":
        return {"form": "weld", "t": float(ov["t_mm"]), "nest": ov.get("nest", st["nest_factor_weld"]),
                "note": ov.get("note", "")}
    rev = None
    for i in range(3):
        for j in range(i + 1, 3):
            if abs(bb[i] - bb[j]) <= st["revolve_tol_frac"] * max(bb[i], bb[j]):
                rev = (max(bb[i], bb[j]), bb[3 - i - j])
    if ov.get("form") == "tube" or rev:
        D, L = rev if rev else (max(bb), min(bb))
        add = al["d_small_mm"] if D <= 10 else (al["d_mm"] if D <= 50 else max(al["d_mm"], al["d_frac"] * D))
        Ds = _std(D + add, st["bar_d_std_mm"])
        out = {"form": "bar", "D": D, "L": L, "Ds": Ds, "Ls": L + al["len_mm"]}
        if ov.get("form") == "tube":
            out.update(form="tube", ID=float(ov["id_mm"]), note=ov.get("note", ""))
        return out
    s = sorted(bb)
    if s[0] <= st["plate_max_t_mm"]:
        return {"form": "plate", "t": _std(s[0], st["plate_t_std_mm"]), "w": s[1] + al["plate_mm"], "h": s[2] + al["plate_mm"]}
    return {"form": "block", "dims": [x + al["block_mm"] for x in bb]}


def stock_rows(inp, man, date):
    st = inp["bom"]["stock"]
    mats = st["materials"]
    spares = st.get("spares", {})
    ids = {r["id"] for r in man["parts"]}
    for k in list(st.get("overrides", {})) + list(spares):
        if k not in ids:
            warn(f"stock: {k} no está en el manifest (¿cambió la geometría?)")
    bars, plates, singles, cls_of = {}, {}, [], {}
    for r in man["parts"]:
        if r["process"] != "torneada":
            continue
        c = classify(r, st)
        cls_of[r["id"]] = c
        if c["form"] == "service":
            continue
        m = mats.get(r["material"])
        if m is None:
            warn(f"{r['id']}: material '{r['material']}' sin precio en bom.stock.materials")
            continue
        n = r["qty"] + spares.get(r["id"], {}).get("qty", 0)
        if c["form"] == "bar":
            bars.setdefault((r["material"], c["Ds"]), []).append((r, n, c))
        elif c["form"] in ("plate", "weld"):
            if c["form"] == "plate":
                area = c["w"] * c["h"] * st["nest_factor_plate"] / 1e6
            else:
                area = r["mass_g_each"] / 1000 / (m["rho_g_cm3"] * 1000) / (c["t"] / 1000) * c["nest"]
            plates.setdefault((r["material"], c["t"]), []).append((r, n, c, area * n))
        else:
            singles.append((r, n, c))
    rows = []

    def mk(rid, mat, desc, spec, kg, price, tag, covers, link):
        m = mats[mat]
        return {"ID": rid, "categoria": CAT_MP, "descripcion": desc, "especificacion_minima": spec,
                "cantidad": 1.0, "unidad": "u", "proveedor_envio_DK": m["supplier"], "link_o_busqueda": link,
                "precio_unit_EUR": round(price, 2), "precio_total_EUR": round(price, 2), "envio": "eu",
                "alcance": "sistema", "etiqueta": tag, "verificado": "sí" if tag.startswith("[VERIFICADO") else "no",
                "cubre": " ".join(covers), "fecha": date, "_kg": kg}

    def est_tag(m):
        return f"[ESTIMADO: {m['eur_kg']:g} €/kg — base en inputs.yaml bom.stock.materials; corte a medida]"

    for (mat, Ds), lst in sorted(bars.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        m = mats[mat]
        Ltot = sum(n * c["Ls"] for _, n, c in lst)
        Lbuy = max(Ltot, st["bar_min_len_mm"] if Ds <= st.get("bar_min_len_d_max_mm", 40.0) else 0.0)
        kg = math.pi / 4 * (Ds / 1000) ** 2 * Lbuy / 1000 * m["rho_g_cm3"] * 1000
        vb = {float(k): float(v) for k, v in m.get("bars_eur_m", {}).items()}
        if Ds in vb:
            Lbuy = max(Lbuy, m.get("bars_min_len_mm", 0))
            price, tag = vb[Ds] * Lbuy / 1000, m["bars_tag"]
        else:
            price, tag = max(kg * m["eur_kg"], st["min_eur"]), est_tag(m)
        pieces = "; ".join(f"{r['id']} Ø{_f(c['D'])} × {_f(c['L'])} → {n} × {c['Ls']:.0f} mm" for r, n, c in lst)
        spec = (f"Barra redonda {m['grade']} Ø{Ds:g} × {Lbuy:.0f} mm ({_f(kg, 2)} kg) — {pieces}. "
                f"Sobremedida: Ø +{_f(st['allowance']['d_small_mm'])} (≤ 10) / +{st['allowance']['d_mm']:g} (≤ 50) / "
                f"+{st['allowance']['d_frac'] * 100:g} % mm; largo +{st['allowance']['len_mm']:g} mm")
        rows.append(mk(f"MP-{MAT_CODE.get(mat, mat)}-D{Ds:g}", mat, f"Barra {MAT_CODE.get(mat, mat)} Ø{Ds:g} (torno propio salvo servicio)",
                       spec, kg, price, tag, [r["id"] for r, _, _ in lst], m["link"].format(d=f"{Ds:g}", t="")))
    for (mat, t), lst in sorted(plates.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        m = mats[mat]
        area = sum(a for *_, a in lst)
        kg = area * t / 1000 * m["rho_g_cm3"] * 1000
        price = max(kg * m["eur_kg"], st["min_eur"])
        side = math.sqrt(area) * 1000
        pieces = "; ".join(
            (f"{r['id']} {c['w']:.0f} × {c['h']:.0f}" if c["form"] == "plate"
             else f"{r['id']} desarrollo ≈ {a / n * 1e6 / 1e4:.0f} dm²·{c['nest']:g} ({c['note']})") + (f" ×{n}" if n > 1 else "")
            for r, n, c, a in lst)
        spec = (f"Chapa {m['grade']} {t:g} mm, ≥ {_f(area, 3)} m² (≈ {side:.0f} × {side:.0f} o recortes) {_f(kg, 2)} kg — {pieces}")
        rows.append(mk(f"MP-{MAT_CODE.get(mat, mat)}-T{t:g}", mat, f"Chapa {MAT_CODE.get(mat, mat)} {t:g} mm", spec, kg, price,
                       est_tag(m), [r["id"] for r, *_ in lst], m["link"].format(d="", t=f"{t:g}")))
    for r, n, c in singles:
        m = mats[r["material"]]
        if c["form"] == "tube":
            Ds, ID = c["Ds"], c["ID"]
            kg = math.pi / 4 * ((Ds / 1000) ** 2 - (ID / 1000) ** 2) * c["Ls"] / 1000 * m["rho_g_cm3"] * 1000 * n
            spec = (f"Barra hueca / tubo grueso {m['grade']} Ø{Ds:g} / Ø{ID:g} × {c['Ls']:.0f} mm ({_f(kg, 2)} kg) — "
                    f"{r['id']} Ø{_f(c['D'])} × {_f(c['L'])}; {c['note']}; si no hay hueca: barra maciza Ø{Ds:g}")
            rid, desc = f"MP-{MAT_CODE.get(r['material'])}-TUBO-{r['id']}", f"Barra hueca {MAT_CODE.get(r['material'])} Ø{Ds:g} para {r['id']}"
            link = m["link"].format(d=f"{Ds:g}", t="").replace("Rundstab", "Hohlstange").replace("Rundstange", "Hohlstange")
        else:
            d = c["dims"]
            kg = d[0] * d[1] * d[2] / 1e9 * m["rho_g_cm3"] * 1000 * n
            spec = (f"Bloque {m['grade']} {d[0]:.0f} × {d[1]:.0f} × {d[2]:.0f} mm ({_f(kg, 2)} kg) — {r['id']} "
                    f"bbox {' × '.join(_f(x) for x in r['bbox_mm'])}")
            rid, desc = f"MP-{MAT_CODE.get(r['material'])}-BLQ-{r['id']}", f"Bloque {MAT_CODE.get(r['material'])} para {r['id']}"
            link = m["link"].format(d="", t=f"{d[0]:.0f}")
        rows.append(mk(rid, r["material"], desc, spec, kg, max(kg * m["eur_kg"], st["min_eur"]), est_tag(m), [r["id"]], link))
    # repuestos fabricados de la misma materia prima
    for pid, sp in spares.items():
        mp = next((x["ID"] for x in rows if pid in x["cubre"].split()), None)
        rows.append({"ID": sp["id"], "categoria": "Repuestos críticos", "descripcion": f"{sp['desc']} ({pid})",
                     "especificacion_minima": f"{sp['qty']} × {pid} torneados como la pieza; material incluido en {mp}",
                     "cantidad": float(sp["qty"]), "unidad": "u", "proveedor_envio_DK": "fabricación propia (torno)",
                     "link_o_busqueda": f"buscar: plano {pid} en 04_diseno/planos", "precio_unit_EUR": 0.0,
                     "precio_total_EUR": 0.0, "envio": "—", "alcance": "sistema",
                     "etiqueta": f"[CALCULADO: material en {mp}]", "verificado": "no", "cubre": pid, "fecha": date})
    return rows, cls_of


def needs_service(part, c, lathe_max):
    txt = f"{part.get('orientation') or ''} {part.get('desc', '')}"
    if c["form"] == "service" or c["form"] == "weld":
        return True
    if c["form"] in ("bar", "tube") and c["D"] > lathe_max:
        return True
    return bool(re.search(r"CNC|5 ejes|4 ejes|láser|soldad|fresad", txt, re.I))


# ------------------------------------------------------------------------------------------------
def main():
    inp = load_inputs()
    sz = load_json("sizing.json")
    man = load_json("manifest.json")
    B = inp["bom"]
    date = B["date"]
    rows, flags = [], []
    covered = {}
    for it in B["items"]:
        spec, price, qty, unit, link, tag = resolve(it, inp, sz, man)
        spec = check_rating(it, spec, sz, inp, flags)
        for pid in it.get("covers", []):
            covered.setdefault(pid, []).append(it["id"])
        rows.append({"ID": it["id"], "categoria": it["cat"], "descripcion": it["desc"],
                     "especificacion_minima": spec, "cantidad": qty, "unidad": unit,
                     "proveedor_envio_DK": it["supplier"], "link_o_busqueda": link,
                     "precio_unit_EUR": round(price, 2), "precio_total_EUR": round(price * qty, 2),
                     "envio": it.get("ship", "eu"), "alcance": it.get("scope", "sistema"), "etiqueta": tag,
                     "verificado": "sí" if tag.startswith("[VERIFICADO") else "no",
                     "cubre": " ".join(it.get("covers", [])), "fecha": it.get("date", date)})
    parts = {r["id"]: r for r in man["parts"]}
    for pid in covered:
        if pid not in parts:
            warn(f"covers: {pid} ({', '.join(covered[pid])}) no está en el manifest")
    # (1) toda pieza comprada cubierta
    unpriced = []
    for r in man["parts"]:
        if r["process"] == "comprada" and r["id"] not in covered:
            unpriced.append(r["id"])
            warn(f"pieza comprada {r['id']} ({r['desc']}) sin ítem con precio")
            rows.append({"ID": f"FALTA-{r['id']}", "categoria": "Sin precio", "descripcion": r["desc"],
                         "especificacion_minima": f"{r['material']}; bbox {r.get('bbox_mm')}", "cantidad": float(r["qty"]),
                         "unidad": "u", "proveedor_envio_DK": "—", "link_o_busqueda": f"buscar: {r['desc']}",
                         "precio_unit_EUR": 0.0, "precio_total_EUR": 0.0, "envio": "eu", "alcance": "sistema",
                         "etiqueta": "[SIN PRECIO: agregar ítem en inputs.yaml bom.items]", "verificado": "no",
                         "cubre": r["id"], "fecha": date})
    # (2) materia prima + servicios de las mecanizadas
    mp_rows, cls_of = stock_rows(inp, man, date)
    rows.extend(mp_rows)
    for r in rows:
        if r["categoria"] == CAT_SERVICE:
            for pid in r["cubre"].split():
                c0 = cls_of.get(pid)
                if c0 and c0["form"] == "service" and pid in parts:
                    cc = classify({**parts[pid], "id": "_"}, inp["bom"]["stock"])
                    m = inp["bom"]["stock"]["materials"].get(parts[pid]["material"], {"grade": parts[pid]["material"]})
                    stock = (f"barra {m['grade']} Ø{cc['Ds']:g} × {cc['Ls']:.0f} mm" if cc["form"] in ("bar", "tube")
                             else f"bloque {m['grade']} {' × '.join(f'{x:.0f}' for x in cc.get('dims', []))} mm")
                    r["especificacion_minima"] += (f". Material incluido en el servicio [CALCULADO del bbox]: {pid} "
                                                   f"{' × '.join(_f(x) for x in parts[pid]['bbox_mm'])} → {stock}")
    svc_cov = {}
    for it in B["items"]:
        if it["cat"] == CAT_SERVICE:
            for pid in it.get("covers", []):
                svc_cov.setdefault(pid, []).append(it["id"])
    no_service, mp_cov = [], {pid for x in mp_rows if x["categoria"] == CAT_MP for pid in x["cubre"].split()}
    for pid, c in cls_of.items():
        if c["form"] == "service":
            if c["service"] not in {it["id"] for it in B["items"]}:
                warn(f"{pid}: by_service {c['service']} no existe")
        elif pid not in mp_cov:
            warn(f"{pid}: pieza mecanizada sin materia prima")
        if needs_service(parts[pid], c, B["lathe_max_d_mm"]) and pid not in svc_cov:
            no_service.append(pid)
            warn(f"{pid} ({parts[pid]['desc'][:60]}) no sale del torno propio y no tiene servicio S-*")
    # (3) piezas impresas (costo en B-PETG) — una fila informativa por pieza
    for r in man["parts"]:
        if r["process"] == "impresa":
            rows.append({"ID": r["id"], "categoria": "Pieza impresa", "descripcion": f"{r['id']}_{r['name']} — {r['desc']}",
                         "especificacion_minima": f"{r['material']}; {r['mass_g_each']:.0f} g c/u; "
                                                  f"{r.get('print_hours_each', 0):.1f} h c/u; {r.get('orientation', '')}",
                         "cantidad": float(r["qty"]), "unidad": "u", "proveedor_envio_DK": "fabricación propia (Ender-3 S1)",
                         "link_o_busqueda": r["files"][0] if r.get("files") else "—", "precio_unit_EUR": 0.0,
                         "precio_total_EUR": 0.0, "envio": "—", "alcance": "sistema",
                         "etiqueta": "[CALCULADO] costo en B-PETG", "verificado": "no", "cubre": r["id"], "fecha": date})

    # ---------------------------------------------------------------- totales
    c = inp["costs"]
    dkk = inp["meta"]["eur_to_dkk"]

    def block(scope):
        rr = [r for r in rows if r["alcance"] == scope]
        sub = sum(r["precio_total_EUR"] for r in rr)
        ship = sum(r["precio_total_EUR"] for r in rr if r["envio"] == "eu") * c["shipping_frac"]
        cn_sup = sorted({r["proveedor_envio_DK"] for r in rr if r["envio"] == "cn" and r["precio_total_EUR"] > 0})
        imp = len(cn_sup) * c["cn_shipping_eur"] * (1 + c["import_vat_frac"])
        return rr, sub, ship, imp, cn_sup

    sys_rows, sub, ship, imp, cn_sup = block("sistema")
    cont = sub * c["contingency_frac"]
    total = sub + ship + imp + cont
    op_rows, sub_op, ship_op, _, _ = block("operacion")
    total_op = sub_op * (1 + c["shipping_frac"])
    h_rows, sub_h, ship_h, _, _ = block("casco")
    total_h = sub_h + ship_h + sub_h * c["contingency_frac"]
    sel = sz["selection"]
    bopt = inp["battery"]["options"][sel["battery"]]
    bat_chg = sum(r["precio_total_EUR"] for r in rows if r["ID"] in ("B-BAT", "B-CHG"))
    core = sum(r["precio_total_EUR"] for r in rows if r["ID"] in ("B-MOT", "B-ESC", "B-BAT", "B-CHG", "B-IMD"))
    eur_ver = sum(r["precio_total_EUR"] for r in sys_rows if r["verificado"] == "sí")
    by_cat = {}
    for r in rows:
        by_cat[r["categoria"]] = round(by_cat.get(r["categoria"], 0) + r["precio_total_EUR"], 2)
    priced = sorted([r for r in sys_rows if r["precio_total_EUR"] > 0], key=lambda r: -r["precio_total_EUR"])
    top = lambda lst, n: [{"ID": r["ID"], "descripcion": r["descripcion"], "EUR": r["precio_total_EUR"],  # noqa: E731
                           "etiqueta": r["etiqueta"]} for r in lst[:n]]
    summ = {"subtotal_eur": sub, "shipping_eur": ship, "import_cn_eur": imp, "cn_suppliers": cn_sup,
            "contingency_eur": cont, "total_eur": total, "total_dkk": total * dkk,
            "battery_eur": bopt["price_eur"], "battery_charger_eur": bat_chg,
            "operation_gear_eur": total_op, "total_with_gear_eur": total + total_op,
            "hull_changes_eur": total_h, "total_with_hull_and_gear_eur": total + total_op + total_h,
            "verified_rows": sum(1 for r in sys_rows if r["verificado"] == "sí" and r["precio_total_EUR"] > 0),
            "verified_frac_of_subtotal": eur_ver / sub if sub else 0.0,
            "fixed_excl_battery_eur": (sub - bat_chg) * (1 + c["contingency_frac"]) + ship + imp,
            "fixed_excl_core_eur": (sub - core) * (1 + c["contingency_frac"]) + ship + imp,
            "core_eur": core, "services_eur": by_cat.get(CAT_SERVICE, 0.0), "raw_material_eur": by_cat.get(CAT_MP, 0.0),
            "by_category": by_cat, "top10": top(priced, 10),
            "top_unverified": top([r for r in priced if r["verificado"] != "sí"], 10),
            "unpriced_bought_parts": unpriced, "machined_without_service": no_service,
            "electrical_rating_flags": flags, "warnings": WARN,
            "n_rows": len(rows), "date": date}
    rows_out = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    with open(ROOT / "bom.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows_out:
            w.writerow(r)
        for label, val in (("SUBTOTAL compras del sistema", sub),
                           (f"Envío UE ({c['shipping_frac'] * 100:.0f} % de ítems 'eu')", ship),
                           (f"Importación China: envío {c['cn_shipping_eur']:.0f} € × {len(cn_sup)} proveedores + IVA "
                            f"{c['import_vat_frac'] * 100:.0f} % del envío (el IVA de la mercadería ya está en el precio)", imp),
                           (f"Imprevistos ({c['contingency_frac'] * 100:.0f} %)", cont),
                           ("TOTAL SISTEMA EUR", total), ("TOTAL SISTEMA DKK", total * dkk),
                           ("Equipo de seguridad de operación (aparte, con envío)", total_op),
                           ("Cambios de casco que hace Jorge (aparte, con envío e imprevistos)", total_h),
                           ("TOTAL CON EQUIPO DE OPERACIÓN EUR", total + total_op),
                           ("TOTAL CON CASCO Y EQUIPO DE OPERACIÓN EUR", total + total_op + total_h)):
            w.writerow({"ID": "", "descripcion": label, "precio_total_EUR": round(val, 2),
                        "etiqueta": "[CALCULADO]", "fecha": date})
    with open(RESULTS_DIR / "bom_resumen.json", "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    cost_curve(inp, sz, summ)
    print(f"BOM: {len(rows)} filas; subtotal {sub:.0f} €, envío {ship:.0f} €, importación CN {imp:.0f} €, "
          f"imprevistos {cont:.0f} € → TOTAL SISTEMA {total:.0f} € ({total * dkk:.0f} DKK); "
          f"operación {total_op:.0f} €; casco {total_h:.0f} €; "
          f"{summ['verified_frac_of_subtotal'] * 100:.0f} % del subtotal con precio verificado; avisos: {len(WARN)}")
    return 0


def cost_curve(inp, sz, summ):
    """Costo total del sistema vs energía nominal por opción de batería (con V máx. de la optimización)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG_DIR.mkdir(exist_ok=True)
    sel = sz["selection"]
    k = 1 + inp["costs"]["contingency_frac"]
    rows = sz.get("optimization", {}).get("rows", [])
    pts = []
    for key, b in inp["battery"]["options"].items():
        E = b["v_nom"] * b["ah"] / 1000
        rr = [r for r in rows if r["battery"] == key]
        same = [r for r in rr if r["motor"] == sel["motor"] and r["esc"] == sel["esc"]]
        rr = same or rr
        if rr:
            best = max(rr, key=lambda r: (r["hard_ok"], r["vmax_cont_kmh"]))
            cost = summ["fixed_excl_core_eur"] + best["cost_eur"] * k
            lab = (f"{key}\n{_f(b['v_max'])} V · V máx. {_f(best['vmax_cont_kmh'])} km/h"
                   + ("" if best["hard_ok"] else " (no cumple)"))
            ok = best["hard_ok"]
        else:
            cost = summ["fixed_excl_battery_eur"] + (b["price_eur"] + b["charger"]["price_eur"]) * k
            lab, ok = f"{key}\n{_f(b['v_max'])} V", True
        pts.append((key, E, cost, lab, ok))
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ink, muted, accent = "#1f2933", "#7b8794", "#2563eb"
    for key, E, cost, lab, ok in pts:
        is_sel = key == sel["battery"]
        ax.plot(E, cost, "o", ms=9, color=accent if is_sel else muted, mfc=accent if is_sel else ("white" if not ok else muted),
                mew=2, zorder=3)
        ax.annotate(lab + ("\n(selección)" if is_sel else ""), (E, cost), textcoords="offset points",
                    xytext=(8, -6) if is_sel else (8, 6), fontsize=7.5, color=ink, va="top" if is_sel else "bottom")
    ax.set_xlabel("Energía nominal de la batería [kWh]")
    ax.set_ylabel("Costo total del sistema [EUR]")
    ax.set_title("Costo del sistema vs energía por opción de batería (BOM + mejor fila de sizing)", fontsize=10)
    ax.grid(alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    x0 = min(p[1] for p in pts)
    x1 = max(p[1] for p in pts)
    ax.set_xlim(x0 - 0.3, x1 + 1.3)
    y0, y1 = min(p[2] for p in pts), max(p[2] for p in pts)
    pad = max(0.12 * (y1 - y0), 150.0)
    ax.set_ylim(y0 - pad, y1 + 1.2 * pad)
    fig.text(0.01, 0.01, "● lleno: cumple todas las restricciones duras · ○ vacío: no cumple (V máx. = continua, banda de diseño)",
             fontsize=7, color=muted)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG_DIR / "costo_autonomia.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
