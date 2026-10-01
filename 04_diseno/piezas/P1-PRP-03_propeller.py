"""P1-PRP-03 — Hélice comprada (envolvente: cubo + volumen barrido por las palas)."""
from cadlib import *

META = dict(id="P1-PRP-03", name="propeller", desc="Hélice comprada (ver BOM) — volumen barrido",
            material="Al / compuesto", process="comprada", qty=1, frame="unit",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    s, vs = p.s_prop, -p.e
    hub = cyl_x(p.prop_hub_d / 2, s - p.prop_hub_L / 2, s + p.prop_hub_L / 2, z=vs)
    disc = cyl_x(p.prop_D / 2, s - 0.1 * p.prop_D, s + 0.1 * p.prop_D, z=vs)
    return (hub + disc) - cyl_x(p.shaft_d / 2 + 0.1, s - p.prop_D, s + p.prop_D, z=vs)


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
