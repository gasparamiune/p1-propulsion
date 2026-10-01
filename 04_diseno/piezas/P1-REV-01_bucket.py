"""P1-REV-01 — Bucket (cuchara) de reversa, Al 5083 4 mm doblado y soldado TIG.

Pivota sobre las orejas de la boquilla (X_bucket_pivot, ±Y, Z_bucket_pivot) y sigue la dirección.
Se diseña en la posición ABAJO (bucket_down_deg) y se lleva a ARRIBA (marco natural) girando −70°:
  - cuchara: chapa curvada (arco elíptico semiejes REV_cup_ax × REV_cup_az, centro a REV_cup_dx de la
    salida) entre los brazos; tapa el chorro (proyección ≥ 90 %, ver checks) y lo devuelve hacia
    proa y abajo por el labio inferior; nervio central de 4 mm en el lomo (zona de impacto, t 70°…−60°);
  - brazos laterales (±Y 49,5–53,5) con aro de refuerzo en el pivote (buje POM P1-REV-03, perno
    con hombro P1-REV-02);
  - brazo +Y: perno de la varilla del Mach5 (P1-REV-06) en una cuerda VERTICAL a popa del pivote
    (+35° arriba / −35° abajo, r = REV_stud_r) y dos agujeros de traba para el émbolo P1-REV-04
    (arriba y abajo): la carga del chorro en reversa NO pasa por el cable.
En ARRIBA no toca el cono del chorro (5°)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import cyl_y, prism_xz  # noqa: E402
from _dir_common import hull, circ, rot_xz, bucket_rel_loc, jet_cone, inter_vol  # noqa: E402

META = dict(
    id="P1-REV-01", name="bucket", desc="Bucket de reversa Al 5083 4 mm (cuchara + brazos + nervio)",
    material="Al 5083", process="torneada", qty=1, frame="bucket", group="jet",
    load_case="Chorro desviado en reversa (R12: 1,4 kN) × impacto 2; presión dinámica en la chapa",
    print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Chapa cortada a láser, cuchara curvada en rodillo, brazos y nervio soldados (TIG 5183)",
    allow={"P1-REV-03": 40.0, "P1-REV-06": 20.0},
)


def P_(p):
    return (p.X_bucket_pivot, p.Z_bucket_pivot)


def lock_pt(p):
    a = math.radians(p.REV_lock_ang)
    return (p.X_bucket_pivot + p.REV_lock_r * math.cos(a), p.Z_bucket_pivot + p.REV_lock_r * math.sin(a))


def stud_pt(p, down=False):
    a = math.radians(p.REV_stud_up_ang - (p.bucket_down_deg if down else 0.0))
    return (p.X_bucket_pivot + p.REV_stud_r * math.cos(a), p.Z_bucket_pivot + p.REV_stud_r * math.sin(a))


def cup_pts(p, off=0.0, t0=None, t1=None, n=40):
    xc = p.STE_X_exit + p.REV_cup_dx
    ax, az = p.REV_cup_ax + off, p.REV_cup_az + off
    t0 = p.REV_cup_t0 if t0 is None else t0
    t1 = p.REV_cup_t1 if t1 is None else t1
    return [(xc + ax * math.cos(math.radians(t0 + (t1 - t0) * i / n)),
             az * math.sin(math.radians(t0 + (t1 - t0) * i / n))) for i in range(n + 1)]


def build_down(p):
    """Geometría en la posición ABAJO (marco de la boquilla)."""
    t, yi = p.REV_t, p.REV_y_in
    P = P_(p)
    inner, outer = cup_pts(p, 0.0), cup_pts(p, t)
    cup = prism_xz(inner + list(reversed(outer)), -yi - 0.01, yi + 0.01)
    rib = prism_xz(cup_pts(p, t - 0.5, 70, -60) + list(reversed(cup_pts(p, t + 10, 70, -60))), -2.0, 2.0)   # nervio en la zona de impacto (no baja a la quilla)
    s = cup + rib
    lk = lock_pt(p)                                   # traba ABAJO: el agujero está en el émbolo
    lk_up = rot_xz(lk, P, p.bucket_down_deg)          # traba ARRIBA (el mismo punto del brazo, bajado)
    sd = stud_pt(p, down=True)
    for sg in (1, -1):
        y0, y1 = (yi, yi + t) if sg > 0 else (-yi - t, -yi)
        a_main = hull(circ(*P, p.REV_boss_r) + outer)
        plate = prism_xz(a_main, y0, y1)
        if sg > 0:                                    # lóbulos: perno de la varilla y 2 trabas
            for q in (sd, lk, lk_up):
                plate = plate + prism_xz(hull(circ(*P, p.REV_boss_r) + circ(*q, 12.0)), y0, y1)
        ring_y = (y1, y1 + t) if sg > 0 else (y0 - t, y0)
        plate = plate + prism_xz(circ(*P, p.REV_boss_r, 32), *ring_y)
        if sg > 0:                                    # buje soldado del perno de la varilla (M6 roscado)
            plate = plate + prism_xz(circ(*sd, 8.0, 32), y1 - 0.01, y1 + p.REV_eye_off)
        s = s + plate
    # agujeros: pivote (buje Ø14), traba (Ø10,5), perno de la varilla (M6 Ø6,4)
    s = s - cyl_y(p.REV_bush_od / 2, -yi - 2 * t - 1, yi + 2 * t + 1, x=P[0], z=P[1])
    for q in (lk, lk_up):
        s = s - cyl_y(p.REV_lock_hole_d / 2, yi - 1, yi + t + 1, x=q[0], z=q[1])
    s = s - cyl_y(2.5, yi - 1, yi + t + p.REV_eye_off + 1, x=sd[0], z=sd[1])    # M6 (Ø5,0) roscado
    return s


def build(p):
    return bucket_rel_loc(p, -p.bucket_down_deg) * build_down(p)


def placements(p, steer=0.0, bucket=0):
    from params import loc_bucket
    return [loc_bucket(p, bool(bucket), steer)]


def coverage(p, part_down, n=24):
    """Fracción del disco del chorro (r_chorro + cono hasta el fondo de la cuchara) tapada por la
    proyección de la cuchara sobre el plano YZ (bucket abajo)."""
    import numpy as np
    v, f = part_down.tessellate(0.3, 0.3)
    V = np.array([(q.Y, q.Z) for q in v])
    X = np.array([q.X for q in v])
    F = np.array(f)
    F = F[X[F].min(axis=1) >= p.STE_X_exit]           # solo lo que está detrás de la salida
    T = V[F]
    xback = p.STE_X_exit + p.REV_cup_dx + p.REV_cup_ax
    R = p.STE_r_jet + (xback - p.STE_X_exit) * math.tan(math.radians(p.STE_cone_deg))
    pts = [(R * math.sqrt((i + 0.5) / n) * math.cos(2.399963 * k), R * math.sqrt((i + 0.5) / n) * math.sin(2.399963 * k))
           for i in range(n) for k in range(i * 6, i * 6 + 6 * (1 + i // 4))]
    pts = np.array(pts)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    hit = 0
    for q in pts:
        d1 = (q[0] - b[:, 0]) * (a[:, 1] - b[:, 1]) - (a[:, 0] - b[:, 0]) * (q[1] - b[:, 1])
        d2 = (q[0] - c[:, 0]) * (b[:, 1] - c[:, 1]) - (b[:, 0] - c[:, 0]) * (q[1] - c[:, 1])
        d3 = (q[0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (q[1] - a[:, 1])
        neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
        pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        if np.any(~(neg & pos)):
            hit += 1
    return hit / len(pts)


def checks(p, part):
    import importlib.util
    import params as Pm
    down = bucket_rel_loc(p, p.bucket_down_deg) * part
    cov = coverage(p, down)
    cone_v = inter_vol(part, jet_cone(p))
    zmin = min(down.moved(Pm.loc_steer(p, s)).bounding_box().min.Z for s in (-p.steer_max, 0.0, p.steer_max))
    # barrido intermedio contra la boquilla
    spec = importlib.util.spec_from_file_location("ste01", os.path.join(os.path.dirname(__file__), "P1-STE-01_boquilla.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    noz = m.build(p)
    vmax = 0.0
    for a in range(0, int(p.bucket_down_deg) + 1, 10):
        vmax = max(vmax, inter_vol(bucket_rel_loc(p, a) * part, noz))
    s_up, s_dn = stud_pt(p), stud_pt(p, True)
    stroke = math.hypot(s_dn[0] - s_up[0], s_dn[1] - s_up[1])
    xb = p.STE_X_exit
    lip = cup_pts(p, 0.0)[-1]
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("abajo: proyección sobre el chorro (r + cono 5°) [fracción]", cov, 0.90, ">="),
            ("arriba: intersección con el cono del chorro (5°) [mm³]", cone_v, 0.1, "<="),
            ("barrido 0→70° sin tocar la boquilla [mm³]", vmax, 1.0, "<="),
            ("abajo: punto más bajo sobre la quilla (z_bote, ±δmax) [mm]", zmin, 5.0, ">="),
            ("cuchara detrás de la salida (labio inferior − salida) [mm]", lip[0] - xb, -2.0, ">="),
            ("labio inferior bajo el cuerpo de la boquilla [mm]", -lip[1] - p.STE_ro, 4.0, ">="),
            ("semieje Z de la cuchara − radio del chorro con cono [mm]",
             p.REV_cup_az - (p.STE_r_jet + (p.REV_cup_dx + p.REV_cup_ax) * math.tan(math.radians(p.STE_cone_deg))), 5.0, ">="),
            ("ancho libre entre brazos − Ø chorro con cono [mm]",
             2 * p.REV_y_in - 2 * (p.STE_r_jet + (p.REV_cup_dx + p.REV_cup_ax) * math.tan(math.radians(p.STE_cone_deg))), 4.0, ">="),
            ("brazo ↔ cuerpo de la boquilla (Y) [mm]", p.REV_y_in - p.STE_ro, 1.5, ">="),
            ("carrera de la varilla del Mach5 [mm]", stroke, 0.8 * p.REV_mach5_stroke, "<="),
            ("cuerda de la varilla vertical (|ΔX| arriba–abajo) [mm]", abs(s_dn[0] - s_up[0]), 0.5, "<=")]
