#!/usr/bin/env python3
"""structural.py — Cálculo estructural a mano del waterjet P1-J: FS por pieza y por caso de carga.

Resistencias de diseño del PETG impreso (inputs.yaml → materials):
    S_corta    = σ_XY · f_agua · f_temp · f_proceso          (cargas de corta duración)
    S_sost     = S_corta · f_creep                            (cargas sostenidas horas–días)
    S_fat      = S_corta · f_fatiga                           (amplitud, 1e7–1e8 ciclos: paso de pala)
    S_lcf      = S_corta · f_fatiga_lcf                       (amplitud, ~1e5–1e6 ciclos: olas, maniobras)
    × f_Z si la tensión cruza capas (se evita por orientación; ver META de cada pieza)
FS = S / σ_aplicada. Requisito: FS ≥ 3 (impresas), ≥ 2 (metálicas).
Salidas: resultados/estructural.json, resultados/estructural_tabla.md. Exit ≠ 0 si algún
FS requerido no se cumple y no está justificado (JUSTIFIED).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import params as P  # noqa: E402

G = 9.81

# Casos aceptados con FS < objetivo, con justificación explícita (se reportan, no fallan)
JUSTIFIED: dict = {}


def allowables(inp):
    m = inp["materials"]["PETG"]
    f = inp["materials"]["design_factors"]
    S = m["sigma_t_xy_mpa"] * f["f_water"] * f["f_temp"] * f["f_process"]
    return {"short": S, "sust": S * f["f_creep"], "fat": S * f["f_fatigue"],
            "lcf": S * f.get("f_fatigue_lcf", f["f_fatigue"]), "fz": f["f_z"], "sigma_xy": m["sigma_t_xy_mpa"]}


def row(rows, part, lc, model, sigma, kind, A, target, extra=""):
    Sa = A[kind] if isinstance(kind, str) else kind
    fs = Sa / sigma if sigma > 0 else math.inf
    ok = fs >= target - 1e-9
    just = JUSTIFIED.get((part, lc))
    rows.append({"part": part, "load_case": lc, "model": model, "sigma_MPa": round(sigma, 3),
                 "allowable": kind if isinstance(kind, str) else "metal", "S_MPa": round(Sa, 2),
                 "FS": round(fs, 2) if fs != math.inf else 999, "target": target,
                 "ok": bool(ok or just), "justification": just or "", "note": extra})


def main():
    """Cada subsistema agrega sus casos en 04_diseno/structural_<grupo>.py con
    cases(p, A, row, rows, T3, T2) → dict de cargas usadas (se guardan en estructural.json)."""
    import importlib.util
    p = P.load()
    inp = p.inp
    A = allowables(inp)
    T3, T2 = inp["materials"]["fs_target_printed"], inp["materials"]["fs_target_metal"]
    rows, loads = [], {"sizing_loads": p.sz["loads"]}
    for f in sorted(HERE.glob("structural_*.py")):
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        JUSTIFIED.update(getattr(mod, "JUSTIFIED", {}))
        loads[f.stem] = mod.cases(p, A, row, rows, T3, T2) or {}
    m = p.sz["mech"]
    rows.append({"part": "P1-DRV eje 316", "load_case": "Torsión máx. del controlador + fatiga (sizing)",
                 "model": "02_calculos.md §7", "sigma_MPa": None, "allowable": "metal", "S_MPa": None,
                 "FS": round(min(m["fs_shaft_static"], m["fs_shaft_fatigue"]), 2), "target": T2,
                 "ok": min(m["fs_shaft_static"], m["fs_shaft_fatigue"]) >= T2, "justification": "",
                 "note": "mín(estático, fatiga)"})
    fails = [r for r in rows if not r["ok"]]
    out = {"allowables_MPa": A, "rows": rows, "n_fail": len(fails), "loads": loads}
    (ROOT / "resultados").mkdir(exist_ok=True)
    with open(ROOT / "resultados" / "estructural.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    L = ["| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s_ = "—" if r["sigma_MPa"] is None else f"{r['sigma_MPa']:.2f}"
        S_ = "—" if r["S_MPa"] is None else f"{r['S_MPa']:.1f}"
        ok = "✔" if r["ok"] and not r["justification"] else ("✔ (justif.)" if r["ok"] else "✘")
        L.append(f"| {r['part']} | {r['load_case']} | {r['model']} | {s_} | {r['allowable']} | {S_} | {r['FS']} | {r['target']} | {ok} |")
    with open(ROOT / "resultados" / "estructural_tabla.md", "w", encoding="utf-8") as f:
        f.write("<!-- generado por 04_diseno/structural.py -->\n" + "\n".join(L) + "\n")
    print(f"structural: {len(rows)} verificaciones, {len(fails)} con FS bajo objetivo")
    for r in fails:
        print(f"  FS BAJO: {r['part']} — {r['load_case']}: FS {r['FS']} < {r['target']}  ({r['model']})")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
