#!/usr/bin/env python3
"""planos.py — Planos acotados (SVG) de las piezas torneadas / mecanizadas del waterjet P1-J.

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
             "P1-J waterjet — generado por 04_diseno/planos.py desde inputs.yaml"]
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
    """Cada subsistema dibuja sus piezas torneadas/mecanizadas en 04_diseno/planos_<grupo>.py con
    draw(p, H) donde H = {"turned": turned, "plate": plate, "OUT": OUT}. Devuelve lista de rutas."""
    import importlib.util
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    p = P.load()
    H = {"turned": turned, "plate": plate, "OUT": OUT, "title_block": title_block, "dim_h": dim_h}
    made = []
    for f in sorted(HERE.glob("planos_*.py")):
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        made += list(mod.draw(p, H) or [])
    print(f"planos: {len(made)} SVG en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
