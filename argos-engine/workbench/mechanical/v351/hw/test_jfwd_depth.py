"""Can the J-FWD M5 tapped holes in TC-02 be deepened (M5 x 10 screws, >= 6 mm engagement) without breaking into a cavity? v3.5.1 dev."""
import sys, math
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import config, build
from geom import radial_hole
P, S, reg, clog = build.build(include=("engine",), iterate_cg=False, overrides=dict(config.V351_ON))
tc = reg.parts["ENG-TC-02"].shape
plug_r = 57.20 / 2
z = -42.0   # part-local z of the M5 taps (hole census)
print("bolt_z_fwd", z, "angles", S["screw_angles"])
for depth in (8.0, 8.5, 9.0):
    worst = 1e9
    for a in S["screw_angles"]:
        ext = radial_hole(4.2, a, z, plug_r - depth, plug_r - 6.5 + 0.01)       # the extra drilled length
        wall = radial_hole(4.2 + 2.0, a, z, plug_r - depth - 1.0, plug_r - 6.5)  # 1 mm wall around/below it
        v_ext = ext.Volume(); vi = tc.intersect(ext).Volume()
        v_w = wall.Volume(); vwi = tc.intersect(wall).Volume()
        worst = min(worst, vi / v_ext, vwi / v_w)
        if vi / v_ext < 0.999 or vwi / v_w < 0.999:
            print(f"  depth {depth} az {a:.1f}: drilled fraction in metal {vi/v_ext:.4f}, 1 mm wall fraction {vwi/v_w:.4f}")
    print(f"depth {depth}: worst fraction {worst:.4f}")
