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
    "P1-REV-01": {"h": (6.0, 3.5), "curv": (8, 14), "hmin": 1.5},
    "P1-STE-01": {"h": (8.0, 4.5), "curv": (8, 14), "hmin": 1.2},
    "P1-INT-02": {"h": (14.0, 8.0), "curv": (6, 10), "hmin": 2.0},
    "P1-CTL-02": {"h": (6.0, 3.0), "curv": (8, 14), "hmin": 1.0},
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


def fs_block(summ, kind, A):
    """FS = admisible / tensión. Metal dúctil: von Mises. PETG: σvm, σ1 y σZ (entre capas)."""
    S = A["S_short"] if kind == "short" else A["S_sust"]

    def fs(Sa, s):
        return float(Sa / s) if s > 1e-9 else 999.0
    out = {"S_MPa": S, "vm": fs(S, summ["vm"]["max_excl"]), "vm_max_global": fs(S, summ["vm"]["max"]),
           "vm_p99": fs(S, summ["vm"]["p99"])}
    crits = ["vm"]
    if A["tipo"] == "PETG":
        SZ = A["SZ_short"] if kind == "short" else A["SZ_sust"]
        out.update({"S_Z_MPa": SZ, "s1": fs(S, summ["s1"]["max_excl"]), "Z": fs(SZ, summ["sZ"]["max_excl"]),
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
        s_fea = reg["vm"][met] * c["escala_carga"]
        s_p99 = reg["vm"]["p99"] * c["escala_carga"]
        S = c["S_cmp_MPa"]
        s_hand = None if c["sigma_MPa"] is None else c["sigma_MPa"] * c["k_mano_a_vm"]
        fs_fea = S / s_fea if s_fea > 1e-9 else 999.0
        fs_hand = (S / s_hand) if s_hand else c["FS"]
        dif = (fs_fea - fs_hand) / fs_hand if fs_hand else None
        rows.append({**c, "sigma_FEA_MPa": s_fea, "sigma_FEA_p99_MPa": s_p99, "sigma_mano_vm_MPa": s_hand,
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
        rec["FS"] = fs_block(rec[level]["resumen"], rec["tipo"], A)
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
        top = summ["vm"]["max_excl"] * 1.15
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
    L += ["", "### Resultados (malla fina) — tensiones en MPa, FS = admisible / σvm máx* (máx. fuera de zonas de carga)", "",
          "| Pieza | Caso | σvm máx | σvm p99 | σvm máx* | u máx [mm] | FS (máx*) | FS (p99) | Veredicto |",
          "|---|---|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        lv = r["nivel_reportado"]
        for cid, c in r["casos"].items():
            s = c[lv]["resumen"]
            fs = c["FS"]
            extra = ""
            if fs["criterio"] != "vm":
                extra = f" ({fs['criterio']})"
            L.append(f"| {pid} | {cid}: {c['nombre']} | {_f(s['vm']['max'])} | {_f(s['vm']['p99'])} | {_f(s['vm']['max_excl'])} | "
                     f"{_f(s['u_max_mm'], 3)} | **{_f(fs['gobernante'])}**{extra} | {_f(fs['vm_p99'])} | "
                     f"{verdict(fs['gobernante'], r['FS_objetivo'])} |")
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
            met = {"max_excl": "máx*", "mean": "promedio", "p99": "p99"}[c.get("metrica", "max_excl")]
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
        H.append(f"- **{pid}: FS = {r['FS_min']:.2f}** (objetivo {tgt:.0f}, {'cumple' if r['cumple'] else 'NO CUMPLE'}); "
                 f"caso {r['caso_gobernante']}, σvm máx* = {s['vm']['max_excl']:.1f} MPa en {tuple(s['vm']['at_max_excl_mm'])} mm, "
                 f"p99 {s['vm']['p99']:.1f} MPa (FS p99 {g['FS']['vm_p99']:.2f}).")
        for c in r["comparacion_mano"]:
            if c["dif_FS_rel"] is not None and abs(c["dif_FS_rel"]) > 0.30:
                H.append(f"  - ⚠ «{c['load_case']}»: FS mano {c['FS_mano_cmp']:.2f} vs FS FEA {c['FS_FEA']:.2f} "
                         f"({100 * c['dif_FS_rel']:+.0f} %). {NOTES.get((pid, c['load_case'][:24]), '')}")
    return H


NOTES = {}      # explicaciones de diferencias > 30 % (clave: (pieza, primeros 24 caracteres de la fila))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--serial", action="store_true")
    ap.add_argument("--no-img", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", default=None)
    ap.add_argument("--h", nargs="*", default=[], metavar="ID=GRUESA,FINA",
                    help="sobrescribe tamaños de malla, p. ej. P1-STE-01=10,5")
    a = ap.parse_args(argv)
    if a.out is None:   # el modo rápido no pisa el entregable
        a.out = str(HERE / ("resultados_fea_quick.json" if a.quick else "resultados_fea.json"))
    for spec in a.h:
        k, v = spec.split("=")
        CFG[k]["h"] = tuple(float(x) for x in v.split(","))
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
    res = {"meta": {"fecha": datetime.date.today().isoformat(), "inputs_version": p.inp["meta"]["version"],
                    "metodo": "gmsh (STEP/OCC, optimización Netgen) → tetraedros; elasticidad lineal P2 (10 nodos), "
                              "isotrópico; PCG + precondicionador P2→P1; contacto unilateral por conjunto activo",
                    "quick": a.quick, "tiempo_total_s": round(time.time() - t0, 1)},
           "piezas": {pid: results[pid] for pid in pids}}
    res["hallazgos"] = findings(res) if not a.quick else []
    res = _j(res)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    if not a.quick and not a.only:
        rd = HERE / "README.md"
        txt = rd.read_text(encoding="utf-8") if rd.exists() else "# FEA\n\n" + AUTO0 + "\n" + AUTO1 + "\n"
        if AUTO0 in txt and AUTO1 in txt:
            i0, i1 = txt.index(AUTO0), txt.index(AUTO1) + len(AUTO1)
            txt = txt[:i0] + readme_block(res) + txt[i1:]
        else:
            txt += "\n" + readme_block(res) + "\n"
        rd.write_text(txt, encoding="utf-8")
    print(f"\nFEA: {len(pids)} piezas en {time.time() - t0:.0f} s → {a.out}")
    for pid in pids:
        r = res["piezas"][pid]
        print(f"  {pid}: FS mín {r['FS_min']:.2f} (objetivo {r['FS_objetivo']:.0f}; caso {r['caso_gobernante']}, "
              f"{r['criterio_gobernante']}) {'OK' if r['cumple'] else 'BAJO OBJETIVO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
