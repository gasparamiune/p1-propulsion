"""planos_bomba.py — planos del grupo BOMBA (P1-PMP-*): piezas torneadas/mecanizadas y tablas de
ángulos de álabe (impulsor y estator) para el taller CNC. Lo llama planos.py → draw(p, H).
Todas las cotas salen de params.py / params_bomba.py (sizing.json)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgwrite

sys.path.insert(0, str(Path(__file__).resolve().parent / "piezas"))
from _pmp_geom import camber_line, naca_half  # noqa: E402


def _f(x, n=2):
    return f"{x:.{n}f}".replace(".", ",")


def _stations(chord, a1, a2, tc, sign, r, x_le, n=10):
    cl = camber_line(chord, a1, a2, sign, n=200, x_le=x_le)
    out = []
    for i in range(n + 1):
        k = int(round(200 * i / n))
        f, X, T, b, _, _ = cl[k]
        out.append((f, X, math.degrees(T / r), b, 2 * naca_half(f, tc) * chord))
    return out


def blade_tables(p, H):
    """Hoja con las tablas de ángulos por sección (impulsor y estator) + coordenadas de línea media."""
    OUT = H["OUT"]
    pid, name = "P1-PMP-03", "tabla_angulos_alabes"
    W, Hh = 1700, 1500
    path = OUT / f"{pid}_{name}.svg"
    dwg = svgwrite.Drawing(str(path), size=(W, Hh))
    dwg.add(dwg.rect((0, 0), (W, Hh), fill="white"))
    g = dwg.add(dwg.g(font_family="DejaVu Sans", font_size=11))

    def txt(x, y, t, **k):
        g.add(dwg.text(t, insert=(x, y), **k))

    y = 30
    txt(20, y, f"IMPULSOR P1-PMP-03 — {p.blades} álabes, Ø{_f(p.D, 1)} (punta), cubo Ø{_f(p.D_hub, 1)}, "
        f"{p.pmp_rpm_design:.0f} rpm de diseño, giro {p.pmp_rot_sense}", font_size=14, font_weight="bold")
    y += 18
    txt(20, y, "Ángulos medidos DESDE LA TANGENCIAL (plano ⟂ al eje); ángulo de calado desde el eje = 90° − β. "
        "β flujo = triángulos de sizing (torbellino " + ("libre" if p.pmp_free_vortex else "LIMITADO en el cubo")
        + f"); β pala = flujo + incidencia {p.pmp_inc_deg:g}° (entrada) y + desviación de Constant (salida), R12 §2.5.")
    y += 16
    txt(20, y, "Perfil: línea media de arco circular (β lineal con el arco) + espesor NACA 00xx (BA redondeado, "
        "r_BA ≈ 1,1·(t/c)²·c); BA apilado radial en X = " + _f(p.pmp_imp_le_X, 1) + " mm (marco JET, X a popa), θ = 0 en +Y.")
    y += 26
    hdr = ["Sección", "r mm", "U m/s", "c_m", "c_u2", "β1 flujo", "β2 flujo", "β1 pala", "β2 pala", "δ", "calado",
           "cuerda", "t máx", "t/c", "solidez", "paso", "D_f", "w2/w1"]
    xs = [20, 110, 170, 230, 290, 350, 430, 510, 590, 670, 730, 810, 880, 950, 1010, 1080, 1150, 1210]
    for xx, hh in zip(xs, hdr):
        txt(xx, y, hh, font_weight="bold")
    for nm in ("cubo", "medio", "punta"):
        b = p.pmp_imp_table[nm]
        y += 16
        vals = [nm, _f(b["r"], 1), _f(b["u"], 1), _f(b["cm"]), _f(b["cu2"]), _f(b["beta1"], 1) + "°",
                _f(b["beta2"], 1) + "°", _f(b["bb1"], 1) + "°", _f(b["bb2"], 1) + "°", _f(b["delta"], 1) + "°",
                _f(90 - b["stagger"], 1) + "°", _f(b["chord"], 1), _f(b["tmax"], 2), _f(b["tc"], 3),
                _f(b["s"], 2), _f(b["pitch"], 1), _f(b["Df"], 2), _f(b["dh"], 2)]
        for xx, v in zip(xs, vals):
            txt(xx, y, v)
    y += 30
    # coordenadas de línea media por sección
    for nm in ("cubo", "medio", "punta"):
        b = p.pmp_imp_table[nm]
        st = _stations(b["chord"], b["bb1"], b["bb2"], b["tc"], -1, b["r"], p.pmp_imp_le_X)
        txt(20, y, f"Impulsor — sección {nm}: r = {_f(b['r'], 2)} mm (cilindro), cuerda {_f(b['chord'], 1)} mm, "
            f"t máx {_f(b['tmax'], 2)} mm", font_weight="bold")
        y += 15
        txt(20, y, "s/c")
        txt(80, y, "X mm")
        txt(150, y, "θ °")
        txt(220, y, "β pala °")
        txt(310, y, "espesor mm")
        for i, (f, X, th, be, t) in enumerate(st):
            txt(420 + 115 * i, y - 0, f"{_f(f, 1)}")
            txt(420 + 115 * i, y + 14, f"X {_f(X, 2)}")
            txt(420 + 115 * i, y + 28, f"θ {_f(th, 2)}")
            txt(420 + 115 * i, y + 42, f"β {_f(be, 1)}")
            txt(420 + 115 * i, y + 56, f"t {_f(t, 2)}")
        y += 76
    txt(20, y, "θ negativo = hacia atrás respecto del giro (el álabe se tuerce contra el sentido de giro hacia la salida). "
        f"Punta tornear a Ø{_f(p.D, 2)} −0/−0,02 contra el anillo de desgaste (holgura radial {_f(p.tip_clr, 2)} ± 0,05).")
    y += 16
    txt(20, y, "Radio de acuerdo álabe–cubo R 2–3 mm; borde de fuga ≥ 0,3 mm; Ra ≤ 1,6 en caras de presión/succión; "
        "balanceo estático + dinámico G 6.3 (ISO 1940) [ESTIMADO]. Alternativa: SLM 316L + mecanizado (R11 §6).")
    y += 36
    # estator
    txt(20, y, f"ESTATOR P1-PMP-06 — {p.vanes} álabes (coprimo con {p.blades}), entrada = stator_inlet_deg de sizing, "
        f"salida axial con sobregiro δ ≤ {p.pmp_st_dev_max:g}° (R12 §3.2); BA apilado en X = {_f(p.pmp_st_le_X, 1)}",
        font_size=14, font_weight="bold")
    y += 22
    hdr2 = ["Sección", "r mm", "c_u2 m/s", "α entrada", "α salida", "sobregiro", "cuerda", "t máx", "t/c", "solidez", "paso"]
    xs2 = [20, 110, 180, 270, 360, 450, 540, 620, 700, 760, 840]
    for xx, hh in zip(xs2, hdr2):
        txt(xx, y, hh, font_weight="bold")
    for nm in ("cubo", "medio", "punta"):
        v = p.pmp_st_table[nm]
        y += 16
        vals = [nm, _f(v["r"], 1), _f(v["cu2"]), _f(v["alpha_in"], 1) + "°", _f(v["alpha_out"], 1) + "°",
                _f(v["dev"], 1) + "°", _f(v["chord"], 1), _f(v["tmax"], 2), _f(v["tc"], 3), _f(v["s"], 2),
                _f(v["pitch"], 1)]
        for xx, val in zip(xs2, vals):
            txt(xx, y, val)
    y += 30
    for nm in ("cubo", "medio", "punta"):
        v = p.pmp_st_table[nm]
        st = _stations(v["chord"], v["alpha_in"], v["alpha_out"], v["tc"], +1, v["r"], p.pmp_st_le_X)
        txt(20, y, f"Estator — sección {nm}: r = {_f(v['r'], 2)} mm", font_weight="bold")
        y += 15
        for i, (f, X, th, be, t) in enumerate(st):
            txt(420 + 115 * i, y, f"{_f(f, 1)}")
            txt(420 + 115 * i, y + 14, f"X {_f(X, 2)}")
            txt(420 + 115 * i, y + 28, f"θ {_f(th, 2)}")
            txt(420 + 115 * i, y + 42, f"α {_f(be, 1)}")
            txt(420 + 115 * i, y + 56, f"t {_f(t, 2)}")
        y += 76
    H["title_block"](dwg, W, Hh, pid, "Tabla de ángulos de álabe (impulsor y estator) para CNC 5 ejes",
                     "AISI 316 (impulsor) / Al 6061-T6 anodizado duro (estator)", "—",
                     ["Geometría completa en 04_diseno/step/P1-PMP-03_impeller.step y P1-PMP-06_stator.step (manda el STEP).",
                      "Ángulos y cuerdas: 04_diseno/params_bomba.py (pmp_blade_row / pmp_vane_row) desde sizing.json."])
    dwg.save()
    return path


def draw(p, H):
    T, PL = H["turned"], H["plate"]
    made = []
    # ---------------- anillo de desgaste
    made.append(T("P1-PMP-02", "wear_ring", "AISI 316 (1.4404) tubo/barra torneado",
                  [(p.L_ring, p.pmp_D_seat, f"Ø ext {_f(p.pmp_D_seat)} p6 (prensado) · Ø int {_f(p.D_bore)} H7")],
                  feats=[(2.0, "ranura anti-rotación 4,1 × 4 prof. (arriba, +Z)")],
                  notes=[f"Ø interior {_f(p.D_bore)} H7 = D {_f(p.D, 1)} + 2 × holgura {_f(p.tip_clr)}; tornear el Ø interior "
                         f"DESPUÉS de prensar en la carcasa (TIR ≤ {_f(p.pmp_ring_TIR)} respecto del asiento).",
                         f"Prensado {p.pmp_ring_fit}; apoya contra el escalón de la carcasa en X_ring0 = {_f(p.X_ring0, 1)} (marco JET).",
                         "Reemplazar si la holgura de punta medida con galgas supera 0,8 mm (R12 §2.7)."]))
    # ---------------- carcasa
    X1h = p.X_st1 - p.pmp_stack_gap
    Lb = X1h - p.pmp_f2_t - (p.X_duct_out + p.pmp_f1_t)
    made.append(T("P1-PMP-01", "housing", "Al 6061-T6, anodizado duro",
                  [(p.pmp_f1_spigot_h, p.pmp_f1_spigot_d, f"espigón de centraje Ø{_f(p.pmp_f1_spigot_d, 0)} h6"),
                   (p.pmp_f1_t, p.pump_flange_od, "brida de la toma"),
                   (Lb, p.pmp_D_barrel, "cuerpo"),
                   (p.pmp_f2_t, p.pmp_f2_od, "brida a la tobera")],
                  feats=[(p.pmp_f1_spigot_h, f"cara: ranura O-ring Ø{_f(2*p.pmp_gl_r_in, 1)}–Ø{_f(2*(p.pmp_gl_r_in+p.pmp_gl_width), 1)} × {_f(p.pmp_gl_depth)} prof."),
                         (p.pmp_f1_spigot_h + p.X_ring0 - p.X_duct_out, "escalón: pasador Ø4 × 6 (r 69,2, arriba)"),
                         (p.pmp_f1_spigot_h + p.pmp_st_screw_X - p.X_duct_out,
                          f"2 × M5 radiales ±Y ROSCADOS (pared + saliente Ø{p.pmp_st_boss_d:g} × {p.pmp_st_boss_h:g}) — anti-giro del estator"),
                         (p.pmp_f1_spigot_h + p.pmp_cool_port[0] - p.X_duct_out, f"puerto {p.pmp_cool_thread} arriba (saliente Ø22)"),
                         (p.pmp_f1_spigot_h + X1h - p.X_duct_out, f"cara trasera: 8 × M5 × {p.pmp_f2_thread_L:g} (broca Ø4,2 × {p.pmp_f2_thread_L + 2:g})")],
                  notes=[f"Bore: Ø{_f(p.D_bore)} H8 de X {_f(p.X_duct_out - p.pmp_f1_spigot_h, 1)} a {_f(p.X_ring0, 1)}; Ø{_f(p.pmp_D_seat)} H7 de {_f(p.X_ring0, 1)} a {_f(X1h, 2)} (marco JET); "
                         "chaflán 15° × 2 a la entrada de popa (O-ring radial de la tobera).",
                         f"CENTRAJE con el conducto: espigón Ø{_f(p.pmp_f1_spigot_d, 0)} h6 × {_f(p.pmp_f1_spigot_h, 1)} en el rebaje H7 × {_f(p.pmp_f1_recess_h, 1)} de P1-INT-01 "
                         f"(las caras de brida apoyan). Brida toma: 8 × Ø6,4 en Ø{_f(p.pump_flange_bc)} a {p.pmp_flange_ang0:g}° + k·45° desde +Y.",
                         f"Brida trasera Ø{_f(p.pmp_f2_od, 1)}: 8 × M5 ciegos en Ø{_f(p.pmp_f2_bc, 2)}, misma fase; la cara queda a {_f(p.pmp_stack_gap)} de la brida de la tobera "
                         "(la espiga aprieta la camisa del estator). M5 radiales con arandela bonded (USIT) bajo la cabeza.",
                         "Galvánica Al–316: anodizado duro, Tef-Gel en roscas y asientos, ánodo de Al (R06 §0, R10b H21).",
                         "Concentricidad asiento ↔ espigón de centraje ≤ 0,03 TIR (mecanizar en una atada)."]))
    # ---------------- impulsor (cubo)
    made.append(T("P1-PMP-03", "impeller_hub", "AISI 316 (CNC 5 ejes; alt. SLM 316L + torneado)",
                  [(p.pmp_nose_L, p.D_hub, f"nariz elíptica Ø{_f(2*p.pmp_nose_r0, 0)}→Ø{_f(p.D_hub, 0)}"),
                   (p.pmp_band_X0, p.D_hub, f"zona de álabes (Ø punta {_f(p.D, 1)})"),
                   (p.pmp_band_L, 2 * p.pmp_land_r, f"asiento anillo retén Ø{_f(2*p.pmp_land_r, 0)} g6")],
                  feats=[(p.pmp_nose_L + p.pmp_pin_X, f"pasador Ø{_f(p.pmp_pin_hole)} H8 pasante (eje Y) + 2 × M3 (±Z)"),
                         (p.pmp_nose_L + p.L_imp - p.pmp_pocket[2], f"ranura anular Ø{_f(2*p.pmp_pocket[0], 0)}–Ø{_f(2*p.pmp_pocket[1], 0)} × {p.pmp_pocket[2]:g} desde popa")],
                  notes=[f"Agujero Ø{_f(p.shaft_d, 0)} H7 pasante, SIN chavetero: el par entra por el pasador de corte "
                         f"(X = {_f(p.pmp_pin_X, 1)} desde la cara del cubo).",
                         f"Fijación axial: arandela 316 + DIN 471-20 adelante (empuje) y atrás (retén). {p.blades} álabes, ver tabla de ángulos.",
                         f"Punta Ø{_f(p.D, 2)} −0/−0,02; caras del cubo ⟂ al agujero ≤ 0,02; balanceo G 6.3 [ESTIMADO]."]))
    made.append(blade_tables(p, H))
    # ---------------- anillo retén, pasador, buje
    made.append(T("P1-PMP-04", "pin_band", "AISI 316 torneado",
                  [(p.pmp_band_L, p.D_hub, f"Ø ext {_f(p.D_hub, 0)} · Ø int {_f(2*p.pmp_land_r, 0)} H7")],
                  feats=[(p.pmp_band_L / 2, "2 × Ø3,4 avellanado 90° (M3 ISO 10642), ±Z")],
                  notes=["Deslizante H7/g6 + Loctite 641 sobre el cubo; enrasado con el cubo; tapa los extremos del pasador."]))
    made.append(T("P1-PMP-05", "shear_pin", "Al 6061-T6 barra Ø3,5 h8",
                  [(p.pmp_pin_half_len, p.pmp_pin_d, f"Ø{_f(p.pmp_pin_d)} h8 — SEMIPASADOR (2 por juego)")],
                  notes=[f"Fusible: 2 semipasadores (uno desde +Y y otro desde −Y, se tocan en el centro del eje); 2 secciones de corte a r_eje → "
                         f"corta a ≈ {_f(p.pmp_pin_T_cut, 1)} N·m (sizing.mech.shear_pin). Llevar {p.pmp_pin_spares_sets} juegos de repuesto ({2 * p.pmp_pin_spares_sets} piezas).",
                         "Extremos con chaflán 0,3 × 45°; reemplazar cada temporada / 50 h y tras cualquier golpe [ESTIMADO]; no sustituir por acero.",
                         "Se cambian con el impulsor en el eje: sacar tobera y estator por popa, deslizar el anillo retén, botador corto Ø3 (≤ 33 mm)."]))
    made.append(T("P1-PMP-07", "water_bushing", "POM-C torneado (alt. Vesconite Hilube)",
                  [(p.pmp_bush_L, p.pmp_brg_od, f"Ø ext {_f(p.pmp_brg_od, 0)} s6 · Ø int {_f(p.pmp_brg_id)} +0,05/0")],
                  feats=[(0.0, f"{p.pmp_brg_grooves[0]} ranuras axiales {p.pmp_brg_grooves[1]:g} × {p.pmp_brg_grooves[2]:g}")],
                  notes=[f"Prensado desde proa en el cubo del estator (X {_f(p.pmp_bush_X0, 1)}–{_f(p.pmp_bush_X1, 1)}).",
                         "Juego en agua 0,2 mm diametral [ESTIMADO]: medir el Ø interior tras 48 h en agua (hinchamiento)."]))
    # ---------------- estator (perfil exterior) y tobera
    made.append(T("P1-PMP-06", "stator", "Al 6061-T6, CNC 5 ejes, anodizado duro",
                  [(p.X_st0 - p.pmp_st_shell_X0, p.pmp_D_seat, "camisa"),
                   (p.pmp_st_shell_X1 - p.X_st0, p.pmp_D_seat, f"camisa + {p.vanes} álabes"),
                   (p.X_st1 - p.pmp_st_shell_X1, p.D_hub, "cubo"),
                   (p.pmp_tail_L, 2 * p.pmp_tail_tip_r + 0.01, f"cono de cola Ø{_f(p.D_hub, 0)}→Ø{_f(2*p.pmp_tail_tip_r, 0)}")],
                  feats=[(p.X_st0 - p.pmp_st_shell_X0, f"alojamiento buje Ø{_f(p.pmp_brg_od, 0)} H7 hasta X {_f(p.pmp_bush_X1, 1)}"),
                         (p.pmp_st_screw_X - p.pmp_st_shell_X0, f"2 × Ø{_f(p.pmp_st_tip_hole[0], 1)} LISOS × {_f(p.pmp_st_tip_hole[1], 1)} prof. (±Y, punta de los M5 de la carcasa)"),
                         (p.pmp_cool_port[0] - p.pmp_st_shell_X0, f"Ø{_f(p.pmp_cool_bore_d, 0)} arriba (puerto de agua)")],
                  notes=[f"Camisa Ø{_f(p.pmp_D_seat)} g6 × Ø{_f(p.D_bore)}; cubo Ø{_f(p.D_hub, 0)}; agujero de salida de agua Ø{_f(p.pmp_tail_hole_d, 0)} en la punta.",
                         "Ángulos de álabe: ver P1-PMP-03_tabla_angulos_alabes. Concentricidad buje ↔ camisa ≤ 0,03 TIR."]))
    Rn = p.D_noz / 2
    made.append(T("P1-PMP-08", "fixed_nozzle", "Al 6061-T6 torneado, anodizado duro",
                  [(p.pmp_noz_spigot, p.pmp_D_seat, f"espiga g6 (+{_f(p.pmp_stack_gap)} sobre el asiento) + O-ring radial"),
                   (p.pmp_noz_f_t, p.pmp_f2_od, f"brida Ø{_f(p.pmp_f2_od, 1)} (pasa por el agujero del espejo)"),
                   (p.pmp_land_X0 - p.X_st1 - p.pmp_noz_f_t, round(p.D_bore / 2 + p.D_noz / 2 + 2 * p.pmp_noz_wall, 1), "cono exterior (Ø medio; pared 5)"),
                   (p.pmp_land_X1 - p.pmp_land_X0, 2 * p.pmp_land_R, f"resalte Ø{_f(2*p.pmp_land_R, 0)} f7 + O-ring")],
                  feats=[(p.pmp_noz_spigot / 2, f"ranura O-ring radial {_f(p.pmp_gl_width)} × {_f(p.pmp_gl_depth)} prof. (cs {_f(p.oring_cs)})"),
                         (p.pmp_noz_spigot + p.pmp_noz_cone_X1 - p.X_st1, f"fin del cono: Ø{_f(p.D_noz)} cilíndrico {_f(p.pmp_noz_cyl, 1)}"),
                         (p.pmp_noz_spigot + p.X_noz1 - p.X_st1, f"SALIDA Ø{_f(p.D_noz)} en X_noz1 = plano del espejo"),
                         (p.pmp_noz_spigot + p.pmp_or_X - p.X_st1, f"ranura O-ring {_f(p.pmp_or_width)} × {_f(p.pmp_or_depth)} prof.")],
                  notes=[f"Interior: Ø{_f(p.D_bore)} → Ø{_f(p.D_noz)} cono (semiángulo {_f(p.pmp_noz_half_angle, 1)}°) de X {_f(p.X_st1, 1)} a {_f(p.pmp_noz_cone_X1, 1)}; "
                         f"alojamiento esférico R{_f(p.pmp_sock_R)} centrado en el pivote (X {_f(p.X_steer_pivot, 1)}) hasta X {_f(p.pmp_sock_X1, 1)}; luego Ø{_f(2*p.pmp_steer_free_r, 1)}.",
                         f"Brida: 8 × Ø{_f(p.pmp_f2_bolt_hole, 1)} en Ø{_f(p.pmp_f2_bc, 2)} a {p.pmp_flange_ang0:g}° + k·45° — ISO 4762 M5 × {p.pmp_f2_screw_L:g} A4-70 + Tef-Gel, roscados en la carcasa (rosca engranada {_f(p.pmp_f2_screw_L - p.pmp_noz_f_t - p.pmp_stack_gap)}). "
                         f"Espiga {_f(p.pmp_noz_spigot)} +0,05/0 desde la cara de la brida: luz entre bridas {_f(p.pmp_stack_gap)} ± 0,05 medida con galgas.",
                         f"SERVICIO: brida Ø{_f(p.pmp_f2_od, 1)} < agujero del espejo Ø{_f(p.transom_hole_d, 1)} → sale por popa con el estator detrás (sin tocar el tren). "
                         f"Área de salida π/4·{_f(p.D_noz)}² = {_f(math.pi/4*p.D_noz**2, 0)} mm²."]))
    # ---------------- placa de espejo (contorno en el plano del espejo)
    R = p.pmp_tp_R
    h = p.z_noz + R - p.pmp_tp_zmin
    holes = [(R, p.z_noz - p.pmp_tp_zmin, 2 * p.pmp_tp_bore_R, f"agujero Ø{_f(2*p.pmp_tp_bore_R, 1)} H8 COAXIAL CON EL JET (inclinado {p.alpha:g}°)")]
    for a in p.pmp_tp_bolt_ang:
        y = R + p.pmp_tp_bc_R * math.cos(math.radians(a))
        z = p.z_noz - p.pmp_tp_zmin + p.pmp_tp_bc_R * math.sin(math.radians(a))
        holes.append((y, z, 6.4, f"M6 pasante ({a:g}°)"))
    made.append(T("P1-PMP-11", "pivot_bushing", "POM-C torneado (alt. iglidur con collar 8×12)",
                  [(p.pmp_lug_bush_L, p.pmp_lug_bush_od, f"Ø ext {_f(p.pmp_lug_bush_od, 0)} s6 · Ø int {_f(p.pmp_lug_bush_id, 1)} H9")],
                  notes=["2 piezas, una por oreja de la placa de espejo; el tornillo con hombro Ø8 e8 316 (DIRECCIÓN) gira dentro.",
                         "Medir el Ø interior tras 48 h en agua (hinchamiento del POM) [ESTIMADO]."]))
    made.append(PL("P1-PMP-09", "transom_plate", "Al 5083 8 mm + orejas 5083", 2 * R, h, p.pmp_tp_t, holes,
                   notes=[f"Contorno: círculo R{_f(R, 1)} centrado en el eje de la tobera en el espejo (z {_f(p.z_noz, 1)} sobre la quilla), "
                          f"recortado a z ≥ {_f(p.pmp_tp_zmin, 1)}.",
                          f"Cuello soldado/mecanizado coaxial con el jet: Ø ext {_f(2*p.pmp_collar_R, 0)}, hasta X {_f(p.pmp_collar_X1, 1)} (marco JET).",
                          f"Orejas ±Z_jet: |Z| {_f(p.pmp_lug_z0)}–{_f(p.pmp_lug_z1)}, ancho {p.pmp_lug_w:g}, extremo R{p.pmp_lug_w/2:g} en X {_f(p.X_steer_pivot, 1)}; "
                          f"alojamiento Ø{_f(p.pmp_lug_hole, 0)} H7 para el buje P1-PMP-11 (eje Z_jet, ⟂ al eje del jet).",
                          f"Va por fuera del espejo sobre la junta NBR 2 mm P1-PMP-10 + masilla butílica NO adhesiva (se desmonta en cada servicio); "
                          f"{len(p.pmp_tp_bolt_ang)} × M6 A4 con arandelas bonded de sellado + aislantes y contraplaca."]))
    return made
