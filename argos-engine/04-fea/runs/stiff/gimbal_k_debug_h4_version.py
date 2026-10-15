"""Gimbal axis stiffness about the pivot -- CalculiX static FE of the as-built CAD v3.3 load path (04-fea/stiffness, v1, 2026-10-12, Mechanical).

Question (lead 2026-10-12): rotational stiffness of the gimballed engine about each gimbal axis at the pivot (N m/rad), at the
centre and at 7 deg, including the rods, horns, servo mounts and their attachment, the gimbal ring and the bearings.  It replaces
the ASSUMED 2e6 N/m linkage stiffness in GNC's control-stability check.

Model (units mm, N, MPa):
  meshed (C3D10 from the CAD solids, posed): FRAME = yoke posts GM-08 x2 + upper ring GM-09 + lower ring GM-10 + TVC brackets
  GM-13/14 fused (bolted joints treated as bonded); RING = GM-03; COLLAR = GM-01 + GM-02 fused (clamp treated as bonded);
  HORN1/2 = GM-16.
  rigid: ENGINE (collar bore nodes; the case is rigid, ASSUMED), each SERVO case incl. gear train (bracket ear-screw holes and ear
  faces + horn spline bore), each joint stud/screw (lever cheek M4 hole + flange face; horn eye hole + seat + washer face), the
  inner pins (collar pin bores) and the bearing outer rings (ring and post 608 seats).
  springs: rod chain i = SPRINGA lever eye -> horn eye (pushrod FE + 2 GE 5 E + stud + shoulder screw in series, rod_k.py);
  608 bearing + pin = SPRING2 per global direction (radial / axial, ANALYTIC Palmgren tangent stiffness at the thrust preload).
  boundary: airframe rigid at the 16 radial M5 holes of GM-09/GM-10 (ASSUMED rigid airframe; Lauty's stiffness unknown).
  loads: unit moments (1 N m) on the engine rotation node about X (alpha, outer axis) and Y (beta, inner axis); servo held at
  its commanded angle (servo internal compliance K_s from electronics.json is added in series in a second run: the total).
Outputs: compliance / stiffness 2x2 about (X, Y), strain-energy split per component (where the compliance sits), mesh study.
"""
from __future__ import annotations
import sys, json, math, time, argparse, hashlib, re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CAD = HERE.parents[1] / "03-cad" / "src"
sys.path.insert(0, str(CAD))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import fe_util as fu
import engmat
sys.path.insert(0, str(CAD / "calcs"))
import actuator_loads

RUNS = Path("/home/claude/work/mechanical/runs/stiff")
E_AL6061 = engmat.prop("AL6061-T6", "E", 20.0) / 1e6
E_AL7075 = engmat.prop("AL7075-T6", "E") / 1e6
NU_AL = 0.33


def bearing_springs(F_thrust_N=62.5):
    """608-2RS radial tangent stiffness (Palmgren/Stribeck, rigid housings) at the radial load from the engine thrust, in series
    with the 8 mm 17-4PH pin cantilever (root compliance by +0.5 d effective length).  ANALYTIC; ball set ASSUMED 7 x 3.969 mm."""
    Z, Dw = 7, 3.969
    Fr = max(F_thrust_N, 1.0) / 2.0                    # two bearings share the thrust
    Q = 5.0 * Fr / Z
    d = 4.36e-4 * (Q ** 2 / Dw) ** (1.0 / 3.0)          # mm (point contact, Palmgren)
    k_b = 1.5 * Fr / d                                  # N/mm tangent
    E, I = 196e3, math.pi * 8.0 ** 4 / 64.0
    k_pin_in = 3 * E * I / (6.0 + 4.0) ** 3             # inner pin: boss face r 39.5 -> bearing centre 45.5, +0.5 d root
    k_pin_out = 3 * E * I / (5.5 + 4.0) ** 3            # outer pin: ring boss face r 49 -> 54.5
    k_ax = 5.0e3                                        # N/mm axial, ASSUMED after the axial play is taken up (608 C0 axial play ~ 0.05-0.1 mm)
    return {"F_thrust_N": F_thrust_N, "Fr_per_bearing_N": Fr, "delta_um": d * 1e3, "k_608_radial_N_mm": k_b,
            "k_pin_in_N_mm": k_pin_in, "k_pin_out_N_mm": k_pin_out,
            "k_in_radial": 1.0 / (1.0 / k_b + 1.0 / k_pin_in), "k_out_radial": 1.0 / (1.0 / k_b + 1.0 / k_pin_out), "k_axial": k_ax,
            "tag": "ANALYTIC Palmgren delta_r = 4.36e-4 (Q^2/Dw)^(1/3) mm, Q = 5 Fr/Z (Harris, Rolling Bearing Analysis); 608 ball set 7 x 5/32 in ASSUMED (verify); "
                   "radial clearance (dead band) excluded; axial 5e3 N/mm ASSUMED"}


def chain_spring(rod, k_GE=1.0e5, Lr=2.5):
    """Series spring of one pushrod chain along the rod line (N/mm): pushrod FE (rod_k.py) + 2 GE 5 E + lever stud + horn screw.
    k_GE: N/mm per spherical plain bearing after the clearance, ASSUMED 1e5 (range 5e4-3e5); Lr: root allowance of the 5 mm
    shoulder cantilever (2.5 = +0.5 d, conservative; 0 = rigid clamp)."""
    E, G = 196e3, 75.4e3
    d, L = 5.0, 4.5                                           # shoulder 5 mm, GE centre 4.5 mm from the clamp face
    I, A = math.pi * d ** 4 / 64, math.pi * d ** 2 / 4
    c_pin = (L + Lr) ** 3 / (3 * E * I) + L / (0.9 * G * A)   # cantilever (bending with root allowance + shear)
    c = 1.0 / rod["k_N_mm"] + 2.0 / k_GE + 2.0 * c_pin
    return {"k_chain_N_mm": 1.0 / c, "k_rod_N_mm": rod["k_N_mm"], "k_GE_N_mm": k_GE, "k_stud_or_screw_N_mm": 1.0 / c_pin,
            "split_compliance": {"rod": (1.0 / rod["k_N_mm"]) / c, "GE_x2": (2.0 / k_GE) / c, "stud+screw": 2 * c_pin / c},
            "tag": "pushrod FE (rod_k.py); GE 5 E radial 1e5 N/mm ASSUMED (steel/steel conformal contact, after clearance); "
                   "stud/screw: 5 mm shoulder cantilever 4.5 mm + 0.5 d root allowance (preloaded stack ignored: conservative)"}


# ----------------------------------------------------------------------------------------------- geometry + mesh
def build_cad():
    import build
    t0 = time.time()
    P, S, reg, log = build.build(include=("engine", "gimbal"), iterate_cg=True)
    return P, S, reg, round(time.time() - t0, 1)


def posed_bodies(P, S, reg, a, b):
    import build, parts_gimbal
    from geom import apply
    import tvc_kinematics as tk
    inst = {f"{pn}#{i}": (grp, shp) for pn, i, grp, shp, body in build.posed_instances(reg, S, a, b)}
    fr = parts_gimbal.tvc_pose_frames(S, a, b)
    parts = {"FRAME": ["ENG-GM-08#0", "ENG-GM-08#1", "ENG-GM-09#0", "ENG-GM-10#0", "ENG-GM-13#0", "ENG-GM-14#0"],
             "RING": ["ENG-GM-03#0"], "COLLAR": ["ENG-GM-01#0", "ENG-GM-02#0"], "HORN1": ["ENG-GM-16#0"], "HORN2": ["ENG-GM-16#1"]}
    bodies = {k: ([inst[n][1] for n in v], v) for k, v in parts.items()}      # touching parts meshed conformingly (bonded joints)
    g = S["tvc"]
    poses = tk.pose_all(g, a, b)
    T = {"engine": build.group_T("engine", a, b), "ring": build.group_T("ring", a, b),
         "horn": {sv["i"]: fr[sv["i"]]["horn"] for sv in g["servos"]}}
    return bodies, T, poses, fr


def _fuse(shapes):
    s = shapes[0]
    for x in shapes[1:]:
        s = s.fuse(x)
    try:
        s = s.clean()
    except Exception:
        pass
    return s


def local(X, T):
    Ti = np.linalg.inv(T)
    return X @ Ti[:3, :3].T + Ti[:3, 3]


def dist_line(X, p0, d):
    d = np.asarray(d, float) / np.linalg.norm(d)
    v = X - np.asarray(p0, float)
    t = v @ d
    return np.linalg.norm(v - np.outer(t, d), axis=1), t


# ----------------------------------------------------------------------------------------------- model
class Model:
    def __init__(self):
        self.X = []            # list of node coordinate arrays per body
        self.offs = {}
        self.conn = {}
        self.n = 0
        self.extra = []        # (id, xyz)
        self.mat = {}
        self.part = {}

    def add_body(self, name, X, conn, E):
        self.offs[name] = self.n + 1                 # CalculiX ids start at 1
        self.X.append(X)
        self.conn[name] = conn
        self.mat[name] = E
        self.n += len(X)

    def gid(self, name, idx):
        return self.offs[name] + np.asarray(idx)

    def new_node(self, xyz):
        self.n += 1
        self.extra.append((self.n, np.asarray(xyz, float)))
        return self.n


def make_model(P, S, reg, a, b, h, kchain, ksprings, tag, workdir, chains_series=None):
    import tvc_kinematics as tk
    bodies, T, poses, fr = posed_bodies(P, S, reg, a, b)
    g = S["tvc"]
    sizes = {"FRAME": (h, h / 5.0), "RING": (0.8 * h, h / 6.0), "COLLAR": (0.6 * h, h / 8.0), "HORN1": (0.5 * h, h / 8.0), "HORN2": (0.5 * h, h / 8.0)}
    M = Model()
    stats = {}
    for name in ("FRAME", "RING", "COLLAR", "HORN1", "HORN2"):
        t0 = time.time()
        shapes, pnames = bodies[name]
        X, conn, part = fu.mesh_multi(shapes, sizes[name][0], sizes[name][1], name=f"{tag}_{name}", workdir=workdir)
        vol = fu.tet_volumes(X, conn)
        if (vol <= 0).any():
            raise RuntimeError(f"{name}: {int((vol <= 0).sum())} inverted tets")
        nc, lab = fu.components(conn, len(X))
        M.add_body(name, X, conn, E_AL7075 if name.startswith("HORN") else E_AL6061)
        M.part[name] = (part, pnames)
        stats[name] = {"nodes": int(len(X)), "tets": int(len(conn)), "volume_mm3": float(vol.sum()), "t_mesh_s": round(time.time() - t0, 1),
                       "connected_components": int(nc), "part_volumes_mm3": {pn: float(vol[part == q].sum()) for q, pn in enumerate(pnames)},
                       "cad_volumes_mm3": {pn: float(sh.Volume()) for pn, sh in zip(pnames, shapes)}}
        if nc != 1:
            raise RuntimeError(f"{name}: mesh has {nc} disconnected pieces (parts not touching): {stats[name]}")
    tol = 0.06
    sets = {}

    def sel(name, mask):
        return M.gid(name, np.nonzero(mask)[0])

    # ---------------- ENGINE rigid body: collar bore r 31.25 (engine-local)
    Xc = local(M.X[list(M.offs).index("COLLAR")], T["engine"])
    rc_in = P["collar_r"]["v"][0] * 1e3
    sets["ENGINE"] = sel("COLLAR", (np.abs(np.hypot(Xc[:, 0], Xc[:, 1]) - rc_in) < tol) & (np.abs(Xc[:, 2]) <= 10.01))
    # ---------------- inner pins A_j (collar pin bores, engine-local, axis Y)
    R = T["engine"][:3, :3]
    for j, sy in ((1, 1.0), (2, -1.0)):
        m = (np.abs(np.hypot(Xc[:, 0], Xc[:, 2]) - 4.0) < tol) & (sy * Xc[:, 1] > 32.9) & (sy * Xc[:, 1] < 39.6)
        sets[f"PIN_IN{j}"] = sel("COLLAR", m)
    # ---------------- lever eyes (engine-local; stud axis along s*et through P_l0)
    t_ch0, t_ch1 = S["tvc_cheek_t"]
    for sv in g["servos"]:
        i, s = sv["i"], sv["s"]
        d = s * sv["et"]
        Q0 = sv["P_l0"] - d * (d @ sv["P_l0"]) + 0.0   # point on the axis with tau = 0
        rr, tau = dist_line(Xc, sv["P_l0"], d)
        tau = tau + g["t_eye"]                          # tau measured from the servo mid-plane: P_l0 sits at tau = t_eye
        hole = (np.abs(rr - 1.65) < tol) & (tau > t_ch0 - 0.02) & (tau < t_ch1 + 0.02)
        face = (np.abs(tau - t_ch0) < 0.03) & (rr <= 3.76)
        sets[f"LEYE{i}"] = sel("COLLAR", hole | face)
    # ---------------- ring seats B_j and outer pin bores C_k (ring-local)
    Xr = local(M.X[list(M.offs).index("RING")], T["ring"])
    rr_in, rr_out = [x * 1e3 for x in P["ring_r"]["v"]]
    for j, sy in ((1, 1.0), (2, -1.0)):
        rad = np.hypot(Xr[:, 0], Xr[:, 2])
        m = ((np.abs(rad - 11.0) < tol) & (sy * Xr[:, 1] > rr_in + 1.0 - 0.02) & (sy * Xr[:, 1] < rr_out + 0.02)) | \
            ((np.abs(sy * Xr[:, 1] - (rr_in + 1.0)) < 0.03) & (rad >= 7.45) & (rad <= 11.05))
        sets[f"SEAT_IN{j}"] = sel("RING", m)
    for k, sx in ((1, 1.0), (2, -1.0)):
        m = (np.abs(np.hypot(Xr[:, 1], Xr[:, 2]) - 4.0) < tol) & (sx * Xr[:, 0] > rr_in - 1.0) & (sx * Xr[:, 0] < rr_out + 0.02)
        sets[f"PIN_OUT{k}"] = sel("RING", m)
    # ---------------- frame: post seats D_k, airframe holes, servo ear holes/faces
    Xf = M.X[list(M.offs).index("FRAME")]
    r_brg_out = rr_out + 2.0
    for k, sx in ((1, 1.0), (2, -1.0)):
        rad = np.hypot(Xf[:, 1], Xf[:, 2])
        m = ((np.abs(rad - 11.0) < tol) & (sx * Xf[:, 0] > r_brg_out - 0.02) & (sx * Xf[:, 0] < r_brg_out + 7.02)) | \
            ((np.abs(sx * Xf[:, 0] - r_brg_out) < 0.03) & (rad >= 7.45) & (rad <= 11.05))
        sets[f"SEAT_OUT{k}"] = sel("FRAME", m)
    R_frame = S["R_frame"]
    fix = np.zeros(len(Xf), bool)
    for (z0, z1) in (S["z_upper_ring"], S["z_lower_ring"]):
        zm = 0.5 * (z0 + z1)
        for kk in range(8):
            az = math.radians(22.5 + 45.0 * kk)
            dvec = np.array([math.cos(az), math.sin(az), 0.0])
            rr, tt = dist_line(Xf, np.array([0.0, 0.0, zm]), dvec)
            fix |= (np.abs(rr - 2.1) < tol) & (tt > R_frame - 11.0 - 0.02)
    sets["FIX"] = sel("FRAME", fix)
    t_ear = g["H"] / 2.0 - 13.5
    z_s = g["z_s"]
    for sv in g["servos"]:
        i, s = sv["i"], sv["s"]
        m = np.zeros(len(Xf), bool)
        et_s = s * sv["et"]
        for zz in (z_s + 34.9, z_s - 14.6):
            for du in (-5.0, 5.0):
                p = (g["u_sh"] + du) * sv["eu"] + 0.0 * sv["et"] + zz * sv["ez"]
                rr, tt = dist_line(Xf, p, et_s)          # tt = coordinate along s*et from the servo mid-plane
                m |= (np.abs(rr - 1.65) < tol) & (tt > t_ear - 10.02) & (tt < t_ear + 0.52)
                m |= (np.abs(tt - t_ear) < 0.03) & (rr <= 4.0)
        sets[f"SERVO{i}"] = sel("FRAME", m)
    # ---------------- horns: spline bore -> servo rigid body; eye -> horn-eye rigid body (horn-local)
    r_h = g["r_h"]
    for sv in g["servos"]:
        i = sv["i"]
        name = f"HORN{i}"
        Xh = local(M.X[list(M.offs).index(name)], T["horn"][i])
        rad0 = np.hypot(Xh[:, 0], Xh[:, 1])
        spl = ((np.abs(rad0 - 2.95) < tol) & (Xh[:, 2] > -0.02) & (Xh[:, 2] < 3.12)) | ((np.abs(Xh[:, 2]) < 0.03) & (rad0 <= 6.0))
        sets[f"SERVO{i}"] = np.concatenate([sets[f"SERVO{i}"], sel(name, spl)])
        re = np.hypot(Xh[:, 0] - r_h, Xh[:, 1])
        eye = ((np.abs(re - 1.65) < tol) & (Xh[:, 2] < 4.02)) | ((np.abs(re - 2.5) < tol) & (Xh[:, 2] > 3.98)) | \
              ((np.abs(Xh[:, 2] - 4.0) < 0.03) & (re >= 1.6) & (re <= 2.55)) | ((np.abs(Xh[:, 2] - 5.0) < 0.03) & (re >= 2.45) & (re <= 3.76))
        sets[f"HEYE{i}"] = sel(name, eye)
    for k_, v in sets.items():
        if len(v) < 6:
            raise RuntimeError(f"node set {k_} has only {len(v)} nodes")
    # ---------------- reference nodes
    ref = {}
    eng_ref, eng_rot = M.new_node((0, 0, 0)), M.new_node((0, 0, 0))
    ref["ENGINE"] = (eng_ref, eng_rot)
    for j, sy in ((1, 1.0), (2, -1.0)):
        pA = R @ np.array([0.0, sy * 45.5, 0.0])
        ref[f"PIN_IN{j}"] = (M.new_node(pA), M.new_node(pA))
        pB = T["ring"][:3, :3] @ np.array([0.0, sy * 45.5, 0.0])
        ref[f"SEAT_IN{j}"] = (M.new_node(pB), M.new_node(pB))
    for k, sx in ((1, 1.0), (2, -1.0)):
        pC = T["ring"][:3, :3] @ np.array([sx * 54.5, 0.0, 0.0])
        ref[f"PIN_OUT{k}"] = (M.new_node(pC), M.new_node(pC))
        pD = np.array([sx * 54.5, 0.0, 0.0])
        ref[f"SEAT_OUT{k}"] = (M.new_node(pD), M.new_node(pD))
    for sv, ps in zip(g["servos"], poses):
        i = sv["i"]
        ref[f"LEYE{i}"] = (M.new_node(ps["P_l"]), M.new_node(ps["P_l"]))
        ref[f"HEYE{i}"] = (M.new_node(ps["P_h"]), M.new_node(ps["P_h"]))
        ref[f"SERVO{i}"] = (M.new_node(sv["O"]), M.new_node(sv["O"]))
    # ---------------- write
    job = f"gk_{tag}"
    path = Path(workdir) / f"{job}.inp"
    kin, kout, kax = ksprings["k_in_radial"], ksprings["k_out_radial"], ksprings["k_axial"]
    with open(path, "w") as f:
        f.write(f"*HEADING\nGimbal axis stiffness {tag} (gimbal_k.py v1) alpha {a:.3f} beta {b:.3f} deg, h {h} mm\n")
        f.write("*NODE, NSET=NALL\n")
        for name, X in zip(M.offs, M.X):
            o = M.offs[name]
            for q, x in enumerate(X):
                f.write(f"{o+q}, {x[0]:.6f}, {x[1]:.6f}, {x[2]:.6f}\n")
        f.write("*NODE, NSET=NREF\n")
        for nid, x in M.extra:
            f.write(f"{nid}, {x[0]:.6f}, {x[1]:.6f}, {x[2]:.6f}\n")
        eid = 0
        psets = {}
        for name in M.offs:
            f.write(f"*ELEMENT, TYPE=C3D10, ELSET=E_{name}\n")
            o = M.offs[name]
            part, pnames = M.part[name]
            e0 = eid + 1
            for e in M.conn[name]:
                eid += 1
                f.write(f"{eid}, " + ", ".join(str(int(o + n)) for n in e) + "\n")
            if len(pnames) > 1:
                for q, pn in enumerate(pnames):
                    psets[f"P_{pn.replace('ENG-', '').replace('#', '_').replace('-', '')}"] = e0 + np.nonzero(part == q)[0]
        sp = []
        for sv in g["servos"]:
            i = sv["i"]
            eid += 1
            sp.append((eid, "SPRINGA", "S_ROD%d" % i, (ref[f"LEYE{i}"][0], ref[f"HEYE{i}"][0])))
        for j in (1, 2):
            for dof, k in ((1, kin), (2, kax), (3, kin)):
                eid += 1
                sp.append((eid, "SPRING2", f"S_IN{j}_{dof}", (ref[f"PIN_IN{j}"][0], ref[f"SEAT_IN{j}"][0]), dof, k))
        for kk in (1, 2):
            for dof, k in ((1, kax), (2, kout), (3, kout)):
                eid += 1
                sp.append((eid, "SPRING2", f"S_OUT{kk}_{dof}", (ref[f"PIN_OUT{kk}"][0], ref[f"SEAT_OUT{kk}"][0]), dof, k))
        for s_ in sp:
            f.write(f"*ELEMENT, TYPE={s_[1]}, ELSET={s_[2]}\n{s_[0]}, {s_[3][0]}, {s_[3][1]}\n")
        for s_ in sp:
            if s_[1] == "SPRINGA":
                i = int(s_[2][-1])
                kc = kchain[i] if isinstance(kchain, dict) else kchain
                f.write(f"*SPRING, ELSET={s_[2]}\n\n{kc:.6e}\n")
            else:
                f.write(f"*SPRING, ELSET={s_[2]}\n{s_[4]}, {s_[4]}\n{s_[5]:.6e}\n")
        for k_, v in psets.items():
            f.write(f"*ELSET, ELSET={k_}\n")
            fu.write_lines(f, v)
        for k_, v in sets.items():
            f.write(f"*NSET, NSET=N_{k_}\n")
            fu.write_lines(f, sorted(set(int(x) for x in v)))
        for k_ in ("FRAME", "RING", "COLLAR", "HORN1", "HORN2"):
            f.write(f"*MATERIAL, NAME=M_{k_}\n*ELASTIC\n{M.mat[k_]:.1f}, {NU_AL}\n*SOLID SECTION, ELSET=E_{k_}, MATERIAL=M_{k_}\n")
        for k_, (r0, r1) in ref.items():
            f.write(f"*RIGID BODY, NSET=N_{k_}, REF NODE={r0}, ROT NODE={r1}\n")
        f.write("*BOUNDARY\nN_FIX, 1, 3\n")
        for step, (dof, lab) in enumerate(((1, "Mx"), (2, "My"), (3, "Mz")), start=1):
            f.write(f"*STEP\n*STATIC\n*CLOAD, OP=NEW\n{eng_rot}, {dof}, 1000.\n")
            f.write("*NODE PRINT, NSET=NREF\nU\n")
            for k_ in ["E_FRAME", "E_RING", "E_COLLAR", "E_HORN1", "E_HORN2"] + list(psets):
                f.write(f"*EL PRINT, ELSET={k_}, TOTALS=ONLY\nELSE\n")
            f.write("*END STEP\n")
    meta = {"job": job, "alpha": a, "beta": b, "h": h, "stats": stats, "part_sets": list(psets), "sets": {k: int(len(v)) for k, v in sets.items()},
            "ref": {k: [int(v[0]), int(v[1])] for k, v in ref.items()}, "springs": [(s_[0], s_[2]) for s_ in sp],
            "poses": [{"psi": float(p["psi"]), "P_l": [float(x) for x in p["P_l"]], "P_h": [float(x) for x in p["P_h"]]} for p in poses],
            "kchain": kchain, "ksprings": ksprings}
    (Path(workdir) / f"{job}.meta.json").write_text(json.dumps(meta, indent=1, default=float))
    return job, meta


def evaluate(workdir, job, meta):
    d = fu.parse_dat(Path(workdir) / f"{job}.dat")
    times = sorted(d)
    rot = meta["ref"]["ENGINE"][1]
    C = np.zeros((3, 3))
    energies = []
    for c, t in enumerate(times[:3]):
        U = d[t]["U"]
        C[:, c] = np.array(U[rot]) / 1000.0              # rad per N mm -> per N m: rotations for a 1000 N mm (1 N m) moment
        en_all = dict(d[t].get("ETOT", {}))
        parts_ = {k: v for k, v in en_all.items() if k.upper().startswith("P_")}
        en = {k: v for k, v in en_all.items() if not k.upper().startswith("P_")}
        # springs
        def dU(name):
            return np.array(U[meta["ref"][name][0]])
        kc = meta["kchain"]
        for i in (1, 2):
            pl, ph = np.array(meta["poses"][i - 1]["P_l"]), np.array(meta["poses"][i - 1]["P_h"])
            e = (pl - ph) / np.linalg.norm(pl - ph)
            dl = (dU(f"LEYE{i}") - dU(f"HEYE{i}")) @ e
            k = kc[str(i)] if isinstance(kc, dict) and str(i) in kc else (kc[i] if isinstance(kc, dict) else kc)
            en[f"ROD_CHAIN{i}"] = 0.5 * k * dl ** 2
        ks = meta["ksprings"]
        e_in = e_out = 0.0
        for j in (1, 2):
            du = dU(f"PIN_IN{j}") - dU(f"SEAT_IN{j}")
            e_in += 0.5 * (ks["k_in_radial"] * (du[0] ** 2 + du[2] ** 2) + ks["k_axial"] * du[1] ** 2)
            du = dU(f"PIN_OUT{j}") - dU(f"SEAT_OUT{j}")
            e_out += 0.5 * (ks["k_out_radial"] * (du[1] ** 2 + du[2] ** 2) + ks["k_axial"] * du[0] ** 2)
        en["BEARINGS_INNER(608+pin)"] = e_in
        en["BEARINGS_OUTER(608+pin)"] = e_out
        Utot = 0.5 * 1000.0 * U[rot][c]
        energies.append({"load": ["Mx", "My", "Mz"][c], "U_total_Nmm": Utot, "sum_parts_Nmm": float(sum(en.values())),
                         "fraction": {k: v / Utot for k, v in en.items()}, "fraction_by_part": {k: v / Utot for k, v in parts_.items()}})
    Cxy = C[:2, :2]
    K = np.linalg.inv(Cxy)
    return {"compliance_rad_per_Nm": C.tolist(), "K_xy_Nm_per_rad": K.tolist(),
            "K_alpha_Nm_rad": float(K[0, 0]), "K_beta_Nm_rad": float(K[1, 1]),
            "K_alpha_other_free_Nm_rad": float(1.0 / Cxy[0, 0]), "K_beta_other_free_Nm_rad": float(1.0 / Cxy[1, 1]),
            "K_roll_Nm_rad": float(1.0 / C[2, 2]), "energy_split": energies}


VARIANTS = {
    # name: (servo, rod sense, thrust N, k_GE N/mm, stud root allowance mm)
    "mech_T_62":    ("none", "T", 62.5, 1.0e5, 2.5),
    "mech_C_62":    ("none", "C", 62.5, 1.0e5, 2.5),
    "mech_M_62":    ("none", "M", 62.5, 1.0e5, 2.5),
    "mech_T_160":   ("none", "T", 160.0, 1.0e5, 2.5),
    "mech_T_500":   ("none", "T", 500.0, 1.0e5, 2.5),
    "mech_T_62_chainlow":  ("none", "T", 62.5, 5.0e4, 2.5),
    "mech_C_62_chainhigh": ("none", "C", 62.5, 3.0e5, 0.0),
    "smin_T_62":    ("min", "T", 62.5, 1.0e5, 2.5),
    "smin_M_62":    ("min", "M", 62.5, 1.0e5, 2.5),
    "smax_T_62":    ("max", "T", 62.5, 1.0e5, 2.5),
    "smax_M_62":    ("max", "M", 62.5, 1.0e5, 2.5),
    "smin_T_500":   ("min", "T", 500.0, 1.0e5, 2.5),
}
SERVO_K = {"min": 58.0e3, "max": 174.0e3}       # N mm/rad, electronics.json v1 actuators.tvc_A.stiffness.servo_output_Nm_per_rad (ASSUMED there)


def variant_springs(name, rod, lam):
    servo, sense, thrust, kGE, Lr = VARIANTS[name]
    k_rod = {"T": rod["k_tension_N_mm"], "C": rod["k_compression_N_mm"], "M": rod["k_mean_N_mm"]}[sense]
    ch = chain_spring({"k_N_mm": k_rod}, k_GE=kGE, Lr=Lr)
    ks = bearing_springs(thrust)
    kchain = {i: ch["k_chain_N_mm"] for i in (1, 2)}
    note = "servo case + gear train rigid (mechanical path only)"
    if servo in SERVO_K:
        Ks = SERVO_K[servo]
        kchain = {i: 1.0 / (1.0 / ch["k_chain_N_mm"] + lam[i - 1] ** 2 / Ks) for i in (1, 2)}
        note = f"servo output stiffness {Ks/1e3:.0f} N m/rad in series on each rod line via the horn arm lambda {[round(x, 3) for x in lam]} mm"
    return {"servo": servo, "rod_sense": sense, "thrust_N": thrust, "k_GE_N_mm": kGE, "stud_root_mm": Lr, "chain": ch, "bearings": ks,
            "kchain": kchain, "note": note}


def rewrite_springs(src, dst, meta, vs):
    txt = Path(src).read_text()
    for i in (1, 2):
        txt = re.sub(rf"(\*SPRING, ELSET=S_ROD{i}\n\n)([-+0-9.eE]+)\n", lambda m: f"{m.group(1)}{vs['kchain'][i]:.6e}\n", txt)
    ks = vs["bearings"]
    for j in (1, 2):
        for dof, k in ((1, ks["k_in_radial"]), (2, ks["k_axial"]), (3, ks["k_in_radial"])):
            txt = re.sub(rf"(\*SPRING, ELSET=S_IN{j}_{dof}\n{dof}, {dof}\n)([-+0-9.eE]+)\n", lambda m: f"{m.group(1)}{k:.6e}\n", txt)
        for dof, k in ((1, ks["k_axial"]), (2, ks["k_out_radial"]), (3, ks["k_out_radial"])):
            txt = re.sub(rf"(\*SPRING, ELSET=S_OUT{j}_{dof}\n{dof}, {dof}\n)([-+0-9.eE]+)\n", lambda m: f"{m.group(1)}{k:.6e}\n", txt)
    Path(dst).write_text(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--poses", default="centre")
    ap.add_argument("--h", type=float, default=3.0)
    ap.add_argument("--variants", default="mech_T_62")
    args = ap.parse_args()
    import tvc_kinematics as tk
    P, S, reg, tb = build_cad()
    poses = {"centre": (0.0, 0.0), "alpha+7": (7.0, 0.0), "alpha-7": (-7.0, 0.0), "beta+7": (0.0, 7.0), "beta-7": (0.0, -7.0)}
    for d in (45, 135, 225, 315):
        poses[f"cone7_{d:03d}"] = tuple(float(x) for x in tk.cone_to_ab(7.0, d))
    rod = json.loads((HERE / "rod_k_v1.json").read_text())
    vnames = list(VARIANTS) if args.variants == "all" else args.variants.split(",")
    for pose in args.poses.split(","):
        a, b = poses[pose]
        lam = [la["lambda_mm"] for la in actuator_loads.lever_arms(S["tvc"], a, b)]
        tag = f"{pose}_h{args.h:g}".replace("+", "p").replace("-", "m")
        wd = RUNS / tag
        wd.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        v0 = variant_springs(vnames[0], rod, lam)
        job, meta = make_model(P, S, reg, a, b, args.h, v0["kchain"], v0["bearings"], tag, wd)
        t_mesh = round(time.time() - t0, 1)
        allres = {"pose": pose, "alpha_deg": a, "beta_deg": b, "h_mm": args.h, "mesh": meta["stats"], "sets": meta["sets"],
                  "lambda_h_mm": lam, "t_model_s": t_mesh, "cad_build_s": tb, "variants": {}}
        for vn in vnames:
            vs = variant_springs(vn, rod, lam)
            vjob = f"{job}_{vn}"
            rewrite_springs(Path(wd) / f"{job}.inp", Path(wd) / f"{vjob}.inp", meta, vs)
            m2 = dict(meta, kchain=vs["kchain"], ksprings=vs["bearings"])
            r = fu.run_ccx(vjob, wd, threads=2)
            res = {"ccx": r, **{k: vs[k] for k in ("servo", "rod_sense", "thrust_N", "k_GE_N_mm", "stud_root_mm", "note", "kchain")},
                   "chain": vs["chain"], "bearings": vs["bearings"]}
            if not r["errors"]:
                res.update(evaluate(wd, vjob, m2))
            allres["variants"][vn] = res
            for ext in (".frd", ".12d", ".cvg", ".sta"):
                fp = Path(wd) / f"{vjob}{ext}"
                if fp.exists() and ext != ".sta":
                    fp.unlink()
            print(pose, vn, r["seconds"], "s", "K_alpha", round(res.get("K_alpha_Nm_rad", float("nan"))), "K_beta", round(res.get("K_beta_Nm_rad", float("nan"))),
                  "K_roll", round(res.get("K_roll_Nm_rad", float("nan"))), r["errors"][:1], flush=True)
            if "energy_split" in res:
                for e in res["energy_split"][:2]:
                    print("   ", e["load"], "sum/total", round(e["sum_parts_Nmm"] / e["U_total_Nmm"], 4),
                          {k: round(v, 3) for k, v in sorted(e["fraction"].items(), key=lambda kv: -kv[1])},
                          {k: round(v, 3) for k, v in sorted(e["fraction_by_part"].items(), key=lambda kv: -kv[1])}, flush=True)
        (wd / "result.json").write_text(json.dumps(allres, indent=1, default=float))


if __name__ == "__main__":
    main()
