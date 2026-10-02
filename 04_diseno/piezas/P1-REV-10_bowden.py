"""P1-REV-10 — Extremo del Bowden inox de liberación de cada émbolo (COMPRADO, ×2: regulador M6 + vaina
Ø4,5–5 con camisa de PTFE + cable inox Ø1,5 con terminal de horquilla al pomo) [ESTIMADO: buscar "Bowden
Edelstahl PTFE 1,5 mm Stellschraube M6"]. Las dos vainas pasan el espejo por el prensaestopas M16 del
Bowden (P1-CTL-05) con inserto de 2 agujeros (B-GLINS) y hacen un bucle libre hasta la boquilla (giran con
la dirección); en la consola los dos cables entran al barril doble del gatillo P1-CTL-14. Desde la placa de
tope la vaina sale hacia la oreja opuesta y curva hacia arriba (R ≥ 30 mm) antes de llegar a ella: el tramo
recto modelado (26 mm) es solo el extremo."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-10", name="bowden_embolo", desc="Bowden inox de liberación de cada émbolo (extremo, comprado; ×2)",
    material="AISI 316", process="comprada", qty=2, frame="steer", group="jet",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=60.0,   # [ESTIMADO: 2,5 m]
)


def build(p):
    lx, lz = RL.lock_xz(p)
    yp = RL.plate_y(p)
    s = cyl_y(2.9, yp - 4.0, yp + 0.01, x=lx, z=lz)                 # regulador M6 en la placa (modelado Ø5,8)
    s = s + cyl_y(5.0, yp - 14.0, yp - 3.99, x=lx, z=lz)             # tuerca + casquillo
    s = s + cyl_y(2.5, yp - 40.0, yp - 13.99, x=lx, z=lz)            # vaina Ø5
    s = s + cyl_y(0.75, yp - 0.01, RL.knob_end_y(p) - 4.0, x=lx, z=lz)   # cable Ø1,5
    s = s + cyl_y(3.0, RL.knob_end_y(p) - 4.01, RL.knob_end_y(p), x=lx, z=lz)   # terminal al pomo
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    from build123d import Pos, Rot
    L = [loc_steer(p, steer)]
    if p.REV_n_locks > 1:                       # gemelo del lado −Y (2.º émbolo; y → −y alrededor de la traba)
        L.append(loc_steer(p, steer) * RL.mirror_loc(p))
    return L


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "=")]
