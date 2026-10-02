#!/usr/bin/env python3
"""fea_run.py — FEA lineal elástico de las piezas críticas del waterjet P1-J.

    P1-DRV-03  pórtico de rodamientos (Al 6082 soldado)   (a) Fa a proa + radial · (b) Fa a popa + radial
    P1-REV-01  bucket de reversa (Al 5083 8 mm)            (a) reversa R12 con las dos trabas (informativo) · (b) con desfase
                                                            entre trabas (informativo) · (d/e) R12 con UNA traba sola, +Y/−Y
                                                            (diseño) · (f/g) ídem con la reversa de sizing (fatiga)
    P1-STE-01  boquilla direccional (Al 6061-T6)           (a) F_s en el paso · (b) F_s en la salida · (c/c2) reversa R12
                                                            con M_h completo en la traba +Y/−Y · (d/d2) c + a ·
                                                            (f/f2) reversa de sizing con M_h completo (fatiga)
    P1-INT-02  placa base de la toma (Al 5083 10 mm)       (a) espárragos del pórtico · (b) golpe + presión de cierre
    P1-CTL-02  caja de palancas (PETG)                     (a)/(b) mano apoyada 150 N en dos posiciones

Geometría: build(p) de cada módulo de pieza → STEP temporal → gmsh (tetraedros) → P2 (fea_core).
Cargas: sizing.json + structural_<grupo>.py + resultados/estructural.json. Malla gruesa y fina
(estudio de convergencia; extrapolación tipo Richardson si el máx* cambia > 10 %) y verificación del borde de los
agujeros cargados por perno a ±90° de la carga (sección neta, «lug»). Salidas: 04_diseno/fea/resultados_fea.json, img/*.png y el bloque AUTO
de 04_diseno/fea/README.md.

Uso:  python 04_diseno/fea/fea_run.py [--only P1-STE-01 ...] [--quick] [--serial] [--no-img] [--out RUTA]
      --quick  solo malla gruesa, sin imágenes ni README (prueba rápida)
"""
from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse  # noqa: E402
import datetime  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from multiprocessing import get_context  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (str(HERE), str(HERE.parent), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Tamaños de malla (mm): (gruesa, fina); curvatura = elementos por 2π en agujeros/redondeos.
CFG = {
    "P1-DRV-03": {"h": (10.0, 5.0), "curv": (8, 14), "hmin": 1.5},
    # ronda 4: criterio de traba única → los casos de una traba sola son de diseño (ya no hay variantes de falla doble)
    "P1-REV-01": {"h": (6.0, 3.5), "curv": (8, 14), "hmin": 1.5},
    "P1-STE-01": {"h": (8.0, 4.5), "curv": (8, 14), "hmin": 1.2},
    "P1-INT-02": {"h": (14.0, 8.0), "curv": (6, 10), "hmin": 2.0},
    "P1-CTL-02": {"h": (6.0, 3.0), "curv": (8, 14), "hmin": 1.0,
                  "variantes": {"V1": {"desc": "sensibilidad: paredes de 4 mm (hoy W_OUT = 5)", "param": {"W_OUT": 4.0},
                                       "objetivo": 3.0}}},     # objetivo por variante (= fs_target_printed)
}
ORDER = ["P1-DRV-03", "P1-REV-01", "P1-STE-01", "P1-INT-02", "P1-CTL-02"]
VIEWS = {"P1-DRV-03": ((25, -60), (25, 120)), "P1-REV-01": ((20, -130), (25, 50)),
         "P1-STE-01": ((25, -60), (20, 130)), "P1-INT-02": ((55, -70), (-40, -70)),
         "P1-CTL-02": ((40, -60), (-35, 120))}   # (elevación, azimut)
R_EX_MIN = 4.0          # [SUPUESTO: radio de exclusión alrededor de cargas/apoyos concentrados ≥ 4 mm y ≥ h_fina]


def _j(o):
    """numpy → tipos JSON."""
    if isinstance(o, dict):
        return {str(k): _j(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_j(v) for v in o]
    if isinstance(o, np.ndarray):
        return _j(o.tolist())
    if isinstance(o, (np.floating,)):
        return _j(float(o))
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float):
        return round(o, 6) if np.isfinite(o) else None
    return o


def map_active(prev, M):
    """Transfiere el estado de contacto (malla gruesa) a las facetas de la malla fina."""
    from scipy.spatial import cKDTree
    out = {}
    for cid, st in (prev or {}).items():
        if not st:
            continue
        d = {}
        for itf in M.interfaces:
            if itf.name in st:
                c0, a0 = st[itf.name]
                _, i = cKDTree(c0).query(M.S.fcent[itf.facets])
                d[itf.name] = a0[i]
        out[cid] = d
    return out


CONV_TOL = 0.20         # [SUPUESTO: el máx* se considera convergido si cambia ≤ 20 % de la malla gruesa a la fina]
RICH_TRIGGER = 0.10     # auditoría ronda 4 (F4): extrapolación tipo Richardson si el cambio gruesa → fina supera el 10 %
RICH_P = 2.0            # [SUPUESTO: orden de convergencia de la tensión con elementos P2 en un campo suave (error O(h²))]


def h_local(malla, pt):
    """Tamaño de malla en `pt`: el h de la esfera de refinamiento que lo contiene (la menor) o el h global."""
    h = malla["h_mm"]
    if pt is None:
        return h
    for (cx, cy, cz, rr, hl) in malla.get("refine") or []:
        if np.linalg.norm(np.asarray(pt, float) - np.array([cx, cy, cz])) <= rr:
            h = min(h, hl)
    return h


def richardson(sc, sf, hc, hf, p=RICH_P):
    """σ extrapolada a h → 0 con dos mallas: σ_f + (σ_f − σ_c)/(r^p − 1), r = h_c/h_f (tamaños locales). None si r ≈ 1."""
    if sc is None or sf is None or hf <= 0 or hc / hf < 1.05:
        return None
    return sf + (sf - sc) / ((hc / hf) ** p - 1.0)


def rich_block(sc, sf, pt, mallas, S):
    """Bloque de extrapolación (solo si |Δ| gruesa → fina > RICH_TRIGGER)."""
    if not mallas or "gruesa" not in mallas or "fina" not in mallas or sc is None or sf is None:
        return None
    if abs(sf - sc) <= RICH_TRIGGER * max(abs(sf), 1e-9):
        return None
    hc, hf = h_local(mallas["gruesa"], pt), h_local(mallas["fina"], pt)
    ext = richardson(sc, sf, hc, hf)
    return {"sigma_gruesa_MPa": sc, "sigma_fina_MPa": sf, "h_local_gruesa_mm": hc, "h_local_fina_mm": hf, "p": RICH_P,
            "sigma_ext_MPa": ext, "FS_ext": (S / ext) if ext and ext > 1e-9 else None}


def design_sigma(summ, key, coarse=None):
    """σ de diseño de un criterio: máx* si convergió (o si no hay malla gruesa con qué comparar); si no
    (pico en arista viva del CAD o astilla de malla que crece al refinar), el máximo del promedio en volumen
    en una esfera de radio fea_model.RHO_AVG. Devuelve (σ, método, cambio gruesa→fina del máx*)."""
    f = summ[key]
    if coarse is None:
        return f["max_excl"], "máx*", None
    c = coarse[key]["max_excl"]
    dif = (f["max_excl"] - c) / max(abs(f["max_excl"]), 1e-9)
    if abs(dif) <= CONV_TOL or f.get("max_vol") is None:
        return f["max_excl"], "máx*", dif
    return f["max_vol"], "promedio en volumen", dif


def allow_of(A, kind):
    """Admisible del caso: corta (fluencia), fatiga (reversa de sizing: S_fat si el material lo define) o sostenida."""
    if kind == "short":
        return A["S_short"]
    if kind == "fatiga" and A.get("S_fat") is not None:
        return A["S_fat"]
    return A["S_sust"]


def fs_block(summ, kind, A, coarse=None, regs=None, mallas=None):
    """FS = admisible / σ de diseño. Metal dúctil: von Mises. PETG: σvm, σ1 y σZ (entre capas).
    regs = (regiones gruesa, regiones fina): si el máx* global no convergió, la σ de diseño es la mayor entre
    el promedio en volumen y los máx* de las regiones que sí convergieron. Con mallas (gruesa y fina) y un cambio del
    máx* > RICH_TRIGGER se agrega la extrapolación tipo Richardson (informativa)."""
    S = allow_of(A, kind)

    def fs(Sa, s):
        return float(Sa / s) if s is not None and s > 1e-9 else 999.0

    at = {}

    def design(key):
        sg, mg, dg = design_sigma(summ, key, coarse)
        at[key] = summ[key]["at_max_excl_mm"] if mg == "máx*" else summ[key].get("at_max_vol_mm")
        if mg != "máx*" and regs and regs[0] and regs[1]:
            for rn, rf in regs[1].items():
                rc = regs[0].get(rn)
                if rc and rf[key]["max_excl"] is not None and rc[key]["max_excl"] is not None:
                    sr, mr, _ = design_sigma(rf, key, rc)
                    if mr == "máx*" and sr > sg:
                        sg, mg = sr, f"máx* de la región «{rn}», convergido"
                        at[key] = rf[key]["at_max_excl_mm"]
        return sg, mg, dg
    sv, mv, dv = design("vm")
    out = {"S_MPa": S, "vm": fs(S, sv), "sigma_vm_diseno_MPa": sv, "metodo_vm": mv, "dif_conv_vm": dv,
           "vm_max_excl": fs(S, summ["vm"]["max_excl"]), "vm_max_global": fs(S, summ["vm"]["max"]),
           "vm_p99": fs(S, summ["vm"]["p99"]), "vm_vol": fs(S, summ["vm"].get("max_vol"))}
    if coarse is not None:
        rb = rich_block(coarse["vm"]["max_excl"], summ["vm"]["max_excl"], summ["vm"]["at_max_excl_mm"], mallas, S)
        if rb:
            out["richardson_vm"] = rb
    crits = ["vm"]
    if A["tipo"] == "PETG":
        SZ = A["SZ_short"] if kind == "short" else A["SZ_sust"]
        s1, m1, d1 = design("s1")
        sz, mz, dz = design("sZ")
        out.update({"S_Z_MPa": SZ, "s1": fs(S, s1), "Z": fs(SZ, sz), "sigma_s1_diseno_MPa": s1, "sigma_Z_diseno_MPa": sz,
                    "metodo_s1": m1, "metodo_Z": mz, "dif_conv_s1": d1, "dif_conv_Z": dz,
                    "s1_max_global": fs(S, summ["s1"]["max"]), "Z_max_global": fs(SZ, summ["sZ"]["max"])})
        crits += ["s1", "Z"]
    out["ubicacion_mm"] = at
    crit = min(crits, key=lambda k: out[k])
    out["gobernante"] = out[crit]
    out["criterio"] = crit
    return out


def compare(out, level):
    """Filas de comparación FEA ↔ structural_<grupo>.py (σ de la región, escalada a la carga de la fila)."""
    rows = []
    for c in out.get("comparacion", []):
        case = out["casos"].get(c["caso"])
        if not case:
            continue
        reg = case[level]["regiones"].get(c["region"])
        if not reg:
            continue
        met = c.get("metrica", "max_excl")
        if reg["vm"].get(met) is None:
            continue
        val = reg["vm"][met]
        if met == "max_excl" and "gruesa" in case and level != "gruesa":
            rg = case["gruesa"]["regiones"].get(c["region"])
            if rg and rg["vm"]["max_excl"] is not None:
                val, met_used, _ = design_sigma(reg, "vm", rg)
                if met_used != "máx*":
                    met = "max_vol"
        s_fea = val * c["escala_carga"]
        s_p99 = reg["vm"]["p99"] * c["escala_carga"]
        S = c["S_cmp_MPa"]
        s_hand = None if c["sigma_MPa"] is None else c["sigma_MPa"] * c["k_mano_a_vm"]
        fs_fea = S / s_fea if s_fea > 1e-9 else 999.0
        fs_hand = (S / s_hand) if s_hand else c["FS"]
        dif = (fs_fea - fs_hand) / fs_hand if fs_hand else None
        rows.append({**c, "metrica": met, "sigma_FEA_MPa": s_fea, "sigma_FEA_p99_MPa": s_p99, "sigma_mano_vm_MPa": s_hand,
                     "FS_FEA": fs_fea, "FS_FEA_p99": S / s_p99 if s_p99 > 1e-9 else 999.0, "FS_mano_cmp": fs_hand,
                     "dif_FS_rel": dif, "at_mm": reg["vm"]["at_max_excl_mm"]})
    return rows


def edge_block(rec, level, A, quick, mallas):
    """Borde de los agujeros cargados por perno a ±90° de la carga (auditoría ronda 4, F3): FS = admisible del caso /
    |σθ| máx. del borde (tensión circunferencial de sección neta del «lug») en la malla reportada; convergencia gruesa →
    fina y extrapolación tipo Richardson si > 10 %. El σvm de la ventana se reporta (incluye el aplastamiento)."""
    S = allow_of(A, rec["tipo"])
    out = {}
    for hn, bf in (rec[level].get("bordes") or {}).items():
        sf = bf["s_theta_abs_max"]
        d = {"sigma_theta_MPa": sf, "signo_sigma_theta": bf.get("s_theta_signo"), "sigma_vm_en_el_punto_MPa": bf.get("vm_en_s_theta"),
             "sigma_vm_ventana_MPa": bf["vm_max"], "at_vm_ventana_mm": bf["at_vm_mm"], "theta_vm_ventana_deg": bf.get("theta_vm_deg"),
             "S_MPa": S, "FS": S / sf if sf > 1e-9 else 999.0, "FS_vm_ventana": S / bf["vm_max"] if bf["vm_max"] > 1e-9 else 999.0,
             "at_mm": bf["at_s_theta_mm"], "theta_deg": bf.get("theta_s_theta_deg"), "n_nodos": bf.get("n_nodos")}
        if not quick and "gruesa" in rec and level != "gruesa":
            bc = (rec["gruesa"].get("bordes") or {}).get(hn)
            if bc:
                d["sigma_theta_gruesa_MPa"] = bc["s_theta_abs_max"]
                d["dif_conv"] = (sf - bc["s_theta_abs_max"]) / max(abs(sf), 1e-9)
                d["convergido"] = abs(d["dif_conv"]) <= CONV_TOL
                rb = rich_block(bc["s_theta_abs_max"], sf, bf["at_s_theta_mm"], mallas, S)
                if rb:
                    d["richardson"] = rb
        out[hn] = d
    return out


def postprocess(out, A, quick, est=None):
    """FS por caso, convergencia, caso gobernante y comparación con el cálculo a mano. Con `est`
    (estructural.json vigente) refresca antes las filas a mano de la comparación."""
    level = out["nivel_reportado"]
    if est is not None:
        import fea_parts as fp
        pid = out["pid"]
        for c in out.get("comparacion", []):
            h = next((r for r in est.get("rows", []) if r.get("part") == pid and r.get("load_case") == c["load_case"]), None) \
                or fp.hand_row(est, pid, c["load_case"][:30])
            if h:
                c.update({"sigma_MPa": h.get("sigma_MPa"), "FS": h.get("FS"), "S_MPa": h.get("S_MPa"), "model": h.get("model")})
                if c.get("S_cmp_MPa") is None:
                    c["S_cmp_MPa"] = h.get("S_MPa")
    fs_min, gov = 1e9, None
    mallas = out.get("mallas")
    design = [cid for cid, rec in out["casos"].items() if rec.get("diseno", True)] or list(out["casos"])
    for cid, rec in out["casos"].items():
        rec["FS"] = fs_block(rec[level]["resumen"], rec["tipo"], A, None if quick else rec["gruesa"]["resumen"],
                             None if quick else (rec["gruesa"].get("regiones"), rec["fina"].get("regiones")), mallas)
        rec["FS"]["gobernante_cuerpo"], rec["FS"]["criterio_cuerpo"] = rec["FS"]["gobernante"], rec["FS"]["criterio"]
        eb = edge_block(rec, level, A, quick, mallas)
        rec["FS_bordes"] = eb
        if eb:
            hn = min(eb, key=lambda k: eb[k]["FS"])
            if eb[hn]["FS"] < rec["FS"]["gobernante"]:
                rec["FS"].update({"gobernante": eb[hn]["FS"], "criterio": "borde", "borde": hn})
        if not quick:
            g, f_ = rec["gruesa"]["resumen"], rec["fina"]["resumen"]
            conv = {k: {"gruesa": g[a][s_], "fina": f_[a][s_], "dif_rel": (f_[a][s_] - g[a][s_]) / max(abs(f_[a][s_]), 1e-9)}
                    for k, a, s_ in (("vm_p99", "vm", "p99"), ("vm_max_excl", "vm", "max_excl"), ("vm_max", "vm", "max"))}
            conv["u_max"] = {"gruesa": g["u_max_mm"], "fina": f_["u_max_mm"],
                             "dif_rel": (f_["u_max_mm"] - g["u_max_mm"]) / max(f_["u_max_mm"], 1e-12)}
            rc = {}
            for rn, rv in rec["fina"]["regiones"].items():
                gv = rec["gruesa"]["regiones"].get(rn)
                if gv:
                    k = "max_excl" if (gv["vm"]["max_excl"] is not None and rv["vm"]["max_excl"] is not None) else "mean"
                    rc[rn] = {"metrica": k, "gruesa": gv["vm"][k], "fina": rv["vm"][k],
                              "dif_rel": (rv["vm"][k] - gv["vm"][k]) / max(rv["vm"][k], 1e-9)}
            conv["regiones_vm_max_excl"] = rc
            rec["convergencia"] = conv
        fsb = rec["FS"]["gobernante"]
        if cid in design and fsb < fs_min:
            fs_min, gov = fsb, cid
    out["casos_diseno"] = design
    out["FS_min"] = fs_min
    out["FS_objetivo"] = A["fs_target"]
    out["cumple"] = bool(fs_min >= A["fs_target"])
    out["caso_gobernante"] = gov
    out["criterio_gobernante"] = out["casos"][gov]["FS"]["criterio"]
    out["comparacion_mano"] = compare(out, level)


def run_part(pid, quick=False, no_img=False, img_dir=None, log_prefix=None, cfg=None):
    import fea_parts as fp
    from fea_model import hole_edge, mesh_quality
    t0 = time.time()
    pre = log_prefix or pid

    def log(msg):
        print(f"[{pre}] {msg}", flush=True)
    p, mods, est = fp.load_project()
    cfg = cfg or CFG[pid]
    levels = [("gruesa", cfg["h"][0], cfg["curv"][0])]
    if not quick:
        levels.append(("fina", cfg["h"][1], cfg["curv"][1]))
    h_ref = levels[-1][1]
    r_ex = max(R_EX_MIN, h_ref)
    meta = mods[pid].META
    out = {"pid": pid, "descripcion": meta["desc"], "material": meta["material"], "print_rot": list(meta.get("print_rot", (0, 0, 0))),
           "dir_Z_impresion_marco_pieza": fp.print_z_dir(meta).round(4).tolist(), "frame": meta["frame"],
           "mallas": {}, "casos": {}, "r_exclusion_mm": r_ex}
    prev_active, last = None, None
    for level, h, cn in levels:
        tl = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            st = fp.SETUPS[pid](p, mods, est, h, cn, tmp, log=log, hmin=cfg["hmin"])
        M = st["model"]
        S = M.S
        A = st["allow"]
        out["admisibles"] = A
        out["marco"] = st.get("frame_label", meta["frame"])
        q = mesh_quality(S.X, S.T)
        out["mallas"][level] = {"h_mm": h, "curv_n": cn, "h_min_mm": cfg["hmin"], "n_tets": int(len(S.T)),
                                "refine": st["mesh"].get("refine"),
                                "n_nodos_vertice": int(S.N), "n_nodos_P2": int(S.nnodes), "n_gdl": int(S.ndof),
                                "calidad_gamma_min": float(q.min()), "calidad_gamma_p01": float(np.percentile(q, 1)),
                                "n_gamma_menor_0_05": int((q < 0.05).sum()),
                                "fuente_geometria": st["mesh"]["source"], "t_ensamble_s": round(M.t_asm, 2)}
        log(f"malla {level}: h={h} mm, {len(S.T)} tetraedros, {S.ndof} gdl, γmin={q.min():.3f}")
        init = map_active(prev_active, M) if prev_active else None
        cases = st["run"](log=None, init=init)
        prev_active = {c["id"]: c.get("active") for c in cases if c.get("active")}
        fields_keep = {}
        for c in cases:
            if c.get("active"):
                for itf in M.interfaces:
                    if itf.name in c["active"]:
                        itf.active = c["active"][itf.name][1]
            F = M.stress_fields(c["u"])
            ez = c.get("zones_extra", ())
            off = [itf for itf in M.interfaces if itf.name in c.get("disabled", ())]
            sk = [itf.facets for itf in off]                  # interfaz ausente: su agujero se evalúa (no es zona)
            summ = M.summarize(F, r_ex, extra_zones=ez, skip_zones=sk)
            regs = M.region_summary(F, r_ex, st.get("regions", {}), extra_zones=ez, skip_zones=sk)
            bordes = {}
            for hn, hs in st.get("holes", {}).items():         # borde de agujeros cargados a ±90° de la carga (F3)
                dv = (c.get("dir_agujeros") or {}).get(hn)
                if dv is not None and np.linalg.norm(dv) > 1e-6:
                    be = hole_edge(S, F, hs, dv)
                    if be:
                        bordes[hn] = be
            for itf in off:                                   # interfaz ausente en este caso (émbolo que no entró)
                itf.enabled = False
            reac = M.interface_forces(c["u"]) if M.interfaces else {}
            for itf in off:
                itf.enabled = True
            info = c.get("info", {})
            rec = out["casos"].setdefault(c["id"], {"nombre": c["name"], "tipo": c["kind"], "diseno": bool(c.get("diseno", True))})
            rec[level] = {"resumen": summ, "regiones": regs, "reacciones": reac, "extra": c.get("extra", {}), "bordes": bordes,
                          "solver": {k: info.get(k) for k in ("contact_iters", "contact_changes", "cg_total", "case_s",
                                                              "converged_contact", "residual_changes_accepted", "rel_res")
                                     if k in info}}
            fields_keep[c["id"]] = {"vm": F["vm"], "sZ": F["sZ"], "u": F["u"]}
        out["verificacion_mano"] = st["checks"]
        out["agujeros"] = {hn: {k: hs[k] for k in ("c", "ax", "r")} for hn, hs in st.get("holes", {}).items()}
        out["comparacion"] = st.get("comparacion", [])
        log(f"  {level} listo en {time.time() - tl:.1f} s")
        last = (level, M, fields_keep)
    level, M, fields_keep = last
    A = out["admisibles"]
    out["nivel_reportado"] = level
    postprocess(out, A, quick)
    # variantes propuestas (solo evaluación: la pieza NO se modifica; geometría alterada dentro del modelo FEA)
    out["variantes"] = {}
    for vname, var in ({} if quick else cfg.get("variantes", {})).items():
        tv = time.time()
        lv_name, h, cn = levels[-1]
        with tempfile.TemporaryDirectory() as tmp:
            stv = fp.SETUPS[pid](p, mods, est, h, cn, tmp, log=log, hmin=cfg["hmin"], variant=var["param"])
        Mv = stv["model"]
        vc = {}
        for c in stv["run"](log=None):
            Fv = Mv.stress_fields(c["u"])
            sv = Mv.summarize(Fv, r_ex)
            rv = Mv.region_summary(Fv, r_ex, stv.get("regions", {}))
            vc[c["id"]] = {"resumen": sv, "regiones": rv, "FS": fs_block(sv, c["kind"], stv["allow"]), "extra": c.get("extra", {})}
        out["variantes"][vname] = {"descripcion": var["desc"], "param": var["param"], "n_tets": int(len(Mv.S.T)),
                                   "objetivo": var.get("objetivo", stv["allow"]["fs_target"]),
                                   "casos": vc, "tiempo_s": round(time.time() - tv, 1)}
        log(f"  variante {vname}: FS {min(v['FS']['gobernante'] for v in vc.values()):.2f}")
    fs_min, gov = out["FS_min"], out["caso_gobernante"]
    imgs = []
    if not no_img and img_dir is not None:
        import fea_plot
        img_dir.mkdir(parents=True, exist_ok=True)
        fk = fields_keep[gov]
        S = M.S
        nm = out["casos"][gov]["nombre"]
        summ = out["casos"][gov][level]["resumen"]
        views = VIEWS.get(pid, ((22, -58), (22, 122)))
        path = img_dir / f"{pid}_vm.png"
        top = out["casos"][gov]["FS"]["sigma_vm_diseno_MPa"] * 1.25
        fea_plot.stress_figure(S, fk["vm"], f"{pid} — von Mises, caso {gov}: {nm[:95]}\nmáx. fuera de zonas de carga "
                               f"{summ['vm']['max_excl']:.1f} MPa · p99 {summ['vm']['p99']:.1f} MPa · máx. global "
                               f"{summ['vm']['max']:.1f} MPa · admisible {out['casos'][gov]['FS']['S_MPa']:.0f} MPa",
                               path, views=views, label="σ von Mises [MPa]", vmax=top,
                               mark=summ["vm"]["at_max_excl_mm"])
        imgs.append(str(path.relative_to(ROOT)))
        if A["tipo"] == "PETG":
            path = img_dir / f"{pid}_sZ.png"
            fea_plot.stress_figure(S, fk["sZ"], f"{pid} — σ normal a las capas (Z de impresión), caso {gov}\n"
                                   f"máx. tracción fuera de zonas {summ['sZ']['max_excl']:.2f} MPa · admisible "
                                   f"{out['casos'][gov]['FS']['S_Z_MPa']:.1f} MPa",
                                   path, views=views, diverging=True, label="σ_Z [MPa] (+ tracción entre capas)")
            imgs.append(str(path.relative_to(ROOT)))
        u = fk["u"]
        um = np.linalg.norm(u, axis=1).max()
        size = np.ptp(S.X, axis=0).max()
        scale = 0.06 * size / max(um, 1e-12)
        path = img_dir / f"{pid}_deformada.png"
        fea_plot.stress_figure(S, np.linalg.norm(u, axis=1), f"{pid} — desplazamiento, caso {gov} "
                               f"(deformada ×{scale:.0f}; máx. {um:.4f} mm)", path, views=views[:1],
                               label="|u| [mm]", deform=u, scale=scale)
        imgs.append(str(path.relative_to(ROOT)))
    out["imagenes"] = imgs
    out["tiempo_s"] = round(time.time() - t0, 1)
    log(f"FS mínimo {fs_min:.2f} (caso {gov}, criterio {out['criterio_gobernante']}); {out['tiempo_s']} s")
    return pid, _j(out)


# ---------------------------------------------------------------------------
# README (bloque AUTO)
# ---------------------------------------------------------------------------
AUTO0, AUTO1 = "<!-- FEA:AUTO:INICIO (generado por fea_run.py; no editar a mano) -->", "<!-- FEA:AUTO:FIN -->"


def _f(x, n=2):
    return "—" if x is None else (f"{x:.{n}f}" if abs(x) < 999 else "≫")


def verdict(fs, target, design=True):
    if fs is None:
        return "—"
    if not design:
        return "informativo"
    return "cumple" if fs >= target else "**NO CUMPLE**"


def readme_block(res):
    L = [AUTO0, "", f"Corrida: {res['meta']['fecha']} · inputs v{res['meta']['inputs_version']} · "
         f"{res['meta']['tiempo_total_s']:.0f} s [CALCULADO]", ""]
    L += ["### Materiales y admisibles", "", "| Pieza | Material | Admisible [MPa] | Criterio | FS objetivo | Marco |", "|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        A = r["admisibles"]
        if A["tipo"] == "PETG":
            adm = f"S_corta {A['S_short']:.2f} · S_Z corta {A['SZ_short']:.2f}"
            crit = "σvm, σ1 y σZ (Z de impresión " + str(tuple(round(x, 2) + 0.0 for x in r["dir_Z_impresion_marco_pieza"])) + ")"
        else:
            adm = f"{A['S_short']:.0f} ({A['material']})"
            crit = "von Mises"
        L.append(f"| {pid} | {r['material']} | {adm} | {crit} | {A['fs_target']:.0f} | {r['marco']} |")
    L += ["", "### Mallas", "", "| Pieza | Malla | h [mm] | Tetraedros | gdl (P2) | γ mín | γ p1 | n(γ<0,05) |",
          "|---|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for lv, m in r["mallas"].items():
            L.append(f"| {pid} | {lv} | {m['h_mm']:g} | {m['n_tets']} | {m['n_gdl']} | {m['calidad_gamma_min']:.3f} | "
                     f"{m['calidad_gamma_p01']:.3f} | {m['n_gamma_menor_0_05']} |")
    L += ["", "### Resultados (malla fina) — tensiones en MPa; FS = admisible / σ de diseño", "",
          "σ de diseño = σvm máx* (máximo fuera de r_excl de cargas y apoyos) si cambia ≤ 20 % de la malla gruesa a la fina; "
          "si no converge (arista viva del CAD o astilla de malla), el máximo del promedio en una esfera de radio 3 mm "
          "(«prom.»). En PETG el FS es el menor de σvm, σ1 y σZ (el criterio va entre paréntesis). El FS del caso es el "
          "menor entre el del cuerpo y el del borde de los agujeros cargados (tabla de bordes; criterio «borde»). Casos de "
          "fatiga (reversa de sizing) contra el admisible de fatiga del material; casos «informativo» fuera del FS mínimo.", "",
          "| Pieza | Caso | σvm máx | σvm p99 | σvm máx* | σvm prom. | σ diseño | u máx [mm] | **FS** | FS (p99) | Veredicto |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        lv = r["nivel_reportado"]
        for cid, c in r["casos"].items():
            s = c[lv]["resumen"]
            fs = c["FS"]
            extra = ""
            if fs["criterio"] != "vm":
                extra = f" ({fs['criterio']})"
            sd = fs.get("sigma_vm_diseno_MPa")
            if fs["criterio"] == "borde":
                b = c["FS_bordes"][fs["borde"]]
                extra = f" (borde {fs['borde']})"
                sd_txt = f"borde {fs['borde']}: σθ {_f(b['sigma_theta_MPa'])}"
            elif fs["criterio"] == "Z":
                sd_txt = f"σZ {_f(fs['sigma_Z_diseno_MPa'])} ({fs['metodo_Z']})"
            elif fs["criterio"] == "s1":
                sd_txt = f"σ1 {_f(fs['sigma_s1_diseno_MPa'])} ({fs['metodo_s1']})"
            else:
                sd_txt = f"{_f(sd)} ({fs['metodo_vm']})"
            L.append(f"| {pid} | {cid}: {c['nombre']} | {_f(s['vm']['max'])} | {_f(s['vm']['p99'])} | {_f(s['vm']['max_excl'])} | "
                     f"{_f(s['vm'].get('max_vol'))} | {sd_txt} | {_f(s['u_max_mm'], 3)} | **{_f(fs['gobernante'])}**{extra} | "
                     f"{_f(fs['vm_p99'])} | {verdict(fs['gobernante'], r['FS_objetivo'], c.get('diseno', True))} |")
    L += ["", "\\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de "
          "convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.", ""]
    brows = [(pid, cid, hn, b) for pid, r in res["piezas"].items() for cid, c in r["casos"].items()
             for hn, b in (c.get("FS_bordes") or {}).items()]
    if brows:
        L += ["### Borde de los agujeros cargados por perno (sección neta, a ±90° de la carga)", "",
              "Nodos de la superficie del agujero con |cos θ| ≤ 0,5 respecto de la dirección de la carga (θ = 60…120°), zona "
              "que la exclusión r_excl del máx* no mira (auditoría ronda 4, F3). Se verifica la tensión circunferencial |σθ| "
              "(sección neta del «lug»): FS = admisible del caso / |σθ| máx. (malla fina). σvm de la ventana: informativo (en el "
              "arco de contacto incluye el aplastamiento y el borde del contacto, que verifican las filas de aplastamiento). Si "
              "|σθ| cambia > 10 % de la gruesa a la fina se extrapola (tipo Richardson, p = 2, tamaños locales).", "",
              "| Pieza | Caso | Agujero | σθ (valor abs.) gruesa → fina [MPa] | θ [°] | σvm ventana [MPa] (FS) | **FS** | Richardson σ_ext (FS) |",
              "|---|---|---|---|---|---|---|---|"]
        for pid, cid, hn, b in brows:
            conv = (f"{_f(b.get('sigma_theta_gruesa_MPa'))} → {_f(b['sigma_theta_MPa'])} ({100 * b['dif_conv']:+.0f} %)"
                    if b.get("dif_conv") is not None else _f(b["sigma_theta_MPa"]))
            rb = b.get("richardson")
            rtxt = "—" if not rb or rb.get("sigma_ext_MPa") is None else f"{_f(rb['sigma_ext_MPa'])} ({_f(rb['FS_ext'])})"
            L.append(f"| {pid} | {cid} | {hn} | {conv} | {_f(b.get('theta_deg'), 0)} | {_f(b['sigma_vm_ventana_MPa'])} "
                     f"({_f(b['FS_vm_ventana'])}) | **{_f(b['FS'])}** | {rtxt} |")
        L += [""]
    L += ["### Convergencia (gruesa → fina)", "",
          "Columna «Richardson»: si el máx* cambia > 10 %, σ_ext = σ_f + (σ_f − σ_g)/(r^p − 1) con r = h_g/h_f locales (esferas "
          "de refinamiento) y p = 2 [SUPUESTO: tensión con P2 en campo suave]; informativo, entre paréntesis el FS con σ_ext.", "",
          "| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] | Richardson máx* |",
          "|---|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for cid, c in r["casos"].items():
            cv = c.get("convergencia")
            if not cv:
                continue

            def cell(k, n=2):
                v = cv[k]
                return f"{_f(v['gruesa'], n)} → {_f(v['fina'], n)} ({100 * v['dif_rel']:+.0f} %)"
            rb = c["FS"].get("richardson_vm")
            rtxt = "—" if not rb or rb.get("sigma_ext_MPa") is None else f"{_f(rb['sigma_ext_MPa'])} ({_f(rb['FS_ext'])})"
            L.append(f"| {pid} | {cid} | {r['r_exclusion_mm']:.0f} | {cell('vm_p99')} | {cell('vm_max_excl')} | {cell('vm_max')} | "
                     f"{cell('u_max', 4)} | {rtxt} |")
    L += ["", "### Comparación con el cálculo a mano (resultados/estructural.json)", "",
          "σ FEA = σvm de la región de la pieza que modela la fila (máx* salvo que se indique promedio en volumen), "
          "escalada a la carga de la fila (columna «×»). "
          "FS con el admisible de la fila. Dif = (FS_FEA − FS_mano)/FS_mano.", "",
          "| Pieza | Fila structural_*.py | Caso FEA · región | × | σ mano [MPa] | σ FEA [MPa] (p99) | FS mano | FS FEA | Dif |",
          "|---|---|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for c in r["comparacion_mano"]:
            flag = " ⚠" if c["dif_FS_rel"] is not None and abs(c["dif_FS_rel"]) > 0.30 else ""
            dif = "—" if c["dif_FS_rel"] is None else f"{100 * c['dif_FS_rel']:+.0f} %"
            met = {"max_excl": "máx*", "mean": "promedio", "p99": "p99", "max_vol": "prom. esfera"}[c.get("metrica", "max_excl")]
            L.append(f"| {pid} | {c['load_case']} | {c['caso']} · {c['region']} ({met}) | {c['escala_carga']:.2f} | "
                     f"{_f(c['sigma_mano_vm_MPa'])} | {_f(c['sigma_FEA_MPa'])} ({_f(c['sigma_FEA_p99_MPa'])}) | "
                     f"{_f(c['FS_mano_cmp'])} | {_f(c['FS_FEA'])} | "
                     f"{dif}{flag} |")
    var_rows = [(pid, vn, v) for pid, r in res["piezas"].items() for vn, v in r.get("variantes", {}).items()]
    if var_rows:
        L += ["", "### Variantes propuestas (evaluadas en el modelo FEA; la pieza NO se modificó)", "",
              "| Pieza | Variante | Caso | σvm máx* | σvm p99 | u máx [mm] | FS (máx*) | FS (p99) | Veredicto |", "|---|---|---|---|---|---|---|---|---|"]
        for pid, vn, v in var_rows:
            tgt = v.get("objetivo", res["piezas"][pid]["FS_objetivo"])      # objetivo por variante (auditoría ronda 4, M5)
            for cid, c in v["casos"].items():
                s = c["resumen"]
                L.append(f"| {pid} | {vn}: {v['descripcion']} | {cid} | {_f(s['vm']['max_excl'])} | {_f(s['vm']['p99'])} | "
                         f"{_f(s['u_max_mm'], 3)} | **{_f(c['FS']['gobernante'])}** | {_f(c['FS']['vm_p99'])} | "
                         f"{verdict(c['FS']['gobernante'], tgt)} |")
    L += ["", "⚠ diferencia > 30 %: explicada en «Hallazgos».", "", "### Hallazgos cuantitativos", ""] + res["hallazgos"] + ["", AUTO1]
    return "\n".join(L)


def findings(res):
    """Hallazgos con las cifras vigentes (una viñeta por pieza)."""
    H = []
    for pid, r in res["piezas"].items():
        lv = r["nivel_reportado"]
        g = r["casos"][r["caso_gobernante"]]
        s = g[lv]["resumen"]
        tgt = r["FS_objetivo"]
        fsg = g["FS"]
        if fsg["criterio"] == "borde":
            b = g["FS_bordes"][fsg["borde"]]
            conv = "" if b.get("dif_conv") is None else f", gruesa→fina {100 * b['dif_conv']:+.0f} %"
            desc = (f"borde del agujero «{fsg['borde']}» a ±90° de la carga: |σθ| {b['sigma_theta_MPa']:.1f} MPa{conv} en "
                    f"{tuple(b['at_mm'])} mm (cuerpo: FS {fsg['gobernante_cuerpo']:.2f})")
        else:
            k = {"vm": ("vm", "sigma_vm_diseno_MPa", "metodo_vm", "dif_conv_vm"), "s1": ("s1", "sigma_s1_diseno_MPa", "metodo_s1", "dif_conv_s1"),
                 "Z": ("sZ", "sigma_Z_diseno_MPa", "metodo_Z", "dif_conv_Z")}[fsg["criterio"]]
            at = fsg.get("ubicacion_mm", {}).get(k[0]) or s[k[0]]["at_max_excl_mm"]
            conv = "" if fsg.get(k[3]) is None else f", máx* gruesa→fina {100 * fsg[k[3]]:+.0f} %"
            desc = f"σ de diseño {fsg[k[1]]:.1f} MPa ({fsg[k[2]]}{conv}) en {tuple(at)} mm"
        rb = fsg.get("richardson_vm")
        rtxt = "" if not rb or rb.get("FS_ext") is None else f" Extrapolación tipo Richardson del máx*: {rb['sigma_ext_MPa']:.1f} MPa (FS {rb['FS_ext']:.2f})."
        H.append(f"- **{pid}: FS = {r['FS_min']:.2f}** (objetivo {tgt:.0f}, {'cumple' if r['cumple'] else '**NO CUMPLE**'}); "
                 f"caso {r['caso_gobernante']}, criterio {fsg['criterio']}: {desc}; σvm p99 {s['vm']['p99']:.1f} MPa "
                 f"(FS p99 {fsg['vm_p99']:.2f}).{rtxt} {PART_NOTES.get(pid, '')}")
        for c in r["comparacion_mano"]:
            if c["dif_FS_rel"] is not None and abs(c["dif_FS_rel"]) > 0.30:
                H.append(f"  - ⚠ «{c['load_case']}»: FS mano {c['FS_mano_cmp']:.2f} vs FS FEA {c['FS_FEA']:.2f} "
                         f"({100 * c['dif_FS_rel']:+.0f} %). {NOTES.get((pid, c['load_case'][:24]), '')}")
    return H


PART_NOTES = {    # notas por pieza: dónde está el máximo y por qué (las cifras están en la tabla y en el JSON)
    "P1-DRV-03": "Alma de ±0,35·Ø del alojamiento con empalmes r 3 alma–tablero y alma–alojamiento (auditoría ronda 3, "
                 "F-03): el máximo queda sobre el empalme alma–tablero y converge (antes era una arista viva, en una cuña "
                 "de ~30° entre el alojamiento y el tablero, que no convergía). Cumple con margen.",
    "P1-REV-01": "Criterio de traba única (ronda 4): con una traba sola (d/e a R12, f/g con la reversa de sizing contra el "
                 "admisible de fatiga de soldadura) todo M_h pasa por un brazo y la cuchara abierta gira hasta él; el máximo "
                 "queda en la cara exterior del brazo trabado, sobre su borde, bajo el pivote (el punto caliente de la ronda 3, "
                 "ahora dentro de una esfera de refinamiento en las dos mallas). Con las dos trabas sin desfase (a, informativo) "
                 "cada una toma la mitad de M_h. El borde de los agujeros de traba y de pivote (|σθ| de sección neta a ±90°) "
                 "queda por debajo del cuerpo; el σvm de la ventana de la traba incluye el borde del contacto del perno rígido "
                 "(aplastamiento). Carga = balance de cantidad de movimiento del chorro, con resultante y momento verificados "
                 "contra bucket_reactions.",
    "P1-STE-01": "Cargas del bucket autoequilibradas por oreja (ronda 4, F1): fuerza en el piloto Ø16 y en la rosca M24 de "
                 "la misma oreja, momentos del muñón y del perno en voladizo como pares de resultante nula (brida y "
                 "contratuerca); resultante y momento verificados contra la estática. Con M_h completo en una traba gobierna "
                 "la oreja de esa traba: el borde de la rosca M24 o del piloto a ±90° de la carga (|σθ| de sección neta, que "
                 "la exclusión del máx* tapaba: F3) y el contorno del lóbulo de la rosca en la cara exterior. Los casos de "
                 "fatiga (f/f2) tienen el menor FS: la reversa de sizing es la mitad de R12 pero el admisible de fatiga es "
                 "bastante menos que la mitad de la fluencia. El pico donde la oreja de pivote toca el labio de entrada "
                 "(radio de 2 mm, F-03) converge.",
    "P1-INT-02": "Gobierna el golpe de fondo con la placa sola (b): máximo en la cara superior sobre el borde del "
                 "apoyo del ala (unión cuerpo–ala), convergido. Con el conducto como rigidizador (b2) baja a "
                 "≈ 18 MPa. Los avellanados M8 del pórtico: σvm promedio bajo el cono ≈ presión de la fila a mano.",
    "P1-CTL-02": "Paredes de 5 mm engrosadas hacia afuera (ronda 3, F-02; el entrehierro del sensor hall no cambia): "
                 "gobierna la tapa (von Mises) y la tracción entre capas de las paredes ya no manda; la variante V1 "
                 "(paredes de 4 mm) muestra la sensibilidad. La pieza real es 5 perímetros + 30 % giroide (solid_frac "
                 "0,55): el FEA macizo es optimista.",
}

# Explicaciones de las diferencias > 30 % (clave: (pieza, primeros 24 caracteres de la fila de structural_*.py)).
NOTES = {
    ("P1-DRV-03", "Mejillas: empuje Fa a pu"):
        "La fila solo mira la flexión de la mejilla en su plano por Fa/2 (sección 12 × 150, muy rígida). El FEA pone el "
        "máximo de la mejilla en su unión con el tablero: el tablero cargado por el alojamiento flexiona y arrastra el "
        "borde superior de la mejilla fuera de su plano (marco tablero + mejillas). Mecanismo que la fila no ve; nivel bajo.",
    ("P1-DRV-03", "Tablero: 3 g vertical de"):
        "El máximo está en la unión del alma central con el tablero (ahora con empalme r 3): el momento de Fa excéntrico y "
        "el radial entran al tablero por el alma; la viga biapoyada de la fila no ve esa concentración. FS sobre 2.",
    ("P1-DRV-03", "Alojamiento Ø47: Fa sobr"):
        "La fila es el corte medio del resalte (τ = Fa/(π·D·t)), un valor nominal; el FEA mide la flexión del resalte como "
        "placa anular (el aro apoya solo entre Da_max y D) y la del alojamiento en su unión con el alma. Ambos lejos del admisible.",
    ("P1-REV-01", "Brazo trabado: flexión e"):
        "La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA "
        "suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el "
        "pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño "
        "es el del FEA.",
    ("P1-REV-01", "Cuchara abierta a torsió"):
        "La fila es torsión de Saint-Venant de la sección abierta con T = M_h en la unión con el brazo trabado, sin "
        "restricción de alabeo (cota). En el FEA (una traba sola) los brazos y el aro restringen el alabeo y parte del "
        "momento entra al brazo como flexión fuera del plano: la cuchara trabaja menos. Fila conservadora para la cuchara.",
    ("P1-REV-01", "Cuchara como viga entre "):
        "La fila trata la cuchara como viga entre brazos; con las dos trabas (a) la cuchara casi no trabaja (σ de pocos MPa "
        "en los dos modelos): diferencia relativa grande sobre valores chicos.",
    ("P1-REV-01", "Chapa de la cuchara: fra"):
        "La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a "
        "p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.",
    ("P1-REV-01", "Pivote: aplastamiento de"):
        "La fila es la presión media R/(d·L) con la reacción del pivote de una traba sola. El FEA promedia σvm en un "
        "anillo de 3 mm alrededor de los pivotes, que además de la presión del buje incluye la flexión del brazo: métricas "
        "distintas, las dos lejos del admisible.",
    ("P1-REV-01", "Agujero de traba: aplast"):
        "La fila es la presión media F/(d·t) con M_h completo en una traba; el FEA promedia σvm en un anillo de 3 mm "
        "alrededor del agujero de la traba cargada (caso d): por definición menor que el pico. Mismo orden de magnitud.",
    ("P1-STE-01", "Flexión del tubo por el "):
        "La fila trata el tubo Ø101 como viga (σ nominal < 1 MPa). En el FEA el máximo de la región del tubo está donde se "
        "le unen la torre y la oreja de pivote superior (entra el par del yugo y la reacción de los pernos): concentración "
        "local que la viga no ve. Nivel bajo (FS > 10).",
    ("P1-STE-01", "Oreja del bucket: flexió"):
        "Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; "
        "fuera del plano: momento del espaciador). El FEA pone el máximo de la oreja en el lóbulo de la rosca M24 y en el "
        "borde de los agujeros, donde la fuerza del perno, el par de la contratuerca y el del espaciador concentran: "
        "mecanismo local que la viga no ve; el FS de diseño es el del FEA.",
    ("P1-STE-01", "Oreja del bucket: ligame"):
        "La fila es el desgarro de los dos ligamentos de la rosca M24 (τ media). El FEA da el máx* del lóbulo de la rosca "
        "fuera de r_excl (flexión del lóbulo por la fuerza del perno y el par de la contratuerca) y el borde del agujero "
        "aparte (tabla de bordes): mecanismos distintos.",
    ("P1-STE-01", "Oreja del bucket: aplast"):
        "La fila es la presión media del piloto Ø16 si la unión desliza; el FEA promedia σvm en el anillo de 3 mm alrededor "
        "del piloto (apoyo cosenoidal + par de la brida): métricas distintas, las dos lejos del admisible.",
    ("P1-STE-01", "Oreja de pivote (dentro "):
        "La fila toma F/2 a 12 mm en 25 × 30. En el FEA los pernos de pivote reciben un par (reacciones opuestas en la "
        "mejilla Ø8 y en la rosca M6) porque el bucket empuja muy por encima del eje; el máximo está donde la oreja "
        "cilíndrica se une al frente esférico.",
    ("P1-INT-02", "Paño lateral entre bulon"):
        "La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, "
        "la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota "
        "conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.",
    ("P1-INT-02", "Arranque de la cabeza M8"):
        "La fila usa τ media en el cilindro Ø dk × (t − h_cono) suponiendo que todo el tiro pasa por corte puro. En el FEA "
        "la compresión de la zapata sobre la cara superior equilibra la precarga en el mismo lugar y el cilindro no está "
        "en corte puro: el promedio de σvm en ese volumen es menor. Fila conservadora.",
    ("P1-INT-02", "Asiento cónico de la cab"):
        "La fila divide la fuerza por la proyección del cono; el FEA promedia σvm en una capa de 1,5 mm bajo el cono.",
    ("P1-CTL-02", "Tapa PETG 6 mm: mano apo"):
        "La fila es una franja 50 × 6 apoyada con luz 50; la tapa real está casi toda ranurada (ranuras de las palancas), "
        "y la palma carga el nervio de 6 mm entre las dos ranuras o la tapa angosta junto a la del bucket.",
}


def write_readme(res):
    rd = HERE / "README.md"
    txt = rd.read_text(encoding="utf-8") if rd.exists() else "# FEA\n\n" + AUTO0 + "\n" + AUTO1 + "\n"
    if AUTO0 in txt and AUTO1 in txt:
        i0, i1 = txt.index(AUTO0), txt.index(AUTO1) + len(AUTO1)
        txt = txt[:i0] + readme_block(res) + txt[i1:]
    else:
        txt += "\n" + readme_block(res) + "\n"
    rd.write_text(txt, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--serial", action="store_true")
    ap.add_argument("--no-img", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--readme-only", action="store_true", help="regenera hallazgos y el bloque AUTO desde el JSON existente")
    ap.add_argument("--merge", action="store_true",
                    help="con --only: reemplaza esas piezas en el JSON existente y regenera hallazgos y README")
    ap.add_argument("--out", default=None)
    ap.add_argument("--h", nargs="*", default=[], metavar="ID=GRUESA,FINA",
                    help="sobrescribe tamaños de malla, p. ej. P1-STE-01=10,5")
    a = ap.parse_args(argv)
    if a.out is None:   # el modo rápido no pisa el entregable
        a.out = str(HERE / ("resultados_fea_quick.json" if a.quick else "resultados_fea.json"))
    for spec in a.h:
        k, v = spec.split("=")
        CFG[k]["h"] = tuple(float(x) for x in v.split(","))
    if a.readme_only:
        import fea_parts as fp
        res = json.loads(Path(a.out).read_text(encoding="utf-8"))
        _, _, est = fp.load_project()
        for pid, r in res["piezas"].items():
            r.setdefault("pid", pid)
            postprocess(r, r["admisibles"], r["nivel_reportado"] == "gruesa", est)
        res["hallazgos"] = findings(res)
        Path(a.out).write_text(json.dumps(_j(res), indent=1, ensure_ascii=False), encoding="utf-8")
        write_readme(res)
        return 0
    t0 = time.time()
    pids = [x for x in ORDER if not a.only or x in a.only]
    img_dir = None if (a.no_img or a.quick) else HERE / "img"
    results = {}
    if a.serial or len(pids) == 1:
        for pid in pids:
            k, v = run_part(pid, a.quick, a.no_img or a.quick, img_dir, None, CFG[pid])
            results[k] = v
    else:
        with ProcessPoolExecutor(max_workers=min(a.jobs, len(pids)), mp_context=get_context("spawn")) as ex:
            futs = [ex.submit(run_part, pid, a.quick, a.no_img or a.quick, img_dir, None, CFG[pid]) for pid in pids]
            for f in futs:
                k, v = f.result()
                results[k] = v
    import fea_parts as fp
    p, _, _ = fp.load_project()
    if a.merge and not a.quick and Path(a.out).exists():
        res = json.loads(Path(a.out).read_text(encoding="utf-8"))
        res["piezas"].update({pid: _j(results[pid]) for pid in pids})
        res["piezas"] = {k: res["piezas"][k] for k in ORDER if k in res["piezas"]}
        res["meta"]["fecha"] = datetime.date.today().isoformat()
        res["meta"]["inputs_version"] = p.inp["meta"]["version"]
        res["meta"]["tiempo_total_s"] = round(sum(r.get("tiempo_s", 0) for r in res["piezas"].values()), 1)
        res["hallazgos"] = findings(res)
        res = _j(res)
        Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        write_readme(res)
        print(f"\nFEA: {', '.join(pids)} combinadas en {a.out}")
        return 0
    res = {"meta": {"fecha": datetime.date.today().isoformat(), "inputs_version": p.inp["meta"]["version"],
                    "metodo": "gmsh (STEP/OCC, optimización Netgen) → tetraedros; elasticidad lineal P2 (10 nodos), "
                              "isotrópico; PCG + precondicionador P2→P1; contacto unilateral por conjunto activo",
                    "quick": a.quick, "tiempo_total_s": round(time.time() - t0, 1)},
           "piezas": {pid: results[pid] for pid in pids}}
    res["hallazgos"] = findings(res) if not a.quick else []
    res = _j(res)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    if not a.quick and not a.only:
        write_readme(res)
    print(f"\nFEA: {len(pids)} piezas en {time.time() - t0:.0f} s → {a.out}")
    for pid in pids:
        r = res["piezas"][pid]
        print(f"  {pid}: FS mín {r['FS_min']:.2f} (objetivo {r['FS_objetivo']:.0f}; caso {r['caso_gobernante']}, "
              f"{r['criterio_gobernante']}) {'OK' if r['cumple'] else 'BAJO OBJETIVO'}")
        lv = r["nivel_reportado"]
        for cid, c in r["casos"].items():
            fs = c["FS"]
            at = (c["FS_bordes"][fs["borde"]]["at_mm"] if fs["criterio"] == "borde"
                  else fs.get("ubicacion_mm", {}).get("vm") or c[lv]["resumen"]["vm"]["at_max_excl_mm"])
            bt = ", ".join(f"{hn} {b['FS']:.2f}" for hn, b in (c.get("FS_bordes") or {}).items())
            print(f"    {cid} [{'diseño' if c.get('diseno', True) else 'info'}, {c['tipo']}]: FS {fs['gobernante']:.2f} "
                  f"({fs['criterio']}{'' if fs['criterio'] != 'borde' else ' ' + fs['borde']}) en {at}; cuerpo "
                  f"{fs['gobernante_cuerpo']:.2f}; bordes: {bt or '—'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
