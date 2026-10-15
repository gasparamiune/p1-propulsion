"""S-3D v1 - strength of the gimbal load path under the limit loads (04-fea/structural, 2026-10-13, Mechanical).

Re-uses the stiffness model of 04-fea/stiffness/gimbal_k.py v2 (CalculiX C3D10 of the CAD v3.4 V5c gimbal: posts GM-08, rings
GM-09/GM-10, TVC brackets GM-13/14 fused as FRAME; GM-03 RING; GM-01+GM-02 COLLAR; GM-16 horns; engine rigid on the collar bore;
inner/outer pins + 608 bearings as springs; rod chains as SPRINGA (rod FE + 2 GE 5 E + stud); servos rigid, holding; airframe rigid at
the 16 radial M5 holes of GM-09/GM-10).  The stiffness deck is re-used unchanged up to its first *STEP; this script writes six unit
load steps on the engine rigid body at the pivot (moments 1 N m about X, Y, Z; forces 1000 N along X, Y, Z, global airframe axes)
with stress / reaction output, solves once per pose, and superposes the limit-load cases (exact for the linear model):
  LC1   thrust 500 N along the engine axis (no inertia relief: hover / lift-off, conservative);
  LC2F  stuck-pintle thrust 907.7 N (Combustion full-stroke failure case);  SF 1.0 yield / 1.5 ultimate;
  LC3   500 N + 1.5 g lateral inertia at the engine CG + engine moment I_pivot x 519 rad/s2 (GNC design limit) + LC-HS;
  GS    500 N + both servos at 8.4 V stall: engine moment 37.95 N m (mechanical.json actuator design loads, as built) + LC-HS;
  SR    500 N + runaway onto the 8 deg stop: 41.14 N m reacted by the bumper force F_b = M / |z_b| at the GM-10 bumper (engine side:
        force -F_b e_r at z_b; the bumper reaction on GM-10 is not in this model, it is a local hand check) + LC-HS;
  LC6   touchdown 10 g toward the nozzle + 3 g lateral at the engine CG, no thrust;
  LC-HS hose end reaction at the 8 deg stop for EI 0.184 N m2 (hose_end_reactions_v341_v1: F 31.2 N, M_pivot 2.55 N m) added to
        LC3, GS and SR with the force along the lateral load and the moment along the engine moment (worst orientation).
GS and SR: when the FE rod force is below the design rod force of mechanical.json (441 N centre, 552 N at 7 deg, 609 N at the stop)
the moment is scaled up to it (scale factor reported).  The SR case uses the beta -7 deg deck as the stop pose (no 8 deg deck).
Worst direction: moment / lateral-force directions scanned every 15 deg in the XY plane, the lateral force at 0/90/180/270 deg to the
moment.  Criteria (ENG-10): MS = Fty(T)/(SF_y sigma_vM) - 1 and Ftu(T)/(SF_u sigma_vM) - 1, SF 1.5 / 2.0 (LC2F 1.0 / 1.5), engmat
v1.2 tables at an ASSUMED part temperature: collar = max(60 C bay bound ASSUMED, case temperature at the collar band from the B1
thermal FE in flight); LC6 collar = the case soak maximum at the collar band (thermal FE); ring, frame, horns 60 C ASSUMED.
Nodal stresses within 1.5 mm of a rigid-body or fixed node set are constraint artefacts: reported, but the margins use the peaks
outside.  Outputs: per case and part the peak von Mises and MS, rod forces, pin/bearing loads, per-hole airframe screw loads (ICD-1).
Units: mm, N, MPa; moments in N m in the tables.

v1.1 (2026-10-13, after review of v1): GS and SR in v1 applied the both-servo moment magnitude (37.95 / 41.14 N m) in EVERY direction,
which puts up to 710-915 N into ONE rod (r_e 53.47 mm): more than any servo can push (design rod forces 441 N centre, 552 N at 7 deg,
609 N at the stop, mechanical.json actuator.design_loads).  v1.1 prescribes the rod forces instead: GS = both rods at +/-F_d(pose)
(4 sign corners; the stress is a convex function of the load vector, so the corners bound the box |F_i| <= F_d) + thrust + hose force in
8 directions; the engine moment is solved from the FE rod responses.  SR = engine at the stop, both rods at +/-609 N, the bumper force
F_b (horizontal, at z_b) solved so that the rods carry those forces, + the hose moment along the rod moment (raises F_b).  LC1, LC2F,
LC3, LC6 unchanged (LC3 keeps the loadcases v1 definition; its rod force 604-676 N exceeds the stall-limited design forces and is kept
as an envelope).  Added per part: the role (all gimbal parts are LOAD-BEARING metal: von Mises vs Fty(T)/SF_y and Ftu(T)/SF_u), the
peak 0.75-1.5 mm from the peak node (gradient check for unfilleted re-entrant corners), a status text, and the collar GM-01/02 margins
for the DESIGN CHANGE 6061-T6 -> 7075-T6 (same geometry; the FE keeps the 6061 modulus, 4 % lower than 7075).  v1 results are kept.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
FEA = HERE.parent
CADS = FEA.parent / "03-cad"
sys.path.insert(0, str(FEA / "src"))
import engmat  # noqa: E402

RUNS_STIFF = Path("/home/claude/work/mechanical/runs/stiff")
RUNS = Path("/home/claude/work/mechanical/runs/structural/s3d")
THERMAL_B1 = Path("/home/claude/work/mechanical/runs/thermal/DC-B1v3p99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB")
VERSION = "v1.1"
DATE = "2026-10-13"
POSES = {"centre": "centre_h3_hf4_T62.5_V5c", "betam7": "betam7_h3_hf4_T62.5_V5c"}
BODY_MAT = {"FRAME": "AL6061-T6", "RING": "AL6061-T6", "COLLAR": "AL6061-T6", "HORN1": "AL7075-T6", "HORN2": "AL7075-T6"}
PART_SETS = {"GM-08#0": "P_GM08_0", "GM-08#1": "P_GM08_1", "GM-09": "P_GM09_0", "GM-10": "P_GM10_0", "GM-13": "P_GM13_0",
             "GM-14": "P_GM14_0", "GM-03": "E_RING", "GM-01": "P_GM01_0", "GM-02": "P_GM02_0", "GM-16#0": "E_HORN1", "GM-16#1": "E_HORN2"}
PART_MAT = {k: ("AL7075-T6" if k.startswith("GM-16") else "AL6061-T6") for k in PART_SETS}
DESIGN_CHANGE_MAT = {"GM-01": "AL7075-T6", "GM-02": "AL7075-T6"}   # v1.1: collar halves 6061-T6 -> 7075-T6 (negative margins in v1/v1.1)
RING_MM = (0.75, 1.5)                                              # gradient check ring around the peak node
CONSTRAINT_SETS = ["N_ENGINE", "N_PIN_IN1", "N_PIN_IN2", "N_SEAT_IN1", "N_SEAT_IN2", "N_PIN_OUT1", "N_PIN_OUT2", "N_SEAT_OUT1",
                   "N_SEAT_OUT2", "N_LEYE1", "N_LEYE2", "N_HEYE1", "N_HEYE2", "N_SERVO1", "N_SERVO2", "N_FIX"]
EXCL_MM = 1.5
G0 = 9.80665
LOADS = {
    "thrust_N": (500.0, "Combustion max thrust (combustion.json / loadcases v1 LC1)"),
    "thrust_stuck_N": (907.7, "Combustion full-stroke stuck-pintle failure thrust (loadcases v2 LC2F)"),
    "lat_g_LC3": (1.5, "loadcases v1 LC3 lateral 1.5 g (ASSUMED envelope over the GNC flight max 0.61 g at the pivot)"),
    "alpha_dot_LC3": (519.0, "rad/s2 GNC design limit engine angular acceleration (loadcases v1 LC3)"),
    "M_GS_Nm": (37.95, "interfaces/mechanical.json actuator.design_loads M_engine_GS_Nm (both-servo stall 8.4 V, as built)"),
    "M_SR_Nm": (41.14, "interfaces/mechanical.json actuator.design_loads M_engine_stop_Nm (runaway onto the stop, as built)"),
    "F_rod_design_N": ({"centre": 441.0, "betam7": 552.0, "stop": 609.0}, "interfaces/mechanical.json actuator.design_loads"),
    "LC6_axial_g": (10.0, "loadcases v1 LC6 touchdown 10 g"),
    "LC6_lat_g": (3.0, "loadcases v1 LC6 touchdown 3 g lateral"),
    "HS_F_N": (31.2, "hose_end_reactions_v341_v1 EI 0.184 N m2 at the 8 deg stop (lead design case)"),
    "HS_M_Nm": (2.55, "hose_end_reactions_v341_v1 moment about the pivot"),
    "T_bay_C": (60.0, "ASSUMED bay-air / structure bound for the ring, frame and horns (no bay thermal model)"),
}
CASES = [  # id, title, SF_y, SF_u
    ("LC1", "Thrust 500 N along the engine axis", 1.5, 2.0),
    ("LC2F", "Stuck-pintle thrust 907.7 N", 1.0, 1.5),
    ("LC3", "500 N + 1.5 g lateral + I x 519 rad/s2 + hose", 1.5, 2.0),
    ("GS", "500 N + both-servo stall 37.95 N m + hose", 1.5, 2.0),
    ("SR", "500 N + runaway onto the stop 41.14 N m (bumper) + hose", 1.5, 2.0),
    ("LC6", "Touchdown 10 g axial + 3 g lateral", 1.5, 2.0),
]


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


# ============================================================================================ deck + solve
def strength_deck(base_inp, out_inp, unit_F=1000.0, unit_M=1000.0):
    """Copy the stiffness deck up to its first *STEP and append the six unit steps with field output."""
    txt = Path(base_inp).read_text()
    head = txt[:txt.index("*STEP")]
    meta = json.loads(Path(str(base_inp).replace(".inp", ".meta.json")).read_text())
    ref, rot = meta["ref"]["ENGINE"]
    steps = []
    for lab, node, dof, val in (("Mx", rot, 1, unit_M), ("My", rot, 2, unit_M), ("Mz", rot, 3, unit_M),
                                ("Fx", ref, 1, unit_F), ("Fy", ref, 2, unit_F), ("Fz", ref, 3, unit_F)):
        steps.append(f"*STEP\n*STATIC\n*CLOAD, OP=NEW\n{node}, {dof}, {val}\n*NODE PRINT, NSET=NREF\nU\n*NODE PRINT, NSET=N_FIX\nRF\n"
                     f"*EL FILE\nS\n*END STEP\n")
    Path(out_inp).parent.mkdir(parents=True, exist_ok=True)
    Path(out_inp).write_text(head + "".join(steps))
    return meta, ["Mx", "My", "Mz", "Fx", "Fy", "Fz"]


def run_ccx(inp, threads=1):
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads))
    t0 = time.time()
    r = subprocess.run(["ccx", "-i", Path(inp).stem], cwd=str(Path(inp).parent), env=env, capture_output=True, text=True)
    (Path(inp).parent / f"{Path(inp).stem}.log").write_text(r.stdout[-100000:] + "\n" + r.stderr)
    return {"seconds": round(time.time() - t0, 1), "errors": [l for l in r.stdout.splitlines() if "*ERROR" in l][:5], "returncode": r.returncode}


# ============================================================================================ readers
def read_nodes_elems(inp):
    """Nodes (id -> xyz) and C3D10 element connectivity per body ELSET E_<body>."""
    X, E, cur = {}, {}, None
    mode = None
    with open(inp) as f:
        for line in f:
            if line.startswith("*"):
                u = line.upper()
                if u.startswith("*NODE") and "PRINT" not in u and "FILE" not in u:
                    mode = "N"
                elif u.startswith("*ELEMENT") and "C3D10" in u:
                    mode = "E"
                    cur = re.search(r"ELSET=(\w+)", line).group(1)
                    E[cur] = []
                else:
                    mode = None
                continue
            if mode == "N":
                p = line.split(",")
                X[int(p[0])] = (float(p[1]), float(p[2]), float(p[3]))
            elif mode == "E":
                p = [int(v) for v in line.strip().rstrip(",").split(",") if v.strip()]
                E[cur].append(p)
    return X, {k: np.array(v) for k, v in E.items()}


def read_sets(inp, prefix=("N_", "P_", "R_")):
    sets, cur = {}, None
    with open(inp) as f:
        for line in f:
            if line.startswith("*"):
                m = re.match(r"\*(NSET|ELSET),\s*(NSET|ELSET)=(\w+)", line.strip(), re.I)
                cur = m.group(3) if m and m.group(3).startswith(prefix) else None
                if cur:
                    sets[cur] = []
                continue
            if cur:
                sets[cur] += [int(v) for v in line.strip().rstrip(",").split(",") if v.strip()]
    return {k: np.array(v) for k, v in sets.items()}


def read_springs(inp):
    """{elset: (type, n1, n2, dof or None, k)} from the *ELEMENT TYPE=SPRING* and *SPRING cards."""
    lines = Path(inp).read_text().splitlines()
    conn, out = {}, {}
    for i, l in enumerate(lines):
        m = re.match(r"\*ELEMENT,\s*TYPE=(SPRINGA|SPRING2),\s*ELSET=(\w+)", l, re.I)
        if m:
            p = [int(v) for v in lines[i + 1].split(",")]
            conn[m.group(2)] = (m.group(1).upper(), p[1], p[2])
        m = re.match(r"\*SPRING,\s*ELSET=(\w+)", l, re.I)
        if m:
            nm = m.group(1)
            if conn[nm][0] == "SPRINGA":
                out[nm] = conn[nm] + (None, float(lines[i + 2]))
            else:
                dof = int(lines[i + 1].split(",")[0])
                out[nm] = conn[nm] + (dof, float(lines[i + 2]))
    return out


def read_frd_stress(frd, n_max):
    """Per step nodal stress (n_max+1, 6) from the .frd."""
    out, blk, vals = [], None, []
    with open(frd) as fh:
        for line in fh:
            if line.startswith(" -4  "):
                blk = line[5:13].strip()
                vals = []
                continue
            if blk != "STRESS":
                continue
            if line.startswith(" -1"):
                vals.append(line)
            elif line.startswith(" -3"):
                a = np.zeros((n_max + 1, 6))
                ids = np.fromiter((int(l[3:13]) for l in vals), int, len(vals))
                arr = np.array([[float(l[13 + 12 * k:25 + 12 * k]) for k in range(6)] for l in vals])
                a[ids] = arr
                out.append(a)
                blk = None
    return out


def read_dat(dat):
    """Per step: {'U': {node: (ux, uy, uz)}, 'RF': {node: (fx, fy, fz)}}."""
    steps, cur, mode = [], None, None
    for line in open(dat):
        s = line.strip()
        if s.startswith("displacements"):
            cur = {"U": {}, "RF": {}}
            steps.append(cur)
            mode = "U"
            continue
        if s.startswith("forces"):
            mode = "RF"
            continue
        p = s.split()
        if mode and len(p) == 4:
            try:
                cur[mode][int(p[0])] = tuple(float(x) for x in p[1:])
            except ValueError:
                pass
    return steps


def vm6(S):
    sx, sy, sz, txy, tyz, tzx = (S[..., k] for k in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (txy ** 2 + tyz ** 2 + tzx ** 2))


# ============================================================================================ solve one pose
def solve_pose(pose, threads=1, force=False):
    tag = POSES[pose]
    base = RUNS_STIFF / tag / f"gk_{tag}.inp"
    wd = RUNS / pose
    inp = wd / f"s3d_{pose}.inp"
    res = wd / "unit.npz"
    if res.exists() and not force:
        return res
    meta, labels = strength_deck(base, inp)
    r = run_ccx(inp, threads=threads)
    if r["errors"] or r["returncode"] != 0:
        (wd / "run.json").write_text(json.dumps({"run": r}, indent=1))
        raise RuntimeError(f"ccx failed {pose}: {r}")
    X, E = read_nodes_elems(inp)
    n_max = max(X)
    S = read_frd_stress(wd / f"s3d_{pose}.frd", n_max)
    D = read_dat(wd / f"s3d_{pose}.dat")
    if len(S) != 6 or len(D) != 6:
        raise RuntimeError(f"{pose}: {len(S)} stress steps, {len(D)} dat steps")
    sets = read_sets(inp)
    sp = read_springs(inp)
    ids = np.array(sorted(X))
    XYZ = np.zeros((n_max + 1, 3))
    XYZ[ids] = np.array([X[i] for i in ids])
    ref_nodes = sorted(D[0]["U"])
    U_ref = np.array([[D[k]["U"][n] for n in ref_nodes] for k in range(6)])          # (6, n_ref, 3)
    fix_nodes = sorted(D[0]["RF"])
    RF = np.array([[D[k]["RF"][n] for n in fix_nodes] for k in range(6)])             # (6, n_fix, 3)
    np.savez_compressed(res, S=np.array(S, dtype=np.float32), XYZ=XYZ, ref_nodes=np.array(ref_nodes), U_ref=U_ref,
                        fix_nodes=np.array(fix_nodes), RF=RF, labels=np.array(labels),
                        sets=json.dumps({k: v.tolist() for k, v in sets.items()}),
                        E=json.dumps({k: v.tolist() for k, v in E.items()}),
                        springs=json.dumps(sp), meta=json.dumps({"stiff_meta": meta, "run": r, "inp": str(inp), "base": str(base),
                                                                  "base_sha256_16": sha16(base)}))
    for f_ in (wd / f"s3d_{pose}.frd",):            # 150 MB of nodal stresses: the unit responses are kept in unit.npz
        f_.unlink(missing_ok=True)
    return res


# ============================================================================================ post-processing
def mass_props():
    m = json.loads((CADS / "massprops_v3.4.1.json").read_text())
    w = m["states"]["wet"]["engine"]
    return {"m_kg": w["m_kg"], "cg_mm": w["cg_mm"], "I_pivot_kgm2": w["I_pivot_kgm2"], "src": "03-cad/massprops_v3.4.1.json states.wet.engine",
            "sha256_16": sha16(CADS / "massprops_v3.4.1.json")}


def collar_temperatures():
    """Case temperature at the collar band (outer r 30.5-31.8, z -10..+10 in the v3.4.1 frame) from the B1 rev B thermal FE."""
    meta = json.loads(next(THERMAL_B1.glob("*_meta.json")).read_text())
    dz = float(meta["case"]["monitors"]["head_top_r12"][1]) - 169.51342601773104
    z = np.load(THERMAL_B1 / "envelope_nodes.npz", allow_pickle=True)
    Xt, Et, pn = z["X"], z["E"], z["pn"]
    case_nodes = np.unique(Et[pn == "ENG-TC-01"])
    sel = case_nodes[(Xt[case_nodes, 0] > 30.5) & (np.abs(Xt[case_nodes, 1] - dz) <= 10.0)]
    Tmax = z["Tmax"][sel] - 273.15
    tmax = z["tmax"][sel]
    fr = np.load(THERMAL_B1 / "frames.npz", allow_pickle=True)          # S-AX frames (burn instants 0.5-21.65 s and the soak maxima)
    fl = [i for i, t in enumerate(fr["t_act"]) if t <= 21.651]
    T_flight = float(np.nanmax(fr["T"][fl][:, sel]) - 273.15)
    return {"n_nodes": int(len(sel)), "T_soak_max_C": float(Tmax.max()), "t_at_max_s": float(tmax[np.argmax(Tmax)]),
            "T_flight_max_C": T_flight, "dz_thermal_mm": dz, "run": THERMAL_B1.name,
            "src": "envelope_nodes.npz (per-node maximum over the run) and frames.npz (S-AX frames, burn instants)"}


def allow(mat, T_C):
    M = engmat.MATERIALS[mat]
    def tab(key):
        d = M[key]
        return float(np.interp(T_C, d["T_C"], d["v"]) / 1e6) if "T_C" in d else d["v"] / 1e6
    return tab("Fty"), tab("Ftu")


def unit_vectors(c, nM=1000.0, nF=1000.0):
    """Coefficient vector on the six unit steps from (M [N m], F [N]) at the pivot: unit M = 1000 N mm = 1 N m, unit F = 1000 N."""
    M, F = c
    return np.array([M[0] * 1000.0 / nM, M[1] * 1000.0 / nM, M[2] * 1000.0 / nM, F[0] / nF, F[1] / nF, F[2] / nF])


def case_loads(cid, pose_ab, mp, z_b, phi, rel, scale=1.0):
    """(M [N m], F [N]) on the engine at the pivot for case cid, moment/force direction phi (deg) and lateral-force offset rel (deg)."""
    a, b = (math.radians(x) for x in pose_ab)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    ea = Rx @ Ry @ np.array([0.0, 0.0, 1.0])                        # engine axis at the pose
    m, cg = mp["m_kg"], np.array(mp["cg_mm"]) / 1000.0
    I = np.array(mp["I_pivot_kgm2"])
    u = np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi)), 0.0])
    ul = np.array([math.cos(math.radians(phi + rel)), math.sin(math.radians(phi + rel)), 0.0])
    M, F = np.zeros(3), np.zeros(3)
    T, Ts = LOADS["thrust_N"][0], LOADS["thrust_stuck_N"][0]
    if cid == "LC1":
        F += T * ea
    elif cid == "LC2F":
        F += Ts * ea
    elif cid == "LC3":
        F += T * ea
        Fl = -m * LOADS["lat_g_LC3"][0] * G0 * ul                     # inertia force of a lateral acceleration +ul
        F += Fl
        M += np.cross(cg, Fl)
        Iu = float(u @ I @ u)
        M += Iu * LOADS["alpha_dot_LC3"][0] * u
        F += LOADS["HS_F_N"][0] * ul
        M += LOADS["HS_M_Nm"][0] * u
    elif cid == "GS":
        F += T * ea
        M += scale * LOADS["M_GS_Nm"][0] * u
        F += LOADS["HS_F_N"][0] * ul
        M += LOADS["HS_M_Nm"][0] * u
    elif cid == "SR":
        # the servo drives the engine into the stop with +Mb u through the rods; the bumper at r_b = z_b z (aft, z_b < 0) reacts with
        # F_b such that r_b x F_b = -Mb u, i.e. F_b = (Mb / z_b) (z x u), |F_b| = Mb / |z_b|.  Applying F_b at r_b to the engine makes
        # the rods react +Mb u (as in the real runaway) and the pins react -F_b; the bumper reaction on GM-10 is a hand check.
        F += T * ea
        Mb = scale * LOADS["M_SR_Nm"][0]
        zr = np.array([0.0, 0.0, z_b / 1000.0])
        Fb = (Mb / zr[2]) * np.cross(np.array([0.0, 0.0, 1.0]), u)
        assert np.linalg.norm(np.cross(zr, Fb) + Mb * u) < 1e-6 * max(1.0, Mb)
        F += Fb
        M += np.cross(zr, Fb)
        F += LOADS["HS_F_N"][0] * ul
        M += -LOADS["HS_M_Nm"][0] * u                                  # adds to the applied -Mb u (rods carry Mb + M_hs)
    elif cid == "LC6":
        Fa = -m * LOADS["LC6_axial_g"][0] * G0 * np.array([0.0, 0.0, 1.0])
        Fl = -m * LOADS["LC6_lat_g"][0] * G0 * ul
        F += Fa + Fl
        M += np.cross(cg, Fa + Fl)
    return M, F


def s3d_status(r):
    """Status text of a part row (lead 2026-10-13: a negative margin on a load-bearing part is a design change, never a pass)."""
    ok = (r["MS_yield"] is not None and r["MS_yield"] >= 0) and (r["MS_ult"] is None or r["MS_ult"] >= 0)
    if ok:
        t = "MS >= 0 (von Mises vs Fty(T)/SF_y and Ftu(T)/SF_u)."
    elif r.get("MS_yield_ring") is not None and r["MS_yield_ring"] >= 0 and (r.get("peak_over_ring") or 0) >= 1.3:
        t = ("NEGATIVE at the peak node, >= 0 at 0.75-1.5 mm (peak/ring %.2f): unfilleted re-entrant corner, mesh-dependent value. "
             "NOT a pass: the drawing needs a fillet and a filleted sub-model must confirm (closure)." % r["peak_over_ring"])
    else:
        t = "NEGATIVE on a load-bearing part: DESIGN CHANGE."
    dc = r.get("design_change")
    if dc:
        okd = dc["MS_yield"] >= 0 and dc["MS_ult"] >= 0
        t += (" Design change %s: MS_y %.3f, MS_u %.3f at the peak node%s." %
              (dc["material"], dc["MS_yield"], dc["MS_ult"], "" if okd else (" (ring %.3f)" % dc["MS_yield_ring"] if dc["MS_yield_ring"] is not None else "")))
        if dc.get("T_max_C") is not None and r["T_C"] > dc["T_max_C"]:
            t += " Part temperature above the %s usable limit %.0f C (engmat): TO-VERIFY." % (dc["material"], dc["T_max_C"])
    return t


def analyse(pose, mp, temps, threads=1):
    z = np.load(solve_pose(pose, threads=threads), allow_pickle=True)
    S_u = z["S"].astype(np.float64)                                   # (6, n+1, 6)
    XYZ = z["XYZ"]
    sets = {k: np.array(v) for k, v in json.loads(str(z["sets"])).items()}
    E = {k: np.array(v) for k, v in json.loads(str(z["E"])).items()}
    sp = json.loads(str(z["springs"]))
    meta = json.loads(str(z["meta"]))
    smeta = meta["stiff_meta"]
    pose_ab = (smeta["alpha"], smeta["beta"])
    ref_nodes = list(z["ref_nodes"])
    U_ref = z["U_ref"]
    fix_nodes = z["fix_nodes"]
    RF = z["RF"]
    # element -> node maps per part
    elem_nodes = {}
    for body, arr in E.items():
        for row in arr:
            elem_nodes[int(row[0])] = row[1:]
    part_nodes = {}
    for pname, es in PART_SETS.items():
        if es.startswith("E_"):
            part_nodes[pname] = np.unique(E[es][:, 1:])
        else:
            part_nodes[pname] = np.unique(np.concatenate([elem_nodes[int(e)] for e in sets[es]]))
    # exclusion around constraint sets
    from scipy.spatial import cKDTree
    cn = np.unique(np.concatenate([sets[s] for s in CONSTRAINT_SETS if s in sets]))
    tree = cKDTree(XYZ[cn])
    # bumper height from the GM-10 nodes (mid-height of the lower ring)
    z10 = XYZ[part_nodes["GM-10"], 2]
    z_b = 0.5 * (z10.min() + z10.max())
    # rod and pin springs
    ridx = {n: i for i, n in enumerate(ref_nodes)}
    def rod_unit(name):
        typ, n1, n2, dof, k = sp[name]
        e = XYZ[n2] - XYZ[n1]
        e = e / np.linalg.norm(e)
        return np.array([k * (U_ref[s, ridx[n2]] - U_ref[s, ridx[n1]]) @ e for s in range(6)])     # tension +
    rods = {nm: rod_unit(nm) for nm in ("S_ROD1", "S_ROD2")}
    def pin_unit(prefix):
        out = np.zeros((6, 3))
        for d in (1, 2, 3):
            typ, n1, n2, dof, k = sp[f"{prefix}_{d}"]
            out[:, dof - 1] = [k * (U_ref[s, ridx[n2]][dof - 1] - U_ref[s, ridx[n1]][dof - 1]) for s in range(6)]
        return out
    pins = {nm: pin_unit(nm) for nm in ("S_IN1", "S_IN2", "S_OUT1", "S_OUT2")}
    pin_axis = {"S_IN1": 1, "S_IN2": 1, "S_OUT1": 0, "S_OUT2": 0}      # inner pins along Y, outer along X
    # airframe screw groups (16 radial holes: az 22.5 + 45 k, upper GM-09 / lower GM-10)
    P = XYZ[fix_nodes]
    az = (np.degrees(np.arctan2(P[:, 1], P[:, 0])) - 22.5) % 360.0
    k_az = np.round(az / 45.0).astype(int) % 8
    upper = P[:, 2] > -30.0
    hole = k_az + 8 * (~upper)
    # node -> part map for reporting the location
    results = {"pose": pose, "alpha_beta_deg": pose_ab, "z_bumper_mm": round(float(z_b), 2), "cases": {}}
    phis = np.arange(0.0, 360.0, 15.0)
    Rm = np.array([[rods["S_ROD1"][0], rods["S_ROD1"][1]], [rods["S_ROD2"][0], rods["S_ROD2"][1]]])   # N per N m about X, Y
    Rf = np.array([[rods["S_ROD1"][3], rods["S_ROD1"][4]], [rods["S_ROD2"][3], rods["S_ROD2"][4]]])   # N per 1000 N along X, Y
    a_, b_ = (math.radians(x) for x in pose_ab)
    Rx_ = np.array([[1, 0, 0], [0, math.cos(a_), -math.sin(a_)], [0, math.sin(a_), math.cos(a_)]])
    Ry_ = np.array([[math.cos(b_), 0, math.sin(b_)], [0, 1, 0], [-math.sin(b_), 0, math.cos(b_)]])
    ea_ = Rx_ @ Ry_ @ np.array([0.0, 0.0, 1.0])

    def rod_bounded(cid):
        """v1.1 GS / SR combos with the two rod forces prescribed at +/-F_d (box corners) and the hose force in 8 directions."""
        fd = LOADS["F_rod_design_N"][0]["stop" if cid == "SR" else pose]
        out_c, info_c = [], []
        for s1 in (1, -1):
            for s2 in (1, -1):
                tgt = np.array([s1 * fd, s2 * fd])
                for hd in range(0, 360, 45):
                    uh = np.array([math.cos(math.radians(hd)), math.sin(math.radians(hd)), 0.0])
                    Fk = LOADS["thrust_N"][0] * ea_ + LOADS["HS_F_N"][0] * uh
                    ck = unit_vectors((np.zeros(3), Fk))
                    r0 = np.array([rods["S_ROD1"] @ ck, rods["S_ROD2"] @ ck])
                    if cid == "GS":
                        mxy = np.linalg.solve(Rm, tgt - r0)
                        M = np.array([mxy[0], mxy[1], 0.0])
                        F = Fk
                        extra = {}
                    else:
                        # bumper force (fbx, fby, 0) at r_b = (0, 0, z_b): moment (-z_b fby, z_b fbx) / 1000 N m; the hose moment
                        # along the rod moment is reacted by the bumper as well
                        m_rod = np.linalg.solve(Rm, tgt)
                        u_m = np.array([m_rod[0], m_rod[1], 0.0]) / max(np.linalg.norm(m_rod), 1e-9)
                        Mh = LOADS["HS_M_Nm"][0] * u_m
                        ch = unit_vectors((Mh, np.zeros(3)))
                        r0 = r0 + np.array([rods["S_ROD1"] @ ch, rods["S_ROD2"] @ ch])
                        G = Rm @ np.array([[0.0, -z_b / 1000.0], [z_b / 1000.0, 0.0]]) + Rf / 1000.0
                        fb = np.linalg.solve(G, tgt - r0)
                        Fb = np.array([fb[0], fb[1], 0.0])
                        M = Mh + np.array([-z_b * fb[1], z_b * fb[0], 0.0]) / 1000.0
                        F = Fk + Fb
                        extra = {"F_bumper_N": round(float(np.linalg.norm(Fb)), 1)}
                    c = unit_vectors((M, F))
                    chk = np.array([rods["S_ROD1"] @ c, rods["S_ROD2"] @ c])
                    assert np.allclose(chk, tgt, atol=1e-3 * fd), (cid, chk, tgt)
                    out_c.append((f"rods {s1 * fd:+.0f}/{s2 * fd:+.0f} N", float(hd), M, F, c))
                    info_c.append(dict(extra, M_engine_Nm=round(float(np.linalg.norm(M[:2])), 2)))
        return out_c, info_c

    for cid, title, sfy, sfu in CASES:
        rels = [0.0, 90.0, 180.0, 270.0] if cid in ("LC3", "LC6") else [0.0]
        ph = phis if cid in ("LC3", "LC6") else [0.0]
        scale = 1.0
        rod_from_moment_N = None
        bounded_info = None
        if cid in ("GS", "SR"):
            # v1 diagnostic kept: rod force of the as-built moment applied along one lever axis (not physically reachable)
            Md = LOADS["M_SR_Nm" if cid == "SR" else "M_GS_Nm"][0]
            fmax = 0.0
            for p_ in phis:
                u_ = np.array([math.cos(math.radians(p_)), math.sin(math.radians(p_)), 0.0])
                c = unit_vectors((Md * u_, np.zeros(3)))
                fmax = max(fmax, max(abs(float(rods[r] @ c)) for r in rods))
            rod_from_moment_N = fmax
        best = {}
        if cid in ("GS", "SR"):
            combos, bounded_info = rod_bounded(cid)
        else:
            combos = []
            for p_ in ph:
                for rl in rels:
                    M, F = case_loads(cid, pose_ab, mp, z_b, p_, rl, scale)
                    combos.append((p_, rl, M, F, unit_vectors((M, F))))
        C = np.array([c[4] for c in combos])                        # (n_combo, 6)
        for pname, nodes in part_nodes.items():
            mat = PART_MAT[pname]
            Tp = temps["collar_LC6" if (cid == "LC6" and pname in ("GM-01", "GM-02")) else
                       ("collar" if pname in ("GM-01", "GM-02") else "bay")]
            fty, ftu = allow(mat, Tp)
            Sn = S_u[:, nodes, :]                                     # (6, n, 6)
            d, _ = tree.query(XYZ[nodes], k=1)
            out_mask = d > EXCL_MM
            vmax_all, vmax_out, arg_all, arg_out = -1.0, -1.0, None, None
            for j in range(len(C)):
                Sc = np.tensordot(C[j], Sn, axes=(0, 0))               # (n, 6)
                v = vm6(Sc)
                i_all = int(np.argmax(v))
                if v[i_all] > vmax_all:
                    vmax_all, arg_all = float(v[i_all]), (j, int(nodes[i_all]))
                if out_mask.any():
                    vo = np.where(out_mask, v, -1.0)
                    i_o = int(np.argmax(vo))
                    if vo[i_o] > vmax_out:
                        vmax_out, arg_out = float(vo[i_o]), (j, int(nodes[i_o]))
            jo = arg_out[0]
            # v1.1 gradient check: the largest von Mises 0.75-1.5 mm from the peak node in the governing combination (an unfilleted
            # re-entrant corner shows a steep drop; the corner value is mesh-dependent and the drawing must carry a fillet)
            v_jo = vm6(np.tensordot(C[jo], Sn, axes=(0, 0)))
            dd = np.linalg.norm(XYZ[nodes] - XYZ[arg_out[1]], axis=1)
            ring = (dd >= RING_MM[0]) & (dd <= RING_MM[1]) & out_mask
            v_ring = float(v_jo[ring].max()) if ring.any() else None
            ms_y = fty / (sfy * vmax_out) - 1.0 if vmax_out > 0 else None
            ms_u = ftu / (sfu * vmax_out) - 1.0 if vmax_out > 0 else None
            ms_ring = (fty / (sfy * v_ring) - 1.0) if v_ring else None
            row = {"material": mat, "role": "LOAD-BEARING (metal: von Mises vs Fty(T)/SF_y and Ftu(T)/SF_u)", "T_C": Tp,
                   "Fty_MPa": round(fty, 1), "Ftu_MPa": round(ftu, 1),
                   "vm_peak_all_MPa": round(vmax_all, 2), "vm_peak_outside_MPa": round(vmax_out, 2),
                   "at_xyz_mm": [round(float(x), 2) for x in XYZ[arg_out[1]]],
                   "phi_deg": combos[jo][0], "rel_deg": combos[jo][1],
                   "MS_yield": round(ms_y, 3) if ms_y is not None else None,
                   "MS_ult": round(ms_u, 3) if ms_u is not None else None,
                   "MS_yield_all_nodes": round(fty / (sfy * vmax_all) - 1.0, 3) if vmax_all > 0 else None,
                   "vm_ring_0p75_1p5mm_MPa": round(v_ring, 2) if v_ring else None,
                   "MS_yield_ring": round(ms_ring, 3) if ms_ring is not None else None,
                   "peak_over_ring": round(vmax_out / v_ring, 2) if v_ring else None}
            if pname in DESIGN_CHANGE_MAT:
                m2 = DESIGN_CHANGE_MAT[pname]
                f2y, f2u = allow(m2, Tp)
                row["design_change"] = {"material": m2, "Fty_MPa": round(f2y, 1), "Ftu_MPa": round(f2u, 1),
                                        "MS_yield": round(f2y / (sfy * vmax_out) - 1.0, 3), "MS_ult": round(f2u / (sfu * vmax_out) - 1.0, 3),
                                        "MS_yield_ring": round(f2y / (sfy * v_ring) - 1.0, 3) if v_ring else None,
                                        "T_max_C": engmat.MATERIALS[m2].get("T_max_C", {}).get("v")}
            row["status"] = s3d_status(row)
            best[pname] = row
        # rods, pins, holes (max over the scan)
        rod_max = {r: float(np.max(np.abs(C @ rods[r]))) for r in rods}
        pin_max = {}
        for pn_, U6 in pins.items():
            Fp = C @ U6                                               # (n_combo, 3)
            ax_ = pin_axis[pn_]
            rad = np.sqrt(np.sum(np.delete(Fp, ax_, axis=1) ** 2, axis=1))
            pin_max[pn_] = {"radial_N": round(float(rad.max()), 1), "axial_N": round(float(np.abs(Fp[:, ax_]).max()), 1)}
        Fh = np.zeros((len(C), 16, 3))
        for hh in range(16):
            sel = hole == hh
            Fh[:, hh, :] = np.tensordot(C, RF[:, sel, :].sum(axis=1), axes=(1, 0))
        hz = np.array([22.5 + 45.0 * (hh % 8) for hh in range(16)])
        er = np.column_stack([np.cos(np.radians(hz)), np.sin(np.radians(hz)), np.zeros(16)])
        Fr = np.einsum("chk,hk->ch", Fh, er)                          # outward reaction on the ring = screw tension (+)
        Fs = np.linalg.norm(Fh - Fr[:, :, None] * er[None], axis=2)
        results["cases"][cid] = {"title": title, "SF_yield": sfy, "SF_ult": sfu, "moment_scale_to_design_rod_force": round(scale, 3),
                                 "rod_force_of_design_moment_alone_N": None if rod_from_moment_N is None else round(rod_from_moment_N, 1),
                                 "rod_forces_prescribed_N": (LOADS["F_rod_design_N"][0]["stop" if cid == "SR" else pose]
                                                             if cid in ("GS", "SR") else None),
                                 "engine_moment_Nm_range": ([min(b["M_engine_Nm"] for b in bounded_info), max(b["M_engine_Nm"] for b in bounded_info)]
                                                            if bounded_info else None),
                                 "bumper_force_N_max": (max(b.get("F_bumper_N", 0.0) for b in bounded_info) if (bounded_info and cid == "SR") else None),
                                 "n_directions": len(C), "parts": best,
                                 "rod_force_max_N": {k: round(v, 1) for k, v in rod_max.items()},
                                 "pin_bearing_max_N": pin_max,
                                 "airframe_screws": {"tension_max_N": round(float(Fr.max()), 1), "compression_max_N": round(float(-Fr.min()), 1),
                                                     "shear_max_N": round(float(Fs.max()), 1),
                                                     "sum_check_N": [round(float(x), 2) for x in Fh.sum(axis=1)[0]]}}
    return results, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["solve", "post"])
    ap.add_argument("--poses", default="centre,betam7")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    poses = [p for p in a.poses.split(",") if p]
    if a.cmd == "solve":
        for p in poses:
            t1 = time.time()
            solve_pose(p, threads=a.threads, force=a.force)
            print(f"{p}: solved in {time.time() - t1:.1f} s", flush=True)
    else:
        mp = mass_props()
        ct = collar_temperatures()
        temps = {"bay": LOADS["T_bay_C"][0], "collar": max(LOADS["T_bay_C"][0], ct["T_flight_max_C"] or -273.0),
                 "collar_LC6": max(LOADS["T_bay_C"][0], ct["T_soak_max_C"])}
        out = {"id": "s3d_gimbal_strength", "version": VERSION, "date": DATE, "owner": "mechanical", "script": "04-fea/structural/gimbal_strength.py",
               "mass_props": mp, "collar_temperature": ct, "temperatures_used_C": temps,
               "loads": {k: {"v": v[0], "src": v[1]} for k, v in LOADS.items()}, "exclusion_mm": EXCL_MM, "poses": {}}
        for p in poses:
            r, meta = analyse(p, mp, temps, threads=a.threads)
            r["run"] = meta["run"]
            r["base_deck"] = meta["base"]
            r["base_sha256_16"] = meta["base_sha256_16"]
            out["poses"][p] = r
        res = HERE / "results" / f"s3d_results_{VERSION}.json"
        res.parent.mkdir(exist_ok=True)
        res.write_text(json.dumps(out, indent=1, default=float))
        rows = []
        for p, r in out["poses"].items():
            for cid, c in r["cases"].items():
                for part, b in c["parts"].items():
                    dc = b.get("design_change") or {}
                    rows.append([p, cid, part, b["material"], b["T_C"], b["vm_peak_outside_MPa"], b["vm_peak_all_MPa"], b["Fty_MPa"], b["Ftu_MPa"],
                                 c["SF_yield"], c["SF_ult"], b["MS_yield"], b["MS_ult"], b.get("vm_ring_0p75_1p5mm_MPa"), b.get("MS_yield_ring"),
                                 dc.get("material", ""), dc.get("MS_yield", ""), dc.get("MS_ult", ""), b["phi_deg"], b["rel_deg"], b["at_xyz_mm"],
                                 b.get("status", "")])
        with open(HERE / "results" / f"s3d_margin_table_{VERSION}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["pose", "case", "part", "material", "T_C", "vm_outside_MPa", "vm_all_MPa", "Fty_MPa", "Ftu_MPa", "SF_y", "SF_u", "MS_y", "MS_u",
                        "vm_ring_0p75_1p5mm_MPa", "MS_y_ring", "design_change_material", "MS_y_design_change", "MS_u_design_change",
                        "combo", "hose_or_rel_deg", "at_xyz_mm", "status"])
            w.writerows(rows)
        print(res)
    print(f"done {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
