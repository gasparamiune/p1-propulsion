"""PRB-P1.1 — Peine de holguras de las piezas impresas del jet (Ø reales del CAD).

Escanea las piezas `process = "impresa"` del manifest (hoy P1-INT-04, P1-ELE-01/02, P1-CTL-02/03) en su
orientación de impresión y junta los agujeros cilíndricos que reciben una pieza real: tornillos M4–M8
(pasantes Ø d + bolt_clearance), rosca de prensaestopas (M16/M20) y agujeros de panel de los pulsadores
(CTL_kill_hole, CTL_estop_hole de params). Para cada Ø nominal d imprime agujeros Ø(d + c) con
c ∈ {0,15; 0,20; 0,25; 0,30} ∪ {geometry.clearance_mm} ∪ {holguras que usa el CAD para ese d}.

  P1.1A  agujeros de EJE VERTICAL (y los inclinados ≤ 45°, p. ej. los Ø22 de la cara a 32° de CTL-03)
         + fila de bolsillos hexagonales de la tuerca M6 de la purga de P1-INT-04 (abiertos a la cama,
         como en la pieza), entrecaras NUT_AF[6] + {0,1; 0,2; 0,3; 0,4}
  P1.1H  agujeros HORIZONTALES (prensaestopas M16 de la pared de CTL-02), de pie como en la pieza

Los insertos térmicos (agujero INSERT_HOLE) se calibran en P1.4, no aquí.
"""
import math

from cadlib import *  # noqa: F401,F403
from _probelib import label, label_on_plane, fmt_mm, cyl_faces, Plane, fuse_all, cut_all

TEST = "P1.1"
KIND = "impresa"
TITULO = "Peine de holguras (Ø reales de las piezas impresas)"
PIEZAS = ("P1-INT-04", "P1-ELE-01", "P1-ELE-02", "P1-CTL-02", "P1-CTL-03")
HOLGURAS_BASE = [0.15, 0.20, 0.25, 0.30]          # [VERIFICADO: PENDIENTES_GASPAR §P1.1]
BOLTS = (4, 5, 6, 8)                               # tornillos métricos que usan las piezas impresas
GLANDS = (16, 20)                                  # roscas de prensaestopas M16/M20 (R08a)
HEX_DELTAS = [0.1, 0.2, 0.3, 0.4]                  # [SUPUESTO: alrededor de la holgura del CAD (+0,3)]
WALL = 4.0          # pared del anillo [SUPUESTO: ≥ geometry.min_wall_mm]
H_RING = 8.0        # largo del agujero [SUPUESTO: suficiente para juzgar juego radial]
TAB_T = 2.0         # espesor de la franja de rótulos
TAB_W = 9.0         # ancho de la franja de rótulos
COL_W = 16.0        # columna del rótulo de fila
MAX_PLATE = 200.0   # [SUPUESTO: 210 útiles − 10 de margen]
H_THICK = 6.0       # espesor de la pared con agujeros horizontales [SUPUESTO]
FOOT = 10.0         # pie de apoyo de la pared horizontal
HEX_CAP = 3.0       # PETG sobre el bolsillo hexagonal [SUPUESTO: tapa delgada para ver la tuerca]
D_MAX = 40.0        # agujeros mayores no son ajustes (ranura del O-ring, boca de la chimenea)


def nominales_candidatos(p):
    return sorted({float(d) for d in BOLTS + GLANDS} | {float(p.CTL_kill_hole), float(p.CTL_estop_hole)})


def _nominal(p, D):
    """Mayor nominal d con −0,16 ≤ D − d ≤ 0,6 (o None: rebaje, ranura, boca)."""
    ok = [d for d in nominales_candidatos(p) if -0.16 - 1e-6 <= D - d <= 0.6 + 1e-6]
    return max(ok) if ok else None


# ---------------------------------------------------------------------------
# escaneo de las piezas impresas reales
# ---------------------------------------------------------------------------
def ajustes_en_piezas(p, ctx):
    return ctx.cached(("P1.1", "ajustes"), lambda: _ajustes(p, ctx))


def _ajustes(p, ctx):
    rows = {}
    for pid, m in sorted(ctx.parts.items()):
        if m.META.get("process") != "impresa":
            continue
        q = to_print(ctx.built(pid), m.META["print_rot"])
        for cf in cyl_faces(q):
            if not cf["hole"]:
                continue
            D = round(2 * cf["r"], 3)
            if D > D_MAX:
                continue
            d = _nominal(p, D)
            if d is None:
                continue
            az = abs(cf["d"].Z)
            eje = "vertical" if az > 0.98 else ("horizontal" if az < 0.2 else "inclinado")
            rows[(pid, d, D, eje)] = {"id": pid, "d_nom": d, "D_cad": D, "holgura_cad": round(D - d, 3),
                                      "eje_impresion": eje,
                                      "ang_vertical_deg": round(math.degrees(math.acos(min(1.0, az))), 1)}
    return list(rows.values())


def hex_en_piezas(ctx):
    """Bolsillos hexagonales de tuerca de las piezas impresas (lectura del código: NUT_AF[n] + holgura)."""
    import inspect
    import re
    out = []
    for pid, m in sorted(ctx.parts.items()):
        if m.META.get("process") != "impresa":
            continue
        src = inspect.getsource(m)
        for mm in re.finditer(r"hex_prism_z\(NUT_AF\[(\d+)\]\s*\+\s*([\d.]+)", src):
            out.append({"id": pid, "M": int(mm.group(1)), "af_cad": NUT_AF[int(mm.group(1))] + float(mm.group(2)),
                        "holgura_cad": float(mm.group(2))})
    return out


def holguras(p):
    return sorted({round(c, 3) for c in HOLGURAS_BASE + [float(p.clr)]})


def holguras_d(p, ctx, d, ejes=("vertical", "inclinado")):
    extra = {r["holgura_cad"] for r in ajustes_en_piezas(p, ctx) if r["d_nom"] == d and r["eje_impresion"] in ejes}
    return sorted({round(c, 3) for c in holguras(p)} | {round(c, 3) for c in extra})


def diam(p, ctx, ejes):
    return sorted({r["d_nom"] for r in ajustes_en_piezas(p, ctx) if r["eje_impresion"] in ejes})


def _dlabel(d):
    return f"Ø{d:g}"


# ---------------------------------------------------------------------------
# geometría
# ---------------------------------------------------------------------------
def hole_row(d, cs):
    """Fila de anillos (agujero vertical Ø d+c) con franja de rótulos al frente (−Y).
    Devuelve (sólido, alto_y, ytop); origen: x = 0 borde izq., y = 0 eje de los agujeros."""
    ids = [d + c for c in cs]
    od = max(ids) + 2 * WALL
    pitch = max(ids) + WALL
    x0 = COL_W + od / 2
    xs = [x0 + i * pitch for i in range(len(cs))]
    yl = -od / 2 - TAB_W / 2
    body = fuse_all([box(0, xs[-1] + od / 2, -od / 2 - TAB_W, 0, 0, TAB_T)]
                    + [cyl_z(od / 2, 0, H_RING, x=x) for x in xs])
    body = cut_all(body, [cyl_z(idd / 2, -1, H_RING + 1, x=x) for x, idd in zip(xs, ids)])
    labels = [label(_dlabel(d), COL_W / 2 + 0.5, -od / 4 - TAB_W / 2, TAB_T, size=4.5)]
    labels += [label(fmt_mm(c), x, yl, TAB_T, size=4.5) for x, c in zip(xs, cs)]
    return fuse_all([body] + labels), od + TAB_W, od / 2


def hex_row(M, deltas):
    """Bloques con bolsillo hexagonal abierto a la cama (z = 0), agujero Ø M + bolt_clr pasante, rótulos arriba."""
    af_max = NUT_AF[M] + max(deltas)
    side = af_max / math.cos(math.radians(30)) + 2 * WALL
    h = NUT_M[M] + 0.2 + HEX_CAP
    xs = [COL_W + side / 2 + i * (side - 0.01) for i in range(len(deltas))]
    body = fuse_all([box(0, xs[-1] + side / 2, -side / 2 - TAB_W, side / 2, 0, TAB_T)]
                    + [box(x - side / 2, x + side / 2, -side / 2, side / 2, 0, h) for x in xs])
    tools = []
    for x, dl in zip(xs, deltas):
        tools.append(hex_prism_z(NUT_AF[M] + dl, -1, NUT_M[M] + 0.2, x=x))
        tools.append(cyl_z((M + 0.4) / 2, -1, h + 1, x=x))
    body = cut_all(body, tools)
    labels = [label(f"M{M}", COL_W / 2 + 0.5, -side / 4 - TAB_W / 2, TAB_T, size=4.5)]
    labels += [label(fmt_mm(dl, 1), x, -side / 2 - TAB_W / 2, TAB_T, size=4.5) for x, dl in zip(xs, deltas)]
    return fuse_all([body] + labels), side + TAB_W, side / 2


def stack(rows):
    """Apila filas en +Y (cada fila solapa 1 mm a la anterior) + lomo izquierdo que las une."""
    placed, y, ymax = [], 0.0, 0.0
    for solid, h, ytop in rows:
        off = y + (h - ytop)
        placed.append(Pos(0, off, 0) * solid)
        y = off + ytop - 1.0
        ymax = off + ytop
    return fuse_all(placed + [box(0, 3, 0, ymax, 0, TAB_T)])


def horizontal_wall(ds, csd):
    """Pared de pie (espesor H_THICK en Y) con agujeros horizontales (eje Y); rótulos en las caras ±Y."""
    blocks, holes, labels = [], [], []
    x = 0.0
    for d in ds:
        cs = csd[d]
        w = len(cs) * (d + max(cs) + WALL) + WALL
        hmax = d + max(cs) + 2 * WALL + 9.0
        blocks.append(box(x, x + w, FOOT, FOOT + H_THICK, 0, hmax))
        zc = WALL + (d + max(cs)) / 2 + 2.0
        for i, c in enumerate(cs):
            xc = x + WALL + (d + max(cs)) / 2 + i * (d + max(cs) + WALL)
            holes.append(cyl_y((d + c) / 2, FOOT - 1, FOOT + H_THICK + 1, x=xc, z=zc))
            pl = Plane(origin=(xc, FOOT, hmax - 4.5), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
            labels.append(label_on_plane(fmt_mm(c), pl, size=4.0))
        pl = Plane(origin=(x + w / 2, FOOT + H_THICK, hmax - 4.5), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
        labels.append(label_on_plane(f"Ø{d:g} H", pl, size=4.5))
        x += w
    body = fuse_all(blocks + [box(0, x, 0, 2 * FOOT + H_THICK, 0, 2.0)])
    return fuse_all([cut_all(body, holes)] + labels)


def build(p, ctx):
    res = []
    dv = diam(p, ctx, ("vertical", "inclinado"))
    rows = [hole_row(d, holguras_d(p, ctx, d)) for d in dv]
    hx = sorted({h["M"] for h in hex_en_piezas(ctx)})
    rows += [hex_row(M, HEX_DELTAS) for M in hx]
    res.append((dict(id="P1.1A", name="peine_agujeros",
                     desc=f"Agujeros Ø(d+c) de eje vertical para {', '.join(_dlabel(d) for d in dv)}; holguras "
                          f"{', '.join(fmt_mm(c) for c in holguras(p))} mm + las del CAD por Ø"
                          + (f"; bolsillos hexagonales M{', M'.join(str(M) for M in hx)}: e/c del CAD "
                             f"{', '.join(fmt_mm(x, 1) for x in HEX_DELTAS)}" if hx else ""),
                     test=TEST, profile="estructural", qty=1, solid_frac=1.0,
                     orientation="Plana: agujeros de eje vertical; bolsillos hexagonales abiertos a la cama "
                                 "(como la tuerca de purga de P1-INT-04)."),
                stack(rows)))
    dh = diam(p, ctx, ("horizontal",))
    if dh:
        res.append((dict(id="P1.1H", name="agujeros_horizontales",
                         desc=f"Agujeros horizontales Ø(d+c) para {', '.join(_dlabel(d) for d in dh)} "
                              "(los que las piezas reales imprimen acostados)",
                         test=TEST, profile="estructural", qty=1, solid_frac=1.0,
                         orientation="De pie: eje del agujero horizontal (Y), como la pared de P1-CTL-02."),
                    horizontal_wall(dh, {d: holguras_d(p, ctx, d, ("horizontal",)) for d in dh})))
    return res


def checks(p, ctx, parts):
    aj = ajustes_en_piezas(p, ctx)
    out = [("holgura de diseño geometry.clearance_mm incluida", float(round(float(p.clr), 3) in holguras(p)), 1.0, ">="),
           ("se hallaron ajustes en las piezas impresas", float(len(aj)), 1.0, ">=")]
    a = parts.get("P1.1A")
    if a is not None:
        radii = {round(cf["r"] * 2, 2) for cf in cyl_faces(a) if cf["hole"]}
        for r in aj:
            if r["eje_impresion"] != "horizontal":
                out.append((f"P1.1A contiene el Ø del CAD de {r['id']} ({r['D_cad']:g})",
                            float(round(r["D_cad"], 2) in radii), 1.0, ">="))
    h = parts.get("P1.1H")
    if h is not None:
        radii = {round(cf["r"] * 2, 2) for cf in cyl_faces(h) if cf["hole"]}
        for r in aj:
            if r["eje_impresion"] == "horizontal":
                out.append((f"P1.1H contiene el Ø del CAD de {r['id']} ({r['D_cad']:g})",
                            float(round(r["D_cad"], 2) in radii), 1.0, ">="))
    return out


def criterios(p, ctx):
    aj = ajustes_en_piezas(p, ctx)
    hx = hex_en_piezas(ctx)
    tol = 0.10                                                     # [SUPUESTO: error de agujero FDM aceptable]
    return {
        "nominales_mm": diam(p, ctx, ("vertical", "inclinado", "horizontal")),
        "holguras_mm": holguras(p), "clearance_cad_mm": float(p.clr), "bolt_clearance_cad_mm": float(p.bolt_clr),
        "holguras_por_d_mm": {f"{d:g}": holguras_d(p, ctx, d, ("vertical", "inclinado", "horizontal"))
                              for d in diam(p, ctx, ("vertical", "inclinado", "horizontal"))},
        "hex": hx, "hex_deltas_mm": HEX_DELTAS, "tol_mm": tol,
        "ajustes_en_piezas": aj,
        "ensayo": "Medir cada agujero con pernos patrón (vástagos de broca) o calibre; probar la pieza real: tornillo "
                  "M5/M6 A4, cuerpo del prensaestopas M16, cuerpo del interruptor de cordón y de la seta (Ø22), tuerca "
                  "ISO 4032 M6 A4 en los hexágonos (empujada con el pulgar desde la cara de cama).",
        "pasa_si": f"El agujero rotulado con la holgura del CAD mide d + c_CAD ± {tol:.2f} mm y la pieza real entra a "
                   "mano; la tuerca M6 entra en la fila del CAD y no cae al dar vuelta la probeta. Si no: la holgura a "
                   "usar es la menor fila que acepta la pieza → corregir el CAD (inputs.yaml geometry.clearance_mm / "
                   "bolt_clearance_mm) antes de imprimir las piezas.",
    }
