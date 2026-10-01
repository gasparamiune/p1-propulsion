"""P1-PRP-01 — Segmento de protector de hélice (×6 idénticos, 60° + solapes de media
pared). Anillo Ri = D/2 + holgura, espesor 6, largo axial 50. Uniones en 30°+60°·k con
tornillo M4 avellanado radial; arriba se fija al brazo de STR-01, abajo al patín PRP-02."""
from cadlib import *

META = dict(
    id="P1-PRP-01", name="guard_segment", desc="Segmento de aro protector de hélice (×6)",
    material="PETG", process="impresa", qty=6, frame="unit",
    load_case="Golpes en el aro (LC5 secundario), arrastre", print_rot=(0, -90, 0), solid_frac=1.0,
    orientation="Eje del anillo = Z: impactos radiales en el plano de capas.",
)
OV = 2.5     # semi-ancho angular del solape [°]


def build(p):
    Ri = p.guard_ri
    Ro = Ri + p.guard_t
    Rm = 0.5 * (Ri + Ro)
    a0, a1 = 30.0 - OV, 90.0 + OV
    pts = polar_pts(Ri, a0, a1 - 2 * OV, 16)
    pts += polar_pts(Rm, a1 - 2 * OV, a1, 2)
    pts += polar_pts(Ro, a1, a0 + 2 * OV, 16)
    pts += polar_pts(Rm, a0 + 2 * OV, a0, 2)
    L = p.guard_L
    seg = prism_yz(pts, -L / 2, L / 2)
    # agujeros radiales M4 en los solapes (30° y 90°)
    from build123d import Pos, Rot
    for a in (30.0, 90.0):
        h = Rot(a - 90.0, 0, 0) * cyl_z(2.2, Ri - 2, Ro + 2)
        seg = seg - h
    return seg


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos, Rot
    from params import loc_unit
    L = loc_unit(p, steer, tilt)
    return [L * Pos(p.s_prop, 0, -p.e) * Rot(60.0 * k, 0, 0) for k in range(6)]


def checks(p, part):
    return [("holgura radial punta–aro [mm]", p.guard_ri - p.prop_D / 2, 8.0, ">=")]
