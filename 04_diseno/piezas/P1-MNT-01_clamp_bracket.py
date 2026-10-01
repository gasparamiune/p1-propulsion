"""P1-MNT-01 — Abrazadera de popa en C con plato de dirección y buje vertical.

Marco: BOTE. Apoya sobre el borde del espejo (z=0) y la cara exterior (x=0); dos
tornillos M12 A4 con zapata (MNT-02) aprietan contra la cara interior. Cubre espejos de
t_min..t_max. Arriba ofrece el plano de apoyo (z = shelf_top_z) del plato giratorio de
la horquilla y el buje de POM del perno de dirección (x = x_s).
"""
from cadlib import *
from params import loc_yoke  # noqa: F401

META = dict(
    id="P1-MNT-01", name="clamp_bracket", desc="Abrazadera de popa (C) + plato de dirección",
    material="PETG", process="impresa", qty=1, frame="boat",
    load_case="LC5 impacto (reacción en pivote) / LC1 empuje / LC7 manipulación",
    print_rot=(90, 0, 0), solid_frac=0.85,
    orientation="Perfil x-z sobre la cama (ancho y = Z de impresión): cargas en el plano XY de capas.",
)


def build(p):
    W = p.clamp_w
    x_in1 = -p.clamp_gap - p.leg_t          # cara interior de la pata interior
    x_in0 = -p.clamp_gap
    top = p.shelf_top_z
    outer = box(0, p.leg_t, -W / 2, W / 2, -p.leg_depth, top)
    bridge = box(x_in1, p.leg_t, -W / 2, W / 2, 0, top)
    inner = box(x_in1, x_in0, -W / 2, W / 2, -p.leg_depth, top)
    body = outer + bridge + inner
    # plato/estante de dirección hacia popa
    xs = p.swivel_x
    shelf_x1 = xs + 45.0
    shelf = box(p.leg_t, shelf_x1, -48, 48, top - 14, top)
    boss = cyl_z(p.boss_od / 2, p.boss_bot_z, top, x=xs)
    web = box(p.leg_t, xs, -16, 16, p.boss_bot_z, top)
    gus = []
    for y0 in (-48, 36):
        gus.append(prism_xz([(p.leg_t, p.boss_bot_z), (p.leg_t, top - 14), (shelf_x1, top - 14)], y0, y0 + 12))
    body = body + shelf + boss + web + gus[0] + gus[1]
    # buje de dirección (POM) pasante
    body = body - cyl_z((p.swivel_bush_od + p.clr) / 2, p.boss_bot_z - 1, top + 1, x=xs)
    # tornillos de apriete M12 con tuerca cautiva (empuje hacia el espejo)
    d = p.clamp_screw_d
    for y in (-45, 45):
        for z in (-70,):
            body = body - cyl_x((d + p.bolt_clr) / 2, x_in1 - 1, x_in0 + 1, y=y, z=z)
            body = body - hex_prism_x(NUT_AF[d] + 0.3, x_in0 - NUT_M[d] - 0.6, x_in0 + 0.1, y=y, z=z)
    # ojal para cabo de seguridad secundario (Ø10)
    body = body - cyl_y(5, -W / 2 - 1, -W / 2 + 20, x=x_in1 + 11, z=-p.leg_depth + 14)
    return body


def placements(p, steer=0.0, tilt=0.0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    bb = part.bounding_box()
    gap = p.clamp_gap
    return [
        ("luz interior abrazadera ≥ espejo máx + 4 mm", gap, p.tr_t_max + 4, ">="),
        ("buje de dirección Ø", 2 * max(r for r in cyl_radii(part) if r < 13), p.swivel_bush_od + p.clr, "≈"),
        ("altura de patas ≥ 120 mm", p.leg_depth, 120.0, ">="),
        ("ancho a lo largo del espejo", bb.max.Y - bb.min.Y, p.clamp_w, "≈"),
    ]
