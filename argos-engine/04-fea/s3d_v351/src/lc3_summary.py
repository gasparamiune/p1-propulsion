"""LC3 per-pose summary table (fea3d 2026-10-19): fb_run range, rod compression, moment-path residual, lowest regular margins,
bearing / washer envelopes (max |component| over 64 sub-cases, SIM), ICD max hole shear. Legacy (asm v1.1) vs asm v1.2 (_c71).
usage: lc3_summary.py [sfx=_c71] [ref=]      -> results/f1_lc3_summary{sfx}.json and results/tables/f1_lc3_summary{sfx}.md
"""
import sys, json
from pathlib import Path
RES = Path("/home/claude/work/fea3d/results")
POSES = ["000", "045", "090", "135", "180", "225", "270", "315"]


def one(p, sfx):
    d = json.loads((RES / f"f1_post_lc3_pose_stop{p}{sfx}.json").read_text())
    reg = [m for m in d["margins"] if m.get("set") == "regular" and m.get("case", "LC3") == "LC3"]
    reg.sort(key=lambda m: m["MS"])
    ce = d["connectors_envelope"]
    grp = lambda pre: max(v["max_abs_N"] for k, v in ce.items() if k.startswith(pre))
    shear = 0.0; hole = None
    for h, v in d["icd_envelope"].items():
        s = v.get("max_shear_N", v.get("shear_max_N"))
        if s is not None and s > shear:
            shear, hole = s, h
    return {"pose": f"stop{p}", "pose_deg": d["pose_deg"], "fb_run_range_N": d["fb_run_range_N"],
            "rod_max_compression_N": d["rod_max_compression_N"],
            "rod_max_abs_N": {k: d["connectors_envelope"][k]["value_N"] for k in ("ROD_1", "ROD_2")},  # sign: - compression, + tension
            "moment_path_residual_rel": d["checks"]["equilibrium_residual_rel"],
            "rod_absorbed_fraction": [d["checks"].get("R1_rod1_absorbed_fraction"), d["checks"].get("R2_rod2_absorbed_fraction")],
            "lowest_regular": [{"part": m["part"], "MS": m["MS"], "MS_ult": m.get("MS_ult")} for m in reg[:4]],
            "inner_needle_cup_max_component_N": grp("BRG_IN"), "inner_washer_N": grp("WSH_IN"),
            "outer_needle_cup_max_component_N": grp("BRG_OUT"), "outer_washer_N": grp("WSH_OUT"),
            "icd_max_hole_shear_N": shear, "icd_hole": hole, "icd_totals_envelope": d["icd_totals_envelope"]}


def main(argv):
    o = dict(a.split("=", 1) for a in argv)
    sfx = o.get("sfx", "_c71")
    rows = [one(p, sfx) for p in POSES]
    (RES / f"f1_lc3_summary{sfx}.json").write_text(json.dumps({"tag": "SIM (FE) / DERIVED envelopes", "sfx": sfx, "rows": rows}, indent=1))
    f = lambda x: "nan" if x is None else f"{x:+.3f}"
    L = ["| pose | fb_run N | max rod abs N (- compr / + tens) | lowest regular MS y / u (part) | inner cup / washer N | outer cup / washer N | max hole shear N | moment residual |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rm = max(r["rod_max_abs_N"].items(), key=lambda kv: abs(kv[1]))
        low = "; ".join(f"{m['part']} {f(m['MS'])} / {f(m['MS_ult'])}" for m in r["lowest_regular"][:3])
        L.append(f"| {r['pose']} | {r['fb_run_range_N'][0]:.0f}-{r['fb_run_range_N'][1]:.0f} | {rm[1]:+.1f} ({rm[0]}) | {low} | "
                 f"{r['inner_needle_cup_max_component_N']:.0f} / {r['inner_washer_N']:.0f} | {r['outer_needle_cup_max_component_N']:.0f} / {r['outer_washer_N']:.0f} | "
                 f"{r['icd_max_hole_shear_N']:.0f} ({r['icd_hole']}) | {100*r['moment_path_residual_rel']:.1f} % |")
    (RES / "tables" / f"f1_lc3_summary{sfx}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
