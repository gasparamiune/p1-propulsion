"""P1-HSG-04 — Abrazadera de caña (×2): sujeta el tubo Ø30 a la placa HSG-07 con 2 M6 A4
c/u (tuerca abajo). Media caña con 0.6 mm de interferencia de apriete."""
import math
from cadlib import *

META = dict(
    id="P1-HSG-04", name="tiller_clamp", desc="Abrazadera del tubo de caña sobre la placa Al (×2)",
    material="PETG", process="impresa", qty=2, frame="unit",
    load_case="LC7 manipulación (par de fuerzas entre abrazaderas)", print_rot=(90, 0, 0), solid_frac=1.0,
    orientation="De canto: la media caña y los pernos en el plano de capas.",
)
L_CL = 22.0


def tiller_dir(p):
    th = math.radians(p.theta)
    ang = math.radians(p.tiller_angle)
    wx, wz = -math.cos(ang), math.sin(ang)
    du = wx * math.cos(th) - wz * math.sin(th)
    dv = wx * math.sin(th) + wz * math.cos(th)
    return du, dv


def tiller_axis(p):
    """(u, v) del eje de la caña sobre la placa y su dirección."""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("tp", os.path.join(os.path.dirname(__file__), "P1-HSG-07_tiller_plate.py"))
    tp = importlib.util.module_from_spec(spec); spec.loader.exec_module(tp)
    v = p.cradle_vtop + tp.T_PL + p.tiller_tube_od / 2        # el tubo apoya sobre la placa
    return 57.5, v, tp.W_TILLER


GAP = 1.0     # luz de apriete entre abrazadera y placa (se cierra al apretar → aprieta el tubo)


def build(p):
    """Abrazadera tipo "sombrero" centrada en el eje del tubo (X). El tubo apoya en la placa
    (v = −rt); la abrazadera queda GAP mm sobre la placa y al apretar los 2 M6 lo pisa."""
    rt = p.tiller_tube_od / 2
    blk = box(-L_CL / 2, L_CL / 2, -rt - 8, rt + 8, -rt + GAP, rt + 6)
    blk = blk - cyl_x(rt + 0.1, -L_CL, L_CL)
    for w in (-12.0, 12.0):
        blk = blk - cyl_z(3.25, -rt - 1, rt + 7, y=w)
    return blk


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Pos, Rot
    from params import loc_unit
    u_c, v_c, w_c = tiller_axis(p)
    L = loc_unit(p, steer, tilt)
    return [L * Pos(u, w_c, v_c) for u in (30.0, 85.0)]


def checks(p, part):
    return [("luz de apriete abrazadera–placa [mm]", GAP, 0.6, ">=")]
