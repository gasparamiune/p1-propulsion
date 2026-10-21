"""m2_rev4_wmark v1.0 (GNC rev4, 2026-10-19): withdrawn-value marker sidecars for the staged rev3 evaluation files
(REV-GNC-5 RV5-06; lead CHANGELOG 208 (6)). rev3 is NOT modified (lead: 'Do not modify staging_v3.1/rev3'): for each
staged rev3 file that carries values computed from a withdrawn model or arm, a sidecar JSON is written to
out/rev4/wmark/<rev3 relative path>.WITHDRAWN.json naming the target file and its sha256, the withdrawn JSON paths (every
leaf path matched, listed in full and as patterns), the withdrawing decision and where the replacement (if any) lives.
The rev4 staging copies these sidecars to staging_v3.1/rev4/withdrawn_markers/.
Withdrawn sets:
  W1 'E2 + 0.22 s' release-hold comparator arms rh220 / rh250 (lead CHANGELOG 194 (1), rev3 F3; replaced by the P6c
     population-hold arms rh300c200 / rh400c200 / rh190c500, themselves NOT ADOPTED by 204 (2) / 208 (3)).
  W2 lit model 62.5 N x pcf_k (lit_k100 / lit_k875* arms and every lit_* statistic / threshold derived from them,
     including P4 gap_N and T_mid_N, which are computed from the lit minima) (lead CHANGELOG 194 (2); REV-GNC-5 RV5-06).
  W3 60 g-residual bands in proposal [3] (SUPERSEDED by 204 (4) / the 80 g onset rule of 208 (1)); marked in the
     rev4 v3.2 proposal file, listed here for completeness (no rev3 evaluation key carries them alone).
DERIVED bookkeeping only; no number is recomputed here."""
import hashlib
import json
import os
import re
import time
from collections import OrderedDict

VERSION = "m2_rev4_wmark v1.0"
REV3 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3"
OUT = os.environ.get("GNC_WM_OUT", "/home/claude/work/space/out/rev4/wmark")

W1 = dict(id="W1", what="release-hold comparator arms at E2 + 0.22 s (rh220, rh250)",
          withdrawn_by="lead CHANGELOG line 194 (1); rev3 F3 / proposal [2]",
          replacement="rev3 P6c arms rh300c200 / rh400c200 / rh190c500 (p6_late_commit_v1p1.json release_hold_v1p1); "
                      "the whole unpurged-alternative branch is NOT ADOPTED (lead 204 (2), strengthened by 208 (3))",
          use="evidence only; not admissible for any P, band or proposal")
W2 = dict(id="W2", what="lit model 62.5 N x pcf_k (arms lit_k100, lit_k875, lit_k875_L400, lit_k875_dt05, lit_k875_dt10) "
                        "and every lit-side statistic derived from them, incl. P4 thresholds gap_N and T_mid_N",
          withdrawn_by="lead CHANGELOG line 194 (2); REV-GNC-5 RV5-06 (gap_N / T_mid_N unmarked); lead 208 (6)",
          replacement="lit side PENDING Combustion v2.4b (F_cold(lift, P_tank) + grain_q1d start history); rev4 "
                      "r2_starve (out/rev4/r2_starve/r2_starve.json) flies the start-plateau lit side on the sim's own "
                      "thrust model as a bracket, not as the v2.4b replacement",
          use="evidence only; the flame-out side (flameout_* keys) is NOT withdrawn")
PAT_W1 = re.compile(r"rh220|rh250")
PAT_W2 = re.compile(r"lit_k|lit_min|lit_margin|lit_not_released|WITHDRAWN_MODEL|/gap_N$|/T_mid_N$|/lit_|^/lit")


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


def leaf_hits(d, pat):
    return [p for p, v in walk(d) if pat.search(p)]


def patterns(paths):
    pp = OrderedDict()
    for p in paths:
        q = re.sub(r"\[\d+\]", "[]", p)
        pp[q] = pp.get(q, 0) + 1
    return pp


def sidecar(rel, sets, paths_by_set, note=None, whole_file=False):
    tgt = os.path.join(REV3, rel)
    sc = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), kind="WITHDRAWN-VALUE MARKER (sidecar; target unchanged)",
                     target=tgt, target_sha256=sha256(tgt), whole_file_withdrawn=whole_file, sets=[], note=note)
    n = 0
    for s in sets:
        e = OrderedDict(s)
        if not whole_file:
            ps = paths_by_set.get(s["id"], [])
            e["n_leaf_paths"] = len(ps)
            e["path_patterns"] = patterns(ps)
            e["leaf_paths"] = ps
            n += len(ps)
        sc["sets"].append(e)
    sc["n_leaf_paths_total"] = n
    out = os.path.join(OUT, rel + ".WITHDRAWN.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(sc, open(out, "w"), indent=1)
    return out, n


def main():
    idx = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), rev3_root=REV3, files=OrderedDict())
    for rel in ("results/eval/p6_late_commit.json", "results/eval/p6_late_commit_v1p1.json", "results/eval/rev3_fly.json",
                "results/eval/reserve_dip.json", "results/eval/r2v2_eval.json", "results/rev3_results.json"):
        d = json.load(open(os.path.join(REV3, rel)))
        h1 = leaf_hits(d, PAT_W1)
        h2 = [p for p in leaf_hits(d, PAT_W2) if p not in set(h1)]
        if rel.endswith("rev3_results.json"):
            # rev3_results already marks lit_* as WITHDRAWN_MODEL; the unmarked keys are P4 gap_N / T_mid_N (RV5-06)
            h2 = [p for p in h2 if p.startswith("/P4_R2v2/thresholds/") and (p.endswith("/gap_N") or p.endswith("/T_mid_N"))]
            h1 = []
        sets = [s for s, h in ((W1, h1), (W2, h2)) if h]
        if not sets:
            continue
        note = None
        if rel.endswith("p6_late_commit.json"):
            note = "v1.0 file: P_total_alternative_DERIVED in lstar_table uses the rh220 minimum (W1); superseded by p6_late_commit_v1p1.json"
        if rel.endswith("rev3_results.json"):
            note = "rev3_results.json marks the lit minima/margins as *_WITHDRAWN_MODEL but not gap_N / T_mid_N (16 entries), which are computed from them"
        out, n = sidecar(rel, sets, {"W1": h1, "W2": h2}, note=note)
        idx["files"][rel] = dict(sidecar=os.path.relpath(out, OUT), n_W1=len(h1), n_W2=len(h2))
        print(f"{rel}: W1 {len(h1)} W2 {len(h2)} -> {out}", flush=True)
    meta = sorted(f for f in os.listdir(os.path.join(REV3, "tables/fly/meta")) if PAT_W1.search(f) or "lit_k" in f)
    for f in meta:
        rel = f"tables/fly/meta/{f}"
        s = W1 if PAT_W1.search(f) else W2
        out, _ = sidecar(rel, [s], {}, whole_file=True,
                         note="whole arm withdrawn; the matching table tables/fly/" + f.replace(".csv.json", ".csv.gz") +
                              " is evidence only")
        tab = os.path.join(REV3, "tables/fly", f.replace(".csv.json", ".csv.gz"))
        idx["files"][rel] = dict(sidecar=os.path.relpath(out, OUT), set=s["id"], table=os.path.relpath(tab, REV3),
                                 table_sha256=sha256(tab) if os.path.exists(tab) else None)
        print(f"{rel}: {s['id']} whole arm -> {out}", flush=True)
    idx["W3"] = "60 g-residual bands of rev3 proposal [3]: SUPERSEDED (lead 204 (4); 208 (1) fixes the onset at 80 g); marked in out/rev4/v32/v32_proposals_rev4.json"
    p = os.path.join(OUT, "WITHDRAWN_INDEX.json")
    json.dump(idx, open(p, "w"), indent=1)
    print("wrote", p, flush=True)


if __name__ == "__main__":
    main()
