"""Write interfaces/mechanical.json v2.4 (Mechanical, 2026-10-21): the v3.5.2 J-FWD FOLLOW-UPS issue (lead brief 2026-10-21T08:05:00Z
F1-F6 and the lead's 08:39:41Z relay of REV-COMB-4 R4-01 / R4-02 / R4-10), a PATCH on base v2.3 (2026-10-21, sha256/16 55397a9b8ddb59be;
v2.3 writer 50c29f6b90057742 kept as 03-cad/v3.5.2/history/write_mechanical_json_v352.py.50c29f6b90057742).

Rule: every v2.3 key and leaf is KEPT except the leaves this writer names in PATCHED (each asserted at its v2.3 value before it is
replaced); the new values GOVERN; each replaced v2.3 leaf is kept whole in superseded_v2p3_values and named in superseded_v2p3_entries.
  - patched: the header, reading_rule_v352, scripts_v352, inputs_read_v352, sources_v352 (keys added only), jfwd_v352.tap_wall (tap wall
    v3, R4-01; R11 closed), jfwd_v352.founder_rules.post_abort_joint_replacement and .C6 (texts v5: C9 (4) / C6 (4)),
    jfwd_v352.hardware.texts_superseding_hardware_strings (the HW-101 action string and the HW-101 tap-wall v1 strings superseded by
    the drawing-text v2 notes),
    jfwd_v352.drawing_texts (drawing texts v2, texts v5), lead_rulings_quoted_v352 (keys added only), requests_v352 ([0] closed, items
    added), open_items_v352 ([4], [12], [13] restated, items added);
  - new: lc_tb70_envelope_v352 (Z3 v2, the J-FWD replace rule, the F4 abort set), c1_seat_v352 (F1 and its cross-check),
    torch_port_bl08_v352 (F2), followups_basis_v352, superseded_v2p3_entries, superseded_v2p3_values;
  - the 29 v2.1 sections are asserted equal to the archived v2.1; every other v2.3 leaf is asserted unchanged.
Every number is read from the result files in sources_v352 (sha256/16 checked against the work tree and, outside --pre, the hub copies);
the lead's rulings are quoted from the hub CHANGELOG lines named (line sha recorded) or, for the 08:05:00Z brief and the 08:39:41Z relay
(not CHANGELOG lines), paraphrased and marked so, with the relay's quoted sentences verbatim; nothing is typed except tagged constants and
ruled texts.  At write time v2.3 is archived by RENAME as 03-cad/v3.5.2/history/mechanical.json.55397a9b8ddb59be and v2.4 is written.
Usage: python3 -B -I write_mechanical_json_v352.py [--pre | --dry]  (--pre: sources not yet on the hub are checked on the work-tree side
only, nothing written; --dry: every hub copy checked, nothing written; no flag: re-reads the hub file just before writing, checks free
space >= 1.95 GiB after the write (lead disk rule), archives v2.3 by rename, writes v2.4, reads it back)."""
import copy, hashlib, json, os, sys
from pathlib import Path

HUBE = Path("/home/claude/work/shared-fallback/engine")
HUB = HUBE / "interfaces" / "mechanical.json"
CL = HUBE / "interfaces" / "CHANGELOG.md"
V23_SHA, V22_SHA, V21_SHA = "55397a9b8ddb59be", "f790d31b5ca7d954", "e4d3e7c9df529171"
HIST = HUBE / "03-cad" / "v3.5.2" / "history" / f"mechanical.json.{V23_SHA}"
V22_HIST = HUBE / "03-cad" / "v3.5.2" / "history" / f"mechanical.json.{V22_SHA}"
V21_HIST = HUBE / "03-cad" / "v3.5.2" / "history" / f"mechanical.json.{V21_SHA}"
W = Path("/home/claude/work/mechanical/v352")
J, T, TB, C1 = W / "jfwd", W / "texts", W / "tb70", W / "c1seat"
# key: (work-tree source or None for a hub-only input, hub path relative to engine/, expected sha256/16)
SRC_NEW = {
    "tap_wall_v3": (J / "jfwd_tapwall_v352_v3.json", "04-fea/v352/jfwd_tapwall_v352_v3.json", "ef70572ec92b05b0"),
    "tap_wall_v2_reviewed": (J / "jfwd_tapwall_v352_v2.json", "04-fea/v352/jfwd_tapwall_v352_v2.json", "9f8849412d4419d7"),
    "lc_tb70_envelope_v2": (TB / "lc_tb70_envelope_v2.json", "04-fea/v352/lc_tb70_envelope_v2.json", "7ebd2fd63dc878ef"),
    "lc_tb70_envelope_v1": (TB / "lc_tb70_envelope_v1.json", "04-fea/v352/lc_tb70_envelope_v1.json", "6f710726e4787134"),
    "texts_v5": (T / "item_c_tf1_texts_v352_v5.json", "04-fea/v352/texts/item_c_tf1_texts_v352_v5.json", "c4ea791b7aa68e2e"),
    "drawing_texts_v2": (T / "jfwd_drawing_texts_v352_v2.json", "03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v2.json", "58683aa9a66a65dd"),
    "c1_seat_v1": (C1 / "c1_seat_v352_v1.json", "04-fea/v352/c1seat/c1_seat_v352_v1.json", "435f5d71f6213160"),
    "c1_seat_xcheck_v1": (C1 / "c1_seat_xcheck_v352_v1.json", "04-fea/v352/c1seat/c1_seat_xcheck_v352_v1.json", "02a9f27c7965f223"),
    "torch_port_bl08_v1": (C1 / "torch_port_bl08_v352_v1.json", "04-fea/v352/c1seat/torch_port_bl08_v352_v1.json", "20220647d32cbbbc"),
    "combustion_v2p4c": (None, "interfaces/combustion.json", "661db0a593462382"),
    "REVIEW-COMBUSTION-R4": (None, "reviews/REVIEW-COMBUSTION-R4.md", "2908321d7f75d439"),
    "margin_matrix_v352_rows_v8": (None, "04-fea/assembly3d_v352_rows_v8/tables/margin_matrix_v352.json", "6c694fa7147fb511")}
SCRIPTS_NEW = {   # the scripts behind the new sources (work tree, hub path, sha256/16)
    "lc_tb70_envelope": (TB / "lc_tb70_envelope.py", "04-fea/v352/lc_tb70_envelope.py", "d14489808338006b"),
    "jfwd_tapwall": (J / "jfwd_tapwall_v352.py", "04-fea/v352/jfwd_tapwall_v352.py", "0de59c74ff531b30"),
    "jfwd_tapwall_v2_reviewed": (J / "jfwd_tapwall_v352_v2.py", "04-fea/v352/history/jfwd_tapwall_v352.py.b7d7aad6eacef440", "b7d7aad6eacef440"),
    "texts": (T / "item_c_tf1_texts_v352.py", "04-fea/v352/texts/item_c_tf1_texts_v352.py", "b75b3a541576474b"),
    "c1_seat": (C1 / "c1_seat_v352.py", "04-fea/v352/c1seat/c1_seat_v352.py", "fe1f41a73f25a0bc"),
    "c1_seat_xcheck": (C1 / "c1_seat_xcheck_v352.py", "04-fea/v352/c1seat/c1_seat_xcheck_v352.py", "bba820fabd895ff6"),
    "torch_port_bl08": (C1 / "torch_port_bl08_v352.py", "04-fea/v352/c1seat/torch_port_bl08_v352.py", "72c853aebfe96fd3")}
HEADER = ("version", "date", "supersedes", "status")
# the v2.3 leaves (and the v2.3 keys) this patch replaces; every other leaf must come out unchanged
PATCHED = ("version", "date", "supersedes", "status", "reading_rule_v352", "scripts_v352", "inputs_read_v352", "sources_v352",
           "jfwd_v352.tap_wall", "jfwd_v352.founder_rules.post_abort_joint_replacement", "jfwd_v352.founder_rules.C6",
           "jfwd_v352.hardware.texts_superseding_hardware_strings", "jfwd_v352.drawing_texts", "lead_rulings_quoted_v352",
           "requests_v352", "open_items_v352")
NEW_KEYS = ("lc_tb70_envelope_v352", "c1_seat_v352", "torch_port_bl08_v352", "followups_basis_v352", "superseded_v2p3_entries",
            "superseded_v2p3_values")
# the lead's ruling on Z3 v2 / the J-FWD replace rule, quoted verbatim at the go (None before the go: status OPEN).  RULED at the go
# 2026-10-21T10:47:17Z, CHANGELOG 258 (3): "quote" names the hub CHANGELOG segment, quoted by cl_segment (line sha recorded)
LEAD_RULING_Z3 = {
    "quote": (258, "Z3 RULING: Z3 v2 ADOPTED as proposed", " (4) ROUTING:"),
    "status": ("ADOPTED by the lead at the go 2026-10-21T10:47:17Z (CHANGELOG 258 (3), quoted in lead_rulings_quoted_v352."
               "Z3_and_jfwd_rule_ruling_at_the_go): REV-COMB-4 Z3' as written plus the v1 window (<= 3.0 ms above 63.1 bar abs) and rise "
               "(10-90 % >= 0.8 ms) kept as the FA-1 class, Z3 only inside the light window; NOT EVALUATED in flight; option 2, option 3 "
               "and the damped variant not adopted"),
    "jfwd_status": ("ADOPTED by the lead at the go 2026-10-21T10:47:17Z (CHANGELOG 258 (3)): Q_JFWD, not the peak alone; on measured "
                    "stand traces a noise-driven trigger still means the inspection until a noise-floor rule is derived from a no-event "
                    "B-DPC-1 record and reviewed (TO-VERIFY); the flight consequence of a flagged first light and one Z3 event per J-FWD "
                    "assembly OPEN (lead, before flight acceptance)"),
    "open_item": "CLOSED: ADOPTED by the lead (CHANGELOG 258 (3), go 10:47:17Z); NOT EVALUATED in flight",
    "jfwd_open_item": ("Q_JFWD ADOPTED by the lead, not the peak alone (CHANGELOG 258 (3), go 10:47:17Z); a noise-driven trigger on a "
                       "measured stand trace still means the inspection until a noise-floor rule from a no-event B-DPC-1 record is "
                       "derived and reviewed (TO-VERIFY)")}


def sha(p, n=16):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


def cl_segment(line_no, start, end):
    """Quote the text of hub CHANGELOG line `line_no` from `start` up to (not including) `end` (both must occur once)."""
    lines = CL.read_text().splitlines()
    ln = lines[line_no - 1]
    assert ln.count(start) == 1, (line_no, start)
    i = ln.index(start)
    if end:
        assert ln.count(end) == 1, (line_no, end)
    j = ln.index(end, i) if end else len(ln)
    return {"changelog_line": line_no, "line_sha256_16": hashlib.sha256((ln + "\n").encode()).hexdigest()[:16], "text": ln[i:j].strip()}


def leaves(x, p=""):
    if isinstance(x, dict):
        if not x and p:
            yield p, {}
        for k, v in x.items():
            yield from leaves(v, f"{p}.{k}" if p else str(k))
    elif isinstance(x, list):
        if not x and p:
            yield p, []
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


def under(path, prefix):
    return path == prefix or path.startswith(prefix + ".") or path.startswith(prefix + "[")


def main(dry=False, pre=False):
    dry = dry or pre
    base_raw = HUB.read_bytes()
    assert sha(HUB) == V23_SHA, ("hub mechanical.json is not the v2.3 this writer was made for", sha(HUB))
    assert not HIST.exists(), ("archive target already exists", HIST)
    base = json.loads(base_raw)
    assert base["version"] == "v2.3" and base["cad_version"] == "v3.5.2"
    assert sha(V22_HIST) == V22_SHA and sha(V21_HIST) == V21_SHA
    V21 = json.loads(V21_HIST.read_text())
    kept21 = [k for k in V21 if k not in HEADER]
    assert len(kept21) == 29 and all(base[k] == V21[k] for k in kept21), "the 29 v2.1 sections are not as archived"

    # ---------------------------------------------------------------------------------------------- sources
    for k, d in base["sources_v352"].items():            # the v2.3 sources stay on the hub, unchanged
        assert sha(HUBE / d["path"]) == d["sha256_16"], ("a v2.3 source moved on the hub", k, d)
    X, src, pending = {}, {}, {}
    for k, (p, hp, s16) in {**SRC_NEW, **SCRIPTS_NEW}.items():
        hub = HUBE / hp
        s = sha(p) if p else sha(hub)
        assert s == s16, (k, p or hub, s)
        if pre and p and (not hub.exists() or sha(hub) != s):       # copied (or replaced) at the publication
            pending[k] = {"hub_path": hp, "hub_exists": hub.exists(), "hub_sha256_16_now": sha(hub) if hub.exists() else None}
        else:
            assert hub.exists() and sha(hub) == s, ("hub copy missing or different", k, hp)
        if k in SRC_NEW:
            if hp.endswith(".json"):
                X[k] = json.loads(Path(p or hub).read_text())
            src[k] = {"path": hp, "sha256_16": s}
    scr = {k: {"path": hp, "sha256_16": s16} for k, (p, hp, s16) in SCRIPTS_NEW.items()}
    TW3, TW2, E2, E1, TX5, DTX2, F1, XC, TP, CB = (X[k] for k in (
        "tap_wall_v3", "tap_wall_v2_reviewed", "lc_tb70_envelope_v2", "lc_tb70_envelope_v1", "texts_v5", "drawing_texts_v2", "c1_seat_v1",
        "c1_seat_xcheck_v1", "torch_port_bl08_v1", "combustion_v2p4c"))
    assert (TW3["version"], TW2["version"], E2["version"], TX5["version"], DTX2["version"], TP["version"]) == ("v3", "v2", "v2", "v5", "v2", "v1")
    TX4 = json.loads((HUBE / base["sources_v352"]["texts_v4"]["path"]).read_text())
    DTX1 = json.loads((HUBE / base["sources_v352"]["drawing_texts_v1"]["path"]).read_text())
    TW1 = json.loads((HUBE / base["sources_v352"]["tap_wall_v1"]["path"]).read_text())
    assert TX4["version"] == "v4" and DTX1["version"] == "v1" and TW1["version"] == "v1"
    HW17 = json.loads((HUBE / base["sources_v352"]["hardware_v352_v1.7"]["path"]).read_text())
    assert HW17["version"] == "v1.7"
    H101d = next(L for L in HW17["lines"] if L["id"] == "HW-101")
    assert CB["version"] == "v2.4c"
    GS, PT = CB["fa1_grid_statistics_v2p4c"]["v"], CB["fa1_p_torch_v2p4c"]["v"]
    Z3P = GS["proposed_Z3_prime"]
    assert GS["status"].startswith("OPEN") and GS["cases_above_all_896"] == [46, 141, 185]
    assert E2["inputs"]["combustion_json_v2p4c"]["sha256_16"] == src["combustion_v2p4c"]["sha256_16"]
    assert E2["inputs"]["tapwall_v3"]["sha256_16"] == src["tap_wall_v3"]["sha256_16"]
    assert E2["inputs"]["envelope_v1_json"]["sha256_16"] == src["lc_tb70_envelope_v1"]["sha256_16"]
    assert E2["inputs"]["margin_matrix_v352"]["sha256_16"] == src["margin_matrix_v352_rows_v8"]["sha256_16"]
    assert TP["inputs"]["c1_seat_v352_v1_json"]["sha256_16"] == src["c1_seat_v1"]["sha256_16"]
    assert XC["inputs"]["c1_seat_v352_v1.json"] == src["c1_seat_v1"]["sha256_16"]
    assert TW3["inputs"]["tapwall_v2_json_reviewed"]["sha256_16"] == src["tap_wall_v2_reviewed"]["sha256_16"]
    others = {}
    for n in ("combustion.json", "electronics.json", "gnc.json", "ENGINE-BASELINE-v0.json"):
        p = HUBE / "interfaces" / n
        d = json.loads(p.read_text())
        others[n] = {"version": d.get("version"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    assert others["combustion.json"]["sha256"][:16] == src["combustion_v2p4c"]["sha256_16"]
    assert others["electronics.json"]["sha256"][:16] == E2["F4_abort_set"]["electronics_source"]["sha256_16"]

    out = copy.deepcopy(base)
    out.update({"version": "v2.4", "date": "2026-10-21",
                "supersedes": (f"v2.3 (2026-10-21, sha256/16 {V23_SHA}; archived by rename as 03-cad/v3.5.2/history/mechanical.json.{V23_SHA}); "
                               f"v2.2 (2026-10-20, {V22_SHA}) and v2.1 (2026-10-13, {V21_SHA}) archived as 03-cad/v3.5.2/history/"
                               "mechanical.json.<sha256/16>"),
                "status": ("v3.5.2 J-FWD follow-ups issue (lead brief 2026-10-21T08:05:00Z F1-F6; REV-COMB-4 R4-01 / R4-02 / R4-10 relayed "
                           "08:39:41Z) on the FINAL 03-cad v3.5.2 set (no CAD change): SIM + CALC + DERIVED + DESIGN as tagged; physical "
                           "validation pending (bench and founder test lists); margins are model results, not test results; negatives are "
                           "shown as found")})
    out["reading_rule_v352"] = base["reading_rule_v352"] + (
        " v2.4: a patch on v2.3 (the J-FWD follow-ups): only the leaves named in superseded_v2p3_entries change (each v2.3 value kept whole "
        "in superseded_v2p3_values, not to be used for v3.5.2); lc_tb70_envelope_v352, c1_seat_v352, torch_port_bl08_v352 and "
        "followups_basis_v352 are new; lc_tb70_envelope_v352 supersedes 04-fea/v352/lc_tb70_envelope_v1.json for v3.5.2.")
    sc = dict(base["scripts_v352"])
    assert sc["writer"] == "03-cad/v3.5.2/src/calcs/write_mechanical_json_v352.py (v2.3)"
    sc.update({"writer": "03-cad/v3.5.2/src/calcs/write_mechanical_json_v352.py (v2.4)", "writer_sha256_16": sha(Path(__file__)),
               "jfwd": ("04-fea/v352/jfwd_*_v352.py (relax v8, rows v8, K_js5 v3, spring v5, head fillet v2, screw LCF v3, P+Q band v1, R6 "
                        "companions v1, J-F1b / LOCTITE v1, tap wall v3 (R4-01))"),
               "texts": "04-fea/v352/texts/item_c_tf1_texts_v352.py (v5; also writes the drawing-text set v2) and tf1_exposure_v352.py (v2)",
               "drawing_texts": "03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v2.json",
               "lc_tb70_envelope": "04-fea/v352/lc_tb70_envelope.py (v2; inside_v2() is the post-run classifier)",
               "c1seat": "04-fea/v352/c1seat/c1_seat_v352.py (F1), c1_seat_xcheck_v352.py (F1 cross-check), torch_port_bl08_v352.py (F2)",
               "scripts_sha256_16_v2p4": scr})
    out["scripts_v352"] = sc
    out["inputs_read_v352"] = others
    out["sources_v352"] = {**base["sources_v352"], **src}

    # ---------------------------------------------------------------------------------------------- jfwd_v352 patches
    JB = base["jfwd_v352"]
    TWg1 = min((v["TC02_thread_T"]["MS_y"], k) for k, v in TW1["rows"]["3750"]["cases"].items() if k.endswith("ruled_+/-0.25deg_net_GOVERNING"))
    assert JB["tap_wall"] == {"governing_case": TWg1[1], "MS_y": TWg1[0], "walls_mm": TW1["walls_mm"], "verdict": TW1["verdict"],
                              "to_confirm": "P_torch and its distribution along the torch passage (REV-COMB-4)",
                              "R11": "stays v1 until REV-COMB-4; if its bounding P_torch is above 102 bar abs, Mechanical re-runs the tap-wall check when the lead relays it"}
    G = TW3["rows"]["3750"]["governing"]
    RA = TW3["R4-01_additions"]
    LIG = RA["(a)_ligament_lowest_local_natural_frequency"]
    f_min = min(c["f_kHz"] for c in LIG["cases"].values())
    PTS = RA["(c)_P_torch_statement_verbatim_REV-COMB-4"]
    assert PTS.rstrip(".") == PT["design_case"] and RA["(b)_NOT_MODELLED"] == PT["not_modelled"]
    assert TW3["rows"]["3750"]["flags_within_0.05_or_negative"] == [] and TW3["rows"]["4096"]["flags_within_0.05_or_negative"] == []
    assert TW3["walls_mm"] == TW1["walls_mm"] and TW3["rows"]["3750"]["v1_governing_record"]["TC02_thread_T"]["MS_y"] == TWg1[0]
    G2 = TW2["rows"]["3750"]["governing"]
    assert (G2["case"], G2["TC02_thread_T"], G2["worst_with_screw_T_sensitivity"]) == (G["case"], G["TC02_thread_T"], G["worst_with_screw_T_sensitivity"])
    SW = G["worst_with_screw_T_sensitivity"]
    tap_wall = {
        "source": {**src["tap_wall_v3"], "script": scr["jfwd_tapwall"],
                   "records": {"v2_the_row_REV-COMB-4_read": {**src["tap_wall_v2_reviewed"], "script": scr["jfwd_tapwall_v2_reviewed"]},
                               "v1": {**base["sources_v352"]["tap_wall_v1"], "MS_y_at_P_torch_102bar_abs_rows_v7": TWg1[0],
                                      "status": "SUPERSEDED for the passage (102 bar abs does not cover it, REV-COMB-4 R4-01)"}}},
        "P_torch_R4-01": PTS,
        "governing_case": G["case"], "MS_y": G["TC02_thread_T"]["MS_y"], "MS_u": G["TC02_thread_T"]["MS_u"],
        "T_C_TC02_thread": G["TC02_thread_T"]["T_C"],
        "screw_T_sensitivity_worst": SW,
        "information_4096N_column": {k: TW3["rows"]["4096"]["governing"][k] for k in ("case", "TC02_thread_T")},
        "flags_within_0.05_or_negative": {"3750_N_column": TW3["rows"]["3750"]["flags_within_0.05_or_negative"],
                                          "4096_N_information_column": TW3["rows"]["4096"]["flags_within_0.05_or_negative"]},
        "walls_mm": TW3["walls_mm"],
        "ligament_lowest_local_natural_frequency_R4-01": {"value": LIG["value"], "tag": LIG["tag"], "lowest_case_kHz": f_min,
                                                          "against_the_passage": LIG["against_the_passage"]},
        "NOT_MODELLED_R4-01": RA["(b)_NOT_MODELLED"], "NOT_MODELLED_note": RA["(b)_source"],
        "verdict": TW3["verdict"],
        "to_confirm": ("none for P_torch: the REV-COMB-4 R4-01 design case (combustion v2.4c fa1_p_torch_v2p4c); the NOT MODELLED items are "
                       "outside the row's basis, not covered by it"),
        "R11": ("CLOSED: REV-COMB-4's bounding P_torch (FA1S 151.04 bar abs uniform over the passage) is above 102 bar abs; Mechanical re-ran "
                "the row on the lead's relay (F5: v2 at 2026-10-21T08:14:51Z, read by REV-COMB-4; v3 adds the R4-01 items); R4-01 closes with "
                "this publication (lead CHANGELOG 256 (5))"),
        "tags": "CALC on FEA3D SIM screw forces (rows v8) and SIM temperatures; SF 1.0 on Fty / Ftu; not physical approval"}
    C94_4, C6_4 = TX4["item_C"]["C9_founder_texts_remap_v352"]["(4)_post_abort_joint_replacement"], TX4["item_C"]["C6_founder_action_list_related"]
    C94_5, C6_5 = TX5["item_C"]["C9_founder_texts_remap_v352"]["(4)_post_abort_joint_replacement"], TX5["item_C"]["C6_founder_action_list_related"]
    assert JB["founder_rules"]["post_abort_joint_replacement"] == C94_4 and JB["founder_rules"]["C6"] == C6_4
    assert C94_5 in C6_5 and C94_4 in C6_4 and C6_5.replace(C94_5, "") == C6_4.replace(C94_4, "")
    for k in ("(1)_HW-170_orientation", "(2)_HW-170_single_use", "(3)_J-F1b", "(5)_stand_T0_cross_reference", "(6)_TC-02_select_fit_band_R2"):
        assert TX5["item_C"]["C9_founder_texts_remap_v352"][k] == TX4["item_C"]["C9_founder_texts_remap_v352"][k]
    assert TX5["item_C"]["C4_assembly_step_founder_procedure"] == JB["founder_rules"]["C4_procedure"] and TX5["T-F1"] == JB["T-F1_R9"]["text"]
    ACT = "after any Pc above 60 bar abs the line-231 J-FWD inspection (C6 (2) list)"
    assert ACT in JB["hardware"]["HW-101"]["action"]
    NOTE = DTX2["ENG-HW-101-IN718"]["jfwd_replace_rule_note_LC-TB70_v2"]
    assert f"'{ACT}'" in NOTE and "Q_JFWD" in NOTE and "60.0 bar abs" in NOTE
    assert set(DTX2) == set(DTX1) and all(DTX2[k] == DTX1[k] for k in DTX1 if k not in (
        "version", "ENG-HW-101-IN718", "assembly_and_founder_rules", "basis", "source"))
    assert {k: v for k, v in DTX2["ENG-HW-101-IN718"].items() if k not in ("jfwd_replace_rule_note_LC-TB70_v2", "tap_wall_note_v3")} == DTX1["ENG-HW-101-IN718"]
    TAPN = DTX2["ENG-HW-101-IN718"]["tap_wall_note_v3"]          # the hardware v1.7 HW-101 tap-wall v1 strings (P_torch 102 bar abs)
    OX_OLD = f"tap-wall v1 MS_y {TWg1[0]:+.3f}"
    i0 = H101d["note"].index("Tap wall to the torch passage (jfwd_tapwall_v352_v1.json")
    NOTE_OLD = H101d["note"][i0:H101d["note"].index("(REV-COMB-4).", i0) + len("(REV-COMB-4).")]
    assert OX_OLD in H101d["oxygen_service"] and "102 bar abs" in NOTE_OLD and "TO-CONFIRM" in NOTE_OLD
    assert f"'{OX_OLD}' (oxygen_service)" in TAPN and f"'{NOTE_OLD}' (note)" in TAPN and src["tap_wall_v3"]["sha256_16"] in TAPN
    assert f"FA1S 151.04 bar abs uniform over the passage" in TAPN and f"MS_y {G['TC02_thread_T']['MS_y']:+.3f} / MS_u {G['TC02_thread_T']['MS_u']:+.3f}" in TAPN
    assert f"MS_y {SW['MS_y']:+.3f} with the screw temperature" in TAPN and TAPN.isascii()
    OI4, OI5 = TX4["item_C"]["C8_jfwd_drawing_texts_rev5"]["open_items"], TX5["item_C"]["C8_jfwd_drawing_texts_rev5"]["open_items"]
    assert OI5[:-2] == OI4 and f"'{ACT}'" in OI5[-2] and f"'{OX_OLD}'" in OI5[-1] and f"'{NOTE_OLD}'" in OI5[-1]
    AF1, AF2 = DTX1["assembly_and_founder_rules"], DTX2["assembly_and_founder_rules"]
    assert AF1["post_abort_joint_replacement"] == C94_4 and AF2["post_abort_joint_replacement"] == C94_5
    assert {k: v for k, v in AF2.items() if k != "post_abort_joint_replacement"} == {k: v for k, v in AF1.items() if k != "post_abort_joint_replacement"}
    TSH = JB["hardware"]["texts_superseding_hardware_strings"]
    TSH_TAIL = " (data/hardware_v352.json is not edited; the lead rules any data update)"
    assert TSH.endswith(TSH_TAIL) and TSH.startswith("03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json: ")
    tsh = ("03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v2.json: " + TSH[len("03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json: "):-len(TSH_TAIL)]
           + f"; ENG-HW-101-IN718.jfwd_replace_rule_note_LC-TB70_v2: the hardware v1.7 HW-101 action string '{ACT}' is superseded by the "
           "LC-TB70 v2 J-FWD replace rule (C9 (4); lc_tb70_envelope_v352.jfwd_replace_rule_v2)"
           + f"; ENG-HW-101-IN718.tap_wall_note_v3: the hardware v1.7 HW-101 tap-wall v1 strings (oxygen_service '{OX_OLD}' and the note "
           "sentence on the tap wall, P_torch 102 bar abs TO-CONFIRM) are superseded by tap wall v3 (P_torch FA1S 151.04 bar abs uniform "
           "over the passage, REV-COMB-4 R4-01; jfwd_v352.tap_wall)" + TSH_TAIL)
    assert JB["drawing_texts"] == ("03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json (TC-02 plug OD band, HW-170 orientation and single-use, "
                                   "the assembly and founder rules); 04-fea/v352/texts/item_c_tf1_texts_v352_v4.json item_C C8 (rev-5 texts) and "
                                   "C9 (re-map texts)")
    JO = out["jfwd_v352"]
    tap_wall["hardware_strings_superseded"] = (
        f"the hardware v1.7 HW-101 strings '{OX_OLD}' (oxygen_service) and the note's tap-wall sentence (P_torch 102 bar abs, TO-CONFIRM) "
        "are superseded by 03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v2.json ENG-HW-101-IN718.tap_wall_note_v3 and texts v5 C8 "
        "open_items[-1]; data/hardware_v352.json is not edited (no CAD change; the lead rules any data update)")
    JO["tap_wall"] = tap_wall
    JO["founder_rules"]["post_abort_joint_replacement"] = C94_5
    JO["founder_rules"]["C6"] = C6_5
    JO["hardware"]["texts_superseding_hardware_strings"] = tsh
    JO["drawing_texts"] = ("03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v2.json (TC-02 plug OD band, HW-170 orientation and single-use, the "
                           "J-FWD replace rule note and the tap-wall note on ENG-HW-101-IN718, the assembly and founder rules); 04-fea/v352/texts/"
                           "item_c_tf1_texts_v352_v5.json item_C C8 (rev-5 texts) and C9 (re-map texts; C9 (4) / C6 (4) restated to the "
                           "LC-TB70 v2 J-FWD replace rule and the F4 abort set)")

    # ---------------------------------------------------------------------------------------------- LC-TB70 envelope v2
    Z = E2["Z3_v2"]
    JR = E2["jfwd_rule_v2"]
    JG = JR["grid"]
    F4 = E2["F4_abort_set"]
    NS = E2["noise_sensitivity_measured_traces"]
    O2 = E2["option_2_shape_limits"]
    GR = E2["grid_reproduction"]
    assert Z["grid"]["n_inside_v2"] == Z["grid"]["n_inside_z3prime"] == 896 and Z["grid"]["S_max_bar_abs"] == GR["grid_max_0p02_50ms"]["S_bar_abs"]
    assert Z["criterion"]["ceiling_bar_abs"] == 88.1 and Z["criterion"]["ESP_bound_bar_abs"] == 151.04 and Z["criterion"]["period_domain_ms"] == [0.02, 50.0]
    assert E2["grid_statistics_reproduced"]["n_peak_above_75.519_63.1_60"] == GS["cases_above_all_896"]
    assert (JG["n_Q_JFWD_above_60_of_896"], JG["n_peak_above_60_of_896"], JG["n_Q_above_60_with_peak_le_60"]) == (298, 185, 113)
    v1_now = {c["case"]: c["v2"]["Q_JFWD_bar_abs"] for c in E2["v1_cases_rechecked"]["cases"] if c["v2"]["jfwd_rule_triggered"] and not c["v1"]["jfwd_rule"]}
    assert v1_now and all(c["v2"]["inside"] for c in E2["v1_cases_rechecked"]["cases"])
    status_z3 = ("PROPOSED by Mechanical: REV-COMB-4 Z3' adopted as written, the v1 window (<= 3.0 ms above 63.1 bar abs) and rise (10-90 % "
                 ">= 0.8 ms) kept as the FA-1 class; OPEN until the lead rules at Mechanical's pre-publication post (CHANGELOG 256 (3); "
                 "combustion v2.4c fa1_grid_statistics_v2p4c.status)") if LEAD_RULING_Z3 is None else LEAD_RULING_Z3["status"]
    out["lc_tb70_envelope_v352"] = {
        "source": {**src["lc_tb70_envelope_v2"], "script": scr["lc_tb70_envelope"]},
        "supersedes": (f"04-fea/v352/lc_tb70_envelope_v1.json {src['lc_tb70_envelope_v1']['sha256_16']} (kept on the hub as the record); its "
                       "script 855ebe04dfe5dbd0 is kept as 04-fea/v352/history/lc_tb70_envelope.py.855ebe04dfe5dbd0"),
        "status": E2["status"],
        "zones": E2["zones"],
        "Z3_v2": {"status": status_z3, "REV-COMB-4_Z3_prime_verbatim": Z3P, "criterion": Z["criterion"],
                  "why_the_kept_conditions": Z["why_the_kept_conditions"],
                  "period_domain_why": " ".join(E2["basis"][E2["basis"].index("Period domain 0.02-50 ms"):E2["basis"].index("MEASURED TRACES:")].split()),
                  "grid": {k: Z["grid"][k] for k in ("n_inside_v2", "n_inside_z3prime", "n_inside_v1", "S_max_bar_abs", "margin_to_FA1S_bar",
                                                     "window_above_63p1_max_ms", "rise_10_90_min_ms", "below_0p02ms_max", "T_50_2000ms_max", "tag")}
                          | {"worst_case": Z["grid"]["worst_cases"][0],
                             "periods_where_grid_within_50bar_of_FA1S_ms": GR["periods_where_grid_within_50bar_of_FA1S_ms"],
                             "periods_where_grid_within_25bar_of_FA1S_ms": GR["periods_where_grid_within_25bar_of_FA1S_ms"],
                             "T_le_0p1ms_max_published_grid": GR["T_le_0p1ms_max_published_grid"]},
                  "text": E2["Z3_v2_text"]},
        "Z3_alternatives_not_adopted": {"option_2_shape_limits": {k: O2[k] for k in (
            "verdict", "smallest_shape_limit_box_admitting_the_grid", "corner_trapezoid_ESP_bar_abs", "corner_trapezoid_at_T_ms",
            "time_limit_at_88.1_rise0.8_for_FA1S", "ceiling_at_v1_shape_limits_for_FA1S_bar_abs", "rise_needed_at_grid_peak_and_time_above_ms")},
            "option_3_higher_FA1S": E2["option_3_higher_FA1S"],
            "damped_ESP_variant": {"information": NS["damped_alternative_information"],
                                   "status": "NOT ADOPTED: needs the structure's damping shown (MISSING); OPEN for the lead"}},
        "jfwd_replace_rule_v2": {k: JR[k] for k in ("rule", "quantity", "level_bar_abs", "duration", "signal", "normal_lights",
                                                     "peak_only_alternative_for_the_lead", "jfwd_band", "action_source")}
                                | {"basis_minimum_at_60bar_nominal_factors": JR["basis_in_the_jfwd_rows"]["minimum_at_60bar_nominal_factors"],
                                   "basis_rule_form": JR["basis_in_the_jfwd_rows"]["rule_form"],
                                   "above_the_level": JR["basis_in_the_jfwd_rows"]["above_the_level"],
                                   "grid": {k: JG[k] for k in ("n_Q_JFWD_above_60_of_896", "n_peak_above_60_of_896", "n_Q_above_60_with_peak_le_60",
                                                                "lowest_peak_with_Q_above_60_bar_abs", "Q_over_peak_gauge_ratio_max", "S_band_max_bar_abs",
                                                                "band_sensitivity_0p1_1ms_n_above_60", "band_sensitivity_0p02_0p5ms_n_above_60",
                                                                "ideal_1kHz_threshold_flagging_every_Q_above_60",
                                                                "n_Q_le_60_flagged_by_that_threshold_best_phase",
                                                                "normal_light_at_MEOP_linear_rise_Q_JFWD_bar_abs",
                                                                "linear_rise_to_MEOP_held_trips_the_rule_below", "tag")},
                                   "text": E2["jfwd_rule_v2_text"],
                                   "supersedes": "v1 'any head excursion above 60.0 bar abs: replace all J-FWD screws (HW-101) and gauge the TC-01 holes / TC-02 taps before the next run'",
                                   "v1_cases_that_now_trigger_it_Q_JFWD_bar_abs": v1_now,
                                   "v1_cases_note": E2["v1_cases_rechecked"]["note"],
                                   "status": ("Q_JFWD PROPOSED by Mechanical (the head peak alone: the lead's alternative); the flight consequence "
                                              "of a flagged first light and one Z3 event per J-FWD assembly OPEN (lead)") if LEAD_RULING_Z3 is None
                                   else LEAD_RULING_Z3["jfwd_status"]},
        "F4_abort_set": {k: F4[k] for k in ("lead_provisional", "verdict", "reasons", "beside_the_abort_set", "observation_for_the_lead")}
                        | {"electronics_source": {k: F4["electronics_source"][k] for k in ("path", "sha256_16")}},
        "measured_traces": {k: NS[k] for k in ("statement", "tone_amplitude_that_trips_the_rule_on_that_light_bar",
                                                "tone_amplitude_that_takes_the_worst_grid_case_past_FA1S_at_3.5ms_bar", "white_noise_example",
                                                "stand_use", "tag")},
        "rules": E2["rules"],
        "how_to_use": E2["how_to_use"],
        "plateau_and_burn_on_families": E2["plateau_and_burn_on_families"]["reading"],
        "margins": ("the per-zone cells are the published v3.5.2 margin matrix (04-fea/assembly3d_v352_rows_v8/tables/margin_matrix_v352.json "
                    f"{src['margin_matrix_v352_rows_v8']['sha256_16']}); no cell changes in v2.4"),
        "combustion_input": ("interfaces/combustion.json v2.4c 661db0a593462382: fa1_grid_statistics_v2p4c (Z3' proposal, status OPEN) and "
                             "fa1_p_torch_v2p4c; the FA-1 grid histories are the v2.4b set (unchanged in v2.4c)"),
        "tags": "DERIVED on SIM (ASSUMED construct; grid counts are not probabilities); not physical approval"}
    assert out["lc_tb70_envelope_v352"]["Z3_v2"]["period_domain_why"].startswith("Period domain 0.02-50 ms (REV-COMB-4's, ADOPTED")

    # ---------------------------------------------------------------------------------------------- F1 (C1 seat) and its cross-check
    xr = XC["runs"]
    seat_drifts = {r: v["seat_drifts_K_unchanged"] for r, v in xr.items()}
    for r, v in xr.items():
        assert v["seat_points"] == {"diaphragm_history_max_abs_diff_K_vs_F1_json": 0.0, "seat_points_at_events_max_abs_diff_K_vs_F1_json": 0.0}
        assert v["frames"]["max_abs_frd_minus_dat_time_s"] == 0.0 and v["numbering"]["NMON_equals_meta_node_plus_1_all"]
        for dk, dv in v["seat_drifts_K_unchanged"].items():
            ev = F1["runs"][r]["drifts"][dk]["diaphragm_zt-9.5"]["dT_K"]
            assert abs(ev - dv) < 5e-5, (r, dk, ev, dv)
    rz2 = {r: [k for k in seat_drifts[r] if k.startswith(("rezero2_end->", "stand_rezero2_end->"))] for r in xr}
    foot = {r: {dk: round(xr[r]["MON_proxy_drifts"][f"{dk}|T1_head_top_bracket_foot"]["at_monitor_node_K"] - seat_drifts[r][dk], 4) for dk in rz2[r]}
            for r in xr}
    bore = {r: {dk: round(xr[r]["MON_proxy_drifts"][f"{dk}|head_bore_N2O"]["at_monitor_node_K"] - seat_drifts[r][dk], 4) for dk in rz2[r]}
            for r in xr}
    foot_max = max(abs(v) for d in foot.values() for v in d.values())
    bore_max = max(abs(v) for d in bore.values() for v in d.values())
    assert foot_max <= 0.3 < bore_max
    mon_change = {r: max(((abs(e["change_K"]), k, e["change_K"]) for k, e in v["MON_proxy_drifts"].items()))[1:] for r, v in xr.items()}
    out["c1_seat_v352"] = {
        "source": {"F1": {**src["c1_seat_v1"], "script": scr["c1_seat"]}, "cross_check": {**src["c1_seat_xcheck_v1"], "script": scr["c1_seat_xcheck"]}},
        "seat_point": ("the C1 Pc seat diaphragm point r 25.0, z = zt - 9.5 (A1 zt {:.4f}, B1 zt {:.4f} mm) in an M_AL6061_T6 CAX6 element; "
                       "quadratic shape functions in space, linear in time between frd frames [SIM]").format(F1["runs"]["A1_NF2b"]["zt_mm"],
                                                                                                         F1["runs"]["B1_R4_GVLO"]["zt_mm"]),
        "runs": {r: {"dir": F1["runs"][r]["dir"], "bound": F1["runs"][r]["bound"]["tag"], "diaphragm_max": F1["runs"][r]["diaphragm_max"],
                     "seat_drifts_K": seat_drifts[r]} for r in xr},
        "C1_bar_per_K_typ_DATASHEET": F1["C1_bar_per_K_typ"], "k_ASSUMED": F1["k_sweep"],
        "cross_check_verdict": XC["verdict"], "root_cause": XC["root_cause"],
        "extraction_caveat": "the +/-0.6 K extraction caveat of the F1 message (08:02:01Z) is WITHDRAWN for the seat values (seat points recomputed: 0.0 K)",
        "MON_proxies_restated": {"largest_change_at_the_events_K": mon_change,
                                 "rise_vs_ARM_max_abs_change_K": {r: v["MON_proxy_rise_vs_ARM_max_abs_change_K"] for r, v in xr.items()},
                                 "where": "c1_seat_xcheck_v352_v1.json runs.<run>.MON_proxy_drifts (every drift, F1 value at the meta node and the value at the monitor's own node)"},
        "proxy_recommendation": (f"T1_head_top_bracket_foot stays the proxy at its own node: within {foot_max:.3f} K of the seat on the "
                                 "re-zero2-referenced drifts (foot minus seat, K: "
                                 + "; ".join(f"{r} " + " / ".join(f"{dk} {v:+.3f}" for dk, v in foot[r].items()) for r in foot)
                                 + f"); head_bore_N2O is not representative (up to {bore_max:.2f} K from the seat on the same drifts) [DERIVED on SIM]"),
        "T0": ("T0 independence: not in c1_seat_v352_v1.json (the F1 message of 08:02:01Z gave a first-order estimate); a flight T0 range and a "
               "T0 0 / 40 C re-run (new FE) are not done: OPEN"),
        "inputs": ("the three NF2b thermal run folders in /home/claude/work/mechanical/runs/thermal (Mechanical work tree; frd / dat / inp / "
                   "meta / monitors.csv sha256/16 in the cross-check json)"),
        "tags": "SIM (FE nodal results of the UPPER-bound heat-transfer runs), DERIVED comparisons; not physical approval"}

    # ---------------------------------------------------------------------------------------------- F2 (torch port, BL-08)
    TPP, BL = TP["torch_port"], TP["BL-08"]
    assert BL["temperature"].startswith("MISSING")
    out["torch_port_bl08_v352"] = {
        "source": {**src["torch_port_bl08_v1"], "script": scr["torch_port_bl08"]},
        "torch_port": {k: TPP[k] for k in ("geometry", "points_r25", "summary", "MISSING", "what_it_would_take")},
        "torch_port_reading": ("the r 25 head-metal rises are the head's contribution only, NOT bounds on the torch-port rise (the local heat and "
                               "its net sign are MISSING); the predecessor's 'lower bound' reading is withdrawn"),
        "BL-08": {k: BL[k] for k in ("part", "location", "temperature", "drivers_not_modelled", "what_it_would_take")}
                 | {"for_U570": BL["for_U570"]["note"]},
        "tags": "SIM (F1 values), DERIVED (differences), MISSING as stated; not physical approval"}
    assert "withdrawn" in TP["basis"]

    # ---------------------------------------------------------------------------------------------- rulings, requests, open items
    LR = dict(base["lead_rulings_quoted_v352"])
    LR.update({
        "Z3_restated_condition_256_3": cl_segment(256, "(3) 253 (7)(i) ride-through stays ADOPTED", "(4) 253 (8) CORRECTED"),
        "R4-10_wording_256_4": cl_segment(256, "(4) 253 (8) CORRECTED (R4-10)", "(5) ROUTING."),
        "routing_mechanical_256_5": cl_segment(256, "(5) ROUTING. Mechanical successor", "Electronics v2.12: R4-09"),
        "F1_and_F5_record_256_6": cl_segment(256, "(6) MECHANICAL: the re-map agent sent F1", "(7) REV-GNC-7 resumed"),
        "combustion_v2p4c_257_1": cl_segment(257, "(1) COMBUSTION v2.4c PUBLISHED", "(2) PURGE CONDITION (d)"),
        "followups_brief_2026-10-21T08:05:00Z": {
            "source": ("the lead's brief to the Mechanical successor (message 2026-10-21T08:05:00Z; not a CHANGELOG line, CHANGELOG 256 (6) "
                       "records it): PARAPHRASED here"),
            "F1": "cross-check the F1 frd monitor-node values against monitors.csv and the .dat NODE PRINT times (the F1 +/-0.6 K caveat)",
            "F2": "the torch-port dT and the BL-08 temperature (253 (10), MISSING in the re-map)",
            "F3": "restate the 60 bar abs joint-replacement rule: quantity, level, duration, basis and the logged signal (REV-COMB-4 interim (f)(ii))",
            "F4": "confirm the TB-state abort set (253 (8), lead PROVISIONAL)",
            "F5": "the tap-wall row at the REV-COMB-4 P_torch (FA1S 151.04 bar abs uniform over the passage; R11)",
            "F6": "restate Z3 in the LC-TB70 envelope (REV-COMB-4 R4-02)",
            "order_and_rules": "F5 first; work tree only until the lead's go after ONE pre-publication post; paper / Python only, no FE, no ccx"},
        "relay_2026-10-21T08:39:41Z": {
            "source": "the lead's relay of the REV-COMB-4 final review (message 2026-10-21T08:39:41Z): PARAPHRASED, the quoted sentences VERBATIM",
            "R4-01": ("add the ligament's lowest local natural frequency (with its tag) and the NOT MODELLED list to the tap-wall row; reviewer "
                      "text verbatim: '" + PTS + "'"),
            "R4-02": ("reviewer Z3' verbatim: '" + Z3P + "'; 'Choose the domain a post-run check on the logged signal can actually evaluate, "
                      "and say why.' 'Say whether you adopt Z3' as written. If you propose something else, give its numbers against the grid.' "
                      "Electronics re-classifies the 10 S6R runs and the 29-33 N-04 burn-on cases: give the exact criterion and logged signal"),
            "R4-10": "section 5 (f)(ii): state whether the 60 bar rule is meant for normal-light transients; the logged quantity and threshold",
            "rest": "'Nothing else in the review is yours. Keep the task order and the rest of your brief as they are.'"}})
    if LEAD_RULING_Z3 is not None:
        LR["Z3_and_jfwd_rule_ruling_at_the_go"] = cl_segment(*LEAD_RULING_Z3["quote"])
        q = LR["Z3_and_jfwd_rule_ruling_at_the_go"]["text"]
        assert q.startswith("Z3 RULING: Z3 v2 ADOPTED as proposed") and "Q_JFWD RULING: the J-FWD replace rule uses Q_JFWD" in q
        assert "not the peak alone" in q and "896 / 896 grid cases inside, ESP max 146.881 bar abs at 3.5 ms, margin 4.159 bar" in q
        assert q.endswith("texts v5 C8 [10] / [11].") and q.isascii()
    out["lead_rulings_quoted_v352"] = LR

    RQ = list(base["requests_v352"])
    assert RQ[0].startswith("REQUEST Combustion (REV-COMB-4): P_torch and its distribution along the torch passage") and len(RQ) == 4
    RQ[0] = (f"CLOSED (REV-COMB-4 R4-01; combustion v2.4c fa1_p_torch_v2p4c): P_torch during FA-1 = FA1S 151.04 bar abs uniform over the "
             f"passage; the TC-02 tap-wall row re-run at it (04-fea/v352/jfwd_tapwall_v352_v3.json): MS_y {G['TC02_thread_T']['MS_y']:+.3f} / "
             f"MS_u {G['TC02_thread_T']['MS_u']:+.3f} ({G['case'].split('|')[0]}, TC-02 thread temperature {G['TC02_thread_T']['T_C']} C), "
             f"screw-temperature sensitivity MS_y {SW['MS_y']:+.3f} ({SW['case'].split('|')[0]}, {SW['T_C']} C), 0 flags [CALC on SIM]; "
             f"ligament lowest local natural frequency {f_min} kHz on the extreme bounding strip [CALC, edges and span ASSUMED].")
    eg = Z["grid"]
    RQ += [
        ("REQUEST Electronics (v2.12; lead 256 (5)): re-classify the 10 S6R runs and the 29-33 N-04 burn-on cases against Z3 v2 once the lead "
         "has ruled (lc_tb70_envelope_v352.Z3_v2.criterion: the SIL plant head pressure at the 25 us step from before the light, the light "
         "window, the published 406-period grid; inside_v2() in 04-fea/v352/lc_tb70_envelope.py); log Q_JFWD per run "
         "(lc_tb70_envelope_v352.jfwd_replace_rule_v2.signal: stand B-DPC-1 DC-restored with C1 after the no-event noise check, TO-VERIFY); "
         f"state the flight LIGHT_SPIKE threshold from the C1 chain model on the 896 grid (TO-VERIFY; ideal sampler "
         f"{JG['ideal_1kHz_threshold_flagging_every_Q_above_60']} bar abs, information)."),
        ("INFORMATION Founder / test owner: the J-FWD replace rule (C9 (4) / C6 (4); the ENG-HW-101-IN718 drawing note) replaces the v1 "
         "'any head excursion above 60.0 bar abs' rule; the TB-state abort set is CONFIRMED with PC_SENSOR on the HIGH side (F4); the stand "
         "use of the Z3 v2 / Q_JFWD post-run checks needs a no-event B-DPC-1 record first (TO-VERIFY).")]
    out["requests_v352"] = RQ

    OI = list(base["open_items_v352"])
    assert OI[4] == "tap wall: stays v1 (R11); P_torch and its distribution TO-CONFIRM (REV-COMB-4)"
    assert OI[12] == "Electronics v2.11 items for Mechanical go to REV-COMB-4 first (R12); lc_tb70_envelope_v1.json unchanged"
    assert OI[13].startswith("ROUTED to Mechanical by lead CHANGELOG 253 (10)") and len(OI) == 14
    OI[4] = (f"tap wall: R4-01 closes with this publication (tap wall v3 at P_torch FA1S 151.04 bar abs uniform: MS_y "
             f"{G['TC02_thread_T']['MS_y']:+.3f} / MS_u {G['TC02_thread_T']['MS_u']:+.3f} {G['case'].split('|')[0]}, screw-temperature "
             f"sensitivity {SW['MS_y']:+.3f} {SW['case'].split('|')[0]}, 0 flags [CALC on SIM]); NOT MODELLED (R4-01): "
             + ", ".join(RA["(b)_NOT_MODELLED"]))
    OI[12] = (f"Z3 v2 (lc_tb70_envelope_v352): REV-COMB-4 Z3' adopted as written with the v1 window / rise kept ({eg['n_inside_v2']} of 896 "
              f"grid cases inside, ESP max {eg['S_max_bar_abs']} bar abs, margin {eg['margin_to_FA1S_bar']} bar [DERIVED on SIM]): "
              + ("OPEN until the lead rules (256 (3))" if LEAD_RULING_Z3 is None else LEAD_RULING_Z3["open_item"])
              + f"; lc_tb70_envelope_v1.json {src['lc_tb70_envelope_v1']['sha256_16']} superseded (kept on the hub)")
    OI[13] = ("ANSWERED in v2.4 (lead CHANGELOG 253 (8) / (10)): the C1 seat point and its dT history (F1) with the cross-check (neither time "
              "shifted; seat values unchanged; the +/-0.6 K caveat WITHDRAWN; the MON proxies re-stated) [c1_seat_v352]; the torch-port dT "
              "(the head's contribution only, NOT a bound: the local torch heat and the 070BG temperature MISSING) and the BL-08 temperature "
              "(MISSING; what it would take stated) [torch_port_bl08_v352]; R3-02: the TB-state abort set CONFIRMED with PC_SENSOR HIGH (F4); "
              "the 60 bar abs rule restated as the J-FWD replace rule, not meant for normal lights (R4-10) [lc_tb70_envelope_v352]. "
              "OPEN: a flight T0 range and a T0 0 / 40 C re-run (new FE) for the T0 independence")
    OI += [
        (f"J-FWD replace rule quantity: Q_JFWD ({JG['n_Q_JFWD_above_60_of_896']} of 896 grid cases) proposed, or the head peak alone "
         f"({JG['n_peak_above_60_of_896']}): "
         + ("lead decision" if LEAD_RULING_Z3 is None else LEAD_RULING_Z3["jfwd_open_item"])
         + "; the flight consequence of a flagged first light (the relight on a used joint) and one Z3 event per J-FWD assembly (line-231 "
           "one-off basis): OPEN (lead)"),
        ("measured traces: the undamped Z3 v2 / Q_JFWD tests integrate trace noise (lc_tb70_envelope_v352.measured_traces); the stand use "
         "follows a no-event B-DPC-1 record through inside_v2 (TO-VERIFY); a damped ESP variant needs the structure's damping (MISSING): NOT "
         "ADOPTED, OPEN for the lead"),
        "J-FWD band 0.2-0.5 ms ASSUMED (no v3.5.2 J-FWD modal in this package): TO-VERIFY",
        ("F4 observation: a shutdown of any cause from a case hotter than the rows' soak basis is outside the rows; a case-TC-at-shutdown "
         "limit would state it (not derived: OPEN, Mechanical, next round)")]
    out["open_items_v352"] = OI

    out["followups_basis_v352"] = {
        "brief": ("lead 2026-10-21T08:05:00Z F1-F6 and the 08:39:41Z relay (lead_rulings_quoted_v352.followups_brief_2026-10-21T08:05:00Z, "
                  ".relay_2026-10-21T08:39:41Z)"),
        "results": {"F5_R4-01": "jfwd_v352.tap_wall", "F6_R4-02_and_F3_R4-10": "lc_tb70_envelope_v352 (Z3_v2, jfwd_replace_rule_v2)",
                    "F4": "lc_tb70_envelope_v352.F4_abort_set", "F2": "torch_port_bl08_v352", "F1_cross_check": "c1_seat_v352",
                    "texts": "jfwd_v352.founder_rules (texts v5 C9 (4) / C6 (4)) and jfwd_v352.hardware.texts_superseding_hardware_strings (drawing texts v2)"},
        "review": {**src["REVIEW-COMBUSTION-R4"], "combustion": src["combustion_v2p4c"]},
        "no_cad_change": "no CAD, mass, hardware-data or BOM change; the drawing texts are text only",
        "margin_matrix": (f"04-fea/assembly3d_v352_rows_v8/tables/margin_matrix_v352.json {src['margin_matrix_v352_rows_v8']['sha256_16']}: no cell "
                          "changes (the tap-wall row is not a matrix row; TC-01 / TC-02 / HW-101 J-FWD cells unchanged)"),
        "evidence": "SIM / CALC / DERIVED as tagged in each source; none of it physical approval; paper and Python only, no FE, no ccx"}

    # ---------------------------------------------------------------------------------------------- superseded v2.3 leaves, marked
    bl, ol = dict(leaves({k: v for k, v in base.items()})), dict(leaves({k: v for k, v in out.items()}))
    changed = sorted(p for p in bl if p not in ol or ol[p] != bl[p])
    added = sorted(p for p in ol if p not in bl)
    assert all(any(under(p, q) for q in PATCHED) for p in changed), [p for p in changed if not any(under(p, q) for q in PATCHED)][:10]
    assert all(any(under(p, q) for q in PATCHED + NEW_KEYS) for p in added), [p for p in added if not any(under(p, q) for q in PATCHED + NEW_KEYS)][:10]
    assert not any(under(p, "sources_v352") or under(p, "lead_rulings_quoted_v352") for p in changed), "keys may only be added there"
    sv, se = {}, []
    for p in changed:
        v = bl[p]
        sv[p] = v
        e = {"path": p, "v2.3": v if not (isinstance(v, str) and len(v) > 160) else "(text; see superseded_v2p3_values)"}
        e["v2.4"] = ("REMOVED (restated; see the section)" if p not in ol else
                     ol[p] if not (isinstance(ol[p], str) and len(ol[p]) > 160) else "(text revised)")
        se.append(e)
    added_roots = sorted({p.split(".")[0].split("[")[0] if p.split(".")[0].split("[")[0] in NEW_KEYS else
                          next(q for q in PATCHED if under(p, q)) for p in added})
    out["superseded_v2p3_entries"] = {"rule": ("v2.3 leaves changed or removed by the v2.4 patch (not to be used for v3.5.2); each one's whole "
                                               "v2.3 value is in superseded_v2p3_values under its path"), "n": len(se), "entries": se,
                                      "added_under": added_roots}
    out["superseded_v2p3_values"] = sv
    assert all(k in out for k in base), "a v2.3 key was dropped"
    assert all(out[k] == V21[k] for k in kept21)
    for k in ("superseded_v2p2_entries", "superseded_v2p2_values", "remap_basis_v352", "superseded_v2p1_entries", "gimballed_mass_properties_v352",
              "design_changes_v352", "not_re_derived_v352"):
        assert out[k] == base[k], k
    s = json.dumps(out, indent=1, default=str)
    assert s.isascii()
    if dry:
        print(json.dumps({"mode": "pre" if pre else "dry", "pending_hub_copies": pending, "n_bytes": len(s),
                          "sha256_16_if_written": hashlib.sha256(s.encode()).hexdigest()[:16], "writer_sha256_16": sha(Path(__file__)),
                          "n_superseded_leaves": len(se), "changed_leaf_roots": sorted({next(q for q in PATCHED if under(p, q)) for p in changed}),
                          "added_under": added_roots, "new_keys": [k for k in out if k not in base],
                          "header": {k: out[k] for k in ("version", "date", "cad_version", "supersedes")}}, indent=1))
        return out
    st = os.statvfs(HUB)
    free = st.f_bavail * st.f_frsize
    assert free - len(s) >= 1.95 * 2 ** 30, ("free space would fall below 1.95 GiB: not written", free)
    cur = HUB.read_bytes()                           # re-read just before writing (shared folder)
    assert cur == base_raw, "hub mechanical.json changed under us"
    os.rename(HUB, HIST)                             # archive v2.3 by rename (never a copy)
    HUB.write_text(s)
    back = json.loads(HUB.read_text())
    assert back["version"] == "v2.4" and back["cad_version"] == "v3.5.2" and "lc_tb70_envelope_v352" in back
    assert all(back[k] == V21[k] for k in kept21) and sha(HIST) == V23_SHA
    print("archived", HIST, sha(HIST), "| written", HUB, sha(HUB), len(s), "bytes")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv, pre="--pre" in sys.argv)
