"""P1-REV-05 — Soporte del cable Mach5 sobre la boquilla, Al 5083 6 mm soldado (frame steer).

La vaina del Mach5 se ancla EN LA BOQUILLA (gira con ella): la varilla baja vertical hasta el perno
del lóbulo del brazo +Y del bucket (cuerda vertical, P1-REV-01) y el cable forma un bucle libre hasta
el prensaestopas del espejo (P1-CTL-05) → la dirección no mueve el bucket (sin acople) y el paso del
espejo queda sobre la flotación. Base atornillada sobre la brida del yugo con los mismos 2 × M6;
alma vertical en X' = 25–31 y 2 grapas con taladro Ø12,8 para la vaina."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_z, prism_yz  # noqa: E402
import _mach5 as M5  # noqa: E402

META = dict(
    id="P1-REV-05", name="soporte_mach5", desc="Soporte de la vaina del Mach5 (Al 5083 6 mm)",
    material="Al 5083", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Reacción del cable al mover el bucket (sin carga del chorro: la toma el émbolo)",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="Chapa cortada y soldada",
)
X0, X1 = 25.0, 31.0          # alma (X' desde el eje de giro)
Z_TOP = 250.0
CLAMPS = ((130.0, 144.0), (226.0, 240.0))


def build(p):
    Xp = p.X_steer_pivot
    z0 = p.STE_zc_top + p.STE_yoke_t
    sx, _ = M5.stud_xz(p)
    ry = M5.rod_y(p)
    s = box(Xp + p.STE_riser_x[0], Xp + p.STE_riser_x[1], -10, 14, z0, z0 + 6)
    web = [(-10, z0 + 5.99), (14, z0 + 5.99), (14, 112.0), (ry + 13.5, 128.0), (ry + 13.5, Z_TOP), (-10, Z_TOP)]
    s = s + prism_yz(web, Xp + X0, Xp + X1)
    for (za, zb) in CLAMPS:
        s = s + box(sx - 6.5, Xp + X0 + 0.01, ry - 10, ry + 10, za, zb)
        s = s - cyl_z(M5.SLEEVE_D / 2 + 0.05, za - 1, zb + 1, x=sx, y=ry)
    for xx in (p.STE_riser_x[0] + 7.0, p.STE_riser_x[1] - 6.0):
        s = s - cyl_z(3.3, z0 - 1, z0 + 7, x=Xp + xx)
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    xs = [part.moved(P.loc_steer(p, s)).bounding_box().max.X for s in (-p.steer_max, 0.0, p.steer_max)]
    sx, _ = M5.stud_xz(p)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz al espejo (±δmax) [mm]", -max(xs), 5.0, ">="),
            ("grapa ↔ alma: vaina adelante del alma [mm]", (p.X_steer_pivot + X0) - (sx + M5.SLEEVE_D / 2), 2.0, ">="),
            ("grapa inferior sobre el lóbulo del bucket abajo [mm]", CLAMPS[0][0] - (M5.stud_xz(p, True)[1] + 11.0), 5.0, ">=")]
