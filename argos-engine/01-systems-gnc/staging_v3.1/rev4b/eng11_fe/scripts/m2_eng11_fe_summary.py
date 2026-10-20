"""m2_eng11_fe_summary v1.0 (GNC rev4b, 2026-10-19): summary of the ENG-11 FE-plant re-run (m2_eng11_fe v1.0 run
files, REV-GNC-6 RV6-14 (a)-(e)).  Reads <GNC_E11FE_OUT>/eng11fe_<variant>.json and eng11fe_check.json; computes no
margin (bookkeeping only).  Writes <GNC_E11FE_OUT>/eng11fe_summary.json.  Deterministic (no timestamps).
For every variant and axis: the passing K_s grid points (90-160 step 5) and their contiguous windows; the both-axes window;
the corners that set each edge (the last passing row's worst corner and the first failing row's first failure and worst
GM in its (condition, e, zeta) block).  Robust windows: the intersection of the both-axes pass sets over a group of
variants, with the variant / axis / corner that sets each edge.
Grid resolution 5 N m/rad: an edge is known to within 5 N m/rad; an edge at 90 or 160 is the grid limit, not a limit found.
Every number is DERIVED (linear CSI margins on SIM FE stiffness); K_s, J, bending and damping ASSUMED; no hardware data;
not physical approval."""
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

sys.dont_write_bytecode = True
VERSION = "m2_eng11_fe_summary v1.0"
OUT = os.environ.get("GNC_E11FE_OUT", "/home/claude/work/space/out/rev4b/eng11_fe")
RUN_VERSION = "m2_eng11_fe v1.0"
KS = [float(k) for k in range(90, 161, 5)]
AXES = ("alpha", "beta")
V5C_WINDOW = (100.0, 130.0)

LABEL = OrderedDict([
    ("A01", "FE rigid airframe, cone poses, T_REF, J 1.6e-3 cons (bench notch) [FE base]"),
    ("A02", "as A01, J 0.76e-3 cons"),
    ("A03", "as A01, J 2.7e-3 cons"),
    ("A04", "as A01, hot E -5 %"),
    ("A05", "as A01, hot E -10 %"),
    ("A06", "as A01, compliant airframe"),
    ("A07", "as A01, compliant airframe + hot E -10 %"),
    ("A07o", "as A07 with the notch re-referenced on its own structure ('own')"),
    ("A08", "as A01, cone + 8 deg stop poses"),
    ("A09", "as A07, J 0.76e-3 cons"),
    ("A10", "as A07, J 2.7e-3 cons"),
    ("A11", "as A01, cone + stop poses, compliant airframe, hot E -10 % [worst FE structure]"),
    ("A12", "V5c structure (CAD v3.3), own notch [the v3.2 basis, reproduction]"),
    ("B01", "as A01, J 1.6e-3 n48"),
    ("B02", "as A01, J 0.76e-3 n48"),
    ("B03", "as A01, J 2.7e-3 n48"),
    ("B04", "as A01, g = FEA3D post_k factor ('fea'; low by up to 1.34x on the cone)"),
    ("B05", "as A01, g = exact CAD kinematics ('kin')"),
    ("B06", "as A01, J 0 (rotor not in the rocking mode)"),
    ("B07", "as A01, two-mass rotor model ('tm', J 1.6e-3)"),
    ("C01", "as A01, bending x 0.9"),
    ("C02", "as A01, bending x 1.1"),
    ("C03", "as A12, bending x 0.9"),
    ("C04", "as A12, bending x 1.1"),
])
GROUPS = OrderedDict([
    ("J_1.6_cons_FE_structure", dict(variants=["A01", "A04", "A05", "A06", "A07", "A08", "A11"],
                                     what="J 1.6e-3 cons on the FE structure: rigid / compliant airframe, T_REF / hot E -5 / -10 %, "
                                          "cone / cone + stop poses (RV6-14 (a), (b))")),
    ("J_1.6_cons_FE_structure_and_bending", dict(variants=["A01", "A04", "A05", "A06", "A07", "A08", "A11", "C01", "C02"],
                                                 what="as above plus bending x 0.9 / 1.1 (RV6-14 (d))")),
    ("J_0.76_cons_FE", dict(variants=["A02", "A09"], what="J 0.76e-3 cons: FE rigid T_REF and compliant + hot E -10 %")),
    ("J_2.7_cons_FE", dict(variants=["A03", "A10"], what="J 2.7e-3 cons: FE rigid T_REF and compliant + hot E -10 %")),
    ("J_all_cons_FE_rigid_TREF", dict(variants=["A01", "A02", "A03"], what="J 0.76 / 1.6 / 2.7e-3 cons, FE rigid T_REF")),
    ("J_all_cons_FE_worst_structure", dict(variants=["A07", "A09", "A10"], what="J 0.76 / 1.6 / 2.7e-3 cons, compliant + hot E -10 %")),
    ("J_all_n48_FE_rigid_TREF", dict(variants=["B01", "B02", "B03"], what="J 0.76 / 1.6 / 2.7e-3 n48, FE rigid T_REF")),
    ("V5c_reference_and_bending", dict(variants=["A12", "C03", "C04"], what="V5c plant (v3.2 basis), bending x 0.9 / 1.0 / 1.1")),
])
# the J / structure matrix the datasheet sentence is read from (RV6-14: window for each J and structure)
MATRIX = OrderedDict([
    ("FE rigid T_REF cone", OrderedDict([("J0.76 cons", "A02"), ("J1.6 cons", "A01"), ("J2.7 cons", "A03"),
                                         ("J0.76 n48", "B02"), ("J1.6 n48", "B01"), ("J2.7 n48", "B03"),
                                         ("J0 (rotor out)", "B06"), ("J1.6 two-mass", "B07")])),
    ("FE hot E -5 %", OrderedDict([("J1.6 cons", "A04")])),
    ("FE hot E -10 %", OrderedDict([("J1.6 cons", "A05")])),
    ("FE compliant airframe", OrderedDict([("J1.6 cons", "A06")])),
    ("FE compliant + hot E -10 %", OrderedDict([("J0.76 cons", "A09"), ("J1.6 cons", "A07"), ("J2.7 cons", "A10")])),
    ("FE compliant + hot E -10 %, own notch", OrderedDict([("J1.6 cons", "A07o")])),
    ("FE cone + stop poses", OrderedDict([("J1.6 cons", "A08")])),
    ("FE cone + stop, compliant, hot E -10 %", OrderedDict([("J1.6 cons", "A11")])),
    ("FE bending x 0.9", OrderedDict([("J1.6 cons", "C01")])),
    ("FE bending x 1.1", OrderedDict([("J1.6 cons", "C02")])),
    ("FE g = exact CAD kinematics", OrderedDict([("J1.6 cons", "B05")])),
    ("FE g = FEA3D post_k", OrderedDict([("J1.6 cons", "B04")])),
    ("V5c (v3.2 basis), own notch", OrderedDict([("J1.6 cons", "A12")])),
    ("V5c bending x 0.9", OrderedDict([("J1.6 cons", "C03")])),
    ("V5c bending x 1.1", OrderedDict([("J1.6 cons", "C04")])),
])


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def runs(ks):
    """contiguous runs of grid points -> [[lo, hi], ...]"""
    out = []
    for k in sorted(ks):
        if out and abs(k - out[-1][1] - 5.0) < 1e-9:
            out[-1][1] = k
        else:
            out.append([k, k])
    return out


def wtxt(w):
    lo, hi = w
    a = f"<= {lo:g}" if lo == KS[0] else f"{lo:g}"
    b = f">= {hi:g}" if hi == KS[-1] else f"{hi:g}"
    return f"{a}-{b}" if lo != hi else (a if lo in (KS[0], KS[-1]) else f"{lo:g} only")


def primary(ws):
    """the window that overlaps the V5c design-to window most; else the lowest"""
    if not ws:
        return None
    def ov(w):
        return max(0.0, min(w[1], V5C_WINDOW[1]) - max(w[0], V5C_WINDOW[0]) + 5.0) if w[1] >= V5C_WINDOW[0] and w[0] <= V5C_WINDOW[1] else 0.0
    best = max(ws, key=lambda w: (ov(w), -w[0]))
    return best if ov(best) > 0 else ws[0]


def rowkey(a, k):
    return f"{a}|Ks{k:g}"


def corner_pass(r):
    return OrderedDict(gm_up_min_dB=r["gm_up_min_dB"], worst=r["worst"], pm_abs_min_deg=r.get("pm_abs_min_deg"),
                       sm_min=r.get("sm_min"), n_corners=r["n_corners"])


def ctype(corner, band):
    """plain-language class of a corner string (bookkeeping)"""
    if not corner:
        return None
    m = re.search(r"\|f1? ?([0-9.]+)\|", corner)
    f = float(m.group(1)) if m else None
    if "maxq" in corner and "|z0.1" in corner:
        return "low-frequency max-q corner (fins, worst actuator, zeta 0.10; rocking mode low against the control loop)"
    if f is not None and band and band[0] - 1.5 <= f <= band[1] + 0.5 and "|z0.02" in corner:
        return "bending coincidence (full-tank rocking mode at the first bending mode, zeta 0.02)"
    if corner.startswith("landing|hover"):
        return "landing hover corner (rocking mode near the landing bending mode, zeta 0.02)"
    return "other"


def corner_fail(r, band=None):
    return OrderedDict(first_fail=r["first_fail"], type=ctype(r["first_fail"], band),
                       fail_block_worst=r.get("fail_block_worst"), n_eval=r["n_eval"], n_corners=r["n_corners"])


def edges(rows, w, band=None):
    """corners that set the edges of the both-axes window w = [lo, hi]"""
    lo, hi = w
    e = OrderedDict()
    for side, inside, outside in (("upper", hi, hi + 5.0), ("lower", lo, lo - 5.0)):
        d = OrderedDict(edge_Ks=inside)
        if outside < KS[0] or outside > KS[-1]:
            d["set_by"] = "grid limit (no failure found inside 90-160)"
            d["inside_worst"] = {a: corner_pass(rows[rowkey(a, inside)]) for a in AXES}
        else:
            fa = [a for a in AXES if not rows[rowkey(a, outside)]["pass_6dB"]]
            d["set_by_axes"] = fa
            d["outside_Ks"] = outside
            d["outside_fail"] = {a: corner_fail(rows[rowkey(a, outside)], band) for a in fa}
            d["inside_worst"] = {a: corner_pass(rows[rowkey(a, inside)]) for a in AXES}
        e[side] = d
    return e


def load_variant(vid):
    p = os.path.join(OUT, f"eng11fe_{vid}.json")
    if not os.path.exists(p):
        return None, None
    return json.load(open(p)), p


def summarize_variant(vid, d):
    rows = d["rows"]
    s = OrderedDict(label=LABEL[vid], spec=d["spec"], J_kgm2=d["J_kgm2"], poses=d["poses"], done=d["done"],
                    version=d["version"])
    complete = d["done"] and all(rowkey(a, k) in rows for a in AXES for k in KS)
    s["complete"] = complete
    if not complete:
        s["n_rows"] = len(rows)
        return s, None
    pas = {a: [k for k in KS if rows[rowkey(a, k)]["pass_6dB"]] for a in AXES}
    both = [k for k in KS if all(rows[rowkey(a, k)]["pass_6dB"] for a in AXES)]
    s["pass_Ks"] = OrderedDict((a, pas[a]) for a in AXES)
    s["windows"] = OrderedDict((a, [wtxt(w) for w in runs(pas[a])]) for a in AXES)
    bw = runs(both)
    s["both_axes_pass_Ks"] = both
    s["both_axes_windows"] = [wtxt(w) for w in bw]
    pw = primary(bw)
    s["primary_window"] = wtxt(pw) if pw else "NONE (no K_s in 90-160 passes on both axes)"
    s["primary_window_Ks"] = pw
    s["covers_v5c_window_100_130"] = bool(pw and pw[0] <= V5C_WINDOW[0] and pw[1] >= V5C_WINDOW[1])
    if pw:
        s["primary_edges"] = edges(rows, pw, d["fmap"]["alpha"]["band_Hz"])
        s["gm_min_inside_primary_dB"] = OrderedDict(
            (a, min(rows[rowkey(a, k)]["gm_up_min_dB"] for k in KS if pw[0] <= k <= pw[1])) for a in AXES)
    fails = OrderedDict()
    for a in AXES:
        for k in KS:
            r = rows[rowkey(a, k)]
            if not r["pass_6dB"]:
                fails[rowkey(a, k)] = OrderedDict(first_fail=r["first_fail"], type=ctype(r["first_fail"], d["fmap"]["alpha"]["band_Hz"]),
                                                  block_worst_dB=(r.get("fail_block_worst") or {}).get("worst_gm_dB"),
                                                  block=(r.get("fail_block_worst") or {}).get("block"))
    s["failing_rows"] = fails
    s["fmap_Ks_pose_max_reaches_band"] = OrderedDict((a, d["fmap"][a]["Ks_pose_max_reaches_band"]) for a in AXES)
    s["coincidence_band_Hz"] = d["fmap"]["alpha"]["band_Hz"]
    if d["spec"].get("model") == "tm":
        s["tm_f1_f2_Hz_at_100_130"] = OrderedDict(
            (rowkey(a, k), OrderedDict(f1=rows[rowkey(a, k)].get("f1_full_Hz"), f2=rows[rowkey(a, k)].get("f2_full_Hz")))
            for a in AXES for k in (100.0, 130.0))
    return s, OrderedDict(both=set(both), rows=rows, band=d["fmap"]["alpha"]["band_Hz"])


def group_window(name, g, data):
    vs = g["variants"]
    miss = [v for v in vs if v not in data]
    out = OrderedDict(what=g["what"], variants=vs)
    if miss:
        out["incomplete"] = miss
        return out
    inter = sorted(set.intersection(*[data[v]["both"] for v in vs]))
    ws = runs(inter)
    out["pass_Ks"] = inter
    out["windows"] = [wtxt(w) for w in ws]
    pw = primary(ws)
    out["primary_window"] = wtxt(pw) if pw else "NONE"
    if pw:
        lo, hi = pw
        e = OrderedDict()
        for side, outside in (("upper", hi + 5.0), ("lower", lo - 5.0)):
            if outside < KS[0] or outside > KS[-1]:
                e[side] = "grid limit"
                continue
            setters = []
            for v in vs:
                for a in AXES:
                    r = data[v]["rows"][rowkey(a, outside)]
                    if not r["pass_6dB"]:
                        setters.append(OrderedDict(variant=v, axis=a, Ks=outside, first_fail=r["first_fail"],
                                                   type=ctype(r["first_fail"], data[v]["band"]),
                                                   block_worst_dB=(r.get("fail_block_worst") or {}).get("worst_gm_dB")))
            e[side] = setters
        out["primary_edges_set_by"] = e
    return out


def pw_of(S, v):
    s = S["variants"].get(v, {})
    return s.get("primary_window", "INCOMPLETE") if s.get("complete") else "INCOMPLETE"


def proposal(S, data):
    """GNC's proposed datasheet sentence, composed from the computed windows (text, DERIVED basis)"""
    need = ["A01", "A02", "A03", "A12", "C01", "C02", "B07"]
    if any(v not in data for v in need):
        return OrderedDict(status="INCOMPLETE: " + ", ".join(v for v in need if v not in data))
    g1 = S["groups"]["J_1.6_cons_FE_structure"]
    gall = S["groups"]["J_all_cons_FE_rigid_TREF"]
    v5c = set(data["A12"]["both"])
    fe_struct = set(g1["pass_Ks"]) if "pass_Ks" in g1 else set(data["A01"]["both"])
    both_plants = runs(sorted(v5c & fe_struct))
    dt = primary(both_plants)
    n48 = [pw_of(S, v) for v in ("B02", "B01", "B03")]
    out = OrderedDict(
        status="PROPOSAL for the lead (227 (3) keeps the decision); DERIVED basis; not physical approval",
        findings=[
            f"V5c plant (v3.2 basis, CAD v3.3), J 1.6e-3 cons: both axes pass {pw_of(S, 'A12')} N m/rad (reproduces the v3.2 window).",
            f"FE plant (CAD v3.5.1), rigid airframe, T_REF, J 1.6e-3 cons: {pw_of(S, 'A01')} N m/rad; over the FE structure set "
            f"(rigid / compliant airframe, T_REF / hot E -5 / -10 %, cone / stop poses): "
            f"{g1.get('primary_window', 'INCOMPLETE: ' + ', '.join(g1.get('incomplete', [])))}.",
            f"J on the FE plant (cons): 0.76e-3 {pw_of(S, 'A02')}; 1.6e-3 {pw_of(S, 'A01')}; 2.7e-3 {pw_of(S, 'A03')} N m/rad; "
            f"all three J together: {gall.get('primary_window', 'INCOMPLETE')}.",
            f"n48 convention (J 0.76 / 1.6 / 2.7e-3): {' / '.join(n48)} N m/rad.",
            f"Rotor model: two-mass (J 1.6e-3) {pw_of(S, 'B07')}; J 0 (rotor out of the mode) {pw_of(S, 'B06')} N m/rad.",
            f"First bending x 0.9 / x 1.1: FE {pw_of(S, 'C01')} / {pw_of(S, 'C02')}; V5c {pw_of(S, 'C03')} / {pw_of(S, 'C04')} N m/rad."],
        design_to_both_plants_nominal_J=(wtxt(dt) if dt else "NONE"),
        design_to_rule="intersection of the V5c window (A12) and the FE structure-set window at the nominal J (group "
                       "J_1.6_cons_FE_structure, else A01)")
    return out


def main():
    chk_p = os.path.join(OUT, "eng11fe_check.json")
    chk = json.load(open(chk_p))
    S = OrderedDict(version=VERSION, run_version=RUN_VERSION, date="2026-10-19",
                    question="does the design-to window 100 <= K_s <= 130 N m/rad (RV6-01 text, V5c plant, CAD v3.3) hold on the 3D FE "
                             "plant of CAD v3.5.1, and what is the window for each J and structure, with the corners that set it? "
                             "(REV-GNC-6 RV6-14 (a)-(e); lead CHANGELOG 227 (3))",
                    tags="DERIVED (linear CSI margins, m2_eng11 v1.1 model and corners) on SIM FE stiffness (FEA3D C7.1, CAD v3.5.1); "
                         "K_s, J value, rocking damping, bending, the compliant-airframe spring and hot E ASSUMED; no hardware data; not "
                         "physical approval; staged apart from the gnc.json v3.2 text (not folded)",
                    grid="K_s 90-160 N m/rad step 5; edges known to +/-5 N m/rad; '<= 90' / '>= 160' are grid limits",
                    criterion="ENG-07d: closed loop stable and upper GM >= 6 dB at every floor20 corner, continuous pose envelope "
                              "(0.1 Hz + 0.02 Hz near the bending frequency), fixed ECU notch Q 1 / -12 dB at e 0.95 / 1 / 1.05 x the "
                              "bench landing centre-pose mode, zeta 0.02 / 0.05 / 0.10",
                    check=OrderedDict(path=os.path.basename(chk_p), sha256_16=sha16(chk_p), passed=chk["passed"],
                                      c3_reproduces_rev_gnc6_v05B=chk["c3_reproduce_rev_gnc6_v05B"]["all_same"],
                                      c4_two_mass_limits=[chk["c4_two_mass_limits"]["T1_ok"], chk["c4_two_mass_limits"]["T2_ok"]],
                                      kin_vs_v5c_max_rel_diff=chk["c2_kinematics"]["max_rel_diff_kin_vs_v5c"],
                                      K_af_Nm_per_rad=chk["c1_fe_table"]["K_af"],
                                      compliant_ratio_stop045=chk["c1_fe_table"]["compliant_ratio"],
                                      centre_full_Hz=chk["c5_centre_full_Hz"],
                                      inputs=chk["inputs"]["files"]),
                    legend=OrderedDict(
                        corner="tank state (full / landing) | floor20 condition | actuator corner | aero corner | f<rocking-mode Hz at "
                               "that pose and condition> | e<notch tuning factor> | z<rocking damping> [| GM<upper gain margin dB>]; "
                               "two-mass rows name the pose (or 'A-B@x' on the skeleton) and f1 = the first (rocking) mode",
                        first_fail="the first corner below 6 dB in the evaluation order (full tank, zeta 0.02, near bending first)",
                        fail_block_worst="the lowest GM in that corner's (condition, e, zeta) block (lumped model only); -99.0 = closed "
                                         "loop UNSTABLE at that corner",
                        window="a contiguous run of passing grid points; '<= 90' / '>= 160' = the grid limit, not a found edge",
                        primary_window="the both-axes window overlapping the v3.2 design-to window 100-130 most (else the lowest)"),
                    how_to_rerun=OrderedDict(
                        tree="01-systems-gnc/staging_v3.1/rev4/sim/gnc_dev3_sim6_v2.9-dev (gncsim 16 files, scripts/m2_eng11.py "
                             "aaad9a07a0551b9b, m2_csi.py 2928d4decb6eac03, m2_csi_v3.py edd32bb4c3fbff79, m2r3_env.sh "
                             "3db997bd5ba95e20, run_rev4_queue2.sh 0871253befcf0e46: byte-identical to the run tree) with "
                             "eng11_fe/scripts/m2_eng11_fe.py (and m2_eng11_fe_q.py, m2_eng11_fe_summary.py) added to its scripts/",
                        env="source scripts/m2r3_env.sh; GNC_IFACE=<rev4/sim/iface_v351> GNC_IFACE_PIN=<rev4/pins/pins_rev4/"
                            "pins_rev4_v351.sha256 (cf6d8d010833a274)> GNC_ACT_RATE=$GNC_IFACE/actuator_rate_check_v2.json "
                            "GNC_E11_MASS=v351 GNC_E11FE_OUT=<dir>; GNC_E11FE_PART=check, then GNC_E11FE_PART=run "
                            "GNC_E11FE_VARIANTS=<ids>; $PY scripts/m2_eng11_fe.py; then $PY scripts/m2_eng11_fe_summary.py",
                        cost="4.5-22 min per variant on one core (a passing row evaluates every corner)",
                        reads="hub 04-fea/assembly3d results (k_cone_c71, k_stop_c71, k_pose_neutral_c71, k_stop045_compliant_c71, "
                              "k_range_v351, modal_summary_v351), 03-cad/src/tvc_kinematics.py and config.py (read only, no "
                              "config.build()), 04-fea/stiffness/gimbal_k_summary_V5c_v1.json, interfaces/mechanical.json, "
                              "reviews/gnc/rev4/results/v05_eng11_env.json and v09_fe_plant.json (sha-pinned in eng11fe_check.json)"),
                    files=OrderedDict(), variants=OrderedDict(), groups=OrderedDict(), matrix=OrderedDict())
    data = {}
    for vid in LABEL:
        d, p = load_variant(vid)
        if d is None:
            S["variants"][vid] = OrderedDict(label=LABEL[vid], status="NOT RUN")
            continue
        if d.get("version") != RUN_VERSION:
            raise RuntimeError(f"{vid}: version {d.get('version')} != {RUN_VERSION}")
        S["files"][vid] = OrderedDict(path=os.path.basename(p), sha256_16=sha16(p))
        s, dd = summarize_variant(vid, d)
        S["variants"][vid] = s
        if dd:
            data[vid] = dd
    for name, g in GROUPS.items():
        S["groups"][name] = group_window(name, g, data)
    for row, cols in MATRIX.items():
        S["matrix"][row] = OrderedDict((c, (S["variants"][v].get("primary_window", "INCOMPLETE") if v in data else "INCOMPLETE")
                                        + f" [{v}]") for c, v in cols.items())
    S["matrix_detail"] = OrderedDict()
    for row, cols in MATRIX.items():
        for c, v in cols.items():
            if v not in data:
                S["matrix_detail"][f"{row} / {c}"] = OrderedDict(variant=v, window="INCOMPLETE")
                continue
            sv = S["variants"][v]
            det = OrderedDict(variant=v, window=sv["primary_window"], both_axes_windows=sv["both_axes_windows"])
            for side in ("lower", "upper"):
                e = (sv.get("primary_edges") or {}).get(side)
                if not e:
                    continue
                if "set_by" in e:
                    det[side] = e["set_by"]
                else:
                    det[side] = [OrderedDict(axis=a, Ks=e["outside_Ks"], type=x["type"], first_fail=x["first_fail"],
                                             block_worst_dB=(x.get("fail_block_worst") or {}).get("worst_gm_dB"))
                                 for a, x in e["outside_fail"].items()]
            S["matrix_detail"][f"{row} / {c}"] = det
    S["proposal"] = proposal(S, data)
    # FEA3D post_k servo factor against the exact CAD kinematics (finding for FEA3D, not used by the primary plant)
    rows = chk["c2_kinematics"]["rows"]
    cone = [rows[p][f"kin_over_fea_{a}"] for p in rows if not p.startswith("stop") and p != "centre" for a in AXES]
    stop = [rows[p][f"kin_over_fea_{a}"] for p in rows if p.startswith("stop") for a in AXES]
    S["finding_fea3d_g_factor"] = OrderedDict(
        what="FEA3D post_k servo factor g_fea (rod arm over the full horn radius, horn normal to the rod) against the exact CAD "
             "linkage kinematics g_kin (03-cad tvc_kinematics solve_psi, horn crank included): g_kin / g_fea",
        cone_7deg_range=[round(min(cone), 4), round(max(cone), 4)], stop_8deg_range=[round(min(stop), 4), round(max(stop), 4)],
        centre=1.0,
        consequence="FEA3D's 'with servo' engine stiffness (REPORT-FEA3D 9) under-counts the servo spring off-centre; GNC's primary "
                    "plant uses the V5c g, which equals g_kin within " + f"{chk['c2_kinematics']['max_rel_diff_kin_vs_v5c'] * 100:.2f} %"
                    " on the cone; variant B04 flies g_fea for comparison",
        tag="DERIVED (kinematics); for FEA3D / Mechanical, not a GNC requirement")
    S["n_variants_complete"] = len(data)
    S["n_variants"] = len(LABEL)
    p = os.path.join(OUT, "eng11fe_summary.json")
    with open(p + ".tmp", "w") as f:
        json.dump(S, f, indent=1, ensure_ascii=False)
    os.replace(p + ".tmp", p)
    print(f"wrote {p} {sha16(p)}; complete {len(data)}/{len(LABEL)}")
    for vid, s in S["variants"].items():
        if s.get("complete"):
            print(f"{vid:5s} alpha {s['windows']['alpha']} beta {s['windows']['beta']} both {s['both_axes_windows']} "
                  f"primary {s['primary_window']}")
        else:
            print(f"{vid:5s} {s.get('status', 'INCOMPLETE')} rows {s.get('n_rows')}")
    for name, g in S["groups"].items():
        print(f"group {name}: {g.get('windows', g.get('incomplete'))} primary {g.get('primary_window')}")


if __name__ == "__main__":
    main()
