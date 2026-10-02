"""P1-REV-04 — Émbolo de traba del bucket (×2), PROPIO: cuerpo y perno de AISI 316 torneados + resorte inox comprado.

Por qué propio (auditoría ronda 4): el émbolo de catálogo supuesto ("GN 617-12 M20 A4") no existe; el GN 617 inox
con rosca M20×1,5 trae perno Ø10 de AISI 303 que sobresale 10 mm (l2) y resorte 17–40 N [VERIFICADO: catálogo Elesa/Ganter
GN 617, pág. 809], y con una traba sola (M_h completo con R12, ≈ 3 kN en el perno) no llega a FS 2.

Geometría (marco local de la oreja +Y; la −Y es su espejo; medidas en piezas/_release.PLG_*): cuerpo Ø24 con rosca
M24×1,5 (REV_lock_thread_d) en la oreja (STE_ear_y0…STE_ear_y1), punta enrasada a la cara exterior; por dentro, el cuerpo tiene
un collar Ø36 (2 planos e/c 32) que apoya en la cara interior de la oreja y se aprieta a REV_lock_T_Nm con Loctite 243
(ubica la punta enrasada y toma el momento del perno sin que la unión se abra); adentro del cuerpo, la guía del perno (18 mm) y la cámara del resorte (largo instalado 30), cerrada por
una tapa roscada de 4 mm con agujero Ø10,2 para la cola Ø10 del perno; pomo Ø25 × 10 con ojal para el Bowden
(P1-REV-10), apoyado en la tapa en reposo. Perno Ø16 h9 (REV_lock_pin_d) que cruza la luz oreja–brazo y el brazo
(REV_t) y sobresale 1 mm de su cara exterior; el escalón Ø16 → Ø10 es el asiento del resorte. Carrera REV_plunger_stroke
(≥ recorrido para liberar el brazo + 2). Resorte inox de compresión (alambre 1,6, Ø ext 15, ~8 espiras útiles, largo
libre ≈ 40, k ≈ 2 N/mm → ≈ 20 N instalado y ≈ 44 N al final de la carrera) [ESTIMADO: como el GN 617-10; B-SPRING].
Traba ARRIBA y ABAJO (dos agujeros por brazo); se libera tirando del pomo con el Bowden desde el gatillo de la palanca del
bucket (P1-CTL-10/14); al soltar, el resorte lo mete (traba automática al llegar). DOS émbolos (qty 2), uno por oreja ±Y
(REV_n_locks): cada uno solo lleva todo M_h (los agujeros tienen juego: no hay reparto garantizado); el segundo es
redundancia. Los cuerpos llegan hasta el plano medio (Y = 0) y los dos émbolos pasan uno al lado del otro (ejes
desfasados: check)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-04", name="embolo",
    desc="Émbolo de traba propio: cuerpo M24×1,5 y perno Ø16 h9 en AISI 316 + resorte inox, uno por oreja ±Y",
    material="AISI 316", process="torneada", qty=2, frame="steer", group="jet",
    load_case="Perno Ø16: flexión + corte con M_h completo en una traba (R12) / REV_lock_r", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—",
)


def pin_tip_y(p):
    return RL.pin_tip_y(p)


def build(p):
    y0, y1 = p.STE_ear_y0, p.STE_ear_y1
    rt = p.REV_lock_thread_d / 2
    ysh = y1 - RL.PLG_GUIDE                                                     # escalón Ø16 → Ø10 (asiento del resorte)
    s = cyl_y(p.REV_lock_pin_d / 2, ysh, pin_tip_y(p))                         # perno Ø16 (guía + luz + brazo)
    s = s + cyl_y(rt - 0.1, y0, y1 + 0.01)                                       # rosca M24 en la oreja (modelada Ø23,8)
    s = s + cyl_y(RL.PLG_COLLAR_D / 2, y0 - RL.PLG_COLLAR_T, y0)                   # collar Ø36 (2 planos e/c 32), apoya en la oreja
    s = s + cyl_y(RL.PLG_BODY_D / 2, RL.body_end_y(p), y0 + 0.01)                # cuerpo Ø24 (cámara del resorte + tapa)
    s = s + cyl_y(12.5, RL.knob_end_y(p), RL.body_end_y(p) + 0.01)   # pomo Ø25
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
    znut = math.sqrt(max(p.STE_ro ** 2 - (p.STE_ear_y0 - RL.PLG_COLLAR_T) ** 2, 0.0))
    rt = p.REV_lock_thread_d / 2
    minor = p.REV_lock_thread_d - 1.6238 * 1.5                                   # Ø menor de la rosca M24×1,5 (ISO 724)
    sp_comp = RL.PLG_SPRING_L1 - p.REV_plunger_stroke                           # largo del resorte con el perno afuera
    d12 = math.dist(lock_xz(p, 1), lock_xz(p, -1)) if p.REV_n_locks > 1 else 99.0
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pomo (tirado) sobre el cuerpo de la boquilla [mm]", min(z, lock_xz(p, -1)[1]) - 12.5 - zbody, 2.0, ">="),
            ("collar del cuerpo sobre el cuerpo de la boquilla [mm]", (min(z, lock_xz(p, -1)[1]) - RL.PLG_COLLAR_D / 2) - znut, 2.0, ">="),
            ("perno sobresale de la cara exterior del brazo [mm]", pin_tip_y(p) - (p.REV_y_in + p.REV_t), 0.5, ">="),
            ("carrera ≥ recorrido para liberar el brazo + 2 [mm]", p.REV_plunger_stroke, RL.need(p) + 2.0, ">="),
            ("resorte con el perno afuera > largo compacto (≈ 16) + 1 [mm]", sp_comp, 17.0, ">="),
            ("holgura diametral perno ↔ agujero del brazo [mm]", p.REV_lock_hole_d - p.REV_lock_pin_d, 0.3, ">="),
            ("pared del cuerpo bajo la rosca sobre el perno [mm]", (minor - (p.REV_lock_pin_d + 0.2)) / 2, 2.5, ">="),
            ("ligamento de la oreja alrededor de la rosca [mm]", p.STE_lock_lobe_r - rt, 6.0, ">="),
            ("cuerpo del émbolo no cruza el plano medio (Y) [mm]", RL.body_end_y(p), -0.01, ">="),
            ("dos trabas: ejes desfasados ≥ pomo + cuerpo del otro + 2 (pasan uno al lado del otro) [mm]",
             d12, 12.5 + RL.PLG_BODY_D / 2 + 2.0, ">=")]
