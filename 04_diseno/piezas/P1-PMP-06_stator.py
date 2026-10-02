"""P1-PMP-06 — Estator / difusor (Al 6061-T6, CNC 5 ejes, anodizado duro). Marco JET.

Camisa Ø pmp_D_seat × Ø D_bore (desliza en la carcasa, apoya adelante contra el anillo de desgaste y
atrás la aprieta la espiga de la tobera; 2 × M5 radiales ±Y, roscados en la carcasa, entran con la punta en 2
agujeros LISOS Ø5,5 × 3,5 de la camisa y la traban al giro), vanes álabes
(coprimo con blades) con ángulo de entrada = stator_inlet_deg de sizing en cada radio (torbellino
libre) y salida axial con sobregiro δ ≤ 8° (regla de Constant, R12 §3.2), cubo Ø D_hub con el buje de
agua P1-PMP-07 (2.º apoyo del eje, entra desde proa) y cono de cola dentro de la tobera, con agujero
de salida del agua de lubricación. Agujero Ø pmp_cool_bore_d arriba, alineado con el puerto G1/8.
Metal y no PETG: con PETG la FS a fatiga de los álabes no llega a 3 sin álabes de ~18 mm (bloqueo
de más del 60 % en el cubo) y el alojamiento del buje no mantendría la concentricidad del eje (structural_bomba).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Rot  # noqa: E402
from _pmp_geom import ring_x, revolve_profile, loft_blade, cyl_x  # noqa: E402
from cadlib import cyl_y, cyl_z, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

# allow: contactos nominales de ajuste (prensado/deslizante); la intersección BRep exacta es 0 —
# lo que mide verify_parts es el facetado de la malla --fast sobre cilindros coincidentes.
META = dict(id="P1-PMP-06", name="stator",
            desc="Estator Al 6061-T6 de 7 álabes con camisa, cubo con buje de agua y cono de cola",
            material="Al 6061-T6", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Reacción del par del rotor en los álabes; carga radial del buje; presión",
            allow={"P1-PMP-01": 368.0, "P1-PMP-02": 5.0, "P1-PMP-07": 5.0, "P1-PMP-08": 5.0})

_CACHE = {}


def vanes(p):
    key = (id(p), p.vanes, p.D_hub)
    if key in _CACHE:
        return _CACHE[key]
    rows = []
    for r, rd in p.pmp_st_loft_r:
        v = p.pmp_vane_row(rd)
        rows.append(dict(r=r, chord=v["chord"], a1=v["alpha_in"], a2=v["alpha_out"], tc=v["tc"]))
    vb = loft_blade(rows, +1, p.pmp_st_le_X)
    _CACHE[key] = [Rot(360.0 * k / p.vanes, 0, 0) * vb for k in range(p.vanes)]
    return _CACHE[key]


def tail_r(p, X):
    """Radio del cono de cola (recto, punta redondeada por el agujero) en X ≥ X_st1."""
    t = (X - p.X_st1) / p.pmp_tail_L
    return p.D_hub / 2 - (p.D_hub / 2 - p.pmp_tail_tip_r) * min(max(t, 0.0), 1.0)


def build(p):
    Rh = p.D_hub / 2
    Xt = p.X_st1 + p.pmp_tail_L
    # cubo + cono, con cavidades interiores (perfil de revolución)
    rb = p.pmp_brg_od / 2
    rc = p.pmp_st_cavity_d / 2
    rw = p.pmp_tail_hole_d / 2
    Xcav = p.pmp_shaft_X_aft + 4.0
    prof = [(p.X_st0, rb), (p.X_st0, Rh), (p.X_st1, Rh), (Xt, p.pmp_tail_tip_r), (Xt, rw),
            (Xcav, rw), (Xcav, rc), (p.pmp_bush_X1, rc), (p.pmp_bush_X1, rb)]
    hub = revolve_profile(prof)
    shell = ring_x(p.pmp_D_seat / 2, p.D_bore / 2, p.pmp_st_shell_X0, p.pmp_st_shell_X1)
    part = hub + shell
    for v in vanes(p):
        part = part + v
    # agujero de refrigeración (arriba) y 2 agujeros lisos ciegos (±Y) para la punta de los M5 anti-giro
    Xc = p.pmp_cool_port[0]
    part = part - cyl_z(p.pmp_cool_bore_d / 2, p.D_bore / 2 - 1, p.pmp_D_seat / 2 + 1, x=Xc)
    Rs = p.pmp_D_seat / 2
    for s in (1, -1):
        dt, ht = p.pmp_st_tip_hole
        y0, y1 = (Rs - ht, Rs + 1) if s > 0 else (-Rs - 1, -Rs + ht)
        part = part - cyl_y(dt / 2, y0, y1, x=p.pmp_st_screw_X)
    if len(part.solids()) == 1:
        part = part.solids()[0]
    return part


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def area_monotonic(p, n=60):
    """Área de paso (tobera − cono de cola) desde X_st1 hasta X_noz1: decreciente."""
    Rb, Rn = p.D_bore / 2, p.D_noz / 2
    A = []
    for i in range(n + 1):
        X = p.X_st1 + (p.X_noz1 - p.X_st1) * i / n
        if X <= p.pmp_noz_cone_X1:
            rn = Rb - (Rb - Rn) * (X - p.X_st1) / (p.pmp_noz_cone_X1 - p.X_st1)
        else:
            rn = Rn
        rc = tail_r(p, X) if X <= p.X_st1 + p.pmp_tail_L else 0.0
        A.append(math.pi * (rn ** 2 - rc ** 2))
    worst = max(A[i + 1] - A[i] for i in range(n))
    return worst, A


def checks(p, part):
    T = p.pmp_st_table
    worst, A = area_monotonic(p)
    bb = vanes(p)[0].bounding_box()
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("álabes del estator coprimos con el rotor (mcd)", math.gcd(p.vanes, p.blades), 1, "="),
        ("camisa Ø ext = asiento de la carcasa", 1.0 if has_radius(part, p.pmp_D_seat / 2) else 0.0, 1.0, "="),
        ("camisa Ø int = D_bore", 1.0 if has_radius(part, p.D_bore / 2) else 0.0, 1.0, "="),
        ("alojamiento del buje Ø = pmp_brg_od", 1.0 if has_radius(part, p.pmp_brg_od / 2) else 0.0, 1.0, "="),
        # con torbellino libre, el ángulo de sizing; si el cubo no cumple de Haller (torbellino limitado, params_bomba), el
        # α3 del triángulo limitado que usan el impulsor y el estator del CAD (regeneración con otras entradas)
        (("entrada cubo = stator_inlet_deg sizing [°]" if p.pmp_free_vortex else
          "entrada cubo = α3 del torbellino limitado en el cubo (de Haller) [°]"), T["cubo"]["alpha_in"],
         (p.pump_sections["cubo"]["stator_inlet_deg"] if p.pmp_free_vortex
          else p.pmp_tri(p.pump_sections["cubo"]["r_mm"])["alpha3"] + p.pmp_st_inc), "="),
        ("entrada medio = stator_inlet_deg sizing [°]", T["medio"]["alpha_in"], p.pump_sections["medio"]["stator_inlet_deg"], "="),
        ("BA del estator ≥ X_st0 (luz rotor–estator) [mm]", bb.min.X, p.X_st0, ">="),
        ("BF de los álabes ≤ fin de la camisa [mm]", bb.max.X, p.pmp_st_shell_X1, "<="),
        ("área de paso tobera+cono decreciente (máx. ΔA) [mm²]", worst, 0.0, "<="),
        ("espesor mín. de álabe [mm]", min(v["tmax"] for v in T.values()), 3.2, ">="),
        ("pared del cubo sobre el buje [mm]", p.D_hub / 2 - p.pmp_brg_od / 2, 10.0, ">="),
        ("concentricidad declarada buje ↔ camisa (TIR) [mm]", 0.03, 0.03, "<="),
        ("agujero de la punta del M5 deja pared en la camisa [mm]", (p.pmp_D_seat - p.D_bore) / 2 - p.pmp_st_tip_hole[1], 1.0, ">="),
        ("BF de los álabes a ≥ 5 mm del fin de la camisa (espiga de la tobera) [mm]", p.pmp_st_shell_X1 - bb.max.X, 5.0, ">="),
    ]
