"""FEA3D v1 - assembly builder (connectors, ties, masses, pressure, thermal map, inertial loads, CalculiX deck).  fea3d 2026-10-13.

Connector technology (tested in runs/cpltest, ccx 2.21):
  * ccx *COUPLING/*DISTRIBUTING reference nodes cannot carry element stiffness (SPRINGA on a coupling REF NODE -> singular matrix in
    every variant tested): no ccx couplings are used.  Kinematic couplings are own RBE3 equations (reference node = weighted mean of the
    surface translations + mean rotation x offset, exact force AND moment transfer, verified on a cube: offset moment recovered to 1e-7);
  * mass items and cap forces are applied as RBE3-distributed nodal forces (f_i = C_i^T F, exact resultant force and moment);
  * rigid connectors are ccx *RIGID BODY (reference node may carry springs; verified);
  * bushings = 3 SPRINGA from node A to auxiliary nodes at x_A + d_k (1 mm), each auxiliary node equal to node B (u_aux = u_B).
"""
from __future__ import annotations
import sys, json, math, csv, time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

SCR = Path("/home/claude/work/fea3d/scripts")
sys.path.insert(0, str(SCR))
import asm3d as A3          # noqa: E402
import asm_def as AD        # noqa: E402
import fe3d                 # noqa: E402
import samples              # noqa: E402

engmat = A3.engmat
EX, EY, EZ = np.eye(3)
K_JFWD_SHEAR = 42.7e3        # N/mm, M5 single shear, Huth (DERIVED, see report)
K_JFWD_AXIAL = 1.0e5         # N/mm, screw axis (ASSUMED)
K_PDFOOT = (1.0e4, 1.0e4, 1.0e5)   # N/mm x, y, z (ASSUMED: ISO 4762 M3 x 12 A2-70 (BOM v3.5.1 HW-105) shear through the G11 washer / washer compression)
SPRING_OFF_MM = 1.0e6         # SPRINGA connector length (fea3d 2026-10-19, REPORT 7.1): CalculiX SPRINGA uses the DEFORMED length and
                              # direction even in linear steps; with 1 mm aux springs the second-order term du_perp^2/(2L) and the
                              # direction drift under thermal / previous-step displacements broke the free body (56-79 % closure).
                              # At 1e6 mm both are negligible (test tests/conn71: closure 99.93 % after an 800 K pre-step).
def spring_off(M):
    """SPRINGA connector length: 1e6 mm (asm v1.2, default) or 1 mm for runs solved before the 7.1 fix (variant conn = legacy)."""
    return 1.0 if M.v.get("conn", "v12") == "legacy" else SPRING_OFF_MM


T_BAY_K = 333.15             # K, bay structure temperature for E(T) and allowables (ASSUMED 60 C, TO-VERIFY)
LEDGER_STATE = "wet"


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


# =============================================================================================== selections (neutral frame)
def sel_cyl(b, pt, ax, R, s0=-1e9, s1=1e9, tolR=0.03, tols=0.05):
    """Faces whose 3 corner nodes lie on the cylinder (axis through pt along ax, radius R) within s0..s1 along the axis."""
    ax, pt = unit(ax), np.asarray(pt, float)
    P = b.X0[b.bf_n[:, :3]]
    v = P - pt
    s = v @ ax
    w = v - s[..., None] * ax
    d = np.linalg.norm(w, axis=2)
    ok = np.all(np.abs(d - R) <= tolR, axis=1) & np.all(s >= s0 - tols, axis=1) & np.all(s <= s1 + tols, axis=1)
    wc = b.fc - pt
    wc = wc - np.outer(wc @ ax, ax)
    wc /= np.maximum(np.linalg.norm(wc, axis=1), 1e-12)[:, None]
    return ok & (np.abs(np.einsum("ij,ij->i", b.fn, wc)) > 0.5)


def sel_plane(b, nrm, p0, tol=0.03, side=0):
    nrm = unit(nrm)
    P = b.X0[b.bf_n[:, :3]]
    h = (P - np.asarray(p0, float)) @ nrm
    ok = np.all(np.abs(h) <= tol, axis=1)
    dn = b.fn @ nrm
    return ok & ((dn > 0.95) if side > 0 else (dn < -0.95) if side < 0 else (np.abs(dn) > 0.95))


def line_dist(P, pt, ax):
    ax = unit(ax)
    v = np.asarray(P, float) - np.asarray(pt, float)
    s = v @ ax
    return np.linalg.norm(v - np.outer(s, ax), axis=1), s


def near_pt(b, p, rad):
    return np.linalg.norm(b.fc - np.asarray(p, float), axis=1) <= rad


def nearest_faces(b, p, extra=3.0):
    """Faces whose centroid lies within (closest centroid distance + extra) of p (attachment of items that do not touch in CAD)."""
    d = np.linalg.norm(b.fc - np.asarray(p, float), axis=1)
    return d <= d.min() + extra


# =============================================================================================== ledger
def ledger():
    m = json.loads(A3.MASSPROPS.read_text())
    rows = {}
    for r in m["ledger_mid"]:
        rows[(r["pn"].replace("ENG-", ""), r["idx"], r["group"])] = r
    grain_wet = m["grain_mass_wet_kg"]
    g_mid = rows[("GR-01", 0, "engine")]["m_kg"] + rows[("GR-02", 0, "engine")]["m_kg"]
    return rows, m, grain_wet / g_mid


# =============================================================================================== assembly
class Asm(A3.Model):
    def __init__(self, level=1.0, variant=None):
        super().__init__(level, variant)
        self.Xp = {nm: self.posed(b.X0, b.grp) for nm, b in self.bodies.items()}
        self.members = {}            # rigid label -> list of member node ids (mass / load points)
        self.loads = {}              # step -> {node: vec3}
        self.dloads = {}             # step -> list of (eid, face, value)
        self.af_sets = {}            # airframe hole label -> node ids for RF output
        self.gnd = set()             # fixed nodes (DOF 1-3)
        self.bush = []               # bushing report rows
        self.rbe = {}                # label -> dict(ref, nodes, area)
        self.items = []              # mass item report rows
        self.press_report = {}
        self.k_chain = self.v["k_chain"] or A3.chain_k_design()
        self.bk = (A3.bearing_springs(self.v["thrust_for_bearings"]) if A3.CAD == "v35"
                   else A3.needle_springs(self.v["thrust_for_bearings"], float(self.v.get("k_needle_scale", 1.0))))
        self.cad = A3.CAD

    # ------------------------------------------------------------------------------------------- geometry helpers
    def xyzp(self, nids):
        nids = np.atleast_1d(np.asarray(nids, dtype=np.int64))
        out = np.zeros((len(nids), 3))
        for nm, b in self.bodies.items():
            m = (nids >= b.noff) & (nids < b.noff + len(b.X0))
            if m.any():
                out[m] = self.Xp[nm][nids[m] - b.noff]
        for k, n in enumerate(nids):
            if int(n) in self.extra:
                x, g = self.extra[int(n)]
                out[k] = self.posed(x[None], g)[0]
        return out

    def face_nodes_weights(self, faces):
        """faces: list of (body, bool mask or index array).  Consistent uniform-traction weights of straight tri6 faces
        (corners 0, mid nodes A/3).  Returns (global node ids, weights summing to 1, total area)."""
        nodes, w = [], []
        for bn, sel in faces:
            b = self.bodies[bn]
            idx = np.nonzero(sel)[0] if np.asarray(sel).dtype == bool else np.asarray(sel, dtype=np.int64)
            if not len(idx):
                continue
            nodes.append(b.gn(b.bf_n[idx, 3:6].ravel()))
            w.append(np.repeat(b.fa[idx] / 3.0, 3))
        if not nodes:
            raise RuntimeError("face set is empty")
        nodes, w = np.concatenate(nodes), np.concatenate(w)
        u, inv = np.unique(nodes, return_inverse=True)
        ww = np.zeros(len(u))
        np.add.at(ww, inv, w)
        return u, ww / ww.sum(), float(ww.sum())

    def rbe3_C(self, nodes, w, xref_p):
        X = self.xyzp(nodes)
        xc = w @ X
        r = X - xc
        d = np.asarray(xref_p, float) - xc
        A = (w[:, None, None] * ((r * r).sum(1)[:, None, None] * np.eye(3)[None] - r[:, :, None] * r[:, None, :])).sum(0)
        if np.linalg.cond(A) > 1e8 or np.linalg.norm(d) < 1e-9:
            return w[:, None, None] * np.eye(3)[None]
        Ai = np.linalg.inv(A)
        Rx = np.zeros((len(r), 3, 3))
        Rx[:, 0, 1], Rx[:, 0, 2], Rx[:, 1, 0], Rx[:, 1, 2], Rx[:, 2, 0], Rx[:, 2, 1] = -r[:, 2], r[:, 1], r[:, 2], -r[:, 0], -r[:, 1], r[:, 0]
        return w[:, None, None] * (np.eye(3)[None] - np.einsum("ab,bc,ncd->nad", skew(d), Ai, Rx))

    # ------------------------------------------------------------------------------------------- connectors
    def rbe3_ref(self, label, faces, xref, grp):
        """Kinematic RBE3: new dependent reference node = weighted mean translation + mean rotation x offset."""
        nodes, w, area = self.face_nodes_weights(faces)
        ref = self.new_node(xref, grp)
        C = self.rbe3_C(nodes, w, self.posed(np.asarray(xref, float)[None], grp)[0])
        for k in range(3):
            terms = [(ref, k + 1, 1.0)]
            for n, Ci in zip(nodes, C):
                for j in range(3):
                    if abs(Ci[k, j]) > 1e-10:
                        terms.append((int(n), j + 1, -float(Ci[k, j])))
            self.C.add_raw(f"RBE3_{label}", terms)
        self.C.protected.update(int(x) for x in nodes)
        self.rbe[label] = {"ref": ref, "n_nodes": int(len(nodes)), "area_mm2": round(area, 3), "nodes": [int(x) for x in nodes]}
        self.ref[label] = ref
        return ref

    def rigid_conn(self, label, faces, xref, grp, members=()):
        """ccx *RIGID BODY on the nodes of faces (all 6 nodes per face) + member nodes (mass / load points, neutral xyz, own group)."""
        nodes = []
        for bn, sel in faces:
            b = self.bodies[bn]
            idx = np.nonzero(sel)[0] if np.asarray(sel).dtype == bool else np.asarray(sel, dtype=np.int64)
            nodes.append(b.gn(np.unique(b.bf_n[idx].ravel())))
        nodes = np.concatenate(nodes) if nodes else np.zeros(0, np.int64)
        if not len(nodes):
            raise RuntimeError(f"rigid {label}: no faces")
        mem = []
        for x, g in members:
            mem.append(self.new_node(x, g))
        ref = self.rigid_body(label, np.concatenate([nodes, np.asarray(mem, np.int64)]), xref, grp)
        self.members[label] = mem
        return ref

    def bushing2(self, label, nA, nB, dirs, ks, grp_aux):
        xA = self.xyz0(nA)
        auxs = []
        for k_, (dv, kk) in enumerate(zip(dirs, ks)):
            if kk is None or kk <= 0:
                continue
            aux = self.new_node(xA + spring_off(self) * unit(dv), grp_aux)
            for d in (1, 2, 3):
                self.C.add_raw(f"{label}_aux", [(aux, d, 1.0), (nB, d, -1.0)])
            self.C.protected.add(aux)
            e = self.spring_a(f"{label}_k{k_}", nA, aux, kk)
            auxs.append((aux, e, [float(c) for c in unit(dv)], kk))
        self.bush.append({"label": label, "A": int(nA), "B": int(nB), "springs": auxs})

    def ground_springs(self, label, nA, dirs, ks, grp):
        xA = self.xyz0(nA)
        g = []
        for k_, (dv, kk) in enumerate(zip(dirs, ks)):
            gn = self.new_node(xA + spring_off(self) * unit(dv), grp)
            self.gnd.add(gn)
            self.spring_a(f"{label}_g{k_}", nA, gn, kk)
            g.append(gn)
        self.bush.append({"label": label, "A": int(nA), "B": None, "springs": [(gn, None, [float(c) for c in unit(dv)], kk) for gn, dv, kk in zip(g, dirs, ks)]})
        return g

    # ------------------------------------------------------------------------------------------- loads
    def add_load(self, step, node, vec):
        d = self.loads.setdefault(step, {})
        d[int(node)] = d.get(int(node), np.zeros(3)) + np.asarray(vec, float)

    def add_force_on_faces(self, step, faces, xref_p, F):
        nodes, w, _ = self.face_nodes_weights(faces)
        C = self.rbe3_C(nodes, w, xref_p)
        f = np.einsum("nkj,k->nj", C, np.asarray(F, float))
        for n, fi in zip(nodes, f):
            self.add_load(step, n, fi)

    def add_pressure(self, step, body, idx, values):
        b = self.bodies[body]
        L = self.dloads.setdefault(step, [])
        for i, v in zip(idx, values):
            L.append((int(b.ge(b.bf_e[i])), int(b.bf_f[i]), float(v)))

    def pressure_force(self, step):
        """Resultant force (posed frame) of the pressure list of a step (straight faces: exact)."""
        F = np.zeros(3)
        for nm, b in self.bodies.items():
            pass
        tot = np.zeros(3)
        lut = {}
        for nm, b in self.bodies.items():
            lut[nm] = b
        L = self.dloads.get(step, [])
        if not L:
            return tot
        E = np.array([l[0] for l in L])
        Fc = np.array([l[1] for l in L])
        V = np.array([l[2] for l in L])
        for nm, b in self.bodies.items():
            m = (E >= b.eoff) & (E < b.eoff + len(b.T10))
            if not m.any():
                continue
            el = E[m] - b.eoff
            key = {(int(e), int(f)): i for i, (e, f) in enumerate(zip(b.bf_e, b.bf_f))}
            ii = np.array([key[(int(e), int(f))] for e, f in zip(el, Fc[m])])
            P = self.Xp[nm][b.bf_n[ii, :3]]
            n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]) * 0.5
            ct = self.Xp[nm][b.T10[b.bf_e[ii], :4]].mean(1)
            sgn = np.sign(np.einsum("ij,ij->i", n, P.mean(1) - ct))
            tot += -(V[m][:, None] * n * sgn[:, None]).sum(0)
        return tot


# =============================================================================================== model definition
def _annulus_plane(b, axis, coord, side, r0, r1):
    """Faces of body b on the plane (axis index) = coord, outward normal sign 'side', within r0..r1 of the axis line."""
    e = np.eye(3)[axis]
    m = sel_plane(b, e, coord * e, tol=0.03, side=side)
    o = [i for i in range(3) if i != axis]
    rho = np.hypot(b.fc[:, o[0]], b.fc[:, o[1]])
    return m & (rho >= r0) & (rho <= r1)


def _gimbal_v351(M, B, rows):
    """CAD v3.5.1 gimbal (parts_gimbal.py, BRG = HK0808): pins pressed into the collar (inner, r 33-39) and ring (outer, r 40.9-49) bores
    (rigid connectors + pin / washer masses), HK0808 cups pressed in the ring (r 41.5-49.5) and post (r 50.5-58.5) bores (rigid seats),
    needle bushing = radial only; axial by the PTFE-composite thrust washers GM-06 (collar boss face r 39 -> ring face r 40.6) and GM-07
    (ring boss face r 49 -> post face r 50.5) as axial bushings between RBE3 references on the washer footprints; one locating washer
    per axis (+Y inner, +X outer), the other side free (select fit / shim +/-0.05 mm: a clearance; one washer bears at a time)."""
    bk = M.bk
    b3 = B["GM-03"]
    for j, sgn, body in ((1, +1, "GM-01"), (2, -1, "GM-02")):
        mpin = sel_cyl(B[body], (0, 0, 0), EY, 4.0, *(sorted((33.0 * sgn, 39.0 * sgn))))
        keys = [("GM-04", j - 1, "engine", 1), ("GM-06", j - 1, "engine", 1), ("HW-21", j - 1, "engine", 1)] + ([("EL-06", 0, "engine", 1)] if j == 1 else [])
        mem = [(np.asarray(rows[k_[:3]]["cg_mm"]), "engine") for k_ in keys]
        refP = M.rigid_conn(f"PIN_IN_{j}", [(body, mpin)], (0, 45.5 * sgn, 0), "engine", mem)
        for k_, nid in zip(keys, M.members[f"PIN_IN_{j}"]):
            M.items.append({"label": f"PIN_IN_{j}", "items": [f"{k_[0]}#{k_[1]}"], "m_kg": rows[k_[:3]]["m_kg"], "cg": rows[k_[:3]]["cg_mm"],
                            "group": "engine", "attach": ("member", nid)})
        mseat = sel_cyl(b3, (0, 0, 0), EY, 6.0, *(sorted((41.5 * sgn, 49.5 * sgn))))
        keyS = ("HW-20", j - 1, "ring")
        refS = M.rigid_conn(f"SEAT_IN_{j}", [("GM-03", mseat)], (0, 45.5 * sgn, 0), "ring", [(np.asarray(rows[keyS]["cg_mm"]), "ring")])
        M.items.append({"label": f"SEAT_IN_{j}", "items": [f"HW-20#{j - 1}"], "m_kg": rows[keyS]["m_kg"], "cg": rows[keyS]["cg_mm"],
                        "group": "ring", "attach": ("member", M.members[f"SEAT_IN_{j}"][0])})
        M.bushing2(f"BRG_IN_{j}", refP, refS, [EX, EZ], [bk["k_in_radial"], bk["k_in_radial"]], "engine")
        if j == 1:
            mc = _annulus_plane(B[body], 1, 39.0 * sgn, +sgn, 4.0, 7.05)
            mr = _annulus_plane(b3, 1, 40.6 * sgn, -sgn, 5.2, 7.05)
            if not mc.any() or not mr.any():
                raise RuntimeError(f"washer WSH_IN_{j}: faces not found ({mc.sum()}, {mr.sum()})")
            rc = M.rbe3_ref(f"WSHC_IN_{j}", [(body, mc)], (0, 39.8 * sgn, 0), "engine")
            rr = M.rbe3_ref(f"WSHR_IN_{j}", [("GM-03", mr)], (0, 39.8 * sgn, 0), "ring")
            M.bushing2(f"WSH_IN_{j}", rc, rr, [EY], [bk["k_washer"]], "engine")
    for k, sgn, post in ((1, +1, "GM-08a"), (2, -1, "GM-08b")):
        mpin = sel_cyl(b3, (0, 0, 0), EX, 4.0, *(sorted((40.8 * sgn, 49.0 * sgn))))
        keys = [("GM-05", k - 1, "ring", 1), ("GM-07", k - 1, "ring", 1), ("HW-21", k + 1, "ring", 1)] + ([("EL-06", 1, "ring", 1)] if k == 2 else [])
        mem = [(np.asarray(rows[key[:3]]["cg_mm"]), "ring") for key in keys]
        refP = M.rigid_conn(f"PIN_OUT_{k}", [("GM-03", mpin)], (54.5 * sgn, 0, 0), "ring", mem)
        for key, nid in zip(keys, M.members[f"PIN_OUT_{k}"]):
            M.items.append({"label": f"PIN_OUT_{k}", "items": [f"{key[0]}#{key[1]}"], "m_kg": rows[key[:3]]["m_kg"], "cg": rows[key[:3]]["cg_mm"],
                            "group": "ring", "attach": ("member", nid)})
        bp = B[post]
        mseat = sel_cyl(bp, (0, 0, 0), EX, 6.0, *(sorted((50.5 * sgn, 58.5 * sgn))))
        key = ("HW-20", k + 1, "fixed")
        refS = M.rigid_conn(f"SEAT_OUT_{k}", [(post, mseat)], (54.5 * sgn, 0, 0), "fixed", [(np.asarray(rows[key]["cg_mm"]), "fixed")])
        M.items.append({"label": f"SEAT_OUT_{k}", "items": [f"HW-20#{k + 1}"], "m_kg": rows[key]["m_kg"], "cg": rows[key]["cg_mm"],
                        "group": "fixed", "attach": ("member", M.members[f"SEAT_OUT_{k}"][0])})
        M.bushing2(f"BRG_OUT_{k}", refP, refS, [EY, EZ], [bk["k_out_radial"], bk["k_out_radial"]], "ring")
        if k == 1:
            mr = _annulus_plane(b3, 0, 49.0 * sgn, +sgn, 4.0, 7.05)
            mp = _annulus_plane(bp, 0, 50.5 * sgn, -sgn, 5.95, 7.05)
            if not mr.any() or not mp.any():
                raise RuntimeError(f"washer WSH_OUT_{k}: faces not found ({mr.sum()}, {mp.sum()})")
            ra = M.rbe3_ref(f"WSHR_OUT_{k}", [("GM-03", mr)], (49.75 * sgn, 0, 0), "ring")
            rb = M.rbe3_ref(f"WSHP_OUT_{k}", [(post, mp)], (49.75 * sgn, 0, 0), "fixed")
            M.bushing2(f"WSH_OUT_{k}", ra, rb, [EX], [bk["k_washer"]], "ring")


def _hardware_items(M, B, mp):
    """massprops v3.5.1 hardware rows (HW-1xx, CALC; one ledger row per host part, the same (pn, idx, group) key repeats) as mass items on
    the nearest faces of the nearest meshed body of the same pose group (within 60 mm of the row CG); rows farther away (airframe-wall
    equipment hardware) are excluded from F1 and listed (F4 scope)."""
    grp_bodies = {}
    for nm, b in B.items():
        g = "horn" if b.grp.startswith("horn") else b.grp
        grp_bodies.setdefault(g, []).append(nm)
    excl = []
    for q, r in enumerate(mp["ledger_mid"]):
        pn, g = r["pn"].replace("ENG-", ""), r["group"]
        if not (pn.startswith("HW-1") and len(pn) == 6):
            continue
        cg = np.asarray(r["cg_mm"], float)
        best = None
        for nm in grp_bodies.get(g, []):
            d = float(np.min(np.linalg.norm(B[nm].fc - cg, axis=1)))
            if best is None or d < best[0]:
                best = (d, nm)
        if best is None or best[0] > 60.0:
            excl.append({"pn": pn, "group": g, "m_kg": r["m_kg"], "cg_mm": r["cg_mm"], "nearest_mm": (round(best[0], 1) if best else None)})
            continue
        nm = best[1]
        M.items.append({"label": f"HW_{pn}_{q}", "items": [f"{pn}#row{q}"], "m_kg": r["m_kg"], "cg": list(map(float, cg)), "group": B[nm].grp,
                        "attach": ("faces", [(nm, nearest_faces(B[nm], cg, extra=3.0))])})
    M.hardware_excluded = excl


def define(M: Asm):
    B = M.bodies
    t0 = time.time()
    rows, mp, gfac = ledger()

    def m_of(keys):
        """keys: list of (pn, idx, group, factor) -> (mass kg, cg neutral)."""
        mm, mc = 0.0, np.zeros(3)
        for pn, i, g, f in keys:
            r = rows[(pn, i, g)]
            mk = r["m_kg"] * f * (gfac if pn in ("GR-01", "GR-02") else 1.0)
            mm += mk
            mc += mk * np.asarray(r["cg_mm"])
        return mm, mc / max(mm, 1e-30)

    # ---------------------------------------------------------------- airframe interface (16 x M5 radial)
    for ring, z, s0, s1 in (("GM-09", 27.0, 58.6, 69.9), ("GM-10", -94.8, 40.0, 75.0)):
        for k in range(8):
            phi = math.radians(22.5 + 45 * k)
            er = np.array([math.cos(phi), math.sin(phi), 0.0])
            et = np.array([-math.sin(phi), math.cos(phi), 0.0])
            m = sel_cyl(B[ring], (0, 0, z), er, 2.1, s0, s1)
            lab = f"AF_{ring.replace('-', '')}_{k}"
            if not m.any():
                raise RuntimeError(f"{lab}: hole faces not found")
            if M.v["airframe"] == "rigid":
                nodes = B[ring].gn(np.unique(B[ring].bf_n[m].ravel()))
                M.gnd.update(int(x) for x in nodes)
                M.C.protected.update(int(x) for x in nodes)
                M.af_sets[lab] = [int(x) for x in nodes]
            else:
                kr, kt, kz = M.v["k_af"]
                ref = M.rbe3_ref(lab, [(ring, m)], er * 0.5 * (s0 + s1) + np.array([0, 0, z]), "fixed")
                M.af_sets[lab] = M.ground_springs(lab, ref, [er, et, EZ], [kr, kt, kz], "fixed")

    # ---------------------------------------------------------------- gimbal: rigid pins / seats + bearing bushings
    bk = M.bk
    if A3.CAD == "v351":
        _gimbal_v351(M, B, rows)
    for j, sgn, body in (((1, +1, "GM-01"), (2, -1, "GM-02")) if A3.CAD == "v35" else ()):
        mpin = sel_cyl(B[body], (0, 0, 0), EY, 4.0, *(sorted((33.0 * sgn, 39.0 * sgn))))
        keys = [("GM-04", j - 1, "engine", 1), ("GM-06", j - 1, "engine", 1), ("HW-21", j - 1, "engine", 1)] + ([("EL-06", 0, "engine", 1)] if j == 1 else [])
        mem = [(np.asarray(rows[(pn, i, g)]["cg_mm"]), "engine") for pn, i, g, f in keys]
        refP = M.rigid_conn(f"PIN_IN_{j}", [(body, mpin)], (0, 45.5 * sgn, 0), "engine", mem)
        for (pn, i, g, f), nid in zip(keys, M.members[f"PIN_IN_{j}"]):
            M.items.append({"label": f"PIN_IN_{j}", "items": [f"{pn}#{i}"], "m_kg": rows[(pn, i, g)]["m_kg"], "cg": rows[(pn, i, g)]["cg_mm"],
                            "group": "engine", "attach": ("member", nid)})
        b3 = B["GM-03"]
        mseat = sel_cyl(b3, (0, 0, 0), EY, 11.0, *(sorted((42.0 * sgn, 49.0 * sgn))))
        rho = np.hypot(b3.fc[:, 0], b3.fc[:, 2])
        msh = sel_plane(b3, EY, (0, 42.0 * sgn, 0)) & (rho >= 7.4) & (rho <= 11.1)
        keyS = [("HW-20", j - 1, "ring", 1)]
        refS = M.rigid_conn(f"SEAT_IN_{j}", [("GM-03", mseat | msh)], (0, 45.5 * sgn, 0), "ring", [(np.asarray(rows[keyS[0][:3]]["cg_mm"]), "ring")])
        M.items.append({"label": f"SEAT_IN_{j}", "items": [f"HW-20#{j - 1}"], "m_kg": rows[keyS[0][:3]]["m_kg"], "cg": rows[keyS[0][:3]]["cg_mm"],
                        "group": "ring", "attach": ("member", M.members[f"SEAT_IN_{j}"][0])})
        # locating bearing = +Y only (axial spring); -Y floats axially (no artificial thermal axial load, see report)
        M.bushing2(f"BRG_IN_{j}", refP, refS, [EX, EZ, EY], [bk["k_in_radial"], bk["k_in_radial"], bk["k_axial"] if j == 1 else 0.0], "engine")
    for k, sgn, post in (((1, +1, "GM-08a"), (2, -1, "GM-08b")) if A3.CAD == "v35" else ()):
        b3 = B["GM-03"]
        mpin = sel_cyl(b3, (0, 0, 0), EX, 4.0, *(sorted((40.8 * sgn, 49.0 * sgn))))
        keys = [("GM-05", k - 1, "ring", 1), ("GM-07", k - 1, "ring", 1), ("HW-21", k + 1, "ring", 1)] + ([("EL-06", 1, "ring", 1)] if k == 2 else [])
        mem = [(np.asarray(rows[key[:3]]["cg_mm"]), "ring") for key in keys]
        refP = M.rigid_conn(f"PIN_OUT_{k}", [("GM-03", mpin)], (54.5 * sgn, 0, 0), "ring", mem)
        for key, nid in zip(keys, M.members[f"PIN_OUT_{k}"]):
            M.items.append({"label": f"PIN_OUT_{k}", "items": [f"{key[0]}#{key[1]}"], "m_kg": rows[key[:3]]["m_kg"], "cg": rows[key[:3]]["cg_mm"],
                            "group": "ring", "attach": ("member", nid)})
        bp = B[post]
        mseat = sel_cyl(bp, (0, 0, 0), EX, 11.0, *(sorted((51.0 * sgn, 58.0 * sgn))))
        rho = np.hypot(bp.fc[:, 1], bp.fc[:, 2])
        msh = sel_plane(bp, EX, (51.0 * sgn, 0, 0)) & (rho >= 7.4) & (rho <= 11.1)
        key = ("HW-20", k + 1, "fixed")
        refS = M.rigid_conn(f"SEAT_OUT_{k}", [(post, mseat | msh)], (54.5 * sgn, 0, 0), "fixed", [(np.asarray(rows[key]["cg_mm"]), "fixed")])
        M.items.append({"label": f"SEAT_OUT_{k}", "items": [f"HW-20#{k + 1}"], "m_kg": rows[key]["m_kg"], "cg": rows[key]["cg_mm"],
                        "group": "fixed", "attach": ("member", M.members[f"SEAT_OUT_{k}"][0])})
        M.bushing2(f"BRG_OUT_{k}", refP, refS, [EY, EZ, EX], [bk["k_out_radial"], bk["k_out_radial"], bk["k_axial"] if k == 1 else 0.0], "ring")

    # ---------------------------------------------------------------- TVC: servo (rigid case + horn spline), horn eye, lever eye, rod
    g = M.g
    for sv in g["servos"]:
        i = sv["i"]
        brk, horn, coll = ("GM-13", "GM-16a", "GM-01") if i == 1 else ("GM-14", "GM-16b", "GM-02")
        gm15 = f"ENG-GM-15_{i - 1}"
        bb, bh, bc = B[brk], B[horn], B[coll]
        ysg = 1.0 if i == 1 else -1.0
        ear_ax = np.array([0.981, 0.196 * ysg, 0.0])
        ear_pts = [np.array([-11.56, 49.32 * ysg, zz]) for zz in (-35.4, -84.9)] + [np.array([-13.52, 59.13 * ysg, zz]) for zz in (-35.4, -84.9)]
        mear = np.zeros(len(bb.fa), bool)
        near_ear = np.zeros(len(bb.fa), bool)
        for p in ear_pts:
            mear |= sel_cyl(bb, p, ear_ax, 1.65, -30, 30)
            near_ear |= line_dist(bb.fc, p, ear_ax)[0] <= 4.5
        mtouch = M.faces_near_instance(brk, gm15, tol=0.3) & near_ear
        spl_ax = unit(sv["et"])
        mspl = sel_cyl(bh, sv["C"], spl_ax, 2.95, -1e9, 1e9)
        d_sh, _ = line_dist(bh.fc, sv["C"], spl_ax)
        mhub = M.faces_near_instance(horn, gm15, tol=0.3) & (d_sh <= 6.0)
        keys = [("GM-15", i - 1, "fixed"), ("HW-25", i - 1, "horn")]
        mem = [(np.asarray(rows[keys[0]]["cg_mm"]), "fixed"), (np.asarray(rows[keys[1]]["cg_mm"]), f"horn{i}")]
        M.rigid_conn(f"SERVO_{i}", [(brk, mear | mtouch), (horn, mspl | mhub)], sv["O"], "fixed", mem)
        for key, nid in zip(keys, M.members[f"SERVO_{i}"]):
            M.items.append({"label": f"SERVO_{i}", "items": [f"{key[0]}#{key[1]}"], "m_kg": rows[key]["m_kg"], "cg": rows[key]["cg_mm"],
                            "group": key[2], "attach": ("member", nid)})
        # horn eye
        de, _ = line_dist(bh.fc, sv["P_h0"], spl_ax)
        meye = de <= 3.8
        kH = [("GM-19", 0 if i == 1 else 3, "horn", 1), ("GM-19", 1 if i == 1 else 4, "horn", 1), ("GM-20", i - 1, "horn", 1),
              ("HW-22-IR", 0 if i == 1 else 2, "horn", 1), ("HW-22", 0 if i == 1 else 2, "pushrod", 1), ("GM-17", i - 1, "pushrod", 0.5)]
        mH = [(np.asarray(sv["P_h0"]) if k_[0] in ("GM-17", "HW-22") else np.asarray(rows[k_[:3]]["cg_mm"]), f"horn{i}") for k_ in kH]
        refH = M.rigid_conn(f"HEYE_{i}", [(horn, meye)], sv["P_h0"], f"horn{i}", mH)
        for k_, nid in zip(kH, M.members[f"HEYE_{i}"]):
            M.items.append({"label": f"HEYE_{i}", "items": [f"{k_[0]}#{k_[1]}x{k_[3]}"], "m_kg": rows[k_[:3]]["m_kg"] * k_[3],
                            "cg": list(M.xyz0(nid)), "group": f"horn{i}", "attach": ("member", nid)})
        # lever eye on the collar
        dl, _ = line_dist(bc.fc, sv["P_l0"], spl_ax)
        mlev = dl <= 3.76
        kL = [("GM-18", i - 1, "engine", 1), ("GM-19", 2 if i == 1 else 5, "engine", 1), ("HW-22-IR", 1 if i == 1 else 3, "engine", 1),
              ("HW-22", 1 if i == 1 else 3, "pushrod", 1), ("GM-17", i - 1, "pushrod", 0.5)]
        mL = [(np.asarray(sv["P_l0"]) if k_[0] in ("GM-17", "HW-22") else np.asarray(rows[k_[:3]]["cg_mm"]), "engine") for k_ in kL]
        refL = M.rigid_conn(f"LEYE_{i}", [(coll, mlev)], sv["P_l0"], "engine", mL)
        for k_, nid in zip(kL, M.members[f"LEYE_{i}"]):
            M.items.append({"label": f"LEYE_{i}", "items": [f"{k_[0]}#{k_[1]}x{k_[3]}"], "m_kg": rows[k_[:3]]["m_kg"] * k_[3],
                            "cg": list(M.xyz0(nid)), "group": "engine", "attach": ("member", nid)})
        if M.v.get("conn", "v12") == "legacy":          # runs solved with fea3d-asm <= v1.1 (reload only)
            e = M.spring_a(f"ROD_{i}", refH, refL, M.k_chain)
            M.bush.append({"label": f"ROD_{i}", "A": int(refH), "B": int(refL), "springs": [(refL, e, None, M.k_chain)]})
            continue
        # rod: SPRINGA from the horn eye to an aux node 1e6 mm along the POSED rod line (group 'fixed' = identity pose), aux tied to the
        # lever eye (u_aux = u_L): linear axial rod spring along the undeformed posed direction (REPORT 7.1)
        xHp, xLp = M.xyzp([refH])[0], M.xyzp([refL])[0]
        e_rod = unit(xLp - xHp)
        aux = M.new_node(xHp + SPRING_OFF_MM * e_rod, "fixed")
        for d in (1, 2, 3):
            M.C.add_raw(f"ROD_{i}_aux", [(aux, d, 1.0), (refL, d, -1.0)])
        M.C.protected.add(aux)
        e = M.spring_a(f"ROD_{i}", refH, aux, M.k_chain)
        M.bush.append({"label": f"ROD_{i}", "A": int(refH), "B": int(refL), "springs": [(aux, e, [float(c) for c in e_rod], M.k_chain)],
                       "rod_length_mm": float(np.linalg.norm(xLp - xHp))})

    # ---------------------------------------------------------------- engine joints
    # J-FWD: 8 x M5 radial screws case -> head (bushings between RBE3 refs at the shear plane r 28.6)
    for k in range(8):
        phi = math.radians(22.5 + 45 * k)
        er = np.array([math.cos(phi), math.sin(phi), 0.0])
        et = np.array([-math.sin(phi), math.cos(phi), 0.0])
        zc = np.array([0, 0, 127.51])
        mA = sel_cyl(B["TC-01"], zc, er, 2.75, 28.3, 31.9)
        mB = sel_cyl(B["TC-02"], zc, er, 2.1, 21.9, 28.8)
        if not mA.any() or not mB.any():
            raise RuntimeError(f"J-FWD {k}: hole faces not found ({mA.sum()}, {mB.sum()})")
        x = zc + 28.6 * er
        rA = M.rbe3_ref(f"JF{k}_case", [("TC-01", mA)], x, "engine")
        rB = M.rbe3_ref(f"JF{k}_head", [("TC-02", mB)], x, "engine")
        M.bushing2(f"JF{k}", rA, rB, [er, et, EZ], [K_JFWD_AXIAL, K_JFWD_SHEAR, K_JFWD_SHEAR], "engine")
    # PD-01 feet: 4 x M2.5 through G11 washers into the head top (bushings)
    for body, ys, ztop in (("PD-01R", 24.43, 175.6), ("PD-01S", -24.43, 176.6)):
        for xs in (-8.89, 8.89):
            p = np.array([xs, ys, 0.0])
            bp, bh = B[body], B["TC-02"]
            mA = sel_cyl(bp, p, EZ, 1.7, 171.4, ztop) | (sel_plane(bp, EZ, (0, 0, 171.51)) & (line_dist(bp.fc, p, EZ)[0] <= 3.5))
            mB = sel_cyl(bh, p, EZ, 1.25, 161.4, 169.6) | (sel_plane(bh, EZ, (0, 0, 169.51)) & (line_dist(bh.fc, p, EZ)[0] <= 3.5))
            if not mA.any() or not mB.any():
                raise RuntimeError(f"PD foot {body} {xs}: faces not found ({mA.sum()}, {mB.sum()})")
            x = np.array([xs, ys, 170.51])
            rA = M.rbe3_ref(f"PDF_{body}_{'p' if xs > 0 else 'm'}", [(body, mA)], x, "engine")
            rB = M.rbe3_ref(f"PDH_{body}_{'p' if xs > 0 else 'm'}", [("TC-02", mB)], x, "engine")
            M.bushing2(f"PDFOOT_{body}_{'p' if xs > 0 else 'm'}", rA, rB, [EX, EY, EZ], list(K_PDFOOT), "engine")
    # PD-02 crank housing: rigid connector over its contact faces on both PD-01 pieces (+ drive items, needle load point)
    mR = M.faces_near_instance("PD-01R", "ENG-PD-02_0", tol=0.25)
    mS = M.faces_near_instance("PD-01S", "ENG-PD-02_0", tol=0.25)
    kD = [("PD-02", 0, "engine", 1), ("PD-03", 0, "engine", 1), ("PD-04", 0, "engine", 1), ("PD-05", 0, "engine", 1), ("PD-09", 0, "engine", 1),
          ("PD-14", 0, "engine", 1), ("PD-15", 0, "engine", 1), ("PD-18", 0, "engine", 1), ("EL-05", 0, "engine", 1)]
    mD, cD = m_of(kD)
    M.rigid_conn("PD02", [("PD-01R", mR), ("PD-01S", mS)], (0.0, 9.59, 237.71), "engine", [(cD, "engine"), (np.array([0.0, 0.0, 237.4]), "engine")])
    M.items.append({"label": "PD02_DRIVE", "items": [k_[0] for k_ in kD], "m_kg": mD, "cg": list(cD), "group": "engine",
                    "attach": ("member", M.members["PD02"][0])})
    M.needle_node = M.members["PD02"][1]

    # ---------------------------------------------------------------- ties (after all connectors: protected nodes known)
    vt = M.v["ties"]
    rule_thr = "zt" if vt == "design" else "bond"
    b1, b9 = B["TC-01"], B["TC-09"]
    M.tie("TC09_TC01_thread", "TC-09", "TC-01", rule_thr, tol=0.12,
          mask_dep=sel_cyl(b9, (0, 0, 0), EZ, 31.51, -147.49, -133.49), mask_ind=sel_cyl(b1, (0, 0, 0), EZ, 31.5, -147.49, -133.49))
    if A3.CAD == "v351" and M.v.get("tb1", "faces") == "thread":
        # TB1 thread variant (v3.5.1): shoulder tie (flange top r 7-10 on the pocket ceiling) + axial/tangential tie along the M14
        # engagement (TC-03 major cylinder R7 -> TC-02 minor bore R6.5, CAD overlap 0.5 mm; radial free), NO end-face tie (the end
        # contact at z 117.51 opens when the 6061 head outgrows the GlidCop insert).  Design model ('faces'): every touching face pair.
        info_, _ = sax_info()
        z_sh, z_tt = info_["z_seat"] - 1.0, info_["z_seat"] + 9.0
        b3_, b2_ = B["TC-03"], B["TC-02"]
        m_sh3 = sel_plane(b3_, EZ, (0, 0, z_sh), side=+1)
        m_sh2 = sel_plane(b2_, EZ, (0, 0, z_sh), side=-1)
        M.tie("TC03_TC02_shoulder", "TC-03", "TC-02", rule_thr, tol=0.12, mask_dep=m_sh3, mask_ind=m_sh2)
        m_th3 = sel_cyl(b3_, (0, 0, 0), EZ, 7.0, z_sh, z_tt)
        m_th2 = sel_cyl(b2_, (0, 0, 0), EZ, 6.5, z_sh, z_tt)
        M.tie("TC03_TC02_thread", "TC-03", "TC-02", "zt", tol=1.2, mask_dep=m_th3, mask_ind=m_th2)
    else:
        M.tie("TC03_TC02_seat", "TC-03", "TC-02", rule_thr, tol=0.12)
    bt4, bt2 = B["TC-04"], B["TC-02"]
    md = np.zeros(len(bt4.fa), bool)
    mi = np.zeros(len(bt2.fa), bool)
    for az in (60, 120, 240, 300):
        p = 16.5 * np.array([math.cos(math.radians(az)), math.sin(math.radians(az)), 0.0])
        md |= sel_plane(bt4, EZ, (0, 0, 169.51), side=-1) & (line_dist(bt4.fc, p, EZ)[0] <= 4.0)
        mi |= sel_plane(bt2, EZ, (0, 0, 169.51), side=+1) & (line_dist(bt2.fc, p, EZ)[0] <= 4.6)
    M.tie("TC04_TC02_bolts", "TC-04", "TC-02", "bond", tol=0.12, mask_dep=md, mask_ind=mi)
    bf = B["FD-01"]
    md = np.zeros(len(bf.fa), bool)
    mi = np.zeros(len(bt2.fa), bool)
    for zs in (144.31, 166.71):
        p = np.array([0.0, 0.0, zs])
        md |= sel_plane(bf, EX, (-30.5, 0, 0), side=+1) & (line_dist(bf.fc, p, EX)[0] <= 4.0)
        mi |= sel_plane(bt2, EX, (-30.5, 0, 0), side=-1) & (line_dist(bt2.fc, p, EX)[0] <= 4.6)
    M.tie("FD01_TC02_screws", "FD-01", "TC-02", "bond", tol=0.12, mask_dep=md, mask_ind=mi)
    M.tie("NZ04_TC09_lip", "NZ-04", "TC-09", rule_thr, tol=0.12)
    M.tie("NZ04_NZ03", "NZ-04", "NZ-03", "bond", tol=0.12)
    M.tie("NZ03_NZ01", "NZ-03", "NZ-01", "bond", tol=0.12)
    M.tie("NZ03_NZ02", "NZ-03", "NZ-02", "bond", tol=0.12)
    # collar
    # 2026-10-19 (modal under the 8 GB cap, TC-01 at mesh level 2): the coarse TC-01 bore faces straddle the +/-10 mm band and their
    # chords sit up to ~0.5 mm off the collar bore, so the L1 rule kept 15 of ~2850 equations.  Only when TC-01 is overridden to level >= 2:
    # independent band +/-16 mm and tie tolerance 0.6 mm (bond with the chord gap; F1 / pose models at L1 are unchanged).
    _lv1 = (M.v.get("levels") or {}).get("TC-01", 1.0)
    _band, _tolb = ((-16.0, 16.0), 0.6) if _lv1 >= 2 else ((-10.0, 10.0), 0.12)
    for coll in ("GM-01", "GM-02"):
        bc = B[coll]
        bore_d = sel_cyl(bc, (0, 0, 0), EZ, 31.25, -10.0, 10.0)
        bore_i = sel_cyl(b1, (0, 0, 0), EZ, 31.25, *_band)
        if M.v["collar"] == "bonded":
            M.tie(f"{coll}_TC01_bore", coll, "TC-01", "bond", tol=_tolb, mask_dep=bore_d, mask_ind=bore_i)
        else:
            M.tie(f"{coll}_TC01_bore", coll, "TC-01", "rt", tol=0.12, mask_dep=bore_d, mask_ind=bore_i)
            fl_d = sel_plane(bc, EZ, (0, 0, -9.95), side=-1, tol=0.03)
            fl_i = sel_plane(b1, EZ, (0, 0, -10.0), side=+1, tol=0.03)
            M.tie(f"{coll}_TC01_aftflank", coll, "TC-01", "z", tol=0.12, mask_dep=fl_d, mask_ind=fl_i)
    M.tie("GM02_GM01_clamp", "GM-02", "GM-01", "bond", tol=0.12)
    # frame
    for dep, ind in (("GM-08a", "GM-09"), ("GM-08a", "GM-10"), ("GM-08b", "GM-09"), ("GM-08b", "GM-10"), ("GM-13", "GM-10"), ("GM-14", "GM-10")):
        M.tie(f"{dep}_{ind}", dep, ind, "bond", tol=0.12)

    # ---------------------------------------------------------------- mass items distributed on faces (RBE3 force distribution)
    fni = lambda body, stem: M.faces_near_instance(body, stem, tol=0.5, corners=False)

    def item(label, keys, faces, grp):
        mm, cg = m_of(keys)
        if not any(np.asarray(s).any() for _, s in faces):
            raise RuntimeError(f"mass item {label}: no attachment faces")
        M.items.append({"label": label, "items": [f"{k_[0]}#{k_[1]}" + (f"x{k_[3]:g}" if k_[3] != 1 else "") for k_ in keys], "m_kg": mm,
                        "cg": list(cg), "group": grp, "attach": ("faces", faces)})
    # grain + liner in 10 axial bands of the case bore (wet grain)
    zb = np.linspace(-156.49, 73.51, 11)
    rr = np.hypot(b1.fc[:, 0], b1.fc[:, 1])
    radial_in = np.einsum("ij,ij->i", b1.fn, np.column_stack([b1.fc[:, 0], b1.fc[:, 1], 0 * rr]) / np.maximum(rr, 1e-9)[:, None]) < -0.5
    for s in range(10):
        z0, z1 = zb[s], zb[s + 1]
        zm = 0.5 * (z0 + z1)
        keys = [("TC-07", 0, "engine", 0.1)] + ([("GR-01", 0, "engine", 0.2)] if zm > -41.49 else [("GR-02", 0, "engine", 0.2)])
        msk = (rr < 28.7) & radial_in & (b1.fc[:, 2] >= z0) & (b1.fc[:, 2] < z1)
        item(f"GRAIN_{s}", keys, [("TC-01", msk)], "engine")
    item("TC06", [("TC-06", 0, "engine", 1)], [("TC-01", (rr < 28.7) & radial_in & (b1.fc[:, 2] >= 73.51) & (b1.fc[:, 2] < 103.6))], "engine")
    item("TC08", [("TC-08", 0, "engine", 1)], [("TC-09", fni("TC-09", "ENG-TC-08_0")),
                                               ("TC-01", fni("TC-01", "ENG-TC-08_0"))], "engine")
    item("TC10", [("TC-10", 0, "engine", 1)], [("TC-02", fni("TC-02", "ENG-TC-10_0"))], "engine")
    item("TORCH", [("IG-01", 0, "engine", 1), ("IG-02", 0, "engine", 1), ("IG-02", 1, "engine", 1)],
         [("TC-02", fni("TC-02", "ENG-IG-01_0"))], "engine")
    item("BLEED", [("BL-01", 0, "engine", 1), ("BL-02", 0, "engine", 1), ("BL-03A", 0, "engine", 1), ("BL-03E", 0, "engine", 1),
                   ("BL-04A", 0, "engine", 1), ("BL-04", 0, "engine", 1)], [("FD-01", fni("FD-01", "ENG-BL-02_0"))], "engine")
    item("FD02", [("FD-02", 0, "engine", 1)], [("TC-02", fni("TC-02", "ENG-FD-02_0"))], "engine")
    item("RISER", [("FD-03", 0, "engine", 1), ("FD-05", 0, "engine", 1), ("FD-07A", 0, "engine", 1), ("FD-07", 0, "engine", 1)],
         [("FD-01", fni("FD-01", "ENG-FD-03_0"))], "engine")
    item("FD04", [("FD-04", 0, "engine", 1)], [("TC-01", fni("TC-01", "ENG-FD-04_0"))], "engine")
    item("RAIL", [("PD-06", 0, "engine", 1), ("PD-07", 0, "engine", 1), ("PD-08", 0, "engine", 1), ("PD-16", 0, "engine", 1),
                  ("PD-17", 0, "engine", 1), ("PD-17", 1, "engine", 1), ("PD-19", 0, "engine", 1), ("TC-05", 0, "engine", 1), ("TC-11", 0, "engine", 1)],
         [("PD-01R", fni("PD-01R", "ENG-PD-19_0")), ("PD-01S", fni("PD-01S", "ENG-PD-19_0"))], "engine")
    fS = fni("PD-01S", "ENG-PD-13_0") | fni("PD-01S", "ENG-PD-12_0") \
        | fni("PD-01S", "ENG-PD-20_0") | fni("PD-01S", "ENG-PD-20_1")
    fR = fni("PD-01R", "ENG-PD-13_0") | fni("PD-01R", "ENG-PD-12_0")
    item("SERVO_PLATE", [("PD-13", 0, "engine", 1), ("PD-12", 0, "engine", 1), ("PD-10", 0, "engine", 1), ("PD-20", 0, "engine", 1),
                         ("PD-20", 1, "engine", 1)], [("PD-01S", fS), ("PD-01R", fR)], "engine")
    fW = np.zeros(len(bt2.fa), bool)
    for q in range(4):
        fW |= fni("TC-02", f"ENG-PD-11_{q}")
    item("PD11_WASHERS", [("PD-11", q, "engine", 1) for q in range(4)], [("TC-02", fW)], "engine")
    item("EL03", [("EL-03", 0, "ring", 1)], [("GM-03", nearest_faces(B["GM-03"], (0, 55.7, 0)))], "ring")
    item("GM11", [("GM-11", 0, "fixed", 1)], [("GM-10", fni("GM-10", "ENG-GM-11_0"))], "fixed")
    item("EL04", [("EL-04", 0, "fixed", 1)], [("GM-08b", nearest_faces(B["GM-08b"], (-64.7, 0, 0)))], "fixed")
    item("FD09_BRACKET", [("FD-09", 0, "fixed", 1), ("FD-07B", 0, "fixed", 1), ("FD-07", 0, "fixed", 1)],
         [("GM-09", fni("GM-09", "ENG-FD-09_0"))], "fixed")
    if A3.CAD == "v351":
        _hardware_items(M, B, mp)
    M.notes.append(f"define(): {time.time() - t0:.1f} s")
    return M


def mass_check(M: Asm):
    """Meshed volume x density + items vs massprops (wet).  Returns a table."""
    rows, mp, gfac = ledger()
    st = mp["states"][LEDGER_STATE]
    grp_mass = {}
    body_rows = []
    for nm, b in M.bodies.items():
        rho = engmat.MATERIALS[b.mat]["rho"]["v"]
        V = float(fe3d.tet_vol(b.X0, b.T10).sum())
        m = rho * V * 1e-9
        pn = nm.replace("a", "").replace("b", "") if nm.startswith("GM-08") or nm.startswith("GM-16") else nm
        g = {"engine": "engine", "ring": "ring", "fixed": "fixed", "horn1": "horn", "horn2": "horn"}[b.grp]
        grp_mass[g] = grp_mass.get(g, 0.0) + m
        body_rows.append({"body": nm, "group": g, "material": b.mat, "V_mm3": V, "m_kg": m})
    for it in M.items:
        g = it["group"]
        g = "horn" if g.startswith("horn") else g
        if any(s.startswith("GM-17") or s.startswith("HW-22#") for s in it["items"]):
            pass
        grp_mass[g] = grp_mass.get(g, 0.0) + it["m_kg"]
    ref = {g: st[g]["m_kg"] for g in ("engine", "ring", "fixed", "horn", "pushrod")}
    # PD-01 ledger is one row for both pieces; GM-08/GM-16 split: compare per ledger part
    led = {}
    for (pn, i, g), r in rows.items():
        led[(pn, g)] = led.get((pn, g), 0.0) + r["m_kg"]
    return {"group_model_kg": grp_mass, "group_massprops_wet_kg": ref, "bodies": body_rows,
            "note": "pushrod items are placed on the eye rigid bodies of the horn (group horn) and collar (group engine)"}


# =============================================================================================== pressure
def sax_info():
    g = json.loads(A3.SAX_GEOM.read_text())
    info = g["info"]
    c = np.array(info["contour"])
    o = np.argsort(c[:, 0])
    rc = lambda z: float(np.interp(z, c[o, 0], c[o, 1]))
    return info, rc


def gas_profile(info):
    rows = [r for r in csv.reader(l for l in open(A3.COMB_BC) if not l.startswith("#"))]
    hdr = rows[0]
    ix, ip = hdr.index("x_face_m"), hdr.index("p_Pa")
    rows = [r for r in rows[1:] if len(r) > ip and r[ip].strip()]
    x = np.array([float(r[ix]) for r in rows])
    p = np.array([float(r[ip]) for r in rows])
    z = info["inj_face"] - 1e3 * x
    o = np.argsort(z)
    pc = p.max()
    return (lambda zz: np.interp(zz, z[o], p[o] / pc)), {"src": A3.COMB_BC.name, "sha256_16": A3.sha16(A3.COMB_BC), "Pc_Pa": float(pc),
                                                          "p_exit_over_Pc": float(p[o][0] / pc)}


def classify_sax(part, r, z, info, rc):
    """Port of Mechanical sax.classify (S-AX v1, 2026-10-13) for one probe point (r, z) of the v3.4.1 frame."""
    g1, g2, gw = info["fwd_glands"]
    z_fwd_seal = g1 + gw
    zg0, gwa, gdia = info["aft_gland"]
    z_aft_seal = zg0 + gwa
    z_lipseal = info["lip_top"] + info["nz_seal_t"]
    ht = info["head_top"]
    if part in ("TC-02", "TC-03", "TC-04"):
        if r < 5.3 and info["z_seat"] < z < info["bonnet_top"] - 9.0:
            return "PM"
        if abs(z - ht) < 1.4 and r < 7.25:
            return "PM"
        if part == "TC-03" and z <= info["z_seat"] and r < 10.5:
            return "PC"
        if part == "TC-02" and r < 28.6 and z < z_fwd_seal:
            return "PC"
        return "AMB"
    if part == "TC-01":
        if r < 28.6 and z < z_fwd_seal and z > info["tube_aft"] - 0.2:
            return "PC"
        if r < 30.6 and z_lipseal < z < z_aft_seal:
            return "PC"
        if 30.3 < r < gdia / 2 + 0.1 and zg0 - 0.1 < z < z_aft_seal + 0.1:
            return "PC"
        return "AMB"
    if part == "TC-09":
        r_in = 30.6 if z > info["aft_step"] + 0.01 else info["r_insert_bore"] + 0.05
        if r < r_in and z_lipseal < z < z_aft_seal:
            return "PC"
        if 30.3 < r < gdia / 2 + 0.1 and zg0 - 0.1 < z < z_aft_seal + 0.1:
            return "PC"
        return "AMB"
    if z < info["exit"] + 1e-3 and r < info["re"] + 0.5:
        return "AMB"
    if info["exit"] <= z <= info["insert_top"] + 0.3 and r <= rc(z) + 0.3:
        return "GAS"
    if part in ("NZ-03", "NZ-04") and r < 16.0:
        return "AMB"
    if z < info["lip_top"] + 1e-3:
        return "AMB"
    if part == "NZ-01" and r < 15.6 and z < info["insert_shoulder"] + 0.05:
        return "AMB"
    return "PC"


R_SEAT, R_STEM = 2.75, 1.525      # mm: TC-03 orifice (seat) radius at z 108.51 and TC-04 stem bore at the stem seal (CAD v3.5 entities)
NSUB = 4                          # sub-triangles per face edge for the pressure classification (16 equal-area samples per face)


def classify_v(part, r, z, info, rc):
    """Vectorised classify_sax (same rule order: first match wins).  Returns codes 0 AMB, 1 PC, 2 GAS, 3 PM."""
    out = np.full(r.shape, -1, np.int8)

    def put(m, c):
        sel = (out < 0) & m
        out[sel] = c
    g1, g2, gw = info["fwd_glands"]
    z_fwd_seal = g1 + gw
    zg0, gwa, gdia = info["aft_gland"]
    z_aft_seal = zg0 + gwa
    z_lipseal = info["lip_top"] + info["nz_seal_t"]
    ht = info["head_top"]
    if part in ("TC-02", "TC-03", "TC-04"):
        put((r < 5.3) & (z > info["z_seat"]) & (z < info["bonnet_top"] - 9.0), 3)
        put((np.abs(z - ht) < 1.4) & (r < 7.25), 3)
        if part == "TC-03":
            put((z <= info["z_seat"]) & (r < 10.5), 1)
        if part == "TC-02":
            put((r < 28.6) & (z < z_fwd_seal), 1)
    elif part == "TC-01":
        put((r < 28.6) & (z < z_fwd_seal) & (z > info["tube_aft"] - 0.2), 1)
        put((r < 30.6) & (z > z_lipseal) & (z < z_aft_seal), 1)
        put((r > 30.3) & (r < gdia / 2 + 0.1) & (z > zg0 - 0.1) & (z < z_aft_seal + 0.1), 1)
    elif part == "TC-09":
        r_in = np.where(z > info["aft_step"] + 0.01, 30.6, info["r_insert_bore"] + 0.05)
        put((r < r_in) & (z > z_lipseal) & (z < z_aft_seal), 1)
        put((r > 30.3) & (r < gdia / 2 + 0.1) & (z > zg0 - 0.1) & (z < z_aft_seal + 0.1), 1)
    else:
        rcz = np.array([rc(zz) for zz in z.ravel()]).reshape(z.shape)
        put((z < info["exit"] + 1e-3) & (r < info["re"] + 0.5), 0)
        put((z >= info["exit"]) & (z <= info["insert_top"] + 0.3) & (r <= rcz + 0.3), 2)
        if part in ("NZ-03", "NZ-04"):
            put(r < 16.0, 0)
        put(z < info["lip_top"] + 1e-3, 0)
        if part == "NZ-01":
            put((r < 15.6) & (z < info["insert_shoulder"] + 0.05), 0)
        put(np.ones(r.shape, bool), 1)
    put(np.ones(r.shape, bool), 0)
    return out


def face_samples(b, n=NSUB):
    """Centroids of the n^2 equal-area sub-triangles of every boundary face (m, n^2, 3), neutral frame."""
    L = []
    for i in range(n):
        for j in range(n - i):
            L.append((1.0 - (i + 1 / 3) / n - (j + 1 / 3) / n, (i + 1 / 3) / n, (j + 1 / 3) / n))
            if i + j < n - 1:
                L.append((1.0 - (i + 2 / 3) / n - (j + 2 / 3) / n, (i + 2 / 3) / n, (j + 2 / 3) / n))
    L = np.asarray(L)
    return np.einsum("sk,mkd->msd", L, b.X0[b.bf_n[:, :3]])


def in_capsule(P, pt, ax, R, s0, s1, tolR=0.02):
    ax = unit(ax)
    v = P - np.asarray(pt, float)
    s = v @ ax
    d = np.linalg.norm(v - s[..., None] * ax, axis=-1)
    return (d <= R + tolR) & (s >= s0) & (s <= s1)


def pressure_sets(M: Asm):
    """Unit pressure loads OP (chamber 1 MPa, nozzle profile p(z)/Pc) and PM (manifold 1 MPa).  Every face is classified on 16
    equal-area sub-triangles (probe 0.05 mm off the face), so class boundaries that cut faces (S01 seal line, port edges) carry the
    exact area fraction; tie coverage (sub-triangle within tol of the tied partner surface) removes pressure from internal contact
    areas.  Port caps, the FD-01 cartridge cap and the pintle needle loads are applied as RBE3-distributed / nodal forces."""
    info, rc = sax_info()
    prof, prov = gas_profile(info)
    B = M.bodies
    # coverage by ties (per sub-sample)
    cover = {}
    for label, dep, ind, md, mi, tol in getattr(M, "tie_masks", []):
        for a, bpart, ma, mb in ((dep, ind, md, mi), (ind, dep, mi, md)):
            ba, bb = B[a], B[bpart]
            idx = np.nonzero(ma)[0]
            if not len(idx) or not mb.any():
                continue
            S = face_samples(ba)[idx]
            dist, _, _ = fe3d.project_points(S.reshape(-1, 3), bb.X0, bb.bf_n[mb], bb.fc[mb], k=8)
            cv = cover.setdefault(a, np.zeros((len(ba.fa), S.shape[1]), bool))
            cv[idx] |= (dist.reshape(S.shape[:2]) <= tol + 0.03)
    codes, Ssamp = {}, {}
    for nm in A3.SAX_PARTS + ["FD-01"]:
        b = B[nm]
        S = face_samples(b)
        Ssamp[nm] = S
        if nm in A3.SAX_PARTS:
            Pp = S + 0.05 * b.fn[:, None, :]
            codes[nm] = classify_v(nm, np.hypot(Pp[..., 0], Pp[..., 1]), Pp[..., 2], info, rc)
        else:
            codes[nm] = np.zeros(S.shape[:2], np.int8)
    over = {}
    S2, S4 = Ssamp["TC-02"], Ssamp["TC-04"]
    caps2 = [("pc_tap", in_capsule(S2, (-18.0, 14.07, 132.51), (0.061, -0.048, -0.997), 1.0, -27.21, 27.21), 1),
             ("pc_counterbore", in_capsule(S2, (-19.7, 15.39, 0.0), EZ, 4.35, 159.49, 169.52), 1),
             ("torch_drill", in_capsule(S2, (23.17, 0.0, 134.61), (-0.072, 0.0, -0.997), 2.6, -25.2, 25.25), 1),
             ("torch_outlet", in_capsule(S2, (19.18, 0.0, 107.49), (-0.5, 0.0, -0.866), 1.5, -3.2, 3.2), 1),
             ("torch_counterbore", in_capsule(S2, (25.0, 0.0, 0.0), EZ, 4.5, 159.49, 169.52), 1),
             ("filter_bore", in_capsule(S2, (0.0, 0.0, 155.51), EX, 7.0, -30.52, -4.5), 3),
             ("E1M_axial_head", in_capsule(S2, (-16.0, 0.0, 0.0), EZ, 4.0, 155.0, 169.52), 3),
             ("E1M_seal_head_top", (np.abs(S2[..., 2] - 169.51) < 0.02) & (np.hypot(S2[..., 0] + 16.0, S2[..., 1]) <= 6.5), 3)]
    caps4 = [("E1M_seal_bonnet", (S4[..., 2] < 170.83) & (np.hypot(S4[..., 0] + 16.0, S4[..., 1]) <= 6.5), 3),
             ("E1M_axial_bonnet", in_capsule(S4, (-16.0, 0.0, 0.0), EZ, 4.0, 169.49, 191.53), 3),
             ("cross_drill", in_capsule(S4, (0.0, 0.0, 187.51), EX, 4.0, -17.95, -3.9), 3),
             ("port_M10", in_capsule(S4, (0.0, 0.0, 187.51), EX, 4.35, -28.02, -17.85), 3)]
    for nm, lst in (("TC-02", caps2), ("TC-04", caps4)):
        over[nm] = {}
        for lab, m, c in lst:
            codes[nm][m] = c
            over[nm][lab] = {"faces_touched": int(m.any(1).sum()), "area_mm2": round(float((m.mean(1) * B[nm].fa).sum()), 2)}
    op_override = {}
    if A3.CAD == "v351":
        # TB1 joint (v3.5.1): TC-03 (GlidCop) screwed into TC-02 (thread engagement z 107.51-117.51, CAD solids overlap between the
        # internal-thread minor radius 6.5 and the external major radius 7.0) with its flange shoulder (r 7.0-10.0, z 107.51) seated on
        # the TC-02 pocket ceiling (r 6.5-10.1).  Same seal assumption as S-AX: the shoulder contact is the Pc boundary, the thread
        # is dry (AMB).  The sub-face tie coverage (tol + 0.03 mm) otherwise leaves the r 6.5-7.27 ceiling strip loaded (+36 N/MPa
        # spurious forward force) and covers the wetted r 10.0-10.1 ring of the pocket gap (-6.3 N/MPa).  Geometry from the CAD
        # section of ENG-TC-02 / ENG-TC-03 v3.5.1 (fea3d section_head.py, 2026-10-13).
        z_sh, r_fl, r_mi, r_ma, z_tt = info["z_seat"] - 1.0, 10.0, 6.5, 7.0, info["z_seat"] + 9.0
        over["TB1"] = {}
        for nm in ("TC-02", "TC-03"):
            b = B[nm]
            V = b.X0[b.bf_n[:, :3]]
            rv, zv = np.hypot(V[..., 0], V[..., 1]), V[..., 2]
            # face-level tests (a sample test would also catch the cone / bore faces that cross the shoulder plane)
            f_sh = (np.abs(zv - z_sh) < 0.02).all(1) & (np.abs(b.fn[:, 2]) > 0.99)
            f_th = ((np.abs(rv - (r_mi if nm == "TC-02" else r_ma)) < 0.1).all(1) & (zv > z_sh - 0.02).all(1)
                    & (zv < z_tt + 0.02).all(1) & (np.abs(b.fn[:, 2]) < 0.2))
            codes[nm][f_sh | f_th] = 0
            over["TB1"][f"{nm}_dry_shoulder_mm2"] = round(float(b.fa[f_sh].sum()), 2)
            over["TB1"][f"{nm}_dry_thread_mm2"] = round(float(b.fa[f_th].sum()), 2)
            if nm == "TC-02":
                # wetted ring r 10.0-10.1 of the pocket ceiling (pocket-wall gap, exact area pi (10.1^2 - 10.0^2) = 6.31 mm2): the
                # L1 TC-02 ceiling is faceted (11 chords on r 10.1, sagitta 0.41 mm > ring width), so the exact ring force is spread
                # uniformly over the ceiling faces that touch the pocket corner (fraction = A_ring / A_faces)
                r_po = float(rv[f_sh].max())
                f_out = np.nonzero(f_sh & (rv > r_po - 0.05).any(1))[0]
                A_ring = math.pi * (r_po ** 2 - r_fl ** 2)
                op_override[nm] = (f_out, np.full(len(f_out), A_ring / float(b.fa[f_out].sum())))
                over["TB1"]["TC-02_pocket_gap_ring_wet_mm2"] = round(A_ring, 3)
                over["TB1"]["TC-02_pocket_gap_ring_faces"] = int(len(f_out))
                over["TB1"]["r_pocket_mm"] = round(r_po, 3)
    rep = {"profile": prov, "overrides": over, "classes": {}, "nsub": NSUB * NSUB}
    applied = {}
    for nm, c in codes.items():
        b = B[nm]
        cv = cover.get(nm)
        free = np.ones(c.shape, bool) if cv is None else ~cv
        zz = Ssamp[nm][..., 2]
        v_op = ((c == 1) * 1.0 + (c == 2) * prof(zz)) * free
        v_pm = (c == 3) * 1.0 * free
        op, pm = v_op.mean(1), v_pm.mean(1)
        if nm in op_override:
            fi, val = op_override[nm]
            op[fi] = val
        cls_area = {}
        for code, lab in ((1, "PC"), (2, "GAS"), (3, "PM")):
            cls_area[lab] = round(float((((c == code) * free).mean(1) * b.fa).sum()), 2)
        cls_area["covered_by_ties_mm2"] = round(float(((~free).mean(1) * b.fa).sum()), 2)
        rep["classes"][nm] = cls_area
        i_op = np.nonzero(op > 1e-9)[0]
        i_pm = np.nonzero(pm > 1e-9)[0]
        if len(i_op):
            M.add_pressure("OP", nm, i_op, op[i_op])
            applied.setdefault("OP", []).append((nm, i_op, op[i_op]))
        if len(i_pm):
            M.add_pressure("PM", nm, i_pm, pm[i_pm])
            applied.setdefault("PM", []).append((nm, i_pm, pm[i_pm]))
    # caps (1 MPa) of closed ports and of the FD-02 filter cartridge (bounding: full filter-bore section on FD-01)
    Rp = M.Rg["engine"]
    b2, b4, bf = B["TC-02"], B["TC-04"], B["FD-01"]
    f_pc = in_capsule(S2, (-19.7, 15.39, 0.0), EZ, 4.35, 159.6, 169.52).mean(1) > 0.5
    f_pc &= np.abs(b2.fn[:, 2]) < 0.5
    f_t = in_capsule(S2, (25.0, 0.0, 0.0), EZ, 4.5, 159.6, 169.52).mean(1) > 0.5
    f_t &= np.abs(b2.fn[:, 2]) < 0.5
    f_port = (in_capsule(S4, (0.0, 0.0, 187.51), EX, 4.35, -28.02, -17.85).mean(1) > 0.5) & (np.abs(b4.fn[:, 0]) < 0.5)
    Sf = face_samples(bf)
    f_fd = (in_capsule(Sf, (0.0, 0.0, 155.51), EX, 7.0, -31.9, -30.45).mean(1) > 0.5)
    for step, faces, xr, F, lab in (
            ("OP", [("TC-02", f_pc)], np.array([-19.7, 15.39, 164.51]), EZ * math.pi * 4.35 ** 2, "Pc transducer port cap (seal at the R4.35 counterbore, bounding)"),
            ("OP", [("TC-02", f_t)], np.array([25.0, 0.0, 164.51]), EZ * math.pi * 4.5 ** 2, "torch igniter port cap (seal at the R4.5 counterbore, bounding)"),
            ("PM", [("TC-04", f_port)], np.array([-23.0, 0.0, 187.51]), -EX * math.pi * 4.35 ** 2, "E1-M cross-drill M10x1 plug cap"),
            ("PM", [("FD-01", f_fd)], np.array([-30.5, 0.0, 155.51]), -EX * math.pi * 7.0 ** 2,
             "FD-02 cartridge / face-seal cap on FD-01 (bounding: full R7 filter-bore section)")):
        nf = int(np.asarray(faces[0][1]).sum())
        if nf == 0:
            raise RuntimeError(f"cap {lab}: no faces")
        M.add_force_on_faces(step, faces, M.posed(xr[None], "engine")[0], Rp @ F)
        rep.setdefault("caps", []).append({"step": step, "label": lab, "faces": nf, "F_N_per_MPa": [float(c) for c in Rp @ F]})
    # pintle needle (not meshed): OP tip load on the seat orifice area, PM load on the area between seat and stem seal; both
    # are carried by the drive into PD-02 (rigid) -> PD-01 -> head (needle seated, drive holding)
    F_op = Rp @ (EZ * math.pi * R_SEAT ** 2)
    F_pm = Rp @ (-EZ * math.pi * (R_SEAT ** 2 - R_STEM ** 2))
    M.add_load("OP", M.needle_node, F_op)
    M.add_load("PM", M.needle_node, F_pm)
    rep["needle"] = {"R_seat_mm": R_SEAT, "R_stem_mm": R_STEM, "OP_N_per_MPa": [float(c) for c in F_op], "PM_N_per_MPa": [float(c) for c in F_pm]}
    for step in ("OP", "PM"):
        Fw = M.pressure_force(step)
        Fc = sum((v for v in M.loads.get(step, {}).values()), np.zeros(3))
        rep[f"{step}_walls_N_per_MPa"] = [float(c) for c in Fw]
        rep[f"{step}_net_before_correction_N_per_MPa"] = [float(c) for c in Fw + Fc]
        # discretisation residual of the non-matching pressure boundary (sub-face classification + tie coverage on coarse faces):
        # OP must have no lateral resultant (axisymmetric chamber + caps; the axial resultant is the pressure thrust and is kept);
        # PM is a closed cavity: walls + caps + needle = 0.  The residual is removed by a uniform traction correction over the
        # loaded faces of the step (reported; < 0.5 % of the pressure).
        R = Fw + Fc
        if step == "OP":
            R = Rp @ (np.array([1.0, 1.0, 0.0]) * (Rp.T @ R))
        nodes, w = [], []
        for nm, idx, val in applied[step]:
            b = B[nm]
            nodes.append(b.gn(b.bf_n[idx, 3:6].ravel()))
            w.append(np.repeat(b.fa[idx] * val / 3.0, 3))
        nodes, w = np.concatenate(nodes), np.concatenate(w)
        A_eff = float(w.sum())
        for n, wi in zip(nodes, w / A_eff):
            M.add_load(step, n, -R * wi)
        rep[f"{step}_residual_correction_N_per_MPa"] = [float(c) for c in -R]
        rep[f"{step}_residual_traction_MPa_per_MPa"] = float(np.linalg.norm(R) / A_eff)
        Fc2 = sum((v for v in M.loads.get(step, {}).values()), np.zeros(3))
        rep[f"{step}_net_N_per_MPa"] = [float(c) for c in Fw + Fc2]
    M.press_report = rep
    return rep


# =============================================================================================== thermal
class SaxThermal:
    def __init__(self):
        import matplotlib.tri as mtri
        m = np.load(A3.SAX_RUN / "mesh.npz", allow_pickle=True)
        self.X, self.E, self.pn = m["X"], m["E"], m["pn"]
        self.tri = {}
        for p in np.unique(self.pn):
            Ep = self.E[self.pn == p]
            used = np.unique(Ep)
            rm = -np.ones(len(self.X), np.int64)
            rm[used] = np.arange(len(used))
            sub = rm[np.vstack([Ep[:, [0, 3, 5]], Ep[:, [3, 1, 4]], Ep[:, [5, 4, 2]], Ep[:, [3, 4, 5]]])]
            Xu = self.X[used]
            self.tri[p.replace("ENG-", "")] = (used, mtri.Triangulation(Xu[:, 0], Xu[:, 1], sub), cKDTree(Xu))

    def field(self, state):
        return np.load(A3.SAX_RUN / state / "res.npz")["T"]

    def at(self, part, T, r, z):
        import matplotlib.tri as mtri
        used, tri, kd = self.tri[part]
        Tu = T[used]
        v = mtri.LinearTriInterpolator(tri, Tu)(r, z)
        v = np.asarray(v.filled(np.nan) if hasattr(v, "filled") else v, float)
        miss = ~np.isfinite(v)
        dmax = 0.0
        if miss.any():
            dd, ii = kd.query(np.column_stack([r[miss], z[miss]]))
            v[miss] = Tu[ii]
            dmax = float(dd.max())
        return v, int(miss.sum()), dmax


def thermal(M: Asm, state, ST: SaxThermal = None):
    ST = ST or SaxThermal()
    T = ST.field(state)
    out = {}
    stats = {}
    for nm, b in M.bodies.items():
        X = b.X0
        r = np.hypot(X[:, 0], X[:, 1])
        if b.trule == "SAX":
            v, nmiss, dmax = ST.at(nm, T, r, X[:, 2])
        elif b.trule == "COLLAR":
            v, nmiss, dmax = ST.at("TC-01", T, np.full(len(X), 31.7), X[:, 2])
        elif b.trule == "HEADTOP":
            v, nmiss, dmax = ST.at("TC-02", T, np.array([26.0]), np.array([169.4]))
            v = np.full(len(X), v[0])
        elif b.trule == "HEADFLAT":
            v, nmiss, dmax = ST.at("TC-02", T, np.full(len(X), 31.7), np.clip(X[:, 2], 136.6, 169.4))
        else:
            v, nmiss, dmax = np.full(len(X), T_BAY_K), 0, 0.0
        out[nm] = v
        stats[nm] = {"rule": b.trule, "T_min_C": round(float(v.min()) - 273.15, 1), "T_max_C": round(float(v.max()) - 273.15, 1),
                     "n_outside_part_domain": nmiss, "max_nearest_mm": round(dmax, 3)}
    return out, stats


# =============================================================================================== inertial unit loads
def inertial(M: Asm, step, kind):
    """kind: ('lin', unit axis 0..2): vehicle acceleration +1 g along the axis -> body force -rho a (GRAV) + item forces.
             ('ang', axis vector, group set): angular acceleration 1 rad/s2 about the pivot (origin) for the listed groups."""
    if kind[0] == "lin":
        a = np.zeros(3)
        a[kind[1]] = A3.G_MM
        M.grav = getattr(M, "grav", {})
        M.grav[step] = -a / A3.G_MM
        for it in M.items:
            F = -(it["m_kg"] * 1e-3) * a
            _apply_item(M, step, it, F)
        return
    alpha, groups = np.asarray(kind[1], float), kind[2]
    for nm, b in M.bodies.items():
        if b.grp not in groups:
            continue
        rho = engmat.MATERIALS[b.mat]["rho"]["v"] * 1e-12
        Xp = M.Xp[nm]
        acc = np.cross(alpha, Xp[b.T10[:, :4]])
        F = fe3d.consistent_linear_field(Xp, b.T10, rho, acc)
        for ln in np.nonzero(np.abs(F).sum(1) > 0)[0]:
            M.add_load(step, b.gn(ln), -F[ln])
    for it in M.items:
        g = it["group"]
        if g not in groups:
            continue
        x = M.posed(np.asarray(it["cg"], float)[None], g)[0]
        F = -(it["m_kg"] * 1e-3) * np.cross(alpha, x)
        _apply_item(M, step, it, F)


def _apply_item(M, step, it, F):
    kind = it["attach"][0]
    if kind == "member":
        M.add_load(step, it["attach"][1], F)
    else:
        g = it["group"]
        x = M.posed(np.asarray(it["cg"], float)[None], g)[0]
        M.add_force_on_faces(step, it["attach"][1], x, F)


K_MASS_LINK = 1.0e8          # N/mm, SPRING2 per direction between a point-mass node and its (dependent) carrier node


def modal_masses(M: Asm):
    """Mass items for *FREQUENCY: a point mass (tonne) at the item CG.  ccx cannot assemble a MASS element on a node that is
    dependent in an MPC (rigid-body member, RBE3 reference: 'add_sm_st: coefficient should be 0'), so each mass sits on its own
    independent node, coincident with the carrier node and linked to it by three SPRING2 (global x, y, z, K_MASS_LINK); the
    link mode (>= ~170 kHz for the heaviest item) is far above the computed band.  Member items: carrier = their rigid-body member
    node.  Face-attached items: carrier = new CG node tied to the attachment faces by a kinematic RBE3 (no added stiffness), so the
    CG offset contributes translational and rotational inertia to the mounting.  Rotary inertia of the item about its own CG is NOT
    represented (ccx MASS element is translational only): stated as a modelling limit.  Call after define() (ties already built)."""
    M.mass_el = []
    M.spring2 = []

    def put(label, carrier, m_t):
        x, g = M.extra[int(carrier)]
        mn = M.new_node(x, g)
        for d in (1, 2, 3):
            M.spring2.append((M.new_elem(), int(carrier), int(mn), d, K_MASS_LINK))
        M.mass_el.append((label, int(mn), m_t, M.new_elem()))
        return mn

    for it in M.items:
        m_t = float(it["m_kg"]) * 1e-3
        if m_t <= 0:
            continue
        if it["attach"][0] == "member":
            carrier = int(it["attach"][1])
        else:
            carrier = M.rbe3_ref(f"MASS_{it['label']}", it["attach"][1], np.asarray(it["cg"], float), it["group"])
        put(it["label"], carrier, m_t)
    # Pc transducer (line 205: miniature seat-mounted unit, body within D12 x 30 above the 1/8-27 NPT seat at r 25 / 142 deg on the head
    # top z 169.513; mass MISSING -> ASSUMED bounding 26 g = solid steel D12 x 30 envelope, CG mid-envelope z 184.51).  Modal decks only.
    m_pc = float(M.v.get("pc_mass_g", 26.0)) * 1e-6
    if m_pc > 0:
        b2 = M.bodies["TC-02"]
        S2 = face_samples(b2)
        f_pc = (in_capsule(S2, (-19.7, 15.39, 0.0), EZ, 4.35, 159.6, 169.52).mean(1) > 0.5) & (np.abs(b2.fn[:, 2]) < 0.5)
        carrier = M.rbe3_ref("MASS_PC_XDCR", [("TC-02", f_pc)], np.array([-19.7, 15.39, 184.51]), "engine")
        mn = put("PC_XDCR_ASSUMED", carrier, m_pc)
        M.pc_xdcr = {"node": int(mn), "carrier": int(carrier), "m_kg": m_pc * 1e3, "faces": int(f_pc.sum()), "cg_mm": [-19.7, 15.39, 184.51],
                     "tag": "ASSUMED (mass MISSING; bounding solid-steel envelope D12 x 30)"}
    return M.mass_el


# =============================================================================================== deck writer
def mat_block(name, mat, expansion=True):
    Mt = engmat.MATERIALS[mat]
    s = [f"*MATERIAL, NAME={name}", "*DENSITY", f"{Mt['rho']['v'] * 1e-12:.6e}", "*ELASTIC"]
    E, nu = Mt["E"], Mt["nu"]["v"]
    if "T_C" in E:
        s += [f"{v / 1e6:.6e}, {nu}, {T + 273.15:.2f}" for T, v in zip(E["T_C"], E["v"])]
    else:
        s.append(f"{E['v'] / 1e6:.6e}, {nu}")
    if expansion:
        al = Mt["alpha"]
        s.append(f"*EXPANSION, ZERO={A3.T_REF}")
        if "T_C" in al:
            s += [f"{v:.6e}, {T + 273.15:.2f}" for T, v in zip(al["T_C"], al["v"])]
        else:
            s.append(f"{al['v']:.6e}")
    return "\n".join(s) + "\n"


def write_deck(M: Asm, path, Tbody, steps, title, out_stress=True):
    """steps: ordered list of step names; 'TH' = thermal only (always first).  Loads from M.loads / M.dloads / M.grav."""
    path = Path(path)
    f = open(path, "w")
    w = f.write
    w(f"*HEADING\n{title}\n")
    w("*NODE, NSET=NALL\n")
    for nm, b in M.bodies.items():
        Xp = M.Xp[nm]
        ids = b.noff + np.arange(len(Xp))
        w("".join(f"{i}, {x:.6f}, {y:.6f}, {z:.6f}\n" for i, (x, y, z) in zip(ids, Xp)))
    if M.extra:
        w("*NODE, NSET=NEXTRA\n")
        for nid in sorted(M.extra):
            x, g = M.extra[nid]
            xp = M.posed(x[None], g)[0]
            w(f"{nid}, {xp[0]:.6f}, {xp[1]:.6f}, {xp[2]:.6f}\n")
    mats = {}
    for nm, b in M.bodies.items():
        w(f"*ELEMENT, TYPE=C3D10, ELSET=B_{nm.replace('-', '')}\n")
        ids = b.eoff + np.arange(len(b.T10))
        T = b.T10 + b.noff
        w("".join(f"{e}, " + ", ".join(str(int(n)) for n in t) + "\n" for e, t in zip(ids, T)))
        mname = b.mat.replace("-", "_") + ("" if b.trule != "BAY" else "_NX")
        mats[mname] = (b.mat, b.trule != "BAY")
    w("*ELSET, ELSET=EALL\n" + "".join(f"B_{nm.replace('-', '')}\n" for nm in M.bodies))
    for mname, (mat, ex) in mats.items():
        w(mat_block(mname, mat, ex))
    for nm, b in M.bodies.items():
        mname = b.mat.replace("-", "_") + ("" if b.trule != "BAY" else "_NX")
        w(f"*SOLID SECTION, ELSET=B_{nm.replace('-', '')}, MATERIAL={mname}\n")
    # springs (one ELSET per stiffness value)
    byk = {}
    for lab, e, n1, n2, k in M.springA:
        byk.setdefault(round(float(k), 6), []).append((e, n1, n2))
    for q, (k, L) in enumerate(sorted(byk.items())):
        w(f"*ELEMENT, TYPE=SPRINGA, ELSET=SPR{q}\n")
        w("".join(f"{e}, {n1}, {n2}\n" for e, n1, n2 in L))
        w(f"*SPRING, ELSET=SPR{q}\n\n{k:.6e}\n")
    # rigid bodies
    for lab, nodes, ref, rot in M.rigid:
        w(f"*NSET, NSET=R_{lab}\n")
        w("".join(f"{int(n)},\n" for n in nodes))
        w(f"*RIGID BODY, NSET=R_{lab}, REF NODE={ref}, ROT NODE={rot}\n")
    # point masses of the items (modal decks only), each on an independent node linked to its carrier by SPRING2 (x, y, z)
    for d in (1, 2, 3):
        L = [(e, n1, n2, k) for e, n1, n2, dd, k in getattr(M, "spring2", []) if dd == d]
        if L:
            w(f"*ELEMENT, TYPE=SPRING2, ELSET=S2D{d}\n" + "".join(f"{e}, {n1}, {n2}\n" for e, n1, n2, _ in L))
            w(f"*SPRING, ELSET=S2D{d}\n{d}, {d}\n{L[0][3]:.6e}\n")
    for q, (lab, node, m_t, e) in enumerate(getattr(M, "mass_el", [])):
        w(f"*ELEMENT, TYPE=MASS, ELSET=PM{q}\n{e}, {node}\n*MASS, ELSET=PM{q}\n{m_t:.9e}\n")
    M.C.write(f)
    # boundary
    if M.gnd:
        w("*NSET, NSET=NGND\n" + "".join(f"{n},\n" for n in sorted(M.gnd)))
        w("*BOUNDARY\nNGND, 1, 3\n")
    for lab, nodes in M.af_sets.items():
        w(f"*NSET, NSET={lab}\n" + "".join(f"{n},\n" for n in nodes))
    w(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {A3.T_REF}\n" + (f"NEXTRA, {A3.T_REF}\n" if M.extra else ""))
    out = "*NODE FILE\nU\n" + ("*EL FILE\nS\n" if out_stress else "") + "".join(f"*NODE PRINT, NSET={lab}, TOTALS=ONLY\nRF\n" for lab in M.af_sets)
    t_ref_line = f"*TEMPERATURE\nNALL, {A3.T_REF}\n" + (f"NEXTRA, {A3.T_REF}\n" if M.extra else "")
    t_set = False                          # ccx needs a final temperature in the first step (checktemp); decks without TH run at T_REF
    for st in steps:
        if st.startswith("FREQ"):          # FREQ or FREQ<n>: n eigenmodes (default 30), unstressed state at T_REF
            nmode = int(st[4:] or 30)
            w(f"** step {st}\n*STEP\n*FREQUENCY, SOLVER=SPOOLES\n{nmode}\n" + ("" if t_set else t_ref_line) + "*NODE FILE\nU\n*END STEP\n")
            t_set = True
            continue
        w(f"** step {st}\n*STEP\n*STATIC\n")
        if st == "TH":
            w("*TEMPERATURE\n")
            for nm, b in M.bodies.items():
                ids = b.noff + np.arange(len(b.X0))
                w("".join(f"{i}, {t:.3f}\n" for i, t in zip(ids, Tbody[nm])))
            if M.extra:
                w(f"NEXTRA, {A3.T_REF}\n")
            t_set = True
        elif not t_set:
            w(t_ref_line)
            t_set = True
        w("*DLOAD, OP=NEW\n")
        if st in getattr(M, "grav", {}):
            gdir = M.grav[st]
            w(f"EALL, GRAV, {A3.G_MM:.1f}, {gdir[0]:.9f}, {gdir[1]:.9f}, {gdir[2]:.9f}\n")
        for e, fc, v in M.dloads.get(st, []):
            w(f"{e}, P{fc}, {v:.6e}\n")
        w("*CLOAD, OP=NEW\n")
        for n, vec in sorted(M.loads.get(st, {}).items()):
            for d in range(3):
                if abs(vec[d]) > 1e-12:
                    w(f"{n}, {d + 1}, {vec[d]:.9e}\n")
        w(out + "*END STEP\n")
    f.close()
    return path


# =============================================================================================== gimbal unit loads (F1 LC3 / F2 poses)
def cone_to_ab(amp_deg, dir_deg):
    """(alpha, beta) of R = Rx(alpha) Ry(beta) whose engine axis makes amp with +Z, tilted toward azimuth dir (the nozzle swings the
    opposite way).  Same convention and formula as Mechanical tvc_kinematics.cone_to_ab (re-implemented, not imported)."""
    th, d = math.radians(amp_deg), math.radians(dir_deg)
    v = np.array([math.sin(th) * math.cos(d), math.sin(th) * math.sin(d), math.cos(th)])
    b = math.asin(max(-1.0, min(1.0, v[0])))
    a = math.atan2(-v[1], v[2])
    return math.degrees(a), math.degrees(b)


def pose_list(rng=7.0, stop=8.0):
    """Mechanical pose_list (build.py): neutral, +/- range per axis, 4 combined corners on the range cone, conical stop in 8
    directions.  (name, alpha, beta, stop azimuth or None)."""
    P = [("neutral", 0.0, 0.0, None)]
    for nm, a, b in (("alpha+", rng, 0.0), ("alpha-", -rng, 0.0), ("beta+", 0.0, rng), ("beta-", 0.0, -rng)):
        P.append((nm, a, b, None))
    for d in (45, 135, 225, 315):
        a, b = cone_to_ab(rng, d)
        P.append((f"combined{d:03d}", a, b, None))
    for d in range(0, 360, 45):
        a, b = cone_to_ab(stop, d)
        P.append((f"stop{d:03d}", a, b, float(d)))
    return P


def rod_pair(M: Asm, step, i):
    """Unit actuator force pair on chain i: +1 N on the lever eye (engine) along (lever - horn), -1 N on the horn eye = rod
    compression (actuator pushing).  The rod spring stays in the model; the post-processing imposes the actuator model (force source
    or position-holding spring) by superposition."""
    bu = next(b for b in M.bush if b["label"] == f"ROD_{i}")
    H, L = int(bu["A"]), int(bu["B"])
    xH, xL = M.xyzp([H])[0], M.xyzp([L])[0]
    e = unit(xL - xH)
    M.add_load(step, L, e)
    M.add_load(step, H, -e)
    M.rod_geom = getattr(M, "rod_geom", {})
    M.rod_geom[i] = {"horn_eye": xH.tolist(), "lever_eye": xL.tolist(), "e_push_on_engine": e.tolist(), "H": H, "L": L}


BUMPER = {"r_case": 31.75, "z_e": (-105.24, -95.14), "r_seat": 48.0, "z_seat": (-99.8, -89.8),
          "half_arc_case_deg": 15.0, "half_arc_seat_deg": 25.0}


def bumper_pair(M: Asm, step, phi_deg):
    """Unit stop force pair at the 8 deg conical stop toward azimuth phi (engine axis tilted toward phi; the aft case swings to phi+180
    and touches the GM-11 PU cone, line contact along the case OD generator z_e -105.2..-95.1 (CAD v3.5.1 GM-11 cone r 46.09 at z
    -99.8 to 44.68 at z -89.8 = 8 deg)).  Engine patch: TC-01 OD faces within +/-15 deg of the contact generator (ASSUMED spread);
    seat patch: GM-10 bore r 48 faces within +/-25 deg (ASSUMED spread through the 2.6 mm PU ring, GM-11 not meshed).  +1 N on GM-10
    along the contact normal (outward), -1 N on the case (frictionless: normal = engine-frame radial at the contact generator)."""
    Re = M.Rg["engine"]
    u = np.array([math.cos(math.radians(phi_deg) + math.pi), math.sin(math.radians(phi_deg) + math.pi), 0.0])
    zc = 0.5 * sum(BUMPER["z_e"])
    psis = np.radians(np.arange(0.0, 360.0, 0.05))
    P = np.stack([BUMPER["r_case"] * np.cos(psis), BUMPER["r_case"] * np.sin(psis), np.full(len(psis), zc)], 1) @ Re.T
    k = int(np.argmax(P @ u))
    psi_e = float(psis[k])
    er_e = np.array([math.cos(psi_e), math.sin(psi_e), 0.0])
    n_out = Re @ er_e                                    # contact normal (fixed frame), pointing from the case into the bumper
    xc = Re @ (BUMPER["r_case"] * er_e + np.array([0, 0, zc]))
    b1 = M.bodies["TC-01"]
    rr = np.hypot(b1.fc[:, 0], b1.fc[:, 1])
    az = np.arctan2(b1.fc[:, 1], b1.fc[:, 0])
    dpsi = np.abs((az - psi_e + math.pi) % (2 * math.pi) - math.pi)
    m1 = ((np.abs(rr - BUMPER["r_case"]) < 0.3) & (b1.fc[:, 2] >= BUMPER["z_e"][0] - 0.05) & (b1.fc[:, 2] <= BUMPER["z_e"][1] + 0.05)
          & (dpsi <= math.radians(BUMPER["half_arc_case_deg"])) & (np.einsum("ij,ij->i", b1.fn, np.stack([np.cos(az), np.sin(az), 0 * az], 1)) > 0.7))
    phi_c = math.atan2(xc[1], xc[0])
    b10 = M.bodies["GM-10"]
    r10 = np.hypot(b10.fc[:, 0], b10.fc[:, 1])
    a10 = np.arctan2(b10.fc[:, 1], b10.fc[:, 0])
    d10 = np.abs((a10 - phi_c + math.pi) % (2 * math.pi) - math.pi)
    m10 = ((np.abs(r10 - BUMPER["r_seat"]) < 0.3) & (b10.fc[:, 2] >= BUMPER["z_seat"][0] - 0.05) & (b10.fc[:, 2] <= BUMPER["z_seat"][1] + 0.05)
           & (d10 <= math.radians(BUMPER["half_arc_seat_deg"])))
    if m1.sum() < 3 or m10.sum() < 3:
        raise RuntimeError(f"bumper patch faces: case {int(m1.sum())}, seat {int(m10.sum())}")
    M.add_force_on_faces(step, [("TC-01", m1)], xc, -n_out)
    M.add_force_on_faces(step, [("GM-10", m10)], xc, n_out)
    M.bumper = {"phi_deg": phi_deg, "psi_e_deg": math.degrees(psi_e), "contact_point_mm": xc.tolist(), "n_out": n_out.tolist(),
                "faces_case": int(m1.sum()), "faces_seat": int(m10.sum()),
                "area_case_mm2": float(b1.fa[m1].sum()), "area_seat_mm2": float(b10.fa[m10].sum()),
                "moment_arm_about_pivot_mm": float(np.linalg.norm(np.cross(xc, n_out)))}
    return M.bumper
