"""P1-DRV-06 — Tapa delantera de rodamientos, Al 6082 torneada, 4 × M5 A4 al alojamiento de P1-DRV-03.
Aprieta el aro exterior del 7204 de proa: es el camino del EMPUJE hacia proa (bollard) a los M5 → soporte.
Agujero central Ø34: la KM4 gira adentro (laberinto de 1 mm); grasa + anillo V (VA-30 [ESTIMADO]) del lado
del acople (seco)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cadlib import cyl_x  # noqa: E402
from _drv_geom import cyl_s, polar_yz  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-06", name="bearing_cover", desc="Tapa delantera Al de rodamientos (4×M5), toma el empuje hacia proa",
            material="Al 5052/6082", process="torneada", qty=1, frame="jet", group="drive",
            load_case="Empuje Fa a punto fijo hacia proa: flexión de la tapa entre el aro y los M5",
            print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            allow={"P1-DRV-03": 5.0, "P1-DRV-04": 5.0})

HOLE = 34.0     # [SUPUESTO: KM4 Ø32 + 2]


def build(p):
    s0, s1 = p.drv_S_brgB, p.drv_S_brgB + p.drv_cover_t
    part = cyl_s(p.drv_hsg_od / 2, s0, s1) - cyl_s(HOLE / 2, s0 - 1, s1 + 1)
    for k in range(4):
        y, z = polar_yz(p.drv_cover_bc / 2, 45 + 90 * k)
        part = part - cyl_x((p.drv_cover_bolt + p.bolt_clr) / 2, -s1 - 1, -s0 + 1, y=y, z=z)
    return part


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    b = p.drv_bearing
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("la tapa apoya en el aro exterior: Ø agujero < D − 2·(D − Da_max)/2… (Ø34 ≤ Da_max) [mm]", HOLE, b["Da_max"], "<="),
            ("agujero M5 fuera del Ø47 del alojamiento (borde) [mm]",
             p.drv_cover_bc / 2 - (p.drv_cover_bolt + p.bolt_clr) / 2 - b["D"] / 2, 1.0, ">="),
            ("agujero M5 dentro de la tapa (borde exterior) [mm]",
             p.drv_hsg_od / 2 - p.drv_cover_bc / 2 - (p.drv_cover_bolt + p.bolt_clr) / 2, 1.5, ">=")]
