"""P1-HSG-05 — Capó ventilado del motor (protección de salpicaduras y de contacto).
Abierto abajo y adelante (atornilla a la cara de popa de la placa motriz). Rejillas
laterales para la refrigeración del outrunner."""
from cadlib import *

META = dict(
    id="P1-HSG-05", name="motor_hood", desc="Capó ventilado del motor",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="Salpicaduras; temperatura del motor (≤ 60 °C en la pieza)", print_rot=(0, 90, 0), solid_frac=1.0,
    orientation="Cara trasera sobre la cama (techo y laterales verticales, sin puentes largos).",
)


def dims(p):
    t = p.cover_wall
    u0 = p.plate_u_aft + 0.3
    u1 = u0 + p.motor_l + 12
    v0 = p.cradle_vtop + 4
    v1 = p.motor_v + p.motor_d / 2 + p.tension_slot + 4 + t
    W = p.motor_d / 2 + 2.0 + t
    return u0, u1, v0, v1, W, t


def build(p):
    u0, u1, v0, v1, W, t = dims(p)
    h = box(u0, u1, -W, W, v0, v1) - box(u0 - 1, u1 - t, -W + t, W - t, v0 - 1, v1 - t)
    # rejillas laterales
    for k in range(5):
        u = u0 + 14 + k * 12
        h = h - box(u, u + 6, -W - 1, W + 1, v0 + 10, v1 - 14)
    return h


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    u0, u1, v0, v1, W, t = dims(p)
    return [("holgura capó–motor radial [mm]", W - t - p.motor_d / 2, 1.5, ">="),
            ("ancho del capó < luz entre mejillas", 2 * W, p.cradle_w, "<=")]
