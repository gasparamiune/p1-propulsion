"""Gimbal (Cardan at the mid-burn CG), fixed thrust frame and TVC actuation -- CAD v3 (2026-10-12).

Engine frame (mm): origin = pivot (intersection of the gimbal axes) at neutral, +Z forward (nozzle -> head),
+X = outer axis (ring pins in the fixed yoke posts), +Y = inner axis (collar pins in the ring).
Groups: 'engine' moves with Rx(alpha)Ry(beta); 'ring' with Rx(alpha); 'fixed' does not move;
'horn:i' rotates about servo i's shaft by psi_i; 'pushrod:i' is re-solved per pose (tvc_kinematics);
'lock' (transport lock) exists only in the transport configuration.

Load path (thrust +Z on the engine): case groove shoulders -> split collar (GM-01/02) -> inner pins (GM-04) ->
608 bearings in the ring bosses -> ring (GM-03) -> outer pins (GM-05) -> 608 bearings in the yoke posts
(GM-08) -> upper thrust ring (GM-09, 8 x M5 radial into the airframe) and lower ring (GM-10, 8 x M5 radial).
TVC: servo (GM-15) on its bracket (GM-13/14) on the lower ring -> horn (GM-16) -> dog-bone pushrod
(GM-17, 2 x GE 5 E) -> lever cheek on the collar.  Conical hard stop: PU bumper (GM-11) with an 8 deg
conical bore in the lower ring bore, line contact with the case at the stop angle.

Geometry derivations are in tvc_kinematics.geometry() (servo frames) and in the part notes.  Every radial
clearance quoted in a note is checked numerically in checks/ (interference sweep), not just asserted here.
"""
from __future__ import annotations
import math
import numpy as np
import cadquery as cq
from geom import (revolve, cyl, cyl_dir, tube, box, radial_hole, union_all, cut_all, T_trans, T_rot,
                  T_axis_to, T_basis, apply)
from partlib import Part
import tvc_kinematics as tk

R_CHEEK = 62.5    # v3.3: max radius of the TVC lever cheek on GM-01/02 (sweep: 62.5 cos 8 + 34 sin 8 = 66.6 < 67 = 70 - 3)


def inv(T):
    Ti = np.eye(4)
    R = T[:3, :3]
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -R.T @ T[:3, 3]
    return Ti


def store(shape_global, T_frame):
    """(local shape, placement) for a part modelled in the engine frame: local = T_frame^-1 * global."""
    return apply(shape_global, inv(T_frame)), T_frame


def box_ut(sv, u0, u1, t0, t1, z0, z1):
    """Box given in the servo-centre (u, t, z) frame of servo sv (bounds in any order)."""
    lo = (min(u0, u1), min(t0, t1), min(z0, z1))
    hi = (max(u0, u1), max(t0, t1), max(z0, z1))
    return apply(box(lo, hi), tk.T_ut(sv))


def pt_ut(sv, u, t, z):
    return u * sv["eu"] + t * sv["et"] + z * sv["ez"]


def axial_cyl(d, p0, axis, length):
    return cyl_dir(d, length, p0, axis)


def sector(r_in, r_out, a0_deg, a1_deg, z0, z1, n=24):
    """Annular sector r_in..r_out between azimuths a0..a1 (deg, about +Z), z0..z1 (v3.5.1 lever root)."""
    R = r_out + 5.0
    pts = [(0.0, 0.0)] + [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in np.linspace(a0_deg, a1_deg, n)]
    wedge = cq.Workplane("XY").workplane(offset=z0 - 1.0).polyline(pts).close().extrude(z1 - z0 + 2.0).val()
    return tube(2 * r_out, 2 * r_in, z0, z1).intersect(wedge)


def _edge_pts(e, n=5):
    return [e.positionAt(t).toTuple() for t in np.linspace(0.0, 1.0, n)]


def fillet_sel(solid, R, pred, label, log, retry=(1.0, 0.8, 0.6)):
    """Fillet radius R on every edge of 'solid' whose sample points all satisfy pred(x, y, z); on an OCC failure or an invalid result the
    radius is retried at 0.8 R and 0.6 R, then edge by edge.  Every attempt is logged; a fillet that cannot be made leaves the edge sharp
    and is reported as such (never silently dropped)."""
    edges = [e for e in solid.Edges() if all(pred(*q) for q in _edge_pts(e))]
    if not edges:
        log.append({"fillet": label, "R_mm": R, "n_edges": 0, "status": "NO EDGES SELECTED"})
        return solid
    tried = []
    for f in retry:
        try:
            out = solid.fillet(R * f, edges)
            if out.isValid() and len(out.Solids()) == 1:
                log.append({"fillet": label, "R_mm": round(R * f, 3), "R_requested_mm": R, "n_edges": len(edges), "status": "ok",
                            "dV_mm3": round(out.Volume() - solid.Volume(), 3), "failed_first": tried})
                return out
            tried.append(f"R {R * f:.2f}: invalid")
        except Exception as ex:      # noqa: BLE001
            tried.append(f"R {R * f:.2f}: {type(ex).__name__}")
    # edge by edge at the requested radius, re-selecting after each success
    done = 0
    for _ in range(len(edges)):
        cand = [e for e in solid.Edges() if all(pred(*q) for q in _edge_pts(e))]
        ok = False
        for e in cand:
            try:
                out = solid.fillet(R, [e])
                if out.isValid() and len(out.Solids()) == 1:
                    solid, ok, done = out, True, done + 1
                    break
            except Exception:        # noqa: BLE001
                pass
        if not ok:
            break
    log.append({"fillet": label, "R_mm": R, "n_edges": len(edges), "n_filleted_edge_by_edge": done,
                "status": "ok (edge by edge)" if done == len(edges) else ("PARTIAL: %d of %d edges filleted, rest SHARP" % (done, len(edges))),
                "failed_first": tried})
    return solid


def _frame_from_z(z):
    z = np.array(z, float) / np.linalg.norm(z)
    a = np.array([0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(a, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return x, y, z


def build_gimbal_parts(P, S, reg, info):
    v = lambda k: P[k]["v"] * 1000.0
    g = tk.geometry(P)
    S["tvc"] = g
    R_case = v("case_OD") / 2.0
    rc_in, rc_out = [x * 1000 for x in P["collar_r"]["v"]]           # 31.25, 37.0
    rr_in, rr_out = [x * 1000 for x in P["ring_r"]["v"]]             # 41, 49
    hb = v("ring_band_h") / 2.0                                       # 7
    BD, BB = v("bearing_D"), v("bearing_B")                           # 22, 7
    # v3.5.1 (lead CHANGELOG 182 (2) / 177 (4): C0 >= 1.80 kN per bearing from a maker datasheet): drawn-cup needle roller bearings
    # HK0808 (Fw 8 x D 12 x C 8; C0r 2.60 kN INA HK0808-B / 2.73 kN Koyo HK0808) run directly on hardened 440C pins; axial location by
    # PTFE-composite thrust washers between the bosses (the cups carry no axial load).  BRG = None keeps the v3.5 608 geometry.
    BRG = (P.get("gimbal_bearing") or {}).get("v")
    if BRG == "HK0808":
        BD, BB = 12.0, 8.0
    S["gimbal_brg"] = {"type": BRG or "608", "D": BD, "B": BB}
    cw = v("collar_w") - 0.1                                          # 19.9 (groove 20.0 +0.1/0)
    z_ur0, z_ur1 = [x * 1000 for x in P["frame_upper_z"]["v"]]       # 22, 32
    R_frame = v("engine_bay_ID") / 2.0 - 0.25                         # frame OD 139.5 in the 140 bay
    stop = P["gimbal_stop_deg"]["v"]
    tst = math.tan(math.radians(stop))
    z_s = g["z_s"]
    z_body_bot, z_body_top = z_s - 10.0, z_s + g["L"] - 10.0         # -74.3, -34.0
    z_ear_bot, z_ear_top = z_body_bot - 7.0, z_body_top + 7.0        # -81.3, -27.0
    z_lr1 = z_ear_bot - 2.5                                           # lower ring top = bracket foot  (-83.8)
    z_lr0 = z_lr1 - 10.0                                              # lower ring bottom (-93.8)
    S.update(z_upper_ring=(z_ur0, z_ur1), z_lower_ring=(z_lr0, z_lr1), R_frame=R_frame)
    hH = g["H"] / 2.0
    sv1, sv2 = g["servos"]

    # ======================================================================== GM-01/02 engine collar halves
    opt = lambda k, d=None: (P[k]["v"] if (k in P and P[k].get("v") is not None) else d)
    LV = opt("tvc_lever_v34", None)            # v3.4 stiffening candidate (ENG-11); None = v3.3 geometry
    z_arm1, z_arm0 = -13.0, -17.0                                      # lever arm (top/bottom)
    S["lever_arm_z"] = (z_arm0, z_arm1)
    t_ch0 = g["t_eye"] + 3.0 + 1.5                                       # cheek face: half GE inner ring 3.0 + spacer washer 1.5
    t_ch1 = t_ch0 + (LV.get("cheek_t", 5.0) if LV else 5.0)              # v3.3: cheek 5 thick (M4 x 4.5 engagement)
    S["tvc_cheek_t"] = (t_ch0, t_ch1)
    S["tvc_lever_v34"] = LV

    def collar_half(sy, sv):
        s = sv["s"]
        half = tube(2 * rc_out, 2 * rc_in, -cw / 2, cw / 2)
        half = half.cut(box((-50, -50 if sy > 0 else 0.25, -20), (50, 0.25 if sy > 0 else 50, 20)))   # keep sy*y >= 0.25
        parts = [half, radial_hole(16.0, 90.0 if sy > 0 else 270.0, 0.0, rc_in, 39.0)]                # inner-pin boss
        for xs in (1, -1):                                                                              # clamp bosses at the split
            x0, x1 = (rc_in, 38.5) if xs > 0 else (-38.5, -rc_in)
            parts.append(box((x0, min(sy * 0.25, sy * 7.5), -7.0), (x1, max(sy * 0.25, sy * 7.5), 7.0)))
        ch_c = pt_ut(sv, g["u_eye"], s * (t_ch0 + t_ch1) / 2, 0.0)
        a_ch = math.degrees(math.atan2(ch_c[1], ch_c[0]))
        r_ch = float(np.hypot(ch_c[0], ch_c[1]))
        arm = apply(box((32.5, -4.5, z_arm0), (r_ch + 2.0, 4.5, z_arm1)), T_rot("z", a_ch))
        drop = apply(box((32.5, -4.5, z_arm0), (38.5, 4.5, -cw / 2 + 0.01)), T_rot("z", a_ch))
        hu = LV.get("cheek_half_u", 6.0) if LV else 6.0
        zc0 = g["z_lb"] - (LV.get("cheek_below_eye", 6.0) if LV else 6.0)
        cheek = box_ut(sv, g["u_eye"] - hu, g["u_eye"] + hu, s * t_ch0, s * t_ch1, zc0, z_arm1)
        RV = LV.get("root_v351") if LV else None
        parts += ([arm, cheek] if RV else [arm, drop, cheek])
        if LV and LV.get("web"):
            # v3.4 candidate: tapered radial web under the arm (rho r0..r2 at the arm underside, bottom edge z_bot from r0 to r1)
            w_ = LV["web"]
            r0, r1, r2 = w_["rho"]
            if LV.get("root_v351"):     # v3.5.1: web bottom-outer corner kept 0.5 mm inside the root cylinder (no 0.26 mm sliver at z0)
                r1 = min(r1, LV["root_v351"].get("r_out", 38.5) - 0.5)
            web = (cq.Workplane("XZ").polyline([(r0, z_arm0 + 0.5), (r2, z_arm0 + 0.5), (r1, w_["z_bot"]), (r0, w_["z_bot"])]).close()
                   .extrude(w_.get("half_w", 4.5), both=True).val())
            parts.append(apply(web, T_rot("z", a_ch)))
        if LV and LV.get("cheek_rib"):
            # v3.4 candidate: rib on the back of the cheek (t > t_ch1), in the radial plane through the eye, from the cheek down to
            # the web root: a second load path from the eye region to the collar that stays behind the cheek (clear of the rod eye)
            cr = LV["cheek_rib"]
            rib = box_ut(sv, cr.get("u0", 34.0), g["u_eye"] + hu, s * (t_ch1 - 0.01), s * (t_ch1 + cr.get("t", 6.0)), zc0, z_arm1)
            parts.append(rib)
        # ---- v3.4 candidates V5 (ENG-11, 2026-10-13); every key is optional and absent = v3.3/V4 geometry
        d_az = ((a_ch - sv["phi"] + 180.0) % 360.0) - 180.0
        sgn = 1.0 if d_az > 0 else -1.0                                   # +1: side of the arm away from the eye is +azimuth (servo 1)
        if LV and LV.get("arm_chamfer"):
            # 45 deg chamfer c on the arm top edge on the side away from the eye, rho 38-52 (stop clearance to the ring band bottom)
            c = float(LV["arm_chamfer"])
            yz = [(sgn * (3.5 - c), z_arm1 + 1.0), (sgn * 5.5, z_arm1 + 1.0), (sgn * 5.5, z_arm1 - 1.0 - c)]
            wedge = cq.Workplane("YZ", origin=(38.0, 0, 0)).polyline(yz).close().extrude(14.0).val()
            parts[parts.index(arm)] = arm.cut(apply(wedge, T_rot("z", a_ch)))
        if LV and LV.get("cheek_ext_lo"):
            # cheek extended on the low-u side (away from the eye) to meet the back web; top lowered (under the ring band)
            parts.append(box_ut(sv, g["u_eye"] - LV["cheek_ext_lo"], g["u_eye"] - hu + 0.01, s * t_ch0, s * t_ch1, zc0,
                                LV.get("cheek_ext_ztop", -14.0)))
        if RV:
            # v3.5.1 (lead 183 (4); REV-MECH-1 RM1-07): the lever root is ONE annular sector r_in..r_out over a_ch +/- half_ang from z0
            # up to the band bottom, replacing the v3.4 'drop' box (its outer corners stood 0.26 mm proud of the flare cylinder r 38.5:
            # LC3 single-node peak 289-332 MPa at its junction with the arm top) and the box-shaped flare, whose planar inner face left
            # the back-web corner 0.75 mm proud of it (LC3 hot spot 273-287 MPa at the band bottom).  Inner face cylindrical r 32.5
            # (0.75 mm to the case OD r 31.75), outer face flush with the old flare r 38.5; fillets applied after the cuts (below).
            parts.append(sector(RV.get("r_in", 32.5), RV.get("r_out", 38.5), a_ch - RV.get("half_ang", 16.0), a_ch + RV.get("half_ang", 16.0),
                                RV.get("z0", -34.0), -cw / 2 + 0.01))
        elif LV and LV.get("root_flare"):
            # root widened in plan under the collar band (rho 32.5..r1, +/- half_w, z0..band bottom), outer face cylindrical at r1
            rf_ = LV["root_flare"]
            fl = box((32.5, -rf_["half_w"], rf_["z0"]), (rf_["r1"] + 5.0, rf_["half_w"], -cw / 2 + 0.01)).intersect(cyl(2 * rf_["r1"], -60.0, 0.0))
            parts.append(apply(fl, T_rot("z", a_ch)))
        if LV and LV.get("back_web"):
            # vertical plate in the radial plane az_off away from the arm (clear of the pushrod eye), root -> cheek, full depth;
            # top z_top under the ring band, rising to z_fin outboard of r_fin (outside the ring band)
            bw = LV["back_web"]
            a_bw = a_ch + sgn * bw["az_off"]
            r0b, r1b, rti = bw.get("r0", 32.5), bw["r1"], bw.get("r_top_in", 38.5)
            prof = [(r0b, bw["z_bot"]), (r1b, bw["z_bot"])]
            if bw.get("z_fin") is not None and bw.get("r_fin", 99.0) < r1b:
                prof += [(r1b, bw["z_fin"]), (bw["r_fin"], bw["z_fin"]), (bw["r_fin"], bw["z_top"])]
            else:
                prof += [(r1b, bw["z_top"])]
            prof += [(rti, bw["z_top"]), (rti, -cw / 2 + 0.01), (r0b, -cw / 2 + 0.01)]
            web2 = cq.Workplane("XZ").polyline(prof).close().extrude(bw["t"] / 2.0, both=True).val()
            web2 = apply(web2, T_rot("z", a_bw))
            if LV.get("root_v351"):     # v3.5.1: the planar web end rti stood up to 0.12 mm outside the root cylinder above z_top: trimmed
                web2 = web2.cut(tube(2 * (bw.get("r_fin", 99.0) - 0.05), 2 * LV["root_v351"].get("r_out", 38.5), bw["z_top"], -cw / 2 + 0.05))
            parts.append(web2)
            S.setdefault("tvc_back_web", {})[sv["i"]] = {"az_deg": a_bw, "t": bw["t"]}
        body = union_all(parts)
        cuts = [cyl(2 * rc_in, -cw, cw), cyl_dir(8.0, 6.5, (0.0, sy * 33.0, 0.0), (0.0, sy, 0.0))]  # bore; pin 8 P7 blind r 33-39.5
        for xs in (1, -1):
            for zz in (-4.0, 4.0):
                x = xs * 34.9
                if sy > 0:   # clearance + counterbore for DIN 7984 M3 (head 5.5 x 2)
                    cuts += [cyl_dir(3.4, 8.0, (x, 0.0, zz), (0, 1, 0)), cyl_dir(6.0, 3.0, (x, 7.5 - 2.2, zz), (0, 1, 0))]
                else:        # M3 tapped
                    cuts.append(cyl_dir(2.5, 8.0, (x, -8.0, zz), (0, 1, 0)))
        cuts.append(axial_cyl(3.3, pt_ut(sv, g["u_eye"], s * (t_ch0 - 0.5), g["z_lb"]), s * sv["et"], t_ch1 - t_ch0 + 1.0 +
                              (LV["cheek_rib"].get("t", 6.0) if (LV and LV.get("cheek_rib")) else 0.0)))  # M4 tapped through (pivot stud)
        # v3.3: outer corner of the lever cheek trimmed to R_CHEEK about the engine axis (v3.2 sweep: cheek corner r 65.2 at
        # z -34 swept to r 69.3 at the 8 deg stop = 0.7 mm to the 140 mm bay wall; moving parts need 3 mm)
        cuts.append(tube(2 * R_CHEEK + 60.0, 2 * R_CHEEK, -60.0, 10.0))
        out = cut_all(body, cuts)
        if RV:
            ca, sa = math.cos(math.radians(a_ch)), math.sin(math.radians(a_ch))
            r_i, r_o, ha = RV.get("r_in", 32.5), RV.get("r_out", 38.5), RV.get("half_ang", 16.0)
            zb = -cw / 2                                                                        # band bottom -9.95

            def yp(x, y):                                                                       # tangential coordinate in the a_ch frame
                return -x * sa + y * ca

            def az_off(x, y):
                return ((math.degrees(math.atan2(y, x)) - a_ch + 180.0) % 360.0) - 180.0
            flog = []
            z0r = RV.get("z0", -34.0)
            # (3) band OD r 37 / root top face (z = zb + 0.01)
            out = fillet_sel(out, RV.get("R_od", 1.0), lambda x, y, z: abs(math.hypot(x, y) - rc_out) < 0.03 and abs(z - zb - 0.01) < 0.03 and
                             abs(az_off(x, y)) < ha + 0.5, "band_od/root_top", flog)
            # (1) root side faces (radial planes at a_ch +/- half_ang) / band bottom
            out = fillet_sel(out, RV.get("R_side", 1.5), lambda x, y, z: abs(z - zb) < 0.03 and r_i - 0.6 <= math.hypot(x, y) <= rc_out + 0.1 and
                             abs(abs(az_off(x, y)) - ha) < 0.6, "root_side/band", flog)
            # (2) root inner face r_in / band bottom: R limited by the 0.75 mm gap to the case OD r 31.75
            out = fillet_sel(out, RV.get("R_in", 0.5), lambda x, y, z: abs(math.hypot(x, y) - r_i) < 0.03 and abs(z - zb) < 0.03, "root_in/band", flog)
            # (4) arm top + arm/web side face / root outer face r_out on the eye side of the arm (flat arm top: the v3.5 LC3 governing
            #     junction); the far side (arm chamfer meeting the back web) is left as modelled and reported (no fillet)
            def arm_chain(x, y, z):
                return (abs(math.hypot(x, y) - r_o) < 0.03 and z0r - 0.1 <= z <= z_arm1 + 0.05 and -4.6 <= sgn * yp(x, y) <= 1.6)
            out = fillet_sel(out, RV.get("R_arm", 1.5), arm_chain, "arm_top+side/root (eye side)", flog)
            S.setdefault("collar_root_v351_fillets", {})[sv["i"]] = flog
        return out

    for pn, sy, sv, nm in (("ENG-GM-01", +1, sv1, "+Y (servo 1 lever, 135 deg)"), ("ENG-GM-02", -1, sv2, "-Y (servo 2 lever, 225 deg), mirror of GM-01")):
        reg.add(Part(pn, f"Engine collar half {nm}", "AL7075-T6", "CNC mill (pair machined as one ring, then split)", collar_half(sy, sv), drawing=True,
                     notes=f"v3.5: 7075-T6 (was 6061-T6; S-3D v1.1 + FA-1 spike margins), all internal corners R >= 2 (drawing note); bore {2*rc_in:.2f} H9 in the case groove (62.50 h9 x 20.0), width {cw:.1f} -0.05; OD {2*rc_out:.0f}; inner-pin boss 16 mm "
                           f"with 8 P7 x 6.5 blind; 2 clamp bosses with 2x M3 DIN 7984 each (4 total, 1.0 N m); TVC lever cheek with M4 x 5 thread "
                           f"for the pivot stud at r_e {g['r_e']:.1f} mm, z {g['z_lb']:.1f}; arm z {z_arm0:.0f}..{z_arm1:.0f}",
                     dwg={"datum": "bore A, split face B, upper face C", "fits": ["bore 62.50 H9 (+0.074/0)", "width 19.90 -0.05/-0.10",
                                                                              "pin bore 8 P7 (-0.009/-0.024), position 0.02 to A", "M4-6H in the cheek, perpendicular 0.05"],
                          "finish": "clear anodise Type II", "ht": "T6"})).place(np.eye(4), "engine")

    # ======================================================================== GM-03 gimbal ring
    zr0, zr1 = opt("ring_band_z", [-hb, hb])                         # v3.4 candidate: taller band (grows upward)
    S["ring_band_z"] = (zr0, zr1)
    # v3.4.1: band OD 0.2 mm below the boss faces (the four bosses stand 0.2 mm proud, functional faces unchanged at r_out).  With the band
    # OD equal to the boss-face radius the flat boss ends were tangent to the band cylinder and the STEP re-import gave an invalid shell
    # (make_all v3.4.1 first run: ENG-GM-03 0 solids; kept in the log)
    band = tube(2 * (rr_out - 0.2), 2 * rr_in, zr0, zr1)
    lip = opt("ring_lip", None)                                       # v3.4 candidate: inward lip on the band top {z0, r_in}
    if lip:
        band = band.fuse(tube(2 * rr_in + 0.2, 2 * lip["r_in"], lip["z0"], zr1))
    if BRG == "HK0808":   # inner-axis boss 17.5 (12 N7 cup seat + 2.75 walls), face 0.5 mm proud of r_out so the 8 mm cup sits flush
        bosses = [radial_hole(17.5, a, 0.0, rr_in - 0.4, rr_out + 0.5) for a in (90.0, 270.0)]
    else:
        bosses = [radial_hole(27.0, a, 0.0, rr_in - 0.4, rr_out) for a in (90.0, 270.0)]
    bosses += [radial_hole(18.0, a, 0.0, rr_in - 0.4, rr_out) for a in (0.0, 180.0)]
    ring = union_all([band] + bosses).cut(cyl(2 * (lip["r_in"] if lip else rr_in), -30, 30))
    if lip:
        ring = ring.cut(cyl(2 * rr_in, -30, lip["z0"]))
    if BRG == "HK0808":   # v3.5.1 freeze fix (make_all attempt 2, 16:58Z: GM-03/GM-06 common 0.5 mm3 at both inner bosses, not whitelisted):
        # the band bore cut (r 41 about Z) removed the flat inner boss face r 40.6 that the thrust washer GM-06 bears on, so the 14 mm washer
        # rim met the curved bore (r 41 at x = 6.1-7 mm sits at y 40.40-40.55).  Flat seat face at r 40.6 over Ø16: land added where the
        # bore lies outside 40.6 (|x| < 5.7) and spot face cut where it lies inside (|x| 5.7-8, <= 0.39 mm deep); 0.05 mm axial play to the
        # washer at r 39.05-40.55 (select fit / shim +/-0.05 as before); the 10.5 pin clearance hole and the cup seat are cut after it
        ring = union_all([ring] + [radial_hole(16.0, a, 0.0, rr_in - 0.4, rr_in + 0.5) for a in (90.0, 270.0)])
        ring = cut_all(ring, [radial_hole(16.0, a, 0.0, rr_in - 2.5, rr_in - 0.4) for a in (90.0, 270.0)])
    rcut = []
    for a in (90.0, 270.0):
        if BRG == "HK0808":   # cup seat 12 N7 r 41.5-49.5 (flush with the boss face), shoulder r 40.6-41.5 with a 10.5 pin clearance hole
            rcut += [radial_hole(BD, a, 0.0, rr_in + 0.5, rr_out + 1.0), radial_hole(10.5, a, 0.0, rr_in - 1.0, rr_in + 0.51)]
        else:
            rcut += [radial_hole(BD, a, 0.0, rr_in + 1.0, rr_out + 1.0), radial_hole(15.0, a, 0.0, rr_in - 1.0, rr_in + 1.01)]
    for a in (0.0, 180.0):
        rcut.append(radial_hole(8.0, a, 0.0, rr_in - 1.0, rr_out + 1.0))
    for a in (70.0, 110.0):                                                                # EL-03 holder: 2x M2 tapped radial
        rcut.append(radial_hole(1.6, a, 0.0, rr_out - 5.0, rr_out + 0.5))
    ring = cut_all(ring, rcut)
    reg.add(Part("ENG-GM-03", "Gimbal ring (Cardan)", "AL6061-T6", "CNC mill + 4th-axis boring (from 100 mm bar or 16 mm plate)", ring, drawing=True,
                 notes=(f"band r {rr_in:.0f}-{rr_out:.0f} x {2*hb:.0f}; " + ("HK0808 cup seats 12 N7 x 8 at +/-Y (bosses 17.5, shoulder 10.5), "
                        "thrust washers on the inner boss faces; " if BRG == "HK0808" else "608 seats 22 K7 x 7 at +/-Y with 15 mm shoulder (cross-located pair); ")
                        + "outer pins pressed 8 P7 at +/-X; 2x M2 for the EL-03 holder"),
                 dwg={"datum": "bearing-seat axis A (Y), pin axis B (X), mid-plane C", "fits": [("cup seats 12 N7 (-0.005/-0.023) coaxial 0.01" if BRG == "HK0808" else "bearing seats 22 K7 (+0.006/-0.015) coaxial 0.01"),
                                                                                           "pin bores 8 P7 coaxial 0.01, perpendicular to A 0.02, intersecting A within 0.02"],
                      "finish": "clear anodise Type II, seats masked", "ht": "T6"})).place(np.eye(4), "ring")

    # ======================================================================== pins, spacers, bearings, clips, encoders
    def pin_shape(Lpin, groove_at):
        return cyl(8.0, 0.0, Lpin).cut(tube(9.0, 6.0, groove_at, groove_at + 0.74))

    def along(r0, a_deg):          # placement: local +Z -> radial direction at azimuth a, local origin at radius r0
        a = math.radians(a_deg)
        d = (math.cos(a), math.sin(a), 0.0)
        return T_trans(r0 * d[0], r0 * d[1], 0.0) @ T_axis_to(d)

    r_pin_in0, r_brg_in = 33.0, rr_in + (0.5 if BRG == "HK0808" else 1.0)   # inner pin starts in the collar boss; bearing 42-49 (HK0808 41.5-49.5)
    r_clip_in = r_brg_in + BB + 0.1
    if BRG == "HK0808":
        reg.add(Part("ENG-GM-04", "Inner pivot pin 8 h5 x 18, needle raceway (AISI 440C, 58-62 HRC)", "SS440C-HT", "CNC lathe, harden, ground h5",
                     pin_shape(18.0, r_clip_in - r_pin_in0), drawing=True,
                     notes="pressed (8 P7) + Loctite 648 into the collar boss; runs in the HK0808 cup in the ring (raceway 58-62 HRC, Ra 0.2, "
                           "Schaeffler drawn-cup shaft rule); DIN 6799-6 clip; +Y pin end carries the EL-03 magnet",
                     dwg={"datum": "axis A", "fits": ["8 h5 (0/-0.006) Ra 0.2 raceway, roundness 0.0015", "groove 6.0 h11 x 0.74 H13 per DIN 6799"],
                          "finish": "passivate", "ht": "harden + temper 58-62 HRC (AISI 440C)"}))
    else:
        reg.add(Part("ENG-GM-04", "Inner pivot pin 8 h6 x 18 (17-4PH H1150)", "SS17-4PH-H1150", "CNC lathe, ground h6", pin_shape(18.0, r_clip_in - r_pin_in0),
                     drawing=True, notes="pressed (8 P7) + Loctite 648 into the collar boss through the ring bearing; DIN 6799-6 clip; +Y pin end carries the EL-03 magnet",
                     dwg={"datum": "axis A", "fits": ["8 h6 (0/-0.009) Ra 0.4", "groove 6.0 h11 x 0.74 H13 per DIN 6799"], "finish": "passivate", "ht": "H1150"}))
    for a in (90.0, 270.0):
        reg.parts["ENG-GM-04"].place(along(r_pin_in0, a), "engine")
    r_pin_out0 = rr_in + 0.5
    r_brg_out = rr_out + (1.5 if BRG == "HK0808" else 2.0)         # 51-58 in the post (HK0808: cup 50.5-58.5 flush with the post inner face)
    S["gimbal_brg"].update({"r_in0": r_brg_in, "r_out0": r_brg_out, "rr_in": rr_in, "rr_out": rr_out})
    r_clip_out = r_brg_out + BB + 0.1
    if BRG == "HK0808":
        reg.add(Part("ENG-GM-05", "Outer pivot pin 8 h5 x 18.5, needle raceway (AISI 440C, 58-62 HRC)", "SS440C-HT", "CNC lathe, harden, ground h5",
                     pin_shape(18.5, r_clip_out - r_pin_out0), drawing=True,
                     notes="pressed (8 P7) + Loctite 648 into the ring boss; runs in the HK0808 cup in the post (raceway 58-62 HRC, Ra 0.2); "
                           "DIN 6799-6 clip; -X pin end carries the EL-04 magnet",
                     dwg={"datum": "axis A", "fits": ["8 h5 (0/-0.006) Ra 0.2 raceway", "groove 6.0 h11 x 0.74 H13"], "finish": "passivate",
                          "ht": "harden + temper 58-62 HRC (AISI 440C)"}))
    else:
        reg.add(Part("ENG-GM-05", "Outer pivot pin 8 h6 x 18.5 (17-4PH H1150)", "SS17-4PH-H1150", "CNC lathe, ground h6", pin_shape(18.5, r_clip_out - r_pin_out0),
                     drawing=True, notes="pressed (8 P7) + Loctite 648 into the ring boss through the post bearing; DIN 6799-6 clip; -X pin end carries the EL-04 magnet",
                     dwg={"datum": "axis A", "fits": ["8 h6 (0/-0.009) Ra 0.4", "groove 6.0 h11 x 0.74 H13"], "finish": "passivate", "ht": "H1150"}))
    for a in (0.0, 180.0):
        reg.parts["ENG-GM-05"].place(along(r_pin_out0, a), "ring")
    if BRG == "HK0808":   # thrust washers (PTFE composite on a steel/bronze back): collar boss face r 39 -> ring boss inner face r 40.6;
        # ring +/-X boss face r 49 -> post inner face r 50.5; they carry the axial loads (the drawn cups carry none)
        tw = "PTFE-composite thrust washer (steel back, bronze sinter + PTFE; SKF PCMW / GGB DU class, TO-SELECT), select fit / shim to +/-0.05"
        reg.add(Part("ENG-GM-06", "Inner-axis thrust washer 8.1/14 x 1.5 (PTFE composite)", "SS304", "COTS (TO-SELECT)", tube(14.0, 8.1, 0.0, 1.5),
                     cots=True, mass_each_kg=0.0012, mass_tag="ESTIMATE annulus x 7.5 g/cm3", price="TO-QUOTE",
                     notes="collar boss face (r 39) to the ring boss inner face (r 40.6); " + tw))
        for a in (90.0, 270.0):
            reg.parts["ENG-GM-06"].place(along(39.05, a), "engine")
        reg.add(Part("ENG-GM-07", "Outer-axis thrust washer 8.1/14 x 1.4 (PTFE composite)", "SS304", "COTS (TO-SELECT)", tube(14.0, 8.1, 0.0, 1.4),
                     cots=True, mass_each_kg=0.0011, mass_tag="ESTIMATE annulus x 7.5 g/cm3", price="TO-QUOTE",
                     notes="ring boss face (r 49) to the post inner face (r 50.5); " + tw))
        for a in (0.0, 180.0):
            reg.parts["ENG-GM-07"].place(along(rr_out + 0.05, a), "ring")
    else:
        reg.add(Part("ENG-GM-06", "Inner-axis spacer sleeve 11/8.1 x 2.85 (304)", "SS304", "lathe from tube", tube(11.0, 8.1, 0.0, r_brg_in - 39.0 - 0.1),
                     notes="collar boss face (r 39) to the 608 inner ring; centres the collar in the ring (select fit / shim to +/-0.05)"))
        for a in (90.0, 270.0):
            reg.parts["ENG-GM-06"].place(along(39.05, a), "engine")
        reg.add(Part("ENG-GM-07", "Outer-axis spacer sleeve 11/8.1 x 1.9 (304)", "SS304", "lathe from tube", tube(11.0, 8.1, 0.0, r_brg_out - rr_out - 0.1),
                     notes="ring boss face (r 49) to the 608 inner ring in the post"))
        for a in (0.0, 180.0):
            reg.parts["ENG-GM-07"].place(along(rr_out + 0.05, a), "ring")
    if BRG == "HK0808":
        reg.add(Part("ENG-HW-20", "Drawn-cup needle roller bearing HK0808 (Fw 8 x D 12 x C 8), open ends", "STEEL", "COTS", tube(BD, 8.0, 0.0, BB), cots=True,
                     mass_each_kg=0.003, mass_tag="DATASHEET Koyo HK0808 0.003 kg (koyo.jtekt.co.jp product page, accessed 2026-10-13)",
                     supplier="INA HK0808-B: RS Components (RS 137-1723, GBP 5.16 ex VAT each, 2026-10-13); price shipped to Sonderborg DK-6400 TO-QUOTE",
                     supplier_pn="HK0808-B", price="TO-QUOTE",
                     notes="C0r 2.60 kN / Cr 2.75 kN (INA HK0808-B, RS 137-1723 page, accessed 2026-10-13); C0r 2.73 kN / Cr 2.90 kN (Koyo HK0808 product "
                           "page, accessed 2026-10-13); requirement C0 >= 1.80 kN per bearing (lead 182 (2)): MS +0.44 on the INA value. Ratings need a "
                           "raceway of 58-64 HRC (pins 440C hardened). Cups pressed N7, flush; axial loads on the PTFE-composite thrust washers GM-06/07. "
                           "Maker datasheet PDF to be filed at purchase (TO-VERIFY)"))
    else:
        reg.add(Part("ENG-HW-20", "Deep-groove ball bearing 608-2RS (8x22x7)", "STEEL", "COTS", tube(BD, 8.0, 0.0, BB), cots=True, mass_each_kg=0.012,
                     mass_tag="DATASHEET SKF 608-2RSH 0.012 kg (verify)", supplier="SKF 608-2RSH: RS Components DK / Simply Bearings", supplier_pn="608-2RSH",
                     notes="C 3.45 kN, C0 1.37 kN (SKF, verify); inner pair in the ring, outer pair in the yoke posts; cross-located (shoulder inside, open outside)"))
    for a in (90.0, 270.0):
        reg.parts["ENG-HW-20"].place(along(r_brg_in, a), "ring")
    for a in (0.0, 180.0):
        reg.parts["ENG-HW-20"].place(along(r_brg_out, a), "fixed")
    reg.add(Part("ENG-HW-21", "Retaining washer DIN 6799-6 (shaft 7-9 mm), spring steel", "STEEL", "COTS", tube(12.3, 6.0, 0.0, 0.7), cots=True, mass_each_kg=0.0003,
                 mass_tag="ASSUMED 0.2-0.4 g", supplier="Bossard DK / RS Components DK", supplier_pn="DIN 6799 RS6"))
    for a in (90.0, 270.0):
        reg.parts["ENG-HW-21"].place(along(r_clip_in, a), "engine")
    for a in (0.0, 180.0):
        reg.parts["ENG-HW-21"].place(along(r_clip_out, a), "ring")
    reg.add(Part("ENG-EL-06", "Diametral NdFeB magnet 6 x 2.5 (AS5048A), bonded on the pin end", "NDFEB", "COTS", cyl(6.0, 0.0, 2.5), cots=True, mass_each_kg=0.0005,
                 mass_tag="DERIVED 6 x 2.5 mm x 7.5 g/cm3", supplier="ams AS5048 evaluation magnet / Magnet-Shop DK", supplier_pn="diametral 6x2.5 N35",
                 notes="Loctite AA 3090; centred on the pin axis within 0.25 mm"))
    reg.parts["ENG-EL-06"].place(along(r_pin_in0 + 18.0, 90.0), "engine")         # inner axis (+Y pin end): engine moves vs ring sensor
    reg.parts["ENG-EL-06"].place(along(r_pin_out0 + 18.5, 180.0), "ring")          # outer axis (-X pin end): ring moves vs fixed sensor
    enc = cyl(20.0, 0.0, 2.8)
    reg.add(Part("ENG-EL-03", "Gimbal encoder, inner axis (beta): AS5048A on a round PCB 20 x 2.8 (REQUEST to Electronics)", "COTS-MIXED", "COTS/custom PCB",
                 enc, cots=True, mass_each_kg=0.003, mass_tag="ASSUMED 2-5 g incl. holder", supplier="ams AS5048A on custom 20 mm PCB (Electronics)",
                 notes="rides on the ring (+Y boss) facing the inner-pin magnet, air gap 0.5-1.5 mm; electronics.json reservation 25x25x10 does NOT fit (upper ring at z 22)"))
    reg.parts["ENG-EL-03"].place(along(r_pin_in0 + 18.0 + 2.5 + 0.8, 90.0), "ring")
    reg.add(Part("ENG-EL-04", "Gimbal encoder, outer axis (alpha): AS5048A on a round PCB 20 x 2.8 recessed in the -X post bore (REQUEST to Electronics)",
                 "COTS-MIXED", "COTS/custom PCB", enc, cots=True, mass_each_kg=0.003, mass_tag="ASSUMED 2-5 g", supplier="ams AS5048A on custom 20 mm PCB (Electronics)",
                 notes="fixed; faces the outer-pin magnet; 25x25x10 reservation does NOT fit (servo/bay corner r 68.75)"))
    reg.parts["ENG-EL-04"].place(along(r_pin_out0 + 18.5 + 2.5 + 0.8, 180.0), "fixed")

    # ======================================================================== GM-08 yoke posts (x2)
    x_p0, x_p1 = rr_out + (1.5 if BRG == "HK0808" else 1.0), 66.0   # inner face 50 (1 mm to the ring boss; HK0808 50.5: 1.4 mm thrust washer), outer face 66
    post = box((x_p0, -14.0, z_lr1), (x_p1, 14.0, z_ur0))
    if BRG == "HK0808":   # cup seat 12 N7 r 50.5-58.5 from the inner face, then a 21 mm recess to the outer face (clip, magnet, EL-04 PCB)
        seat_cuts = [radial_hole(BD, 0.0, 0.0, x_p0 - 1.0, r_brg_out + BB), radial_hole(21.0, 0.0, 0.0, r_brg_out + BB - 0.01, x_p1 + 1.0)]
    else:
        seat_cuts = [radial_hole(BD, 0.0, 0.0, r_brg_out, x_p1 + 1.0), radial_hole(15.0, 0.0, 0.0, x_p0 - 1.0, r_brg_out + 0.01)]
    pcut = seat_cuts + [
            box((x_p0 + 4.0, -10.0, z_lr1 + 7.0), (x_p1 + 1.0, 10.0, -16.0)),          # outer-face pocket (U section)
            box((x_p0 + 4.0, -10.0, 16.0), (x_p1 + 1.0, 10.0, z_ur0 - 5.0)),
            box((x_p1 - 3.0, -1.5, -16.0), (x_p1 + 1.0, 1.5, 16.0))]                     # EL-04 cable slot (on both, used at -X)
    for y in (-8.0, 8.0):
        pcut += [cyl(4.2, z_ur0 - 12.0, z_ur0 + 1.0, 58.0, y), cyl(4.2, z_lr1 - 1.0, z_lr1 + 12.0, 58.0, y)]       # M5 tapped top/bottom
    pcut += [cyl(4.0, z_ur0 - 8.0, z_ur0 + 1.0, 62.5, 0.0), cyl(4.0, z_lr1 - 1.0, z_lr1 + 8.0, 62.5, 0.0)]          # dowel 4 m6 holes
    post = cut_all(post, pcut)
    reg.add(Part("ENG-GM-08", "Yoke post (outer-axis bearing housing + frame post), x2", "AL6061-T6", "CNC mill from 20 x 30 bar (3 setups)", post, drawing=True,
                 notes=(f"HK0808 cup seat 12 N7 x 8 at r {r_brg_out:.1f}-{r_brg_out+BB:.1f} flush with the inner face, 21 mm outer recess; " if BRG == "HK0808" else
                        f"608 seat 22 K7 x 7 at r {r_brg_out:.0f}-{r_brg_out+BB:.0f} with 15 mm shoulder; ") + "2x M5 + 1 dowel 4 m6 each end; "
                       f"posts tie the upper ring (z {z_ur0:.0f}) to the lower ring (z {z_lr1:.1f}); inner face r {x_p0:.0f}",
                 dwg={"datum": "bearing axis A, top face B", "fits": [("12 N7 cup seat" if BRG == "HK0808" else "22 K7 seat"), "dowel holes 4 H7", "top/bottom faces parallel 0.02, distance +/-0.02"],
                      "finish": "clear anodise", "ht": "T6"})).place(np.eye(4), "fixed").place(T_rot("z", 180.0), "fixed")

    # ======================================================================== GM-09 upper thrust ring
    ur = tube(2 * R_frame, 104.0, z_ur0, z_ur1)
    ucut = [radial_hole(4.2, 22.5 + 45.0 * k, (z_ur0 + z_ur1) / 2, R_frame - 11.0, R_frame + 1.0) for k in range(8)]   # M5 x 10 radial (airframe)
    for xs in (1, -1):
        for y in (-8.0, 8.0):
            ucut += [cyl(5.5, z_ur0 - 1, z_ur1 + 1, xs * 58.0, y), cyl(9.5, z_ur1 - 5.5, z_ur1 + 1, xs * 58.0, y)]
        ucut.append(cyl(4.0, z_ur0 - 1, z_ur1 + 1, xs * 62.5, 0.0))
    for a in (45.0, 90.0, 135.0, 225.0, 270.0, 315.0):                                                      # lightening pockets from the top
        ucut.append(apply(box((55.0, -9.0, z_ur0 + 3.0), (R_frame - 4.0, 9.0, z_ur1 + 1.0)), T_rot("z", a)))
    ur = cut_all(ur, ucut)
    reg.add(Part("ENG-GM-09", "Upper thrust ring (engine module to airframe, thrust path)", "AL6061-T6", "CNC mill from 12 mm plate", ur, drawing=True,
                 notes=f"OD {2*R_frame:.1f} h9 in the {v('engine_bay_ID'):.0f} mm bay; ID 104; 8x M5 radial tapped at 22.5+45k deg (ICD-AIRFRAME); "
                       "4x M5 counterbored + 2 dowels to the yoke posts; 6 pockets",
                 dwg={"datum": "bottom face A, OD B", "fits": [f"OD {2*R_frame:.1f} h9", "post hole pattern position 0.03 to B", "dowel 4 H7"],
                      "finish": "clear anodise", "ht": "T6"})).place(np.eye(4), "fixed")

    # ======================================================================== GM-10 lower ring + GM-11 bumper + GM-12 transport lock
    r_lr_in = 48.0
    lr = tube(2 * R_frame, 2 * r_lr_in, z_lr0, z_lr1)
    lcut = [radial_hole(4.2, 22.5 + 45.0 * k, (z_lr0 + z_lr1) / 2, R_frame - 11.0, R_frame + 1.0) for k in range(8)]
    for xs in (1, -1):
        for y in (-8.0, 8.0):
            lcut += [cyl(5.5, z_lr0 - 1, z_lr1 + 1, xs * 58.0, y), cyl(9.5, z_lr0 - 1, z_lr0 + 5.5, xs * 58.0, y)]
        lcut.append(cyl(4.0, z_lr0 - 1, z_lr1 + 1, xs * 62.5, 0.0))
    foot_pts = []
    for sv in g["servos"]:
        s = sv["s"]
        for t_ in (-12.0, -26.0):
            for u_ in (52.5, 59.0):
                p = pt_ut(sv, u_, s * t_, 0.0)
                foot_pts.append(p)
                lcut += [cyl(4.5, z_lr0 - 1, z_lr1 + 1, p[0], p[1]), cyl(8.0, z_lr0 - 1, z_lr0 + 4.5, p[0], p[1])]
    for a in (45.0, 315.0):
        lcut.append(apply(box((53.0, -9.0, z_lr0 - 1.0), (R_frame - 4.0, 9.0, z_lr1 - 3.0)), T_rot("z", a)))
    lr = cut_all(lr, lcut)
    reg.add(Part("ENG-GM-10", "Lower ring (stop ring, TVC servo base, frame tie)", "AL6061-T6", "CNC mill from 12 mm plate", lr, drawing=True,
                 notes=f"OD {2*R_frame:.1f} h9; bore {2*r_lr_in:.0f} H9 for the bonded PU bumper; 8x M5 radial (airframe); 4x M5 to the posts; "
                       "8x M4 counterbored from below to the TVC brackets",
                 dwg={"datum": "top face A, bore B", "fits": [f"OD {2*R_frame:.1f} h9", "bore 96.0 H9", "bracket pattern position 0.05 to B"],
                      "finish": "clear anodise", "ht": "T6"})).place(np.eye(4), "fixed")
    S["tvc_foot_pts"] = foot_pts
    rb = lambda z: R_case / math.cos(math.radians(stop)) + abs(z) * tst      # case generatrix radius at the stop
    bump = revolve([(rb(z_lr1), z_lr1), (r_lr_in, z_lr1), (r_lr_in, z_lr0), (rb(z_lr0), z_lr0)])
    S["stop_bumper"] = {"z": (z_lr0, z_lr1), "r_contact": (rb(z_lr1), rb(z_lr0)), "stop_deg": stop}
    reg.add(Part("ENG-GM-11", f"Conical stop bumper, PU 90A, {stop:.0f} deg line contact", "ELASTOMER-PU", "cast or turned from PU 90A tube", bump,
                 supplier="PU 90A tube 100 x 80: Kubo / RS Components DK (TO-QUOTE)",
                 notes=f"bore cone r {rb(z_lr1):.2f}->{rb(z_lr0):.2f} matches the case generatrix at {stop:.0f} deg (line contact over 10 mm); "
                       "bonded with PU adhesive; replace after any hard-stop event above the stall moment")).place(np.eye(4), "fixed")
    lk = revolve([(R_case + 0.15, z_lr1 + 6.0), (rb(z_lr1) - 0.3, z_lr1 + 6.0), (rb(z_lr1) - 0.3, z_lr1), (rb(z_lr0) - 0.3, z_lr0),
                  (R_case + 0.15, z_lr0)])
    lk = lk.cut(box((-1.0, -60.0, z_lr0 - 1.0), (1.0, 60.0, z_lr1 + 7.0)))
    reg.add(Part("ENG-GM-12", "Transport / neutral lock, 2 half rings (REMOVE BEFORE FLIGHT)", "PETG", "FDM print PETG", lk,
                 petg={"orientation": "flat, ring axis vertical", "infill": "40 %, 4 perimeters", "note": "this part IS printed PETG (cold, not flight-loaded)"},
                 notes="fills the case-to-bumper gap; red streamer; transport and locked-gimbal static fires (servos unpowered)")).place(np.eye(4), "lock")

    # ======================================================================== TVC: brackets, servos, horns, pushrods, studs, bearings
    L, W, H = g["L"], g["W"], g["H"]
    u_in, u_out, u_sh = g["u_in"], g["u_out"], g["u_sh"]
    t_ear = hH - 13.5                                                    # ear underside plane (6.65)
    rail_t0, rail_t1 = -(hH + 0.4), -(hH + 11.5)                        # back rail behind the body
    for pn, sv in (("ENG-GM-13", sv1), ("ENG-GM-14", sv2)):
        s = sv["s"]
        top = box_ut(sv, u_in, u_out, s * rail_t1, s * t_ear, z_body_top + 0.3, z_ear_top + 2.5)
        bot = box_ut(sv, 46.0, u_out, s * rail_t1, s * t_ear, z_lr1, z_body_bot - 0.3)
        rail = box_ut(sv, 46.5, 58.0, s * rail_t0, s * rail_t1, z_lr1, z_ear_top + 2.5)
        br = union_all([top, bot, rail]).intersect(cyl(2 * g["R_lim"], -200, 200))
        bcut = [box_ut(sv, 40.0, 48.5, s * (rail_t1 - 1), s * (t_ear + 1), z_lr1 - 1, z_lr1 + 0.5)]                    # relief over the bumper
        for zz in (z_s + 34.9, z_s - 14.6):
            for du in (-5.0, 5.0):
                bcut.append(axial_cyl(3.3, pt_ut(sv, u_sh + du, s * (t_ear + 0.5), zz), -s * sv["et"], 10.5))           # M4 ear screws, tapped 10 deep
        for t_ in (-12.0, -26.0):
            for u_ in (52.5, 59.0):
                p = pt_ut(sv, u_, s * t_, 0.0)
                bcut.append(cyl(3.3, z_lr1 - 1, z_lr1 + 10.0, p[0], p[1]))                                              # M4 tapped from below
        br = cut_all(br, bcut)
        shp, T = store(br, tk.T_ut(sv, origin=np.array([0.0, 0.0, z_lr1])))
        reg.add(Part(pn, f"TVC servo {sv['i']} bracket ({'mirror of GM-13' if s < 0 else 'C-frame: top/bottom ear blocks + back rail'})", "AL6061-T6",
                     "CNC mill from 40 x 50 bar (3 setups)", shp, drawing=True,
                     notes=f"servo body inner face u {u_in:.2f} / outer {u_out:.2f} mm (corner r {g['R_lim']:.2f}); ears on 4x M4 tapped (49.5 x 10 pattern, "
                           f"VERIFY on the received servo); back rail 11.1 x 11.5; 4x M4 from below into the lower ring; clipped to r {g['R_lim']:.2f}",
                     dwg={"datum": "foot face A, ear plane B, servo-centre plane C", "fits": ["ear-hole pattern position 0.1 to C", "foot flat 0.02",
                                                                                          "ear plane B perpendicular to A 0.05"],
                          "finish": "clear anodise", "ht": "T6"})).place(T, "fixed")
    import parts_engine
    reg.add(Part("ENG-GM-15", f"TVC servo {P['tvc_servo_model']['v']} (electronics.json)", "COTS-MIXED", "COTS", parts_engine.servo_shape(L, W, H), cots=True,
                 mass_each_kg=P["tvc_servo_mass"]["v"], mass_tag=f"{P['tvc_servo_mass']['tag']} ({P['tvc_servo_mass']['src']})",
                 supplier="Lindinger (AT) item 9738546 per electronics.json v1", price="119.99 EUR incl. VAT (electronics.json v1, 2026-10-11; DK delivery TO-QUOTE)",
                 notes="body L vertical, shaft tangential 10 mm above the body bottom; ear plane 11 mm below the spline face ASSUMED class value - VERIFY"))
    for sv in g["servos"]:
        reg.parts["ENG-GM-15"].place(tk.T_servo(sv), "fixed")
    r_h = g["r_h"]
    # horn: hub 12 x 5.0 on the 25T spline (spline 3 deep), arm and eye boss flush at 5.0 (one clamp face for the
    # joint stack), M4 tapped through the eye with a 5 H8 x 1.0 seat for the shoulder; countersunk M3 axial screw
    # flush with the hub top; radial M3 pinch clamp in the slotted hub (screw in the BOM, not modelled)
    horn = union_all([cyl(12.0, 0.0, 5.0), box((0.0, -4.0, 0.5), (r_h, 4.0, 5.0)), cyl(10.0, 0.5, 5.0, r_h, 0.0)])
    horn = cut_all(horn, [cyl(5.9, -1.0, 3.1), cyl(3.4, 3.0, 6.0), cq.Solid.makeCone(1.7, 3.4, 1.75, cq.Vector(0, 0, 3.26), cq.Vector(0, 0, 1)),
                          cyl(3.3, -1.0, 6.0, r_h, 0.0), cyl(5.0, 4.0, 6.0, r_h, 0.0), box((-7.0, -0.5, -1.0), (-2.5, 0.5, 6.0))])
    reg.add(Part("ENG-GM-16", f"TVC horn r {r_h:.1f} mm, 25T clamp (7075-T6)", "AL7075-T6", "CNC mill + wire-EDM 25T spline (or re-machined COTS 25T clamp horn)", horn,
                 drawing=True, notes=f"eye at r {r_h:.2f} +/-0.02 (sets n = {g['n']:.2f}); M4 tapped through + 5 H8 x 1.0 shoulder seat; hub top, arm and eye flush "
                                     "(5.00 +/-0.02 above the spline face, clamp face of the joint stack); M3 countersunk axial screw flush; M3 radial pinch clamp",
                 dwg={"datum": "spline axis A, horn face B", "fits": [f"eye M4-6H at r {r_h:.2f} +/-0.02 from A", "shoulder seat 5 H8 x 1.0", "face B flat 0.02, perpendicular to A 0.03",
                                                                      "spline 25T Futaba-type (per servo vendor - VERIFY)"],
                      "finish": "hard anodise", "ht": "T6"}))
    S["horn_T0"] = {}
    for sv in g["servos"]:
        Th = T_basis(sv["O"], -sv["eu"], np.cross(sv["sd"], -sv["eu"]), sv["sd"])
        S["horn_T0"][sv["i"]] = Th
        reg.parts["ENG-GM-16"].place(Th, f"horn:{sv['i']}")
    csk = union_all([cq.Solid.makeCone(1.5, 3.0, 1.7, cq.Vector(0, 0, 3.3), cq.Vector(0, 0, 1)), cyl(3.0, -1.0, 3.31)])
    reg.add(Part("ENG-HW-25", "Horn axial screw ISO 10642 M3 x 6 (countersunk, 10.9), Loctite 243", "STEEL", "COTS", csk, cots=True, mass_each_kg=0.0005,
                 mass_tag="ASSUMED 0.4-0.6 g", supplier="Bossard DK / RS Components DK", supplier_pn="ISO 10642 M3x6 10.9",
                 notes="flush with the hub top (no head above the joint clamp face); length to suit the servo output shaft thread depth - VERIFY"))
    for sv in g["servos"]:
        reg.parts["ENG-HW-25"].place(S["horn_T0"][sv["i"]], f"horn:{sv['i']}")
    Lp = g["L_pr"]
    GE = {"d": 5.0, "D": 14.0, "B": 6.0, "C": 4.0, "dk": 10.0, "alpha_deg": 13.0}
    S["ge"] = GE
    S["joint_stack"] = {"washer_t": 1.5, "washer_od": 7.5, "horn_face_t": 5.0}
    e_od = 18.0
    eye = lambda zc: cyl_dir(e_od, GE["C"], (-GE["C"] / 2, 0.0, zc), (1, 0, 0))
    dog = union_all([eye(0.0), eye(Lp), box((-GE["C"] / 2, -3.5, 0.0), (GE["C"] / 2, 3.5, Lp))])
    dog = cut_all(dog, [cyl_dir(GE["D"], GE["C"] + 2, (-GE["C"] / 2 - 1, 0.0, zc), (1, 0, 0)) for zc in (0.0, Lp)])
    reg.add(Part("ENG-GM-17", f"TVC pushrod dog-bone {Lp:.1f} mm between eyes (7075-T6), fixed length", "AL7075-T6", "CNC mill", dog, drawing=True,
                 notes=f"eyes {e_od:.0f} x {GE['C']:.0f} with 14 N7 bores for GE 5 E outer rings (pressed, staked 3 points); fixed length: servo neutral trimmed in the "
                       "ECU (neutral gauge); two-force member",
                 dwg={"datum": "eye bores A, B", "fits": [f"eye centres {Lp:.2f} +/-0.02", "eye bores 14 N7 (-0.005/-0.023)", "eye faces parallel 0.02"],
                      "finish": "hard anodise", "ht": "T6"}))
    # GE 5 E modelled as two solids so the spherical joint can articulate in the pose checks:
    # outer ring (moves with the rod) and inner ring (moves with the bolt: horn or engine lever)
    Rk = GE["dk"] / 2
    outer = cyl(GE["D"], -GE["C"] / 2, GE["C"] / 2).cut(cq.Solid.makeSphere(Rk, cq.Vector(0, 0, 0), angleDegrees1=-90, angleDegrees2=90))
    inner = cq.Solid.makeSphere(Rk, cq.Vector(0, 0, 0), angleDegrees1=-90, angleDegrees2=90).intersect(cyl(2 * Rk + 1, -GE["B"] / 2, GE["B"] / 2)).cut(cyl(GE["d"], -5, 5))
    ge_note = (f"ISO 12240-1 dimension series E as recalled: d {GE['d']:.0f}, D {GE['D']:.0f}, B {GE['B']:.0f}, C {GE['C']:.0f}, dk {GE['dk']:.0f}, tilt alpha {GE['alpha_deg']:.0f} deg "
               "(alpha consistent with dk/B/C) - VERIFY on the vendor sheet before machining the eyes; misalignment demand in checks/tvc_joints")
    reg.add(Part("ENG-HW-22", "Spherical plain bearing GE 5 E (steel/steel) - outer ring (pressed in the pushrod eye)", "STEEL", "COTS", outer, cots=True,
                 mass_tag="CAD volume of the recalled envelope", supplier="SKF / INA / Hepco GE 5 E class: RS Components DK (TO-QUOTE)", supplier_pn="GE 5 E",
                 notes=ge_note + "; BOM qty = bearings (inner ring ENG-HW-22-IR is the same item)"))
    reg.add(Part("ENG-HW-22-IR", "GE 5 E inner ring (part of ENG-HW-22; modelled separately for articulation)", "STEEL", "COTS (in HW-22)", inner, cots=True,
                 mass_tag="CAD volume of the recalled envelope", notes="not a separate purchase: BOM rolls it into ENG-HW-22"))
    reg.parts["ENG-HW-22-IR"].bom_parent = "ENG-HW-22"
    wsh = tube(S["joint_stack"]["washer_od"], 5.1, 0.0, S["joint_stack"]["washer_t"])
    reg.add(Part("ENG-GM-19", "Joint spacer washer 5.1 x 7.5 x 1.5 (17-4PH H1150), ground faces", "SS17-4PH-H1150", "CNC lathe from bar, faces ground", wsh, drawing=True,
                 notes="clamps the GE inner ring and holds the 2.5 mm eye-face clearance (16 deg with the 18 mm eye); OD 7.5 < inner-ring face OD 8 (stays clear of the "
                       "tilted outer ring up to the GE limit); select 1.45/1.50/1.55 to set the clamp at the horn joint",
                 dwg={"datum": "face A", "fits": ["bore 5.1 +0.05/0", "OD 7.5 -0.05", "thickness 1.50 +/-0.01, faces parallel 0.005"], "finish": "passivate", "ht": "H1150"}))
    stud = union_all([cyl(7.5, 0.0, 1.5), cyl(5.0, 1.5, 9.0), cyl(4.0, 9.0, 13.5)]).cut(cyl(2.9, -0.1, 2.0))
    reg.add(Part("ENG-GM-18", "Lever pivot stud: flange 7.5 x 1.5 (= washer), 5 h7 shoulder x 7.5, M4 x 4.5, 2.5 hex (17-4PH)", "SS17-4PH-H1150", "CNC lathe",
                 stud, drawing=True, notes="screwed into the collar-lever cheek from the servo side, Loctite 243, 2.0 N m; flange clamps the GE inner ring and the far-side "
                                           "spacer against the cheek; flange replaces the servo-side washer (v3.1, stop-pose clearance to the servo body)",
                 dwg={"datum": "shoulder axis A", "fits": ["5 h7 shoulder", "M4-6g x 4.5", "flange face perpendicular 0.02", "shoulder length 7.50 +0.02/0"],
                      "finish": "passivate", "ht": "H1150"}))
    shs = union_all([cyl(8.5, 0.0, 4.0), cyl(5.0, 4.0, 14.0), cyl(4.0, 14.0, 17.5)]).cut(cyl(2.9, -0.1, 2.5))
    reg.add(Part("ENG-GM-20", "Horn-joint shoulder screw: head 8.5 x 4, 5 h7 x 10 shoulder, M4 x 3.5 (17-4PH)", "SS17-4PH-H1150", "CNC lathe", shs, drawing=True,
                 notes="custom because the thread must end inside the horn eye (servo case directly below: a standard ISO 7379 thread is too long); "
                       "shoulder seats in the 5 H8 x 1.0 horn counterbore; Loctite 243, 2.0 N m",
                 dwg={"datum": "shoulder axis A", "fits": ["5 h7 shoulder x 10.00 +0.02/0", "M4-6g x 3.5", "head face perpendicular 0.02"], "finish": "passivate", "ht": "H1150"}))
    for sv in g["servos"]:
        i = sv["i"]
        reg.parts["ENG-GM-17"].place(np.eye(4), f"pushrod:{i}:rod")
        reg.parts["ENG-HW-22"].place(np.eye(4), f"pushrod:{i}:lo")
        reg.parts["ENG-HW-22"].place(np.eye(4), f"pushrod:{i}:hi")
        reg.parts["ENG-HW-22-IR"].place(np.eye(4), f"pushrod:{i}:lo_ir")
        reg.parts["ENG-HW-22-IR"].place(np.eye(4), f"pushrod:{i}:hi_ir")
        reg.parts["ENG-GM-20"].place(np.eye(4), f"pushrod:{i}:screw")
        reg.parts["ENG-GM-19"].place(np.eye(4), f"pushrod:{i}:w_lo1")
        reg.parts["ENG-GM-19"].place(np.eye(4), f"pushrod:{i}:w_lo2")
        reg.parts["ENG-GM-19"].place(np.eye(4), f"pushrod:{i}:w_hi")
        reg.parts["ENG-GM-18"].place(np.eye(4), f"pushrod:{i}:stud")
    return S


# --------------------------------------------------------------------------------------------- pose helpers
def tvc_pose_frames(S, alpha, beta):
    """Per servo i: placements of the pose-dependent TVC items at the engine pose (alpha, beta):
    rod (dog-bone), lo/hi (GE outer rings, with the rod), lo_ir/hi_ir (GE inner rings, on the bolt axes),
    screw (horn shoulder screw), w_lo1/w_lo2 (horn-joint washers), w_hi (lever-joint far-side washer),
    stud (lever pivot stud, engine-fixed), horn; plus psi (deg), rod tilt from +Z and the GE misalignment
    (angle between the rod axis and the plane normal to each bolt axis, deg)."""
    g = S["tvc"]
    R = tk.R_pose(alpha, beta)
    js = S.get("joint_stack", {"washer_t": 1.5})
    w = js["washer_t"]
    hb = S.get("ge", {"B": 6.0})["B"] / 2
    out = {}
    for r, sv in zip(tk.pose_all(g, alpha, beta), g["servos"]):
        i, s = sv["i"], sv["s"]
        Ph, Pl = r["P_h"], r["P_l"]
        zax = (Pl - Ph) / np.linalg.norm(Pl - Ph)
        xax = sv["sd"] - (sv["sd"] @ zax) * zax
        xax /= np.linalg.norm(xax)
        yax = np.cross(zax, xax)
        T_rod = T_basis(Ph, xax, yax, zax)
        T_lo = T_basis(Ph, yax, zax, xax)            # outer ring axis = eye axis (x of the rod frame)
        T_hi = T_basis(Pl, yax, zax, xax)
        sd = sv["sd"]
        sd_e = R @ sv["sd"]
        T_lo_ir = T_basis(Ph, *_frame_from_z(sd))     # inner ring axis = bolt axis (horn: shaft direction)
        T_hi_ir = T_basis(Pl, *_frame_from_z(sd_e))   # lever: engine-fixed bolt axis
        T_horn = S["horn_T0"][i] @ T_rot("z", s * r["psi"])
        T_scr = T_basis(Ph + sd * (hb + w + 4.0), *_frame_from_z(-sd))       # head beyond the far washer, shank toward the horn
        T_w1 = T_basis(Ph - sd * (hb + w), *_frame_from_z(sd))               # horn face -> inner ring
        T_w2 = T_basis(Ph + sd * hb, *_frame_from_z(sd))                     # inner ring -> screw head
        T_wh = T_basis(Pl + sd_e * hb, *_frame_from_z(sd_e))                 # inner ring -> cheek face
        T_st = T_basis(Pl - sd_e * (hb + 1.5), *_frame_from_z(sd_e))         # flange (1.5) on the servo side, thread into the cheek
        mis_lo = math.degrees(math.asin(max(-1.0, min(1.0, float(zax @ sd)))))
        mis_hi = math.degrees(math.asin(max(-1.0, min(1.0, float(zax @ sd_e)))))
        out[i] = {"rod": T_rod, "lo": T_lo, "hi": T_hi, "lo_ir": T_lo_ir, "hi_ir": T_hi_ir, "horn": T_horn, "screw": T_scr,
                  "w_lo1": T_w1, "w_lo2": T_w2, "w_hi": T_wh, "stud": T_st,
                  "psi": r["psi"], "rod_tilt": r["rod_tilt_deg"], "rod_len": r["rod_len"], "mis_lo_deg": mis_lo, "mis_hi_deg": mis_hi}
    return out
