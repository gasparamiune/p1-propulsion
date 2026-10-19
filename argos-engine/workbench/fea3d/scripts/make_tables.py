"""FEA3D F1 tables: per-part minimum MS over every case (CSV + markdown) and airframe-interface reaction tables (fea3d successor 2026-10-15).

Inputs (results/): f1_post_lc1v351_design_rigid.json (LC1, 4 S-AX thermal states), f1_post_fa1_v351.json (FA1Q/D/U/S + FA1T when merged
with tz_v351), f1_post_lc3_pose_stopXXX.json (LC3 cold, 8 stop azimuths), f1_lc3_hot_bound.json (LC3 hot lower bound),
optional f1_post_tc03_thread.json (TB1 thread variant), f1_post_lc1v351_compliant.json, f1_post_lc3_pose_stop045_compliant.json.
Regular node set (outside 1 mm of idealisation singularities) unless a column says 'all'.  MS = margin of safety, mm / N / MPa / C.
"""
from __future__ import annotations
import json, csv, math
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
OUT = RES / "tables"
OUT.mkdir(exist_ok=True)
POSES = [f"pose_stop{d:03d}" for d in range(0, 360, 45)]


def load(name):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None


def rows_of(d, case, sset="regular"):
    out = []
    if not d:
        return out
    for st, sd in d["states"].items():
        c = sd["cases"].get(case)
        if c:
            out += [dict(r, state=st) for r in c["margins"] if r["set"] == sset]
    return out


def minrow(rows, part, key="MS"):
    rr = [r for r in rows if r["part"] == part and r.get(key) is not None]
    return min(rr, key=lambda r: r[key]) if rr else None


def f(x, n=3):
    return "n/a" if x is None else (f"{x:+.{n}f}" if abs(x) < 1e3 else ">+999")


def main():
    lc1 = load("f1_post_lc1v351_design_rigid.json")
    fa1 = load("f1_post_fa1_v351.json")
    thr = load("f1_post_tc03_thread.json")
    cmp_ = load("f1_post_lc1v351_compliant.json")
    lc3 = {p: load(f"f1_post_lc3_{p}.json") for p in POSES}
    lc3 = {p: v for p, v in lc3.items() if v}
    hot = load("f1_lc3_hot_bound.json")
    parts = sorted({r["part"] for r in rows_of(lc1, "LC1")}, key=lambda s: (s[:2] != "TC", s[:2] != "NZ", s))
    L1r, L1a = rows_of(lc1, "LC1"), rows_of(lc1, "LC1", "all")
    FA = {c: rows_of(fa1, c) for c in ("FA1Q", "FA1D", "FA1U", "FA1S", "FA1T")}
    THr = rows_of(thr, "LC1") if thr else []
    CPr = rows_of(cmp_, "LC1") if cmp_ else []
    L3 = []
    for p, d in lc3.items():
        L3 += [dict(r, pose=p) for r in d["margins"] if r["set"] == "regular"]
    table = []
    for pt in parts:
        a = minrow(L1r, pt)
        au = minrow(L1r, pt, "MS_ult")
        ap = minrow(L1r, pt, "MS_primary_only")
        apq = minrow(L1r, pt, "MS_PQ_nodal_shakedown")
        aa = minrow(L1a, pt)
        row = {"part": pt, "material": a["material"] if a else None, "role": a["role"] if a else None,
               "T_part_max_C_LC1": max((r["T_part_max_C"] for r in L1r if r["part"] == pt), default=None),
               "T_limit_C": a.get("T_limit_C") if a else None,
               "T_limit_exceeded_LC1": any(r.get("T_limit_exceeded") for r in L1r if r["part"] == pt),
               "LC1_MS_y": a["MS"] if a else None, "LC1_state": a["state"] if a else None, "LC1_rtz": a["r_theta_z"] if a else None,
               "LC1_MS_u": au["MS_ult"] if au else None, "LC1_MS_primary": ap["MS_primary_only"] if ap else None,
               "LC1_MS_PQ_shakedown": apq["MS_PQ_nodal_shakedown"] if apq else None, "LC1_MS_y_allnodes": aa["MS"] if aa else None,
               "LC1_vm_MPa": a["vm_MPa"] if a else None, "LC1_vm_thermal_MPa": a["vm_thermal_MPa"] if a else None}
        for c, rr in FA.items():
            r_ = minrow(rr, pt)
            ru = minrow(rr, pt, "MS_ult")
            row[f"{c}_MS_y"] = r_["MS"] if r_ else None
            row[f"{c}_MS_u"] = ru["MS_ult"] if ru else None
            row[f"{c}_rtz"] = r_["r_theta_z"] if r_ else None
        r3 = minrow(L3, pt)
        r3u = minrow(L3, pt, "MS_ult")
        row["LC3cold_MS_y"] = r3["MS"] if r3 else None
        row["LC3cold_MS_u"] = r3u["MS_ult"] if r3u else None
        row["LC3cold_pose"] = r3["pose"] if r3 else None
        row["LC3cold_rtz"] = r3["r_theta_z"] if r3 else None
        if hot and pt in hot["summary_min_over_states_regular"]:
            h = hot["summary_min_over_states_regular"][pt]
            row["LC3hot_bound_MS_y"], row["LC3hot_bound_MS_u"], row["LC3hot_bound_state"] = h["MS_bound"], h["MS_ult_bound"], h["state"]
        if THr:
            t = minrow(THr, pt)
            tu = minrow(THr, pt, "MS_ult")
            row["LC1_thread_MS_y"] = t["MS"] if t else None
            row["LC1_thread_MS_u"] = tu["MS_ult"] if tu else None
            row["LC1_thread_state"] = t["state"] if t else None
        if CPr:
            t = minrow(CPr, pt)
            row["LC1_compliant_B1_21.65_MS_y"] = t["MS"] if t else None
        cand = [(row.get(k), k) for k in ("LC1_MS_y", "LC1_MS_u", "FA1Q_MS_y", "FA1Q_MS_u", "FA1D_MS_y", "FA1U_MS_u", "FA1S_MS_y", "FA1S_MS_u",
                                          "FA1T_MS_y", "FA1T_MS_u", "LC3cold_MS_y", "LC3cold_MS_u", "LC3hot_bound_MS_y", "LC3hot_bound_MS_u")
                if row.get(k) is not None]
        mn = min(cand) if cand else (None, None)
        row["min_MS"], row["min_MS_column"] = mn
        table.append(row)
    keys = list(dict.fromkeys(k for r in table for k in r))
    with open(OUT / "f1_part_margins.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in table:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
    (OUT / "f1_part_margins.json").write_text(json.dumps(table, indent=1))
    # markdown
    hdr = ("| Part | Material | LC1 MS y / u (state) | LC1 primary | LC1 P+Q 2Fty | FA1Q y / u | FA1D y | FA1U u | FA1S y / u | FA1T y / u | "
           "LC3 cold y / u (pose) | LC3 hot bound y / u | min MS (column) |")
    md = [hdr, "|" + "---|" * 13]
    for r in table:
        md.append(f"| {r['part']} | {r['material']} | {f(r['LC1_MS_y'])} / {f(r['LC1_MS_u'])} ({r['LC1_state']}) | {f(r['LC1_MS_primary'])} | "
                  f"{f(r['LC1_MS_PQ_shakedown'])} | {f(r['FA1Q_MS_y'])} / {f(r['FA1Q_MS_u'])} | {f(r['FA1D_MS_y'])} | {f(r['FA1U_MS_u'])} | "
                  f"{f(r['FA1S_MS_y'])} / {f(r['FA1S_MS_u'])} | {f(r.get('FA1T_MS_y'))} / {f(r.get('FA1T_MS_u'))} | "
                  f"{f(r['LC3cold_MS_y'])} / {f(r['LC3cold_MS_u'])} ({(r['LC3cold_pose'] or '').replace('pose_', '')}) | "
                  f"{f(r.get('LC3hot_bound_MS_y'))} / {f(r.get('LC3hot_bound_MS_u'))} | {f(r['min_MS'])} ({r['min_MS_column']}) |")
    (OUT / "f1_part_margins.md").write_text("\n".join(md) + "\n")
    # ------------------------------------------------------------------ ICD
    icd = {}

    def holes_env(d, case):
        env = {}
        if not d:
            return env
        for st, sd in d["states"].items():
            c = sd["cases"].get(case)
            if not c:
                continue
            for sc in c["icd"]:
                for h in sc["holes"]:
                    e = env.setdefault(h["hole"], {"x_mm": h["x_mm"], "max_shear_N": 0.0, "max_radial_out_N": -1e9, "min_radial_N": 1e9,
                                                   "max_abs_axial_N": 0.0, "max_abs_tangential_N": 0.0})
                    e["max_shear_N"] = max(e["max_shear_N"], h["shear_in_screw_N"])
                    e["max_radial_out_N"] = max(e["max_radial_out_N"], h["radial_N"])
                    e["min_radial_N"] = min(e["min_radial_N"], h["radial_N"])
                    e["max_abs_axial_N"] = max(e["max_abs_axial_N"], abs(h["axial_N"]))
                    e["max_abs_tangential_N"] = max(e["max_abs_tangential_N"], abs(h["tangential_N"]))
        return env

    def totals(d, case):
        out = []
        if not d:
            return out
        for st, sd in d["states"].items():
            c = sd["cases"].get(case)
            if c:
                for sc in c["icd"]:
                    out.append({"state": st, "subcase": sc["subcase"], "F_total_on_airframe_N": sc["F_total_on_airframe_N"],
                                "M_total_about_pivot_Nmm": sc["M_total_about_pivot_Nmm"]})
        return out
    icd["LC1_rigid"] = {"holes": holes_env(lc1, "LC1"), "totals": totals(lc1, "LC1")}
    if cmp_:
        icd["LC1_compliant"] = {"holes": holes_env(cmp_, "LC1"), "totals": totals(cmp_, "LC1")}
    for c in ("FA1S", "FA1T"):
        icd[f"{c}_rigid"] = {"holes": holes_env(fa1, c), "totals": totals(fa1, c)}
    env3 = {}
    for p, d in lc3.items():
        for h, e in d["icd_envelope"].items():
            g = env3.setdefault(h, {"x_mm": e["x_mm"], "max_shear_N": 0.0, "max_radial_out_N": -1e9, "min_radial_N": 1e9,
                                    "max_abs_axial_N": 0.0, "max_abs_tangential_N": 0.0, "pose_max_shear": None})
            if e["max_shear_N"] > g["max_shear_N"]:
                g["max_shear_N"], g["pose_max_shear"] = e["max_shear_N"], p
            g["max_radial_out_N"] = max(g["max_radial_out_N"], e["max_radial_out_N"])
            g["min_radial_N"] = min(g["min_radial_N"], e["min_radial_N"])
            g["max_abs_axial_N"] = max(g["max_abs_axial_N"], e["max_abs_axial_N"])
            g["max_abs_tangential_N"] = max(g["max_abs_tangential_N"], e["max_abs_tangential_N"])
    icd["LC3_rigid_8poses"] = {"holes": env3, "totals_envelope": {p: d["icd_totals_envelope"] for p, d in lc3.items()}}
    c45 = load("f1_post_lc3_pose_stop045_compliant.json")
    if c45:
        icd["LC3_compliant_stop045"] = {"holes": c45["icd_envelope"], "totals_envelope": c45["icd_totals_envelope"]}
    (OUT / "f1_icd_airframe.json").write_text(json.dumps(icd, indent=1))
    md = ["| Case | max screw shear N (hole) | max radial pull-out N (hole) | max push-in N | max |axial| N | sum F on airframe N (max |Fx|, |Fy|, |Fz|) |",
          "|---|---|---|---|---|---|"]
    for k, v in icd.items():
        H = v["holes"]
        if not H:
            continue
        hs = max(H.items(), key=lambda kv: kv[1]["max_shear_N"])
        hr = max(H.items(), key=lambda kv: kv[1]["max_radial_out_N"])
        hp = min(H.items(), key=lambda kv: kv[1]["min_radial_N"])
        ha = max(H.items(), key=lambda kv: kv[1]["max_abs_axial_N"])
        if "totals" in v and v["totals"]:
            tf = [max(abs(t["F_total_on_airframe_N"][i]) for t in v["totals"]) for i in range(3)]
        else:
            tf = [max(t["max_abs_F_on_airframe_N"][i] for t in v["totals_envelope"].values()) for i in range(3)] if "totals_envelope" in v and isinstance(next(iter(v["totals_envelope"].values()), None), dict) and "max_abs_F_on_airframe_N" in next(iter(v["totals_envelope"].values())) else v.get("totals_envelope", {}).get("max_abs_F_on_airframe_N", [None] * 3)
        md.append(f"| {k} | {hs[1]['max_shear_N']:.1f} ({hs[0]}) | {hr[1]['max_radial_out_N']:.1f} ({hr[0]}) | {-hp[1]['min_radial_N']:.1f} ({hp[0]}) | "
                  f"{ha[1]['max_abs_axial_N']:.1f} ({ha[0]}) | " + ", ".join("n/a" if x is None else f"{x:.1f}" for x in tf) + " |")
    (OUT / "f1_icd_airframe.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(open(OUT / "f1_part_margins.md").read())


if __name__ == "__main__":
    main()
