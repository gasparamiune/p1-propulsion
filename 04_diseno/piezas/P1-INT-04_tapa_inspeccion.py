"""P1-INT-04 — Tapa de la chimenea de inspección de la toma (PETG impresa, por encima de la flotación).

Marco BOTE (apoya sobre la brida de la chimenea de P1-INT-01 a z = toma_chim_top). Disco con ranura de
O-ring de cara en la cara inferior (se imprime BOCA ABAJO: ranura sobre la cama, fondo liso — R05) y
4 × Ø6,4 para M6 A4 con arandela ancha (perillas M6 para abrir sin herramientas). Por la chimenea se
sacan algas de la rejilla, del eje y del cubo del impulsor sin desarmar (R10a §7), con el sistema
desarmado. En marcha la tapa ve la presión de recuperación de la toma y en punto fijo succión: tiene
que sellar en ambos sentidos (si entra aire la bomba se desceba).
PURGA DE AIRE: con el bote quieto la chimenea guarda ~0,5 L de aire bajo la tapa, que la bomba
aspiraría al arrancar. Tornillo de purga M6 × 12 A4 con arandela de estanqueidad (tipo Dowty / cobre-
NBR) en un resalte de la cara superior, roscado en una tuerca ISO 4032 A4 cautiva en un hexágono desde
abajo (la presión interna la aprieta contra su asiento). Antes de arrancar: aflojar hasta que salga
agua, cerrar. Va en el punto más alto bajo la tapa, dentro del O-ring y sobre la boca de la chimenea.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402

from cadlib import NUT_AF, NUT_M, cyl_z, hex_prism_z  # noqa: E402

PURGE_R = 32.0       # radio de la purga desde el eje de la chimenea [CALCULADO: dentro de la boca Ø100 y lejos del centro]
BOSS_D, BOSS_H = 26.0, 6.0   # resalte que repone el espesor sobre el hexágono [CALCULADO: structural_toma]

META = dict(id="P1-INT-04", name="tapa_inspeccion",
            desc="Tapa PETG Ø160 × 10 de la chimenea de inspección, O-ring de cara, 4 × M6",
            material="PETG", process="impresa", qty=1, frame="boat", group="jet",
            load_case="Presión interna de la toma (succión de cierre / recuperación a 30 km/h) sobre Ø de la junta",
            print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="Cara de la ranura del O-ring y del hexágono de la tuerca sobre la cama (fondos lisos), resalte arriba, 100 % relleno",
            allow={"P1-INT-01": 5.0})


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
    # purga: resalte arriba, hexágono de tuerca M6 desde abajo, agujero Ø6,4
    xp = xc + PURGE_R
    zt = z0 + p.toma_cover_t
    c = c + cyl_z(BOSS_D / 2, zt - 0.5, zt + BOSS_H, x=xp)
    c = c - hex_prism_z(NUT_AF[6] + 0.3, z0 - 1, z0 + NUT_M[6] + 0.2, x=xp)
    c = c - cyl_z((6 + p.bolt_clr) / 2, z0 - 1, zt + BOSS_H + 1, x=xp)
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
        ("purga dentro de la boca de la chimenea (sale el aire) [mm]", p.toma_chim_id / 2 - (PURGE_R + (NUT_AF[6] + 0.3) / math.sqrt(3)), 2.0, ">="),
        ("purga dentro del O-ring [mm]", (rm - w / 2) - (PURGE_R + BOSS_D / 2), 0.0, ">="),
        ("PETG sobre el hexágono de la tuerca de purga [mm]", p.toma_cover_t + BOSS_H - NUT_M[6] - 0.2, 10.0, ">="),
    ]
