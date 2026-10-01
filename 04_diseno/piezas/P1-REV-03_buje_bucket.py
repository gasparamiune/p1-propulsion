"""P1-REV-03 — Buje con brida de POM-C del pivote del bucket (×2), torneado.

Ø10,1 × Ø14 × 8 (brazo 4 + aro de refuerzo 4) + brida Ø20 × 1 entre brazo y oreja (luz 1,5 → 0,5 mm).
Prensado en el bucket; gira sobre el hombro Ø10 del perno P1-REV-02."""
from cadlib import cyl_y

META = dict(
    id="P1-REV-03", name="buje_bucket", desc="Buje con brida POM-C Ø10,1/Ø14 × 8 + brida Ø20 × 1",
    material="POM-C", process="torneada", qty=2, frame="bucket", group="jet",
    load_case="Aplastamiento: reacción del bucket / 2", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
)


def build(p):
    s = cyl_y(p.REV_bush_od / 2, 0.0, p.REV_bush_L) + cyl_y(p.REV_bush_fl_d / 2, -p.REV_bush_fl_t, 0.0)
    return s - cyl_y((p.REV_pin_d + 0.1) / 2, -2, p.REV_bush_L + 1)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos, Rot
    from params import loc_bucket
    L0 = loc_bucket(p, bool(bucket), steer)
    Xb, Zb, y = p.X_bucket_pivot, p.Z_bucket_pivot, p.REV_y_in
    return [L0 * Pos(Xb, y, Zb), L0 * Pos(Xb, -y, Zb) * Rot(0, 0, 180)]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pared del buje [mm]", (p.REV_bush_od - p.REV_pin_d - 0.1) / 2, 1.5, ">="),
            ("luz brida ↔ oreja [mm]", (p.REV_y_in - p.STE_ear_y1) - p.REV_bush_fl_t, 0.3, ">=")]
