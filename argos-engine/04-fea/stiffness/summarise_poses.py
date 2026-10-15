"""Collects the gimbal_k.py runs (runs/stiff/*/result.json) into gimbal_k_summary_v1.json (04-fea/stiffness, v1, 2026-10-12, Mechanical).

Content: K (N m/rad) about the outer (alpha, X) and inner (beta, Y) axes for every pose and chain/servo variant, the full 2x2 K
(cross terms at the cone poses), mesh study at the centre (h 4 / 3 / 2.5 mm, hf 3 / 4), thrust preload study (62.5 / 160 / 500 N
on the 608 bearings), the approved lever-web stiffening variant (centre), and rocking-mode estimates f = sqrt(K/I)/(2 pi) with the
engine-group inertia about the pivot (+ the ring for alpha).  Rocking estimates exclude the reflected servo rotor inertia J_int n^2
(Electronics servo_jint_estimate_v1: 0.032-0.042 kg m2 at the engine for SB-2292SG), which GNC's CSI model carries.
"""
from __future__ import annotations
import sys, json, math, glob, hashlib
from pathlib import Path
import numpy as np

RUNS = Path("/home/claude/work/mechanical/runs/stiff")
HERE = Path(__file__).resolve().parent
OUT = HERE / "gimbal_k_summary_v1.json"
VARS = ["mech_T", "mech_M", "mech_C", "mech_T_chainlow", "mech_C_chainhigh", "mech_rigidchain", "smin_T", "smin_M", "smin_C",
        "smax_T", "smax_M", "smax_C", "servo_only_min", "servo_only_max"]
POSES = ["centre_h3_hf4_T62.5", "alphap7_h3_hf4_T62.5", "alpham7_h3_hf4_T62.5", "betap7_h3_hf4_T62.5", "betam7_h3_hf4_T62.5",
         "cone7_045_h3_hf4_T62.5", "cone7_135_h3_hf4_T62.5", "cone7_225_h3_hf4_T62.5", "cone7_315_h3_hf4_T62.5"]


def load(d):
    r = json.loads((RUNS / d / "result.json").read_text())
    return r


def main(I_xx_engine=0.05178, I_yy_engine=0.05176, I_xx_ring=0.000139, tag=""):
    """tag: run-name suffix of a design variant (e.g. '_V5c'); writes gimbal_k_summary<tag>_v1.json with the 9 poses only
    (v1.1, 2026-10-13: ENG-11 V5c acceptance). The inertia stays the v3.3 basis (variant mass change is reported separately)."""
    global OUT
    if tag:
        OUT = HERE / f"gimbal_k_summary{tag}_v1.json"
    out = {"id": "gimbal_k_summary", "version": "v1", "date": "2026-10-12", "script": "04-fea/stiffness/summarise_poses.py",
           "model": "gimbal_k.py v1 (CalculiX C3D10 static, CAD v3.3 as built; airframe rigid at the 16 M5 holes; engine case rigid)",
           "servo_basis": {"K_s_output_Nm_per_rad": [58.0, 174.0], "tag": "ASSUMED in electronics.json v1 (T_stall / 1-3 deg proportional band); "
                           "bench measurement B-TVC-1 required", "series_model": "1/k = 1/k_chain + lambda^2/K_s per rod (lambda = horn moment arm at the pose)"},
           "chain_basis": "rod FE (rod_k.py) + 2 x GE 5 E (1e5 N/mm ASSUMED; low 5e4, high 3e5) + stud/shoulder screw cantilever; variants T/M/C = rod "
                          "tension / mean / compression stiffness",
           "I_used_kgm2": {"alpha": I_xx_engine + I_xx_ring, "beta": I_yy_engine,
                           "src": "massprops_v2.json mid-burn engine group about the pivot (+ ring for alpha), CAD v3.3"},
           "poses": {}, "mesh_study": {}, "thrust_study": {}, "stiffening_web_variant": {}, "runs_sha256_16": {}}
    for d in [p + tag for p in POSES]:
        r = load(d)
        v = r["variants"]
        rec = {"alpha_deg": r["alpha_deg"], "beta_deg": r["beta_deg"], "nodes": sum(x["nodes"] for x in r["mesh"].values()),
               "K_roll_Nm_rad": round(r["base"]["K_roll_Nm_rad"], 0), "lambda_h_mm": r["lambda_h_mm"]}
        for k in VARS:
            K = v[k]
            rec[k] = {"K_alpha": round(K["K_alpha_Nm_rad"], 1), "K_beta": round(K["K_beta_Nm_rad"], 1),
                      "K_xy": [[round(x, 1) for x in row] for row in K["K_xy_Nm_per_rad"]]}
        for k in ("mech_T", "smin_T", "smax_T"):
            rec[k]["f_rock_Hz"] = [round(math.sqrt(rec[k]["K_alpha"] / out["I_used_kgm2"]["alpha"]) / (2 * math.pi), 1),
                                   round(math.sqrt(rec[k]["K_beta"] / out["I_used_kgm2"]["beta"]) / (2 * math.pi), 1)]
        es = r["base"].get("energy_split") if isinstance(r["base"], dict) else None
        if es:
            rec["energy_split_base"] = [{"load": e["load"], "fraction": {kk: round(vv, 3) for kk, vv in e["fraction"].items() if vv > 0.005}} for e in es]
        out["poses"][d.split("_h3")[0]] = rec
        out["runs_sha256_16"][d] = hashlib.sha256((RUNS / d / "result.json").read_bytes()).hexdigest()[:16]
    # envelope over the 9 poses
    env = {}
    for k in VARS:
        ka = [out["poses"][p][k]["K_alpha"] for p in out["poses"]]
        kb = [out["poses"][p][k]["K_beta"] for p in out["poses"]]
        env[k] = {"K_alpha_min": min(ka), "K_alpha_max": max(ka), "K_beta_min": min(kb), "K_beta_max": max(kb),
                  "K_beta_min_pose": list(out["poses"])[int(np.argmin(kb))], "K_alpha_min_pose": list(out["poses"])[int(np.argmin(ka))]}
    out["envelope_over_poses"] = env
    if tag:
        mt = [out["poses"][p]["mech_T"] for p in out["poses"]]
        allk = [m["K_alpha"] for m in mt] + [m["K_beta"] for m in mt]
        mean = sum(allk) / len(allk)
        out["variant"] = {"tag": tag, "K_mech_T_min_Nm_rad": min(allk), "K_mech_T_max_Nm_rad": max(allk), "mean": round(mean, 1),
                          "spread_pct": [round(100 * (min(allk) - mean) / mean, 1), round(100 * (max(allk) - mean) / mean, 1)]}
        for k in ("mech_T", "smin_T", "smax_T"):
            e = env[k]
            e["f_rock_min_Hz"] = [round(math.sqrt(e["K_alpha_min"] / out["I_used_kgm2"]["alpha"]) / (2 * math.pi), 1),
                                  round(math.sqrt(e["K_beta_min"] / out["I_used_kgm2"]["beta"]) / (2 * math.pi), 1)]
        OUT.write_text(json.dumps(out, indent=1))
        print("wrote", OUT)
        for p, rec in out["poses"].items():
            print(f"{p:10s} mech {rec['mech_T']['K_alpha']:7.0f}/{rec['mech_T']['K_beta']:7.0f}  smin {rec['smin_T']['K_alpha']:6.0f}/{rec['smin_T']['K_beta']:6.0f}"
                  f"  smax {rec['smax_T']['K_alpha']:6.0f}/{rec['smax_T']['K_beta']:6.0f}  es {rec.get('energy_split_base', '')}"[:400])
        print(json.dumps(out["variant"]), json.dumps(env["mech_T"]), json.dumps(env["smin_T"]))
        return
    for k in ("mech_T", "smin_T", "smax_T"):
        e = env[k]
        e["f_rock_min_Hz"] = [round(math.sqrt(e["K_alpha_min"] / out["I_used_kgm2"]["alpha"]) / (2 * math.pi), 1),
                              round(math.sqrt(e["K_beta_min"] / out["I_used_kgm2"]["beta"]) / (2 * math.pi), 1)]
    # mesh study (centre, mech_T)
    ms = {}
    for d in ("centre_h4_hf4_T62.5", "centre_h3_hf4_T62.5", "centre_h3_hf3_T62.5", "centre_h2.5_hf4_T62.5"):
        r = load(d)
        ms[d] = {"nodes": sum(x["nodes"] for x in r["mesh"].values()), "K_alpha": round(r["variants"]["mech_T"]["K_alpha_Nm_rad"], 1),
                 "K_beta": round(r["variants"]["mech_T"]["K_beta_Nm_rad"], 1)}
    a4, a3, a25 = (ms[d]["K_alpha"] for d in ("centre_h4_hf4_T62.5", "centre_h3_hf4_T62.5", "centre_h2.5_hf4_T62.5"))
    b4, b3, b25 = (ms[d]["K_beta"] for d in ("centre_h4_hf4_T62.5", "centre_h3_hf4_T62.5", "centre_h2.5_hf4_T62.5"))
    ms["change_h3_to_h2.5_pct"] = [round(100 * (a25 - a3) / a3, 2), round(100 * (b25 - b3) / b3, 2)]
    ms["change_h4_to_h3_pct"] = [round(100 * (a3 - a4) / a4, 2), round(100 * (b3 - b4) / b4, 2)]
    ms["note"] = ("C3D10 displacement FE converges from above; h 3 (production) is within 0.4 % of h 2.5 and the hf 3 refinement of the "
                  "fillet/eye zones changes K by < 0.05 %")
    out["mesh_study"] = ms
    for d in ("centre_h3_hf4_T62.5", "centre_h3_hf4_T160", "centre_h3_hf4_T500"):
        r = load(d)
        out["thrust_study"][d.split("_")[-1]] = {"K_alpha": round(r["variants"]["mech_T"]["K_alpha_Nm_rad"], 1),
                                                 "K_beta": round(r["variants"]["mech_T"]["K_beta_Nm_rad"], 1),
                                                 "smin_T": [round(r["variants"]["smin_T"]["K_alpha_Nm_rad"], 1), round(r["variants"]["smin_T"]["K_beta_Nm_rad"], 1)],
                                                 "K_roll": round(r["base"]["K_roll_Nm_rad"], 0)}
    r = load("centre_h3_hf4_T62.5_web")
    out["stiffening_web_variant"] = {k: [round(r["variants"][k]["K_alpha_Nm_rad"], 1), round(r["variants"][k]["K_beta_Nm_rad"], 1)]
                                     for k in ("mech_T", "smin_T", "smax_T", "servo_only_min", "servo_only_max")}
    out["stiffening_web_variant"]["note"] = ("tapered lever-root webs on GM-01/02 + deeper GM-03 section (lead-approved concept), centre pose only; "
                                             "not yet in the CAD baseline (v3.4) and not yet checked for pushrod-eye clearance at the stop poses")
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)
    for p, rec in out["poses"].items():
        print(f"{p:10s} mech {rec['mech_T']['K_alpha']:7.0f}/{rec['mech_T']['K_beta']:7.0f}  smin {rec['smin_T']['K_alpha']:6.0f}/{rec['smin_T']['K_beta']:6.0f}"
              f"  smax {rec['smax_T']['K_alpha']:6.0f}/{rec['smax_T']['K_beta']:6.0f}  f smin {rec['smin_T']['f_rock_Hz']} smax {rec['smax_T']['f_rock_Hz']} mech {rec['mech_T']['f_rock_Hz']}")
    print(json.dumps(env["smin_T"]), json.dumps(env["mech_T"]))
    print(json.dumps(out["mesh_study"]))


if __name__ == "__main__":
    main(tag=sys.argv[1] if len(sys.argv) > 1 else "")
