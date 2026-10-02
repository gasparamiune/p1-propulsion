"""P1-REV-02 — Pivote del bucket (×2), EN DOS PIEZAS de dúplex 1.4462 + tornillo ISO 4017 M12 A4-80 + tuerca baja ISO 4035.

Re-auditoría ronda 5, MECH-1: el espaciador de una pieza (piloto Ø24 hacia adentro, brida Ø36 en la luz, muñón Ø20 hacia
afuera) NO se podía montar: desde afuera no pasa por el buje Ø20,1; desde adentro la brida no pasa por el agujero de la
oreja; y con los espaciadores puestos antes, el bucket soldado no calza sobre los muñones. Ahora:
  - CASQUILLO: brida Ø REV_sp_fl_d × REV_sp_fl_t apoyada en la cara EXTERIOR de la oreja (Y = ±STE_ear_y1) y piloto
    Ø REV_sp_pilot_d h6 ajustado en el agujero H7 del lóbulo engrosado del pivote (STE_piv_t), ENRASADO con su cara
    interior, con Loctite 641 en el ajuste (llena el juego: el apoyo lineal del cálculo y del FEA vale; re-auditoría
    ronda 5, FEA-4). Agujero Ø REV_pin_d H7 ciego con fondo de SLEEVE_BOTTOM y Ø12,5 para el tornillo. Se monta desde
    afuera ANTES del bucket: no pasa de la brida del buje POM (luz 0,5, check de P1-REV-03).
  - MUÑÓN: tubo Ø REV_pin_d h7 / Ø12,5 (el bucket gira sobre él con su buje P1-REV-03), del fondo del casquillo hasta
    afuera del buje; entra DESPUÉS del bucket, por el buje, con Tef-Gel (inox con inox).
  - Tornillo M12 A4-80 con arandela ISO 7089 (Ø24) bajo la cabeza sobre el extremo del muñón; por dentro arandela ancha
    ISO 7093 (Ø37 × 3) sobre el fondo del casquillo y la cara del lóbulo (sin puente: CALC-4) + tuerca baja ISO 4035 M12
    A4-035 con Loctite 243. Par REV_bolt_T_Nm BAJO: la precarga va cabeza → muñón → fondo del casquillo ← arandela; solo
    retiene (con precarga alta la brida y el muñón fluían: re-auditoría ronda 5, MEC-01).
El corte y el momento del pivote van muñón → casquillo → oreja por el apoyo del piloto (camino DISEÑADO; con Tef-Gel la
brida no lleva corte: MEC-02). La reacción de cada pivote incluye la de SU traba (tangencial, M_h/r): con R12 y una traba
sola llega a ~3,3 kN (structural_direccion.bucket_reactions). Se modela como un solo sólido (casquillo + muñón + tornillo
+ tuerca: la envolvente es la misma) para el ensamblaje; marco local: eje +y desde la cara exterior de la oreja."""
import math

from cadlib import NUT_AF, cyl_y, hex_prism_y

META = dict(
    id="P1-REV-02", name="perno_bucket",
    desc="Pivote del bucket en dos piezas de dúplex 1.4462: casquillo (brida Ø36 × 4, piloto Ø24 h6, Ø20 H7 ciego) + muñón Ø20 h7; tornillo M12 A4-80 + tuerca baja ISO 4035 con Loctite",
    material="Dúplex 1.4462", process="torneada", qty=2, frame="steer", group="jet",
    load_case="Reacción del pivote = chorro/2 + traba con M_h completo (R12, una traba sola): flexión del muñón y apertura de la unión",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)
WASHER_T = 2.5            # [VERIFICADO: ISO 7089 M12, Ø24 × 2,5]
NUT_H = 6.0               # [ESTIMADO: ISO 4035 M12, m máx. 6] (= REV_nut_h)
HEAD_K = 7.5              # [VERIFICADO: ISO 4017 M12, k = 7,5]
SLEEVE_BOTTOM = 4.0       # fondo del casquillo (entre el muñón y la arandela interior: compresión) [SUPUESTO]


def shoulder_L(p):
    """Largo de brida + muñón desde la cara de la oreja: brida + luz al brazo + buje (brazo + aro) + 0,3 de juego axial."""
    return (p.REV_y_in + p.REV_bush_L + 0.3) - p.STE_ear_y1


def ear_t(p):
    """Espesor del lóbulo engrosado del pivote (cara exterior → cara interior del refuerzo; R5-N5): largo del agujero
    H7 del piloto y apoyo de la arandela ancha y la tuerca."""
    return p.STE_piv_t


def pilot_L(p):
    """Piloto del casquillo ENRASADO con la cara interior del lóbulo (la arandela apoya en su fondo y en la cara)."""
    return ear_t(p)


def pin_L(p):
    """Largo del muñón: del fondo del casquillo al extremo exterior (bajo la arandela de la cabeza)."""
    return shoulder_L(p) + pilot_L(p) - SLEEVE_BOTTOM


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
    s = s + cyl_y(d / 2, p.REV_sp_fl_t - 0.01, L)                                  # muñón (pieza aparte)
    s = s + cyl_y(p.REV_sp_pilot_d / 2 - 0.01, -pilot_L(p) + 0.01, 0.01)           # piloto del casquillo (enrasado)
    s = s + cyl_y(p.REV_head_d / 2, L, L + WASHER_T)                               # arandela Ø24
    s = s + hex_prism_y(NUT_AF[12], L + WASHER_T, L + WASHER_T + HEAD_K)           # cabeza M12 (18 e/c)
    lb = bolt_len_iso(p)
    s = s + cyl_y(db / 2 - 0.1, L + WASHER_T - lb, -pilot_L(p) + 0.02)             # caña/rosca M12 (modelada Ø11,8)
    yn = -ear_t(p)
    dw, tw = p.REV_washer_in
    s = s + cyl_y(dw / 2, yn - tw, yn)                                             # arandela ancha ISO 7093 interior
    s = s + hex_prism_y(NUT_AF[12], yn - tw - p.REV_nut_h, yn - tw)                # tuerca baja ISO 4035 M12
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
            ("fondo del casquillo dentro del lóbulo (fondo < largo del piloto) [mm]", pilot_L(p) - SLEEVE_BOTTOM, 10.0, ">="),
            ("fondo del casquillo enrasado con la cara interior del lóbulo (arandela sin puente) [mm]", ear_t(p) - pilot_L(p), 0.0, "="),
            ("el muñón entra DESPUÉS del bucket por el buje (Ø interior del buje − Ø muñón) [mm]", 0.1, 0.05, ">="),
            ("pared del casquillo alrededor del muñón (Ø piloto − Ø muñón) / 2 [mm]", (p.REV_sp_pilot_d - p.REV_pin_d) / 2, 1.5, ">="),
            ("brida dentro de la oreja (r oreja − r brida) [mm]", p.STE_ear_r - p.REV_sp_fl_d / 2, 2.0, ">="),
            ("arandela ancha interior dentro de la oreja (r oreja − r arandela) [mm]", p.STE_ear_r - p.REV_washer_in[0] / 2, 1.0, ">=")]
