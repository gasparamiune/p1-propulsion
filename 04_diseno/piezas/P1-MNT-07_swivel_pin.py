"""P1-MNT-07 — Perno de dirección Ø16 (AISI 316, torneado). Rosca M16 abajo con tuerca
autoblocante A4 + arandela elástica (fricción de dirección regulable)."""
from cadlib import *

META = dict(id="P1-MNT-07", name="swivel_pin", desc="Perno de dirección Ø16 × L (316 torneado, rosca M16 inferior)",
            material="AISI 316", process="torneada", qty=1, frame="yoke",
            load_case="LC5/LC1 momento de vuelco", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—")


def build(p):
    z_top = p.disc_z0 + p.disc_t + 4
    z_bot = p.boss_bot_z - 22
    pin = cyl_z(p.swivel_pin_d / 2, z_bot, z_top, x=p.swivel_x)
    pin = pin + cyl_z(p.swivel_pin_d / 2 + 4, z_top, z_top + 5, x=p.swivel_x)  # cabeza
    return pin


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return []
