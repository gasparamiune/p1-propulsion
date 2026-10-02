"""P1-REV-02 — Pivote del bucket (×2): espaciador de dúplex 1.4462 torneado + tornillo ISO 4017 M12 A4-80 + tuerca ISO 4032.

Espaciador (auditoría ronda 4): muñón Ø REV_pin_d h7 (el bucket gira sobre él con su buje POM-C P1-REV-03), brida
Ø REV_sp_fl_d × REV_sp_fl_t apoyada en la cara EXTERIOR de la oreja de la boquilla (Y = ±STE_ear_y1) y piloto
Ø REV_sp_pilot_d h6 ajustado en el agujero H7 escariado de la oreja (largo = oreja − 0,5: el apriete lo toma la brida,
no el piloto). El piloto ubica el pivote y es el camino DISEÑADO del corte y del momento: con Tef-Gel la brida desliza
con R12, así que el piloto apoya en la oreja como un perno en voladizo (re-auditoría ronda 5, MEC-02). Agujero Ø12,5
para el tornillo M12 A4-80; arandela ISO 7089 (Ø24) bajo la cabeza y, por dentro de la oreja, arandela ancha ISO 7093
(Ø37 × 3) + tuerca ISO 4032 M12 A4-80, con Loctite 243 en la rosca. Par REV_bolt_T_Nm BAJO: el tornillo solo retiene
(con precarga alta la brida y el muñón fluían: re-auditoría ronda 5, MEC-01). La precarga pasa por el muñón y la brida
(placa anular en flexión) y se suma a la flexión del muñón: dúplex 1.4462 (Rp0,2 ≥ 450) (structural_direccion).

La reacción de cada pivote incluye la de SU traba (tangencial, M_h/r): con R12 y una traba sola llega a ~3,3 kN
(structural_direccion.bucket_reactions). Se modela como un solo sólido (espaciador + tornillo + tuerca) para el
ensamblaje; marco local: eje +y desde la cara exterior de la oreja."""
import math

from cadlib import NUT_AF, cyl_y, hex_prism_y

META = dict(
    id="P1-REV-02", name="perno_bucket",
    desc="Pivote del bucket: espaciador dúplex 1.4462 (muñón Ø20 h7, brida Ø36 × 4, piloto Ø20 h6) + tornillo M12 A4-80 + tuerca ISO 4032 con Loctite",
    material="Dúplex 1.4462", process="torneada", qty=2, frame="steer", group="jet",
    load_case="Reacción del pivote = chorro/2 + traba con M_h completo (R12, una traba sola): flexión del muñón y apertura de la unión",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)
WASHER_T = 2.5            # [VERIFICADO: ISO 7089 M12, Ø24 × 2,5]
NUT_H = 10.8              # [ESTIMADO: ISO 4032 M12, m máx. 10,8] (= REV_nut_h)
HEAD_K = 7.5              # [VERIFICADO: ISO 4017 M12, k = 7,5]


def shoulder_L(p):
    """Largo de brida + muñón desde la cara de la oreja: brida + luz al brazo + buje (brazo + aro) + 0,3 de juego axial."""
    return (p.REV_y_in + p.REV_bush_L + 0.3) - p.STE_ear_y1


def ear_t(p):
    return p.STE_ear_y1 - p.STE_ear_y0


def pilot_L(p):
    return ear_t(p) - 0.5


def bolt_len(p):
    """Largo bajo cabeza mínimo: arandela + espaciador + oreja + arandela ancha + tuerca + 2 hilos (paso 1,75)."""
    return WASHER_T + shoulder_L(p) + ear_t(p) + p.REV_washer_in[1] + p.REV_nut_h + 2 * 1.75


TOWER_Y = 14.0            # semiancho de la torre del yugo de P1-STE-01 frente al pivote [CALCULADO: CAD, ronda 4]


def tip_y(p, L):
    """|Y| de la punta del tornillo de largo L (la cabeza está afuera, sobre el muñón)."""
    return p.STE_ear_y1 + shoulder_L(p) + WASHER_T - L


def bolt_len_iso(p):
    """Largo normalizado ISO 4017 (pasos de 5 mm) ≥ bolt_len; si así la punta entra en la torre del yugo (|Y| < 15),
    el tornillo se corta a medida (mm entero ≥ bolt_len, chaflán): pasa con otras entradas (regeneración)."""
    L5 = 5.0 * math.ceil(bolt_len(p) / 5.0)
    return L5 if tip_y(p, L5) >= TOWER_Y + 1.0 else float(math.ceil(bolt_len(p)))


def build(p):
    L = shoulder_L(p)
    d, db = p.REV_pin_d, p.REV_bolt_d
    s = cyl_y(p.REV_sp_fl_d / 2, 0.0, p.REV_sp_fl_t)                             # brida
    s = s + cyl_y(d / 2, p.REV_sp_fl_t - 0.01, L)                                  # muñón
    s = s + cyl_y(p.REV_sp_pilot_d / 2 - 0.01, -pilot_L(p), 0.01)                  # piloto (ajustado en la oreja)
    s = s + cyl_y(p.REV_head_d / 2, L, L + WASHER_T)                               # arandela Ø24
    s = s + hex_prism_y(NUT_AF[12], L + WASHER_T, L + WASHER_T + HEAD_K)           # cabeza M12 (18 e/c)
    lb = bolt_len_iso(p)
    s = s + cyl_y(db / 2 - 0.1, L + WASHER_T - lb, -pilot_L(p) + 0.01)             # caña/rosca M12 (modelada Ø11,8)
    yn = -ear_t(p)
    dw, tw = p.REV_washer_in
    s = s + cyl_y(dw / 2, yn - tw, yn)                                             # arandela ancha ISO 7093 interior
    s = s + hex_prism_y(NUT_AF[12], yn - tw - p.REV_nut_h, yn - tw)                # tuerca ISO 4032 M12
    return s


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    from params import loc_steer
    L0 = loc_steer(p, steer)
    Xb, Zb, y = p.X_bucket_pivot, p.Z_bucket_pivot, p.STE_ear_y1
    return [L0 * Pos(Xb, y, Zb), L0 * Pos(Xb, -y, Zb) * Rot(0, 0, 180)]


def checks(p, part):
    L = shoulder_L(p)
    rosca = (bolt_len_iso(p) - (WASHER_T + L + ear_t(p) + p.REV_washer_in[1]))     # rosca que pasa la arandela interior
    a_cl = math.pi / 4 * (p.REV_sp_fl_d ** 2 - (p.REV_sp_pilot_d + 1.0) ** 2)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("juego axial del bucket contra la arandela de la cabeza [mm]", L - (p.REV_y_in + p.REV_bush_L - p.STE_ear_y1), 0.2, ">="),
            ("rosca útil para la tuerca M12 (≥ tuerca + 2 hilos) [mm]", rosca, p.REV_nut_h + 2 * 1.75, ">="),
            ("presión de la brida sobre la oreja con la precarga MÁX. ≤ 0,5·Rp0,2 6061-T6 [MPa]", p.REV_bolt_pre_max_N / a_cl, 120.0, "<="),
            ("punta del tornillo fuera de la torre del yugo (|Y| ≥ 14 + 1) [mm]", tip_y(p, bolt_len_iso(p)), TOWER_Y + 1.0, ">="),
            ("pared del muñón (Ø − Ø 12,5) / 2 [mm]", (p.REV_pin_d - 12.5) / 2, 2.5, ">="),
            ("pared del piloto (Ø − Ø 12,5) / 2 [mm]", (p.REV_sp_pilot_d - 12.5) / 2, 1.5, ">="),
            ("piloto más corto que la oreja (aprieta la brida) [mm]", ear_t(p) - pilot_L(p), 0.3, ">="),
            ("brida dentro de la oreja (r oreja − r brida) [mm]", p.STE_ear_r - p.REV_sp_fl_d / 2, 2.0, ">="),
            ("arandela ancha interior dentro de la oreja (r oreja − r arandela) [mm]", p.STE_ear_r - p.REV_washer_in[0] / 2, 1.0, ">=")]
