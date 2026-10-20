"""REV-MECH-2 (independent reviewer): servo-in-series factor check for FEA3D post_k (criterion f2, GNC rev4b finding 14).

For every FEA3D pose run (9 cone + 8 stop poses, *_c71) the solved model.json rod_geom (horn eye H, lever eye L, push direction e) and
the servo geometry (geom/tvc_geometry_v35.json: shaft point C, shaft axis et, horn radius r_h) give the exact first-order kinematics of
the two-force rod: theta_dot * a = phi_dot * r_eff, with a = (X_L x e) . axis (arm of the rod line about the gimbal axis) and
r_eff = ((X_H - C) x e) . et (arm of the rod line about the servo shaft).  So the servo output stiffness K_s [N m/rad] reflects to the
rod as k_rod = K_s / r_eff^2 and to the gimbal axis as K_s (a / r_eff)^2.  post_k uses r_h in place of r_eff ('horn normal to the
rod'), i.e. g_fea = a / r_h against g_kin = a / r_eff; ratio g_kin / g_fea = r_h / r_eff (per servo).
Outputs per pose and axis: r_eff, ratios, the per-axis servo stiffness and the series total (post_k diagonal rule) with r_h and with
r_eff, for K_s 58 / 100 / 130 / 174 N m/rad; plus a coupled check: C_total = C_FE (diagonal, 1/K_FE) + inv(sum_i k_i a_i a_i^T).
Reads FEA3D results/k_cone_c71.json and k_stop_c71.json (K_FE, arms) read-only.

usage: python -I rm2_servo_g.py <out.json>
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

RUNS = Path("/home/claude/work/fea3d/runs")
GEOM = Path("/home/claude/work/fea3d/geom/tvc_geometry_v35.json")
HUBR = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d/results")
KS = (58.0, 100.0, 130.0, 174.0)


def main(outp):
    g = json.loads(GEOM.read_text())
    rh = float(g["r_h"])
    sv = {int(s["i"]): {k: np.asarray(s[k], float) for k in ("C", "et", "eu", "ez")} for s in g["servos"]}
    kres = {}
    for f in ("k_cone_c71.json", "k_stop_c71.json"):
        for r in json.loads((HUBR / f).read_text())["runs"]:
            kres[r["run"]] = (f, r)
    rows = []
    for run, (src, kr) in sorted(kres.items()):
        m = json.loads((RUNS / run / "model.json").read_text())
        Rg = np.asarray(m["Rg"]["ring"], float)
        axes = {"alpha": np.array([1.0, 0, 0]), "beta": Rg @ np.array([0, 1.0, 0])}
        rg = m["rod_geom"]
        per = {}
        for i in sorted(rg, key=int):
            H, L = np.asarray(rg[i]["horn_eye"], float), np.asarray(rg[i]["lever_eye"], float)
            e = (L - H) / np.linalg.norm(L - H)
            e_stored = np.asarray(rg[i]["e_push_on_engine"], float)
            C, et = sv[int(i)]["C"], sv[int(i)]["et"]
            hc = H - C
            r_eff = float(abs(np.cross(hc, e) @ et))
            per[i] = {"rod_len_mm": float(np.linalg.norm(L - H)), "e_vs_stored_max": float(np.max(np.abs(e - e_stored))),
                      "horn_radius_check_mm": float(np.linalg.norm(hc)), "horn_plane_offset_mm": float(hc @ et),
                      "r_eff_mm": r_eff, "r_eff_over_rh": r_eff / rh, "g_kin_over_g_fea": rh / r_eff,
                      "arm_mm": {ax: float(np.cross(L, e) @ v) for ax, v in axes.items()}}
        row = {"run": run, "src": src, "pose_deg": kr["pose_deg"], "servos": per, "axes": {}}
        # compare arms with post_k's stored arms
        Kfe = {}
        for axn, a in kr["axes"].items():
            ax = "alpha" if axn.startswith("alpha") else "beta"
            Kfe[ax] = a["K_FE_engine_Nm_per_rad"]
            row["axes"][ax] = {"K_FE_engine": a["K_FE_engine_Nm_per_rad"],
                               "arm_check_max_abs_mm": max(abs(abs(a["rods"][f"ROD_{i}"]["arm_mm"]) - abs(per[i]["arm_mm"][ax])) for i in per),
                               "stored_servo_series": {k: v["K_total_Nm_per_rad"] for k, v in a["servo_series"].items() if k.endswith("_engine")}}
        for ax in ("alpha", "beta"):
            A = row["axes"][ax]
            for ks in KS:
                kserv_fea = sum(ks / rh ** 2 * per[i]["arm_mm"][ax] ** 2 for i in per)        # N m/rad (ks N m/rad, mm^2/mm^2)
                kserv_kin = sum(ks / per[i]["r_eff_mm"] ** 2 * per[i]["arm_mm"][ax] ** 2 for i in per)
                tot_fea = 1.0 / (1.0 / Kfe[ax] + 1.0 / kserv_fea)
                tot_kin = 1.0 / (1.0 / Kfe[ax] + 1.0 / kserv_kin)
                # coupled: servo stiffness matrix about (alpha, beta) from both rods, FE taken diagonal
                Ks = np.zeros((2, 2))
                for i in per:
                    av = np.array([per[i]["arm_mm"]["alpha"], per[i]["arm_mm"]["beta"]])
                    Ks += ks / per[i]["r_eff_mm"] ** 2 * np.outer(av, av)
                try:
                    Cs = np.linalg.inv(Ks)
                    j = 0 if ax == "alpha" else 1
                    tot_cpl = 1.0 / (1.0 / Kfe[ax] + Cs[j, j])
                    tot_cpl_hold = None
                    Ct = np.diag([1.0 / Kfe["alpha"], 1.0 / Kfe["beta"]]) + Cs
                    Kt = np.linalg.inv(Ct)
                    tot_cpl_hold = float(Kt[j, j])          # other axis held at zero rotation
                except np.linalg.LinAlgError:
                    tot_cpl, tot_cpl_hold = None, None
                A[f"Ks{ks:g}"] = {"K_servo_axis_postk": kserv_fea, "K_servo_axis_kin": kserv_kin, "servo_ratio": kserv_kin / kserv_fea,
                                  "g_axis_ratio": math.sqrt(kserv_kin / kserv_fea), "K_total_postk": tot_fea, "K_total_kin": tot_kin,
                                  "K_total_kin_coupled_other_free": tot_cpl, "K_total_kin_coupled_other_held": tot_cpl_hold,
                                  "total_ratio_kin_over_postk": tot_kin / tot_fea}
            # reproduce post_k's stored numbers at 58 / 174
            for ks in (58.0, 174.0):
                st = A["stored_servo_series"].get(f"k_s{ks:g}_engine")
                A[f"Ks{ks:g}"]["stored_postk_K_total"] = st
        rows.append(row)
    # summaries
    def rng(sel, key):
        v = [s[key] for r in rows if sel(r) for s in r["servos"].values()]
        return [min(v), max(v)]
    cone = lambda r: not r["run"].startswith("pose_stop")
    stop = lambda r: r["run"].startswith("pose_stop")
    off = lambda r: cone(r) and r["run"] != "pose_neutral_c71"
    summ = {"r_h_mm": rh,
            "g_kin_over_g_fea_cone_all": rng(cone, "g_kin_over_g_fea"), "g_kin_over_g_fea_cone_offcentre": rng(off, "g_kin_over_g_fea"),
            "g_kin_over_g_fea_stops": rng(stop, "g_kin_over_g_fea"),
            "r_eff_mm_cone": rng(cone, "r_eff_mm"), "r_eff_mm_stops": rng(stop, "r_eff_mm")}
    for ks in KS:
        for ax in ("alpha", "beta"):
            for lab, sel in (("cone", cone), ("stops", stop)):
                v = [r["axes"][ax][f"Ks{ks:g}"] for r in rows if sel(r)]
                summ[f"Ks{ks:g}_{ax}_{lab}"] = {
                    "K_total_postk": [min(x["K_total_postk"] for x in v), max(x["K_total_postk"] for x in v)],
                    "K_total_kin": [min(x["K_total_kin"] for x in v), max(x["K_total_kin"] for x in v)],
                    "K_total_kin_coupled_other_free": [min(x["K_total_kin_coupled_other_free"] for x in v), max(x["K_total_kin_coupled_other_free"] for x in v)],
                    "g_axis_ratio": [min(x["g_axis_ratio"] for x in v), max(x["g_axis_ratio"] for x in v)],
                    "total_ratio_kin_over_postk": [min(x["total_ratio_kin_over_postk"] for x in v), max(x["total_ratio_kin_over_postk"] for x in v)]}
    out = {"tool": "REV-MECH-2 rm2_servo_g.py (own code)", "date": "2026-10-19", "summary": summ, "poses": rows}
    Path(outp).write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(summ, indent=1)[:6000])
    for r in rows:
        s = r["servos"]
        print(f"{r['run']:<24} pose {str([round(x, 2) for x in r['pose_deg']]):<16} r_eff {s['1']['r_eff_mm']:.3f}/{s['2']['r_eff_mm']:.3f}  "
              f"g ratio {s['1']['g_kin_over_g_fea']:.3f}/{s['2']['g_kin_over_g_fea']:.3f}  rodlen {s['1']['rod_len_mm']:.3f}/{s['2']['rod_len_mm']:.3f} "
              f"hornchk {s['1']['horn_radius_check_mm']:.3f}/{s['2']['horn_radius_check_mm']:.3f} plane {s['1']['horn_plane_offset_mm']:.1e} "
              f"armchk a {r['axes']['alpha']['arm_check_max_abs_mm']:.1e} b {r['axes']['beta']['arm_check_max_abs_mm']:.1e} | "
              f"K58 a {r['axes']['alpha']['Ks58']['K_total_postk']:.0f}->{r['axes']['alpha']['Ks58']['K_total_kin']:.0f} (stored {r['axes']['alpha']['Ks58']['stored_postk_K_total']:.0f}) "
              f"b {r['axes']['beta']['Ks58']['K_total_postk']:.0f}->{r['axes']['beta']['Ks58']['K_total_kin']:.0f}")


if __name__ == "__main__":
    main(sys.argv[1])
