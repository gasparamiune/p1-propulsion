"""v3.5.2 J-FD01: minimum TC-02 (6061-T6) wall from the new M4 taps (at the thread major diameter 4.0) and from the deeper / wider flat
(r 29.5, +/-13; v3.5.1 r 30.5, +/-10) to any OTHER internal cavity of TC-02 (manifold, ports, bores).  Method: probe solids grown by w
around the tap (cylinder d 4.0 + 2w, from 0.2 below the flat to w beyond the drill bottom) and under the flat (slab of depth w over the
flat area); probe.cut(TC-02 + the E1-M cuts that open at the flat) > 0.01 mm3 means another cavity lies within w; w by bisection
(0.05 mm).  Software geometry check, not a strength check.  Mechanical, 2026-10-19."""
import sys, json, math
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import config, build, parts_inlet
from geom import cyl_dir, box, cyl, apply
import cadquery as cq

def run(tag, ov):
    P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=False, overrides=dict(ov))
    p2 = reg.parts["ENG-TC-02"]
    tc = apply(p2.shape, build.group_T("engine", 0.0, 0.0) @ p2.placements[0][0])        # part frame -> engine frame (neutral)
    st = parts_inlet.stations(S)
    g = parts_inlet._g(S)
    cuts = parts_inlet.head_cuts(S)
    fill = cuts[1:]                                     # everything E1-M cuts except the flat box itself
    filled = tc
    for c in fill:
        filled = filled.fuse(c)
    filled = filled.clean()
    R = 31.75 - 0.02                                    # head OD 63.5 (envelope just inside the OD)
    env = cyl(2 * R, st["zb"] + 0.5, st["zt"] - 0.5).intersect(box((-g["flat_r"] + 0.01, -40.0, st["zb"]), (40.0, 40.0, st["zt"])))
    def extra(probe):
        try:
            return probe.intersect(env).cut(filled).Volume()
        except Exception as ex:
            return float("nan")
    def bisect(make, lo=0.0, hi=4.0):
        if extra(make(hi)) <= 0.01:
            return f">{hi}"
        for _ in range(7):
            mid = 0.5 * (lo + hi)
            if extra(make(mid)) > 0.01:
                hi = mid
            else:
                lo = mid
        return round(lo, 3)
    res = {"tag": tag, "flat_r": g["flat_r"], "taps": [], "flat": None}
    if S.get("jfd01_v352"):
        for sc in parts_inlet.JFD01_V352["screws"]:
            z = st["zb"] + sc["z_rel"]
            x0 = -g["flat_r"] + 0.2
            x1 = -g["flat_r"] + sc["tap_depth"]
            mk = lambda w, y=sc["y"], z=z, x0=x0, x1=x1: cyl_dir(4.0 + 2 * w, (x1 + w) - x0, (x0, y, z), (1.0, 0.0, 0.0))
            res["taps"].append({"y": sc["y"], "z": round(z, 3), "tap_depth": sc["tap_depth"], "min_wall_mm_from_major_d4": bisect(mk)})
    hw = parts_inlet.JFD01_V352["flat_half_w_cut"] if S.get("jfd01_v352") else 10.0
    mkf = lambda w: box((-g["flat_r"] + 0.01, -hw, st["z_blk0"]), (-g["flat_r"] + 0.01 + w, hw, st["z_blk1"]))
    res["flat"] = {"half_w": hw, "z": [round(st["z_blk0"], 3), round(st["z_blk1"], 3)], "min_wall_mm_below_flat": bisect(mkf, 0.0, 8.0)}
    res["envelope"] = f"head OD 63.5 (r 31.73) x z [zb+0.5, zt-0.5] = [{st['zb']+0.5:.3f}, {st['zt']-0.5:.3f}] above the flat"
    print(tag, json.dumps(res), flush=True)
    return res

out = {"id": "wall_jfd01", "version": "v1", "date": "2026-10-19", "owner": "mechanical",
       "method": __doc__.strip(), "v352": run("v352", config.V352_ON), "v351": run("v351", config.V351_ON)}
open("/home/claude/work/mechanical/v352/checks/wall_jfd01_v1.json", "w").write(json.dumps(out, indent=1))
print("done")
