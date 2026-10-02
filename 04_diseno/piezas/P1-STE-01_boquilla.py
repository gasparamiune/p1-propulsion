"""P1-STE-01 — Boquilla direccional (Al 6061-T6 mecanizada).

Tubo que recibe el chorro de la tobera fija (Ø D_noz) y lo orienta ±steer_max alrededor del eje Z_jet
en X = X_steer_pivot. Geometría (marco JET, δ = 0):
  - cara de entrada EN el plano del pivote; frente esférico R = STE_Rs centrado en el pivote, que entra
    en el alojamiento esférico de la tobera fija (P1-PMP-08, R ≤ pmp_steer_ball_R_max) y no avanza al
    girar; boca abocinada Ø 2·STE_rf que se cierra a Ø D_steer_in en STE_bell_L; paso recto a la salida;
  - orejas de pivote ±Z POR DENTRO de las de la bomba (|Z| ≤ Z_steer_lug − STE_gz), radio STE_ear_rp
    alrededor del perno (zona libre de la tobera fija), arandela de empuje POM (P1-STE-03) y tornillo
    con hombro 316 (P1-STE-02 arriba, P1-STE-05 abajo) roscado M6 en la oreja; el hombro Ø8 gira en el
    agujero Ø8,2 de la oreja de la bomba. Hueco = barrido ±(δmax+5°) de la oreja de la bomba inflada;
  - torre del yugo (X' 15–40) detrás del extremo de la oreja de la bomba, con 2 × M6 para la brida
    P1-STE-04 (que lleva el poste y el brazo del cable M66 por encima de la flotación);
  - orejas del bucket (±Y STE_ear_y0–STE_ear_y1, 12 mm) con Ø16 H7 escariado para el piloto del espaciador del
    pivote P1-REV-02 (su brida apoya en la cara exterior; uno por oreja) y rosca M24×1,5 del émbolo propio
    P1-REV-04 en cada una (traba arriba/abajo en los dos brazos del bucket, +Y a REV_lock_ang y −Y a
    REV_lock_ang_m). Cada oreja lleva sola su pivote y su traba con M_h completo (auditoría ronda 4);
  - pad plano sobre el cuerpo a popa de los émbolos con 2 roscas M5 × 7,5 para el soporte de reenvío del desbloqueo
    P1-REV-09 (R4-07).
PETG descartado: FS < 3 en orejas del bucket y pernos (ver structural_direccion.py)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build123d import Polyline, make_face, revolve, Axis, Pos, Rot  # noqa: E402
from cadlib import box, cyl_x, cyl_z, cyl_y, prism_arc, prism_xz  # noqa: E402
from _dir_common import hull, circ, lug_sweep, pump_lug_proxy, inter_vol  # noqa: E402
import _release as RL  # noqa: E402

META = dict(
    id="P1-STE-01", name="boquilla", desc="Boquilla direccional con orejas de pivote, torre del yugo y orejas del bucket",
    material="Al 6061-T6", process="torneada", qty=1, frame="steer", group="jet",
    load_case="Desvío del chorro F_steer (R12: 364 N) + reacciones del bucket (R12: 1,4 kN, impacto ×2)",
    print_rot=(0, 0, 0), solid_frac=1.0,
    orientation="Torneado del cuerpo (barra Ø100 × 150) + fresado 4 ejes de orejas y torre (bloque 6061-T6 100 × 165 × 165)",
    allow={"P1-REV-04": 5.0, "P1-STE-02": 5.0, "P1-STE-05": 5.0, "P1-REV-02": 5.0},   # roscas (émbolo M24, tornillos M6), piloto H7/h6
)


def _revolved(prof):
    face = make_face(Polyline(*[(x, 0, r) for x, r in prof], close=True))
    return revolve(face, Axis.X, 360)


def _bell(p):
    Xp = p.X_steer_pivot
    rf, rb, bl = p.STE_rf, p.STE_rb, p.STE_bell_L
    rho = (bl ** 2 + (rf - rb) ** 2) / (2 * (rf - rb))
    cx, cz = Xp + bl, rb + rho
    a0 = math.degrees(math.atan2(rf - cz, Xp - cx))
    return [(cx + rho * math.cos(math.radians(a)), cz + rho * math.sin(math.radians(a)))
            for a in [a0 + (-90 - a0) * i / 12 for i in range(13)]]


X_FRONT, X_CONE = 16.0, 22.0     # tramo delantero (dentro de la rótula de BOMBA) y cono al cuerpo


def body_profile(p):
    Xp, L = p.X_steer_pivot, p.L_steer
    Rs, r1, ro = p.STE_Rs, p.STE_ro_front, p.STE_ro
    xt = math.sqrt(max(Rs ** 2 - r1 ** 2, 0.0))
    ph1 = math.degrees(math.atan2(r1, xt))
    outer = [(Xp + Rs * math.cos(math.radians(a)), Rs * math.sin(math.radians(a)))
             for a in [90 - (90 - ph1) * i / 8 for i in range(9)]]
    outer += [(Xp + X_FRONT, r1), (Xp + X_CONE, ro), (Xp + L - 1.0, ro), (Xp + L, ro - 1.0)]
    inner = [(Xp + L, p.STE_rb)] + list(reversed(_bell(p)))
    return outer + inner


def bore_cut(p):
    Xp, L = p.X_steer_pivot, p.L_steer
    prof = [(Xp - 40, 0.0), (Xp - 40, p.STE_rf), (Xp - 0.01, p.STE_rf)] + _bell(p)[1:] + \
           [(Xp + L + 2, p.STE_rb), (Xp + L + 2, 0.0)]
    return _revolved(prof)


def lock_point(p, side=1):
    """Eje del émbolo de la traba en la oreja +Y (side = 1) o −Y (side = −1) (fuente única: _release)."""
    return RL.lock_xz(p, side)


def ear_outline(p, sign):
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    pts = circ(Xb, Zb, p.STE_ear_r) + [(Xb - 18, -2.0), (Xb + 18, -2.0), (Xb - 16, 40.0), (Xb + 16, 40.0)]
    rl = p.STE_lock_lobe_r                            # lóbulo alrededor de la rosca M24 del émbolo (ligamento 8)
    if sign > 0:
        lx, lz = lock_point(p)
        pts += circ(lx, lz, rl) + [(lx + 10, -2.0), (lx + 12, 30.0)]
    elif p.REV_n_locks > 1:                           # traba −Y (otro ángulo)
        lx, lz = lock_point(p, -1)
        pts += circ(lx, lz, rl)
    return hull(pts)


def pivot_ear(p, sign):
    """Oreja de pivote de la boquilla (por dentro de la de la bomba). Arriba: + torre del yugo y mejilla
    superior sobre la oreja de la bomba (el hueco lo abre el barrido de la oreja)."""
    Xp = p.X_steer_pivot
    r = p.STE_ear_rp
    if sign > 0:
        zt = p.STE_riser_top
        x0, x1 = p.STE_riser_x
        e = cyl_z(r, 38.0, zt, x=Xp) + box(Xp, Xp + 30.0, -r, r, 38.0, zt)
        return e + box(Xp + x0, Xp + x1, -p.STE_riser_y, p.STE_riser_y, 38.0, zt)
    zt = p.STE_ear_top
    e = cyl_z(r, 38.0, zt, x=Xp) + box(Xp, Xp + 30.0, -r, r, 38.0, zt)
    return Rot(180, 0, 0) * e        # espejo en Z (la oreja es simétrica en Y)


EAR_LIP_R = 2.0      # [SUPUESTO: radio de fresa 2 mm] empalme oreja de pivote ↔ cara del labio (auditoría ronda 3, FEA F-03)


def ear_lip_fillets(p, r=EAR_LIP_R):
    """Empalmes cóncavos de radio r donde el frente de cada oreja de pivote (cilindro r_e alrededor del eje de
    giro, x < X_pivote) se apoya en la cara del labio de entrada (plano x = X_pivote, anillo rf–Rs) a |y| = r_e:
    sin ellos esa esquina es una arista viva donde el FEA no converge (auditoría ronda 3, F-03). En el plano xy
    el arco es tangente al plano del labio y al cilindro de la oreja; se extruye en z y se recorta al anillo."""
    Xp, re = p.X_steer_pivot, p.STE_ear_rp
    yc = math.sqrt((re + r) ** 2 - r ** 2)                   # centro del arco: (Xp − r, ±yc)
    k = re / (re + r)
    t_pt = (Xp - r * k, yc * k)                             # tangencia sobre el cilindro de la oreja
    a_m = 0.5 * math.atan2(-yc, r)                          # ángulo medio del arco (desde el centro)
    mid = (Xp - r + r * math.cos(a_m), yc + r * math.sin(a_m))
    ring = cyl_x(p.STE_Rs, Xp - r - 1.0, Xp + 0.3)          # el labio llega hasta Rs (lo de r < rf lo quita el taladro)
    out = None
    for sz in (1, -1):
        z0, z1 = (38.0, p.STE_Rs + 0.5) if sz > 0 else (-p.STE_Rs - 0.5, -38.0)
        for sy in (1, -1):
            f = prism_arc("xy", (Xp + 0.3, sy * (re - 1.0)),
                          [(Xp + 0.3, sy * yc), (Xp, sy * yc), ((mid[0], sy * mid[1]), (t_pt[0], sy * t_pt[1])),
                           (t_pt[0], sy * (re - 1.0))], z0, z1) & ring
            out = f if out is None else out + f
    return out


def build(p):
    Xp = p.X_steer_pivot
    b = _revolved(body_profile(p))
    b = b + pivot_ear(p, 1) + pivot_ear(p, -1) + ear_lip_fillets(p)
    for s in (1, -1):
        y0, y1 = (p.STE_ear_y0, p.STE_ear_y1) if s > 0 else (-p.STE_ear_y1, -p.STE_ear_y0)
        b = b + prism_xz(ear_outline(p, s), y0, y1)
    b = b - lug_sweep(p, 1) - lug_sweep(p, -1)
    # roscas M6 de los tornillos de pivote (Ø5,0 × STE_m6_depth)
    zt, dpt = p.STE_ear_top, p.STE_m6_depth
    b = b - cyl_z(2.5, zt - dpt, zt + 1, x=Xp) - cyl_z(2.5, -zt - 1, -zt + dpt, x=Xp)
    b = b - cyl_z(4.0, p.STE_cheek_z0 - 1, p.STE_riser_top + 1, x=Xp)          # Ø8 H7 (escariado) en la mejilla superior
    # roscas M6 de la brida del yugo (Ø5,0 × 12) en la torre
    for (xx, yy) in p.STE_riser_bolts:                                      # M8 (Ø6,8 × 16)
        b = b - cyl_z(3.4, p.STE_riser_top - 16, p.STE_riser_top + 1, x=Xp + xx, y=yy)
    # orejas del bucket: Ø16 H7 escariado para el piloto del espaciador P1-REV-02 (su brida apoya en la cara exterior;
    # tuerca adentro), UNA POR OREJA (no pasante de lado a lado: no toca la torre del yugo; auditoría ronda 4, F1)
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    rp = p.REV_sp_pilot_d / 2
    b = b - cyl_y(rp, p.STE_ear_y0 - 1, p.STE_ear_y1 + 1, x=Xb, z=Zb)
    b = b - cyl_y(rp, -p.STE_ear_y1 - 1, -p.STE_ear_y0 + 1, x=Xb, z=Zb)
    rt = p.REV_lock_thread_d / 2
    lx, lz = lock_point(p)
    b = b - cyl_y(rt, p.STE_ear_y0 - 1, p.STE_ear_y1 + 1, x=lx, z=lz)                # M24×1,5 del émbolo (+Y)
    if p.REV_n_locks > 1:
        lx2, lz2 = lock_point(p, -1)
        b = b - cyl_y(rt, -p.STE_ear_y1 - 1, -p.STE_ear_y0 + 1, x=lx2, z=lz2)        # M24×1,5 del 2.º émbolo (−Y)
    # pad de fijación del soporte de reenvío del desbloqueo P1-REV-09 (cara plana sobre el cuerpo, a popa de los émbolos)
    # con 2 roscas M5 × 7,5 (taladro Ø4,2): auditoría ronda 4, R4-07 (geometría en piezas/_release)
    b = b + RL.pad_box(p) - RL.pad_holes(p)
    b = b - bore_cut(p)
    return b


def placements(p, steer=0.0, bucket=0):
    from params import loc_steer
    return [loc_steer(p, steer)]


def _other(stem):
    import importlib.util
    f = os.path.join(os.path.dirname(__file__), stem + ".py")
    if not os.path.exists(f):
        return None
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def free_angle(p, part, fixed):
    """Mayor δ (paso 2,5°) con intersección nula contra 'fixed' (marco JET)."""
    Xp = p.X_steer_pivot
    free = 0.0
    a = 2.5
    while a <= p.STE_sweep + 1e-6:
        v = sum(inter_vol(Pos(Xp, 0, 0) * Rot(0, 0, s) * Pos(-Xp, 0, 0) * part, fixed) for s in (a, -a))
        if v > 0.5:
            break
        free = a
        a += 2.5
    return free


def intercept_fraction(p, n=400):
    """Fracción del área del chorro (r_chorro) cuya huella en el plano de la boca (elipse r/cos δ × r)
    queda fuera del círculo de la boca R_f con δ = δmax."""
    rj, Rf = p.STE_r_jet, p.STE_rf
    c = math.cos(math.radians(p.steer_max))
    out = tot = 0
    for i in range(n):
        for k in range(n):
            u, v = -1 + 2 * (i + 0.5) / n, -1 + 2 * (k + 0.5) / n
            if u * u + v * v > 1:
                continue
            tot += 1
            if (u * rj / c) ** 2 + (v * rj) ** 2 > Rf ** 2:
                out += 1
    return out / tot


def checks(p, part):
    smax = p.steer_max
    rj = p.STE_r_jet
    lug = pump_lug_proxy(p, 1) + pump_lug_proxy(p, -1)
    free_proxy = free_angle(p, part, lug)
    fixed = None
    for stem in ("P1-PMP-08_fixed_nozzle", "P1-PMP-09_transom_plate"):
        m = _other(stem)
        if m is not None:
            sh = m.build(p)
            if stem.startswith("P1-PMP-09"):           # placa en el BOTE → marco JET
                from params import loc_jet
                sh = sh.moved(loc_jet(p).inverse())
            fixed = sh if fixed is None else fixed + sh
    free_real = free_angle(p, part, fixed) if fixed is not None else free_proxy
    rr = math.hypot(p.STE_ear_top, p.STE_ear_rp)
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("giro libre contra las orejas de la bomba (modelo) [°]", free_proxy, smax + 2.5, ">="),
        ("giro libre contra tobera fija + placa de espejo reales (P1-PMP-08/09) [°]", free_real, smax + 2.5, ">="),
        ("boca: fracción del chorro que toca el labio con δmax", intercept_fraction(p), p.STE_intercept_max, "<="),
        ("boca: fracción interceptada con δ = 20°", _frac20(p), 0.0, "<="),
        ("frente esférico ≤ R máx. de la rótula de la tobera fija [mm]", p.STE_Rs, p.raw.get("pmp_steer_ball_R_max", p.STE_Rs), "<="),
        ("pared en el labio de entrada [mm]", p.STE_Rs - p.STE_rf, 1.8, ">="),
        ("pared del cuerpo [mm]", p.STE_ro - p.STE_rb, 4.0, ">="),
        ("pared del tramo delantero (dentro de la rótula) [mm]", p.STE_ro_front - p.STE_rb, 2.5, ">="),
        ("mejilla superior por encima del cuello de la placa (z − R_cuello) [mm]",
         p.STE_cheek_z0 - p.raw.get("pmp_collar_R", p.STE_cheek_z0 - 3.0), 2.0, ">="),
        ("oreja de pivote dentro de la zona libre de la tobera fija (r) [mm]", p.STE_free_r - rr, 1.0, ">="),
        ("piso de la rosca M6 sobre la boca [mm]", (p.STE_ear_top - p.STE_m6_depth) - p.STE_rf, 2.5, ">="),
        ("luz axial a la oreja de la bomba (con arandela) [mm]", p.STE_gz - p.STE_wash_t, 0.3, ">="),
        ("oreja del bucket fuera del cuerpo: Y_oreja_ext − r_ext [mm]", p.STE_ear_y1 - p.STE_ro, 0.0, ">="),
        ("rosca M8 de la torre: piel bajo el agujero (sobre la boca) [mm]", (p.STE_riser_top - 16) - p.STE_rf, 10.0, ">="),
    ]


def _frac20(p):
    class Q:
        pass
    q = Q()
    q.STE_r_jet, q.STE_rf, q.steer_max = p.STE_r_jet, p.STE_rf, 20.0
    return intercept_fraction(q, 200)
