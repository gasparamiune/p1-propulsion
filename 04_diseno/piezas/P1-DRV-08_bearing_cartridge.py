"""P1-DRV-08 — Cartucho del rodamiento A (Al 6082-T6, torneado de barra Ø55): brida Ø52×4
con 3×M4 a la placa motriz, cuerpo Ø40, asiento Ø32 M7 para 6002, labio delantero con paso
Ø21. Toma el empuje axial en ambos sentidos (rodamiento localizador)."""
import math
from cadlib import *

META = dict(id="P1-DRV-08", name="bearing_cartridge", desc="Cartucho rodamiento A (Al 6082 torneado)",
            material="Al 5052/6082", process="torneada", qty=1, frame="unit",
            load_case="LC1/LC2 empuje axial, LC3/LC4 radial", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—")


def build(p):
    vs = -p.e
    lay = p.layout
    uf, ua = p.plate_u_fwd, p.plate_u_aft
    u_end = lay["u_boss_aft"]
    c = cyl_x(p.cart_od / 2, uf, u_end, z=vs) + cyl_x(p.cart_fl_d / 2, ua, ua + p.cart_fl_t, z=vs)
    seat0 = u_end - p.brg_B - 1.0
    c = c - cyl_x(p.brg_D / 2, seat0, u_end + 1, z=vs)          # asiento (prensado en Al: M7)
    c = c - cyl_x(10.5, uf - 1, seat0 + 0.1, z=vs)              # labio con paso de eje
    for k in range(3):
        a = math.radians(90 + 120 * k)
        c = c - cyl_x(2.2, ua - 1, ua + p.cart_fl_t + 1, y=23 * math.cos(a), z=vs + 23 * math.sin(a))
    return c


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("pared del cartucho sobre el rodamiento [mm]", (p.cart_od - p.brg_D) / 2, 3.0, ">=")]
