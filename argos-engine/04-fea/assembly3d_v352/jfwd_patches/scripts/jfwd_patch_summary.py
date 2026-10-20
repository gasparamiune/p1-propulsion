"""J-FWD seat-patch summary for the lead (fea3d 2026-10-20 ~15:30Z; lead 14:01Z "send me (b2) when it is extracted and gzipped"; 12:28Z /
12:52Z / 11:41Z items for (b2)).  DERIVED from the posts of one patch run (no solve; nothing re-computed from the field):
  seatforce.json   screw HEAD force along the axis, exact N and V at the shear plane, seat window sum (|daz| <= 9 deg, |z'| <= 9 mm),
                   footprint (CPRESS > 0 extent, force-weighted centroid and r', clusters), shell pull (tie pull minus seat)
  shank.json       N, V, M along the shank; M_max on the threaded length and in the TC-01 shank; the equivalent arm M / V at the
                   shear plane (replaces the 1.120 mm CALC arm of Mechanical's Eq. 22 row if the lead so rules)
  compare.json     the patch's own TC-01 band (under-head), hole bearing V / (D t) as jfwd_seat_cmp posts it (t = the sharp wall
                   2.688 or the mesh's own), the 54 seat lines and the 10 hole-edge lines (min MS P+Q 2 Fty, count negative, count
                   Pm > Fty), and the patch vs the reference ('global_same_sets' = gref, or the global run)
  hole bearing     V_plane / (D t_eff) with D 5.0 and t_eff = 2.688 - break (lead: t_eff 2.388 on the broken edge), Fbry / Fbru
                   at the hole temperature from compare.json [DERIVED]
  histcheck.json   the repeats (SOAK_rep vs SOAK, SOAK52_rep vs SOAK52): the lead's 5 % criterion (54 lines, N, M at the shear plane,
                   window)
  histcheck_<R>.json / runcmp_<R>.json   against a reference run R (state by state, information on a different geometry)
  lig_station.json the TC-01 ligament station (clipped to the material on the broken edge) and the TC-02 thread-tie resultant
usage: jfwd_patch_summary.py JOB [t_eff=2.388] [ref=JOB_R ...] -> jfwd/runs/JOB/summary.json (and a compact print)"""
from __future__ import annotations
import sys, json, hashlib, time
from pathlib import Path

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
D_SCREW = 5.0


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(p):
    return json.loads(p.read_text()) if p.exists() else None


def main(job, t_eff, refs):
    R = RUNS / job
    files = {n: R / n for n in ("seatforce.json", "shank.json", "compare.json", "histcheck.json", "lig_station.json", "meta.json")}
    for r in refs:
        files[f"histcheck_{r}.json"] = R / f"histcheck_{r}.json"
        files[f"runcmp_{r}.json"] = R / f"runcmp_{r}.json"
    D = {k: load(p) for k, p in files.items()}
    out = {"job": job, "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "doc": __doc__.split("usage:")[0].strip(),
           "evidence": "SIM (posts of the patch run) + DERIVED (this summary)", "t_eff_mm": t_eff,
           "files": {k: ({"sha16": sha16(p)} if p.exists() else "missing") for k, p in files.items()}, "steps": {}, "repeats": {}, "refs": {}}
    sf, sh, cm, lg = D["seatforce.json"], D["shank.json"], D["compare.json"], D["lig_station.json"]
    steps = list((sf or {}).get("steps", {}).keys())
    for st in steps:
        s = sf["steps"][st]
        fp = s["seat_TC02"]["footprint"]
        cl = sorted(fp.get("clusters", []), key=lambda c: -abs(c["Fn_N"]))[:3]
        e = {"label": s["label"], "HEAD_N": s["screw"]["HEAD_on_screw_along_n_N"], "N_plane_N": s["screw"]["N_plane_N_tension_pos"],
             "V_plane_N": s["screw"]["V_plane_N"], "seat_window_N": fp["window_daz9_zp9_N"], "seat_outside_window_N": fp["outside_window_N"],
             "footprint": {"centroid_z_prime_mm": fp["centroid_force_weighted"]["z_prime_mm"], "centroid_daz_deg": fp["centroid_force_weighted"]["daz_deg"],
                           "r_prime_force_weighted_mm": fp["r_prime_force_weighted_mm"], "extent_z_prime_mm": fp["extent_CPRESS_pos"]["z_prime_mm"],
                           "extent_daz_deg": fp["extent_CPRESS_pos"]["daz_deg"], "n_clusters": fp["n_clusters"],
                           "clusters_top3": [{"Fn_N": c["Fn_N"], "z_prime_mm": c["z_prime_mm"], "daz_deg": c["daz_deg"]} for c in cl]},
             "shell_pull_N": s["shell_TC02"]["shell_pull_N_tie_minus_seat"]}
        if sh and st in sh["steps"]:
            k = sh["steps"][st]
            pe = k["plane_exact"]
            m286 = min(k["sections"], key=lambda q: abs(q["x"] - 28.6))
            e["shank"] = {"M_max_threaded": k["M_max_threaded"], "M_max_shank_in_TC01": k["M_max_shank_in_TC01"],
                          "plane_exact_N_N": pe["N_N"], "plane_exact_V_N": pe["V_N"], "section_x28.6": m286,
                          "arm_M_over_V_at_x28.6_mm": round(m286["M"] / max(abs(pe["V_N"]), 1e-9), 3)}
        if cm and st in cm["steps"]:
            c = cm["steps"][st]
            p = c["patch"]
            hb = p["hole_bearing"]
            V = s["screw"]["V_plane_N"]
            sbr = V / (D_SCREW * t_eff)
            e["band"] = {k: p["under_head_band"][k] for k in ("vm_MPa", "node", "x_prime", "r_prime", "d_hole_mm", "MS_y_SF1_elastic",
                                                             "neuber_MS_strain_n15", "neuber_MS_strain_n30")}
            e["hole_bearing_posted"] = hb
            e["hole_bearing_t_eff"] = {"t_eff_mm": t_eff, "sigma_br_MPa": round(sbr, 1), "MS_y_SF1": round(hb["Fbry_MPa"] / sbr - 1, 3),
                                       "MS_u_SF1": round(hb["Fbru_MPa"] / sbr - 1, 3), "basis": "V_plane / (5.0 x t_eff), Fbry / Fbru as posted"}
            e["lines"] = {"seat_line_min": p["lines"]["seat"], "ring_line_min": p["lines"]["ring"], "hole_edge_line_min": p["lines"]["hole_edge"],
                          "relax_seat_lines_summary": c.get("relax_seat_lines_summary")}
            e["forces_patch"] = p["forces"]
            e["vs_gref"] = {"global_job": cm.get("global_job"), "global_sets_from": cm.get("global_sets_from"),
                            "rel_patch_vs_global": c.get("rel_patch_vs_global")}
        if lg and st in lg.get("steps", {}):
            g = lg["steps"][st]
            e["lig_station"] = {sd: {k: g[sd][k] for k in ("r_start_mm", "d_hole_wall_at_start_mm", "clipped_mm", "length_mm", "Pm", "PmPb")}
                                for sd in ("side-", "side+") if sd in g}
            e["TC02_thread_resultant"] = g.get("TC02_thread_resultant")
        out["steps"][st] = e
    h = D["histcheck.json"]
    if h:
        for st, p in h.get("pairs", {}).items():
            out["repeats"][st] = {"vs": p["B_reference"], "pass": p["pass"], "criterion_5pct": p["criterion_5pct"],
                                  "N": p["N"], "M_shear_plane": p["M_shear_plane"], "M_max_threaded": p["M_max_threaded"],
                                  "seat_window": p["seat_window"], "HEAD": p["HEAD"],
                                  "lines_max_abs_rel_PmPb": p["lines"]["seat"]["max_abs_rel_PmPb"], "lines_n_gt_5pct": p["lines"]["seat"]["n_gt_5pct"],
                                  "lines_min_MS_PQ": [p["lines"]["seat"]["min_MS_PQ_A"], p["lines"]["seat"]["min_MS_PQ_B"]]}
    for r in refs:
        hr = D.get(f"histcheck_{r}.json")
        if hr:
            out["refs"][r] = {st: {"N": p["N"], "M_shear_plane": p["M_shear_plane"], "M_max_threaded": p["M_max_threaded"], "seat_window": p["seat_window"],
                                   "HEAD": p["HEAD"], "lines_max_abs_rel_PmPb": p["lines"]["seat"]["max_abs_rel_PmPb"],
                                   "lines_min_MS_PQ": [p["lines"]["seat"]["min_MS_PQ_A"], p["lines"]["seat"]["min_MS_PQ_B"]], "pass_5pct": p["pass"]}
                              for st, p in hr.get("pairs", {}).items()}
    (R / "summary.json").write_text(json.dumps(out, indent=1))
    # compact print
    print(f"{job}: t_eff {t_eff}")
    for st, e in out["steps"].items():
        sk = e.get("shank", {})
        hb = e.get("hole_bearing_t_eff", {})
        ln = (e.get("lines") or {}).get("relax_seat_lines_summary") or {}
        print(f"{st:11s} HEAD {e['HEAD_N']:7.1f} N {e['N_plane_N']:7.1f} V {e['V_plane_N']:7.1f} | win {e['seat_window_N']:7.1f} out {e['seat_outside_window_N']:6.1f} "
              f"cz' {e['footprint']['centroid_z_prime_mm']:+.2f} r' {e['footprint']['r_prime_force_weighted_mm']:.2f} ncl {e['footprint']['n_clusters']} | "
              f"pull {e['shell_pull_N']:7.1f} | Mthr {sk.get('M_max_threaded', {}).get('M', float('nan')):7.1f} @x' {sk.get('M_max_threaded', {}).get('x', float('nan'))} "
              f"M28.6 {sk.get('section_x28.6', {}).get('M', float('nan')):7.1f} arm {sk.get('arm_M_over_V_at_x28.6_mm', float('nan'))} | "
              f"br {hb.get('sigma_br_MPa')} MPa MS {hb.get('MS_y_SF1')}/{hb.get('MS_u_SF1')} | 54L min MS_PQ {ln.get('min_MS_PQ_patch')} neg {ln.get('n_lines_MS_PQ_patch_negative')} "
              f"Pm>Fty {ln.get('n_lines_Pm_gt_Fty_patch')}", flush=True)
        if e.get("lig_station"):
            print("            lig " + "; ".join(f"{sd}: r0 {v['r_start_mm']} d {v['d_hole_wall_at_start_mm']} clip {v['clipped_mm']} Pm {v['Pm']} PmPb {v['PmPb']}"
                                         for sd, v in e["lig_station"].items()) + f" | thread {e.get('TC02_thread_resultant')}", flush=True)
    for st, r in out["repeats"].items():
        print(f"repeat {st} vs {r['vs']}: pass {r['pass']} {r['criterion_5pct']} N {r['N']} M28.6 {r['M_shear_plane']} win {r['seat_window']} "
              f"54L max rel {r['lines_max_abs_rel_PmPb']} ({r['lines_n_gt_5pct']} > 5 %)", flush=True)
    print("wrote", R / "summary.json", sha16(R / "summary.json"))


if __name__ == "__main__":
    a = sys.argv[1:]
    kw = dict(x.split("=", 1) for x in a[1:] if x.startswith("t_eff="))
    refs = [x.split("=", 1)[1] for x in a[1:] if x.startswith("ref=")]
    main(a[0], float(kw.get("t_eff", 2.388)), refs)
