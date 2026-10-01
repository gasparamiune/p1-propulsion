"""P1-MNT-02 — Zapata del tornillo de apriete (×2). Aísla el inox del casco de aluminio."""
from cadlib import *

META = dict(
    id="P1-MNT-02", name="clamp_pad", desc="Zapata giratoria del tornillo de apriete (aislante)",
    material="PETG", process="impresa", qty=2, frame="boat",
    load_case="Apriete del tornillo (compresión)", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Plana, cara de apoyo sobre la cama; compresión a través de capas (admisible).",
)


def build(p):
    t, D = p.pad_t, p.pad_d
    pad = cyl_z(D / 2, 0, t)
    pad = pad - cyl_z((p.clamp_screw_d + 0.6) / 2, 4, t + 1)          # alojamiento de la punta
    pad = pad - cyl_y(1.6, -D / 2 - 1, D / 2 + 1, z=t - 3.5)          # pasador de retención Ø3
    return pad


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos, Rot
    x_face = -p.tr_t                     # cara interior del espejo
    return [Pos(x_face, y, -70) * Rot(0, -90, 0) for y in (-45, 45)]


def checks(p, part):
    return [("espesor de zapata", p.pad_t, 10.0, ">=")]
