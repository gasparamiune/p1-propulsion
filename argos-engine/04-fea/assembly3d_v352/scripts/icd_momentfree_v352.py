"""Datasheet mounting rows with the OP-moment residue removed: the estimate beside each affected row (fea3d 2026-10-20; lead 22:24:34Z:
"Put the moment-free statics estimate beside each affected row").  Python only, no solve: superposition of the posted unit steps.

Basis [DERIVED on SIM]:
  * the OP unit step of every v3.5.2 model carries a moment about the pivot that the physical load does not have (report 9B.3,
    op_moment_check_v352 / op_moment_global_v352): R3 pose runs (TC-09 level 1.8) Q [304-307, 2,298] N mm/MPa, of which the two one-sided
    TC-09 aft-boundary faces (elements 24664 / 23610 at p/Pc 0.75) give a couple of about 1.56 N m/MPa; L1 global runs (LC1, LC2, FA-1)
    Q [539, 484] N mm/MPa;
  * the rods are the only moment path about the two gimbal axes, so that residue reaches the airframe as the rod-force pair it
    produces (statics: dt = A^-1 (-dQ)) plus the opposite bearing forces;
  * the airframe-hole reactions of such a pure couple are taken from the engine angular-acceleration unit steps EAX / EAY of a pose run,
    combined to give the same rod tensions: dRF = b_X RF_EAX + b_Y RF_EAY with [s_EAX s_EAY] b = dt (s from the fields with the post's
    own spring code).  Neglected: the EA steps' small net force (about 0.012 N per rad/s2) and the residue's roll component (about 6 %
    of the couple); ASSUMED: the transmission does not depend on where on the engine the couple is applied (the engine is a free body on
    the gimbal: its rods and bearings carry the resultant);
  * R3 pose runs use their own EA steps; the L1 global runs (neutral, no EA steps) use those of pose_neutral_v352r3R3 (same fixed
    group and airframe meshes at L1) [ASSUMED];
  * variants: 'tc09_removed' = the two TC-09 faces at p/Pc 1.0 (the moment-free statics estimate of the lead's note; R3 runs only),
    'op_zero' = the whole OP moment removed (the physical statics: no OP moment about the pivot);
  * case logic as posted: LC1 / LC2 / FA-1 / TD / LC6 / LC2F sub-case coefficients unchanged; GS re-solves EAX / EAY so the rods stay at
    the prescribed corners (post_s3d); LC3 re-solves the runaway bumper force fb_run (M_stop 41.14 N m and 609 N per rod, post_lc3).
Checks recorded: the deck statics against the posted OP unit rods; the fields' EA unit rods against the posts; the recomputed LC3 fb_run
(as found) against the posted fb_N; the as-found envelope against icd_export_v352's (every hole and component).
Governing value (lead 22:54:03Z: "For every datasheet hole-load row, L1 and R3 alike, the governing value is the larger of the as-found
value and the moment-free estimate ... Tag the governing value DERIVED ... Pull-out follows the same rule"): per case, hole and component
(shear, |axial|, |tangential|, pull-out, push-in, resultant) and per ring-resultant component, governing = the largest of the as-found
value and the estimates (L1 global: 'op_zero'; R3 pose: 'tc09_removed' and 'op_zero', so that the governing value bounds every value
shown), with the variant that governs.  Not physical approval.
usage: FEA3D_CAD=v352 icd_momentfree_v352.py -> results/v352/icd_momentfree_v352.json, results/v352/tables/icd_momentfree_v352.md"""
from __future__ import annotations
import sys, json, math, time, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import icd_export_v352 as IE           # noqa: E402  (reactions, combine, envelope, hole frames, sources, lc3_coefs)
import op_moment_check_v352 as OM      # noqa: E402  (deck(): OP load from the deck, statics rods, TC-09 boundary removed)
import post_f1 as PF                   # noqa: E402
import post_lc3 as PL                  # noqa: E402

ROOT = Path("/home/claude/work/fea3d")
RUNS, RES = ROOT / "runs", ROOT / "results"
OUTJ, OUTM = RES / "v352" / "icd_momentfree_v352.json", RES / "v352" / "tables" / "icd_momentfree_v352.md"
STOPS, CONES = IE.STOPS, IE.CONES
RODS = ("ROD_1", "ROD_2")
G_STEPS = ("OP", "GX", "GY", "GZ")
VARS = ("as_found", "tc09_removed", "op_zero")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def ea_unit(run):
    """rod tensions per unit EAX / EAY from the stored fields (the post's own spring code) and the run's hole reactions."""
    M, meta = PF.load_model(run)
    z = np.load(RUNS / run / "B1_21.65" / "fields.npz")
    sf = PL.spring_forces_per_step(M, {k: z[k] for k in ("U_EAX", "U_EAY")}, ["EAX", "EAY"])
    S = np.array([[sf[r]["EAX"], sf[r]["EAY"]] for r in RODS])
    return S, IE.reactions(run, "B1_21.65")


def drf(S, RF, dt):
    b = np.linalg.solve(S, np.asarray(dt, float))
    return {h: b[0] * (RF["EAX"][h]) + b[1] * (RF["EAY"][h]) for h in RF["EAX"]}, b.tolist()


def modified_rf(RF, d):
    out = {st: dict(v) for st, v in RF.items()}
    out["OP"] = {h: RF["OP"][h] - d.get(h, 0.0) for h in RF["OP"]}
    return out


def lc3_resolve(post, s, A, var_dop, coefs):
    """post_lc3 runaway logic with the OP unit rods replaced (s['OP'] - var_dop); returns new coefficient dicts and fb values."""
    sp = dict(s)
    sp["OP"] = s["OP"] - var_dop
    Q = {st: A @ sp[st] for st in sp}
    QB = Q["BUMP"]
    u = QB / np.linalg.norm(QB)
    out, fbs = [], []
    for co, i_ in zip(coefs, post["subcases"]):
        c0 = {k: v for k, v in co.items() if k != "BUMP"}
        if i_["mode"] == "hold":
            out.append(dict(c0, BUMP=0.0))
            continue
        QL = sum(c * Q[st] for st, c in c0.items())
        tL = sum(c * sp[st] for st, c in c0.items())
        lims = [(PL.M_STOP - QL @ u) / np.linalg.norm(QB)]
        for j in range(2):
            sb = sp["BUMP"][j]
            if abs(sb) > 1e-9:
                lims.append((((-PL.F_ROD_STOP if sb < 0 else PL.F_ROD_STOP) - tL[j]) / sb))
        fb = max(min(lims), 0.0)
        fbs.append(fb)
        out.append(dict(c0, BUMP=float(fb)))
    return out, fbs


def main():
    t0 = time.time()
    rs = json.loads((RES / "v352" / "rodstep_cones_v352.json").read_text())
    og = json.loads((RES / "v352" / "op_moment_global_v352.json").read_text())
    t_glob = np.asarray(next(r for r in og["rows"] if r["run"] == "lc1v352g" and r["step"] == "OP")["rods_statics_N_per_MPa"])
    res = {"doc": __doc__.split("usage:")[0].strip(), "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": {}, "runs": {}, "cases": [],
           "files_sha16": {f: sha16(RES / f) for f in ("v352/rodstep_cones_v352.json", "v352/op_moment_global_v352.json", "v352/op_moment_check_v352.json")}}
    # ---------------------------------------------------------------- per R3 pose run: deck statics, EA response, hole deltas
    per = {}
    for run in [f"pose_{p}_v352r3R3" for p in CONES + STOPS]:
        dk = OM.deck(run)
        S, RF = ea_unit(run)
        t_op, t_cl = np.asarray(dk["rods_OP_statics_N_per_MPa"]), np.asarray(dk["TC09_boundary_removed"]["rods_OP_statics_N_per_MPa"])
        d_tc, b_tc = drf(S, RF, t_op - t_cl)
        d_z, b_z = drf(S, RF, t_op)
        per[run] = {"S_EA": S, "RF": RF, "t_op": t_op, "t_cl": t_cl, "d": {"tc09_removed": d_tc, "op_zero": d_z, "as_found": {}},
                    "dop": {"tc09_removed": t_op - t_cl, "op_zero": t_op, "as_found": np.zeros(2)}}
        res["runs"][run] = {"deck_sha16": dk["deck_sha16"], "Q_gimbal_axes_Nmm_per_MPa": dk["Q_gimbal_axes_Nmm_per_MPa"], "OP_rods_statics_N_per_MPa": t_op.tolist(),
                            "OP_rods_tc09_removed_N_per_MPa": t_cl.tolist(), "EA_unit_rods_from_fields": S.round(4).tolist(),
                            "b_EA_rad_s2_per_MPa": {"tc09_removed": b_tc, "op_zero": b_z},
                            "net_hole_force_of_dRF_N_per_MPa": {k: np.round(sum(v[h] for h in v if h in IE.HF), 4).tolist() for k, v in (("tc09_removed", d_tc), ("op_zero", d_z))}}
        print(f"[{time.time() - t0:6.1f} s] {run}: t_op {t_op.round(3).tolist()} t_cl {t_cl.round(3).tolist()} b_tc {np.round(b_tc, 2).tolist()}", flush=True)
    # checks against the posts (cones: rodstep_cones; EA: rodstep_cones)
    ck = []
    for p in CONES:
        u = rs["poses"][p]["v352_R3"]["unit_rod_N"]
        run = f"pose_{p}_v352r3R3"
        ck.append({"pose": p, "OP_statics_minus_post": float(np.max(np.abs(per[run]["t_op"] - np.array([u[r]["OP"] for r in RODS])))),
                   "EA_fields_minus_post": float(np.max(np.abs(per[run]["S_EA"] - np.array([[u[r]["EAX"], u[r]["EAY"]] for r in RODS]))))})
    res["checks"]["cones_unit_rods"] = ck
    # neutral EA response for the L1 global runs
    nS, nRF = per["pose_neutral_v352r3R3"]["S_EA"], per["pose_neutral_v352r3R3"]["RF"]
    d_glob, b_glob = drf(nS, nRF, t_glob)
    res["global_L1"] = {"OP_rods_statics_N_per_MPa": t_glob.tolist(), "EA_response_from": "pose_neutral_v352r3R3", "b_EA_rad_s2_per_MPa": b_glob}
    # ---------------------------------------------------------------- cases
    BURN = IE.BURN

    def env_variant(items_by_var, rfmod):
        out = {}
        for var, items in items_by_var.items():
            cache = {}
            for run, st, _ in items:
                cache[(run, st)] = rfmod(var, run, st)
            out[var] = IE.envelope(items, cache)
        return out

    def summarize(e):
        hs = e["holes"]
        h = max(hs, key=lambda k: hs[k]["max_shear_N"])
        return {"max_shear_N": round(hs[h]["max_shear_N"], 1), "hole": h, "max_abs_axial_N": round(max(v["max_abs_axial_N"] for v in hs.values()), 1),
                "max_pullout_N": round(max(v["max_pullout_N"] for v in hs.values()), 1),
                "per_hole_max_shear_N": {k: round(v["max_shear_N"], 1) for k, v in sorted(hs.items())},
                "per_hole": {k: {q: round(float(v[q]), 3) for q in IE.Q} for k, v in sorted(hs.items())},
                "rings": e["rings"], "total_on_airframe": e["total_on_airframe"]}

    rf_glob = {}

    def rf_global(var, run, st):
        if (run, st) not in rf_glob:
            rf_glob[(run, st)] = IE.reactions(run, st)
        RF = rf_glob[(run, st)]
        return modified_rf(RF, d_glob) if var == "op_zero" else RF

    def rf_pose(var, run, st):
        return modified_rf(per[run]["RF"], per[run]["d"][var]) if var != "as_found" else per[run]["RF"]

    # LC1 / LC2 (lc1v352g / lc1v352h, 4 burn states) and FA-1 (fa1v352n): L1 global, coefficients unchanged
    glob_cases = []
    for c in ("LC1", "LC2"):
        it = []
        for run in ("lc1v352g", "lc1v352h"):
            x = IE.f1_items(RES / f"f1_post_{run}.json", run, c, BURN)
            it += x or []
        glob_cases.append((c, f"{c} (GVLO + GVHI)", it))
    for c in ("FA1Q", "FA1D", "FA1U", "FA1S", "FA1T"):
        glob_cases.append((c, c, IE.f1_items(RES / "f1_post_fa1v352n.json", "fa1v352n", c)))
    for c, lab, it in glob_cases:
        ev = env_variant({"as_found": it, "op_zero": it}, rf_global)
        res["cases"].append({"group": c, "case": lab, "model": "L1 global", "n_subcases": ev["as_found"]["n_subcases"],
                             "variants": {k: summarize(v) for k, v in ev.items()}, "tc09_removed": "n/a (L1 mesh: no one-sided TC-09 faces)"})
        print(f"[{time.time() - t0:6.1f} s] {lab}: " + "; ".join(f"{k} {summarize(v)['max_shear_N']} ({summarize(v)['hole']})" for k, v in ev.items()), flush=True)
    # LC3: 8 stops, the runaway bumper force re-solved per variant
    lc3_items = {v: [] for v in VARS}
    fbchk, fbr = [], {v: [] for v in VARS}
    for s_ in STOPS:
        run = f"pose_{s_}_v352r3R3"
        post = IE.jl(RES / f"f1_post_lc3_pose_{s_}_v352r3R3.json")
        A = np.asarray(post["rod_moment_matrix_Nmm_per_N"])
        coefs = IE.lc3_coefs(post)
        Sx = per[run]["S_EA"]
        # unit rods OP, GX, GY, GZ, BUMP by least squares on the 64 sub-cases after removing the EA share (fields)
        C, T = [], []
        for co, i_ in zip(coefs, post["subcases"]):
            t = np.array([i_["rod_tension_N"][r] for r in RODS]) - (co["EAX"] * Sx[:, 0] + co["EAY"] * Sx[:, 1])
            C.append([co["OP"], co["GX"], co["GY"], co["GZ"], co["BUMP"]])
            T.append(t)
        C, T = np.array(C), np.array(T)
        X, *_ = np.linalg.lstsq(C, T, rcond=None)
        resid = float(np.max(np.abs(C @ X - T)))
        s = {st: X[k] for k, st in enumerate(("OP", "GX", "GY", "GZ", "BUMP"))}
        s["EAX"], s["EAY"] = Sx[:, 0], Sx[:, 1]
        for var in VARS:
            nc, fbs = lc3_resolve(post, s, A, per[run]["dop"][var], coefs)
            lc3_items[var].append((run, "B1_21.65", nc))
            fbr[var] += fbs
            if var == "as_found":
                post_fb = [i_["fb_N"] for i_ in post["subcases"] if i_["mode"] == "runaway"]
                fbchk.append({"run": run, "unit_rod_fit_resid_N": resid, "fb_run_recomputed_minus_post_max_N": float(np.max(np.abs(np.array(fbs) - np.array(post_fb)))),
                              "OP_lstsq_minus_statics": float(np.max(np.abs(s["OP"] - per[run]["t_op"])))})
    res["checks"]["lc3"] = fbchk
    ev = env_variant(lc3_items, rf_pose)
    res["cases"].append({"group": "LC3", "case": "LC3 (8 stop poses at R3)", "model": "R3 pose", "n_subcases": ev["as_found"]["n_subcases"],
                         "variants": {k: summarize(v) for k, v in ev.items()},
                         "fb_run_range_N": {v: [round(min(fbr[v]), 1), round(max(fbr[v]), 1)] for v in VARS}})
    print(f"[{time.time() - t0:6.1f} s] LC3: " + "; ".join(f"{k} {summarize(v)['max_shear_N']} ({summarize(v)['hole']})" for k, v in ev.items())
          + f" fb_run {res['cases'][-1]['fb_run_range_N']}", flush=True)
    # F2 (9 cones): GS re-solves EA; TD0 / TDP / LC6 / LC2F coefficients unchanged
    for c, lab in IE.F2C:
        items = {v: [] for v in VARS}
        for p in CONES:
            run = f"pose_{p}_v352r3R3"
            d = IE.jl(RES / f"s3d_pose_{p}_v352r3R3.json")
            cc = d["cases"][c]
            u = rs["poses"][p]["v352_R3"]["unit_rod_N"]
            s = {st: np.array([u[r][st] for r in RODS]) for st in ("OP", "GX", "GY", "GZ", "EAX", "EAY")}
            S2 = np.column_stack([s["EAX"], s["EAY"]])
            for var in VARS:
                if c != "GS":
                    items[var].append((run, "B1_21.65", cc["subcase_coefs"]))
                    continue
                sop = s["OP"] - per[run]["dop"][var]
                nc = []
                for co, i_ in zip(cc["subcase_coefs"], cc["subcases"]):
                    tt = np.array([i_["rod_tension_N"][r] for r in RODS])
                    tL = co["OP"] * sop + sum(co.get(st, 0.0) * s[st] for st in ("GX", "GY", "GZ"))
                    ea = np.linalg.solve(S2, tt - tL)
                    nc.append(dict(co, EAX=float(ea[0]), EAY=float(ea[1])))
                items[var].append((run, "B1_21.65", nc))
        ev = env_variant(items, rf_pose)
        res["cases"].append({"group": c, "case": lab, "model": "R3 pose", "n_subcases": ev["as_found"]["n_subcases"], "variants": {k: summarize(v) for k, v in ev.items()}})
        print(f"[{time.time() - t0:6.1f} s] {lab}: " + "; ".join(f"{k} {summarize(v)['max_shear_N']} ({summarize(v)['hole']})" for k, v in ev.items()), flush=True)
    # ---------------------------------------------------------------- governing value (lead 22:54:03Z), DERIVED
    gov_vars = {"L1 global": ("op_zero",), "R3 pose": ("tc09_removed", "op_zero")}
    note = {"L1 global": "transfer through pose_neutral_v352r3R3's EA steps (ASSUMED); the as-found value carries the 0.72 N m/MPa residue",
            "R3 pose": "transfer through the run's own EA steps (ASSUMED pure-couple transmission); the as-found value carries the ~2.3 N m/MPa residue"}
    cnt = {"cells": 0, "estimate_governs": 0, "estimate_governs_by_0p5N_or_more": 0, "op_zero_above_as_found_and_tc09_by_0p5N_or_more": 0}
    vmax = lambda arrs: np.maximum.reduce([np.atleast_1d(np.asarray(x, float)) for x in arrs])
    for c in res["cases"]:
        v, ests = c["variants"], gov_vars[c["model"]]
        gh = {}
        for h, a in v["as_found"]["per_hole"].items():
            gh[h] = {}
            for q in IE.Q:
                cand = [("as_found", a[q])] + [(k, v[k]["per_hole"][h][q]) for k in ests]
                by, val = max(cand, key=lambda x: x[1])          # ties -> as found (first)
                gh[h][q] = {"value": val, "by": by, **{k: x for k, x in cand}}
                cnt["cells"] += 1
                if by != "as_found":
                    cnt["estimate_governs"] += 1
                    cnt["estimate_governs_by_0p5N_or_more"] += int(val - a[q] >= 0.5)
                    if "tc09_removed" in ests and by == "op_zero" and val - max(a[q], v["tc09_removed"]["per_hole"][h][q]) >= 0.5:
                        cnt["op_zero_above_as_found_and_tc09_by_0p5N_or_more"] += 1
        gr = {g: {q: (vmax([v[k]["rings"][g][q] for k in ("as_found",) + ests]).tolist() if isinstance(x, list)
                      else float(max(v[k]["rings"][g][q] for k in ("as_found",) + ests)))
                  for q, x in v["as_found"]["rings"][g].items()} for g in v["as_found"]["rings"]}
        gt = {q: vmax([v[k]["total_on_airframe"][q] for k in ("as_found",) + ests]).tolist() for q in v["as_found"]["total_on_airframe"]}
        hs = max(gh, key=lambda k: gh[k]["max_shear_N"]["value"])
        hp = max(gh, key=lambda k: gh[k]["max_pullout_N"]["value"])
        c["governing"] = {"tag": "DERIVED", "rule": "lead 22:54:03Z: the larger of the as-found value and the estimate(s)", "estimates": list(ests),
                          "note": note[c["model"]], "max_shear_N": round(gh[hs]["max_shear_N"]["value"], 1), "hole": hs, "by": gh[hs]["max_shear_N"]["by"],
                          "max_pullout_N": round(gh[hp]["max_pullout_N"]["value"], 1), "pullout_hole": hp, "pullout_by": gh[hp]["max_pullout_N"]["by"],
                          "per_hole": gh, "rings": gr, "total_on_airframe": gt}
    res["governing_counts"] = cnt
    # as-found check against icd_export_v352's own envelope (same runs and sub-cases): case maxima and every hole / component
    mj = IE.jl(IE.OUTJ) if IE.OUTJ.exists() else None
    if mj:
        ref = {c["case"].split(" (")[0]: c for c in mj["models"]["v352"]["cases"] if not c.get("pending") and c.get("holes")}
        diffs, dmax = [], 0.0
        for c in res["cases"]:
            k = c["case"].split(" (")[0]
            r = ref.get(k)
            if r:
                mx = max(h["max_shear_N"] for h in r["holes"].values())
                d_ = max(abs(c["variants"]["as_found"]["per_hole"][h][q] - r["holes"][h][q]) for h in r["holes"] for q in IE.Q)
                dmax = max(dmax, d_)
                diffs.append({"case": c["case"], "icd_export_max_shear_N": round(mx, 1), "as_found_here_N": c["variants"]["as_found"]["max_shear_N"],
                              "max_abs_diff_any_hole_component_N": d_})
        res["checks"]["as_found_vs_icd_export"] = {"file_sha16": sha16(IE.OUTJ), "rows": diffs, "max_abs_diff_N": dmax}
        print(f"[{time.time() - t0:6.1f} s] as found vs icd_export (every hole, component): max |diff| {dmax:.2e} N", flush=True)
    print(f"[{time.time() - t0:6.1f} s] governing: {cnt}", flush=True)
    OUTJ.write_text(json.dumps(res, indent=1, default=float))
    # markdown
    L = ["# Airframe-hole loads with the OP-moment residue removed: estimate beside each datasheet row and the governing value (v3.5.2)", "",
         f"Generated {res['date']} by scripts/icd_momentfree_v352.py (DERIVED on SIM; superposition of the posted unit steps, no re-solve). "
         "As found = the datasheet value (engine_mount_data_v352). Moment-free estimate = the two one-sided TC-09 aft-boundary faces at p/Pc 1.0 "
         "(R3 pose runs; the lead's 22:24:34Z note). OP moment zero = the physical statics (no OP moment about the pivot). The OP-moment residue is an "
         "MF observation (report 9B.3); the as-found value carries the non-physical couple and the estimates rest on an ASSUMED transfer, so the "
         "GOVERNING value [DERIVED] is the larger of the as-found value and the estimates (lead 22:54:03Z; L1 global: OP moment zero, through "
         "pose_neutral_v352r3R3's EA steps, ASSUMED; R3 pose: both estimates), per hole and component; ! = an estimate governs by 0.5 N or more.", "",
         "| case | model | max screw shear N, as found (hole) | moment-free estimate (hole) | OP moment zero (hole) | governing [DERIVED] (hole, by) | "
         "max pull-out N: as found / estimate / zero / governing |",
         "|---|---|---|---|---|---|---|"]
    for c in res["cases"]:
        v, gv = c["variants"], c["governing"]
        tc = v.get("tc09_removed")
        bang = lambda q, h: " !" if gv["per_hole"][h][q]["value"] - gv["per_hole"][h][q]["as_found"] >= 0.5 else ""
        L.append(f"| {c['case']} | {c['model']} | {v['as_found']['max_shear_N']:.0f} ({v['as_found']['hole']}) | "
                 + (f"{tc['max_shear_N']:.0f} ({tc['hole']})" if tc else "n/a (L1 mesh)") + f" | {v['op_zero']['max_shear_N']:.0f} ({v['op_zero']['hole']}) | "
                 f"**{gv['max_shear_N']:.0f}**{bang('max_shear_N', gv['hole'])} ({gv['hole']}, {gv['by'].replace('_', ' ')}) | "
                 f"{v['as_found']['max_pullout_N']:.0f} / " + (f"{tc['max_pullout_N']:.0f}" if tc else "n/a") + f" / {v['op_zero']['max_pullout_N']:.0f} / "
                 f"**{gv['max_pullout_N']:.0f}**{bang('max_pullout_N', gv['pullout_hole'])} |")
    L += ["", f"Governing cells (every case, hole and component): {json.dumps(res['governing_counts'])}.", "",
          "Governing per hole [DERIVED], max screw shear / max pull-out N (! = an estimate governs by 0.5 N or more):", ""]
    holes = sorted(IE.HF)
    L.append("| case | " + " | ".join(holes) + " |")
    L.append("|---|" + "---|" * len(holes))
    for c in res["cases"]:
        g = c["governing"]["per_hole"]
        mk = lambda h, q: f"{g[h][q]['value']:.0f}" + ("!" if g[h][q]["value"] - g[h][q]["as_found"] >= 0.5 else "")
        L.append(f"| {c['case'].split(' (')[0]} | " + " | ".join(f"{mk(h, 'max_shear_N')} / {mk(h, 'max_pullout_N')}" for h in holes) + " |")
    L += ["", "Per hole, max screw shear N: as found / moment-free estimate / OP moment zero (L1 global cases: as found / zero).", ""]
    holes = sorted(IE.HF)
    L.append("| case | " + " | ".join(holes) + " |")
    L.append("|---|" + "---|" * len(holes))
    for c in res["cases"]:
        v = c["variants"]
        cells = []
        for h in holes:
            a = v["as_found"]["per_hole_max_shear_N"].get(h)
            z = v["op_zero"]["per_hole_max_shear_N"].get(h)
            t = v["tc09_removed"]["per_hole_max_shear_N"].get(h) if "tc09_removed" in v else None
            cells.append(f"{a:.0f} / {t:.0f} / {z:.0f}" if t is not None else f"{a:.0f} / {z:.0f}")
        L.append(f"| {c['case'].split(' (')[0]} | " + " | ".join(cells) + " |")
    L += ["", "Checks: " + json.dumps({"cones": res["checks"]["cones_unit_rods"], "lc3": res["checks"]["lc3"]}, default=float)[:3000]]
    OUTM.write_text("\n".join(L) + "\n")
    print(f"[{time.time() - t0:6.1f} s] wrote {OUTJ.name} {sha16(OUTJ)}, {OUTM.name} {sha16(OUTM)}", flush=True)


if __name__ == "__main__":
    main()
