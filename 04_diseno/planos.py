#!/usr/bin/env python3
"""planos.py — Planos acotados (SVG) de las piezas torneadas / mecanizadas de P1.

Genera 04_diseno/planos/<ID>_<nombre>.svg con: perfil, cotas de diámetros y largos
(acumuladas desde la cara de referencia), detalles (agujeros, ranuras, roscas), rótulo con
material, tolerancias generales y fecha. Todas las cotas salen de params.py / sizing.json.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgwrite

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import params as P  # noqa: E402

OUT = HERE / "planos"
TOL = "Tolerancias generales ISO 2768-m; aristas matadas 0.3×45°; Ra 1.6 en asientos"


def title_block(dwg, W, H, pid, name, material, scale, notes):
    g = dwg.add(dwg.g(font_family="DejaVu Sans", font_size=11))
    x0, y0 = W - 430, H - 110
    g.add(dwg.rect((x0, y0), (420, 100), fill="none", stroke="black"))
    lines = [f"{pid}  {name}", f"Material: {material}", f"Escala {scale}  —  cotas en mm", TOL,
             "P1 propulsión — generado por 04_diseno/planos.py desde inputs.yaml"]
    for i, t in enumerate(lines):
        g.add(dwg.text(t, insert=(x0 + 8, y0 + 18 + 17 * i), font_size=12 if i == 0 else 10,
                       font_weight="bold" if i == 0 else "normal"))
    for i, n in enumerate(notes):
        g.add(dwg.text(f"• {n}", insert=(20, H - 110 + 15 * i), font_size=10))


def dim_h(dwg, x1, x2, y, text, off=0):
    dwg.add(dwg.line((x1, y), (x2, y), stroke="#0050a0", stroke_width=0.8))
    for x in (x1, x2):
        dwg.add(dwg.line((x, y - 4), (x, y + 4), stroke="#0050a0", stroke_width=0.8))
    dwg.add(dwg.text(text, insert=((x1 + x2) / 2, y - 3 - off), font_size=9, text_anchor="middle",
                     fill="#0050a0", font_family="DejaVu Sans"))


def turned(pid, name, material, segs, feats=None, notes=None, scale=None):
    """segs: lista de (largo, diámetro, etiqueta). feats: lista de (x_desde_izq, texto)."""
    feats = feats or []
    notes = notes or []
    Ltot = sum(s[0] for s in segs)
    Dmax = max(s[1] for s in segs)
    W, H = 1400, 620
    k = scale or min((W - 120) / Ltot, 220 / Dmax)
    dwg = svgwrite.Drawing(str(OUT / f"{pid}_{name}.svg"), size=(W, H))
    dwg.add(dwg.rect((0, 0), (W, H), fill="white"))
    x0, yc = 60, 200
    dwg.add(dwg.line((x0 - 20, yc), (x0 + Ltot * k + 20, yc), stroke="black", stroke_dasharray="12,3,3,3",
                     stroke_width=0.6))
    x = x0
    acc = 0.0
    for i, (L, D, lab) in enumerate(segs):
        dwg.add(dwg.rect((x, yc - D * k / 2), (L * k, D * k), fill="#e8e8e8", stroke="black", stroke_width=1))
        # cota de diámetro
        dwg.add(dwg.text(f"Ø{D:g}", insert=(x + L * k / 2, yc + 4), font_size=9, text_anchor="middle",
                         font_family="DejaVu Sans"))
        acc += L
        dim_h(dwg, x0, x + L * k, yc + Dmax * k / 2 + 22 + 16 * i, f"{acc:.1f}")
        if lab:
            dwg.add(dwg.text(lab, insert=(x + 2, yc - Dmax * k / 2 - 10 - 12 * (i % 3)), font_size=8,
                             font_family="DejaVu Sans", fill="#444"))
        x += L * k
    for (xf, txt) in feats:
        xx = x0 + xf * k
        dwg.add(dwg.line((xx, yc - Dmax * k / 2 - 50), (xx, yc), stroke="red", stroke_width=0.8))
        dwg.add(dwg.text(txt, insert=(xx + 3, yc - Dmax * k / 2 - 52), font_size=9, fill="red",
                         font_family="DejaVu Sans"))
    dim_h(dwg, x0, x0 + Ltot * k, 60, f"Largo total {Ltot:.1f}")
    title_block(dwg, W, H, pid, name, material, f"{k:.2f}:1 (pantalla)", notes)
    dwg.save()
    return OUT / f"{pid}_{name}.svg"


def plate(pid, name, material, w, h, t, holes, notes=None, outline=None):
    """Placa: rectángulo w×h (o contorno) + tabla de agujeros (x, y, Ø, texto)."""
    W, H = 1400, 900
    k = min(700 / w, 520 / h)
    dwg = svgwrite.Drawing(str(OUT / f"{pid}_{name}.svg"), size=(W, H))
    dwg.add(dwg.rect((0, 0), (W, H), fill="white"))
    ox, oy = 80, 80
    dwg.add(dwg.rect((ox, oy), (w * k, h * k), fill="#eeeeee", stroke="black"))
    for i, (x, y, d, txt) in enumerate(holes):
        cx, cy = ox + x * k, oy + (h - y) * k
        dwg.add(dwg.circle((cx, cy), d * k / 2, fill="white", stroke="black"))
        dwg.add(dwg.text(f"{i+1}", insert=(cx + d * k / 2 + 2, cy - 2), font_size=9, font_family="DejaVu Sans"))
    tx = ox + w * k + 40
    dwg.add(dwg.text("Agujeros (origen: esquina inferior izquierda)", insert=(tx, oy), font_size=11,
                     font_family="DejaVu Sans", font_weight="bold"))
    for i, (x, y, d, txt) in enumerate(holes):
        dwg.add(dwg.text(f"{i+1}: x={x:.1f}  y={y:.1f}  Ø{d:g}  {txt}", insert=(tx, oy + 18 + 15 * i), font_size=10,
                         font_family="DejaVu Sans"))
    dim_h(dwg, ox, ox + w * k, oy - 20, f"{w:.1f}")
    dwg.add(dwg.text(f"{h:.1f}", insert=(ox - 40, oy + h * k / 2), font_size=10, font_family="DejaVu Sans"))
    dwg.add(dwg.text(f"Espesor {t} mm", insert=(ox, oy + h * k + 25), font_size=11, font_family="DejaVu Sans"))
    title_block(dwg, W, H, pid, name, material, f"{k:.2f}:1 (pantalla)", notes or [])
    dwg.save()
    return OUT / f"{pid}_{name}.svg"


def main():
    p = P.load()
    OUT.mkdir(exist_ok=True)
    lay = p.layout
    sz = p.sz
    out = []
    # ---- eje DRV-01 ----
    import importlib.util
    spec = importlib.util.spec_from_file_location("sh", HERE / "piezas" / "P1-DRV-01_shaft.py")
    shm = importlib.util.module_from_spec(spec); spec.loader.exec_module(shm)
    st = shm.stations(p)
    segs = []
    for i in range(len(st) - 1):
        segs.append((st[i + 1][1] - st[i][1], st[i][2], st[i][0]))
    u0 = st[0][1]
    pin = sz["mech"]["shear_pin"]
    feats = [(p.s_prop - u0, f"agujero pasador Ø{pin['d_std_mm'] + 0.1:.1f} H8 pasante (centro de hélice)"),
             (lay["u_pulley_c"] - u0, "plano 1 mm para prisioneros de polea (2×, a 90°)"),
             (p.u_bush[2] - u0, "zona de buje inferior (Ra 0.8)")]
    out.append(turned("P1-DRV-01", "shaft", "AISI 316 (barra Ø16 h9)", segs, feats,
                      [f"Largo total {p.u_shaft_bot - p.u_shaft_top:.0f} mm; tramo Ø{p.shaft_jd:g} k5 continuo (rodamientos 6202 + polea re-mandrinada Ø{p.shaft_jd:g} H7)",
                       f"Montaje desde arriba: rodamiento A → separador DRV-10 → polea → separador DRV-09 → rodamiento B → tuerca M12×1.25 A4 autoblocante que aprieta la pila contra el hombro Ø{p.shaft_d:g}",
                       f"Asiento de hélice Ø{p.prop_seat_d:g} = bore de la hélice comprada: MEDIR antes de tornear; retención según la hélice",
                       f"Pasador de corte: {pin['material']} Ø{pin['d_std_mm']} — corta a {pin['Q_shear_Nm']:.1f} N·m",
                       "Radio de transición r = 1 mm en todos los escalones; sin rayas transversales (fatiga)"]))
    # ---- pernos ----
    zt = p.disc_z0 + p.disc_t + 4
    zb = p.boss_bot_z - 22
    out.append(turned("P1-MNT-07", "swivel_pin", "AISI 316", [(5, p.swivel_pin_d + 8, "cabeza"),
                      (zt - zb - 22, p.swivel_pin_d, "cuerpo (ajuste f7 en buje POM)"), (22, 16, "rosca M16×1.5")],
                      notes=["Tuerca M16 autoblocante A4 + arandela elástica (fricción de dirección regulable)"]))
    Lp = 2 * (p.cheek_y + p.cheek_t / 2) + 8
    out.append(turned("P1-MNT-08", "tilt_pin", "AISI 316", [(3.0, p.tilt_pin_d, ""), (1.1, 11.5, "ranura DIN 471"),
                      (Lp - 8.2, p.tilt_pin_d, "cuerpo h8"), (1.1, 11.5, "ranura DIN 471"), (3.0, p.tilt_pin_d, "")],
                      notes=["2 anillos de retención DIN 471 Ø12 inox", "Engrasar con grasa de PTFE al montar"]))
    # ---- bujes POM ----
    out.append(turned("P1-MNT-09", "swivel_bushing", "POM-C",
                      [(p.shelf_top_z - p.boss_bot_z, p.swivel_bush_od, f"interior Ø{p.swivel_pin_d + 0.2:g} H8")],
                      notes=["Ajuste en MNT-01: deslizante + gota de epoxi o pasador"]))
    out.append(turned("P1-MNT-10", "pivot_bushing", "POM-C", [(p.cradle_w, 20.0, f"interior Ø{p.tilt_pin_d + 0.25:g}")]))
    for pid, nm in (("P1-DRV-09", "spacer_b"), ("P1-DRV-10", "spacer_a")):
        spec = importlib.util.spec_from_file_location(nm, HERE / "piezas" / f"{pid}_{nm}.py")
        sm = importlib.util.module_from_spec(spec); spec.loader.exec_module(sm)
        a_, b_ = sm.span(p)
        out.append(turned(pid, nm, "AISI 316 (barra Ø20)", [(b_ - a_, sm.OD, f"interior Ø{p.shaft_jd + 0.1:g}")],
                          notes=["Caras paralelas ±0,02 (parte de la pila apretada)", "Apoya solo en el aro interior del rodamiento"]))
    out.append(turned("P1-DRV-06", "pulley_shaft_rebore", "Al (polea HTD-5M Dold comprada)",
                      [(p.pulley_w, p.pd_shaft, f"re-mandrinar bore a Ø{p.shaft_jd:g} H7")],
                      notes=["Centrar sobre el diámetro primitivo (dientes) con mordazas blandas; comprobar salto ≤ 0,05",
                             "Prisioneros M5 A4 a 90° sobre el plano del eje + fijador de retención metal-metal (no en PETG)"]))
    Ls = p.plate_u_fwd - p.bridge_u_aft
    out.append(turned("P1-DRV-03", "bridge_spacer", "AISI 316", [(Ls, 12.0, "interior Ø6.5")], notes=["Cantidad 2; caras paralelas ±0.05"]))
    out.append(turned("P1-PRP-04", "shear_pin", pin["material"], [(p.prop_seat_d + 6, pin["d_std_mm"], "")],
                      notes=[f"Corta a {pin['Q_shear_Nm']:.1f} N·m (2× torque máx. normal); llevar 5 de repuesto",
                             "Mismo metal que el eje (sin par galvánico); NO reemplazar por uno más grueso ni de acero templado"]))
    # ---- placas ----
    Li, Wi, Hi = p.esc_in
    Lo, Wo = Li + 36, Wi + 36
    spec = importlib.util.spec_from_file_location("eb", HERE / "piezas" / "P1-ELE-01_esc_box.py")
    eb = importlib.util.module_from_spec(spec); spec.loader.exec_module(eb)
    holes = [(x + Lo / 2, y + Wo / 2, 4.4, "pasante M4") for (x, y) in eb.lid_holes(p)]
    out.append(plate("P1-ELE-02", "esc_lid_heatsink", "Al 5052-H32 / 6082-T6", Lo, Wo, 4, holes,
                     ["Cara interior plana (pad térmico del ESC y del antichispa); agujeros M3 ciegos para ambos según el modelo comprado",
                      f"Cara exterior: disipador de aletas comprado, R_th ≤ {p.sz['thermal_esc']['heatsink']['R_hs_required_K_W']:.2f} K/W "
                      "(convección natural), pasta térmica; 4 tornillos M4 desde adentro con arandela de sellado (Dowty)",
                      "Montar la caja a la sombra; el disipador no debe tocar PETG"]))
    spec = importlib.util.spec_from_file_location("tp", HERE / "piezas" / "P1-HSG-07_tiller_plate.py")
    tp = importlib.util.module_from_spec(spec); spec.loader.exec_module(tp)
    W = p.cradle_w / 2
    w0 = -W
    holes = [(u - tp.U0, w - w0, 6.5, "M6 pasante (perno de tapa)") for u in (20.0, 80.0) for w in (-29.0, 29.0)]
    holes += [(70.0 - tp.U0, 0 - w0, 8.5, "M8 cáncamo")]
    holes += [(u - tp.U0, w - w0, 6.5, "M6 abrazadera de caña") for u in (30.0, 85.0) for w in (tp.W_TILLER - 12, tp.W_TILLER + 12)]
    out.append(plate("P1-HSG-07", "tiller_plate", "Al 6082-T6", tp.U1 - tp.U0, tp.W_TILLER + 16 - w0, tp.T_PL, holes,
                     ["Aristas redondeadas r 3; anodizar o pintar", "Aislar del inox con arandelas de nylon + Tef-Gel"]))
    print(f"planos: {len(out)} SVG en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
