"""P1-PRP-05 — Placa antiventilación sobre la hélice (impresa plana, recambiable): impide que
la hélice aspire aire de la superficie cuando se navega con la cola levantada en aguas
someras (research/R02 B4: a poca inmersión la hélice ventila). 2×M4 al brazo de STR-01."""
import importlib.util
import os
from cadlib import *

META = dict(
    id="P1-PRP-05", name="antivent_plate", desc="Placa antiventilación sobre la hélice",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="Presión hidrodinámica baja; golpes leves", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Plana: flexión en el plano de capas.",
)
T = 5.0


def build(p):
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("gg", os.path.join(here, "_guard_geom.py"))
    gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
    u_hole, r_hole, r_top, lt, la2, r_prof = gg.lug_geom(p)
    vs = -p.e
    arm1 = vs + r_top + 9.5
    u_le = p.s_prop - p.guard_L / 2
    pl = box(u_le - 20, p.s_prop + p.guard_L / 2 + 4, -60, 60, arm1, arm1 + T)
    for u in (u_le - 2.0, u_hole + la2 - 2.0):
        pl = pl - cyl_z(2.2, arm1 - 1, arm1 + T + 1, x=u)
    return pl


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
