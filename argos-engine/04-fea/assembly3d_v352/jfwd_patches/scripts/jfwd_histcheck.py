"""J-FWD history check (fea3d 2026-10-20 ~12:00Z; lead 11:41Z (b2) form (A) criterion: each repeat state within 5 % of its first instance
on the 54 seat lines, the screw N and M, and the seat window sum).  DERIVED from the per-run posts (no solve):
  compare.json  (jfwd_seat_cmp: the 54 seat lines (family 'seat') and 10 hole-edge lines of the patch, Pm / Pm+Pb / MS_PQ per line)
  shank.json    (jfwd_shank: exact N at the shear plane, M at the shear plane x' 28.6, M_max on the threaded length)
  seatforce.json(jfwd_seatforce: HEAD force, seat window sum |daz| <= 9 deg, |z'| <= 9 mm (lead 11:41Z: the reported seat force))
usage: jfwd_histcheck.py JOB             -> each repeat label (meta step_base) vs its base state in the same run
       jfwd_histcheck.py JOB_A JOB_B      -> the same state names in two runs of the same model (e.g. (a) vs (a'): two histories)
       -> jfwd/runs/JOB(_A)/histcheck[_JOB_B].json"""
from __future__ import annotations
import sys, json
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
TOL = 0.05


def rel(a, b):
    if a is None or b is None or abs(b) < 1e-9:
        return None
    return round((a - b) / abs(b), 4)


def load(job):
    d = {k: json.loads((RUNS / job / f"{k}.json").read_text()) for k in ("compare", "shank", "seatforce")}
    d["meta"] = json.loads((RUNS / job / "meta.json").read_text())
    return d


def state(d, st):
    c = d["compare"]["steps"][st]
    lines = {(r["family"], r["delta_deg"], r["z_prime_mm"]): r for r in c["relax_seat_lines_cmp"]}
    sh = d["shank"]["steps"][st]
    sp = {round(s["x"], 2): s for s in sh["sections"]}
    m286 = sp.get(28.6, {}).get("M")
    sf = d["seatforce"]["steps"][st]
    return {"lines": lines, "N": -sh["plane_exact"]["N_N"], "V": sh["plane_exact"]["V_N"], "M_shear_plane": m286,
            "M_max_threaded": (sh.get("M_max_threaded") or {}).get("M"), "HEAD": sf["screw"]["HEAD_on_screw_along_n_N"],
            "seat_window": sf["seat_TC02"]["footprint"].get("window_daz9_zp9_N"), "seat_n_total": sf["seat_TC02"]["along_n_inward_N"]}


def pair(a, b, la, lb):
    out = {"A": la, "B_reference": lb}
    for q in ("N", "V", "M_shear_plane", "M_max_threaded", "HEAD", "seat_window", "seat_n_total"):
        out[q] = {"A": a[q], "B": b[q], "rel": rel(a[q], b[q])}
    fam = {}
    for f in ("seat", "hole_edge"):
        keys = [k for k in b["lines"] if k[0] == f and k in a["lines"]]
        rows = []
        for k in keys:
            ra, rb = a["lines"][k], b["lines"][k]
            rows.append({"delta_deg": k[1], "z_prime_mm": k[2], "PmPb_A": ra["PmPb_patch"], "PmPb_B": rb["PmPb_patch"],
                         "rel_PmPb": rel(ra["PmPb_patch"], rb["PmPb_patch"]), "Pm_A": ra["Pm_patch"], "Pm_B": rb["Pm_patch"],
                         "rel_Pm": rel(ra["Pm_patch"], rb["Pm_patch"]), "MS_PQ_A": ra["MS_PQ_patch"], "MS_PQ_B": rb["MS_PQ_patch"]})
        fam[f] = {"n_lines": len(rows),
                  "max_abs_rel_PmPb": max((abs(r["rel_PmPb"]) for r in rows if r["rel_PmPb"] is not None), default=None),
                  "max_abs_rel_Pm": max((abs(r["rel_Pm"]) for r in rows if r["rel_Pm"] is not None), default=None),
                  "n_gt_5pct": sum(1 for r in rows if any(r[k] is not None and abs(r[k]) > TOL for k in ("rel_PmPb", "rel_Pm"))),
                  "min_MS_PQ_A": min((r["MS_PQ_A"] for r in rows), default=None), "min_MS_PQ_B": min((r["MS_PQ_B"] for r in rows), default=None),
                  "rows": rows}
    out["lines"] = fam
    crit = {"seat_lines_54": (fam["seat"]["max_abs_rel_PmPb"] or 0) <= TOL and (fam["seat"]["max_abs_rel_Pm"] or 0) <= TOL,
            "screw_N": abs(out["N"]["rel"] or 0) <= TOL, "screw_M_shear_plane": abs(out["M_shear_plane"]["rel"] or 0) <= TOL,
            "seat_window": abs(out["seat_window"]["rel"] or 0) <= TOL}
    out["criterion_5pct"] = crit
    out["pass"] = all(crit.values())
    return out


def main(ja, jb=None):
    A = load(ja)
    if jb is None:
        base = A["meta"].get("step_base", {})
        after = A["meta"].get("step_after", {})
        pairs = [(lab, b, A, A) for lab, b in base.items()]
        tag = ""
    else:
        B = load(jb)
        pairs = [(s, s, A, B) for s in A["compare"]["steps"] if s in B["compare"]["steps"]]
        after = A["meta"].get("step_after", {})
        tag = f"_{jb}"
    res = {"job_A": ja, "job_B": jb or ja, "doc": __doc__.split("usage:")[0].strip(), "tolerance": TOL, "pairs": {}}
    for la, lb, DA, DB in pairs:
        r = pair(state(DA, la), state(DB, lb), la, lb)
        r["after_A"] = DA["meta"].get("step_after", {}).get(la)
        r["after_B"] = DB["meta"].get("step_after", {}).get(lb)
        res["pairs"][la if jb is None else la] = r
        s = r["lines"]["seat"]
        print(f"{la} (after {r['after_A']}) vs {lb} (after {r['after_B']}): N {r['N']['A']:.1f}/{r['N']['B']:.1f} ({r['N']['rel']}) | M28.6 "
              f"{r['M_shear_plane']['A']}/{r['M_shear_plane']['B']} ({r['M_shear_plane']['rel']}) | window {r['seat_window']['A']}/"
              f"{r['seat_window']['B']} ({r['seat_window']['rel']}) | 54 lines max |rel| PmPb {s['max_abs_rel_PmPb']} Pm {s['max_abs_rel_Pm']} "
              f"(>5 %: {s['n_gt_5pct']}), min MS_PQ {s['min_MS_PQ_A']} / {s['min_MS_PQ_B']} | PASS {r['pass']}", flush=True)
    p = RUNS / ja / f"histcheck{tag}.json"
    p.write_text(json.dumps(res, indent=1))
    print("wrote", p)
    return res


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
