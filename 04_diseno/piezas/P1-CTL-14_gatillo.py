"""P1-CTL-14 — Gatillo de la palanca del bucket (Al 6061-T6 6 mm), tira del Bowden de liberación del émbolo.

Pivota en el mango superior de P1-CTL-10 (pasador Ø4 A4) con resorte de retorno; apretado contra el
mango recorre ≥ el recorrido de liberación del émbolo + juego del Bowden. La vaina apoya en un tope del
mango (no modelado). Se mueve con la palanca (estados del bucket).
Con traba en los dos brazos del bucket (REV_n_locks = 2, auditoría ronda 3) el gatillo tira de DOS cables
Bowden a la vez: los dos cables entran en un terminal doble (barril con 2 agujeros, Ø8) enganchado en el
agujero WIRE; las dos vainas apoyan en el mismo tope y pasan el espejo por un prensaestopas M16 con inserto
de 2 agujeros [ESTIMADO: buscar "Kabelverschraubung M16 Mehrfachdichteinsatz 2 × 6 mm"]. Tiro ≈ 2 × resorte."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y, prism_xz  # noqa: E402
import _ctl as U  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-CTL-14", name="gatillo", desc="Gatillo del Bowden de liberación (Al 6061 6 mm)",
    material="Al 6061-T6", process="torneada", qty=1, frame="bucket", group="ele",
    load_case="Apriete de la mano 100 N [SUPUESTO]", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)
Y0, Y1 = 33.5, 39.5          # al lado del mango superior (y 25–33)
PIV = (12.0, 128.0)          # pivote (x, z) local
WIRE = (12.0, 108.0)         # enganche del cable (a 20 mm del pivote)
ANG = 32.0                   # recorrido angular del gatillo [SUPUESTO]


def build_local(p):
    poly = [(8.0, 132.0), (16.0, 132.0), (26.0, 104.0), (18.0, 100.0), (8.0, 112.0)]
    s = prism_xz(poly, Y0, Y1)
    s = s - cyl_y(2.1, Y0 - 1, Y1 + 1, x=PIV[0], z=PIV[1]) - cyl_y(1.6, Y0 - 1, Y1 + 1, x=WIRE[0], z=WIRE[1])
    return s


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    th = -p.CTL_bkt_travel if bucket else 0.0
    x, y, z = p.CTL_axis
    return [Pos(x, y, z) * Rot(0, th, 0) * Pos(-x, -y, -z)]


def checks(p, part):
    r = math.hypot(WIRE[0] - PIV[0], WIRE[1] - PIV[1])
    travel = 2 * r * math.sin(math.radians(ANG / 2))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("recorrido del cable con el gatillo apretado [mm]", travel, RL.need(p) + 3.0, ">="),
            ("separación del mango superior (y) [mm]", Y0 - 33.0, 0.3, ">=")]
