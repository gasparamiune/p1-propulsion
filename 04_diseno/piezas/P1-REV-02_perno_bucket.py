"""P1-REV-02 — Perno con hombro del pivote del bucket, AISI 316 torneado (×2).

Hombro Ø10 (f7) × 9,8 que apoya en la cara exterior de la oreja de la boquilla (Y = ±48) y deja
0,3 mm de juego axial al brazo + refuerzo del bucket; rosca M8 que atraviesa la oreja (Ø8,4) con tuerca
autoblocante A4 por dentro (entre las orejas, sobre la boquilla). Cabeza Ø16 × 6. Marco local: eje +y
desde la cara exterior de la oreja."""
from cadlib import cyl_y

META = dict(
    id="P1-REV-02", name="perno_bucket", desc="Perno con hombro Ø10 × 9,8 / M8 del bucket (316)",
    material="AISI 316", process="torneada", qty=2, frame="steer", group="jet",
    load_case="Corte simple + flexión: reacción del bucket (R12 1,4 kN × impacto 2) / 2",
    print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def shoulder_L(p):
    return (p.REV_y_in + 2 * p.REV_t + 0.3) - p.STE_ear_y1


def build(p):
    L = shoulder_L(p)
    s = cyl_y(p.REV_pin_d / 2, 0.0, L) + cyl_y(p.REV_head_d / 2, L, L + p.REV_head_t)
    s = s + cyl_y(3.9, -(p.STE_ear_y1 - p.STE_ear_y0) - 10.0, 0.01)       # M8 (modelado Ø7,8)
    return s


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    from params import loc_steer
    L0 = loc_steer(p, steer)
    Xb, Zb, y = p.X_bucket_pivot, p.Z_bucket_pivot, p.STE_ear_y1
    return [L0 * Pos(Xb, y, Zb), L0 * Pos(Xb, -y, Zb) * Rot(0, 0, 180)]


def checks(p, part):
    L = shoulder_L(p)
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("juego axial del bucket en el hombro [mm]", L - (p.REV_y_in + 2 * p.REV_t - p.STE_ear_y1), 0.2, ">="),
            ("rosca útil para tuerca M8 (≥ 8 + 2 hilos) [mm]", 10.0, 9.5, ">=")]
