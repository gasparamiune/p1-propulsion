"""m2_rev4b_wmark v1.0 (GNC rev4b, 2026-10-19): REV-GNC-6 RV6-10 residual of the withdrawn-value sidecars.
rev3 and rev4 are NOT modified. The rev4 sidecar for rev3/results/rev3_results.json (set W2: 32 P4 gap_N / T_mid_N
leaves) missed the lit-model command-hold trace. This script writes a REPLACEMENT sidecar for that one file to
<GNC_WM4B_OUT>/results/rev3_results.json.WITHDRAWN.json (staged as staging_v3.1/rev4b/withdrawn_markers/...):
  W2 = the 32 rev4 leaves (copied from the staged rev4 sidecar, sha-pinned)
       + every leaf under /P4_R2v2/command_hold_trace/lit_k100_hold/ (RV6-10: n_runs, hold_s[], hold_records_at_62p5N[],
         ECU_command_values_N[], F_cold_max_N[], valve_lift_max_mm[], R2_estimate_max_N[], F_truth_max_N[])
       + /bitchecks/v2.10_vs_v2.9/functional/checks/hold_trace_lit_k875 (code-function check run on the withdrawn lit
         model: kept as a code fact, withdrawn as lit-side evidence);
  W1 = /bitchecks/v2.10_vs_v2.9/functional/checks/release_hold_0p22 (same treatment; the W1 E2 + 0.22 s release-hold
       mechanism; beyond the RV6-10 list, added for consistency; the rh220 / rh250 arms themselves already carry an in-file
       SUPERSEDED status in rev3_results.json and are not repeated).
The flame-out traces (/P4_R2v2/command_hold_trace/fo_cb_hold, fo_cb_nohold) are NOT withdrawn.
It also writes a rev4b WITHDRAWN_INDEX.json that points at the rev4 index (all other rev4 sidecars stand unchanged).
Checks: target sha256 equals the rev4 sidecar's target_sha256; every listed leaf exists in the target; the RV6-10 quoted
ranges (R2_estimate_max_N 52.39-60.30 N, F_truth_max_N 59.5-65.3 N) equal the target values.
DERIVED bookkeeping only; no number is recomputed. Deterministic (no timestamps): run twice -> identical bytes."""
import hashlib
import json
import os
import re
from collections import OrderedDict

VERSION = "m2_rev4b_wmark v1.0"
DATE = "2026-10-19"
HUB = "/home/claude/work/shared-fallback/engine"
REV3 = f"{HUB}/01-systems-gnc/staging_v3.1/rev3"
REV4WM = f"{HUB}/01-systems-gnc/staging_v3.1/rev4/withdrawn_markers"
STAGE = "01-systems-gnc/staging_v3.1/rev4b"
OUT = os.environ.get("GNC_WM4B_OUT", "/home/claude/work/space/out/rev4b/wmark")
TARGET_REL = "results/rev3_results.json"
PIN = OrderedDict([
    ("rev3_results", (f"{REV3}/{TARGET_REL}", "e0f6e7611fe523b5")),
    ("rev4_sidecar", (f"{REV4WM}/{TARGET_REL}.WITHDRAWN.json", None)),
    ("rev4_index", (f"{REV4WM}/WITHDRAWN_INDEX.json", "9a652a75813fada2")),
    ("review_rev_gnc_6", (f"{HUB}/reviews/REVIEW-GNC-R4.md", "d83c93504accd30a")),
])
RV6_10 = ("Exact correction: add to results/rev3_results.json.WITHDRAWN.json set W2 the paths "
          "/P4_R2v2/command_hold_trace/lit_k100_hold/* (9 leaf patterns: n_runs, hold_s[], hold_records_at_62p5N[], "
          "ECU_command_values_N[], F_cold_max_N[], valve_lift_max_mm[], R2_estimate_max_N[] 52.39-60.30 N, F_truth_max_N[] "
          "59.5-65.3 N) and /bitchecks/v2.10_vs_v2.9/functional/checks/hold_trace_lit_k875, or state why these lit-model "
          "values are not withdrawn.")
LIT = "/P4_R2v2/command_hold_trace/lit_k100_hold/"
BC_LIT = "/bitchecks/v2.10_vs_v2.9/functional/checks/hold_trace_lit_k875"
BC_W1 = "/bitchecks/v2.10_vs_v2.9/functional/checks/release_hold_0p22"
CODE_FACT = ("code-function check (sim6 v2.10-dev vs v2.9-dev, m2_bitcheck_v210 v1.0): its pass is kept as a code fact "
             "(the sequencing reproduces across versions); it is withdrawn as evidence of any physical value")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + f"[{i}]")
    else:
        yield p, o


def patterns(paths):
    pp = OrderedDict()
    for p in paths:
        q = re.sub(r"\[\d+\]", "[]", p)
        pp[q] = pp.get(q, 0) + 1
    return pp


def main():
    for k, (p, h) in PIN.items():
        if h and sha256(p)[:16] != h:
            raise RuntimeError(f"{k}: {p} sha256/16 {sha256(p)[:16]} != pinned {h}")
    review = open(PIN["review_rev_gnc_6"][0], encoding="utf-8").read()
    if RV6_10 not in review:
        raise RuntimeError("RV6-10 text not verbatim in REVIEW-GNC-R4.md")
    tgt = PIN["rev3_results"][0]
    old = json.load(open(PIN["rev4_sidecar"][0]))
    if old["target_sha256"] != sha256(tgt):
        raise RuntimeError("rev4 sidecar target_sha256 != rev3_results.json")
    d = json.load(open(tgt))
    leaves = OrderedDict(walk(d))
    w2_old = [s for s in old["sets"] if s["id"] == "W2"]
    assert len(old["sets"]) == 1 and len(w2_old) == 1
    w2_old = w2_old[0]
    lit = [p for p in leaves if p.startswith(LIT)]
    new_w2 = lit + [BC_LIT]
    new_w1 = [BC_W1]
    for p in w2_old["leaf_paths"] + new_w2 + new_w1:
        if p not in leaves:
            raise RuntimeError(f"leaf not in target: {p}")
    if set(new_w2) & set(w2_old["leaf_paths"]):
        raise RuntimeError("overlap with the rev4 W2 set")
    names = sorted({re.sub(r"\[\d+\]$", "", p[len(LIT):]) for p in lit})
    want = sorted(["n_runs", "hold_s", "hold_records_at_62p5N", "ECU_command_values_N", "F_cold_max_N",
                   "valve_lift_max_mm", "R2_estimate_max_N", "F_truth_max_N"])
    r2 = [v for p, v in leaves.items() if p.startswith(LIT + "R2_estimate_max_N[")]
    ft = [v for p, v in leaves.items() if p.startswith(LIT + "F_truth_max_N[")]
    checks = OrderedDict(
        rev4_sidecar_target_sha_equal=True,
        rv6_10_text_verbatim=True,
        lit_k100_hold_key_names_equal_rv6_10_list=(names == want),
        rv6_10_R2_estimate_range_52p39_60p30=(round(min(r2), 2) == 52.39 and round(max(r2), 2) == 60.30),
        rv6_10_F_truth_range_59p5_65p3=(round(min(ft), 1) == 59.5 and round(max(ft), 1) == 65.3),
        bitcheck_values=OrderedDict(hold_trace_lit_k875=leaves[BC_LIT], release_hold_0p22=leaves[BC_W1]),
        flameout_traces_not_listed=not any("/fo_cb_" in p for p in new_w2 + new_w1),
        every_leaf_exists_in_target=True)
    if not all(v for k, v in checks.items() if k != "bitcheck_values"):
        raise RuntimeError(f"check failed: {checks}")
    W2 = OrderedDict((k, w2_old[k]) for k in ("id", "what", "withdrawn_by", "replacement", "use"))
    W2["what"] = (w2_old["what"] + "; rev4b (RV6-10): also the lit-model command-hold trace "
                  "/P4_R2v2/command_hold_trace/lit_k100_hold/* and the lit_k875 hold-trace bitcheck")
    W2["withdrawn_by"] = w2_old["withdrawn_by"] + "; REV-GNC-6 RV6-10 (lit_k100_hold trace and hold_trace_lit_k875)"
    paths = w2_old["leaf_paths"] + new_w2
    W2["n_leaf_paths"] = len(paths)
    W2["n_leaf_paths_rev4"] = len(w2_old["leaf_paths"])
    W2["n_leaf_paths_added_rev4b"] = len(new_w2)
    W2["path_patterns"] = patterns(paths)
    W2["leaf_paths"] = paths
    W2["per_path_note"] = OrderedDict([(BC_LIT, CODE_FACT + " (lit model 62.5 N x pcf_k, arm lit_k875)")])
    W1 = OrderedDict(id="W1", what="release-hold comparator arms at E2 + 0.22 s (rh220, rh250): here only the v2.10 "
                                   "functional bitcheck of the 0.22 s release-hold mechanism",
                     withdrawn_by="lead CHANGELOG line 194 (1) / (3); rev3 F3 / proposal [2]; rev4b: added for consistency "
                                  "with RV6-10 (not in the RV6-10 list)",
                     replacement="none needed (the arms are SUPERSEDED in-file: /P6_late_commit/comparator_line194/arms/"
                                 "*rh220* / *rh250* status)",
                     use="evidence only", n_leaf_paths=1, path_patterns=patterns(new_w1), leaf_paths=new_w1,
                     per_path_note=OrderedDict([(BC_W1, CODE_FACT + " (E2 + 0.22 s release hold, W1)")]))
    sc = OrderedDict(
        version=VERSION, date=DATE, kind="WITHDRAWN-VALUE MARKER (sidecar; target unchanged)",
        target=tgt, target_sha256=sha256(tgt), whole_file_withdrawn=False,
        replaces_sidecar=OrderedDict(path=PIN["rev4_sidecar"][0], sha256=sha256(PIN["rev4_sidecar"][0]),
                                     version=old.get("version"), note="the rev4 sidecar stays as staged; this one "
                                     "replaces it for rev3_results.json (it carries all 32 rev4 W2 leaves unchanged)"),
        review_item="REV-GNC-6 RV6-10 (MINOR): " + RV6_10,
        sets=[W2, W1],
        note=old.get("note", "") + "; rev4b: the lit_k100_hold trace (27 leaves, 8 key patterns) and the two v2.10 "
             "functional bitchecks are added; RV6-10 counts '9 leaf patterns' = the 8 lit_k100_hold keys + "
             "hold_trace_lit_k875; the flame-out traces fo_cb_hold / fo_cb_nohold are NOT withdrawn",
        checks=checks,
        n_leaf_paths_total=len(paths) + len(new_w1))
    os.makedirs(os.path.join(OUT, "results"), exist_ok=True)
    out = os.path.join(OUT, TARGET_REL + ".WITHDRAWN.json")
    with open(out, "w") as f:
        json.dump(sc, f, indent=1)
    idx = OrderedDict(
        version=VERSION, date=DATE, rev3_root=REV3,
        base_index=OrderedDict(path=PIN["rev4_index"][0], sha256=sha256(PIN["rev4_index"][0]),
                               note="every rev4 sidecar listed there stands unchanged except rev3_results.json"),
        files=OrderedDict([(TARGET_REL, OrderedDict(
            sidecar=f"{STAGE}/withdrawn_markers/{TARGET_REL}.WITHDRAWN.json", sidecar_sha256=sha256(out),
            replaces=f"01-systems-gnc/staging_v3.1/rev4/withdrawn_markers/{TARGET_REL}.WITHDRAWN.json",
            n_W1=len(new_w1), n_W2=len(paths), n_W2_rev4=len(w2_old["leaf_paths"]), n_W2_added=len(new_w2),
            review="REV-GNC-6 RV6-10"))]),
        tag="DERIVED bookkeeping; no value recomputed; not physical approval")
    p = os.path.join(OUT, "WITHDRAWN_INDEX.json")
    with open(p, "w") as f:
        json.dump(idx, f, indent=1)
    print(f"wrote {out} {sha256(out)[:16]} W2 {len(paths)} (rev4 {len(w2_old['leaf_paths'])} + {len(new_w2)}) W1 "
          f"{len(new_w1)}; {p} {sha256(p)[:16]}; checks {json.dumps(checks)}", flush=True)


if __name__ == "__main__":
    main()
