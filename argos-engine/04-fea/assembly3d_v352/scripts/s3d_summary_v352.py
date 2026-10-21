"""F2 summary on CAD v3.5.2 (fea3d 2026-10-20; report section 9B): S-3D gimbal strength at the 9 range-cone poses on the rev-3 levers at R3.

Collects results/s3d_pose_<cone>_v352r3R3.json (post_s3d.py: GS, TD, LC6, LC2F), the F1 stop-pose runaway case (SR = F1 LC3,
results/f1_post_lc3_pose_stopXXX_v352r3R3.json) and FA1T (results/f1_post_fa1v352n.json, A1_22.2).  Per part and case: the lowest
REGULAR and the lowest ALL-NODE margin (CHANGELOG 234 (4)) with pose, node class and distance.  The GM-01 / GM-02 lever-root cells
are taken from results/v352/lever_root_table_v352.json (ACCEPTED lead 20:44:07Z (1)): the R3 value, or the p = 1 bound where R2 -> R3
exceeded 5 % (GS GM-02 alpha- +0.591 / +0.371; alpha+ GM-02 is also a p = 1 cell but does not govern).  Same quantities as the v3.5.1
s3d_summary.py (results/s3d_summary_v351.json), which is not changed.  Read-only on the posts.  Tags: SIM (FE) / DERIVED (envelopes, p = 1).
usage: s3d_summary_v352.py  -> results/v352/s3d_summary_v352.json, results/v352/tables/s3d_{part_margins,rods,connectors}_v352.md"""
from __future__ import annotations
import json, hashlib
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
OUT = RES / "v352"
TAB = OUT / "tables"
SFX = "_v352r3R3"
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
STOPS = [f"stop{d:03d}" for d in range(0, 360, 45)]
GIMBAL = ["GM-01", "GM-02", "GM-03", "GM-16a", "GM-16b", "GM-08a", "GM-08b", "GM-09", "GM-10", "GM-13", "GM-14"]
CASES = ["GS", "TD", "LC6", "LC2F"]


def f(x):
    return "n/a" if x is None else (f"{x:+.3f}" if abs(x) < 100 else ">+99")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def low(recs, pose_of):
    """lowest regular and all-node record per part (MS_y and, separately, MS_u)."""
    best = {}
    for r, pose in recs:
        if r.get("MS") is None:
            continue
        k = (r["part"], r["set"])
        b = best.setdefault(k, {"MS": None, "MS_ult": None})
        if b["MS"] is None or r["MS"] < b["MS"]:
            b.update(MS=r["MS"], pose=pose, node=r.get("node"), cls=r.get("node_class"), detail=r.get("node_class_detail"),
                     d_mm=r.get("d_class_mm"), vm_MPa=r.get("vm_MPa"), T_C=r.get("T_C"))
        if r.get("MS_ult") is not None and (b["MS_ult"] is None or r["MS_ult"] < b["MS_ult"]):
            b.update(MS_ult=r["MS_ult"], pose_u=pose)
    return best


def main():
    files = {}
    cone = {}
    for p in CONES:
        fp = RES / f"s3d_pose_{p}{SFX}.json"
        if fp.exists():
            cone[p] = json.loads(fp.read_text())
            files[fp.name] = sha16(fp)
    lt = json.loads((OUT / "lever_root_table_v352.json").read_text())
    files["v352/lever_root_table_v352.json"] = sha16(OUT / "lever_root_table_v352.json")
    out = {"tag": "SIM (FE, asm v1.3, rev-3 levers at R3) / DERIVED envelopes and p = 1 cells", "doc": __doc__.split("usage:")[0].strip(),
           "cone_poses_present": list(cone), "cone_poses_missing": [p for p in CONES if p not in cone],
           "per_case": {}, "rods": {}, "connectors": {}, "icd": {}, "ang_accel_GS_rad_s2": {}, "lever_root_cells": {}, "files_sha16": files}
    for c in CASES:
        best = low([(r, p) for p, d in cone.items() for r in d["cases"][c]["margins"]], None)
        out["per_case"][c] = {f"{k[0]}|{k[1]}": v for k, v in best.items()}
        out["rods"][c] = {p: d["cases"][c]["rod_max_abs_N"] for p, d in cone.items()}
        if c != "TD":
            env = {}
            for p, d in cone.items():
                for lab, v in d["cases"][c]["connectors_envelope"].items():
                    if lab.startswith(("BRG", "WSH", "ROD")):
                        base = lab.split("_k")[0]
                        if v["max_abs_N"] > env.get(base, (0, ""))[0]:
                            env[base] = (v["max_abs_N"], p)
            out["connectors"][c] = {k: {"max_abs_component_N": v[0], "pose": v[1]} for k, v in env.items()}
            ic = max(((h["max_shear_N"], hn, p) for p, d in cone.items() for hn, h in d["cases"][c]["icd_envelope"].items()), default=None)
            out["icd"][c] = {"max_hole_shear_N": ic[0], "hole": ic[1], "pose": ic[2]} if ic else None
    for p, d in cone.items():
        sc = d["cases"]["GS"].get("subcases") or []
        if sc and all("engine_ang_accel_rad_s2" in s for s in sc):
            out["ang_accel_GS_rad_s2"][p] = [min(s["engine_ang_accel_rad_s2"] for s in sc), max(s["engine_ang_accel_rad_s2"] for s in sc)]
    # lever-root cells (accepted table): GS at the cones, LC3 (= SR) at the stops
    for kind, key in (("cones", "GS"), ("stops", "SR")):
        for lever in ("GM-01", "GM-02"):
            g = lt["governing"][f"{kind}|{lever}|all"]
            out["lever_root_cells"][f"{key}|{lever}"] = {"cold": [g["cold_cell_MS_y"], g["cold_cell_MS_u"]], "cold_pose": g["cold_cell_pose"],
                                                        "cold_rule": g["cold_cell_rule"], "hot": [g["hot_cell_MS_y"], g["hot_cell_MS_u"]],
                                                        "hot_pose": g["hot_cell_pose"], "hot_rule": g["hot_cell_rule"], "hot_base_state": g["hot_base_state"]}
    # SR = F1 LC3 stop poses (R3), FA1T (fa1v352n)
    sr = []
    for p in STOPS:
        fp = RES / f"f1_post_lc3_pose_{p}{SFX}.json"
        if fp.exists():
            files[fp.name] = sha16(fp)
            sr += [(r, p) for r in json.loads(fp.read_text())["margins"] if r.get("case", "LC3") == "LC3"]
    out["per_case"]["SR"] = {f"{k[0]}|{k[1]}": v for k, v in low(sr, None).items()}
    fa = RES / "f1_post_fa1v352n.json"
    files[fa.name] = sha16(fa)
    fr = json.loads(fa.read_text())["states"]["A1_22.2"]["cases"]["FA1T"]["margins"]
    out["per_case"]["FA1T"] = {f"{k[0]}|{k[1]}": v for k, v in low([(r, "neutral") for r in fr], None).items()}
    TAB.mkdir(parents=True, exist_ok=True)
    (OUT / "s3d_summary_v352.json").write_text(json.dumps(out, indent=1, default=float))
    pc = out["per_case"]

    def cell(c, part, s, show_pose=True):
        if c in ("GS", "SR") and part in ("GM-01", "GM-02"):
            lr = out["lever_root_cells"][f"{c}|{part}"]
            tagp = " p1" if "p = 1" in lr["cold_rule"] else ""
            return f"{f(lr['cold'][0])} / {f(lr['cold'][1])} ({lr['cold_pose']}{tagp})"
        r = pc.get(c, {}).get(f"{part}|{s}")
        if not r:
            return "-"
        cl = f", {r['cls']} {r['d_mm']}" if s == "all" and r.get("cls") not in (None, "regular") else ""
        return f"{f(r['MS'])} / {f(r.get('MS_ult'))}" + (f" ({r['pose']}{cl})" if show_pose and r.get("pose") else (f" ({r['cls']} {r['d_mm']})" if cl else ""))

    L = ["| part | set | GS y / u (pose) | TD y / u (pose) | LC6 y / u | LC2F y / u (SF 1.0 / 1.5) | SR = F1 LC3 y / u (pose) | FA1T y / u |",
         "|---|---|---|---|---|---|---|---|"]
    for part in GIMBAL + ["TC-01"]:
        for s in ("regular", "all"):
            L.append(f"| {part} | {s} | {cell('GS', part, s)} | {cell('TD', part, s)} | {cell('LC6', part, s, False)} | {cell('LC2F', part, s, False)} | "
                     f"{cell('SR', part, s)} | {cell('FA1T', part, s, False)} |")
    (TAB / "s3d_part_margins_v352.md").write_text("\n".join(L) + "\n")
    R = ["| pose | GS rods (N) | GS engine ang. accel. rad/s2 | TD max rod abs N | LC6 max rod abs N | LC2F max rod abs N |", "|---|---|---|---|---|---|"]
    for p in cone:
        aa = out["ang_accel_GS_rad_s2"].get(p)
        R.append(f"| {p} | +/-{cone[p]['F_d_N']:.0f} | {(f'{aa[0]:.0f}-{aa[1]:.0f}') if aa else 'n/a'} | {max(out['rods']['TD'][p].values()):.0f} | "
                 f"{max(out['rods']['LC6'][p].values()):.0f} | {max(out['rods']['LC2F'][p].values()):.0f} |")
    (TAB / "s3d_rods_v352.md").write_text("\n".join(R) + "\n")
    C = ["| case | inner cup max comp. N | inner washer N | outer cup N | outer washer N | max hole shear N (hole, pose) |", "|---|---|---|---|---|---|"]
    for c in ("GS", "LC6", "LC2F"):
        cc = out["connectors"].get(c, {})
        g = lambda pre: max((v["max_abs_component_N"] for k, v in cc.items() if k.startswith(pre)), default=0.0)
        ic = out["icd"].get(c) or {}
        C.append(f"| {c} | {g('BRG_IN'):.0f} | {g('WSH_IN'):.0f} | {g('BRG_OUT'):.0f} | {g('WSH_OUT'):.0f} | "
                 f"{ic.get('max_hole_shear_N', 0):.0f} ({ic.get('hole')}, {ic.get('pose')}) |")
    (TAB / "s3d_connectors_v352.md").write_text("\n".join(C) + "\n")
    (OUT / "s3d_summary_v352.json").write_text(json.dumps(out, indent=1, default=float))
    print("\n".join(L)); print(); print("\n".join(R)); print(); print("\n".join(C))


if __name__ == "__main__":
    main()
