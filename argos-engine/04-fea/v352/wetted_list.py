import sys
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import config, build, cadquery as cq
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
print("cq has distance:", hasattr(cq.Shape, "distance"))
w = [(p.pn, p.material, p.cots, len(p.placements), [g for _, g in p.placements][:3]) for p in reg if getattr(p, "wetted", "") == "N2O"]
print(len(w))
for x in w: print(x)
print("TC-01/TC-02 wetted:", [(p.pn, p.wetted) for p in reg if p.pn in ("ENG-TC-01", "ENG-TC-02", "ENG-TC-04", "ENG-IG-01")])
