"""FEA3D F1 driver: build the assembled model, write one deck per (variant, thermal state), solve with CalculiX, store unit fields.
usage: run_f1.py RUN_NAME LEVEL STATE[,STATE...] [key=value variant options] [steps=TH,OP,PM,GX,GY,GZ] [solve=0|1]
fea3d 2026-10-13."""
from __future__ import annotations
import sys, json, time, os
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import asm_build as AB      # noqa: E402
import asm3d as A3          # noqa: E402
import fe3d                 # noqa: E402
import ccxrun               # noqa: E402

RUNS = Path("/home/claude/work/fea3d/runs")
COARSE_BODIES = ["TC-02", "TC-03", "TC-04", "TC-09", "NZ-01", "NZ-02", "NZ-03", "NZ-04", "FD-01", "PD-01R", "PD-01S"]


def build(level, variant, steps, pose_steps=True):
    t0 = time.time()
    M = AB.Asm(level=level, variant=variant)
    AB.define(M)
    rep = AB.pressure_sets(M)
    for st in steps:
        if st in ("GX", "GY", "GZ"):
            AB.inertial(M, st, ("lin", "XYZ".index(st[1])))
        elif st in ("AX", "AY", "AZ"):
            ax = np.eye(3)["XYZ".index(st[1])]
            AB.inertial(M, st, ("ang", ax, {"engine", "ring", "fixed", "horn1", "horn2"}))
        elif st == "EAX":       # engine + ring about the outer gimbal axis (fixed X)
            AB.inertial(M, st, ("ang", np.array([1.0, 0, 0]), {"engine", "ring"}))
        elif st == "EAY":       # engine about the inner axis (ring Y, posed)
            AB.inertial(M, st, ("ang", M.Rg["ring"] @ np.array([0, 1.0, 0]), {"engine"}))
        elif st in ("R1", "R2"):  # unit actuator force pair (rod compression)
            AB.rod_pair(M, st, int(st[1]))
        elif st == "BUMP":        # unit stop force pair at the 8 deg conical stop (variant stop = azimuth)
            AB.bumper_pair(M, st, float(M.v["stop"]))
        elif st == "TZ":          # unit net thrust: +1 N along the engine axis on the TC-02 chamber face (FA-1 thrust spike / ICD)
            b2 = M.bodies["TC-02"]
            m2 = (b2.fn[:, 2] < -0.99) & (np.hypot(b2.fc[:, 0], b2.fc[:, 1]) <= 28.0) & (b2.fc[:, 2] < 112.0)
            if m2.sum() < 10:
                raise RuntimeError(f"TZ: TC-02 chamber face not found ({int(m2.sum())} faces)")
            Rp = M.Rg["engine"]
            zc = float(np.average(b2.fc[m2, 2], weights=b2.fa[m2]))
            M.add_force_on_faces(st, [("TC-02", m2)], Rp @ np.array([0.0, 0.0, zc]), Rp @ np.array([0.0, 0.0, 1.0]))
            M.notes.append(f"TZ: +1 N (engine +Z) on {int(m2.sum())} TC-02 chamber-face faces, area {float(b2.fa[m2].sum()):.1f} mm2, z {zc:.3f}")
    if any(st.startswith("FREQ") for st in steps):
        ml = AB.modal_masses(M)
        M.notes.append(f"modal: {len(ml)} item point masses, {sum(m for _, _, m, _ in ml) * 1e3:.4f} kg")
    M.notes.append(f"build total {time.time() - t0:.1f} s")
    return M, rep


def model_meta(M):
    return {"steps": getattr(M, "steps", None), "rod_geom": getattr(M, "rod_geom", None), "bumper": getattr(M, "bumper", None),
            "level": M.level, "cad": A3.CAD, "step_sha16": A3.A.STEP_SHA16, "version": A3.VERSION, "bodies": {nm: {"noff": int(b.noff), "n": int(len(b.X0)), "eoff": int(b.eoff), "ne": int(len(b.T10)), "grp": b.grp, "mat": b.mat,
                            "trule": b.trule, "role": b.role, "mesh": b.meta} for nm, b in M.bodies.items()},
            "extra": {int(k): [list(map(float, v[0])), v[1]] for k, v in M.extra.items()},
            "ref": {k: int(v) for k, v in M.ref.items()}, "members": {k: [int(x) for x in v] for k, v in M.members.items()},
            "bush": M.bush, "springA": [(lab, int(e), int(n1), int(n2), float(k)) for lab, e, n1, n2, k in M.springA],
            "rigid": [(lab, [int(x) for x in nodes], int(ref), int(rot)) for lab, nodes, ref, rot in M.rigid],
            "af_sets": M.af_sets, "variant": {k: (list(v) if isinstance(v, tuple) else v) for k, v in M.v.items()},
            "hardware_excluded": getattr(M, "hardware_excluded", []), "bk": M.bk,
            "alpha": M.alpha, "beta": M.beta, "psi": M.psi, "Rg": {k: v.tolist() for k, v in M.Rg.items()},
            "cg": {k: v.tolist() for k, v in M.cg.items()}, "k_chain": M.k_chain, "bearing": M.bk,
            "ties": M.ties, "rbe": M.rbe, "skipped": M.C.skipped, "n_eq": len(M.C.eqs), "notes": M.notes,
            "tie_edges": getattr(M, "tie_edges", {}), "gnd": sorted(int(x) for x in M.gnd), "needle_node": int(M.needle_node),
            "items": [{k: (v if k != "attach" else (v[0], v[1] if v[0] == "member" else [(b, int(np.asarray(s).sum())) for b, s in v[1]]))
                       for k, v in it.items()} for it in M.items]}


def read_dat_modal(dat):
    """Eigenvalue table, participation factors and effective modal mass of a ccx *FREQUENCY step (.dat)."""
    L = open(dat, errors="replace").read().splitlines()
    out = {"modes": [], "participation": [], "effective_mass": [], "total_effective_mass": None}
    k = 0
    while k < len(L):
        u = L[k].upper()
        if "E I G E N V A L U E   O U T P U T" in u:
            k += 1
            while k < len(L) and not L[k].strip()[:1].isdigit():
                k += 1
            while k < len(L) and L[k].strip()[:1].isdigit():
                p = L[k].split()
                out["modes"].append({"mode": int(p[0]), "eigenvalue": float(p[1]), "omega_rad_s": float(p[2]), "f_Hz": float(p[3])})
                k += 1
            continue
        if "T O T A L   E F F E C T I V E   M A S S" in u:
            k += 1
            while k < len(L) and not L[k].strip()[:1].isdigit():
                k += 1
            try:
                out["total_effective_mass"] = [float(x) for x in L[k].split()[:6]]
            except (ValueError, IndexError):
                pass
            k += 1
            continue
        for key, tag in (("participation", "P A R T I C I P A T I O N   F A C T O R S"), ("effective_mass", "E F F E C T I V E   M O D A L   M A S S")):
            if tag in u:
                k += 1
                while k < len(L) and not L[k].strip()[:1].isdigit():
                    k += 1
                while k < len(L) and L[k].strip()[:1].isdigit():
                    p = L[k].split()
                    out[key].append([int(p[0])] + [float(x) for x in p[1:7]])
                    k += 1
                break
        else:
            k += 1
            continue
    return out


def extract(frd, M, steps, out):
    nmax = M.next_n
    t0 = time.time()
    res = fe3d.read_frd(frd, nmax)
    arrs = {}
    if any(st.startswith("FREQ") for st in steps):
        # static steps first (one block each), then the FREQ step (one block per mode, possibly fewer than requested)
        stat = [st for st in steps if not st.startswith("FREQ")]
        if steps[:len(stat)] != stat or len(steps) != len(stat) + 1:
            raise RuntimeError("FREQ must be the last and only eigen step")
        for st, r in zip(stat, res[:len(stat)]):
            arrs[f"U_{st}"] = r["DISP"][:, :3].astype(np.float64)
            if "STRESS" in r:
                arrs[f"S_{st}"] = r["STRESS"][:, :6].astype(np.float32)
        arrs["U_FREQ"] = np.stack([r["DISP"][:, :3] for r in res[len(stat):]]).astype(np.float32)
        np.savez_compressed(out, **arrs)
        return time.time() - t0
    if len(res) != len(steps):
        raise RuntimeError(f"frd has {len(res)} result blocks, expected {len(steps)}")
    for st, r in zip(steps, res):
        arrs[f"U_{st}"] = r["DISP"][:, :3].astype(np.float64)
        if "STRESS" in r:
            arrs[f"S_{st}"] = r["STRESS"][:, :6].astype(np.float32)
        if "ERROR" in r:
            arrs[f"E_{st}"] = r["ERROR"][:, 0].astype(np.float32)      # ccx stress error estimator (per node, %)
    np.savez_compressed(out, **arrs)
    return time.time() - t0


def extract_only(name, state, steps):
    """Re-extract fields from a kept frd (no model rebuild: node count from model.json)."""
    wd = RUNS / name
    meta = json.loads((wd / "model.json").read_text())
    nmax = max([int(k) for k in meta["extra"]] + [b["noff"] + b["n"] - 1 for b in meta["bodies"].values()]) + 1

    class _M:
        next_n = nmax
    sd = wd / state
    dt = extract(sd / "f1.frd", _M, steps, sd / "fields.npz")
    print(f"[{name}/{state}] extracted in {dt:.1f} s", flush=True)
    os.remove(sd / "f1.frd")


def main(argv):
    if argv[0] == "--extract":
        steps = (argv[3] if len(argv) > 3 else "TH,OP,PM,GX,GY,GZ").split(",")
        return extract_only(argv[1], argv[2], steps)
    name, level, states = argv[0], float(argv[1]), argv[2].split(",")
    opts = dict(a.split("=", 1) for a in argv[3:])
    steps = opts.pop("steps", "TH,OP,PM,GX,GY,GZ").split(",")
    solve = opts.pop("solve", "1") == "1"
    variant = {}
    for k, v in opts.items():
        if k == "pose":
            variant[k] = tuple(float(x) for x in v.split("/"))
        elif k == "posename":     # Mechanical pose_list name (neutral, alpha+, ..., combined045, stop000 ...): sets pose (+ stop)
            pl = {p[0]: p for p in AB.pose_list()}
            _, a_, b_, stp = pl[v]
            variant["pose"] = (a_, b_)
            variant["posename"] = v
            if stp is not None:
                variant["stop"] = stp
        elif k == "stop":
            variant[k] = float(v)
        elif k == "coarse":       # coarse=2: engine pressure parts at level 2 (gimbal / fixed / TC-01 / collar stay at LEVEL)
            variant["levels"] = {bn: float(v) for bn in COARSE_BODIES}
        elif k == "refine":       # refine=GM-01:x/y/z/r/h;GM-01:x/y/z/r/h
            ref = {}
            for part in v.split(";"):
                bn, nums = part.split(":")
                ref.setdefault(bn, []).append(tuple(float(x) for x in nums.split("/")))
            variant[k] = ref
        elif k == "k_af":
            variant[k] = tuple(float(x) for x in v.split("/"))
        elif k in ("thrust_for_bearings", "k_chain", "k_needle_scale", "pc_mass_g"):
            variant[k] = float(v)
        else:
            variant[k] = v
    wd = RUNS / name
    wd.mkdir(parents=True, exist_ok=True)
    M, prep = build(level, variant, steps)
    M.steps = steps
    (wd / "model.json").write_text(json.dumps(model_meta(M), default=float))
    (wd / "pressure.json").write_text(json.dumps(prep, indent=1, default=float))
    (wd / "mass.json").write_text(json.dumps(AB.mass_check(M), indent=1, default=float))
    ST = AB.SaxThermal()
    log = wd / "runs.jsonl"
    for state in states:
        Tb, tstats = AB.thermal(M, state, ST)
        sd = wd / state
        sd.mkdir(exist_ok=True)
        (sd / "thermal.json").write_text(json.dumps(tstats, indent=1))
        np.savez_compressed(sd / "T.npz", **{nm: v for nm, v in Tb.items()})
        title = f"FEA3D {A3.VERSION} {name} level {level} state {state} variant {json.dumps(M.v, default=str)}"
        inp = AB.write_deck(M, sd / "f1.inp", Tb, steps, title)
        print(f"[{name}/{state}] deck {inp.stat().st_size / 1e6:.1f} MB", flush=True)
        if not solve:
            continue
        r = ccxrun.run_ccx("f1", sd, threads=int(os.environ.get("FEA3D_THREADS", "2")), mem_cap_gb=6.0, log=log)
        print(f"[{name}/{state}] ccx {json.dumps(r)}", flush=True)
        if r["returncode"] != 0 or r["killed"]:
            raise SystemExit(f"ccx failed: {r}")
        dt = extract(sd / "f1.frd", M, steps, sd / "fields.npz")
        print(f"[{name}/{state}] extracted in {dt:.1f} s", flush=True)
        if any(st.startswith("FREQ") for st in steps):
            (sd / "modal.json").write_text(json.dumps(read_dat_modal(sd / "f1.dat"), indent=1))
        os.remove(sd / "f1.frd")


if __name__ == "__main__":
    main(sys.argv[1:])
