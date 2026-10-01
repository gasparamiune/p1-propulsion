"""P1-ELE-02 — Capota antisalpicaduras del controlador (PETG impresa, se imprime con el techo sobre la
cama). Cubre el ESC IP65 por arriba y los costados, lo aprieta contra P1-ELE-01 a través de una
dos tiras de EPDM celular (ele_pad_t × ele_pad_w) sobre los bordes largos (la carga va cerca de las paredes: el techo casi no flexa) con 4 × M5 A4 (nervios verticales de altura completa: imprimibles sin
soportes). Ranuras en ambos extremos, abiertas hacia abajo, para los cables de 70 mm² (DC y fases) y las
mangueras Ø8 de refrigeración: el agua que salpica escurre hacia afuera; el ESC queda IP65 + techo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos  # noqa: E402
from cadlib import box, cyl_z  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("_ele01", str(Path(__file__).resolve().parent / "P1-ELE-01_esc_stand.py"))
_ele01 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ele01)

META = dict(id="P1-ELE-02", name="esc_hood", desc="Capota antisalpicaduras PETG del controlador (4 × M5 a la base)",
            material="PETG", process="impresa", qty=1, frame="boat", group="ele",
            load_case="Apriete de la almohadilla EPDM (4 × M5) y 3 g vertical del ESC hacia arriba (golpe de ola)",
            print_rot=(180, 0, 0), solid_frac=0.8,
            orientation="Techo sobre la cama, paredes y nervios hacia arriba (sin soportes).",
            allow={"P1-ELE-04": 2.0, "P1-ELE-01": 2.0})

TOP_T = 3.2


def build(p):
    Lo, Wo = p.ele_out
    L, W, H = p.ele_esc_size
    c, w = p.ele_clr, p.ele_wall
    hc = H + p.ele_pad_t * (1 - p.ele_pad_comp)                  # tiras de EPDM celular comprimidas
    part = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, hc + TOP_T)
    part = part - box(-L / 2 - c, L / 2 + c, -W / 2 - c, W / 2 + c, -1, hc)
    sw, sh = p.ele_hood_slot
    for sx in (-1, 1):
        part = part - box(sx * Lo / 2 - 5 if sx > 0 else -Lo / 2 - 5, Lo / 2 + 5 if sx > 0 else -Lo / 2 + 5,
                          -sw / 2, sw / 2, -1, sh)
    for (x, y) in _ele01.rib_pts(p):
        sy = 1 if y > 0 else -1
        y0, y1 = (Wo / 2 - 0.5, Wo / 2 + _ele01.RIB_D) if sy > 0 else (-Wo / 2 - _ele01.RIB_D, -Wo / 2 + 0.5)
        part = part + box(x - _ele01.RIB_W / 2, x + _ele01.RIB_W / 2, y0, y1, 0, hc + TOP_T)
        part = part - cyl_z(2.75, -1, hc + TOP_T + 1, x=x, y=y)
    return part


def placements(p, steer=0.0, bucket=0):
    x, y, z = p.ele_pos
    return [Pos(x, y, z + p.ele_raise)]


def checks(p, part):
    L, W, H = p.ele_esc_size
    sw, sh = p.ele_hood_slot
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("holgura ESC ↔ capota por lado [mm]", p.ele_clr, 0.4, ">="),
            ("ranura de cables/mangueras ≤ ancho del ESC [mm]", sw, W - 10.0, "<="),
            ("ranura de cables: alto ≥ 2 × Ø cable 70 mm² (≈ 15 [ESTIMADO]) [mm]", sh, 30.0, ">="),
            ("techo ≥ min_wall [mm]", TOP_T, p.wall, ">=")]
