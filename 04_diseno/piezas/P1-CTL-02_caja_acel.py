"""P1-CTL-02 — Caja de la unidad de palancas (acelerador + bucket), PETG impreso.

Tapa/cubierta sobre el recorte de la tapa de la consola (la estructura es la placa central Al
P1-CTL-08): ranuras para los dos mangos con sus recorridos, alojamiento del sensor hall A1324 en la
pared −y (piel de 1 mm, encapsulado en epoxi; entrehierro al imán del eje = CTL_hall_gap, como pide el
firmware: calibración T0.5), salida del cable del sensor por prensaestopas M16 (R08a) y ala con 4 × M5
a la consola. Rótulos en relieve "0 / AVANCE / REVERSA" y "BUCKET ARRIBA / ABAJO" (no modelados)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cadlib import box, cyl_y, cyl_z  # noqa: E402
import _ctl as U  # noqa: E402

META = dict(
    id="P1-CTL-02", name="caja_acel", desc="Caja PETG de palancas con sensor hall",
    material="PETG", process="impresa", qty=1, frame="boat", group="ele",
    load_case="Pisada/golpe 300 N sobre la tapa [SUPUESTO]; sin cargas de mando (van a P1-CTL-08)",
    print_rot=(180, 0, 0), solid_frac=0.55,
    orientation="Tapa sobre la cama (ranuras planas, sin soportes); ala arriba. 0,2 mm, 5 perímetros, 30 % giroide",
)
X0, X1 = -95.0, 62.0
Y0, Y1 = -27.0, 27.5
ZT = 40.0
W = 3.5
WT = 6.0          # tapa (mano apoyada 150 N, structural_direccion)
SENSOR = (5.0, 4.5, 2.5)     # bolsillo del A1324 (x, z, y) [ESTIMADO: SIP-3 4,1 × 3 × 1,5 + epoxi]


def slot(p, ylo, yhi, th_min, th_max, half_w):
    zt = ZT
    xa = min(zt * math.tan(math.radians(th_min)), (zt - WT) * math.tan(math.radians(th_min)))
    xb = max(zt * math.tan(math.radians(th_max)), (zt - WT) * math.tan(math.radians(th_max)))
    pad = half_w / math.cos(math.radians(max(abs(th_min), abs(th_max)))) + 2.0
    return box(xa - pad, xb + pad, ylo, yhi, zt - WT - 1, zt + 1)


def build_local(p):
    zb = U.top_local(p)
    s = box(X0, X1, Y0, Y1, zb, ZT) - box(X0 + W, X1 - W, Y0 + W, Y1 - W, zb - 1, ZT - WT)
    s = s + (box(X0 - 12, X1 + 12, Y0 - 12, Y1 + 12, zb, zb + 4) - box(X0 + W, X1 - W, Y0 + W, Y1 - W, zb - 1, zb + 5))
    s = s - slot(p, U.Y_THR[0] - 2, U.Y_THR[1] + 2, -p.CTL_thr_rev, p.CTL_thr_fwd, 8.0)
    s = s - slot(p, U.Y_BKT[0] - 2, U.Y_BKT[1] + 2, -p.CTL_bkt_travel, 0.0, 8.0)
    # sensor hall: bolsillo desde afuera dejando 1 mm de piel
    sx, sz, sy = SENSOR
    yin = Y0 + W
    s = s - box(-sx / 2, sx / 2, Y0 - 1, yin - 1.0, -sz / 2, sz / 2)
    s = s - box(-1.5, 1.5, Y0 - 1, yin - 1.0, -14, 0)                       # canal de los terminales
    s = s - cyl_y(8.25, Y0 - 1, Y0 + W + 1, x=-30.0, z=zb + 14)              # prensaestopas M16 del sensor
    for xx in (X0 - 6, X1 + 6):
        for yy in (Y0 - 6, Y1 + 6):
            s = s - cyl_z(2.75, zb - 1, zb + 5, x=xx, y=yy)
    return s


def build(p):
    return U.unit_loc(p) * build_local(p)


def placements(p, steer=0.0, bucket=0):
    from build123d import Location
    return [Location()]


def checks(p, part):
    gap = (U.Y_HEAD[0]) - (Y0 + W - 1.0) - 0.0
    hub_clear = min((X1 - W) - U.HUB_R, -(X0 + W) - (U.CRANK_R + 9.0))
    return [("un solo sólido", len(part.solids()), 1, "="),
            ("entrehierro imán ↔ cara del sensor [mm]", U.Y_HEAD[0] - (Y0 + W - 1.0), p.CTL_hall_gap, "="),
            ("luz cabeza del eje ↔ pared [mm]", U.Y_HEAD[0] - (Y0 + W), 1.0, ">="),
            ("manivela dentro de la caja (x) [mm]", hub_clear, 2.0, ">="),
            ("cubo de palanca bajo la tapa (z) [mm]", (ZT - WT) - U.HUB_R, 3.0, ">="),
            ("pared mínima [mm]", W, p.wall, ">=")]
