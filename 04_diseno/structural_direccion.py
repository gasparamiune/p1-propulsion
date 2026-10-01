"""structural_direccion.py — cálculo a mano de DIRECCIÓN, REVERSA y MANDOS (P1-STE-*, P1-REV-*, P1-CTL-*).

Cargas (se toma el MAYOR entre sizing y research/R12 §7, como pidió el principal):
  F_s  = STE_F_design  = máx(sizing F_steer_side_N, 364 N [R12 §7.4: 7,2 kW, δ 30°])     desvío del chorro
  M_s  = F_s · e,  e = STE_e_frac · L_steer [ESTIMADO: R12 §7.4, 0,3–0,5 L]              momento de dirección
  F_b  = REV_F_design  = máx(sizing F_bucket_N, 1408 N [R12 §7.5: 7,2 kW, k_r = 1])      bucket (corta duración)
  F_bn = sizing F_bucket_N (reversa con límite de potencia del controlador)              bucket (fatiga, ~1e5 ciclos)
  M_h  = F · Z_bucket_pivot · 1,10 (el chorro pega a la altura del eje; +10 % por la componente vertical
         de la salida hacia abajo) → R12 da 53–85 N·m con brazo de 60 mm; acá el brazo es 81,8 mm.
Metales: FS ≥ 2 sobre fluencia (corta) o sobre el límite de fatiga (ciclos). PETG: admisibles de R05.
"""
from __future__ import annotations

import math

# --- admisibles de metales [MPa] ---
AL6061 = 240.0        # [ESTIMADO: EN 755-2, 6061-T6 Rp0,2 ≥ 240]
AL6061_FAT = 90.0     # [ESTIMADO: 6061-T6 sin muesca, R = −1, ~1e7 ciclos (≈ 96 MPa, Aluminum Design Manual)]
AL5083 = 125.0        # [ESTIMADO: EN 485-2, 5083-O/H111 Rp0,2 ≥ 125 (= ZAT de soldadura)]
AL5083_WLCF = 68.0    # [CALCULADO: detalle soldado FAT 25 MPa a 2e6 (EN 1999-1-3) con m = 3 → 1e5 ciclos]
SS316 = 205.0         # [ESTIMADO: inputs.yaml shaft.sy_mpa, 316 recocido]
SS316_CD = 310.0      # [ESTIMADO: EN 10088-3 1.4401+C barra estirada ≤ Ø16 — pernos de pivote; pedir certificado]
SS316_FAT = 180.0     # [ESTIMADO: inputs.yaml shaft.se_mpa]
A4_70 = 450.0         # [VERIFICADO: ISO 3506-1, A4-70 Rp0,2 = 450 MPa]
POM_STAT = 20.0       # [ESTIMADO: POM-C, presión admisible estática en buje ~20 MPa]
POM_DYN = 10.0        # [ESTIMADO: POM-C, presión admisible con oscilación lenta]


def vm(s, t):
    return math.sqrt(s ** 2 + 3 * t ** 2)


def z_round(d):
    return math.pi * d ** 3 / 32


def link_force(p, Ms):
    """Fuerza en la biela del M66 = M_s / brazo mínimo (distancia del eje de giro a la línea de la biela)
    en δ ∈ [−δmax, δmax]."""
    a, b = p.STE_stud_x, p.STE_post_y
    arms = []
    for k in range(-5, 6):
        s = math.radians(p.steer_max * k / 5)
        X = a * math.cos(s) - b * math.sin(s)
        Y = a * math.sin(s) + b * math.cos(s)
        dy = Y - p.STE_ram_y
        dx = math.sqrt(p.STE_link_L ** 2 - dy ** 2)
        ux, uy = dx / p.STE_link_L, dy / p.STE_link_L          # dirección de la biela (barra → rótula)
        arms.append(abs(X * uy - Y * ux))
    return Ms / min(arms), min(arms)


def cup_section(p, n=60):
    """I_z de la sección de la cuchara (arco + nervio) para flexión entre los brazos (carga en X)."""
    ax, az, t = p.REV_cup_ax, p.REV_cup_az, p.REV_t
    t0, t1 = math.radians(p.REV_cup_t0), math.radians(p.REV_cup_t1)
    pts = []
    for i in range(n):
        u = t0 + (t1 - t0) * (i + 0.5) / n
        du = abs(t1 - t0) / n
        x = (ax + t / 2) * math.cos(u)
        ds = math.hypot((ax + t / 2) * math.sin(u), (az + t / 2) * math.cos(u)) * du
        pts.append((x, ds * t))
    A = sum(a for _, a in pts)
    xb = sum(x * a for x, a in pts) / A
    I = sum(a * (x - xb) ** 2 for x, a in pts)
    c = max(abs(x - xb) for x, _ in pts) + t / 2
    return I, c


def cases(p, A, row, rows, T3, T2):
    L = p.sz["loads"]
    Fs = p.STE_F_design
    Fs_n = L["F_steer_side_N"]
    e = p.STE_e_frac * p.L_steer
    Ms = Fs * e                               # N·mm
    Ms_n = Fs_n * e
    Fb, Fbn = p.REV_F_design, L["F_bucket_N"]
    Zb = p.Z_bucket_pivot
    Mh = Fb * Zb * 1.10                       # N·mm
    Mh_n = Fbn * Zb * 1.10

    # ------------------------------------------------------------------ boquilla P1-STE-01 (Al 6061-T6)
    ro, rb = p.STE_ro, p.STE_rb
    Zt = math.pi / 32 * ((2 * ro) ** 4 - (2 * rb) ** 4) / (2 * ro)
    row(rows, "P1-STE-01", "Flexión del tubo por el desvío del chorro (fatiga, sizing)",
        f"M = F_s·e = {Fs_n:.0f} N × {e:.0f} mm; Z tubo Ø{2*ro:.1f}/Ø{2*rb:.1f}", Ms_n / Zt, AL6061_FAT, A, T2)
    Fe = Fb / 2
    lev = Zb - 30.0
    Ze = p.STE_ear_y1 - p.STE_ear_y0
    Ze = Ze * 36.0 ** 2 / 6
    row(rows, "P1-STE-01", "Oreja del bucket: flexión en su plano (bucket R12, corta)",
        f"F/2 = {Fe:.0f} N a {lev:.0f} mm de la raíz; sección 8 × 36", Fe * lev / Ze, AL6061, A, T2)
    row(rows, "P1-STE-01", "Oreja del bucket: flexión (reversa sizing, fatiga)",
        f"F/2 = {Fbn/2:.0f} N a {lev:.0f} mm; 8 × 36", (Fbn / 2) * lev / Ze, AL6061_FAT, A, T2)
    Fp = math.hypot(Fb / 2, Fs / 2)
    Zp = (2 * p.STE_ear_rp) * 30.0 ** 2 / 6
    row(rows, "P1-STE-01", "Oreja de pivote (dentro de la de la bomba): flexión de la raíz",
        f"F = √((F_b/2)²+(F_s/2)²) = {Fp:.0f} N a 12 mm; 25 × 30", Fp * 12.0 / Zp, AL6061, A, T2)
    # PETG (descartado) — mismo caso de la oreja del bucket con la admisible de fatiga de ciclos bajos
    s_petg = (Fbn / 2) * lev / (12.0 * 36.0 ** 2 / 6)
    petg_fs = A["lcf"] / s_petg

    # ------------------------------------------------------------------ pernos de pivote P1-STE-02/05 (316)
    d = p.steer_pin_d
    Zp = p.Z_steer_lug + p.STE_lug_t / 2           # altura de la reacción en cada pivote
    F_top = math.hypot(Fb * (Zp + Zb) / (2 * Zp), Fs / 2)      # el bucket empuja a Z_bucket_pivot (> 0)
    F_bot = math.hypot(Fb * abs(Zp - Zb) / (2 * Zp), Fs / 2)
    Lsp = p.STE_lug_t + 2 * p.STE_gz                # luz entre oreja de la boquilla y mejilla superior
    Mtop = F_top * Lsp / 8                          # biempotrado: rosca M6 + escalón abajo, cabeza apretada arriba
    t_top = 4 / 3 * (F_top / 2) / (math.pi * d ** 2 / 4)
    row(rows, "P1-STE-02", "Hombro Ø8 biempotrado: flexión + corte (bucket R12 + dirección, corta)",
        f"reacción superior {F_top:.0f} N en luz {Lsp:.1f} mm (M = F·L/8); 316 estirado", vm(Mtop / z_round(d), t_top), SS316_CD, A, T2,
        "cabeza apretada sobre la mejilla (agujero Ø8 H7) y escalón sobre la oreja")
    row(rows, "P1-STE-02", "Hombro Ø8: flexión por maniobras (fatiga)",
        f"F_s/2 = {Fs_n/2:.0f} N, M = F·L/8", (Fs_n / 2) * Lsp / 8 / z_round(d), SS316_FAT, A, T2)
    lev_p = p.STE_gz + p.STE_lug_t / 2              # inferior: voladizo hasta el medio de la oreja de la bomba
    row(rows, "P1-STE-05", "Hombro Ø8 en voladizo: flexión + corte (corta)",
        f"reacción inferior {F_bot:.0f} N a {lev_p:.1f} mm", vm(F_bot * lev_p / z_round(d), 4 / 3 * F_bot / (math.pi * d ** 2 / 4)), SS316_CD, A, T2)
    row(rows, "P1-STE-05", "Hombro Ø8 en voladizo: flexión por maniobras (fatiga)",
        f"F_s/2 = {Fs_n/2:.0f} N a {lev_p:.1f} mm", (Fs_n / 2) * lev_p / z_round(d), SS316_FAT, A, T2)
    Fp = F_top
    Mp = Mtop
    row(rows, "P1-STE-02", "Presión en el buje POM de la oreja de la bomba (P1-PMP-11)",
        f"{Fp:.0f} N / (Ø8 × {p.STE_lug_t:.1f})", Fp / (d * p.STE_lug_t), POM_STAT, A, T2)
    wa = math.pi / 4 * (p.STE_wash_od ** 2 - p.STE_wash_id ** 2)
    row(rows, "P1-STE-03", "Arandela POM: empuje axial (peso boquilla + bucket + componente vertical)",
        f"60 N [ESTIMADO] / {wa:.0f} mm²", 60.0 / wa, POM_DYN, A, T2)

    # ------------------------------------------------------------------ yugo P1-STE-04/06/07
    F_l, arm = link_force(p, Ms)
    F_ln, _ = link_force(p, Ms_n)
    z_ball = p.STE_ram_z
    zb = p.STE_zc_top + p.STE_yoke_t
    h = z_ball - zb
    Mpost = F_l * h
    Tpost = F_l * (p.STE_stud_x - p.STE_post_x)
    dpo = p.STE_post_d
    row(rows, "P1-STE-06", "Poste Ø22: flexión + torsión (biela M66, M_s con F_s R12)",
        f"F_biela = M_s/{arm:.0f} mm = {F_l:.0f} N a {h:.0f} mm de la brida", vm(Mpost / z_round(dpo), Tpost / (2 * z_round(dpo))),
        AL6061, A, T2)
    row(rows, "P1-STE-06", "Poste Ø22: flexión (fatiga, sizing)",
        f"F_biela = {F_ln:.0f} N", F_ln * h / z_round(dpo), AL6061_FAT, A, T2)
    Fbolt = 4 * Mpost / (4 * 32.0)
    row(rows, "P1-STE-06", "Brida del poste: 4 × M8 A4-70 en Ø32 (tracción)",
        f"F = 4M/(n·BC) = {Fbolt:.0f} N; As 36,6 mm²", Fbolt / 36.6, A4_70, A, T2)
    # brida del yugo: torsión de la banda (X' 6–30 = 24 mm × 20 mm) + flexión por la fuerza de la biela
    a_, b_ = 24.0, p.STE_yoke_t
    lo, sh = max(a_, b_), min(a_, b_)
    alpha = 0.208 + (0.231 - 0.208) * min(max((lo / sh - 1.0) / 0.5, 0.0), 1.0)   # tabla de Roark (1,0 → 1,5)
    tau = Mpost / (alpha * lo * sh ** 2)
    Lb = abs(p.STE_post_y) - p.STE_riser_y
    sig = F_l * Lb / (b_ * a_ ** 2 / 6)
    row(rows, "P1-STE-04", "Banda de la brida: torsión (momento del poste) + flexión",
        f"T = {Mpost/1000:.1f} N·m en 24 × {b_:.0f} (α = {alpha:.3f}); F_biela × {Lb:.0f} mm", vm(sig, tau), AL5083, A, T2)
    Fr = Mpost / (38.0 - 19.0) / 2
    row(rows, "P1-STE-04", "4 × M8 A4-70 a la torre: tracción por el momento del poste",
        f"F = M/(19 mm)/2 = {Fr:.0f} N por bulón", Fr / 36.6, A4_70, A, T2)
    Ma = F_l * 12.0
    # topes de dirección P1-STE-08: timón forzado contra el tope (2 × fuerza de la biela)
    F_st = 2 * F_l
    Rp = math.hypot(p.STE_post_x, p.STE_post_y)
    row(rows, "P1-STE-08", "Placa de topes 8 mm: flexión en su plano (timón forzado)",
        f"F = 2·F_biela = {F_st:.0f} N a 90 mm del ala; sección 32 × 8", F_st * 90.0 / (8 * 32 ** 2 / 6), AL5083, A, T2)
    row(rows, "P1-STE-06", "Poste contra el tope: flexión (timón forzado)",
        f"F = {F_st:.0f} N a {p.STE_stop_z[1] - zb:.0f} mm de la brida", F_st * (p.STE_stop_z[1] - zb) / z_round(dpo), AL6061, A, T2)
    row(rows, "P1-STE-08", "2 × M6 A4-70 del ala al espejo (tracción por el momento)",
        f"M = F × 40 mm / 30 mm entre bulón y borde", F_st * 40.0 / 30.0 / 20.1, A4_70, A, T2)
    row(rows, "P1-STE-07", "Brazo 10 mm: flexión por la altura de la rótula + tracción",
        f"F_biela {F_l:.0f} N; M = F × 12 mm en 24 × 10", Ma / (24 * 10 ** 2 / 6) + F_l / (24 * 10), AL5083, A, T2)

    # ------------------------------------------------------------------ bucket P1-REV-01 (Al 5083 4 mm)
    pdyn = L["p_nozzle_dyn_Pa"] / 1e6
    span = p.REV_y_in                         # del nervio central al brazo
    s_strip = pdyn * span ** 2 / 12 * 6 / p.REV_t ** 2
    row(rows, "P1-REV-01", "Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta)",
        f"p = {pdyn*1000:.0f} kPa, luz {span:.1f} mm (nervio central), t = {p.REV_t:.0f}", s_strip, AL5083, A, T2)
    row(rows, "P1-REV-01", "Chapa de la cuchara: franja (fatiga de soldadura, 1e5)",
        f"ídem", s_strip, AL5083_WLCF, A, T2)
    I, c = cup_section(p)
    Mc = Fb * (2 * p.REV_y_in) / 8
    row(rows, "P1-REV-01", "Cuchara como viga entre brazos (bucket R12, corta)",
        f"M = F·L/8, L = {2*p.REV_y_in:.0f}; I_arco = {I/1e3:.0f}e3 mm⁴", Mc * c / I, AL5083, A, T2)
    Xc = p.STE_X_exit + p.REV_cup_dx
    la = math.hypot(Xc - p.X_bucket_pivot, Zb)
    Zarm = p.REV_t * 60.0 ** 2 / 6
    row(rows, "P1-REV-01", "Brazo lateral: flexión (bucket R12, corta)",
        f"F/2 = {Fb/2:.0f} N a {la:.0f} mm; sección 4 × 60", (Fb / 2) * la / Zarm, AL5083, A, T2)
    row(rows, "P1-REV-01", "Brazo lateral: flexión (reversa sizing, fatiga de soldadura)",
        f"F/2 = {Fbn/2:.0f} N", (Fbn / 2) * la / Zarm, AL5083_WLCF, A, T2)
    Fl = Mh / p.REV_lock_r
    Fl_n = Mh_n / p.REV_lock_r
    row(rows, "P1-REV-01", "Agujero de traba: aplastamiento del brazo (émbolo Ø12)",
        f"F = M_h/r = {Mh/1000:.0f} N·m / {p.REV_lock_r:.0f} mm = {Fl:.0f} N", Fl / (p.REV_lock_pin_d * p.REV_t), AL5083, A, T2)
    row(rows, "P1-REV-01", "Pivote: aplastamiento del brazo + refuerzo (buje Ø14 × 8)",
        f"F/2 = {Fb/2:.0f} N", (Fb / 2) / (p.REV_bush_od * p.REV_bush_L), AL5083, A, T2)

    # ------------------------------------------------------------------ pernos, bujes, émbolo
    lev_b = (p.REV_y_in - p.STE_ear_y1) + p.REV_bush_L / 2
    Mb = (Fb / 2) * lev_b
    row(rows, "P1-REV-02", "Perno con hombro Ø10: flexión + corte (bucket R12, corta)",
        f"F/2 = {Fb/2:.0f} N a {lev_b:.1f} mm", vm(Mb / z_round(p.REV_pin_d), 4 / 3 * (Fb / 2) / (math.pi * p.REV_pin_d ** 2 / 4)),
        SS316, A, T2)
    row(rows, "P1-REV-02", "Perno con hombro Ø10: flexión (fatiga)",
        f"F/2 = {Fbn/2:.0f} N", (Fbn / 2) * lev_b / z_round(p.REV_pin_d), SS316_FAT, A, T2)
    row(rows, "P1-REV-03", "Buje POM Ø10/Ø14 × 8: presión (bucket R12, corta)",
        f"{Fb/2:.0f} N / (10 × 8)", (Fb / 2) / (p.REV_pin_d * p.REV_bush_L), POM_STAT, A, T2)
    row(rows, "P1-REV-03", "Buje POM: presión (reversa sizing, oscilación)",
        f"{Fbn/2:.0f} N / (10 × 8)", (Fbn / 2) / (p.REV_pin_d * p.REV_bush_L), POM_DYN, A, T2)
    dl = p.REV_lock_pin_d
    lev_l = (p.REV_y_in - p.STE_ear_y1) + p.REV_t / 2
    row(rows, "P1-REV-04", "Perno del émbolo Ø12: flexión + corte (M_h con bucket R12)",
        f"F = {Fl:.0f} N a {lev_l:.1f} mm; 316", vm(Fl * lev_l / z_round(dl), 4 / 3 * Fl / (math.pi * dl ** 2 / 4)), SS316, A, T2)
    row(rows, "P1-REV-04", "Perno del émbolo: flexión (reversa sizing, fatiga)",
        f"F = {Fl_n:.0f} N", Fl_n * lev_l / z_round(dl), SS316_FAT, A, T2)
    F_cab = p.CTL_hand_F * 125.0 / 46.0      # palanca forzada contra el tope: 100 N × 125 mm / manivela 46
    row(rows, "P1-REV-06", "Tornillo con hombro Ø8 de la varilla: flexión (palanca forzada)",
        f"F = 100 N × 125/46 = {F_cab:.0f} N a 6 mm", F_cab * 6.0 / z_round(p.REV_stud_d), SS316, A, T2)
    row(rows, "P1-REV-09", "Soporte del Bowden 4 mm: placa de tope en voladizo",
        "tiro 60 N [ESTIMADO] a 34 mm; sección 16 × 4", 60.0 * 34.0 / (16 * 4 ** 2 / 6), AL5083, A, T2)
    row(rows, "P1-CTL-14", "Gatillo 6 mm: flexión por el apriete (100 N a 20 mm del pivote)",
        "sección 10 × 6", 100.0 * 20.0 / (6 * 10 ** 2 / 6), AL6061, A, T2)
    row(rows, "P1-REV-05", "Soporte del Mach5: placa lateral en voladizo (palanca forzada)",
        f"{F_cab:.0f} N a 48 mm; 6 × 124", F_cab * 48.0 / (6 * 124 ** 2 / 6), AL5083, A, T2)

    # ------------------------------------------------------------------ mandos (consola y espejo)
    Fh = p.CTL_hand_F
    Lv = p.CTL_lever_L
    row(rows, "P1-CTL-09", "Palanca del acelerador: flexión en el cubo (100 N en el pomo)",
        f"M = 100 N × {Lv-30:.0f} mm; barra 16 × 8", Fh * (Lv - 30) / (8 * 16 ** 2 / 6), AL6061, A, T2)
    row(rows, "P1-CTL-10", "Palanca del bucket: flexión en el escalón (100 N en el pomo)",
        f"M = 100 N × 125 mm; 16 × 8", Fh * 125.0 / (8 * 16 ** 2 / 6), AL6061, A, T2)
    T_sh = Fh * Lv
    row(rows, "P1-CTL-11", "Eje Ø12: torsión (100 N en el pomo del acelerador)",
        f"T = {T_sh/1000:.0f} N·m", 16 * T_sh / (math.pi * 12 ** 3) * math.sqrt(3), SS316, A, T2)
    row(rows, "P1-CTL-11", "Pasador Ø4 A4 palanca–eje: doble corte",
        f"F = T/d = {T_sh/12:.0f} N", (T_sh / 12) / (2 * math.pi * 2 ** 2) * math.sqrt(3), A4_70, A, T2)
    F_il = Fh * 125.0 / p.CTL_ilock_r
    row(rows, "P1-CTL-12", "Perno de enclavamiento Ø6: corte (palanca forzada contra el enclavamiento)",
        f"F = 100 N × 125 / {p.CTL_ilock_r:.0f} = {F_il:.0f} N", 4 / 3 * F_il / (math.pi * 9) * math.sqrt(3), SS316, A, T2)
    row(rows, "P1-CTL-08", "Placa central: aplastamiento del perno de enclavamiento (6 mm)",
        f"{F_il:.0f} N / (6 × 6)", F_il / 36.0, AL5083, A, T2)
    row(rows, "P1-CTL-08", "Placa central: flexión bajo el eje (100 N en el pomo)",
        f"M = 100 N × {Lv+40:.0f} mm; sección 6 × 56", Fh * (Lv + 40) / (6 * 56 ** 2 / 6), AL5083, A, T2)
    # PETG
    row(rows, "P1-CTL-02", "Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)",
        "franja 50 × 6 apoyada, luz 50: M = F·L/4", 150 * 50 / 4 / (50 * 6 ** 2 / 6), "short", A, T3)
    tf = 10.0      # espesor de la cara inclinada (P1-CTL-03 TF)
    row(rows, "P1-CTL-03", "Cara PETG 10 mm: tirón del cordón 150 N [SUPUESTO] (corta, cruza capas)",
        "franja 50 × 10 empotrada, luz 76: M = F·L/8; ÷ f_Z (cara inclinada 32°)", 150 * 76 / 8 / (50 * tf ** 2 / 6) / A["fz"], "short", A, T3)
    row(rows, "P1-CTL-03", "Cara PETG 10 mm: golpe sobre la seta 200 N [SUPUESTO] (corta, cruza capas)",
        "ídem", 200 * 76 / 8 / (50 * tf ** 2 / 6) / A["fz"], "short", A, T3)
    sig_tp = 3 * F_l / (2 * math.pi * 6 ** 2) * (1.3 * math.log(60 / 10) + 1)
    row(rows, "P1-CTL-01", "Placa de refuerzo 6 mm: carga del pasamuros del M66",
        f"placa circular empotrada R 60, carga {F_l:.0f} N en r 10", sig_tp, AL5083, A, T2)
    row(rows, "P1-CTL-04", "Pasamuros M66: cuerpo Ø20/Ø9,6 a tracción + flexión",
        f"{F_l:.0f} N; momento por 20 mm de voladizo", F_l / (math.pi / 4 * (20 ** 2 - 9.6 ** 2)) +
        F_l * 20 / (math.pi / 32 * (20 ** 4 - 9.6 ** 4) / 20), SS316, A, T2)

    return {
        "F_steer_N": Fs, "F_steer_sizing_N": Fs_n, "e_mm": e, "M_steer_Nm": Ms / 1000,
        "F_link_M66_N": round(F_l, 1), "link_arm_min_mm": round(arm, 1),
        "F_bucket_N": Fb, "F_bucket_sizing_N": Fbn, "M_hinge_Nm": round(Mh / 1000, 1),
        "F_lock_pin_N": round(Fl, 0), "F_pivot_pin_top_N": round(F_top, 0), "F_pivot_pin_bot_N": round(F_bot, 0),
        "F_stop_N": round(F_st, 0),
        "PETG_boquilla": {"caso": "oreja del bucket 12 mm, reversa sizing, admisible lcf",
                          "sigma_MPa": round(s_petg, 2), "FS": round(petg_fs, 2),
                          "conclusion": "FS < 3 → boquilla de Al 6061-T6 (además el perno Ø8 en PETG: aplastamiento)"},
    }
