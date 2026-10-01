"""P1-REV-08 — Varilla del Mach5 con rótula hembra M6 en el perno del bucket (COMPRADA con el cable).

Vertical (la cuerda del perno es vertical, a popa del pivote): baja 45,9 mm al bajar el bucket, sin girar.
Placements: marco de la boquilla + traslación en Z según el estado del bucket."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y, cyl_z  # noqa: E402
import _mach5 as M5  # noqa: E402

META = dict(
    id="P1-REV-08", name="varilla_mach5", desc="Varilla Ø6,4 + rótula M6 del Mach5 (comprada)",
    material="AISI 316", process="comprada", qty=1, frame="bucket", group="jet",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=40.0,   # [ESTIMADO]
)


def build(p):
    sx, sz = M5.stud_xz(p)
    ry = M5.rod_y(p)
    w = p.REV_eye_w
    eye = cyl_y(9.0, ry - w / 2, ry + w / 2, x=sx, z=sz) - cyl_y(p.REV_stud_d / 2 + 0.1, ry - w, ry + w, x=sx, z=sz)
    # (el separador POM entre brazo y ojo viene con el perno)
    rod = cyl_z(3.2, sz + 8.0, p.REV_sleeve_z0 + 60.0, x=sx, y=ry)
    return eye + rod


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    from params import loc_steer
    return [loc_steer(p, steer) * Pos(0, 0, M5.dz(p) if bucket else 0.0)]


def checks(p, part):
    dz = M5.dz(p)
    top = p.REV_sleeve_z0 + 60.0
    tops = (top, top + dz)
    zs = (M5.stud_xz(p)[1], M5.stud_xz(p, True)[1])
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("varilla dentro de la vaina (mínimo) [mm]", min(tops) - p.REV_sleeve_z0, 10.0, ">="),
            ("varilla: margen al fondo de la vaina [mm]", (p.REV_sleeve_z0 + M5.SLEEVE_L + M5.HUB_L - 5) - max(tops), 5.0, ">="),
            ("varilla expuesta mínima [mm]", p.REV_sleeve_z0 - (max(zs) + 9.0), 8.0, ">=")]
