"""Geometría maestra de la cola larga (long-tail). Fuente única para sizing y CAD.

Sistema de coordenadas del BOTE (mm):
    origen en la cara EXTERIOR del espejo, a la altura del BORDE SUPERIOR, en crujía.
    x: hacia popa (afuera del bote) ;  y: a babor ;  z: arriba.
    El espejo ocupa x ∈ [−t_esp, 0], z ∈ [−H_esp, 0].

Sistema LOCAL de la unidad basculante (marco de la cuna), origen en el eje de
basculación (pivote):
    u: a lo largo del eje de la hélice, hacia la hélice ;  v: perpendicular "arriba"
    (lado del motor) ;  w: lateral (= y en marcha recta).
    La línea del eje está en v = −e.  En marcha: û = (cosθ, 0, −sinθ), v̂ = (sinθ, 0, cosθ).

Estaciones a lo largo de u (de proa a popa):
    tuerca | polea conducida | placa motriz (rodamiento delantero) | buje con rodamiento
    trasero | entrada del tubo | cuna (pivote) | ... tubo ... | carcasa inferior (buje
    inferior) | hélice | tuerca
"""
from __future__ import annotations

import math


def layout(inp: dict, draft_m: float) -> dict:
    a = inp["architecture"]
    b = inp["boat"]
    pr = inp["propeller"]["options"][inp["propeller"]["chosen"]]
    dt = inp["drivetrain"]
    brg = inp["bearings"]

    th = math.radians(a["shaft_angle_deg"])
    H = b["transom"]["height_mm"]
    t_tr = b["transom"]["thickness_mm"]
    xp, zp = a["pivot_aft_of_transom_mm"], a["pivot_height_above_transom_mm"]
    e = a["shaft_line_offset_below_pivot_mm"]
    D = pr["D_mm"]

    z_wl = -H + draft_m * 1000.0                        # flotación en el espejo
    h_c = D / 2 + a["prop_tip_immersion_frac_D"] * D    # profundidad del centro de hélice
    # punto P0 de la línea de eje más cercano al pivote
    P0 = (xp - e * math.sin(th), zp - e * math.cos(th))
    s_prop = (P0[1] - (z_wl - h_c)) / math.sin(th)      # distancia P0→centro de hélice
    x_prop = P0[0] + s_prop * math.cos(th)
    z_prop = z_wl - h_c

    hub_L = pr["hub_length_mm"]
    # --- placa motriz de Al (con cartucho torneado del rodamiento A), poleas y puente (rodamiento B) ---
    motor = inp["motor"]["options"][inp["motor"]["chosen"]]
    w_pulley = dt["belt_width_mm"] + 6.0                  # ancho de polea (bridas)
    t_plate = dt["drive_plate_t_mm"]
    if t_plate + 2.0 + w_pulley > motor["shaft_protrusion_mm"]:
        raise ValueError("el eje del motor no alcanza la polea: placa demasiado gruesa")
    u_plate_aft = -a["shaft_top_ahead_of_pivot_mm"]       # cara de popa de la placa = cara delantera de la cuna
    u_plate_fwd = u_plate_aft - t_plate
    t_fl = dt["cartridge_flange_t_mm"]
    u_brgA = u_plate_aft + t_fl + brg["B_mm"] / 2         # rodamiento A (localizador, axial) en el cartucho
    u_boss_aft = u_plate_aft + t_fl + brg["B_mm"] + 1.0   # extremo de popa del cartucho
    boss_len = u_boss_aft - u_plate_fwd
    u_pulley_c = u_plate_fwd - 2.0 - w_pulley / 2         # plano de correa (ambas poleas)
    t_bridge = 12.0                                       # espesor del puente [SUPUESTO]
    u_bridge_aft = u_pulley_c - w_pulley / 2 - 3.0
    u_bridge_fwd = u_bridge_aft - t_bridge
    u_brgB = u_bridge_aft - 1.5 - brg["B_mm"] / 2         # rodamiento B (flotante)
    u_shaft_top = u_bridge_fwd - 10.0                     # collar + tuerca en el extremo
    # --- tubo ---
    u_tube_top = u_boss_aft + 8.0                         # el tubo arranca detrás del rebaje del buje
    lower_housing_L = 55.0                                # [SUPUESTO]
    gap_hub = 6.0                                         # luz cubo–carcasa inferior
    u_lh_aft = s_prop - hub_L / 2 - gap_hub               # cara de popa carcasa inferior
    u_lh_fwd = u_lh_aft - lower_housing_L
    u_tube_bot = u_lh_fwd + 45.0                          # el tubo entra 45 mm en la carcasa
    u_shaft_bot = s_prop + hub_L / 2 + 22.0               # tuerca + chaveta
    # --- apoyos del eje: 2 rodamientos + bujes de agua ---
    bl = inp["shaft"]["bushing_length_mm"]
    u_bush_top = u_tube_top + 2.0 + bl / 2
    u_bush_bot = u_tube_bot - 2.0 - bl / 2                # buje inferior dentro del extremo del tubo
    u_bush_mid = 0.5 * (u_bush_top + u_bush_bot)
    supports = [u_brgB, u_brgA, u_bush_top, u_bush_mid, u_bush_bot]
    spans = [supports[i + 1] - supports[i] for i in range(len(supports) - 1)]

    return {
        "theta_rad": th, "theta_deg": a["shaft_angle_deg"],
        "pivot_xz": (xp, zp), "e_mm": e, "P0_xz": P0,
        "z_wl_mm": z_wl, "prop_center_depth_mm": h_c,
        "s_prop_mm": s_prop, "prop_xz": (x_prop, z_prop), "D_mm": D,
        "prop_tip_low_z_mm": z_prop - D / 2,
        "keel_z_mm": -H, "transom_t_mm": t_tr, "transom_H_mm": H,
        "u_plate_aft": u_plate_aft, "u_plate_fwd": u_plate_fwd, "t_plate": t_plate,
        "u_brgA": u_brgA, "u_brgB": u_brgB,
        "u_bridge_aft": u_bridge_aft, "u_bridge_fwd": u_bridge_fwd, "t_bridge": t_bridge,
        "u_boss_aft": u_boss_aft, "boss_len": boss_len,
        "u_pulley_c": u_pulley_c, "w_pulley": w_pulley,
        "u_shaft_top": u_shaft_top, "u_shaft_bot": u_shaft_bot,
        "u_tube_top": u_tube_top, "u_tube_bot": u_tube_bot,
        "u_lh_fwd": u_lh_fwd, "u_lh_aft": u_lh_aft, "lower_housing_L": lower_housing_L,
        "u_bush": [u_bush_top, u_bush_mid, u_bush_bot],
        "supports_u": supports, "spans_mm": spans,
        "max_span_mm": max(spans[1:]),      # vanos entre bujes (el vano entre rodamientos es corto)
        "shaft_length_mm": u_shaft_bot - u_shaft_top,
        "tube_length_mm": u_tube_bot - u_tube_top,
        "pulley_a_mm": u_brgA - u_pulley_c,           # polea → rodamiento A
        "pulley_b_mm": u_pulley_c - u_brgB,           # polea → rodamiento B
        "bearing_spacing_mm": u_brgA - u_brgB,
        "prop_overhang_mm": s_prop - u_bush_bot,
        "center_distance_mm": dt["center_distance_mm"],
        "motor_v_mm": -e + dt["center_distance_mm"],   # eje del motor en v (local)
        "hub_L_mm": hub_L,
    }


def local_to_boat(u: float, v: float, theta_rad: float, pivot_xz, tilt_rad: float = 0.0):
    """Convierte (u, v) local → (x, z) del bote para basculación tilt_rad (+ = cola arriba)."""
    ang = -theta_rad + tilt_rad          # ángulo de û respecto de +x
    ux, uz = math.cos(ang), math.sin(ang)
    vx, vz = -math.sin(ang), math.cos(ang)
    return (pivot_xz[0] + u * ux + v * vx, pivot_xz[1] + u * uz + v * vz)
