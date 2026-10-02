"""P1-CTL-06 — Tubo terminal del cable de dirección Ultraflex M66 (COMPRADO; R11 §7: desde 735 kr).

Se enrosca en el pasamuros P1-CTL-04 y corre por dentro del casco hacia proa; la barra sale a popa por
el pasamuros. [ESTIMADO: tubo Ø7/8" × 230; buscar "Ultraflex M66 dimensions"]."""
from cadlib import cyl_x

META = dict(
    id="P1-CTL-06", name="terminal_m66", desc="Tubo terminal del cable M66 (comprado)",
    material="Acero", process="comprada", qty=1, frame="boat", group="ele",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=350.0,   # [ESTIMADO]
)


def build(p):
    _, y, z = p.CTL_m66_pt
    return cyl_x(p.CTL_m66_tube_d / 2, 22.0, 22.0 + p.CTL_m66_tube_L, y=y, z=z) - \
        cyl_x(p.CTL_gland_m66_bore / 2 + 0.3, 21.0, 23.0 + p.CTL_m66_tube_L, y=y, z=z)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "=")]
