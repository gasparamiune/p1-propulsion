"""P1-DRV-03 — Separador del puente (×2), AISI 316 torneado Ø12/Ø6.5: compresión por precarga + corte."""
from cadlib import *

META = dict(id="P1-DRV-03", name="bridge_spacer", desc="Separador Ø12/Ø6.5 (×2), 316",
            material="AISI 316", process="torneada", qty=2, frame="unit",
            load_case="Compresión por precarga del perno M6", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—")


def build(p):
    L = p.plate_u_fwd - p.bridge_u_aft
    return cyl_x(6, 0, L) - cyl_x(3.2, -1, L + 1)


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos
    from params import loc_unit
    L = loc_unit(p, steer, tilt)
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("br", os.path.join(os.path.dirname(__file__), "P1-HSG-02_bearing_bridge.py"))
    br = importlib.util.module_from_spec(spec); spec.loader.exec_module(br)
    return [L * Pos(p.bridge_u_aft, w, v) for v, w in br.spacer_points(p)]


def checks(p, part):
    return []
