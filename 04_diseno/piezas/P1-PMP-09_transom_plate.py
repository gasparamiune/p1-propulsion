"""P1-PMP-09 — Placa de espejo con cuello coaxial y OREJAS DE PIVOTE (Al 5083, 8 mm + orejas soldadas
o fresadas de bloque 5083, mecanizada). Marco BOTE.

Orejas (interfaz DIRECCIÓN): |Z_jet| ∈ [Z_steer_lug, pmp_lug_z1], ancho pmp_lug_w, extremo redondo en
(X_steer_pivot, 0); alojamiento Ø pmp_lug_hole H7 para el buje POM P1-PMP-11 (tornillo con hombro Ø8 de
DIRECCIÓN). Hacia proa se unen al cuello por encima del resalte de la tobera (r ≥ pmp_tp_bore_R).
Están en la placa y no en la tobera para que la placa (que se monta desde popa) no tenga que pasar por
encima de ellas: así el resalte no depende de D_noz (optimizador 0,58–0,74·D). Las fuerzas de la boquilla
y del bucket van directo al espejo por los 6 × M6.

Va por FUERA del espejo (x ∈ [−gasket_t − tp_t, −gasket_t]) sobre la junta P1-PMP-10, abulonada a
través del espejo con 6 × M6 A4 (Tef-Gel, arandelas aislantes; contraplaca/arandelas grandes por dentro),
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
from cadlib import box, prism_yz, cyl_z, has_radius  # noqa: E402
from params import loc_jet  # noqa: E402

# allow: contactos nominales de ajuste (prensado/deslizante); la intersección BRep exacta es 0 —
# lo que mide verify_parts es el facetado de la malla --fast sobre cilindros coincidentes.
META = dict(id="P1-PMP-09", name="transom_plate",
            desc="Placa de espejo Al 5083 con cuello coaxial, sello radial sobre la tobera y orejas de pivote",
            material="Al 5083", process="torneada", qty=1, frame="boat", group="jet",
            load_case="F lateral de la boquilla y F del bucket en las orejas; sello del casco",
            allow={"P1-PMP-08": 50.0, "P1-PMP-10": 5.0, "P1-PMP-11": 60.0})


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


def lugs(p):
    """Las dos orejas en el marco JET (sin la zona del resalte de la tobera)."""
    hw = p.pmp_lug_w / 2
    out = None
    for s in (1, -1):
        z0, z1 = (p.pmp_lug_z0, p.pmp_lug_z1) if s > 0 else (-p.pmp_lug_z1, -p.pmp_lug_z0)
        lug = box(p.pmp_lug_X0, p.X_steer_pivot, -hw, hw, z0, z1) + cyl_z(hw, z0, z1, x=p.X_steer_pivot)
        lug = lug - cyl_z(p.pmp_lug_hole / 2, z0 - 1, z1 + 1, x=p.X_steer_pivot)
        out = lug if out is None else out + lug
    # libra el resalte de la tobera (adelante de pmp_land_X1 + 0,5 solo existe por fuera del agujero de la placa)
    out = out - cyl_x(p.pmp_tp_bore_R, p.pmp_land_X0 - 5, p.pmp_land_X1 + 0.5)
    return out


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
    part = part + lugs(p).moved(L)
    part = part - box(x1, 300, -300, 300, -300, 400)            # nada dentro del espejo / junta
    if len(part.solids()) == 1:
        part = part.solids()[0]
    return part


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    bb = part.bounding_box()
    zb = min(z for _, z in bolt_yz(p))
    # cuello: debe cubrir la ranura del O-ring en todo el perímetro (la placa está inclinada α respecto del eje)
    sa, ca = math.sin(math.radians(p.alpha)), math.cos(math.radians(p.alpha))
    X_face_max = (p.x_if + p.pmp_gasket_t + p.pmp_land_R * sa) / ca   # cara de PROA de la placa, abajo (la más a popa)
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("orejas: alojamiento del buje Ø pmp_lug_hole", 1.0 if has_radius(part, p.pmp_lug_hole / 2) else 0.0, 1.0, "="),
        ("orejas: cara interior en |Z| = Z_steer_lug [mm]", p.pmp_lug_z0, p.raw["Z_steer_lug"], "="),
        ("orejas: espesor ≥ 12 mm (fatiga con F_bucket)", p.pmp_lug_t, 12.0, ">="),
        ("orejas: pared alrededor del buje [mm]", (p.pmp_lug_w - p.pmp_lug_hole) / 2, 5.0, ">="),
        ("orejas: libran la zona de las orejas de la boquilla (z0 − free) [mm]", p.pmp_lug_z0 - (p.Z_steer_lug - 0.5), 0.5, ">="),
        ("orejas sobre la quilla (z BOTE mín. de la pieza) [mm]", bb.min.Z, 0.0, ">="),
        ("agujero = resalte de la tobera + 0,1 (H8/f7) [mm]", p.pmp_tp_bore_R - p.pmp_land_R, 0.1, "="),
        ("el resalte de la tobera pasa por el agujero del espejo [mm]", p.transom_hole_d / 2 - p.pmp_land_R, 3.0, ">="),
        ("cuello libra las cabezas de los bulones de la placa [mm]", p.pmp_tp_bc_R - 6.0 - p.pmp_collar_R, 2.0, ">="),
        ("placa+cuello cubren el O-ring en todo el perímetro (X) [mm]", p.pmp_or_X - p.pmp_or_width / 2 - X_face_max, 0.0, ">="),
        ("cuello: fin ≥ O-ring + ancho [mm]", p.pmp_collar_X1 - (p.pmp_or_X + p.pmp_or_width / 2), 1.0, ">="),
        ("ligamento agujero del espejo → bulones [mm]", p.pmp_tp_bc_R - (p.pmp_tp_bolt + p.bolt_clr) / 2 - p.transom_hole_d / 2, 8.0, ">="),
        ("ligamento bulones → borde [mm]", p.pmp_tp_R - p.pmp_tp_bc_R - (p.pmp_tp_bolt + p.bolt_clr) / 2, 8.0, ">="),
        ("bulón más bajo sobre la quilla (z) [mm]", zb - (p.pmp_tp_bolt + p.bolt_clr) / 2, p.bottom_t + 8.0, ">="),
        (f"no baja de la quilla (z mín.) [mm] — si falla: subir waterjet.axis_height_m a ≥ {p.h_axis / 1000 - min(bb.min.Z, 0.0) / 1000:.3f} m",
         bb.min.Z, 0.0, ">="),
        ("afuera del espejo (x máx.) [mm]", bb.max.X, -p.pmp_gasket_t, "<="),
    ]
