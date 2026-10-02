"""planos_tren.py — planos acotados del grupo TREN Y ELECTRÓNICA (eje, caja del sello, tapa, soporte de
rodamientos, soporte del motor). Todas las cotas salen de params (params.py + params_tren.py)."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _mod(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), str(HERE / "piezas" / f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def draw(p, H):
    import sys
    sys.path.insert(0, str(HERE / "piezas"))
    from _drv_geom import z_axis as z_axis_s
    out = []
    turned, plate = H["turned"], H["plate"]
    sh = _mod("P1-DRV-01_shaft")
    segs = sh.segments(p)
    S_aft = segs[0][0]
    tol = {"asiento impulsor Ø20 g6": "g6", "muñón 2×7204 Ø20 k5": "k5", "asiento acople Ø20 h6": "h6"}
    tsegs = [(b - a, round(d, 2), lab) for a, b, d, lab in segs]
    km = p.drv_km
    k = p.drv_key
    feats = []
    for s0, s1, d2, lab in sh.grooves(p):
        feats.append((s0 - S_aft, f"{lab}: ranura {p.drv_circlip['m']:g} × Ø{d2:g}"))
    feats.append((-p.drv_pin_X - S_aft, f"agujero pasador Ø{p.drv_pin_hole:.2f} H8 pasante (eje Y), X={p.drv_pin_X:.1f}"))
    s_k1 = p.drv_S_front - 0.5
    feats.append((s_k1 - p.drv_cpl_key_l - S_aft, f"chavetero {k['b']:g} P9 × {k['t1']:g} × {p.drv_cpl_key_l:g} (DIN 6885 A)"))
    feats.append((p.drv_S_brgB - S_aft, f"ranura MB4 {km['mb_slot_w']:g} × {km['mb_slot_t']:g} en la rosca {km['thread']}"))
    notes = [
        f"Material 1.4404 (AISI 316L) barra Ø{p.drv_bar_d:g} (R11 §5); entre puntos con luneta; largo total {p.drv_shaft_L:.1f} mm.",
        "Tolerancias: asiento impulsor Ø20 g6; muñón rodamientos Ø20 k5 (Ra 0,8); sello Ø20 h8 (Ra 0,4, sin rayas axiales);"
        " muñón buje estator Ø20 f7; asiento acople Ø20 h6. Concentricidad de todos los Ø ≤ 0,02 mm respecto de A–B (muñones).",
        f"Pasador de corte Al 6061-T6 Ø{p.drv_pin_d:g} (corta a {p.sz['mech']['shear_pin']['T_cut_Nm']:.0f} N·m): "
        f"llevar {p.pmp_pin_spares_sets} juegos de 2 semipasadores de REPUESTO (P1-PMP-05) + 2 anillos DIN 471-20 en la caja de herramientas; revisar cada salida.",
        f"Anillos DIN 471-20 A4: empuje (ranura centrada en X = {p.pmp_circlip_fwd_X:.2f}; arandela 316 20×30×1,5 contra la nariz del impulsor), "
        f"respaldo de la cabeza del sello, retención a popa (X = {p.pmp_circlip_aft_X:.2f}, con arandela). Ranuras = las de P1-PMP-03 (params_bomba).",
        "Montaje (A-08): caja del sello y cabeza entran por la PUNTA DE POPA; rodamientos/KM4/tapa/acople por PROA (ver params_tren.py).",
    ]
    out.append(turned("P1-DRV-01", "shaft", "AISI 316L (1.4404)", tsegs, feats=feats, notes=notes))

    # ---------------- caja del sello
    sh2 = _mod("P1-DRV-02_seal_housing")
    st = sh2.stations(p)
    seal = p.drv_seal
    segs2 = [(st["S0"] - st["S_sp0"], round(p.seal_spigot_d - 0.05, 2), f"espigón Ø{p.seal_spigot_d:g} f7 (cámara Ø{p.drv_chamber_d:g})"),
             (st["S_fl1"] - st["S0"], p.drv_flange_od, f"brida 4 × Ø6,4 en BC{p.seal_bc:g} a {sh2.bolt_angles(p)[0]:g}°+k·90°"),
             (st["S_front"] - st["S_fl1"], sh2.BODY_OD, f"cuerpo: asiento Ø{seal['seat_od']:g} H8 × {seal['seat_l']:g}, paso Ø{sh2.SEAT_WALL_HOLE:g}, linterna Ø{p.drv_lantern_d:g}")]
    feats2 = [(p.drv_S_seat_face - st["S_sp0"], f"cara del asiento fijo (S = {p.drv_S_seat_face:.1f})"),
              ((st["S_wall1"] + st["S_front"]) / 2 - st["S_sp0"], "linterna: 2 ventanas ±Y + G1/8 abajo (testigo)")]
    out.append(turned("P1-DRV-02", "seal_housing", "AISI 316L", segs2, feats=feats2, notes=[
        f"Sello {seal['name']}: pedir caras CARBÓN/SiC (arranques cortos en seco).",
        "Asiento fijo prensado desde popa con agua jabonosa; cámara y alojamiento Ra 1,6; espigón concéntrico a la cara de brida ≤ 0,03.",
        "Junta: Tef-Gel o arandelas aislantes en los M6 si el buje de la toma es de Al (par 316–Al, R10b H21).",
        "Salida G1/8: espiga + manguera transparente Ø6 a la sentina (testigo de goteo)."]))

    # ---------------- tapa de rodamientos
    out.append(turned("P1-DRV-06", "bearing_cover", "Al 6082-T651", [(p.drv_cover_t, p.drv_hsg_od, "tapa: agujero Ø34, 4 × Ø5,4 en BC%g a 45°+k·90°" % p.drv_cover_bc)],
                      notes=["Cara de apoyo plana ≤ 0,02 sobre el aro exterior del 7204 de proa; bulones M5 A4 + Loctite 243.",
                             "Anillo V VA-30 [ESTIMADO] sobre la KM4 o grasa + tapa: lado seco."]))

    # ---------------- soporte de rodamientos (zapatas y alojamiento)
    b3 = _mod("P1-DRV-03_bearing_bracket")
    g = b3.geom(p)
    x0, x1 = p.brg_bracket_x0, p.brg_bracket_x1
    y_lo = -p.drv_pad_y[1]
    w = x1 - x0
    h = 2 * p.drv_pad_y[1]
    holes = [(xh - x0, yh - y_lo, p.drv_bracket_hole, "espárrago M8 en RANURA de 9 abierta a popa (fondo R4,5 en el de proa)") for xh, yh in p.brg_bracket_holes]
    holes += [(xd - x0, yd - y_lo, p.drv_dowel_d, f"Ø6 H7 pasante, escariar EN MONTAJE junto con la placa base (ISO 8735 Ø6 × {p.drv_dowel_L:g} A4)")
              for xd, yd in p.drv_dowels]
    out.append(plate("P1-DRV-03", "bearing_bracket", "Al 6082-T651 (soldado TIG o de bloque)", w, h, p.drv_bracket_base_t, holes, notes=[
        f"Vista en planta de las zapatas (BOTE): x desde {x0:.1f} (marco BOTE), y desde {y_lo:.1f}. Mejillas 12 mm en |y| = {p.drv_cheek_y[0]:g}–{p.drv_cheek_y[1]:g}.",
        f"Alojamiento Ø{p.drv_bearing['D']:g} H7 × {2 * p.drv_bearing['B']:g} para 2 × {p.drv_bearing['name']} + resalte {p.drv_brg_shoulder_t:g} (paso Ø{p.drv_brg_shoulder_hole:g}: > d1 del aro interior, < D1 del exterior); eje a 5° (sube a proa), "
        f"centro en S = {(p.drv_S_brgA + p.drv_S_brgB) / 2:.1f} mm (z = {p.z_if + (p.drv_S_brgA + p.drv_S_brgB) / 2 * math.sin(math.radians(p.alpha)):.1f}).",
        f"Tablero 12 mm a z = {g['zd0']:.1f}–{g['zd1']:.1f}; 4 × M5 roscados en la cara delantera en BC{p.drv_cover_bc:g}.",
        "Mecanizar el Ø47 DESPUÉS de soldar, en una sola atada con la cara delantera (perpendicularidad ≤ 0,02).",
        f"Zapatas: una ranura de {p.drv_bracket_hole:g} mm por lado, ABIERTA HACIA POPA desde x = {x0:.1f} hasta el espárrago de proa (toma los 2 espárragos).",
        f"Fijación: {p.drv_stud}; {p.drv_nut_torque_Nm:g} N·m con Tef-Gel (K {p.drv_nut_K:g} → F_v {p.drv_nut_Fpre_N:.0f} N, structural).",
        f"Montaje: tuercas sacadas, apoyar el pórtico {p.drv_brg_travel:.0f} mm más a proa (a lo largo del eje) y deslizarlo a popa sobre el eje; alinear con el PROPIO EJE libre en el buje del estator (galgas); apretar.",
        f"Pasadores: 2 × ISO 8735 Ø6 × {p.drv_dowel_L:g} A4 (rosca interior M4, extraíbles) por zapata en |y| = {p.drv_dowel_y:g}, x = " + ", ".join(f"{x:.1f}" for x in sorted({d[0] for d in p.drv_dowels}))
        + f" (BOTE): pasantes en la zapata y CIEGOS {p.drv_dowel_plate_depth:g} mm en la placa base (taladro con TOPE: quedan {p.base_top_z - p.drv_dowel_plate_depth:g} mm de fondo mojado)."]))

    # ---------------- soporte del motor (placa)
    m2 = _mod("P1-MOT-02_motor_mount")
    gm = m2.geom(p)
    mm = p.mot
    hw = p.mot_foot_y[1]
    top = p.motor_d / 2 + 10.0
    ca = math.cos(math.radians(p.alpha))
    zc = (z_axis_s(p, p.S_motor0) - gm["zf0"]) / ca            # eje sobre el borde inferior, medido en la placa
    ph = zc + top
    mholes = [(hw, zc, p.mot_hole_d, "paso del acople")]
    for kk in range(mm["mount_n"]):
        a_ = math.radians(45 + 360 / mm["mount_n"] * kk)
        mholes.append((hw + mm["mount_pcd"] / 2 * math.cos(a_), zc + mm["mount_pcd"] / 2 * math.sin(a_),
                       mm["mount_bolt"] + p.bolt_clr, f"M{mm['mount_bolt']} A4 a la cara del motor [ESTIMADO: medir PCD]"))
    out.append(plate("P1-MOT-02", "motor_mount", "Al 6082-T651 (placa + pies + cartelas soldados)", 2 * hw, ph, p.mot_plate_t, mholes, notes=[
        f"Placa ⟂ al eje (5°); borde inferior sobre el piso z = {gm['zf0']:.0f}. Pies {p.mot_foot_l:g} × {p.mot_foot_y[1] - p.mot_foot_y[0]:g} × {p.mot_foot_t:g} hacia proa en |y| = {p.mot_foot_y[0]:.0f}–{p.mot_foot_y[1]:.0f}.",
        "Agujeros de los pies: 4 × Ø9 (M8 A4 a varengas/largueros a través del piso): " +
        ", ".join(f"({x:.0f}, {y:.0f})" for x, y in gm["holes"]) + " (x, y BOTE).",
        "Antes de agujerear la placa: MEDIR el patrón de agujeros y el centrador del motor recibido (MTI120116 no publica plano).",
        "Sin empuje: dejar la luz 's' del Rotex (2 mm) con el motor abulonado; verificar alineación < 0,2 mm / 0,5° con reloj."]))
    return out
