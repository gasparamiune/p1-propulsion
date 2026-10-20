"""REV-MECH-2 (independent reviewer): does the FEA3D 3D model tie or merge the two designed clearances that the S-AX
0.10 mm thermal-mesh closure rule joins at the governing TC-03 / TC-02 results (lead message 2026-10-20)?

Own code on FEA3D's stored decks / fields (lc1v351_c71, fea3d-asm v1.2, 'design' ties, TB1 'faces'); nothing is re-solved.
 1. TC03_TC02_seat tie census from the deck *EQUATION terms (dependent TC-03 node, all other terms TC-02 nodes), split into
    flange OD (r ~10.0, designed 0.10 mm radial clearance to the TC-02 counterbore r 10.1), shoulder (z 107.51) and end face
    (z 117.51); faceting of the TC-02 counterbore wall; distances of the TC-03 governing node n44861.
 2. TC-01 / TC-02 structural coupling (f7/H8 fit): equations that contain both TC-01 and TC-02 nodes.
 3. Mapped temperatures (TH step of each solved deck) across both interfaces, 4 S-AX states: nearest-node pairs and dT.
 4. Location of the TC-02 / TC-03 maximum temperature per state; thermal-step stress components at n44861 (B1_1).
 5. FEA3D's own TB1 variants as published (thread-only vs 'faces' on the same R2 mesh), quoted from the hub results.
 6. DERIVED fit-closure thresholds from the CAD fits and engmat CTE.

usage: python -I rm2_closure.py <out.json>
"""
from __future__ import annotations
import sys, json, math, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rm2_repost import load_deck, RUNS, HUB, engmat  # noqa: E402  (own deck cache loader; hub engmat read-only)

RUN = "lc1v351_c71"
STATES = ("B1_1", "B1_2", "B1_19", "B1_21.65")
N_TC03, N_TC02, N_NZ01 = 44861, 26334, (74445, 72033)
K0 = 273.15


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def body_nodes(z, key):
    return np.unique(z[key][:, 1:])


def main(outp):
    out = {"run": RUN, "inputs": {}, "states": {}}
    z, meta = load_deck(RUN, "B1_1")
    for st in STATES:
        out["inputs"][f"{st}/f1.inp.gz"] = sha16(RUNS / RUN / st / "f1.inp.gz")
    out["inputs"]["B1_1/fields.npz"] = sha16(RUNS / RUN / "B1_1" / "fields.npz")
    nid, X = z["nodes_id"], z["nodes_x"]
    pos = {int(n): i for i, n in enumerate(nid)}
    xyz = lambda ns: X[[pos[int(n)] for n in ns]]
    n1, n2, n3 = body_nodes(z, "E_B_TC01"), body_nodes(z, "E_B_TC02"), body_nodes(z, "E_B_TC03")
    S1, S2, S3 = set(n1.tolist()), set(n2.tolist()), set(n3.tolist())
    # ---------------------------------------------------------------- 1. tie census
    nt, T = z["eq_nterm"], z["eq_terms"]
    off = np.concatenate([[0], np.cumsum(nt)])
    dep3, n_12, n_dep2 = {}, 0, 0
    for k in range(len(nt)):
        t = T[off[k]:off[k + 1]]
        nn = [int(a) for a in t[:, 0]]
        if nn[0] in S3 and all(n in S2 for n in nn[1:] if n != nn[0]):   # a rotated-direction equation repeats the dependent node
            dep3[nn[0]] = dep3.get(nn[0], 0) + 1
        if any(n in S1 for n in nn) and any(n in S2 for n in nn):
            n_12 += 1
        if nn[0] in S2:
            n_dep2 += 1
    D = np.array(sorted(dep3))
    P = xyz(D)
    r, zz = np.hypot(P[:, 0], P[:, 1]), P[:, 2]
    cls = {"flange_OD": (r > 9.9) & (zz > 105.4) & (zz < 107.6),
           "shoulder_z107.51": (np.abs(zz - 107.5134) < 0.05) & (r <= 9.9),
           "end_face_z117.51": np.abs(zz - 117.5134) < 0.05}
    other = ~np.any(np.vstack(list(cls.values())), axis=0)
    census = {"n_dep_nodes": int(len(D)), "n_equations": int(sum(dep3.values())),
              "eq_per_node": sorted(set(dep3.values()))}
    for k, m in list(cls.items()) + [("other", other)]:
        census[k] = {"n": int(m.sum())}
        if m.any():
            census[k].update(r_mm=[round(float(r[m].min()), 3), round(float(r[m].max()), 3)],
                             z_mm=[round(float(zz[m].min()), 3), round(float(zz[m].max()), 3)])
    P3, P2 = xyz(n3), xyz(n2)
    r3, z3, r2, z2 = np.hypot(P3[:, 0], P3[:, 1]), P3[:, 2], np.hypot(P2[:, 0], P2[:, 1]), P2[:, 2]
    od_all = (r3 > 9.95) & (z3 > 105.3) & (z3 < 107.7)
    wall = (r2 > 9.5) & (r2 < 10.15) & (z2 > 105.6) & (z2 < 107.4)
    census["TC03_OD_nodes_total"] = int(od_all.sum())
    census["TC02_counterbore_wall_r_mm"] = [round(float(r2[wall].min()), 3), round(float(r2[wall].max()), 3)] if wall.any() else None
    census["chord_radius_11_facets_on_r10.1_mm"] = round(10.1 * math.cos(math.pi / 11), 3)
    g = X[pos[N_TC03]]
    dd = np.linalg.norm(P - g, axis=1)
    census["n44861"] = {"xyz_mm": np.round(g, 4).tolist(), "r_mm": round(float(np.hypot(g[0], g[1])), 4),
                        "dist_nearest_tied_node_mm": round(float(dd.min()), 3),
                        "dist_nearest_tied_OD_node_mm": round(float(dd[cls["flange_OD"]].min()), 3)}
    out["TC03_TC02_seat_tie"] = census
    # ---------------------------------------------------------------- 2. TC-01 / TC-02 coupling
    out["TC01_TC02_coupling"] = {"equations_with_TC01_and_TC02_nodes": int(n_12), "equations_with_TC02_dependent": int(n_dep2)}
    # ---------------------------------------------------------------- 3./4. temperatures per state
    P1 = xyz(n1)
    r1, z1 = np.hypot(P1[:, 0], P1[:, 1]), P1[:, 2]
    for st in STATES:
        zs, _ = load_deck(RUN, st)
        Tm = dict(zip(zs["T_0"][:, 0].astype(int).tolist(), zs["T_0"][:, 1].tolist()))
        T1 = np.array([Tm[int(n)] for n in n1]) - K0
        T2 = np.array([Tm[int(n)] for n in n2]) - K0
        T3 = np.array([Tm[int(n)] for n in n3]) - K0
        res = {}
        # (a) TC-03 flange OD vs TC-02 counterbore wall (incl. ceiling corner nodes)
        m3 = (r3 > 9.95) & (z3 > 105.45) & (z3 < 107.56)
        m2 = (r2 > 9.6) & (r2 < 10.15) & (z2 > 102.4) & (z2 < 107.56)
        d = np.linalg.norm(P3[m3][:, None, :] - P2[m2][None, :, :], axis=2)
        j = d.argmin(1)
        dT = T3[m3] - T2[m2][j]
        res["TC03_OD_vs_TC02_wall"] = {"n_pairs": int(m3.sum()), "pair_dist_mm": [round(float(d.min(1).min()), 3), round(float(d.min(1).max()), 3)],
                                       "dT_K": [round(float(dT.min()), 2), round(float(dT.max()), 2)],
                                       "T_TC03_OD_C": [round(float(T3[m3].min()), 1), round(float(T3[m3].max()), 1)]}
        # (b) f7/H8 fit: TC-02 plug OD vs TC-01 forward bore, common z range
        mp, mb = (r2 > 28.4) & (r2 < 28.65), (r1 > 28.55) & (r1 < 28.8)
        z0, z9 = max(z2[mp].min(), z1[mb].min()), min(z2[mp].max(), z1[mb].max())
        mp &= (z2 >= z0) & (z2 <= z9)
        mb &= (z1 >= z0) & (z1 <= z9)
        d = np.linalg.norm(P2[mp][:, None, :] - P1[mb][None, :, :], axis=2)
        j = d.argmin(1)
        dT = T2[mp] - T1[mb][j]
        close = d.min(1) <= 1.0
        res["f7H8_plug_vs_bore"] = {"z_mm": [round(float(z0), 2), round(float(z9), 2)], "n_pairs": int(mp.sum()),
                                    "dT_K_all_pairs": [round(float(dT.min()), 2), round(float(dT.max()), 2)],
                                    "n_pairs_within_1mm": int(close.sum()),
                                    "dT_K_pairs_within_1mm": [round(float(dT[close].min()), 2), round(float(dT[close].max()), 2)] if close.any() else None,
                                    "T_plug_C": [round(float(T2[mp].min()), 1), round(float(T2[mp].max()), 1)]}
        for nm, ns, Tb, Pb in (("TC-02", n2, T2, P2), ("TC-03", n3, T3, P3)):
            i = int(np.argmax(Tb))
            res[f"{nm}_Tmax"] = {"node": int(ns[i]), "T_C": round(float(Tb[i]), 2), "r_mm": round(float(np.hypot(Pb[i, 0], Pb[i, 1])), 3),
                                 "z_mm": round(float(Pb[i, 2]), 3)}
        res["T_C_n44861"] = round(Tm[N_TC03] - K0, 2)
        res["T_C_n26334"] = round(Tm[N_TC02] - K0, 2)
        # flange gap change from the mapped temperatures (DERIVED; CTE engmat mean values, TC-03 GlidCop / TC-02 6061)
        a2 = engmat.prop("AL6061-T6", "alpha", float(T2[m2].mean()))
        a3 = engmat.prop("GLIDCOP-AL15", "alpha", float(T3[m3].mean()))
        res["flange_gap_mm_hot"] = round(0.10 + 10.1 * a2 * (float(T2[m2].mean()) - 20.0) - 10.0 * a3 * (float(T3[m3].mean()) - 20.0), 4)
        out["states"][st] = res
    # thermal-step stress at the TC-03 corner, B1_1 (cylindrical components; the node lies on the -x axis)
    F = np.load(RUNS / RUN / "B1_1" / "fields.npz")
    s = F["S_TH"][N_TC03, :6].astype(float)
    ang = math.atan2(g[1], g[0])
    c, sn = math.cos(ang), math.sin(ang)
    srr = c * c * s[0] + sn * sn * s[1] + 2 * c * sn * s[3]
    stt = sn * sn * s[0] + c * c * s[1] - 2 * c * sn * s[3]
    out["n44861_S_TH_B1_1_MPa"] = {"s_rr": round(srr, 1), "s_tt": round(stt, 1), "s_zz": round(s[2], 1),
                                   "OP_minus_TH_s_tt": round(float((F["S_OP"][N_TC03, 1] - F["S_TH"][N_TC03, 1])), 2),
                                   "PM_minus_TH_s_tt": round(float((F["S_PM"][N_TC03, 1] - F["S_TH"][N_TC03, 1])), 2)}
    # NZ-01 governing nodes: distance to the NZ-01 OD (r 22.0)
    nz = body_nodes(z, "E_B_NZ01")
    rz = np.hypot(xyz(nz)[:, 0], xyz(nz)[:, 1])
    out["NZ01_nodes"] = {}
    for gnode in N_NZ01:
        x = X[pos[gnode]]
        out["NZ01_nodes"][str(gnode)] = {"r_mm": round(float(np.hypot(x[0], x[1])), 3), "z_mm": round(float(x[2]), 3),
                                         "dist_to_OD_mm": round(float(rz.max() - np.hypot(x[0], x[1])), 3)}
    # ---------------------------------------------------------------- 5. FEA3D's TB1 variants as published
    th = HUB / "04-fea/assembly3d/results/f1_post_tc03_thread.json"
    cv = HUB / "04-fea/assembly3d/results/f1_convergence.json"
    TH = json.loads(th.read_text())
    CV = json.loads(cv.read_text())
    pub = {"f1_post_tc03_thread.json": sha16(th), "f1_convergence.json": sha16(cv), "thread_variant": {}, "faces_levels": []}
    pub["thread_variant"]["version"] = TH.get("version")
    pub["thread_variant"]["refine_TC03"] = TH["variant"]["refine"].get("TC-03")
    for e in TH["states"]["B1_1"]["cases"]["LC1"]["margins"]:
        if e["part"] == "TC-03" and e["set"] == "regular":
            pub["thread_variant"]["TC03_B1_1_regular"] = {"MS": round(e["MS"], 3), "MS_ult": round(e["MS_ult"], 3), "vm_MPa": round(e["vm_MPa"], 1),
                                                         "vm_thermal_MPa": round(e["vm_thermal_MPa"], 1), "node_xyz": e["xyz_mm"]}
    pt = CV["points"]["TC-03 flange corner (B1_1)"]
    for lv in pt["levels"]:
        pub["faces_levels"].append({"level": lv["level"], "run": lv["run"], "h_loc_mm": round(lv["h_loc_mm"], 3),
                                    "MS_min_reg": round(lv["MS_min_reg"], 3), "q_max_reg_MPa": round(lv["q_max_reg_MPa"], 1)})
    for runname in ("conv_r2", "tc03_thread"):
        Mj = json.loads((RUNS / runname / "model.json").read_text())
        pub[f"{runname}_model"] = {"version": Mj.get("version"), "tb1": Mj["variant"].get("tb1"),
                                   "refine_TC03": Mj["variant"].get("refine", {}).get("TC-03"),
                                   "TC03_ties": [(t["label"], t["n_dep_nodes"], t["n_eq"]) for t in Mj["ties"] if "TC03" in t["label"]]}
    out["FEA3D_TB1_variants_published"] = pub
    # ---------------------------------------------------------------- 6. fit-closure thresholds (DERIVED)
    a = engmat.prop("AL6061-T6", "alpha", 100.0)
    rf = 28.6
    fits = {"CAD_nominal": (57.25 - 57.20) / 2, "toleranced_min": (57.25 - 57.17) / 2, "toleranced_max": (57.296 - 57.14) / 2}
    out["f7H8_closure_threshold"] = {"alpha_6061_100C": a, "r_mm": rf,
                                     **{k: {"radial_clearance_mm": round(v, 4), "dT_plug_minus_bore_to_close_K": round(v / (rf * a), 1)}
                                        for k, v in fits.items()}}
    Path(outp).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
