"""fea_parts.py — Modelos FEA de P1-MNT-01, P1-MNT-05 (+MNT-06 y tubo rígido) y P1-MNT-04.

Toda la geometría sale de los módulos de pieza (build(p) en su marco natural) y de
params.load(); las posiciones que el módulo de pieza no expone como parámetro (ejes de
tornillos, pernos, tope) se leen del CAD (caras cilíndricas vía OCP). Las cargas se leen de
resultados/estructural.json ("loads") y de inputs.yaml (vía params). Ver README.md (§BCs).
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
DISENO = HERE.parent
ROOT = DISENO.parent
for _p in (str(HERE), str(DISENO), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fea_core as fc  # noqa: E402
from fea_model import (Interface, Model, cad_cylinders, cos_bearing, find_cyl, force_of,  # noqa: E402
                       moment_of, radial, sel_annulus, sel_cyl, sel_plane, uniform_traction)

# ---------------------------------------------------------------------------
# Constantes de modelado (no son entradas de diseño: supuestos del modelo FEA)
# ---------------------------------------------------------------------------
NU_PETG = 0.38          # [ESTIMADO: ν de PETG/copoliésteres amorfos 0,37–0,40 (no hay dato en inputs.yaml)]
E_TRANSOM = 500.0       # [ESTIMADO: madera/contrachapado del espejo ⟂ a la fibra 300–800 MPa]
E_A4 = 193000.0         # [ESTIMADO: AISI 316 / A4, E ≈ 193 GPa]
AS_M12, AS_M6 = 84.3, 20.1   # [ESTIMADO: área resistente ISO 898-1 (M12 84,3; M6 20,1 mm²)]
K_SCREW = 0.2           # [ESTIMADO: igual que structural.py, F = T/(K·d)]
E_POM = 2800.0          # [ESTIMADO: POM-C 2,6–3,0 GPa]
R_WASHER_M16 = 15.0     # [ESTIMADO: arandela ISO 7089 M16 Ø30 bajo la tuerca del perno de dirección]
R_WASHER_M6 = 12.0      # [SUPUESTO: arandela Ø24 de los pasantes M6 de la tapa (structural.py, MNT-05)]
CONTACT_LEN = 1.0       # [SUPUESTO: rigidez de penalización de contacto k = E_PETG/1 mm]
KT_FRAC = 0.01          # [SUPUESTO: rigidez tangencial de estabilización = 1 % de la normal]


def load_project():
    import params
    from build_all import load_parts
    p = params.load()
    mods = {m.META["id"]: m for m in load_parts()}
    with open(ROOT / "resultados" / "estructural.json", encoding="utf-8") as f:
        est = json.load(f)
    return p, mods, est


def print_z_dir(meta):
    """Dirección Z de impresión (perpendicular a capas) en el marco de la pieza."""
    from build123d import Rot
    t = Rot(*meta["print_rot"]).wrapped.Transformation()
    R = np.array([[t.Value(r, c) for c in range(1, 4)] for r in range(1, 4)])
    return R.T @ np.array([0.0, 0.0, 1.0])


def allowables(inp):
    """Admisibles FDM degradados (vigentes en inputs.yaml)."""
    m = inp["materials"]["PETG"]
    f = inp["materials"]["design_factors"]
    k = f["f_water"] * f["f_temp"] * f["f_process"]
    sz_base = min(m["sigma_t_z_mpa"], f["f_z"] * m["sigma_t_xy_mpa"])
    return {"S_short": m["sigma_t_xy_mpa"] * k, "S_sust": m["sigma_t_xy_mpa"] * k * f["f_creep"],
            "SZ_short": sz_base * k, "SZ_sust": sz_base * k * f["f_creep"],
            "factors": dict(f), "sigma_xy": m["sigma_t_xy_mpa"], "sigma_z": m["sigma_t_z_mpa"],
            "sigma_z_base": sz_base, "E": m["E_mpa"], "nu": NU_PETG, "fs_target": inp["materials"]["fs_target_printed"]}


def export_tmp(part, name, tmpdir):
    from build123d import export_step
    path = Path(tmpdir) / f"{name}.step"
    export_step(part, str(path))
    return path


def mesh_part(part, pid, tmpdir, h, curv, hmin=1.0, refine=None):
    step = export_tmp(part, pid, tmpdir)
    stl = DISENO / "stl" / "asm" / f"{pid}.stl"
    X, T, info = fc.mesh_step(step, h, curv_n=curv, hmin=hmin, stl_fallback=stl if stl.exists() else None,
                              refine=refine)
    return X, T, info


def hand_rows(est, part, keys):
    """Filas del cálculo a mano (structural.py) cuyo caso contiene alguna de `keys`."""
    out = []
    for r in est.get("rows", []):
        if r.get("part") == part and any(k.lower() in r.get("load_case", "").lower() for k in keys):
            out.append({"part": part, "load_case": r["load_case"], "sigma_MPa": r.get("sigma_MPa"), "FS": r.get("FS"),
                        "S_MPa": r.get("S_MPa"), "model": r.get("model")})
    return out


# ===========================================================================
# P1-MNT-01 — abrazadera de popa en C
# ===========================================================================

def setup_mnt01(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0):
    meta = mods["P1-MNT-01"].META
    part = mods["P1-MNT-01"].build(p)
    X, T, minfo = mesh_part(part, "P1-MNT-01", tmpdir, h, curv, hmin)
    A = allowables(p.inp)
    S = fc.P2Space(X, T)
    M = Model(S, A["E"], A["nu"], print_z_dir(meta))
    M.assemble()
    cyls = cad_cylinders(part)
    loads = est["loads"]
    mnt = p.inp["mount"]

    # --- tornillos de apriete: ejes desde el CAD, cara de apoyo de la tuerca = fin del agujero ---
    d = p.clamp_screw_d
    r_hole = (d + p.bolt_clr) / 2
    screws = find_cyl(cyls, r_hole, (1, 0, 0))
    if len(screws) != mnt["clamp_screws"]:
        raise RuntimeError(f"MNT-01: se esperaban {mnt['clamp_screws']} agujeros Ø{2*r_hole} en x, hay {len(screws)}")
    try:
        from cadlib import NUT_AF
        r_hex = (NUT_AF[int(d)] + 0.3) / math.sqrt(3) + 0.5
    except Exception:
        r_hex = 0.95 * d
    nut_faces = []
    for pt, ax in screws:
        hole = sel_cyl(S, pt, ax, r_hole)
        x_nut = S.X[S.ftri[hole]][..., 0].max()
        reg = (lambda c, pt=pt, ax=ax: radial(c, pt, ax)[0] < r_hex)
        nf = sel_plane(S, (1, 0, 0), x_nut, tol=0.1, region=reg)
        nut_faces.append({"facets": nf, "axis_point": pt, "x": float(x_nut), "area": float(S.farea[nf].sum())})
    F_scr = mnt["clamp_screw_torque_nm"] / (K_SCREW * d / 1000.0)

    # --- espejo: cara exterior (x=0) y borde superior (z=0) — Winkler unilateral ---
    k_tr = E_TRANSOM / p.tr_t
    c1 = sel_plane(S, (-1, 0, 0), 0.0)
    c2 = sel_plane(S, (0, 0, -1), 0.0, region=lambda c: (c[:, 0] > -p.tr_t) & (c[:, 0] < 0))
    M.add_interface(Interface("espejo_cara_exterior", c1, k_tr, k_t=KT_FRAC * k_tr, zone=False))
    M.add_interface(Interface("espejo_borde_superior", c2, k_tr, k_t=KT_FRAC * k_tr, zone=False))

    f_pre = np.zeros(S.ndof)
    for nf in nut_faces:
        f_pre += S.traction_load(nf["facets"], uniform_traction((-F_scr / nf["area"], 0, 0)))
        M.zones.append(nf["facets"])

    # --- cadena tornillo + zapata + espejo (rigidez axial, para el incremento de impacto) ---
    k_chain = []
    for nf in nut_faces:
        L_free = abs(nf["x"]) - (p.tr_t + p.pad_t)
        k_s = E_A4 * AS_M12 / max(L_free, 5.0)
        A_pad = math.pi * p.pad_d ** 2 / 4
        k_pad = A["E"] * A_pad / p.pad_t
        k_w = E_TRANSOM * A_pad / p.tr_t
        k_chain.append(1.0 / (1 / k_s + 1 / k_pad + 1 / k_w))
    K_chain = [S.spring_matrix(nf["facets"], kc / nf["area"], mode="dir", direction=(1, 0, 0))
               for nf, kc in zip(nut_faces, k_chain)]

    # --- buje de dirección, plato, tuerca del perno ---
    xs = p.swivel_x
    r_bore = (p.swivel_bush_od + p.clr) / 2
    hit = find_cyl(cyls, r_bore, (0, 0, 1), near=(xs, 0, 0), max_dist=1.0)
    if hit:
        r_bore_cad = r_bore
    else:
        raise RuntimeError("MNT-01: no se encontró el agujero del buje de dirección en el CAD")
    bore = sel_cyl(S, (xs, 0, 0), (0, 0, 1), r_bore_cad)
    yb = mods["P1-MNT-03"].build(p).bounding_box()
    foot = (yb.min.X, yb.max.X, yb.min.Y, yb.max.Y)
    z_top = p.shelf_top_z
    boss_ann = sel_annulus(S, (0, 0, -1), -p.boss_bot_z, (xs, 0, p.boss_bot_z), r_bore_cad, R_WASHER_M16)
    H = 0.5 * loads["F_impact_peak_N"]
    z_piv = p.pivot_z

    def impact_loads(sign):
        dvec = np.array([sign, 0.0, 0.0])
        fb = S.traction_load(bore, cos_bearing(dvec))
        fb *= H / (force_of(S, fb) @ dvec)
        Mt = z_piv * H * sign                                   # M_y de H·d aplicada a z_piv
        for side in (sign, -sign):
            reg = (lambda c, side=side: (c[:, 0] >= foot[0]) & (c[:, 0] <= foot[1]) & (c[:, 1] >= foot[2])
                   & (c[:, 1] <= foot[3]) & ((c[:, 0] - xs) * side > 0))
            disc = sel_plane(S, (0, 0, 1), z_top, region=reg)
            fd = S.traction_load(disc, lambda Xq, n, side=side: np.stack(
                [0 * Xq[..., 0], 0 * Xq[..., 0], -np.maximum(0.0, side * (Xq[..., 0] - xs))], axis=-1))
            fn = S.traction_load(boss_ann, uniform_traction((0, 0, 1.0 / S.farea[boss_ann].sum())))
            Fd1 = force_of(S, fd)[2]
            Md1, Mn1 = moment_of(S, fd, (0, 0, 0))[1], moment_of(S, fn, (0, 0, 0))[1]
            Mb = moment_of(S, fb, (0, 0, 0))[1]
            q = (Mt - Mb) / (Md1 - Fd1 * Mn1)
            if q > 0:
                break
        T_pin = -Fd1 * q
        f = fb + q * fd + T_pin * fn
        Fchk, Mchk = force_of(S, f), moment_of(S, f, (0, 0, 0))
        return f, {"H_N": H, "T_perno_N": float(T_pin), "F_plato_N": float(-Fd1 * q),
                   "lado_compresion": "popa (+x)" if side > 0 else "proa (−x)",
                   "check_F_N": Fchk.round(2).tolist(), "check_My_Nmm": float(Mchk[1]), "target_My_Nmm": float(Mt)}, [bore, boss_ann, disc]

    # --- verificación a mano corregida (sección real del puente de la C) ---
    t_br = p.shelf_top_z                                     # el puente ocupa z ∈ [0, shelf_top_z]
    arm = abs(nut_faces[0]["axis_point"][2]) + t_br / 2
    sig_bridge = 2 * F_scr * arm / (p.clamp_w * t_br ** 2 / 6)
    checks = {"F_tornillo_N": F_scr, "ancho_abrazadera_mm": p.clamp_w, "k_cadena_N_mm": [round(k, 0) for k in k_chain], "k_espejo_N_mm3": k_tr,
              "z_tornillos_mm": [float(nf["axis_point"][2]) for nf in nut_faces],
              "y_tornillos_mm": [float(nf["axis_point"][1]) for nf in nut_faces],
              "x_apoyo_tuerca_mm": [nf["x"] for nf in nut_faces],
              "puente_espesor_mm": t_br, "sigma_puente_mano_MPa": sig_bridge,
              "nota_mano": "structural.py usa Z = b·leg_t²/6 (pata); la sección mínima de la C es el puente "
                           f"(t = shelf_top_z = {t_br:.0f} mm) → σ = 2F·brazo/(b·t²/6)"}

    def run(log=print, init=None):
        res = []
        ia = (init or {}).get("a")
        u_a, info = M.solve(f_pre, init_active=ia, log=log)
        res.append({"id": "a", "name": "Apriete sostenido de 2×M%d (%.1f N·m → %.0f N c/u)" % (d, mnt["clamp_screw_torque_nm"], F_scr),
                    "kind": "sust", "u": u_a, "info": info, "extra": {}, "active": M_active(M)})
        for sign, cid in ((+1, "b+"), (-1, "b-")):
            fH, xinfo, zones = impact_loads(sign)
            Kx = K_chain[0]
            for Kc in K_chain[1:]:
                Kx = Kx + Kc
            u_b, info = M.solve(f_pre + fH, extra_K=Kx, extra_f=Kx @ u_a, init_active=(init or {}).get(cid), log=log)
            scr = []
            for nf, Kc in zip(nut_faces, K_chain):
                dF = -(Kc @ (u_b - u_a))
                scr.append(float(F_scr - force_of(S, dF)[0]))
            xinfo["F_tornillos_N"] = scr
            res.append({"id": cid, "name": "Impacto H = 0,5·F_pico = %.0f N %s a la altura del pivote + apriete" % (
                H, "hacia popa (+x)" if sign > 0 else "hacia proa (−x)"), "kind": "short", "u": u_b, "info": info,
                "extra": xinfo, "active": M_active(M), "zones_extra": zones})
        return res

    hand = hand_rows(est, "P1-MNT-01", ["Apriete (sostenido)", "impacto"])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "hand": hand,
            "case_hand_map": {"a": "Apriete (sostenido)", "b+": "impacto", "b-": "impacto"}}


def M_active(M):
    return {itf.name: (M.S.fcent[itf.facets].copy(), itf.active.copy()) for itf in M.interfaces if itf.unilateral}


# ===========================================================================
# P1-MNT-04 — mejilla de horquilla
# ===========================================================================

def setup_mnt04(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0):
    meta = mods["P1-MNT-04"].META
    part = mods["P1-MNT-04"].build(p)
    X, T, minfo = mesh_part(part, "P1-MNT-04", tmpdir, h, curv, hmin)
    A = allowables(p.inp)
    S = fc.P2Space(X, T)
    M = Model(S, A["E"], A["nu"], print_z_dir(meta))
    M.assemble()
    cyls = cad_cylinders(part)
    z0 = p.disc_z0 + p.disc_t
    foot = sel_plane(S, (0, 0, -1), -z0)
    M.fix_facets(foot, zone=True)                       # pie empotrado en la base (MNT-03); banda r_ex excluida del máx. de diseño
    px, pz = p.pivot_x, p.pivot_z
    r_pin = (p.tilt_pin_d + 0.1) / 2
    if not find_cyl(cyls, r_pin, (0, 1, 0), near=(px, 0, pz), max_dist=0.5):
        raise RuntimeError("MNT-04: no se encontró el agujero del perno de basculación")
    bore = sel_cyl(S, (px, 0, pz), (0, 1, 0), r_pin)
    y0 = p.cheek_y - p.cheek_t / 2                      # cara interior (hacia la cuna)
    bb = mods["P1-MNT-10"].build(p).bounding_box()
    r_bush = 0.5 * (bb.max.X - bb.min.X)                # buje POM de la cuna (apoyo lateral)
    ann = sel_annulus(S, (0, -1, 0), -y0, (px, y0, pz), r_pin, r_bush)
    M.zones += [bore, ann]
    H = 0.5 * est["loads"]["F_impact_peak_N"]
    Fx = 0.5 * H
    F_lat = 200.0                                       # [SUPUESTO: golpe lateral, igual que structural.py]

    def fx(sign):
        dvec = np.array([sign, 0.0, 0.0])
        f = S.traction_load(bore, cos_bearing(dvec))
        return f * (Fx / (force_of(S, f) @ dvec))

    def fy(F):
        return S.traction_load(ann, uniform_traction((0, F / S.farea[ann].sum(), 0)))

    def run(log=print, init=None):
        loads = [("a+", "Perno: 0,5·H = %.0f N hacia popa (+x)" % Fx, fx(+1)),
                 ("a-", "Perno: 0,5·H = %.0f N hacia proa (−x)" % Fx, fx(-1)),
                 ("b", "Golpe lateral %.0f N en una mejilla (+y, cuna contra la cara interior)" % F_lat, fy(F_lat)),
                 ("b50", "Golpe lateral repartido %.0f N por mejilla (perno atado; = structural.py)" % (F_lat / 2), fy(F_lat / 2))]
        res, U = [], {}
        for cid, name, f in loads:
            u, info = M.solve(f, log=None)
            U[cid] = u
            res.append({"id": cid, "name": name, "kind": "short", "u": u, "info": info, "extra": {}})
        for s in ("+", "-"):
            res.append({"id": "c" + s, "name": "Combinado oblicuo: a%s + b (superposición lineal)" % s, "kind": "short",
                        "u": U["a" + s] + U["b"], "info": {"superposicion": True}, "extra": {}})
        return res

    hc = pz - z0
    try:
        from cadlib import NUT_AF
        w_slot = NUT_AF[6] + 0.4                         # ranura de tuerca M6 (como en el módulo de la pieza)
    except Exception:
        w_slot = None
    checks = {"ancho_ranura_mm": w_slot, "F_x_por_mejilla_N": Fx, "F_lateral_N": F_lat, "brazo_pivote_pie_mm": hc, "r_buje_mm": r_bush,
              "sigma_mano_x_MPa": Fx * hc / (p.cheek_t * 64.0 ** 2 / 6),
              "sigma_mano_lat200_MPa": F_lat * hc / (64.0 * p.cheek_t ** 2 / 6)}
    hand = hand_rows(est, "P1-MNT-04", ["en el plano", "lateral", "Apoyo del perno"])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "hand": hand,
            "case_hand_map": {"a+": "en el plano", "a-": "en el plano", "b": "lateral", "b50": "lateral",
                              "c+": "en el plano", "c-": "en el plano"}}


# ===========================================================================
# P1-MNT-05 — cuna basculante (+ tapa MNT-06 + tubo rígido + tope de marcha)
# ===========================================================================

def stop_u(p, mods):
    """Coordenada u (marco UNIDAD) del contacto del tornillo de trimado/tope sobre la cara
    inferior de la tapa (v = cradle_vbot). Eje del tornillo leído del CAD de MNT-03."""
    th = math.radians(p.theta)
    base = mods["P1-MNT-03"].build(p)
    x_scr = None
    for c in cad_cylinders(base):
        if abs(abs(c["axis"][2]) - 1) < 1e-6 and abs(c["point"][1]) < 1e-3 and abs(c["point"][0] - p.swivel_x) > 1.0 \
                and c["r"] < 0.6 * p.swivel_pin_d:
            x_scr = c["point"][0]
            break
    if x_scr is None:
        xs, _ = mods["P1-MNT-03"].stop_point(p)
        x_scr = xs
    vb = p.cradle_vbot
    return (x_scr - p.pivot_x) / math.cos(th) - vb * math.tan(th), float(x_scr)


def setup_mnt05(p, mods, est, h, curv, tmpdir, log=print, hmin=1.0):
    meta = mods["P1-MNT-05"].META
    meta_cap = mods["P1-MNT-06"].META
    cradle = mods["P1-MNT-05"].build(p)
    cap = mods["P1-MNT-06"].build(p)
    us0, _ = stop_u(p, mods)
    hr = max(0.5 * h, hmin)            # refinamiento local: pared pivote–tubo y apoyo del tope (h/2)
    ref = [(0.0, 0.0, -0.5 * p.e, 0.5 * p.e + 12.0, hr),
           (us0, 0.0, p.cradle_vbot, 0.5 * float(p.raw.get("stop_pad_d", 16.0)) + 12.0, hr)]
    X1, T1, minfo = mesh_part(cradle, "P1-MNT-05", tmpdir, h, curv, hmin, refine=ref)
    X2, T2, _ = mesh_part(cap, "P1-MNT-06", tmpdir, h, curv, hmin, refine=ref)
    X, T, body = fc.merge_meshes([(X1, T1), (X2, T2)])
    A = allowables(p.inp)
    S = fc.P2Space(X, T, body=body)
    M = Model(S, A["E"], A["nu"], print_z_dir(meta), body_names=("P1-MNT-05", "P1-MNT-06"))
    M.n_print_body = [print_z_dir(meta), print_z_dir(meta_cap)]
    vs = -p.e
    u_ref = 0.5 * (p.u_tube_top + p.cradle_u1)
    xref = np.array([u_ref, 0.0, vs])
    tube = M.add_rigid("tubo", xref, fixed_local=(0, 3))    # sin rigidez axial ni de giro propio
    M.assemble()
    E = A["E"]
    k_c = E / CONTACT_LEN

    # pivote: perno rígido fijo, resortes radiales (articulación sin fricción) + axial débil
    cc = cad_cylinders(cradle)
    piv = [c for c in cc if abs(abs(c["axis"][1]) - 1) < 1e-6 and np.hypot(c["point"][0], c["point"][2]) < 0.5]
    if not piv:
        raise RuntimeError("MNT-05: no se encontró el alojamiento del buje del pivote")
    r_piv = min(c["r"] for c in piv if c["r"] > 0.5 * p.tilt_pin_d)   # buje POM (no el recorte R≈100)
    bore = sel_cyl(S, (0, 0, 0), (0, 1, 0), r_piv, body=0)
    t_bush = r_piv - p.tilt_pin_d / 2
    k_pin = E_POM / t_bush
    M.add_interface(Interface("perno_pivote", bore, k_pin, kind="ground", axis=((0, 0, 0), (0, 1, 0))))
    M.add_static(S.spring_matrix(bore, 1e-3 * k_pin, mode="dir", direction=(0, 1, 0)))

    # asiento del tubo en cuna y tapa ↔ tubo rígido (unilateral)
    r_seat = (p.tube_od + 0.3) / 2
    if not find_cyl(cc, r_seat, (1, 0, 0), near=(0, 0, vs), max_dist=0.5):
        raise RuntimeError("MNT-05: no se encontró el asiento del tubo")
    seat_cr = sel_cyl(S, (0, 0, vs), (1, 0, 0), r_seat, body=0)
    seat_cap = sel_cyl(S, (0, 0, vs), (1, 0, 0), r_seat, body=1)
    ax_t = ((0, 0, vs), (1, 0, 0))
    M.add_interface(Interface("tubo_cuna", seat_cr, k_c, kind="rigid", rigid="tubo", zone=False, axis=ax_t))
    M.add_interface(Interface("tubo_tapa", seat_cap, k_c, kind="rigid", rigid="tubo", zone=False, axis=ax_t))

    # pernos pasantes M6 tapa ↔ cuna (resortes entre promedios de parche)
    capc = cad_cylinders(cap)
    holes = [c for c in capc if abs(abs(c["axis"][2]) - 1) < 1e-6 and c["r"] < 0.5 * p.clamp_bolt_d + 0.4]
    pts = []
    for c in holes:
        q = c["point"][:2]
        if not any(np.linalg.norm(q - z) < 1e-3 for z in pts):
            pts.append(q)
    bolts, Kb = [], None
    for (ub, wb) in pts:
        top = sel_annulus(S, (0, 0, 1), p.cradle_vtop, (ub, wb, p.cradle_vtop), 0.0, R_WASHER_M6, body=0)
        dist = radial(S.fcent, np.array([ub, wb, 0.0]), np.array([0, 0, 1.0]))[0]
        head = np.flatnonzero((S.fnormal[:, 2] < -0.99) & (S.fbody == 1) & (dist < 0.5 * p.clamp_bolt_d + 3.0)
                              & (S.fcent[:, 2] > p.cradle_vbot + 0.5))
        if len(top) == 0 or len(head) == 0:
            raise RuntimeError(f"MNT-05/06: parche de perno vacío en u={ub:.1f}, w={wb:.1f}")
        v_head = float(S.fcent[head, 2].mean())
        kb = E_A4 * AS_M6 / (p.cradle_vtop - v_head)
        vecs = {}
        for i, dvec in enumerate(np.eye(3)):
            a = sp.csr_matrix(S.patch_average(top, dvec) - S.patch_average(head, dvec))
            vecs[i] = a
            kk = kb if i == 2 else 0.1 * kb                 # [SUPUESTO: corte del perno 10 % de la axial]
            Ki = (a.T @ a) * kk
            Kb = Ki if Kb is None else Kb + Ki
        bolts.append({"u": float(ub), "w": float(wb), "k_N_mm": kb, "a_axial": vecs[2]})
        M.zones += [top, head]
    M.add_static(Kb)

    # tope de marcha sobre la cara inferior de la tapa (unilateral, normal = −v)
    us, x_scr = stop_u(p, mods)
    r_pad = 0.5 * float(p.raw.get("stop_pad_d", 16.0))      # [SUPUESTO si falta: tapón Ø16 de structural.py]
    stop = sel_annulus(S, (0, 0, -1), -p.cradle_vbot, (us, 0, p.cradle_vbot), 0.0, r_pad, body=1)
    M.add_interface(Interface("tope_marcha", stop, k_c, kind="ground"))

    # carga: cola trabada — fuerza transversal V (fusible del patín) con momento M_lock en el centro de la cuna
    L = est["loads"]
    V = L["F_skeg_fuse_N"]
    M_lock = L["M_tail_locked_Nm"] * 1000.0
    u_c = p.cradle_u1 / 2                                    # referencia de structural.py
    u_load = u_c + M_lock / V
    F = np.array([0.0, 0.0, -V])                              # −v: empuja la cola contra el tope
    r = np.array([u_load, 0.0, vs]) - xref
    f = np.zeros(S.ndof)
    f[tube] = np.concatenate([F, np.cross(r, F)])
    S_stat = V * u_load / us                                  # estática: Σ M_pivote = 0 con tope ⟂ cara (sin fricción)

    def run(log=print, init=None):
        u, info = M.solve(f, init_active=(init or {}).get("a"), log=log)
        Fb = [float(kb_["k_N_mm"] * (kb_["a_axial"] @ u)[0]) for kb_ in bolts]
        q = u[tube]
        extra = {"V_N": V, "u_carga_mm": u_load, "M_pivote_Nm": V * u_load / 1000, "u_tope_mm": us,
                 "x_tornillo_tope_mm": x_scr, "F_tope_estatica_N": S_stat, "F_pernos_tapa_N": Fb,
                 "tubo_giro_mrad": float(q[4] * 1000), "tubo_desplazamiento_v_mm": float(q[2])}
        return [{"id": "a", "name": "Cola trabada contra el tope de marcha: M = %.0f N·m (V = %.0f N a %.0f mm)" % (
            M_lock / 1000, V, u_load), "kind": "short", "u": u, "info": info, "extra": extra, "active": M_active(M)}]

    r_hand = math.hypot(30.0, p.cradle_vbot)
    checks = {"r_pivote_mm": r_piv, "r_tope_mm": r_pad, "k_perno_N_mm3": k_pin, "k_contacto_N_mm3": k_c, "u_tope_mm": us,
              "brazo_tope_real_mm": us, "brazo_tope_structural_py_mm": r_hand, "F_tope_estatica_N": S_stat,
              "pernos_tapa": [{k: v for k, v in b.items() if k != "a_axial"} for b in bolts],
              "nota_tope": "El tornillo de trimado es vertical (marco bote) y apoya sobre la cara inferior de la "
                           "tapa (inclinada θ): sin fricción la reacción es normal a esa cara (eje v) y su brazo "
                           f"respecto del pivote es u = {us:.0f} mm, no hypot(30, v_bot) = {r_hand:.0f} mm."}
    hand = hand_rows(est, "P1-MNT-05", ["cola trabada", "apoyo del buje del pivote"])
    hand += hand_rows(est, "P1-MNT-05/06", ["Tope de marcha"])
    hand += hand_rows(est, "P1-MNT-06", ["cola trabada"])
    return {"model": M, "run": run, "meta": meta, "mesh": minfo, "checks": checks, "hand": hand,
            "case_hand_map": {"a": "cola trabada"}, "bodies": ["P1-MNT-05", "P1-MNT-06"]}


SETUPS = {"P1-MNT-01": setup_mnt01, "P1-MNT-05": setup_mnt05, "P1-MNT-04": setup_mnt04}
