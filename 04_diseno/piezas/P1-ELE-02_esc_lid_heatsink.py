"""P1-ELE-02 — Tapa-disipador de aluminio 5052/6082 de 4 mm (mecanizada: cortar y taladrar).
El ESC se atornilla debajo con pad térmico: la tapa es el camino de calor al aire."""
from cadlib import *

META = dict(id="P1-ELE-02", name="esc_lid_heatsink", desc="Tapa-disipador Al 4 mm (mecanizada)",
            material="Al 5052/6082", process="torneada", qty=1, frame="boat_free",
            load_case="Compresión del O-ring; disipación ESC", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    Li, Wi, Hi = p.esc_in
    rim = 18.0                       # = ELE-01 RIM
    Lo, Wo = Li + 2 * rim, Wi + 2 * rim
    lid = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, 4)
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("eb", os.path.join(os.path.dirname(__file__), "P1-ELE-01_esc_box.py"))
    eb = importlib.util.module_from_spec(spec); spec.loader.exec_module(eb)
    for (x, y) in eb.lid_holes(p):
        lid = lid - cyl_z(2.2, -1, 5, x=x, y=y)
    return lid


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    Li, Wi, Hi = p.esc_in
    return [Pos(-700, 150, -300 + 3.2 + Hi + 0.05)]


def checks(p, part):
    return []
