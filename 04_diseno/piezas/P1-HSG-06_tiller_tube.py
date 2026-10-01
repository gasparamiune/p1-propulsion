"""P1-HSG-06 — Tubo de caña Al 6061-T6 Ø30×3 (comprado, cortado a largo)."""
import importlib.util, math, os
from cadlib import *

META = dict(id="P1-HSG-06", name="tiller_tube", desc="Tubo de caña Al 6061-T6 Ø30×3 × 550 mm",
            material="Al 6061-T6", process="comprada", qty=1, frame="unit",
            load_case="LC7", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")
LEN = 550.0


AFT = 50.0      # largo del tubo hacia popa del centro de la abrazadera trasera


def _tc():
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("tc", os.path.join(here, "P1-HSG-04_tiller_clamp.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build(p):
    """Tubo recto a lo largo de −u (paralelo al eje de hélice), apoyado en las abrazaderas.
    En marcha sube 25° sobre la horizontal hacia proa."""
    tc = _tc()
    u_c, v_c, w_c = tc.tiller_axis(p)
    r = p.tiller_tube_od / 2
    u_aft = 85.0 + AFT
    return Pos(0, w_c, v_c) * (cyl_x(r, u_aft - LEN, u_aft) - cyl_x(r - 3, u_aft - LEN - 1, u_aft + 1))


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
