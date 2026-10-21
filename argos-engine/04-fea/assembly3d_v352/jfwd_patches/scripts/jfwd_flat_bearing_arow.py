"""TC-01 under-head flat bearing on the ruled ring area A_ROW (fea3d 2026-10-20 ~15:45Z; Mechanical 15:27Z note, lead ruling 14:14Z rows v4 (a):
the jfwd_spotface.py A_ANN basis (full flat annulus d9.5 / d5.5, 47.12 mm2) is SUPERSEDED for every quoted TC-01 under-head flat-bearing
row; quoted rows use the minimum ring at the rev-5 worst stack, A_ROW 38.171 mm2 (Mechanical jfwd_in718_rows_v352_v5.json; 38.498 without
the ISO 13715 OD break = information; 36.401 on the union inner boundary = Mechanical's recommended basis, information here).
DERIVED, no solve: sigma = F_head / A, MS = Fbry(T) / sigma - 1 at SF 1 (Fbry = 1.40 Fty(T), the engmat e/D 2 ratio as jfwd_spotface.py),
with F_head and Fbry(T) from the js5 spotface post (A4-80 FE screw, 3750 N, js5 history) and, as information, F_head = the screw N of
the ADOPTED envelope v3 (jfwd_soak_envelope_v352_v3.json, lead 15:37Z (R1): worst of the computed histories and edge forms, sharp +
R0.2) and, for the record, of the superseded sharp-only v2 (336568296bdb896f) and the (b2) instances (envelope_candidate.json) at the js5
T of the state.  The FE rows are information (A4-80); the criterion rows are Mechanical's IN718 rows (v5).
v2 of this output (15:56Z): jfwd_flat_bearing_arow_v352_v2.json; v1 jfwd_flat_bearing_arow_v352.json (bdb34ca4af677bca, envelope v2) kept.
usage: python -I -B jfwd_flat_bearing_arow.py -> results/v352/jfwd_flat_bearing_arow_v352.json"""
from __future__ import annotations
import json, math, hashlib, time
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
SPOT = RUNS / "js5_mu0_T3750_g078" / "spotface.json"
ENV = Path("/home/claude/work/fea3d/results/v352/jfwd_soak_envelope_v352_v3.json")      # adopted (R1)
ENV_V2 = Path("/home/claude/work/fea3d/results/v352/jfwd_soak_envelope_v352.json")       # superseded sharp-only record
CAND = RUNS / "seat_s6L12_mu0" / "envelope_candidate.json"
OUT = Path("/home/claude/work/fea3d/results/v352/jfwd_flat_bearing_arow_v352_v2.json")
AREAS = {"A_ROW_ruled": 38.171, "A_ROW_no_OD_break_info": 38.498, "A_union_inner_info": 36.401,
         "A_ANN_superseded": math.pi / 4.0 * (9.5 ** 2 - 5.5 ** 2)}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    sp = json.loads(SPOT.read_text())
    env = json.loads(ENV.read_text())
    env2 = json.loads(ENV_V2.read_text())
    cand = json.loads(CAND.read_text()) if CAND.exists() else None
    out = {"id": "jfwd_flat_bearing_arow_v352", "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "owner": "fea3d",
           "doc": __doc__.split("usage:")[0].strip(), "evidence": "SIM (js5 head force, posts) + DERIVED (area basis, MS)",
           "inputs": {"spotface.json": sha16(SPOT), "soak_envelope_adopted_v3": sha16(ENV), "soak_envelope_v2_superseded": sha16(ENV_V2),
                      "b2_envelope_candidate": sha16(CAND) if cand else None},
           "areas_mm2": {k: round(v, 3) for k, v in AREAS.items()}, "states": {}}
    for st, v in sp["steps"].items():
        Fh, Fbry, T = v["head_bearing"]["F_head_N"], v["Fbry_MPa"], v["T_TC01_C"]
        e = {"T_TC01_C": T, "Fbry_MPa": Fbry, "F_head_js5_N": Fh, "rows": {}}
        forces = {"js5 head force": Fh}
        sN = (env["states"].get(st, {}).get("envelope") or {}).get("N_max_N")
        if sN:
            forces["adopted envelope v3 N_max (" + str(sN[1]) + ")"] = sN[0]
        s2 = (env2["states"].get(st, {}).get("envelope") or {}).get("N_max_N")
        if s2:
            forces["superseded sharp-only v2 N_max (" + str(s2[1]) + "; record)"] = s2[0]
        if cand and st in cand["states"]:
            bN = cand["states"][st]["envelope_b2"]["N_max_N"]
            forces["(b2) N_max (" + str(bN[1]) + ")"] = bN[0]
        for fl, F in forces.items():
            e["rows"][fl] = {"F_N": F, **{k: {"sigma_MPa": round(F / A, 1), "MS_SF1": round(Fbry / (F / A) - 1, 3)} for k, A in AREAS.items()}}
        out["states"][st] = e
        print(st, T, Fbry, {fl: (r["F_N"], r["A_ROW_ruled"]["MS_SF1"], r["A_ANN_superseded"]["MS_SF1"]) for fl, r in e["rows"].items()}, flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT, sha16(OUT))


if __name__ == "__main__":
    main()
