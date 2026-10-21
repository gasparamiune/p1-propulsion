"""(b1) s6 / s9 mesh correction, 240 (9)(v) (FEA3D-2, 2026-10-21; DERIVED from the posts, no solve).
Rule 240 (9)(v): "(b1) runs on s9 at mu 0.2 with (b2') s9 mu 0 as the mesh check (within 5 % on the 54 lines, the screw sections, the
seat force and footprint and the hole bearing; else (b1) is corrected by the s6 / s9 ratio at mu 0 and tagged DERIVED)".  Lead 15:37Z
(R3): (b2') judged by the 5 % rule at PRELOAD / FA1S; its soak states join the envelope.  The judge (jfwd_patch_judge.py, file
jfwd/runs/seat_s9L12_mu0/judge_seat_s6L12_mu0.json) FAILS at PRELOAD and FA1S, so the correction applies.
Meshes (jfwd/mesh_s6.json, mesh_s9.json, seat_s6L12.json, seat_s9L12.json; PROGRESS 11:12Z MESHES): s6 is the FINER break mesh (h_brk 0.08
mm, transition 0.6; L12 patch 107,611 nodes, TC-01 28,562 tets), s9 the coarser one (h_brk 0.15 / 0.3; L12 patch 60,812 nodes, TC-01
15,398 tets), built cheap for the friction run.  r = PmPb(s6) / PmPb(s9) > 1 means the P+Q rises with refinement.
RULING (lead 2026-10-21T01:30:18Z (5)): C1 ADOPTED: for each line and each state, the s6 / s9 PmPb ratio at mu 0 ((b2) / (b2'), both in
the physical order PRELOAD > SOAK52 > SOAK > SOAK70 > FA1S, as (b1)) multiplies (b1)'s line stresses, FLOORED at 1.00 (no line less
severe); the (b1) repeats SOAK_rep / SOAK52_rep take their state's ratio [ASSUMED]; MS = (1 + MS_b1) / max(1, r) - 1 (2 Fty(T) is (b1)'s
own); DERIVED.  C2 (per line, max(r_PRELOAD, r_FA1S) at every state) is a SENSITIVITY for the convergence section, not cells.  C0 = as
solved (record).  Resultants (N, V, M, seat window, HEAD) are NOT corrected (as solved); beside (b1)'s resultants the mu 0 s6 / s9
resultant ratio of each state is quoted as a disclosure, and any governing resultant (N max, window min, M max) that the ratio would make
more than 5 % more severe is FLAGGED (01:30:18Z (5)).
(5b): the seat-line P+Q is NOT shown converged (nothing finer than s6).  Two-mesh extrapolated estimate on the governing line d+6.051 z'0,
per state, at ASSUMED orders p = 1 and p = 2 with the h ratio 0.15 / 0.08 = 1.875 [ESTIMATE]: f_ext = f6 + (f6 - f9) / (h_r^p - 1), factor
= f_ext / f6, applied to the band anchors (the envelope seat-line PmPb max per state, C1 included) as information.
usage: jfwd_b1_meshcorr_v352.py -> results/v352/jfwd_b1_meshcorr_v352.json + results/v352/tables/jfwd_b1_meshcorr_v352.md"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
RES = Path("/home/claude/work/fea3d/results/v352")
B2, B2P, B1 = "seat_s6L12_mu0", "seat_s9L12_mu0", "seat_s9L12_mu02A"
ENV = RES / "jfwd_soak_envelope_v352_v4.json"
STATES = ["PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S"]
B1_STEPS = {"PRELOAD": ["PRELOAD"], "SOAK52": ["SOAK52", "SOAK52_rep"], "SOAK": ["SOAK", "SOAK_rep"], "SOAK70": ["SOAK70"], "FA1S": ["FA1S"]}
JUDGED = ("PRELOAD", "FA1S")
GOV = "d+6.051_z+0.0"
H_R = 0.15 / 0.08                     # s9 / s6 h_brk
RULING = "lead 2026-10-21T01:30:18Z (5): C1 ADOPTED, ratio floored at 1.00, repeats take their state's ratio [ASSUMED]; DERIVED"
FLAG_TOL = 0.05


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def lines(job, step):
    c = json.loads((RUNS / job / "compare.json").read_text())
    out = {}
    for row in c["steps"][step]["relax_seat_lines_cmp"]:
        if row["family"] == "hole_edge":
            continue
        out[f"d{row['delta_deg']:+.3f}_z{row['z_prime_mm']:+.1f}"] = (row["PmPb_patch"], row["MS_PQ_patch"])
    return out


def resultants(job, step):
    sh = json.loads((RUNS / job / "shank.json").read_text())["steps"][step]
    sf = json.loads((RUNS / job / "seatforce.json").read_text())["steps"][step]
    m286 = [x["M"] for x in sh["sections"] if abs(x["x"] - 28.6) < 0.051]
    return {"N_plane_N": round(abs(sh["plane_exact"]["N_N"]), 1), "V_plane_N": round(abs(sh["plane_exact"]["V_N"]), 1),
            "HEAD_N": round(abs(sf["screw"]["HEAD_on_screw_along_n_N"]), 1),
            "seat_window_N": sf["seat_TC02"]["footprint"].get("window_daz9_zp9_N"),
            "M_x28.6_Nmm": round(abs(m286[0]), 1) if m286 else None, "M_max_threaded_Nmm": round(abs((sh.get("M_max_threaded") or {}).get("M", 0.0)), 1)}


def fm(v, n=3):
    return f"{v:+.{n}f}" if isinstance(v, (int, float)) else "n/a"


def main():
    env = json.loads(ENV.read_text())
    L = {st: {"b2": lines(B2, st), "b2p": lines(B2P, st)} for st in STATES}
    ratio = {st: {k: L[st]["b2"][k][0] / L[st]["b2p"][k][0] for k in L[st]["b2"] if k in L[st]["b2p"] and L[st]["b2p"][k][0] > 0} for st in STATES}
    keys = sorted(set.intersection(*[set(ratio[st]) for st in STATES]))
    r_c2 = {k: max(ratio[s][k] for s in JUDGED) for k in keys}
    out = {"doc": __doc__.split("usage:")[0].strip(), "ruling": RULING, "status": "C1 ADOPTED (lead 01:30:18Z (5)); C2 sensitivity; C0 record",
           "inputs_sha16": {f"{j}/{f}": sha16(RUNS / j / f) for j in (B2, B2P, B1) for f in ("compare.json", "shank.json", "seatforce.json")},
           "judge": {"file": "jfwd/runs/seat_s9L12_mu0/judge_seat_s6L12_mu0.json", "sha16": sha16(RUNS / B2P / "judge_seat_s6L12_mu0.json")},
           "envelope_v4": {"file": "results/v352/jfwd_soak_envelope_v352_v4.json", "sha16": sha16(ENV)},
           "meshes": {"s6": {"h_brk_mm": 0.08, "transition_mm": 0.6, "L12_patch_nodes": 107611, "TC01_tets": 28562, "role": "finer (b2)"},
                      "s9": {"h_brk_mm": 0.15, "transition_mm": 0.3, "L12_patch_nodes": 60812, "TC01_tets": 15398, "role": "coarser (b2') / (b1)"}},
           "n_lines": len(keys), "ratio_s6_over_s9": {}, "states": {}, "extrapolation_governing_line": {}, "resultant_flags": []}
    for st in STATES:
        out["ratio_s6_over_s9"][st] = {"governing_line": round(ratio[st][GOV], 4), "min": round(min(ratio[st][k] for k in keys), 4),
                                       "max": round(max(ratio[st][k] for k in keys), 4), "n_gt_1": sum(1 for k in keys if ratio[st][k] > 1),
                                       "n_floored": sum(1 for k in keys if ratio[st][k] < 1)}
    # resultants of every envelope instance (v4) + (b2'), for the flags
    inst_res = {}
    for st in STATES:
        s4 = env["states"][st]
        inst_res[st] = {lab: {"N_plane_N": s4["N_plane_N"].get(lab), "M_x28.6_Nmm": s4["M_x28.6_Nmm"].get(lab),
                              "M_max_threaded_Nmm": (s4["M_max_threaded_Nmm"].get(lab) or [None])[0], "seat_window_N": s4["seat_window_N"].get(lab)}
                        for lab in s4["N_plane_N"]}
        r = resultants(B2P, st)
        inst_res[st]["(b2')"] = {q: r[q] for q in ("N_plane_N", "M_x28.6_Nmm", "M_max_threaded_Nmm", "seat_window_N")}
    for st in STATES:
        e4 = env["states"][st]["envelope"]
        gl = env["states"][st]["lines"][GOV]
        r2, r2p = resultants(B2, st), resultants(B2P, st)
        rr = {q: (round(r2[q] / r2p[q], 4) if isinstance(r2[q], (int, float)) and isinstance(r2p[q], (int, float)) and r2p[q] else None) for q in r2}
        rec = {"ratio_per_line": {k: round(ratio[st][k], 4) for k in keys}, "resultant_ratio_b2_over_b2p": rr,
               "resultants_b2": r2, "resultants_b2p": r2p, "instances": {}}
        for sk in B1_STEPS[st]:
            b1 = lines(B1, sk)
            rf = {k: max(1.0, ratio[st][k]) for k in keys}
            c0 = {k: b1[k][1] for k in keys}
            c1 = {k: round((1 + b1[k][1]) / rf[k] - 1, 3) for k in keys}
            c2 = {k: round((1 + b1[k][1]) / r_c2[k] - 1, 3) for k in keys}
            pm1 = {k: round(b1[k][0] * rf[k], 1) for k in keys}
            lab = "(b1)" if not sk.endswith("_rep") else "(b1) rep"
            inst = {"step": sk, "label": lab, "ratio_floored": {k: round(rf[k], 4) for k in keys},
                    "C0_MS": c0, "C0_PmPb_MPa": {k: b1[k][0] for k in keys}, "C1_MS": c1, "C1_PmPb_MPa": pm1, "C2_MS_sensitivity": c2,
                    "min": {c: [min(d.values()), min(d, key=d.get)] for c, d in (("C0", c0), ("C1", c1), ("C2", c2))},
                    "governing_line": {"PmPb_b1_MPa": b1[GOV][0], "MS_b1": b1[GOV][1], "ratio": round(ratio[st][GOV], 4), "ratio_floored": round(rf[GOV], 4),
                                       "C1_PmPb_MPa": pm1[GOV], "C1_MS": c1[GOV], "C2_PmPb_MPa": round(b1[GOV][0] * r_c2[GOV], 1), "C2_MS": c2[GOV]},
                    "lines_below_v4_env": {c: sorted(k for k in keys if d[k] < env["states"][st]["lines"][k]["MS_PQ_env"] - 1e-9) for c, d in (("C1", c1), ("C2", c2))},
                    "resultants_as_solved": resultants(B1, sk)}
            rec["instances"][sk] = inst
        for c in ("C1", "C2"):
            worst = min(((inst[f"{c}_MS" if c == "C1" else "C2_MS_sensitivity"][k], k, sk) for sk, inst in rec["instances"].items() for k in keys))
            rec[f"env_with_{c}"] = {"min_MS": worst[0], "line": worst[1], "instance": worst[2], "v4_min_MS": e4["lines_min_MS_PQ"][0], "v4_from": e4["lines_min_MS_PQ"][1],
                                    "state_min_moves": worst[0] < e4["lines_min_MS_PQ"][0] - 1e-9,
                                    "n_lines_below_v4_env": len(set().union(*[set(inst["lines_below_v4_env"][c]) for inst in rec["instances"].values()]))}
        # governing-line band anchor with C1: max over the v4 instances (+ (b2')) with (b1) replaced by its C1 value
        pm = dict(gl["PmPb_MPa"])
        ms = dict(gl["MS_PQ"])
        pm["(b2')"], ms["(b2')"] = L[st]["b2p"][GOV]
        for sk, inst in rec["instances"].items():
            pm[inst["label"]] = inst["governing_line"]["C1_PmPb_MPa"]
            ms[inst["label"]] = inst["governing_line"]["C1_MS"]
        ka = max(pm, key=pm.get)
        km = min(ms, key=ms.get)
        f6, f9 = L[st]["b2"][GOV][0], L[st]["b2p"][GOV][0]
        ex = {"f_s9_MPa": f9, "f_s6_MPa": f6, "MS_s6": L[st]["b2"][GOV][1], "ratio": round(f6 / f9, 4)}
        for p in (1, 2):
            fac = 1 + (f6 - f9) / (H_R ** p - 1) / f6
            ex[f"p{p}"] = {"factor": round(fac, 4), "f_ext_MPa": round(f6 * fac, 1), "MS_s6_line_ext": round((1 + L[st]["b2"][GOV][1]) / fac - 1, 3),
                           "band_anchor_PmPb_MPa": [pm[ka], ka], "band_anchor_ext_MPa": round(pm[ka] * fac, 1),
                           "band_MS_min": [ms[km], km], "band_MS_min_ext": round((1 + ms[km]) / fac - 1, 3)}
        ex["tag"] = "ESTIMATE (two meshes, observed order ASSUMED p = 1 / p = 2, h ratio 0.15 / 0.08; nothing finer than s6 run)"
        out["extrapolation_governing_line"][st] = ex
        rec["band_anchor_C1"] = {"PmPb_max_MPa": [pm[ka], ka], "MS_min": [ms[km], km]}
        # resultant flags (01:30:18Z (5)): governing N max, window min, M max; (b1) instances scaled by the s6/s9 resultant ratio
        ir = inst_res[st]
        for q, sense in (("N_plane_N", "max"), ("seat_window_N", "min"), ("M_x28.6_Nmm", "max"), ("M_max_threaded_Nmm", "max")):
            vals = {lab: v[q] for lab, v in ir.items() if isinstance(v[q], (int, float))}
            if not vals or rr.get(q) is None:
                continue
            gov = (max if sense == "max" else min)(vals, key=vals.get)
            for sk, inst in rec["instances"].items():
                lab = inst["label"]
                if lab not in vals:
                    continue
                scaled = vals[lab] * rr[q]
                more = (scaled / vals[gov] - 1) if sense == "max" else (1 - scaled / vals[gov])
                is_gov = lab == gov
                if more > FLAG_TOL:
                    out["resultant_flags"].append({"state": st, "quantity": f"{q} {sense}", "instance": lab, "as_solved": vals[lab], "ratio_s6_s9": rr[q],
                                                   "scaled": round(scaled, 1), "envelope_governing": [vals[gov], gov], "governs_now": is_gov,
                                                   "more_severe_than_governing": round(more, 4)})
        out["states"][st] = rec
    # ---- md
    md = ["# (b1) s6 / s9 mesh correction, 240 (9)(v): C1 ADOPTED (lead 2026-10-21T01:30:18Z (5)); DERIVED", "",
          f"(b2') `{B2P}` FAILS the 5 % rule against (b2) `{B2}` at PRELOAD and FA1S (judge `judge_seat_s6L12_mu0.json` {out['judge']['sha16']}). "
          f"s6 is the finer break mesh (h_brk 0.08 mm; L12 patch 107,611 nodes), s9 the coarser (h_brk 0.15 mm; 60,812 nodes). "
          f"C1: (b1) line stresses x max(1, r), r = PmPb(b2) / PmPb(b2') per line and state; repeats take their state's ratio [ASSUMED]. "
          f"C2 = sensitivity only. Envelope v4 `{out['envelope_v4']['sha16']}` for comparison. [SIM inputs; DERIVED values; extrapolation ESTIMATE]", "",
          "## s6 / s9 PmPb ratio at mu 0, per state (54 lines)", "", "| state | governing line d+6.051 z'0 | min | max | lines r > 1 | lines floored (r < 1) |", "|---|---|---|---|---|---|"]
    for st in STATES:
        q = out["ratio_s6_over_s9"][st]
        md.append(f"| {st} | {q['governing_line']:.4f} | {q['min']:.4f} | {q['max']:.4f} | {q['n_gt_1']} / {len(keys)} | {q['n_floored']} |")
    md += ["", "## (b1) seat lines: as solved (C0), C1 (ADOPTED), C2 (sensitivity)", "",
           "| state | instance | C0 min MS (line) | C1 min MS (line) | C1 governing line PmPb MPa (MS) | C2 min MS (sensitivity) | v4 envelope min MS (from) |",
           "|---|---|---|---|---|---|---|"]
    for st in STATES:
        e4 = env["states"][st]["envelope"]
        for sk, inst in out["states"][st]["instances"].items():
            m, g = inst["min"], inst["governing_line"]
            md.append(f"| {st} | {inst['label']} | {fm(m['C0'][0])} ({m['C0'][1]}) | {fm(m['C1'][0])} ({m['C1'][1]}) | {g['C1_PmPb_MPa']:.1f} ({fm(g['C1_MS'])}) | "
                      f"{fm(m['C2'][0])} ({m['C2'][1]}) | {fm(e4['lines_min_MS_PQ'][0])} ({e4['lines_min_MS_PQ'][1]}) |")
    md += ["", "## Envelope state minimum with (b1) at C1 (and the C2 sensitivity)", "",
           "| state | v4 min MS (from) | with C1: min (line, instance) | C1 lines below v4 | C2 sensitivity: min | band anchor with C1: PmPb max (from) / MS min (from) |", "|---|---|---|---|---|---|"]
    for st in STATES:
        a, b, ba = out["states"][st]["env_with_C1"], out["states"][st]["env_with_C2"], out["states"][st]["band_anchor_C1"]
        md.append(f"| {st} | {fm(a['v4_min_MS'])} ({a['v4_from']}) | {fm(min(a['min_MS'], a['v4_min_MS']))} ({a['line'] if a['state_min_moves'] else a['v4_from']}"
                  f"{', ' + a['instance'] + ' C1; moves' if a['state_min_moves'] else '; v4 stands'}) | {a['n_lines_below_v4_env']} | "
                  f"{fm(min(b['min_MS'], b['v4_min_MS']))}{' (moves)' if b['state_min_moves'] else ''} | {ba['PmPb_max_MPa'][0]:.1f} ({ba['PmPb_max_MPa'][1]}) / "
                  f"{fm(ba['MS_min'][0])} ({ba['MS_min'][1]}) |")
    md += ["", "## Not shown converged (5b): two-mesh extrapolation on the governing line d+6.051 z'0 [ESTIMATE; p ASSUMED; h ratio 0.15 / 0.08]", "",
           "| state | s9 PmPb | s6 PmPb (as found) | s6 / s9 | p = 1 factor | p = 1 PmPb (MS on (b2)) | p = 2 factor | p = 2 PmPb (MS on (b2)) | band anchor (from) | anchor x p1 / x p2 | band MS min (from) -> p1 / p2 |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for st in STATES:
        ex = out["extrapolation_governing_line"][st]
        p1, p2 = ex["p1"], ex["p2"]
        md.append(f"| {st} | {ex['f_s9_MPa']:.1f} | {ex['f_s6_MPa']:.1f} ({fm(ex['MS_s6'])}) | {ex['ratio']:.4f} | {p1['factor']:.4f} | {p1['f_ext_MPa']:.1f} ({fm(p1['MS_s6_line_ext'])}) | "
                  f"{p2['factor']:.4f} | {p2['f_ext_MPa']:.1f} ({fm(p2['MS_s6_line_ext'])}) | {p1['band_anchor_PmPb_MPa'][0]:.1f} ({p1['band_anchor_PmPb_MPa'][1]}) | "
                  f"{p1['band_anchor_ext_MPa']:.1f} / {p2['band_anchor_ext_MPa']:.1f} | {fm(p1['band_MS_min'][0])} ({p1['band_MS_min'][1]}) -> {fm(p1['band_MS_min_ext'])} / {fm(p2['band_MS_min_ext'])} |")
    md += ["", "## (b1) resultants as solved, with the mu 0 s6 / s9 resultant ratio per state (disclosure; not corrected)", "",
           "| state | instance | N plane N | V plane N | seat window N | M x' 28.6 N mm | M_max threaded N mm | ratio N / V / window / M28.6 / M_max thr |", "|---|---|---|---|---|---|---|---|"]
    f3 = lambda v: f"{v:.3f}" if isinstance(v, (int, float)) else "n/a"
    for st in STATES:
        rr = out["states"][st]["resultant_ratio_b2_over_b2p"]
        for sk, inst in out["states"][st]["instances"].items():
            r = inst["resultants_as_solved"]
            md.append(f"| {st} | {inst['label']} | {r['N_plane_N']:.1f} | {r['V_plane_N']:.1f} | {r['seat_window_N']:.1f} | {r['M_x28.6_Nmm']:.1f} | {r['M_max_threaded_Nmm']:.1f} | "
                      f"{f3(rr['N_plane_N'])} / {f3(rr['V_plane_N'])} / {f3(rr['seat_window_N'])} / {f3(rr['M_x28.6_Nmm'])} / {f3(rr['M_max_threaded_Nmm'])} |")
    md += ["", "## Flags: governing resultants the s6 / s9 ratio would make more than 5 % more severe (01:30:18Z (5))", ""]
    if out["resultant_flags"]:
        md += ["| state | quantity | (b1) instance | as solved | ratio | scaled | envelope governing (from) | (b1) governs now | more severe by |", "|---|---|---|---|---|---|---|---|---|"]
        for fl in out["resultant_flags"]:
            md.append(f"| {fl['state']} | {fl['quantity']} | {fl['instance']} | {fl['as_solved']} | {fl['ratio_s6_s9']:.3f} | {fl['scaled']} | {fl['envelope_governing'][0]} ({fl['envelope_governing'][1]}) | "
                      f"{'yes' if fl['governs_now'] else 'no'} | {100 * fl['more_severe_than_governing']:.1f} % |")
    else:
        md.append("none")
    oj, om = RES / "jfwd_b1_meshcorr_v352.json", RES / "tables" / "jfwd_b1_meshcorr_v352.md"
    oj.write_text(json.dumps(out, indent=1))
    om.write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print("wrote", oj, sha16(oj), om, sha16(om))


if __name__ == "__main__":
    main()
