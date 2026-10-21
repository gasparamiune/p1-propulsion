"""Margin matrix v3.5.2: every part x every case (fea3d 2026-10-20; brief item 7, CHANGELOG 234 (4) all-node rule, REV-MECH-2 classes).

Cell = MS_y / MS_u (allowable / (SF x stress) - 1), minimum over states / poses / sub-cases, with BOTH node sets:
  regular   the regular node set (idealisation classes excluded within 1.0 mm: RE re-entrant = BREP zero-radius concave edges or facet
            turns > ~60 deg ('brep60'), ID idealisation = RBE3 couplings / rigid connectors / ground / tie-patch edges, BT bad tets), and
  all-node  every node, with its node, class and distance to the class feature.
The cell value follows 234 (4): the regular value stands only where the all-node minimum sits at an idealisation that a named sub-model or
contact FE replaces (owner and line in the cell's 'basis') or where refinement converges (the refined value is used); otherwise the
all-node value is the cell.  Every negative cell carries a REV-MECH-2 class (REVIEW-MECHANICAL-R2 section 10):
  DC design change; TS-183 thermal-secondary under 183 (1) (primary and shakedown pass; LCF and temperature with Mechanical); TS-212 TC-02
  under 212 (1) ((a)-(c) pass, (d) open); BR brittle and thermal (183 (2) capture / containment); CH char primary vs the ASSUMED 20 MPa;
  MF model-fidelity question on the value (the class it carries stands; value re-posted on the named variant).
Sources (SIM unless tagged; v3.5.1 cells are carried from the published c71 posts where no v3.5.2 run covers them, only for parts NOT
changed in v3.5.2, marked 'carried v3.5.1'; their all-node minima are re-classified under brep60 on the v3.5.1 model
(results/v352/c71_allnode_classes.json); their regular values stay as published (v3.5.1 'mesh30' rule)):
  LC1 / LC2          f1_post_lc1v352g (GVLO) + f1_post_lc1v352h (GVHI) at B1_21.65 / 19 / 2 / 1: envelope of the two bounds (lead 04:13Z);
                     merged-node map f1_post_lc1v352 (L1, interim run on the v3.5.1 S-AX map L1_thv351_TB1GC_cad351: both RM2-13
                     clearances closed; NOT the v3.5.2 NF2b field) = perfect-contact information column 'LC1 merged v351 map (info)'
                     (12:11Z label fix: the column was labelled 'NF2b' in the 09:47Z draft by mistake)
  LC2F               v3.5.1 carried (234 (2): LC2F stays as published): s3d_pose_<cone>_c71 case LC2F, 9 cone poses
  FA1Q/D/U/S/T       f1_post_fa1v352n (merged NF2b A1_22.2; 230 (2) band values 94 / 121 / 147 bar abs, FA1S 151.04; posted by hand
                     2026-10-20T20:55:18Z, runs/post_fa1v352n.log: chain E posts FA1 runs by hand and this post had not been run)
  LC3 cold           f1_post_lc3_pose_<stop>_v352r3R3 (rev 3 levers at R3), 8 stop poses; lever-root cells (GM-01 / GM-02) where R2 -> R3
                     changes the peak by > 5 % quote the p = 1 bound (DERIVED, order ASSUMED; lead 12:28Z (5); results/v352/
                     lever_root_bound_v352.json, R2 and R3 values in the cell record)
  LC3 hot bound      f1_lc3_hot_bound_v352g3 / _v352h3 (DERIVED, node-wise on the R3 base lc1v352hbg3 / hbh3, GVLO / GVHI envelope);
                     GM-01 / GM-02 also from the item-1 lever-root table results/v352/lever_root_table_v352.json (ACCEPTED lead
                     20:44:07Z (1)): per pose, hot bound + the p = 1 increment at the ruled GM-02 cells (DERIVED, order ASSUMED).
                     All-node rows on lc3_bound's part-max branch (engine parts outside its SAME_MESH_ENGINE list: their increments
                     are not summed node by node; lc3_bound adds the part's REGULAR-node maximum, which does not bound a singular
                     node's own increment) take (1) min(stored, node-wise at the stored node) from results/v352/hb_singular_check_v352.json
                     (run 2026-10-20, between the 21:28:05Z and 21:35:34Z date -u readings; at 3 decimals this lowers TC-04 n42993,
                     LC3 and F2, ruled lead 21:47:29Z (4), and NZ-04 F2), then (2) the rigorous part-wide bound over every node of the
                     part (results/v352/hb_partwide_v352.json, unrounded; added after the 21:50:58Z date -u reading) wherever it is
                     lower than that all-node value at 3 decimals, with the stored value beside it and the method named in the cell
                     (lead 21:47:29Z).  Same for the F2 hot bound.
  GS / TD / LC6 F2   s3d_pose_<cone>_v352r3R3, 9 cone poses (GS lever roots at alpha+ / alpha-: the same p = 1 bound rule);
                     F2 hot bound f1_lc3_hot_bound_s3d_v352g3 / _h3 (DERIVED; GS + TD + LC6 increment); GM-01 / GM-02 also from
                     the lever-root table as for LC3 (the hot cone values are lower bounds on the GS-only hot margin, lead 20:44:07Z (1))
  LC6 soak           f1_post_lc1v352g B1_51.7 / B1_70.7 + f1_post_lc1v352h B1_43.7 / B1_70.7 (global LC6 at the soak states)
  TB70 / TBS         f1_post_tb352g / tb352h (blocked distribution BL); 188 (9): TB70 nominal SF 1.5 / 2.0, TBS abnormal SF 1.0 / 1.5
                     (line 106 = criterion type); (a) / (b) / thermal share from results/v352/tb_primary_v352.json
  TS2 (info)         soak states of lc1v352g / h + soak352g / h (TS2 = thermal only, SF 1.0)
  J-FWD              one-sector contact sub-model rows (jfwd_cells(), 14:49Z): js5 cells_v352An.json (A_n 68.4) + the soak envelope
                     results/v352/jfwd_soak_envelope_v352_v6.json (sha16 in the output; 240 (9)(i); v6 FINAL, lead 2026-10-21T02:01:34Z
                     (E), 03:30:46Z (3), 05:17:36Z (3): cD moved envelope quantities: worst of the computed histories and edge forms,
                     sharp js5 / (a) / (a') / (a'') + (b2) R0.2 incl. its repeats + (b1) s9 mu 0.2 R0.2 incl. its repeats with its seat
                     lines at C1 + (b2') s9 mu 0 + cD's resultants (s6 + Balls, FINAL TC-01, mu 0; its seat lines per the 02:01:34Z (C)
                     rule: s6 + C1 stand); v5 ef22b59cf2413b46 (ACCEPTED 03:30:46Z (3)), v4 9d9fd8ee991f9887 (ADOPTED 00:39:30Z (1)), v3
                     0872de4ea7e3601d and v2 336568296bdb896f = superseded records) [SIM / DERIVED]; Mechanical's FA1S hand checks (i)-(iii) and
                     5020A Eq. 22 (04-fea/v352/jfwd_fix_v352_v2.json, IN718 option) [CALC]; Mechanical's IN718 rows on the FE envelope
                     (newest published of jfwd_in718_rows_v352_v7 / v6 / v5 / v4; v7 = route (i) (HW-170 disc spring, lead 16:53Z R2),
                     on envelope v3 (superseded; Mechanical re-maps them ONCE on the final envelope, lead 00:39:30Z (1)), 3750 N column
                     GOVERNS and 4096 N is information (J-F1
                     maximum capped at 3750 N, lead 17:56:12Z); TC-02 thread shear on Mechanical's THE ROW A_n 67.93 (M5 x 10.7 + spring,
                     L_e min 7.294), FEA3D's drawn-basis A_n 68.4 kept as an information record) [CALC / DERIVED];
                     js5b (FA1U / FA1D / LC2, IN718) rows from results/v352/jfwd_js5b_rows_v352.json (lead 2026-10-21T03:30:46Z (1)); final envelope v6
  J-FD01 / J-FD09    results/v352/f4_v352.json (DERIVED hand calcs; HW-103 / HW-127 rows, host thread on TC-02 / GM-09)
usage: margin_matrix_v352.py -> results/v352/tables/margin_matrix_v352.{md,json}"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
JF = Path("/home/claude/work/fea3d/jfwd/runs")
OUTD = RES / "v352" / "tables"
STOPS = ["stop000", "stop045", "stop090", "stop135", "stop180", "stop225", "stop270", "stop315"]
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
BURN = ["B1_21.65", "B1_19", "B1_2", "B1_1"]
PARTS = ["TC-01", "TC-02", "TC-03", "TC-04", "TC-09", "NZ-01", "NZ-02", "NZ-03", "NZ-04", "FD-01", "GM-01", "GM-02", "GM-03", "GM-08a",
         "GM-08b", "GM-09", "GM-10", "GM-13", "GM-14", "GM-16a", "GM-16b", "PD-01R", "PD-01S"]
JOINT_ROWS = ["HW-101 (J-FWD)", "HW-103 (J-FD01)", "HW-127 (J-FD09)"]
CHANGED = {"TC-01", "TC-02", "TC-09", "GM-01", "GM-02", "FD-01", "NZ-01"}   # v3.5.2 changed parts with an FE body (NZ-06 = mass item)
# Mechanical's FINAL 03-cad v3.5.2 set (CHANGELOG 247, MANIFEST a94851ae4dc22cc4): changed vs v3.5.1 = these 11.  TC-03 (rev-4 seat
# details), FD-02 and FD-04 changed in CAD but not in this FE model (TC-03 = the v3.5.1 mesh, its seat region defers to Mechanical's rev-4
# S-AX contact sub-model; FD-02 / FD-04 have no FE body); ENG-TC-01's rev-5 d11.2 flats lie inside the global model's J-FWD connector
# regions (section 2.1).  Recorded in the output; no v3.5.1 value is carried in this matrix (every v3.5.2 source is present).
CAD_CHANGED_FINAL = ["FD-01", "FD-02", "FD-04", "GM-01", "GM-02", "NZ-01", "NZ-06", "TC-01", "TC-02", "TC-03", "TC-09"]
COLS = ["LC1", "LC2", "LC2F", "FA1Q", "FA1D", "FA1U", "FA1S", "FA1T", "LC3 cold", "LC3 hot bound", "GS", "TD", "LC6 F2", "F2 hot bound",
        "LC6 soak", "TB70", "TBS", "J-FWD", "J-FD01", "J-FD09"]
INFO_COLS = ["TS2 (info)", "TB70 SF1.0 (info)", "LC1 merged v351 map (info)"]
COL_DOC = {
    "LC1": "LC1 steady max thrust, SF 1.5 / 2.0, 4 burn states, GVLO + GVHI envelope (L1; rev 1 levers: no load path through the junction)",
    "LC2": "LC2 MEOP 4.5 MPa chamber + 7.0 MPa manifold + inertia, SF 1.5 / 2.0, 4 burn states, GVLO + GVHI envelope",
    "LC2F": "LC2F failure thrust 907.7 N at 9 cone poses, SF 1.0 / 1.5 (the case stays as published, 234 (2)): R3 cone posts; v3.5.1 c71 carried for unchanged parts until then",
    "FA1Q": "FA-1 94 bar abs (T <= 0.1 ms and 20-50 ms), SF 1.0", "FA1D": "FA-1 121 bar abs (0.1-1 ms), SF 1.0",
    "FA1U": "FA-1 147 bar abs (1-20 ms), SF 1.0", "FA1S": "FA-1 step bound 151.04 bar abs (every period), SF 1.0",
    "FA1T": "FA-1 thrust spike 3.6 kN (gimbal / mount parts), SF 1.0",
    "LC3 cold": "LC3 at the 8 stop poses (rev 3 levers at R3), cold, SF 1.5 / 2.0",
    "LC3 hot bound": "LC3 hot lower bound (DERIVED, sub-additivity, node-wise on the R3 base; GVLO / GVHI)",
    "GS": "F2 gimbal slew at 9 cone poses (R3)", "TD": "F2 touchdown TD at 9 cone poses (R3)", "LC6 F2": "F2 LC6 at 9 cone poses (R3)",
    "F2 hot bound": "F2 hot lower bound (DERIVED; GS + TD + LC6 increment on the hot base)",
    "LC6 soak": "global LC6 (10 g axial + 3 g lateral, unpressurised) at the soak states, SF 1.5 / 2.0 at temperature",
    "TB70": "LC-TB70 58.1 bar abs blocked + manifold, TB state, NOMINAL SF 1.5 / 2.0 (188 (9); lead 08:58Z)",
    "TBS": "LC-TB-S 63.1 bar abs blocked + manifold, TB state, ABNORMAL SF 1.0 / 1.5 (188 (9))",
    "J-FWD": "J-FWD joint: one-sector contact sub-model (FE, envelope over the histories) + Mechanical's hand checks (i)-(iii) and IN718 rows on the FE (231 (1), 234 (1)(b), 240 (3)-(10)); cell = minimum over the criterion rows (section 'J-FWD column rows')",
    "J-FD01": "J-FD01 HW-103 / 103B (F4 v352, DERIVED)", "J-FD09": "J-FD09 HW-127 (F4 v352, DERIVED)",
    "TS2 (info)": "TS2 post-landing soak, thermal only, SF 1.0 (information)",
    "TB70 SF1.0 (info)": "TB70 at SF 1.0 yield (line 106 criterion type; information under 188 (9))",
    "LC1 merged v351 map (info)": "LC1 on the v3.5.1 merged-node S-AX map (interim run lc1v352; both RM2-13 clearances closed = perfect-contact information; not the v3.5.2 NF2b field)",
}
# '-' cells: why a case is not evaluated for a part (14:49Z; rendered under the matrix)
NOT_EVAL = {
    "FA1T": "evaluated on the gimbal / mount parts only (post_f1 GIMBAL_PARTS: GM-01, GM-02, GM-03, GM-08a/b, GM-09, GM-10, GM-13, GM-14, "
            "GM-16a/b): the thrust spike counts only for parts with T <= 20 ms (lead 194); the pressure parts are bounded by FA1Q / D / U / S",
    "LC2F": "evaluated on the gimbal / mount parts only (post_s3d GIMBAL_PARTS; the pressure parts are not at a defined Pc in this case), as "
            "published for v3.5.1 (234 (2))",
    "J-FWD": "only TC-01, TC-02 and the HW-101 screw are in the J-FWD sub-model; the global TC-01 / TC-02 cells at the J-FWD connectors "
             "(z >= 97.5) defer to this column (NAMED rules)",
    "J-FD01": "F4 joint: the HW-103 / 103B screws and the TC-02 host thread only",
    "J-FD09": "F4 joint: the HW-127 screws and the GM-09 host thread only",
    "joint rows": "HW-101 / HW-103 / HW-127 are connectors in the global model (no FE body): their rows sit in the joint columns only",
}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(name):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None


_C71 = None


def c71cls(run, node):
    global _C71
    if _C71 is None:
        _C71 = load("v352/c71_allnode_classes.json") or {"runs": {}}
    r = _C71["runs"].get(run) or {}
    return (r.get("classes") or {}).get(str(node))


def margins_of(post, cases, states=None):
    """margin records of a post JSON (f1 state posts, LC3 pose posts, s3d pose posts) for the given case ids."""
    out = []
    if post is None:
        return out
    if "states" in post:
        for s, v in post["states"].items():
            if states and s not in states:
                continue
            for c, cv in v.get("cases", {}).items():
                if c in cases:
                    out += [dict(m, state=m.get("state", s)) for m in cv.get("margins", [])]
    elif isinstance(post.get("cases"), dict) and any(c in post["cases"] for c in cases):
        for c, cv in post["cases"].items():
            if c in cases and isinstance(cv, dict):
                out += cv.get("margins", [])
    elif "margins" in post:
        out += [m for m in post["margins"] if m.get("case") in cases]
    return out


def tag(recs, label, run=None, carried=False):
    out = []
    for m in recs:
        m = dict(m)
        m["_src"] = label
        m["_carried"] = carried
        if m.get("set") == "all" and m.get("node_class") is None and run:
            c = c71cls(run, m.get("node"))
            if c:
                m.update(node_class=c["class"], node_class_detail=c["detail"], d_class_mm=c["d_mm"], _class_rule="brep60, re-classified on the v3.5.1 model")
        if carried and m.get("set") == "regular":
            m["_regular_rule"] = "mesh30 (v3.5.1 as published)"
        out.append(m)
    return out


_HBS = None
HBS_FILE = "v352/hb_singular_check_v352.json"


def hbs_rows():
    """results/v352/hb_singular_check_v352.json rows keyed (case, base, state, part)."""
    global _HBS
    if _HBS is None:
        d = load(HBS_FILE) or {"rows": []}
        _HBS = {(r["case"], r["base"], r["state"], r["part"]): r for r in d["rows"]}
    return _HBS


_PW = None
PW_FILE = "v352/hb_partwide_v352.json"
HOTCASE = {"LC3 hot bound": "LC3", "F2 hot bound": "F2"}
PW_METHOD = ("part-wide singular-node bound 1 / (1 / (1 + MS_min) + SF delta / a_min) - 1 over every node of the part (delta = all-node "
             "minus regular maximum of the part's increment envelope, a_min = its lowest allowable at the state; DERIVED; lead 21:47:29Z)")


def pw_cells():
    """results/v352/hb_partwide_v352.json per (case, part): unrounded part-wide minimum per slot with its row, and the stored minimum."""
    global _PW
    if _PW is None:
        d = load(PW_FILE) or {"per_part_case": {}}
        _PW = {tuple(k.split("|", 1)): o for k, o in d["per_part_case"].items()}
    return _PW


def bound_recs(d, label, carried=False, case=None, base=None):
    """hot-bound rows (lc3_bound.py) -> margin-like records.  An all-node row on lc3_bound's part-max branch takes min(stored, node-wise
    at the stored node) of hb_singular_check_v352 (case 'LC3' / 'F2', base 'GVLO' / 'GVHI'); the stored values go with it."""
    out = []
    if d is None:
        return out
    H = hbs_rows() if case and base else {}
    for st, rows in d["states"].items():
        for r in rows:
            m = {"part": r["part"], "set": r["set"], "state": st, "MS": r["MS_bound"], "MS_ult": r.get("MS_ult_bound"),
                 "node": r.get("node"), "node_class": r.get("node_class") or ("regular" if r["set"] == "regular" else None),
                 "node_class_detail": r.get("node_class_detail"), "d_class_mm": r.get("d_class_mm"), "T_C": r.get("T_C"),
                 "r_theta_z": r.get("r_theta_z"), "vm_MPa": None, "_src": label, "_carried": carried, "method": r.get("method")}
            h = H.get((case, base, st, r["part"]))
            if h and r["set"] == "all" and "part-max" in (r.get("method") or "") and h.get("node") == r.get("node"):
                an = h["at_node_MS"]
                lw = h.get("at_node_lowered") or [False, False]
                an = [a_ if l_ else b_ for a_, b_, l_ in zip(an, (r["MS_bound"], r.get("MS_ult_bound")), lw)]
                low = any(lw)
                m["_singular"] = {"stored_MS": [r["MS_bound"], r.get("MS_ult_bound")], "at_node_MS": an, "lowered": bool(low),
                                  "node_increment_MPa": h.get("node_increment", h.get("node_excess_MPa")), "reg_max_MPa": h.get("reg_max"),
                                  "part_wide_bound_MS": h.get("corrected_all_node_MS"), "delta_MPa": h.get("delta"), "file": HBS_FILE}
                if low:
                    m["MS"] = an[0] if isnum(an[0]) else m["MS"]
                    m["MS_ult"] = an[1] if isnum(an[1]) else m["MS_ult"]
                    m["_src"] = f"{label} (node-wise at n{r.get('node')}, hb_singular_check)"
            out.append(m)
    return out


_LB = None


def lever_bound(recs, pose, case):
    """lead 12:28Z (5): a GM-01 / GM-02 lever-root record whose R2 -> R3 change exceeds 5 % takes the p = 1 bound of
    lever_root_bound_v352.py (DERIVED, order ASSUMED, no R4 run); the R2 / R3 values go with it.  Matched on pose, case, part, set and
    the R3 peak node."""
    global _LB
    if _LB is None:
        _LB = load("v352/lever_root_bound_v352.json") or {"cells": []}
    cells = {(c["pose"], c["case"], c["part"], c["set"]): c for c in _LB.get("cells", [])}
    out = []
    for m in recs:
        c = cells.get((pose, case, m.get("part"), m.get("set")))
        if c and m.get("node") == c["R3_node"]:
            ratio = c["vm_MPa"] / c["R3_MPa"] if c.get("R3_MPa") else 1.0     # the bound scales the peak stress; MS + 1 ~ 1 / vm
            sc = lambda v: (round((1.0 + v) / ratio - 1.0, 4) if isnum(v) else v)
            m = dict(m, MS=c["MS_y"], MS_ult=c["MS_u"], vm_MPa=c["vm_MPa"], _src=f"{m.get('_src')} (p = 1 bound on R2 -> R3)",
                     MS_primary_only=sc(m.get("MS_primary_only")), MS_PQ_nodal_shakedown=sc(m.get("MS_PQ_nodal_shakedown")),
                     _lever_bound={"R2_MPa": c["R2_MPa"], "R3_MPa": c["R3_MPa"], "change": c["change"], "bound_MPa": c["vm_MPa"],
                                   "MS_R3": [round(m["MS"], 3), round(m["MS_ult"], 3)],
                                   "tag": "DERIVED; order ASSUMED; R2 -> R3 > 5 %; lead 12:28Z (5)"})
        out.append(m)
    return out


def lever_hot_recs(kind):
    """GM-01 / GM-02 hot cells per pose from the item-1 lever-root table (ACCEPTED lead 20:44:07Z (1)): the hot bound with the p = 1
    increment where the R2 -> R3 change of the pose's cold cell exceeds 5 % (lead 12:28Z (5); DERIVED, order ASSUMED, no R4); elsewhere
    the hot bound itself (the table's per-pose minimum reproduces the hb3 envelope exactly).  The 10 unruled R2-checked-node rows of
    the table are information and are not used."""
    d = load("v352/lever_root_table_v352.json")
    if d is None:
        return []
    out = []
    for r in d["rows"]:
        if r.get("kind") != kind or r.get("part") not in ("GM-01", "GM-02"):
            continue
        hc = r.get("hot_cell") or {}
        if not isnum(hc.get("MS_y")):
            continue
        p1 = r.get("hot_p1") if isinstance(r.get("hot_p1"), dict) and isnum((r.get("hot_p1") or {}).get("MS_bound")) else None
        h = p1 or r.get("hot") or {}       # the p = 1 record carries its own node / base / state / vm_bound (= the cell)
        out.append({"part": r["part"], "set": r["set"], "state": f"{h.get('base')} {h.get('state')}", "MS": hc["MS_y"], "MS_ult": hc.get("MS_u"),
                    "node": h.get("node"), "node_class": h.get("node_class") or ("regular" if r["set"] == "regular" else None),
                    "node_class_detail": h.get("node_class_detail"), "d_class_mm": h.get("d_class_mm"), "T_C": h.get("T_C"),
                    "r_theta_z": h.get("r_theta_z"), "vm_MPa": h.get("vm_bound_MPa"), "added_p1_MPa": h.get("added_p1_MPa") if p1 else 0.0,
                    "_src": f"lever-root table {r['pose']} ({hc.get('rule')}; {hc.get('tag')})", "_carried": False,
                    "method": hc.get("rule"), "pose": r["pose"]})
    return out


# ============================================================================================ sources per column
def sources():
    S = {c: {"srcs": [], "carried": [], "pending": [], "files": []} for c in COLS + INFO_COLS}

    def add(col, label, recs, fn, carried=False):
        (S[col]["carried"] if carried else S[col]["srcs"]).append((label, recs))
        if fn not in S[col]["files"]:
            S[col]["files"].append(fn)

    for run, b, soak in (("lc1v352g", "GVLO", ["B1_51.7", "B1_70.7"]), ("lc1v352h", "GVHI", ["B1_43.7", "B1_70.7"])):
        fn = f"f1_post_{run}.json"
        d = load(fn)
        if d is None:
            for col in ("LC1", "LC2", "LC6 soak", "TS2 (info)"):
                S[col]["pending"].append(f"{run} ({b})")
            continue
        add("LC1", f"{b}", tag(margins_of(d, {"LC1"}, BURN), b), fn)
        add("LC2", f"{b}", tag(margins_of(d, {"LC2"}, BURN), b), fn)
        add("LC6 soak", f"{b}", tag(margins_of(d, {"LC6"}, soak), b), fn)
        add("TS2 (info)", f"{b}", tag(margins_of(d, {"TS2"}, soak), b), fn)
    for run, b in (("soak352g", "GVLO"), ("soak352h", "GVHI")):
        fn = f"f1_post_{run}.json"
        d = load(fn)
        if d is None:
            S["TS2 (info)"]["pending"].append(f"{run} ({b})")
        else:
            add("TS2 (info)", f"{run} {b}", tag(margins_of(d, {"TS2"}), f"{run} {b}"), fn)
    d = load("f1_post_lc1v352.json")
    if d is not None:
        add("LC1 merged v351 map (info)", "v351 merged map", tag(margins_of(d, {"LC1"}, BURN), "v351 merged map"), "f1_post_lc1v352.json")
    d = load("f1_post_fa1v352n.json")
    for col in ("FA1Q", "FA1D", "FA1U", "FA1S", "FA1T"):
        if d is None:
            S[col]["pending"].append("fa1v352n")
        else:
            add(col, "fa1v352n", tag(margins_of(d, {col}), "fa1v352n"), "f1_post_fa1v352n.json")
    for s in STOPS:
        fn = f"f1_post_lc3_pose_{s}_v352r3R3.json"
        d = load(fn)
        if d is not None:
            add("LC3 cold", f"{s} R3", lever_bound(tag(margins_of(d, {"LC3"}), f"{s} R3"), s, "LC3"), fn)
        else:
            S["LC3 cold"]["pending"].append(f"{s} R3")
            fc = f"f1_post_lc3_pose_{s}_c71.json"
            dc = load(fc)
            if dc is not None:
                add("LC3 cold", f"{s} c71", tag(margins_of(dc, {"LC3"}), f"{s} c71", run=f"pose_{s}_c71", carried=True), fc, carried=True)
    # LC2F (14:49Z): the case stays as published (234 (2)); its v3.5.2 values come from the R3 cone posts like GS / TD / LC6 F2 (changed
    # parts need the v3.5.2 geometry); until a cone's R3 post lands the v3.5.1 c71 value is carried for the unchanged parts only.
    for col, case in (("GS", "GS"), ("TD", "TD"), ("LC6 F2", "LC6"), ("LC2F", "LC2F")):
        for c in CONES:
            fn = f"s3d_pose_{c}_v352r3R3.json"
            d = load(fn)
            if d is not None:
                add(col, f"{c} R3", lever_bound(tag(margins_of(d, {case}), f"{c} R3"), c, case), fn)
            else:
                S[col]["pending"].append(f"{c} R3")
                fc = f"s3d_pose_{c}_c71.json"
                dc = load(fc)
                if dc is not None:
                    add(col, f"{c} c71", tag(margins_of(dc, {case}), f"{c} c71", run=f"pose_{c}_c71", carried=True), fc, carried=True)
    for col, pfx, old in (("LC3 hot bound", "f1_lc3_hot_bound_v352", "f1_lc3_hot_bound_c71.json"),
                          ("F2 hot bound", "f1_lc3_hot_bound_s3d_v352", "f1_lc3_hot_bound_s3d.json")):
        got = 0
        for sfx, b in (("g3", "GVLO"), ("h3", "GVHI")):
            fn = f"{pfx}{sfx}.json"
            d = load(fn)
            if d is not None:
                add(col, f"{b} R3 base", bound_recs(d, f"{b} R3 base", case=("LC3" if col == "LC3 hot bound" else "F2"), base=b), fn)
                for xf in (HBS_FILE, PW_FILE):
                    if load(xf) is not None and xf not in S[col]["files"]:
                        S[col]["files"].append(xf)
                got += 1
            else:
                S[col]["pending"].append(f"{pfx}{sfx}")
        if got < 2:
            d = load(old)
            if d is not None:
                add(col, "v3.5.1 bound", bound_recs(d, "v3.5.1 bound", carried=True), old, carried=True)
        lt = lever_hot_recs("stops" if col == "LC3 hot bound" else "cones")
        if lt:
            add(col, "lever-root table (hot + p = 1)", lt, "v352/lever_root_table_v352.json")
    for run, b in (("tb352g", "GVLO"), ("tb352h", "GVHI")):
        fn = f"f1_post_{run}.json"
        d = load(fn)
        if d is None:
            for col in ("TB70", "TBS", "TB70 SF1.0 (info)"):
                S[col]["pending"].append(run)
            continue
        add("TB70", b, tag(margins_of(d, {"TB70"}), b), fn)
        add("TBS", b, tag(margins_of(d, {"TBS"}), b), fn)
        r1 = []
        for m in tag(margins_of(d, {"TB70"}), b):
            m = dict(m)
            m["MS"] = (1.0 + m["MS"]) * m.get("SF_y", 1.5) - 1.0 if m.get("MS") is not None else None
            m["MS_ult"] = None
            r1.append(m)
        add("TB70 SF1.0 (info)", b, r1, fn)
    return S


# ============================================================================================ rulings
def z_of(m):
    rtz = m.get("r_theta_z") or [None, None, None]
    return rtz[2] if rtz[2] is not None else -1e9


def r_of(m):
    rtz = m.get("r_theta_z") or [None, None, None]
    return rtz[0] if rtz[0] is not None else 1e9


def seat_region(m):
    """TC-02 / TC-03 seat region (TC-02 seat bore r 7.0 z 107.5, TC-03 flange r <= 10.1): r <= 12 and z < 125; excludes the J-FD01
    tie patches on the TC-02 x -29.5 flat (r ~31.75, z 146.5-165.5) and the J-FWD region."""
    return r_of(m) <= 12.0 and z_of(m) < 125.0


# named sub-model / contact FE that replaces an idealisation class (234 (4)); (part, class_detail, predicate) -> (text, reference)
NAMED = [
    ("TC-01", "rbe3_couplings", lambda m: z_of(m) >= 97.5,
     "J-FWD connector RBE3: the J-FWD one-sector contact sub-model governs TC-01 at z >= 97.5 (J-FWD column)", "lead 07:51Z (c)/(d)"),
    ("TC-02", "rbe3_couplings", lambda m: z_of(m) >= 97.5,
     "J-FWD connector RBE3 on TC-02: the J-FWD contact sub-model (TC-02 thread / band cells, J-FWD column)", "lead 07:21Z (4), 07:51Z (d)"),
    ("TC-02", "tie_patch_edges", seat_region,
     "TC-02 / TC-03 seat-region tie edge: Mechanical's S-AX v352r4 contact sub-model (rev 4 seat) and the T-F2 contact runs", "lead 05:42Z, 07:51Z (b), 08:40Z (2)"),
    ("TC-03", "tie_patch_edges", seat_region,
     "TC-03 seat / thread tie edge: Mechanical's S-AX v352r4 contact sub-model and the T-F2 contact runs", "lead 05:42Z, 07:51Z (a), 08:40Z (2)"),
    ("NZ-01", "tie_patch_edges", None, "NZ-01 / NZ-03 shoulder and foil interface: Mechanical S-AX v352_NF2b", "lead 05:45Z, 07:51Z (f)"),
    ("NZ-03", "tie_patch_edges", None, "NZ-01 / NZ-03 shoulder and foil interface: Mechanical S-AX v352_NF2b (188 (3) contact FE + N-F1)", "lead 05:45Z, 07:51Z (f)"),
    ("PD-01R", "rigid_connectors", None, "PD-02 modelled rigid (same alloy AL6061-T6, BOM_v3.5.2): the thermal mismatch at the rigid connector is a model artefact (MF)", "lead 07:51Z (e), 08:04Z"),
    ("PD-01S", "rigid_connectors", None, "PD-02 modelled rigid (same alloy AL6061-T6, BOM_v3.5.2): the thermal mismatch at the rigid connector is a model artefact (MF)", "lead 07:51Z (e), 08:04Z"),
]

# classes of negative cells: (part, column or '*') -> (class, closure text, reference).  Column-specific entries win.
CLASS_RULES = {
    ("NZ-01", "*"): ("BR", "brittle and thermal: 183 (2) capture / containment shown + test basis, else design change", "REV-MECH-2 rows 8-10"),
    ("NZ-03", "*"): ("CH", "char primary vs the ASSUMED 20 MPa: N-F1 (>= 21.96 MPa inside the 23.7 MPa acceptance); tie edge 188 (3) contact FE + N-F1", "REV-MECH-2 LC2 table"),
    ("TC-03", "*"): ("TS-183", "thermal-secondary 183 (1): (a) primary and (b) P+Q pass; (c) LCF and (d) GlidCop time at temperature with Mechanical; MF on the value (gap-variant field, RM2-13)", "REV-MECH-2 rows 5-7; lead 07:51Z (a), 08:58Z"),
    ("TC-02", "*"): ("TS-212", "TC-02 under 212 (1): (a)-(c) pass; (d) time at temperature open with T-F1 (Mechanical's (b) package)", "REV-MECH-2 rows 2-4; lead 08:58Z, 09:15Z (3)"),
    ("FD-01", "*"): ("TS-183", "thermal-secondary 183 (1), all-node value at the FD01_TC02_screws bonded-patch edge kept in the cell (234 (4): no named sub-model): (a) primary and (b) P+Q <= 2 Fty(T) pass; (c) LCF with Mechanical; (d) passes on the sourced long-time allowable where T <= 150 C, otherwise to T-F1 (node T in the row)", "lead 08:58Z, 09:47Z (6)"),
    ("PD-01R", "*"): ("MF", "PD-02 rigid in the model (same alloy): the PD-01 / PD-02 mismatch is a model artefact; primary-only > +20", "lead 07:51Z (e), 08:04Z"),
    ("PD-01S", "*"): ("MF", "PD-02 rigid in the model (same alloy): the PD-01 / PD-02 mismatch is a model artefact; primary-only > +20", "lead 07:51Z (e), 08:04Z"),
    ("TC-01", "LC6 soak"): ("TS-183", "thermal-secondary (provisional, lead 08:04Z); in the J-FWD region (z >= 97.5) the J-FWD sub-model governs: js5 soak P+Q <= 2 Fty(T) rows (J-FWD column)", "lead 07:51Z (d), 08:04Z, 08:40Z"),
    ("TC-01", "TB70"): ("MF", "n9090 1.05 mm from the J-FWD RBE3: connector artefact, closed by the J-FWD sub-model (FA1S / LC2 bound the primary)", "lead 08:58Z"),
    ("TC-01", "TBS"): ("MF", "J-FWD connector: closed by the J-FWD sub-model", "lead 08:58Z"),
    ("TC-01", "J-FWD"): ("DC", "TC-01 seat / ring line P+Q (secondary, shakedown, P+Q <= 2 Fty(T)) FOUND NEGATIVE on the worst computed instance "
                         "of the FINAL envelope v6 (lead 02:01:34Z (E), 03:30:46Z (3), 05:17:36Z (3): sharp js5 / (a) / (a') / (a'') + (b2) "
                         "R0.2 incl. its repeats + (b1) s9 mu 0.2 R0.2 incl. its repeats, seat lines at C1 + (b2') s9 mu 0 + cD's resultants; "
                         "cD's seat lines per the 02:01:34Z (C) rule: s6 + C1 stand; "
                         "not a proven bound): {rows}. R0.2 bore-side "
                         "break adopted (240 (5)); route (i) adopted (HW-170 disc spring under the head, lead 16:53Z R2; rev-5 CAD check accepted "
                         "17:55:55Z); J-F1 maximum capped at 3750 N (lead 17:56:12Z). (b1) at C1 is negative (SOAK52 -0.030), so the 240 (10) "
                         "seat-line P+Q select-fit band APPLIES (IN718 [0.040, 0.0761] mm radial, as a narrower TC-02 spigot OD tolerance); it is "
                         "re-sized ONCE by Mechanical on the final envelope from the FEA3D P+Q-vs-radial-gap sensitivity [DERIVED, "
                         "existing runs, no new run]; if no band inside [0.040, 0.0761] closes it, the seat-line P+Q stays a found negative in the "
                         "datasheet; the governing minimum on the final envelope is SOAK -0.071 ((b2) rep); owner Mechanical",
                         "240 (9)(i), (10); lead 13:14Z, 15:37Z (R1) / (R3), 16:53Z R2, 17:56:12Z, 2026-10-21T00:39:30Z (1) / (4), 01:30:18Z (3) / (5), 02:01:34Z (C) / (E), 05:17:36Z (1) / (3)"),
    ("HW-101 (J-FWD)", "J-FWD"): ("DC", "J-FWD screw = ENG-HW-101-IN718 (240 (4); A4-80 withdrawn) on route (i) (M5 x 10.7 + HW-170 spring, lead 16:53Z R2): "
                                  "FA1S 5020A Eq. 22 preload omitted, soak 234 (1)(b) tension; LC2 from js5b (lead 2026-10-21T03:30:46Z (1)): {rows}", "240 (3), (4); lead 16:53Z R2; lead 2026-10-21T03:30:46Z (1)"),
    ("TC-02", "J-FWD"): ("DC", "TC-02 thread shear (IN718 soak force) on THE ROW (route (i), A_n 67.93): {rows}; fixes per 240 (10) / Mechanical v7 "
                         "(J-F1 maximum capped at 3750 N, length, insert)", "240 (10); lead 13:14Z, 16:53Z R2, 17:56:12Z"),
    # 2026-10-20 (written between the 21:28:05Z and 21:35:34Z date -u readings): lead 21:15:29Z (3) APPROVED MF for TC-01 FA1U / FA1S at n9090
    # under 234 (4), on the 239 TB70 basis for this node; conditions (a)-(d) are built into the closure in build() ('{mf}').
    ("TC-01", "FA1U"): ("MF", "{mf}", "lead 21:15:29Z (3) under 234 (4); basis as the 239 TB70 ruling (lines 231 (3), 239)"),
    ("TC-01", "FA1S"): ("MF", "{mf}", "lead 21:15:29Z (3) under 234 (4); basis as the 239 TB70 ruling (lines 231 (3), 239)"),
    # lead 21:15:29Z (4): TC-04 LC3 / F2 hot bound at n42993 is NOT an exception under 234 (4) (a bad tet is a discretisation defect, refinement
    # convergence not shown): the all-node value is the cell, class BT; details built in build() ('{bt}').
    ("TC-04", "LC3 hot bound"): ("BT", "{bt}", "lead 21:15:29Z (4)"),
    ("TC-04", "F2 hot bound"): ("BT", "{bt}", "lead 21:15:29Z (4)"),
}


def ruling_named(part, m):
    if m is None:
        return None
    det = m.get("node_class_detail")
    for p, d, pred, text, ref in NAMED:
        if p == part and d == det and (pred is None or pred(m)):
            return text, ref
    return None


def neg_class(part, col):
    return CLASS_RULES.get((part, col)) or CLASS_RULES.get((part, "*"))


# ============================================================================================ cells
def isnum(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def where(m):
    if m is None:
        return None
    return {"state": m.get("state"), "node": m.get("node"), "class": m.get("node_class"), "class_detail": m.get("node_class_detail"),
            "d_class_mm": m.get("d_class_mm"), "vm_MPa": round(m["vm_MPa"], 1) if isnum(m.get("vm_MPa")) else None,
            "T_C": round(m["T_C"], 1) if isnum(m.get("T_C")) else None, "r_theta_z": m.get("r_theta_z"), "src": m.get("_src"),
            "carried_v351": bool(m.get("_carried")), "class_rule": m.get("_class_rule"),
            "MS_primary_only": round(m["MS_primary_only"], 3) if isnum(m.get("MS_primary_only")) else None,
            "MS_PQ_nodal": round(m["MS_PQ_nodal_shakedown"], 3) if isnum(m.get("MS_PQ_nodal_shakedown")) else None,
            "lever_bound": m.get("_lever_bound"), "singular_check": m.get("_singular"), "part_wide": m.get("_part_wide")}


def minrec(recs, part, sset, key):
    c = [m for m in recs if m.get("part") == part and m.get("set") == sset and isnum(m.get(key))]
    return min(c, key=lambda m: m[key]) if c else None


def cell(part, col, S):
    src = S[col]["srcs"]
    car = S[col]["carried"] if part not in CHANGED else []
    recs = [m for _, rr in src for m in rr] + [m for _, rr in car for m in rr]
    out = {"regular": {}, "all": {}, "value": [None, None], "basis": [None, None], "class": None, "closure": None, "ref": None,
           "carried_v351": False, "pending": list(S[col]["pending"]) if S[col]["pending"] else [], "files": S[col]["files"]}
    if part in CHANGED and S[col]["carried"] and S[col]["pending"]:
        out["note"] = "changed part: v3.5.1 values not carried; v3.5.2 sources pending"
    pw = pw_cells().get((HOTCASE[col], part)) if col in HOTCASE else None
    for j, key in enumerate(("MS", "MS_ult")):
        r = minrec(recs, part, "regular", key)
        a = minrec(recs, part, "all", key)
        k = "y" if key == "MS" else "u"
        pv = (pw.get("pw_min") or [None, None])[j] if pw else None
        if a is not None and isnum(pv) and round(pv, 3) < round(a[key], 3):
            # lead 21:47:29Z: the rigorous part-wide bound replaces the all-node value (stored, or node-wise where that lowered it)
            # wherever it is lower at 3 decimals; the stored value goes beside it
            a = dict(a)
            a["_part_wide"] = {"MS": pv, "stored_MS": a[key], "stored_node": a.get("node"), "stored_state": a.get("state"),
                               "stored_class": f"{a.get('node_class')} {a.get('node_class_detail') or ''}".strip(), "stored_src": a.get("_src"),
                               "pw_row": (pw.get("pw_at") or [None, None])[j], "delta_max_MPa": pw.get("delta_max_MPa"), "method": PW_METHOD,
                               "file": PW_FILE}
            a[key] = pv
            a["_src"] = f"{a.get('_src')} (part-wide bound, hb_partwide_v352)"
            out.setdefault("part_wide_stored", [None, None])[j] = round(a["_part_wide"]["stored_MS"], 3)
        out["regular"][k] = {"MS": round(r[key], 3), **where(r)} if r else None
        out["all"][k] = {"MS": round(a[key], 3), **where(a)} if a else None
        if r is None and a is None:
            continue
        if a is None or (r is not None and a[key] >= r[key] - 1e-9):
            out["value"][j] = round(r[key], 3)
            out["basis"][j] = "all-node minimum at a regular node (= regular value)"
        elif r is None:
            out["value"][j] = round(a[key], 3)
            out["basis"][j] = "all-node (no regular-set record)"
        else:
            nm = ruling_named(part, a)
            pwr = a.get("_part_wide")
            if nm:
                out["value"][j] = round(r[key], 3)
                out["basis"][j] = f"regular stands: all-node at {a.get('node_class')} {a.get('node_class_detail')} -> {nm[0]} ({nm[1]})"
                if pwr:
                    out["part_wide_info"] = True
                    out["basis"][j] += (f"; all-node information value = the part-wide bound {f(pwr['MS'])} (stored {f(pwr['stored_MS'])} at "
                                        f"n{pwr['stored_node']} beside it; hb_partwide_v352, lead 21:47:29Z)")
            elif pwr:
                out["value"][j] = round(a[key], 3)
                out["part_wide_cell"] = True
                out["basis"][j] = (f"all-node value (234 (4)) = the {PW_METHOD}: {f(pwr['MS'])}, below the stored all-node {f(pwr['stored_MS'])} "
                                   f"(n{pwr['stored_node']}, {pwr['stored_state']}, {pwr['stored_class']}) at 3 decimals; row {pwr['pw_row']} (hb_partwide_v352)")
            else:
                out["value"][j] = round(a[key], 3)
                out["basis"][j] = f"all-node value (234 (4)): {a.get('node_class')} {a.get('node_class_detail') or ''} not replaced by a named sub-model"
                if (a.get("_singular") or {}).get("lowered"):
                    out["singular_lowered"] = True
                    out["basis"][j] += f" (lowered to the node-wise bound at n{a.get('node')}: hb_singular_check_v352)"
        if (r is not None and r.get("_carried")) or (a is not None and a.get("_carried")):
            out["carried_v351"] = True
    vals = [v for v in out["value"] if isnum(v)]
    if vals and min(vals) < 0:
        c = neg_class(part, col)
        if c is None and out["carried_v351"] and out["pending"]:
            # 14:55Z: a carried v3.5.1 record (unchanged part) whose v3.5.2 source is pending and which has no node class (the v3.5.1
            # bound rows carried none): not classified here; it is re-classified when the v3.5.2 source lands
            g = (out["all"].get("u") if isnum(out["value"][1]) and out["value"][1] < 0 else out["all"].get("y")) or {}
            c = ("UNCLASSIFIED (pending)", f"carried v3.5.1 all-node record without a node class (r, theta, z {g.get('r_theta_z')}, state "
                 f"{g.get('state')}); re-classified on the v3.5.2 source when it lands ({', '.join(out['pending'])})", None)
        out["class"], out["closure"], out["ref"] = (c if c else ("UNCLASSIFIED", "to the lead", None))
    return out


# ============================================================================================ J-FWD / F4 columns
MECH = Path("/home/claude/work/shared-fallback/engine/04-fea/v352")
# Mechanical: IN718 rows mapped onto the FEA3D envelope (CALC / DERIVED; read-only).  v5 (A_ROW 38.171 mm2 flat-bearing basis, lead 14:14Z
# rows v4 (a); Mechanical 15:27Z) is used once published in 04-fea/v352; until then v4.  The output records the file and its sha16.
MECH_IN718 = next((MECH / f for f in ("jfwd_in718_rows_v352_v7.json", "jfwd_in718_rows_v352_v6.json", "jfwd_in718_rows_v352_v5.json",
                                       "jfwd_in718_rows_v352_v4.json") if (MECH / f).exists()), MECH / "jfwd_in718_rows_v352_v4.json")
# 2026-10-20 (written between the 20:55:18Z and 21:01:31Z date -u readings): v7 (hub publication CHANGELOG 246, 04-fea/v352 MANIFEST 04a357d05c26a609 row 107, sha16 6113d28b64d0dba5)
MECH_FIX = MECH / "jfwd_fix_v352_v2.json"            # Mechanical: FA1S hand checks (i)-(iii) + 5020A Eq. 22, IN718 option (240 (3)-(5))
JF_ENV = RES / "v352" / "jfwd_soak_envelope_v352_v6.json"   # FEA3D soak envelope v6 = FINAL (lead 2026-10-21T02:01:34Z (E), 05:17:36Z (3))
#   (FEA3D-2 final re-run: v4 9d9fd8ee991f9887 ADOPTED 00:39:30Z (1) is the superseded record; v5 = v4 + (b2') + (b1) seat lines at C1;
#   v6 = v5 + cD's resultants (cD moved the SOAK70 window max, the FA1S N min / window min; seat lines per (C): s6 + C1 stand);
#   v5 ef22b59cf2413b46 (ACCEPTED 03:30:46Z (3) unless cD moves a quantity) = superseded record; its table = results/v352/records/
#   margin_matrix_v352_5568033c68742a65.md / _a53b309c5d7e1f55.json, script scripts/records/margin_matrix_v352_79d3605788f134d9.py)
#   (switched from v3 by FEA3D-2 after the 00:49:38Z date -u reading): js5 / (a) / (a') / (a'') sharp + (b2) R0.2 incl. SOAK_rep / SOAK52_rep
#   + (b1) s9 mu 0.2 R0.2 incl. its repeats.  v3 jfwd_soak_envelope_v352_v3.json 0872de4ea7e3601d (ADOPTED 15:37Z (R1)) = superseded record;
#   v2 jfwd_soak_envelope_v352.json 336568296bdb896f = superseded sharp-only record (lead 13:14Z).  v6 = final after cD.
JF_ENV_ADOPTED = ("FINAL v6: lead 2026-10-21T05:17:36Z (3) (cD moved envelope quantities; rule 02:01:34Z (E), 03:30:46Z (3)); "
                  "supersedes v5 ef22b59cf2413b46")
ENV_BASIS = ("worst of the computed histories and edge forms (sharp, R0.2); the contact solution depends on the predecessor state, so this "
             "is the worst computed instance, not a proven bound")
JF_CELLS = JF / "js5_mu0_T3750_g078" / "cells_v352An.json"
A_N, A_N_MECH = 68.4, 63.48        # mm2: drawn M5 x 10.2 basis (lead 13:14Z) / Mechanical's row basis (v3.5.1 L_eff 6.35)
JFWD_PENDING = ["Mechanical's single IN718 re-map and the select-fit band re-size on the final envelope (lead 00:39:30Z (1), (4)); "
                "Eq. 22 at V 4079.2 N (FE (b1)) and M 4354.7 N mm (CALC) in that re-map (lead 01:30:18Z (6))"]
# cD (lead 02:01:34Z (C)) DONE 05:11:29Z: s6 + C1 stand on the seat lines; its resultants moved envelope quantities -> v6 (05:17:36Z (3));
# this table is the one re-run on v6 (03:30:46Z (5), the second and last).
# (b1) s9 mu 0.2 POSTED 00:30:31Z: its instances are in the adopted envelope v4 (no longer pending; lead 00:39:30Z (1)).
# js5b rows (lead 2026-10-21T03:30:46Z (1)): per state, which members' rows are criterion rows and which slots (yield, ultimate) they fill.
JS5B_TREAT = {'FA1U': {'parts': True, 'screw': False, 'slots': [1, 1]}, 'FA1D': {'parts': True, 'screw': False, 'slots': [1, 1]}, 'LC2Y': {'parts': True, 'screw': False, 'slots': [1, 0]}, 'LC2U': {'parts': True, 'screw': False, 'slots': [0, 1]}, 'LC2N': {'parts': False, 'screw': True, 'slots': [1, 1]}, 'LC2M': {'parts': False, 'screw': True, 'slots': [1, 1]}}


def _r(state, row, y, u, src, tag, info=False, crit=None, note=None, preload=None):
    return {"state": state, "row": row, "MS_y": round(y, 3) if isnum(y) else None, "MS_u": round(u, 3) if isnum(u) else None,
            "src": src, "tag": tag, "info": info, "criterion": crit, "note": note, "preload_N": preload}


def jfwd_cells():
    """J-FWD column (rewritten 2026-10-20 14:49Z (date -u); brief item 7 J-FWD column; 231 (1) (i)-(iii), 234 (1)(b), 240 (3)-(10), lead 13:14Z).

    Rows per member; the cell is the minimum over the non-information rows (yield and ultimate slots separately; strain-based and
    P+Q margins sit in the yield slot).  Sources:
      FE      js5 (s5, sharp hole edges, mu 0, 3750 N, fit 0.078; A4-80 screw properties) cells_v352An.json (thread rows on A_n 68.4,
              tap bearing on L_e 6.84), and the soak envelope over js5 / (a) / (a') / (a'') (240 (9)(i)): seat-line P+Q minimum per
              state, and the thread shear at the envelope screw force [SIM / DERIVED].
      CALC    Mechanical jfwd_fix_v352_v2.json, IN718 option: FA1S hand checks at the drawing-limit wall (hole bearing, shear-out, net
              section, ligament Pm+Pb; hole-edge Neuber = Mechanical's information row), TC-02 tap bearing and thread shear, and the
              screw 5020A Eq. 22 (preload omitted = criterion; included = information) + direct shear on the minor area (240 (3)-(5)).
      IN718   Mechanical jfwd_in718_rows_v352_v4.json: the flight screw (240 (4)) mapped onto the FE envelope per state at 3750 N
              (+25 %) and 4096 N (J-F1 maximum); the cell takes the worse of the two and the record names the preload.  Thread
              shear re-based from A_n 63.48 to 68.4 with Mechanical's own N, Fsy, Fsu [DERIVED].  Seat / ring line: the F_sh form
              (MS_PQ_2Fty) is the row, the head-force bound is information.
    A4-80 screw rows are information (A4-80 withdrawn for J-FWD, 240 (4)).  PRELOAD rows and the TC-01 ligament station are
    information (lead 08:40Z / 09:15Z; 240 (9)).  FA1S P+Q is information (240 (2))."""
    out = {"TC-01": [], "TC-02": [], "HW-101 (J-FWD)": [], "files": [], "pending": list(JFWD_PENDING), "sha16": {}}
    for fp in (JF_CELLS, JF_ENV, MECH_FIX, MECH_IN718):
        if fp.exists():
            out["files"].append(str(fp))
            out["sha16"][fp.name] = sha16(fp)
        else:
            out["pending"].append(f"missing {fp}")
    C = json.loads(JF_CELLS.read_text())["steps"] if JF_CELLS.exists() else {}
    E = json.loads(JF_ENV.read_text())["states"] if JF_ENV.exists() else {}
    ENV_SRC = f"FE envelope {JF_ENV.stem} {sha16(JF_ENV)}" if JF_ENV.exists() else "FE envelope missing"
    out["envelope_basis"] = ENV_BASIS
    X = json.loads(MECH_FIX.read_text())["options"]["IN718 M5 x10"] if MECH_FIX.exists() else None
    M = json.loads(MECH_IN718.read_text()) if MECH_IN718.exists() else None
    T1, T2, SC = out["TC-01"], out["TC-02"], out["HW-101 (J-FWD)"]
    FE, FED = "FE js5 cells_v352An", "SIM / DERIVED"
    # ---------------- FA1S (primary, SF 1.0, 45.6 C)
    f = C.get("FA1S")
    if f:
        a, b = f["TC-01"], f["TC-02"]
        sp = a["SCL_primary"]
        lg = sp["TC01_net_ligament_avg_half"]
        T1.append(_r("FA1S", "(i) ligament Pm+Pb, half-ligament average", lg["MS_y_PmPb"], lg["MS_u_PmPb"], FE, FED, crit="231 (1)(i)"))
        T1.append(_r("FA1S", "(i) ligament Pm, half-ligament average", lg["MS_y_Pm"], lg["MS_u_Pm"], FE, FED, crit="231 (1)(i)"))
        for k in ("TC01_shear_out_flank+", "TC01_shear_out_flank-"):
            s = sp[k]
            T1.append(_r("FA1S", f"(i) shear-out {k[-6:]} Pm", s["MS_y_Pm"], s["MS_u_Pm"], FE, FED, crit="231 (1)(i)"))
            T1.append(_r("FA1S", f"(i) shear-out {k[-6:]} Pm+Pb", s["MS_y_PmPb"], s["MS_u_PmPb"], FE, FED, crit="231 (1)(i)"))
        hb = a["hole_bearing"]["spot_t2.688"]
        T1.append(_r("FA1S", "(ii) hole bearing, exact V 3603.6 N on t 2.688 (sharp)", hb["MS_y"], hb["MS_u"], FE, FED, crit="231 (1)(ii)"))
        T1.append(_r("FA1S", "(iii) band Neuber n30 (local strain)", a["neuber_band"]["n30"]["MS_strain"], None, FE, FED, crit="231 (1)(iii)"))
        T1.append(_r("FA1S", "elastic band (contact-edge field)", a["band_elastic"]["MS_y"], a["band_elastic"]["MS_u"], FE, FED, info=True))
        T1.append(_r("FA1S", "all-node (hole / head contact edge)", a["all_node_info"]["MS_y"], a["all_node_info"]["MS_u"], FE, FED, info=True,
                     note=f"n{a['all_node_info']['node']} {a['all_node_info']['vm_MPa']} MPa"))
        c2 = b["cell_231_1"]
        so = b["SCL_primary"]["TC02_shear_out_to_g2_x28.0"]
        T2.append(_r("FA1S", "(i) shear-out to g2 at x' 28.0 Pm+Pb", so["MS_y_PmPb"], so["MS_u_PmPb"], FE, FED, crit="231 (1)(i)"))
        T2.append(_r("FA1S", "(i) shear-out to g2 at x' 28.0 Pm", so["MS_y_Pm"], so["MS_u_Pm"], FE, FED, crit="231 (1)(i)"))
        th = b["thread_shear_An"]
        T2.append(_r("FA1S", f"(ii) thread shear on A_n {th['A_n_mm2']}", th["MS_y"], th["MS_u"], FE, FED, crit="231 (1)(ii)"))
        tb = b["tap_bearing_derived"]
        T2.append(_r("FA1S", f"(ii) tap bearing on L_e {tb['L_e_mm']}", tb["MS_y"], tb["MS_u"], FE, FED, crit="231 (1)(ii)"))
        T2.append(_r("FA1S", "(iii) band Neuber n15", b["neuber_band_iii"]["n15"]["MS_strain"], None, FE, FED, crit="231 (1)(iii)"))
        w = b["wall_SCL_band_node"]
        T2.append(_r("FA1S", "condition: through-wall SCL at the band node (must pass)", min(w["MS_y_Pm"], w["MS_y_PmPb"]),
                     min(w["MS_u_Pm"], w["MS_u_PmPb"]), FE, FED, info=True, crit="lead 07:21Z (4) condition", note="passes"))
        T2.append(_r("FA1S", "elastic band (contact-edge field, 0.99 mm from the TC-01 hole-edge footprint)", b["band"]["MS_y"], b["band"]["MS_u"],
                     FE, FED, info=True))
        T2.append(_r("FA1S", "all-node (bonded-thread tie edge)", b["all_node_info"]["MS_y"], b["all_node_info"]["MS_u"], FE, FED, info=True,
                     note=f"n{b['all_node_info']['node']} {b['all_node_info']['vm_MPa']} MPa"))
        s = f["SCREW"]
        SC.append(_r("FA1S", "A4-80 FE: interaction (234 (1)(b)) / shear-only yield on A_3", s.get("MS_y_shear_only_A3"), s.get("MS_u_interaction"),
                     FE, FED, info=True, note="A4-80 withdrawn (240 (4))"))
    if X:
        dl = X["TC01"]["drawing_limit_wall"]
        src = "Mechanical jfwd_fix_v352_v2 (IN718 option), drawing-limit wall 2.665"
        T1.append(_r("FA1S", "(ii) hole bearing, CALC V 3888.1 N, L 2.365 (governing, 240 (5))", dl["hole_bearing"]["MS_y"], dl["hole_bearing"]["MS_u"],
                     src, "CALC", crit="231 (1)(ii)"))
        T1.append(_r("FA1S", "(i) shear-out", dl["shear_out"]["MS_y"], dl["shear_out"]["MS_u"], src, "CALC", crit="231 (1)(i)"))
        T1.append(_r("FA1S", "(i) net section Pm", dl["net_section"]["MS_y"], dl["net_section"]["MS_u"], src, "CALC", crit="231 (1)(i)"))
        T1.append(_r("FA1S", "(i) ligament Pm+Pb", dl["ligament_PmPb"]["MS_y"], dl["ligament_PmPb"]["MS_u"], src, "CALC", crit="231 (1)(i)"))
        T1.append(_r("FA1S", "(iii) hole-edge Neuber (Mechanical's information row)", dl["hole_edge_neuber_info"]["MS_strain"], None, src, "CALC",
                     info=True))
        x2 = X["TC02"]
        T2.append(_r("FA1S", "(ii) tapped-thread bearing", x2["tapped_thread_bearing"]["MS_y"], x2["tapped_thread_bearing"]["MS_u"],
                     "Mechanical jfwd_fix_v352_v2 (IN718 option)", "CALC", crit="231 (1)(ii)"))
        it = x2["internal_thread_shear_at_F_max_thermal"]
        T2.append(_r("FA1S", f"(ii) internal thread shear at {it['F_N']} N on A_n {it['A_n_mm2']}", it["MS_y"], it["MS_u"],
                     "Mechanical jfwd_fix_v352_v2 (IN718 option)", "CALC", crit="231 (1)(ii)"))
        q = X["screw_FA1S_5020A"]
        SC.append(_r("FA1S", "IN718 5020A Eq. 22, preload omitted (criterion, 240 (3)); arm 1.120 mm (RETAINED, lead 15:37Z (R2))", None, q["governing"],
                     "Mechanical jfwd_fix_v352_v2 (IN718 option)", "CALC", crit="NASA-STD-5020A Eq. 22",
                     note=f"preload included {q['included_at_governing_row']} (information)"))
        ds = q["direct_shear_minor_231ii"]["CALC_abs_3888.1"]
        SC.append(_r("FA1S", "IN718 direct shear on the minor area (231 (ii))", ds["MS_y"], ds["MS_u"], "Mechanical jfwd_fix_v352_v2 (IN718 option)",
                     "CALC", crit="231 (ii)"))
    # ---------------- soak and preload states (secondary: P+Q <= 2 Fty(T) + band local strain; lead 08:40Z, 06:36Z)
    for st in ("PRELOAD", "SOAK70", "SOAK", "SOAK52"):
        v = C.get(st)
        info = st == "PRELOAD"
        if v:
            a, b, s = v["TC-01"], v["TC-02"], v["SCREW"]
            T1.append(_r(st, "band Neuber n30 (under-head band, local strain)", a["neuber_band"]["n30"]["MS_strain"], None, FE, FED, info=info,
                         crit="lead 06:36Z (DC head seat)"))
            sv = (a.get("cell") or {}).get("seat_values_DERIVED") or {}
            if isnum(sv.get("flat_seat_bearing_MS_vs_Fbry")):
                T1.append(_r(st, "flat-seat head bearing vs Fbry (A4-80 FE head force)", sv["flat_seat_bearing_MS_vs_Fbry"], None, FE, FED, info=True,
                             note="flight row = IN718 below"))
            T1.append(_r(st, "ligament station P+Q (0.087 mm from the hole wall; contact-edge field)", a["cell"].get("MS_PQ_min"), None, FE, FED,
                         info=True, crit="240 (9): information"))
            T1.append(_r(st, "all-node (hole / head contact edge)", a["all_node_info"]["MS_y"], a["all_node_info"]["MS_u"], FE, FED, info=True,
                         note=f"n{a['all_node_info']['node']} {a['all_node_info']['vm_MPa']} MPa"))
            th = b["thread_shear_An"]
            T2.append(_r(st, f"thread shear on A_n {th['A_n_mm2']}, js5 N (A4-80 FE)", th["MS_y"], th["MS_u"], FE, FED, info=True,
                         note="A4-80 FE force (A4-80 withdrawn, 240 (4)): the flight row is Mechanical's IN718 THE ROW"))
            e = (E.get(st) or {}).get("envelope") or {}
            nmax = (e.get("N_max_N") or [None, None])
            if not info and isnum(nmax[0]) and isnum(th.get("tau_MPa")):
                fsy, fsu = th["tau_MPa"] * (1 + th["MS_y"]), th["tau_MPa"] * (1 + th["MS_u"])
                tau = nmax[0] / A_N
                T2.append(_r(st, f"thread shear on A_n {A_N} at the envelope N {nmax[0]} ({nmax[1]}; A4-80 FE)", fsy / tau - 1, fsu / tau - 1,
                             ENV_SRC, "DERIVED", info=True, note="A4-80 FE force (A4-80 withdrawn, 240 (4)): the flight row is Mechanical's IN718 THE ROW"))
            T2.append(_r(st, "all-node (bonded-thread tie edge)", b["all_node_info"]["MS_y"], b["all_node_info"]["MS_u"], FE, FED, info=True,
                         note=f"n{b['all_node_info']['node']} {b['all_node_info']['vm_MPa']} MPa"))
            SC.append(_r(st, "A4-80 FE: tension on A_s (234 (1)(b))", s["MS_y"], s["MS_u"], FE, FED, info=True, note="A4-80 withdrawn (240 (4))"))
        e = (E.get(st) or {}).get("envelope") or {}
        lm = e.get("lines_min_MS_PQ")
        if lm and isnum(lm[0]):
            T1.append(_r(st, f"54 seat lines P+Q <= 2 Fty(T), envelope minimum (line d{lm[2]:+.3f} z'{lm[3]:+.1f}, {lm[1]}; A4-80 FE)", lm[0], None,
                         ENV_SRC, "SIM / DERIVED", info=info, crit="240 (9)(i)"))
    # ---------------- js5b (s5, mu 0, IN718 screw, 3750 N; FA1U / FA1D / LC2U / LC2Y / LC2N / LC2M): rows per lead 2026-10-21T03:30:46Z (1)
    JB = RES / "v352" / "jfwd_js5b_rows_v352.json"
    if JB.exists():
        out["files"].append(str(JB))
        out["sha16"][JB.name] = sha16(JB)
        B5 = json.loads(JB.read_text())
        bsrc, bt = f"FE js5b (jfwd_js5b_rows_v352 {sha16(JB)})", "SIM / DERIVED"
        HAND = ("hand form: SF on the total stress including preload, linear superposition ASSUMED (information; "
                "lead 2026-10-21T03:30:46Z (1))")
        FEF = ("FE-factored: the x1.5 / x2.0 state solved with contact at the 3750 N maximum preload (J-F1 cap), SF 1.0; "
               "LC2Y = yield slot, LC2U = ultimate slot (lead 2026-10-21T03:30:46Z (1))")
        for st, r in B5["states"].items():
            if st not in JS5B_TREAT:
                continue
            tr = JS5B_TREAT[st]
            a, b, s = r["TC-01"], r["TC-02"], r["SCREW"]
            lab = f"js5b {st} ({r['kind']}, SF {r['SF_member']})"
            ys, us = tr["slots"]

            hn = HAND if r["kind"] == "LC2" else (FEF if r["kind"] == "FE-factored" else None)

            def put(lst, row, y, u, info, crit, note=None):
                lst.append(_r(st, f"{lab}: {row}", y if ys else None, u if us else None, bsrc, bt, info=info, crit=crit, note=note))
            lg = a["ligament_half_avg"]
            put(T1, "(i) ligament Pm+Pb, half-ligament average", lg.get("MS_y_PmPb"), lg.get("MS_u_PmPb"), not tr["parts"], "231 (1)(i)", note=hn)
            put(T1, "(i) ligament Pm, half-ligament average", lg.get("MS_y_Pm"), lg.get("MS_u_Pm"), not tr["parts"], "231 (1)(i)", note=hn)
            for k, so in (a.get("shear_out") or {}).items():
                put(T1, f"(i) shear-out {k[-6:]} Pm+Pb", so.get("MS_y_PmPb"), so.get("MS_u_PmPb"), not tr["parts"], "231 (1)(i)", note=hn)
            hb = a.get("hole_bearing_t2.688") or {}
            put(T1, f"(ii) hole bearing, exact V {hb.get('V_N')} N on t 2.688", hb.get("MS_y"), hb.get("MS_u"), not tr["parts"], "231 (1)(ii)", note=hn)
            if ys:
                T1.append(_r(st, f"{lab}: (iii) band Neuber n30 (local strain)", (a.get("band_neuber") or {}).get("n30"), None, bsrc, bt,
                             info=not tr["parts"], crit="231 (1)(iii)", note=hn))
            so2 = b.get("shear_out_x28.0") or {}
            put(T2, "(i) shear-out to g2 at x' 28.0 Pm+Pb", so2.get("MS_y_PmPb"), so2.get("MS_u_PmPb"), not tr["parts"], "231 (1)(i)", note=hn)
            th = b.get("thread_shear_An") or {}
            put(T2, f"(ii) thread shear on A_n {th.get('A_n_mm2')}", th.get("MS_y"), th.get("MS_u"), not tr["parts"], "231 (1)(ii)", note=hn)
            tb = b.get("tap_bearing") or {}
            put(T2, f"(ii) tap bearing on L_e {tb.get('L_e_mm')}", tb.get("MS_y"), tb.get("MS_u"), not tr["parts"], "231 (1)(ii)", note=hn)
            put(SC, f"IN718 FE screw, {(s.get('form') or '')[:60]} (engmat AMS 5662/5663 bar minimums)", s.get("MS_y"), s.get("MS_u"),
                not tr["screw"], "234 (1)(b)")
    if M:
        menv = ((M.get("inputs") or {}).get("fea3d_soak_envelope") or {}).get("sha256_16")
        cur = sha16(JF_ENV) if JF_ENV.exists() else None
        src = f"Mechanical {MECH_IN718.stem} {sha16(MECH_IN718)} (IN718 on the FE envelope {menv})"
        out["in718_rows"] = {"file": str(MECH_IN718), "sha16": sha16(MECH_IN718), "version": M.get("version"), "envelope_sha16": menv,
                             "envelope_is_adopted": bool(menv and cur and menv == cur),
                             "adopted_envelope": f"{JF_ENV.stem} {cur} ({JF_ENV_ADOPTED})"}
        if menv and cur and menv != cur:
            src += f"; mapped on a superseded envelope (adopted {JF_ENV.stem} {cur}), re-mapping once on the final envelope"
            out["pending"].append(f"IN718 rows mapped on envelope {menv}, not on the adopted {JF_ENV.stem} {cur}: Mechanical re-maps ONCE on the "
                                  f"final envelope (lead 00:39:30Z (1))")
        jf1 = M.get("J_F1") or {}
        gov = f"{float(jf1['maximum_N']):.0f}" if isnum(jf1.get("maximum_N")) else None   # v7: '3750' governs (lead 17:56:12Z)
        if gov:
            out["in718_rows"]["governing_preload_N"] = gov
            out["in718_rows"]["columns"] = jf1.get("columns")

        def pinfo(pl):
            """a preload column other than the J-F1 maximum is information (v7: 4096 N = superseded maximum, lead 17:56:12Z)"""
            return bool(gov) and str(pl) != gov

        def pnote(pl, txt=None):
            t = [txt] if txt else []
            if pinfo(pl):
                t.append(f"{pl} N column = information (J-F1 maximum capped at {gov} N, lead 17:56:12Z)")
            return "; ".join(t) or None

        for st, v in M["states"].items():
            for pl, rows in v["rows"].items():
                info = st == "PRELOAD" or pinfo(pl)
                for rn, r in rows.items():
                    if not isinstance(r, dict):
                        continue
                    hist = r.get("from")
                    if rn == "screw_tension_234_1b":
                        SC.append(_r(st, "IN718 tension on A_s (234 (1)(b))" if st != "FA1S" else "IN718 tension on A_s at FA1S (information beside Eq. 22)",
                                     r["MS_y"], r["MS_u"], src, "CALC / DERIVED", info=info or st == "FA1S", preload=pl,
                                     note=pnote(pl, f"N {r['N_N']} ({hist}), T {r.get('T_C')} C")))
                    elif rn == "screw_fibre_soak":
                        SC.append(_r(st, "IN718 soak fibre yield (secondary: relaxation / shakedown / LCF, lead 10:14Z)", r["MS_y_fibre"], None, src,
                                     "CALC / DERIVED", info=True, preload=pl,
                                     note=pnote(pl, f"{hist}; shakedown {r.get('MS_shakedown')}, range {r.get('range_max_MPa')} MPa")))
                    elif rn == "head_on_spring_IN718":
                        SC.append(_r(st, f"IN718 head on the HW-170 spring, A {r.get('A_mm2')} mm2 (IN718 Fty / Ftu, no bearing credit)", r["MS_y"],
                                     r["MS_u"], src, "CALC / DERIVED", info=info, preload=pl,
                                     note=pnote(pl, f"N {r.get('N_N')} ({hist}), T {r.get('T_C')} C; spring side TO-SOURCE (Mechanical)")))
                    elif rn == "TC01_flat_bearing":
                        ab = r.get("area_mm2")
                        if "NO_SPRING_RECORD_A_ROW" in r:       # v7: route (i) spring footprint
                            T1.append(_r(st, f"IN718 flat bearing vs Fbry on the route (i) spring footprint (A {ab} mm2, registered stack)",
                                         r["MS_vs_Fbry"], None, src, "CALC / DERIVED", info=info, preload=pl,
                                         note=pnote(pl, f"no-spring records (information): union 36.401 mm2 {r.get('NO_SPRING_RECORD_union_basis_R4')}, "
                                                        f"A_ROW 38.171 mm2 {r.get('NO_SPRING_RECORD_A_ROW')}")))
                        else:
                            T1.append(_r(st, "IN718 flat-seat head bearing vs Fbry, rev-5 worst stack" + (f" (A_ROW {ab} mm2)" if ab else ""),
                                         r["MS_vs_Fbry"], None, src, "CALC / DERIVED", info=info, preload=pl,
                                         note=(f"A_ANN 47.12 superseded: {r.get('info_MS_full_flat_on_A_ANN_47.12_superseded')}; union inner "
                                               f"{r.get('info_MS_union_inner_boundary_RECOMMENDED')} (info)") if ab else f"full flat {r.get('MS_vs_Fbry_full_flat')}"))
                    elif rn == "TC01_under_head_band_neuber":
                        tg = r.get("tag")
                        T1.append(_r(st, "IN718 under-head band Neuber (local strain)" + (f" [{tg}]" if tg else ""), r["MS_strain"], None, src,
                                     "CALC / DERIVED" + ("; ASSUMED scaling" if tg and "ASSUMED" in tg else ""), info=info, preload=pl,
                                     note=pnote(pl, f"{hist}; {r.get('quoted_basis')}" if r.get("quoted_basis") else hist)))
                    elif rn in ("seat_line_d6p051_z0_PQ", "ring_line_PQ"):
                        nm = "seat line d6.051 z'0" if rn.startswith("seat") else "ring line"
                        T1.append(_r(st, f"IN718 {nm} P+Q <= 2 Fty(T), F_sh form", r["MS_PQ_2Fty"], None, src, "CALC / DERIVED", info=info,
                                     preload=pl, note=pnote(pl, r.get("from")), crit="240 (9)(i), (10)"))
                        T1.append(_r(st, f"IN718 {nm} P+Q, head-force bound", r["bound_MS"], None, src, "CALC / DERIVED", info=True, preload=pl,
                                     note=pnote(pl, r.get("bound_from"))))
                    elif rn == "TC01_ligament_station_PQ_FEA3D_cell_INFO":
                        T1.append(_r(st, "IN718 ligament station P+Q (0.08 mm from the hole wall; contact-edge field)", r.get("MS_PQ_2Fty_info"), None,
                                     src, "CALC / DERIVED", info=True, preload=pl, crit="240 (9): information", note=pnote(pl)))
                    elif rn == "TC01_lines_Pm_gt_Fty" and any(isnum(x) for x in r.values()):
                        T1.append(_r(st, "IN718 TC-01 lines with Pm > Fty (Mechanical)", None, None, src, "CALC / DERIVED", info=True, preload=pl,
                                     note=json.dumps(r)[:300]))
        # TC-02 thread shear: v7 THE ROW (route (i) A_n) is the row; FEA3D's drawn-basis A_n 68.4 is an information record
        tr = M.get("TC02_thread_shear_full_row") or {}
        trb = ((tr.get("A_n_bases") or {}).get("THE_ROW") or {})
        for st, by in (tr.get("rows") or {}).items():
            for pl, r in by.items():
                info = st == "PRELOAD" or pinfo(pl)
                tau = r["N_N"] / A_N
                if isinstance(r.get("THE_ROW"), dict):
                    t = r["THE_ROW"]
                    T2.append(_r(st, f"IN718 thread shear on THE ROW A_n {t['A_n_mm2']} (route (i): M5 x {trb.get('L_nom_mm', '10.7')} + HW-170 spring, "
                                     f"L_e min {trb.get('L_e_gap_bound_mm')})", t["MS_y"], t["MS_u"], src, "CALC / DERIVED", info=info, preload=pl,
                                 crit="234 (1)(b)", note=pnote(pl, f"N {r['N_N']} ({r.get('from')}), T {r['T_C']} C" + (f"; {r['flag']}" if r.get("flag") else ""))))
                    T2.append(_r(st, f"IN718 thread shear on FEA3D's drawn-basis A_n {A_N} (M5 x 10.2, lead 13:14Z; superseded by THE ROW)",
                                 r["Fsy_MPa"] / tau - 1, r["Fsu_MPa"] / tau - 1, src, "CALC / DERIVED", info=True, preload=pl,
                                 note=pnote(pl, f"N {r['N_N']} ({r.get('from')}), T {r['T_C']} C")))
                elif isinstance(r.get("FEA3D_A_n"), dict):      # v4 / v5 layout
                    T2.append(_r(st, f"IN718 thread shear on A_n {A_N} (re-based from Mechanical's {A_N_MECH} row)", r["Fsy_MPa"] / tau - 1,
                                 r["Fsu_MPa"] / tau - 1, src, "CALC / DERIVED", info=info, preload=pl,
                                 note=f"N {r['N_N']} ({r.get('from')}), T {r['T_C']} C; Mechanical row on {A_N_MECH}: {r['FEA3D_A_n']['MS_y']} / {r['FEA3D_A_n']['MS_u']}"))
        # FA1S rows of the rows file beside fix v2 (v7): Eq. 22 arm +0.4 sensitivity and the tap bearing on FEA3D's d x L_e basis
        q7 = M.get("FA1S_screw_5020A_eq22") or {}
        sn = q7.get("arm_+0.4_sens") or {}
        if isnum(sn.get("MS_omitted_governing")):
            SC.append(_r("FA1S", "IN718 5020A Eq. 22 at arm +0.4 mm (sensitivity), preload omitted", None, sn["MS_omitted_governing"], src, "CALC",
                         info=True, crit="NASA-STD-5020A Eq. 22", note=f"preload included {sn.get('MS_included_info')} (information)"))
        tb7 = (M.get("FA1S_tap_bearing") or {}).get("CALC_3888.1") or {}
        if isnum(tb7.get("MS_y")):
            T2.append(_r("FA1S", f"(ii) tap bearing, CALC V {tb7.get('V_N')} N on FEA3D's d x L_e basis (Mechanical rows)", tb7["MS_y"], tb7.get("MS_u"),
                         src, "CALC", crit="231 (1)(ii)", note=(M.get("FA1S_tap_bearing") or {}).get("note")))
    return out


def jfwd_rows_text(rows, lim=0.05):
    """the criterion rows below 0 (negative) and those in [0, lim) (flags), per state and preload, for a closure text."""
    neg, flg = [], []
    for r in sorted((r for r in rows if not r["info"]), key=lambda r: (r["state"], r["row"])):
        vals = [x for x in (r["MS_y"], r["MS_u"]) if isnum(x)]
        if not vals or min(vals) >= lim:
            continue
        t = (f"{r['state']} {r['row']}{' at ' + str(r['preload_N']) + ' N' if r.get('preload_N') else ''} "
             f"{'/'.join(('n/a' if not isnum(x) else f'{x:+.3f}') for x in (r['MS_y'], r['MS_u']))} [{r['tag']}]")
        (neg if min(vals) < 0 else flg).append(t)
    return ("negative: " + ("; ".join(neg) if neg else "none") + " | flags (0 to +0.05): " + ("; ".join(flg) if flg else "none"))


def jfwd_cell(rows, pending, files, sha):
    """cell of one J-FWD member: minimum over the non-information rows (y and u separately), with the governing row of each."""
    crit = [r for r in rows if not r["info"]]
    gy = min((r for r in crit if isnum(r["MS_y"])), key=lambda r: r["MS_y"], default=None)
    gu = min((r for r in crit if isnum(r["MS_u"])), key=lambda r: r["MS_u"], default=None)
    return {"value": [gy["MS_y"] if gy else None, gu["MS_u"] if gu else None], "governing": [gy, gu], "rows": rows, "pending": pending,
            "files": files, "sources_sha16": sha,
            "basis": [f"J-FWD rows (jfwd_cells): {gy['state']} {gy['row']} [{gy['tag']}; {gy['src']}]" + (f" at {gy['preload_N']} N" if gy and gy.get('preload_N') else "") if gy else None,
                      f"J-FWD rows (jfwd_cells): {gu['state']} {gu['row']} [{gu['tag']}; {gu['src']}]" + (f" at {gu['preload_N']} N" if gu and gu.get('preload_N') else "") if gu else None]}


def f4_cells():
    d = load("v352/f4_v352.json")
    if d is None:
        return None
    J = d["joints"]
    out = {}
    for j, host in (("J-FD01", "TC-02"), ("J-FD09", "GM-09")):
        rows = J[j]["rows"]
        rows = [r for v in rows.values() for r in v] if isinstance(rows, dict) else rows
        by = lambda k: min((r for r in rows if isnum(r.get(k))), key=lambda r: r[k], default=None)
        b, bu, th = by("MS_bolt_y"), by("MS_bolt_u"), by("MS_thread_host")
        b2 = by("MS_bolt_y_phi02")
        sep, slip = by("MS_sep"), by("MS_slip")
        out[j] = {"screw": {"MS_y": b["MS_bolt_y"] if b else None, "MS_u": bu["MS_bolt_u"] if bu else None,
                            "case": b.get("case") if b else None, "area": b.get("area") if b else None,
                            "MS_y_phi02": b2["MS_bolt_y_phi02"] if b2 else None, "MS_sep": sep["MS_sep"] if sep else None,
                            "MS_slip": slip["MS_slip"] if slip else None},
                  "host": host, "host_thread": {"MS": th["MS_thread_host"] if th else None, "case": th.get("case") if th else None},
                  "worst": J[j].get("worst"), "hardware": J[j].get("hardware")}
    return out


# ============================================================================================ build
def f(x):
    if not isnum(x):
        return "n/a"
    return f"{x:+.3f}" if abs(x) < 100 else ">+99"


def flag(c):
    s = ""
    b = " ".join(x or "" for x in c["basis"])
    if "regular stands" in b:
        s += "r"
    elif "all-node value" in b:
        s += "a"
    if c.get("carried_v351"):
        s += "c"
    if c.get("pending"):
        s += "p"
    if c.get("singular_lowered"):
        s += "s"
    if c.get("part_wide_cell"):
        s += "w"
    return s


def _src_file(src, jc):
    for fn, sh in (jc.get("sha16") or {}).items():
        if Path(fn).stem in (src or ""):
            return fn, sh
    return None, None


# lead 21:47:29Z (4): the route that would settle TC-04 n42993, with its time and disk (DERIVED from the logged runs: runs/lc1v352hbg3.log,
# lc1v352hbh3.log, pose_*_v352r3R3.log ccx seconds and peak_MB, chain_E.log run / end lines, du of the 19 run folders and their results)
TC04_ROUTE = ("TC-04 local remesh to q >= 0.1 (TC-04 only, L2 sizing; mesh cache < 1 MB) + hot-bound re-solve on the rebuilt R3 model: the 2 "
              "bases (GVLO / GVHI x 4 burn states, logged ccx 916 + 843 s) and the 17 R3 poses (logged 7,929 s, about 8.2 min each with "
              "extraction), re-posted (each post overlaps the next solve), then lc3_bound (LC3 and F2) and this matrix: about 2.7 h of ccx, "
              "about 3.1 h wall at one ccx with 2 threads (peak RSS 5.64 GB logged); disk about 0.46 GB transient per run before the trim "
              "(largest logged peak_MB 459.9) and about 0.49 GB held (19 trimmed run folders 448 MB + posts, envelopes and bound files "
              "40.5 MB) while the current cited set stays, so the free-space low point is about 0.95 GB below its start [DERIVED]")
# lead 22:24:34Z: the route is shared with the moment-free OP re-solve of the 17 R3 poses (report 9B.3) and is written as follows
TC04_ROUTE_STATUS = ("shared with the moment-free OP re-solve of the same 17 R3 poses (report 9B.3); not schedulable under the disk rules as "
                     "costed (the per-run start gate needs about 2.50 GiB free and the route leaves free about 0.95 GB lower); the lead decides "
                     "after js5b; nothing is scheduled (lead 22:24:34Z)")


def mf_bt_details(rows, jc):
    """lead 21:15:29Z (3): TC-01 FA1U / FA1S class MF with conditions (a)-(d); (4): TC-04 LC3 / F2 hot bound class BT with the bad-tet
    metric, the regular values beside it and the node-wise check (results/v352/tc04_bt_n42993_v352.json, hb_singular_check_v352.json)."""
    t01 = next((r for r in rows if r["part"] == "TC-01"), None)
    fa = load("f1_post_fa1v352n.json")
    sub = [x for x in jc.get("TC-01", []) if x["state"] == "FA1S" and not x["info"]]
    for x in sub:
        x["file"], x["file_sha16"] = _src_file(x["src"], jc)
    gy = min((x for x in sub if isnum(x["MS_y"])), key=lambda x: x["MS_y"], default=None)
    gu = min((x for x in sub if isnum(x["MS_u"])), key=lambda x: x["MS_u"], default=None)
    fe = [x for x in sub if x["src"].startswith("FE js5")]
    fy = min((x for x in fe if isnum(x["MS_y"])), key=lambda x: x["MS_y"], default=None)
    fu = min((x for x in fe if isnum(x["MS_u"])), key=lambda x: x["MS_u"], default=None)
    v7 = [x for x in sub if "jfwd_in718_rows" in x["src"]]
    neg = [x for x in sub if any(isnum(v) and v < 0 for v in (x["MS_y"], x["MS_u"]))]
    flg = [x for x in sub if x not in neg and any(isnum(v) and v < 0.05 for v in (x["MS_y"], x["MS_u"]))]
    rtxt = lambda x: (f"{x['row']} {f(x['MS_y'])} / {f(x['MS_u'])} [{x['tag']}; {x.get('file')} {x.get('file_sha16')}"
                      + (f"; {x['preload_N']} N" if x.get("preload_N") else "") + "]")
    if t01:
        for col in ("FA1U", "FA1S"):
            c = t01["cells"].get(col)
            if not c or c.get("class") != "MF":
                continue
            ry, ay, au = (c["regular"].get("y") or {}), (c["all"].get("y") or {}), (c["all"].get("u") or {})
            d_rbe3 = None
            if fa:
                for m in fa["states"]["A1_22.2"]["cases"][col]["margins"]:
                    if m["part"] == "TC-01" and m["set"] == "regular" and m.get("node") == ry.get("node"):
                        d_rbe3 = (m.get("d_singular_mm") or {}).get("rbe3_couplings")
            mf = {"rule": "lead 21:15:29Z (3): MF APPROVED under 234 (4), basis as the 239 TB70 ruling for this node; not physical approval",
                  "a_global_as_found": {"regular": list(c["value"]), "regular_node": ry.get("node"), "d_rbe3_mm": d_rbe3,
                                        "all_node": [ay.get("MS"), au.get("MS")], "all_node_node": ay.get("node"), "all_node_class": f"{ay.get('class')} {ay.get('class_detail')}"},
                  "b_governing_submodel": {"rows": sub, "value": [gy["MS_y"] if gy else None, gu["MS_u"] if gu else None],
                                           "governing_rows": [gy, gu], "fe_js5_min": [fy["MS_y"] if fy else None, fu["MS_u"] if fu else None],
                                           "fe_js5_rows": [fy, fu], "mechanical_v7_rows_3750N": v7, "flags_0_to_0.05": flg,
                                           "b1": ("POSTED 2026-10-21T00:30:31Z: (b1) seat_s9L12_mu02A (s9 R0.2, mu 0.2) FA1S: under-head band vM 491.3 MPa (n80299), hole bearing "
                                                  "255.6 MPa, seat lines P+Q min +0.147 (patch), N 2963.9 N, V 4079.2 N; head friction T/N 0.196 = mu at every step "
                                                  "(slipping, bearing-type at FA1S); information beside the CALC rows (not a criterion change)")},
                  "d_negative_rows": neg}
            if col == "FA1U":
                fs = t01["cells"].get("FA1S") or {}
                mf["c_FA1U_bounded_by_FA1S"] = ("DERIVED: FA1U (147 bar abs) is bounded by FA1S (151.04 bar abs) on the same pressure distribution: the FA-1 "
                                                "bands scale one OP unit field at the same thermal / manifold state (A1_22.2) and the J-FWD joint load grows "
                                                f"with the chamber pressure (global n{ry.get('node')}: FA1U {f(c['value'][0])} / {f(c['value'][1])} above FA1S "
                                                f"{f((fs.get('value') or [None, None])[0])} / {f((fs.get('value') or [None, None])[1])}); the js5b FA1U sub-model rows are in the J-FWD column")
            if neg:
                ny = min((x["MS_y"] for x in neg if isnum(x["MS_y"]) and x["MS_y"] < 0), default=None)
                nu = min((x["MS_u"] for x in neg if isnum(x["MS_u"]) and x["MS_u"] < 0), default=None)
                c["value_submodel_negative"] = [ny, nu]
            c["mf"] = mf
            txt = (f"MF (n{ry.get('node')} regular, {d_rbe3} mm from the J-FWD RBE3 in the J-FWD region; the all-node minimum n{ay.get('node')} "
                   f"{f(ay.get('MS'))} / {f(au.get('MS'))} is the RBE3 itself, d {ay.get('d_class_mm')}): (a) global values kept as found; "
                   f"(b) governing = the J-FWD sub-model's TC-01 FA1S criterion rows, minimum {f(mf['b_governing_submodel']['value'][0])} / "
                   f"{f(mf['b_governing_submodel']['value'][1])}: y {rtxt(gy) if gy else 'n/a'}; u {rtxt(gu) if gu else 'n/a'}; FE js5 FA1S minimum "
                   f"{f(fy['MS_y'] if fy else None)} / {f(fu['MS_u'] if fu else None)} ({fy['row'] if fy else ''}); Mechanical v7 at 3750 N: "
                   + ("; ".join(rtxt(x) for x in v7) or "none") + "; flags 0 to +0.05: " + ("; ".join(rtxt(x) for x in flg) or "none")
                   + " (the +0.005 hole-bearing row is in jfwd_fix_v352_v2, the FA1S CALC source v7 cites); (b1) FA1S rows posted (information, 10A.12); "
                   + (f"(c) {mf['c_FA1U_bounded_by_FA1S']}; " if col == "FA1U" else "")
                   + ("(d) sub-model row(s) NEGATIVE, carried: " + "; ".join(rtxt(x) for x in neg) if neg else "(d) no sub-model TC-01 FA1S criterion row is negative")
                   + ". Not physical approval.")
            c["closure"] = txt
    # TC-04 BT (lead 21:15:29Z (4))
    t04 = next((r for r in rows if r["part"] == "TC-04"), None)
    bt = load("v352/tc04_bt_n42993_v352.json")
    if t04:
        for col, case in (("LC3 hot bound", "LC3"), ("F2 hot bound", "F2")):
            c = t04["cells"].get(col)
            if not c or c.get("class") != "BT":
                continue
            au = (c["all"].get("u") or {})
            ru, ry_ = (c["regular"].get("u") or {}), (c["regular"].get("y") or {})
            sc = au.get("singular_check") or {}
            if bt:
                tets = bt["bt"]["tets_containing_node"]
                near = [x for x in bt["within_2mm"]["nodes"] if x["regular"]]
                bt_txt = (f"n{bt['node']} sits on {len(tets)} TC-04 tets with q " + " / ".join(f"{x['q']:.3f}" for x in tets)
                          + f" (BT criterion: post_f1.tet_quality q = 12 (3V)^(2/3) / sum of the 6 squared edge lengths < {bt['bt']['q_bad']}; TC-04 "
                          f"{bt['bt']['TC-04_n_tets_q_below_0.1']} of {bt['bt']['TC-04_n_tets']} tets below, q_min {bt['bt']['TC-04_q_min']:.3f}, L2 mesh hmax "
                          f"{bt['mesh_identity']['base_mesh_meta']['hmax']} / hmin {bt['mesh_identity']['base_mesh_meta']['hmin']} mm)")
                tens = ("tensor recombination not available: TC-04 is meshed identically in the R3 base and all 17 R3 poses, but the base tensors "
                        "were trimmed (C) (the extract holds GM-01 / GM-02 only) and the increments are stored as vM envelopes only"
                        if not bt["tensors_stored"]["recombination_available"] else "tensors stored")
                nr = ("; ".join(f"n{x['node']} {x['d_mm']} mm" for x in near) or "none")
                regtxt = (f"worst regular node within 2 mm: {len(near)} regular nodes ({nr}); no per-node hot value is stored for them, each is >= the "
                          f"part's regular minimum {f(ry_.get('MS'))} / {f(ru.get('MS'))} (n{ru.get('node')}, beside the cell as information)")
            else:
                bt_txt, tens, regtxt = "tc04_bt_n42993_v352.json missing", "", ""
            lowtxt = ""
            if sc.get("lowered"):
                lowtxt = (f"; value = the node-wise bound at n{au.get('node')}: its own increment envelope {sc.get('node_increment_MPa')} MPa exceeds the "
                          f"regular part maximum {sc.get('reg_max_MPa')} MPa that lc3_bound adds, so the stored {f(sc['stored_MS'][0])} / {f(sc['stored_MS'][1])} "
                          f"is not a bound at this node (hb_singular_check_v352)")
            pwc = pw_cells().get((case, "TC-04")) or {}
            pwv = pwc.get("pw_min") or [None, None]
            anv = sc.get("at_node_MS") or [None, None]
            pwtxt = ""
            if all(isnum(x) for x in (pwv[1], anv[1])):
                pwtxt = (f"; the part-wide bound over every TC-04 node (hb_partwide_v352) is {pwv[0]:+.5f} / {pwv[1]:+.5f} against the node-wise "
                         f"{anv[0]:+.5f} / {anv[1]:+.5f}: equal at 3 decimals, so the node-wise value stands (lead 21:47:29Z (4); stored "
                         f"{f(sc['stored_MS'][0])} / {f(sc['stored_MS'][1])} and the regular values beside it as information)")
            c["bt"] = {"tc04_bt_file": "v352/tc04_bt_n42993_v352.json", "singular_check": sc, "part_wide": pwc,
                       "route_to_settle": TC04_ROUTE, "route_status": TC04_ROUTE_STATUS,
                       "ruling": "lead 21:47:29Z (4): ACCEPTED, conservative side; a found negative, nothing scheduled; the lead decides after js5b"}
            c["closure"] = (f"found negative: DERIVED lower bound at a mesh-defect node (not an exception under 234 (4): a bad tet is a discretisation "
                            f"defect, refinement convergence not shown; no refinement or sub-model replaces it); {bt_txt}{lowtxt}{pwtxt}; {tens}; {regtxt}; "
                            f"route that would settle it: {TC04_ROUTE} ({TC04_ROUTE_STATUS}). Not physical approval.")


def build():
    S = sources()
    rows = []
    for p in PARTS:
        cells = {}
        for col in COLS + INFO_COLS:
            if col in ("J-FWD", "J-FD01", "J-FD09"):
                continue
            if not S[col]["srcs"] and not S[col]["carried"]:
                cells[col] = {"value": [None, None], "pending": S[col]["pending"], "basis": [None, None], "regular": {}, "all": {}}
                continue
            cells[col] = cell(p, col, S)
        rows.append({"part": p, "changed_v352": p in CHANGED, "cells": cells})
    # J-FWD / F4 columns
    jc = jfwd_cells()
    f4 = f4_cells() or {}
    jrows = {jr: {"part": jr, "joint_row": True, "cells": {}} for jr in JOINT_ROWS}
    for mem in ("TC-01", "TC-02", "HW-101 (J-FWD)"):
        cj = jfwd_cell(jc[mem], jc["pending"], jc["files"], jc["sha16"])
        v = [x for x in cj["value"] if isnum(x)]
        if v and min(v) < 0:
            c = neg_class(mem, "J-FWD")
            cj["class"], cj["closure"], cj["ref"] = c if c else ("UNCLASSIFIED", "to the lead", None)
        elif v:
            c = neg_class(mem, "J-FWD")
            if c:     # positive cell: the class does not apply; the rows near zero are still stated
                cj["note"] = "cell positive (no class applies): " + c[1].split(": ", 1)[0] + "; " + jfwd_rows_text(cj["rows"])
        if cj.get("closure") and "{rows}" in cj["closure"]:
            cj["closure"] = cj["closure"].replace("{rows}", jfwd_rows_text(cj["rows"]))
        tgt = next((r for r in rows if r["part"] == mem), None) or jrows.get(mem)
        tgt["cells"]["J-FWD"] = cj
    mf_bt_details(rows, jc)
    for j, jr in (("J-FD01", "HW-103 (J-FD01)"), ("J-FD09", "HW-127 (J-FD09)")):
        if j not in f4:
            continue
        sc = f4[j]["screw"]
        jrows[jr]["cells"][j] = {"value": [sc["MS_y"], sc["MS_u"]], "detail": f4[j], "files": ["v352/f4_v352.json"],
                                 "basis": ["F4 bounding (Phi 0 / 1), DERIVED", "F4 bounding, DERIVED"]}
        host = next(r for r in rows if r["part"] == f4[j]["host"])
        host["cells"][j] = {"value": [f4[j]["host_thread"]["MS"], None], "detail": {"host_thread": f4[j]["host_thread"]},
                            "files": ["v352/f4_v352.json"], "basis": ["host thread strip, DERIVED", None]}
    rows += list(jrows.values())
    # row minimum over the governing columns (info columns excluded)
    for r in rows:
        best = None
        for col in COLS:
            c = r["cells"].get(col)
            if not c:
                continue
            for j, k in enumerate("yu"):
                v = c["value"][j] if c.get("value") else None
                if isnum(v) and (best is None or v < best[0]):
                    best = (v, col, k)
        r["min"] = list(best) if best else None
    srcfiles = sorted({fn for col in S for fn in S[col]["files"]})
    out = {"doc": __doc__.split("usage:")[0].strip(), "date": "2026-10-21", "columns": COLS, "info_columns": INFO_COLS, "column_doc": COL_DOC,
           "changed_parts_v352": sorted(CHANGED), "cad_changed_final_v352": {"parts": CAD_CHANGED_FINAL, "ref": "CHANGELOG 247 (Mechanical final 03-cad v3.5.2 set, MANIFEST a94851ae4dc22cc4)", "note": "TC-03 (rev-4 seat details), FD-02 and FD-04 changed in CAD, not in this FE model (TC-03 = v3.5.1 mesh, seat region deferred to Mechanical's rev-4 S-AX contact sub-model; FD-02 / FD-04 no FE body); ENG-TC-01's rev-5 d11.2 flats lie inside the global model's J-FWD connector regions"}, "sources_sha16": {fn: sha16(RES / fn) for fn in srcfiles if (RES / fn).exists()},
           "pending": {col: S[col]["pending"] for col in S if S[col]["pending"]}, "rows": rows,
           "named_submodels": [{"part": p, "class_detail": d, "text": t, "ref": rf} for p, d, _, t, rf in NAMED], "not_evaluated": NOT_EVAL,
           "class_rules": [{"part": k[0], "column": k[1], "class": v[0], "closure": v[1], "ref": v[2]} for k, v in CLASS_RULES.items()]}
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / "margin_matrix_v352.json").write_text(json.dumps(out, indent=1, default=float))
    (OUTD / "margin_matrix_v352.md").write_text(render(out))
    return out


def render(out):
    cols = out["columns"]
    L = ["# FEA3D margin matrix v3.5.2 (every part x every case)", "",
         "Cell = MS_y / MS_u after the 234 (4) all-node rule. Flags: r = regular value stands (the all-node minimum sits at an idealisation a "
         "named sub-model / contact FE replaces), a = all-node value is the cell, c = includes v3.5.1 carried values (unchanged part), "
         "p = some sources pending, s = hot-bound all-node value lowered to the node-wise bound at its node (hb_singular_check_v352), "
         "w = hot-bound all-node value replaced by the rigorous part-wide bound over every node of the part, stored value beside it "
         "(hb_partwide_v352; lead 21:47:29Z: lc3_bound does not sum the increments of parts outside SAME_MESH_ENGINE node by node). "
         "MF (gov. ...) = model-fidelity class with the governing sub-model value (lead 21:15:29Z (3)); BT = bad-tet class (lead 21:15:29Z (4)). "
         "'-' = case not evaluated for the part; n/a = no allowable in that slot (brittle parts: one value).", "",
         "| part | " + " | ".join(cols) + " | min |", "|---|" + "---|" * (len(cols) + 1)]
    for r in out["rows"]:
        cs = []
        for col in cols:
            c = r["cells"].get(col)
            if not c or c.get("value") in (None, [None, None]):
                cs.append("-" if not (c and c.get("pending")) else "pending")
                continue
            y, u = c["value"]
            fl = flag(c) if "regular" in c else ("p" if c.get("pending") else "")
            gv = ((c.get("mf") or {}).get("b_governing_submodel") or {}).get("value")
            ps = c.get("part_wide_stored") if c.get("part_wide_cell") else None
            cs.append(f"{f(y)} / {f(u)}" + (f" {fl}" if fl else "") + (f" MF (gov. sub-model {f(gv[0])} / {f(gv[1])})" if gv else "")
                      + (" BT" if c.get("class") == "BT" else "")
                      + (f" (part-wide; stored {f(ps[0] if ps[0] is not None else y)} / {f(ps[1] if ps[1] is not None else u)})" if ps else ""))
        mn = r.get("min")
        L.append(f"| {r['part']} | " + " | ".join(cs) + " | " + (f"{f(mn[0])} ({mn[1]} {mn[2]})" if mn else "-") + " |")
    L += ["", "## All-node minima beside the regular values (every cell where they differ)", "",
          "| part | column | regular y / u (node, state) | all-node y / u (node, class, detail, d mm) | cell basis |", "|---|---|---|---|---|"]
    for r in out["rows"]:
        for col in cols + out["info_columns"]:
            c = r["cells"].get(col)
            if not c or "regular" not in c:
                continue
            ry, ay = (c["regular"].get("y") or {}), (c["all"].get("y") or {})
            ru, au = (c["regular"].get("u") or {}), (c["all"].get("u") or {})
            if not ay or (ry and ay.get("MS") == ry.get("MS") and ay.get("node") == ry.get("node") and not ay.get("part_wide")):
                continue
            pwy, pwu = (ay.get("part_wide") or {}), (au.get("part_wide") or {})
            pwt = (f" [part-wide bound; stored {f(pwy.get('stored_MS', ay.get('MS')))} / {f(pwu.get('stored_MS', au.get('MS')))}]"
                   if (pwy or pwu) else "")
            L.append(f"| {r['part']} | {col} | {f(ry.get('MS'))} / {f(ru.get('MS'))} (n{ry.get('node')}, {ry.get('state') or ry.get('src')}) | "
                     f"{f(ay.get('MS'))} / {f(au.get('MS'))}{pwt} (n{ay.get('node')}, {ay.get('class')}, {ay.get('class_detail') or ''}, {ay.get('d_class_mm')}) | "
                     f"{c['basis'][0] or ''} |")
    L += ["", "## Negative cells and their classes (REV-MECH-2 section 10 classes)", "",
          "Governing record = the record behind the cell value (all-node or regular per the cell basis): node, state, node class / detail / "
          "distance, node temperature, set-minimum primary-only MS and nodal P+Q (2 Fty(T) / vM - 1) of the same set.", "",
          "| part | column | cell y / u | governing record (node, state, class, d mm, T C, primary-only MS, P+Q) | class | closure | ref |",
          "|---|---|---|---|---|---|---|"]
    for r in out["rows"]:
        for col in cols:
            c = r["cells"].get(col)
            if not c or not c.get("class"):
                continue
            g = ""
            if "regular" in c:
                b0 = (c.get("basis") or [""])[0] or ""
                rec = (c["regular"].get("y") if "regular stands" in b0 or "= regular value" in b0 else c["all"].get("y")) or {}
                if rec:
                    g = (f"n{rec.get('node')}, {rec.get('state') or rec.get('src') or ''}, {rec.get('class') or ''} {rec.get('class_detail') or ''}, "
                         f"{rec.get('d_class_mm')}, {rec.get('T_C')}, {f(rec.get('MS_primary_only'))}, {f(rec.get('MS_PQ_nodal'))}")
                    if rec.get("part_wide"):
                        g = f"part-wide bound (every node; hb_partwide_v352), stored minimum at: {g}"
            L.append(f"| {r['part']} | {col} | {f(c['value'][0])} / {f(c['value'][1])} | {g} | {c['class']} | {c.get('closure') or ''} | {c.get('ref') or ''} |")
    # OP-moment residue: DERIVED bounds beside cells (lead 22:54:03Z (2)-(3), 23:12:52Z (2)); the cells above stay as found
    _g = RES / "v352" / "gm01_rodpath_bound_v352.json"
    _h = RES / "v352" / "hb_base_residue_v352.json"
    if _g.exists() or _h.exists():
        L += ["", "## OP-moment residue: DERIVED bounds beside cells (cells stand as found; MF observation, lead 22:24:34Z / 22:54:03Z / 23:12:52Z)", ""]
        out["op_residue_beside"] = {}
    if _g.exists():
        g = json.loads(_g.read_text())
        L += [f"GM-01 FA-1 cells (`gm01_rodpath_bound_v352.json` {hashlib.sha256(_g.read_bytes()).hexdigest()[:16]}): ROD_1 residue + (tension) in "
              f"every case; GM-01 stress per unit rod force from the EA unit steps of pose_neutral_c71 (v3.5.1 L1, rev-1 lever; cell node "
              f"n{g['node']} = c71 n{g['c71_node']} at {g['c71_node_distance_mm']:.3f} mm) [DERIVED; transfer ASSUMED].", "",
              "| cell | as found (posted) | ROD_1 as found / moment-free N | moment-free (tensor) | sign-free bound (triangle) |", "|---|---|---|---|---|"]
        for cid, c in g["cases"].items():
            a_ = c["at_node"]
            L.append(f"| GM-01 {cid} | {a_['MS_posted'][0]:+.3f} / {a_['MS_posted'][1]:+.3f} | {c['rods_as_found_N']['ROD_1']:+.1f} / "
                     f"{c['rods_moment_free_N']['ROD_1']:+.1f} | {c['part_all_node_min']['moment_free']['MS'][0]:+.3f} / "
                     f"{c['part_all_node_min']['moment_free']['MS'][1]:+.3f} | {c['part_all_node_min']['triangle_bound']['MS'][0]:+.3f} / "
                     f"{c['part_all_node_min']['triangle_bound']['MS'][1]:+.3f} |")
        out["op_residue_beside"]["GM-01 FA-1"] = {k: {"moment_free": v["part_all_node_min"]["moment_free"]["MS"],
                                                      "triangle_bound": v["part_all_node_min"]["triangle_bound"]["MS"]} for k, v in g["cases"].items()}
    if _h.exists():
        h = json.loads(_h.read_text())
        L += ["", f"Hot-bound base residue (`hb_base_residue_v352.json` {hashlib.sha256(_h.read_bytes()).hexdigest()[:16]}): base +"
              f"{h['base_residue_N'][0]:.0f} / +{h['base_residue_N'][1]:.0f} N at Pc_max; rods prescribed (LC3 runaway, GS): REPLACED to within "
              "(t_base - t_pose) Pc_max; rods reacting inertia (TD, LC6): ADDS.  Worst-sign estimate dMS <= (1 + MS) dF / F [DERIVED; ASSUMED "
              "linear, whole increment rod-driven].", "",
              "| cell (lever root) | governing pose | lever rod d_rod N (sign) | dF / F |", "|---|---|---|---|"]
        for k, v in h["cells"].items():
            ir = 0 if v["lever_rod"] == "ROD_1" else 1
            L.append(f"| {k} | {v['governing_pose']} | {v['lever_rod']} {v['d_rod_N'][ir]:+.1f} | {v['d_rod_over_F']:.4f} |")
        out["op_residue_beside"]["hot-bound base"] = {k: {"pose": v["governing_pose"], "d_rod_N": v["d_rod_N"], "dF_over_F": v["d_rod_over_F"]}
                                                      for k, v in h["cells"].items()}
    L += ["", "## Cells shown '-' and why", ""] + [f"- **{k}**: {v}" for k, v in out.get("not_evaluated", {}).items()]
    L += ["", "## J-FWD column rows (cell = minimum over the criterion rows; information rows listed after them)", ""]
    for r in out["rows"]:
        c = r["cells"].get("J-FWD")
        if not c or "rows" not in c:
            continue
        L += [f"### {r['part']}: cell {f(c['value'][0])} / {f(c['value'][1])}", "",
              f"- governing y: {c['basis'][0]}", f"- governing u: {c['basis'][1]}"] + \
             ([f"- class {c['class']}: {c.get('closure')} ({c.get('ref')})"] if c.get("class") else []) + \
             ([f"- {c['note']}"] if c.get("note") else []) + ["",
              "- pending: " + "; ".join(c.get("pending") or []), "",
              "| state | row | y | u | preload N | tag | source | note |", "|---|---|---|---|---|---|---|---|"]
        for x in sorted(c["rows"], key=lambda x: (x["info"], x["state"], x["row"])):
            L.append(f"| {x['state']} | {'(info) ' if x['info'] else ''}{x['row']} | {f(x['MS_y'])} | {f(x['MS_u'])} | {x.get('preload_N') or ''} | "
                     f"{x['tag']} | {x['src']} | {x.get('note') or ''} |")
        L.append("")
    L += ["", "## Columns", ""] + [f"- **{k}**: {v}" for k, v in out["column_doc"].items()]
    if out["pending"]:
        L += ["", "## Pending sources", ""] + [f"- {k}: {', '.join(v)}" for k, v in out["pending"].items()]
    L += ["", "## Source files (sha256/16)", ""] + [f"- results/{k}: {v}" for k, v in out["sources_sha16"].items()]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = build()
    neg = [(r["part"], col, c["value"], c.get("class")) for r in o["rows"] for col, c in r["cells"].items()
           if col in COLS and c.get("value") and any(isnum(v) and v < 0 for v in c["value"])]
    print(f"rows {len(o['rows'])}, negative cells {len(neg)}")
    for n in neg:
        print("  ", n)
    print("pending:", json.dumps(o["pending"])[:2000])
