"""P1-DRV-04 — Rodamiento de bolas de contacto angular SKF 7204 BECBP (40°, APAREABLE UNIVERSAL, juego
axial normal CB; alternativa 7204 BEGAP con precarga ligera GA), 2 unidades montadas en O (espalda con
espalda) en P1-DRV-03: fijan el eje axialmente en ambos sentidos y toman todo el empuje del impulsor.
Auditoría Pass 3 H8: el 7204 BEP NO es apareable universal; con aros interiores (KM4 contra el collar) y
exteriores (resalte + tapa) apretados, el juego/precarga del par solo queda definido con caras rectificadas
para apareo universal (sufijo CB/GA). Comprado (precio de referencia del BEP: research/R11 §5, 31,40 € c/u;
el BECBP es otro ítem — cotizar). Modelo simplificado: anillo 20 × 47 × 14."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos  # noqa: E402
from _drv_geom import tube_s  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-04", name="bearing_7204BEP", desc="Rodamiento SKF 7204 BECBP apareable universal (par en O), comprado",
            material="Acero", process="comprada", qty=2, frame="jet", group="drive",
            load_case="Empuje Fa + reacción radial (L10 en sizing)", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—", mass_g=110.0,   # [ESTIMADO: params_tren.BEARING mass_g]
            allow={"P1-DRV-03": 5.0, "P1-DRV-01": 10.0, "P1-DRV-04": 1.0})


def build(p):
    b = p.drv_bearing
    return tube_s(b["D"] / 2, b["d"] / 2, p.drv_S_brgA, p.drv_S_brgA + b["B"])


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p), loc_jet(p) * Pos(-p.drv_bearing["B"], 0, 0)]


def checks(p, part):
    b = p.drv_bearing
    m = p.sz["mech"]
    Fa, Fr = m["Fa_max_N"], m["Fr_N"]
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("C0 / Fa a punto fijo (estático) ≥ 2 [—]", b["C0_n"] / Fa, 2.0, ">="),
            ("L10 a V máx. (sizing) ≥ vida objetivo [h]", m["L10_top_h"], p.inp["bearings"]["life_target_h"], ">="),
            ("par en O: 2 × B = largo del muñón [mm]", 2 * b["B"], p.drv_S_brgB - p.drv_S_brgA, "=")]
