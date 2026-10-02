"""P1-REV-06 — Tornillo con hombro de la varilla del Mach5 en el bucket, AISI 316 torneado.

Entra desde afuera: cabeza Ø13, hombro Ø8 × 10 que lleva la rótula hembra M6 de la varilla y rosca M6
(Loctite 243) en el buje soldado + brazo +Y del bucket (8 mm de rosca; no sobresale hacia la oreja de
la boquilla). Marco local: eje +y desde la cara exterior del buje soldado."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _mach5 as M5  # noqa: E402

META = dict(
    id="P1-REV-06", name="perno_varilla", desc="Tornillo con hombro Ø8 × 10 / M6 (316)",
    material="AISI 316", process="torneada", qty=1, frame="bucket", group="jet",
    load_case="Fuerza de maniobra del Mach5 (bucket sin carga del chorro)", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—",
)


def L_sh(p):
    return p.REV_eye_w + 2.0


def build(p):
    L = L_sh(p)
    s = cyl_y(p.REV_stud_d / 2, 0.0, L) + cyl_y(6.5, L, L + 4.0)
    return s + cyl_y(2.45, -(p.REV_t + p.REV_eye_off) + 0.5, 0.01)          # M6 (modelado Ø4,9)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    from params import loc_bucket
    x, z = M5.stud_xz(p)
    return [loc_bucket(p, bool(bucket), steer) * Pos(x, p.REV_y_in + p.REV_t + p.REV_eye_off, z)]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("hombro ≥ ojo + 2 [mm]", L_sh(p), p.REV_eye_w + 2.0, ">="),
            ("rosca no sobresale hacia la oreja (Y) [mm]", p.REV_y_in - p.STE_ear_y1 - 0.5, 0.5, ">=")]
