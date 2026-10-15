"""A1 head-end bleed, MODELLED in CAD v3.5 (run 6; replaces the v3.4.1 'designed-in provision' lines).  Mechanical, 2026-10-13.

Requests: lead CHANGELOG 166 (REV-ELEC-1 RE-10: "CAD run 6 must state the bleed topology explicitly: restrictor positions relative to
V1/V2, V1-V2 mid volume <= 0.5 cm3, P_mid transducer location, V2 vent path"), coordinator A (F3 restrictors 0.707 mm / 0.71 drill,
F2 inline <= 15 um element on the FD-01 leg, Cd.A >= 1.57 mm2; F1 valves 2 x Ø36 x 90 envelopes, mass risk) and B (valve target
<= 0.15 kg, seat >= 2 mm, 12 V NC).  Route: bleed_corridor_v35_v1.json (fixed 1/8 in line free sectors az 304-322 etc.).

Topology (flow order; every dimension tagged in BLEED below):
  T4 crown (TC-04 bonnet, filtered by FD-02) -> Ø1.5 drilling -> BL-01 tap block with R1 0.71 mm  ---\
  FD-01 riser leg (unfiltered) -> M8x1 port -> BL-02 adapter: <= 15 um sintered disc, then R2 0.71 mm -> integral tee
  -> BL-03E common line (engine) -> BL-04A elbow -> BL-04 -2 crossing hose (bundled 23 mm above the FD-07 coil, same sweep)
  -> BL-04B fixed sleeve -> BL-03F fixed line (corridor az 312, r 66) -> BL-10 inlet -> V1 (BL-05 #0)
  -> BL-07 manifold mid passage Ø1.5 (P_mid port -> BL-08 transducer) -> V2 (BL-05 #1) -> radial Ø3 vent -> BL-06 bulkhead through
  the bay wall at az 112 -> non-propulsive opposed tee outside (airframe ICD-14, TO-DEFINE, not modelled).
Both restrictors are UPSTREAM of V1 (at the engine taps); the lines between the restrictors and V1 sit at tap pressure when V1 is closed.
Tubes are routing polylines (rods + sphere joints, bores NOT modelled; mass from the annulus); bend radii R >= 10 mm at manufacture.
The Ø1.5 drilling from the TC-04 boss top into the T4 cavity crown is a TC-04 drawing operation (not cut in the v3.5 solid; no fit effect).
"""
from __future__ import annotations
import math
import numpy as np
import cadquery as cq
from partlib import Part
from geom import cyl_dir, union_all

DZ_HOSE = 23.0      # mm, DESIGN: BL-04 centreline = FD-07 centreline + 23 mm z (clears FD-05 top 88 by >= 3 mm at the elbow; FD-07 OD 16.2)
BLEED = {
    "tube": {"od": 3.175, "wall": 0.711, "tag": "STANDARD 1/8 x 0.028 in 316L seamless (ASTM A269)"},
    "hose": {"od": 6.4, "id": 2.4, "mass_kg_m": 0.07, "tag": "ESTIMATE -2 PTFE / 316 braid class (no datasheet; TO-VERIFY at selection)"},
    "restrictor_d_mm": 0.71, "restrictor_tag": "DESIGN (lead F3: 0.707 mm computed, 0.71 drill)",
    "element": {"rating_um": 15, "cdA_min_mm2": 1.57, "where": "BL-02, FD-01 leg, upstream of R2",
                "tag": "DESIGN requirement (lead F2); product TO-SELECT; dP-flow curve ESTIMATE in mechanical.json v2.1 bench list"},
    "t4_tap_xy": (-20.3, 0.0), "boss_top_z": 201.5, "t4_crown_z": 191.6,
    "fd01_tap": {"x": -41.5, "z": 159.2, "port": "M8x1 (bonded seal)", "src": "v3.4.1 provision note (riser leg crown)"},
    "valve": {"d": 36.0, "h": 90.0, "r": 48.0, "az": (26.0, 112.0), "z0": 265.0, "port_offset": 8.0, "mass_kg": 0.30,
              "tag": "ENVELOPE (lead F1, Ø36 x 90 kept); mass ASSUMED 0.30 kg = MASS RISK (target <= 0.15 kg, seat >= 2 mm, 12 V NC)"},
    "manifold": {"z0": 255.0, "z1": 265.0, "pad_d": 38.0, "bar_w": 14.0, "boss_d": 24.0, "boss_h": 3.0, "passage_d": 1.5, "vent_d": 3.0},
    "pmid": {"d": 22.0, "h": 55.0, "mass_kg": 0.050, "tag": "ENVELOPE Ø22 x 55 (Electronics selects; TE M3234 class ASSUMED, 50 g ASSUMED)"},
    "fixed_line": {"az": 312.0, "r": 66.0, "z_arc": 257.0, "az_end": 364.0},
    "mid_volume_budget_cm3": 0.5,
}
TUBE_KG_M = math.pi / 4.0 * (3.175e-3 ** 2 - (3.175e-3 - 2 * 0.711e-3) ** 2) * 7990.0   # 316L 7990 kg/m3 (EN 10088-1)


def pol(r, az, z):
    a = math.radians(az)
    return np.array([r * math.cos(a), r * math.sin(a), z])


def _u(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rodline(pts, d):
    """Polyline rod: cylinders + spheres at interior vertices (routing representation; bore not modelled)."""
    pts = [np.asarray(p, float) for p in pts]
    pieces, L = [], 0.0
    for p0, p1 in zip(pts[:-1], pts[1:]):
        l = float(np.linalg.norm(p1 - p0))
        L += l
        pieces.append(cyl_dir(d, l, tuple(p0), tuple(_u(p1 - p0))))
    for p in pts[1:-1]:
        pieces.append(cq.Solid.makeSphere(d / 2.0, cq.Vector(*p), angleDegrees1=-90, angleDegrees2=90))
    return union_all(pieces).clean(), L


def arc_points(r, z, az0, az1, step=6.0):
    n = max(2, int(math.ceil(abs(az1 - az0) / step)))
    return [pol(r, a, z) for a in np.linspace(az0, az1, n + 1)]


def hose_offset(pts_neutral, pts_posed=None, R=None):
    """BL-04 centreline: FD-07 centreline + DZ_HOSE, the offset rotated with the engine at the engine end and fixed at the fixed end."""
    X = np.asarray(pts_neutral if pts_posed is None else pts_posed, float)
    dz = np.array([0.0, 0.0, DZ_HOSE])
    off0 = dz if R is None else R @ dz
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    s = s / s[-1]
    return X + np.outer(1.0 - s, off0) + np.outer(s, dz)


def build_bleed_parts(P, S, reg):
    import parts_feed
    B, tb, hs, V, M = BLEED, BLEED["tube"], BLEED["hose"], BLEED["valve"], BLEED["manifold"]
    f = S["feed"]
    tq = "TO-QUOTE"
    topo = {"version": "v3.5", "frame": "engine frame mm, +Z forward, pivot origin (neutral pose)", "items": {}}

    # ---------------------------------------------------------------- BL-01 T4 tap block (engine)
    x0, y0 = B["t4_tap_xy"]
    zb = B["boss_top_z"]
    blk = cq.Workplane("XY").box(12.0, 12.0, 8.0, centered=(True, True, False)).translate((-22.0, 0.0, zb)).val()
    zp = zb + 4.0
    cuts = [cyl_dir(1.5, 4.0 + 0.01, (x0, y0, zb - 0.01), (0, 0, 1)), cyl_dir(1.5, 28.0 + x0 + 0.5, (x0, y0, zp), (-1, 0, 0)),
            cyl_dir(2.7, 8.2, (-25.5, 3.5, zb - 0.1), (0, 0, 1)), cyl_dir(2.7, 8.2, (-17.6, -3.5, zb - 0.1), (0, 0, 1))]
    for c in cuts:
        blk = blk.cut(c)
    reg.add(Part("ENG-BL-01", "Bleed tap block T4 crown (316L) with R1 0.71 mm restrictor insert, O-ring face seal to a Ø1.5 TC-04 drilling, 2 x M2.5",
                 "SS316L", "CNC-mill", blk.clean(), price=tq, drawing=False, wetted="N2O",
                 notes=f"R1 {B['restrictor_d_mm']} mm ({B['restrictor_tag']}) in the block; T4 gas is already filtered by FD-02. TC-04 drawing "
                       f"operation: Ø1.5 drilling from the boss top z {zb} to the T4 cavity crown z ~{B['t4_crown_z']} at ({x0}, {y0}) + 2 x M2.5 "
                       "tapped holes (NOT cut in the v3.5 TC-04 solid). Face O-ring size TO-SELECT (FFKM/FKM, N2O-compatible). Oxygen-clean.",
                 dwg={"finish": "pickled + passivated, oxygen-clean ASTM G93"})).place(np.eye(4), "engine")
    topo["items"]["R1"] = {"where": "ENG-BL-01 (on TC-04 boss top)", "at_mm": [x0, y0, zp], "d_mm": B["restrictor_d_mm"], "upstream_of": "V1"}

    # ---------------------------------------------------------------- BL-02 FD-01 tap adapter with element, R2 and integral tee (engine)
    fx, fz = B["fd01_tap"]["x"], B["fd01_tap"]["z"]
    t0 = _u(f["hose"][1] - f["hose"][0])                                  # hose start tangent at Q
    H0 = np.asarray(f["Q"], float) + np.array([0.0, 0.0, DZ_HOSE])     # BL-04 hose start
    port = H0 - 12.0 * t0                                                 # BL-04A vertical port axis (xy)
    xt, yt = float(port[0]), float(port[1])
    v351 = bool((P.get("bleed_tap_v351") or {}).get("v", False))
    if v351:   # v3.5.1 (bay wall, lead CHANGELOG 182 (5)): Ø10 x 10 adapter inclined 30 deg towards +x from (x -39, +y face); the v3.5 Ø12 x 12
        # radial adapter reached r 73.24 mm at the 8 deg stop (dir 155 deg) against the 69.0 mm limit; the tee sits 6.5 mm along the axis
        ua = np.array([math.sin(math.radians(30.0)), math.cos(math.radians(30.0)), 0.0])
        a0 = np.array([-39.0, 8.0, fz])
        ad = cyl_dir(10.0, 10.0, tuple(a0), tuple(ua))
        ad = ad.cut(cyl_dir(1.5, 10.2, tuple(a0 - 0.1 * ua), tuple(ua)))
        tee = a0 + 6.5 * ua
        S["bl02_tee_xy"] = (float(tee[0]), float(tee[1]))
        # v3.5.1 freeze fix (make_all attempt 2, 16:58Z: BL-02/FD-01 common 47.8 mm3 = the wedge (2/3) R^3 tan 30 = 48.1 mm3 of the Ø10 base
        # in the un-cut +y face): the spot face normal to the inclined axis is now CUT in FD-01 (Ø11, from the seat plane through a0 outwards;
        # deepest 2.75 mm at the +x rim; >= 2.6 mm wall left to the radial 8 mm passage, measured in v351/hw/fd01_spotface_check.json)
        if "ENG-FD-01" in reg.parts:
            fd = reg.parts["ENG-FD-01"]
            fd.shape = fd.shape.cut(cyl_dir(11.0, 4.0, tuple(a0), tuple(ua))).clean()
            fd.notes += ("; v3.5.1: spot face Ø11 normal to the BL-02 axis (30 deg towards +x from +y, seat plane through (-39.0, 8.0, z "
                         f"{fz}), deepest 2.75 mm at the +x rim), cut in the solid")
    else:
        ad = cyl_dir(12.0, 12.0, (fx, 8.0, fz), (0, 1, 0))
        ad = ad.cut(cyl_dir(1.5, 12.2, (fx, 7.9, fz), (0, 1, 0)))
        S["bl02_tee_xy"] = (xt, yt)
    reg.add(Part("ENG-BL-02", "Bleed tap adapter on FD-01 (316L): M8x1 port, <= 15 um sintered 316L disc, R2 0.71 mm, integral tee (T4 leg in, common out)",
                 "SS316L", "CNC-lathe", ad.clean(), price=tq, wetted="N2O",
                 notes=f"Element {B['element']['rating_um']} um, Cd.A >= {B['element']['cdA_min_mm2']} mm2 ({B['element']['tag']}), UPSTREAM of R2 "
                       "so that unfiltered FD-01 debris cannot block R2. FD-01 drawing operation: M8x1 port on the +y face at "
                       + (f"(x -39.0, z {fz}) on an axis inclined 30 deg towards +x (spot face normal to the axis) into the riser leg; v3.5.1 body "
                          "Ø10 x 10 (bay-wall sweep: the v3.5 Ø12 x 12 radial adapter reached r 73.24 mm at the 8 deg stop)" if v351 else
                          f"(x {fx}, z {fz}) into the riser leg") + " (not cut in the FD-01 solid). Oxygen-clean.")).place(np.eye(4), "engine")
    if v351:
        e_at, r2_at = a0 + 2.5 * ua, a0 + 4.5 * ua
    else:
        e_at, r2_at = np.array([fx, 10.0, fz]), np.array([fx, 12.0, fz])
    topo["items"]["element"] = {"where": "ENG-BL-02, FD-01 leg", "at_mm": [round(float(c), 2) for c in e_at], "rating_um": 15, "cdA_min_mm2": 1.57}
    topo["items"]["R2"] = {"where": "ENG-BL-02 downstream of the element", "at_mm": [round(float(c), 2) for c in r2_at], "d_mm": B["restrictor_d_mm"],
                           "upstream_of": "V1"}

    # ---------------------------------------------------------------- BL-03A T4 leg and BL-03E common line (engine)
    zt, zbt = fz + 6.0, fz - 6.0
    zport = H0[2] + 7.0
    if v351:   # v3.5.1: lines meet the inclined adapter's tee; BL-03E jogs back to the BL-04A port axis (bends R >= 10 mm at manufacture)
        zt, zbt = fz + 5.0, fz - 5.0
        tx, ty = S["bl02_tee_xy"]
        legA, LA = rodline([(-28.0, 0.0, zp), (-30.0, 0.0, zp), (-32.0, 3.0, zp), (tx, ty, 172.0), (tx, ty, zt)], tb["od"])
        legE, LE = rodline([(tx, ty, zbt), (tx, ty, zbt - 12.0), (xt, yt, zbt - 32.0), (xt, yt, zport)], tb["od"])
    else:
        legA, LA = rodline([(-28.0, 0.0, zp), (-30.0, 0.0, zp), (-32.0, 3.0, zp), (xt, yt, 172.0), (xt, yt, zt)], tb["od"])
        legE, LE = rodline([(xt, yt, zbt), (xt, yt, zport)], tb["od"])
    for pn, sh, L, what in (("ENG-BL-03A", legA, LA, "T4 leg BL-01 -> BL-02 tee"), ("ENG-BL-03E", legE, LE, "common line BL-02 -> BL-04A")):
        reg.add(Part(pn, f"Bleed line {what}: 1/8 x 0.028 in 316L, {L:.0f} mm developed (routing polyline; bends R >= 10 mm)", "SS316L", "cut-stock",
                     sh, mass_each_kg=round(TUBE_KG_M * L * 1e-3, 5), mass_tag=f"DERIVED annulus {TUBE_KG_M * 1e3:.1f} g/m x {L:.0f} mm",
                     price=tq, wetted="N2O", notes=f"{tb['tag']}; rod representation (bore not modelled). Swept outer r at the 8 deg stop stays "
                     "inside the existing FD-01 sweep (cone rule r_sweep exceeded locally there: existing open item)")).place(np.eye(4), "engine")

    # ---------------------------------------------------------------- BL-04 crossing hose (group 'hose') + end fittings
    hp = hose_offset(f["hose"])
    hose = parts_feed.sweep_tube(hp, hs["od"], hs["id"])
    Lh = float(np.sum(np.linalg.norm(np.diff(hp, axis=0), axis=1)))
    reg.add(Part("ENG-BL-04", f"Bleed crossing hose -2 class PTFE / 316 braid, bundled {DZ_HOSE:.0f} mm above the FD-07 coil (same sweep), {Lh:.0f} mm",
                 "PTFE", "COTS", hose, cots=True, mass_each_kg=round(hs["mass_kg_m"] * Lh * 1e-3, 4),
                 mass_tag=f"ESTIMATE {hs['mass_kg_m'] * 1e3:.0f} g/m x {Lh:.0f} mm", price=tq, wetted="N2O", supplier="TO-SELECT",
                 notes=f"{hs['tag']}; stiffness about the pivot TO-VERIFY (bench); bundle clips to FD-07 TO-DESIGN")).place(np.eye(4), "hose")
    e1 = union_all([cyl_dir(8.0, 16.0, tuple(H0 - 16.0 * t0), tuple(t0)), cyl_dir(8.0, 11.0, (xt, yt, H0[2] - 4.0), (0, 0, 1))]).clean()
    reg.add(Part("ENG-BL-04A", "Bleed hose end, engine side: crimp sleeve + 90 deg elbow port (316L)", "SS316L", "COTS", e1, cots=True,
                 mass_each_kg=0.008, mass_tag="ESTIMATE 8 g", bom_parent="ENG-BL-04", wetted="N2O", price=tq)).place(np.eye(4), "engine")
    Fq = np.asarray(f["Fq"], float)
    cd = _u(np.asarray(f["cdir"], float))
    H1 = Fq + np.array([0.0, 0.0, DZ_HOSE])
    S1 = H1 + 12.0 * cd
    e2 = cyl_dir(8.0, 12.0, tuple(H1), tuple(cd))
    reg.add(Part("ENG-BL-04B", "Bleed hose end, fixed side: crimp sleeve + tube stub (316L), clamped to the FD-09 clamp (extension TO-DESIGN)", "SS316L", "COTS",
                 e2, cots=True, mass_each_kg=0.006, mass_tag="ESTIMATE 6 g", bom_parent="ENG-BL-04", wetted="N2O", price=tq)).place(np.eye(4), "fixed")

    # ---------------------------------------------------------------- V1 / V2, manifold BL-07, P_mid BL-08, inlet BL-10, vent bulkhead BL-06
    FL = B["fixed_line"]
    C1, C2 = pol(V["r"], V["az"][0], 0)[:2], pol(V["r"], V["az"][1], 0)[:2]
    Mxy = 0.5 * (C1 + C2)
    u12 = _u(C2 - C1)
    zc = 0.5 * (M["z0"] + M["z1"])
    A_end = pol(FL["r"], FL["az_end"], FL["z_arc"])
    d_in = _u(C1 - A_end[:2])                                             # BL-10 axis (towards the V1 centre)
    P10 = C1 - (M["pad_d"] / 2.0) * d_in                                   # BL-10 seat on the V1 pad edge
    inlet_port = C1 - V["port_offset"] * d_in
    v1_out, v2_in = C1 + V["port_offset"] * u12, C2 - V["port_offset"] * u12
    u2r = _u(C2)
    v2_out = C2 + V["port_offset"] * u2r
    vent_end = C2 + (M["pad_d"] / 2.0) * u2r
    h = M["z1"] - M["z0"]
    body = [cq.Solid.makeCylinder(M["pad_d"] / 2.0, h, cq.Vector(*C1, M["z0"])), cq.Solid.makeCylinder(M["pad_d"] / 2.0, h, cq.Vector(*C2, M["z0"]))]
    Lc = float(np.linalg.norm(C2 - C1))
    ang = math.degrees(math.atan2(u12[1], u12[0]))
    bar = cq.Workplane("XY").box(Lc, M["bar_w"], h, centered=(True, True, False)).rotate((0, 0, 0), (0, 0, 1), ang).translate((*Mxy, M["z0"])).val()
    body += [bar, cq.Solid.makeCylinder(M["boss_d"] / 2.0, M["boss_h"], cq.Vector(*Mxy, M["z1"]))]
    man = union_all(body).clean()
    v_before = man.Volume()
    pd = M["passage_d"]
    Lin = float(np.linalg.norm(inlet_port - P10))
    cuts = [cyl_dir(pd, Lin + 0.1, (*(P10 - 0.1 * d_in), zc), (*d_in, 0)),                               # inlet passage BL-10 -> V1 in
            cyl_dir(pd, M["z1"] - zc + 0.1, (*inlet_port, zc), (0, 0, 1)),                                 # V1 inlet riser
            cyl_dir(pd, M["z1"] - zc + 0.1, (*v1_out, zc), (0, 0, 1)),                                     # V1 outlet riser   (mid volume)
            cyl_dir(pd, float(np.linalg.norm(v2_in - v1_out)), (*v1_out, zc), (*u12, 0)),                # mid passage       (mid volume)
            cyl_dir(pd, M["z1"] - zc + 0.1, (*v2_in, zc), (0, 0, 1)),                                      # V2 inlet riser    (mid volume)
            cyl_dir(pd, M["z1"] + M["boss_h"] - zc + 0.1, (*Mxy, zc), (0, 0, 1)),                          # P_mid riser       (mid volume)
            cyl_dir(M["vent_d"], M["z1"] - zc + 0.1, (*v2_out, zc), (0, 0, 1)),                            # V2 outlet riser
            cyl_dir(M["vent_d"], float(np.linalg.norm(vent_end - v2_out)) + 0.1, (*v2_out, zc), (*u2r, 0))]  # vent passage
    for c in cuts:
        man = man.cut(c)
    man = man.clean()
    v_cut = v_before - man.Volume()
    a = math.pi / 4.0 * pd ** 2
    rz = M["z1"] - zc
    mid = {"mid_passage_mm3": round(a * float(np.linalg.norm(v2_in - v1_out)), 1), "risers_v1out_v2in_mm3": round(2 * a * rz, 1),
           "pmid_riser_mm3": round(a * (rz + M["boss_h"]), 1)}
    mid["modelled_total_cm3"] = round(sum(mid.values()) / 1e3, 4)
    mid.update({"budget_cm3": B["mid_volume_budget_cm3"], "not_modelled": "valve outlet/inlet cavities and the transducer port dead volume "
                "(TO-VERIFY at selection); allowance left = budget - modelled", "allowance_left_cm3": round(B["mid_volume_budget_cm3"] - sum(
                v for k, v in mid.items() if k.endswith("mm3")) / 1e3, 4), "cut_volume_check_mm3": round(v_cut, 1)})
    reg.add(Part("ENG-BL-07", "Bleed valve manifold (6061-T6): V1/V2 pads, Ø1.5 mid passage with P_mid port, Ø3 V2 vent passage",
                 "AL6061-T6", "CNC-mill", man, price=tq, wetted="N2O", drawing=False,
                 notes=f"Mid volume (V1 outlet -> V2 inlet incl. P_mid riser) modelled {mid['modelled_total_cm3']} cm3 vs budget 0.5 cm3 "
                       f"(lead RE-10); valve and transducer cavities TO-VERIFY. Mount to the airframe TO-DEFINE (ICD-14). Valve sub-base "
                       f"ports {V['port_offset']} mm off the valve axis ASSUMED (TO-VERIFY at valve selection). Anodise; oxygen-clean.")).place(np.eye(4), "fixed")
    pv = reg.add(Part("ENG-BL-05", "Bleed valve 2/2 NC solenoid, 12 V, seat >= 2 mm, sub-base mount (ENVELOPE Ø36 x 90)", "SS316L", "COTS",
                      cq.Solid.makeCylinder(V["d"] / 2.0, V["h"], cq.Vector(0, 0, 0)), cots=True, mass_each_kg=V["mass_kg"],
                      mass_tag="ASSUMED 0.30 kg (MASS RISK; target <= 0.15 kg)", supplier="TO-SELECT", price=tq, wetted="N2O",
                      notes=V["tag"] + "; rated >= SEG-P 9.975 MPa, N2O-compatible seals, fail-closed. #0 = V1 (az 26), #1 = V2 (az 112)"))
    for c in (C1, C2):
        T = np.eye(4)
        T[:3, 3] = (c[0], c[1], V["z0"])
        pv.place(T, "fixed")
    pm = reg.add(Part("ENG-BL-08", "P_mid pressure transducer (ENVELOPE Ø22 x 55, Electronics selects) on the manifold boss", "SS316L", "COTS",
                      cq.Solid.makeCylinder(B["pmid"]["d"] / 2.0, B["pmid"]["h"], cq.Vector(0, 0, 0)), cots=True, mass_each_kg=B["pmid"]["mass_kg"],
                      mass_tag="ASSUMED 50 g", supplier="Electronics (TO-SELECT)", price=tq, wetted="N2O", notes=B["pmid"]["tag"]))
    T = np.eye(4)
    T[:3, 3] = (Mxy[0], Mxy[1], M["z1"] + M["boss_h"])
    pm.place(T, "fixed")
    reg.add(Part("ENG-BL-10", "V1 inlet fitting (316L): fixed line BL-03F into the manifold", "SS316L", "COTS",
                 cyl_dir(8.0, 6.0, (*(P10 - 6.0 * d_in), zc), (*d_in, 0)), cots=True, mass_each_kg=0.005, mass_tag="ESTIMATE 5 g",
                 price=tq, wetted="N2O")).place(np.eye(4), "fixed")
    reg.add(Part("ENG-BL-06", "V2 vent bulkhead fitting (316L) through the bay wall at az 112; outside: non-propulsive opposed tee (airframe ICD-14)",
                 "SS316L", "COTS", cyl_dir(10.0, 7.0, (*vent_end, zc), (*u2r, 0)), cots=True, mass_each_kg=0.010, mass_tag="ESTIMATE 10 g",
                 price=tq, wetted="N2O", notes="the opposed tee outside the wall is an airframe item (ICD-14, TO-DEFINE), not modelled")).place(np.eye(4), "fixed")

    # ---------------------------------------------------------------- BL-03F fixed line (corridor az 304-322, r 66; arc above the swept top)
    in_face = P10 - 6.0 * d_in
    pts = [S1, S1 + 6.0 * cd, pol(FL["r"], 290.0, 103.0), pol(FL["r"], FL["az"], 106.0)] + arc_points(FL["r"], FL["z_arc"], FL["az"], FL["az_end"]) \
        + [np.array([*(in_face - 5.0 * d_in), zc]), np.array([in_face[0], in_face[1], zc])]
    legF, LF = rodline(pts, tb["od"])
    reg.add(Part("ENG-BL-03F", f"Bleed line fixed side: 1/8 x 0.028 in 316L, {LF:.0f} mm developed (wall clamps to the airframe TO-DEFINE)", "SS316L",
                 "cut-stock", legF, mass_each_kg=round(TUBE_KG_M * LF * 1e-3, 5), mass_tag=f"DERIVED annulus x {LF:.0f} mm", price=tq,
                 wetted="N2O", notes=tb["tag"] + "; vertical run at az 312, r 66 inside the free corridor az 304-322 (bleed_corridor_v35_v1.json, "
                 "swept engine r <= 62.0 there); arc at z 257 above the swept engine top 251.9")).place(np.eye(4), "fixed")

    topo["items"].update({
        "V1": {"pn": "ENG-BL-05#0", "axis_xy_mm": [round(float(c), 2) for c in C1], "z_mm": [V["z0"], V["z0"] + V["h"]]},
        "V2": {"pn": "ENG-BL-05#1", "axis_xy_mm": [round(float(c), 2) for c in C2], "z_mm": [V["z0"], V["z0"] + V["h"]]},
        "P_mid": {"pn": "ENG-BL-08", "port_xy_mm": [round(float(c), 2) for c in Mxy], "z_port_mm": M["z1"] + M["boss_h"],
                  "position": "on the V1-V2 mid passage, chord midpoint (r 35.1, az 69)"},
        "mid_volume": mid,
        "vent": {"path": "V2 outlet riser Ø3 -> radial Ø3 passage -> ENG-BL-06 bulkhead at az 112 (r 67 -> 74) -> opposed NPV tee outside "
                         "(airframe ICD-14 TO-DEFINE)", "bulkhead_xy_mm": [round(float(c), 2) for c in vent_end], "z_mm": zc},
        "lines_mm": {"BL-03A": round(LA, 1), "BL-03E": round(LE, 1), "BL-04": round(Lh, 1), "BL-03F": round(LF, 1)},
        "volumes_upstream_of_V1_note": "restrictors R1/R2 at the taps: lines BL-03A/E, BL-04, BL-03F sit at tap pressure behind closed V1",
    })
    S["bleed"] = topo
    return S
