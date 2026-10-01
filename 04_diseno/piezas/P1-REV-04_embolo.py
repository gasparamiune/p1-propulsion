"""P1-REV-04 — Émbolo indexador inox (COMPRADO) que traba el bucket ARRIBA y ABAJO.

[ESTIMADO: émbolo indexador A4 M16×1,5 con perno Ø10, carrera ~8 mm, con pomo y retén de tirar;
buscar "GN 617-10-M16 A4" / "Arretierbolzen Edelstahl M16"]. Se enrosca en la oreja +Y de la boquilla
(contratuerca por dentro) y su perno entra en el agujero del brazo del bucket que corresponde a cada
posición: la carga del chorro en reversa (R12: 53–85 N·m en la bisagra) la toma el perno, no el cable
Mach5. Se libera tirando del pomo con un Bowden inox desde el gatillo de la palanca del bucket
(P1-CTL-10); al soltar el gatillo, el resorte lo vuelve a meter (traba automática al llegar)."""
import math
from cadlib import cyl_y

META = dict(
    id="P1-REV-04", name="embolo", desc="Émbolo indexador A4 M16 / perno Ø10 (comprado)",
    material="AISI 316", process="comprada", qty=1, frame="steer", group="jet",
    load_case="Corte del perno Ø10: momento del bucket en reversa / REV_lock_r", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—", mass_g=110.0,   # [ESTIMADO: catálogo de émbolos M16]
)


def build(p):
    y0, y1, yi = p.STE_ear_y0, p.STE_ear_y1, p.REV_y_in
    s = cyl_y(p.REV_lock_pin_d / 2, y1 - 0.01, yi + p.REV_t + 1.0)       # perno
    s = s + cyl_y(7.9, y0, y1)                                         # rosca en la oreja (modelado Ø15,8)
    s = s + cyl_y(12.0, y0 - 7.0, y0)                                  # contratuerca M16 (Ø24)
    s = s + cyl_y(8.0, y0 - 14.0, y0 - 7.0)                            # cuerpo
    s = s + cyl_y(10.0, y0 - 24.0, y0 - 14.0)                          # pomo Ø20
    return s


def lock_xz(p):
    a = math.radians(p.REV_lock_ang)
    return (p.X_bucket_pivot + p.REV_lock_r * math.cos(a), p.Z_bucket_pivot + p.REV_lock_r * math.sin(a))


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    from params import loc_steer
    x, z = lock_xz(p)
    return [loc_steer(p, steer) * Pos(x, 0, z)]


def checks(p, part):
    x, z = lock_xz(p)
    ybot = p.STE_ear_y0 - 24.0
    zbody = math.sqrt(max(p.STE_ro ** 2 - ybot ** 2, 0.0))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pomo sobre el cuerpo de la boquilla [mm]", (z - 10.0) - zbody, 2.0, ">="),
            ("perno sobresale de la cara exterior del brazo [mm]", 1.0, 0.5, ">="),
            ("holgura diametral perno ↔ agujero del brazo [mm]", p.REV_lock_hole_d - p.REV_lock_pin_d, 0.3, ">=")]
