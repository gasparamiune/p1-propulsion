"""Localise the v3.5.2 interim interference ENG-BL-03E (bleed common line) x ENG-FD-01 (J-FD01 lower ears) found by clear_interim352 (33.65 mm3),
and print the J-FWD stations (z of the injector face, head bottom, case fwd end, screw row, glands).  Mechanical, 2026-10-20."""
import sys, json
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import config, build, parts_inlet
from geom import bbox
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
inst = {f"{pn}#{i}": sh for (pn, i, g, sh, b) in build.posed_instances(reg, S, 0.0, 0.0)}
a, b = inst["ENG-BL-03E#0"], inst["ENG-FD-01#0"]
c = a.intersect(b)
print("common", round(c.Volume(), 2), "bbox", [round(x, 2) for x in bbox(c)])
print("BL-03E bbox", [round(x, 2) for x in bbox(a)])
print("FD-01 bbox", [round(x, 2) for x in bbox(b)])
st = parts_inlet.stations(S)
print("stations", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in st.items()})
print("J-FWD", {k: S.get(k) for k in ("inj_face", "head_bot", "head_top", "tube_fwd", "bolt_z_fwd", "fwd_glands", "screw_angles", "pc_port")})
bl = S.get("bleed") or {}
print("bleed keys", list(bl.keys())[:30])
for k in ("path_E", "pts_E", "legE", "common_line", "BL-03E"):
    if k in bl:
        print(k, json.dumps(bl[k])[:1500])
