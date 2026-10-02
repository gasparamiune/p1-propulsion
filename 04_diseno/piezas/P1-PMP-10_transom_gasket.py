"""P1-PMP-10 — Junta de espejo NBR 2 mm (cortada de plancha) entre el espejo y la placa P1-PMP-09.
Marco BOTE, x ∈ [−pmp_gasket_t, 0]. Agujero = transom_hole_d. Montar con sellador
de poliuretano (p. ej. Sikaflex 291 [ESTIMADO: buscar ficha]) además de la junta. 6 agujeros de bulón
(los de P1-PMP-09, pmp_tp_bolt_ang).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402
from cadlib import prism_yz, cyl_x  # noqa: E402

import importlib.util  # noqa: E402
_s = importlib.util.spec_from_file_location("_tp", str(Path(__file__).resolve().parent / "P1-PMP-09_transom_plate.py"))
_tp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_tp)

META = dict(id="P1-PMP-10", name="transom_gasket",
            desc="Junta NBR 2 mm del espejo (bajo la placa P1-PMP-09)",
            material="NBR", process="comprada", qty=1, frame="boat", group="jet",
            load_case="Compresión de los 6 × M6", allow={"P1-PMP-09": 5.0})


def build(p):
    g = prism_yz(_tp.outline(p, p.pmp_tp_R), -p.pmp_gasket_t, 0.0)
    g = g - cyl_x(p.transom_hole_d / 2, -5, 5, y=0.0, z=p.z_noz)
    for y, z in _tp.bolt_yz(p):
        g = g - cyl_x((p.pmp_tp_bolt + p.bolt_clr) / 2, -5, 5, y=y, z=z)
    return g


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    bb = part.bounding_box()
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("espesor [mm]", bb.max.X - bb.min.X, p.pmp_gasket_t, "="),
        ("agujero = transom_hole_d", p.transom_hole_d, p.raw["transom_hole_d"], "="),
        (f"ancho de junta bajo el agujero (z) [mm] — si falla: subir waterjet.axis_height_m a ≥ "
         f"{p.h_axis / 1000 + max(0.0, 8.0 - (p.z_noz - p.transom_hole_d / 2 - p.pmp_tp_zmin)) / 1000:.3f} m",
         p.z_noz - p.transom_hole_d / 2 - p.pmp_tp_zmin, 8.0, ">="),
        ("agujeros de bulón = los de la placa P1-PMP-09", len(_tp.bolt_yz(p)), len(p.pmp_tp_bolt_ang), "="),
    ]
