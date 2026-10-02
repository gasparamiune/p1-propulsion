"""P1-CTL-14 — Gatillo de liberación de las trabas (Al 6061-T6 6 mm) con BARRA IGUALADORA de los dos Bowden.

Ronda 4 (R4-06): el gatillo gira en un pasador Ø5 A4 que atraviesa la placa lateral del mango (P1-CTL-10) y el mango;
la hoja sube por delante del mango (los dedos la traen hacia el mango) y el brazo inferior lleva, en un pasador Ø4,
la barra igualadora (316, 5 × 4 × 24): los dos cables (uno por émbolo P1-REV-04, vía los balancines 1:1 de P1-REV-09)
se enganchan con su terminal en las ranuras de los extremos de la barra (a ±8 del pasador) y salen hacia popa a las
dos vainas, que apoyan en la pestaña de tope de la placa lateral del mango. La barra gira libre: reparte la fuerza
del gatillo por igual entre los dos cables aunque tengan distinto largo/juego (los reguladores M6 de P1-REV-09 quitan
el juego al montar) y aunque un émbolo quede trabado (la barra gira hasta que el otro llega al final de su carrera:
cada cable lleva como máximo la mitad del tiro del gatillo). Retorno: resorte de torsión del gatillo + resortes de los
émbolos. Se mueve con la palanca (estados del bucket).

Cadena de fuerzas (re-auditoría ronda 5, DES-01/DES-03): el tiro por cable que da la mano de diseño (con el rendimiento
del gatillo TRIG_ETA) tiene que llegar al resorte del émbolo al final de su carrera (_release.SPRING_F_MAX) a través del
Bowden (BOWDEN_ETA) y del balancín de P1-REV-09, cuyo eje toma el par F·e del eslabón (_release.lever_eta). Para eso el
brazo del cable es más corto (R_W 17,5) y el giro mayor (50°): la relación mano → cable sube sin pasar 30 mm de dedos."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y, prism_xz  # noqa: E402
from _dir_common import circ, hull  # noqa: E402
import _ctl as U  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-CTL-14", name="gatillo",
    desc="Gatillo del desbloqueo (Al 6061 6 mm) con barra igualadora 316 de los dos Bowden",
    material="Al 6061-T6", process="torneada", qty=1, frame="bucket", group="ele",
    load_case="Apriete de la mano 100 N [SUPUESTO] en la hoja; tiro de los dos cables por la barra igualadora",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="Corte láser 6 mm + barra 316 mecanizada",
)
Y0, Y1 = 37.5, 43.5          # gatillo, por fuera de la placa lateral del mango (P1-CTL-10, y 33–37)
BAR_Y = (44.0, 48.0)         # barra igualadora (y); los cables van en y = 46
PIV = (0.0, 106.0)           # pasador Ø5 en el mango (x, z local) [CALCULADO: borde ≥ 3,5 en el mango 16 × 35]
PIV_D = 5.0
R_W = 17.5                   # pasador de la barra a 17,5 mm del pivote [CALCULADO: recorrido ≥ liberación + 3 + 2]
ANG = 50.0                   # giro del gatillo (reposo → apretado) [CALCULADO: relación mano → cable con ≤ 30 mm de dedos]
R_F = 35.4                   # punto de apoyo de los dedos a 35,4 mm del pivote (recorrido de los dedos ≤ 30)
BETA0 = 52.0                 # hoja en reposo: 52° desde la vertical hacia proa (apretada: 2°)
TRIG_ETA = 0.95              # rendimiento del gatillo (pasador Ø5 + pasador de la barra, engrasados) [ESTIMADO]
BAR_H = 8.0                  # cables a ±8 del pasador de la barra
BAR_L = 24.0
BAR_T = 5.0                  # espesor de la barra (x)


def wire_pt(a):
    """Pasador de la barra con el gatillo girado a (0 reposo … ANG apretado): el brazo cuelga a ±ANG/2 de la vertical
    (la cuerda es horizontal: el cable sale recto a popa)."""
    g = math.radians(-ANG / 2 + a)
    return (PIV[0] + R_W * math.sin(g), PIV[1] - R_W * math.cos(g))


def finger_pt(a):
    b = math.radians(BETA0 - a)
    return (PIV[0] + R_F * math.sin(b), PIV[1] + R_F * math.cos(b))


def travel():
    return 2 * R_W * math.sin(math.radians(ANG / 2))


def outline():
    """Contornos (x, z) del gatillo en reposo: hoja (pivote → apoyo de los dedos) y brazo de la barra."""
    w = wire_pt(0.0)
    f = finger_pt(0.0)
    b = math.radians(BETA0)
    blade = hull(circ(PIV[0], PIV[1], 7.0) + circ(f[0], f[1], 6.0) + [(f[0] + 8 * math.sin(b), f[1] + 8 * math.cos(b))])
    arm = hull(circ(PIV[0], PIV[1], 7.0) + circ(w[0], w[1], 5.0))
    return blade, arm


def build_local(p):
    w = wire_pt(0.0)
    blade, arm = outline()
    s = prism_xz(blade, Y0, Y1) + prism_xz(arm, Y0, Y1)
    s = s - cyl_y(PIV_D / 2 + 0.1, Y0 - 1, Y1 + 1, x=PIV[0], z=PIV[1])
    # barra igualadora en su pasador Ø4 (giro libre; modelada en reposo, cables iguales)
    s = s + cyl_y(2.0, Y0 + 0.5, BAR_Y[1], x=w[0], z=w[1])
    s = s + box(w[0] - BAR_T / 2, w[0] + BAR_T / 2, BAR_Y[0], BAR_Y[1], w[1] - BAR_L / 2, w[1] + BAR_L / 2)
    for dz in (-BAR_H, BAR_H):                                           # ranuras de los terminales de los cables
        s = s - box(w[0] - BAR_T / 2 - 1, w[0] + BAR_T / 2 + 1, (BAR_Y[0] + BAR_Y[1]) / 2 - 0.9,
                    (BAR_Y[0] + BAR_Y[1]) / 2 + 0.9, w[1] + dz - 0.9, w[1] + dz + 0.9)
    return s


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    th = -p.CTL_bkt_travel if bucket else 0.0
    x, y, z = p.CTL_axis
    return [Pos(x, y, z) * Rot(0, th, 0) * Pos(-x, -y, -z)]


def cable_pull_max(p):
    """Tiro máximo por cable (N) con la mano de diseño SIN rozamiento (carga de diseño de las piezas): momento de la mano /
    brazo del cable en el extremo del recorrido, repartido en 2 por la barra igualadora."""
    arm = R_W * math.cos(math.radians(ANG / 2))
    return p.CTL_hand_F * R_F / arm / max(len(RL.lock_sides(p)), 1)


def cable_pull_design(p):
    """Tiro por cable (N) que da la mano de diseño descontando el rozamiento del gatillo (TRIG_ETA [ESTIMADO])."""
    return cable_pull_max(p) * TRIG_ETA


def checks(p, part):
    need = RL.cable_need(p)                  # cable que hay que tirar para liberar (balancín 1:1, peor ajuste del eslabón)
    tr = travel()
    w0, w1 = wire_pt(0.0), wire_pt(ANG)
    f_need = RL.cable_force_need(p)          # resorte final / (η Bowden · η balancín)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("recorrido del cable con el gatillo apretado ≥ liberación + 3 de juego (pomo apoyado en la tapa) [mm]", tr, need + 3.0, ">="),
            ("sobrecarrera más allá de liberación + 3 [mm]", tr - (need + 3.0), 2.0, ">="),
            ("cable sale recto: desnivel del pasador de la barra entre reposo y apretado [mm]", abs(w1[1] - w0[1]), 0.1, "<="),
            ("igualador: giro de la barra para compensar una carrera completa del émbolo [°]",
             math.degrees(math.asin(min(p.REV_plunger_stroke / (2 * BAR_H), 1.0))), 60.0, "<="),
            ("tiro por cable con la mano de diseño × η gatillo ≥ resorte final / (η Bowden · η balancín) [N]",
             cable_pull_design(p), f_need, ">="),
            ("rendimiento del balancín de P1-REV-09 (par F·e en el eje; μ ESTIMADOS) [-]", RL.lever_eta(p), 0.7, ">="),
            ("recorrido de los dedos en la hoja [mm]", 2 * R_F * math.sin(math.radians(ANG / 2)), 30.0, "<="),
            ("hoja apretada sin pasar la vertical (no toca el mango) [°]", BETA0 - ANG, 0.0, ">="),
            ("separación de la placa lateral del mango (y) [mm]", Y0 - 37.0, 0.3, ">=")]
