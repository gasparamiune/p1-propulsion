"""Engine mounting data for the datasheet (fea3d 2026-10-19; was the ICD-AIRFRAME v2.1 export: ICD removed from scope by CHANGELOG 222, the
data are kept as ENGINE data; the earlier tables/icd_airframe_v21.md and results/icd_airframe_v21_fea3d.json stay as published and are no
longer rewritten): per-hole screw shear / axial / radial envelopes and the
resultant of each airframe ring (GM-09 forward ring z +27, GM-10 aft ring z -94.8; 8 radial M5 each) per load case, from the
solved unit-step reactions (ccx RF at the 16 hole node sets) re-combined with every sub-case of the posted cases (SIM, asm v1.2).

Sign: forces are those the ENGINE MODULE applies ON THE AIRFRAME; radial + = outward (screw pull-out), axial = +Z (forward),
shear = hypot(tangential, axial) in the screw (radial screws); moments about the gimbal pivot (engine frame origin), N mm.
usage: icd_export.py            -> results/engine_mount_data_v351.json, results/tables/engine_mount_data_v351.md
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import post_lc3 as PL       # noqa: E402

RES = PF.RES
STOPS = [f"pose_stop{d:03d}_c71" for d in range(0, 360, 45)]
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]


def lc3_coefs(js):
    psi = math.radians(js["psi_ang_deg"])
    out = []
    for i_ in js["subcases"]:
        ph = math.radians(i_["lat_dir_deg"])
        out.append({"OP": PL.PC_MAX, "GX": PL.G_LAT * math.cos(ph), "GY": PL.G_LAT * math.sin(ph), "GZ": i_["GZ_g"],
                    "EAX": i_["ang_sign"] * PL.ALPHA * math.cos(psi), "EAY": i_["ang_sign"] * PL.ALPHA * math.sin(psi), "BUMP": i_["fb_N"]})
    return out


def sources():
    """[(case label, airframe, [(run, state, [coef dicts])])]"""
    S = []
    lc1 = json.loads((RES / "f1_post_lc1v351_c71.json").read_text())
    S.append(("LC1", "rigid", [("lc1v351_c71", st, sd["cases"]["LC1"]["subcases"]) for st, sd in lc1["states"].items()]))
    fp = RES / "f1_post_lc1v351_compliant_c71.json"
    if fp.exists():
        d = json.loads(fp.read_text())
        S.append(("LC1", "compliant", [("lc1v351_compliant_c71", st, sd["cases"]["LC1"]["subcases"]) for st, sd in d["states"].items()]))
    fa = json.loads((RES / "f1_post_fa1_c71.json").read_text())["states"]["A1_22.2"]["cases"]
    for c in ("FA1Q", "FA1S", "FA1T"):
        S.append((c, "rigid", [("fa1_c71", "A1_22.2", fa[c]["subcases"])]))
    S.append(("LC3 (8 stop poses, runaway / hold)", "rigid",
              [(p, "B1_21.65", lc3_coefs(json.loads((RES / f"f1_post_lc3_{p}.json").read_text()))) for p in STOPS]))
    fp = RES / "f1_post_lc3_pose_stop045_compliant_c71.json"
    if fp.exists():
        S.append(("LC3 stop045", "compliant", [("pose_stop045_compliant_c71", "B1_21.65", lc3_coefs(json.loads(fp.read_text())))]))
    cones = {p: RES / f"s3d_pose_{p}_c71.json" for p in CONES}
    cones = {p: json.loads(f.read_text()) for p, f in cones.items() if f.exists()}
    if cones:
        for c, lab in (("GS", "F2 GS servo stall (9 cone poses)"), ("TD0", "F2 TD touchdown Pc 0"), ("TDP", "F2 TD touchdown Pc max"),
                       ("LC6", "F2 LC6 hard landing 10 g"), ("LC2F", "F2 LC2F stuck pintle")):
            S.append((lab, "rigid", [(f"pose_{p}_c71", "B1_21.65", d["cases"][c]["subcase_coefs"]) for p, d in cones.items()
                                     if d["cases"][c].get("subcase_coefs")]))
    return S


def main():
    out = {"doc": __doc__.split("usage:")[0].strip(), "cases": []}
    models = {}
    for lab, af, items in sources():
        holes, rings, tot = {}, {}, {"F": np.zeros(3), "M": np.zeros(3)}
        n = 0
        for run, st, subs in items:
            if run not in models:
                models[run] = PF.load_model(run)
            M, meta = models[run]
            RF = PF.reactions(run, st, meta["steps"])
            for co in subs:
                tab, totals = PF.icd_table(M, PF.combine_rf(RF, co))
                n += 1
                acc = {"GM09": [np.zeros(3), np.zeros(3)], "GM10": [np.zeros(3), np.zeros(3)]}
                for r in tab:
                    h = holes.setdefault(r["hole"], {"x_mm": r["x_mm"], "max_shear_N": 0.0, "max_abs_axial_N": 0.0, "max_abs_tangential_N": 0.0,
                                                     "max_pullout_N": 0.0, "max_pushin_N": 0.0})
                    h["max_shear_N"] = max(h["max_shear_N"], r["shear_in_screw_N"])
                    h["max_abs_axial_N"] = max(h["max_abs_axial_N"], abs(r["axial_N"]))
                    h["max_abs_tangential_N"] = max(h["max_abs_tangential_N"], abs(r["tangential_N"]))
                    h["max_pullout_N"] = max(h["max_pullout_N"], r["radial_N"])
                    h["max_pushin_N"] = max(h["max_pushin_N"], -r["radial_N"])
                    g = "GM09" if "GM09" in r["hole"] else "GM10"
                    F = np.asarray(r["F_on_airframe_N"])
                    acc[g][0] += F
                    acc[g][1] += np.cross(np.asarray(r["x_mm"]), F)
                for g, (F, Mm) in acc.items():
                    e = rings.setdefault(g, {"max_abs_F_N": np.zeros(3), "max_lateral_F_N": 0.0, "max_abs_M_Nmm": np.zeros(3), "max_lateral_M_Nmm": 0.0})
                    e["max_abs_F_N"] = np.maximum(e["max_abs_F_N"], np.abs(F))
                    e["max_lateral_F_N"] = max(e["max_lateral_F_N"], float(np.hypot(F[0], F[1])))
                    e["max_abs_M_Nmm"] = np.maximum(e["max_abs_M_Nmm"], np.abs(Mm))
                    e["max_lateral_M_Nmm"] = max(e["max_lateral_M_Nmm"], float(np.hypot(Mm[0], Mm[1])))
                tot["F"] = np.maximum(tot["F"], np.abs(totals["F_total_on_airframe_N"]))
                tot["M"] = np.maximum(tot["M"], np.abs(totals["M_total_about_pivot_Nmm"]))
        out["cases"].append({"case": lab, "airframe": af, "n_subcases": n, "runs": sorted({r for r, _, _ in items}),
                             "holes": holes, "rings": {g: {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in e.items()} for g, e in rings.items()},
                             "total_on_airframe": {"max_abs_F_N": tot["F"].tolist(), "max_abs_M_Nmm": tot["M"].tolist()}})
        print(f"[icd] {lab} ({af}): {n} sub-cases, max shear {max(h['max_shear_N'] for h in holes.values()):.1f} N", flush=True)
    (RES / "engine_mount_data_v351.json").write_text(json.dumps(out, indent=1, default=float))
    # paste-ready tables
    L = ["ENGINE MOUNTING DATA (datasheet; CAD v3.5.1, fea3d-asm v1.2, SIM unless tagged). 16 radial M5 holes: GM-09 forward ring z +27 mm, GM-10 aft ring z -94.8 mm.", "",
         "Per-hole envelopes, N (shear in the radial M5 screw / max |axial| / max pull-out); forces of the engine module ON its mount; SIM asm v1.2.", ""]
    cs = out["cases"]
    hdr = "| hole (x, y, z mm) | " + " | ".join(f"{c['case']} [{c['airframe']}]" for c in cs) + " |"
    L += [hdr, "|---|" + "---|" * len(cs)]
    for h in sorted(cs[0]["holes"]):
        x = cs[0]["holes"][h]["x_mm"]
        cells = []
        for c in cs:
            v = c["holes"].get(h)
            cells.append(f"{v['max_shear_N']:.0f} / {v['max_abs_axial_N']:.0f} / {v['max_pullout_N']:.0f}" if v else "-")
        L.append(f"| {h} ({x[0]:.1f}, {x[1]:.1f}, {x[2]:.1f}) | " + " | ".join(cells) + " |")
    L += ["", "Ring resultants (engine module ON airframe), envelope over the sub-cases: max |Fx|, |Fy|, |Fz| N ; max lateral |F| N ; max |M| about the pivot N m (x, y, z).", "",
          "| case | airframe | GM-09 ring (z +27) F | GM-09 lat | GM-09 M | GM-10 ring (z -94.8) F | GM-10 lat | GM-10 M | total F | total M |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for c in cs:
        r9, r10, t = c["rings"]["GM09"], c["rings"]["GM10"], c["total_on_airframe"]
        fm = lambda v: ", ".join(f"{x:.0f}" for x in v)
        mm = lambda v: ", ".join(f"{x / 1e3:.2f}" for x in v)
        L.append(f"| {c['case']} | {c['airframe']} | {fm(r9['max_abs_F_N'])} | {r9['max_lateral_F_N']:.0f} | {mm(r9['max_abs_M_Nmm'])} | "
                 f"{fm(r10['max_abs_F_N'])} | {r10['max_lateral_F_N']:.0f} | {mm(r10['max_abs_M_Nmm'])} | {fm(t['max_abs_F_N'])} | {mm(t['max_abs_M_Nmm'])} |")
    # gimbal stiffness at the stop poses (F3) and first engine-mount modes (modal 9A), engine data for the datasheet (lead 222)
    fk = RES / "k_stop_c71.json"
    if fk.exists():
        L += ["", "Gimbal-axis stiffness at the 8 deg stop poses (engine held by the two TVC chains; rigid airframe; SIM with the servo output rigid, "
              "DERIVED with the servo output k_s 58 / 174 N m/rad per servo in series, ASSUMED TO-VERIFY B-TVC-1), N m/rad:", "",
              "| pose (alpha, beta deg) | K_alpha FE | K_alpha +servo 58 / 174 | K_beta FE | K_beta +servo 58 / 174 |", "|---|---|---|---|---|"]
        for r in json.loads(fk.read_text())["runs"]:
            a, b = r["axes"]["alpha (outer, X)"], r["axes"]["beta (inner, ring Y)"]
            sv = lambda x, k: x["servo_series"][f"k_s{k}_engine"]["K_total_Nm_per_rad"]
            L.append(f"| {r['run'].replace('pose_', '').replace('_c71', '')} ({r['pose_deg'][0]:+.2f}, {r['pose_deg'][1]:+.2f}) | {a['K_FE_engine_Nm_per_rad']:.0f} | "
                     f"{sv(a, 58):.0f} / {sv(a, 174):.0f} | {b['K_FE_engine_Nm_per_rad']:.0f} | {sv(b, 58):.0f} / {sv(b, 174):.0f} |")
        out["K_stop_source"] = "results/k_stop_c71.json"
    fm_ = RES / "modal_summary_v351.json"
    if fm_.exists():
        ms = json.loads(fm_.read_text())
        L += ["", f"First engine-mount modes ({ms['modal_run']}, every body at mesh level 2, rigid airframe holes, servo output rigid, unstressed T_REF; SIM; "
              "production-K and servo-in-series columns DERIVED):", "",
              "| mode | shape | f FE Hz | f at production K Hz | f with servo k_s 58 / 174 Hz |", "|---|---|---|---|---|"]
        for e in ms["engine_mount_modes"]:
            L.append(f"| {e['mode']} | {e['description']} | {e['f_FE_rigid_servo_Hz']:.1f} | "
                     + (f"{e['f_scaled_to_pose_model_K_Hz']:.1f} | {e['f_with_servo_k58_Hz_DERIVED']:.1f} / {e['f_with_servo_k174_Hz_DERIVED']:.1f} |"
                        if "f_scaled_to_pose_model_K_Hz" in e else "- | - |"))
        out["modes_source"] = "results/modal_summary_v351.json"
        out["engine_mount_modes"] = ms["engine_mount_modes"]
    (RES / "engine_mount_data_v351.json").write_text(json.dumps(out, indent=1, default=float))
    (RES / "tables" / "engine_mount_data_v351.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
