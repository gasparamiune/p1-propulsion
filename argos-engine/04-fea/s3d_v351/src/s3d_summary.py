"""F2 summary: S-3D gimbal strength on CAD v3.5.1 (fea3d 2026-10-19).

Collects results/s3d_pose_<cone>_c71.json (post_s3d.py: GS, TD, LC6, LC2F at the 9 range-cone poses), the F1 stop-pose runaway case
(SR = F1 LC3, results/f1_post_lc3_pose_stopXXX_c71.json, L1 regular set, plus the lever-root R3 refinements f1_lever_root_GM0x_c71.json)
and FA1T (results/f1_post_fa1_c71.json), and writes results/s3d_summary_v351.json + results/tables/s3d_*.md.
usage: s3d_summary.py
"""
from __future__ import annotations
import json
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
TAB = RES / "tables"
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
STOPS = [f"stop{d:03d}" for d in range(0, 360, 45)]
GIMBAL = ["GM-01", "GM-02", "GM-03", "GM-16a", "GM-16b", "GM-08a", "GM-08b", "GM-09", "GM-10", "GM-13", "GM-14"]
CASES = ["GS", "TD", "LC6", "LC2F"]


def f(x):
    return "n/a" if x is None else (f"{x:+.3f}" if abs(x) < 100 else ">+99")


def main():
    cone = {}
    for p in CONES:
        fp = RES / f"s3d_pose_{p}_c71.json"
        if fp.exists():
            cone[p] = json.loads(fp.read_text())
    out = {"tag": "SIM (FE, asm v1.2) / DERIVED envelopes", "cone_poses_present": list(cone), "cone_poses_missing": [p for p in CONES if p not in cone],
           "per_case": {}, "rods": {}, "connectors": {}, "icd": {}, "ang_accel_GS_rad_s2": {}}
    for c in CASES:
        best = {}
        for p, d in cone.items():
            for r in d["cases"][c]["margins"]:
                if r["set"] != "regular":
                    continue
                k = r["part"]
                if k not in best or r["MS"] < best[k]["MS"]:
                    best[k] = {"MS": r["MS"], "MS_ult": r.get("MS_ult"), "pose": p, "vm_MPa": r.get("vm_MPa"), "xyz_mm": r.get("xyz_mm"),
                               "T_C": r.get("T_C")}
                if r.get("MS_ult") is not None and (best[k].get("MS_ult_min") is None or r["MS_ult"] < best[k]["MS_ult_min"]):
                    best[k]["MS_ult_min"] = r["MS_ult"]
        out["per_case"][c] = best
        out["rods"][c] = {p: d["cases"][c]["rod_max_abs_N"] for p, d in cone.items()}
        if c != "TD":
            env = {}
            for p, d in cone.items():
                for lab, v in d["cases"][c]["connectors_envelope"].items():
                    if lab.startswith(("BRG", "WSH", "ROD")):
                        base = lab.split("_k")[0]
                        if v["max_abs_N"] > env.get(base, (0, ""))[0]:
                            env[base] = (v["max_abs_N"], p)
                    elif lab.startswith("JF") or lab.startswith("PDF"):
                        pass
            out["connectors"][c] = {k: {"max_abs_component_N": v[0], "pose": v[1]} for k, v in env.items()}
            ic = max(((h["max_shear_N"], hn, p) for p, d in cone.items() for hn, h in d["cases"][c]["icd_envelope"].items()), default=None)
            out["icd"][c] = {"max_hole_shear_N": ic[0], "hole": ic[1], "pose": ic[2]} if ic else None
    for p, d in cone.items():
        sc = d["cases"]["GS"].get("subcases") or []
        if sc:
            out["ang_accel_GS_rad_s2"][p] = [min(s["engine_ang_accel_rad_s2"] for s in sc), max(s["engine_ang_accel_rad_s2"] for s in sc)]
    # SR = F1 LC3 stop poses (L1 regular) + lever-root refinement; FA1T
    sr = {}
    for p in STOPS:
        fp = RES / f"f1_post_lc3_pose_{p}_c71.json"
        if not fp.exists():
            continue
        d = json.loads(fp.read_text())
        for r in d["margins"]:
            if r["set"] == "regular" and (r["part"] not in sr or r["MS"] < sr[r["part"]]["MS"]):
                sr[r["part"]] = {"MS": r["MS"], "MS_ult": r.get("MS_ult"), "pose": p}
    for part in ("GM-01", "GM-02"):
        fp = RES / f"f1_lever_root_{part.replace('-', '')}_c71.json"
        if fp.exists():
            lv = json.loads(fp.read_text())["levels"]
            r3 = [v for k, v in lv.items() if "r3" in k]
            if r3:
                sr[part]["R3_MS"], sr[part]["R3_MS_ult"] = r3[0]["MS_regular"], r3[0]["MS_ult_regular"]
    out["per_case"]["SR"] = sr
    fa = json.loads((RES / "f1_post_fa1_c71.json").read_text())["states"]["A1_22.2"]["cases"]["FA1T"]["margins"]
    out["per_case"]["FA1T"] = {r["part"]: {"MS": r["MS"], "MS_ult": r.get("MS_ult"), "pose": "neutral"} for r in fa if r["set"] == "regular"}
    (RES / "s3d_summary_v351.json").write_text(json.dumps(out, indent=1, default=float))
    # tables
    L = ["| part | GS y / u (pose) | TD y / u (pose) | LC6 y / u | LC2F y / u (SF 1.0 / 1.5) | SR = F1 LC3 runaway y / u (pose), L1 | SR lever root R3 | FA1T y / u |",
         "|---|---|---|---|---|---|---|---|"]
    pc = out["per_case"]
    for part in GIMBAL + ["TC-01"]:
        def cell(c, show_pose=True):
            r = pc.get(c, {}).get(part)
            if not r:
                return "-"
            u = r.get("MS_ult_min", r.get("MS_ult"))
            return f"{f(r['MS'])} / {f(u)}" + (f" ({r['pose']})" if show_pose and r.get("pose") else "")
        s = pc["SR"].get(part, {})
        r3 = f"{f(s.get('R3_MS'))} / {f(s.get('R3_MS_ult'))}" if "R3_MS" in s else "-"
        L.append(f"| {part} | {cell('GS')} | {cell('TD')} | {cell('LC6', False)} | {cell('LC2F', False)} | {cell('SR')} | {r3} | {cell('FA1T', False)} |")
    TAB.mkdir(exist_ok=True)
    (TAB / "s3d_part_margins_v351.md").write_text("\n".join(L) + "\n")
    R = ["| pose | GS rods (N) | GS engine ang. accel. rad/s2 | TD max rod abs N | LC6 max rod abs N | LC2F max rod abs N |", "|---|---|---|---|---|---|"]
    for p in cone:
        aa = out["ang_accel_GS_rad_s2"].get(p, [None, None])
        R.append(f"| {p} | +/-{cone[p]['F_d_N']:.0f} | {aa[0]:.0f}-{aa[1]:.0f} | {max(out['rods']['TD'][p].values()):.0f} | "
                 f"{max(out['rods']['LC6'][p].values()):.0f} | {max(out['rods']['LC2F'][p].values()):.0f} |")
    (TAB / "s3d_rods_v351.md").write_text("\n".join(R) + "\n")
    C = ["| case | inner cup max comp. N | inner washer N | outer cup N | outer washer N | max hole shear N (hole, pose) |", "|---|---|---|---|---|---|"]
    for c in ("GS", "LC6", "LC2F"):
        cc = out["connectors"].get(c, {})
        g = lambda pre: max((v["max_abs_component_N"] for k, v in cc.items() if k.startswith(pre)), default=0.0)
        ic = out["icd"].get(c) or {}
        C.append(f"| {c} | {g('BRG_IN'):.0f} | {g('WSH_IN'):.0f} | {g('BRG_OUT'):.0f} | {g('WSH_OUT'):.0f} | "
                 f"{ic.get('max_hole_shear_N', 0):.0f} ({ic.get('hole')}, {ic.get('pose')}) |")
    (TAB / "s3d_connectors_v351.md").write_text("\n".join(C) + "\n")
    print("\n".join(L)); print(); print("\n".join(R)); print(); print("\n".join(C))


if __name__ == "__main__":
    main()
