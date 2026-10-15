"""Quick check of the v3.5.1 freeze fixes (ring land, FD-01 spot face): validity, common volumes at neutral, FD-01 wall to the passages."""
import sys, json, math, time
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np
import config, build, checks
from geom import cyl, cyl_dir, radial_hole
import parts_inlet
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=config.V351_ON)
inst = {}
for pn, i, grp, shp, body in build.posed_instances(reg, S, 0, 0):
    inst[f"{pn}#{i}"] = shp
out = {"t_build_s": round(time.time() - t0, 1)}
for pn in ("ENG-FD-01", "ENG-GM-03", "ENG-BL-02", "ENG-GM-06"):
    sh = reg.parts[pn].shape
    out[pn] = {"valid": bool(sh.isValid()), "n_solids": len(sh.Solids()), "volume_mm3": round(sh.Volume(), 3)}
for a, b in (("ENG-BL-02#0", "ENG-FD-01#0"), ("ENG-GM-03#0", "ENG-GM-06#0"), ("ENG-GM-03#0", "ENG-GM-06#1")):
    c = inst[a].intersect(inst[b])
    v = sum(s.Volume() for s in c.Solids()) if c.Solids() else 0.0
    d = inst[a].distance(inst[b]) if hasattr(inst[a], "distance") else None
    out[f"{a}|{b}"] = {"common_mm3": round(v, 4)}
# FD-01 wall from the spot-face cutter to the internal 8 mm passages (reconstructed from parts_inlet parameters)
g, st = parts_inlet.E1M, parts_inlet.stations(S)
blk = g["block"]; rs = blk["socket_r"]; d8 = blk["passage_d"]
z0 = st["z_blk0"]
vert = cyl(d8, z0 + blk["socket_depth"] - 0.01, st["z_f"] + d8 / 2.0, -rs, 0.0)
rad = radial_hole(d8, g["az_deg"], st["z_f"], g["flat_r"] - 0.5, 41.0)
ua = np.array([math.sin(math.radians(30.0)), math.cos(math.radians(30.0)), 0.0])
a0 = np.array([-39.0, 8.0, 159.2])
cutter = cyl_dir(11.0, 4.0, tuple(a0), tuple(ua))
seat_disc = cyl_dir(11.0, 0.01, tuple(a0), tuple(ua))
fd = reg.parts["ENG-FD-01"].shape
import cadquery as cq
def dist(s1, s2):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    e = BRepExtrema_DistShapeShape(s1.wrapped, s2.wrapped); e.Perform(); return e.Value()
out["fd01"] = {"z_f": st["z_f"], "socket_r": rs, "passage_d": d8, "flat_r": g["flat_r"],
               "removed_by_spotface_mm3": round(fd.Volume() - 0.0, 3),
               "min_dist_seat_plane_disc_to_vertical_passage_mm": round(dist(seat_disc, vert), 3),
               "min_dist_seat_plane_disc_to_radial_passage_mm": round(dist(seat_disc, rad), 3),
               "M8_axis_material_to_passage_mm": None}
# material along the M8 axis from the seat point inwards until a passage is met
s = 0.0
pts = []
while s < 15.0:
    p = a0 - s * ua
    inside = fd.isInside(cq.Vector(*map(float, p)), 1e-4)
    pts.append(inside)
    if not inside and s > 0.2:
        break
    s += 0.05
out["fd01"]["M8_axis_material_to_passage_mm"] = round(s, 2)
print(json.dumps(out, indent=1))
json.dump(out, open("/home/claude/work/mechanical/v351/hw/fd01_spotface_check.json", "w"), indent=1)
