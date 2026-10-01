"""PRB-P1.2 — Alojamiento de rodamiento (PENDIENTES_GASPAR §P1.2).

PENDIENTES cita el 6002 (Ø32); el diseño vigente usa el rodamiento de inputs.yaml → bearings
(hoy 6202-2RS 15×35×11, decisiones D-37). La probeta lee D y B de params, así que sigue al diseño.
Asientos (eje vertical, como el alojamiento de HSG-02 impreso con u = Z):
  D − 0,15 / D − 0,10 / D − 0,05 (+ geometry.press_fit_mm si difiere)  → ajuste a presión
  D + δ_HSG02 (δ leído del puente P1-HSG-02: hoy +0,10, rodamiento B flotante) → ajuste deslizante
Pared del anillo = pared mínima real del alojamiento en HSG-02 (escaneada), con labio inferior
para que el rodamiento haga tope y pueda sacarse empujando el aro exterior.
Los anillos van separados (no comparten pared) y unidos por una franja de 2 mm con rótulos.
"""
from cadlib import *  # noqa: F401,F403
from _probelib import label, fmt_mm, cyl_faces, scan

TEST = "P1.2"
PRESS_BASE = [-0.15, -0.10, -0.05]   # [VERIFICADO: PENDIENTES_GASPAR §P1.2]
LIP = 1.5                            # labio inferior [SUPUESTO]
GAP = 4.0
TAB_T, TAB_W = 2.0, 9.0
WALL_FALLBACK = 4.5                  # [SUPUESTO: si no se puede escanear HSG-02]


def _hsg02(ctx):
    """(holgura del alojamiento en HSG-02, pared mínima radial) leídas de la pieza real."""
    p = ctx.p
    part = ctx.built("P1-HSG-02")
    best = None
    for cf in cyl_faces(part):
        if cf["hole"] and abs(abs(cf["d"].X) - 1) < 1e-3:                 # eje u (X del marco unidad)
            dD = 2 * cf["r"] - p.brg_D
            if -0.3 <= dD <= 0.5 and (best is None or abs(dD) < abs(best[0])):
                best = (dD, cf["loc"])
    if best is None:
        ctx.notes.append("P1.2: no se halló el alojamiento en HSG-02; δ = +0,10 y pared por defecto")
        return 0.10, WALL_FALLBACK
    dD, loc = best
    u_mid = p.bridge_u_aft - p.brg_B / 2                                  # mitad del asiento
    walls = []
    for dy, dz in ((1, 0), (-1, 0), (0, -1), (0, 1), (0.7071, -0.7071), (-0.7071, -0.7071)):
        tr = scan(part, (u_mid, loc.Y, loc.Z), (0, dy, dz), 80.0, step=0.25)
        # desde el eje: primero vacío (agujero), luego sólido, luego vacío (exterior)
        ins = [s for s, now_in in tr if now_in]
        outs = [s for s, now_in in tr if not now_in]
        if ins and outs:
            s_in = ins[0]
            s_out = next((s for s in outs if s > s_in), None)
            if s_out is not None:
                walls.append(s_out - s_in)
    wall = min(walls) if walls else WALL_FALLBACK
    return round(dD, 3), round(wall, 2)


def offsets(p, ctx):
    dfit, _ = _hsg02(ctx)
    press = sorted({round(c, 3) for c in PRESS_BASE + [float(p.press)]})
    return press, dfit


def build(p, ctx):
    press, dfit = offsets(p, ctx)
    _, wall = _hsg02(ctx)
    wall = max(wall, p.wall)
    D, B = float(p.brg_D), float(p.brg_B)
    offs = press + [dfit]
    H = B + LIP
    x = 0.0
    s = None
    xs = []
    for o in offs:
        od = D + o + 2 * wall
        xc = x + od / 2
        ring = cyl_z(od / 2, 0, H, x=xc) - cyl_z((D + o) / 2, LIP, H + 1, x=xc) \
            - cyl_z((D - 6.0) / 2, -1, LIP + 1, x=xc)                      # labio: el aro exterior apoya 3 mm
        s = ring if s is None else s + ring
        xs.append((xc, od, o))
        x += od + GAP
    odm = max(od for _, od, _ in xs)
    tab = box(0, x - GAP, -odm / 2 - TAB_W, 0, 0, TAB_T)
    for xc, od, o in xs:
        tab = tab - cyl_z((D - 6.0) / 2, -1, TAB_T + 1, x=xc)
    s = s + tab
    for xc, od, o in xs:
        s = s + label(fmt_mm(o), xc, -odm / 2 - TAB_W / 2, TAB_T, size=4.5)
    meta = dict(id="P1.2", name="alojamiento_rodamiento",
                desc=f"Asientos Ø{D:g}{'/'.join(fmt_mm(o) for o in offs)} para {p.inp['bearings']['name']}, "
                     f"pared {wall:.2f} mm (= HSG-02), labio {LIP} mm",
                test=TEST, profile="estructural", qty=2, solid_frac=1.0,
                orientation="Eje del rodamiento vertical (Z), como HSG-02 (u = Z): asiento redondo en XY.")
    return [(meta, s)]


def checks(p, ctx, parts):
    press, dfit = offsets(p, ctx)
    part = parts["P1.2"]
    D = float(p.brg_D)
    hole_d = {round(2 * cf["r"], 3) for cf in cyl_faces(part) if cf["hole"]}
    out = [(f"asiento Ø{D + o:.2f} presente", float(any(abs(h - (D + o)) < 0.005 for h in hole_d)), 1.0, ">=")
           for o in press + [dfit]]
    out.append(("press_fit_mm de inputs.yaml incluido", float(round(float(p.press), 3) in press), 1.0, ">="))
    return out


def criterios(p, ctx):
    press, dfit = offsets(p, ctx)
    _, wall = _hsg02(ctx)
    return {
        "rodamiento": p.inp["bearings"]["name"], "D_mm": float(p.brg_D), "B_mm": float(p.brg_B),
        "asientos_presion_mm": press, "asiento_HSG02_mm": dfit, "pared_mm": wall,
        "ensayo": "Prensar el rodamiento a mano/prensa de banco (o tornillo y arandelas) en cada asiento a presión; "
                  "insertar a mano en el asiento deslizante. Revisar con lupa 10× a las 24 h.",
        "pasa_si": "Asiento a presión: entra con prensa sin fisurar ni blanquear el anillo y el aro exterior no gira "
                   "con la mano → actualizar geometry.press_fit_mm al valor menos interferente que cumple. "
                   f"Asiento {fmt_mm(dfit)} (HSG-02, rodamiento B flotante): entra y se desliza axialmente a mano, "
                   "sin juego radial perceptible.",
        "nota": "PENDIENTES_GASPAR §P1.2 menciona 6002 Ø32: el diseño vigente es "
                f"{p.inp['bearings']['name']} (Ø{p.brg_D:g}); la probeta sigue a inputs.yaml.",
    }
