"""PRB-P1.9 — Juego de 2 semipasadores de corte Al 6061-T6 (P1-PMP-05) en un dispositivo de corte doble
(ensayo de taller, sin CAD).

El fusible de par del impulsor (research/R12 §7.6; sizing.mech.shear_pin) son pmp_pin_n semipasadores Ø pmp_pin_d
× pmp_pin_half_len, uno desde cada lado del agujero transversal Ø pmp_pin_hole; se tocan en el centro del eje y
cada uno cruza UNA vez la superficie del eje → 2 secciones de corte a r = shaft_d/2, el mismo T_cut que el
pasador pasante anterior. El dispositivo reproduce eso: MUÑÓN de barra 316 Ø shaft_d con el agujero
transversal (hace de eje) dentro de un MANGUITO de 316/acero con agujero Ø shaft_d H7, el mismo agujero
transversal y Ø exterior 2·pmp_land_r (= asiento del anillo retén: los semipasadores quedan enrasados como en el
cubo). Se montan los 2 semipasadores de un juego, uno desde cada lado. Muñón en la morsa, brazo de palanca de
largo L_BRAZO sobre el manguito, dinamómetro en la punta perpendicular al brazo: T = F·L. Juegos del MISMO
lote/barra que los de repuesto (R-PIN, pmp_pin_spares_sets juegos). Variante en prensa: F = 2·T/d_eje.
"""
TEST = "P1.9"
KIND = "taller"
TITULO = "Semipasadores de corte (juego de 2) en dispositivo de corte doble"
PIEZAS = ("P1-PMP-05", "P1-PMP-03", "P1-DRV-01")
BAND = (0.8, 1.2)        # [VERIFICADO: tarea — corta entre 0,8 y 1,2 × T_cut]
L_BRAZO_M = 0.50         # [SUPUESTO: palanca de 500 mm (tubo sobre el manguito)]
N_JUEGOS = 3              # [SUPUESTO: 3 juegos = 6 semipasadores, además de los de repuesto]


def build(p, ctx):
    return []


def _vals(p, ctx):
    sp = p.sz["mech"]["shear_pin"]
    lu = ctx.est.get("loads", {}).get("structural_bomba", {}).get("loads_used", {})
    T_cut = float(sp["T_cut_Nm"])
    T_ctrl = float(lu.get("T_ctrl", p.sz["mech"]["T_max_Nm"]))
    d_sh = float(p.shaft_d)
    fs_cut = float(sp["fs_shaft_at_cut"])
    return dict(d=float(sp["d_mm"]), mat=sp["material"], T_cut=T_cut, T_ctrl=T_ctrl, d_sh=d_sh, fs_cut=fs_cut,
                hole=float(p.pmp_pin_hole), tau=float(p.inp["waterjet"]["shear_pin"]["tau_u_mpa"]),
                n=int(p.pmp_pin_n), L=float(p.pmp_pin_half_len), D_mang=2 * float(p.pmp_land_r),
                spares=int(p.pmp_pin_spares_sets))


def checks(p, ctx, parts):
    v = _vals(p, ctx)
    return [("ventana: 0,8·T_cut > T máx. del controlador (no corta en marcha) [N·m]", BAND[0] * v["T_cut"], v["T_ctrl"], ">="),
            ("ventana: FS del eje a 1,2·T_cut ≥ 1,2 (criterio de sizing) [—]", v["fs_cut"] / BAND[1], 1.2, ">="),
            ("Ø del pasador = sizing.mech.shear_pin.d_mm [mm]", float(p.pmp_pin_d), v["d"], "="),
            ("semipasadores por juego = 2 (2 secciones de corte, igual que sizing) [—]", float(v["n"]), 2.0, "="),
            ("semipasador cruza la superficie del eje (largo − r_eje ≥ d) [mm]", v["L"] - v["d_sh"] / 2, v["d"], ">=")]


def criterios(p, ctx):
    v = _vals(p, ctx)
    lo, hi = BAND[0] * v["T_cut"], BAND[1] * v["T_cut"]
    return {
        "d_pin_mm": v["d"], "material": v["mat"], "agujero_mm": v["hole"], "d_eje_mm": v["d_sh"],
        "tau_u_MPa": v["tau"], "T_cut_Nm": round(v["T_cut"], 2), "T_ctrl_Nm": round(v["T_ctrl"], 2),
        "banda": list(BAND), "T_min_Nm": round(lo, 1), "T_max_Nm": round(hi, 1),
        "L_brazo_m": L_BRAZO_M, "F_brazo_min_N": round(lo / L_BRAZO_M, 0), "F_brazo_max_N": round(hi / L_BRAZO_M, 0),
        "F_prensa_min_N": round(2 * lo / (v["d_sh"] / 1000), 0), "F_prensa_max_N": round(2 * hi / (v["d_sh"] / 1000), 0),
        "n_juegos": N_JUEGOS, "semipasadores_por_juego": v["n"], "largo_semipasador_mm": v["L"],
        "D_manguito_mm": v["D_mang"], "juegos_repuesto": v["spares"],
        "fuente": "resultados/sizing.json mech.shear_pin (T_cut = 2·(π/4)d²·τ_u·d_eje/2) y estructural.json "
                  "loads.structural_bomba.loads_used.T_ctrl",
        "ensayo": f"Tornear {N_JUEGOS} juegos de {v['n']} semipasadores Ø{v['d']:g} × {v['L']:g} de la misma barra que "
                  f"los {v['spares']} juegos de repuesto (medir Ø con micrómetro y largo con calibre). Muñón Ø{v['d_sh']:g} "
                  f"en la morsa; manguito Ø{v['D_mang']:g} exterior con agujero Ø{v['d_sh']:g} H7; agujero transversal "
                  f"Ø{v['hole']:g} pasante en muñón y manguito (taladro + escariador, alineados juntos). Meter un "
                  "semipasador desde cada lado hasta que se toquen en el centro (enrasados con el Ø exterior del "
                  f"manguito). Tirar del brazo de {L_BRAZO_M * 1000:.0f} mm con el dinamómetro, despacio (~10 s hasta "
                  "el corte); anotar F máx. Después: sacar los restos con un botador corto desde un lado (es el "
                  "procedimiento de cambio en el eje real).",
        "pasa_si": f"Los {N_JUEGOS} juegos cortan entre {lo:.1f} y {hi:.1f} N·m ({BAND[0]:g}–{BAND[1]:g} × T_cut) = "
                   f"{lo / L_BRAZO_M:.0f}–{hi / L_BRAZO_M:.0f} N en el brazo, con las 2 secciones cortadas en la cara "
                   "muñón ↔ manguito (una por semipasador) y los restos salen con el botador. Si cortan abajo: barra "
                   "más blanda (no T6) → cambiar de barra; si cortan arriba: no subir el Ø, revisar material y "
                   "agujeros (filo vivo); si un solo semipasador corta: agujeros desalineados.",
    }
