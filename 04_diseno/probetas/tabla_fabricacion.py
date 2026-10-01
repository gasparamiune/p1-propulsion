#!/usr/bin/env python3
"""tabla_fabricacion.py — Regenera las tablas de 05_fabricacion.md (bloques <!-- FAB:nombre --> … <!-- /FAB:nombre -->).

Fuentes: resultados/manifest.json (id, name, qty, print_rot, orientation, load_case, print_bbox_mm,
mass_g_each, print_hours_each, solid_frac), resultados/estructural.json (FS mín. por pieza),
04_diseno/probetas/probetas_manifest.json (probetas y criterios), prusaslicer/slice_report.json (laminado
real, si existe) y el código de 04_diseno/piezas/ (tuercas cautivas e insertos). Familia y ajustes por
objeto: familias.py. También refresca los valores <!--V:…--> del propio 05 (mismo formato que docgen.py).
Re-ejecutable:  python 04_diseno/probetas/tabla_fabricacion.py   (no toca otros archivos)
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "04_diseno"))
import familias as FAM  # noqa: E402

DOC = ROOT / "05_fabricacion.md"
SPOOL_MARGIN = 1.30          # = bom.py: +30 % purga, probetas, reimpresiones


def jload(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def n(v, nd=0):
    if v is None:
        return "—"
    s = f"{v:,.{nd}f}".replace(",", " ")
    return s.replace(".", ",")


def fs_min(est, pid):
    best = None
    for r in est.get("rows", []):
        base = r["part"].split(" ")[0]
        ids = {base}
        if "/" in base:
            pre = base[:base.rfind("-") + 1]
            ids = {pre + x for x in base[base.rfind("-") + 1:].split("/")}
        if pid in ids and (best is None or r["FS"] < best["FS"]):
            best = r
    return best


def slice_items(rep):
    return {(it["tipo"], it["id"]): it for it in rep.get("laminado", {}).get("items", [])}


# ---------------------------------------------------------------------------
def blk_orientacion(man, est, rep):
    sl = slice_items(rep)
    rows = []
    for r in man["parts"]:
        if r["process"] != "impresa":
            continue
        fam, why = FAM.familia(r)
        inf = FAM.relleno(r, fam)
        b = FAM.brim(r)
        fs = fs_min(est, r["id"])
        lc = fs["load_case"] if fs else ""
        lc = lc if len(lc) <= 60 else lc[:58].rstrip(" (") + "…"
        fs_s = "—" if not fs else (f"{n(fs['FS'], 2)} ({lc})"
                                    + (" — fusible por diseño" if r["id"] == "P1-PRP-02" and fs["FS"] < 1.5 else ""))
        it = sl.get(("pieza", r["id"]))
        if it and it.get("ok"):
            sup = "sí" if it.get("con_soporte", {}).get("soporte") else "no"
            if it.get("avisos"):
                sup += " · " + ", ".join(a for a in it["avisos"] if a != "Consider enabling supports")
            h = n(it["h"], 1)
        else:
            sup, h = "[NO EJECUTADO]", "—"
        bb = "×".join(n(x, 0) for x in r["print_bbox_mm"])
        rows.append([r["id"], r["name"], r["qty"], f"**{fam}** {inf} %" + (f", brim {b}" if b else ""),
                     r["load_case"], f"{r['orientation']} `print_rot={tuple(r['print_rot'])}`", bb, fs_s, sup,
                     n(r["mass_g_each"], 0), n(r["print_hours_each"], 1), h])
    return table(["ID", "Pieza", "Cant.", "Perfil, relleno", "Carga dominante (manifest)",
                  "Orientación de impresión: por qué (manifest)", "Envolvente impresión [mm]",
                  "FS mín. (estructural.json)", "Soporte auto / avisos PrusaSlicer", "g c/u (CAD)",
                  "h c/u (18 g/h)", "h c/u (PrusaSlicer)"], rows)


def blk_probetas(pm, rep):
    sl = slice_items(rep)
    rows = []
    for r in pm.get("probetas", []):
        it = sl.get(("probeta", r["id"]))
        h = n(it["h"], 1) if it and it.get("ok") else "—"
        ov = FAM.overrides(r, r["profile"])
        rows.append([r["test"], f"`{r['file_stem']}`", r["profile"] + (f" ({', '.join(f'{k}={v}' for k, v in ov.items())})" if ov else ""),
                     r["qty"], "×".join(n(x, 0) for x in r["print_bbox_mm"]), n(r["mass_g_each"], 1), h,
                     "sí" if r.get("ok_manifold") else "NO", r["desc"]])
    return table(["Ensayo", "Archivo (step/ y stl/)", "Perfil (ajustes por objeto)", "Cant.", "Envolvente [mm]",
                  "g c/u", "h c/u (PrusaSlicer)", "Malla cerrada", "Descripción"], rows)


def blk_criterios(pm):
    T = pm.get("tests", {})
    rows = []
    c = T.get("P1.1", {}).get("criterios", {})
    if c:
        rows.append(["P1.1", "holgura deslizante sin juego", f"elegir entre {', '.join(n(x, 2) for x in c['holguras_mm'])} mm "
                     f"(CAD hoy {n(c['clearance_cad_mm'], 2)})", "—", "PENDIENTES §P1.1"])
    c = T.get("P1.2", {}).get("criterios", {})
    if c:
        rows.append(["P1.2", f"{c['rodamiento']}: asiento a presión / deslizante",
                     f"Ø{n(c['D_mm'], 0)} {', '.join(n(x, 2) for x in c['asientos_presion_mm'])} (presión); "
                     f"{n(c['asiento_HSG02_mm'], 2)} (HSG-02)", f"pared {n(c['pared_mm'], 2)} mm = HSG-02", "PENDIENTES §P1.2"])
    c = T.get("P1.3", {}).get("criterios", {})
    if c:
        pr = c["prediccion"]
        rows.append(["P1.3", "arranque de tuerca M6 en bolsillo transversal",
                     f"≥ {n(c['umbral_N'])} N (= {n(c['FS'], 0)} × {n(c['F_perno_N'])} N); PENDIENTES pide ≥ "
                     f"{n(c['umbral_PENDIENTES_N'])} N → usar el mayor",
                     f"apoyo bajo tuerca ≈ {n(pr['F_aplastamiento_bajo_tuerca_N'])} N; corte ≈ {n(pr['F_corte_seco_N'])} N "
                     "[ESTIMADO]", "estructural.json + R05 S1"])
    c = T.get("P1.4", {}).get("criterios", {})
    if c:
        rows.append(["P1.4", "arranque de inserto M4 inox (reborde ELE-01)",
                     f"≥ {n(c['umbral_N'])} N (= {n(c['FS'], 0)} × {n(c['F_inserto_N'])} N); PENDIENTES ≥ "
                     f"{n(c['umbral_PENDIENTES_N'])} N", "PEM M4 en ABS inyectado 912–1646 N [VERIFICADO: R05 S29]",
                     "estructural.json"])
    c = T.get("P1.5", {}).get("criterios", {})
    if c:
        rows.append(["P1.5", "flexión 3 puntos, luz " + n(c["luz_mm"]) + " mm",
                     "σ_mojada/σ_seca ≥ f_water; σ_Z/σ_XY ≥ f_z",
                     f"XY seca ≥ {n(c['F_pred_XY_seca_N'])} N, mojada ≥ {n(c['F_pred_XY_mojada_N'])} N, Z ≥ "
                     f"{n(c['F_pred_Z_seca_N'])} N [ESTIMADO: piso]", "inputs.yaml materials"])
    c = T.get("P1.6", {}).get("criterios", {})
    if c:
        rows.append(["P1.6", "estanqueidad 24 h a 0,5 m (" + n(c["presion_0_5m_kPa"], 1) + " kPa)",
                     "papel tisú seco, 0 gotas",
                     f"ranura {n(c['ranura_mm'][0], 2)}×{n(c['ranura_mm'][1], 2)} mm; cordón {n(c['cordon_mm'], 2)} mm × "
                     f"{n(c['largo_cordon_mm'])} mm; planitud ≤ {n(c['planitud_max_mm'], 2)} mm", "R05 B3 (Parker)"])
    c = T.get("P1.7", {}).get("criterios", {})
    if c:
        rows.append(["P1.7", f"absorción 7 días, {n(c['sal_g_L'])} g/L", "ganancia ≤ 1 %", "PETG macizo ~0,3 % [VERIFICADO: R05 S11]",
                     "PENDIENTES §P1.7"])
    c = T.get("P1.8", {}).get("criterios", {})
    if c:
        rows.append(["P1.8", f"rotura del cuello {n(c['seccion_mm'][0], 2)}×{n(c['seccion_mm'][1], 0)} mm, brazo "
                     f"{n(c['brazo_ref_mm'], 1)} mm", f"{n(c['banda_N'][0])}–{n(c['banda_N'][1])} N (mojadas)",
                     f"mojada ≈ {n(c['F_pred_mojada_raiz_N'])} N, seca ≈ {n(c['F_pred_seca_raiz_N'])} N [CALCULADO]",
                     "PENDIENTES §P1.8 + params"])
    return table(["Ensayo", "Qué se mide", "Pasa si", "Predicción / referencia", "Fuente del umbral"], rows)


def blk_ajustes(pm):
    aj = pm.get("tests", {}).get("P1.1", {}).get("criterios", {}).get("ajustes_en_piezas", [])
    rows = []
    for r in sorted(aj, key=lambda x: (x["d_nom"], x["id"])):
        c = r["holgura_cad"]
        if c >= 0.39:
            cal = "pasante de perno (no es ajuste)"
        elif c <= 0:
            cal = "ajuste a presión: fila Ø" + n(r["d_nom"]) + (" de P1.1H" if r["eje_impresion"] == "horizontal" else " de P1.1A/B")
        else:
            cal = "P1.1H (horizontal)" if r["eje_impresion"] == "horizontal" else "P1.1A/B (vertical)"
        rows.append([r["id"], f"Ø{n(r['d_nom'])}", n(r["D_cad"], 2), f"{c:+.2f}".replace(".", ","), r["eje_impresion"], cal])
    return table(["Pieza", "Nominal (metal/POM)", "Ø en CAD [mm]", "Holgura CAD [mm]", "Eje en impresión", "Se calibra con"], rows)


def blk_roscas():
    sys.path.insert(0, str(ROOT / "04_diseno"))
    from cadlib import INSERT_HOLE, INSERT_LEN, NUT_AF, NUT_M  # noqa: F401
    ns = {"NUT_AF": NUT_AF, "NUT_M": NUT_M, "INSERT_HOLE": INSERT_HOLE, "INSERT_LEN": INSERT_LEN}
    rows = []
    for f in sorted((ROOT / "04_diseno" / "piezas").glob("P1-*.py")):
        lines = f.read_text(encoding="utf-8").splitlines()
        pid = f.stem.split("_")[0]
        last_comment = ""
        for i, l in enumerate(lines):
            s = l.strip()
            if s.startswith("#"):
                last_comment = s.lstrip("# ").strip()
            m_nut = re.search(r"NUT_AF\[(\d+)\]", l)
            m_ins = re.search(r"INSERT_HOLE\[(\d+)\]", l)
            if not (m_nut or m_ins) or "def " in l or s.startswith("#") or "sep =" in l or "checks" in l:
                continue
            com = (l.split("#", 1)[1].strip() if "#" in l else last_comment)[:90]
            if m_nut:
                kind = ("tuerca cautiva, bolsillo hexagonal" if "hex_prism" in l else
                        "tuerca cautiva, bolsillo transversal/lateral")
                rows.append([pid, kind, f"M{m_nut.group(1)} A4 (ISO 4032: {n(NUT_AF[int(m_nut.group(1))], 0)} e/c)",
                             com or "—"])
            else:
                arg = re.search(r"cyl_[xyz]\(([^,]+),", l)
                dia = "—"
                if arg:
                    try:
                        dia = n(2 * eval(arg.group(1), {}, ns), 1)          # noqa: S307 (fuente propia)
                    except Exception:
                        pass
                rows.append([pid, "inserto térmico (agujero Ø " + dia + " mm)",
                             "ver comentario", com or "—"])
    return table(["Pieza", "Tipo", "Rosca", "Comentario en el CAD"], rows)


PERFIL_KEYS = [("layer_height", "capa [mm]"), ("first_layer_height", "1.ª capa [mm]"), ("perimeters", "perímetros"),
               ("perimeter_generator", "generador de perímetros"), ("top_solid_layers", "capas sólidas arriba"),
               ("bottom_solid_layers", "capas sólidas abajo"), ("fill_density", "relleno base"),
               ("fill_pattern", "patrón"), ("fill_angle", "ángulo de relleno [°]"), ("infill_overlap", "solape relleno–perímetro"),
               ("seam_position", "costura"), ("staggered_inner_seams", "costuras internas escalonadas"),
               ("ironing", "planchado"), ("external_perimeter_speed", "v perímetro externo [mm/s]"),
               ("perimeter_speed", "v perímetros [mm/s]"), ("infill_speed", "v relleno [mm/s]"),
               ("solid_infill_speed", "v relleno sólido [mm/s]"), ("support_material", "soportes (por defecto)"),
               ("elefant_foot_compensation", "compensación pata de elefante [mm]")]
COMUN_KEYS = [("P1_filamento_PETG.ini", k) for k in ("first_layer_temperature", "temperature", "first_layer_bed_temperature",
                                                     "bed_temperature", "min_fan_speed", "max_fan_speed", "bridge_fan_speed",
                                                     "disable_fan_first_layers", "filament_max_volumetric_speed",
                                                     "filament_retract_length", "filament_retract_speed")] + \
    [("P1_impresora_Ender3S1.ini", k) for k in ("bed_shape", "max_print_height", "nozzle_diameter", "gcode_flavor",
                                                 "machine_max_acceleration_extruding")]


def ini(path):
    d = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([a-z0-9_]+) = ?(.*)$", line)
        if m:
            d[m.group(1)] = m.group(2)
    return d


def blk_perfiles():
    P = {fam: ini(FAM.PS / fn) for fam, fn in FAM.PERFILES.items()}
    rows = [[lab] + [P[f].get(k, "—") for f in FAM.PERFILES] for k, lab in PERFIL_KEYS]
    s = table(["Parámetro (print)"] + [f"{f} (`{FAM.PERFILES[f]}`)" for f in FAM.PERFILES], rows)
    rows2 = [[f"`{fn}`", k, ini(FAM.PS / fn).get(k, "—")] for fn, k in COMUN_KEYS]
    return s + "\n\n" + table(["Archivo", "Clave", "Valor"], rows2)


def blk_totales(man, pm, rep):
    t = man.get("totals", {})
    lam = rep.get("laminado", {}).get("totales", {})
    pp, pr = lam.get("pieza", {}), lam.get("probeta", {})
    tp = pm.get("totals", {})
    g_cad = (t.get("printed_mass_g", 0) or 0) + (tp.get("mass_g", 0) or 0)
    g_ps = (pp.get("g") or 0) + (pr.get("g") or 0) if lam else None
    rows = [["Piezas P1 (19 tipos)", sum(r["qty"] for r in man["parts"] if r["process"] == "impresa"),
             n(t.get("printed_mass_g")), n(pp.get("g")), n(t.get("printed_hours")), n(pp.get("h"))],
            ["Probetas P1.1–P1.8", tp.get("n_impresiones"), n(tp.get("mass_g")), n(pr.get("g")), n(tp.get("hours")),
             n(pr.get("h"))],
            ["**Total**", "", f"**{n(g_cad)}**", f"**{n(g_ps)}**" if g_ps else "—",
             f"**{n((t.get('printed_hours') or 0) + (tp.get('hours') or 0))}**",
             f"**{n((pp.get('h') or 0) + (pr.get('h') or 0))}**" if lam else "—"]]
    spools = math.ceil(max(g_cad, g_ps or 0) * SPOOL_MARGIN / 1000)
    s = table(["Conjunto", "Impresiones", "g (CAD × solid_frac)", "g (PrusaSlicer)", "h (18 g/h, inputs.yaml)",
               "h (PrusaSlicer)"], rows)
    s += (f"\n\nBobinas de 1 kg a comprar: **{spools}** [CALCULADO: máx(g) × {SPOOL_MARGIN:.2f} de purga, fallas y "
          "reimpresiones (= bom.py)]. Laminado: " + (rep.get("prusaslicer", "[NO EJECUTADO]") if rep else "[NO EJECUTADO]")
          + ", perfiles y ajustes por objeto de esta página, sin soportes (con soportes automáticos suma "
          + (n(sum((it.get('con_soporte', {}).get('g') or 0) - (it.get('g') or 0) for it in rep.get('laminado', {}).get('items', [])
                   if it['tipo'] == 'pieza') if rep else None, 0)) + " g).")
    if lam and t.get("printed_hours"):
        s += (f" El ritmo real de las piezas es **{n(pp['g'] / pp['h'], 1)} g/h**, no los "
              f"{n(t['printed_mass_g'] / t['printed_hours'], 0)} g/h de inputs.yaml (printer.print_rate_g_h): "
              "6 perímetros y velocidades moderadas. Corregir ese valor en inputs.yaml para el plan de impresión.")
    return s


def refresh_values(txt):
    sys.path.insert(0, str(ROOT))
    from docgen import getpath, load
    srcs = {"sizing": load("sizing.json"), "bom": load("bom_resumen.json"), "manifest": load("manifest.json"),
            "est": load("estructural.json"), "verify": load("verify.json"), "arch": load("arquitectura.json")}
    pat = re.compile(r"(<!--V:([\w.]+):([^>]*?)-->)(.*?)(<!--/V-->)", re.S)

    def rv(m):
        src, _, rest = m.group(2).partition(".")
        try:
            return f"{m.group(1)}{format(getpath(srcs[src], rest), m.group(3))}{m.group(5)}"
        except Exception:
            return m.group(0)
    return pat.sub(rv, txt)


def main():
    man = jload(ROOT / "resultados" / "manifest.json")
    est = jload(ROOT / "resultados" / "estructural.json")
    pm = jload(HERE / "probetas_manifest.json")
    rep = jload(ROOT / "prusaslicer" / "slice_report.json")
    B = {"perfiles": blk_perfiles(), "orientacion": blk_orientacion(man, est, rep), "probetas": blk_probetas(pm, rep),
         "criterios": blk_criterios(pm), "ajustes": blk_ajustes(pm), "roscas": blk_roscas(),
         "totales": blk_totales(man, pm, rep)}
    txt = DOC.read_text(encoding="utf-8")
    pat = re.compile(r"(<!-- FAB:(\w+) -->)(.*?)(<!-- /FAB:\2 -->)", re.S)
    missing = []

    def rb(m):
        if m.group(2) not in B:
            missing.append(m.group(2))
            return m.group(0)
        return f"{m.group(1)}\n{B[m.group(2)]}\n{m.group(4)}"
    new = refresh_values(pat.sub(rb, txt))
    if new != txt:
        DOC.write_text(new, encoding="utf-8")
    found = set(re.findall(r"<!-- FAB:(\w+) -->", new))
    print(f"tabla_fabricacion: bloques {sorted(found)}; faltan en el doc: {sorted(set(B) - found)}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
