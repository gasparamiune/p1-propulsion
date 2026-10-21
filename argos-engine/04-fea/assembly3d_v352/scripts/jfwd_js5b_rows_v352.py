"""js5b rows (FEA3D-2, 2026-10-21): the J-FWD FE rows of js5b_in718_mu0_T3750_g078_cf (s5 global sector, sharp hole edges, mu 0, 3750 N,
fit 0.078, IN718 screw properties; steps SEAT, PRELOAD, FA1U, FA1D, LC2U, LC2Y, LC2N, LC2M) for the hand steps after its post (handover:
"js5b: FA1U / FA1D / LC2 J-FWD rows; the matrix LC2 J-FWD column reads 'pending js5b'").  Read-only on the posts (cells_v352An.json,
spotface.json, shank.json, seatforce.json, ccx_run.json); no solve.  [SIM values from the posts; DERIVED margins]
Per state: the case rule of jfwd_post.py (FA1 = SF 1.0; LC2N / LC2M = kind 'LC2', Mechanical's hand form, member SF 1.5 / 2.0 on the
stresses and on V for the screw; LC2Y / LC2U = 'FE-factored' x1.5 / x2.0 load steps at SF 1.0, the like-for-like nonlinear check), and
  TC-01  (i) half-ligament average Pm / Pm+Pb, (i) shear-out flanks, (ii) hole bearing on t 2.688 (exact BEAR V), (iii) band Neuber n15 /
         n30; information: elastic band, all-node (contact edge);
  TC-02  (i) shear-out at x' 28.0, (ii) thread shear on A_n 68.4 and tap bearing on L_e 6.84, (iii) band Neuber, the 231 (1) cell and the
         ruled cell (lead 07:21Z); information: all-node (tie edge);
  SCREW  IN718 FE rows on engmat AMS 5662/5663 bar minimums (fastener allowables are Mechanical's): FA1 form (ultimate interaction with the
         FE tension, yield shear-only on A_3) and LC2 form (combined vM / Rt^2 + Rs^2), with N, V at the shear plane and M_max on the thread.
The rows are offered for the lead's ruling on which enter the matrix as criterion rows (the FA-1 J-FWD cell is governed by the FA1S
criterion rows; 5020A Eq. 22 at FA1S is Mechanical's CALC criterion for the screw).
usage: jfwd_js5b_rows_v352.py [JOB] -> results/v352/jfwd_js5b_rows_v352.json + results/v352/tables/jfwd_js5b_rows_v352.md"""
import sys, json, hashlib
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
OUT = Path("/home/claude/work/fea3d/results/v352/jfwd_js5b_rows_v352.json")
OUT_MD = Path("/home/claude/work/fea3d/results/v352/tables/jfwd_js5b_rows_v352.md")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def g(d, *ks):
    for k in ks:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def main(job):
    wd = RUNS / job
    C = json.loads((wd / "cells_v352An.json").read_text())
    sh = json.loads((wd / "shank.json").read_text()) if (wd / "shank.json").exists() else {}
    sf = json.loads((wd / "seatforce.json").read_text()) if (wd / "seatforce.json").exists() else {}
    files = {f: sha16(wd / f) for f in ("cells_v352An.json", "spotface.json", "shank.json", "seatforce.json", "post.json", "ccx_run.json",
                                        "ligament.json", "meta.json") if (wd / f).exists()}
    out = {"id": "jfwd_js5b_rows_v352", "job": job, "doc": __doc__.split("usage:")[0].strip(), "inputs_sha16": files,
           "screw_mat": C.get("screw_mat") or json.loads((wd / "meta.json").read_text()).get("screw_mat"), "thread_basis": C.get("thread_basis"),
           "states": {}}
    for st, f in C["steps"].items():
        a, b, s = f["TC-01"], f["TC-02"], f["SCREW"]
        sp = a.get("SCL_primary") or {}
        lg = sp.get("TC01_net_ligament_avg_half") or {}
        hb = g(a, "hole_bearing", "spot_t2.688") or {}
        nb = a.get("neuber_band") or {}
        so = g(b, "SCL_primary", "TC02_shear_out_to_g2_x28.0") or {}
        th = b.get("thread_shear_An") or {}
        tb = b.get("tap_bearing_derived") or {}
        nb2 = b.get("neuber_band_iii") or {}
        rec = {"kind": f.get("kind"), "label": f.get("label"), "SF_member": f.get("SF_member"),
               "TC-01": {"ligament_half_avg": {k: lg.get(k) for k in ("Pm", "PmPb", "MS_y_Pm", "MS_y_PmPb", "MS_u_Pm", "MS_u_PmPb")},
                         "shear_out": {k: {kk: (sp.get(k) or {}).get(kk) for kk in ("Pm", "PmPb", "MS_y_Pm", "MS_y_PmPb", "MS_u_Pm", "MS_u_PmPb")}
                                       for k in ("TC01_shear_out_flank+", "TC01_shear_out_flank-") if k in sp},
                         "hole_bearing_t2.688": hb, "band_neuber": {k: g(nb, k, "MS_strain") for k in ("n15", "n30")},
                         "cell": a.get("cell"), "info_band_elastic": a.get("band_elastic"), "info_all_node": a.get("all_node_info")},
               "TC-02": {"shear_out_x28.0": so, "thread_shear_An": th, "tap_bearing": tb,
                         "band_neuber": {k: g(nb2, k, "MS_strain") for k in ("n15", "n30")}, "cell_231_1": b.get("cell_231_1"),
                         "cell_ruled": {k: g(b, "cell_ruled", k) for k in ("MS_y", "MS_u", "class", "governs")},
                         "info_all_node": b.get("all_node_info")},
               "SCREW": s}
        shs = g(sh, "steps", st) or {}
        sfs = g(sf, "steps", st) or {}
        rec["screw_resultants"] = {"plane_exact_N_N": g(shs, "plane_exact", "N_N"), "plane_exact_V_N": g(shs, "plane_exact", "V_N"),
                                   "M_max_threaded": shs.get("M_max_threaded"), "M_max_shank_in_TC01": shs.get("M_max_shank_in_TC01"),
                                   "HEAD_on_screw_along_n_N": g(sfs, "screw", "HEAD_on_screw_along_n_N"),
                                   "seat_window_N": g(sfs, "seat_TC02", "footprint", "window_daz9_zp9_N")}
        out["states"][st] = rec
    OUT.write_text(json.dumps(out, indent=1, default=float))

    def f3(x):
        return f"{x:+.3f}" if isinstance(x, (int, float)) else "-"
    L = [f"# js5b J-FWD FE rows ({job}; IN718 screw, s5, mu 0, 3750 N, fit 0.078) [SIM / DERIVED]", "",
         "Margins MS_y / MS_u at the case rule (FA1: SF 1.0; LC2N / LC2M: hand form SF 1.5 / 2.0; LC2Y / LC2U: FE-factored x1.5 / x2.0 at SF 1.0).", "",
         "| state | kind (SF) | TC-01 ligament Pm+Pb | TC-01 hole bearing (V N) | TC-01 band Neuber n30 | TC-02 231 (1) cell | TC-02 thread A_n | "
         "screw N / V plane (N) | M_max thread (N mm) | screw MS y / u (form) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for st, r in out["states"].items():
        t1, t2, s = r["TC-01"], r["TC-02"], r["SCREW"]
        lg, hb = t1["ligament_half_avg"], t1["hole_bearing_t2.688"]
        c2, th = t2["cell_231_1"] or {}, t2["thread_shear_An"]
        L.append(f"| {st} | {r['kind']} ({r['SF_member']}) | {f3(lg.get('MS_y_PmPb'))} / {f3(lg.get('MS_u_PmPb'))} | "
                 f"{f3(hb.get('MS_y'))} / {f3(hb.get('MS_u'))} ({hb.get('V_N')}) | {f3(t1['band_neuber'].get('n30'))} | "
                 f"{f3(c2.get('MS_y'))} / {f3(c2.get('MS_u'))} | {f3(th.get('MS_y'))} / {f3(th.get('MS_u'))} | "
                 f"{r['screw_resultants']['plane_exact_N_N']} / {r['screw_resultants']['plane_exact_V_N']} | "
                 f"{(r['screw_resultants']['M_max_threaded'] or {}).get('M')} | {f3(s.get('MS_y'))} / {f3(s.get('MS_u'))} ({(s.get('form') or '')[:24]}) |")
    L += ["", f"Inputs (sha256/16): {json.dumps(files)}", "", "Nothing here is physical approval."]
    OUT_MD.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(OUT, sha16(OUT), OUT_MD, sha16(OUT_MD))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "js5b_in718_mu0_T3750_g078_cf")
