"""P1-DRV-02 — Caja del sello mecánico, AISI 316 torneada (lado mojado; sin par galvánico con el eje).

Marco JET, coaxial al eje. Espigón Ø seal_spigot_d f7 que entra en el buje de la toma (H8) y brida
de 4 × M6 en seal_bc sobre la cara del buje (plano S = S_seal). Adentro, de popa a proa:
  • cámara MOJADA Ø drv_chamber_d abierta al conducto: aloja la cabeza rotante del sello (cara mojada
    hacia el conducto, montaje interior: la presión y la centrífuga empujan el agua/arena hacia afuera
    de las caras);
  • alojamiento Ø seat_od H8 del asiento fijo (copa de NBR), que apoya en una pared con paso Ø24;
  • LINTERNA de goteo/testigo (R10b H4): cámara seca con 2 ventanas laterales (inspección visual con
    el motor en marcha) y una salida G1/8 abajo para la manguera testigo hacia la sentina.
Se monta en banco sobre el eje entrando por la PUNTA DE POPA (ver params_tren.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cadlib import box, cyl_x, cyl_y, cyl_z  # noqa: E402
from _drv_geom import cyl_s, polar_yz  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-02", name="seal_housing", desc="Caja del sello mecánico 316: espigón Ø42, brida 4×M6, cámara mojada, linterna de goteo",
            material="AISI 316", process="torneada", qty=1, frame="jet", group="drive",
            load_case="Presión de diseño de la bomba 0,2 MPa + resorte del sello; bulones M6 al buje de la toma",
            print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            allow={"P1-DRV-07": 30.0})

BODY_OD = 42.5          # [SUPUESTO: deja 0,75 mm a las cabezas M6 Ø10 (DIN 912) sobre la brida]
SEAT_WALL_HOLE = 24.0   # [SUPUESTO: paso del eje Ø20 por la pared del asiento]


def bolt_angles(p):
    a0 = p.raw.get("tom_seal_bolt_ang0", 45.0)   # [SUPUESTO: 45° (±Y ±Z libres) — coordinado con TOMA si define la clave]
    return [a0 + 90 * k for k in range(4)]


def stations(p):
    S0 = p.S_seal
    return dict(S_sp0=S0 - p.drv_spigot_l, S0=S0, S_fl1=S0 + p.drv_flange_t,
                S_seat0=p.drv_S_seat_face, S_seat1=p.drv_S_seat_back,
                S_wall1=p.drv_S_seat_back + p.drv_seat_wall, S_front=p.drv_S_hsg_front)


def build(p):
    s = stations(p)
    seal = p.drv_seal
    spig = p.seal_spigot_d - 0.05                                # f7 aprox.
    part = cyl_s(spig / 2, s["S_sp0"], s["S0"])
    part = part + cyl_s(p.drv_flange_od / 2, s["S0"], s["S_fl1"])
    part = part + cyl_s(BODY_OD / 2, s["S0"], s["S_front"])
    # saliente del drenaje (abajo, −Z) bajo la linterna
    S_l0, S_l1 = s["S_wall1"], s["S_front"]
    boss = box(-S_l1, -(S_l0 - 5.0), -8.0, 8.0, -(BODY_OD / 2 + 6.0), -BODY_OD / 2 + 3.0)
    part = part + boss
    # cavidades
    part = part - cyl_s(p.drv_chamber_d / 2, s["S_sp0"] - 1, s["S_seat0"])
    part = part - cyl_s(seal["seat_od"] / 2, s["S_seat0"] - 0.01, s["S_seat1"])
    part = part - cyl_s(SEAT_WALL_HOLE / 2, s["S_seat1"] - 0.01, s["S_wall1"])
    part = part - cyl_s(p.drv_lantern_d / 2, S_l0, s["S_front"] + 1)
    # ventanas laterales de la linterna (±Y) y drenaje G1/8 (−Z)
    Sm = (S_l0 + S_l1) / 2
    win_w = S_l1 - S_l0 - 1.5
    for sy in (-1, 1):
        y0, y1 = (8.0, 30.0) if sy > 0 else (-30.0, -8.0)
        part = part - box(-Sm - win_w / 2, -Sm + win_w / 2, y0, y1, -7.0, 7.0)
    part = part - cyl_z(p.drv_drain_tap / 2, -(BODY_OD / 2 + 7.0), -10.0, x=-Sm, y=0.0)
    # 4 × M6 pasantes en la brida
    for a in bolt_angles(p):
        y, z = polar_yz(p.seal_bc / 2, a)
        part = part - cyl_x((6 + p.bolt_clr) / 2, -s["S_fl1"] - 1, -s["S0"] + 1, y=y, z=z)
    return part


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    s = stations(p)
    seal = p.drv_seal
    head_clear = (p.drv_chamber_d - seal["head_od"]) / 2
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("espigón Ø (f7 en buje H8 Ø seal_spigot_d) [mm]", p.seal_spigot_d - 0.05, p.seal_spigot_d, "<="),
        ("pared del espigón alrededor de la cámara mojada [mm]", (p.seal_spigot_d - p.drv_chamber_d) / 2, 2.5, ">="),
        ("holgura radial cabeza del sello ↔ cámara [mm]", head_clear, 1.0, ">="),
        ("la cabeza cabe entre su anillo de respaldo y el asiento (largo de trabajo) [mm]",
         s["S_seat0"] - p.drv_S_head_back, seal["head_l"], "="),
        ("asiento pasa por la cámara al montarlo desde popa (Ø cámara − Ø asiento) [mm]",
         p.drv_chamber_d - seal["seat_od"], 0.5, ">="),
        ("paso del eje por la pared del asiento (holgura radial) [mm]", (SEAT_WALL_HOLE - p.shaft_d) / 2, 1.5, ">="),
        ("pared de la caja en el alojamiento del asiento [mm]", (BODY_OD - seal["seat_od"]) / 2, 3.0, ">="),
        ("luz cabeza M6 (Ø10) ↔ cuerpo [mm]", p.seal_bc / 2 - 5.0 - BODY_OD / 2, 0.5, ">="),
        ("borde brida ↔ agujero M6 [mm]", (p.drv_flange_od - p.seal_bc) / 2 - (6 + p.bolt_clr) / 2, 4.0, ">="),
        ("brida Ø ≤ Ø del buje de la toma + 10 [mm]", p.drv_flange_od, p.seal_boss_od + 10.0, "<="),
        ("linterna de goteo (largo axial) [mm]", p.drv_lantern_l, 6.0, ">="),
        ("pared de la linterna [mm]", (BODY_OD - p.drv_lantern_d) / 2, 3.0, ">="),
        ("v en el sello ≤ v máx. [m/s]", p.sz["mech"]["seal_speed_ms"], seal["v_max_ms"], "<="),
        ("presión de diseño ≤ p máx. del sello [bar]", 2.0, seal["p_max_bar"], "<="),
    ]
