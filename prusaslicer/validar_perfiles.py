#!/usr/bin/env python3
"""validar_perfiles.py — Valida los perfiles PrusaSlicer de P1 y, si hay PrusaSlicer CLI, lamina.

1. Formato: cada línea no comentada es «clave = valor», sin claves duplicadas.
2. Límites: boquilla ≤ printer.hotend_max_c, cama ≤ printer.bed_max_c, boquilla = printer.nozzle_mm,
   forma de cama = zona útil printer.envelope_mm (X, Y) y alto máx. = envelope Z (inputs.yaml);
   estructural: perímetros ≥ 6; sellado: capa 0,12–0,15 y (100 % de relleno o ≥ 4 perímetros);
   cubiertas: perímetros ≥ 4 (paredes de 3,2 mm macizas); relleno base = familias.INFILL_BASE.
3. Con `prusa-slicer` en el PATH:
   - claves conocidas por esa versión (config por defecto ∪ --help-fff);
   - genera completo/P1_<familia>_completo.ini (impresora + filamento + impresión, guardado por el propio
     PrusaSlicer: prueba de que los carga) para importar en la GUI;
   - lamina cada probeta IMPRESA (04_diseno/probetas/probetas_manifest.json; los ensayos de taller no tienen
     STL) y cada pieza impresa del jet (resultados/manifest.json, process = "impresa") con su familia y ajustes
     por objeto (familias.py), sin y con soportes automáticos; lee tiempo y gramos del G-code y verifica que el
     G-code repite los valores de los .ini.
   Resultado: prusaslicer/slice_report.json.  Sin PrusaSlicer: solo 1–2 y el informe dice [NO EJECUTADO].
Uso: python prusaslicer/validar_perfiles.py [--sin-laminar] [--solo-probetas] [--sin-completo] [--informe RUTA]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "04_diseno" / "probetas"))
import familias as FAM  # noqa: E402

LINE = re.compile(r"^([a-z0-9_]+) = ?(.*)$")
ISSUES = ["Floating object part", "Floating bridge anchors", "Loose extrusions", "Long bridging extrusions",
          "Collapsing overhang", "Low bed adhesion", "Consider enabling supports"]   # avisos de estabilidad 2.7
CRITICAS = ["temperature", "first_layer_temperature", "bed_temperature", "first_layer_bed_temperature",
            "perimeters", "fill_density", "fill_pattern", "layer_height", "nozzle_diameter", "bed_shape",
            "max_print_height", "seam_position", "top_solid_layers", "bottom_solid_layers", "perimeter_generator",
            "fill_angle", "ironing", "max_fan_speed", "filament_type"]


def parse_ini(path):
    keys, errs = {}, []
    for i, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        s = raw.rstrip()
        if not s.strip() or s.lstrip().startswith(("#", ";")):
            continue
        m = LINE.match(s)
        if not m:
            errs.append(f"{Path(path).name}:{i}: línea mal formada: {s[:60]}")
            continue
        k, v = m.group(1), m.group(2)
        if k in keys:
            errs.append(f"{Path(path).name}:{i}: clave duplicada {k}")
        keys[k] = v
    return keys, errs


def pct(v):
    return float(str(v).rstrip("%"))


def inputs():
    import yaml
    with open(ROOT / "inputs.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_limits(cfg, inp):
    pr = inp["printer"]
    errs = []
    printer, fil = cfg["impresora"], cfg["filamento"]
    for k in ("temperature", "first_layer_temperature"):
        if float(fil[k]) > pr["hotend_max_c"]:
            errs.append(f"filamento {k} = {fil[k]} > {pr['hotend_max_c']} °C")
    for k in ("bed_temperature", "first_layer_bed_temperature"):
        if float(fil[k]) > pr["bed_max_c"]:
            errs.append(f"filamento {k} = {fil[k]} > {pr['bed_max_c']} °C")
    if abs(float(printer["nozzle_diameter"]) - pr["nozzle_mm"]) > 1e-9:
        errs.append("nozzle_diameter ≠ printer.nozzle_mm")
    pts = [tuple(float(c) for c in p.split("x")) for p in printer["bed_shape"].split(",")]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ex, ey, ez = pr["envelope_mm"]
    if abs((max(xs) - min(xs)) - ex) > 1e-6 or abs((max(ys) - min(ys)) - ey) > 1e-6 or max(xs) > 220 or max(ys) > 220:
        errs.append(f"bed_shape {printer['bed_shape']} ≠ zona útil {ex}×{ey} dentro de 220×220")
    if float(printer["max_print_height"]) != float(ez):
        errs.append("max_print_height ≠ envelope Z")
    est = cfg["estructural"]
    if int(est["perimeters"]) < 6:
        errs.append("estructural: perimeters < 6")
    if int(est["top_solid_layers"]) < 1 or int(est["bottom_solid_layers"]) < 1:
        errs.append("estructural: sin capas sólidas")
    if est["fill_pattern"] != "gyroid" or pct(est["fill_density"]) < 60:
        errs.append("estructural: relleno gyroid alto (≥ 60 %) requerido")
    sel = cfg["sellado"]
    if not (0.12 <= float(sel["layer_height"]) <= 0.15):
        errs.append("sellado: layer_height fuera de 0,12–0,15")
    if not (pct(sel["fill_density"]) >= 100 or int(sel["perimeters"]) >= 4):
        errs.append("sellado: ni 100 % de relleno ni ≥ 4 perímetros")
    if int(cfg["cubiertas"]["perimeters"]) < 4:
        errs.append("cubiertas: perimeters < 4")
    for fam in FAM.PERFILES:
        if pct(cfg[fam]["fill_density"]) != FAM.INFILL_BASE[fam]:
            errs.append(f"{fam}: fill_density ≠ familias.INFILL_BASE")
    return errs


# ---------------------------------------------------------------------------
def known_keys(ps):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "def.ini"
        subprocess.run([ps, "--save", str(d)], capture_output=True, text=True, timeout=120)
        keys = {LINE.match(l).group(1) for l in d.read_text().splitlines() if LINE.match(l)}
    h = subprocess.run([ps, "--help-fff"], capture_output=True, text=True, timeout=120).stdout
    keys |= {m.group(1).replace("-", "_") for m in re.finditer(r"^\s+--([a-z0-9-]+)", h, re.M)}
    return keys


def version(ps):
    r = subprocess.run([ps, "--help"], capture_output=True, text=True, timeout=60)
    return (r.stdout.splitlines() or ["?"])[0].strip()


def gcode_info(path):
    txt = Path(path).read_text(errors="ignore")
    tail = txt[-200000:]
    g = re.search(r"; total filament used \[g\] = ([\d.]+)", tail)
    t = re.search(r"; estimated printing time \(normal mode\) = (.+)", tail)
    secs = 0
    if t:
        for val, unit in re.findall(r"(\d+)([dhms])", t.group(1)):
            secs += int(val) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unit]
    cfg = dict(re.findall(r"^; ([a-z0-9_]+) = (.*)$", tail, re.M))
    return {"g": float(g.group(1)) if g else None, "h": round(secs / 3600, 2),
            "soporte": ";TYPE:Support material" in txt}, cfg


def slice_one(ps, stl, fam, over, support, td):
    out = Path(td) / (Path(stl).stem + f"_{fam}_{'S' if support else 'N'}.gcode")
    cmd = [ps, "--load", str(HERE / FAM.IMPRESORA), "--load", str(HERE / FAM.FILAMENTO),
           "--load", str(HERE / FAM.PERFILES[fam])]
    for k, v in over.items():
        cmd += [f"--{k.replace('_', '-')}", str(v)]
    if support:
        cmd += ["--support-material", "--support-material-auto"]
    cmd += ["--export-gcode", str(stl), "-o", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0 or not out.exists():
        return {"ok": False, "error": (r.stdout + r.stderr)[-600:]}, {}
    info, cfg = gcode_info(out)
    issues = set()
    for l in (r.stdout + r.stderr).splitlines():
        for name in ISSUES:
            if name.lower() in l.lower():
                issues.add(name)
    info.update({"ok": True, "avisos": sorted(issues)})
    out.unlink()
    return info, cfg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-laminar", action="store_true")
    ap.add_argument("--solo-probetas", action="store_true")
    ap.add_argument("--sin-completo", action="store_true", help="no regenerar completo/*.ini")
    ap.add_argument("--informe", default=str(HERE / "slice_report.json"), help="ruta del informe JSON")
    a = ap.parse_args(argv)
    inp = inputs()
    files = {"impresora": FAM.IMPRESORA, "filamento": FAM.FILAMENTO, **FAM.PERFILES}
    cfg, errs = {}, []
    for name, fn in files.items():
        k, e = parse_ini(HERE / fn)
        cfg[name] = k
        errs += e
    errs += check_limits(cfg, inp)
    rep = {"formato_y_limites_ok": not errs, "errores": errs, "perfiles": files}
    ps = shutil.which("prusa-slicer") or shutil.which("PrusaSlicer") or shutil.which("prusa-slicer-console")
    if not ps:
        rep["prusaslicer"] = "[NO EJECUTADO: prusa-slicer no está en el PATH]"
    else:
        rep["prusaslicer"] = version(ps)
        kk = known_keys(ps)
        unk = {n: [k for k in c if k not in kk] for n, c in cfg.items()}
        rep["claves_desconocidas"] = {n: u for n, u in unk.items() if u}
        errs += [f"{n}: clave desconocida para {rep['prusaslicer']}: {k}" for n, u in unk.items() for k in u]
        (HERE / "completo").mkdir(exist_ok=True)
        for fam, fn in ({} if a.sin_completo else FAM.PERFILES).items():
            dst = HERE / "completo" / f"P1_{fam}_completo.ini"
            r = subprocess.run([ps, "--load", str(HERE / FAM.IMPRESORA), "--load", str(HERE / FAM.FILAMENTO),
                                "--load", str(HERE / fn), "--save", str(dst)], capture_output=True, text=True)
            if r.returncode != 0 or not dst.exists():
                errs.append(f"PrusaSlicer no pudo cargar/guardar la familia {fam}: {r.stdout[-300:]}")
        if not a.sin_laminar:
            rep["laminado"] = laminar(ps, cfg, a.solo_probetas, errs)
    rep["errores"] = errs
    rep["ok"] = not errs
    with open(a.informe, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    for e in errs:
        print("ERROR:", e)
    print(f"validar_perfiles: {'OK' if not errs else 'FALLAS'} ({rep['prusaslicer']})")
    return 0 if not errs else 1


def laminar(ps, cfg, solo_probetas, errs):
    jobs = []
    pm = json.loads((ROOT / "04_diseno" / "probetas" / "probetas_manifest.json").read_text(encoding="utf-8"))
    for r in pm["probetas"]:
        fam = r["profile"]
        jobs.append(("probeta", r["id"], r["files"][1], fam, FAM.overrides(r, fam), r["qty"], r["mass_g_each"]))
    if not solo_probetas:
        man = json.loads((ROOT / "resultados" / "manifest.json").read_text(encoding="utf-8"))
        for r in man["parts"]:
            if r["process"] != "impresa":
                continue
            fam, _why = FAM.familia(r)
            jobs.append(("pieza", r["id"], r["files"][1], fam, FAM.overrides(r, fam), r["qty"], r["mass_g_each"]))
    res = []
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        for kind, pid, stl, fam, over, qty, m_cad in jobs:
            info, gcfg = slice_one(ps, ROOT / stl, fam, over, False, td)
            rec = {"tipo": kind, "id": pid, "familia": fam, "ajustes_objeto": over, "qty": qty,
                   "g_cad": m_cad, **info}
            if info.get("ok"):
                # el G-code repite los valores críticos de los .ini (o del ajuste por objeto)
                want = {**cfg["impresora"], **cfg["filamento"], **cfg[fam], **over}
                bad = [k for k in CRITICAS if k in want and k in gcfg and gcfg[k].strip() != want[k].strip()]
                rec["config_ok"] = not bad
                if bad:
                    errs.append(f"{pid}: el G-code no repite {bad}")
                if kind == "pieza":
                    s_info, _ = slice_one(ps, ROOT / stl, fam, over, True, td)
                    rec["con_soporte"] = {k: s_info.get(k) for k in ("ok", "g", "h", "soporte")}
            else:
                errs.append(f"{pid}: no se pudo laminar con {fam}: {info.get('error', '')[-200:]}")
            res.append(rec)
            print(f"  {kind:7s} {pid:12s} {fam:11s} {str(over):40s} "
                  f"{info.get('g')} g {info.get('h')} h  soporte(auto)="
                  f"{rec.get('con_soporte', {}).get('soporte')}")
    tot = {}
    for kind in ("probeta", "pieza"):
        rr = [r for r in res if r["tipo"] == kind and r.get("ok")]
        tot[kind] = {"g": round(sum(r["g"] * r["qty"] for r in rr), 0),
                     "h": round(sum(r["h"] * r["qty"] for r in rr), 1),
                     "g_cad": round(sum(r["g_cad"] * r["qty"] for r in rr), 0)}
    return {"items": res, "totales": tot, "segundos": round(time.time() - t0, 0)}


if __name__ == "__main__":
    sys.exit(main())
