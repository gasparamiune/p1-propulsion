"""P1-ELE-02 — Tapa-disipador de aluminio 5052/6082 de 4 mm (mecanizada: cortar y taladrar).
El ESC se atornilla debajo con pad térmico: la tapa es el camino de calor al aire."""
from cadlib import *

META = dict(id="P1-ELE-02", name="esc_lid_heatsink", desc="Tapa-disipador Al 4 mm (mecanizada)",
            material="Al 5052/6082", process="torneada", qty=1, frame="boat_free",
            load_case="Compresión del O-ring; disipación ESC", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    Li, Wi, Hi = p.esc_in
    rim = 12.0
    Lo, Wo = Li + 2 * rim, Wi + 2 * rim
    lid = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, 4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid - cyl_z(2.2, -1, 5, x=sx * (Lo / 2 - 4.5), y=sy * (Wo / 2 - 4.5))
    return lid


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    Li, Wi, Hi = p.esc_in
    return [Pos(-700, 150, -300 + 3.2 + Hi + 0.05)]


def checks(p, part):
    return []
