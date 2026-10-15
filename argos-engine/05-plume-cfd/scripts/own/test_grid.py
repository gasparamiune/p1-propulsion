import sys, time, json, numpy as np
sys.path.insert(0, '/home/claude/work/combustion/cfd/own')
import plume2s as P
J, pts, Rbody = P.load_geometry()
for lev in (0.5, 1.0, 2.0):
    g = P.Grid(pts, Rbody, level=lev)
    print(lev, json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in g.summary().items()}))
