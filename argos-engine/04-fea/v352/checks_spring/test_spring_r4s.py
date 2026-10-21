"""v3.5.2 J-FWD disc-spring scoping (lead 12:09Z item 4 (iii), 12:52Z item 4): CAD envelope check of a flat (solid) disc spring under the
ISO 7380-1 M5 head, on the rev-4 + d10.5 spot-face build (config.V352_ON, as test_r4s v1).  Paper scoping: no CAD change, no part file
written.
(a) per solid thickness t (0.40, 0.50, 0.52): head envelope cyl d9.5 x 2.85 radially from r_flat + t (head raised by the flat spring) and
    spring envelope cyl d10.0 (OD max, DIN 2093 h12) x t from r_flat, vs every other instance within 3 mm, at neutral and at the four
    combined gimbal extremes (as test_r4s (b)); the minimum to ENG-FD-04 and to every other part.
(b) spring on the TC-01 flat: common volume of the spring envelope with TC-01, centred and offset along the engine axis z and
    tangentially by e = 0.10 / 0.25 / 0.40 / 0.584 mm (0.584 = screw at the 5.5 hole wall 0.337 + spring on the M5 thread 0.247:
    the H12 ID 5.32 max on the 6g major 4.826 min); a non-zero common volume = the spring rim rides on the spot-face pocket wall.
Software checks, not physical validation.  Mechanical, 2026-10-20."""
import sys, json, hashlib, time, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/thermal")
import cadquery as cq
import config, build, checks
from geom import apply, bbox, cyl_dir
OUT = "/home/claude/work/mechanical/v352/checks/test_spring_r4s_v1.json"
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_ON))
out = {"id": "test_spring_r4s", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "method": __doc__.strip(), "t_build_s": round(time.time() - t0, 1)}
sp = S["jfwd_od_spot"]
angs, zb_ = S["screw_angles"], S["bolt_z_fwd"]
rf = sp["r_flat_mm"]
out["spot"] = sp
POSES = ((0.0, 0.0), (-4.96, 4.94), (-4.96, -4.94), (4.96, -4.94), (4.96, 4.94))
OD_SPRING = 10.0
res = {}
for t in (0.40, 0.50, 0.52):
    bodies = []
    for a in angs:
        u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
        bodies.append(("head", a, cyl_dir(9.5, 2.75 + 0.1, tuple(u * (rf + t) + np.array([0.0, 0.0, zb_])), tuple(u))))
        bodies.append(("spring", a, cyl_dir(OD_SPRING, t, tuple(u * rf + np.array([0.0, 0.0, zb_])), tuple(u))))
    pr = {}
    for pose in POSES:
        inst = build.posed_instances(reg, S, pose[0], pose[1])
        Tg = build.group_T("engine", pose[0], pose[1])
        bs_ = [(kind, a, apply(b, Tg)) for kind, a, b in bodies]
        recs = []
        for (pn, i, g, sh, body) in inst:
            if pn == "ENG-TC-01":
                continue
            bsh = bbox(sh)
            for kind, a, b in bs_:
                if not checks.bb_overlap(bbox(b), bsh, 4.0):
                    continue
                dd = checks.min_distance(b, sh)[0]
                if dd < 3.0:
                    recs.append({"body": kind, "az": a, "other": f"{pn}#{i}", "dist_mm": round(dd, 3)})
        recs.sort(key=lambda r: r["dist_mm"])
        fd = [r for r in recs if r["other"].startswith("ENG-FD-04")]
        pr[f"a{pose[0]:+g}_b{pose[1]:+g}"] = {"close_lt_3mm": recs[:30], "min_mm": recs[0]["dist_mm"] if recs else None,
                                             "min_FD04_head_mm": min((r["dist_mm"] for r in fd if r["body"] == "head"), default=None),
                                             "min_FD04_spring_mm": min((r["dist_mm"] for r in fd if r["body"] == "spring"), default=None),
                                             "min_other_than_FD04_mm": min((r["dist_mm"] for r in recs if not r["other"].startswith("ENG-FD-04")), default=None)}
        print("t", t, "pose", pose, pr[f"a{pose[0]:+g}_b{pose[1]:+g}"]["min_FD04_head_mm"], pr[f"a{pose[0]:+g}_b{pose[1]:+g}"]["min_FD04_spring_mm"],
              recs[:3], flush=True)
    res[f"t{t:.2f}"] = {"poses": pr,
                        "min_FD04_all_poses_mm": min(min(x for x in (v["min_FD04_head_mm"], v["min_FD04_spring_mm"]) if x is not None) for v in pr.values()),
                        "min_other_all_poses_mm": min(v["min_other_than_FD04_mm"] for v in pr.values() if v["min_other_than_FD04_mm"] is not None)}
out["envelopes"] = res
# (b) spring on the flat, centred and offset (neutral pose, engine frame; the TC-01 instance at pose 0)
inst0 = build.posed_instances(reg, S, 0.0, 0.0)
tc1 = [x for x in inst0 if x[0] == "ENG-TC-01"][0][3]
off = {}
for a in (162.0, 18.0):
    u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
    tvec = np.array([-math.sin(math.radians(a)), math.cos(math.radians(a)), 0.0])
    for e in (0.0, 0.10, 0.25, 0.40, 0.584):
        for dname, dv in (("z", np.array([0.0, 0.0, 1.0])), ("tangential", tvec)):
            if e == 0.0 and dname == "tangential":
                continue
            b = cyl_dir(OD_SPRING, 0.50, tuple(u * rf + np.array([0.0, 0.0, zb_]) + e * dv), tuple(u))
            v = b.intersect(tc1).Volume()
            off[f"az{a:g}|e{e:.3f}|{dname}"] = round(v, 4)
            print("offset", a, e, dname, round(v, 4), flush=True)
out["spring_on_flat_common_volume_mm3"] = off
out["t_total_s"] = round(time.time() - t0, 1)
s = json.dumps(out, indent=1, default=str)
open(OUT, "w").write(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
