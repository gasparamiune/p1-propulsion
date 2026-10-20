"""J-FWD soak envelope over the solved histories (fea3d 2026-10-20 ~12:20Z; lead 11:41Z ruling (3)); v3 2026-10-20 ~16:10Z (lead 15:37Z
(R1): "adopt the worst of sharp + (b2) over every computed instance").
BASIS (lead 15:37Z, for every quote): "worst of the computed histories and edge forms (sharp, R0.2); the contact solution depends on
the predecessor state, so this is the worst computed instance, not a proven bound".  The drawing allows R0.1-R0.2 at the bore-side
hole edge, which lies between the two models.  Mechanical re-maps its IN718 rows on this file.
Files: v3 -> results/v352/jfwd_soak_envelope_v352_v3.json (ADOPTED, lead 15:37Z).  Superseded records (kept, not rewritten):
jfwd_soak_envelope_v352.json 336568296bdb896f (v2, sharp only: js5 / (a) / (a') / (a''), adopted 13:14Z) and
jfwd_soak_envelope_v352_v1.json 1d970741cb95a885 (v1: js5 / (a) / (a')).
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
usage: jfwd_envelope.py -> results/v352/jfwd_soak_envelope_v352_v3.json (the v1 / v2 files are not written)"""
from __future__ import annotations
import json
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
OUT = Path("/home/claude/work/fea3d/results/v352/jfwd_soak_envelope_v352_v3.json")   # v3 (lead 15:37Z (R1)); v2 / v1 files kept as records
SUPERSEDES = {"jfwd_soak_envelope_v352.json": "336568296bdb896f (v2, sharp only, adopted 13:14Z; superseded record)",
              "jfwd_soak_envelope_v352_v1.json": "1d970741cb95a885 (v1; superseded record)"}
BASIS = ("worst of the computed histories and edge forms (sharp, R0.2); the contact solution depends on the predecessor state, so this "
         "is the worst computed instance, not a proven bound")
GLOBAL = "js5_mu0_T3750_g078"
PATCHES = ["seat_s5L8_mu0", "seat_s5L8_mu0_go", "seat_s5L12_mu0_go", "seat_s6L12_mu0"]
LABEL = {GLOBAL: "js5", "seat_s5L8_mu0": "(a)", "seat_s5L8_mu0_go": "(a')", "seat_s5L12_mu0_go": "(a'')", "seat_s6L12_mu0": "(b2)"}
EDGE = {GLOBAL: "sharp", "seat_s5L8_mu0": "sharp", "seat_s5L8_mu0_go": "sharp", "seat_s5L12_mu0_go": "sharp", "seat_s6L12_mu0": "R0.2"}
REPEATS = {"seat_s6L12_mu0": {"SOAK": "SOAK_rep", "SOAK52": "SOAK52_rep"}}    # extra instances of a state in the same run
STATES = ["PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S"]
A_S = 14.18


def jl(p):
    return json.loads(p.read_text()) if p.exists() else None


def main():
    post = jl(RUNS / GLOBAL / "post.json")
    runs = [GLOBAL] + [p for p in PATCHES if (RUNS / p / "compare.json").exists() and (RUNS / p / "shank.json").exists()]
    out = {"doc": __doc__.split("usage:")[0].strip(), "version": "v3", "status": "ADOPTED (lead 15:37Z (R1))", "basis": BASIS,
           "supersedes": SUPERSEDES, "runs": {LABEL[r]: r for r in runs}, "edge_form": {LABEL[r]: EDGE[r] for r in runs},
           "repeat_instances": {f"{LABEL[r]} rep": {st: k for st, k in REPEATS[r].items()} for r in runs if r in REPEATS},
           "inputs_sha16": {}, "states": {}}
    import hashlib
    for r in runs:
        for fn in ("shank.json", "seatforce.json", "compare.json", "post.json"):
            fp = RUNS / r / fn
            if fp.exists():
                out["inputs_sha16"][f"{r}/{fn}"] = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
    for st in STATES:
        rec = {"N_plane_N": {}, "M_x28.6_Nmm": {}, "M_max_threaded_Nmm": {}, "seat_window_N": {}, "after": {}, "lines": {}}
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
            if r == GLOBAL:
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
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
