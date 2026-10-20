"""J-FWD run-to-run comparison of the mesh-independent screw and seat quantities (fea3d 2026-10-20 ~11:25Z; lead 10:15Z (3) / 10:24Z: the
mu 0 sharp patch (a) must reproduce js5 within 5 % on the 54 lines AND the screw sections; (b2) = broken edge vs (a) / js5).
DERIVED from the per-run posts (no new solve): jfwd_shank.py (shank.json: N, V, M along the screw on the common x' grid, the exact shear-plane
resultant, M_max on the threaded length / in the TC-01 hole) and jfwd_seatforce.py (seatforce.json: screw tension, seat normal force, shell
pull, footprint).  Relative differences A vs B (B = reference); |rel| > 5 % flagged for N and V where |B| >= 5 % of the step's largest
|N| / |V| on the grid, for M where |B| >= 5 % of the step's largest |M| (small values: absolute differences only).
usage: jfwd_runcmp.py JOB_A JOB_B [x_lo=26.0] [map=SA:SB,...] [tag=T] -> jfwd/runs/JOB_A/runcmp_<JOB_B>[_T].json
       map: compare state SA of A with state SB of B (default: same names); A == B with a map = the in-run history check (11:50Z)."""
from __future__ import annotations
import sys, json
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")


def rel(a, b):
    if a is None or b is None or abs(b) < 1e-9:
        return None
    return round((a - b) / abs(b), 4)


def main(ja, jb, x_lo=26.0, smap=None, tag=""):
    A = {k: json.loads((RUNS / j / f"{k}.json").read_text()) for j, k in ((ja, "shank"), (ja, "seatforce"))}
    B = {k: json.loads((RUNS / jb / f"{k}.json").read_text()) for j, k in ((jb, "shank"), (jb, "seatforce"))}
    out = {"A": ja, "B_reference": jb, "doc": __doc__.split("usage:")[0].strip(), "x_lo": x_lo, "steps": {}, "flags_gt_5pct": []}
    pairs = list(smap.items()) if smap else [(s, s) for s in A["shank"]["steps"]]
    out["state_map"] = dict(pairs)
    for st, stb in pairs:
        ra = A["shank"]["steps"].get(st)
        rb = B["shank"]["steps"].get(stb)
        if ra is None or rb is None:
            continue
        sb = {round(s["x"], 2): s for s in rb["sections"]}
        rows = []
        big = {q: max([abs(s[q]) for s in rb["sections"] if s["x"] >= x_lo] or [1.0]) for q in ("N", "V", "M")}
        for s in ra["sections"]:
            x = round(s["x"], 2)
            if x < x_lo or x not in sb:
                continue
            t = sb[x]
            r = {"x": x}
            for q in ("N", "V", "M"):
                r[f"{q}_A"], r[f"{q}_B"] = s[q], t[q]
                r[f"d{q}"] = round(s[q] - t[q], 1)
                r[f"rel_{q}"] = rel(s[q], t[q]) if abs(t[q]) >= 0.05 * big[q] else None
                if r[f"rel_{q}"] is not None and abs(r[f"rel_{q}"]) > 0.05:
                    out["flags_gt_5pct"].append([st, f"section x' {x} {q}", r[f"rel_{q}"], s[q], t[q]])
            rows.append(r)
        pa, pb = ra["plane_exact"], rb["plane_exact"]
        rec = {"sections": rows,
               "max_abs_rel": {q: max([abs(r[f"rel_{q}"]) for r in rows if r[f"rel_{q}"] is not None] or [0.0]) for q in ("N", "V", "M")},
               "plane_exact": {"N_A": pa["N_N"], "N_B": pb["N_N"], "rel_N": rel(pa["N_N"], pb["N_N"]), "V_A": pa["V_N"], "V_B": pb["V_N"],
                               "rel_V": rel(pa["V_N"], pb["V_N"]) if abs(pb["V_N"]) > 50 else None},
               "M_max_threaded": {"A": ra.get("M_max_threaded"), "B": rb.get("M_max_threaded")},
               "M_max_shank_in_TC01": {"A": ra.get("M_max_shank_in_TC01"), "B": rb.get("M_max_shank_in_TC01")}}
        mta, mtb = ra.get("M_max_threaded") or {}, rb.get("M_max_threaded") or {}
        rec["M_max_threaded"]["rel"] = rel(mta.get("M"), mtb.get("M"))
        fa, fb = A["seatforce"]["steps"].get(st), B["seatforce"]["steps"].get(stb)
        if fa and fb:
            sa, sb2 = fa["seat_TC02"], fb["seat_TC02"]
            wa, wb = sa["footprint"].get("window_daz9_zp9_N"), sb2["footprint"].get("window_daz9_zp9_N")
            ha, hb = fa["screw"], fb["screw"]
            sha, shb = fa["shell_TC02"], fb["shell_TC02"]
            ca = sa["footprint"].get("centroid_force_weighted") or {}
            cb = sb2["footprint"].get("centroid_force_weighted") or {}
            rec["seat"] = {"HEAD_A": ha["HEAD_on_screw_along_n_N"], "HEAD_B": hb["HEAD_on_screw_along_n_N"],
                           "rel_HEAD": rel(ha["HEAD_on_screw_along_n_N"], hb["HEAD_on_screw_along_n_N"]),
                           "seat_n_A": sa["along_n_inward_N"], "seat_n_B": sb2["along_n_inward_N"], "rel_seat_n": rel(sa["along_n_inward_N"], sb2["along_n_inward_N"]),
                           "seat_r_A": sa["normal_force_radial_sum_N"], "seat_r_B": sb2["normal_force_radial_sum_N"],
                           "shell_A": sha["shell_pull_N_tie_minus_seat"], "shell_B": shb["shell_pull_N_tie_minus_seat"],
                           "rel_shell": rel(sha["shell_pull_N_tie_minus_seat"], shb["shell_pull_N_tie_minus_seat"]),
                           "seat_window_A": wa, "seat_window_B": wb, "rel_seat_window": rel(wa, wb),
                           "centroid_A": ca, "centroid_B": cb,
                           "area_A": sa["footprint"].get("area_faces_mean_CPRESS_pos_mm2"), "area_B": sb2["footprint"].get("area_faces_mean_CPRESS_pos_mm2"),
                           "extent_A": sa["footprint"].get("extent_CPRESS_pos"), "extent_B": sb2["footprint"].get("extent_CPRESS_pos")}
            for k in ("rel_HEAD", "rel_seat_n", "rel_seat_window", "rel_shell"):
                v = rec["seat"][k]
                if v is not None and abs(v) > 0.05:
                    out["flags_gt_5pct"].append([st, k, v])
        out["steps"][st if st == stb else f"{st}~{stb}"] = rec
        print(f"{st}{'' if st == stb else ' vs ' + stb}: sections max |rel| N {rec['max_abs_rel']['N']:.4f} V {rec['max_abs_rel']['V']:.4f} M {rec['max_abs_rel']['M']:.4f} | plane N "
              f"{pa['N_N']} vs {pb['N_N']} V {pa['V_N']} vs {pb['V_N']} | M_max thread {mta.get('M')}@{mta.get('x')} vs {mtb.get('M')}@{mtb.get('x')}"
              + (f" | HEAD {rec['seat']['HEAD_A']} vs {rec['seat']['HEAD_B']} seat {rec['seat']['seat_n_A']} vs {rec['seat']['seat_n_B']} shell "
                 f"{rec['seat']['shell_A']} vs {rec['seat']['shell_B']}" if "seat" in rec else ""), flush=True)
    p = RUNS / ja / f"runcmp_{jb}{('_' + tag) if tag else ''}.json"
    p.write_text(json.dumps(out, indent=1))
    print("flags > 5 %:", out["flags_gt_5pct"])
    print("wrote", p)
    return out


if __name__ == "__main__":
    kw = dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a)
    sm = dict(p.split(":", 1) for p in kw["map"].split(",")) if kw.get("map") else None
    main(sys.argv[1], sys.argv[2], float(kw.get("x_lo", 26.0)), sm, kw.get("tag", ""))
