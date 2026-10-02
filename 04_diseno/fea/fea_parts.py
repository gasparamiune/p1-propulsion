"""fea_parts.py — Modelos FEA de las piezas críticas del waterjet P1-J.

    P1-DRV-03  pórtico de rodamientos (Al 6082 soldado)   empuje Fa (avance / reversa) + radial 3 g
    P1-REV-01  bucket de reversa (Al 5083 8 mm)            chorro en reversa (cantidad de movimiento) con una traba sola
    P1-STE-01  boquilla direccional (Al 6061-T6)           desvío del chorro (F_s) y reacciones del bucket
    P1-INT-02  placa base de la toma (Al 5083 10 mm)       tiro de los espárragos del pórtico; presión de cierre
    P1-CTL-02  caja de palancas (PETG impresa)             mano apoyada 150 N sobre la tapa

Toda la geometría sale de los módulos de pieza (build(p) en su marco natural) y de params.load(); los
ejes de agujeros que el módulo no expone se leen del CAD (caras cilíndricas vía OCP) o de las funciones
del propio módulo. Las cargas se leen en cada corrida de sizing.json (p.sz), de las constantes de
structural_<grupo>.py y de resultados/estructural.json ("loads" por grupo). Ver README.md (§BCs).
"""
from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
DISENO = HERE.parent
ROOT = DISENO.parent
for _p in (str(HERE), str(DISENO), str(DISENO / "piezas"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fea_core as fc  # noqa: E402
from fea_model import (Interface, Model, cad_cylinders, cos_bearing, find_cyl, force_of,  # noqa: E402
                       moment_of, radial, sel_annulus, sel_cyl, sel_plane, uniform_traction)

G = 9.81
# ---------------------------------------------------------------------------
# Constantes de modelado (no son entradas de diseño: supuestos del modelo FEA)
# ---------------------------------------------------------------------------
NU_PETG = 0.38          # [ESTIMADO: ν de PETG/copoliésteres amorfos 0,37–0,40 (no hay dato en inputs.yaml)]
E_AL, NU_AL = 70000.0, 0.33   # [ESTIMADO: aleaciones 5xxx/6xxx, E 69–71 GPa, ν 0,33 (EN 1999-1-1 §3.2.5)]
E_A4 = 193000.0         # [ESTIMADO: AISI 316 / A4, E ≈ 193 GPa]
E_POM = 2800.0          # [ESTIMADO: POM-C 2,6–3,0 GPa]
E_PLY = 500.0           # [ESTIMADO: contrachapado ⟂ a la fibra 300–800 MPa (tapa de la consola)]
CONTACT_LEN = 1.0       # [SUPUESTO: rigidez de penalización de contacto metal-metal k = E/1 mm]
KT_FRAC = 0.01          # [SUPUESTO: rigidez tangencial de estabilización = 1 % de la normal]
R_CLAMP_M8 = 12.0       # [ESTIMADO: cono de compresión VDI 2230 de un M8 en la interfaz zapata/placa (Ø ≈ 3 d)]
R_WASHER_M6 = 6.0       # [ESTIMADO: arandela ISO 7089 M6 Ø12 bajo la tuerca de los bulones del ala]
R_WASHER_M5 = 5.0       # [ESTIMADO: arandela ISO 7089 M5 Ø10 sobre el ala de la caja]
D_PALM = 50.0           # [SUPUESTO: mano apoyada = presión uniforme en un círculo Ø50 (palma)]


def load_project():
    import params
    from build_all import load_parts
    p = params.load()
    mods = {m.META["id"]: m for m in load_parts()}
    with open(ROOT / "resultados" / "estructural.json", encoding="utf-8") as f:
        est = json.load(f)
    return p, mods, est


def struct_mod(name):
    """Módulo structural_<grupo>.py (sus constantes de admisibles son la fuente única)."""
    return importlib.import_module(name)


def print_z_dir(meta):
    """Dirección Z de impresión (perpendicular a capas) en el marco de la pieza."""
    from build123d import Rot
    t = Rot(*meta.get("print_rot", (0, 0, 0))).wrapped.Transformation()
    R = np.array([[t.Value(r, c) for c in range(1, 4)] for r in range(1, 4)])
    return R.T @ np.array([0.0, 0.0, 1.0])


def allowables(inp):
    """Admisibles FDM degradados del PETG (vigentes en inputs.yaml)."""
    m = inp["materials"]["PETG"]
    f = inp["materials"]["design_factors"]
    k = f["f_water"] * f["f_temp"] * f["f_process"]
    sz_base = min(m["sigma_t_z_mpa"], f["f_z"] * m["sigma_t_xy_mpa"])
    return {"tipo": "PETG", "S_short": m["sigma_t_xy_mpa"] * k, "S_sust": m["sigma_t_xy_mpa"] * k * f["f_creep"],
            "SZ_short": sz_base * k, "SZ_sust": sz_base * k * f["f_creep"],
            "factors": dict(f), "sigma_xy": m["sigma_t_xy_mpa"], "sigma_z": m["sigma_t_z_mpa"],
            "sigma_z_base": sz_base, "E": m["E_mpa"], "nu": NU_PETG, "fs_target": inp["materials"]["fs_target_printed"]}


def metal_allow(inp, name, S, fuente, S_fat=None, fuente_fat=None, S_u=None, fuente_u=None):
    """Admisible de un metal dúctil: von Mises contra S (fluencia; ZAT si es soldado). S_fat: admisible de los casos
    de fatiga (kind = "fatiga", reversa de sizing), con el mismo FS objetivo. S_u: resistencia a la tracción para la
    corrección de Goodman de una tensión media (precarga) en los casos de fatiga (fea_model.goodman_fields)."""
    out = {"tipo": "metal", "material": name, "S_short": S, "S_sust": S, "SZ_short": None, "SZ_sust": None,
           "E": E_AL, "nu": NU_AL, "fuente": fuente, "fs_target": inp["materials"]["fs_target_metal"]}
    if S_fat is not None:
        out.update({"S_fat": S_fat, "fuente_fat": fuente_fat})
    if S_u is not None:
        out.update({"S_u": S_u, "fuente_u": fuente_u})
    return out


def export_tmp(part, name, tmpdir):
    from build123d import export_step
    path = Path(tmpdir) / f"{name}.step"
    export_step(part, str(path))
    return path


def mesh_part(part, pid, tmpdir, h, curv, hmin=1.0, refine=None, netgen=True):
    step = export_tmp(part, pid, tmpdir)
    stl = DISENO / "stl" / "asm" / f"{pid}.stl"
    X, T, info = fc.mesh_step(step, h, curv_n=curv, hmin=hmin, stl_fallback=stl if stl.exists() else None,
                              refine=refine, netgen=netgen)
    return X, T, info


def hand_row(est, part, key):
    """Fila del cálculo a mano (resultados/estructural.json) de `part` cuyo caso empieza con `key`."""
    for r in est.get("rows", []):
        if r.get("part") == part and r.get("load_case", "").lower().startswith(key.lower()):
            return {"part": part, "load_case": r["load_case"], "sigma_MPa": r.get("sigma_MPa"), "FS": r.get("FS"),
                    "S_MPa": r.get("S_MPa"), "model": r.get("model")}
    return None


def comparisons(est, part, specs):
    """specs: lista de dict(key, caso, region, escala=1, k_mano=1, S=None, nota='').
    k_mano convierte la σ de la fila a von Mises (p. ej. √3 para una τ); S reemplaza el admisible
    de la fila cuando la fila no es von Mises."""
    out = []
    for s in specs:
        h = hand_row(est, part, s["key"])
        if h is None:
            continue
        rec = dict(h)
        rec.update({"caso": s["caso"], "region": s["region"], "escala_carga": s.get("escala", 1.0),
                    "k_mano_a_vm": s.get("k_mano", 1.0), "S_cmp_MPa": s.get("S", h["S_MPa"]), "nota": s.get("nota", ""),
                    "metrica": s.get("metrica", "max_excl")})
        out.append(rec)
    return out


def M_active(M):
    return {itf.name: (M.S.fcent[itf.facets].copy(), itf.active.copy()) for itf in M.interfaces if itf.unilateral}


def _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A, refine=None):
    X, T, minfo = mesh_part(part, pid, tmpdir, h, curv, hmin, refine=refine)
    S = fc.P2Space(X, T)
    M = Model(S, A["E"], A["nu"], print_z_dir(meta))
    return S, M, minfo


def dir_stiffness(n, dofs, direction, k):
    """Resorte a tierra k·(d·u)² sobre 3 gdl `dofs` (traslación de un cuerpo rígido)."""
    d = np.asarray(direction, float) / np.linalg.norm(direction)
    r = np.repeat(dofs, 3)
    c = np.tile(dofs, 3)
    return sp.csr_matrix((k * np.outer(d, d).ravel(), (r, c)), shape=(n, n))


# ===========================================================================
# P1-DRV-03 — pórtico de rodamientos
# ===========================================================================

def setup_drv03(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0):
    from _drv_geom import x_boat, z_axis
    pid = "P1-DRV-03"
    meta = mods[pid].META
    b3 = mods[pid]
    g = b3.geom(p)
    part = b3.build(p)
    st = struct_mod("structural_tren")
    A = metal_allow(p.inp, "Al 6082-T651 soldado (ZAT)", st.SY_6082_HAZ, "structural_tren.SY_6082_HAZ [ESTIMADO: EN 1999-1-1 ρ_haz ≈ 0,48]")
    S, M, minfo = _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A)
    M.assemble()
    cyls = cad_cylinders(part)
    brg = p.drv_bearing
    al = math.radians(p.alpha)
    ef = np.array([math.cos(al), 0.0, math.sin(al)])            # eje del jet hacia proa (S creciente), marco BOTE

    def axis_pt(Sst):
        return np.array([x_boat(p, Sst), 0.0, z_axis(p, Sst)])

    zb0, zb1 = p.base_top_z, p.base_top_z + p.drv_bracket_base_t
    # --- apoyos: zapatas sobre la placa base. Unión precargada (4 × M8 a T/(K·d)) que no se abre y transmite
    # el corte por fricción + 2 pasadores Ø6 por zapata (escariados en montaje, no están en el CAD; las
    # ranuras abiertas a popa no toman corte en x): resortes bilaterales normal k y tangencial k/2 en toda
    # la cara inferior de las zapatas ---
    pads = sel_plane(S, (0, 0, -1), -zb0)
    k_pl = E_AL / p.base_top_z
    M.add_interface(Interface("zapatas_placa", pads, k_pl, k_t=0.5 * k_pl, unilateral=False, zone=False))
    slots = np.flatnonzero((np.abs(S.fnormal[:, 2]) < 0.2) & (S.fcent[:, 2] < zb1 + 0.1)
                           & (np.min([np.hypot(S.fcent[:, 0] - xh, S.fcent[:, 1] - yh) for xh, yh in p.brg_bracket_holes], axis=0)
                              < p.drv_bracket_hole / 2 + 0.6))
    M.zones.append(slots)                        # arandelas/espárragos: zona de apoyo excluida
    # --- cargas: alojamiento Ø47 ---
    pA, pB = axis_pt(p.drv_S_brgA), axis_pt(g["S_h1"])
    bore = sel_cyl(S, pA, ef, brg["D"] / 2, region=lambda c: ((c - pA) @ ef > -0.2) & ((c - pB) @ ef < 0.2))
    m5 = find_cyl(cyls, b3.M5_TAP / 2, ef)
    if len(m5) != 4:
        raise RuntimeError(f"DRV-03: se esperaban 4 roscas M5 de la tapa, hay {len(m5)}")
    taps = np.concatenate([sel_cyl(S, pt, ax, b3.M5_TAP / 2) for pt, ax in m5])
    shoulder = sel_annulus(S, ef, float(ef @ pA), pA, (p.drv_collar_d + 3.0) / 2 - 0.5, brg["D"] / 2 + 0.5)

    def ring_push(Xq, n):                         # aro exterior: apoya entre Da_max y D (máscara por punto de cuadratura)
        rq = np.linalg.norm((Xq - pA) - ((Xq - pA) @ ef)[..., None] * ef, axis=-1)
        on = ((rq >= brg["Da_max"] / 2) & (rq <= brg["D"] / 2 + 0.3)).astype(float)
        return -on[..., None] * ef
    M.zones += [bore, taps, shoulder]
    tr = est["loads"].get("structural_tren", {})
    Fa = p.sz["mech"]["Fa_max_N"]
    Fr = p.sz["mech"]["Fr_N"]
    m_rot = tr.get("m_rotor_kg", 3.11)
    Fv = 3 * G * m_rot + Fr

    def unit(f, d):
        F1 = force_of(S, f) @ d
        if not F1 > 1e-9:
            raise RuntimeError("DRV-03: carga de selección vacía")
        return f / F1
    dv = np.array([0, 0, -1.0]) - (np.array([0, 0, -1.0]) @ ef) * ef      # vertical, ⟂ al eje
    dv /= np.linalg.norm(dv)
    f_rad = Fv * unit(S.traction_load(bore, cos_bearing(dv)), dv)
    f_fwd = Fa * unit(S.traction_load(taps, lambda Xq, n: np.broadcast_to(ef, Xq.shape).copy()), ef)
    f_rev = Fa * unit(S.traction_load(shoulder, ring_push), -ef)

    def run(log=print, init=None):
        res = []
        for cid, name, f in (("a", "Empuje Fa = %.0f N hacia proa (tapa → 4 × M5) + radial 3 g + Fr = %.0f N" % (Fa, Fv), f_fwd + f_rad),
                             ("b", "Empuje Fa = %.0f N hacia popa (resalte trasero, reversa) + radial %.0f N" % (Fa, Fv), f_rev + f_rad)):
            u, info = M.solve(f, init_active=(init or {}).get(cid), log=None)
            res.append({"id": cid, "name": name, "kind": "short", "u": u, "info": info, "active": M_active(M),
                        "extra": {"F_total_N": force_of(S, f).round(1).tolist()}})
        return res

    r_o = p.drv_hsg_od / 2
    cy0 = p.drv_cheek_y[0]

    def dist_axis(X):
        v = X - pA
        return np.linalg.norm(v - np.outer(v @ ef, ef), axis=1)
    regions = {
        "alojamiento": lambda X: dist_axis(X) <= r_o + 0.5,
        "tablero_y_alma": lambda X: (dist_axis(X) > r_o + 0.5) & (np.abs(X[:, 1]) < cy0 - 0.1) & (X[:, 2] > g["zd0"] - 15.0),
        "mejillas": lambda X: (np.abs(X[:, 1]) >= cy0 - 0.1) & (X[:, 2] > zb1 - 0.5),
        "zapatas": lambda X: X[:, 2] <= zb1 - 0.5,
    }
    h_ax = tr.get("h_axis_over_base_mm")
    checks = {"Fa_N": Fa, "Fr_N": Fr, "m_rotor_kg": m_rot, "F_vertical_N": Fv, "h_eje_sobre_base_mm": h_ax,
              "k_zapata_N_mm3": k_pl, "nota": "Unión zapata/placa precargada (F_pre = T/(K·d) ≫ F_t): resortes bilaterales "
                                               "normal k y tangencial k/2 (fricción + pasadores Ø6 escariados en montaje)."}
    comp = comparisons(est, pid, [
        {"key": "Mejillas", "caso": "a", "region": "mejillas"},
        {"key": "Tablero", "caso": "a", "region": "tablero_y_alma"},
        {"key": "Alojamiento Ø47", "caso": "b", "region": "alojamiento"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A,
            "regions": regions, "comparacion": comp, "frame_label": "BOTE"}


# ===========================================================================
# P1-REV-01 — bucket (posición ABAJO, marco de la boquilla)
# ===========================================================================

def jet_footprint(p):
    """Radio del chorro con cono a la altura del fondo de la cuchara (= structural_direccion, como el check de cobertura)."""
    return struct_mod("structural_direccion").jet_footprint(p)


def jet_moment_signed(p, Fb):
    """Momento (y) del chorro alrededor del pivote del bucket CON SIGNO (convención de moment_of: M_y = Δz·F_x − Δx·F_z),
    con la misma cuenta que structural_direccion.jet_momentum (que devuelve |M_h|). N·mm."""
    jm = struct_mod("structural_direccion").jet_momentum(p, Fb)
    J, (tx, tz), (lx, lz) = jm["J"], jm["t_out"], jm["lip"]
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    return (0.0 - Zb) * J + ((lz - Zb) * (-J * tx) - (lx - Xb) * (-J * tz))


def bucket_statics(p, Fb, share=None):
    """Estática del bucket abajo (fuente única: structural_direccion.bucket_reactions, con F y M_h del balance de
    cantidad de movimiento jet_momentum): cada traba toma solo la componente tangencial (momento) y cada pivote la mitad
    del chorro + la reacción de su traba. Devuelve fuerzas SOBRE LA BOQUILLA. share = {lado: fracción de M_h} (lado +1 =
    brazo +Y, −1 = brazo −Y; suma 1). Por defecto {+1: 1} (criterio de la ronda 4: cada traba sola lleva M_h)."""
    import _release as RL
    sd = struct_mod("structural_direccion")
    share = share or {1: 1.0}
    r = sd.bucket_reactions(p, Fb, share)
    v3 = lambda q: np.array([q[0], 0.0, q[1]])                 # noqa: E731  (x, z) → (x, 0, z)
    F, L, R = v3(r["F"]), {k: v3(q) for k, q in r["L"].items()}, {k: v3(q) for k, q in r["R"].items()}
    lp = {k: list(RL.lock_xz(p, k)) for k in (1, -1)}
    return {"F_N": F.tolist(), "x_cp_mm": r["x_cp"], "M_h_Nm": r["Mh"] / 1000, "M_y_chorro_Nm": jet_moment_signed(p, Fb) / 1000,
            "J_N": r["J"], "t_salida": list(r["t_out"]), "labio_mm": list(r["lip"]), "n_traba": len(RL.lock_sides(p)),
            "reparto_M_h": {("+Y" if k > 0 else "-Y"): v for k, v in share.items()},
            "lock_point": lp[1], "lock_point_menos_y": lp[-1],
            "F_traba_sobre_boquilla_N": (-L[1]).tolist(), "F_traba_menos_y_sobre_boquilla_N": (-L[-1]).tolist(),
            "F_pivote_mas_y_sobre_boquilla_N": (-R[1]).tolist(), "F_pivote_menos_y_sobre_boquilla_N": (-R[-1]).tolist(),
            "y_orejas_mm": 0.5 * (p.STE_ear_y0 + p.STE_ear_y1), "R_chorro_mm": jet_footprint(p)}


class _Override:
    """Vista de params con algunos valores reemplazados (solo para variantes de evaluación)."""

    def __init__(self, base, **over):
        self.__dict__["_b"], self.__dict__["_o"] = base, over

    def __getattr__(self, k):
        o = self.__dict__["_o"]
        return o[k] if k in o else getattr(self.__dict__["_b"], k)


K_LOCK = 1e6            # [SUPUESTO: rigidez del émbolo en la dirección tangencial (cuerpo rígido fijado a la boquilla); ≈ 100 × la del
                        # brazo en el agujero: flecha < 0,003 mm con M_h completo, y el desfase no infla el residuo del CG]
K_LOCK_WEAK = 1.0       # [SUPUESTO: resorte débil (N/mm) en las otras traslaciones del émbolo: evita gdl libres si la traba se abre]
MISMATCH_INFO = 0.10    # [SUPUESTO: desfase entre trabas del caso informativo (b), mm; ya no es criterio de diseño (ronda 4)]
STRIP_W = 10.0          # [SUPUESTO: ancho, medido sobre la cuchara, de la franja junto al labio inferior donde se aplica la
                        # reacción de la salida −J·t_out; la lámina conserva el ancho del chorro (|y| ≤ R_chorro)]
TOL_STATICS_REV = 0.02  # resultante y momento aplicados contra bucket_reactions (pedido de la auditoría ronda 4)
TOL_STATICS_STE = 0.01  # resultante aplicada a la boquilla contra la estática (F1)
# Punto caliente de REV-01 en la ronda 3 (cara exterior del brazo a ~47 mm del pivote, hacia abajo, junto al lóbulo de
# la traba): (ΔX, ΔZ) desde el pivote [CALCULADO: FEA ronda 3, máx. en (353,9; −59,5; 36,7) con el pivote en (341,9; 81,8)]
HOT_REV = (12.0, -45.0)


def _lock_name(s_):
    return "traba" if s_ > 0 else "traba_menos_y"


def setup_rev01(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0, variant=None):
    """Bucket ABAJO (reversa), marco de la boquilla, con una traba por brazo (REV_n_locks = 2) y el criterio de la
    ronda 4: CADA traba sola lleva M_h completo (la segunda es redundancia, no reparto).

    Carga del chorro = structural_direccion.jet_momentum (balance de cantidad de movimiento): entrada J uniforme en +x
    por área proyectada del chorro (Ø del chorro + cono) sobre la cara interior de la cuchara, y reacción de la salida
    −J·t_out como tracción uniforme en una franja de STRIP_W mm junto al labio inferior. El setup verifica que la
    resultante y el momento alrededor del pivote coinciden con bucket_reactions (± TOL_STATICS_REV).
    Pivotes: bujes POM (Winkler unilateral, normal radial exacta, sin fricción). Cada émbolo (perno Ø REV_lock_pin_d en
    el agujero Ø REV_lock_hole_d) es un cuerpo rígido que solo reacciona la componente TANGENCIAL al círculo de la traba
    (el momento), contra la MITAD DE APOYO de su agujero (la que avanza hacia el perno). Casos:
      a    R12, las dos trabas apoyan a la vez, sin desfase (informativo);
      b    R12, la traba −Y apoya MISMATCH_INFO mm después que la +Y (informativo, sin requisito);
      d/e  R12 con SOLO la traba +Y (d) / SOLO la −Y (e): la interfaz de la otra no existe en el caso y su agujero
           sale de las zonas excluidas (DISEÑO, FS ≥ 2 contra fluencia);
      f/g  reversa de sizing con solo la traba +Y / −Y, corrida explícitamente (fatiga de soldadura AL5083_WLCF, FS ≥ 2).
    variant (solo evaluación; NO modifica la pieza): dict(t=espesor de chapa mm, casos=[ids] para correr solo esos)."""
    import _release as RL
    pid = "P1-REV-01"
    meta = mods[pid].META
    m = mods[pid]
    variant = variant or {}
    if variant.get("t"):
        p = _Override(p, REV_t=float(variant["t"]), REV_bush_L=float(variant["t"]) + p.REV_ring_t)
    part = m.build_down(p)
    sides = tuple(RL.lock_sides(p))
    sd = struct_mod("structural_direccion")
    A = metal_allow(p.inp, "Al 5083-O/H111 (= ZAT)", sd.AL5083, "structural_direccion.AL5083 [ESTIMADO: EN 485-2]",
                    S_fat=sd.AL5083_WLCF, fuente_fat="structural_direccion.AL5083_WLCF [CALCULADO: detalle soldado FAT 25, "
                    "m = 3, 1e5 ciclos] (en toda la pieza: conservador lejos de las soldaduras)")
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    lks = {s_: RL.lock_xz(p, s_) for s_ in sides}
    yi, t = p.REV_y_in, p.REV_t
    rt = p.REV_ring_t
    hr = max(0.5 * h, hmin)
    ref = [(Xb, s_ * (yi + (t + rt) / 2), Zb, 24.0, hr) for s_ in (1, -1)] \
        + [(lks[s_][0], s_ * (yi + t / 2), lks[s_][1], 20.0, hr) for s_ in sides] \
        + [(Xb + HOT_REV[0], s_ * (yi + t / 2), Zb + HOT_REV[1], 16.0, hr) for s_ in (1, -1)]
    S, M, minfo = _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A, refine=ref)
    embs = {s_: M.add_rigid("embolo" if s_ > 0 else "embolo_menos_y", np.array([lks[s_][0], s_ * (yi + t / 2), lks[s_][1]]),
                            fixed_local=(1, 3, 4, 5)) for s_ in sides}
    M.assemble()
    # pivotes: muñón Ø REV_pin_d (P1-REV-02) en el buje POM P1-REV-03 (articulación sin fricción)
    r_b = p.REV_bush_od / 2
    piv = sel_cyl(S, (Xb, 0, Zb), (0, 1, 0), r_b)
    k_piv = E_POM / ((p.REV_bush_od - p.REV_pin_d) / 2)
    for s_, nm in ((1, "pivote_mas_y"), (-1, "pivote_menos_y")):     # por lado: reacción de cada pivote (fila a mano)
        M.add_interface(Interface(nm, piv[S.fcent[piv, 1] * s_ > 0], k_piv, axis=((Xb, 0, Zb), (0, 1, 0))))
    M.add_static(S.spring_matrix(piv, 1e-3 * k_piv, mode="dir", direction=(0, 1, 0)))
    # --- carga: cantidad de movimiento del chorro (structural_direccion.jet_momentum) ---
    Fbn = p.sz["loads"]["F_bucket_N"]
    Fb = p.REV_F_design
    jm = sd.jet_momentum(p, Fb)
    J, tout = jm["J"], np.array([jm["t_out"][0], 0.0, jm["t_out"][1]])
    R = jet_footprint(p)
    xc0 = p.STE_X_exit + p.REV_cup_dx
    axc, azc = p.REV_cup_ax, p.REV_cup_az
    ex, ez = (S.fcent[:, 0] - xc0) / axc, S.fcent[:, 2] / azc
    ell = ex ** 2 + ez ** 2
    n_in = -np.c_[ex / axc, np.zeros(len(ex)), ez / azc]
    n_in /= np.linalg.norm(n_in, axis=1, keepdims=True)
    inner = (np.abs(ell - 1) < 0.04) & (np.einsum("ij,ij->i", S.fnormal, n_in) > 0.9) & (np.abs(S.fcent[:, 1]) < yi)
    cup = np.flatnonzero(inner & (S.fnormal[:, 0] < -0.05) & (S.fcent[:, 1] ** 2 + S.fcent[:, 2] ** 2 <= R ** 2)
                         & (S.fcent[:, 0] > p.STE_X_exit))
    t1 = math.radians(p.REV_cup_t1)
    dth = STRIP_W / math.hypot(axc * math.sin(t1), azc * math.cos(t1))
    th = np.arctan2(ez, ex)
    strip = np.flatnonzero(inner & (th >= t1 - 1e-6) & (th <= t1 + dth) & (np.abs(S.fcent[:, 1]) <= R))
    if len(cup) < 20 or len(strip) < 4:
        raise RuntimeError(f"REV-01: selección de la cuchara vacía (entrada {len(cup)}, franja de salida {len(strip)} facetas)")
    A_proj = float((S.farea[cup] * np.abs(S.fnormal[cup, 0])).sum())
    A_strip = float(S.farea[strip].sum())
    f_in = S.traction_load(cup, lambda Xq, n: np.abs(n[:, 0])[:, None, None] * np.broadcast_to((1.0, 0.0, 0.0), Xq.shape))
    f_in *= J / force_of(S, f_in)[0]
    f_out = S.traction_load(strip, uniform_traction(-tout))
    f_out *= J / float(np.linalg.norm(force_of(S, f_out)))
    f = f_in + f_out
    piv_pt = (Xb, 0.0, Zb)
    F_app, M_app = force_of(S, f), float(moment_of(S, f, piv_pt)[1])
    st1 = bucket_statics(p, Fb, {1: 1.0})
    F_ref, M_ref = np.array(st1["F_N"]), st1["M_y_chorro_Nm"] * 1000
    errF = float(np.linalg.norm(F_app - F_ref) / np.linalg.norm(F_ref))
    errM = abs(M_app - M_ref) / abs(M_ref)
    if errF > TOL_STATICS_REV or errM > TOL_STATICS_REV:
        raise RuntimeError(f"REV-01: la carga aplicada no es la de bucket_reactions: F {F_app.round(1)} vs {F_ref.round(1)} "
                           f"({errF:.1%}), M_y {M_app / 1000:.1f} vs {M_ref / 1000:.1f} N·m ({errM:.1%})")
    resultante = {"F_aplicada_N": F_app.round(2).tolist(), "F_estatica_N": F_ref.round(2).tolist(), "err_F_rel": errF,
                  "M_y_aplicado_Nm": M_app / 1000, "M_y_estatica_Nm": M_ref / 1000, "err_M_rel": errM,
                  "tolerancia": TOL_STATICS_REV}
    M.zones += [strip]                                         # franja de salida: tracción concentrada junto al labio
    pdyn = p.sz["loads"]["p_nozzle_dyn_Pa"] / 1e6
    q = J / A_proj
    # --- trabas: perno en el agujero Ø REV_lock_hole_d; contacto solo en la mitad de apoyo (la que avanza hacia el perno)
    sgn = float(np.sign(M_app))                                # el brazo gira en el sentido del momento del chorro
    dirs, itf_lock, holes = {}, {}, {}
    for s_ in sides:
        lq = lks[s_]
        hole = sel_cyl(S, (lq[0], 0, lq[1]), (0, 1, 0), p.REV_lock_hole_d / 2,
                       region=lambda c, lq=lq: np.hypot(c[:, 0] - lq[0], c[:, 2] - lq[1]) < p.REV_lock_hole_d)
        a = math.atan2(lq[1] - Zb, lq[0] - Xb)
        tvec = np.array([math.sin(a), 0.0, -math.cos(a)])          # giro +Y alrededor del pivote → el punto se mueve en +t
        d = sgn * tvec                                             # sentido en que el brazo avanza contra el perno
        rvec = np.array([math.cos(a), 0.0, math.sin(a)])
        hs = hole[S.fcent[hole, 1] * s_ > 0]
        rel = S.fcent[hs] - np.array([lq[0], 0.0, lq[1]])
        hs = hs[(rel @ d) < 0.0]                                   # mitad de apoyo: la pared detrás del perno
        itf_lock[s_] = M.add_interface(Interface(_lock_name(s_), hs, E_AL / CONTACT_LEN, kind="rigid",
                                                 rigid="embolo" if s_ > 0 else "embolo_menos_y", k_t=0.0,
                                                 axis=((lq[0], 0, lq[1]), (0, 1, 0))))
        M.add_static(dir_stiffness(S.ndof, embs[s_][[0, 1, 2]], tvec, K_LOCK))
        M.add_static(dir_stiffness(S.ndof, embs[s_][[0, 1, 2]], rvec, K_LOCK_WEAK))
        dirs[s_] = d
        holes[_lock_name(s_)] = {"c": [lq[0], 0.0, lq[1]], "ax": [0.0, 1.0, 0.0], "r": p.REV_lock_hole_d / 2,
                                 "region": lambda X, s_=s_: (X[:, 1] * s_ >= yi - 0.05) & (X[:, 1] * s_ <= yi + t + 0.05)}
    for s_, nm in ((1, "pivote_mas_y"), (-1, "pivote_menos_y")):
        holes[nm] = {"c": [Xb, 0.0, Zb], "ax": [0.0, 1.0, 0.0], "r": r_b, "region": lambda X, s_=s_: X[:, 1] * s_ > 0}

    def late(s_, dl):
        """Carga extra que corre el émbolo `s_` dl mm en el sentido de avance del brazo: el agujero tiene que
        cerrar ese juego antes de apoyar (desfase de fabricación entre las dos trabas; solo caso informativo)."""
        fe = np.zeros(S.ndof)
        fe[embs[s_][[0, 1, 2]]] = K_LOCK * dl * dirs[s_]
        return fe

    sd_loads = est["loads"].get("structural_direccion", {})
    kz = Fbn / Fb                                              # reversa de sizing / R12 (la carga es lineal en F_b)
    z0 = np.zeros(S.ndof)
    two = len(sides) == 2
    # (id, texto, factor de carga, carga extra, traba deshabilitada, tipo, caso de diseño)
    cases = [("a", "R12: las dos trabas apoyan a la vez, sin desfase (informativo)" if two else "R12: traba +Y",
              1.0, z0, None, "short", not two)]
    if two:
        cases += [("b", f"R12: la traba −Y apoya {MISMATCH_INFO:g} mm después que la +Y (desfase; informativo, sin requisito)",
                   1.0, late(-1, MISMATCH_INFO), None, "short", False),
                  ("d", "R12 con SOLO la traba +Y (la −Y no está): M_h completo por el brazo +Y (DISEÑO)", 1.0, z0, -1, "short", True),
                  ("e", "R12 con SOLO la traba −Y (la +Y no está): M_h completo por el brazo −Y (DISEÑO)", 1.0, z0, 1, "short", True),
                  ("f", "Reversa de sizing con SOLO la traba +Y (fatiga de soldadura)", kz, z0, -1, "fatiga", True),
                  ("g", "Reversa de sizing con SOLO la traba −Y (fatiga de soldadura)", kz, z0, 1, "fatiga", True)]
    if variant.get("casos"):                                   # solo evaluación: subconjunto de casos
        cases = [c_ for c_ in cases if c_[0] in variant["casos"]]

    def run(log=print, init=None):
        out = []
        for cid, txt, kf, fe, off, kind, design in cases:
            if off is not None:                               # émbolo ausente: su contacto no existe en este caso
                itf_lock[off].enabled = False
            try:
                u, info = M.solve(kf * f, extra_f=fe, init_active=(init or {}).get(cid), log=None)
                R_ = M.interface_forces(u)
                act = M_active(M)
            finally:
                if off is not None:
                    itf_lock[off].enabled = True
            on = [s_ for s_ in sides if s_ != off]
            Ftan, Mlk = {}, {}
            for s_ in on:
                Fv = np.array(R_[_lock_name(s_)]["F_N"])
                Ftan[_lock_name(s_)] = float(Fv @ (-dirs[s_]))          # el perno empuja el brazo en −d
                lq = lks[s_]
                Mlk[_lock_name(s_)] = float(((lq[1] - Zb) * Fv[0] - (lq[0] - Xb) * Fv[2]) / 1000)
            Ft = {k: R_[k]["F_abs_N"] for k in R_ if k.startswith("traba")}
            dirh = {_lock_name(s_): (-dirs[s_]).tolist() for s_ in on}
            dirh.update({k: R_[k]["F_N"] for k in ("pivote_mas_y", "pivote_menos_y")})
            extra = {"F_b_N": Fb * kf, "J_N": J * kf, "F_z_N": float(F_app[2] * kf),
                     "M_pivote_Nm": float(kf * M_app / 1000), "M_h_mano_Nm": float(kf * jm["Mh"] / 1000),
                     "resultante": {"factor_carga_sobre_R12": kf, **resultante},
                     "A_proyectada_mm2": A_proj, "q_entrada_MPa": q * kf, "desfase_mm": MISMATCH_INFO if cid == "b" else 0.0,
                     "trabas_activas": [_lock_name(s_) for s_ in on],
                     "F_traba_por_lado_N": Ft, "F_traba_tangencial_N": Ftan, "M_traba_por_lado_Nm": Mlk,
                     "F_traba_M_h_sobre_r_N": float(kf * jm["Mh"] / p.REV_lock_r),
                     "F_traba_mano_N": sd_loads.get("F_lock_pin_N" if kind == "short" else "F_lock_pin_sizing_N"),
                     "F_pivote_por_lado_N": {k: R_[k]["F_abs_N"] for k in R_ if k.startswith("pivote")},
                     "F_pivotes_N": (np.array(R_["pivote_mas_y"]["F_N"]) + np.array(R_["pivote_menos_y"]["F_N"])).round(2).tolist(),
                     "R_pivote_mano_N": sd_loads.get("R_bucket_pivot_design_N" if kind == "short" else "R_bucket_pivot_sizing_N"),
                     "embolo_u_mm": {("embolo" if s_ > 0 else "embolo_menos_y"): u[embs[s_]][:3].round(4).tolist() for s_ in sides}}
            out.append({"id": cid, "name": "Reversa: chorro F_b = %.0f N (J = %.0f N, M_h = %.0f N·m); %s"
                        % (Fb * kf, J * kf, kf * jm["Mh"] / 1000, txt),
                        "kind": kind, "diseno": design, "u": u, "info": info, "extra": extra, "active": act,
                        "disabled": [] if off is None else [itf_lock[off].name], "dir_agujeros": dirh})
        return out

    def ring_lock(X, s_):                                     # anillo de 3 mm alrededor del agujero de traba del brazo s_
        return (np.hypot(X[:, 0] - lks[s_][0], X[:, 2] - lks[s_][1]) <= p.REV_lock_hole_d / 2 + 3.0) & (X[:, 1] * s_ > yi - 0.05)
    regions = {"traba": lambda X: np.any([ring_lock(X, s_) for s_ in sides], axis=0),
               **{_lock_name(s_): (lambda X, s_=s_: ring_lock(X, s_)) for s_ in sides},
               "pivotes": lambda X: np.hypot(X[:, 0] - Xb, X[:, 2] - Zb) <= r_b + 3.0,
               "brazos": lambda X: np.abs(X[:, 1]) >= yi - 0.05,
               "cuchara": lambda X: np.abs(X[:, 1]) < yi - 0.05}
    checks = {"F_b_N": Fb, "F_b_sizing_N": Fbn, "J_N": J, "t_salida": tout.tolist(), "labio_inferior_mm": list(jm["lip"]),
              "M_h_Nm": jm["Mh"] / 1000, "R_chorro_mm": R, "k_pivote_N_mm3": k_piv, "q_entrada_MPa": q,
              "p_dinamica_MPa": pdyn, "A_proyectada_mm2": A_proj, "franja_salida_mm": STRIP_W, "A_franja_mm2": A_strip,
              "resultante_R12": resultante, "estatica_traba_mas_y": st1, "trabas": [int(s_) for s_ in sides],
              "desfase_informativo_mm": MISMATCH_INFO, "refinamiento": [list(map(float, r_)) for r_ in ref],
              "nota": "Carga = cantidad de movimiento del chorro (structural_direccion.jet_momentum): J en +x por área proyectada "
                      "sobre la cuchara + −J·t_out en una franja junto al labio inferior; resultante y momento verificados contra "
                      "bucket_reactions en el setup. Cada traba toma solo la componente tangencial (momento alrededor del pivote); "
                      "los pivotes, el resto. Criterio de la ronda 4: cada traba sola (casos d/e a R12, f/g de sizing en fatiga)."}
    comp = comparisons(est, pid, [
        {"key": "Brazo trabado: flexión en su plano con M_h completo (R12", "caso": "d" if two else "a", "region": "brazos",
         "nota": "la fila: flexión del brazo EN SU PLANO con M_h completo; el FEA (una traba sola) suma la flexión fuera del plano"},
        {"key": "Brazo trabado: flexión en su plano con M_h completo (reversa sizing", "caso": "f" if two else "a", "region": "brazos",
         "nota": "caso de sizing corrido explícitamente (sin escalar)"},
        {"key": "Cuchara como viga", "caso": "a", "region": "cuchara"},
        {"key": "Chapa de la cuchara: franja empotrada", "caso": "a", "region": "cuchara", "escala": pdyn / q,
         "nota": "FEA escalado a p_dinámica / q_entrada (caso sin juego inicial: homogéneo de grado 1, el escalado es exacto)"},
        {"key": "Chapa de la cuchara: franja (fatiga", "caso": "a", "region": "cuchara", "escala": pdyn / q},
        {"key": "Cuchara abierta a torsión con un solo brazo trabado (R12", "caso": "d" if two else "a", "region": "cuchara"},
        {"key": "Cuchara abierta a torsión con un solo brazo trabado (reversa sizing", "caso": "f" if two else "a", "region": "cuchara",
         "nota": "caso de sizing corrido explícitamente (sin escalar)"},
        {"key": "Pivote: aplastamiento", "caso": "d" if two else "a", "region": "pivotes", "metrica": "mean",
         "nota": "aplastamiento: presión media R/(d·L); FEA: σvm promedio en el anillo de 3 mm alrededor de los pivotes"},
        {"key": "Agujero de traba", "caso": "d" if two else "a", "region": _lock_name(1), "metrica": "mean",
         "nota": "aplastamiento: la fila es presión media F/(d·t) con M_h completo; FEA: σvm promedio en el anillo de 3 mm"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A, "holes": holes,
            "regions": regions, "comparacion": comp, "frame_label": "BOQUILLA (bucket abajo)"}


# ===========================================================================
# P1-STE-01 — boquilla direccional (marco de la boquilla, δ = 0)
# ===========================================================================

RM_6061 = 260.0         # [ESTIMADO: EN 755-2, 6061-T6 Rm ≥ 260 MPa (misma norma que structural_direccion.AL6061)]: Goodman


def couple_load(S, facets, n_out, Mv):
    """Par puro Mv (en el plano de las facetas) sobre facetas planas de normal n_out: tracción normal lineal
    t = ((X − C)·a)·n_out, C = centroide (en las mismas cuadraturas) de las facetas → resultante exactamente nula. Se
    combinan las dos direcciones a del plano para que el VECTOR momento sea Mv aunque la corona mallada no tenga los
    momentos de inercia iguales (con una sola dirección el par salía girado, ~1 N·m en la malla gruesa)."""
    Mv = np.asarray(Mv, float)
    if np.linalg.norm(Mv) < 1e-9:
        return np.zeros(S.ndof)
    n_out = np.asarray(n_out, float) / np.linalg.norm(n_out)
    Xq, W, _ = S.facet_quad(np.asarray(facets))
    C = (Xq * W[..., None]).sum(axis=(0, 1)) / W.sum()
    u1 = np.cross(n_out, [1.0, 0.0, 0.0] if abs(n_out[0]) < 0.9 else [0.0, 1.0, 0.0])
    u1 /= np.linalg.norm(u1)
    u2 = np.cross(n_out, u1)
    fs, Ms = [], []
    for a in (u1, u2):
        f = S.traction_load(facets, lambda Xq_, n, a=a: ((Xq_ - C) @ a)[..., None] * n_out)
        fs.append(f)
        Ms.append(moment_of(S, f, C))
    Am = np.array([[Ms[0] @ u1, Ms[1] @ u1], [Ms[0] @ u2, Ms[1] @ u2]])
    al = np.linalg.solve(Am, [Mv @ u1, Mv @ u2])
    return al[0] * fs[0] + al[1] * fs[1]


def linear_bearing(S, facets, F, center, side, ecc, length, tol=1e-5, maxit=20):
    """Apoyo de un perno en voladizo en un agujero de eje y (par de aplastamiento): presión cosenoidal en la dirección
    de la carga con intensidad LINEAL a lo largo del agujero, ℓ(η) = 1 + κ·η (η = side·(y − center_y), hacia afuera
    de la oreja). Donde ℓ < 0 el perno apoya en la pared opuesta: ℓ⁺·cos(d) + ℓ⁻·cos(−d) (solo compresión, sin
    tracción en la pared). La fuerza por unidad de largo es ∝ ℓ, así que la resultante es la de un perno cargado en
    η = κ·L²/12: κ se ajusta (secante) para que la línea de acción quede a `ecc` mm del plano medio hacia afuera (la
    mitad del buje o del brazo; ecc = 0: en el plano medio), y una corrección lateral chica β·(±e) deja la
    resultante EXACTA en el plano ⟂ al eje. Normal radial exacta (sin la componente axial de las facetas planas).
    Devuelve (f, info)."""
    yv = np.array([0.0, 1.0, 0.0])
    F = np.asarray(F, float)
    Fm = float(np.linalg.norm(F))
    if Fm < 1e-9:
        return np.zeros(S.ndof), {}
    d = F / Fm
    e_ = np.cross(yv, d)
    c = np.asarray(center, float)

    def build(kap, dv, signed=False):
        def t(Xq, n):
            nr = n - np.outer(n @ yv, yv)                       # normal radial exacta (sin la componente y de las facetas
            nr /= np.linalg.norm(nr, axis=1, keepdims=True)     # planas inscritas en el cilindro: si no, ℓ la amplifica)
            cn = nr @ dv
            eta = side * (Xq[..., 1] - c[1])
            if signed:                                          # corrección: η·cos(dv) con signo (≈ 1 % de la carga)
                w = eta * np.maximum(0.0, -cn)[:, None]
            else:
                ell = 1.0 + kap * eta
                w = np.maximum(ell, 0.0) * np.maximum(0.0, -cn)[:, None] + np.maximum(-ell, 0.0) * np.maximum(0.0, cn)[:, None]
            return -w[..., None] * nr[:, None, :]
        return S.traction_load(facets, t)

    def ecc_of(f):
        Fd = float(force_of(S, f) @ d)
        return side * float(moment_of(S, f, c) @ e_) / Fd

    tol_e = tol * max(abs(ecc), length)
    k0 = 12.0 * ecc / length ** 2
    k1 = k0 + 0.1 * max(abs(k0), 1.0 / length)
    g0 = ecc_of(build(k0, d)) - ecc
    kap = k0
    if abs(g0) > tol_e:
        for _ in range(maxit):
            g1 = ecc_of(build(k1, d)) - ecc
            kap = k1
            if abs(g1) <= tol_e or abs(g1 - g0) < 1e-15:
                break
            k0, k1, g0 = k1, k1 - g1 * (k1 - k0) / (g1 - g0), g1
    # corrección: la discretización deja una fuerza lateral (e) chica y, por la variación lineal, un momento alrededor de d;
    # se anulan los dos con una carga lateral uniforme y otra lineal con signo (coeficientes ≈ 1 % de α)
    fd, gu, gl = build(kap, d), build(0.0, e_), build(0.0, e_, signed=True)

    def comps(f):
        return [float(force_of(S, f) @ d), float(force_of(S, f) @ e_), float(moment_of(S, f, c) @ d)]
    coef = np.linalg.solve(np.array([comps(fd), comps(gu), comps(gl)]).T, [Fm, 0.0, 0.0])
    f = coef[0] * fd + coef[1] * gu + coef[2] * gl
    return f, {"kappa_1_mm": kap, "ell_extremos": [1.0 - kap * length / 2, 1.0 + kap * length / 2],
               "excentricidad_mm": ecc, "excentricidad_aplicada_mm": ecc_of(f),
               "correccion_lateral_rel": [float(coef[1] / coef[0]), float(coef[2] / coef[0])]}


def _point_in_poly(pt, poly):
    """Punto dentro de un polígono (lista de (u, v)), por paridad de cruces."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def lobe_foot_edges(boss_poly, plate_poly, y, name, step=4.0, r=4.0):
    """Aristas vivas del CAD en el PIE de un lóbulo engrosado de P1-STE-01 (re-auditoría ronda 5, FEA-3): esferas de radio r
    sobre el contorno XZ del lóbulo, en la cara Y = y de la placa de la oreja, solo donde la placa sigue más allá del
    lóbulo (unión reentrante a 90°). El plano pide R1,5 en esos pies; el CAD los modela vivos y el FEA los evalúa con el
    promedio en volumen (fea_run.design_sigma, FEA-R5-01). Devuelve {nombre: {c, r, motivo}}."""
    out = {}
    n = len(boss_poly)
    area = sum(boss_poly[i][0] * boss_poly[(i + 1) % n][1] - boss_poly[(i + 1) % n][0] * boss_poly[i][1] for i in range(n))
    sg = 1.0 if area > 0 else -1.0
    k = 0
    for i in range(n):
        (x1, z1), (x2, z2) = boss_poly[i], boss_poly[(i + 1) % n]
        L = math.hypot(x2 - x1, z2 - z1)
        if L < 1e-9:
            continue
        nx, nz = sg * (z2 - z1) / L, -sg * (x2 - x1) / L          # normal hacia afuera del lóbulo
        m = max(1, int(math.ceil(L / step)))
        for j in range(m):
            t = (j + 0.5) / m
            px, pz = x1 + t * (x2 - x1), z1 + t * (z2 - z1)
            if _point_in_poly((px + nx, pz + nz), plate_poly):
                out[f"{name}_{k}"] = {"c": [px, y, pz], "r": r,
                                      "motivo": "pie de lóbulo engrosado (unión reentrante con la placa de la oreja): R1,5 en "
                                                "el plano, viva en el CAD (re-auditoría ronda 5, FEA-3)"}
                k += 1
    return out


def ste01_sharp_edges(p, m):
    """Aristas vivas declaradas de P1-STE-01: pies de los lóbulos de la traba (hacia afuera en la cara exterior de la
    oreja y hacia adentro en la interior) y del lóbulo del pivote (cara interior), en las dos orejas."""
    from _dir_common import hull, circ
    out = {}
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    for s_ in (1, -1):
        tg = "mas_y" if s_ > 0 else "menos_y"
        plate = m.ear_outline(p, s_)
        out.update(lobe_foot_edges(hull(circ(Xb, Zb, p.STE_ear_r)), plate, s_ * p.STE_ear_y0, f"pie_pivote_{tg}"))
        if s_ > 0 or p.REV_n_locks > 1:
            lx, lz = m.lock_point(p, s_)
            out.update(lobe_foot_edges(hull(circ(lx, lz, p.STE_lock_lobe_r)), plate, s_ * p.STE_ear_y1, f"pie_traba_ext_{tg}"))
            out.update(lobe_foot_edges(hull(m.inner_boss_outline(p, s_)), plate, s_ * p.STE_ear_y0, f"pie_traba_int_{tg}"))
    return out


def setup_ste01(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0, variant=None):
    """Boquilla a δ = 0 (marco de la boquilla). Casos:
      a/b    desvío del chorro F_s en el paso / en la boca de salida;
      c/c2   reversa R12 con M_h COMPLETO en la traba +Y / −Y (criterio de traba única, ronda 4): esa oreja lleva su
             pivote (chorro/2 + traba) y su traba; la otra, solo chorro/2 en su pivote. DISEÑO, FS ≥ 2 contra fluencia;
      d/d2   c/c2 + desvío F_s en el paso (maniobra en reversa);
      f/f2   reversa de sizing con M_h completo en la traba +Y / −Y: fatiga, AL6061_FAT, FS ≥ 2 (corridos, sin escalar).
    Cargas del bucket SOBRE CADA OREJA (bucket_statics = structural_direccion.bucket_reactions), autoequilibradas (F1):
      pivote (P1-REV-02 en dos piezas, ronda 5): el piloto Ø REV_sp_pilot_d h6 del casquillo entra ajustado (Loctite 641) en el Ø H7
              que atraviesa la oreja; el camino DISEÑADO del corte y del momento es el apoyo del piloto en el agujero (par
              de aplastamiento): presión cosenoidal con variación LINEAL a lo largo del agujero (linear_bearing) cuya
              resultante pasa por la mitad del buje, a (REV_y_in − STE_ear_y1) + REV_bush_L/2 de la cara exterior. NO hay
              par en la cara de la brida (la unión apretada no se cuenta: MEC-02); selección restringida a la oreja
              (|y| ≥ STE_ear_y0 − 0,5);
      traba:  el cuerpo AJUSTADO del émbolo (Ø REV_lock_bore_d h6 en el H7 liso de la MISMA oreja, Loctite 641, sin
              rosca ni precarga: ronda 5, R5-N1) apoya igual que el piloto: linear_bearing con la resultante en la mitad
              del brazo del bucket (línea de acción del perno), a (REV_y_in − STE_ear_y1) + REV_t/2 de la cara exterior.
    Los dos agujeros atraviesan los lóbulos ENGROSADOS hacia adentro (STE_piv_t, STE_lock_t; R5-N5): las selecciones,
    los planos medios de los apoyos lineales y los bordes de agujero usan el largo de cada lóbulo.
    La precarga del M12 del pivote (baja: 12 N·m, 3,6–6,7 kN, compresión de la oreja ≈ 10 MPa entre brida y arandela)
    no se modela: la cubren las filas a mano. Los casos de fatiga son ciclos 0 → máx. sin media. El setup verifica que la
    resultante aplicada, su momento alrededor del eje del pivote (M_y) y el vector momento completo coinciden con la
    estática (± TOL_STATICS_STE)."""
    pid = "P1-STE-01"
    meta = mods[pid].META
    m = mods[pid]
    part = m.build(p)
    sd = struct_mod("structural_direccion")
    A = metal_allow(p.inp, "Al 6061-T6", sd.AL6061, "structural_direccion.AL6061 [ESTIMADO: EN 755-2]",
                    S_fat=sd.AL6061_FAT, fuente_fat="structural_direccion.AL6061_FAT [ESTIMADO: 6061-T6 sin muesca, R = −1, ~1e7]",
                    S_u=RM_6061, fuente_u="fea_parts.RM_6061 [ESTIMADO: EN 755-2, Rm ≥ 260]")
    Xp, Lst = p.X_steer_pivot, p.L_steer
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    y0e, y1e = p.STE_ear_y0, p.STE_ear_y1
    # lóbulos engrosados hacia adentro (R5-N5): cara interior y plano medio de cada agujero
    yi_p, yi_l = y1e - p.STE_piv_t, p.STE_lock_y1 - p.STE_lock_t
    ypp, ypl = 0.5 * (yi_p + y1e), 0.5 * (yi_l + p.STE_lock_y1)
    yi_min = min(yi_p, yi_l, y0e)
    lpt = {s_: m.lock_point(p, s_) for s_ in (1, -1)}
    zt = p.STE_ear_top
    hr = max(0.5 * h, hmin)
    ref = [(Xb, s * ypp, Zb, 26.0, hr) for s in (1, -1)] + [(lpt[s][0], s * ypl, lpt[s][1], 24.0, hr) for s in (1, -1)] + \
          [(Xp, 0.0, s * zt, 22.0, hr) for s in (1, -1)]
    S, M, minfo = _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A, refine=ref)
    zr = p.STE_riser_top
    M.add_rigid("yugo", (Xp, 0.0, zr), fixed_local=(5,))      # solo el giro alrededor del eje de pivote
    M.assemble()
    k_c = E_AL / CONTACT_LEN
    # pernos de pivote (rígidos, fijos en las orejas de la bomba): Ø8 H7 de la mejilla + roscas M6
    axp = ((Xp, 0, 0), (0, 0, 1))
    top8 = sel_cyl(S, (Xp, 0, 0), (0, 0, 1), 4.0, region=lambda c: c[:, 2] > p.STE_cheek_z0 - 0.5)
    m6t = sel_cyl(S, (Xp, 0, 0), (0, 0, 1), 2.5, region=lambda c: c[:, 2] > 0)
    m6b = sel_cyl(S, (Xp, 0, 0), (0, 0, 1), 2.5, region=lambda c: c[:, 2] < 0)
    for nm, fs_ in (("perno_sup_mejilla", top8), ("perno_sup_rosca", m6t), ("perno_inf_rosca", m6b)):
        M.add_interface(Interface(nm, fs_, k_c, axis=axp))
    M.add_static(S.spring_matrix(np.concatenate([top8, m6t, m6b]), 1e-4 * k_c, mode="dir", direction=(0, 0, 1)))   # estabilización axial
    # arandelas de empuje POM (eje z) en las caras de las orejas de pivote
    k_w = E_POM / p.STE_wash_t
    ro_w = 0.5 * float(getattr(p, "STE_wash_od", 2 * p.STE_ear_rp))
    w_top = sel_annulus(S, (0, 0, 1), zt, (Xp, 0, zt), 2.5, ro_w)
    w_bot = sel_annulus(S, (0, 0, -1), zt, (Xp, 0, -zt), 2.5, ro_w)
    M.add_interface(Interface("arandela_sup", w_top, k_w, unilateral=False))     # boquilla atrapada entre las dos orejas
    M.add_interface(Interface("arandela_inf", w_bot, k_w, unilateral=False))     # de la bomba (luz axial 0,3 mm: se ignora)
    # yugo: brida rígida sobre la torre (4 roscas M8 + cara superior); reacciona solo el par de dirección
    rb_holes = [sel_cyl(S, (Xp + xx, yy, 0), (0, 0, 1), 3.4, region=lambda c: c[:, 2] > zr - 17) for xx, yy in p.STE_riser_bolts]
    rb = np.concatenate(rb_holes)
    x0r, x1r = p.STE_riser_x
    top_r = sel_plane(S, (0, 0, 1), zr, region=lambda c: (c[:, 0] > Xp + x0r - 0.1) & (c[:, 0] < Xp + x1r + 0.1))
    M.add_interface(Interface("yugo_roscas_M8", rb, k_c, kind="rigid", rigid="yugo", k_t=0.1 * k_c, unilateral=False))
    M.add_interface(Interface("yugo_cara", top_r, k_c, kind="rigid", rigid="yugo", k_t=KT_FRAC * k_c, zone=False))
    # cargas: desvío del chorro
    Fs = p.STE_F_design
    Fsn = p.sz["loads"]["F_steer_side_N"]
    e = p.STE_e_frac * Lst
    rb_ = p.STE_rb
    half = min(e - p.STE_bell_L, Lst - e)
    band_e = sel_cyl(S, (0, 0, 0), (1, 0, 0), rb_, region=lambda c: np.abs(c[:, 0] - (Xp + e)) <= half)
    band_o = sel_cyl(S, (0, 0, 0), (1, 0, 0), rb_, region=lambda c: c[:, 0] >= Xp + Lst - 20.0)
    yv = np.array([0.0, 1.0, 0.0])

    def lat(fs_):
        f = S.traction_load(fs_, cos_bearing(yv))
        return f / (force_of(S, f) @ yv)
    f_e, f_o = Fs * lat(band_e), Fs * lat(band_o)
    # --- reversa: selecciones de cada oreja (F1: solo la oreja, el CAD no tiene agujero pasante de lado a lado) ---
    rp_ = p.REV_sp_pilot_d / 2
    rt_ = p.REV_lock_bore_d / 2
    in_piv = lambda c, s_: c[:, 1] * s_ >= yi_p - 0.5              # noqa: E731
    in_lock = lambda c, s_: c[:, 1] * s_ >= yi_l - 0.5             # noqa: E731
    pil, thr = {}, {}
    # facetas del agujero del piloto FUERA de las orejas (diagnóstico de F1: el agujero no es pasante de lado a lado): solo
    # las que tienen TODOS sus nodos sobre el cilindro (la cara de popa de la torre del yugo queda a ≈ 12 mm del eje y, con
    # malla muy gruesa, sus facetas planas pasaban el filtro de radio y normal)
    _so = sel_cyl(S, (Xb, 0, Zb), (0, 1, 0), rp_, region=lambda c: np.abs(c[:, 1]) < yi_p - 0.5)
    _rv = np.hypot(S.X[S.ftri[_so]][..., 0] - Xb, S.X[S.ftri[_so]][..., 2] - Zb)
    n_out_ear = int(np.sum(np.all(np.abs(_rv - rp_) < 0.15, axis=1)))
    for s_ in (1, -1):
        lxs, lzs = lpt[s_]
        pil[s_] = sel_cyl(S, (Xb, 0, Zb), (0, 1, 0), rp_, region=lambda c, s_=s_: in_piv(c, s_))
        thr[s_] = sel_cyl(S, (lxs, 0, lzs), (0, 1, 0), rt_, region=lambda c, s_=s_: in_lock(c, s_))
        for nm_, sel_ in (("agujero del piloto", pil), ("agujero del cuerpo del émbolo", thr)):
            if len(sel_[s_]) == 0:
                raise RuntimeError(f"STE-01: selección vacía ({nm_}) en la oreja {s_:+d}")
    M.zones += [band_o] + list(pil.values()) + list(thr.values())
    y_bush = p.REV_y_in + p.REV_bush_L / 2                  # |y| de la mitad del buje (línea de acción del pivote)
    y_arm = p.REV_y_in + p.REV_t / 2                        # |y| de la mitad del brazo (línea de acción del perno)
    lev_face = (p.REV_y_in - y1e) + p.REV_bush_L / 2        # cara exterior de la oreja → mitad del buje
    ecc_p = y_bush - ypp                                    # plano medio del agujero del piloto → mitad del buje
    lev_l = y_arm - ypl                                     # mitad del brazo (perno) → plano medio del agujero del cuerpo
    L_pil = {s_: float(np.ptp(S.X[S.ftri[pil[s_]].ravel(), 1])) for s_ in (1, -1)}   # largo del agujero en la malla
    L_thr = {s_: float(np.ptp(S.X[S.ftri[thr[s_]].ravel(), 1])) for s_ in (1, -1)}

    names = {(1, "p"): "pivote_mas_y", (-1, "p"): "pivote_menos_y", (1, "l"): "embolo_mas_y", (-1, "l"): "embolo_menos_y"}

    def reverse_load(Fb_, side):
        st_ = bucket_statics(p, Fb_, share={side: 1.0})
        f = np.zeros(S.ndof)
        dirh, lb = {}, {}
        M_ref = 0.0
        M3_ref = np.zeros(3)
        o = np.array([Xb, 0.0, Zb])
        for s_, kp, kl in ((1, "F_pivote_mas_y_sobre_boquilla_N", "F_traba_sobre_boquilla_N"),
                           (-1, "F_pivote_menos_y_sobre_boquilla_N", "F_traba_menos_y_sobre_boquilla_N")):
            Fp, Fl = np.array(st_[kp]), np.array(st_[kl])
            fp_, lb[names[(s_, "p")]] = linear_bearing(S, pil[s_], Fp, (Xb, s_ * ypp, Zb), s_, ecc_p, L_pil[s_])
            f += fp_
            M3_ref += np.cross(np.array([Xb, s_ * y_bush, Zb]) - o, Fp)
            dirh[names[(s_, "p")]] = Fp.tolist()
            if np.linalg.norm(Fl) > 1e-6:
                lxs, lzs = lpt[s_]
                fl_, lb[names[(s_, "l")]] = linear_bearing(S, thr[s_], Fl, (lxs, s_ * ypl, lzs), s_, lev_l, L_thr[s_])
                f += fl_                                     # cuerpo ajustado: resultante en la mitad del brazo
                dirh[names[(s_, "l")]] = Fl.tolist()
                M_ref += (lzs - Zb) * Fl[0] - (lxs - Xb) * Fl[2]
                M3_ref += np.cross(np.array([lxs, s_ * y_arm, lzs]) - o, Fl)
        F_ref = np.array(st_["F_N"])
        F_app = force_of(S, f)
        M3_app = moment_of(S, f, o)
        M_app = float(M3_app[1])
        errF = float(np.linalg.norm(F_app - F_ref) / np.linalg.norm(F_ref))
        errM = abs(M_app - M_ref) / max(abs(M_ref), 1e-9)
        errM3 = float(np.linalg.norm(M3_app - M3_ref) / max(np.linalg.norm(M3_ref), 1e-9))
        if errF > TOL_STATICS_STE or errM > TOL_STATICS_STE or errM3 > TOL_STATICS_STE:
            raise RuntimeError(f"STE-01: la carga del bucket aplicada no es la estática (lado {side:+d}, F_b {Fb_:.0f} N): "
                               f"F {F_app.round(1)} vs {F_ref.round(1)} ({errF:.2%}), M_y {M_app / 1000:.2f} vs "
                               f"{M_ref / 1000:.2f} N·m ({errM:.2%}), M {(M3_app / 1000).round(2)} vs "
                               f"{(M3_ref / 1000).round(2)} N·m ({errM3:.2%})")
        res_ = {"F_aplicada_N": F_app.round(2).tolist(), "F_estatica_N": F_ref.round(2).tolist(), "err_F_rel": errF,
                "M_y_pivote_aplicado_Nm": M_app / 1000, "M_y_pivote_estatica_Nm": M_ref / 1000, "err_M_rel": errM,
                "M_pivote_aplicado_Nm": (M3_app / 1000).round(3).tolist(), "M_pivote_estatica_Nm": (M3_ref / 1000).round(3).tolist(),
                "err_M3_rel": errM3, "apoyo_lineal": lb, "tolerancia": TOL_STATICS_STE}
        return f, st_, res_, dirh
    Fb, Fbn = p.REV_F_design, p.sz["loads"]["F_bucket_N"]
    rev = {(k, s_): reverse_load(F_, s_) for k, F_ in (("R12", Fb), ("sz", Fbn)) for s_ in (1, -1)}
    Mh = rev[("R12", 1)][1]["M_h_Nm"]
    Mhn = rev[("sz", 1)][1]["M_h_Nm"]
    cases = [
        ("a", "Desvío del chorro F_s = máx(sizing %.0f, R12 364) = %.0f N repartido en el paso (centro de presión e = %.0f mm, = structural)"
         % (Fsn, Fs, e), f_e, None, "short"),
        ("b", "F_s = %.0f N en la boca de salida (últimos 20 mm; brazo ≈ L = %.0f mm, conservador)" % (Fs, Lst), f_o, None, "short"),
        ("c", "Reversa R12 (F_b = %.0f N, M_h = %.0f N·m) con M_h COMPLETO en la traba +Y: pivote +Y (chorro/2 + traba), "
              "pivote −Y (chorro/2) y cuerpo del émbolo +Y (DISEÑO)" % (Fb, Mh), rev[("R12", 1)][0], ("R12", 1), "short"),
        ("c2", "Reversa R12 con M_h COMPLETO en la traba −Y: pivote −Y (chorro/2 + traba), pivote +Y y cuerpo del émbolo −Y (DISEÑO)",
         rev[("R12", -1)][0], ("R12", -1), "short"),
        ("d", "Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa)", rev[("R12", 1)][0] + f_e, ("R12", 1), "short"),
        ("d2", "Combinado: reversa (c2) + desvío F_s en el paso (a)", rev[("R12", -1)][0] + f_e, ("R12", -1), "short"),
        ("f", "Reversa de sizing (F_b = %.0f N, M_h = %.1f N·m) con M_h completo en la traba +Y (fatiga, 0 → máx.)"
         % (Fbn, Mhn), rev[("sz", 1)][0], ("sz", 1), "fatiga"),
        ("f2", "Reversa de sizing con M_h completo en la traba −Y (fatiga, 0 → máx.)",
         rev[("sz", -1)][0], ("sz", -1), "fatiga")]

    def run(log=print, init=None):
        res = []
        for cid, name, f, rk, kind in cases:
            u, info = M.solve(f, init_active=(init or {}).get(cid), log=None)
            R_ = M.interface_forces(u)
            act = M_active(M)
            ex = {"F_N": force_of(S, f).round(1).tolist(), "M_z_pivote_Nm": float(moment_of(S, f, (Xp, 0.0, 0.0))[2] / 1000),
                  "reacciones": {k: v["F_N"] for k, v in R_.items()}}
            rec = {"id": cid, "name": name, "kind": kind, "diseno": True, "u": u, "info": info, "active": act,
                   "extra": ex, "dir_agujeros": rev[rk][3] if rk is not None else {}}
            if rk is not None:
                ex["resultante_bucket"] = rev[rk][2]
            res.append(rec)
        return res

    holes = {}
    for s_ in (1, -1):
        holes[names[(s_, "p")]] = {"c": [Xb, 0.0, Zb], "ax": [0.0, 1.0, 0.0], "r": rp_, "region": lambda X, s_=s_: in_piv(X, s_)}
        holes[names[(s_, "l")]] = {"c": [lpt[s_][0], 0.0, lpt[s_][1]], "ax": [0.0, 1.0, 0.0], "r": rt_,
                                   "region": lambda X, s_=s_: in_lock(X, s_)}
    ro = p.STE_ro
    rlobe = p.STE_lock_lobe_r
    regions = {
        "tubo": lambda X: (np.hypot(X[:, 1], X[:, 2]) <= ro + 0.3) & (X[:, 0] > Xp + 20.0),
        "orejas_bucket": lambda X: (np.abs(X[:, 1]) >= yi_min - 0.1),
        "lobulo_embolo": lambda X: (np.abs(X[:, 1]) >= yi_l - 0.1) & np.any(
            [(X[:, 1] * s_ > 0) & (np.hypot(X[:, 0] - lpt[s_][0], X[:, 2] - lpt[s_][1]) <= rlobe + 0.5) for s_ in (1, -1)], axis=0),
        "anillo_piloto": lambda X: (np.abs(X[:, 1]) >= yi_p - 0.1) & (np.hypot(X[:, 0] - Xb, X[:, 2] - Zb) <= rp_ + 3.0),
        "orejas_pivote": lambda X: (np.abs(X[:, 2]) >= 38.0) & (np.abs(X[:, 1]) < yi_min - 0.1),
    }
    checks = {"F_s_N": Fs, "F_s_sizing_N": Fsn, "e_mm": e, "banda_e_mm": [Xp + e - half, Xp + e + half],
              "k_contacto_N_mm3": k_c, "k_arandela_N_mm3": k_w,
              "estatica_bucket_c": rev[("R12", 1)][1], "estatica_bucket_c2": rev[("R12", -1)][1],
              "resultante_bucket": {f"{k}_{'+Y' if s_ > 0 else '-Y'}": v[2] for (k, s_), v in rev.items()},
              "d_agujero_piloto_mm": 2 * rp_, "largo_agujero_piloto_malla_mm": L_pil,
              "brazo_pivote_desde_cara_exterior_mm": lev_face, "excentricidad_pivote_desde_plano_medio_mm": ecc_p,
              "d_agujero_embolo_mm": 2 * rt_, "largo_agujero_embolo_malla_mm": L_thr,
              "excentricidad_traba_desde_plano_medio_mm": lev_l,
              "facetas_agujero_pivote_fuera_de_las_orejas": n_out_ear,
              "nota": "El par de dirección lo reacciona el yugo (brida sobre la torre) como cuerpo rígido con solo el giro "
                      "alrededor del eje de pivote bloqueado: par puro, sin fuerza neta. Cargas del bucket autoequilibradas por "
                      "oreja: pivote = apoyo del piloto en su agujero H7 con presión lineal a lo largo del agujero (par de "
                      "aplastamiento; resultante en la mitad del buje, sin par en la brida); traba = apoyo del cuerpo ajustado "
                      "del émbolo en su agujero H7, igual (resultante en la mitad del brazo); resultante, M_y y el vector "
                      "momento verificados contra la estática en el setup. Sin precarga en la oreja (cuerpo ajustado)."}
    comp = comparisons(est, pid, [
        {"key": "Flexión del tubo", "caso": "a", "region": "tubo", "escala": Fsn / Fs,
         "nota": "caso sin juego inicial (homogéneo de grado 1): escalar a F_s de sizing es exacto"},
        {"key": "Oreja del bucket: flexión en su plano (R12", "caso": "c", "region": "orejas_bucket"},
        {"key": "Oreja del bucket: flexión (reversa sizing", "caso": "f", "region": "orejas_bucket",
         "nota": "caso de sizing corrido explícitamente (sin escalar)"},
        {"key": "Oreja del bucket: ligamento del agujero", "caso": "c", "region": "lobulo_embolo"},
        {"key": "Oreja del bucket: flexión fuera del plano", "caso": "c", "region": "orejas_bucket"},
        {"key": "Oreja: aplastamiento del piloto", "caso": "c", "region": "anillo_piloto", "metrica": "mean",
         "nota": "la fila: p_máx = R/(d·L)·(1 + 6·a/L) (par de aplastamiento, a al plano medio del agujero); FEA: σvm promedio en el anillo de 3 mm alrededor del piloto"},
        {"key": "Oreja: aplastamiento del cuerpo ajustado", "caso": "c", "region": "lobulo_embolo", "metrica": "mean",
         "nota": "la fila: p = F/(d·L)·(1 + 6·a/L); FEA: σvm promedio en el lóbulo de la traba"},
        {"key": "Oreja de pivote", "caso": "d", "region": "orejas_pivote"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A, "holes": holes,
            "regions": regions, "comparacion": comp, "frame_label": "BOQUILLA (δ = 0)",
            "aristas_vivas": ste01_sharp_edges(p, m)}


# ===========================================================================
# P1-INT-02 — placa base de la toma (marco BOTE)
# ===========================================================================

def setup_int02(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0):
    pid = "P1-INT-02"
    meta = mods[pid].META
    m = mods[pid]
    part = m.build(p)
    Sy = p.raw.get("pmp_mat", {}).get("Al 5083", {}).get("Sy", 125.0)
    A = metal_allow(p.inp, "Al 5083-H111", Sy, "params pmp_mat['Al 5083'].Sy (= structural_toma) [ESTIMADO: EN 485-2]")
    zt = p.base_top_z
    hr = max(0.5 * h, hmin)
    ref = [(x, y, zt / 2, 18.0, hr) for (x, y) in p.brg_bracket_holes]
    S, M, minfo = _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A, refine=ref)
    xf0, xf1 = p.toma_x_lb_aft - p.toma_bf_aft, p.toma_x_j + p.toma_ffw
    duct_ref = np.array([0.5 * (xf0 + xf1), 0.0, zt])
    duct_dofs = M.add_rigid("conducto", duct_ref)
    M.assemble()
    # apoyos: ala sobre el casco (contacto unilateral) + bulones M6 del ala (tuerca + arandela: empotrados)
    k_h = E_AL / p.bottom_t
    rim = sel_plane(S, (0, 0, -1), -p.toma_rim_z0)
    M.add_interface(Interface("ala_casco", rim, k_h, k_t=KT_FRAC * k_h, zone=False, unilateral=False))   # ala apretada por 26 × M6
    hb = m.hull_bolts(p)
    r6 = (p.toma_hull_bolt + p.bolt_clr) / 2
    wash = np.concatenate([sel_annulus(S, (0, 0, 1), zt, (x, y, zt), r6, R_WASHER_M6) for x, y in hb])
    M.fix_facets(wash, zone=True)
    # carga (a): espárragos del pórtico — cono avellanado (tiro) + compresión de la zapata + corte Fa
    tr = est["loads"].get("structural_tren", {})
    Fa = p.sz["mech"]["Fa_max_N"]
    F_pre = p.drv_nut_torque_Nm * 1e3 / (p.drv_nut_K * p.brg_bracket_bolt)
    h_ax = tr.get("h_axis_over_base_mm", 120.0)
    xs = sorted({h_[0] for h_ in p.brg_bracket_holes})
    dx = xs[-1] - xs[0]
    dF = Fa * (h_ax + p.drv_bracket_base_t) / dx / 2              # = structural_tren
    W4 = 3 * G * tr.get("m_rotor_kg", 3.11) / 4
    Phi = 0.25                                                     # [ESTIMADO: VDI 2230, como structural_toma]
    r8 = (8 + p.bolt_clr) / 2
    zc = m.CSK_H
    f_a = np.zeros(S.ndof)
    stud = []
    zv = np.array([0, 0, 1.0])
    for (x, y) in p.brg_bracket_holes:
        dd, _ = radial(S.fcent, np.array([x, y, 0.0]), zv)
        cone = np.flatnonzero((S.fcent[:, 2] < zc + 0.05) & (S.fcent[:, 2] > -0.05) & (dd > r8 - 0.2) & (dd < m.CSK_D / 2 + 0.3)
                              & (S.fnormal[:, 2] < -0.3) & (S.fnormal[:, 2] > -0.95))
        pad = sel_annulus(S, (0, 0, 1), zt, (x, y, zt), r8, R_CLAMP_M8)
        if len(cone) < 6 or len(pad) < 6:
            raise RuntimeError(f"INT-02: selección vacía en el espárrago ({x:.0f}, {y:.0f})")
        sgn = 1.0 if x == xs[0] else -1.0                           # vuelco: popa (x menor) a tracción
        Fb_ = F_pre + Phi * sgn * dF                                 # tiro del espárrago sobre el cono
        Fp_ = F_pre - (1 - Phi) * sgn * dF + W4                      # compresión de la zapata
        fc_ = S.traction_load(cone, lambda Xq, n: -n[:, None, :] * np.ones(Xq.shape[:2])[..., None])
        fc_ *= Fb_ / force_of(S, fc_)[2]
        fp_ = S.traction_load(pad, lambda Xq, n: np.broadcast_to((0.0, 0.0, -1.0), Xq.shape).copy())
        fp_ *= Fp_ / -force_of(S, fp_)[2]
        fs_ = S.traction_load(pad, lambda Xq, n: np.broadcast_to((1.0, 0.0, 0.0), Xq.shape).copy())
        fs_ *= (Fa / 4) / force_of(S, fs_)[0]
        f_a += fc_ + fp_ + fs_
        A_cone = float(S.farea[cone].sum())
        stud.append({"x": x, "y": y, "F_esparrago_N": Fb_, "F_zapata_N": Fp_, "A_cono_mm2": A_cone,
                     "p_cono_MPa": Fb_ / (A_cone * math.sin(math.radians(45)))})
        M.zones += [cone, pad]
    # carga (b): presión de cierre en la abertura + golpe de fondo + tiro de la brida del conducto
    L = p.sz["loads"]
    p_max = L["p_pump_max_Pa"] / 1e6
    p_slam = p.toma_p_slam_Pa / 1e6
    p_des = max(p_max, p_slam)
    W2 = p.W_open / 2
    bottom = np.flatnonzero((S.fnormal[:, 2] < -0.99) & (S.fcent[:, 2] < 0.05))
    opening = np.flatnonzero((np.abs(S.fcent[:, 1]) < W2 + 0.3) & ~((S.fnormal[:, 2] < -0.99) & (S.fcent[:, 2] < 0.05)))
    import importlib.util as iu
    spec = iu.spec_from_file_location("_int01", str(DISENO / "piezas" / "P1-INT-01_conducto.py"))
    mi = iu.module_from_spec(spec)
    spec.loader.exec_module(mi)
    duct = np.concatenate([sel_cyl(S, (x, s * p.toma_bolt_y, 0), (0, 0, 1), m.M6_TAP / 2) for x in mi.bolt_x(p) for s in (1, -1)])
    A_open = p.W_open * p.L_open
    F_duct = p_des * A_open
    f_slam = S.traction_load(bottom, lambda Xq, n: np.broadcast_to((0, 0, p_slam), Xq.shape).copy())
    f_open = S.traction_load(opening, lambda Xq, n: -p_des * n[:, None, :] * np.ones(Xq.shape[:2])[..., None])
    f_duct = S.traction_load(duct, lambda Xq, n: np.broadcast_to((0, 0, 1.0), Xq.shape).copy())
    f_duct *= F_duct / force_of(S, f_duct)[2]
    M.zones += [duct]
    f_b = f_slam + f_open + f_duct
    # variante (b2): conducto P1-INT-01 como rigidizador rígido (cota de máxima rigidez: costados de 150 mm
    # de alto abulonados a la placa). Cuerpo rígido unido a la huella de la brida y a las roscas M6; el tiro
    # p·A_abertura se aplica al conducto. (b) sin conducto es la cota opuesta (placa sola).
    W2b = W2
    flange = sel_plane(S, (0, 0, 1), zt, region=lambda c: (np.abs(c[:, 1]) >= W2b - 0.1) & (np.abs(c[:, 1]) <= p.toma_bf_y + 0.1)
                       & (c[:, 0] >= xf0) & (c[:, 0] <= xf1))
    K_duct = S.rigid_coupling(flange, E_AL / CONTACT_LEN, duct_dofs, duct_ref, k_t=KT_FRAC * E_AL / CONTACT_LEN) + \
        S.rigid_coupling(duct, E_AL / CONTACT_LEN, duct_dofs, duct_ref, k_t=E_AL / CONTACT_LEN,
                         axis=None)
    f_b2 = f_slam + f_open
    f_b2[duct_dofs[2]] += F_duct
    # sin la variante el cuerpo rígido queda suelto: resorte débil a tierra en sus 6 gdl
    K_loose = sp.csr_matrix((np.full(6, 1e-3), (duct_dofs, duct_dofs)), shape=(S.ndof, S.ndof))

    def run(log=print, init=None):
        res = []
        for cid, name, f, Kx in (
                ("a", "Espárragos del pórtico: precarga %.0f N (%.0f N·m, K %.2f) ± vuelco Fa·h/Δx/2 = %.0f N (Φ = %.2f) + corte Fa/4"
                 % (F_pre, p.drv_nut_torque_Nm, p.drv_nut_K, dF, Phi), f_a, K_loose),
                ("b", "Golpe de fondo %.0f kPa + presión de cierre %.0f kPa en la abertura + tiro de la brida del conducto %.0f N "
                 "(placa sola, sin la rigidez del conducto: conservador)" % (p_slam * 1e3, p_des * 1e3, F_duct), f_b, K_loose),
                ("b2", "Ídem (b) con el conducto P1-INT-01 como rigidizador rígido abulonado (cota rígida; = modelo de structural_toma)",
                 f_b2, K_duct)):
            u, info = M.solve(f, extra_K=Kx, init_active=(init or {}).get(cid), log=None)
            R_ = M.interface_forces(u)
            res.append({"id": cid, "name": name, "kind": "short", "u": u, "info": info, "active": M_active(M),
                        "extra": {"F_N": force_of(S, f).round(1).tolist(), "ala_casco_N": R_["ala_casco"]["F_N"],
                                  "ala_casco_activa": R_["ala_casco"]["active_frac"]}})
        return res

    def near_studs(X):
        d = np.min([np.hypot(X[:, 0] - x, X[:, 1] - y) for x, y in p.brg_bracket_holes], axis=0)
        return d <= 20.0
    yb = p.toma_plate_y + p.toma_rim_w / 2
    def cone_layer(X):                           # capa de 1,5 mm bajo la superficie del avellanado
        out = np.zeros(len(X), bool)
        for x, y in p.brg_bracket_holes:
            r = np.hypot(X[:, 0] - x, X[:, 1] - y)
            rc = m.CSK_D / 2 - X[:, 2]                # cono 90°: r = dk/2 − z
            out |= (X[:, 2] <= zc + 0.01) & (r >= rc - 0.01) & (r <= rc + 1.5)
        return out

    def plug(X):                                  # cilindro Ø dk sobre el cono (tapón de arranque), ±1 mm
        out = np.zeros(len(X), bool)
        for x, y in p.brg_bracket_holes:
            r = np.hypot(X[:, 0] - x, X[:, 1] - y)
            out |= (X[:, 2] >= zc - 0.01) & (np.abs(r - m.CSK_D / 2) <= 1.0)
        return out
    regions = {"avellanados_M8": near_studs, "asiento_cono": cone_layer, "tapon_dk": plug,
               "pano_lateral": lambda X: (np.abs(X[:, 1]) > p.toma_bolt_y) & (np.abs(X[:, 1]) < yb) & ~near_studs(X),
               "cuna_y_abertura": lambda X: np.abs(X[:, 1]) <= W2 + 15.0}
    checks = {"F_pre_N": F_pre, "F_pre_structural_toma_N": 7000.0, "dF_vuelco_N": dF, "Phi": Phi, "esparragos": stud,
              "p_cierre_MPa": p_max, "p_golpe_MPa": p_slam, "F_brida_conducto_N": F_duct,
              "nota": "Precarga con el par de montaje del pórtico (structural_tren: T/(K·d)); structural_toma usa 7000 N [ESTIMADO]."}
    sq3 = math.sqrt(3)
    comp = comparisons(est, pid, [
        {"key": "Paño lateral", "caso": "b2", "region": "pano_lateral"},
        {"key": "Paño lateral", "caso": "b", "region": "pano_lateral", "nota": "placa sola (sin conducto)"},
        {"key": "Asiento cónico", "caso": "a", "region": "asiento_cono", "metrica": "mean",
         "escala": (7000.0 + 0.25 * dF) / (F_pre + 0.25 * dF),
         "nota": "aplastamiento: promedio de σvm en la capa de 1,5 mm bajo el cono, escalado a la precarga de la fila (7000 N)"},
        {"key": "Arranque de la cabeza M8", "caso": "a", "region": "tapon_dk", "metrica": "mean", "k_mano": sq3, "S": Sy,
         "escala": (7000.0 + 0.25 * dF) / (F_pre + 0.25 * dF),
         "nota": "τ de la fila × √3 → von Mises; FEA: promedio en el cilindro Ø dk ± 1 mm sobre el cono"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A,
            "regions": regions, "comparacion": comp, "frame_label": "BOTE"}


# ===========================================================================
# P1-CTL-02 — caja de palancas PETG (marco BOTE)
# ===========================================================================

def setup_ctl02(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0, variant=None):
    """variant (solo evaluación; NO modifica la pieza): dict con constantes del módulo a reemplazar durante el
    build (p. ej. {"W_OUT": 4.0} pared real, {"WT": 8.0} tapa)."""
    import _ctl as U
    pid = "P1-CTL-02"
    meta = mods[pid].META
    m = mods[pid]
    saved = {k: getattr(m, k) for k in (variant or {})}
    try:
        for k, v in (variant or {}).items():
            setattr(m, k, v)
        part = m.build(p)
        WT_, W_ = m.WT, m.W_OUT
        bolts = m.bolt_xy()
    finally:
        for k, v in saved.items():
            setattr(m, k, v)
    A = allowables(p.inp)
    ax = np.array(p.CTL_axis, float)
    zb = U.top_local(p) + ax[2]
    ztop = m.ZT + ax[2]
    S, M, minfo = _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A)
    M.assemble()
    k_ply = E_PLY / p.CTL_ply_t
    base = sel_plane(S, (0, 0, -1), -zb)
    M.add_interface(Interface("consola", base, k_ply, k_t=KT_FRAC * k_ply, zone=False))
    screws = []
    for xx, yy in bolts:                          # posiciones del módulo de la pieza (pared engrosada hacia afuera)
        c = ax + np.array([xx, yy, 0.0])
        screws.append(sel_annulus(S, (0, 0, 1), zb + 4.0, (c[0], c[1], zb + 4.0), 2.75, R_WASHER_M5))
    M.fix_facets(np.concatenate(screws), zone=True)
    F = 150.0                                     # [SUPUESTO: structural_direccion, mano apoyada]
    top = sel_plane(S, (0, 0, 1), ztop)
    # centros de la palma (marco local U): (a) sobre el nervio entre las dos ranuras, a mitad de su luz libre;
    # (b) sobre el tramo de tapa más ancho sin ranura (lado −y, junto a la ranura del bucket)
    centers = {"a": (-10.0, 0.0), "b": (-62.0, -12.0)}
    loads = {}
    for cid, (cx, cy) in centers.items():
        c = ax + np.array([cx, cy, 0.0])
        sel = top[np.hypot(S.fcent[top, 0] - c[0], S.fcent[top, 1] - c[1]) <= D_PALM / 2]
        f = S.traction_load(sel, lambda Xq, n: np.broadcast_to((0, 0, -1.0), Xq.shape).copy())
        f *= F / -force_of(S, f)[2]
        loads[cid] = (f, sel, (cx, cy), float(S.farea[sel].sum()))

    def run(log=print, init=None):
        res = []
        for cid, (f, sel, (cx, cy), Ap) in loads.items():
            u, info = M.solve(f, init_active=(init or {}).get(cid), log=None)
            nm = "Mano apoyada %.0f N, palma Ø%.0f en (x, y)_U = (%.0f, %.0f) mm (%s); A cargada %.0f mm²" % (
                F, D_PALM, cx, cy, "nervio entre ranuras" if cid == "a" else "tapa ancha junto a la ranura del bucket", Ap)
            res.append({"id": cid, "name": nm, "kind": "short", "u": u, "info": info, "active": M_active(M),
                        "extra": {"A_cargada_mm2": Ap, "p_media_MPa": F / Ap}})   # presión repartida: no se excluye
        return res

    zl = lambda X: X[:, 2] - ax[2]              # noqa: E731
    regions = {"tapa": lambda X: zl(X) >= m.ZT - WT_ - 0.05,
               "paredes": lambda X: (zl(X) < m.ZT - WT_ - 0.05) & (zl(X) > U.top_local(p) + 4.05),
               "ala": lambda X: zl(X) <= U.top_local(p) + 4.05}
    checks = {"F_mano_N": F, "D_palma_mm": D_PALM, "k_consola_N_mm3": k_ply, "solid_frac": meta.get("solid_frac"),
              "pared_mm": W_, "tapa_mm": WT_,
              "nota": "Material macizo isotrópico equivalente; la pieza real es 5 perímetros + 30 % giroide (solid_frac 0,55)."}
    comp = comparisons(est, pid, [
        {"key": "Tapa PETG 6 mm", "caso": "a", "region": "tapa"},
        {"key": "Tapa PETG 6 mm", "caso": "b", "region": "tapa"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A,
            "regions": regions, "comparacion": comp, "frame_label": "BOTE"}


SETUPS = {"P1-DRV-03": setup_drv03, "P1-REV-01": setup_rev01, "P1-STE-01": setup_ste01,
          "P1-INT-02": setup_int02, "P1-CTL-02": setup_ctl02}
