"""v3.5.2 REV 5 CAD check, J-FWD (lead 16:53Z R2 / R4 = CHANGELOG 243 (4) / (6); CHANGELOG 241 (6) / (8)), on config.V352_R5.
(a) TC-01 rev-5 J-FWD geometry as built, all 10 flats: flat face area and extents in the screw frame (x' radial, y' tangential, z' axial),
    point probes of the flat, the pocket wall, the tangential run-out and the wall to the 57.25 bore; the 15 deg x 3.5 lead-in (C2).
(b) pocket length against the TC-01 forward features: pocket ends (cutter d11.2 modelled; d11.3 maximum on paper) to the fwd end face (datum
    B), the lead-in end and the seal-land end; min distance flat / pocket wall to the end face; ENG-FD-04 (foil, clips) to the pocket faces
    of every hole (the 162 / 198 deg holes lie in its sector).
(c) head raised by the solid spring (t 0.44 / 0.52; head envelope d9.5 x 2.85 from r_flat + t, spring d10.0 x t on the flat) at the screw-axis
    offset 0 and at the method stack toward FD-04 (-z), against every other instance within 3 mm at neutral and the four combined gimbal
    extremes (as test_spring_r4s v1); TC-01 excluded (the spring sits on it).
(d) flat complete under the spring in the axial direction: common volume of the spring envelope (full disc d10.0 x 0.52, conservative) with
    TC-01 at z offsets 0 / 0.328 / the method stack / 0.547 / 0.557 / 0.60 / 0.62, both signs, at two holes (the CAD corner is sharp: contact
    at 0.60; the drawn corner R <= 0.05 makes the paper tolerable e 0.55).
(e) supported area of the spring annulus (OD 10.0 / ID 5.2) on the flat: the annulus face 0.0005 below the flat intersected with TC-01
    (excludes the hole and the tangential run-out), at tangential and axial offsets, on the CAD nominal TC-01 and on a worst-stack tube built
    here (OD 63.426 centred 0.02 away from the hole side, flat at 31.333 from datum A, cutter d11.2, hole 5.62; the 0.1 OD break is not
    modelled): cross-check of spring v3's seg_area table ('without_break' column) and the bearing fraction with the hole excluded.
(f) TC-02 J-FWD tap walls at the clocking tolerance: probe bisection as test_interim352b v1 at az 18 / 342 / 126 / 162 rotated by +/-0.5 and
    +/-1.0 deg (the taps are match-drilled where the TC-01 holes are, so a clocking error moves them in TC-02's frame).
(g) datum B: TC-02 head shoulder to the TC-01 fwd end face, TC-02 plug end to the TC-01 bore step, the hole row from the end face.
(h) the positional stack on the match-drill method (paper; sourced terms) and the ENG-HW-101-IN718 pilot / undercut drawing values.
Software checks, not physical validation.  Mechanical, 2026-10-20."""
import sys, json, hashlib, time, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import cadquery as cq
import config, build, checks
from geom import apply, bbox, cyl_dir, cyl, radial_hole, revolve, tube, cut_all
from OCP.BRepAdaptor import BRepAdaptor_Surface

OUT = "/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v1.json"
t0 = time.time()
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V352_R5))
out = {"id": "test_rev5_jfwd", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "cad": "v3.5.2 rev 5 (config.V352_R5)",
       "method": __doc__.strip(), "t_build_s": round(time.time() - t0, 1)}
sp = S["jfwd_od_spot"]
angs, zb_ = S["screw_angles"], S["bolt_z_fwd"]
rf, d_cut = sp["r_flat_mm"], sp["d_mm"]
z1 = S["tube_fwd"]
case_R, seal_r, case_r = 31.75, 57.25 / 2.0, 57.15 / 2.0
out["spot"] = sp
out["S"] = {"bolt_z_fwd": zb_, "tube_fwd_z1": z1, "head_bot": S["head_bot"], "inj_face": S["inj_face"], "tc01_leadin_mm": S["tc01_leadin_mm"],
            "screw_angles": angs, "jfwd_tap_drill_mm": S["jfwd_tap_drill_mm"], "jfwd_rev5": S["jfwd_rev5"]}
inst0 = build.posed_instances(reg, S, 0.0, 0.0)
I0 = {f"{pn}#{i}": sh for (pn, i, g, sh, b) in inst0}
Tg0 = build.group_T("engine", 0.0, 0.0)
tc01 = I0["ENG-TC-01#0"]
tc02 = I0["ENG-TC-02#0"]
fd04 = I0["ENG-FD-04#0"]
out["frames"] = {"engine_T_neutral_is_identity": bool(np.allclose(Tg0, np.eye(4)))}
assert np.allclose(Tg0, np.eye(4)), Tg0


def frame(a):
    r = math.radians(a)
    u = np.array([math.cos(r), math.sin(r), 0.0])
    t = np.array([-math.sin(r), math.cos(r), 0.0])
    return u, t, np.array([0.0, 0.0, 1.0])


def pt(a, xp, yp, zp):
    u, t, ez = frame(a)
    return u * xp + t * yp + ez * (zb_ + zp)


def inside(shape, p):
    return bool(shape.isInside(cq.Vector(*[float(c) for c in p]), 1e-5))


def loc(a, p):
    u, t, ez = frame(a)
    p = np.asarray(p, float)
    return float(p @ u), float(p @ t), float(p[2] - zb_)


def edge_pts(face, n=64):
    pts = []
    for e in face.Edges():
        for k in range(n + 1):
            v = e.positionAt(k / n)
            pts.append((v.x, v.y, v.z))
    return pts


# ---------------------------------------------------------------- (a) TC-01 rev-5 geometry as built
flats, probes = {}, {}
faces = tc01.Faces()
for a in angs:
    u, t, ez = frame(a)
    cand = []
    for f in faces:
        if f.geomType() != "PLANE":
            continue
        c = f.Center()
        n = f.normalAt(c)
        xp, yp, zp = loc(a, (c.x, c.y, c.z))
        if abs(abs(n.x * u[0] + n.y * u[1] + n.z * u[2]) - 1.0) < 1e-6 and abs(xp - rf) < 0.01 and abs(yp) < 6 and abs(zp) < 6:
            cand.append(f)
    assert len(cand) == 1, (a, len(cand))
    f = cand[0]
    lp = [loc(a, q) for q in edge_pts(f)]
    xs, ys, zs = [q[0] for q in lp], [q[1] for q in lp], [q[2] for q in lp]
    flats[f"{a:g}"] = {"area_mm2": round(f.Area(), 3), "x_prime_mm": [round(min(xs), 4), round(max(xs), 4)],
                       "y_prime_extent_mm": [round(min(ys), 4), round(max(ys), 4)], "z_prime_extent_mm": [round(min(zs), 4), round(max(zs), 4)]}
    pr = {"flat_below_material_z+-5.55": [inside(tc01, pt(a, rf - 0.01, 0.0, s * 5.55)) for s in (1, -1)],
          "flat_above_air_z+-5.55": [not inside(tc01, pt(a, rf + 0.01, 0.0, s * 5.55)) for s in (1, -1)],
          "pocket_wall_material_z+-5.62_x'+0.2": [inside(tc01, pt(a, rf + 0.2, 0.0, s * 5.62)) for s in (1, -1)],
          "pocket_air_z+-5.58_x'+0.2": [not inside(tc01, pt(a, rf + 0.2, 0.0, s * 5.58)) for s in (1, -1)],
          "tangential_runout_air_y+-5.30_on_flat": [not inside(tc01, pt(a, rf + 0.002, s * 5.30, 0.0)) for s in (1, -1)],
          "wall_bore_side_air_x'=seal_r-0.01_at_z'4": not inside(tc01, pt(a, seal_r - 0.01, 0.0, 4.0)),
          "wall_material_x'=seal_r+0.01_at_z'4": inside(tc01, pt(a, seal_r + 0.01, 0.0, 4.0)),
          "wall_material_x'=r_flat-0.01_at_z'4": inside(tc01, pt(a, rf - 0.01, 0.0, 4.0)),
          "hole_air_at_axis_mid_wall": not inside(tc01, pt(a, 0.5 * (rf + seal_r), 0.0, 0.0)),
          "hole_wall_material_r2.80_mid_wall": inside(tc01, pt(a, 0.5 * (rf + seal_r), 0.0, 2.80))}
    probes[f"{a:g}"] = pr
allp = all(all(v) if isinstance(v, list) else v for pr in probes.values() for v in pr.values())
A_flat_paper = math.pi * 5.6 ** 2 - 2 * (5.6 ** 2 * math.acos(sp["half_chord_on_OD_mm"] / 5.6) - sp["half_chord_on_OD_mm"]
                                          * math.sqrt(5.6 ** 2 - sp["half_chord_on_OD_mm"] ** 2)) - math.pi / 4 * 5.5 ** 2
# lead-in C2: at z1 - 1.0 the 3.5 chamfer is at seal_r + 2.5 tan15 = +0.670 (the 3.0 one at +0.536); below z1 - 3.5 the bore is seal_r
li = S["tc01_leadin_mm"]
aL = 90.0                                                  # an azimuth clear of the holes
uL = frame(aL)[0]
pl = {"z1-1.0_r_seal+0.60_air (3.5 lead-in; material if 3.0)": not inside(tc01, uL * (seal_r + 0.60) + np.array([0, 0, z1 - 1.0])),
      "z1-1.0_r_seal+0.69_material": inside(tc01, uL * (seal_r + 0.69) + np.array([0, 0, z1 - 1.0])),
      "z1-3.6_r_seal+0.01_material": inside(tc01, uL * (seal_r + 0.01) + np.array([0, 0, z1 - 3.6])),
      "z1-3.4_r_seal+0.01_air": not inside(tc01, uL * (seal_r + 0.01) + np.array([0, 0, z1 - 3.4]))}
out["a_tc01_geometry"] = {"flats": flats, "probes_all_pass": allp, "probes": probes,
                          "flat_area_paper_mm2": round(A_flat_paper, 3),
                          "flat_area_paper_basis": "d11.2 disc truncated at the half chord on the OD, less the d5.5 hole",
                          "wall_at_hole_mm": round(rf - seal_r, 3), "wall_at_hole_drawing_mm": [2.665, 2.708],
                          "lead_in": {"length_mm": li, "probes": pl, "all_pass": all(pl.values())}}
print("(a)", json.dumps({k: v for k, v in out["a_tc01_geometry"].items() if k != "probes"})[:1500], flush=True)

# ---------------------------------------------------------------- (b) pocket length vs the TC-01 forward features, FD-04
endf = [f for f in faces if f.geomType() == "PLANE" and abs(f.Center().z - z1) < 1e-6]
assert len(endf) == 1, len(endf)
endf = endf[0]
pocket = {}
for a in angs:
    u, t, ez = frame(a)
    fl = [f for f in faces if f.geomType() == "PLANE" and abs(loc(a, (f.Center().x, f.Center().y, f.Center().z))[0] - rf) < 0.01
          and abs(loc(a, (f.Center().x, f.Center().y, f.Center().z))[1]) < 6 and abs(loc(a, (f.Center().x, f.Center().y, f.Center().z))[2]) < 6]
    walls = []
    for f in faces:
        if f.geomType() != "CYLINDER":
            continue
        c = f.Center()
        xp, yp, zp = loc(a, (c.x, c.y, c.z))
        if xp > rf - 0.01 and abs(yp) < 6.5 and abs(zp) < 6.5 and math.hypot(c.x, c.y) > 31.0:
            r_ = BRepAdaptor_Surface(f.wrapped).Cylinder().Radius()
            if abs(r_ - d_cut / 2.0) < 1e-6:
                walls.append(f)
    d_end_flat = checks.min_distance(fl[0], endf)[0]
    d_end_wall = min(checks.min_distance(w, endf)[0] for w in walls) if walls else None
    d_fd04 = min(checks.min_distance(x, fd04)[0] for x in fl + walls)
    pocket[f"{a:g}"] = {"n_pocket_wall_faces": len(walls), "flat_to_end_face_mm": round(d_end_flat, 3),
                        "pocket_wall_to_end_face_mm": (round(d_end_wall, 3) if d_end_wall is not None else None),
                        "pocket_faces_to_FD04_mm": round(d_fd04, 3)}
zp_end = z1 - zb_
pk = {"per_hole": pocket,
      "axial_paper_mm": {"hole_axis_to_end_face_B": round(zp_end, 3),
                         "pocket_fwd_end_to_end_face": {"d11.2": round(zp_end - 5.6, 3), "d11.3_max": round(zp_end - 5.65, 3)},
                         "pocket_fwd_end_to_lead_in_end (axial; the lead-in is on the bore)": {"d11.2": round(zp_end - li - 5.6, 3),
                                                                                                "d11.3_max": round(zp_end - li - 5.65, 3)},
                         "pocket_aft_end_to_seal_land_end": round((zp_end - 38.0) * -1 - 5.65, 3),
                         "wall_under_the_whole_flat_mm": [round(31.313 - 57.296 / 2, 3), round(31.333 - 57.25 / 2, 3)],
                         "wall_under_the_flat_note": "the flat lies at r_flat from A over its whole area, so the longer pocket keeps the 2.665-2.708 wall; the lead-in (bore side) ends before the pocket starts"},
      "FD04": {"z_cap_foil_top": round(zb_ - 9.5 / 2 - 1.0, 3), "foil_top_below_hole_axis_mm": 5.75,
               "pocket_aft_end_below_hole_axis_mm": {"d11.2": 5.6, "d11.3_max": 5.65},
               "min_FD04_to_pocket_faces_mm": round(min(v["pocket_faces_to_FD04_mm"] for v in pocket.values()), 3)}}
out["b_pocket_vs_forward_features_and_FD04"] = pk
print("(b)", json.dumps(pk)[:1500], flush=True)

# ---------------------------------------------------------------- (h) positional stack on the match-drill method (paper, sourced terms)
SRC = {"ISO286": "CADforum 'ISO Tolerances' (ISO 286 tables), https://www.cadforum.cz/en/tolerance.asp, accessed 2026-10-20: 3-6 mm F7 +22/+10, h8 0/-18, h9 0/-30, g6 -4/-12 um",
       "DIN13": "GANTER 'Specifications and Extracts from DIN / ISO Standards' 2393, DIN 13 extract, tolerance fields 6g / 6H, https://www.ganternorm.com/fileadmin/user_upload/downloads/technischer%20anhang/technical_information/13_gewinde.pdf, accessed 2026-10-20: M5 6g d 4.976/4.826, d2 4.456/4.361, d1 3.995/3.869; 6H D >= 5.000, D2 4.480/4.605, D1 4.134/4.334",
       "spring_ID": "spring v3 inputs (Schnorr brochure 2024-02 p. 10 / Lesjofors 7909: Di 5.2 +0.12/0)"}
pilot = (5.120, 5.150)
Di = (5.20, 5.32)
terms_z = {"pilot_play (spring ID H12 max 5.32 on the pilot h9 min 5.12) / 2": round((Di[1] - pilot[0]) / 2, 4),
           "pilot coaxial to the thread pitch cylinder dia 0.02 (PROPOSED HW-101 drawing value, TO-CONFIRM with the maker)": 0.010,
           "thread play: M5 6H D2 max 4.605 - 6g d2 min 4.361, / 2 (screw axis off the tap axis when the head clamps at first contact)": round((4.605 - 4.361) / 2, 4),
           "tap axis to its TC-01 hole at match-drilling (guide bushing method)": None,
           "axial re-registration: head-gap gauge 2.00 +/-0.02 at match-drilling and at every assembly (TO-CONFIRM), arithmetic": 0.040,
           "spot face coaxial to its hole (dia 0.10, drawn)": 0.050}
bush = {"bushing OD g6 in 0.01 steps selected to the pin-gauged hole (pins in 0.01 steps): (0.01 step + 0.01 pin + 0.012 g6) / 2": round((0.01 + 0.01 + 0.012) / 2, 4),
        "4.2 h8 drill in a 4.2 F7 bushing bore: (0.022 + 0.018) / 2": round((0.022 + 0.018) / 2, 4),
        "bushing bore to OD concentricity 0.005 TIR (GSE drawing requirement) / 2": 0.0025,
        "drill wander over the 9.0 depth past the bushing (ASSUMED, no source)": 0.010}
tap = round(sum(bush.values()), 4)
terms_z["tap axis to its TC-01 hole at match-drilling (guide bushing method)"] = tap
z_stack = round(sum(terms_z.values()), 4)
tol_e = round((11.2 - 0.1 - 10.0) / 2.0, 3)
tang = {"pilot_play": terms_z["pilot_play (spring ID H12 max 5.32 on the pilot h9 min 5.12) / 2"], "pilot_coax": 0.010,
        "thread_play": terms_z["thread play: M5 6H D2 max 4.605 - 6g d2 min 4.361, / 2 (screw axis off the tap axis when the head clamps at first contact)"],
        "tap_to_hole": tap, "fit_registration (plug f7 / bore H8 radial gap, acts tangentially at a radial hole)": 0.078, "spot_face_coax": 0.050}
t_stack = round(sum(tang.values()), 4)
full_float = round((5.62 - 4.826) / 2 + terms_z["pilot_play (spring ID H12 max 5.32 on the pilot h9 min 5.12) / 2"] + 0.010 + 0.050, 4)
out["h_positional_stack_on_the_method"] = {
    "sources": SRC,
    "z_axial_terms_mm": terms_z, "tap_to_hole_terms_mm": bush, "tap_to_hole_mm": tap,
    "z_stack_mm": z_stack, "z_stack_without_thread_play_mm": round(z_stack - terms_z["thread play: M5 6H D2 max 4.605 - 6g d2 min 4.361, / 2 (screw axis off the tap axis when the head clamps at first contact)"], 4),
    "tolerable_e_mm (cutter d11.2 min, corner R 0.05, spring OD 10.0 max)": tol_e, "margin_mm": round(tol_e - z_stack, 4),
    "ruled_design_basis_0.328": {"terms": "pilot play 0.100 + hole position 0.050 + spot-face coaxiality 0.050 + tap position 0.050 + fit registration 0.078",
                                 "finding": ("on the match-drill method the 0.328 is not the axial bound: its fit-registration term (the plug f7 / bore H8 radial "
                                             "gap) moves a radial screw along its own axis or tangentially, never along the engine axis; the hole position "
                                             "to A|B does not enter (the flat is coaxial to its own hole); it omits the thread play, the pilot coaxiality and "
                                             "the axial re-registration")},
    "tangential_terms_mm": tang, "tangential_stack_mm": t_stack,
    "full_float_info_mm": {"value": full_float, "terms": "screw major 4.826 min against the hole wall 5.62 max ((5.62 - 4.826) / 2 = 0.397) + pilot play + pilot coaxiality + spot-face coaxiality",
                           "vs_tolerable": round(tol_e - full_float, 4),
                           "note": "information: a re-assembly with no axial registration (no gauge); spring v3's 0.547 used the hole position in place of the coaxiality and no pilot coaxiality"},
    "pilot_and_undercut_HW101_drawing": {"pilot": "5.15 h9 (5.120-5.150) [ISO286]", "pilot_length_mm": "0.35-0.40 from the bearing face: centres the spring over most of its thickness (t 0.44-0.52) and ends above the flat at every t, so the TC-01 hole sees only the thread (float 0.397, the rows' basis)",
                                          "undercut": "fillet r 0.2-0.3 recessed into the pilot just below the bearing face, root diameter >= 4.75 (below the thread major minimum 4.826, above the thread minor maximum 3.995: the undercut section 17.72 mm2 at d 4.75 stays larger than the thread stress area A_s 14.18 mm2)",
                                          "da_max_mm": 5.15, "da_basis": "the undercut keeps the bearing-face inner edge at the pilot diameter (lead 16:53Z R2: 'State da on our own drawing')",
                                          "pilot_coaxiality": "dia 0.02 to the thread pitch cylinder (PROPOSED, TO-CONFIRM with the maker)"}}
print("(h)", json.dumps(out["h_positional_stack_on_the_method"])[:1200], flush=True)
E_Z = z_stack
E_HEAD = round(tap + 0.040 + terms_z["thread play: M5 6H D2 max 4.605 - 6g d2 min 4.361, / 2 (screw axis off the tap axis when the head clamps at first contact)"], 4)

# ---------------------------------------------------------------- (c) raised head + spring vs every other instance, 5 poses
POSES = ((0.0, 0.0), (-4.96, 4.94), (-4.96, -4.94), (4.96, -4.94), (4.96, 4.94))
res_c = {}
for t_ in (0.44, 0.52):
    for lab, dzh, dzs in (("nominal", 0.0, 0.0), ("offset_toward_FD04", -E_HEAD, -(E_HEAD + 0.110))):
        bodies = []
        for a in angs:
            u, t, ez = frame(a)
            bodies.append(("head", a, cyl_dir(9.5, 2.75 + 0.1, tuple(u * (rf + t_) + np.array([0.0, 0.0, zb_ + dzh])), tuple(u))))
            bodies.append(("spring", a, cyl_dir(10.0, t_, tuple(u * (rf + 0.001) + np.array([0.0, 0.0, zb_ + dzs])), tuple(u))))
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
            pr[f"a{pose[0]:+g}_b{pose[1]:+g}"] = {"close_lt_3mm": recs[:12], "min_mm": recs[0]["dist_mm"] if recs else None,
                                                 "min_FD04_head_mm": min((r["dist_mm"] for r in fd if r["body"] == "head"), default=None),
                                                 "min_FD04_spring_mm": min((r["dist_mm"] for r in fd if r["body"] == "spring"), default=None),
                                                 "min_other_than_FD04_mm": min((r["dist_mm"] for r in recs if not r["other"].startswith("ENG-FD-04")), default=None)}
        mins = [v["min_mm"] for v in pr.values() if v["min_mm"] is not None]
        res_c[f"t{t_:.2f}|{lab}"] = {"head_dz_mm": round(dzh, 4), "spring_dz_mm": round(dzs, 4), "poses": pr,
                                     "min_any_mm": min(mins) if mins else None,
                                     "min_FD04_head_all_poses_mm": min((v["min_FD04_head_mm"] for v in pr.values() if v["min_FD04_head_mm"] is not None), default=None),
                                     "min_FD04_spring_all_poses_mm": min((v["min_FD04_spring_mm"] for v in pr.values() if v["min_FD04_spring_mm"] is not None), default=None)}
        print("(c)", t_, lab, res_c[f"t{t_:.2f}|{lab}"]["min_any_mm"], res_c[f"t{t_:.2f}|{lab}"]["min_FD04_head_all_poses_mm"],
              res_c[f"t{t_:.2f}|{lab}"]["min_FD04_spring_all_poses_mm"], flush=True)
out["c_raised_head_and_spring_vs_parts"] = res_c

# ---------------------------------------------------------------- (d) spring rim vs the pocket wall (axial)
res_d = {}
for a in (angs[0], angs[5]):
    u, t, ez = frame(a)
    for e in (0.0, 0.328, E_Z, 0.547, full_float, 0.60, 0.62):
        for sgn in (1, -1):
            sprg = cyl_dir(10.0, 0.52, tuple(u * (rf + 0.001) + np.array([0.0, 0.0, zb_ + sgn * e])), tuple(u))
            v = sprg.intersect(tc01).Volume()
            res_d[f"az{a:g}|e{sgn * e:+.4f}"] = round(v, 5)
onset = {k: v for k, v in res_d.items() if v > 1e-4}
out["d_spring_rim_vs_pocket_wall"] = {"common_volume_mm3": res_d, "nonzero": onset,
                                      "verdict": ("no common volume up to e 0.60 (CAD sharp corner at the cutter radius 5.6); the drawn corner R <= 0.05 gives "
                                                  f"the paper tolerable e {tol_e}; method stack {E_Z} (margin {round(tol_e - E_Z, 4)}), ruled 0.328 "
                                                  f"(margin {round(tol_e - 0.328, 3)}), full float {full_float} (information, {round(tol_e - full_float, 4)})")}
print("(d)", json.dumps(out["d_spring_rim_vs_pocket_wall"])[:1500], flush=True)


# ---------------------------------------------------------------- (e) supported area of the spring annulus on the flat
def annulus_face(a, x_plane, dy, dz, od=10.0, idd=5.2):
    u, t, ez = frame(a)
    c = u * x_plane + t * dy + ez * (zb_ + dz)
    pl = cq.Plane(origin=cq.Vector(*c), xDir=cq.Vector(*t), normal=cq.Vector(*u))
    wp = cq.Workplane(pl).circle(od / 2.0).circle(idd / 2.0).extrude(0.002)
    return wp.val()


def supported(solid, a, x_plane, dy, dz):
    sl = annulus_face(a, x_plane - 0.0025, dy, dz)          # 0.002 slab from x' - 0.0025 to x' - 0.0005
    return sl.intersect(solid).Volume() / 0.002


def seg_area(R_, d):
    if d >= R_:
        return 0.0
    if d <= -R_:
        return math.pi * R_ ** 2
    return R_ ** 2 * math.acos(d / R_) - d * math.sqrt(R_ ** 2 - d ** 2)


def hole_overlap(R_out, r_hole, R_in, e):
    """area of the hole circle (radius r_hole, centred on the flat axis) inside the annulus R_in..R_out offset by e: numerical"""
    n = 400
    xs = np.linspace(-r_hole, r_hole, n)
    dx = xs[1] - xs[0]
    tot = 0.0
    for x in xs:
        h = math.sqrt(max(r_hole ** 2 - x ** 2, 0.0))
        ys = np.linspace(-h, h, 60)
        dy_ = ys[1] - ys[0] if len(ys) > 1 else 0.0
        rr = np.hypot(x - e, ys)
        tot += float(np.sum((rr <= R_out) & (rr >= R_in))) * dy_ * dx
    return tot


Ann = math.pi / 4.0 * (10.0 ** 2 - 5.2 ** 2)
res_e = {"annulus_mm2": round(Ann, 3), "nominal_CAD": {}, "worst_stack_tube": {}}
a = angs[0]
hc_nom = sp["half_chord_on_OD_mm"]
for e_t, e_z in ((0.0, 0.0), (0.328, 0.0), (t_stack, 0.0), (0.547, 0.0), (0.0, E_Z), (0.0, 0.547)):
    A_cad = supported(tc01, a, rf, e_t, e_z)
    over = seg_area(5.0, hc_nom - e_t) + seg_area(5.0, hc_nom + e_t)
    hol = hole_overlap(5.0, 2.75, 2.6, math.hypot(e_t, e_z))
    res_e["nominal_CAD"][f"e_t{e_t:.3f}|e_z{e_z:.3f}"] = {"A_CAD_mm2": round(A_cad, 3), "A_paper_mm2 (annulus - tangential overhang - hole overlap)": round(Ann - over - hol, 3),
                                                         "tangential_supported_fraction_paper (spring v3 definition)": round((Ann - over) / Ann, 4),
                                                         "bearing_fraction_CAD (hole excluded)": round(A_cad / Ann, 4)}
# worst-stack tube: OD 63.426 centred 0.02 away from the hole side, flat at 31.333 from A, cutter d11.2, hole 5.62
R_ws, ecc, rf_ws, hole_ws = 63.426 / 2.0, 0.02, 31.333, 5.62
u, t, ez = frame(a)
L_ = 40.0
outer = cyl_dir(2 * R_ws, L_, tuple(-u * ecc + np.array([0.0, 0.0, zb_ - L_ / 2])), (0.0, 0.0, 1.0))
inner = cyl_dir(57.25, L_ + 2, tuple(np.array([0.0, 0.0, zb_ - L_ / 2 - 1])), (0.0, 0.0, 1.0))
ws = outer.cut(inner)
ws = ws.cut(radial_hole(11.2, a, zb_, rf_ws, R_ws + 2.0)).cut(radial_hole(hole_ws, a, zb_, 27.0, R_ws + 2.0))
hc_ws = math.sqrt(R_ws ** 2 - (rf_ws + ecc) ** 2)
for e_t, e_z in ((0.0, 0.0), (0.328, 0.0), (t_stack, 0.0), (0.547, 0.0), (0.0, E_Z)):
    A_cad = supported(ws, a, rf_ws, e_t, e_z)
    over = seg_area(5.0, hc_ws - e_t) + seg_area(5.0, hc_ws + e_t)
    hol = hole_overlap(5.0, hole_ws / 2.0, 2.6, math.hypot(e_t, e_z))
    res_e["worst_stack_tube"][f"e_t{e_t:.3f}|e_z{e_z:.3f}"] = {"A_CAD_mm2": round(A_cad, 3), "A_paper_mm2 (annulus - tangential overhang - hole overlap)": round(Ann - over - hol, 3),
                                                              "tangential_supported_fraction_paper (spring v3 definition, no OD break)": round((Ann - over) / Ann, 4),
                                                              "bearing_fraction_CAD (hole excluded)": round(A_cad / Ann, 4)}
res_e["worst_stack_tube_basis"] = {"OD": 63.426, "ecc_away_from_hole_side": ecc, "r_flat_from_A": rf_ws, "hole": hole_ws, "half_chord_mm": round(hc_ws, 4),
                                   "spring_v3_half_chord_worst_stack_mm": 4.7633,
                                   "note": "spring v3 / rows v6 subtract the eccentricity from the OD radius (4.7633); here the OD centre is offset (4.7649): 0.0016 apart; the 0.1 OD break is not modelled"}
out["e_supported_area"] = res_e
print("(e)", json.dumps(res_e)[:2500], flush=True)

# ---------------------------------------------------------------- (f) TC-02 tap walls at the clocking tolerance
plug_r, jd = 57.20 / 2.0, S["jfwd_tap_drill_mm"]
filled = tc02
for t_ in [radial_hole(4.2, a, zb_, plug_r - jd, plug_r + 1.0) for a in angs]:
    filled = filled.fuse(t_)
filled = filled.clean()
env = cyl(2 * (plug_r - 0.01), S["inj_face"] + 0.5, S["head_bot"] - 0.5)


def extra(pr_):
    return pr_.intersect(env).cut(filled).Volume()


def bis(mk, hi=4.0):
    if extra(mk(hi)) <= 0.01:
        return f">{hi}"
    lo = 0.0
    for _ in range(8):
        mid = 0.5 * (lo + hi)
        if extra(mk(mid)) > 0.01:
            hi = mid
        else:
            lo = mid
    return round(lo, 3)


res_f = {}
for a0 in (18.0, 342.0, 126.0, 162.0):
    row = {}
    for dl in (0.0, -0.5, 0.5, -1.0, 1.0):
        a = a0 + dl
        mk = lambda w, a=a: radial_hole(5.0 + 2 * w, a, zb_, plug_r - jd - w, plug_r - 0.2)
        row[f"{dl:+.1f}deg"] = bis(mk)
    res_f[f"az{a0:g}"] = row
    print("(f)", a0, row, flush=True)
out["f_tc02_tap_walls_clocking"] = {"walls_mm_from_M5_major": res_f, "probe": "d 5.0 + 2w from r 28.6 - 9.0 - w to r 28.4 inside the plug envelope (as test_interim352b v1)",
                                    "note": "add the TC-01 hole position (0.05 radial) and the axial gauge (0.02) arithmetically to any wall read here"}

# ---------------------------------------------------------------- (g) datum B
d12 = checks.min_distance(tc01, tc02)[0]
zb, zf = S["head_bot"], S["inj_face"]
f02 = tc02.Faces()
shoulder = [f for f in f02 if f.geomType() == "PLANE" and abs(f.Center().z - zb) < 1e-6]
plug_end = [f for f in f02 if f.geomType() == "PLANE" and abs(f.Center().z - zf) < 1e-6]
d_end_shoulder = min(checks.min_distance(endf, f)[0] for f in shoulder) if shoulder else None
d_end_tc02 = checks.min_distance(endf, tc02)[0]
step = [f for f in faces if f.geomType() == "PLANE" and abs(f.Center().z - (z1 - (P["plug_len_fwd"]["v"] * 1000.0 + 2.0))) < 1e-6
        and math.hypot(f.Center().x, f.Center().y) < 29.0]
d_step = min(checks.min_distance(step[0], f)[0] for f in plug_end) if (step and plug_end) else None
out["g_datum_B"] = {"min_TC01_TC02_mm (radial plug / bore gap, CAD nominal)": round(d12, 4),
                    "TC01_fwd_end_face_to_TC02_head_shoulder_mm": (round(d_end_shoulder, 4) if d_end_shoulder is not None else "shoulder face not found"),
                    "TC01_fwd_end_face_to_TC02_any_mm (the plug passes the end face's inner edge radially)": round(d_end_tc02, 4),
                    "TC01_bore_step_to_TC02_plug_end_mm": (round(d_step, 4) if d_step is not None else "faces not found"),
                    "n_faces": {"tc02_shoulder": len(shoulder), "tc02_plug_end": len(plug_end), "tc01_step": len(step)},
                    "hole_row_from_end_face_mm": round(z1 - zb_, 4),
                    "verdict": ("TC-02 does not seat axially on TC-01 (head shoulder and plug end both clear); the hole row is dimensioned from the "
                                "TC-01 fwd end face: datum B = the TC-01 fwd end face")}
print("(g)", out["g_datum_B"], flush=True)
out["t_total_s"] = round(time.time() - t0, 1)
Path_ = __import__("pathlib").Path
Path_(OUT).write_text(json.dumps(out, indent=1, default=str))
print("written", OUT, hashlib.sha256(Path_(OUT).read_bytes()).hexdigest()[:16], out["t_total_s"], flush=True)
