"""_transom.py — pasos del espejo del grupo MANDOS (no es una pieza)."""
PLATE_Z = (322.0, 412.0)
PLATE_T = 6.0


def plate_y(p):
    return (-235.0, max(95.0, round(p.CTL_m66_pt[1] + 25.0)))


def bolts(p):
    y0, y1 = plate_y(p)
    return [(y0 + 10, 332.0), (y0 + 10, 402.0), (-80.0, 332.0), (-80.0, 402.0), (y1 - 10, 332.0), (y1 - 10, 402.0)]


def holes(p):
    """(y, z, Ø, texto) en el espejo/placa."""
    (_, ym, zm), (_, yb, zb), (_, yw, zw) = p.CTL_m66_pt, p.CTL_mach5_pt, p.CTL_bowden_pt
    out = [(ym, zm, 20.5, "pasamuros M66 (P1-CTL-04)"), (yb, zb, 16.5, "prensaestopas M16 Mach5"),
           (yw, zw, 16.5, "prensaestopas M16 Bowden")]
    out += [(y, z, 6.6, "M6 A4 pasante") for y, z in bolts(p)]
    return out
