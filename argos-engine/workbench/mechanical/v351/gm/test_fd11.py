import sys, math
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np, config, build
ov = dict(config.V34_ON); ov["fd11_tab_on_bore"] = True
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=ov)
p = reg.parts["ENG-FD-11"]
print("valid", p.shape.isValid(), "solids", len(p.shape.Solids()), "V", round(p.shape.Volume(), 2))
for pn, i, grp, sh, body in build.posed_instances(reg, S, 0, 0):
    if pn == "ENG-FD-11":
        vs = np.array([v.toTuple() for v in sh.Vertices()])
        mesh = sh.tessellate(0.01, 0.1)[0]
        V = np.array([q.toTuple() for q in mesh])
        print(pn, i, "r_max vertices", round(np.hypot(vs[:, 0], vs[:, 1]).max(), 4), "tess", round(np.hypot(V[:, 0], V[:, 1]).max(), 4))
