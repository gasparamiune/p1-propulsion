"""v3.5.2 REV 4 CAD check (lead 2026-10-20 05:42Z item 4, 06:05Z item 4, 06:23Z items 2, 3, 6): TC-02 seat-bore entry R0.5 + d14.5 thread
relief at the d10 shoulder, TC-03 thread undercut d12.5 R0.6 + 0.70 x 45 deg / R0.25 top edge + top 0.15 below the shoulder; J-FWD head-seat
option (a) d10.5 OD spot face as a rev-4 parameter (off in V352_ON).
(a) TC-01 / TC-02 / TC-03 rev 4 vs rev 3 (config.V352_REV3_ON) and option (a) (config.V352_R4_JFWD_SPOT): validity, solids, volume / mass,
    STEP round-trip (make_all criterion), material removal only (rev4 - rev3 = 0), bounding box;
(b) TC-02 x TC-03: common volume (the smeared M14x1 overlap r 6.5..7.0, whitelisted) and its z-extent vs the engaged length; common volume
    outside the engaged band (must be 0); min distances of the TC-03 top zone (z >= chamfer start) and top face to TC-02;
(c) TC-02 / TC-03 vs every other instance at neutral with an overlapping bounding box: common volume rev 4 vs rev 3 (no new interference);
(d) option (a): wall at the hole, spot-face depth, J-FWD head envelopes (dk 9.5 x 2.85 from the flat) vs every other instance at neutral.
Software checks, not physical validation.  Mechanical, 2026-10-20."""
import sys, json, hashlib, time, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import cadquery as cq
import config, build, engmat, checks
from geom import apply, bbox, cyl_dir, cyl, box
OUT = "/home/claude/work/mechanical/v352/checks/test_r4_v1.json"
t0 = time.time()
B = {}
for nm, ov in (("rev3", config.V352_REV3_ON), ("rev4", config.V352_ON), ("rev4_spot", config.V352_R4_JFWD_SPOT)):
    t1 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(ov))
    B[nm] = (P, S, reg)
    print(nm, "built", round(time.time() - t1, 1), "s", flush=True)
out = {"id": "test_r4", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "method": __doc__.strip(),
       "t_build_s": round(time.time() - t0, 1)}


def rt(shape, path):
    cq.exporters.export(shape, path)
    imp = cq.importers.importStep(path).val()
    v0 = sum(s.Volume() for s in shape.Solids()); v1 = sum(s.Volume() for s in imp.Solids())
    from make_all import bounds_of
    b0, b1 = bounds_of(shape), bounds_of(imp)
    berr = max(abs(a - b) for a, b in zip(b0, b1))
    ok = imp.isValid() and len(imp.Solids()) == len(shape.Solids()) and abs(v1 - v0) / v0 < 1e-5 and berr < 0.01
    return {"passed": bool(ok), "dV_rel": abs(v1 - v0) / v0, "bbox_err_mm": round(berr, 5), "n_solids": len(imp.Solids()),
            "sha256_16": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]}


def props(p, tag):
    sh = p.shape
    V = sum(s.Volume() for s in sh.Solids())
    rho = engmat.rho(p.material)
    from make_all import bounds_of
    return {"material": p.material, "valid": bool(sh.isValid()), "n_solids": len(sh.Solids()), "volume_mm3": round(V, 3),
            "mass_g": round(V * 1e-9 * rho * 1e3, 3), "bbox_mm": [round(x, 4) for x in bounds_of(sh)],
            "roundtrip": rt(sh, f"/home/claude/work/mechanical/v352/checks/rt352/{p.pn}_{tag}.step")}


out["parts"] = {}
for pn, tags in (("ENG-TC-01", ("rev3", "rev4", "rev4_spot")), ("ENG-TC-02", ("rev3", "rev4")), ("ENG-TC-03", ("rev3", "rev4"))):
    row = {}
    for tg in tags:
        row[tg] = props(B[tg][2].parts[pn], tg)
    a, b = B["rev3"][2].parts[pn].shape, B[tags[-1]][2].parts[pn].shape
    row["removed_mm3"] = round(a.cut(b).Volume(), 4)
    row["added_mm3"] = round(b.cut(a).Volume(), 6)
    row["delta_mass_g"] = round(row[tags[-1]]["mass_g"] - row["rev3"]["mass_g"], 3)
    if pn == "ENG-TC-01":
        row["rev4_vs_rev3_identical_volume"] = abs(row["rev4"]["volume_mm3"] - row["rev3"]["volume_mm3"]) < 1e-3
    out["parts"][pn] = row
    print(pn, json.dumps({k: (v if not isinstance(v, dict) else {kk: v[kk] for kk in ("valid", "volume_mm3", "mass_g")}) for k, v in row.items()}), flush=True)
out["delta_total_rev4_vs_rev3_g"] = round(sum(out["parts"][pn]["rev4"]["mass_g"] - out["parts"][pn]["rev3"]["mass_g"] for pn in out["parts"]), 3)
out["delta_option_a_spot_face_g"] = round(out["parts"]["ENG-TC-01"]["rev4_spot"]["mass_g"] - out["parts"]["ENG-TC-01"]["rev4"]["mass_g"], 3)
S4 = B["rev4"][1]
out["geometry_rev4"] = {k: S4.get(k) for k in ("tc02_r4", "tc03_r4", "tc0203_engagement_mm", "z_ins_top", "tc03_top_z", "tc03_flange_z")}
out["geometry_option_a"] = B["rev4_spot"][1].get("jfwd_od_spot")
# (b) TC-02 x TC-03 (engine-frame instances at neutral)
res_b = {}
for tg in ("rev3", "rev4"):
    P_, S_, reg_ = B[tg]
    I = {f"{pn}#{i}": sh for (pn, i, g, sh, b) in build.posed_instances(reg_, S_, 0.0, 0.0)}
    t2, t3 = I["ENG-TC-02#0"], I["ENG-TC-03#0"]
    com = t2.intersect(t3)
    V = com.Volume()
    bb = bbox(com) if V > 0 else None
    r = {"common_mm3": round(V, 3), "common_bbox": ([round(x, 3) for x in bb] if bb else None)}
    z_fl1 = S_["tc03_flange_z"][1]
    zt = S_["z_ins_top"]
    if tg == "rev4":
        z_ue = z_fl1 + S_["tc03_r4"]["thread_major_from_z_above_flange"]
        z_te = S_["tc02_r4"]["thread_end_z_top"]
        band = cyl(40.0, z_ue - 0.6, z_te + 0.0005)
        r["engaged_band_z"] = [round(z_ue, 4), round(z_te, 4)]
        r["common_outside_engaged_band_mm3"] = round(com.cut(band).Volume(), 6)
        # expected smeared overlap: annulus r 6.5..7.0 over the engaged length + the TC-03 run-out triangle below z_ue (r 6.5..7.0)
        exp = math.pi * (7.0 ** 2 - 6.5 ** 2) * (z_te - z_ue)
        r["expected_annulus_mm3"] = round(exp, 3)
        z_c0 = S_["tc03_top_z"] - S_["tc03_r4"]["chamfer_start_z_below_top"]
        top_zone = t3.intersect(cyl(40.0, z_c0, zt + 1.0))
        d, p1, p2 = checks.min_distance(top_zone, t2)
        r["tc03_top_zone_min_dist_to_tc02_mm"] = {"zone": f"TC-03 z >= chamfer start {z_c0:.4f}", "d": round(d, 4),
                                                   "p_tc03": [round(x, 4) for x in p1], "p_tc02": [round(x, 4) for x in p2],
                                                   "r_p_tc03": round(math.hypot(p1[0], p1[1]), 4), "r_p_tc02": round(math.hypot(p2[0], p2[1]), 4)}
        top_face = t3.intersect(cyl(40.0, S_["tc03_top_z"] - 0.02, zt + 1.0))
        d2, q1, q2 = checks.min_distance(top_face, t2)
        r["tc03_top_face_min_dist_to_tc02_mm"] = {"d": round(d2, 4), "r_p_tc03": round(math.hypot(q1[0], q1[1]), 4), "z_p_tc03": round(q1[2], 4),
                                                   "r_p_tc02": round(math.hypot(q2[0], q2[1]), 4), "z_p_tc02": round(q2[2], 4)}
        ent = t3.intersect(cyl(40.0, z_fl1 + 0.001, z_ue - 0.6))
        d3, e1, e2 = checks.min_distance(ent, t2)
        r["tc03_undercut_zone_min_dist_to_tc02_mm"] = {"zone": f"TC-03 z {z_fl1 + 0.001:.3f}..{z_ue - 0.6:.3f}", "d": round(d3, 4),
                                                        "r_p_tc03": round(math.hypot(e1[0], e1[1]), 4), "z_p_tc03": round(e1[2], 4),
                                                        "r_p_tc02": round(math.hypot(e2[0], e2[1]), 4), "z_p_tc02": round(e2[2], 4)}
    res_b[tg] = r
    print("TC02xTC03", tg, r, flush=True)
out["tc02_tc03"] = res_b
# (c) TC-02 / TC-03 vs all other instances at neutral
res_c = {}
for tg in ("rev3", "rev4"):
    P_, S_, reg_ = B[tg]
    inst = build.posed_instances(reg_, S_, 0.0, 0.0)
    I = {f"{pn}#{i}": sh for (pn, i, g, sh, b) in inst}
    rows = []
    for me in ("ENG-TC-02#0", "ENG-TC-03#0"):
        bm = bbox(I[me])
        for k, sh in I.items():
            if k in ("ENG-TC-02#0", "ENG-TC-03#0") and k <= me:
                continue
            if k == me or not checks.bb_overlap(bm, bbox(sh), 0.5):
                continue
            v_ = I[me].intersect(sh).Volume()
            d_ = checks.min_distance(I[me], sh)[0] if v_ <= 1e-6 else 0.0
            rows.append({"a": me, "b": k, "common_mm3": round(v_, 4), "min_dist_mm": round(d_, 4)})
    res_c[tg] = rows
    print("pairs", tg, len(rows), [r for r in rows if r["common_mm3"] > 1e-4], flush=True)
cmp = []
r3 = {(r["a"], r["b"]): r for r in res_c["rev3"]}
for r in res_c["rev4"]:
    q = r3.get((r["a"], r["b"]))
    cmp.append({"pair": f"{r['a']} x {r['b']}", "rev3_common_mm3": (q["common_mm3"] if q else None), "rev4_common_mm3": r["common_mm3"],
                "rev3_min_dist": (q["min_dist_mm"] if q else None), "rev4_min_dist": r["min_dist_mm"],
                "new_interference": bool(r["common_mm3"] > 1e-4 and (q is None or r["common_mm3"] > q["common_mm3"] + 1e-4))})
out["neighbours_neutral"] = {"rows": cmp, "any_new_interference": any(c["new_interference"] for c in cmp)}
# (d) option (a) heads
P_, S_, reg_ = B["rev4_spot"]
sp = S_["jfwd_od_spot"]
angs = S_["screw_angles"]
zb_ = S_["bolt_z_fwd"]
heads = []
for a in angs:
    u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
    heads.append(cyl_dir(9.5, 2.75 + 0.1, tuple(u * sp["r_flat_mm"] + np.array([0.0, 0.0, zb_])), tuple(u)))
recs = []
for (pn, i, g, sh, body) in build.posed_instances(reg_, S_, 0.0, 0.0):
    if pn == "ENG-TC-01":
        continue
    bs = bbox(sh)
    for k, h in enumerate(heads):
        if not checks.bb_overlap(bbox(h), bs, 4.0):
            continue
        dd = checks.min_distance(h, sh)[0]
        if dd < 3.0:
            recs.append({"head_az": angs[k], "other": f"{pn}#{i}", "dist_mm": round(dd, 3)})
recs.sort(key=lambda r: r["dist_mm"])
tc1 = [x for x in build.posed_instances(reg_, S_, 0.0, 0.0) if x[0] == "ENG-TC-01"][0][3]
seat = [round(h.intersect(tc1).Volume(), 4) for h in heads]
out["option_a_spot_face"] = {"spot": sp, "head_envelope": "cyl d 9.5 x 2.85 radially from the flat r_flat (ISO 7380-1 M5 dk 9.5 / k 2.75 + 0.1)",
                             "head_x_tc01_common_mm3": seat, "close_lt_3mm": recs[:20], "min_mm": (recs[0]["dist_mm"] if recs else None)}
print("option a", out["option_a_spot_face"]["spot"], seat[:3], recs[:5], flush=True)
out["t_total_s"] = round(time.time() - t0, 1)
s = json.dumps(out, indent=1, default=str)
open(OUT, "w").write(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
