#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - independent re-computation of the mesh-convergence metrics (own formulas, Roache GCI with Fs = 1.25,
refinement ratio 2) from the three mesh levels the author stored in sax_convergence_v1.json, at the governing locations, and a
classification that does not assume asymptotic convergence (oscillation / divergence / p far below the element order).

Element: CAX6 (quadratic), nominal order of the stress error p ~ 2 for smooth fields; p_obs < 1 => the evaluation point is in a
singular / steep-gradient zone and Richardson extrapolation is not a valid basis for a margin.
Usage: python -I rm1_convergence_recheck.py <sax_convergence_v1.json> <out_json>
"""
import json
import math
import sys

KEYS = [("FA1Q", "A1_22.2", "ENG-TC-01", "regular"), ("FA1D", "A1_22.2", "ENG-TC-01", "regular"),
        ("FA1U", "A1_22.2", "ENG-TC-01", "regular"), ("LC2", "B1_1", "ENG-TC-01", "regular"),
        ("LC1", "B1_19", "ENG-TC-02", "regular"), ("LC1", "B1_1", "ENG-TC-03", "regular"),
        ("LC1", "B1_1", "ENG-NZ-01", "regular"), ("FA1Q", "A1_22.2", "ENG-NZ-01", "regular"),
        ("FA1D", "A1_22.2", "ENG-TC-09", "regular"), ("FA1Q", "A1_22.2", "ENG-TC-09", "regular"),
        ("BN", "B1_19", "ENG-TC-02", "regular"), ("TB70", "TB", "ENG-TC-02", "regular")]


def metrics(f):
    f1, f2, f3 = f            # coarse (h 2), medium (h 1), fine (h 0.5)
    e21, e32 = f2 - f1, f3 - f2
    out = {"values": f, "e21": e21, "e32": e32}
    if e21 == 0 or e32 == 0:
        out["class"] = "no change"
        return out
    R = e32 / e21
    out["ratio_e32_e21"] = R
    if R < 0:
        out["class"] = "OSCILLATORY"
        return out
    p = math.log(abs(e21 / e32)) / math.log(2.0)
    out["p_obs"] = p
    if p <= 0:
        out["class"] = "DIVERGING (changes grow with refinement)"
        return out
    ext = f3 + e32 / (2.0 ** p - 1.0)
    gci = 1.25 * abs(e32 / f3) / (2.0 ** p - 1.0) if f3 != 0 else float("nan")
    out.update({"extrapolated": ext, "GCI_fine": gci})
    out["class"] = ("asymptotic-like (p >= 1.5)" if p >= 1.5 else "monotonic but p << element order: singular/steep zone, "
                    "extrapolation not a valid basis")
    return out


def main():
    d = json.load(open(sys.argv[1]))
    idx = {tuple(r["key"]): r for r in d["rows"] if r.get("quantity") == "MS"}
    res = {"who": "REV-MECH-1", "date": "2026-10-13", "source": sys.argv[1], "levels": d.get("levels"),
           "mesh": d.get("mesh"), "rows": []}
    for k in KEYS:
        r = idx.get(k)
        if r is None:
            res["rows"].append({"key": list(k), "missing": True})
            continue
        m = metrics(r["values"])
        m.update({"key": list(k), "author_p": r.get("p_observed"), "author_GCI": r.get("GCI_fine"),
                  "author_extrapolated": r.get("extrapolated"), "author_verdict": r.get("verdict")})
        if "p_obs" in m and r.get("p_observed") is not None:
            m["p_matches_author"] = abs(m["p_obs"] - r["p_observed"]) < 1e-9
        res["rows"].append(m)
        print(json.dumps(m))
    # census of the author's verdicts over all MS rows
    cens = {}
    for r in d["rows"]:
        if r.get("quantity") == "MS":
            cens[r.get("verdict")] = cens.get(r.get("verdict"), 0) + 1
    res["author_verdict_census_MS_rows"] = cens
    # rows where the sign of MS changes between levels or the fine value is negative
    flips = [r["key"] for r in d["rows"] if r.get("quantity") == "MS" and min(r["values"]) < 0 < max(r["values"])]
    res["MS_sign_change_across_levels"] = flips
    json.dump(res, open(sys.argv[2], "w"), indent=1)
    print(json.dumps(cens))
    print("sign changes across levels:", flips)


if __name__ == "__main__":
    main()
