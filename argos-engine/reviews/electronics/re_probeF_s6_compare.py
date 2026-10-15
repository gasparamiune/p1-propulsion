"""REV-ELEC-1 probe F (part 2): S6 abort set re-run on the reviewer copies with the 30 bar firmware abort persistence at 5 ms
(ovp5: filtered channel as published; ovp5raw: raw channel, the wording of CHANGELOG l.160 item 2) against the published v2.9 record
(06-electronics/results/sil_v2p9/S6_aborts.json). Lists every case whose pass flag, cause or abort time changes, and the blocked-throat /
pintle-runaway cases with the firmware and comparator trip times (the l.160 (2) claim: the comparator stays the fast path).
Usage: python -I re_probeF_s6_compare.py <scratch_dir>   (reads <scratch>/s6_ovp5/S6_aborts.json and <scratch>/s6_ovp5raw/S6_aborts.json)
Writes re_probeF_s6_compare.{json,txt} next to this script.
"""
import json, os, sys, hashlib

S = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
PUB = "/home/claude/work/shared-fallback/engine/06-electronics/results/sil_v2p9/S6_aborts.json"


def load(p):
    d = json.load(open(p))
    cases = d.get("cases", d) if isinstance(d, dict) else d
    if isinstance(cases, dict):
        cases = list(cases.values())
    return {c["case"]: c for c in cases}, hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


pub, hpub = load(PUB)
var = {v: load(os.path.join(S, "s6_%s" % v, "S6_aborts.json")) for v in ("ovp5", "ovp5raw")}
out = {"id": "re_probeF_s6_compare", "review": "REV-ELEC-1", "tag": "SIM", "published_sha256_16": hpub,
       "variant_sha256_16": {v: var[v][1] for v in var}, "n_cases": len(pub), "changed": {}, "pressure_cases": {}}
lines = ["REV-ELEC-1 probe F part 2: S6 with the 30 bar FW abort persistence 5 ms (ovp5 filtered, ovp5raw raw) vs published v2.9",
         "published S6 sha256/16 %s; cases %d; failures published %d, ovp5 %d, ovp5raw %d" % (
             hpub, len(pub), sum(not c["pass"] for c in pub.values()),
             sum(not c["pass"] for c in var["ovp5"][0].values()), sum(not c["pass"] for c in var["ovp5raw"][0].values()))]
keys = ("pass", "cause_name", "inj_to_abort_s", "inj_to_hw_comparator_trip_s", "Pc_max_abs_Pa", "t_Pc_above_30bar_s", "t_Pc_above_MEOP_s")
for name, c in pub.items():
    for v in var:
        cv = var[v][0].get(name)
        if cv is None:
            continue
        diff = {k: (c.get(k), cv.get(k)) for k in keys if c.get(k) != cv.get(k)}
        if diff:
            out["changed"].setdefault(name, {})[v] = diff
    if "throat" in name or "runaway" in name or "hard_start" in name:
        out["pressure_cases"][name] = {"published": {k: c.get(k) for k in keys},
                                       **{v: {k: var[v][0][name].get(k) for k in keys} for v in var}}
lines.append("cases with any change in %s:" % ", ".join(keys))
if not out["changed"]:
    lines.append("  none")
for name, dv in out["changed"].items():
    for v, d in dv.items():
        lines.append("  %-62s %-8s %s" % (name, v, "; ".join("%s %s -> %s" % (k, a, b) for k, (a, b) in d.items())))
lines.append("over-pressure / runaway / late-light cases: cause, FW-or-HW abort time after injection [s], comparator trip [s], pass")
for name, r in out["pressure_cases"].items():
    s = "  %-62s" % name
    for v in ("published", "ovp5", "ovp5raw"):
        x = r[v]
        s += " | %s %s %s %s" % (v[:7], x["cause_name"], x["inj_to_abort_s"], x["inj_to_hw_comparator_trip_s"]) + (" P" if x["pass"] else " F")
    lines.append(s)
json.dump(out, open(os.path.join(HERE, "re_probeF_s6_compare.json"), "w"), indent=1)
open(os.path.join(HERE, "re_probeF_s6_compare.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
