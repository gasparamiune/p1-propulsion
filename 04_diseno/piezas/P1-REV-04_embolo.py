"""P1-REV-04 — Émbolo de traba del bucket (×2), PROPIO: cuerpo y perno de AISI 316 torneados + resorte inox comprado.

Por qué propio (auditoría ronda 4): el émbolo de catálogo supuesto ("GN 617-12 M20 A4") no existe; el GN 617 inox
con rosca M20×1,5 trae perno Ø10 de AISI 303 que sobresale 10 mm (l2) y resorte 17–40 N [VERIFICADO: catálogo Elesa/Ganter
GN 617, pág. 809], y con una traba sola (M_h completo con R12, ≈ 3 kN en el perno) no llega a FS 2.

Geometría (marco local de la oreja +Y; la −Y es su espejo; medidas en piezas/_release.PLG_*): cuerpo AJUSTADO Ø26 h6
(REV_lock_bore_d) en el agujero liso Ø26 H7 del lóbulo engrosado de la oreja (STE_lock_t, de STE_lock_y1 hacia adentro,
R5-N5) con Loctite 641; collar EXTERIOR Ø32 × 1,5 en la luz lóbulo–brazo (apoya en la cara exterior del lóbulo: ubica la
punta y toma el empuje del resorte y del tiro del cable, que van hacia adentro) y, por dentro, arandela 0,8 + anillo DIN 471-26 contra la cara interior del
lóbulo (retiene el cuerpo; el Ø26 sigue PLG_FIT_EXT más allá para la ranura). SIN rosca ni precarga en la oreja: el cuerpo
pasa la fuerza y el momento del perno a la oreja por aplastamiento, como el piloto del pivote (re-auditoría ronda 5:
la precarga de 110 N·m del cuerpo roscado M24 abría el lóbulo de la oreja y el FEA de P1-STE-01 daba FS 1,74).
Adentro del cuerpo: guía del perno (18 mm desde la cara exterior de la placa de la oreja, más el lóbulo y el collar) y cámara del resorte
(largo instalado 30), cerrada por una tapa roscada de 4 mm con agujero Ø10,2 para la cola Ø10 del perno; pomo Ø25 × 10
con agujero pasante Ø4,5, apoyado en la tapa en reposo; rosca M4 × 10 axial en el extremo de la cola Ø10 (vástago del
eslabón rígido de P1-REV-09, Loctite 243; re-auditoría ronda 5, DES-04). Cola = cámara + tapa + pomo (44 mm: la carrera
no se suma, DES-02/MEC-03). Perno Ø16 h9 (REV_lock_pin_d) que cruza la luz oreja–brazo y el brazo (REV_t) y sobresale
1 mm de su cara exterior; el escalón Ø16 → Ø10 es el asiento del resorte. Carrera REV_plunger_stroke (≥ recorrido para
liberar el brazo + 2). Resorte inox de compresión: alambre 1,4, Ø ext 15, 6,5 espiras útiles, largo libre 40,
compacto ≈ 11,9, k ≈ 2,06 N/mm → ≈ 20,6 N instalado y ≈ 45 N al final de la carrera [CALCULADO: _release.SPRING_*,
G ESTIMADO; B-SPRING; re-auditoría ronda 5, DES-01]. Montaje: el cuerpo armado (perno, resorte, tapa) entra desde
AFUERA de la oreja (pomo Ø25 y cuerpo Ø24 pasan por el Ø26), antes del bucket y del soporte P1-REV-09.
Traba ARRIBA y ABAJO (dos agujeros por brazo); se libera tirando de la cola (eslabón rígido → balancín de P1-REV-09 →
Bowden) desde el gatillo de la palanca del bucket (P1-CTL-10/14); al soltar, el resorte lo mete (traba automática al
llegar). DOS émbolos (qty 2), uno por oreja ±Y (REV_n_locks): cada uno solo lleva todo M_h (los agujeros tienen juego:
no hay reparto garantizado); el segundo es redundancia. Los cuerpos llegan hasta el plano medio (Y = 0) y los dos
émbolos pasan uno al lado del otro (ejes desfasados: check)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-04", name="embolo",
    desc="Émbolo de traba propio: cuerpo ajustado Ø26 h6 (Loctite 641, collar exterior + anillo DIN 471) y perno Ø16 h9 "
         "en AISI 316 + resorte inox, uno por oreja ±Y",
    material="AISI 316", process="torneada", qty=2, frame="steer", group="jet",
    load_case="Perno Ø16: flexión + corte con M_h completo en una traba (R12) / REV_lock_r; cuerpo: aplastamiento en la oreja",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def pin_tip_y(p):
    return RL.pin_tip_y(p)


def lobe_y0(p):
    """Cara interior del lóbulo engrosado de la traba (apoyo del anillo DIN 471)."""
    return p.STE_lock_y1 - p.STE_lock_t


def fit_y0(p):
    """Extremo interior del tramo ajustado Ø26 (ranura del anillo DIN 471 incluida)."""
    return lobe_y0(p) - RL.PLG_FIT_EXT


def build(p):
    y0, y1 = lobe_y0(p), p.STE_lock_y1                                         # caras del lóbulo de la traba
    ysh = p.STE_ear_y1 - RL.PLG_GUIDE                                                     # escalón Ø16 → Ø10 (asiento del resorte)
    s = cyl_y(p.REV_lock_pin_d / 2, ysh, pin_tip_y(p))                         # perno Ø16 (guía + luz + brazo)
    s = s + cyl_y(p.REV_lock_bore_d / 2 - 0.01, fit_y0(p), y1 + 0.01)            # tramo ajustado Ø26 h6 (lóbulo + ranura)
    s = s + cyl_y(RL.PLG_COLLAR_D / 2, y1, y1 + RL.PLG_COLLAR_T)                 # collar exterior Ø32, apoya en la oreja
    s = s + cyl_y(RL.PLG_RING_D / 2, y0 - RL.PLG_RING_T, y0)                     # arandela + anillo DIN 471-26 (Ø máx.)
    s = s + cyl_y(RL.PLG_BODY_D / 2, RL.body_end_y(p), fit_y0(p) + 0.01)         # cuerpo Ø24 (cámara del resorte + tapa)
    s = s + cyl_y(12.5, RL.knob_end_y(p), RL.body_end_y(p) + 0.01)               # pomo Ø25
    return s


lock_xz = RL.lock_xz          # posición de cada émbolo (fuente única: _release)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    from params import loc_steer
    x, z = lock_xz(p)
    L = [loc_steer(p, steer) * Pos(x, 0, z)]
    if p.REV_n_locks > 1:
        x2, z2 = lock_xz(p, -1)
        L.append(loc_steer(p, steer) * Pos(x2, 0, z2) * Rot(180, 0, 0))   # gemelo en la oreja −Y (ángulo REV_lock_ang_m)
    return L


def checks(p, part):
    x, z = lock_xz(p)
    ybot = RL.knob_end_y(p) - p.REV_plunger_stroke                             # pomo con el perno afuera (tirado)
    zbody = math.sqrt(max(p.STE_ro ** 2 - min(abs(ybot), p.STE_ro) ** 2, 0.0)) if abs(ybot) < p.STE_ro else 0.0
    zring = math.sqrt(max(p.STE_ro ** 2 - (lobe_y0(p) - RL.PLG_RING_T) ** 2, 0.0))
    sp_comp = RL.PLG_SPRING_L1 - p.REV_plunger_stroke                           # largo del resorte con el perno afuera
    d12 = math.dist(lock_xz(p, 1), lock_xz(p, -1)) if p.REV_n_locks > 1 else 99.0
    zlow = min(z, lock_xz(p, -1)[1])
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pomo (tirado) sobre el cuerpo de la boquilla [mm]", zlow - 12.5 - zbody, 2.0, ">="),
            ("anillo DIN 471 del cuerpo sobre el cuerpo de la boquilla [mm]", (zlow - RL.PLG_RING_D / 2) - zring, 2.0, ">="),
            ("collar exterior: luz al brazo del bucket [mm]", p.REV_y_in - (p.STE_lock_y1 + RL.PLG_COLLAR_T), 1.0, ">="),
            ("collar exterior libre de la brida del pivote [mm]", p.REV_lock_r - (RL.PLG_COLLAR_D + p.REV_sp_fl_d) / 2, 2.0, ">="),
            ("collar exterior: apoyo en la oreja (r collar − r agujero) [mm]", (RL.PLG_COLLAR_D - p.REV_lock_bore_d) / 2, 2.5, ">="),
            ("perno sobresale de la cara exterior del brazo [mm]", pin_tip_y(p) - (p.REV_y_in + p.REV_t), 0.5, ">="),
            ("carrera ≥ recorrido para liberar el brazo + 2 [mm]", p.REV_plunger_stroke, RL.need(p) + 2.0, ">="),
            ("resorte con el perno afuera ≥ compacto + Sa (EN 13906-1) [mm]", sp_comp,
             RL.spring_L_solid() + RL.spring_Sa(), ">="),
            ("holgura diametral perno ↔ agujero del brazo [mm]", p.REV_lock_hole_d - p.REV_lock_pin_d, 0.3, ">="),
            ("ranura del anillo dentro del cuerpo: Ø26 más allá del lóbulo − (arandela + ranura) [mm]",
             RL.PLG_FIT_EXT - (0.8 + 1.3), 1.8, ">="),
            ("escalón del perno (asiento del resorte) dentro del tramo ajustado [mm]",
             (p.STE_ear_y1 - RL.PLG_GUIDE) - fit_y0(p), 0.0, ">="),
            ("pared del cuerpo bajo la ranura del anillo sobre el perno [mm]",
             (RL.PLG_RING_GROOVE_D - (p.REV_lock_pin_d + 0.2)) / 2, 2.5, ">="),
            ("pomo y cuerpo pasan por el agujero de la oreja al montar (Ø agujero − Ø pomo) [mm]",
             p.REV_lock_bore_d - max(25.0, RL.PLG_BODY_D), 0.5, ">="),
            ("ligamento de la oreja alrededor del agujero del cuerpo [mm]", p.STE_lock_lobe_r - p.REV_lock_bore_d / 2, 6.0, ">="),
            ("dos trabas: ejes desfasados ≥ pomo + cuerpo del otro + 2 (pasan uno al lado del otro) [mm]",
             d12, 12.5 + RL.PLG_BODY_D / 2 + 2.0, ">=")]
