"""P1-DRV-01 — Eje de hélice AISI 316 Ø16 (barra h9), torneado: tramo superior Ø15 continuo
(rodamiento B, polea re-mandrinada a Ø15 con plano de prisionero, rodamiento A) que termina en
el hombro Ø16 de empuje; la pila rodamiento A → separador → polea → separador → rodamiento B
se aprieta con la tuerca M12 superior (todo se monta desde arriba). Abajo: asiento de hélice
Ø = bore de la hélice comprada con agujero del pasador de corte. Plano acotado en planos/."""
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
        (f"tramo Ø{p.shaft_jd:g} k5: rodamiento B, polea (plano de prisionero), rodamiento A", lay["u_brgB"] - B / 2 - 2, p.shaft_jd),
        (f"hombro de empuje Ø{p.shaft_d:g}", lay["u_brgA"] + B / 2, p.shaft_d),
        (f"cuerpo Ø{p.shaft_d:g}", lay["u_brgA"] + B / 2 + 3, p.shaft_d),
        (f"asiento de hélice Ø{p.prop_seat_d:g} + pasador de corte", p.s_prop - p.prop_hub_L / 2, p.prop_seat_d),
        ("retención de hélice (rosca/tuerca según la hélice comprada)", p.s_prop + p.prop_hub_L / 2 + 1, min(12.0, p.prop_seat_d - 2)),
        ("extremo inferior", p.u_shaft_bot, min(12.0, p.prop_seat_d - 2)),
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
    st = stations(p)
    # montaje desde arriba: ningún diámetro por encima del hombro supera al muñón
    above = [d for (_, u, d) in st if u < p.layout["u_brgA"] + p.brg_B / 2 - 1e-6]
    return [("largo total del eje", p.u_shaft_bot - p.u_shaft_top, p.layout["shaft_length_mm"], "≈"),
            ("Ø máx. sobre el hombro − Ø muñón (montaje desde arriba) [mm]", max(above) - p.shaft_jd, 0.0, "<=")]
