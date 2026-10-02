"""P1-REV-10 — Extremo de la boquilla del Bowden inox de liberación de cada émbolo (COMPRADO, ×2): regulador M6 con
contratuerca en la pestaña del soporte P1-REV-09 + vaina Ø5 con camisa de PTFE (cable inox Ø1,5 adentro)
[ESTIMADO: buscar "Bowden Edelstahl PTFE 1,5 mm Stellschraube M6"].

Recorrido modelado (línea media de la vaina, R ≥ _release.BOWDEN_R_MIN, plano XZ en Y = cable_y del balancín): sale
vertical del regulador, curva R _release.BOWDEN_R 45° hacia proa y sube a 45° hasta Z = _release.Z_SHEATH_END, por
delante del barrido de la cuchara (bucket arriba: labio en X ≈ 393, Z ≈ 172) y por encima de los émbolos y de las
orejas; gira con la dirección (marco steer) y verify la revisa contra todo en δ = −25/0/+25 y bucket arriba/abajo
(y contra el bucket en 10–55°). Desde ahí las dos vainas hacen un bucle libre (≈ 0,5 m, R ≥ 150 mm) hasta el
prensaestopas M16 del Bowden en el espejo (P1-CTL-05, inserto de 2 agujeros B-GLINS) y siguen a la consola, donde
apoyan en el tope del mango de la palanca del bucket (P1-CTL-10) y los dos cables entran en la barra igualadora del
gatillo P1-CTL-14. Instancia 0: émbolo +Y (vaina en Y = cable_y(+1)); instancia 1: émbolo −Y (la misma pieza
trasladada en Y: los dos reguladores están a la misma altura)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_z  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-REV-10", name="bowden_embolo", desc="Bowden inox de liberación de cada émbolo (extremo de la boquilla, comprado; ×2)",
    material="AISI 316", process="comprada", qty=2, frame="steer", group="jet",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=60.0,   # [ESTIMADO: 2,5 m]
)


def sheath(p, y):
    """Vaina Ø BOWDEN_D barrida por la línea media de RL.sheath_path en el plano Y = y."""
    from build123d import Circle, Line, Plane, ThreePointArc, Wire, sweep
    g = RL.sheath_path(p)
    (x0, z0), (xb, zb), (xe, ze), (xf, zf), (cx, cz) = g["p0"], g["pb"], g["pe"], g["pf"], g["c"]
    R = RL.BOWDEN_R
    am = math.radians(22.5)
    mid = (cx + R * math.cos(am), cz + R * math.sin(am))
    z0 = z0 - 1.0                                  # arranca dentro de la cabeza del regulador (un solo sólido)
    path = Wire([Line((x0, y, z0), (xb, y, zb)),
                 ThreePointArc((xb, y, zb), (mid[0], y, mid[1]), (xe, y, ze)),
                 Line((xe, y, ze), (xf, y, zf))])
    prof = Plane(origin=(x0, y, z0), z_dir=(0, 0, 1)) * Circle(RL.BOWDEN_D / 2)
    return sweep(prof, path=path)


def build(p):
    y = RL.cable_y(p, 1)
    xc = RL.cable_x(p)
    zs = RL.stop_z(p)
    zt = zs + RL.TAB_T
    s = cyl_z(2.9, zs - RL.ADJ_BELOW, zt + RL.ADJ_NUT[1], x=xc, y=y)                                 # rosca M6 (modelada Ø5,8)
    s = s + cyl_z(RL.ADJ_NUT[0] / 2, zt + 0.02, zt + RL.ADJ_NUT[1], x=xc, y=y)              # contratuerca M6
    zh = zt + RL.ADJ_NUT[1]
    s = s + cyl_z(RL.ADJ_HEAD[0] / 2, zh - 0.01, zh + RL.ADJ_HEAD[1] + 0.06, x=xc, y=y)      # cabeza con el casquillo
    return s + sheath(p, y)


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    from build123d import Pos
    L = [loc_steer(p, steer)]
    if p.REV_n_locks > 1:                       # vaina del émbolo −Y: misma pieza trasladada en Y
        L.append(loc_steer(p, steer) * Pos(0, RL.cable_y(p, -1) - RL.cable_y(p, 1), 0))
    return L


def checks(p, part):
    g = RL.sheath_path(p)
    out = [("un solo sólido", len(part.solids()), 1, "="),
           ("radio de curvatura de la vaina ≥ mínimo [mm]", RL.BOWDEN_R, RL.BOWDEN_R_MIN, ">="),
           ("fin del tramo modelado sobre el barrido de los émbolos y orejas (Z) [mm]",
            g["pf"][1] - (max(RL.lock_xz(p, s)[1] for s in RL.lock_sides(p)) + p.STE_lock_lobe_r), 50.0, ">=")]
    return out
