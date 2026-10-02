"""P1-PMP-08 — Tobera fija (Al 6061-T6 torneada, anodizado duro). Marco JET.

Brida delantera en X_st1 (Ø pmp_f2_od, MÁS CHICA que el agujero del espejo) con 8 × Ø5,5 en Ø pmp_f2_bc
para ISO 4762 M5 A4-70 roscados en la carcasa, y espiga Ø pmp_D_seat × (pmp_noz_spigot) con O-ring RADIAL
(cs oring_cs) que sella contra el asiento de la carcasa y aprieta la camisa del estator (la espiga es
pmp_stack_gap más larga que el asiento: queda esa luz entre las caras de las bridas, lado seco).
Contracción cónica Ø D_bore → Ø D_noz entre X_st1 y X_noz1 − pmp_noz_cyl y tramo cilíndrico hasta la
SALIDA en X_noz1 (plano del espejo, R12 §3.3). Aguas abajo de la salida: alojamiento esférico
R = pmp_sock_R centrado en el pivote de la boquilla y zona libre r ≤ pmp_steer_free_r desde pmp_sock_X1
para las orejas de la boquilla. Resalte Ø 2·pmp_land_R con ranura de O-ring radial (sella contra el cuello
de la placa de espejo P1-PMP-09). Las orejas de pivote están en la placa de espejo.
SERVICIO (camino de extracción, params_bomba.service_paths, checks abajo): con boquilla, bucket y placa de
espejo afuera y los 8 × M5 sacados desde adentro, la tobera sale POR POPA por el agujero del espejo; detrás
salen el estator (con buje y cono) y, si hace falta, el impulsor. Los semipasadores P1-PMP-05 se cambian con
el impulsor en el eje. El tren no se toca.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Pos, Sphere  # noqa: E402
from _pmp_geom import ring_x, revolve_profile, cyl_x, bore_radius_at  # noqa: E402
from cadlib import box, cyl_z, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

# allow: contactos nominales de ajuste (prensado/deslizante); la intersección BRep exacta es 0 —
# lo que mide verify_parts es el facetado de la malla --fast sobre cilindros coincidentes.
META = dict(id="P1-PMP-08", name="fixed_nozzle",
            desc="Tobera fija Al: contracción a D_noz, rótula de la boquilla y resalte del sello de espejo",
            material="Al 6061-T6", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Presión interna 0,2 MPa; reacción de la placa de espejo por el O-ring",
            allow={"P1-PMP-01": 22.0, "P1-PMP-06": 5.0, "P1-PMP-09": 5.0})


def rn(p, X):
    """Radio interior de la tobera en X."""
    Rb, Rn = p.D_bore / 2, p.D_noz / 2
    if X <= p.X_st1:
        return Rb
    if X >= p.pmp_noz_cone_X1:
        return Rn
    return Rb - (Rb - Rn) * (X - p.X_st1) / (p.pmp_noz_cone_X1 - p.X_st1)


def build(p):
    w = p.pmp_noz_wall
    X0, Xf = p.X_st1 - p.pmp_noz_spigot, p.X_st1 + p.pmp_noz_f_t
    Rn = p.D_noz / 2
    prof = [(X0, p.D_bore / 2), (X0, p.pmp_D_seat / 2), (p.X_st1, p.pmp_D_seat / 2),
            (p.X_st1, p.pmp_f2_od / 2), (Xf, p.pmp_f2_od / 2), (Xf, rn(p, Xf) + w),
            (p.pmp_noz_cone_X1, Rn + w), (p.pmp_land_X0, Rn + w), (p.pmp_land_X0, p.pmp_land_R),
            (p.pmp_land_X1, p.pmp_land_R), (p.pmp_land_X1, Rn), (p.pmp_noz_cone_X1, Rn),
            (p.X_st1, p.D_bore / 2)]
    n = revolve_profile(prof)
    # alojamiento esférico de la rótula + zona libre de las orejas de la boquilla
    n = n - Pos(p.X_steer_pivot, 0, 0) * Sphere(p.pmp_sock_R)
    n = n - cyl_x(p.pmp_steer_free_r, p.pmp_sock_X1, p.pmp_land_X1 + 1)
    # ranura del O-ring radial del espejo
    n = n - ring_x(p.pmp_land_R + 1, p.pmp_land_R - p.pmp_or_depth,
                   p.pmp_or_X - p.pmp_or_width / 2, p.pmp_or_X + p.pmp_or_width / 2)
    # ranura del O-ring radial de la espiga (sello carcasa ↔ tobera)
    Rs = p.pmp_D_seat / 2
    n = n - ring_x(Rs + 1, Rs - p.pmp_gl_depth, p.pmp_f2or_X - p.pmp_gl_width / 2, p.pmp_f2or_X + p.pmp_gl_width / 2)
    # brida: 8 × Ø5,5 (M5 roscados en la carcasa)
    dh = p.pmp_f2_bolt_hole / 2
    for k in range(p.pmp_f2_n):
        a = math.radians(p.pmp_flange_ang0 + 360.0 * k / p.pmp_f2_n)
        n = n - cyl_x(dh, p.X_st1 - 1, Xf + 1, y=p.pmp_f2_bc / 2 * math.cos(a), z=p.pmp_f2_bc / 2 * math.sin(a))
    if len(n.solids()) == 1:
        n = n.solids()[0]
    return n


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    from params import loc_jet as LJ
    r_exit = bore_radius_at(part, p.X_noz1 - 3.0, p.D_noz / 2 + 3)
    r_open = bore_radius_at(part, p.X_noz1 + 1.0, p.D_noz / 2 + 6)
    A = math.pi * r_exit ** 2
    zmin = part.moved(LJ(p)).bounding_box().min.Z
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("Ø de salida = D_noz [mm]", 2 * r_exit, p.D_noz, "="),
        ("área de salida = π/4·D_noz² [mm²]", A, math.pi / 4 * p.D_noz ** 2, "="),
        ("la salida termina en X_noz1 (r libre en X_noz1+1 > D_noz/2) [mm]", r_open - p.D_noz / 2, 0.1, ">="),
        ("semiángulo del cono [°] (R12 §3.3: 8–12, ≤ 14 aceptado)", p.pmp_noz_half_angle, 14.0, "<="),
        ("rótula: R alojamiento − R bola máx. [mm]", p.pmp_sock_R - p.pmp_steer_ball_R_max, 1.0, ">="),
        ("pared del resalte sobre la zona libre, en la ranura del O-ring [mm]", p.pmp_land_R - p.pmp_or_depth - p.pmp_steer_free_r, 3.2, ">="),
        ("pared del resalte sobre el alojamiento esférico [mm]", p.pmp_land_R - p.pmp_or_depth - p.pmp_sock_R, 3.2, ">="),
        ("resalte pasa por el agujero del espejo (radial) [mm]", p.transom_hole_d / 2 - p.pmp_land_R, 3.0, ">="),
        ("brida = brida trasera de la carcasa (bc) [mm]", p.pmp_f2_bc, p.pmp_f2_bc, "="),
        ("brida pasa por el agujero del espejo (radial, servicio por popa) [mm]", p.transom_hole_d / 2 - p.pmp_f2_od / 2, 1.5, ">="),
        ("pared mín. del cono [mm]", p.pmp_noz_wall, 3.2, ">="),
        (f"punto más bajo sobre el fondo interior (z BOTE) [mm] — si falla: subir waterjet.axis_height_m a ≥ {p.pmp_axis_h_min_m:.3f} m",
         zmin, p.bottom_t + 2.0, ">="),
        ("espiga: pared bajo la ranura del O-ring radial [mm]", (p.pmp_D_seat - p.D_bore) / 2 - p.pmp_gl_depth, 2.0, ">="),
        ("espiga: apoyos a ambos lados de la ranura del O-ring [mm]", (p.pmp_noz_spigot - p.pmp_gl_width) / 2, 3.0, ">="),
        ("brida: cabeza M5 libra el cono exterior (radial) [mm]", p.pmp_f2_bc / 2 - p.pmp_f2_head_d / 2 - (rn(p, p.X_st1 + p.pmp_noz_f_t) + p.pmp_noz_wall), 1.0, ">="),
        ("brida: borde sobre la cabeza M5 (radial) [mm]", p.pmp_f2_od / 2 - p.pmp_f2_bc / 2 - p.pmp_f2_head_d / 2, 0.3, ">="),
    ] + [(f"camino de extracción: {r['item']}", r["need"], r["avail"], r["op"]) for r in p.pmp_service]
