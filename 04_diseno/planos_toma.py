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


def draw(p, H):
    out = []
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
            holes.append((x - X0, s * p.toma_bolt_y - Y0, 5.0, "M6 ciega prof. 8 (broca Ø5,0 × 9,5) — conducto"))
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
        "Soporte de rodamientos: 4 × ISO 10642 M8 × 35 A4-70 desde afuera (cabeza en Sikaflex), tuerca ISO 4032 A4 + arandela arriba, ~15 Nm con Tef-Gel.",
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
    ]
    out.append(H["plate"]("P1-INT-03", "rejilla", "AISI 316 (pletina 4 × 21 y 3 mm)", gx1 - gx0, 2 * gy, 3.0, holes, notes=notes))
    return out
