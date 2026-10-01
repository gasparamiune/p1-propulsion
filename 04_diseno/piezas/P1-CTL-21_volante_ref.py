"""P1-CTL-21 — Volante Osculati Ø320 + timonería rotativa Ultraflex T85 (REFERENCIA; R11 §7).

Aro Ø320 en el plano x = CTL_wheel_x, cubo, eje Ø20 que atraviesa el panel de la consola y caja de
la timonería por dentro [ESTIMADO: dimensiones de la T85; buscar "Ultraflex T85 dimensions"]. De la
T85 sale el cable M66 por la banda de babor hasta el espejo (P1-CTL-04/06)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build123d import Pos, Rot, Torus  # noqa: E402
from cadlib import box, cyl_x  # noqa: E402

META = dict(
    id="P1-CTL-21", name="volante_ref", desc="Volante Ø320 + timonería T85 (referencia)",
    material="referencia", process="referencia", qty=1, frame="boat", group="ref",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def build(p):
    xw, zw, R = p.CTL_wheel_x, p.CTL_wheel_z, p.CTL_wheel_d / 2
    x0 = p.CTL_console_x0
    ring = Pos(xw, 0, zw) * Rot(0, 90, 0) * Torus(R - 12.5, 12.5)
    s = ring + cyl_x(30.0, xw - 20, xw + 30, z=zw)
    for a in (90, 210, 330):
        import math
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        s = s + Pos(xw, (R - 20) / 2 * c, zw + (R - 20) / 2 * sn) * Rot(a, 0, 0) * box(-6, 6, -(R - 20) / 2, (R - 20) / 2, -4, 4)
    s = s + cyl_x(10.0, xw + 29, x0 + p.CTL_ply_t + 1, z=zw)
    s = s + box(x0 + p.CTL_ply_t + 0.5, x0 + p.CTL_ply_t + 110, -60, 60, zw - 70, zw + 60)
    return s


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("volante a popa del panel [mm]", p.CTL_console_x0 - (p.CTL_wheel_x + 12.5), 50.0, ">="),
            ("aro sobre el piso [mm]", p.CTL_wheel_z - p.CTL_wheel_d / 2 - p.floor_z, 100.0, ">=")]
