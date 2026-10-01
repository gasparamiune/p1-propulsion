"""P1-PMP-05 — Pasador de corte (fusible mecánico) Al 6061-T6, Ø sz.mech.shear_pin.d_mm. Marco JET.

Atraviesa el cubo del impulsor y el eje (agujero del eje Ø pmp_pin_hole en X = pmp_pin_X, eje Y,
lo hace el grupo TREN). Corte doble a T_cut (R12 §7.6; sizing.mech.shear_pin). Llevar 3 de repuesto.
Largo = Ø del asiento − 1 mm: los extremos quedan 0,5 mm bajo el anillo retén P1-PMP-04.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cadlib import cyl_y  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-05", name="shear_pin",
            desc="Pasador de corte Al 6061-T6 (fusible de par del impulsor)",
            material="Al 6061-T6", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Par del controlador (no corta); corta a T_cut (piedra)",
            allow={"P1-PMP-03": 60.0})


def build(p):
    L = p.pmp_pin_len
    return cyl_y(p.pmp_pin_d / 2, -L / 2, L / 2, x=p.pmp_pin_X)


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    bb = part.bounding_box()
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø pasador = sizing.mech.shear_pin.d_mm", bb.max.X - bb.min.X, p.sz["mech"]["shear_pin"]["d_mm"], "="),
        ("extremos bajo el anillo retén [mm]", p.pmp_land_r - bb.max.Y, 0.3, ">="),
        ("juego en el agujero [mm]", p.pmp_pin_hole - p.pmp_pin_d, 0.05, "="),
        ("T_corte / T_máx controlador ≥ 1,5 (R12 §7.6)", p.pmp_pin_T_cut / p.sz["mech"]["T_max_Nm"], 1.5, ">="),
    ]
