"""P1-STE-05 — Espárrago con hombro del pivote INFERIOR de la boquilla, AISI 316 torneado.

Sin cabeza (la oreja inferior de la bomba llega casi a la quilla): rosca M6 (Loctite 243) en la oreja
inferior de la boquilla, hombro Ø8 e8 que entra en el buje POM de la oreja de la bomba y termina 1 mm
adentro; hexágono interior 4 en la punta para el apriete. La reacción del bucket va casi toda al
pivote superior (el bucket empuja a Z = Z_bucket_pivot): este perno toma ~F_s/2."""
from cadlib import cyl_z

META = dict(
    id="P1-STE-05", name="perno_inf", desc="Espárrago con hombro Ø8 / M6 del pivote inferior (316)",
    material="AISI 316", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Flexión en voladizo + corte: F_s/2", print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="—",
)


def z_end(p):
    return -(p.Z_steer_lug + p.STE_lug_t - 1.0)


def build(p):
    Xp = p.X_steer_pivot
    z0 = -p.STE_ear_top
    s = cyl_z(p.STE_pin_d_model / 2, z_end(p), z0, x=Xp)
    return s + cyl_z(2.45, z0 - 0.01, z0 + p.STE_m6_depth - 1.0, x=Xp)


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    zmin = min(P.jet_to_boat(p, p.X_steer_pivot + dx, 0, z_end(p))[2] for dx in (-4, 4))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("punta dentro del buje de la bomba [mm]", (p.Z_steer_lug + p.STE_lug_t) - abs(z_end(p)), 0.5, ">="),
            ("punta sobre la quilla (z_bote) [mm]", zmin, 2.0, ">=")]
