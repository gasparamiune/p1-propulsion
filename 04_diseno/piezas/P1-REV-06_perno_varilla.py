"""P1-REV-06 — Perno con hombro de la varilla del Mach5 en el bucket, AISI 316 torneado.

Hombro Ø8 × 10 (lleva la rótula hembra M6 de la varilla), rosca M6 que atraviesa el brazo +Y del
bucket con tuerca autoblocante A4 por dentro. Marco local: eje +y desde la cara exterior del brazo."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _mach5 as M5  # noqa: E402

META = dict(
    id="P1-REV-06", name="perno_varilla", desc="Perno con hombro Ø8 × 10 / M6 (316)",
    material="AISI 316", process="torneada", qty=1, frame="bucket", group="jet",
    load_case="Fuerza de maniobra del Mach5 (bucket sin carga del chorro)", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—",
)


def build(p):
    s = cyl_y(p.REV_stud_d / 2, 0.0, 10.0) + cyl_y(6.5, 10.0, 14.0)
    return s + cyl_y(2.9, -p.REV_t - 6.0, 0.01)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    from params import loc_bucket
    x, z = M5.stud_xz(p)
    return [loc_bucket(p, bool(bucket), steer) * Pos(x, p.REV_y_in + p.REV_t, z)]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("hombro ≥ ancho del ojo + 2 [mm]", 10.0, p.REV_eye_w + 2.0, ">=")]
