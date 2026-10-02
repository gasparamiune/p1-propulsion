"""P1-REV-09 — Soporte de reenvío del desbloqueo (frame steer): placa base 6 + montante 8 Al 5083 soldados, con DOS
balancines de reenvío 1:1 (Al 5083 fresados) y las pestañas de los reguladores M6 de las dos vainas del Bowden (P1-REV-10).

Por qué un reenvío (auditoría ronda 4, R4-06): con el émbolo propio (cuerpo hasta Y = 0, pomo Ø23 que baja 12 mm
hacia el plano medio) no cabe un tope de vaina coaxial con el pomo entre las orejas: desde el pomo tirado
(|Y| ≈ 22) + el regulador, la vaina tendría que girar 90° con R ≥ _release.BOWDEN_R_MIN antes de la cara interior del
brazo del bucket (|Y| 56,5) [CALCULADO: _release]. Cada pomo tira de un ESLABÓN RÍGIDO (re-auditoría ronda 5, DES-04):
ojo de 316 con ranura vertical en el perno de manivela Ø6 de su balancín + vástago M4 roscado en la cola del perno del
émbolo (Loctite 243), largo ajustable ±_release.LINK_ADJ al montar (la cinemática
se revisa con un desajuste residual ±_release.LINK_TOL). El balancín gira en un eje fijo 1.4401+C (Ø8 prensado
en el montante, muñón Ø7 con casquillo polimérico en el cubo del balancín) y su brazo de salida SUBE lo mismo que corre
el pomo; el cable del Bowden sale vertical desde el terminal (barril Ø5) hasta el regulador M6 de la pestaña y la vaina
sigue hacia arriba y a proa (P1-REV-10).

Momento fuera del plano (re-auditoría ronda 5, DES-03): el eslabón tira sobre el eje del émbolo, 17–20 mm delante del
cubo del balancín → par F·e. Lo toman CUBOS largos hacia proa (fresados con el balancín de placa de 12: eje con apoyo de
14 = 2·Ø, perno de manivela prensado H7/m6 en 12 con Loctite 638 y hombro Ø9 adelante; anillo DIN 6799 delante
del ojo del eslabón) y el eje Ø8 prensado en el
montante de 8; las presiones y el rozamiento del eje (rendimiento del balancín, _release.lever_eta) están en
structural_direccion (filas P1-REV-09) y en el check de fuerza del gatillo P1-CTL-14.
Los balancines están a popa de los retenes interiores (anillos DIN 471) de los émbolos; el del émbolo +Y tiene el eje DEBAJO de la manivela y el
del −Y ENCIMA.

Fijación (R4-07): la placa base apoya de cara sobre un PAD fresado en la parte superior del cuerpo de la boquilla
(P1-STE-01, a popa de los émbolos, X 399–426,5) y se atornilla con 2 × ISO 4762 M5 × 12 A4-70 en roscas M5 × 7,5 del
pad (Tef-Gel; arandela de nylon bajo la cabeza). Lejos de los ligamentos del pivote y de los agujeros Ø24 de los émbolos en las orejas.
Modelo: el conjunto (soporte soldado + ejes + balancines + pernos + eslabones + tramo de cable hasta el regulador +
tornillos) es UN sólido en REPOSO (bucket trabado, cables flojos; el ojo del eslabón se modela macizo alrededor del
perno); los checks verifican también la posición TIRADA y los dos extremos del ajuste del eslabón."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_x, cyl_y, cyl_z, prism_yz  # noqa: E402
from _dir_common import circ, hull  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-09", name="soporte_bowden",
    desc="Soporte de reenvío del desbloqueo: base + montante Al 5083 soldados, 2 balancines 1:1 y 2 pestañas de reguladores M6",
    material="Al 5083", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Tiro de diseño por cable (mano 100 N en el gatillo P1-CTL-14 repartida por el igualador) [CALCULADO]",
    print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Chapa cortada y soldada (base 6 + montante 8 + pestañas 5); balancines fresados de placa de 12",
)
BASE_T = 6.0          # placa base [SUPUESTO]
UP_T = RL.UP_T        # montante (el eje del balancín Ø8 se prensa en él)
BASE_W = RL.PAD_W      # semiancho de la base (= pad de la boquilla)
M5_DRILL = RL.PAD_M5_DRILL
SCREW_L = 12.0        # ISO 4762 M5 × 12: 6 mm de rosca en el pad (rosca de 7,5, taladro de 9: no toca fondo)
pad_z = RL.pad_z
GAP = RL.LEV_GAP      # luz alma del balancín ↔ montante
CLIP = 1.5            # muñón / perno que asoma por delante del cubo para el anillo DIN 6799
CLIP_R = 6.0          # radio exterior del anillo DIN 6799 del muñón Ø7 (modelo de holgura) [ESTIMADO]


def up_x(p):
    return RL.up_x(p)


def link_solid(p, side, t=0.0, link=RL.LINK):
    """Eslabón rígido (modelo): ojo macizo (ranura no modelada) alrededor del perno de manivela + vástago M4 hasta la cara
    del pomo (pose t, largo `link`)."""
    lx, lz = RL.lock_xz(p, side)
    sg = 1 if side > 0 else -1
    kf = sg * (RL.knob_end_y(p) - t * RL.lev_travel(p))                 # cara del pomo
    cy = kf - sg * link                                                  # eje del perno de manivela (Y)
    hz = RL.LINK_EYE_SLOT_W / 2 + RL.LINK_SLOT + RL.LINK_EYE_WALL
    e = box(lx - RL.LINK_EYE_T / 2, lx + RL.LINK_EYE_T / 2, cy - RL.LINK_EYE_HALF, cy + RL.LINK_EYE_HALF, lz - hz, lz + hz)
    ya, yb = cy + sg * (RL.LINK_EYE_HALF - 0.01), kf - sg * 0.01
    e = e + cyl_y(2.0, min(ya, yb), max(ya, yb), x=lx, z=lz)               # vástago M4
    return e


def lever_solid(p, side, t=0.0, link=RL.LINK):
    """Balancín (alma + cubos) + perno de manivela + eslabón (en la pose t) + terminal y tramo de cable de salida."""
    L = RL.lever(p, side)
    (cy, cz), (oy, oz) = L["pose"](t, link)
    py, pz = L["piv"]
    x0, x1 = RL.lever_x0(p), RL.lever_x0(p) + RL.LEV_T
    lx, lz = L["lock"]
    s = prism_yz(hull(circ(cy, cz, RL.CRANK_BOSS_R) + circ(py, pz, RL.PIV_BOSS_R) + circ(oy, oz, RL.OUT_BOSS_R)), x0, x1)
    s = s + cyl_x(RL.PIV_BOSS_R, RL.piv_hub(p)[0], x0 + 0.01, y=py, z=pz)               # cubo del eje (hacia proa)
    xc = RL.crank_hub(p)[0]
    s = s + cyl_x(RL.CRANK_HUB_R, xc, x0 + 0.01, y=cy, z=cz)                            # cubo de la manivela
    s = s + cyl_x(RL.CRANK_SHOULDER[0] / 2, xc - RL.CRANK_SHOULDER[1], xc + 0.01, y=cy, z=cz)   # hombro del perno
    s = s + cyl_x(RL.CRANK_D / 2, lx - RL.CRANK_FRONT, x1, y=cy, z=cz)                             # perno de manivela Ø6
    s = s + link_solid(p, side, t, link)
    # terminal (barril Ø5 a lo largo de X) y cable vertical hasta 0,3 mm bajo el regulador (sigue por dentro: P1-REV-10)
    s = s + cyl_x(RL.NIPPLE_R, x0 - 0.5, x1 + 0.5, y=oy, z=oz)
    s = s + cyl_z(0.75, oz, RL.stop_z(p) - RL.ADJ_BELOW - 0.3, x=RL.cable_x(p), y=oy)
    return s


TAB_HW = 7.0          # medio ancho de las pestañas de los reguladores


def upright_outline(p):
    """Contorno (y, z) del montante: base, cubos de los ejes de los balancines (r 8) y pestañas de los reguladores."""
    zb = pad_z(p) + BASE_T
    zs = RL.stop_z(p)
    pts = [(-BASE_W, zb - 0.5), (BASE_W, zb - 0.5)]
    for sd in RL.lock_sides(p):
        L = RL.lever(p, sd)
        pts += circ(L["piv"][0], L["piv"][1], 8.0)
        yc = RL.cable_y(p, sd)
        pts += [(yc - TAB_HW, zs), (yc + TAB_HW, zs), (yc - TAB_HW, zs + RL.TAB_T), (yc + TAB_HW, zs + RL.TAB_T)]
    return hull(pts)


def lever_outline(p):
    """Contorno del alma del balancín en su propio marco (eje en el origen, manivela en +v, salida en +u): los dos son
    iguales (el del émbolo −Y es el mismo dado vuelta)."""
    return hull(circ(0.0, RL.LEV_L, RL.CRANK_BOSS_R) + circ(0.0, 0.0, RL.PIV_BOSS_R) + circ(RL.LEV_L, 0.0, RL.OUT_BOSS_R))


def crank_pin_len(p, side):
    """Largo del perno de manivela: CRANK_FRONT delante del eje del émbolo (medio ojo + ranura y anillo DIN 6799 + borde)
    … a ras de la cara de popa del alma (prensado H7/m6 + Loctite 638 contra el hombro: la carga es radial)."""
    return RL.lever_x0(p) + RL.LEV_T - (RL.lock_xz(p, side)[0] - RL.CRANK_FRONT)


def pivot_len(p):
    """Largo del eje del balancín: CLIP delante del cubo … cara de popa del montante (prensado a ras)."""
    return up_x(p) + UP_T - (RL.piv_hub(p)[0] - CLIP)


def bracket(p):
    """Soporte soldado (base + montante + pestañas) con los ejes de los balancines y los M5 de la base."""
    zp = pad_z(p)
    zb = zp + BASE_T
    ux = up_x(p)
    xc = RL.cable_x(p)
    zs = RL.stop_z(p)
    sides = RL.lock_sides(p)
    px = RL.pad_x(p)
    s = box(px[0] + 0.5, px[1], -BASE_W, BASE_W, zp, zb)                         # base sobre el pad
    s = s + prism_yz(upright_outline(p), ux, ux + UP_T)                                   # montante
    for sd in sides:
        yc = RL.cable_y(p, sd)
        tab = box(xc - RL.ADJ_HOLE_R - RL.ADJ_EDGE, ux + 0.01, yc - TAB_HW, yc + TAB_HW, zs, zs + RL.TAB_T)
        s = s + tab - cyl_z(RL.ADJ_HOLE_R, zs - 1, zs + RL.TAB_T + 1, x=xc, y=yc)        # pestaña + M6 del regulador
        py, pz = RL.lever(p, sd)["piv"]
        s = s + cyl_x(RL.PIV_STUD_D / 2, ux - 0.01, ux + UP_T, y=py, z=pz)                # eje Ø8 prensado en el montante
        s = s + cyl_x(RL.PIV_D / 2, RL.piv_hub(p)[0] - CLIP, ux + 0.01, y=py, z=pz)       # muñón Ø7
    for (x, y) in RL.pad_screws(p):                                                       # 2 × ISO 4762 M5 × 12
        s = s + cyl_z(2.0, zb - SCREW_L, zb, x=x, y=y) + cyl_z(4.25, zb, zb + 5.0, x=x, y=y)
    return s


def build(p, t=0.0):
    s = bracket(p)
    for sd in RL.lock_sides(p):
        s = s + lever_solid(p, sd, t)
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def _other(stem):
    import importlib.util
    f = os.path.join(os.path.dirname(__file__), stem + ".py")
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pulled_interference(p):
    """Volumen (mm³) de los balancines/eslabones TIRADOS (carrera completa del émbolo, eslabón en su largo MÁXIMO del
    ajuste: manivelas más cerca de las orejas) contra los émbolos (cuerpo, tramo ajustado, anillo DIN 471; pomo tirado) y la boquilla."""
    from build123d import Pos, Rot
    m4 = _other("P1-REV-04_embolo")
    e = m4.build(p)
    obst = []
    for sd in RL.lock_sides(p):
        x, z = RL.lock_xz(p, sd)
        loc = Pos(x, 0, z) if sd > 0 else Pos(x, 0, z) * Rot(180, 0, 0)
        obst.append(loc * (e - cyl_y(12.6, RL.knob_end_y(p) - 0.01, RL.body_end_y(p) - 0.01)))   # sin el pomo en reposo
        kz = RL.knob_end_y(p) - RL.lev_travel(p)
        k = cyl_y(RL.PLG_KNOB_D / 2, kz, kz + RL.PLG_KNOB_L)                                     # pomo tirado
        obst.append(Pos(x, 0, z) * k if sd > 0 else Pos(x, 0, z) * Rot(180, 0, 0) * k)
    obst.append(_other("P1-STE-01_boquilla").build(p))
    v = 0.0
    for sd in RL.lock_sides(p):
        lv = lever_solid(p, sd, 1.0, RL.LINK + RL.LINK_TOL)
        for o in obst:
            try:
                v += (lv & o).volume
            except Exception:                         # noqa: BLE001
                v += 0.0
    return v


# ------------------------------------------------------------------ holguras (geometría analítica, plano XZ por franja de Y)
def _seg_dist(a, b, c, d):
    """Distancia entre los segmentos 2D ab y cd."""
    def pt_seg(p_, a_, b_):
        ax, az = a_
        bx, bz = b_
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p_[0] - ax) * dx + (p_[1] - az) * dz) / L2))
        return math.hypot(p_[0] - ax - u * dx, p_[1] - az - u * dz)

    def cross(o, p_, q):
        return (p_[0] - o[0]) * (q[1] - o[1]) - (p_[1] - o[1]) * (q[0] - o[0])
    d1, d2 = cross(a, b, c), cross(a, b, d)
    d3, d4 = cross(c, d, a), cross(c, d, b)
    if d1 * d2 < 0 and d3 * d4 < 0:
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


def _inside(pt, poly):
    x, z = pt
    c = False
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            c = not c
    return c


def _rect_poly_clear(rect, poly):
    """Holgura entre un rectángulo (x0, x1, z0, z1) y un polígono convexo (lista (x, z)); < 0 si se tocan."""
    x0, x1, z0, z1 = rect
    rp = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    if any(_inside(q, poly) for q in rp) or any(x0 <= q[0] <= x1 and z0 <= q[1] <= z1 for q in poly):
        return -1.0
    return min(_seg_dist(rp[i], rp[(i + 1) % 4], poly[j], poly[(j + 1) % len(poly)])
               for i in range(4) for j in range(len(poly)))


def _rect_circle_clear(rect, c, R):
    x0, x1, z0, z1 = rect
    dx = max(x0 - c[0], 0.0, c[0] - x1)
    dz = max(z0 - c[1], 0.0, c[1] - z1)
    return math.hypot(dx, dz) - R


def _xcyl_rect(yc, zc, r, x0, x1, yr):
    """Sección XZ (rectángulo) de un cilindro de eje X (y = yc, z = zc, radio r, x0…x1) dentro de la franja Y yr = (ya, yb):
    None si no la toca."""
    ya, yb = yr
    if yc + r <= ya or yc - r >= yb:
        return None
    yn = min(max(yc, ya), yb)
    w = math.sqrt(max(r * r - (yn - yc) ** 2, 0.0))
    return (x0, x1, zc - w, zc + w)


def _moving_rects(p, side, t, link):
    """Lo que se mueve con el balancín `side` en la pose (t, link): [(nombre, (yc, zc, r, x0, x1))] de cilindros de eje X
    y, al final, ("ojo del eslabón", (y0, y1, rectángulo XZ))."""
    L = RL.lever(p, side)
    (cy, cz), _ = L["pose"](t, link)
    lx, lz = L["lock"]
    xc = RL.crank_hub(p)[0]
    hz = RL.LINK_EYE_SLOT_W / 2 + RL.LINK_SLOT + RL.LINK_EYE_WALL
    return [("cubo de la manivela", (cy, cz, RL.CRANK_HUB_R, xc, RL.lever_x0(p))),
            ("hombro del perno", (cy, cz, RL.CRANK_SHOULDER[0] / 2, xc - RL.CRANK_SHOULDER[1], xc)),
            ("perno de manivela", (cy, cz, RL.CRANK_D / 2, lx - RL.CRANK_FRONT, xc)),
            ("ojo del eslabón", (cy - RL.LINK_EYE_HALF, cy + RL.LINK_EYE_HALF,
                                 (lx - RL.LINK_EYE_T / 2, lx + RL.LINK_EYE_T / 2, lz - hz, lz + hz)))]


def _obstacles(p):
    """Obstáculos fijos o de los émbolos: (nombre, (y0, y1), ('c', centro xz, R) | ('p', polígono xz), lado del pomo).
    Pomos en reposo y tirados (el del OTRO émbolo puede estar en cualquiera de los dos; el propio va con su eslabón y
    su luz es el check de LINK_GAP)."""
    import importlib.util
    f = os.path.join(os.path.dirname(__file__), "P1-STE-01_boquilla.py")
    spec = importlib.util.spec_from_file_location("ste01_clear", f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = []
    for sd in RL.lock_sides(p):
        x, z = RL.lock_xz(p, sd)
        tg = "+Y" if sd > 0 else "−Y"
        rng = lambda a, b: (min(sd * a, sd * b), max(sd * a, sd * b))   # noqa: E731
        out.append((f"cuerpo del émbolo {tg}", rng(RL.body_end_y(p), p.STE_ear_y0), ("c", (x, z), RL.PLG_BODY_D / 2), 0))
        yl0 = p.STE_lock_y1 - p.STE_lock_t                   # cara interior del lóbulo engrosado de la traba (R5-N5)
        out.append((f"lóbulo engrosado de la traba {tg}", rng(yl0, p.STE_ear_y0), ("p", m.hull(m.inner_boss_outline(p, sd))), 0))
        out.append((f"tramo ajustado Ø{p.REV_lock_bore_d:g} del émbolo {tg}", rng(yl0 - RL.PLG_FIT_EXT, yl0),
                    ("c", (x, z), p.REV_lock_bore_d / 2), 0))
        out.append((f"anillo DIN 471 del émbolo {tg}", rng(yl0 - RL.PLG_NUT_T, yl0), ("c", (x, z), RL.NUT_R), 0))
        out.append((f"lóbulo engrosado del pivote {tg}", rng(p.STE_ear_y1 - p.STE_piv_t, p.STE_ear_y0),
                    ("c", (p.X_bucket_pivot, p.Z_bucket_pivot), p.STE_ear_r), 0))
        k0 = RL.knob_end_y(p)
        out.append((f"pomo {tg} (reposo)", rng(k0, k0 + RL.PLG_KNOB_L), ("c", (x, z), RL.PLG_KNOB_D / 2), sd))
        k1 = k0 - RL.lev_travel(p)
        out.append((f"pomo {tg} (tirado)", rng(k1, k1 + RL.PLG_KNOB_L), ("c", (x, z), RL.PLG_KNOB_D / 2), sd))
        out.append((f"oreja {tg}", rng(p.STE_ear_y0, p.STE_ear_y1), ("p", m.ear_outline(p, sd)), 0))
    return out


def clearances(p):
    """Holgura mínima (mm) de cubos, pernos y ojos de los balancines contra émbolos y orejas, en reposo y tirado, en los
    dos extremos del ajuste del eslabón; y de los cubos de los ejes (fijos). Devuelve (holgura, descripción)."""
    obst = _obstacles(p)
    best = (99.0, "—")

    def test(name, item, pose_txt, own=0):
        nonlocal best
        if len(item) == 3:
            y0, y1, rect0 = item
            yr_item = (y0, y1)
        for oname, (ya, yb), geo, knob_side in obst:
            if own and knob_side == own:
                continue
            if len(item) == 5:
                rect = _xcyl_rect(item[0], item[1], item[2], item[3], item[4], (ya, yb))
                if rect is None:
                    continue
            else:
                if yr_item[1] <= ya or yr_item[0] >= yb:
                    continue
                rect = rect0
            c = _rect_circle_clear(rect, geo[1], geo[2]) if geo[0] == "c" else _rect_poly_clear(rect, geo[1])
            if c < best[0]:
                best = (c, f"{name} ↔ {oname} ({pose_txt})")
    for sd in RL.lock_sides(p):
        tg = "+Y" if sd > 0 else "−Y"
        py, pz = RL.lever(p, sd)["piv"]
        xf, xb, _ = RL.piv_hub(p)
        test(f"cubo del eje {tg}", (py, pz, RL.PIV_BOSS_R, xf, xb), "fijo")
        test(f"anillo del eje {tg}", (py, pz, CLIP_R, xf - CLIP, xf), "fijo")
        for lk in RL.link_lengths():
            for t in (0.0, 0.5, 1.0):
                for name, item in _moving_rects(p, sd, t, lk)[:3]:
                    test(f"{name} {tg}", item, f"t {t:g}, eslabón {lk:g}", sd)
                name, item = _moving_rects(p, sd, t, lk)[3]
                test(f"{name} {tg}", item, f"t {t:g}, eslabón {lk:g}", sd)
    return best


def _tol():
    return format(RL.LINK_TOL, "g").replace(".", ",")


def checks(p, part):
    out = [("un solo sólido", len(part.solids()), 1, "=")]
    T = RL.lev_travel(p)
    need = RL.need(p)
    zs = RL.stop_z(p)
    out.append(("recorrido de la manivela del balancín (= carrera del émbolo) ≥ liberación + 2 [mm]", T, need + 2.0, ">="))
    # resorte del émbolo (B-SPRING, DES-01): cabe en la cámara y en la cola, no llega a compacto y τ (Wahl) ≤ τ_zul
    out += [("resorte: largo con el perno afuera = cámara − carrera del émbolo [mm]", RL.SPRING_L_MIN,
             RL.PLG_SPRING_L1 - p.REV_plunger_stroke, "="),
            ("resorte: Ø exterior ≤ cámara Ø16 H8 − 1 [mm]", RL.SPRING_OD, p.REV_lock_pin_d - 1.0, "<="),
            ("resorte: Ø interior ≥ cola Ø10 + 1 [mm]", RL.SPRING_OD - 2 * RL.SPRING_WIRE_D, 11.0, ">="),
            ("resorte: largo mínimo de trabajo ≥ compacto + Σ luces mínimas (EN 13906-1) [mm]", RL.SPRING_L_MIN,
             RL.spring_L_solid() + RL.spring_Sa(), ">="),
            ("resorte: precarga instalada (perno adentro) [N]", RL.spring_F(RL.SPRING_L_INST), 15.0, ">="),
            ("resorte: τ con Wahl al largo mínimo ≤ τ_zul = 0,5·Rm (EN 13906-1) [MPa]",
             RL.spring_tau(RL.SPRING_F_MAX), RL.SPRING_TAU_ZUL, "<="),
            ("resorte: τ sin corregir a bloque ≤ τ_zul (resorte apto a bloque) [MPa]",
             RL.spring_tau(RL.spring_F(RL.spring_L_solid()), wahl=False), RL.SPRING_TAU_ZUL, "<=")]
    # eslabón rígido ajustable (DES-04)
    out += [("resorte: precarga instalada con G de 1.4401 (65 GPa, k −7 %) [N]",
             RL.spring_F(RL.SPRING_L_INST) * 65000.0 / RL.SPRING_G, 15.0, ">=")]
    # eslabón rígido ajustable (DES-04): rango físico del ajuste ±LINK_ADJ ≥ cadena de tolerancias; cinemática con ±LINK_TOL
    out += [("eslabón: rango del ajuste roscado ≥ cadena de tolerancias pomo ↔ manivela (peor caso) [mm]",
             RL.LINK_ADJ, RL.LINK_STACK_FULL, ">="),
            ("eslabón: desajuste revisado en la cinemática ≥ residual (media vuelta/2 + re-montaje del soporte) [mm]",
             RL.LINK_TOL, RL.LINK_STACK_RES, ">="),
            ("eslabón: luz ojo ↔ cara del pomo con el ajuste en su mínimo (−LINK_ADJ) [mm]", RL.LINK_GAP - RL.LINK_ADJ, 0.5, ">="),
            ("eslabón: rosca M4 enganchada en la cola con el ajuste en su máximo (+LINK_ADJ) ≥ 1,5·d [mm]",
             RL.LINK_SHANK_L - (RL.LINK_GAP + RL.LINK_ADJ), 6.0, ">=")]
    for sd in RL.lock_sides(p):
        L = RL.lever(p, sd)
        tag = "+Y" if sd > 0 else "−Y"
        (c0, o0), (c1, o1) = L["pose"](0.0), L["pose"](1.0)
        out.append((f"balancín {tag}: subida de la salida = recorrido del pomo (1:1) [mm]", o1[1] - o0[1], T, "="))
        lk_all = RL.link_lengths()
        out.append((f"balancín {tag}: terminal tirado bajo el regulador (ajuste del eslabón ±{RL.LINK_TOL:g}) [mm]",
                    min((zs - RL.ADJ_BELOW) - (L["pose"](1.0, lk)[1][1] + RL.NIPPLE_R) for lk in lk_all), 2.0, ">="))
        dz = max(abs(L["pose"](t, lk)[0][1] - L["lock"][1]) for lk in lk_all for t in (0.0, 0.25, 0.5, 0.75, 1.0))
        out.append((f"balancín {tag}: arco de la manivela ↔ eje del émbolo dentro de la ranura del ojo (±{_tol()}) [mm]",
                    dz, RL.LINK_SLOT, "<="))
        dmax = max(abs(L["pose"](t, lk)[0][0] - L["piv"][0]) for lk in lk_all for t in (0.0, 1.0))
        out.append((f"balancín {tag}: ángulo de la manivela desde la vertical del eje (±{_tol()}) [°]",
                    math.degrees(math.asin(dmax / RL.LEV_L)), 60.0, "<="))
        out.append((f"balancín {tag}: cable para liberar el brazo, peor ajuste del eslabón [mm]",
                    max(RL.lever_rise(p, sd, need, lk) for lk in lk_all), need + 0.5, "<="))
    if len(RL.lock_sides(p)) > 1:
        Lb = RL.lever(p, -1)
        La = RL.lever(p, 1)
        lk = RL.LINK + RL.LINK_TOL
        out.append(("ojo del eslabón −Y tirado (ajuste máx.) ↔ cara interior de la oreja +Y [mm]",
                    p.STE_ear_y0 - (Lb["pose"](1.0, lk)[0][0] + RL.LINK_EYE_HALF), 1.5, ">="))
        out.append(("ojo del eslabón +Y tirado (ajuste máx.) ↔ cara interior de la oreja −Y [mm]",
                    p.STE_ear_y0 + (La["pose"](1.0, lk)[0][0] - RL.LINK_EYE_HALF), 1.5, ">="))
    cl, what = clearances(p)
    out.append((f"cubos/pernos/ojos ↔ émbolos y orejas: holgura mínima ({what}) [mm]", cl, 1.5, ">="))
    # cubos (DES-03): apoyos de ≥ 2·Ø
    out.append(("cubo del eje del balancín: apoyo ≥ 2·Ø del muñón [mm]", RL.piv_hub(p)[2], 2 * RL.PIV_D, ">="))
    out.append(("cubo de la manivela: perno prensado en ≥ 2·Ø [mm]", RL.crank_hub(p)[2], 2 * RL.CRANK_D, ">="))
    out.append(("alma del balancín ↔ montante: arandela PTFE de 1 del eje + luz [mm]", GAP - 1.0, 0.5, ">="))
    x_ear = max(RL.lock_xz(p, s)[0] for s in RL.lock_sides(p)) + p.STE_lock_lobe_r
    out.append(("pestaña del regulador a popa del lóbulo de la oreja [mm]",
                (RL.cable_x(p) - RL.ADJ_HOLE_R - RL.ADJ_EDGE) - x_ear, 2.0, ">="))
    out.append(("alma de los balancines a popa de los retenes interiores de los émbolos (anillo DIN 471) [mm]",
                RL.lever_x0(p) - max(RL.lock_xz(p, s)[0] + RL.NUT_R for s in RL.lock_sides(p)), 2.0, ">="))
    out.append(("montante dentro del pad (X, popa) [mm]", RL.pad_x(p)[1] - (up_x(p) + UP_T), 0.0, ">="))
    out.append(("salida del balancín ↔ brazo del bucket (Y) [mm]",
                p.REV_y_in - max(abs(RL.lever(p, s)["pose"](0.5)[1][0]) + RL.OUT_BOSS_R for s in RL.lock_sides(p)), 5.0, ">="))
    out.append(("cable de salida ↔ alma de la manivela del mismo balancín (Y, peor pose y ajuste) [mm]",
                min(abs(RL.cable_y(p, s) - RL.lever(p, s)["pose"](t, lk)[0][0]) - RL.CRANK_BOSS_R - 0.75
                    for s in RL.lock_sides(p) for t in (0.0, 0.5, 1.0) for lk in RL.link_lengths()), 1.0, ">="))
    out.append(("pestañas de los reguladores sobre los balancines (Z) [mm]",
                RL.stop_z(p) - max(RL.lever_top(p, s) for s in RL.lock_sides(p)), 2.0, ">="))
    # fijación (R4-07): tornillos dentro del pad con borde ≥ 6 y fondo del taladro sobre el paso del chorro
    px = RL.pad_x(p)
    edge = min(min(x - px[0], px[1] - x, y + BASE_W, BASE_W - y) for (x, y) in RL.pad_screws(p))
    out.append(("M5 de la base: distancia al borde del pad [mm]", edge, 6.0, ">="))
    floor = min((pad_z(p) - M5_DRILL) - math.sqrt(p.STE_rb ** 2 - y ** 2) for (_, y) in RL.pad_screws(p))
    out.append(("M5 de la base: piel bajo el taladro (sobre el paso del chorro) [mm]", floor, 2.0, ">="))
    out.append(("M5 de la base: rosca enganchada en el pad ≥ 1,2·d [mm]", SCREW_L - BASE_T, 6.0, ">="))
    out.append(("M5 de la base: la punta no toca el fondo de la rosca [mm]", RL.PAD_M5_THREAD - (SCREW_L - BASE_T), 1.0, ">="))
    zb = pad_z(p) + BASE_T                                           # cara superior de la base
    # lo que pasa sobre la base (dentro de su ancho + 1) va ≥ 2 por encima; lo demás pasa al costado con ≥ 1 en Y
    low = [(z - r) for s in RL.lock_sides(p) for t in (0.0, 0.5, 1.0) for lk in RL.link_lengths()
           for (y, z), r in zip(RL.lever(p, s)["pose"](t, lk), (max(RL.CRANK_HUB_R, RL.CRANK_SHOULDER[0] / 2), RL.OUT_BOSS_R))
           if abs(y) - r < BASE_W + 1.0 - 1e-6]
    low += [RL.lever(p, s)["piv"][1] - RL.PIV_BOSS_R for s in RL.lock_sides(p)
            if abs(RL.lever(p, s)["piv"][0]) - RL.PIV_BOSS_R < BASE_W + 1.0 - 1e-6]
    out.append(("balancines sobre la base (Z; lo que no pasa al costado con ≥ 1 en Y) [mm]", (min(low) if low else 99.0) - zb, 2.0, ">="))
    out.append(("balancines, pernos y eslabones TIRADOS (eslabón máx.) ↔ émbolos y boquilla: interferencia [mm³]",
                pulled_interference(p), 0.5, "<="))
    return out
