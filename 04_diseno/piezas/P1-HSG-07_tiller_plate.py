"""P1-HSG-07 — Placa de caña Al 6082-T6 de 10 mm (mecanizada: cortar, taladrar).
Se aprieta SOBRE la cuna con los 4 pernos M6 A4 pasantes de la tapa (MNT-06) y se
extiende a babor hasta w = 86 mm; allí dos abrazaderas impresas (HSG-04) sujetan el tubo
de caña Ø30 (HSG-06) a w = 70, por fuera de mejillas, capó y cubrecorrea.
El momento de la caña llega a la cuna como par de fuerzas entre los pernos (u = 20 y 80)."""
import math
from cadlib import *

META = dict(id="P1-HSG-07", name="tiller_plate", desc="Placa de caña Al 6082-T6 10 mm (mecanizada)",
            material="Al 5052/6082", process="torneada", qty=1, frame="unit",
            load_case="LC7 manipulación (torsión en la placa)", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—")
T_PL = 10.0
U0, U1 = 18.0, 95.0
W_TILLER = 70.0


def build(p):
    v0 = p.cradle_vtop
    W = p.cradle_w / 2
    pl = box(U0, U1, -W, W_TILLER + 16, v0, v0 + T_PL)
    for u in (20.0, 80.0):
        for w in (-29.0, 29.0):
            pl = pl - cyl_z(3.25, v0 - 1, v0 + T_PL + 1, x=u, y=w)
    pl = pl - cyl_z(4.25, v0 - 1, v0 + T_PL + 1, x=70.0, y=0)              # cáncamo M8 (cabo de seguridad)
    for u in (30.0, 85.0):                                                 # abrazaderas de caña
        for w in (W_TILLER - 12, W_TILLER + 12):
            pl = pl - cyl_z(3.25, v0 - 1, v0 + T_PL + 1, x=u, y=w)
    return pl


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("placa de caña: luz a la mejilla exterior [mm]", W_TILLER - 15 - (p.cheek_y + p.cheek_t / 2), 2.0, ">=")]
