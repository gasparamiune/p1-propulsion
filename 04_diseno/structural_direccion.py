"""structural_direccion.py — cálculo a mano de DIRECCIÓN, REVERSA y MANDOS (P1-STE-*, P1-REV-*, P1-CTL-*).

Cargas (se toma el MAYOR entre sizing y research/R12 §7, como pidió el principal):
  F_s  = STE_F_design  = máx(sizing F_steer_side_N, 364 N [R12 §7.4: 7,2 kW, δ 30°])     desvío del chorro
  M_s  = F_s · e,  e = STE_e_frac · L_steer [ESTIMADO: R12 §7.4, 0,3–0,5 L]              momento de dirección
  F_b  = REV_F_design  = máx(sizing F_bucket_N, 1408 N [R12 §7.5: 7,2 kW, k_r = 1])      bucket (corta duración)
  F_bn = sizing F_bucket_N (reversa con límite de potencia del controlador)              bucket (fatiga, ~1e5 ciclos)
  M_h, F_z del bucket: balance de cantidad de movimiento con la salida por el labio inferior de la cuchara
         (jet_momentum; auditoría ronda 4). Criterio de las trabas: CADA traba sola lleva M_h completo
         (los agujeros tienen juego: no hay reparto garantizado entre las dos), con R12 (FS ≥ 2) y con la
         reversa de sizing en fatiga.
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
A4_80 = 600.0         # [VERIFICADO: ISO 3506-1, A4-80 Rp0,2 = 600 MPa] (tornillo del pivote del bucket)
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


def _cup_line(p, n=60):
    """Línea media de la cuchara (x, z) para el largo desarrollado."""
    ax, az, t = p.REV_cup_ax + p.REV_t / 2, p.REV_cup_az + p.REV_t / 2, p.REV_t
    t0, t1 = math.radians(p.REV_cup_t0), math.radians(p.REV_cup_t1)
    return [(ax * math.cos(t0 + (t1 - t0) * i / n), az * math.sin(t0 + (t1 - t0) * i / n)) for i in range(n + 1)]


def jet_footprint(p):
    """Radio del chorro con cono (STE_cone_deg) a la altura del fondo de la cuchara."""
    xback = p.STE_X_exit + p.REV_cup_dx + p.REV_cup_ax
    return p.STE_r_jet + (xback - p.STE_X_exit) * math.tan(math.radians(p.STE_cone_deg))


def cup_xcp(p, n=60):
    """x del centro de presión del chorro sobre la cuchara (bucket ABAJO): promedio de la superficie elíptica
    de la cuchara sobre la proyección del chorro (y² + z² ≤ R², |y| ≤ y_in)."""
    R = jet_footprint(p)
    xc0 = p.STE_X_exit + p.REV_cup_dx
    acc, k = 0.0, 0
    for i in range(n):
        z = -R + 2 * R * i / (n - 1)
        for j in range(n):
            y = -R + 2 * R * j / (n - 1)
            if y * y + z * z <= R * R and abs(y) <= p.REV_y_in and abs(z) < p.REV_cup_az:
                acc += xc0 + p.REV_cup_ax * math.sqrt(1 - (z / p.REV_cup_az) ** 2)
                k += 1
    return acc / k


def lock_angle(p, side):
    """Ángulo (°) de la traba del brazo +Y (side > 0) o −Y (side < 0): fuente única piezas/_release.lock_ang."""
    import sys
    from pathlib import Path
    q = str(Path(__file__).resolve().parent / "piezas")
    if q not in sys.path:
        sys.path.insert(0, q)
    import _release
    return _release.lock_ang(p, side)


def jet_momentum(p, Fb):
    """Chorro sobre la cuchara (bucket ABAJO), balance de cantidad de movimiento en el plano xz de la boquilla
    (auditoría ronda 4, R4-04): entra J = ṁ·V por el eje (z = 0) en +x y sale por el labio INFERIOR de la cuchara
    (punto y tangente de la elipse interior en REV_cup_t1, hacia proa y arriba) con el mismo módulo (k_r = 1).
    F_x = F_b fija J = F_b / (1 − t_x); la fuerza SOBRE el bucket es F = J·(1 − t_x, −t_z) y el momento alrededor
    del pivote M_h = |−Z_p·J + (r_labio × (−J·t))_y|. Toda la salida por el labio inferior es la cota de M_h: por el
    superior da la mitad (verificado al escribirlo: 135 contra 68 N·m con R12) [CALCULADO]."""
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    t1 = math.radians(p.REV_cup_t1)
    ax, az = p.REV_cup_ax, p.REV_cup_az
    lip = (p.STE_X_exit + p.REV_cup_dx + ax * math.cos(t1), az * math.sin(t1))
    d = (ax * math.sin(t1), -az * math.cos(t1))                 # −d/dt: el agua corre hacia el labio inferior
    n = math.hypot(*d)
    tout = (d[0] / n, d[1] / n)
    J = Fb / (1.0 - tout[0])
    F = (Fb, -J * tout[1])
    rx, rz = lip[0] - Xb, lip[1] - Zb
    M = -Zb * J + (rz * (-J * tout[0]) - rx * (-J * tout[1]))
    return {"J": J, "F": F, "Mh": abs(M), "lip": lip, "t_out": tout}


def bucket_reactions(p, Fb, share):
    """Estática del bucket ABAJO (reversa), marco de la boquilla, plano xz. Chorro: F y M_h de jet_momentum
    (cantidad de movimiento con salida por el labio inferior); cada traba toma SOLO la componente tangencial a su
    círculo (el momento) y cada pivote la mitad del chorro más la reacción de la traba de su brazo:
        L_s = (M_h·share_s / r)·t_s,  t_s = (sen a_s, −cos a_s);   R_s = −F/2 − L_s.
    share = {+1: fracción de M_h en la traba +Y, −1: en la −Y} (suman 1; falta = 0). Criterio de diseño (ronda 4):
    share = 1 en una traba (los agujeros tienen juego y el desfase entre trabas no está controlado: cada traba
    sola lleva todo M_h). Fuerzas SOBRE EL BUCKET [N]."""
    if abs(sum(share.values()) - 1.0) > 1e-9:
        raise ValueError(f"bucket_reactions: el reparto entre trabas debe sumar 1 ({share})")
    jm = jet_momentum(p, Fb)
    F, Mh = jm["F"], jm["Mh"]
    L, R = {}, {}
    for s_ in (1, -1):
        a = math.radians(lock_angle(p, s_))
        lam = Mh * share.get(s_, 0.0) / p.REV_lock_r
        L[s_] = (lam * math.sin(a), -lam * math.cos(a))
        R[s_] = (-F[0] / 2 - L[s_][0], -F[1] / 2 - L[s_][1])
    return {"F": F, "Mh": Mh, "x_cp": cup_xcp(p), "lip": jm["lip"], "t_out": jm["t_out"], "J": jm["J"], "L": L, "R": R}


def pivot_load_max(p, Fb, shares):
    """Mayor reacción de pivote (módulo) entre los repartos dados y los dos brazos."""
    return max(math.hypot(*bucket_reactions(p, Fb, sh)["R"][s_]) for sh in shares for s_ in (1, -1))


def ear_root_moment(p, Fb, share, side):
    """Momento en el plano de la oreja del bucket (lado `side`) en su raíz (x = X_pivote, z = 30 mm): fuerzas
    SOBRE LA OREJA = −(reacción del pivote) en el pivote y −(reacción de la traba) en el eje del émbolo."""
    r = bucket_reactions(p, Fb, share)
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    a = math.radians(lock_angle(p, side))
    lx, lz = Xb + p.REV_lock_r * math.cos(a), Zb + p.REV_lock_r * math.sin(a)
    M, Fz = 0.0, 0.0
    for (x, z), (fx, fz) in (((Xb, Zb), (-r["R"][side][0], -r["R"][side][1])), ((lx, lz), (-r["L"][side][0], -r["L"][side][1]))):
        M += (z - 30.0) * fx - (x - Xb) * fz
        Fz += fz
    return abs(M), Fz


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
    Mh = jet_momentum(p, Fb)["Mh"]            # N·mm (R12)
    Mh_n = jet_momentum(p, Fbn)["Mh"]         # reversa de sizing

    # ------------------------------------------------------------------ boquilla P1-STE-01 (Al 6061-T6)
    ro, rb = p.STE_ro, p.STE_rb
    Zt = math.pi / 32 * ((2 * ro) ** 4 - (2 * rb) ** 4) / (2 * ro)
    row(rows, "P1-STE-01", "Flexión del tubo por el desvío del chorro (fatiga, sizing)",
        f"M = F_s·e = {Fs_n:.0f} N × {e:.0f} mm; Z tubo Ø{2*ro:.1f}/Ø{2*rb:.1f}", Ms_n / Zt, AL6061_FAT, A, T2)
    # Orejas del bucket (auditoría ronda 4): cada oreja lleva SOLA la reacción de su pivote (chorro/2 + traba) y la de
    # su traba con M_h COMPLETO (criterio de traba única: los agujeros tienen juego, no hay reparto garantizado), con
    # R12 (corta) y con la reversa de sizing (fatiga). Raíz: sección STE_ear_t × 36 en z = 30 bajo el pivote (la oreja
    # real es más ancha: lóbulos del pivote y de la traba → fila conservadora). El pico en el borde de los agujeros lo da
    # el FEA (04_diseno/fea, P1-STE-01).
    ty = p.STE_ear_t
    Ze = ty * 36.0 ** 2 / 6
    lev = Zb - 30.0
    full = ({1: 1.0}, {-1: 1.0})
    Me, Fze = max((ear_root_moment(p, Fb, sh, s_) for sh in full for s_ in sh), key=lambda q: q[0])
    Me_n, Fze_n = max((ear_root_moment(p, Fbn, sh, s_) for sh in full for s_ in sh), key=lambda q: q[0])
    row(rows, "P1-STE-01", "Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo)",
        f"M raíz = {Me/1000:.0f} N·m (pivote a {lev:.0f} mm + traba a r {p.REV_lock_r:g}); sección {ty:g} × 36",
        Me / Ze + abs(Fze) / (ty * 36.0), AL6061, A, T2)
    row(rows, "P1-STE-01", "Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba)",
        f"M raíz = {Me_n/1000:.1f} N·m; {ty:g} × 36", Me_n / Ze + abs(Fze_n) / (ty * 36.0), AL6061_FAT, A, T2)
    F_lk = Mh / p.REV_lock_r
    dth = p.REV_lock_thread_d
    lig = p.STE_lock_lobe_r - dth / 2         # lóbulo alrededor de la rosca M24 del émbolo [P1-STE-01]
    row(rows, "P1-STE-01", f"Oreja del bucket: ligamento de la rosca M{dth:g} del émbolo (R12, M_h completo)",
        f"F = M_h/r = {F_lk:.0f} N; desgarro por 2 ligamentos {lig:g} × {ty:g}: σ = √3·F/(2·l·t)",
        math.sqrt(3) * F_lk / (2 * lig * ty), AL6061, A, T2)
    row(rows, "P1-STE-01", f"Rosca M{dth:g}×1,5 del émbolo en la oreja: aplastamiento lateral (R12)",
        f"F = {F_lk:.0f} N / (Ø{dth:g} × {ty:g})", F_lk / (dth * ty), AL6061, A, T2)
    R_d = pivot_load_max(p, Fb, full)
    R_dn = pivot_load_max(p, Fbn, full)
    lev_b = (p.REV_y_in - p.STE_ear_y1) + p.REV_bush_L / 2          # cara de la oreja → mitad del buje
    row(rows, "P1-STE-01", "Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, M_h completo)",
        f"M = R_pivote {R_d:.0f} N × {lev_b:.1f} mm en la cara; raíz 36 × {ty:g}", R_d * lev_b / (36.0 * ty ** 2 / 6), AL6061, A, T2)
    row(rows, "P1-STE-01", f"Oreja del bucket: aplastamiento del piloto Ø{p.REV_sp_pilot_d:g} del espaciador en el agujero H7 (R12, si la unión desliza)",
        f"{R_d:.0f} N / (Ø{p.REV_sp_pilot_d:g} × {ty:g})", R_d / (p.REV_sp_pilot_d * ty), AL6061, A, T2)
    Fp = math.hypot(Fb / 2, Fs / 2)
    Zp = (2 * p.STE_ear_rp) * 30.0 ** 2 / 6
    row(rows, "P1-STE-01", "Oreja de pivote (dentro de la de la bomba): flexión de la raíz",
        f"F = √((F_b/2)²+(F_s/2)²) = {Fp:.0f} N a 12 mm; 25 × 30", Fp * 12.0 / Zp, AL6061, A, T2)
    # PETG (descartado) — mismo caso de la oreja del bucket con la admisible de fatiga de ciclos bajos
    s_petg = (Fbn / 2) * lev / (12.0 * 36.0 ** 2 / 6)          # (cálculo de la ronda 1: oreja de 12 mm con F_b/2)
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

    # ------------------------------------------------------------------ bucket P1-REV-01 (Al 5083 REV_t; FS de diseño: FEA, 04_diseno/fea)
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
    # Brazos y trabas (auditoría ronda 4). Una traba por brazo (REV_n_locks = 2); cada traba toma solo la componente
    # tangencial (el momento) y cada pivote el chorro/2 más la reacción de la traba de su brazo. Los agujeros de traba
    # tienen juego (Ø16,5 / perno Ø16) y el desfase entre las dos no se controla: con la reversa de servicio una sola
    # traba lleva todo M_h (FEA ronda 3). Criterio: CADA traba sola, con su brazo, su pivote y su oreja, lleva M_h
    # completo con R12 (FS ≥ 2, corta) y con la reversa de sizing (fatiga). La segunda traba es redundancia.
    t = p.REV_t
    Zarm = t * 60.0 ** 2 / 6
    row(rows, "P1-REV-01", "Brazo trabado: flexión en su plano con M_h completo (R12, corta)",
        f"M = M_h = {Mh/1000:.0f} N·m en un brazo; sección {t:g} × 60", Mh / Zarm, AL5083, A, T2)
    row(rows, "P1-REV-01", "Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura)",
        f"M = M_h,sizing = {Mh_n/1000:.0f} N·m", Mh_n / Zarm, AL5083_WLCF, A, T2)
    # sección abierta (Saint-Venant): τ = T·t/J, J = s·t³/3; con un solo brazo trabado el momento del otro lado llega
    # al brazo trabado por torsión de la cuchara: en la unión con ese brazo T = M_h (cota: sin restricción de alabeo)
    s_len = sum(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(_cup_line(p), _cup_line(p)[1:]))
    J = s_len * t ** 3 / 3
    row(rows, "P1-REV-01", "Cuchara abierta a torsión con un solo brazo trabado (R12, corta)",
        f"T = M_h = {Mh/1000:.0f} N·m en la unión con el brazo trabado; τ = T·t/J, J = s·t³/3 (s = {s_len:.0f})",
        math.sqrt(3) * Mh * t / J, AL5083, A, T2)
    row(rows, "P1-REV-01", "Cuchara abierta a torsión con un solo brazo trabado (reversa sizing, fatiga de soldadura)",
        f"T = M_h,sizing = {Mh_n/1000:.0f} N·m; τ en la soldadura brazo–cuchara", math.sqrt(3) * Mh_n * t / J, AL5083_WLCF, A, T2)
    Fl = Mh / p.REV_lock_r                      # M_h completo en una traba
    Fl_n = Mh_n / p.REV_lock_r
    dl = p.REV_lock_pin_d
    row(rows, "P1-REV-01", f"Agujero de traba: aplastamiento del brazo (perno Ø{dl:g}, M_h completo, R12)",
        f"F = M_h/r = {Mh/1000:.0f} N·m / {p.REV_lock_r:.0f} mm = {Fl:.0f} N", Fl / (dl * p.REV_t), AL5083, A, T2)
    row(rows, "P1-REV-01", f"Pivote: aplastamiento del brazo + aro (buje Ø{p.REV_bush_od:g} × {p.REV_bush_L:g}), R12",
        f"R_pivote = {R_d:.0f} N (chorro/2 + traba con M_h completo)", R_d / (p.REV_bush_od * p.REV_bush_L), AL5083, A, T2)

    # ------------------------------------------------------------------ pivote (espaciador + M12), buje, émbolo
    # Espaciador P1-REV-02: muñón Ø REV_pin_d (el bucket gira en su buje) en voladizo desde la brida Ø REV_sp_fl_d, que
    # apoya en la cara exterior de la oreja; piloto Ø REV_sp_pilot_d ajustado (H7/h6) en la oreja: no desliza.
    d_o, d_i = p.REV_pin_d, 12.5
    Zsl = math.pi * (d_o ** 4 - d_i ** 4) / (32 * d_o)
    Asl = math.pi / 4 * (d_o ** 2 - d_i ** 2)
    lev_j = (p.REV_y_in - p.STE_ear_y1 - p.REV_sp_fl_t) + p.REV_bush_L / 2     # cara de la brida → mitad del buje

    def sleeve(Rp):
        return vm(Rp * lev_j / Zsl, 2 * Rp / Asl)
    row(rows, "P1-REV-02", f"Muñón Ø{d_o:g}/Ø{d_i:g} en voladizo desde la brida: flexión + corte (R12, una traba)",
        f"R = {R_d:.0f} N a {lev_j:.1f} mm de la brida; τ = 2V/A (tubo)", sleeve(R_d), SS316, A, T2)
    row(rows, "P1-REV-02", "Muñón: flexión (reversa sizing, fatiga; una traba)",
        f"R = {R_dn:.0f} N", R_dn * lev_j / Zsl, SS316_FAT, A, T2)
    # unión brida–oreja apretada por el M12: no se abre con la precarga MÍNIMA (par con K máx.). Momento en la cara de
    # la oreja M = R·lev_b; la corona de contacto Ø(piloto + 1)…Ø brida abre cuando M > F·k, k = (D² + d²)/(8·D)
    Dk, dk = p.REV_sp_fl_d, p.REV_sp_pilot_d + 1.0
    kern = (Dk ** 2 + dk ** 2) / (8 * Dk)
    Fmin, Fmax = p.REV_bolt_pre_N, p.REV_bolt_pre_max_N
    row(rows, "P1-REV-02", "Unión brida–oreja: no se abre con la precarga mínima (R12, una traba) [N·m]",
        f"M = {R_d:.0f} N × {lev_b:.1f} mm = {R_d*lev_b/1000:.1f} N·m contra F_mín·k = {Fmin/1000:.1f} kN × {kern:.2f} mm "
        f"(par {p.REV_bolt_T_Nm:g} N·m, K ≤ {p.REV_bolt_K[1]:g})", R_d * lev_b / 1000, Fmin * kern / 1000, A, T2)
    A_cl = math.pi / 4 * (Dk ** 2 - dk ** 2)
    row(rows, "P1-REV-02", "Brida sobre la oreja 6061: presión con la precarga máxima (K 0,12)",
        f"{Fmax/1000:.1f} kN / corona {A_cl:.0f} mm²", Fmax / A_cl, AL6061, A, T2)
    row(rows, "P1-REV-02", "Tornillo M12 A4-80 al montar con la precarga máxima: σ_red ≈ 1,15·F/A_s ≤ 0,9·Rp0,2 (VDI 2230)",
        f"{Fmax/1000:.1f} kN / 84,3 mm²; torsión de la rosca ≈ +15 % [ESTIMADO]", 1.15 * Fmax / 84.3, 0.9 * A4_80, A, 1.0,
        "criterio de montaje (no de servicio): VDI 2230 admite hasta el 90 % de Rp0,2 al apretar")
    row(rows, "P1-REV-03", f"Buje POM Ø{d_o + 0.1:g}/Ø{p.REV_bush_od:g} × {p.REV_bush_L:g}: presión (R12, una traba)",
        f"{R_d:.0f} N / ({d_o:g} × {p.REV_bush_L:g})", R_d / (d_o * p.REV_bush_L), POM_STAT, A, T2)
    row(rows, "P1-REV-03", "Buje POM: presión (reversa sizing, oscilación; una traba)",
        f"{R_dn:.0f} N / ({d_o:g} × {p.REV_bush_L:g})", R_dn / (d_o * p.REV_bush_L), POM_DYN, A, T2)
    lev_l = (p.REV_y_in - p.STE_ear_y1) + p.REV_t / 2           # cara de la oreja (punta del cuerpo) → mitad del brazo
    row(rows, "P1-REV-04", f"Perno del émbolo Ø{dl:g} (316): flexión + corte con M_h completo (R12)",
        f"F = M_h/r = {Fl:.0f} N a {lev_l:.1f} mm", vm(Fl * lev_l / z_round(dl), 4 / 3 * Fl / (math.pi * dl ** 2 / 4)), SS316, A, T2)
    row(rows, "P1-REV-04", "Perno del émbolo: flexión (reversa sizing, fatiga; M_h completo)",
        f"F = {Fl_n:.0f} N", Fl_n * lev_l / z_round(dl), SS316_FAT, A, T2)
    # cuerpo del émbolo apretado contra su collar (Ø36 con 2 planos e/c 32 → corona equivalente Ø34/Ø24,5) en la cara
    # interior de la oreja: el momento del perno en el plano medio de la oreja (F·(luz + t/2 + oreja/2)) no abre la unión
    # con la precarga mínima; con la máxima el cuerpo (316, A_s M24×1,5 − agujero Ø16,2) no pasa 0,9·Rp0,2
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parent / "piezas"))
    import _release as _RL
    Kmin, Kmax = p.REV_bolt_K
    dth = p.REV_lock_thread_d
    Fc_min = p.REV_lock_T_Nm * 1000 / (Kmax * dth)
    Fc_max = p.REV_lock_T_Nm * 1000 / (Kmin * dth)
    Dc, dc = _RL.PLG_COLLAR_D - 2.0, dth + 0.5
    kern_c = (Dc ** 2 + dc ** 2) / (8 * Dc)
    M_lk = Fl * (lev_l + p.STE_ear_t / 2)
    row(rows, "P1-REV-04", "Cuerpo del émbolo apretado contra su collar: la unión no se abre (R12, M_h completo) [N·m]",
        f"M = {Fl:.0f} N × {lev_l + p.STE_ear_t / 2:.1f} mm = {M_lk/1000:.1f} N·m contra F_mín·k = {Fc_min/1000:.1f} kN × {kern_c:.2f} mm "
        f"(par {p.REV_lock_T_Nm:g} N·m, K ≤ {Kmax:g}, Loctite 243)", M_lk / 1000, Fc_min * kern_c / 1000, A, T2)
    A_body = math.pi / 4 * ((dth - 0.9382 * 1.5) ** 2 - (dl + 0.2) ** 2)     # A_s ≈ (d − 0,9382·P)² (ISO 898) − agujero
    row(rows, "P1-REV-04", "Cuerpo del émbolo (316) al apretar con la precarga máxima: σ_red ≈ 1,15·F/A ≤ 0,9·Rp0,2 (VDI 2230)",
        f"{Fc_max/1000:.1f} kN / {A_body:.0f} mm² (A_s M{dth:g}×1,5 − Ø{dl + 0.2:g})", 1.15 * Fc_max / A_body, 0.9 * SS316, A, 1.0,
        "criterio de montaje (no de servicio)")
    # arrancamiento de la rosca interior M24×1,5 de la oreja (6061) con la precarga máxima: área de corte ≈ 0,75·π·d·L_e
    # [ESTIMADO: fórmula simplificada de rosca interior, L_e = espesor de la oreja]; τ admisible 0,58·Rp0,2 (von Mises)
    A_th = 0.75 * math.pi * dth * p.STE_ear_t
    row(rows, "P1-STE-01", f"Rosca M{dth:g}×1,5 de la oreja (6061): arrancamiento con la precarga máxima del émbolo",
        f"τ = {Fc_max/1000:.1f} kN / (0,75·π·{dth:g}·{p.STE_ear_t:g} = {A_th:.0f} mm²) contra 0,58·Rp0,2", Fc_max / A_th, 0.58 * AL6061, A, T2)
    row(rows, "P1-STE-01", "Collar del émbolo sobre la oreja 6061: presión con la precarga máxima",
        f"{Fc_max/1000:.1f} kN / corona Ø{Dc:g}/Ø{dc:g}", Fc_max / (math.pi / 4 * (Dc ** 2 - dc ** 2)), AL6061, A, T2)
    F_cab = p.CTL_hand_F * 125.0 / 46.0      # palanca forzada contra el tope: 100 N × 125 mm / manivela 46
    row(rows, "P1-REV-06", "Tornillo con hombro Ø8 de la varilla: flexión (palanca forzada)",
        f"F = 100 N × 125/46 = {F_cab:.0f} N a 6 mm", F_cab * 6.0 / z_round(p.REV_stud_d), SS316, A, T2)
    # desbloqueo (ronda 4, R4-06/R4-07): tiro de diseño por cable = mano de diseño en el gatillo repartida por la barra
    # igualadora (cada cable lleva a lo sumo la mitad, aunque un émbolo quede trabado) ≥ resorte final / rendimiento
    import importlib.util as _ilu
    import sys as _sys
    from pathlib import Path as _P
    _pz = str(_P(__file__).resolve().parent / "piezas")
    if _pz not in _sys.path:
        _sys.path.insert(0, _pz)
    import _release as RL
    _sp = _ilu.spec_from_file_location("ctl14", _P(_pz) / "P1-CTL-14_gatillo.py")
    G = _ilu.module_from_spec(_sp)
    _sp.loader.exec_module(G)
    F_rel = max(G.cable_pull_design(p), RL.SPRING_F_MAX / RL.BOWDEN_ETA)
    _c = lambda v, f=".1f": format(v, f).replace(".", ",")              # noqa: E731
    rel_txt = (f"tiro de diseño {F_rel:.0f} N por cable [CALCULADO: mano {p.CTL_hand_F:g} N [SUPUESTO] × {_c(G.R_F, 'g')}/"
               f"{_c(G.R_W * math.cos(math.radians(G.ANG / 2)))} / 2 cables; ≥ resorte {_c(RL.SPRING_F_MAX, 'g')} N [ESTIMADO] / "
               f"η {_c(RL.BOWDEN_ETA, 'g')} [ESTIMADO]]")
    L_cr = RL.lever_x0(p) - min(RL.lock_xz(p, s_)[0] for s_ in RL.lock_sides(p))     # voladizo del perno más largo
    row(rows, "P1-REV-09", f"Perno de manivela Ø{RL.CRANK_D:g} 316 estirado (voladizo hasta el eje del émbolo): flexión",
        f"{rel_txt} a {_c(L_cr)} mm", F_rel * L_cr / z_round(RL.CRANK_D), SS316_CD, A, T2)
    b_arm = 2 * RL.CRANK_BOSS_R
    row(rows, "P1-REV-09", f"Balancín {RL.LEV_T:g} mm 5083: flexión del brazo junto al cubo del eje",
        f"{F_rel:.0f} N a {RL.LEV_L - RL.PIV_BOSS_R:g} mm; sección {b_arm:g} × {RL.LEV_T:g}",
        F_rel * (RL.LEV_L - RL.PIV_BOSS_R) / (RL.LEV_T * b_arm ** 2 / 6), AL5083, A, T2)
    h_m5 = max(RL.lock_xz(p, s_)[1] for s_ in RL.lock_sides(p)) - RL.pad_z(p)
    T_m5 = F_rel * h_m5 / (RL.PAD_W + abs(RL.pad_screws(p)[0][1]))
    row(rows, "P1-REV-09", "Tornillo M5 A4-70 de la base al pad de la boquilla: tracción (un cable tirando, eslabón a la altura del émbolo)",
        f"T = {F_rel:.0f} N × {_c(h_m5)} / {RL.PAD_W + abs(RL.pad_screws(p)[0][1]):g} = {T_m5:.0f} N / A_s 14,2 mm²",
        T_m5 / 14.2, A4_70, A, T2)
    row(rows, "P1-CTL-14", f"Gatillo 6 mm: flexión de la hoja en el cubo ({p.CTL_hand_F:g} N a {G.R_F:g} mm del pivote)",
        f"M = {p.CTL_hand_F:g} N × {G.R_F - 7.0:g} mm; sección 12 × 6", p.CTL_hand_F * (G.R_F - 7.0) / (6 * 12 ** 2 / 6), AL6061, A, T2)
    F_piv = p.CTL_hand_F + 2 * F_rel
    arm_p = (G.Y0 + G.Y1) / 2 - 37.0
    row(rows, "P1-CTL-14", f"Pasador Ø{G.PIV_D:g} A4-70 del gatillo: flexión (mano + 2 cables; apoyo en la placa lateral del mango)",
        f"F = {F_piv:.0f} N a {_c(arm_p)} mm", F_piv * arm_p / z_round(G.PIV_D), A4_70, A, T2)
    row(rows, "P1-CTL-14", f"Barra igualadora 316 {G.BAR_T:g} × 4: flexión (dos cables a ±{G.BAR_H:g} del pasador)",
        f"M = {F_rel:.0f} N × {G.BAR_H:g} mm; sección {G.BAR_T:g} × 4", F_rel * G.BAR_H / (4 * G.BAR_T ** 2 / 6), SS316, A, T2)
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
        "M_hinge_sizing_Nm": round(Mh_n / 1000, 1), "F_z_bucket_N": round(jet_momentum(p, Fb)["F"][1], 0),
        "J_jet_N": round(jet_momentum(p, Fb)["J"], 0),
        "F_lock_pin_N": round(Fl, 0), "F_lock_pin_sizing_N": round(Fl_n, 0), "n_locks": p.REV_n_locks,
        "lock_criterion": "cada traba sola lleva M_h completo",
        "R_bucket_pivot_design_N": round(R_d, 0), "R_bucket_pivot_sizing_N": round(R_dn, 0),
        "bolt_torque_Nm": p.REV_bolt_T_Nm, "lock_body_torque_Nm": p.REV_lock_T_Nm, "bolt_pre_min_N": round(Fmin, 0), "bolt_pre_max_N": round(Fmax, 0),
        "F_pivot_pin_top_N": round(F_top, 0), "F_pivot_pin_bot_N": round(F_bot, 0),
        "F_stop_N": round(F_st, 0),
        "PETG_boquilla": {"caso": "oreja del bucket 12 mm, reversa sizing, admisible lcf",
                          "sigma_MPa": round(s_petg, 2), "FS": round(petg_fs, 2),
                          "conclusion": "FS < 3 → boquilla de Al 6061-T6 (además el perno Ø8 en PETG: aplastamiento)"},
    }
