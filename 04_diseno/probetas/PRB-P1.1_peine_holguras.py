"""PRB-P1.1 — Peine de holguras (PENDIENTES_GASPAR §P1.1).

Agujeros Ø(d + c) y pernos Ø(d − c) para cada diámetro nominal d de las piezas metálicas/POM que
entran en piezas impresas, con c ∈ {0,15; 0,20; 0,25; 0,30} (+ geometry.clearance_mm si difiere).
Rótulos en relieve: "Ø<d>" por fila y "+.15"… bajo cada agujero ("-.15"… bajo cada perno).

  P1.1A, P1.1B…  agujeros de EJE VERTICAL (redondos en XY: caso de los alojamientos de pie)
  P1.1P…         pernos impresos de eje vertical (error dimensional exterior; ajuste impreso–impreso)
  P1.1H          agujeros HORIZONTALES (caen por voladizo arriba) para los Ø que las piezas reales
                 imprimen acostados — se detectan escaneando las piezas en orientación de impresión.

Los diámetros salen de la lista de la tarea ∪ params (perno de basculación/dirección, eje, muñón,
tubo de cola, tubo de caña, bujes); el escaneo de las piezas también se guarda en el manifest
("ajustes_en_piezas") para la tabla de 05_fabricacion.md.
"""
from cadlib import *  # noqa: F401,F403
from _probelib import label, label_on_plane, fmt_mm, cyl_faces, Plane, fuse_all, cut_all

TEST = "P1.1"
NOMINALES_BASE = [12, 15, 16, 20, 25, 30, 40]   # [VERIFICADO: PENDIENTES_GASPAR §P1.1 + tarea de fabricación]
HOLGURAS_BASE = [0.15, 0.20, 0.25, 0.30]         # [VERIFICADO: PENDIENTES_GASPAR §P1.1]
WALL = 4.0          # pared del anillo [SUPUESTO: ≥ geometry.min_wall_mm; ~6 perímetros + relleno]
H_RING = 8.0        # largo del agujero [SUPUESTO: suficiente para juzgar juego radial]
H_PIN = 10.0        # altura útil del perno (> H_RING: atraviesa el anillo)
TAB_T = 2.0         # espesor de la franja de rótulos
TAB_W = 9.0         # ancho de la franja de rótulos
COL_W = 16.0        # columna del rótulo de fila "Ø<d>"
GAP_PIN = 6.0       # luz entre pernos
MAX_PLATE = 200.0   # [SUPUESTO: 210 útiles − 10 de margen para la falda]
H_THICK = 6.0       # espesor de la pared con agujeros horizontales (largo del agujero) [SUPUESTO]
FOOT = 10.0         # pie de apoyo de la pared horizontal a cada lado


def nominales(p):
    extra = (p.tilt_pin_d, p.swivel_pin_d, p.shaft_d, p.shaft_jd, p.tube_od, p.tiller_tube_od,
             p.bush_od, p.swivel_bush_od)
    return sorted({float(d) for d in NOMINALES_BASE} | {float(d) for d in extra})


def holguras(p):
    return sorted({round(c, 3) for c in HOLGURAS_BASE + [float(p.clr)]})


def holguras_d(p, ctx, d, eje=None):
    """Holguras base ∪ las que el CAD usa para ese Ø (escaneo de piezas; incluye ajustes a presión)."""
    extra = {r["holgura_cad"] for r in ajustes_en_piezas(p, ctx)
             if r["d_nom"] == d and (eje is None or r["eje_impresion"] == eje)}
    return sorted({round(c, 3) for c in holguras(p)} | {round(c, 3) for c in extra})


def _dlabel(d):
    return f"Ø{d:g}"


# ---------------------------------------------------------------------------
# filas
# ---------------------------------------------------------------------------
def hole_row(d, cs):
    """Fila de anillos (agujero vertical Ø d+c) con franja de rótulos al frente (−Y).
    Devuelve (sólido, alto_y, largo_x); origen: x=0 borde izq., y=0 eje de los agujeros."""
    ids = [d + c for c in cs]
    od = max(ids) + 2 * WALL
    pitch = max(ids) + WALL
    x0 = COL_W + od / 2
    xs = [x0 + i * pitch for i in range(len(cs))]
    yl = -od / 2 - TAB_W / 2
    body = fuse_all([box(0, xs[-1] + od / 2, -od / 2 - TAB_W, 0, 0, TAB_T)]            # franja
                    + [cyl_z(od / 2, 0, H_RING, x=x) for x in xs])
    body = cut_all(body, [cyl_z(idd / 2, -1, H_RING + 1, x=x) for x, idd in zip(xs, ids)])
    labels = [label(_dlabel(d), COL_W / 2 + 0.5, -od / 4 - TAB_W / 2, TAB_T, size=4.5)]
    labels += [label(fmt_mm(c), x, yl, TAB_T, size=4.5) for x, c in zip(xs, cs)]
    return fuse_all([body] + labels), od + TAB_W, xs[-1] + od / 2


def pin_row(d, cs):
    """Fila de pernos Ø(d−c) de pie sobre una base con rótulos. Huecos (pared WALL) si d ≥ 20."""
    ods = [d - c for c in cs]
    x0 = COL_W + d / 2 + 2
    xs = [x0 + i * (d + GAP_PIN) for i in range(len(cs))]
    y_top = d / 2 + 2
    base = box(0, xs[-1] + d / 2 + 2, -d / 2 - TAB_W - 1, y_top, 0, TAB_T)
    pins = [cyl_z(od / 2, TAB_T - 0.01, TAB_T + H_PIN, x=x) for x, od in zip(xs, ods)]
    body = fuse_all([base] + pins)
    if d >= 20:
        body = cut_all(body, [cyl_z(od / 2 - WALL, TAB_T + 1.0, TAB_T + H_PIN + 1, x=x) for x, od in zip(xs, ods)])
    yl = -d / 2 - TAB_W / 2 - 0.5
    labels = [label(_dlabel(d), COL_W / 2 + 0.5, yl + 2, TAB_T, size=4.5)]
    labels += [label(fmt_mm(-c), x, yl, TAB_T, size=4.5) for x, c in zip(xs, cs)]
    return fuse_all([body] + labels), (y_top + d / 2 + TAB_W + 1), xs[-1] + d / 2 + 2


def stack(rows):
    """Apila filas en +Y (cada fila solapa 1 mm a la anterior) + lomo izquierdo que las une."""
    placed = []
    y = 0.0
    ymax = 0.0
    for solid, h, lx, ytop in rows:
        # ytop = extensión de la fila por encima de su origen (+Y); h = alto total
        off = y + (h - ytop)
        placed.append(Pos(0, off, 0) * solid)
        y = off + ytop - 1.0
        ymax = off + ytop
    return fuse_all(placed + [box(0, 3, 0, ymax, 0, TAB_T)])


def plates(rows_spec, build_row):
    """Agrupa filas en placas de ≤ MAX_PLATE (greedy por diámetro creciente)."""
    groups, cur, hcur = [], [], 0.0
    for d, cs in rows_spec:
        solid, h, lx = build_row(d, cs)
        if cur and hcur + h - 1.0 > MAX_PLATE:
            groups.append(cur)
            cur, hcur = [], 0.0
        cur.append((d, solid, h, lx))
        hcur += h - (1.0 if len(cur) > 1 else 0.0)
    if cur:
        groups.append(cur)
    return groups


# ---------------------------------------------------------------------------
# escaneo de las piezas reales: ¿qué ajustes hay y con qué eje se imprimen?
# ---------------------------------------------------------------------------
def ajustes_en_piezas(p, ctx, c_min=-0.16, c_max=0.45):
    return ctx.cached(("P1.1", "ajustes"), lambda: _ajustes(p, ctx, c_min, c_max))


def _ajustes(p, ctx, c_min, c_max):
    noms = nominales(p)
    rows = {}
    for pid, m in sorted(ctx.parts.items()):
        if m.META.get("process") != "impresa":
            continue
        try:
            q = to_print(ctx.built(pid), m.META["print_rot"])
        except Exception as e:                                       # pragma: no cover
            ctx.notes.append(f"P1.1: no se pudo escanear {pid}: {e}")
            continue
        for cf in cyl_faces(q):
            if not cf["hole"]:
                continue
            D = 2 * cf["r"]
            for d in noms:
                c = D - d
                if c_min - 1e-6 <= c <= c_max + 1e-6:
                    az = abs(cf["d"].Z)
                    eje = "vertical" if az > 0.98 else ("horizontal" if az < 0.2 else "inclinado")
                    key = (pid, d, round(D, 3), eje)
                    rows[key] = {"id": pid, "d_nom": d, "D_cad": round(D, 3), "holgura_cad": round(c, 3),
                                 "eje_impresion": eje}
    return list(rows.values())


def diam_horizontales(p, ctx):
    aj = ajustes_en_piezas(p, ctx)
    ds = sorted({r["d_nom"] for r in aj if r["eje_impresion"] == "horizontal" and r["holgura_cad"] > 0})
    if not ds:
        ctx.notes.append("P1.1H: el escaneo no halló agujeros horizontales con holgura; se usa [tilt_pin_d, tube_od]")
        ds = sorted({float(p.tilt_pin_d), float(p.tube_od)})
    return ds, aj


def horizontal_wall(p, ds, csd):
    """Paredes de pie (espesor H_THICK en Y) con agujeros horizontales (eje Y), rótulos en la cara −Y.
    csd: {d: [holguras]}. Cada bloque tiene la altura de su Ø."""
    def wid(d):
        cs = csd[d]
        return len(cs) * (d + max(cs) + WALL) + WALL

    groups, cur, wcur = [], [], 0.0
    for d in ds:
        w = wid(d)
        if cur and wcur + w > MAX_PLATE:
            groups.append(cur)
            cur, wcur = [], 0.0
        cur.append((d, w))
        wcur += w
    if cur:
        groups.append(cur)
    blocks, holes, labels = [], [], []
    y0 = FOOT
    for g in groups:
        x = 0.0
        for d, w in g:
            cs = csd[d]
            hmax = d + max(cs) + 2 * WALL + 9.0
            blocks.append(box(x, x + w, y0, y0 + H_THICK, 0, hmax))
            zc = WALL + (d + max(cs)) / 2 + 2.0
            for i, c in enumerate(cs):
                xc = x + WALL + (d + max(cs)) / 2 + i * (d + max(cs) + WALL)
                holes.append(cyl_y((d + c) / 2, y0 - 1, y0 + H_THICK + 1, x=xc, z=zc))
                pl = Plane(origin=(xc, y0, hmax - 4.5), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
                labels.append(label_on_plane(fmt_mm(c), pl, size=4.0))
            pl = Plane(origin=(x + w / 2, y0 + H_THICK, hmax - 4.5), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
            labels.append(label_on_plane(f"Ø{d:g} H", pl, size=4.5))
            x += w
        y0 += H_THICK + 2 * FOOT
    ymax = y0 - FOOT
    xmax = max(sum(w for _, w in g) for g in groups)
    body = fuse_all(blocks + [box(0, xmax, 0, ymax, 0, 2.0)])       # pie común
    body = cut_all(body, holes)
    return fuse_all([body] + labels)


# ---------------------------------------------------------------------------
def build(p, ctx):
    cs = holguras(p)
    noms = nominales(p)
    res = []

    def mk(groups, prefix, kind, desc):
        letters = "ABCDEFG"
        for i, g in enumerate(groups):
            rows = []
            for d, solid, h, lx in g:
                cd = holguras_d(p, ctx, d) if kind == "agujeros" else cs
                ytop = (max(d + c for c in cd) + 2 * WALL) / 2 if kind == "agujeros" else d / 2 + 2
                rows.append((solid, h, lx, ytop))
            part = stack(rows)
            ids = ", ".join(_dlabel(d) for d, *_ in g)
            pid = f"P1.1{prefix}{letters[i]}" if prefix else f"P1.1{letters[i]}"
            res.append((dict(id=pid, name=f"peine_{kind}_{int(g[0][0])}_{int(g[-1][0])}",
                             desc=f"{desc} {ids}; holguras {', '.join(fmt_mm(c) for c in cs)} mm"
                                  + (" + las del CAD por Ø" if kind == "agujeros" else ""),
                             test=TEST, profile="estructural", qty=1, solid_frac=1.0,
                             orientation="Plana, agujeros/pernos de eje vertical (círculo en el plano XY)."),
                        part))

    mk(plates([(d, holguras_d(p, ctx, d)) for d in noms], hole_row), "", "agujeros", "Agujeros Ø(d+c) de eje vertical:")
    mk(plates([(d, cs) for d in noms], pin_row), "P", "pernos", "Pernos Ø(d−c) de eje vertical:")
    ds, _aj = diam_horizontales(p, ctx)
    res.append((dict(id="P1.1H", name="agujeros_horizontales",
                     desc=f"Agujeros horizontales Ø(d+c) para {', '.join(_dlabel(d) for d in ds)} "
                          "(diámetros que las piezas reales imprimen acostados)",
                     test=TEST, profile="estructural", qty=1, solid_frac=1.0,
                     orientation="De pie: eje del agujero horizontal (Y), como en MNT-05/STR-01."),
                horizontal_wall(p, ds, {d: holguras_d(p, ctx, d, "horizontal") for d in ds})))
    return res


def checks(p, ctx, parts):
    cs = holguras(p)
    noms = nominales(p)
    out = [("holgura de diseño geometry.clearance_mm incluida en el peine", float(p.clr in cs), 1.0, ">="),
           ("Ø del tubo de cola incluido", float(float(p.tube_od) in noms), 1.0, ">="),
           ("Ø del perno de basculación incluido", float(float(p.tilt_pin_d) in noms), 1.0, ">=")]
    # cada placa de agujeros contiene exactamente los Ø d+c esperados
    for pid, part in parts.items():
        if pid.startswith("P1.1") and pid[4:5] in "ABCDEFG" and len(pid) == 5:
            radii = {round(cf["r"] * 2, 2) for cf in cyl_faces(part) if cf["hole"]}
            exp = {round(d + c, 2) for d in noms for c in holguras_d(p, ctx, d)}
            out.append((f"{pid}: agujeros con Ø = d + c", float(radii <= exp and len(radii) > 0), 1.0, ">="))
    return out


def criterios(p, ctx):
    ds, aj = diam_horizontales(p, ctx)
    return {
        "ensayo": "Medir cada agujero con calibre/pernos patrón (vástagos de broca o las piezas reales: eje Ø16, "
                  "tubo Ø40, pernos Ø12/Ø16); medir cada perno impreso con calibre.",
        "pasa_si": "Se identifica, por diámetro, la menor holgura que da ajuste deslizante a mano sin juego visible "
                   "(agujeros) → actualizar inputs.yaml geometry.clearance_mm; error del perno impreso ≤ ±0,10 mm "
                   "[SUPUESTO] (si no, usar xy_size_compensation en el perfil).",
        "holguras_mm": holguras(p), "nominales_mm": nominales(p), "horizontales_mm": ds,
        "holguras_por_d_mm": {f"{d:g}": holguras_d(p, ctx, d) for d in nominales(p)},
        "clearance_cad_mm": float(p.clr),
        "ajustes_en_piezas": aj,
    }
