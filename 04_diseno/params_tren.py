"""params_tren.py — parámetros del grupo TREN Y ELECTRÓNICA (P1-DRV-*, P1-MOT-*, P1-ELE-*).

Convención de estaciones: S = distancia a lo largo del eje hacia PROA desde la cara de entrada del
impulsor (marco JET: X = −S). Todas las piezas coaxiales se construyen en el marco JET.

Pila axial (de popa a proa), ver extend():
  rosca M16 de la tuerca del impulsor (X_imp1 → X_aft) · asiento del impulsor Ø20 g6 con agujero del
  pasador de corte (X = pmp_pin_X) · anillo DIN 471-20 de empuje delante del impulsor (X ≈ 0) · tramo
  mojado Ø20 por el conducto · anillo DIN 471-20 de respaldo de la cabeza del sello · cabeza rotante
  del sello mecánico (en la cámara mojada de P1-DRV-02) · asiento fijo · linterna de goteo/testigo ·
  collar Ø26 (apoyo de los aros interiores) · 2 × 7204 BEP en O · tuerca KM4 + MB4 · asiento del cubo
  del acople Ø20 con chaveta 6×6 · acople Rotex 24 · eje del motor · motor (cara de brida en S_motor0).

Secuencia de montaje (A-08: cada pieza pasa por los Ø de lo ya montado) — la verifican los checks de
P1-DRV-01:
  1. Banco: deslizar desde la PUNTA DE POPA del eje la caja del sello P1-DRV-02 (con el asiento fijo ya
     prensado) hasta el collar, y después la cabeza rotante hasta su anillo DIN 471 de respaldo.
     Pasan por: rosca M16, asiento del impulsor, ranuras (todo ≤ Ø20) → nunca por el collar Ø26.
  2. Bote: el subconjunto entra desde PROA, punta de popa primero, por el buje del sello de la toma
     (Ø seal_spigot_d), el conducto y el cubo del impulsor (ya puesto en el anillo de desgaste).
     Se centra el espigón de la caja en el buje y se aprietan los 4 × M6.
  3. Soporte de rodamientos P1-DRV-03: baja VERTICAL sobre los 4 espárragos (tornillos ISO 10642 M8 × 35
     A4-70 colocados desde afuera en la placa base de la toma, cabeza enrasada en Sikaflex) pasando el
     agujero Ø47 por la punta de proa del eje (≤ Ø20); arandela + tuerca ISO 4032 A4 a mano. Rodamientos (2 × 7204 BEP en O) prensados a la vez
     en el alojamiento y en el muñón desde proa (pasan por el asiento del acople y la rosca M20×1,
     ambos ≤ Ø20) contra el collar. MB4 + KM4 (precarga), tapa P1-DRV-06, recién ahí se aprietan las
     tuercas M8 (drv_nut_torque_Nm, Tef-Gel) con el alojamiento alineado al buje por un casquillo de
     centrado en la caja del sello (holgura Ø9 sobre M8: ±0,3 mm).
  4. Popa: anillo DIN 471 de empuje, impulsor + pasador de corte, tuerca M16 (grupo BOMBA).
  5. Cubo del acople en el eje (chaveta + prisionero), motor con su cubo y soporte P1-MOT-02.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------------------------------------
# Datos de componentes comprados (research/R11_componentes_jet.md; lo no publicado → [ESTIMADO])
# ---------------------------------------------------------------------------------------------
BEARING = {  # SKF 7204 BEP, montaje en O (inputs.yaml bearings.type)
    "name": "SKF 7204 BEP",
    "d": 20.0, "D": 47.0, "B": 14.0,        # [VERIFICADO: research/R11 §5 (Klium) — 20 × 47 × 14 mm]
    "C_n": 13300.0, "C0_n": 7650.0,         # [VERIFICADO: research/R11 §5 — C = 13,3 kN, C0 = 7,65 kN]
    "r_s": 1.0,                             # [ESTIMADO: chaflán r_s mín. 1,0 mm de la serie 7204 (catálogo SKF, no abierto)]
    "da_min": 25.6,                         # [ESTIMADO: diámetro de apoyo mín. del aro interior 7204 (catálogo SKF, no abierto)]
    "Da_max": 41.4,                         # [ESTIMADO: diámetro de apoyo máx. del aro exterior 7204 (catálogo SKF, no abierto)]
    "mass_g": 110.0,                        # [ESTIMADO: 7204 BEP ≈ 0,11 kg; buscar ficha SKF]
    "price_eur": 31.40,                     # [VERIFICADO: research/R11 §5 — 31,40 € c/u]
}
KM = {  # tuerca de fijación KM4 + arandela MB4 (DIN 981 / DIN 5406)
    "thread": "M20×1", "d": 20.0, "od": 32.0, "b": 7.0, "mb_t": 1.0,   # [ESTIMADO: DIN 981 KM4 Ø32 × 7; MB4 1 mm; buscar ficha SKF KM 4]
    "mb_slot_w": 4.0, "mb_slot_t": 2.5,     # [ESTIMADO: ranura del diente de MB4 en el eje (DIN 5406)]
    "mass_g": 25.0,                         # [ESTIMADO: KM4 + MB4]
}
SEAL = {  # sello mecánico ST-MG1 Ø20 (fuelle elastomérico), caras carbón/SiC
    "name": "ST-MG1 Ø20 carbón/SiC/NBR (tipo MG1, EN 12756)",
    "d": 20.0,
    "head_od": 33.0,                        # [ESTIMADO: MG1 d1 = 20 → Ø cabeza ≈ 32–33 (EN 12756); medir]
    "head_l": 25.0,                         # [ESTIMADO: largo de trabajo de la cabeza; l1N EN 12756 d1 = 20 ≈ 32,5 con el asiento]
    "seat_od": 35.0,                        # [ESTIMADO: Ø del asiento fijo con su copa de NBR (G60); medir]
    "seat_id": 22.0,                        # [ESTIMADO]
    "seat_l": 7.5,                          # [ESTIMADO]
    "p_max_bar": 12.0, "v_max_ms": 10.0,    # [VERIFICADO: research/R11 §5 — ST-MG1: 12 bar, 10 m/s]
    "mass_g": 60.0,                         # [ESTIMADO: research/R11 §9 "< 0,1 kg"]
    "price_eur": 29.0,                      # [VERIFICADO: research/R11 §5 — desde 29 €]
}
CIRCLIP20 = {"s": 1.2, "m": 1.3, "d2": 19.0, "d3_free": 27.0, "F_N_groove_n": 3800.0}
# [ESTIMADO: DIN 471 d1 = 20 — espesor 1,2, ranura 1,3 × Ø19,0, Ø exterior ≈ 27; carga axial admisible
#  de la ranura (arista viva) ≈ 3,8 kN; buscar tabla DIN 471 (Seeger) para confirmar]
COUPLING = {  # KTR Rotex 24 (estrella T-PUR 92/98 ShA)
    "name": "KTR Rotex 24",
    "D": 55.0,                              # [VERIFICADO: research/R11 §5 — Rotex 24 Ø55]
    "T_KN_Nm": 35.0, "T_Kmax_Nm": 70.0,     # [VERIFICADO: research/R11 §5 — 92 ShA: T_KN 35 / T_Kmax 70 N·m]
    "T_KN_98_Nm": 60.0,                     # [VERIFICADO: research/R11 §5 — 98 ShA: 60 N·m]
    "bore_max": 35.0,                       # [VERIFICADO: research/R11 §5 — agujero 0–35]
    "n_max_rpm": 12100.0,                   # [VERIFICADO: research/R11 §5 — 12 100–13 800 rpm]
    "l_hub": 30.0, "E": 18.0, "s": 2.0,     # [ESTIMADO: catálogo KTR Rotex 24 (l1 = l2 = 30, E = 18, s = 2); no abierto]
    "l_hub_shaft": 24.0,                    # [SUPUESTO: el cubo del lado del eje se refrenta a 24 mm para que entre la pila]
    "mass_g": 600.0,                        # [ESTIMADO: research/R11 §9 ≈ 0,6 kg]
    "price_eur": 67.47,                     # [VERIFICADO: research/R11 §5]
}
KEY_6x6 = {"b": 6.0, "h": 6.0, "t1": 3.5, "t2": 2.8}   # [ESTIMADO: DIN 6885 A 6 × 6 para Ø17–22 (t1 eje 3,5, t2 cubo 2,8)]
MOTORS = {  # por clave de inputs.yaml motor.options (cuerpo Ø × largo sale de inputs: size_mm)
    "HPM5000B": {
        "shaft_d": 22.2,                    # [VERIFICADO: research/R11 §1.2 — Kelly 22,3 mm / Monster 7/8" (22,2); MEDIR]
        "shaft_l": 50.0,                    # [ESTIMADO: chavetero de 43 mm (Kelly, R11) → eje ≥ 45; MEDIR]
        "key_w": 5.0,                       # [VERIFICADO: research/R11 §1.2 — Kelly 5 mm (Monster 5/16"); MEDIR]
        "pilot_d": 70.0, "pilot_l": 4.0,    # [ESTIMADO: centrador de la tapa delantera; buscar plano HPM5000B]
        "mount_pcd": 150.0, "mount_n": 4, "mount_bolt": 8,   # [ESTIMADO: 4 × M8 en la tapa del lado del eje; buscar plano HPM5000B]
    },
    "MTI120116": {
        "shaft_d": 15.0, "shaft_l": 30.0,   # [VERIFICADO: research/R11 §1.2 — Ø15 × 30 mm con chavetero]
        "key_w": 5.0,                       # [ESTIMADO]
        "pilot_d": 40.0, "pilot_l": 2.5,    # [ESTIMADO: buscar plano MTI120116]
        "mount_pcd": 80.0, "mount_n": 4, "mount_bolt": 6,    # [ESTIMADO: buscar plano MTI120116]
    },
}
ESC_FALLBACK = {  # si inputs.yaml esc.options.<sel> no trae size_mm
    "CTRL_48_200": [130.0, 68.0, 41.0],     # [VERIFICADO: research/R11 §2.1 — Flipsky 75200 Pro V2.0 130 × 68 × 41]
    "CTRL_72_150": [183.8, 80.2, 43.8],     # [VERIFICADO: research/R11 §2.2 — Flipsky FSESC 110300]
}


def _motor_data(d):
    key = d["sz"]["selection"]["motor"]
    mo = d["inp"]["motor"]["options"][key]
    for k, v in MOTORS.items():
        if key.startswith(k) or k in key:
            v = dict(v)
            if mo.get("shaft_d_mm"):
                v["shaft_d"] = float(mo["shaft_d_mm"])                  # inputs.yaml (con su etiqueta)
            return key, v, True
    md = d["motor_d"]
    return key, {"shaft_d": round(0.11 * md, 1), "shaft_l": 40.0, "key_w": 5.0, "pilot_d": 0.35 * md,
                 "pilot_l": 3.0, "mount_pcd": 0.7 * md, "mount_n": 4, "mount_bolt": 8}, False   # [ESTIMADO: escalado]


def hull_half_width(d, z):
    """Semimanga interior aproximada del casco a la altura z (mm) [ESTIMADO: fondo plano de
    bottom_beam hasta la quilla y costado recto hasta el pantoque (inputs.yaml boat)]."""
    b = d["inp"]["boat"]
    hb, hc, zc = b["bottom_beam_m"] * 500, b["chine_beam_m"] * 500, b["chine_height_m"] * 1000
    t = d["inp"]["boat"]["bottom_thickness_mm"]
    return min(hb + (hc - hb) * max(z, 0) / zc, hc) - t


def extend(d):
    ca = math.cos(math.radians(d["alpha"]))
    sa = math.sin(math.radians(d["alpha"]))
    inp, sz = d["inp"], d["sz"]
    sd = d["shaft_d"]
    d["drv_bearing"], d["drv_km"], d["drv_seal"] = BEARING, KM, SEAL
    d["drv_circlip"], d["drv_coupling"], d["drv_key"] = CIRCLIP20, COUPLING, KEY_6x6
    mkey, mot, known = _motor_data(d)
    d["mot_key"], d["mot"], d["mot_known"] = mkey, mot, known

    # ---------------- popa del eje (interfaz con BOMBA) ----------------
    # BOMBA (params_bomba.py) define el buje de agua del estator: muñón Ø pmp_journal_d de X_shaft_aft a
    # pmp_shaft_aft_X; el impulsor apoya hacia proa contra un tope (anillo DIN 471) en pmp_imp_front_X.
    d["drv_X_aft"] = d.get("pmp_shaft_aft_X", d.get("pmp_shaft_X_aft", d["X_shaft_aft"]))   # extremo de popa (marco JET)
    d["drv_journal_d"] = d.get("pmp_journal_d", d["shaft_d"])          # muñón del buje del estator (f7)
    d["drv_bush"] = ((d["pmp_brg_X0"], d["pmp_brg_X0"] + d["pmp_brg_L"]) if "pmp_brg_X0" in d else None)
    d["drv_imp_front_X"] = d.get("pmp_imp_front_X", 0.0)               # cara de proa del cubo del impulsor
    d["drv_imp_m_kg"] = 1.35                                            # [CALCULADO: CAD de BOMBA P1-PMP-03 = 1,33 kg (manifest) + anillo retén y pasador]
    d["drv_pin_X"] = d.get("pmp_pin_X", d["X_imp1"] / 2)                # agujero del pasador (BOMBA)
    d["drv_pin_d"] = sz["mech"].get("shear_pin", {}).get("d_mm", 3.5)   # [CALCULADO: sizing.json mech.shear_pin]
    d["drv_pin_hole"] = d["drv_pin_d"] + 0.03                           # [SUPUESTO: agujero H8 escariado (pasador h8 deslizante)]
    d["drv_thread_d"] = 16.0                                            # [SUPUESTO: tuerca del impulsor M16 (brief del grupo)]
    d["drv_imp_seat_X0"] = 0.0                                          # asiento del impulsor X ∈ [0, X_imp1]
    d["drv_thrust_groove"] = (d["drv_imp_front_X"] - CIRCLIP20["m"], d["drv_imp_front_X"])   # ranura del anillo de empuje (X0, X1)
    d["drv_aft_groove"] = (d["X_imp1"] + 0.3, d["X_imp1"] + 0.3 + CIRCLIP20["m"])   # anillo de retención a popa (opcional, en la luz rotor–estator)

    # ---------------- sello (estación S_seal = cara del buje de la toma) ----------------
    S0 = d["S_seal"]
    d["drv_spigot_l"] = 6.0                                             # [SUPUESTO: espigón Ø seal_spigot_d f7 de 6 mm dentro del buje H8 — CONFIRMAR profundidad con TOMA]
    d["drv_flange_t"] = 8.0                                             # [SUPUESTO]
    d["drv_flange_od"] = d["seal_bc"] + 2 * 8.0                         # [CALCULADO: BC + 2 × 8 (arandela M6 Ø12 + 2)]
    d["drv_S_head_back"] = S0 - d["drv_spigot_l"] + 0.5                 # respaldo de la cabeza (dentro del espigón)
    d["drv_S_seat_face"] = d["drv_S_head_back"] + SEAL["head_l"]
    d["drv_S_seat_back"] = d["drv_S_seat_face"] + SEAL["seat_l"]
    d["drv_seat_wall"] = 3.5                                            # [SUPUESTO: pared de apoyo del asiento]
    d["drv_lantern_l"] = 7.0                                            # [SUPUESTO: linterna de goteo/testigo con ventanas y drenaje]
    d["drv_S_hsg_front"] = d["drv_S_seat_back"] + d["drv_seat_wall"] + d["drv_lantern_l"]
    d["drv_chamber_d"] = SEAL["head_od"] + 3.0                          # cámara mojada (holgura radial 1,5)
    d["drv_lantern_d"] = 34.0                                           # [SUPUESTO: pared 4 mm]
    d["drv_drain_tap"] = 8.0                                            # [SUPUESTO: G1/8 (Ø8,8 rosca; macho Ø8,0 para el modelo) — espiga para manguera testigo]

    # ---------------- rodamientos y soporte ----------------
    d["drv_gap_hsg_brg"] = 1.0                                          # [SUPUESTO: luz caja del sello ↔ soporte]
    d["drv_brg_shoulder_t"] = 3.0                                       # [SUPUESTO: resalto del alojamiento (apoyo del aro exterior trasero)]
    d["drv_S_brgA"] = d["drv_S_hsg_front"] + d["drv_gap_hsg_brg"] + d["drv_brg_shoulder_t"]   # cara trasera del rodamiento de popa
    d["drv_S_brgB"] = d["drv_S_brgA"] + 2 * BEARING["B"]                # cara delantera del rodamiento de proa
    d["drv_collar_l"] = d["drv_gap_hsg_brg"] + d["drv_brg_shoulder_t"] - 0.5   # collar: de 0,5 mm delante de la caja del sello al aro
    d["drv_collar_d"] = 26.0                                            # [CALCULADO: ≥ da_min 25,6 del 7204 (BEARING, ESTIMADO catálogo SKF); torneado desde barra Ø28]
    
    d["drv_hsg_od"] = BEARING["D"] + 2 * 9.0                            # alojamiento Ø65 [SUPUESTO: pared 9 mm]
    d["drv_cover_t"] = 7.0                                              # [SUPUESTO: tapa anular 7 mm; la KM4 gira dentro de su agujero Ø34 (laberinto 1 mm)]
    d["drv_S_brg_front"] = d["drv_S_brgB"] + max(d["drv_cover_t"], KM["mb_t"] + KM["b"])   # fin de la pila de rodamientos (tapa o tuerca)
    d["drv_cover_bolt"] = 5                                             # [SUPUESTO: 4 × M5 A4 tapa ↔ soporte]
    d["drv_cover_bc"] = BEARING["D"] + 2 * 4.5                          # [CALCULADO: Ø47 + 2 × 4,5]
    # soporte = PÓRTICO sobre el conducto: dos mejillas longitudinales (planos xz) con zapatas sobre la
    # placa base a ambos lados de la abertura (agujeros en |y| = brg_bracket_y) y un tablero horizontal
    # por ENCIMA del eje del que cuelga el alojamiento: nada del soporte baja entre las mejillas.
    d["drv_bracket_base_t"] = 12.0                                      # [SUPUESTO: zapatas 12 mm (Al 6082-T651)]
    d["drv_bracket_web_t"] = 12.0                                       # [SUPUESTO: mejillas 12 mm]
    d["drv_bracket_pad_w"] = 48.0                                       # [SUPUESTO: ancho de zapata (y)]
    by = d.get("brg_bracket_y", 45.0)
    d["drv_cheek_y"] = (by - 24.2, by - 12.2)                           # [SUPUESTO: cara interior a 12 mm del eje del bulón → llave Allen por arriba]
    d["drv_pad_y"] = (by - 24.2, by + 23.8)
    d["drv_deck_t"] = 12.0                                              # [SUPUESTO: tablero 12 mm]
    d["drv_bracket_hole"] = d["brg_bracket_bolt"] + 1.0                 # [SUPUESTO: Ø9 sobre espárrago M8: ±0,5 mm de ajuste para alinear con el buje del sello; luego 2 pasadores Ø6 escariados en montaje]
    # fijación a la placa base (definida por TOMA en P1-INT-02): espárrago = tornillo avellanado desde afuera
    d["drv_stud"] = "ISO 10642 M8 × 35 A4-70 (desde afuera, cabeza enrasada en Sikaflex) + arandela ISO 7089 + tuerca ISO 4032 A4"
    d["drv_stud_L"] = 35.0                                              # [VERIFICADO: interfaz de TOMA (mensaje del grupo principal)]
    d["drv_nut_m"] = 6.8                                                # [ESTIMADO: ISO 4032 M8, m = 6,8]
    d["drv_washer_t"] = 1.6                                             # [ESTIMADO: ISO 7089 M8, 1,6 mm]
    d["drv_nut_socket_d"] = 18.0                                        # [ESTIMADO: vaso de 13 mm, Ø ext ≈ 18]
    d["drv_nut_torque_Nm"] = 15.0                                       # [VERIFICADO: interfaz de TOMA — ~15 N·m con Tef-Gel]
    d["drv_nut_K"] = 0.18                                               # [ESTIMADO: coeficiente de par A4 con Tef-Gel 0,15–0,20]

    # ---------------- acople y motor ----------------
    d["mot_flange_gap"] = 3.5                                           # [SUPUESTO: cara del cubo del motor a 3,5 mm de la cara del motor (1 mm del centrador)]
    d["drv_S_cpl_motor_face"] = d["S_motor0"] - d["mot_flange_gap"]
    d["drv_cpl_L"] = COUPLING["l_hub_shaft"] + COUPLING["E"] + COUPLING["l_hub"]
    d["drv_S_cpl0"] = d["drv_S_cpl_motor_face"] - d["drv_cpl_L"]          # cara de popa del cubo del lado del eje
    d["drv_S_cpl_spider0"] = d["drv_S_cpl0"] + COUPLING["l_hub_shaft"]
    d["drv_S_front"] = d["drv_S_cpl_spider0"] - COUPLING["s"] / 2 - 0.5  # punta de proa del eje (dentro del cubo)
    d["drv_cpl_key_l"] = COUPLING["l_hub_shaft"] - 2.0                  # chavetero del acople [SUPUESTO: todo el cubo menos 2 mm (aplastamiento FS ≥ 2)]
    d["drv_S_thread0"] = d["drv_S_brgB"] + KM["mb_t"]                    # rosca M20×1 desde la cara del rodamiento + MB4
    d["drv_thread_l"] = KM["b"] + 2.0
    d["drv_shaft_L"] = d["drv_X_aft"] + d["drv_S_front"]                # largo total del eje
    d["drv_bar_d"] = 28.0                                               # [SUPUESTO: barra 1.4404 Ø28 (la compra la BOM); R11 §5 verificó Ø20/Ø25 — buscar precio Ø28]

    # ---------------- soporte del motor ----------------
    d["mot_plate_t"] = 10.0                                             # [SUPUESTO: Al 6082-T651 10 mm]
    d["mot_hole_d"] = COUPLING["D"] + 9.0                               # paso del acople por la placa
    d["mot_foot_z"] = d["floor_z"]                                      # pies sobre el piso (interfaz con el casco)
    d["mot_foot_t"] = 10.0
    d["mot_foot_y"] = (0.75 * d["motor_d"] / 2, 0.75 * d["motor_d"] / 2 + 50.0)  # [SUPUESTO: pies hacia proa, a los costados del cuerpo]
    d["mot_foot_l"] = 60.0                                              # largo de los pies (x)
    d["mot_foot_bolt"] = 8
    d["mot_clear_min"] = 10.0                                           # [VERIFICADO: brief — luz motor–fondo ≥ 10 mm]
    # punto más bajo del cuerpo del motor (borde inferior de popa) y luz al fondo interior
    S_m0 = d["S_motor0"]
    z_ax0 = d["z_if"] + S_m0 * sa
    d["mot_bottom_z_min"] = z_ax0 - d["motor_d"] / 2 * ca
    d["mot_axis_z0"] = z_ax0
    d["mot_clear_bottom"] = d["mot_bottom_z_min"] - d["bottom_t"]
    d["mot_floor_clash"] = d["mot_bottom_z_min"] < d["floor_z"]
    d["mot_clear_floor"] = d["mot_bottom_z_min"] - d["floor_z"]
    d["mot_x0"] = d["x_if"] + S_m0 * ca
    d["mot_x1"] = d["x_if"] + d["S_motor1"] * ca

    # ---------------- electrónica: controlador IP65 refrigerado por agua sobre base elevada + capota
    # Decisión: el FSESC 75350 trae caja de agua IP65 (research/R11 §2.1); su calor (sizing thermal
    # P_loss_esc) se va por el agua → no hace falta tapa-disipador. Una caja estanca alrededor no entra en
    # la cama de 210 mm (ESC de 200 mm + prensaestopas + curvas) → base elevada impresa (ELE-01) que lo
    # aleja del agua del piso + capota antisalpicaduras impresa (ELE-02) que lo sujeta.
    sel = sz["selection"]
    eo = inp["esc"]["options"][sel["esc"]]
    esz = eo.get("size_mm") or ESC_FALLBACK.get(sel["esc"], [130.0, 68.0, 41.0])
    d["ele_esc_size"] = tuple(float(x) for x in esz)
    d["ele_esc_water"] = "agua" in str(eo.get("cooling", ""))
    d["ele_esc_mass_kg"] = eo.get("mass_kg", 1.0)
    d["ele_wall"] = 3.2                                                 # [SUPUESTO: = min_wall]
    d["ele_clr"] = 0.6                                                  # [SUPUESTO: holgura ESC ↔ cuna/capota (caja de Al anodizado, tolerancia ±0,3 [ESTIMADO])]
    d["ele_pad_t"] = 3.0                                                # [SUPUESTO: 2 tiras de EPDM celular 3 × 10 mm sobre los bordes largos del ESC]
    d["ele_pad_comp"] = 0.25                                            # [SUPUESTO: compresión 25 %]
    d["ele_pad_p_mpa"] = 0.04                                           # [ESTIMADO: EPDM celular a 25 % ≈ 0,02–0,05 MPa (fichas típicas); buscar ficha del elegido]
    d["ele_pad_w"] = 10.0
    d["ele_raise"] = 60.0                                               # [SUPUESTO: fondo del ESC 60 mm sobre el piso (sobre el agua de cubierta/sentina que pase el piso)]
    d["ele_tray_d"] = 8.0                                               # [SUPUESTO: profundidad de la cuna]
    d["ele_ear"] = 16.0                                                 # orejas de anclaje al piso (4 × M6)
    d["ele_hood_slot"] = (60.0, 36.0)                                   # [ESTIMADO: ranura de cables/mangueras en cada extremo (ancho, alto): 2 × 70 mm² (Ø ext ≈ 15 [ESTIMADO]) + 2 mangueras Ø8]
    L, W, H = d["ele_esc_size"]
    d["ele_out"] = (L + 2 * (d["ele_clr"] + d["ele_wall"]), W + 2 * (d["ele_clr"] + d["ele_wall"]))
    # ubicación: masses.esc (x ≈ 0,9 m) sobre el piso; al costado del motor si se solapan en x
    x_req = inp["masses"]["items"]["esc"]["x_m"] * 1000
    Lo, Wo = d["ele_out"]
    Wtot = Wo + 2 * d["ele_ear"]
    overlap_x = not (x_req + Lo / 2 < d["mot_x0"] - 60.0 or x_req - Lo / 2 > d["mot_x1"] + 10.0)
    y_c = (d["motor_d"] / 2 + 25.0 + Wtot / 2) if overlap_x else 0.0   # [SUPUESTO: 25 mm de luz al motor]
    d["ele_x_req"] = x_req
    d["ele_pos"] = (x_req, y_c, d["floor_z"])                          # BOTE: centro de la base, sobre el piso
    d["ele_hw_avail"] = hull_half_width(d, d["floor_z"] + d["ele_raise"] + H)
    d["ele_y_outer"] = y_c + Wtot / 2

    # ---------------- circuito de refrigeración (bomba → ESC → motor → espejo) ----------------
    d["cool_hose"] = (6.0, 8.0)                                         # [SUPUESTO: manguera Ø6 × Ø8 (pedido del grupo principal), PVC armada o silicona]
    d["cool_out_yz"] = (180.0, 300.0)                                   # [SUPUESTO: testigo en el espejo, a estribor de la tobera, visible desde el puesto]
    d["cool_tap_X"] = d.get("pmp_cool_tap_X", (d["X_st0"] + d["X_st1"]) / 2)   # puerto del grupo BOMBA (si no lo define: centro del estator)


def cooling_runs(p):
    """Tramos de manguera del circuito de refrigeración (marco BOTE) y su largo [CALCULADO: recta × 1,3
    + 0,15 m de reserva, SUPUESTO]. Devuelve [(desde, hasta, (x,y,z)0, (x,y,z)1, largo_m)]."""
    import params as P
    from build123d import Pos
    port = p.raw.get("pmp_cool_port", ((p.X_st0 + p.X_st1) / 2, 0.0, p.D_bore / 2 + 15.0))
    a = P.jet_to_boat(p, *port)
    x, y, z = p.ele_pos
    L, W, H = p.ele_esc_size
    ze = z + p.ele_raise + H / 2
    esc_in, esc_out = (x - L / 2 - 10, y, ze), (x + L / 2 + 10, y, ze)
    r = p.motor_d / 2 + 10
    mot_in = P.jet_to_boat(p, -(p.S_motor1 - 15.0), 0.0, r)
    mot_out = P.jet_to_boat(p, -(p.S_motor0 + 15.0), 0.0, r)
    yo, zo = p.cool_out_yz
    outlet = (p.transom_t + 30.0, yo, zo)
    pts = [("puerto de la bomba (BOMBA)", a), ("entrada caja de agua ESC", esc_in), ("salida caja de agua ESC", esc_out),
           ("entrada camisa del motor", mot_in), ("salida camisa del motor", mot_out), ("pasacasco testigo P1-ELE-03", outlet)]
    runs = []
    for (n0, p0), (n1, p1) in [(pts[0], pts[1]), (pts[2], pts[3]), (pts[4], pts[5])]:
        dd = math.dist(p0, p1) / 1000
        runs.append((n0, n1, p0, p1, round(1.3 * dd + 0.15, 2)))
    return runs


K_JACKETS = 15.0   # [ESTIMADO: pérdidas locales de 2 camisas + espigas + codos, ΣK ≈ 15 (sin datos del fabricante)]
DT_WATER = 10.0    # [SUPUESTO: salto de temperatura del agua de refrigeración 10 K]


def cooling_hydraulics(p):
    """Caudal necesario y caída de presión del circuito vs presión disponible en el puerto [CALCULADO:
    Darcy (laminar 64/Re, turbulento Blasius) + ΣK; presión del puerto ∝ n² desde p_pump_max a n_max]."""
    th = p.sz["thermal"]
    P_loss = th["P_loss_motor_W"] + th["P_loss_esc_W"]
    rho = p.inp["water"]["density_kg_m3"]
    nu = p.inp["water"]["kinematic_viscosity_m2_s"]
    Q = P_loss / (4186.0 * DT_WATER) / rho                 # m³/s
    Di = p.cool_hose[0] / 1000
    A = math.pi * Di ** 2 / 4
    v = Q / A
    Re = v * Di / nu
    f = 64 / Re if Re < 2300 else 0.316 * Re ** -0.25
    Lh = sum(r[4] for r in cooling_runs(p))
    dp = (f * Lh / Di + K_JACKETS) * rho * v ** 2 / 2
    n_leg = p.sz["legal_speed"].get("n_legal_rpm", 2000.0)
    p_avail = p.sz["loads"]["p_pump_max_Pa"] * (n_leg / p.sz["mech"]["n_max_rpm"]) ** 2
    return {"P_loss_W": P_loss, "Q_l_min": Q * 6e4, "v_ms": v, "Re": Re, "L_hose_m": Lh, "dp_Pa": dp,
            "p_avail_legal_Pa": p_avail, "n_legal_rpm": n_leg}
