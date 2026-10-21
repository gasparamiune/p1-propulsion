"""FEA3D J-FWD sub-model post-processing (v3.5.2 item 2).  Reads jfwd/runs/<job>/<job>.frd + .dat and the model npz.

Per step: screw section forces (pretension-section reactions at x' 30.2; stress-resultant integration over screw cross-sections at
x' 28.70 / 29.0 / 29.5 / 30.2 / 31.0 (nodal-averaged S, quadratic interpolation)); screw checks per CHANGELOG 234 (1)(b) (Mechanical's
formulas: A_s 14.18 / A_3 12.69 mm2, Rp0.2 600 / Rm 800 MPa x k_T / k_Tu = SS316L Fty(T)/Fty(20), Ftu(T)/Ftu(20); TC-02 internal-thread
shear on A_n 63.5 mm2 against 0.577 Fty(T) / 0.6 Ftu(T)); TC-01 / TC-02 all-node and band (> 1 mm from the hole / tap surface) von Mises
with node, position and distances; SCL membrane and membrane+bending (linearised von Mises) on the net ligament and the shear-out path
of both members; Neuber local strain at the all-node hole-edge peaks; contact state (pressure, slip) per pair.
usage: jfwd_post.py <job>"""
from __future__ import annotations
import sys, json, math, re, gzip
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import fe3d                  # noqa: E402
import asm3d as A3           # noqa: E402

MAT = A3.engmat.MATERIALS
AS, A3M, AN = 14.18, 12.69, 63.5
RP20, RM20 = 600.0, 800.0
SMAT = "A480"     # screw material of the run being posted (set from meta in post(); jfwd_mat.py, 11:55Z)
TK = 273.15


def tab(mat, key, T):
    d = MAT[mat][key]
    f = 1e6 if key in ("Fty", "Ftu", "E") else 1.0
    if "T_C" in d:
        return float(np.interp(T, d["T_C"], d["v"])) / f
    return d["v"] / f


def kT(T):
    return tab("SS316L", "Fty", max(T, 20.0)) / tab("SS316L", "Fty", 20.0)


def kTu(T):
    return tab("SS316L", "Ftu", max(T, 20.0)) / tab("SS316L", "Ftu", 20.0)


def vm(S):
    S = np.asarray(S)
    sx, sy, sz, txy, tyz, txz = (S[..., i] for i in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (txy ** 2 + tyz ** 2 + txz ** 2))


def read_dat(path):
    """per step (in order): ref-node U and RF (*NODE PRINT N_REF) and contact CF totals if printed."""
    txt = open(path, errors="replace").read().splitlines()
    out = []
    k = 0
    cur = None
    while k < len(txt):
        L = txt[k]
        m = re.match(r"\s*displacements \(vx,vy,vz\) for set N_REF and time\s+([0-9.Ee+-]+)", L)
        if m:
            t = float(m.group(1))
            cur = {"time": t}
            out.append(cur)
            v = txt[k + 2].split()
            cur["U"] = [float(x) for x in v[1:4]]
            k += 3
            continue
        m = re.match(r"\s*forces \(fx,fy,fz\) for set N_REF and time\s+([0-9.Ee+-]+)", L)
        if m:
            v = txt[k + 2].split()
            if cur is not None:
                cur["RF"] = [float(x) for x in v[1:4]]
            k += 3
            continue
        if "contact" in L.lower() and "force" in L.lower() and cur is not None:
            cur.setdefault("cf_lines", []).append(L.strip())
            j = k + 1
            while j < len(txt) and txt[j].strip() and j < k + 6:
                cur["cf_lines"].append(txt[j].strip())
                j += 1
        k += 1
    return out


def read_frd_steps(path, n_nodes, upto=None):
    """{ccx step number: {block name: (n_nodes, ncomp) array, 0-based node rows}} keeping the LAST increment written for each step
    (the '1PSTEP <block> <increment> <step>' header of every block; ccx writes every increment unless FREQUENCY limits it).
    Streams the file; an incomplete trailing block (file still being written) is dropped; upto: ignore ccx steps > upto."""
    out = {}
    cur_step, cur_inc = None, None
    name = ncomp = None
    ids, vals = [], []
    in_block = False
    with open(path, "r", errors="replace") as fh:
        for L in fh:
            if in_block:
                if L.startswith(" -1"):
                    ids.append(int(L[3:13]))
                    t = L.rstrip("\r\n")
                    nf = min((len(t) - 13) // 12, ncomp, 6)
                    v = [float(t[13 + 12 * k: 25 + 12 * k]) for k in range(nf)]
                    vals.append(v + [0.0] * (min(ncomp, 6) - nf))
                elif L.startswith(" -3"):
                    in_block = False
                    if upto is not None and cur_step > upto:
                        continue
                    arr = np.zeros((n_nodes, min(ncomp, 6)))
                    ida = np.asarray(ids, np.int64)
                    keep = ida <= n_nodes
                    arr[ida[keep] - 1] = np.asarray(vals)[keep]
                    d = out.setdefault(cur_step, {"_inc": cur_inc})
                    if cur_inc != d["_inc"]:                  # a later increment of the same step replaces the earlier one
                        out[cur_step] = d = {"_inc": cur_inc}
                    d[name] = arr
                continue
            if L.startswith("    1PSTEP"):
                f = L.split()
                cur_inc, cur_step = int(f[2]), int(f[3])
            elif L.startswith(" -4  "):
                name, ncomp = L.split()[1], int(L.split()[2])
                ids, vals = [], []
                in_block = True
    return out


class Locator:
    def __init__(self, X, T):
        self.X, self.T = X, T
        self.C = X[T[:, :4]].mean(1)
        self.kd = cKDTree(self.C)
        Xc = X[T[:, :4]]
        self.Minv = np.linalg.inv(np.stack([Xc[:, 1] - Xc[:, 0], Xc[:, 2] - Xc[:, 0], Xc[:, 3] - Xc[:, 0]], 2))
        self.X0 = Xc[:, 0]

    def bary(self, P, k=24):
        P = np.atleast_2d(P)
        _, cand = self.kd.query(P, k=min(k, len(self.C)))
        el = -np.ones(len(P), np.int64)
        L = np.zeros((len(P), 4))
        best = np.full(len(P), -np.inf)
        for j in range(cand.shape[1]):
            e = cand[:, j]
            l123 = np.einsum("nij,nj->ni", self.Minv[e], P - self.X0[e])
            l = np.column_stack([1 - l123.sum(1), l123])
            mn = l.min(1)
            upd = mn > best
            best[upd] = mn[upd]
            el[upd] = e[upd]
            L[upd] = l[upd]
        return el, L, best

    def interp(self, F, P):
        el, L, best = self.bary(P)
        L1, L2, L3, L4 = L.T
        N = np.column_stack([L1 * (2 * L1 - 1), L2 * (2 * L2 - 1), L3 * (2 * L3 - 1), L4 * (2 * L4 - 1),
                             4 * L1 * L2, 4 * L2 * L3, 4 * L1 * L3, 4 * L1 * L4, 4 * L2 * L4, 4 * L3 * L4])
        V = F[self.T[el]]
        return np.einsum("nk,nk...->n...", N, V), best


def section_force(loc, S, x_s, n=24, nr=10):
    """stress resultant (N, V_t1, V_z; and the moment about the section centre) over the screw disc r' <= 2.5 at x' = x_s."""
    rr = (np.arange(nr) + 0.5) / nr * JS.GEO["shank_r"] * 0.999
    th = (np.arange(n) + 0.5) / n * 2 * math.pi
    R, TH = np.meshgrid(rr, th, indexing="ij")
    dA = (JS.GEO["shank_r"] * 0.999 / nr) * R * (2 * math.pi / n)
    yl, zl = R * np.cos(TH), R * np.sin(TH)
    P = JD.C0 + x_s * JD.EN + yl.ravel()[:, None] * JD.ET1 + zl.ravel()[:, None] * JD.ET2
    Sv, best = loc.interp(S, P)
    sig = np.zeros((len(P), 3, 3))
    sig[:, 0, 0], sig[:, 1, 1], sig[:, 2, 2] = Sv[:, 0], Sv[:, 1], Sv[:, 2]
    sig[:, 0, 1] = sig[:, 1, 0] = Sv[:, 3]
    sig[:, 1, 2] = sig[:, 2, 1] = Sv[:, 4]
    sig[:, 0, 2] = sig[:, 2, 0] = Sv[:, 5]
    t = sig @ JD.EN                       # traction on the face with normal +n (force of the head side on the tip side, sign: tension +)
    F = (t * dA.ravel()[:, None]).sum(0)
    arm = yl.ravel()[:, None] * JD.ET1 + zl.ravel()[:, None] * JD.ET2
    Mo = (np.cross(arm, t) * dA.ravel()[:, None]).sum(0)
    return {"x_prime_mm": x_s, "N": float(F @ JD.EN), "V_t1": float(F @ JD.ET1), "V_z": float(F @ JD.ET2),
            "V": float(math.hypot(F @ JD.ET1, F @ JD.ET2)), "M_bend_Nmm": float(math.hypot(Mo @ JD.ET1, Mo @ JD.ET2)),
            "min_bary": float(best.min()), "area_mm2": float(dA.sum())}


def linearise(loc, S, a, b, n=41):
    """ASME-type linearisation of all six components along a -> b (t = |b - a|): membrane and membrane + bending at both ends."""
    s = np.linspace(0, 1, n)
    P = a[None] + s[:, None] * (b - a)[None]
    Sv, best = loc.interp(S, P)
    t = float(np.linalg.norm(b - a))
    sm = np.trapezoid(Sv, s, axis=0)
    sb = 6.0 * np.trapezoid(Sv * (0.5 - s)[:, None], s, axis=0)
    return {"t_mm": round(t, 4), "Pm": float(vm(sm)), "PmPb": float(max(vm(sm + sb), vm(sm - sb))), "peak_on_line": float(vm(Sv).max()),
            "min_bary": float(best.min()), "sm": [float(c) for c in sm], "sb": [float(c) for c in sb]}


def neuber(sig_el, E, Fty, n):
    """Neuber sigma*eps = sig_el^2 / E on eps = s/E + 0.002 (s/Fty)^n; returns (s, eps)."""
    lo, hi = 0.0, sig_el
    for _ in range(80):
        s = 0.5 * (lo + hi)
        e = s / E + 0.002 * (s / Fty) ** n
        if s * e > sig_el ** 2 / E:
            hi = s
        else:
            lo = s
    return s, s / E + 0.002 * (s / Fty) ** n


def contact_summary(m, F, mu):
    """per pair (HEAD / BEAR / FIT): faces in contact (mean CPRESS of the 6 face nodes > 0), contact area, max CPRESS, the normal-force
    resultant on the slave (sum of -p n A over the slave faces; engine axes), max |opening| closed, and for mu > 0 the slip fraction
    (faces with |CSHEAR| >= 0.98 mu CPRESS, mean over the face nodes)."""
    C = F.get("CONTACT")
    if C is None:
        return None
    out = {}
    for nm, key in (("HEAD", "head_s"), ("BEAR", "bear_s"), ("FIT", "fit_s")):
        msk = m[key]
        nodes6 = np.concatenate([m["fcn"][msk], m["fmn"][msk]], 1)
        cp = C[nodes6, 3].mean(1)
        sh = np.hypot(C[nodes6, 4], C[nodes6, 5]).mean(1)
        on = cp > 1e-6
        A = m["area"][msk]
        Fv = -(cp[:, None] * m["nrm"][msk] * A[:, None]).sum(0)
        rec = {"faces": int(msk.sum()), "faces_in_contact": int(on.sum()), "area_in_contact_mm2": round(float(A[on].sum()), 3),
               "max_CPRESS_MPa": round(float(C[np.unique(nodes6), 3].max()), 2),
               "CPRESS_face_mean_integral_N_BIASED_not_used": [round(float(v), 1) for v in Fv]}
        if mu > 0 and on.any():
            slip = on & (sh >= 0.98 * mu * cp)
            rec["slip_area_fraction"] = round(float(A[slip].sum() / max(A[on].sum(), 1e-12)), 3)
            rec["max_CSHEAR_MPa"] = round(float(sh.max()), 2)
        out[nm] = rec
    return out


def contact_forces_exact(m, U, Tnod_K, pc, smat="A480"):
    """EXACT contact resultants from the solved displacements (fea3d 2026-10-20): nodal internal forces f = sum_e int B^T sigma dV
    (jfwd_cforce.body_forces, C3D10 4-point rule, E(T) / alpha(T) secant from 293.15 K as in the deck).  On the screw the HEAD face nodes
    and the shank (BEAR) nodes carry only those contacts, so their sums are the contact forces on the screw.  FIT: the TC-01 node sum of
    f . e_r(az) contains only HEAD + BEAR + FIT + pressure (the symmetry-plane reactions are tangential, the aft-cut reaction axial), so
    FIT_r(on TC-01) = sum_TC01 f.e_r + sum_screw(HEAD + BEAR) f.e_r + Pc sum_wet,TC01 A (n . e_r).  The CPRESS face-mean integral of
    contact_summary is biased high (x1.8 HEAD, x7 FIT at js4 PRELOAD) for quadratic faces and is NOT used."""
    import jfwd_cforce as JC
    X, T, B = m["X"], m["T"], m["B"]
    mats = {"AL": ([[6.890e4, 293.15], [6.620e4, 373.15], [6.340e4, 423.15], [6.0e4, 473.15], [5.58e4, 523.15], [5.1e4, 573.15]], 0.33,
                   [[2.32e-5, 293.15], [2.36e-5, 373.15], [2.43e-5, 473.15], [2.52e-5, 573.15]]),
            "A480": ([[1.93e5, 293.15], [1.8721e5, 373.15], [1.7949e5, 473.15], [1.72735e5, 573.15], [1.6598e5, 673.15]], 0.29,
                     [[1.6e-5, 293.15], [1.6e-5, 373.15], [1.65e-5, 473.15], [1.7e-5, 573.15], [1.75e-5, 673.15]])}
    f = np.zeros((len(X), 3))
    import jfwd_mat as JMAT
    mats[smat] = JMAT.ROWS[smat]
    for b, mt in (("TC-01", "AL"), ("TC-02", "AL"), ("SCREW", smat)):
        e, nu, a = mats[mt]
        f += JC.body_forces(X, T[B == b], U, Tnod_K, e, nu, a)
    az = np.arctan2(X[:, 1], X[:, 0])
    er = np.stack([np.cos(az), np.sin(az), np.zeros(len(X))], 1)
    nodes = lambda key: np.unique(np.concatenate([m["fcn"][m[key]].ravel(), m["fmn"][m[key]].ravel()]))
    nsc_set = set(m["nsc"].tolist())
    def screw_side(a, b):
        na, nb = nodes(a), nodes(b)
        fa = np.mean([x in nsc_set for x in na])
        return (na, nb) if fa > 0.5 else (nb, na)
    hs, _ = screw_side("head_s", "head_m")        # screw head bearing face (the slave of the HEAD pair is the TC-01 OD patch)
    bs, _ = screw_side("bear_s", "bear_m")        # screw shank in the TC-01 hole
    bs = np.setdiff1d(bs, hs)
    cons = np.unique(np.concatenate([m[k].ravel() for k in ("sec", "new_sec", "thr", "new_thr")]))
    bs = np.setdiff1d(bs, cons)                   # pretension-section and thread-tie nodes carry constraint forces
    hs = np.setdiff1d(hs, cons)
    n_ax = JD.EN
    head = f[hs].sum(0)
    bear = f[bs].sum(0)
    fb = np.array(["TC-01" if b == "TC-01" else ("TC-02" if b == "TC-02" else "SCREW") for b in B[m["fe"]]])
    w01 = (m["wet"] > 0) & (fb == "TC-01")
    azf = np.arctan2((m["nrm"][w01] * 0 + X[m["fcn"][w01]].mean(1))[:, 1], X[m["fcn"][w01]].mean(1)[:, 0])
    erf = np.stack([np.cos(azf), np.sin(azf), np.zeros(len(azf))], 1)
    p_r01 = float(-(pc * m["wet"][w01] * m["area"][w01] * (m["nrm"][w01] * erf).sum(1)).sum())
    n01 = m["n01"]
    fit_r = float((f[n01] * er[n01]).sum(1).sum() + (f[hs] * er[hs]).sum(1).sum() + (f[bs] * er[bs]).sum(1).sum() - p_r01)
    bear_perp = bear - (bear @ n_ax) * n_ax
    return {"HEAD_on_screw_along_axis_N": round(float(head @ n_ax), 1), "HEAD_on_screw_vec_N": [round(float(v), 1) for v in head],
            "BEAR_on_screw_vec_N": [round(float(v), 1) for v in bear], "BEAR_shear_perp_axis_N": round(float(np.linalg.norm(bear_perp)), 1),
            "FIT_radial_on_TC01_N": round(fit_r, 1), "pressure_radial_on_TC01_N": round(p_r01, 1),
            "note": "exact from K u (contact_forces_exact); + = along the screw axis n (outward) / outward radial"}


def screw_checks(st, N, V, Ts, T02, pc, sfy, sfu, kind, smat="A480"):
    """CHANGELOG 234 (1)(b) screw checks with FE resultants N (tension), V (shear at the joint plane) per screw, NASA-STD-5020A form
    (AS RECALLED, TO-VERIFY, Mechanical's jfwd_preload_v352 formulas): A_s 14.18, A_3 12.69, A_n 63.5 mm2; A4-80 Rp0.2 600 / Rm 800 x k_T /
    k_Tu (engmat SS316L proxy, ASSUMED).  kind: 'soak' (tension only), 'LC2' (SF_y / SF_u on V, as Mechanical's hand form), 'FE-factored'
    (the step already carries the factored load: SF on nothing), 'FA1' (SF 1.0: ultimate interaction + yield shear-only on A_3)."""
    import jfwd_mat as JMAT
    Rp, Rm, kt, ktu, basis = JMAT.allowables(smat, Ts)      # 11:55Z: A480 = 600 / 800 x SS316L k_T (as before); IN718 = engmat Fty / Ftu(T)
    o = {"N_N": round(N, 1), "V_N": round(V, 1), "T_screw_C": round(Ts, 1), "kT": round(kt, 4), "kTu": round(ktu, 4),
         "kT_Rp_MPa": round(Rp, 1), "kTu_Rm_MPa": round(Rm, 1), "kind": kind, "screw_mat": smat, "allowable_basis": basis}
    st_ = N / AS
    if kind == "soak":
        o["sigma_t_MPa"] = round(st_, 1)
        o["MS_y_tension"] = round(Rp / st_ - 1, 4)
        o["MS_u_tension"] = round(Rm / st_ - 1, 4)
    else:
        fy = sfy if kind == "LC2" else 1.0
        fu = sfu if kind == "LC2" else 1.0
        tau_y = fy * V / A3M
        svm = math.sqrt(st_ ** 2 + 3 * tau_y ** 2)
        o.update({"sigma_t_MPa": round(st_, 1), "tau_factored_MPa": round(tau_y, 1), "sigma_vm_MPa": round(svm, 1),
                  "MS_y_combined": round(Rp / svm - 1, 4)})
        Rt = N / (Rm * AS)
        Rs = fu * V / (0.6 * Rm * A3M)
        q = Rt ** 2 + Rs ** 2
        o.update({"Rt": round(Rt, 4), "Rs": round(Rs, 4), "Rt2_Rs2": round(q, 4), "MS_u_interaction": round(1.0 / math.sqrt(q) - 1, 4)})
        o["MS_y_shear_only_minor"] = round(0.577 * Rp / max(V / A3M, 1e-9) - 1, 4)
    # TC-02 internal-thread shear (FED-STD-H28 area form, A_n 63.5 mm2) at the tap temperature
    tau_n = N / AN
    o["TC02_thread"] = {"tau_MPa": round(tau_n, 1), "T02_C": round(T02, 1),
                        "MS_y": round(0.577 * tab("AL6061-T6", "Fty", T02) / tau_n - 1, 4),
                        "MS_u": round(0.6 * tab("AL6061-T6", "Ftu", T02) / tau_n - 1, 4)}
    return o


def neuber_check(sig_el, T, mat="AL6061-T6"):
    """Mechanical (iii): Neuber on R-O eps = s/E + 0.002 (s/Fty)^n, n 15 and 30 (ASSUMED range), eps_L = 0.52 (0.98 - Fty/Ftu)
    (ASME VIII-2 5.3.3 m2 aluminium row, AS RECALLED, TO-VERIFY); E, Fty, Ftu at T (engmat)."""
    E, Fy, Fu = tab(mat, "E", T), tab(mat, "Fty", T), tab(mat, "Ftu", T)
    epsL = 0.52 * (0.98 - Fy / Fu)
    out = {"sigma_el_MPa": round(sig_el, 1), "T_C": round(T, 1), "E_MPa": round(E, 0), "Fty_MPa": round(Fy, 1), "Ftu_MPa": round(Fu, 1),
           "eps_limit": round(epsL, 5)}
    for nRO in (15.0, 30.0):
        sl, el = neuber(sig_el, E, Fy, nRO)
        out[f"n{int(nRO)}"] = {"sigma_local_MPa": round(sl, 1), "eps_local": round(el, 5), "MS_strain": round(epsL / el - 1, 3)}
    return out


def post(job, upto=None):
    """upto: post only ccx steps <= upto (steps completed per the .sta of a running job) -> post_partial.json"""
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    import jfwd_mat as JMAT
    global SMAT
    SMAT = JMAT.screw_mat(meta)
    tag = meta["mesh"]
    JS.use_mesh(tag)                                # 2026-10-20 08:35Z: seat geometry (spot face: x_seat 31.313, x_tap_lo 21.063)
    m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
    mj = json.loads((JD.OUT / f"mesh_{tag}.json").read_text())
    shift = mj["shift"]
    X, T, B = m["X"], m["T"], m["B"]
    frd = wd / f"{job}.frd"
    if not frd.exists() and (wd / f"{job}.frd.gz").exists():
        import shutil
        with gzip.open(wd / f"{job}.frd.gz", "rb") as fi, open(frd, "wb") as fo:
            shutil.copyfileobj(fi, fo)
    by_step = read_frd_steps(frd, len(X), upto)    # ccx step numbers: 1 = SEAT (no field output), 2 = PRELOAD, 3.. = cases
    dat = read_dat(wd / f"{job}.dat")
    names = meta["steps"]
    # the SEAT step prints no field output: frd steps = names[1:] (ccx step numbers 2 ..)
    fsteps = [nm for k, nm in enumerate(names) if (k + 1) in by_step]
    steps = [by_step[k + 1] for k, nm in enumerate(names) if (k + 1) in by_step]
    fidx = [k for k, nm in enumerate(names) if (k + 1) in by_step]
    res_missing = [nm for k, nm in enumerate(names[1:], start=2) if k not in by_step and (upto is None or k <= upto)]
    # dat: one N_REF block per increment; keep the last per step (time = step end: total times 1, 2, 3 ...)
    last = {}
    for d in dat:
        last[round(d["time"], 6)] = d
    dat_steps = [last[k] for k in sorted(last)]
    body_el = {b: np.nonzero(B == b)[0] for b in ("TC-01", "TC-02", "SCREW")}
    locs = {b: Locator(X, T[e]) for b, e in body_el.items()}
    n01, n02, nsc = m["n01"], m["n02"], m["nsc"]
    # geometry helpers
    xa, ya, za, ra = JD.loc(X)
    _, _, _, ra1 = JD.loc(X, -shift)
    d_hole = ra1 - JS.GEO["hole_r"]                  # TC-01: distance from the hole surface (radial in the hole frame)
    # TC-02: distance from the tap surface (cylinder r' 2.5 over x' 21.5 .. 28.6 and the bottom disc at x' 21.5)
    d_tap = np.where(xa >= JS.GEO["x_tap_lo"], np.abs(ra - JS.GEO["shank_r"]),
                     np.hypot(np.maximum(ra - JS.GEO["shank_r"], 0.0), JS.GEO["x_tap_lo"] - xa))
    r_g = np.hypot(X[:, 0], X[:, 1])
    res = {"job": job, "meta": meta, "steps": {}, "frd_steps_missing": res_missing}
    tcache = {}
    for i, st in enumerate(fsteps):
        F = steps[i]
        S = F["STRESS"]
        U = F["DISP"]
        o = {}
        dd = last.get(round(fidx[i] + 1.0, 6))          # dat N_REF block at the step end (total time = ccx step number)
        if dd is not None:
            o["ref_U"] = dd.get("U")
            o["ref_RF"] = dd.get("RF")
            if dd.get("cf_lines"):
                o["cf_lines"] = dd["cf_lines"][:24]
        secs = [section_force(locs["SCREW"], S, x) for x in (28.70, 29.0, 29.5, 30.2, 31.0)]
        o["screw_sections"] = secs
        if st == "PRELOAD":
            pc, tc, lab = 0.0, JD.U(20.0), "preload at 20 C"
        else:
            pc, tc, lab = meta["step_defs"][st]
        o["label"], o["Pc_MPa_abs"] = lab, pc
        # temperatures: uniform per part (step definition) or the mapped S-AX field (recomputed exactly as the deck writer did)
        Tn = None
        if isinstance(tc, (list, tuple)) and tc and tc[0] == "map":
            key = (tc[1], tc[2])
            if key not in tcache:
                tcache[key] = JD.mapped_temps(m, shift, tc[1], tc[2])
            Tn, tst = tcache[key]
            o["mapped_T"] = tst
        def part_T(nodes, part):
            if Tn is not None:
                return Tn[nodes] - TK
            if isinstance(tc, dict):
                return np.full(len(nodes), tc[part])
            return np.full(len(nodes), np.nan)
        # ---- screw: tension = section force at the interface side of the hole (x' 28.70) and at the pretension section
        sh = [s for s in secs if s["x_prime_mm"] <= 29.0]
        N_if = max(s["N"] for s in secs)
        V_if = max(s["V"] for s in sh)
        Ts = part_T(nsc[(xa[nsc] > 28.6) & (xa[nsc] < 30.5)], "SCREW")
        Ts_c = float(np.nanmax(Ts)) if np.isfinite(Ts).any() else float("nan")
        o["screw"] = {"N_max_N": round(N_if, 1), "V_shear_plane_N": round(V_if, 1), "T_shank_max_C": round(Ts_c, 1),
                      "kT": round(JMAT.allowables(SMAT, Ts_c)[2], 4), "kTu": round(JMAT.allowables(SMAT, Ts_c)[3], 4),
                      "kT_Rp_MPa": round(JMAT.allowables(SMAT, Ts_c)[0], 1), "screw_mat": SMAT}
        # case rule: soak / preload = screw tension only (234 (1)(b) soak form); LC2 at 4.5 MPa = Mechanical's hand form (SF 1.5 / 2.0 on V);
        # LC2 x1.5 / x2.0 steps = FE-factored (the joint is nonlinear: the factored step is the like-for-like FE check); FA-1 = SF 1.0
        if st == "PRELOAD" or st.startswith("SOAK") or st == "COLD":
            kind, sfy, sfu = "soak", 1.0, 1.0
        elif st.startswith("LC2") and (st.endswith("Y") or st.endswith("U")):
            kind, sfy, sfu = "FE-factored", 1.0, 1.0
        elif st.startswith("LC2"):
            kind, sfy, sfu = "LC2", 1.5, 2.0
        else:
            kind, sfy, sfu = "FA1", 1.0, 1.0
        tapz = n02[(d_tap[n02] < 1.0) & (xa[n02] >= JS.GEO["x_tap_lo"] - 0.1) & (xa[n02] <= 28.6)]
        T02 = float(np.nanmax(part_T(tapz, "TC-02")))
        o["screw_check"] = screw_checks(st, N_if, V_if, Ts_c, T02, pc, sfy, sfu, kind, SMAT)
        o["case_rule"] = {"kind": kind, "SF_y": sfy, "SF_u": sfu,
                          "member_SF": ({"LC2": (1.5, 2.0)}.get(kind, (1.0, 1.0)))}
        o["contact"] = contact_summary(m, F, float(meta.get("mu", 0.0)))
        Tnod = np.full(len(X), 293.15)
        if Tn is not None:
            Tnod = np.asarray(Tn, float)
        elif isinstance(tc, dict):
            for part, nodes in (("TC-01", n01), ("TC-02", n02), ("SCREW", nsc)):
                Tnod[nodes] = tc[part] + TK
        o["contact_exact"] = contact_forces_exact(m, U[:, :3], Tnod, pc, SMAT)
        # ---- member stresses
        for part, nodes, dist in (("TC-01", n01, d_hole), ("TC-02", n02, d_tap)):
            s = vm(S[nodes])
            Tp = part_T(nodes, part)
            Fty = np.array([tab("AL6061-T6", "Fty", t) for t in Tp])
            Ftu = np.array([tab("AL6061-T6", "Ftu", t) for t in Tp])
            dd_ = dist[nodes]
            rec = {}
            for nm, msk in (("all", np.ones(len(nodes), bool)), ("band", dd_ > 1.0)):
                if not msk.any():
                    continue
                j = np.argmax(np.where(msk, s, -1))
                ju = np.argmin(np.where(msk, Fty / np.maximum(s, 1e-9), np.inf))
                rec[nm] = {"vm_max_MPa": round(float(s[j]), 1), "node": int(nodes[j]) + 1, "X_mm": X[nodes[j]].round(3).tolist(),
                           "x_prime": round(float(xa[nodes[j]]), 3), "r_global": round(float(r_g[nodes[j]]), 3),
                           "dist_hole_or_tap_mm": round(float(dd_[j]), 3), "T_C": round(float(Tp[j]), 1),
                           "Fty_MPa": round(float(Fty[j]), 1), "Ftu_MPa": round(float(Ftu[j]), 1),
                           "MS_y_SF1": round(float(Fty[ju] / max(s[ju], 1e-9) - 1), 3),
                           "MS_u_SF1": round(float(np.min(np.where(msk, Ftu / np.maximum(s, 1e-9), np.inf)) - 1), 3)}
                msf = o["case_rule"]["member_SF"]
                rec[nm]["MS_y_case"] = round(float(np.min(np.where(msk, Fty / (msf[0] * np.maximum(s, 1e-9)), np.inf)) - 1), 3)
                rec[nm]["MS_u_case"] = round(float(np.min(np.where(msk, Ftu / (msf[1] * np.maximum(s, 1e-9)), np.inf)) - 1), 3)
                if nm == "all" and kind in ("FA1", "FE-factored"):
                    rec[nm]["neuber"] = neuber_check(float(s[j]), float(Tp[j]))
            o[part] = rec
        # ---- SCLs (TC-01 in its shifted frame; TC-02 at the screw azimuth)
        zc1 = JS.Z_SCREW - shift
        def P01(xp, yp, zp):
            return np.array([0, 0, zc1]) + xp * JD.EN + yp * JD.ET1 + np.array([0, 0, zp])
        scl = {}
        off = JS.GEO["hole_r"] + 0.05
        # net ligament: through-wall (along n) at the hole-axis height, at the hole flank (y' = 2.80) and mid-ligament (az 0 plane)
        for nm, ypp in (("TC01_net_ligament_hole_flank", off), ("TC01_net_ligament_hole_flank_-t1", -off)):
            a = P01(JS.R_BORE01 + 0.002, ypp, 0.0)
            b = P01(JS.R_OD - 0.002, ypp, 0.0)
            # keep the line radial (through the wall): project on the global radius at the same azimuth
            scl[nm] = linearise(locs["TC-01"], S, *radial_line(a, b, zc1))
        a0 = np.array([JS.R_BORE01 + 0.002, 0.0, zc1])
        b0 = np.array([JS.R_OD - 0.002, 0.0, zc1])
        scl["TC01_net_ligament_mid_az0"] = linearise(locs["TC-01"], S, a0, b0)
        a36 = np.array([(JS.R_BORE01 + 0.002) * JD.C36, (JS.R_BORE01 + 0.002) * JD.S36, zc1])
        b36 = np.array([(JS.R_OD - 0.002) * JD.C36, (JS.R_OD - 0.002) * JD.S36, zc1])
        scl["TC01_net_ligament_mid_az36"] = linearise(locs["TC-01"], S, a36, b36)
        # shear-out path: through-wall at the hole flank, half way between the hole top (z_c + 2.75) and the case end (139.513 - shift)
        z_so = 0.5 * ((zc1 + JS.GEO["hole_r"]) + (139.513426 - shift))
        for nm, ypp in (("TC01_shear_out_flank+", off), ("TC01_shear_out_flank-", -off)):
            a = P01(JS.R_BORE01 + 0.002, ypp, z_so - zc1)
            b = P01(JS.R_OD - 0.002, ypp, z_so - zc1)
            scl[nm] = linearise(locs["TC-01"], S, *radial_line(a, b, zc1))
            scl[nm]["z"] = round(float(z_so), 3)
        # TC-02: shear-out path from the tap's aft wall (z_screw - 2.5) down to the gland-2 upper flank (z 119.213), at x' 28.0 and 26.5
        for xp in (28.0, 26.5, 24.0):
            a = JD.C0 + xp * JD.EN + np.array([0, 0, -JS.GEO["shank_r"] - 0.002])
            b = np.array([a[0], a[1], 119.2134 + 0.002])
            scl[f"TC02_shear_out_to_g2_x{xp}"] = linearise(locs["TC-02"], S, a, b)
        # TC-02 net ligament at the tap row: hoop line at r 27.5 from the tap flank to the az 0 plane and to the az 36 plane
        for nm, az_end in (("TC02_net_ligament_r27.5_to_az0", 0.0), ("TC02_net_ligament_r27.5_to_az36", JS.SECTOR)):
            r0 = 27.5
            dth = math.degrees((JS.GEO["shank_r"] + 0.05) / r0)
            az0 = JS.AZ_SCREW - dth if az_end == 0.0 else JS.AZ_SCREW + dth
            az1 = az_end + (0.3 if az_end == 0.0 else -0.3)
            a = np.array([r0 * math.cos(math.radians(az0)), r0 * math.sin(math.radians(az0)), JS.Z_SCREW])
            b = np.array([r0 * math.cos(math.radians(az1)), r0 * math.sin(math.radians(az1)), JS.Z_SCREW])
            scl[nm] = linearise(locs["TC-02"], S, a, b)
        o["SCL"] = scl
        # ---- contact blocks (if any): pressure / slip summary per slave set
        o["frd_blocks"] = sorted(F.keys())
        res["steps"][st] = o
    if upto is not None:
        res["partial_upto_ccx_step"] = int(upto)
    (wd / ("post.json" if upto is None else "post_partial.json")).write_text(json.dumps(res, indent=1, default=float))
    return res


def radial_line(a, b, zc1=None):
    """through-wall line in the global radial direction through the mid-point azimuth of a -> b; ends on the outer surface (OD, or the
    spot-face flat at x' = x_seat when the line crosses it: JS.r_out; zc1 = the TC-01 hole-axis z, default Z_SCREW - 0.24)."""
    mid = 0.5 * (a + b)
    az = math.atan2(mid[1], mid[0])
    er = np.array([math.cos(az), math.sin(az), 0.0])
    zc1 = JS.Z_SCREW - 0.24 if zc1 is None else zc1
    ra_, rb_ = JS.R_BORE01 + 0.002, JS.r_out(az - math.radians(JS.AZ_SCREW), float(mid[2]) - zc1)
    return np.array([ra_ * er[0], ra_ * er[1], mid[2]]), np.array([rb_ * er[0], rb_ * er[1], mid[2]])


if __name__ == "__main__":
    r = post(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
    for st, o in r["steps"].items():
        print(st, json.dumps({k: o[k] for k in ("screw", "TC-01", "TC-02") if k in o})[:900])
