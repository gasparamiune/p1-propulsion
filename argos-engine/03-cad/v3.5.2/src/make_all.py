"""CAD make-all: build, verify, export, BOM, mass properties, drawings, README (03-cad/src, v2 for CAD v3.5.1, 2026-10-13, Mechanical).

usage: make_all.py [--stages build,checks,parts,assembly,glb,bom,mass,drawings,readme] [--poses neutral,stop045] [--out DIR]

Stages (all by default):
  build     build.build(engine, gimbal, feed; config.V351_ON) with the pivot frozen at the v3.4.1 rev A mid-burn CG (z_head_mid).
  checks    BRepCheck validity of every part; boolean interference at neutral (all pairs) and, for relatively moving bodies, at every
            pose of build.pose_list (18: neutral, +/-7 deg per axis, 4 combined corners at 7 deg, the 8 deg conical stop in 8
            directions and toward the fixed hose end; the feed hose re-swept per pose from the linear frame shape); exact
            clearances < 3 mm between relatively moving bodies, classified per pair over all poses (v3.5.1); clearance of every
            instance to the 140 mm bay wall at every pose; v3.5.1 (lead 188 (2)): the signed per-instance bay-wall sweep of every
            moving group (72 directions x 0..8 deg incl. 7 and 8 deg + the stop polygon, pass r <= 69.0 mm) and the fixed-part
            on-the-bore check (r <= 70.0 mm unless whitelisted); swept envelope of the engine group.  --poses runs a subset and
            MERGES it into the existing checks file of the same build fingerprint (chunked runs under the 2 h task limit).
  parts     per part number: STEP (mm, +Z forward, the part's modelling frame; parts modelled in place carry engine-frame
            coordinates) with the repository round-trip method (re-import: every solid valid, same solid count, |dV|/V < 1e-5,
            bbox error < 0.01 mm; software verification, NOT a manufacturing tolerance) and STL (mm, linear deflection 0.05 mm).
  assembly  assembly STEP of every instance at neutral (names PN#i, colours by material) + re-import verification; a posed
            STEP at the 8 deg stop toward 45 deg (visual).
  glb       GLB in metres with +Y up: (x, y, z)_glTF = (x, z, -y)_engine / 1000 (proper rotation, det +1); one mesh per instance,
            material colours; read back and checked (node count, bounds against the STEP assembly within the tessellation
            deflection).
  bom       BOM_<ver>.csv/.json: one line per part number (sub-solids roll into their parent), qty, material, process, supplier,
            mass and its source, unit price TO-QUOTE with delivery to Sonderborg DK-6400 unless the part carries a dated price
            (no price is invented, no "from" offers), N2O-wetted flag (oxygen-clean), drawing file.
  mass      massprops_<ver>.json: groups engine / fixed / ring / horn / pushrod (hose split by its engine fraction), burn states
            wet / mid / burnout / nograin, mass, CG, inertia about the CG and about the pivot; per-part ledger.
  drawings  hidden-line projections (front = view along +Y, top = along -Z, side = along -X, iso) of every part with
            drawing=True: SVG + PDF (matplotlib) + DXF (ezdxf, mm, layer per view) with a title block, overall dimensions and
            the part's datum / fits / finish / heat-treatment notes.  DESIGN-MODEL drawings: not released for fabrication.
  readme    03-cad/README.md and 03-cad/properties.json (generator versions, sha256 of every source and output).
Every output is a DESIGN MODEL from the parameter set; geometric checks are software checks, not physical validation.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, sys, time, traceback
from pathlib import Path
# v3.4.1: single-threaded BLAS before numpy loads (the feed-route SLSQP plan is not reproducible with threaded BLAS; the baseline
# route comes from the frozen plan 03-cad/src/data/feed_plan_v341.json, this keeps any re-plan deterministic)
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
import numpy as np

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "04-fea" / "src"))
import cadquery as cq
import config
import build
import checks
import sweep
import engmat
from geom import apply, bbox, T_trans

# v3.5.2 (lead CHANGELOG 206 (2), 2026-10-13): MAKE_ALL_CAD=v352 selects config.V352_ON, data/hardware_v352.json and the v3.5.2 file names
# (mass-delta sensitivity for GNC P2); default v351 reproduces the frozen v3.5.1 run.
_MAKE_CAD = os.environ.get("MAKE_ALL_CAD", "v351")
assert _MAKE_CAD in ("v351", "v352"), _MAKE_CAD
CAD_VERSION = {"v351": "v3.5.1", "v352": "v3.5.2"}[_MAKE_CAD]
BUILD_OVERRIDES = {"v351": config.V351_ON, "v352": config.V352_ON}[_MAKE_CAD]
R_BAY = 70.0
DELIVERY = "Sonderborg, Denmark, DK-6400"
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def jdump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))


def solid_volume(shape):
    return sum(s.Volume() for s in shape.Solids())


def bounds_of(shape):
    """Exact (optimal) bounding box from the B-rep geometry, ignoring any triangulation and the shape tolerances.  v3.4.1: the cadquery
    BoundingBox used the triangulation when one existed (the in-memory part is meshed by the checks stage, the re-imported one is not),
    which failed ENG-EL-04 on a 0.012 mm tessellation difference (make_all v3.4.1 first run, kept in the log)."""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped, b, False, False)
    return list(b.Get())


# --------------------------------------------------------------------------------------------- build
def stage_build():
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=BUILD_OVERRIDES)
    log(f"build: {len(list(reg))} part numbers, {sum(p.qty for p in reg)} instances, {time.time() - t0:.1f} s, "
        f"z_head_mid {P['z_head_mid']['v'] * 1e3:.3f} mm")
    return P, S, reg, clog


# --------------------------------------------------------------------------------------------- checks
def build_fingerprint():
    """sha256/16 over the generator sources (src/*.py, src/data/*, 04-fea/src/engmat.py) and the build overrides: chunked check runs
    merge only into a checks file with the same fingerprint."""
    h = hashlib.sha256()
    for f in sorted(HERE.glob("*.py")) + sorted((HERE / "data").glob("*")) + [HERE.parents[1] / "04-fea" / "src" / "engmat.py"]:
        if f.is_file():
            h.update(f.name.encode())
            h.update(f.read_bytes())
    h.update(json.dumps(BUILD_OVERRIDES, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


# v3.5.1: dispositions of the < 3 mm pairs between relatively moving bodies (REV-MECH-1 freeze item "< 3 mm pairs classified").
# Classes over all poses: JOINT = both bodies belong to one kinematic joint (spherical bearing stack, horn joint); TIGHT = 0.3-1.0 mm
# with relative motion (tolerance stack on the drawings + feeler sweep at the stops, B-GM bench); OK = >= 1.0 mm; ACTION < 0.3 mm.
CLOSE_DISPOSITION = {
    ("ENG-GM-18", "ENG-HW-22"): "JOINT: lever-stud flange (7.5) next to the GE 5 E outer ring of the pushrod eye; the outer ring tilts with the "
                                "pushrod misalignment (demand in checks/tvc_joints, GE alpha 13 deg): gap closes to the listed minimum at the "
                                "extreme pose, no contact; drawing: flange diameter 7.5 -0.1 max",
    ("ENG-GM-19", "ENG-HW-22"): "JOINT: 1.5 mm spacer washer next to the GE outer ring (as GM-18): misalignment clearance, no contact",
    ("ENG-GM-20", "ENG-HW-22"): "JOINT: horn-joint shoulder screw head next to the GE outer ring of the pushrod upper eye",
    ("ENG-GM-15", "ENG-GM-20"): "TIGHT by design: horn-joint screw head 0.5 mm above the servo case top; the head moves in a plane parallel "
                                "to the case (horn rotation), so the gap is constant over the poses; tolerance stack (case top, spline seat, "
                                "horn thickness) TO-VERIFY on the received servo",
    ("ENG-GM-01", "ENG-GM-17"): "relative motion collar lever / pushrod: minimum at the listed pose; drawing tolerance stack TO-DO",
    ("ENG-GM-02", "ENG-GM-17"): "relative motion collar lever / pushrod: minimum at the listed pose; drawing tolerance stack TO-DO",
    ("ENG-GM-03", "ENG-GM-08"): "axial gap ring boss / post inner face on the outer (X) axis: rotation about that axis keeps it constant; "
                                "set by the thrust washer GM-07 stack",
    ("ENG-GM-01", "ENG-GM-03"): "collar half / ring: relative rotation about the inner (Y) axis",
    ("ENG-GM-02", "ENG-GM-03"): "collar half / ring: relative rotation about the inner (Y) axis",
    ("ENG-GM-11", "ENG-TC-01"): "stop bumper / case: the 8 deg stop is the designed contact (line contact at the stop poses)",
}


def _close_class(dmin, ga, gb, key):
    if key in CLOSE_DISPOSITION and CLOSE_DISPOSITION[key].startswith("JOINT"):
        return "JOINT"
    if dmin < 0.3:
        return "ACTION"
    if dmin < 1.0:
        return "TIGHT"
    return "OK"


def classify_close(poses):
    pairs = {}
    for r in poses:
        for c in r.get("clearance_lt_3mm_unexpected", []):
            pa, pb = c["a"].split("#")[0], c["b"].split("#")[0]
            key = tuple(sorted((pa, pb)))
            k = (c["a"], c["b"])
            if k not in pairs or c["dist_mm"] < pairs[k]["min_mm"]:
                pairs[k] = {"a": c["a"], "b": c["b"], "ga": c.get("ga"), "gb": c.get("gb"), "min_mm": c["dist_mm"], "pose": r["pose"],
                            "at": c.get("at"), "key": key}
            pairs[k].setdefault("poses_lt_3", set()).add(r["pose"])
    rows = []
    for k, v in pairs.items():
        cls = _close_class(v["min_mm"], v["ga"], v["gb"], v["key"])
        rows.append({"a": v["a"], "b": v["b"], "groups": [v["ga"], v["gb"]], "min_mm": v["min_mm"], "at_pose": v["pose"], "at_mm": v["at"],
                     "n_poses_lt_3mm": len(v["poses_lt_3"]), "class": cls,
                     "disposition": CLOSE_DISPOSITION.get(v["key"], "relative motion, >= 1.0 mm: no action" if cls == "OK" else
                                                          "relative motion below 1.0 mm: tolerance stack on the drawings + feeler sweep at "
                                                          "the stops (B-GM bench) TO-DO" if cls == "TIGHT" else
                                                          "relative motion below 0.3 mm: DESIGN ACTION" if cls == "ACTION" else "")})
    rows.sort(key=lambda r: r["min_mm"])
    counts = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    return {"rule": "classes over all poses run: JOINT (one kinematic joint), OK >= 1.0 mm, TIGHT 0.3-1.0 mm (tolerance stack + B-GM "
                    "feeler sweep), ACTION < 0.3 mm; same-rigid-body pairs are not listed (no relative motion)",
            "counts": counts, "rows": rows}


def stage_checks(P, S, reg, out, only_poses=None):
    cdir = out / "checks"
    fp = build_fingerprint()
    res = {"cad_version": CAD_VERSION, "build_fingerprint": fp, "validity": checks.validity(reg), "poses": [], "cg_iteration": S.get("cg_iteration")}
    old_path = cdir / f"checks_{CAD_VERSION}.json"
    if only_poses and old_path.exists():           # v3.5.1: chunked runs merge into the stored file of the same fingerprint
        try:
            old = json.loads(old_path.read_text())
            if old.get("build_fingerprint") == fp:
                res["poses"] = [r for r in old.get("poses", []) if r["pose"] not in only_poses]
                for k in ("bay_wall_sweep", "fixed_wall_check"):
                    if k in old:
                        res[k] = old[k]
                log(f"checks: merging into {old_path.name} ({len(res['poses'])} stored poses, fingerprint {fp})")
            else:
                log(f"checks: stored {old_path.name} has fingerprint {old.get('build_fingerprint')} != {fp}: NOT merged (fresh file)")
        except Exception as ex:
            log(f"checks: stored file unreadable ({ex!r}): fresh file")
    bad_valid = [v for v in res["validity"] if not v["valid"]]
    bad_solids = [v for v in res["validity"] if not v.get("solids_ok", True)]
    log(f"validity: {len(res['validity'])} parts, invalid {len(bad_valid)}: {[v['pn'] for v in bad_valid]}; unexpected solid count "
        f"{len(bad_solids)}: {[(v['pn'], v['n_solids']) for v in bad_solids]}")
    poses = build.pose_list(P, S)
    order = [nm for nm, _, _ in poses]
    if "bay_wall_sweep" not in res:                 # v3.5.1 (lead 188 (2)): signed sweep of every moving instance + fixed parts on the bore
        t1 = time.time()
        bw = checks.bay_wall_sweep(reg, S, P)
        res["bay_wall_sweep"] = bw
        res["fixed_wall_check"] = checks.fixed_wall_check(reg, S)
        log(f"bay-wall sweep: {len(bw['rows'])} moving instances, fail {bw['fail']}; worst {bw['rows'][0]['inst']} r {bw['rows'][0]['r_max_mm']:.3f} "
            f"(clear {bw['rows'][0]['clear_to_bore_mm']:.3f}); fixed fail {res['fixed_wall_check']['fail']}; {time.time() - t1:.0f} s")
        jdump(cdir / f"checks_{CAD_VERSION}.json", res)
    for nm, a, b in poses:
        if only_poses and nm not in only_poses:
            continue
        t1 = time.time()
        inst = build.posed_instances(reg, S, a, b)
        checks.PERTURB_LOG.clear()
        hits = checks.interference_at_pose(inst, all_pairs=(nm == "neutral"))
        close = checks.clearances_at_pose(inst, limit=3.0, pose=nm)
        wall = checks.wall_clearance(inst, R_BAY, -260.0, 380.0)
        rec = {"pose": nm, "alpha_deg": a, "beta_deg": b, "t_s": None, "interference": hits,
               "interference_not_whitelisted": [h for h in hits if not h["whitelisted"]],
               "clearance_lt_3mm": sorted(close, key=lambda r: r["dist_mm"]),
               "clearance_lt_3mm_unexpected": sorted([c for c in close if not c["expected_contact"]], key=lambda r: r["dist_mm"]),
               "bay_wall_min": wall[:12], "perturb_log": list(checks.PERTURB_LOG)}
        rec["t_s"] = round(time.time() - t1, 1)
        res["poses"] = [r for r in res["poses"] if r["pose"] != nm] + [rec]
        res["poses"].sort(key=lambda r: order.index(r["pose"]) if r["pose"] in order else 99)
        log(f"checks {nm}: a {a:.2f} b {b:.2f}: interference {len(hits)} (not whitelisted {len(rec['interference_not_whitelisted'])}), "
            f"close<3 unexpected {len(rec['clearance_lt_3mm_unexpected'])}, wall min "
            f"{wall[0]['dist_mm'] if wall else None} ({wall[0]['inst'] if wall else ''}), {rec['t_s']} s")
        jdump(cdir / f"checks_{CAD_VERSION}.json", res)
    inst0 = build.posed_instances(reg, S, 0.0, 0.0)
    try:
        res["swept_envelope"] = sweep.report(inst0, P, R_bay_mm=R_BAY)
        res["swept_envelope_required_bay"] = sweep.required_bay(res["swept_envelope"])
    except Exception as ex:
        res["swept_envelope_error"] = repr(ex)
    res["close_pairs_classified"] = classify_close(res["poses"])
    done = [r["pose"] for r in res["poses"]]
    bw = res.get("bay_wall_sweep", {})
    fw = res.get("fixed_wall_check", {})
    summ = {"cad_version": CAD_VERSION, "build_fingerprint": fp, "n_parts": len(res["validity"]), "invalid": [v["pn"] for v in bad_valid],
            "unexpected_solid_count": [(v["pn"], v["n_solids"]) for v in bad_solids],
            "poses_done": done, "poses_missing": [nm for nm in order if nm not in done], "n_poses_required": len(order),
            "poses": [{"pose": r["pose"], "interference_not_whitelisted": len(r["interference_not_whitelisted"]),
                       "unexpected_close_lt_3mm": len(r["clearance_lt_3mm_unexpected"]),
                       "min_unexpected_mm": (r["clearance_lt_3mm_unexpected"][0]["dist_mm"] if r["clearance_lt_3mm_unexpected"] else None),
                       "wall_min_mm": (r["bay_wall_min"][0]["dist_mm"] if r["bay_wall_min"] else None),
                       "wall_min_by": (r["bay_wall_min"][0]["inst"] if r["bay_wall_min"] else None)} for r in res["poses"]],
            "bay_wall_sweep": {"rule": bw.get("rule"), "fail": bw.get("fail"),
                               "worst": (bw["rows"][0] | {}) if bw.get("rows") else None},
            "fixed_wall_check": {"rule": fw.get("rule"), "fail": fw.get("fail"), "whitelist": fw.get("whitelist"),
                                 "worst_not_whitelisted": next((r for r in fw.get("rows", []) if not r.get("whitelisted")), None)},
            "close_pairs_counts": res["close_pairs_classified"]["counts"],
            "swept_worst_band": res.get("swept_envelope", {}).get("worst_band")}
    res["summary"] = summ
    jdump(cdir / f"checks_{CAD_VERSION}.json", res)
    jdump(cdir / f"checks_summary_{CAD_VERSION}.json", summ)
    return res


# --------------------------------------------------------------------------------------------- per-part STEP / STL
def roundtrip(shape, path):
    cq.exporters.export(shape, str(path))
    imp = cq.importers.importStep(str(path)).val()
    v0, v1 = solid_volume(shape), solid_volume(imp)
    b0, b1 = bounds_of(shape), bounds_of(imp)
    rel = abs(v1 - v0) / v0 if v0 > 0 else float("nan")
    berr = max(abs(x - y) for x, y in zip(b0, b1))
    ok = (imp.isValid() and all(s.isValid() for s in imp.Solids()) and len(imp.Solids()) == len(shape.Solids())
          and rel < 1e-5 and berr < 0.01)
    return {"passed": bool(ok), "solids": len(imp.Solids()), "volume_mm3": round(v0, 3), "volume_rel_err": rel,
            "bbox_err_mm": berr, "sha256_16": sha16(path)}


def stage_parts(reg, out):
    pdir = out / "parts"
    pdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in reg:
        t1 = time.time()
        rec = {"pn": p.pn, "file_step": f"parts/{p.pn}.step", "file_stl": f"parts/{p.pn}.stl"}
        try:
            rec.update(roundtrip(p.shape, pdir / f"{p.pn}.step"))
            cq.exporters.export(p.shape, str(pdir / f"{p.pn}.stl"), tolerance=0.05, angularTolerance=0.2)
            rec["stl_sha256_16"] = sha16(pdir / f"{p.pn}.stl")
        except Exception as ex:
            rec.update(passed=False, error=repr(ex))
        rec["t_s"] = round(time.time() - t1, 2)
        rows.append(rec)
        if not rec.get("passed"):
            log(f"  STEP round-trip FAILED {p.pn}: {rec}")
    n_ok = sum(1 for r in rows if r.get("passed"))
    log(f"parts: {n_ok}/{len(rows)} STEP round-trips passed")
    res = {"cad_version": CAD_VERSION, "units": "mm", "frame": "part modelling frame (+Z forward); parts modelled in place carry engine-frame "
                                                            "coordinates (origin = gimbal pivot at neutral)",
           "thresholds": {"volume_rel": 1e-5, "bbox_mm": 0.01, "meaning": "software round-trip verification, NOT manufacturing tolerances"},
           "n_passed": n_ok, "n": len(rows), "rows": rows}
    jdump(out / "checks" / f"roundtrip_parts_{CAD_VERSION}.json", res)
    return res


# --------------------------------------------------------------------------------------------- assembly STEP
def instances_neutral(reg, S, alpha=0.0, beta=0.0):
    return build.posed_instances(reg, S, alpha, beta)


def stage_assembly(reg, S, out):
    adir = out / "assembly"
    adir.mkdir(parents=True, exist_ok=True)
    res = {}
    for tag in ("neutral", "stop045"):          # v3.4.1 fix: the v1 loop unpacked None for the posed tag (TypeError, run 1 log kept)
        if tag == "stop045":
            import tvc_kinematics as tk
            a, b = tk.cone_to_ab(8.0, 45.0)
        else:
            a, b = 0.0, 0.0
        inst = instances_neutral(reg, S, a, b)
        asm = cq.Assembly(name=f"ARGOS_ENGINE_{CAD_VERSION.replace('.', '_')}_{tag}_DESIGN_MODEL")
        mats = {p.pn: p.material for p in reg}
        for (pn, i, g, sh, body) in inst:
            c = engmat.color(mats[pn])
            asm.add(sh, name=f"{pn}#{i}", color=cq.Color(*c[:3]))
        path = adir / f"ENGINE_{CAD_VERSION}_{tag}.step"
        asm.export(str(path))
        comp = cq.Compound.makeCompound([t[3] for t in inst])
        imp = cq.importers.importStep(str(path)).val()
        v0, v1 = solid_volume(comp), solid_volume(imp)
        b0, b1 = bounds_of(comp), bounds_of(imp)
        rel = abs(v1 - v0) / v0
        berr = max(abs(x - y) for x, y in zip(b0, b1))
        ok = (imp.isValid() and len(imp.Solids()) == len(comp.Solids()) and rel < 1e-5 and berr < 0.01)
        res[tag] = {"file": f"assembly/{path.name}", "sha256_16": sha16(path), "instances": len(inst), "solids": len(comp.Solids()),
                    "alpha_deg": a, "beta_deg": b, "bounds_mm": [round(x, 3) for x in b0], "roundtrip": {"passed": bool(ok), "volume_rel_err": rel,
                                                                                                       "bbox_err_mm": berr, "solids_reimported": len(imp.Solids())}}
        log(f"assembly {tag}: {len(inst)} instances, {len(comp.Solids())} solids, round-trip {'PASS' if ok else 'FAIL'} (dV/V {rel:.2e}, bbox {berr:.4f} mm)")
        if tag == "neutral":
            man = [{"inst": f"{pn}#{i}", "group": g, "body": body, "bounds_mm": [round(x, 2) for x in bounds_of(sh)]} for (pn, i, g, sh, body) in inst]
            jdump(adir / f"assembly_manifest_{CAD_VERSION}.json", {"cad_version": CAD_VERSION, "frame": "engine frame, mm, +Z forward, origin pivot",
                                                                   "instances": man})
    jdump(out / "checks" / f"roundtrip_assembly_{CAD_VERSION}.json", res)
    return res


def stage_placements(reg, S, out):
    """v3.5.2: assembly/placements_<ver>.json in the v3.5.1 hub format: per instance the part-to-engine 4x4 transform at neutral
    (x_engine = T @ x_part, mm); horns / pushrod items from tvc_pose_frames at neutral; hoses / lines are neutral shapes in the engine frame."""
    import parts_gimbal
    fr = parts_gimbal.tvc_pose_frames(S, 0.0, 0.0)
    rows = []
    for p in reg:
        for i, (T, g) in enumerate(p.placements):
            grp = build.group_of(g)
            if g.startswith("horn:"):
                Tp = fr[int(g.split(":")[1])]["horn"]
            elif g.startswith("pushrod:"):
                _, k, item = g.split(":")
                Tp = fr[int(k)][item]
            elif grp in ("hose", "line"):
                Tp = np.eye(4)
            else:
                Tp = build.group_T(grp if grp != "lock" else "fixed", 0.0, 0.0) @ T
            rows.append({"pn": p.pn, "idx": i, "group": g, "body": build.body_of(g, i, p.pn), "material": p.material,
                         "T_4x4_mm": [[round(float(x), 9) for x in r] for r in np.asarray(Tp, float)]})
    path = out / "assembly" / f"placements_{CAD_VERSION}.json"
    jdump(path, {"id": "placements", "cad_version": CAD_VERSION, "date": time.strftime("%Y-%m-%d", time.gmtime()), "owner": "mechanical",
                 "frame": "engine frame, mm, +Z forward (up on the stand), origin = gimbal pivot; per-part STEP files are in the part local "
                          "frame; x_engine = T @ x_part (homogeneous, mm)",
                 "pose": "neutral (alpha = beta = 0); horns/pushrods/hoses/lines follow tvc_pose_frames / posed_flex at other poses (see the "
                         "assembly STEP stop045)", "instances": rows})
    log(f"placements: {len(rows)} instances -> assembly/{path.name}")
    return {"file": f"assembly/{path.name}", "sha256_16": sha16(path), "instances": len(rows)}


# --------------------------------------------------------------------------------------------- GLB
R_GLTF = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])     # engine (mm, +Z up) -> glTF (+Y up); det +1


def stage_glb(reg, S, out, tol=0.1):
    import trimesh
    adir = out / "assembly"
    adir.mkdir(parents=True, exist_ok=True)
    assert abs(np.linalg.det(R_GLTF) - 1.0) < 1e-12
    inst = instances_neutral(reg, S)
    mats = {p.pn: p.material for p in reg}
    scene = trimesh.Scene()
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    n = 0
    for (pn, i, g, sh, body) in inst:
        vs, ts = sh.tessellate(tol, 0.3)
        if not ts:
            continue
        V = np.array([[p.x, p.y, p.z] for p in vs])
        Vg = (V @ R_GLTF.T) * 1e-3
        c = engmat.color(mats[pn])
        rgba = [int(255 * x) for x in c[:3]] + [255]
        m = trimesh.Trimesh(vertices=Vg, faces=np.array(ts), process=False)
        m.visual.face_colors = np.tile(rgba, (len(ts), 1))
        scene.add_geometry(m, node_name=f"{pn}#{i}", geom_name=f"{pn}#{i}")
        lo, hi = np.minimum(lo, Vg.min(0)), np.maximum(hi, Vg.max(0))
        n += 1
    path = adir / f"ENGINE_{CAD_VERSION}_neutral.glb"
    scene.export(str(path))
    back = trimesh.load(str(path), force="scene")
    bl = np.array(back.bounds)
    comp = cq.Compound.makeCompound([t[3] for t in inst])
    b0 = np.array(bounds_of(comp))
    exp_lo = np.minimum((R_GLTF @ b0[:3]), (R_GLTF @ b0[3:])) * 1e-3
    exp_hi = np.maximum((R_GLTF @ b0[:3]), (R_GLTF @ b0[3:])) * 1e-3
    err = float(max(np.abs(bl[0] - exp_lo).max(), np.abs(bl[1] - exp_hi).max()))
    ok = (len(back.geometry) == n) and err < 2e-4
    res = {"file": f"assembly/{path.name}", "sha256_16": sha16(path), "units": "m", "up": "+Y", "transform": "(x, y, z)_glTF = (x, z, -y)_engine / 1000",
           "meshes": n, "readback_meshes": len(back.geometry), "bounds_m": bl.tolist(), "expected_bounds_m": [exp_lo.tolist(), exp_hi.tolist()],
           "bounds_err_m": err, "tessellation_deflection_mm": tol, "passed": bool(ok),
           "note": "visualisation geometry only (tessellated); the STEP files are the CAD of record"}
    jdump(out / "checks" / f"glb_readback_{CAD_VERSION}.json", res)
    log(f"glb: {n} meshes, readback {len(back.geometry)}, bounds err {err * 1e3:.3f} mm, {'PASS' if ok else 'FAIL'}")
    return res


# --------------------------------------------------------------------------------------------- BOM
# v3.4.1 (lead 2026-10-13): A1 head-end bleed = DESIGNED-IN PROVISION, reserved in the ICD but NOT modelled in the CAD solids.  The
# lines below reserve part numbers, interfaces and budget; masses are computed only where the geometry is defined (tube), otherwise
# None with an ESTIMATE range (no datasheet yet).  Ranges are summed separately (PROVISION_RANGE_G), never mixed with CAD masses.
PROVISION_RANGE_G = {"ENG-BL-01": (10.0, 15.0), "ENG-BL-02": (10.0, 15.0), "ENG-BL-03": (13.0, 22.0), "ENG-BL-04": (15.0, 25.0),
                     "ENG-BL-06": (10.0, 20.0)}          # ESTIMATE (engineering judgement, no datasheet); valves ENG-BL-05 TO-VERIFY
BLEED_MODELLED = bool(config.V34_ON.get("v35_bleed"))  # v3.5 (run 6): the bleed is MODELLED (parts_bleed.py, BL-01..BL-10 in the BOM);
if BLEED_MODELLED:                                     # only the opposed vent tee outside the wall (airframe ICD-14) stays a provision
    PROVISION_RANGE_G = {"ENG-BL-06N": (10.0, 20.0)}


def provision_lines():
    rho316 = engmat.MATERIALS["SS316L"]["rho"]["v"]           # kg/m3, EN 10088-1
    od, t = 3.175e-3, 0.711e-3                                 # 1/8 in x 0.028 in tube (standard size)
    a_tube = math.pi / 4.0 * (od ** 2 - (od - 2 * t) ** 2)
    L_tube = 0.30                                              # m, ESTIMATE route length (engine side ~0.10 + fixed side ~0.20)
    m_tube = a_tube * rho316 * L_tube
    tq = f"TO-QUOTE (delivery {DELIVERY})"
    base = {"qty": 1, "groups": "provision (not modelled)", "cots": True, "supplier": "TO-SELECT", "supplier_pn": "", "unit_price": tq,
            "wetted": "N2O", "oxygen_clean": True, "drawing": "", "step": "", "step_roundtrip": None, "sub_solids": ""}
    rows = [
        {"pn": "ENG-BL-01", "name": "bleed tap T4 crown take-off fitting with restrictor", "material": "SS316L", "process": "COTS fitting",
         "unit_mass_kg": None, "mass_source": "ESTIMATE 10-15 g (no datasheet)",
         "notes": "PROVISION (lead 2026-10-13, A1 head-end bleed): 1/8-27 NPT port at the TEE/T4 crown (CAD frame approx (-20.3, 0, 191.6) mm, "
                  "bleed_taps_v341_v1), restrictor orifice >= 0.8 mm (Dyer purge-sweep bound; 1.0 mm HEM bound), oxygen-clean; port NOT cut in "
                  "the CAD v3.4.1 solids"},
        {"pn": "ENG-BL-02", "name": "bleed tap FD-01 radial take-off (plug-tap fitting)", "material": "SS316L", "process": "COTS fitting",
         "unit_mass_kg": None, "mass_source": "ESTIMATE 10-15 g (no datasheet)",
         "notes": "PROVISION: radial port on the FD-01 riser upstream crown (CAD frame approx (-41.5, 0, 159.2) mm); second tap required by the "
                  "barrier-filter voxel model (T4 alone leaves 4.72 cm3 at 0 deg); port NOT cut in CAD v3.4.1"},
        {"pn": "ENG-BL-03", "name": "bleed line 1/8 in x 0.028 in 316L tube + tee", "material": "SS316L", "process": "COTS tube, bent",
         "unit_mass_kg": round(m_tube, 4),
         "mass_source": f"CALC tube only: {a_tube * 1e6:.3f} mm2 x {rho316:.0f} kg/m3 x {L_tube} m (route length ESTIMATE); tee ESTIMATE +8 g",
         "notes": "PROVISION: -2 class line from both taps to the crossing hose; route reserved in the ICD (mechanical.json v2.1 icd_airframe."
                  "bleed_provision); not modelled"},
        {"pn": "ENG-BL-04", "name": "bleed crossing hose -2 class PTFE / 316 braid, ~0.2 m", "material": "PTFE/SS316", "process": "COTS hose assembly",
         "unit_mass_kg": None, "mass_source": "ESTIMATE 15-25 g (no datasheet)",
         "notes": "PROVISION: crosses the gimbal next to FD-07; stiffness about the pivot 0.5-2 N m/rad ESTIMATE (coordinator 2026-10-13), "
                  "carried inside the 17.2 N m/rad hose budget; to be measured with B-FD-1"},
        {"pn": "ENG-BL-05", "name": "bleed valve 2/2 NC solenoid, x2 in series", "material": "SS316/FFKM", "process": "COTS valve",
         "qty": 2, "unit_mass_kg": None, "mass_source": "TO-VERIFY (datasheet)",
         "notes": "PROVISION: rated >= SEG-P 9.975 MPa, N2O-compatible seals, orifice >= 1.0 mm, fail-closed; two in series for "
                  "stuck-open tolerance (stuck-open flow share 3.5-14 % at 0.8 mm, 5.5-22 % at 1.0 mm); ECU channel with Electronics; "
                  "maker TO-SELECT"},
        {"pn": "ENG-BL-06", "name": "bleed overboard vent: balanced opposed pair or axial outlet", "material": "SS316L", "process": "COTS fitting",
         "unit_mass_kg": None, "mass_source": "ESTIMATE 10-20 g (no datasheet)",
         "notes": "PROVISION: overboard vent through the airframe as a BALANCED OPPOSED PAIR (tee to two equal outlets 180 deg apart) or a "
                  "single AXIAL outlet (coordinator 2026-10-13: a single lateral jet of about 2 N tilts the vehicle 1.2-1.9 deg); location in "
                  "the ICD (airframe owner, mechanical.json v2.1 icd_airframe); away from the plume and the avionics bay"},
    ]
    if BLEED_MODELLED:
        rows = [{"pn": "ENG-BL-06N", "name": "bleed vent non-propulsive opposed tee outside the airframe wall (on ENG-BL-06)", "material": "SS316L",
                 "process": "COTS fitting", "unit_mass_kg": None, "mass_source": "ESTIMATE 10-20 g (no datasheet)",
                 "notes": "PROVISION (v3.5): airframe item at the bay-wall bulkhead ENG-BL-06 (az 112, z 260); balanced opposed pair "
                          "180 deg apart (single lateral jet of ~2 N tilts the vehicle 1.2-1.9 deg, coordinator 2026-10-13); ICD-14 TO-DEFINE"}]
    # v3.5.1 (lead 194 (6) / coordinator 2026-10-13, OI-32): the N2O tank is not in the CAD part set; its outlet geometry is MISSING
    rows.append({"pn": "ENG-TK-OUT", "name": "N2O tank outlet on the aft bulkhead (OI-32): position, bore, sump / dip tube / anti-vortex - MISSING",
                 "material": "SS316L", "process": "TO-DESIGN", "unit_mass_kg": None, "mass_source": "MISSING (tank not in CAD)",
                 "groups": "provision (not modelled: MISSING)",
                 "notes": "MISSING (stated explicitly, OI-32): the tank (combustion.json tank_outlet_coverage_v2p4a geometry_used: tube 101.6 x "
                          "3.175, ID 95.25, internal length 444.9 mm, flat bolted bulkheads = mechanical.json v1 concept, NOT in CAD) and its "
                          "outlet are not modelled; the feed ends at ENG-FD-12F (tank-line flange on FS-01B, route TO-DEFINE ICD-5). GNC needs "
                          "the outlet geometry for the landing-burn dip onset (60-62 g at 125 N ... 78-80 g at 500 N, lead 194 (6)) against its "
                          "ASSUMED 60 g residual. Required decisions: outlet position (centre / r_o), bore, flush or sump, dip tube, screen."})
    out = []
    for r in rows:
        line = dict(base)
        line.update(r)
        line["material_name"] = engmat.MATERIALS.get(line["material"], {}).get("name", line["material"])
        out.append({k: line[k] for k in ("pn", "name", "qty", "groups", "material", "material_name", "process", "cots", "supplier",
                                         "supplier_pn", "unit_mass_kg", "mass_source", "unit_price", "wetted", "oxygen_clean", "drawing",
                                         "step", "step_roundtrip", "sub_solids", "notes")})
    return out


def contingency_lines():
    """Lines that are NOT fitted in the baseline but have a decided procurement path (lead 2026-10-13)."""
    tq = f"TO-QUOTE (delivery {DELIVERY})"
    r = {"pn": "ENG-NZ-05", "name": "J1b contingency: insulating layer 0.5 mm phlogopite mica between the NZ-03 hot layer and the NZ-04 seal",
         "qty": 0, "groups": "contingency (not fitted)", "material": "MICA", "material_name": "phlogopite mica sheet/paper (grade TO-SELECT)",
         "process": "cut from sheet (water-jet / punch)", "cots": True,
         "supplier": "phlogopite mica sheet rated >= 1002 C (J1b FE mica-face peak 901.8 C + 100 K, j1_check v1.1); maker TO-SELECT",
         "supplier_pn": "", "unit_mass_kg": None, "mass_source": "not fitted", "unit_price": tq, "wetted": "", "oxygen_clean": False,
         "drawing": "", "step": "", "step_roundtrip": None, "sub_solids": "",
         "notes": "Lead 2026-10-13: J1 confirmed, J1b dropped UNLESS S-AX fails the 316L lip at 342 C under the 10.6 MPa bearing load at 63.1 bar. "
                  "If fitted: stack +0.5 mm (holder depth or exit plane changes in CAD); NZ-04 in-burn 271.2 C (class >= 371 C), lip 222.9 C."}
    return [r]


def stage_bom(reg, out, roundtrip_rows=None):
    rt = {r["pn"]: r for r in (roundtrip_rows or [])}
    lines = []
    for p in reg:
        if p.bom_parent:
            continue
        m, cg, I, tag = build.part_mass(p)
        groups = sorted({build.group_of(g) for (_, g) in p.placements})
        price = p.price if p.price and p.price != "TO-QUOTE" else f"TO-QUOTE (delivery {DELIVERY})"
        lines.append({"pn": p.pn, "name": p.name, "qty": p.qty, "groups": "/".join(groups), "material": p.material,
                      "material_name": engmat.MATERIALS.get(p.material, {}).get("name", p.material), "process": p.process,
                      "cots": p.cots, "supplier": p.supplier or ("in-house / workshop TO-QUOTE" if not p.cots else "TO-SELECT"),
                      "supplier_pn": p.supplier_pn, "unit_mass_kg": round(m, 5), "mass_source": tag, "unit_price": price,
                      "wetted": p.wetted, "oxygen_clean": bool(p.wetted == "N2O"), "drawing": f"drawings/{p.pn}.pdf" if p.drawing else "",
                      "step": f"parts/{p.pn}.step", "step_roundtrip": (rt.get(p.pn, {}).get("passed") if rt else None),
                      "sub_solids": ", ".join(q.pn for q in reg if q.bom_parent == p.pn), "notes": p.notes})
    # v3.5 (lead 177 (5), datasheet finding C-13): the transport lock (group "lock", GSE) is NOT flight hardware: excluded from the sum
    gse = [l for l in lines if "lock" in str(l.get("groups", ""))]
    for l in lines:
        l["category"] = "GSE (not flight)" if l in gse else "FLIGHT part"
    tot = sum(l["unit_mass_kg"] * l["qty"] for l in lines if l not in gse)
    prov = provision_lines()
    cont = contingency_lines()
    for l in prov:
        l["category"] = "PROVISION (not modelled)"
    for l in cont:
        l["category"] = "CONTINGENCY (not fitted)"
    hw = hardware_lines()
    # v3.5.2 (lead 2026-10-19 item 3): torque + tightening-method + preload-scatter columns on every BOM line (hardware lines from
    # data/hardware_v352.json; the modelled fastener parts below; empty = not a torque joint)
    meth = (hw["raw"].get("rules") or {}).get("tightening_methods")
    for l in lines:
        t = PART_TIGHTENING.get(l["pn"])
        if t and meth:
            l.update(torque_Nm=t[0], torque_basis=t[1], tightening_method=t[2], preload_scatter=t[3], thread_locker=t[4])
    hdr = list(lines[0].keys())
    for k in ("torque_Nm", "torque_basis", "tightening_method", "preload_scatter", "thread_locker"):
        if k not in hdr:
            hdr.append(k)
    path = out / f"BOM_{CAD_VERSION}.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, extrasaction="ignore")
        w.writeheader()
        for l in [l for l in lines if l not in gse] + hw["bom_lines"] + gse + prov + cont:
            w.writerow({k: l.get(k, "") for k in hdr})
    pm = [l["unit_mass_kg"] * l["qty"] for l in prov if l["unit_mass_kg"] is not None]
    res = {"cad_version": CAD_VERSION, "delivery": DELIVERY, "currency": "prices not given: every line TO-QUOTE unless dated",
           "n_lines": len(lines), "n_instances": sum(l["qty"] for l in lines), "mass_sum_kg": round(tot, 4),
           "mass_sum_note": "sum of unit masses x qty (CAD volume x density, or tagged COTS masses); includes the transport-lock items only "
                            "if they are placed (they are not: group 'lock' is excluded from the instance list); PROVISION lines excluded",
           "lines": lines, "mass_sum_flight_kg": round(tot, 4), "gse_lines_excluded_from_flight_mass": [{"pn": l["pn"], "qty": l["qty"], "unit_mass_kg": l["unit_mass_kg"]} for l in gse], "provision_lines": prov, "contingency_lines": cont,
           "tightening_methods": meth or {}, "preload_scatter_rule": (hw["raw"].get("rules") or {}).get("preload_scatter", ""),
           "hardware": {"source": hw["source"], "source_sha256_16": hw["sha"], "n_lines": len(hw["bom_lines"]),
                        "n_items": sum(l["qty"] for l in hw["bom_lines"]), "calc_mass_total_kg": hw["calc_total_kg"],
                        "calc_mass_by_group_kg": hw["calc_by_group_kg"], "lines_without_mass": hw["no_mass"],
                        "mass_rule": "CALC masses (standard nominal geometry), NOT datasheet: the hardware is carried in massprops as "
                                     "max(0.20 kg allowance, CALC sum) at the host parts (lead 188 (11))", "lines": hw["bom_lines"]},
           "provision_mass_estimate_kg": {"computed_lines": round(sum(pm), 4),
                                          "estimate_range_kg": [round(sum(v[0] for v in PROVISION_RANGE_G.values()) / 1e3, 3),
                                                                round(sum(v[1] for v in PROVISION_RANGE_G.values()) / 1e3, 3)],
                                          "valves": "TO-VERIFY (datasheet)",
                                          "note": ("v3.5: bleed MODELLED (ENG-BL-01..10 in the BOM lines); provision = opposed vent tee outside the wall only"
                                                   if BLEED_MODELLED else "A1 head-end bleed provision (lead 2026-10-13), NOT modelled in CAD v3.4.1; range = "
                                                   "ESTIMATE of taps, tube+tee, crossing hose and bulkhead (excl. valves)")}}
    jdump(out / f"BOM_{CAD_VERSION}.json", res)
    log(f"bom: {len(lines)} lines, {res['n_instances']} instances, mass sum {tot:.3f} kg; hardware {len(hw['bom_lines'])} lines, "
        f"{res['hardware']['n_items']} items, CALC {hw['calc_total_kg']:.4f} kg (no mass: {len(hw['no_mass'])} lines)")
    return res


HARDWARE_FILE = HERE / "data" / ("hardware_v351.json" if _MAKE_CAD == "v351" else "hardware_v352.json")
# v3.5.2: modelled fastener parts (BOM part lines): (torque N m, basis, method, preload scatter, thread locker)
PART_TIGHTENING = {
    "ENG-GM-18": (2.0, "DESIGN (GM-18 note)", "M-T1L", "+/-25 % (ASSUMED, K 0.20)", "Loctite 243 (GM-18 note)"),
    "ENG-GM-20": (2.0, "DESIGN (GM-20 note)", "M-T1L", "+/-25 % (ASSUMED, K 0.20)", "Loctite 243 (GM-20 note)"),
    "ENG-HW-25": (None, "TO-DEFINE: servo output-shaft thread (maker value); 10.9 M3 cap 0.2 x 0.65 x 940 MPa x 5.03 mm2 x 3 mm = 1.84 N m (DERIVED)",
                  "M-T1L", "+/-25 % (ASSUMED, K 0.20)", "Loctite 243 (HW-25 name)")}


def hardware_lines():
    """v3.5.1 (REV-MECH-1 RM1-12, lead 188 (11)): standard hardware / O-rings / seals not modelled as solids, from
    data/hardware_v351.json (generated by calcs/hardware_v351.py), as BOM rows (category HARDWARE)."""
    d = json.loads(HARDWARE_FILE.read_text())
    tq = f"TO-QUOTE (delivery {DELIVERY})"
    rows = []
    for r in d["lines"]:
        um = r["unit_mass_g"] / 1e3 if r["unit_mass_g"] is not None else None
        rows.append({"pn": "ENG-" + r["id"], "name": r["item"], "qty": r["qty"], "groups": r["group"], "material": r["grade"],
                     "material_name": r["grade"], "process": "COTS standard part" if r["kind"] != "consumable" else "consumable",
                     "cots": True, "supplier": "TO-SELECT", "supplier_pn": f"{r['standard']} {r['size']}" + (f" x {r['length_mm']}" if r["length_mm"] else ""),
                     "unit_mass_kg": um, "mass_source": r["mass_evidence"], "unit_price": tq, "wetted": "", "oxygen_clean": False,
                     "drawing": "", "step": "", "step_roundtrip": None, "sub_solids": "",
                     "notes": (f"host {r['host']}; joint {r['joint']}; torque {r['torque_Nm']} N m ({r['torque_basis']})" if r["torque_Nm"] is not None
                               else f"host {r['host']}; joint {r['joint']}") + (f"; {r['thread_locker']}" if r["thread_locker"] else "")
                              + f"; L basis: {r['L_basis']}; status {r['status']}" + (f"; ACTION: {r['action']}" if r["action"] else "")
                              + (f"; {r['note']}" if r["note"] else ""),
                     "category": "HARDWARE (standard part, not modelled)", "host": r["host"], "kind": r["kind"],
                     "standard": r["standard"], "size": r["size"], "length_mm": r["length_mm"], "grade": r["grade"],
                     "torque_Nm": r["torque_Nm"], "torque_basis": r["torque_basis"], "status": r["status"],
                     "tightening_method": r.get("tightening_method", ""), "preload_scatter": r.get("preload_scatter", ""),
                     "thread_locker": r.get("thread_locker", "")})
    return {"source": f"03-cad/src/data/{HARDWARE_FILE.name}", "sha": sha16(HARDWARE_FILE), "bom_lines": rows,
            "calc_total_kg": round(d["calc_mass_total_g"] / 1e3, 5),
            "calc_by_group_kg": {k: round(v / 1e3, 5) for k, v in d["calc_mass_by_group_g"].items()}, "no_mass": d["lines_without_mass"],
            "raw": d}


# --------------------------------------------------------------------------------------------- mass properties
HW_ALLOWANCE_KG = 0.20          # lead CHANGELOG 188 (11): carried until DATASHEET masses replace it
GROUPS = (("engine", ("engine",)), ("fixed", ("fixed",)), ("ring", ("ring",)), ("horn", ("horn",)), ("pushrod", ("pushrod",)),
          ("all", ("engine", "fixed", "ring", "horn", "pushrod")))


def evidence_class(tag):
    t = str(tag)
    if t.startswith("CAD volume"):
        return "CAD (volume x engmat density)"
    if t.startswith("HARDWARE"):
        return "HARDWARE CALC (standard nominal geometry; carried as max(allowance, CALC))"
    if t.startswith("COTS mass ("):
        w = t[len("COTS mass ("):].split()[0].rstrip(")").rstrip(",")
        return f"COTS {w}"
    return "OTHER: " + t[:30]


def hardware_rows(rows, d_hw):
    """Hardware lines of data/hardware_v351.json as point masses at their host parts (mean CG of the host instances in the line's
    group), scaled so that the total is max(HW_ALLOWANCE_KG, CALC sum): the allowance is carried where the hardware is."""
    by_pn = {}
    for r in rows:
        by_pn.setdefault(r["pn"], []).append(r)
    calc = sum(l["unit_mass_g"] * l["qty"] for l in d_hw["lines"] if l["unit_mass_g"] is not None) / 1e3
    carried = max(HW_ALLOWANCE_KG, calc)
    scale = carried / calc if calc > 0 else 0.0
    out, unplaced = [], []
    gmap = {"hose": "fixed"}                         # 2 bundle clips without mass: fixed side (no effect)
    for l in d_hw["lines"]:
        if not l["unit_mass_g"]:
            continue
        g = gmap.get(l["group"], l["group"])
        hosts = [h.strip() for h in str(l["host"]).replace(" ", "/").split("/") if h.strip().startswith("ENG-")]
        pts = []
        for h in hosts:
            rr = [r for r in by_pn.get(h, []) if r["group"] == g] or by_pn.get(h, [])
            pts += [np.asarray(r["cg"], float) for r in rr]
        if not pts:
            unplaced.append(l["id"])
            pts = [np.zeros(3)]
        m = l["unit_mass_g"] * l["qty"] / 1e3 * scale
        for q in pts:
            out.append({"pn": "ENG-" + l["id"], "idx": 0, "group": g, "m": m / len(pts), "cg": q, "I": np.zeros((3, 3)),
                        "tag": f"HARDWARE CALC x {scale:.4f} (carried max(allowance {HW_ALLOWANCE_KG} kg, CALC {calc:.4f} kg))"})
    return out, {"allowance_kg": HW_ALLOWANCE_KG, "calc_sum_kg": round(calc, 5), "carried_kg": round(carried, 5), "scale": round(scale, 5),
                 "unplaced_at_origin": unplaced, "lines_without_mass": d_hw["lines_without_mass"]}


def group_block(rows):
    d = {}
    for name, grps in GROUPS:
        gp = build.group_props(rows, grps)
        d[name] = {"m_kg": round(gp["m"], 5), "cg_mm": [round(x, 3) for x in gp["cg_mm"]], "n": gp["n"],
                   "I_cg_kgm2": np.round(gp["I_cg"], 7).tolist(), "I_pivot_kgm2": np.round(gp["I_about"], 7).tolist()}
    return d


def _delta(a, b):
    """b - a for one group block entry (mass, CG, pivot inertia diagonal)."""
    return {"dm_kg": round(b["m_kg"] - a["m_kg"], 5), "dcg_mm": [round(y - x, 3) for x, y in zip(a["cg_mm"], b["cg_mm"])],
            "dI_pivot_diag_kgm2": [round(b["I_pivot_kgm2"][k][k] - a["I_pivot_kgm2"][k][k], 7) for k in range(3)]}


def stage_mass(P, S, reg, out):
    d_hw = json.loads(HARDWARE_FILE.read_text())
    res = {"cad_version": CAD_VERSION, "frame": "engine frame, mm, origin = gimbal pivot (v3.4.1 rev B: pivot FROZEN at the rev A mid-burn CG, "
                                                 "z_head_mid 155.513 mm; the rev B CG offset is reported in states.mid)",
           "z_head_mid_mm": P["z_head_mid"]["v"] * 1e3, "cg_iteration": S.get("cg_iteration"),
           "hardware_rule": f"v3.5.1 (lead 188 (11)): 'states' INCLUDE the standard hardware (data/{HARDWARE_FILE.name}) as point masses at the "
                            "host parts, carried as max(0.20 kg allowance, CALC sum) until DATASHEET masses are in; 'states_without_hardware' "
                            "is the CAD ledger alone",
           "states": {}, "states_without_hardware": {}, "evidence_classes_kg": {}}
    for st in ("wet", "mid", "burnout", "nograin"):
        rows, mg0 = build.mass_ledger(reg, P, st, S)
        hw_rows, hw_info = hardware_rows(rows, d_hw)
        res["states_without_hardware"][st] = group_block(rows)
        res["states"][st] = group_block(rows + hw_rows)
        ev = {}
        for name, grps in GROUPS:
            e = {}
            for r in rows + hw_rows:
                if r["group"] in grps:
                    k = evidence_class(r["tag"])
                    e[k] = e.get(k, 0.0) + r["m"]
            ev[name] = {k: round(v, 5) for k, v in sorted(e.items(), key=lambda kv: -kv[1])}
        res["evidence_classes_kg"][st] = ev
        if st == "mid":
            res["hardware_carried"] = hw_info
            res["ledger_mid"] = [{"pn": r["pn"], "idx": r["idx"], "group": r["group"], "m_kg": round(r["m"], 6),
                                  "cg_mm": [round(x, 2) for x in r["cg"]], "tag": r["tag"]} for r in rows + hw_rows]
            res["grain_mass_wet_kg"] = round(mg0, 5)
    # v3.5.1: deltas against CAD v3.5 (massprops_v3.5.json, 8c11e1e136fc59d8 per lead 182 (7)) and mechanical.json v2.1 gimballed props
    deltas = {}
    f35 = CAD / "massprops_v3.5.json"
    if f35.exists():
        m35 = json.loads(f35.read_text())
        deltas["vs_massprops_v3.5"] = {"file": "03-cad/massprops_v3.5.json", "sha256_16": sha16(f35),
                                       "note": "v3.5 had no hardware: the 'with hardware' delta includes it, 'cad_only' does not",
                                       "with_hardware": {st: {g: _delta(m35["states"][st][g], res["states"][st][g]) for g, _ in GROUPS}
                                                         for st in res["states"] if st in m35.get("states", {})},
                                       "cad_only": {st: {g: _delta(m35["states"][st][g], res["states_without_hardware"][st][g]) for g, _ in GROUPS}
                                                    for st in res["states"] if st in m35.get("states", {})}}
    f351 = CAD / "massprops_v3.5.1.json"                    # v3.5.2: delta against the frozen v3.5.1 file (488b47f9d55ff91b)
    if CAD_VERSION != "v3.5.1" and f351.exists():
        m351 = json.loads(f351.read_text())
        deltas["vs_massprops_v3.5.1"] = {"file": "03-cad/v3.5.1/massprops_v3.5.1.json", "sha256_16": sha16(f351),
                                         "with_hardware": {st: {g: _delta(m351["states"][st][g], res["states"][st][g]) for g, _ in GROUPS}
                                                           for st in res["states"] if st in m351.get("states", {})},
                                         "cad_only": {st: {g: _delta(m351["states_without_hardware"][st][g], res["states_without_hardware"][st][g])
                                                           for g, _ in GROUPS} for st in res["states"] if st in m351.get("states_without_hardware", {})}}
    fmj = HERE.parents[1] / "interfaces" / "mechanical.json"
    if fmj.exists():
        mj = json.loads(fmj.read_text())
        gmp = mj.get("gimballed_mass_properties", {})
        dd = {}
        for st, key in (("wet", "wet_full_grain"), ("mid", "mid_burn"), ("nograin", "dry_grain_burnt")):
            g = gmp.get(key)
            if not g:
                continue
            a = {"m_kg": g["m_kg"]["v"], "cg_mm": [x * 1e3 for x in g["cg_m"]["v"]], "I_pivot_kgm2": g["I_pivot_kgm2"]["v"]}
            dd[st + " (" + key + ")"] = _delta(a, res["states"][st]["engine"])
        deltas["vs_mechanical_json_gimballed"] = {"file": "interfaces/mechanical.json", "version": mj.get("version"), "sha256_16": sha16(fmj),
                                                  "group": "engine (gimballed body; ring, horns, pushrods excluded as in mechanical.json)",
                                                  "deltas": dd}
    res["deltas"] = deltas
    jdump(out / f"massprops_{CAD_VERSION}.json", res)
    e = res["states"]["mid"]["engine"]
    log(f"mass: engine group mid {e['m_kg']:.4f} kg (with hardware), CG {e['cg_mm']}, I_pivot diag {[round(e['I_pivot_kgm2'][k][k], 5) for k in range(3)]}; "
        f"fixed {res['states']['mid']['fixed']['m_kg']:.4f} kg; all {res['states']['mid']['all']['m_kg']:.4f} kg; hardware carried "
        f"{res['hardware_carried']['carried_kg']} kg (CALC {res['hardware_carried']['calc_sum_kg']})")
    return res


# --------------------------------------------------------------------------------------------- drawings
VIEWS = {"front": ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),        # looking along +Y: x right, z up
         "top": ((0.0, 0.0, -1.0), (1.0, 0.0, 0.0)),         # looking down -Z: x right, y up (third-angle top)
         "side": ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),        # looking along -X: y right, z up
         "iso": ((-1.0, 1.0, -0.8), (1.0, 1.0, 0.0))}


def hlr_polylines(shape, view_dir, x_dir, n_seg=24):
    from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    from OCP.HLRAlgo import HLRAlgo_Projector
    from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
    vd = np.array(view_dir, float)
    vd /= np.linalg.norm(vd)
    xd = np.array(x_dir, float)
    xd = xd - (xd @ vd) * vd
    xd /= np.linalg.norm(xd)
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*(-vd)), gp_Dir(*xd))))
    algo.Update()
    algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    out = {"visible": [], "hidden": []}
    for kind, comps in (("visible", (h.VCompound(), h.Rg1LineVCompound(), h.OutLineVCompound())),
                        ("hidden", (h.HCompound(), h.OutLineHCompound()))):
        for c in comps:
            if c is None or c.IsNull():
                continue
            for e in cq.Shape.cast(c).Edges():
                try:
                    pts = e.positions(np.linspace(0.0, 1.0, n_seg if e.geomType() != "LINE" else 2))
                except Exception:
                    continue
                out[kind].append(np.array([[p.x, p.y] for p in pts]))
    return out


def draw_part(p, out_dir, mass_kg, cad_version):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import ezdxf
    sh = p.shape
    b = bounds_of(sh)
    dims = [b[3] - b[0], b[4] - b[1], b[5] - b[2]]
    proj = {k: hlr_polylines(sh, *v) for k, v in VIEWS.items()}
    # layout (third-angle): top above front, side right of front, iso top-right
    def ext(pl):
        allp = np.vstack(pl["visible"] + pl["hidden"]) if (pl["visible"] or pl["hidden"]) else np.zeros((1, 2))
        return allp.min(0), allp.max(0)
    ex = {k: ext(v) for k, v in proj.items()}
    gap = 0.25 * max(dims) + 10.0
    fw, fh = ex["front"][1] - ex["front"][0]
    origin = {"front": np.array([0.0, 0.0]) - ex["front"][0],
              "top": np.array([0.0, fh + gap]) - ex["top"][0],
              "side": np.array([fw + gap, 0.0]) - ex["side"][0]}
    sw = ex["side"][1][0] - ex["side"][0][0]
    origin["iso"] = np.array([fw + gap, fh + gap]) - ex["iso"][0]
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for k in proj:
        doc.layers.add(f"{k.upper()}_VISIBLE", color=7)
        doc.layers.add(f"{k.upper()}_HIDDEN", color=8, linetype="DASHED" if "DASHED" in doc.linetypes else "CONTINUOUS")
    fig, ax = plt.subplots(figsize=(16.54, 11.69))       # A3 landscape
    for k, pl in proj.items():
        o = origin[k]
        for kind, style in (("hidden", dict(color="0.6", lw=0.4, ls=(0, (3, 2)))), ("visible", dict(color="k", lw=0.7))):
            for poly in pl[kind]:
                q = poly + o
                ax.plot(q[:, 0], q[:, 1], **style)
                msp.add_lwpolyline([tuple(map(float, r)) for r in q], dxfattribs={"layer": f"{k.upper()}_{kind.upper()}"})
        lab = (o + np.array([ex[k][0][0], ex[k][0][1]]) + np.array([0.0, -6.0]))
        ax.text(lab[0], lab[1], k.upper() + (" (along +Y)" if k == "front" else " (along -Z)" if k == "top" else " (along -X)" if k == "side" else " (iso, not to scale)"),
                fontsize=7)
        msp.add_text(k.upper(), dxfattribs={"layer": f"{k.upper()}_VISIBLE", "height": 2.5}).set_placement((float(lab[0]), float(lab[1])))
    # overall dimensions on the front and top views
    of, ot = origin["front"], origin["top"]
    x0f, z0f = ex["front"][0] + of
    x1f, z1f = ex["front"][1] + of
    ax.annotate("", xy=(x0f, z0f - 0.08 * gap), xytext=(x1f, z0f - 0.08 * gap), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text((x0f + x1f) / 2, z0f - 0.08 * gap - 3, f"{dims[0]:.2f} (X)", ha="center", va="top", fontsize=7)
    ax.annotate("", xy=(x0f - 0.08 * gap, z0f), xytext=(x0f - 0.08 * gap, z1f), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text(x0f - 0.08 * gap - 2, (z0f + z1f) / 2, f"{dims[2]:.2f} (Z)", ha="right", va="center", fontsize=7, rotation=90)
    y0t, y1t = ex["top"][0][1] + ot[1], ex["top"][1][1] + ot[1]
    xt = ex["top"][0][0] + ot[0]
    ax.annotate("", xy=(xt - 0.08 * gap, y0t), xytext=(xt - 0.08 * gap, y1t), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text(xt - 0.08 * gap - 2, (y0t + y1t) / 2, f"{dims[1]:.2f} (Y)", ha="right", va="center", fontsize=7, rotation=90)
    ax.set_aspect("equal")
    ax.axis("off")
    d = p.dwg or {}
    tb = [f"{p.pn}   {p.name[:110]}",
          f"Material: {engmat.MATERIALS.get(p.material, {}).get('name', p.material)}   Process: {p.process[:80]}",
          f"Mass: {mass_kg * 1e3:.1f} g (CAD volume x density)   Units: mm   Frame: modelling frame (+Z forward)   Bounding box: "
          f"{dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f}",
          f"Datum: {d.get('datum', 'TO-DEFINE')}   Finish: {d.get('finish', 'TO-DEFINE')}   Heat treatment: {d.get('ht', 'n/a')}",
          "Fits / features: " + "; ".join(d.get("fits", []))[:200],
          f"Notes: {p.notes[:220]}",
          f"ARGOS engine CAD {cad_version} - DESIGN-MODEL DRAWING generated from the solid; dimensions from the model; "
          "general tolerances ISO 2768-m unless a fit is listed; NOT released for fabrication (Mechanical, 2026-10-13)",
          ("Oxygen service: clean to ASTM G93, Krytox only" if p.wetted == "N2O" else "")]
    fig.text(0.02, 0.02, "\n".join(t for t in tb if t), fontsize=7, family="monospace", va="bottom",
             bbox=dict(boxstyle="square", fc="white", ec="black", lw=0.6))
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{p.pn}.pdf")
    fig.savefig(out_dir / f"{p.pn}.svg")
    plt.close(fig)
    y = -20.0
    for t in tb:
        if t:
            msp.add_text(t[:250], dxfattribs={"height": 2.0}).set_placement((0.0, y))
            y -= 4.0
    doc.saveas(out_dir / f"{p.pn}.dxf")
    return {"pn": p.pn, "views": list(proj), "n_visible_edges": sum(len(v["visible"]) for v in proj.values()),
            "files": [f"drawings/{p.pn}.{x}" for x in ("pdf", "svg", "dxf")], "bbox_mm": [round(x, 3) for x in dims]}


def stage_drawings(reg, out):
    rows = []
    for p in reg:
        if not p.drawing:
            continue
        t1 = time.time()
        try:
            m = build.part_mass(p)[0]
            r = draw_part(p, out / "drawings", m, CAD_VERSION)
            r["t_s"] = round(time.time() - t1, 1)
            rows.append(r)
        except Exception as ex:
            rows.append({"pn": p.pn, "error": repr(ex), "trace": traceback.format_exc()[-600:]})
            log(f"  drawing FAILED {p.pn}: {ex!r}")
    log(f"drawings: {sum(1 for r in rows if 'error' not in r)}/{len(rows)}")
    jdump(out / "checks" / f"drawings_{CAD_VERSION}.json", {"cad_version": CAD_VERSION, "rows": rows})
    return rows


# --------------------------------------------------------------------------------------------- README + properties
def stage_readme(P, S, reg, out, results):
    import importlib.metadata as md
    srcs = sorted(HERE.glob("*.py")) + sorted((HERE / "calcs").glob("*.py")) + sorted((HERE.parent / "calcs").glob("*.py")) + sorted((HERE / "data").glob("*.json"))
    outs = sorted([p for p in out.rglob("*") if p.is_file() and p.suffix in (".step", ".stl", ".glb", ".csv", ".json", ".pdf", ".svg", ".dxf")
                   and "src" not in p.parts])
    props = {"cad_version": CAD_VERSION, "date": "2026-10-13", "owner": "mechanical",
             "status": "DESIGN MODEL - not released for fabrication; geometric checks are software checks, not physical validation",
             "generator": {"cadquery": md.version("cadquery"), "cadquery-ocp": md.version("cadquery-ocp") if _has("cadquery-ocp") else "n/a",
                           "trimesh": md.version("trimesh"), "ezdxf": md.version("ezdxf"), "python": sys.version.split()[0]},
             "frames": {"cad": "engine frame, mm, +Z forward (nozzle -> injector), origin = gimbal pivot at neutral, +X outer gimbal axis, +Y inner",
                        "glb": "metres, +Y up: (x, y, z)_glTF = (x, z, -y)_engine / 1000"},
             "config_overrides": BUILD_OVERRIDES | {"z_head_mid_m": P["z_head_mid"]["v"]},
             "sources_sha256_16": {str(p.relative_to(HERE.parents[1])): sha16(p) for p in srcs},
             "outputs_sha256_16": {str(p.relative_to(out)): sha16(p) for p in outs},
             "results": {k: v for k, v in results.items() if k in ("assembly", "glb", "parts_summary", "checks_summary", "bom_summary", "mass_summary")}}
    jdump(out / "properties.json", props)
    n_parts = len(list(reg))
    cs = results.get("checks_summary") or {}
    if not cs and (out / "checks" / f"checks_summary_{CAD_VERSION}.json").exists():
        cs = json.loads((out / "checks" / f"checks_summary_{CAD_VERSION}.json").read_text())
    bws, fws = cs.get("bay_wall_sweep") or {}, cs.get("fixed_wall_check") or {}
    n_int = sum(r.get("interference_not_whitelisted", 0) for r in cs.get("poses", []))
    hwf = HARDWARE_FILE
    lines = [f"# ARGOS hopper engine - CAD {CAD_VERSION} (design model)", "",
             "Mechanical, 2026-10-13.  Generated by `03-cad/src/make_all.py`; do not edit outputs by hand.", "",
             "## Status", "",
             "Design model of the gimballed N2O hybrid engine, its gimbal, TVC linkage, feed (riser TEE, O3b hose coil, fixed 3/8 line), the",
             "MV-P main-valve module and the A1 bleed path.  It is **not released for fabrication**: drawings are design-model projections with the",
             "fits and notes the parts carry; tolerances, weld procedures and inspection plans are open.  Geometric checks (validity, interference,",
             "clearance, bay-wall sweep, STEP round-trip, GLB read-back) are software checks; they are not physical validation, and matching",
             "numbers or zero interferences are not an approval.", "",
             "## Changes from v3.5 (lead CHANGELOG 182, 183, 188, 194)", "",
             "- RM1-01 (BLOCKING): ENG-BL-02 bleed tap turned inward (axis inclined 30 deg, x -39) and BL-03A/E re-routed; BL-04 hose unchanged.",
             "- 182 (2): gimbal bearings 608-2RS -> drawn-cup needle bearings HK0808 (C0r 2.60 kN INA / 2.73 kN Koyo >= 1.80 kN) on 440C pins",
             "  (58-62 HRC raceway), 12 N7 cup seats in the ring and posts.",
             "- RM1-02: FD-11 P-clip tabs formed to the 140 mm bore (on the bore, not in it); the signed bay-wall sweep is a permanent check.",
             "- 183 (4) / RM1-07: GM-01/02 lever root = one annular sector + fillets (R 1.5 side (R 1.2 where R 1.5 fails), R 0.5 inner (0.75 mm",
             "  gap to the case), R 1.0 OD, R 1.5 arm chain; the far-side arm-chamfer/back-web junction stays sharp: see the build log).",
             "- 182 (1) head fix (selected, verification OPEN): TC-03 flange recessed under the TC-10 insulator (TB1) and TC-03 in GlidCop AL-15",
             "  dispersion-strengthened copper (Hoganas 0667HOG-2); AS568-016 FFKM under the flange.",
             "- RM1-12: TC-02 J-FWD taps drilled 4.2 x 9.0 (M5-6H full thread 8.0) so the ISO 7380-1 M5 x 10 A4-80 screw engages 6.83 mm (v3.5:",
             "  6.5 deep, M5 x 10 bottomed); every fastener, O-ring and seal not modelled as a solid has a BOM line (category HARDWARE).", "",
             "## Frames and units", "",
             "- CAD / STEP: millimetres, engine frame, +Z forward (nozzle to injector), origin at the gimbal pivot at neutral, +X outer gimbal axis,",
             "  +Y inner gimbal axis.  Parts modelled in place carry engine-frame coordinates in their STEP files.",
             "- GLB: metres, +Y up, (x, y, z)_glTF = (x, z, -y)_engine / 1000.  Visualisation only (tessellated).", "",
             "## Contents", "",
             f"- `parts/` - {n_parts} part numbers: STEP (verified round-trip) and STL.",
             f"- `assembly/` - ENGINE_{CAD_VERSION}_neutral.step (every instance, re-import verified), ENGINE_{CAD_VERSION}_stop045.step (8 deg stop,",
             f"  visual), ENGINE_{CAD_VERSION}_neutral.glb, assembly_manifest_{CAD_VERSION}.json.",
             f"- `drawings/` - design-model drawings (PDF, SVG, DXF) of the {sum(1 for p in reg if p.drawing)} machined parts.",
             f"- `BOM_{CAD_VERSION}.csv/.json` - one line per part number plus the HARDWARE lines ({hwf.name}); categories FLIGHT part / HARDWARE /",
             f"  GSE (not flight, excluded from the flight mass) / PROVISION / CONTINGENCY; every price TO-QUOTE (delivery {DELIVERY}) unless dated.",
             f"- `massprops_{CAD_VERSION}.json` - groups, burn states, CG and inertia about the CG and the pivot, WITH the hardware carried as",
             "  max(0.20 kg allowance, CALC sum) at the host parts (and without it), mass by evidence class, deltas against v3.5 and mechanical.json.",
             f"- `checks/` - validity, interference and clearance at {cs.get('n_poses_required', 18)} poses, classified < 3 mm pairs, signed bay-wall",
             "  sweep (72 directions x 0..8 deg + stop polygon, r <= 69.0 mm) and fixed-part check, swept envelope, round-trips, GLB read-back.",
             "- `src/` - the generator (parameters from the interface files through config.py; calcs/ holds the design calculations).", "",
             "## Rebuild", "",
             "```", "/opt/engine-venv/bin/python 03-cad/src/make_all.py            # all stages",
             "/opt/engine-venv/bin/python 03-cad/src/make_all.py --stages checks --poses stop135,stop180   # chunk, merged into checks/",
             "/opt/engine-venv/bin/python 03-cad/src/calcs/hardware_v351.py   # regenerates src/data/hardware_v351.json", "```", "",
             "## Check results of this build", "",
             f"- poses done {len(cs.get('poses_done', []))} of {cs.get('n_poses_required', '?')}; missing: {cs.get('poses_missing', '?')}",
             f"- non-whitelisted interferences summed over the poses: {n_int}",
             f"- bay-wall sweep (moving): fail {bws.get('fail')}; worst {((bws.get('worst') or {}).get('inst'))} r "
             f"{((bws.get('worst') or {}).get('r_max_mm'))} mm",
             f"- fixed parts on the bore: fail {fws.get('fail')}; whitelist {list((fws.get('whitelist') or {}).keys())}",
             f"- < 3 mm pairs between relatively moving bodies, classes: {cs.get('close_pairs_counts')}", "",
             "```", json.dumps(props["results"], indent=1, default=str)[:6000], "```", "",
             "## Open items carried in this freeze (not closed by this build)", "",
             "- 182 (1) TC-02 head fix: design selected (TB1 + GlidCop TC-03); acceptance on the S-AX contact model (RM1-03) with the line 183",
             "  criterion, and GlidCop hot strength (datasheet gives RT only), seat coining/erosion, galvanic couple and N2O on hot CuO: OPEN.",
             "- 182 (4) NZ-04 flexible graphite >= 627 C oxidising-service datasheet: OPEN (see mechanical.json / handback).",
             "- 182 (6) J-FWD A4-80 in joints.py at 93 / 102 bar and FA1S (lead 194): see 04-fea/structural/joints.py results.",
             "- OI-32: the N2O tank and its outlet are NOT in the CAD part set: outlet geometry MISSING (BOM provision line ENG-TK-OUT).",
             "- Hardware masses are CALC (standard nominal geometry), not datasheet; lines without mass are listed in the BOM JSON.",
             "- Hose FD-07: convoluted PTFE -6 assumed (sourced data in calcs/coil_reroute_v341.py); maker, pressurised EI (B-FD-1), dynamic",
             "  duty acceptance and the convolution volume are open.",
             "- Prices: every line TO-QUOTE for delivery to Sonderborg DK-6400.",
             "- Fabrication drawings, tolerances, weld and cleaning procedures: open.", ""]
    (out / "README.md").write_text("\n".join(lines))
    log("readme + properties written")
    return props


def _has(dist):
    import importlib.metadata as md
    try:
        md.version(dist)
        return True
    except md.PackageNotFoundError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="build,checks,parts,assembly,glb,bom,mass,drawings,readme")
    ap.add_argument("--poses", default="")
    ap.add_argument("--out", default=str(CAD))
    a = ap.parse_args()
    st = set(a.stages.split(","))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    P, S, reg, clog = stage_build()
    results = {}
    # v3.4.1: a partial re-run (e.g. --stages bom,...,readme after a failure) reports the stored results of the stages it skips
    for stage, key, fn in (("parts", "parts_summary", f"roundtrip_parts_{CAD_VERSION}.json"),
                           ("assembly", "assembly", f"roundtrip_assembly_{CAD_VERSION}.json"),
                           ("glb", "glb", f"glb_readback_{CAD_VERSION}.json")):
        f = out / "checks" / fn
        if stage not in st and f.exists():
            d = json.loads(f.read_text())
            d = {"n": d["n"], "passed": d["n_passed"]} if stage == "parts" else d
            results[key] = d | {"from_stored_file": f"checks/{fn}", "stored_sha256_16": sha16(f)}
    jdump(out / "checks" / f"build_log_{CAD_VERSION}.json", {"cad_version": CAD_VERSION, "config_log": clog, "cg_iteration": S.get("cg_iteration")})
    if S.get("bleed"):                                   # v3.5: bleed topology (lead RE-10) next to the other checks
        jdump(out / "checks" / f"bleed_topology_{CAD_VERSION}.json", S["bleed"])
    if "parts" in st:
        r = stage_parts(reg, out)
        results["parts_summary"] = {"n": r["n"], "passed": r["n_passed"]}
    if "assembly" in st:
        results["assembly"] = stage_assembly(reg, S, out)
    if "glb" in st:
        results["glb"] = stage_glb(reg, S, out)
    if "placements" in st:
        results["placements"] = stage_placements(reg, S, out)
    if "bom" in st:
        rt = json.loads((out / "checks" / f"roundtrip_parts_{CAD_VERSION}.json").read_text())["rows"] if (out / "checks" / f"roundtrip_parts_{CAD_VERSION}.json").exists() else None
        b = stage_bom(reg, out, rt)
        results["bom_summary"] = {"lines": b["n_lines"], "instances": b["n_instances"], "mass_sum_kg": b["mass_sum_kg"]}
    if "mass" in st:
        m = stage_mass(P, S, reg, out)
        results["mass_summary"] = {k: m["states"]["mid"][k]["m_kg"] for k in ("engine", "fixed", "ring", "horn", "pushrod", "all")}
        results["mass_summary"]["engine_cg_mid_mm"] = m["states"]["mid"]["engine"]["cg_mm"]
    if "drawings" in st:
        stage_drawings(reg, out)
    if "checks" in st:
        c = stage_checks(P, S, reg, out, only_poses=[x for x in a.poses.split(",") if x] or None)
        results["checks_summary"] = c["summary"]
    if "readme" in st:
        stage_readme(P, S, reg, out, results)
    jdump(out / "checks" / f"make_all_log_{CAD_VERSION}.json", {"stages": sorted(st), "t_s": round(time.time() - t0, 1), "log": LOG})
    log(f"make_all done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
