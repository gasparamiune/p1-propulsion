"""P1-INT-04 — Tapa de la chimenea de inspección de la toma (PETG impresa, por encima de la flotación).

Marco BOTE (apoya sobre la brida de la chimenea de P1-INT-01 a z = toma_chim_top). Disco con ranura de
O-ring de cara en la cara inferior (se imprime BOCA ABAJO: ranura sobre la cama, fondo liso — R05) y
4 × Ø6,4 para M6 A4 con arandela ancha (perillas M6 para abrir sin herramientas). Por la chimenea se
sacan algas de la rejilla, del eje y del cubo del impulsor sin desarmar (R10a §7), con el sistema
desarmado. En marcha la tapa ve la presión de recuperación de la toma y en punto fijo succión: tiene
que sellar en ambos sentidos (si entra aire la bomba se desceba).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402

from cadlib import cyl_z  # noqa: E402

META = dict(id="P1-INT-04", name="tapa_inspeccion",
            desc="Tapa PETG Ø160 × 10 de la chimenea de inspección, O-ring de cara, 4 × M6",
            material="PETG", process="impresa", qty=1, frame="boat", group="jet",
            load_case="Presión interna de la toma (succión de cierre / recuperación a 30 km/h) sobre Ø de la junta",
            print_rot=(180, 0, 0), solid_frac=1.0,
            orientation="Boca abajo (ranura del O-ring sobre la cama), 100 % relleno",
            allow={"P1-INT-01": 1.0})


def oring_r(p):
    """Radio medio de la ranura: centrada entre la boca y los agujeros."""
    return 0.5 * (p.toma_chim_id / 2 + p.toma_chim_bc / 2 - (6 + p.bolt_clr) / 2)


def build(p):
    z0 = p.toma_chim_top
    xc = p.toma_chim_x
    R = p.toma_chim_fl_od / 2
    c = cyl_z(R, z0, z0 + p.toma_cover_t, x=xc)
    rm, w = oring_r(p), p.toma_gl_width
    c = c - (cyl_z(rm + w / 2, z0 - 1, z0 + p.toma_gl_depth, x=xc) - cyl_z(rm - w / 2, z0 - 2, z0 + p.toma_gl_depth + 1, x=xc))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        c = c - cyl_z((6 + p.bolt_clr) / 2, z0 - 1, z0 + p.toma_cover_t + 1,
                      x=xc + p.toma_chim_bc / 2 * math.cos(a), y=p.toma_chim_bc / 2 * math.sin(a))
    return c


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    rm, w = oring_r(p), p.toma_gl_width
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("O-ring: profundidad = cs·(1 − apriete) [mm]", p.toma_gl_depth, p.oring_cs * (1 - p.oring_sq), "="),
        ("O-ring: labio interior a la boca [mm]", rm - w / 2 - p.toma_chim_id / 2, 2.5, ">="),
        ("O-ring: labio exterior al agujero M6 [mm]", p.toma_chim_bc / 2 - (6 + p.bolt_clr) / 2 - (rm + w / 2), 2.5, ">="),
        ("espesor ≥ pared mínima [mm]", p.toma_cover_t, p.wall, ">="),
        ("tapa sobre la flotación estática [mm]", p.toma_chim_top - p.toma_draft, 50.0, ">="),
    ]
