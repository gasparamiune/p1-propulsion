"""_transom.py — pasos del espejo del grupo MANDOS (no es una pieza).

La placa interior P1-CTL-01 se ubica en z a partir del ala del tope de dirección P1-STE-08 (que está en el
marco JET y sube/baja con waterjet.axis_height_m): así las dos no se pisan en el espejo para cualquier
altura de eje y espesor de fondo (pedido de regeneración: eje ±10 mm, fondo 3–6 mm)."""
import math

PLATE_Z0_MIN = 322.0      # [SUPUESTO: borde inferior nominal de la placa interior]
PLATE_H = 90.0            # alto de la placa [SUPUESTO]
PLATE_CLR = 2.0           # luz sobre el ala del tope de dirección [SUPUESTO]
PLATE_T = 6.0


def stop_wing_top(p):
    """z BOTE del borde superior del ala de P1-STE-08 en el espejo: la placa de topes está en Z_jet ≤
    STE_stop_z[1]; en el plano x = −5 (cara del ala) z = z_if − (x_if + 5)·tan α + Z/cos α [CALCULADO]."""
    a = math.radians(p.alpha)
    return p.z_if - (p.x_if + 5.0) * math.tan(a) + p.STE_stop_z[1] / math.cos(a)


def plate_z(p):
    z0 = max(PLATE_Z0_MIN, math.ceil(stop_wing_top(p) + PLATE_CLR))
    zt = p.inp["boat"]["transom_height_m"] * 1000
    z1 = min(z0 + PLATE_H, zt - 5.0)
    return (float(z0), float(z1))


def plate_y(p):
    return (-235.0, max(95.0, round(p.CTL_m66_pt[1] + 25.0)))


def bolts(p):
    y0, y1 = plate_y(p)
    z0, z1 = plate_z(p)
    return [(y0 + 10, z0 + 10), (y0 + 10, z1 - 10), (-80.0, z0 + 10), (-80.0, z1 - 10), (y1 - 10, z0 + 10), (y1 - 10, z1 - 10)]


def holes(p):
    """(y, z, Ø, texto) en el espejo/placa."""
    (_, ym, zm), (_, yb, zb), (_, yw, zw) = p.CTL_m66_pt, p.CTL_mach5_pt, p.CTL_bowden_pt
    out = [(ym, zm, 20.5, "pasamuros M66 (P1-CTL-04)"), (yb, zb, 16.5, "prensaestopas M16 Mach5"),
           (yw, zw, 16.5, "prensaestopas M16 Bowden")]
    out += [(y, z, 6.6, "M6 A4 pasante") for y, z in bolts(p)]
    return out
