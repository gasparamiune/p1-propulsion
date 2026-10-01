"""PRB-P1.8 — Cuello (cintura fusible) del patín P1-PRP-02 (PENDIENTES_GASPAR §P1.8).

La probeta es un RECORTE del patín real: lengüeta (con sus 2 agujeros M6, que se sujeta como en la
ranura de STR-01) + cintura de sección skeg_neck_len × skeg_t hasta el fin del tramo recto, más un
brazo ensanchado (más resistente que la cintura) con el agujero de carga a skeg_neck_lever de la
sección de referencia skeg_neck_v (= mismo brazo de palanca que la punta del patín). Se tira con
el dinamómetro en el plano del patín, perpendicular al brazo, como la fuerza horizontal en la punta.
Se imprime como el patín (META.print_rot de PRP-02: plano u–v en la cama) y con el perfil FUSIBLE.
"""
from cadlib import *  # noqa: F401,F403
from _probelib import scan, label_on_plane, Plane, petg

TEST = "P1.8"
SRC = "P1-PRP-02"
HOLE_D = 8.5          # agujero de carga (gancho/grillete) [SUPUESTO]
EDGE = 12.0           # borde más allá del agujero [SUPUESTO]


def geo(p, ctx):
    m = ctx.part(SRC)
    um = 0.5 * (p.u_lh_fwd + p.u_lh_aft)
    L = p.skeg_neck_len
    v_root = -p.e - m.LH_BOTTOM
    pts = m.profile(p)
    v_ends = [v for (u, v) in pts if (abs(u - (um + L / 2)) < 1e-6 or abs(u - (um - L / 2)) < 1e-6)
              and v < v_root - 1e-6]
    v_cut = max(v_ends)                                   # fin del tramo recto común a ambos lados
    vn = p.skeg_neck_v
    v_tip = vn - p.skeg_neck_lever
    A = max(2 * L, 30.0)
    return dict(um=um, L=L, t=p.skeg_t, v_root=v_root, v_cut=v_cut, vn=vn, v_tip=v_tip, A=A,
                top=v_root + m.TONGUE)


def unit_frame(p, ctx):
    """Probeta en el marco UNIDAD del patín (X=u, Y=w, Z=v)."""
    g = geo(p, ctx)
    sk = ctx.built(SRC)
    um, L, t = g["um"], g["L"], g["t"]
    cut = sk & box(um - 40, um + 40, -t, t, g["v_cut"], g["top"] + 1)
    A = g["A"]
    vw = g["v_cut"] - (A - L) / 2
    arm = prism_xz([(um - L / 2, g["v_cut"] + 0.5), (um + L / 2, g["v_cut"] + 0.5), (um + L / 2, g["v_cut"]),
                    (um + A / 2, vw), (um + A / 2, g["v_tip"] - EDGE), (um - A / 2, g["v_tip"] - EDGE),
                    (um - A / 2, vw), (um - L / 2, g["v_cut"])], -t / 2, t / 2)
    arm = arm - cyl_y(HOLE_D / 2, -t, t, x=um, z=g["v_tip"])
    s = cut + arm
    pl = Plane(origin=(um, t / 2, 0.5 * (vw + g["v_tip"])), x_dir=(0, 0, -1), z_dir=(0, 1, 0))
    return s + label_on_plane(f"P1.8 L{p.skeg_neck_lever:.0f}", pl, size=5.0)


def build(p, ctx):
    s = unit_frame(p, ctx)
    L = p.skeg_neck_len
    t = p.skeg_t
    rot = ctx.part(SRC).META["print_rot"]
    meta = dict(id="P1.8", name="cuello_patin",
                desc=f"Lengüeta + cintura {L:.2f}×{t:g} mm del patín real + brazo; carga a {p.skeg_neck_lever:.1f} mm "
                     f"de la sección de referencia (agujero Ø{HOLE_D})",
                test=TEST, profile="fusible", qty=6, solid_frac=ctx.part(SRC).META.get("solid_frac", 1.0),
                orientation="Como el patín PRP-02: plano u–v en la cama (espesor skeg_t = Z), flexión en el plano de capas.")
    return [(meta, to_print(s, rot))]


def _neck_width(part, u_c, v):
    tr = scan(part, (u_c - 60, 0.0, v), (1, 0, 0), 120.0, step=0.05)
    ins = [s for s, now_in in tr if now_in]
    outs = [s for s, now_in in tr if not now_in]
    return (outs[0] - ins[0]) if ins and outs else 0.0


def checks(p, ctx, parts):
    g = geo(p, ctx)
    s_unit = unit_frame(p, ctx)
    real = _neck_width(ctx.built(SRC), g["um"], g["vn"])
    probe = _neck_width(s_unit, g["um"], g["vn"])
    return [("ancho de cintura del patín real en skeg_neck_v = skeg_neck_len [mm]", real, p.skeg_neck_len, "="),
            ("ancho de cintura de la probeta = patín real [mm]", probe, real, "="),
            ("brazo: agujero de carga − sección de referencia = skeg_neck_lever [mm]", g["vn"] - g["v_tip"],
             p.skeg_neck_lever, "="),
            ("brazo más ancho que la cintura (rompe en la cintura) [mm]", g["A"], 1.3 * p.skeg_neck_len, ">=")]


def criterios(p, ctx):
    g = geo(p, ctx)
    pet, f = petg(ctx)
    F = float(p.skeg_fuse_force)
    t, L = g["t"], g["L"]
    lever_root = g["vn"] - g["v_tip"] + (g["v_root"] - g["vn"])
    F_root_wet = p.skeg_sig_break * t * L ** 2 / (6 * lever_root)
    return {
        "F_diseno_N": F, "banda_N": [round(2 * F / 3), round(4 * F / 3)],
        "banda_base": "[VERIFICADO: PENDIENTES_GASPAR §P1.8: rompe entre 200 y 400 N (diseño 300 N)]",
        "seccion_mm": [round(L, 2), t], "brazo_ref_mm": round(p.skeg_neck_lever, 1),
        "brazo_raiz_mm": round(lever_root, 1),
        "F_pred_mojada_raiz_N": round(F_root_wet, 0), "F_pred_seca_raiz_N": round(F_root_wet / f["f_water"], 0),
        "pred_base": "[CALCULADO: σ_rotura = σt,XY·f_water = params.skeg_sig_break; M en la raíz (escalón con la "
                     "lengüeta, 4 mm por encima de skeg_neck_v) con brazo mayor → rompe un poco antes que en la sección "
                     "de referencia]",
        "ensayo": "Lengüeta entre 2 pletinas de acero con los 2 pernos M6 (como en STR-01), bordes de las pletinas a "
                  "ras de la raíz; tirar del agujero con el dinamómetro en el plano de la probeta, perpendicular al "
                  "brazo, despacio (~10 N/s) hasta romper. 3 secas + 3 tras 7 días en agua salada 25 g/L.",
        "pasa_si": "Las mojadas rompen en la cintura entre 200 y 400 N. Si la media F̄ cae fuera: corregir "
                   "skeg_neck_len ← L·√(300/F̄) [CALCULADO: σ ∝ F/L²] vía inputs (skeg_fuse_force/σ) y re-ensayar. "
                   "Las secas son informativas (esperado ≈ F_pred_seca).",
    }
