"""Item 5b re-posts on the gap-conductance variant (fea3d 2026-10-20; brief item 5b, CHANGELOG 234 (7) = REV-MECH-2 RM2-13 correction 5).

Re-map and re-post, from the solved v3.5.2 global runs (no new solve):
  * TC-03 as a whole part, with the sub-regions the review names: the flange front corner (the v3.5.1 n44861 / v3.5.2 n46040 point
    r 9.8, z 105.513 and the nodes within 0.5 mm of the flange front outer corner r 10.0), the flange (r >= 7.0, z 105.51-107.52), the
    shoulder (TC-03 nodes within 1.0 mm of the TC03_TC02_shoulder tie faces) and the thread root (within 1.0 mm of the TC03_TC02_thread
    tie faces);
  * the TC-02 seat (r <= 12, z 105-118: TB1 seat bore, shoulder seat face, r-10.1 OD-gap bore) and the TC-02 forward face (TC-02 boundary
    nodes on the plane z = z_ff, 12 < r < 28.6, z_ff = the lowest TC-02 z in that band; the face the S-AX TC-02 maximum sits on);
  * NZ-01 as a whole part and at the v3.5.1 n72033 location (the NZ-01 node nearest the v3.5.1 n72033 coordinates, which the FE keeps:
    NZ-01 / NZ-02 meshes are the v3.5.1 ones);
at the four burn states B1_21.65 / B1_19 / B1_2 / B1_1 (B1_21.65 = the S-AX state nearest the S-AX TC-02 maximum at 21.5 s; S-AX
writes no 21.5 s state), cases LC1 and LC2 (post_f1 combos: 4 lateral sub-cases each, node-wise envelope), both node sets (all-node and
regular, brep60 rule), with: MS y / u on the total stress at SF 1.5 / 2.0, primary-only MS y / u (mechanical stress only), nodal P+Q
2 Fty(T) / vm - 1, thermal share vm_TH / vm at the governing node, node class / distance, T; region T max per state; and the plug-to-bore
dT at the TC-01 / TC-02 fit (TC-02 plug OD nodes r >= 28.55 vs the TC-01 bore nodes r <= 28.68 nearest in (z, theta); closure needs
dT = gap / (r alpha): 37.0 K at 0.025 (CAD), 59.3 K at 0.040, 115.6 K at 0.078 mm, alpha 23.6e-6 /K (REV-MECH-2 RM2-13 (c), DERIVED)).
Evidence: SIM (3-D linear elastic FE, mapped S-AX thermal fields: lc1v352g GVLO, lc1v352h GVHI; lc1v352 = the v3.5.1 merged map
L1_thv351_TB1GC_cad351 on the v3.5.2 mesh, information only) + DERIVED (this post-processing).
[13:42Z (date -u) correction: this line said 'lc1v352 merged NF2b = perfect-contact bound'; lc1v352 has no sax= option and used the v3.5.1
merged map (PROGRESS 12:10Z; margin_matrix_v352 label 'LC1 merged v351 map (info)').  Docstring only; no code changed.]  Allowables engmat (GlidCop AL-15 above 20 C CONDITIONAL / ASSUMED hot retention; 6061-T6
LITERATURE 10,000 h basis; NZ-01 graphite brittle St / Sc).
fea3d 11:26Z: + the S-AX TC-02 maximum point region (r 24.95, z 103.513, 0.5 mm), the fit dT per plug land (A / B / C, 3-D = S-AX frame) with the
variant's own cold-gap closure, and the closure ruling (lead 10:36Z: CLOSED on the Lame bound + land-A check; js5c dropped).
usage: FEA3D_CAD=v352 repost_5b_v352.py RUN [RUN ...] -> results/v352/repost_5b_<RUN>.json"""
from __future__ import annotations
import sys, json, math, hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF  # noqa: E402
import engmat  # noqa: E402

RES = Path("/home/claude/work/fea3d/results")
BURN = ["B1_21.65", "B1_19", "B1_2", "B1_1"]
ALPHA = 23.6e-6
R_FIT = 28.6
GAPS = {"0.025 CAD": 0.025, "0.040 drawing min": 0.040, "0.078 drawing max": 0.078}
P_CORNER = (9.8, 105.5134)       # FEA3D / S-AX TC-03 corner point (S-AX z_fl0)
P_CORNER_OD = (10.0, 105.5134)   # flange front outer corner
P_SAX_MAX = (24.95, 103.5134)    # S-AX TC-02 maximum (NF2b B1_21.65): the forward-face hot corner r 24.95, z_ff 103.513 (fea3d 10:12Z frame fix)
# 2026-10-20 ~11:26Z: the three plug lands in the 3-D (= S-AX) frame (gapvar J1 z_overlap minus 6.544 mm, fit_dT_sax.py v2) and the
# per-variant closure (cold radial gap of the variant: GVLO = drawing max 0.078, GVHI = drawing min 0.040; NF2b merged = perfect contact)
LANDS = {"A": (103.5135, 106.5135), "B": (111.3635, 114.3635), "C": (119.2135, 136.5135)}
VARIANT_COLD_GAP = {"GVLO": 0.078, "GVHI": 0.040}
CLOSURE_RULING = ("plug-to-bore closure CLOSED (lead 10:36Z): GVHI on the Lame bound + the land-A cell check (results/v352/"
                  "landA_closure_gvhi_v352.json 7754f21e2910220a, all cells positive; GVHI own interference <= 0.0086 mm at B1_8..B1_19), "
                  "GVLO stays open at its own 0.078 mm cold gap (0.018 mm left at the closest instant), NF2b merged = the perfect-contact bound; "
                  "the fit dT rows below are context (fit_dT_sax_v352.json 93d87757edbcdcaf = the S-AX record)")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def n72033_xyz():
    """xyz of the v3.5.1 NZ-01 all-node governing node n72033 (lc1v351_c71 post, REV-MECH-2 LC1 table)."""
    d = json.loads((RES / "f1_post_lc1v351_c71.json").read_text())
    for s, v in d["states"].items():
        for c, cv in v.get("cases", {}).items():
            for m in cv.get("margins", []):
                if m.get("node") == 72033:
                    return m["xyz_mm"], s, c, m.get("MS")
    return None, None, None, None


def body_nodes(M, nm):
    b = M.bodies[nm]
    return b, b.noff + np.arange(len(b.X0))


def tie_zone(M, label, ex=1.0):
    """global node ids of the dependent body within ex mm of the dependent faces of tie 'label' (and the dep body name)."""
    for lab, dep, ind, md, mi, tol in getattr(M, "tie_masks", []):
        if lab == label:
            b = M.bodies[dep]
            loc = b.nodes_of(md)
            P = b.X0[loc]
            d, _ = cKDTree(P).query(b.X0, k=1)
            return dep, b.noff + np.nonzero(d <= ex)[0], b.noff + loc
    return None, np.array([], np.int64), np.array([], np.int64)


def regions(M, X):
    out = {}
    b3, n3 = body_nodes(M, "TC-03")
    r3, z3 = np.hypot(X[n3, 0], X[n3, 1]), X[n3, 2]
    out["TC-03 whole"] = n3
    i_pt = int(np.argmin(np.hypot(r3 - P_CORNER[0], z3 - P_CORNER[1])))
    out["TC-03 corner point (r 9.8 z 105.513)"] = n3[[i_pt]]
    out["TC-03 corner r0.5 (r 10.0 z 105.513)"] = n3[np.hypot(r3 - P_CORNER_OD[0], z3 - P_CORNER_OD[1]) <= 0.5]
    out["TC-03 flange (r >= 7.0, z 105.51-107.52)"] = n3[(r3 >= 7.0) & (z3 >= 105.50) & (z3 <= 107.52)]
    dep, zs, _ = tie_zone(M, "TC03_TC02_shoulder")
    if dep == "TC-03":
        out["TC-03 shoulder (<= 1 mm of the TC03_TC02_shoulder tie)"] = zs
    dep, zt, _ = tie_zone(M, "TC03_TC02_thread")
    if dep == "TC-03":
        out["TC-03 thread root (<= 1 mm of the TC03_TC02_thread tie)"] = zt
    b2, n2 = body_nodes(M, "TC-02")
    r2, z2 = np.hypot(X[n2, 0], X[n2, 1]), X[n2, 2]
    out["TC-02 whole"] = n2
    out["TC-02 seat (r <= 12, z 105-118)"] = n2[(r2 <= 12.0) & (z2 >= 105.0) & (z2 <= 118.0)]
    out["TC-02 S-AX max point r0.5 (r 24.95 z 103.513)"] = n2[np.hypot(r2 - P_SAX_MAX[0], z2 - P_SAX_MAX[1]) <= 0.5]
    band = (r2 > 12.0) & (r2 < 28.6)
    z_ff = float(z2[band].min())
    bnd = np.zeros(len(n2), bool)
    bnd[np.unique(b2.bf_n.ravel())] = True
    out[f"TC-02 forward face (z {z_ff:.3f}, 12 < r < 28.6)"] = n2[band & bnd & (np.abs(z2 - z_ff) <= 0.05)]
    b1, n1 = body_nodes(M, "NZ-01")
    out["NZ-01 whole"] = n1
    xyz, st, cs, ms = n72033_xyz()
    meta = {"z_forward_face_mm": round(z_ff, 4), "n72033_v351_xyz_mm": xyz, "n72033_v351_governing": [st, cs, ms]}
    if xyz is not None:
        d = np.linalg.norm(X[n1] - np.asarray(xyz), axis=1)
        j = int(np.argmin(d))
        out["NZ-01 at v3.5.1 n72033"] = n1[[j]]
        meta["n72033_v352_node"] = int(n1[j])
        meta["n72033_v352_offset_mm"] = round(float(d[j]), 4)
        out["NZ-01 within 1 mm of v3.5.1 n72033"] = n1[d <= 1.0]
    return out, meta


def fit_dT(M, X, T, variant=None):
    """plug-to-bore dT at the TC-01 / TC-02 fit: TC-02 plug OD nodes r >= 28.55 vs the nearest TC-01 bore node (r <= 28.70) in (z, r theta)."""
    b2, n2 = body_nodes(M, "TC-02")
    b1, n1 = body_nodes(M, "TC-01")
    r2, r1 = np.hypot(X[n2, 0], X[n2, 1]), np.hypot(X[n1, 0], X[n1, 1])
    bnd2 = np.zeros(len(n2), bool)
    bnd2[np.unique(b2.bf_n.ravel())] = True
    bnd1 = np.zeros(len(n1), bool)
    bnd1[np.unique(b1.bf_n.ravel())] = True
    p = n2[bnd2 & (r2 >= 28.55) & (r2 <= 28.65)]
    q = n1[bnd1 & (r1 >= 28.58) & (r1 <= 28.70)]
    if len(p) == 0 or len(q) == 0:
        return {"n_plug": int(len(p)), "n_bore": int(len(q))}
    zq = X[q, 2]
    zp = X[p, 2]
    zlo, zhi = max(zp.min(), zq.min()), min(zp.max(), zq.max())
    p = p[(X[p, 2] >= zlo) & (X[p, 2] <= zhi)]
    tq = np.arctan2(X[q, 1], X[q, 0]) * R_FIT
    tp = np.arctan2(X[p, 1], X[p, 0]) * R_FIT
    tr = cKDTree(np.c_[X[q, 2], tq])
    d, j = tr.query(np.c_[X[p, 2], tp], k=1)
    ok = d <= 1.0
    dT = T[p[ok]] - T[q[j[ok]]]
    k = int(np.argmax(dT))
    o = {"n_pairs": int(ok.sum()), "z_range_mm": [round(float(zlo), 3), round(float(zhi), 3)],
         "dT_plug_minus_bore_K": {"max": round(float(dT.max()), 2), "min": round(float(dT.min()), 2), "mean": round(float(dT.mean()), 2)},
         "at_max": {"plug_node": int(p[ok][k]), "bore_node": int(q[j[ok]][k]), "z_mm": round(float(X[p[ok][k], 2]), 3),
                    "T_plug_C": round(float(T[p[ok][k]] - 273.15), 1), "T_bore_C": round(float(T[q[j[ok]][k]] - 273.15), 1)},
         "T_plug_C_range": [round(float(T[p].min() - 273.15), 1), round(float(T[p].max() - 273.15), 1)],
         "T_bore_C_range": [round(float(T[q].min() - 273.15), 1), round(float(T[q].max() - 273.15), 1)],
         "closure_dT_K": {k_: round(g / (R_FIT * ALPHA), 1) for k_, g in GAPS.items()}}
    o["closes"] = {k_: bool(dT.max() >= g / (R_FIT * ALPHA)) for k_, g in GAPS.items()}
    o["needs_fit_contact (dT >= 37-59 K)"] = bool(dT.max() >= 0.025 / (R_FIT * ALPHA))
    # 11:26Z: per land (3-D = S-AX frame) and the variant's own cold gap
    zpp = X[p[ok], 2]
    per = {}
    for nm, (a, b) in LANDS.items():
        kk = (zpp >= a - 0.05) & (zpp <= b + 0.05)
        if kk.any():
            jj = int(np.argmax(np.where(kk, dT, -1e9)))
            per[nm] = {"z_mm": [a, b], "n_pairs": int(kk.sum()), "dT_max_K": round(float(dT[jj]), 2), "z_at_max_mm": round(float(zpp[jj]), 3),
                       "dT_mean_K": round(float(dT[kk].mean()), 2)}
        else:
            per[nm] = {"z_mm": [a, b], "n_pairs": 0}
    o["per_land"] = per
    o["n_pairs_outside_lands"] = int(sum(1 for z_ in zpp if not any(a - 0.05 <= z_ <= b + 0.05 for a, b in LANDS.values())))
    g = VARIANT_COLD_GAP.get(variant or "")
    o["variant"] = variant or "NF2b merged (perfect contact)"
    if g:
        o["variant_cold_gap_mm"] = g
        o["variant_closure_dT_K"] = round(g / (R_FIT * ALPHA), 1)
        o["closes_variant_cold_gap_by_max"] = bool(dT.max() >= g / (R_FIT * ALPHA))
        o["variant_gap_left_mm_at_max"] = round(g - R_FIT * ALPHA * float(dT.max()), 4)
    else:
        o["variant_closure_note"] = "merged NF2b field = perfect thermal contact: no gap to close (bound)"
    o["closure_ruling"] = CLOSURE_RULING
    return o


def eval_region(M, X, T, reg, sing, F, sub, sfy, sfu, nodes, part):
    b = M.bodies[part]
    mat = b.mat
    brittle = mat in PF.BRITTLE
    Tn = T[nodes]
    a1, a2 = PF.allowables(mat, Tn)
    best = None
    env = {k: np.full(len(nodes), np.inf) for k in ("ms", "msu", "msp", "mspu", "mspq")}
    arg = np.zeros(len(nodes), np.int16)
    vms, vmm = {}, {}
    STH = F["S_TH"].astype(np.float64)[nodes] if "S_TH" in F else None
    for si, co in enumerate(sub):
        S, Sm = PF.combine(F, "S", co)
        Sb, Smb = S[nodes], Sm[nodes]
        v, vmech = PF.vm(Sb), PF.vm(Smb)
        vms[si], vmm[si] = v, vmech
        if brittle:
            s1, s3 = PF.principal(Sb)
            sf = sfu if sfu else 1.5
            mt = np.where(s1 > 0, a1 / (sf * np.maximum(s1, 1e-9)) - 1.0, np.inf) if a1 is not None else np.full(len(nodes), np.inf)
            mc = np.where(s3 < 0, a2 / (sf * np.maximum(-s3, 1e-9)) - 1.0, np.inf) if a2 is not None else np.full(len(nodes), np.inf)
            ms = np.minimum(mt, mc)
            msu = msp = mspu = mspq = np.full(len(nodes), np.inf)
        else:
            ms = a1 / (sfy * np.maximum(v, 1e-9)) - 1.0
            msu = a2 / (sfu * np.maximum(v, 1e-9)) - 1.0
            msp = a1 / (sfy * np.maximum(vmech, 1e-9)) - 1.0
            mspu = a2 / (sfu * np.maximum(vmech, 1e-9)) - 1.0
            mspq = 2.0 * a1 / np.maximum(v, 1e-9) - 1.0
        upd = ms < env["ms"]
        arg[upd] = si
        for k, a in (("ms", ms), ("msu", msu), ("msp", msp), ("mspu", mspu), ("mspq", mspq)):
            env[k] = np.minimum(env[k], a)
    out = {"material": mat, "brittle": brittle, "n_nodes": int(len(nodes)),
           "T_max_C": round(float(Tn.max() - 273.15), 1), "T_min_C": round(float(Tn.min() - 273.15), 1),
           "T_max_node": int(nodes[int(np.argmax(Tn))]),
           "T_max_r_z_mm": [round(float(math.hypot(*X[nodes[int(np.argmax(Tn))], :2])), 3), round(float(X[nodes[int(np.argmax(Tn))], 2]), 3)]}
    for tag, msk in (("all", np.ones(len(nodes), bool)), ("regular", reg[nodes])):
        if not msk.any():
            out[tag] = None
            continue
        i = int(np.argmin(np.where(msk, env["ms"], np.inf)))
        n = int(nodes[i])
        si = int(arg[i])
        v = float(vms[si][i])
        vth = float(PF.vm(STH[i][None])[0]) if STH is not None else 0.0
        x = X[n]
        nc = PF.node_class(X, sing, n, 1.0)
        rec = {"node": n, "r_theta_z": [round(math.hypot(x[0], x[1]), 3), round(math.degrees(math.atan2(x[1], x[0])), 1), round(float(x[2]), 3)],
               "T_C": round(float(Tn[i] - 273.15), 1), "MS_y": round(float(env["ms"][i]), 3),
               "MS_u": (round(float(env["msu"][i]), 3) if np.isfinite(env["msu"][i]) else None),
               "vm_MPa": round(v, 1), "vm_mech_MPa": round(float(vmm[si][i]), 1), "vm_thermal_only_MPa": round(vth, 1),
               "thermal_share_vm": round(vth / max(v, 1e-9), 3), "subcase": sub[si],
               "Fty_MPa": (round(float(a1[i]), 1) if a1 is not None else None), "Ftu_MPa": (round(float(a2[i]), 1) if a2 is not None else None),
               "node_class": nc["class"], "class_detail": nc["class_detail"], "d_class_mm": nc["d_class_mm"]}
        if not brittle:
            rec["MS_primary_y_at_node"] = round(float(env["msp"][i]), 3)
            rec["MS_primary_u_at_node"] = round(float(env["mspu"][i]), 3)
            rec["MS_PQ_2Fty_at_node"] = round(float(env["mspq"][i]), 3)
            jp = int(np.argmin(np.where(msk, env["msp"], np.inf)))
            rec["MS_primary_y_set_min"] = round(float(env["msp"][jp]), 3)
            rec["MS_primary_y_set_min_node"] = int(nodes[jp])
            rec["MS_primary_u_set_min"] = round(float(np.min(np.where(msk, env["mspu"], np.inf))), 3)
            rec["MS_PQ_2Fty_set_min"] = round(float(np.min(np.where(msk, env["mspq"], np.inf))), 3)
        out[tag] = rec
    return out


def main(runs):
    for run in runs:
        M, meta = PF.load_model(run)
        names, body, T0, X = PF.node_arrays(M, run, BURN[0])
        reg, rep, sing = PF.singular_sets(M, X, ex_r=1.0)
        R, rmeta = regions(M, X)
        res = {"id": f"repost_5b_{run}", "date": "2026-10-20", "owner": "fea3d", "run": run, "sax": meta["variant"].get("sax"),
               "tb1": meta["variant"].get("tb1"), "tiex": meta["variant"].get("tiex"), "re_rule": rep.get("re_rule"),
               "model_json_sha16": sha16(Path(PF.RUNS) / run / "model.json"), "regions_meta": rmeta,
               "regions_n_nodes": {k: int(len(v)) for k, v in R.items()},
               "ties_TC02_TC03": [t for t in meta.get("ties", []) if {t.get("dep"), t.get("ind")} == {"TC-02", "TC-03"}],
               "ties_TC01_TC02": [t for t in meta.get("ties", []) if {t.get("dep"), t.get("ind")} == {"TC-01", "TC-02"}],
               "evidence": "SIM (3-D linear elastic FE on the mapped S-AX field) + DERIVED (post-processing)", "states": {}}
        for st in BURN:
            if not (Path(PF.RUNS) / run / st / "fields.npz").exists():
                res["states"][st] = {"missing": True}
                continue
            _, _, T, _ = PF.node_arrays(M, run, st)
            F = PF.load_fields(run, st)
            th = json.loads((Path(PF.RUNS) / run / st / "thermal.json").read_text())
            so = {"thermal_source": th.get("_source"), "fit_dT": fit_dT(M, X, T, meta["variant"].get("sax")), "cases": {}}
            for cid, title, sub, sfy, sfu, crit, parts in PF.combos(st, meta.get("steps")):
                if cid not in ("LC1", "LC2"):
                    continue
                co = {}
                for lab, nodes in R.items():
                    part = lab.split(" ")[0]
                    if len(nodes) == 0:
                        co[lab] = None
                        continue
                    co[lab] = eval_region(M, X, T, reg, sing, F, sub, sfy, sfu, nodes, part)
                so["cases"][cid] = {"title": title, "SF_y": sfy, "SF_u": sfu, "regions": co}
            res["states"][st] = so
            print(run, st, "fit dT max", so["fit_dT"].get("dT_plug_minus_bore_K"), flush=True)
            for cid, c in so["cases"].items():
                for lab, r in c["regions"].items():
                    if r is None:
                        continue
                    a, g = r.get("all"), r.get("regular")
                    print(f"  {cid} {lab:58s} Tmax {r['T_max_C']:7.1f} | all {a['MS_y']:+.3f}/{a['MS_u'] if a['MS_u'] is not None else float('nan'):+.3f} n{a['node']} {a['node_class']} {a['d_class_mm']} prim {a.get('MS_primary_y_at_node')} PQ {a.get('MS_PQ_2Fty_at_node')} th {a['thermal_share_vm']}"
                          + (f" | reg {g['MS_y']:+.3f}/{g['MS_u'] if g['MS_u'] is not None else float('nan'):+.3f} n{g['node']} prim-min {g.get('MS_primary_y_set_min')} PQ-min {g.get('MS_PQ_2Fty_set_min')}" if g else " | reg none"), flush=True)
        out = RES / "v352" / f"repost_5b_{run}.json"
        out.write_text(json.dumps(res, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
        print("wrote", out, sha16(out))


if __name__ == "__main__":
    main(sys.argv[1:])
