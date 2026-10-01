#!/usr/bin/env python3
"""fea_run.py — FEA lineal elástico de las 3 piezas impresas más críticas de P1.

    P1-MNT-01  abrazadera de popa en C         (a) apriete sostenido · (b±) impacto en el buje + apriete
    P1-MNT-05  cuna basculante (+ tapa MNT-06, tubo rígido, tope de marcha)   cola trabada contra el tope
    P1-MNT-04  mejilla de horquilla             (a±) 0,5·H en el perno · (b) lateral 200 N · (c±) combinado

Geometría: build(p) de cada módulo de pieza (marco natural) → STEP temporal → gmsh (tetraedros)
→ P2 (fea_core). Cargas: resultados/estructural.json ("loads") + inputs.yaml. Malla gruesa y fina
(estudio de convergencia). Salidas: 04_diseno/fea/resultados_fea.json, img/*.png y el bloque AUTO
de 04_diseno/fea/README.md.

Uso:  python 04_diseno/fea/fea_run.py [--only P1-MNT-04 ...] [--quick] [--serial] [--no-img] [--out RUTA]
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
    "P1-MNT-01": {"h": (14.0, 7.0), "curv": (6, 12), "hmin": 1.5},
    "P1-MNT-05": {"h": (14.0, 8.0), "curv": (5, 9), "hmin": 2.0},
    "P1-MNT-04": {"h": (6.0, 3.0), "curv": (6, 12), "hmin": 1.0},
}
ORDER = ["P1-MNT-01", "P1-MNT-05", "P1-MNT-04"]
VIEWS = {"P1-MNT-01": ((22, -58), (-32, 125)), "P1-MNT-05": ((20, -60), (-28, 115)),
         "P1-MNT-06": ((-38, -62), (-30, 118)), "P1-MNT-04": ((18, -75), (18, 105))}   # (elevación, azimut)
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
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float):
        return round(o, 6) if np.isfinite(o) else None
    return o


def _r(x, n=3):
    return None if x is None else float(round(x, n))


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
    S = A["S_short"] if kind == "short" else A["S_sust"]
    SZ = A["SZ_short"] if kind == "short" else A["SZ_sust"]
    eps = 1e-9

    def fs(Sa, s):
        return float(Sa / s) if s > eps else 999.0
    out = {"S_XY_MPa": S, "S_Z_MPa": SZ,
           "vm": fs(S, summ["vm"]["max_excl"]), "s1": fs(S, summ["s1"]["max_excl"]), "Z": fs(SZ, summ["sZ"]["max_excl"]),
           "vm_max_global": fs(S, summ["vm"]["max"]), "vm_p99": fs(S, summ["vm"]["p99"]),
           "s1_max_global": fs(S, summ["s1"]["max"]), "Z_max_global": fs(SZ, summ["sZ"]["max"])}
    crit = min(("vm", "s1", "Z"), key=lambda k: out[k])
    out["gobernante"] = out[crit]
    out["criterio"] = crit
    return out


def run_part(pid, quick=False, no_img=False, img_dir=None, log_prefix=None, cfg=None):
    import fea_parts as fp
    from fea_model import mesh_quality
    t0 = time.time()
    pre = log_prefix or pid

    def log(msg):
        print(f"[{pre}] {msg}", flush=True)
    p, mods, est = fp.load_project()
    A = fp.allowables(p.inp)
    cfg = cfg or CFG[pid]
    levels = [("gruesa", cfg["h"][0], cfg["curv"][0])]
    if not quick:
        levels.append(("fina", cfg["h"][1], cfg["curv"][1]))
    h_ref = levels[-1][1]
    r_ex = max(R_EX_MIN, h_ref)
    meta = mods[pid].META
    out = {"descripcion": meta["desc"], "material": meta["material"], "print_rot": list(meta["print_rot"]),
           "dir_Z_impresion_marco_pieza": fp.print_z_dir(meta).round(4).tolist(), "frame": meta["frame"],
           "mallas": {}, "casos": {}, "r_exclusion_mm": r_ex, "admisibles": A}
    prev_active, last = None, None
    for level, h, cn in levels:
        tl = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            st = fp.SETUPS[pid](p, mods, est, h, cn, tmp, log=log, hmin=cfg["hmin"])
        M = st["model"]
        S = M.S
        q = mesh_quality(S.X, S.T)
        bodies = st.get("bodies", [pid])
        nb = np.zeros(len(S.T), int) if S.body is None else S.body
        out["mallas"][level] = {"h_mm": h, "curv_n": cn, "h_min_mm": cfg["hmin"], "n_tets": int(len(S.T)),
                                "n_tets_por_cuerpo": {b: int((nb == i).sum()) for i, b in enumerate(bodies)},
                                "n_nodos_vertice": int(S.N), "n_nodos_P2": int(S.nnodes), "n_gdl": int(S.ndof),
                                "calidad_gamma_min": float(q.min()), "calidad_gamma_p01": float(np.percentile(q, 1)),
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
            summ = {b: M.summarize(F, r_ex, body=i, extra_zones=c.get("zones_extra", ())) for i, b in enumerate(bodies)}
            reac = M.interface_forces(c["u"]) if M.interfaces else {}
            info = c.get("info", {})
            rec = out["casos"].setdefault(c["id"], {"nombre": c["name"], "tipo": c["kind"]})
            rec[level] = {"resumen": summ, "reacciones": reac, "extra": c.get("extra", {}),
                          "solver": {k: info.get(k) for k in ("contact_iters", "contact_changes", "cg_total", "case_s",
                                                              "converged_contact", "residual_changes_accepted", "rel_res",
                                                              "superposicion") if k in info}}
            fields_keep[c["id"]] = {"vm": F["vm"], "sZ": F["sZ"], "u": F["u"]}
        out["verificacion_mano"] = st["checks"]
        out["calculo_a_mano_structural_py"] = st["hand"]
        out["case_hand_map"] = st["case_hand_map"]
        log(f"  {level} listo en {time.time() - tl:.1f} s")
        last = (level, M, fields_keep, bodies)
    # FS, convergencia
    level, M, fields_keep, bodies = last
    fs_min, gov = 1e9, None
    for cid, rec in out["casos"].items():
        rec["FS"] = {b: fs_block(rec[level]["resumen"][b], rec["tipo"], A) for b in bodies}
        if not quick:
            conv = {}
            for b in bodies:
                g, f_ = rec["gruesa"]["resumen"][b], rec["fina"]["resumen"][b]
                conv[b] = {k: {"gruesa": g[a][s_], "fina": f_[a][s_], "dif_rel": (f_[a][s_] - g[a][s_]) / max(abs(f_[a][s_]), 1e-9)}
                           for k, a, s_ in (("vm_p99", "vm", "p99"), ("vm_max_excl", "vm", "max_excl"),
                                            ("vm_max", "vm", "max"), ("s1_max_excl", "s1", "max_excl"))}
                conv[b]["u_max"] = {"gruesa": g["u_max_mm"], "fina": f_["u_max_mm"],
                                    "dif_rel": (f_["u_max_mm"] - g["u_max_mm"]) / max(f_["u_max_mm"], 1e-9)}
            rec["convergencia"] = conv
        fsb = rec["FS"][bodies[0]]["gobernante"]
        if fsb < fs_min:
            fs_min, gov = fsb, cid
    out["FS_min"] = fs_min
    out["caso_gobernante"] = gov
    out["criterio_gobernante"] = out["casos"][gov]["FS"][bodies[0]]["criterio"]
    out["nivel_reportado"] = level
    # imágenes
    imgs = []
    if not no_img and img_dir is not None:
        import fea_plot
        img_dir.mkdir(parents=True, exist_ok=True)
        fk = fields_keep[gov]
        S = M.S
        axl = ("u", "w", "v") if out["frame"] == "unit" else ("x", "y", "z")
        nm = out["casos"][gov]["nombre"]
        for i, b in enumerate(bodies):
            summ = out["casos"][gov][level]["resumen"][b]
            views = VIEWS.get(b, ((22, -58), (22, 122)))
            path = img_dir / f"{b}_vm.png"
            fea_plot.stress_figure(S, fk["vm"], f"{b} — von Mises, caso {gov}: {nm}\nmáx. fuera de zonas de carga "
                                   f"{summ['vm']['max_excl']:.1f} MPa · p99 {summ['vm']['p99']:.1f} MPa · máx. global "
                                   f"{summ['vm']['max']:.1f} MPa (escala recortada al p99,5)",
                                   path, body=i if len(bodies) > 1 else None, views=views, label="σ von Mises [MPa]",
                                   mark=summ["vm"]["at_max_mm"], axis_labels=axl)
            imgs.append(str(path.relative_to(ROOT)))
            path = img_dir / f"{b}_sZ.png"
            fea_plot.stress_figure(S, fk["sZ"], f"{b} — σ normal a las capas (Z de impresión), caso {gov}\n"
                                   f"máx. tracción fuera de zonas {summ['sZ']['max_excl']:.2f} MPa · admisible "
                                   f"{out['casos'][gov]['FS'][b]['S_Z_MPa']:.1f} MPa",
                                   path, body=i if len(bodies) > 1 else None, views=views, diverging=True,
                                   label="σ_Z [MPa] (+ tracción entre capas)", axis_labels=axl)
            imgs.append(str(path.relative_to(ROOT)))
        # deformada del caso gobernante (pieza principal)
        u = fk["u"]
        um = np.linalg.norm(u, axis=1).max()
        size = np.ptp(S.X, axis=0).max()
        scale = 0.08 * size / max(um, 1e-9)
        path = img_dir / f"{bodies[0]}_deformada.png"
        fea_plot.stress_figure(S, np.linalg.norm(u, axis=1), f"{bodies[0]} — desplazamiento, caso {gov} "
                               f"(deformada ×{scale:.1f}; máx. {um:.3f} mm)", path,
                               body=0 if len(bodies) > 1 else None, views=VIEWS.get(bodies[0], ((22, -58),))[:1],
                               label="|u| [mm]",
                               deform=u, scale=scale, axis_labels=axl)
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


def readme_block(res):
    L = [AUTO0, "", f"Corrida: {res['meta']['fecha']} · inputs v{res['meta']['inputs_version']} · "
         f"{res['meta']['tiempo_total_s']:.0f} s · admisibles vigentes: S_corta = {res['meta']['admisibles']['S_short']:.2f} MPa, "
         f"S_sost = {res['meta']['admisibles']['S_sust']:.2f} MPa, S_Z corta/sost = {res['meta']['admisibles']['SZ_short']:.2f}/"
         f"{res['meta']['admisibles']['SZ_sust']:.2f} MPa [CALCULADO]", ""]
    L += ["### Orientación de impresión (anisotropía)", "", "| Pieza | print_rot (META) | Z de impresión en el marco de la pieza | Marco |",
          "|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        L.append(f"| {pid} | {tuple(r['print_rot'])} | {tuple(round(x, 3) + 0.0 for x in r['dir_Z_impresion_marco_pieza'])} | {r['frame']} |")
    L += ["", "### Mallas", "", "| Pieza | Malla | h [mm] | Tetraedros | gdl (P2) | γ mín | γ p1 |", "|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for lv, m in r["mallas"].items():
            L.append(f"| {pid} | {lv} | {m['h_mm']:.0f} | {m['n_tets']} | {m['n_gdl']} | {m['calidad_gamma_min']:.3f} | {m['calidad_gamma_p01']:.3f} |")
    L += ["", "### Resultados (malla fina) — tensiones en MPa, FS = admisible / tensión (máx. fuera de zonas de carga)", "",
          "| Pieza | Caso | Tipo | σvm máx | σvm p99 | σvm máx* | σ1 máx* | σZ máx* | u máx [mm] | FS vm | FS σ1 | FS Z | **FS** |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        lv = r["nivel_reportado"]
        for cid, c in r["casos"].items():
            for b, s in c[lv]["resumen"].items():
                fs = c["FS"][b]
                L.append(f"| {b} | {cid}: {c['nombre']} | {'corta' if c['tipo'] == 'short' else 'sostenida'} | "
                         f"{_f(s['vm']['max'])} | {_f(s['vm']['p99'])} | {_f(s['vm']['max_excl'])} | {_f(s['s1']['max_excl'])} | "
                         f"{_f(s['sZ']['max_excl'])} | {_f(s['u_max_mm'], 3)} | {_f(fs['vm'])} | {_f(fs['s1'])} | {_f(fs['Z'])} | "
                         f"**{_f(fs['gobernante'])}** |")
    L += ["", "\\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (radio de exclusión en la tabla de "
          "convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.", ""]
    L += ["### Convergencia (gruesa → fina, pieza principal)", "",
          "| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] |", "|---|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for cid, c in r["casos"].items():
            cv = c.get("convergencia", {}).get(pid)
            if not cv:
                continue

            def cell(k, n=2):
                v = cv[k]
                return f"{_f(v['gruesa'], n)} → {_f(v['fina'], n)} ({100 * v['dif_rel']:+.0f} %)"
            L.append(f"| {pid} | {cid} | {r['r_exclusion_mm']:.0f} | {cell('vm_p99')} | {cell('vm_max_excl')} | {cell('vm_max')} | {cell('u_max', 3)} |")
    L += ["", "### Comparación con el cálculo a mano (resultados/estructural.json, structural.py)", "",
          "| Pieza (FEA) | Caso FEA | FS FEA | Fila structural.py (pieza) | σ mano [MPa] | FS mano |", "|---|---|---|---|---|---|"]
    for pid, r in res["piezas"].items():
        for cid, c in r["casos"].items():
            key = r["case_hand_map"].get(cid, "")
            rows = [h for h in r["calculo_a_mano_structural_py"] if key.lower() in h["load_case"].lower()] if key else []
            for h in rows[:3] or [{"part": pid, "load_case": "—", "sigma_MPa": None, "FS": None}]:
                b = h.get("part", pid) if h.get("part") in c["FS"] else pid
                L.append(f"| {b} | {cid} | {_f(c['FS'][b]['gobernante'])} | {h['load_case']} ({h.get('part', pid)}) | "
                         f"{_f(h['sigma_MPa'])} | {_f(h['FS'])} |")
    L += ["", "### Hallazgos cuantitativos", ""] + res["hallazgos"] + ["", AUTO1]
    return "\n".join(L)


def findings(res):
    H = []
    A = res["meta"]["admisibles"]
    target = A["fs_target"]
    r1 = res["piezas"].get("P1-MNT-01")
    if r1:
        ck = r1["verificacion_mano"]
        lv = r1["nivel_reportado"]
        a = r1["casos"]["a"]
        s = a[lv]["resumen"]["P1-MNT-01"]
        # espesor de puente necesario (fórmula de viga verificada por el FEA) para FS objetivo a creep
        F2 = 2 * ck["F_tornillo_N"]
        zs = abs(ck["z_tornillos_mm"][0])
        t_req = None
        for t in np.arange(8, 80, 0.5):
            if F2 * (zs + t / 2) / (ck["ancho_abrazadera_mm"] * t * t / 6) <= A["S_sust"] / target:
                t_req = t
                break
        hand = [h for h in r1["calculo_a_mano_structural_py"] if "apriete (sostenido)" in h["load_case"].lower()]
        H.append(f"- **P1-MNT-01 — el puente de la C gobierna.** Apriete sostenido: σvm p99 = {s['vm']['p99']:.1f} MPa en el "
                 f"puente de {ck['puente_espesor_mm']:.0f} mm (la viga a mano con esa sección da {ck['sigma_puente_mano_MPa']:.1f} MPa, "
                 f"coincide) contra S_sost = {A['S_sust']:.2f} MPa → **FS = {a['FS']['P1-MNT-01']['gobernante']:.2f}** "
                 f"(objetivo {target:.0f}). structural.py informa σ = {_f(hand[0]['sigma_MPa'] if hand else None)} MPa porque usa "
                 f"Z = b·leg_t²/6 de la pata (t = leg_t) y no la del puente. La C se abre {s['u_max_mm']:.1f} mm en el pie de la "
                 f"pata interior (análisis lineal: indica flexibilidad excesiva, no un valor exacto). Con el apriete actual el "
                 f"puente necesita t ≥ {t_req if t_req else '>80'} mm [CALCULADO: viga, verificada por FEA] o bajar el brazo/apriete. "
                 f"Además la pieza se imprime con el ancho (y) como Z: la flexión de placa ancha genera σZ ≈ ν·σx = "
                 f"{s['sZ']['max_excl']:.1f} MPa a través de capas contra S_Z,sost = {A['SZ_sust']:.2f} MPa.")
    r5 = res["piezas"].get("P1-MNT-05")
    if r5:
        ck = r5["verificacion_mano"]
        lv = r5["nivel_reportado"]
        c = r5["casos"]["a"][lv]
        ft = c["reacciones"].get("tope_marcha", {}).get("F_abs_N")
        fp_ = c["reacciones"].get("perno_pivote", {}).get("F_abs_N")
        s6 = c["resumen"].get("P1-MNT-06")
        fs6 = r5["casos"]["a"]["FS"].get("P1-MNT-06", {}).get("gobernante")
        H.append(f"- **P1-MNT-05/06 — brazo del tope de marcha.** El tornillo de trimado es vertical y apoya en la cara "
                 f"inferior de la tapa, inclinada θ: sin fricción la reacción es normal a esa cara y su brazo respecto del "
                 f"pivote es u = {ck['brazo_tope_real_mm']:.0f} mm, no hypot(30, v_bot) = {ck['brazo_tope_structural_py_mm']:.0f} mm "
                 f"como en structural.py. Con la cola trabada, el FEA da F_tope = {ft or 0:.0f} N (estática con el centro del tope: "
                 f"{ck['F_tope_estatica_N']:.0f} N) y F_pivote = {fp_ or 0:.0f} N. La cuna (MNT-05) queda con FS = {r5['FS_min']:.2f}; la **tapa MNT-06** recibe el tope "
                 f"en un Ø{2 * ck['r_tope_mm']:.0f} y su FS es {_f(fs6)} "
                 f"(σvm máx. {_f(s6['vm']['max'] if s6 else None, 1)} MPa, compresión entre tope y tubo; presión media en el tope "
                 f"F/A = {(ft or 0) / (np.pi * ck['r_tope_mm'] ** 2):.1f} MPa contra S_corta = {A['S_short']:.1f} MPa). En marcha normal "
                 f"el mismo brazo multiplica por {ck['brazo_tope_structural_py_mm'] / ck['brazo_tope_real_mm']:.1f} la fuerza sostenida "
                 f"del tope respecto de structural.py.")
    r4 = res["piezas"].get("P1-MNT-04")
    if r4:
        lv = r4["nivel_reportado"]
        gid = r4["caso_gobernante"]
        g = r4["casos"][gid]
        sg = g[lv]["resumen"]["P1-MNT-04"]
        crit = {"vm": "vm", "s1": "s1", "Z": "sZ"}[r4["criterio_gobernante"]]
        cb = r4["casos"]["b50"][lv]["resumen"]["P1-MNT-04"]
        ck = r4["verificacion_mano"]
        cv = g.get("convergencia", {}).get("P1-MNT-04", {})
        dmax = cv.get("s1_max_excl" if crit == "s1" else "vm_max_excl", {}).get("dif_rel")
        hand = [h for h in r4["calculo_a_mano_structural_py"] if "lateral" in h["load_case"].lower()]
        H.append(f"- **P1-MNT-04 — ranuras pasantes de las tuercas M6 en la raíz.** FS gobernante {r4['FS_min']:.2f} "
                 f"(caso {gid}: {g['nombre']}; criterio {r4['criterio_gobernante']}) con el máximo en "
                 f"{tuple(sg[crit]['at_max_excl_mm'])} mm: esquina viva de la ranura/raíz, singular (cambia "
                 f"{100 * dmax if dmax is not None else 0:+.0f} % al refinar), mientras el p99 converge; con el p99 el FS es "
                 f"{g['FS']['P1-MNT-04']['vm_p99']:.2f}. Con el reparto de structural.py (100 N por mejilla) σvm máx* = "
                 f"{cb['vm']['max_excl']:.1f} MPa contra {_f(hand[0]['sigma_MPa'] if hand else None)} MPa a mano (Z = L·t²/6 con L = 64 mm "
                 f"no descuenta las dos ranuras de {ck.get('ancho_ranura_mm', 10.4):.1f} mm ni la concentración en sus esquinas).")
    return H


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--serial", action="store_true")
    ap.add_argument("--no-img", action="store_true")
    ap.add_argument("--out", default=str(HERE / "resultados_fea.json"))
    ap.add_argument("--h", nargs="*", default=[], metavar="ID=GRUESA,FINA",
                    help="sobrescribe tamaños de malla, p. ej. P1-MNT-05=10,6")
    a = ap.parse_args(argv)
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
        with ProcessPoolExecutor(max_workers=min(3, len(pids)), mp_context=get_context("spawn")) as ex:
            futs = [ex.submit(run_part, pid, a.quick, a.no_img or a.quick, img_dir, None, CFG[pid]) for pid in pids]
            for f in futs:
                k, v = f.result()
                results[k] = v
    import fea_parts as fp
    p, _, _ = fp.load_project()
    res = {"meta": {"fecha": datetime.date.today().isoformat(), "inputs_version": p.inp["meta"]["version"],
                    "metodo": "gmsh (STEP/OCC) → tetraedros; elasticidad lineal P2 (10 nodos), isotrópico equivalente; "
                              "PCG + precondicionador P2→P1; contacto unilateral por conjunto activo",
                    "material": {"E_MPa": fp.allowables(p.inp)["E"], "nu": fp.NU_PETG},
                    "admisibles": fp.allowables(p.inp), "quick": a.quick,
                    "tiempo_total_s": round(time.time() - t0, 1)},
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
        print(f"  {pid}: FS mín {r['FS_min']:.2f} (caso {r['caso_gobernante']}, {r['criterio_gobernante']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
