"""TC-03 flange-corner stresses of S-AX runs (Mechanical, 2026-10-20; lead 2026-10-20 gap-conductance variant (2) + (4)).  No solve.
r4 copy (2026-10-20 ~08:10Z, lead 07:51Z: FEA3D global lc1v352g n46040 (r 9.8, z 105.51) at B1_1 LC1 / LC2, both bounds, class and P+Q):
v352r4 tree, fields through sax.load_res_any (float32 -> float64; trimmed res_sub.npz states), nodal P+Q = 2 Fty(T) / vm - 1 (as S-AX
evaluate), the thermal share vm_thermal / vm and the distance to the nearest singular point added per region minimum.

For each S-AX run directory (runs/structural/<run>, solved by sax.py) and each load case that loads the TC-03 seat insert, the stresses
of the TC-03 nodes at the flange front corner, where FEA3D reports its TC-03 negative (r 9.8 at the flange front face z_fl0 = z_ins_top - 12,
v3.5.1 FEA3D frame (9.8, 105.51)), per state: von Mises total (thermal + mechanical) and primary (mechanical only), node temperature,
Fty(T) / Ftu(T) (engmat, GlidCop AL-15 CONDITIONAL above 20 C), MS = Fty/(SF_y vm) - 1, MS_ult = Ftu/(SF_u vm) - 1, MS_primary =
Fty/(SF_y vm_mech) - 1, and whether the node is in the S-AX 'regular' set (outside 1.0 mm of a singular point of that run's ties).
Regions: 'fea3d_point' = the TC-03 node nearest (9.8, z_fl0); 'corner_r0.5' = TC-03 nodes within 0.5 mm of the flange front outer corner
(10.0, z_fl0); 'flange_top_corner_r0.5' = within 0.5 mm of (10.0, z_fl1) (the end of the flange-top tie when the r-10 OD is released);
'flange' = the whole flange (r >= 7.0, z_fl0 - 0.01 <= z <= z_fl1 + 0.01).  The released-interface gap change of the TC-02 / TC-03 r-10
nodes (radial normal) is reported per state (negative = closing; the CAD gap is 0.10 mm).
Usage: SAX_CAD=v352 tc03_corner.py --runs <run dir> [...] --out <json>"""
import sys, os, json, math, argparse, hashlib
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--runs", nargs="+", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--cases", default="LC1,LC2,BN,TB70,TBS,TS2,LC6")
a = ap.parse_args()
os.environ.setdefault("SAX_CAD", "v352")
TREE = Path("/home/claude/work/mechanical/v352/engine") if os.environ["SAX_CAD"] in ("v352", "v352r4") else Path("/home/claude/work/mechanical/v351/engine")
sys.path.insert(0, str(TREE / "04-fea/structural"))
sys.path.insert(0, str(TREE / "04-fea/src"))
import sax
from scipy.spatial import cKDTree

faces, info = sax.geometry()
z_fl1 = info["z_ins_top"] - 10.0
z_fl0 = z_fl1 - 2.0
CB = {c[0]: c for c in sax.combos(info)}
cases = [c for c in a.cases.split(",") if c in CB]
out = {"id": "tc03_corner", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "cad": os.environ["SAX_CAD"],
       "z_fl0_sax_mm": round(z_fl0, 4), "z_fl1_sax_mm": round(z_fl1, 4), "fea3d_point_sax_mm": [9.8, round(z_fl0, 4)],
       "evidence": "SIM (S-AX linear elastic axisymmetric FE) + CALC (this post-processing); allowables engmat (GlidCop AL-15 hot retention ASSUMED)",
       "runs": {}}
for rd in a.runs:
    rd = Path(rd)
    d, meta_m = sax._load_mesh_file(rd / "mesh.npz")
    X = d["X"]
    node_part, node_mat = sax.node_maps(d)
    sp = sax.singular_points(d, info)
    dsp = cKDTree(sp).query(X)[0] if len(sp) else np.full(len(X), np.inf)
    reg = dsp > 1.0
    n3 = np.nonzero(node_part == "ENG-TC-03")[0]
    mat3 = node_mat[n3[0]]
    P3 = X[n3]
    i_pt = n3[int(np.argmin(np.hypot(P3[:, 0] - 9.8, P3[:, 1] - z_fl0)))]
    regions = {"fea3d_point": np.array([i_pt]),
               "corner_r0.5": n3[np.hypot(P3[:, 0] - 10.0, P3[:, 1] - z_fl0) <= 0.5],
               "flange_top_corner_r0.5": n3[np.hypot(P3[:, 0] - 10.0, P3[:, 1] - z_fl1) <= 0.5],
               "flange": n3[(P3[:, 0] >= 7.0) & (P3[:, 1] >= z_fl0 - 0.01) & (P3[:, 1] <= z_fl1 + 0.01)]}
    # TC-02 / TC-03 interface copies on the flange OD (r >= 9.95, z < z_fl1 - 0.01)
    r10 = [(int(ia), int(ib), str(rule)) for (n, pa, pb, ia, ib, rule) in d["pairs"]
           if {str(pa), str(pb)} == {"ENG-TC-02", "ENG-TC-03"} and X[int(ia), 0] >= 9.95 and X[int(ia), 1] < z_fl1 - 0.01]
    states = sorted([p.name for p in rd.iterdir() if (p / "res.npz").exists() or (p / "res_sub.npz").exists()])
    burn = [s for s in states if s.startswith("B1_") and float(s[3:]) <= 21.66]
    soak = [s for s in states if s.startswith("B1_") and float(s[3:]) > 21.7]
    st_of = {"LC1": burn, "LC2": burn, "BN": burn, "TB70": ["TB"], "TBS": ["TB"], "TS2": soak, "LC6": soak[:2]}
    rec = {"run": rd.name, "mesh_sha256_16": sax.sha16(rd / "mesh.npz"), "ties_r10": sorted({r for _, _, r in r10}), "n_r10_pairs": len(r10),
           "fea3d_point_node_sax_mm": [round(float(X[i_pt, 0]), 3), round(float(X[i_pt, 1]), 3)], "fea3d_point_regular": bool(reg[i_pt]),
           "region_nodes": {k: int(len(v)) for k, v in regions.items()}, "region_regular_nodes": {k: int(reg[v].sum()) for k, v in regions.items()},
           "states": states, "cases": {}}
    cache = {}
    for cid in cases:
        _, title, _, co, sfy, sfu, _ = CB[cid]
        rows = []
        for st in st_of.get(cid, []):
            if st not in states:
                continue
            if st not in cache:
                cache[st] = {k: v for k, v in sax.load_res_any(1.0, st).items() if k not in ("meta", "nodes")} if rd == sax.run_dir(1.0) else None
                assert cache[st] is not None, f"run dir {rd} is not the run dir of the SAX_* environment ({sax.run_dir(1.0)})"
            r_ = cache[st]
            Sm = sum(c * r_[f"S_{k}"] for k, c in co.items()) if co else np.zeros_like(r_["S1"])
            Um = sum(c * r_[f"U_{k}"] for k, c in co.items()) if co else np.zeros_like(r_["U1"])
            S, U, T = r_["S1"] + Sm, r_["U1"] + Um, r_["T"]
            v, vmech, vth = sax.vm(S), sax.vm(Sm), sax.vm(r_["S1"])
            row = {"state": st}
            for nm, nodes in regions.items():
                if len(nodes) == 0:
                    continue
                fy, fu = sax.allowables(mat3, T[nodes])
                ms = fy / (sfy * np.maximum(v[nodes], 1e-9)) - 1.0
                msu = fu / (sfu * np.maximum(v[nodes], 1e-9)) - 1.0 if sfu else None
                msp = fy / (sfy * np.maximum(vmech[nodes], 1e-9)) - 1.0
                k = int(np.argmin(ms))
                kp = int(np.argmin(msp))
                n = nodes[k]
                mspq = 2.0 * fy / np.maximum(v[nodes], 1e-9) - 1.0
                row[nm] = {"MS": round(float(ms[k]), 4), "MS_ult": (round(float(np.min(msu)), 4) if msu is not None else None),
                           "MS_primary": round(float(msp[kp]), 4), "vm_MPa": round(float(v[n]), 2), "vm_mech_MPa": round(float(vmech[n]), 2),
                           "vm_thermal_MPa": round(float(vth[n]), 2), "vm_mech_max_MPa": round(float(vmech[nodes].max()), 2),
                           "T_C": round(float(T[n] - 273.15), 1), "Fty_MPa": round(float(fy[k]), 1),
                           "Ftu_MPa": (round(float(fu[k]), 1) if fu is not None else None), "at_r_z_sax_mm": [round(float(X[n, 0]), 3), round(float(X[n, 1]), 3)],
                           "regular": bool(reg[n]), "dist_singular_mm": round(float(dsp[n]), 3),
                           "MS_PQ_nodal": round(float(mspq[k]), 4), "MS_PQ_nodal_min": round(float(np.min(mspq)), 4),
                           "thermal_share_vm": round(float(vth[n] / max(float(v[n]), 1e-9)), 3)}
            # spanner holes (CAD: 2 x dia 2.0 at r 8.8, 0 / 180 deg, from the flange front face z_fl0 to z_fl0 + 1.5; not in the 214 deg
            # S-AX section): S-AX stress components at the hole radii on the front face and at mid-depth, and the Kirsch hole-edge
            # estimate sigma_peak = 3 s_tt - s_rr (circular hole in a plane field; CALC, the hoop direction is tangential to the ring)
            hole = {}
            for zlab, zq in (("front_face", z_fl0), ("depth_0.75", z_fl0 + 0.75)):
                for rq in (7.8, 8.8, 9.8):
                    q = n3[int(np.argmin(np.hypot(P3[:, 0] - rq, P3[:, 1] - zq)))]
                    st_, sth_ = S[q], r_["S1"][q]
                    hole[f"r{rq:g}_{zlab}"] = {"node_sax_mm": [round(float(X[q, 0]), 3), round(float(X[q, 1]), 3)], "T_C": round(float(T[q] - 273.15), 1),
                                               "S_rr_zz_tt_rz_MPa": [round(float(x), 2) for x in st_[:4]],
                                               "S_thermal_rr_zz_tt_rz_MPa": [round(float(x), 2) for x in sth_[:4]]}
            for zlab in ("front_face", "depth_0.75"):
                c_ = hole[f"r8.8_{zlab}"]["S_rr_zz_tt_rz_MPa"]
                hole[f"kirsch_peak_at_r8.8_field_{zlab}_MPa"] = round(3 * c_[2] - c_[0], 2)
                fy8, fu8 = sax.allowables(mat3, np.array([hole[f"r8.8_{zlab}"]["T_C"] + 273.15]))
                pk = abs(3 * c_[2] - c_[0])
                hole[f"kirsch_MS_y_{zlab}"] = round(float(fy8[0] / (sfy * max(pk, 1e-9)) - 1.0), 4)
                if sfu:
                    hole[f"kirsch_MS_u_{zlab}"] = round(float(fu8[0] / (sfu * max(pk, 1e-9)) - 1.0), 4)
            row["spanner_hole"] = hole
            if r10:
                # radial normal: TC-03 copy is the inner side; gap change = u_r(TC-02) - u_r(TC-03)
                g = []
                for ia, ib, rule in r10:
                    i3, i2 = (ia, ib) if node_part[ia] == "ENG-TC-03" else (ib, ia)
                    g.append(float(U[i2, 0] - U[i3, 0]))
                row["r10_gap_change_mm"] = {"min": round(min(g), 5), "max": round(max(g), 5)}
                dz_ = [float(U[(ib if node_part[ib] == "ENG-TC-03" else ia), 1] - U[(ia if node_part[ib] == "ENG-TC-03" else ib), 1]) for ia, ib, _ in r10]
                row["r10_slip_z_TC03_minus_TC02_mm"] = {"min": round(min(dz_), 5), "max": round(max(dz_), 5)}
            rows.append(row)
        if not rows:
            continue
        worst = {nm: min((r for r in rows if nm in r), key=lambda r: r[nm]["MS"]) for nm in regions if any(nm in r for r in rows)}
        rec["cases"][cid] = {"title": title, "SF_y": sfy, "SF_u": sfu, "coefficients": co, "rows": rows,
                             "worst_state": {nm: {"state": w["state"], **w[nm]} for nm, w in worst.items()}}
    out["runs"][rd.name] = rec
    print("==", rd.name, "ties r10", rec["ties_r10"], "fea3d node", rec["fea3d_point_node_sax_mm"], "regular", rec["fea3d_point_regular"], flush=True)
    for cid, c in rec["cases"].items():
        for nm in ("fea3d_point", "corner_r0.5", "flange_top_corner_r0.5", "flange"):
            w = c["worst_state"].get(nm)
            if w:
                print(f"  {cid:5s} {nm:22s} {w['state']:9s} MS {w['MS']:8.3f} MSu {w['MS_ult']} MSp {w['MS_primary']:8.3f} vm {w['vm_MPa']:7.1f} "
                      f"mech {w['vm_mech_MPa']:6.1f} th {w['vm_thermal_MPa']:6.1f} T {w['T_C']:6.1f} at {w['at_r_z_sax_mm']} reg {w['regular']}")
        for r_ in c["rows"]:
            h_ = r_.get("spanner_hole")
            if h_ and cid in ("LC1", "TB70"):
                print(f"    {cid} {r_['state']:9s} hole r8.8 face S(rr,zz,tt,rz) {h_['r8.8_front_face']['S_rr_zz_tt_rz_MPa']} T {h_['r8.8_front_face']['T_C']} "
                      f"Kirsch {h_['kirsch_peak_at_r8.8_field_front_face_MPa']} MSy {h_['kirsch_MS_y_front_face']} | r9.8 {h_['r9.8_front_face']['S_rr_zz_tt_rz_MPa']}"
                      + (f" r10 gap {r_['r10_gap_change_mm']} slip {r_['r10_slip_z_TC03_minus_TC02_mm']}" if 'r10_gap_change_mm' in r_ else ""))
s = json.dumps(out, indent=1, default=float)
Path(a.out).write_text(s)
print("wrote", a.out, "sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])
