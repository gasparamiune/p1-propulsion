"""P1-HSG-03 — Cubrecorrea (protección de atrapamiento). Abierto hacia la placa motriz."""
from cadlib import *

META = dict(
    id="P1-HSG-03", name="belt_guard", desc="Cubrecorrea / protección de poleas",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="Salpicaduras, manipulación leve", print_rot=(0, -90, 0), solid_frac=1.0,
    orientation="Cara cerrada sobre la cama, abierto arriba (sin puentes).",
)


def dims(p):
    vs = -p.e
    t = p.cover_wall
    u0 = p.layout["u_shaft_top"] - 6
    u1 = p.plate_u_fwd - 0.3
    v0 = vs - p.pd_shaft / 2 - 3 - 6 - t
    v1 = p.motor_v + p.tension_slot + p.pd_motor / 2 + 3 + 3 + t   # polea del motor en su tensado máximo
    W = p.pd_shaft / 2 + 3.0 + 3.0 + t                          # polea conducida (disco en el plano v–w)
    return u0, u1, v0, v1, W, t


def build(p):
    u0, u1, v0, v1, W, t = dims(p)
    g = box(u0, u1, -W, W, v0, v1) - box(u0 + t, u1 + 1, -W + t, W - t, v0 + t, v1 - t)
    # 4 agujeros M4 en las paredes laterales (tornillos a insertos en el canto de la placa)
    for v in (v0 + 15, v1 - 15):
        g = g - cyl_y(2.2, -W - 1, W + 1, x=u1 - 4, z=v)
    return g


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    u0, u1, v0, v1, W, t = dims(p)
    return [("holgura polea conducida–cubrecorrea [mm]", W - t - (p.pd_shaft / 2 + 3), 2.5, ">=")]
