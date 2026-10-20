"""FEA3D J-FWD margin-matrix cells from the contact sub-model posts (fea3d 2026-10-20 ~06:50Z; lead 06:17Z item 3 classes, CHANGELOG 231 (1)
criterion (i)-(iii), 234 (1)(b) screw form, 234 (4) all-node rule).  DERIVED from SIM posts (jfwd/runs/<job>/post.json or post_partial.json
and spotface.json); no new run.

Per step and member:
  TC-02  cell = lower of the band value (> 1 mm from the tap) and the A_n internal-thread shear check; the all-node value (tie edge of the
         bonded thread) is information (class TIE-EDGE, node, distance).
  TC-01  all-node at the hole / head edge = contact singularity (information, class CONTACT-EDGE); cell per 183 (1) / 231 (1):
         soak / preload (secondary): P+Q on the SCLs <= 2 Fty(T) and the under-head band by the local-strain (Neuber) check (class DC
         head seat, lead 06:36Z);  FA1 / LC2 (primary): SCL Pm and Pm+Pb <= Fty / Ftu at the case SF (no bending shape credit, S-AX
         convention), hole bearing V / (D t) <= Fbry / Fbru (e/D 2.18, engmat e/D 2.0 ratios), and the hole-edge peaks of both members by
         Neuber (231 (1)(iii), one-off abnormal FA-1); the band elastic value is reported beside.
  SCREW  234 (1)(b): soak = tension on A_s against k_T Rp0.2 / k_Tu Rm; LC2 = combined vM (max preload on A_s + factored shear on A_3) and
         Rt^2 + Rs^2; FA1 = ultimate interaction with the max preload (criterion) + shear-only yield on A_3 (with the preload-relaxation
         argument and the 233 (4) replace rule) + the combined vM for information.  Tension = exact K u head resultant.
07:15Z revision: the TC-01 net-ligament value is the ligament average of jfwd_ligament.py (ligament.json; ASME VIII-2 Table 5.6 typical
ligament: Pm through the ligament cross section, Pb across the width), the half-ligament (one side) averages taken (max of the two sides);
the jfwd_post 'TC01_net_ligament_hole_flank*' lines are SUPERSEDED (partly inside the hole, extrapolated; hole-edge in-plane Kt) and not
used; soak P+Q = max over the full-wall ligament stations (CAD and spot-face seat) and the shear-out lines; FA1 / LC2 local check (iii) =
Neuber on the band value of each member (the all-node value is the contact / tie edge: information); TC-02 cell given both by the lead
06:17Z rule as written (lower of elastic band and A_n thread shear) and by 231 (1) ((i) SCL, (ii) thread / tap bearing, (iii) band Neuber).
07:35Z (lead 07:21Z rulings): TC-02 'cell_ruled' = the 06:17Z rule (lower of band and A_n thread) where the band is a regular body
stress; where the band node lies in a contact-edge field (<= 1.5 mm from the TC-01 hole-edge footprint on the TC-02 OD, as node 13503
at FA1S: 1.05 mm, FIT CPRESS max 0.24 mm from it) the elastic band is information and the (iii) Neuber stands in its place; the cell
record carries the through-wall SCL at the band node (Pm, Pm+Pb, radial, OD to the first free surface) as a check that must pass.
TC-01 under-head (soak) cell class: 'DC adopted (d10.5 spot face, V352_R4_JFWD_SPOT), FE closure pending' with the [DERIVED] seat values.
usage: jfwd_cells.py JOB [partial] -> jfwd/runs/JOB/cells.json"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_post as JP     # noqa: E402

RUNS = Path("/home/claude/work/fea3d/jfwd/runs")
AS, A3M, AN = 14.18, 12.69, 63.5


def ms(allow, s):
    return round(allow / max(s, 1e-9) - 1.0, 3)


def cells(job, partial=False):
    wd = RUNS / job
    d = json.loads((wd / ("post_partial.json" if partial else "post.json")).read_text())
    sp = json.loads((wd / "spotface.json").read_text()) if (wd / "spotface.json").exists() else {"steps": {}}
    lgf = wd / ("ligament_partial.json" if partial and (wd / "ligament_partial.json").exists() else "ligament.json")
    lg = json.loads(lgf.read_text()) if lgf.exists() else {"steps": {}}
    spot = d["meta"].get("seat") == "spot"
    out = {"job": job, "doc": __doc__.split("usage:")[0].strip(), "mu": d["meta"]["mu"], "preload_N": d["meta"]["preload_N"],
           "seat": "spot" if spot else "cad", "FIT_clearance_mm": d["meta"].get("FIT_clearance_mm"), "steps": {}}
    for st, o in d["steps"].items():
        rule = o["case_rule"]
        kind = rule["kind"]
        sfy, sfu = rule["member_SF"]
        sc = o["screw_check"]
        ce = o.get("contact_exact", {})
        N = ce.get("HEAD_on_screw_along_axis_N", sc["N_N"])
        V = sc["V_N"]
        Rp, Rm = sc["kT_Rp_MPa"], sc["kTu_Rm_MPa"]
        scr = {"N_exact_N": N, "N_section_N": sc["N_N"], "V_section_N": V, "V_bear_exact_N": ce.get("BEAR_shear_perp_axis_N"),
               "T_C": sc["T_screw_C"], "kT_Rp_MPa": Rp, "kTu_Rm_MPa": Rm}
        st_ = N / AS
        if kind == "soak":
            scr.update({"form": "tension on A_s (soak)", "MS_y": ms(Rp, st_), "MS_u": ms(Rm, st_)})
        else:
            fy = rule["SF_y"] if kind == "LC2" else 1.0
            fu = rule["SF_u"] if kind == "LC2" else 1.0
            tau = fy * V / A3M
            svm = math.sqrt(st_ ** 2 + 3 * tau ** 2)
            q = (N / (Rm * AS)) ** 2 + (fu * V / (0.6 * Rm * A3M)) ** 2
            scr.update({"sigma_t_MPa": round(st_, 1), "tau_A3_MPa": round(tau, 1), "sigma_vm_MPa": round(svm, 1),
                        "MS_y_combined": ms(Rp, svm), "Rt2_Rs2": round(q, 4), "MS_u_interaction": round(1 / math.sqrt(q) - 1, 3),
                        "MS_y_shear_only_A3": ms(0.577 * Rp, V / A3M)})
            if kind == "FA1":
                scr["form"] = "FA1 (234 (1)(b)): ultimate interaction = criterion; yield shear-only on A_3 (preload relaxation + 233 (4) replace rule)"
                scr["MS_y"], scr["MS_u"] = scr["MS_y_shear_only_A3"], scr["MS_u_interaction"]
            else:
                scr["form"] = f"{kind}: combined vM (preload on A_s + factored shear on A_3) / Rt^2 + Rs^2"
                scr["MS_y"], scr["MS_u"] = scr["MS_y_combined"], scr["MS_u_interaction"]
        thr = sc["TC02_thread"]
        tau_n = N / AN
        T02 = thr["T02_C"]
        thr_y = round(0.577 * JP.tab("AL6061-T6", "Fty", T02) / (sfy * tau_n) - 1, 3)
        thr_u = round(0.6 * JP.tab("AL6061-T6", "Ftu", T02) / (sfu * tau_n) - 1, 3)
        # TC-02
        t2 = o["TC-02"]
        c02 = {"all_node_info": {"vm_MPa": t2["all"]["vm_max_MPa"], "node": t2["all"]["node"], "x_prime": t2["all"]["x_prime"],
                                 "dist_tap_mm": t2["all"]["dist_hole_or_tap_mm"], "class": "TIE-EDGE (bonded thread)",
                                 "MS_y": t2["all"]["MS_y_case"], "MS_u": t2["all"]["MS_u_case"]},
               "band": {"vm_MPa": t2["band"]["vm_max_MPa"], "node": t2["band"]["node"], "MS_y": t2["band"]["MS_y_case"], "MS_u": t2["band"]["MS_u_case"]},
               "thread_shear_An": {"tau_MPa": round(tau_n, 1), "T_C": T02, "MS_y": thr_y, "MS_u": thr_u}}
        c02["cell"] = {"MS_y": min(c02["band"]["MS_y"], thr_y), "MS_u": min(c02["band"]["MS_u"], thr_u),
                       "governs": "thread shear A_n" if thr_y <= c02["band"]["MS_y"] else "band"}
        # TC-01
        t1 = o["TC-01"]
        T01 = t1["band"]["T_C"]
        Fty, Ftu = JP.tab("AL6061-T6", "Fty", T01), JP.tab("AL6061-T6", "Ftu", T01)
        scl = o.get("SCL", {})
        lines01 = {k: v for k, v in scl.items() if k.startswith("TC01_shear_out")}
        lgo = lg["steps"].get(st)
        sup = {k: {"Pm": round(v["Pm"], 1), "PmPb": round(v["PmPb"], 1), "min_bary": round(v["min_bary"], 3)}
               for k, v in scl.items() if k.startswith("TC01_net_ligament_hole_flank")}
        lines02 = {k: v for k, v in scl.items() if k.startswith("TC02_")}
        c01 = {"all_node_info": {"vm_MPa": t1["all"]["vm_max_MPa"], "node": t1["all"]["node"], "dist_hole_mm": t1["all"]["dist_hole_or_tap_mm"],
                                 "class": "CONTACT-EDGE (hole / head edge)", "MS_y": t1["all"]["MS_y_case"], "MS_u": t1["all"]["MS_u_case"]},
               "band_elastic": {"vm_MPa": t1["band"]["vm_max_MPa"], "node": t1["band"]["node"], "dist_hole_mm": t1["band"]["dist_hole_or_tap_mm"],
                                "T_C": T01, "MS_y": t1["band"]["MS_y_case"], "MS_u": t1["band"]["MS_u_case"]},
               "neuber_band": JP.neuber_check(float(t1["band"]["vm_max_MPa"]), float(T01))}
        if kind == "soak":
            pq = {k: ms(2 * Fty, v["PmPb"]) for k, v in lines01.items()}
            if lgo:
                for key in ("cad", "seat"):
                    smx = lgo["station_average"][key]["station_max_PmPb"]
                    pq[f"ligament_station_max_{key}"] = ms(2 * Fty, smx["PmPb"])
                    c01[f"SCL_PQ_ligament_station_max_{key}"] = dict(smx, MS_PQ_2Fty=ms(2 * Fty, smx["PmPb"]))
                pq_seat = pq.pop("ligament_station_max_seat")
                c01["SCL_PQ_seat_DERIVED"] = pq_seat
            c01["SUPERSEDED_hole_flank_lines_not_used"] = sup
            pq02 = {k: ms(2 * JP.tab("AL6061-T6", "Fty", T02), v["PmPb"]) for k, v in lines02.items()}
            nb = c01["neuber_band"]
            c01["SCL_PQ_shakedown_2Fty"] = pq
            c02["SCL_PQ_shakedown_2Fty"] = pq02
            nmin = min(nb["n15"]["MS_strain"], nb["n30"]["MS_strain"])
            spo_ = sp["steps"].get(st, {})
            c01["cell"] = {"MS_strain_neuber": nmin, "MS_PQ_min": min(pq.values()) if pq else None,
                           "governs": "under-head band local strain (class DC head seat, lead 06:36Z)",
                           **({"FE_spot_face": "spot-face mesh: the FE is the seat (no [DERIVED] scaling); mu %s; the mu 0.2 closure = local seat "
                                               "sub-model (lead 08:17Z)" % d["meta"]["mu"]} if spot else {}),
                           "class": "DC adopted (d10.5 spot face at r 31.313, wall 2.688 at the hole, V352_R4_JFWD_SPOT; lead 07:21Z), FE closure pending "
                                    "(mu 0.2 / 3750 N seat run)",
                           "seat_values_DERIVED": {"flat_seat_bearing_MS_vs_Fbry": spo_.get("head_bearing", {}).get("flat_seat_MS_vs_Fbry"),
                                                   "PQ_seat_MS_2Fty": c01.get("SCL_PQ_seat_DERIVED")},
                           "CAD_as_found": {"neuber_band_MS_strain": nmin, "band_elastic_MS_y": t1["band"]["MS_y_case"]}}
        else:
            prim = {k: {"Pm": round(v["Pm"], 1), "PmPb": round(v["PmPb"], 1), "MS_y_Pm": ms(Fty, sfy * v["Pm"]), "MS_y_PmPb": ms(Fty, sfy * v["PmPb"]),
                        "MS_u_Pm": ms(Ftu, sfu * v["Pm"]), "MS_u_PmPb": ms(Ftu, sfu * v["PmPb"])} for k, v in lines01.items()}
            Fty2, Ftu2 = JP.tab("AL6061-T6", "Fty", T02), JP.tab("AL6061-T6", "Ftu", T02)
            prim02 = {k: {"Pm": round(v["Pm"], 1), "PmPb": round(v["PmPb"], 1), "MS_y_Pm": ms(Fty2, sfy * v["Pm"]), "MS_y_PmPb": ms(Fty2, sfy * v["PmPb"]),
                          "MS_u_Pm": ms(Ftu2, sfu * v["Pm"]), "MS_u_PmPb": ms(Ftu2, sfu * v["PmPb"])} for k, v in lines02.items()}
            if lgo:
                la = lgo["ligament_avg_CAD"]
                Pm_l = max(la["side-"]["Pm"], la["side+"]["Pm"])
                PmPb_l = max(la["side-"]["PmPb"], la["side+"]["PmPb"])
                prim["TC01_net_ligament_avg_half"] = {"Pm": Pm_l, "PmPb": PmPb_l, "MS_y_Pm": ms(Fty, sfy * Pm_l), "MS_y_PmPb": ms(Fty, sfy * PmPb_l),
                                                      "MS_u_Pm": ms(Ftu, sfu * Pm_l), "MS_u_PmPb": ms(Ftu, sfu * PmPb_l),
                                                      "Fz_section_N": la["both"]["Fz_N"], "full_ligament_both_sides": {"Pm": la["both"]["Pm"], "PmPb": la["both"]["PmPb"]}}
                se = lgo["station_average"]["seat"]
                c01["SCL_ligament_seat_DERIVED"] = {"Pm": se["Pm"], "PmPb": se["PmPb"], "MS_y_Pm": ms(Fty, sfy * se["Pm"]), "MS_y_PmPb": ms(Fty, sfy * se["PmPb"]),
                                                    "MS_u_Pm": ms(Ftu, sfu * se["Pm"]), "MS_u_PmPb": ms(Ftu, sfu * se["PmPb"]),
                                                    "station_CAD": {k_: lgo["station_average"]["cad"][k_] for k_ in ("Pm", "PmPb")}}
                c01["hole_edge_station_local_info"] = lgo["station_average"]["cad"]["station_max_PmPb"]
            c01["SUPERSEDED_hole_flank_lines_not_used"] = sup
            c01["SCL_primary"] = prim
            c02["SCL_primary"] = prim02
            spo = sp["steps"].get(st, {})
            hb = spo.get("hole_bearing", {})
            c01["hole_bearing"] = hb
            c01["neuber_all_node_iii"] = JP.neuber_check(float(t1["all"]["vm_max_MPa"]), float(t1["all"]["T_C"]))
            c02["neuber_all_node_iii"] = JP.neuber_check(float(t2["all"]["vm_max_MPa"]), float(t2["all"]["T_C"]))
            ys = [min(p["MS_y_Pm"], p["MS_y_PmPb"]) for p in prim.values()]
            us = [min(p["MS_u_Pm"], p["MS_u_PmPb"]) for p in prim.values()]
            hbr = hb.get("spot_t2.688") or hb.get("CAD_t3.125")       # 08:35Z: spot-face mesh -> the FE wall 2.688
            if hbr:
                ys.append(hbr["MS_y"])
                us.append(hbr["MS_u"])
            c01["neuber_all_node_info"] = c01.pop("neuber_all_node_iii")
            c02["neuber_all_node_info"] = c02.pop("neuber_all_node_iii")
            nb = c01["neuber_band"]
            k1 = 1.0 if spot else 3.125 / 2.69
            c01["neuber_band_seat_DERIVED" if not spot else "neuber_band_FE_spot"] = {"k1": JP.neuber_check(k1 * float(t1["band"]["vm_max_MPa"]), float(T01)),
                                               "k1sq_bound": JP.neuber_check(k1 * k1 * float(t1["band"]["vm_max_MPa"]), float(T01))}
            c01["cell"] = {"MS_y_primary_bearing": round(min(ys), 3) if ys else None, "MS_u_primary_bearing": round(min(us), 3) if us else None,
                           "MS_strain_neuber_band_iii": min(nb["n15"]["MS_strain"], nb["n30"]["MS_strain"]),
                           "governs": "min of SCL primary (i: ligament average + shear-out), hole bearing (ii) and the band Neuber (iii); "
                                      "elastic band and all-node = information (contact edge)"}
            # (ii) tapped-thread bearing in TC-02 [DERIVED]: mean bearing of the screw shear on the engaged length (tip x' 21.75 to the
            # TC-02 OD x' 28.6: 6.85 mm) at the thread major D 5.0 against Fbry / Fbru = 1.40 Fty / 1.60 Ftu (engmat e/D 2.0 ratios)
            sb = V / (5.0 * 6.85)
            c02["tap_bearing_derived"] = {"sigma_MPa": round(sb, 1), "L_e_mm": 6.85, "MS_y": ms(1.40 * Fty2, sfy * sb), "MS_u": ms(1.60 * Ftu2, sfu * sb)}
            ys2 = [min(p["MS_y_Pm"], p["MS_y_PmPb"]) for p in prim02.values()]
            us2 = [min(p["MS_u_Pm"], p["MS_u_PmPb"]) for p in prim02.values()]
            if ys2:
                c02["cell_SCL"] = {"MS_y": round(min(ys2), 3), "MS_u": round(min(us2), 3)}
            nb2 = JP.neuber_check(float(t2["band"]["vm_max_MPa"]), float(t2["band"]["T_C"]))
            c02["neuber_band_iii"] = nb2
            if lgo:
                c02["band_excl_TC01_hole_edge_footprint"] = lgo["TC02_band"]["band_gt1_tap_and_gt1_TC01_hole_edge"]
                c02["FIT_CPRESS_max_info"] = lgo.get("FIT_CPRESS_max_on_TC02")
            c02["cell_231_1"] = {"MS_y": round(min(min(ys2) if ys2 else 9e9, thr_y, c02["tap_bearing_derived"]["MS_y"]), 3),
                                 "MS_u": round(min(min(us2) if us2 else 9e9, thr_u, c02["tap_bearing_derived"]["MS_u"]), 3),
                                 "MS_strain_neuber_band_iii": min(nb2["n15"]["MS_strain"], nb2["n30"]["MS_strain"]),
                                 "governs": "(i) SCL shear-out / net ligament, (ii) A_n thread shear and tap bearing, (iii) band Neuber; elastic band = information"}
            c02["cell_rule_0617_as_written"] = c02.pop("cell")
        # TC-02 ruled cell (lead 07:21Z)
        lw = (lgo or {}).get("TC02_wall_SCL", {}).get("band_node")
        bfp = (lgo or {}).get("TC02_band", {}).get("band_gt1_tap", {})
        d_fp = bfp.get("d_TC01_hole_edge_mm")
        contact_field = d_fp is not None and d_fp <= 1.5
        if lw:
            lw = dict(lw, MS_y_Pm=ms(lw["Fty_MPa"], sfy * lw["Pm"]), MS_y_PmPb=ms(lw["Fty_MPa"], sfy * lw["PmPb"]),
                      MS_u_Pm=ms(lw["Ftu_MPa"], sfu * lw["Pm"]), MS_u_PmPb=ms(lw["Ftu_MPa"], sfu * lw["PmPb"]))
            lw["pass"] = min(lw["MS_y_Pm"], lw["MS_y_PmPb"], lw["MS_u_Pm"], lw["MS_u_PmPb"]) >= 0.0
        c02["wall_SCL_band_node"] = lw
        c02["band_node_d_TC01_hole_edge_mm"] = d_fp
        if contact_field:
            nbx = c02.get("neuber_band_iii") or JP.neuber_check(float(t2["band"]["vm_max_MPa"]), float(t2["band"]["T_C"]))
            c02["neuber_band_iii"] = nbx
            cand_y = [thr_y] + ([c02["tap_bearing_derived"]["MS_y"]] if "tap_bearing_derived" in c02 else []) + ([c02["cell_SCL"]["MS_y"]] if "cell_SCL" in c02 else [])
            cand_u = [thr_u] + ([c02["tap_bearing_derived"]["MS_u"]] if "tap_bearing_derived" in c02 else []) + ([c02["cell_SCL"]["MS_u"]] if "cell_SCL" in c02 else [])
            c02["cell_ruled"] = {"MS_y": round(min(cand_y), 3), "MS_u": round(min(cand_u), 3),
                                 "class": "band in a contact-edge field (%.2f mm from the TC-01 hole-edge footprint): elastic band = information "
                                          "(%.1f MPa, MS %+.3f / %+.3f); (iii) Neuber MS_strain %+.3f; wall SCL at node %s %s (lead 07:21Z)" % (
                                              d_fp, t2["band"]["vm_max_MPa"], t2["band"]["MS_y_case"], t2["band"]["MS_u_case"],
                                              min(nbx["n15"]["MS_strain"], nbx["n30"]["MS_strain"]), lw["node"] if lw else None,
                                              ("passes (Pm %+.3f, Pm+Pb %+.3f)" % (lw["MS_y_Pm"], lw["MS_y_PmPb"])) if lw and lw["pass"] else "FAILS" if lw else "n/a"),
                                 "governs": "A_n thread shear" if min(cand_y) == thr_y else "other (ii)/(i)"}
        else:
            c02["cell_ruled"] = dict(c02.get("cell_rule_0617_as_written") or c02.get("cell"), **{"class": "06:17Z rule: band is a regular body stress"})
        out["steps"][st] = {"kind": kind, "label": o.get("label"), "SF_member": [sfy, sfu], "SCREW": scr, "TC-01": c01, "TC-02": c02,
                            "FIT_radial_N": ce.get("FIT_radial_on_TC01_N")}
    (wd / "cells.json").write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    r = cells(sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "partial")
    for st, v in r["steps"].items():
        print(st, v["kind"], "SCREW", {k: v["SCREW"].get(k) for k in ("N_exact_N", "V_section_N", "MS_y", "MS_u")},
              "TC-02 cell", v["TC-02"].get("cell_ruled"),
              "TC-01 cell", v["TC-01"]["cell"])
