"""Delta table between two J-FWD soak envelopes (FEA3D-2, 2026-10-21; lead brief: "the final envelope (v5, or v6 if cD moves anything)
with a delta table against v4").  Read-only on the two envelope files; writes the delta json + md.  [DERIVED]
Per state: the envelope quantities (screw N max / min, seat window min / max, M at x' 28.6 max, M max on the threaded length over the
instances, seat-line P+Q minimum with its instance and line, lines negative, spread) old -> new with the instance that sets each, and the
count of the 54 seat lines whose envelope MS is lower / higher / equal in the new file (3 decimals).
usage: jfwd_envelope_delta_v352.py OLD NEW [NOTE]   (version tags, e.g. v4 v5; NOTE: optional text stored as "note" and printed under the
table; without it the output is as before) -> results/v352/jfwd_envelope_delta_v352_<NEW>_vs_<OLD>.{json,md}"""
import sys, json, hashlib
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results/v352")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def env_path(v):
    return RES / f"jfwd_soak_envelope_v352_{v}.json"


def mthr(s):
    m = s.get("M_max_threaded_Nmm") or {}
    best = max(((v[0], k) for k, v in m.items() if v and isinstance(v[0], (int, float))), default=(None, None))
    return [best[0], best[1]]


def main(a, b, note=None):
    A, B = json.loads(env_path(a).read_text()), json.loads(env_path(b).read_text())
    out = {"id": f"jfwd_envelope_delta_v352_{b}_vs_{a}", "old": {"file": env_path(a).name, "sha16": sha16(env_path(a))},
           "new": {"file": env_path(b).name, "sha16": sha16(env_path(b))}, "states": {}, "doc": __doc__.split("usage:")[0].strip()}
    if note:
        out["note"] = note
    keys = ["N_max_N", "N_min_N", "window_min_N", "window_max_N", "M_x28.6_max_Nmm", "lines_min_MS_PQ", "n_lines_negative_env", "max_spread_MS"]
    for st in B["states"]:
        ea, eb = (A["states"].get(st) or {}).get("envelope") or {}, B["states"][st]["envelope"]
        rec = {"quantities": {}, "lines": {}}
        for k in keys:
            va, vb = ea.get(k), eb.get(k)
            rec["quantities"][k] = {"old": va, "new": vb, "changed": va != vb}
        ma, mb = mthr(A["states"].get(st) or {}), mthr(B["states"][st])
        rec["quantities"]["M_max_threaded_max_Nmm"] = {"old": ma, "new": mb, "changed": ma != mb}
        lo = hi = eq = 0
        moved = []
        for ln, L in B["states"][st]["lines"].items():
            ob = ((A["states"].get(st) or {}).get("lines") or {}).get(ln) or {}
            x, y = ob.get("MS_PQ_env"), L.get("MS_PQ_env")
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                continue
            if round(y, 3) < round(x, 3):
                lo += 1
                moved.append([ln, x, ob.get("env_from"), y, L.get("env_from")])
            elif round(y, 3) > round(x, 3):
                hi += 1
            else:
                eq += 1
        rec["lines"] = {"lower_in_new": lo, "higher_in_new": hi, "equal": eq, "lower_rows": sorted(moved, key=lambda r: r[3])}
        out["states"][st] = rec
    oj = RES / f"jfwd_envelope_delta_v352_{b}_vs_{a}.json"
    om = RES / "tables" / f"jfwd_envelope_delta_v352_{b}_vs_{a}.md"
    oj.write_text(json.dumps(out, indent=1))

    def f(v):
        if isinstance(v, list):
            return " ".join(str(x) for x in v if x is not None)
        return str(v)
    L = [f"# J-FWD envelope delta {b} against {a} [DERIVED]", "",
         f"Old `{env_path(a).name}` `{sha16(env_path(a))}`; new `{env_path(b).name}` `{sha16(env_path(b))}`. Only changed quantities are listed; "
         "lines = the 54 seat lines' envelope MS (P+Q <= 2 Fty(T)) at 3 decimals.", "",
         "| state | quantity | old (from) | new (from) |", "|---|---|---|---|"]
    for st, r in out["states"].items():
        ch = [(k, q) for k, q in r["quantities"].items() if q["changed"]]
        for k, q in ch:
            L.append(f"| {st} | {k} | {f(q['old'])} | {f(q['new'])} |")
        if not ch:
            L.append(f"| {st} | (no envelope quantity changed) | | |")
        li = r["lines"]
        L.append(f"| {st} | seat lines lower / higher / equal | | {li['lower_in_new']} / {li['higher_in_new']} / {li['equal']} |")
    if note:
        L += ["", "Note: " + note]
    L += ["", "Nothing here is physical approval."]
    om.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(oj, sha16(oj), om, sha16(om))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
