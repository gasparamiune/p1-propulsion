"""_release.py — geometría de las trabas del bucket y de su desbloqueo (no es una pieza).

Fuente ÚNICA de la posición de los émbolos P1-REV-04 (la usan P1-REV-01/04/09/10, P1-STE-01, planos y FEA):
traba del brazo +Y a REV_lock_ang y del brazo −Y a REV_lock_ang_m, las dos a REV_lock_r del pivote del bucket
(marco de la boquilla, bucket ABAJO = posición en la que el émbolo entra en el agujero "abajo")."""
import math


def lock_ang(p, side=1):
    """Ángulo (°, desde +X hacia +Z) de la traba del brazo +Y (side > 0) o −Y (side < 0)."""
    return p.REV_lock_ang if side > 0 else p.REV_lock_ang_m


def lock_xz(p, side=1):
    """(X, Z) del eje del émbolo de la traba del brazo +Y (side > 0) o −Y (side < 0), marco de la boquilla."""
    a = math.radians(lock_ang(p, side))
    return (p.X_bucket_pivot + p.REV_lock_r * math.cos(a), p.Z_bucket_pivot + p.REV_lock_r * math.sin(a))


def lock_sides(p):
    """Brazos con traba: (+1,) o (+1, −1) según REV_n_locks."""
    return (1, -1) if p.REV_n_locks > 1 else (1,)


def mirror_loc(p):
    """Lleva la geometría construida alrededor de la traba +Y a la traba −Y (y → −y)."""
    from build123d import Pos, Rot
    x1, z1 = lock_xz(p, 1)
    x2, z2 = lock_xz(p, -1)
    return Pos(x2, 0, z2) * Rot(180, 0, 0) * Pos(-x1, 0, -z1)


# Émbolo propio P1-REV-04 (ronda 4), medidas a lo largo de su eje desde la cara EXTERIOR de la oreja hacia adentro:
# guía del perno Ø16 (18), cámara del resorte (largo instalado 30: alambre 1,6, Ø ext 15, ~8 espiras útiles, compacto
# ≈ 16 → con la carrera de 12 queda en 18 > 16), tapa (4) y pomo (10) apoyado en la tapa en reposo [CALCULADO/ESTIMADO:
# P1-REV-04]. El GN 617-10 de catálogo mide 80 mm (rosca 33 + cuerpo y pomo 47): el émbolo real NO es corto.
PLG_GUIDE = 18.0
PLG_SPRING_L1 = 30.0
PLG_CAP_T = 4.0
PLG_KNOB_L = 10.0
PLG_BODY_D = 24.0
# collar del cuerpo (en vez de contratuerca, ronda 4): Ø36 con 2 planos e/c 32 para la llave, apoya en la cara interior
# de la oreja; el cuerpo se aprieta contra él (REV_lock_T_Nm, Loctite 243): ubica la punta enrasada a la cara exterior y
# toma el momento del perno sin que la unión se abra (structural_direccion, P1-REV-04)
PLG_COLLAR_D = 36.0
PLG_COLLAR_T = 8.0
PLG_NUT_T = PLG_COLLAR_T      # (nombre histórico: zona del collar a lo largo del eje)


def body_end_y(p):
    """Cara trasera de la tapa del cuerpo del émbolo (lado +Y; el −Y es el espejo)."""
    return p.STE_ear_y1 - (PLG_GUIDE + PLG_SPRING_L1 + PLG_CAP_T)


def knob_end_y(p):
    return body_end_y(p) - PLG_KNOB_L          # cara del pomo en reposo (perno adentro); al tirar se corre −carrera


def pin_tip_y(p):
    return p.REV_y_in + p.REV_t + 1.0


def need(p):
    """Recorrido del pomo para sacar el perno del brazo del bucket (+0,5 de luz)."""
    return pin_tip_y(p) - (p.REV_y_in - 0.5)


# ---------------------------------------------------------------------------------------------------------------
# Desbloqueo (ronda 4, R4-06/R4-07): cada pomo se tira por un BALANCÍN de reenvío 1:1 (P1-REV-09) detrás de los émbolos
# (popa, X > contratuercas), porque entre las orejas no cabe un tope de vaina coaxial con el pomo: la vaina tendría que
# girar 90° con R ≥ BOWDEN_R_MIN dentro de |Y| ≤ 53 (cara interior del brazo del bucket 56,5 − r de la vaina − 1)
# partiendo de |Y| ≥ 26 (pomo tirado + regulador) → faltan ≥ 3 mm [CALCULADO]. El pomo tira de un eslabón corto de cable
# (LINK) enganchado en un perno de manivela Ø CRANK_D que sale del balancín hacia proa hasta el eje del émbolo; el
# balancín gira alrededor de un eje paralelo a X y su brazo de salida sube: el cable sale VERTICAL hacia el regulador M6
# de la pestaña del soporte, y la vaina sube y se curva hacia proa por delante del barrido del bucket.
LINK = 10.0             # cara del pomo → eje del perno de manivela, en reposo [SUPUESTO: terminal 4 + lazo de cable]
LEV_L = 14.0            # brazos del balancín (manivela = salida: 1:1) [CALCULADO: oreja +Y / brazo del bucket]
LEV_T = 5.0             # balancín Al 5083 5 mm [SUPUESTO]
CRANK_D = 6.0           # perno de manivela AISI 316 Ø6 [CALCULADO: structural_direccion, fila P1-REV-09]
PIV_D = 6.0             # tornillo con hombro ISO 7379 Ø6 × M5 (eje del balancín) [SUPUESTO]
CRANK_BOSS_R = 4.5      # cubo del balancín alrededor del perno de manivela (pared 1,5) [SUPUESTO]
OUT_BOSS_R = 5.0        # cubo del brazo de salida (terminal Ø5) [SUPUESTO]
PIV_BOSS_R = 6.0        # cubo del eje del balancín [SUPUESTO]
NIPPLE_R = 2.5          # terminal del cable (barril Ø5) en el brazo de salida [ESTIMADO: barril de Bowden Ø5 × 6]
ADJ_EDGE = 3.0          # borde de la pestaña alrededor del regulador M6 [SUPUESTO]
ADJ_HOLE_R = 3.25       # agujero roscado M6 de la pestaña (modelado Ø6,5)
TAB_T = 5.0             # pestañas del soporte (tope de las vainas)
NUT_R = PLG_COLLAR_D / 2      # radio máximo del collar del cuerpo del émbolo (P1-REV-04)
BOWDEN_D = 5.0          # vaina con camisa de PTFE Ø5 [ESTIMADO: B-BOWDEN]
BOWDEN_R_MIN = 30.0     # radio mínimo de curvatura de la vaina Ø5 con PTFE [ESTIMADO: ≈ 6 × Ø; ficha del fabricante a confirmar]
BOWDEN_R = 40.0         # radio usado en el modelo (≥ BOWDEN_R_MIN) [SUPUESTO]
SPRING_F_MAX = 45.0     # resorte del émbolo con el perno afuera [ESTIMADO: P1-REV-04, como el GN 617-10]
BOWDEN_ETA = 0.6        # rendimiento del Bowden (≈ 300–360° de curvas, μ ≈ 0,08 cable/PTFE) [ESTIMADO: e^(−μθ)]


def lev_travel(p):
    """Recorrido de diseño de la manivela del balancín = carrera del émbolo (el pomo hace tope antes)."""
    return p.REV_plunger_stroke


def lever_x0(p):
    """Cara de proa de los balancines: la pestaña del regulador del lado +Y queda ≥ 2 mm a popa del lóbulo de la oreja
    +Y (la vaina del émbolo −Y sube junto a esa oreja) y el cable sale por el plano medio del balancín."""
    x_ear = max(lock_xz(p, s)[0] for s in lock_sides(p)) + p.STE_lock_lobe_r
    x_cable = x_ear + 2.0 + ADJ_EDGE + ADJ_HOLE_R
    return x_cable - LEV_T / 2


def cable_x(p):
    return lever_x0(p) + LEV_T / 2


def lever(p, side=1):
    """Geometría del balancín del émbolo `side` en el plano YZ (marco de la boquilla). El pomo del émbolo +Y tira hacia −Y
    y el del −Y hacia +Y (d = −side). La manivela trabaja a la altura del eje del émbolo: el balancín +Y tiene su eje
    DEBAJO de la manivela (el perno pasa SOBRE la contratuerca del émbolo −Y; está a la altura del eje en los extremos
    del recorrido y 1,35 más arriba en el medio) y el −Y ENCIMA (el perno pasa BAJO la contratuerca del +Y; a la altura
    del eje en los extremos y 1,35 más abajo en el medio). En los dos el brazo de salida apunta a +Y, a 90° de la
    manivela, y SUBE lo mismo que corre el pomo (1:1). pose(t), t = 0 reposo … 1 tirado (carrera del émbolo):
    ((y, z) manivela, (y, z) salida)."""
    lx, lz = lock_xz(p, side)
    T = lev_travel(p)
    d = -1 if side > 0 else 1
    c0 = (knob_end_y(p) - LINK) if side > 0 else -(knob_end_y(p) - LINK)
    cm = c0 + d * T / 2
    h = math.sqrt(LEV_L ** 2 - (T / 2) ** 2)
    below = side > 0
    sgn = 1 if below else -1                           # manivela arriba (+1) o abajo (−1) del eje
    piv = (cm, lz - sgn * h)

    def pose(t):
        dy = c0 + d * T * t - cm
        ang = math.atan2(sgn * math.sqrt(LEV_L ** 2 - dy ** 2), dy)
        a_out = ang - sgn * math.pi / 2
        return ((piv[0] + LEV_L * math.cos(ang), piv[1] + LEV_L * math.sin(ang)),
                (piv[0] + LEV_L * math.cos(a_out), piv[1] + LEV_L * math.sin(a_out)))
    return dict(side=side, lock=(lx, lz), d=d, piv=piv, sgn=sgn, pose=pose, T=T)


def cable_y(p, side=1):
    """Y de la línea del cable (vertical) que sale del brazo de salida: igual en reposo y tirado."""
    return lever(p, side)["pose"](0.0)[1][0]


def lever_top(p, side):
    """Z más alta del balancín `side` en todo su recorrido (cubos de la manivela, del eje y de la salida)."""
    L = lever(p, side)
    zs = [L["piv"][1] + PIV_BOSS_R]
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        (_, cz), (_, oz) = L["pose"](t)
        zs += [cz + CRANK_BOSS_R, oz + OUT_BOSS_R]
    return max(zs)


def stop_z(p):
    """Cara inferior de las pestañas del soporte (regulador M6), la misma para las dos vainas: sobre la salida más
    alta tirada + terminal + 4 y 2 mm sobre lo más alto de los balancines (la pestaña cruza su plano)."""
    return max(max(lever(p, s)["pose"](1.0)[1][1] + NIPPLE_R + 4.0, lever_top(p, s) + 2.0) for s in lock_sides(p))


ADJ_BELOW = 2.0         # rosca del regulador que asoma bajo la pestaña
ADJ_NUT = (10.0, 4.0)       # contratuerca M6 del regulador (Ø modelado, alto)
ADJ_HEAD = (8.0, 8.0)       # cabeza del regulador con el casquillo de la vaina (Ø, alto) [ESTIMADO: regulador M6 de Bowden]


def sheath_path(p):
    """Línea media de la vaina del lado +Y (sale del regulador de la pestaña; marco de la boquilla, plano XZ en
    Y = cable_y): tramo vertical, curva de radio BOWDEN_R hacia proa (45°) y recta a 45° hasta Z_SHEATH_END, por
    delante del barrido de la cuchara (bucket arriba: labio en X ≈ 393, Z ≈ 172). La del −Y es la misma trasladada
    en Y (los dos reguladores están a la misma altura). Devuelve (x, z) de: inicio, inicio de la curva, fin de la
    curva, fin; y el centro de la curva."""
    xc = cable_x(p)
    z0 = stop_z(p) + TAB_T + ADJ_NUT[1] + ADJ_HEAD[1] + 0.05
    zb = z0 + 1.0
    R = BOWDEN_R
    cx, cz = xc - R, zb
    a = math.radians(45.0)
    xe, ze = cx + R * math.cos(a), cz + R * math.sin(a)
    zf = Z_SHEATH_END
    return dict(p0=(xc, z0), pb=(xc, zb), pe=(xe, ze), pf=(xe - (zf - ze), zf), c=(cx, cz))


Z_SHEATH_END = 180.0        # fin del tramo modelado: sobre los émbolos y por delante del bucket; sigue el bucle libre


# Pad de fijación del soporte P1-REV-09 sobre el cuerpo de la boquilla (P1-STE-01), a popa de los émbolos (R4-07):
# cara plana fresada, 2 roscas M5 × 7,5 (taladro Ø4,2 × 9), lejos de los ligamentos del pivote y de las roscas M24.
PAD_W = 12.0            # semiancho del pad y de la base [CALCULADO: libra los balancines (|Y| ≥ 15) y los M5 a ±6 con borde 6]
PAD_H = 6.5             # cara superior del pad a r_ext + 6,5 [SUPUESTO: la base libra el cuerpo; piel bajo los M5 ≥ 2]
PAD_M5_THREAD = 7.5     # rosca M5 útil (1,5·d) [SUPUESTO]
PAD_M5_DRILL = 9.0      # profundidad del taladro Ø4,2


def pad_x(p):
    """(X0, X1) del pad: 3,8 mm a popa del pomo Ø25 del émbolo más bajo (el que pasa junto al cuerpo); hasta 1,2 mm
    antes de la salida (chaflán)."""
    lo = min(lock_sides(p), key=lambda s: lock_xz(p, s)[1])
    x0 = lock_xz(p, lo)[0] + 12.5 + 3.8
    return (round(x0, 1), round(p.STE_X_exit - 1.2, 1))


def pad_screws(p):
    x0 = pad_x(p)[0]
    return ((x0 + 6.0, -6.0), (x0 + 6.0, 6.0))


def pad_z(p):
    return p.STE_ro + PAD_H


def pad_box(p):
    """Pad que agrega P1-STE-01 (se une antes de taladrar el paso del chorro)."""
    from cadlib import box
    x0, x1 = pad_x(p)
    return box(x0, x1, -PAD_W, PAD_W, p.STE_rb + 1.0, pad_z(p))


def pad_holes(p):
    """Taladros Ø4,2 × PAD_M5_DRILL de las roscas M5 del pad (los resta P1-STE-01)."""
    from cadlib import cyl_z
    zt = pad_z(p)
    s = None
    for (x, y) in pad_screws(p):
        c = cyl_z(2.1, zt - PAD_M5_DRILL, zt + 1.0, x=x, y=y)
        s = c if s is None else s + c
    return s
