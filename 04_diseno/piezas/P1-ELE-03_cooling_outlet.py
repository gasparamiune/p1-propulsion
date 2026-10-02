"""P1-ELE-03 — Pasacasco de salida del circuito de refrigeración con TESTIGO visible (AISI 316, comprado:
pasacasco recto G3/8 con espiga Ø8 [ESTIMADO: buscar "pasacasco inox 3/8 espiga 8 mm" Osculati/Watski]).

Circuito (pedido del grupo principal; como en los jetboards): puerto de presión de la bomba (grupo BOMBA,
pmp_cool_port, G1/8 con espiga) → manguera Ø6 × Ø8 → caja de agua del ESC (P1-ELE-04) → camisa del motor
(P1-MOT-01) → este pasacasco en el ESPEJO, por encima de la flotación y a la vista del piloto: si no sale
chorro, no hay refrigeración (parar). Agujero Ø17 en el espejo (casco de referencia del grupo TOMA)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402
from cadlib import cyl_x, hex_prism_x  # noqa: E402

META = dict(id="P1-ELE-03", name="cooling_outlet", desc="Pasacasco 316 de salida del agua de refrigeración (testigo en el espejo)",
            material="AISI 316", process="comprada", qty=1, frame="boat", group="ele",
            load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            mass_g=45.0)   # [ESTIMADO: pasacasco G3/8 inox con tuerca]

FL_D, FL_T = 28.0, 3.0       # [ESTIMADO: brida exterior]
TUBE_D = 16.0                # [ESTIMADO: G3/8 ≈ Ø16,7]
NUT_AF, NUT_T = 22.0, 6.0    # [ESTIMADO]
BARB_D, BARB_L = 8.0, 22.0   # espiga para manguera Ø6 int.


def build(p):
    y, z = p.cool_out_yz
    t = p.transom_t
    part = cyl_x(FL_D / 2, -FL_T, 0.0, y=y, z=z)
    part = part + cyl_x(TUBE_D / 2, -0.5, t + 0.5, y=y, z=z)
    part = part + hex_prism_x(NUT_AF, t, t + NUT_T, y=y, z=z)
    part = part + cyl_x(BARB_D / 2, t + NUT_T - 0.5, t + NUT_T + BARB_L, y=y, z=z)
    part = part - cyl_x(2.5, -FL_T - 1, t + NUT_T + BARB_L + 1, y=y, z=z)
    return part


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    y, z = p.cool_out_yz
    import params_tren as T
    h = T.cooling_hydraulics(p)
    return [("un solo sólido", len(part.solids()), 1, "="),
            (f"presión del puerto a rpm de 5 kn ≥ 3 × Δp del circuito (Q {h['Q_l_min']:.2f} L/min, {h['L_hose_m']:.1f} m de manguera) [Pa]",
             h["p_avail_legal_Pa"], 3 * h["dp_Pa"], ">="),
            ("salida por encima del espejo inferior y debajo del borde (z) [mm]", z, p.inp["boat"]["transom_height_m"] * 1000 - 60.0, "<="),
            ("salida lejos de la placa de espejo de la bomba (|y| − radio de la placa) [mm]",
             abs(y) - p.raw.get("pmp_tp_R", p.transom_hole_d / 2 + 25.0), 20.0, ">=")]
