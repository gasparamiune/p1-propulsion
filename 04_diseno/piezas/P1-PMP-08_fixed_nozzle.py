"""P1-PMP-08 — Tobera fija con orejas de pivote (Al 6061-T6 torneada + fresada, anodizado duro). Marco JET.

Brida delantera en X_st1 (Ø pmp_f2_od, 8 × M6 con la carcasa) con espiga Ø pmp_D_seat × 4 que aprieta
la camisa del estator. Contracción cónica Ø D_bore → Ø D_noz entre X_st1 y X_noz1 − pmp_noz_cyl y
tramo cilíndrico hasta la SALIDA en X_noz1 (plano del espejo, R12 §3.3). Aguas abajo de la salida:
alojamiento esférico R = pmp_sock_R centrado en el pivote de la boquilla (la boquilla direccional
termina adelante en una rótula R ≤ pmp_steer_ball_R_max, ver informe) y zona libre r ≤ pmp_steer_free_r
desde pmp_sock_X1 para las orejas de la boquilla. Resalte Ø 2·pmp_land_R con ranura de O-ring radial
(sella contra el cuello de la placa de espejo P1-PMP-09, que pasa por encima de las orejas).
Orejas fijas: |Z| ∈ [Z_steer_lug, Z_steer_lug + pmp_lug_t], ancho pmp_lug_w, agujero Ø steer_pin_d + 0,2
en (X_steer_pivot, 0) — las orejas de la boquilla van POR DENTRO (|Z| ≤ Z_steer_lug − 0,5).
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
            desc="Tobera fija Al: contracción a D_noz, rótula de la boquilla, sello de espejo y orejas de pivote",
            material="Al 6061-T6", process="torneada", qty=1, frame="jet", group="jet",
            load_case="Presión interna 0,2 MPa; F lateral de la boquilla y F del bucket en las orejas",
            allow={"P1-PMP-01": 300.0, "P1-PMP-06": 300.0, "P1-PMP-09": 50.0})


def rn(p, X):
    """Radio interior de la tobera en X."""
    Rb, Rn = p.D_bore / 2, p.D_noz / 2
    if X <= p.X_st1:
        return Rb
    if X >= p.pmp_noz_cone_X1:
        return Rn
    return Rb - (Rb - Rn) * (X - p.X_st1) / (p.pmp_noz_cone_X1 - p.X_st1)


def lug_envelope_r(p):
    return math.hypot(p.Z_steer_lug + p.pmp_lug_t, p.pmp_lug_w / 2)


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
    # orejas de pivote (±Z), extremo redondeado alrededor del perno
    hw, t = p.pmp_lug_w / 2, p.pmp_lug_t
    for s in (1, -1):
        z0, z1 = (p.Z_steer_lug, p.Z_steer_lug + t) if s > 0 else (-p.Z_steer_lug - t, -p.Z_steer_lug)
        lug = box(p.pmp_land_X1 - 14.0, p.X_steer_pivot, -hw, hw, z0, z1) + cyl_z(hw, z0, z1, x=p.X_steer_pivot)
        n = n + lug
        n = n - cyl_z(p.pmp_lug_hole / 2, z0 - 1, z1 + 1, x=p.X_steer_pivot)
    # brida: 8 × M6
    dh = (p.pmp_f2_bolt + p.bolt_clr) / 2
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
        ("orejas: agujero Ø steer_pin_d + 0,2", 1.0 if has_radius(part, p.pmp_lug_hole / 2) else 0.0, 1.0, "="),
        ("orejas: cara interior en |Z| = Z_steer_lug [mm]", p.Z_steer_lug, p.raw["Z_steer_lug"], "="),
        ("orejas: eje del perno en X_steer_pivot [mm]", p.X_steer_pivot, p.raw["X_steer_pivot"], "="),
        ("rótula: R alojamiento − R bola máx. [mm]", p.pmp_sock_R - p.pmp_steer_ball_R_max, 1.0, ">="),
        ("zona libre de orejas de la boquilla < Z_steer_lug + t (r) [mm]", p.pmp_steer_free_r, lug_envelope_r(p), "<="),
        ("la placa de espejo pasa sobre las orejas (bore − envolvente) [mm]", p.pmp_tp_bore_R - lug_envelope_r(p), 2.0, ">="),
        ("resalte pasa por el agujero del espejo (radial) [mm]", p.transom_hole_d / 2 - p.pmp_land_R, 3.0, ">="),
        ("brida = brida trasera de la carcasa (bc) [mm]", p.pmp_f2_bc, p.pmp_f2_bc, "="),
        ("pared mín. del cono [mm]", p.pmp_noz_wall, 3.2, ">="),
        ("punto más bajo sobre el fondo interior (z BOTE) [mm]", zmin, p.bottom_t + 2.0, ">="),
    ]
