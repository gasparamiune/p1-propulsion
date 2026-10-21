"""Write interfaces/mechanical.json v2.2 (Mechanical, 2026-10-20): the v3.5.2 issue of the Mechanical interface file, written with the FINAL
03-cad v3.5.2 set (lead release 19:09:50Z; lead 18:36:37Z item 5; publication 2 approved 19:22:55Z).

Rule: the v2.1 sections (2026-10-13, CAD v3.3 / v3.5 / v3.5.1 bases) are kept unchanged as the record; the sections added here end in _v352
(plus the header) and GOVERN for v3.5.2; 'superseded_v2p1_entries' names the v2.1 entries a v3.5.2 reader must not use.  Every number is
read from the result files in 'sources_v352' (sha256/16 recorded and checked against the hub copies at write time); the lead's rulings are
quoted from the hub CHANGELOG lines named (line sha recorded); nothing is typed except tagged constants and ruled texts.  The v2.1 file is
archived by the publication as 03-cad/v3.5.2/history/mechanical.json.e4d3e7c9df529171.
Usage: python write_mechanical_json_v352.py [--pre | --dry]  (--pre: before the publication, the 03-cad/v3.5.2 sources are checked on the
dev side only, nothing written; --dry: every hub copy checked, nothing written; no flag: re-reads the hub file just before writing, checks
free space >= 2.20 GiB (lead 19:09:50Z), writes it, reads it back)."""
import hashlib, json, os, re, sys
from pathlib import Path

HUBE = Path("/home/claude/work/shared-fallback/engine")
HUB = HUBE / "interfaces" / "mechanical.json"
CL = HUBE / "interfaces" / "CHANGELOG.md"
V21_SHA = "e4d3e7c9df529171"
D = Path("/home/claude/work/mechanical/v352/engine/03-cad")
J = Path("/home/claude/work/mechanical/v352/jfwd")
T = Path("/home/claude/work/mechanical/v352/texts")
# key: (dev source, hub path relative to engine/, expected sha256/16 or None = recorded as found)
SRC = {"massprops_v352": (D / "massprops_v3.5.2.json", "03-cad/v3.5.2/massprops_v3.5.2.json", None),
       "massdelta_v352_v9": (D / "massdelta_v3.5.2_vs_v3.5.1.json", "03-cad/v3.5.2/massdelta_v3.5.2_vs_v3.5.1.json", "6f39368668acafd1"),
       "bom_v352": (D / "BOM_v3.5.2.json", "03-cad/v3.5.2/BOM_v3.5.2.json", None),
       "hardware_v352_v1.7": (D / "src/data/hardware_v352.json", "03-cad/v3.5.2/data/hardware_v352.json", "c2c7b13d3a0086e3"),
       "test_final352": (Path("/home/claude/work/mechanical/v352/checks/test_final352_v1.json"), "03-cad/v3.5.2/checks/test_final352_v1.json", None),
       "rows_v7": (J / "jfwd_in718_rows_v352_v7.json", "04-fea/v352/jfwd_in718_rows_v352_v7.json", "6113d28b64d0dba5"),
       "K_js5_v2": (J / "jfwd_embed_fit_js5_v352_v2.json", "04-fea/v352/jfwd_embed_fit_js5_v352_v2.json", "e2624bf729633fb8"),
       "spring_v4": (J / "jfwd_spring_v352_v4.json", "04-fea/v352/jfwd_spring_v352_v4.json", "a277b996c2d61b83"),
       "head_fillet_v1": (J / "jfwd_head_fillet_v352_v1.json", "04-fea/v352/jfwd_head_fillet_v352_v1.json", "337883c3f2076a32"),
       "tap_wall_v1": (J / "jfwd_tapwall_v352_v1.json", "04-fea/v352/jfwd_tapwall_v352_v1.json", "bcb21243d57af998"),
       "screw_lcf_v2": (J / "jfwd_screw_lcf_v352_v2.json", "04-fea/v352/jfwd_screw_lcf_v352_v2.json", "6acdaa2febdf3f6c"),
       "texts_v3": (T / "item_c_tf1_texts_v352_v3.json", "04-fea/v352/texts/item_c_tf1_texts_v352_v3.json", "7d857240da06f4eb"),
       "rev5_cad_check_v2": (Path("/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v2.json"), "04-fea/v352/checks_rev5/test_rev5_jfwd_v2.json",
                             "32c41e1e207f9d64")}


def sha(p, n=16):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


def cl_segment(line_no, start, end):
    """Quote the text of hub CHANGELOG line `line_no` from `start` up to (not including) `end` (both must occur once)."""
    lines = CL.read_text().splitlines()
    ln = lines[line_no - 1]
    i = ln.index(start)
    assert ln.count(start) == 1, (line_no, start)
    j = ln.index(end, i) if end else len(ln)
    return {"changelog_line": line_no, "line_sha256_16": hashlib.sha256((ln + "\n").encode()).hexdigest()[:16], "text": ln[i:j].strip()}


def main(dry=False, pre=False):
    dry = dry or pre
    base_raw = HUB.read_bytes()
    assert sha(HUB) == V21_SHA, ("hub mechanical.json is not the v2.1 this writer was made for", sha(HUB))
    base = json.loads(base_raw)
    assert base["version"] == "v2.1"
    X, src, pending = {}, {}, {}
    for k, (p, hp, s16) in SRC.items():
        s = sha(p)
        if s16:
            assert s == s16, (k, p, s)
        hub = HUBE / hp
        if pre and hp.startswith("03-cad/v3.5.2/"):
            pending[k] = {"hub_exists": hub.exists(), "hub_sha_equal_dev": bool(hub.exists() and sha(hub) == s)}
        else:
            assert hub.exists() and sha(hub) == s, ("hub copy missing or different", k, hp)
        X[k] = json.loads(Path(p).read_text())
        src[k] = {"path": hp, "sha256_16": s}
    MP, MD, BOM, HW, R7, JS2, SP4, HF1, TW1, LC2, TX = (X[k] for k in ("massprops_v352", "massdelta_v352_v9", "bom_v352", "hardware_v352_v1.7",
                                                                       "rows_v7", "K_js5_v2", "spring_v4", "head_fillet_v1", "tap_wall_v1",
                                                                       "screw_lcf_v2", "texts_v3"))
    TF = X["test_final352"]
    assert MP["cad_version"] == "v3.5.2" and MD["version"] == "v9" and HW["version"] == "v1.7"
    others = {}
    for n in ("combustion.json", "electronics.json", "gnc.json", "ENGINE-BASELINE-v0.json"):
        p = HUBE / "interfaces" / n
        d = json.loads(p.read_text())
        others[n] = {"version": d.get("version"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    out = dict(base)
    out.update({"version": "v2.2", "date": "2026-10-20", "supersedes": f"v2.1 (2026-10-13, sha256/16 {V21_SHA}; archived as "
                "03-cad/v3.5.2/history/mechanical.json.e4d3e7c9df529171)", "cad_version": "v3.5.2",
                "status": ("v3.5.2 issue with the FINAL 03-cad v3.5.2 set (lead release 19:09:50Z): SIM + CALC + DERIVED + DESIGN as tagged; "
                           "physical validation pending (bench and founder test lists); margins are model results, not test results; "
                           "negatives are shown as found")})
    out["reading_rule_v352"] = ("Sections whose key ends in _v352 (and the header) govern for v3.5.2. The v2.1 sections are kept unchanged as "
                                "the record of CAD v3.3 / v3.5 / v3.5.1; where a v2.1 value conflicts with a _v352 section, the _v352 section "
                                "governs; superseded_v2p1_entries lists the v2.1 entries not to be used for v3.5.2.")
    out["scripts_v352"] = {"writer": "03-cad/v3.5.2/src/calcs/write_mechanical_json_v352.py", "writer_sha256_16": sha(Path(__file__)),
                           "mass": "03-cad/v3.5.2/src/make_all.py stage_mass (MAKE_ALL_CAD=v352) + src/calcs/mass_delta_v352.py",
                           "hardware": "03-cad/v3.5.2/src/calcs/hardware_v352.py -> data/hardware_v352.json",
                           "jfwd": "04-fea/v352/jfwd_*_v352.py (rows v7, K_js5 v2, spring v4, head fillet v1, tap wall v1, screw LCF v2)",
                           "texts": "04-fea/v352/texts/item_c_tf1_texts_v352.py (v3)"}
    out["inputs_read_v352"] = others
    out["sources_v352"] = src

    # ---------------------------------------------------------------------------------------------- mass properties (FINAL v3.5.2 set)
    gp = {}
    for st in ("wet", "mid", "burnout", "nograin"):
        gp[st] = {}
        for g in ("engine", "fixed", "ring", "horn", "pushrod", "all"):
            e = MP["states"][st][g]
            gp[st][g] = {"m_kg": e["m_kg"], "cg_mm": e["cg_mm"], "cg_m": [round(x / 1000.0, 6) for x in e["cg_mm"]],
                         "I_pivot_kgm2": e["I_pivot_kgm2"], "I_cg_kgm2": e["I_cg_kgm2"]}
    gnc = MD["gnc_trigger"]
    out["gimballed_mass_properties_v352"] = {
        "source": "03-cad/v3.5.2/massprops_v3.5.2.json (FINAL set; CAD volume x engmat density + COTS + hardware carried as max(0.20 kg "
                  "allowance, CALC sum) at the host parts)", "frame": MP["frame"], "z_head_mid_mm": MP["z_head_mid_mm"],
        "states_definition": "wet = fresh grain; mid = half the max-thrust-case fuel burnt (pivot definition state); burnout = the max-thrust "
                             "case fuel burnt; nograin = no grain (03-cad/src/build.py mass_ledger)",
        "groups_definition": "engine = the gimballed body (thrust chamber, grain, collar + levers, inner pins, pintle stack, engine shares of "
                             "hose and lines, J-FWD hardware); fixed = the fixed module; ring, horn, pushrod as named; all = every group",
        "hardware_rule": MP["hardware_rule"], "hardware_carried": MP["hardware_carried"], "grain_mass_wet_kg": MP["grain_mass_wet_kg"],
        "states": gp, "evidence_classes_kg": MP["evidence_classes_kg"],
        "delta_vs_v3.5.1": {"source": "03-cad/v3.5.2/massdelta_v3.5.2_vs_v3.5.1.json v9", "states": MD["states"], "gnc_trigger": gnc,
                            "rows_mid_by_part": MD["rows_mid_by_part"]},
        "for_gnc": (f"landing-mass change vs v3.5.1 {gnc['dm_landing_kg']:+.4f} kg ({gnc['dm_landing_without_TC09_thinning_kg']:+.4f} kg "
                    f"without the conditional TC-09 thinning): {gnc['verdict']}; GNC keeps the v3.5.1 mass properties; the v3.5.2 values are "
                    "for information and for the ICD-11 mass"),
        "tag": "DERIVED (CAD) + CALC (hardware) + COTS as tagged in evidence_classes_kg; not weighed"}

    # ---------------------------------------------------------------------------------------------- design changes v3.5.2 (per part, from massdelta v9)
    out["design_changes_v352"] = {
        "changed_parts_vs_v3.5.1": [r["pn"] for r in TF["parts_changed_vs_v351"]],
        "per_part_mass_and_why": [{"pn": r["pn"], "group": r["group"], "delta_kg": r["delta_kg"], "why": r["why"]} for r in MD["rows_mid_by_part"]],
        "changes_in": MD["changes_in"], "not_in": MD["not_in"],
        "final_set_check": {"source": "03-cad/v3.5.2/checks/test_final352_v1.json", "TC-01_final_vs_interim": {
            k: TF["ENG-TC-01_final_vs_interim"][k] for k in ("dV_mm3", "interim_minus_final_mm3", "final_minus_interim_mm3", "final_minus_interim_rule")},
            "bom_vs_interim": {k: TF["bom_vs_hub_interim"][k] for k in ("added", "removed", "changed")}}}

    # ---------------------------------------------------------------------------------------------- J-FWD route (i)
    H101 = next(L for L in HW["lines"] if L["id"] == "HW-101")
    H170 = next(L for L in HW["lines"] if L["id"] == "HW-170")
    JF1 = R7["J_F1"]
    st3 = ("SOAK52", "SOAK70", "SOAK", "FA1S")
    row = lambda st, k: R7["states"][st]["rows"]["3750"][k]
    THE_ROW = {st: R7["TC02_thread_shear_full_row"]["rows"][st]["3750"]["THE_ROW"]["MS_y"] for st in st3}
    assert THE_ROW["SOAK"] == 0.104
    HG = HF1["governing_and_thread_root_comparison"]["3750"]
    TWc = TW1["rows"]["3750"]["cases"]
    TWg = min((v["TC02_thread_T"]["MS_y"], k) for k, v in TWc.items() if k.endswith("ruled_+/-0.25deg_net_GOVERNING"))
    SEAT = SP4["lead_16_07Z_item5_seated_and_solid"]
    out["jfwd_v352"] = {
        "route": "route (i) (lead 16:53Z R2, CAD check ACCEPTED 17:55:55Z, rows v7 and companions ACCEPTED 18:36:37Z)",
        "hardware": {"HW-101": {k: H101[k] for k in ("item", "standard", "size", "length_mm", "grade", "head_form_F3", "unit_mass_g", "torque_Nm",
                                                     "torque_basis", "thread_locker", "status", "action", "assembly_note")},
                     "HW-170": {k: H170[k] for k in ("item", "standard", "size", "grade", "qty", "unit_mass_g", "status", "action", "assembly_note")},
                     "M-T1J": HW["rules"]["tightening_methods"]["M-T1J"], "J-F1": H101["test"]},
        "J_F1": JF1,
        "rows_3750_governing": {
            "THE_ROW_TC02_thread_shear_MS_y": THE_ROW,
            "THE_ROW_note": "file values (TC02_thread_shear_full_row); SOAK52 +0.045 is a FLAG (< 0.05)",
            "under_head_full_float_MS_strain_ASSUMED": {st: row(st, "TC01_under_head_band_neuber")["MS_strain"] for st in st3},
            "TC01_flat_bearing_registered_stack_MS": {st: row(st, "TC01_flat_bearing")["MS_vs_Fbry"] for st in st3[:3]},
            "screw_tension_MS_y": {st: row(st, "screw_tension_234_1b")["MS_y"] for st in st3[:3]},
            "head_on_spring_MS_y_min": min(row(st, "head_on_spring_IN718")["MS_y"] for st in st3 + ("PRELOAD",)),
            "found_negatives": {"seat_ring_line_PQ_2Fty": {st: row(st, "seat_line_d6p051_z0_PQ")["MS_PQ_2Fty"] for st in st3[:3]},
                                "screw_fibre_yield": {st: row(st, "screw_fibre_soak")["MS_y_fibre"] for st in st3[:3]},
                                "screw_fibre_shakedown_min": min(row(st, "screw_fibre_soak")["MS_shakedown"] for st in st3[:3])},
            "flags_and_negatives_list": R7["flags_within_0.05_or_negative"]},
        "screw_LCF_thread_root_C6": {"per_firing": {"N_allow": HG["i_firing"]["thread_root_N_allow"], "MS": HG["i_firing"]["thread_root_MS"]},
                                     "assembly_from_zero": {"N_allow": HG["ii_assembly_from_zero"]["thread_root_N_allow"],
                                                            "MS": HG["ii_assembly_from_zero"]["thread_root_MS"]},
                                     "status": "FOUND NEGATIVE (183 (1)(c)); C6 OPEN; paths 2 ((b1) FE levers / select-fit band) and 3 "
                                               "(qualification test, TO-DEFINE, founder) remain; path 1 (MJ) closed NOT SOURCED"},
        "head_fillet": {"static": HG["static"], "per_firing": {k: HG["i_firing"][k] for k in ("fillet_N_allow", "fillet_MS", "fillet_governs")},
                        "assembly_from_zero": {k: HG["ii_assembly_from_zero"][k] for k in ("fillet_N_allow", "fillet_MS", "fillet_governs")},
                        "tags": "Kt LITERATURE (secondary, via AMESweb citing Pilkey 2005); the Pilkey page and the T-head Kt TO-SOURCE; "
                                "head-end resultants carried over ASSUMED (lead 18:36:37Z); from zero = FOUND NEGATIVE, not governing"},
        "tap_wall": {"governing_case": TWg[1], "MS_y": TWg[0], "walls_mm": TW1["walls_mm"], "verdict": TW1["verdict"],
                     "to_confirm": "P_torch and its distribution along the torch passage (REV-COMB-4)"},
        "spring_v4": {"verdict": "all 24 cases seated at both k_b ends, both families, R 0 to 0.80, both springs",
                      "F_S_min_N_by_case": {k: v["F_S_min_N"] for k, v in SEAT.items()}},
        "K_js5_v2_no_spring_record": JS2["stop_test_lead_F1"],
        "founder_rules": {"single_use": ("J-FWD screws are new at every assembly, never reused or re-torqued; removed screws are kept per hole "
                                         "and inspected at 10x plus dye penetrant at the thread root AND the head-to-shank fillet, as data "
                                         "(lead 16:53Z R3 + LEAD ADDITION 18:36:37Z)"),
                          "C4_procedure": TX["item_C"]["C4_assembly_step_founder_procedure"],
                          "C6": TX["item_C"]["C6_founder_action_list_related"]},
        "drawing_texts": "04-fea/v352/texts/item_c_tf1_texts_v352_v3.json item_C C8 (TC-01 / TC-02 rev 5, ENG-HW-101-IN718, HW-170, M-T1J, J-F1)"}

    # ---------------------------------------------------------------------------------------------- lead rulings quoted (hub CHANGELOG)
    out["lead_rulings_quoted_v352"] = {
        "abort_value_A150_243_3": cl_segment(243, "(3) ABORT VALUE (16:53Z)", "(4) SLACK FIX (16:53Z)"),
        "rev5_jfwd_245_4": cl_segment(245, "(4) REV-5 J-FWD (17:55:55Z, on line 244)", "(5) ROWS V7 ACCEPTED"),
        "rows_v7_accepted_245_5": cl_segment(245, "(5) ROWS V7 ACCEPTED", "(6) DISK AND THE CHAIN E TAIL")}
    out["requests_v352"] = [
        "REQUEST Electronics (lead 243 (3)(a) / (b)): v2.11 shows the false-trip side of the case-abort channel (TC class, CJC, ADC, "
        "persistence filter) inside +12.3 K at A = 150 C, and states the low-reading tolerance including the surface-mount error (it sets "
        "the T-F1 exposure temperature).",
        "REQUEST Combustion (REV-COMB-4): P_torch and its distribution along the torch passage at the J-FWD taps (az 18 / 342), for the "
        "TC-02 tap-wall row (04-fea/v352/jfwd_tapwall_v352_v1.json, MS_y +0.814 on a uniform passage pressure: TO-CONFIRM).",
        "INFORMATION GNC: v3.5.2 landing mass change below the 0.10 kg trigger with and without the conditional TC-09 thinning: no re-fly "
        "by mass (gimballed_mass_properties_v352.for_gnc).",
        "REQUEST Founder (test list): J-F1 on the flight lots with the spring items and the Prescale footprint item (TO-VERIFY) before the "
        "first J-FWD assembly; C6 path 3 qualification test TO-DEFINE; T-F1 gate before the first static fire."]
    out["open_items_v352"] = [
        "C6 OPEN: J-FWD screw LCF at the thread root FOUND NEGATIVE (paths 2 and 3); single-use founder rule in force",
        "head-to-shank fillet: Pilkey page and T-head Kt TO-SOURCE; head-end resultants ASSUMED",
        "tap wall: P_torch and its distribution TO-CONFIRM (REV-COMB-4)",
        "under-head row at full float: FLAG, ASSUMED mean-pressure scaling (SOAK52 +0.039); THE ROW SOAK52 +0.045 FLAG",
        "known negatives for FE confirmation: seat ring line P+Q, screw fibre yield (shakedown positive); re-map after the chain E tail "
        "((b1), soak352g/h, (b2'))",
        "J-F1: Prescale footprint TO-VERIFY (film grade TO-SELECT); J-F1b cycle temperature TO-RULE; LOCTITE 243 tap-zone temperature at "
        "the abort TB states TO-VERIFY",
        "ENG-HW-101-IN718 drawing TO-DRAW (pilot coaxiality dia 0.02 TO-CONFIRM with the maker; spring orientation TO-DEFINE); HW-170 "
        "TO-QUOTE (spring A / B, relaxation data at about 160 C), reuse TO-RULE",
        "ENG-TC-13 registration shoulder screws TO-DRAW; match-drill fixture with the index pin and guide bushings TO-DRAW (shop tooling); "
        "head-shoulder gap gauge 2.00 +/-0.02 TO-CONFIRM",
        "T-F1 / 183 (1)(d) OPEN for TC-01 / TC-02 at every abort value and in nominal operation",
        "TC-09 thinning (206 (2a)) conditional on its re-run, as in the interim"]
    out["superseded_v2p1_entries"] = {
        "gimballed_mass_properties": "CAD v3.3 basis: use gimballed_mass_properties_v352",
        "icd_airframe.ICD-11_mass": "CAD v3.5 massprops: use gimballed_mass_properties_v352 (03-cad/v3.5.2/massprops_v3.5.2.json)",
        "design_changes_v35.J-FWD_screws": "A4-80 (lead 177 (2)): superseded by route (i), ENG-HW-101-IN718 + HW-170 (jfwd_v352)",
        "fa1.fmea_wording_proposal.J-FWD 8 x M5": "8 x M5 A4-70 / A4-80: superseded by 10 x ENG-HW-101-IN718 with HW-170 (jfwd_v352)",
        "fa1.joints_table": "J-FWD 8 x M5 A4-70 rows: superseded by jfwd_v352 (rows v7)"}
    HDR = ("id", "version", "date", "owner", "supersedes", "status", "units", "written_to", "scripts", "inputs_read", "errata_to_v1", "frames")
    out["not_re_derived_v352"] = {
        "sections": [k for k in base if k not in HDR],
        "rule": ("these v2.1 sections were not re-derived for v3.5.2: their values are the v2.1 record on the CAD basis each one states "
                 "(v3.3 / v3.5 / v3.5.1); superseded_v2p1_entries names the entries that v3.5.2 replaces; before using any other entry that a "
                 "v3.5.2 change could touch (design_changes_v352: 11 parts + hardware), ask Mechanical")}
    s = json.dumps(out, indent=1, default=str)
    if dry:
        print(json.dumps({"mode": "pre" if pre else "dry", "pending_03cad_hub_copies": pending, "n_bytes": len(s),
                          "sha256_16_if_written": hashlib.sha256(s.encode()).hexdigest()[:16],
                          "new_keys": [k for k in out if k not in base], "header": {k: out[k] for k in ("version", "date", "cad_version", "supersedes")}},
                         indent=1))
        return out
    st = os.statvfs(HUB)
    free = st.f_bavail * st.f_frsize
    assert free - len(s) >= 2.20 * 2 ** 30, ("free space below 2.20 GiB: not written", free)
    cur = HUB.read_bytes()                           # re-read just before writing (shared folder)
    assert cur == base_raw, "hub mechanical.json changed under us"
    HUB.write_text(s)
    back = json.loads(HUB.read_text())
    assert back["version"] == "v2.2" and back["cad_version"] == "v3.5.2" and "jfwd_v352" in back and back["gimballed_mass_properties"] == base["gimballed_mass_properties"]
    print("written", HUB, sha(HUB), len(s), "bytes")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv, pre="--pre" in sys.argv)
