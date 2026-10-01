#!/usr/bin/env python3
"""build_probetas.py — Construye las probetas P1.x (PENDIENTES_GASPAR §P1) y exporta:

    04_diseno/probetas/step/<ID>_<nombre>.step   (orientación de impresión, apoyada en z = 0)
    04_diseno/probetas/stl/<ID>_<nombre>.stl     (ídem, mm)
    04_diseno/probetas/probetas_manifest.json    (envolvente, masa, horas, manifold, cotas, criterios)

Cada módulo PRB-P1.x_*.py expone build(p, ctx) → [(meta, Part)], checks(p, ctx, parts) y
criterios(p, ctx). Las probetas leen geometría y cargas de params.py, de los módulos de
04_diseno/piezas/ y de resultados/estructural.json (nada copiado a mano).
Verifica: sólido válido, malla cerrada (trimesh: estanca, bobinado consistente, 1 cuerpo, V > 0),
envolvente ≤ printer.envelope_mm, apoyo en z = 0 y las cotas de cada módulo. Exit ≠ 0 si algo falla.
Uso:  python 04_diseno/probetas/build_probetas.py [--only P1.3] [--fast]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _probelib as L  # noqa: E402  (agrega 04_diseno y la raíz al path)

from build123d import Rot, export_step, export_stl  # noqa: E402

import build_all  # noqa: E402
from cadlib import to_print  # noqa: E402

PROFILES = ("estructural", "sellado", "fusible", "cubiertas")


def load_modules():
    mods = []
    for f in sorted(HERE.glob("PRB-*.py")):
        spec = importlib.util.spec_from_file_location(f.stem.replace("-", "_").replace(".", "_"), f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.__file_stem__ = f.stem
        mods.append(m)
    return mods


def mesh_check(path):
    import trimesh
    m = trimesh.load(path, force="mesh")
    bodies = m.split(only_watertight=False)
    return {"watertight": bool(m.is_watertight), "winding_consistent": bool(m.is_winding_consistent),
            "volume_mm3": float(m.volume), "bodies": len(bodies),
            "bounds": [[round(float(v), 3) for v in row] for row in m.bounds]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="ID de probeta o de ensayo (p. ej. P1.3 o P1.1A)")
    ap.add_argument("--fast", action="store_true", help="malla gruesa")
    a = ap.parse_args(argv)
    t_all = time.time()
    ctx = L.load_ctx()
    p = ctx.p
    env = tuple(float(v) for v in p.envelope)
    rho = float(p.inp["materials"]["PETG"]["density_g_cm3"])
    rate = float(p.inp["printer"]["print_rate_g_h"])
    tol, atol = (0.2, 0.3) if a.fast else (0.05, 0.15)
    (HERE / "step").mkdir(exist_ok=True)
    (HERE / "stl").mkdir(exist_ok=True)

    out = {"inputs_version": p.inp["meta"]["version"], "envelope_mm": list(env), "probetas": [], "tests": {},
           "notes": []}
    fails = []
    for m in load_modules():
        test = getattr(m, "TEST", m.__file_stem__)
        if a.only and not (a.only == test or a.only.startswith(test)):
            continue
        t0 = time.time()
        items = m.build(p, ctx)
        parts = {}
        for meta, part in items:
            if a.only and a.only != test and a.only != meta["id"]:
                continue
            assert meta["profile"] in PROFILES, meta
            pp = to_print(part, (0, 0, 0))                      # centrada en XY, apoyada en z = 0
            ang, dims = build_all.min_xy_footprint(pp)
            pp = to_print(Rot(0, 0, ang) * pp, (0, 0, 0))
            parts[meta["id"]] = pp
            stem = f"{meta['id']}_{meta['name']}"
            f_step = HERE / "step" / f"{stem}.step"
            f_stl = HERE / "stl" / f"{stem}.stl"
            export_step(pp, str(f_step))
            export_stl(pp, str(f_stl), tolerance=tol, angular_tolerance=atol)
            mc = mesh_check(f_stl)
            vol = float(pp.volume)
            mass = vol / 1000 * rho * float(meta.get("solid_frac", 1.0))
            bb = pp.bounding_box()
            rec = {**meta, "file_stem": stem, "valid_solid": bool(pp.is_valid), "volume_mm3": round(vol, 1),
                   "print_bbox_mm": [round(x, 2) for x in dims], "print_zrot_deg": ang,
                   "z_min_mm": round(bb.min.Z, 4), "mass_g_each": round(mass, 1),
                   "mass_g_total": round(mass * meta["qty"], 1), "print_hours_each": round(mass / rate, 2),
                   "mesh": mc,
                   "files": [str(f_step.relative_to(L.ROOT)), str(f_stl.relative_to(L.ROOT))]}
            ok_env = all(d <= e + 1e-6 for d, e in zip(dims, env))
            ok_mesh = mc["watertight"] and mc["winding_consistent"] and mc["volume_mm3"] > 0 and mc["bodies"] == 1
            rec["ok_envelope"], rec["ok_manifold"] = ok_env, ok_mesh
            if not (ok_env and ok_mesh and rec["valid_solid"] and abs(bb.min.Z) < 1e-3):
                fails.append(f"{meta['id']}: envolvente={ok_env} manifold={ok_mesh} válido={rec['valid_solid']} "
                             f"zmin={bb.min.Z:.3f}")
            out["probetas"].append(rec)
            print(f"  {stem:38s} {meta['profile']:11s} ×{meta['qty']}  bbox={rec['print_bbox_mm']}  "
                  f"m={mass:6.1f} g  estanca={mc['watertight']} cuerpos={mc['bodies']}")
        if not parts:
            continue
        chk = [build_all.eval_check(c) for c in m.checks(p, ctx, parts)] if hasattr(m, "checks") else []
        crit = m.criterios(p, ctx) if hasattr(m, "criterios") else {}
        out["tests"][test] = {"modulo": m.__file_stem__, "doc": (m.__doc__ or "").strip().split("\n")[0],
                              "checks": chk, "criterios": crit, "build_s": round(time.time() - t0, 1)}
        for c in chk:
            print(f"      [{'OK ' if c['ok'] else 'MAL'}] {c['name']}: {c['value']} {c['op']} {c['ref']}")
            if not c["ok"]:
                fails.append(f"{test}: {c['name']}")

    pr = out["probetas"]
    out["totals"] = {"n_stl": len(pr), "n_impresiones": sum(r["qty"] for r in pr),
                     "mass_g": round(sum(r["mass_g_total"] for r in pr), 0),
                     "hours": round(sum(r["print_hours_each"] * r["qty"] for r in pr), 1),
                     "por_perfil": {k: round(sum(r["mass_g_total"] for r in pr if r["profile"] == k), 0)
                                    for k in PROFILES}}
    out["notes"] = ctx.notes
    out["fails"] = fails
    name = "probetas_manifest.json" if not a.only else "probetas_manifest_partial.json"
    with open(HERE / name, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=float)
    print(f"Probetas: {len(pr)} STL, {out['totals']['n_impresiones']} impresiones, {out['totals']['mass_g']:.0f} g, "
          f"{out['totals']['hours']:.1f} h (a {rate:g} g/h); {time.time() - t_all:.0f} s")
    for n in ctx.notes:
        print("  NOTA:", n)
    if fails:
        print("FALLAS:")
        for f_ in fails:
            print("  -", f_)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
