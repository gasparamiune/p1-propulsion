"""params_bomba.py — parámetros propios del grupo BOMBA (P1-PMP-*), marco JET salvo indicación.

Lo carga params.load() (extend(d)). Todo sale de las claves base (D, D_hub, D_bore, D_noz, tip_clr,
blades, vanes, pump_sections, X_*, interfaces) y de sizing.json; las decisiones propias llevan
etiqueta. Prefijo de todas las claves: "pmp_".

Arquitectura de la bomba (de proa a popa, marco JET, X hacia popa):
  P1-PMP-01 carcasa Al 6061-T6 torneada: brida de la toma (X_duct_out) → brida trasera (X_st1).
            Aloja el anillo de desgaste (prensado contra un escalón) y la camisa del estator.
  P1-PMP-02 anillo de desgaste AISI 316 torneado, Ø int D_bore, X_ring0 … X_ring0+L_ring.
  P1-PMP-03 impulsor AISI 316 (CNC 5 ejes; alternativa SLM 316L + torneado, R11 §6), arrastrado
            por un PASADOR DE CORTE transversal (fusible mecánico, R12 §7.6), sin chavetero.
  P1-PMP-04 anillo retén del pasador (316), tapa los extremos del pasador.
  P1-PMP-05 pasador de corte Al 6061-T6 Ø sz.mech.shear_pin.d_mm.
  P1-PMP-06 estator Al 6061-T6 (CNC 5 ejes) con camisa, 7 álabes, cubo con buje de agua y cono.
  P1-PMP-07 buje de agua Ø20 POM-C/Vesconite (2.º apoyo del eje, lubricado por agua).
  P1-PMP-08 tobera fija Al 6061-T6: contracción a D_noz, salida en X_noz1, alojamiento esférico
            de la boquilla, resalte del O-ring del espejo y orejas de pivote (±Z_steer_lug).
  P1-PMP-09 placa de espejo Al 5083 con cuello coaxial (sello radial O-ring sobre la tobera).
  P1-PMP-10 junta de espejo NBR 2 mm.
"""
from __future__ import annotations

import math


def _deg(x):
    return math.degrees(x)


def _rad(x):
    return math.radians(x)


def free_vortex_model(d):
    """Triángulos de velocidad en cualquier radio, consistentes con sizing.json (torbellino libre:
    c_m uniforme, r·c_u2 = cte) o, si sizing marca que el cubo no lo admite, torbellino limitado
    en el cubo (c_u2 recortado para w2/w1 ≥ 0,70 y mezclado linealmente hasta el radio medio)."""
    S = d["pump_sections"]
    rh, rm, rt = S["cubo"]["r_mm"], S["medio"]["r_mm"], S["punta"]["r_mm"]
    cm = S["cubo"]["cm"]
    omega = S["punta"]["u"] / (rt / 1000.0)            # rad/s
    K = S["cubo"]["cu2"] * rh                          # r·c_u2 (m/s·mm)
    free_ok = bool(d["sz"]["pump"].get("hub_free_vortex_ok", True))

    def cu2_of(r):
        cu = K / r
        if free_ok:
            return cu
        # torbellino limitado: w2/w1 ≥ 0,70 en el cubo [ESTIMADO: límite de de Haller, R12 §2.3]
        u = omega * r / 1000.0
        w1 = math.hypot(cm, u)
        cu_max = u - math.sqrt(max((0.70 * w1) ** 2 - cm ** 2, 0.0))
        f = min(max((r - rh) / (rm - rh), 0.0), 1.0)
        return min(cu, cu_max) * (1 - f) + cu * f

    def tri(r):
        u = omega * r / 1000.0
        cu2 = cu2_of(r)
        b1 = _deg(math.atan2(cm, u))
        b2 = _deg(math.atan2(cm, u - cu2))
        a3 = _deg(math.atan2(cm, cu2))
        w1 = math.hypot(cm, u)
        w2 = math.hypot(cm, u - cu2)
        return dict(r=r, u=u, cm=cm, cu2=cu2, beta1=b1, beta2=b2, alpha3=a3, w1=w1, w2=w2,
                    dh=w2 / w1)
    return tri, omega, free_ok


def _interp(r, pts):
    """Interpolación lineal (extrapola con los extremos) de [(r, v), ...]."""
    pts = sorted(pts)
    if r <= pts[0][0]:
        (r0, v0), (r1, v1) = pts[0], pts[1]
    elif r >= pts[-1][0]:
        (r0, v0), (r1, v1) = pts[-2], pts[-1]
    else:
        for (r0, v0), (r1, v1) in zip(pts, pts[1:]):
            if r0 <= r <= r1:
                break
    return v0 + (v1 - v0) * (r - r0) / (r1 - r0)


def extend(d):
    S = d["pump_sections"]
    sz = d["sz"]
    rh, rm, rt = S["cubo"]["r_mm"], S["medio"]["r_mm"], S["punta"]["r_mm"]
    R_bore = d["D_bore"] / 2

    # ------------------------------------------------------------------ materiales (metales)
    d["pmp_mat"] = {
        # [ESTIMADO: valores típicos de norma EN 573/755 y ASM; el certificado del material manda]
        "Al 6061-T6": {"Sy": 240.0, "Su": 290.0, "Se": 96.0},     # Se: 5e8 ciclos (ASM)
        "AISI 316": {"Sy": d["inp"]["shaft"]["sy_mpa"], "Su": d["inp"]["shaft"]["su_mpa"],
                     "Se": d["inp"]["shaft"]["se_mpa"]},          # [inputs.yaml shaft (316)]
        "Al 5083": {"Sy": 125.0, "Su": 275.0, "Se": 110.0},       # 5083-O/H111 [ESTIMADO]
        "A4-70": {"Sy": 450.0},                                   # ISO 3506 A4-70 Rp0,2 [ESTIMADO: norma]
    }
    d["pmp_p_design_Pa"] = max(200e3, 2.0 * sz["loads"]["p_pump_max_Pa"])
    # [R12 §7.2: p_diseño = 0,2 MPa ≈ 1,3 × presión de cierre; prueba hidrostática 0,3 MPa]

    # ------------------------------------------------------------------ anillo de desgaste
    d["pmp_ring_t"] = 5.0                              # pared del anillo 316 [ESTIMADO: tubo torneado, rigidez de prensado]
    d["pmp_D_seat"] = d["D_bore"] + 2 * d["pmp_ring_t"]   # asiento común anillo + camisa del estator
    d["pmp_ring_X1"] = d["X_ring0"] + d["L_ring"]
    d["pmp_ring_fit"] = "H7/p6 + Loctite 648"           # [ESTIMADO: prensado ligero + retenedor anaeróbico]
    d["pmp_ring_pin_d"] = 4.0                            # pasador anti-rotación Ø4 A4 en el escalón [ESTIMADO]
    d["pmp_ring_pin_r"] = (R_bore + d["pmp_D_seat"] / 2) / 2
    d["pmp_ring_pin_ang"] = 90.0                         # arriba (+Z)
    d["pmp_ring_TIR"] = 0.05                             # concentricidad anillo ↔ eje declarada [ESTIMADO: torno, mismo montaje]

    # ------------------------------------------------------------------ carcasa
    d["pmp_h_wall"] = 5.0                               # pared Al 6061-T6 [CALCULADO: ver structural_bomba; ≥ min mecanizado]
    d["pmp_D_barrel"] = d["pmp_D_seat"] + 2 * d["pmp_h_wall"]
    d["pmp_f1_t"] = 12.0                                 # brida de la toma (espesor) [ESTIMADO: M6, rigidez]
    d["pmp_flange_ang0"] = 22.5                          # fase de los 8 agujeros (desde +Y hacia +Z): ninguno en ±Y/±Z [SUPUESTO: coordinar con TOMA]
    d["pmp_f2_od"] = 186.0                               # brida carcasa ↔ tobera [ESTIMADO: libra el fondo ≥ 5 mm]
    d["pmp_f2_bc"] = 170.0
    d["pmp_f2_n"] = 8
    d["pmp_f2_t"] = 12.0
    d["pmp_f2_bolt"] = 6                                 # M6 A4-70 pasantes con tuerca
    # O-ring de cara en la brida de la toma (cs de inputs.geometry)
    cs, sq, fill = d["oring_cs"], d["oring_sq"], d["oring_fill"]
    d["pmp_gl_depth"] = round(cs * (1 - sq), 2)
    d["pmp_gl_width"] = round(math.pi * cs ** 2 / 4 / (fill * d["pmp_gl_depth"]), 2)
    d["pmp_gl_r_in"] = R_bore + 5.0
    # tornillos anti-rotación del estator: 2 × M5 A4 radiales (±Y) a través de la carcasa
    d["pmp_st_screw_X"] = d["X_st0"] + 37.0
    d["pmp_st_screw_d"] = 5
    # PUERTO DE AGUA DE REFRIGERACIÓN (lado de alta presión, aguas abajo del estator, arriba)
    # [pedido del agente principal: para ESC y motor refrigerados por agua (grupo TREN)]
    d["pmp_cool_thread"] = "G1/8"                        # espiga de manguera Ø6–8 G1/8 A4 [ESTIMADO: buscar "Schlauchtülle G1/8 8 mm 1.4404"]
    d["pmp_cool_tap_d"] = 8.8                            # broca de roscar G1/8 (ISO 228) [ESTIMADO: tabla de roscado ISO 228-1 (G1/8 = 28 hilos/pulg), verificar con el macho]
    d["pmp_cool_thread_L"] = 8.0
    d["pmp_cool_bore_d"] = 5.0                           # paso al flujo
    d["pmp_cool_boss_d"] = 22.0
    d["pmp_cool_boss_top"] = d["pmp_D_barrel"] / 2 + 10.0
    d["pmp_cool_port"] = (round(d["X_st1"] - 14.0, 2), 0.0, round(d["pmp_cool_boss_top"], 2))  # (X, Y, Z) JET, cara del saliente
    d["pmp_cool_dir"] = (0.0, 0.0, 1.0)                  # eje del puerto (radial, hacia arriba)
    d["pmp_cool_tap_X"] = d["pmp_cool_port"][0]          # alias que lee params_tren.py

    # ------------------------------------------------------------------ impulsor
    tri, omega, free_ok = free_vortex_model(d)
    d["pmp_omega_rad_s"] = omega
    d["pmp_rpm_design"] = omega * 60 / (2 * math.pi)
    d["pmp_free_vortex"] = free_ok
    d["pmp_rot_sense"] = "antihorario visto desde popa (+X, regla de la mano derecha)"  # [SUPUESTO: coordinar sentido con TREN/ESC]
    d["pmp_inc_deg"] = 3.0                               # incidencia [R12 §2.5: 2–4°]
    d["pmp_imp_sol"] = [(rh, 1.30), (rm, 0.95), (rt, 0.70)]   # [R12 §2.4: 1,2–1,4 / 0,9–1,0 / 0,6–0,8]
    d["pmp_imp_tc"] = [(rh, 0.08), (rm, 0.06), (rt, 0.05)]    # t/c [R12 §2.6: 8–10 % cubo, 4–6 % punta]
    d["pmp_imp_le_X"] = 2.0                              # borde de ataque apilado radial en X = 2
    d["pmp_le_r_frac"] = 0.0                             # (perfil NACA 00xx: radio de BA ≈ 1,1·(t/c)²·c)
    d["pmp_nose_L"] = 14.0                               # nariz elíptica del cubo [ESTIMADO]
    d["pmp_nose_r0"] = 16.0                              # cara de apoyo (arandela + DIN 471 delantero)
    d["pmp_imp_front_X"] = -d["pmp_nose_L"]              # cara delantera del cubo (apoyo del anillo de empuje)
    d["pmp_band_t"] = 3.0                                # anillo retén del pasador (pared)
    d["pmp_band_L"] = 16.0
    d["pmp_land_r"] = d["D_hub"] / 2 - d["pmp_band_t"]
    d["pmp_band_X0"] = d["L_imp"] - d["pmp_band_L"]
    sp = sz["mech"].get("shear_pin", {"d_mm": 3.5, "T_cut_Nm": 33.5, "material": "Al 6061-T6"})
    d["pmp_pin_d"] = sp["d_mm"]
    d["pmp_pin_hole"] = sp["d_mm"] + 0.05
    d["pmp_pin_T_cut"] = sp["T_cut_Nm"]
    d["pmp_pin_X"] = round(d["L_imp"] - d["pmp_band_L"] / 2, 2)   # ← TREN: agujero Ø pmp_pin_hole en el eje, eje Y
    d["pmp_pin_axis"] = "Y"
    d["pmp_pin_len"] = round(2 * d["pmp_land_r"] - 1.0, 1)       # extremos 0,5 mm bajo el asiento del anillo
    d["pmp_band_screw"] = 3                              # 2 × M3 A4 avellanados (±Z) traban el anillo retén
    d["pmp_pocket"] = (15.0, d["pmp_land_r"] - 4.0, 40.0)  # ranura anular aligerante desde popa (r_in, r_out, prof.)
    d["pmp_tip_r"] = d["D"] / 2

    def blade_row(r):
        t = tri(r)
        s = _interp(r, d["pmp_imp_sol"])
        tc = _interp(r, d["pmp_imp_tc"])
        pitch = 2 * math.pi * r / d["blades"]
        c = s * pitch
        bb1 = t["beta1"] + d["pmp_inc_deg"]
        k = 0.26 / math.sqrt(s)                        # Constant: δ = 0,26·θ/√s [R12 tabla 1 #17]
        delta = k * (t["beta2"] - bb1) / (1 - k)
        bb2 = t["beta2"] + delta
        Df = 1 - t["w2"] / t["w1"] + t["cu2"] / (2 * s * t["w1"])   # Lieblein [R12 tabla 1 #18]
        return dict(t, s=s, tc=tc, pitch=pitch, chord=c, tmax=tc * c, bb1=bb1, bb2=bb2, delta=delta,
                    Df=Df, stagger=(bb1 + bb2) / 2)
    d["pmp_blade_row"] = blade_row
    d["pmp_imp_table"] = {k: blade_row(S[k]["r_mm"]) for k in ("cubo", "medio", "punta")}
    # secciones del loft (CAD): se extienden dentro del cubo y por fuera de la punta (se recorta a r = D/2)
    # (r del loft, r de diseño): las secciones extremas copian la de cubo/punta (extrusión radial corta);
    # pocas secciones = loft suave y booleanas rápidas
    d["pmp_imp_loft_r"] = [(rh - 1.5, rh), (rm, rm), (rt, rt), (rt + 2.0, rt)]

    # ------------------------------------------------------------------ estator
    d["pmp_st_shell_X0"] = d["pmp_ring_X1"]              # la camisa apoya contra el anillo de desgaste
    d["pmp_noz_spigot"] = 4.0
    d["pmp_st_shell_X1"] = d["X_st1"] - d["pmp_noz_spigot"]
    d["pmp_st_le_X"] = d["X_st0"] + 1.0
    d["pmp_st_sol"] = [(rh, 1.5), (rm, 1.2), (R_bore, 1.0)]    # [R12 §3.2: 1,0–1,5]
    d["pmp_st_tc"] = [(rh, 0.10), (rm, 0.09), (R_bore, 0.08)]  # Al: robustez a golpes [ESTIMADO]
    d["pmp_st_inc"] = 0.0                                # entrada = stator_inlet_deg (sizing)
    d["pmp_st_dev_max"] = 8.0                            # sobregiro de salida ≤ 8° [R12 §3.2: 3–8°]

    def vane_row(r):
        t = tri(r)
        s = _interp(r, d["pmp_st_sol"])
        tc = _interp(r, d["pmp_st_tc"])
        pitch = 2 * math.pi * r / d["vanes"]
        a1 = t["alpha3"] + d["pmp_st_inc"]
        k = 0.26 / math.sqrt(s)
        dev = min(k * (90.0 - a1) / (1 - k), d["pmp_st_dev_max"])
        return dict(r=r, alpha_in=a1, alpha_out=90.0 + dev, dev=dev, s=s, tc=tc, pitch=pitch,
                    chord=s * pitch, tmax=tc * s * pitch, cu2=t["cu2"], cm=t["cm"])
    d["pmp_vane_row"] = vane_row
    d["pmp_st_table"] = {"cubo": vane_row(rh), "medio": vane_row(rm), "punta": vane_row(R_bore)}
    d["pmp_st_loft_r"] = [(rh - 2.0, rh), (rm, rm), (R_bore, R_bore), (R_bore + 2.0, R_bore)]
    # cono de cola del cubo del estator (dentro de la tobera)
    d["pmp_tail_tip_r"] = 5.0
    d["pmp_tail_hole_d"] = 6.0                           # salida del agua de lubricación del buje
    # buje lubricado por agua (2.º apoyo del eje, pedido por TREN) y extremo de popa del eje
    d["pmp_journal_d"] = d["shaft_d"]                    # el eje Ø20 atraviesa el impulsor hasta el cubo del estator
    d["pmp_shaft_X_aft"] = round(d["X_st0"] + 45.0, 1)  # ← TREN: fin de popa del eje (pedido: ≈ X_st0 + 45)
    d["pmp_shaft_aft_X"] = d["pmp_shaft_X_aft"]          # alias
    d["pmp_bush_L"] = 30.0                               # ← TREN: largo del buje (L/d = 1,5) [ESTIMADO]
    d["pmp_bush_X1"] = d["pmp_shaft_X_aft"] - 3.0        # el eje sobresale 3 mm del buje
    d["pmp_bush_X0"] = d["pmp_bush_X1"] - d["pmp_bush_L"]
    d["pmp_bush_X"] = round(0.5 * (d["pmp_bush_X0"] + d["pmp_bush_X1"]), 2)   # ← TREN: centro del buje
    d["pmp_brg_id"] = d["shaft_d"] + 0.20                # juego diametral en agua 0,2 mm [ESTIMADO: buje polimérico lubricado por agua; confirmar con el fabricante]
    d["pmp_brg_od"] = d["shaft_d"] + 8.0                 # pared 4 mm [ESTIMADO]
    d["pmp_brg_L"] = d["pmp_bush_L"]
    d["pmp_brg_X0"] = d["pmp_bush_X0"]
    d["pmp_brg_grooves"] = (4, 2.5, 1.5)                 # ranuras axiales de agua (n, ancho, prof.) [ESTIMADO]
    d["pmp_brg_material"] = "POM-C torneado (alt. Vesconite Hilube / iglidur para Ø20: buscar 'Vesconite Hilube bush 20 mm', 'iglidur H370 20x28')"
    d["pmp_st_cbore_d"] = d["shaft_d"] + 1.5             # entrada del cubo del estator: libra el eje Ø20 y el anillo DIN 471
    # fijación axial del impulsor: 2 anillos DIN 471-20 en el eje (adelante: empuje; atrás: retén)
    d["pmp_circlip"] = "DIN 471-20 A4 (ranura Ø19 × 1,3) + arandela 316 20×30×1,5"   # [ESTIMADO: norma DIN 471]
    d["pmp_circlip_fwd_X"] = d["pmp_imp_front_X"] - 1.5 - 0.6    # ← TREN: centro de la ranura delantera
    d["pmp_circlip_aft_X"] = d["L_imp"] + 1.5 + 0.6              # ← TREN: centro de la ranura trasera
    d["pmp_st_cavity_d"] = d["shaft_d"] + 2.0

    # ------------------------------------------------------------------ tobera fija
    d["pmp_noz_wall"] = 5.0
    # tramo cilíndrico final [R12 §3.3: 0,3–0,5 D_n]; se acorta (≥ 0,1·D_n) para que el semiángulo
    # del cono no pase de 13,9° con la tobera más chica del optimizador (L_noz es fijo)
    dR = R_bore - d["D_noz"] / 2
    d["pmp_noz_cyl"] = round(max(0.1 * d["D_noz"], min(0.2 * d["D_noz"], d["L_noz"] - dR / math.tan(math.radians(13.9)))), 1)
    d["pmp_noz_cone_X1"] = d["X_noz1"] - d["pmp_noz_cyl"]
    # cono de cola del estator: termina dentro del cono de la tobera (área de paso monótona decreciente)
    d["pmp_tail_L"] = round(0.8 * (d["pmp_noz_cone_X1"] - d["X_st1"]), 1)   # [CALCULADO: ver check del estator]
    d["pmp_noz_half_angle"] = _deg(math.atan((R_bore - d["D_noz"] / 2) / (d["pmp_noz_cone_X1"] - d["X_st1"])))
    d["pmp_noz_f_t"] = 12.0
    # alojamiento esférico para la boquilla direccional (rótula alrededor del pivote)
    dxp = d["X_steer_pivot"] - d["X_noz1"]
    d["pmp_sock_R"] = math.hypot(dxp, d["D_noz"] / 2)   # pasa por el labio de salida (X_noz1, D_noz/2)
    d["pmp_steer_ball_R_max"] = math.floor((d["pmp_sock_R"] - 1.0) * 10) / 10   # → DIRECCIÓN: frente esférico R ≤ esto
    d["pmp_steer_ear_w"] = 24.0                          # ancho (Y) supuesto de las orejas de la boquilla
    d["pmp_steer_ear_r"] = 13.0                          # radio de barrido de las orejas alrededor del perno
    d["pmp_sock_X1"] = d["X_steer_pivot"] - d["pmp_steer_ear_r"]
    d["pmp_steer_free_r"] = round(math.hypot(d["Z_steer_lug"] - 0.5, d["pmp_steer_ear_w"] / 2) + 1.5, 1)
    # resalte (land) del sello del espejo + O-ring radial. Ya NO lleva las orejas (están en la placa de
    # espejo P1-PMP-09): su radio no depende de D_noz y pasa por el agujero del espejo (transom_hole_d fijo).
    d["pmp_land_R"] = 77.0                               # [CALCULADO: ≤ transom_hole_d/2 − 3; pared ≥ 3,2 sobre la zona libre con D_noz máx.]
    d["pmp_land_X0"] = 264.0
    d["pmp_pin_head_clr_r"] = 10.0                       # arandela Ø18 del perno de DIRECCIÓN + 1
    d["pmp_land_X1"] = round(d["X_steer_pivot"] - d["pmp_pin_head_clr_r"], 1)
    # O-ring: dentro de la placa en todo el perímetro (la cara de proa de la placa está más a popa abajo, por α)
    sa, ca = math.sin(math.radians(d["alpha"])), math.cos(math.radians(d["alpha"]))
    d["pmp_tp_front_Xmax"] = (d["x_if"] + 2.0 + d["pmp_land_R"] * sa) / ca   # cara de proa de la placa (junta 2 mm), abajo
    d["pmp_or_X"] = round(0.5 * ((d["pmp_tp_front_Xmax"] + d["pmp_gl_width"] / 2 + 0.3)
                                 + (d["pmp_land_X1"] - 1.0 - d["pmp_gl_width"] / 2)), 1)
    d["pmp_or_depth"] = d["pmp_gl_depth"]
    d["pmp_or_width"] = d["pmp_gl_width"]

    # ------------------------------------------------------------------ placa de espejo (marco BOTE)
    d["pmp_gasket_t"] = 2.0                              # NBR 2 mm + sellador [ESTIMADO]
    d["pmp_tp_t"] = 8.0                                  # Al 5083 8 mm [VERIFICADO: R11 §7 (placa 5083 8 mm, Dold)]
    d["pmp_tp_R"] = d["transom_hole_d"] / 2 + 25.0
    d["pmp_tp_bc_R"] = d["transom_hole_d"] / 2 + 13.0
    d["pmp_tp_bolt"] = 6
    d["pmp_tp_bolt_ang"] = [60.0, 120.0, 10.0, 170.0, -40.0, 220.0]   # ninguno en ±Z (orejas) ni abajo (fondo)
    d["pmp_tp_zmin"] = 0.5                               # recorte inferior sobre la quilla (z BOTE)
    d["pmp_tp_bore_R"] = d["pmp_land_R"] + 0.1           # H8/f7 sobre el resalte; sella el O-ring
    d["pmp_collar_R"] = d["pmp_tp_bore_R"] + 6.0
    d["pmp_collar_X1"] = d["pmp_land_X1"]
    # OREJAS DE PIVOTE (interfaz DIRECCIÓN) — integradas a la PLACA DE ESPEJO (se monta desde popa
    # después de la bomba, así que no limitan el resalte; válido para D_noz 0,58–0,74·D).
    # |Z| ∈ [Z_steer_lug, pmp_lug_z1], ancho pmp_lug_w (Y), extremo redondo R = w/2 en el perno.
    # Las orejas de la boquilla van POR DENTRO (|Z| ≤ Z_steer_lug − 0,5).
    d["pmp_lug_z0"] = d["Z_steer_lug"]
    d["pmp_lug_z1"] = round(d["pmp_collar_R"] + 4.0, 2)  # se une al cuello por encima del resalte
    d["pmp_lug_t"] = round(d["pmp_lug_z1"] - d["pmp_lug_z0"], 2)
    d["pmp_lug_w"] = 24.0
    d["pmp_lug_X0"] = d["pmp_land_X1"] - 12.0            # arranque (sobre el cuello, r ≥ pmp_tp_bore_R)
    d["pmp_lug_X1"] = d["X_steer_pivot"] + d["pmp_lug_w"] / 2
    # buje de pivote POM-C (o iglidur con collar) en cada oreja: evita 316 contra Al (pedido de DIRECCIÓN)
    d["pmp_lug_hole"] = 12.0                             # alojamiento H7 del buje
    d["pmp_lug_bush_od"] = 12.0
    d["pmp_lug_bush_id"] = d["steer_pin_d"] + 0.1        # ← DIRECCIÓN: tornillo con hombro Ø8 e8 gira aquí [ESTIMADO: juego POM en agua]
    d["pmp_lug_bush_L"] = d["pmp_lug_t"]
    d["pmp_lug_bush_material"] = "POM-C torneado (alt. iglidur con collar 8×12; buscar 'iglidur GFM-0812')"
    # → DIRECCIÓN/REVERSA: envolvente fija a popa del espejo que no debe invadir lo que gira con la boquilla
    #   (resalte + cuello hasta X1 con radio R; placa de espejo de radio plate_R alrededor del eje en el espejo)
    d["pmp_fixed_aft_env"] = dict(X1=d["pmp_land_X1"], R=d["pmp_collar_R"], plate_R=d["pmp_tp_R"],
                                  free_r=d["pmp_steer_free_r"], sock_R=d["pmp_sock_R"])
    return d
