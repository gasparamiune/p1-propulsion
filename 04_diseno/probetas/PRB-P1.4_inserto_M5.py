"""PRB-P1.4 — Inserto térmico M5 inox en el nervio de la base del controlador P1-ELE-01.

RECORTE de la pieza real alrededor de uno de los 4 insertos M5 de la capota (P1-ELE-02 se atornilla con
4 × M5 A4 a estos insertos): el nervio exterior (ELE-01.RIB_W × RIB_D) con su tramo de pared del pedestal,
desde la cara superior hasta INSERT_LEN[5] + 1 + BELOW hacia abajo; agujero cadlib.INSERT_HOLE[5] del CAD
(leído del sólido). Abajo, un agujero transversal Ø8,4 para el pasador de tiro. Se imprime como ELE-01
(base sobre la cama, inserto vertical abierto hacia arriba) y con su perfil (familias.py).
Las otras piezas del controlador (P1-CTL-02/03, P1-ELE-02) usan tornillos pasantes M5 (P1.1), sin insertos.
"""
import re

from cadlib import *  # noqa: F401,F403
from _probelib import cyl_faces, est_row, fs_target, label_on_plane, Plane
import familias as FAM

TEST = "P1.4"
KIND = "impresa"
TITULO = "Inserto térmico M5 inox en el nervio de P1-ELE-01"
PIEZAS = ("P1-ELE-01", "P1-ELE-02")
SRC = "P1-ELE-01"
M = 5
BELOW = 22.0           # material bajo el fondo del agujero del inserto [SUPUESTO: lugar para el pasador de tiro]
PIN_D = 8.4            # pasador M8 [SUPUESTO]
T_APRIETE_NM = 2.0     # apriete M5 sobre PETG [ESTIMADO: research/R05 A10.3, ~50 % del torque de falla]


def _geo(p, ctx):
    eb = ctx.part(SRC)
    part = ctx.built(SRC)
    bb = part.bounding_box()
    x, y = sorted(eb.rib_pts(p))[0]                      # marco local de la pieza (build(p))
    sy = 1 if y > 0 else -1
    _Lo, Wo = eb.outer(p)
    y_wall = sy * (Wo / 2 - p.ele_wall)
    y_out = sy * (Wo / 2 + eb.RIB_D)
    y0, y1 = sorted((y_wall, y_out))
    z1 = bb.max.Z
    H = INSERT_LEN[M] + 1 + BELOW
    cut = part & box(x - eb.RIB_W / 2, x + eb.RIB_W / 2, y0, y1, z1 - H, z1)
    return dict(x=x, y=y, sy=sy, y0=y0, y1=y1, z1=z1, H=H, cut=cut)


def build(p, ctx):
    g = _geo(p, ctx)
    eb = ctx.part(SRC)
    zp = g["z1"] - g["H"] + 8.0
    s = g["cut"] - cyl_y(PIN_D / 2, g["y0"] - 1, g["y1"] + 1, x=g["x"], z=zp)
    xo = g["x"] + eb.RIB_W / 2
    pl = Plane(origin=(xo, 0.5 * (g["y0"] + g["y1"]), zp + 10.0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    s = s + label_on_plane(f"M{M}", pl, size=5.0)
    fam = FAM.familia({"id": SRC})[0]
    meta = dict(id="P1.4", name=f"inserto_M{M}",
                desc=f"Recorte del nervio de {SRC} ({eb.RIB_W:g} × {eb.RIB_D:g} mm + pared {p.ele_wall:g}) con el "
                     f"agujero de inserto Ø{INSERT_HOLE[M]:g} × {INSERT_LEN[M] + 1:g}; pasador de tiro Ø{PIN_D:g}",
                test=TEST, profile=fam, qty=3, solid_frac=eb.META.get("solid_frac", 1.0),
                orientation=f"Como {SRC}: base sobre la cama, inserto vertical abierto hacia arriba.")
    return [(meta, to_print(s, eb.META["print_rot"]))]


def checks(p, ctx, parts):
    part = parts["P1.4"]
    rs = [cf["r"] for cf in cyl_faces(part) if cf["hole"]]
    d_ins = 2 * min(rs, key=lambda r: abs(r - INSERT_HOLE[M] / 2))
    eb = ctx.part(SRC)
    return [("agujero de inserto = cadlib.INSERT_HOLE[5] (leído del recorte) [mm]", d_ins, INSERT_HOLE[M], "="),
            ("pared alrededor del inserto en el nervio ≥ 2 mm [mm]", (eb.RIB_D - INSERT_HOLE[M]) / 2, 2.0, ">="),
            ("un solo sólido", len(part.solids()), 1, "=")]


def _f_insert(ctx):
    """Carga por inserto de estructural.json: fila 'Insertos M5 de la capota' (F = máx(EPDM, 3 g)/n)."""
    r = est_row(ctx, SRC, "insertos m5")
    if not r:
        return None, None, None
    fs_ = [float(v) for v in re.findall(r"([\d.]+)\s*N", r["model"])]
    n = re.search(r"\)\s*/\s*(\d+)", r["model"])
    if fs_ and n:
        return max(fs_) / int(n.group(1)), r, int(n.group(1))
    return None, r, None


def criterios(p, ctx):
    F, r, n = _f_insert(ctx)
    fs = fs_target(ctx)
    thr = None if F is None else round(fs * F, 0)
    return {
        "F_inserto_N": None if F is None else round(F, 1), "n_insertos": n,
        "fuente_carga": "resultados/estructural.json: fila P1-ELE-01 «" + (r["load_case"] if r else "—") + "»",
        "FS_est": None if r is None else r["FS"],
        "FS": fs, "umbral_N": thr, "T_apriete_Nm": T_APRIETE_NM, "T_giro_min_Nm": 2 * T_APRIETE_NM,
        "instalacion": "Inserto M5 de inox 300 (en zona húmeda solo inox: latón se descinfica, research/R05 A10.2) "
                       "[VERIFICADO: research/R05 S29 existen]; soldador a ~250–260 °C [ESTIMADO: research/R05 A10.3]; "
                       "hundir el 90 % con la punta y el resto con herramienta plana [VERIFICADO: R05 S28].",
        "ensayo": "Tornillo M5 A4 con cáncamo en el inserto; pasador M8 en el agujero inferior a una horquilla fija; "
                  "tirar con dinamómetro a ~10 N/s. 3 probetas. Además: torque de giro del inserto con llave "
                  "dinamométrica (o brazo + dinamómetro).",
        "pasa_si": (f"Las 3 resisten ≥ {thr:.0f} N (= FS {fs:g} × {F:.0f} N por inserto, estructural.json) sin arrancar "
                    if thr else "Las 3 resisten FS × carga de estructural.json ") +
                   f"y el inserto no gira con ≥ {2 * T_APRIETE_NM:g} N·m (2 × apriete M5 sobre PETG) "
                   "[SUPUESTO: criterio de giro]. A ras ±0,2 mm, sin fisura alrededor (lupa 10×).",
    }
