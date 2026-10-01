"""P1-CTL-05 — Prensaestopas M16 IP68 (COMPRADOS, ×2) para la vaina del Mach5 y el Bowden de liberación.

[VERIFICADO: research/R08a §8 — Biltema M16 4–8 mm]. Vaina estática (el cable no desliza en el
prensaestopas). Modelo: cuerpo exterior Ø24 × 10, rosca Ø15,8 × 12, contratuerca Ø24 × 5."""
from cadlib import cyl_x

META = dict(
    id="P1-CTL-05", name="prensaestopas", desc="Prensaestopas M16 IP68 (comprado)",
    material="referencia", process="comprada", qty=2, frame="boat", group="ele",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=15.0,   # [ESTIMADO]
    allow={"P1-REF-01": 1300.0},
)


def build(p):
    s = cyl_x(12.0, -10.0, 0.0) + cyl_x(7.9, -0.01, 12.0) + cyl_x(12.0, 12.0, 17.0)
    return s - cyl_x(4.0, -11, 18)


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    return [Pos(0.0, p.CTL_mach5_pt[1], p.CTL_mach5_pt[2]), Pos(0.0, p.CTL_bowden_pt[1], p.CTL_bowden_pt[2])]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("separación entre prensaestopas − Ø24 [mm]", abs(p.CTL_bowden_pt[1] - p.CTL_mach5_pt[1]) - 24.0, 10.0, ">=")]
