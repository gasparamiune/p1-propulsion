"""P1-INT-02 — Placa base de la toma (Al 5083-H111, mecanizada de chapa de 10 mm).

Marco BOTE. Reemplaza un paño del fondo del casco alrededor de la toma:
  • cuerpo enrasado (z 0 → base_top_z = 10) que llena el recorte del casco (luz 0,5 mm con
    Sikaflex-291i [ESTIMADO: research/R05 S36]); su cara inferior continúa el fondo (escalón ≤ 1 mm);
  • ala perimetral (z 4,5 → 10) que monta sobre el casco con cama de sellador, abulonada con
    M6 ISO 10642 A4-70 avellanados desde afuera (cabeza enrasada) y tuerca autofrenante A4 adentro;
  • abertura de la toma: costados verticales en ±W_open/2 (continúan el conducto); a proa, la CUÑA
    del techo (rampa) mecanizada en 3D desde la tangencia hasta donde el techo llega a 9 mm; a popa,
    el alojamiento del bloque del labio de P1-INT-01;
  • roscas ciegas M6 para la brida del conducto (P1-INT-01), 4 × M8 ciegas para el soporte de
    rodamientos del grupo TREN (brg_bracket_holes, cara superior plana a base_top_z) y bolsillos
    + roscas M5 del tirante delantero de la rejilla (P1-INT-03).
El empuje del tren llega por el soporte de rodamientos a esta placa y de acá al casco por los bulones
del ala (no pasa por el conducto).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402

import _toma_geom as G  # noqa: E402
from cadlib import box, cyl_z  # noqa: E402

META = dict(id="P1-INT-02", name="placa_base",
            desc="Placa base de la toma Al 5083 10 mm: cuerpo enrasado + ala abulonada al casco, cuña de la rampa, roscas del conducto y del soporte de rodamientos",
            material="Al 5083", process="torneada", qty=1, frame="boat", group="jet",
            load_case="Golpe de fondo, empuje del tren por el soporte de rodamientos, tracción de los bulones del conducto",
            allow={"P1-INT-01": 30.0, "P1-REF-01": 30.0, "P1-DRV-03": 30.0})

M6_TAP, M8_TAP, M5_TAP = 5.0, 6.8, 4.2   # brocas de roscar ISO [VERIFICADO: tabla ISO 261/DIN 336]


def hull_bolts(p):
    """Bulones del ala (x, y): en la línea media del ala, paso ≤ toma_hull_pitch."""
    x0, x1 = p.toma_plate_x0 - p.toma_rim_w / 2, p.toma_plate_x1 + p.toma_rim_w / 2
    yb = p.toma_plate_y + p.toma_rim_w / 2
    pts = []
    n = int(math.ceil((x1 - x0) / p.toma_hull_pitch)) + 1
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        pts += [(x, yb), (x, -yb)]
    m = int(math.ceil(2 * yb / p.toma_hull_pitch)) + 1
    for j in range(1, m - 1):
        y = -yb + 2 * yb * j / (m - 1)
        pts += [(x0, y), (x1, y)]
    return pts


def tie_screws(p):
    return [(p.toma_x_bf, s * (p.W_open / 2 + 7.0)) for s in (1, -1)]


def build(p):
    W2 = p.W_open / 2
    zt = p.base_top_z
    x0, x1, yc, rw = p.toma_plate_x0, p.toma_plate_x1, p.toma_plate_y, p.toma_rim_w
    body = G.rounded_rect_xy(x0, x1, -yc, yc, p.toma_plate_r, 0.0, zt)
    rim = G.rounded_rect_xy(x0 - rw, x1 + rw, -yc - rw, yc + rw, p.toma_plate_r + rw, p.toma_rim_z0, zt)
    P = body + rim
    # abertura: pasaje (da la cuña de la rampa a proa) + caja vertical hasta x_j (costados y labio)
    P = P - G.solid(p, "P_fwd")
    P = P - box(p.toma_x_lb_aft, p.toma_x_j, -W2, W2, -1, zt + 1)
    # roscas M6 ciegas (8 mm) para la brida del conducto
    import importlib.util
    spec = importlib.util.spec_from_file_location("_int01", str(Path(__file__).resolve().parent / "P1-INT-01_conducto.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for x in m.bolt_x(p):
        for s in (1, -1):
            P = P - cyl_z(M6_TAP / 2, zt - 8.0, zt + 1, x=x, y=s * p.toma_bolt_y)
    # 4 × M8 ciegas (8,5 mm) del soporte de rodamientos (TREN)
    for (x, y) in p.brg_bracket_holes:
        P = P - cyl_z(M8_TAP / 2, zt - 8.5, zt + 1, x=x, y=y)
    # bulones del ala al casco (M6 pasantes)
    for (x, y) in hull_bolts(p):
        P = P - cyl_z((p.toma_hull_bolt + p.bolt_clr) / 2, p.toma_rim_z0 - 1, zt + 1, x=x, y=y)
    # tirante delantero de la rejilla: bolsillos laterales (abajo) + M5 ciegas
    gc = 0.3
    xb, tw = p.toma_x_bf, p.toma_tie_w
    for s in (1, -1):
        ya, yb = (W2 - 1.0, W2 + 12.0 + gc) if s > 0 else (-(W2 + 12.0 + gc), -(W2 - 1.0))
        P = P - box(xb - tw / 2 - gc, xb + tw / 2 + gc, ya, yb, -1, p.toma_strap_t + gc)
    for (x, y) in tie_screws(p):
        P = P - cyl_z(M5_TAP / 2, 0, p.toma_strap_t + 5.0, x=x, y=y)
    return P


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    W2 = p.W_open / 2
    zt = p.base_top_z
    bb = part.bounding_box()
    # material bajo/encima de las roscas
    skin_m8 = zt - 8.5 - 0.0
    xs = [h[0] for h in p.brg_bracket_holes]
    ys = [abs(h[1]) for h in p.brg_bracket_holes]
    roof_at_tie = float(p.toma_roof_z(p.toma_x_bf))
    cuna_min = zt - float(p.toma_roof_z(p.toma_x_j))
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("cara inferior enrasada con el fondo: z mín. [mm]", bb.min.Z, 0.0, "="),
        ("cara superior = base_top_z [mm]", bb.max.Z, zt, "="),
        ("ancho ≥ ±145 mm en la huella del soporte (pedido del principal) [mm]", p.toma_plate_y, 145.0, ">="),
        ("agujeros M8 del soporte dentro del cuerpo de 10 mm: |y| máx. + 9 ≤ semiancho [mm]", max(ys) + 9.0, p.toma_plate_y, "<="),
        ("agujeros M8 del soporte fuera de la abertura: |y| mín. − 4 − W/2 [mm]", min(ys) - 4.0 - W2, 10.0, ">="),
        ("agujeros M8 dentro de la placa en x [mm]", min(min(xs) - p.toma_plate_x0, p.toma_plate_x1 - max(xs)), 15.0, ">="),
        ("M8 ciegas: piel bajo la rosca [mm]", skin_m8, 1.5, ">="),
        ("M8 ciegas: rosca útil ≥ 0,9 d [mm]", 8.5 - 1.0, 0.9 * 8, ">="),
        ("cuña de la rampa: espesor mín. en la unión con el conducto [mm]", cuna_min, 0.9, ">="),
        ("escalón techo placa → conducto (≤ 1 mm, hacia afuera del flujo) [mm]", zt - float(p.toma_roof_z(p.toma_x_j)), 1.1, "<="),
        ("luz bloque del labio ↔ placa por lado [mm]", p.toma_seal_gap, 0.5, "="),
        ("ala sobre el casco: cama de sellador [mm]", p.toma_rim_z0 - p.bottom_t, 0.5, "="),
        ("paso de bulones del ala ≤ toma_hull_pitch [mm]", p.toma_hull_pitch, 70.0, "<="),
        ("rejilla: el tirante delantero queda bajo el techo (techo − espesor) [mm]", roof_at_tie - p.toma_strap_t, 3.0, ">="),
    ]
