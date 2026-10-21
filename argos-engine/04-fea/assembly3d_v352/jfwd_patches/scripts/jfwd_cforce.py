"""J-FWD sub-model: exact contact / constraint forces from the solved displacements (fea3d 2026-10-20 diagnostic).
Nodal internal forces f = sum_e int B^T sigma dV with sigma = D(E(T), nu) (B u - alpha (T - T0) I), C3D10 4-point rule, per body; at a
contact-surface node with no other load f equals the contact force on that body.  Sums over the HEAD / BEAR / FIT node sets
(both sides), the scalar normal-force total (f . e_r(az) for FIT, f . n for HEAD) and the vector sum.  Uniform step temperatures only
(PRELOAD, SOAK, FA1*, LC2U/Y/N; mapped steps use the deck's per-node temperatures if given).
usage: jfwd_cforce.py JOB STEP_NAME [STEP_NAME ...]"""
import sys, json, math
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_deck as JD   # noqa: E402
import jfwd_post as JP   # noqa: E402
import jfwd_sub as JS    # noqa: E402

GP = np.array([[0.1381966011250105, 0.1381966011250105, 0.1381966011250105], [0.5854101966249685, 0.1381966011250105, 0.1381966011250105],
               [0.1381966011250105, 0.5854101966249685, 0.1381966011250105], [0.1381966011250105, 0.1381966011250105, 0.5854101966249685]])
W = np.full(4, 1.0 / 24.0)


def dN(xi, eta, zeta):
    """derivatives of the CCX C3D10 shape functions wrt (xi, eta, zeta): (10, 3)."""
    L1 = 1 - xi - eta - zeta
    L = [L1, xi, eta, zeta]
    dL = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    d = np.zeros((10, 3))
    for i in range(4):
        d[i] = (4 * L[i] - 1) * dL[i]
    pairs = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
    for k, (a, b) in enumerate(pairs):
        d[4 + k] = 4 * (L[a] * dL[b] + L[b] * dL[a])
    return d


def tab(rows, T):
    rows = np.asarray(rows)
    return np.interp(T, rows[:, -1], rows[:, 0])


def body_forces(X, T, U, temp, E_rows, nu, a_rows, T0=293.15):
    """nodal internal forces of the elements T (n, 10) with nodal temperatures temp (K)."""
    f = np.zeros((len(X), 3))
    Xe, Ue, Te = X[T], U[T], temp[T]
    for g in range(4):
        d = dN(*GP[g])                                    # (10, 3)
        J = np.einsum("eia,ib->eab", Xe, d)               # dx_a / dxi_b
        Ji = np.linalg.inv(J)
        detJ = np.linalg.det(J)
        Dx = np.einsum("ib,eba->eia", d, Ji)              # dN_i / dx_a
        gradu = np.einsum("eik,eia->eka", Ue, Dx)         # du_k / dx_a
        eps = 0.5 * (gradu + np.transpose(gradu, (0, 2, 1)))
        L1 = 1 - GP[g].sum()
        Nn = np.array([L1 * (2 * L1 - 1)] + [GP[g][k] * (2 * GP[g][k] - 1) for k in range(3)] +
                      [4 * L1 * GP[g][0], 4 * GP[g][0] * GP[g][1], 4 * GP[g][1] * L1, 4 * L1 * GP[g][2], 4 * GP[g][0] * GP[g][2], 4 * GP[g][1] * GP[g][2]])
        Tg = Te @ Nn
        E = tab(E_rows, Tg)
        al = tab(a_rows, Tg)
        lam = E * nu / ((1 + nu) * (1 - 2 * nu))
        mu = E / (2 * (1 + nu))
        eth = al * (Tg - T0)
        tr = np.trace(eps, axis1=1, axis2=2) - 3 * eth
        sig = 2 * mu[:, None, None] * (eps - eth[:, None, None] * np.eye(3)) + (lam * tr)[:, None, None] * np.eye(3)
        fe = np.einsum("eia,eka->eik", Dx, sig) * (W[g] * detJ)[:, None, None]
        np.add.at(f, T.ravel(), fe.reshape(-1, 3))
    return f


def main(job, names):
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    m = dict(np.load(JD.OUT / f"model_{meta['mesh']}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
    chk = np.abs(X[T[:, 4]] - 0.5 * (X[T[:, 0]] + X[T[:, 1]])).max()
    steps = meta["steps"]
    want = [steps.index(n) + 1 for n in names]
    by = JP.read_frd_steps(wd / f"{job}.frd", len(X), max(want))
    mats = {"AL": ([[6.890e4, 293.15], [6.620e4, 373.15], [6.340e4, 423.15], [6.0e4, 473.15], [5.58e4, 523.15], [5.1e4, 573.15]], 0.33,
                   [[2.32e-5, 293.15], [2.36e-5, 373.15], [2.43e-5, 473.15], [2.52e-5, 573.15]]),
            "A480": ([[1.93e5, 293.15], [1.8721e5, 373.15], [1.7949e5, 473.15], [1.72735e5, 573.15], [1.6598e5, 673.15]], 0.29,
                     [[1.6e-5, 293.15], [1.6e-5, 373.15], [1.65e-5, 473.15], [1.7e-5, 573.15], [1.75e-5, 673.15]])}
    import jfwd_mat as JMAT                       # 11:55Z: screw material from the run meta (A480 default; IN718 for js5b)
    mats[JMAT.screw_mat(meta)] = JMAT.ROWS[JMAT.screw_mat(meta)]
    bm = {"TC-01": "AL", "TC-02": "AL", "SCREW": JMAT.screw_mat(meta)}
    az = np.degrees(np.arctan2(X[:, 1], X[:, 0]))
    er = np.stack([np.cos(np.radians(az)), np.sin(np.radians(az)), np.zeros(len(X))], 1)
    n_ax = JD.EN
    sets = {}
    for key in ("head_s", "head_m", "bear_s", "bear_m", "fit_s", "fit_m"):
        msk = m[key]
        sets[key] = np.unique(np.concatenate([m["fcn"][msk].ravel(), m["fmn"][msk].ravel()]))
    out = {"job": job, "midside_check_mm": float(chk), "steps": {}}
    for nm, k in zip(names, want):
        F = by[k]
        U = F["DISP"][:, :3]
        sd = meta["step_defs"].get(nm)
        Tn = np.full(len(X), 293.15)
        if nm not in ("SEAT", "PRELOAD") and sd is not None and isinstance(sd[1], dict):
            for b, tc in sd[1].items():
                el = T[B == b]
                Tn[np.unique(el)] = tc + 273.15
        elif nm not in ("SEAT", "PRELOAD"):
            print("non-uniform temperature step", nm, "- skipped")
            continue
        f = np.zeros((len(X), 3))
        for b in ("TC-01", "TC-02", "SCREW"):
            e, nu, a = mats[bm[b]]
            f += body_forces(X, T[B == b], U, Tn, e, nu, a)
        rec = {}
        for key, idx in sets.items():
            fv = f[idx].sum(0)
            rad = float((f[idx] * er[idx]).sum())
            axn = float(f[idx] @ n_ax).sum() if False else float((f[idx] @ n_ax).sum())
            rec[key] = {"n_nodes": int(len(idx)), "sum_vec_N": [round(float(v), 1) for v in fv], "sum_radial_local_N": round(rad, 1),
                        "sum_along_screw_axis_N": round(axn, 1)}
        out["steps"][nm] = rec
        print(nm, json.dumps(rec))
    (wd / "cforce.json").write_text(json.dumps(out, indent=1))
    print("midside check", chk)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
