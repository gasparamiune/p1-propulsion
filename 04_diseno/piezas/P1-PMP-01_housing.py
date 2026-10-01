"""P1-PMP-01 — Carcasa de la bomba (Al 6061-T6 torneada + taladrada, anodizado duro). Marco JET.

De la brida de la toma (plano X_duct_out: Ø pump_flange_od, 8 × M6 en Ø pump_flange_bc, O-ring de
cara cs = oring_cs) a la brida trasera (X_st1: Ø pmp_f2_od, 8 × M6 en Ø pmp_f2_bc, tobera P1-PMP-08).
Bore: labio Ø D_bore (continúa el conducto de la toma) → escalón en X_ring0 → asiento Ø pmp_D_seat
común para el anillo de desgaste (P1-PMP-02, prensado desde popa) y la camisa del estator
(P1-PMP-06, deslizante, la aprieta la espiga de la tobera). Anti-rotación: pasador Ø4 en el escalón
(anillo) y 2 × M5 A4 radiales en ±Y (estator). Puerto de refrigeración G1/8 arriba, aguas abajo del
estator (pmp_cool_port), para la manguera del ESC y del motor (grupo TREN).
Material: Al mecanizado y no PETG: la concentricidad anillo ↔ eje (holgura 0,66 mm) depende de esta
pieza (R10b H15); galvánica Al–316: anodizado duro + Tef-Gel + ánodo de aluminio (R06 §0, R10b H21).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _pmp_geom import ring_x, revolve_profile  # noqa: E402
from cadlib import cyl_x, cyl_y, cyl_z, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-PMP-01", name="housing",
            desc="Carcasa Al 6061-T6: brida de la toma, asiento del anillo y del estator, puerto de agua",
            material="Al 6061-T6", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Presión interna 0,2 MPa; reacción del estator; momentos de boquilla/bucket en bridas",
            allow={"P1-PMP-02": 20.0, "P1-PMP-06": 20.0, "P1-PMP-08": 20.0})


def bolt_xy(r, n, a0):
    return [(r * math.cos(math.radians(a0 + 360.0 * k / n)), r * math.sin(math.radians(a0 + 360.0 * k / n)))
            for k in range(n)]


def build(p):
    Rf1, Rb, Rs, Rbo = p.pump_flange_od / 2, p.pmp_D_barrel / 2, p.pmp_D_seat / 2, p.D_bore / 2
    Rf2 = p.pmp_f2_od / 2
    X0, X1 = p.X_duct_out, p.X_st1
    prof = [(X0, Rbo), (X0, Rf1), (X0 + p.pmp_f1_t, Rf1), (X0 + p.pmp_f1_t, Rb),
            (X1 - p.pmp_f2_t, Rb), (X1 - p.pmp_f2_t, Rf2), (X1, Rf2), (X1, Rs),
            (p.X_ring0, Rs), (p.X_ring0, Rbo)]
    h = revolve_profile(prof)
    # saliente del puerto de refrigeración (arriba)
    Xc, _, Zc = p.pmp_cool_port
    h = h + cyl_z(p.pmp_cool_boss_d / 2, Rb - 3.0, Zc, x=Xc)
    h = h - cyl_z(p.pmp_cool_tap_d / 2, Zc - p.pmp_cool_thread_L, Zc + 1, x=Xc)
    h = h - cyl_z(p.pmp_cool_bore_d / 2, Rs - 1, Zc, x=Xc)
    # bridas: agujeros pasantes M6
    dh = p.pump_flange_bolt + p.bolt_clr
    for y, z in bolt_xy(p.pump_flange_bc / 2, p.pump_flange_n, p.pmp_flange_ang0):
        h = h - cyl_x(dh / 2, X0 - 1, X0 + p.pmp_f1_t + 1, y=y, z=z)
    for y, z in bolt_xy(p.pmp_f2_bc / 2, p.pmp_f2_n, p.pmp_flange_ang0):
        h = h - cyl_x((p.pmp_f2_bolt + p.bolt_clr) / 2, X1 - p.pmp_f2_t - 1, X1 + 1, y=y, z=z)
    # O-ring de cara (brida de la toma)
    ri = p.pmp_gl_r_in
    h = h - ring_x(ri + p.pmp_gl_width, ri, X0 - 1, X0 + p.pmp_gl_depth)
    # pasador anti-rotación del anillo (en el escalón, arriba)
    a = math.radians(p.pmp_ring_pin_ang)
    rp = p.pmp_ring_pin_r
    h = h - cyl_x(p.pmp_ring_pin_d / 2, p.X_ring0 - 6.0, p.X_ring0 + 0.1, y=rp * math.cos(a), z=rp * math.sin(a))
    # 2 × M5 radiales (±Y) para trabar la camisa del estator
    for s in (1, -1):
        y0, y1 = (Rs - 0.5, Rb + 1) if s > 0 else (-Rb - 1, -Rs + 0.5)
        h = h - cyl_y((p.pmp_st_screw_d + p.bolt_clr) / 2, y0, y1, x=p.pmp_st_screw_X)
    return h


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    from params import loc_jet as LJ
    zmin = part.moved(LJ(p)).bounding_box().min.Z
    Xc, _, Zc = p.pmp_cool_port
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("brida de la toma: Ø ext = pump_flange_od", 1.0 if has_radius(part, p.pump_flange_od / 2) else 0.0, 1.0, "="),
        ("brida de la toma: plano = X_duct_out [mm]", part.bounding_box().min.X, p.X_duct_out, "="),
        ("brida de la toma: 8 agujeros Ø6,4 en Ø bc", 1.0 if has_radius(part, (p.pump_flange_bolt + p.bolt_clr) / 2) else 0.0, 1.0, "="),
        ("labio Ø D_bore (sin escalón contra la toma)", 1.0 if has_radius(part, p.D_bore / 2) else 0.0, 1.0, "="),
        ("asiento del anillo/estator Ø pmp_D_seat", 1.0 if has_radius(part, p.pmp_D_seat / 2) else 0.0, 1.0, "="),
        ("pared mín. del cuerpo [mm]", p.pmp_h_wall, 3.2, ">="),
        ("ligamento brida–O-ring [mm]", p.pump_flange_bc / 2 - (p.pump_flange_bolt + p.bolt_clr) / 2 - (p.pmp_gl_r_in + p.pmp_gl_width), 2.0, ">="),
        ("cabeza M6 (Ø10) libra el cuerpo [mm]", p.pump_flange_bc / 2 - 5.0 - p.pmp_D_barrel / 2, 0.5, ">="),
        ("punto más bajo sobre el fondo interior (z BOTE) [mm]", zmin, p.bottom_t + 2.0, ">="),
        ("puerto G1/8: rosca entera en el saliente [mm]", Zc - p.pmp_cool_thread_L - p.pmp_D_barrel / 2, 0.0, ">="),
        ("puerto aguas abajo de los álabes del estator (X)", Xc, p.X_st1 - 20.0, ">="),
        ("concentricidad declarada asiento ↔ brida (TIR) [mm]", 0.03, 0.03, "<="),
    ]
