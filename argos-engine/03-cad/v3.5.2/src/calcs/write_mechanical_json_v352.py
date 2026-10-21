"""Write interfaces/mechanical.json v2.3 (Mechanical, 2026-10-21): the v3.5.2 J-FWD RE-MAP issue (lead 2026-10-21T05:50:45Z re-map brief
R1-R12: one re-map on FEA3D-2's FINAL envelope v6 43a5d78b67c615fc and the cD input record 5a41c8d74897bdda), on base v2.2 (2026-10-20,
sha256/16 f790d31b5ca7d954; v2.2 writer 95dc582b1deeccde kept as 03-cad/v3.5.2/history/write_mechanical_json_v352.py.95dc582b1deeccde).

Rule (brief): the 29 v2.1 sections and the v2.2 _v352 sections are KEPT; the re-mapped values GOVERN; superseded values are MARKED.
  - the 29 v2.1 sections (every v2.1 key but version / date / supersedes / status) are carried unchanged, asserted equal to the archived
    v2.1 (03-cad/v3.5.2/history/mechanical.json.e4d3e7c9df529171);
  - every v2.2 key stays.  Sections the re-map does not touch (gimballed_mass_properties_v352, design_changes_v352, not_re_derived_v352)
    are carried unchanged (their sources asserted unchanged); the sections it touches hold the re-mapped values, and the v2.2 value of each
    is kept whole in superseded_v2p2_values, with superseded_v2p2_entries naming every changed or removed leaf (v2.2 -> v2.3);
  - new: remap_basis_v352, superseded_v2p2_entries, superseded_v2p2_values.
Every number is read from the result files in sources_v352 (sha256/16 recorded and checked against the hub copies at write time); the
lead's rulings are quoted from the hub CHANGELOG lines named (line sha recorded) or, for the 05:50:45Z brief (not yet a CHANGELOG line),
paraphrased and marked so; nothing is typed except tagged constants and ruled texts.  At write time the v2.2 file is archived by RENAME as
03-cad/v3.5.2/history/mechanical.json.f790d31b5ca7d954 and v2.3 is written in its place.
Usage: python write_mechanical_json_v352.py [--pre | --dry]  (--pre: before the publication, sources not yet on the hub are checked on the
dev side only, nothing written; --dry: every hub copy checked, nothing written; no flag: re-reads the hub file just before writing, checks
free space >= 1.95 GiB after the write (lead disk rule), archives v2.2 by rename, writes v2.3, reads it back)."""
import copy, hashlib, json, os, sys
from pathlib import Path

HUBE = Path("/home/claude/work/shared-fallback/engine")
HUB = HUBE / "interfaces" / "mechanical.json"
HIST = HUBE / "03-cad" / "v3.5.2" / "history" / "mechanical.json.f790d31b5ca7d954"
V21_HIST = HUBE / "03-cad" / "v3.5.2" / "history" / "mechanical.json.e4d3e7c9df529171"
CL = HUBE / "interfaces" / "CHANGELOG.md"
V22_SHA, V21_SHA = "f790d31b5ca7d954", "e4d3e7c9df529171"
D = Path("/home/claude/work/mechanical/v352/engine/03-cad")
J = Path("/home/claude/work/mechanical/v352/jfwd")
T = Path("/home/claude/work/mechanical/v352/texts")
A = "04-fea/assembly3d_v352/results/v352/"
# key: (dev source or None for a hub-only input, hub path relative to engine/, expected sha256/16 or None = recorded as found)
SRC = {"massprops_v352": (D / "massprops_v3.5.2.json", "03-cad/v3.5.2/massprops_v3.5.2.json", None),
       "massdelta_v352_v9": (D / "massdelta_v3.5.2_vs_v3.5.1.json", "03-cad/v3.5.2/massdelta_v3.5.2_vs_v3.5.1.json", "6f39368668acafd1"),
       "bom_v352": (D / "BOM_v3.5.2.json", "03-cad/v3.5.2/BOM_v3.5.2.json", None),
       "hardware_v352_v1.7": (D / "src/data/hardware_v352.json", "03-cad/v3.5.2/data/hardware_v352.json", "c2c7b13d3a0086e3"),
       "test_final352": (Path("/home/claude/work/mechanical/v352/checks/test_final352_v1.json"), "03-cad/v3.5.2/checks/test_final352_v1.json", None),
       "rev5_cad_check_v2": (Path("/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v2.json"), "04-fea/v352/checks_rev5/test_rev5_jfwd_v2.json",
                             "32c41e1e207f9d64"),
       "relax_v8": (J / "jfwd_relax_v352_v8.json", "04-fea/v352/jfwd_relax_v352_v8.json", "51e9eddb9b9e6711"),
       "rows_v8": (J / "jfwd_in718_rows_v352_v8.json", "04-fea/v352/jfwd_in718_rows_v352_v8.json", "af072cc2e70711ca"),
       "K_js5_v3": (J / "jfwd_embed_fit_js5_v352_v3.json", "04-fea/v352/jfwd_embed_fit_js5_v352_v3.json", "6ab5d369ef8594ce"),
       "spring_v5": (J / "jfwd_spring_v352_v5.json", "04-fea/v352/jfwd_spring_v352_v5.json", "7d2e27d74f202418"),
       "head_fillet_v2": (J / "jfwd_head_fillet_v352_v2.json", "04-fea/v352/jfwd_head_fillet_v352_v2.json", "704f55ecb7a18dea"),
       "tap_wall_v1": (J / "jfwd_tapwall_v352_v1.json", "04-fea/v352/jfwd_tapwall_v352_v1.json", "bcb21243d57af998"),
       "screw_lcf_v3": (J / "jfwd_screw_lcf_v352_v3.json", "04-fea/v352/jfwd_screw_lcf_v352_v3.json", "b6ff0ea0f731c7dc"),
       "pq_band_v1": (J / "jfwd_pq_band_v352_v1.json", "04-fea/v352/jfwd_pq_band_v352_v1.json", "1ba3147b42edfeed"),
       "r6_companions_v1": (J / "jfwd_r6_companions_v352_v1.json", "04-fea/v352/jfwd_r6_companions_v352_v1.json", "dac127af6f742cf2"),
       "jf1b_loctite_v1": (J / "jf1b_loctite_v352_v1.json", "04-fea/v352/jf1b_loctite_v352_v1.json", "2ba9d10745f3f651"),
       "texts_v4": (T / "item_c_tf1_texts_v352_v4.json", "04-fea/v352/texts/item_c_tf1_texts_v352_v4.json", "13ca091930716950"),
       "tf1_exposure_v2": (T / "tf1_exposure_v352_v2.json", "04-fea/v352/texts/tf1_exposure_v352_v2.json", "d60f5da3ce3e5cb7"),
       "drawing_texts_v1": (T / "jfwd_drawing_texts_v352_v1.json", "03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json", "872b9637bfcdc6c0"),
       "fea3d_envelope_v6": (None, A + "jfwd_soak_envelope_v352_v6.json", "43a5d78b67c615fc"),
       "fea3d_v7inputs_cD": (None, A + "jfwd_v7inputs_cD_v352.json", "5a41c8d74897bdda"),
       "fea3d_b1_meshcorr": (None, A + "jfwd_b1_meshcorr_v352.json", "adac16afd42ef7bd"),
       "fea3d_js5b_rows": (None, A + "jfwd_js5b_rows_v352.json", "91278d6b039c5b27")}
UNTOUCHED = ("gimballed_mass_properties_v352", "design_changes_v352", "not_re_derived_v352")
HEADER_V21 = ("version", "date", "supersedes", "status")


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
        for k, v in x.items():
            yield from leaves(v, f"{p}.{k}" if p else str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


def main(dry=False, pre=False):
    dry = dry or pre
    base_raw = HUB.read_bytes()
    assert sha(HUB) == V22_SHA, ("hub mechanical.json is not the v2.2 this writer was made for", sha(HUB))
    assert not HIST.exists(), ("archive target already exists", HIST)
    base = json.loads(base_raw)
    assert base["version"] == "v2.2" and base["cad_version"] == "v3.5.2"
    assert sha(V21_HIST) == V21_SHA
    V21 = json.loads(V21_HIST.read_text())
    kept21 = [k for k in V21 if k not in HEADER_V21]
    assert len(kept21) == 29 and all(base[k] == V21[k] for k in kept21), "the 29 v2.1 sections are not as archived"
    X, src, pending = {}, {}, {}
    for k, (p, hp, s16) in SRC.items():
        hub = HUBE / hp
        s = sha(p) if p else sha(hub)
        if s16:
            assert s == s16, (k, p or hub, s)
        if p and not hub.exists() and pre:
            pending[k] = {"hub_path": hp, "hub_exists": False}
        else:
            assert hub.exists() and sha(hub) == s, ("hub copy missing or different", k, hp)
        X[k] = json.loads(Path(p or hub).read_text())
        src[k] = {"path": hp, "sha256_16": s}
    for k in ("massprops_v352", "massdelta_v352_v9", "bom_v352", "hardware_v352_v1.7", "test_final352", "rev5_cad_check_v2"):
        assert src[k] == base["sources_v352"][k], ("a v2.2 source of the untouched sections moved", k)
    HW, R8, JS3, SP5, HF2, TW1, LC3, BD, RC, JL, TX, TF, DTX, RX = (X[k] for k in (
        "hardware_v352_v1.7", "rows_v8", "K_js5_v3", "spring_v5", "head_fillet_v2", "tap_wall_v1", "screw_lcf_v3", "pq_band_v1",
        "r6_companions_v1", "jf1b_loctite_v1", "texts_v4", "tf1_exposure_v2", "drawing_texts_v1", "relax_v8"))
    assert (HW["version"], R8["version"], JS3["version"], SP5["version"], HF2["version"], LC3["version"], BD["version"], TX["version"],
            TF["version"], RX["version"]) == ("v1.7", "v8", "v3", "v5", "v2", "v3", "v1", "v4", "v2", "v8")
    assert R8["inputs"]["fea3d_soak_envelope"]["sha256_16"] == src["fea3d_envelope_v6"]["sha256_16"]
    others = {}
    for n in ("combustion.json", "electronics.json", "gnc.json", "ENGINE-BASELINE-v0.json"):
        p = HUBE / "interfaces" / n
        d = json.loads(p.read_text())
        others[n] = {"version": d.get("version"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    out = copy.deepcopy(base)
    out.update({"version": "v2.3", "date": "2026-10-21",
                "supersedes": (f"v2.2 (2026-10-20, sha256/16 {V22_SHA}; archived by rename as 03-cad/v3.5.2/history/mechanical.json.{V22_SHA}); "
                               f"v2.1 (2026-10-13, {V21_SHA}) archived as 03-cad/v3.5.2/history/mechanical.json.{V21_SHA}"),
                "status": ("v3.5.2 J-FWD re-map issue (lead 2026-10-21T05:50:45Z R1-R12) on the FINAL 03-cad v3.5.2 set (no CAD change in the "
                           "re-map): SIM + CALC + DERIVED + DESIGN as tagged; physical validation pending (bench and founder test lists); margins "
                           "are model results, not test results; negatives are shown as found")})
    out["reading_rule_v352"] = ("Sections whose key ends in _v352 (and the header) govern for v3.5.2. The v2.1 sections are kept unchanged as "
                                "the record of CAD v3.3 / v3.5 / v3.5.1; where a v2.1 value conflicts with a _v352 section, the _v352 section "
                                "governs; superseded_v2p1_entries lists the v2.1 entries not to be used for v3.5.2. v2.3: the _v352 sections hold "
                                "the J-FWD re-map values (relax v8, rows v8 and companions on FEA3D-2's FINAL envelope v6); every v2.2 value they "
                                "replace is kept in superseded_v2p2_values and named leaf by leaf in superseded_v2p2_entries (not to be used for "
                                "v3.5.2).")
    out["scripts_v352"] = {"writer": "03-cad/v3.5.2/src/calcs/write_mechanical_json_v352.py (v2.3)", "writer_sha256_16": sha(Path(__file__)),
                           "mass": base["scripts_v352"]["mass"], "hardware": base["scripts_v352"]["hardware"],
                           "jfwd": ("04-fea/v352/jfwd_*_v352.py (relax v8, rows v8, K_js5 v3, spring v5, head fillet v2, screw LCF v3, P+Q band "
                                    "v1, R6 companions v1, J-F1b / LOCTITE v1; tap wall v1 stays, R11)"),
                           "texts": "04-fea/v352/texts/item_c_tf1_texts_v352.py (v4; also writes the drawing-text set) and tf1_exposure_v352.py (v2)",
                           "drawing_texts": "03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json"}
    out["inputs_read_v352"] = others
    out["sources_v352"] = src

    # ---------------------------------------------------------------------------------------------- J-FWD route (i), re-mapped
    H101 = next(L for L in HW["lines"] if L["id"] == "HW-101")
    H170 = next(L for L in HW["lines"] if L["id"] == "HW-170")
    JF1 = R8["J_F1"]
    st3 = ("SOAK52", "SOAK70", "SOAK", "FA1S")
    row = lambda st, k: R8["states"][st]["rows"]["3750"][k]          # noqa: E731
    THE_ROW = {st: R8["TC02_thread_shear_full_row"]["rows"][st]["3750"]["THE_ROW"]["MS_y"] for st in st3}
    assert THE_ROW == {"SOAK52": 0.045, "SOAK70": 0.087, "SOAK": 0.104, "FA1S": 1.802}
    HG = HF2["governing_and_thread_root_comparison"]["3750"]
    TWc = TW1["rows"]["3750"]["cases"]
    TWg = min((v["TC02_thread_T"]["MS_y"], k) for k, v in TWc.items() if k.endswith("ruled_+/-0.25deg_net_GOVERNING"))
    SEAT = SP5["lead_16_07Z_item5_seated_and_solid"]
    LCg, LCi = LC3["governing"], LC3["governing_info_M_x_ratio"]
    E8 = R8["FA1S_screw_5020A_eq22"]
    BR = BD["RESULT"]
    C9 = TX["item_C"]["C9_founder_texts_remap_v352"]
    c96 = C9["(6)_TC-02_select_fit_band_R2"]
    i0 = c96.index("LEAD RULING R2-B (2026-10-21T07:37:34Z): ")
    i1 = c96.index("this is CALC on SIM, not physical approval.", i0) + len("this is CALC on SIM, not physical approval.")
    R2B = c96[i0:i1]
    assert R2B.isascii() and "D_meas - 0.1262 <= OD <= D_meas - 0.080" in R2B and R2B in DTX["ENG-TC-02"]["plug_OD_seat_line_band_R2"]
    G_R2B = BR["g_for_MS_+0.05_3750_mm"]
    assert G_R2B == 0.0631 and f"[0.040, {G_R2B}] mm" in R2B
    E631 = {f"{kb}|{f}": min((BD["per_key"][f"{kb}|{fam}|{f}"]["per_state"][st]["MS_at_gap_new_points"][str(G_R2B)], st)
                            for fam in ("seat", "ring") for st in ("SOAK70", "SOAK", "SOAK52")) for kb in ("hi", "lo") for f in (3750, 4096)}
    T0I, PSH = BR["stand_T0_24C_info"], BD["per_key"]["hi|seat|3750"]["per_state"]
    P4 = min((round((1 + PSH[st]["MS_at_gap_new_points"][str(G_R2B)]) * T0I["per_state"][st]["Fty_at_T_line_+4K_MPa"]
                    / T0I["per_state"][st]["Fty_at_T_line_MPa"] - 1, 4), st) for st in PSH)
    assert f"seat-line MS {E631['hi|3750'][0]:+.4f} (k_b hi) / {E631['lo|3750'][0]:+.4f} (k_b lo) at 3750 N" in c96 and f"{P4[0]:+.4f} ({P4[1]})" in c96
    R2B_REC = {"text": R2B, "source": "lead message 2026-10-21T07:37:34Z, logged in CHANGELOG 254",
               "ruled_band_mm_radial": [0.04, G_R2B], "select_fit": "D_meas - 0.1262 <= OD <= D_meas - 0.080 mm (window 0.0462 mm on the diameter, less 2U, U TO-DEFINE)",
               "MS_at_ruled_edge_CALC_on_SIM": {"3750_k_b_hi": E631["hi|3750"], "3750_k_b_lo": E631["lo|3750"], "4096_k_b_hi_info": E631["hi|4096"],
                                                "4096_k_b_lo_info": E631["lo|4096"], "ASSUMED_+4K_info_k_b_hi_3750": P4},
               "drawing_text": "03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json ENG-TC-02.plug_OD_seat_line_band_R2 = texts v4 C9 (6)",
               "option_A_drawn_57.20_-0.030/-0.040": "not adopted (information only)",
               "data_strings": "parts_engine.py 'plug 57.20 f7', BOM_v3.5.2 and hardware_v352.json stay unedited in v3.5.2, superseded by the drawing note (lead 07:37:34Z (i))"}
    SB = R8["seat_line_basis_R3_R4"]
    seat = {st: row(st, "seat_line_d6p051_z0_PQ") for st in st3[:3]}
    assert {st: v["MS_PQ_2Fty"] for st, v in seat.items()} == {"SOAK52": -0.033, "SOAK70": -0.059, "SOAK": -0.075}
    assert (E8["governing_omitted"], E8["included"]) == (0.278, 0.065) and BR["band_mm_radial"] == [0.04, 0.0686]
    lcf = lambda k: {x: LCg[k][x] for x in ("case", "N_allow", "MS_cycles_vs_50")}     # noqa: E731
    out["jfwd_v352"] = {
        "route": ("route (i) (lead 16:53Z R2, CAD check ACCEPTED 17:55:55Z, rows v7 and companions ACCEPTED 18:36:37Z); v2.3: RE-MAPPED ONCE "
                  "on FEA3D-2's FINAL envelope v6 and the cD input record (lead 2026-10-21T05:50:45Z R1): relax v8, rows v8 and companions"),
        "remap_inputs": {k: src[k] for k in ("fea3d_envelope_v6", "fea3d_v7inputs_cD", "fea3d_b1_meshcorr", "fea3d_js5b_rows", "relax_v8", "rows_v8")},
        "anchors_R3": {"rule": SB["rule"], "cD_beside": SB["cD_beside"],
                       "note": "s6 + C1 stand; the anchors are FINAL; cD's local values are recorded beside, not entered (lead R3)"},
        "MF_note_R4": SB["MF_note"],
        "cad_basis_R8": R8["cad_basis_R8"],
        "hardware": {"HW-101": {k: H101[k] for k in ("item", "standard", "size", "length_mm", "grade", "head_form_F3", "unit_mass_g", "torque_Nm",
                                                     "torque_basis", "thread_locker", "status", "action", "assembly_note")},
                     "HW-170": {k: H170[k] for k in ("item", "standard", "size", "grade", "qty", "unit_mass_g", "status", "action", "assembly_note")},
                     "M-T1J": HW["rules"]["tightening_methods"]["M-T1J"], "J-F1": H101["test"],
                     "texts_superseding_hardware_strings": (
                         "03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json: HW-170 orientation DEFINED (C9 (1)) and SINGLE-USE (C9 (2), 248 (7)); "
                         "the hardware v1.7 strings 'orientation TO-DEFINE' and 'reuse of a removed spring TO-RULE' are superseded by these texts "
                         "(data/hardware_v352.json is not edited; the lead rules any data update)")},
        "J_F1": JF1,
        "rows_3750_governing": {
            "THE_ROW_TC02_thread_shear_MS_y": THE_ROW,
            "THE_ROW_note": "file values (TC02_thread_shear_full_row); SOAK52 +0.045 is a FLAG (< 0.05)",
            "under_head_full_float_MS_strain_ASSUMED": {st: row(st, "TC01_under_head_band_neuber")["MS_strain"] for st in st3},
            "TC01_flat_bearing_registered_stack_MS": {st: row(st, "TC01_flat_bearing")["MS_vs_Fbry"] for st in st3[:3]},
            "screw_tension_MS_y": {st: row(st, "screw_tension_234_1b")["MS_y"] for st in st3[:3]},
            "head_on_spring_MS_y_min": min(row(st, "head_on_spring_IN718")["MS_y"] for st in st3 + ("PRELOAD",)),
            "found_negatives": {"seat_ring_line_PQ_2Fty_at_drawn_fit_g0.078": {st: v["MS_PQ_2Fty"] for st, v in seat.items()},
                                "seat_ring_line_PQ_from": {st: v["from"] for st, v in seat.items()},
                                "screw_fibre_yield": {st: row(st, "screw_fibre_soak")["MS_y_fibre"] for st in st3[:3]},
                                "screw_fibre_yield_from": {st: row(st, "screw_fibre_soak")["from"] for st in st3[:3]},
                                "screw_fibre_shakedown_min": min(row(st, "screw_fibre_soak")["MS_shakedown"] for st in st3[:3])},
            "flags_and_negatives_list": R8["flags_within_0.05_or_negative"],
            "information_rows_list": R8["information_rows_negative_or_within_0.05"]},
        "R5_information_moment_ratio": {
            "rule": "lead R5: screw rows use M as solved; M x 1.404 (PRELOAD) and M x 1.476 (SOAK) are INFORMATION, never govern",
            "SOAK_screw_fibre_b1": row("SOAK", "screw_fibre_soak_info_M_x_ratio"),
            "PRELOAD_screw_fibre_info": {k: R8["states"]["PRELOAD"]["rows"]["3750"]["screw_fibre_preload_info"][k]
                                         for k in ("MS_y_fibre_info", "MS_y_fibre_info_M_x_ratio", "from", "class")},
            "screw_LCF_info_Kf3.0_3750": {k: LCi[k] for k in ("i_firing|Kf3.0|3750", "ii_assembly_from_zero|Kf3.0|3750")}},
        "R6_FA1S_screw_eq22": {**{k: E8[k] for k in ("governing_omitted", "included", "R6_basis", "CALC_record_fix_v2", "arm_+0.4_sens",
                                                    "direct_shear_minor_CALC", "direct_shear_minor_at_R6_V_companion", "hole_bearing_TC01")},
                               "companions_info_R6_basis": {k: RC[k] for k in ("eq22_arm_+0.4_sens_R6_basis_INFO", "TC02_tap_bearing_at_R6_V_INFO")}},
        "R7_LC2_FA1U_FA1D": R8["LC2_FA1U_FA1D_parts_rows_R7"],
        "seat_line_PQ_band_R2": {k: BR[k] for k in ("band_mm_radial", "band_upper_edge_basis", "governs", "MS_min_at_band_edge_3750", "flag",
                                                    "g_at_MS0_4096_info_mm", "g_for_MS_+0.05_3750_mm", "line_240_band_[0.040,0.0761]",
                                                    "closes_seat_line", "lead_CALC_check", "fit_windows", "drawn_options", "select_fit",
                                                    "what_it_acts_on", "MF_note_R4", "stand_T0_24C_info", "drawing_text_status")}
                                | {"lead_ruling_R2-B": R2B_REC},
        "screw_LCF_thread_root_C6": {
            "per_firing": {"N_allow": HG["i_firing"]["thread_root_N_allow"], "MS": HG["i_firing"]["thread_root_MS"]},
            "assembly_from_zero": {"N_allow": HG["ii_assembly_from_zero"]["thread_root_N_allow"], "MS": HG["ii_assembly_from_zero"]["thread_root_MS"]},
            "governing_case": LCg["i_firing|Kf3.0|worst_of_histories|3750"]["case"],
            "Kf2.2_sensitivity_per_firing": {**lcf("i_firing|Kf2.2|worst_of_histories|3750"), "v2_MS": 0.36,
                                             "note": "SIGN CHANGE v2 -> v3 (rows v8, SOAK (b1)); sensitivity row, Kf 3.0 governs"},
            "status": ("FOUND NEGATIVE (183 (1)(c)), deeper on rows v8; C6 OPEN; path 2: (b1) solved and entered (rows v8 under C1 / R5), the "
                       "row stays negative, the P+Q band takes no screw credit; path 3 (qualification test, TO-DEFINE, founder) remains; path 1 "
                       "(MJ) closed NOT SOURCED")},
        "head_fillet": {"static": HG["static"], "per_firing": {k: HG["i_firing"][k] for k in ("fillet_N_allow", "fillet_MS", "fillet_governs")},
                        "assembly_from_zero": {k: HG["ii_assembly_from_zero"][k] for k in ("fillet_N_allow", "fillet_MS", "fillet_governs")},
                        "tags": "Kt LITERATURE (secondary, via AMESweb citing Pilkey 2005); the Pilkey page and the T-head Kt TO-SOURCE; "
                                "head-end resultants carried over ASSUMED (lead 18:36:37Z); from zero = FOUND NEGATIVE, not governing"},
        "tap_wall": {"governing_case": TWg[1], "MS_y": TWg[0], "walls_mm": TW1["walls_mm"], "verdict": TW1["verdict"],
                     "to_confirm": "P_torch and its distribution along the torch passage (REV-COMB-4)",
                     "R11": "stays v1 until REV-COMB-4; if its bounding P_torch is above 102 bar abs, Mechanical re-runs the tap-wall check when the lead relays it"},
        "spring_v5": {"verdict": SP5["stop_test_lead_F1"]["verdict"] + " (every spring run, A and B, R 0-0.80, both k_b ends and families)",
                      "F_S_min_N_by_case": {k: v["F_S_min_N"] for k, v in SEAT.items()}},
        "K_js5_v3_no_spring_record": JS3["stop_test_lead_F1"],
        "founder_rules": {"single_use": ("J-FWD screws are new at every assembly, never reused or re-torqued; removed screws are kept per hole "
                                         "and inspected at 10x plus dye penetrant at the thread root AND the head-to-shank fillet, as data "
                                         "(lead 16:53Z R3 + LEAD ADDITION 18:36:37Z)"),
                          "HW-170_single_use": C9["(2)_HW-170_single_use"], "HW-170_orientation": C9["(1)_HW-170_orientation"],
                          "J-F1b": C9["(3)_J-F1b"], "post_abort_joint_replacement": C9["(4)_post_abort_joint_replacement"],
                          "stand_T0_cross_reference": C9["(5)_stand_T0_cross_reference"],
                          "C4_procedure": TX["item_C"]["C4_assembly_step_founder_procedure"], "C6": TX["item_C"]["C6_founder_action_list_related"]},
        "T-F1_R9": {"text": TX["T-F1"], "basis": TX["T-F1_exposure_basis_R9"],
                    "TB_rows_basis_and_beside": [r for r in TX["T-F1_TB_table"] if r["row"] in ("TB", "TB_a150")]},
        "drawing_texts": ("03-cad/v3.5.2/texts/jfwd_drawing_texts_v352_v1.json (TC-02 plug OD band, HW-170 orientation and single-use, the "
                          "assembly and founder rules); 04-fea/v352/texts/item_c_tf1_texts_v352_v4.json item_C C8 (rev-5 texts) and C9 (re-map texts)")}
    assert DTX["ENG-TC-02"]["plug_OD_seat_line_band_R2"] == C9["(6)_TC-02_select_fit_band_R2"]

    # ---------------------------------------------------------------------------------------------- lead rulings quoted (hub CHANGELOG)
    out["lead_rulings_quoted_v352"] = dict(base["lead_rulings_quoted_v352"])
    out["lead_rulings_quoted_v352"].update({
        "jfwd_rulings_248_7": cl_segment(248, "(7) J-FWD RULINGS (19:53:27Z)", "(8) USER and STORAGE"),
        "stand_T0_249_2": cl_segment(249, "(2) STAND T0 RULE (founder action)", "(3) T-F1 EXPOSURE BASIS"),
        "tf1_exposure_basis_249_3": cl_segment(249, "(3) T-F1 EXPOSURE BASIS", "(4) RELIGHT AND TRANSDUCER"),
        "convergence_cD_249_11": cl_segment(249, "(11) CONVERGENCE CHECK cD", "(12) DISK"),
        "lc2_parts_rows_250_2": cl_segment(250, "(2) LC2 PARTS ROWS", "(3) TC-04 BT"),
        "R2-B_2026-10-21T07:37:34Z": {"source": "lead message 2026-10-21T07:37:34Z, logged in CHANGELOG 254", "text": R2B,
                                      "answers_PARAPHRASED": {"(i)": "the texts carry the ruling, not both options; the data strings stay unedited, superseded by the drawing note",
                                                              "(ii)": "C9 (4) / C6 (4) go out with the line-253 OPEN sentence",
                                                              "(iii)": "the 253 (8) / (10) items come after the publication (F1-F4)"}},
        "cD_in_v7_inputs_253_1": cl_segment(253, "(1) cD in Mechanical's v7 inputs", "(2) Line order"),
        "remap_record_253_3": cl_segment(253, "(3) Mechanical re-map", "(4) REV-ELEC-3"),
        "R3-02_provisional_253_8_OPEN": cl_segment(253, "(8) R3-02, provisional lead definition", "(9) ELECTRONICS ROUND"),
        "routed_253_10_OPEN": cl_segment(253, "(10) Routed:", "(11) Founder items added"),
        "remap_brief_2026-10-21T05:50:45Z": {
            "source": ("the lead's re-map brief to Mechanical (message 2026-10-21T05:50:45Z; not itself a CHANGELOG line up to line 253, "
                       "which records the cD ruling (253 (1)) and the re-map go (253 (3)), both quoted above): PARAPHRASED here; the lead's "
                       "CHANGELOG line is the record"),
            "R1": "re-map ONCE on the FINAL envelope v6 plus the cD input record",
            "R2": ("the P+Q select-fit band APPLIES (line 240: IN718 [0.040, 0.0761] mm radial, narrower TC-02 spigot OD tolerance); re-size it "
                   "once on the final anchors; the lead's CALC (a [0.040, 0.0684] band leaves about 0.011 mm of spigot OD window unless "
                   "select-fitted) to confirm or correct; if no band inside [0.040, 0.0761] closes the seat line it stays a FOUND NEGATIVE; the "
                   "band goes on the TC-02 drawing text only after the re-size; no geometry change without asking the lead first"),
            "R3": "s6 + C1 stand; the anchors are FINAL; cD's local values recorded beside, not entered",
            "R4": "the seat-line P+Q is NOT shown mesh-converged; quoted as found with the MF note; extrapolations are information only",
            "R5": "screw rows use M as solved, plus M x 1.404 (PRELOAD) and M x 1.476 (SOAK) as information",
            "R6": "HW-101 Eq. 22 at max(CALC, FE) per resultant: V 4079.2 N (FE, (b1) FA1S) and M 4354.7 N mm (CALC); hole bearing stays on the CALC row (+0.005 / +0.239)",
            "R7": ("LC2 parts rows: external load factored, preload not; TC-01 / TC-02 LC2 yield slot = LC2Y, ultimate slot = LC2U; hand-form "
                   "LC2N / LC2M parts rows information beside; screw LC2N / LC2M = criterion (234 (1)(b)); FA1U / FA1D parts rows = criterion "
                   "(231 (1)), bounded by FA1S"),
            "R8": "CAD basis: every J-FWD FE except cD on the interim TC-01 (d10.5 flats); effect of the final d11.2 part ASSUMED small; cited in the rows and texts",
            "R9": "T-F1 restated on the A 175 rows (both bounds) with the A 150 rows beside; re-basing to A 165 only after B-TC-1, by the lead",
            "R10": "founder texts: the orientation note, HW-170 single-use, J-F1b (175 C, >= 10 min), the post-abort joint replacement rule, the stand T0 rule as a cross-reference",
            "R11": "the tap wall stays v1 until REV-COMB-4; re-run if its bounding P_torch is above 102 bar abs, when the lead relays it",
            "R12": "Electronics v2.11 items go to REV-COMB-4 first; act only on the lead's relay; lc_tb70_envelope_v1.json not changed"}})
    out["requests_v352"] = [
        "REQUEST Combustion (REV-COMB-4): P_torch and its distribution along the torch passage at the J-FWD taps (az 18 / 342), for the "
        "TC-02 tap-wall row (04-fea/v352/jfwd_tapwall_v352_v1.json, MS_y +0.814 on a uniform passage pressure: TO-CONFIRM); R11: if the "
        "bounding P_torch is above 102 bar abs, Mechanical re-runs the tap-wall check when the lead relays it.",
        "INFORMATION GNC: the re-map changes no CAD and no mass; gimballed_mass_properties_v352 is unchanged.",
        "INFORMATION Electronics: the stand T0 rule (249 (2)) is cross-referenced in the founder texts (C9 (5)); the J-FWD rows are at T0 20 C; "
        f"at T0 24 C the ruled R2-B edge g {G_R2B} mm reads MS {P4[0]:+.3f} (the R2 band edge 0.0686 mm: "
        f"{BR['stand_T0_24C_info']['MS_at_band_edge_+4K_min']:+.3f}) (information, ASSUMED +4 K).",
        "REQUEST Founder (test list): J-F1 on the flight lots with the spring items, the spring ORIENTED per C9 (1), and the Prescale "
        "footprint item (TO-VERIFY) before the first J-FWD assembly; J-F1b at 175 C with >= 10 min at the peak (method TO-DEFINE: a uniform "
        "oven only if the LOCTITE 243 range covers 175 C); the post-abort joint replacement rule; the LOCTITE 243 range and hot-strength "
        "fractions TO-VERIFY; C6 path 3 qualification test TO-DEFINE; T-F1 gate before the first static fire on the A 175 basis rows."]
    out["open_items_v352"] = [
        f"C6 OPEN: J-FWD screw LCF at the thread root FOUND NEGATIVE, deeper on rows v8 (Kf 3.0 per firing N_allow {HG['i_firing']['thread_root_N_allow']}, "
        f"MS {HG['i_firing']['thread_root_MS']:+.3f}; from zero {HG['ii_assembly_from_zero']['thread_root_N_allow']}, "
        f"{HG['ii_assembly_from_zero']['thread_root_MS']:+.3f}; Kf 2.2 now {LCg['i_firing|Kf2.2|worst_of_histories|3750']['MS_cycles_vs_50']:+.3f}); "
        "paths 2 and 3; single-use founder rule in force",
        f"seat-line P+Q FOUND NEGATIVE at the drawn 57.20 f7 (SOAK {seat['SOAK']['MS_PQ_2Fty']:+.3f} {seat['SOAK']['from']}); RULED R2-B "
        f"(07:37:34Z): select fit, flag-free band [0.040, {G_R2B}] mm (MS {E631['hi|3750'][0]:+.3f} / {E631['lo|3750'][0]:+.3f} at 3750 N, k_b hi / lo) "
        "[CALC on SIM]; U (measurement uncertainty) TO-DEFINE (shop); NOT shown mesh-converged (R4)",
        f"screw fibre yield FOUND NEGATIVE (SOAK {row('SOAK', 'screw_fibre_soak')['MS_y_fibre']:+.3f} {row('SOAK', 'screw_fibre_soak')['from']}; "
        f"shakedown {min(row(st, 'screw_fibre_soak')['MS_shakedown'] for st in st3[:3]):+.3f})",
        "head-to-shank fillet: Pilkey page and T-head Kt TO-SOURCE; head-end resultants ASSUMED; from zero FOUND NEGATIVE, not governing",
        "tap wall: stays v1 (R11); P_torch and its distribution TO-CONFIRM (REV-COMB-4)",
        "under-head row at full float: ASSUMED mean-pressure scaling; THE ROW SOAK52 +0.045 FLAG",
        "J-F1: Prescale footprint TO-VERIFY (film grade TO-SELECT); J-F1b heating method TO-DEFINE (test owner); LOCTITE 243 range and hot "
        "strength TO-VERIFY (founder)",
        "ENG-HW-101-IN718 drawing TO-DRAW (pilot coaxiality dia 0.02 TO-CONFIRM with the maker; the C9 (1) orientation note goes on it; the "
        "installation convention AS RECALLED, TO-VERIFY); HW-170 TO-QUOTE delivered to Sonderborg DK-6400 (spring A / B, relaxation data at "
        "about 160 C), SINGLE-USE ruled",
        "ENG-TC-13 registration shoulder screws TO-DRAW; match-drill fixture with the index pin and guide bushings TO-DRAW (shop tooling); "
        "head-shoulder gap gauge 2.00 +/-0.02 TO-CONFIRM",
        "T-F1 / 183 (1)(d) OPEN for TC-01 / TC-02 on the A 175 basis rows (A 150 beside); re-basing to A 165 only after B-TC-1 (lead)",
        "CAD basis R8: the J-FWD FE except cD on the interim TC-01 (d10.5 flats); the effect of the final part ASSUMED small",
        "TC-09 thinning (206 (2a)) conditional on its re-run, as in the interim",
        "Electronics v2.11 items for Mechanical go to REV-COMB-4 first (R12); lc_tb70_envelope_v1.json unchanged",
        "ROUTED to Mechanical by lead CHANGELOG 253 (10) (Mechanical's next round on the lead's brief, not this re-map; quoted in "
        "lead_rulings_quoted_v352): the node that represents the C1 diaphragm and its ARM-to-light dT history with T0 independence (stand T0 "
        "<= 24 C; a flight range to be stated), the torch-port dT and the BL-08 temperature [MISSING]; R3-02 (253 (8)): confirm the TB-state "
        "abort list (lead PROVISIONAL: HW_OVERPRESSURE, PC_OVERPRESSURE, HARD_START; the case-TC OVER_TEMP abort in F-14) and state whether "
        "the LC-TB70 60 bar abs rule is meant for normal-light transients (185 of 896 FA-1 grid head peaks above 60 bar abs [SIM grid "
        "fraction]); the founder text C9 (4) carries both as OPEN"]
    sup21 = dict(base["superseded_v2p1_entries"])
    assert sup21["fa1.joints_table"] == "J-FWD 8 x M5 A4-70 rows: superseded by jfwd_v352 (rows v7)"
    sup21["fa1.joints_table"] = "J-FWD 8 x M5 A4-70 rows: superseded by jfwd_v352 (rows v8)"
    out["superseded_v2p1_entries"] = sup21
    out["remap_basis_v352"] = {
        "brief": "lead 2026-10-21T05:50:45Z re-map brief R1-R12 (lead_rulings_quoted_v352.remap_brief_2026-10-21T05:50:45Z)",
        "fea3d_inputs": {k: src[k] for k in ("fea3d_envelope_v6", "fea3d_v7inputs_cD", "fea3d_b1_meshcorr", "fea3d_js5b_rows")},
        "relax_v7_to_v8_moves": RX.get("v7_to_v8_moves"),
        "no_cad_change": "the re-map changes no CAD, mass or hardware line; the drawing texts are text only",
        "evidence": "SIM (FEA3D-2 FE as solved) / CALC / DERIVED as tagged in each source; none of it physical approval"}
    for k in UNTOUCHED:
        assert out[k] == base[k]

    # ---------------------------------------------------------------------------------------------- superseded v2.2 values, marked
    changed = [k for k in base if k not in HEADER_V21 + ("cad_version",) and out[k] != base[k]]
    assert not any(k in kept21 for k in changed)
    sv, se = {}, []
    for k in changed:
        b, o = base[k], out[k]
        if isinstance(b, dict) and isinstance(o, dict) and all(kk in o and o[kk] == b[kk] for kk in b):
            sv[k] = {"only_added_keys_v2p3": [kk for kk in o if kk not in b]}
            continue
        sv[k] = b
        nl = dict(leaves(o, k))
        for p, v in leaves(b, k):
            if p not in nl or nl[p] != v:
                e = {"path": p, "v2.2": v if not (isinstance(v, str) and len(v) > 160) else "(text; see superseded_v2p2_values)"}
                e["v2.3"] = ("REMOVED (re-mapped; see the section)" if p not in nl else
                             nl[p] if not (isinstance(nl[p], str) and len(nl[p]) > 160) else "(text revised)")
                se.append(e)
    out["superseded_v2p2_entries"] = {"rule": ("v2.2 leaves changed or removed by the v2.3 re-map (not to be used for v3.5.2); each changed "
                                               "section's whole v2.2 value is in superseded_v2p2_values"), "n": len(se), "entries": se}
    out["superseded_v2p2_values"] = sv
    assert all(k in out for k in base), "a v2.2 key was dropped"
    s = json.dumps(out, indent=1, default=str)
    if dry:
        print(json.dumps({"mode": "pre" if pre else "dry", "pending_hub_copies": pending, "n_bytes": len(s),
                          "sha256_16_if_written": hashlib.sha256(s.encode()).hexdigest()[:16], "changed_v2p2_sections": changed,
                          "n_superseded_leaves": len(se), "new_keys": [k for k in out if k not in base],
                          "header": {k: out[k] for k in ("version", "date", "cad_version", "supersedes")}}, indent=1))
        return out
    st = os.statvfs(HUB)
    free = st.f_bavail * st.f_frsize
    assert free - len(s) >= 1.95 * 2 ** 30, ("free space would fall below 1.95 GiB: not written", free)
    cur = HUB.read_bytes()                           # re-read just before writing (shared folder)
    assert cur == base_raw, "hub mechanical.json changed under us"
    os.rename(HUB, HIST)                             # archive v2.2 by rename (never a copy)
    HUB.write_text(s)
    back = json.loads(HUB.read_text())
    assert back["version"] == "v2.3" and back["cad_version"] == "v3.5.2" and "jfwd_v352" in back
    assert all(back[k] == V21[k] for k in kept21) and sha(HIST) == V22_SHA
    print("archived", HIST, sha(HIST), "| written", HUB, sha(HUB), len(s), "bytes")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv, pre="--pre" in sys.argv)
