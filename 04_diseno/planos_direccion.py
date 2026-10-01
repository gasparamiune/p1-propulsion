"""planos_direccion.py — planos acotados (SVG) de las piezas torneadas/mecanizadas/de chapa del grupo
DIRECCIÓN, REVERSA y MANDOS. Todas las cotas salen de params (params_direccion.py) y de las piezas."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _mod(stem):
    import sys
    sys.path.insert(0, str(HERE / "piezas"))
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), HERE / "piezas" / f"{stem}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bbox_holes(poly, holes):
    xs, zs = [q[0] for q in poly], [q[1] for q in poly]
    x0, z0 = min(xs), min(zs)
    return max(xs) - x0, max(zs) - z0, [(x - x0, z - z0, d, t) for (x, z, d, t) in holes]


def draw(p, H):
    T, PL = H["turned"], H["plate"]
    out = []
    M316 = "AISI 316 (1.4401) — pernos de pivote: estirado en frío +C, Rp0,2 ≥ 310 MPa"

    # ---------------- P1-STE-01 boquilla (perfil torneado + notas de fresado)
    Rs, ro, rf, rb = p.STE_Rs, p.STE_ro, p.STE_rf, p.STE_rb
    xt = math.sqrt(max(Rs ** 2 - ro ** 2, 0.0))
    Xb = p.X_bucket_pivot - p.X_steer_pivot
    lx = p.X_bucket_pivot + p.REV_lock_r * math.cos(math.radians(p.REV_lock_ang)) - p.X_steer_pivot
    lz = p.Z_bucket_pivot + p.REV_lock_r * math.sin(math.radians(p.REV_lock_ang))
    out.append(T("P1-STE-01", "boquilla", "Al 6061-T6 (anodizado duro 50 µm)",
                 [(round(xt, 2), round(2 * Rs, 2), f"esfera SR{Rs:g} (centro en la cara)"),
                  (round(p.L_steer - xt, 2), round(2 * ro, 2), "cuerpo")],
                 feats=[(0.0, "cara = eje de giro (X_steer_pivot)"), (p.STE_bell_L, f"fin abocinado → Ø{2*rb:.2f}"),
                        (Xb, f"eje del bucket Z={p.Z_bucket_pivot:.2f}, Ø8,4 pasante ±Y"),
                        (p.STE_riser_x[0], f"torre del yugo X' {p.STE_riser_x[0]:g}–{p.STE_riser_x[1]:g}, 4×M8×16")],
                 notes=[f"Paso interior: boca Ø{2*rf:.1f} en la cara, arco tangente a Ø{2*rb:.2f} H11 en {p.STE_bell_L:g} mm; recto hasta la salida",
                        f"Orejas de pivote ±Z: cara a |Z| = {p.STE_ear_top:.2f} (−0,1/0), R{p.STE_ear_rp:g} alrededor del eje de giro; M6×{p.STE_m6_depth:g} en el eje",
                        f"Orejas del bucket |Y| {p.STE_ear_y0:g}–{p.STE_ear_y1:g}; +Y: M20×1,5 del émbolo en X'={lx:.1f}, Z={lz:.1f}",
                        f"Hueco de las orejas de la bomba (|Z| {p.Z_steer_lug:.2f}–{p.Z_steer_lug + p.STE_lug_t:.2f}): fresar el barrido ±{p.STE_sweep:g}° (STEP)",
                        "Cotas 3D completas en step/P1-STE-01_boquilla.step (marco JET, δ = 0)"]))
    # ---------------- pernos de pivote
    sh = p.STE_head_z0 - p.STE_ear_top
    for pid, nm in (("P1-STE-02", "perno_sup"), ("P1-STE-05", "perno_inf")):
        out.append(T(pid, nm, M316,
                     [(p.STE_m6_depth - 1.0, 6.0, "M6 (Loctite 243)"), (round(sh, 2), p.steer_pin_d, "hombro Ø8 e8"),
                      (p.STE_head_t, p.STE_head_d, "cabeza")],
                     feats=[(p.STE_m6_depth - 1.0, "escalón: apoya en la oreja de la boquilla")],
                     notes=["Hombro Ø8 e8 (7,947–7,972), Ra 0,8; gira en el Ø8,2 de la oreja de la bomba",
                            "Hexágono interior 5 en la cabeza; chaflanes 0,5 × 45°"]))
    out.append(T("P1-STE-03", "arandela_pom", "POM-C",
                 [(p.STE_wash_t, p.STE_wash_od, f"Ø{p.STE_wash_id:g} interior")],
                 notes=["Arandela de empuje ×4", "Planitud 0,05"]))
    # ---------------- yugo
    m4 = _mod("P1-STE-04_brida_yugo")
    polys = m4.outline_parts(p)
    pts = [q for poly in polys for q in poly]
    holes = [(x, y, 9.0, "M8 pasante (torre)") for x, y in p.STE_riser_bolts]
    holes += [(p.STE_post_x, p.STE_post_y, 16.2, "centrador del poste, prof. 5")]
    holes += [(p.STE_post_x + 16 * math.cos(math.radians(45 + 90 * k)), p.STE_post_y + 16 * math.sin(math.radians(45 + 90 * k)),
               6.8, "M8 × 16 (brida del poste)") for k in range(4)]
    w, h, hh = _bbox_holes(pts, holes)
    out.append(PL("P1-STE-04", "brida_yugo", "Al 5083-H111", w, h, p.STE_yoke_t, hh,
                  notes=["Contorno: banda X' 6–30 + extremo R22 alrededor del poste (STEP)", "Origen: esquina del contorno (X' mín., Y mín.)"]))
    out.append(T("P1-STE-06", "poste", "Al 6061-T6",
                 [(4.0, 16.0, "centrador"), (8.0, 44.0, "brida 4×Ø9 en Ø32"),
                  (round(p.STE_post_z1 - p.STE_arm_t - (p.STE_zc_top + p.STE_yoke_t) - 8.0, 1), p.STE_post_d, "caña"),
                  (p.STE_arm_t + 10.0, 16.0, "M16×1,5, doble plano 17")],
                 notes=["Tuerca M16 A4 autoblocante sobre el brazo", "Anodizado duro"]))
    L7 = p.STE_stud_x - p.STE_post_x
    out.append(PL("P1-STE-07", "brazo", "Al 5083-H111", L7 + 28.0, 32.0, p.STE_arm_t,
                  [(16.0, 16.0, 17.2, "doble D 17 (poste M16)"), (16.0 + L7, 16.0, p.STE_stud_hole, "rótula M8 DIN 71802")],
                  notes=["Extremos redondeados R16 / R12"]))
    # ---------------- bucket (chapas planas)
    mb = _mod("P1-REV-01_bucket")
    outer = mb.cup_pts(p, p.REV_t / 2)
    Ldev = sum(math.hypot(outer[i + 1][0] - outer[i][0], outer[i + 1][1] - outer[i][1]) for i in range(len(outer) - 1))
    out.append(PL("P1-REV-01", "bucket_cuchara", "Al 5083-H111", round(Ldev, 1), 2 * p.REV_y_in, p.REV_t, [],
                  notes=[f"Desarrollo de la cuchara: curvar en rodillo a elipse {p.REV_cup_ax:g} × {p.REV_cup_az:g} (fibra interior)",
                         "Nervio central 4 mm (alto 12) soldado en el lomo; brazos soldados TIG 5183 en ambos bordes",
                         f"Bucket armado: plantilla de soldadura en posición ABAJO ({p.bucket_down_deg:g}°)"]))
    P0 = mb.P_(p)
    from _dir_common import hull, circ, rot_xz
    lk = mb.lock_pt(p)
    lk_up = rot_xz(lk, P0, p.bucket_down_deg)
    sd = mb.stud_pt(p, down=True)
    poly = hull(circ(*P0, p.REV_boss_r) + mb.cup_pts(p, p.REV_t) + circ(*sd, 12.0) + circ(*lk, 12.0) + circ(*lk_up, 12.0))
    holes = [(P0[0], P0[1], p.REV_bush_od, "buje POM (H7)"), (lk[0], lk[1], p.REV_lock_hole_d, "traba ABAJO"),
             (lk_up[0], lk_up[1], p.REV_lock_hole_d, "traba ARRIBA"), (sd[0], sd[1], 5.0, "M6 (con buje soldado Ø16 × 4)")]
    w, h, hh = _bbox_holes(poly, holes)
    out.append(PL("P1-REV-01", "bucket_brazo_estribor", "Al 5083-H111", w, h, p.REV_t, hh,
                  notes=["Brazo +Y (estribor del bote); el −Y es igual sin trabas ni perno de varilla",
                         "Contorno = envolvente (STEP, posición ABAJO); aro de refuerzo Ø24 × 4 soldado en el pivote"]))
    out.append(T("P1-REV-02", "perno_bucket", M316,
                 [(10.0, 8.0, "M8"), (8.0, 10.0, "M8 en oreja"), (round(_mod('P1-REV-02_perno_bucket').shoulder_L(p), 2), p.REV_pin_d, "hombro Ø10 f7"),
                  (p.REV_head_t, p.REV_head_d, "cabeza")],
                 notes=["Tuerca M8 A4 autoblocante por dentro de la oreja", "×2"]))
    out.append(T("P1-REV-03", "buje_bucket", "POM-C",
                 [(p.REV_bush_fl_t, p.REV_bush_fl_d, "brida"), (p.REV_bush_L, p.REV_bush_od, f"Ø{p.REV_pin_d + 0.1:g} H9 interior")],
                 notes=["Prensado en el brazo + aro (Ø14 H7)", "×2"]))
    out.append(PL("P1-REV-05", "soporte_mach5", "Al 5083-H111", 95.0 - 25.0, 248.0 - 124.0, 6.0,
                  [(54.0, 14.0 + 6.0, 12.8, "grapa inferior (bloque soldado)"), (54.0, 110.0 + 6.0, 12.8, "grapa superior")],
                  notes=["Placa lateral; alma transversal 6 mm en X' 25–31 y base 27 × 28 con 4 × Ø9 (STEP)"]))
    out.append(T("P1-REV-06", "perno_varilla", "AISI 316",
                 [(p.REV_t + p.REV_eye_off - 0.5, 6.0, "M6"), (p.REV_eye_w + 2.0, p.REV_stud_d, "hombro Ø8 f7"), (4.0, 13.0, "cabeza")],
                 notes=["Rótula hembra M6 del Mach5 en el hombro"]))
    # ---------------- mandos
    import _transom as TR
    PY = TR.plate_y(p)
    holes = [(y - PY[0], z - TR.PLATE_Z[0], d, t) for (y, z, d, t) in TR.holes(p)]
    out.append(PL("P1-CTL-01", "placa_espejo", "Al 5083-H111", PY[1] - PY[0], TR.PLATE_Z[1] - TR.PLATE_Z[0],
                  TR.PLATE_T, holes, notes=["Por dentro del espejo; origen = esquina inferior de estribor (y mín., z mín.) en el BOTE",
                                            "Taladrar el espejo con la placa como plantilla; Sikaflex 291i en todos los pasos"]))
    out.append(T("P1-CTL-04", "pasamuros_m66", "AISI 316",
                 [(3.0, 32.0, "brida (afuera)"), (20.0, 20.0, "M20×1,5"), (20.0, 32.0, "rosca 7/8\"-14 UNF × 18")],
                 notes=[f"Agujero Ø{p.CTL_gland_m66_bore + 0.1:g} H9 con ranura de junta tórica + rascador [ESTIMADO: barra 3/8\"]",
                        "Fuelle de goma sobre la barra, por fuera"]))
    m8 = _mod("P1-CTL-08_placa_central")
    out.append(PL("P1-CTL-08", "placa_central", "Al 5083-H111", 120.0, 182.0, 6.0,
                  [(60.0, 150.0, 12.0, "eje Ø12 H8"), (60.0, 150.0 + p.CTL_ilock_r, p.CTL_ilock_d + 0.1, "perno de enclavamiento 2"),
                   (60.0, 150.0 - p.CTL_ilock_r, p.CTL_ilock_d + 0.1, "perno de enclavamiento 3")],
                  notes=["Ala doblada 90° bajo la tapa de la consola, 2 × M6", "Grapas Ø12,8 del Mach5 soldadas en la lengüeta (STEP)"]))
    out.append(PL("P1-CTL-09", "palanca_acel", "Al 6061-T6", 60.0, 30.0 + p.CTL_lever_L + 11.0, 8.0,
                  [(30.0, 30.0, 12.0, "eje (pasador Ø4 transversal)"), (30.0, 30.0 + p.CTL_lever_L, 8.5, "pomo M8")],
                  notes=["Ranuras del enclavamiento en la cara interior: r 22, ancho 6,4, prof. 3, φ 60–90° y 270–310° (chaflán 1×45°)"]))
    out.append(PL("P1-CTL-10", "palanca_bucket", "Al 6061-T6", 80.0, 30.0 + 112.0, 8.0,
                  [(40.0, 30.0, 12.2, "eje (buje POM)"), (40.0 - 39.8, 30.0 + 23.0, 8.0, "perno de manivela Ø8 prensado")],
                  notes=["Muescas Ø6,4 × 3 en r 22, φ 90° y 210° (cara interior)", "Escalón 20 mm a babor y mango hasta z 135 (soldado)",
                         "Gatillo del Bowden de liberación del émbolo (no modelado)"]))
    out.append(T("P1-CTL-11", "eje_palancas", "AISI 316",
                 [(6.0, 18.0, "cabeza portaimán Ø10,2 × 3"), (32.0, 12.0, "Ø12 h7"), (3.0, 12.0, "ranura anillo E")],
                 feats=[(9.0, "pasador Ø4 (palanca del acelerador)")], notes=["Imán NdFeB Ø10×3 diametral pegado (epoxi)"]))
    out.append(T("P1-CTL-12", "perno_enclav", "AISI 316", [(13.0, p.CTL_ilock_d, "Ø6 g6, puntas 45°")], notes=["×2"]))
    return out
