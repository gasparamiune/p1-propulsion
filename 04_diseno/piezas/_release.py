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
# guía del perno Ø16 (18), cámara del resorte (largo instalado 30; resorte SPRING_* más abajo: alambre 1,4, Ø ext 15,
# 6,5 espiras útiles, compacto ≈ 11,9 → con la carrera de 12 queda en 18 > compacto + holgura EN 13906-1), tapa (4) y
# pomo (10) apoyado en la tapa en reposo [CALCULADO/ESTIMADO: P1-REV-04]. El GN 617-10 de catálogo mide 80 mm (rosca 33
# + cuerpo y pomo 47): el émbolo real NO es corto.
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
# Resorte del émbolo P1-REV-04 (B-SPRING; re-auditoría ronda 5, DES-01): resorte de compresión inox de catálogo que
# ENTRA en la cámara (Ø ext ≤ 15 en el Ø16 H8, Ø int ≥ 11 sobre la cola Ø10) y no llega a compacto con la carrera.
# k = G·d⁴/(8·D³·n) (EN 13906-1); τ = 8·F·D/(π·d³) × k_Wahl.
SPRING_WIRE_D = 1.4     # alambre [SUPUESTO: elegido; EN 10270-3]
SPRING_OD = 15.0        # Ø exterior (Ø int 12,2) [SUPUESTO: elegido]
SPRING_NA = 6.5         # espiras útiles [SUPUESTO: elegido]
SPRING_N_END = 2.0      # espiras de apoyo (extremos cerrados y amolados) [SUPUESTO]
SPRING_L0 = 40.0        # largo libre [SUPUESTO: elegido]
SPRING_G = 70000.0      # módulo de corte [ESTIMADO: EN 13906-1/EN 10270-3: 1.4310 ≈ 70 GPa, 1.4401 ≈ 65–68 GPa (k −5 %)]
SPRING_RM = 1500.0      # Rm del alambre Ø1,4 [ESTIMADO: EN 10270-3, 1.4401 ≈ 1500–1800 MPa, 1.4310 ≈ 1850–2100 MPa]
SPRING_TAU_ZUL = 0.5 * SPRING_RM    # τ admisible estático [ESTIMADO: EN 13906-1, 0,5·Rm para inox de resorte]
SPRING_L_INST = PLG_SPRING_L1       # largo instalado (perno adentro, pomo apoyado en la tapa)
SPRING_L_MIN = PLG_SPRING_L1 - 12.0  # largo con el perno afuera (carrera REV_plunger_stroke = 12; check en P1-REV-09)


def spring_dm():
    return SPRING_OD - SPRING_WIRE_D


def spring_k():
    """Rigidez (N/mm) [CALCULADO: EN 13906-1 con SPRING_G ESTIMADO]."""
    return SPRING_G * SPRING_WIRE_D ** 4 / (8 * spring_dm() ** 3 * SPRING_NA)


def spring_F(L):
    return spring_k() * (SPRING_L0 - L)


def spring_L_solid():
    return (SPRING_NA + SPRING_N_END) * SPRING_WIRE_D


def spring_Sa():
    """Suma mínima de luces entre espiras al largo mínimo de trabajo [EN 13906-1: (0,0015·D²/d + 0,1·d)·n]."""
    return (0.0015 * spring_dm() ** 2 / SPRING_WIRE_D + 0.1 * SPRING_WIRE_D) * SPRING_NA


def spring_wahl():
    c = spring_dm() / SPRING_WIRE_D
    return (4 * c - 1) / (4 * c - 4) + 0.615 / c


def spring_tau(F, wahl=True):
    t = 8 * F * spring_dm() / (math.pi * SPRING_WIRE_D ** 3)
    return t * spring_wahl() if wahl else t


SPRING_F_MAX = spring_F(SPRING_L_MIN)      # ≈ 45 N con el perno afuera [CALCULADO: k ESTIMADO (G)]

# ---------------------------------------------------------------------------------------------------------------
# Desbloqueo (ronda 4, R4-06/R4-07): cada pomo se tira por un BALANCÍN de reenvío 1:1 (P1-REV-09) detrás de los émbolos
# (popa, X > collares de los émbolos), porque entre las orejas no cabe un tope de vaina coaxial con el pomo: la vaina tendría que
# girar 90° con R ≥ BOWDEN_R_MIN dentro de |Y| ≤ 53 (cara interior del brazo del bucket 56,5 − r de la vaina − 1)
# partiendo de |Y| ≥ 26 (pomo tirado + regulador) → faltan ≥ 3 mm [CALCULADO]. El pomo tira de un ESLABÓN RÍGIDO
# (re-auditoría ronda 5, DES-04: un lazo de cable crimpado de 10 mm no se puede fabricar): ojo de 316 con RANURA vertical
# en el perno de manivela + vástago M4 roscado en la cola del perno del émbolo (rosca M4 axial en la cola, P1-REV-04),
# fijado con Loctite 243: el largo se ajusta ±LINK_TOL al montar (medias vueltas = 0,35 mm, la ranura queda vertical) y
# la ranura absorbe el arco de la manivela (el eslabón queda coaxial con el émbolo: sin carga lateral sobre el perno).
# El balancín gira alrededor de un eje paralelo a X y su brazo de salida sube: el cable sale VERTICAL hacia el regulador
# M6 de la pestaña del soporte, y la vaina sube y se curva hacia proa por delante del barrido del bucket.
LINK_EYE_SLOT_W = 6.2   # ancho de la ranura del ojo (perno Ø6) [SUPUESTO]
LINK_EYE_WALL = 2.0     # pared del ojo alrededor de la ranura (316, flexión: check en P1-REV-09) [SUPUESTO]
LINK_EYE_T = 4.0        # espesor del ojo (X) [SUPUESTO]
LINK_SLOT = 1.75        # medio largo extra de la ranura (Z): absorbe el arco de la manivela [SUPUESTO]
LINK_EYE_HALF = LINK_EYE_SLOT_W / 2 + LINK_EYE_WALL       # eje del perno → extremo del ojo (5,1)
LINK_GAP = 3.15         # vástago M4 a la vista entre el ojo y la cara del pomo (ajuste ±LINK_TOL) [CALCULADO: manivela
#                         −Y tirada a ≥ 1,5 de la oreja +Y y manivelas a ≥ 1 de la base del soporte con el ajuste ±LINK_TOL]
LINK = LINK_EYE_HALF + LINK_GAP   # cara del pomo → eje del perno de manivela, en reposo [CALCULADO: ojo 5,1 + 3,15]
LINK_TOL = 0.75         # rango del ajuste del largo del eslabón (± 2 medias vueltas M4) [SUPUESTO: tolerancias de montaje]
LINK_SHANK_L = 12.0     # vástago M4 del ojo (rosca enganchada en la cola: 12 − LINK_GAP ∓ LINK_TOL ≥ 1,5·d) [SUPUESTO]
LEV_L = 14.0            # brazos del balancín (manivela = salida: 1:1) [CALCULADO: oreja +Y / brazo del bucket]
LEV_T = 5.0             # alma del balancín (Al 5083 fresado de placa de 12: alma 5 + cubos hacia proa) [SUPUESTO]
CRANK_D = 6.0           # perno de manivela 1.4401+C Ø6 m6 [CALCULADO: structural_direccion, filas P1-REV-09]
CRANK_SHOULDER = (9.0, 1.5)   # hombro del perno de manivela (Ø, largo) contra la cara del cubo [SUPUESTO]
CRANK_HUB_R = 4.5       # cubo de la manivela Ø9 (pared 1,5) [SUPUESTO]
CRANK_HUB_H = 7.0       # largo del cubo de la manivela hacia proa (perno prensado en LEV_T + 7 = 12 = 2·Ø) [CALCULADO: libra la oreja]
PIV_D = 7.0             # muñón del eje del balancín (perno fijo 1.4401+C: Ø8 m6 prensado en el montante, Ø7 f7 adelante)
PIV_STUD_D = 8.0        # parte del eje prensada en el montante [CALCULADO: structural_direccion, filas P1-REV-09]
PIV_BUSH_OD = 9.0       # casquillo polimérico autolubricado Ø7/Ø9 prensado en el cubo del eje [ESTIMADO: tipo iglidur, apto agua salada]
PIV_HUB_H = 9.0         # largo del cubo del eje hacia proa (apoyo LEV_T + 9 = 14 = 2·Ø) [CALCULADO: libra los collares]
LEV_GAP = 1.5           # alma del balancín ↔ montante (anillo DIN 6799 del perno de manivela + arandela PTFE 1 del eje)
UP_T = 8.0              # montante del soporte (Al 5083 8 mm: el eje Ø8 se prensa en él) [SUPUESTO]
CRANK_BOSS_R = 4.0      # alma alrededor del perno de manivela (el cable de salida pasa a ≥ 1) [SUPUESTO]
OUT_BOSS_R = 5.0        # alma del brazo de salida (terminal Ø5) [SUPUESTO]
PIV_BOSS_R = 7.0        # alma y cubo del eje del balancín (Ø14 sobre el casquillo Ø9) [SUPUESTO]
NIPPLE_R = 2.5          # terminal del cable (barril Ø5) en el brazo de salida [ESTIMADO: barril de Bowden Ø5 × 6]
ADJ_EDGE = 3.0          # borde de la pestaña alrededor del regulador M6 [SUPUESTO]
ADJ_HOLE_R = 3.25       # agujero roscado M6 de la pestaña (modelado Ø6,5)
TAB_T = 5.0             # pestañas del soporte (tope de las vainas)
NUT_R = PLG_COLLAR_D / 2      # radio máximo del collar del cuerpo del émbolo (P1-REV-04)
BOWDEN_D = 5.0          # vaina con camisa de PTFE Ø5 [ESTIMADO: B-BOWDEN]
BOWDEN_R_MIN = 30.0     # radio mínimo de curvatura de la vaina Ø5 con PTFE [ESTIMADO: ≈ 6 × Ø; ficha del fabricante a confirmar]
BOWDEN_R = 40.0         # radio usado en el modelo (≥ BOWDEN_R_MIN) [SUPUESTO]
BOWDEN_ETA = 0.6        # rendimiento del Bowden (≈ 300–360° de curvas, μ ≈ 0,08 cable/PTFE) [ESTIMADO: e^(−μθ)]
# Rendimiento del balancín (DES-03): el eslabón tira sobre el eje del émbolo, delante del alma del balancín, y el momento
# F·e fuera del plano lo toma el cubo del eje como un par de presiones → rozamiento del eje mucho mayor que el de F sola
LEV_MU_PIV = 0.10       # casquillo polimérico / muñón 316, mojado [ESTIMADO: 0,08–0,15]
LEV_MU_PIN = 0.15       # ojo del eslabón / perno y barril / brazo, 316 engrasado [ESTIMADO]


def lev_travel(p):
    """Recorrido de diseño de la manivela del balancín = carrera del émbolo (el pomo hace tope antes)."""
    return p.REV_plunger_stroke


def lever_x0(p):
    """Cara de proa del alma de los balancines: la pestaña del regulador del lado +Y queda ≥ 2 mm a popa del lóbulo de
    la oreja +Y (la vaina del émbolo −Y sube junto a esa oreja) y el cable sale por el plano medio del alma."""
    x_ear = max(lock_xz(p, s)[0] for s in lock_sides(p)) + p.STE_lock_lobe_r
    x_cable = x_ear + 2.0 + ADJ_EDGE + ADJ_HOLE_R
    return x_cable - LEV_T / 2


def cable_x(p):
    return lever_x0(p) + LEV_T / 2


def up_x(p):
    """Cara de proa del montante del soporte."""
    return lever_x0(p) + LEV_T + LEV_GAP


def lever(p, side=1):
    """Geometría del balancín del émbolo `side` en el plano YZ (marco de la boquilla). El pomo del émbolo +Y tira hacia −Y
    y el del −Y hacia +Y (d = −side). La manivela trabaja a la altura del eje del émbolo: el balancín +Y tiene su eje
    DEBAJO de la manivela y el −Y ENCIMA (la manivela a la altura del eje del émbolo en los extremos del recorrido y
    1,35 más arriba/abajo en el medio: lo absorbe la ranura del ojo del eslabón). En los dos el brazo de salida apunta
    a +Y, a 90° de la manivela, y SUBE lo mismo que corre el pomo (1:1). El eje se ubica con el eslabón NOMINAL (LINK).
    pose(t, link) con t = 0 reposo … 1 tirado (carrera del émbolo) y link = largo real del eslabón (por defecto LINK):
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

    def pose(t, link=LINK):
        dy = c0 + d * (link - LINK) + d * T * t - cm
        ang = math.atan2(sgn * math.sqrt(LEV_L ** 2 - dy ** 2), dy)
        a_out = ang - sgn * math.pi / 2
        return ((piv[0] + LEV_L * math.cos(ang), piv[1] + LEV_L * math.sin(ang)),
                (piv[0] + LEV_L * math.cos(a_out), piv[1] + LEV_L * math.sin(a_out)))
    return dict(side=side, lock=(lx, lz), d=d, piv=piv, sgn=sgn, pose=pose, T=T, c0=c0, cm=cm)


def link_lengths():
    """Largos del eslabón a revisar: extremos del ajuste y nominal."""
    return (LINK - LINK_TOL, LINK, LINK + LINK_TOL)


def lever_rise(p, side, knob_travel, link=LINK):
    """Subida de la salida del balancín (= cable que hay que tirar) para correr el pomo `knob_travel` mm."""
    L = lever(p, side)
    T = L["T"]
    return L["pose"](knob_travel / T, link)[1][1] - L["pose"](0.0, link)[1][1]


def cable_need(p):
    """Cable a tirar para liberar el brazo (RL.need), peor balancín y peor largo del eslabón [CALCULADO]."""
    return max(lever_rise(p, s, need(p), lk) for s in lock_sides(p) for lk in link_lengths())


def _socket(F, a, L, d):
    """Perno rígido en un agujero de largo L cargado por F a la distancia a FUERA de la cara (a < 0: dentro): presión
    proyectada lineal p(x) = p0 + p1·x [Shigley/Roark, perno empotrado]. Devuelve (p máx [MPa], Σ|N| [N])."""
    p0 = F / (d * L) * (4 + 6 * a / L)
    p1 = -F / (d * L * L) * (6 + 12 * a / L)
    n = 200
    s = sum(abs(p0 + p1 * (i + 0.5) * L / n) for i in range(n)) * d * L / n
    return max(abs(p0), abs(p0 + p1 * L)), s


def piv_hub(p):
    """(x proa, x popa, largo) del apoyo del balancín en su eje: cubo hacia proa + alma."""
    x0 = lever_x0(p)
    return x0 - PIV_HUB_H, x0 + LEV_T, PIV_HUB_H + LEV_T


def crank_hub(p):
    """(x proa, x popa, largo) del apoyo del perno de manivela en el balancín (prensado): cubo hacia proa + alma."""
    x0 = lever_x0(p)
    return x0 - CRANK_HUB_H, x0 + LEV_T, CRANK_HUB_H + LEV_T


def lever_bearing(p, side, F=1.0):
    """Cargas del eje del balancín `side` para un tiro F del eslabón (sobre el eje del émbolo, a lo largo de Y) y F del
    cable de salida (vertical, en el plano medio del alma; 1:1): presiones en el casquillo del cubo (p máx combinada) y
    Σ|N| para el rozamiento. Devuelve dict(a_link, p_max, N_sum)."""
    xf, xb, L = piv_hub(p)
    lx = lock_xz(p, side)[0]
    a_y = xf - lx                                         # eslabón: fuera del cubo, delante de su cara de proa
    a_z = xf - cable_x(p)                                 # cable de salida: dentro del cubo (a < 0)
    py, ny = _socket(F, a_y, L, PIV_D)
    pz, nz = _socket(F, a_z, L, PIV_D)
    return dict(a_link=a_y, p_max=math.hypot(py, pz), N_sum=ny + nz, L=L)


def lever_eta(p, side=None):
    """Rendimiento del balancín (peor de los dos si side es None) [CALCULADO con μ ESTIMADOS]: 1 − (rozamiento del eje con
    el par F·e + ojo del eslabón en el perno + barril en el brazo de salida) / (F·LEV_L)."""
    sides = lock_sides(p) if side is None else (side,)
    out = []
    for s in sides:
        b = lever_bearing(p, s, 1.0)
        tf = LEV_MU_PIV * PIV_D / 2 * b["N_sum"] + LEV_MU_PIN * (CRANK_D / 2 + NIPPLE_R)
        out.append(1.0 - tf / LEV_L)
    return min(out)


def cable_force_need(p):
    """Tiro por cable en el gatillo para sacar el perno con el resorte al final de la carrera [CALCULADO]."""
    return SPRING_F_MAX / (BOWDEN_ETA * lever_eta(p))


def cable_y(p, side=1):
    """Y de la línea del cable (vertical) que sale del brazo de salida: igual en reposo y tirado."""
    return lever(p, side)["pose"](0.0)[1][0]


def lever_top(p, side):
    """Z más alta del balancín `side` en todo su recorrido (cubos de la manivela, del eje y de la salida) y en todo el
    ajuste del eslabón."""
    L = lever(p, side)
    zs = [L["piv"][1] + PIV_BOSS_R]
    for lk in link_lengths():
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            (_, cz), (_, oz) = L["pose"](t, lk)
            zs += [cz + max(CRANK_BOSS_R, CRANK_HUB_R, CRANK_SHOULDER[0] / 2), oz + OUT_BOSS_R]
    return max(zs)


def stop_z(p):
    """Cara inferior de las pestañas del soporte (regulador M6), la misma para las dos vainas: sobre la salida más
    alta tirada + terminal + 4 y 2 mm sobre lo más alto de los balancines (la pestaña cruza su plano)."""
    return max(max(max(lever(p, s)["pose"](1.0, lk)[1][1] for lk in link_lengths()) + NIPPLE_R + 4.0,
                   lever_top(p, s) + 2.0) for s in lock_sides(p))


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
