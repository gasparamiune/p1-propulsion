"""P1-DRV-03 — Soporte de rodamientos (pórtico), Al 6082-T651 mecanizado y soldado (TIG, alivio no
requerido: tensiones muy bajas) o mecanizado de bloque.

Toma TODO el empuje axial (Fa a punto fijo) del par 7204 BECBP en O y lo baja a la placa base de la toma
por los 4 × M8 de la interfaz (brg_bracket_holes, z = base_top_z). Es un PUENTE sobre el conducto:
  • alojamiento Ø47 H7 (marco JET, coaxial) con resalte trasero (apoyo del aro exterior de popa) con paso
    Ø drv_brg_shoulder_hole: mayor que d1 del aro interior (no roza) y menor que D1 del exterior (lo apoya);
    4 × M5 en la cara delantera para la tapa P1-DRV-06, que toma el empuje hacia proa;
  • tablero horizontal POR ENCIMA del eje, del que cuelga el alojamiento;
  • dos mejillas longitudinales (planos xz, a |y| ≥ drv_cheek_y) que bajan a dos zapatas sobre la placa
    base, a ambos lados de la abertura de la toma — nada del soporte baja entre las mejillas.
Fijación (definida por TOMA en P1-INT-02): 4 espárragos = tornillos avellanados ISO 10642 M8 × 35 A4-70
colocados desde afuera (cabeza enrasada con el fondo, en Sikaflex).
SECUENCIA DE MONTAJE (auditoría Pass 3 H2): el alojamiento es cerrado alrededor del eje, así que el pórtico
NO puede bajar vertical sobre los espárragos. Cada zapata tiene UNA RANURA de 9 mm abierta hacia POPA que
toma sus dos espárragos: (1) tuercas de los espárragos sacadas; (2) apoyar el pórtico drv_brg_travel más a
proa (alojamiento delante de la punta de proa del eje; los espárragos de proa ya quedan dentro de las
ranuras, los de popa detrás de las zapatas); (3) deslizarlo hacia popa a lo largo del eje (el resalte pasa
sobre el Ø20) hasta que los espárragos de proa toquen el fondo de las ranuras; (4) arandela ancha ISO 7093 +
tuerca a mano; (5) rodamientos, KM4/MB4, tapa; (6) alinear el alojamiento con un mandril (eje patrón Ø20
del buje del estator al alojamiento), apretar las tuercas a drv_nut_torque_Nm con Tef-Gel y escariar 2
pasadores Ø6 por zapata (toman el corte en x que la ranura no toma). Ver 06 §3 M6–M7.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build123d import Location  # noqa: E402
from cadlib import box, cyl_x, cyl_z, prism_xz  # noqa: E402
from _drv_geom import cyl_s, polar_yz, x_boat, z_axis  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-03", name="bearing_bracket", desc="Pórtico Al 6082 sobre el conducto: alojamiento 2×7204 BECBP, 4×M8 a la placa base",
            material="Al 5052/6082", process="torneada", qty=1, frame="boat", group="drive",
            load_case="Empuje Fa a punto fijo + reacción radial + 3 g vertical del tren; bulones M8 a la placa base de Al",
            print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            allow={"P1-DRV-04": 5.0, "P1-DRV-06": 5.0})

M5_TAP = 4.2          # [ESTIMADO: broca de roscar M5 (ISO 2306)]


def geom(p):
    brg = p.drv_bearing
    S_h0 = p.drv_S_brgA - p.drv_brg_shoulder_t
    S_h1 = p.drv_S_brgB
    ca = math.cos(math.radians(p.alpha))
    r_o = p.drv_hsg_od / 2
    # extremos del alojamiento en el BOTE
    xh0, xh1 = x_boat(p, S_h0), x_boat(p, S_h1)
    z_top = max(z_axis(p, S_h0), z_axis(p, S_h1)) + r_o * ca
    z_bore_top = max(z_axis(p, S_h0), z_axis(p, S_h1)) + brg["D"] / 2
    zd0 = z_bore_top + 4.0
    return dict(S_h0=S_h0, S_h1=S_h1, xh0=xh0, xh1=xh1, z_top=z_top, zd0=zd0, zd1=zd0 + p.drv_deck_t)


def build(p):
    g = geom(p)
    brg = p.drv_bearing
    cy0, cy1 = p.drv_cheek_y
    py0, py1 = p.drv_pad_y
    x0, x1 = p.brg_bracket_x0, p.brg_bracket_x1
    zb0, zb1 = p.base_top_z, p.base_top_z + p.drv_bracket_base_t
    # alojamiento (marco JET → BOTE)
    hsg = cyl_s(p.drv_hsg_od / 2, g["S_h0"], g["S_h1"]).moved(loc_jet(p))
    # tablero sobre el eje
    # el tablero no pasa los planos de las caras (inclinadas α): arista superior a r_o·sen α hacia popa
    sa = math.sin(math.radians(p.alpha))
    xd0, xd1 = g["xh0"] - p.drv_hsg_od / 2 * sa, g["xh1"] - p.drv_hsg_od / 2 * sa - 0.5
    deck = box(xd0, xd1, -cy1, cy1, g["zd0"], g["zd1"])
    # columna central tablero ↔ alojamiento (rellena entre la parte alta del alojamiento y el tablero)
    web = box(xd0 + 0.5, xd1 - 0.5, -p.drv_hsg_od / 4, p.drv_hsg_od / 4, g["zd0"] - 14.0, g["zd0"] + 1.0)
    part = hsg + deck + web
    # mejillas (trapecio en xz) y zapatas
    for sy in (-1, 1):
        ya, yb = (cy0, cy1) if sy > 0 else (-cy1, -cy0)
        pts = [(x0, zb1 - 1.0), (x1, zb1 - 1.0), (xd1, g["zd1"]), (xd0, g["zd1"])]
        part = part + prism_xz(pts, ya, yb)
        pa, pb = (py0, py1) if sy > 0 else (-py1, -py0)
        part = part + box(x0, x1, pa, pb, zb0, zb1)
    # alojamiento: agujero Ø47 H7, resalte con paso Ø collar + 3 (laberinto con el collar)
    bore = cyl_s(brg["D"] / 2, p.drv_S_brgA, g["S_h1"] + 1.0)
    bore = bore + cyl_s(p.drv_brg_shoulder_hole / 2, g["S_h0"] - 1.0, p.drv_S_brgA + 0.01)
    holes = None
    for k in range(4):
        y, z = polar_yz(p.drv_cover_bc / 2, 45 + 90 * k)
        h = cyl_x(M5_TAP / 2, -g["S_h1"] - 1.0, -g["S_h1"] + 12.0, y=y, z=z)
        holes = h if holes is None else holes + h
    part = part - (bore + holes).moved(loc_jet(p))
    # ranuras de las zapatas: una por lado, abierta hacia popa, fondo en el espárrago de proa
    for xh, yh in slot_ends(p):
        r = p.drv_bracket_hole / 2
        part = part - box(x0 - 1.0, xh, yh - r, yh + r, zb0 - 1, zb1 + 1)
        part = part - cyl_z(r, zb0 - 1, zb1 + 1, x=xh, y=yh)
    return part


def slot_ends(p):
    """(x, y) del fondo de cada ranura = espárrago de proa de cada lado."""
    out = []
    for sy in (-1, 1):
        hs = [h for h in p.brg_bracket_holes if h[1] * sy > 0]
        out.append(max(hs, key=lambda h: h[0]))
    return out


def placements(p, steer=0.0, bucket=0):
    return [Location()]


def checks(p, part):
    g = geom(p)
    brg = p.drv_bearing
    cy0, cy1 = p.drv_cheek_y
    hy = abs(p.brg_bracket_holes[0][1])
    z_axis_min = min(z_axis(p, g["S_h0"]), z_axis(p, g["S_h1"]))
    stick = p.drv_stud_L - p.base_top_z - p.drv_bracket_base_t           # espárrago sobre la zapata (cabeza enrasada con z = 0)
    As8 = 36.6                                                            # [ESTIMADO: ISO 898-1]
    F_pre = p.drv_nut_torque_Nm * 1e3 / (p.drv_nut_K * p.brg_bracket_bolt)
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("espárrago sobre la zapata ≥ arandela + tuerca + 2 hilos (2,5 mm) [mm]", stick,
         p.drv_washer_t + p.drv_nut_m + 2.5, ">="),
        ("luz vaso de la tuerca M8 (Ø18) ↔ mejilla [mm]", hy - p.drv_nut_socket_d / 2 - cy1, 2.0, ">="),
        ("precarga a par de apriete ≤ 0,7·Rp0,2·A_s del espárrago A4-70 [N]", F_pre, 0.7 * 450.0 * As8, "<="),
        ("largo del alojamiento = resalte + 2 × B [mm]", g["S_h1"] - g["S_h0"], p.drv_brg_shoulder_t + 2 * brg["B"], "="),
        ("resalte ≤ Da máx. del aro exterior: Ø paso < Da_max [mm]", p.drv_brg_shoulder_hole, brg["Da_max"], "<="),
        ("resalte no roza el aro interior: Ø paso − d1 [mm]", p.drv_brg_shoulder_hole - brg["d1"], 1.0, ">="),
        ("resalte apoya el aro exterior: D1 − Ø paso [mm]", brg["D1"] - p.drv_brg_shoulder_hole, 2.0, ">="),
        ("montaje por deslizamiento: resalte pasa sobre el eje a proa del collar (holgura radial) [mm]",
         (p.drv_brg_shoulder_hole - p.shaft_d) / 2, 2.0, ">="),
        ("montaje por deslizamiento: ranura abierta a popa toma los 2 espárragos (largo − Δx entre ellos) [mm]",
         min(xh for xh, _ in slot_ends(p)) - p.brg_bracket_x0 - (max(h[0] for h in p.brg_bracket_holes) - min(h[0] for h in p.brg_bracket_holes)), 0.0, ">="),
        ("arandela ancha puentea la ranura (Ø − ancho ≥ 2 × 6) [mm]", p.drv_washer_od - p.drv_bracket_hole, 12.0, ">="),
        ("pared del alojamiento [mm]", (p.drv_hsg_od - brg["D"]) / 2, 6.0, ">="),
        ("tablero por encima del agujero Ø47 [mm]", g["zd0"] - (max(z_axis(p, g["S_h0"]), z_axis(p, g["S_h1"])) + brg["D"] / 2), 3.0, ">="),
        ("mejillas fuera de la abertura de la toma: |y| interior − W_open/2 [mm]", cy0 - p.W_open / 2, 15.0, ">="),
        ("zapata cubre el agujero M8 con borde ≥ 1,5 d [mm]",
         min(hy - p.drv_pad_y[0], p.drv_pad_y[1] - hy), 1.5 * p.brg_bracket_bolt, ">="),
        ("agujeros M8 dentro de la huella x0…x1 [mm]",
         min(min(h[0] for h in p.brg_bracket_holes) - p.brg_bracket_x0,
             p.brg_bracket_x1 - max(h[0] for h in p.brg_bracket_holes)), 12.0, ">="),
        ("eje del alojamiento sobre la placa base [mm]", z_axis_min - p.base_top_z, 60.0, ">="),
        ("alojamiento detrás del cubo del acople (luz) [mm]", p.drv_S_cpl0 - p.drv_S_brg_front, 1.0, ">="),
        ("alojamiento delante de la caja del sello (luz) [mm]", g["S_h0"] - p.drv_S_hsg_front, 0.5, ">="),
    ]
