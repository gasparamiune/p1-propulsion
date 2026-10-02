"""P1-STE-03 — Arandela de empuje de POM-C (×3) de los pivotes de la boquilla, torneada.

Ø8,4 × Ø18 × 1: entre cada oreja de la boquilla y la de la bomba, y entre la oreja superior de la
bomba y la mejilla superior (luz axial 1,5 → 0,5 mm). Pieza de desgaste reemplazable."""
from cadlib import cyl_z

META = dict(
    id="P1-STE-03", name="arandela_pom", desc="Arandela de empuje POM-C Ø8,4/Ø18 × 1",
    material="POM-C", process="torneada", qty=3, frame="steer", group="jet",
    load_case="Empuje axial: peso de la boquilla + bucket y componente vertical del chorro",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def build(p):
    return cyl_z(p.STE_wash_od / 2, 0, p.STE_wash_t) - cyl_z(p.STE_wash_id / 2, -1, p.STE_wash_t + 1)


def zs(p):
    a = p.STE_ear_top
    b = p.Z_steer_lug + p.STE_lug_t + (p.STE_gz - p.STE_wash_t) / 2
    return [a, b, -a - p.STE_wash_t]


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    from params import loc_steer
    L0 = loc_steer(p, steer)
    return [L0 * Pos(p.X_steer_pivot, 0, z) for z in zs(p)]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("luz arandela ↔ oreja de la bomba [mm]", p.STE_gz - p.STE_wash_t, 0.3, ">="),
            ("holgura diametral arandela ↔ hombro [mm]", p.STE_wash_id - p.STE_pin_d_model, 0.3, ">=")]
