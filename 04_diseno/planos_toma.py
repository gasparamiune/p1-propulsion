"""planos_toma.py — planos acotados (SVG) del grupo TOMA: placa base P1-INT-02 y rejilla P1-INT-03.
La geometría 3D (cuña de la rampa, perfil de las barras) va en el STEP; acá van agujeros, roscas,
contornos y notas de fabricación."""
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


def _flange_view(dwg, cx, cy, k, title, od, bore, bc, n, hole_d, ang0, rings=(), hole_txt=""):
    """Vista de frente de una brida: Ø exterior, agujero, círculo de bulones con n agujeros a ang0 + k·360/n."""
    g = dwg.add(dwg.g(font_family="DejaVu Sans", font_size=10))
    g.add(dwg.text(title, insert=(cx - od * k / 2, cy - od * k / 2 - 14), font_size=12, font_weight="bold"))
    g.add(dwg.circle((cx, cy), od * k / 2, fill="#eeeeee", stroke="black"))
    for (d, lab, dash) in rings:
        g.add(dwg.circle((cx, cy), d * k / 2, fill="none", stroke="#0050a0", stroke_dasharray="4,2" if dash else "none"))
    g.add(dwg.circle((cx, cy), bore * k / 2, fill="white", stroke="black"))
    g.add(dwg.circle((cx, cy), bc * k / 2, fill="none", stroke="black", stroke_dasharray="10,3,2,3", stroke_width=0.5))
    for i in range(n):
        a = math.radians(ang0 + 360.0 * i / n)
        hx, hy = cx + bc / 2 * k * math.cos(a), cy - bc / 2 * k * math.sin(a)
        g.add(dwg.circle((hx, hy), max(hole_d * k / 2, 1.5), fill="white", stroke="black"))
    g.add(dwg.line((cx - od * k / 2 - 10, cy), (cx + od * k / 2 + 10, cy), stroke="black", stroke_width=0.4, stroke_dasharray="8,2,2,2"))
    g.add(dwg.line((cx, cy - od * k / 2 - 10), (cx, cy + od * k / 2 + 10), stroke="black", stroke_width=0.4, stroke_dasharray="8,2,2,2"))
    y = cy + od * k / 2 + 18
    lines = [f"Ø ext {od:.1f}  ·  agujero Ø{bore:.1f}", f"{n} × {hole_txt} en Ø{bc:.2f} a {ang0:g}° + k·{360 / n:g}° (desde +Y hacia +Z)"]
    lines += [lab for (_, lab, _) in rings]
    for t in lines:
        g.add(dwg.text(t, insert=(cx - od * k / 2, y)))
        y += 13


def draw_conducto(p, H):
    """Plano de P1-INT-01 (conducto soldado): interfaces críticas a mecanizar después de soldar (auditoría Pass 3 H9)."""
    import svgwrite
    OUT = H["OUT"]
    pid, name = "P1-INT-01", "conducto"
    W, Hh = 1500, 980
    path = OUT / f"{pid}_{name}.svg"
    dwg = svgwrite.Drawing(str(path), size=(W, Hh))
    dwg.add(dwg.rect((0, 0), (W, Hh), fill="white"))
    k = 1.6
    _flange_view(dwg, 250, 260, k, "A — Brida de la bomba (cara de popa, plano X_duct_out)",
                 p.pump_flange_od, p.toma_D_out, p.pump_flange_bc, p.pump_flange_n, p.pump_flange_bolt + p.bolt_clr,
                 p.pmp_flange_ang0,
                 rings=[(p.pmp_f1_spigot_d, f"rebaje de centraje Ø{p.pmp_f1_spigot_d:g} H7 × {p.pmp_f1_recess_h:g} prof. (espigón h6 de P1-PMP-01)", False),
                        (2 * (p.pmp_gl_r_in + p.pmp_gl_width), f"zona del O-ring de cara de P1-PMP-01 (Ø{2 * p.pmp_gl_r_in:.1f}–Ø{2 * (p.pmp_gl_r_in + p.pmp_gl_width):.1f}): Ra 1,6, sin rayas radiales", True)],
                 hole_txt=f"Ø{p.pump_flange_bolt + p.bolt_clr:g} pasantes (M6 A4 + tuerca de este lado)")
    k2 = 3.0
    ang_s = p.tom_seal_bolt_ang0
    _flange_view(dwg, 760, 230, k2, "B — Buje del sello (cara de proa, plano S_seal ⟂ al eje)",
                 p.seal_boss_od, p.seal_spigot_d, p.seal_bc, 4, 5.0, ang_s,
                 rings=[(p.toma_tube_id, f"pasaje del eje Ø{p.toma_tube_id:g} (tubo Ø{p.toma_tube_od:g} × {(p.toma_tube_od - p.toma_tube_id) / 2:g})", True)],
                 hole_txt=f"M6 ciegos prof. rosca 12 (broca Ø5,0 × 14) — alojamiento Ø{p.seal_spigot_d:g} H8 × {p.toma_cbore_L:g}")
    k3 = 1.1
    _flange_view(dwg, 1230, 230, k3, "C — Brida de la chimenea (cara superior, horizontal)",
                 p.toma_chim_fl_od, p.toma_chim_id, p.toma_chim_bc, 4, 5.0, 45.0,
                 hole_txt="M6 ciegos prof. 12 (tapa P1-INT-04)")
    from params import jet_to_boat
    xs, ys, zs = jet_to_boat(p, -p.S_seal, 0.0, 0.0)
    xf, yf, zf = jet_to_boat(p, p.X_duct_out, 0.0, 0.0)
    g = dwg.add(dwg.g(font_family="DejaVu Sans", font_size=11))
    notes = [
        "MECANIZAR DESPUÉS DE SOLDAR, en UNA atada (conjunto soldado fijado por la brida inferior): cara A + rebaje H7 + 8 agujeros, cara B + Ø42 H8 + 4 × M6, cara C.",
        f"Coaxialidad: rebaje A Ø{p.pmp_f1_spigot_d:g} H7 ↔ alojamiento B Ø{p.seal_spigot_d:g} H8 ≤ Ø0,05 respecto del eje del jet (inclinado α = {p.alpha:g}° respecto de la placa base); "
        "caras A y B ⟂ al eje ≤ 0,05; planitud de la brida inferior 0,1 (apoya en la placa base con el cordón NBR).",
        f"Ubicación (marco BOTE, origen cara exterior del espejo / crujía / quilla): centro de la cara A en x = {xf:.1f}, z = {zf:.1f}; "
        f"centro de la cara B en x = {xs:.1f}, z = {zs:.1f}; eje de la chimenea en x = {p.toma_chim_x:.1f}, cara C a z = {p.toma_chim_top:.0f}.",
        f"Fase de los agujeros de A: {p.pmp_flange_ang0:g}° + k·45° desde +Y_jet (babor) hacia +Z_jet: ninguno en ±Y/±Z (coordinado con P1-PMP-01). "
        f"B: {ang_s:g}° + k·90°.",
        f"Pasaje: rampa C2 (ver STEP P1-INT-01) hasta Ø{p.toma_D_out:.2f} en la cara A (= labio de P1-PMP-01, sin escalón); chapa 5083 de {p.toma_t:g} mm, cordones continuos estancos.",
        "Ensayos antes de anodizar/pintar: estanqueidad del conjunto soldado con aire 0,3 bar + agua jabonosa (S-WELD-INT); hidrostática con la bomba a 0,3 MPa (06 §3).",
        f"Ranuras de la rejilla en el bloque del labio y bolsillos: luz {p.toma_iso_gap:g} mm por lado para la camisa de PTFE (aislación 316 ↔ 5083).",
        "Material Al 5083-H111 (mismo que el casco y la placa base: sin par galvánico). Tolerancias generales ISO 2768-m; soldadura ISO 10042 nivel C [ESTIMADO].",
    ]
    y = 560
    for t in notes:
        g.add(dwg.text("• " + t, insert=(20, y)))
        y += 18
    H["title_block"](dwg, W, Hh, pid, "Conducto de la toma (soldado) — interfaces mecanizadas", "Al 5083-H111 soldado TIG/MIG", "—",
                     ["Geometría completa del pasaje en 04_diseno/step/P1-INT-01_conducto.step (manda el STEP)."])
    dwg.save()
    return path


def draw(p, H):
    out = []
    out.append(draw_conducto(p, H))
    m1, m2, m3 = _mod("P1-INT-01_conducto"), _mod("P1-INT-02_placa_base"), _mod("P1-INT-03_rejilla")
    # ---------------- placa base ----------------
    rw = p.toma_rim_w
    X0, Y0 = p.toma_plate_x0 - rw, -(p.toma_plate_y + rw)
    w = (p.toma_plate_x1 + rw) - X0
    h = 2 * (p.toma_plate_y + rw)
    holes = []
    for (x, y) in m2.hull_bolts(p):
        holes.append((x - X0, y - Y0, p.toma_hull_bolt + p.bolt_clr, "pasante, ala → casco (M6 ISO 10642 A4-70 + tuerca autofr.)"))
    for x in m1.bolt_x(p):
        for s in (1, -1):
            holes.append((x - X0, s * p.toma_bolt_y - Y0, 5.0, f"M6 ciega rosca {p.toma_m6_thread_L:g} (broca Ø5,0 × {p.toma_m6_depth:g}) — conducto, {p.toma_m6_torque_Nm:g} N·m + Loctite 243"))
    for (x, y) in p.brg_bracket_holes:
        holes.append((x - X0, y - Y0, 8.4, "Ø8,4 pasante + avellanado 90° Ø16,4 ABAJO — ISO 10642 M8 A4 (soporte de rodamientos)"))
    for (x, y) in m2.tie_screws(p):
        holes.append((x - X0, y - Y0, 4.2, "M5 ciega desde ABAJO prof. 5 — tirante de la rejilla"))
    W2 = p.W_open / 2
    notes = [
        f"Al 5083-H111 chapa 10 mm. Cuerpo enrasado {p.toma_plate_x1 - p.toma_plate_x0:.1f} × {2*p.toma_plate_y:.0f} (R{p.toma_plate_r:.0f}); "
        f"ala z {p.toma_rim_z0:.1f}–10 (rebaje 4,5 desde abajo) de {rw:.0f} mm alrededor.",
        f"Origen del plano = esquina popa-estribor del ala; x del bote = x_plano + {X0:.1f}; y del bote = y_plano − {-Y0:.1f}.",
        f"Abertura: costados en y_bote = ±{W2:.1f}, de x_bote {p.toma_x_lb_aft:.1f} (alojamiento del labio) a {p.toma_x_j:.1f}; "
        f"a proa, CUÑA de la rampa fresada 3D hasta la tangencia x_bote {p.x_tan:.1f} (ver STEP P1-INT-02).",
        f"Bolsillos del tirante de la rejilla (abajo): x_bote {p.toma_x_bf:.1f} ± {p.toma_tie_w/2 + 0.3:.1f}, |y| {W2 - 1:.1f}–{W2 + 12.3:.1f}, prof. {p.toma_strap_t + 0.3:.1f}.",
        "Cara superior plana 0,1 mm en la huella del soporte de rodamientos (x_bote "
        f"{p.brg_bracket_x0:.1f}–{p.brg_bracket_x1:.1f}); cara inferior lisa, aristas exteriores redondeadas R1 (flujo).",
        "Montaje: Sikaflex-291i en el ala y en la luz de 0,5 mm del recorte [ESTIMADO R05 S36]; enrasar por fuera; Tef-Gel en tornillería A4.",
        f"Soporte de rodamientos: 4 × ISO 10642 M8 × 35 A4-70 desde afuera (cabeza en Sikaflex), tuerca ISO 4032 A4 + arandela ISO 7093 arriba, {p.drv_nut_torque_Nm:g} N·m con Tef-Gel (FS del avellanado ≥ 2, structural).",
        f"Brida del conducto: M6 A4 a {p.toma_m6_torque_Nm:g} N·m (F_v {p.toma_m6_Fpre_N:.0f} N) + Loctite 243 — rosca en Al: NO usar el par de tabla de acero (structural_toma, auditoría H6).",
    ]
    out.append(H["plate"]("P1-INT-02", "placa_base", "Al 5083-H111 (10 mm)", w, h, 10.0, holes, notes=notes))
    # ---------------- rejilla ----------------
    xa, xf = m3.bar_x_range(p)
    gx0 = p.toma_strap_x[0]
    gx1 = p.toma_x_bf + p.toma_tie_w / 2
    gy = W2 + 12.0
    holes = []
    for y in m1.strap_screw_y(p):
        holes.append((0.5 * sum(p.toma_strap_x) - gx0, y + gy, 5.5, "Ø5,5 avellanado 90° Ø10,4 — M5 ISO 10642 A4 al bloque del labio"))
    for (x, y) in m2.tie_screws(p):
        holes.append((x - gx0, y + gy, 5.5, "Ø5,5 avellanado 90° Ø10,4 — M5 ISO 10642 A4 a la placa base"))
    for yb in p.toma_bar_y:
        holes.append(((xa + xf) / 2 - gx0, yb + gy, p.grille_bar_d, f"barra en y_bote {yb:+.1f}"))
    notes = [
        f"{p.grille_bars} pletinas AISI 316 {p.grille_bar_d:.0f} × {p.toma_bar_h:.0f}, de x_bote {xa:.1f} a {xf:.1f}, paso {p.toma_bar_gap + p.grille_bar_d:.1f}, luz {p.toma_bar_gap:.1f} mm.",
        "Sección perfilada: canto inferior redondo R2 (lado casco), últimos 6 mm afinados a 1,6 mm. Cara inferior enrasada con el fondo (z = 0).",
        f"Alto {p.toma_bar_h:.0f} mm hasta el labio + 1; hacia proa sigue el techo − 2 mm y APOYA en la cuña de la placa (x_bote ≥ {p.toma_x_j:.1f}): cortar con la plantilla del STEP.",
        f"Pletina de popa 316 3 × {p.toma_strap_x[1]-p.toma_strap_x[0]:.0f} × {2*(W2-4):.0f}; tirante de proa 316 3 × {p.toma_tie_w:.0f} × {2*gy:.0f}; barras soldadas TIG a ambas.",
        "Decapar y pasivar después de soldar; sin rebabas (R10a §8.6: escalón ≤ 2 mm). Origen del plano: x_bote = x + "
        f"{gx0:.1f}, y_bote = y − {gy:.1f}.",
        "Desmontaje desde afuera: 4 × M5 A4 (Tef-Gel), con el sistema DESARMADO (R10a §0).",
        f"Luz ≤ {p.toma_gap_max:g} mm: una varilla Ø13 no pasa (R10a §8.6). AISLACIÓN 316 ↔ 5083: camisa/cinta de PTFE en ranuras y bolsillos (luz {p.toma_iso_gap:g}), "
        f"cinta PTFE {p.toma_bar_iso_t:g} en el canto que apoya en la cuña, arandelas cónicas de nylon bajo los M5; > 1 kΩ 316 ↔ 5083 al montar.",
    ]
    out.append(H["plate"]("P1-INT-03", "rejilla", "AISI 316 (pletina 4 × 21 y 3 mm)", gx1 - gx0, 2 * gy, 3.0, holes, notes=notes))
    return out
