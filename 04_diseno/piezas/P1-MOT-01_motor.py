"""P1-MOT-01 — Motor eléctrico de la selección de sizing (hoy Maytech MTI120116 150 KV, inrunner
refrigerado por agua, Ø120 × 116, eje Ø15 × 30 con chavetero — research/R11 §1.2). Comprado; modelo
simplificado: cuerpo Ø motor_d × motor_l coaxial al eje (S_motor0 … S_motor1), centrador delantero y
eje. Cara delantera (lado del eje) en S_motor0: ahí se abulona P1-MOT-02. Las espigas de la camisa de
agua (entrada/salida) van arriba [ESTIMADO: posición real según el motor recibido]."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _drv_geom import cyl_s  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-MOT-01", name="motor", desc="Motor de la selección (MTI120116: Ø120 × 116, refrigerado por agua)",
            material="referencia", process="comprada", qty=1, frame="jet", group="motor",
            load_case="Par de reacción T_max sobre P1-MOT-02; 3 g vertical", print_rot=(0, 0, 0),
            solid_frac=1.0, orientation="—", mass_from="motor",
            allow={"P1-DRV-08": 5.0, "P1-MOT-02": 5.0})


def build(p):
    m = p.mot
    body = cyl_s(p.motor_d / 2, p.S_motor0, p.S_motor1)
    pilot = cyl_s(m["pilot_d"] / 2, p.S_motor0 - m["pilot_l"], p.S_motor0 + 0.5)
    shaft = cyl_s(m["shaft_d"] / 2, p.S_motor0 - m["shaft_l"], p.S_motor0 + 0.5)
    return body + pilot + shaft


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz motor ↔ fondo interior del casco [mm]", p.mot_clear_bottom, p.mot_clear_min, ">="),
            ("motor por encima del piso (luz al piso) [mm]", p.mot_clear_floor, 0.0, ">="),
            ("coaxialidad declarada motor ↔ eje (mismo marco JET, desalineación de montaje) [mm]", 0.0, 0.0, "="),
            ("datos del motor encontrados en la tabla de params_tren (si no: escalado ESTIMADO) [—]", float(p.mot_known), 1.0, "=")]
