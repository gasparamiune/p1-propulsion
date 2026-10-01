"""PRB-P1.7 — Cubos de absorción 20 mm (PENDIENTES_GASPAR §P1.7).

Tres cubos rotulados A/B/C (relieve arriba) impresos con el perfil ESTRUCTURAL: tienen relleno
gyroid interno (poros abiertos entre perímetros y relleno) → caso más desfavorable de absorción
de las piezas sumergidas (STR-01 y PRP-05 usan ese perfil).
"""
from cadlib import *  # noqa: F401,F403
from _probelib import label

TEST = "P1.7"
A = 20.0                     # [VERIFICADO: PENDIENTES_GASPAR §P1.7 / tarea: cubos de 20 mm]
SALT_G_L = 25.0              # [VERIFICADO: PENDIENTES_GASPAR §P1.5: agua salada 25 g/L]


def build(p, ctx):
    out = []
    for k in "ABC":
        c = box(-A / 2, A / 2, -A / 2, A / 2, 0, A) + label(k, 0, 0, A, size=8.0)
        out.append((dict(id=f"P1.7{k}", name=f"cubo_absorcion_{k}", desc=f"Cubo {A:g} mm rotulado {k}",
                         test=TEST, profile="estructural", qty=1, solid_frac=1.0,
                         orientation="Cara de cama abajo; rótulo arriba."), c))
    return out


def checks(p, ctx, parts):
    bb = parts["P1.7A"].bounding_box()
    return [("arista del cubo [mm]", bb.max.X - bb.min.X, A, "=")]


def criterios(p, ctx):
    return {
        "sal_g_L": SALT_G_L,
        "ensayo": "Acondicionar 48 h a temperatura ambiente con desecante (no secar a 65 °C: Tg 69 °C); pesar m0 "
                  "(balanza 0,01 g). Sumergir 7 días en agua con 25 g/L de sal a temperatura ambiente; secar la "
                  "superficie con papel y pesar m7 en < 1 min. Opcional: seguir a 30 días (saturación en semanas, "
                  "research/R05 A2).",
        "pasa_si": "Ganancia (m7 − m0)/m0 ≤ 1 % en los 3 cubos (PENDIENTES §P1.7). Referencia: PETG macizo ~0,3 % a "
                   "saturación [VERIFICADO: research/R05 S11]; impreso más por porosidad [VERIFICADO: R05 S14].",
        "si_no_pasa": "Subir perímetros/relleno de las piezas sumergidas (perfil fusible = 100 %) o sellar con epoxi.",
    }
