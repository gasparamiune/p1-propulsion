"""Joints and seals of the assembled engine, FE-informed hand calculations (04-fea/structural, v1, 2026-10-13, Mechanical).

Question (founder through the lead): "full FEA of the assembled engine at max thrust ... fasteners and seals"; FMEA FA-1 (lead
2026-10-13): head-end pulse 75.5 bar abs <= 3 ms at an A1 relight: "check the case, both closures, fasteners and seals ... report the
burst margin and any seal unloading"; REV-ELEC-1 (1): LC-TB70 carried with the per-part failure criterion.

The axisymmetric FE (sax.py, S-AX) smears the non-axisymmetric fasteners: the 8 radial M5 screws of the forward closure are a u_z tie
over the screw band, the M63x1.5 aft thread a u_z tie over the engagement, the 4 M4 bonnet bolts a tie over the bolt band.  The joint
loads therefore come from the same pressures and states as the S-AX load cases (sax.combos), with the FE section force as the
cross-check of each end load, and the joint temperatures from the S-AX thermal states (stress classification lines at the joint).
The calculations reuse 03-cad/src/calcs/hand_calcs.py (v2, cited references [R1]-[R6]): closure_bolts, thread_strip, row/ms.

Joints and criteria (per part: load-bearing unless stated; a negative margin is a design change, never a pass):
  J-FWD   forward closure, 8 x M5 ISO 7380 A4-70 radial screws in single shear at the plug/case interface (thread-root area A3), end
          load F = P pi/4 D_seal^2 (D_seal 57.25 bore), unequal sharing x1.15 (ASSUMED, hand_calcs v2): screw shear (0.577 Fty /
          0.6 Ftu), bearing in the 6061 case wall (1.4 Fty / 1.6 Ftu [R4]), shear-out to the tube end, net section, bearing on the plug
          thread.  A4-70 has RT allowables only in engmat (ISO 3506-1): rows above 50 C carry the flag 'A4-70 hot knock-down TO-VERIFY'.
          FE cross-check: |Fz| of the case_mid SCL (mechanical section force, full ring) vs F.
  J-AFT   aft closure M63x1.5 x 14 (6g case / 6H TC-09), stripping of both threads (uniform share; the FE first-thread peak is
          reported from the S-AX nodal table), F = aft closure load from the S-AX unit responses: 2716.0 N/MPa (operating
          distribution) or 2928.2 N/MPa (blocked: P pi r_land^2 + plug), checked against the case_aft_land SCL force.
  J-TC03  seat insert TC-03 (IN718) in the 6061 head: chamber load forward onto the counterbore floor (flange lands 49.4 mm2 between
          the 20.0 flange OD, the 14 mm body and the S03 groove 15.6/19.6), and the manifold load aft on the M14x1 x 10 thread
          (manifold inside the S03 groove OD 19.6, chamber vented: SEG-P / proof).
  J-BON   bonnet TC-04 on the head, 4 x M4 A4-70 at r 16.5 (60/120/240/300 deg): separating load = manifold x (face O-ring S04 area
          inside 14.4 + E1-M transfer face seal S05 inside 13.0 at r 16 / 180 deg, eccentric); required preload = max bolt load with
          no gapping; rigid-flange bolt-group distribution (ASSUMED, no prying credited).
  J-LIP   nozzle stack bearing on the J1 lip seal NZ-04 and the hot layer NZ-03: P pi r_bore^2 over the lip-face annulus (S-AX gives
          the stress field; this line gives the mean bearing for the gasket-stress criterion).
  J-GIM   gimbal pins / 608 bearings and the 16 x M5 airframe screws under the FA-1 thrust spike: S-3D v1.1 LC1 reactions scaled by
          the static spike thrust (500 N x P_pulse / Pc_max, ESTIMATE) and by a DLF bound of 2 (the axial mode of the engine on the
          gimbal is not computed: OPEN); 608 static rating C0 1.37 kN AS RECALLED (SKF catalogue class), TO-VERIFY.
  SEALS   S01/S02 (head plug, AS568-226 FKM 90A) and S13 (aft rod gland, AS568-229 FFKM): extrusion gap = cold diametral clearance max
          + 2 x the FE radial opening at the extrusion flank (sax.py seals) vs the Parker ORD 5700 Fig. 3-2 limit at the case pressure
          (approximate table of hand_calcs [R2]; continuous-pressure guidance, no credit for the <= 3 ms pulse); squeeze loss vs the
          minimum squeeze.  S03 / S14 are pressure-assisted (stated, no number).

Inputs: results/sax_results_<tag>_v1.json (S-AX L1 design and the TC-09 IN718 variant), results/sax_seal_gaps_L1_v1.json,
results/s3d_results_v1.1.json, results/sax_fa1_dlf_v1.json; sax.combos (pressures per case).  Outputs: results/joints_v1.json and
results/joints_table_v1.csv.  Tags: DERIVED (this script) on ASSUMED/LITERATURE inputs as cited; no test.
"""
from __future__ import annotations
import csv, hashlib, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
FEA = HERE.parent
CAD = FEA.parent / "03-cad" / "src"
sys.path.insert(0, str(CAD))
sys.path.insert(0, str(CAD / "calcs"))
sys.path.insert(0, str(FEA / "src"))
sys.path.insert(0, str(HERE))
import hand_calcs as hc  # noqa: E402
from engmat import prop  # noqa: E402

RES = HERE / "results"
PI = math.pi
AL = "AL6061-T6"
A4 = "SS-A4-70"
D_SEAL = 0.05725                 # m, case bore at the head glands (config case_bore_seal)
CASE_OD = 0.0635
T_CASE_WALL = (CASE_OD - D_SEAL) / 2
E_EDGE = 0.012                   # m, screw row to tube end (config bolt_edge_chamber)
LE_PLUG = 0.006                  # m, M5 engagement in the 6061 plug (tapped 6.5 deep, parts_engine)
K_AFT = {"OP": 2716.0, "BL": 2928.2}   # N/MPa, aft closure load per unit chamber pressure (S-AX unit responses, rev B run 2)
A_TC03_FWD = 290.4               # mm2, TC-03 area loaded forward by the chamber (S-AX unit response, N/MPa)
A_TC03_LANDS = PI / 4 * (20.0 ** 2 - 14.0 ** 2) - PI / 4 * (19.6 ** 2 - 15.6 ** 2)   # mm2 flange lands outside the S03 groove
A_TC03_AFT = PI / 4 * 19.6 ** 2  # mm2, manifold pressure inside the S03 groove OD (chamber vented)
A_END_FACE = PI / 4 * (61.0 ** 2 - 57.15 ** 2)   # mm2, case aft end face inside the S13 seal (pressurised, pushes the case aft)
A_S04 = PI / 4 * 14.4 ** 2       # mm2, bonnet face O-ring groove OD (parts_engine tube(14.4, 12.0))
A_S05 = PI / 4 * 13.0 ** 2       # mm2, E1-M transfer groove OD 13.0 (tc04_fits '9.4/13.0 x 1.30 at r 16')
BON_R, BON_ANG = 16.5, (60.0, 120.0, 240.0, 300.0)
S05_XY = (16.0 * math.cos(math.radians(180.0)), 16.0 * math.sin(math.radians(180.0)))
C0_608_N = 1370.0                # N, 608 static load rating AS RECALLED (SKF 608 class), TO-VERIFY
THRUST_MAX_N, PC_MAX_BAR = 500.0, 25.01
TAG_IN = "L1_TC09IN718_thJ1revB_TC09IN"   # v1.1: TC-09 IN718 on its own thermal history (A1 + B1 TC09IN runs)
FA_CASES = ("FA1", "FA1S", "FA1Q", "FA1QB", "FA1D", "FA1DB", "FA1U", "FA1UB")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load_results(tag):
    p = RES / f"sax_results_{tag}_v1.json"
    d = json.loads(p.read_text())
    scl = {(r["case"], r["state"], r["scl"]): r for r in d["scl_all"]}
    parts = {}
    for r in d["rows"]:
        k = (r["case"], r["state"], r["part"])
        if r["set"] == "regular":
            parts[k] = r
    return d, scl, parts, sha16(p)


def combos_table():
    import sax
    faces, info = sax.geometry()
    C = sax.combos(info)
    return {c[0]: {"title": c[1], "states": c[2], "coef": c[3], "SF_y": c[4], "SF_u": c[5], "crit": c[6]} for c in C}


def t_at(scl, case, state, name, default=20.0):
    r = scl.get((case, state, name))
    return float(r["T_max_C"]) if r else default


def worst(rows):
    vals = [(x["MS_y"] if x["MS_y"] is not None else 1e9, x["MS_u"] if x["MS_u"] is not None else 1e9) for x in rows]
    return min(min(a, b) for a, b in vals)


def clean(rows, sfu):
    for x in rows:
        if sfu is None:
            x["MS_u"], x["SF_u"] = None, None
        for k in ("applied", "allow_yield", "allow_ult", "MS_y", "MS_u"):
            if isinstance(x.get(k), float):
                x[k] = round(x[k], 4)
    return rows


def fwd_closure(P_MPa, T_C, sfy, sfu, label, n=8, d=0.005, share=1.15):
    r = hc.closure_bolts(P_MPa * 1e6, D_SEAL, n, d, A4, T_CASE_WALL, CASE_OD, AL, AL, max(E_EDGE, 2.4 * d), LE_PLUG, T_C, sfy,
                         sfu if sfu else 1.0, label, share=share)
    for x in r["rows"]:
        if "screw shear" in x["check"] and T_C > 50.0:
            x["note"] += "; A4-70 allowables at RT (ISO 3506-1), hot knock-down at %.0f C TO-VERIFY" % T_C
    return r


def shoulder_option(P_MPa, sfy, sfu, n=8, d_shank=0.006, share=1.15):
    """ISO 7379-type shoulder screw with the shank in the shear plane (plug counterbored for the shoulder): shear on the shank."""
    F = P_MPa * 1e6 * PI / 4 * D_SEAL ** 2
    V = F / n * share
    A = PI / 4 * d_shank ** 2
    return [hc.row(f"{n} x shoulder screw, shank {d_shank*1e3:.0f} mm in the shear plane (A4-70 class ASSUMED): shank shear", V / A,
                   0.577 * prop(A4, "Fty"), 0.6 * prop(A4, "Ftu"), sfy, sfu if sfu else 1.0, note=f"V/screw {V:.0f} N"),
            hc.row(f"{n} x shoulder screw: bearing of the {d_shank*1e3:.0f} mm shank in the case wall", V / (d_shank * T_CASE_WALL),
                   1.4 * prop(AL, "Fty", 47.0), 1.6 * prop(AL, "Ftu", 47.0), sfy, sfu if sfu else 1.0, note="6061 at 47 C (A1 relight state)")]


def aft_thread(F_N, T_C, mat_int, sfy, sfu, label):
    r = hc.thread_strip(F_N, 0.063, 0.0015, 0.014, AL, mat_int, T_C, sfy, sfu if sfu else 1.0, label, Td2=0.132e-3, TD2=0.174e-3, TD1=0.300e-3)
    return r


def m14_thread(F_N, T_C, sfy, sfu, label):
    # ISO 965-1 M14x1 6g/6H: es -26 um, Td2 112 um, TD2 150 um, TD1 236 um (AS RECALLED, TO-VERIFY); TC-02 callout M14x1-6H x 10
    r = hc.thread_strip(F_N, 0.014, 0.001, 0.010, "IN718", AL, T_C, sfy, sfu if sfu else 1.0, label, Td2=0.112e-3, TD2=0.150e-3, TD1=0.236e-3)
    for x in r["rows"]:
        x["check"] = x["check"].replace("external thread (case)", "external thread (TC-03 IN718)").replace("internal thread (closure)", "internal thread (TC-02 6061)")
    return r


def bonnet_bolts(PM_MPa, T_C, label, phi=0.2, pre_frac=0.65):
    """Max external tensile load per M4 bolt (rigid flange, bolt-group moment about the centroid) and the preload check."""
    F_c, F_t = PM_MPa * A_S04, PM_MPa * A_S05
    xy = [(BON_R * math.cos(math.radians(a)), BON_R * math.sin(math.radians(a))) for a in BON_ANG]
    Ix = sum(x * x for x, _ in xy)
    Iy = sum(y * y for _, y in xy)
    loads = [F_c / 4 + F_t / 4 + F_t * S05_XY[0] * x / Ix + F_t * S05_XY[1] * y / Iy for x, y in xy]
    Fmax = max(loads)
    As = 8.78                                            # mm2, M4 stress area (ISO 898-1 table)
    Fpre = pre_frac * prop(A4, "Fty") / 1e6 * As         # N, preload at 65 % of Rp0.2 (ASSUMED assembly target)
    sb = (Fpre + phi * Fmax) / As
    return {"label": label, "PM_MPa": PM_MPa, "F_center_N": round(F_c, 1), "F_transfer_N": round(F_t, 1),
            "bolt_loads_N": [round(v, 1) for v in loads], "F_bolt_max_ext_N": round(Fmax, 1),
            "preload_target_N": round(Fpre, 0), "preload_note": "65 % of A4-70 Rp0.2 x As 8.78 mm2 (ASSUMED target); torque ~0.2 x F x d "
                                                               f"= {0.2 * Fpre * 0.004:.2f} N m (K 0.2 ASSUMED, lubricated stainless lower: TO-VERIFY)",
            "MS_no_gapping": round(Fpre / Fmax - 1.0, 3) if Fmax > 0 else None,
            "bolt_stress_MPa": round(sb, 1), "MS_bolt_y": round(prop(A4, "Fty") / 1e6 / sb - 1.0, 3),
            "joint_factor_phi": phi, "T_C": round(T_C, 1),
            "strip_6061": hc.row(f"{label}: M4 in 6061 head, stripping (Le 6 mm ASSUMED of the 10 mm tapped depth)",
                                 (Fpre + phi * Fmax) / (PI * 4.0e-3 * 6.0e-3 * 0.75) * 1.0, 0.577 * prop(AL, "Fty", T_C),
                                 0.6 * prop(AL, "Ftu", T_C), 1.0, 1.0, note="A_strip ~ 0.75 pi d Le (internal thread, approx [R3])")}


def extrusion_limit(P_MPa, duro):
    table = {75: [(3.5, 0.25), (7.0, 0.15), (10.5, 0.10), (14.0, 0.07)], 90: [(3.5, 0.35), (7.0, 0.25), (10.5, 0.18), (14.0, 0.13)]}[duro]
    p, g = [a for a, _ in table], [b for _, b in table]
    if P_MPa <= p[-1]:
        return float(np.interp(P_MPa, p, g)), "Parker ORD 5700 Fig. 3-2 approx (hand_calcs [R2])"
    # beyond the table: log-linear extension of the last segment (no credit beyond the chart: flagged)
    k = math.log(g[-1] / g[-2]) / (p[-1] - p[-2])
    return g[-1] * math.exp(k * (P_MPa - p[-1])), "EXTRAPOLATED beyond the Parker chart (14 MPa): no data, guideline only"


def main():
    C = combos_table()
    dD, sclD, partsD, shaD = load_results("L1")
    dI, sclI, partsI, shaI = load_results(TAG_IN)
    gaps_p = RES / "sax_seal_gaps_L1_v1.json"
    gaps = json.loads(gaps_p.read_text())
    s3d_p = RES / "s3d_results_v1.1.json"
    s3d = json.loads(s3d_p.read_text())
    dlf = json.loads((RES / "sax_fa1_dlf_v1.json").read_text())
    out = {"id": "joints", "version": "v1.1", "date": "2026-10-13", "owner": "mechanical", "script": "04-fea/structural/joints.py",
           "status": "DERIVED hand calculations on S-AX loads/temperatures (SIM) and ASSUMED/LITERATURE allowables; no test",
           "inputs": {"sax_results_L1_v1.json": shaD, f"sax_results_{TAG_IN}_v1.json": shaI, "sax_seal_gaps_L1_v1.json": sha16(gaps_p),
                      "s3d_results_v1.1.json": sha16(s3d_p), "hand_calcs.py": sha16(CAD / "calcs" / "hand_calcs.py")},
           "method": __doc__.split("\n\n")[2] if len(__doc__.split("\n\n")) > 2 else "", "joints": {}}
    table = []

    def add(joint, case, state, rows, extra=None):
        for x in rows:
            table.append([joint, case, state, x["check"], x["applied"], x.get("allow_yield"), x.get("allow_ult"), x.get("SF_y"), x.get("SF_u"),
                          x.get("MS_y"), x.get("MS_u"), x.get("note", "")])

    # ------------------------------------------------------------------------------------------------ J-FWD
    fwd = {}
    for cid, c in C.items():
        P = c["coef"].get("OP", c["coef"].get("BL"))
        if not P:
            continue
        best = None
        for st in c["states"]:
            Tw = max(t_at(sclD, cid, st, "case_screw_row"), t_at(sclD, cid, st, "head_r26_gland_land"))
            r = fwd_closure(P, Tw, c["SF_y"], c["SF_u"], f"J-FWD 8xM5 A4-70 [{cid} {st} P {P*10:.1f} bar, T {Tw:.0f} C]")
            rows = clean(r["rows"], c["SF_u"])
            fe = sclD.get((cid, st, "case_fwd_gland"))          # case wall between the screw row and the collar carries F_end
            F_fe = abs(fe["Fz_section_N_mech"]) if fe else None
            w = worst(rows)
            if best is None or w < best["min_MS"]:
                best = {"state": st, "P_MPa": P, "T_joint_C": round(Tw, 1), "F_end_N": round(r["F_end_N"], 1),
                        "F_end_FE_case_fwd_gland_N": round(F_fe, 1) if F_fe else None,
                        "FE_over_hand": round(F_fe / r["F_end_N"], 4) if F_fe else None,
                        "V_per_screw_N": round(r["V_per_screw_N"], 1), "rows": rows, "min_MS": round(w, 4), "criterion": c["crit"]}
        fwd[cid] = best
        add("J-FWD", cid, best["state"], best["rows"])
    # design-change options at FA1 / FA1S (A1 relight state, 47 C)
    opts = {}
    for cid in FA_CASES:
        c = C[cid]
        P = c["coef"].get("OP", c["coef"].get("BL"))
        st = c["states"][0]
        Tw = max(t_at(sclD, cid, st, "case_screw_row"), t_at(sclD, cid, st, "head_r26_gland_land"))
        o = {}
        for (n, d) in ((12, 0.005), (8, 0.006), (12, 0.006), (16, 0.005)):
            r = fwd_closure(P, Tw, c["SF_y"], c["SF_u"], f"option {n}xM{d*1e3:.0f} A4-70 [{cid}]", n=n, d=d)
            rows = clean(r["rows"], c["SF_u"])
            o[f"{n}xM{d*1e3:.0f}"] = {"min_MS": round(worst(rows), 4), "rows": rows}
        rows = clean(shoulder_option(P, c["SF_y"], c["SF_u"]), c["SF_u"])
        o["8x shoulder 6/M5"] = {"min_MS": round(worst(rows), 4), "rows": rows}
        opts[cid] = o
    out["joints"]["J-FWD"] = {"description": "forward closure 8 x M5 ISO 7380 A4-70 radial screws (single shear, thread root in the shear plane)",
                              "role": "LOAD-BEARING (retention of the forward closure)", "governing_per_case": fwd,
                              "options_FA1": opts,
                              "note": "screw shear at the thread root uses A3 = pi/4 d3^2 (12.68 mm2 for M5); x1.15 unequal sharing ASSUMED"}

    # ------------------------------------------------------------------------------------------------ J-AFT
    aft = {}
    for variant, scl, mat in (("TC09_316L", sclD, "SS316L"), ("TC09_IN718", sclI, "IN718")):
        aft[variant] = {}
        for cid, c in C.items():
            if "OP" in c["coef"]:
                P, k = c["coef"]["OP"], K_AFT["OP"]
            elif "BL" in c["coef"]:
                P, k = c["coef"]["BL"], K_AFT["BL"]
            else:
                continue
            best = None
            for st in c["states"]:
                Tt = max(t_at(scl, cid, st, "case_thread"), t_at(scl, cid, st, "tc09_socket"))
                F = k * P
                r = aft_thread(F, Tt, mat, c["SF_y"], c["SF_u"], f"J-AFT M63x1.5x14 ({mat}) [{cid} {st} P {P*10:.1f} bar, T {Tt:.0f} C]")
                rows = clean(r["rows"], c["SF_u"])
                fe = scl.get((cid, st, "case_mid"))                # aft of the collar: aft closure load minus the case end-face load
                w = worst(rows)
                if best is None or w < best["min_MS"]:
                    best = {"state": st, "P_MPa": P, "T_thread_C": round(Tt, 1), "F_N": round(F, 1),
                            "F_FE_case_mid_plus_end_face_N": round(abs(fe["Fz_section_N_mech"]) + P * A_END_FACE, 1) if fe else None,
                            "A_s_mm2": round(r["A_s_m2"] * 1e6, 1), "A_n_mm2": round(r["A_n_m2"] * 1e6, 1), "rows": rows, "min_MS": round(w, 4)}
            aft[variant][cid] = best
            add(f"J-AFT-{variant}", cid, best["state"], best["rows"])
    # FE first-thread peak (S-AX nodal, regular set) for the governing FA cases
    peak = {}
    for cid in FA_CASES + ("TB70", "TBS", "LC4"):
        for (cc, st, pn), r in partsD.items():
            if cc == cid and pn == "ENG-TC-01":
                peak[cid] = {"state": st, "MS_regular": round(r["MS"], 4), "at_r_z_mm": r["at_r_z_mm"], "T_C": round(r["T_C"], 1),
                             "vm_MPa": round(r["vm_MPa"], 1), "note": "S-AX L1 regular-set peak of TC-01 (location decides whether it is the first engaged thread)"}
    out["joints"]["J-AFT"] = {"description": "aft closure M63x1.5 x 14, 6061 case (6g) in the TC-09 socket (6H)", "role": "LOAD-BEARING",
                              "governing_per_case": aft, "FE_peak_TC01": peak,
                              "note": "uniform load share over 14 mm (hand_calcs [R3]); the first-thread peak is a local (P+Q) quantity: S-AX "
                                      "convergence shows the FA1S TC-01 regular peak at the thread top converging slowly (MS 0.213/0.137/0.078 "
                                      "on L2/L1/L0.5)"}

    # ------------------------------------------------------------------------------------------------ J-TC03
    tc = {}
    for cid, c in C.items():
        P = c["coef"].get("OP", c["coef"].get("BL"))
        PMv = c["coef"].get("PM", 0.0)
        st_rows = []
        for st in c["states"]:
            r_head = partsD.get((cid, st, "ENG-TC-02"))
            Th = float(r_head["T_part_max_C"]) if r_head else 20.0
            rows = []
            if P:
                F = A_TC03_FWD * P
                rows.append(hc.row(f"J-TC03 flange bearing on the 6061 counterbore floor, lands {A_TC03_LANDS:.1f} mm2 [{cid} {st}, T_head_max {Th:.0f} C]",
                                   F / A_TC03_LANDS * 1e6, 1.4 * prop(AL, "Fty", Th), 1.6 * prop(AL, "Ftu", Th), c["SF_y"], c["SF_u"] or 1.0,
                                   note=f"chamber only, manifold relief not credited: F {F:.0f} N"))
            if PMv:
                F2 = A_TC03_AFT * PMv
                rr = m14_thread(F2, Th, c["SF_y"], c["SF_u"], f"J-TC03 M14x1 x 10 thread, manifold {PMv*10:.1f} bar, chamber vented [{cid} {st}]")
                rows += rr["rows"]
            rows = clean(rows, c["SF_u"])
            if rows:
                st_rows.append((worst(rows), st, rows))
        if st_rows:
            w, st, rows = min(st_rows, key=lambda q: q[0])
            tc[cid] = {"state": st, "rows": rows, "min_MS": round(w, 4)}
            add("J-TC03", cid, st, rows)
    out["joints"]["J-TC03"] = {"description": "TC-03 IN718 seat insert in the 6061 head (flange seat + M14x1)", "role": "LOAD-BEARING",
                               "governing_per_case": tc, "lands_mm2": round(A_TC03_LANDS, 1), "A_manifold_aft_mm2": round(A_TC03_AFT, 1),
                               "note": "head temperature = TC-02 part maximum at the state (conservative for the flange seat at the injector face)"}

    # ------------------------------------------------------------------------------------------------ J-BON
    bon = {}
    for cid, c in C.items():
        PMv = c["coef"].get("PM")
        if not PMv:
            continue
        st = c["states"][0]
        r_head = partsD.get((cid, st, "ENG-TC-04"))
        Tb = float(r_head["T_part_max_C"]) if r_head else 20.0
        bon[cid] = bonnet_bolts(PMv, Tb, f"J-BON 4xM4 A4-70 [{cid}]")
        x = bon[cid]["strip_6061"]
        clean([x], 1.0)
        add("J-BON", cid, st, [x])
        table.append(["J-BON", cid, st, f"no-gapping preload {bon[cid]['preload_target_N']:.0f} N vs max bolt load {bon[cid]['F_bolt_max_ext_N']:.0f} N",
                      bon[cid]["F_bolt_max_ext_N"], bon[cid]["preload_target_N"], None, 1.0, None, bon[cid]["MS_no_gapping"], None,
                      "rigid flange bolt group (ASSUMED), E1-M transfer seal eccentric at r 16 / 180 deg"])
    out["joints"]["J-BON"] = {"description": "bonnet TC-04 on the head: 4 x M4 A4-70 at r 16.5", "role": "LOAD-BEARING + SEAL (S04, S05)",
                              "per_case": bon}

    # ------------------------------------------------------------------------------------------------ J-LIP
    lip = {}
    r_bore, r_sp = 22.0 + 3.0 - 0.025, None
    for cid, c in C.items():
        P = c["coef"].get("OP", c["coef"].get("BL"))
        if not P:
            continue
        # mean bearing of the stack on the lip seal: 10.6 MPa at BN 63.1 bar (Combustion nozzle_joint_v2p4) scales with P
        q = 10.6 * (P * 10.0) / 63.1
        lip[cid] = {"P_MPa": P, "mean_bearing_MPa": round(q, 2),
                    "MS_NZ04_vs_Sc150_ASSUMED": round(150.0 / q - 1.0, 2),
                    "note": "scaled from Combustion's 10.6 MPa at BN 63.1 bar (P pi r_bore^2 / lip annulus); the S-AX NZ-03/NZ-04 rows hold the field"}
    out["joints"]["J-LIP"] = {"description": "nozzle stack bearing on the J1 lip seal NZ-04 (and hot layer NZ-03)", "role": "SEAL (bearing) / LOAD-BEARING",
                              "per_case": lip, "pressure_assisted": "the insert load grows with chamber pressure: the lip seal is pressure-energised "
                                                                       "(no unloading under FA-1); S-AX NZ-04 MS 4.78 at FA1S (regular set, L1)"}

    # ------------------------------------------------------------------------------------------------ J-GIM
    lc1 = s3d["poses"]["centre"]["cases"]["LC1"]
    pin250 = max(v["radial_N"] for v in lc1["pin_bearing_max_N"].values())
    scr92 = lc1["airframe_screws"]["shear_max_N"]
    s3d_max_pin = max(max(v["radial_N"] for v in cc["pin_bearing_max_N"].values()) for p in s3d["poses"].values() for cc in p["cases"].values())
    s3d_max_scr = max(cc["airframe_screws"]["shear_max_N"] for p in s3d["poses"].values() for cc in p["cases"].values())
    spike = THRUST_MAX_N * FA1_P() / PC_MAX_BAR
    gim = {"thrust_spike_static_N": round(spike, 0), "basis": "500 N x 75.52 / 25.01 bar (thrust ~ Pc at fixed Cf, ESTIMATE)",
           "pin_radial_LC1_N": pin250, "airframe_screw_shear_LC1_N": scr92}
    for lab, f in (("static", 1.0), ("FA1_DLF", float(dlf["DLF_governing"])), ("bound_DLF2", 2.0)):
        s = spike * f / THRUST_MAX_N
        gim[lab] = {"factor_on_LC1": round(s, 3), "pin_radial_N": round(pin250 * s, 0), "MS_608_C0": round(C0_608_N / (pin250 * s) - 1.0, 3),
                    "airframe_screw_shear_N": round(scr92 * s, 0), "vs_S3D_design_max_screw_N": s3d_max_scr,
                    "vs_S3D_design_max_pin_N": s3d_max_pin}
    gim["note"] = ("DLF of the axial engine-on-gimbal mode is NOT computed (the V5c gimbal stiffness summary has no axial term): the FA1 "
                   "DLF (pressure-part modes >= 2.1 kHz) does not apply to it; the bound 2.0 covers any mode.  608 C0 1.37 kN AS RECALLED, TO-VERIFY "
                   "(static overload = brinelling, not fracture: inspect / replace the bearings after a FA-1 event)")
    out["joints"]["J-GIM"] = gim
    table.append(["J-GIM", "FA1S", "A1_22.2", "608 bearing radial (DLF 2 bound) vs C0 1.37 kN AS RECALLED", gim["bound_DLF2"]["pin_radial_N"],
                  C0_608_N, None, 1.0, None, gim["bound_DLF2"]["MS_608_C0"], None, "ESTIMATE: LC1 reactions x spike / 500 N x 2"])
    table.append(["J-GIM", "FA1", "A1_22.2", "608 bearing radial (FA1 DLF) vs C0", gim["FA1_DLF"]["pin_radial_N"], C0_608_N, None, 1.0, None,
                  gim["FA1_DLF"]["MS_608_C0"], None, "ESTIMATE"])

    # ------------------------------------------------------------------------------------------------ FA-1 INTERIM spike (lead 172 (2))
    out["fa1_interim_spike"] = fa1q_spike(s3d, table)
    out["fa1_periods"] = fa1_periods(dlf)
    # ------------------------------------------------------------------------------------------------ SEALS
    seals = {}
    geo = {"S01": {"ring": "AS568-226 FKM 90A", "duro": 90, "cold_gap_max_mm": 57.296 - 57.140, "min_squeeze_mm": 0.57,
                   "note": "bore 57.25 +0.046 (H8), plug 57.20 -0.030/-0.060 (f7): diametral 0.156 max cold"},
           "S02": {"ring": "AS568-226 FKM 90A (back-up gland)", "duro": 90, "cold_gap_max_mm": 0.156, "min_squeeze_mm": 0.57, "note": "as S01"},
           "S13": {"ring": "AS568-229 FFKM (Kalrez 7075 class, ~75 Sh A AS RECALLED)", "duro": 75, "cold_gap_max_mm": 0.106, "min_squeeze_mm": None,
                   "note": "TC-09 bore 61.0 +0.046 (H8) on the case land 61.0 -0.030/-0.060 (f7): diametral 0.106 max cold"}}
    for grow in gaps["rows"]:
        case, state = grow["case"], grow["state"]
        c = C.get(case)
        P = c["coef"].get("OP", c["coef"].get("BL")) if c else None
        for sid in ("S01", "S02", "S13"):
            g = grow["seals"].get(sid)
            if not g:
                continue
            opening = g["opening_at_flank_mm"]
            gm = geo[sid]
            gap = gm["cold_gap_max_mm"] + 2.0 * max(opening, 0.0)
            lim, src = extrusion_limit(P, gm["duro"]) if P else (None, "")
            ent = {"state": state, "P_MPa": P, "radial_opening_flank_mm": round(opening, 4), "radial_opening_mean_mm": round(g["opening_mean_mm"], 4),
                   "radial_opening_max_mm": round(g["opening_max_mm"], 4),
                   "extrusion_gap_mm": round(gap, 4), "limit_mm": round(lim, 4) if lim else None, "limit_src": src,
                   "MS_extrusion": round(lim / gap - 1.0, 3) if lim else None,
                   "squeeze_loss_pct_of_min": (round(100.0 * max(g["opening_max_mm"], 0.0) / gm["min_squeeze_mm"], 1)
                                               if gm["min_squeeze_mm"] else None),
                   "pressure_tightened_at_flank": bool(opening < 0)}
            seals.setdefault(sid, {"ring": gm["ring"], "note": gm["note"], "cases": {}})["cases"][f"{case}@{state}"] = ent
            table.append(["SEAL", case, state, f"{sid} extrusion gap {gap:.3f} mm (cold {gm['cold_gap_max_mm']:.3f} + 2 x FE flank opening) vs limit",
                          gap, lim, None, 1.0, None, ent["MS_extrusion"], None, src])
    out["seals"] = seals
    out["seals_qualitative"] = {"S03": "TC-03 flange O-ring AS568-016 FFKM: the chamber pushes the TC-03 flange onto its seat (J-TC03): "
                                       "pressure-assisted, no unloading under FA-1",
                                "S14": "J1 lip-face seal NZ-04: the insert load grows with chamber pressure (pressure-energised); bearing "
                                       "scales to ~25 MPa at FA1S vs 150 MPa max gasket stress ASSUMED"}
    (RES / "joints_v1p1.json").write_text(json.dumps(out, indent=1, default=float))
    with open(RES / "joints_table_v1p1.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# joints.py v1.1 (2026-10-13, Mechanical; v1.1 adds the FA-1 INTERIM cases FA1Q/FA1QB and the 1.8 kN / 4 ms spike block): FE-informed joint and seal checks; MS = allowable/(SF x applied) - 1; DERIVED"])
        w.writerow(["joint", "case", "state", "check", "applied", "allow_yield", "allow_ult", "SF_y", "SF_u", "MS_y", "MS_u", "note"])
        w.writerows(table)
    # console summary
    for cid in ("LC1", "LC2", "BN", "LC4", "TB70", "TBS") + FA_CASES:
        if cid in fwd:
            print(f"J-FWD {cid:5s} {fwd[cid]['state']:9s} T {fwd[cid]['T_joint_C']:6.1f} min MS {fwd[cid]['min_MS']:+.3f}  FE/hand {fwd[cid]['FE_over_hand']}")
    for cid in FA_CASES:
        print(cid, {k: v["min_MS"] for k, v in opts[cid].items()})
    for v in aft:
        print("J-AFT", v, {k: aft[v][k]["min_MS"] for k in aft[v]})
    print("J-TC03", {k: v["min_MS"] for k, v in tc.items()})
    print("J-BON", {k: (v["F_bolt_max_ext_N"], v["MS_no_gapping"], v["MS_bolt_y"]) for k, v in bon.items()})
    print("J-GIM", json.dumps({k: gim[k] for k in ("static", "FA1_DLF", "bound_DLF2")}))
    print("SEALS", json.dumps({s: {c: (e["extrusion_gap_mm"], e["limit_mm"], e["MS_extrusion"]) for c, e in v["cases"].items()} for s, v in seals.items()}))


def fa1_periods(dlf):
    """Natural periods of the closures, closure fasteners and the J1 lip (S-AX axisymmetric modal, 20 C, internals absent: model
    frequency = UPPER bound; the band goes down to f / sqrt(mass factor 2)) and the FA-1 load each one takes (lead CHANGELOG 173)."""
    modes = {m["mode"]: m for m in dlf["modes"]}
    mf = math.sqrt(float(dlf.get("mass_factor_ASSUMED", 2.0)))
    def band(k):
        f = modes[k]["f_Hz"]
        return [round(1e3 / f, 3), round(1e3 * mf / f, 3)]
    rows = {
        "ENG-TC-02 forward closure (head) on its 8 screws": (2, "J-FWD screws, TC-02, S01/S02"),
        "8 x closure screws (axial mode of the head on the screw band)": (2, "J-FWD"),
        "ENG-TC-09 aft closure on the M63 thread + J1 lip + nozzle stack": (1, "J-AFT, TC-09, J1 lip, NZ-01..04, S13/S14"),
        "ENG-TC-01 case shell (breathing)": (6, "TC-01"),
        "ENG-TC-04 bonnet on 4 x M4": (9, "J-BON, TC-04"),
    }
    out = {"source": "results/sax_fa1_dlf_v1.json (sax.py modal, axisymmetric n = 0)", "rule": "lead CHANGELOG 173: 90 bar abs quasi-static for "
           "every part; parts with T 0.25-1 ms also at 92 bar (design) and 102 bar (sensitivity); T <= 0.1 ms: DLF <= 1.007 (Combustion)", "rows": []}
    for name, (k, applies) in rows.items():
        T = band(k)
        in_band = T[1] >= 0.25 and T[0] <= 1.0
        cases = "FA1Q 90 + FA1D 92 + FA1U 102 (and the blocked bounds FA1QB/FA1DB/FA1UB)" if in_band else (
            "FA1Q 90 (quasi-static)" if T[1] <= 0.1 else "FA1Q 90; T between 0.1 and 0.25 ms: FA1D 92 reported as well (conservative)")
        out["rows"].append({"item": name, "mode": k, "f_model_Hz": modes[k]["f_Hz"], "dominant_part": modes[k]["dominant_part"],
                            "T_ms_band": T, "in_0.25_1ms": in_band, "load_cases": cases, "checks": applies})
    return out


# ================================================================================ FA-1 INTERIM: 1.8 kN / 4 ms thrust spike (v1.1)
SPIKE = {"F_N": 1800.0, "td_s": 0.004, "T_band_s": [0.001, 0.005], "P_bar": 90.0,
         "src": "lead CHANGELOG line 172 (2) / coordinator 2026-10-13: thrust spike 1.8 kN for 4 ms on the parts with periods of 1-5 ms "
                "(gimbal, thrust mount, pintle linkage), by DLF or impulse; 1.8 kN = 500 N x 90 / 25 bar"}
MISALIGN_ARM_M = 0.0005 + math.sin(math.radians(0.25)) * 0.2330      # config misalign_offset + misalign_deg x pivot-exit arm (ASSUMED tolerances)
SIDE_LOAD_FLOOR_NM = 1.291                                             # mechanical.json v2 hinge term at 500 N (DERIVED from gnc.json v1)
TVC_RATING_NM = {"lead_35.3": 35.3, "as_built_design_37.95": 37.95}
PINTLE = {"seat_d_mm": 5.5, "stem_d_mm": 3.0, "jam_design_link_N": 831.6, "jam_failure_link_N": 933.7, "stall_7V4_Nm": 0.90,
          "crank_r_mm": 3.0, "link_L_mm": 28.0, "phi_closed_deg": 15.0, "phi_stop_deg": 113.09,
          "src": "03-cad/src/calcs/pintle_inline_v34_v2p4.json (jam_component_margins: every component MS >= 0 and s0 >= 1.64 at 831.6 N)"}
M5_A3_MM2 = 12.68                                                      # M5 thread-root area (hand_calcs v2)


def _pulse(shape, t, td):
    t1 = 0.001
    if shape == "rect":
        return np.where(t <= td, 1.0, 0.0)
    if shape == "trap_rise1ms":
        return np.clip(np.minimum(t / t1, (td - t) / t1), 0.0, 1.0)
    if shape == "tri_rise1ms":
        return np.clip(np.where(t <= t1, t / t1, (td - t) / (td - t1)), 0.0, 1.0)
    if shape == "halfsine":
        return np.where(t <= td, np.sin(np.pi * np.clip(t, 0, td) / td), 0.0)
    raise ValueError(shape)


def spike_dlf(T, shape, td=SPIKE["td_s"]):
    """Peak |x| / x_static(peak) of x'' + w^2 x = w^2 p(t), undamped, from rest (lsim, piecewise-linear input, dt = T/400)."""
    from scipy import signal
    w = 2.0 * math.pi / T
    dt = min(T, td) / 400.0
    t = np.arange(0.0, td + 3.0 * T, dt)
    p = _pulse(shape, t, td)
    if shape == "rect":
        p[0] = 1.0                                    # step at t = 0 (lsim then ramps over the first dt: DLF -> 2 from below)
    _, x, _ = signal.lsim(signal.lti([w * w], [1.0, 0.0, w * w]), p, t)
    return float(np.max(np.abs(x)))


def fa1q_spike(s3d, table):
    Ts = np.round(np.arange(1.0, 5.0001, 0.25) * 1e-3, 6)
    shapes = ("rect", "trap_rise1ms", "tri_rise1ms", "halfsine")
    dl = {sh: {f"{T * 1e3:.2f}ms": round(spike_dlf(T, sh), 3) for T in Ts} for sh in shapes}
    dmax = {sh: max(v.values()) for sh, v in dl.items()}
    DLF_B = 2.0                                       # step bound (exact for the rectangular pulse with td >= T/2, i.e. T <= 8 ms)
    cases = {"bound_DLF2.0": DLF_B, "trap_rise1ms_max": dmax["trap_rise1ms"],
             "combustion_SDOF_max_3.05kN": 3050.0 / SPIKE["F_N"],   # lead 173 (3): fa1_envelope_v2p4a SDOF equivalent <= 3.05 kN
             "static_DLF1.0": 1.0}
    lc1 = [cc["cases"]["LC1"] for cc in s3d["poses"].values() if "LC1" in cc["cases"]]
    pin = max(max(v["radial_N"] for v in c["pin_bearing_max_N"].values()) for c in lc1)
    scr = max(c["airframe_screws"]["shear_max_N"] for c in lc1)
    gm = {}
    with open(RES / "s3d_margin_table_v1.1.csv") as f:
        rd = csv.reader(f)
        hdr = next(rd)
        for row in rd:
            r = dict(zip(hdr, row))
            if r.get("case") != "LC1":
                continue
            k = r["part"].split("#")[0]
            v = float(r["vm_all_MPa"])
            if k not in gm or v > gm[k]["vm_LC1_MPa"]:
                gm[k] = {"vm_LC1_MPa": v, "material": r["material"], "Fty_MPa": float(r["Fty_MPa"]), "Ftu_MPa": float(r["Ftu_MPa"]),
                         "T_C": float(r["T_C"]), "pose": r["pose"]}
    A4y, A4u = prop(A4, "Fty") / 1e6, prop(A4, "Ftu") / 1e6
    res = {"load": SPIKE, "dlf_by_shape_and_period": dl, "dlf_max_by_shape": dmax, "DLF_bound": DLF_B,
           "dlf_note": ("undamped SDOF from rest over the lead's 1-5 ms band (the axial engine-on-gimbal mode is not computed: OPEN); the "
                        "rectangular pulse gives 2.0 for every T <= 8 ms, a 1 ms rise (Combustion tf 1 ms) gives up to the trapezoid value; the "
                        "impulse route is not used because td = 4 ms is not short against T (impulse regime needs td << T/4)"),
           "basis_LC1": {"pin_radial_max_over_poses_N": pin, "airframe_screw_shear_max_over_poses_N": scr, "thrust_N": THRUST_MAX_N,
                         "src": "S-3D v1.1 LC1 (500 N + 3.65 g + design rod forces): scaling ALL LC1 reactions by F_eq / 500 N is conservative "
                                "for the thrust-driven terms (ESTIMATE)"},
           "cases": {}}
    for lab, dlf in cases.items():
        Feq = SPIKE["F_N"] * dlf
        s = Feq / THRUST_MAX_N
        items = []
        P0 = pin * s
        items.append({"item": "gimbal 608 bearings (inner and outer axes, 2 per axis)", "role": "LOAD-BEARING", "load": round(P0, 0), "unit": "N per bearing",
                      "rating": C0_608_N, "rating_src": "608 C0 1.37 kN AS RECALLED (SKF class), TO-VERIFY",
                      "ratio": round(P0 / C0_608_N, 3), "MS": round(C0_608_N / P0 - 1.0, 3),
                      "criterion": "static capacity s0 = C0/P0 >= 1.0 (failure case, no SF): above it the raceways brinell (permanent dent); "
                                   "ring/ball fracture load NOT known (no maker data): ultimate not demonstrated"})
        Vs = scr * s
        items.append({"item": "16 x M5 airframe ring screws (thrust mount, ICD-1)", "role": "LOAD-BEARING", "load": round(Vs, 0), "unit": "N shear per screw",
                      "rating": round(0.577 * A4y * M5_A3_MM2, 0), "rating_src": "shear yield 0.577 Fty x A3 12.68 mm2, A4-70 class ASSUMED (ICD grade TO-DEFINE)",
                      "ratio": round(Vs / (0.577 * A4y * M5_A3_MM2), 3), "MS": round(0.577 * A4y * M5_A3_MM2 / Vs - 1.0, 3),
                      "MS_ult": round(0.6 * A4u * M5_A3_MM2 / Vs - 1.0, 3), "criterion": "no yield / no rupture in shear (SF 1.0, failure case)"})
        for k, g in sorted(gm.items()):
            v = g["vm_LC1_MPa"] * s
            items.append({"item": f"{k} ({g['material']}, S-3D LC1 peak x {s:.2f})", "role": "LOAD-BEARING", "load": round(v, 1), "unit": "MPa von Mises",
                          "rating": g["Fty_MPa"], "rating_src": f"Fty({g['T_C']:.0f} C) engmat", "ratio": round(v / g["Fty_MPa"], 3),
                          "MS": round(g["Fty_MPa"] / v - 1.0, 3) if v > 0 else None, "MS_ult": round(g["Ftu_MPa"] / v - 1.0, 3) if v > 0 else None,
                          "criterion": "von Mises vs Fty(T) and Ftu(T), SF 1.0 (failure case); S-3D peak node incl. the excluded ring as tabulated"})
        M = Feq * MISALIGN_ARM_M + SIDE_LOAD_FLOOR_NM * s
        for rk, rv in TVC_RATING_NM.items():
            items.append({"item": f"TVC linkage (servo + rods) vs {rk} N m", "role": "LOAD-BEARING", "load": round(M, 2), "unit": "N m hinge moment",
                          "rating": rv, "rating_src": "lead 35.3 N m (M_engine_GS) / mechanical.json hinge_moment_design 37.95 N m",
                          "ratio": round(M / rv, 3), "MS": round(rv / M - 1.0, 3),
                          "criterion": "spike hinge moment = F_eq x (0.5 mm + 0.25 deg x 233 mm, ASSUMED tolerances) + nozzle side-load floor x F_eq/500 "
                                       "(at full deflection the thrust line passes through the pivot: no extra moment)"})
        for pos, A_mm2, phi in (("needle open (stem area, uniform pressure)", math.pi / 4 * PINTLE["stem_d_mm"] ** 2, PINTLE["phi_stop_deg"]),
                                ("needle near-closed (seat area, chamber side only)", math.pi / 4 * PINTLE["seat_d_mm"] ** 2, PINTLE["phi_closed_deg"])):
            F = SPIKE["P_bar"] / 10.0 * A_mm2 * dlf
            ph = math.radians(phi)
            r_, L_ = PINTLE["crank_r_mm"], PINTLE["link_L_mm"]
            dxdphi = r_ * math.sin(ph) + r_ * r_ * math.sin(ph) * math.cos(ph) / math.sqrt(L_ * L_ - (r_ * math.sin(ph)) ** 2)
            Tq = F * dxdphi / 1000.0
            items.append({"item": f"pintle linkage, {pos}: link force", "role": "LOAD-BEARING", "load": round(F, 1), "unit": "N",
                          "rating": PINTLE["jam_design_link_N"], "rating_src": PINTLE["src"], "ratio": round(F / PINTLE["jam_design_link_N"], 3),
                          "MS": round(PINTLE["jam_design_link_N"] / F - 1.0, 3),
                          "criterion": "link force <= the jam design force at which every component has MS >= 0 (compression here: link Euler load >> 1 kN)"})
            items.append({"item": f"pintle servo back-drive, {pos}", "role": "FUNCTION", "load": round(Tq, 3), "unit": "N m at the crank",
                          "rating": PINTLE["stall_7V4_Nm"], "rating_src": "HV69 stall 0.90 N m at 7.4 V (retailer copies of MKS data, TO-CONFIRM)",
                          "ratio": round(Tq / PINTLE["stall_7V4_Nm"], 3), "MS": round(PINTLE["stall_7V4_Nm"] / Tq - 1.0, 3),
                          "criterion": f"back-drive torque F dx/dphi (dx/dphi {dxdphi:.3f} mm/rad at {phi:.2f} deg) below the stall torque; gear-train "
                                       "overload strength not published (TO-VERIFY)"})
        res["cases"][lab] = {"DLF": round(dlf, 3), "F_eq_N": round(Feq, 0), "factor_on_LC1": round(s, 3), "items": items}
        for it in items:
            table.append(["FA1Q-SPIKE", f"FA1Q {lab}", "A1_22.2", it["item"], it["load"], it["rating"], None, 1.0, None, it["MS"],
                          it.get("MS_ult"), it["criterion"][:160]])
    return res


def FA1_P():
    import sax
    return sax.FA1["P_head_abs_bar"]


if __name__ == "__main__":
    main()
