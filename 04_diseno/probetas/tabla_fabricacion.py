#!/usr/bin/env python3
"""tabla_fabricacion.py — Regenera las tablas de 05_fabricacion.md (bloques <!-- FAB:nombre --> … <!-- /FAB:nombre -->).

Fuentes (nada a mano): resultados/manifest.json (piezas: material, proceso, cantidad, masa, envolvente,
orientación, print_rot), bom.csv (servicios S-*, materia prima MP-*, ítems comprados y su columna «cubre»),
resultados/sizing.json (bomba, mech), resultados/estructural.json (FS mín. por pieza), inputs.yaml (límite de
Ø del torno propio bom.lathe_max_d_mm, ritmo de impresión), 04_diseno/probetas/probetas_manifest.json
(probetas y ensayos de taller con sus criterios), prusaslicer/slice_report.json (laminado real) y el código
de 04_diseno/piezas/ (tuercas cautivas e insertos de las piezas impresas). Familia de perfil y ajustes por
objeto: familias.py. También refresca los valores <!--V:…--> del propio 05 (mismo formato que docgen.py).
Re-ejecutable:  python 04_diseno/probetas/tabla_fabricacion.py   (lo llama también build_probetas.py)
"""
from __future__ import annotations

import csv
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
G_BAL = 6.3                  # grado de balanceo ISO 21940-11 para impulsores de bomba [ESTIMADO: verificar con el taller]


def jload(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def inputs():
    import yaml
    with open(ROOT / "inputs.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def bom_rows():
    try:
        with open(ROOT / "bom.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


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


def plano(pid):
    fs = sorted((ROOT / "04_diseno" / "planos").glob(f"{pid}_*.svg"))
    return ", ".join(f"`{f.name}`" for f in fs) if fs else "—"


# ---------------------------------------------------------------------------
# rutas de fabricación (manifest × bom.csv)
# ---------------------------------------------------------------------------
SERV = [("S-CNC", "CNC 5 ejes (taller)"), ("S-TURN", "torno de taller"), ("S-MILL", "torno + fresado 4 ejes (taller)"),
        ("S-LASER", "corte láser/agua"), ("S-WELD", "soldadura TIG (taller)"), ("S-ANOD", "anodizado duro")]


def covers(bom):
    """id de pieza → [filas de bom que la cubren (columna cubre) o la mencionan en la especificación (MP-*)]."""
    cov = {}
    for r in bom:
        ids = set(r.get("cubre", "").split())
        if r["ID"].startswith("MP-"):
            ids |= set(re.findall(r"P1-[A-Z]{3}-\d{2}", r["especificacion_minima"]))
        for i in ids:
            cov.setdefault(i, []).append(r)
    return cov


def stock_d(mp):
    """Ø de barra (o Ø exterior de barra hueca) de una fila MP-*, o None si es chapa/bloque."""
    s = mp["especificacion_minima"]
    if not s.startswith(("Barra", "Barra hueca")):
        return None
    m = re.search(r"Ø(\d+(?:[.,]\d+)?)", s)
    return float(m.group(1).replace(",", ".")) if m else None


def stock_len(mp, pid):
    m = re.search(re.escape(pid) + r"[^—;]*?→\s*\d+\s*×\s*(\d+)\s*mm", mp["especificacion_minima"])
    if m:
        return float(m.group(1))
    m = re.search(r"Ø\d+(?:\s*/\s*Ø\d+)?\s*×\s*(\d+)\s*mm", mp["especificacion_minima"])
    return float(m.group(1)) if m else None


def ruta(r, cov, lathe):
    pid = r["id"]
    rows = cov.get(pid, [])
    sids = [x["ID"] for x in rows if x["ID"].startswith("S-")]
    mps = [x for x in rows if x["ID"].startswith("MP-")]
    if r["process"] == "impresa":
        return f"Impresa PETG — perfil **{FAM.familia(r)[0]}** (§2)", sids, mps
    if r["process"] == "referencia":
        return "Referencia (no se fabrica: casco, consola, volante)", sids, mps
    if r["process"] == "comprada":
        b = [x["ID"] for x in rows if not x["ID"].startswith(("S-", "MP-"))]
        return "Comprada" + (f" ({', '.join(b)})" if b else ""), sids, mps
    steps = []
    for pre, txt in SERV:
        if any(s.startswith(pre) for s in sids):
            steps.append(txt)
    own = not any(s.startswith(("S-CNC", "S-TURN", "S-MILL")) for s in sids)
    ds = [d for d in (stock_d(m) for m in mps) if d]
    if own and ds:
        d = max(ds)
        steps.insert(0, "torno propio" + (" ⚠ Ø barra > límite del torno" if d > lathe else ""))
    elif own and not steps:
        steps.append("mecanizado propio (taladro/fresado manual)")
    elif own and "corte láser/agua" in steps and "soldadura TIG (taller)" not in steps:
        steps.append("taladrado/plegado propio")
    return " → ".join(steps), sids, mps


def blk_procesos(man, bom, inp):
    cov = covers(bom)
    lathe = float(inp["bom"]["lathe_max_d_mm"])
    rows = []
    for r in man["parts"]:
        txt, sids, mps = ruta(r, cov, lathe)
        rows.append([r["id"], r["name"], r["material"], r["qty"], r["process"], txt,
                     ", ".join(sids) or "—", ", ".join(m["ID"] for m in mps) or "—", n(r["mass_g_each"], 0), plano(r["id"])])
    cnt = {}
    for r in man["parts"]:
        cnt[r["process"]] = cnt.get(r["process"], 0) + 1
    s = table(["ID", "Pieza", "Material", "Cant.", "Proceso (manifest)", "Ruta de fabricación", "Servicio (bom.csv)",
               "Materia prima (bom.csv)", "g c/u (CAD)", "Plano"], rows)
    s += "\n\nPiezas por proceso del manifest: " + ", ".join(f"{k} **{v}**" for k, v in sorted(cnt.items())) + \
         f" ({len(man['parts'])} tipos). «torneada» en el manifest = toda pieza mecanizada (torno, fresa, láser, soldada)."
    return s


def blk_torno(man, bom, inp):
    cov = covers(bom)
    lathe = float(inp["bom"]["lathe_max_d_mm"])
    rows = []
    for r in man["parts"]:
        if r["process"] != "torneada":
            continue
        mps = [x for x in cov.get(r["id"], []) if x["ID"].startswith("MP-")]
        sids = [x["ID"] for x in cov.get(r["id"], []) if x["ID"].startswith("S-")]
        bars = [(m, stock_d(m)) for m in mps if stock_d(m)]
        if not bars:
            continue
        m, d = max(bars, key=lambda t: t[1])
        L = stock_len(m, r["id"])
        shop = [s for s in sids if s.startswith(("S-TURN", "S-CNC", "S-MILL"))]
        quien = ("taller (" + ", ".join(shop) + ")") if shop else "**torno propio**"
        ok = "sí" if d <= lathe else "**NO**"
        bb = r.get("bbox_mm") or [0, 0, 0]
        rows.append([r["id"], r["name"], r["material"], r["qty"], f"Ø{n(max(sorted(bb)[1:]), 1)} × {n(min(bb), 1)}"
                     if abs(sorted(bb)[1] - sorted(bb)[2]) < 0.02 * max(bb) else "×".join(n(x, 0) for x in bb),
                     m["ID"], f"Ø{n(d, 0)}" + (f" × {n(L, 0)}" if L else ""), ok, quien, plano(r["id"])])
    rows.sort(key=lambda x: (x[8] != "**torno propio**", x[0]))
    s = table(["ID", "Pieza", "Material", "Cant.", "Pieza Ø × largo [mm]", "Barra (bom.csv)", "Barra Ø × largo [mm]",
               f"Ø barra ≤ {n(lathe, 0)} mm", "Quién", "Plano"], rows)
    s += (f"\n\nLímite supuesto del torno propio: **Ø {n(lathe, 0)} mm** (inputs.yaml `bom.lathe_max_d_mm`, "
          "[SUPUESTO] — **medir** volteo sobre la bancada y sobre el carro, y distancia entre puntos).")
    return s


def blk_soldadura(bom):
    rows = [[r["ID"], r["descripcion"], r["especificacion_minima"], r.get("cubre", "") or "—",
             n(float(r["precio_total_EUR"] or 0), 0), r["etiqueta"]] for r in bom if r["ID"].startswith("S-WELD")]
    rows += [[r["ID"], r["descripcion"], r["especificacion_minima"], r.get("cubre", "") or "—",
              n(float(r["precio_total_EUR"] or 0), 0), r["etiqueta"]] for r in bom if r["ID"] == "S-LASER"]
    return table(["Servicio", "Qué", "Especificación (bom.csv)", "Cubre", "EUR", "Etiqueta"], rows)


def blk_cnc(man, sz, bom):
    pu, me = sz.get("pump", {}), sz.get("mech", {})
    parts = {r["id"]: r for r in man["parts"]}
    imp, sta = parts.get("P1-PMP-03", {}), parts.get("P1-PMP-06", {})
    nmax = float(me.get("n_max_rpm", 0) or 0)
    m_imp = float(imp.get("mass_g_each", 0)) / 1000
    e_per = 9549 * G_BAL / nmax if nmax else None                 # µm = g·mm/kg  (ISO 21940-11: e·ω = G)
    U_per = e_per * m_imp if e_per else None                      # g·mm
    D, c = pu.get("D_mm"), pu.get("tip_clearance_mm")
    rows = [
        ["Impulsor P1-PMP-03", f"{imp.get('material', '—')}; {pu.get('blades')} álabes; Ø{n(D, 1)} punta, cubo "
         f"Ø{n(D * pu.get('hub_ratio', 0), 1)}; masa CAD {n(m_imp * 1000, 0)} g",
         " + ".join(f"`{x}`" for x in imp.get("files", [])[:1]) + " + " + plano("P1-PMP-03"),
         f"Ø de puntas torneado a medida del anillo: holgura radial {n(c, 2)} mm (Ø anillo {n(D + 2 * c, 2)}); "
         "agujero del eje y agujero del pasador según plano del cubo",
         f"G{G_BAL:g} a {n(nmax, 0)} rpm: e_per = {n(e_per, 1)} µm → U_per = {n(U_per, 1)} g·mm "
         "(dos planos: la mitad por plano)"],
        ["Estator P1-PMP-06", f"{sta.get('material', '—')}; {pu.get('stator_vanes')} álabes + camisa + cubo; masa CAD "
         f"{n(float(sta.get('mass_g_each', 0)), 0)} g", " + ".join(f"`{x}`" for x in sta.get("files", [])[:1]) + " + " + plano("P1-PMP-06"),
         "alojamiento del buje P1-PMP-07 (H7) y bridas según plano; anodizado duro después (S-ANOD)", "no gira: sin balanceo"],
    ]
    s = table(["Pieza", "Qué es", "Qué mandar", "Cotas críticas", "Balanceo"], rows)
    sec = pu.get("sections", {})
    if sec:
        s += "\n\n" + table(["Sección", "r [mm]", "U [m/s]", "β1 flujo [°]", "β2 flujo [°]", "Entrada al estator [°]",
                             "de Haller"],
                            [[k, n(v["r_mm"], 1), n(v["u"], 1), n(v["beta1_deg"], 1), n(v["beta2_deg"], 1),
                              n(v["stator_inlet_deg"], 1), n(v["de_haller"], 2)] for k, v in sec.items()])
        s += ("\n\nÁngulos de flujo de `resultados/sizing.json` (pump.sections, desde la tangencial); los de **pala** "
              "(con incidencia y desviación) están en `P1-PMP-03_tabla_angulos_alabes.svg`, que es lo que se manda.")
    srv = [[r["ID"], r["descripcion"], n(float(r["precio_total_EUR"] or 0), 0), r["etiqueta"]]
           for r in bom if r["ID"] in ("S-CNC-IMP", "S-CNC-STAT")]
    if srv:
        s += "\n\n" + table(["Servicio", "Qué", "EUR", "Etiqueta"], srv)
    return s


def blk_anodizado(bom, man):
    parts = {r["id"]: r for r in man["parts"]}
    rows = []
    for r in bom:
        if r["ID"] in ("S-ANOD", "B-ANODE", "B-TEFGEL", "B-ISOW"):
            cub = r.get("cubre", "")
            rows.append([r["ID"], r["descripcion"], r["especificacion_minima"],
                         ", ".join(f"{i} ({parts[i]['material']})" for i in cub.split() if i in parts) or "—",
                         n(float(r["precio_total_EUR"] or 0), 0), r["etiqueta"]])
    return table(["Ítem (bom.csv)", "Qué", "Especificación", "Piezas", "EUR", "Etiqueta"], rows)


# ---------------------------------------------------------------------------
# impresión
# ---------------------------------------------------------------------------
def blk_orientacion(man, est, rep, inp):
    sl = slice_items(rep)
    rate = inp["printer"]["print_rate_g_h"]
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
        fs_s = "—" if not fs else f"{n(fs['FS'], 2)} ({lc})"
        it = sl.get(("pieza", r["id"]))
        if it and it.get("ok"):
            sup = "sí" if it.get("con_soporte", {}).get("soporte") else "no"
            av = [a for a in it.get("avisos", []) if a != "Consider enabling supports"]
            if av:
                sup += " · " + ", ".join(av)
            h, g = n(it["h"], 1), n(it["g"], 0)
        else:
            sup, h, g = "[NO EJECUTADO]", "—", "—"
        bb = "×".join(n(x, 0) for x in (r.get("print_bbox_mm") or r["bbox_mm"]))
        rows.append([r["id"], r["name"], r["qty"], f"**{fam}** {inf} %" + (f", brim {b}" if b else ""), why,
                     f"{r['orientation']} `print_rot={tuple(r['print_rot'])}`", bb, fs_s, sup,
                     n(r["mass_g_each"], 0), g, n(r["print_hours_each"], 1), h])
    return table(["ID", "Pieza", "Cant.", "Perfil, relleno", "Por qué ese perfil (familias.py)",
                  "Orientación de impresión (manifest)", "Envolvente [mm]", "FS mín. (estructural.json)",
                  "Soporte auto / avisos PrusaSlicer", "g c/u (CAD × solid_frac)", "g c/u (PrusaSlicer)",
                  f"h c/u ({n(rate, 0)} g/h)", "h c/u (PrusaSlicer)"], rows)


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


def coma(txt):
    """Decimales con coma en el texto generado (no toca IDs como P1.6 ni G6.3)."""
    return re.sub(r"(?<![A-Za-z\d.])(\d+)\.(\d+)", r"\1,\2", txt)


def blk_procedimientos(pm):
    out = []
    for t, v in pm.get("tests", {}).items():
        c = v.get("criterios", {})
        out.append(f"- **{t} — {v.get('titulo', '')}** ({'impresa' if v.get('tipo') == 'impresa' else 'taller'}). "
                   + coma(c.get("ensayo", "—"))
                   + (f" *Instalación:* {coma(c['instalacion'])}" if c.get("instalacion") else "")
                   + (f" *Si no pasa:* {coma(c['si_no_pasa'])}" if c.get("si_no_pasa") else ""))
    return "\n".join(out)


def blk_ensayos(pm):
    rows = []
    for t, v in pm.get("tests", {}).items():
        c = v.get("criterios", {})
        ok = all(x["ok"] for x in v.get("checks", []))
        rows.append([t, "impresa (CAD)" if v.get("tipo") == "impresa" else "taller (sin CAD)", v.get("titulo", ""),
                     ", ".join(v.get("piezas", [])), coma(c.get("pasa_si", "—")),
                     f"{sum(1 for x in v.get('checks', []) if x['ok'])}/{len(v.get('checks', []))} " + ("OK" if ok else "**FALLA**")])
    return table(["Ensayo", "Tipo", "Qué se ensaya", "Piezas", "Pasa si (números de los JSON)",
                  "Cotas/coherencia verificadas en software"], rows)


def blk_ajustes(pm):
    aj = pm.get("tests", {}).get("P1.1", {}).get("criterios", {}).get("ajustes_en_piezas", [])
    rows = []
    for r in sorted(aj, key=lambda x: (x["d_nom"], x["id"])):
        c = r["holgura_cad"]
        cal = "P1.1H (horizontal)" if r["eje_impresion"] == "horizontal" else "P1.1A"
        rows.append([r["id"], f"Ø{n(r['d_nom'])}", n(r["D_cad"], 2), f"{c:+.2f}".replace(".", ","),
                     r["eje_impresion"] + (f" ({n(r['ang_vertical_deg'], 0)}° de la vertical)" if r["eje_impresion"] == "inclinado" else ""),
                     cal])
    for h in pm.get("tests", {}).get("P1.1", {}).get("criterios", {}).get("hex", []):
        rows.append([h["id"], f"tuerca M{h['M']} (e/c)", n(h["af_cad"], 2), f"+{n(h['holgura_cad'], 2)}",
                     "bolsillo abierto a la cama", "P1.1A (fila hexagonal)"])
    return table(["Pieza", "Nominal", "Ø / e/c en CAD [mm]", "Holgura CAD [mm]", "Eje en impresión", "Se calibra con"], rows)


def blk_roscas(man):
    from cadlib import INSERT_HOLE, INSERT_LEN, NUT_AF, NUT_M  # noqa: F401
    ns = {"NUT_AF": NUT_AF, "NUT_M": NUT_M, "INSERT_HOLE": INSERT_HOLE, "INSERT_LEN": INSERT_LEN}
    printed = {r["id"] for r in man["parts"] if r["process"] == "impresa"}
    rows = []
    for f in sorted((ROOT / "04_diseno" / "piezas").glob("P1-*.py")):
        pid = f.stem.split("_")[0]
        if pid not in printed:
            continue
        lines = f.read_text(encoding="utf-8").splitlines()
        last_comment = ""
        for line in lines:
            s = line.strip()
            if s.startswith("#"):
                last_comment = s.lstrip("# ").strip()
            m_nut = re.search(r"NUT_AF\[(\d+)\]", line)
            m_ins = re.search(r"INSERT_HOLE\[(\d+)\]", line)
            if not (m_nut or m_ins) or "def " in line or s.startswith("#") or "checks" in line or '("' in line:
                continue
            com = (line.split("#", 1)[1].strip() if "#" in line else last_comment)[:90]
            if m_nut:
                M = int(m_nut.group(1))
                rows.append([pid, "tuerca cautiva, bolsillo hexagonal", f"M{M} A4 (ISO 4032: {n(NUT_AF[M], 0)} e/c)", com or "—"])
            else:
                M = int(m_ins.group(1))
                rows.append([pid, f"inserto térmico M{M} (agujero Ø {n(INSERT_HOLE[M], 1)} × {n(INSERT_LEN[M] + 1, 1)} mm)",
                             f"M{M}", com or "—"])
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


def blk_perfiles(man):
    P = {fam: ini(FAM.PS / fn) for fam, fn in FAM.PERFILES.items()}
    use = {fam: [r["id"] for r in man["parts"] if r["process"] == "impresa" and FAM.familia(r)[0] == fam] for fam in P}
    rows = [["**piezas**"] + [", ".join(use[f]) or "(solo probetas)" for f in FAM.PERFILES]]
    rows += [[lab] + [P[f].get(k, "—") for f in FAM.PERFILES] for k, lab in PERFIL_KEYS]
    s = table(["Parámetro (print)"] + [f"{f} (`{FAM.PERFILES[f]}`)" for f in FAM.PERFILES], rows)
    rows2 = [[f"`{fn}`", k, ini(FAM.PS / fn).get(k, "—")] for fn, k in COMUN_KEYS]
    return s + "\n\n" + table(["Archivo", "Clave", "Valor"], rows2)


def blk_totales(man, pm, rep, inp):
    t = man.get("totals", {})
    rate = inp["printer"]["print_rate_g_h"]
    margin = float(inp["bom"]["filament"]["margin_frac"])
    lam = rep.get("laminado", {}).get("totales", {})
    pp, pr = lam.get("pieza", {}), lam.get("probeta", {})
    tp = pm.get("totals", {})
    printed = [r for r in man["parts"] if r["process"] == "impresa"]
    g_cad = (t.get("printed_mass_g", 0) or 0) + (tp.get("mass_g", 0) or 0)
    g_ps = (pp.get("g") or 0) + (pr.get("g") or 0) if lam else None
    rows = [[f"Piezas del jet ({len(printed)} tipos)", sum(r["qty"] for r in printed),
             n(t.get("printed_mass_g")), n(pp.get("g")), n(t.get("printed_hours")), n(pp.get("h"))],
            ["Probetas impresas (" + ", ".join(k for k, v in pm.get("tests", {}).items() if v.get("tipo") == "impresa") + ")",
             tp.get("n_impresiones"), n(tp.get("mass_g")), n(pr.get("g")), n(tp.get("hours")), n(pr.get("h"))],
            ["**Total**", "", f"**{n(g_cad)}**", f"**{n(g_ps)}**" if g_ps else "—",
             f"**{n((t.get('printed_hours') or 0) + (tp.get('hours') or 0))}**",
             f"**{n((pp.get('h') or 0) + (pr.get('h') or 0))}**" if lam else "—"]]
    spools = math.ceil(max(g_cad, g_ps or 0) * (1 + margin) / 1000)
    s = table(["Conjunto", "Impresiones", "g (CAD × solid_frac)", "g (PrusaSlicer)", f"h ({n(rate, 0)} g/h, inputs.yaml)",
               "h (PrusaSlicer)"], rows)
    s += (f"\n\nBobinas de 1 kg: **{spools}** [CALCULADO: máx(g) × (1 + {n(margin, 2)}) de purga, fallas y reimpresiones "
          "(inputs.yaml bom.filament.margin_frac, = bom.py)]. Laminado: " +
          (rep.get("prusaslicer", "[NO EJECUTADO]") if rep else "[NO EJECUTADO]") +
          ", perfiles y ajustes por objeto de esta página, sin soportes.")
    if lam and pp.get("h"):
        s += (f" Ritmo real de las piezas: **{n(pp['g'] / pp['h'], 1)} g/h** contra {n(rate, 0)} g/h de inputs.yaml "
              f"(printer.print_rate_g_h); la masa real de PrusaSlicer es {n(100 * (pp['g'] / max(1, pp['g_cad']) - 1), 0)} % "
              "mayor que la del manifest (CAD × solid_frac): 5–6 perímetros llenan casi todas las paredes de 3–6 mm.")
    return s


# ---------------------------------------------------------------------------
def refresh_values(txt):
    sys.path.insert(0, str(ROOT))
    from docgen import getpath, load
    srcs = {"sizing": load("sizing.json"), "bom": load("bom_resumen.json"), "manifest": load("manifest.json"),
            "est": load("estructural.json"), "verify": load("verify.json"), "arch": load("arquitectura.json"),
            "cmp": load("comparacion.json")}
    pat = re.compile(r"(<!--V:([\w.]+):([^>]*?)-->)(.*?)(<!--/V-->)", re.S)

    def rv(m):
        src, _, rest = m.group(2).partition(".")
        try:
            return f"{m.group(1)}{format(getpath(srcs[src], rest), m.group(3))}{m.group(5)}"
        except Exception:
            return m.group(0)
    return pat.sub(rv, txt)


def blocks():
    man = jload(ROOT / "resultados" / "manifest.json")
    est = jload(ROOT / "resultados" / "estructural.json")
    sz = jload(ROOT / "resultados" / "sizing.json")
    pm = jload(HERE / "probetas_manifest.json")
    rep = jload(ROOT / "prusaslicer" / "slice_report.json")
    bom = bom_rows()
    inp = inputs()
    return {"procesos": blk_procesos(man, bom, inp), "perfiles": blk_perfiles(man),
            "orientacion": blk_orientacion(man, est, rep, inp), "roscas": blk_roscas(man),
            "torno": blk_torno(man, bom, inp), "soldadura": blk_soldadura(bom), "cnc": blk_cnc(man, sz, bom),
            "anodizado": blk_anodizado(bom, man), "probetas": blk_probetas(pm, rep), "ensayos": blk_ensayos(pm),
            "procedimientos": blk_procedimientos(pm),
            "ajustes": blk_ajustes(pm), "totales": blk_totales(man, pm, rep, inp)}


def main():
    B = blocks()
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
