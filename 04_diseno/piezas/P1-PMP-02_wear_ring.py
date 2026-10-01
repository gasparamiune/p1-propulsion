"""P1-PMP-02 — Anillo de desgaste (AISI 316 torneado). Marco JET.

Ø interior D_bore (= D + 2·tip_clr), Ø exterior pmp_D_seat (prensado H7/p6 + Loctite 648 en la
carcasa P1-PMP-01), de X_ring0 a X_ring0 + L_ring; apoya adelante contra el escalón de la carcasa y
atrás lo empuja la camisa del estator. Anti-rotación: ranura frontal 4,1 × 4 arriba (+Z) que
engancha un pasador Ø4 A4 prensado en el escalón de la carcasa. R10b H15: la holgura de punta solo
se mantiene con anillo metálico torneado; tornear el Ø interior DESPUÉS de prensar (mismo montaje)
para la concentricidad declarada (TIR ≤ pmp_ring_TIR) y medir la holgura con galgas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _pmp_geom import ring_x  # noqa: E402
from cadlib import box, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-02", name="wear_ring",
            desc="Anillo de desgaste 316 torneado, prensado en la carcasa; holgura de punta tip_clr",
            material="AISI 316", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Presión de la bomba (apoyado en la carcasa); roce de piedras",
            allow={"P1-PMP-01": 20.0, "P1-PMP-06": 5.0})


def build(p):
    R0, Ri = p.pmp_D_seat / 2, p.D_bore / 2
    r = ring_x(R0, Ri, p.X_ring0, p.pmp_ring_X1)
    w = p.pmp_ring_pin_d / 2 + 0.05
    r = r - box(p.X_ring0 - 1, p.X_ring0 + 4.0, -w, w, Ri - 1, R0 + 1)
    return r


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    bb = part.bounding_box()
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø interior = D_bore", 1.0 if has_radius(part, p.D_bore / 2) else 0.0, 1.0, "="),
        ("Ø exterior = asiento de la carcasa", 1.0 if has_radius(part, p.pmp_D_seat / 2) else 0.0, 1.0, "="),
        ("largo = L_ring [mm]", bb.max.X - bb.min.X, p.L_ring, "="),
        ("holgura de punta (D_bore − D)/2 [mm]", (p.D_bore - p.D) / 2, p.tip_clr, "="),
        ("cubre el impulsor: X_ring0 ≤ 0", p.X_ring0, 0.0, "<="),
        ("cubre el impulsor: fin ≥ L_imp", p.pmp_ring_X1, p.L_imp, ">="),
        ("pared ≥ 3,2 mm", p.pmp_ring_t, 3.2, ">="),
        ("concentricidad declarada (TIR) [mm]", p.pmp_ring_TIR, 0.05, "<="),
        ("centrado en el eje (bbox Y) [mm]", abs(bb.max.Y + bb.min.Y) / 2, 0.01, "<="),
    ]
