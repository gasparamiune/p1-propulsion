"""P1-REV-09 — Soporte en L del Bowden de liberación del émbolo, Al 5083 4 mm (frame steer).

Atornillado (2 × M5 A4) a la cara interior de la oreja +Y de la boquilla, con la placa de tope frente
al pomo del émbolo P1-REV-04: la vaina del Bowden inox (P1-REV-10) apoya en la placa y el cable tira del
pomo hacia el eje de la boquilla. Al apretar el gatillo de la palanca del bucket (P1-CTL-14) el perno
sale del brazo del bucket; al soltarlo, el resorte del émbolo lo vuelve a meter (traba automática)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-09", name="soporte_bowden", desc="Soporte en L del Bowden de liberación (Al 5083 4 mm)",
    material="Al 5083", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Tiro del Bowden (resorte del émbolo + fricción) 60 N [ESTIMADO]", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="Chapa doblada",
)
DX_LEG = 22.0


def build(p):
    lx, lz = RL.lock_xz(p)
    y0 = RL.plate_y(p) - 4.0
    y1 = p.STE_ear_y0
    s = box(lx - DX_LEG - 4.0, lx - DX_LEG, y0, y1, lz - 8.0, lz + 8.0)                 # pata (a la oreja)
    s = s + box(lx - DX_LEG - 4.0, lx + 12.0, y0, y0 + 4.0, lz - 8.0, lz + 8.0)          # placa de tope
    s = s - cyl_y(3.25, y0 - 1, y0 + 5, x=lx, z=lz)                                     # regulador M6 del Bowden
    for dz in (-4.0, 4.0):
        pass
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import math
    lx, lz = RL.lock_xz(p)
    y0 = RL.plate_y(p) - 4.0
    zb = math.sqrt(max(p.STE_ro ** 2 - max(y0, 0.0) ** 2, 0.0))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("recorrido libre pomo ↔ placa − recorrido de liberación [mm]", (RL.knob_end_y(p) - RL.plate_y(p)) - RL.need(p), 2.0, ">="),
            ("recorrido de liberación ≤ carrera del émbolo − 1 [mm]", RL.need(p), p.REV_plunger_stroke - 1.0, "<="),
            ("pata fuera del pomo (X) [mm]", (DX_LEG) - 12.5, 3.0, ">="),
            ("soporte sobre el cuerpo de la boquilla [mm]", (lz - 8.0) - zb, 3.0, ">=")]
