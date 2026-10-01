"""P1-REV-07 — Terminal del cable Ultraflex Mach5 en la boquilla (COMPRADO; R11 §7: Mach5 10 ft 553 kr).

Vaina rígida + cabeza con ranura de grapa, sujetas en P1-REV-05. Dimensiones [ESTIMADO: tipo 33C —
vaina Ø1/2" × 120, cabeza Ø22 × 20; buscar "Ultraflex Mach5 end fitting dimensions"]. Modelada hueca
(Ø6,6) para la varilla P1-REV-08."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_z  # noqa: E402
import _mach5 as M5  # noqa: E402

META = dict(
    id="P1-REV-07", name="terminal_mach5", desc="Terminal Mach5 (vaina + cabeza) en la boquilla — comprado",
    material="Acero", process="comprada", qty=1, frame="steer", group="jet",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=120.0,   # [ESTIMADO]
)


def build(p):
    sx, _ = M5.stud_xz(p)
    ry = M5.rod_y(p)
    z0 = p.REV_sleeve_z0
    s = cyl_z(M5.SLEEVE_D / 2, z0, z0 + M5.SLEEVE_L, x=sx, y=ry)
    s = s + cyl_z(M5.HUB_D / 2, z0 + M5.SLEEVE_L, z0 + M5.SLEEVE_L + M5.HUB_L, x=sx, y=ry)
    return s - cyl_z(3.3, z0 - 1, z0 + M5.SLEEVE_L + M5.HUB_L - 5, x=sx, y=ry)


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def checks(p, part):
    import params as P
    sx, _ = M5.stud_xz(p)
    top = P.jet_to_boat(p, sx, M5.rod_y(p), p.REV_sleeve_z0 + M5.SLEEVE_L + M5.HUB_L)
    wl = p.sz["hydrostatics"]["draft_m"] * 1000
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("salida del cable sobre la flotación estática [mm]", top[2] - wl, 30.0, ">="),
            ("carrera usada / carrera del Mach5 [fracción]", abs(M5.dz(p)) / p.REV_mach5_stroke, 0.8, "<=")]
