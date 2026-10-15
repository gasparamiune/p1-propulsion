#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - exact-geometry cross-check of the BL-02 bay-wall result (own code).

Reads the author's part STEP ENG-BL-02.step (engine frame, mm, modelled in place), rotates it about the pivot with
R = Rx(alpha) Ry(beta) for the given cone angle / azimuths, tessellates the B-rep with a fine linear deflection (0.002 mm) and
reports the maximum radius sqrt(x^2 + y^2) (wall r 70.0 mm, 1 mm requirement r <= 69.0 mm).  Also checks whether the rotated
solid intersects a solid cylindrical shell r 70.0 .. 75.0 (boolean common volume > 0) as an independent penetration test.
Usage: python -I rm1_bl02_exact.py <BL-02.step> <out_json>
"""
import json
import math
import sys

import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform


def pose(th_deg, phi_deg):
    th, ph = math.radians(th_deg), math.radians(phi_deg)
    b = math.asin(math.sin(th) * math.cos(ph))
    a = math.asin(-math.sin(th) * math.sin(ph) / math.cos(b))
    return a, b


def rotated(shape, a, b):
    # R = Rx(a) Ry(b): apply Ry(b) first, then Rx(a)
    t1 = gp_Trsf()
    t1.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), b)
    t2 = gp_Trsf()
    t2.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), a)
    t = t2.Multiplied(t1)
    return BRepBuilderAPI_Transform(shape, t, True).Shape()


def vol(s):
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, p)
    return p.Mass()


def main():
    step, out = sys.argv[1], sys.argv[2]
    part = cq.importers.importStep(step)
    s0 = part.val().wrapped
    bb = part.val().BoundingBox()
    shell = cq.Workplane("XY").workplane(offset=-50).circle(75.0).circle(70.0).extrude(400).val().wrapped
    res = {"who": "REV-MECH-1", "step": step, "neutral_bbox_mm": [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax],
           "volume_mm3": vol(s0), "cases": []}
    for th in (7.0, 8.0):
        for phi in (135.0, 140.0, 150.0, 155.0, 157.5, 160.0, 170.0, 180.0):
            a, b = pose(th, phi)
            s = rotated(s0, a, b)
            sh = cq.Shape.cast(s)
            vs, _ = sh.tessellate(0.002, 0.05)
            rmax = max(math.hypot(v.x, v.y) for v in vs)
            com = BRepAlgoAPI_Common(s, shell)
            com.Build()
            v_in = vol(com.Shape()) if com.IsDone() else float("nan")
            res["cases"].append({"cone_deg": th, "phi_deg": phi, "alpha_deg": math.degrees(a), "beta_deg": math.degrees(b),
                                 "r_max_mm": rmax, "clearance_to_r70_mm": 70.0 - rmax,
                                 "volume_inside_wall_shell_mm3": v_in})
            print(f"cone {th:g} phi {phi:6.1f} a {math.degrees(a):7.3f} b {math.degrees(b):7.3f} r_max {rmax:8.3f} "
                  f"clearance {70.0 - rmax:+7.3f} mm  volume beyond r70 {v_in:9.3f} mm3")
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
