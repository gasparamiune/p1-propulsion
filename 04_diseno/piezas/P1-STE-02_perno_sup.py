"""P1-STE-02 — Tornillo con hombro del pivote SUPERIOR de la boquilla, AISI 316 torneado.

Doble apoyo: entra desde arriba por la mejilla superior de la boquilla (Ø8,2), atraviesa el buje POM
de la oreja de la bomba (P1-PMP-11, Ø8,1 — ahí gira) y se rosca M6 (Loctite 243) en la oreja inferior
de la boquilla; el escalón del hombro apoya en esa oreja. Hombro Ø8 e8 (interfaz steer_pin_d;
modelado Ø7,9), cabeza Ø14 × 3 sobre la mejilla, hexágono interior 5."""
from cadlib import cyl_z

META = dict(
    id="P1-STE-02", name="perno_sup", desc="Tornillo con hombro Ø8 / M6 del pivote superior (316 estirado)",
    material="AISI 316", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Flexión en doble apoyo + corte: reacción superior (bucket R12 + dirección)", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—",
)


def build(p):
    Xp = p.X_steer_pivot
    z0, zh = p.STE_ear_top, p.STE_head_z0
    s = cyl_z(p.STE_pin_d_model / 2, z0, zh, x=Xp) + cyl_z(p.STE_head_d / 2, zh, zh + p.STE_head_t, x=Xp)
    return s + cyl_z(2.45, z0 - p.STE_m6_depth + 1.0, z0 + 0.01, x=Xp)       # M6 (modelado Ø4,9)


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    need = p.STE_lug_t + 2 * p.STE_gz + p.STE_cheek_t
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("largo del hombro − (oreja de bomba + 2 luces + mejilla) [mm]", (p.STE_head_z0 - p.STE_ear_top) - need, 0.0, "="),
            ("rosca útil M6 [mm]", p.STE_m6_depth - 1.0, 6.0, ">=")]
