"""STEP round-trip of GM-01 (v3.5.1 fillets): original, ShapeFix, and R_side variants."""
import sys, json, copy
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import cadquery as cq
import config, build
def rt(shape, path):
    cq.exporters.export(shape, path)
    imp = cq.importers.importStep(path).val()
    v0 = sum(s.Volume() for s in shape.Solids()); v1 = sum(s.Volume() for s in imp.Solids())
    return round(v0, 3), round(v1, 3), abs(v1 - v0) / v0, imp.isValid(), len(imp.Faces()), len(shape.Faces())
variants = {"orig": dict(config.V351_ON)}
lv = copy.deepcopy(config.V5C_LEVER_V351); lv["root_v351"]["R_side"] = 1.2
variants["Rside1.2"] = dict(config.V351_ON, tvc_lever_v34=lv)
lv2 = copy.deepcopy(config.V5C_LEVER_V351); lv2["root_v351"]["R_side"] = 1.0
variants["Rside1.0"] = dict(config.V351_ON, tvc_lever_v34=lv2)
for nm, ov in variants.items():
    P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=False, overrides=ov)
    for pn in ("ENG-GM-01", "ENG-GM-02"):
        sh = reg.parts[pn].shape
        r = rt(sh, f"/home/claude/work/mechanical/v351/gm/rt/{nm}_{pn}.step")
        fx = sh.fix()
        r2 = rt(fx, f"/home/claude/work/mechanical/v351/gm/rt/{nm}_{pn}_fix.step")
        print(nm, pn, "orig", r, "| fix", r2, "| log", json.dumps(S.get("collar_root_v351_fillets", {}).get(1 if pn.endswith("01") else 2))[:300], flush=True)
