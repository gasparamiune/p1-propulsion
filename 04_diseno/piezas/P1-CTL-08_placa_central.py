"""P1-CTL-08 — Placa central de la unidad de palancas, Al 5083 6 mm (con ala doblada y grapas soldadas).

Soporta el eje (P1-CTL-11, Ø12 H8 con grasa), aloja los 2 pernos de enclavamiento (P1-CTL-12) entre la
palanca del acelerador y la del bucket, y lleva las 2 grapas de la vaina del Mach5 de la consola. Se
abulona POR DEBAJO de la tapa de la consola con 2 × M6 (la caja PETG P1-CTL-02 solo cubre): las fuerzas
de mano (100 N) y del cable no pasan por el PETG."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y, cyl_z, prism_xz  # noqa: E402
from _dir_common import circ, hull  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-08", name="placa_central", desc="Placa central de palancas Al 5083 6 mm (eje, enclavamiento, grapas Mach5)",
    material="Al 5083", process="torneada", qty=1, frame="boat", group="ele",
    load_case="Fuerza de mano 100 N en el pomo (150 mm) contra el enclavamiento", print_rot=(0, 0, 0),
    solid_frac=1.0, orientation="Corte láser, doblado del ala, grapas soldadas",
    allow={"P1-CTL-11": 5.0},
)
CLAMPS = ((-60.0, -48.0), (-146.0, -134.0))


def build_local(p):
    y0, y1 = U.Y_MID
    zb = U.top_local(p) - p.CTL_ply_t            # cara inferior de la tapa
    cx, _ = U.crank_pin(U.CRANK_PHI_UP)
    s = prism_xz(circ(0, 0, 32.0, 48), y0, y1)
    s = s + box(-28, 28, y0, y1, zb - 6, 0) + box(-28, cx + 12, y0, y1, zb - 12, zb)
    s = s + box(cx - 12, cx + 12, y0, y1, -150, zb)
    s = s + box(-60, 60, -50, y0 + 0.01, zb - 6, zb)                    # ala bajo la tapa
    for (za, zz) in CLAMPS:
        s = s + box(cx - 10, cx + 10, y1 - 0.01, U.ROD_Y + 10, za, zz)
        s = s - cyl_z(6.4, za - 1, zz + 1, x=cx, y=U.ROD_Y)
    s = s - cyl_y(6.05, y0 - 1, y1 + 1)                                  # eje Ø12 H8
    for k in (2, 3):
        import math
        a = math.radians(U.PIN_PHI[k])
        s = s - cyl_y(p.CTL_ilock_d / 2 + 0.05, y0 - 1, y1 + 1, x=p.CTL_ilock_r * math.cos(a), z=p.CTL_ilock_r * math.sin(a))
    for xx in (-45.0, 45.0):
        s = s - cyl_z(3.3, zb - 7, zb + 1, x=xx, y=-35.0)
    return s


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    # lógica del enclavamiento en una grilla de estados (acelerador × bucket)
    bad_allowed, bad_blocked = 0, 0
    for tt in [x * 2.5 for x in range(-12, 17)]:
        for tb in [-x * 5.0 for x in range(0, 13)]:
            ok = U.interlock_ok(p, tt, tb)
            want = (abs(tt) < 1e-9) or (abs(tb) < 1e-9 and tt > 0) or (abs(tb + 60) < 1e-9 and tt < 0)
            if ok and not want:
                bad_allowed += 1
            if want and not ok:
                bad_blocked += 1
    zb = U.top_local(p) - p.CTL_ply_t
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("estados prohibidos alcanzables (avance con bucket abajo, reversa con bucket arriba, bucket con acelerador) [n]", bad_allowed, 0, "="),
            ("estados válidos bloqueados por el enclavamiento [n]", bad_blocked, 0, "="),
            ("ala bajo la tapa de la consola (z local) [mm]", zb, -60.0, ">="),
            ("pernos de enclavamiento a r ≥ eje + 9 [mm]", p.CTL_ilock_r - p.CTL_shaft_d / 2, 9.0, ">=")]
