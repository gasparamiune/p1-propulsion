"""P1-STE-05 — Tornillo con hombro del pivote INFERIOR de la boquilla, AISI 316 torneado (espejo del
P1-STE-02: entra desde abajo, rosca M6 en la oreja inferior de la boquilla)."""
from cadlib import cyl_z

META = dict(
    id="P1-STE-05", name="perno_inf", desc="Tornillo con hombro Ø8 × 13 / M6 del pivote inferior (316)",
    material="AISI 316", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Corte + flexión del hombro: F_steer/2", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="—",
)


def build(p):
    Xp = p.X_steer_pivot
    z0, zh = -p.STE_ear_top, -p.STE_head_z0
    s = cyl_z(p.STE_pin_d_model / 2, zh, z0, x=Xp) + cyl_z(p.STE_head_d / 2, zh - p.STE_head_t, zh, x=Xp)
    return s + cyl_z(2.45, z0 - 0.01, z0 + p.STE_m6_depth - 1.0, x=Xp)


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    zmin = min(P.jet_to_boat(p, p.X_steer_pivot + dx, 0, -p.STE_head_z0 - p.STE_head_t)[2] for dx in (-7, 7))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("cabeza sobre la quilla (z_bote) [mm]", zmin, 5.0, ">=")]
