"""m2_gnc_json_v31_rev2p2 v1.2 (GNC, 2026-10-13): staging rev2.2 = the gnc.json v3.1 publication candidate. Copy of staging
rev2.1 (gnc_v3.1_staging_rev2p1.json c2860bd89c1e5920) with the corrections C1-C5 of the independent document check REV-GNC-4
(reviews/REVIEW-GNC-R2P1.md b54970c4d39e192c; lead CHANGELOG line 190) applied. Text and folds only: every replaced value keeps
its old text under a sibling key ending in '_superseded_rev2p2' (or a list item is prefixed 'SUPERSEDED (rev2.2; ...)' and the
current text appended); no GNC-computed number is added (numbers quoted here come from the lead lines, Combustion's v2.4a
files, the reviewer's files or values already in rev2.1, each with its source).
Corrections: C1 (RV4-01) lead line 186 (1)-(6) folded (L* = 1.3 s for both brackets, no purge and no unpurged relight below
it, P_total ~0.75 premise REFUTED, R2 command hold at the 62.5 N start level, Combustion's DERIVED cold-flow bound, FMEA, W10
'why', rev3 plan, fold map); C2 (RV4-02) ledger-v3d validity in status, flight_profile, propellant_closure_v3 and
rev2.apogee_trim; C3 (RV4-03) stale 300 m targets, duty-cycle record, pre-R2 predicate, unscoped plan sentence, pivot station,
build basis; C4 (RV4-04) four citations; C5 (RV4-05) rev3 P-labels defined (rev3_plan), change-list pointers, publication
wording. RV4-06 (recommended): bay-wall / gimbal-stop open item (RM1-01, 188 (1)), the 175 (5) fold wording, the remaining
notes as open items. Lead line 188 items that address GNC are folded as open items (no flight in this build).
Output: out/rev3/rev2p2/gnc_v3.1_rev2p2.json (deterministic) and gnc_v3.1_rev2p2_keydiff.json (paths changed against rev2.1).
v1.1 (first run of v1.0 left 2 unmarked self-check hits, both scanner scope, no document text changed): S20 narrowed to
the claim form (a W10 / m/s figure cited to s04_wind.out, as t10 C18; the inputs_read.rev2p1 file list records what rev2.1
read and is not a citation); marker list extended with 'withdrawn' / 'Withdrawn' (as the t10 MARK set: 'the k_hat / apex
freeze is withdrawn' is the current, correct statement).
v1.2 (t10 --publication on the v1.1 output: C04 flagged rev2p2_document_self_check/hit_paths, because a recorded path
under rev2p1_document_self_check/patterns/ quotes a rev2.1 pattern name): the hit-path list leaves out the rev2.1 scan
record and counts its hits instead (that key is exempt by rule in both scans); no document text changed."""
import copy
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

VERSION = "m2_gnc_json_v31_rev2p2 v1.2"
SP = "/home/claude/work/space"
HUB = "/home/claude/work/shared-fallback/engine"
R21 = f"{HUB}/01-systems-gnc/staging_v3.1/rev2p1"
R21JSON = f"{R21}/results/gnc_json/gnc_v3.1_staging_rev2p1.json"
R21JSON_SHA16 = "c2860bd89c1e5920"
OUTD = f"{SP}/out/rev3/rev2p2"
OUT = f"{OUTD}/gnc_v3.1_rev2p2.json"
KEYDIFF = f"{OUTD}/gnc_v3.1_rev2p2_keydiff.json"
CHLOG = f"{HUB}/interfaces/CHANGELOG.md"
STAGE = "01-systems-gnc/staging_v3.1/rev2p2"
LEAD_LINES = (186, 188, 190)
REF_LINES = (184, 185, 187, 189)
SRC = OrderedDict([  # cited files: path relative to the hub (or absolute), pinned sha256/16
    ("rev2p1_json", ("01-systems-gnc/staging_v3.1/rev2p1/results/gnc_json/gnc_v3.1_staging_rev2p1.json", "c2860bd89c1e5920")),
    ("rev2p1_manifest", ("01-systems-gnc/staging_v3.1/rev2p1/MANIFEST_rev2p1.sha256", "02c554a2f0fe68fa")),
    ("review_rev_gnc_4", ("reviews/REVIEW-GNC-R2P1.md", "b54970c4d39e192c")),
    ("review_rev_gnc_4_manifest", ("reviews/gnc/rev2p1/MANIFEST_REV-GNC-4.sha256", "e3d4413e5ed10b94")),
    ("postcheck_tool", ("reviews/gnc/rev2p1/scripts/t10_postcheck.py", "d51d079d81d64766")),
    ("review_rev_gnc_3", ("reviews/REVIEW-GNC-R2.md", "fabfc81fa1d70327")),
    ("s03_trim", ("reviews/gnc/rev2/logs/s03_trim.out", "819a79cf0db42fda")),
    ("s15_g_decided", ("reviews/gnc/rev2/logs/s15_g_decided.out", "be3a6105746f9bce")),
    ("rv_rg16_budget", ("reviews/gnc/rev2/results/rg16held/rv_rg16_budget.json", "65939777a57180ec")),
    ("vehicle_v3d", ("01-systems-gnc/vehicle/vehicle_v3d.json", "b26938b809bc4910")),
    ("mechanical_v2_iface_v3d", (f"{SP}/iface_v3d/mechanical.json", "4f024ed4ccb4618c")),
    ("cold_flow_csv", ("02-combustion/data/v2p4a/cold_flow_thrust_v2p4a.csv", "e094c4be80d12f66")),
    ("cold_flow_json", ("02-combustion/data/v2p4a/cold_flow_thrust_v2p4a.json", "a226dfacf494cb2c")),
    ("unpurged_outcomes", ("02-combustion/data/v2p4a/unpurged_outcomes_v2p4a.json", "18a639d61b58ce8a")),
    ("review_rev_mech_1", ("reviews/REVIEW-MECHANICAL-R1.md", "dc1c1c6b8931c95d")),
])
# author's own scan (pattern texts stay in this script; the JSON records pattern ids only, so the record itself carries no
# stale phrase): the rev2.1 patterns of REV-GNC-3 4.8 plus the REV-GNC-4 items
STALE = OrderedDict([
    ("S01", r"650 N[^.;]{0,60}(CONFIRMED|confirmed)|(CONFIRMED|confirmed)[^.;]{0,30}650 N"),
    ("S02", r"(<=|≤) ?1 ?% \(1 sigma\)"),
    ("S03", r"300 m baseline|A1 300 m|apogee \(300 m\)|A1 at 300 m"),
    ("S04", r"costs no measurable P|delay <= 0\.6 s costs"),
    ("S05", r"error budget: OPEN"),
    ("S06", r"pcf_tmax 0\.8"),
    ("S07", r"0xFFFF AND t >= t_E2"),
    ("S08", r"per-flight form[^.;]{0,60}provisional support"),
    ("S09", r"\bfreeze[^.;]{0,40}(k_hat|apex)|(k_hat|apex)[^.;]{0,40}\bfreeze"),
    ("S10", r"0\.30 kg[^.;]{0,40}trigger|trigger[^.;]{0,40}0\.30 kg"),
    ("S11", r"(?i)interim[^.;]{0,20}1\.7 ?s|L\* ?= ?1\.7"),
    ("S12", r"(?i)(?<!no )(?<!alternative: )(relight (proceeds )?unpurged|proceeds unpurged|unpurged relight)"
            r"(?![^.;]{0,80}(E2 ?\+ ?0\.22|held to))"),
    ("S13", r"(?i)P_total ~?0\.75"),
    ("S14", r"RELEASE iff b4 AND \[\(d2-d3 != 0xFFFF"),
    ("S15", r"(?i)0\.81 s plan holds(?![^.;]{0,80}predictor path)"),
    ("S16", r"pivot at 0\.2223 m"),
    ("S17", r"(?i)cold-flow apparent thrust unbounded|0 / 5 / 10 N parametric"),
    ("S18", r"(?i)(H20|OI-31|no relight on that pass)[^\n]{0,200}?(not decided by the lead|pending a lead decision)"),
    ("S19", r"(?i)plain trigger fired \(2000 runs"),
    ("S20", r"(?i)(W10|m/s)[^\n]{0,80}s04_wind\.out"),
    ("S21", r"(?i)margin 0\.012 ?%"),
    ("S22", r"NOT PUBLISHED|Por revisar|nothing yet \(staging\)"),
])
MARKERS = ("SUPERSEDED", "WITHDRAWN", "NOT ADOPTED", "NOT adopted", "REFUTED", "REPLACED", "HISTORY", "superseded", "refuted",
           "replaced", "no longer", "ANSWERED", "withdrawn", "Withdrawn")


def sha(p, n=16):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]


def shas(s, n=16):
    return hashlib.sha256(s.encode()).hexdigest()[:n]


def jload(p):
    return json.load(open(p), object_pairs_hook=OrderedDict)


def hubp(p):
    return p if p.startswith("/") else f"{HUB}/{p}"


def changelog_lines():
    L = open(CHLOG, encoding="utf-8").read().split("\n")
    out = OrderedDict((n, L[n - 1]) for n in sorted(LEAD_LINES + REF_LINES))
    for n in LEAD_LINES:
        if " | lead | (decision) | " not in out[n]:
            raise RuntimeError(f"CHANGELOG line {n} is not a lead decision: {out[n][:80]}")
    for n, key in ((186, "OI-38 R2 command hold ADOPTED"), (188, "RM1-01: BL-02 is fixed on the engine side"),
                   (190, "GNC applies C1-C5 as staging rev2.2"), (189, "REV-GNC-4 independent document check")):
        if key not in out[n]:
            raise RuntimeError(f"CHANGELOG line {n} does not carry '{key}'")
    return out


def sup(s, why):
    return f"SUPERSEDED (rev2.2; {why}): {s}"


def inline(s, phrase, note):
    if s.count(phrase) != 1:
        raise RuntimeError(f"phrase must occur once for an inline marker: {phrase}")
    return s.replace(phrase, f"{phrase} [{note}]", 1)


def replace_kept(dct, key, new, suffix="_superseded_rev2p2"):
    if key + suffix in dct:
        raise RuntimeError(f"{key}{suffix} exists already")
    dct[key + suffix] = copy.deepcopy(dct[key])
    dct[key] = new


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
            pl = "/".join(path).lower()
            for pid, pat in STALE.items():
                for m in re.finditer(pat, x):
                    win = x[max(0, m.start() - 120): m.end() + 120]
                    ok = ("superseded" in pl or "history" in pl or "/verbatim/" in pl or pl.startswith("rev2p1_document_self_check")
                          or x.startswith(("SUPERSEDED", "HISTORY")) or any(mk in win for mk in MARKERS))
                    hits.append(dict(pattern=pid, path="/".join(path), marked=bool(ok)))
    walk(d, [])
    un = [h for h in hits if not h["marked"]]
    return OrderedDict(rule=("author's scan: every string matching a pattern of the builder's list (ids S01-S22: the REV-GNC-3 "
                             "4.8 items and the REV-GNC-4 items C09-C19, N01-type wording, publication wording) must sit under "
                             "a key containing 'superseded' / 'history' / 'verbatim', start with SUPERSEDED / HISTORY, or carry "
                             "a marker word within 120 characters; the pattern texts are in the builder script, not here"),
                       builder=VERSION, patterns=list(STALE), hits=len(hits), unmarked=len(un),
                       unmarked_list=[dict(pattern=h["pattern"], path=h["path"]) for h in un],
                       hits_in_rev2p1_scan_record=sum(1 for h in hits if h["path"].startswith("rev2p1_document_self_check")),
                       hit_paths=sorted({h["path"] for h in hits if not h["path"].startswith("rev2p1_document_self_check")}))


def keydiff(a, b, path="", out=None, depth=0):
    """paths (to depth 6) whose value differs between rev2.1 (a) and rev2.2 (b)."""
    if out is None:
        out = OrderedDict(changed=[], added=[], removed=[])
    if isinstance(a, dict) and isinstance(b, dict) and depth < 6:
        for k in a:
            if k not in b:
                out["removed"].append(f"{path}/{k}")
            elif a[k] != b[k]:
                keydiff(a[k], b[k], f"{path}/{k}", out, depth + 1)
        for k in b:
            if k not in a:
                out["added"].append(f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list) and depth < 6:
        for i in range(max(len(a), len(b))):
            if i >= len(a):
                out["added"].append(f"{path}/{i}")
            elif i >= len(b):
                out["removed"].append(f"{path}/{i}")
            elif a[i] != b[i]:
                keydiff(a[i], b[i], f"{path}/{i}", out, depth + 1)
    else:
        out["changed"].append(path)
    return out


def main():
    for k, (p, h) in SRC.items():
        if sha(hubp(p)) != h:
            raise RuntimeError(f"{k}: {p} sha256/16 {sha(hubp(p))} != pinned {h}")
    d0 = jload(R21JSON)
    d = copy.deepcopy(d0)
    cl = changelog_lines()
    lines_sha = shas("\n".join(cl[n] for n in sorted(cl)))
    src = lambda k: f"{SRC[k][0]} ({SRC[k][1]})"  # noqa: E731
    VALID = ("VALIDITY (REV-GNC-4 C2, lead line 190): every P, reserve, propellant-closure and apogee-trim figure in this "
             "document was computed at GNC mass ledger v3d (18 items, total 13.6706 kg); CAD v3.5 is +0.87 to +1.17 kg heavier "
             "(valve pair at its 2 x 0.15 kg target / at the ASSUMED 0.60 kg; REV-GNC-4 (f)), far beyond the 0.10 kg re-fly "
             "trigger (181 (5)), so the 285 m target and its P are NOT demonstrated for the current design until the rev3 "
             "flights at the v3.5.1 ledger (rev3 P2)")
    COLD = ("Combustion v2.4a DERIVED adiabatic bound of the cold-flow apparent thrust after an undetected flame-out with Pc "
            "invalid (open-loop lift; " + src("cold_flow_csv") + "): 12.5-13.3 N at the 62.5 N start level, 35.6-37.5 N at a "
            "200 N command (lead lines 185, 186 (2))")
    # ------------------------------------------------------------------------------------------------ identity (C5)
    d["version"] = "v3.1"
    d["date"] = "2026-10-13"
    replace_kept(d, "staging", OrderedDict(
        v=("Built as staging rev2.2 (" + STAGE + ") from rev2.1 (c2860bd89c1e5920) with the REV-GNC-4 corrections C1-C5 "
           "applied (text and folds only; no new computed number): the publication candidate for interfaces/gnc.json v3.1. "
           "The lead runs the post-check (" + src("postcheck_tool") + ", --publication), reads the diff against "
           "c2860bd89c1e5920 and publishes (lead line 190). GNC does not write interfaces/gnc.json."),
        tag="BUILD RECORD"))
    replace_kept(d, "supersedes", "gnc.json v3 (interfaces/gnc.json v3); built from staging rev2.2, which replaces the "
                                  "unpublished v3.1 staging builds (v3.1, rev1, rev2, rev2.1)")
    # ------------------------------------------------------------------------------------------------ status (C1, C2, C5)
    replace_kept(d, "status", (
        "gnc.json v3.1 (2026-10-13): built as rev2.2 from rev2.1 (c2860bd89c1e5920) with the corrections C1-C5 of the "
        "independent document check REV-GNC-4 (lead lines 189, 190); published by the lead. Simulation and analysis "
        "evidence only; nothing here is physical approval. " + VALID + ". Decided state for GNC: (1) A1 apogee target "
        "285 m ADOPTED with conditions (175 (1), 181 (6)): the launch-commit wind rule W10 < 6 m/s AND sigma_u(3 m) <= "
        "1.0 m/s is HARD for A1 and now also carries the R2 flame-out margin (186 (2)); 285 m coverage on all four bases "
        "and on pl, e19, the prep path, L400 and PURGE NOT RUN is rev3 P3. (2) Mass change control (181 (5)): re-fly at "
        "the actual ledger for any confirmed landing-mass growth >= 0.10 kg over ledger v3d; a 0.20 kg hardware allowance "
        "counts against that trigger until fasteners and seals are in the BOM (188 (11)); the v3.5 / v3.5.1 flights are "
        "rev3 P2. (3) FC_THRUST NOT armed on A1 (168 (5), 175 (6), 181 (3)); RG-16 is budgeted at the detector output; "
        "PROVISIONAL detection-latency allowance 0.5 s from the onset of the 670 N plateau, strict windowed form, no "
        "window-gain credit (REVIEWER 2.973 % against the allowed 2.985 %: 0.012 percentage points of margin, relative "
        "0.4 %, on an ASSUMED white vibration model; not robust); the trajectory consequence of 0.5 s at 670 N, the B1 "
        "miss side and the non-white sensitivity are rev3 P5. (4) Late purge commit (181 (2) as amended by 186 (1)): L* "
        "= 1.3 s for both the LO and the HI bracket; PURGE commits iff the lead from the commit to the plain relight "
        "trigger is >= 1.3 s; below it there is no purge and no unpurged relight on that pass (drogue descent; vehicle "
        "loss in the FMEA). The earlier 1.7 s value of 181 (2) and its premise (an unpurged LO start at P_total ~0.75) are "
        "REFUTED and replaced: at the worst PURGE NOT RUN states an unpurged start succeeds with P 0 under LO and under HI "
        "(light, release at E2, vapour gap, A3: a dead vehicle released at about -32 m/s; 186 (1)). The alternative, an "
        "unpurged relight with the drogue release held to >= E2 + 0.22 s, is flown in rev3 P6 and is adopted only if it "
        "gains P without the released-dead-vehicle hazard; LO/HI stays open (CF-4 generation runs, T4). 'The 0.81 s plan "
        "holds' is scoped to the predictor path. (5) Drogue release with Pc invalid (181 (4), 186 (2)): R2 ADOPTED in "
        "design over R1, pcf_tmax 0.5 s; R2 COMMAND HOLD ADOPTED: while the drogue is attached with Pc invalid, the ECU "
        "open-loop command is held at the start level 62.5 N until the release. Reason: " + COLD + "; at the start level "
        "the bound consumes the all-winds R2 margin (4.16 N) and stays inside the W10 < 6 m/s margin (16.31 N) unless "
        "chamber heat pick-up is large (TO-VERIFY: CF-3 with a load cell, a post-burn N2O pulse in the T series). R2 v2 "
        "with F_cold(lift, P_tank) in the flame-out case is rev3 P4. (6) The k_hat / apex freeze on Pc invalid is REFUTED "
        "and withdrawn (175 (4)); its replacement (re-reference to throttle-map thrust) is rev3 P7; Pc VALID is a "
        "launch-commit condition. (7) A1 FMEA inputs (fmea_inputs_rev2p1): no over-thrust detector after an in-flight Pc "
        "loss (181 (3)); a pass below L* is a vehicle loss (186 (1)); 'R2 holds the drogue' after an undetected flame-out "
        "depends on the command hold and on W10 < 6 m/s (186 (2)). (8) Open for GNC from the Mechanical review (188 (1), "
        "(7)): the bay wall and gimbal stop (RM1-01), TVC robustness over the V5c stiffness range. The rev3 items P1-P9 are "
        "defined in rev3_plan. Earlier status texts: status_superseded_rev2p2 (rev2.1), status_superseded_rev2p1 (rev2)."))
    # ------------------------------------------------------------------------------------------------ C1: relight conditions
    rc = d["requirements"]["ignition"]["relight_conditions"]
    replace_kept(rc, "v", (
        "liquid settled aft by the drogue (~1 g); tank P >= 3.5 MPa; chamber purged per the purge commit rule: PURGE "
        "commits iff the lead to the plain relight trigger is >= L* = 1.3 s (both the LO and the HI bracket, lead 186 (1)); "
        "below it there is no purge and no unpurged relight on that pass (drogue descent, vehicle loss); ignition at the "
        "floor; drogue release on the adopted predicate with the Pc-invalid term R2 (lead 181 (4)): RELEASE iff RUN AND b4 "
        "AND [(Pc valid AND Pc >= 300 kPa abs) OR b7 OR (d2-d3 = 0xFFFF AND m_est x (filtered axial specific force - its "
        "drogue-descent baseline) >= 37.16 N on 3 consecutive 100 Hz frames with the ECU in RUN)], latched; R2 COMMAND HOLD "
        "(lead 186 (2)): while the drogue is attached with Pc invalid, the ECU open-loop command is held at the start level "
        "62.5 N until the release; with Pc invalid and no R2 confirmation by t_E2 + pcf_tmax (0.5 s): hold the drogue and "
        "command ECU ABORT. The baseline is frozen at E0 in the flown implementation; R2 v2 (re-reference at E2 or "
        "drogue-drag compensation, threshold for the window, cold-flow apparent thrust F_cold(lift, P_tank) in the "
        "flame-out case) is rev3 P4 and the lead then sets pcf_tmax. The alternative for a pass below L* (unpurged relight "
        "with the drogue release held to >= E2 + 0.22 s) is not adopted unless rev3 P6 shows that it gains P without the "
        "released-dead-vehicle hazard (186 (1))"))
    replace_kept(rc, "tag", "DESIGN (LEAD CHANGELOG lines 168 (1), 181 (4), 186 (1)-(2)); R2 v2 OPEN")
    rc["status_rev2p2"] = ("L* = 1.3 s for both brackets and the R2 command hold folded from lead 186 (1)-(2); the rev2.1 text "
                           "is kept in v_superseded_rev2p2 (SUPERSEDED)")
    # ------------------------------------------------------------------------------------------------ C1: FSW entries
    fe = d["flight_software"]["rev2p1_entries"]
    pcr = fe["purge_commit_rule"]
    replace_kept(pcr, "v", "PURGE commits iff the lead to the plain relight trigger >= L* = 1.3 s (both brackets, lead 186 (1)); "
                           "below it: no purge and no unpurged relight on that pass (drogue descent, vehicle loss)")
    replace_kept(pcr, "tag", "DESIGN (LEAD 181 (2), 186 (1))")
    pcr["alternative_rev2p2"] = ("unpurged relight with the drogue release held to >= E2 + 0.22 s: flown in rev3 P6; adopted "
                                 "only if it gains P without the released-dead-vehicle hazard (lead 186 (1))")
    drp = fe["drogue_release_pc_invalid"]
    replace_kept(drp, "v", "R2 accelerometer confirmation (relight_conditions.v); pcf_tmax 0.5 s; R2 COMMAND HOLD ADOPTED (lead "
                           "186 (2)): while the drogue is attached with Pc invalid, the ECU open-loop command is held at the "
                           "start level 62.5 N until the release; R2 v2 with the cold-flow apparent thrust is rev3 P4")
    replace_kept(drp, "tag", "DESIGN (LEAD 181 (4), 186 (2))")
    # ------------------------------------------------------------------------------------------------ C1 + C4: G finding
    G = d["rev2"]["amendment_G_late_commit"]
    f_old = G["finding"]
    a0 = f_old.index("A deadline with no measurable loss")
    head = f_old[:a0]
    replace_kept(G, "finding", head + (
        "A deadline with no measurable loss would be about plain trigger - 1.9 s. Rule adopted by the lead (181 (2)) and "
        "amended by 186 (1): PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s for both the LO and "
        "the HI bracket; below it there is no purge and no unpurged relight on that pass (drogue descent, vehicle loss). "
        "The 181 (2) break-even premise (PURGE NOT RUN LO at P_total ~0.75, which gave the earlier 1.7 s value) is REFUTED "
        "by Combustion v2.4a (186 (1): at the worst PURGE NOT RUN states an unpurged start succeeds with P 0 under LO and "
        "under HI, RELEASED_THEN_A3, a dead vehicle released at about -32 m/s; " + src("unpurged_outcomes") + "). Scope: "
        "the decided predictor commits >= 2.66 s before the plain trigger in each of the 649 of 2000 runs in which the "
        "plain trigger fired (the 2.66 s minimum is over those 649 runs), with a purge flow >= 2.387 s in all 2000 runs "
        "(REVIEWER " + src("s15_g_decided") + ", lines 4-5), so the rule acts only on a contingency (gate or predictor "
        "failure); 'the 0.81 s plan holds' is scoped to the predictor path. The contingency re-admits flows of 1.9-2.4 s, "
        "for which the plan check gives no cover (e19|G73|L400 vs liq|none|L400 -39/+3, p 5.6e-9, LOSES, "
        "comparators_rev2p1); its probability, the contingency flights with the L400 plateau, the L* table in Combustion's "
        "outcome classes and the alternative (unpurged relight with the drogue release held to >= E2 + 0.22 s) are rev3 "
        "P6. Combustion v2.4a H20 / OI-31 (PURGE NOT RUN LO worst: every light followed by a 23.4 cm3 vapour gap) is "
        "DECIDED by lead 186 (1) (L* = 1.3 s; no unpurged relight below it); LO/HI stays open (CF-4 generation runs, T4)."))
    replace_kept(G, "tag_rev2p1", "SIM (rev2 flights) + REVIEWER paired tables; DESIGN rule LEAD 181 (2) amended by 186 (1) "
                                  "(L* = 1.3 s)")
    # ------------------------------------------------------------------------------------------------ C1: open items
    oi = d["open_items"]
    n_oi = len(oi)
    oi[32] = sup(oi[32], "DECIDED by lead 186 (1): L* = 1.3 s for both brackets, no purge and no unpurged relight below it")
    oi[33] = sup(oi[33], "Combustion's DERIVED cold-flow bound delivered (185) and the R2 command hold ADOPTED (186 (2)); "
                         "the current item follows below")
    oi.append("rev2.2 (lead 186 (1)): late purge commit - L* = 1.3 s ADOPTED for both brackets; below it no purge and no "
              "unpurged relight on that pass; GNC flies the alternative (unpurged relight with the drogue release held to >= "
              "E2 + 0.22 s; adopted only if it gains P without the released-dead-vehicle hazard), the L* table in Combustion's "
              "outcome classes and the contingency probability by gate-failure injection (rev3 P6); LO/HI open (CF-4 "
              "generation runs, T4); canopy dynamics TO-VERIFY (181 (2))")
    oi.append("rev2.2 (lead 186 (2)): R2 v2 (baseline re-referenced at E2 or drogue-drag compensation, threshold re-derived for "
              "the window, pcf_tmax 0.5 / 0.8 s on both bases with L400, pcf_k 0.875, flame-out, onsets 0.005 / 0.010 s and "
              "the landings after 0.5-0.8 s releases) re-flown with the R2 command hold at 62.5 N (command trace recorded) and "
              "the cold-flow apparent thrust F_cold(lift, P_tank) from " + src("cold_flow_csv") + " in the flame-out case "
              "(rev3 P4); chamber heat pick-up TO-VERIFY (CF-3 with a load cell, post-burn N2O pulse in the T series)")
    oi.append("rev2.2 (RV4-06; lead 182 (5), REV-MECH-1 RM1-01, 188 (1)): bay wall and gimbal stop - the BL-02 bleed adapter "
              "penetrates the 140 mm bay bore inside the flown gimbal envelope (REV-MECH-1, " + src("review_rev_mech_1") +
              ": r_max 70.605 mm at 7 deg, 72.08-73.26 mm at the 8 deg stop; gnc.json v3 per-run maximum gimbal p99 7.94 "
              "deg, SIM); the lead fixes BL-02 on the engine side (188 (1)); any reduction of the 8 deg stop instead changes "
              "TVC authority and needs a GNC re-fly (gimbal saturation, landing P) before it is accepted")
    oi.append("rev2.2 (lead 188 (7)): ENG-11 stiffness - GNC assesses TVC loop robustness over the V5c stiffness range "
              "3133-7406 N m/rad; if robust the lead amends the spread requirement, otherwise Mechanical stiffens (not run "
              "in this build)")
    oi.append("rev2.2 (RV4-06): the full m2_bitcheck_v29 v1.2 run on the rev3 code is rev3 P9 (181 (8)); the B1 default grain "
              "gate costs a printed ABS grain in 27.2 % of draws in the GNC model (181 (9); revisited when T1-T4 measure a)")
    oi.append("rev2.2 (C2, lead line 190): " + VALID + "; a 0.20 kg hardware allowance counts against the 181 (5) trigger "
              "(188 (11))")
    # ------------------------------------------------------------------------------------------------ C1 + C4: pending inputs
    pi = d["pending_inputs_rev2p1"]
    cus = pi["combustion_unpurged_start"]
    replace_kept(cus, "v", ("DECIDED by lead 186 (1) on Combustion v2.4a (" + src("unpurged_outcomes") + "): the P_total ~0.75 "
                            "premise for an unpurged LO start is REFUTED (at the worst PURGE NOT RUN states P 0 under LO and "
                            "HI, released-then-A3); L* = 1.3 s for both brackets; below it no purge and no unpurged relight; "
                            "the release-hold alternative is rev3 P6; LO/HI stays open (CF-4, T4)"))
    replace_kept(cus, "tag", "Combustion SIM; DESIGN (LEAD 186 (1))")
    replace_kept(pi, "lo_hi_settlement", "LO / HI of an unpurged start stays open (CF-4 generation runs, T4); it no longer moves "
                                         "L* (1.3 s for both brackets, lead 186 (1))")
    replace_kept(pi, "cold_flow_bound", OrderedDict(
        v=(COLD + "; HEM nominal 0.8-0.9 N at the start level and 12.5-13.2 N at 200 N; chamber heat pick-up excluded and "
           "TO-VERIFY (CF-3, T series); lead 186 (2): R2 command hold ADOPTED; GNC adds F_cold(lift, P_tank) to the sim6 V "
           "flame-out case and re-flies R2 v2 (rev3 P4)"),
        source=f"{src('cold_flow_csv')}; {src('cold_flow_json')}", tag="DERIVED (Combustion); DESIGN (LEAD 186 (2))"))
    replace_kept(pi, "vibration_spectrum", (
        "measured IMU vibration spectrum at F_max (DC-C / DC-D, founders): the RG-16 strict windowed form passes by 0.012 "
        "percentage points (REVIEWER: D2 strict window 0.5 s, 2.973 % against the allowed 2.985 %, " + src("rv_rg16_budget") +
        "; relative margin 0.4 %) on an ASSUMED white vibration model; a non-white spectrum can remove it (sensitivity "
        "rev3 P5)"))
    # ------------------------------------------------------------------------------------------------ C1: FMEA inputs
    fm = d["fmea_inputs_rev2p1"]
    v_old = list(fm["v"])
    replace_kept(fm, "v", [
        v_old[0], v_old[1], v_old[2],
        "PURGE NOT RUN (LO and HI): an unpurged start at the worst states succeeds with P 0 (released-then-A3: a dead vehicle "
        "released at about -32 m/s); decided response: below L* = 1.3 s no purge and no unpurged relight on that pass (lead "
        "186 (1))",
        "a pass below L* = 1.3 s (late commit after a gate or predictor failure): no relight, drogue descent, vehicle loss "
        "(lead 186 (1)); its probability is rev3 P6",
        "undetected flame-out at E2 with Pc invalid: in the rev2 flights, which modelled no cold-flow thrust, R2 holds the "
        "drogue (touchdown p50 -21.8 m/s, vehicle loss) and R1 released a dead vehicle in 1000/1000 (rev2 amendment V); "
        "with " + COLD + ", 'R2 holds' relies on the R2 command hold (lead 186 (2)) and on W10 < 6 m/s (margin 16.31 N; the "
        "all-winds margin 4.16 N is consumed); chamber heat pick-up TO-VERIFY; R2 v2 with F_cold is rev3 P4"])
    fm["status_rev2p2"] = ("lead 186 (1)-(2) folded: item 3 covers LO and HI, item 4 added (pass below L*), item 5 qualified "
                           "(cold flow, command hold, W10); the rev2.1 list is kept in v_superseded_rev2p2")
    # ------------------------------------------------------------------------------------------------ C1 + C4: W10 entry
    lcw = d["requirements"]["launch_commit_rev2p1"]["v"][1]
    replace_kept(lcw, "why", (
        "at 285 m the trim trades exhaustion for wind-driven landing failures: the failing runs of the reviewer's trim "
        "tables sit at W10 6.956-7.836 m/s (n 24; REVIEWER " + src("s03_trim") + "; " + src("review_rev_gnc_3") +
        " lines 224 and 526); the rule now also carries the R2 flame-out margin (lead 186 (2)): with the cold-flow apparent "
        "thrust at the start level (DERIVED bound 12.5-13.3 N) the all-winds margin (4.16 N) is consumed and the W10 < 6 "
        "m/s margin (16.31 N) remains unless chamber heat pick-up is large (TO-VERIFY); the equivalence of the 10-min sigma "
        "and the Dryden intensity is a model-form ASSUMPTION"))
    # ------------------------------------------------------------------------------------------------ C4: W < 6 probe
    rp = d["rev2"]["amendment_V_pc_invalid"]["reviewer_probes"]
    rp["inside_W10_lt6_N"]["base_rev2p2"] = ("A1_none (the reviewer's pcf_tmax probe, " + src("review_rev_gnc_3") +
                                              " line 330: 18.75 N at 0.5 s, 20.06 N at 0.8 s)")
    rp["inside_W10_lt6_A1J_pc_N"] = OrderedDict(
        t05_max=20.85, base="A1J_pc", tag="REVIEWER SIM (cited)",
        source=src("review_rev_gnc_3") + " line 317: 'for W < 6 m/s the largest estimate is 18.75 / 20.85 N' (A1_none / "
               "A1J_pc, pcf_tmax 0.5 s)",
        note="the binding value of lead 186 (2): the W10 < 6 m/s margin 16.31 N = 37.16 - 20.85 N (the lead's value)")
    # ------------------------------------------------------------------------------------------------ C4 (3): margin unit
    dor = d["rev2"]["rg16_v2"]["detector_output_reviewer"]
    replace_kept(dor["H_cal_comp_path"], "verdict", "instantaneous FAIL; strict windowed passes from W = 0.5 s (2.973 % against "
                                                    "2.985 %: 0.012 percentage points, relative 0.4 %)")
    replace_kept(dor, "noise_model", "frame noise ASSUMED white at 2.0 m/s2 sd at F_max (run6); a measured vibration spectrum "
                                     "may remove the 0.012 percentage-point margin (rev3 P5 sensitivity to non-white spectra, "
                                     "ASSUMED spectra)")
    # ------------------------------------------------------------------------------------------------ C2: validity statements
    d["flight_profile"]["status_rev2p2"] = VALID + "."
    d["propellant_closure_v3"]["status_rev2p2"] = (
        VALID + ". HISTORY for the targets: the DC-A1 / DC-A2 h_target_m 300.0 rows and the A1 / A2 h_target sweeps that "
        "start at 300 m are the v3 closure at 300 m (2026-10-12); A1 is 285 m (lead 175 (1), 181 (6)); A2 was removed from "
        "the 2.00 kg plan (lead line 51).")
    d["rev2"]["apogee_trim"]["status_rev2p2"] = (
        VALID + ". Per base, M60-purge-liq-A1none (liq|G73|m60 vs liq|none|m60 on A1_none) is -6/+0 (p 0.031) and LOSES "
        "(comparators_rev2p1); the m60 statement above reports the pooled and mass-effect rows only (RV4-06).")
    # ------------------------------------------------------------------------------------------------ C3: stale items
    d["flight_profile"]["mission_plan_v3"]["status_rev2p2"] = (
        "HISTORY for the targets: A1 apogee_target_m 300.0 and A2 300.0 are the v3 sizing values (2026-10-12). A1 is 285 m "
        "(lead 175 (1), 181 (6)); A2 was removed from the 2.00 kg plan (lead line 51). Every figure in this table is at "
        "ledger v3d (flight_profile.status_rev2p2).")
    d["duty_cycles"]["status_rev2p2"] = (
        "the current A1 record DC-A1_full_flight_drogue_fins_300m_v3 is the v3 BASELINE flight at 300 m (apex 304.8 m) and "
        "stays the A1 duty-cycle record of this document; whether it envelopes the 285 m target is not re-derived here (no "
        "new computation): the 285 m record comes with the rev3 coverage flights (rev3 P3); every record is at ledger v3d")
    fi = d["rev1_items"]["v"]["drogue_release_rule"]["fc_implementation"]
    replace_kept(fi, "predicate", "REPLACED by the adopted predicate with the Pc-invalid term R2 (lead 181 (4)) and the R2 "
                                  "command hold (186 (2)): requirements.ignition.relight_conditions.v; the rev1 mapping onto "
                                  "TLM_FAST is kept in predicate_superseded_rev2p2")
    replace_kept(fi, "open_item", "ANSWERED by R2 (lead 181 (4)) and the R2 command hold (186 (2)): with Pc invalid inside [E2, "
                                  "release] the accelerometer term confirms the release, or the drogue is held and the ECU "
                                  "aborted at t_E2 + pcf_tmax 0.5 s; sim6 v2.9-dev amendment V flies it "
                                  "(rev2.amendment_V_pc_invalid); R2 v2 is rev3 P4")
    pcd = d["rev1_items"]["v"]["purge_cost_A1_reserve"]
    replace_kept(pcd, "decision", inline(pcd["decision"], "0.81 s plan holds",
                                         "scope: the predictor path only, lead 181 (2); a contingency commit follows the L* "
                                         "rule, 186 (1)"))
    replace_kept(d["conventions"], "stations", (
        "z [m] from the airframe aft datum (base plane), +z toward the nose; engine pivot station 0.203 m "
        "(mechanical.json v2 frames.rv1_station_of_pivot_m, " + src("mechanical_v2_iface_v3d") + "; " + src("vehicle_v3d") +
        " z_pivot_m); the earlier text quoting 0.2223 m is SUPERSEDED"))
    d["publication_note"]["built_on_rev2p2"] = (
        "the rev2 and rev2.1 evidence (sim6 amendments M, W, F, P, R, S, G, K, V; comparators_rev2p1; the G6 recheck) runs on "
        "sim6 / run6 v2.9-dev (sim6 f90e0ba8e993ad60, run6 b054a222eff38b6e) with the interface set iface_v3d "
        "(combustion.json v2.4 469727032124329f, mechanical.json v2 4f024ed4ccb4618c, electronics.json v1 pin "
        "42fe12e15baa6e3e; pins_rev2 4c97768d53b57eef); built_on above describes the v3 evidence base of 2026-10-12/13; "
        "rev2.2 adds no evidence (text and folds only)")
    # ------------------------------------------------------------------------------------------------ C5: rev3 plan + changes
    d["rev3_plan"] = OrderedDict(
        tag="PLAN (GNC rev3, lead line 181 items 2-8 as amended by 186 and 188; results go to staging_v3.1/rev3/ with their "
            "own check; none is in this document)",
        P1="staging rev2.1 for the v3.1 publication gate (181 (1)) and this rev2.2 with the REV-GNC-4 corrections (190)",
        P2=("mass at 285 m (181 (5)): +0.1 / +0.2 / +0.3 / +0.45 kg on liq|G73 and pw|G73 (A1_none, A1J_pc) against "
            "h285; the v3.5 ledger with the ASSUMED valves as the bracket (gimballed / fixed split stated) and at the valve "
            "target; the lead's options if propellant is exhausted (trim below 275 m, or a propellant / landing-reserve change "
            "within the 2.0 kg tank); then the v3.5.1 ledger incl. the 0.20 kg hardware allowance (188 (11))"),
        P3=("285 m coverage (181 (6)): all four bases and pl, e19, the prep path, L400 and PURGE NOT RUN; landing failures "
            "by wind and inside W10 < 6 m/s; the 285 m duty-cycle record"),
        P4=("R2 v2 (181 (4), 186 (2)): baseline re-referenced at E2 or drogue-drag compensation; threshold re-derived for "
            "the window; both bases at pcf_tmax 0.5 / 0.8 s with L400, pcf_k 0.875, the flame-out case with F_cold(lift, "
            "P_tank) (DERIVED adiabatic bound = design case; HEM nominal and a +30 % heat pick-up = sensitivities, ASSUMED), "
            "onsets 0.005 / 0.010 s, landings after 0.5-0.8 s releases; the command hold at 62.5 N flown with its trace; "
            "margins for all winds and inside W10 < 6 m/s; the lead then sets pcf_tmax"),
        P5=("RG-16 at the PROVISIONAL 0.5 s allowance (181 (3)): windowed detector-output budget for A1 and B1 incl. the B1 "
            "miss side; trajectory consequence of 0.5 s at 670 N (delta-v, apex, landing P) on A1 and B1; sensitivity to "
            "non-white vibration (ASSUMED spectra)"),
        P6=("late commit (181 (2), 186 (1)): the L* table in Combustion's outcome classes; contingency flights with L400 "
            "(flows 1.9-2.4 s); probability by gate-failure injection; the alternative unpurged relight with the drogue "
            "release held to >= E2 + 0.22 s (adopted only if it gains P without the released-dead-vehicle hazard); canopy "
            "TO-VERIFY"),
        P7="K replacement (181 (7)): k_hat / apex re-reference to throttle-map thrust on FSW-R2 with a map-error band",
        P8=("RG-08 line-state flag PRIMED / UNPRIMED / UNKNOWN in the loop, incl. a late flip to UNPRIMED (UNKNOWN is "
            "treated as UNPRIMED: plan 1.41 s, prep +0.56 s)"),
        P9=("configuration (181 (8)): simulator data tables and work-area inputs pinned (strict mode refuses a mismatch), "
            "code hashes in every bit-check run, P30_reproduced part of the G6 pass, the full m2_bitcheck_v29 v1.2 run on "
            "the rev3 code"),
        not_in_rev3_unless_added=("188 (7) TVC robustness over the V5c stiffness range and the bay-wall / stop item (open "
                                  "items) are GNC tasks outside the line-181 list"))
    d["changes_from_v3"].append("later changes: changes_rev2 (staging rev2), changes_rev2p1 (staging rev2.1), changes_rev2p2 "
                                "(this build: REV-GNC-4 C1-C5)")
    # ------------------------------------------------------------------------------------------------ fold map (C1 item 9)
    ldl = d["lead_decisions_2026-10-13"]
    f21 = ldl["rev2p1_lines_175_183"]
    replace_kept(f21, "folded", copy.deepcopy(f21["folded"]))
    f21["folded"]["175 (3)"] = ("SUPERSEDED in its basis by 181 (2), whose L* value is in turn replaced by 186 (1) "
                                "(rev2.amendment_G_late_commit.finding)")
    f21["folded"]["175 (5)"] = ("R2 ADOPTED in design by 181 (4) (relight_conditions, amendment_V.status_rev2p1); only its "
                                "pcf_tmax 0.8 s proposal is NOT adopted (pcf_tmax 0.5 s)")
    ldl["rev2p2_lines_184_190"] = OrderedDict(
        source=(f"interfaces/CHANGELOG.md lines {', '.join(str(n) for n in LEAD_LINES)} (lead decisions, verbatim); "
                f"reference lines {', '.join(str(n) for n in REF_LINES)}; sha256/16 of lines 184-190 {lines_sha}"),
        verbatim=OrderedDict((str(n), cl[n]) for n in LEAD_LINES),
        folded=OrderedDict([
            ("186 (1)", "L* = 1.3 s for both brackets; below it no purge and no unpurged relight (status (4); "
                        "requirements.ignition.relight_conditions; flight_software.rev2p1_entries.purge_commit_rule; "
                        "rev2.amendment_G_late_commit.finding; fmea_inputs_rev2p1 items 3-4; "
                        "pending_inputs_rev2p1.combustion_unpurged_start and lo_hi_settlement; open items); the P_total "
                        "~0.75 premise REFUTED; the release-hold alternative is rev3 P6"),
            ("186 (2)", "R2 command hold at the 62.5 N start level (status (5); relight_conditions; "
                        "flight_software.rev2p1_entries.drogue_release_pc_invalid); Combustion's DERIVED cold-flow bound "
                        "(pending_inputs_rev2p1.cold_flow_bound; fmea_inputs_rev2p1 item 5; launch_commit_rev2p1 W10 why; "
                        "amendment_V reviewer_probes A1J_pc 20.85 N); heat pick-up TO-VERIFY; R2 v2 with F_cold is rev3 P4"),
            ("186 (3)", "OI-40 NZ-01 acceptance criterion: no GNC change"),
            ("186 (4)", "OI-37 interface configuration (mechanical.json v2.2, Electronics v2.10): no GNC change in this "
                        "build; GNC reads them when published"),
            ("186 (5)", "tank outlet geometry (OI-32) to Mechanical: no GNC change"),
            ("186 (6)", "REV-COMB-3 launched: no GNC change"),
            ("188 (1)", "RM1-01, BL-02 fixed on the engine side: GNC open item (bay wall / gimbal stop; a stop reduction "
                        "would change TVC authority)"),
            ("188 (7)", "ENG-11: GNC assesses TVC loop robustness over the V5c stiffness range 3133-7406 N m/rad: GNC open "
                        "item (not run in this build)"),
            ("188 (11)", "0.20 kg hardware allowance counts against the 181 (5) trigger: status (2), mass open item, rev3 P2"),
            ("188 other", "Mechanical FEA and CAD items, v3.5.1 freeze, REV-MECH-2: no GNC change; the v3.5.1 ledger re-fly "
                          "is rev3 P2"),
            ("190", "this build: C1-C5, the ledger-v3d validity statement in status, flight_profile, propellant_closure_v3 "
                    "and rev2.apogee_trim, the bay-wall open item; the lead runs the post-check and publishes")]),
        tag="LEAD decisions (verbatim) and where rev2.2 folds them")
    # ------------------------------------------------------------------------------------------------ records of this build
    d["changes_rev2p2"] = [
        "identity (C5): version v3.1; staging, supersedes and status replaced (old under *_superseded_rev2p2)",
        "status (C1, C2): line 186 (1)-(2), the ledger-v3d validity statement, line 188 items, rev3_plan pointer",
        "requirements.ignition.relight_conditions (C1): L* = 1.3 s, no unpurged relight below it, R2 command hold (old: "
        "v_superseded_rev2p2, tag_superseded_rev2p2); status_rev2p2",
        "flight_software.rev2p1_entries.purge_commit_rule and drogue_release_pc_invalid (C1): v and tag replaced, "
        "alternative_rev2p2 added",
        "rev2.amendment_G_late_commit.finding (C1, C4 (2)): L* 1.3 s, REFUTED premise, decided H20 / OI-31, 649 of 2000 "
        "runs (old: finding_superseded_rev2p2); tag_rev2p1 replaced",
        "open_items[32], [33] marked SUPERSEDED; six rev2.2 items appended (late commit, R2 v2 with F_cold, bay wall / stop, "
        "ENG-11 stiffness, bit-check and grain gate, mass validity)",
        "pending_inputs_rev2p1 (C1, C4 (3)): combustion_unpurged_start, lo_hi_settlement, cold_flow_bound, vibration_spectrum "
        "replaced (old under *_superseded_rev2p2)",
        "fmea_inputs_rev2p1 (C1): item 3 covers LO and HI, item 4 added, item 5 qualified (old: v_superseded_rev2p2); "
        "status_rev2p2",
        "requirements.launch_commit_rev2p1.v[1].why (C1 item 7, C4 (1)): s03_trim.out source and the R2 flame-out margin "
        "(old: why_superseded_rev2p2)",
        "rev2.amendment_V_pc_invalid.reviewer_probes (C4 (4)): inside_W10_lt6_N.base_rev2p2, inside_W10_lt6_A1J_pc_N",
        "rev2.rg16_v2.detector_output_reviewer: the same C4 (3) unit correction (H_cal_comp_path.verdict, noise_model; old "
        "under *_superseded_rev2p2)",
        "C2 validity: flight_profile.status_rev2p2, propellant_closure_v3.status_rev2p2, rev2.apogee_trim.status_rev2p2 (with "
        "the RV4-06 m60 per-base row)",
        "C3: flight_profile.mission_plan_v3.status_rev2p2 and propellant_closure_v3.status_rev2p2 (300 m targets HISTORY), "
        "duty_cycles.status_rev2p2, rev1_items drogue_release_rule.fc_implementation predicate and open_item replaced, "
        "purge_cost_A1_reserve.decision inline scope marker, conventions.stations (pivot 0.203 m), "
        "publication_note.built_on_rev2p2",
        "C5: rev3_plan (P1-P9 defined), changes_from_v3 pointer, publication wording",
        "fold map: lead_decisions_2026-10-13.rev2p1_lines_175_183.folded 175 (3) / 175 (5) reworded (old: "
        "folded_superseded_rev2p2); rev2p2_lines_184_190 (verbatim 186, 188, 190)",
        "checkpoint_rev2p1 moved to rev2p1_checkpoint_superseded_rev2p2; checkpoint_rev2p2, inputs_read.rev2p2, "
        "scripts_rev2p2, rev2p2_document_self_check added",
        "not changed: every number computed by GNC; RV4-07 notes (ASSUMED mass share, ledger P00 label, BOM sums, inputs "
        "outside the hub) are left for the mass work of rev3 P2"]
    d["inputs_read"]["rev2p2"] = OrderedDict(
        [(k, OrderedDict(path=p, sha256_16=h)) for k, (p, h) in SRC.items()]
        + [("changelog_lines", OrderedDict(lines=sorted(LEAD_LINES + REF_LINES), sha256_16_of_lines=lines_sha))])
    d["scripts_rev2p2"] = [f"{STAGE}/scripts/m2_gnc_json_v31_rev2p2.py"]
    d["rev2p1_checkpoint_superseded_rev2p2"] = d.pop("checkpoint_rev2p1")
    d["checkpoint_rev2p2"] = OrderedDict(
        delivered_reviewed_date=("GNC (Senior Space/GNC, rev3 session) / independent document check REV-GNC-4 by the "
                                 "REV-GNC-3 reviewer: PUBLISHABLE WITH CORRECTIONS (" + src("review_rev_gnc_4") + ") / "
                                 "2026-10-13; C1-C5 applied in this build; the lead runs the post-check, reads the diff "
                                 "and publishes (line 190)"),
        configuration=("text and folds only; no flight and no new computed number; source rev2.1 JSON c2860bd89c1e5920 "
                       "(MANIFEST_rev2p1 02c554a2f0fe68fa); builder " + VERSION + " (deterministic); CHANGELOG lines "
                       "184-190 quoted (sha256/16 " + lines_sha + "); the evidence base is unchanged: sim6 / run6 v2.9-dev "
                       "on iface_v3d (publication_note.built_on_rev2p2)"),
        claim=["C1: lead line 186 (1)-(6) folded into status, relight_conditions, the FSW entries, the G finding, open items, "
               "pending inputs, the FMEA inputs, the W10 entry, the rev3 plan and the fold map; old text kept",
               "C2: ledger-v3d validity stated in status, flight_profile, propellant_closure_v3 and rev2.apogee_trim; 285 m and "
               "its P are NOT demonstrated for CAD v3.5",
               "C3: stale 300 m targets, duty-cycle record, pre-R2 predicate, unscoped plan sentence, pivot station and build "
               "basis marked or corrected",
               "C4: the four citations corrected (s03_trim.out, 649 of 2000 runs, 0.012 percentage points as the reviewer's "
               "number, the A1_none base and A1J_pc 20.85 N)",
               "C5: rev3 P1-P9 defined, change-list pointers, publication wording",
               "RV4-06: bay-wall / gimbal-stop open item, 175 (5) fold wording, remaining notes as open items"],
        sources=[src(k) for k in SRC] + ["interfaces/CHANGELOG.md lines 184-190"],
        tests=["builder run twice: identical bytes", "author scan rev2p2_document_self_check: 0 unmarked",
               "reviewer gate t10_postcheck v2 with --publication: exit required 0 (log in " + STAGE + "/logs/)",
               "key diff against rev2.1 recorded (" + STAGE + "/logs/gnc_v3.1_rev2p2_keydiff.json)",
               "NOT run: any flight (by design)"],
        unknowns=["LO / HI of an unpurged start (CF-4, T4); whether the release-hold alternative gains P (rev3 P6)",
                  "R2 v2 with F_cold not yet flown at this build; chamber heat pick-up TO-VERIFY (CF-3)",
                  "RG-16 strict windowed margin 0.012 percentage points (REVIEWER) on an ASSUMED white vibration model; the "
                  "consequence of 0.5 s at 670 N and the B1 miss side (rev3 P5)",
                  "every P / reserve / closure / trim figure is at ledger v3d; CAD v3.5 +0.87 to +1.17 kg; massprops v3.5.1 "
                  "pending; valve masses ASSUMED; fasteners and seals (0.20 kg allowance)",
                  "canopy dynamics TO-VERIFY; bay wall / gimbal stop (RM1-01); TVC robustness over the V5c stiffness range",
                  "no hardware data; nothing here is physical approval"],
        next_closure=["the lead runs t10_postcheck --publication on this file, reads the diff against c2860bd89c1e5920 and "
                      "publishes interfaces/gnc.json v3.1 (line 190); GNC does not write interfaces/gnc.json",
                      "GNC rev3 (rev3_plan P1-P9) in staging_v3.1/rev3/ with its own check"],
        note="the harness refused a separate REPORT .md from this GNC session; the checkpoint is carried here and in the "
             "session handback")
    d["rev2p2_document_self_check"] = self_check(d)
    os.makedirs(OUTD, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    kd = keydiff(d0, d)
    kd = OrderedDict(builder=VERSION, a=dict(path=src("rev2p1_json")), b=dict(path=OUT, sha256_16=sha(OUT)),
                     n_changed=len(kd["changed"]), n_added=len(kd["added"]), n_removed=len(kd["removed"]), **kd)
    with open(KEYDIFF, "w") as f:
        json.dump(kd, f, indent=1, ensure_ascii=False)
    sc = d["rev2p2_document_self_check"]
    print(f"wrote {OUT} {sha(OUT)} keys {len(d)} (rev2.1 {len(d0)}); open_items {n_oi} -> {len(oi)}; self-check hits "
          f"{sc['hits']} unmarked {sc['unmarked']}; keydiff changed {kd['n_changed']} added {kd['n_added']} removed "
          f"{kd['n_removed']} ({sha(KEYDIFF)})")
    for h in sc["unmarked_list"]:
        print("UNMARKED", h["pattern"], h["path"])
    if sc["unmarked"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
