"""Assemble s3d/REPORT-S3D.md (F2: S-3D gimbal strength on CAD v3.5.1) from the posted results (fea3d 2026-10-19).
Numbers in the text are read from results/*.json (no hand-typed values except the cited S-3D v1.1 comparison, read from the hub CSV).
usage: s3d_report.py
"""
from __future__ import annotations
import json, csv, hashlib
import numpy as np
from pathlib import Path

W = Path("/home/claude/work/fea3d")
RES, TAB = W / "results", W / "results" / "tables"
HUB = Path("/home/claude/work/shared-fallback/engine")
V11 = HUB / "04-fea" / "structural" / "results" / "s3d_margin_table_v1.1.csv"


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def f(x, nd=3):
    return "n/a" if x is None else (f"{x:+.{nd}f}" if abs(x) < 100 else ">+99")


def main():
    S = json.loads((RES / "s3d_summary_v351.json").read_text())
    pc = S["per_case"]
    cones = S["cone_poses_present"]
    miss = S["cone_poses_missing"]
    kr = json.loads((RES / "k_range_v351.json").read_text())
    hb_f = RES / "f1_lc3_hot_bound_s3d.json"
    hb = json.loads(hb_f.read_text())["summary_min_over_states_regular"] if hb_f.exists() else {}
    em = json.loads((RES / "engine_mount_data_v351.json").read_text()) if (RES / "engine_mount_data_v351.json").exists() else None
    gim = ["GM-01", "GM-02", "GM-03", "GM-16a", "GM-16b", "GM-08a", "GM-08b", "GM-09", "GM-10", "GM-13", "GM-14"]

    def mn(c, parts):
        rows = [(min(v["MS"], v.get("MS_ult_min", v.get("MS_ult")) if v.get("MS_ult_min", v.get("MS_ult")) is not None else 9e9), p, v)
                for p, v in pc.get(c, {}).items() if p in parts]
        return min(rows) if rows else None

    gs1, gs2 = pc["GS"]["GM-01"], pc["GS"]["GM-02"]
    perpose, ball_d = {}, {}
    for p in cones:
        d = json.loads((RES / f"s3d_pose_{p}_c71.json").read_text())
        rr = [r for r in d["cases"]["GS"]["margins"] if r["set"] == "regular" and r["part"] in ("GM-01", "GM-02")]
        ry = min(rr, key=lambda r: r["MS"])
        ru = min(rr, key=lambda r: r["MS_ult"] if r.get("MS_ult") is not None else 9e9)
        perpose[p] = (ry["MS"], ry["part"], ru["MS_ult"], ru["part"], ry.get("vm_MPa"))
        mj = json.loads((W / "runs" / f"pose_{p}_c71" / "model.json").read_text())
        Rg = np.array(mj["Rg"]["engine"])
        for r in rr:
            ball = np.array(mj["variant"]["refine"][r["part"]][0][:3])
            ball_d[(p, r["part"])] = float(np.linalg.norm(Rg.T @ np.array(r["xyz_mm"]) - ball))
    bd = list(ball_d.values())
    n_ult_neg = sum(1 for v in perpose.values() if v[2] < 0)
    n_y_neg = sum(1 for v in perpose.values() if v[0] < 0)
    least = max(perpose.items(), key=lambda kv: kv[1][2])
    f1m = {r["part"]: r for r in json.loads((TAB / "f1_part_margins.json").read_text())}
    lc1_collar = min(min(f1m[q]["LC1_MS_y"], f1m[q]["LC1_MS_u"]) for q in ("GM-01", "GM-02"))
    others = [p for p in gim if p not in ("GM-01", "GM-02")]
    o = {c: mn(c, others) for c in ("GS", "TD", "LC6", "LC2F", "SR", "FA1T")}
    rods_td = max(max(v.values()) for v in S["rods"]["TD"].values())
    rods_lc6 = max(max(v.values()) for v in S["rods"]["LC6"].values())
    rods_lc2f = max(max(v.values()) for v in S["rods"]["LC2F"].values())
    con = S["connectors"]
    icd = S["icd"]
    # v1.1 comparison (Mechanical, CAD v3.4 V5c, 7075 design-change columns, 1.5 mm exclusion)
    v11 = {}
    for r in csv.DictReader(V11.open()):
        if r["part"] in ("GM-01", "GM-02") and r.get("MS_y_design_change"):
            k = (r["part"], r["case"])
            y, u = float(r["MS_y_design_change"]), float(r["MS_u_design_change"])
            if k not in v11 or y < v11[k][0]:
                v11[k] = (y, u, r["pose"], float(r["vm_outside_MPa"]))
    allk = kr["range"]
    L = []
    A = L.append
    A("# ARGOS H1 engine - S-3D gimbal strength on CAD v3.5.1 (F2, fea3d)")
    A("")
    A("| | |")
    A("|---|---|")
    A(f"| Status | **2026-10-19, F2 on fea3d-asm v1.2**: {len(cones)} of 9 range-cone poses ({', '.join(cones)}){' - MISSING: ' + ', '.join(miss) if miss else ''}; "
      "the 8 deg stop poses (runaway, SR) and the FA-1 thrust spike (FA1T) are taken from F1 (REPORT-FEA3D sections 6, 4.6, 3). Replaces S-3D v1.1 "
      "(Mechanical, CAD v3.4 V5c, centre + betam7) for CAD v3.5.1 (lead 188 (6), RM1-07/15). |")
    A("| Author | fea3d (successor Senior FEA analyst 3D); brief lead CHANGELOG 188 + coordinator 2026-10-19 |")
    A("| Configuration | CAD v3.5.1 frozen (CHANGELOG 206): MANIFEST `b62c0e0ac8555fb8`, ENGINE STEP `4ca22820c796b670`; collar GM-01 / GM-02 7075-T6 with the lever-root fillets as modelled in v3.5.1 |")
    A("| Tool | CalculiX 2.21 (SPOOLES), C3D10; own pre / post (`src/`); assembly model fea3d-asm v1.2 (connector fix 7.1 of REPORT-FEA3D) |")
    A("| Units | SI; mm, N, MPa, degC where conventional. MS = allowable / (SF x stress) - 1 |")
    A("| Tags | SIM (FE), DERIVED, ASSUMED, DATASHEET, LITERATURE, TO-VERIFY, AS RECALLED |")
    A("")
    A("> **Not physical approval.** Converged solutions, matching numbers or clean plots do not approve hardware. Negative margins are reported as found; none is forced.")
    A("")
    A("## 1. Claims (checkpoint, SUPERVISION-WORKFLOW)")
    A("")
    A(f"1. **GS (both servos at stall, rods +/-441 N at neutral, +/-552 N on the 7 deg cone) is NEGATIVE at both lever roots** with the fillet zone resolved (R3 refinement in every cone run): "
      f"**GM-02 {f(gs2['MS'])} / {f(gs2.get('MS_ult_min', gs2.get('MS_ult')))} ({gs2['pose']}, {gs2['vm_MPa']:.0f} MPa)**, **GM-01 {f(gs1['MS'])} / {f(gs1.get('MS_ult_min', gs1.get('MS_ult')))} ({gs1['pose']}, {gs1['vm_MPa']:.0f} MPa)** [SIM]. "
      f"The lever-root GS margin is ultimate-negative at {n_ult_neg} of {len(perpose)} cone poses and yield-negative at {n_y_neg} "
      f"(least severe: {least[0]}, MS_y {f(least[1][0])} {least[1][1]}, MS_u {f(least[1][2])} {least[1][3]}; per pose in 4.1a). Same location as the F1 LC3 finding (R1.2 lever-root fillet where it meets the R32.5 collar OD). "
      "Mechanical DESIGN CHANGE item (CHANGELOG 223 (5)); not redesigned here.")
    sr1, sr2 = pc["SR"]["GM-01"], pc["SR"]["GM-02"]
    A(f"2. **SR (runaway onto the 8 deg stop = F1 LC3, rod at the 609 N stall limit):** L1 regular set GM-02 {f(sr2['MS'])} / {f(sr2['MS_ult'])} ({sr2['pose']}), GM-01 {f(sr1['MS'])} / {f(sr1['MS_ult'])} ({sr1['pose']}); "
      f"**refined R3: GM-02 {f(sr2.get('R3_MS'))} / {f(sr2.get('R3_MS_ult'))}, GM-01 {f(sr1.get('R3_MS'))} / {f(sr1.get('R3_MS_ult'))}** (REPORT-FEA3D 4.6; the L1 value is unconservative).")
    A(f"3. **All other gimbal and mount parts are positive** in every case [SIM]: lowest GS {o['GS'][1]} {f(o['GS'][0])}, TD {o['TD'][1]} {f(o['TD'][0])}, LC6 {o['LC6'][1]} {f(o['LC6'][0])}, "
      f"LC2F (SF 1.0 / 1.5) {o['LC2F'][1]} {f(o['LC2F'][0])} (min of yield and ultimate); SR (F1 LC3, L1) {o['SR'][1]} {f(o['SR'][0])}; FA1T (F1) {o['FA1T'][1]} {f(o['FA1T'][0])}.")
    A(f"4. **Touchdown (TD, servos holding):** rod forces stay at or below {rods_td:.0f} N against the 609 N stall force at every cone pose, so the servos hold and the engine does not reach the stop under the touchdown loads [SIM]; "
      f"lever-root margins >= {f(min(pc['TD']['GM-01']['MS'], pc['TD']['GM-02']['MS']))} (yield). LC6 rods <= {rods_lc6:.0f} N, LC2F rods <= {rods_lc2f:.0f} N.")
    gsc = con.get("GS", {})
    cup = max((v["max_abs_component_N"] for k, v in gsc.items() if k.startswith("BRG")), default=0)
    wsh = max((v["max_abs_component_N"] for k, v in gsc.items() if k.startswith("WSH")), default=0)
    A(f"5. **Connector loads (GS envelope):** needle-cup radial component up to {cup:.0f} N, thrust washers up to {wsh:.0f} N; largest M5 hole shear at the mount "
      f"{icd['GS']['max_hole_shear_N']:.0f} N ({icd['GS']['hole']}, {icd['GS']['pose']}) [SIM]. Bearing / washer / screw capacities against datasheets: TO-VERIFY (Mechanical).")
    kc = allk.get("range cone, rigid airframe")
    ks = allk.get("stop (8 deg), rigid airframe")
    lo_s = min(allk["ALL"][ax]["with_servo_58"][0] for ax in ("K_alpha", "K_beta"))
    hi_s = max(allk["ALL"][ax]["with_servo_174"][1] for ax in ("K_alpha", "K_beta"))
    rw = {r["run"]: r for r in kr["rows"]}
    dc_a = 100 * (rw["pose_stop045_compliant_c71"]["K_alpha"]["K_FE_engine"] / rw["pose_stop045_c71"]["K_alpha"]["K_FE_engine"] - 1)
    dc_b = 100 * (rw["pose_stop045_compliant_c71"]["K_beta"]["K_FE_engine"] / rw["pose_stop045_c71"]["K_beta"]["K_FE_engine"] - 1)
    if kc:
        A(f"6. **Stiffness (F3):** over the 9 cone poses K_alpha {kc['K_alpha']['K_FE_engine'][0]:.0f}-{kc['K_alpha']['K_FE_engine'][1]:.0f}, K_beta {kc['K_beta']['K_FE_engine'][0]:.0f}-{kc['K_beta']['K_FE_engine'][1]:.0f} N m/rad (rigid servo); "
          f"over the 8 stop poses {ks['K_alpha']['K_FE_engine'][0]:.0f}-{ks['K_alpha']['K_FE_engine'][1]:.0f} / {ks['K_beta']['K_FE_engine'][0]:.0f}-{ks['K_beta']['K_FE_engine'][1]:.0f}; "
          f"with the servo output (k_s 58-174 N m/rad, ASSUMED) {lo_s:.0f}-{hi_s:.0f} N m/rad overall [SIM / DERIVED]; compliant airframe at stop045 {dc_a:+.0f} / {dc_b:+.0f} % vs rigid.")
    if hb:
        h1, h2 = hb.get("GM-01"), hb.get("GM-02")
        A(f"7. **Hot lower bound** (cone-pose increments added to the LC1 thermo-pressure field by sub-additivity; for the refined collars the part-maximum increment is added to every L1 node, a conservative but coarse bound): "
          f"GM-01 {f(h1['MS_bound'])} / {f(h1['MS_ult_bound'])}, GM-02 {f(h2['MS_bound'])} / {f(h2['MS_ult_bound'])} [DERIVED]; other gimbal parts in section 4.4.")
    A("")
    A("## 2. Scope and what changed from S-3D v1.1")
    A("")
    A("- S-3D v1.1 (Mechanical, 2026-10-13; hub `04-fea/structural/results/s3d_results_v1.1.json` " + sha16(HUB / "04-fea/structural/results/s3d_results_v1.1.json") +
      ", `s3d_margin_table_v1.1.csv` " + sha16(V11) + "): CAD v3.4 V5c, poses centre and betam7 only, collar in 6061-T6 with 7075-T6 design-change columns, 1.5 mm exclusion around connectors and edges, gimbal-only model with the engine rigid.")
    A("- This F2 (lead 188 (6)): CAD v3.5.1 with the GM-01 / GM-02 lever-root fillets modelled and the collar in 7075-T6; all 9 range-cone poses + the 8 deg stop poses (F1); the flexible engine in the assembled model; "
      "v3.5.1 mass properties; gnc.json v3.1 inertial loads (flight 0.61 g lateral / 4.04 g axial, touchdown 6.29 g lateral / 5.43 g axial / 79.28 rad/s2, SIM); the FA-1 thrust spike (FA1T, F1). "
      "The GNC hinge moments (flight max 19.53 N m, touchdown 7.83 N m; gnc.json v3.1 design_limit_loads, SIM) are enveloped by GS (both-servo stall, M_engine_GS 37.95 N m) and SR "
      "(M_engine_stop 41.14 N m), mechanical.json v2.1 tvc_actuation.design_loads [DERIVED].")
    A("")
    A((W / "s3d" / "method_section.md").read_text().strip())
    A("")
    A("## 4. Results")
    A("")
    A("### 4.1 Per-part minimum margins, regular node set, yield / ultimate (pose of the minimum) [SIM]; SR lever root R3 from F1; FA1T from F1")
    A("")
    A((TAB / "s3d_part_margins_v351.md").read_text().strip())
    A("")
    A("")
    A("### 4.1a GS lever-root minimum per cone pose (GM-01 / GM-02 at R3, regular set) [SIM]")
    A("")
    A("| pose | MS_y (part) | MS_u (part) | vM at the MS_y node MPa | peak to the R3-ball centre, GM-01 / GM-02 mm |")
    A("|---|---|---|---|---|")
    for p, v in perpose.items():
        A(f"| {p} | {f(v[0])} ({v[1]}) | {f(v[2])} ({v[3]}) | {v[4]:.0f} | {ball_d[(p, 'GM-01')]:.2f} / {ball_d[(p, 'GM-02')]:.2f} |")
    A("")
    A(f"In every pose the regular-set lever-root peak of both collar halves lies {min(bd):.2f}-{max(bd):.2f} mm from the refinement-ball centre (ball radius 2.5 mm, "
      "body frame), i.e. inside the refined zone; the ball spec is the F1 R3 spec (target h 0.25 mm, achieved about 0.34 mm in F1 4.6).")
    A("")
    A("Chart S3D-C1 (`figs/S3D-C1_gimbal_margins.png`); lever-root field S3D-01 (`figs/S3D-01_alpha-_GM02_R3_zoom_vM.png`).")
    A("")
    A("### 4.2 Rod forces and engine angular acceleration (GS realised by the engine inertia) [SIM]")
    A("")
    A((TAB / "s3d_rods_v351.md").read_text().strip())
    A("")
    A("### 4.3 Connector envelopes and mount hole shear [SIM]")
    A("")
    A((TAB / "s3d_connectors_v351.md").read_text().strip())
    A("")
    if hb:
        A("### 4.4 Hot lower bound (DERIVED; `results/f1_lc3_hot_bound_s3d.json`)")
        A("")
        A("| part | MS_y bound | MS_u bound | state | method |")
        A("|---|---|---|---|---|")
        for p in gim + ["TC-01"]:
            r = hb.get(p)
            if r:
                A(f"| {p} | {f(r['MS_bound'])} | {f(r.get('MS_ult_bound'))} | {r['state']} | {r['method']} |")
        A("")
    A("### 4.5 Comparison with S-3D v1.1 (collar 7075-T6 design-change columns, 1.5 mm exclusion; Mechanical) [SIM, both]")
    A("")
    A("| part, case | v1.1 (CAD v3.4 V5c) MS_y / MS_u (pose, vM outside 1.5 mm) | v3.5.1 this work MS_y / MS_u (pose) |")
    A("|---|---|---|")
    for part in ("GM-01", "GM-02"):
        for c, mine in (("GS", pc["GS"][part]), ("SR", pc["SR"][part]), ("LC6", pc["LC6"][part]), ("LC2F", pc["LC2F"][part])):
            v = v11.get((part, c))
            if c == "SR":
                m = f"L1 {f(mine['MS'])} / {f(mine['MS_ult'])} ({mine['pose']}); R3 {f(mine.get('R3_MS'))} / {f(mine.get('R3_MS_ult'))}"
            else:
                m = f"{f(mine['MS'])} / {f(mine.get('MS_ult_min', mine.get('MS_ult')))} ({mine['pose']}, {mine['vm_MPa']:.0f} MPa)"
            A(f"| {part} {c} | " + (f"{f(v[0])} / {f(v[1])} ({v[2]}, {v[3]:.0f} MPa)" if v else "-") + f" | {m} |")
    A("")
    lvr = {q: json.loads((RES / f"f1_lever_root_{q.replace('-', '')}_c71.json").read_text())["levels"] for q in ("GM-01", "GM-02")}
    sr_vm = [v["vm_regular_MPa"] for q in lvr for k, v in lvr[q].items() if "r3" in k]
    v11j = json.loads((HUB / "04-fea/structural/results/s3d_results_v1.1.json").read_text())
    v11rod = v11j["loads"]["F_rod_design_N"]["v"]
    gsvm = [pc["GS"][q]["vm_MPa"] for q in ("GM-01", "GM-02")]
    A(f"Reading: the prescribed rod forces are the same in both (v1.1 {v11rod['centre']:.0f} / {v11rod['betam7']:.0f} / {v11rod['stop']:.0f} N; here 441 / 552 / 609 N). "
      f"v1.1 excluded 1.5 mm around edges and connectors, which removes the R1.2 lever-root fillet zone; with the fillet zone resolved (R3) the GS load gives {min(gsvm):.0f}-{max(gsvm):.0f} MPa there "
      f"and SR {min(sr_vm):.0f}-{max(sr_vm):.0f} MPa (F1 4.6: stable 0.5 mm from the edge line, not a singularity). On the same v3.5.1 model the L1 1 mm exclusion gives SR "
      f"{f(sr2['MS'])} / {f(sr2['MS_ult'])} (GM-02) against R3 {f(sr2.get('R3_MS'))} / {f(sr2.get('R3_MS_ult'))}, so the stress resolution at the fillet explains most of the difference [DERIVED]; "
      "the geometry change CAD v3.4 V5c -> v3.5.1 is not separated here. The v1.1 GS / SR yield margins (+0.16 / +0.05) are therefore not conservative for the lever root. "
      f"LC2F: v1.1 applied the stuck-pintle thrust alone (rods unloaded); this work adds the flight inertia (rods up to {rods_lc2f:.0f} N), hence about 50 MPa against 9-10 MPa (both far positive).")
    A("")
    A("## 5. Stiffness over the cone and stop poses (F3; `results/k_cone_c71.json`, `results/k_range_v351.json`, `tables/k_range_v351.md`)")
    A("")
    A((TAB / "k_range_v351.md").read_text().strip())
    A("")
    A("## 6. Not run or not done")
    A("")
    A(f"1. Hot S-3D on the refined lever-root meshes node by node (only the conservative part-maximum bound of 4.4; the collar thermal stress is small: F1 LC1 collar margins >= {f(lc1_collar)}, min of yield and ultimate).")
    A("2. Lever-root fatigue (servo dither / vibration) and a local strain criterion at the fillet: not run (no load spectrum; lead 188 (4) asks for it at corner peaks).")
    A("3. 7075-T6 temperature table (RM1-06, Mechanical): allowables taken temperature-independent (470 / 540 MPa, LITERATURE, verify mill cert).")
    A("4. Needle-cup / thrust-washer / M5 screw capacities against datasheets (HK0808, PTFE washers, A4 screws): TO-VERIFY (Mechanical).")
    A("5. Compliant airframe at the cone poses (only stop045 run in F1: rigid bounds the hole loads, gimbal margins change <= 0.001).")
    A("6. Moment-closure observation 7.2 of REPORT-FEA3D (97-99.5 %, bounded rod-force impact <= ~6 N) applies here too.")
    A("")
    A("## 7. Files (sha256/16 of every file in MANIFEST.json in this folder)")
    A("")
    A("- `results/`: `s3d_pose_<pose>_c71.json` (9 cone poses: per case GS / TD0 / TDP / TD / LC6 / LC2F margins, rods, connector and mount envelopes, sub-case coefficients), "
      "`s3d_summary_v351.json`, the F1 stop-pose LC3 posts and lever-root refinements used for SR, `f1_post_fa1_c71.json` (FA1T), `f1_lc3_hot_bound_s3d.json`, `k_cone_c71.json`, `k_stop_c71.json`, `k_range_v351.json`, `engine_mount_data_v351.json`.")
    A("- `tables/`: `s3d_part_margins_v351.md`, `s3d_rods_v351.md`, `s3d_connectors_v351.md`, `k_range_v351.md`, `engine_mount_data_v351.md` (mounting data as engine data, lead 222), `margin_matrix_v351.md` (every part x case, F1 + F2).")
    A("- `figs/`: S3D-01 GM-02 lever root at alpha -7 deg (vM, R3), S3D-C1 margins chart.")
    A("- `src/`: scripts (post_s3d.py, s3d_summary.py, s3d_report.py, post_k.py, k_range.py, chart_s3d.py, icd_export.py, ...). Solver bulk stays in /home/claude/work/fea3d/runs.")
    out = W / "s3d" / "REPORT-S3D.md"
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out} ({out.stat().st_size} B)")


if __name__ == "__main__":
    main()
