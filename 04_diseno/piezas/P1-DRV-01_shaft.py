"""P1-DRV-01 — Eje de hélice AISI 316 Ø16 (barra h9), torneado: muñones Ø15 para 6002,
asiento de polea con plano de prisionero, agujero del pasador de corte, rosca de tuerca
de hélice y ranura de chaveta/collar superior. Plano acotado en planos/."""
from cadlib import *

META = dict(id="P1-DRV-01", name="shaft", desc="Eje de hélice 316 Ø16 torneado",
            material="AISI 316", process="torneada", qty=1, frame="unit",
            load_case="LC3/LC4 torsión, flexión por correa, fatiga", print_rot=(0, 0, 0), solid_frac=1.0,
            orientation="—")


def stations(p):
    """Estaciones (u) y diámetros del eje torneado — usadas también por el plano."""
    lay = p.layout
    B = p.brg_B
    s = [
        ("extremo superior (rosca M12×1.25 + tuerca)", p.u_shaft_top, 12.0),
        ("muñón rodamiento B Ø15", lay["u_brgB"] - B / 2 - 2, p.shaft_jd),
        ("asiento de polea Ø16 (plano prisionero)", lay["u_brgB"] + B / 2 + 1, p.shaft_d),
        ("muñón rodamiento A Ø15", lay["u_brgA"] - B / 2 - 1, p.shaft_jd),
        ("hombro de empuje Ø16", lay["u_brgA"] + B / 2, p.shaft_d),
        ("cuerpo Ø16", lay["u_brgA"] + B / 2 + 3, p.shaft_d),
        ("asiento de hélice Ø16 + pasador de corte", p.s_prop - p.prop_hub_L / 2, p.shaft_d),
        ("rosca de tuerca de hélice M12", p.s_prop + p.prop_hub_L / 2 + 1, 12.0),
        ("extremo inferior", p.u_shaft_bot, 12.0),
    ]
    return s


def build(p):
    vs = -p.e
    st = stations(p)
    shaft = None
    for i in range(len(st) - 1):
        u0, u1, d = st[i][1], st[i + 1][1], st[i][2]
        seg = cyl_x(d / 2, u0, u1, z=vs)
        shaft = seg if shaft is None else shaft + seg
    return shaft


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    return [("largo total del eje", p.u_shaft_bot - p.u_shaft_top, p.layout["shaft_length_mm"], "≈")]
