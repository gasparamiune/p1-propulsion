"""P1-PMP-11 — Buje de pivote de la boquilla (POM-C torneado; alt. iglidur con collar 8×12). Marco JET.

Uno en cada oreja de la placa de espejo P1-PMP-09 (qty 2): Ø ext pmp_lug_bush_od (prensado H7/s6),
Ø int pmp_lug_bush_id para el tornillo con hombro Ø steer_pin_d e8 de DIRECCIÓN; evita el contacto
316–Al (galvánica y desgaste). Largo = espesor de la oreja.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos, Rot, Cylinder, Align  # noqa: E402
from cadlib import has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-11", name="pivot_bushing",
            desc="Buje POM-C de pivote de la boquilla en las orejas de la placa de espejo (×2)",
            material="POM-C", process="torneada", qty=2, frame="jet", group="jet",
            load_case="F lateral de la boquilla / F del bucket (aplastamiento)", allow={"P1-PMP-09": 60.0})


def build(p):
    c = Align.CENTER
    L = p.pmp_lug_bush_L
    o = Pos(p.X_steer_pivot, 0, p.pmp_lug_z0) * Cylinder(p.pmp_lug_bush_od / 2, L, align=(c, c, Align.MIN))
    i = Pos(p.X_steer_pivot, 0, p.pmp_lug_z0 - 1) * Cylinder(p.pmp_lug_bush_id / 2, L + 2, align=(c, c, Align.MIN))
    return o - i


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p), loc_jet(p) * Pos(0, 0, -(p.pmp_lug_z0 + p.pmp_lug_z1))]


def checks(p, part):
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø int = hombro del perno + 0,1", p.pmp_lug_bush_id - p.steer_pin_d, 0.1, "="),
        ("Ø ext = alojamiento de la oreja", 1.0 if has_radius(part, p.pmp_lug_hole / 2) else 0.0, 1.0, "="),
        ("pared del buje ≥ 1,5 mm", (p.pmp_lug_bush_od - p.pmp_lug_bush_id) / 2, 1.5, ">="),
    ]
