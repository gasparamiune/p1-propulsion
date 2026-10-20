"""Probe the J-FD01 screw paths through FD-01 and TC-02 (v3.5.2 tree, unchanged J-FD01): material along each screw axis."""
import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import numpy as np, cadquery as cq
import config, build
P, S, reg, clog = build.build(include=("engine", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
st = S["e1m"]
out = {"z_scr": st["z_scr"], "zb": st["zb"], "z_f": st["z_f"], "parts": {}}
names = [pn for pn in reg.parts if pn.startswith("ENG-FD-0") or pn in ("ENG-TC-02",)]
for pn in names:
    p = reg.parts[pn]
    for inst_i, (T, grp) in enumerate(p.instances if hasattr(p, "instances") else []):
        pass
for pn in ("ENG-FD-01", "ENG-TC-02", "ENG-FD-03", "ENG-FD-05"):
    if pn not in reg.parts:
        continue
    p = reg.parts[pn]
    # global shape (placed instance 0)
    try:
        sh = build.posed_instances(reg, S, 0.0, 0.0, groups=None)
    except Exception:
        sh = None
    out["parts"][pn] = {}
inst = build.posed_instances(reg, S, 0.0, 0.0)
for (pn, idx, grp, shp, body) in inst:
    if pn not in ("ENG-FD-01", "ENG-TC-02", "ENG-FD-03", "ENG-FD-05", "ENG-FD-02"):
        continue
    rec = {}
    for zs in st["z_scr"]:
        prof = []
        for r in np.arange(20.0, 50.01, 0.25):
            pt = cq.Vector(-r, 0.0, zs)
            prof.append(1 if shp.isInside(pt, 1e-4) else 0)
        # runs of material
        runs, cur, r0 = [], None, None
        rr = list(np.arange(20.0, 50.01, 0.25))
        for r, f in zip(rr, prof):
            if f and cur is None:
                cur = r
            if not f and cur is not None:
                runs.append([round(cur, 2), round(r, 2)]); cur = None
        if cur is not None:
            runs.append([round(cur, 2), 50.0])
        rec[f"z{zs:.2f}"] = runs
    out["parts"][f"{pn}#{idx}"] = rec
print(json.dumps(out, indent=1))
