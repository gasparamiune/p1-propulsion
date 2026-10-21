"""m2_gnc_json_v31_rev2p1 v1.0 (GNC rev2.1, 2026-10-13): rebuild of the gnc.json v3.1 staging rev2 (a5564b45ed7fb463) as
rev2.1 for the publication gate (REV-GNC-3 RV3-01 (a)-(f), RV3-08, RV3-09; lead CHANGELOG line 181 (1)). Publication work only:
no new flight. Every number added here is either recomputed from the staged rev2 tables (m2_rev2p1_comparators v1.0), taken
from the bit-check records (m2_bit29_g6_recheck v1.0), cited from the independent reviewer's files (REV-GNC-3; marked
REVIEWER), or DERIVED from cited mass files (m2_mass_v35 v1.0; no flight).

Conventions used for superseded content (so that a document check can find every stale statement):
  - a replaced value keeps the old text under a sibling key ending in '_superseded_rev2p1';
  - a string kept for history is prefixed 'SUPERSEDED (rev2.1 ...)' or carries an inline '[SUPERSEDED rev2.1 ...]' /
    '[NOT ADOPTED ...]' / '[REFUTED ...]' marker next to the stale phrase;
  - the self-check at the end scans every string for the stale patterns of REV-GNC-3 §4.8 and fails the build if one has
    no marker within 200 characters or no superseded key on its path.
Output: out/rev3/rev2p1/gnc_v3.1_staging_rev2p1.json (deterministic: no time stamps beyond the date)."""
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

VERSION = "m2_gnc_json_v31_rev2p1 v1.0"
SP = "/home/claude/work/space"
HUB = "/home/claude/work/shared-fallback/engine"
R2 = f"{HUB}/01-systems-gnc/staging_v3.1/rev2"
R2JSON = f"{R2}/results/gnc_json/gnc_v3.1_staging_rev2.json"
R2JSON_SHA16 = "a5564b45ed7fb463"
OUTD = f"{SP}/out/rev3/rev2p1"
OUT = f"{OUTD}/gnc_v3.1_staging_rev2p1.json"
CHLOG = f"{HUB}/interfaces/CHANGELOG.md"
REVW = f"{HUB}/reviews/REVIEW-GNC-R2.md"
RVD = f"{HUB}/reviews/gnc/rev2"
COMP = f"{OUTD}/comparators_rev2p1.json"
G6R = f"{OUTD}/bit29_g6_recheck.json"
MASS = f"{SP}/out/rev3/mass_v35/mass_v35_vs_v3d.json"
BIT_TOOL = f"{SP}/gnc_dev3/scripts/m2_bitcheck_v29.py"
H20 = f"{HUB}/02-combustion/data/v2p4a/unpurged_start_check_v2p4a.json"
STAGE = "01-systems-gnc/staging_v3.1/rev2p1"
REVIEWER_FILES = OrderedDict([
    ("late_commit_P_vs_delay_and_lead", "logs/s07_latecommit.out"),
    ("late_commit_paired_loss", "logs/s08_latecommit_paired.out"),
    ("rg16_detector_output_budget", "logs/rv_rg16_budget.out"),
    ("rg16_detector_output_budget_json", "results/rg16held/rv_rg16_budget.json"),
    ("rg16_held_H_cal_comp", "results/rg16held/rg16held_H_cal_comp_path.json"),
    ("rg16_held_H_cal", "results/rg16held/rg16held_H_cal_path.json"),
    ("v_probe_flights", "logs/vprobe1.log"),
    ("v_probe_flights_2", "logs/vprobe2.log"),
    ("v_probe_paired", "logs/s13_vprobe_cmp.out"),
    ("v_flameout_mechanism", "logs/s14_fo_mech.out"),
    ("g_decided_path", "logs/s15_g_decided.out"),
    ("m60_pairs", "logs/s09_m60.out"),
    ("trim_tables", "logs/s03_trim.out"),
    ("trim_wind", "logs/s04_wind.out"),
    ("m30_interp", "logs/s16_m30_interp.out"),
    ("bitcheck_reviewer", "results/bit29/bitcheck_v29_reviewer.json"),
])
LEAD_LINES = (175, 177, 181, 182, 183)
REF_LINES = (174, 176, 178, 179, 180)
STALE = OrderedDict([
    ("650 N confirmed", r"650 N[^.;]{0,60}(CONFIRMED|confirmed)|(CONFIRMED|confirmed)[^.;]{0,30}650 N"),
    ("<= 1 % (1 sigma)", r"(<=|≤) ?1 ?% \(1 sigma\)"),
    ("A1 300 m baseline", r"300 m baseline|A1 300 m|apogee \(300 m\)|A1 at 300 m"),
    ("0.6 s delay costs no P", r"costs no measurable P|delay <= 0\.6 s costs"),
    ("FC_THRUST budget OPEN", r"error budget: OPEN"),
    ("pcf_tmax 0.8 s proposal", r"pcf_tmax 0\.8"),
    ("time-only release term", r"0xFFFF AND t >= t_E2"),
    ("per-flight RG-16 support", r"per-flight form[^.;]{0,60}provisional support"),
    ("k_hat freeze", r"\bfreeze[^.;]{0,40}(k_hat|apex)|(k_hat|apex)[^.;]{0,40}\bfreeze"),
    ("0.30 kg mass trigger", r"0\.30 kg[^.;]{0,40}trigger|trigger[^.;]{0,40}0\.30 kg"),
])
MARKERS = ("SUPERSEDED", "WITHDRAWN", "NOT ADOPTED", "NOT adopted", "REFUTED", "REPLACED", "HISTORY", "NOT armed", "not armed")


def sha(p, n=16):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]


def shas(s, n=16):
    return hashlib.sha256(s.encode()).hexdigest()[:n]


def jload(p):
    return json.load(open(p), object_pairs_hook=OrderedDict)


def changelog_lines():
    L = open(CHLOG, encoding="utf-8").read().split("\n")
    out = OrderedDict()
    for n in LEAD_LINES + REF_LINES:
        out[n] = L[n - 1]
    for n in LEAD_LINES:
        if " | lead | (decision) | " not in out[n]:
            raise RuntimeError(f"CHANGELOG line {n} is not a lead decision: {out[n][:80]}")
    return out


def mark(s, why):
    return f"SUPERSEDED (rev2.1; {why}): {s}"


def inline(s, phrase, note):
    if phrase not in s:
        raise RuntimeError(f"phrase not found for an inline marker: {phrase}")
    return s.replace(phrase, f"{phrase} [{note}]", 1)


def comparators_table(cj):
    rows = []
    for r in cj["rows"]:
        p = r["pooled"]
        rows.append(OrderedDict(name=r["claim"], case=r["case"], comparator=r["comparator"], cls=r["comparator_class"],
                                bases=r["bases"], n=p["n"], P_case=p["P_case"], P_comparator=p["P_comparator"],
                                lost=p["lost"], gained=p["gained"], p_exact=float(f"{p['p_exact']:.4g}"), loses=p["loses"],
                                note=r.get("note", "")))
    return rows


def self_check(d):
    hits = []

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, path + [str(k)])
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, path + [str(i)])
        elif isinstance(x, str):
            for name, pat in STALE.items():
                for m in re.finditer(pat, x):
                    win = x[max(0, m.start() - 200): m.end() + 200]
                    ok = (any("superseded" in p.lower() or p == "rev2p1_marker" for p in path)
                          or x.startswith(("SUPERSEDED", "HISTORY")) or any(mk in win for mk in MARKERS))
                    hits.append(dict(pattern=name, path="/".join(path), marked=bool(ok),
                                     context=x[max(0, m.start() - 80): m.end() + 80]))
    walk(d, [])
    un = [h for h in hits if not h["marked"]]
    return OrderedDict(rule="every string matching a stale pattern of REV-GNC-3 §4.8 must sit under a key containing "
                            "'superseded', start with SUPERSEDED/HISTORY, or carry one of " + ", ".join(MARKERS) +
                            " within 200 characters of the match (author's check; the independent document check follows)",
                       patterns=STALE, hits=len(hits), unmarked=len(un), unmarked_list=un,
                       hit_paths=sorted({h["path"] for h in hits}))


def main():
    if sha(R2JSON) != R2JSON_SHA16:
        raise RuntimeError("staged rev2 JSON hash mismatch")
    d = jload(R2JSON)
    cl = changelog_lines()
    cj, g6, mj, h20 = jload(COMP), jload(G6R), jload(MASS), jload(H20)
    rvh = OrderedDict((k, dict(file=f"reviews/gnc/rev2/{v}", sha256_16=sha(f"{RVD}/{v}"))) for k, v in REVIEWER_FILES.items())
    rv_ref = lambda *ks: "; ".join(f"{rvh[k]['file']} ({rvh[k]['sha256_16']})" for k in ks)  # noqa: E731
    lines_sha = shas("\n".join(cl[n] for n in sorted(cl)))
    ld = lambda n: f"CHANGELOG line {n}"  # noqa: E731
    mt = mj["totals"]
    mass_txt = (f"CAD v3.5 against ledger v3d: landing mass +{mt['landing_mass_delta_kg']['v']:.3f} kg DERIVED (gimballed "
                f"+{mt['gimballed_delta_kg']['v']:.3f} kg, TVC inertia about the pivot +4.8 to +5.5 %; fixed "
                f"+{mt['fixed_delta_kg']['v']:.3f} kg incl. the ring +0.104 kg, the bleed fixed side +0.764 kg of which the "
                f"valve pair 0.60 kg ASSUMED, EL-11/12 +0.065 kg, horns and pushrods +0.037 kg omitted in v3d) "
                f"(m2_mass_v35 v1.0, {sha(MASS)}); the 0.10 kg trigger is met; flights at the v3.5 ledger are rev3 P2; "
                "massprops_v3.5.1 pending (lines 182 (8), 183)")
    new = OrderedDict()
    # ---------------------------------------------------------------- identity
    d["version"] = "v3.1-staging-rev2.1"
    d["date"] = "2026-10-13"
    st_old = d["staging"]
    d["staging"] = OrderedDict(
        v=("STAGING rev2.1 for the lead: not interfaces/gnc.json. Rebuild of rev2 (a5564b45ed7fb463) for the gnc.json v3.1 "
           "publication gate: RV3-01 (a)-(f) superseded markers and missing entries, RV3-08 bit-check record, RV3-09 named "
           "comparators, RG-16 detector-output results and the V probes cited from the reviewer, lead decisions folded "
           "through CHANGELOG line 183 (decisions 175, 177, 181, 182, 183). No new flight. An independent document check "
           f"follows ({ld(181)} (1)); then v3.1 is published by the lead."),
        tag="STAGING", staging_superseded_rev2p1=st_old)
    d["supersedes"] = "nothing yet (staging); rev2.1 replaces staging rev2 for the document check; on publication it would supersede gnc.json v3"
    # ---------------------------------------------------------------- (a) status
    d["status_superseded_rev2p1"] = d["status"]
    d["status"] = (
        "v3.1 STAGING rev2.1 (2026-10-13): NOT PUBLISHED. Rebuild of rev2 (a5564b45ed7fb463) for the gnc.json v3.1 publication "
        "gate (REV-GNC-3 RV3-01; lead CHANGELOG line 181 (1)); publication only, no new flight. Decided state for GNC (SIM "
        "evidence; no physical validation): (1) A1 apogee target 285 m ADOPTED with conditions (lines 175 (1), 181 (6)): the "
        "launch-commit wind rule W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s is HARD for A1; 285 m on all four bases and on "
        "pl, e19, the prep path, L400 and PURGE NOT RUN is flown in rev3 before SIL/HIL freeze. (2) Mass change control "
        "(181 (5)): re-fly at the actual ledger for any confirmed landing-mass growth >= 0.10 kg over ledger v3d; "
        + mass_txt + ". (3) FC_THRUST NOT armed on A1 (168 (5), 175 (6), 181 (3)); the rev2 threshold statement '650 N / "
        "20 ms confirmed' and the '<= 1 % (1 sigma)' mass-estimate requirement are SUPERSEDED (RG-16 budget form 168 (5); "
        "random term at the detector output 175 (6); per-flight support WITHDRAWN and a PROVISIONAL detection-latency "
        "allowance of 0.5 s from the onset of the 670 N plateau, strict windowed form 2.973 % vs 2.985 % on an ASSUMED white "
        "vibration model, REVIEWER-computed, not robust (181 (3)); the trajectory consequence of 0.5 s at 670 N and the B1 "
        "miss side are rev3 items). (4) Late purge commit (181 (2)): PURGE commits iff the lead from the commit to the plain "
        "relight trigger is >= L*, else no purge; L* = 1.7 s if an unpurged start is LO, 1.3 s if HI; FSW interim 1.7 s; the "
        "rev2 basis that a T_fire delay up to 0.6 s costs no P is WITHDRAWN (REVIEWER paired loss 7.4 % at 0.50-0.55 s and "
        "22.4 % at 0.55-0.60 s); 'the 0.81 s plan holds' is scoped to the predictor path. (5) Drogue release with Pc invalid "
        "(181 (4)): R2 ADOPTED in design over R1; pcf_tmax stays 0.5 s; 0.8 s NOT adopted; R2 v2 is a rev3 item. (6) The "
        "k_hat / apex freeze on Pc invalid is REFUTED and withdrawn (175 (4)); its replacement (re-reference to throttle-map "
        "thrust) is OPEN and is flown on FSW-R2 with a map-error band in rev3 (181 (7)); Pc VALID is a launch-commit "
        "condition. (7) A1 FMEA: no over-thrust detector after an in-flight Pc loss (181 (3), RV3-12). Earlier status text: "
        "status_superseded_rev2p1 (rev2).")
    # ---------------------------------------------------------------- (b) FC_THRUST block and its copies
    ot = d["over_thrust_fc_thrust"]["v"]
    why_fc = "FC_THRUST NOT armed on A1; RG-16 form adopted, lead lines 168 (5), 175 (6), 181 (3)"
    thr = ot["proposal"]["threshold"]
    thr["v_superseded_rev2p1"] = thr["v"]
    thr["v"] = ("CANDIDATE only: 650 N held 20 ms (3 consecutive 100 Hz frames) on the tau 20 ms estimate, NOT armed on A1 "
                "(lead 168 (5), 181 (3)); the rev2 word CONFIRMED is WITHDRAWN. Arming on any mission needs the RG-16 budget "
                "at the detector output with the PROVISIONAL 0.5 s detection-latency allowance from the onset of the 670 N "
                "plateau (strict windowed form, no window-gain credit) and its trajectory consequence (rev3 P5)")
    thr["tag"] = "DESIGN candidate (rev2.1); SIM evidence"
    mer = ot["proposal"]["mass_estimate_requirement"]
    mer["v_superseded_rev2p1"] = mer["v"]
    mer["v"] = ("REPLACED by the RG-16 budget form (lead 168 (5)): total = 3 x RSS(random terms) + sum of bias bounds <= the "
                "allowed 1 - 650/670 = 2.985 % at the detector output (175 (6), 181 (3)); requirement candidates: weighing at "
                "ARM 20 g at 1 sigma (scale TO-DEFINE), static-fire flow-calibration residual 1.5 %; the rev2 '1 % (1 sigma)' "
                "requirement is SUPERSEDED")
    mer["tag"] = "DESIGN (LEAD 168 (5)); rev2 proposal SUPERSEDED"
    ot["claim"] = mark(ot["claim"], why_fc)
    ot["finding"] = mark(ot["finding"], why_fc)
    ot["refutation"][4] = mark(ot["refutation"][4], "the 1 % requirement is replaced by the RG-16 budget form, lead 168 (5)")
    ot["unknowns"][5] = ot["unknowns"][5] + " [rev2.1: candidate threshold only; FC_THRUST NOT armed on A1, 181 (3)]"
    ot["unknowns"][10] = ot["unknowns"][10] + " [rev2.1: FC_THRUST NOT armed on A1, 181 (3); the question returns with arming]"
    ot["rev2p1_status"] = OrderedDict(
        v=("FC_THRUST NOT armed on A1. The evidence above (rev2, m2_fc_thrust) stays as SIM history; its proposal is "
           "superseded as stated in proposal.threshold and proposal.mass_estimate_requirement. Current definition: RG-16 "
           "random term at the detector output (after its filtering and hold); the instantaneous form fails (REVIEWER 4.20 % "
           "/ 4.76 % with the hold shift vs 2.985 %); the strict windowed form over 0.5 s passes with almost no margin "
           "(REVIEWER 2.973 %) on an ASSUMED white vibration model; lead 181 (3): PROVISIONAL detection-latency allowance "
           "0.5 s; if the trajectory consequence is unacceptable or a measured spectrum removes the margin, the detector "
           "changes, not the allowance"),
        tag="DESIGN (LEAD 181 (3)); REVIEWER SIM", source=rv_ref("rg16_detector_output_budget", "rg16_detector_output_budget_json"))
    oi = d["open_items"]
    oi[22] = mark(oi[22], why_fc)
    oi[29] = mark(oi[29], "mass-estimate error is budgeted by the RG-16 form, lead 168 (5)")
    oi.append("rev2.1: FC_THRUST arming (any mission) needs the RG-16 detector-output budget with the 0.5 s latency allowance, "
              "its trajectory consequence at 670 N on A1 and B1 and the B1 miss side (lead 181 (3); rev3 P5)")
    oi.append("rev2.1: purge commit rule L* (lead 181 (2)): Combustion settles LO/HI and the unpurged-start hazard; Combustion "
              "v2.4a H20 / OI-31 proposes 'no commit by the deadline -> no relight on that pass' (not decided by the lead)")
    oi.append("rev2.1: R2 v2 (baseline at E2 or drogue-drag compensation, threshold for the window, pcf_tmax 0.5 / 0.8 s with "
              "L400, pcf_k 0.875, flame-out, onsets 0.005 / 0.010 s, landings after 0.5-0.8 s releases); Combustion bounds "
              "cold-flow apparent thrust under the drogue (lead 181 (4); rev3 P4)")
    oi.append("rev2.1: k_hat / apex re-reference to throttle-map thrust with Pc invalid flown on FSW-R2 with a map-error band "
              "(lead 181 (7); rev3 P7)")
    oi.append("rev2.1: mass change control (lead 181 (5)): " + mass_txt)
    ans = d["answers_to_requests"]
    k_ans = "lead_fc_thrust_closure_item_1_2026-10-13"
    ans[k_ans] = mark(ans[k_ans], why_fc)
    ldv = d["lead_decisions_2026-10-13"]["v"]
    for k in ("over_thrust_abort", "fc_thrust_closure_item_1"):
        ldv[k + "_status_rev2p1"] = ("HISTORY of the decision record; current: FC_THRUST NOT armed on A1 (lead 168 (5), "
                                     "175 (6), 181 (3)); RG-16 at the detector output; PROVISIONAL 0.5 s latency allowance")
    # ---------------------------------------------------------------- 300 m baseline marker (flight profile)
    fp = d["flight_profile"]["recommended_baseline"]
    fp["note"] = inline(fp["note"], "MECO on predicted apogee (300 m)",
                        "SUPERSEDED rev2.1: A1 MECO on predicted apogee 285 m, lead lines 168 (4), 175 (1), 181 (6)")
    fp["note_rev2p1"] = ("A1 apogee target 285 m (h_target trim) ADOPTED with conditions (175 (1), 181 (6)): W10 < 6 m/s AND "
                         "sigma_u(3 m) <= 1.0 m/s HARD at launch commit; coverage flights rev3 P3; mass growth re-fly rev3 P2 "
                         "(" + mass_txt + ")")
    # ---------------------------------------------------------------- (c) G basis corrected
    G = d["rev2"]["amendment_G_late_commit"]
    G["finding_superseded_rev2p1"] = G["finding"]
    G["finding"] = (
        "FINDING (amendment a), corrected in rev2.1 (RV3-02; lead 181 (2)). The rule 'never T_fire before 1.9 s of flow; "
        "delay T_fire instead' is safe only for an early commit. Commit-floor sweep on state e19 (Tp1.9 robust-edge table), "
        "A1_none / A1J_pc, seed 101, 500 runs each, against the decided e19 commit (C-DEC, comparators_rev2p1): commit at the "
        "plain trigger (T_fire delayed 2.30 s) 0.000 (-988/+0); forced commit at 100 m -3/+4 (p 1.0; T_fire delay <= 0.64 s); "
        "90 m -51/+2 (p 3.2e-13, LOSES); 80 m -536/+0; 70 m -968/+0. The rev2 DERIVED sentence 'a T_fire delay up to ~0.6 s "
        "costs no measurable P' is WITHDRAWN: the reviewer's paired table on the same flights (runs that succeed with the "
        "decided commit, lost when the commit is forced late) gives 0.2 % lost at 0-0.2 s of delay, 0.9-1.4 % at 0.2-0.4 s, "
        "4.1 % at 0.40-0.45 s, 6.2 % at 0.45-0.50 s, 7.4 % at 0.50-0.55 s, 22.4 % at 0.55-0.60 s, 46 % at 0.65-0.70 s and "
        "100 % beyond 1.0 s; by lead time commit -> plain trigger: 100 % lost below 1.30 s, 91 % at 1.30-1.50 s, 64 % at "
        "1.50-1.60 s, 40 % at 1.60-1.70 s, 21 % at 1.70-1.75 s, 9 % at 1.75-1.80 s, <= 5 % from 1.85 s, ~1 % from 1.90 s "
        "(REVIEWER, " + rv_ref("late_commit_P_vs_delay_and_lead", "late_commit_paired_loss") + "). A deadline with no "
        "measurable loss would be about plain trigger - 1.9 s. Rule adopted by the lead (181 (2)): PURGE commits iff the lead "
        "to the plain relight trigger is >= L*, else no purge; L* = 1.7 s if an unpurged start is LO (break-even against "
        "PURGE NOT RUN LO, P_total ~0.75) and 1.3 s if HI (skipping gives P_total 0); FSW interim 1.7 s until Combustion "
        "settles LO/HI and the unpurged-start hazard (the 175 (3) refutation clause stands). Scope: the decided predictor "
        "commits >= 2.66 s before the plain trigger in every run where the plain trigger fired (2000 runs; flow >= 2.387 s; "
        "REVIEWER " + rv_ref("g_decided_path") + "), so the rule acts only on a contingency (gate or predictor failure); 'the "
        "0.81 s plan holds' is scoped to the predictor path. The contingency re-admits flows of 1.9-2.4 s, for which the plan "
        "check gives no cover (e19|G73|L400 vs liq|none|L400 -39/+3, p 5.6e-9, LOSES, comparators_rev2p1); its probability "
        "and the contingency flights with the L400 plateau are rev3 P6. Combustion v2.4a H20 / OI-31 (PURGE NOT RUN LO worst: "
        "every light followed by a 23.4 cm3 vapour gap; proposal 'no commit by the deadline -> no relight on that pass') is "
        "pending a lead decision and would move L* (rev3 P6 adds it as a third case).")
    G["tag_rev2p1"] = "SIM (rev2 flights) + REVIEWER paired tables; DESIGN rule LEAD 181 (2) (PROVISIONAL)"
    # ---------------------------------------------------------------- (d) relight conditions
    rc = d["requirements"]["ignition"]["relight_conditions"]
    rc["v_superseded_rev2p1"] = rc["v"]
    rc["v"] = ("liquid settled aft by the drogue (~1 g); tank P >= 3.5 MPa; chamber purged per the purge commit rule (PURGE "
               "commits iff the lead to the plain relight trigger is >= L*, interim 1.7 s; else the relight proceeds unpurged, "
               "lead 181 (2)); ignition at the floor; drogue release on the adopted predicate with the Pc-invalid term R2 "
               "(lead 181 (4)): RELEASE iff RUN AND b4 AND [(Pc valid AND Pc >= 300 kPa abs) OR b7 OR (d2-d3 = 0xFFFF AND "
               "m_est x (filtered axial specific force - its drogue-descent baseline) >= 37.16 N on 3 consecutive 100 Hz "
               "frames with the ECU in RUN)], latched; with Pc invalid and no R2 confirmation by t_E2 + pcf_tmax (0.5 s): "
               "hold the drogue and command ECU ABORT. The baseline is frozen at E0 in the flown implementation; R2 v2 "
               "(re-reference at E2 or drogue-drag compensation, threshold for the window) is flown in rev3 P4 and the lead "
               "then sets pcf_tmax")
    rc["tag"] = "DESIGN (LEAD CHANGELOG lines 168 (1), 181 (4)); R2 v2 OPEN"
    rc["status_rev2p1"] = ("the time-only term of line 168 (1) is REPLACED in design by R2 (lead 175 (5), adopted 181 (4)); "
                           "pcf_tmax 0.8 s NOT adopted; old texts in v_superseded_rev2p1 and v_superseded_rev2")
    # ---------------------------------------------------------------- V recommendation + reviewer probes
    V = d["rev2"]["amendment_V_pc_invalid"]
    V["recommendation"] = inline(V["recommendation"], "PROPOSAL pcf_tmax 0.8 s (not flown)",
                                 "NOT ADOPTED, lead 181 (4): pcf_tmax stays 0.5 s; REVIEWER probe at 0.8 s: flame-out max "
                                 "35.20 N, margin 1.96 N")
    V["status_rev2p1"] = ("R2 ADOPTED in design over R1 (lead 181 (4)); pcf_tmax 0.5 s (the flown value; L400 releases 440-470 "
                          "ms, 0 aborts); 0.8 s NOT adopted; R2 v2 OPEN (rev3 P4); Combustion bounds the cold-flow apparent "
                          "thrust under the drogue after a flame-out (TO-VERIFY)")
    V["reviewer_probes"] = OrderedDict(
        tag="REVIEWER SIM (REV-GNC-3; cited, not re-flown by GNC)",
        sources=rv_ref("v_probe_flights", "v_probe_flights_2", "v_probe_paired", "v_flameout_mechanism"),
        flameout_estimate_max_N=OrderedDict(
            t05_A1_none=29.92, t05_A1J_pc=32.98, t08_A1_none=35.20, threshold=37.16,
            note=("the rev2 '33.0 N' is the A1J_pc value at pcf_tmax 0.5 s; at 0.8 s the A1_none maximum is 35.20 N (run 218, "
                  "W10 7.30 m/s, gust scale 1.39): margin 1.96 N; the increase acts through gusts on the E0-frozen baseline "
                  "(44 of 500 runs increase; corr with wind 0.21)")),
        inside_W10_lt6_N=OrderedDict(t05_max=18.75, t08_max=20.06, n=364),
        plateau_release_ms=OrderedDict(L400_k875_t05="440-470", L400_k875_t08="440-470 (identical table to t05)",
                                       L400_t08="440-470"),
        paired=("rvR2L400k_t05 vs pw|G73 -1/+2 (p 1); vs pcfR2k875 -2/+1; rvR2L400_t08 identical to pcfR2L400 (0 columns "
                "differ); rvR2fo_t08 P 0 (hold, 500 aborts)"))
    # ---------------------------------------------------------------- K
    K = d["rev2"]["amendment_K"]
    K["finding"] = inline(K["finding"], "with Pc invalid the freeze", "REFUTED and withdrawn, lead 175 (4)")
    K["status_rev2p1"] = ("freeze REFUTED and WITHDRAWN (lead 175 (4)); replacement (re-reference k_hat and the apex predictor "
                          "to throttle-map thrust with Pc invalid; freeze only for short dropouts, length TO-DEFINE) is OPEN: "
                          "flown on FSW-R2 with a throttle-map error band before SIL/HIL freeze (181 (7), rev3 P7). RV3-10: "
                          "the K evidence above was flown on the mass-estimator Pc-lost configuration, not on FSW-R2; the "
                          "refutation stands")
    api = d["rev2"].get("api_v29", {})
    if "K" in api and "kfz_on" in api["K"]:
        api["K"]["kfz_on"]["tag"] = api["K"]["kfz_on"]["tag"] + " [REFUTED and withdrawn, lead 175 (4); do not fly]"
    # ---------------------------------------------------------------- trim + mass
    T = d["rev2"]["apogee_trim"]
    T["decision"] = inline(T["decision"], "a trim below 275 m or another fix (propellant load, landing reserve) is a LEAD "
                                          "decision if the mass materialises",
                           "SUPERSEDED rev2.1: lead 175 (2) set a 0.30 kg valve-pair trigger, itself REPLACED by 181 (5): "
                           "re-fly at the actual ledger for any confirmed growth >= 0.10 kg over ledger v3d")
    T["status_rev2p1"] = ("285 m ADOPTED (175 (1)) with conditions (181 (6)): W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s HARD for "
                          "A1; coverage on four bases and pl, e19, prep path, L400, PURGE NOT RUN in rev3 P3; +0.1/+0.2/+0.3 "
                          "kg at 285 m and the v3.5 ledger in rev3 P2. " + mass_txt)
    T["m60_comparators_rev2p1"] = ("RV3-09: the rev2 m60 pairs (liq|G73|m60 vs liq|none|m60 -11/+5, p 0.21) measure the PURGE "
                                   "effect at +0.60 kg, not the mass effect. Mass effect (same arm, nominal mass, C-SAME): "
                                   "liq|none|m60 vs liq|none -11/+9 (p 0.82); liq|G73|m60 vs liq|G73 -15/+12 (p 0.70); "
                                   "pw|G73|m60 vs pw|G73 -17/+13 (p 0.59); none loses by the rule, but exhaustions grow "
                                   "(6/7 at 300 m) and the reserve tail shifts (comparators_rev2p1)")
    # ---------------------------------------------------------------- RG-16 detector output (reviewer)
    rg = d["rev2"]["rg16_v2"]
    rg["status_superseded_rev2p1"] = rg["status"]
    rg["status"] = ("FC_THRUST NOT armed on A1 (lead 168 (5), 181 (3)); per-flight form as support WITHDRAWN (181 (3)); "
                    "PROVISIONAL detection-latency allowance 0.5 s from the onset of the 670 N plateau, strict windowed form, "
                    "no window-gain credit")
    rg["detector_output_reviewer"] = OrderedDict(
        tag="REVIEWER SIM (REV-GNC-3 rv_rg16_budget / rv_rg16_held; cited, not recomputed by GNC)",
        sources=rv_ref("rg16_detector_output_budget", "rg16_detector_output_budget_json", "rg16_held_H_cal_comp",
                       "rg16_held_H_cal"),
        allowed_pct=2.985, form="total = 3 x RSS(random) + sum of bias bounds",
        H_cal_comp_path=OrderedDict(bias_pct=1.281, s_mass_pct=0.143, frame_noise_sd_pct=0.986, rho1=0.616,
                                    D0_single_frame_total_pct=4.453, D1_instantaneous_held_total_pct=4.197,
                                    D1_with_hold_shift_pct=4.760, D2_window_ms_total_pct={"50": 3.876, "100": 3.497,
                                                                                         "200": 3.225, "300": 3.086,
                                                                                         "500": 2.973, "1000": 2.780},
                                    per_flight_total_pct=2.319, verdict="instantaneous FAIL; strict windowed passes from "
                                                                        "W = 0.5 s (2.973 %, margin 0.012 %)"),
        H_cal_path=OrderedDict(bias_pct=1.383, D1_instantaneous_held_total_pct=5.069, D2_500ms_total_pct=4.015,
                               D2_1000ms_total_pct=3.508, verdict="fails every strict form"),
        noise_model="frame noise ASSUMED white at 2.0 m/s2 sd at F_max (run6); a measured vibration spectrum may remove "
                    "the 0.012 % margin (rev3 P5 sensitivity to non-white spectra, ASSUMED spectra)",
        lead_decision=ld(181) + " (3)")
    # ---------------------------------------------------------------- (e) launch commit + FSW entries
    req = d["requirements"]
    req["launch_commit_rev2p1"] = OrderedDict(
        v=[OrderedDict(item="Pc VALID on the pad (ECU Pc channel valid at ARM and at launch commit)", missions="A1, B1",
                       tag="DESIGN (LEAD 175 (4))",
                       why="the k_hat / apex freeze is withdrawn and FC_THRUST is not armed: an in-flight Pc loss has no "
                           "over-thrust detector (A1 FMEA, 181 (3)); the pad check covers only the pad"),
           OrderedDict(item="W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s (10 min before ARM; anemometer at 3 m)",
                       missions="A1: HARD (181 (6)); B1: provisional (161)", tag="DESIGN (LEAD 181 (6))",
                       why="at 285 m the trim trades exhaustion for wind-driven landing failures at W10 6.96-7.84 m/s "
                           "(REVIEWER " + rv_ref("trim_wind") + "); the equivalence of the 10-min sigma and the Dryden "
                           "intensity is a model-form ASSUMPTION"),
           OrderedDict(item="bleed closure confirmed from P_mid (pad go/no-go on every flight with the bleed fitted)",
                       missions="every flight with the bleed", tag="DESIGN (LEAD 168 (3))", why="BLEED_FAULT stuck from E0: "
                       "P 0.92, 32 exhausted per base (175 (7)); FC action LOG-ONLY (168 (2))")],
        tag="DESIGN (LEAD)")
    fs = d["flight_software"]
    fs["rev2p1_entries"] = OrderedDict(
        drogue_release_pc_invalid=OrderedDict(v="R2 accelerometer confirmation (relight_conditions.v); pcf_tmax 0.5 s; R2 v2 "
                                                "OPEN (rev3 P4)", tag="DESIGN (LEAD 181 (4))"),
        k_hat_pc_invalid=OrderedDict(v="k_hat / apex freeze WITHDRAWN (175 (4)); replacement OPEN (181 (7)); not in FSW-R2",
                                     tag="DESIGN OPEN"),
        purge_commit_rule=OrderedDict(v="PURGE commits iff lead to the plain relight trigger >= L* (interim 1.7 s; 1.3 s if "
                                        "HI); else no purge, relight unpurged", tag="DESIGN (LEAD 181 (2)) PROVISIONAL",
                                      scope="contingency only; the decided predictor commits >= 2.66 s ahead"),
        fc_thrust=OrderedDict(v="NOT armed on A1; arming needs the RG-16 detector-output budget with the 0.5 s latency "
                                "allowance and its trajectory consequence", tag="DESIGN (LEAD 181 (3))"),
        mass_change_control=OrderedDict(v="re-fly at the actual ledger for any confirmed landing-mass growth >= 0.10 kg over "
                                          "ledger v3d (all engine-module and vehicle changes summed)",
                                        tag="DESIGN (LEAD 181 (5))", status=mass_txt))
    # ---------------------------------------------------------------- launch commit evidence status
    d["launch_commit_wind_evidence"]["status_rev2p1"] = "A1: HARD rule (lead 181 (6)); B1: provisional (161)"
    d["rev1_items"]["v"]["launch_commit_proposal"]["status_rev2p1"] = ("ADOPTED for A1 as a HARD rule (lead 181 (6)); site data "
                                                                       "TO-DEFINE")
    # ---------------------------------------------------------------- (f) lead decisions folded
    d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"] = OrderedDict(
        source=f"interfaces/CHANGELOG.md lines {', '.join(str(n) for n in LEAD_LINES)} (lead decisions, verbatim); reference "
               f"lines {', '.join(str(n) for n in REF_LINES)}; sha256/16 of the quoted lines {lines_sha}",
        verbatim=OrderedDict((str(n), cl[n]) for n in LEAD_LINES),
        folded=OrderedDict([
            ("175 (1)", "flight_profile.recommended_baseline.note_rev2p1; rev2.apogee_trim.status_rev2p1"),
            ("175 (2)", "SUPERSEDED by 181 (5) (rev2.apogee_trim.decision inline marker)"),
            ("175 (3)", "SUPERSEDED in its basis by 181 (2) (rev2.amendment_G_late_commit.finding)"),
            ("175 (4)", "rev2.amendment_K.status_rev2p1; requirements.launch_commit_rev2p1 (Pc VALID)"),
            ("175 (5)", "SUPERSEDED by 181 (4) (relight_conditions, amendment_V.status_rev2p1)"),
            ("175 (6)", "per-flight support WITHDRAWN by 181 (3) (rg16_v2.status, over_thrust_fc_thrust.rev2p1_status)"),
            ("175 (7)", "FMEA inputs: fmea_inputs_rev2p1"),
            ("177 (1), (4)", "mass: mass_change_control (TC-09 IN718 +0.0137 kg in CAD v3.5; bearings OPEN)"),
            ("181 (1)-(11)", "this rebuild (1); G (2); RG-16 (3); R2 (4); mass (5); 285 m (6); K (7); configuration (8): "
                             "rev2.bitcheck_v29.record_rev2p1 (RV3-08) and rev3 P9; grain gate (9) unchanged; interface "
                             "note (10): interface_notes_rev2p1; next session (11)"),
            ("182 (7)", "GNC mass delta from massprops_v3.5.json and mechanical.json v2.1: " + mass_txt),
            ("182 (9)", "process rule: kill processes by PID only (followed)"),
            ("183", "FEA design changes (TC-02 head, GM-01/02 geometry, NZ-01 capture) may change mass: v3.5.1 re-fly")]),
        tag="LEAD decisions (verbatim) and where rev2.1 folds them")
    # ---------------------------------------------------------------- RV3-08 bit-check record
    bc = d["rev2"]["bitcheck_v29"]
    bc["record_rev2p1"] = OrderedDict(
        g6_redesign_declared=("G6 (gate-off positive control) was redesigned between run 1 (tool v1.0, arms oldP_PS10, "
                              "G_gate0_CA, G_decided; G6 passed without reproducing P30) and run 2 (tool v1.1, arm oldP_P30 "
                              "added: 6 starts above 200 m reproduced; G_gate0_CA_h3.5: 6 spurious). Run 1 recorded no code "
                              "hashes; the simulator was unchanged between the runs (REVIEWER: 0 leaf differences on the "
                              "final code, " + rv_ref("bitcheck_reviewer") + ")."),
        tool_v12=OrderedDict(file=f"{STAGE}/scripts/m2_bitcheck_v29.py", sha256_16=sha(BIT_TOOL),
                             change="P30_reproduced and the gate-off reproduction are part of the G6 pass (g6_pass: passed = "
                                    "decided_clean AND P30_reproduced AND gate_off_CA_reproduces_flagged); code, data-table "
                                    "and pin-list hashes recorded at the start and the end of every run; a run fails if any "
                                    "hash changes during it; inputs opened are hashed (audit hook)"),
        recheck=OrderedDict(file=f"{STAGE}/results/bitcheck/bit29_g6_recheck.json", sha256_16=sha(G6R),
                            result=("v1.2 criterion applied to the stored G6 blocks without flying: run 1 FAILS (no P30 arm, "
                                    "no positive control); run 2 PASSES"),
                            test_passed=bool(g6.get("test_passed"))),
        note="a full v1.2 bit-check run on the rev3 code is a rev3 item (P9); rev2.1 adds no flight")
    # ---------------------------------------------------------------- RV3-09 named comparators
    d["rev2"]["comparators_rev2p1"] = OrderedDict(
        source=f"{STAGE}/results/comparators/comparators_rev2p1.json (sha256/16 {sha(COMP)}; m2_rev2p1_comparators v1.0)",
        method=cj["method"], tables_verified_against_manifest_rev2=cj["all_tables_manifest_verified"],
        classes=OrderedDict([("C-LIQ", "liq|none on the same base and plateau: the liquid plan without purge (total cost)"),
                             ("C-LS", "liq with the same purge and plateau: the line-state effect alone"),
                             ("C-SAME", "the same state and purge without the one factor named (mass, plateau, offset, "
                                        "trim, prep path)"),
                             ("C-DEC", "the decided arm of the same state (late commit, Pc-invalid rules)")]),
        rows=comparators_table(cj),
        statements=["liq|G73 vs liq|none: main2 -9/+4 (p 0.27); all4 -21/+7 (p 0.0125) LOSES: the purge mass costs P on "
                    "the liquid line when the four bases are pooled",
                    "pw|G73|L400o vs pw|G73 (nominal decided arm): -17/+5 (p 0.017) LOSES (RV3-09); vs liq|G73|L400o "
                    "(the only rev2 comparator) -17/+9 (p 0.17); offset alone vs pw|G73|L400 -11/+6 (p 0.33)",
                    "m60: the rev2 pairs measure the purge effect at +0.60 kg; the mass effect is -11/+9, -15/+12, -17/+13 "
                    "(none loses)",
                    "liqP|G73 vs liq|none on A1_none -6/+0 (p 0.031) LOSES per base; pooled main2 -12/+4 (p 0.077)",
                    "e19|G73|L400 vs liq|none|L400 -39/+3 (p 5.6e-9) LOSES; vs e19|G73 -43/+2"])
    # ---------------------------------------------------------------- FMEA + interface notes + pending inputs
    d["fmea_inputs_rev2p1"] = OrderedDict(
        v=["A1: no over-thrust detector after an in-flight Pc loss (the 30 bar abort needs Pc valid; FC_THRUST not armed; "
           "the K freeze withdrawn) (lead 181 (3), RV3-12)",
           "BLEED_FAULT stuck from E0: P 0.92, 32 exhausted per base (lead 175 (7))",
           "both case TCs lost or ECU reset -> relight refused, drogue touchdown ~22 m/s = vehicle loss (175 (7))",
           "PURGE NOT RUN HI: P_total 0 (175 (7))",
           "undetected flame-out at E2 with Pc invalid: R2 holds the drogue (touchdown p50 -21.8 m/s, vehicle loss); R1 "
           "released a dead vehicle in 1000/1000 (rev2 amendment V)"],
        tag="SIM inputs for the lead's FMEA (not an FMEA)")
    d["interface_notes_rev2p1"] = OrderedDict(
        purge_mass=("the <= 73.0 g / <= 76 g purge figure is vented, vehicle-level N2O; tank liquid depletion on the nominal "
                    "flight is 81.6 g (8.6 g boils into the ullage in the tank model); the reserves already include it; "
                    "tank-outlet coverage checks use liquid depletion (lead 181 (10), RV3-12)"),
        tag="DESIGN note (Combustion / Mechanical)")
    d["pending_inputs_rev2p1"] = OrderedDict(
        combustion_unpurged_start=OrderedDict(
            v=("Combustion v2.4a H20 / OI-31: PURGE NOT RUN LO worst -> every light (P 0.758) followed by a 23.4 cm3 vapour "
               "gap; released-then-A3 0.712 (ramp) / 0.717 (flow held); proposal 'no commit by the deadline -> no relight on "
               "that pass'; NOT decided by the lead; affects L* (lead 175 (3) refutation clause)"),
            source=f"02-combustion/data/v2p4a/unpurged_start_check_v2p4a.json ({sha(H20)})", tag="Combustion SIM (pending)"),
        lo_hi_settlement="Combustion settles LO / HI of an unpurged start (lead 181 (2)): L* 1.7 or 1.3 s",
        cold_flow_bound="Combustion bounds the cold-flow apparent thrust under the drogue after a flame-out (181 (4)); "
                        "rev3 P4 carries 0 / 5 / 10 N parametric until then",
        mass=OrderedDict(v=mass_txt, source=f"out/rev3/mass_v35/mass_v35_vs_v3d.json ({sha(MASS)}); staged in "
                                            f"{STAGE}/results/mass_v35/", tag="DERIVED"),
        vibration_spectrum="measured IMU vibration spectrum at F_max (DC-C / DC-D, founders); RG-16 margin 0.012 %")
    # ---------------------------------------------------------------- changes + inputs
    d["changes_rev2p1"] = [
        "status replaced (old: status_superseded_rev2p1); staging block replaced",
        "over_thrust_fc_thrust: proposal.threshold and mass_estimate_requirement replaced (old under v_superseded_rev2p1); "
        "claim, finding, refutation[4] marked SUPERSEDED; unknowns[5], [10] annotated; rev2p1_status added",
        "open_items[22], [29] marked SUPERSEDED; five rev2.1 open items appended",
        "answers_to_requests.lead_fc_thrust_closure_item_1_2026-10-13 marked SUPERSEDED; lead_decisions_2026-10-13.v "
        "over_thrust_abort / fc_thrust_closure_item_1 status siblings",
        "flight_profile.recommended_baseline.note: inline marker on the 300 m apogee; note_rev2p1 added",
        "rev2.amendment_G_late_commit.finding corrected (old: finding_superseded_rev2p1) with the reviewer's paired tables",
        "requirements.ignition.relight_conditions: R2 replaces the time-only term (old: v_superseded_rev2p1); status_rev2p1",
        "rev2.amendment_V_pc_invalid: inline NOT ADOPTED marker on pcf_tmax 0.8 s; status_rev2p1; reviewer_probes",
        "rev2.amendment_K.status_rev2p1; api_v29.K.kfz_on tag marked REFUTED",
        "rev2.apogee_trim: inline marker on the mass sentence; status_rev2p1; m60_comparators_rev2p1",
        "rev2.rg16_v2: status replaced (old: status_superseded_rev2p1); detector_output_reviewer",
        "requirements.launch_commit_rev2p1 (Pc VALID, wind HARD for A1, bleed closure); flight_software.rev2p1_entries",
        "launch_commit_wind_evidence.status_rev2p1; rev1_items.v.launch_commit_proposal.status_rev2p1",
        "lead_decisions_2026-10-13.rev2p1_lines_175_183 (verbatim lines 175, 177, 181, 182, 183)",
        "rev2.bitcheck_v29.record_rev2p1 (RV3-08); rev2.comparators_rev2p1 (RV3-09)",
        "fmea_inputs_rev2p1, interface_notes_rev2p1, pending_inputs_rev2p1",
        "inputs_read.rev2p1; scripts_rev2p1; rev2p1_document_self_check"]
    d["inputs_read"]["rev2p1"] = OrderedDict(
        staged_rev2_json=OrderedDict(path=f"01-systems-gnc/staging_v3.1/rev2/results/gnc_json/gnc_v3.1_staging_rev2.json",
                                     sha256_16=R2JSON_SHA16),
        rev2_manifest=OrderedDict(path="01-systems-gnc/staging_v3.1/rev2/MANIFEST_rev2.sha256",
                                  sha256_16=sha(f"{R2}/MANIFEST_rev2.sha256")),
        review=OrderedDict(path="reviews/REVIEW-GNC-R2.md", sha256_16=sha(REVW)),
        reviewer_files=rvh,
        changelog_lines=OrderedDict(lines=list(LEAD_LINES + REF_LINES), sha256_16_of_lines=lines_sha),
        comparators=OrderedDict(path=f"{STAGE}/results/comparators/comparators_rev2p1.json", sha256_16=sha(COMP)),
        g6_recheck=OrderedDict(path=f"{STAGE}/results/bitcheck/bit29_g6_recheck.json", sha256_16=sha(G6R)),
        mass_v35=OrderedDict(path=f"{STAGE}/results/mass_v35/mass_v35_vs_v3d.json", sha256_16=sha(MASS)),
        combustion_h20=OrderedDict(path="02-combustion/data/v2p4a/unpurged_start_check_v2p4a.json", sha256_16=sha(H20)))
    d["scripts_rev2p1"] = [f"{STAGE}/scripts/{n}" for n in (
        "m2_gnc_json_v31_rev2p1.py", "m2_rev2p1_comparators.py", "m2_bit29_g6_recheck.py", "m2_bitcheck_v29.py",
        "m2_mass_v35.py")]
    d["checkpoint_rev2p1"] = OrderedDict(
        delivered_reviewed_date="GNC (Senior Space/GNC, successor session) / independent document check to be assigned by "
                                "the lead (181 (1)) / 2026-10-13; status Por revisar",
        configuration=("publication only, no new flight; sim6/run6 v2.9-dev and FSW-R2 unchanged (sim6 f90e0ba8e993ad60, run6 "
                       "b054a222eff38b6e, pins_rev2 4c97768d53b57eef); staged rev2 MANIFEST cb5d2c48e8d8fa27 verified 280/280, "
                       "reviewer MANIFEST d3bca19f1fdb1ca2 61/61; builder " + VERSION + " (deterministic)"),
        claim=["every stale statement of REV-GNC-3 4.8 (a)-(f) is replaced (old text under *_superseded_rev2p1) or marked "
               "inline; author's scan: rev2p1_document_self_check",
               "lead decisions 175, 177, 181, 182, 183 folded verbatim with a fold map",
               "G basis corrected with the reviewer's paired-loss table; L* rule (181 (2)) and its scope stated",
               "R2 replaces the time-only release term (pcf_tmax 0.5 s); Pc VALID, wind HARD (A1) and bleed closure are "
               "launch-commit entries; K replacement OPEN",
               "RV3-08: G6 redesign declared; tool v1.2 makes P30_reproduced part of the G6 pass (run 1 FAIL / run 2 PASS "
               "under v1.2, no flight)",
               "RV3-09: 69 named comparisons recomputed from the manifest-verified rev2 tables reproduce the reviewer",
               "RG-16 detector-output results and V probes cited from reviewer files (not GNC results)"],
        tests=["builder run twice: identical bytes", "self-check 0 unmarked stale hits", "comparators: 69 rows, tables "
               "verified against MANIFEST_rev2, pairing checked", "G6 recheck test_passed", "mass closure (R.build ledger "
               "reproduces the mapped delta to 2e-4 kg and the first moment to 2e-3 kg m)",
               "NOT run: a full v1.2 bit-check (rev3 P9); any flight (by design)"],
        unknowns=["late-commit contingency probability; LO/HI and the unpurged-start hazard (Combustion; H20/OI-31 pending)",
                  "RG-16 margin 0.012 % on an ASSUMED white vibration model; consequence of 0.5 s at 670 N; B1 miss side",
                  "R2 v2 unflown; cold-flow apparent thrust unbounded", "K replacement unflown; no throttle-map error band",
                  "massprops_v3.5.1 pending; bleed valves ASSUMED; EL-11/12 overlap TO-VERIFY; fasteners not modelled",
                  "no hardware data; nothing here is physical approval"],
        next_closure=["independent document check of rev2.1; then the lead publishes v3.1 (GNC does not write "
                      "interfaces/gnc.json)", "GNC rev3 (line 181 items 2-8) in staging_v3.1/rev3/"],
        note="the harness refused a separate REPORT .md from this GNC session; the checkpoint is carried here and in the "
             "session handback")
    d["rev2p1_document_self_check"] = self_check(d)
    os.makedirs(OUTD, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    sc = d["rev2p1_document_self_check"]
    print(f"wrote {OUT} {sha(OUT)} keys {len(d)}; self-check hits {sc['hits']} unmarked {sc['unmarked']}")
    for h in sc["unmarked_list"]:
        print("UNMARKED", h["pattern"], h["path"], "|", h["context"][:200])
    if sc["unmarked"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
