"""PRB-P1.12 — Medición de la holgura de punta impulsor ↔ anillo de desgaste (ensayo de taller, sin CAD).

Holgura de diseño radial sizing.pump.tip_clearance_mm (= tip_clearance_frac × D, research/R12 §3: 0,3–0,4 mm
con el anillo torneado en sitio). Ø del anillo P1-PMP-02 = D + 2·holgura (params D_bore). Se mide montado: el
impulsor en el eje con sus rodamientos (el juego de los rodamientos y el desbalance cuentan).
"""
import math

TEST = "P1.12"
KIND = "taller"
TITULO = "Holgura de punta impulsor ↔ anillo de desgaste"
PIEZAS = ("P1-PMP-02", "P1-PMP-03")
C_MIN_MM = 0.30          # [VERIFICADO: research/R12 §3 (inputs.yaml waterjet.tip_clearance_frac): 0,3–0,4 mm]
DISP_MAX_MM = 0.05       # [SUPUESTO: diferencia máx. entre lecturas (excentricidad / alabeo de puntas)]


def build(p, ctx):
    return []


def _v(p):
    pu = p.sz["pump"]
    c = float(pu["tip_clearance_mm"])
    return dict(D=float(pu["D_mm"]), c=c, c_max=math.ceil(c * 100 - 1e-9) / 100, D_bore=float(p.D_bore),
                Z=int(pu["blades"]))


def checks(p, ctx, parts):
    v = _v(p)
    return [("Ø anillo = D + 2·holgura [mm]", v["D_bore"], v["D"] + 2 * v["c"], "="),
            ("holgura de diseño dentro de la ventana [mm]", v["c"], C_MIN_MM, ">=")]


def criterios(p, ctx):
    v = _v(p)
    return {
        "D_imp_mm": v["D"], "D_anillo_mm": round(v["D_bore"], 3), "c_diseno_mm": round(v["c"], 3),
        "c_min_mm": C_MIN_MM, "c_max_mm": v["c_max"], "dispersion_max_mm": DISP_MAX_MM, "alabes": v["Z"],
        "fuente": "resultados/sizing.json pump.tip_clearance_mm y pump.D_mm; params D_bore",
        "ensayo": f"Anillo montado en la carcasa; impulsor en el eje con rodamientos y pasador. Galgas de espesores "
                  f"entre la punta de cada uno de los {v['Z']} álabes y el anillo, en la entrada, al medio y a la salida "
                  "de la punta, girando a mano; repetir en 4 posiciones angulares del eje. Control cruzado: Ø del "
                  "anillo con alesómetro y Ø de puntas del impulsor en el torno (reloj comparador sobre mandril).",
        "pasa_si": f"Todas las lecturas entre {C_MIN_MM:.2f} y {v['c_max']:.2f} mm y diferencia máx. − mín. ≤ "
                   f"{DISP_MAX_MM:.2f} mm; el impulsor gira sin roce. Menor: repasar el anillo (no el impulsor); "
                   "mayor: anillo nuevo (el anillo es la pieza de desgaste).",
    }
