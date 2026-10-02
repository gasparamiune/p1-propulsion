#!/usr/bin/env python3
"""run_all.py — Pipeline completo de P1, regenerable desde inputs.yaml:

    1. sizing.py                  dimensionamiento → resultados/sizing.json, figuras
    2. 04_diseno/build_all.py     CAD → STEP/STL, manifest
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="mallas gruesas (más rápido)")
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args()
    fast = ["--fast"] if a.fast else []
    step("1/8 Dimensionamiento", ["sizing.py", "--quiet"])
    step("2/8 CAD + exportes", ["04_diseno/build_all.py"] + fast)
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
    if not a.skip_render:
        step("8/8 Vistas del ensamblaje (matplotlib)", ["blender/preview_views.py"], required=False)
    print("\nPIPELINE COMPLETO: exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
