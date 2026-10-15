"""Pintle-drive mount thermal network: HV69 servo, MGN09H guide, crank housing, bracket (04-fea/thermal, v1, 2026-10-13, Mechanical).

Question (lead 2026-10-13): the head top soaks to 128-130 C (DC-B1 hi, TC-06 1.6 mm). Do the HV69 and the MGN09H survive, and what
stand-off / shield is needed?  Close this before CAD v3.4 is released.
Limits (sources):
  HV69 operating -10..60 C: retailer copies of MKS data (Electronics pintle_mini_servo_v1, mirrored), TO-CONFIRM with MKS; storage /
       non-operating limit NOT PUBLISHED -> the soak is screened against the same 60 C (only published number), TO-VERIFY with MKS.
  Mount limit 50 C in flight incl. relight (lead CHANGELOG 2026-10-12) -> applied to the bracket at the servo seat and the servo case.
  MGN09H: no temperature limit in the HIWIN MG catalogue read; polymer end caps / recirculation parts -> 80 C screen ASSUMED, TO-VERIFY.
Model: lumped transient network (lumped.py, backward Euler, Newton on radiation) of the planned v3.4 drive (pintle_v2p3/v2p4: crank axis
z 246.5, HV69 case z 224.7-253.7 on -y, crank housing +y, MGN09H rail beside the bonnet).  Boundaries = axisymmetric FE histories
(histories.npz of the run): head-top face r 20-26 mm, bonnet OD / top, case OD z 30-150 mm (mean).  Free nodes: bracket, servo, crank
housing, guide, optional shield, bay air, airframe wall.  Every geometric / surface value is ASSUMED or ESTIMATE (PARAMS tags).  This is a
design screen for the mount, not a prediction: T1 thermocouples on the bracket foot, servo case and guide (CF-3 / hot-fire) replace it.
Variants (mount): V0 bracket bolted directly to the head top; V1 4 G10 isolators (stand-off 2 mm + screw path); V2 V1 + polished Al
shield node intercepting every head/bonnet -> drive view, bare (low-e) bracket faces; V3 V2 + G10 pad under the servo ears.
Air: 'mixed' well-mixed bay (all engine surfaces, whole wall, bulkhead); 'strat' stratified bound - the case plume and every engine
surface feed an upper-bay layer that loses heat only to the upper wall (z 178-300) and the bulkhead.
Servo dissipation: in flight P_hold = V I_stall (T/Ts)^2 (zero-speed holding loss) with V 7.49 V, I_stall 1.7 A (Electronics
pintle_rail_v3 bound, ASSUMED), T/Ts 0.62 (C2 peak 0.56 / 0.90 N m) -> 4.9 W, taken as 5 W over each burn; 0 W bound; after the last
shutdown 0.1 W idle (ASSUMED; the spring closes the needle, the one-sided dog leaves the servo unloaded).
v2 (2026-10-13): unchanged network, run on the dispersed duty cycles; adds --variants and --vent (upper-bay vent as an air -> ambient
exchange G_vent = m_dot cp, W/K, 0 = closed-bay baseline) and converts G_vent to a natural-draft hole area (vent_area_mm2, ASSUMED Cd, H, dT).
"""
from __future__ import annotations
import sys, json, math, argparse, itertools, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lumped import Net, a_eff, lumped_selftest

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUTD = HERE / "networks"
T_AMB = 293.15

PARAMS = {
    "h_bay_W_m2K": (5.0, "ASSUMED enclosure natural convection inside the bay (sensitivity 2 / 10)"),
    "h_out_W_m2K": (5.0, "ASSUMED natural convection outside the airframe after landing (in-flight forced convection ignored: conservative)"),
    "eps_anodised": (0.75, "ASSUMED clear-anodised 6061 (head TC-02, bonnet TC-04, case TC-01, bracket)"),
    "eps_bare_Al": (0.10, "ASSUMED bare / polished 6061 bracket faces toward the hot parts (V2, V3)"),
    "eps_shield": (0.05, "ASSUMED polished Al sheet, both faces"),
    "eps_servo": (0.85, "ASSUMED HV69 case (anodised / plastic)"),
    "eps_steel_guide": (0.30, "ASSUMED"),
    "eps_wall": (0.85, "ASSUMED airframe inner wall (painted / CFRP)"),
    "m_bracket_kg": (0.040, "ESTIMATE planned v3.4 drive bracket (Al 6061-T6)"),
    "m_servo_kg": (0.021, "DATASHEET-retail: MKS HV69 21 g (Lindinger listing)"),
    "c_servo": (700.0, "ASSUMED mixed Al / steel / PCB"),
    "m_crankhousing_kg": (0.025, "ESTIMATE crank housing + crank + bearings A/B + spring"),
    "m_guide_kg": (0.049, "DATASHEET HIWIN MGN09H block 0.030 kg + 50 mm MGNR09R rail 0.019 kg"),
    "m_shield_kg": (0.004, "ESTIMATE 0.5 mm polished Al, ~3000 mm2"),
    "A_bracket_m2": (0.008, "ESTIMATE bracket wetted area (both faces)"),
    "A_servo_m2": (0.00316, "DERIVED 29 x 13 x 28.7 mm box"),
    "A_crankhousing_m2": (0.0020, "ESTIMATE"),
    "A_guide_m2": (0.0025, "ESTIMATE block + rail"),
    "A_headtop_m2": (math.pi * (0.03175 ** 2 - 0.020 ** 2), "DERIVED head-top annulus r 20-31.75 mm"),
    "A_bonnet_OD_m2": (math.pi * 0.040 * 0.032, "DERIVED bonnet OD 40 x 32 mm"),
    "A_bonnet_top_m2": (math.pi * 0.020 ** 2, "DERIVED"),
    "A_case_m2": (math.pi * 0.0635 * 0.146, "DERIVED case OD z 32-178 mm"),
    "A_wall_m2": (math.pi * 0.140 * 0.268, "DERIVED upper bay wall z 32-300 mm"),
    "A_wall_upper_m2": (math.pi * 0.140 * 0.122, "DERIVED wall above the head top z 178-300 mm (strat air sink)"),
    "m_wall_kg": (2700 * math.pi * 0.142 * 0.002 * 0.268, "ASSUMED Al tube 140 ID x 2 mm (airframe material TBD - ICD)"),
    "A_bulkhead_m2": (math.pi / 4 * 0.140 ** 2, "DERIVED tank bulkhead at the bay top (held at 20 C: tank liquid)"),
    "V_air_m3": (math.pi / 4 * 0.140 ** 2 * 0.268 - 0.0011, "DERIVED upper bay air minus the engine / drive volume ESTIMATE"),
    "G_isolator_each_W_K": (2 * 0.29 * 29.4e-6 / 0.002 / 2 + 1 / (1 / (16 * 7.07e-6 / 0.010) + 1 / (0.29 * 29.4e-6 / 0.002)),
                            "DERIVED G10 shoulder washer 7/3.4 x 2 mm (k 0.29 W/mK AS RECALLED) under the bracket foot // M3 A2 screw "
                            "shank (k 16) in series with the top G10 washer; 4 per bracket"),
    "G_direct_contact_W_K": (0.30, "ASSUMED Al-Al bolted contact 4 feet x ~30 mm2 x 2000 W/m2K + 4 screws"),
    "G_bracket_servo_W_K": (0.10, "ASSUMED HV69 Al ears on 4 x M2 (contact ~60 mm2 x ~1500 W/m2K); 0.03 lower bound"),
    "G_servo_pad_W_K": (0.012, "DERIVED V3: 1.5 mm G10 pad under the ears, 60 mm2 (k 0.29) // 4 x M2 A2 screws through G10 washers"),
    "G_bracket_crankhousing_W_K": (0.20, "ASSUMED bolted Al-Al"),
    "G_bracket_guide_W_K": (0.10, "ASSUMED rail bolted (steel on Al), 2 x M3"),
    "G_bonnet_guide_W_K": (0.013, "DERIVED stem 3 mm 17-4PH (k 18) over 10 mm + carriage contacts (series ignored: conservative)"),
    "G_servo_crank_W_K": (0.02, "ASSUMED dog coupling + face contact"),
    "G_shield_mount_W_K": (0.005, "ASSUMED shield on 3 G10 stand-offs from the bracket"),
    "F_head_bracket": (0.6, "ASSUMED base plate 5 mm over the head-top annulus"),
    "F_bonnet_bracket": (0.25, "ASSUMED"), "F_bonnet_guide": (0.15, "ASSUMED rail beside the bonnet"),
    "F_bonnettop_servo": (0.10, "ASSUMED servo >= 14 mm above the bonnet top, offset in y"),
    "F_bonnettop_crank": (0.10, "ASSUMED"), "F_part_wall": (0.4, "ASSUMED each drive part to the airframe wall"),
    "P_servo_burn_W": (5.0, "ESTIMATE holding loss V I_stall (T/Ts)^2 = 7.49 x 1.7 x 0.62^2 = 4.9 W (I_stall 1.7 A Electronics pintle_rail_v3 bound, "
                            "ASSUMED); 0 W lower bound; B-PNT-1 measures stall current and case temperature"),
    "P_servo_idle_W": (0.1, "ASSUMED after the last shutdown (needle closed by the spring, servo unloaded)"),
    # v2 (2026-10-13): upper-bay vent as an air -> ambient exchange G_vent = m_dot cp (W/K); 0 = closed bay (v1 baseline, conservative)
    "G_vent_W_K": (0.0, "baseline closed bay; --vent sweeps it (upper-bay venting, airframe ICD)"),
    "vent_Cd": (0.6, "ASSUMED sharp-edged hole discharge coefficient"),
    "vent_H_m": (0.20, "ASSUMED stack height between the low inlet vents and the high outlet vents of the upper bay"),
    "vent_dT_ref_K": (20.0, "ASSUMED bay-air rise used to convert G_vent to a hole area (the soak peak sees ~30-45 K: conservative)"),
}


def vent_area_mm2(G):
    """total outlet area (= inlet area) of a two-level natural-draft vent giving m_dot cp = G at the reference rise:
    m_dot = rho Cd A_eff sqrt(2 g H dT / T), A_eff = A / sqrt(2) for equal inlet and outlet areas in series"""
    if G <= 0:
        return 0.0
    rho, cp = 1.2, 1005.0
    v = math.sqrt(2 * 9.81 * P("vent_H_m") * P("vent_dT_ref_K") / T_AMB)
    return G / (rho * cp * P("vent_Cd") * v) * math.sqrt(2) * 1e6
LIMITS = {
    "servo_op_C": (60.0, "HV69 operating -10..60 C (retailer copies of MKS data, Electronics pintle_mini_servo_v1), TO-CONFIRM with MKS"),
    "servo_soak_C": (60.0, "HV69 storage limit NOT PUBLISHED -> screened at the operating 60 C, TO-VERIFY with MKS"),
    "mount_flight_C": (50.0, "lead CHANGELOG 2026-10-12: mount limit 50 C in flight incl. relight (bracket at the servo seat and servo case)"),
    "guide_C": (80.0, "MGN09H: NOT STATED in the HIWIN MG catalogue read; polymer end caps -> 80 C ASSUMED screen, TO-VERIFY with HIWIN"),
}
VARIANTS = {"V0": dict(mount="direct", shield=False, pad=False), "V1": dict(mount="iso", shield=False, pad=False),
            "V2": dict(mount="iso", shield=True, pad=False), "V3": dict(mount="iso", shield=True, pad=True)}


def P(k):
    return PARAMS[k][0]


def bc_from(t, y):
    return lambda tt: float(np.interp(tt, t, y))


def ex_area(A1, e1, F, A2, e2):
    """two grey surfaces, exchange area 1/[(1-e1)/(e1 A1) + 1/(A1 F) + (1-e2)/(e2 A2)]"""
    return 1.0 / ((1 - e1) / (e1 * A1) + 1.0 / (A1 * F) + (1 - e2) / (e2 * A2))


def build(hist, var, air, p_burn, G_bs, h_bay, segments, t_last, g_vent=0.0):
    t = hist["t_s"]
    head = hist["head_top_r20_26_mean"]
    bon_od = hist["bonnet_OD_mean"]
    bon_top = hist["bonnet_top_mean"]
    case_keys = [k for k in hist.files if k.startswith("case_OD_z") and k.endswith("_mean") and 30 <= int(k.split("_z")[1].split("_")[0]) < 150]
    case = np.mean([hist[k] for k in case_keys], axis=0)
    v = VARIANTS[var]
    n = Net()
    n.node("head", 0, head[0], bc=bc_from(t, head))
    n.node("bonnet_OD", 0, bon_od[0], bc=bc_from(t, bon_od))
    n.node("bonnet_top", 0, bon_top[0], bc=bc_from(t, bon_top))
    n.node("case", 0, case[0], bc=bc_from(t, case))
    n.node("bulkhead", 0, T_AMB, bc=lambda tt: T_AMB)
    n.node("ambient", 0, T_AMB, bc=lambda tt: T_AMB)
    n.node("bracket", P("m_bracket_kg") * 896.0, T_AMB)
    n.node("servo", P("m_servo_kg") * P("c_servo"), T_AMB)
    n.node("crank", P("m_crankhousing_kg") * 700.0, T_AMB)
    n.node("guide", P("m_guide_kg") * 460.0, T_AMB)
    n.node("wall", P("m_wall_kg") * 896.0, T_AMB)
    n.node("air", 1.2 * P("V_air_m3") * 1005.0, T_AMB)
    ea, eb, es = P("eps_anodised"), P("eps_bare_Al"), P("eps_shield")
    e_br = eb if v["shield"] else ea
    # conduction
    n.cond("head", "bracket", P("G_direct_contact_W_K") if v["mount"] == "direct" else 4 * P("G_isolator_each_W_K"))
    g_srv = 1.0 / (1.0 / G_bs + 1.0 / P("G_servo_pad_W_K")) if v["pad"] else G_bs
    n.cond("bracket", "servo", g_srv)
    n.cond("bracket", "crank", P("G_bracket_crankhousing_W_K"))
    n.cond("bracket", "guide", P("G_bracket_guide_W_K"))
    n.cond("bonnet_OD", "guide", P("G_bonnet_guide_W_K"))
    n.cond("servo", "crank", P("G_servo_crank_W_K"))
    # radiation engine -> drive (direct, or through the shield node)
    paths = [("head", P("A_headtop_m2"), ea, P("F_head_bracket"), "bracket", e_br),
             ("bonnet_OD", P("A_bonnet_OD_m2"), ea, P("F_bonnet_bracket"), "bracket", e_br),
             ("bonnet_OD", P("A_bonnet_OD_m2"), ea, P("F_bonnet_guide"), "guide", P("eps_steel_guide")),
             ("bonnet_top", P("A_bonnet_top_m2"), ea, P("F_bonnettop_servo"), "servo", P("eps_servo")),
             ("bonnet_top", P("A_bonnet_top_m2"), ea, P("F_bonnettop_crank"), "crank", ea)]
    if v["shield"]:
        n.node("shield", P("m_shield_kg") * 896.0, T_AMB)
        A_sh_tot = 0.0
        for src, A, e, F, dst, ed in paths:
            Ash = A * F                                              # shield area intercepting this path
            A_sh_tot += Ash
            n.rad(src, "shield", ex_area(A, e, F, Ash, es))            # front face intercepts the path's view
            n.rad("shield", dst, ex_area(Ash, es, 1.0, Ash, ed))     # back face sees the drive part (F ~ 1, A_dst ~ A_sh ESTIMATE)
        n.cond("bracket", "shield", P("G_shield_mount_W_K"))
        n.cond("shield", "air", h_bay * 2 * A_sh_tot)
    else:
        for src, A, e, F, dst, ed in paths:
            n.rad(src, dst, ex_area(A, e, F, A * F, ed))               # destination area ~ A F (ESTIMATE)
    # drive parts and the case to the wall; drive parts to the air
    for nm, A, e in (("bracket", P("A_bracket_m2"), ea), ("servo", P("A_servo_m2"), P("eps_servo")), ("crank", P("A_crankhousing_m2"), ea),
                     ("guide", P("A_guide_m2"), P("eps_steel_guide"))):
        n.rad(nm, "wall", a_eff(A, e, P("F_part_wall"), P("A_wall_m2"), P("eps_wall")))
        n.cond(nm, "air", h_bay * A)
    n.rad("case", "wall", a_eff(P("A_case_m2"), ea, 1.0, P("A_wall_m2"), P("eps_wall")))
    for nm, A in (("head", P("A_headtop_m2")), ("bonnet_OD", P("A_bonnet_OD_m2")), ("bonnet_top", P("A_bonnet_top_m2")), ("case", P("A_case_m2"))):
        n.cond(nm, "air", h_bay * A)
    if air == "mixed":
        n.cond("air", "wall", h_bay * P("A_wall_m2"))
    else:                                                           # stratified: only the upper wall touches the hot layer
        n.cond("air", "wall", h_bay * P("A_wall_upper_m2"))
    n.cond("air", "bulkhead", h_bay * P("A_bulkhead_m2"))
    n.cond("wall", "ambient", P("h_out_W_m2K") * P("A_wall_m2") * 1.03)
    if g_vent > 0:                                                  # v2: upper-bay vent exchange with outside air
        n.cond("air", "ambient", g_vent)
    # servo dissipation
    def q_servo(tt, segs=segments, pb=p_burn, tl=t_last):
        if any(a <= tt <= b for a, b in segs):
            return pb
        return P("P_servo_idle_W") if tt > tl else 0.0
    n.src("servo", q_servo)
    return n


def vlabel(var, g, vents):
    """case-group label: the bare variant name for the closed-bay baseline run, 'V3+vent0.2' in a vent sweep"""
    return var if tuple(vents) == (0.0,) else f"{var}+vent{g:g}"


def run(label, h_bays=(5.0,), variants=tuple(VARIANTS), vents=(0.0,)):
    rd = RUNS / label
    hist = np.load(rd / "histories.npz")
    meta = json.loads((rd / f"{label}_meta.json").read_text())
    t_last = meta["t_last_shutdown_s"]
    segs = [tuple(s) for s in meta["segments_s"]]
    t_end = float(hist["t_s"][-1])
    res = {"label": label, "segments_s": segs, "t_last_shutdown_s": t_last,
           "histories_sha256_16": hashlib.sha256((rd / "histories.npz").read_bytes()).hexdigest()[:16],
           "boundary_peaks_C": {k: round(float(hist[k].max()) - 273.15, 1) for k in ("head_top_r20_26_mean", "bonnet_OD_mean", "bonnet_top_mean")},
           "cases": []}
    for var, gv, air, pb, gbs, hb in itertools.product(variants, vents, ("mixed", "strat"), (0.0, P("P_servo_burn_W")), (0.03, P("G_bracket_servo_W_K")), h_bays):
        n = build(hist, var, air, pb, gbs, hb, segs, t_last, g_vent=gv)
        ts, T = n.solve(t_end, 1.0, t0=float(hist["t_s"][0]), record_every=2)
        fl = ts <= t_last + 1e-6
        row = {"variant": var, "group": vlabel(var, gv, vents), "G_vent_W_K": gv, "air": air, "P_servo_burn_W": pb,
               "G_bracket_servo_W_K": gbs, "h_bay": hb, "nodes": {}}
        for nm in ("bracket", "servo", "crank", "guide", "air", "wall") + (("shield",) if VARIANTS[var]["shield"] else ()):
            y = T[:, n.idx(nm)] - 273.15
            row["nodes"][nm] = {"T_max_C": round(float(y.max()), 1), "t_at_max_s": round(float(ts[int(np.argmax(y))]), 0),
                                "T_max_flight_C": round(float(y[fl].max()), 1), "T_end_C": round(float(y[-1]), 1)}
            if nm == "servo":
                row["nodes"][nm]["s_above_60C"] = round(float(np.sum(np.diff(ts)[y[1:] > 60.0])), 0)
        nd = row["nodes"]
        row["checks"] = {"servo_flight_le_50": nd["servo"]["T_max_flight_C"] <= LIMITS["mount_flight_C"][0],
                         "bracket_flight_le_50": nd["bracket"]["T_max_flight_C"] <= LIMITS["mount_flight_C"][0],
                         "servo_soak_le_60": nd["servo"]["T_max_C"] <= LIMITS["servo_soak_C"][0],
                         "guide_le_80": nd["guide"]["T_max_C"] <= LIMITS["guide_C"][0]}
        row["pass"] = all(row["checks"].values())
        res["cases"].append(row)
    # envelope per variant (worst over air model, servo power, ear conductance, h)
    env = {}
    for var in dict.fromkeys(r["group"] for r in res["cases"]):
        rows = [r for r in res["cases"] if r["group"] == var]
        e = {}
        for nm in ("bracket", "servo", "crank", "guide", "air"):
            w = max(rows, key=lambda r: r["nodes"][nm]["T_max_C"])
            wf = max(rows, key=lambda r: r["nodes"][nm]["T_max_flight_C"])
            e[nm] = {"T_max_C": w["nodes"][nm]["T_max_C"], "at": f'{w["air"]}, P {w["P_servo_burn_W"]} W, G {w["G_bracket_servo_W_K"]}, h {w["h_bay"]}',
                     "t_at_max_s": w["nodes"][nm]["t_at_max_s"], "T_max_flight_C": wf["nodes"][nm]["T_max_flight_C"]}
        e["all_cases_pass"] = all(r["pass"] for r in rows)
        e["n_cases"] = len(rows)
        e["n_pass"] = sum(r["pass"] for r in rows)
        e["G_vent_W_K"] = rows[0]["G_vent_W_K"]
        e["vent_area_mm2_each_level"] = round(vent_area_mm2(rows[0]["G_vent_W_K"]), 0)
        env[var] = e
    res["envelope"] = env
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("labels", nargs="+")
    ap.add_argument("--hbay", default="5")
    ap.add_argument("--out", default="servo_mount_net_v1.json")
    ap.add_argument("--version", default="v1", help="v2 (2026-10-13): same network, run on the dispersed duty cycles (DC-B1 v3 p99/max, DC-A1 p99)")
    ap.add_argument("--variants", default=",".join(VARIANTS), help="v2: subset of the mount variants, e.g. V3")
    ap.add_argument("--vent", default="0", help="v2: upper-bay vent exchange G_vent = m_dot cp (W/K), comma list; 0 = closed bay")
    a = ap.parse_args()
    OUTD.mkdir(exist_ok=True)
    hb = tuple(float(x) for x in a.hbay.split(","))
    vs = tuple(x.strip() for x in a.variants.split(","))
    gv = tuple(float(x) for x in a.vent.split(","))
    out = {"id": "servo_mount_net", "version": a.version, "date": "2026-10-13", "script": "04-fea/thermal/servo_mount_net.py",
           "lumped_selftest": lumped_selftest(), "params": {k: {"v": v[0], "tag": v[1]} for k, v in PARAMS.items()},
           "limits": {k: {"v": v[0], "tag": v[1]} for k, v in LIMITS.items()}, "variants": {k: VARIANTS[k] for k in vs},
           "vent_sweep_W_K": list(gv), "runs": [run(l, hb, vs, gv) for l in a.labels]}
    # conclusion: the lowest-numbered variant (or variant + vent) that passes every case of every run (all air models, servo powers, ear G, h_bay)
    groups = list(out["runs"][0]["envelope"])
    ok = [v for v in groups if all(r["envelope"][v]["all_cases_pass"] for r in out["runs"])]
    worst = {v: {"servo_max_C": max(r["envelope"][v]["servo"]["T_max_C"] for r in out["runs"]),
                 "guide_max_C": max(r["envelope"][v]["guide"]["T_max_C"] for r in out["runs"]),
                 "bracket_max_C": max(r["envelope"][v]["bracket"]["T_max_C"] for r in out["runs"]),
                 "servo_flight_max_C": max(r["envelope"][v]["servo"]["T_max_flight_C"] for r in out["runs"]),
                 "bracket_flight_max_C": max(r["envelope"][v]["bracket"]["T_max_flight_C"] for r in out["runs"]),
                 "n_pass": sum(r["envelope"][v]["n_pass"] for r in out["runs"]), "n_cases": sum(r["envelope"][v]["n_cases"] for r in out["runs"])}
             for v in groups}
    out["conclusion"] = {"variants_passing_all_cases": ok, "selected": ok[0] if ok else None, "worst_by_variant": worst,
                         "note": "screen against ASSUMED / TO-VERIFY limits (HV69 storage not published, MGN09H not stated); the stratified-air "
                                 "bound and h_bay 10 govern - upper-bay venting (airframe ICD) and TC-06 3.6 mm add margin; T1 thermocouples "
                                 "(bracket foot, servo case, guide, upper-bay air) replace the screen"}
    p = OUTD / a.out
    p.write_text(json.dumps(out, indent=1, default=float))
    print("CONCLUSION", json.dumps(out["conclusion"]))
    for r in out["runs"]:
        print(r["label"], r["boundary_peaks_C"])
        for v, e in r["envelope"].items():
            print("  ", v, f'pass {e["n_pass"]}/{e["n_cases"]}', f'vent {e["G_vent_W_K"]} W/K ~{e["vent_area_mm2_each_level"]:.0f} mm2/level', {k: (x["T_max_C"], x["T_max_flight_C"], x["t_at_max_s"], x["at"]) for k, x in e.items() if isinstance(x, dict)})
    print(p, hashlib.sha256(p.read_bytes()).hexdigest()[:16])
