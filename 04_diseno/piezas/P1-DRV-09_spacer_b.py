"""P1-DRV-09 — Separador de eje entre el rodamiento B y la polea conducida (AISI 316, torneado
de la barra Ø20). Parte de la pila apretada por la tuerca M12 superior; apoya solo en el
aro interior del rodamiento."""
from cadlib import *

META = dict(id="P1-DRV-09", name="spacer_b", desc="Separador de eje rodamiento B ↔ polea (316)",
            material="AISI 316", process="torneada", qty=1, frame="unit",
            load_case="Precarga de la pila (tuerca M12)", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")

OD = 19.0


def span(p):
    lay = p.layout
    return lay["u_brgB"] + p.brg_B / 2, lay["u_pulley_c"] - p.pulley_w / 2


def build(p):
    u0, u1 = span(p)
    return cyl_x(OD / 2, u0, u1, z=-p.e) - cyl_x(p.shaft_jd / 2 + 0.05, u0 - 1, u1 + 1, z=-p.e)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    u0, u1 = span(p)
    return [("largo del separador B [mm]", u1 - u0, 2.0, ">=")]
