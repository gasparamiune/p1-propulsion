"""J-FWD seat contact under the screw (TC-02 plug OD on the TC-01 bore = the FIT pair), screw tension and shell pull, per step
(fea3d 2026-10-20 ~11:00Z; lead 10:47Z: '(a), (b2) and (b1) each report the integrated seat contact normal force under the screw at every
step: PRELOAD, SOAK70, SOAK52 and FA1S ... next to the screw tension and the shell pull, and give the contact footprint (its centroid and
its extent along z and around the circumference).  Do the same from the existing js5 results ... js5 at SOAK70 has 5695 N head force
against 4294 N shell pull, which leaves roughly 1.4 kN on the seat.  Confirm or correct that.').

All forces EXACT from the solved displacements (DERIVED from the SIM .frd): nodal internal forces f = sum_e int B^T sigma dV per body
(jfwd_cforce.body_forces, the deck's E(T), alpha(T), the step's nodal temperatures) minus the applied nodal loads (consistent pressure
loads on the wetted straight T6 faces: midside nodes p A n / 3, corners 0; the cap and M14 z-tractions of the global deck) = the external
(contact / tie / boundary) force at each node; every node of a body is put in exactly one class, so the class sums close exactly.
  seat     TC-02 FIT slave nodes (plug OD r 28.6): the contact force from TC-01.  At the 1:1 thread-tie nodes on the FIT surface (tap
           mouth) the tie force is removed (F_c[b] = g[b] + f_screw[a], a the tied screw node); at symmetry-plane nodes the plane-normal
           component (the symmetry reaction) is removed (frictionless contact is in-plane there).  Normal force F_n = -F_c . e_r (+ =
           compressive).  Totals: scalar radial sum, and along the screw axis n.  Footprint: the CPRESS > 0 nodes (contact zone) and the
           force-carrying nodes (|F_n| > 1 % of the largest nodal F_n): force-weighted centroid (az from the screw plane az 18 deg, arc at
           r 28.6, z and z' = z - 127.513 = from the screw / tap axis), extents in z and around the circumference (min / max of the
           CPRESS > 0 nodes and the 5-95 % quantiles of the cumulative F_n), contact area (faces with mean CPRESS > 0, as
           jfwd_post.contact_summary), and the connected clusters of force-carrying faces; 'window' = |daz| <= 9 deg and |z'| <= 9 mm.
  tension  the screw head contact force on the screw along n (HEAD), the exact shear-plane resultant N_plane (screw nodal internal
           forces summed over the tip side x' < 28.61, as jfwd_shank; + = tension), and the thread-tie pull on TC-02 along n.
  shell    the TC-02 ring's share: the symmetry-plane reactions on TC-02 (global sector: az 0 u_y, az 36 u_theta) along n, the pressure
           resultant on TC-02 along n, and in a patch the prescribed cut-boundary reactions (TC-02, and the screw section at x'cut, which
           stands for the thread below the cut).  Shell pull := tie pull - seat (along n) = -(symmetry + pressure + cut)_n (+ springs,
           unclassified; z-only loads have no n component).
  TC-01    the same split on the case: HEAD (from the screw), FIT (bore), BEAR (hole), shared hole-edge nodes, symmetry, pressure, aft cut /
           patch cut; the seat force seen by TC-01 must equal the TC-02 one (and the indirect jfwd_post.contact_forces_exact value).
usage: jfwd_seatforce.py JOB [STEP ...] -> jfwd/runs/JOB/seatforce.json"""
from __future__ import annotations
import sys, json, math, gzip
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import jfwd_post as JP       # noqa: E402
import jfwd_midbay as JM     # noqa: E402
import jfwd_cforce as JC     # noqa: E402
from jfwd_shank import MATS, X_PLANE   # noqa: E402

R_FIT = 28.6
AZ_SCREW = float(JS.AZ_SCREW)
Z_AXIS = float(JD.C0[2])


def read_by(frd, n, upto=None):
    if Path(frd).exists():
        return JP.read_frd_steps(frd, n, upto)
    JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)
    try:
        return JP.read_frd_steps(frd, n, upto)
    finally:
        del JP.open


class Ctx:
    def __init__(self, job):
        self.job = job
        self.wd = JD.RUNS / job
        self.meta = json.loads((self.wd / "meta.json").read_text())
        self.patch = self.meta.get("kind") == "seat_submodel"
        tag = self.meta["mesh"]
        mj = JS.use_mesh(tag)
        self.shift = mj["shift"]
        m = self.m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
        self.X, self.T, self.B = m["X"], m["T"], m["B"]
        nf = len(m["fe"])
        if self.patch:
            self.gmeta = json.loads((JD.RUNS / self.meta["global_job"] / "meta.json").read_text())
            S = dict(np.load(JD.OUT / f"seat_{self.meta['seat_tag']}.npz", allow_pickle=False))
            self.keep = S["keep"].astype(bool)
            self.faces = {k: np.asarray(S[f"f_{k}"], int) for k in ("head_s", "head_m", "bear_s", "bear_m", "fit_s", "fit_m")}
            self.y0, self.y36 = np.asarray(S["y0"], int), np.asarray(S["y36"], int)
            self.wet_f = np.asarray(S["wet"], int)
            self.pres = np.asarray(S["pres"], int)
            pin = np.asarray(S["pair_in"])
            self.pair_mask = pin.astype(bool) if pin.dtype == bool else np.isin(np.arange(len(m["thr"])), pin)
            self.cut_z = np.zeros(0, int)
            self.springs = np.zeros(0, int)
            self.capf = None
        else:
            self.gmeta = self.meta
            self.keep = np.ones(len(self.T), bool)
            self.faces = {k: np.nonzero(m[k])[0] for k in ("head_s", "head_m", "bear_s", "bear_m", "fit_s", "fit_m")}
            self.y0, self.y36 = np.asarray(m["y0"], int), np.asarray(m["y36"], int)
            self.wet_f = np.nonzero(m["wet"] > 0)[0]
            self.pres = np.zeros(0, int)
            self.pair_mask = np.ones(len(m["thr"]), bool)
            self.cut_z = np.asarray(m["ncut"], int)
            self.springs = np.asarray(m["springs"], int)
            self.capf = True
        inK = np.zeros(len(self.X), bool)
        inK[np.unique(self.T[self.keep])] = True
        self.inK = inK
        self.n01 = m["n01"][inK[m["n01"]]]
        self.n02 = m["n02"][inK[m["n02"]]]
        self.nsc = m["nsc"][inK[m["nsc"]]]
        self.a_tie = m["new_thr"][self.pair_mask]
        self.b_tie = m["thr"][self.pair_mask]
        X = self.X
        r = np.hypot(X[:, 0], X[:, 1])
        self.er = np.stack([X[:, 0] / np.maximum(r, 1e-12), X[:, 1] / np.maximum(r, 1e-12), np.zeros(len(X))], 1)
        self.az = np.degrees(np.arctan2(X[:, 1], X[:, 0]))
        self.r = r
        frd = self.wd / f"{job}.frd"
        self.frd = frd
        self.by = read_by(frd, len(X))
        self.names = self.meta["steps"]

    def nodes(self, key):
        f = self.faces[key]
        return np.unique(np.concatenate([self.m["fcn"][f].ravel(), self.m["fmn"][f].ravel()])) if len(f) else np.zeros(0, int)

    def screw_side(self, a, b):
        na, nb = self.nodes(a), self.nodes(b)
        insc = np.isin(na, self.m["nsc"]).mean() if len(na) else 0
        return (na, nb) if insc > 0.5 else (nb, na)

    def temps(self, nm):
        if nm in ("SEAT", "PRELOAD"):
            return np.full(len(self.X), 293.15), 0.0
        sdef = self.gmeta["step_defs"][nm]
        Tn = JM.step_temps(self.m, self.shift, sdef)
        return np.where(np.isfinite(Tn), Tn, 293.15), float(sdef[0])

    def applied(self, pc):
        """applied nodal loads (pressure consistent loads; global: + cap and M14 z-tractions)."""
        m = self.m
        Fa = np.zeros((len(self.X), 3))
        if pc <= 0:
            return Fa
        for i in self.wet_f:
            for nd in m["fmn"][i]:
                Fa[nd] += -pc * m["wet"][i] * m["area"][i] * m["nrm"][i] / 3.0
        if self.capf:
            cap_unit = float(self.meta["cap_force_per_MPa_N"])
            for nd, F in JD.traction_cloads(m, m["cbw"], [0.0, 0.0, pc * cap_unit]).items():
                Fa[nd] += F
            for nd, F in JD.traction_cloads(m, m["m14"], [0.0, 0.0, pc * math.pi * 10.1 ** 2 / 10.0]).items():
                Fa[nd] += F
        return Fa


def vec(v, nd=1):
    return [round(float(x), nd) for x in v]


def quantiles(x, w, qs=(0.05, 0.95)):
    k = w > 0
    if not k.any():
        return [None for _ in qs]
    o = np.argsort(x[k])
    xs, ws = x[k][o], w[k][o]
    c = np.cumsum(ws) / ws.sum()
    return [round(float(xs[min(np.searchsorted(c, q), len(xs) - 1)]), 3) for q in qs]


def footprint(c, nodes, Fn, cp, faces_fit):
    """nodes: TC-02 FIT nodes; Fn their normal force (+ compressive); cp their CPRESS (or None)."""
    X = c.X
    daz = c.az[nodes] - AZ_SCREW
    z = X[nodes, 2]
    arc = np.radians(daz) * R_FIT
    rp = np.hypot(arc, z - Z_AXIS)
    out = {}
    tot = float(Fn.sum())
    if abs(tot) > 1e-9:
        out["centroid_force_weighted"] = {"daz_deg": round(float((Fn * daz).sum() / tot), 3), "arc_mm": round(float((Fn * arc).sum() / tot), 3),
                                          "z_mm": round(float((Fn * z).sum() / tot), 3), "z_prime_mm": round(float((Fn * z).sum() / tot - Z_AXIS), 3)}
    if cp is not None:
        on = cp > 1e-9
        out["n_nodes_CPRESS_pos"] = int(on.sum())
        if on.any():
            out["extent_CPRESS_pos"] = {"z_mm": [round(float(z[on].min()), 3), round(float(z[on].max()), 3)],
                                        "z_prime_mm": [round(float(z[on].min() - Z_AXIS), 3), round(float(z[on].max() - Z_AXIS), 3)],
                                        "daz_deg": [round(float(daz[on].min()), 3), round(float(daz[on].max()), 3)],
                                        "arc_mm": [round(float(arc[on].min()), 3), round(float(arc[on].max()), 3)],
                                        "r_prime_mm": [round(float(rp[on].min()), 3), round(float(rp[on].max()), 3)],
                                        "max_CPRESS_MPa_edge_penalty_artefact": round(float(cp.max()), 2)}
            out["r_prime_force_weighted_mm"] = round(float((Fn * rp).sum() / tot), 3) if abs(tot) > 1e-9 else None
            out["r_prime_quantiles_5_95_mm"] = quantiles(rp, Fn)
            out["Fn_on_CPRESS_pos_nodes_N"] = round(float(Fn[on].sum()), 1)
            out["Fn_on_other_nodes_N"] = round(float(Fn[~on].sum()), 1)
        # contact area: faces with mean CPRESS > 0 (as jfwd_post.contact_summary)
        pos = {int(n): float(v) for n, v in zip(nodes, cp)}
        fm = []
        for fi in faces_fit:
            nn = list(c.m["fcn"][fi]) + list(c.m["fmn"][fi])
            fm.append(np.mean([pos.get(int(n), 0.0) for n in nn]))
        fm = np.array(fm)
        A = c.m["area"][faces_fit]
        out["area_faces_mean_CPRESS_pos_mm2"] = round(float(A[fm > 0].sum()), 3)
        out["n_faces_mean_CPRESS_pos"] = int((fm > 0).sum())
    mx = float(np.abs(Fn).max()) if len(Fn) else 0.0
    act = np.abs(Fn) > 0.01 * mx if mx > 0 else np.zeros(len(Fn), bool)
    out["n_force_carrying_nodes"] = int(act.sum())
    if act.any():
        out["extent_force_carrying"] = {"z_prime_mm": [round(float(z[act].min() - Z_AXIS), 3), round(float(z[act].max() - Z_AXIS), 3)],
                                        "daz_deg": [round(float(daz[act].min()), 3), round(float(daz[act].max()), 3)]}
    q = quantiles(z - Z_AXIS, Fn)
    qa = quantiles(arc, Fn)
    out["quantiles_5_95_of_Fn"] = {"z_prime_mm": q, "arc_mm": qa}
    win = (np.abs(daz) <= 9.0) & (np.abs(z - Z_AXIS) <= 9.0)
    out["window_daz9_zp9_N"] = round(float(Fn[win].sum()), 1)
    out["outside_window_N"] = round(float(Fn[~win].sum()), 1)
    # clusters of force-carrying faces (faces with any force-carrying node), union-find on shared nodes
    idx = {int(n): i for i, n in enumerate(nodes)}
    actn = set(int(n) for n in nodes[act])
    fl = [fi for fi in faces_fit if any(int(n) in actn for n in list(c.m["fcn"][fi]) + list(c.m["fmn"][fi]))]
    par = {}

    def find(a):
        while par.setdefault(a, a) != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for fi in fl:
        nn = [int(n) for n in list(c.m["fcn"][fi]) + list(c.m["fmn"][fi])]
        r0 = find(nn[0])
        for n in nn[1:]:
            par[find(n)] = r0
    groups = {}
    for n in par:
        groups.setdefault(find(n), []).append(n)
    cl = []
    for g in groups.values():
        ii = np.array([idx[n] for n in g if n in idx])
        if not len(ii):
            continue
        F = float(Fn[ii].sum())
        cen = {}
        if abs(F) > 1e-9:
            cen = {"daz_deg": round(float((Fn[ii] * daz[ii]).sum() / F), 3), "z_prime_mm": round(float((Fn[ii] * (z[ii] - Z_AXIS)).sum() / F), 3)}
        cl.append({"Fn_N": round(F, 1), "n_nodes": int(len(ii)), "centroid": cen,
                   "z_prime_mm": [round(float(z[ii].min() - Z_AXIS), 3), round(float(z[ii].max() - Z_AXIS), 3)],
                   "daz_deg": [round(float(daz[ii].min()), 3), round(float(daz[ii].max()), 3)]})
    cl.sort(key=lambda d: -abs(d["Fn_N"]))
    out["clusters"] = cl[:6]
    out["n_clusters"] = len(cl)
    return out


def decompose(c, nm, F):
    m, X, T, B = c.m, c.X, c.T, c.B
    U = F["DISP"][:, :3]
    Tn, pc = c.temps(nm)
    e1, nu1, a1 = MATS["AL"]
    es, nus, as_ = MATS["A480"]
    f01 = JC.body_forces(X, T[c.keep & (B == "TC-01")], U, Tn, e1, nu1, a1)
    f02 = JC.body_forces(X, T[c.keep & (B == "TC-02")], U, Tn, e1, nu1, a1)
    fsc = JC.body_forces(X, T[c.keep & (B == "SCREW")], U, Tn, es, nus, as_)
    Fa = c.applied(pc)
    g01, g02, gsc = f01 - Fa, f02 - Fa, fsc - Fa
    EN = JD.EN
    n0 = np.array([0.0, 1.0, 0.0])
    n36 = np.array([-JD.S36, JD.C36, 0.0])
    C = F.get("CONTACT")
    # ---------------- screw
    hs, hm = c.screw_side("head_s", "head_m")
    bs, bm = c.screw_side("bear_s", "bear_m")
    cons = np.unique(np.concatenate([m[k].ravel() for k in ("sec", "new_sec", "thr", "new_thr")]))
    hs_c = np.setdiff1d(hs, cons)
    bs_c = np.setdiff1d(np.setdiff1d(bs, hs), cons)
    head_scr = gsc[hs_c].sum(0)
    xs = JD.loc(X[c.nsc])[0]
    tip = c.nsc[xs < X_PLANE]
    Fpl = gsc[tip].sum(0)
    N_pl = float(Fpl @ EN)
    V_pl = Fpl - N_pl * EN
    scr_contact_nodes = set(np.concatenate([hs, bs]).tolist())
    a_in_contact = np.array([int(a) in scr_contact_nodes for a in c.a_tie])
    a_pres = np.isin(c.a_tie, c.pres)
    tie_on_scr = gsc[c.a_tie].sum(0)
    rec = {"label": (c.gmeta["step_defs"].get(nm, [None, None, nm])[2] if nm not in ("SEAT", "PRELOAD") else nm), "Pc_MPa": pc}
    rec["screw"] = {"HEAD_on_screw_along_n_N": round(float(head_scr @ EN), 1), "HEAD_on_screw_vec_N": vec(head_scr),
                    "N_plane_N_tension_pos": round(-N_pl, 1), "V_plane_N": round(float(np.linalg.norm(V_pl)), 1),
                    "tie_force_on_screw_along_n_N": round(float(tie_on_scr @ EN), 1),
                    "n_tie_screw_nodes_also_in_screw_contact": int(a_in_contact.sum()), "n_tie_screw_nodes_prescribed": int(a_pres.sum())}
    if c.patch and len(c.pres):
        ps = np.intersect1d(c.pres, c.nsc)
        rec["screw"]["cut_reaction_on_screw_vec_N"] = vec(gsc[ps].sum(0))
        rec["screw"]["cut_reaction_on_screw_along_n_N"] = round(float(gsc[ps].sum(0) @ EN), 1)
    # ---------------- TC-02 classes
    fit02 = np.intersect1d(c.nodes("fit_s"), c.n02)
    b2a = {int(b): int(a) for a, b in zip(c.a_tie, c.b_tie)}
    sym0 = np.intersect1d(c.y0, c.n02)
    sym36 = np.intersect1d(c.y36, c.n02)
    Fc = g02[fit02].copy()
    pres_set = set(c.pres.tolist())
    s0_set, s36_set = set(sym0.tolist()), set(sym36.tolist())
    tie_part_fit = np.zeros(3)
    sym_part_fit = np.zeros(3)
    contam = 0
    for i, n in enumerate(fit02):
        n = int(n)
        if n in b2a:
            a = b2a[n]
            if a in scr_contact_nodes or a in pres_set:
                contam += 1
            Fc[i] += gsc[a]
            tie_part_fit += -gsc[a]
        if n in s0_set:
            p = (Fc[i] @ n0) * n0
            Fc[i] -= p
            sym_part_fit += p
        elif n in s36_set:
            p = (Fc[i] @ n36) * n36
            Fc[i] -= p
            sym_part_fit += p
    Fn = -(Fc * c.er[fit02]).sum(1)
    seat_vec = Fc.sum(0)
    cls02 = {}
    used = set(fit02.tolist())
    tie_b = np.array([b for b in c.b_tie if int(b) not in used and int(b) not in pres_set], int)
    used |= set(tie_b.tolist())
    pres02 = np.array([n for n in np.intersect1d(c.pres, c.n02) if int(n) not in used], int)
    used |= set(pres02.tolist())
    s0 = np.array([n for n in sym0 if int(n) not in used], int)
    used |= set(s0.tolist())
    s36 = np.array([n for n in sym36 if int(n) not in used], int)
    used |= set(s36.tolist())
    spr = np.array([n for n in np.intersect1d(c.springs, c.n02) if int(n) not in used], int)
    used |= set(spr.tolist())
    rest02 = np.array([n for n in c.n02 if int(n) not in used], int)
    tie_vec = g02[tie_b].sum(0) + tie_part_fit
    sym_vec = (g02[s0].sum(0) if len(s0) else np.zeros(3)) + (g02[s36].sum(0) if len(s36) else np.zeros(3)) + sym_part_fit
    sym_inplane = 0.0
    if len(s0):
        q = g02[s0] - np.outer(g02[s0] @ n0, n0)
        sym_inplane = max(sym_inplane, float(np.abs(q).max()))
    if len(s36):
        q = g02[s36] - np.outer(g02[s36] @ n36, n36)
        sym_inplane = max(sym_inplane, float(np.abs(q).max()))
    cut_vec = g02[pres02].sum(0) if len(pres02) else np.zeros(3)
    spr_vec = g02[spr].sum(0) if len(spr) else np.zeros(3)
    rest_vec = g02[rest02].sum(0) if len(rest02) else np.zeros(3)
    app02 = Fa[c.n02].sum(0)
    total = seat_vec + tie_vec + sym_vec + cut_vec + spr_vec + rest_vec + app02
    S_n_in = float(-seat_vec @ EN)
    S_r = float(Fn.sum())
    tie_n_out = float(tie_vec @ EN)
    cp = C[fit02, 3] if C is not None else None
    rec["seat_TC02"] = {"normal_force_radial_sum_N": round(S_r, 1), "along_n_inward_N": round(S_n_in, 1), "vec_on_TC02_N": vec(seat_vec),
                        "z_on_TC02_N": round(float(seat_vec[2]), 1), "n_fit_nodes": int(len(fit02)),
                        "n_fit_tie_nodes_with_contaminated_screw_node": int(contam),
                        "footprint": footprint(c, fit02, Fn, cp, c.faces["fit_s"])}
    shell_direct = float(-(sym_vec + cut_vec + spr_vec + rest_vec + app02) @ EN)
    rec["shell_TC02"] = {"tie_pull_on_TC02_along_n_N": round(tie_n_out, 1), "tie_vec_on_TC02_N": vec(tie_vec),
                         "shell_pull_N_tie_minus_seat": round(tie_n_out - S_n_in, 1),
                         "shell_pull_direct_minus_sym_cut_press_N": round(shell_direct, 1),
                         "sym_reaction_along_n_N": round(float(sym_vec @ EN), 1), "sym_reaction_vec_N": vec(sym_vec),
                         "sym_inplane_residual_max_N": round(sym_inplane, 4),
                         "cut_reaction_TC02_along_n_N": round(float(cut_vec @ EN), 1), "cut_reaction_TC02_vec_N": vec(cut_vec),
                         "pressure_on_TC02_along_n_N": round(float(app02 @ EN), 1), "applied_on_TC02_vec_N": vec(app02),
                         "springs_vec_N": vec(spr_vec, 3), "unclassified_vec_N": vec(rest_vec, 3), "n_unclassified_nodes": int(len(rest02)),
                         "closure_residual_vec_N": vec(total, 4)}
    # ---------------- TC-01 classes
    fit01 = np.intersect1d(c.nodes("fit_m"), c.n01)
    head01 = np.intersect1d(hm, c.n01)
    bear01 = np.intersect1d(bm, c.n01)
    sh_fb = np.intersect1d(fit01, bear01)
    sh_hb = np.intersect1d(head01, bear01)
    fit_only = np.setdiff1d(fit01, bear01)
    head_only = np.setdiff1d(head01, bear01)
    bear_only = np.setdiff1d(np.setdiff1d(bear01, fit01), head01)
    used = set(np.concatenate([fit01, head01, bear01]).tolist())
    p01 = np.array([n for n in np.intersect1d(c.pres, c.n01) if int(n) not in used], int)
    used |= set(p01.tolist())
    t0 = np.array([n for n in np.intersect1d(c.y0, c.n01) if int(n) not in used], int)
    used |= set(t0.tolist())
    t36 = np.array([n for n in np.intersect1d(c.y36, c.n01) if int(n) not in used], int)
    used |= set(t36.tolist())
    cz = np.array([n for n in np.intersect1d(c.cut_z, c.n01) if int(n) not in used], int)
    used |= set(cz.tolist())
    rest01 = np.array([n for n in c.n01 if int(n) not in used], int)
    # symmetry-plane nodes of TC-01 that are also contact nodes: the plane-normal component is the symmetry reaction (fea3d 11:06Z)
    g01 = g01.copy()
    sym01_extra = np.zeros(3)
    for nn_, nv in ((np.intersect1d(c.y0, c.n01), n0), (np.intersect1d(c.y36, c.n01), n36)):
        sel = np.intersect1d(nn_, np.concatenate([fit01, head01, bear01, p01]))
        if len(sel):
            pp = np.outer(g01[sel] @ nv, nv)
            g01[sel] -= pp
            sym01_extra += pp.sum(0)
    S01 = lambda nn: g01[nn].sum(0) if len(nn) else np.zeros(3)
    r01 = lambda nn: float((g01[nn] * c.er[nn]).sum()) if len(nn) else 0.0
    rec["TC01"] = {"FIT_only_along_n_N": round(float(S01(fit_only) @ EN), 1), "FIT_only_radial_sum_N": round(r01(fit_only), 1),
                   "FIT_BEAR_shared_edge_along_n_N": round(float(S01(sh_fb) @ EN), 1), "FIT_BEAR_shared_edge_radial_N": round(r01(sh_fb), 1),
                   "HEAD_only_along_n_N": round(float(S01(head_only) @ EN), 1), "HEAD_BEAR_shared_along_n_N": round(float(S01(sh_hb) @ EN), 1),
                   "BEAR_only_vec_N": vec(S01(bear_only)), "sym_along_n_N": round(float((S01(t0) + S01(t36) + sym01_extra) @ EN), 1),
                   "cut_patch_along_n_N": round(float(S01(p01) @ EN), 1), "aft_cut_z_N": round(float(S01(cz)[2]), 1),
                   "pressure_on_TC01_along_n_N": round(float(Fa[c.n01].sum(0) @ EN), 1),
                   "unclassified_vec_N": vec(S01(rest01), 3), "n_unclassified_nodes": int(len(rest01))}
    if not c.patch:
        ce = JP.contact_forces_exact(m, U, Tn, pc)
        rec["TC01"]["indirect_contact_forces_exact"] = ce
    return rec


def main(job, steps=None):
    c = Ctx(job)
    out = {"job": job, "patch": c.patch, "mesh": c.meta["mesh"], "frd": str(c.frd), "doc": __doc__.split("usage:")[0].strip(),
           "evidence": "SIM (.frd) + DERIVED (exact nodal internal forces, consistent loads)", "z_axis_mm": Z_AXIS, "az_screw_deg": AZ_SCREW,
           "steps": {}}
    if c.patch:
        out["global_job"] = c.meta["global_job"]
    for k, nm in enumerate(c.names):
        if (k + 1) not in c.by or "DISP" not in c.by[k + 1]:
            continue
        if steps and nm not in steps:
            continue
        rec = decompose(c, nm, c.by[k + 1])
        out["steps"][nm] = rec
        s, sh, sc = rec["seat_TC02"], rec["shell_TC02"], rec["screw"]
        fp = s["footprint"]
        print(f"{nm}: HEAD {sc['HEAD_on_screw_along_n_N']} N_plane {sc['N_plane_N_tension_pos']} tie->TC02 {sh['tie_pull_on_TC02_along_n_N']} | "
              f"seat r {s['normal_force_radial_sum_N']} n {s['along_n_inward_N']} z {s['z_on_TC02_N']} | shell {sh['shell_pull_N_tie_minus_seat']} "
              f"direct {sh['shell_pull_direct_minus_sym_cut_press_N']} (sym {sh['sym_reaction_along_n_N']} cut {sh['cut_reaction_TC02_along_n_N']} "
              f"p {sh['pressure_on_TC02_along_n_N']}) | TC01 FIT {rec['TC01']['FIT_only_along_n_N']}+edge {rec['TC01']['FIT_BEAR_shared_edge_along_n_N']} "
              f"| centroid {fp.get('centroid_force_weighted')} r' {fp.get('r_prime_force_weighted_mm')} q {fp.get('r_prime_quantiles_5_95_mm')} ext {fp.get('extent_CPRESS_pos')} area {fp.get('area_faces_mean_CPRESS_pos_mm2')} "
              f"win {fp['window_daz9_zp9_N']} out {fp['outside_window_N']} | uncl02 {sh['unclassified_vec_N']} res {sh['closure_residual_vec_N']}", flush=True)
    (c.wd / "seatforce.json").write_text(json.dumps(out, indent=1, default=float))
    print("wrote", c.wd / "seatforce.json")
    return out


if __name__ == "__main__":
    a = [x for x in sys.argv[2:] if "=" not in x]
    main(sys.argv[1], a or None)
