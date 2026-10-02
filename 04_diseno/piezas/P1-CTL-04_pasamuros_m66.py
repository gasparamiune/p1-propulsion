"""P1-CTL-04 — Pasamuros del cable de dirección M66, AISI 316 torneado.

Brida Ø32 × 3 por fuera del espejo (Sikaflex), cuerpo Ø20 M20×1,5 a través del espejo y de la placa
P1-CTL-01 con tuerca A4 por dentro, cabeza Ø32 con rosca hembra 7/8"-14 UNF donde se enrosca el tubo
del M66 [ESTIMADO: rosca del extremo de los cables de fueraborda; buscar "Ultraflex M66 7/8-14"].
La barra (Ø 3/8" [ESTIMADO]) pasa por el agujero Ø9,6 con junta tórica + rascador y sale hacia la biela
del yugo; fuelle de goma por fuera. El paso queda sobre la flotación estática."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_x  # noqa: E402

META = dict(
    id="P1-CTL-04", name="pasamuros_m66", desc="Pasamuros 316 del M66 (brida, M20, rosca 7/8\" UNF)",
    material="AISI 316", process="torneada", qty=1, frame="boat", group="ele",
    load_case="Tiro/empuje del M66 contra la placa del espejo", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="—", allow={"P1-REF-01": 2000.0, "P1-CTL-06": 5.0},
)


def build(p):
    _, y, z = p.CTL_m66_pt
    s = cyl_x(16.0, -3.0, 0.0, y=y, z=z) + cyl_x(10.0, -0.01, 20.0, y=y, z=z) + cyl_x(16.0, 20.0, 40.0, y=y, z=z)
    s = s - cyl_x(p.CTL_gland_m66_bore / 2 + 0.05, -4.0, 41.0, y=y, z=z)
    return s - cyl_x(p.CTL_m66_tube_d / 2, 22.0, 41.0, y=y, z=z)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("cuerpo cubre espejo + placa + tuerca [mm]", 20.0, p.transom_t + 6.0 + 8.0, ">="),
            ("pared del cuerpo en la rosca del tubo [mm]", (32.0 - p.CTL_m66_tube_d) / 2, 3.0, ">=")]
