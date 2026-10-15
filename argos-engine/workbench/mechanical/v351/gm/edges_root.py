import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np, config, build
RV = json.loads(sys.argv[1])
ov = dict(config.V34_ON); lv = dict(ov["tvc_lever_v34"]); lv["root_v351"] = RV; ov["tvc_lever_v34"] = lv; ov["gimbal_bearing"] = "HK0808"
P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=False, overrides=ov)
sh = reg.parts["ENG-GM-01"].shape
a_ch = 141.9
ca, sa = math.cos(math.radians(a_ch)), math.sin(math.radians(a_ch))
for e in sh.Edges():
    pts = [e.positionAt(t).toTuple() for t in np.linspace(0, 1, 5)]
    rs = [math.hypot(p[0], p[1]) for p in pts]
    if max(abs(r - 38.5) for r in rs) < 0.2 or (min(rs) < 39.5 and max(p[2] for p in pts) < -12.5 and min(rs) > 37.5):
        yps = [-p[0] * sa + p[1] * ca for p in pts]
        print(e.geomType(), "r", [round(r, 2) for r in rs], "z", [round(p[2], 2) for p in pts], "yp", [round(y, 2) for y in yps])
print(json.dumps(S.get("collar_root_v351_fillets")))
