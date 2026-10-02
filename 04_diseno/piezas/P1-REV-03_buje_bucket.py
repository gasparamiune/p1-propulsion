"""P1-REV-03 — Buje con brida de POM-C del pivote del bucket (×2), torneado.

Ø(REV_pin_d + 0,1) × REV_bush_od × REV_bush_L (brazo REV_t + aro de refuerzo REV_ring_t) + brida REV_bush_fl_d × 1
entre el brazo y la brida del espaciador P1-REV-02 (luz 1,5 → 0,5 mm). Exterior con 0,05–0,10 mm de interferencia en
el agujero Ø REV_bush_od H7 del bucket; se prensa y DESPUÉS se escaria el interior a Ø(REV_pin_d + 0,1) (el prensado
cierra el juego: auditoría ronda 4, R4-08). Gira sobre el muñón 316 del espaciador. Dimensionado por presión con la
reacción de un pivote cuando su traba lleva SOLA todo M_h (R12 y reversa de sizing): ver structural_direccion."""
from cadlib import cyl_y

META = dict(
    id="P1-REV-03", name="buje_bucket", desc="Buje con brida POM-C del pivote del bucket (Ø20,1/Ø24 × 18 + brida Ø30 × 1), escariado después de prensar",
    material="POM-C", process="torneada", qty=2, frame="bucket", group="jet",
    load_case="Presión: reacción del pivote (chorro/2 + traba con M_h completo, R12 y reversa de sizing)", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
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
            ("luz brida del buje ↔ brida del espaciador [mm]", (p.REV_y_in - p.STE_ear_y1 - p.REV_sp_fl_t) - p.REV_bush_fl_t, 0.3, ">=")]
