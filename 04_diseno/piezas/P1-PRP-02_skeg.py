"""P1-PRP-02 — Patín (skeg) SACRIFICIAL: va por delante y por debajo de la hélice, toca
primero arena/piedras y empuja la cola hacia arriba (kick-up). Su CINTURA (justo bajo la
carcasa inferior) está dimensionada para romper con F_fusible horizontal en la punta, antes
que tubo/cuna/abrazadera. Atrás, una montura abraza el par de orejas inferiores del
protector (tornillo tangencial M4) y el cuerpo pasa por debajo de ellas."""
import importlib.util
import os
from cadlib import *

META = dict(
    id="P1-PRP-02", name="skeg", desc="Patín sacrificial bajo la hélice (cintura fusible)",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC5 varada/impacto (fusible mecánico)", print_rot=(90, 0, 0), solid_frac=1.0,
    orientation="Plano u–v sobre la cama: flexión en el plano de capas, rotura predecible en la cintura.",
)
LH_BOTTOM = 42.0     # = params lh_bottom
TONGUE = 14.0        # = params skeg_tongue


def _lug(p):
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("gg", os.path.join(here, "_guard_geom.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.lug_geom(p)


def levels(p):
    vs = -p.e
    u_hole, r_hole, r_top, lt, la2, r_prof = _lug(p)
    v_under = vs - r_top - 1.5                       # cara superior del cuerpo bajo las orejas
    v_bot = v_under - 12.0                           # fondo del patín
    return v_under, v_bot


def profile(p):
    vs = -p.e
    R = LH_BOTTOM
    u0, u1 = p.u_lh_fwd, p.u_lh_aft
    s = p.s_prop
    top = vs - R + TONGUE
    v_under, v_bot = levels(p)
    um = 0.5 * (u0 + u1)
    L = p.skeg_neck_len
    vn = p.skeg_neck_v
    u_te = s + p.guard_L / 2
    u_front = min(u1 + 6, s - p.guard_L / 2 - 2.0)   # el patín no invade el borde de ataque del aro
    pts = [(u0 + 8.2, top), (u1 - 8.2, top), (u1 - 8.2, vs - R), (um + L / 2, vs - R),
           (um + L / 2, vn - 4), (u_front, vn - 14),
           (u_front, v_under), (u_te, v_under), (u_te, v_bot),
           (s - 70, v_bot), (um - L / 2, vn - 20), (um - L / 2, vs - R), (u0 + 8.2, vs - R)]
    return pts


def build(p):
    t = p.skeg_t
    sk = prism_xz(profile(p), -t / 2, t / 2)
    vs = -p.e
    R = LH_BOTTOM
    for u in (p.u_lh_fwd + 18, p.u_lh_aft - 18):
        sk = sk - cyl_y(3.2, -t, t, x=u, z=vs - R + TONGUE / 2)
    # montura de las orejas inferiores
    u_hole, r_hole, r_top, lt, la2, r_prof = _lug(p)
    v_under, v_bot = levels(p)
    cw = 5.0
    for sgn in (-1, 1):
        y0, y1 = sorted((sgn * (lt + 0.3), sgn * (lt + 0.3 + cw)))
        sk = sk + box(u_hole - la2, u_hole + la2, y0, y1, v_under - 2.0, vs - r_prof - 1.0)
    sk = sk + box(u_hole - la2, u_hole + la2, -lt - 0.3 - cw, lt + 0.3 + cw, v_under - 6.0, v_under)
    sk = sk - cyl_y(2.2, -lt - cw - 2, lt + cw + 2, x=u_hole, z=vs - r_hole)
    return sk


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    vs = -p.e
    v_under, v_bot = levels(p)
    return [("patín por debajo de la punta de hélice [mm]", (vs - p.prop_D / 2) - v_bot, 15.0, ">="),
            ("largo de la cintura fusible [mm]", p.skeg_neck_len, 12.0, ">=")]
