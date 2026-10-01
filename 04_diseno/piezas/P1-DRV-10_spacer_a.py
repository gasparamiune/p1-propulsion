"""P1-DRV-10 — Separador de eje entre la polea conducida y el rodamiento A (AISI 316, torneado
de la barra Ø20). Atraviesa el agujero de la placa motriz y el labio del cartucho (Ø21);
apoya solo en el aro interior del rodamiento A."""
from cadlib import *

META = dict(id="P1-DRV-10", name="spacer_a", desc="Separador de eje polea ↔ rodamiento A (316)",
            material="AISI 316", process="torneada", qty=1, frame="unit",
            load_case="Precarga de la pila; empuje en marcha atrás", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")

OD = 19.0


def span(p):
    lay = p.layout
    return lay["u_pulley_c"] + p.pulley_w / 2, lay["u_brgA"] - p.brg_B / 2


def build(p):
    u0, u1 = span(p)
    return cyl_x(OD / 2, u0, u1, z=-p.e) - cyl_x(p.shaft_jd / 2 + 0.05, u0 - 1, u1 + 1, z=-p.e)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    u0, u1 = span(p)
    return [("largo del separador A [mm]", u1 - u0, 2.0, ">="),
            ("holgura radial al labio del cartucho (Ø21) [mm]", 10.5 - OD / 2, 0.5, ">=")]
