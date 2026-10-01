"""P1-CTL-20 — Consola de Jorge (REFERENCIA, contrachapado 12 mm) para ubicar los mandos.

[SUPUESTO: panel en x = CTL_console_x0, tapa a CTL_console_top, ancho 2·CTL_console_hw — MEDIR la
consola real]. Recortes: unidad de palancas (P1-CTL-02/08), pasacables del kill switch, eje del timón."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_x, cyl_z  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-20", name="consola_ref", desc="Consola (referencia, medir la real)",
    material="referencia", process="referencia", qty=1, frame="boat", group="ref",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def build(p):
    t = p.CTL_ply_t
    x0, x1, hw, zt = p.CTL_console_x0, p.CTL_console_x1, p.CTL_console_hw, p.CTL_console_top
    z0 = p.floor_z + 5.0
    s = box(x0, x0 + t, -hw, hw, z0, zt)                                   # panel (cara a popa)
    s = s + box(x0, x1, -hw, hw, zt, zt + t)                               # tapa
    s = s + box(x0 + t, x1, hw - t, hw, z0, zt) + box(x0 + t, x1, -hw, -hw + t, z0, zt)   # costados
    ax, ay, az = p.CTL_axis
    s = s - box(ax - 90, ax + 55, ay - 24, ay + 24, zt - 1, zt + t + 1)    # recorte de la unidad de palancas
    s = s - cyl_z(10.0, zt - 1, zt + t + 1, x=1735.0, y=30.0)             # pasacables del kill switch
    s = s - cyl_x(14.0, x0 - 1, x0 + t + 1, z=p.CTL_wheel_z)               # eje del timón
    return s


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("tapa a ≤ 0,3 m sobre la borda (alcance) [mm]", p.CTL_console_top - p.inp["boat"]["gunwale_height_m"] * 1000, 300.0, "<=")]
