"""RM2-05 addendum (fea3d 2026-10-20): candidate cause of the FE K_beta excess over V5c (REV-MECH-2 (f2), CHANGELOG 234 (5)).
DERIVED estimate only, no model change: re-weight the V5c centre-pose strain-energy split (Mechanical SIM, hub 04-fea/stiffness/
gimbal_k_summary_V5c_v1.json, read only) by the ratio of the gimbal bearing spring stiffnesses of the two models:
  V5c (CAD v3.3): 608-2RS ball bearings, Palmgren point contact at F_thrust 62.5 N, in series with the 8 mm pin cantilever (+0.5 d root);
  FE  (CAD v3.5.1, asm v1.2): HK0808 drawn-cup needles, Palmgren line contact at F_thrust 500 N, in series with the 440C pin cantilever.
For a spring set j holding the energy fraction f_j of the V5c compliance, replacing k_j,V5c by k_j,FE changes the compliance by
f_j (k_j,V5c / k_j,FE - 1).  usage: k_beta_cause.py -> results/v352/k_beta_cause.json
"""
import json, hashlib, sys
from pathlib import Path
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import asm3d as A3   # noqa: E402

V5C = Path("/home/claude/work/shared-fallback/engine/04-fea/stiffness/gimbal_k_summary_V5c_v1.json")
raw = V5C.read_bytes()
d = json.loads(raw)
c = d["poses"]["centre"]
es = {e["load"]: e["fraction"] for e in c["energy_split_base"]}
bv = A3.bearing_springs(62.5)
bf = A3.needle_springs(500.0)
fe = json.loads(Path("/home/claude/work/fea3d/results/k_cone_c71_v352.json").read_text())
neu = [r for r in fe["runs"] if r["run"] == "pose_neutral_c71"][0]
out = {"tag": "DERIVED (estimate from Mechanical's V5c energy split; SIM inputs); no model change", "V5c_sha16": hashlib.sha256(raw).hexdigest()[:16],
       "springs_N_per_mm": {"V5c_inner": bv["k_in_radial"], "V5c_outer": bv["k_out_radial"], "V5c_608_alone": bv["k_608"],
                             "FE_inner": bf["k_in_radial"], "FE_outer": bf["k_out_radial"], "FE_needle_alone": bf["k_needle"]},
       "axes": {}}
for ax, load, lab, j in (("alpha (outer, X)", "Mx", "K_alpha", 0), ("beta (inner, ring Y)", "My", "K_beta", 1)):
    f = es[load]
    f_in, f_out = f.get("BEARINGS_INNER(608+pin)", 0.0), f.get("BEARINGS_OUTER(608+pin)", 0.0)
    f_rod = sum(v for k, v in f.items() if k.startswith("ROD_CHAIN"))
    ratio = 1.0 + f_in * (bv["k_in_radial"] / bf["k_in_radial"] - 1.0) + f_out * (bv["k_out_radial"] / bf["k_out_radial"] - 1.0)
    K_v5c = c["mech_T"][lab]
    K_fe = neu["two_axis"]["rigid_servo"]["coupled_Nm_per_rad"][j]
    sh = neu["axes"][ax]["structure_compliance_share"]
    K_struct_fe = K_fe / sh
    K_struct_v5c = K_v5c / (1.0 - f_rod)
    K_struct_v5c_fe_brg = K_v5c / (ratio - f_rod)
    out["axes"][ax] = {"V5c_energy_fraction": {"bearings_inner": f_in, "bearings_outer": f_out, "rod_chains": f_rod},
                       "K_V5c_mech_T_centre": K_v5c, "K_FE_neutral": K_fe, "FE_over_V5c": K_fe / K_v5c - 1.0,
                       "compliance_ratio_with_FE_bearings": ratio, "K_V5c_with_FE_bearings": K_v5c / ratio,
                       "explained_fraction_of_excess": ((K_v5c / ratio) - K_v5c) / (K_fe - K_v5c) if K_fe != K_v5c else None,
                       "structure": {"K_struct_FE": K_struct_fe, "K_struct_V5c": K_struct_v5c, "FE_over_V5c": K_struct_fe / K_struct_v5c - 1.0,
                                     "K_struct_V5c_with_FE_bearings": K_struct_v5c_fe_brg,
                                     "FE_over_V5c_with_FE_bearings": K_struct_fe / K_struct_v5c_fe_brg - 1.0}}
Path("/home/claude/work/fea3d/results/v352/k_beta_cause.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
