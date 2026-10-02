"""PRB-P1.10 — Hinchamiento de los bujes POM-C en agua, 48 h (ensayo de taller, sin CAD).

Bujes: P1-PMP-07 (2.º apoyo del eje, Ø int pmp_brg_id sobre el eje Ø shaft_d, prensado en el cubo del
estator) y P1-PMP-11 (pivote de la boquilla, Ø int pmp_lug_bush_id sobre el perno Ø steer_pin_d, prensados
en las orejas de P1-PMP-09). El POM-C absorbe poco agua pero el prensado H7/s6 ya achica el Ø interior; el
ensayo mide el juego REAL montado, seco y tras 48 h en agua, contra el eje/perno real.
"""
TEST = "P1.10"
KIND = "taller"
TITULO = "Hinchamiento de los bujes POM-C a 48 h en agua"
PIEZAS = ("P1-PMP-07", "P1-PMP-11")
HORAS = 48               # [VERIFICADO: tarea]
F_MIN = 0.5              # holgura mínima = 50 % de la del CAD [SUPUESTO: criterio; confirmar con el fabricante del buje]


def build(p, ctx):
    return []


def _rows(p):
    return [dict(id="P1-PMP-07", eje="eje P1-DRV-01", d=float(p.shaft_d), D=float(p.pmp_brg_id)),
            dict(id="P1-PMP-11", eje="perno con hombro de dirección", d=float(p.steer_pin_d), D=float(p.pmp_lug_bush_id))]


def checks(p, ctx, parts):
    return [(f"{r['id']}: holgura del CAD > 0 [mm]", r["D"] - r["d"], 0.01, ">=") for r in _rows(p)]


def criterios(p, ctx):
    rows = []
    for r in _rows(p):
        c = r["D"] - r["d"]
        rows.append({**r, "c_cad_mm": round(c, 3), "c_min_mm": round(F_MIN * c, 3),
                     "D_min_mm": round(r["d"] + F_MIN * c, 3)})
    return {
        "horas": HORAS, "f_min": F_MIN, "bujes": rows,
        "ensayo": "Tornear los bujes, prensarlos en su alojamiento definitivo (estator / orejas de la placa de espejo, "
                  "ya anodizados). Medir Ø int en 3 alturas × 2 direcciones con pernos patrón o alesómetro, y el Ø real "
                  f"del eje/perno con micrómetro. Sumergir el conjunto {HORAS} h en agua del lugar a temperatura "
                  "ambiente; secar y medir dentro de 10 min. El eje/perno real tiene que girar a mano sin puntos duros.",
        "pasa_si": "; ".join(f"{r['id']}: Ø int a {HORAS} h ≥ Ø {r['eje']} medido + {r['c_min_mm']:.2f} mm "
                             f"(≥ {r['D_min_mm']:.2f} con Ø nominal {r['d']:g}; CAD {r['D']:g})" for r in rows)
                   + ". Si no: repasar el Ø int con escariador al Ø del CAD y repetir.",
    }
