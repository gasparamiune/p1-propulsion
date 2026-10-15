"""v3.5.2 (lead CHANGELOG 206 (2b)) Ti-6Al-4V screws at non-wetted locations: exclusion rules, CAD distances to the N2O sources,
mass saving, preload over the soak range on the aluminium joints.  Mechanical, 2026-10-13, v1.  Units: N, mm, MPa, K (output SI-labelled).

Rules (lead 206 (2b); R3 threshold ASSUMED, line of sight not credited):
 R1  no Ti in a joint that clamps or is threaded into an N2O-wetted part or seal (CAD 'wetted' flag + hardware joint list)
 R2  no Ti in the head-top zone (bonnet rod seal, inlet, bleed tap and transducer ports vent there) or in the plume/nozzle zone
 R3  no Ti within D_R3 of any N2O-wetted part (TC-02 head counted whole: J-FWD / J-BON / port seals sit on it) at the neutral pose
 R4  strength-critical lines whose steel grade exceeds Ti-6Al-4V yield stay steel (12.9)
Strength (DATASHEET, supplier web pages, accessed 2026-10-13): TorqBolt (IN) ASTM F468 alloy Ti-5 R56400 table: machined specimen
Rm >= 130 ksi (896 MPa), Rp0.2 >= 120 ksi (827 MPa), A >= 10 %, 30-39 HRC; Accu Ltd (UK) 'Grade 5: >= 895 MPa' (SSCF-..-TI5 range).
Temperature knock-down, E and CTE: engmat TI6AL4V (LITERATURE-approx).  Purchase condition: certificate to ASTM F468 R56400 (or bar to
ASTM B348 Gr 5 / AMS 4928) per lot (TO-VERIFY at quote).
"""
import sys, json, math, hashlib
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import numpy as np
import cadquery as cq
import config, build, engmat

OUT = "/home/claude/work/mechanical/v352/ti/ti_screws_v352_v1.json"
HW = json.load(open("/home/claude/work/mechanical/v351/engine/03-cad/src/data/hardware_v351.json"))
HOLES = json.load(open("/home/claude/work/mechanical/v351/hw/hole_census_v351.json"))
D_R3 = (50.0, 100.0)            # mm, ASSUMED thresholds (reported at both; 50 mm used for the v3.5.2 list)
T_ASM, T_MIN = 20.0, -20.0      # C; T_MIN ASSUMED cold soak / launch environment (TO-VERIFY airframe environment spec)
T_HOT = {"collar": (130.5, "SIM bound: case head-region O-ring monitor head_oring_lower B1 soak max 130.5 C (v351_TB1GC); collar on the case"),
         "frame": (80.0, "ASSUMED: fixed frame (GM-08/09/10/13/14, servo) has no thermal model (MISSING); sensitivity at 130.5 C")}
# ---------------------------------------------------------------- standard thread / head data (ISO 261/724/898-1, ISO 4762/7984/10642/7380; AS RECALLED)
TH = {"M2": dict(d=2.0, P=0.40, As=2.07, dh=2.4, dw=3.8), "M2.5": dict(d=2.5, P=0.45, As=3.39, dh=2.9, dw=4.5),
      "M3": dict(d=3.0, P=0.50, As=5.03, dh=3.4, dw=5.5), "M4": dict(d=4.0, P=0.70, As=8.78, dh=4.5, dw=7.0),
      "M5": dict(d=5.0, P=0.80, As=14.2, dh=5.5, dw=8.5)}
RHO = {"A4-70": 8000.0, "A4-80": 8000.0, "A2-70": 7900.0, "12.9": 7850.0}
FTY = {"A4-70": 450.0, "A4-80": 600.0, "A2-70": 450.0, "12.9": 1080.0}       # MPa, ISO 3506-1 / ISO 898-1 minima
# joint -> (host PN for the posed hole positions, hole kind, dir filter, clamped-part material, grip L_k mm, engagement L_e mm, T zone)
JOINT = {
    "J-COLLAR": ("ENG-GM-02", "M3 tap", None, "AL7075-T6", 5.05, 4.95, "collar"),
    "J-EL03": ("ENG-GM-03", "M2 tap", None, "AL6061-T6", 1.5, 3.0, "collar"),
    "J-FRAME-U": ("ENG-GM-09", "M5 cb", None, "AL6061-T6", 4.5, 7.5, "frame"),
    "J-FRAME-L": ("ENG-GM-10", "M5 cb", None, "AL6061-T6", 4.5, 7.5, "frame"),
    "J-BRKT": ("ENG-GM-10", "M4 cb", None, "AL6061-T6", 5.5, 6.5, "frame"),
    "J-SERVO": (("ENG-GM-13", "ENG-GM-14"), "M4 tap", 1, "AL6061-T6", 3.8, 6.0, "frame"),
    "ICD-1U": ("ENG-GM-09", "M5 tap", None, "AL6061-T6", 2.0, 8.0, "frame"),
    "ICD-1L": ("ENG-GM-10", "M5 tap", None, "AL6061-T6", 2.0, 8.0, "frame"),
    "ICD-2": ("ENG-FS-15", "M5 clr / M3 DIN7984 cb", 0, "AL6061-T6", 4.0, 6.0, "frame"),
    "J-PD01": ("ENG-PD-01", "M3 clr", None, "AL6061-T6", 6.0, 5.0, "frame"),
}
LINE2JOINT = {"HW-125": "ICD-1U", "HW-126": "ICD-1L", "HW-137": "ICD-2"}   # hardware 'joint' text -> JOINT key
R1_JOINTS = {"J-FWD", "J-BON", "J-FD01", "J-BL01", "J-FD08F", "J-FD12F", "J-MVP", "J-FS06", "J-FS08", "J-FS15", "J-BL05", "ICD-14",
             "J-FD09", "J-PCLIP", "torch port", "sensor ports"}
R2_JOINTS = {"J-PD01", "J-PD02", "J-HV69", "J-RAIL", "J-CARR", "J-PD03", "J-PD05", "J-PD10"}
R4_LINES = {"HW-114"}


def ev(mname, key, T):
    return float(engmat.prop(mname, key, T))


def main():
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=False, overrides=dict(config.V351_ON))
    inst = build.posed_instances(reg, S, 0.0, 0.0)
    wet = [(pn, shp) for (pn, i, grp, shp, body) in inst if getattr(reg.parts[pn], "wetted", "") == "N2O"]
    # hole positions (posed, neutral) per joint
    res = {"id": "ti_screws_v352", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "cad": "v3.5.1 config.V351_ON (neutral pose)",
           "rules": __doc__.split("Rules")[1].split("Strength")[0].strip(), "D_R3_mm_ASSUMED": D_R3, "lines": []}
    pos = {}
    for jn, (hosts, kind, dsel, *_r) in JOINT.items():
        hosts = hosts if isinstance(hosts, tuple) else (hosts,)
        pts = []
        for h in hosts:
            p = reg.parts[h]
            for (T, g) in p.placements:
                grp = build.group_of(g)
                Tp = build.group_T(grp if grp != "lock" else "fixed", 0.0, 0.0) @ T
                for hole in HOLES.get(h, []):
                    if hole["kind"] != kind:
                        continue
                    if dsel is not None and abs(hole["dir"][dsel]) < 0.9:
                        continue
                    tm = 0.5 * (hole["t_range"][0] + hole["t_range"][1])
                    x = np.array(hole["axis_pt"]) + tm * np.array(hole["dir"])
                    xp = (Tp @ np.r_[x, 1.0])[:3]
                    pts.append([round(float(v), 2) for v in xp])
        dmin, near = 1e9, None
        for xp in pts:
            v = cq.Vertex.makeVertex(*xp)
            for (wpn, shp) in wet:
                dd = v.distance(shp)
                if dd < dmin:
                    dmin, near = dd, wpn
        pos[jn] = {"n_points": len(pts), "points_mm": pts, "d_min_to_N2O_mm": round(dmin, 1) if pts else None, "nearest_N2O_part": near}
        print(jn, pos[jn]["n_points"], pos[jn]["d_min_to_N2O_mm"], near, flush=True)
    E_ti = ev("TI6AL4V", "E", 20.0) / 1e6
    a_ti = ev("TI6AL4V", "alpha", 20.0)
    tot = {"steel_g": 0.0, "ti_g": 0.0}
    for L in HW["lines"]:
        if L["kind"] != "screw":
            continue
        lid = L["id"]
        jn = LINE2JOINT.get(lid, L["joint"])
        m_st = (L.get("unit_mass_g") or 0.0) * L["qty"]
        grade = L.get("grade", "")
        row = {"id": lid, "joint": jn, "joint_text_v351": L["joint"], "item": L["item"], "size": L["size"], "length_mm": L.get("length_mm"), "grade_v351": grade, "qty": L["qty"],
               "mass_v351_g": round(m_st, 2)}
        why = []
        if jn in R1_JOINTS or jn.startswith("J-FD") or jn.startswith("J-BL") or jn.startswith("J-FS") or jn in ("J-FWD", "J-BON"):
            why.append("R1 joint clamps / is threaded into an N2O-wetted part or seal")
        if jn in R2_JOINTS or (jn == "J-PD01"):
            why.append("R2 head-top zone (bonnet rod seal, inlet, bleed tap, transducer ports vent there)")
        if lid in R4_LINES:
            why.append(f"R4 strength: {grade} Rp0.2 >= {FTY.get(grade, 0):.0f} MPa > Ti-6Al-4V 827 MPa")
        if jn in pos and pos[jn]["d_min_to_N2O_mm"] is not None:
            row["d_min_to_N2O_mm"] = pos[jn]["d_min_to_N2O_mm"]
            row["nearest_N2O_part"] = pos[jn]["nearest_N2O_part"]
            if pos[jn]["d_min_to_N2O_mm"] < D_R3[0]:
                why.append(f"R3 {pos[jn]['d_min_to_N2O_mm']:.1f} mm < {D_R3[0]:.0f} mm from {pos[jn]['nearest_N2O_part']}")
        row["excluded_by"] = why
        row["status_v352"] = "STEEL (excluded)" if why else ("Ti-6Al-4V (ICD agreement required)" if jn.startswith("ICD") else "Ti-6Al-4V")
        if not why and grade in RHO:
            m_ti = m_st * 4430.0 / RHO[grade]
            row["mass_ti_g"] = round(m_ti, 2)
            row["saving_g"] = round(m_st - m_ti, 2)
            tot["steel_g"] += m_st
            tot["ti_g"] += m_ti
            # ---------------- preload over the soak range (keep the v3.5.1 assembly preload: same clamp on the Al parts)
            th = TH[L["size"]]
            host, kind, dsel, cmat, Lk, Le, zone = JOINT[jn]
            Fi = 0.65 * FTY[grade] * th["As"]                                   # N, v3.5.1 preload (hardware_v351 rule, K 0.2 ASSUMED)
            E_c = ev(cmat, "E", 20.0) / 1e6
            a_c = ev(cmat, "alpha", 20.0)
            d, dw, dh = th["d"], th["dw"], th["dh"]
            Ad = math.pi / 4 * d ** 2
            res_b = {}
            for bname, Eb, ab in (("Ti-6Al-4V", E_ti, a_ti), (grade, 193000.0 if grade.startswith("A") else 205000.0, 16.0e-6 if grade.startswith("A") else 11.5e-6)):
                dlt_b = (0.4 * d) / (Eb * Ad) + Lk / (Eb * th["As"]) + (0.5 * d) / (Eb * th["As"]) + (0.33 * d) / (E_c * Ad)   # VDI 2230 simplified (mm/N)
                t = Lk
                kc = math.pi * E_c * dh * math.tan(math.radians(30.0)) / math.log(((1.155 * t + dw - dh) * (dw + dh)) / ((1.155 * t + dw + dh) * (dw - dh)))
                dlt_c = 1.0 / kc
                dFdT = (a_c - ab) * Lk / (dlt_b + dlt_c)                         # N/K (positive: preload rises when hot)
                fZ = 7.0e-3                                                        # mm embedding (VDI 2230 Rz<10: thread 3 + head 2.5 + interface 1.5 um, AS RECALLED)
                dFz = fZ / (dlt_b + dlt_c)
                Th, Th_src = T_HOT[zone]
                Fmax = Fi + dFdT * (Th - T_ASM)
                Fmin = Fi - dFz + dFdT * (T_MIN - T_ASM)
                Fty_b = (ev("TI6AL4V", "Fty", Th) / 1e6) if bname == "Ti-6Al-4V" else FTY[grade]
                Fty_c = ev(cmat, "Fty", Th) / 1e6
                Ftu_c = ev(cmat, "Ftu", Th) / 1e6
                p_bear = Fmax / (math.pi / 4 * (dw ** 2 - dh ** 2))
                tau_strip = Fmax / (0.75 * math.pi * d * Le)
                res_b[bname] = {"F_i_N": round(Fi, 0), "dF_dT_N_per_K": round(dFdT, 2), "dF_embed_N": round(dFz, 0),
                                "T_hot_C": Th, "T_hot_basis": Th_src, "T_min_C": T_MIN,
                                "F_max_hot_N": round(Fmax, 0), "F_min_cold_after_embedding_N": round(Fmin, 0), "F_min_over_F_i": round(Fmin / Fi, 3),
                                "screw_stress_hot_over_0p9Fty": round(Fmax / th["As"] / (0.9 * Fty_b), 3),
                                "head_bearing_p_MPa": round(p_bear, 1), "p_over_Fty_Al_hot": round(p_bear / Fty_c, 3),
                                "Al_thread_strip_tau_MPa": round(tau_strip, 1), "tau_over_0p6Ftu_Al_hot": round(tau_strip / (0.6 * Ftu_c), 3)}
            row["preload"] = {"clamped_material": cmat, "grip_L_k_mm": Lk, "engagement_L_e_mm": Le, "zone": zone, "by_screw_material": res_b,
                              "evidence": "DERIVED (VDI 2230 simplified compliances, Shigley 30 deg frustum; standard geometry AS RECALLED; "
                                          "engmat E/alpha/Fty LITERATURE-approx; temperatures per T_hot_basis)"}
        res["lines"].append(row)
    res["positions"] = pos
    res["total"] = {"steel_mass_of_converted_lines_g": round(tot["steel_g"], 2), "ti_mass_g": round(tot["ti_g"], 2),
                    "saving_g": round(tot["steel_g"] - tot["ti_g"], 2),
                    "saving_without_ICD_lines_g": round(sum(r.get("saving_g", 0.0) for r in res["lines"] if not r["joint"].startswith("ICD")), 2)}
    res["strength_basis"] = {"Ti-6Al-4V": {"Rm_min_MPa": 896, "Rp02_min_MPa": 827, "A_min_pct": 10, "hardness_HRC": "30-39",
                             "evidence": "DATASHEET (supplier web pages, accessed 2026-10-13)",
                             "sources": ["https://torqbolt.com/suppliers/titanium-grade-5-screws/ (ASTM F468 alloy Ti 5 / R56400 table)",
                                         "https://www.accu.co.uk/p/46-titanium (Accu Ltd, Grade 5 >= 895 MPa; parts SSCF-M5-10-TI5 etc.)"],
                             "purchase": "certificate of conformance to ASTM F468 R56400 per lot; price TO-QUOTE delivered Soenderborg DK-6400"}}
    res["anti_galling_spec"] = ("Ti-6Al-4V screws anodised AMS 2488 Type 2 (anti-galling / anti-fretting); threads and head bearing face assembled with a "
                                "PFPE-based thread lubricant (oxygen-compatible class, product TO-SELECT with datasheet) so one lubricant serves the whole "
                                "engine; no graphite or MoS2 anti-seize; no helicoil (304) under a Ti screw (Ti/stainless galling) - HW-127/128 stay A4-70; "
                                "torque re-derived from a torque-tension test on 3 samples per size (K of anodised + lubricated Ti TO-VERIFY); "
                                "galvanic couple Ti/Al: Al parts anodised (as drawn), lubricant film, no bare Ti in salt fog storage")
    s = json.dumps(res, indent=1, default=float)
    open(OUT, "w").write(s)
    print("total", res["total"])
    print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])


if __name__ == "__main__":
    main()
