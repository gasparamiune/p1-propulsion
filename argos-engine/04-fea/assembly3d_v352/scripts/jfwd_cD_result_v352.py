"""cD result (FEA3D-2, 2026-10-21; lead 2026-10-21T02:01:34Z (C)): the convergence check seat_sDL12_mu0 (s6 + two Ball fields h 0.04
mm, r 0.3 + 0.3, at both ends of the governing seat line d+6.051 z'0; FINAL TC-01 fcb3b5b93bebdb01; mu 0; physical order PRELOAD >
SOAK52 > SOAK > SOAK70 > FA1S, as (b2')) against (b2) seat_s6L12_mu0 (s6) and (b2') seat_s9L12_mu0 (s9).  Read-only on the posts.
Rule per state on the governing line (lead 02:01:34Z (C)):
  cD within 5 % of s6 (0.95 <= cD / s6 <= 1.05 on PmPb)  -> s6 and C1 stand; MF note: the check passed on the final geometry;
  cD > s6 by more than 5 %                               -> cD governs and anchors the band; (b1) re-based C1' = cD / s9 per line and
                                                            state (floored 1.00) on the lines cD refines, C1 elsewhere; the cD - s6
                                                            difference is quoted as mesh + geometry (not split);
  cD < s6 by more than 5 %                               -> s6 stands (conservative); the difference is quoted.
  The two-mesh p = 1 / p = 2 estimate stays information.
Also: all 54 lines (cD / s6 and cD / s9 per line; the Ball-zone class of each line from its end points' distance to the Ball centres:
core <= 0.3 mm at both ends, transition <= 0.6 mm, else outside), cD's resultants (screw N at the shear plane, M at x' 28.6, M max on the
thread, seat window) against the final-candidate envelope, and the boundary-extrapolation record.  [SIM values; DERIVED ratios]
usage: jfwd_cD_result_v352.py [ENV_TAG]  (default v5) -> results/v352/jfwd_cD_result_v352.json + results/v352/tables/jfwd_cD_result_v352.md"""
import sys, json, math, hashlib
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
RES = Path("/home/claude/work/fea3d/results/v352")
OUT, OUT_MD = RES / "jfwd_cD_result_v352.json", RES / "tables" / "jfwd_cD_result_v352.md"
CD, S6, S9 = "seat_sDL12_mu0", "seat_s6L12_mu0", "seat_s9L12_mu0"
STATES = ["PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S"]
GOV = "d+6.051_z+0.0"
AZ, ZC, RB = 18.0, 127.513 - 0.24, 28.625
BALLS = [(28.652, 6.051), (31.313 / math.cos(math.radians(6.051)) - 0.03, 6.051)]   # (r, delta) at z' 0


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def jl(p):
    return json.loads(Path(p).read_text())


def xyz(r, delta, zp):
    a = math.radians(AZ + delta)
    return (r * math.cos(a), r * math.sin(a), ZC + zp)


def zone(delta, zp):
    p0 = xyz(RB, delta, zp)
    p1 = xyz(31.313 / math.cos(math.radians(delta)), delta, zp)
    b0, b1 = xyz(*BALLS[0], 0.0), xyz(*BALLS[1], 0.0)
    d0, d1 = math.dist(p0, b0), math.dist(p1, b1)
    cls = "core" if max(d0, d1) <= 0.3 else ("transition" if max(d0, d1) <= 0.6 else "outside")
    return cls, round(d0, 3), round(d1, 3)


def lines(run, st):
    c = jl(RUNS / run / "compare.json")
    out = {}
    for row in c["steps"][st]["relax_seat_lines_cmp"]:
        if row["family"] == "hole_edge":
            continue
        out[f"d{row['delta_deg']:+.3f}_z{row['z_prime_mm']:+.1f}"] = row
    return out


def res(run, st):
    sh, sf = jl(RUNS / run / "shank.json")["steps"][st], jl(RUNS / run / "seatforce.json")["steps"][st]
    m286 = [x["M"] for x in sh["sections"] if abs(x["x"] - 28.6) < 0.051]
    return {"N_plane_N": round(abs(sh["plane_exact"]["N_N"]), 1), "M_x28.6_Nmm": round(abs(m286[0]), 1) if m286 else None,
            "M_max_threaded_Nmm": round(abs((sh.get("M_max_threaded") or {}).get("M", 0.0)), 1),
            "seat_window_N": sf["seat_TC02"]["footprint"].get("window_daz9_zp9_N")}


def main(tag):
    env = RES / f"jfwd_soak_envelope_v352_{tag}.json"
    E = jl(env)
    files = {f"{r}/{f}": sha16(RUNS / r / f) for r in (CD, S6, S9) for f in ("compare.json", "shank.json", "seatforce.json") if (RUNS / r / f).exists()}
    for f in ("judge_seat_s6L12_mu0.json", "judge_seat_s9L12_mu0.json", "ccx_run.json", "meta.json", "COMPRESSED.txt", "DECK_XZ.txt"):
        if (RUNS / CD / f).exists():
            files[f"{CD}/{f}"] = sha16(RUNS / CD / f)
    files[env.name] = sha16(env)
    ex = RES / "jfwd_patch_extrap_nodes_v352.json"
    X = jl(ex)
    files[ex.name] = sha16(ex)
    out = {"id": "jfwd_cD_result_v352", "doc": __doc__.split("usage:")[0].strip(), "inputs_sha16": files, "governing_line": GOV,
           "balls": [{"r": round(r, 3), "delta_deg": d, "z_prime": 0.0} for r, d in BALLS], "states": {},
           "extrapolation": {k: {kk: v[kk] for kk in ("n_prescribed", "max_extrap_mm", "n_gt_0p01mm", "min_distance_to_ball_centre_mm",
                                                       "any_on_flat_region")} for k, v in X["patches"].items()}}
    for st in STATES:
        Ld, L6, L9 = lines(CD, st), lines(S6, st), lines(S9, st)
        g = {k: L[GOV] for k, L in (("cD", Ld), ("s6", L6), ("s9", L9))}
        r6 = g["cD"]["PmPb_patch"] / g["s6"]["PmPb_patch"]
        r9 = g["cD"]["PmPb_patch"] / g["s9"]["PmPb_patch"]
        verdict = ("within 5 %: s6 and C1 stand (check passed on the final geometry)" if 0.95 <= r6 <= 1.05 else
                   ("cD higher by more than 5 %: cD governs and anchors the band; (b1) C1' = cD / s9 on the lines cD refines" if r6 > 1.05 else
                    "cD lower by more than 5 %: s6 stands (conservative); difference quoted"))
        per = {}
        for k in Ld:
            if k in L6 and k in L9:
                zc, d0, d1 = zone(Ld[k]["delta_deg"], Ld[k]["z_prime_mm"])
                per[k] = {"PmPb_cD": Ld[k]["PmPb_patch"], "PmPb_s6": L6[k]["PmPb_patch"], "PmPb_s9": L9[k]["PmPb_patch"],
                          "MS_cD": Ld[k]["MS_PQ_patch"], "MS_s6": L6[k]["MS_PQ_patch"], "MS_s9": L9[k]["MS_PQ_patch"],
                          "cD_over_s6": round(Ld[k]["PmPb_patch"] / L6[k]["PmPb_patch"], 4),
                          "cD_over_s9": round(Ld[k]["PmPb_patch"] / L9[k]["PmPb_patch"], 4), "ball_zone": zc, "end_dist_mm": [d0, d1]}
        rr = sorted(v["cD_over_s6"] for v in per.values())
        ms_min = min(per.items(), key=lambda kv: kv[1]["MS_cD"])
        e = E["states"][st]["envelope"]
        rcd = res(CD, st)
        mthr = max((v[0] for v in (E["states"][st].get("M_max_threaded_Nmm") or {}).values() if v and v[0] is not None), default=None)
        # both sides of every envelope{} resultant (05:2xZ fix: N_min and window_max were not checked), the per-instance thread M max
        moves = {"N_max": rcd["N_plane_N"] > e["N_max_N"][0], "N_min": rcd["N_plane_N"] < e["N_min_N"][0],
                 "window_min": (rcd["seat_window_N"] or 9e9) < e["window_min_N"][0],
                 "window_max": (rcd["seat_window_N"] or 0) > e["window_max_N"][0],
                 "M_x28.6_max": (rcd["M_x28.6_Nmm"] or 0) > e["M_x28.6_max_Nmm"][0], "M_max_threaded": rcd["M_max_threaded_Nmm"] > (mthr or 0),
                 "lines_min": ms_min[1]["MS_cD"] < e["lines_min_MS_PQ"][0]}
        out["states"][st] = {
            "governing_line": {"PmPb_MPa": {k: v["PmPb_patch"] for k, v in g.items()}, "MS_PQ": {k: v["MS_PQ_patch"] for k, v in g.items()},
                               "cD_over_s6": round(r6, 4), "cD_over_s9": round(r9, 4), "verdict": verdict,
                               "C1_prime_if_cD_governs": round(max(1.0, r9), 4)},
            "all_lines": {"cD_over_s6_min_median_max": [rr[0], rr[len(rr) // 2], rr[-1]], "n_cD_over_s6_gt_1.05": sum(x > 1.05 for x in rr),
                          "n_lines": len(rr), "cD_min_MS_line": [ms_min[0], ms_min[1]["MS_cD"]], "per_line": per},
            "resultants_cD": rcd,
            "envelope_tag": tag,
            "envelope_now": {"N_max_N": e["N_max_N"], "N_min_N": e["N_min_N"], "window_min_N": e["window_min_N"],
                             "window_max_N": e["window_max_N"], "M_x28.6_max_Nmm": e["M_x28.6_max_Nmm"],
                             "M_max_threaded_max_Nmm": mthr, "lines_min_MS_PQ": e["lines_min_MS_PQ"]},
            "cD_outside_envelope": moves}
    OUT.write_text(json.dumps(out, indent=1))
    L = ["# cD convergence check on the governing seat line (seat_sDL12_mu0; FINAL TC-01; mu 0) [SIM / DERIVED]", "",
         f"Rule: lead 2026-10-21T02:01:34Z (C). Governing line {GOV}. Envelope compared: {env.name} `{sha16(env)}`.", "",
         "| state | PmPb s9 / s6 / cD (MPa) | MS s9 / s6 / cD | cD / s6 | cD / s9 | verdict | all 54 lines cD / s6 min / median / max (n > 1.05) | cD min-MS line |",
         "|---|---|---|---|---|---|---|---|"]
    for st, r in out["states"].items():
        gl, al = r["governing_line"], r["all_lines"]
        L.append(f"| {st} | {gl['PmPb_MPa']['s9']} / {gl['PmPb_MPa']['s6']} / {gl['PmPb_MPa']['cD']} | {gl['MS_PQ']['s9']:+.3f} / "
                 f"{gl['MS_PQ']['s6']:+.3f} / {gl['MS_PQ']['cD']:+.3f} | {gl['cD_over_s6']:.4f} | {gl['cD_over_s9']:.4f} | {gl['verdict']} | "
                 f"{al['cD_over_s6_min_median_max'][0]:.3f} / {al['cD_over_s6_min_median_max'][1]:.3f} / {al['cD_over_s6_min_median_max'][2]:.3f} "
                 f"({al['n_cD_over_s6_gt_1.05']}) | {al['cD_min_MS_line'][0]} {al['cD_min_MS_line'][1]:+.3f} |")
    L += ["", "Resultants of cD against the envelope (as solved) [SIM]:", "",
          "| state | N plane (env min / max) | window (env min / max) | M x' 28.6 (env max) | M max thread (env max) | outside the envelope |", "|---|---|---|---|---|---|"]
    for st, r in out["states"].items():
        c, e = r["resultants_cD"], r["envelope_now"]
        mv = [k for k, v in r["cD_outside_envelope"].items() if v]
        L.append(f"| {st} | {c['N_plane_N']} ({e['N_min_N'][0]} / {e['N_max_N'][0]}) | {c['seat_window_N']} ({e['window_min_N'][0]} / {e['window_max_N'][0]}) | {c['M_x28.6_Nmm']} "
                 f"({e['M_x28.6_max_Nmm'][0]}) | {c['M_max_threaded_Nmm']} ({e['M_max_threaded_max_Nmm']}) | {', '.join(mv) or 'none'} |")
    xe = out["extrapolation"]
    L += ["", "Boundary extrapolation (`jfwd_patch_extrap_nodes_v352.json`): " + "; ".join(
        f"{k} max {v['max_extrap_mm']} mm, {v['n_gt_0p01mm']} nodes > 0.01 mm, nearest {v['min_distance_to_ball_centre_mm']} mm from a Ball centre, "
        f"on the flat region: {v['any_on_flat_region']}" for k, v in xe.items()) + ".", "", f"Inputs (sha256/16): {json.dumps(files)}", "",
          "Nothing here is physical approval."]
    OUT_MD.write_text("\n".join(L) + "\n")
    print("\n".join(L[:14]))
    print(OUT, sha16(OUT), OUT_MD, sha16(OUT_MD))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v5")
