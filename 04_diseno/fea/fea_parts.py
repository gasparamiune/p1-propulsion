"""fea_parts.py — Modelos FEA de las piezas críticas del waterjet P1-J.

    P1-DRV-03  pórtico de rodamientos (Al 6082 soldado)   empuje Fa (avance / reversa) + radial 3 g
    P1-REV-01  bucket de reversa (Al 5083 4 mm)            chorro en reversa repartido en la cuchara
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
                       moment_of, radial, sel_annulus, sel_cyl, sel_plane)

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


def metal_allow(inp, name, S, fuente):
    """Admisible de un metal dúctil: von Mises contra S (fluencia; ZAT si es soldado)."""
    return {"tipo": "metal", "material": name, "S_short": S, "S_sust": S, "SZ_short": None, "SZ_sust": None,
            "E": E_AL, "nu": NU_AL, "fuente": fuente, "fs_target": inp["materials"]["fs_target_metal"]}


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


def bucket_statics(p, Fb, n=60, share=None):
    """Estática del bucket abajo con el modelo de structural_direccion (fuente única: bucket_reactions): chorro F_b
    en el eje sobre la cuchara + componente vertical tal que M_h = 1,10·F_b·Z_pivote; cada traba toma solo la
    componente tangencial (momento) y cada pivote la mitad del chorro + la reacción de su traba. Devuelve fuerzas
    SOBRE LA BOQUILLA. share = {lado: fracción de M_h} (lado +1 = brazo +Y, −1 = brazo −Y; suma 1); por defecto,
    reparto igual entre las trabas del CAD. {1: 1.0} = toda la traba en +Y (la otra todavía no apoyó)."""
    import _release as RL
    sd = struct_mod("structural_direccion")
    sides = RL.lock_sides(p)
    share = share or {s_: 1.0 / len(sides) for s_ in sides}
    r = sd.bucket_reactions(p, Fb, share)
    v3 = lambda q: np.array([q[0], 0.0, q[1]])                 # noqa: E731  (x, z) → (x, 0, z)
    F, L, R = v3(r["F"]), {k: v3(q) for k, q in r["L"].items()}, {k: v3(q) for k, q in r["R"].items()}
    lp = {k: list(RL.lock_xz(p, k)) for k in (1, -1)}
    return {"F_N": F.tolist(), "x_cp_mm": r["x_cp"], "M_h_Nm": r["Mh"] / 1000, "n_traba": len(sides),
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


def setup_rev01(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0, variant=None):
    """Bucket ABAJO (reversa) con una traba por brazo (REV_n_locks = 2, auditoría ronda 3).

    Cada émbolo es un cuerpo rígido que solo reacciona la componente TANGENCIAL al círculo de la traba
    (momento alrededor del pivote, como structural_direccion) contra la MITAD DE APOYO de su agujero (la
    que avanza hacia el perno bajo la carga; la otra mitad tiene la holgura del agujero Ø12,5). Casos:
      a   R12: las dos trabas apoyan a la vez (agujeros perfectos: reparto nominal);
      b/c R12: la traba −Y (b) o +Y (c) apoya REV_lock_mismatch mm DESPUÉS que la otra (desfase de fabricación
          admitido): hasta cerrar ese juego todo M_h pasa por un solo brazo y la cuchara gira;
      d/e FALLA, reversa de sizing (límite del controlador): el émbolo −Y (d) o +Y (e) no entró → M_h por un
          solo brazo (el émbolo ausente se corre 50 mm: su contacto nunca cierra).
    variant (solo evaluación; NO modifica la pieza): dict(t=espesor mm, trabas=(1,) | (-1,) | (1, -1),
    carga="sizing" → F_b de sizing en vez de REV_F_design, desfase=mm en lugar de REV_lock_mismatch)."""
    import _release as RL
    pid = "P1-REV-01"
    meta = mods[pid].META
    m = mods[pid]
    variant = variant or {}
    if variant.get("t"):
        p = _Override(p, REV_t=float(variant["t"]), REV_bush_L=2 * float(variant["t"]))
    part = m.build_down(p)
    sides = tuple(variant.get("trabas", RL.lock_sides(p)))
    delta = float(variant.get("desfase", p.REV_lock_mismatch))
    sd = struct_mod("structural_direccion")
    A = metal_allow(p.inp, "Al 5083-O/H111 (= ZAT)", sd.AL5083, "structural_direccion.AL5083 [ESTIMADO: EN 485-2]")
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    lks = {s_: RL.lock_xz(p, s_) for s_ in sides}
    yi, t = p.REV_y_in, p.REV_t
    hr = max(0.5 * h, hmin)
    ref = [(Xb, s_ * (yi + t), Zb, 22.0, hr) for s_ in (1, -1)] + [(lks[s_][0], s_ * (yi + t / 2), lks[s_][1], 18.0, hr) for s_ in sides]
    S, M, minfo = _setup_model(part, pid, meta, tmpdir, h, curv, hmin, A, refine=ref)
    names = {1: "embolo", -1: "embolo_menos_y"}
    embs = {s_: M.add_rigid(names[s_], np.array([lks[s_][0], s_ * (yi + t / 2), lks[s_][1]]), fixed_local=(1, 3, 4, 5))
            for s_ in sides}
    M.assemble()
    # pivotes: pernos con hombro Ø10 en bujes POM Ø10/Ø14 (articulación sin fricción)
    r_b = p.REV_bush_od / 2
    piv = sel_cyl(S, (Xb, 0, Zb), (0, 1, 0), r_b)
    k_piv = E_POM / ((p.REV_bush_od - p.REV_pin_d) / 2)
    for s_, nm in ((1, "pivote_mas_y"), (-1, "pivote_menos_y")):     # por lado: reacción de cada pivote (fila a mano)
        M.add_interface(Interface(nm, piv[S.fcent[piv, 1] * s_ > 0], k_piv, axis=((Xb, 0, Zb), (0, 1, 0))))
    M.add_static(S.spring_matrix(piv, 1e-3 * k_piv, mode="dir", direction=(0, 1, 0)))
    # carga: chorro sobre la cara interior de la cuchara, uniforme sobre la proyección del chorro
    R = jet_footprint(p)
    xc0 = p.STE_X_exit + p.REV_cup_dx
    ell = ((S.fcent[:, 0] - xc0) / p.REV_cup_ax) ** 2 + (S.fcent[:, 2] / p.REV_cup_az) ** 2
    cup = np.flatnonzero((np.abs(ell - 1) < 0.04) & (S.fnormal[:, 0] < -0.05) & (np.abs(S.fcent[:, 1]) < yi)
                         & (S.fcent[:, 1] ** 2 + S.fcent[:, 2] ** 2 <= R ** 2) & (S.fcent[:, 0] > p.STE_X_exit))
    if len(cup) < 20:
        raise RuntimeError("REV-01: no se encontró la cara interior de la cuchara")
    A_proj = float((S.farea[cup] * np.abs(S.fnormal[cup, 0])).sum())

    def proj(vec):
        v = np.asarray(vec, float)

        def tf(Xq, n):
            return np.abs(n[:, 0])[:, None, None] * np.broadcast_to(v, Xq.shape)
        return tf
    fX = S.traction_load(cup, proj((1, 0, 0)))
    fZ = S.traction_load(cup, proj((0, 0, 1)))
    fX /= force_of(S, fX)[0]
    fZ /= force_of(S, fZ)[2]
    piv_pt = (Xb, 0.0, Zb)
    MX, MZ = moment_of(S, fX, piv_pt)[1], moment_of(S, fZ, piv_pt)[1]
    sd_loads = est["loads"].get("structural_direccion", {})
    Fbn = p.sz["loads"]["F_bucket_N"]
    Fb = Fbn if variant.get("carga") == "sizing" else p.REV_F_design
    M_tgt = 1.10 * Fb * Zb * np.sign(MX)
    Fz = (M_tgt - Fb * MX) / MZ
    f = Fb * fX + Fz * fZ
    q = Fb / A_proj
    pdyn = p.sz["loads"]["p_nozzle_dyn_Pa"] / 1e6
    # trabas: émbolo Ø12 en el agujero Ø12,5; contacto solo en la mitad de apoyo (la que avanza hacia el perno)
    dirs = {}
    for s_ in sides:
        lq = lks[s_]
        hole = sel_cyl(S, (lq[0], 0, lq[1]), (0, 1, 0), p.REV_lock_hole_d / 2,
                       region=lambda c, lq=lq: np.hypot(c[:, 0] - lq[0], c[:, 2] - lq[1]) < p.REV_lock_hole_d)
        a = math.atan2(lq[1] - Zb, lq[0] - Xb)
        tvec = np.array([math.sin(a), 0.0, -math.cos(a)])          # giro +Y alrededor del pivote → el punto se mueve en +t
        d = np.sign(M_tgt) * tvec                                  # sentido en que el brazo avanza contra el perno
        rvec = np.array([math.cos(a), 0.0, math.sin(a)])
        hs = hole[S.fcent[hole, 1] * s_ > 0]
        rel = S.fcent[hs] - np.array([lq[0], 0.0, lq[1]])
        hs = hs[(rel @ d) < 0.0]                                   # mitad de apoyo: la pared detrás del perno
        M.add_interface(Interface("traba" if s_ > 0 else "traba_menos_y", hs, E_AL / CONTACT_LEN, kind="rigid",
                                  rigid=names[s_], k_t=0.0, axis=((lq[0], 0, lq[1]), (0, 1, 0))))
        M.add_static(dir_stiffness(S.ndof, embs[s_][[0, 1, 2]], tvec, K_LOCK))
        M.add_static(dir_stiffness(S.ndof, embs[s_][[0, 1, 2]], rvec, K_LOCK_WEAK))
        dirs[s_] = d

    def late(s_, dl):
        """Carga extra que corre el émbolo `s_` dl mm en el sentido de avance del brazo: el agujero tiene que
        cerrar ese juego antes de apoyar (desfase de fabricación entre las dos trabas)."""
        fe = np.zeros(S.ndof)
        fe[embs[s_][[0, 1, 2]]] = K_LOCK * dl * dirs[s_]
        return fe

    k_n = Fbn / Fb                                            # reversa de sizing (límite del controlador) / carga del caso
    itf_lock = {s_: next(i for i in M.interfaces if i.name == ("traba" if s_ > 0 else "traba_menos_y")) for s_ in sides}
    z0 = np.zeros(S.ndof)
    cases = [("a", "R12: las dos trabas apoyan a la vez (reparto nominal)", z0, 1.0, None)]
    if len(sides) == 2:
        if delta > 0:
            cases += [("b", f"R12: la traba −Y apoya {delta:g} mm después que la +Y (desfase de fabricación admitido)", late(-1, delta), 1.0, None),
                      ("c", f"R12: la traba +Y apoya {delta:g} mm después que la −Y (desfase de fabricación admitido)", late(1, delta), 1.0, None)]
        if variant.get("carga") != "sizing":
            cases += [("d", "FALLA, reversa de sizing: el émbolo −Y no entró (M_h por el brazo +Y)", z0, k_n, -1),
                      ("e", "FALLA, reversa de sizing: el émbolo +Y no entró (M_h por el brazo −Y)", z0, k_n, 1)]

    def run(log=print, init=None):
        out = []
        for cid, txt, fe, kf, off in cases:
            if off is not None:                               # émbolo que no entró: su contacto no existe en este caso
                itf_lock[off].enabled = False
            try:
                u, info = M.solve(kf * f, extra_f=fe, init_active=(init or {}).get(cid), log=None)
                R_ = M.interface_forces(u)
                act = M_active(M)
            finally:
                if off is not None:
                    itf_lock[off].enabled = True
            Ft = {k: R_[k]["F_abs_N"] for k in R_ if k.startswith("traba")}
            extra = {"F_b_N": Fb * kf, "F_z_N": float(Fz * kf), "M_pivote_Nm": float(kf * moment_of(S, f, piv_pt)[1] / 1000),
                     "A_proyectada_mm2": A_proj, "q_media_MPa": q * kf, "desfase_mm": delta if cid in ("b", "c") else 0.0,
                     "F_traba_N": float(sum(np.linalg.norm(R_[k]["F_N"]) for k in R_ if k.startswith("traba"))),
                     "F_traba_por_lado_N": Ft,
                     "reparto_max_M_h": float(max(Ft.values()) / max(sum(Ft.values()), 1e-9)) if Ft else None,
                     "M_traba_por_lado_Nm": {k: float(np.linalg.norm(R_[k]["F_N"]) * p.REV_lock_r / 1000) for k in R_ if k.startswith("traba")},
                     "F_pivote_por_lado_N": {k: R_[k]["F_abs_N"] for k in R_ if k.startswith("pivote")},
                     "F_pivotes_N": (np.array(R_["pivote_mas_y"]["F_N"]) + np.array(R_["pivote_menos_y"]["F_N"])).round(2).tolist(),
                     "F_traba_mano_N": sd_loads.get("F_lock_pin_N"),
                     "R_pivote_mano_N": sd_loads.get("R_bucket_pivot_design_N" if kf == 1.0 else "R_bucket_pivot_fault_sizing_N"),
                     "embolo_u_mm": {names[s_]: u[embs[s_]][:3].round(4).tolist() for s_ in sides}}
            out.append({"id": cid, "name": "Reversa: chorro F_b = %.0f N en la cuchara; M_h = %.0f N·m; %s"
                        % (Fb * kf, kf * abs(M_tgt) / 1000, txt),
                        "kind": "short", "u": u, "info": info, "extra": extra, "active": act,
                        "disabled": [] if off is None else [itf_lock[off].name]})
        return out

    regions = {"traba": lambda X: np.any([(np.hypot(X[:, 0] - lks[s_][0], X[:, 2] - lks[s_][1]) <= p.REV_lock_hole_d / 2 + 3.0)
                                          & (X[:, 1] * s_ > yi - 0.05) for s_ in sides], axis=0),
               "pivotes": lambda X: np.hypot(X[:, 0] - Xb, X[:, 2] - Zb) <= r_b + 3.0,
               "brazos": lambda X: np.abs(X[:, 1]) >= yi - 0.05,
               "cuchara": lambda X: np.abs(X[:, 1]) < yi - 0.05}
    checks = {"F_b_N": Fb, "F_b_sizing_N": Fbn, "R_chorro_mm": R, "k_pivote_N_mm3": k_piv, "q_chorro_MPa": q,
              "p_dinamica_MPa": pdyn, "estatica": bucket_statics(p, Fb), "trabas": [int(s_) for s_ in sides],
              "desfase_mm": delta,
              "nota": "Cada traba toma solo la componente tangencial (momento alrededor del pivote), como structural_direccion; "
                      "los pivotes toman el resto. Contacto solo en la mitad de apoyo de cada agujero; con desfase, el émbolo "
                      "tardío se corre δ en el sentido de avance del brazo. q = F_b/A_proyectada > p_dinámica: el caso cubre la chapa."}
    two = len(sides) == 2 and delta > 0
    cb = "b" if two else "a"                                   # caso de diseño con el reparto máximo admitido
    comp = comparisons(est, pid, [
        {"key": "Brazo trabado: flexión en su plano con M_h completo (bucket R12", "caso": cb, "region": "brazos",
         "nota": "la fila carga el brazo con M_h completo (cota); el FEA con el desfase admitido"},
        {"key": "Brazo trabado: flexión en su plano con M_h completo (reversa sizing", "caso": cb, "region": "brazos", "escala": Fbn / Fb},
        {"key": "Cuchara como viga", "caso": "a", "region": "cuchara"},
        {"key": "Chapa de la cuchara: franja empotrada", "caso": "a", "region": "cuchara", "escala": pdyn / q,
         "nota": "FEA escalado a p_dinámica / q"},
        {"key": "Chapa de la cuchara: franja (fatiga", "caso": "a", "region": "cuchara", "escala": pdyn / q},
        {"key": "Cuchara abierta a torsión con un solo brazo trabado (FALLA: un émbolo no entró", "caso": "d" if len(sides) == 2 else "a",
         "region": "cuchara", "nota": "falla: un solo brazo trabado con la reversa de sizing"},
        {"key": "Pivote: aplastamiento", "caso": cb, "region": "pivotes", "metrica": "mean",
         "nota": "aplastamiento: presión media R/(d·L); FEA: σvm promedio en el anillo de 3 mm alrededor de los pivotes"},
        {"key": "Agujero de traba", "caso": cb, "region": "traba", "metrica": "mean",
         "nota": "aplastamiento: la fila es presión media F/(d·t) con M_h completo; FEA: σvm promedio en el anillo de 3 mm"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A,
            "regions": regions, "comparacion": comp, "frame_label": "BOQUILLA (bucket abajo)"}


# ===========================================================================
# P1-STE-01 — boquilla direccional (marco de la boquilla, δ = 0)
# ===========================================================================

def setup_ste01(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0, variant=None):
    """variant (solo evaluación): dict(reparto="completo") → reversa con M_h COMPLETO en una traba (falla doble: un
    émbolo no entró + R12 sin límite del controlador; criterio sin fluencia)."""
    pid = "P1-STE-01"
    meta = mods[pid].META
    m = mods[pid]
    part = m.build(p)
    sd = struct_mod("structural_direccion")
    A = metal_allow(p.inp, "Al 6061-T6", sd.AL6061, "structural_direccion.AL6061 [ESTIMADO: EN 755-2]")
    Xp, Lst = p.X_steer_pivot, p.L_steer
    Xb, Zb = p.X_bucket_pivot, p.Z_bucket_pivot
    lx, lz = m.lock_point(p)
    yp = 0.5 * (p.STE_ear_y0 + p.STE_ear_y1)
    zt = p.STE_ear_top
    hr = max(0.5 * h, hmin)
    lx2, lz2 = m.lock_point(p, -1)
    ref = [(Xb, s * yp, Zb, 24.0, hr) for s in (1, -1)] + [(lx, yp, lz, 22.0, hr), (lx2, -yp, lz2, 22.0, hr)] + \
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
    # cargas
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
    # Reversa (auditoría ronda 3): una traba por oreja. Diseño (R12): el reparto máximo admitido entre trabas
    # (REV_lock_share_max, FEA del bucket con el desfase admitido) del lado +Y (c) o −Y (c2). Variante "completo": M_h
    # COMPLETO en una traba (falla doble). En cada pivote: la reacción como apoyo cosenoidal en el
    # agujero Ø(M12 + 0,4) + el momento del espaciador en voladizo (P1-REV-02) como par lineal sobre su anillo de
    # apoyo en la cara exterior de la oreja (la precarga del M12, autoequilibrada, no se modela).
    Fb = p.REV_F_design
    ears = sel_cyl(S, (Xb, 0, Zb), (0, 1, 0), p.REV_bolt_d / 2 + 0.2)
    ear_s = {1: ears[S.fcent[ears, 1] > 0], -1: ears[S.fcent[ears, 1] < 0]}
    lock_s, faces = {}, {}
    for s_ in (1, -1):
        lxs, lzs = m.lock_point(p, s_)
        lk_ = sel_cyl(S, (lxs, 0, lzs), (0, 1, 0), 10.0)
        lock_s[s_] = lk_[S.fcent[lk_, 1] * s_ > 0]
        faces[s_] = sel_annulus(S, (0, s_, 0), p.STE_ear_y1, (Xb, s_ * p.STE_ear_y1, Zb), p.REV_bolt_d / 2 + 0.2, p.REV_pin_d / 2)
        if len(lock_s[s_]) == 0 or len(faces[s_]) == 0:
            raise RuntimeError(f"STE-01: no se encontró la rosca de la traba o la cara del pivote del lado {s_:+d}")
    M.zones += [band_o] + list(ear_s.values()) + list(lock_s.values()) + list(faces.values())
    lev = (p.REV_y_in - p.STE_ear_y1) + p.REV_bush_L / 2 + 0.5 * (p.STE_ear_y1 - p.STE_ear_y0)

    def pin_load(fs_, F):
        F = np.asarray(F, float)
        Fm = np.linalg.norm(F)
        if Fm < 1e-9:
            return np.zeros(S.ndof)
        f = S.traction_load(fs_, cos_bearing(F / Fm))
        return f * (Fm / (force_of(S, f) @ (F / Fm)))

    def face_couple(s_, R_ear):
        """Par del espaciador en voladizo sobre la oreja s_: M = s_·lev·(ŷ × R) respecto del centro C de la cara,
        como tracción normal lineal t = (a·ρ)·n con a = n × M / I (resultante nula, momento M)."""
        R_ear = np.asarray(R_ear, float)
        Mv = s_ * lev * np.cross(np.array([0.0, 1.0, 0.0]), R_ear)
        if np.linalg.norm(Mv) < 1e-9:
            return np.zeros(S.ndof)
        C = np.array([Xb, s_ * p.STE_ear_y1, Zb])
        n_out = np.array([0.0, float(s_), 0.0])
        a = np.cross(n_out, Mv)

        def tf(Xq, n):
            return ((Xq - C) @ a)[..., None] * n_out
        f = S.traction_load(faces[s_], tf)
        Mn = moment_of(S, f, C)
        return f * (Mv @ Mn) / (Mn @ Mn)

    def reverse_load(share):
        st_ = bucket_statics(p, Fb, share=share)
        f = np.zeros(S.ndof)
        for s_, kp, kl in ((1, "F_pivote_mas_y_sobre_boquilla_N", "F_traba_sobre_boquilla_N"),
                           (-1, "F_pivote_menos_y_sobre_boquilla_N", "F_traba_menos_y_sobre_boquilla_N")):
            f += pin_load(ear_s[s_], st_[kp]) + face_couple(s_, st_[kp]) + pin_load(lock_s[s_], st_[kl])
        return f, st_
    full = (variant or {}).get("reparto") == "completo"
    sm = 1.0 if full else p.REV_lock_share_max
    f_c, st = reverse_load({1: sm, -1: 1.0 - sm} if sm < 1.0 else {1: 1.0})
    f_c2, st2 = reverse_load({-1: sm, 1: 1.0 - sm} if sm < 1.0 else {-1: 1.0})
    txt_c = "M_h completo (falla doble)" if full else f"{sm:.0%} de M_h (reparto máx. con el desfase admitido)"

    def run(log=print, init=None):
        res = []
        for cid, name, f in (
                ("a", "Desvío del chorro F_s = máx(sizing %.0f, R12 364) = %.0f N repartido en el paso (centro de presión e = %.0f mm, = structural)" % (Fsn, Fs, e), f_e),
                ("b", "F_s = %.0f N en la boca de salida (últimos 20 mm; brazo ≈ L = %.0f mm, conservador)" % (Fs, Lst), f_o),
                ("c", "Reversa R12 (F_b = %.0f N, M_h = %.0f N·m), %s en la traba +Y: pivotes (+ par del espaciador) y roscas M20" % (Fb, st["M_h_Nm"], txt_c), f_c),
                ("c2", "Reversa R12, %s en la traba −Y: pivotes (+ par del espaciador) y roscas M20" % txt_c, f_c2),
                ("d", "Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa)", f_c + f_e),
                ("d2", "Combinado: reversa (c2) + desvío F_s en el paso (a)", f_c2 + f_e)):
            u, info = M.solve(f, init_active=(init or {}).get(cid), log=None)
            R_ = M.interface_forces(u)
            res.append({"id": cid, "name": name, "kind": "short", "u": u, "info": info, "active": M_active(M),
                        "extra": {"F_N": force_of(S, f).round(1).tolist(),
                                  "M_z_pivote_Nm": float(moment_of(S, f, (Xp, 0.0, 0.0))[2] / 1000),
                                  "reacciones": {k: v["F_N"] for k, v in R_.items()}}})
        return res

    ro = p.STE_ro
    regions = {
        "tubo": lambda X: (np.hypot(X[:, 1], X[:, 2]) <= ro + 0.3) & (X[:, 0] > Xp + 20.0),
        "orejas_bucket": lambda X: (np.abs(X[:, 1]) >= p.STE_ear_y0 - 0.1),
        "orejas_pivote": lambda X: (np.abs(X[:, 2]) >= 38.0) & (np.abs(X[:, 1]) < p.STE_ear_y0 - 0.1),
    }
    checks = {"F_s_N": Fs, "F_s_sizing_N": Fsn, "e_mm": e, "banda_e_mm": [Xp + e - half, Xp + e + half],
              "k_contacto_N_mm3": k_c, "k_arandela_N_mm3": k_w, "estatica_bucket": st, "estatica_bucket_c2": st2,
              "brazo_par_espaciador_mm": lev,
              "nota": "El par de dirección lo reacciona el yugo (brida sobre la torre) como cuerpo rígido con solo el giro "
                      "alrededor del eje de pivote bloqueado: par puro, sin fuerza neta."}
    Fbn = p.sz["loads"]["F_bucket_N"]
    comp = comparisons(est, pid, [
        {"key": "Flexión del tubo", "caso": "a", "region": "tubo", "escala": Fsn / Fs},
        {"key": "Oreja del bucket: flexión en su plano", "caso": "c", "region": "orejas_bucket"},
        {"key": "Oreja del bucket: flexión (reversa sizing", "caso": "c", "region": "orejas_bucket", "escala": Fbn / p.REV_F_design,
         "nota": "FEA con M_h completo en una traba escalado a la reversa de sizing (la fila usa el reparto máx.: FEA conservador)"},
        {"key": "Oreja del bucket: ligamento de la rosca M20", "caso": "c", "region": "orejas_bucket"},
        {"key": "Oreja del bucket: flexión fuera del plano", "caso": "c", "region": "orejas_bucket"},
        {"key": "Oreja de pivote", "caso": "d", "region": "orejas_pivote"},
    ])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "allow": A,
            "regions": regions, "comparacion": comp, "frame_label": "BOQUILLA (δ = 0)"}


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
