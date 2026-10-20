"""J-FWD patch-to-patch 5 % judgement (fea3d 2026-10-20 ~12:58Z; lead 12:28Z (2): (a'') seat_s5L12_mu0_go vs (a') seat_s5L8_mu0_go "within
5 % at every state" -> (b2) on L8, else L12 for (b2), (b2') and (b1)).  DERIVED from the posts of the two runs (no solve):
  histcheck_<B>.json (jfwd_histcheck A B): the 54 seat lines (Pm+Pb and Pm per line), exact screw N at the shear plane, M at the shear
                     plane and M_max on the threaded length, HEAD force, seat window sum (|daz| <= 9 deg, |z'| <= 9 mm)
  runcmp_<B>.json    (jfwd_runcmp A B x_lo=26.5): N, V, M on the common x' sections with the small-value rule of jfwd_runcmp (relative
                     differences only where |B| >= 5 % of the step's largest |value|; smaller values compared in absolute terms)
A state passes when the quantities the lead uses (12:28Z (1): N, V, M and the 54 lines; 11:41Z (1): the seat window) are all within
5 %: 54 lines max |rel Pm+Pb|, N and V exact at the shear plane (V only where |V_B| > 50 N), M at the shear plane x' 28.6 and M_max on
the threaded length (relative only where |M_B| >= 300 N mm, about 10 % of the FA1S bending; below that the absolute difference is
shown), the seat window sum and the HEAD force.  The section-grid flags of jfwd_runcmp (N, V, M at every x' station, incl. the M
zero crossings) and the shell pull are listed as information.
usage: jfwd_patch_judge.py JOB_A JOB_B -> jfwd/runs/JOB_A/judge_<JOB_B>.json"""
from __future__ import annotations
import sys, json
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
TOL = 0.05


def main(ja, jb):
    H = json.loads((RUNS / ja / f"histcheck_{jb}.json").read_text())
    R = json.loads((RUNS / ja / f"runcmp_{jb}.json").read_text())
    out = {"A": ja, "B_reference": jb, "doc": __doc__.split("usage:")[0].strip(), "tol": TOL, "states": {}, "pass_all": True}
    flags = {}
    for f in R.get("flags_gt_5pct", []):
        flags.setdefault(f[0], []).append(f)
    for st, p in H["pairs"].items():
        ln = p["lines"]["seat"]
        rs = R["steps"].get(st, {})
        rec = {"lines_max_rel_PmPb": ln["max_abs_rel_PmPb"], "lines_max_rel_Pm": ln.get("max_abs_rel_Pm"), "lines_n_gt_5pct": ln["n_gt_5pct"],
               "lines_min_MS_PQ": [ln["min_MS_PQ_A"], ln["min_MS_PQ_B"]],
               "N_exact": p["N"], "seat_window": p["seat_window"], "HEAD": p["HEAD"],
               "M_shear_plane": p["M_shear_plane"], "M_max_threaded": p["M_max_threaded"],
               "sections_max_abs_rel": rs.get("max_abs_rel"), "section_flags": flags.get(st, [])}
        fails = []
        if ln["max_abs_rel_PmPb"] > TOL:
            fails.append(f"54 lines Pm+Pb up to {100 * ln['max_abs_rel_PmPb']:.1f} % ({ln['n_gt_5pct']} lines > 5 %)")
        for q in ("N_exact", "seat_window", "HEAD"):
            r = rec[q].get("rel")
            if r is not None and abs(r) > TOL:
                fails.append(f"{q} {100 * r:+.1f} %")
        pe = rs.get("plane_exact") or {}
        rec["V_exact"] = {"A": pe.get("V_A"), "B": pe.get("V_B"), "rel": pe.get("rel_V")}
        if pe.get("rel_V") is not None and abs(pe["rel_V"]) > TOL:
            fails.append(f"V_exact {100 * pe['rel_V']:+.1f} %")
        for q in ("M_shear_plane", "M_max_threaded"):
            a_, b_ = rec[q].get("A"), rec[q].get("B")
            if a_ is None or b_ is None:
                continue
            if abs(b_) >= 300.0:
                r = (a_ - b_) / abs(b_)
                rec[q]["judged"] = f"rel {100 * r:+.1f} %"
                if abs(r) > TOL:
                    fails.append(f"{q} {100 * r:+.1f} % ({a_} vs {b_} N mm)")
            else:
                rec[q]["judged"] = f"small (|B| < 300 N mm): abs diff {a_ - b_:+.1f} N mm"
        rec["information"] = [f for f in rec["section_flags"]]
        rec["fails"] = fails
        rec["pass"] = not fails
        out["pass_all"] &= rec["pass"]
        out["states"][st] = rec
        print(f"{st:8s} {'PASS' if rec['pass'] else 'FAIL'} | lines PmPb max {100 * ln['max_abs_rel_PmPb']:.2f} % (n>5% {ln['n_gt_5pct']}), "
              f"min MS {ln['min_MS_PQ_A']} vs {ln['min_MS_PQ_B']} | N {p['N']['A']} vs {p['N']['B']} | window {p['seat_window']['A']} vs "
              f"{p['seat_window']['B']} | M28.6 {p['M_shear_plane']['A']} vs {p['M_shear_plane']['B']} | sections {rs.get('max_abs_rel')}"
              + (f" | FAILS: {'; '.join(fails)}" if fails else ""), flush=True)
    print("PASS ALL" if out["pass_all"] else "NOT WITHIN 5 % AT EVERY STATE", flush=True)
    (RUNS / ja / f"judge_{jb}.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
