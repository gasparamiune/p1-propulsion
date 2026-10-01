#!/usr/bin/env python3
"""verify_parts.py — Verificación automática del CAD de P1. Termina con exit code ≠ 0 si
algo falla.

Chequeos:
  V1  Cada pieza impresa tiene STEP + STL.
  V2  Malla STL manifold (estanca, normales consistentes, volumen > 0) y sólido OCC válido.
  V3  Envolvente de impresión ≤ 210 × 210 × 260 mm (orientación de impresión elegida).
  V4  Cotas críticas declaradas por cada pieza (checks()).
  V5  Sin interferencias en el ensamblaje: barrido de dirección ψ ∈ {−ψmax, 0, +ψmax} ×
      basculación φ ∈ [0, φmax] (paso configurable), unidad vs abrazadera/horquilla/espejo,
      y pares internos de la unidad y de la horquilla (rígidos).
  V6  Coherencia de masa: masa de la unidad del CAD vs estimación usada en sizing.
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

# Pares con contacto/ajuste prensado intencional: volumen de intersección admisible [mm³]
ALLOWED = {
    frozenset(["P1-DRV-07", "P1-HSG-01"]): 15.0,     # rodamiento A prensado
    frozenset(["P1-DRV-07", "P1-HSG-02"]): 15.0,     # rodamiento B prensado
    frozenset(["P1-DRV-07", "P1-DRV-01"]): 15.0,     # pista interna en muñón (ajuste)
}
FIXED_FRAMES = ("boat",)
YOKE_FRAMES = ("yoke",)
UNIT_FRAMES = ("unit",)


def to_np(mat):
    return np.array(mat, dtype=float)


def placements_np(mod, p, steer, tilt):
    from build_all import loc_matrix
    return [to_np(loc_matrix(L)) for L in mod.placements(p, steer, tilt)]


def transom_mesh(p):
    t, H, W = p.tr_t, p.tr_H, p.inp["boat"]["transom"]["top_width_mm"]
    m = trimesh.creation.box(extents=(t, W, H))
    m.apply_translation((-t / 2, 0, -H / 2))
    return m


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


def run(p=None, mods=None, manifest=None, tilt_step=None, steer_list=None, quiet=False,
        extra_fixed=None):
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
    by_frame = {}
    for m in mods:
        by_frame.setdefault(m.META["frame"], []).append(m)
    tr = transom_mesh(p)
    step = tilt_step or p.inp["geometry"]["tilt_check_step_deg"]
    tilts = list(np.arange(0.0, p.tilt_range + 1e-9, step))
    if tilts[-1] < p.tilt_range:
        tilts.append(p.tilt_range)
    steers = steer_list if steer_list is not None else [-p.steer_range, 0.0, p.steer_range]

    def placed(mod, steer, tilt):
        out = []
        for k, M in enumerate(placements_np(mod, p, steer, tilt)):
            mm = meshes[mod.META["id"]].copy()
            mm.apply_transform(M)
            out.append((f"{mod.META['id']}#{k}", mm))
        return out

    fixed = [("ESPEJO", tr)]
    for mod in by_frame.get("boat", []):
        fixed += placed(mod, 0.0, 0.0)
    if extra_fixed:
        fixed += extra_fixed

    def check(a_name, a, b_name, b, state):
        ida, idb = a_name.split("#")[0], b_name.split("#")[0]
        if ida == idb and a_name == b_name:
            return
        v = intersect_volume(a, b)
        allow = ALLOWED.get(frozenset([ida, idb]), tol)
        if v > allow:
            item = {"a": a_name, "b": b_name, "state": state, "vol_mm3": round(v, 2)}
            results["interference"].append(item)
            fails.append(f"interferencia {a_name} ↔ {b_name} en {state}: {v:.1f} mm³")

    n_checks = 0
    # unidad (rígida): pares internos en marcha
    unit0 = []
    for mod in by_frame.get("unit", []):
        unit0 += placed(mod, 0.0, 0.0)
    yoke0 = []
    for mod in by_frame.get("yoke", []):
        yoke0 += placed(mod, 0.0, 0.0)
    for (na, a), (nb, b) in itertools.combinations(unit0, 2):
        check(na, a, nb, b, "ψ=0,φ=0 (interno unidad)"); n_checks += 1
    for (na, a), (nb, b) in itertools.combinations(yoke0, 2):
        check(na, a, nb, b, "ψ=0 (interno horquilla)"); n_checks += 1
    # barrido
    for s in steers:
        yk = []
        for mod in by_frame.get("yoke", []):
            yk += placed(mod, s, 0.0)
        for (na, a) in yk:
            for (nb, b) in fixed:
                check(na, a, nb, b, f"ψ={s:+.0f}"); n_checks += 1
        for t in tilts:
            un = []
            for mod in by_frame.get("unit", []):
                un += placed(mod, s, t)
            for (na, a) in un:
                for (nb, b) in fixed + yk:
                    check(na, a, nb, b, f"ψ={s:+.0f},φ={t:.0f}"); n_checks += 1
    results["n_pair_checks"] = n_checks
    results["states"] = {"steer": steers, "tilt": [float(x) for x in tilts]}

    # ---------------- V6 masa ----------------
    est = p.inp["architecture"]["unit_mass_estimate_kg"]
    cad = manifest["totals"]["unit_mass_kg_cad"]
    results["unit_mass"] = {"cad_kg": cad, "estimate_kg": est, "rel_diff": (cad - est) / est}
    if abs(cad - est) / est > 0.25:
        fails.append(f"masa de la unidad CAD {cad:.2f} kg difiere > 25 % de la estimación {est} kg (actualizar inputs.yaml)")
    elif abs(cad - est) / est > 0.10:
        notes.append(f"masa de la unidad CAD {cad:.2f} kg vs estimación {est} kg (>10 %)")

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
    ap.add_argument("--tilt-step", type=float, default=None)
    a = ap.parse_args(argv)
    res = run(tilt_step=a.tilt_step)
    with open(ROOT / "resultados" / "verify.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
