"""P1-REV-02 — Pivote del bucket (×2): buje-espaciador AISI 316 torneado Ø REV_pin_d h7 (agujero Ø12,5) apretado
contra la cara EXTERIOR de la oreja de la boquilla (Y = ±STE_ear_y1, agujero Ø12,4) por un tornillo ISO 4017 M12
A4-80 con arandela ISO 7089 (Ø24) bajo la cabeza y, por dentro de la oreja, arandela + tuerca autoblocante
DIN 985 M12 A4 (precarga REV_bolt_pre_N). El bucket gira sobre el espaciador con su buje POM-C (P1-REV-03) y
queda con 0,3 mm de juego axial contra la arandela de la cabeza.

Auditoría ronda 3: la reacción de cada pivote incluye la de la traba (tangencial, M_h/r ≈ 2·F_b): con R12 y el
desfase admitido entre trabas llega a ~2,3 kN (antes se calculaba con F_b/2 = 0,7 kN sobre un perno Ø10 con M8
en voladizo). El momento en voladizo (reacción × (luz + L_buje/2)) lo toma la unión apretada; si se abriera, lo
toma el M12 A4-80 solo (structural_direccion). Se modela como un solo sólido (espaciador + tornillo + tuerca)
para el ensamblaje; marco local: eje +y desde la cara exterior de la oreja."""
import math

from cadlib import NUT_AF, NUT_M, cyl_y, hex_prism_y

META = dict(
    id="P1-REV-02", name="perno_bucket", desc="Pivote del bucket: espaciador 316 Ø18 h7 + tornillo M12 A4-80 + tuerca DIN 985",
    material="AISI 316", process="torneada", qty=2, frame="steer", group="jet",
    load_case="Reacción del pivote = chorro/2 + traba (R12, reparto con desfase): flexión del espaciador en voladizo",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)
WASHER_T = 2.5            # [VERIFICADO: ISO 7089 M12, Ø24 × 2,5]
NUT_H = 12.0              # [ESTIMADO: DIN 985 M12 (tuerca autoblocante con anillo), m ≈ 12 mm]
HEAD_K = 7.5              # [VERIFICADO: ISO 4017 M12, k = 7,5]


def shoulder_L(p):
    """Largo del espaciador: luz oreja–brazo + buje (brazo + aro) + 0,3 de juego axial."""
    return (p.REV_y_in + p.REV_bush_L + 0.3) - p.STE_ear_y1


def ear_t(p):
    return p.STE_ear_y1 - p.STE_ear_y0


def bolt_len(p):
    """Largo bajo cabeza mínimo: arandela + espaciador + oreja + arandela + tuerca + 2 hilos (paso 1,75)."""
    return WASHER_T + shoulder_L(p) + ear_t(p) + WASHER_T + NUT_H + 2 * 1.75


def bolt_len_iso(p):
    """Largo normalizado ISO 4017 (pasos de 5 mm) ≥ bolt_len."""
    return 5.0 * math.ceil(bolt_len(p) / 5.0)


def build(p):
    L = shoulder_L(p)
    d, db = p.REV_pin_d, p.REV_bolt_d
    s = cyl_y(d / 2, 0.0, L)                                                       # espaciador
    s = s + cyl_y(p.REV_head_d / 2, L, L + WASHER_T)                               # arandela Ø24
    s = s + hex_prism_y(NUT_AF[12], L + WASHER_T, L + WASHER_T + HEAD_K)           # cabeza M12 (18 e/c)
    lb = bolt_len_iso(p)
    s = s + cyl_y(db / 2 - 0.1, L + WASHER_T - lb, 0.01)                           # caña/rosca M12 (modelada Ø11,8)
    yn = -ear_t(p)
    s = s + cyl_y(p.REV_head_d / 2, yn - WASHER_T, yn)                             # arandela interior
    s = s + hex_prism_y(NUT_AF[12], yn - WASHER_T - NUT_H, yn - WASHER_T)          # tuerca DIN 985 M12
    return s


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    from params import loc_steer
    L0 = loc_steer(p, steer)
    Xb, Zb, y = p.X_bucket_pivot, p.Z_bucket_pivot, p.STE_ear_y1
    return [L0 * Pos(Xb, y, Zb), L0 * Pos(Xb, -y, Zb) * Rot(0, 0, 180)]


def checks(p, part):
    L = shoulder_L(p)
    rosca = (bolt_len_iso(p) - (WASHER_T + L + ear_t(p) + WASHER_T))               # rosca que pasa la arandela interior
    a_clamp = math.pi / 4 * (p.REV_pin_d ** 2 - (p.REV_bolt_d + 0.4) ** 2)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("juego axial del bucket contra la arandela de la cabeza [mm]", L - (p.REV_y_in + p.REV_bush_L - p.STE_ear_y1), 0.2, ">="),
            ("rosca útil para la tuerca M12 (≥ tuerca + 2 hilos) [mm]", rosca, NUT_H + 2 * 1.75, ">="),
            ("presión del espaciador sobre la oreja (precarga / anillo) ≤ 0,5·Rp0,2 6061-T6 [MPa]", p.REV_bolt_pre_N / a_clamp, 120.0, "<="),
            ("pared del espaciador (Ø ext − Ø 12,5) / 2 [mm]", (p.REV_pin_d - 12.5) / 2, 2.5, ">=")]
