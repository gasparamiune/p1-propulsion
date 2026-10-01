"""P1-CTL-01 — Placa interior de refuerzo del espejo para los cables de mando, Al 5083 6 mm.

Va por DENTRO del espejo (x ∈ [transom_t, transom_t + 6]), por encima de la flotación estática
(calado de sizing), con 6 × M6 A4 pasantes (arandelas grandes afuera, Sikaflex) y los 3 pasos:
  - pasamuros del cable de dirección Ultraflex M66 (P1-CTL-04, 316) donde se enrosca su tubo
    (P1-CTL-06) y por el que sale la barra hacia la biela del yugo;
  - 2 prensaestopas M16 IP68 (P1-CTL-05, R08a) para la vaina del Mach5 del bucket y el Bowden de
    liberación del émbolo (vainas ESTÁTICAS: el bucle libre hasta la boquilla absorbe la dirección).
Reparte el tiro del M66 (≈ 400 N) en el espejo de 6 mm."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_x  # noqa: E402
import _transom as T  # noqa: E402

META = dict(
    id="P1-CTL-01", name="placa_espejo", desc="Placa interior del espejo para M66 + 2 prensaestopas (Al 5083 6 mm)",
    material="Al 5083", process="torneada", qty=1, frame="boat", group="ele",
    load_case="Reacción del M66 (momento de dirección / brazo) en el espejo", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="Corte láser + taladrado; plano en planos_direccion",
)


def build(p):
    x0 = p.transom_t
    s = box(x0, x0 + T.PLATE_T, *T.PLATE_Y, *T.PLATE_Z)
    for y, z, d, _ in T.holes(p):
        s = s - cyl_x(d / 2, x0 - 1, x0 + T.PLATE_T + 1, y=y, z=z)
    return s


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    wl = p.sz["hydrostatics"]["draft_m"] * 1000
    zt = p.inp["boat"]["transom_height_m"] * 1000
    edge = min(min(abs(y - T.PLATE_Y[0]), abs(T.PLATE_Y[1] - y), abs(z - T.PLATE_Z[0]), abs(T.PLATE_Z[1] - z)) - d / 2
               for y, z, d, _ in T.holes(p))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pasos sobre la flotación estática (z mín. − Ø/2 − calado) [mm]",
             min(z - d / 2 for _, z, d, _t in T.holes(p)[:3]) - wl, 30.0, ">="),
            ("placa bajo el borde del espejo [mm]", zt - T.PLATE_Z[1], 5.0, ">="),
            ("borde mínimo agujero ↔ canto [mm]", edge, 6.0, ">=")]
