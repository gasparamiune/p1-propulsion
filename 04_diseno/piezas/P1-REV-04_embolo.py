"""P1-REV-04 — Émbolo indexador inox (COMPRADO) que traba el bucket ARRIBA y ABAJO.

[ESTIMADO: émbolo indexador A4 M16×1,5 con perno Ø10, carrera ~8 mm, con pomo y retén de tirar;
buscar "GN 617-10-M16 A4" / "Arretierbolzen Edelstahl M16"]. Se enrosca en la oreja +Y de la boquilla
(contratuerca M20 por dentro) y su perno entra en el agujero del brazo del bucket que corresponde a cada
posición: la carga del chorro en reversa (R12: 53–85 N·m en la bisagra) la toma el perno, no el cable
Mach5. Se libera tirando del pomo con un Bowden inox desde el gatillo de la palanca del bucket
(P1-CTL-10); al soltar el gatillo, el resorte lo vuelve a meter (traba automática al llegar).
DOS émbolos (qty 2), uno en cada oreja ±Y (REV_n_locks; auditoría ronda 3: con uno solo la cuchara se
torcía); el gatillo tira de los dos Bowden a la vez (P1-REV-09/10 también ×2)."""
import math
from cadlib import cyl_y

META = dict(
    id="P1-REV-04", name="embolo", desc="Émbolo indexador A4 M20 / perno Ø12 (comprado), uno por oreja ±Y",
    material="AISI 316", process="comprada", qty=2, frame="steer", group="jet",
    load_case="Corte del perno Ø10: momento del bucket en reversa / REV_lock_r", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="—", mass_g=160.0,   # [ESTIMADO: catálogo de émbolos M20]
)


def build(p):
    y0, y1, yi = p.STE_ear_y0, p.STE_ear_y1, p.REV_y_in
    s = cyl_y(p.REV_lock_pin_d / 2, y1 - 0.01, yi + p.REV_t + 1.0)       # perno Ø12
    s = s + cyl_y(9.9, y0, y1)                                         # rosca M20 en la oreja (modelado Ø19,8)
    s = s + cyl_y(15.0, y0 - 8.0, y0)                                  # contratuerca M20 (Ø30)
    s = s + cyl_y(10.0, y0 - 14.0, y0 - 8.0)                           # cuerpo Ø20
    s = s + cyl_y(12.5, y0 - 24.0, y0 - 14.0)                          # pomo Ø25
    return s


def lock_xz(p, side=1):
    a = math.radians(p.REV_lock_ang if side > 0 else p.raw.get("REV_lock_ang_m", p.REV_lock_ang))
    return (p.X_bucket_pivot + p.REV_lock_r * math.cos(a), p.Z_bucket_pivot + p.REV_lock_r * math.sin(a))


def placements(p, steer=0.0, bucket=0):
    from build123d import Pos
    from params import loc_steer
    from build123d import Rot
    x, z = lock_xz(p)
    L = [loc_steer(p, steer) * Pos(x, 0, z)]
    if p.REV_n_locks > 1:
        x2, z2 = lock_xz(p, -1)
        L.append(loc_steer(p, steer) * Pos(x2, 0, z2) * Rot(180, 0, 0))   # gemelo en la oreja −Y (ángulo REV_lock_ang_m)
    return L


def checks(p, part):
    x, z = lock_xz(p)
    ybot = p.STE_ear_y0 - 24.0
    zbody = math.sqrt(max(p.STE_ro ** 2 - ybot ** 2, 0.0))
    znut = math.sqrt(max(p.STE_ro ** 2 - (p.STE_ear_y0 - 8.0) ** 2, 0.0))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("pomo sobre el cuerpo de la boquilla [mm]", (z - 12.5) - zbody, 2.0, ">="),
            ("contratuerca sobre el cuerpo de la boquilla [mm]", (z - 15.0) - znut, 2.0, ">="),
            ("perno sobresale de la cara exterior del brazo [mm]", 1.0, 0.5, ">="),
            ("holgura diametral perno ↔ agujero del brazo [mm]", p.REV_lock_hole_d - p.REV_lock_pin_d, 0.3, ">="),
            ("dos trabas: ejes de los émbolos desfasados ≥ pomo + tuerca del Bowden + 3 (pasan uno al lado del otro) [mm]",
             math.dist(lock_xz(p, 1), lock_xz(p, -1)) if p.REV_n_locks > 1 else 99.0, 12.5 + 5.0 + 3.0, ">="),
            ("pomo −Y sobre el cuerpo de la boquilla [mm]", (lock_xz(p, -1)[1] - 12.5) - zbody, 2.0, ">=")]
