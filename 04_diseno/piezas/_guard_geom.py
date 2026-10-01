"""Geometría compartida del protector (orejas) para STR-01 y PRP-02 (no es una pieza)."""
import importlib.util
import os


def guard_module():
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("gs", os.path.join(here, "P1-PRP-01_guard_segment.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def lug_geom(p):
    """Devuelve: u del agujero, r del agujero, r tope de orejas, semiancho tangencial del par,
    semilargo axial, r exterior del perfil en la zona de orejas."""
    g = guard_module()
    xl, rl = g.lug_center(p)
    lt, la, lr = p.guard_lug
    r_top = rl + lr / 2 + 2.0
    r_prof = p.guard_ri + max(g.thickness(p, xl + p.guard_L / 2 + d) for d in (-la / 2, 0, la / 2))
    return p.s_prop + xl, rl, r_top, lt, la / 2, r_prof
