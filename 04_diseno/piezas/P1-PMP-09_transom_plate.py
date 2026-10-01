"""P1-PMP-09 — Placa de espejo con cuello coaxial (Al 5083, 8 mm, mecanizada). Marco BOTE.

Va por FUERA del espejo (x ∈ [−gasket_t − tp_t, −gasket_t]) sobre la junta P1-PMP-10, abulonada a
través del espejo con 7 × M6 A4 (Tef-Gel, arandelas aislantes; contraplaca/arandelas grandes por dentro),
ninguno abajo (el borde inferior queda a pmp_tp_zmin sobre la quilla). El cuello es coaxial con el
eje del jet (α = 5°) y su agujero Ø 2·pmp_tp_bore_R desliza sobre el resalte de la tobera fija con el
O-ring radial: sella el casco sin hiperestatismo (la bomba se apoya solo en la brida de la toma) y se
monta desde popa pasando por encima de las orejas de pivote. Agujero del espejo: transom_hole_d.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402
from _pmp_geom import cyl_x  # noqa: E402
from cadlib import box, prism_yz  # noqa: E402
from params import loc_jet  # noqa: E402

# allow: contactos nominales de ajuste (prensado/deslizante); la intersección BRep exacta es 0 —
# lo que mide verify_parts es el facetado de la malla --fast sobre cilindros coincidentes.
META = dict(id="P1-PMP-09", name="transom_plate",
            desc="Placa de espejo Al 5083 con cuello coaxial y sello radial sobre la tobera fija",
            material="Al 5083", process="torneada", qty=1, frame="boat", group="jet",
            load_case="Sello del casco; carga lateral si la tobera apoya (O-ring a tope)",
            allow={"P1-PMP-08": 50.0, "P1-PMP-10": 5.0})


def outline(p, R, n=96):
    """Contorno (y, z) de la placa: círculo R alrededor del eje de la tobera en el espejo, recortado abajo."""
    zc = p.z_noz
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        y, z = R * math.cos(a), zc + R * math.sin(a)
        pts.append((y, max(z, p.pmp_tp_zmin)))
    out = []
    for q in pts:                                   # quita duplicados del recorte
        if not out or (abs(q[0] - out[-1][0]) > 1e-6 or abs(q[1] - out[-1][1]) > 1e-6):
            out.append(q)
    return out


def bolt_yz(p):
    return [(p.pmp_tp_bc_R * math.cos(math.radians(a)), p.z_noz + p.pmp_tp_bc_R * math.sin(math.radians(a)))
            for a in p.pmp_tp_bolt_ang]


def build(p):
    x1 = -p.pmp_gasket_t
    x0 = x1 - p.pmp_tp_t
    plate = prism_yz(outline(p, p.pmp_tp_R), x0, x1)
    L = loc_jet(p)
    collar = cyl_x(p.pmp_collar_R, p.X_noz1 - 30.0, p.pmp_collar_X1).moved(L)
    collar = collar - box(x0, 200, -200, 200, -200, 400)          # solo a popa de la cara aft de la placa
    part = plate + collar
    part = part - cyl_x(p.pmp_tp_bore_R, p.X_noz1 - 60.0, p.pmp_collar_X1 + 5).moved(L)
    for y, z in bolt_yz(p):
        part = part - cyl_x((p.pmp_tp_bolt + p.bolt_clr) / 2, x0 - 1, x1 + 1, y=y, z=z)
    if len(part.solids()) == 1:
        part = part.solids()[0]
    return part


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    bb = part.bounding_box()
    lug_r = math.hypot(p.Z_steer_lug + p.pmp_lug_t, p.pmp_lug_w / 2)
    zb = min(z for _, z in bolt_yz(p))
    # cuello: debe cubrir la ranura del O-ring en todo el perímetro (la placa está inclinada α respecto del eje)
    sa, ca = math.sin(math.radians(p.alpha)), math.cos(math.radians(p.alpha))
    X_face_max = (p.x_if + p.pmp_gasket_t + p.pmp_land_R * sa) / ca   # cara de PROA de la placa, abajo (la más a popa)
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("agujero = resalte de la tobera + 0,1 (H8/f7) [mm]", p.pmp_tp_bore_R - p.pmp_land_R, 0.1, "="),
        ("pasa sobre las orejas de pivote [mm]", p.pmp_tp_bore_R - lug_r, 2.0, ">="),
        ("placa+cuello cubren el O-ring en todo el perímetro (X) [mm]", p.pmp_or_X - p.pmp_or_width / 2 - X_face_max, 0.0, ">="),
        ("cuello: fin ≥ O-ring + ancho [mm]", p.pmp_collar_X1 - (p.pmp_or_X + p.pmp_or_width / 2), 1.0, ">="),
        ("ligamento agujero del espejo → bulones [mm]", p.pmp_tp_bc_R - (p.pmp_tp_bolt + p.bolt_clr) / 2 - p.transom_hole_d / 2, 8.0, ">="),
        ("ligamento bulones → borde [mm]", p.pmp_tp_R - p.pmp_tp_bc_R - (p.pmp_tp_bolt + p.bolt_clr) / 2, 8.0, ">="),
        ("bulón más bajo sobre la quilla (z) [mm]", zb - (p.pmp_tp_bolt + p.bolt_clr) / 2, p.bottom_t + 8.0, ">="),
        ("no baja de la quilla (z mín.) [mm]", bb.min.Z, 0.0, ">="),
        ("afuera del espejo (x máx.) [mm]", bb.max.X, -p.pmp_gasket_t, "<="),
    ]
