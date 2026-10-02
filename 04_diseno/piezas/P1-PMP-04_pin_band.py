"""P1-PMP-04 — Anillo retén del pasador de corte (AISI 316 torneado). Marco JET.

Manguito Ø D_hub × pared pmp_band_t, deslizante (H7/g6 + Loctite 641) sobre el asiento Ø 2·pmp_land_r
de la popa del cubo del impulsor; tapa los extremos de los 2 semipasadores de corte (P1-PMP-05). Lo traban
2 tornillos M3 A4 avellanados (ISO 10642) en ±Z. Para cambiar los semipasadores: sacar tobera y estator por
popa (P1-PMP-08), quitar los M3, deslizar el anillo hacia popa (pasa sobre el DIN 471 de popa y su arandela)
y botar cada semipasador con un botador Ø3 corto desde el lado opuesto; el impulsor queda en el eje.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _pmp_geom import ring_x  # noqa: E402
from cadlib import cyl_z, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-04", name="pin_band",
            desc="Anillo retén 316 que tapa los extremos del pasador de corte",
            material="AISI 316", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Centrífuga a n máx.; retención del pasador", allow={"P1-PMP-03": 30.0})


def build(p):
    R, r = p.D_hub / 2, p.pmp_land_r
    b = ring_x(R, r, p.pmp_band_X0, p.L_imp)
    for z0, z1 in ((r - 1, R + 1), (-R - 1, -r + 1)):
        b = b - cyl_z(1.7, z0, z1, x=p.pmp_pin_X)
    return b


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø exterior = D_hub (enrasado con el cubo)", 1.0 if has_radius(part, p.D_hub / 2) else 0.0, 1.0, "="),
        ("cubre el pasador: X0 ≤ pin_X − d", p.pmp_band_X0, p.pmp_pin_X - p.pmp_pin_d, "<="),
        ("cubre el pasador: X1 ≥ pin_X + d", p.L_imp, p.pmp_pin_X + p.pmp_pin_d, ">="),
        ("pared ≥ 2,5 mm (M3 avellanado)", p.pmp_band_t, 2.5, ">="),
    ]
