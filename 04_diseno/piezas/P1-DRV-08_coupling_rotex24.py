"""P1-DRV-08 — Acople elástico de mordazas KTR Rotex 24 (research/R11 §5: T_KN 35 N·m con estrella
92 ShA / 60 N·m con 98 ShA; 67,47 €). Une el eje Ø20 (chaveta 6 × 6) con el eje del motor (Ø de
inputs.yaml, chavetero). Distancia entre cubos "s" con juego axial: el motor NO recibe empuje (el empuje
queda en el par 7204). El cubo del lado del eje se refrenta a drv_coupling.l_hub_shaft.
Modelo simplificado: Ø55 × largo total con los dos agujeros."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _drv_geom import cyl_s  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-08", name="coupling_rotex24", desc="Acople Rotex 24 Ø20 / Ø motor (comprado; cubo de eje refrentado)",
            material="referencia", process="comprada", qty=1, frame="jet", group="drive",
            load_case="Par T_max del controlador; par de corte del pasador (pico)", print_rot=(0, 0, 0),
            solid_frac=1.0, orientation="—", mass_g=600.0,   # [ESTIMADO: research/R11 §9]
            allow={"P1-DRV-01": 20.0, "P1-MOT-01": 20.0})


def build(p):
    c = p.drv_coupling
    s0, s1 = p.drv_S_cpl0, p.drv_S_cpl_motor_face
    part = cyl_s(c["D"] / 2, s0, s1)
    part = part - cyl_s(p.shaft_d / 2, s0 - 1, p.drv_S_cpl_spider0 - 0.01)
    part = part - cyl_s(p.mot["shaft_d"] / 2, p.drv_S_cpl_spider0 + c["E"] + 0.01, s1 + 1)
    return part


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    c = p.drv_coupling
    m = p.sz["mech"]
    T = m["T_max_Nm"]
    T_cut = m.get("shear_pin", {}).get("T_cut_Nm", 0.0)
    eng = p.mot["shaft_l"] - p.mot_flange_gap
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("T_KN (estrella 92 ShA) ≥ 1,5 × T_max del controlador [N·m]", c["T_KN_Nm"], 1.5 * T, ">="),
            ("T_Kmax ≥ par de corte del pasador (pico de traba) [N·m]", c["T_Kmax_Nm"], T_cut, ">="),
            ("n máx. del acople ≥ n máx. [rpm]", c["n_max_rpm"], m["n_max_rpm"], ">="),
            ("agujeros ≤ agujero máx. [mm]", max(p.shaft_d, p.mot["shaft_d"]), c["bore_max"], "<="),
            ("eje del motor dentro del cubo (encastre) [mm]", eng, 0.8 * c["l_hub"], ">="),
            ("eje del motor no toca la estrella (luz) [mm]",
             (p.S_motor0 - p.mot["shaft_l"]) - (p.drv_S_cpl_spider0 + c["E"]), 0.5, ">=")]
