"""PRB-P1.6 — Tapa con O-ring de cara y purga, representativa de P1-INT-04, a la presión de la chimenea.

Réplica REDUCIDA de la tapa de inspección (misma sección, distinto diámetro):
  • P1.6B tapa: mismo espesor toma_cover_t, misma ranura de cara (toma_gl_depth × toma_gl_width → cordón
    NBR Ø oring_cs, research/R05 B3), misma distancia ranura ↔ boca y ranura ↔ agujeros M6 que INT-04
    (oring_r), mismos 4 × Ø(6 + bolt_clr), mismo resalte de purga con tuerca M6 cautiva en hexágono desde la
    cara de cama (INT-04.BOSS_D/BOSS_H, NUT_AF[6] + 0,3); se imprime igual (ranura sobre la cama) y con el
    perfil de INT-04 (familias.py).
  • P1.6A caja: hace de brida de la chimenea (en la pieza real es Al 5083 de P1-INT-01): brida de
    toma_chim_fl_t con los mismos radios relativos, 4 × M6 pasantes con tuerca abajo, vaso cerrado y un
    agujero en el piso para una válvula de neumático de tuerca (presión con inflador, vacío sin el obús).
Boca de la probeta BOCA_D [SUPUESTO] (la real es toma_chim_id): con la purga al centro, entra el hexágono.
Presión de ensayo = presión de cierre de la bomba (sizing loads.p_pump_max_Pa = estructural.json
structural_toma.p_max_Pa), que la tapa ve como succión en punto fijo y como contrapresión.
"""
import importlib.util
import math

from build123d import Align, Cone, Pos

from cadlib import *  # noqa: F401,F403
from _probelib import label, cyl_faces
import familias as FAM

TEST = "P1.6"
KIND = "impresa"
TITULO = "Tapa con O-ring de cara y purga (réplica de P1-INT-04) a la presión de la chimenea"
PIEZAS = ("P1-INT-04", "P1-INT-01")
SRC = "P1-INT-04"
BOCA_D = 60.0          # [SUPUESTO: boca reducida; la purga va al centro]
POT_WALL = 6.0         # pared del vaso [SUPUESTO: ≥ 2 × min_wall; ve p_cierre]
H_CYL = 10.0           # tramo cilíndrico de la cavidad (= espesor de brida) [SUPUESTO: volumen chico = poca energía]
R_TOP = 8.0            # meseta del techo cónico donde va la válvula [SUPUESTO: > VALVE_D/2]
POT_FLOOR = 6.0        # techo del vaso (piso en uso)
VALVE_D = 11.5         # válvula de neumático de tuerca (clamp-in) en el piso [ESTIMADO: agujero de llanta 11,3–11,5; buscar
                       # "clamp-in tire valve 11.5 mm" y confirmar el espesor de pared admitido ≥ POT_FLOOR]
HOLD_MIN = 15          # [SUPUESTO: tiempo de retención]
DROP_FRAC = 0.10       # [SUPUESTO: caída admisible de presión en HOLD_MIN (incluye temperatura del aire)]
R05_DEPTH = (2.57, 2.72)  # [VERIFICADO: research/R05 B3 (Parker 4-3), cordón 3,53]
R05_WIDTH = (4.50, 4.75)  # [VERIFICADO: idem]


def _int04(ctx):
    return ctx.part(SRC)


def dims(p, ctx):
    m = _int04(ctx)
    gap_bolt = p.toma_chim_bc / 2 - p.toma_chim_id / 2          # boca → círculo de agujeros (= INT-04)
    gap_rim = p.toma_chim_fl_od / 2 - p.toma_chim_bc / 2         # agujeros → borde (= INT-04)
    rb = BOCA_D / 2
    bc = 2 * (rb + gap_bolt)
    od = bc + 2 * gap_rim
    rm = 0.5 * (rb + bc / 2 - (6 + p.bolt_clr) / 2)               # misma regla que INT-04.oring_r
    return dict(rb=rb, bc=bc, od=od, rm=rm, w=p.toma_gl_width, dep=p.toma_gl_depth, t=p.toma_cover_t,
                boss_d=m.BOSS_D, boss_h=m.BOSS_H, t_fl=p.toma_chim_fl_t)


def build(p, ctx):
    d = dims(p, ctx)
    rm, w, dep, t = d["rm"], d["w"], d["dep"], d["t"]
    hole = (6 + p.bolt_clr) / 2
    # --- tapa (cara de la ranura sobre la cama, z = 0)
    lid = cyl_z(d["od"] / 2, 0, t)
    lid = lid - (cyl_z(rm + w / 2, -1, dep) - cyl_z(rm - w / 2, -2, dep + 1))
    lid = lid + cyl_z(d["boss_d"] / 2, t - 0.5, t + d["boss_h"])
    lid = lid - hex_prism_z(NUT_AF[6] + 0.3, -1, NUT_M[6] + 0.2)
    lid = lid - cyl_z(hole, -1, t + d["boss_h"] + 1)
    pts = [(d["bc"] / 2 * math.cos(math.radians(45 + 90 * k)), d["bc"] / 2 * math.sin(math.radians(45 + 90 * k)))
           for k in range(4)]
    for (x, y) in pts:
        lid = lid - cyl_z(hole, -1, t + 1, x=x, y=y)
    lid = lid + label("P1.6", 0, -(d["boss_d"] / 2 + d["rb"]) / 2 - 2, t, size=6.0)
    # --- caja: se imprime BOCA ABAJO (cara de la brida sobre la cama, lisa y plana como la de la tapa);
    #     techo interior cónico a 45° (sin puentes) hasta una meseta Ø2·R_TOP con la válvula
    ro = d["rb"] + POT_WALL
    h_cone = d["rb"] - R_TOP                                       # 45°
    ztop = H_CYL + h_cone + POT_FLOOR
    pot = cyl_z(ro, 0, ztop) + cyl_z(d["od"] / 2, 0, d["t_fl"])
    cav = cyl_z(d["rb"], -1, H_CYL) + (Pos(0, 0, H_CYL) * Cone(d["rb"], R_TOP, h_cone, align=(Align.CENTER,) * 2 + (Align.MIN,)))
    cav = cav + cyl_z(R_TOP, H_CYL + h_cone - 0.5, H_CYL + h_cone)
    pot = pot - cav
    for (x, y) in pts:
        pot = pot - cyl_z(hole, -1, d["t_fl"] + 1, x=x, y=y)
    pot = pot - cyl_z(VALVE_D / 2, H_CYL + h_cone - 1, ztop + 1)
    fam = FAM.familia({"id": SRC})[0]
    rot = _int04(ctx).META["print_rot"]
    return [
        (dict(id="P1.6A", name="caja_brida", desc=f"Vaso Ø{2 * ro:g} × {ztop:g} con brida Ø{d['od']:g} × {d['t_fl']:g} "
              f"(hace de chimenea), boca Ø{BOCA_D:g}, 4 × M6 en Ø{d['bc']:g}, válvula de neumático Ø{VALVE_D:g} en el piso",
              test=TEST, profile=fam, qty=1, solid_frac=1.0,
              orientation="Boca abajo: cara de sello de la brida sobre la cama (lisa y plana); techo cónico 45°, sin soportes."),
         pot),
        (dict(id="P1.6B", name="tapa_oring_purga", desc=f"Tapa Ø{d['od']:g} × {t:g} (= espesor de {SRC}), ranura "
              f"{dep:.2f} × {w:.2f} en r = {rm:.1f}, resalte de purga Ø{d['boss_d']:g} con tuerca M6 cautiva, 4 × M6",
              test=TEST, profile=fam, qty=1, solid_frac=1.0,
              orientation=f"Como {SRC}: cara de la ranura y del hexágono sobre la cama (fondos lisos), resalte arriba."),
         to_print(lid, rot)),
    ]


def checks(p, ctx, parts):
    d = dims(p, ctx)
    m = _int04(ctx)
    rm_real = m.oring_r(p)
    lid = parts["P1.6B"]
    radii = {round(cf["r"], 3) for cf in cyl_faces(lid)}
    hole = (6 + p.bolt_clr) / 2
    return [
        ("profundidad de ranura ≥ 2,57 (R05) [mm]", d["dep"], R05_DEPTH[0], ">="),
        ("profundidad de ranura ≤ 2,72 (R05) [mm]", d["dep"], R05_DEPTH[1], "<="),
        ("ancho de ranura ≥ 4,50 (R05) [mm]", d["w"], R05_WIDTH[0], ">="),
        ("ancho de ranura ≤ 4,75 (R05) [mm]", d["w"], R05_WIDTH[1], "<="),
        ("labio interior ranura ↔ boca = INT-04 [mm]", (d["rm"] - d["w"] / 2 - d["rb"]) -
         (rm_real - d["w"] / 2 - p.toma_chim_id / 2), 0.0, "="),
        ("labio exterior ranura ↔ agujero M6 = INT-04 [mm]", (d["bc"] / 2 - hole - d["rm"] - d["w"] / 2) -
         (p.toma_chim_bc / 2 - hole - rm_real - d["w"] / 2), 0.0, "="),
        ("ranura modelada en la tapa (radio exterior) [mm]", float(round(d["rm"] + d["w"] / 2, 3) in radii), 1.0, "="),
        ("purga (hexágono M6) dentro de la boca [mm]", d["rb"] - (NUT_AF[6] + 0.3) / math.sqrt(3), 2.0, ">="),
        ("resalte de purga dentro del O-ring [mm]", (d["rm"] - d["w"] / 2) - d["boss_d"] / 2, 0.0, ">="),
        ("espesor de la tapa = INT-04 [mm]", lid.bounding_box().max.Z - d["boss_h"], p.toma_cover_t, "="),
    ]


def criterios(p, ctx):
    d = dims(p, ctx)
    sz = p.sz["loads"]
    est = ctx.est.get("loads", {}).get("structural_toma", {})
    p_test = float(est.get("p_max_Pa", sz["p_pump_max_Pa"]))
    perim = 2 * math.pi * d["rm"]
    h_c = d["rb"] - R_TOP
    vol = math.pi * d["rb"] ** 2 * H_CYL + math.pi * h_c / 3 * (d["rb"] ** 2 + d["rb"] * R_TOP + R_TOP ** 2)   # mm³
    energia = p_test * vol * 1e-9                                  # J (cota superior: p·V)
    return {
        "vol_cavidad_cm3": round(vol / 1000, 0), "energia_J": round(energia, 1),
        "p_ensayo_Pa": round(p_test, 0), "p_ensayo_kPa": round(p_test / 1000, 1),
        "fuente_presion": "estructural.json loads.structural_toma.p_max_Pa = sizing loads.p_pump_max_Pa (cierre)",
        "p_ram_kPa": round(float(est.get("p_ram_Pa", 0)) / 1000, 1),
        "dp_ciclo_kPa": round(float(est.get("dp_cyc_Pa", 0)) / 1000, 1),
        "retencion_min": HOLD_MIN, "caida_max_frac": DROP_FRAC,
        "caida_max_kPa": round(DROP_FRAC * p_test / 1000, 1),
        "ranura_mm": [round(d["dep"], 3), round(d["w"], 3)], "rango_R05_mm": [R05_DEPTH, R05_WIDTH],
        "cordon_mm": p.oring_cs, "largo_cordon_mm": round(perim, 0),
        "largo_cordon_INT04_mm": round(2 * math.pi * _int04(ctx).oring_r(p), 0),
        "planitud_max_mm": 0.10,
        "planitud_base": "[CALCULADO: ±0,15 mm de profundidad mantiene la compresión en 21–29 % (research/R05 B3)]",
        "ensayo": "Medir ranura (profundidad y ancho) y planitud de las dos caras de sello (regla + galgas). Cordón "
                  "NBR70 con empalme a tope y grasa de silicona; 4 × M6 A4 con arandela ancha apretados a mano (perillas, "
                  "como INT-04); purga M6 × 12 con arandela de estanqueidad. Conjunto con la tapa arriba (como en el "
                  "bote), apoyado en dos listones (la válvula queda abajo); un dedo de agua adentro para mojar el O-ring. "
                  f"(1) +p con inflador con manómetro, {HOLD_MIN} min, agua jabonosa por fuera; (2) −p con bomba de vacío "
                  f"manual (válvula sin obús), {HOLD_MIN} min; (3) 20 ciclos abrir/cerrar tapa y purga, repetir (1). "
                  f"Con aire la energía guardada es chica (cavidad {vol / 1000:.0f} cm³: p·V = {energia:.1f} J "
                  "[CALCULADO]); igual, gafas.",
        "pasa_si": f"En (1), (2) y (3): caída ≤ {DROP_FRAC * 100:.0f} % de la presión de ensayo en {HOLD_MIN} min, "
                   "0 gotas en el O-ring y en la purga (papel tisú alrededor) y sin burbujas con agua jabonosa; sin "
                   "fisura ni blanqueo en el resalte de la purga. Si gotea: separar O-ring / purga / poros repitiendo "
                   "con la purga sellada con teflón.",
    }
