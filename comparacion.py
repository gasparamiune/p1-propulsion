#!/usr/bin/env python3
"""comparacion.py — Comprar vs construir el waterjet (README, 03 §4).

A  = este diseño (bomba propia)                      → sizing.json + bom_resumen.json
B  = AWT JT132 comprada (Ø130 / tobera Ø70, 12 kg) + el tren eléctrico de este diseño
     Prestaciones: el mismo modelo de sizing.py con D = 130 y D_tobera = 70 [VERIFICADO: R11 §4],
     impulsor diseñado por el fabricante (se usa el mismo η de diseño) y la masa de la unidad
     reemplazada (grupo "jet" del CAD → 12 kg).
     Costo: total de A − costo de las piezas del grupo "jet" de la BOM + JT132 puesta en DK.
Lampuga Air: jet boat eléctrico comercial de 2,30 m (referencia de prestaciones, R12).
Escribe resultados/comparacion.json (marcadores <!--V:cmp.…-->).
"""
from __future__ import annotations

import copy
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import sizing  # noqa: E402
from p1calc.io import RESULTS_DIR, load_inputs  # noqa: E402


def jet_group_cost(man, bom_csv):
    """Costo en la BOM de las piezas del grupo 'jet' (toma, bomba, dirección, reversa) — las que
    reemplaza la JT132. Usa la columna 'piezas' de bom.csv si existe, si no la categoría."""
    ids = {p["id"] for p in man["parts"] if p.get("group") == "jet"}
    tot = 0.0
    if not bom_csv.exists():
        return None, sorted(ids)
    with open(bom_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            refs = (r.get("piezas") or r.get("parts") or "")
            cat = (r.get("categoria") or r.get("cat") or "").lower()
            if any(i in refs for i in ids) or cat.startswith(("waterjet", "bomba", "toma", "dirección", "reversa")):
                try:
                    tot += float(r.get("total_eur") or r.get("subtotal_eur") or 0)
                except ValueError:
                    pass
    return tot, sorted(ids)


def run(inp: dict) -> dict:
    c = inp["comparison"]
    sz = json.loads((RESULTS_DIR / "sizing.json").read_text(encoding="utf-8"))
    man = json.loads((RESULTS_DIR / "manifest.json").read_text(encoding="utf-8"))
    bomp = RESULTS_DIR / "bom_resumen.json"
    bom = json.loads(bomp.read_text(encoding="utf-8")) if bomp.exists() else {}
    sel = sz["selection"]
    usd, dkk = inp["meta"]["usd_to_eur"], inp["meta"]["eur_to_dkk"]

    # --- B: prestaciones con la geometría de la JT132 y su masa ---
    m_jet_cad = sum(p["mass_g_total"] for p in man["parts"] if p.get("group") == "jet") / 1000
    m_drive_cad = sum(p["mass_g_total"] for p in man["parts"] if p.get("group") == "drive") / 1000
    ii = copy.deepcopy(inp)
    ii["masses"]["jet_mass_estimate_kg"] = c["jt132_mass_kg"] + m_drive_cad
    sizing.jet_mass = lambda _inp: _inp["masses"]["jet_mass_estimate_kg"]      # no leer el manifest
    rB = sizing.evaluate(ii, sel["motor"], sel["esc"], sel["battery"], 130, 70 / 130, sel["f_pow"])
    # --- costos ---
    jet_cost, jet_ids = jet_group_cost(man, ROOT / "bom.csv")
    jt_lo, jt_hi = [x * usd * (1 + c["import_duty_frac"]) * (1 + inp["costs"]["import_vat_frac"]) + c["jt132_freight_eur"]
                    for x in c["jt132_usd"]]
    A_tot = bom.get("total_eur")
    out = {
        "A_total_eur": A_tot, "A_vmax_kmh": sz["performance"]["vmax_cont_kmh"],
        "A_hump_margin": sz["performance"]["hump_margin_min"], "A_jet_mass_kg": m_jet_cad,
        "A_jet_cost_eur": jet_cost, "jet_part_ids": jet_ids,
        "B_jt132_landed_eur_min": jt_lo, "B_jt132_landed_eur_max": jt_hi,
        "B_total_eur_min": (A_tot - jet_cost * (1 + inp["costs"]["contingency_frac"]) + jt_lo) if (A_tot and jet_cost) else None,
        "B_total_eur_max": (A_tot - jet_cost * (1 + inp["costs"]["contingency_frac"]) + jt_hi) if (A_tot and jet_cost) else None,
        "B_jet_mass_kg": c["jt132_mass_kg"], "B_vmax_kmh": rB["vmax_cont_kmh"], "B_hump_margin": rB["hump_margin"],
        "B_planes": rB["planes"], "B_mass_total_kg": rB["mass_kg"], "B_S_top": rB["S_top"],
        "B_P_bat_legal_W": rB["P_bat_legal_W"], "B_hard_ok": rB["hard_ok"],
        "B_fails": [k[3:] for k in rB if k.startswith("ok_") and not rB[k]],
        "maytech_mtwj12kw_eur": c["maytech_mtwj12kw_usd"] * usd,
        "spark_parts_eur": c["spark_impeller_eur"] + c["spark_wearring_eur"],
        "lampuga": c["lampuga_air"],
        "_etiquetas": {"B": "[CALCULADO: modelo de sizing.py con la geometría VERIFICADA de la JT132 (R11 §4); "
                            "η y curva del impulsor de AWT ESTIMADOS iguales a los propios; precio ESTIMADO]"},
    }
    if A_tot:
        out["A_total_dkk"] = A_tot * dkk
    (RESULTS_DIR / "comparacion.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main():
    o = run(load_inputs())
    print(f"A: {o['A_vmax_kmh']:.1f} km/h, jet {o['A_jet_mass_kg']:.1f} kg | B (JT132): {o['B_vmax_kmh']:.1f} km/h, "
          f"margen joroba {o['B_hump_margin']*100:.0f} %, puesta en DK {o['B_jt132_landed_eur_min']:.0f}–"
          f"{o['B_jt132_landed_eur_max']:.0f} €; fallas B: {o['B_fails']}")


if __name__ == "__main__":
    main()
