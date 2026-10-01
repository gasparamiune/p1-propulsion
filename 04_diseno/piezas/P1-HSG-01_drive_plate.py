"""P1-HSG-01 — Placa motriz de ALUMINIO 6082-T6, 6 mm (mecanizada: cortar, taladrar, limar
colisos). Lleva el cartucho torneado del rodamiento A (DRV-08), el motor con colisos de
tensado ±8 mm y los separadores del puente; atornilla a la cara delantera de la cuna (4×M6
a tuercas cautivas). Pasa a metal en la Pasada 2 porque el empuje axial y el tiro de correa
son cargas alternas a ~50 Hz (research/R05: f_fatiga del PETG ≈ 0,06; research/R01–R02:
"empuje axial a metal").

Marco: UNIDAD. Empuje avante: el eje empuja la pista interna hacia −u; la pista externa apoya
en el labio delantero del cartucho, cuya brida (cara de popa de la placa) empuja la placa.
Marcha atrás: el cartucho apoya en el fondo del rebaje de la cuna.
"""
from cadlib import *

META = dict(
    id="P1-HSG-01", name="drive_plate", desc="Placa motriz Al 6082-T6 6 mm (motor + cartucho + tensado)",
    material="Al 5052/6082", process="torneada", qty=1, frame="unit",
    load_case="LC1/LC2 empuje axial, LC3 torque de motor + tiro de correa, LC4 tirón al cortar el pasador, LC6 fatiga",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def slot_z(r, v0, v1, u0, u1, w=0.0):
    """Coliso a lo largo de v (Z del marco unidad) atravesando u."""
    return cyl_x(r, u0, u1, y=w, z=v0) + cyl_x(r, u0, u1, y=w, z=v1) + box(u0, u1, w - r, w + r, v0, v1)


def outline(p):
    vs = -p.e
    W = 37.0
    v_top = p.motor_v + p.motor_d / 2 + p.tension_slot + 8
    v_bot = vs - p.cart_fl_d / 2 - 8
    return W, v_bot, v_top


def build(p):
    ua, uf = p.plate_u_aft, p.plate_u_fwd
    vs = -p.e
    W, v_bot, v_top = outline(p)
    plate = box(uf, ua, -W, W, v_bot, v_top)
    # agujero del cartucho + 3×M4 de la brida
    plate = plate - cyl_x(p.cart_od / 2 + 0.1, uf - 1, ua + 1, z=vs)
    import math
    for k in range(3):
        a = math.radians(90 + 120 * k)
        plate = plate - cyl_x(2.2, uf - 1, ua + 1, y=p.cart_bc_r * math.cos(a), z=vs + p.cart_bc_r * math.sin(a))
    # motor: coliso central + 4 colisos M4
    tz = p.tension_slot
    mv = p.motor_v
    plate = plate - slot_z(12.5, mv - tz, mv + tz, uf - 1, ua + 1)
    r = p.motor_bc / 2 * 0.7071
    for dw in (-r, r):
        for dv in (-r, r):
            plate = plate - slot_z(2.2, mv + dv - tz, mv + dv + tz, uf - 1, ua + 1, w=dw)
    # 4×M6 a la cuna
    for v in (p.cradle_vbot + 12, 18.0):
        for w in (-26.0, 26.0):
            plate = plate - cyl_x(3.25, uf - 1, ua + 1, y=w, z=v)
    # 2×M6 separadores del puente (a los costados de la polea del motor)
    wsp = p.pd_motor / 2 + 3.0 + 3.0 + 6.0 + 1.0
    for w in (-wsp, wsp):
        plate = plate - cyl_x(3.25, uf - 1, ua + 1, y=w, z=p.motor_v)
    return plate


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [
        ("alcance de eje de motor requerido ≤ saliente", p.plate_t + 2 + p.pulley_w,
         p.inp["motor"]["options"][p.sz["selection"]["motor"]]["shaft_protrusion_mm"], "<="),
        ("distancia entre centros (nominal)", p.motor_v + p.e, p.center_dist, "≈"),
    ]
