"""params_direccion.py — parámetros del grupo DIRECCIÓN Y REVERSA + MANDOS (prefijos STE_, REV_, CTL_).

Marcos: las piezas de la boquilla (STE) se modelan en el marco JET con δ = 0 (loc_steer las gira);
las del bucket (REV) en el marco JET con δ = 0 y bucket ARRIBA (loc_bucket las baja
bucket_down_deg alrededor de (X_bucket_pivot, Z_bucket_pivot)). Ojo: en el marco JET el eje +Y
apunta a ESTRIBOR del bote (Rot_z(180°) de loc_jet: y_bote = −Y_jet).

Concepto (ver docstrings de cada pieza):
  - Boquilla de Al 6061-T6 (FS de PETG < 3 en orejas y pernos: ver structural_direccion.py) con cara
    de entrada en el plano del pivote, entrada abocinada y frente esférico centrado en el pivote que
    entra en la rótula de la tobera fija (P1-PMP-08). Orejas ±Z por DENTRO de las de la bomba.
  - Mando de dirección por yugo: brida sobre la torre de la boquilla → poste vertical desplazado
    86 mm a babor del eje → brazo superior con rótula a Z ≈ 257 (por ENCIMA de la flotación
    estática y del barrido del bucket). Cable Ultraflex M66 (R11 §7) con biela de 60 mm.
  - Bucket: cable Ultraflex Mach5 anclado EN la boquilla (bucle libre: sin acople con la dirección).
  - Bucket de Al 5083 4 mm con traba por émbolo indexador en ARRIBA y en ABAJO (la carga del
    chorro no pasa por el cable Mach5); el émbolo se libera con el gatillo de la palanca del bucket.
"""
from __future__ import annotations

import math


def extend(d):
    sz = d["sz"]
    loads = sz["loads"]
    a = math.radians(d["alpha"])
    smax = d["steer_max"]

    # ------------------------------------------------------------------ boquilla (STE)
    r_jet = d["D_noz"] / 2
    d["STE_r_jet"] = r_jet
    d["STE_cone_deg"] = 5.0            # [ESTIMADO: brief CAD — semiángulo de expansión del chorro]
    d["STE_rb"] = d["D_steer_in"] / 2  # Ø de paso de la boquilla (núcleo)
    # Frente esférico centrado en el pivote: debe entrar en el alojamiento esférico de la tobera fija
    # del grupo BOMBA (pmp_steer_ball_R_max, si existe) → R_s; la boca abocinada deja 1,8 mm de pared.
    # Escala con D_noz (rango del optimizador 0,58–0,74·D): la rótula de BOMBA pasa por el labio de la
    # tobera fija (R = √(Δx² + r_chorro²)), así que con δmax = 25° y toberas grandes el labio puede
    # interceptar una franja del chorro a fondo de giro → check de fracción interceptada (≤ 1,5 %).
    d["STE_Rs"] = d.get("pmp_steer_ball_R_max",
                        math.hypot(d["X_steer_pivot"] - d["X_noz1"], r_jet) - 1.0)   # [CALCULADO: interfaz BOMBA (P1-PMP-08)]
    d["STE_wall_face"] = 1.8           # [SUPUESTO: labio de Al 6061 con chaflán]
    d["STE_rf"] = d["STE_Rs"] - d["STE_wall_face"]
    d["STE_ro"] = round(d["STE_rb"] + 5.0, 2)                    # cuerpo (pared 5 mm) desde X' = 22
    d["STE_ro_front"] = round(min(d["STE_Rs"] - 1.0, d["STE_ro"]), 2)   # tramo X' ≤ 16 dentro de la rótula de BOMBA
    d["STE_intercept_max"] = 0.015     # [SUPUESTO: fracción del área del chorro que puede tocar el labio con δmax]
    d["STE_bell_L"] = 12.0             # [SUPUESTO: largo del abocinado]
    d["STE_X_exit"] = d["X_steer_pivot"] + d["L_steer"]   # salida (cara de entrada = plano del pivote)
    # Orejas de la BOMBA (P1-PMP-08): |Z| ∈ [Z_steer_lug, Z_steer_lug + pmp_lug_t], ancho pmp_lug_w,
    # extremo redondo alrededor del perno. Las de la boquilla van POR DENTRO (|Z| < Z_steer_lug): la
    # mejilla exterior que pedía el brief choca con el cuello de la placa de espejo (r 75–81 hasta
    # X = pmp_land_X1) → ver informe. Si el grupo BOMBA no existe, valores supuestos.
    d["STE_lug_t"] = d.get("pmp_lug_t", 10.0)       # [interfaz BOMBA]
    d["STE_lug_w"] = d.get("pmp_lug_w", 24.0)       # [interfaz BOMBA]
    d["STE_lug_r"] = d["STE_lug_w"] / 2
    d["STE_lug_x0"] = d.get("pmp_land_X1", d["X_noz1"] + 25.0) - 14.0
    d["STE_gz"] = 1.5                  # [SUPUESTO: luz axial oreja ↔ oreja (arandela POM 1 mm + 0,5)]
    d["STE_gr"] = 2.0                  # [SUPUESTO: luz radial alrededor de la oreja barrida]
    d["STE_sweep"] = smax + 5.0        # recorte barrido hasta δmax + 5° (topes reales en la biela/timonería)
    zl = d["Z_steer_lug"]
    d["STE_ear_top"] = zl - d["STE_gz"]   # cara superior de la oreja de la boquilla (debajo de la de la bomba)
    d["STE_ear_rp"] = min(d.get("pmp_steer_ear_r", 13.0) - 0.5, 12.5)   # radio de la oreja alrededor del perno
    d["STE_ear_w"] = min(d.get("pmp_steer_ear_w", 24.0), 2 * d["STE_ear_rp"])
    d["STE_free_r"] = d.get("pmp_steer_free_r", 61.1)   # zona libre de la tobera fija (radio)
    d["STE_riser_x"] = (15.0, 42.0)    # torre del yugo detrás del extremo de la oreja de la bomba (X')
    d["STE_riser_bolts"] = [(19.0, -8.0), (19.0, 8.0), (38.0, -8.0), (38.0, 8.0)]   # 4 × M8 A4 (X', Y)
    d["STE_riser_y"] = 14.0
    # mejilla superior por ENCIMA de la oreja de la bomba (ya fuera del cuello de la placa, r > pmp_collar_R):
    # el perno superior trabaja en doble apoyo (oreja de la boquilla abajo + mejilla arriba)
    d["STE_cheek_z0"] = zl + d["STE_lug_t"] + d["STE_gz"]
    d["STE_cheek_t"] = 10.0            # [SUPUESTO]
    d["STE_riser_top"] = round(d["STE_cheek_z0"] + d["STE_cheek_t"], 2)   # cara superior de torre y mejilla
    d["STE_zc_top"] = d["STE_riser_top"]   # apoyo de la brida del yugo
    # pernos de pivote Ø8 (interfaz steer_pin_d): tornillo con hombro 316, hombro Ø8 e8 (modelado Ø7,9)
    # que gira en el agujero Ø8,2 de la oreja de la bomba; rosca M6 a la oreja de la boquilla
    d["STE_pin_d_model"] = d["steer_pin_d"] - 0.1
    d["STE_wash_id"] = d["steer_pin_d"] + 0.4
    d["STE_wash_od"] = 18.0
    d["STE_wash_t"] = 1.0              # arandela de empuje POM-C [SUPUESTO]
    d["STE_head_d"] = 14.0
    d["STE_head_t"] = 3.0              # [CALCULADO: la cabeza no entra en el cuello de la placa (r ≥ pmp_tp_bore_R)]
    d["STE_head_z0"] = d["STE_riser_top"]   # la cabeza apoya sobre la mejilla superior
    d["STE_m6_depth"] = 8.0
    # yugo de dirección
    d["STE_yoke_t"] = 20.0             # brida del yugo sobre la torre (Al 5083 20 mm) [CALCULADO: torsión del poste, structural_direccion]
    # poste: Y_jet (babor del bote) fuera de la cabeza del perno del bucket; X' crece con |Y| para que el
    # poste no avance hacia la placa de espejo con δ = −δmax [CALCULADO]
    _yin = max(48.0, math.ceil(d["STE_ro"] + 0.5)) + 1.5
    d["STE_post_y"] = -round(_yin + 2 * 4.0 + 0.3 + 6.0 + 22.0 + 0.5, 1)
    d["STE_post_x"] = round(33.0 + (abs(d["STE_post_y"]) - 86.0) * math.tan(math.radians(smax)), 1)
    d["STE_post_d"] = 22.0             # [CALCULADO: ver structural_direccion]
    d["STE_post_z1"] = 245.0           # cara superior del brazo [CALCULADO: rótula a Z ≈ 257 → z_bote ≈ 345 > flotación 273]
    d["STE_arm_t"] = 10.0
    d["STE_stud_x"] = d["STE_post_x"] + 33.0   # rótula del brazo superior [CALCULADO: luz de la barra al espejo]
    d["STE_stud_hole"] = 8.4           # rótula angular M8 (DIN 71802) [ESTIMADO: buscar "Winkelgelenk DIN 71802 M8 A4"]
    d["STE_ball_h"] = 12.0             # centro de bola sobre la cara del brazo [ESTIMADO: DIN 71802 M8]
    d["STE_link_L"] = 60.0             # biela cable M66 → brazo [CALCULADO: recorrido simétrico ±29,6 mm]
    d["STE_stop_deg"] = smax + 1.5     # topes mecánicos de dirección (P1-STE-08) [SUPUESTO: 1,5° sobre δmax]
    d["STE_stop_z"] = (222.0, 230.0)   # placa de topes, entre el bucket arriba y el brazo del yugo [CALCULADO]
    d["REV_plunger_stroke"] = 10.0     # [ESTIMADO: carrera del émbolo GN 617-12; buscar ficha]
    d["STE_e_frac"] = 0.5              # [ESTIMADO: research/R12 §7.4 — brazo del momento 0,3–0,5 L]
    d["STE_F_design"] = max(loads["F_steer_side_N"], 364.0)   # [CALCULADO: research/R12 §7.4 — 364 N (7,2 kW, δ 30°); se toma el mayor con sizing]
    # orejas del bucket sobre la boquilla
    d["STE_ear_y1"] = max(48.0, math.ceil(d["STE_ro"] + 0.5))   # oreja del bucket por fuera del cuerpo
    d["STE_ear_y0"] = d["STE_ear_y1"] - 8.0
    d["STE_ear_r"] = 12.0

    # ------------------------------------------------------------------ bucket (REV)
    d["bucket_down_deg"] = 70.0        # [SUPUESTO: pedido del brief, default 70°] (lo lee params.loc_bucket)
    # Auditoría ronda 3 (FEA, resultados_fea.json): con traba solo en el brazo +Y todo M_h pasaba por la cuchara
    # abierta en torsión (FS 0,44). Variante V2 del FEA: traba en LOS DOS brazos + chapa de 6 mm → FS 2,34.
    d["REV_t"] = 6.0                   # Al 5083 6 mm [CALCULADO: FEA V2 (resultados_fea.json), FS ≥ 2]
    d["REV_n_locks"] = 2               # émbolos P1-REV-04, uno por brazo (±Y), liberados juntos por 2 Bowden
    d["REV_release_need"] = d["REV_t"] + 1.5   # recorrido del pomo para liberar el brazo (perno +1 sobre la cara + 0,5 de luz) [CALCULADO]
    d["REV_y_in"] = d["STE_ear_y1"] + 1.5   # cara interior de los brazos (luz 1,5 a la oreja; arandela POM 1 mm)
    d["REV_cup_dx"] = 12.0             # centro de la cuchara a 12 mm de la salida [SUPUESTO]
    d["REV_cup_ax"] = 50.0             # semiejes de la cuchara (abajo): X 50, Z 56 [SUPUESTO: cubre r_chorro + cono]
    rjc = r_jet + 62.0 * math.tan(math.radians(5.0))      # chorro con cono en el fondo de la cuchara
    d["REV_cup_az"] = round(max(54.0, rjc + 7.0, (d["STE_ro"] + 4.0) / math.sin(math.radians(75.0)) + 0.5), 1)   # [CALCULADO]
    d["REV_cup_t0"] = 85.0             # arco de la cuchara (ángulo paramétrico, °): labio superior
    d["REV_cup_t1"] = -105.0           # labio inferior: el agua sale hacia proa y abajo
    d["REV_boss_r"] = 12.0
    d["REV_pin_d"] = 10.0              # perno con hombro Ø10 / M8 (316)
    d["REV_bush_od"] = 14.0
    d["REV_bush_fl_d"] = 20.0
    d["REV_bush_fl_t"] = 1.0
    d["REV_bush_L"] = 2 * d["REV_t"]   # brazo + aro de refuerzo (los dos de REV_t)
    d["REV_head_d"] = 16.0
    d["REV_head_t"] = 6.0
    # biela del Mach5: perno en el brazo +Y a REV_stud_r del pivote, a +35° (arriba) y −35° (abajo):
    # cuerda VERTICAL a popa del pivote → la varilla del Mach5 trabaja vertical, anclada en la boquilla,
    # y nada del mando avanza hacia la tobera fija al girar (pmp_fixed_aft_env)
    d["REV_stud_r"] = 40.0             # [CALCULADO: carrera 2·r·sin35° = 45,9 mm < carrera del Mach5]
    d["REV_stud_up_ang"] = 35.0        # ° desde +X hacia +Z, bucket ARRIBA (marco natural)
    d["REV_stud_d"] = 8.0              # perno con hombro Ø8 / M6 (316)
    d["REV_eye_off"] = 4.0             # buje soldado (Ø16 × 4, M6) entre el brazo y la rótula (la vaina libra el brazo)
    d["REV_eye_w"] = 8.0               # ojo de la varilla (rótula hembra M6) [ESTIMADO: DIN ISO 12240-4 M6; buscar]
    d["REV_sleeve_z0"] = 130.0         # fin de la vaina rígida del Mach5 (sale la varilla) [CALCULADO]
    d["REV_lock_r"] = 45.0             # émbolo indexador a 45 mm del pivote [CALCULADO: FS ≥ 2 del perno Ø12]
    d["REV_lock_ang"] = 10.0           # ° (marco de la boquilla) [CALCULADO: arriba-popa del pivote, libra la varilla del Mach5]
    d["REV_lock_pin_d"] = 12.0         # [ESTIMADO: émbolo indexador A4 M20×1,5 con perno Ø12; buscar "GN 617-12-M20 A4"]
    d["REV_lock_hole_d"] = 12.5
    d["REV_mach5_stroke"] = 76.0       # [ESTIMADO: cable 33C/Mach5 carrera 3" típica; buscar "Ultraflex Mach5 stroke"]
    d["REV_impact"] = 2.0              # [SUPUESTO: R10b H10 — bisagra para ≥ 2 × 760 N]
    d["REV_F_design"] = max(loads["F_bucket_N"], 1408.0)   # [CALCULADO: research/R12 §7.5 — 1408 N (7,2 kW, k_r = 1); se toma el mayor con sizing]
    d["REV_M_hinge_R12"] = 85.0        # [CALCULADO: research/R12 §7.5 — 53–85 N·m con brazo de 60 mm]

    # ------------------------------------------------------------------ mandos (CTL), marco BOTE (mm)
    d["CTL_x_pilot"] = d["inp"]["masses"]["items"]["pilot"]["x_m"] * 1000
    d["CTL_console_x0"] = 1700.0       # [SUPUESTO: consola de Jorge, panel a 0,32 m del CG del piloto — medir]
    d["CTL_console_x1"] = 1950.0
    d["CTL_console_hw"] = 180.0
    d["CTL_console_top"] = 600.0       # [SUPUESTO: tapa de consola a 0,60 m del fondo — medir]
    d["CTL_ply_t"] = 12.0              # [SUPUESTO: contrachapado marino 12 mm]
    d["CTL_wheel_d"] = 320.0           # [VERIFICADO: research/R11 §7 — volante Osculati Ø320]
    d["CTL_wheel_x"] = 1600.0
    d["CTL_wheel_z"] = 470.0
    d["CTL_hand_F"] = 100.0            # [SUPUESTO: brief — fuerza de mano en palancas]
    d["CTL_axis"] = (1830.0, -110.0, 640.0)   # eje de palancas (x, y, z) en el BOTE [SUPUESTO]
    d["CTL_lever_L"] = 150.0           # largo eje → pomo [SUPUESTO]
    d["CTL_thr_fwd"] = 40.0            # recorrido avance [SUPUESTO]
    d["CTL_thr_rev"] = 30.0            # recorrido reversa [SUPUESTO]
    d["CTL_bkt_travel"] = 60.0         # palanca de bucket: 0 (arriba, adelante) → −60° (abajo) [SUPUESTO]
    d["CTL_ilock_r"] = 22.0            # radio de los pernos de enclavamiento
    d["CTL_ilock_d"] = 6.0
    d["CTL_ilock_depth"] = 3.0
    d["CTL_shaft_d"] = 12.0
    d["CTL_magnet"] = (10.0, 3.0)      # [VERIFICADO: 04_diseno/electronica/README §4 — imán NdFeB Ø10×3 diametral]
    d["CTL_hall_gap"] = 2.5            # [ESTIMADO: entrehierro A1324 2–4 mm; ajustar en la calibración T0.5]
    d["CTL_kill_hole"] = 22.0          # [ESTIMADO: buscar ficha Watski 'Dødmands kontakt universal' — agujero de panel]
    d["CTL_estop_hole"] = 22.0         # [ESTIMADO: README electrónica §4 — seta Ø22]
    d["CTL_cord_F"] = 150.0            # [SUPUESTO: tirón del cordón antes de soltar el clip]
    # pasos del espejo (frame BOTE): se calculan en el marco JET y se pasan al BOTE
    def j2b(X, Y, Z):
        x = d["x_if"] - X * math.cos(a) - Z * math.sin(a)
        z = d["z_if"] - X * math.sin(a) + Z * math.cos(a)
        return (x, -Y, z)
    # línea de la barra del M66: Y medio de la rótula en el recorrido, Z del centro de bola
    Xs, Ys = d["STE_stud_x"], d["STE_post_y"]
    ys = [Xs * math.sin(math.radians(s)) + Ys * math.cos(math.radians(s)) for s in (-smax, 0.0, smax)]
    d["STE_ram_y"] = round((min(ys) + max(ys)) / 2, 1)          # [CALCULADO]
    d["STE_ram_z"] = d["STE_post_z1"] + d["STE_ball_h"]
    zt = d["STE_ram_z"]
    Xtr = (d["x_if"] - zt * math.sin(a)) / math.cos(a)       # espejo (x_bote = 0) a esa altura
    d["CTL_m66_pt"] = j2b(Xtr, d["STE_ram_y"], zt)               # (x, y, z) BOTE del paso del M66
    # Mach5 y Bowden de liberación del émbolo: vaina estática por prensaestopas en el espejo, sobre la
    # flotación; bucle libre hasta el anclaje en la boquilla (gira con la dirección: sin acople)
    d["CTL_mach5_pt"] = (0.0, -160.0, 385.0)   # [SUPUESTO: bucle del Mach5 con radio ≥ 150 mm hacia estribor]
    d["CTL_bowden_pt"] = (0.0, -205.0, 385.0)  # [SUPUESTO: Bowden de liberación del émbolo, junto al Mach5]
    d["CTL_gland_m66_bore"] = 9.5      # [ESTIMADO: barra del M66 3/8"; buscar "Ultraflex M66 ram diameter"]
    d["CTL_gland_m5_bore"] = 6.5       # [ESTIMADO: varilla 33C Ø 1/4"; buscar "Ultraflex Mach5 rod diameter"]
    d["CTL_m66_tube_d"] = 22.2         # [ESTIMADO: tubo del M66 7/8"-14 UNF; buscar "Ultraflex M66 dimensions"]
    d["CTL_m66_tube_L"] = 230.0        # [ESTIMADO: idem]
    d["CTL_m5_hub_d"] = 12.7           # [ESTIMADO: cabeza 33C con ranura de grapa; buscar ficha Mach5]
    d["CTL_m5_sleeve_L"] = 120.0       # [ESTIMADO: idem]
