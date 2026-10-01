"""P1-REV-05 — Soporte del cable Mach5 sobre la boquilla, Al 5083 6 mm soldado (frame steer).

La vaina del Mach5 se ancla EN LA BOQUILLA (gira con ella): la varilla baja vertical hasta el perno
del brazo +Y del bucket (cuerda vertical a popa del pivote, P1-REV-01) y el cable forma un bucle libre
hasta el prensaestopas del espejo (P1-CTL-05) → la dirección no mueve el bucket (sin acople) y el paso
del espejo queda sobre la flotación. Base sobre la brida del yugo (mismos 4 × M8), alma transversal en
X' = 25–31 (cruza el plano de los brazos del bucket por delante de su barrido) y placa lateral por
fuera del brazo +Y con 2 grapas Ø12,8 para la vaina."""
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
CLAMPS = ((138.0, 150.0), (234.0, 246.0))
Z_SIDE = (124.0, 248.0)


def side_y(p):
    y0 = M5.rod_y(p) + M5.SLEEVE_D / 2 + 1.0
    return y0, y0 + 6.0


def build(p):
    Xp = p.X_steer_pivot
    z0 = p.STE_zc_top + p.STE_yoke_t
    sx, _ = M5.stud_xz(p)
    ry = M5.rod_y(p)
    ys0, ys1 = side_y(p)
    s = box(Xp + p.STE_riser_x[0], Xp + p.STE_riser_x[1], -14, 14, z0, z0 + 6)
    web = [(-14, z0 + 5.99), (14, z0 + 5.99), (14, 118.0), (ys1, 128.0), (ys1, 150.0), (-14, 150.0)]
    s = s + prism_yz(web, Xp + X0, Xp + X1)
    s = s + box(Xp + X0, sx + 16.0, ys0, ys1, *Z_SIDE)
    for (za, zb) in CLAMPS:
        s = s + box(sx - 10, sx + 10, ry - 6.0, ys0 + 0.01, za, zb)
        s = s - cyl_z(M5.SLEEVE_D / 2 + 0.05, za - 1, zb + 1, x=sx, y=ry)
    for (xx, yy) in p.STE_riser_bolts:
        s = s - cyl_z(4.5, z0 - 1, z0 + 7, x=Xp + xx, y=yy)
    return s


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    xs = [part.moved(P.loc_steer(p, s)).bounding_box().max.X for s in (-p.steer_max, 0.0, p.steer_max)]
    ry = M5.rod_y(p)
    hub_top = p.REV_sleeve_z0 + M5.SLEEVE_L
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz al espejo (±δmax) [mm]", -max(xs), 5.0, ">="),
            ("grapa ↔ brazo +Y del bucket (Y) [mm]", (ry - 6.0) - (p.REV_y_in + p.REV_t), 1.5, ">="),
            ("alma delante del refuerzo del pivote del bucket (X') [mm]", (p.X_bucket_pivot - p.X_steer_pivot - p.REV_boss_r) - X1, 2.0, ">="),
            ("placa lateral bajo la cabeza del Mach5 [mm]", hub_top - Z_SIDE[1], 1.0, ">=")]
