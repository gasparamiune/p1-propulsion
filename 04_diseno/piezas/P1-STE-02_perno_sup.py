"""P1-STE-02 — Tornillo con hombro del pivote SUPERIOR de la boquilla, AISI 316 torneado.

Hombro Ø8 e8 (interfaz steer_pin_d; modelado Ø7,9) que gira en el agujero Ø8,2 de la oreja de la
bomba (P1-PMP-08), con arandelas de empuje POM-C (P1-STE-03) a ambos lados; el escalón del hombro
apoya en la oreja de la boquilla y la rosca M6 (Loctite 243) entra STE_m6_depth en ella. Cabeza
Ø14 × 3 arriba de la oreja de la bomba (fuera del cuello de la placa de espejo)."""
from cadlib import cyl_z

META = dict(
    id="P1-STE-02", name="perno_sup", desc="Tornillo con hombro Ø8 × 13 / M6 del pivote superior (316)",
    material="AISI 316", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Corte + flexión del hombro (voladizo sobre la oreja): F_steer/2", print_rot=(0, 0, 0),
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
    import math
    rh = math.hypot(p.STE_head_z0 + p.STE_head_t, p.STE_head_d / 2)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("largo del hombro − (oreja + 2 luces) [mm]", (p.STE_head_z0 - p.STE_ear_top) - (p.STE_lug_t + 2 * p.STE_gz), 0.0, "="),
            ("cabeza dentro del cuello de la placa de espejo: r_cuello − r_cabeza [mm]",
             p.raw.get("pmp_tp_bore_R", rh + 1.0) - rh, 0.5, ">="),
            ("rosca útil M6 [mm]", p.STE_m6_depth - 1.0, 6.0, ">=")]
