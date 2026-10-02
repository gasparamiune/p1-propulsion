"""PRB-P1.11 — Prueba hidrostática de carcasa + estator + tobera (ensayo de taller, sin CAD).

research/R12 §7.2: diseño p = 0,2 MPa (≈ 1,3 × la presión de cierre) y prueba hidrostática a 0,3 MPa. Aquí
p_ensayo = 1,5 × p_diseño de estructural.json (loads.structural_bomba.loads_used.p_design_Pa). Conjunto:
P1-PMP-01 carcasa con P1-PMP-02 anillo, P1-PMP-06 estator y P1-PMP-08 tobera. Juntas:
  • entrada (brida de la toma, f1): O-ring de CARA + espigón de centraje Ø pmp_f1_spigot_d → brida ciega con
    rebaje H7 y cara lisa, como la brida del conducto;
  • carcasa ↔ tobera (f2): O-ring RADIAL (cs oring_cs) en la espiga de pmp_noz_spigot de la tobera, dentro del
    asiento Ø pmp_D_seat de la carcasa; pmp_f2_n × M{pmp_f2_bolt} del lado seco; entre bridas queda la luz
    pmp_stack_gap (la espiga aprieta la camisa del estator): una fuga de f2 aparece en esa luz;
  • salida de la tobera (Ø D_noz): tapón con O-ring radial retenido por una varilla roscada central hasta la
    brida ciega de entrada (la tobera no tiene brida de salida).
"""
import math

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


def _geo(p):
    return dict(D_noz=float(p.D_noz), D_seat=float(p.pmp_D_seat), spig=float(p.pmp_noz_spigot),
                gap=float(p.pmp_stack_gap), n=int(p.pmp_f2_n), M=int(p.pmp_f2_bolt), cs=float(p.oring_cs),
                f1=float(p.pmp_f1_spigot_d), gl=(float(p.pmp_gl_depth), float(p.pmp_gl_width)))


def _p(p, ctx):
    lu = ctx.est.get("loads", {}).get("structural_bomba", {}).get("loads_used", {})
    pd = float(lu.get("p_design_Pa", p.pmp_p_design_Pa))
    return pd, F_PRUEBA * pd, float(p.sz["loads"]["p_pump_max_Pa"])


def checks(p, ctx, parts):
    pd, pt, pmax = _p(p, ctx)
    g = _geo(p)
    return [("p_ensayo ≥ 0,3 MPa (R12 §7.2) [MPa]", pt / 1e6, 0.3, ">="),
            ("p_ensayo / p de cierre de la bomba [—]", pt / pmax, 2.0, ">="),
            ("junta f2 radial: espiga más larga que la ranura del O-ring [mm]", g["spig"], g["gl"][1] + 2 * 3.5, ">=")]


def criterios(p, ctx):
    pd, pt, pmax = _p(p, ctx)
    g = _geo(p)
    F_tapon = pt * math.pi / 4 * (g["D_noz"] / 1000) ** 2
    return {
        "D_salida_mm": g["D_noz"], "F_tapon_N": round(F_tapon, 0), "luz_bridas_mm": g["gap"],
        "f2": f"O-ring radial cs {g['cs']:g} en espiga de {g['spig']:g} mm, asiento Ø{g['D_seat']:.2f}, "
              f"{g['n']} × M{g['M']} del lado seco",
        "p_diseno_MPa": round(pd / 1e6, 3), "p_ensayo_MPa": round(pt / 1e6, 3), "p_ensayo_bar": round(pt / 1e5, 1),
        "p_cierre_kPa": round(pmax / 1000, 1), "retencion_min": HOLD_MIN, "caida_max_frac": DROP_FRAC,
        "deformacion_max_mm": DEF_MAX_MM,
        "fuente": "estructural.json loads.structural_bomba.loads_used.p_design_Pa × 1,5 (research/R12 §7.2)",
        "ensayo": "Armar carcasa + anillo + estator; O-ring radial engrasado (silicona) en la espiga de la tobera, "
                  f"meterla en el asiento sin pellizcarlo (chaflán de entrada) y apretar los {g['n']} × M{g['M']} en "
                  f"cruz; medir con galgas la luz entre bridas (diseño {g['gap']:.2f} mm, igual en los {g['n']} "
                  "tornillos: si es 0, la espiga no aprieta la camisa del estator). Entrada: brida ciega con rebaje "
                  f"H7 para el espigón Ø{g['f1']:g} y O-ring de cara. Salida Ø{g['D_noz']:.1f}: tapón con O-ring radial "
                  f"y varilla roscada central M12 A4 hasta la brida ciega de entrada (carga {F_tapon:.0f} N a "
                  "p_ensayo), pasando por el cubo del estator antes de prensar el buje P1-PMP-07 (o con un tubo "
                  "guía). Medir el Ø del asiento del anillo antes. Llenar de agua purgando el aire por el puerto "
                  "G1/8 (arriba); bomba de prueba hidrostática manual (o bomba de engrase + manómetro 0–6 bar). "
                  f"Subir en 3 escalones, retener {HOLD_MIN} min a p_ensayo, bajar, desarmar y medir el asiento.",
        "pasa_si": f"A {pt / 1e6:.2f} MPa ({pt / 1e5:.1f} bar) durante {HOLD_MIN} min: caída ≤ {DROP_FRAC * 100:.0f} %, "
                   f"0 gotas en la brida de entrada, en la luz entre bridas carcasa ↔ tobera (O-ring radial), en el "
                   f"puerto y en los tornillos anti-rotación del estator (papel tisú), y deformación permanente del Ø "
                   f"del asiento ≤ {DEF_MAX_MM:.2f} mm. Sin aire en la prueba (seguridad: una prueba con aire guarda "
                   "energía).",
    }
