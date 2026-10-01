"""P1-HSG-01 — Placa motriz: rodamiento A (localizador, en buje trasero), montaje del
motor con colisos de tensado ±8 mm, unión a la cuna (4×M6) y al puente (2×M6 + separadores).

Marco: UNIDAD. Empuje avante: el eje empuja la pista interna hacia −u; la pista externa
apoya en el labio delantero del alojamiento. Marcha atrás: la pista externa apoya en el
fondo del rebaje de la cuna.
"""
from cadlib import *

META = dict(
    id="P1-HSG-01", name="drive_plate", desc="Placa motriz (rodamiento A + motor + tensado)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC1/LC2 empuje axial, LC3 torque de motor + tiro de correa, LC4 tirón al cortar el pasador",
    print_rot=(0, -90, 0), solid_frac=1.0,
    orientation="Plana (u = Z): tiro de correa y torque en el plano de capas; buje del rodamiento vertical (redondez).",
)


def slot_z(r, v0, v1, u0, u1, w=0.0):
    """Coliso a lo largo de v (Z del marco unidad) atravesando u."""
    return cyl_x(r, u0, u1, y=w, z=v0) + cyl_x(r, u0, u1, y=w, z=v1) + box(u0, u1, w - r, w + r, v0, v1)


def build(p):
    lay = p.layout
    ua, uf = p.plate_u_aft, p.plate_u_fwd
    vs = -p.e
    W = 37.0
    v_top = p.motor_v + p.motor_d / 2 + p.tension_slot + 8
    v_bot = vs - (p.brg_D + 10) / 2 - 10
    plate = box(uf, ua, -W, W, v_bot, v_top)
    # buje del rodamiento A hacia popa
    boss_r = (p.brg_D + 10.0) / 2
    plate = plate + cyl_x(boss_r, uf, lay["u_boss_aft"], z=vs)
    # alojamiento del rodamiento (abierto hacia popa) + labio con paso de eje
    plate = plate - cyl_x((p.brg_D + p.press) / 2, lay["u_boss_aft"] - p.brg_B - 0.3, lay["u_boss_aft"] + 1, z=vs)
    plate = plate - cyl_x(10.5, uf - 1, lay["u_boss_aft"], z=vs)
    # motor: coliso central + 4 colisos M4 en círculo de pernos
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
            plate = plate - cyl_x(3.2, uf - 1, ua + 1, y=w, z=v)
    # 2×M6 separadores del puente (a los costados de la polea del motor)
    wsp = p.pd_motor / 2 + 3.0 + 3.0 + 6.0 + 1.0
    for w in (-wsp, wsp):
        plate = plate - cyl_x(3.2, uf - 1, ua + 1, y=w, z=p.motor_v)
    return plate


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    lay = p.layout
    return [
        ("Ø alojamiento rodamiento (ajuste prensado)", p.brg_D + p.press, p.brg_D - 0.05, "≈"),
        ("alcance de eje de motor requerido ≤ saliente", p.plate_t + 2 + p.pulley_w,
         p.inp["motor"]["options"][p.sz["selection"]["motor"]]["shaft_protrusion_mm"], "<="),
        ("distancia entre centros (nominal)", p.motor_v + p.e, p.center_dist, "≈"),
    ]
