"""P1-ELE-01 — Base elevada del controlador (PETG impresa).

Decisión (pedido del grupo principal): el controlador elegido trae caja de agua IP65 (FSESC 75350,
research/R11 §2.1) y su calor (sizing thermal P_loss_esc) se va por el circuito de agua → no hace falta
tapa-disipador. Una caja estanca con O-ring a su alrededor no entra en la cama de 210 mm (ESC de 200 mm +
prensaestopas + curvas de cable de 70 mm²) y sumaría juntas. Se usa: base elevada (esta pieza) que pone el
ESC a ele_raise sobre el piso, lejos del agua que corre por el piso, + capota antisalpicaduras P1-ELE-02
que lo aprieta contra la base con 4 × M5 (insertos térmicos: pieza seca, no sumergida).
Pedestal hueco (abierto abajo, nervios internos) con 4 orejas de anclaje M6 al piso (insertos/T-nuts en
el piso)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos  # noqa: E402
from cadlib import box, cyl_z, INSERT_HOLE, INSERT_LEN  # noqa: E402

META = dict(id="P1-ELE-01", name="esc_stand", desc="Base elevada PETG del controlador IP65 (4 × M6 al piso, 4 insertos M5 para la capota)",
            material="PETG", process="impresa", qty=1, frame="boat", group="ele",
            load_case="Peso del ESC + capota a 3 g vertical y 1 g lateral; tirón de cables",
            print_rot=(0, 0, 0), solid_frac=0.6,
            orientation="Base abierta sobre la cama; tablero arriba (puentes de 3,2 mm entre nervios, sin soportes).",
            allow={"P1-ELE-04": 5.0, "P1-ELE-02": 5.0})

RIB_X = 20.0      # centro de los nervios de abulonado desde el extremo
RIB_W = 20.0      # largo (x) del nervio
RIB_D = 12.0      # saliente (y) del nervio
EAR_X = 60.0      # orejas de anclaje al piso desde el extremo
EAR_D = 16.0
DECK_T = 4.0


def outer(p):
    return p.ele_out


def rib_pts(p):
    Lo, Wo = outer(p)
    return [(sx * (Lo / 2 - RIB_X), sy * (Wo / 2 + RIB_D / 2)) for sx in (-1, 1) for sy in (-1, 1)]


def ear_pts(p):
    Lo, Wo = outer(p)
    return [(sx * (Lo / 2 - EAR_X), sy * (Wo / 2 + EAR_D / 2 + 1.0)) for sx in (-1, 1) for sy in (-1, 1)]


def build(p):
    Lo, Wo = outer(p)
    w, h = p.ele_wall, p.ele_raise
    part = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, h)
    part = part - box(-Lo / 2 + w, Lo / 2 - w, -Wo / 2 + w, Wo / 2 - w, -1, h - DECK_T)
    # nervios internos (1 longitudinal + 3 transversales)
    part = part + box(-Lo / 2, Lo / 2, -w / 2, w / 2, 0, h)
    for x in (-Lo / 4, 0.0, Lo / 4):
        part = part + box(x - w / 2, x + w / 2, -Wo / 2, Wo / 2, 0, h)
    # nervios exteriores para la capota (insertos M5 arriba)
    for (x, y) in rib_pts(p):
        sy = 1 if y > 0 else -1
        y0, y1 = (Wo / 2 - 0.5, Wo / 2 + RIB_D) if sy > 0 else (-Wo / 2 - RIB_D, -Wo / 2 + 0.5)
        part = part + box(x - RIB_W / 2, x + RIB_W / 2, y0, y1, 0, h)
        part = part - cyl_z(INSERT_HOLE[5] / 2, h - INSERT_LEN[5] - 1.0, h + 1, x=x, y=y)
    # orejas de anclaje al piso (M6 pasante)
    for (x, y) in ear_pts(p):
        sy = 1 if y > 0 else -1
        y0, y1 = (Wo / 2 - 0.5, Wo / 2 + EAR_D + 2.0) if sy > 0 else (-Wo / 2 - EAR_D - 2.0, -Wo / 2 + 0.5)
        part = part + box(x - 11, x + 11, y0, y1, 0, 7.0)
        part = part - cyl_z(3.2, -1, 8, x=x, y=y)
    # drenaje del tablero (2 ranuras) para que no quede agua bajo el ESC
    for x in (-Lo / 8, Lo / 8):
        part = part - box(x - 15, x + 15, -Wo / 4 - 2, -Wo / 4 + 2, h - DECK_T - 1, h + 1)
    return part


def placements(p, steer=0.0, bucket=0):
    x, y, z = p.ele_pos
    return [Pos(x, y, z)]


def checks(p, part):
    Lo, Wo = outer(p)
    x, y, z = p.ele_pos
    L, W, H = p.ele_esc_size
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("fondo del ESC sobre el piso [mm]", p.ele_raise, 50.0, ">="),
            ("la base apoya el ESC completo (largo base − largo ESC) [mm]", Lo - L, 0.0, ">="),
            ("controlador refrigerado por agua (si no: volver a caja + disipador) [—]", float(p.ele_esc_water), 1.0, "="),
            ("dentro de la manga del casco a la altura del ESC [mm]", p.ele_hw_avail - (abs(y) + Wo / 2 + EAR_D + 2), 10.0, ">="),
            ("luz al motor: máx(separación en x, separación en y) [mm]",
             max((x - Lo / 2) - p.mot_x1, p.mot_x0 - (x + Lo / 2),
                 abs(y) - (Wo / 2 + EAR_D + 2) - p.motor_d / 2), 20.0, ">="),
            ("pared ≥ min_wall [mm]", p.ele_wall, p.wall, ">=")]
