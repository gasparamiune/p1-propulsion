"""cD-ONLY COPY of jfwd_sub.py cbc4c2ae2a1b61fd (FEA3D-2, 2026-10-21; lead 2026-10-21T02:01:34Z (C)): the mu 0 convergence check cD of the
governing seat line d+6.051 z'0, mesh tag sD, on the FINAL TC-01.  Changes against the production file (nothing else changed; the
production jfwd_sub.py is untouched and still expects the interim TC-01):
  (1) STEP_SHA["spot"] = fcb3b5b93bebdb01: the FINAL 03-cad v3.5.2 parts/ENG-TC-01.step (CHANGELOG 247, rev 5: the 10 flats cut with
      the d11.2 cutter at r_flat 31.313, coplanar with the interim d10.5 flats; wall at the hole 2.688; material removal only);
  (2) two gmsh Ball fields, h 0.04 (VIn), Radius 0.3, Thickness 0.3, at both ends of the governing line (radial, az 18 + 6.051 deg,
      z = Z_SCREW - shift): the bore end r 28.652 and the flat end r 31.313 / cos(6.051 deg) - 0.03 (MeshSizeMin stays
      0.5 x min(h, h_brk) = 0.04 = VIn, as in the costing build);
      recorded in mesh_sD.json "cD_balls";
  (3) OUT may be redirected with FEA3D_CD_OUT (the count build in /dev/shm before the production build; default jfwd/).
Costing: runs/cost_convcheck_v352 (candidate cD, built there on the interim TC-01).

FEA3D J-FWD one-sector contact sub-model (v3.5.2 item 2; lead CHANGELOG 231 (3), 234 (1)(b)/(c)/(e); relays 2026-10-20 ~02:50Z / 03:10Z).

Geometry (CAD v3.5.2 interim, Mechanical 03-cad/v3.5.2/parts ENG-TC-01 / ENG-TC-02 STEP, placed with placements_v3.5.2.json z offsets):
  one 36 deg sector az 0..36 deg of TC-01 (case, z >= ZCUT) and TC-02 (head) holding the J-FWD screw at az 18 deg (10x at 18 + 36k);
  the az 0 plane is the mirror plane of the torch passage (TC-02 drill R2.6 + outlet R1.5 + counterbore R4.5 lie in it), so the sector
  carries half of the torch passage and the 1.906 mm tap-to-passage wall (Mechanical 233 (4)); both cut planes are symmetry planes (u_theta = 0).
  Screw HW-101 ISO 7380-1 M5 x 10 A4-80 as a SOLID screw (lead 231 (3)): button head modelled as a cylinder D 9.5 x k 2.75 with a flat
  bearing face (dome and hex socket omitted), shank D 5.0 (thread major) through the TC-01 hole D 5.5; in TC-02 the tap is opened to
  the thread major D 5.0 over the engaged length (x' 21.5..28.6) and the screw is BONDED there (conformal mesh): the TC-02 wall is
  modelled at the thread-root diameter, so the tap-to-passage wall is the 1.906 mm of the drawing (the 4.2 mm drill would leave 2.3 mm);
  the screw tip annulus is detached (no end bond).  Screw tip at x' 21.75 (L 10 under the head from the OD r 31.75).
  'Settled bearing' state: the TC-01 sector is shifted by -0.24 mm in z, so the shank touches the hole's +z wall (gap 0.01 mm) and the
  head (pushed +z by the chamber pressure) bears at once (Mechanical: the head settles one way into bearing within the 0.26 mm clearance;
  234 (1)(c): bearing-type joint); the -z side clearance is 0.49 mm.  The 0.025 mm radial fit gap TC-01 bore r 28.625 / TC-02 r 28.600
  and the 0.01 mm head-to-OD gap at the tangency line are kept (contact).
Units mm, N, MPa, K.  fea3d 2026-10-20.
usage: jfwd_sub.py mesh [tag=s1] [h=0.3] [zcut=97.5] [shift=0.24] [hmax=3.0] [dmax=9.0] [members_only=0] [seat=cad|spot]
                       [brk_r=0] [brk_c=0] [h_brk=0.08] [brk_dmax=0.6]   (s6: seat=spot brk_r=0.2 brk_c=0.1)
"""
from __future__ import annotations
import sys, json, math, time, os
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import mesh3d                # noqa: E402  (PERM_TET10, TET_FACES, FACE_MID)

CAD = Path("/home/claude/work/shared-fallback/engine/03-cad/v3.5.2")
OUT = Path(os.environ.get("FEA3D_CD_OUT", "/home/claude/work/fea3d/jfwd"))   # cD copy (3)
Z_OFF = {"TC-01": 139.513426018, "TC-02": 169.513426018}     # placements_v3.5.2.json (identity rotation)
AZ_SCREW = 18.0
SECTOR = 36.0
Z_SCREW = 127.513
R_OD, R_BORE01, R_OD02 = 31.75, 28.625, 28.600
GEO = {"head_r": 4.75, "head_k": 2.75, "shank_r": 2.5, "hole_r": 2.75, "x_tip": 21.75, "x_tap_lo": 21.5, "x_od": R_OD, "head_gap": 0.01,
       "x_pre": 30.2, "x_tc02": R_OD02, "seat": "cad", "x_seat": R_OD}
# 2026-10-20 07:55Z (lead 07:43Z): seat 'spot' = Mechanical's spot-face TC-01 (03-cad/v3.5.2/parts/ENG-TC-01.step 1ad07e472709b1b2,
# V352_R4_JFWD_SPOT): 10 flats d10.5 normal to the hole axes, flat at x' 31.313 (depth 0.437 at the screw axis, wall 2.688 at the hole),
# each running out on the OD (half-chord 5.25 at R31.75).  The head bears on the flat: the screw moves 0.437 mm inward (tip x' 21.313,
# engagement in the TC-02 tap 28.6 - 21.313 = 7.287 mm; tip 0.713 mm short of the 8.0 full thread); the tap opening keeps its 0.25 mm
# below the tip.  seat 'cad' = the old cylindrical seat (history ENG-TC-01.step.5273048e98033c1e; meshes s1..s4, jobs jt1 / js4 / js4b).
SPOT = {"x_seat": 31.313, "depth": 0.437, "r_flat": 5.25, "wall_at_hole": 2.688}
STEP_SHA = {"cad": "5273048e98033c1e", "spot": "fcb3b5b93bebdb01"}   # cD copy (1): FINAL TC-01 (the production file: interim 1ad07e472709b1b2)
CD_BALL = {"h": 0.04, "r": 0.3, "t": 0.3, "delta_deg": 6.051, "r_bore_end": 28.652, "flat_end_inset": 0.03}   # cD copy (2)


def set_seat(seat):
    """set the head-seat geometry in GEO ('cad' or 'spot'); returns GEO."""
    if seat == "spot":
        dx = R_OD - SPOT["x_seat"]
        GEO.update({"seat": "spot", "x_seat": SPOT["x_seat"], "x_tip": round(21.75 - dx, 6), "x_tap_lo": round(21.5 - dx, 6)})
    elif seat == "cad":
        GEO.update({"seat": "cad", "x_seat": R_OD, "x_tip": 21.75, "x_tap_lo": 21.5})
    else:
        raise ValueError(seat)
    return GEO


def use_mesh(tag):
    """restore GEO from a mesh's json (meshes before 07:55Z carry no 'seat' key: the CAD seat)."""
    mj = json.loads((OUT / f"mesh_{tag}.json").read_text())
    g = dict(mj.get("geo", {}))
    set_seat(g.get("seat", "cad"))
    GEO.update({"brk_r": 0.0, "brk_c": 0.0})          # meshes before s6 carry no edge breaks (sharp hole edges)
    GEO.update(g)
    return mj


def r_out(delta, zp, eps=0.002):
    """exit radius (minus eps) of the radial line at azimuth offset delta (rad) from the screw axis, at z' (mm) about the TC-01 hole axis:
    R_OD on the cylinder; on the spot-face flat (|y'| = r sin|delta| <= the flat's half-width at z') the line ends on the plane x' = x_seat,
    r = x_seat / cos(delta) (2026-10-20 08:35Z; shared by jfwd_post / jfwd_ligament / jfwd_midbay)."""
    ro = R_OD - eps
    if GEO.get("seat") == "spot" and abs(zp) < SPOT["r_flat"]:
        w = math.sqrt(SPOT["r_flat"] ** 2 - zp ** 2)
        r1 = SPOT["x_seat"] / math.cos(delta)
        if r1 * abs(math.sin(delta)) <= w:
            ro = min(ro, r1 - eps)
    return ro


def x_out(yp, zp):
    """local outer-surface x' of TC-01 at screw-local (y', z') (relative to the TC-01 hole axis): the spot-face flat inside the d10.5
    cutter, else the OD cylinder R31.75 (x' = sqrt(R_OD^2 - y'^2))."""
    yp, zp = np.asarray(yp, float), np.asarray(zp, float)
    od = np.sqrt(np.maximum(R_OD ** 2 - yp ** 2, 0.0))
    if GEO.get("seat") == "spot":
        return np.where(yp ** 2 + zp ** 2 <= SPOT["r_flat"] ** 2, np.minimum(SPOT["x_seat"], od), od)
    return od


def er(az_deg):
    a = math.radians(az_deg)
    return np.array([math.cos(a), math.sin(a), 0.0])


def _hole_frame(P):
    """x' along the screw axis and r' from the (unshifted) TC-01 hole axis (az 18, z Z_SCREW) for points P (n,3)."""
    e = er(AZ_SCREW)
    rel = np.atleast_2d(P) - np.array([0.0, 0.0, Z_SCREW])
    xa = rel @ e
    rp = np.linalg.norm(rel - np.outer(xa, e), axis=1)
    return xa, rp


def _curve_pts(gm, c, n=9):
    lo, hi = gm.model.getParametrizationBounds(1, c)
    return np.array(gm.model.getValue(1, c, list(np.linspace(lo[0], hi[0], n)))).reshape(-1, 3)


def _surf_pts(gm, s, n=5):
    lo, hi = gm.model.getParametrizationBounds(2, s)
    u, v = np.meshgrid(np.linspace(lo[0], hi[0], n), np.linspace(lo[1], hi[1], n))
    uv = np.column_stack([u.ravel(), v.ravel()]).ravel()
    return np.array(gm.model.getValue(2, s, list(uv))).reshape(-1, 3)


def _hole_edges(gm, vt):
    """(bore-end curves, flat-end curves, the flat face of each flat-end curve) of the TC-01 screw hole (hole cylinder r' = hole_r)."""
    bore, flat, flat_faces = [], [], []
    for v in vt:
        for _, s in gm.model.getBoundary([(3, v)], oriented=False):
            for _, c in gm.model.getBoundary([(2, abs(s))], oriented=False):
                c = abs(c)
                P = _curve_pts(gm, c)
                xa, rp = _hole_frame(P)
                if not np.all(np.abs(rp - GEO["hole_r"]) < 2e-3):
                    continue
                rr = np.hypot(P[:, 0], P[:, 1])
                if np.all(np.abs(rr - R_BORE01) < 2e-3) and c not in bore:
                    bore.append(c)
                elif np.all(np.abs(xa - GEO["x_seat"]) < 2e-3) and c not in flat:
                    # the face of this curve that is the spot-face flat (plane x' = x_seat)
                    up, _ = gm.model.getAdjacencies(1, c)
                    for f in up:
                        xs, _ = _hole_frame(_surf_pts(gm, int(f)))
                        if np.all(np.abs(xs - GEO["x_seat"]) < 2e-3):
                            flat.append(c)
                            flat_faces.append(int(f))
                            break
    return bore, flat, flat_faces


def break_hole_edges(gm, t01):
    """2026-10-20 10:30Z (lead 10:14Z (4)): drawing-maximum edge breaks of the TC-01 J-FWD hole -- fillet GEO['brk_r'] on the hole-to-bore
    edge and a 45 deg chamfer GEO['brk_c'] on the hole-to-flat (spot face) edge; OCC on the imported STEP sector, before the settle shift.
    No-op when both are 0 (meshes s1..s5)."""
    br, bc = float(GEO.get("brk_r", 0.0)), float(GEO.get("brk_c", 0.0))
    if br <= 0 and bc <= 0:
        return t01
    occ = gm.model.occ
    occ.synchronize()
    vt = [t for d, t in t01 if d == 3]
    bore, flat, ff = _hole_edges(gm, vt)
    GEO["brk_found"] = {"bore_curves": len(bore), "flat_curves": len(flat)}
    if br > 0:
        if not bore:
            raise RuntimeError("hole-to-bore edge not found")
        t01 = occ.fillet(vt, bore, [br], removeVolume=True)
        occ.synchronize()
        vt = [t for d, t in t01 if d == 3]
    if bc > 0:
        bore2, flat, ff = _hole_edges(gm, vt)
        if not flat:
            raise RuntimeError("hole-to-flat edge not found")
        t01 = occ.chamfer(vt, flat, ff, [bc] * len(flat), removeVolume=True)
        occ.synchronize()
    return [(3, t) for d, t in t01 if d == 3]


def break_faces(gm, t01):
    """TC-01 faces created by the edge breaks (all sampled points with hole_r <= r' <= hole_r + max break + 0.01, some above hole_r + 0.01),
    in the final (shifted) geometry: r' about the shifted hole axis."""
    br, bc = float(GEO.get("brk_r", 0.0)), float(GEO.get("brk_c", 0.0))
    if br <= 0 and bc <= 0:
        return []
    shift = float(GEO.get("_shift", 0.0))
    out = []
    for v in [t for d, t in t01]:
        for _, s in gm.model.getBoundary([(3, v)], oriented=False):
            P = _surf_pts(gm, abs(s), 7) + np.array([0.0, 0.0, shift])
            xa, rp = _hole_frame(P)
            if np.all(rp >= GEO["hole_r"] - 2e-3) and np.all(rp <= GEO["hole_r"] + max(br, bc) + 0.01) and (rp > GEO["hole_r"] + 0.01).any():
                out.append(abs(s))
    return sorted(set(out))


def build_geometry(gm, zcut=97.5, shift=0.24):
    occ = gm.model.occ
    vols = {}
    for part in ("TC-01", "TC-02"):
        dt = occ.importShapes(str(CAD / "parts" / f"ENG-{part}.step"))
        occ.translate(dt, 0, 0, Z_OFF[part])
        vols[part] = [t for d, t in dt if d == 3]
    ang = math.radians(SECTOR)
    w1 = occ.addCylinder(0, 0, zcut, 0, 0, 141.0 - zcut, 45.0, angle=ang)
    w2 = occ.addCylinder(0, 0, 102.0, 0, 0, 69.0, 45.0, angle=ang)
    t01, _ = occ.intersect([(3, v) for v in vols["TC-01"]], [(3, w1)])
    t02, _ = occ.intersect([(3, v) for v in vols["TC-02"]], [(3, w2)])
    t01 = break_hole_edges(gm, t01)
    occ.translate(t01, 0, 0, -shift)
    # screw along local x at az 0, then rotated to az 18 about z through the origin, at z = Z_SCREW
    g = GEO
    x_head = g["x_seat"] + g["head_gap"]
    head = occ.addCylinder(x_head, 0, 0, g["head_k"], 0, 0, g["head_r"])
    sh_hi = occ.addCylinder(g["x_pre"], 0, 0, x_head - g["x_pre"], 0, 0, g["shank_r"])
    sh_lo = occ.addCylinder(g["x_tip"], 0, 0, g["x_pre"] - g["x_tip"], 0, 0, g["shank_r"])
    sh_up, _ = occ.fuse([(3, head)], [(3, sh_hi)])
    for dt in (sh_up, [(3, sh_lo)]):
        occ.translate(dt, 0, 0, Z_SCREW)
        occ.rotate(dt, 0, 0, 0, 0, 0, 1, math.radians(AZ_SCREW))
    # open the TC-02 tap to the thread major over the engaged length (x' x_tap_lo .. 29.0)
    cut = occ.addCylinder(g["x_tap_lo"], 0, 0, 29.0 - g["x_tap_lo"], 0, 0, g["shank_r"])
    occ.translate([(3, cut)], 0, 0, Z_SCREW)
    occ.rotate([(3, cut)], 0, 0, 0, 0, 0, 1, math.radians(AZ_SCREW))
    t02c, _ = occ.cut(t02, [(3, cut)])
    occ.synchronize()
    # fragment TC-02 with the two screw pieces (conformal bonded thread cylinder + the pretension section disc); TC-01 stays separate
    out, omap = occ.fragment(t02c, sh_up + [(3, sh_lo)])
    occ.synchronize()
    return t01, out


def classify_volumes(gm, t01):
    """body name per volume tag from its centre of mass (screw = inside the screw cylinder or the head)."""
    occ = gm.model.occ
    e = er(AZ_SCREW)
    names = {}
    for d, t in gm.model.getEntities(3):
        c = np.array(occ.getCenterOfMass(3, t))
        if (3, t) in t01:
            names[t] = "TC-01"
            continue
        rel = c - np.array([0, 0, Z_SCREW])
        xa = rel @ e
        rr = np.linalg.norm(rel - xa * e)
        if (rr <= GEO["head_r"] + 1e-6 and xa >= GEO["x_od"]) or (rr <= GEO["shank_r"] + 1e-6 and GEO["x_tip"] - 1e-6 <= xa <= GEO["x_od"] + 0.02):
            names[t] = "SCREW"
        else:
            names[t] = "TC-02"
    return names


def mesh(tag="s1", h=0.3, zcut=97.5, shift=0.24, hmax=3.0, verbose=False, dmax=9.0, members_only=False, seat="cad",
         brk_r=0.0, brk_c=0.0, h_brk=0.08, brk_dmax=0.6):
    """brk_r / brk_c (2026-10-20 ~10:50Z, lead 10:14Z (4) / ~10:15Z (3)): drawing-maximum edge breaks of the TC-01 J-FWD hole (R brk_r
    fillet hole-to-bore, brk_c x 45 deg chamfer hole-to-flat), meshed at h_brk on the break faces (Threshold DistMin 0.05 -> h at brk_dmax)."""
    import gmsh
    set_seat(seat)
    GEO.update({"brk_r": float(brk_r), "brk_c": float(brk_c), "h_brk": float(h_brk), "_shift": float(shift)})
    t0 = time.time()
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.model.add("jfwd")
    t01, out = build_geometry(gmsh, zcut, shift)
    names = classify_volumes(gmsh, t01)
    info = {"volumes": {int(t): n for t, n in names.items()}}
    # ------------------------------------------------------------------ size fields
    e = er(AZ_SCREW)
    c0 = np.array([0, 0, Z_SCREW])
    surf_ref = []
    # members_only (2026-10-20 04:52Z): size from the TC-01 / TC-02 faces only (hole, tap, OD patch under the head, torch wall); the
    # screw takes h where it touches them (bonded thread = shared tap faces, shank 0.25 mm inside the hole, head 0.01 mm off the OD)
    mem_faces = set()
    for t, n in names.items():
        if n in ("TC-01", "TC-02"):
            up, dn = gmsh.model.getAdjacencies(3, t)
            mem_faces.update(int(f) for f in dn)
    for d, t in gmsh.model.getEntities(2):
        if members_only and t not in mem_faces:
            continue
        bb = gmsh.model.getBoundingBox(2, t)
        cmin, cmax = np.array(bb[:3]), np.array(bb[3:])
        cc = 0.5 * (cmin + cmax)
        rel = cc - c0
        xa = rel @ e
        rr = np.linalg.norm(rel - xa * e)
        ext = np.linalg.norm(cmax - cmin)
        if rr <= 5.0 and 19.0 <= xa <= 35.0 and ext <= 20.0:      # hole / tap / screw / head faces round the screw axis
            surf_ref.append(t)
    f_d = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(f_d, "SurfacesList", surf_ref)
    gmsh.model.mesh.field.setNumber(f_d, "Sampling", 60)
    f_t = gmsh.model.mesh.field.add("Threshold")
    for k, v in (("InField", f_d), ("SizeMin", h), ("SizeMax", hmax), ("DistMin", 0.35), ("DistMax", dmax)):
        gmsh.model.mesh.field.setNumber(f_t, k, v)
    # torch-passage wall: ball round the closest approach of the tap and the passage (z ~ Z_SCREW)
    # 2026-10-20 04:58Z: the Ball field was not honoured (wall tets 0.42-0.47 mean edge, drill-face nodes coarse: tap-to-drill node gap
    # 2.15 mm on s3 vs the CAD 1.906); replaced by a Threshold on a MathEval distance to the wall centre (h within 3.2 mm, ramp to hmax at 6.5)
    f_pd = gmsh.model.mesh.field.add("MathEval")
    gmsh.model.mesh.field.setString(f_pd, "F", f"sqrt((x-21.56)^2+(y-3.38)^2+(z-{Z_SCREW})^2)")
    f_b = gmsh.model.mesh.field.add("Threshold")
    for k, v in (("InField", f_pd), ("SizeMin", h), ("SizeMax", hmax), ("DistMin", 3.2), ("DistMax", 6.5)):
        gmsh.model.mesh.field.setNumber(f_b, k, v)
    fields = [f_t, f_b]
    bfaces = break_faces(gmsh, t01)
    info["break_faces"] = [int(v) for v in bfaces]
    if bfaces:
        f_bd = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(f_bd, "SurfacesList", bfaces)
        gmsh.model.mesh.field.setNumber(f_bd, "Sampling", 120)
        f_bt = gmsh.model.mesh.field.add("Threshold")
        # StopAtDistMax: no size imposed beyond brk_dmax (10:51Z: without it the field returned h everywhere -> 3.9 M nodes)
        for k, v in (("InField", f_bd), ("SizeMin", h_brk), ("SizeMax", h), ("DistMin", 0.05), ("DistMax", brk_dmax), ("StopAtDistMax", 1)):
            gmsh.model.mesh.field.setNumber(f_bt, k, v)
        fields.append(f_bt)
    # cD copy (2): Ball fields at both ends of the governing seat line d+6.051 z'0 (lead 02:01:34Z (C))
    azb = math.radians(AZ_SCREW + CD_BALL["delta_deg"])
    zb = Z_SCREW - shift
    r_flat_end = SPOT["x_seat"] / math.cos(math.radians(CD_BALL["delta_deg"])) - CD_BALL["flat_end_inset"]
    info["cD_balls"] = []
    for rb in (CD_BALL["r_bore_end"], r_flat_end):
        f_ball = gmsh.model.mesh.field.add("Ball")
        for k, v in (("VIn", CD_BALL["h"]), ("VOut", 1e3), ("Radius", CD_BALL["r"]), ("Thickness", CD_BALL["t"]),
                     ("XCenter", rb * math.cos(azb)), ("YCenter", rb * math.sin(azb)), ("ZCenter", zb)):
            gmsh.model.mesh.field.setNumber(f_ball, k, v)
        fields.append(f_ball)
        info["cD_balls"].append({"r": round(rb, 4), "x": round(rb * math.cos(azb), 5), "y": round(rb * math.sin(azb), 5), "z": round(zb, 4),
                                 "VIn": CD_BALL["h"], "Radius": CD_BALL["r"], "Thickness": CD_BALL["t"]})
    f_m = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(f_m, "FieldsList", fields)
    gmsh.model.mesh.field.setAsBackgroundMesh(f_m)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", hmax)
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.5 * (min(h, h_brk) if bfaces else h))
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    ok = False
    for a2, a3 in ((6, 10), (6, 1), (1, 1)):
        gmsh.model.mesh.clear()
        gmsh.option.setNumber("Mesh.Algorithm", a2)
        gmsh.option.setNumber("Mesh.Algorithm3D", a3)
        try:
            gmsh.model.mesh.generate(3)
            ok = True
            info["alg"] = [a2, a3]
            break
        except Exception as ex:
            info.setdefault("alg_fail", []).append([a2, a3, str(ex)[:200]])
    if not ok:
        gmsh.finalize()
        raise RuntimeError(f"gmsh failed: {info}")
    ntag, xyz, _ = gmsh.model.mesh.getNodes()
    X = xyz.reshape(-1, 3)
    idx = {int(t): i for i, t in enumerate(ntag)}
    T, B = [], []
    for d, t in gmsh.model.getEntities(3):
        et, el, en = gmsh.model.mesh.getElements(3, t)
        for a, b in zip(et, en):
            if a == 11:
                c = np.vectorize(idx.get)(np.asarray(b, np.int64).reshape(-1, 10))[:, mesh3d.PERM_TET10]
                T.append(c)
                B += [names[t]] * len(c)
    T = np.vstack(T)
    B = np.array(B)
    q = []
    for d, t in gmsh.model.getEntities(3):
        et, el, en = gmsh.model.mesh.getElements(3, t)
        for a, b in zip(et, el):
            if a == 11:
                q.append(np.asarray(gmsh.model.mesh.getElementQualities(b, "minSICN")))
    q = np.concatenate(q)
    gmsh.finalize()
    # drop unused nodes
    used = np.unique(T)
    rm = -np.ones(len(X), np.int64)
    rm[used] = np.arange(len(used))
    X, T = X[used], rm[T]
    import hashlib
    info["TC01_step_sha16"] = hashlib.sha256((CAD / "parts" / "ENG-TC-01.step").read_bytes()).hexdigest()[:16]
    info["TC02_step_sha16"] = hashlib.sha256((CAD / "parts" / "ENG-TC-02.step").read_bytes()).hexdigest()[:16]
    if info["TC01_step_sha16"] != STEP_SHA[seat]:
        raise RuntimeError(f"seat {seat} needs TC-01 STEP {STEP_SHA[seat]}, found {info['TC01_step_sha16']}")
    info.update({"tag": tag, "h": h, "hmax": hmax, "dmax": dmax, "members_only": bool(members_only), "zcut": zcut, "shift": shift, "n_nodes": int(len(X)), "n_tets": int(len(T)),
                 "per_body_tets": {b: int((B == b).sum()) for b in sorted(set(B))}, "q_min": float(q.min()),
                 "n_q_lt_0.1": int((q < 0.1).sum()), "seconds": round(time.time() - t0, 1), "geo": GEO, "surf_ref": [int(s) for s in surf_ref]})
    np.savez_compressed(OUT / f"mesh_{tag}.npz", X=X, T=T, B=B)
    (OUT / f"mesh_{tag}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps({k: info[k] for k in ("n_nodes", "n_tets", "per_body_tets", "q_min", "n_q_lt_0.1", "seconds", "volumes")}), flush=True)
    return info


if __name__ == "__main__":
    cmd = sys.argv[1]
    kw = dict(a.split("=", 1) for a in sys.argv[2:])
    if cmd == "mesh":
        mesh(tag=kw.get("tag", "s1"), h=float(kw.get("h", 0.3)), zcut=float(kw.get("zcut", 97.5)), shift=float(kw.get("shift", 0.24)),
             hmax=float(kw.get("hmax", 3.0)), verbose=kw.get("verbose", "0") == "1", dmax=float(kw.get("dmax", 9.0)),
             members_only=kw.get("members_only", "0") == "1", seat=kw.get("seat", "cad"), brk_r=float(kw.get("brk_r", 0.0)),
             brk_c=float(kw.get("brk_c", 0.0)), h_brk=float(kw.get("h_brk", 0.08)), brk_dmax=float(kw.get("brk_dmax", 0.6)))
