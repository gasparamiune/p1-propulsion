"""P1-CTL-07 — Terminal del cable Ultraflex Mach5 en la consola (COMPRADO, mismo cable que P1-REV-07).

Vaina rígida vertical sujeta por las grapas de P1-CTL-08; cabeza abajo; el cable baja por dentro de la
consola y va por la banda de estribor hasta el prensaestopas del espejo (P1-CTL-05). Dimensiones
[ESTIMADO: tipo 33C; buscar "Ultraflex Mach5 end fitting dimensions"]."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_z  # noqa: E402
import _ctl as U  # noqa: E402
import _mach5 as M5  # noqa: E402

META = dict(
    id="P1-CTL-07", name="terminal_mach5_consola", desc="Terminal Mach5 en la consola — comprado",
    material="Acero", process="comprada", qty=1, frame="boat", group="ele",
    load_case="—", print_rot=(0, 0, 0), solid_frac=1.0, orientation="—", mass_g=120.0,   # [ESTIMADO]
)


def build_local(p):
    cx, _ = U.crank_pin(U.CRANK_PHI_UP)
    z1 = U.SLEEVE_TOP_Z
    s = cyl_z(M5.SLEEVE_D / 2, z1 - M5.SLEEVE_L, z1, x=cx, y=U.ROD_Y)
    s = s + cyl_z(M5.HUB_D / 2, z1 - M5.SLEEVE_L - M5.HUB_L, z1 - M5.SLEEVE_L + 0.01, x=cx, y=U.ROD_Y)
    return s - cyl_z(3.3, z1 - M5.SLEEVE_L - M5.HUB_L + 5, z1 + 1, x=cx, y=U.ROD_Y)


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    return [("un solo sólido", len(part.solids()), 1, "=")]
