"""PRB-P1.3 — Tuerca cautiva M6 en bolsillo transversal (PENDIENTES_GASPAR §P1.3).

La probeta es un RECORTE de la mejilla real P1-MNT-04 alrededor del perno M6 con el ligamento
lateral más delgado (el más crítico), más un agarre con agujero Ø12,5 (perno M12 / grillete)
para tirar con el dinamómetro. Altura del bolsillo h, ancho y alto del bolsillo y Ø del perno se
LEEN de la pieza (escaneo del sólido), no se copian: si MNT-04 cambia, la probeta cambia.
Se imprime igual que la mejilla (META.print_rot de MNT-04: espesor = Z).
"""
import math

from cadlib import *  # noqa: F401,F403
from _probelib import (cyl_faces, scan, est_row, rx_float, fs_target, label_on_plane, Plane, petg,
                       LABEL_DEPTH)

TEST = "P1.3"
SRC = "P1-MNT-04"
GRIP_D = 12.5          # agujero del agarre (perno M12 A4 como pasador) [SUPUESTO]
GRIP_H = 34.0          # alto del agarre [SUPUESTO: borde 10,75 mm sobre el agujero]
ABOVE = 16.0           # material sobre el bolsillo antes del agarre [SUPUESTO]
HALF_W = 26.0          # media ventana de recorte en x [SUPUESTO]


def geometry(ctx):
    """Lee de MNT-04: base z0, pernos M6, h del bolsillo, alto/ancho del bolsillo, ligamentos."""
    part = ctx.built(SRC)
    bb = part.bounding_box()
    z0 = bb.min.Z
    bolts = {}
    for cf in cyl_faces(part):
        if cf["hole"] and abs(abs(cf["d"].Z) - 1) < 1e-3 and 3.0 < cf["r"] < 3.6:
            bolts[(round(cf["loc"].X, 3), round(cf["loc"].Y, 3))] = cf["r"]
    res = []
    for (x, y), r in sorted(bolts.items()):
        tz = scan(part, (x + r + 0.7, y, z0 + 0.05), (0, 0, 1), 45.0, step=0.1)
        outs = [s for s, now_in in tz if not now_in]
        ins = [s for s, now_in in tz if now_in]
        if not outs:
            continue
        h = outs[0] + 0.05
        hs = next(s for s in ins if s > outs[0]) - outs[0]
        zm = z0 + h + hs / 2
        lig = []
        half = []
        for sx in (1, -1):
            tx = scan(part, (x, y, zm), (sx, 0, 0), 60.0, step=0.1)
            first_in = next(s for s, now_in in tx if now_in)
            exit_ = next((s for s, now_in in tx if (not now_in) and s > first_in), 60.0)
            half.append(first_in)
            lig.append(exit_ - first_in)
        res.append(dict(x=x, y=y, r=r, h=round(h, 2), slot_h=round(hs, 2), slot_w=round(sum(half), 2),
                        lig_min=round(min(lig), 2), z0=z0))
    if not res:
        raise RuntimeError("P1.3: no se encontraron pernos M6 con bolsillo en MNT-04")
    return min(res, key=lambda g: g["lig_min"]), res, bb


def build(p, ctx):
    g, _all, bb = geometry(ctx)
    part = ctx.built(SRC)
    x, z0 = g["x"], g["z0"]
    zc = g["h"] + g["slot_h"] + ABOVE
    cut = part & box(x - HALF_W, x + HALF_W, bb.min.Y - 1, bb.max.Y + 1, z0 - 1, z0 + zc)
    cb = cut.bounding_box()
    xm = 0.5 * (cb.min.X + cb.max.X)
    grip = box(cb.min.X, cb.max.X, cb.min.Y, cb.max.Y, z0 + zc - 1.0, z0 + zc + GRIP_H)
    grip = grip - cyl_y(GRIP_D / 2, cb.min.Y - 1, cb.max.Y + 1, x=xm, z=z0 + zc + GRIP_H / 2)
    pl = Plane(origin=(xm, cb.max.Y, z0 + zc + GRIP_H - 6.0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    s = cut + grip + label_on_plane(f"M6 h{g['h']:g}", pl, size=5.0)
    rot = ctx.part(SRC).META["print_rot"]
    meta = dict(id="P1.3", name="tuerca_cautiva_M6",
                desc=f"Recorte de {SRC} en el perno x={x:g} (ligamento mín. {g['lig_min']:.1f} mm), bolsillo "
                     f"transversal a h={g['h']:g} mm, {g['slot_w']:g}×{g['slot_h']:g} mm; agarre Ø{GRIP_D}",
                test=TEST, profile="estructural", qty=3, solid_frac=ctx.part(SRC).META.get("solid_frac", 1.0),
                orientation=f"Como {SRC} (print_rot {tuple(rot)}): espesor de mejilla = Z; perno y tirón en el plano de capas.")
    return [(meta, to_print(s, rot))]


def _h_model(ctx):
    r = est_row(ctx, "P1-MNT-04", "Tuerca cautiva")
    return r, rx_float(r"h\s*=\s*([\d.,]+)\s*mm", r["model"] if r else "", 18.0)


def checks(p, ctx, parts):
    g, _all, _bb = geometry(ctx)
    _r, hm = _h_model(ctx)
    return [("h del bolsillo (MNT-04 escaneado) = h de structural.py [mm]", g["h"], hm, "="),
            ("alto del bolsillo ≥ altura de tuerca M6 ISO 4032 [mm]", g["slot_h"], NUT_M[6], ">="),
            ("ancho del bolsillo ≥ entrecaras M6 [mm]", g["slot_w"], NUT_AF[6], ">="),
            ("espesor de la probeta (sin relieve del rótulo) = espesor de mejilla [mm]",
             parts["P1.3"].bounding_box().max.Z - parts["P1.3"].bounding_box().min.Z - LABEL_DEPTH, p.cheek_t, "=")]


def criterios(p, ctx):
    g, allb, _bb = geometry(ctx)
    r, hm = _h_model(ctx)
    t = float(p.cheek_t)
    fs = fs_target(ctx)
    F_bolt = r["sigma_MPa"] * 2 * t * hm if r else None             # τ = F/(2·t·h) → F
    pet, f = petg(ctx)
    A_shear = 2 * t * g["h"]
    A_bear = 0.866 * NUT_AF[6] ** 2 - math.pi / 4 * (2 * g["r"]) ** 2
    F_shear = 0.5 * pet["sigma_t_xy_mpa"] * A_shear
    F_bear = pet["sigma_t_xy_mpa"] * A_bear
    return {
        "F_perno_N": None if F_bolt is None else round(F_bolt, 1),
        "fuente_carga": "resultados/estructural.json: fila P1-MNT-04 'Tuerca cautiva…', F = τ·2·t·h",
        "FS": fs, "umbral_N": None if F_bolt is None else round(fs * F_bolt, 0),
        "umbral_PENDIENTES_N": 2100.0,
        "h_mm": g["h"], "bolsillo_mm": [g["slot_w"], g["slot_h"]], "ligamento_min_mm": g["lig_min"],
        "pernos_escaneados": allb,
        "prediccion": {
            "F_corte_seco_N": round(F_shear, 0),
            "F_aplastamiento_bajo_tuerca_N": round(F_bear, 0),
            "base": "[ESTIMADO: τ_ult ≈ 0,5·σt,XY y σ_aplast ≈ σt,XY (47 MPa, research/R05 S1), área de apoyo = "
                    "hexágono M6 − Ø del perno; probablemente cede primero el apoyo bajo la tuerca]",
        },
        "ensayo": "Varilla roscada M6 A4 atornillada a la tuerca desde la cara de apoyo (z0); agarre con perno M12 "
                  "como pasador en una horquilla fija; tirar con dinamómetro + palanca 5:1. 3 probetas.",
        "pasa_si": f"Las 3 resisten ≥ max(umbral, 2,1 kN de PENDIENTES) sin arrancar ni fisurar (lupa 10×).",
    }
