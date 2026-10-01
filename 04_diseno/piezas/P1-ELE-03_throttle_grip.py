"""P1-ELE-03 — Puño giratorio del acelerador (sobre el extremo del tubo de caña Ø30).
Imán de neodimio Ø10×3 diametral en el cubo; retorno al centro por resortes; topes ±30°.
Centro = motor parado (zona muerta en firmware); girar hacia uno u otro lado = avante/atrás."""
import importlib.util, math, os
from cadlib import *

META = dict(
    id="P1-ELE-03", name="throttle_grip", desc="Puño giratorio del acelerador (imán)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="Torsión de mano (~5 N·m), golpes", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Eje vertical (Z): anillos de capa en la dirección del torque.",
)
L_GRIP = 110.0


def _tm():
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("tm", os.path.join(here, "P1-HSG-04_tiller_mount.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tiller_loc(p, along):
    from build123d import Pos, Rot
    tm = _tm()
    u_c, v_c = tm.tiller_origin(p)
    du, dv = tm.tiller_dir(p)
    beta = math.degrees(math.atan2(dv, du))
    return Pos(u_c, tm.W_OFF, v_c) * Rot(0, -beta, 0) * Pos(along, 0, 0) * Rot(0, 90, 0)


def build(p):
    ri = (p.tiller_tube_od + 0.4) / 2
    g = cyl_z(ri + 6, 0, L_GRIP) - cyl_z(ri, -1, L_GRIP + 1)
    g = g + cyl_z(ri + 9, 0, 12) - cyl_z(ri, -1, 13)            # brida con imán
    g = g - box(ri + 3, ri + 9.5, -5.2, 5.2, 3, 9)                  # bolsillo del imán 10×3
    g = g - box(-ri - 9.5, -ri - 3, -2, 2, -1, 12.5)                # ranura de tope
    return g


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    from importlib import import_module
    tube_len = 700.0
    return [loc_unit(p, steer, tilt) * tiller_loc(p, tube_len - 18 - L_GRIP - 2)]


def checks(p, part):
    return [("holgura diametral puño–tubo [mm]", 0.4, 0.3, ">=")]
