"""J-FWD broken-edge soak envelope CANDIDATE from (b2) (fea3d 2026-10-20 ~15:40Z; lead 11:41Z (b2) form (A): "each repeat within 5 % of
its first instance (54 lines, screw N and M, seat window).  Holds -> (b2) soak values are the soak basis; else envelope + tell the lead
before (b2') / (b1)").  The criterion FAILED (histcheck.json), so this script forms the envelope over (b2)'s own instances, per state and
per quantity, in the form of ruling 11:41Z (3) (highest screw N, lowest seat window force, lowest MS per line; M at x' 28.6 and on the
threaded length as the highest), and, next to it, the worst of that and the ADOPTED sharp-edge envelope (results/v352/
jfwd_soak_envelope_v352.json, lead 13:14Z; read-only here, sha recorded).  It does NOT replace the adopted file: which envelope the
J-FWD rows use is the lead's ruling.
Runs: seat_s6L12_mu0 (b2) = s6 mesh, R0.2 drawing-maximum break at the TC-01 hole-to-bore edge + 0.1 x 45 at the flat, patch L12 on js5's
field, mu 0, 3750 N, A4-80 properties (Mechanical maps to IN718, CHANGELOG 240); order PRELOAD > SOAK52 > SOAK > SOAK70 > FA1S >
SOAK_rep > SOAK52_rep.  Instances: SOAK = {SOAK (after SOAK52), SOAK_rep (after FA1S)}, SOAK52 = {SOAK52 (after PRELOAD), SOAK52_rep
(after SOAK_rep)}; PRELOAD, SOAK70 (after SOAK) and FA1S (after SOAK70) have one instance each.
Evidence: SIM (posts of the run: shank.json plane_exact / sections, seatforce.json window, compare.json 54 seat lines) + DERIVED (envelope).
usage: python -I -B jfwd_envelope_b2.py -> jfwd/runs/seat_s6L12_mu0/envelope_candidate.json"""
from __future__ import annotations
import json, hashlib, time
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
JOB = "seat_s6L12_mu0"
SHARP = Path("/home/claude/work/fea3d/results/v352/jfwd_soak_envelope_v352.json")
OUT = RUNS / JOB / "envelope_candidate.json"
INST = {"PRELOAD": ["PRELOAD"], "SOAK52": ["SOAK52", "SOAK52_rep"], "SOAK": ["SOAK", "SOAK_rep"], "SOAK70": ["SOAK70"], "FA1S": ["FA1S"]}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def jl(p):
    return json.loads(Path(p).read_text())


def main():
    R = RUNS / JOB
    sh, sf, cm, meta = jl(R / "shank.json"), jl(R / "seatforce.json"), jl(R / "compare.json"), jl(R / "meta.json")
    sharp = jl(SHARP)
    out = {"id": "jfwd_envelope_b2_candidate", "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "owner": "fea3d",
           "doc": __doc__.split("usage:")[0].strip(), "status": "CANDIDATE - not adopted; the adopted envelope is unchanged",
           "inputs": {"shank.json": sha16(R / "shank.json"), "seatforce.json": sha16(R / "seatforce.json"), "compare.json": sha16(R / "compare.json"),
                      "histcheck.json": sha16(R / "histcheck.json"), "sharp_envelope_adopted": {"path": str(SHARP), "sha16": sha16(SHARP)}},
           "step_after": meta.get("step_after"), "states": {}}
    for st, inst in INST.items():
        rec = {"instances": inst, "N_plane_N": {}, "M_x28.6_Nmm": {}, "M_max_threaded_Nmm": {}, "seat_window_N": {}, "lines": {}}
        for i in inst:
            k = sh["steps"][i]
            rec["N_plane_N"][i] = round(abs(k["plane_exact"]["N_N"]), 1)
            m = [x["M"] for x in k["sections"] if abs(x["x"] - 28.6) < 0.051]
            rec["M_x28.6_Nmm"][i] = round(abs(m[0]), 1)
            rec["M_max_threaded_Nmm"][i] = [round(abs(k["M_max_threaded"]["M"]), 1), k["M_max_threaded"]["x"]]
            rec["seat_window_N"][i] = sf["steps"][i]["seat_TC02"]["footprint"]["window_daz9_zp9_N"]
            for row in cm["steps"][i]["relax_seat_lines_cmp"]:
                if row["family"] == "hole_edge":
                    continue
                key = f"d{row['delta_deg']:+.3f}_z{row['z_prime_mm']:+.1f}"
                L = rec["lines"].setdefault(key, {"delta_deg": row["delta_deg"], "z_prime_mm": row["z_prime_mm"], "MS_PQ": {}, "PmPb_MPa": {}})
                L["MS_PQ"][i] = row["MS_PQ_patch"]
                L["PmPb_MPa"][i] = row["PmPb_patch"]
        for L in rec["lines"].values():
            k = min(L["MS_PQ"], key=lambda q: L["MS_PQ"][q])
            L["MS_PQ_env_b2"], L["env_from"] = L["MS_PQ"][k], k
        b2 = {}
        kN = max(rec["N_plane_N"], key=lambda q: rec["N_plane_N"][q])
        b2["N_max_N"] = [rec["N_plane_N"][kN], kN]
        kw = min(rec["seat_window_N"], key=lambda q: rec["seat_window_N"][q])
        b2["window_min_N"] = [rec["seat_window_N"][kw], kw]
        km = max(rec["M_x28.6_Nmm"], key=lambda q: rec["M_x28.6_Nmm"][q])
        b2["M_x28.6_max_Nmm"] = [rec["M_x28.6_Nmm"][km], km]
        kt = max(rec["M_max_threaded_Nmm"], key=lambda q: rec["M_max_threaded_Nmm"][q][0])
        b2["M_max_threaded_max_Nmm"] = rec["M_max_threaded_Nmm"][kt] + [kt]
        gov = min(rec["lines"].values(), key=lambda L: L["MS_PQ_env_b2"])
        b2["lines_min_MS_PQ"] = [gov["MS_PQ_env_b2"], gov["env_from"], gov["delta_deg"], gov["z_prime_mm"]]
        b2["n_lines_negative"] = sum(1 for L in rec["lines"].values() if L["MS_PQ_env_b2"] < 0)
        b2["n_lines"] = len(rec["lines"])
        rec["envelope_b2"] = b2
        # worst of the adopted sharp envelope and (b2), per quantity (and per line)
        se = sharp["states"].get(st, {}).get("envelope", {})
        sl = sharp["states"].get(st, {}).get("lines", {})
        comb = {}
        if "N_max_N" in se:
            comb["N_max_N"] = [b2["N_max_N"][0], f"(b2) {b2['N_max_N'][1]}"] if b2["N_max_N"][0] >= se["N_max_N"][0] else [se["N_max_N"][0], f"sharp {se['N_max_N'][1]}"]
        if "window_min_N" in se:
            comb["window_min_N"] = [b2["window_min_N"][0], f"(b2) {b2['window_min_N'][1]}"] if b2["window_min_N"][0] <= se["window_min_N"][0] else [se["window_min_N"][0], f"sharp {se['window_min_N'][1]}"]
        if "M_x28.6_max_Nmm" in se:
            comb["M_x28.6_max_Nmm"] = [b2["M_x28.6_max_Nmm"][0], f"(b2) {b2['M_x28.6_max_Nmm'][1]}"] if b2["M_x28.6_max_Nmm"][0] >= se["M_x28.6_max_Nmm"][0] else [se["M_x28.6_max_Nmm"][0], f"sharp {se['M_x28.6_max_Nmm'][1]}"]
        cl = {}
        for key, L in rec["lines"].items():
            s_ms = sl.get(key, {}).get("MS_PQ_env")
            if s_ms is None or L["MS_PQ_env_b2"] <= s_ms:
                cl[key] = [L["MS_PQ_env_b2"], f"(b2) {L['env_from']}"]
            else:
                cl[key] = [s_ms, f"sharp {sl[key]['env_from']}"]
        g = min(cl, key=lambda q: cl[q][0])
        comb["lines_min_MS_PQ"] = cl[g] + [g]
        comb["n_lines_negative"] = sum(1 for v in cl.values() if v[0] < 0)
        comb["n_lines_from_b2"] = sum(1 for v in cl.values() if v[1].startswith("(b2)"))
        rec["sharp_envelope_adopted"] = {k: se.get(k) for k in ("N_max_N", "window_min_N", "M_x28.6_max_Nmm", "lines_min_MS_PQ", "n_lines_negative_env")}
        rec["envelope_sharp_and_b2"] = comb
        out["states"][st] = rec
        print(f"{st:8s} (b2) N {b2['N_max_N']} win {b2['window_min_N']} M28.6 {b2['M_x28.6_max_Nmm']} Mthr {b2['M_max_threaded_max_Nmm']} "
              f"lines {b2['lines_min_MS_PQ']} neg {b2['n_lines_negative']} | sharp N {se.get('N_max_N')} win {se.get('window_min_N')} "
              f"M {se.get('M_x28.6_max_Nmm')} lines {se.get('lines_min_MS_PQ')} | comb {comb}", flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT, sha16(OUT))


if __name__ == "__main__":
    main()
