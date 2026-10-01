"""P1-DRV-05 — Tuerca de fijación KM4 (M20×1) + arandela MB4: aprieta los aros interiores del par
7204 BEP contra el collar Ø25 del eje (precarga de fábrica del par apareado) y toma el empuje hacia popa
(reversa). Comprada. Modelo simplificado: MB4 1 mm + KM4 Ø32 × 7."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _drv_geom import tube_s  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-05", name="locknut_KM4", desc="Tuerca KM4 M20×1 + arandela MB4 (comprada)",
            material="Acero", process="comprada", qty=1, frame="jet", group="drive",
            load_case="Empuje en reversa (≤ Fa) y precarga", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—", mass_g=25.0,   # [ESTIMADO: params_tren.KM]
            allow={"P1-DRV-01": 5.0, "P1-DRV-04": 1.0})


def build(p):
    k = p.drv_km
    s0 = p.drv_S_brgB
    mb = tube_s(k["od"] / 2 - 1.0, k["d"] / 2, s0, s0 + k["mb_t"])
    nut = tube_s(k["od"] / 2, k["d"] / 2, s0 + k["mb_t"], s0 + k["mb_t"] + k["b"])
    return mb + nut


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    k = p.drv_km
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("tuerca pasa por el agujero de la tapa (holgura radial) [mm]", (34.0 - k["od"]) / 2, 0.8, ">="),
            ("tuerca antes del cubo del acople (luz) [mm]", p.drv_S_cpl0 - (p.drv_S_brgB + k["mb_t"] + k["b"]), 1.0, ">=")]
