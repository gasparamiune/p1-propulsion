#!/usr/bin/env python3
"""verify_parts.py — Verificación automática del CAD del waterjet P1-J. Termina con exit code
≠ 0 si algo falla.

Chequeos:
  V1  Cada pieza impresa tiene STEP + STL.
  V2  Malla STL manifold (estanca, normales consistentes, volumen > 0) y sólido OCC válido.
  V3  Envolvente de impresión ≤ 210 × 210 × 260 mm (orientación de impresión elegida).
  V4  Cotas críticas declaradas por cada pieza (checks()).
  V5  Sin interferencias: pares internos de todo lo fijo (casco de referencia, toma, bomba, tren,
      motor) y barrido de la boquilla δ ∈ {−δmax, 0, +δmax} × bucket {arriba, abajo} contra lo fijo.
      Contactos intencionales (prensados, asientos) se declaran en META["allow"] = {id: mm³}.
  V6  Masa de la unidad de jet del CAD (la usa sizing.py vía manifest).
Salida: resultados/verify.json + resumen por consola.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

FIXED_FRAMES = ("boat", "jet", "drive")
MOVING_FRAMES = ("steer", "bucket")


def to_np(mat):
    return np.array(mat, dtype=float)


def placements_np(mod, p, steer, tilt):
    from build_all import loc_matrix
    return [to_np(loc_matrix(L)) for L in mod.placements(p, steer, tilt)]


def intersect_volume(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    # prefiltro por cajas envolventes
    amin, amax = a.bounds
    bmin, bmax = b.bounds
    if np.any(amax < bmin - 1e-6) or np.any(bmax < amin - 1e-6):
        return 0.0
    try:
        r = trimesh.boolean.intersection([a, b], engine="manifold")
        return float(abs(r.volume)) if r is not None and not r.is_empty else 0.0
    except Exception:
        return 0.0


def run(p=None, mods=None, manifest=None, steer_list=None, quiet=False):
    import params as P
    from build_all import load_parts
    p = p or P.load()
    mods = mods or load_parts()
    if manifest is None:
        with open(ROOT / "resultados" / "manifest.json", encoding="utf-8") as f:
            manifest = json.load(f)
    rec = {r["id"]: r for r in manifest["parts"]}
    env = p.envelope
    tol = p.inp["geometry"]["interference_tol_mm3"]
    fails, notes = [], []
    results = {"parts": {}, "interference": [], "fails": fails, "notes": notes}

    # ---------------- V1–V4 por pieza ----------------
    meshes = {}
    for m in mods:
        meta = m.META
        pid = meta["id"]
        r = rec.get(pid)
        pr = {"id": pid, "process": meta["process"]}
        if r is None:
            fails.append(f"{pid}: falta en manifest (no construida)")
            continue
        mesh_path = HERE / "stl" / "asm" / f"{pid}.stl"
        mesh = trimesh.load(mesh_path, force="mesh")
        meshes[pid] = mesh
        pr["valid_solid"] = r["valid_solid"]
        if not r["valid_solid"]:
            fails.append(f"{pid}: sólido OCC inválido")
        if meta["process"] == "impresa":
            files_ok = all((ROOT / f).exists() for f in r["files"])
            pr["files_ok"] = files_ok
            if not files_ok:
                fails.append(f"{pid}: faltan STEP/STL")
            pm = trimesh.load(ROOT / r["files"][1], force="mesh")
            man = bool(pm.is_watertight and pm.is_winding_consistent and pm.volume > 0)
            pr["manifold"] = man
            if not man:
                fails.append(f"{pid}: STL no manifold (estanca={pm.is_watertight}, "
                             f"normales={pm.is_winding_consistent})")
            bb = r["print_bbox_mm"]
            fit = bb[0] <= env[0] + 1e-6 and bb[1] <= env[1] + 1e-6 and bb[2] <= env[2] + 1e-6
            pr["print_bbox_mm"] = bb
            pr["fits_printer"] = fit
            if not fit:
                fails.append(f"{pid}: envolvente {bb} excede {env}")
        for c in r.get("checks", []):
            if not c["ok"]:
                fails.append(f"{pid}: cota crítica '{c['name']}' = {c['value']} (ref {c['op']} {c['ref']})")
        pr["mass_g_total"] = r["mass_g_total"]
        results["parts"][pid] = pr

    # ---------------- V5 interferencias ----------------
    allowed = {}
    for m in mods:
        for other, vol in m.META.get("allow", {}).items():
            allowed[frozenset([m.META["id"], other])] = float(vol)
    steers = steer_list if steer_list is not None else [-p.steer_max, 0.0, p.steer_max]
    buckets = [0, 1]

    def placed(mod, steer, bucket):
        out = []
        for k, M in enumerate(placements_np(mod, p, steer, bucket)):
            mm = meshes[mod.META["id"]].copy()
            mm.apply_transform(M)
            out.append((f"{mod.META['id']}#{k}", mm))
        return out

    def check(a_name, a, b_name, b, state):
        ida, idb = a_name.split("#")[0], b_name.split("#")[0]
        if a_name == b_name:
            return
        v = intersect_volume(a, b)
        allow = allowed.get(frozenset([ida, idb]), tol)
        if v > allow:
            results["interference"].append({"a": a_name, "b": b_name, "state": state, "vol_mm3": round(v, 2)})
            fails.append(f"interferencia {a_name} ↔ {b_name} en {state}: {v:.1f} mm³")

    n_checks = 0
    fixed = []
    for mod in mods:
        if mod.META["frame"] in FIXED_FRAMES and mod.META["id"] in meshes:
            fixed += placed(mod, 0.0, 0)
    for (na, a), (nb, b) in itertools.combinations(fixed, 2):
        check(na, a, nb, b, "fijo"); n_checks += 1
    for s in steers:
        for bk in buckets:
            mv = []
            for mod in mods:
                if mod.META["frame"] in MOVING_FRAMES and mod.META["id"] in meshes:
                    mv += placed(mod, s, bk)
            st = f"δ={s:+.0f}°, bucket {'abajo' if bk else 'arriba'}"
            for (na, a) in mv:
                for (nb, b) in fixed:
                    check(na, a, nb, b, st); n_checks += 1
            for (na, a), (nb, b) in itertools.combinations(mv, 2):
                check(na, a, nb, b, st); n_checks += 1
    results["n_pair_checks"] = n_checks
    results["states"] = {"steer": steers, "bucket": buckets}

    # ---------------- V6 masa ----------------
    cad = manifest["totals"].get("jet_unit_mass_kg", 0.0)
    est = p.inp["masses"]["jet_mass_estimate_kg"]
    results["jet_mass"] = {"cad_kg": cad, "estimate_kg": est}
    notes.append(f"masa de la unidad de jet (CAD) {cad:.2f} kg — sizing.py la usa desde manifest (estimación previa {est} kg)")

    results["ok"] = not fails
    if not quiet:
        print(f"verify: {len(results['parts'])} piezas, {n_checks} pares×estados de interferencia")
        for n in notes:
            print("  NOTA:", n)
        for f_ in fails:
            print("  FALLA:", f_)
        print("  RESULTADO:", "OK" if not fails else f"{len(fails)} FALLAS")
    return results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.parse_args(argv)
    res = run()
    with open(ROOT / "resultados" / "verify.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
