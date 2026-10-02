"""P1-PMP-05 — Semipasadores de corte (fusible mecánico) Al 6061-T6, Ø sz.mech.shear_pin.d_mm. Marco JET.

DOS piezas iguales (qty 2 por juego), una desde +Y y otra desde −Y, en el agujero transversal Ø pmp_pin_hole
del cubo del impulsor y del eje (X = pmp_pin_X, eje Y, lo hace el grupo TREN); se tocan en el centro del eje.
Cada una cruza una vez la superficie del eje: 2 secciones de corte a r = d_eje/2 → el mismo par de corte
T_cut que el pasador pasante de sizing (R12 §7.6; sizing.mech.shear_pin). Largo = r del asiento − 0,5:
los extremos quedan 0,5 mm bajo el anillo retén P1-PMP-04.
Por qué partido (auditoría Pass 3 H1): un pasador pasante de 2·r_asiento (59 mm) no entra en el anillo libre
de ~36 mm entre el cubo y el anillo de desgaste; cada semipasador sí, con el impulsor en el eje y el tren
montado. Cambio: sacar tobera y estator por popa (P1-PMP-08), deslizar el anillo retén a popa, empujar un
semipasador con un botador corto (≤ 33 mm) desde el lado opuesto para expulsar el otro, y repetir.
Repuestos: pmp_pin_spares_sets juegos (2 piezas c/u) del mismo lote que la probeta P1.9.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Rot  # noqa: E402
from cadlib import cyl_y  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-05", name="shear_pin",
            desc="2 semipasadores de corte Al 6061-T6 (fusible de par del impulsor, cambiables en el eje)",
            material="Al 6061-T6", process="torneada", qty=2, frame="jet", group="jet",
            load_case="Par del controlador (no corta); corta a T_cut (piedra)",
            allow={"P1-PMP-03": 5.0})


def build(p):
    return cyl_y(p.pmp_pin_d / 2, 0.0, p.pmp_pin_half_len, x=p.pmp_pin_X)


def placements(p, steer=0.0, bucket=0):
    # +Y y su simétrico en −Y (giro de 180° alrededor de X)
    return [loc_jet(p), loc_jet(p) * Rot(180, 0, 0)]


def checks(p, part):
    bb = part.bounding_box()
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø pasador = sizing.mech.shear_pin.d_mm", bb.max.X - bb.min.X, p.sz["mech"]["shear_pin"]["d_mm"], "="),
        ("extremos bajo el anillo retén [mm]", p.pmp_land_r - bb.max.Y, 0.3, ">="),
        ("cruza la superficie del eje con ≥ 1 d en el cubo [mm]", bb.max.Y - p.shaft_d / 2, p.pmp_pin_d, ">="),
        ("juego en el agujero [mm]", p.pmp_pin_hole - p.pmp_pin_d, 0.05, "="),
        ("entra en el anillo libre cubo ↔ anillo de desgaste (+3 mm de pinza) [mm]",
         p.pmp_pin_half_len + 3.0, p.D_bore / 2 - p.pmp_land_r, "<="),
        ("T_corte / T_máx controlador ≥ 1,5 (R12 §7.6)", p.pmp_pin_T_cut / p.sz["mech"]["T_max_Nm"], 1.5, ">="),
    ]
