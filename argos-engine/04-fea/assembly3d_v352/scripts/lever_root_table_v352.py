"""Lever-root table, v3.5.2 brief item 1 (fea3d, written 2026-10-20T19:52:52Z (date -u)).

Brief item 1: "Lever roots: F2 GS servo stall at all 9 cone poses and F1 LC3 at the 8 stop poses at R3 on the changed CAD, cold and with
the hot bound node by node".  Per pose and lever (GM-01 / GM-02), all-node and regular sets (all-node rule 234 (4)):
  cold    the R3 post record: LC3 at the stops (results/f1_post_lc3_pose_<stop>_v352r3R3.json), GS at the cones
          (results/s3d_pose_<cone>_v352r3R3.json, cases GS; TD and LC6 for context), B1_21.65 node temperatures, SF 1.5 / 2.0 [SIM];
  cell    lead 12:28Z (5): where R2 -> R3 changed the lever-root peak by more than 5 % the cell quotes the p = 1 bound
          (results/v352/lever_root_bound_v352.json; DERIVED, order ASSUMED, no R4 run), else the R3 value.  R2 ran at stop045, stop315,
          alpha+ and alpha- only: at the other 13 poses the cell is the R3 value, and the record says whether the peak node is one of the
          R2-checked peak nodes (and its distance to the nearest one);
  hot     the node-wise sub-additivity bound of lc3_bound.py (same mesh): vm <= vm_LC1(n) + vmD(n), with vm_LC1 the thermo-pressure field
          (TH + OP x Pc_max + PM x 7 MPa, no LC1 inertia) of the R3 base at the node and vmD the pose's OWN increment at the node (stops:
          LC3, 64 sub-cases; cones: the GS + TD + LC6 increment envelope of the pose, so also a lower bound on the GS-only hot margin),
          computed PER POSE here from the inputs of the published envelope bound: the lever-root extracts
          results/v352/hb3_leverroot_extract_g3 / _h3.npz of the bases lc1v352hbg3 (GVLO) / lc1v352hbh3 (GVHI), their T.npz per state,
          the pose env npz; 4 burn states; allowables at the node temperature, SF 1.5 / 2.0.  The cell takes the worst base and state
          [DERIVED];
  hot p1  at the three p = 1 cells only: the hot bound with the cold p = 1 increment (R3 - R2 peak vM, MPa, from the R2 / R3 posts) added
          at every node of the lever [DERIVED, order ASSUMED];
  check   per base, state, part and set: the minimum over the poses of the per-pose hot bound equals the published envelope bound
          (results/f1_lc3_hot_bound_v352<tag>_x.json, results/f1_lc3_hot_bound_s3d_v352<tag>_x.json), MS_bound and MS_ult_bound
          (exact: fl(a + x) is monotone in x and the MS is monotone in the bound stress).
Writes results/v352/lever_root_table_v352.json and results/v352/tables/lever_root_table_v352.md.  Read-only on everything else.
usage: FEA3D_CAD=v352 lever_root_table_v352.py"""
from __future__ import annotations
import sys, os, json, math, time, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF          # noqa: E402
import lc3_bound as LB        # noqa: E402

ROOT = Path("/home/claude/work/fea3d")
RES, RUNS = ROOT / "results", ROOT / "runs"
OUT_J = RES / "v352" / "lever_root_table_v352.json"
OUT_M = RES / "v352" / "tables" / "lever_root_table_v352.md"
PARTS = ["GM-01", "GM-02"]
STATES = ["B1_21.65", "B1_19", "B1_2", "B1_1"]
STOPS = [f"stop{d:03d}" for d in range(0, 360, 45)]
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
BASES = [("g3", "lc1v352hbg3", "GVLO"), ("h3", "lc1v352hbh3", "GVHI")]
SFY, SFU = 1.5, 2.0
SETS = ("all", "regular")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()[:16]


def run(p):
    return f"pose_{p}_v352r3R3"


def rel(p):
    return str(Path(p).relative_to(ROOT))


def cold_rec(r):
    return {"case": r["case"], "state": r["state"], "MS_y": r["MS"], "MS_u": r["MS_ult"], "vm_MPa": r["vm_MPa"], "node": r["node"],
            "node_class": r.get("node_class"), "node_class_detail": r.get("node_class_detail"), "d_class_mm": r.get("d_class_mm"),
            "T_C": r["T_C"], "r_theta_z": r["r_theta_z"], "xyz_mm": r.get("xyz_mm"), "subcase_info": r.get("subcase_info"),
            "Fty_MPa": r.get("Fty_or_St_MPa"), "Ftu_MPa": r.get("Ftu_or_Sc_MPa"), "SF": [r.get("SF_y"), r.get("SF_u")]}


def cold_inputs():
    cold, files = {}, {}
    for s in STOPS:
        fn = RES / f"f1_post_lc3_pose_{s}_v352r3R3.json"
        d = json.loads(fn.read_text())
        files[s] = {"post": rel(fn), "post_sha16": sha16(fn)}
        for r in d["margins"]:
            if r["part"] in PARTS and r["case"] == "LC3":
                k = (s, "LC3", r["part"], r["set"])
                assert k not in cold, k
                cold[k] = cold_rec(r)
    for c in CONES:
        fn = RES / f"s3d_pose_{c}_v352r3R3.json"
        d = json.loads(fn.read_text())
        files[c] = {"post": rel(fn), "post_sha16": sha16(fn)}
        for case in ("GS", "TD", "LC6"):
            for r in d["cases"][case]["margins"]:
                if r["part"] in PARTS:
                    k = (c, case, r["part"], r["set"])
                    assert k not in cold, k
                    cold[k] = cold_rec(r)
    return cold, files


def r2_inputs():
    """lever_root_bound_v352.json: the R2 -> R3 records (4 poses x 2 levers x 2 sets) and the p = 1 cells; exact R3 - R2 from the posts."""
    fn = RES / "v352" / "lever_root_bound_v352.json"
    B = json.loads(fn.read_text())
    conv, delta = {}, {}
    for pose, P in B["poses"].items():
        case = P["case"]
        f2, f3 = RES / P["R2_file"], RES / P["R3_file"]
        d2, d3 = json.loads(f2.read_text()), json.loads(f3.read_text())

        def recs(d):
            m = d["margins"] if "margins" in d else d["cases"][case]["margins"]
            return {(r["part"], r["set"]): r for r in m if r["part"] in PARTS and r.get("case", case) == case}
        R2, R3 = recs(d2), recs(d3)
        for part, S in P["parts"].items():
            for st, x in S.items():
                conv[(pose, part, st)] = {"case": case, "R2_node": x["R2"]["node"], "R2_MPa": x["R2"]["vm_MPa"], "R3_node": x["R3"]["node"],
                                          "R3_MPa": x["R3"]["vm_MPa"], "change": x["change_R2_R3"], "converged_5pct": x["converged_5pct"],
                                          "p1": x["bound"]["p1"], "cell": x["cell"], "R2_R3_peak_distance_mm": x.get("R2_R3_peak_distance_mm")}
                if not x["converged_5pct"]:
                    dv = float(R3[(part, st)]["vm_MPa"]) - float(R2[(part, st)]["vm_MPa"])
                    assert abs((R3[(part, st)]["vm_MPa"] + dv) - x["bound"]["p1"]["vm_MPa"]) < 0.011, (pose, part, st)
                    delta[(pose, part, st)] = dv
    cells = {(c["pose"], c["case"], c["part"], c["set"]): c for c in B["cells"]}
    assert set((p, pa, s) for (p, _, pa, s) in cells) == set(delta), "p = 1 cells and non-converged records differ"
    return conv, delta, cells, {"file": rel(fn), "sha16": sha16(fn), "tol": B.get("tol")}


def hot_base(tag, lc1, delta, X_ref=None):
    """Per-pose node-wise hot bound on one base: {(pose, part, set, state): {"hot": row, "hot_p1": row or None}}."""
    t0 = time.time()
    M, meta = PF.load_model(lc1)
    ext = RES / "v352" / f"hb3_leverroot_extract_{tag}.npz"
    names = [x for x in M.bodies if x in PARTS]
    assert names == [x for x in PARTS], names
    poses = [(p, "lc3_env_") for p in STOPS] + [(p, "s3d_env_") for p in CONES]
    pm, env, files = {}, {}, {}
    for p, pfx in poses:
        mj = RUNS / run(p) / "model.json"
        pm[p] = json.loads(mj.read_text())
        fe = RES / f"{pfx}{run(p)}.npz"
        env[p] = np.load(fe)["vmD"]
        files[p] = {"env": rel(fe), "env_sha16": sha16(fe), "model_json_sha16": sha16(mj)}
    out, same_noff = {}, {}
    Xs = None
    for state in STATES:
        F = LB.fields_from_extract(str(ext), state, PARTS)
        _, body, T, X = PF.node_arrays(M, lc1, state)
        reg, _, sing = PF.singular_sets(M, X, ex_r=1.0)
        S, _ = PF.combine(F, "S", {"OP": PF.PC_MAX, "PM": PF.P_MAN})
        Xs = X
        for nm in names:
            b = M.bodies[nm]
            nodes = b.noff + np.arange(len(b.X0))
            a1, a2 = PF.allowables(b.mat, T[nodes])
            Tc = T[nodes] - 273.15
            v1 = np.max([PF.vm(S[nodes])], axis=0)          # as lc3_bound (one thermo-pressure combination)
            assert np.isfinite(v1).all(), f"{nm}: NaN in the extract rows"
            msk = reg[nodes]
            for p, _pfx in poses:
                bm = pm[p]["bodies"][nm]
                assert bm["n"] == len(b.X0), f"{p} {nm}: pose mesh differs from the base mesh"
                same_noff[(p, nm)] = bm["noff"] == b.noff
                vmD = env[p][bm["noff"]: bm["noff"] + bm["n"]].astype(np.float64)
                vb0 = v1 + vmD
                for st, m_ in (("regular", msk), ("all", np.ones(len(nodes), bool))):
                    res = {}
                    for key, dv in (("hot", 0.0), ("hot_p1", delta.get((p, nm, st)))):
                        if dv is None:
                            res[key] = None
                            continue
                        vb = vb0 + dv if dv else vb0
                        ms = a1 / (SFY * np.maximum(vb, 1e-9)) - 1.0
                        msu = a2 / (SFU * np.maximum(vb, 1e-9)) - 1.0
                        i = int(np.argmin(np.where(m_, ms, np.inf)))
                        iu = int(np.argmin(np.where(m_, msu, np.inf)))
                        x = X[nodes[i]]
                        nc = PF.node_class(X, sing, int(nodes[i]), ex_r=1.0)
                        res[key] = {"MS_bound": float(ms[i]), "MS_ult_bound": float(msu[iu]), "node": int(nodes[i]), "node_ult": int(nodes[iu]),
                                    "T_C": float(Tc[i]), "vm_bound_MPa": float(vb[i]), "vm_LC1_MPa": float(v1[i]), "vmD_MPa": float(vmD[i]),
                                    "added_p1_MPa": float(dv) if dv else 0.0, "Fty_MPa": float(a1[i]), "Ftu_MPa": float(a2[i]),
                                    "r_theta_z": [round(math.hypot(x[0], x[1]), 3), round(math.degrees(math.atan2(x[1], x[0])), 1), round(float(x[2]), 3)],
                                    "node_class": nc["class"], "node_class_detail": nc["class_detail"], "d_class_mm": nc["d_class_mm"]}
                    out[(p, nm, st, state)] = res
        print(f"{now()} [lever_root_table {tag} {state}] {time.time() - t0:.1f} s", flush=True)
    return out, files, same_noff, Xs, {"lc1_run": lc1, "extract": rel(ext), "extract_sha16": sha16(ext),
                                       "model_json_sha16": sha16(RUNS / lc1 / "model.json"),
                                       "T_npz_sha16": {s: sha16(RUNS / lc1 / s / "T.npz") for s in STATES}}


def check_env(tag, hot):
    """min over the poses of the per-pose bound == the published envelope bound (lc3_bound _x outputs), per state / part / set."""
    rep = []
    for kind, fn, poses in (("stops", RES / f"f1_lc3_hot_bound_v352{tag}_x.json", STOPS),
                            ("cones", RES / f"f1_lc3_hot_bound_s3d_v352{tag}_x.json", CONES)):
        d = json.loads(fn.read_text())
        assert d["poses"] == [run(p) for p in poses], (fn, d["poses"])
        for state, rows in d["states"].items():
            for r in rows:
                mine = [(hot[(p, r["part"], r["set"], state)]["hot"], p) for p in poses]
                ms_min, p_at = min((x["MS_bound"], p) for x, p in mine)
                msu_min = min(x["MS_ult_bound"] for x, _ in mine)
                node_at = next(x["node"] for x, p in mine if p == p_at)
                exact = ms_min == r["MS_bound"] and msu_min == r["MS_ult_bound"]
                close = abs(ms_min - r["MS_bound"]) <= 1e-12 * max(1.0, abs(r["MS_bound"])) and \
                    abs(msu_min - r["MS_ult_bound"]) <= 1e-12 * max(1.0, abs(r["MS_ult_bound"]))
                rep.append({"set_kind": kind, "file": rel(fn), "state": state, "part": r["part"], "set": r["set"], "MS_env": r["MS_bound"],
                            "MS_min_over_poses": ms_min, "MSu_env": r["MS_ult_bound"], "MSu_min_over_poses": msu_min, "pose_at_min": p_at,
                            "node_env": r["node"], "node_at_min": node_at, "result": "exact" if exact else ("rel1e-12" if close else "DIFFERENT")})
    return rep, {kind: sha16(fn) for kind, fn in (("stops", RES / f"f1_lc3_hot_bound_v352{tag}_x.json"),
                                                   ("cones", RES / f"f1_lc3_hot_bound_s3d_v352{tag}_x.json"))}


def main():
    if os.environ.get("FEA3D_CAD") != "v352":
        raise SystemExit("FEA3D_CAD=v352 required")
    t0 = time.time()
    cold, cold_files = cold_inputs()
    conv, delta, cells, bound_src = r2_inputs()
    per_base, base_meta, checks, env_sha = {}, {}, {}, {}
    X_ref, pose_files, noff = None, None, {}
    for tag, lc1, lab in BASES:
        hot, pfiles, same_noff, X, bm = hot_base(tag, lc1, delta)
        per_base[tag] = hot
        base_meta[tag] = dict(bm, label=lab)
        pose_files = pose_files or pfiles
        assert all(pose_files[p]["env_sha16"] == pfiles[p]["env_sha16"] for p in pfiles)
        noff[tag] = all(same_noff.values())
        X_ref = X if X_ref is None else X_ref
        checks[tag], env_sha[tag] = check_env(tag, hot)
    all_checks = [c for v in checks.values() for c in v]
    check_ok = all(c["result"] in ("exact", "rel1e-12") for c in all_checks)
    # R2-checked peak nodes per lever (any pose, any set) for the 13 poses without R2
    checked = {}
    for (pose, part, st), c in conv.items():
        checked.setdefault(part, {}).setdefault(c["R3_node"], []).append({"pose": pose, "set": st, "case": c["case"], "change": c["change"]})

    def near_checked(part, node):
        best = None
        for n, L in checked.get(part, {}).items():
            dd = float(np.linalg.norm(X_ref[n] - X_ref[node]))
            if best is None or dd < best[0]:
                best = (dd, n, L)
        return {"node": best[1], "distance_mm": round(best[0], 3), "checked_at": best[2]} if best else None

    rows = []
    for kind, poses, case in (("stops", STOPS, "LC3"), ("cones", CONES, "GS")):
        for p in poses:
            for part in PARTS:
                for st in SETS:
                    c = cold[(p, case, part, st)]
                    cv = conv.get((p, part, st))
                    cl = cells.get((p, case, part, st))
                    if cl:
                        cell = {"MS_y": cl["MS_y"], "MS_u": cl["MS_u"], "vm_MPa": cl["vm_MPa"], "rule": "p = 1 bound (R2 -> R3 > 5 %; order ASSUMED; lead 12:28Z (5))",
                                "tag": "DERIVED"}
                    else:
                        cell = {"MS_y": c["MS_y"], "MS_u": c["MS_u"], "vm_MPa": c["vm_MPa"],
                                "rule": ("R3 value (R2 -> R3 within 5 %)" if cv else "R3 value (no R2 run at this pose)"), "tag": "SIM"}
                    hb = []
                    for tag, _, lab in BASES:
                        for state in STATES:
                            h = per_base[tag][(p, part, st, state)]
                            hb.append((h["hot"]["MS_bound"], tag, lab, state, h))
                    worst = min(hb, key=lambda t: t[0])
                    worst_u = min(hb, key=lambda t: t[4]["hot"]["MS_ult_bound"])
                    hot = dict(worst[4]["hot"], base=f"{worst[1]} ({worst[2]})", state=worst[3],
                               MS_ult_bound_worst=worst_u[4]["hot"]["MS_ult_bound"],
                               MS_ult_bound_at=f"{worst_u[1]} ({worst_u[2]}) {worst_u[3]}")
                    per_base_min = {tag: min(per_base[tag][(p, part, st, s)]["hot"]["MS_bound"] for s in STATES) for tag, _, _ in BASES}
                    hp1 = None
                    if (p, part, st) in delta:
                        hq = [(per_base[tag][(p, part, st, s)]["hot_p1"], tag, lab, s) for tag, _, lab in BASES for s in STATES]
                        w = min(hq, key=lambda t: t[0]["MS_bound"])
                        wu = min(hq, key=lambda t: t[0]["MS_ult_bound"])
                        hp1 = dict(w[0], base=f"{w[1]} ({w[2]})", state=w[3], MS_ult_bound_worst=wu[0]["MS_ult_bound"],
                                   MS_ult_bound_at=f"{wu[1]} ({wu[2]}) {wu[3]}")
                    ctx = None
                    if kind == "cones":
                        ctx = {cs: {k: cold[(p, cs, part, st)][k] for k in ("case", "MS_y", "MS_u", "vm_MPa", "node", "node_class")}
                               for cs in ("TD", "LC6")}
                    rows.append({"kind": kind, "pose": p, "run": run(p), "case": case, "part": part, "set": st, "cold": c,
                                 "R2_R3": cv, "cell": cell, "peak_vs_R2_checked": (None if cv else near_checked(part, c["node"])),
                                 "hot": hot, "hot_min_per_base": per_base_min, "hot_p1": hp1,
                                 "hot_cell": ({"MS_y": hp1["MS_bound"], "MS_u": hp1["MS_ult_bound_worst"], "rule": "hot bound + p = 1 increment",
                                               "tag": "DERIVED"} if hp1 else
                                              {"MS_y": hot["MS_bound"], "MS_u": hot["MS_ult_bound_worst"], "rule": "hot bound", "tag": "DERIVED"}),
                                 "cold_context_F2": ctx})
    # governing rows per lever and kind
    gov = {}
    for kind in ("stops", "cones"):
        for part in PARTS:
            R = [r for r in rows if r["kind"] == kind and r["part"] == part]
            for st in SETS:
                Rs = [r for r in R if r["set"] == st]
                gc = min(Rs, key=lambda r: r["cell"]["MS_y"])
                gcu = min(Rs, key=lambda r: r["cell"]["MS_u"])
                gh = min(Rs, key=lambda r: r["hot_cell"]["MS_y"])
                ghu = min(Rs, key=lambda r: r["hot_cell"]["MS_u"])
                gov[f"{kind}|{part}|{st}"] = {"cold_cell_MS_y": gc["cell"]["MS_y"], "cold_cell_pose": gc["pose"], "cold_cell_rule": gc["cell"]["rule"],
                                              "cold_cell_MS_u": gcu["cell"]["MS_u"], "cold_cell_pose_u": gcu["pose"],
                                              "hot_cell_MS_y": gh["hot_cell"]["MS_y"], "hot_cell_pose": gh["pose"], "hot_cell_rule": gh["hot_cell"]["rule"],
                                              "hot_cell_MS_u": ghu["hot_cell"]["MS_u"], "hot_cell_pose_u": ghu["pose"],
                                              "hot_base_state": f"{gh['hot']['base']} {gh['hot']['state']}" if not gh["hot_p1"] else f"{gh['hot_p1']['base']} {gh['hot_p1']['state']}"}
    neg = [r for r in rows if min(r["cell"]["MS_y"], r["cell"]["MS_u"], r["hot_cell"]["MS_y"], r["hot_cell"]["MS_u"]) < 0]
    out = {"id": "lever_root_table_v352", "date_utc": now(), "doc": __doc__.split("usage:")[0].strip(),
           "evidence": "cold SIM (R3 pose runs, rev 3 levers, CAD v3.5.2); p = 1 cells DERIVED (order ASSUMED, no R4); hot DERIVED "
                       "(node-wise sub-additivity bound on SIM inputs).  Nothing here is physical approval.",
           "inputs": {"cold_posts": cold_files, "pose_env_and_model": pose_files, "bases": base_meta, "lever_root_bound": bound_src,
                      "envelope_bound_x_sha16": env_sha, "script_sha16": sha16(Path(__file__))},
           "same_node_numbering_pose_vs_base": noff,
           "check_per_pose_vs_envelope": {"result": "PASS" if check_ok else "FAIL", "n": len(all_checks),
                                          "n_exact": sum(c["result"] == "exact" for c in all_checks), "rows": all_checks},
           "governing": gov, "n_negative_rows": len(neg), "rows": rows, "runtime_s": round(time.time() - t0, 1)}
    OUT_J.write_text(json.dumps(out, indent=1, default=float))
    OUT_M.write_text(markdown(out))
    print(f"{now()} lever_root_table: {len(rows)} rows, check {out['check_per_pose_vs_envelope']['result']} "
          f"({out['check_per_pose_vs_envelope']['n_exact']} of {len(all_checks)} exact), negatives {len(neg)}; "
          f"json {sha16(OUT_J)} md {sha16(OUT_M)} ({time.time() - t0:.0f} s)", flush=True)
    for k, g in gov.items():
        print(f"  {k}: cold cell {g['cold_cell_MS_y']:+.3f} / {g['cold_cell_MS_u']:+.3f} ({g['cold_cell_pose']}/{g['cold_cell_pose_u']}); "
              f"hot {g['hot_cell_MS_y']:+.3f} / {g['hot_cell_MS_u']:+.3f} ({g['hot_cell_pose']}/{g['hot_cell_pose_u']}; {g['hot_base_state']}; {g['hot_cell_rule']})")
    return 0 if check_ok else 2


def f3(x):
    return f"{x:+.3f}"


def cls(c):
    return c["node_class"] if c["node_class"] == "regular" else f"{c['node_class']} {c['d_class_mm']} mm"


def markdown(o):
    rows = o["rows"]
    L = ["# Lever roots at R3: F1 LC3 at the 8 stops and F2 GS at the 9 cones, cold and hot bound (v3.5.2 item 1)", "",
         f"fea3d, {o['date_utc']} (date -u); results/v352/lever_root_table_v352.json, scripts/lever_root_table_v352.py "
         f"{o['inputs']['script_sha16']}.  {o['evidence']}", "",
         "Levers GM-01 (servo 1) and GM-02 (servo 2), rev 3 (CAD v3.5.2), at R3 (the six junction faces at h 0.25 / 0.2 mm).  MS = "
         "Fty(T) / (1.5 vM) - 1 and Ftu(T) / (2.0 vM) - 1 at the node temperature (AL7075-T6, 470 / 540 MPa at the lever-root "
         "temperatures).  Cold: B1_21.65 node temperatures, no thermal stress.  Cell: the R3 value, or the p = 1 bound where R2 -> R3 "
         "exceeded 5 % (lead 12:28Z (5); R2 exists at stop045, stop315, alpha+, alpha- only).  Hot: per pose, node by node, LC1 "
         "thermo-pressure vM of the R3 base (GVLO hbg3 / GVHI hbh3, 4 burn states) + the pose's own increment vM; worst base and "
         "state.  At the cones the increment is the GS + TD + LC6 envelope of the pose (a lower bound on the GS-only hot margin).  "
         "Hot + p1: the hot bound with the cold p = 1 increment added at every lever node (the three p = 1 cells).", "",
         f"Check: the minimum over the poses of the per-pose hot bound equals the published envelope bound per base, state, part and "
         f"set: {o['check_per_pose_vs_envelope']['result']} ({o['check_per_pose_vs_envelope']['n_exact']} of "
         f"{o['check_per_pose_vs_envelope']['n']} rows exact).  Node numbering of the levers identical in the pose and base models: "
         f"{o['same_node_numbering_pose_vs_base']}.", ""]
    L += ["## Governing values per lever", "", "| set | lever | cold cell MS y / u (pose) | rule | hot cell MS y / u (pose; base, state) | rule |",
          "|---|---|---|---|---|---|"]
    for kind, lab in (("stops", "F1 LC3, 8 stops"), ("cones", "F2 GS, 9 cones")):
        for part in PARTS:
            for st in SETS:
                g = o["governing"][f"{kind}|{part}|{st}"]
                L.append(f"| {lab}, {st} | {part} | {f3(g['cold_cell_MS_y'])} / {f3(g['cold_cell_MS_u'])} ({g['cold_cell_pose']}"
                         + (f" / {g['cold_cell_pose_u']}" if g['cold_cell_pose_u'] != g['cold_cell_pose'] else "") + f") | {g['cold_cell_rule']} | "
                         f"{f3(g['hot_cell_MS_y'])} / {f3(g['hot_cell_MS_u'])} ({g['hot_cell_pose']}"
                         + (f" / {g['hot_cell_pose_u']}" if g['hot_cell_pose_u'] != g['hot_cell_pose'] else "") + f"; {g['hot_base_state']}) | {g['hot_cell_rule']} |")
    L += ["", f"Rows with a negative cell or hot cell: {o['n_negative_rows']}.", ""]
    for kind, lab, case in (("stops", "F1 LC3 at the 8 stop poses", "LC3"), ("cones", "F2 GS (servo stall) at the 9 cone poses", "GS")):
        L += [f"## {lab}", "",
              "| pose | lever | set | cold MS y / u (vM MPa; node, class) | R2 -> R3 | cell MS y / u | hot bound MS y / u (vM_LC1 + vMD MPa; node; base, state) | hot + p1 |"
              + (" TD / LC6 cold MS y |" if kind == "cones" else ""),
              "|---|---|---|---|---|---|---|---|" + ("---|" if kind == "cones" else "")]
        for r in [x for x in rows if x["kind"] == kind]:
            c, h, cv = r["cold"], r["hot"], r["R2_R3"]
            if cv:
                conv_s = f"{cv['change'] * 100:+.2f} % ({cv['R2_MPa']:.1f} -> {cv['R3_MPa']:.1f})"
            else:
                pc = r["peak_vs_R2_checked"]
                conv_s = "no R2" + (f"; peak node = R2-checked node ({', '.join(x['pose'] + ' ' + format(x['change'] * 100, '+.1f') + ' %' for x in pc['checked_at'][:2])})"
                                    if pc and pc["distance_mm"] == 0 else (f"; {pc['distance_mm']:.2f} mm from R2-checked node {pc['node']}" if pc else ""))
            hp = r["hot_p1"]
            L.append(f"| {r['pose']} | {r['part']} | {r['set']} | {f3(c['MS_y'])} / {f3(c['MS_u'])} ({c['vm_MPa']:.1f}; {c['node']}, {cls(c)}) | {conv_s} | "
                     f"{f3(r['cell']['MS_y'])} / {f3(r['cell']['MS_u'])}{' (p1)' if r['cell']['tag'] == 'DERIVED' else ''} | "
                     f"{f3(h['MS_bound'])} / {f3(h['MS_ult_bound_worst'])} ({h['vm_LC1_MPa']:.1f} + {h['vmD_MPa']:.1f}; {h['node']}; {h['base']}, {h['state']}) | "
                     + (f"{f3(hp['MS_bound'])} / {f3(hp['MS_ult_bound_worst'])} (+{hp['added_p1_MPa']:.1f} MPa)" if hp else "-") + " |"
                     + (f" {f3(r['cold_context_F2']['TD']['MS_y'])} / {f3(r['cold_context_F2']['LC6']['MS_y'])} |" if kind == "cones" else ""))
        L.append("")
    L += ["## Notes", "",
          "- The cold rows are the R3 post records (SIM) unchanged; the p = 1 cells are those of results/v352/lever_root_bound_v352.json "
          "(DERIVED; the R2 and R3 values are shown).  At the 13 poses without an R2 run the cell is the R3 value (no R2 run there), and the "
          "row says whether the peak node is one of the R2-checked peak nodes; this table does not extend the p = 1 rule to them.",
          "- The hot rows are a LOWER BOUND on the hot margin (sub-additivity: vM(A + D) <= vM(A) + vM(D)); the exact hot sum is not "
          "available because the pose runs carry no thermal step.  The pose-by-pose minimum reproduces the published envelope bound "
          "exactly (check above).",
          "- 'hot + p1' adds the cold R3 - R2 peak difference (MPa) at every node of the lever: a uniform shift, conservative away from "
          "the peak; it is not a hot R2 / R3 study.",
          "- Node classes (all-node rule 234 (4)): regular, RE (re-entrant edge within 1 mm), ID (idealisation), BT (low-quality tet); "
          "the regular set excludes them.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
