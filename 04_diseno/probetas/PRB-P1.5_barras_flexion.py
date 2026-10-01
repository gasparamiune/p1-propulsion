"""PRB-P1.5 — Barras de flexión 10×10×100 (PENDIENTES_GASPAR §P1.5).

P1.5A: acostada (capas paralelas al eje → σ de flexión en el plano de capas, como las piezas).
P1.5B: de pie (capas perpendiculares al eje → σ a través de capas: anisotropía Z/XY, f_z).
Flexión en 3 puntos con luz S y carga central con el dinamómetro.
"""
from cadlib import *  # noqa: F401,F403
from _probelib import label, petg

TEST = "P1.5"
B, H, L = 10.0, 10.0, 100.0     # [VERIFICADO: PENDIENTES_GASPAR §P1.5 / tarea: 10×10×100]
SPAN = 80.0                     # luz entre apoyos [SUPUESTO: 10 mm de vuelo a cada lado]


def build(p, ctx):
    xy = box(-L / 2, L / 2, -B / 2, B / 2, 0, H) + label("XY", -L / 2 + 5.0, 0, H, size=4.0, rot=90)
    z = box(-B / 2, B / 2, -H / 2, H / 2, 0, L) + label("Z", 0, 0, L, size=6.0)
    return [
        (dict(id="P1.5A", name="barra_flexion_XY", desc=f"Barra {B:g}×{H:g}×{L:g} acostada (rótulo fuera de la luz)",
              test=TEST, profile="estructural", qty=6, solid_frac=1.0,
              orientation="Acostada: filamentos y capas a lo largo de la barra (σ en el plano de capas)."), xy),
        (dict(id="P1.5B", name="barra_flexion_Z", desc=f"Barra {B:g}×{H:g}×{L:g} de pie (σ a través de capas)",
              test=TEST, profile="estructural", qty=3, solid_frac=1.0,
              orientation="De pie (eje = Z), con brim de 8 mm: la flexión abre las capas."), z),
    ]


def checks(p, ctx, parts):
    a = parts["P1.5A"].bounding_box()
    b = parts["P1.5B"].bounding_box()
    return [("largo barra XY [mm]", a.max.X - a.min.X, L, "="),
            ("alto barra Z (sin rótulo) [mm]", b.max.Z - b.min.Z - 0.6, L, "="),
            ("vuelo sobre cada apoyo ≥ 5 mm [mm]", (L - SPAN) / 2, 5.0, ">=")]


def criterios(p, ctx):
    pet, f = petg(ctx)
    k = 2 * B * H ** 2 / (3 * SPAN)                       # F = σ·2bh²/(3S)
    F_xy = pet["sigma_t_xy_mpa"] * k
    F_z = pet["sigma_t_z_mpa"] * k
    return {
        "luz_mm": SPAN, "formula": "σ_f = 3·F·S/(2·b·h²) [CALCULADO: viga simplemente apoyada, carga central]",
        "F_pred_XY_seca_N": round(F_xy, 0), "F_pred_XY_mojada_N": round(F_xy * f["f_water"], 0),
        "F_pred_Z_seca_N": round(F_z, 0),
        "base_pred": "[ESTIMADO: σ de flexión ≈ σt de inputs.yaml (XY 47, Z 18 MPa, research/R05 S1); en PETG la "
                     "resistencia a flexión suele ser mayor que la de tracción → la predicción es un piso]",
        "ensayo": "3 barras XY secas + 3 XY tras 7 días en agua con 25 g/L de sal (PENDIENTES); 3 barras Z secas. "
                  "Apoyos: 2 pernos Ø10 a 80 mm; carga en el centro con lazo de cable + dinamómetro (balde que se "
                  "llena de agua o palanca). Registrar F máx.",
        "pasa_si": f"σ_mojada / σ_seca ≥ f_water = {f['f_water']} (pérdida ≤ {100 * (1 - f['f_water']):.0f} %); "
                   f"si no, bajar materials.design_factors.f_water. Además σ_Z/σ_XY ≥ f_z = {f['f_z']}; si no, bajar f_z.",
    }
