"""Land-A closure superposition check, no solve (lead ~10:15Z (2); fea3d 2026-10-20 ~10:35Z).

GVHI (drawing-minimum J1 fit, 0.040 mm radial) closes the TC-01 / TC-02 fit at land A (S-AX z 103.513-106.513) from B1_8 to B1_19
(fit_dT_sax_v352.json 93d87757edbcdcaf, rev-3 S-AX thermal fields); interference <= 0.0084 mm; Lame (two long cylinders, E 66 GPa,
r 28.6 / r_o 31.75 / r_i 24.95, sum of factors 16.976): p 1.139 MPa, TC-01 bore hoop +10.9 MPa, TC-02 OD hoop -8.4 MPa.
The S-AX models of Mechanical release the TC-01 / TC-02 pair (no contact), so the closure stress is absent from them and is added here.

Cells (Mechanical's S-AX GVHI fields, rev 4 cad352r4 eh0p1 = current; rev 3 cad352 = the fields behind the closure dT, cross-check):
  TC-01 land A: bore surface nodes (r = bore over z 103.513-106.513) and the wall r bore..31.75 over the land; SCL through the wall at
  z 103.763 / 105.013 / 106.263.  TC-02 land A: spigot OD surface nodes (r 28.6) and the wall r_i..28.6; SCL at z 103.763 / 105.013
  (24.95 -> 28.6) and 106.263 (24.076 -> 28.6).
Cases: LC1 (asked; Pc 25 bar + manifold 70 bar + 3.65 g, SF 1.5 / 2.0), LC2 (MEOP 45 bar, information) and BN (blocked 63.08 bar,
SF 1.0, information), states B1_8 / B1_12 / B1_16 / B1_19.
Criteria (= sax.py evaluate, Mechanical, hub sax_r4/sax.py): node MS_y = Fty(T)/(SF_y vM_total) - 1, MS_u = Ftu(T)/(SF_u vM_total) - 1,
node primary = Fty(T)/(SF_y vM_mech) - 1, node P+Q = 2 Fty(T)/vM_total - 1; SCL Pm and Pm+Pb (mechanical) vs Fty(T_max,line)/SF_y,
P+Q Pm+Pb (total) vs 2 Fty.  Closure stress = SECONDARY (thermal interference, displacement-controlled): it enters the total and P+Q
rows; the primary rows are unchanged (also reported with the closure added as if primary, information).
Superpositions:
  L   lead's specification: TC-01 +10.9 hoop, TC-02 -8.4 hoop, -1.1 radial on both, uniform over the cell
  LE  exact Lame distribution at the state's own interference (delta = r alpha dT_max - 0.040 on that run's T field; p = delta E/(r 16.976))
  B   band-load envelope (information): land A is 3.0 mm long, shorter than the shell decay length (1/beta 7.6 mm TC-01, 7.7 mm TC-02), and
      sits at the free end of the TC-02 spigot, so the long-cylinder Lame is not an upper bound on every component: beam-on-elastic-
      foundation hand model (TC-01 infinite cylinder under a 3 mm band, TC-02 semi-infinite with the band at its free end): P 8.6 N/mm,
      p_avg 2.9 MPa (x2 edge peak -> 5.7), TC-01 hoop 5.6 (Lame 10.9 kept), axial bending +-8.2 MPa; TC-02 hoop -14.6 - nu 9.0 = -17.6,
      axial bending +-9.0 MPa (moment peak in the gland-1 tube section).  Both signs of the bending are evaluated, worst kept.
Evidence: SIM (Mechanical S-AX fields) + DERIVED (combination, cells, superposition, hand bounds); not physical approval.
usage: landA_closure_gvhi.py -> results/v352/landA_closure_gvhi_v352.json"""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np
import matplotlib.tri as mtri
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/snap/engmat_v1p6")
import engmat  # noqa: E402

RUNS = Path("/home/claude/work/mechanical/runs/structural")
RUN = {"rev4": RUNS / "L1_thv352_NF2b_R4_GVHI_r10free_cad352r4_eh0p1", "rev3": RUNS / "L1_thv352_NF2b_GVHI_r10free_cad352"}
SAXPY = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/sax_r4/sax.py")
FITDT = Path("/home/claude/work/fea3d/results/v352/fit_dT_sax_v352.json")
OUT = Path("/home/claude/work/fea3d/results/v352/landA_closure_gvhi_v352.json")
STATES = ["B1_8", "B1_12", "B1_16", "B1_19"]
Z0, Z1 = 103.513, 106.513
G_FL = 35.8 / 9.80665
CASES = {"LC1": ({"OP": 2.5, "PM": 7.0, "G": G_FL}, 1.5, 2.0), "LC2": ({"OP": 4.5, "PM": 7.0, "G": G_FL}, 1.5, 2.0),
         "BN": ({"BL": 6.308, "PM": 7.0}, 1.0, None)}
E_L, R_IF, R_O, R_I, ALPHA, GAP = 66000.0, 28.6, 31.75, 24.95, 23.6e-6, 0.040
FSUM = ((R_O**2 + R_IF**2) / (R_O**2 - R_IF**2) + 0.33) + ((R_IF**2 + R_I**2) / (R_IF**2 - R_I**2) - 0.33)
EDGE = {1: (0, 1, 3), 2: (1, 2, 4), 3: (2, 0, 5)}
MAT = engmat.MATERIALS["AL6061-T6"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def allow(T_K):
    TC = np.asarray(T_K, float) - 273.15
    f = lambda k: np.interp(TC, MAT[k]["T_C"], MAT[k]["v"]) / 1e6
    return f("Fty"), f("Ftu")


def vm(S):
    a, b, c, d = S[..., 0], S[..., 1], S[..., 2], S[..., 3]
    return np.sqrt(0.5 * ((a - b) ** 2 + (b - c) ** 2 + (c - a) ** 2) + 3.0 * d ** 2)


def singular_points(X, E, pn, eqs):
    """copy of sax.singular_points (re-entrant corners > 10 deg, ends of tied runs)."""
    tied = set(int(v) for a in eqs for v in a.ravel())
    pts = []
    for p in np.unique(pn):
        idx = np.nonzero(pn == p)[0]
        cnt = {}
        for e in idx:
            for f, (i, j, k) in EDGE.items():
                key = (min(E[e, i], E[e, j]), max(E[e, i], E[e, j]))
                cnt.setdefault(key, []).append((e, i, j))
        nb = {}
        for key, lst in cnt.items():
            if len(lst) == 1:
                e, i, j = lst[0]
                a_, b_ = int(E[e, i]), int(E[e, j])
                nb.setdefault(a_, [None, None])[1] = b_
                nb.setdefault(b_, [None, None])[0] = a_
        for n, (pa, pb) in nb.items():
            if pa is None or pb is None:
                continue
            u, w = X[n] - X[pa], X[pb] - X[n]
            ang = math.degrees(math.atan2(u[0] * w[1] - u[1] * w[0], u @ w))
            if ang < -10.0 or (n in tied and ((pa not in tied) or (pb not in tied))):
                pts.append(X[n])
    return np.array(pts) if pts else np.zeros((0, 2))


def line_weights(X, E, pn, part, p0, p1, n=41):
    """copy of sax.line_weights."""
    Ep = E[pn == part]
    sub = np.vstack([Ep[:, [0, 3, 5]], Ep[:, [3, 1, 4]], Ep[:, [5, 4, 2]], Ep[:, [3, 4, 5]]])
    used = np.unique(sub)
    rm = -np.ones(len(X), np.int64)
    rm[used] = np.arange(len(used))
    tri = mtri.Triangulation(X[used, 0], X[used, 1], rm[sub])
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    s = np.linspace(0.0, 1.0, n)
    P = p0 + s[:, None] * (p1 - p0)
    P[0] = p0 + 0.005 * (p1 - p0)
    P[-1] = p1 - 0.005 * (p1 - p0)
    it = tri.get_trifinder()(P[:, 0], P[:, 1])
    rows, cols, vals = [], [], []
    for q in np.nonzero(it >= 0)[0]:
        t3 = sub[it[q]]
        A = X[t3]
        T = np.array([[A[0, 0] - A[2, 0], A[1, 0] - A[2, 0]], [A[0, 1] - A[2, 1], A[1, 1] - A[2, 1]]])
        l1, l2 = np.linalg.solve(T, P[q] - A[2])
        rows += [q] * 3
        cols += [int(c) for c in t3]
        vals += [l1, l2, 1.0 - l1 - l2]
    W = csr_matrix((vals, (rows, cols)), shape=(n, len(X)))
    return {"W": W, "s": s, "ok": it >= 0, "L": float(np.linalg.norm(p1 - p0)), "P": P, "p0": p0.tolist(), "p1": p1.tolist()}


def _longest_run(ok):
    best, cur, bs, s0 = 0, 0, 0, 0
    for i, v in enumerate(ok):
        if v:
            if cur == 0:
                s0 = i
            cur += 1
            if cur > best:
                best, bs = cur, s0
        else:
            cur = 0
    m = np.zeros(len(ok), bool)
    m[bs:bs + best] = True
    return m


def linearise(lw, S, T):
    """copy of sax.linearise_w (straight SCL, no radius correction)."""
    ok = _longest_run(lw["ok"])
    if ok.sum() < 5:
        return None
    v = (lw["W"] @ np.column_stack([S[:, :4], T]))[ok]
    xm = lw["s"][ok] * lw["L"]
    xm = xm - xm[0]
    t = xm[-1]
    mem = np.trapezoid(v[:, :4], xm, axis=0) / t
    ben = 6.0 / t ** 2 * np.trapezoid(v[:, :4] * (t / 2 - xm)[:, None], xm, axis=0)
    ben[3] = 0.0
    return {"Pm_vm": float(vm(mem)), "PmPb_vm": max(float(vm(mem + ben)), float(vm(mem - ben))), "T_max_K": float(v[:, 4].max()),
            "valid_points": int(ok.sum()), "membrane": [round(float(x), 2) for x in mem], "bending": [round(float(x), 2) for x in ben]}


def lame(r, part, p):
    """closure stresses (rr, tt) at radius r for interface pressure p: TC-01 internal (a 28.6, b 31.75), TC-02 external (a 24.95, b 28.6)."""
    r = np.asarray(r, float)
    if part == "ENG-TC-01":
        a, b = R_IF, R_O
        c = p * a * a / (b * b - a * a)
        return c * (1 - b * b / r ** 2), c * (1 + b * b / r ** 2)
    a, b = R_I, R_IF
    c = -p * b * b / (b * b - a * a)
    return c * (1 - a * a / r ** 2), c * (1 + a * a / r ** 2)


class Run:
    def __init__(self, key):
        self.key, self.d = key, RUN[key]
        m = np.load(self.d / "mesh.npz", allow_pickle=True)
        self.X, self.E, self.pn = m["X"], m["E"], m["pn"]
        self.mesh_sha = sha16(self.d / "mesh.npz")
        self.sp = singular_points(self.X, self.E, self.pn, [m["eq1"], m["eq2"]])
        self.dsp = cKDTree(self.sp).query(self.X)[0] if len(self.sp) else np.full(len(self.X), np.inf)
        self.part_nodes = {p: np.unique(self.E[self.pn == p]) for p in ("ENG-TC-01", "ENG-TC-02")}

    def res(self, st):
        f = self.d / st / "res.npz"
        sub = not f.exists()
        if sub:
            f = self.d / st / "res_sub.npz"
        z = np.load(f, allow_pickle=True)
        N = len(self.X)
        out = {"file": str(f), "sha16": sha16(f)}
        idx = z["nodes"] if sub else np.arange(N)
        for k in z.files:
            if k in ("nodes", "meta"):
                continue
            a = z[k].astype(float)
            full = np.full((N,) + a.shape[1:], np.nan)
            full[idx] = a
            out[k] = full
        return out


def cells(run):
    X = run.X
    c = {}
    n1 = run.part_nodes["ENG-TC-01"]
    k1 = n1[(X[n1, 1] >= Z0 - 1e-3) & (X[n1, 1] <= Z1 + 1e-3) & (X[n1, 0] > 28.0) & (X[n1, 0] < 31.76)]
    rb = X[k1, 0].min()
    c["TC01_bore_landA"] = ("ENG-TC-01", k1[X[k1, 0] < rb + 0.03])          # interface nodes (rev 3: land ends at 28.625, interior 28.6)
    c["TC01_wall_landA"] = ("ENG-TC-01", k1)
    n2 = run.part_nodes["ENG-TC-02"]
    k2 = n2[(X[n2, 1] >= Z0 - 1e-3) & (X[n2, 1] <= Z1 + 1e-3) & (X[n2, 0] > 23.5)]
    ro = X[k2, 0].max()
    c["TC02_spigotOD_landA"] = ("ENG-TC-02", k2[X[k2, 0] > ro - 0.03])
    c["TC02_wall_landA"] = ("ENG-TC-02", k2)
    return c, float(rb), float(ro)


def scl_lines(rb):
    return {"TC01_wall_z103.763": ("ENG-TC-01", (rb, 103.763), (R_O, 103.763)),
            "TC01_wall_z105.013": ("ENG-TC-01", (rb, 105.013), (R_O, 105.013)),
            "TC01_wall_z106.263": ("ENG-TC-01", (rb, 106.263), (R_O, 106.263)),
            "TC02_wall_z103.763": ("ENG-TC-02", (R_I, 103.763), (R_IF, 103.763)),
            "TC02_wall_z105.013": ("ENG-TC-02", (R_I, 105.013), (R_IF, 105.013)),
            "TC02_wall_z106.263": ("ENG-TC-02", (24.076, 106.263), (R_IF, 106.263))}


def dT_land(run, T):
    """plug OD (r 28.6, TC-02) minus bore (r 28.625, TC-01) over land A, as fit_dT_sax (linear sub-triangles, nearest outside)."""
    z = np.arange(103.5135, 106.5135 + 1e-9, 0.05)
    vals = {}
    for p, r in (("ENG-TC-02", 28.6), ("ENG-TC-01", 28.625)):
        Ep = run.E[run.pn == p]
        used = np.unique(Ep)
        rm = -np.ones(len(run.X), np.int64)
        rm[used] = np.arange(len(used))
        sub = rm[np.vstack([Ep[:, [0, 3, 5]], Ep[:, [3, 1, 4]], Ep[:, [5, 4, 2]], Ep[:, [3, 4, 5]]])]
        Xu = run.X[used]
        tri = mtri.Triangulation(Xu[:, 0], Xu[:, 1], sub)
        Tu = T[used]
        v = mtri.LinearTriInterpolator(tri, np.nan_to_num(Tu, nan=-1e9))(np.full(len(z), r), z)
        v = np.asarray(v.filled(np.nan) if hasattr(v, "filled") else v, float)
        bad = ~np.isfinite(v) | (v < 0)
        if bad.any():
            ok = np.isfinite(Tu)
            kd = cKDTree(Xu[ok])
            _, ii = kd.query(np.column_stack([np.full(bad.sum(), r), z[bad]]))
            v[bad] = Tu[ok][ii]
        vals[p] = v
    dT = vals["ENG-TC-02"] - vals["ENG-TC-01"]
    k = int(np.argmax(dT))
    return {"dT_max_K": round(float(dT[k]), 2), "z_mm": round(float(z[k]), 3), "dT_mean_K": round(float(dT.mean()), 2)}


def node_ms(S, Sm, T, nodes, sfy, sfu):
    fy, fu = allow(T[nodes])
    v, vmm = vm(S[nodes]), vm(Sm[nodes])
    return {"y": fy / (sfy * np.maximum(v, 1e-9)) - 1, "u": (fu / (sfu * np.maximum(v, 1e-9)) - 1) if sfu else None,
            "p": fy / (sfy * np.maximum(vmm, 1e-9)) - 1, "pq": 2 * fy / np.maximum(v, 1e-9) - 1, "vm": v, "vm_mech": vmm}


def cell_rows(run, S, Sm, T, nodes, sfy, sfu, reg_r=1.0):
    ms = node_ms(S, Sm, T, nodes, sfy, sfu)
    X = run.X
    out = {}
    for tag, msk in (("all", np.ones(len(nodes), bool)), ("regular", run.dsp[nodes] > reg_r)):
        if not msk.any():
            continue
        o = {}
        for crit in ("y", "u", "p", "pq"):
            if ms[crit] is None:
                continue
            a = np.where(msk, ms[crit], np.inf)
            i = int(np.argmin(a))
            n = int(nodes[i])
            o[crit] = {"MS": round(float(a[i]), 4), "node_index": n, "r_z_mm": [round(float(X[n, 0]), 3), round(float(X[n, 1]), 3)],
                       "vm_MPa": round(float(ms["vm"][i]), 2), "vm_mech_MPa": round(float(ms["vm_mech"][i]), 2),
                       "T_C": round(float(T[n] - 273.15), 1), "S_rr_zz_tt_rz": [round(float(x), 2) for x in S[n, :4]],
                       "dist_singular_mm": round(float(run.dsp[n]), 3)}
        out[tag] = o
    return out


def superpose(S, X, nodes_by_part, mode, p_state, sgn=(1, 1)):
    S2 = S.copy()
    for part, nodes in nodes_by_part.items():
        r = X[nodes, 0]
        if mode == "L":
            drr = np.full(len(nodes), -1.1)
            dtt = np.full(len(nodes), 10.9 if part == "ENG-TC-01" else -8.4)
            dzz = np.zeros(len(nodes))
        elif mode == "LE":
            drr, dtt = lame(r, part, p_state)
            dzz = np.zeros(len(nodes))
        else:  # band-load envelope (information)
            drr = np.full(len(nodes), -5.7)
            if part == "ENG-TC-01":
                dtt, dzz = np.full(len(nodes), 10.9), np.full(len(nodes), 8.2 * sgn[0])
            else:
                dtt, dzz = np.full(len(nodes), -17.6), np.full(len(nodes), 9.0 * sgn[1])
        S2[nodes, 0] += drr
        S2[nodes, 2] += dtt
        S2[nodes, 1] += dzz
    return S2


def main():
    fit = json.loads(FITDT.read_text())
    out = {"id": "landA_closure_gvhi_v352", "date": "2026-10-20", "owner": "fea3d", "doc": __doc__.split("\n")[0],
           "basis": {"lead": "~10:15Z (2): land-A cells, GVHI B1_8..B1_19, superpose +10.9 hoop TC-01, -8.4 hoop TC-02, p 1.1 radial",
                     "fit_dT_sax_v352_sha16": sha16(FITDT), "sax_py_sha16": sha16(SAXPY), "lame_sum_of_factors": round(FSUM, 3),
                     "E_MPa": E_L, "alpha_per_K": ALPHA, "cold_gap_GVHI_mm": GAP,
                     "criteria": "sax.py evaluate: node MS_y Fty(T)/(SF_y vM) - 1, MS_u Ftu(T)/(SF_u vM) - 1, primary Fty/(SF_y vM_mech) - 1, "
                                 "P+Q 2 Fty/vM - 1; SCL Pm / Pm+Pb (mech) vs Fty(T_max)/SF_y, P+Q Pm+Pb (total) vs 2 Fty",
                     "classification": "closure = SECONDARY (thermal interference): total and P+Q rows; primary rows unchanged",
                     "evidence": "SIM (Mechanical S-AX GVHI fields) + DERIVED (combination, superposition); band bound DERIVED hand model"},
           "runs": {}}
    for key in ("rev4", "rev3"):
        run = Run(key)
        cs, rb, ro = cells(run)
        lines = {nm: (pt, line_weights(run.X, run.E, run.pn, pt, a, b)) for nm, (pt, a, b) in scl_lines(rb).items()}
        ro_ = {"dir": str(run.d), "mesh_sha16": run.mesh_sha, "singular_points": int(len(run.sp)), "bore_r_landA_mm": rb,
               "spigot_OD_r_landA_mm": ro, "cells_n_nodes": {k: int(len(v[1])) for k, v in cs.items()}, "states": {}}
        for st in STATES:
            R = run.res(st)
            T = R["T"]
            dT = dT_land(run, T)
            delta = R_IF * ALPHA * dT["dT_max_K"] - GAP
            p_st = max(delta, 0.0) * E_L / (R_IF * FSUM)
            so = {"res": R["file"], "res_sha16": R["sha16"], "landA_dT": dT, "interference_mm": round(delta, 5),
                  "p_lame_MPa": round(p_st, 3), "closes": bool(delta > 0), "cases": {}}
            if key == "rev3":
                fr = fit["fields"].get("v352_NF2b_GVHI", {}).get("states", {}).get(st, {})
                so["fit_dT_sax_record"] = {k: fr.get(k) for k in ("dT_max_K", "z_at_max_mm", "closure_left_mm_at_max")}
            for cid, (co, sfy, sfu) in CASES.items():
                Sm = np.zeros_like(R["S1"])
                for k_, c_ in co.items():
                    Sm = Sm + c_ * R[f"S_{k_}"]
                S = R["S1"] + Sm
                co_out = {"SF_y": sfy, "SF_u": sfu, "coefficients": co}
                byp = {"ENG-TC-01": cs["TC01_wall_landA"][1], "ENG-TC-02": cs["TC02_wall_landA"][1]}
                variants = {"base": [S]}
                variants["L"] = [superpose(S, run.X, byp, "L", p_st)]
                variants["LE"] = [superpose(S, run.X, byp, "LE", p_st)]
                variants["B"] = [superpose(S, run.X, byp, "B", p_st, sg) for sg in ((1, 1), (1, -1), (-1, 1), (-1, -1))]
                for cname, (part, nodes) in cs.items():
                    cc = {}
                    for vn, Ss in variants.items():
                        best = None
                        for S2 in Ss:
                            rows = cell_rows(run, S2, Sm, T, nodes, sfy, sfu)
                            if best is None:
                                best = rows
                            else:
                                for tag in rows:
                                    for crit in rows[tag]:
                                        if rows[tag][crit]["MS"] < best[tag][crit]["MS"]:
                                            best[tag][crit] = rows[tag][crit]
                        cc[vn] = best
                    co_out[cname] = cc
                scl = {}
                for nm, (pt, lw) in lines.items():
                    sv = {}
                    for vn, Ss in variants.items():
                        worst = None
                        for S2 in Ss:
                            lc, lp = linearise(lw, S2, T), linearise(lw, Sm, T)
                            if lc is None or lp is None:
                                continue
                            fy, fu = allow(np.array([lc["T_max_K"]]))
                            fy, fu = float(fy[0]), float(fu[0])
                            row = {"T_max_C": round(lc["T_max_K"] - 273.15, 1), "Fty_MPa": round(fy, 1), "Pm_vm": round(lp["Pm_vm"], 2),
                                   "PmPb_vm": round(lp["PmPb_vm"], 2), "PQ_PmPb_vm": round(lc["PmPb_vm"], 2),
                                   "MS_Pm_y": round(fy / (sfy * max(lp["Pm_vm"], 1e-9)) - 1, 3),
                                   "MS_PmPb_y": round(fy / (sfy * max(lp["PmPb_vm"], 1e-9)) - 1, 3),
                                   "MS_PQ_shakedown": round(2 * fy / max(lc["PmPb_vm"], 1e-9) - 1, 3),
                                   "MS_combined_PmPb_y": round(fy / (sfy * max(lc["PmPb_vm"], 1e-9)) - 1, 3),
                                   "valid_points": lc["valid_points"], "membrane_total": lc["membrane"], "bending_total": lc["bending"]}
                            if vn != "base":
                                # closure treated as primary (information): Pm / Pm+Pb of mechanical + closure
                                Smc = Sm + (S2 - S)
                                lpc = linearise(lw, Smc, T)
                                row["MS_PmPb_y_if_closure_primary"] = round(fy / (sfy * max(lpc["PmPb_vm"], 1e-9)) - 1, 3)
                                row["MS_Pm_y_if_closure_primary"] = round(fy / (sfy * max(lpc["Pm_vm"], 1e-9)) - 1, 3)
                            if worst is None or row["MS_PQ_shakedown"] < worst["MS_PQ_shakedown"]:
                                worst = row
                        sv[vn] = worst
                    scl[nm] = sv
                co_out["SCL"] = scl
                so["cases"][cid] = co_out
            ro_["states"][st] = so
        out["runs"][key] = ro_
    # verification: reproduce Mechanical's published LC1 TC-02 regular row at B1_12 (rev 4)
    J = json.loads((Path("/home/claude/work/shared-fallback/engine/04-fea/v352/sax_r4") /
                    "sax_results_L1_thv352_NF2b_R4_GVHI_r10free_cad352r4_eh0p1_v1.json").read_text())
    run = Run("rev4")
    ver = []
    for row in J["rows"]:
        if row["case"] in ("LC1", "LC2", "BN") and row["state"] in STATES and row["part"] == "ENG-TC-02" and row["set"] == "regular":
            R = run.res(row["state"])
            co, sfy, sfu = CASES[row["case"]]
            Sm = sum(c_ * R[f"S_{k_}"] for k_, c_ in co.items())
            S = R["S1"] + Sm
            n2 = run.part_nodes["ENG-TC-02"]
            n = n2[np.argmin(np.hypot(run.X[n2, 0] - row["at_r_z_mm"][0], run.X[n2, 1] - row["at_r_z_mm"][1]))]
            ver.append({"case": row["case"], "state": row["state"], "at": row["at_r_z_mm"], "vm_published": round(row["vm_MPa"], 3),
                        "vm_here": round(float(vm(S[n])), 3), "MS_published": round(row["MS"], 4),
                        "MS_here": round(float(allow(T_K=R["T"][n])[0] / (sfy * vm(S[n])) - 1), 4)})
    out["verification_vs_published_rows"] = ver
    OUT.write_text(json.dumps(out, indent=1))
    # ---- print summary
    for key, ro_ in out["runs"].items():
        print(f"== {key} {Path(ro_['dir']).name} bore r {ro_['bore_r_landA_mm']} OD r {ro_['spigot_OD_r_landA_mm']} cells {ro_['cells_n_nodes']}")
        for st, so in ro_["states"].items():
            print(f"  {st}: dT {so['landA_dT']} delta {so['interference_mm']} p_Lame {so['p_lame_MPa']} {so.get('fit_dT_sax_record','')}")
            for cid, co_out in so["cases"].items():
                for cname in ("TC01_bore_landA", "TC01_wall_landA", "TC02_spigotOD_landA", "TC02_wall_landA"):
                    cc = co_out[cname]
                    s = []
                    for vn in ("base", "L", "LE", "B"):
                        a = cc[vn]["all"]
                        s.append(f"{vn}: y {a['y']['MS']:+.3f} pq {a['pq']['MS']:+.3f} p {a['p']['MS']:+.3f}")
                    print(f"    {cid} {cname:20s} all-node | " + " | ".join(s))
                for nm, sv in co_out["SCL"].items():
                    s = [f"{vn}: Pm {sv[vn]['MS_Pm_y']:+.3f} PmPb {sv[vn]['MS_PmPb_y']:+.3f} PQ {sv[vn]['MS_PQ_shakedown']:+.3f}" for vn in ("base", "L", "LE", "B") if sv.get(vn)]
                    print(f"    {cid} SCL {nm:20s} | " + " | ".join(s))
    print("verification", json.dumps(out["verification_vs_published_rows"])[:1500])
    print("wrote", OUT, sha16(OUT))


if __name__ == "__main__":
    main()
