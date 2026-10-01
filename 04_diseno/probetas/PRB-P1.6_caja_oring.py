"""PRB-P1.6 — Caja estanca reducida con O-ring de cara (PENDIENTES_GASPAR §P1.6).

Réplica de P1-ELE-01 en planta reducida: mismo reborde (RIM), misma ranura de cara (profundidad
y ancho de ELE-01.gland_groove → cordón 3,53 mm, research/R05 B3), mismo piso, misma altura
interior (para que el prensaestopas M20 quede a la misma altura GLAND_ZC con su rebaje y pared
GLAND_WALL), mismo respiradero, insertos M4 en las 4 esquinas: luz entre insertos ≈ la mayor luz
de ELE-01 (tapa de 4 mm entre apoyos). Todo se lee del módulo de ELE-01.

P1.6A: caja (perfil sellado).  P1.6B: tapa plana IMPRESA solo de prueba (la real es de Al,
ELE-02); se imprime con la cara de sello sobre la cama y sirve de plantilla para taladrar la de Al.
"""
import math

from cadlib import *  # noqa: F401,F403
from _probelib import label, scan

TEST = "P1.6"
SRC = "P1-ELE-01"
LI, WI = 70.0, 50.0      # interior reducido [SUPUESTO: entra el contratuerca M20 y el papel tisú]
T_LID = 8.0              # tapa impresa de prueba [SUPUESTO: más gruesa que la de Al para limitar la flecha]
R05_DEPTH = (2.57, 2.72)  # [VERIFICADO: research/R05 B3 (Parker ORD 5700 Design Chart 4-3), cordón 3,53]
R05_WIDTH = (4.50, 4.75)  # [VERIFICADO: idem]


def _floor_t(ctx):
    return ctx.cached(("P1.6", "floor"), lambda: _floor_scan(ctx))


def _floor_scan(ctx):
    """Espesor de piso de ELE-01 leído del sólido (rayo vertical por el centro)."""
    part = ctx.built(SRC)
    bb = part.bounding_box()
    tr = scan(part, (0.0, 0.0, bb.min.Z - 0.5), (0, 0, 1), 20.0, step=0.25)
    ins = [s for s, now_in in tr if now_in]
    outs = [s for s, now_in in tr if not now_in]
    return round(outs[0] - ins[0], 3)


def max_span(pts):
    """Mayor distancia entre insertos consecutivos alrededor del reborde (orden angular)."""
    q = sorted(pts, key=lambda t: math.atan2(t[1], t[0]))
    return max(math.dist(q[i], q[(i + 1) % len(q)]) for i in range(len(q)))


def dims(p, ctx):
    eb = ctx.part(SRC)
    Hi = float(p.esc_in[2])
    tf = _floor_t(ctx)
    Lo, Wo = LI + 2 * eb.RIM, WI + 2 * eb.RIM
    depth, width = eb.gland_groove(p)
    c = eb.groove_center_offset(p)
    e = eb.INS_EDGE
    ins = [(sx * (Lo / 2 - e), sy * (Wo / 2 - e)) for sx in (-1, 1) for sy in (-1, 1)]
    return dict(Lo=Lo, Wo=Wo, Hi=Hi, tf=tf, z1=tf + Hi, depth=depth, width=width, c=c, ins=ins, e=e)


def build(p, ctx):
    eb = ctx.part(SRC)
    d = dims(p, ctx)
    Lo, Wo, z1, depth, width, c = d["Lo"], d["Wo"], d["z1"], d["depth"], d["width"], d["c"]
    bx = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, z1)
    bx = bx - box(-LI / 2, LI / 2, -WI / 2, WI / 2, d["tf"], z1 + 1)
    outer = box(-LI / 2 - c - width / 2, LI / 2 + c + width / 2, -WI / 2 - c - width / 2, WI / 2 + c + width / 2,
                z1 - depth, z1 + 1)
    inner = box(-LI / 2 - c + width / 2, LI / 2 + c - width / 2, -WI / 2 - c + width / 2, WI / 2 + c - width / 2,
                z1 - depth - 1, z1 + 2)
    bx = bx - (outer - inner)
    for (x, y) in d["ins"]:
        bx = bx - cyl_z(INSERT_HOLE[4] / 2, z1 - INSERT_LEN[4] - 1, z1 + 1, x=x, y=y)
    # un prensaestopas M20 en el extremo −x (mismas cotas que ELE-01)
    _y, dh, dc = eb.GLANDS["+x"][1]
    zc = eb.GLAND_ZC
    x_out, x_in = -Lo / 2, -LI / 2
    bx = bx - cyl_x(dh / 2, x_out - 1, x_in + 1, y=0.0, z=zc)
    bx = bx - cyl_x(dc / 2, x_out - 1, x_in - eb.GLAND_WALL, y=0.0, z=zc)
    # respiradero M12 en +y (como ELE-01)
    bx = bx - cyl_y(eb.VENT[0] / 2, WI / 2 - 1, Wo / 2 + 1, x=0.0, z=zc)
    bx = bx - cyl_y(eb.VENT[1] / 2, WI / 2 + eb.GLAND_WALL, Wo / 2 + 1, x=0.0, z=zc)
    lid = box(-Lo / 2, Lo / 2, -Wo / 2, Wo / 2, 0, T_LID)
    for (x, y) in d["ins"]:
        lid = lid - cyl_z((4 + p.bolt_clr) / 2, -1, T_LID + 1, x=x, y=y)
    lid = lid + label("SOLO PRUEBA", 0, 6, T_LID, size=7.0) + label("cara de sello abajo", 0, -8, T_LID, size=4.5)
    rot = eb.META["print_rot"]
    return [
        (dict(id="P1.6A", name="caja_oring", desc=f"Caja {LI:g}×{WI:g}×{d['Hi']:g} interior, reborde {eb.RIM:g}, ranura "
              f"{depth:.2f}×{width:.2f} (cordón {p.oring_cs} mm), 4 insertos M4, 1 prensaestopas M20, respiradero M12",
              test=TEST, profile="sellado", qty=1, solid_frac=eb.META.get("solid_frac", 1.0),
              orientation="Como ELE-01: fondo en la cama, cara del O-ring arriba (planchado + refrentado/lijado)."),
         to_print(bx, rot)),
        (dict(id="P1.6B", name="tapa_prueba_impresa", desc=f"Tapa plana impresa {Lo:g}×{Wo:g}×{T_LID:g} SOLO DE PRUEBA "
              "(la real es Al 4 mm, ELE-02) y plantilla de taladrado", test=TEST, profile="sellado", qty=1, solid_frac=1.0,
              orientation="Cara de sello sobre la cama (la cara más lisa de FDM, research/R05 B4)."),
         lid),
    ]


def checks(p, ctx, parts):
    d = dims(p, ctx)
    eb = ctx.part(SRC)
    lo_real = max_span(eb.lid_holes(p))                          # mayor luz entre insertos vecinos en ELE-01
    span = max_span(d["ins"])
    top_cb = eb.GLAND_ZC + eb.GLANDS["+x"][1][2] / 2
    return [("profundidad de ranura ≥ 2,57 (R05) [mm]", d["depth"], R05_DEPTH[0], ">="),
            ("profundidad de ranura ≤ 2,72 (R05) [mm]", d["depth"], R05_DEPTH[1], "<="),
            ("ancho de ranura ≥ 4,50 (R05) [mm]", d["width"], R05_WIDTH[0], ">="),
            ("ancho de ranura ≤ 4,75 (R05) [mm]", d["width"], R05_WIDTH[1], "<="),
            ("luz entre insertos de la probeta ≥ mayor luz de ELE-01 [mm]", span, lo_real, ">="),
            ("rebaje del prensaestopas bajo la ranura (≥ 2 mm) [mm]", (d["z1"] - d["depth"]) - top_cb, 2.0, ">="),
            ("contratuerca M20 (27,7 entre vértices) entra en el ancho interior [mm]", WI, 27.7 + 2, ">=")]


def criterios(p, ctx):
    d = dims(p, ctx)
    eb = ctx.part(SRC)
    a = LI / 2 + d["c"]
    b = WI / 2 + d["c"]
    perim_mid = 4 * (a + b)
    t_al = None
    try:
        bb = ctx.built("P1-ELE-02").bounding_box()
        t_al = round(bb.max.Z - bb.min.Z, 2)
    except Exception:                                                # pragma: no cover
        pass
    rho, g, h = 1000.0, 9.81, 0.5
    return {
        "ranura_mm": [round(d["depth"], 3), round(d["width"], 3)], "rango_R05_mm": [R05_DEPTH, R05_WIDTH],
        "cordon_mm": p.oring_cs, "largo_cordon_mm": round(perim_mid, 0),
        "largo_base": "[CALCULADO: perímetro de la línea media de la ranura; empalme a tope]",
        "tapa_Al_mm": [d["Lo"], d["Wo"], t_al], "agujeros_tapa_mm": 4 + p.bolt_clr,
        "presion_0_5m_kPa": round(rho * g * h / 1000, 2),
        "planitud_max_mm": 0.10,
        "planitud_base": "[CALCULADO: ±0,15 mm de profundidad mantiene la compresión en 21–29 % (research/R05 B3); "
                         "planitud ≤ 0,10 deja margen a la tolerancia del cordón ±0,10]",
        "ensayo": "Medir ranura (calibre de profundidades) y planitud (regla + galgas). O-ring NBR70 con grasa de "
                  "silicona; tapa de Al con 4 tornillos M4 A4 a 1,0 N·m [ESTIMADO: R05 A10.3]; prensaestopas M20 con "
                  "un trozo de cable de punta sellada; papel tisú adentro. (1) 30 min a 0,3 m; (2) 24 h a 0,5 m con "
                  "lastre; (3) 20 ciclos abrir/cerrar y repetir (1).",
        "pasa_si": "Papel tisú seco y 0 gotas tras las 24 h a 0,5 m (PENDIENTES §P1.6) y tras los 20 ciclos. Si falla: "
                   "repetir con tapón M12 ciego en el respiradero y tapón M20 para aislar la causa.",
    }
