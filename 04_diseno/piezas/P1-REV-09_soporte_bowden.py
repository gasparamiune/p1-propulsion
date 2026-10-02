"""P1-REV-09 — Soporte de reenvío del desbloqueo (frame steer): placa base + montante Al 5083 6/5 mm soldados, con DOS
balancines de reenvío 1:1 (Al 5083 5 mm) y las pestañas de los reguladores M6 de las dos vainas del Bowden (P1-REV-10).

Por qué un reenvío (auditoría ronda 4, R4-06): con el émbolo propio (cuerpo hasta Y = 0, pomo Ø25 que baja 12 mm
hacia el plano medio) no cabe un tope de vaina coaxial con el pomo entre las orejas: desde el pomo tirado
(|Y| ≈ 22) + el regulador, la vaina tendría que girar 90° con R ≥ _release.BOWDEN_R_MIN antes de la cara interior del
brazo del bucket (|Y| 56,5) [CALCULADO: _release]. Cada pomo tira de un eslabón corto de cable (terminal en el ojal
del pomo, lazo en el perno de manivela Ø6 de su balancín); el balancín gira en un tornillo con hombro ISO 7379 Ø6 × M5
del montante y su brazo de salida SUBE lo mismo que corre el pomo; el cable del Bowden sale vertical desde el
terminal (barril Ø5) hasta el regulador M6 de la pestaña y la vaina sigue hacia arriba y a proa (P1-REV-10).
Los balancines están a popa de las contratuercas M24 (la oreja +Y queda a ≥ 2 mm de la pestaña del lado +Y); el
del émbolo +Y tiene el eje DEBAJO de la manivela (el perno pasa sobre la contratuerca del émbolo −Y) y el del −Y
ENCIMA (el perno pasa bajo la contratuerca del +Y).

Fijación (R4-07): la placa base apoya de cara sobre un PAD fresado en la parte superior del cuerpo de la boquilla
(P1-STE-01, a popa de los émbolos, X 399–426,5) y se atornilla con 2 × ISO 4762 M5 × 12 A4-70 en roscas M5 × 7,5 del
pad (Tef-Gel; arandela de nylon bajo la cabeza). Lejos de los ligamentos del pivote y de las roscas M24 de las orejas.
Modelo: el conjunto (soporte soldado + balancines + pernos + eslabones + tramo de cable hasta el regulador +
tornillos) es UN sólido en REPOSO (bucket trabado, cables flojos); los checks verifican también la posición TIRADA."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_x, cyl_y, cyl_z, hex_prism_x, prism_yz  # noqa: E402
from _dir_common import circ, hull  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-09", name="soporte_bowden",
    desc="Soporte de reenvío del desbloqueo: base + montante Al 5083 soldados, 2 balancines 1:1 y 2 pestañas de reguladores M6",
    material="Al 5083", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Tiro de diseño por cable (mano 100 N en el gatillo P1-CTL-14 repartida por el igualador) [CALCULADO]",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="Chapa cortada y soldada (base 6 + montante 5 + pestañas 5)",
)
BASE_T = 6.0          # placa base [SUPUESTO]
UP_T = 5.0            # montante [SUPUESTO]
BASE_W = RL.PAD_W      # semiancho de la base (= pad de la boquilla)
M5_DRILL = RL.PAD_M5_DRILL
SCREW_L = 12.0        # ISO 4762 M5 × 12: 6 mm de rosca en el pad (rosca de 7,5, taladro de 9: no toca fondo)
pad_z = RL.pad_z
GAP = 0.5             # luz balancín ↔ montante


def up_x(p):
    return RL.lever_x0(p) + RL.LEV_T + GAP


def lever_solid(p, side, t=0.0):
    """Balancín + perno de manivela + eslabón (en la pose t) + terminal y tramo de cable de salida."""
    L = RL.lever(p, side)
    (cy, cz), (oy, oz) = L["pose"](t)
    py, pz = L["piv"]
    x0, x1 = RL.lever_x0(p), RL.lever_x0(p) + RL.LEV_T
    lx, lz = L["lock"]
    s = prism_yz(hull(circ(cy, cz, RL.CRANK_BOSS_R) + circ(py, pz, RL.PIV_BOSS_R) + circ(oy, oz, RL.OUT_BOSS_R)), x0, x1)
    s = s + cyl_x(RL.CRANK_D / 2, lx - 4.0, x0 + 0.01, y=cy, z=cz)                      # perno de manivela Ø6
    # eslabón: terminal en el ojal del pomo + cable Ø1,5 hasta el perno (coaxial con el émbolo en reposo)
    kf = RL.knob_end_y(p) - t * RL.lev_travel(p)                                          # cara del pomo (lado +Y)
    sg = 1 if side > 0 else -1
    ka, kb = sg * (kf - 0.3), sg * (kf - 4.3)
    s = s + cyl_y(3.0, min(ka, kb), max(ka, kb), x=lx, z=lz)
    y_t, y_c = kb, cy
    s = s + cyl_y(0.75, min(y_t, y_c), max(y_t, y_c), x=lx, z=lz)
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
    """Contorno del balancín en su propio marco (eje en el origen, manivela en +v, salida en +u): los dos son iguales
    (el del émbolo −Y es el mismo dado vuelta)."""
    return hull(circ(0.0, RL.LEV_L, RL.CRANK_BOSS_R) + circ(0.0, 0.0, RL.PIV_BOSS_R) + circ(RL.LEV_L, 0.0, RL.OUT_BOSS_R))


def crank_pin_len(p, side):
    """Largo del perno de manivela: prensado en el balancín + voladizo hasta 4 mm más allá del eje del émbolo."""
    return RL.lever_x0(p) + RL.LEV_T - (RL.lock_xz(p, side)[0] - 4.0)


def bracket(p):
    """Soporte soldado (base + montante + pestañas) con los tornillos del balancín y los M5 de la base."""
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
        s = s + cyl_x(RL.PIV_D / 2, RL.lever_x0(p) - 0.01, ux + UP_T + 0.01, y=py, z=pz)  # hombro Ø6
        s = s + cyl_x(5.0, RL.lever_x0(p) - 4.0, RL.lever_x0(p), y=py, z=pz)              # cabeza ISO 7379
        s = s + hex_prism_x(8.0, ux + UP_T, ux + UP_T + 4.0, y=py, z=pz)                  # tuerca M5
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
    """Volumen (mm³) de los balancines/eslabones TIRADOS (carrera completa del émbolo) contra los émbolos (cuerpo,
    contratuerca; pomo tirado) y la boquilla."""
    from build123d import Pos, Rot
    m4 = _other("P1-REV-04_embolo")
    e = m4.build(p)
    obst = []
    for sd in RL.lock_sides(p):
        x, z = RL.lock_xz(p, sd)
        loc = Pos(x, 0, z) if sd > 0 else Pos(x, 0, z) * Rot(180, 0, 0)
        obst.append(loc * (e - cyl_y(12.6, RL.knob_end_y(p) - 0.01, RL.body_end_y(p) - 0.01)))   # sin el pomo en reposo
        kz = RL.knob_end_y(p) - RL.lev_travel(p)
        k = cyl_y(12.5, kz, kz + RL.PLG_KNOB_L)                                                  # pomo tirado
        obst.append(Pos(x, 0, z) * k if sd > 0 else Pos(x, 0, z) * Rot(180, 0, 0) * k)
    obst.append(_other("P1-STE-01_boquilla").build(p))
    v = 0.0
    for sd in RL.lock_sides(p):
        lv = lever_solid(p, sd, 1.0)
        for o in obst:
            try:
                v += (lv & o).volume
            except Exception:                         # noqa: BLE001
                v += 0.0
    return v


def checks(p, part):
    out = [("un solo sólido", len(part.solids()), 1, "=")]
    T = RL.lev_travel(p)
    need = RL.need(p)
    zs = RL.stop_z(p)
    out.append(("recorrido de la manivela del balancín (= carrera del émbolo) ≥ liberación + 2 [mm]", T, need + 2.0, ">="))
    for sd in RL.lock_sides(p):
        L = RL.lever(p, sd)
        tag = "+Y" if sd > 0 else "−Y"
        (c0, o0), (c1, o1) = L["pose"](0.0), L["pose"](1.0)
        out.append((f"balancín {tag}: subida de la salida = recorrido del pomo (1:1) [mm]", o1[1] - o0[1], T, "="))
        out.append((f"balancín {tag}: terminal tirado bajo el regulador [mm]",
                    (zs - RL.ADJ_BELOW) - (o1[1] + RL.NIPPLE_R), 2.0, ">="))
        zc = [L["pose"](t)[0][1] for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        out.append((f"balancín {tag}: desalineación del eslabón (manivela ↔ eje del émbolo) [°]",
                    math.degrees(math.atan2(max(abs(z - L['lock'][1]) for z in zc), RL.LINK)), 10.0, "<="))
    if len(RL.lock_sides(p)) > 1:
        zp, zm = RL.lock_xz(p, 1)[1], RL.lock_xz(p, -1)[1]
        La, Lb = RL.lever(p, 1), RL.lever(p, -1)
        za = min(La["pose"](t)[0][1] for t in (0.0, 0.5, 1.0))
        zb_ = max(Lb["pose"](t)[0][1] for t in (0.0, 0.5, 1.0))
        out.append(("perno de manivela +Y sobre la contratuerca del émbolo −Y (círculo circunscrito) [mm]",
                    (za - RL.CRANK_D / 2) - (zm + RL.NUT_R), 2.0, ">="))
        out.append(("perno de manivela −Y bajo la contratuerca del émbolo +Y (círculo circunscrito) [mm]",
                    (zp - RL.NUT_R) - (zb_ + RL.CRANK_D / 2), 2.0, ">="))
        out.append(("perno de manivela −Y tirado ↔ cara interior de la oreja +Y [mm]",
                    p.STE_ear_y0 - (Lb["pose"](1.0)[0][0] + RL.CRANK_D / 2), 2.0, ">="))
    x_ear = max(RL.lock_xz(p, s)[0] for s in RL.lock_sides(p)) + p.STE_lock_lobe_r
    out.append(("pestaña del regulador a popa del lóbulo de la oreja [mm]",
                (RL.cable_x(p) - RL.ADJ_HOLE_R - RL.ADJ_EDGE) - x_ear, 2.0, ">="))
    out.append(("balancines a popa de las contratuercas M24 (círculo circunscrito) [mm]",
                RL.lever_x0(p) - max(RL.lock_xz(p, s)[0] + RL.NUT_R for s in RL.lock_sides(p)), 2.0, ">="))
    out.append(("salida del balancín ↔ brazo del bucket (Y) [mm]",
                p.REV_y_in - max(abs(RL.lever(p, s)["pose"](0.5)[1][0]) + RL.OUT_BOSS_R for s in RL.lock_sides(p)), 5.0, ">="))
    out.append(("cable de salida ↔ cubo de la manivela del mismo balancín (Y, peor pose) [mm]",
                min(abs(RL.cable_y(p, s) - RL.lever(p, s)["pose"](t)[0][0]) - RL.CRANK_BOSS_R - 0.75
                    for s in RL.lock_sides(p) for t in (0.0, 0.5, 1.0)), 1.0, ">="))
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
    zb = pad_z(p) + BASE_T + 5.0                                     # base + cabezas de los M5
    low = [(z - r) for s in RL.lock_sides(p) for t in (0.0, 0.5, 1.0)
           for (y, z), r in zip(RL.lever(p, s)["pose"](t), (RL.CRANK_BOSS_R, RL.OUT_BOSS_R)) if abs(y) - r < BASE_W]
    low += [RL.lever(p, s)["piv"][1] - RL.PIV_BOSS_R for s in RL.lock_sides(p)
            if abs(RL.lever(p, s)["piv"][0]) - RL.PIV_BOSS_R < BASE_W]
    out.append(("balancines sobre la base y las cabezas de los M5 (Z) [mm]", (min(low) if low else 99.0) - (zb - 5.0), 2.0, ">="))
    out.append(("balancines, pernos y eslabones TIRADOS ↔ émbolos y boquilla: interferencia [mm³]",
                pulled_interference(p), 0.5, "<="))
    return out
