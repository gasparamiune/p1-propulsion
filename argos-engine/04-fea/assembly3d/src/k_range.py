"""F3 stiffness range on CAD v3.5.1 (fea3d 2026-10-19): K_alpha (outer axis X) / K_beta (inner axis, ring Y) of the engine held by the
two TVC chains, from post_k.py results (SIM unit angular-acceleration steps EAX / EAY, asm v1.2, coarse=2 pose runs, rigid servo output)
plus the servo output compliance in series (k_s 58 / 174 N m/rad per servo, line 13 range, TO-VERIFY bench B-TVC).
Sources: results/k_stop_c71.json (8 stop poses, 8 deg), results/k_cone_c71.json (9 range-cone poses, if present),
results/k_stop045_compliant_c71.json (stop045 on the compliant airframe).  Comparison: V5c (CAD v3.3, engine rigid) as published in
hub/04-fea/stiffness/gimbal_k_summary_V5c_v1.json (read only).
usage: k_range.py  -> results/k_range_v351.json, results/tables/k_range_v351.md
"""
from __future__ import annotations
import json
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
SRC = [("stop (8 deg), rigid airframe", "k_stop_c71.json"), ("range cone, rigid airframe", "k_cone_c71.json"),
       ("stop045, compliant airframe", "k_stop045_compliant_c71.json")]
AX = {"alpha (outer, X)": "K_alpha", "beta (inner, ring Y)": "K_beta"}


V5C_FILE = Path("/home/claude/work/shared-fallback/engine/04-fea/stiffness/gimbal_k_summary_V5c_v1.json")


def v5c():
    """Mechanical V5c (SIM, CAD v3.3 as built, engine case rigid, 9 poses at 7 deg): ranges per variant (read, not edited)."""
    import hashlib
    raw = V5C_FILE.read_bytes()
    d = json.loads(raw)
    P = d["poses"]
    out = {"source": "hub/04-fea/stiffness/gimbal_k_summary_V5c_v1.json", "sha16": hashlib.sha256(raw).hexdigest()[:16], "model": d["model"],
           "poses": list(P)}
    for v in ("mech_T", "mech_T_chainlow", "mech_C_chainhigh", "mech_rigidchain", "smin_T", "smax_T"):
        out[v] = {ax: [min(p[v][ax] for p in P.values()), max(p[v][ax] for p in P.values())] for ax in ("K_alpha", "K_beta")}
    return out


def main():
    rows, groups = [], {}
    for g, fn in SRC:
        fp = RES / fn
        if not fp.exists():
            continue
        d = json.loads(fp.read_text())
        for r in d["runs"]:
            row = {"group": g, "run": r["run"], "pose_deg": r["pose_deg"]}
            for ax, lab in AX.items():
                a = r["axes"][ax]
                row[lab] = {"K_FE_engine": a["K_FE_engine_Nm_per_rad"], "K_FE_nozzle": a["K_FE_nozzle_Nm_per_rad"],
                            "K_rods_only": a["K_rods_only_Nm_per_rad"], "structure_share": a["structure_compliance_share"],
                            "with_servo_58": a["servo_series"]["k_s58_engine"]["K_total_Nm_per_rad"],
                            "with_servo_174": a["servo_series"]["k_s174_engine"]["K_total_Nm_per_rad"]}
            rows.append(row)
            groups.setdefault(g, []).append(row)
    rng = {}
    for g, rs in list(groups.items()) + [("ALL", rows)]:
        rng[g] = {lab: {k: [min(r[lab][k] for r in rs), max(r[lab][k] for r in rs)] for k in rs[0][lab]} for lab in AX.values()}
    out = {"tag": "SIM (FE unit steps, asm v1.2, rigid servo output) + DERIVED (servo in series, k_s ASSUMED 58-174 N m/rad TO-VERIFY)",
           "units": "N m/rad", "rows": rows, "range": rng,
           "V5c_comparison": v5c()}
    (RES / "k_range_v351.json").write_text(json.dumps(out, indent=1, default=float))
    L = ["K about the gimbal axes, N m/rad (engine best-fit rotation; SIM rigid servo output; DERIVED with servo k_s 58 / 174 N m/rad per servo in series).", "",
         "| group | run | pose (alpha, beta) deg | K_alpha FE | K_alpha +servo 58 / 174 | K_beta FE | K_beta +servo 58 / 174 | rods-only alpha / beta | structure share alpha / beta |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a, b = r["K_alpha"], r["K_beta"]
        L.append(f"| {r['group']} | {r['run']} | {r['pose_deg'][0]:+.2f}, {r['pose_deg'][1]:+.2f} | {a['K_FE_engine']:.0f} | {a['with_servo_58']:.0f} / {a['with_servo_174']:.0f} | "
                 f"{b['K_FE_engine']:.0f} | {b['with_servo_58']:.0f} / {b['with_servo_174']:.0f} | {a['K_rods_only']:.0f} / {b['K_rods_only']:.0f} | "
                 f"{a['structure_share']:.2f} / {b['structure_share']:.2f} |")
    L += ["", "| group | K_alpha FE | K_alpha +servo 58 | K_alpha +servo 174 | K_beta FE | K_beta +servo 58 | K_beta +servo 174 |", "|---|---|---|---|---|---|---|"]
    fm = lambda v: f"{v[0]:.0f}-{v[1]:.0f}"
    for g, v in rng.items():
        a, b = v["K_alpha"], v["K_beta"]
        L.append(f"| {g} | {fm(a['K_FE_engine'])} | {fm(a['with_servo_58'])} | {fm(a['with_servo_174'])} | {fm(b['K_FE_engine'])} | {fm(b['with_servo_58'])} | {fm(b['with_servo_174'])} |")
    v = out["V5c_comparison"]
    L += ["", f"V5c comparison (Mechanical SIM, {v['source']} {v['sha16']}; CAD v3.3, engine case rigid, 9 poses at 7 deg; ENG-11 range 3133-7406 per CHANGELOG 188 (7)):",
          "", "| V5c variant | K_alpha | K_beta |", "|---|---|---|"]
    for k in ("mech_T", "mech_T_chainlow", "mech_C_chainhigh", "mech_rigidchain", "smin_T", "smax_T"):
        L.append(f"| {k} | {fm(v[k]['K_alpha'])} | {fm(v[k]['K_beta'])} |")
    (RES / "tables").mkdir(exist_ok=True)
    (RES / "tables" / "k_range_v351.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
