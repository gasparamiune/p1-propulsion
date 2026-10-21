"""Engine mounting data, v3.5.2 re-check with RM2-11 folded (fea3d 2026-10-20; brief item 6, REV-MECH-2 RM2-11, CHANGELOG 234).

Per-hole screw shear / axial / pull-out / push-in envelopes and ring resultants of the 16 airframe holes (GM-09 forward ring z +27,
GM-10 aft ring z -94.8; 8 radial M5 each), from the solved unit-step reactions (ccx RF totals of the 16 hole node sets in each run's f1.dat)
re-combined with every sub-case of the posted cases (SIM; same combination as icd_export.py, which wrote the v3.5.1 tables).  This script
does not rebuild the FE model (it reads model.json for the step list and f1.dat for the reactions only).

RM2-11 (REV-MECH-2, NOTE) folded:
  * header: the forces include the FE model mass (v3.5.1 c71 4.10307 kg = engine 2.88625 + ring 0.21701 + fixed 0.97058 + horns 0.02923;
    v3.5.2 L1 4.03255 kg, rev-3 R3 pose model 4.02989 kg) and exclude the airframe-wall equipment (massprops wet fixed group minus the
    model's fixed group: 1.30992 kg v3.5.1, 1.30993 kg v3.5.2);
  * sub-cases: FA1Q / FA1D / FA1U / FA1S are pressure only; the LC2F envelope is its thrust-only sub-case (GZ 0 bounds: inertia opposes
    thrust);
  * rigid vs compliant airframe: the rigid airframe bounds the maximum hole load but not every hole -> the datasheet per-hole rows are the
    ENVELOPE of the rigid and the compliant airframe; the compliant runs cover LC1 (B1_21.65) and LC3 at stop045 only (the coverage is
    stated in the table).  The v3.5.2 model has no compliant run: its datasheet rows are the envelope of the v3.5.2 rigid rows and the
    v3.5.1 compliant rows (carried, marked 'c351'; model mass 4.103 vs 4.030 kg, OP net 202.925 vs 202.50 N/MPa).
v3.5.2 OP-moment residue (MF, report 9B.3; lead 22:24:34Z / 22:54:03Z): the datasheet rows are the GOVERNING values [DERIVED] = the
larger of the as-found value (SIM, kept beside them) and the moment-free estimate of scripts/icd_momentfree_v352.py (read, not recomputed),
per hole and component, then enveloped with the carried v3.5.1 compliant rows; ring resultants likewise.  Extras: the v3.5.2 R3 K table at
the 8 stops (results/v352/k_table_r3_v352.json, read only) and the RM2-06 modal re-solve note (modal_ca2c_vs_ca2b_v352.json).
Sign: forces the ENGINE MODULE applies ON THE AIRFRAME; radial + = outward (screw pull-out); axial = +Z (forward);
shear = hypot(tangential, axial) in the radial screw; moments about the gimbal pivot (engine frame origin).
usage: FEA3D_CAD=v352 icd_export_v352.py -> results/v352/engine_mount_data_v352.json, results/v352/tables/engine_mount_data_v352.md"""
from __future__ import annotations
import sys, json, math, gzip, re, time, hashlib
from pathlib import Path
import numpy as np

ROOT = Path("/home/claude/work/fea3d")
RUNS, RES = ROOT / "runs", ROOT / "results"
OUTJ = RES / "v352" / "engine_mount_data_v352.json"
OUTM = RES / "v352" / "tables" / "engine_mount_data_v352.md"

sys.path.insert(0, str(ROOT / "scripts"))
import post_lc3 as PL      # noqa: E402  (PC_MAX, G_LAT, ALPHA: the LC3 sub-case coefficients, as icd_export.py)

STOPS = [f"stop{d:03d}" for d in range(0, 360, 45)]
CONES = ["neutral", "alpha+", "alpha-", "beta+", "beta-", "combined045", "combined135", "combined225", "combined315"]
F2C = (("GS", "F2 GS servo stall (9 cone poses)"), ("TD0", "F2 TD touchdown Pc 0"), ("TDP", "F2 TD touchdown Pc max"),
       ("LC6", "F2 LC6 hard landing 10 g"), ("LC2F", "F2 LC2F stuck pintle (thrust-only sub-case bounds)"))
MASS = {"v351": {"model_kg": 4.10307, "engine": 2.88625, "ring": 0.21701, "fixed": 0.97058, "horns": 0.02923, "excluded_kg": 1.30992,
                 "source": "runs/lc1v351_c71/mass.json (FE volume x density + point masses); massprops wet fixed 2.2805 kg"},
        "v352": {"model_kg": 4.03255, "model_kg_R3_pose": 4.02989, "engine": 2.82932, "engine_R3_pose": 2.82667, "ring": 0.21701,
                 "fixed": 0.95698, "horns": 0.02923, "excluded_kg": 1.30993,
                 "source": "runs/lc1v352g/mass.json, runs/pose_stop045_v352r3R3/mass.json; massprops v3.5.2 wet fixed 2.26691 kg"}}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def read_totals(sd):
    """(time, set, vector) of every '*NODE PRINT ... TOTALS=ONLY' block of f1.dat (or f1.dat.gz)."""
    p = sd / "f1.dat"
    txt = (p.read_text(errors="replace") if p.exists() else gzip.open(sd / "f1.dat.gz", "rt", errors="replace").read()).splitlines()
    out, k = [], 0
    while k < len(txt):
        m = re.match(r"\s*total force \(fx,fy,fz\) for set (\S+) and time\s+([0-9.Ee+-]+)", txt[k])
        if m:
            out.append((float(m.group(2)), m.group(1), np.asarray([float(x) for x in txt[k + 2].split()])))
            k += 3
            continue
        k += 1
    return out


def reactions(run, state):
    steps = json.loads((RUNS / run / "model.json").read_text())["steps"]
    rf = {}
    for t, st, v in read_totals(RUNS / run / state):
        rf.setdefault(steps[int(round(t)) - 1], {})[st] = v
    return rf


def combine(RF, co):
    any_st = next(iter(RF))
    base = RF["TH"] if "TH" in RF else {s: np.zeros(3) for s in RF[any_st]}
    res = {}
    for s in base:
        v = base[s].copy()
        for st, c in co.items():
            if c:
                v = v + c * (RF[st][s] - base[s])
        res[s] = v
    return res


def hole_frames():
    out = {}
    for ring, z, s0, s1 in (("GM-09", 27.0, 58.6, 69.9), ("GM-10", -94.8, 40.0, 75.0)):
        for k in range(8):
            phi = math.radians(22.5 + 45 * k)
            er = np.array([math.cos(phi), math.sin(phi), 0.0])
            et = np.array([-math.sin(phi), math.cos(phi), 0.0])
            out[f"AF_{ring.replace('-', '')}_{k}"] = (er * 0.5 * (s0 + s1) + np.array([0, 0, z]), er, et)
    return out


HF = hole_frames()


def lc3_coefs(js):
    psi = math.radians(js["psi_ang_deg"])
    return [{"OP": PL.PC_MAX, "GX": PL.G_LAT * math.cos(math.radians(i_["lat_dir_deg"])), "GY": PL.G_LAT * math.sin(math.radians(i_["lat_dir_deg"])),
             "GZ": i_["GZ_g"], "EAX": i_["ang_sign"] * PL.ALPHA * math.cos(psi), "EAY": i_["ang_sign"] * PL.ALPHA * math.sin(psi), "BUMP": i_["fb_N"]}
            for i_ in js["subcases"]]


def jl(p):
    return json.loads(Path(p).read_text())


def f1_items(post, run, cases_key, states=None):
    if not post.exists():
        return None
    d = jl(post)
    return [(run, st, sd["cases"][cases_key]["subcases"]) for st, sd in d["states"].items()
            if (states is None or st in states) and cases_key in sd["cases"]]


BURN = ["B1_21.65", "B1_19", "B1_2", "B1_1"]


def sources(model):
    """[(group, case label, airframe, items or None (pending), source posts)]; items = [(run, state, [coef dicts])]"""
    S = []
    if model == "v351":
        S.append(("LC1", "LC1", "rigid", f1_items(RES / "f1_post_lc1v351_c71.json", "lc1v351_c71", "LC1"), ["results/f1_post_lc1v351_c71.json"]))
        S.append(("LC1", "LC1", "compliant", f1_items(RES / "f1_post_lc1v351_compliant_c71.json", "lc1v351_compliant_c71", "LC1"),
                  ["results/f1_post_lc1v351_compliant_c71.json"]))
        fa = RES / "f1_post_fa1_c71.json"
        for c in ("FA1Q", "FA1S", "FA1T"):
            S.append((c, c, "rigid", f1_items(fa, "fa1_c71", c), ["results/f1_post_fa1_c71.json"]))
        stops = [(f"pose_{s}_c71", RES / f"f1_post_lc3_pose_{s}_c71.json") for s in STOPS]
        S.append(("LC3", "LC3 (8 stop poses, runaway / hold)", "rigid", [(r, "B1_21.65", lc3_coefs(jl(p))) for r, p in stops],
                  [str(p.relative_to(ROOT)) for _, p in stops]))
        p = RES / "f1_post_lc3_pose_stop045_compliant_c71.json"
        S.append(("LC3", "LC3 stop045 only", "compliant", [("pose_stop045_compliant_c71", "B1_21.65", lc3_coefs(jl(p)))], [str(p.relative_to(ROOT))]))
        cones = {c: RES / f"s3d_pose_{c}_c71.json" for c in CONES}
        for c, lab in F2C:
            S.append((c, lab, "rigid", [(f"pose_{q}_c71", "B1_21.65", jl(f)["cases"][c]["subcase_coefs"]) for q, f in cones.items()],
                      [str(f.relative_to(ROOT)) for f in cones.values()]))
        return S
    # v3.5.2 (rigid airframe only; GVLO and GVHI thermal bounds both enveloped for LC1 / LC2)
    for c in ("LC1", "LC2"):
        it, src = [], []
        for run in ("lc1v352g", "lc1v352h"):
            x = f1_items(RES / f"f1_post_{run}.json", run, c, BURN)
            if x:
                it += x
                src.append(f"results/f1_post_{run}.json")
        miss = [r for r in ("lc1v352g", "lc1v352h") if not (RES / f"f1_post_{r}.json").exists()]
        S.append((c, c + (" (GVLO + GVHI)" if not miss else f" (pending {', '.join(miss)})"), "rigid", it or None, src))
    fa = RES / "f1_post_fa1v352n.json"
    for c in ("FA1Q", "FA1D", "FA1U", "FA1S", "FA1T"):
        S.append((c, c, "rigid", f1_items(fa, "fa1v352n", c), ["results/f1_post_fa1v352n.json"]))
    have = [(f"pose_{s}_v352r3R3", RES / f"f1_post_lc3_pose_{s}_v352r3R3.json") for s in STOPS]
    ok = [(r, p) for r, p in have if p.exists()]
    S.append(("LC3", f"LC3 (stop poses at R3: {len(ok)} of 8)", "rigid", [(r, "B1_21.65", lc3_coefs(jl(p))) for r, p in ok] or None,
              [str(p.relative_to(ROOT)) for _, p in ok]))
    cones = {c: RES / f"s3d_pose_{c}_v352r3R3.json" for c in CONES}
    okc = {c: f for c, f in cones.items() if f.exists()}
    for c, lab in F2C:
        S.append((c, f"{lab.split(' (')[0]} (cone poses at R3: {len(okc)} of 9)", "rigid",
                  [(f"pose_{q}_v352r3R3", "B1_21.65", jl(f)["cases"][c]["subcase_coefs"]) for q, f in okc.items()] or None,
                  [str(f.relative_to(ROOT)) for f in okc.values()]))
    return S


def envelope(items, rf_cache):
    holes, rings, tot, n = {}, {}, {"F": np.zeros(3), "M": np.zeros(3)}, 0
    for run, st, subs in items:
        key = (run, st)
        if key not in rf_cache:
            rf_cache[key] = reactions(run, st)
        RF = rf_cache[key]
        for co in subs:
            rf = combine(RF, co)
            n += 1
            acc = {"GM09": [np.zeros(3), np.zeros(3)], "GM10": [np.zeros(3), np.zeros(3)]}
            Ft, Mt = np.zeros(3), np.zeros(3)
            for lab, v in rf.items():
                if lab not in HF:
                    continue
                x, er, et = HF[lab]
                L = -np.asarray(v)
                sh = math.hypot(L @ et, L[2])
                h = holes.setdefault(lab, {"x_mm": [round(float(c), 2) for c in x], "max_shear_N": 0.0, "max_abs_axial_N": 0.0,
                                           "max_abs_tangential_N": 0.0, "max_pullout_N": 0.0, "max_pushin_N": 0.0, "max_resultant_N": 0.0,
                                           "at_max_shear": None})
                if sh > h["max_shear_N"]:
                    h["at_max_shear"] = f"{run} {st}"
                h["max_shear_N"] = max(h["max_shear_N"], sh)
                h["max_abs_axial_N"] = max(h["max_abs_axial_N"], abs(float(L[2])))
                h["max_abs_tangential_N"] = max(h["max_abs_tangential_N"], abs(float(L @ et)))
                h["max_pullout_N"] = max(h["max_pullout_N"], float(L @ er))
                h["max_pushin_N"] = max(h["max_pushin_N"], -float(L @ er))
                h["max_resultant_N"] = max(h["max_resultant_N"], float(np.linalg.norm(L)))
                g = "GM09" if "GM09" in lab else "GM10"
                acc[g][0] += L
                acc[g][1] += np.cross(x, L)
                Ft += L
                Mt += np.cross(x, L)
            for g, (F, Mm) in acc.items():
                e = rings.setdefault(g, {"max_abs_F_N": np.zeros(3), "max_lateral_F_N": 0.0, "max_abs_M_Nmm": np.zeros(3), "max_lateral_M_Nmm": 0.0})
                e["max_abs_F_N"] = np.maximum(e["max_abs_F_N"], np.abs(F))
                e["max_lateral_F_N"] = max(e["max_lateral_F_N"], float(np.hypot(F[0], F[1])))
                e["max_abs_M_Nmm"] = np.maximum(e["max_abs_M_Nmm"], np.abs(Mm))
                e["max_lateral_M_Nmm"] = max(e["max_lateral_M_Nmm"], float(np.hypot(Mm[0], Mm[1])))
            tot["F"] = np.maximum(tot["F"], np.abs(Ft))
            tot["M"] = np.maximum(tot["M"], np.abs(Mt))
    return {"n_subcases": n, "holes": holes,
            "rings": {g: {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in e.items()} for g, e in rings.items()},
            "total_on_airframe": {"max_abs_F_N": tot["F"].tolist(), "max_abs_M_Nmm": tot["M"].tolist()}}


Q = ("max_shear_N", "max_abs_axial_N", "max_abs_tangential_N", "max_pullout_N", "max_pushin_N", "max_resultant_N")


def env_rows(groups):
    """groups: {group: [(label, airframe, model_tag, env or None)]} -> per group, per hole: envelope over its entries + which entry governs."""
    out = {}
    for g, entries in groups.items():
        live = [(lab, af, tag, e) for lab, af, tag, e in entries if e]
        if not live:
            continue
        rows = {}
        for h in sorted(HF):
            r = {"x_mm": [round(float(c), 2) for c in HF[h][0]]}
            for q in Q:
                vals = [(e["holes"][h][q], f"{af}{'' if tag == 'own' else ' ' + tag}") for _, af, tag, e in live if h in e["holes"]]
                v, by = max(vals)
                r[q] = round(v, 1)
                r[q + "_by"] = by
                rig = [x for x, b in vals if b == "rigid"]
                if rig and len(vals) > 1 and v > max(rig) + max(1.0, 0.05 * max(rig)):      # noise filter: > 1 N and > 5 %
                    r.setdefault("compliant_above_rigid", {})[q] = {"compliant": round(v, 1), "rigid": round(max(rig), 1)}
            rows[h] = r
        out[g] = {"entries": [f"{lab} [{af}{'' if tag == 'own' else ', ' + tag}] ({e['n_subcases']} sub-cases)" for lab, af, tag, e in live], "holes": rows}
    return out


def main():
    rf_cache = {}
    res = {"doc": __doc__.split("usage:")[0].strip(), "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "mass": MASS, "models": {}}
    for model in ("v351", "v352"):
        cases = []
        for grp, lab, af, items, src in sources(model):
            e = envelope(items, rf_cache) if items else None
            cases.append({"group": grp, "case": lab, "airframe": af, "pending": e is None, "sources": src,
                          "runs": sorted({r for r, _, _ in items}) if items else [], **(e or {})})
            print(f"[mount {model}] {lab} ({af}): " + (f"{e['n_subcases']} sub-cases, max shear {max(h['max_shear_N'] for h in e['holes'].values()):.1f} N"
                                                      if e else "PENDING"), flush=True)
        res["models"][model] = {"cases": cases}
    # per-hole envelopes (RM2-11): v3.5.1 = rigid u compliant (own model); v3.5.2 datasheet = v3.5.2 rigid u v3.5.1 compliant (carried)
    c351 = {c["group"]: c for c in res["models"]["v351"]["cases"] if c["airframe"] == "compliant"}
    g351, g352 = {}, {}
    for c in res["models"]["v351"]["cases"]:
        g351.setdefault(c["group"], []).append((c["case"], c["airframe"], "own", None if c["pending"] else c))
    for c in res["models"]["v352"]["cases"]:
        g352.setdefault(c["group"], []).append((c["case"], c["airframe"], "own", None if c["pending"] else c))
    for g, c in c351.items():
        if g in g352:
            g352[g].append((c["case"] + " (v3.5.1 model)", "compliant", "c351", c))
    res["envelope_v351_rigid_u_compliant"] = env_rows(g351)
    res["envelope_v352_datasheet"] = env_rows(g352)
    # lead 22:54:03Z: every v3.5.2 datasheet hole-load row is GOVERNED by the larger of the as-found value and the moment-free estimate
    # (DERIVED; scripts/icd_momentfree_v352.py 'governing', per hole and component; read here, not recomputed), then enveloped with the
    # carried v3.5.1 compliant rows as before.  The as-found envelope above stays in the JSON and the table file beside it.
    mfp = RES / "v352" / "icd_momentfree_v352.json"
    MF = jl(mfp) if mfp.exists() else None
    if MF and all("governing" in c for c in MF["cases"]):
        E, gov = res["envelope_v352_datasheet"], {}
        for c in MF["cases"]:
            g = c["group"]
            if g not in E:
                continue
            comp = [e for _, af, tag, e in g352[g] if e and tag == "c351"]
            rows = {}
            for h in sorted(HF):
                gp_h, r = c["governing"]["per_hole"][h], {"x_mm": E[g]["holes"][h]["x_mm"]}
                for q in Q:
                    gp = gp_h[q]
                    cv = max((e["holes"][h][q] for e in comp if h in e["holes"]), default=None)
                    if cv is not None and cv > gp["value"]:
                        r[q], r[q + "_by"] = round(cv, 1), "compliant c351"
                    else:
                        r[q], r[q + "_by"] = round(gp["value"], 1), ("rigid as found" if gp["by"] == "as_found" else f"rigid estimate {gp['by']}")
                    r[q + "_as_found_rigid"] = round(gp["as_found"], 1)
                    r[q + "_as_found_datasheet"] = E[g]["holes"][h][q]
                    r[q + "_estimate_governs"] = bool(r[q + "_by"].startswith("rigid estimate") and gp["value"] - gp["as_found"] >= 0.5)
                    if cv is not None and cv > gp["value"] + max(1.0, 0.05 * gp["value"]):           # same noise filter as env_rows
                        r.setdefault("compliant_above_rigid", {})[q] = {"compliant": round(cv, 1), "rigid": round(gp["value"], 1)}
                rows[h] = r
            gov[g] = {"case": c["case"], "model": c["model"], "tag": "DERIVED", "estimates": c["governing"]["estimates"], "note": c["governing"]["note"],
                      "entries": E[g]["entries"], "holes": rows, "rings_rigid": c["governing"]["rings"], "total_on_airframe_rigid": c["governing"]["total_on_airframe"]}
        res["datasheet_v352_governing"] = {"rule": "lead 22:54:03Z: governing = the larger of the as-found value and the moment-free estimate "
                                           "(L1 global: OP moment zero through pose_neutral_v352r3R3's EA steps, ASSUMED; R3 pose: the two-face estimate and "
                                           "OP moment zero), per hole and component, then enveloped with the carried v3.5.1 compliant rows; DERIVED",
                                           "source": "results/v352/icd_momentfree_v352.json " + sha16(mfp), "groups": gov}
    OUTJ.write_text(json.dumps(res, indent=1, default=float))
    # markdown
    L = ["# Engine mounting data (datasheet), v3.5.2 re-check with RM2-11 folded", "",
         f"Generated {res['date']} by scripts/icd_export_v352.py from the f1.dat reaction totals of the listed runs (SIM unless tagged). "
         "16 radial M5 holes: GM-09 forward ring z +27 mm, GM-10 aft ring z -94.8 mm. Forces of the engine module ON the airframe; radial + = pull-out; "
         "shear = hypot(tangential, axial) in the radial screw.", "",
         "**Header (RM2-11).**",
         f"- Included mass: the forces include the FE model mass. v3.5.1 model (c71): **4.103 kg** (engine 2.886, ring 0.217, fixed 0.971, horns 0.029 kg). "
         f"v3.5.2 model: **4.033 kg** L1 (engine 2.829) / **4.030 kg** rev-3 R3 pose model (engine 2.827); ring 0.217, fixed 0.957, horns 0.029 kg [DERIVED, mass.json].",
         "- Excluded: **1.31 kg** of airframe-wall equipment (massprops wet fixed group minus the model's fixed group: 2.2805 - 0.9706 = 1.3099 kg v3.5.1; "
         "2.2669 - 0.9570 = 1.3099 kg v3.5.2). Its inertia loads go into the airframe wall directly, not through these 16 holes.",
         "- Sub-cases: FA1Q / FA1D / FA1U / FA1S are pressure only (no inertia). The LC2F envelope (908 N) is its thrust-only sub-case: GZ 0 bounds, "
         "because inertia opposes thrust.",
         "- Rigid against compliant airframe: the rigid airframe bounds the maximum hole load, but not every hole. The per-hole datasheet rows are the "
         "ENVELOPE of the rigid and the compliant airframe (k_af 2e3 / 2e4 / 2e4 N/mm, ASSUMED). Compliant coverage: LC1 at B1_21.65 (lc1v351_compliant_c71) "
         "and LC3 at stop045 only (pose_stop045_compliant_c71); every other case and pose is rigid only.",
         "- v3.5.2: no compliant run. The v3.5.2 datasheet rows are the envelope of the v3.5.2 rigid rows and the v3.5.1 compliant rows "
         "(carried, marked c351; model mass 4.103 vs 4.030 kg, OP net 202.925 vs 202.50 N/MPa).", ""]
    GV = res.get("datasheet_v352_governing")
    if GV:
        G = GV["groups"]
        L += ["## v3.5.2 model: DATASHEET per-hole values, governing [DERIVED] (lead 22:54:03Z)", "",
              "Governing = the larger of the as-found value (SIM, the table further down) and the moment-free estimate (section 'OP-moment residue' "
              "below), per hole and component, then enveloped with the carried v3.5.1 compliant rows (c351) as before. The as-found value carries "
              "a non-physical OP couple; the estimate rests on an ASSUMED transfer (the residue as the rod-force pair it produces, hole reactions "
              "from the EAX / EAY unit steps). LC1 / LC2 / FA-1 (L1 global): estimate = OP moment zero, transferred through pose_neutral_v352r3R3's "
              "EA steps (ASSUMED). LC3 / F2 (R3 poses): both estimates (two TC-09 faces at p/Pc 1.0; OP moment zero), so the governing value bounds "
              "every value shown. Pull-out, axial and the other components follow the same rule.", "",
              "Cell = max shear / max |axial| / max pull-out, N; ! = an estimate governs that value by 0.5 N or more; * = a compliant-airframe value "
              "exceeds the rigid governing one by more than 1 N and 5 %.", ""]
        gs = list(G)
        L += ["| hole (x, y, z mm) | " + " | ".join(gs) + " |", "|---|" + "---|" * len(gs)]
        for h in sorted(HF):
            x = HF[h][0]
            cells = []
            for g in gs:
                r = G[g]["holes"][h]
                f = lambda q: f"{r[q]:.0f}" + ("!" if r[q + "_estimate_governs"] else "")
                cells.append(f"{f('max_shear_N')} / {f('max_abs_axial_N')} / {f('max_pullout_N')}" + (" *" if r.get("compliant_above_rigid") else ""))
            L.append(f"| {h} ({x[0]:.1f}, {x[1]:.1f}, {x[2]:.1f}) | " + " | ".join(cells) + " |")
        L.append("")
        for g in gs:
            n_bang = sum(int(r[q + "_estimate_governs"]) for r in G[g]["holes"].values() for q in Q)
            L.append(f"- {g}: {G[g]['case']} ({G[g]['model']}; estimate {' + '.join(G[g]['estimates'])}; {G[g]['note']}): "
                     f"{n_bang} of {len(G[g]['holes']) * len(Q)} hole values governed by the estimate")
            ab = [(h, r["compliant_above_rigid"]) for h, r in G[g]["holes"].items() if r.get("compliant_above_rigid")]
            if ab:
                L.append("  - compliant above rigid governing: " + "; ".join(f"{h} " + ", ".join(f"{q.replace('max_', '').replace('_N', '')} {v['compliant']:.0f} vs {v['rigid']:.0f}"
                                                                                                  for q, v in d.items()) for h, d in ab))
        L.append("")
    for title, key in (("v3.5.2 model: AS FOUND per-hole envelope (SIM; v3.5.2 rigid u v3.5.1 compliant, carried)" +
                        ("; the governing table above is the datasheet (lead 22:54:03Z)" if GV else ""), "envelope_v352_datasheet"),
                       ("v3.5.1 model: per-hole envelope of the rigid and the compliant airframe (RM2-11; restates tables/engine_mount_data_v351.md)",
                        "envelope_v351_rigid_u_compliant")):
        E = res[key]
        L += [f"## {title}", "", "Cell = max shear / max |axial| / max pull-out, N; * = a compliant-airframe value exceeds the rigid one at that hole "
              "by more than 1 N and 5 % (listed under the table).", ""]
        gs = list(E)
        L += ["| hole (x, y, z mm) | " + " | ".join(gs) + " |", "|---|" + "---|" * len(gs)]
        for h in sorted(HF):
            x = HF[h][0]
            cells = []
            for g in gs:
                r = E[g]["holes"][h]
                cells.append(f"{r['max_shear_N']:.0f} / {r['max_abs_axial_N']:.0f} / {r['max_pullout_N']:.0f}" + (" *" if r.get("compliant_above_rigid") else ""))
            L.append(f"| {h} ({x[0]:.1f}, {x[1]:.1f}, {x[2]:.1f}) | " + " | ".join(cells) + " |")
        L.append("")
        for g in gs:
            L.append(f"- {g}: " + "; ".join(E[g]["entries"]))
            ab = [(h, r["compliant_above_rigid"]) for h, r in E[g]["holes"].items() if r.get("compliant_above_rigid")]
            if ab:
                L.append("  - compliant above rigid: " + "; ".join(f"{h} " + ", ".join(f"{q.replace('max_', '').replace('_N', '')} {v['compliant']:.0f} vs {v['rigid']:.0f}"
                                                                                       for q, v in d.items()) for h, d in ab))
        L.append("")
    # lead 22:24:34Z: the OP-moment residue (MF observation, report 9B.3) quoted as found, with the moment-free estimate beside each affected
    # row (scripts/icd_momentfree_v352.py: superposition of the posted unit steps, DERIVED; read here if present, not recomputed)
    mfp = RES / "v352" / "icd_momentfree_v352.json"
    if mfp.exists():
        MF = jl(mfp)
        res["op_moment_residue_estimate"] = "results/v352/icd_momentfree_v352.json " + sha16(mfp)
        L += ["## v3.5.2: OP-moment residue (MF observation, lead 22:24:34Z): the moment-free estimate beside each affected row", "",
              "The as-found rows (SIM) stand as found; the datasheet rows are the governing values [DERIVED] (lead 22:54:03Z: the larger of the "
              "as-found value and the estimate, table at the top). The OP unit step of the v3.5.2 models carries a moment about the pivot that the physical load "
              "does not have (closed cavity, axisymmetric exit): in the R3 pose runs (LC3, F2) a couple of about 1.56 N m/MPa from two one-sided "
              "TC-09 aft-boundary faces (elements 24664 / 23610 at p/Pc 0.75), within a total of about 2.3 N m/MPa; in the L1 global runs (LC1, LC2, "
              "FA-1) 0.72 N m/MPa. The rods carry it to the airframe as a rod-force pair. Estimates [DERIVED, superposition of the posted unit steps "
              "through the EAX / EAY steps; ASSUMED transmission as a pure couple; the L1 global runs use pose_neutral_v352r3R3's EA steps]: "
              "'moment-free' = the two TC-09 faces at p/Pc 1.0 (R3 runs); 'OP moment zero' = the physical statics. Not proven conservative for "
              "every hole: where an estimate is ABOVE the as-found value it is marked !.", "",
              "| case | max screw shear N as found (hole) | moment-free estimate (hole) | OP moment zero (hole) | governing [DERIVED] (hole, by) | "
              "max pull-out N as found / estimate / zero / governing |",
              "|---|---|---|---|---|---|"]
        for c in MF["cases"]:
            v, gv = c["variants"], c.get("governing")
            a, z, t = v["as_found"], v["op_zero"], v.get("tc09_removed")
            mk = lambda x: (" !" if x["max_shear_N"] > a["max_shear_N"] + 0.5 else "")
            mp = lambda x: (" !" if x["max_pullout_N"] > a["max_pullout_N"] + 0.5 else "")
            L.append(f"| {c['case']} | {a['max_shear_N']:.0f} ({a['hole']}) | " + (f"{t['max_shear_N']:.0f} ({t['hole']}){mk(t)}" if t else "n/a (L1 mesh)")
                     + f" | {z['max_shear_N']:.0f} ({z['hole']}){mk(z)} | "
                     + (f"**{gv['max_shear_N']:.0f}**{mk(gv)} ({gv['hole']}, {gv['by'].replace('_', ' ')})" if gv else "-")
                     + f" | {a['max_pullout_N']:.0f} / " + (f"{t['max_pullout_N']:.0f}" if t else "n/a")
                     + f" / {z['max_pullout_N']:.0f} / " + (f"**{gv['max_pullout_N']:.0f}**{mp(gv)}" if gv else "-") + " |")
        L += ["", "Per hole, max screw shear N where an estimate differs from the as-found value by more than 1 N "
              "(as found / moment-free estimate / OP moment zero; L1 global cases as found / zero):", ""]
        for c in MF["cases"]:
            v = c["variants"]
            ch = []
            for h in sorted(HF):
                a = v["as_found"]["per_hole_max_shear_N"].get(h)
                z = v["op_zero"]["per_hole_max_shear_N"].get(h)
                t = v["tc09_removed"]["per_hole_max_shear_N"].get(h) if "tc09_removed" in v else None
                if a is None or z is None:
                    continue
                if abs(z - a) > 1.0 or (t is not None and abs(t - a) > 1.0):
                    ch.append(f"{h} {a:.0f} / {t:.0f} / {z:.0f}" if t is not None else f"{h} {a:.0f} / {z:.0f}")
            L.append(f"- {c['case']}: " + ("; ".join(ch) if ch else "no hole changes by more than 1 N"))
        L.append("")
    for model in ("v351", "v352"):
        L += [f"## Ring resultants, {model} model (envelope over the sub-cases): max |Fx|, |Fy|, |Fz| N; max lateral |F| N; max |M| about the pivot N m", "",
              "| case | airframe | GM-09 ring F | GM-09 lat | GM-09 M | GM-10 ring F | GM-10 lat | GM-10 M | total F | total M |", "|---|---|---|---|---|---|---|---|---|---|"]
        for c in res["models"][model]["cases"]:
            if c["pending"]:
                L.append(f"| {c['case']} | {c['airframe']} | pending | | | | | | | |")
                continue
            r9, r10, t = c["rings"]["GM09"], c["rings"]["GM10"], c["total_on_airframe"]
            fm = lambda v: ", ".join(f"{x:.0f}" for x in v)
            mm = lambda v: ", ".join(f"{x / 1e3:.2f}" for x in v)
            L.append(f"| {c['case']} | {c['airframe']} | {fm(r9['max_abs_F_N'])} | {r9['max_lateral_F_N']:.0f} | {mm(r9['max_abs_M_Nmm'])} | "
                     f"{fm(r10['max_abs_F_N'])} | {r10['max_lateral_F_N']:.0f} | {mm(r10['max_abs_M_Nmm'])} | {fm(t['max_abs_F_N'])} | {mm(t['max_abs_M_Nmm'])} |")
        L.append("")
    if GV:
        L += ["## Ring resultants, v352 model, governing [DERIVED] (lead 22:54:03Z): rigid airframe, the larger of the as-found value and the "
              "estimate(s) per component; max |Fx|, |Fy|, |Fz| N; max lateral |F| N; max |M| about the pivot N m", "",
              "The as-found total moment of the L1 global cases (LC1, LC2, FA-1) is mostly the OP residue couple (0.72 N m/MPa); the governing "
              "value keeps it (the as-found value is the larger).", "",
              "| case | GM-09 ring F | GM-09 lat | GM-09 M | GM-10 ring F | GM-10 lat | GM-10 M | total F | total M |", "|---|---|---|---|---|---|---|---|---|"]
        for g, G_ in GV["groups"].items():
            r9, r10, t = G_["rings_rigid"]["GM09"], G_["rings_rigid"]["GM10"], G_["total_on_airframe_rigid"]
            fm = lambda v: ", ".join(f"{x:.0f}" for x in v)
            mm = lambda v: ", ".join(f"{x / 1e3:.2f}" for x in v)
            L.append(f"| {G_['case']} | {fm(r9['max_abs_F_N'])} | {r9['max_lateral_F_N']:.0f} | {mm(r9['max_abs_M_Nmm'])} | "
                     f"{fm(r10['max_abs_F_N'])} | {r10['max_lateral_F_N']:.0f} | {mm(r10['max_abs_M_Nmm'])} | {fm(t['max_abs_F_N'])} | {mm(t['max_abs_M_Nmm'])} |")
        L.append("")
    # 8.1 datasheet extras: K at the stop poses (RM2-05: r_eff per servo and pose; coupled and diagonal labelled) and the engine-mount
    # modes with the servo J (RM2-07)
    kr = RES / "k_range_v352.json"
    if kr.exists():
        K = jl(kr)
        L += ["## Gimbal-axis stiffness at the 8 deg stop poses (RM2-05 folded)", "",
              "N m/rad. FE = SIM unit steps EAX / EAY with the servo output rigid (CAD v3.5.1 c71 pose runs, asm v1.2: the v3.5.1-model F3; "
              "the v3.5.2 R3 values are in the next table; at stop045 they are 8-13 % stiffer with the servo rigid and 2-6 % with it in series, report section 9). With the servo = DERIVED: "
              "r_eff per servo and pose in series, k_s 58 / 174 N m/rad per servo (ASSUMED, TO-VERIFY B-TVC-1). coupled = 1 / C_jj (other axis "
              "moment-free; what a single-axis load measures); diagonal = (C^-1)_jj (other axis held at zero rotation). The v3.5.1 table used "
              "r_h 11.139 mm at every pose and is superseded.", "",
              "| pose (alpha, beta deg) | r_eff 1 / 2 mm | K_alpha FE coupled | K_alpha +58 coupled / diag | K_alpha +174 coupled / diag | "
              "K_beta FE coupled | K_beta +58 coupled / diag | K_beta +174 coupled / diag |", "|---|---|---|---|---|---|---|---|"]
        for r in K["rows"]:
            if not r["group"].startswith("stop (8 deg), rigid"):
                continue
            a, b = r["K_alpha"], r["K_beta"]
            L.append(f"| {r['run'].replace('pose_', '').replace('_c71', '')} ({r['pose_deg'][0]:+.2f}, {r['pose_deg'][1]:+.2f}) | "
                     f"{r['r_eff_mm'][0]:.2f} / {r['r_eff_mm'][1]:.2f} | {a['FE_coupled']:.0f} | {a['servo58_coupled']:.0f} / {a['servo58_diagonal']:.0f} | "
                     f"{a['servo174_coupled']:.0f} / {a['servo174_diagonal']:.0f} | {b['FE_coupled']:.0f} | {b['servo58_coupled']:.0f} / {b['servo58_diagonal']:.0f} | "
                     f"{b['servo174_coupled']:.0f} / {b['servo174_diagonal']:.0f} |")
        res["K_stop_source"] = "results/k_range_v352.json " + sha16(kr)
        L.append("")
    # v3.5.2 R3 model: the REV-GNC-7 K table (results/v352/k_table_r3_v352.json, lead 17:33:40Z / 18:40:44Z; read only), the 8 stop rows
    # here, the 17 poses with deltas and fractions in its own table file
    kt = RES / "v352" / "k_table_r3_v352.json"
    if kt.exists():
        KT = jl(kt)
        rows = {r["pose"]: r for r in KT["rows"]}
        rg = KT["range_over_posted_R3_poses"]
        fr = lambda q: f"{rg[q]['min']:.0f} ({rg[q]['min_pose']}) - {rg[q]['max']:.0f} ({rg[q]['max_pose']})"
        L += ["## Gimbal-axis stiffness at the 8 deg stop poses, v3.5.2 R3 model (REV-GNC-7 input)", "",
              f"N m/rad; SIM (FE unit steps EAX / EAY on the v3.5.2 R3 pose runs, rev-3 levers) + DERIVED (servo in series as above; k_s 58 / 174 "
              f"ASSUMED, TO-VERIFY B-TVC-1). Source results/v352/k_table_r3_v352.json {sha16(kt)} ({KT['n_posted']} of {KT['n_poses']} poses posted; "
              f"{KT['acceptance']}); all 17 poses with the v3.5.1 values, deltas and fractions: results/v352/tables/k_table_r3_v352.md. GNC sets its "
              "K band from the full R3 table (lead 17:33:40Z), not from stop045. Range over the 17 poses, coupled: K_alpha FE "
              f"{fr('FE_coupled_alpha')}, +58 {fr('k_s58_coupled_alpha')}, +174 {fr('k_s174_coupled_alpha')}; K_beta FE {fr('FE_coupled_beta')}, "
              f"+58 {fr('k_s58_coupled_beta')}, +174 {fr('k_s174_coupled_beta')}.", "",
              "| pose (alpha, beta deg) | K_alpha FE coupled / diag | K_alpha +58 coupled / diag | K_alpha +174 coupled / diag | "
              "K_beta FE coupled / diag | K_beta +58 coupled / diag | K_beta +174 coupled / diag |", "|---|---|---|---|---|---|---|"]
        for p in STOPS:
            r = rows.get(p)
            if not r or r.get("status") != "posted":
                L.append(f"| {p} | pending | | | | | |")
                continue
            v = lambda q: r["values"][q]["R3"]
            L.append(f"| {p} ({r['pose_deg'][0]:+.2f}, {r['pose_deg'][1]:+.2f}) | " + " | ".join(
                f"{v(f'{k}_coupled_{ax}'):.0f} / {v(f'{k}_diagonal_{ax}'):.0f}" for ax in ("alpha", "beta") for k in ("FE", "k_s58", "k_s174")) + " |")
        res["K_stop_source_v352_R3"] = "results/v352/k_table_r3_v352.json " + sha16(kt)
        L.append("")
    rk = RES / "v352" / "rocking_servo_J_v352.json"
    ms_ = RES / "modal_summary_v351.json"
    if rk.exists() and ms_.exists():
        R, MSm = jl(rk), jl(ms_)
        nb, na = R["neutral"]["beta"], R["neutral"]["alpha"]
        L += ["## First engine-mount modes (RM2-07 folded)", "",
              f"Coarsened all-L2 modal ({MSm['modal_run']}, CAD v3.5.1 model; SIM), rigid airframe holes. The loop-relevant rocking pair is the one WITH the "
              "servo in series AND the servo inertia J (rotor + gear train at the output shaft, added through the kinematic factor g = 23.04 at neutral; "
              "J nominal 1.6e-3, range 0.76-2.7e-3 kg m2, ASSUMED from the GNC SB-2292SG datasheet, TO-VERIFY B-TVC-1) [DERIVED]. The v3.5.1 "
              "'21-33 Hz with the servo in series' omitted J and is WITHDRAWN as the loop-relevant pair.", "",
              "| mode | f FE, servo rigid Hz | f at production K Hz | servo k_s 58: J nominal (J range) Hz | servo k_s 174: J nominal (J range) Hz |", "|---|---|---|---|---|"]
        for e, n in ((MSm["engine_mount_modes"][0], nb), (MSm["engine_mount_modes"][1], na)):
            L.append(f"| {e['description']} | {e['f_FE_rigid_servo_Hz']:.1f} | {e['f_scaled_to_pose_model_K_Hz']:.1f} | "
                     f"{n['k_s58']['J_nom']:.2f} ({n['k_s58']['J_high']:.2f}-{n['k_s58']['J_low']:.2f}) | {n['k_s174']['J_nom']:.2f} ({n['k_s174']['J_high']:.2f}-{n['k_s174']['J_low']:.2f}) |")
        for e in MSm["engine_mount_modes"][2:]:
            L.append(f"| {e['description']} | {e['f_FE_rigid_servo_Hz']:.1f} | - | - | - |")
        pr = R["pose_range_Hz"]
        L += ["", f"Over the 17 poses (lumped 2-DOF, r_eff per servo and pose): k_s 58 {pr['58']['J_nom'][0]:.1f}-{pr['58']['J_nom'][1]:.1f} Hz at J nominal; "
              f"k_s 174 {pr['174']['J_nom'][0]:.1f}-{pr['174']['J_nom'][1]:.1f} Hz; over the J range {min(pr['58']['J_high'][0], pr['174']['J_high'][0]):.1f}-"
              f"{max(pr['58']['J_low'][1], pr['174']['J_low'][1]):.1f} Hz. Neutral over the k_s and J ranges: {nb['k_s58']['J_high']:.1f}-{na['k_s174']['J_low']:.1f} Hz.", ""]
        res["modes_source"] = ["results/modal_summary_v351.json " + sha16(ms_), "results/v352/rocking_servo_J_v352.json " + sha16(rk)]
        mc = RES / "v352" / "modal_ca2c_vs_ca2b_v352.json"
        if mc.exists():          # RM2-06 re-solve on the corrected L2 mesh (report 9A): the first six modes against ca2b
            MC = jl(mc)
            m6 = [m for m in MC["modes"] if m["mode"] <= 6]
            L += [f"RM2-06 re-solve (modal_v351ca2c_c71, TC-01 OP loads mapped from L1; report 9A): modes 1-6 move by at most "
                  f"{max(abs(m['delta_pct']) for m in m6):.3f} % (MAC >= {min(m['MAC_same_index'] for m in m6):.4f}); the table stands "
                  f"[SIM; results/v352/modal_ca2c_vs_ca2b_v352.json {sha16(mc)}].", ""]
            res["modes_source"].append("results/v352/modal_ca2c_vs_ca2b_v352.json " + sha16(mc))
        OUTJ.write_text(json.dumps(res, indent=1, default=float))
    OUTM.write_text("\n".join(L) + "\n")
    print(f"wrote {OUTJ.relative_to(ROOT)} {sha16(OUTJ)}, {OUTM.relative_to(ROOT)} {sha16(OUTM)}", flush=True)


if __name__ == "__main__":
    main()
