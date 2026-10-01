"""P1-PMP-07 — Buje lubricado por agua (2.º apoyo del eje) en el cubo del estator. Marco JET.

POM-C torneado [R05: bujes bajo agua en POM-C torneado] o Vesconite Hilube / iglidur de catálogo
(Ø20 no verificado: buscar). Ø int pmp_brg_id (juego en agua), Ø ext pmp_brg_od (prensado H7/s6 en
el cubo del estator, entra desde proa), largo pmp_bush_L, 4 ranuras axiales de agua: el agua entra
por la luz rotor–estator (alta presión) y sale por el agujero de la punta del cono de cola.
Velocidad periférica a n_máx: π·d·n ≈ 5 m/s → confirmar límite del material con el fabricante.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Rot  # noqa: E402
from _pmp_geom import ring_x  # noqa: E402
from cadlib import box, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-07", name="water_bushing",
            desc="Buje Ø20 lubricado por agua en el cubo del estator (2.º apoyo del eje)",
            material="POM-C", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Carga radial del eje (desbalance + hidráulica)", allow={"P1-PMP-06": 40.0})


def build(p):
    ro, ri = p.pmp_brg_od / 2, p.pmp_brg_id / 2
    b = ring_x(ro, ri, p.pmp_bush_X0, p.pmp_bush_X1)
    n, w, dep = p.pmp_brg_grooves
    g = box(p.pmp_bush_X0 - 1, p.pmp_bush_X1 + 1, -w / 2, w / 2, ri - 1, ri + dep)
    for k in range(n):
        b = b - Rot(360.0 * k / n + 45.0, 0, 0) * g
    return b


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    n_max = p.sz["mech"]["n_max_rpm"]
    v = math.pi * p.shaft_d / 1000 * n_max / 60
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø ext = alojamiento del estator", 1.0 if has_radius(part, p.pmp_brg_od / 2) else 0.0, 1.0, "="),
        ("juego diametral sobre el eje [mm]", p.pmp_brg_id - p.shaft_d, 0.20, "="),
        ("L/d ≥ 1,5", p.pmp_bush_L / p.shaft_d, 1.5, ">="),
        ("pared ≥ 3,2 mm", (p.pmp_brg_od - p.pmp_brg_id) / 2, 3.2, ">="),
        ("eje cubre todo el buje: X_aft ≥ X1", p.pmp_shaft_X_aft, p.pmp_bush_X1, ">="),
        ("velocidad periférica a n_máx [m/s] (info, confirmar material)", v, 8.0, "<="),
    ]
