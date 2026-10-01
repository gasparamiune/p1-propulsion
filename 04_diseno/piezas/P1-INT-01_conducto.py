"""P1-INT-01 — Conducto de la toma enrasada (Al 5083 soldado + bridas y bloque del labio mecanizados).

Marco BOTE. Del plano del fondo (abertura L_open × W_open entre el labio x_lip y la tangencia x_tan)
sube por la rampa (techo C2, ~27°) y termina en la brida circular Ø toma_D_out del plano X_duct_out
(8 × M6 en pump_flange_bc, pasantes, tuercas A4 de este lado; el O-ring de cara está en P1-PMP-01).

Partes del conjunto soldado:
  • chapa 5083 de toma_t mm: techo + costados (cerrado a popa del labio: piso);
  • brida inferior (8 mm, barra delantera de 10 mm) sobre la placa base P1-INT-02, con ranura para
    cordón NBR Ø3,53 vulcanizado en anillo, y bulones M6 A4 a la placa (roscas en la placa);
  • bloque macizo del labio (nariz r_lip enrasada con el fondo, entra en la placa con 0,5 mm de luz);
    tiene las ranuras de las barras de la rejilla y el alojamiento de la pletina de popa (2 × M5);
  • brida de la bomba Ø pump_flange_od × 12;
  • tubo mojado del eje desde el cruce del techo hasta el buje del sello (cara en S_seal, ⟂ al eje,
    centrador Ø seal_spigot_d H8, 4 × M6 en seal_bc a tom_seal_bolt_ang0) con alma de refuerzo;
  • chimenea de inspección Ø toma_chim_id hasta toma_chim_top (sobre la flotación, R10a §0.3) con
    brida para la tapa P1-INT-04.
Se eligió Al soldado y no PETG: ver structural_toma.py (PETG en 2–3 segmentos necesitaba ~13 mm de
pared + nervios para FS ≥ 3 a fatiga por presión, ~3 kg y ~190 h de impresión, y sumaba 2 juntas
más en el límite estanco del casco; 5083 es el mismo metal que el casco: sin par galvánico).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
from build123d import Location  # noqa: E402

import _toma_geom as G  # noqa: E402
from cadlib import box, cyl_x, cyl_y, cyl_z, has_radius, prism_xz  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-INT-01", name="conducto",
            desc="Conducto de toma enrasada Al 5083 soldado: rampa C2, transición a Ø D_bore, brida bomba, buje del sello, chimenea de inspección",
            material="Al 5083", process="torneada", qty=1, frame="boat", group="jet",
            load_case="Presión interna −p_pump_max…+p_pump_max, golpe de fondo, 3 g agua; empuje NO pasa por acá",
            allow={"P1-INT-02": 30.0, "P1-PMP-01": 30.0, "P1-DRV-02": 30.0})


def _ring_jet(r_out, r_in, X0, X1):
    return cyl_x(r_out, X0, X1) - cyl_x(r_in, X0 - 1, X1 + 1)


def lip_solid(p):
    """Bloque del labio + nariz (marco BOTE), recortado a W_open − 2·luz por debajo de la placa."""
    W2, t, g = p.W_open / 2, p.toma_t, p.toma_seal_gap
    xa = p.toma_x_lb_aft + g
    xs = np.linspace(xa, p.toma_x_n, 30)
    top = [(float(x), float(p.toma_floor_z(x)) + 1.0) for x in xs[::-1]]
    poly = [(xa, 0.0), (p.toma_x_n, 0.0)] + [(p.toma_x_n, p.toma_lip_top + 1.0)] + top[1:]
    blk = prism_xz(poly, -(W2 + t), W2 + t)
    nose = cyl_y(p.r_lip, -(W2 + t), W2 + t, x=p.toma_x_n, z=p.r_lip)
    lip = blk + nose
    for s in (1, -1):
        ya, yb = (W2 - g, W2 + t + 1) if s > 0 else (-(W2 + t + 1), -(W2 - g))
        lip = lip - box(xa - 1, p.x_lip + 1, ya, yb, -1, p.base_top_z)
    return lip


def bolt_x(p):
    """Posiciones x de los bulones M6 brida ↔ placa (a ambos lados, |y| = toma_bolt_y)."""
    x0 = p.toma_x_lb_aft - 17.0
    x1 = p.toma_x_j + p.toma_ffw / 2
    n = int(math.ceil((x1 - x0) / 70.0)) + 1
    return [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]


def groove(p, z0, depth):
    """Ranura del cordón NBR (lazo cerrado) en la cara inferior de la brida."""
    w = p.toma_gl_width / 2
    xa, xb = p.toma_x_lb_aft - 11.0, p.toma_x_j + p.toma_ffw / 2
    yy = p.toma_groove_y
    o = G.rounded_rect_xy(xa - w, xb + w, -yy - w, yy + w, 12.0 + w, z0, z0 + depth)
    i = G.rounded_rect_xy(xa + w, xb - w, -yy + w, yy - w, 12.0 - w, z0 - 1, z0 + depth + 1)
    return o - i


def build(p):
    t = p.toma_t
    LJ = loc_jet(p)
    ztop = p.base_top_z
    W2 = p.W_open / 2
    # --- cáscara exterior + bridas + buje + chimenea
    A = G.solid(p, "O_fwd") + G.solid(p, "O_aft")
    # brida de la bomba (marco JET)
    X0 = p.X_duct_out
    A = A + _ring_jet(p.pump_flange_od / 2, p.toma_R_out - 1.0, X0 - p.toma_f_t, X0).moved(LJ)
    # brida inferior + barra delantera
    xa, xb = p.toma_x_lb_aft - p.toma_bf_aft, p.toma_x_j + p.toma_ffw
    A = A + G.rounded_rect_xy(xa, xb, -p.toma_bf_y, p.toma_bf_y, 8.0, ztop, ztop + p.toma_bf_t)
    A = A + box(p.toma_x_j, xb, -p.toma_bf_y, p.toma_bf_y, ztop, ztop + p.toma_ff_t)
    # tubo del eje + buje del sello + alma (marco JET)
    S0, Sc, Lb = p.S_seal, p.toma_S_cross, p.toma_boss_L
    tube = cyl_x(p.toma_tube_od / 2, -(S0 - Lb) - 0.5, -(Sc - 25.0))
    boss = cyl_x(p.seal_boss_od / 2, -S0, -(S0 - Lb))
    web = box(-(S0 - 3.0), -(Sc - 10.0), -4.0, 4.0, -150.0, 0.0)
    A = A + (tube + boss + web).moved(LJ)
    # chimenea de inspección (vertical)
    xc = p.toma_chim_x
    zr = float(p.toma_roof_z(xc))
    rc = p.toma_chim_id / 2
    A = A + cyl_z(rc + t, zr - 25.0, p.toma_chim_top - p.toma_chim_fl_t + 0.5, x=xc)
    A = A + cyl_z(p.toma_chim_fl_od / 2, p.toma_chim_top - p.toma_chim_fl_t, p.toma_chim_top, x=xc)
    # --- recorte: nada por debajo de la cara de la placa (salvo el labio) ni a proa de la barra
    A = A & box(150.0, xb, -400, 400, ztop, 1000)
    # --- pasaje
    A = A - G.solid(p, "P_fwd")
    A = A - G.solid(p, "P_aft")
    # --- labio
    lip = lip_solid(p) - G.solid(p, "P_aft")
    A = A + lip
    # --- agujeros, alojamientos
    # eje: pasaje Ø tube_id, centrador Ø seal_spigot_d H8, 4 × M6 (broca Ø5,0) prof. 14
    cut = cyl_x(p.toma_tube_id / 2, -(S0 + 1.0), -(Sc - 40.0))
    cut = cut + cyl_x(p.seal_spigot_d / 2, -(S0 + 1.0), -(S0 - p.toma_cbore_L))
    for k in range(4):
        a = math.radians(p.tom_seal_bolt_ang0 + 90 * k)
        cut = cut + cyl_x(2.5, -(S0 + 1.0), -(S0 - 14.0), y=p.seal_bc / 2 * math.cos(a), z=p.seal_bc / 2 * math.sin(a))
    # brida de la bomba: 8 × Ø6,4 pasantes
    a0 = p.raw.get("pmp_flange_ang0", 22.5)
    for k in range(p.pump_flange_n):
        a = math.radians(a0 + 360.0 * k / p.pump_flange_n)
        r = p.pump_flange_bc / 2
        cut = cut + cyl_x((p.pump_flange_bolt + p.bolt_clr) / 2, X0 - p.toma_f_t - 1, X0 + 1,
                          y=r * math.cos(a), z=r * math.sin(a))
    A = A - cut.moved(LJ)
    # chimenea: boca Ø chim_id y 4 × M6 (broca Ø5,0) prof. 12
    A = A - cyl_z(rc, zr - 40.0, p.toma_chim_top + 1, x=xc)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        A = A - cyl_z(2.5, p.toma_chim_top - 12.0, p.toma_chim_top + 1,
                      x=xc + p.toma_chim_bc / 2 * math.cos(a), y=p.toma_chim_bc / 2 * math.sin(a))
    # brida inferior: bulones M6 (Ø6,4) y ranura del cordón
    for x in bolt_x(p):
        for s in (1, -1):
            A = A - cyl_z((6 + p.bolt_clr) / 2, ztop - 1, ztop + p.toma_ff_t + 1, x=x, y=s * p.toma_bolt_y)
    A = A - groove(p, ztop - 0.01, p.toma_gl_depth)
    # rejilla: ranuras de las barras en el labio (abiertas abajo), alojamiento de la pletina, 2 × M5
    gc = 0.3
    for yb in p.toma_bar_y:
        A = A - box(p.toma_strap_x[0] - 1, p.x_lip + 1, yb - p.grille_bar_d / 2 - gc, yb + p.grille_bar_d / 2 + gc,
                    -1, p.toma_bar_h + gc)
    sx0, sx1 = p.toma_strap_x
    A = A - box(sx0 - gc, sx1 + gc, -(W2 - 4 + gc), W2 - 4 + gc, -1, p.toma_strap_t + gc)
    for y in strap_screw_y(p):
        A = A - cyl_z(2.1, 0, p.toma_strap_t + 12.0, x=0.5 * (sx0 + sx1), y=y)
    return A


def strap_screw_y(p):
    yb = p.toma_bar_y
    i = len(yb) // 2
    return [0.5 * (yb[i + 1] + yb[i + 2]), -0.5 * (yb[i + 1] + yb[i + 2])] if len(yb) >= 5 else [30.0, -30.0]


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    LJ = loc_jet(p)
    t = p.toma_t
    W2 = p.W_open / 2
    # enrase del labio y de la cara exterior con el fondo
    zmin = part.bounding_box().min.Z
    # ángulo de rampa y curvatura
    xs = np.linspace(p.x_lip, p.x_tan, 2000)
    zs = p.toma_roof_z(xs)
    ang = np.degrees(np.arctan(np.abs(np.gradient(zs, xs))))
    # garganta: estación donde el área de la sección llega a la de Ø D_throat
    A_th = math.pi / 4 * p.D_throat ** 2
    Xs = np.linspace(p.toma_X_nose, p.X_duct_out, 200)
    areas = np.array([G.section_area(p, X) for X in Xs])
    A_out = math.pi / 4 * p.toma_D_out ** 2
    # contracción monótona en el codo (sin difusor hacia la bomba)
    mono = float(np.max(areas[1:] / areas[:-1]) - 1.0) * 100.0      # % máx. de aumento entre estaciones
    # tuercas de la brida de la bomba: la cara exterior del conducto libra la tuerca M6 (esquina 5,8 mm)
    r_nut = p.pump_flange_bc / 2 - 5.8 - 1.0
    worst = 0.0
    a0 = p.raw.get("pmp_flange_ang0", 22.5)
    for X in np.linspace(p.X_duct_out - p.toma_f_t - 8.0, p.X_duct_out - p.toma_f_t, 5):
        Zt, Zb, w, rt, rb = G.sec_params(p, X, "aft", t)
        pts = G._rr_points(Zt, Zb, w, rt, rb, 360)
        for k in range(p.pump_flange_n):
            a = math.radians(a0 + 360.0 * k / p.pump_flange_n)
            # radio de la cara exterior en la dirección del bulón
            angs = np.array([math.atan2(z, y) for y, z in pts])
            rr = np.array([math.hypot(y, z) for y, z in pts])
            i = int(np.argmin(np.abs((angs - a + math.pi) % (2 * math.pi) - math.pi)))
            worst = max(worst, rr[i])
    # chimenea ↔ tuercas de la brida de la bomba (cara trasera de la tuerca + arandela)
    from params import jet_to_boat
    zr_c = float(p.toma_roof_z(p.toma_chim_x))
    nut_gap = 1e9
    for k in range(p.pump_flange_n):
        a = math.radians(a0 + 360.0 * k / p.pump_flange_n)
        for Xn in (p.X_duct_out - p.toma_f_t, p.X_duct_out - p.toma_f_t - 8.0):
            xn, yn, zn = jet_to_boat(p, Xn, p.pump_flange_bc / 2 * math.cos(a), p.pump_flange_bc / 2 * math.sin(a))
            if zn + 6 > zr_c - 25.0:
                nut_gap = min(nut_gap, math.hypot(xn - p.toma_chim_x, yn) - (p.toma_chim_id / 2 + t) - 5.8)
    # buje del sello: el techo libra la caja del sello de TREN
    S_min = p.toma_S_min_fn(max(p.raw.get("drv_flange_od", 70.0) / 2, 35.0) + 2.0)
    # cabeza de la tapa de inspección sobre la flotación
    fl_land = p.toma_bf_y - (p.toma_bolt_y + (6 + p.bolt_clr) / 2)
    gl_in = p.toma_groove_y - p.toma_gl_width / 2 - (W2 + 0.0)
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("labio enrasado: z mín. del conducto [mm]", zmin, 0.0, "="),
        ("rampa: ángulo máx. del techo [°]", float(ang.max()), 30.0, "<="),
        ("rampa: ángulo máx. del techo ≥ 25° (R10a §4)", float(ang.max()), 25.0, ">="),
        ("techo: radio de curvatura mín. ≥ 100 mm (sin quiebres)", p.toma_roof_Rmin, 100.0, ">="),
        ("pared mínima del conducto [mm]", t, 4.0, ">="),
        ("labio: radio de nariz r_lip [mm]", p.r_lip, 0.09 * p.D_throat, ">="),
        ("abertura: largo L_open = x_tan − x_lip [mm]", p.x_tan - p.x_lip, p.L_open, "="),
        ("abertura entera a proa de la cara del impulsor: x_lip − x_if [mm]", p.x_lip - p.x_if, 0.85 * p.D, ">="),
        ("salida Ø = D_bore del labio de P1-PMP-01 (sin escalón) [mm]", p.toma_D_out, p.D_bore, "="),
        ("codo convergente: aumento máx. de área entre estaciones ≤ 1 % (sin difusor) [%]", mono, 1.0, "<="),
        ("área de garganta Ø D_throat alcanzada dentro del codo", float(areas.max() >= A_th and A_out <= A_th), 1.0, "="),
        ("brida bomba: Ø ext = pump_flange_od", 1.0 if has_radius(part, p.pump_flange_od / 2, 0.05) else 0.0, 1.0, "="),
        ("brida bomba: 8 agujeros en Ø pump_flange_bc", p.pump_flange_n, 8, "="),
        ("tuercas M6 de la brida de la bomba libres del conducto: r cara ext. [mm]", worst, r_nut, "<="),
        ("buje del sello en S_seal: techo libra la caja Ø70 de TREN (S_seal ≥ S_min) [mm]", p.S_seal, S_min, ">="),
        ("buje del sello: pared al agujero M6 [mm]", p.seal_boss_od / 2 - p.seal_bc / 2 - 3.0, 1.5, ">="),
        ("brida inferior libra las zapatas del soporte (|y| ≤ brg_bracket_y − 24,2 − 1) [mm]", p.toma_bf_y,
         p.brg_bracket_y - 24.2 - 1.0, "<="),
        ("brida inferior: borde al agujero M6 [mm]", fl_land, 1.5, ">="),
        ("cordón: ranura fuera del pasaje [mm]", gl_in, 3.0, ">="),
        ("cordón: profundidad = cs·(1 − apriete) [mm]", p.toma_gl_depth, p.oring_cs * (1 - p.oring_sq), "="),
        ("chimenea: brida ≥ 60 mm sobre la flotación estática [mm]", p.toma_chim_top - p.toma_draft, 60.0, ">="),
        ("chimenea libre de las tuercas M6 de la brida de la bomba [mm]", nut_gap, 2.0, ">="),
        ("chimenea a popa del tubo del eje [mm]", (p.toma_x_cross - p.toma_tube_od / 2) - (p.toma_chim_x + p.toma_chim_id / 2 + t), 0.0, ">="),
    ]
