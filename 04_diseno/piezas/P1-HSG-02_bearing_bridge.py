"""P1-HSG-02 — Puente del rodamiento B (flotante) delante de las poleas.
Tira vertical desde debajo del rodamiento B hasta por encima de la polea del motor, donde
2 separadores torneados (DRV-03) + pernos M6 A4 la unen a la placa motriz, FUERA del lazo
de la correa. El tiro de la correa sobre el rodamiento B apunta hacia el motor (+v):
el puente trabaja en tracción en su plano (línea de fuerza por los apoyos)."""
from cadlib import *

META = dict(
    id="P1-HSG-02", name="bearing_bridge", desc="Puente del rodamiento B (polea entre apoyos)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC3/LC4 tiro de correa (reacción R_B)", print_rot=(0, -90, 0), solid_frac=1.0,
    orientation="Plana (u = Z): reacción radial en el plano de capas; alojamiento vertical.",
)


def spacer_points(p):
    """(v, w) de los separadores: a los costados de la polea del motor, fuera del lazo de la
    correa (ramal de correa a |w| ≈ r_pm + 3.8 mm) y fuera de la brida de la polea."""
    w = p.pd_motor / 2 + 3.0 + 3.0 + 6.0 + 1.0
    return [(p.motor_v, -w), (p.motor_v, w)]


def build(p):
    vs = -p.e
    sp = spacer_points(p)
    ws = abs(sp[0][1])
    vtop = sp[0][0] + 9
    b = box(p.bridge_u_fwd, p.bridge_u_aft, -22, 22, vs - 24, vs + 10)
    b = b + box(p.bridge_u_fwd, p.bridge_u_aft, -12, 12, vs, vtop)
    b = b + box(p.bridge_u_fwd, p.bridge_u_aft, -ws - 9, ws + 9, sp[0][0] - 9, vtop)
    # alojamiento del rodamiento B (pasante: el aro exterior flota; lo ubica axialmente la pila del eje)
    # deslizante (+0,1) y 1 mm más profundo que el rodamiento: B flota axialmente (A es el localizador)
    b = b - cyl_x((p.brg_D + 0.1) / 2, p.bridge_u_aft - p.brg_B - 2.5, p.bridge_u_aft + 1, z=vs)
    b = b - cyl_x(10.5, p.bridge_u_fwd - 1, p.bridge_u_aft, z=vs)
    for v, w in sp:
        b = b - cyl_x(3.2, p.bridge_u_fwd - 1, p.bridge_u_aft + 1, y=w, z=v)
    return b


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("espesor de puente", p.bridge_t, 10.0, ">=")]
