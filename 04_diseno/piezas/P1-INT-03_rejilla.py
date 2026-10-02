"""P1-INT-03 — Rejilla de la toma (AISI 316 soldada: pletinas perfiladas + pletina de popa + tirante).

Marco BOTE. grille_bars pletinas de grille_bar_d × toma_bar_h, LONGITUDINALES (el rastrillo entra
desde el espejo entre barras, R10a §4), con la cara inferior enrasada con el fondo (z = 0):
  • sección perfilada: nariz semicircular abajo (borde de ataque del flujo que sube) y cola afinada
    arriba (Kirschmer β ≈ 1,67–1,83 en vez de 2,42 rectangular, research/R12 §4.3);
  • alto 18 mm donde el techo lo permite y, hacia la tangencia, techo − 2 mm;
  • a popa entran en ranuras del bloque del labio de P1-INT-01 (abiertas hacia abajo) y se sueldan a
    una pletina transversal 3 mm alojada enrasada bajo el bloque (2 × M5 ISO 10642 A4);
  • a proa se sueldan a un tirante transversal 3 × 12 que entra en bolsillos laterales de la placa
    base P1-INT-02 (2 × M5 ISO 10642 A4). A proa del tirante el techo está a < 8 mm del fondo: el
    pasaje mismo hace de rejilla.
Desmontable DESDE AFUERA con 4 tornillos M5 A4 (bote en el trailer o buceando, con el sistema
desarmado — R10a §0).
Luz entre barras ≤ toma_gap_max (una varilla Ø13 no pasa, R10a §8.6; auditoría Pass 3 / bloqueo H-11):
n = grille_bars sale de params_toma; K de Kirschmer con barra perfilada ≈ grille_k de inputs (check).
AISLACIÓN GALVÁNICA (316 bajo el agua contra 5083): camisa/cinta de PTFE en las ranuras del labio y los
bolsillos (luz toma_iso_gap), cinta de PTFE toma_bar_iso_t en el canto que apoya en la cuña de la placa,
casquillos aislantes de nylon en los 4 × M5 (arandela cónica de nylon bajo la cabeza avellanada) + Tef-Gel;
continuidad 316 ↔ 5083 > 1 kΩ al montar (06 §4).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
from build123d import Location  # noqa: E402

from cadlib import box, cyl_z, prism_xz, prism_yz  # noqa: E402

META = dict(id="P1-INT-03", name="rejilla",
            desc="Rejilla 316: pletinas perfiladas 4 × 21 longitudinales (luz ≤ 12,5) enrasadas, pletina de popa y tirante de proa, 4 × M5 A4 aislados",
            material="AISI 316", process="torneada", qty=1, frame="boat", group="jet",
            load_case="Rejilla tapada a la presión de cierre de la bomba; golpe de objeto 200 N en el centro de una barra",
            allow={"P1-INT-01": 5.0, "P1-INT-02": 40.0})


def bar_x_range(p):
    return p.toma_strap_x[0] + 2.0, p.toma_x_bf + p.toma_tie_w / 2


def bar_top(p, x):
    """Alto de la barra en x: toma_bar_h; cerca de la tangencia, techo − 2 mm; sobre la cuña de la
    placa base (x ≥ toma_x_j) la barra APOYA contra el techo de Al: ahí descarga la succión."""
    if x <= p.x_lip + 1.0:
        return p.toma_bar_h
    c = max(p.toma_bar_clr * min(1.0, max(0.0, (p.toma_x_j - x) / 15.0)), p.toma_bar_iso_t)
    return float(min(p.toma_bar_h, p.toma_roof_z(x) - c))


def build(p):
    b, h = p.grille_bar_d, p.toma_bar_h
    xa, xf = bar_x_range(p)
    xs = np.linspace(xa, xf, 60)
    side = [(xa, 0.0)] + [(float(x), bar_top(p, x)) for x in xs] + [(xf, 0.0)]
    # sección perfilada (y, z): nariz semicircular abajo, cola afinada a 1,6 mm arriba
    r = b / 2
    arc = [(r * math.cos(math.radians(a)), r + r * math.sin(math.radians(a))) for a in range(195, 360, 15)]
    sec = [(r, r), (r, h - 6.0), (0.8, h + 0.01), (-0.8, h + 0.01), (-r, h - 6.0), (-r, r)] + arc
    G = None
    for yb in p.toma_bar_y:
        s_ = prism_xz(side, yb - r - 0.01, yb + r + 0.01)
        q = prism_yz([(yb + y, z) for (y, z) in sec], xa - 1, xf + 1)
        bar = s_ & q
        G = bar if G is None else G + bar
    W2 = p.W_open / 2
    sx0, sx1 = p.toma_strap_x
    G = G + box(sx0, sx1, -(W2 - 4), W2 - 4, 0, p.toma_strap_t)
    G = G + box(p.toma_x_bf - p.toma_tie_w / 2, p.toma_x_bf + p.toma_tie_w / 2, -(W2 + 12), W2 + 12, 0, p.toma_strap_t)
    # tornillos M5 avellanados (Ø5,5 pasante; avellanado 90° no modelado)
    import importlib.util
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("_int01", str(here / "P1-INT-01_conducto.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for y in m.strap_screw_y(p):
        G = G - cyl_z(2.75, -1, p.toma_strap_t + 1, x=0.5 * (sx0 + sx1), y=y)
    for s in (1, -1):
        G = G - cyl_z(2.75, -1, p.toma_strap_t + 1, x=p.toma_x_bf, y=s * (W2 + 7.0))
    return G


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def open_area(p):
    """Área efectiva: abertura bruta − barras − tirante (misma definición que R10a §5.2)."""
    n, b = p.grille_bars, p.grille_bar_d
    xa, xf = bar_x_range(p)
    L_bar_open = min(xf, p.x_tan) - p.x_lip
    A = p.W_open * p.L_open - n * b * L_bar_open - p.toma_tie_w * (p.W_open - n * b)
    return A


def checks(p, part):
    A_imp = math.pi / 4 * p.D ** 2
    req = p.inp["waterjet"]["grille_open_area_m2_per_Aimp"]
    bb = part.bounding_box()
    gap = p.toma_bar_gap
    xs = np.linspace(p.x_lip, bar_x_range(p)[1], 300)
    clr = min(float(p.toma_roof_z(x)) - bar_top(p, x) for x in xs if x <= p.toma_x_j - 15.0)
    bear = p.toma_x_bf + p.toma_tie_w / 2 - p.toma_x_j
    # mínimo pasaje del rotor (R12 §4.3: ~34 mm en el cubo con Z = 5) — la luz tiene que ser menor
    pitch_hub = 2 * math.pi * (p.D_hub / 2) / p.blades
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("área efectiva / A_impulsor ≥ grille_open_area_m2_per_Aimp", open_area(p) / A_imp, req, ">="),
        ("luz entre barras ≤ toma_gap_max: varilla Ø13 no pasa (R10a §8.6) [mm]", gap, p.toma_gap_max, "<="),
        ("luz entre barras ≥ 10 mm (basura/limpieza; R12 §4.3 recomienda 15–20) [mm]", gap, 10.0, ">="),
        ("K Kirschmer barra perfilada 1,83·(t/e)^(4/3) ≤ grille_k + 0,05 (inputs) [—]",
         1.83 * (p.grille_bar_d / gap) ** (4 / 3), p.inp["waterjet"]["grille_k"] + 0.05, "<="),
        ("luz < paso entre álabes en el cubo [mm]", gap, pitch_hub, "<="),
        ("enrase: z mín. de la rejilla = fondo [mm]", bb.min.Z, 0.0, "="),
        ("barras libres del techo del conducto [mm]", clr, p.toma_bar_clr - 0.01, ">="),
        ("barras apoyan en la cuña de Al de la placa: largo de apoyo [mm]", bear, 6.0, ">="),
        ("barras cubren la abertura desde el labio: x_lip ≥ inicio de barras [mm]", p.x_lip - bar_x_range(p)[0], 0.0, ">="),
        ("pasaje a proa del tirante < luz (sin barras) [mm]", float(p.toma_roof_z(p.toma_x_bf + p.toma_tie_w / 2)), gap, "<="),
    ]
