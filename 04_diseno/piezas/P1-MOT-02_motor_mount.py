"""P1-MOT-02 — Soporte del motor, Al 6082-T651 mecanizado + soldado (placa 10 mm + 2 pies + 2 cartelas).

Placa ⟂ al eje abulonada a la cara delantera del motor (4 × M de la tabla MOTORS de params_tren,
[ESTIMADO: medir el motor recibido]), con agujero central por donde pasa el cubo del acople. Dos pies
hacia proa, bajo el cuerpo del motor, apoyados en el PISO (z = floor_z) y abulonados con 4 × M8 a las
varengas/largueros del casco a través del piso (interfaz con el casco de referencia del grupo TOMA).
NO toma empuje: el Rotex tiene juego axial "s" y el empuje queda en el par 7204 (P1-DRV-03).
Toma el par de reacción del motor (T_max) y 3 g vertical."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402
from cadlib import box, cyl_x, cyl_z, prism_xz  # noqa: E402
from _drv_geom import cyl_s, polar_yz, x_boat, z_axis  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-MOT-02", name="motor_mount", desc="Soporte del motor Al: placa a la cara del motor + pies al piso (4×M8)",
            material="Al 5052/6082", process="torneada", qty=1, frame="boat", group="motor",
            load_case="Par de reacción T_max del controlador + 3 g vertical del motor; sin empuje",
            print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            allow={"P1-MOT-01": 5.0})

PLATE_HW = None   # semiancho de la placa = semiancho de los pies (ver geom)
GUSSET_T = 6.0    # [SUPUESTO]


def geom(p):
    ca = math.cos(math.radians(p.alpha))
    fy0, fy1 = p.mot_foot_y
    S0 = p.S_motor0 - p.mot_plate_t
    x_aft = x_boat(p, S0) - (p.motor_d / 2 + 30.0) * math.sin(math.radians(p.alpha))   # base de la placa (popa)
    xf0 = x_boat(p, p.S_motor0)
    holes = [(xf0 + 15.0, sy * (fy0 + fy1) / 2) for sy in (-1, 1)] + \
            [(xf0 + p.mot_foot_l - 12.0, sy * (fy0 + fy1) / 2) for sy in (-1, 1)]
    return dict(S0=S0, xf0=xf0, fy0=fy0, fy1=fy1, holes=holes, zf0=p.mot_foot_z, zf1=p.mot_foot_z + p.mot_foot_t)


def build(p):
    g = geom(p)
    m = p.mot
    hw = g["fy1"]
    top = p.motor_d / 2 + 10.0
    # placa ⟂ al eje (marco JET), recortada abajo por el plano del piso
    plate = box(-p.S_motor0, -g["S0"], -hw, hw, -(p.z_if + p.S_motor0) , top).moved(loc_jet(p))
    plate = plate - box(-2000, 2000, -500, 500, -500, g["zf0"])
    # pies hacia proa sobre el piso
    feet = None
    for sy in (-1, 1):
        ya, yb = (g["fy0"], g["fy1"]) if sy > 0 else (-g["fy1"], -g["fy0"])
        f = box(g["xf0"] - 12.0, g["xf0"] + p.mot_foot_l, ya, yb, g["zf0"], g["zf1"])
        # cartela (xz) en el borde exterior del pie
        gy = (yb - GUSSET_T, yb) if sy > 0 else (ya, ya + GUSSET_T)
        gus = prism_xz([(g["xf0"] - 6.0, g["zf1"] - 1), (g["xf0"] + p.mot_foot_l - 15.0, g["zf1"] - 1),
                        (g["xf0"] - 6.0, g["zf1"] + 55.0)], gy[0], gy[1])
        f = f + gus
        feet = f if feet is None else feet + f
    part = plate + feet
    # agujero del acople y agujeros a la cara del motor (marco JET)
    cut = cyl_s(p.mot_hole_d / 2, g["S0"] - 1, p.S_motor0 + 1)
    for k in range(m["mount_n"]):
        y, z = polar_yz(m["mount_pcd"] / 2, 45 + 360 / m["mount_n"] * k)
        cut = cut + cyl_x((m["mount_bolt"] + p.bolt_clr) / 2, -p.S_motor0 - 1, -g["S0"] + 1, y=y, z=z)
    part = part - cut.moved(loc_jet(p))
    for (xh, yh) in g["holes"]:
        part = part - cyl_z((p.mot_foot_bolt + 1.0) / 2, g["zf0"] - 1, g["zf1"] + 1, x=xh, y=yh)
    return part


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    g = geom(p)
    m = p.mot
    c = p.drv_coupling
    edge = m["mount_pcd"] / 2 - (m["mount_bolt"] + p.bolt_clr) / 2 - p.mot_hole_d / 2
    hw_floor = p.raw.get("ele_hw_avail", 300.0)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("agujero de la placa ≥ Ø acople + 2 × 3 (pasa el cubo) [mm]", p.mot_hole_d, c["D"] + 6.0, ">="),
            ("borde entre el agujero central y los agujeros del motor [mm]", edge, 3.0, ">="),
            ("agujero central ≥ centrador del motor [mm]", p.mot_hole_d, m["pilot_d"] + 1.0, ">="),
            ("pies sobre el piso (z apoyo = floor_z) [mm]", g["zf0"], p.floor_z, "="),
            ("pies dentro de la manga del casco [mm]", hw_floor - g["fy1"], 20.0, ">="),
            ("pie ↔ cuerpo del motor (luz vertical en |y| = fy0) [mm]",
             (z_axis(p, p.S_motor0) - math.sqrt(max((p.motor_d / 2) ** 2 - g["fy0"] ** 2, 0.0))) - g["zf1"]
             if g["fy0"] < p.motor_d / 2 else 99.0, 3.0, ">="),
            ("placa fuera del soporte de rodamientos (|y| placa < mejilla) [mm]", p.drv_cheek_y[0] - g["fy1"], 3.0, ">=")]
