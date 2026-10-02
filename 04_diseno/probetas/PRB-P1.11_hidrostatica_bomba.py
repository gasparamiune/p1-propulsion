"""PRB-P1.11 — Prueba hidrostática de carcasa + estator + tobera (ensayo de taller, sin CAD).

research/R12 §7.2: diseño p = 0,2 MPa (≈ 1,3 × la presión de cierre) y prueba hidrostática a 0,3 MPa. Aquí
p_ensayo = 1,5 × p_diseño de estructural.json (loads.structural_bomba.loads_used.p_design_Pa). Conjunto:
P1-PMP-01 carcasa con P1-PMP-02 anillo, P1-PMP-06 estator, P1-PMP-08 tobera, O-rings de las bridas; bridas
ciegas en la entrada (brida de toma) y en la salida de la tobera; puerto G1/8 de la carcasa para manómetro.
"""
TEST = "P1.11"
KIND = "taller"
TITULO = "Prueba hidrostática de carcasa + estator + tobera"
PIEZAS = ("P1-PMP-01", "P1-PMP-02", "P1-PMP-06", "P1-PMP-08")
F_PRUEBA = 1.5           # [VERIFICADO: research/R12 §7.2 — 0,3 MPa de prueba sobre 0,2 MPa de diseño]
HOLD_MIN = 15            # [SUPUESTO: retención]
DROP_FRAC = 0.02         # [SUPUESTO: caída admisible (agua, sin aire atrapado)]
DEF_MAX_MM = 0.02        # [SUPUESTO: deformación permanente admisible del Ø del asiento del anillo]


def build(p, ctx):
    return []


def _p(p, ctx):
    lu = ctx.est.get("loads", {}).get("structural_bomba", {}).get("loads_used", {})
    pd = float(lu.get("p_design_Pa", p.pmp_p_design_Pa))
    return pd, F_PRUEBA * pd, float(p.sz["loads"]["p_pump_max_Pa"])


def checks(p, ctx, parts):
    pd, pt, pmax = _p(p, ctx)
    return [("p_ensayo ≥ 0,3 MPa (R12 §7.2) [MPa]", pt / 1e6, 0.3, ">="),
            ("p_ensayo / p de cierre de la bomba [—]", pt / pmax, 2.0, ">=")]


def criterios(p, ctx):
    pd, pt, pmax = _p(p, ctx)
    return {
        "p_diseno_MPa": round(pd / 1e6, 3), "p_ensayo_MPa": round(pt / 1e6, 3), "p_ensayo_bar": round(pt / 1e5, 1),
        "p_cierre_kPa": round(pmax / 1000, 1), "retencion_min": HOLD_MIN, "caida_max_frac": DROP_FRAC,
        "deformacion_max_mm": DEF_MAX_MM,
        "fuente": "estructural.json loads.structural_bomba.loads_used.p_design_Pa × 1,5 (research/R12 §7.2)",
        "ensayo": "Armar carcasa + anillo + estator + tobera con sus O-rings y bulones al torque de montaje; bridas "
                  "ciegas (placa de Al o contrachapado 18 mm + goma) en la entrada y la salida. Medir el Ø del asiento "
                  "del anillo antes. Llenar de agua purgando el aire por el puerto G1/8 (arriba); bomba de prueba "
                  "hidrostática manual (o bomba de engrase + manómetro 0–6 bar). Subir en 3 escalones, retener "
                  f"{HOLD_MIN} min a p_ensayo, bajar, desarmar y medir el asiento.",
        "pasa_si": f"A {pt / 1e6:.2f} MPa ({pt / 1e5:.1f} bar) durante {HOLD_MIN} min: caída ≤ {DROP_FRAC * 100:.0f} %, "
                   f"0 gotas en bridas, puerto y soldaduras (papel tisú), y deformación permanente del Ø del asiento "
                   f"≤ {DEF_MAX_MM:.2f} mm. Sin aire en la prueba (seguridad: una prueba con aire guarda energía).",
    }
