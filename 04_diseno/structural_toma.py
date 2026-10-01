"""structural_toma.py — FS del grupo TOMA (P1-INT-01 conducto, -02 placa base, -03 rejilla, -04 tapa).

Cargas (sizing.json loads + params_toma):
  p_max  = p_pump_max_Pa (presión de cierre de la bomba): con la rejilla tapada la succión en la toma
           llega a −p_max; con la boquilla cerrada la contrapresión se toma como +p_max (conservador).
  p_slam = toma_p_slam_Pa [ESTIMADO, ISO 12215-5, no verificado] sobre el fondo y transmitido al agua
           de la toma (la abertura comunica el conducto con el fondo).
  p_ram  = recuperación de presión dinámica a 30 km/h (sostenida en marcha).
  Δp_cic = p_ram + succión dinámica a Q_max (ciclo marcha ↔ punto fijo, ~1e5 ciclos/temporada).
  3 g × (agua del conducto + conducto) como carga de inercia en la brida.
El empuje del tren NO pasa por el conducto: va por el soporte de rodamientos (TREN) a la placa base.
Metales: FS ≥ 2 contra fluencia (estático) o contra la curva S-N de la unión soldada (fatiga).
"""
from __future__ import annotations

import math


def _sec_props(poly):
    """Área, I_y (flexión en z) y fibra máx. de un polígono (y, z)."""
    n = len(poly)
    A = Cz = 0.0
    for i in range(n):
        y0, z0 = poly[i]
        y1, z1 = poly[(i + 1) % n]
        c = y0 * z1 - y1 * z0
        A += c
        Cz += (z0 + z1) * c
    A *= 0.5
    Cz /= (6 * A)
    Izz = 0.0
    for i in range(n):
        y0, z0 = poly[i]
        y1, z1 = poly[(i + 1) % n]
        c = y0 * z1 - y1 * z0
        Izz += (z0 * z0 + z0 * z1 + z1 * z1) * c
    Izz = Izz / 12.0 - A * Cz * Cz
    zmax = max(abs(z - Cz) for _, z in poly)
    return abs(A), abs(Izz), zmax


def cases(p, A, row, rows, T3, T2):
    L = p.sz["loads"]
    rho = p.inp["water"]["density_kg_m3"]
    g = 9.81
    mat = p.raw.get("pmp_mat", {})
    Sy_al = mat.get("Al 5083", {}).get("Sy", 125.0)         # [ESTIMADO: EN 485-2 5083-O/H111 Rp0,2 ≥ 125 MPa]
    Sy_316 = mat.get("AISI 316", {}).get("Sy", 205.0)
    Sy_a4 = mat.get("A4-70", {}).get("Sy", 450.0)
    FAT_al = 25.0     # [ESTIMADO: IIW, aluminio, filete transversal/borde de placa soldada, Δσ a 2e6 ciclos, m = 3 — buscar: "IIW recommendations fatigue aluminium FAT 25"]
    N_cyc = 1.0e5     # [ESTIMADO: ciclos marcha ↔ punto fijo y olas por temporada, R05]
    S_fat_al = FAT_al * (2e6 / N_cyc) ** (1 / 3)
    p_max = L["p_pump_max_Pa"] / 1e6
    p_slam = p.toma_p_slam_Pa / 1e6
    p_ram = p.toma_p_ram_Pa / 1e6
    A_out = math.pi / 4 * (p.toma_D_out / 1000) ** 2
    V_th = L["Q_max_m3s"] / A_out
    p_suc = 0.5 * rho * V_th ** 2 / 1e6
    dp_cyc = p_ram + p_suc
    p_des = max(p_max, p_slam)
    t = p.toma_t
    W = p.W_open
    # ---------------- P1-INT-01 conducto ----------------
    pid = "P1-INT-01"
    s = p_des * W ** 2 / (2 * t ** 2)
    row(rows, pid, "Techo plano entre costados, p = máx(p_cierre, p_golpe)",
        f"placa larga empotrada: σ = p·b²/(2t²), b = W_open = {W:.0f}, t = {t}", s, Sy_al, A, T2)
    xs = [p.x_lip + i for i in range(0, int(p.toma_x_j - p.x_lip), 5)]
    h = max(float(p.toma_roof_z(x)) for x in xs) - p.base_top_z
    s = p_des * h ** 2 / (2 * t ** 2)
    row(rows, pid, "Costado plano más alto (en el labio), p = máx(p_cierre, p_golpe)",
        f"placa empotrada brida–techo: σ = p·h²/(2t²), h = {h:.0f}", s, Sy_al, A, T2)
    s = dp_cyc * h ** 2 / (2 * t ** 2)
    row(rows, pid, f"Fatiga de la soldadura del costado: Δp = p_ram + p_succión = {dp_cyc*1e3:.0f} kPa, {N_cyc:.0e} ciclos",
        f"Δσ = Δp·h²/(2t²) vs FAT {FAT_al:.0f} (IIW, m = 3) → {S_fat_al:.0f} MPa", s, S_fat_al, A, T2)
    # brida inferior: tracción de bulones por la presión sobre la proyección de la abertura + 3 g
    import importlib.util
    from pathlib import Path
    here = Path(__file__).resolve().parent / "piezas"
    spec = importlib.util.spec_from_file_location("_int01", str(here / "P1-INT-01_conducto.py"))
    m1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m1)
    nb = 2 * len(m1.bolt_x(p))
    A_open = W * p.L_open
    V_w = A_open * 150.0 * 1e-9          # [ESTIMADO: agua en el conducto ≈ abertura × 150 mm medios]
    m_d = 4.7                            # [CALCULADO: manifest P1-INT-01 ≈ 4,7 kg]
    F_up = p_des * A_open + 3 * g * (rho * V_w + m_d)
    As6 = 20.1
    F_v = 4000.0                         # [ESTIMADO: precarga M6 A4-70 en rosca de Al, ~6 Nm]
    Phi = 0.25                           # [ESTIMADO: factor de carga de la unión (VDI 2230), bulón de acero en bridas de Al, valor típico 0,1–0,3]
    s = (F_v + Phi * F_up / nb) / As6
    row(rows, pid, f"Bulones M6 A4 brida ↔ placa ({nb}): precarga + p·A_abertura + 3 g",
        f"σ = (F_v + Φ·F/n)/A_s, F = {F_up:.0f} N, Φ = 0,25", s, Sy_a4, A, T2)
    # brida de la bomba: momento del bucket si la placa de espejo no lo tomara (conservador)
    lever = (p.X_bucket_pivot - p.X_duct_out)
    M = L["F_bucket_N"] * lever
    r = p.toma_R_out + t
    Wt = math.pi * r ** 2 * t
    s = M / Wt
    row(rows, pid, "Tubo junto a la brida de la bomba: momento del bucket (sin placa de espejo)",
        f"σ = M/(π r² t), M = F_bucket·{lever:.0f}", s, Sy_al, A, T2)
    F_b = 4 * M / (p.pump_flange_n * p.pump_flange_bc / 2)
    s = (F_v + Phi * F_b) / As6
    row(rows, pid, "Bulones M6 de la brida de la bomba: precarga + momento del bucket",
        "σ = (F_v + Φ·4M/(n·r_bc))/A_s, Φ = 0,25 (VDI 2230)", s, Sy_a4, A, T2)
    # buje del sello: reacción de la caja del sello (presión sobre Ø42 + resorte + 3 g) en voladizo del tubo
    F_s = p_max * math.pi / 4 * p.seal_spigot_d ** 2 + 60.0 + 3 * g * 0.6   # [ESTIMADO: resorte 60 N, caja 0,6 kg]
    Lt = p.S_seal - p.toma_S_cross
    do, di = p.toma_tube_od, p.toma_tube_id
    Wtube = math.pi * (do ** 4 - di ** 4) / (32 * do)
    s = F_s * Lt / Wtube
    row(rows, pid, "Tubo del eje en voladizo (sin contar el alma): caja del sello",
        f"σ = F·L/W, L = {Lt:.0f}", s, Sy_al, A, T2)
    # chimenea
    s = p_max * (p.toma_chim_id / 2 + t) / t
    row(rows, pid, "Chimenea de inspección: presión de cierre (aro)", "σ = p·r/t", s, Sy_al, A, T2)

    # ---------------- P1-INT-02 placa base ----------------
    pid = "P1-INT-02"
    tb = p.base_top_z
    b = (p.toma_plate_y + p.toma_rim_w / 2) - p.toma_bolt_y
    s = p_slam * b ** 2 / (2 * tb ** 2)
    row(rows, pid, "Paño lateral entre bulones del conducto y del ala: golpe de fondo",
        f"σ = p·b²/(2t²), b = {b:.0f}", s, Sy_al, A, T2)
    # M8 del soporte de rodamientos: ISO 10642 desde abajo (cabeza avellanada en la placa) + tuerca A4 arriba
    F_v8 = 7000.0                        # [ESTIMADO: M8 A4-70 a ~15 Nm con Tef-Gel (K ≈ 0,25)]
    z_ax = p.z_if + (0.5 * (p.brg_bracket_x0 + p.brg_bracket_x1) - p.x_if) * math.tan(math.radians(p.alpha))
    Mth = L["T_bollard_N"] * (z_ax - tb)
    dx = p.brg_bracket_holes[2][0] - p.brg_bracket_holes[0][0]
    F_t = Mth / dx / 2 + 3 * g * 3.0 / 4            # [ESTIMADO: soporte + rodamientos + eje ≈ 3 kg a 3 g]
    As8 = 36.6
    row(rows, pid, "Tornillos M8 A4-70 del soporte (ISO 10642 desde abajo + tuerca): precarga + vuelco del empuje",
        f"σ = (F_v + Φ·F_t)/A_s, F_v = {F_v8:.0f} N, F_t = {F_t:.0f} N, Φ = 0,25", (F_v8 + 0.25 * F_t) / As8, Sy_a4, A, T2)
    dk, d8 = 16.4, 8.4
    hc = (dk - d8) / 2
    sb = (F_v8 + F_t) / (math.pi / 4 * (dk ** 2 - d8 ** 2))
    row(rows, pid, "Asiento cónico de la cabeza M8 en el 5083 (aplastamiento)",
        "σ_b = F/(π/4·(dk² − d²)) (proyección del cono)", sb, Sy_al, A, T2)
    tau = (F_v8 + F_t) / (math.pi * dk * (tb - hc))
    row(rows, pid, "Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono)",
        f"τ = F/(π·dk·(t − h_cono)), t − h = {tb - hc:.1f}", tau, Sy_al / math.sqrt(3), A, T2)
    # bulones del ala (M6 ISO 10642): tracción por golpe + presión en la abertura; corte por empuje
    import importlib.util as iu
    spec = iu.spec_from_file_location("_int02", str(here / "P1-INT-02_placa_base.py"))
    m2 = iu.module_from_spec(spec)
    spec.loader.exec_module(m2)
    nh = len(m2.hull_bolts(p))
    A_body = (p.toma_plate_x1 - p.toma_plate_x0) * 2 * p.toma_plate_y
    F_up = p_slam * (A_body - A_open) + p_des * A_open
    s = (F_v + Phi * F_up / nh) / As6
    row(rows, pid, f"Bulones M6 del ala al casco ({nh}): precarga + golpe de fondo + presión en la abertura",
        f"σ = (F_v + Φ·F/n)/A_s, F = {F_up:.0f} N, Φ = 0,25", s, Sy_a4, A, T2)
    t_h = p.bottom_t
    sb = (L["T_bollard_N"] / nh) / (6 * t_h)
    row(rows, pid, "Aplastamiento del casco (Al 4 mm) por el empuje en los bulones del ala",
        "σ_b = (T/n)/(d·t)", sb, Sy_al, A, T2)
    pull = (F_up / nh) / (math.pi * 9.0 * (t_h - 2.8))
    row(rows, pid, "Arranque de la cabeza avellanada M6 en el casco de 4 mm (corte del labio de 1,2 mm)",
        "τ = (F/n)/(π·d_m·t_labio), d_m = 9", pull, Sy_al / math.sqrt(3), A, T2)

    # ---------------- P1-INT-03 rejilla ----------------
    pid = "P1-INT-03"
    bb, hh = p.grille_bar_d, p.toma_bar_h
    r = bb / 2
    arc = [(r * math.cos(math.radians(a)), r + r * math.sin(math.radians(a))) for a in range(195, 360, 15)]
    sec = [(r, r), (r, hh - 6.0), (0.8, hh), (-0.8, hh), (-r, hh - 6.0), (-r, r)] + arc
    Asec, I, c = _sec_props(sec)
    Wb = I / c
    span = p.toma_x_bf - p.toma_x_n
    w = p_max * (p.toma_bar_gap + bb)
    Mb = w * span ** 2 / 8
    row(rows, pid, "Barra con la rejilla tapada (bolsa) a la presión de cierre",
        f"viga simplemente apoyada L = {span:.0f}, w = p·paso, W = {Wb:.0f} mm³ (sección perfilada)", Mb / Wb, Sy_316, A, T2)
    P_imp = 200.0                        # [SUPUESTO: golpe de objeto/piedra 200 N en el centro de una barra]
    row(rows, pid, "Barra: golpe de objeto 200 N en el centro", "M = P·L/4", P_imp * span / 4 / Wb, Sy_316, A, T2)
    R_f = w * span / 2
    sb = R_f / (bb * 9.0)
    row(rows, pid, "Apoyo de la barra contra la cuña de la placa (aplastamiento del Al)",
        "σ_b = R/(b·9 mm)", sb, Sy_al, A, T2)

    # ---------------- P1-INT-04 tapa PETG ----------------
    pid = "P1-INT-04"
    import importlib.util as iu2
    spec = iu2.spec_from_file_location("_int04", str(here / "P1-INT-04_tapa_inspeccion.py"))
    m4 = iu2.module_from_spec(spec)
    spec.loader.exec_module(m4)
    a = m4.oring_r(p)
    tc = p.toma_cover_t                             # máximo en el centro (la ranura está en el borde cargado, donde M → 0)
    k = 3 * (3 + 0.38) / 8                          # placa circular simplemente apoyada, ν PETG ≈ 0,38 [ESTIMADO]
    row(rows, pid, "Tapa: succión/contrapresión de cierre (corta)", f"σ = 3(3+ν)p a²/(8t²), a = {a:.0f}, t = {tc:.1f}",
        k * p_max * a ** 2 / tc ** 2, "short", A, T3)
    row(rows, pid, "Tapa: recuperación de presión a 30 km/h (sostenida)", "ídem con p_ram",
        k * p_ram * a ** 2 / tc ** 2, "sust", A, T3)
    row(rows, pid, f"Tapa: ciclo marcha ↔ punto fijo Δp = {dp_cyc*1e3:.0f} kPa (olas/maniobras)", "ídem con Δp",
        k * dp_cyc * a ** 2 / tc ** 2, "lcf", A, T3)
    # purga: hexágono desde abajo con resalte arriba (r = PURGE_R): σ_r de placa apoyada en r
    tp = p.toma_cover_t + m4.BOSS_H - 5.2 - 0.2
    rr = m4.PURGE_R
    row(rows, pid, f"Tapa en la purga (r = {rr:.0f}, espesor neto {tp:.1f}): ciclo Δp (olas/maniobras)",
        "σ_r = 3(3+ν)p(a² − r²)/(8t²)", k * dp_cyc * (a ** 2 - rr ** 2) / tp ** 2, "lcf", A, T3)
    F_bolt = p_max * math.pi * a ** 2 / 4
    row(rows, pid, "Tapa: aplastamiento bajo arandela M6 Ø18 (sostenido)", "σ = F/(π/4(18² − 6,4²))",
        (p_ram * math.pi * a ** 2 / 4) / (math.pi / 4 * (18 ** 2 - 6.4 ** 2)), "sust", A, T3)
    return {"p_max_Pa": p_max * 1e6, "p_slam_Pa": p_slam * 1e6, "p_ram_Pa": p_ram * 1e6, "dp_cyc_Pa": dp_cyc * 1e6,
            "V_throat_ms": V_th, "FAT_al_MPa": FAT_al, "S_fat_al_MPa": S_fat_al,
            # alternativa descartada: conducto PETG — pared necesaria para FS 3 en fatiga del costado
            "petg_wall_req_mm": h * math.sqrt(dp_cyc / (2 * A["lcf"] / T3)),
            "petg_roof_req_mm": W * math.sqrt(dp_cyc / (2 * A["lcf"] / T3))}
