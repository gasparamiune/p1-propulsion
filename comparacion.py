#!/usr/bin/env python3
"""comparacion.py — Comprar vs construir el waterjet (README, 03 §4).

A  = este diseño (bomba propia)                      → sizing.json + bom_resumen.json
B  = AWT JT132 comprada (Ø130 / tobera Ø70, 12 kg) + el tren eléctrico de este diseño
     Prestaciones: el mismo modelo de sizing.py con D = 130 y D_tobera = 70 [VERIFICADO: R11 §4],
     impulsor diseñado por el fabricante (se usa el mismo η de diseño: ver B_vmax_caveat) y la masa
     de la unidad reemplazada: JT132 (12 kg, trae eje inox, rodamientos y sello) + lo que B conserva
     del tren de A (comparison.jt132_keeps_from_A: el acople).
     Costo (regla explícita, B_note):
       B = A − (filas de la BOM que reemplaza la JT132, con su envío UE e imprevistos)
             + (JT132 puesta en DK + adaptación de toma/acople) × (1 + imprevistos)
       · filas reemplazadas = las que cubren piezas del grupo "jet" o "drive" del CAD (salvo las que B conserva);
         una fila que además cubre piezas de otros grupos (servicios de láser/soldadura, chapa compartida)
         se PRORRATEA por la masa del CAD de las piezas cubiertas;
       · los cables y terminales de mando (categoría "Mandos" que también cubre la consola: Mach5, varillas)
         se conservan enteros: la JT132 también se acciona con cables;
       · importación con criterio único (comparison.import_basis = CIF, igual que motor/ESC de A):
         (precio FOB + flete) × (1 + arancel) × (1 + IVA).
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

KEEP_CATS = ("Mandos",)          # cables de mando: B también los necesita (si además cubren piezas de la consola)


def replaced_rows(man, bom_csv, keep_ids):
    """Filas de bom.csv que reemplaza la JT132 y fracción reemplazada de cada una (prorrateo por masa del CAD)."""
    parts = {p["id"]: p for p in man["parts"]}
    repl = {pid for pid, p in parts.items() if p.get("group") in ("jet", "drive") and pid not in keep_ids}
    out = []
    if not bom_csv.exists():
        return None, sorted(repl)
    with open(bom_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("ID"):
                continue                                   # filas de totales
            cov = (r.get("cubre") or "").split()
            hit = [c for c in cov if c in repl]
            if not hit:
                continue
            try:
                eur = float(r.get("precio_total_EUR") or 0)
            except ValueError:
                eur = 0.0
            if eur <= 0:
                continue
            others = [c for c in cov if c not in repl]
            if others and r.get("categoria", "").startswith(KEEP_CATS):
                continue                                   # cable/terminal de mando compartido: se conserva
            m_hit = sum(parts[c]["mass_g_total"] for c in hit if c in parts)
            m_all = sum(parts[c]["mass_g_total"] for c in cov if c in parts)
            frac = 1.0 if not others else (m_hit / m_all if m_all > 0 else len(hit) / len(cov))
            out.append({"ID": r["ID"], "EUR": eur, "frac": frac, "EUR_repl": eur * frac,
                        "envio": r.get("envio", "eu"), "regla": "entera" if frac == 1.0 else "prorrateo por masa"})
    return out, sorted(repl)


def run(inp: dict) -> dict:
    c = inp["comparison"]
    costs = inp["costs"]
    sz = json.loads((RESULTS_DIR / "sizing.json").read_text(encoding="utf-8"))
    man = json.loads((RESULTS_DIR / "manifest.json").read_text(encoding="utf-8"))
    bomp = RESULTS_DIR / "bom_resumen.json"
    bom = json.loads(bomp.read_text(encoding="utf-8")) if bomp.exists() else {}
    sel = sz["selection"]
    usd, dkk = inp["meta"]["usd_to_eur"], inp["meta"]["eur_to_dkk"]
    keep = set(c.get("jt132_keeps_from_A", []))

    # --- B: prestaciones con la geometría de la JT132 y su masa ---
    m_jet_cad = sum(p["mass_g_total"] for p in man["parts"] if p.get("group") == "jet") / 1000
    m_keep = sum(p["mass_g_total"] for p in man["parts"] if p["id"] in keep) / 1000
    ii = copy.deepcopy(inp)
    ii["masses"]["jet_mass_estimate_kg"] = c["jt132_mass_kg"] + m_keep
    sizing.jet_mass = lambda _inp: _inp["masses"]["jet_mass_estimate_kg"]      # no leer el manifest
    rB = sizing.evaluate(ii, sel["motor"], sel["esc"], sel["battery"], 130, 70 / 130, sel["f_pow"])
    # --- costos ---
    rows, repl_ids = replaced_rows(man, ROOT / "bom.csv", keep)
    duty, vat = c["import_duty_frac"], costs["import_vat_frac"]
    jt_lo, jt_hi = [(x * usd + c["jt132_freight_eur"]) * (1 + duty) * (1 + vat) for x in c["jt132_usd"]]
    ad_lo, ad_hi = c["jt132_adaptation_eur"]
    A_tot = bom.get("total_eur")
    cont = costs["contingency_frac"]
    if rows is not None and A_tot:
        sub_r = sum(r["EUR_repl"] for r in rows)
        ship_r = sum(r["EUR_repl"] for r in rows if r["envio"] == "eu") * costs["shipping_frac"]
        minus = sub_r * (1 + cont) + ship_r
        B_lo = A_tot - minus + (jt_lo + ad_lo) * (1 + cont)
        B_hi = A_tot - minus + (jt_hi + ad_hi) * (1 + cont)
    else:
        sub_r = ship_r = minus = None
        B_lo = B_hi = None
    out = {
        "A_total_eur": A_tot, "A_vmax_kmh": sz["performance"]["vmax_cont_kmh"],
        "A_hump_margin": sz["performance"]["hump_margin_min"], "A_jet_mass_kg": m_jet_cad,
        "A_jet_cost_eur": sub_r, "A_jet_cost_with_ship_cont_eur": minus, "jet_part_ids": repl_ids,
        "B_replaced_rows": rows,
        "B_jt132_landed_eur_min": jt_lo, "B_jt132_landed_eur_max": jt_hi,
        "B_adaptation_eur_min": ad_lo, "B_adaptation_eur_max": ad_hi,
        "B_total_eur_min": B_lo, "B_total_eur_max": B_hi,
        "B_jet_mass_kg": c["jt132_mass_kg"], "B_kept_mass_kg": m_keep,
        "B_vmax_kmh": rB["vmax_cont_kmh"], "B_hump_margin": rB["hump_margin"],
        "B_planes": rB["planes"], "B_mass_total_kg": rB["mass_kg"], "B_S_top": rB["S_top"],
        "B_P_bat_legal_W": rB["P_bat_legal_W"], "B_hard_ok": rB["hard_ok"],
        "B_fails": [k[3:] for k in rB if k.startswith("ok_") and not rB[k]],
        "B_note": ("B = A − filas de la BOM reemplazadas por la JT132 (grupos jet + drive del CAD salvo "
                   f"{', '.join(sorted(keep)) or '—'}; filas compartidas prorrateadas por masa; cables de mando conservados) "
                   f"con su envío UE ({costs['shipping_frac'] * 100:.0f} %) e imprevistos ({cont * 100:.0f} %) + "
                   f"(JT132 puesta en DK con base {c.get('import_basis', 'CIF')}: (FOB + flete {c['jt132_freight_eur']:.0f} €) × "
                   f"(1 + {duty * 100:.1f} % arancel) × (1 + {vat * 100:.0f} % IVA) + adaptación de toma/acople "
                   f"{ad_lo:.0f}–{ad_hi:.0f} € [ESTIMADO]) × (1 + {cont * 100:.0f} % imprevistos). Precio FOB y flete [ESTIMADO]: cotizar."),
        "B_vmax_caveat": ("B_vmax usa el modelo de sizing.py con la geometría VERIFICADA de la JT132 (Ø130/Ø70) pero el η de "
                          "diseño y la curva de NUESTRA bomba: AWT no publica la curva H-Q del impulsor estándar (R11 §4). "
                          "Leer como «≈ A ± curva AWT», no como una ventaja de B; se resuelve con la curva del fabricante."),
        "maytech_mtwj12kw_eur": c["maytech_mtwj12kw_usd"] * usd,
        "spark_parts_eur": c["spark_impeller_eur"] + c["spark_wearring_eur"],
        "lampuga": c["lampuga_air"],
        "_etiquetas": {"B": "[CALCULADO: modelo de sizing.py con la geometría VERIFICADA de la JT132 (R11 §4); "
                            "η y curva del impulsor de AWT ESTIMADOS iguales a los propios; precio, flete y adaptación ESTIMADOS]"},
    }
    if A_tot:
        out["A_total_dkk"] = A_tot * dkk
    (RESULTS_DIR / "comparacion.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main():
    o = run(load_inputs())
    tot = (f"; B total {o['B_total_eur_min']:.0f}–{o['B_total_eur_max']:.0f} € (A {o['A_total_eur']:.0f} €)"
           if o["B_total_eur_min"] is not None else "")
    print(f"A: {o['A_vmax_kmh']:.1f} km/h, jet {o['A_jet_mass_kg']:.1f} kg | B (JT132): {o['B_vmax_kmh']:.1f} km/h, "
          f"margen joroba {o['B_hump_margin']*100:.0f} %, puesta en DK {o['B_jt132_landed_eur_min']:.0f}–"
          f"{o['B_jt132_landed_eur_max']:.0f} €{tot}; fallas B: {o['B_fails']}")


if __name__ == "__main__":
    main()
