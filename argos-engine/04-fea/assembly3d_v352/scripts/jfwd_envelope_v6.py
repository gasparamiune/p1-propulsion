"""J-FWD soak envelope over the solved histories (fea3d 2026-10-20 ~12:20Z; lead 11:41Z ruling (3)); v3 2026-10-20 ~16:10Z (lead 15:37Z
(R1): "adopt the worst of sharp + (b2) over every computed instance").
BASIS (lead 15:37Z, for every quote): "worst of the computed histories and edge forms (sharp, R0.2); the contact solution depends on
the predecessor state, so this is the worst computed instance, not a proven bound".  The drawing allows R0.1-R0.2 at the bore-side
hole edge, which lies between the two models.  Mechanical re-maps its IN718 rows on this file.
v4 (2026-10-21, lead 15:37Z (R3)): v3 + the (b1) instances seat_s9L12_mu02A (s9 R0.2, mu 0.2, physical order + SOAK / SOAK52 repeats).
v4 ADOPTED by the lead 2026-10-21T00:39:30Z (1) (supersedes v3; "if (b2') or js5b raises any quantity, the envelope grows again (v5 =
final)").
v5 (FEA3D-2, 2026-10-21 after (b2') posted 01:18:57Z): v4 + the (b2') instances seat_s9L12_mu0 (s9 R0.2, mu 0, physical order PRELOAD >
SOAK52 > SOAK > SOAK70 > FA1S, no repeats; lead 15:37Z (R3): its soak states join the envelope).  (b2') is the s9 mesh check of (b1)
against (b2) on s6 (240 (9)(v)); its 5 % result is in jfwd/runs/seat_s9L12_mu0/judge_seat_s6L12_mu0.json: FAIL at PRELOAD and FA1S.
C1 (lead 2026-10-21T01:30:18Z (3) / (5)): (b1)'s 54 seat-line stresses enter at their C1 values: PmPb x max(1, r), r = PmPb(b2) /
PmPb(b2') per line and state at mu 0, FLOORED at 1.00, the repeats take their state's ratio [ASSUMED]; MS = (1 + MS_b1) / max(1, r) - 1;
DERIVED; read from results/v352/jfwd_b1_meshcorr_v352.json (scripts/jfwd_b1_meshcorr_v352.py); the as-solved s9 values are kept beside
them per line.  (b1)'s resultants (N, M, window) enter AS SOLVED (not corrected; the more severe of s6 and s9 where both meshes exist is
what the envelope takes); the mu 0 s6 / s9 resultant ratio per state and the > 5 % flags are quoted from the meshcorr file (disclosure).
(B) (lead 2026-10-21T02:01:34Z (B)): the mu 0 M ratios are NOT applied to (b1)'s friction-driven moments; Mechanical's screw fibre and
LCF rows quote M as solved, with M x 1.404 (PRELOAD) and x 1.476 (SOAK), the mu 0 ratios of M_max on the thread, as information.
js5b (FEA3D-2, after js5b ended 2026-10-21T03:18:21Z): js5b_in718_mu0_T3750_g078_cf (s5 global sector, sharp, mu 0, IN718 screw) has
no seat patch (no compare.json, no seat lines); of the envelope states it solves PRELOAD only, and its PRELOAD N, window and M lie inside
the v5 PRELOAD envelope (record 'js5b_check' in the output, from its shank.json / seatforce.json): js5b raises no envelope quantity, so
v5 is the final envelope at the js5b end (lead 01:30:18Z (3), 02:01:34Z (E)), unless cD moves a quantity (then v6 supersedes it).
v6 (FEA3D-2, 2026-10-21 after cD seat_sDL12_mu0 ended 05:11:29Z; lead 02:01:34Z (E), 03:30:46Z (3): "v6 if cD moves a quantity"):
v5 + cD's RESULTANTS as solved (N at the shear plane, M at x' 28.6, M max on the threaded length, seat window) as the instance "(cD)"
(s6 + two Ball fields h 0.04 mm at the governing-line ends, FINAL TC-01 fcb3b5b93bebdb01 with the d11.2 flats, mu 0, physical order
PRELOAD > SOAK52 > SOAK > SOAK70 > FA1S, no repeats), on the worst-of basis above, as (b2') entered v5.  cD's SEAT LINES are NOT an
instance: they enter only through the lead 02:01:34Z (C) rule, which keeps s6 + C1 in every state (governing line d+6.051 z'0: cD lower
than s6 by more than 5 % at PRELOAD / SOAK52, within 5 % at SOAK / SOAK70 / FA1S; no line above 1.05 x s6); they are recorded in
'cD_check' with the per-state verdict, read from results/v352/jfwd_cD_result_v352.json (scripts/jfwd_cD_result_v352.py).  'v5_to_v6'
lists every envelope quantity that cD moves (cross-check of the delta file).  Recorded for Mechanical (lead 2026-10-21T05:17:36Z (3)),
outside envelope{}: per instance the M max on the threaded length and 'M_max_shank_in_TC01_Nmm', the M max over the screw shank inside
TC-01 (Mechanical's v7 input M_max: SOAK70 (b2) 3415.2 N mm at x' 30.5; cD 3438.9).
Files: v6 -> results/v352/jfwd_soak_envelope_v352_v6.json (FINAL); v5 results/v352/jfwd_soak_envelope_v352_v5.json ef22b59cf2413b46
(ACCEPTED 03:30:46Z (3) as final unless cD moves a quantity) is superseded by v6 and kept (scripts/jfwd_envelope_v5.py 18886bbde22e1493,
not rewritten); v4 results/v352/jfwd_soak_envelope_v352_v4.json 9d9fd8ee991f9887 (ADOPTED 00:39:30Z (1)) is superseded by v5.  Records (kept, not rewritten):
jfwd_soak_envelope_v352_v3.json 0872de4ea7e3601d (v3), jfwd_soak_envelope_v352.json 336568296bdb896f (v2, sharp only: js5 / (a) / (a') /
(a''), adopted 13:14Z) and jfwd_soak_envelope_v352_v1.json 1d970741cb95a885 (v1: js5 / (a) / (a')).
Edge forms: sharp = js5 and the s5 patches; R0.2 = (b2) seat_s6L12_mu0 (s6 mesh, R0.2 drawing-maximum break at the TC-01 hole-to-bore
edge + 0.1 x 45 at the flat), with its repeat instances SOAK_rep (state SOAK, after FA1S) and SOAK52_rep (state SOAK52, after
SOAK_rep) as separate instances "(b2) rep".

Ruling: until a history-robust model exists, the sharp-edge soak quantities are the WORST over the solved histories, per state and per
quantity: highest screw tension N, lowest seat window force, lowest MS (P+Q <= 2 Fty(T)) on each of the 54 seat lines.  The A4-80 screw
rows are moot (screw = IN718 M5, lead 11:25Z (3)); the envelope feeds Mechanical's IN718 mapping and its relaxation calibration.
Runs (all mu 0, 3750 N, fit 0.078, sharp TC-01 hole edge, spot-face TC-01):
  js5_mu0_T3750_g078   global one-sector model s5; order PRELOAD > SOAK70 > FA1S > SOAK > SOAK52 (SOAK took a second, zero-size increment)
  seat_s5L8_mu0  (a)   seat patch L 8 on js5's field; physical order PRELOAD > SOAK52 > SOAK > SOAK70 > FA1S, SEAT d1 0.015
  seat_s5L8_mu0_go (a')  same patch, js5's order and SEAT (d1 0.05)
  seat_s5L12_mu0_go (a'') patch L 12 (full sector width), js5's order and SEAT        [included when its posts exist]
Quantities (SIM, exact nodal-force resultants and SCL lines of the posts; DERIVED envelope):
  N        screw tension at the shear plane (jfwd_shank plane_exact, the thread-tie resultant); A4-80 tension MS = kT Rp A_s / N - 1 with
           kT Rp from the js5 post at the step's shank temperature (A_s 14.18 mm2) - information
  M        screw bending at x' 28.6 (shear plane, thread entry) and the maximum on the threaded length (secondary at the soaks, 10:14Z)
  window   seat normal force on TC-02 summed over |daz| <= 9 deg, |z'| <= 9 mm (lead 11:41Z (1); box-edge artefact excluded)
  lines    the 54 seat SCL lines of jfwd_relax (P+Q MS = 2 Fty(T) / PmPb - 1); js5 values from the patch compare files' global columns
usage: jfwd_envelope_v6.py -> results/v352/jfwd_soak_envelope_v352_v6.json (the v1 / v2 / v3 / v4 / v5 files are not written)"""
from __future__ import annotations
import json
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
MESHCORR = Path("/home/claude/work/fea3d/results/v352/jfwd_b1_meshcorr_v352.json")   # C1 (lead 01:30:18Z (5)); DERIVED
B1 = "seat_s9L12_mu02A"
JS5B = "js5b_in718_mu0_T3750_g078_cf"      # checked against the envelope (js5b_check), not an instance
CD = "seat_sDL12_mu0"                      # cD: resultants are an instance; seat lines per the 02:01:34Z (C) rule only (cD_check)
CDRES = Path("/home/claude/work/fea3d/results/v352/jfwd_cD_result_v352.json")      # the (C) rule per state (scripts/jfwd_cD_result_v352.py)
V5 = Path("/home/claude/work/fea3d/results/v352/jfwd_soak_envelope_v352_v5.json")   # superseded record (read only, for v5_to_v6)
OUT = Path("/home/claude/work/fea3d/results/v352/jfwd_soak_envelope_v352_v6.json")  # v6 FINAL; v5 / v4 / v3 / v2 / v1 files kept as records
SUPERSEDES = {"jfwd_soak_envelope_v352_v5.json": "ef22b59cf2413b46 (v5, ACCEPTED lead 2026-10-21T03:30:46Z (3) as final unless cD moves a quantity; kept, not rewritten)",
              "jfwd_soak_envelope_v352_v4.json": "9d9fd8ee991f9887 (v4, ADOPTED lead 2026-10-21T00:39:30Z (1), superseded by v5; kept, not rewritten)",
              "jfwd_soak_envelope_v352_v3.json": "0872de4ea7e3601d (v3, adopted lead 15:37Z (R1), superseded by v4; kept, not rewritten)",
              "jfwd_soak_envelope_v352.json": "336568296bdb896f (v2, sharp only, adopted 13:14Z; superseded record)",
              "jfwd_soak_envelope_v352_v1.json": "1d970741cb95a885 (v1; superseded record)"}
BASIS = ("worst of the computed histories and edge forms (sharp, R0.2); the contact solution depends on the predecessor state, so this "
         "is the worst computed instance, not a proven bound")
GLOBAL = "js5_mu0_T3750_g078"
PATCHES = ["seat_s5L8_mu0", "seat_s5L8_mu0_go", "seat_s5L12_mu0_go", "seat_s6L12_mu0", "seat_s9L12_mu02A", "seat_s9L12_mu0"]
LABEL = {GLOBAL: "js5", "seat_s5L8_mu0": "(a)", "seat_s5L8_mu0_go": "(a')", "seat_s5L12_mu0_go": "(a'')", "seat_s6L12_mu0": "(b2)", "seat_s9L12_mu02A": "(b1)",
         "seat_s9L12_mu0": "(b2')", CD: "(cD)"}
EDGE = {GLOBAL: "sharp", "seat_s5L8_mu0": "sharp", "seat_s5L8_mu0_go": "sharp", "seat_s5L12_mu0_go": "sharp", "seat_s6L12_mu0": "R0.2",
        "seat_s9L12_mu02A": "R0.2 (s9, mu 0.2; seat lines at C1 = x max(1, s6/s9), DERIVED; resultants as solved)",
        "seat_s9L12_mu0": "R0.2 (s9, mu 0)",
        CD: ("R0.2 (s6 + Ball h 0.04 mm at the governing-line ends, FINAL TC-01 d11.2 flats, mu 0; resultants as solved; seat lines per "
             "the lead 02:01:34Z (C) rule: s6 + C1 stand, cD's lines in cD_check, not an instance)")}
REPEATS = {"seat_s6L12_mu0": {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"}, "seat_s9L12_mu02A": {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"}}    # extra instances of a state in the same run
STATES = ["PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S"]
A_S = 14.18


def jl(p):
    return json.loads(p.read_text()) if p.exists() else None


def main():
    post = jl(RUNS / GLOBAL / "post.json")
    runs = [GLOBAL] + [p for p in PATCHES if (RUNS / p / "compare.json").exists() and (RUNS / p / "shank.json").exists()]
    assert (RUNS / CD / "DONE").exists() and (RUNS / CD / "shank.json").exists() and (RUNS / CD / "seatforce.json").exists(), "cD posts missing"
    runs.append(CD)
    out = {"doc": __doc__.split("usage:")[0].strip(), "version": "v6",
           "status": ("FINAL (lead 2026-10-21T02:01:34Z (E), 03:30:46Z (3): v6 = v5 + cD's resultants as solved, because cD moves envelope "
                      "quantities (v5_to_v6); seat lines: the 02:01:34Z (C) rule keeps s6 + C1 in every state (cD_check)); supersedes v5 "
                      "ef22b59cf2413b46 (ACCEPTED 03:30:46Z (3) as final unless cD moves a quantity)"), "basis": BASIS,
           "supersedes": SUPERSEDES, "runs": {LABEL[r]: r for r in runs}, "edge_form": {LABEL[r]: EDGE[r] for r in runs},
           "repeat_instances": {f"{LABEL[r]} rep": {st: k for st, k in REPEATS[r].items()} for r in runs if r in REPEATS},
           "inputs_sha16": {}, "states": {}}
    import hashlib
    mc = json.loads(MESHCORR.read_text())
    out["inputs_sha16"]["results/v352/jfwd_b1_meshcorr_v352.json"] = hashlib.sha256(MESHCORR.read_bytes()).hexdigest()[:16]
    out["mesh_correction_b1"] = {"rule": mc["ruling"], "file": "results/v352/jfwd_b1_meshcorr_v352.json",
                                 "ratio_s6_over_s9_lines": mc["ratio_s6_over_s9"],
                                 "resultant_ratio_s6_over_s9_mu0": {st: mc["states"][st]["resultant_ratio_b2_over_b2p"] for st in mc["states"]},
                                 "resultant_flags_gt_5pct": mc["resultant_flags"],
                                 "note": ("seat lines of (b1) at C1 (DERIVED); (b1) resultants as solved (not corrected); the flags are a disclosure "
                                          "(the M ratios come from small mu 0 moments), not applied"),
                                 "ruling_B": ("lead 2026-10-21T02:01:34Z (B): the mu 0 M ratios are NOT applied to (b1)'s friction-driven moments; "
                                              "Mechanical's screw fibre and LCF rows quote M as solved, with M x 1.404 (PRELOAD) and x 1.476 (SOAK) "
                                              "(mu 0 ratios of M_max on the thread) as information")}
    for r in runs:
        for fn in ("shank.json", "seatforce.json", "compare.json", "post.json"):
            fp = RUNS / r / fn
            if fp.exists():
                out["inputs_sha16"][f"{r}/{fn}"] = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
    for st in STATES:
        rec = {"N_plane_N": {}, "M_x28.6_Nmm": {}, "M_max_threaded_Nmm": {}, "M_max_shank_in_TC01_Nmm": {}, "seat_window_N": {},
               "after": {}, "lines": {}}
        inst = []                                   # (run, step key in that run, instance label)
        for r in runs:
            inst.append((r, st, LABEL[r]))
            if st in REPEATS.get(r, {}):
                inst.append((r, REPEATS[r][st], f"{LABEL[r]} rep"))
        for r, sk, lab in inst:
            sh = jl(RUNS / r / "shank.json")
            sf = jl(RUNS / r / "seatforce.json")
            meta = jl(RUNS / r / "meta.json") or {}
            if sh is None or sk not in sh["steps"]:
                continue
            s = sh["steps"][sk]
            rec["N_plane_N"][lab] = round(abs(s["plane_exact"]["N_N"]), 1)
            m286 = [x["M"] for x in s["sections"] if abs(x["x"] - 28.6) < 0.051]
            rec["M_x28.6_Nmm"][lab] = round(abs(m286[0]), 1) if m286 else None
            mt = s.get("M_max_threaded") or {}
            rec["M_max_threaded_Nmm"][lab] = [round(abs(mt.get("M", 0.0)), 1), mt.get("x")]
            ms = s.get("M_max_shank_in_TC01") or {}
            rec["M_max_shank_in_TC01_Nmm"][lab] = [round(abs(ms.get("M", 0.0)), 1), ms.get("x")] if ms else None
            if sf and sk in sf["steps"]:
                rec["seat_window_N"][lab] = sf["steps"][sk]["seat_TC02"]["footprint"].get("window_daz9_zp9_N")
            aft = (meta.get("step_after") or {}).get(sk)
            if aft is None and meta.get("steps"):
                seq = meta["steps"]
                aft = seq[seq.index(sk) - 1] if sk in seq and seq.index(sk) > 0 else None
            rec["after"][lab] = aft
        # 54 lines: patch values per run, js5 from the first compare file
        lines = {}
        for r, sk, lab in inst:
            if r in (GLOBAL, CD):                   # cD's seat lines: the (C) rule only (cD_check), not an instance
                continue
            cmpj = jl(RUNS / r / "compare.json")
            if cmpj is None or sk not in cmpj["steps"]:
                continue
            for row in cmpj["steps"][sk]["relax_seat_lines_cmp"]:
                if row["family"] == "hole_edge":
                    continue
                key = f"d{row['delta_deg']:+.3f}_z{row['z_prime_mm']:+.1f}"
                L = lines.setdefault(key, {"delta_deg": row["delta_deg"], "z_prime_mm": row["z_prime_mm"], "t_mm": row.get("t_mm"),
                                           "T_mean_C": row.get("T_mean_C"), "MS_PQ": {}, "PmPb_MPa": {}})
                if r == B1:                       # C1 (lead 01:30:18Z (5)): the s6-level (b1) line stresses; as solved kept beside
                    ci = mc["states"][st]["instances"][sk]
                    L.setdefault("b1_as_solved_s9", {})[lab] = {"MS_PQ": row["MS_PQ_patch"], "PmPb_MPa": row["PmPb_patch"],
                                                                "ratio_floored": ci["ratio_floored"][key]}
                    L["MS_PQ"][lab] = ci["C1_MS"][key]
                    L["PmPb_MPa"][lab] = ci["C1_PmPb_MPa"][key]
                else:
                    L["MS_PQ"][lab] = row["MS_PQ_patch"]
                    L["PmPb_MPa"][lab] = row["PmPb_patch"]
                if EDGE[r] == "sharp":            # js5's own values: the global columns of the sharp patches' compare files (same mesh)
                    L["MS_PQ"].setdefault("js5", row["MS_PQ_global"])
                    L["PmPb_MPa"].setdefault("js5", row["PmPb_global"])
        for key, L in lines.items():
            k_min = min(L["MS_PQ"], key=lambda k: L["MS_PQ"][k])
            L["MS_PQ_env"] = L["MS_PQ"][k_min]
            L["env_from"] = k_min
            L["spread_MS"] = round(max(L["MS_PQ"].values()) - min(L["MS_PQ"].values()), 3)
        rec["lines"] = lines
        # envelope
        env = {}
        if rec["N_plane_N"]:
            kN = max(rec["N_plane_N"], key=lambda k: rec["N_plane_N"][k])
            env["N_max_N"] = [rec["N_plane_N"][kN], kN]
            env["N_min_N"] = [min(rec["N_plane_N"].values()), min(rec["N_plane_N"], key=lambda k: rec["N_plane_N"][k])]
        w = {k: v for k, v in rec["seat_window_N"].items() if v is not None}
        if w:
            kw = min(w, key=lambda k: w[k])
            env["window_min_N"] = [w[kw], kw]
            env["window_max_N"] = [max(w.values()), max(w, key=lambda k: w[k])]
        mm = {k: v for k, v in rec["M_x28.6_Nmm"].items() if v is not None}
        if mm:
            km = max(mm, key=lambda k: mm[k])
            env["M_x28.6_max_Nmm"] = [mm[km], km]
        if lines:
            gov = min(lines.values(), key=lambda L: L["MS_PQ_env"])
            env["lines_min_MS_PQ"] = [gov["MS_PQ_env"], gov["env_from"], gov["delta_deg"], gov["z_prime_mm"]]
            env["n_lines_negative_env"] = sum(1 for L in lines.values() if L["MS_PQ_env"] < 0)
            env["n_lines"] = len(lines)
            env["max_spread_MS"] = max(L["spread_MS"] for L in lines.values())
        if post and st in post["steps"] and "screw_check" in post["steps"][st]:
            sc = post["steps"][st]["screw_check"]
            if sc.get("kT_Rp_MPa"):
                cap = sc["kT_Rp_MPa"] * A_S
                env["A480_kT_Rp_MPa"] = sc["kT_Rp_MPa"]
                env["A480_capacity_N"] = round(cap, 1)
                env["T_shank_C"] = sc.get("T_screw_C")
                if "N_max_N" in env:
                    env["A480_MS_tension_at_N_max_info"] = round(cap / env["N_max_N"][0] - 1, 3)
                    env["A480_MS_tension_per_run_info"] = {k: round(cap / v - 1, 3) for k, v in rec["N_plane_N"].items()}
        rec["envelope"] = env
        out["states"][st] = rec
        print(st, json.dumps(env), "| N", rec["N_plane_N"], "| window", rec["seat_window_N"], "| after", rec["after"], flush=True)
    # cD check (FEA3D-2): the (C) rule per state on the governing line, from the cD result file (read-only)
    cr = json.loads(CDRES.read_text())
    out["inputs_sha16"]["results/v352/jfwd_cD_result_v352.json"] = hashlib.sha256(CDRES.read_bytes()).hexdigest()[:16]
    out["cD_check"] = {"run": CD, "rule": ("lead 2026-10-21T02:01:34Z (C), per state on the governing line d+6.051 z'0: within 5 % of s6 -> "
                                           "s6 and C1 stand; cD higher by more than 5 % -> cD governs, (b1) re-based C1' = cD / s9; "
                                           "cD lower by more than 5 % -> s6 stands, difference quoted"),
                       "file": "results/v352/jfwd_cD_result_v352.json", "lines_entered": False,
                       "states": {st: {"governing_line": cr["states"][st]["governing_line"],
                                       "all_lines_cD_over_s6_min_median_max": cr["states"][st]["all_lines"]["cD_over_s6_min_median_max"],
                                       "n_lines_cD_over_s6_gt_1.05": cr["states"][st]["all_lines"]["n_cD_over_s6_gt_1.05"],
                                       "cD_min_MS_line": cr["states"][st]["all_lines"]["cD_min_MS_line"]} for st in STATES},
                       "extrapolation": cr["extrapolation"]}
    assert all(v["governing_line"]["cD_over_s6"] <= 1.05 for v in out["cD_check"]["states"].values()), "cD > 1.05 x s6: the C1' branch applies"
    v5 = json.loads(V5.read_text())
    mv = []
    for st in STATES:
        a, b = v5["states"][st]["envelope"], out["states"][st]["envelope"]
        for q in ("N_max_N", "N_min_N", "window_min_N", "window_max_N", "M_x28.6_max_Nmm", "lines_min_MS_PQ"):
            if a.get(q) != b.get(q):
                mv.append({"state": st, "quantity": q, "v5": a.get(q), "v6": b.get(q)})
        ma = max((v[0], k) for k, v in v5["states"][st]["M_max_threaded_Nmm"].items() if v and v[0] is not None)
        mb = max((v[0], k) for k, v in out["states"][st]["M_max_threaded_Nmm"].items() if v and v[0] is not None)
        if ma != mb:
            mv.append({"state": st, "quantity": "M_max_threaded_Nmm (per-instance, outside envelope{})", "v5": list(ma), "v6": list(mb)})
        sh_all = {k: v for k, v in out["states"][st]["M_max_shank_in_TC01_Nmm"].items() if v}
        sa = max((v[0], k) for k, v in sh_all.items() if k != "(cD)")      # v5 has no such record: the same instances without cD
        sb = max((v[0], k) for k, v in sh_all.items())
        if sa != sb:
            mv.append({"state": st, "quantity": "M_max_shank_in_TC01_Nmm (per-instance, outside envelope{}; Mechanical's v7 M_max)",
                       "v5_instances": list(sa) + [sh_all[sa[1]][1]], "v6": list(sb) + [sh_all[sb[1]][1]]})
    out["inputs_sha16"]["results/v352/jfwd_soak_envelope_v352_v5.json"] = hashlib.sha256(V5.read_bytes()).hexdigest()[:16]
    out["v5_to_v6"] = mv
    print("v5 -> v6:", json.dumps(mv), flush=True)
    # js5b check (FEA3D-2): js5b's envelope states (PRELOAD only) against this envelope; js5b is not an instance (no seat lines)
    jb = {"run": JS5B, "note": ("js5b solves SEAT, PRELOAD, FA1U, FA1D, LC2U, LC2Y, LC2N, LC2M; of the envelope states only PRELOAD; "
                                "no seat patch, so no seat lines; FA1U / FA1D / LC2 are not envelope states (rows in "
                                "results/v352/jfwd_js5b_rows_v352.json)"), "inputs_sha16": {}, "states": {}, "raises": []}
    shb, sfb = jl(RUNS / JS5B / "shank.json"), jl(RUNS / JS5B / "seatforce.json")
    for fn in ("shank.json", "seatforce.json"):
        fp = RUNS / JS5B / fn
        if fp.exists():
            jb["inputs_sha16"][fn] = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
    for st in STATES:
        if shb is None or st not in shb["steps"] or st not in out["states"]:
            continue
        s = shb["steps"][st]
        m286 = [x["M"] for x in s["sections"] if abs(x["x"] - 28.6) < 0.051]
        mt = s.get("M_max_threaded") or {}
        q = {"N_plane_N": round(abs(s["plane_exact"]["N_N"]), 1), "M_x28.6_Nmm": round(abs(m286[0]), 1) if m286 else None,
             "M_max_threaded_Nmm": [round(abs(mt.get("M", 0.0)), 1), mt.get("x")],
             "seat_window_N": (sfb["steps"][st]["seat_TC02"]["footprint"].get("window_daz9_zp9_N") if sfb and st in sfb["steps"] else None)}
        e = out["states"][st]["envelope"]
        mthr = max((v[0] for v in out["states"][st]["M_max_threaded_Nmm"].values() if v and v[0] is not None), default=None)
        r = []
        if q["N_plane_N"] > e["N_max_N"][0] or q["N_plane_N"] < e["N_min_N"][0]:
            r.append("N")
        if q["seat_window_N"] is not None and (q["seat_window_N"] < e["window_min_N"][0] or q["seat_window_N"] > e["window_max_N"][0]):
            r.append("window")
        if q["M_x28.6_Nmm"] is not None and q["M_x28.6_Nmm"] > e["M_x28.6_max_Nmm"][0]:
            r.append("M_x28.6")
        if mthr is not None and q["M_max_threaded_Nmm"][0] > mthr:
            r.append("M_max_threaded")
        q["outside_envelope"] = r
        jb["states"][st] = q
        jb["raises"] += [f"{st} {x}" for x in r]
    out["js5b_check"] = jb
    print("js5b check", json.dumps(jb["states"]), "raises", jb["raises"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
