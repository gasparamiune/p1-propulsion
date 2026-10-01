"""params.py — parámetros geométricos del CAD del waterjet P1-J, derivados de inputs.yaml y de
resultados/sizing.json (no se edita a mano: cambiar inputs.yaml y correr run_all.py).

Marcos de referencia
  BOTE (x, y, z): origen en la cara EXTERIOR del espejo, en crujía, sobre la cara exterior del
        fondo (quilla). x hacia PROA (positivo dentro del bote), y a babor, z hacia arriba.
        El fondo del casco es el plano z = 0 en la zona de la toma (fondo plano local).
  JET (X, Y, Z): origen en el centro de la CARA DE ENTRADA DEL IMPULSOR. X a lo largo del eje
        hacia POPA (sentido del flujo), Y a babor, Z perpendicular "arriba". El eje sube hacia
        proa con el ángulo α (inputs waterjet.shaft_incline_deg): JET → BOTE = Pos(x_if, 0, z_if)
        · Rot_y(−α) · Rot_z(180°)  (ver loc_jet()).
  BOQUILLA (para dirección y reversa): rotaciones alrededor de sus pivotes en el marco JET.

Proporciones del jet escaladas con D (research/R10a §5.2, Ø108 de referencia) [CALCULADO/ESTIMADO
allí]: pila impulsor+estator 1,11·D, tobera 0,93·D, labio a 0,89·D y tangencia a 3,77·D a proa
de la cara del impulsor, garganta Ø1,11·D, abertura 2,9·D × 1,2·D, rampa 27°.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from p1calc.io import load_inputs  # noqa: E402


@dataclass
class P:
    """Contenedor de parámetros (mm salvo indicación)."""
    raw: dict = field(default_factory=dict)

    def __getattr__(self, k):
        try:
            return self.raw[k]
        except KeyError as e:
            raise AttributeError(k) from e


def load(inputs_path=None, sizing_path=None) -> P:
    inp = load_inputs(inputs_path)
    sp = Path(sizing_path) if sizing_path else ROOT / "resultados" / "sizing.json"
    with open(sp, encoding="utf-8") as f:
        sz = json.load(f)
    sel = sz["selection"]
    g, j, b = inp["geometry"], inp["waterjet"], inp["boat"]
    mo = inp["motor"]["options"][sel["motor"]]
    d = {"inp": inp, "sz": sz}
    d["clr"] = g["clearance_mm"]
    d["press"] = g["press_fit_mm"]
    d["bolt_clr"] = g["bolt_clearance_mm"]
    d["wall"] = g["min_wall_mm"]
    d["envelope"] = tuple(inp["printer"]["envelope_mm"])

    # --- bomba (de sizing) ---
    D = sel["D_imp_mm"]
    d["D"] = D                                            # Ø punta del impulsor
    d["D_hub"] = sel["hub_d_mm"]
    d["D_noz"] = sel["D_noz_mm"]
    d["tip_clr"] = sz["pump"]["tip_clearance_mm"]
    d["D_bore"] = D + 2 * d["tip_clr"]                    # Ø interior del anillo de desgaste
    d["blades"] = j["blades"]
    d["vanes"] = j["stator_vanes"]
    d["pump_sections"] = sz["pump"]["sections"]           # triángulos de velocidad (cubo/medio/punta)
    d["alpha"] = j["shaft_incline_deg"]
    d["ramp"] = j["ramp_angle_deg"]
    d["h_axis"] = j["axis_height_m"] * 1000               # eje en la cara del impulsor sobre la quilla

    # --- pila axial (marco JET, X hacia popa desde la cara de entrada del impulsor) ---
    d["L_imp"] = round(0.42 * D, 1)                       # largo axial del impulsor (cubo)
    d["gap_rs"] = round(0.06 * D, 1)                      # luz rotor–estator
    d["L_stat"] = round(1.11 * D - d["L_imp"] - d["gap_rs"], 1)   # estator: completa 1,11·D
    d["L_noz"] = round(0.93 * D, 1)                       # tobera (contracción hasta D_noz)
    d["X_imp1"] = d["L_imp"]
    d["X_st0"] = d["L_imp"] + d["gap_rs"]
    d["X_st1"] = d["X_st0"] + d["L_stat"]
    d["X_noz1"] = d["X_st1"] + d["L_noz"]                 # salida de la tobera fija
    d["L_ring"] = round(d["L_imp"] + 0.10 * D, 1)         # anillo de desgaste: cubre el impulsor + 5 % D por lado
    d["X_ring0"] = -0.05 * D
    ca = math.cos(math.radians(d["alpha"]))
    sa = math.sin(math.radians(d["alpha"]))
    # la salida de la tobera fija queda en el plano del espejo (x = 0) → posición de la cara del impulsor
    d["x_if"] = d["X_noz1"] * ca
    d["z_if"] = d["h_axis"]
    d["z_noz"] = d["z_if"] - d["X_noz1"] * sa             # eje de la tobera en el espejo

    # --- boquilla direccional y bucket (afuera del espejo) ---
    d["steer_max"] = j["steering"]["max_deflection_deg"]
    d["X_steer_pivot"] = d["X_noz1"] + 0.20 * D           # eje vertical de la boquilla (marco JET)
    d["L_steer"] = round(1.0 * D, 1)
    d["D_steer_in"] = d["D_noz"] + 4.0
    d["X_bucket_pivot"] = d["X_steer_pivot"] + 0.35 * D
    d["Z_bucket_pivot"] = 0.62 * D

    # --- toma (marco BOTE) ---
    d["D_throat"] = round(1.11 * D, 1)
    d["x_lip"] = d["x_if"] + 0.89 * D
    d["x_tan"] = d["x_if"] + 3.77 * D
    d["W_open"] = round(1.2 * D, 1)
    d["L_open"] = d["x_tan"] - d["x_lip"]
    d["r_lip"] = round(0.11 * D, 1)
    d["grille_bars"] = 7 if D <= 115 else 8
    d["grille_bar_d"] = 4.0                               # [ESTIMADO: research/R10a §4 — barras de 4 mm, luz ~12 mm]
    d["bottom_t"] = b["bottom_thickness_mm"]
    d["transom_t"] = b["transom_thickness_mm"]
    d["floor_z"] = b["floor_height_m"] * 1000
    d["shaft_exit_x"] = d["x_if"] + 1.2 * D               # el eje sale por el techo de la rampa (R10a §5.2: 130 mm con Ø108)

    # --- tren (marco BOTE, a lo largo del eje) ---
    d["shaft_d"] = inp["shaft"]["d_mm"]
    d["motor_d"], d["motor_l"] = mo["size_mm"]
    d["L_bearing_housing"] = 80.0                         # [SUPUESTO: par 7204 BEP + sello + tapa]
    d["L_coupling"] = 60.0                                # [ESTIMADO: acople de mordazas L-090/Rotex 24]
    d["S_seal"] = (d["shaft_exit_x"] - d["x_if"]) / ca + 15.0   # distancia a lo largo del eje desde la cara del impulsor, hacia proa
    d["S_brg0"] = d["S_seal"] + 10.0
    d["S_brg1"] = d["S_brg0"] + d["L_bearing_housing"]
    d["S_cpl1"] = d["S_brg1"] + d["L_coupling"]
    d["S_motor0"] = d["S_cpl1"] + 5.0
    d["S_motor1"] = d["S_motor0"] + d["motor_l"]
    d["S_shaft_fwd"] = d["S_cpl1"] - 0.5 * d["L_coupling"] + 25.0
    d["X_shaft_aft"] = d["X_imp1"] + 12.0                 # extremo de popa del eje (tuerca del impulsor)
    d["motor_axis_z_mid"] = d["z_if"] + (d["S_motor0"] + d["motor_l"] / 2) * sa
    d["motor_bottom_z"] = d["motor_axis_z_mid"] - d["motor_d"] / 2 * ca
    d["motor_x_mid"] = d["x_if"] + (d["S_motor0"] + d["motor_l"] / 2) * ca

    # --- INTERFACES entre subsistemas (las fija este archivo; cada grupo las respeta) ---
    # toma ↔ bomba: brida en el plano X_jet = X_duct_out (marco JET)
    d["X_duct_out"] = d["X_ring0"] - 10.0
    d["pump_flange_od"] = d["D_bore"] + 2 * 30.0
    d["pump_flange_bc"] = d["D_bore"] + 2 * 16.0
    d["pump_flange_n"] = 8
    d["pump_flange_bolt"] = 6                             # M6 A4
    # bomba ↔ espejo: agujero en el espejo y placa de espejo (la hace el grupo bomba)
    d["transom_hole_d"] = d["D_bore"] + 2 * 14.0
    # bomba ↔ dirección: orejas de pivote de la boquilla (en la tobera fija, grupo bomba)
    d["steer_pin_d"] = 8.0                                # pernos 316 Ø8
    d["Z_steer_lug"] = d["D_noz"] / 2 + 18.0              # ± sobre el eje (marco JET), en X = X_steer_pivot
    # toma ↔ tren: el eje atraviesa el techo de la rampa en S_seal; buje de la toma
    d["seal_boss_od"] = 64.0
    d["seal_spigot_d"] = 42.0                             # centrador de la caja del sello (H8)
    d["seal_bc"] = 54.0                                   # 4 × M6 alrededor del eje, en el plano ⟂ al eje
    # toma ↔ tren: soporte de rodamientos sobre la placa base de la toma (marco BOTE)
    d["base_top_z"] = 10.0                                # cara superior de la placa base de la toma
    d["brg_bracket_x0"] = d["x_if"] + (d["S_brg0"] - 5.0) * ca
    d["brg_bracket_x1"] = d["brg_bracket_x0"] + 150.0
    # el soporte es un PUENTE sobre el conducto de la toma: apoya en la placa base a ambos lados de
    # la abertura (|y| = W_open/2 + 45), nunca dentro de ella
    d["brg_bracket_y"] = d["W_open"] / 2 + 45.0
    d["brg_bracket_holes"] = [(d["brg_bracket_x0"] + 15.0, y) for y in (-d["brg_bracket_y"], d["brg_bracket_y"])] + \
                             [(d["brg_bracket_x1"] - 15.0, y) for y in (-d["brg_bracket_y"], d["brg_bracket_y"])]   # 4 × M8, (x, y)
    d["brg_bracket_bolt"] = 8

    # --- caja del controlador (heredada) ---
    d["esc_in"] = tuple(g["esc_box_inner_mm"])
    d["oring_cs"] = g["oring_cs_mm"]
    d["oring_sq"] = g["oring_squeeze_frac"]
    d["oring_fill"] = g["oring_gland_fill_frac"]
    # parámetros por subsistema: 04_diseno/params_<grupo>.py con extend(d) (cada grupo edita el suyo)
    import importlib.util
    for f in sorted(Path(__file__).resolve().parent.glob("params_*.py")):
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.extend(d)
    return P(d)


# ---------------------------------------------------------------------------
# Transformaciones
# ---------------------------------------------------------------------------
def loc_jet(p: P):
    """Marco JET → BOTE. X_jet (popa) → −x del bote inclinado α hacia abajo."""
    from build123d import Pos, Rot
    return Pos(p.x_if, 0, p.z_if) * Rot(0, -p.alpha, 0) * Rot(0, 0, 180)


def jet_to_boat(p: P, X, Y, Z):
    """Punto del marco JET en coordenadas del BOTE."""
    from build123d import Pos
    v = (loc_jet(p) * Pos(X, Y, Z)).position
    return (v.X, v.Y, v.Z)


def loc_steer(p: P, steer_deg: float = 0.0):
    """Boquilla direccional: rotación alrededor del eje Z_jet en X = X_steer_pivot."""
    from build123d import Pos, Rot
    return loc_jet(p) * Pos(p.X_steer_pivot, 0, 0) * Rot(0, 0, steer_deg) * Pos(-p.X_steer_pivot, 0, 0)


def loc_bucket(p: P, down: bool = False, steer_deg: float = 0.0):
    """Bucket de reversa: pivota alrededor de Y_jet en (X_bucket_pivot, Z_bucket_pivot); arriba
    (avante) o abajo (reversa). Va montado en la boquilla (sigue la dirección)."""
    from build123d import Pos, Rot
    ang = 0.0 if not down else p.raw.get("bucket_down_deg", 70.0)
    return (loc_steer(p, steer_deg) * Pos(p.X_bucket_pivot, 0, p.Z_bucket_pivot) * Rot(0, ang, 0)
            * Pos(-p.X_bucket_pivot, 0, -p.Z_bucket_pivot))


def loc_boat(p: P):
    from build123d import Location
    return Location()


if __name__ == "__main__":
    pp = load()
    for k, v in sorted(pp.raw.items()):
        if k in ("inp", "sz", "pump_sections"):
            continue
        print(f"{k:22s} {v}")
