"""REV-MECH-2 (independent reviewer): own re-derivation of the FEA3D FA-1 modal decomposition (criterion e; lead 223 (3)(b), OI-51).

Run modal_v351ca2b_c71 (all-L2, 60 modes, T_REF 293.15 K; FEA3D stored U_FREQ / U_OP / S_OP and modal.json, read-only).  Own code only:
  - unit-OP load vector F from the solved deck: *DLOAD face pressures on C3D10 faces integrated with the quadratic face shape functions
    (6-point Gauss, outward normal from the element), plus the step's *CLOAD nodal forces;  checks: resultant vs FEA3D's 202.92 N/MPa (L1);
  - modal participation p_i = phi_i . F (ccx eigenvectors are mass-normalised); static modal sum check against U_OP;
  - nodal stress probe: strain from the C3D10 shape-function gradients evaluated AT the node in every adjacent element of the body,
    isotropic elasticity at T_REF (E, nu from the deck), averaged; checked against ccx S_OP at the node;
  - shares c_i = f(sigma(phi_i)) p_i / omega_i^2 / f(sigma(U_OP)) for f = projection on the dominant principal direction of the static
    stress (as FEA3D) and the tensor projection; band sums at FE frequency scale 1.00 / 0.90 / 0.85; all 60 shares written out.
usage: python -I rm2_modal.py <out.json> [node ...]
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rm2_repost as RP  # noqa: E402

RUN, STATE = "modal_v351ca2b_c71", "B1_21.65"
ELAS = {"AL6061_T6": (68900.0, 0.33), "AL6061_T6_NX": (68900.0, 0.33), "AL7075_T6": (71700.0, 0.33), "AL7075_T6_NX": (71700.0, 0.33),
        "GLIDCOP_AL15": (130000.0, 0.33), "IN718": (200000.0, 0.29), "GRAPHITE_ISO": (9800.0, 0.15), "CARBON_PHENOLIC": (12000.0, 0.2),
        "FLEX_GRAPHITE_OI": (500.0, 0.05), "SS316L": (200000.0, 0.29)}   # deck *ELASTIC at 293.15 K (all nodes at 293.15 K in this run)
# C3D10 natural coordinates (L2, L3, L4) of the 10 nodes; L1 = 1 - sum
NAT = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, 0, 0], [.5, .5, 0], [0, .5, 0], [0, 0, .5], [.5, 0, .5], [0, .5, .5]], float)
EDGES = {4: (0, 1), 5: (1, 2), 6: (2, 0), 7: (0, 3), 8: (1, 3), 9: (2, 3)}


def dN_dnat(p):
    """derivatives of the 10 C3D10 shape functions w.r.t. (xi, eta, zeta) = (L2, L3, L4) at natural point p."""
    L = np.array([1 - p.sum(), p[0], p[1], p[2]])
    dL = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)    # dL_k / d(xi, eta, zeta)
    D = np.zeros((10, 3))
    for k in range(4):
        D[k] = (4 * L[k] - 1) * dL[k]
    for m, (a, b) in EDGES.items():
        D[m] = 4 * (L[a] * dL[b] + L[b] * dL[a])
    return D


def tri6_N(s, t):
    r = 1 - s - t
    N = np.array([r * (2 * r - 1), s * (2 * s - 1), t * (2 * t - 1), 4 * r * s, 4 * s * t, 4 * t * r])
    dNs = np.array([-(4 * r - 1), 4 * s - 1, 0, 4 * (r - s), 4 * t, -4 * t])
    dNt = np.array([-(4 * r - 1), 0, 4 * t - 1, -4 * s, 4 * s, 4 * (r - t)])
    return N, dNs, dNt


# 6-point Gauss rule on the triangle (degree 4)
_a, _b = 0.445948490915965, 0.091576213509771
_wa, _wb = 0.223381589678011 / 2, 0.109951743655322 / 2
GP = [(_a, _a, _wa), (1 - 2 * _a, _a, _wa), (_a, 1 - 2 * _a, _wa), (_b, _b, _wb), (1 - 2 * _b, _b, _wb), (_b, 1 - 2 * _b, _wb)]


def main(outp, probe_nodes):
    t0 = time.time()
    z, meta = RP.load_deck(RUN, STATE)
    X = np.zeros((int(z["nodes_id"].max()) + 2, 3))
    X[z["nodes_id"]] = z["nodes_x"]
    elem, ebody = {}, {}
    for es in meta["bodies"]:
        E = z[f"E_{es}"]
        for row in E:
            elem[int(row[0])] = row[1:]
            ebody[int(row[0])] = es
    # ---- unit OP load vector
    iop = [s["i"] for s in meta["steps"] if s["name"] == "OP"][0]
    DL = z[f"DL_{iop}"]
    F = np.zeros_like(X)
    for eid, face, p in DL:
        conn = elem[int(eid)]
        fl = RP.FACES[int(face) - 1]
        nodes = conn[list(fl)]
        P = X[nodes]
        cen_e = X[conn[:4]].mean(0)
        cen_f = P[:3].mean(0)
        for s_, t_, w in GP:
            N, dNs, dNt = tri6_N(s_, t_)
            n = np.cross(dNs @ P, dNt @ P)                   # area-scaled normal
            if n @ (cen_f - cen_e) < 0:
                n = -n
            F[nodes] += np.outer(N, -p * n * w)
    nfd = F.copy()
    if f"CL_{iop}" in z.files:
        for nd, dof, v in z[f"CL_{iop}"]:
            F[int(nd), int(dof) - 1] += v
    res = {"F_dload_sum_N_per_MPa": nfd.sum(0).tolist(), "F_total_sum_N_per_MPa": F.sum(0).tolist(),
           "n_dload": int(len(DL)), "n_cload": int(len(z[f"CL_{iop}"])) if f"CL_{iop}" in z.files else 0}
    # ---- fields
    Z = np.load(RP.RUNS / RUN / STATE / "fields.npz")
    Uf = Z["U_FREQ"].astype(np.float64)
    Uop = Z["U_OP"].astype(np.float64)
    Sop = Z["S_OP"].astype(np.float64)
    n1 = min(Uf.shape[1], len(X))
    md = json.loads((RP.RUNS / RUN / STATE / "modal.json").read_text())
    f = np.array([m["f_Hz"] for m in md["modes"]])[:Uf.shape[0]]
    om2 = (2 * math.pi * f) ** 2
    p = np.einsum("kij,ij->k", Uf[:, :n1], F[:n1])
    res["participation_top"] = sorted([[int(i + 1), float(f[i]), float(p[i])] for i in range(len(f))], key=lambda r: -abs(r[2]))[:8]
    Urec = np.einsum("k,kij->ij", p / om2, Uf[:, :n1])
    # displacement check: engine axial (z) displacement of the nozzle-exit region and overall norm
    res["U_modal_sum_vs_U_OP"] = {"rel_norm_err_all": float(np.linalg.norm(Urec - Uop[:n1]) / np.linalg.norm(Uop[:n1]))}
    # ---- stress probe
    def probe(nd, U):
        es_list = [eid for eid in node_elems.get(nd, [])]
        out = []
        for eid in es_list:
            conn = elem[eid]
            k = int(np.nonzero(conn == nd)[0][0])
            D = dN_dnat(NAT[k])
            J = X[conn].T @ D                       # 3x3: dx/dnat
            G = D @ np.linalg.inv(J)                # 10x3: dN/dx
            Ee, nu = ELAS[meta["sections"][ebody[eid]]]
            lam, mu = Ee * nu / ((1 + nu) * (1 - 2 * nu)), Ee / (2 * (1 + nu))
            if U.ndim == 2:
                gu = U[conn].T @ G                  # du_i/dx_j
                eps = 0.5 * (gu + gu.T)
                out.append(lam * np.trace(eps) * np.eye(3) + 2 * mu * eps)
            else:
                gu = np.einsum("kai,aj->kij", U[:, conn, :], G)
                eps = 0.5 * (gu + np.transpose(gu, (0, 2, 1)))
                tr = np.trace(eps, axis1=1, axis2=2)
                out.append(lam * tr[:, None, None] * np.eye(3) + 2 * mu * eps)
        return np.mean(out, axis=0), len(out)
    # node -> elements of the same body as the probe node
    node_elems = {}
    want = set(int(n) for n in probe_nodes)
    body_of = {}
    for eid, conn in elem.items():
        for nd in conn:
            if int(nd) in want:
                node_elems.setdefault(int(nd), []).append(eid)
    for nd in want:                                   # keep only the elements of the dominant body at that node
        bs = [ebody[e] for e in node_elems[nd]]
        b0 = max(set(bs), key=bs.count)
        body_of[nd] = b0
        node_elems[nd] = [e for e in node_elems[nd] if ebody[e] == b0]
    vm = lambda T: math.sqrt(0.5 * ((T[0, 0] - T[1, 1]) ** 2 + (T[1, 1] - T[2, 2]) ** 2 + (T[2, 2] - T[0, 0]) ** 2) + 3 * (T[0, 1] ** 2 + T[1, 2] ** 2 + T[0, 2] ** 2))
    pts = {}
    for nd in probe_nodes:
        nd = int(nd)
        s0, ne = probe(nd, Uop)
        sm, _ = probe(nd, Uf)
        sc = Sop[nd]
        Tc = np.array([[sc[0], sc[3], sc[5]], [sc[3], sc[1], sc[4]], [sc[5], sc[4], sc[2]]])
        w, V = np.linalg.eigh(s0)
        kk = int(np.argmax(np.abs(w)))
        nvec = V[:, kk]
        funs = {"principal": (np.einsum("i,kij,j->k", nvec, sm, nvec), float(nvec @ s0 @ nvec)),
                "tensor": (np.einsum("kij,ij->k", sm, s0), float(np.einsum("ij,ij->", s0, s0)))}
        row = {"node": nd, "body": body_of[nd], "xyz": X[nd].round(3).tolist(), "n_elems": ne, "s0_vm_probe": vm(s0), "s0_vm_ccx": vm(Tc),
               "s0_principal": float(w[kk]), "dominant_dir": nvec.round(4).tolist()}
        for fk, (vals, den) in funs.items():
            c = vals * p / om2 / den
            rr = {"residual": float(1 - c.sum()), "shares_all_60": [[int(i + 1), float(f[i]), float(c[i])] for i in range(len(f))]}
            for s in (1.00, 0.90, 0.85):
                fs = s * f
                rr[f"s{s:.2f}"] = {"slow_T_gt_1ms": float(c[fs < 1000].sum()), "abs_slow": float(np.abs(c[fs < 1000]).sum()),
                                   "mid_0p1_1ms": float(c[(fs >= 1000) & (fs < 10000)].sum()), "residual_fast": float(1 - c.sum())}
            rr["top6"] = sorted([[int(i + 1), float(f[i]), float(c[i])] for i in range(len(f))], key=lambda r: -abs(r[2]))[:6]
            rr["abs_sum_computed_modes"] = float(np.abs(c).sum())
            row[fk] = rr
        pts[str(nd)] = row
    res["points"] = pts
    res["f_Hz"] = f.tolist()
    res["p_i"] = p.tolist()
    res["time_s"] = time.time() - t0
    Path(outp).write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("points", "f_Hz", "p_i")}, indent=1))
    for nd, r in pts.items():
        print(f"node {nd} {r['body']} {r['xyz']} elems {r['n_elems']}: vm probe {r['s0_vm_probe']:.3f} ccx {r['s0_vm_ccx']:.3f} principal {r['s0_principal']:.3f}")
        for fk in ("principal", "tensor"):
            rr = r[fk]
            print(f"   {fk}: " + "; ".join(f"x{s}: slow {rr[f's{s}']['slow_T_gt_1ms']:+.4f} |slow| {rr[f's{s}']['abs_slow']:.4f} mid {rr[f's{s}']['mid_0p1_1ms']:+.4f}"
                                     for s in ("1.00", "0.90", "0.85")) + f"; residual {rr['residual']:+.4f}; top {[(a, round(b), round(c, 4)) for a, b, c in rr['top6'][:4]]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
