"""LC3 per-pose summary, v3.5.2 (fea3d 2026-10-20; report section 6): the 8 stop poses at R3 on the rev-3 levers (pose_stopXXX_v352r3R3).

Per pose: fb_run range, rod forces (max |F|, sign - compression / + tension), moment-path residual, the lowest REGULAR margins and the
lowest ALL-NODE margins with their class and distance (CHANGELOG 234 (4): every cell carries the all-node minimum beside the regular
value), bearing / washer envelopes (max |component| over the 64 sub-cases), and the ICD maximum hole shear.  Same quantities as the
v3.5.1 lc3_summary.py (results/f1_lc3_summary_c71.json), which is not changed.  The GM-02 stop045 lever-root cell of the matrix is the
p = 1 bound on R2 -> R3 (+0.400 / +0.206, DERIVED, order ASSUMED; lead 12:28Z (5)); this table shows the R3 values as solved and marks
that pose.  Read-only on the posts.  Tags: SIM (FE) / DERIVED (envelopes).
usage: lc3_summary_v352.py [sfx=_v352r3R3]  -> results/v352/f1_lc3_summary{sfx}.json, results/v352/tables/f1_lc3_summary{sfx}.md"""
import sys, json, hashlib
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
POSES = ["000", "045", "090", "135", "180", "225", "270", "315"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def one(p, sfx):
    fn = RES / f"f1_post_lc3_pose_stop{p}{sfx}.json"
    d = json.loads(fn.read_text())
    ms = [m for m in d["margins"] if m.get("case", "LC3") == "LC3" and m.get("MS") is not None]
    reg = sorted((m for m in ms if m.get("set") == "regular"), key=lambda m: m["MS"])
    alln = sorted((m for m in ms if m.get("set") == "all"), key=lambda m: m["MS"])
    ce = d["connectors_envelope"]
    grp = lambda pre: max(v["max_abs_N"] for k, v in ce.items() if k.startswith(pre))
    shear, hole = 0.0, None
    for h, v in d["icd_envelope"].items():
        s = v.get("max_shear_N", v.get("shear_max_N"))
        if s is not None and s > shear:
            shear, hole = s, h
    rec = lambda m: {"part": m["part"], "MS": m["MS"], "MS_ult": m.get("MS_ult"), "node": m.get("node"), "class": m.get("node_class"),
                     "class_detail": m.get("node_class_detail"), "d_class_mm": m.get("d_class_mm"), "vm_MPa": m.get("vm_MPa")}
    return {"pose": f"stop{p}", "post": fn.name, "post_sha16": sha16(fn), "pose_deg": d["pose_deg"], "fb_run_range_N": d["fb_run_range_N"],
            "rod_max_compression_N": d["rod_max_compression_N"],
            "rod_max_abs_N": {k: ce[k]["value_N"] for k in ("ROD_1", "ROD_2")},
            "moment_path_residual_rel": d["checks"]["equilibrium_residual_rel"],
            "lowest_regular": [rec(m) for m in reg[:4]], "lowest_all_node": [rec(m) for m in alln[:4]],
            "inner_needle_cup_max_component_N": grp("BRG_IN"), "inner_washer_N": grp("WSH_IN"),
            "outer_needle_cup_max_component_N": grp("BRG_OUT"), "outer_washer_N": grp("WSH_OUT"),
            "icd_max_hole_shear_N": shear, "icd_hole": hole, "icd_totals_envelope": d["icd_totals_envelope"]}


def main(argv):
    o = dict(a.split("=", 1) for a in argv)
    sfx = o.get("sfx", "_v352r3R3")
    rows = [one(p, sfx) for p in POSES]
    out = {"tag": "SIM (FE) / DERIVED envelopes", "sfx": sfx, "doc": __doc__.split("usage:")[0].strip(), "rows": rows}
    (RES / "v352").mkdir(exist_ok=True)
    (RES / "v352" / f"f1_lc3_summary{sfx}.json").write_text(json.dumps(out, indent=1))
    f = lambda x: "n/a" if x is None else f"{x:+.3f}"
    L = ["| pose | fb_run N | max rod abs N (- compr / + tens) | lowest regular MS y / u (part) | lowest all-node MS y / u (part, class, d mm) | "
         "inner cup / washer N | outer cup / washer N | max hole shear N | moment residual |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rm = max(r["rod_max_abs_N"].items(), key=lambda kv: abs(kv[1]))
        low = "; ".join(f"{m['part']} {f(m['MS'])} / {f(m['MS_ult'])}" for m in r["lowest_regular"][:3])
        lowa = "; ".join(f"{m['part']} {f(m['MS'])} / {f(m['MS_ult'])} ({m['class']}{', ' + str(m['d_class_mm']) if m['d_class_mm'] is not None else ''})"
                         for m in r["lowest_all_node"][:3])
        mark = " (GM-02 matrix cell: p = 1 bound +0.400 / +0.206)" if r["pose"] == "stop045" else ""
        L.append(f"| {r['pose']}{mark} | {r['fb_run_range_N'][0]:.0f}-{r['fb_run_range_N'][1]:.0f} | {rm[1]:+.1f} ({rm[0]}) | {low} | {lowa} | "
                 f"{r['inner_needle_cup_max_component_N']:.0f} / {r['inner_washer_N']:.0f} | {r['outer_needle_cup_max_component_N']:.0f} / {r['outer_washer_N']:.0f} | "
                 f"{r['icd_max_hole_shear_N']:.0f} ({r['icd_hole']}) | {100 * r['moment_path_residual_rel']:.1f} % |")
    (RES / "v352" / "tables").mkdir(exist_ok=True)
    (RES / "v352" / "tables" / f"f1_lc3_summary{sfx}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
