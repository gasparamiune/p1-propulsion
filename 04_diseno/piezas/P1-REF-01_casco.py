"""P1-REF-01 — Casco de referencia (popa del bote de Jorge, simplificado). NO se fabrica.

Marco BOTE. Sirve para que verify_parts.py detecte choques reales de la toma, la bomba, el tren y el
motor contra el casco. Datos de inputs.yaml boat.* (todos [ESTIMADO] hasta medir, R10b §4.3):
  • sección constante (sin arrufo ni astilla variable) desde el espejo hasta x = toma_ref_L:
    fondo con astilla muerta deadrise_deg desde un PAÑO PLANO en crujía (toma_ref_pad_y, [SUPUESTO]:
    la toma y su placa base necesitan fondo plano; MEDIR) hasta la manga de fondo bottom_beam,
    costado hasta el pantoque (chine_beam a chine_height) y hasta la borda (beam a gunwale_height);
  • fondo y costados de bottom_thickness, espejo de transom_thickness y transom_height de alto;
  • recorte del fondo para el cuerpo de la placa base P1-INT-02 (+ luz de sellador) y agujeros de sus
    bulones; agujero del espejo Ø transom_hole_d centrado en el eje de la tobera (en x = 0, z_noz).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Kind, Location, Plane, Polyline, extrude, make_face, offset  # noqa: E402

import _toma_geom as G  # noqa: E402
from cadlib import box, cyl_x, cyl_z  # noqa: E402

META = dict(id="P1-REF-01", name="casco",
            desc="Casco de referencia (popa 1,4 m): fondo con astilla muerta y paño plano, pantoque, costados, espejo; recorte de la toma y agujero del espejo",
            material="referencia", process="referencia", qty=1, frame="boat", group="ref",
            load_case="—", allow={"P1-INT-02": 30.0})

REF_L = 1400.0      # [SUPUESTO: largo modelado desde el espejo; cubre el motor (x ≤ ~800) y el controlador]
PAD_Y = 185.0       # [SUPUESTO: paño plano en crujía ±185 mm (placa base ±175 + 10); MEDIR el fondo real]


def section_pts(p):
    b = p.inp["boat"]
    yb, yc, yg = b["bottom_beam_m"] * 500, b["chine_beam_m"] * 500, b["beam_m"] * 500
    zc, zg = b["chine_height_m"] * 1000, b["gunwale_height_m"] * 1000
    zb = (yb - PAD_Y) * math.tan(math.radians(b["deadrise_deg"]))
    half = [(PAD_Y, 0.0), (yb, zb), (yc, zc), (yg, zg)]
    return [(-y, z) for (y, z) in half[::-1]] + [(y, z) for (y, z) in half]


def build(p):
    pts = section_pts(p)
    face = make_face(Polyline(*[(0, y, z) for y, z in pts], close=True))
    outer = extrude(face, amount=REF_L, dir=(1, 0, 0))
    inner_face = offset(face, amount=-p.bottom_t, kind=Kind.INTERSECTION)
    inner = extrude(inner_face, amount=REF_L, dir=(1, 0, 0)).moved(Location((p.transom_t, 0, 0)))
    hull = outer - inner
    zg = p.inp["boat"]["gunwale_height_m"] * 1000
    hull = hull - box(-1, REF_L + 1, -1000, 1000, zg - p.bottom_t - 0.01, zg + 10)   # borda abierta
    zt = p.inp["boat"]["transom_height_m"] * 1000
    hull = hull - box(-1, p.transom_t + 1, -1000, 1000, zt, zg + 10)               # espejo más bajo que la borda
    # recorte del fondo para el cuerpo de la placa base (+ luz de sellador)
    g = p.toma_seal_gap
    hull = hull - G.rounded_rect_xy(p.toma_plate_x0 - g, p.toma_plate_x1 + g, -p.toma_plate_y - g, p.toma_plate_y + g,
                                    p.toma_plate_r + g, -1, p.bottom_t + 1)
    # bulones del ala de la placa base
    import importlib.util
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("_int02", str(here / "P1-INT-02_placa_base.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for (x, y) in m.hull_bolts(p):
        hull = hull - cyl_z((p.toma_hull_bolt + p.bolt_clr) / 2, -1, p.bottom_t + 1, x=x, y=y)
    # agujero del espejo en el eje de la tobera
    hull = hull - cyl_x(p.transom_hole_d / 2, -1, p.transom_t + 1, z=p.z_noz)
    # pasacasco de salida de refrigeración (grupo TREN/ELE, P1-ELE-03): Ø17 en el espejo
    if "cool_out_yz" in p.raw:
        yo, zo = p.cool_out_yz
        hull = hull - cyl_x(17.0 / 2, -1, p.transom_t + 1, y=yo, z=zo)
    return hull


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    bb = part.bounding_box()
    b = p.inp["boat"]
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("largo modelado desde el espejo ≥ 1,4 m [mm]", bb.max.X, 1400.0, ">="),
        ("manga en la borda = beam [mm]", bb.max.Y - bb.min.Y, b["beam_m"] * 1000, "="),
        ("paño plano ≥ semiancho del ala de la placa base [mm]", PAD_Y, p.toma_plate_y + p.toma_rim_w, ">="),
        ("agujero del espejo sobre el fondo interior (z_noz − Ø/2 ≥ bottom_t) [mm]", p.z_noz - p.transom_hole_d / 2, p.bottom_t, ">="),
    ]
