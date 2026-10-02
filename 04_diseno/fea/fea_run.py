#!/usr/bin/env python3
"""fea_run.py — FEA lineal elástico de las piezas críticas del waterjet P1-J.

    P1-DRV-03  pórtico de rodamientos (Al 6082 soldado)   (a) Fa a proa + radial · (b) Fa a popa + radial
    P1-REV-01  bucket de reversa (Al 5083 4 mm)            (a) chorro en reversa en la cuchara (traba + pivotes)
    P1-STE-01  boquilla direccional (Al 6061-T6)           (a) F_s en el paso · (b) F_s en la salida ·
                                                            (c) reacciones del bucket · (d) c + a
    P1-INT-02  placa base de la toma (Al 5083 10 mm)       (a) espárragos del pórtico · (b) golpe + presión de cierre
    P1-CTL-02  caja de palancas (PETG)                     (a)/(b) mano apoyada 150 N en dos posiciones

Geometría: build(p) de cada módulo de pieza → STEP temporal → gmsh (tetraedros) → P2 (fea_core).
Cargas: sizing.json + structural_<grupo>.py + resultados/estructural.json. Malla gruesa y fina
(estudio de convergencia). Salidas: 04_diseno/fea/resultados_fea.json, img/*.png y el bloque AUTO
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
    "P1-REV-01": {"h": (6.0, 3.5), "curv": (8, 14), "hmin": 1.5,
                  "variantes": {"V1": {"desc": "traba en ambos brazos (2.º émbolo en −Y), chapa 4 mm", "param": {"traba_doble": True}},
                                "V2": {"desc": "traba en ambos brazos + brazos y cuchara de 6 mm", "param": {"traba_doble": True, "t": 6.0}}}},
    "P1-STE-01": {"h": (8.0, 4.5), "curv": (8, 14), "hmin": 1.2},
    "P1-INT-02": {"h": (14.0, 8.0), "curv": (6, 10), "hmin": 2.0},
    "P1-CTL-02": {"h": (6.0, 3.0), "curv": (8, 14), "hmin": 1.0,
                  "variantes": {"V1": {"desc": "paredes de 5 mm (hoy 3,5)", "param": {"W": 5.0}},
                                "V2": {"desc": "paredes de 5 mm + tapa de 8 mm", "param": {"W": 5.0, "WT": 8.0}}}},
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


def fs_block(summ, kind, A, coarse=None):
    """FS = admisible / σ de diseño. Metal dúctil: von Mises. PETG: σvm, σ1 y σZ (entre capas)."""
    S = A["S_short"] if kind == "short" else A["S_sust"]

    def fs(Sa, s):
        return float(Sa / s) if s is not None and s > 1e-9 else 999.0
    sv, mv, dv = design_sigma(summ, "vm", coarse)
    out = {"S_MPa": S, "vm": fs(S, sv), "sigma_vm_diseno_MPa": sv, "metodo_vm": mv, "dif_conv_vm": dv,
           "vm_max_excl": fs(S, summ["vm"]["max_excl"]), "vm_max_global": fs(S, summ["vm"]["max"]),
           "vm_p99": fs(S, summ["vm"]["p99"]), "vm_vol": fs(S, summ["vm"].get("max_vol"))}
    crits = ["vm"]
    if A["tipo"] == "PETG":
        SZ = A["SZ_short"] if kind == "short" else A["SZ_sust"]
        s1, m1, d1 = design_sigma(summ, "s1", coarse)
        sz, mz, dz = design_sigma(summ, "sZ", coarse)
        out.update({"S_Z_MPa": SZ, "s1": fs(S, s1), "Z": fs(SZ, sz), "sigma_s1_diseno_MPa": s1, "sigma_Z_diseno_MPa": sz,
                    "metodo_s1": m1, "metodo_Z": mz, "dif_conv_s1": d1, "dif_conv_Z": dz,
                    "s1_max_global": fs(S, summ["s1"]["max"]), "Z_max_global": fs(SZ, summ["sZ"]["max"])})
        crits += ["s1", "Z"]
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


def run_part(pid, quick=False, no_img=False, img_dir=None, log_prefix=None, cfg=None):
    import fea_parts as fp
    from fea_model import mesh_quality
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
    out = {"descripcion": meta["desc"], "material": meta["material"], "print_rot": list(meta.get("print_rot", (0, 0, 0))),
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
            summ = M.summarize(F, r_ex, extra_zones=ez)
            regs = M.region_summary(F, r_ex, st.get("regions", {}), extra_zones=ez)
            reac = M.interface_forces(c["u"]) if M.interfaces else {}
            info = c.get("info", {})
            rec = out["casos"].setdefault(c["id"], {"nombre": c["name"], "tipo": c["kind"]})
            rec[level] = {"resumen": summ, "regiones": regs, "reacciones": reac, "extra": c.get("extra", {}),
                          "solver": {k: info.get(k) for k in ("contact_iters", "contact_changes", "cg_total", "case_s",
                                                              "converged_contact", "residual_changes_accepted", "rel_res")
                                     if k in info}}
            fields_keep[c["id"]] = {"vm": F["vm"], "sZ": F["sZ"], "u": F["u"]}
        out["verificacion_mano"] = st["checks"]
        out["comparacion"] = st.get("comparacion", [])
        log(f"  {level} listo en {time.time() - tl:.1f} s")
        last = (level, M, fields_keep)
    level, M, fields_keep = last
    A = out["admisibles"]
    fs_min, gov = 1e9, None
    for cid, rec in out["casos"].items():
        rec["FS"] = fs_block(rec[level]["resumen"], rec["tipo"], A, None if quick else rec["gruesa"]["resumen"])
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
        if fsb < fs_min:
            fs_min, gov = fsb, cid
    out["FS_min"] = fs_min
    out["FS_objetivo"] = A["fs_target"]
    out["cumple"] = bool(fs_min >= A["fs_target"])
    out["caso_gobernante"] = gov
    out["criterio_gobernante"] = out["casos"][gov]["FS"]["criterio"]
    out["nivel_reportado"] = level
    out["comparacion_mano"] = compare(out, level)
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
                                   "casos": vc, "tiempo_s": round(time.time() - tv, 1)}
        log(f"  variante {vname}: FS {min(v['FS']['gobernante'] for v in vc.values()):.2f}")
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


def verdict(fs, target):
    return "—" if fs is None else ("cumple" if fs >= target else "**NO CUMPLE**")


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
          "(«prom.»). En PETG el FS es el menor de σvm, σ1 y σZ (el criterio va entre paréntesis).", "",
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
            if fs["criterio"] == "Z":
                sd_txt = f"σZ {_f(fs['sigma_Z_diseno_MPa'])} ({fs['metodo_Z']})"
            elif fs["criterio"] == "s1":
                sd_txt = f"σ1 {_f(fs['sigma_s1_diseno_MPa'])} ({fs['metodo_s1']})"
            else:
                sd_txt = f"{_f(sd)} ({fs['metodo_vm']})"
            L.append(f"| {pid} | {cid}: {c['nombre']} | {_f(s['vm']['max'])} | {_f(s['vm']['p99'])} | {_f(s['vm']['max_excl'])} | "
                     f"{_f(s['vm'].get('max_vol'))} | {sd_txt} | {_f(s['u_max_mm'], 3)} | **{_f(fs['gobernante'])}**{extra} | "
                     f"{_f(fs['vm_p99'])} | {verdict(fs['gobernante'], r['FS_objetivo'])} |")
    L += ["", "\\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de "
          "convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.", ""]
    L += ["### Convergencia (gruesa → fina)", "",
          "| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] |", "|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for cid, c in r["casos"].items():
            cv = c.get("convergencia")
            if not cv:
                continue

            def cell(k, n=2):
                v = cv[k]
                return f"{_f(v['gruesa'], n)} → {_f(v['fina'], n)} ({100 * v['dif_rel']:+.0f} %)"
            L.append(f"| {pid} | {cid} | {r['r_exclusion_mm']:.0f} | {cell('vm_p99')} | {cell('vm_max_excl')} | {cell('vm_max')} | {cell('u_max', 4)} |")
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
            tgt = res["piezas"][pid]["FS_objetivo"]
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
        k = {"vm": ("vm", "sigma_vm_diseno_MPa", "metodo_vm", "dif_conv_vm"), "s1": ("s1", "sigma_s1_diseno_MPa", "metodo_s1", "dif_conv_s1"),
             "Z": ("sZ", "sigma_Z_diseno_MPa", "metodo_Z", "dif_conv_Z")}[fsg["criterio"]]
        at = s[k[0]]["at_max_excl_mm"] if fsg[k[2]] == "máx*" else s[k[0]]["at_max_vol_mm"]
        conv = "" if fsg.get(k[3]) is None else f", máx* gruesa→fina {100 * fsg[k[3]]:+.0f} %"
        H.append(f"- **{pid}: FS = {r['FS_min']:.2f}** (objetivo {tgt:.0f}, {'cumple' if r['cumple'] else '**NO CUMPLE**'}); "
                 f"caso {r['caso_gobernante']}, criterio {fsg['criterio']}: σ de diseño {fsg[k[1]]:.1f} MPa ({fsg[k[2]]}{conv}) en "
                 f"{tuple(at)} mm; σvm p99 {s['vm']['p99']:.1f} MPa (FS p99 {fsg['vm_p99']:.2f}). {PART_NOTES.get(pid, '')}")
        for c in r["comparacion_mano"]:
            if c["dif_FS_rel"] is not None and abs(c["dif_FS_rel"]) > 0.30:
                H.append(f"  - ⚠ «{c['load_case']}»: FS mano {c['FS_mano_cmp']:.2f} vs FS FEA {c['FS_FEA']:.2f} "
                         f"({100 * c['dif_FS_rel']:+.0f} %). {NOTES.get((pid, c['load_case'][:24]), '')}")
    return H


PART_NOTES = {}   # notas por pieza (ubicación, causa y propuesta), se completan abajo

# Explicaciones de las diferencias > 30 % (clave: (pieza, primeros 24 caracteres de la fila de structural_*.py)).
NOTES = {
    ("P1-DRV-03", "Mejillas: empuje Fa a pu"):
        "La fila solo mira la flexión de la mejilla en su plano por Fa/2 (sección 12 × 150, muy rígida). El FEA pone el "
        "máximo de la mejilla en su unión con el tablero: el tablero cargado por el alojamiento flexiona y arrastra el "
        "borde superior de la mejilla fuera de su plano (marco tablero + mejillas). Mecanismo que la fila no ve; nivel bajo.",
    ("P1-DRV-03", "Tablero: 3 g vertical de"):
        "El máximo está en la unión del alma central (columna tablero–alojamiento) con el tablero: el momento de Fa "
        "excéntrico y el radial entran al tablero por el alma, con concentración en la esquina viva de esa unión; la viga "
        "biapoyada de la fila no la ve. Fila a mano no conservadora, pero el FS sigue sobre 2.",
    ("P1-DRV-03", "Alojamiento Ø47: Fa sobr"):
        "La fila es el corte medio del resalte (τ = Fa/(π·D·t)), un valor nominal; el FEA mide la flexión del resalte como "
        "placa anular (el aro apoya solo entre Da_max y D) y la del alojamiento en su unión con el alma. Ambos lejos del admisible.",
    ("P1-REV-01", "Brazo lateral: flexión ("):
        "Modelo a mano NO conservador. La fila reparte F_b/2 a cada brazo, pero la traba está solo en el brazo +Y: todo el "
        "momento M_h de la cuchara tiene que llegar a ese brazo, y la cuchara (sección abierta de chapa de 4 mm) lo lleva "
        "por torsión. El FEA muestra la cuchara girando (u máx. ≈ 3,6 mm) y el pico en el lóbulo de la traba (flexión fuera "
        "del plano de la chapa junto al agujero, que no converge: crece al refinar). Ver variantes V1/V2.",
    ("P1-REV-01", "Cuchara como viga entre "):
        "Misma causa: la fila trata la cuchara como viga entre brazos con los dos extremos apoyados; con la traba de un "
        "solo lado la cuchara trabaja a torsión (sección abierta) y su borde inferior junto al brazo (soldadura) concentra.",
    ("P1-REV-01", "Chapa de la cuchara: fra"):
        "La franja empotrada (p_dinámica) no incluye la torsión de la cuchara; el FEA (escalado a p_dinámica/q) mide la "
        "tensión total de la chapa, dominada por esa torsión. Con traba en los dos brazos (V1) la cuchara baja a < 10 MPa.",
    ("P1-REV-01", "Pivote: aplastamiento de"):
        "La fila es la presión media F_b/2/(d·L). El FEA promedia σvm en un anillo de 3 mm alrededor de los pivotes, que "
        "además de la presión del buje incluye la flexión del brazo, y las reacciones reales: con la traba tangencial los "
        "pivotes toman ≈ 3,3 kN en total (no F_b/2 = 0,7 kN cada uno).",
    ("P1-REV-01", "Agujero de traba: aplast"):
        "La fila es la presión media de aplastamiento F/(d·t); el FEA promedia σvm en un anillo de 3 mm: por definición "
        "menor que el pico. Coinciden en el orden de magnitud; el pico local (fuera de r_excl) es el que no cumple.",
    ("P1-STE-01", "Flexión del tubo por el "):
        "La fila trata el tubo Ø101 como viga (σ nominal < 1 MPa). En el FEA el máximo de la región del tubo está donde se "
        "le unen la torre y la oreja de pivote superior (entra el par del yugo y la reacción de los pernos): concentración "
        "local que la viga no ve. Nivel bajo (FS > 10).",
    ("P1-STE-01", "Oreja del bucket: flexió"):
        "La fila carga cada oreja con F_b/2 a 52 mm. Con la traba la oreja +Y recibe además la fuerza del émbolo (≈ 2,8 kN "
        "en la rosca M20, a 45 mm del pivote) y el pivote +Y toma más que el −Y; el máximo está en el lóbulo de la traba.",
    ("P1-STE-01", "Oreja de pivote (dentro "):
        "La fila toma F/2 a 12 mm en 25 × 30. En el FEA los pernos de pivote reciben un par (reacciones opuestas en la "
        "mejilla Ø8 y en la rosca M6) porque el bucket empuja muy por encima del eje, y el máximo está en la arista viva "
        "donde la oreja cilíndrica corta el frente esférico (sin radio en el CAD; zona con astillas de malla).",
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
        "y la palma carga el nervio de 6 mm entre las dos ranuras o la tapa angosta junto a la del bucket. Ver σZ: la "
        "flexión de las paredes cruza capas.",
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
        res = json.loads(Path(a.out).read_text(encoding="utf-8"))
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
