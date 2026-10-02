"""PRB-P1.7 — Cubos de absorción de agua 20 mm con el perfil de la pieza impresa mojada (P1-INT-04).

Tres cubos rotulados A/B/C (relieve arriba) impresos con la familia de P1-INT-04 (familias.py: «sellado»,
100 %): la tapa de inspección es la única pieza impresa que trabaja mojada y a presión (cara interior de la
chimenea). Las del controlador (P1-ELE-01/02, P1-CTL-02/03) van secas, sobre el piso o la consola.
La ganancia de masa se compara con la pérdida de resistencia que supone structural.py (materials.design_factors
.f_water de inputs.yaml).
"""
from cadlib import *  # noqa: F401,F403
from _probelib import label, petg
import familias as FAM

TEST = "P1.7"
KIND = "impresa"
TITULO = "Absorción de agua (perfil de P1-INT-04)"
PIEZAS = ("P1-INT-04",)
SRC = "P1-INT-04"
A = 20.0                     # [VERIFICADO: PENDIENTES_GASPAR §P1.7: cubos de 20 mm]
SALT_G_L = 25.0              # [VERIFICADO: PENDIENTES_GASPAR §P1.5: agua salada 25 g/L]
GAIN_MAX = 0.01              # [VERIFICADO: PENDIENTES_GASPAR §P1.7: ganancia ≤ 1 %]
DAYS = 7


def build(p, ctx):
    fam = FAM.familia({"id": SRC})[0]
    sf = float(ctx.part(SRC).META.get("solid_frac", 1.0))
    out = []
    for k in "ABC":
        c = box(-A / 2, A / 2, -A / 2, A / 2, 0, A) + label(k, 0, 0, A, size=8.0)
        out.append((dict(id=f"P1.7{k}", name=f"cubo_absorcion_{k}", desc=f"Cubo {A:g} mm rotulado {k}",
                         test=TEST, profile=fam, qty=1, solid_frac=sf,
                         orientation="Cara de cama abajo; rótulo arriba."), c))
    return out


def checks(p, ctx, parts):
    bb = parts["P1.7A"].bounding_box()
    return [("arista del cubo [mm]", bb.max.X - bb.min.X, A, "=")]


def criterios(p, ctx):
    _m, df = petg(ctx)
    return {
        "sal_g_L": SALT_G_L, "dias": DAYS, "ganancia_max": GAIN_MAX, "f_water": df.get("f_water"),
        "perfil": FAM.familia({"id": SRC})[0],
        "ensayo": "Acondicionar 48 h con desecante (no secar a 65 °C: Tg ~69 °C); pesar m0 (balanza 0,01 g). "
                  f"Sumergir {DAYS} días en agua con {SALT_G_L:g} g/L de sal a temperatura ambiente; secar la "
                  f"superficie con papel y pesar m{DAYS} en < 1 min. Opcional: seguir a 30 días (saturación en "
                  "semanas, research/R05 A2).",
        "pasa_si": f"Ganancia (m{DAYS} − m0)/m0 ≤ {GAIN_MAX * 100:.0f} % en los 3 cubos. Referencia: PETG macizo "
                   "~0,3 % a saturación [VERIFICADO: research/R05 S11]; impreso absorbe más por porosidad "
                   "[VERIFICADO: R05 S14].",
        "si_no_pasa": "Revisar secado del filamento y solape relleno–perímetro del perfil sellado; la tapa es "
                      "reemplazable (el CAD está) — inspeccionarla cada temporada.",
    }
