"""FEA3D v1 - assembled 3D FE model of the ARGOS H1 engine module (CAD v3.5), CalculiX 2.21 C3D10, fea3d 2026-10-13.

Bodies (asm_def.BODIES) are meshed separately (non-conforming) and joined by:
  * ties (own *EQUATION MPCs, closest-point projection on the independent quadratic face): 'bond' (u x,y,z), 'zt' (u_z + u_theta
    about the engine axis, radial free: thread / insert / lip rules of S-AX ported to 3D), 'rt' (radial + tangential, axial free);
  * connectors: rigid bodies (pins in bores, bearing outer rings in seats, servo case + horn spline, rod-eye studs, PD-02 crank
    housing), distributing couplings (screws, masses, airframe holes in the compliant variant) and 'bushings' = three SPRINGA
    along principal directions between two coincident reference nodes (aux node trick, ccx linear SPRINGA);
  * point masses (ledger items that are not meshed) on distributing couplings.
Loads (unit steps per thermal state, linear superposition, exact for a fixed temperature field):
  TH (mapped temperature), OP (chamber 1 MPa with the Combustion p(z)/Pc nozzle profile + port cap forces), PM (manifold 1 MPa +
  port caps + needle reaction), GX/GY/GZ (1 g acceleration of the vehicle along +axis: body force -m a), AX/AY (1 rad/s2 angular
  acceleration of the vehicle about the pivot), EAX (engine + ring about the outer axis X), EAY (engine about the inner axis Y).
Units: mm, N, MPa, t/mm3, K, s.  Engine frame: +Z forward, origin = gimbal pivot.
"""
from __future__ import annotations
import sys, json, math, time, csv, hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

SCR = Path("/home/claude/work/fea3d/scripts")
sys.path.insert(0, str(SCR))
import asm_def as A          # noqa: E402
import os                    # noqa: E402
import fe3d                  # noqa: E402
import samples               # noqa: E402
import mesh_all              # noqa: E402
# engmat v1.6 (hub 04-fea/src, 46ba163b864c7fc5): adds GLIDCOP-AL15 and SS440C-HT; values of every v3.5 material identical to the v1.4
# snapshot used by the first pipeline run (checked 2026-10-13)
SNAP = Path("/home/claude/work/fea3d/snap/engmat_v1p6")
sys.path.insert(0, str(SNAP))
import engmat                # noqa: E402

VERSION = "fea3d-asm v1.3"   # v1.2 2026-10-19: SPRINGA connectors 1e6 mm (REPORT 7.1); v1.3 2026-10-20: affine-consistent ties (variant tiex)
CAD = A.CAD
T_REF = 293.15
G_MM = 9810.0
_MR = Path("/home/claude/work/mechanical/runs/structural")
# v352 (Mechanical INTERIM set, CHANGELOG 233): until Mechanical publishes its v3.5.2 thermal / S-AX (lead brief 2026-10-20: NZ-01 / NZ-06 /
# TC-09 margins 'pending Mechanical v352 thermal'; TC-03 / TC-02 temperature 'open: thermal-joint model'), the v3.5.1 S-AX thermal map
# (L1_thv351_TB1GC_cad351) and its 2-D geometry (pressure classification) are used on the v3.5.2 geometry [interim basis, stated in the
# report].  FEA3D_SAX_RUN / FEA3D_SAX_GEOM override both (absolute paths) when a published v352 field is mapped.
SAX_RUN = Path(os.environ["FEA3D_SAX_RUN"]) if os.environ.get("FEA3D_SAX_RUN") else \
    {"v35": _MR / "L1_TC09IN718_thJ1revB_TC09IN", "v351": _MR / "L1_thv351_TB1GC_cad351", "v352": _MR / "L1_thv351_TB1GC_cad351"}[CAD]
SAX_GEOM = Path(os.environ["FEA3D_SAX_GEOM"]) if os.environ.get("FEA3D_SAX_GEOM") else \
    {"v35": _MR / "geom_v341revB" / "geometry.json", "v351": _MR / "geom_v351" / "geometry.json", "v352": _MR / "geom_v351" / "geometry.json"}[CAD]
COMB_BC = Path("/home/claude/work/shared-fallback/engine/02-combustion/data/v2/thermal_bc_max_v2.csv")
TVC_GEOM = Path("/home/claude/work/fea3d/geom/tvc_geometry_v35.json")      # servo / horn / lever eyes identical in v3.5.1 (CAD survey)
INST = A.GEOM / "instances.json"
MASSPROPS = {"v35": Path("/home/claude/work/mechanical/engine/03-cad/massprops_v3.5.json"),
             "v351": Path("/home/claude/work/shared-fallback/engine/03-cad/v3.5.1/massprops_v3.5.1.json"),
             "v352": Path("/home/claude/work/shared-fallback/engine/03-cad/v3.5.2/massprops_v3.5.2.json")}[CAD]
SAX_PARTS = ["TC-01", "TC-02", "TC-03", "TC-04", "TC-09", "NZ-01", "NZ-02", "NZ-03", "NZ-04"]

DEFAULT_VARIANT = {
    "ties": "design",            # 'design' (thread/insert z+theta) or 'bound' (bonded)
    "collar": "bonded",          # 'bonded' bore (clamped, no slip) or 'flank' (bore radial+tangential, lower flank bearing in z)
    "airframe": "rigid",         # 'rigid' (16 hole bores fixed) or 'compliant' (per hole springs, ASSUMED)
    "k_af": (2.0e3, 2.0e4, 2.0e4),   # N/mm per hole: radial, tangential, axial (compliant variant, ASSUMED; TO-VERIFY)
    "thrust_for_bearings": 500.0,    # N, Palmgren tangent stiffness load point
    "k_chain": None,             # N/mm rod chain (None = Mechanical mech_M design value, computed)
    "pose": (0.0, 0.0),
    "refine": None,              # {body: [(x, y, z, r, h)]} local mesh refinement (convergence study)
    "srefine": None,             # {body: [{faces_c, h, dmin, dmax, hout}]} CAD-face distance refinement (v3.5.2 rev 3 lever-root loop)
    # TC-03/TC-02 TB1 joint: 'faces' (every touching face pair within 0.12 mm: shoulder, 46 flange-OD nodes across the 0.10 mm design gap
    # and the z 117.51 end face, RM2-13) or 'thread' (shoulder + M14 engagement 'zt'; flange OD and end face free).  v3.5.2 default
    # 'thread' (CHANGELOG 234 (7)): consistent with the open, wetted flange-OD gap of the pressure model.
    "tb1": "thread" if CAD == "v352" else "faces",
    # Tie formulation (fea3d 2026-10-20, v3.5.2 re-check): legacy ties tie a dependent node to its closest point on the independent
    # face (tri6 interpolation at the projection point x_p); with an offset x_d - x_p (CAD gap / overlap, up to 0.17 mm for the bonded
    # ties and 0.5 mm for the TB1 'thread' engagement R7 -> R6.5) the constraint is NOT satisfied by a rigid rotation or a uniform
    # strain (patch test), so a rigid-body rotation of the engine group is resisted by a spurious stiffness and the tie does not
    # conserve moment (v3.5.2 stop045 L1: BUMP moment closure 82 %, rods / bumper; v3.5.1 faces variant 97.1 %).  tiex = True adds the
    # parent-tet gradient term:  u_d = sum_k N_k(x_p) u_k + sum_i (grad lambda_i . (x_d - x_p)) u_i  (i = 4 corners of the independent
    # face's tet, straight-sided C3D10) which is exact for every linear field (rigid motions, uniform strain) and reduces to the legacy
    # tie when the offset is zero.  Default on for CAD v3.5.2; runs solved without the key rebuild as legacy (post_f1.load_model).
    "tiex": CAD == "v352",
}


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def rot_axis(axis, ang_deg):
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    t = math.radians(ang_deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def R_pose(alpha, beta):
    a, b = math.radians(alpha), math.radians(beta)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    return Rx @ Ry


def tvc_geometry():
    g = json.loads(TVC_GEOM.read_text())
    for sv in g["servos"]:
        for k in ("eu", "et", "ez", "sd", "O", "C", "P_h0", "P_l0"):
            sv[k] = np.asarray(sv[k], float)
    return g


def solve_psi(g, sv, alpha, beta):
    """Horn angle psi (deg) keeping |P_h - P_l| = L_pr (copy of tvc_kinematics.solve_psi, Mechanical; branch nearest 0)."""
    Pl = R_pose(alpha, beta) @ sv["P_l0"]
    d = Pl - sv["C"]
    du, dz, dt = float(d @ sv["eu"]), float(d @ sv["ez"]), float(d @ sv["et"])
    L, rh = g["L_pr"], g["r_h"]
    K = (du * du + dz * dz + dt * dt + rh * rh - L * L) / (2.0 * rh)
    rho = math.hypot(dz, du)
    phi0 = math.atan2(-du, dz)
    base = math.asin(K / rho)
    cands = [base - phi0, math.pi - base - phi0]
    cands = [((c + math.pi) % (2 * math.pi)) - math.pi for c in cands]
    psi = min(cands, key=abs)
    return math.degrees(psi), Pl


def bearing_springs(F_thrust_N):
    """Port of Mechanical gimbal_k.bearing_springs (608-2RS Palmgren tangent stiffness in series with the 8 mm pin cantilever)."""
    Z, Dw = 7, 3.969
    Fr = max(F_thrust_N, 1.0) / 2.0
    Q = 5.0 * Fr / Z
    d = 4.36e-4 * (Q ** 2 / Dw) ** (1.0 / 3.0)
    k_b = 1.5 * Fr / d
    E, I = 196e3, math.pi * 8.0 ** 4 / 64.0
    k_pin_in = 3 * E * I / (6.0 + 4.0) ** 3
    k_pin_out = 3 * E * I / (5.5 + 4.0) ** 3
    return {"k_in_radial": 1.0 / (1.0 / k_b + 1.0 / k_pin_in), "k_out_radial": 1.0 / (1.0 / k_b + 1.0 / k_pin_out), "k_axial": 5.0e3,
            "k_608": k_b, "Fr": Fr, "tag": "ANALYTIC Palmgren (Mechanical gimbal_k.bearing_springs port); axial 5e3 N/mm ASSUMED"}


def needle_springs(F_thrust_N, scale=1.0):
    """CAD v3.5.1 gimbal: HK0808 drawn-cup needle bearings (Fw 8 x D 12 x C 8) running on 440C pins + PTFE-composite thrust washers.
    Radial: Palmgren line contact (Harris, Rolling Bearing Analysis, as recalled) delta = 3.84e-5 Q^0.9 / l^0.8 per raceway contact
    (mm, N), two contacts in series, Q_max = 4.08 Fr / Z (zero clearance); Z = 13 needles, effective length l = 5.0 mm ASSUMED (maker
    needle data not in the BOM: TO-VERIFY); tangent stiffness = secant / 0.9.  In series with the pin (440C E 209.6 GPa, DATASHEET) as a
    cantilever from the pressed boss face to the cup centre (inner 6.5 mm, outer 5.5 mm, bending + shear).  Washers: axial only,
    1.0e6 N/mm ASSUMED (steel-backed composite, effectively rigid next to the bosses that the FE resolves)."""
    Z, l = 13, 5.0
    Fr = max(F_thrust_N, 1.0) / 2.0
    Q = 4.08 * Fr / Z
    d = 2.0 * 3.84e-5 * Q ** 0.9 / l ** 0.8
    k_b = Fr / d / 0.9 * float(scale)          # scale: F3 sensitivity of the needle contact stiffness (variant k_needle_scale)
    E, nu = 209.6e3, 0.28
    G = E / (2 * (1 + nu))
    I, Ar = math.pi * 8.0 ** 4 / 64.0, math.pi * 8.0 ** 2 / 4.0

    def kpin(L):
        return 1.0 / (L ** 3 / (3 * E * I) + L / (0.9 * G * Ar))
    k_pi, k_po = kpin(6.5), kpin(5.5)
    return {"k_in_radial": 1.0 / (1.0 / k_b + 1.0 / k_pi), "k_out_radial": 1.0 / (1.0 / k_b + 1.0 / k_po), "k_washer": 1.0e6,
            "k_needle": k_b, "k_needle_scale": float(scale), "k_pin_in": k_pi, "k_pin_out": k_po, "Fr": Fr, "Q_max": Q, "Z_ASSUMED": Z, "l_eff_ASSUMED": l,
            "tag": "DERIVED Palmgren line contact (LITERATURE as recalled) with Z, l ASSUMED (TO-VERIFY maker data); washers 1e6 N/mm ASSUMED"}


def chain_k_design():
    """Mechanical chain variant mech_M: mean pushrod k (rod_k_v1 43864.6 N/mm) + 2 GE 5 E (1e5 N/mm ASSUMED) + 2 stud/screw
    cantilevers (5 mm shoulder, 4.5 + 2.5 mm); servo output rigid (holding)."""
    k_rod = 43864.623846622686
    E, G = 196e3, 75.4e3
    d, L, Lr = 5.0, 4.5, 2.5
    I, Ar = math.pi * d ** 4 / 64, math.pi * d ** 2 / 4
    c_pin = (L + Lr) ** 3 / (3 * E * I) + L / (0.9 * G * Ar)
    return 1.0 / (1.0 / k_rod + 2.0 / 1.0e5 + 2.0 * c_pin)


# =============================================================================================== bodies
class Body:
    def __init__(self, name, level, balls=None, tag="", surf=None):
        stem, si, grp, mat, trule, role = A.BODIES[name]
        d = mesh_all.mesh_body(name, level, balls=balls, tag=tag, surf=surf)
        self.name, self.stem, self.grp, self.mat, self.trule, self.role = name, stem, grp, mat, trule, role
        self.X0 = d["X"].astype(float)
        self.T10 = d["T10"].astype(np.int64)
        self.bf_e, self.bf_f, self.bf_n, self.bf_ent = d["bf_e"], d["bf_f"], d["bf_n"], d["bf_ent"]
        self.ent = json.loads(str(d["ent"]))
        self.meta = json.loads(str(d["meta"]))
        self.fc, self.fn, self.fa = fe3d.face_geom(self.X0, self.T10, self.bf_e, self.bf_f, self.bf_n)
        self.noff = 0
        self.eoff = 0

    def gn(self, local):
        return self.noff + np.asarray(local, dtype=np.int64)

    def ge(self, local):
        return self.eoff + np.asarray(local, dtype=np.int64)

    def ents(self, kind="Cylinder", R=None, axis=None, pt=None, tolR=0.02, tolpt=0.1):
        out = []
        for k, v in self.ent.items():
            if v["type"] != kind:
                continue
            if R is not None and (("R" not in v) or abs(v["R"] - R) > tolR):
                continue
            if axis is not None:
                if "axis" not in v or abs(abs(np.dot(v["axis"], axis) / np.linalg.norm(axis)) - 1.0) > 1e-3:
                    continue
                if pt is not None:
                    a = np.asarray(axis, float) / np.linalg.norm(axis)
                    w = np.asarray(v["axis_pt"]) - np.asarray(pt)
                    if np.linalg.norm(w - (w @ a) * a) > tolpt:
                        continue
            out.append(int(k))
        return out

    def faces_of_ents(self, tags):
        return np.isin(self.bf_ent, np.asarray(tags, dtype=np.int64))

    def nodes_of(self, mask):
        return np.unique(self.bf_n[mask].ravel())


# =============================================================================================== model
class Model:
    def __init__(self, level=1.0, variant=None):
        self.level = level
        self.v = dict(DEFAULT_VARIANT, **(variant or {}))
        self.alpha, self.beta = self.v["pose"]
        self.bodies = {}
        n = e = 0
        ref = self.v.get("refine") or {}          # {body: [(x, y, z, r, h), ...]} local refinement (convergence study)
        sref = self.v.get("srefine") or {}
        rtag = "_r" + hashlib.sha256(json.dumps(ref, sort_keys=True).encode()).hexdigest()[:8] if ref else ""
        if sref:
            rtag = "_r" + hashlib.sha256(json.dumps([ref, sref], sort_keys=True).encode()).hexdigest()[:8]
        lv = self.v.get("levels") or {}          # {body: level} per-body mesh level (pose runs: coarse engine pressure parts)
        for name in A.BODIES:
            b = Body(name, float(lv.get(name, level)), balls=ref.get(name), tag=rtag, surf=sref.get(name))
            b.noff, b.eoff = n + 1, e + 1
            n += len(b.X0)
            e += len(b.T10)
            self.bodies[name] = b
        self.n_mesh, self.e_mesh = n, e
        self.next_n, self.next_e = n + 1, e + 1
        self.extra = {}                         # id -> (xyz neutral, group)
        self.C = fe3d.Constraints()
        self.rigid = []                         # (label, [global node ids], ref, rot)
        self.coup = []                          # (label, ref, [(global eid, face)])
        self.springA = []                       # (label, eid, n1, n2, k)
        self.mass = []                          # (label, eid, node, m_t)
        self.fix = []                           # global node ids, DOF 1-3
        self.ground_aux = []                    # aux ground nodes (fixed)
        self.tied = {nm: np.zeros(len(b.fa), bool) for nm, b in self.bodies.items()}
        self.ties = []                          # report rows
        self.notes = []
        self.ref = {}                           # label -> ref node id
        self.mass_items = []                    # report rows
        self.g = tvc_geometry()
        self._pose_setup()

    # ------------------------------------------------------------------------------------------- pose
    def _pose_setup(self):
        a, b = self.alpha, self.beta
        self.Rg = {"engine": R_pose(a, b), "ring": R_pose(a, 0.0), "fixed": np.eye(3)}
        self.cg = {"engine": np.zeros(3), "ring": np.zeros(3), "fixed": np.zeros(3)}
        self.psi = {}
        for sv in self.g["servos"]:
            i = sv["i"]
            psi, Pl = solve_psi(self.g, sv, a, b)
            self.psi[i] = psi
            self.Rg[f"horn{i}"] = rot_axis(sv["et"], psi)
            self.cg[f"horn{i}"] = sv["C"]

    def posed(self, X, grp):
        R, c = self.Rg[grp], self.cg[grp]
        return (np.asarray(X) - c) @ R.T + c

    def new_node(self, xyz, grp):
        nid = self.next_n
        self.next_n += 1
        self.extra[nid] = (np.asarray(xyz, float), grp)
        return nid

    def new_elem(self):
        e = self.next_e
        self.next_e += 1
        return e

    def body_of_node(self, nid):
        for b in self.bodies.values():
            if b.noff <= nid < b.noff + len(b.X0):
                return b
        return None

    def xyz0(self, nid):
        if nid in self.extra:
            return self.extra[nid][0]
        b = self.body_of_node(nid)
        return b.X0[nid - b.noff]

    def grp_of(self, nid):
        if nid in self.extra:
            return self.extra[nid][1]
        return self.body_of_node(nid).grp

    # ------------------------------------------------------------------------------------------- selections
    def faces_near_instance(self, body, stem, tol=0.25, h=0.4, corners=True):
        b = self.bodies[body]
        Xs, Ts = samples.instance_surface(stem, h)
        d = samples.dist_to_surface(b.fc, Xs, Ts)
        m = d <= tol
        if corners:
            for k in range(3):
                dk = samples.dist_to_surface(b.X0[b.bf_n[:, k]], Xs, Ts)
                m &= dk <= tol
        return m

    def faces_near_body(self, dep, ind, tol, opp=-0.5, mask_dep=None, mask_ind=None):
        """Faces of dep whose centroid lies within tol of ind's boundary (normals opposed); returns (mask_dep, mask_ind_near)."""
        bd, bi = self.bodies[dep], self.bodies[ind]
        mi = np.ones(len(bi.fa), bool) if mask_ind is None else mask_ind
        md = np.ones(len(bd.fa), bool) if mask_dep is None else mask_dep
        tri = bi.bf_n[mi]
        dist, t, bary = fe3d.project_points(bd.fc, bi.X0, tri, bi.fc[mi], k=12)
        nI = bi.fn[mi][t]
        ok = md & (dist <= tol) & (np.einsum("ij,ij->i", bd.fn, nI) <= opp)
        # independent faces near the selected dep faces
        if ok.any():
            dist2, t2, _ = fe3d.project_points(bi.fc[mi], bd.X0, bd.bf_n[ok], bd.fc[ok], k=8)
            near = np.zeros(len(bi.fa), bool)
            idx_mi = np.nonzero(mi)[0]
            near[idx_mi[dist2 <= tol]] = True
        else:
            near = np.zeros(len(bi.fa), bool)
        return ok, near

    # ------------------------------------------------------------------------------------------- ties
    def tie(self, label, dep, ind, rule, tol=0.12, mask_dep=None, mask_ind=None, opp=-0.5):
        bd, bi = self.bodies[dep], self.bodies[ind]
        if bd.grp != bi.grp:
            raise ValueError(f"tie {label}: bodies in different pose groups")
        md, near = self.faces_near_body(dep, ind, tol, opp, mask_dep, mask_ind)
        mi = near if mask_ind is None else (near & mask_ind)
        if not md.any() or not mi.any():
            self.notes.append(f"tie {label}: no faces found ({dep}->{ind})")
            self.ties.append({"label": label, "dep": dep, "ind": ind, "rule": rule, "n_dep_nodes": 0, "n_eq": 0})
            return
        nodes = bd.nodes_of(md)
        P = bd.X0[nodes]
        tri = bi.bf_n[mi]
        dist, t, bary = fe3d.project_points(P, bi.X0, tri, bi.fc[mi], k=12)
        N = fe3d.tri6_N(bary)
        n_eq = 0
        n_far = int((dist > tol + 0.05).sum())
        ext = bool(self.v.get("tiex", False))
        n_ext_fb = 0
        if ext:
            # affine-consistent correction (variant tiex): grad lambda of the independent face's parent tet (straight-sided C3D10)
            fidx = np.nonzero(mi)[0][t]
            C4 = bi.T10[bi.bf_e[fidx], :4]
            Xc = bi.X0[C4]
            J = np.stack([Xc[:, 1] - Xc[:, 0], Xc[:, 2] - Xc[:, 0], Xc[:, 3] - Xc[:, 0]], axis=2)
            detJ = np.linalg.det(J)
            okJ = np.abs(detJ) > 1e-9 * np.max(np.abs(detJ))
            Jinv = np.zeros_like(J)
            Jinv[okJ] = np.linalg.inv(J[okJ])
            Gl = np.concatenate([-Jinv.sum(1, keepdims=True), Jinv], axis=1)            # (k, 4, 3): grad lambda_0..3
            Xp = np.einsum("kj,kjd->kd", bary, bi.X0[tri[t, :3]])                       # projection points
            cgr = np.einsum("kid,kd->ki", Gl, P - Xp)                                   # (k, 4) gradient weights
        for q, nl in enumerate(nodes):
            if dist[q] > tol + 0.05:
                continue
            gdep = int(bd.gn(nl))
            gind = bi.gn(tri[t[q]])
            wq = N[q]
            if ext:
                if okJ[q]:
                    ids = np.concatenate([gind, bi.gn(C4[q])])
                    ww = np.concatenate([N[q], cgr[q]])
                    gind, inv_ = np.unique(ids, return_inverse=True)
                    wq = np.zeros(len(gind))
                    np.add.at(wq, inv_, ww)
                else:
                    n_ext_fb += 1
            x = P[q]
            r = math.hypot(x[0], x[1])
            if rule == "bond":
                dirs = [np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])]
            elif rule in ("zt", "rt", "z", "t"):
                et = np.array([-x[1], x[0], 0.0]) / max(r, 1e-9)
                er = np.array([x[0], x[1], 0.0]) / max(r, 1e-9)
                ez = np.array([0, 0, 1.0])
                dirs = {"zt": [ez, et], "rt": [er, et], "z": [ez], "t": [et]}[rule]
            else:
                raise ValueError(rule)
            for dv in dirs:
                if self.C.add(label, gdep, self.Rg[bd.grp] @ dv, gind, wq):
                    n_eq += 1
        self.tied[dep] |= md
        self.tied[ind] |= mi
        if not hasattr(self, "tie_masks"):
            self.tie_masks = []
        self.tie_masks.append((label, dep, ind, md.copy(), mi.copy(), tol))
        # boundary edge nodes of the dependent patch (bonded-patch edges are singular in a linear model: post-processing exclusion)
        # (2026-10-13 fix: corner AND mid-side nodes of the patch boundary edges, on the dependent AND the independent patch; the
        # first version registered dependent corner nodes only, so mid-side nodes of long edges stayed in the regular set)
        from collections import Counter

        def patch_edge_nodes(b, mask):
            cnt, mid = Counter(), {}
            for f in np.nonzero(mask)[0]:
                c, m = b.bf_n[f, :3], b.bf_n[f, 3:6]
                for (a_, b_), mm in zip(((c[0], c[1]), (c[1], c[2]), (c[2], c[0])), m):
                    key = (min(a_, b_), max(a_, b_))
                    cnt[key] += 1
                    mid[key] = mm
            return sorted({int(n) for key, k in cnt.items() if k == 1 for n in (key[0], key[1], mid[key])})
        if not hasattr(self, "tie_edges"):
            self.tie_edges = {}
        self.tie_edges[label] = ([int(bd.gn(n)) for n in patch_edge_nodes(bd, md)]
                                 + [int(bi.gn(n)) for n in patch_edge_nodes(bi, mi)])
        self.ties.append({"label": label, "dep": dep, "ind": ind, "rule": rule, "n_dep_faces": int(md.sum()),
                          "n_ind_faces": int(mi.sum()), "n_dep_nodes": int(len(nodes)), "n_far_skipped": n_far, "n_eq": n_eq,
                          "dep_area_mm2": float(bd.fa[md].sum()), "max_gap_mm": float(dist[dist <= tol + 0.05].max()) if n_eq else None,
                          "tiex": ext, "n_tiex_fallback": n_ext_fb})

    # ------------------------------------------------------------------------------------------- connectors
    def rigid_body(self, label, node_ids, ref_xyz, grp):
        node_ids = np.unique(np.asarray(node_ids, dtype=np.int64))
        ref = self.new_node(ref_xyz, grp)
        rot = self.new_node(ref_xyz, grp)
        self.rigid.append((label, node_ids, ref, rot))
        self.C.protected.update(int(x) for x in node_ids)
        self.ref[label] = ref
        return ref

    def coupling(self, label, faces, ref_xyz, grp):
        """faces: list of (body name, local face index array)."""
        ref = self.new_node(ref_xyz, grp)
        F = []
        nodes = []
        for bn, fidx in faces:
            b = self.bodies[bn]
            fidx = np.asarray(fidx)
            for fi in fidx:
                F.append((int(b.ge(b.bf_e[fi])), int(b.bf_f[fi])))
            nodes.append(b.gn(np.unique(b.bf_n[fidx].ravel())))
        if not F:
            raise RuntimeError(f"coupling {label}: no faces")
        self.coup.append((label, ref, F))
        self.C.protected.update(int(x) for x in np.concatenate(nodes))
        self.ref[label] = ref
        return ref

    def spring_a(self, label, n1, n2, k):
        e = self.new_elem()
        self.springA.append((label, e, n1, n2, k))
        return e

    def bushing(self, label, nA, nB, dirs, ks, grp):
        """Three SPRINGA from nA to aux nodes placed at xA + d_k (1 mm), each aux node tied to nB (u_aux = u_B)."""
        xA = self.xyz0(nA)
        for k_, (dv, kk) in enumerate(zip(dirs, ks)):
            if kk is None or kk <= 0:
                continue
            aux = self.new_node(xA + np.asarray(dv, float), grp)
            for d in (1, 2, 3):
                self.C.add_raw(f"{label}_aux", [(aux, d, 1.0), (nB, d, -1.0)])
            self.spring_a(f"{label}_k{k_}", nA, aux, kk)

    def point_mass(self, label, node, m_kg):
        e = self.new_elem()
        self.mass.append((label, e, node, m_kg * 1e-3))

    # ------------------------------------------------------------------------------------------- report
    def summary(self):
        return {"version": VERSION, "level": self.level, "variant": {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.v.items()},
                "n_mesh_nodes": self.n_mesh, "n_mesh_elems": self.e_mesh, "n_extra_nodes": len(self.extra),
                "n_equations": len(self.C.eqs), "n_rigid": len(self.rigid), "n_coupling": len(self.coup), "n_springA": len(self.springA),
                "n_mass": len(self.mass), "n_fix_nodes": len(self.fix), "skipped_dep": self.C.skipped, "ties": self.ties,
                "notes": self.notes, "psi_deg": self.psi,
                "bodies": {nm: {"nodes": int(len(b.X0)), "tets": int(len(b.T10)), "group": b.grp, "material": b.mat,
                                "q_min": b.meta["q_min"], "n_q_below_0.1": b.meta["n_q_below_0.1"], "volume_mm3": b.meta["volume_mm3"],
                                "brep": b.meta["brep"]} for nm, b in self.bodies.items()}}
