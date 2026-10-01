"""_transom.py — pasos del espejo del grupo MANDOS (no es una pieza)."""
PLATE_Y = (-235.0, 95.0)
PLATE_Z = (322.0, 412.0)
PLATE_T = 6.0
BOLTS = [(-225.0, 332.0), (-225.0, 402.0), (-80.0, 332.0), (-80.0, 402.0), (85.0, 332.0), (85.0, 402.0)]


def holes(p):
    """(y, z, Ø, texto) en el espejo/placa."""
    (_, ym, zm), (_, yb, zb), (_, yw, zw) = p.CTL_m66_pt, p.CTL_mach5_pt, p.CTL_bowden_pt
    out = [(ym, zm, 20.5, "pasamuros M66 (P1-CTL-04)"), (yb, zb, 16.5, "prensaestopas M16 Mach5"),
           (yw, zw, 16.5, "prensaestopas M16 Bowden")]
    out += [(y, z, 6.6, "M6 A4 pasante") for y, z in BOLTS]
    return out
