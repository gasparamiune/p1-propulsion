"""P1-ELE-04 — Controlador de la selección de sizing (hoy Flipsky FSESC 75350 con caja de agua IP65,
200 × 94,6 × 50 mm, 2,0 kg — research/R11 §2.1). Comprado; modelo de referencia (caja) para verificar
interferencias con la base P1-ELE-01 y la capota P1-ELE-02."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos  # noqa: E402
from cadlib import box  # noqa: E402

META = dict(id="P1-ELE-04", name="esc", desc="Controlador VESC de la selección (FSESC 75350 con caja de agua)",
            material="referencia", process="comprada", qty=1, frame="boat", group="ele",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            mass_g=2000.0,   # [VERIFICADO: research/R11 §2.1 — 2000 g con caja]; se reemplaza por inputs en build()
            allow={"P1-ELE-01": 5.0, "P1-ELE-02": 5.0})


def build(p):
    META["mass_g"] = float(p.ele_esc_mass_kg) * 1000
    L, W, H = p.ele_esc_size
    return box(-L / 2, L / 2, -W / 2, W / 2, 0, H)


def placements(p, steer=0.0, bucket=0):
    x, y, z = p.ele_pos
    return [Pos(x, y, z + p.ele_raise)]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "=")]
