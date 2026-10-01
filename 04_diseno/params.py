"""params.py — parámetros geométricos del CAD derivados de inputs.yaml y de
resultados/sizing.json (no se edita a mano: cambiar inputs.yaml y correr run_all.py).

Marcos de referencia (ver p1calc/geometry.py):
  BOTE  (x popa, y babor, z arriba), origen: cara exterior del espejo, borde superior, crujía.
  UNIDAD (X=u a lo largo del eje hacia la hélice, Y=w lateral, Z=v "arriba"), origen en el
  eje de basculación. En marcha: rotación Ry(θ) y traslación al pivote.
  HORQUILLA: marco del bote rotado ψ (dirección) alrededor del eje vertical x = x_s.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from p1calc.io import load_inputs  # noqa: E402


@dataclass
class P:
    """Contenedor de parámetros (mm salvo indicación)."""
    raw: dict = field(default_factory=dict)

    def __getattr__(self, k):
        try:
            return self.raw[k]
        except KeyError as e:
            raise AttributeError(k) from e


def load(inputs_path=None, sizing_path=None) -> P:
    inp = load_inputs(inputs_path)
    sp = Path(sizing_path) if sizing_path else ROOT / "resultados" / "sizing.json"
    with open(sp, encoding="utf-8") as f:
        sz = json.load(f)
    lay = sz["layout"]
    sel = sz["selection"]
    g = inp["geometry"]
    m = inp["mount"]
    a = inp["architecture"]
    tr = inp["boat"]["transom"]
    prop = inp["propeller"]["options"][sel["propeller"]]
    motor = inp["motor"]["options"][sel["motor"]]
    brg = inp["bearings"]
    sh = inp["shaft"]
    c = g["clearance_mm"]

    d = {}
    d["inp"] = inp
    d["sz"] = sz
    d["clr"] = c
    d["press"] = g["press_fit_mm"]
    d["bolt_clr"] = g["bolt_clearance_mm"]
    d["wall"] = g["min_wall_mm"]
    d["envelope"] = tuple(inp["printer"]["envelope_mm"])
    d["theta"] = lay["theta_deg"]
    d["e"] = lay["e_mm"]
    d["pivot_x"], d["pivot_z"] = lay["pivot_xz"]
    d["steer_range"] = a["steer_range_deg"]
    d["tilt_range"] = a["tilt_range_deg"]

    # --- espejo (rango de diseño) ---
    d["tr_t"] = tr["thickness_mm"]
    d["tr_t_min"], d["tr_t_max"] = tr["thickness_range_mm"]
    d["tr_H"] = tr["height_mm"]
    d["tr_W"] = tr["top_width_mm"]

    # --- abrazadera (MNT-01) ---
    d["clamp_w"] = m["clamp_width_mm"]                    # ancho a lo largo del espejo (y)
    d["clamp_screw_d"] = m["clamp_screw_d_mm"]
    d["leg_t"] = m["clamp_leg_t_mm"]                      # espesor de patas (FS en structural.py)
    d["bridge_t"] = 18.0                                  # espesor del puente sobre el espejo
    d["leg_depth"] = 130.0                                # largo de patas hacia abajo
    d["pad_t"] = 12.0                                     # espesor de la zapata (MNT-02)
    d["pad_d"] = 40.0
    d["clamp_gap"] = d["tr_t_max"] + 6.0                  # luz interior (espejo máx + holgura)
    d["screw_z"] = [m["clamp_screw_z_mm"]]                # altura de los tornillos de apriete
    d["swivel_x"] = 42.0                                  # eje de dirección (x_s)
    d["swivel_pin_d"] = m["swivel_pin_d_mm"]
    d["swivel_bush_od"] = d["swivel_pin_d"] + 8.0         # buje de POM en el soporte
    d["shelf_top_z"] = 12.0                               # superficie del plato giratorio
    d["boss_bot_z"] = -70.0                               # fondo del buje de dirección
    d["boss_od"] = 46.0

    # --- horquilla (MNT-03 base, MNT-04 mejillas) ---
    d["disc_d"] = 90.0
    d["disc_t"] = 20.0                                    # (FS de la base en structural.py)
    d["washer_t"] = 1.5                                   # arandela UHMW/PTFE bajo el disco
    d["disc_z0"] = d["shelf_top_z"] + d["washer_t"]
    d["cradle_w"] = 76.0                                  # ancho de la cuna (w)
    d["cheek_t"] = 14.0
    d["cheek_gap"] = 1.0                                  # luz cuna–mejilla por lado
    d["cheek_y"] = d["cradle_w"] / 2 + d["cheek_gap"] + d["cheek_t"] / 2  # centro de mejilla
    d["tilt_pin_d"] = m["tilt_pin_d_mm"]
    d["pivot_boss_r"] = 24.0

    # --- cuna (MNT-05), en marco UNIDAD ---
    d["tube_od"] = sh["tube_od_mm"]
    d["tube_wall"] = sh["tube_wall_mm"]
    d["cradle_u0"] = lay["u_plate_aft"]                   # cara delantera (contra la placa motriz)
    d["cradle_u1"] = 95.0                                 # cara trasera
    d["cradle_vtop"] = 30.0                               # tope superior (debajo del motor)
    d["cradle_vbot"] = -d["e"] - d["tube_od"] / 2 - 10.0  # base bajo el tubo (despeje con la base de horquilla)
    d["clamp_bolt_d"] = 6.0

    # --- placa motriz (HSG-01) y puente (HSG-02) ---
    d["plate_t"] = lay["t_plate"]
    d["plate_u_aft"] = lay["u_plate_aft"]
    d["plate_u_fwd"] = lay["u_plate_fwd"]
    d["brg_d"], d["brg_D"], d["brg_B"] = brg["d_mm"], brg["D_mm"], brg["B_mm"]
    dtr = inp["drivetrain"]
    d["cart_od"], d["cart_fl_d"], d["cart_fl_t"] = dtr["cartridge_od_mm"], dtr["cartridge_flange_d_mm"], dtr["cartridge_flange_t_mm"]
    d["stop_pad_d"] = a["stop_pad_d_mm"]
    d["motor_d"], d["motor_l"] = motor["d_mm"], motor["l_mm"]
    d["motor_shaft_d"] = motor["shaft_d_mm"]
    d["motor_bc"] = motor["mount_bolt_circle_mm"]
    d["motor_v"] = lay["motor_v_mm"]
    d["center_dist"] = lay["center_distance_mm"]
    d["tension_slot"] = 8.0                               # carrera de tensado ±
    d["plate_w"] = 96.0
    d["pulley_c"] = lay["u_pulley_c"]
    d["pulley_w"] = lay["w_pulley"]
    belt = sz["mech"]["belt"]
    d["pd_motor"] = belt["d1_mm"]
    d["pd_shaft"] = belt["d2_mm"]
    d["belt_w"] = inp["drivetrain"]["belt_width_mm"]
    d["bridge_t"] = lay["t_bridge"]
    d["bridge_u_aft"] = lay["u_bridge_aft"]
    d["bridge_u_fwd"] = lay["u_bridge_fwd"]
    d["u_brgA"], d["u_brgB"] = lay["u_brgA"], lay["u_brgB"]

    # --- eje, tubo, bujes ---
    d["shaft_d"] = sh["d_mm"]
    d["shaft_jd"] = sh["d_bearing_mm"]
    d["u_shaft_top"] = lay["u_shaft_top"]
    d["u_shaft_bot"] = lay["u_shaft_bot"]
    d["u_tube_top"] = lay["u_tube_top"]
    d["u_tube_bot"] = lay["u_tube_bot"]
    d["bush_len"] = sh["bushing_length_mm"]
    d["u_bush"] = lay["u_bush"]

    # --- carcasa inferior (STR-01), hélice, protector, patín ---
    d["s_prop"] = lay["s_prop_mm"]
    d["prop_D"] = prop["D_mm"]
    d["prop_hub_L"] = prop["hub_length_mm"]
    d["prop_hub_d"] = prop["hub_d_mm"]
    d["u_lh_fwd"], d["u_lh_aft"] = lay["u_lh_fwd"], lay["u_lh_aft"]
    d["guard_clr"] = inp["propeller"]["guard"]["radial_clearance_mm"]
    d["guard_ri"] = d["prop_D"] / 2 + d["guard_clr"]
    gd = inp["propeller"]["guard"]
    d["guard_L"] = gd["profile_length_mm"]
    d["guard_tc"] = gd["profile_thickness_frac"]
    d["guard_t"] = 2 * 5 * d["guard_tc"] * 0.1 * 0 + d["guard_tc"] * d["guard_L"]   # espesor máx. del perfil
    d["guard_segments"] = 6
    d["guard_lug"] = (8.0, 16.0, 10.0)                    # oreja: tangencial, axial, radial sobre el perfil [mm]
    d["skeg_t"] = 12.0
    d["skeg_below_guard"] = 12.0
    d["skeg_fuse_force"] = inp["propeller"]["skeg_fuse_force_n"]
    d["lh_bottom"] = 42.0                                 # carcasa inferior bajo el eje
    d["skeg_tongue"] = 14.0
    # cintura fusible del patín: rompe con F_fuse horizontal en su punta inferior
    pet = inp["materials"]["PETG"]
    sig_break = pet["sigma_t_xy_mpa"] * inp["materials"]["design_factors"]["f_water"]   # resistencia media húmeda
    Ro = d["guard_ri"] + d["guard_t"]
    v_neck = -d["e"] - d["lh_bottom"] - 4.0
    v_tip = -d["e"] - Ro - d["skeg_below_guard"]
    d["skeg_neck_v"] = v_neck
    d["skeg_neck_lever"] = v_neck - v_tip
    d["skeg_neck_len"] = (6 * d["skeg_fuse_force"] * d["skeg_neck_lever"] / (sig_break * d["skeg_t"])) ** 0.5
    d["skeg_sig_break"] = sig_break

    # --- tapa, caña ---
    d["cover_wall"] = 2.4
    d["tiller_tube_od"] = 30.0                            # Al 6061-T6 Ø30×3 (LC7)
    d["tiller_len"] = 550.0                               # tubo de caña (HSG-06)
    d["tiller_angle"] = 25.0                              # = θ: caña paralela al eje de hélice (25° sobre la horizontal en marcha)

    # --- caja ESC ---
    d["esc_in"] = tuple(g["esc_box_inner_mm"])
    d["oring_cs"] = g["oring_cs_mm"]
    d["oring_sq"] = g["oring_squeeze_frac"]
    d["oring_fill"] = g["oring_gland_fill_frac"]

    d["layout"] = lay
    return P(d)


# ---------------------------------------------------------------------------
# Transformaciones de ensamblaje
# ---------------------------------------------------------------------------
def loc_yoke(p: P, steer_deg: float):
    """Marco HORQUILLA → BOTE (rotación ψ alrededor del eje de dirección)."""
    from build123d import Pos, Rot
    xs = p.swivel_x
    return Pos(xs, 0, 0) * Rot(0, 0, steer_deg) * Pos(-xs, 0, 0)


def loc_unit(p: P, steer_deg: float, tilt_deg: float):
    """Marco UNIDAD (X=u, Y=w, Z=v; origen en el pivote) → BOTE."""
    from build123d import Pos, Rot
    return loc_yoke(p, steer_deg) * Pos(p.pivot_x, 0, p.pivot_z) * Rot(0, p.theta - tilt_deg, 0)


if __name__ == "__main__":
    pp = load()
    for k, v in sorted(pp.raw.items()):
        if k in ("inp", "sz", "layout"):
            continue
        print(f"{k:18s} {v}")
