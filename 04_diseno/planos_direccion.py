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
    xt = math.sqrt(max(Rs ** 2 - p.STE_ro_front ** 2, 0.0))
    Xb = p.X_bucket_pivot - p.X_steer_pivot
    import sys as _sys
    _sys.path.insert(0, str(HERE / "piezas"))
    import _release as RL
    lx, lz = RL.lock_xz(p, 1)
    lx -= p.X_steer_pivot
    lx2, lz2 = RL.lock_xz(p, -1)
    lx2 -= p.X_steer_pivot
    out.append(T("P1-STE-01", "boquilla", "Al 6061-T6 (anodizado duro 50 µm)",
                 [(round(xt, 2), round(2 * Rs, 2), f"esfera SR{Rs:g} (centro en la cara)"),
                  (round(16.0 - xt, 2), round(2 * p.STE_ro_front, 2), "tramo en la rótula"),
                  (6.0, round(2 * ro, 2), "cono"), (round(p.L_steer - 22.0, 2), round(2 * ro, 2), "cuerpo")],
                 feats=[(0.0, "cara = eje de giro (X_steer_pivot)"), (p.STE_bell_L, f"fin abocinado → Ø{2*rb:.2f}"),
                        (Xb, f"eje del bucket Z={p.Z_bucket_pivot:.2f}, Ø{p.REV_sp_pilot_d:g} H7 escariado en CADA oreja (piloto del espaciador P1-REV-02)"),
                        (p.STE_riser_x[0], f"torre del yugo X' {p.STE_riser_x[0]:g}–{p.STE_riser_x[1]:g}, 4×M8×16")],
                 notes=[f"Paso interior: boca Ø{2*rf:.1f} en la cara, arco tangente a Ø{2*rb:.2f} H11 en {p.STE_bell_L:g} mm; recto hasta la salida",
                        f"Exterior: SR{Rs:g}, Ø{2*p.STE_ro_front:g} hasta X' 16, cono a Ø{2*ro:g} en X' 22; mejilla superior Z {p.STE_cheek_z0:.2f}–{p.STE_riser_top:.2f} con Ø8 H7",
                        f"Orejas de pivote ±Z: cara a |Z| = {p.STE_ear_top:.2f} (−0,1/0), R{p.STE_ear_rp:g} alrededor del eje de giro; M6×{p.STE_m6_depth:g} en el eje",
                        f"Orejas del bucket |Y| {p.STE_ear_y0:g}–{p.STE_ear_y1:g} ({p.STE_ear_t:g} mm), R{p.STE_ear_r:g} alrededor del pivote; "
                        f"+Y: M{p.REV_lock_thread_d:g}×1,5-6H del émbolo en X'={lx:.1f}, Z={lz:.1f}" + (
                            f"; −Y: M{p.REV_lock_thread_d:g}×1,5-6H del 2.º émbolo en X'={lx2:.1f}, Z={lz2:.1f}" if p.REV_n_locks > 1 else "") +
                        f"; lóbulo R{p.STE_lock_lobe_r:g} alrededor de cada rosca",
                        f"Ø{p.REV_sp_pilot_d:g} H7 y roscas M{p.REV_lock_thread_d:g}×1,5 con plantilla referida al pivote (posición ±0,1); cara exterior plana "
                        f"Ra 1,6 en Ø{p.REV_sp_fl_d + 4:g} alrededor del pivote (apoyo de la brida del espaciador), ANODIZADA (no enmascarar: aísla del 316)",
                        f"Radio R{_mod('P1-STE-01_boquilla').EAR_LIP_R:g} donde el frente de cada oreja de pivote toca la cara del labio de entrada (|Y| = {p.STE_ear_rp:g}; F-03)",
                        f"Hueco de las orejas de la bomba (|Z| {p.Z_steer_lug:.2f}–{p.Z_steer_lug + p.STE_lug_t:.2f}): fresar el barrido ±{p.STE_sweep:g}° (STEP)",
                        "Cotas 3D completas en step/P1-STE-01_boquilla.step (marco JET, δ = 0)"]))
    # ---------------- pernos de pivote
    sh = p.STE_head_z0 - p.STE_ear_top
    out.append(T("P1-STE-02", "perno_sup", M316,
                 [(p.STE_m6_depth - 1.0, 6.0, "M6 (Loctite 243)"), (round(sh, 2), p.steer_pin_d, "hombro Ø8 e8"),
                  (p.STE_head_t, p.STE_head_d, "cabeza")],
                 feats=[(p.STE_m6_depth - 1.0, "escalón: apoya en la oreja de la boquilla")],
                 notes=["Hombro Ø8 e8 (7,947–7,972), Ra 0,8; gira en el buje POM Ø8,1 de la oreja de la bomba (P1-PMP-11)",
                        "Mejilla superior de la boquilla Ø8 H7 escariado: cabeza apretada (biempotrado)", "Hexágono interior 5"]))
    sh5 = (p.Z_steer_lug + p.STE_lug_t - 1.0) - p.STE_ear_top
    out.append(T("P1-STE-05", "perno_inf", M316,
                 [(p.STE_m6_depth - 1.0, 6.0, "M6 (Loctite 243)"), (round(sh5, 2), p.steer_pin_d, "hombro Ø8 e8")],
                 notes=["Espárrago sin cabeza: hexágono interior 4 en la punta (abajo)", "Punta 1 mm adentro del buje de la bomba"]))
    out.append(T("P1-STE-03", "arandela_pom", "POM-C",
                 [(p.STE_wash_t, p.STE_wash_od, f"Ø{p.STE_wash_id:g} interior")],
                 notes=["Arandela de empuje ×3", "Planitud 0,05"]))
    m8t = _mod("P1-STE-08_tope_direccion")
    Rp, th0, dlt = m8t.geom(p)
    out.append(PL("P1-STE-08", "tope_direccion", "Al 5083-H111", 150.0, 90.0, 8.0,
                  [(20.0, 15.0, 6.6, "M6 al espejo (ala)"), (60.0, 15.0, 6.6, "M6 al espejo (ala)")],
                  notes=[f"Arco alrededor del eje de giro: ranura R{Rp - 12:.1f}–R{Rp + 12:.1f} entre {th0 - p.STE_stop_deg - dlt:.1f}° y {th0 + p.STE_stop_deg + dlt:.1f}° (marco JET)",
                         f"Topes a ±{p.STE_stop_deg:g}° (poste del yugo); taco POM 3 mm pegado en cada cara de tope",
                         f"Plano de la placa ⟂ eje de giro, Z = {p.STE_stop_z[0]:g}–{p.STE_stop_z[1]:g}; ala doblada 90° (STEP)"]))
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
                         f"Chapa Al 5083 {p.REV_t:g} mm; nervio central 4 mm (alto 12) soldado en el lomo; brazos soldados TIG 5183 en ambos bordes",
                         f"Bucket armado: plantilla de soldadura en posición ABAJO ({p.bucket_down_deg:g}°)"]))
    P0 = mb.P_(p)
    from _dir_common import hull, circ, rot_xz
    cup_o = mb.cup_pts(p, p.REV_t)
    rl = p.REV_lock_lobe_r
    sd = mb.stud_pt(p, down=True)
    for side, nm, lado in ((1, "bucket_brazo_estribor", "+Y (estribor del bote)"), (-1, "bucket_brazo_babor", "−Y (babor del bote)")):
        if side < 0 and p.REV_n_locks < 2:
            continue
        lk = mb.lock_pt(p, side)
        lk_up = rot_xz(lk, P0, p.bucket_down_deg)
        pts = circ(*P0, p.REV_boss_r) + cup_o + circ(*lk, rl) + circ(*lk_up, rl)
        holes = [(P0[0], P0[1], p.REV_bush_od, "buje POM (H7)"),
                 (lk[0], lk[1], p.REV_lock_hole_d, f"traba ABAJO ({mb.RL.lock_ang(p, side):g}°, r {p.REV_lock_r:g}) — con plantilla"),
                 (lk_up[0], lk_up[1], p.REV_lock_hole_d, "traba ARRIBA — con plantilla")]
        if side > 0:
            pts += circ(*sd, 12.0)
            holes.append((sd[0], sd[1], 5.0, "M6 (con buje soldado Ø16 × 4)"))
        w, h, hh = _bbox_holes(hull(pts), holes)
        out.append(PL("P1-REV-01", nm, "Al 5083-H111", w, h, p.REV_t, hh,
                      notes=[f"Brazo {lado}; contorno = STEP (posición ABAJO): placa principal + lóbulos r {rl:g} alrededor de cada "
                             "traba, el de la traba ABAJO unido al labio superior de la cuchara (sin muesca: FEA ronda 3)",
                             f"Chapa {p.REV_t:g} mm; aro de refuerzo Ø{2 * p.REV_boss_r:g} × {p.REV_ring_t:g} soldado en la cara exterior del pivote "
                             f"(buje POM Ø{p.REV_bush_od:g} H7 × {p.REV_bush_L:g} pasante brazo + aro)",
                             f"Agujeros de traba Ø{p.REV_lock_hole_d:g} (+0,1/0) DESPUÉS DE SOLDAR, con plantilla centrada en el agujero del buje "
                             f"Ø{p.REV_bush_od:g} H7 (05 §bucket), posición ±0,2: cada traba sola lleva todo M_h, no hay reparto que ajustar"]))
    m2 = _mod('P1-REV-02_perno_bucket')
    out.append(T("P1-REV-02", "espaciador_pivote_bucket", "Dúplex 1.4462 (2205) +AT barra Ø40, certificado 3.1 (Rp0,2 ≥ 450)",
                 [(round(m2.pilot_L(p), 2), p.REV_sp_pilot_d, f"piloto Ø{p.REV_sp_pilot_d:g} h6 (ajustado en la oreja: lleva corte y momento)"),
                  (p.REV_sp_fl_t, p.REV_sp_fl_d, f"brida Ø{p.REV_sp_fl_d:g}"),
                  (round(m2.shoulder_L(p) - p.REV_sp_fl_t, 2), p.REV_pin_d, f"muñón Ø{p.REV_pin_d:g} h7, Ra 0,8 (gira el buje POM)")],
                 feats=[(round(m2.pilot_L(p), 2), "cara de apoyo de la brida: plana, a escuadra ≤ 0,02 con el piloto")],
                 notes=[f"Agujero Ø12,5 pasante (tornillo ISO 4017 M12 × {m2.bolt_len_iso(p):g} A4-80); ×2",
                        "Montaje: Tef-Gel en piloto, cara de la brida y rosca; arandela ISO 7089 M12 bajo la cabeza,",
                        f"  espaciador, oreja, arandela ancha ISO 7093 (Ø{p.REV_washer_in[0]:g} × {p.REV_washer_in[1]:g}) y tuerca ISO 7040 M12 A4-80 por dentro",
                        f"Par {p.REV_bolt_T_Nm:g} N·m → precarga {p.REV_bolt_pre_N / 1000:.0f}–{p.REV_bolt_pre_max_N / 1000:.0f} kN "
                        f"(K {p.REV_bolt_K[0]:g}–{p.REV_bolt_K[1]:g} [ESTIMADO])",
                        f"El piloto ({m2.pilot_L(p):.1f} mm) es 0,5 más corto que la oreja: aprieta la brida, no el piloto",
                        "Juego axial del bucket 0,3 mm contra la arandela de la cabeza (verificar a mano: gira libre)"]))
    out.append(T("P1-REV-03", "buje_bucket", "POM-C",
                 [(p.REV_bush_fl_t, p.REV_bush_fl_d, "brida"), (p.REV_bush_L, p.REV_bush_od, f"Ø{p.REV_pin_d + 0.1:g} interior, escariado tras prensar")],
                 notes=[f"Exterior Ø{p.REV_bush_od:g} con 0,05–0,10 de interferencia en el agujero Ø{p.REV_bush_od:g} H7 del brazo + aro",
                        f"Prensar y DESPUÉS escariar Ø{p.REV_pin_d + 0.1:g} (+0,05/0): el prensado cierra el juego (R4-08)", "×2"]))
    # ---------------- émbolo de traba propio P1-REV-04 (cuerpo + tapa + perno; resorte comprado)
    tip = RL.pin_tip_y(p) - (p.STE_ear_y1 - RL.PLG_GUIDE)                      # largo del Ø16
    tail = RL.PLG_SPRING_L1 + RL.PLG_CAP_T + RL.PLG_KNOB_L                       # cola: cámara + tapa + pomo (la carrera NO se suma)
    out.append(T("P1-REV-04", "embolo_cuerpo", "AISI 316 (1.4401) barra Ø40 (collar Ø36)",
                 [(p.STE_ear_t, p.REV_lock_thread_d, f"M{p.REV_lock_thread_d:g}×1,5-6g (en la oreja; punta enrasada a la cara exterior)"),
                  (RL.PLG_COLLAR_T, RL.PLG_COLLAR_D, f"collar Ø{RL.PLG_COLLAR_D:g}, 2 planos e/c 32; cara de apoyo a escuadra ≤ 0,02"),
                  (round(RL.PLG_GUIDE + RL.PLG_SPRING_L1 - p.STE_ear_t - RL.PLG_COLLAR_T, 2), RL.PLG_BODY_D, f"cuerpo Ø{RL.PLG_BODY_D:g}"),
                  (RL.PLG_CAP_T, RL.PLG_BODY_D, "tapa roscada M20×1 con Ø10,2 (cola del perno)")],
                 feats=[(0.0, "punta: cara exterior de la oreja"), (RL.PLG_GUIDE, "fin de la guía / inicio de la cámara del resorte")],
                 notes=[f"Interior Ø{p.REV_lock_pin_d:g} H8 pasante (guía del perno, Ra 0,8); rosca interior M20×1 × 6 atrás para la tapa; ×2",
                        f"El collar apoya en la cara interior de la oreja: apretar el cuerpo a {p.REV_lock_T_Nm:g} N·m (K {p.REV_lock_K[0]:g}–{p.REV_lock_K[1]:g}) con Loctite 243 (rosca de la oreja",
                        "  sin Tef-Gel; la cara del collar sobre el anodizado); la punta queda enrasada a la cara exterior",
                        "Resorte de compresión inox (B-SPRING): alambre 1,6, Ø ext 15, largo libre ≈ 40,",
                        "  instalado 30 (≈ 20 N), con el perno afuera 18 (≈ 44 N) [ESTIMADO]"]))
    out.append(T("P1-REV-04", "embolo_perno", "AISI 316 (1.4401) barra Ø18",
                 [(round(tip, 2), p.REV_lock_pin_d, f"Ø{p.REV_lock_pin_d:g} h9, Ra 0,8; chaflán 1 × 45° en la punta"),
                  (round(tail, 2), 10.0, "cola Ø10 (resorte); M6 × 10 en el extremo para el pomo")],
                 feats=[(round(tip, 2), "escalón = asiento del resorte")],
                 notes=[f"Largo del Ø{p.REV_lock_pin_d:g}: guía {RL.PLG_GUIDE:g} + luz oreja–brazo {p.REV_y_in - p.STE_ear_y1:g} + brazo {p.REV_t:g} + 1 de sobresalida",
                        f"Carrera {p.REV_plunger_stroke:g} mm (liberar pide {RL.need(p):g}); pomo Ø25 × 10 (POM) con ojal para el terminal del Bowden; ×2"]))
    out.append(PL("P1-REV-05", "soporte_mach5", "Al 5083-H111", 95.0 - 25.0, 248.0 - 124.0, 6.0,
                  [(54.0, 14.0 + 6.0, 12.8, "grapa inferior (bloque soldado)"), (54.0, 110.0 + 6.0, 12.8, "grapa superior")],
                  notes=["Placa lateral; alma transversal 6 mm en X' 25–31 y base 27 × 28 con 4 × Ø9 (STEP)"]))
    # ---------------- desbloqueo de las trabas (ronda 4, R4-06/R4-07; ronda 5: DES-01/03/04/05/07): soporte de reenvío,
    # balancines con cubos, ejes, pernos de manivela, eslabones rígidos, vainas y gatillo
    m9 = _mod("P1-REV-09_soporte_bowden")
    _c = lambda v, f=".1f": format(v, f).replace(".", ",")             # noqa: E731
    _g = lambda v: format(v, "g").replace(".", ",")                     # noqa: E731
    M316C = "1.4401+C (AISI 316 estirado, Rp0,2 ≥ 310, certificado 3.1)"
    up = m9.upright_outline(p)
    uy0, uz0 = min(q[0] for q in up), min(q[1] for q in up)
    uw, uh = max(q[0] for q in up) - uy0, max(q[1] for q in up) - uz0
    hl = []
    for sd in RL.lock_sides(p):
        L = RL.lever(p, sd)
        tg = "+Y" if sd > 0 else "−Y"
        hl.append((L["piv"][0] - uy0, L["piv"][1] - uz0, RL.PIV_STUD_D,
                   f"eje del balancín {tg}: Ø{_g(RL.PIV_STUD_D)} H7 escariado DESPUÉS de soldar (eje prensado)"))
    px = RL.pad_x(p)
    zs = RL.stop_z(p)
    tab_l = m9.up_x(p) - (RL.cable_x(p) - RL.ADJ_HOLE_R - RL.ADJ_EDGE)
    out.append(PL("P1-REV-09", "soporte_bowden", "Al 5083-H111", round(uw, 1), round(uh, 1), m9.UP_T, hl,
                  notes=[f"MONTANTE {_g(m9.UP_T)} mm (plano YZ; origen = esquina inferior de estribor del contorno). Conjunto soldado ×1:",
                         f"BASE {m9.BASE_T:g} mm: {_c(px[1] - px[0] - 0.5)} × {2 * m9.BASE_W:g} con 2 × Ø5,5 a {_c(RL.pad_screws(p)[0][0] - px[0] - 0.5)} del borde de proa, ±{abs(RL.pad_screws(p)[0][1]):g} "
                         f"(ISO 4762 M5 × 12 A4-70 + Tef-Gel a las roscas M5 × 7,5 del pad de P1-STE-01)",
                         f"PESTAÑAS {RL.TAB_T:g} mm ×2: {_c(tab_l)} × {2 * m9.TAB_HW:g}, M6 en Y {_c(RL.cable_y(p, 1))} y {_c(RL.cable_y(p, -1))}, "
                         f"cara inferior a Z {_c(zs)} (marco de la boquilla); reguladores M6 del Bowden (P1-REV-10)",
                         f"Montante a X {_c(m9.up_x(p))}–{_c(m9.up_x(p) + m9.UP_T)}; la base apoya de cara en el pad plano (Z {_c(RL.pad_z(p))})",
                         "Soldar base + montante + pestañas con plantilla; escariar los Ø8 H7 de los ejes después de soldar, a escuadra con la base",
                         "Ejes (hoja P1-REV-09_eje_balancin): prensar desde proa hasta el escalón, Loctite 638; balancines: hoja P1-REV-09_balancin"]))
    lo = m9.lever_outline(p)
    lu0, lv0 = min(q[0] for q in lo), min(q[1] for q in lo)
    lw, lh = max(q[0] for q in lo) - lu0, max(q[1] for q in lo) - lv0
    Lc = [m9.crank_pin_len(p, sd) for sd in RL.lock_sides(p)]
    xph, _, Lph = RL.piv_hub(p)
    xch, _, Lch = RL.crank_hub(p)
    out.append(PL("P1-REV-09", "balancin", "Al 5083-H111", round(lw, 1), round(lh, 1), RL.LEV_T,
                  [(-lu0, -lv0, RL.PIV_BUSH_OD, f"eje: Ø{_g(RL.PIV_BUSH_OD)} H7 en el cubo Ø{_g(2 * RL.PIV_BOSS_R)} × {_g(Lph)} "
                    f"(casquillo polimérico con collar Ø{_g(RL.PIV_D)}/Ø{_g(RL.PIV_BUSH_OD)} prensado)"),
                   (-lu0, RL.LEV_L - lv0, RL.CRANK_D, f"perno de manivela: Ø{_g(RL.CRANK_D)} H7 en el cubo Ø{_g(2 * RL.CRANK_HUB_R)} × {_g(Lch)}"),
                   (RL.LEV_L - lu0, -lv0, 2 * RL.NIPPLE_R + 0.2, "terminal (barril Ø5) del cable + ranura 1,8 hacia arriba")],
                  notes=[f"×2 (el del émbolo −Y va dado vuelta). Fresado de placa 5083 de 12: alma {_g(RL.LEV_T)} mm (contorno) + cubos "
                         f"hacia PROA: eje Ø{_g(2 * RL.PIV_BOSS_R)} × {_g(RL.PIV_HUB_H)} y manivela Ø{_g(2 * RL.CRANK_HUB_R)} × {_g(RL.CRANK_HUB_H)} "
                         f"(apoyos {_g(Lph)} y {_g(Lch)} = 2·Ø: toman el par F·e del eslabón, DES-03)",
                         f"Brazos {RL.LEV_L:g} a 90° (1:1): la salida sube lo que corre el pomo",
                         f"Perno de manivela (hoja P1-REV-09_perno_manivela): prensado desde proa hasta el hombro, Loctite 638; "
                         f"anillos DIN 6799 atrás y adelante (ojo del eslabón)",
                         f"Rendimiento estimado del balancín {_c(RL.lever_eta(p), '.2f')} (μ del eje {_g(RL.LEV_MU_PIV)} [ESTIMADO]): engrasar el casquillo"]))
    # eje del balancín (prensado en el montante) y perno de manivela (prensado en el cubo): torneados de 1.4401+C
    l_j = Lph + m9.GAP + m9.CLIP
    out.append(T("P1-REV-09", "eje_balancin", M316C,
                 [(m9.CLIP, RL.PIV_D - 1.0, "ranura DIN 6799 (anillo del balancín)"),
                  (round(l_j - m9.CLIP, 2), RL.PIV_D, f"muñón Ø{_g(RL.PIV_D)} f7 (casquillo del balancín + arandela PTFE 1)"),
                  (m9.UP_T, RL.PIV_STUD_D, f"Ø{_g(RL.PIV_STUD_D)} m6 prensado en el montante (a ras atrás)")],
                 notes=[f"×2. Largo total {_c(m9.pivot_len(p))}; escalón Ø{_g(RL.PIV_STUD_D)}/Ø{_g(RL.PIV_D)} a escuadra: apoya en la cara del montante",
                        "Prensar con Loctite 638; flexión del muñón y presión en el montante: structural_direccion (P1-REV-09)"]))
    lfree = [round(Lc[i] - Lch - RL.CRANK_SHOULDER[1] - 1.0, 2) for i in range(len(Lc))]
    out.append(T("P1-REV-09", "perno_manivela", M316C,
                 [(lfree[-1], RL.CRANK_D, f"Ø{_g(RL.CRANK_D)} h9 libre: ojo del eslabón + ranura DIN 6799 a 2 del extremo"),
                  (RL.CRANK_SHOULDER[1], RL.CRANK_SHOULDER[0], f"hombro Ø{_g(RL.CRANK_SHOULDER[0])} (apoya en la cara del cubo)"),
                  (Lch, RL.CRANK_D, f"Ø{_g(RL.CRANK_D)} m6 prensado en el cubo"), (1.0, RL.CRANK_D - 1.0, "ranura DIN 6799 (atrás)")],
                 notes=[f"×2: largo {_c(Lc[0])} (émbolo +Y, tramo libre {_c(lfree[0])})"
                        + (f" y {_c(Lc[1])} (émbolo −Y, tramo libre {_c(lfree[1])})" if len(Lc) > 1 else "") + "; dibujado el más largo",
                        "Prensar desde proa hasta el hombro con Loctite 638"]))
    hz = RL.LINK_EYE_SLOT_W / 2 + RL.LINK_SLOT + RL.LINK_EYE_WALL
    out.append(PL("P1-REV-09", "eslabon", "1.4401 (AISI 316)", round(2 * RL.LINK_EYE_HALF + RL.LINK_SHANK_L, 1), round(2 * hz, 1),
                  RL.LINK_EYE_T,
                  [(RL.LINK_EYE_HALF, hz, RL.LINK_EYE_SLOT_W, f"ranura {_g(RL.LINK_EYE_SLOT_W)} × {_g(RL.LINK_EYE_SLOT_W + 2 * RL.LINK_SLOT)} VERTICAL (perno de manivela)")],
                  notes=[f"×2. ESLABÓN RÍGIDO (DES-04): ojo {_g(2 * RL.LINK_EYE_HALF)} × {_c(2 * hz)} × {_g(RL.LINK_EYE_T)} con la ranura + vástago M4 × "
                         f"{_g(RL.LINK_SHANK_L)} en el eje (torneado y fresado de barra Ø16)",
                         f"El vástago se rosca en la rosca M4 axial de la cola del perno del émbolo (P1-REV-04) con Loctite 243",
                         f"Largo cara del pomo → eje del perno {_c(RL.LINK, '.2f')} (luz ojo ↔ pomo {_c(RL.LINK_GAP, '.2f')}); ajuste ±{_g(RL.LINK_TOL)} "
                         f"por medias vueltas (0,35): la ranura queda vertical",
                         "Montaje: bucket trabado, pomo apoyado en la tapa: ajustar hasta que el perno de manivela quede a la altura del eje del émbolo"]))
    g = RL.sheath_path(p)
    xs = [g[k][0] for k in ("p0", "pb", "pe", "pf")]
    zz = [g[k][1] for k in ("p0", "pb", "pe", "pf")]
    xr0, zr0 = min(xs), min(zz)
    l_arc = RL.BOWDEN_R * math.pi / 4
    l_str = math.dist(g["pe"], g["pf"])
    out.append(PL("P1-REV-10", "recorrido_vaina", "comprado (vaina Ø5 PTFE + cable inox Ø1,5)", round(max(xs) - xr0, 1), round(max(zz) - zr0, 1),
                  RL.BOWDEN_D,
                  [(g["p0"][0] - xr0, g["p0"][1] - zr0, RL.BOWDEN_D, "sale del regulador M6 (vertical)"),
                   (g["pb"][0] - xr0, g["pb"][1] - zr0, RL.BOWDEN_D, f"inicio de la curva R{RL.BOWDEN_R:g}"),
                   (g["pe"][0] - xr0, g["pe"][1] - zr0, RL.BOWDEN_D, "fin de la curva (45° hacia proa)"),
                   (g["pf"][0] - xr0, g["pf"][1] - zr0, RL.BOWDEN_D, "fin del tramo fijado: sigue el bucle libre")],
                  notes=[f"Línea media en el plano XZ (marco de la boquilla), Y = {_c(RL.cable_y(p, 1))} (émbolo +Y) y {_c(RL.cable_y(p, -1))} (émbolo −Y)",
                         f"Curva R{RL.BOWDEN_R:g} (≥ R{RL.BOWDEN_R_MIN:g} mínimo de la vaina [ESTIMADO]) de {_c(l_arc)} mm + recta a 45° de {_c(l_str)} mm",
                         "Atar las dos vainas al montante con brida inox; bucle libre ≈ 0,5 m (R ≥ 150) hasta el prensaestopas P1-CTL-05",
                         "Regulador M6 + contratuerca en cada pestaña de P1-REV-09: con el bucket trabado, cable apenas flojo "
                         "(pomo apoyado en la tapa); si el cable queda tenso, el perno no entra"]))
    m14 = _mod("P1-CTL-14_gatillo")
    gpts = [q for poly in m14.outline() for q in poly]
    gx0, gz0 = min(q[0] for q in gpts), min(q[1] for q in gpts)
    gw, gh = max(q[0] for q in gpts) - gx0, max(q[1] for q in gpts) - gz0
    w0 = m14.wire_pt(0.0)
    out.append(PL("P1-CTL-14", "gatillo", "Al 6061-T6", round(gw, 1), round(gh, 1), 6.0,
                  [(m14.PIV[0] - gx0, m14.PIV[1] - gz0, m14.PIV_D + 0.1, f"pivote: pasador Ø{m14.PIV_D:g} A4 (mango + placa lateral de P1-CTL-10)"),
                   (w0[0] - gx0, w0[1] - gz0, 4.0, f"pasador Ø4 de la barra igualadora (a {_g(m14.R_W)} del pivote)")],
                  notes=[f"Giro {_g(m14.ANG)}° → {_c(m14.travel())} mm de cable (liberar pide {_c(RL.cable_need(p))} + 3 de juego); dedos {_c(2 * m14.R_F * math.sin(math.radians(m14.ANG / 2)))} mm a {_g(m14.R_F)} del pivote",
                         f"Barra igualadora AISI 316 {m14.BAR_T:g} × 4 × {m14.BAR_L:g}: pasador Ø4 al centro, ranuras de los terminales a ±{m14.BAR_H:g}; gira libre",
                         f"Tiro por cable con {p.CTL_hand_F:g} N de mano: {m14.cable_pull_design(p):.0f} N (η gatillo {_g(m14.TRIG_ETA)}) ≥ "
                         f"{RL.cable_force_need(p):.0f} N = resorte {_c(RL.SPRING_F_MAX)} N / (η Bowden {_g(RL.BOWDEN_ETA)} · η balancín {_c(RL.lever_eta(p), '.2f')}) [CALCULADO/ESTIMADO]",
                         "Tope de las vainas: pestaña 5 mm (2 × M6 con contratuerca) de la placa lateral soldada al mango de P1-CTL-10; resorte de torsión de retorno"]))
    out.append(T("P1-REV-06", "perno_varilla", "AISI 316",
                 [(p.REV_t + p.REV_eye_off - 0.5, 6.0, "M6"), (p.REV_eye_w + 2.0, p.REV_stud_d, "hombro Ø8 f7"), (4.0, 13.0, "cabeza")],
                 notes=["Rótula hembra M6 del Mach5 en el hombro"]))
    # ---------------- mandos
    import _transom as TR
    PY = TR.plate_y(p)
    holes = [(y - PY[0], z - TR.plate_z(p)[0], d, t) for (y, z, d, t) in TR.holes(p)]
    out.append(PL("P1-CTL-01", "placa_espejo", "Al 5083-H111", PY[1] - PY[0], TR.plate_z(p)[1] - TR.plate_z(p)[0],
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
    m10 = _mod("P1-CTL-10_palanca_bucket")
    out.append(PL("P1-CTL-10", "palanca_bucket", "Al 6061-T6", 80.0, 30.0 + 112.0, 8.0,
                  [(40.0, 30.0, 12.2, "eje (buje POM)"), (40.0 - 39.8, 30.0 + 23.0, 8.0, "perno de manivela Ø8 prensado")],
                  notes=["Muescas Ø6,4 × 3 en r 22, φ 90° y 210° (cara interior)", "Escalón 20 mm a babor y mango hasta z 135 (soldado)",
                         "Placa lateral 4 mm (≈ 28 × 65, x −20…8, z 70–135) soldada al mango: lleva el pasador Ø5 del gatillo P1-CTL-14",
                         f"  y la pestaña de tope de las 2 vainas (5 mm, x {_g(m10.STOP_X[0])}…{_g(m10.STOP_X[1])}, y {_g(m10.PERCH_Y[0])}–{_g(m10.STOP_Y1)}, "
                         f"z {_g(m10.PERCH[4][1])}–{_g(m10.PERCH[5][1])}): 2 × M6 en y {_g((m14.BAR_Y[0] + m14.BAR_Y[1]) / 2)}, "
                         f"z {_c(m14.wire_pt(0.0)[1] - m14.BAR_H)} y {_c(m14.wire_pt(0.0)[1] + m14.BAR_H)} (borde ≥ {_g(m10.ADJ_EDGE_MIN)})",
                         "  Reguladores M6 del Bowden con su contratuerca apoyada en la pestaña; contorno exacto en el STEP"]))
    out.append(T("P1-CTL-11", "eje_palancas", "AISI 316",
                 [(6.0, 18.0, "cabeza portaimán Ø10,2 × 3"), (32.0, 12.0, "Ø12 h7"), (3.0, 12.0, "ranura anillo E")],
                 feats=[(9.0, "pasador Ø4 (palanca del acelerador)")], notes=["Imán NdFeB Ø10×3 diametral pegado (epoxi)"]))
    out.append(T("P1-CTL-12", "perno_enclav", "AISI 316", [(13.0, p.CTL_ilock_d, "Ø6 g6, puntas 45°")], notes=["×2"]))
    return out
