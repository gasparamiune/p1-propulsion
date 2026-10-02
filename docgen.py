#!/usr/bin/env python3
"""docgen.py — Mantiene los .md coherentes con lo que calcula el código.

Reemplaza en todos los .md del proyecto:
  • Bloques   <!-- AUTO:nombre --> ... <!-- /AUTO:nombre -->   por tablas generadas.
  • Valores   <!--V:fuente.ruta.al.valor:formato-->texto<!--/V-->  por el valor actual.
    fuente ∈ {sizing, bom, manifest, est, verify, arch, cmp}; formato estilo Python (p. ej. .0f, .2f).
Así ningún número de los documentos queda desincronizado de resultados/*.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT / "resultados"


def load(name):
    p = RES / name
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sizing_section(title):
    txt = (RES / "sizing_tablas.md").read_text(encoding="utf-8")
    parts = re.split(r"^## ", txt, flags=re.M)
    for prt in parts:
        if prt.startswith(title):
            return prt[len(title):].strip()
    return f"(sección '{title}' no encontrada)"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def _fmt(x, f=".0f", inf="∞"):
    try:
        return inf if x == float("inf") or x > 1e8 else format(x, f)
    except (TypeError, ValueError):
        return str(x)


def blocks(sz, bom, man, est, ver):
    B = {}
    if (RES / "sizing_tablas.md").exists():
        B["sizing_main"] = sizing_section("Resumen")
        B["sizing_curve"] = sizing_section("Curva a fondo (potencia pico, banda de diseño, batería nominal)")
        B["sizing_pump"] = sizing_section("Triángulos de velocidad del impulsor")
        B["optimization"] = sizing_section("Optimizador (15 mejores)")
    if est:
        B["estructural"] = (RES / "estructural_tabla.md").read_text(encoding="utf-8").split("\n", 1)[1].strip()
    if man:
        rows = []
        for r in man["parts"]:
            env = r.get("print_bbox_mm") or r.get("bbox_mm")
            env_s = "×".join(f"{x:.0f}" for x in env) if env else "—"
            rows.append([r["id"] + "_" + r["name"], r["desc"], env_s, r["material"], r["process"], r["qty"],
                         r["load_case"], r["orientation"] if r["process"] == "impresa" else "—",
                         f"{r['mass_g_each']:.0f}", f"{r.get('print_hours_each', 0):.1f}" if r["process"] == "impresa" else "—"])
        B["parts_list"] = table(["ID", "Función", "Envolvente [mm]", "Material", "Proceso", "Cant.", "Caso de carga dominante",
                                 "Orientación de impresión", "g c/u", "h c/u"], rows)
        t = man["totals"]
        B["parts_totals"] = (f"Total impreso: **{t['printed_mass_g']/1000:.2f} kg** de PETG, **{t['printed_hours']:.0f} h** de impresión "
                             f"(a {load_inputs_rate()} g/h); masa de la unidad de jet (CAD, sin motor): **{t.get('jet_unit_mass_kg', 0):.2f} kg**.")
    if bom:
        rows = [[k, f"{v:.0f}"] for k, v in sorted(bom["by_category"].items(), key=lambda kv: -kv[1]) if v > 0]
        rows += [["**Subtotal**", f"**{bom['subtotal_eur']:.0f}**"], ["Envío", f"{bom['shipping_eur']:.0f}"],
                 ["Imprevistos", f"{bom['contingency_eur']:.0f}"],
                 ["**TOTAL**", f"**{bom['total_eur']:.0f} € ≈ {bom['total_dkk']:.0f} DKK**"]]
        B["bom_summary"] = table(["Categoría", "EUR"], rows)
    if ver:
        B["verify"] = (f"Resultado: **{'OK' if ver['ok'] else 'FALLAS'}** — {len(ver['parts'])} piezas, "
                       f"{ver['n_pair_checks']} pares×estados de interferencia; boquilla δ ∈ {ver['states']['steer']}°, "
                       f"bucket {{arriba, abajo}}; masa de la unidad de jet (CAD) {ver.get('jet_mass', {}).get('cad_kg', 0):.2f} kg."
                       + ("" if ver["ok"] else "\n\nFallas:\n" + "\n".join("- " + f for f in ver["fails"])))
    if sz:
        sn = sz.get("sensitivity", {})
        if sn:
            pm = sz_inputs("operation.plane_margin_frac")
            B["sizing_sens"] = table(["Entrada incierta", "Rango", "V máx. sostenida [km/h] (bajo / alto)",
                                      "Margen en la joroba (bajo / alto)",
                                      f"¿Margen ≥ {pm*100:.0f} % (restricción dura) en ambos extremos?"],
                                     [[r["label"], f"{_fmt(r['lo']['value'], '.3g')} – {_fmt(r['hi']['value'], '.3g')}",
                                       f"{r['lo']['vmax']:.1f} / {r['hi']['vmax']:.1f}",
                                       f"{r['lo']['hump']*100:.0f} % / {r['hi']['hump']*100:.0f} %",
                                       "sí" if (r["lo"].get("hump_ok", r["lo"]["planes"]) and r["hi"].get("hump_ok", r["hi"]["planes"]))
                                       else ("**NO**" + ("" if (r["lo"]["planes"] and r["hi"]["planes"]) else " (no cruza)"))]
                                      for r in sn["rows"]])
        lg, pf = sz["legal_speed"], sz["performance"]
        B["legal_speed"] = table(["Magnitud", "Valor", "Etiqueta"], [
            ["Límite legal a < 300 m de la costa", f"{sz_inputs('operation.legal_speed_limit_kmh'):.2f} km/h (5 kn)", "[VERIFICADO: research/R07, R13]"],
            [f"Tope de rpm 'modo costa' (piloto liviano, {lg['mass_light_kg']:.0f} kg, banda baja, batería llena)",
             f"{lg['rpm_cap']:.0f} rpm / {lg['erpm_cap']:.0f} ERPM", "[CALCULADO] → VESC `l_max_erpm` en el perfil de costa"],
        ] + ([
            ["COSTA a fondo, piloto liviano (banda baja, batería llena)",
             f"{lg['costa']['light_low']['V_kmh']:.1f} km/h, {lg['costa']['light_low']['P_bat_W']:.0f} W", "[CALCULADO] (el caso del tope)"],
            ["COSTA a fondo, piloto de diseño (banda nominal / alta, batería nominal)",
             f"{lg['costa']['design_nominal']['V_kmh']:.1f} / {lg['costa']['design_high']['V_kmh']:.1f} km/h, "
             f"{lg['costa']['design_nominal']['P_bat_W']:.0f} / {lg['costa']['design_high']['P_bat_W']:.0f} W "
             f"(autonomía {lg['costa']['design_high']['autonomy_h']:.1f} h)", "[CALCULADO]"],
        ] if "costa" in lg else []) + [
            ["P de batería para ir a 5 kn con el piloto de diseño (banda alta)",
             f"{lg['P_bat_legal_W']:.0f} W a {lg['n_legal_rpm']:.0f} rpm"
             + ("" if lg.get("legal_rpm_reachable_in_costa", True) else " — por encima del tope de COSTA: solo con el perfil ABIERTO"),
             "[CALCULADO] (energía de la misión, conservador)"],
            ["Autonomía a esa potencia", f"{lg['autonomy_legal_h']:.1f} h", "[CALCULADO]"],
        ])
        th, el, en, me, cl = sz["thermal"], sz["electrical"], sz["energy"], sz["mech"], sz.get("cooling", {})
        _px = ROOT / "04_diseno" / "electronica" / "electronica.json"
        elx = json.loads(_px.read_text(encoding="utf-8")) if _px.exists() else {}
        B["thermal"] = table(["Magnitud", "Valor", "Etiqueta"], [
            ["Pérdida del motor a V máx. sostenida", f"{th['P_loss_motor_W']:.0f} W", "[CALCULADO]"],
            ["T del motor estacionaria (aire 30 °C, refrigeración por agua)", f"{th['T_motor_steady_C']:.0f} °C (máx. {th['t_winding_max_C']:.0f})", "[CALCULADO, R_th ESTIMADO]"],
            ["Pérdida del controlador a V máx. sostenida", f"{th['P_loss_esc_W']:.0f} W", "[CALCULADO]"],
            ["Agua de refrigeración (orificio, a V máx. / a 5 kn)", f"{cl.get('Q_l_min_top', 0):.1f} / {cl.get('Q_l_min_legal', 0):.1f} L/min", "[CALCULADO]"],
            ["Salto de temperatura del agua", f"{cl.get('dT_water_K', 0):.1f} K", "[CALCULADO]"],
            ["V máx. por ratos (potencia pico)", f"{pf.get('vmax_peak_kmh', 0):.1f} km/h, "
             + ("sin límite térmico del motor" if pf.get('t_peak_from_cruise_min', 0) in (float('inf'),) or pf.get('t_peak_from_cruise_min', 0) > 1e6
                else f"{pf.get('t_peak_from_cruise_min', 0):.0f} min hasta el límite"), "[CALCULADO]"],
        ])
        B["electrical"] = table(["Magnitud", "Valor", "Etiqueta"], [
            ["Corriente de batería pico / a V máx. sostenida", f"{el['I_bat_peak_A']:.0f} / {el['I_bat_top_A']:.0f} A", "[CALCULADO]"],
            ["Límite de corriente de fase (controlador)", f"{el['I_phase_limit_A']:.0f} A", "[CALCULADO]"],
            ["Fusible principal", f"{el['fuse_a']} A", "[CALCULADO]"],
            ["Cable DC (batería → controlador)", f"{el['cable_dc']['section_mm2']} mm² ({el['cable_dc']['drop_frac']*100:.1f} %)", "[CALCULADO]"],
            ["Fases controlador → motor", "cables propios del motor (6 AWG) y del controlador (8 AWG) con conectores bala de 8 mm, sin tramo agregado"
             + (f"; caída ≈ {elx['cables']['phase_drop_leads_frac']*100:.2f} % a {elx['cables']['I_phase_limit_A']:.0f} A"
                if elx.get("cables", {}).get("phase_drop_leads_frac") is not None else ""),
             "[CALCULADO: 04_diseno/electronica/calc_electronica.py; calibres VERIFICADOS en inputs.yaml]"],
            ["Energía usable / requerida por la misión", f"{en['E_usable_wh']:.0f} / {en['E_req_wh']:.0f} Wh", "[CALCULADO]"],
        ])
        sp = me.get("shear_pin", {})
        B["mech"] = table(["Magnitud", "Valor", "Etiqueta"], [
            ["Par máx. del controlador / a V máx.", f"{me['T_max_Nm']:.1f} / {me['T_top_Nm']:.1f} N·m", "[CALCULADO]"],
            ["Eje Ø20 316: FS estático / fatiga", f"{me['fs_shaft_static']:.1f} / {me['fs_shaft_fatigue']:.1f}", "[CALCULADO]"],
            ["Pasador de corte", f"Ø{sp.get('d_mm', 0)} {sp.get('material', '')}: corta a {sp.get('T_cut_Nm', 0):.1f} N·m "
             f"(FS del eje al corte {sp.get('fs_shaft_at_cut', 0):.1f})"
             + (f"; con τ_u {sp['tau_u_hi_mpa']:.0f} MPa corta a {sp['T_cut_hi_Nm']:.1f} N·m (FS del eje {sp['fs_shaft_at_cut_hi']:.1f})"
                if "T_cut_hi_Nm" in sp else ""), "[CALCULADO: research/R12 §7.6; τ_u alto ESTIMADO]"],
            ["Empuje axial máx. al par de rodamientos", f"{me['Fa_max_N']:.0f} N", "[CALCULADO]"],
            ["Vida L10 a V máx.", f"{_fmt(me['L10_top_h'])} h", "[CALCULADO]"],
            ["Velocidad crítica / rpm máx.", f"{me['n_crit_rpm']:.0f} / {me['n_max_rpm']:.0f} rpm ({me['crit_ratio']:.1f}×)", "[CALCULADO]"],
            ["Velocidad periférica en el sello", f"{me['seal_speed_ms']:.1f} m/s", "[CALCULADO]"],
        ])
    return B


def sz_inputs(path):
    import yaml
    with open(ROOT / "inputs.yaml", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    for k in path.split("."):
        d = d[k]
    return d


def load_inputs_rate():
    import yaml
    with open(ROOT / "inputs.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["printer"]["print_rate_g_h"]


def getpath(src, path):
    cur = src
    for k in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(k)]
        else:
            cur = cur[k]
    return cur


def main():
    sz, bom, man, est, ver = load("sizing.json"), load("bom_resumen.json"), load("manifest.json"), load("estructural.json"), load("verify.json")
    arch = load("arquitectura.json")
    cmp_ = load("comparacion.json")
    srcs = {"sizing": sz, "bom": bom, "manifest": man, "est": est, "verify": ver, "arch": arch, "cmp": cmp_}
    B = blocks(sz, bom, man, est, ver)
    if (RES / "arquitectura_tabla.md").exists():
        B["arch"] = (RES / "arquitectura_tabla.md").read_text(encoding="utf-8").strip()
    pat_block = re.compile(r"(<!-- AUTO:(\w+) -->)(.*?)(<!-- /AUTO:\2 -->)", re.S)
    pat_val = re.compile(r"(<!--V:([\w.]+):([^>]*?)-->)(.*?)(<!--/V-->)", re.S)
    n_b = n_v = 0
    missing = []
    for md in sorted(list(ROOT.glob("*.md")) + list((ROOT / "04_diseno").rglob("*.md"))):
        txt = md.read_text(encoding="utf-8")
        orig = txt

        def rb(m):
            nonlocal n_b
            name = m.group(2)
            if name not in B:
                missing.append(f"{md.name}: bloque {name}")
                return m.group(0)
            n_b += 1
            return f"{m.group(1)}\n{B[name]}\n{m.group(4)}"

        def rv(m):
            nonlocal n_v
            path, fmt = m.group(2), m.group(3)
            src, _, rest = path.partition(".")
            try:
                val = getpath(srcs[src], rest)
                s = format(val, fmt) if fmt else str(val)
            except Exception:
                missing.append(f"{md.name}: valor {path}")
                return m.group(0)
            n_v += 1
            return f"{m.group(1)}{s}{m.group(5)}"

        txt = pat_block.sub(rb, txt)
        txt = pat_val.sub(rv, txt)
        if txt != orig:
            md.write_text(txt, encoding="utf-8")
    print(f"docgen: {n_b} bloques y {n_v} valores actualizados")
    for m in missing:
        print("  FALTA:", m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
