#!/usr/bin/env python3
"""build_all.py — Construye todas las piezas P1-<SUB>-<NN>_<nombre> del waterjet desde params.py y exporta:

    04_diseno/step/<ID>_<nombre>.step   (impresas: orientación de impresión; resto: marco natural)
    04_diseno/stl/<ID>_<nombre>.stl     (solo impresas, orientación de impresión, mm)
    04_diseno/stl/asm/<ID>.stl          (todas, marco natural; las usa verify_parts.py y Blender)
    04_diseno/step/P1-ASM_marcha.step   (ensamblaje: boquilla recta, bucket arriba)
    resultados/manifest.json            (envolventes, masas, horas, metadatos, cotas críticas)
Uso:  python 04_diseno/build_all.py [--only ID] [--fast]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

from build123d import Compound, export_step, export_stl  # noqa: E402

import params as P  # noqa: E402
from cadlib import to_print  # noqa: E402

DENSITY = {"PETG": 1.27, "ASA": 1.07, "POM-C": 1.41, "AISI 316": 8.0, "AISI 440C": 7.7, "Acero": 7.85,
           "Al 6061-T6": 2.70, "Al": 2.70, "Al 5052/6082": 2.68, "Al 5083": 2.66, "CuAl10Ni": 7.6,
           "Bronce": 8.8, "NBR": 1.3, "referencia": 0.0}   # g/cm³ [ESTIMADO: valores típicos]
# META["mass_from"] = "motor" → masa del catálogo (inputs) en lugar de volumen × densidad
# META["group"]: "jet" | "drive" | "motor" | "ele" | "ref" (masa de la unidad = jet + drive)


def load_parts():
    mods = []
    for f in sorted((HERE / "piezas").glob("P1-*.py")):      # los auxiliares empiezan con "_"
        spec = importlib.util.spec_from_file_location(f.stem.replace("-", "_"), f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.__file_stem__ = f.stem
        mods.append(m)
    return mods


def loc_matrix(loc):
    """Location build123d → matriz 4×4 (lista de listas)."""
    t = loc.wrapped.Transformation()
    return [[t.Value(r, c) for c in range(1, 5)] for r in range(1, 4)] + [[0, 0, 0, 1]]


def eval_check(chk):
    name, val, ref, op = chk
    if op == ">=":
        ok = val >= ref - 1e-9
    elif op == "<=":
        ok = val <= ref + 1e-9
    else:
        ok = abs(val - ref) <= max(0.05, 0.005 * abs(ref))
    return {"name": name, "value": round(float(val), 3), "ref": round(float(ref), 3), "op": op, "ok": bool(ok)}


def min_xy_footprint(part):
    """Envolvente de impresión: rota alrededor de Z (0–90°, paso 5°) y devuelve la mínima
    (x, y, z) — la pieza puede girarse sobre la cama."""
    from build123d import Rot
    best = None
    for a in range(0, 91, 5):
        bb = (Rot(0, 0, a) * part).bounding_box()
        dims = (bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z)
        key = max(dims[0], dims[1])
        if best is None or key < best[0]:
            best = (key, a, dims)
    return best[1], best[2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--fast", action="store_true", help="tolerancia de malla gruesa")
    a = ap.parse_args(argv)
    p = P.load()
    inp = p.inp
    (HERE / "step").mkdir(exist_ok=True)
    (HERE / "stl" / "asm").mkdir(parents=True, exist_ok=True)
    tol, atol = (0.2, 0.3) if a.fast else (0.05, 0.15)

    sel = p.sz["selection"]
    manifest = {"parts": [], "inputs_version": inp["meta"]["version"],
                "selection": sel, "params": {k: v for k, v in p.raw.items()
                                             if k not in ("inp", "sz", "layout") and not callable(v)}}
    asm_shapes = []
    t_all = time.time()
    rate = inp["printer"]["print_rate_g_h"]
    for m in load_parts():
        meta = dict(m.META)
        if a.only and meta["id"] != a.only:
            continue
        t0 = time.time()
        part = m.build(p)
        valid = bool(part.is_valid)
        vol = float(part.volume)
        stem = f"{meta['id']}_{meta['name']}"
        rec = {**meta, "file_stem": stem, "valid_solid": valid, "volume_mm3": vol,
               "frame": meta["frame"]}
        # masa
        if meta.get("mass_from") == "motor":
            mass_g = inp["motor"]["options"][sel["motor"]]["mass_kg"] * 1000
        elif "mass_g" in meta:
            mass_g = float(meta["mass_g"])
        else:
            rho = DENSITY.get(meta["material"], 1.27)
            mass_g = vol / 1000 * rho * meta.get("solid_frac", 1.0)
        rec["mass_g_each"] = mass_g
        rec["mass_g_total"] = mass_g * meta["qty"]
        # exportes
        export_stl(part, str(HERE / "stl" / "asm" / f"{meta['id']}.stl"), tolerance=tol, angular_tolerance=atol)
        if meta["process"] == "referencia":
            rec["files"] = []
            bb = part.bounding_box()
            rec["bbox_mm"] = [round(bb.max.X - bb.min.X, 2), round(bb.max.Y - bb.min.Y, 2), round(bb.max.Z - bb.min.Z, 2)]
        elif meta["process"] == "impresa":
            pp = to_print(part, meta["print_rot"])
            ang, dims = min_xy_footprint(pp)
            from build123d import Rot
            pp = to_print(Rot(0, 0, ang) * pp, (0, 0, 0))
            export_step(pp, str(HERE / "step" / f"{stem}.step"))
            export_stl(pp, str(HERE / "stl" / f"{stem}.stl"), tolerance=tol, angular_tolerance=atol)
            rec["print_bbox_mm"] = [round(x, 2) for x in dims]
            rec["print_zrot_deg"] = ang
            rec["print_hours_each"] = mass_g / rate
            rec["files"] = [f"04_diseno/step/{stem}.step", f"04_diseno/stl/{stem}.stl"]
        else:
            stale = HERE / "stl" / f"{stem}.stl"        # una pieza que dejó de imprimirse no deja STL viejo
            if stale.exists():
                stale.unlink()
            export_step(part, str(HERE / "step" / f"{stem}.step"))
            bb = part.bounding_box()
            rec["bbox_mm"] = [round(bb.max.X - bb.min.X, 2), round(bb.max.Y - bb.min.Y, 2), round(bb.max.Z - bb.min.Z, 2)]
            rec["files"] = [f"04_diseno/step/{stem}.step"]
        # cotas críticas
        try:
            rec["checks"] = [eval_check(c) for c in m.checks(p, part)]
        except Exception as e:  # pragma: no cover
            rec["checks"] = [{"name": f"error en checks: {e}", "value": 0, "ref": 0, "op": "=", "ok": False}]
        # ubicaciones de ensamblaje en marcha (boquilla recta, bucket arriba)
        rec["placements_running"] = [loc_matrix(L) for L in m.placements(p, 0.0, 0.0)]
        for L in m.placements(p, 0.0, 0.0):
            asm_shapes.append(part.moved(L))
        rec["build_s"] = round(time.time() - t0, 2)
        manifest["parts"].append(rec)
        print(f"  {stem:40s} {meta['process']:9s} vol={vol/1000:8.1f} cm³ "
              f"m={rec['mass_g_total']:7.0f} g  valid={valid}  ({rec['build_s']} s)")

    if not a.only:
        asm = Compound(children=asm_shapes)
        export_step(asm, str(HERE / "step" / "P1-ASM_marcha.step"))
        # el STEP de ensamblaje pesa > 50 MB: se versiona comprimido (gzip) y el .step queda local
        import gzip
        import shutil
        with open(HERE / "step" / "P1-ASM_marcha.step", "rb") as fi, gzip.open(HERE / "step" / "P1-ASM_marcha.step.gz", "wb", 9) as fo:
            shutil.copyfileobj(fi, fo)
    printed = [r for r in manifest["parts"] if r["process"] == "impresa"]
    manifest["totals"] = {
        "printed_mass_g": sum(r["mass_g_total"] for r in printed),
        "printed_hours": sum(r["print_hours_each"] * r["qty"] for r in printed),
        "jet_unit_mass_kg": sum(r["mass_g_total"] for r in manifest["parts"]
                                if r.get("group") in ("jet", "drive")) / 1000,
        "n_parts": len(manifest["parts"]),
    }
    out = ROOT / "resultados" / ("manifest.json" if not a.only else "manifest_partial.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Total impreso: {manifest['totals']['printed_mass_g']:.0f} g, "
          f"{manifest['totals']['printed_hours']:.1f} h; masa de la unidad de jet (CAD) "
          f"{manifest['totals']['jet_unit_mass_kg']:.2f} kg; {time.time()-t_all:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
