"""P1-BAT-01 — Batería de la selección de sizing (hoy 2 × LiTime 36 V 60 Ah Golf Cart en paralelo,
532 × 207 × 215 mm c/u [ESTIMADO: research/R11 §3.2, medir]). Comprada; modelo de referencia para
verificar que entra en el casco (lado a lado, a proa del controlador) y fijar su posición en
inputs.yaml masses.battery. La masa está en masses.battery (no suma a la unidad de jet)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos  # noqa: E402
from cadlib import box  # noqa: E402

META = dict(id="P1-BAT-01", name="bateria", desc="Batería LFP de la selección (modelo de referencia, una por rama)",
            material="referencia", process="comprada", qty=2, frame="boat", group="bat",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=19800.0)

GAP = 12.0          # [SUPUESTO: luz entre baterías y a la base del controlador]


def _bat(p):
    sel = p.sz["selection"]["battery"]
    b = p.inp["battery"]["options"][sel]
    return b, tuple(b.get("unit_size_mm", (532, 207, 215))), int(b.get("parallel", 1))


def build(p):
    b, (L, W, H), n = _bat(p)
    META["qty"] = n
    META["mass_g"] = b["mass_kg"] / n * 1000
    return box(-L / 2, L / 2, -W / 2, W / 2, 0, H)


def _x_center(p):
    _, (L, W, H), n = _bat(p)
    x_esc_fwd = p.ele_pos[0] + p.ele_out[0] / 2          # cara de proa de la base del controlador
    return x_esc_fwd + GAP + L / 2


def placements(p, steer=0.0, bucket=0):
    _, (L, W, H), n = _bat(p)
    xc = _x_center(p)
    if n == 1:
        return [Pos(xc, 0, p.floor_z)]
    return [Pos(xc, s * (W / 2 + GAP / 2), p.floor_z) for s in (-1, 1)]


def checks(p, part):
    _, (L, W, H), n = _bat(p)
    xc = _x_center(p)
    x_m = p.inp["masses"]["items"]["battery"]["x_m"] * 1000
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("posición de la batería en inputs (masses.battery.x_m) = CAD [mm]", x_m, xc, "="),
            ("extremo de proa dentro del 75 % de la eslora (zona de fondo útil, no la proa lanzada) [mm]",
             xc + L / 2, 0.75 * p.inp["boat"]["loa_m"] * 1000, "<=")]
