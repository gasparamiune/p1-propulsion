#!/usr/bin/env python3
"""GM-01 FA-1 cells: DERIVED rod-path bound for the OP-moment residue (lead 22:54:03Z (2), refined 23:12:52Z (2)).

The v3.5.2 L1 OP unit step carries a non-physical moment about the pivot; the rods are the only moment path, so it shows as a
rod-force pair (statics of the deck load: ROD_1 +13.531, ROD_2 -0.724 N/MPa; icd_momentfree_v352.json global_L1).  The physical OP
moment is zero.  For each FA-1 case (OP coefficient = bar abs / 10, as post_f1) this script states the rod forces with and without
the residue, and applies the residue rod force through GM-01's stress per unit rod force from the EA unit steps:
  * the v3.5.2 L1 model (fa1v352n) has no EA step; the v3.5.1 L1 neutral run pose_neutral_c71 has S_EAX / S_EAY and its own EA unit
    rods (rodstep_cones_v352.json, v351_c71).  b solves [s_EAX s_EAY] b = t_residue; the residue field in GM-01 is
    c_OP (b_X S_EAX + b_Y S_EAY), transferred to each v3.5.2 GM-01 node from the nearest c71 GM-01 node [ASSUMED: same rev-1 lever,
    Saint-Venant at GM-01 between a pressure-borne and an inertia-borne pivot moment; the governing node n88188 coincides with
    c71 n55792 at 0.0 mm].
  * moment-free field = as found - residue field (tensor); also the triangle bound vM + vM(residue field) (any sign).
Reads only; writes results/v352/gm01_rodpath_bound_v352.json and results/v352/tables/gm01_rodpath_bound_v352.md.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import post_f1 as PF   # noqa: E402
import post_lc3 as PL  # noqa: E402

ROOT = Path("/home/claude/work/fea3d")
RUNS, RES = ROOT / "runs", ROOT / "results"
RUN_V, ST_V, RUN_C, ST_C = "fa1v352n", "A1_22.2", "pose_neutral_c71", "B1_21.65"
OUTJ, OUTM = RES / "v352" / "gm01_rodpath_bound_v352.json", RES / "v352" / "tables" / "gm01_rodpath_bound_v352.md"
RODS = ("ROD_1", "ROD_2")
NODE = 88188          # post label = 0-based field index (post_f1 'node': int(n)); deck node id = label + 1
POSTED = {"FA1Q": (0.767, 1.030), "FA1D": (0.373, 0.578), "FA1U": (0.130, 0.299), "FA1S": (0.100, 0.264), "FA1T": (0.777, 1.042)}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def vm(s):
    s = np.atleast_2d(np.asarray(s, float))
    sx, sy, sz, txy, tyz, txz = s.T
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (txy ** 2 + tyz ** 2 + txz ** 2))


def deck_nodes(path, lo, hi):
    X = {}
    with gzip.open(path, "rt") as f:
        on = False
        for line in f:
            if line.startswith("*"):
                u = line.upper()
                on = u.startswith("*NODE") and not u.startswith(("*NODE PRINT", "*NODE FILE", "*NODE OUTPUT"))
                continue
            if on:
                p = line.split(",")
                n = int(p[0])
                if lo <= n <= hi:
                    X[n] = [float(p[1]), float(p[2]), float(p[3])]
    return X


def main():
    mom = json.loads((RES / "v352" / "icd_momentfree_v352.json").read_text())
    t_res = np.asarray(mom["global_L1"]["OP_rods_statics_N_per_MPa"], float)
    rs = json.loads((RES / "v352" / "rodstep_cones_v352.json").read_text())
    u71 = rs["poses"]["neutral"]["v351_c71"]["unit_rod_N"]
    S71 = np.array([[u71[r]["EAX"], u71[r]["EAY"]] for r in RODS])
    b = np.linalg.solve(S71, t_res)                       # rad/s2 per MPa of OP

    # v3.5.2 L1 FA-1 model: GM-01 nodes, fields, temperatures, rods
    M, meta = PF.load_model(RUN_V)
    bod = meta["bodies"]["GM-01"] if "bodies" in meta else json.loads((RUNS / RUN_V / "model.json").read_text())["bodies"]["GM-01"]
    nv = np.arange(bod["noff"] + 1, bod["noff"] + bod["n"] + 1)
    Pv = np.asarray(M["X"])[nv - 1] if isinstance(M, dict) and "X" in M else None
    z = np.load(RUNS / RUN_V / ST_V / "fields.npz")
    TK = np.load(RUNS / RUN_V / ST_V / "T.npz")["GM-01"]
    mat = bod["mat"]
    fty, ftu = PF.allowables(mat, TK)
    sf = PL.spring_forces_per_step(M, {k: z[k] for k in z.files if k.startswith("U_")}, [k[2:] for k in z.files if k.startswith("U_")])
    # c71 neutral: GM-01 nodes and the EA unit stresses
    mc = json.loads((RUNS / RUN_C / "model.json").read_text())["bodies"]["GM-01"]
    Xc = deck_nodes(RUNS / RUN_C / ST_C / "f1.inp.gz", mc["noff"] + 1, mc["noff"] + mc["n"])
    nc = np.array(sorted(Xc))
    Pc = np.array([Xc[n] for n in nc])
    if Pv is None:
        Xv = {}
        import lzma
        with lzma.open(RUNS / RUN_V / ST_V / "f1.inp.xz", "rt") as f:
            on = False
            for line in f:
                if line.startswith("*"):
                    u = line.upper()
                    on = u.startswith("*NODE") and not u.startswith(("*NODE PRINT", "*NODE FILE", "*NODE OUTPUT"))
                    continue
                if on:
                    p = line.split(",")
                    n = int(p[0])
                    if nv[0] <= n <= nv[-1]:
                        Xv[n] = [float(p[1]), float(p[2]), float(p[3])]
        Pv = np.array([Xv[n] for n in nv])
    zc = np.load(RUNS / RUN_C / ST_C / "fields.npz")
    d, j = cKDTree(Pc).query(Pv)
    mapc = nc[j] - 1
    R_unit = b[0] * zc["S_EAX"][mapc].astype(float) + b[1] * zc["S_EAY"][mapc].astype(float)   # per MPa of OP
    i0 = int(np.where(nv == NODE + 1)[0][0])

    S = {k[2:]: z[k][nv - 1].astype(float) for k in z.files if k.startswith("S_")}
    cases = {cid: {"OP": bar / 10.0, "PM": PF.P_MAN} for cid, bar in PF.FA1_BAR.items()}
    cases["FA1T"] = {"OP": PF.FA1_BAR["FA1Q"] / 10.0, "PM": PF.P_MAN, "TZ": PF.FA1_THRUST_N - PF.OP_NET_Z * PF.FA1_BAR["FA1Q"] / 10.0}
    out = {"id": "gm01_rodpath_bound_v352", "doc": __doc__, "evidence": "DERIVED (superposition on SIM unit steps; transfer ASSUMED)",
           "t_residue_N_per_MPa": t_res.tolist(), "c71_EA_unit_rods_N": S71.tolist(), "b_EA_rad_s2_per_MPa": b.tolist(),
           "node_label_convention": "nNNNN = post label = 0-based field index (post_f1); deck node id = label + 1",
           "node": NODE, "deck_node": NODE + 1, "c71_node": int(nc[j[i0]]) - 1, "c71_node_distance_mm": float(d[i0]),
           "transfer_distance_mm": {"median": float(np.median(d)), "p95": float(np.percentile(d, 95)), "max": float(d.max())},
           "material": mat, "cases": {}, "files_sha16": {}}
    for cid, co in cases.items():
        sig = S["TH"] + sum(c * (S[s] - S["TH"]) for s, c in co.items())
        rods = {r: float(sf[r]["TH"] + sum(c * (sf[r][s] - sf[r]["TH"]) for s, c in co.items())) for r in RODS}
        dres = co["OP"] * t_res
        res_field = co["OP"] * R_unit
        sig_mf = sig - res_field
        v, vmf, vres = vm(sig), vm(sig_mf), vm(res_field)
        ms = lambda a, s: a / s - 1.0                                          # noqa: E731  (SF 1.0, FA-1)
        k_af, k_mf, k_tb = int(np.argmin(ms(fty, v))), int(np.argmin(ms(fty, vmf))), int(np.argmin(ms(fty, v + vres)))
        out["cases"][cid] = {
            "coefs": co, "rods_as_found_N": rods, "rods_residue_N": dict(zip(RODS, dres.round(2).tolist())),
            "rods_moment_free_N": {r: round(rods[r] - float(dres[i]), 2) for i, r in enumerate(RODS)},
            "ROD_1_residue_sign": "+ (tension)" if dres[0] > 0 else "- (compression)",
            "at_node": {"T_C": float(TK[i0] - 273.15), "vm_as_found_MPa": float(v[i0]), "vm_moment_free_MPa": float(vmf[i0]),
                        "vm_residue_field_MPa": float(vres[i0]),
                        "MS_as_found": [round(float(ms(fty[i0], v[i0])), 4), round(float(ms(ftu[i0], v[i0])), 4)],
                        "MS_posted": list(POSTED[cid]),
                        "MS_moment_free": [round(float(ms(fty[i0], vmf[i0])), 4), round(float(ms(ftu[i0], vmf[i0])), 4)],
                        "MS_triangle_bound": [round(float(ms(fty[i0], v[i0] + vres[i0])), 4), round(float(ms(ftu[i0], v[i0] + vres[i0])), 4)]},
            "part_all_node_min": {
                "as_found": {"node": int(nv[k_af]) - 1, "MS": [round(float(ms(fty[k_af], v[k_af])), 4), round(float(ms(ftu[k_af], v[k_af])), 4)]},
                "moment_free": {"node": int(nv[k_mf]) - 1, "MS": [round(float(ms(fty[k_mf], vmf[k_mf])), 4), round(float(ms(ftu[k_mf], vmf[k_mf])), 4)],
                                "transfer_distance_mm": float(d[k_mf])},
                "triangle_bound": {"node": int(nv[k_tb]) - 1, "MS": [round(float(ms(fty[k_tb], v[k_tb] + vres[k_tb])), 4),
                                                                  round(float(ms(ftu[k_tb], v[k_tb] + vres[k_tb])), 4)],
                                   "transfer_distance_mm": float(d[k_tb])}},
            "max_vm_residue_field_MPa": {"value": float(vres.max()), "node": int(nv[int(np.argmax(vres))]) - 1,
                                         "xyz_mm": [round(float(c), 3) for c in Pv[int(np.argmax(vres))]]}}
    for p in (RES / "v352" / "icd_momentfree_v352.json", RES / "v352" / "rodstep_cones_v352.json", RUNS / RUN_V / ST_V / "fields.npz",
              RUNS / RUN_C / ST_C / "fields.npz", RUNS / RUN_C / ST_C / "f1.inp.gz", Path(__file__)):
        out["files_sha16"][str(p.relative_to(ROOT))] = sha16(p)
    OUTJ.write_text(json.dumps(out, indent=1, default=float))
    L = ["# GM-01 FA-1 cells: rod-path bound for the OP-moment residue (DERIVED; transfer ASSUMED)", "",
         f"Residue rods {t_res.round(3).tolist()} N/MPa (ROD_1, ROD_2); c71 EA unit rods {S71.round(4).tolist()} N per rad/s2; "
         f"b {np.round(b, 4).tolist()} rad/s2 per MPa.  Node n{NODE} (post label; deck node {NODE + 1}) = c71 n{int(nc[j[i0]]) - 1} ({d[i0]:.4f} mm).", "",
         "| case | OP MPa | ROD_1 as found / residue / moment-free N (residue sign) | n88188 MS posted | reproduced | moment-free | triangle bound | GM-01 all-node min, moment-free (node) |",
         "|---|---|---|---|---|---|---|---|"]
    for cid, c in out["cases"].items():
        a, pa = c["at_node"], c["part_all_node_min"]
        L.append(f"| {cid} | {c['coefs']['OP']:.3f} | {c['rods_as_found_N']['ROD_1']:+.1f} / {c['rods_residue_N']['ROD_1']:+.1f} / "
                 f"{c['rods_moment_free_N']['ROD_1']:+.1f} ({c['ROD_1_residue_sign']}) | {a['MS_posted'][0]:+.3f} / {a['MS_posted'][1]:+.3f} | "
                 f"{a['MS_as_found'][0]:+.3f} / {a['MS_as_found'][1]:+.3f} | {a['MS_moment_free'][0]:+.3f} / {a['MS_moment_free'][1]:+.3f} | "
                 f"{a['MS_triangle_bound'][0]:+.3f} / {a['MS_triangle_bound'][1]:+.3f} | {pa['moment_free']['MS'][0]:+.3f} / "
                 f"{pa['moment_free']['MS'][1]:+.3f} (n{pa['moment_free']['node']}) |")
    OUTM.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
