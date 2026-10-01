"""P1-PRP-02 — Patín (skeg) SACRIFICIAL: va por delante y por debajo de la hélice, toca
primero arena/piedras y empuja la cola hacia arriba (kick-up). Su cuello (lengüeta en la
carcasa inferior) está dimensionado para romper antes que tubo/cuna/abrazadera."""
from cadlib import *

META = dict(
    id="P1-PRP-02", name="skeg", desc="Patín sacrificial bajo la hélice",
    material="PETG", process="impresa", qty=1, frame="unit",
    load_case="LC5 varada/impacto (fusible mecánico)", print_rot=(90, 0, 0), solid_frac=1.0,
    orientation="Plano u–v sobre la cama: flexión en el plano de capas, rotura predecible en el cuello.",
)


LH_BOTTOM = 42.0
TONGUE = 14.0


def profile(p):
    vs = -p.e
    R = LH_BOTTOM
    u0, u1 = p.u_lh_fwd, p.u_lh_aft
    s = p.s_prop
    Ro = p.guard_ri + p.guard_t
    vring = vs - Ro                     # cara exterior inferior del anillo
    vbot = vring - p.skeg_below_guard
    top = vs - R + TONGUE               # tope de la lengüeta (dentro de la ranura)
    pts = [(u0 + 8.2, top), (u1 - 8.2, top), (u1 - 8.2, vs - R), (s - p.prop_D / 2 * 0 - 40, vs - R),
           (s - 40, vring), (s + p.guard_L / 2, vring), (s + p.guard_L / 2, vbot),
           (s - 70, vbot), (u0 + 8.2, vs - R - 30)]
    return pts


def build(p):
    t = p.skeg_t
    sk = prism_xz(profile(p), -t / 2, t / 2)
    vs = -p.e
    R = LH_BOTTOM
    for u in (p.u_lh_fwd + 18, p.u_lh_aft - 18):
        sk = sk - cyl_y(3.2, -t, t, x=u, z=vs - R + TONGUE / 2)
    # tornillo M4 al anillo (abajo)
    Ro = p.guard_ri + p.guard_t
    sk = sk - cyl_z(2.2, vs - Ro - p.skeg_below_guard - 1, vs - Ro + 1, x=p.s_prop)
    sk = sk - hex_prism_z(NUT_AF[4] + 0.3, vs - Ro - p.skeg_below_guard - 0.1, vs - Ro - p.skeg_below_guard + 4, x=p.s_prop)
    return sk


def placements(p, steer=0.0, tilt=0.0):
    from params import loc_unit
    return [loc_unit(p, steer, tilt)]


def checks(p, part):
    vs = -p.e
    Ro = p.guard_ri + p.guard_t
    return [("patín por debajo de la punta de hélice [mm]", (vs - p.prop_D / 2) - (vs - Ro - p.skeg_below_guard), 15.0, ">=")]
