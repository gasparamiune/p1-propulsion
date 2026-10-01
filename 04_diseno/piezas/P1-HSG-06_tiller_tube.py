"""P1-HSG-06 — Tubo de caña Al 6061-T6 Ø30×3 (comprado, cortado a largo)."""
import importlib.util, math, os
from cadlib import *

META = dict(id="P1-HSG-06", name="tiller_tube", desc="Tubo de caña Al 6061-T6 Ø30×3 × 700 mm",
            material="Al 6061-T6", process="comprada", qty=1, frame="unit",
            load_case="LC7", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")
LEN = 700.0


def _tm():
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("tm", os.path.join(here, "P1-HSG-04_tiller_mount.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build(p):
    tm = _tm()
    u_c, v_c = tm.tiller_origin(p)
    du, dv = tm.tiller_dir(p)
    beta = math.degrees(math.atan2(dv, du))
    r = p.tiller_tube_od / 2
    t = Pos(u_c, tm.W_OFF, v_c) * Rot(0, -beta, 0) * (cyl_x(r, -18, LEN - 18) - cyl_x(r - 3, -19, LEN))
    return t


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return []
