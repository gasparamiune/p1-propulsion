"""Gimballed thrust-chamber parts (TC, NZ, GR, IG), the pintle actuation train and the head crown (GM-06).

All dimensions mm, engine frame at neutral (z=0 at the pivot, +Z forward).  Each part is built in the engine
frame and stored in a local frame translated so that its reference face is z=0 (the drawing datum); the
placement restores it.  Geometry follows combustion.json (gas path, pintle, insert envelope) and
electronics.json (servo envelopes); Mechanical choices are documented in the part notes and README.

Architecture decisions recorded here (CAD v2 2026-10-11, v3 2026-10-12):
 * v3: the gimbal pivot moved from the head to the mid-burn CG (calcs/gimbal_trade.py: tail-wags-dog zero).
   The head no longer carries trunnions; the engine collar (GM-01) clamps in a 0.5 mm groove of the case at
   the pivot plane.  Everything on the head must stay inside the swept envelope of a 140 mm engine bay, so the
   pintle servo stands on the engine axis (body vertical, shaft along +Y) and drives a guided carriage through
   an 18 mm link (offset crank-slider); head-top ports re-allocated: inlet 90, torch 10, Pc 160 deg.
 * Forward closure = injector head: internal plug with 2 AS568-226 FKM 90A glands + 8 radial M5 screws
   (v3.1: -227 label corrected to -226 for the 51.65 groove; 90A for the extrusion gap at 67.5 bar proof).
 * Aft closure = threaded socket (M63x1.5 on the case end) with one AS568-229 rod gland on a 61.0 mm land
   (v3.1: -233 was a label error, its ID 72.6 mm is loose on the 61.0 land - hand_calcs v2 gland check).
 * v3.1 (MEOP 45 bar, lead 2026-10-12): graphite insert retained by a 6 mm lip on its shoulder with a 30 mm aft
   spigot through the lip (was a 4 mm lip under the insert bottom face, 22 mm ID in the plume).
   An internal plug cannot hold the 44 mm graphite insert inside the 57.15 mm case bore with gland and
   tapped-hole walls (README "aft closure trade").
 * Pc tap and torch port are on the head top with drilled passages to the injector face periphery
   (r ~ 21 mm): a radial boss in the 3.2 mm 6061 wall at x_face = 15 mm needs welding or a saddle clamp and
   the 70 mm torch cannot point radially inside a 120 mm airframe (REQUEST to Combustion in CHANGELOG).
 * v3.2 (lead relays 2026-10-12): grain v2 S230 (straight centred 25 mm port, 230 mm, contour +30 mm).
   Aft section: the aluminium case ends at the grain's aft face; the post-chamber, convergent insulator,
   graphite insert and retaining lip sit in a one-piece high-temperature aft section (316L baseline, material
   from config) screwed onto the case's M63x1.5 end.  Insert insulated: 3 mm phenolic sleeve + 1 mm mica
   shoulder gasket (the 0.5 mm Grafoil short-circuited the insert to the lip).  Soak-back and wall
   temperatures are verified in 04-fea (LC5 thermal).
   Torch: Combustion v2 asks for a radial boss at x_face 15 mm inclined 30 deg; on this engine x_face 15 is
   inside the 3.2 mm aluminium case below the head plug and a body leaning out of the case sweeps beyond the
   140 mm bay (calcs/torch_sweep.py).  Mechanical v3.2 counter-proposal: the 20 x 45 torch seats on the head
   top (0 deg, r 25) and fires through a 5.2 mm passage and a 3 mm outlet drilled 30 deg inward/aft that leaves
   the face at r 16.9 (jet axis at r 8 at x_face 15).  Check valves are cartridge inserts in the torch inlets.
"""
from __future__ import annotations
import math
import numpy as np
import cadquery as cq
from geom import (revolve, cyl, cyl_dir, tube, box, radial_hole, union_all, cut_all, T_trans, T_rot,
                  T_axis_to, T_basis, apply)
from partlib import Part

ANG = {"pc": 105.0, "torch": 0.0, "inlet": 180.0, "bonnet_bolts": (60.0, 120.0, 240.0, 300.0)}
TORCH_R = 25.0                      # torch seat axis radius on the head top (mm)
TORCH_OUT_DEG = 30.0                # outlet inclination from the engine axis, inward/aft (Combustion v2)
TORCH_KNEE_H = 8.0                  # height above the injector face where the 30 deg outlet meets the passage
BONNET_H = 32.0                     # TC-04 bonnet height above the head top (v3.3 and v3.4)
TC03_NOSE_R = 7.6                   # v3.5.1 TB1: TC-03 nose radius (1.0 mm IN718 wall around the r 6.59 diffuser exit at the face)
TC10_NOSE_GAP = 0.05                # v3.5.1 TB1: TC-10 bore to TC-03 nose radial clearance (RTV-filled bond line; closed in the thermal mesh)


def localize(shape, z_ref):
    return apply(shape, T_trans(0, 0, -z_ref)), T_trans(0, 0, z_ref)


def gland_cut(r_groove, r_outer, z0, width):
    """Annular groove for a piston (plug) O-ring: removes r in [r_groove, r_outer+1] over z0..z0+width."""
    return tube(2 * r_outer + 2, 2 * r_groove, z0, z0 + width)


def polar(r, a_deg, z=0.0):
    a = math.radians(a_deg)
    return np.array([r * math.cos(a), r * math.sin(a), z])


def helical_port(d_port, r_helix, pitch, z0, z1, n_per_turn=16):
    """Round port of diameter d_port whose centre follows a helix of radius r_helix (sections normal to the
    engine axis are circles): loft through circles."""
    if r_helix <= 1e-6:
        return cyl(d_port, z0, z1)
    L = z1 - z0
    n = max(8, int(math.ceil(L / pitch * n_per_turn)))
    sections = []
    for i in range(n + 1):
        z = z0 + L * i / n
        a = 2 * math.pi * (z - z0) / pitch
        sections.append(cq.Wire.makeCircle(d_port / 2, cq.Vector(r_helix * math.cos(a), r_helix * math.sin(a), z), cq.Vector(0, 0, 1)))
    return cq.Solid.makeLoft(sections, False)


def servo_shape(L, W, H, shaft_from_end=10.0, ear_below_face=11.0, ear_t=2.5, ear_ext=7.0):
    """Standard-size servo in its local frame: origin on the output-shaft axis at the spline face, Z_s = shaft
    out of the case, X_s along the body length (shaft 10 mm from the near end), Y_s across the width.  Ears in the
    plane 11 mm below the spline face (ASSUMED class values: verify on the received unit)."""
    body = box((-shaft_from_end, -W / 2, -H), (L - shaft_from_end, W / 2, 0.0))
    ears = box((-shaft_from_end - ear_ext, -W / 2, -ear_below_face - ear_t), (L - shaft_from_end + ear_ext, W / 2, -ear_below_face))
    spline = cyl_dir(6.0, 3.0, (0, 0, 0), (0, 0, 1))
    return union_all([body, ears, spline])


def build_engine_parts(P, S, reg, mat):
    v = lambda k: P[k]["v"] * 1000.0
    HV69_ON = bool(P.get("v34_pintle_hv69", {}).get("v", False))       # v3.4 HV69 in-line pintle drive (parts_pintle.py)
    E1M_ON = bool(P.get("v34_inlet_e1m", {}).get("v", False))           # v3.4 E1-M inlet (parts_inlet.py)
    # v3.4: Pc tap 1/8-27 NPT at r 25 / 142 deg, between the E1-M bonnet boss (y <= 8) and the PD-01 +Y foot (x >= -13); the v3.3 1/4 NPT
    # at r 24 / 105 deg sits under the PD-01 foot; 135 deg lightening pocket deleted (it overlaps the tap)
    pc_ang, pc_r = (142.0, 25.0) if HV69_ON else (ANG["pc"], 24.0)
    S["pc_port"] = (pc_ang, pc_r)
    case_R = v("case_OD") / 2                  # 31.75
    case_r = v("case_ID") / 2                  # 28.575
    seal_r = v("case_bore_seal") / 2           # 28.625
    plug_r = 57.20 / 2                         # plug 57.20 f7
    groove_r = 51.65 / 2                       # piston gland diameter (hand_calcs gland check)
    gw = 4.85                                  # groove width (AS568-2xx, 3.53 CS)
    nb = int(P["n_bolts_chamber"]["v"])
    db = v("bolt_d_chamber")
    tap = {5.0: 4.2, 4.0: 3.3, 6.0: 5.0, 3.0: 2.5}[round(db, 1)]
    a0_j = float((P.get("jfwd_ang0_deg") or {}).get("v", 22.5))       # v3.5.2 (lead CHANGELOG 231 (1)): 10x M5 at 18 + 36k deg
    angs = [a0_j + 360.0 / nb * k for k in range(nb)]
    S["screw_angles"] = angs
    zt, zb = S["head_top"], S["head_bot"]
    zf = S["inj_face"]
    liner_or = v("liner_OD") / 2               # 28.55
    lip_r = v("lip_ID") / 2                    # 25.0
    r_pre = v("D_pre") / 2                     # 26.95
    r_post = v("D_post") / 2

    # ------------------------------------------------------------------ TC-01 case tube
    z0, z1 = S["tube_aft"], S["tube_fwd"]
    land = v("plug_len_fwd") + 2.0           # v3.2: bored land covers the whole plug (v3.1 check: 24 mm < 36 mm plug -> TC-01/TC-02 interference)
    r_land_aft = v("case_aft_land_d") / 2      # 30.5
    zl, zth = S["aft_land_top"], S["aft_thread_top"]
    # v3.5.2 (lead CHANGELOG 230 (1), item 11): J-FWD land - OD jl_od from jl_aft aft of the screw axis to the fwd end (30 deg taper) with flat
    # spot faces so that the wall at the 5.5 hole (bore to spot face) is jl_t; 0 = v3.5.1 tube OD (case_R) to the fwd end
    jl_t = float((P.get("jfwd_land_t") or {}).get("v", 0.0) or 0.0) * 1000.0
    if jl_t > 0:
        jl_R = float(P["jfwd_land_od"]["v"]) * 500.0
        jl_z1 = S["bolt_z_fwd"] - float(P["jfwd_land_aft"]["v"]) * 1000.0
        jl_z0 = jl_z1 - (jl_R - case_R) / math.tan(math.radians(30.0))
        fwd_od = [(case_R, jl_z0), (jl_R, jl_z1), (jl_R, z1)]
        S["jfwd_land"] = {"t_at_hole_mm": jl_t, "R_land_mm": jl_R, "z_taper0": round(jl_z0, 3), "z_land0": round(jl_z1, 3), "z_fwd": round(z1, 3),
                          "spot_d_mm": float(P["jfwd_spot_d"]["v"]) * 1000.0, "r_spot_mm": seal_r + jl_t}
    else:
        jl_R = case_R
        fwd_od = [(case_R, z1)]
    case = revolve([(case_r, z0), (r_land_aft - 0.6, z0), (r_land_aft, z0 + 0.6 / math.tan(math.radians(15))),
                    (r_land_aft, zl), (31.5, zl), (31.5, zth), (r_land_aft, zth), (r_land_aft, zth + 2.0),
                    (case_R, zth + 2.0 + (case_R - r_land_aft))] + fwd_od + [(case_r, z1)])
    case = case.cut(tube(2 * seal_r, 2 * case_r - 1, z1 - land, z1 + 1))
    ch = revolve([(seal_r, z1 - 3.0), (seal_r + 3.0 * math.tan(math.radians(15)), z1), (seal_r + 3, z1 + 0.01), (seal_r, z1 + 0.01)])
    case = case.cut(ch)
    case = cut_all(case, [radial_hole(db + 0.5, a, S["bolt_z_fwd"], case_r - 1, jl_R + 1) for a in angs])
    if jl_t > 0:                                                            # flat spot faces for the ISO 7380 heads (dk 9.5) on the land
        case = cut_all(case, [radial_hole(S["jfwd_land"]["spot_d_mm"], a, S["bolt_z_fwd"], seal_r + jl_t, jl_R + 1.0) for a in angs])
    gd, gwid = v("collar_groove_depth"), v("collar_w")
    S["collar_groove"] = (case_R - gd, -gwid / 2, gwid / 2)
    case = case.cut(tube(2 * case_R + 2, 2 * (case_R - gd), -gwid / 2, gwid / 2))      # engine-collar groove at the pivot plane
    shp, T = localize(case, z1)
    reg.add(Part("ENG-TC-01", "Combustion case tube", "AL6061-T6", "cut-stock + CNC lathe (bore fwd seal land, turn aft land and thread) + drill",
                 shp, drawing=True, hot=True,
                 supplier=("6061-T6 drawn tube 69.85 x 6.35 (2.75 x 0.25 in; ID 57.15 as the v3.5.1 tube) or >= 67 x <= 57.15 bar/tube, OD turned to 63.5 "
                           "except the J-FWD land (v3.5.2): supplier TO-SELECT (DK delivery), TO-QUOTE" if jl_t > 0 else
                           "6061-T6 drawn tube 63.5 x 3.175 (2.5 x 0.125 in): Aluminium-Online.de / Wefa / Metals4U (DK delivery)"),
                 notes=f"v3.2: case ends at the grain aft face (aft section TC-09 carries the post-chamber). Length {z1-z0:.2f} mm. Collar groove {2*(case_R-gd):.2f} h9 x {gwid:.0f} mm at {z1:.1f} mm from the fwd end (pivot plane). "
                       f"Fwd: seal land bored 57.25 H8 x {land:.0f} mm Ra 0.8, 15 deg lead-in; {nb}x {db + 0.5:.1f} radial holes at "
                       f"{z1-S['bolt_z_fwd']:.0f} mm" + (f" (az {angs[0]:g} + {360.0 / nb:g} k deg; v3.5.2 J-FWD per lead CHANGELOG 231 (1): {nb}x M5 A4-80, no spot face (the "
                                                       f"button head seats on the OD), holes match-drilled with TC-02)" if (nb != 8 and jl_t <= 0) else "") + (f" (v3.5.2 J-FWD land OD {2*jl_R:.1f} from z {S['jfwd_land']['z_land0']:.1f} to the fwd end, 30 deg taper; 8x spot face d{S['jfwd_land']['spot_d_mm']:.1f} flat, wall {jl_t:.2f} at the hole; stock >= 2.75 x 0.25 in tube, OD turned to 63.5 elsewhere)" if jl_t > 0 else "") + f". Aft: M63x1.5-6g x {P['aft_thread_len']['v']*1e3:.0f} mm (modelled at 63.0 major), relief 61.0 x 2, "
                       f"seal land 61.0 f7 x {P['aft_land_len']['v']*1e3:.0f} mm Ra 0.8 with 15 deg lead-in",
                 dwg={"datum": "fwd end face A, axis B", "fits": ["fwd bore 57.25 H8 (+0.046/0) Ra 0.8", "aft land 61.0 f7 (-0.030/-0.060) Ra 0.8",
                                                                "collar groove 62.50 h9 (0/-0.074) x 20.0 +0.1/0, corner R0.4",
                                                                "M63x1.5-6e thread, 14 mm (6e: thermal growth into the steel aft section)"],
                      "finish": "clear anodise (Type II) after machining, seal lands masked", "ht": "T6 as supplied (no welding)"}
                 )).place(T, "engine")

    # ------------------------------------------------------------------ TC-02 injector head / forward closure
    face_rec = 2.0                                                        # recess for TC-10 face insulator
    body = revolve([(0, zf + face_rec), (10.1, zf + face_rec), (10.1, zf), (plug_r, zf), (plug_r, zb), (case_R, zb), (case_R, zt), (0, zt)])
    body = body.cut(tube(2 * r_pre, 2 * 10.1, zf - 1, zf + face_rec))      # face recess r 10.1..26.95
    g1 = zf + 3.0
    g2 = g1 + gw + 3.0
    S["fwd_glands"] = (g1, g2, gw)
    body = body.cut(gland_cut(groove_r, plug_r, g1, gw)).cut(gland_cut(groove_r, plug_r, g2, gw))
    # v3.5.1 (LC-TB70/LC1 TC-02 head fix, lead CHANGELOG 182 (1) / 183 (1)): 'TB1' recesses the TC-03 flange by the face-insulator
    # thickness under an extended TC-10 disc (the IN718 flange face no longer sees the chamber gas); TC-03 keeps its gas-side geometry
    # (diffuser exit at the face plane, seat zf + 5) through a nose of radius TC03_NOSE_R; thread M14x1 x 10 kept (insert +2 mm upward).
    tc03_face = str((P.get("tc03_face") or {}).get("v", "BASE"))
    nose_t = face_rec if tc03_face in ("TB1", "TB2") else 0.0
    nose_r = float((P.get("tc03_nose_r_mm") or {}).get("v", TC03_NOSE_R))
    S["tc03_face"], S["tc03_nose_t"], S["tc03_nose_r"] = tc03_face, nose_t, nose_r
    ins_L = 12.0 + nose_t                                                 # seat insert length (nose + flange 2 + thread 10)
    z_ins_top = zf + ins_L
    z_fl0, z_fl1 = zf + nose_t, zf + nose_t + 2.0                         # TC-03 flange front face / counterbore floor
    S["z_ins_top"] = z_ins_top
    S["tc03_flange_z"] = (z_fl0, z_fl1)
    cuts = [cyl(13.0, zf - 1, z_ins_top), cyl(20.2, zf - 1, z_fl1),      # M14x1 tap drill 13.0 x 12 + flange counterbore
            cyl(10.0, z_ins_top - 0.01, zt + 1)]                           # manifold bore 10 mm (needle body 6 mm)
    for a in ANG["bonnet_bolts"]:                                         # bonnet: 4x M4
        c = polar(16.5, a)
        cuts.append(cyl(3.3, zt - 10, zt + 1, c[0], c[1]))
    jdrill = float((P.get("jfwd_tap_drill_mm") or {}).get("v", 6.5))     # v3.5.1 (RM1-12): 9.0 drill / 8.0 full thread for M5 x 10 (6.83 engagement)
    S["jfwd_tap_drill_mm"] = jdrill
    for a in angs:                                                        # M5 tapped radial holes
        cuts.append(radial_hole(tap, a, S["bolt_z_fwd"], plug_r - jdrill, plug_r + 1))
    if HV69_ON:                                                           # v3.4: PD-01 feet, 4x M3 tapped 8 deep at r 26 (tap drill 2.5)
        S["bracket_holes"] = []
        S["pd01_feet_xy"] = [tuple(polar(26.0, a)[:2]) for a in (70.0, 110.0, 250.0, 290.0)]
        for (hx, hy) in S["pd01_feet_xy"]:
            cuts.append(cyl(2.5, zt - 8, zt + 1, hx, hy))
    else:
        S["bracket_holes"] = [(-10.0, -23.5), (10.0, -23.5)]               # M4 tapped for the pintle bracket TC-12
        for (hx, hy) in S["bracket_holes"]:
            cuts.append(cyl(3.3, zt - 8, zt + 1, hx, hy))
    cpc = polar(pc_r, pc_ang)
    if HV69_ON:                                                           # 1/8-27 NPT (tap drill 8.7) x 10 + 2 mm passage to the face
        cuts.append(cyl(8.7, zt - 10, zt + 1, cpc[0], cpc[1]))
        p0, p1 = polar(pc_r, pc_ang, zt - 9.5), polar(20.5, pc_ang, zf - 1)
    else:                                                                 # Pc tap 1/4-18 NPT + 2 mm passage
        cuts.append(cyl(11.1, zt - 12, zt + 1, cpc[0], cpc[1]))
        p0, p1 = polar(24.0, ANG["pc"], zt - 11.5), polar(20.5, ANG["pc"], zf - 1)
    cuts.append(cyl_dir(2.0, np.linalg.norm(p1 - p0) + 1, p0, p1 - p0))
    S["pc_passage"] = (p0, p1)
    cto = polar(TORCH_R, ANG["torch"])                                    # torch seat M10x1 x 10 + 5.2 mm passage + 30 deg 3 mm outlet
    cuts.append(cyl(9.0, zt - 10, zt + 1, cto[0], cto[1]))
    r_knee = 21.5
    p0, p1 = polar(TORCH_R, ANG["torch"], zt - 9.5), polar(r_knee, ANG["torch"], zf + TORCH_KNEE_H)
    cuts.append(cyl_dir(5.2, np.linalg.norm(p1 - p0) + 2.0, p0, p1 - p0))
    r_out = r_knee - TORCH_KNEE_H * math.tan(math.radians(TORCH_OUT_DEG))
    q0, q1 = polar(r_knee, ANG["torch"], zf + TORCH_KNEE_H), polar(r_out, ANG["torch"], zf)
    cuts.append(cyl_dir(3.0, np.linalg.norm(q1 - q0) + 1.5, q0 + (q0 - q1) / np.linalg.norm(q1 - q0) * 0.5, q1 - q0))
    S["pc_exit"] = polar(20.5, pc_ang, zf)
    S["torch_exit"] = polar(r_out, ANG["torch"], zf)
    S["torch_jet"] = {"exit_r_mm": round(r_out, 2), "incl_deg": TORCH_OUT_DEG,
                      "r_at_xface15_mm": round(r_out - 15.0 * math.tan(math.radians(TORCH_OUT_DEG)), 2)}
    for a in ((45.0, 225.0, 315.0) if HV69_ON else (45.0, 135.0, 225.0, 315.0)):   # lightening pockets 7 x 8 deep
        cc = polar(26.0, a)
        cuts.append(cyl(7.0, zt - 8, zt + 1, cc[0], cc[1]))
    # v3.4 (HV69): the 10 mm bonnet bore ends at zb0 + 22, 1 mm below the rod-seal gland (zb0 + 23..26.6).  In v3.3 and the first
    # v3.4 layout the bore ran to zb0 + 26, so 3 of the 3.6 mm gland lay inside the 10 mm bore and the seal OD had no static land
    # (found by the segment trap analysis 2026-10-13); the cross-drilling stays flush with the new bore top (Combustion C2).
    S["bonnet_bore_rel"] = 22.0 if HV69_ON else 26.0
    if E1M_ON:                                                            # v3.4 inlet E1-M: block flat, radial filter bore, axial 8 mm
        import parts_inlet
        S["jfd01_v352"] = bool((P.get("jfd01_v352") or {}).get("v", False))   # v3.5.2 J-FD01: flat r 29.5, 3x M4 (lead 2026-10-19 item 2)
        cuts += parts_inlet.head_cuts(S)
    body = cut_all(body, cuts)
    shp, T = localize(body, zt)
    reg.add(Part("ENG-TC-02", "Injector head / forward closure (pintle seat bore, manifold, Pc and torch ports)", "AL6061-T6",
                 "CNC lathe + 3-axis mill (2 setups)", shp, drawing=True, wetted="N2O",
                 notes="Head 63.5 x 28; plug 57.20 f7 with 2 AS568-226 FKM 90A glands (51.65 h9 groove, 4.85 wide); "
                       "M14x1 seat-insert bore; 10 mm manifold bore; 1/4-18 NPT Pc tap (105 deg, 1/8 in sense line < 0.3 m) with 2 mm passage to the face at r 20.5; "
                       "M10x1 torch seat (0 deg, r 25) with 5.2 mm passage and 3 mm outlet drilled 30 deg inward/aft leaving the face at r 16.9 "
                       "(v3.2 counter-proposal to Combustion's x_face 15 boss); " + (f"{nb}x M5 radial tapped at az {angs[0]:g} + {360.0 / nb:g} k deg (v3.5.2 J-FWD, lead CHANGELOG 231 (1): "
                       "ISO 7380-1 M5 x 10 A4-80, sized at FA1S 151.04 bar abs SF 1.0 in v352/jfwd/jfwd_v352_v1.json; match-drilled with TC-01)" if nb != 8 else
                       "8x M5 radial tapped (J-FWD screws ISO 3506-1 A4-80, v3.5 lead decision 177 (2): yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar)")
                       + (f"; v3.5.1: taps drilled 4.2 x {jdrill:.1f}, M5-6H full thread {jdrill - 1.0:.1f} for ISO 7380-1 M5 x 10 A4-80 (6.83 mm engagement; "
                          "v3.5 6.5 deep: M5 x 10 bottomed)" if jdrill > 6.5 else "")
                       + "; 4x M4 bonnet" + (", 4x M3 PD-01 feet (r 26, 8 deep)" if HV69_ON else ", 2x M4 pintle bracket") + "; oxygen-clean, Krytox only",
                 dwg={"datum": "head top face A, axis B", "fits": ["plug 57.20 f7 (-0.030/-0.060)",
                                                                  "gland groove 51.65 h9 x 4.85 +0.13/0, Ra 0.8 groove bottom, Ra 1.6 flanks (Parker ORD 5700)",
                                                                  "M14x1-6H x 10, M10x1-6H x 10, 1/4-18 NPT, " + (f"M5-6H x {jdrill - 1.0:.1f} full thread (drill 4.2 x {jdrill:.1f})" if jdrill > 6.5 else "M5-6H x 6.5") + ", M4-6H"],
                      "finish": "clear anodise Type II except threads and gland; oxygen-clean per ASTM G93 / CGA G-4.1", "ht": "T6 as supplied"}
                 )).place(T, "engine")

    # ------------------------------------------------------------------ TC-03 pintle seat insert
    d_seat = v("pintle_seat_d")
    z_seat = zf + 5.0
    S["z_seat"] = z_seat
    half_d = math.radians(37.5)
    if nose_t > 0:   # v3.5.1 TB1: nose (r TC03_NOSE_R) through the TC-10 bore, flange behind the insulator
        ins = revolve([(0, zf), (nose_r, zf), (nose_r, z_fl0), (10.0, z_fl0), (10.0, z_fl1), (7.0, z_fl1), (7.0, z_ins_top), (0, z_ins_top)])
    else:
        ins = revolve([(0, zf), (10.0, zf), (10.0, zf + 2.0), (7.0, zf + 2.0), (7.0, z_ins_top), (0, z_ins_top)])
    r_diff_face = d_seat / 2 + (z_seat - zf) * math.tan(half_d)
    ins = ins.cut(revolve([(0, zf - 0.01), (r_diff_face, zf - 0.01), (d_seat / 2, z_seat), (d_seat / 2, z_seat + 0.3),
                           (4.0, z_seat + 0.3 + (4.0 - d_seat / 2)), (4.0, z_ins_top + 0.01), (0, z_ins_top + 0.01)]))
    r_sp = max(8.8, nose_r + 1.2) if nose_t > 0 else 8.0                  # spanner holes (TB1: outside the nose)
    ins = cut_all(ins, [cyl(2.0, z_fl0 - (0.0 if nose_t > 0 else 1.0), z_fl0 + 1.5, r_sp * math.cos(math.radians(a)), r_sp * math.sin(math.radians(a)))
                        for a in (0, 180)])
    # v3.5.1 TBC screen (P['tc03_tbc_mm'] > 0): APS YSZ thermal-barrier layer of that thickness on the gas-exposed TC-03 faces (exposed face annulus and the
    # diffuser cone from the face up to 0.5 mm before the sharp seat edge, which stays bare metal); the metal is undercut by the same thickness so the coated
    # contour is the nominal contour.  Separate part ENG-TC-03C (thermal model; non-structural in SAX).
    tbc = float((P.get("tc03_tbc_mm") or {}).get("v", 0.0))
    S["tc03_tbc_mm"] = tbc
    coat = None
    if tbc > 0:
        r_out = nose_r if nose_t > 0 else 10.0
        tn = math.tan(half_d)
        zc = z_seat - 0.5
        nr, nz = math.cos(half_d), math.sin(half_d)                       # cone normal into the metal (r out, z up)
        p0, pc = (r_diff_face, zf), (r_diff_face - (zc - zf) * tn, zc)
        band = revolve([p0, (p0[0] + tbc * nr, p0[1] + tbc * nz), (pc[0] + tbc * nr, pc[1] + tbc * nz), pc]).fuse(
            revolve([(r_diff_face - 1.0, zf - 0.01), (r_out + 0.01, zf - 0.01), (r_out + 0.01, zf + tbc), (r_diff_face - 1.0, zf + tbc)]))
        coat = ins.intersect(band)
        ins = ins.cut(band)
    shp, T = localize(ins, zf)
    t3mat = P["tc03_material"]["v"] if "tc03_material" in P else "SS17-4PH-H1150"
    if t3mat == "IN718":   # v3.4.1: lead decision 2026-10-13 (Combustion v2.4 item 7; 04-fea/thermal/tc03_in718_check_v1.json)
        t3ht = ("Inconel 718 (UNS N07718) bar, solution treated + precipitation hardened (AMS 5662 / AMS 5663 class, AS RECALLED: "
                "confirm the condition with the supplier); exit-lip peak A1 819.5 C above the 650 C long-term limit for seconds per burn (lip unloaded)")
        t3seal = ("AS568-016 FFKM (Kalrez 7075 class, TO-QUOTE) under the flange in the TC-02 counterbore-floor groove (seal S03: FKM exceeds its "
                  "200 C class, 224.7 C at B1, seal_table_v1); B-PNT-1 GN2 leak check across S03 at 56 bar after a >= 230 C soak")
    elif t3mat == "GLIDCOP-AL15":   # v3.5.1 (182 (1) head fix): TB1 recessed flange + dispersion-strengthened copper
        t3ht = ("GlidCop AL-15 (UNS C15715) dispersion-strengthened copper, 25-30 mm rod (Hoganas 0667HOG-2: 29 mm as-consolidated rod "
                "YS 324 / UTS 393 MPa, k 365 W/m/K, typical values; design allowables x0.8 ASSUMED); no heat treatment; seat edge lapped. "
                "TO-VERIFY: seat-edge coining/erosion (flow calibration of the seat before/after firings), galvanic couple with the 6061 head "
                "(thread sealant / nickel flash on the insert), N2O decomposition on hot copper-oxide surfaces (wetted bore <= 200 C ASSUMED)")
        t3seal = ("AS568-016 FFKM under the flange in the TC-02 counterbore-floor groove (flange now behind the TC-10 insulator, TB1); "
                  "B-PNT-1 GN2 leak check across S03 at 56 bar")
    else:
        t3ht = "17-4PH H1150 (AMS 5643 / ASTM A564)"
        t3seal = "thread sealed with PTFE tape (oxygen grade) or AS568-016 FKM under the flange (groove in TC-02 counterbore floor)"
    reg.add(Part("ENG-TC-03", f"Pintle seat insert ({d_seat:.1f} mm sharp-edged seat, 37.5 deg diffuser)", t3mat, "CNC lathe",
                 shp, drawing=True, wetted="N2O", hot=True,
                 notes=f"M14x1-6g external, flange 20 x 2 with 2 spanner holes; seat {d_seat:.2f} mm sharp edge (land 0.3 mm, no burr), "
                       f"seat {z_seat-zf:.1f} mm above the face, diffuser 37.5 deg half-angle to {2*r_diff_face:.1f} mm at the face; " + t3seal,
                 dwg={"datum": "flange face A", "fits": [f"seat {d_seat:.3f} +0.010/0, sharp edge", "M14x1-6g", "approach bore 8.0 H8"],
                      "finish": "seat lapped with the needle cone (bluing check, 360 deg contact)", "ht": t3ht}
                 )).place(T, "engine")
    if coat is not None:
        shc, Tc = localize(coat, zf)
        reg.add(Part("ENG-TC-03C", f"TC-03 thermal-barrier coating, APS YSZ {tbc:.2f} mm on a NiCrAlY bond coat (face + diffuser cone, seat edge bare)",
                     "YSZ-APS", "plasma spray (supplier)", shc, drawing=False, hot=True,
                     notes="v3.5.1 SCREEN: coating as a separate solid for the thermal model; supplier, bond-coat and thickness tolerance TO-QUOTE; "
                           "spallation is test-based (inspect after every static fire)")).place(Tc, "engine")

    # ------------------------------------------------------------------ TC-05 pintle needle
    stroke = v("pintle_stroke_v34") if HV69_ON else v("pintle_stroke")
    cone = math.radians(P["pintle_cone_half_deg"]["v"])
    # v3.4: the cone seats on the UPSTREAM (top) edge of the 0.3 mm land; v3.3 placed it at the land bottom, so the closed needle
    # overlapped the land by up to 0.08 mm radially (found 2026-10-13 while building the segment fluid domain)
    z_sl = z_seat + (0.3 if HV69_ON else 0.0)
    S["z_seat_line"] = z_sl
    z_cone_top = z_sl + (3.0 - d_seat / 2) / math.tan(cone)
    r_tip = d_seat / 2 - (stroke + 0.5) * math.tan(cone)
    z_tip = z_sl - (d_seat / 2 - r_tip) / math.tan(cone)
    S["needle_profile"] = {"z_tip": z_tip, "r_tip": r_tip, "z_cone_top": z_cone_top, "z_body_top": zt + 2.0, "cone_rad": cone}
    z_body_top = zt + 2.0
    if HV69_ON:                                                             # v3.4: 3 mm stem, M3 top screwed into the PD-07 arm (no cross-hole)
        d_stem = v("pintle_stem_d_v34")
        S["z_needle_top"] = zt + BONNET_H + 9.0                              # = bonnet top + 9 (top of the PD-07 arm, closed)
        needle = revolve([(0, z_tip - 0.6), (r_tip - 0.6, z_tip - 0.6), (r_tip, z_tip), (3.0, z_cone_top), (3.0, z_body_top),
                          (d_stem / 2, z_body_top + 1.5), (d_stem / 2, S["z_needle_top"]), (0, S["z_needle_top"])])
        tc05_notes = (f"closed position shown; stroke {stroke:.1f} mm away from the chamber opens (crank stop 113.09 deg); cone half-angle "
                      f"{P['pintle_cone_half_deg']['v']:.0f} deg (combustion.json); v3.4 stem 3 h7 through the PTFE spring-energised seal (TC-04), "
                      "M3 x 0.5 top thread 4.5 mm into the PD-07 arm (Loctite 243); stem buckling/tension margins in pintle_inline_v34_v2p4")
        tc05_fits = ["stem 3 h7 (0/-0.010) Ra 0.2", "M3-6g top thread, 6 mm", "body 6 f7", "cone 15 deg +/-5' lapped to TC-03"]
    else:
        d_stem = v("pintle_stem_d")
        S["z_needle_top"] = zt + 40.0                                       # stem top (clevis) at closed position
        needle = revolve([(0, z_tip - 0.6), (r_tip - 0.6, z_tip - 0.6), (r_tip, z_tip), (3.0, z_cone_top), (3.0, z_body_top),
                          (2.0, z_body_top + 1.0), (2.0, S["z_needle_top"]), (0, S["z_needle_top"])])
        needle = needle.cut(cyl_dir(2.0, 8, (-4, 0, S["z_needle_top"] - 3.0), (1, 0, 0)))      # carriage cross-pin, along X
        tc05_notes = (f"closed position shown; stroke {stroke:.1f} mm away from the chamber opens; cone half-angle {P['pintle_cone_half_deg']['v']:.0f} deg "
                      "(combustion.json); stem 4 h7 through the PTFE spring-energised seal; 2 mm cross-hole along X for the TC-16 carriage pin")
        tc05_fits = ["stem 4 h7 (0/-0.012) Ra 0.2", "body 6 f7", "cone 15 deg +/-5' lapped to TC-03"]
    shp, T = localize(needle, z_seat)
    reg.add(Part("ENG-TC-05", f"Pintle needle (15 deg metering cone, 6 mm body, {d_stem:.0f} mm stem)", "SS17-4PH-H1150",
                 "CNC lathe, stem ground h7 Ra 0.2", shp, drawing=True, wetted="N2O", hot=True, notes=tc05_notes,
                 dwg={"datum": "seat contact line A", "fits": tc05_fits, "finish": "passivate (ASTM A967)", "ht": "17-4PH H1150"}
                 )).place(T, "engine")

    # ------------------------------------------------------------------ TC-04 bonnet (stem seal, guide, inlet, P_feed port)
    zb0, zb1 = zt, zt + BONNET_H
    S["bonnet_top"] = zb1
    S["inlet_port"] = (ANG["inlet"], 22.0, zb0 + 30.0)
    S["guide_pins_xy"] = [(-9.0, 4.75), (9.0, 4.75)]
    rin = polar(22.0, ANG["inlet"])                                       # inlet riser axis (axial -6 ORB port on its top)
    S["inlet_riser"] = (rin[0], rin[1], zb0 + 30.0)
    top_fl = [] if HV69_ON else [cyl(30.0, zb1 - 4.0, zb1)]                # v3.4 HV69: no carriage guide-pin flange (MGN09H guides PD-07)
    if E1M_ON:                                                            # v3.4 E1-M: boss + axial/cross 8 mm + transfer groove, no ORB inlet
        boss_e1m, cuts_e1m = parts_inlet.bonnet_body_and_cuts(S, zb0, v34_port=HV69_ON)
        bon = union_all([cyl(40.0, zb0, zb0 + 5.0), cyl(24.0, zb0, zb1)] + top_fl + [boss_e1m])
    else:
        bon = union_all([cyl(40.0, zb0, zb0 + 5.0), cyl(24.0, zb0, zb1)] + top_fl +
                        [cyl(24.0, zb0, zb0 + 30.0, rin[0], rin[1]), radial_hole(12.0, ANG["inlet"], zb0 + 12.0, 0.0, 22.0)])
    d_sb = 3.05 if HV69_ON else 4.05                                      # stem bore (3 mm stem with HV69, 4 mm v3.3)
    bcuts = [cyl(10.0, zb0 - 1, zb0 + S["bonnet_bore_rel"]), cyl(d_sb, zb0 + S["bonnet_bore_rel"] - 0.1, zb1 + 1),
             tube(7.4 if HV69_ON else 8.9, d_sb - 0.05, zb1 - 9.0, zb1 - 5.4),   # PTFE spring-energised rod seal gland (TO-VERIFY vs vendor)
             tube(5.0 if HV69_ON else 6.0, d_sb - 0.05, zb1 - 4.0, zb1 + 1),     # guide bushing seat (TC-11)
             tube(14.4, 12.0, zb0 - 0.01, zb0 + 1.30)]                       # face O-ring groove AS568-013
    if HV69_ON:                                                           # flat on the base flange for the Pc connector hex (r 25 / 142 deg)
        bcuts.append(apply(box((18.0, -15.0, zb0 - 1), (30.0, 15.0, zb0 + 6.0)), T_rot("z", pc_ang)))
    for a in ANG["bonnet_bolts"]:
        c = polar(16.5, a)
        bcuts += [cyl(4.5, zb0 - 1, zb0 + 6, c[0], c[1]), cyl(7.5, zb0 + 5.0 - 0.01, zb0 + 12, c[0], c[1])]
    if E1M_ON:
        bcuts += cuts_e1m
    else:
        bcuts.append(cyl(13.0, zb0 + 18.0, zb0 + 31.0, rin[0], rin[1]))        # 9/16-18 UNF (-6 SAE J1926 ORB) tap drill, axial
        bcuts.append(cyl(22.5, zb0 + 29.0, zb0 + 31.0, rin[0], rin[1]))        # ORB spot face
        bcuts.append(cyl(10.0, zb0 + 15.5, zb0 + 18.01, rin[0], rin[1]))       # 40 um sintered screen seat 10 x 2.5 under the ORB port
        bcuts.append(cyl(6.0, zb0 + 9.0, zb0 + 15.6, rin[0], rin[1]))          # riser bore
        bcuts.append(radial_hole(6.0, ANG["inlet"], zb0 + 12.0, 3.0, 34.5))     # cross-drilling to the manifold, outer end plugged (HW Lee plug)
    if not HV69_ON:
        for (gx, gy) in S["guide_pins_xy"]:                                 # guide-pin bores 5 P7 x 6 deep in the top flange
            bcuts.append(cyl(5.0, zb1 - 7.5, zb1 + 1, gx, gy))
        bcuts.append(box((13.0, -20, zb1 - 5), (30, 20, zb1 + 1)))          # v3.2 flat on the top flange for the torch body
    bcuts.append(box((15.5, -25, zb0 - 1), (30, 25, zb0 + 6)))              # v3.2 flat on the base flange for the torch hex (0 deg)
    bon = cut_all(bon, bcuts)
    shp, T = localize(bon, zb0)
    if E1M_ON:
        tc04_name = "Bonnet: stem seal + guide housing, E1-M inlet boss (8 mm transfer, cross-drilling at the bore top, P_manifold tap), guide-pin flange"
        tc04_notes = ("v3.4 E1-M: oxidiser arrives from the TC-02 filter bore through the 8 mm axial drilling at r 16 / 180 deg (AS568-012 FKM 75 face "
                      "transfer seal in this bottom face), rises in the boss and enters the 10 mm bore through an 8 mm cross-drilling flush with the bore "
                      "top (flow-through manifold, no dead leg: Combustion C2); M10x1 port at the cross-drilling end = P_manifold tap or plug; v3.3 ORB "
                      "inlet, 40 um screen seat and 6 mm riser deleted (filter moved to TC-02, C5); 4x M4 A4-70 to TC-02; face seal AS568-013 FKM 75; "
                      "4 mm PTFE spring-energised rod seal (TO-VERIFY) + PTFE/25 % glass guide bushing; flats clear the torch")
        tc04_fits = ["stem bore 4.05 +0.02/0", "seal gland per vendor catalogue", "transfer groove 9.4/13.0 x 1.30 (AS568-012) at r 16 +/-0.05",
                     "M10x1-6H tap port", "guide-pin bores 5 P7 at (+/-9, 4.75) position 0.02 to the stem bore"]
    else:
        tc04_name = "Bonnet: stem seal + guide housing, -6 ORB ox inlet with 40 um screen (90 deg), carriage guide-pin flange"
        tc04_notes = ("4x M4 A4-70 to TC-02; face seal AS568-013 FKM 75; 4 mm PTFE spring-energised rod seal (e.g. Trelleborg Turcon Variseal M2, "
                      "gland per vendor, TO-VERIFY) + PTFE/25 % glass guide bushing; 40 um sintered 316L screen disc 10 x 2.5 under the -6 ORB inlet "
                      "(combustion.json filter moved into the inlet); 2x 5 P7 bores for the TC-17 guide pins; P_feed measured at the fixed hose end; "
                      "manifold volume with TC-02 bore ~3.3 cm3 (target <= 5); v3.2: flats at x 15.5 (base flange) and x 13 (top flange) clear the torch")
        tc04_fits = ["stem bore 4.05 +0.02/0", "seal gland per vendor catalogue", "9/16-18 UNF-2B SAE J1926-1 port",
                     "guide-pin bores 5 P7 at (+/-9, 4.75) position 0.02 to the stem bore", "screen seat 10 H8"]
    reg.add(Part("ENG-TC-04", tc04_name, "AL6061-T6", "CNC lathe + mill",
                 shp, drawing=True, wetted="N2O", notes=tc04_notes,
                 dwg={"datum": "bottom face A", "fits": tc04_fits, "finish": "clear anodise; oxygen-clean", "ht": "T6"}
                 )).place(T, "engine")
    gb = tube(4.95, 3.03, zb1 - 4.0, zb1) if HV69_ON else tube(5.95, 4.03, zb1 - 4.0, zb1)
    shp, T = localize(gb, zb1 - 4.0)
    reg.add(Part("ENG-TC-11", "Stem guide bushing 5/3 x 4 (PTFE + 25 % glass)" if HV69_ON else "Stem guide bushing 6/4 x 4 (PTFE + 25 % glass)",
                 "PTFE", "lathe from rod", shp, wetted="N2O",
                 supplier="PTFE-glass rod 10 mm: RS Components DK / Polyfluor", notes="press into TC-04 top")).place(T, "engine")

    # ------------------------------------------------------------------ TC-10 face insulator disc
    disc = tube(2 * r_pre - 0.2, (2 * (S.get("tc03_nose_r", TC03_NOSE_R) + TC10_NOSE_GAP)) if S.get("tc03_nose_t", 0.0) > 0 else 20.4, zf, zf + face_rec)
    for (r_, a, d_) in [(20.5, pc_ang, 3.0), (S["torch_exit"][0] * 0 + np.hypot(*S["torch_exit"][:2]) + 0.6, ANG["torch"], 4.6)]:
        c = polar(r_, a)
        disc = disc.cut(cyl(d_, zf - 1, zf + face_rec + 1, c[0], c[1]))
    shp, T = localize(disc, zf)
    reg.add(Part("ENG-TC-10", "Injector-face insulator disc, phenolic 2 mm", "PHENOLIC", "water-jet or lathe from sheet", shp, hot=True, drawing=True,
                 supplier="glass- or paper-phenolic sheet 2 mm: RS Components DK / Rochling",
                 notes="bonded into the TC-02 face recess with RTV 106 (high-temperature silicone, outside the N2O path)")).place(T, "engine")

    # ------------------------------------------------------------------ TC-06 pre-chamber insulator, TC-07 liner, TC-08 post/convergent insulator
    lipH = v("prechamber_lip")
    pre = revolve([(r_pre, zf), (liner_or, zf), (liner_or, S["grain_top"]), (lip_r, S["grain_top"]), (lip_r, S["grain_top"] + lipH), (r_pre, S["grain_top"] + lipH)])
    r_key = v("D_grain_outer") / 2 - 0.4                                  # outer end of the GR-01 keys
    for a in (0, 180):                                                    # anti-rotation notches for the grain keys
        # v3.4: notch spans min..max(lip_r, r_pre) so a thicker TC-06 (r_pre < lip_r, TC-06 sizing study) builds
        # v3.4.1 rev B: ... and out to the key end + 0.5 (with D_pre 49.9 the notch stopped at r 25.5 and the keys, to r 26.55, overlapped
        # TC-06 by 2 x 4.3 mm3 in make_all checks)
        pre = pre.cut(box((-1.6, min(lip_r, r_pre) - 0.5, S["grain_top"] - 1), (1.6, max(lip_r, r_pre, r_key) + 0.5, S["grain_top"] + lipH + 0.01)).rotate((0, 0, 0), (0, 0, 1), a))
    shp, T = localize(pre, zf)
    reg.add(Part("ENG-TC-06", f"Pre-combustion chamber insulator (phenolic, bore {2*r_pre:.1f}, wall {liner_or-r_pre:.2f} mm, 30 mm long)", "PHENOLIC",
                 "lathe from phenolic tube", shp, hot=True, drawing=True,
                 notes=f"2 anti-rotation notches 3.2 x 2 for the grain keys (radially to r {max(lip_r, r_pre, r_key) + 0.5:.2f}, rev B); gas side {2*r_pre:.1f} mm "
                       + ("(v3.4.1: TC-06 3.6 mm, lead decision 2026-10-13 on the case over-temperature, Combustion v2.4 accepted D_pre 49.9 mm, L* -3.3 %; "
                          f"grain-seat counterbore {2*lip_r:.1f} x {lipH:.1f} = 0.05 mm relief, may be omitted)" if r_pre < lip_r
                          else "per combustion.json (grain seat lip 50 mm ID)"))).place(T, "engine")
    liner = tube(2 * liner_or, v("liner_ID"), S["grain_bot"], S["grain_top"])
    shp, T = localize(liner, S["grain_top"])
    reg.add(Part("ENG-TC-07", "Grain liner (phenolic tube 57.10/53.95)", "PHENOLIC", "cut from stock tube, OD sanded to slip fit",
                 shp, hot=True, drawing=True, supplier="paper- or glass-phenolic tube 2.25 x 0.0625 in class: Aerocon / Kinetic / RS Components DK",
                 notes=f"OD {2*liner_or:.2f} / ID {v('liner_ID'):.2f} x {S['grain_top']-S['grain_bot']:.1f} mm; replaceable with the grain")).place(T, "engine")
    zp = S["grain_bot"]
    r_ins0 = P["insert_r_start"]["v"] * 1e3
    prof = [(r, z) for z, r in S["contour"] if S["insert_top"] + 1e-6 < z < S["post_bot"] - 1e-6]
    r_bar = v("aft_bore_d") / 2 - 0.05                                     # 30.45: slip fit in the 61.0 H8 aft-section bore
    r_ib = S["r_insert_bore"]
    post_pts = [(lip_r, zp), (lip_r, zp - lipH), (r_post, zp - lipH), (r_post, S["post_bot"])] + prof + \
               [(r_ins0, S["insert_top"]), (r_ib - 0.05, S["insert_top"]), (r_ib - 0.05, S["aft_step"]), (r_bar, S["aft_step"]), (r_bar, zp)]
    post = revolve(post_pts)
    shp, T = localize(post, zp)
    t_post = r_bar - r_post
    S["post_insul_t"] = t_post
    reg.add(Part("ENG-TC-08", f"Post-chamber + convergent insulator (phenolic, {t_post:.2f} mm over the post-chamber, contour per combustion v2)", "PHENOLIC",
                 "lathe from glass- or silica-phenolic rod/tube", shp, hot=True, drawing=True,
                 notes=f"v3.2: OD {2*r_bar:.1f} (slip in the 61.0 H8 aft-section bore) over the post-chamber, steps to {2*r_ib-0.1:.1f} at the aft-section "
                       f"bore step; gas side: lip 50 mm ID (grain aft seat), 53.9 mm post-chamber, combustion contour v2 down to r = {r_ins0:.0f} mm; "
                       f"min thickness {P['post_insul_min_t']['v']*1e3:.1f} mm over the steel; top face carries the case end face and TC-07; seats on the aft-section step and NZ-01/NZ-02",
                 dwg={"datum": "top face A, axis B", "fits": [f"OD {2*r_bar:.2f} h9", f"spigot {2*r_ib-0.1:.2f} h9", "gas contour profile 0.1 to A/B"],
                      "finish": "as turned", "ht": "-"}
                 )).place(T, "engine")

    # ------------------------------------------------------------------ GR-01 grain (helical port)
    Lg = S["grain_top"] - S["grain_bot"]
    gr_od = v("D_grain_outer")
    dport = v("D_port0")
    nseg = max(1, math.ceil(Lg / v("max_print_height") - 1e-9))
    seg = Lg / nseg
    port = helical_port(dport, v("port_helix_r"), v("port_helix_pitch"), S["grain_bot"] - 1, S["grain_top"] + 1)
    for i in range(nseg):
        ztop = S["grain_top"] - i * seg
        zbot = ztop - seg
        g = cyl(gr_od, zbot, ztop).cut(port)
        if i == 0:
            for a in (0, 180):                                            # anti-rotation keys into the TC-06 notches
                g = g.fuse(box((-1.4, lip_r - 0.3, ztop), (1.4, gr_od / 2 - 0.4, ztop + lipH - 0.2)).rotate((0, 0, 0), (0, 0, 1), a))
        shp, T = localize(g, ztop)
        reg.add(Part(f"ENG-GR-{i+1:02d}", (f"Fuel grain {i+1}/{nseg}: ABS {gr_od:.1f} OD x {seg:.0f}, helical port {dport:.0f} mm (helix r {v('port_helix_r'):.0f}, pitch {v('port_helix_pitch'):.0f})"
                      if v('port_helix_r') > 1e-6 else f"Fuel grain {i+1}/{nseg}: ABS {gr_od:.1f} OD x {seg:.1f}, straight centred port {dport:.0f} mm (grain v2 S230)"),
                     "ABS", "FDM print ABS 100 % infill, concentric perimeters", shp, hot=True,
                     petg={"orientation": "axis vertical, keys up", "infill": "100 %", "comp": "OD -0.15 mm, port +0.2 mm",
                           "note": "flight part is ABS (combustion.json); the PETG copy is a fit check only"},
                     notes="port per combustion grain v2 S230 (lead relay; combustion.json v1 was a helical port); replaced every flight (ENG-06); weigh each grain (density ASSUMED 1000 kg/m3); total mass 0.404 kg per Combustion"
                     )).place(T, "engine")

    # ------------------------------------------------------------------ NZ-01 graphite insert, NZ-02 sleeve, NZ-03 gasket
    zi, zib = S["insert_top"], S["insert_bot"]
    zsh = S["insert_shoulder"]
    r_io = v("insert_OD") / 2
    r_sp = v("insert_spigot_d") / 2
    gas = [(r, z) for z, r in S["contour"] if z < zi - 1e-6]
    gas = [(r_ins0, zi)] + gas + [(S["re"], zib)]
    ins = revolve(gas + [(r_sp, zib), (r_sp, zsh), (r_io, zsh), (r_io, zi)])
    # v3.5.2 N-F2 (lead CHANGELOG 212): R on the shoulder outer edge (circle r_io at z_sh), a true fillet applied before the vent grooves
    _shR = (P.get("nz01_shoulder_R") or {}).get("v")
    if _shR:
        _e = [e for e in ins.Edges() if e.geomType() == "CIRCLE" and abs(e.radius() - r_io) < 1e-3 and abs(e.Center().z - zsh) < 1e-3]
        assert len(_e) == 1, f"NZ-01 shoulder edge not unique: {len(_e)}"
        ins = ins.fillet(float(_shR) * 1000.0, _e)
        S["nz01_shoulder_R_mm"] = float(_shR) * 1000.0
    ins = cut_all(ins, [apply(box((r_io - 0.5, -0.5, zsh + 1.0), (r_io + 1.0, 0.5, zi + 1.0)), T_rot("z", a)) for a in (45.0, 135.0, 225.0, 315.0)])
    shp, T = localize(ins, zi)
    reg.add(Part("ENG-NZ-01", f"Graphite throat insert (Dt {2*S['rt']:.2f}, De {2*S['re']:.2f}, OD {2*r_io:.0f}, aft spigot {2*r_sp:.0f})", "GRAPHITE-ISO",
                 "CNC lathe from isomolded graphite rod (dust extraction, sharp carbide)", shp, drawing=True, hot=True,
                 supplier="isomolded graphite rod 50 mm (Toyo Tanso IG-110 / SGL R6510 class): Schunk Carbon / Mersen / graphite-shop.de",
                 notes=f"gas-side contour from combustion nozzle_contour (v2: +30 mm), exit extended 3 mm at the exit diameter; OD 44 h9 in the 3 mm sleeve NZ-02; "
                       f"aft spigot {2*r_sp:.0f} h9 x {zsh-zib:.1f} through the closure lip (bottom face flush with the lip = aft-most face); shoulder on "
                       + ("the J1 stack (2.0 mm carbon-phenolic hot layer NZ-03 on a 0.5 mm flexible-graphite lip-face seal NZ-04); shoulder face lapped flat 0.01 "
                          "(the hot-layer contact is the only barrier on the path insert-OD gap -> shoulder -> spigot annulus); " if S.get("nozzle_joint") in ("J1", "J2")
                          else "the 1 mm mica gasket; ")
                       + "4 axial vent grooves 1.0 x 0.5 on the OD (sleeve gap at chamber pressure: hoop stress compressive, hand_calcs v2)",
                 dwg={"datum": "shoulder face A, axis B", "fits": ["OD 44.0 h9 (0/-0.062)", f"spigot {2*r_sp:.1f} h9 (0/-0.052)", f"throat {2*S['rt']:.3f} +0.02/0 (gauge pin)",
                                                                  "contour profile 0.05 to A/B", "shoulder face A perpendicular to B 0.02"]
                                                                 + ([f"shoulder outer edge R {S['nz01_shoulder_R_mm']:.1f} +/-0.2 tangent (v3.5.2 N-F2, lead 212)"] if S.get("nz01_shoulder_R_mm") else []),
                      "finish": "as turned Ra 1.6 gas side; no coating", "ht": "-"}
                 )).place(T, "engine")
    r_bore = r_io + v("insert_sleeve_t")
    slv = tube(2 * r_bore - 0.05, 2 * r_io + 0.02, zsh, zi)
    shp, T = localize(slv, zi)
    J1 = S.get("nozzle_joint") in ("J1", "J1B", "J2")   # J2 (SCREEN 2026-10-13): J1 stack geometry, zirconia hot layer NZ-03
    J1B = S.get("nozzle_joint") == "J1B"
    J2 = S.get("nozzle_joint") == "J2"
    smat = P["insert_sleeve_material"]["v"] if "insert_sleeve_material" in P else "PHENOLIC"
    if smat == "CARBON-PHENOLIC":
        s_name, s_mfg = "carbon-phenolic", "lathe from carbon-fabric/phenolic tube (tape-wrapped or moulded; supplier TO-SOURCE, TO-QUOTE Sonderborg DK-6400)"
        s_note = ("v3.4.1: carbon-phenolic (was glass/silica phenolic): NZ-02 peaks 1551 C in the B1 p99 soak, E-glass softens far below that and silica "
                  "reacts with graphite above ~1500 C (Combustion nozzle_joint_v2p4 side finding, AS RECALLED); carbon char is compatible with the "
                  "graphite insert; material data ASSUMED (engmat v1.2), char depth/shrinkage TO-VERIFY at T1 (section after firing)")
    else:
        s_name, s_mfg = "phenolic", "lathe from glass- or silica-phenolic tube"
        s_note = "v3.2: 3 mm (was 2) to slow the soak-back of the insert into the aft section"
    reg.add(Part("ENG-NZ-02", f"Insert insulating sleeve ({s_name} {2*r_bore:.0f}/{2*r_io:.0f}, {v('insert_sleeve_t'):.0f} mm)", smat,
                 s_mfg, shp, hot=True, drawing=True,
                 notes=s_note + ("; stands on the J1 hot layer NZ-03 with the insert shoulder" if J1 else "; stands on the mica gasket with the insert shoulder"))
            ).place(T, "engine")
    if J1:
        # v3.4.1 nozzle joint J1 (Combustion nozzle_joint_v2p4.json b5f396c7155c06c4; lead 2026-10-13): split functions, bearing thermal break on
        # the hot side (carbon-phenolic), seal on the cold lip face (flexible graphite).  Washer form chosen over a top-hat NZ-02 so the plies
        # lie parallel to the faces (lowest through-thickness k, bearing across the plies) and the hot layer can be replaced alone.
        z_seal_top = S["lip_top"] + S["nz_seal_t"]
        z_hl_bot = z_seal_top + S.get("nz_mica_t", 0.0)
        if J1B:
            # J1b SCREEN (coordinator 2026-10-13): mica/vermiculite insulating layer between the seal and the hot layer (not the v3.4.1 baseline)
            mk = tube(2 * r_bore - 0.2, 2 * r_sp + 0.6, z_seal_top, z_hl_bot)
            shp, T = localize(mk, z_hl_bot)
            reg.add(Part("ENG-NZ-05", f"Nozzle-joint insulating layer J1b (SCREEN): mica/vermiculite ring {2*r_sp+0.6:.1f}/{2*r_bore-0.2:.1f} x {S['nz_mica_t']:.2f}",
                         "MICA", "cut from sheet (water-jet / punch)", shp, hot=True,
                         supplier="phlogopite-mica or vermiculite gasket sheet (Flexitallic Thermiculite 866 / Klinger Milam PSS class), TO-QUOTE Sonderborg DK-6400",
                         notes="J1b screen: insulating layer behind the carbon-phenolic hot layer (sees its back face, 900 C class); not in the baseline")
                    ).place(T, "engine")
        z_foil_bot = zsh - S.get("nz_foil_t", 0.0)            # v3.5.2 N-F2: hot layer top = foil bottom (= zsh without the foil)
        hl = tube(2 * r_bore - 0.2, 2 * r_sp + 0.6, z_hl_bot, z_foil_bot)
        shp, T = localize(hl, z_foil_bot)
        if J2:
            # J2 SCREEN (Combustion nozzle_joint_v2p4 candidate J2; coordinator 2026-10-13 "re-run the J1 and J2 nozzle-joint FE"): dense
            # fully stabilised zirconia washer at the J1 hot-layer thickness (2.0 mm, Combustion range 1.5-2.0), same seal NZ-04
            reg.add(Part("ENG-NZ-03", f"Nozzle-joint hot layer J2 (SCREEN): zirconia washer {2*r_sp+0.6:.1f}/{2*r_bore-0.2:.1f} x {S['nz_hot_layer_t']:.1f}",
                         "ZIRCONIA-FS", "COTS ceramic washer, ground and lapped faces (supplier machining)", shp, hot=True, drawing=True,
                         supplier="dense fully stabilised zirconia (Y-FSZ / Mg-FSZ) washer, lapped: supplier TO-SOURCE, price TO-QUOTE Sonderborg DK-6400",
                         notes="J2 screen only (not the v3.4.1 baseline): bearing thermal break in compression; risks named by Combustion: thermal-shock "
                               "cracking (acceptable only while confined and in compression) and k ~2-2.5 W/m/K raising the seal-face and lip "
                               "temperature (FE: 04-fea REPORT J1/J2 comparison); material data AS RECALLED (engmat v1.4 ZIRCONIA-FS), TO-VERIFY",
                         dwg={"datum": "face A", "fits": [f"ID {2*r_sp+0.6:.1f} +0.1/0", f"OD {2*r_bore-0.2:.1f} 0/-0.1", f"t {S['nz_hot_layer_t']:.2f} +/-0.01",
                                                         "faces parallel 0.005, flat 0.003 (lapped)"], "finish": "faces lapped Ra 0.2", "ht": "-"})
                    ).place(T, "engine")
        else:
          reg.add(Part("ENG-NZ-03", f"Nozzle-joint hot layer J1: carbon-phenolic washer {2*r_sp+0.6:.1f}/{2*r_bore-0.2:.1f} x {S['nz_hot_layer_t']:.1f}",
                     "CARBON-PHENOLIC", "water-jet + face-grind from carbon-fabric/phenolic laminate plate (plies parallel to the faces)", shp, hot=True, drawing=True,
                     supplier="carbon-fabric / phenolic laminate plate >= 2.5 mm (aerospace ablative or industrial carbon-phenolic laminate makers): supplier TO-SOURCE, "
                              "price TO-QUOTE Sonderborg DK-6400",
                     notes="J1 hot layer: bearing thermal break between the graphite insert shoulder (1595 C face, v3.4 FE) and the lip-face seal; "
                           "bearing 10.6 MPa at BN 63.1 bar (Combustion requirement: >= 1700 C service, strength >= 2x bearing at temperature, k <= ~1 W/m/K, "
                           "no SiO2 against graphite); chars in service (pressure-energised preload: the insert follows the stack); faces flat 0.01, Ra 0.8; "
                           "replace at every insert change; char depth / stack-height loss measured after each firing (T1). Material data ASSUMED (engmat v1.2)",
                     dwg={"datum": "face A", "fits": [f"ID {2*r_sp+0.6:.1f} +0.1/0", f"OD {2*r_bore-0.2:.1f} 0/-0.1", f"t {S['nz_hot_layer_t']:.2f} +/-0.02",
                                                     "faces parallel 0.01, flat 0.01"], "finish": "faces ground Ra 0.8", "ht": "post-cure per laminate maker"})
                ).place(T, "engine")
        if S.get("nz_foil_t", 0.0) > 0.0:
            # v3.5.2 N-F2 (lead CHANGELOG 212): load-spreading foil between the hot layer and the insert shoulder / sleeve
            fo = tube(2 * r_bore - 0.2, 2 * r_sp + 0.6, z_foil_bot, zsh)
            shp, T = localize(fo, zsh)
            reg.add(Part("ENG-NZ-06", f"Nozzle-joint load-spreading foil (v3.5.2 N-F2): flexible graphite ring {2*r_sp+0.6:.1f}/{2*r_bore-0.2:.1f} x {S['nz_foil_t']:.2f}",
                         "FLEX-GRAPHITE-TH", "cut from roll foil (steel-rule die / water-jet)", shp, hot=True,
                         supplier="flexible graphite roll foil 0.25 mm, >= 99.85 % C, 1.0 g/cm3 (SGL SIGRAFLEX TH class, datasheet "
                                  "https://www.sglcarbon.com/pdf/SGL-Datasheet-SIGRAFLEX-TH-NH-THP-S-HP-UHP-Foil-EN.pdf read 2026-10-13: roll thickness 0.25 mm, "
                                  "k 220 W/m/K parallel / 5 perpendicular, ~400 C in air / ~3000 C inert); grade and supplier TO-SELECT; price TO-QUOTE Sonderborg DK-6400",
                         notes="N-F2 (lead CHANGELOG 212): spreads the insert-shoulder bearing on the J1 hot layer NZ-03 towards the mean "
                               "(S-AX v3.5.1: NZ-03 TB70 node MS -0.158 at r 20.98 vs mean +0.063).  Sits at the 1500 C shoulder: above the ~400 C "
                               "in-air rating, relies on the confined joint (limited oxidant); char/oxidation loss TO-VERIFY at T1 (section after "
                               "firing); a lost foil leaves the R 1.0 shoulder edge only.  Replace at every insert change.  Material data in "
                               "engmat v352 FLEX-GRAPHITE-TH (k isotropic at the in-plane value = upper bound of radial spreading)")
                    ).place(T, "engine")
        sl = tube(2 * r_bore - 0.2, 2 * r_sp + 0.6, S["lip_top"], z_seal_top)
        shp, T = localize(sl, z_seal_top)
        reg.add(Part("ENG-NZ-04", f"Nozzle-joint lip-face seal J1: flexible graphite ring {2*r_sp+0.6:.1f}/{2*r_bore-0.2:.1f} x {S['nz_seal_t']:.1f}, oxidation-inhibited",
                     "FLEX-GRAPHITE-OI", "cut from sheet (steel-rule die / water-jet)", shp, hot=True,
                     supplier="flexible graphite sheet 0.5 mm, oxidation-inhibited grade, >= 98 % C (SGL SIGRAFLEX / GrafTech GRAFOIL / Klinger graphite class; "
                              "grade TO-SELECT with the supplier: service rating >= 527 C required = J1 in-burn FE peak 427.1 C + 100 K, j1_check v1.1); "
                              "price TO-QUOTE Sonderborg DK-6400",
                     notes="J1 seal on the cold lip face (seal S14 -> NZ-04): gas-tight at MEOP 45 bar, seated by the insert at BN 63.1 bar; service limit = class "
                           "rating minus 100 K (rating TO-VERIFY with the grade; FE in 04-fea REPORT); lip face flat 0.02, Ra <= 1.6; replace at every insert change. "
                           "LEAK-PATH NOTE (Mechanical 2026-10-13): this seal blocks the outer path (sleeve OD / holder bore -> lip face -> spigot annulus) but NOT the "
                           "inner path (insert-OD vent gap -> insert shoulder / hot-layer contact -> spigot annulus); that path is closed only by the hot-layer "
                           "bearing contact (lapped faces), TO-VERIFY by the H19 N2 decay check at 67.5 bar before and after every firing. "
                           "Soak peaks above the in-burn value (B1 737.5 C, A1 578.2 C, J1 FE) exceed the ~650 C oxidation limit quoted for inhibited grades "
                           "(TO-VERIFY): matters only if reached before a relight (04-fea REPORT, A1 coast history). J1 confirmed (lead 2026-10-13); J1b "
                           "(0.5 mm phlogopite mica rated >= 1002 C behind the hot layer) is the contingency only if S-AX fails the J1 lip")
                ).place(T, "engine")
    else:
        gk = tube(2 * r_bore - 0.2, 2 * r_sp + 0.6, S["lip_top"], zsh)
        shp, T = localize(gk, zsh)
        reg.add(Part("ENG-NZ-03", f"Insert shoulder gasket ring {2*r_sp+0.6:.1f}/{2*r_bore-0.2:.1f} x {S['gasket_t']:.1f}, mica/vermiculite high-temperature gasket", "MICA",
                     "cut from sheet (water-jet / punch)", shp, hot=True,
                     supplier="phlogopite-mica or vermiculite gasket sheet 1.0 mm (Flexitallic Thermiculite 866 / Klinger Milam PSS class): Klinger Denmark / Flexitallic distributor (TO-QUOTE)",
                     notes="v3.2: insulating face seal between the insert shoulder/sleeve and the aft-section lip (bearing 10.6 MPa at BN 63.1 bar); replaces the 0.5 mm Grafoil ring "
                           "(through-thickness k ~5 W/m/K short-circuited the insert); through-thickness k TO-VERIFY with the supplier (0.2-0.6 W/m/K used in 04-fea); "
                           "replace at every insert change. v3.4 seal_table_v1: S14 FAILS (1595 C vs 900 C class) -> J1 in v3.4.1")).place(T, "engine")

    # ------------------------------------------------------------------ TC-09 aft section v3.2 (post-chamber + nozzle holder, threaded socket)
    za = S["tube_aft"]                                                      # case end face = grain aft face plane
    amat = P["aft_section_material"]["v"]
    R_s = 36.0                                                              # socket OD 72 over the M63x1.5 thread and the gland
    r_bb = v("aft_bore_d") / 2 + 0.03                                       # 30.53: post-chamber bore 61.0 H8 = land bore
    R_b = v("aft_bore_d") / 2 + v("aft_wall_t")                             # barrel OD
    # v3.5.2 (lead CHANGELOG 206 (2a), 2026-10-13, Mechanical): TC-09 thinning, accepted only if the thermal + S-AX re-run (not 1/t
    # scaling) meets 183 (1) with the 194 period domain.  tc09_barrel_wall = radial wall of the barrel over the 61.06 bore (m; v3.5.1 2.47 mm);
    # tc09_socket_R2 = socket OD radius (m) above the gland band (v3.5.1 36.0 mm everywhere); the holder keeps aft_wall_t.
    _tbw = (P.get("tc09_barrel_wall") or {}).get("v")
    _rs2 = (P.get("tc09_socket_R2") or {}).get("v")
    if _tbw:
        R_b = r_bb + float(_tbw) * 1000.0
    r_ib = S["r_insert_bore"]
    R_h = r_ib + v("aft_wall_t")                                            # insert-holder OD
    gro = r_land_aft + 2.75                       # rod gland groove radius (diameter 66.5) for 3.53 CS (hand_calcs v2: squeeze 17.9-23.8 %)
    zg0 = za + 2.0
    S["aft_gland"] = (zg0, gw, 2 * gro)
    r_lb = v("lip_bore_d") / 2
    zst = S["aft_step"]
    z_sock_bot = za - 4.0
    # v3.4.1 rev B (2026-10-13, found by the S-AX structural mesh): the 45 deg holder-to-barrel cone started 2.5 mm below the bore step and
    # passed 0.38 mm INSIDE the inner step corner (r_bb, zst): the turned part was two rings joined along a circle (zero wall).  The cone
    # now starts low enough to leave the barrel wall thickness, measured normal to the cone, at that corner (+~34 g of 316L).
    t_w = v("aft_wall_t")
    z_c0 = min(zst - 2.5, zst + (R_h - r_bb) - math.sqrt(2.0) * t_w)
    S["aft_cone"] = {"z_start": z_c0, "z_end": z_c0 + (R_b - R_h), "wall_normal_at_step_mm": ((R_h - z_c0) - (r_bb - zst)) / math.sqrt(2.0)}
    if _rs2:                                                                # v3.5.2: socket OD stepped to R_s2 2.0 mm above the gland groove (45 deg)
        R_s2 = float(_rs2) * 1000.0
        z_sstep = zg0 + gw + 2.0
        sock = [(R_s, z_sock_bot), (R_s, z_sstep), (R_s2, z_sstep + (R_s - R_s2)), (R_s2, zth)]
        S["aft_socket_step"] = {"R_s2": R_s2, "z_step": z_sstep, "z_step_end": z_sstep + (R_s - R_s2), "z_thread_top": zth,
                                "flat_width_mm": round(2.0 * math.sqrt(max(R_s2 ** 2 - 34.0 ** 2, 0.0)), 2)}
    else:
        sock = [(R_s, z_sock_bot), (R_s, zth)]
    ac = revolve([(r_lb, S["aft_bottom"]), (R_h, S["aft_bottom"]), (R_h, z_c0), (R_b, z_c0 + (R_b - R_h)), (R_b, z_sock_bot - (R_s - R_b))]
                 + sock + [(31.51, zth), (31.51, zl), (r_bb, zl), (r_bb, zst), (r_ib, zst),
                           (r_ib, S["lip_top"]), (r_lb, S["lip_top"])])
    ac = ac.cut(tube(2 * gro, 2 * r_bb, zg0, zg0 + gw))
    acuts = [cyl(1.6, S["aft_bottom"] - 1, S["aft_bottom"] + 5.0, 0.0, -21.0)]        # TC well 1.6 x 5 deep in the lip (retainer temperature)
    if S.get("nozzle_joint") in ("J1", "J2"):   # v3.4.1: second T1 well at the lip bore edge (Combustion nozzle_joint_v2p4 verification list), r 17.5 at 90 deg
        acuts.append(cyl(1.6, S["aft_bottom"] - 1, S["aft_bottom"] + 5.0, 0.0, 17.5))
    for a in (45, 135, 225, 315):                                                        # pin-spanner holes 4 x 3 deep
        c = polar(21.0, a)
        acuts.append(cyl(4.0, S["aft_bottom"] - 1, S["aft_bottom"] + 3.0, c[0], c[1]))
    ac = cut_all(ac, acuts)
    ac = ac.cut(box((34.0, -40, zth - 14.0), (40, 40, zth + 1))).cut(box((-40, -40, zth - 14.0), (-34.0, 40, zth + 1)))  # 68 A/F flats
    shp, T = localize(ac, za)
    S["aft_section"] = {"material": amat, "R_socket": R_s, "R_socket2": (float(_rs2) * 1000.0 if _rs2 else None), "R_barrel": R_b, "R_holder": R_h, "bore_post": 2 * r_bb, "bore_insert": 2 * r_ib,
                        "z_top": zth, "z_bottom": S["aft_bottom"], "z_step": zst}
    reg.add(Part("ENG-TC-09", f"Aft section v3.2: post-chamber barrel + nozzle holder + retaining lip ({amat}, M63x1.5 socket on the case)", amat,
                 "CNC lathe (bore from the forward end) + flats", shp, drawing=True, hot=True,
                 notes=f"v3.2 (lead relay 2026-10-12, soak-back / post-chamber wall): one piece from the thread top to the aft face, length {zth-S['aft_bottom']:.1f} mm. "
                       f"M63x1.5-6H x 14 on the case's external thread (fit 6H/6e: the aluminium male grows ~0.05 mm more than the steel at +100 K); "
                       f"AS568-229 FKM 75 rod gland (groove {2*gro:.1f} H9 x {gw}) on the case's 61.0 land; post-chamber bore {2*r_bb:.2f} (61.0 H8) for TC-08; "
                       f"bore step at z {zst:.1f}; insert bore {2*r_ib:.1f} H8 for NZ-02; lip {v('aft_lip_t'):.0f} mm on the insert shoulder through " + ("the J1 stack (NZ-04 0.5 mm flexible-graphite seal on the lip face + NZ-03 2.0 mm carbon-phenolic hot layer), " if S.get("nozzle_joint") == "J1" else ("the J2 screen stack (NZ-04 0.5 mm flexible-graphite seal + NZ-03 2.0 mm zirconia washer), " if S.get("nozzle_joint") == "J2" else "the 1 mm mica gasket, "))
                       + f"bore {2*r_lb:.1f} H11 around the insert spigot (no metal in the plume); 68 A/F flats; 4 pin-spanner holes; TC well 1.6 x 5 in the lip at r 21" + (" and a second at the lip bore edge (r 17.5, 90 deg)" if S.get("nozzle_joint") in ("J1", "J2") else "") + "; "
                       "nickel anti-seize on the steel/aluminium thread (not N2O-wetted). Material per 04-fea LC5 (316L baseline; Ti-6Al-4V is the -0.2 kg option). "
                       f"Rev B (v3.4.1, 2026-10-13): holder-to-barrel 45 deg cone from z {S['aft_cone']['z_start']:.2f} to {S['aft_cone']['z_end']:.2f}, "
                       f"{S['aft_cone']['wall_normal_at_step_mm']:.2f} mm wall normal to the cone at the bore step (rev A had zero wall there: two rings)"
                       + (f". v3.5.2 (lead 206 (2a)): barrel wall {R_b - r_bb:.2f} mm (v3.5.1 2.47)" if _tbw else "")
                       + (f"; socket OD {2 * S['aft_socket_step']['R_s2']:.1f} from z {S['aft_socket_step']['z_step']:.2f} (2.0 above the gland groove, 45 deg) "
                          f"to the thread top, 68 A/F flats {S['aft_socket_step']['flat_width_mm']:.1f} mm wide (pin-spanner holes carry the torque)" if _rs2 else ""),
                 dwg={"datum": "socket face A (thread top), axis B", "fits": ["M63x1.5-6H (mating 6e on TC-01)", f"gland bore 61.0 H8, groove {2*gro:.2f} H9 x 4.85, Ra 0.8",
                                                                            f"post-chamber bore {2*r_bb:.2f} H8", f"insert bore {2*r_ib:.1f} H8 (+0.039/0)",
                                                                            f"lip bore {2*r_lb:.1f} H11 (+0.16/0)", "lip top face flat 0.02, perpendicular to B 0.03"],
                      "finish": "316L: glass-bead or as turned, passivate ASTM A967; Ti-6Al-4V: anti-gall coating on the thread", "ht": "316L solution-annealed (EN 10088-3 1.4404 +AT)"}
                 )).place(T, "engine")

    if HV69_ON:                                                           # v3.4: HV69 in-line drive, rolling-guide carriage, servo mount V3
        import parts_pintle
        parts_pintle.build_pintle_parts(P, S, reg)
    else:
        # ------------------------------------------------------------------ pintle actuator (v3): servo standing on the engine axis
        # Offset in-line crank-slider: crank on the servo spline (shaft along +Y, spline face y = 3), 18 mm link in the
        # plane y = 9.7, carriage TC-16 clamped to the needle top and guided on two 5 mm pins (TC-17) pressed into the
        # bonnet flange.  The couple F x 9.7 mm is taken by the guide bushings (friction ~0.1 x 2 x 100 N).
        Lp, Wp, Hp = [x * 1e3 for x in P["pintle_servo_box"]["v"]]           # 40.3, 20.2, 40.3 (H reserved)
        y_face = 3.0
        rc = P["pintle_crank_r_mm"]["v"]
        Lk = v("pintle_link_L")
        phi_c = math.radians(25.0)                                           # crank swing +/-25 deg (electronics.json)
        z_nt = S["z_needle_top"]
        z_k0 = z_nt - 3.0                                                    # carriage pin = needle cross-pin height, closed
        z_s = z_k0 + rc * math.sin(phi_c) + math.sqrt(Lk ** 2 - (rc * math.cos(phi_c)) ** 2)
        y_l = y_face + 6.7                                                   # link mid-plane (link y_face+5.2 .. +8.2)
        S["pintle_shaft"] = np.array([0.0, y_face, z_s])
        S["pintle_link"] = Lk
        S["pintle_geom"] = dict(y_face=y_face, rc=rc, Lk=Lk, z_s=z_s, z_k0=z_k0, y_l=y_l, phi_closed_deg=-25.0)
        Ts = T_basis((0.0, y_face, z_s), (0, 0, 1), (1, 0, 0), (0, 1, 0))  # servo local: X_s -> +Z (body up), Y_s -> +X, Z_s -> +Y
        S["pintle_servo_T"] = Ts
        sb = servo_shape(Lp, Wp, Hp)
        reg.add(Part("ENG-TC-13", f"Pintle throttle servo ({P['tvc_servo_model']['v']}, electronics.json), standing on the engine axis", "COTS-MIXED", "COTS", sb, cots=True,
                     mass_each_kg=P["pintle_servo_mass"]["v"], mass_tag=f"{P['pintle_servo_mass']['tag']} ({P['pintle_servo_mass']['src']})",
                     supplier="Lindinger (AT) item 9738546 per electronics.json v1", price="119.99 EUR incl. VAT (electronics.json v1, 2026-10-11; DK delivery TO-QUOTE)",
                     notes="body vertical, shaft along +Y; 4 ears (plane 11 mm below the spline face, ASSUMED class value) on the TC-12 plate; keep < 50 C"
                     )).place(Ts, "engine")
        # bracket TC-12: vertical plate behind the ears + web + foot on the head top (2x M4 into TC-02)
        yp0, yp1 = y_face - 11.0 - 2.5 - 4.0, y_face - 11.0 - 2.5                # plate y -14.5 .. -10.5
        zb_top = z_s + (Lp - 10.0) + 7.0 + 2.0
        zc_mid = z_s + (Lp - 10.0) / 2.0 - 5.0                                     # body centre along Z
        plate = box((-15.0, yp0, zt + 10.0), (15.0, yp1, zb_top))
        web = box((-15.0, -26.0, zt + 10.0), (15.0, yp1, zt + 14.5))
        foot = box((-15.0, -26.0, zt), (15.0, -20.5, zt + 14.5))
        brk = union_all([plate, web, foot])
        bcut = [box((-10.5, yp0 - 1, z_s - 10.4), (10.5, yp1 + 1, z_s + Lp - 10.0 + 0.4)),           # servo body window
                box((-11.5, yp0 - 1, zt + 9.0), (11.5, yp1 + 1, zt + 33.5))]                         # bonnet top-flange window
        for dz in (-24.75, 24.75):                                                                   # ear screws M4 (4x), tapped
            for dx in (-5.0, 5.0):
                bcut.append(cyl_dir(3.3, 6.0, (dx, yp0 - 1, z_s + (Lp - 20.0) / 2.0 + dz), (0, 1, 0)))
        for (hx, hy) in S["bracket_holes"]:
            bcut += [cyl(4.5, zt - 1, zt + 15, hx, hy), cyl(8.0, zt + 9.0, zt + 15, hx, hy)]
        brk = cut_all(brk, bcut)
        shp, T = localize(brk, zt)
        reg.add(Part("ENG-TC-12", "Pintle actuator bracket (servo plate + web + foot)", "AL6061-T6", "CNC mill (2 setups) from 30 mm plate",
                     shp, drawing=True,
                     notes="2x M4 into TC-02 (counterbored); servo ears on the -Y side of the ears with 4x M4 tapped; window clears the bonnet top flange",
                     dwg={"datum": "foot face A (head top), plate face B", "fits": ["ear-hole pattern 49.5 x 10 per received servo, position 0.1",
                                                                                    "M4 clearance 4.5 to TC-02 pattern (+/-10, -23.5)"],
                          "finish": "clear anodise", "ht": "T6"})).place(T, "engine")
        # crank TC-14 (closed position: phi = -25 deg about +Y)
        ph = -phi_c
        crank = union_all([cyl_dir(12.0, 5.0, (0, 0, 0), (0, 0, 1)), box((-3.0, -3.0, 2.0), (3.0, rc + 2.5, 5.0)),
                           cyl_dir(2.0, 7.2, (0, rc, 2.0), (0, 0, 1)), cyl_dir(3.0, 7.0, (0, 0, 5.0), (0, 0, 1)), cyl_dir(4.0, 2.0, (0, 0, 12.0), (0, 0, 1))])
        # local crank frame = servo frame (Y_s -> +X): rotate about Z_s (= +Y) by the crank angle
        Tc = Ts @ T_rot("z", math.degrees(ph))
        reg.add(Part("ENG-TC-14", f"Pintle crank r {rc:.2f} mm, 25T clamp hub (6061-T6) + AS5048A magnet post", "AL6061-T6",
                     "CNC mill/lathe + broached 25T spline (or COTS clamp horn re-machined)", crank, drawing=True,
                     notes="M3 clamp; 2 mm pin ISO 2338 h8 pressed; diametral 4 x 2 magnet (AS5048A) bonded on the 3 mm post end"
                     )).place(Tc, "engine")
        # link TC-15 between the crank pin and the carriage pin (plane y = y_l)
        Pc_ = np.array([rc * math.cos(ph), y_l, z_s + rc * math.sin(ph)])
        Pk_ = np.array([0.0, y_l, z_k0])
        link = union_all([box((-1.25, -1.5, 0.0), (1.25, 1.5, Lk)), cyl_dir(5.0, 3.0, (0, -1.5, 0), (0, 1, 0)), cyl_dir(5.0, 3.0, (0, -1.5, Lk), (0, 1, 0))])
        link = link.cut(cyl_dir(2.05, 5, (0, -2.5, 0), (0, 1, 0))).cut(cyl_dir(2.05, 5, (0, -2.5, Lk), (0, 1, 0)))
        reg.add(Part("ENG-TC-15", f"Pintle connecting link {Lk:.0f} mm (17-4PH)", "SS17-4PH-H1150", "CNC mill / wire EDM", link, drawing=True,
                     notes="2 mm pins ISO 2338 h8, eyes 2.00 H7; side load on the carriage <= F tan(9.6 deg)")).place(T_trans(*Pk_) @ T_axis_to(Pc_ - Pk_), "engine")
        # carriage TC-16 (closed position) and guide pins TC-17
        zk = z_k0
        car = box((-13.5, -3.0, zk - 4.0), (13.5, y_l + 4.5, zk + 4.0))
        ccut = [cyl(4.05, zk - 5, zk + 5), cyl_dir(2.0, 30.0, (-15, 0, zk), (1, 0, 0)),                       # stem bore + cross pin along X
                box((-3.6, y_l - 1.65, zk - 5.0), (3.6, y_l + 1.65, zk + 5.0)),                              # link slot
                cyl_dir(2.0, 20.0, (0, -1.0, zk), (0, 1, 0))]                                                  # link pin along Y
        for (gx, gy) in S["guide_pins_xy"]:
            ccut.append(cyl(7.0, zk - 5, zk + 5, gx, gy))                                                      # DU bushing 5/7 x 8 bores
        car = cut_all(car, ccut)
        shp, T = localize(car, zk)
        reg.add(Part("ENG-TC-16", "Pintle carriage (needle clamp + link clevis + 2 guide bushings)", "AL6061-T6", "CNC mill", shp, drawing=True,
                     notes="clamps the needle top with a 2 mm cross pin; pressed SKF PCM 050708 E (5/7 x 8, PTFE-lined) bushings; hard anodise",
                     dwg={"datum": "stem bore A, bottom face B", "fits": ["stem bore 4.00 H7", "bushing bores 7.00 H7 (press per SKF)", "link slot 3.10 +0.05/0",
                                                                        "guide-bore pattern (+/-9, 4.75) position 0.02 to A"],
                          "finish": "hard anodise 25 um", "ht": "T6"})).place(T, "engine")
        gp = cyl(5.0, 0.0, 20.0)
        reg.add(Part("ENG-TC-17", "Carriage guide pin 5 h6 x 20 (17-4PH, ground)", "SS17-4PH-H1150", "COTS dowel ISO 8734 5 m6 x 20 (A4) or ground 17-4PH", gp,
                     notes="pressed 7 mm into the TC-04 flange (v3.2: 22 -> 20 mm, pin top 1.5 mm under the servo body; bushings stay fully engaged at full stroke)",
                     supplier="ISO 8734 dowel 5 x 20 A1/A4: Bossard DK / Misumi")).place(T_trans(-9.0, 4.75, S["bonnet_top"] - 7.0), "engine")
        reg.parts["ENG-TC-17"].place(T_trans(9.0, 4.75, S["bonnet_top"] - 7.0), "engine")
        enc = box((-12.5, 0.0, -12.5), (12.5, 10.0, 12.5))
        reg.add(Part("ENG-EL-05", "Pintle-position encoder AS5048A PCB reservation 25x25x10 (electronics.json)", "COTS-MIXED", "COTS", enc, cots=True,
                     mass_each_kg=0.008, mass_tag="ASSUMED 5-12 g", supplier="ams AS5048A adapter board: Mouser DK / RS Components DK",
                     notes="faces the magnet on the crank post (air gap 1-2 mm); mounted on a 2 mm standoff arm from TC-12 (detail at the electronics fit check)"))
        reg.parts["ENG-EL-05"].place(T_trans(0.0, y_face + 15.5, z_s), "engine")      # v3.2: chip face 1.5 mm from the magnet (post end y_face + 14)

    # ------------------------------------------------------------------ IG-01 torch igniter envelope (v3.2) + IG-02 cartridge check valves
    tD, tL = [x * 1e3 for x in P["torch_env"]["v"]]
    torch = union_all([cyl(10.0, -10.0, 0.0),                       # M10x1 nose in the head seat (modelled at the major diameter)
                       cyl(17.0, 0.0, 6.0),                         # hex / seat flange (crush washer)
                       cyl(tD, 6.0, 6.0 + tL),                      # torch body envelope (Combustion v2: <= 20 x 45)
                       cyl(11.0, 6.0 + tL, 6.0 + tL + 15.0, 0.0, 5.5), cyl(11.0, 6.0 + tL, 6.0 + tL + 15.0, 0.0, -5.5)])   # 2 x 1/8 in inlet fittings
    m_t = P["torch_mass_engine"]["v"] + 0.010
    reg.add(Part("ENG-IG-01", f"Torch igniter (N2O/propane, spark) - ENVELOPE {tD:.0f} x {tL:.0f} mm + M10x1 nose + 2 inlet fittings (Combustion ignition_v2)", "COTS-MIXED",
                 "Combustion design (316L body, micro spark plug)", torch, cots=True, mass_each_kg=m_t,
                 mass_tag=f"ASSUMED body 50 g + plug 10 g (ignition_v2.json) + 2 fittings 10 g",
                 supplier="Combustion design: body CNC 316L, micro spark plug (model-engine class, TO-QUOTE)",
                 notes="v3.2 Mechanical counter-proposal (Combustion asked for a radial boss at x_face 15 inclined 30 deg, which sweeps beyond the 140 mm bay): "
                       "seated on the head top at 0 deg, r 25 (M10x1, crush washer); body parallel to the axis; fires through the TC-02 5.2 mm passage and "
                       "3 mm outlet drilled 30 deg inward/aft (face exit r 16.9, jet axis r 8 at x_face 15); 1/8 in lines from the fixed-side solenoids"))
    reg.parts["ENG-IG-01"].place(T_trans(*polar(TORCH_R, ANG["torch"], zt)), "engine")
    cv = cyl(5.5, 0.0, 9.0)
    reg.add(Part("ENG-IG-02", "Torch inlet check valve, cartridge insert in the torch inlet bore (N2O and propane, x2)", "COTS-MIXED", "COTS",
                 cv, cots=True, mass_each_kg=0.002, mass_tag="ASSUMED 1-3 g cartridge", wetted="N2O", bom_parent="",
                 supplier="Lee Company Chek cartridge (stainless, 5.5 mm class, cracking <= 0.3 bar, rated >= 45 bar) or Swagelok SS-CHS2 inline: TO-QUOTE",
                 notes="Combustion v2: check valve on each torch line at the torch inlet, rated to chamber MEOP 45 bar and hot gas; modelled inside the IG-01 envelope "
                       "(cartridge in the inlet bore below each fitting)"))
    ct = polar(TORCH_R, ANG["torch"])
    for dy in (5.5, -5.5):
        reg.parts["ENG-IG-02"].place(T_trans(ct[0], ct[1] + dy, zt + 6.0 + tL - 9.5), "engine")
    if E1M_ON:                                                            # v3.4: inlet block, cartridge, riser, shield, coil-end adapter
        parts_inlet.build_inlet_parts(P, S, reg)
        p2 = reg.parts["ENG-TC-02"]
        p2.name = "Injector head / forward closure (pintle seat bore, manifold, Pc and torch ports, E1-M filter bore and inlet flat)"
        _fr = 29.5 if S.get("jfd01_v352") else 30.5
        p2.notes += (f"; v3.4 E1-M: flat r {_fr:.1f} at 180 deg for the FD-01 block (" + ("v3.5.2: 3x M4-6H, 2 at y +/-8.5 / zb+5 full thread 9.0, 1 at y 0 / zb+24 full thread 6.5"
                     if S.get("jfd01_v352") else "2x M3 tapped") + "), radial 14 mm filter bore (axis 14 mm above the cap "
                     "bottom, flat bottom at r 9.5) holding the FD-02 cartridge, axial 8 mm at r 16 to the top face (transfer to TC-04)")
        p2.dwg["fits"] = list(p2.dwg.get("fits", [])) + ["filter bore 14.00 H8 Ra 0.8 (cartridge O-ring)", f"flat r {_fr:.2f} +/-0.05, Ra 0.8 (face seal)",
                                                         "axial 8 mm at r 16.00 +/-0.05, 180 deg"]
    return {"angs": angs}
