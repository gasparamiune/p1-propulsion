"""P1-PMP-03 — Impulsor axial (AISI 316, CNC 5 ejes; alternativa SLM 316L + torneado, R11 §6).

Marco JET: X = 0 en la cara de entrada (cubo), X a popa. Cubo Ø D_hub, largo L_imp, nariz elíptica
hacia proa (apoya en arandela + DIN 471-20 delantero, empuje), agujero Ø shaft_d H7 sin chavetero.
El par entra por el PASADOR DE CORTE transversal (P1-PMP-05, eje Y, X = pmp_pin_X) que atraviesa
cubo y eje; sus extremos los tapa el anillo retén P1-PMP-04 sobre el asiento Ø 2·pmp_land_r.
Álabes: Z = blades, secciones de arco circular + espesor NACA 00xx sobre cilindros, ángulos de pala
de p.pmp_blade_row(r) (triángulos de sizing + incidencia 3° + desviación de Constant, R12 §2.5),
borde de ataque apilado radial en X = pmp_imp_le_X; punta recortada exactamente a r = D/2.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Rot, Pos, Solid  # noqa: E402
from _pmp_geom import (cyl_x, ring_x, revolve_profile, loft_blade, max_radius)  # noqa: E402
from cadlib import cyl_y, cyl_z, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-03", name="impeller",
            desc="Impulsor axial de 5 álabes, cubo Ø66 con nariz, pasador de corte (sin chavetero)",
            material="AISI 316", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Par máx. del controlador + empuje axial; corte del pasador (piedra)",
            allow={"P1-PMP-05": 5.0, "P1-PMP-04": 8.0})


_CACHE = {}


def blades(p):
    key = (id(p), p.D, p.blades, p.D_hub)
    if key in _CACHE:
        return _CACHE[key]
    rows = []
    for r, rd in p.pmp_imp_loft_r:
        b = p.pmp_blade_row(rd)
        rows.append(dict(r=r, chord=b["chord"], a1=b["bb1"], a2=b["bb2"], tc=b["tc"]))
    bl = loft_blade(rows, -1, p.pmp_imp_le_X)
    bl = bl & cyl_x(p.pmp_tip_r, -50, 200)          # punta exacta en r = D/2
    _CACHE[key] = [Rot(360.0 * k / p.blades, 0, 0) * bl for k in range(p.blades)]
    return _CACHE[key]


def hub(p):
    rb = p.shaft_d / 2
    L, Rh, rl = p.L_imp, p.D_hub / 2, p.pmp_land_r
    nL, r0 = p.pmp_nose_L, p.pmp_nose_r0
    prof = [(-nL, rb), (-nL, r0)]
    for i in range(1, 13):                           # nariz: cuarto de elipse
        a = math.pi / 2 * i / 12
        prof.append((-nL * math.cos(a), r0 + (Rh - r0) * math.sin(a)))
    prof += [(p.pmp_band_X0, Rh), (p.pmp_band_X0, rl), (L, rl), (L, rb)]
    h = revolve_profile(prof)
    ri, ro, dep = p.pmp_pocket
    h = h - ring_x(ro, ri, L - dep, L + 1)          # ranura aligerante desde popa
    return h


def build(p):
    part = hub(p)
    for b in blades(p):
        part = part + b
    # pasador de corte (eje Y) y 2 × M3 (±Z) del anillo retén
    part = part - cyl_y(p.pmp_pin_hole / 2, -p.D_hub, p.D_hub, x=p.pmp_pin_X)
    ro = p.pmp_pocket[1]
    for s in (1, -1):
        z0, z1 = (ro - 0.5, p.pmp_land_r + 0.1) if s > 0 else (-p.pmp_land_r - 0.1, -ro + 0.5)
        part = part - cyl_z(1.25, z0, z1, x=p.pmp_pin_X)   # broca M3 (Ø2,5) hasta la ranura
    if hasattr(part, "solids") and len(part.solids()) == 1:
        part = part.solids()[0]
    return part


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    T = p.pmp_imp_table
    bl = blades(p)[0]
    bb = bl.bounding_box()
    rmax = max(max_radius(bl), p.D_hub / 2)          # el cubo (Ø D_hub) queda dentro de la punta
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("radio de punta = D/2 [mm]", rmax, p.D / 2, "="),
        ("holgura de punta (D_bore/2 − r_punta) [mm] ≥ tip_clr − 0,05", p.D_bore / 2 - rmax, p.tip_clr - 0.05, ">="),
        ("holgura de punta [mm] ≤ tip_clr + 0,05", p.D_bore / 2 - rmax, p.tip_clr + 0.05, "<="),
        ("agujero del eje Ø shaft_d (H7)", 1.0 if has_radius(part, p.shaft_d / 2) else 0.0, 1.0, "="),
        ("agujero del pasador Ø d+0,05", 1.0 if has_radius(part, p.pmp_pin_hole / 2, tol=0.01) else 0.0, 1.0, "="),
        ("cubo Ø D_hub", 1.0 if has_radius(part, p.D_hub / 2) else 0.0, 1.0, "="),
        ("álabes dentro del cubo (BF ≤ asiento del anillo − 1) [mm]", bb.max.X, p.pmp_band_X0 - 1.0, "<="),
        ("BA de los álabes ≥ cara del cubo [mm]", bb.min.X, 0.0, ">="),
        ("espesor máx. de punta ≥ 2,0 mm", T["punta"]["tmax"], 2.0, ">="),
        ("solidez cubo ≥ 1,2 (R12 §2.4)", T["cubo"]["s"], 1.2, ">="),
        ("solidez punta ≥ 0,6 (R12 §2.4)", T["punta"]["s"], 0.6, ">="),
        ("factor de difusión cubo ≤ 0,45 (Lieblein)", T["cubo"]["Df"], 0.45, "<="),
        ("de Haller w2/w1 cubo ≥ 0,70", T["cubo"]["dh"], 0.70, ">="),
        ("pared mín. cubo entre agujero y ranura [mm]", p.pmp_pocket[0] - p.shaft_d / 2, 3.2, ">="),
        ("concentricidad declarada (TIR agujero ↔ punta) [mm]", 0.03, 0.03, "<="),
    ]
