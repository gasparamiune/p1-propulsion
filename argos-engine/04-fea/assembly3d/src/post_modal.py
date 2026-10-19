"""FEA3D modal post-processing (lead 188 (14), 194: governing natural periods of the pressure-loaded load paths).

usage: post_modal.py RUN STATE [govjson=results/f1_post_X.json,...]
  RUN solved with steps OP,PM,FREQn (static OP / PM at T_REF + n eigenmodes, unstressed, T_REF).

What it does (all SIM / DERIVED on the 3-D assembly FE, rigid airframe holes, design ties, actuator chain springs in place):
  * frequencies, periods, ccx participation factors / effective masses; lumped-mass check of the ccx mass normalisation;
  * kinetic-energy fraction per load-path group (bodies + item point masses) and the rigid-body share of the engine (gimbal modes);
  * modal decomposition of the STATIC chamber-pressure response (unit OP, same model, T_REF):
        u_OP = sum_i phi_i (phi_i . F_OP) / omega_i^2  (+ residual of the modes above the highest computed one)
    for path functionals (pintle vs seat, head centre vs rim, nozzle vs J1 lip, engine axial / rocking, rod elongation, item
    CG relative to the head, Pc transducer) and for the dominant principal stress at the governing nodes of the margin tables.
    The share of each functional carried by modes with T > 20 ms, 1-20 ms, 0.1-1 ms (computed) and the residual (T < 1/f_max)
    classifies the path in the lead 194 period domain; the governing period is that of the mode with the largest share.
Units: mm, N, tonne, s, MPa (ccx consistent set); f in Hz, T in ms.  fea3d 2026-10-13.
"""
from __future__ import annotations
import sys, json, math, csv
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF        # noqa: E402
import asm_build as AB      # noqa: E402
import asm3d as A3          # noqa: E402
import fe3d                 # noqa: E402

RUNS, RES = PF.RUNS, PF.RES
EZ = np.array([0.0, 0.0, 1.0])

PATH_OF_BODY = {"PD-01R": "pintle_linkage", "PD-01S": "pintle_linkage", "TC-04": "fwd_equipment", "FD-01": "fwd_equipment",
                "TC-02": "head", "TC-03": "head", "NZ-01": "nozzle_J1", "NZ-02": "nozzle_J1", "NZ-03": "nozzle_J1", "NZ-04": "nozzle_J1",
                "TC-09": "aft_TC09", "TC-01": "case", "GM-01": "collar", "GM-02": "collar", "GM-03": "ring",
                "GM-08a": "posts_rings", "GM-08b": "posts_rings", "GM-09": "posts_rings", "GM-10": "posts_rings",
                "GM-13": "servo_brackets", "GM-14": "servo_brackets", "GM-16a": "horns", "GM-16b": "horns"}
ITEM_PATH = {"PD02_DRIVE": "pintle_linkage", "RAIL": "pintle_linkage", "SERVO_PLATE": "pintle_linkage",
             "TORCH": "fwd_equipment", "BLEED": "fwd_equipment", "RISER": "fwd_equipment", "FD02": "fwd_equipment",
             "FD04": "fwd_equipment", "TC10": "head", "PD11_WASHERS": "head", "TC06": "case", "TC08": "aft_TC09",
             "PC_XDCR_ASSUMED": "pc_port", "SERVO_1": "servos", "SERVO_2": "servos", "GM11": "posts_rings", "FD09_BRACKET": "posts_rings",
             "EL03": "ring", "EL04": "posts_rings"}
PREFIX_PATH = [("GRAIN_", "case"), ("PIN_IN_", "collar"), ("LEYE_", "collar"), ("SEAT_IN_", "ring"), ("PIN_OUT_", "ring"),
               ("SEAT_OUT_", "posts_rings"), ("HEYE_", "horns")]
ITEM_FUNCTIONALS = ["TORCH", "RISER", "BLEED", "FD02", "FD04", "PD02_DRIVE", "RAIL", "SERVO_PLATE", "PC_XDCR_ASSUMED", "SERVO_1", "SERVO_2"]
BINS = [("T>20ms", 0.0, 50.0), ("1<T<=20ms", 50.0, 1000.0), ("0.1<T<=1ms", 1000.0, 10000.0), ("T<=0.1ms", 10000.0, 1e12)]


def item_path(label, attach_bodies):
    if label in ITEM_PATH:
        return ITEM_PATH[label]
    for pre, g in PREFIX_PATH:
        if label.startswith(pre):
            return g
    if attach_bodies:
        b0 = attach_bodies[0]
        return PATH_OF_BODY.get(b0, "other")
    return "other"


def lumped_masses(M):
    """HRZ diagonal lumping of the straight-sided tet10 (corner m/36, mid-side 4m/27) + item point masses (tonne)."""
    n = M.next_n + 1
    m = np.zeros(n)
    grp = np.full(n, "", dtype=object)
    for nm, b in M.bodies.items():
        rho = A3.engmat.MATERIALS[b.mat]["rho"]["v"] * 1e-12
        me = rho * np.abs(fe3d.tet_vol(M.Xp[nm], b.T10))
        np.add.at(m, b.noff + b.T10[:, :4], np.repeat((me / 36.0)[:, None], 4, 1))
        np.add.at(m, b.noff + b.T10[:, 4:], np.repeat((me * 4.0 / 27.0)[:, None], 6, 1))
        grp[b.noff:b.noff + len(b.X0)] = PATH_OF_BODY.get(nm, "other")
    item_nodes = {}
    lab2bodies = {}
    for it in M.items:
        a = it["attach"]
        lab2bodies.setdefault(it["label"], [bb for bb, _ in a[1]] if a[0] != "member" else [])
    for lab, node, m_t, e in M.mass_el:
        m[node] += m_t
        grp[node] = item_path(lab, lab2bodies.get(lab, []))
        item_nodes.setdefault(lab, []).append((int(node), float(m_t)))
    return m, grp, item_nodes


def nodal_force(M, step):
    """Consistent nodal forces of the pressure list (tri6 straight faces: corners 0, mid-sides p A / 3 along -n_out) + nodal loads."""
    F = np.zeros((M.next_n + 1, 3))
    L = M.dloads.get(step, [])
    if L:
        E = np.array([l[0] for l in L])
        Fc = np.array([l[1] for l in L])
        V = np.array([l[2] for l in L])
        for nm, b in M.bodies.items():
            msk = (E >= b.eoff) & (E < b.eoff + len(b.T10))
            if not msk.any():
                continue
            key = {(int(e), int(f)): i for i, (e, f) in enumerate(zip(b.bf_e, b.bf_f))}
            ii = np.array([key[(int(e) - b.eoff, int(f))] for e, f in zip(E[msk], Fc[msk])])
            Rg = M.Rg[b.grp]
            nout = b.fn[ii] @ Rg.T
            f = -(V[msk] * b.fa[ii] / 3.0)[:, None] * nout
            for k in range(3):
                np.add.at(F, b.gn(b.bf_n[ii, 3 + k]), f)
    for n, vec in M.loads.get(step, {}).items():
        F[int(n)] += vec
    return F


# ----------------------------------------------------------------------------------------------- tet10 nodal stress recovery
NAT = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1],
                [.5, .5, 0, 0], [0, .5, .5, 0], [.5, 0, .5, 0], [.5, 0, 0, .5], [0, .5, 0, .5], [0, 0, .5, .5]], float)


def dN_dL(Lc):
    """d N_a / d L_j (10 x 4) of the quadratic tet at volume coordinates Lc (4,)."""
    D = np.zeros((10, 4))
    for a in range(4):
        D[a, a] = 4.0 * Lc[a] - 1.0
    for m, (k, l) in enumerate(fe3d.EDGES):
        D[4 + m, k] = 4.0 * Lc[l]
        D[4 + m, l] = 4.0 * Lc[k]
    return D


def grad_ops(Xe, local):
    """Shape-function gradients (10 x 3) at the element's local node 'local' (isoparametric, curved sides allowed)."""
    D = dN_dL(NAT[local])
    Dxi = D[:, :3] - D[:, 3:4]                      # L4 = 1 - xi1 - xi2 - xi3
    J = Xe.T @ Dxi                                  # dx/dxi (3 x 3)
    return Dxi @ np.linalg.inv(J)                   # dN/dx


class StressProbe:
    """Linear map u -> nodal stress tensor (6, Voigt xx yy zz xy yz zx, engineering shear) at one mesh node, averaged over the
    elements that share the node (T_REF isotropic elasticity)."""

    def __init__(self, M, node):
        self.node = int(node)
        nm = next(n for n, b in M.bodies.items() if b.noff <= node < b.noff + len(b.X0))
        b = M.bodies[nm]
        self.body = nm
        loc = node - b.noff
        els, pos = np.nonzero(b.T10 == loc)
        mat = A3.engmat.MATERIALS[b.mat]
        Ev = mat["E"]
        E = float(np.interp(A3.T_REF - 273.15, Ev["T_C"], Ev["v"])) / 1e6 if "T_C" in Ev else float(Ev["v"]) / 1e6
        nu = float(mat["nu"]["v"])
        lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
        self.terms = []
        for e, p in zip(els, pos):
            conn = b.T10[e]
            G = grad_ops(M.Xp[nm][conn], int(p))
            self.terms.append((b.noff + conn, G))
        self.lam, self.mu, self.n_el = lam, mu, len(self.terms)

    def stress(self, U):
        """U: (N+1, 3) or (k, N+1, 3) -> (6,) or (k, 6)."""
        U = np.asarray(U)
        single = U.ndim == 2
        if single:
            U = U[None]
        acc = np.zeros((U.shape[0], 3, 3))
        for ids, G in self.terms:
            acc += np.einsum("kai,aj->kij", U[:, ids, :], G)       # du_i/dx_j
        H = acc / len(self.terms)
        eps = 0.5 * (H + np.transpose(H, (0, 2, 1)))
        tr = np.trace(eps, axis1=1, axis2=2)
        S = 2 * self.mu * eps + self.lam * tr[:, None, None] * np.eye(3)[None]
        out = np.stack([S[:, 0, 0], S[:, 1, 1], S[:, 2, 2], S[:, 0, 1], S[:, 1, 2], S[:, 2, 0]], 1)
        return out[0] if single else out


def tens(v):
    return np.array([[v[0], v[3], v[5]], [v[3], v[1], v[4]], [v[5], v[4], v[2]]])


# ----------------------------------------------------------------------------------------------- rigid fits
def rigid_fit_op(X, w):
    """Weighted least-squares rigid motion of a node set: returns A (6 x 3n) with [t; theta] = A @ u.ravel() (about the origin)."""
    n = len(X)
    G = np.zeros((3 * n, 6))
    for k in range(n):
        x, y, z = X[k]
        G[3 * k:3 * k + 3, :3] = np.eye(3)
        G[3 * k:3 * k + 3, 3:] = np.array([[0, z, -y], [-z, 0, x], [y, -x, 0]])
    W = np.repeat(w, 3)
    Nm = G.T @ (W[:, None] * G)
    return np.linalg.solve(Nm, (G * W[:, None]).T)


def main(argv):
    name, state = argv[0], argv[1]
    opts = dict(a.split("=", 1) for a in argv[2:])
    M, meta = PF.load_model(name)
    AB.pressure_sets(M)
    sd = RUNS / name / state
    Z = np.load(sd / "fields.npz")
    Uf = Z["U_FREQ"].astype(np.float64)
    U_op = Z["U_OP"].astype(np.float64)
    md = json.loads((sd / "modal.json").read_text())
    nmode = Uf.shape[0]
    f = np.array([r["f_Hz"] for r in md["modes"]][:nmode])
    om = 2 * math.pi * f
    m, grp, item_nodes = lumped_masses(M)
    N1 = M.next_n + 1
    Uf = Uf[:, :N1]
    U_op = U_op[:N1]
    X = np.zeros((N1, 3))
    for nm, b in M.bodies.items():
        X[b.noff:b.noff + len(b.X0)] = M.Xp[nm]
    for nid, (x, g) in M.extra.items():
        if nid < N1:
            X[nid] = M.posed(np.asarray(x)[None], g)[0]
    F_op = nodal_force(M, "OP")
    out = {"run": name, "state": state, "version": A3.VERSION, "date": "2026-10-13", "n_modes": int(nmode),
           "f_max_Hz": float(f.max()), "T_min_ms": float(1e3 / f.max()),
           "model": {"level": meta["level"], "cad": meta["cad"], "n_nodes": int(M.n_mesh), "n_eq": meta["n_eq"],
                     "boundary": "16 airframe M5 hole bores fixed (rigid airframe)", "temperature": f"T_REF {A3.T_REF} K (unstressed)",
                     "pc_transducer": getattr(M, "pc_xdcr", None)},
           "checks": {}, "modes": [], "functionals": {}, "stress_functionals": [], "notes": []}
    tot_m = float(m.sum())
    out["checks"]["lumped_total_mass_kg"] = tot_m * 1e3
    out["checks"]["F_OP_resultant_N_per_MPa"] = F_op.sum(0).tolist()
    comp = float(np.einsum("ij,ij->", F_op, U_op))
    out["checks"]["OP_compliance_F_dot_u_static"] = comp
    # modal participation of the OP load and mass-normalisation check
    p = np.einsum("kij,ij->k", Uf, F_op)
    gm = np.einsum("kij,i->k", Uf ** 2, m)
    capt = float(np.sum(p ** 2 / om ** 2))
    out["checks"]["OP_compliance_captured_by_modes"] = capt / comp
    out["checks"]["generalised_mass_lumped_min_max"] = [float(gm.min()), float(gm.max())]
    # engine rigid-body fit (gimbal modes)
    eng_nodes = np.concatenate([b.noff + np.arange(len(b.X0)) for nm, b in M.bodies.items() if b.grp == "engine"])
    lab_grp = {it["label"]: it["group"] for it in M.items}
    lab_grp["PC_XDCR_ASSUMED"] = "engine"
    eng_items = [n for lab, L in item_nodes.items() for n, _ in L if n >= M.n_mesh + 1 and lab_grp.get(lab, "") == "engine"]
    en = np.unique(np.concatenate([eng_nodes, np.asarray(eng_items, np.int64)]))
    sub = en[:: max(1, len(en) // 6000)]                       # rigid fit on a representative subset (mass-weighted)
    Aop = rigid_fit_op(X[sub], m[sub] / m[sub].sum())
    # groups
    groups = sorted(set(grp[m > 0]))
    gidx = {g: np.nonzero((grp == g) & (m > 0))[0] for g in groups}
    # ---------------------------------------------------------------- functionals (linear in u)
    b3, b2, b9 = M.bodies["TC-03"], M.bodies["TC-02"], M.bodies["TC-09"]
    r3 = np.hypot(M.Xp["TC-03"][:, 0], M.Xp["TC-03"][:, 1])
    seat = b3.noff + np.nonzero(r3 <= 3.6)[0]
    r2 = np.hypot(M.Xp["TC-02"][:, 0], M.Xp["TC-02"][:, 1])
    rim = b2.noff + np.nonzero(r2 >= r2.max() - 0.6)[0]
    t3 = b3.noff + np.arange(len(b3.X0))
    nz1 = M.bodies["NZ-01"].noff + np.arange(len(M.bodies["NZ-01"].X0))
    tree4 = cKDTree(M.Xp["NZ-04"])
    d9, _ = tree4.query(M.Xp["TC-09"], k=1)
    lip = b9.noff + np.nonzero(d9 <= 0.3)[0]
    rods = {b_["label"]: b_ for b_ in M.bush if b_["label"].startswith("ROD_")}
    # head rigid motion (TC-02) for item relative displacements
    h_nodes = b2.noff + np.arange(len(b2.X0))
    hsub = h_nodes[:: max(1, len(h_nodes) // 3000)]
    Ah = rigid_fit_op(X[hsub], m[hsub] / m[hsub].sum())

    def eval_fun(U):
        """U (k, N1, 3) -> dict of functional values (k,)."""
        res = {}
        res["pintle_needle_vs_seat_z"] = U[:, M.needle_node, 2] - (U[:, seat, 2] * m[seat]).sum(1) / m[seat].sum()
        res["head_seat_vs_rim_z"] = (U[:, t3, 2] * m[t3]).sum(1) / m[t3].sum() - U[:, rim, 2].mean(1)
        res["nozzle_NZ01_vs_J1_lip_z"] = (U[:, nz1, 2] * m[nz1]).sum(1) / m[nz1].sum() - U[:, lip, 2].mean(1)
        rb = np.einsum("aj,kj->ka", Aop, U[:, sub, :].reshape(U.shape[0], -1))
        res["engine_axial_tz"] = rb[:, 2]
        res["engine_lateral_tx"] = rb[:, 0]
        res["engine_lateral_ty"] = rb[:, 1]
        res["engine_rot_x"] = rb[:, 3]
        res["engine_rot_y"] = rb[:, 4]
        res["engine_rot_z"] = rb[:, 5]
        for lab, bu in rods.items():
            H, L = int(bu["A"]), int(bu["B"])
            e = AB.unit(X[L] - X[H])
            # asm v1.2 (REPORT 7.1): REF nodes in no element are not in the .frd -> use the rod spring's aux node (as post_k.py)
            Lu = int(bu["springs"][0][0]) if bu.get("springs") and bu["springs"][0][0] is not None else L
            res[f"{lab}_elongation"] = (U[:, Lu, :] - U[:, H, :]) @ e
        hb = np.einsum("aj,kj->ka", Ah, U[:, hsub, :].reshape(U.shape[0], -1))
        for lab in ITEM_FUNCTIONALS:
            if lab not in item_nodes:
                continue
            nd = max(item_nodes[lab], key=lambda t: t[1])[0]
            x = X[nd]
            rig = hb[:, :3] + np.cross(hb[:, 3:], x[None])
            res[f"item_{lab}_rel_head"] = U[:, nd, :] - rig          # vector (k, 3): projected later
        return res

    Fs = eval_fun(U_op[None])
    Fm = eval_fun(Uf)
    fun_tab = {}
    for k, vs in Fs.items():
        vm_ = Fm[k]
        if vs.ndim == 2:                                            # vector functional: project on the static direction
            v0 = vs[0]
            nrm = np.linalg.norm(v0)
            d = v0 / nrm if nrm > 1e-15 else EZ
            vs_s = float(v0 @ d)
            vm_s = vm_ @ d
            mag = np.linalg.norm(vm_, axis=1)
            extra = {"direction": d.tolist(), "per_mode_abs_max_mode": int(np.argmax(mag * np.abs(p) / om ** 2)) + 1}
        else:
            vs_s = float(vs[0])
            vm_s = vm_
            extra = {}
        contrib = vm_s * p / om ** 2
        fun_tab[k] = summarize(vs_s, contrib, f, extra)
    out["functionals"] = fun_tab
    # ---------------------------------------------------------------- per-mode table
    for i in range(nmode):
        e_i = (np.einsum("ij,i->i", Uf[i] ** 2, m))
        tot = float(e_i.sum())
        fr = {g: float(e_i[ix].sum() / tot) for g, ix in gidx.items()}
        top = sorted(fr.items(), key=lambda t: -t[1])[:4]
        rb = Aop @ Uf[i, sub, :].ravel()
        urb = rb[:3][None] + np.cross(rb[3:][None], X[en])
        e_eng = float((np.einsum("ij,i->", Uf[i, en] ** 2, m[en])))
        e_rb = float(np.einsum("ij,i->", urb ** 2, m[en]))
        row = {"mode": i + 1, "f_Hz": float(f[i]), "T_ms": float(1e3 / f[i]), "gm_lumped": float(gm[i]),
               "p_OP": float(p[i]), "OP_compliance_share": float(p[i] ** 2 / om[i] ** 2 / comp),
               "ke_fraction": fr, "top_groups": top, "engine_ke_share": e_eng / tot,
               "engine_rigid_share_of_engine_ke": min(1.0, e_rb / max(e_eng, 1e-30)),
               "engine_rigid_t_mm": rb[:3].tolist(), "engine_rigid_theta_rad": rb[3:].tolist()}
        if i < len(md.get("effective_mass", [])):
            row["eff_mass_ccx_t"] = md["effective_mass"][i][1:]
        out["modes"].append(row)
    # ---------------------------------------------------------------- governing-node stress functionals
    gfiles = [Path(x) for x in opts.get("govjson", "").split(",") if x]
    nodes = {}
    for gf in gfiles:
        d = json.loads(gf.read_text())
        for stn, st in d["states"].items():
            for cid, c in st["cases"].items():
                for r in c["margins"]:
                    if r["set"] != "regular":
                        continue
                    nodes.setdefault((r["part"], int(r["node"])), []).append(f"{cid}@{stn} MS {r['MS']:.3f}")
    S_ccx = Z["S_OP"].astype(np.float64) if "S_OP" in Z.files else None
    for (part, nd), tags in sorted(nodes.items()):
        try:
            pr = StressProbe(M, nd)
        except Exception as ex:                                   # noqa: BLE001
            out["notes"].append(f"stress probe {part} node {nd}: {ex}")
            continue
        s0 = pr.stress(U_op)
        w, V = np.linalg.eigh(tens(s0))
        kk = int(np.argmax(np.abs(w)))
        nvec = V[:, kk]
        sm = pr.stress(Uf)
        vals = np.einsum("i,kij,j->k", nvec, np.stack([tens(v) for v in sm]), nvec)
        contrib = vals * p / om ** 2
        row = summarize(float(w[kk]), contrib, f, {"part": part, "node": nd, "xyz": X[nd].tolist(), "tags": tags,
                                                    "principal_dir": nvec.tolist(), "n_elements": pr.n_el,
                                                    "sigma_OP_static_MPa_per_MPa_probe": s0.tolist(),
                                                    "sigma_OP_static_ccx": (S_ccx[nd].tolist() if S_ccx is not None else None)})
        out["stress_functionals"].append(row)
    out["notes"] += [
        "Mode shapes from ccx *FREQUENCY are normalised to unit generalised (consistent) mass; gm_lumped is the HRZ-lumped check.",
        "Item point masses are translational (ccx MASS); their own rotary inertia is not represented; face-attached items hang on RBE3 "
        "CG nodes (no added stiffness).  The pintle needle, PD-02 crank housing and servo drive are rigid: the pintle/linkage period "
        "excludes the servo gear-train / link / needle-stem compliance (MISSING) and is therefore a LOWER bound on the true period.",
        "Pc transducer: line 205 miniature seat-mounted unit, mass MISSING -> ASSUMED 26 g (solid-steel D12 x 30 envelope, bounding), "
        "RBE3 to the 1/8-27 NPT seat bore (thread / body compliance not modelled -> period LOWER bound).",
        "Rigid airframe; the airframe's own modes are outside this model (ICD).  T_REF stiffness: the hot B1/A1 states lower E of "
        "6061 by up to ~5-10 % at 120-150 C (f by ~2.5-5 %).",
        "Residual = static response not represented by the computed modes = modes above f_max (T < T_min).",
    ]
    RES.mkdir(exist_ok=True)
    (RES / f"modal_{name}.json").write_text(json.dumps(out, indent=1, default=float))
    with open(RES / f"modal_{name}_modes.csv", "w", newline="") as fh:
        wcsv = csv.writer(fh)
        wcsv.writerow(["mode", "f_Hz", "T_ms", "OP_compliance_share", "engine_ke_share", "engine_rigid_share", "top1", "frac1", "top2",
                       "frac2", "top3", "frac3", "t_x", "t_y", "t_z", "th_x", "th_y", "th_z"])
        for r in out["modes"]:
            tg = r["top_groups"] + [("", 0.0)] * 3
            wcsv.writerow([r["mode"], f"{r['f_Hz']:.2f}", f"{r['T_ms']:.4f}", f"{r['OP_compliance_share']:.4g}", f"{r['engine_ke_share']:.3f}",
                           f"{r['engine_rigid_share_of_engine_ke']:.3f}", tg[0][0], f"{tg[0][1]:.3f}", tg[1][0], f"{tg[1][1]:.3f}",
                           tg[2][0], f"{tg[2][1]:.3f}"] + [f"{v:.4g}" for v in r["engine_rigid_t_mm"] + r["engine_rigid_theta_rad"]])
    print(json.dumps({k: out["checks"][k] for k in out["checks"]}, indent=1, default=float))
    return out


def summarize(r_static, contrib, f, extra):
    contrib = np.asarray(contrib, float)
    tot = float(contrib.sum())
    res = r_static - tot
    row = dict(extra)
    row["static"] = r_static
    row["sum_modes"] = tot
    row["residual_share"] = res / r_static if r_static else None
    bins = {}
    for lab, lo, hi in BINS:
        msk = (f >= lo) & (f < hi)
        bins[lab] = {"share": float(contrib[msk].sum() / r_static) if r_static else None,
                     "abs_share": float(np.abs(contrib[msk]).sum() / abs(r_static)) if r_static else None}
    row["bins"] = bins
    k = int(np.argmax(np.abs(contrib)))
    row["largest_mode"] = {"mode": k + 1, "f_Hz": float(f[k]), "T_ms": float(1e3 / f[k]),
                           "share": float(contrib[k] / r_static) if r_static else None}
    order = np.argsort(-np.abs(contrib))[:5]
    row["top_modes"] = [[int(i + 1), float(f[i]), float(contrib[i] / r_static) if r_static else None] for i in order]
    slow = float(np.abs(contrib[f < 1000.0]).sum() / abs(r_static)) if r_static else None
    row["share_T_gt_1ms_abs"] = slow
    resid = abs(res / r_static) if r_static else None
    # governing period: largest single contributor unless the residual (modes above f_max) carries more
    if r_static and resid is not None and resid > abs(contrib[k] / r_static):
        row["governing"] = {"T_ms": f"< {1e3 / f.max():.3f}", "basis": "residual of the modes above f_max carries the largest share"}
    else:
        row["governing"] = {"T_ms": float(1e3 / f[k]), "basis": f"mode {k + 1}"}
    return row


if __name__ == "__main__":
    main(sys.argv[1:])
