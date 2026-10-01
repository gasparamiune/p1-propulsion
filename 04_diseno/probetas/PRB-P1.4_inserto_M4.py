"""PRB-P1.4 — Inserto térmico M4 inox en PETG (PENDIENTES_GASPAR §P1.4).

RECORTE del reborde real de la caja del ESC (P1-ELE-01) alrededor de un inserto M4 de la tapa
(se prefiere uno de ESQUINA: dos bordes libres a INS_EDGE = caso más desfavorable):
misma sección del reborde (RIM), misma distancia al borde (INS_EDGE), ranura del O-ring vecina,
agujero de inserto cadlib.INSERT_HOLE[4] × (INSERT_LEN[4] + 1). Se elige el primer inserto cuyo
recorte no contiene otros agujeros (prensaestopas, respiradero, orejas). Abajo se agrega un
agujero transversal Ø8,4 para el pasador de tiro. Impresión igual que ELE-01 (fondo en la cama,
inserto vertical abierto hacia arriba).
"""
from cadlib import *  # noqa: F401,F403
from _probelib import cyl_faces, est_row, rx_float, fs_target, label_on_plane, Plane, LABEL_DEPTH

TEST = "P1.4"
SRC = "P1-ELE-01"
HALF_X = 15.0          # media longitud del recorte a lo largo del reborde [SUPUESTO]
BELOW = 22.0           # material bajo el fondo del agujero del inserto [SUPUESTO]
PIN_D = 8.4            # pasador M8 [SUPUESTO]


def _pick(p, ctx):
    eb = ctx.part(SRC)
    part = ctx.built(SRC)
    bb = part.bounding_box()
    z1 = bb.max.Z
    Li, Wi, Hi = p.esc_in
    Wo = Wi + 2 * eb.RIM
    H = INSERT_LEN[4] + 1 + BELOW
    Lo = Li + 2 * eb.RIM

    def n_edges(xy):                                            # bordes exteriores a INS_EDGE del inserto
        x, y = xy
        return (abs(abs(x) - (Lo / 2 - eb.INS_EDGE)) < 1e-6) + (abs(abs(y) - (Wo / 2 - eb.INS_EDGE)) < 1e-6)

    # primero los de esquina (dos bordes a INS_EDGE: el caso más desfavorable para rajar el reborde)
    for (x, y) in sorted(eb.lid_holes(p), key=lambda xy: -n_edges(xy)):
        if abs(abs(y) - (Wo / 2 - eb.INS_EDGE)) > 1e-6:
            continue                                            # solo insertos sobre los lados largos
        sy = 1 if y > 0 else -1
        y0, y1 = sorted((sy * Wi / 2, sy * Wo / 2))
        cut = part & box(x - HALF_X, x + HALF_X, y0, y1, z1 - H, z1 + 1)
        holes = [cf for cf in cyl_faces(cut) if cf["hole"]]
        extra = [cf for cf in holes if abs(cf["r"] - INSERT_HOLE[4] / 2) > 1e-3]
        cbb = cut.bounding_box()
        if not extra and abs((cbb.max.Z - cbb.min.Z) - H) < 1e-3 and abs((cbb.max.Y - cbb.min.Y) - eb.RIM) < 1e-3:
            return dict(x=x, y=y, sy=sy, y0=y0, y1=y1, z1=z1, H=H, cut=cut, n_edges=n_edges((x, y)))
    raise RuntimeError("P1.4: no hay inserto de lado largo con recorte limpio en ELE-01")


def build(p, ctx):
    g = _pick(p, ctx)
    eb = ctx.part(SRC)
    zp = g["z1"] - g["H"] + 9.0
    s = g["cut"] - cyl_y(PIN_D / 2, g["y0"] - 1, g["y1"] + 1, x=g["x"], z=zp)
    yo = g["y1"] if g["sy"] > 0 else g["y0"]
    pl = Plane(origin=(g["x"], yo, zp + 9.0), x_dir=(-g["sy"], 0, 0), z_dir=(0, g["sy"], 0))
    s = s + label_on_plane("M4", pl, size=5.0)
    rot = eb.META["print_rot"]
    meta = dict(id="P1.4", name="inserto_M4",
                desc=f"Recorte del reborde de {SRC} (RIM {eb.RIM:g} mm, inserto de {'esquina' if g['n_edges'] == 2 else 'lado'} "
                     f"a {eb.INS_EDGE:g} mm del borde, "
                     f"ranura de O-ring vecina); agujero Ø{INSERT_HOLE[4]}×{INSERT_LEN[4] + 1:g}; pasador Ø{PIN_D}",
                test=TEST, profile="sellado", qty=3, solid_frac=eb.META.get("solid_frac", 1.0),
                orientation=f"Como {SRC}: fondo en la cama, inserto vertical abierto hacia arriba.")
    return [(meta, to_print(s, rot))]


def checks(p, ctx, parts):
    part = parts["P1.4"]
    hole_r = sorted({round(cf["r"], 3) for cf in cyl_faces(part) if cf["hole"]})
    eb = ctx.part(SRC)
    depth, width = eb.gland_groove(p)
    return [("agujero de inserto = cadlib.INSERT_HOLE[4] [mm]", 2 * min(hole_r, key=lambda r: abs(r - INSERT_HOLE[4] / 2)),
             INSERT_HOLE[4], "="),
            ("ancho del reborde (sin relieve del rótulo) = ELE-01 RIM [mm]",
             min(part.bounding_box().max.X - part.bounding_box().min.X,
                 part.bounding_box().max.Y - part.bounding_box().min.Y) - LABEL_DEPTH, eb.RIM, "="),
            ("pared ranura–inserto ≥ 2 mm (como ELE-01) [mm]",
             (eb.RIM - eb.INS_EDGE - INSERT_HOLE[4] / 2) - (eb.groove_center_offset(p) + width / 2), 2.0, ">=")]


def _f_insert(ctx):
    r = est_row(ctx, "P1-ELE-01", "insertos M4")
    if not r:
        return None, None
    Ft = rx_float(r"F_total\s*=\s*([\d.,]+)\s*N", r["model"])
    n = rx_float(r"/\s*(\d+)\s*insertos", r["model"])
    if Ft and n:
        return Ft / n, r
    return 1000.0 * r["sigma_MPa"] / r["S_MPa"], r                     # fila: σ = (F/1000)·S


def criterios(p, ctx):
    F, r = _f_insert(ctx)
    fs = fs_target(ctx)
    return {
        "F_inserto_N": None if F is None else round(F, 1),
        "fuente_carga": "resultados/estructural.json: fila P1-ELE-01 'Compresión del O-ring en insertos M4'",
        "FS": fs, "umbral_N": None if F is None else round(fs * F, 0), "umbral_PENDIENTES_N": 600.0,
        "instalacion": "Inserto M4 de inox 300 [VERIFICADO: research/R05 S29 existen]; soldador a ~250–260 °C "
                       "[ESTIMADO: research/R05 A10.3]; hundir 90 % con la punta y el resto con herramienta plana "
                       "[VERIFICADO: R05 S28].",
        "ensayo": "Tornillo M4 A4 con cáncamo/varilla en el inserto; pasador M8 en el agujero inferior a una horquilla "
                  "fija; tirar con dinamómetro (+ palanca si hace falta). 3 probetas. Además: torque de giro del "
                  "inserto con llave dinamométrica o brazo + dinamómetro.",
        "pasa_si": "Las 3 resisten ≥ max(umbral, 0,6 kN de PENDIENTES) sin arrancar; torque de giro del inserto "
                   "≥ 2 × 1,0 N·m (apriete de tapa M4 [ESTIMADO: research/R05 A10.3]) [SUPUESTO: criterio].",
    }
