#!/usr/bin/env python3
"""run_all.py — Pipeline completo de P1, regenerable desde inputs.yaml:

    1. sizing.py                  dimensionamiento → resultados/sizing.json, figuras
    2. 04_diseno/build_all.py     CAD → STEP/STL, manifest
       (1b/2b: si la masa del jet del CAD no es la que usó sizing.py, se repite el dimensionamiento — y el CAD si
        cambió la selección — hasta que coincidan: sizing.py lee la masa del manifest de la corrida anterior)
    3. 04_diseno/structural.py    FS por pieza y caso de carga → resultados/estructural.json
    4. 04_diseno/planos.py        planos acotados (SVG) de piezas torneadas
    5. 04_diseno/verify_parts.py  verificación (exit ≠ 0 si falla)
    6. bom.py                     bom.csv + curvas costo–autonomía
    6c–6g. electrónica (VESC, diagrama), probetas, FEA (si hay gmsh), visor 3D
    7. docgen.py                  inserta resultados en los .md (bloques AUTO)
    8. renders                    Blender headless si hay bpy; si no, vistas matplotlib
Uso: python run_all.py [--fast] [--skip-render]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def step(name, cmd, required=True):
    t0 = time.time()
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run([sys.executable] + cmd, cwd=ROOT)
    dt = time.time() - t0
    status = "OK" if r.returncode == 0 else f"FALLÓ (exit {r.returncode})"
    print(f"--- {name}: {status} en {dt:.1f} s", flush=True)
    if r.returncode != 0 and required:
        print(f"\nPIPELINE DETENIDO en '{name}'.")
        sys.exit(r.returncode)
    return r.returncode


def _mass_state():
    """(masa del jet que usó sizing.py, masa del jet del CAD, selección del optimizador)."""
    sz = json.loads((ROOT / "resultados" / "sizing.json").read_text(encoding="utf-8"))
    mf = json.loads((ROOT / "resultados" / "manifest.json").read_text(encoding="utf-8"))
    jet = next((it.get("kg") for it in sz.get("masses", {}).get("items", []) if it.get("id") == "jet"), None)
    return jet, mf.get("totals", {}).get("jet_unit_mass_kg"), json.dumps(sz.get("selection"), sort_keys=True)


def converge_mass(fast, tol=0.05, max_iter=3):
    """Punto fijo sizing ↔ CAD: la masa del jet del CAD entra en el dimensionamiento (planeo, estabilidad)."""
    for k in range(max_iter):
        jet, cad, sel = _mass_state()
        if not isinstance(jet, (int, float)) or not isinstance(cad, (int, float)) or abs(jet - cad) <= tol:
            return
        print(f"\nMasa del jet: sizing.py usó {jet:.2f} kg y el CAD da {cad:.2f} kg → se repite el dimensionamiento", flush=True)
        step(f"1b/8 Dimensionamiento con la masa del CAD (iteración {k + 1})", ["sizing.py", "--quiet"])
        if _mass_state()[2] != sel:
            step(f"2b/8 CAD con la selección nueva (iteración {k + 1})", ["04_diseno/build_all.py"] + fast)
    jet, cad, _ = _mass_state()
    if isinstance(jet, (int, float)) and isinstance(cad, (int, float)) and abs(jet - cad) > tol:
        print(f"\nPIPELINE DETENIDO: la masa del jet no converge ({jet:.2f} contra {cad:.2f} kg)")
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="mallas gruesas (más rápido)")
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args()
    fast = ["--fast"] if a.fast else []
    step("1/8 Dimensionamiento", ["sizing.py", "--quiet"])
    step("2/8 CAD + exportes", ["04_diseno/build_all.py"] + fast)
    converge_mass(fast)
    step("3/8 Estructural (FS)", ["04_diseno/structural.py"])
    step("4/8 Planos de torneado", ["04_diseno/planos.py"])
    step("5/8 Verificación", ["04_diseno/verify_parts.py"])
    step("6/8 BOM y costos", ["bom.py"])
    step("6b/8 Matriz de arquitectura", ["arquitectura.py"])
    step("6b2/8 Comprar vs construir (JT132)", ["comparacion.py"])
    step("6c/8 Electrónica (config. VESC, tabla de verdad, diagrama)", ["04_diseno/electronica/calc_electronica.py"])
    step("6d/8 Diagrama de cableado", ["04_diseno/electronica/diagrama_cableado.py"])
    step("6e/8 Probetas (CAD)", ["04_diseno/probetas/build_probetas.py"], required=False)
    if importlib.util.find_spec("gmsh") is not None and not a.fast:
        step("6f/8 FEA de piezas críticas", ["04_diseno/fea/fea_run.py"], required=False)
    else:
        print("FEA [NO EJECUTADO en este corrido]: requiere gmsh (y no corre con --fast); resultados previos en 04_diseno/fea/")
    step("6g/8 Visor 3D web (datos)", ["04_diseno/visor/build_visor.py"])
    step("7/8 Documentos (bloques AUTO)", ["docgen.py"])
    step("7b/8 Sitio web (docs/ para GitHub Pages)", ["build_site.py"])
    if not a.skip_render:
        step("8/8 Vistas del ensamblaje (matplotlib)", ["blender/preview_views.py"], required=False)
    print("\nPIPELINE COMPLETO: exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
