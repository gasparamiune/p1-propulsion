"""PRB-P1.9 — Pasador de corte Al 6061-T6 (P1-PMP-05) en un dispositivo de corte doble (ensayo de taller, sin CAD).

El pasador es el fusible de par del impulsor (research/R12 §7.6; sizing.mech.shear_pin). El dispositivo
reproduce el corte doble real: MUÑÓN de barra 316 Ø shaft_d con agujero transversal Ø pmp_pin_hole (hace de
eje) dentro de un MANGUITO de 316/acero con agujero Ø shaft_d H7 y el mismo agujero transversal (hace de cubo
del impulsor). Muñón en la morsa, brazo de palanca de largo L_BRAZO sobre el manguito, dinamómetro en la punta
perpendicular al brazo: T = F·L. Se ensayan pasadores del MISMO lote/barra que los de repuesto (R-PIN).
Variante en prensa (corte doble lineal): F = 2·T/d_eje, la misma τ en las dos secciones.
"""
TEST = "P1.9"
KIND = "taller"
TITULO = "Pasador de corte en dispositivo de corte doble"
PIEZAS = ("P1-PMP-05", "P1-PMP-03", "P1-DRV-01")
BAND = (0.8, 1.2)        # [VERIFICADO: tarea — corta entre 0,8 y 1,2 × T_cut]
L_BRAZO_M = 0.50         # [SUPUESTO: palanca de 500 mm (tubo sobre el manguito)]
N_PROBETAS = 3


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
                hole=float(p.pmp_pin_hole), tau=float(p.inp["waterjet"]["shear_pin"]["tau_u_mpa"]))


def checks(p, ctx, parts):
    v = _vals(p, ctx)
    return [("ventana: 0,8·T_cut > T máx. del controlador (no corta en marcha) [N·m]", BAND[0] * v["T_cut"], v["T_ctrl"], ">="),
            ("ventana: FS del eje a 1,2·T_cut ≥ 1,2 (criterio de sizing) [—]", v["fs_cut"] / BAND[1], 1.2, ">="),
            ("Ø del pasador = sizing.mech.shear_pin.d_mm [mm]", float(p.pmp_pin_d), v["d"], "=")]


def criterios(p, ctx):
    v = _vals(p, ctx)
    lo, hi = BAND[0] * v["T_cut"], BAND[1] * v["T_cut"]
    return {
        "d_pin_mm": v["d"], "material": v["mat"], "agujero_mm": v["hole"], "d_eje_mm": v["d_sh"],
        "tau_u_MPa": v["tau"], "T_cut_Nm": round(v["T_cut"], 2), "T_ctrl_Nm": round(v["T_ctrl"], 2),
        "banda": list(BAND), "T_min_Nm": round(lo, 1), "T_max_Nm": round(hi, 1),
        "L_brazo_m": L_BRAZO_M, "F_brazo_min_N": round(lo / L_BRAZO_M, 0), "F_brazo_max_N": round(hi / L_BRAZO_M, 0),
        "F_prensa_min_N": round(2 * lo / (v["d_sh"] / 1000), 0), "F_prensa_max_N": round(2 * hi / (v["d_sh"] / 1000), 0),
        "n_probetas": N_PROBETAS,
        "fuente": "resultados/sizing.json mech.shear_pin (T_cut = 2·(π/4)d²·τ_u·d_eje/2) y estructural.json "
                  "loads.structural_bomba.loads_used.T_ctrl",
        "ensayo": f"Tornear {N_PROBETAS} pasadores Ø{v['d']:g} de la misma barra que los de repuesto (medir Ø con "
                  f"micrómetro). Muñón Ø{v['d_sh']:g} en la morsa, manguito con agujero Ø{v['d_sh']:g} H7 y ambos "
                  f"agujeros transversales Ø{v['hole']:g} (taladro + escariador, alineados juntos). Tirar del brazo "
                  f"de {L_BRAZO_M * 1000:.0f} mm con el dinamómetro, despacio (~10 s hasta el corte); anotar F máx.",
        "pasa_si": f"Los {N_PROBETAS} cortan entre {lo:.1f} y {hi:.1f} N·m ({BAND[0]:g}–{BAND[1]:g} × T_cut) = "
                   f"{lo / L_BRAZO_M:.0f}–{hi / L_BRAZO_M:.0f} N en el brazo, en corte doble limpio (dos secciones). "
                   "Si cortan abajo: barra más blanda (no T6) → cambiar de barra; si cortan arriba: no subir el Ø, "
                   "revisar material y agujeros (filo vivo).",
    }
