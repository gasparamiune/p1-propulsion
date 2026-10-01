#!/usr/bin/env python3
"""docgen.py — Mantiene los .md coherentes con lo que calcula el código.

Reemplaza en todos los .md del proyecto:
  • Bloques   <!-- AUTO:nombre --> ... <!-- /AUTO:nombre -->   por tablas generadas.
  • Valores   <!--V:fuente.ruta.al.valor:formato-->texto<!--/V-->  por el valor actual.
    fuente ∈ {sizing, bom, manifest, est, verify}; formato estilo Python (p. ej. .0f, .2f).
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


def blocks(sz, bom, man, est, ver):
    B = {}
    B["sizing_main"] = sizing_section("Resumen")
    B["sizing_sweep"] = sizing_section("Barrido de velocidad")
    B["sizing_sustain"] = sizing_section("Tiempo sostenible a velocidad alta")
    B["sizing_sens"] = sizing_section("Sensibilidad")
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
                             f"(a {load_inputs_rate()} g/h); masa de la unidad basculante (CAD): **{t['unit_mass_kg_cad']:.2f} kg**.")
    if bom:
        rows = [[k, f"{v:.0f}"] for k, v in sorted(bom["by_category"].items(), key=lambda kv: -kv[1]) if v > 0]
        rows += [["**Subtotal**", f"**{bom['subtotal_eur']:.0f}**"], ["Envío", f"{bom['shipping_eur']:.0f}"],
                 ["Imprevistos", f"{bom['contingency_eur']:.0f}"],
                 ["**TOTAL**", f"**{bom['total_eur']:.0f} € ≈ {bom['total_dkk']:.0f} DKK**"]]
        B["bom_summary"] = table(["Categoría", "EUR [ESTIMADO]"], rows)
    if ver:
        B["verify"] = (f"Resultado: **{'OK' if ver['ok'] else 'FALLAS'}** — {len(ver['parts'])} piezas, "
                       f"{ver['n_pair_checks']} pares×estados de interferencia; dirección ψ ∈ {ver['states']['steer']}°, "
                       f"basculación φ ∈ {ver['states']['tilt']}°; masa unidad CAD {ver['unit_mass']['cad_kg']:.2f} kg vs "
                       f"estimación {ver['unit_mass']['estimate_kg']} kg." + ("" if ver["ok"] else "\n\nFallas:\n" + "\n".join("- " + f for f in ver["fails"])))
    if sz:
        rows = []
        for r in sorted(sz["optimization"], key=lambda r: (not r["hard_ok"], r["cost_eur"]))[:14]:
            fails = [k[3:] for k in r if k.startswith("ok_") and not r[k]]
            rows.append([r["prop"], r["battery"], f"{r['z_motor']}:{r['z_shaft']}", f"{r['P_bat_cruise_des_W']:.0f}",
                         f"{r['E_req_wh']:.0f}/{r['E_nom_wh']:.0f}", f"{r['autonomy_des_h']:.2f}", f"{r['vmax_nom_kmh']:.1f}",
                         f"{r['bollard_N']:.0f}", f"{r['cost_eur']:.0f}", ", ".join(fails) or "—"])
        B["optimization"] = table(["Hélice", "Batería", "Poleas", "P_bat crucero diseño [W]", "E req/nom [Wh]",
                                   "Autonomía diseño [h]", "V máx nom [km/h]", "Bollard [N]", "Costo hélice+bat [€]",
                                   "No cumple"], rows)
        cav = sz["cavitation"]
        B["cavitation"] = table(["Condición", "T [N]", "n [rpm]", "σ0.7R", "τc", "τc límite (Burrill aprox.)", "AE/A0 mín Keller", "AE/A0"],
                                [[k, f"{v['T_N']:.0f}", f"{v['n_rpm']:.0f}", f"{v['sigma07']:.2f}", f"{v['tau_c']:.3f}",
                                  f"{v['tau_limit']:.3f}", f"{v['keller_min_BAR']:.2f}", f"{v['BAR']:.2f}"] for k, v in cav.items()])
        th = sz["thermal"]
        B["thermal"] = table(["Condición", "Pérdida motor [W]", "Pérdida ESC [W]", "T motor estac. [°C]", "t a límite [min]"],
                             [[k, f"{v['P_loss_motor_W']:.0f}", f"{v.get('P_loss_esc_W', float('nan')):.0f}",
                               f"{v.get('T_motor_steady_C', float('nan')):.0f}",
                               "∞" if v["t_to_limit_min"] == float("inf") or v["t_to_limit_min"] > 1e6 else f"{v['t_to_limit_min']:.0f}"]
                              for k, v in th.items()])
        te = sz["thermal_esc"]
        hs = te["heatsink"]
        B["thermal_esc"] = table(["Condición", "Pérdida ESC [W]", "Sol [W]", "R disipador máx. [K/W]"],
                                 [[k, f"{te[k]['P_loss_esc_W']:.0f}", f"{te[k]['sun_W']:.0f}", f"{te[k]['R_hs_max_K_W']:.2f}"]
                                  for k in ("esc_cruise", "esc_vmax")]
                                 + [["Requisito de compra (crucero → caja ≤ " + f"{hs['T_box_max_C']:.0f} °C)", "", "",
                                     f"**≤ {hs['R_hs_required_K_W']:.2f}**"],
                                    [f"Con ese disipador, a V máx sostenida: {hs['T_vmax_steady_C']:.0f} °C estacionario "
                                     f"(límite ESC {hs['t_esc_limit_C']:.0f} °C)", "", "",
                                     "∞" if hs["t_vmax_to_limit_min"] == float("inf") else f"{hs['t_vmax_to_limit_min']:.0f} min"]])
        lg = sz["legal_speed"]
        B["legal_speed"] = table(["Magnitud", "Valor", "Etiqueta"], [
            ["Límite legal a < 300 m de la costa", f"{lg['limit_kmh']:.2f} km/h (5 kn)", "[VERIFICADO: research/R07 §1.2]"],
            [f"V máx con carga liviana ({lg['mass_light_kg']:.0f} kg), batería llena, banda baja", f"{lg['vmax_light_low_kmh']:.1f} km/h", "[CALCULADO]"],
            ["¿Cumple sin limitador?", "sí" if lg["ok_by_physics"] else "**no → tope de ERPM 'modo costa'**", "[CALCULADO]"],
            ["Tope de rpm del motor / ERPM (VESC `l_max_erpm`)", f"{lg['rpm_cap_motor']:.0f} rpm / {lg['erpm_cap']:.0f} ERPM", "[CALCULADO]"],
            ["V máx a plena carga con el tope (banda nominal)", f"{lg['vmax_full_load_with_cap_kmh']:.1f} km/h", "[CALCULADO]"],
        ])
    return B


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
    srcs = {"sizing": sz, "bom": bom, "manifest": man, "est": est, "verify": ver, "arch": arch}
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
