"""P1-CTL-12 — Pernos deslizantes de enclavamiento acelerador ↔ bucket (×2), AISI 316 Ø6 × 13 con
puntas a 45° (las ranuras/muescas de las palancas tienen chaflán 1 × 45° para empujarlos).

Largo = placa 6 + 2 luces de 2 + profundidad de muesca 3: siempre uno de los extremos está en una
muesca/ranura. Ubicación según el estado del bucket (arriba: perno 2 en la muesca del bucket; abajo:
en la ranura del acelerador)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-12", name="perno_enclav", desc="Perno de enclavamiento Ø6 × 13 (316)",
    material="AISI 316", process="torneada", qty=2, frame="bucket", group="ele",
    load_case="Corte: 100 N en el pomo del bucket contra el enclavamiento", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—",
)
L = 13.0


def build(p):
    return cyl_y(p.CTL_ilock_d / 2, 0.0, L)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    out = []
    for k in (2, 3):
        a = math.radians(U.PIN_PHI[k])
        x, z = p.CTL_ilock_r * math.cos(a), p.CTL_ilock_r * math.sin(a)
        in_b = (k == 2 and not bucket)                       # perno 2 en la muesca del bucket (arriba)
        y0 = (U.Y_MID[0] - 2.0) if in_b else (U.Y_THR[1] - p.CTL_ilock_depth)
        out.append(U.unit_loc(p) * Pos(x, y0, z))
    return out


def checks(p, part):
    need = (U.Y_MID[1] - U.Y_MID[0]) + 2 * 2.0 + p.CTL_ilock_depth
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("largo = placa + 2 luces + muesca [mm]", L, need, "=")]
