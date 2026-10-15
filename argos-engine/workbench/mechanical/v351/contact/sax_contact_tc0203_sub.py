"""T-F2 / RM1-03 (lead CHANGELOG 212): contact FE of the TC-02 / TC-03 seat-insert interface, SUBMODEL of the v3.5.1 S-AX L1 model.
Mechanical, 2026-10-13, v1.

Why a submodel: the full-model frictional contact run (sax_contact_tc0203.py v1, C3 TB70) converged its first increment in 40 s and then
spent > 12 min of CPU in the first iteration of increment 2 (unsymmetric SPOOLES, ccx stdout not flushed); killed by PID 18:52Z.

Submodel = every S-AX L1 element of TC-02, TC-03, TC-04 and the TC-01 elements with centroid z >= Z_CUT (the case wall 30 mm below the
TC-01 / TC-02 bolt band).  Same mesh (runs/structural/L1_thv351_TB1GC_cad351/mesh.npz b780ed547ad8f3ba), materials, equations, thermal
field (state_temperature, thermal v351_TB1GC), face loads and gravity as the linear S-AX run.  Boundary: the TC-01 cut nodes take u_r and
u_z of the linear global solution of the same state and case (step 1: thermal-only U1; step 2: U1 + sum c_k U_k, sax.combo_fields).
Variants (all two steps: 1 = thermal state, 2 = the case's mechanical loads added; contact variants nonlinear):
  C0  linear ties exactly as S-AX (no contact): must reproduce the global linear result (submodel check)
  C5  mu 0   : TC-02 / TC-03 shank kept tied axially (thread interlock, as S-AX), radial contact on the shank, flange top and insert top in
               frictionless contact (no tension) instead of the S-AX normal tie
  C3  mu 0.2 : as C5 with Coulomb friction 0.2 on all TC-02 / TC-03 contact faces
  C4  mu 0.6 : as C5 with friction 0.6
Margins of TC-02 / TC-03: S-AX nodal criterion (von Mises vs Fty(T)/SF_y and Ftu(T)/SF_u on the total stress; 'regular' = nodes farther
than 1.0 mm from the singular points of the linear model; 'all' = every node), compared with the linear S-AX row of the same state.
Not a mesh-convergence study; the thread is a smeared axial tie (no flank wedge, no preload); the submodel boundary carries the linear
tie solution 30 mm away from the seat (St-Venant)."""
from __future__ import annotations
import os, sys, json, math, time, hashlib, subprocess
from pathlib import Path
os.environ.setdefault("SAX_CAD", "v351")
os.environ.setdefault("SAX_THERMAL_TAG", "v351_TB1GC")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/structural")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/src")
import numpy as np
import sax

OUTROOT = Path("/home/claude/work/mechanical/runs/structural/contact_tc0203_cad351_sub")
VARIANTS = {"C0": {"contact": False, "mu": None}, "C5": {"contact": True, "mu": 0.0},
            "C3": {"contact": True, "mu": 0.2}, "C4": {"contact": True, "mu": 0.6}}
CASES = {"LC2": "B1_19", "TB70": "TB"}
K_PEN, STICK = 5.0e5, 1.0e4        # MPa/mm penalty (normal), MPa/mm stick slope (ASSUMED numerical parameters, ccx guidance K/50)
SUBPARTS = ("ENG-TC-02", "ENG-TC-03", "ENG-TC-04")
A, B = "ENG-TC-02", "ENG-TC-03"
Z_CUT_BELOW_BAND = 30.0            # mm


def faces_on(d, part, nodeset, elems):
    E, pn = d["E"], d["pn"]
    out = []
    for e in elems:
        if pn[e] != part:
            continue
        for f, (i, j, k) in sax.EDGE.items():
            if int(E[e, i]) in nodeset and int(E[e, j]) in nodeset and int(E[e, k]) in nodeset:
                out.append((int(e), f))
    return out


def submodel(d, info):
    X, E, pn = d["X"], d["E"], d["pn"]
    cen_z = X[E[:, :3], 1].mean(axis=1)
    z_cut = info["bolt_z_fwd"] - Z_CUT_BELOW_BAND
    in_el = np.isin(pn, SUBPARTS) | ((pn == "ENG-TC-01") & (cen_z >= z_cut))
    els = np.nonzero(in_el)[0]
    nodes = np.unique(E[els])
    out_nodes = np.unique(E[(~in_el) & (pn == "ENG-TC-01")])
    cut = np.intersect1d(nodes, out_nodes)
    other = np.intersect1d(nodes, np.unique(E[(~in_el) & (pn != "ENG-TC-01")]))   # must be empty: no other part touches the submodel
    return els, nodes, cut, other, z_cut


def write_deck(path, d, els, nodes, cut, eqs, fb, info, T, gp, plug, co, U1, Uc, contact, slave, master, mu, title):
    X, E, mat = d["X"], d["E"], d["mat"]
    L = [f"*HEADING\n{title}\n", "*NODE, NSET=NALL\n"]
    L += [f"{n + 1}, {X[n, 0]:.6f}, {X[n, 1]:.6f}\n" for n in nodes]
    for m_ in sax.MAT_MECH:
        idx = els[mat[els] == m_]
        if len(idx):
            L.append(f"*ELEMENT, TYPE=CAX6, ELSET=M_{m_.replace('-', '_')}\n")
            L += [f"{e + 1}, " + ", ".join(str(int(n) + 1) for n in E[e]) + "\n" for e in idx]
    L.append("*NSET, NSET=NCUT\n")
    L += [", ".join(str(int(n) + 1) for n in cut[k:k + 12]) + "\n" for k in range(0, len(cut), 12)]
    for m_ in sax.MAT_MECH:
        if (mat[els] == m_).any():
            L.append(sax.mat_cards(m_))
            L.append(f"*SOLID SECTION, ELSET=M_{m_.replace('-', '_')}, MATERIAL={m_.replace('-', '_')}\n")
    for dof in (1, 2):
        for a_, b_ in eqs[dof]:
            L.append(f"*EQUATION\n2\n{a_ + 1}, {dof}, 1., {b_ + 1}, {dof}, -1.\n")
    if contact:
        L.append("*SURFACE, NAME=SLV, TYPE=ELEMENT\n")
        L += [f"{e + 1}, S{f}\n" for (e, f) in slave]
        L.append("*SURFACE, NAME=MST, TYPE=ELEMENT\n")
        L += [f"{e + 1}, S{f}\n" for (e, f) in master]
        L.append("*CONTACT PAIR, INTERACTION=SI1, TYPE=SURFACE TO SURFACE\nSLV, MST\n")
        L.append(f"*SURFACE INTERACTION, NAME=SI1\n*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR\n{K_PEN:.3e}\n")
        if mu and mu > 0:
            L.append(f"*FRICTION\n{mu}, {STICK:.3e}\n")
    L.append(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {sax.T_REF}\n")
    outq = "*NODE FILE\nU\n*EL FILE\nS\n"
    stat = "*STEP, INC=300\n*STATIC\n0.25, 1.0, 1e-6, 0.5\n" if contact else "*STEP\n*STATIC\n"
    L.append(stat + "*BOUNDARY\n")
    L += [f"{n + 1}, 1, 1, {U1[n, 0]:.9e}\n{n + 1}, 2, 2, {U1[n, 1]:.9e}\n" for n in cut]
    L.append("*TEMPERATURE\n")
    L += [f"{n + 1}, {T[n]:.3f}\n" for n in nodes]
    L.append(outq + "*END STEP\n")
    L.append(stat + "*BOUNDARY\n")
    L += [f"{n + 1}, 1, 1, {Uc[n, 0]:.9e}\n{n + 1}, 2, 2, {Uc[n, 1]:.9e}\n" for n in cut]
    L.append("*DLOAD, OP=NEW\n")
    elset = set(int(e) for e in els)
    for (e, f, c, r, z, n, Lf) in fb:
        if e not in elset:
            continue
        v = 0.0
        if "OP" in co:
            v += co["OP"] * (1.0 if c == "PC" else (gp(z) if c == "GAS" else 0.0))
        if "BL" in co:
            v += co["BL"] * ((1.0 if c == "PC" else ((1.0 if z >= info["throat"] else 0.0) if c == "GAS" else 0.0)) + plug.get((e, f), 0.0))
        if "PM" in co:
            v += co["PM"] * (1.0 if c == "PM" else 0.0)
        if v != 0.0:
            L.append(f"{e + 1}, P{f}, {v:.6f}\n")
    if co.get("G"):
        for m_ in sax.MAT_MECH:
            if (mat[els] == m_).any():
                L.append(f"M_{m_.replace('-', '_')}, GRAV, {sax.G * co['G']:.6f}, 0., -1., 0.\n")
    L.append(outq + "*END STEP\n")
    Path(path).write_text("".join(L))


def run_ccx(inp, timeout=3 * 3600):
    env = dict(os.environ, OMP_NUM_THREADS="1", CCX_NPROC_EQUATION_SOLVER="1")
    t0 = time.time()
    with open(inp.parent / f"{inp.stem}.out", "w") as fo:          # line-buffered stdout: progress visible while it runs
        r = subprocess.run(["stdbuf", "-oL", "ccx", "-i", inp.stem], cwd=str(inp.parent), env=env, stdout=fo, stderr=subprocess.STDOUT,
                           timeout=timeout)
    txt = (inp.parent / f"{inp.stem}.out").read_text(errors="replace")
    return {"seconds": round(time.time() - t0, 1), "returncode": r.returncode,
            "errors": [l for l in txt.splitlines() if "*ERROR" in l][:5], "warnings": [l for l in txt.splitlines() if "*WARNING" in l][:5],
            "n_increments_converged": txt.count("convergence\n") - txt.count("no convergence"),
            "contact_spring_elements_last": next((l.split("=")[-1].strip() for l in reversed(txt.splitlines()) if "contact spring elements" in l), None)}


def margins(d, nodes_sub, S, T, sfy, sfu, reg, parts=(A, B)):
    node_part, node_mat = sax.node_maps(d)
    v = sax.vm(S)
    out = {}
    for p in parts:
        nodes = np.intersect1d(np.nonzero(node_part == p)[0], nodes_sub)
        m_ = node_mat[nodes[0]]
        a1, a2 = sax.allowables(m_, T[nodes])
        ms = a1 / (sfy * np.maximum(v[nodes], 1e-9)) - 1.0
        msu = a2 / (sfu * np.maximum(v[nodes], 1e-9)) - 1.0
        o = {}
        for tag, msk in (("regular", reg[nodes]), ("all", np.ones(len(nodes), bool))):
            i = int(np.argmin(np.where(msk, msu, np.inf)))
            j = int(np.argmin(np.where(msk, ms, np.inf)))
            n = nodes[i]
            o[tag] = {"MS_ult_min": round(float(msu[i]), 4), "at_r_z_mm": [round(float(d["X"][n, 0]), 3), round(float(d["X"][n, 1]), 3)],
                      "vm_MPa": round(float(v[n]), 2), "T_C": round(float(T[n] - 273.15), 1), "MS_y_min": round(float(ms[j]), 4),
                      "node": int(n) + 1}
        out[p] = o
    return out


def main(variants=None, cases=None):
    faces, info = sax.geometry()
    d, meta_m = sax.load_mesh(1)
    X = d["X"]
    fb = sax.boundary_faces(d, info)
    gp, gmeta = sax.gas_profile(info)
    plug, pmeta = sax.plug_band(fb, info, d["X"], d["E"])
    from scipy.spatial import cKDTree
    sp = sax.singular_points(d, info)
    reg = cKDTree(sp).query(X)[0] > 1.0
    node_part, _ = sax.node_maps(d)
    els, nodes, cut, other, z_cut = submodel(d, info)
    assert len(other) == 0, f"submodel touches other parts at {len(other)} nodes"
    nodeset = set(int(n) for n in nodes)
    ifc = [(int(n), (int(ia), int(ib)) if str(pa) == A else (int(ib), int(ia))) for (n, pa, pb, ia, ib, rule) in d["pairs"] if {str(pa), str(pb)} == {A, B}]
    s02 = {i02 for _, (i02, _) in ifc}
    s03 = {i03 for _, (_, i03) in ifc}
    shank03 = {i03 for _, (i02, i03) in ifc if abs(X[i03, 0] - 7.0) < 1e-3}
    co_all = {c[0]: c for c in sax.combos(info)}
    rd_lin = sax.run_dir(1)
    OUTROOT.mkdir(parents=True, exist_ok=True)
    part_f = OUTROOT / "sax_contact_tc0203_sub_v1_partial.json"
    res = {"id": "sax_contact_tc0203_sub", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "request": "lead CHANGELOG 212: T-F2 / RM1-03",
           "doc": __doc__, "mesh": {"file": str(rd_lin / "mesh.npz"), "sha256_16": hashlib.sha256((rd_lin / "mesh.npz").read_bytes()).hexdigest()[:16]},
           "cad": "v3.5.1 (geom_v351)", "thermal": os.environ["SAX_THERMAL_TAG"],
           "submodel": {"parts": list(SUBPARTS) + [f"ENG-TC-01 (centroid z >= {z_cut:.3f} mm)"], "n_elements": int(len(els)), "n_nodes": int(len(nodes)),
                        "n_cut_nodes": int(len(cut)), "z_cut_mm": round(z_cut, 3)},
           "penalty": {"K_MPa_per_mm": K_PEN, "stick_slope_MPa_per_mm": STICK},
           "interface_pairs": len(ifc), "shank_pairs": len(shank03), "runs": {}}
    if part_f.exists():
        old = json.loads(part_f.read_text())
        if old.get("mesh", {}).get("sha256_16") == res["mesh"]["sha256_16"]:
            res["runs"].update({k: v for k, v in old.get("runs", {}).items() if v.get("margins")})
    for vn, vv in VARIANTS.items():
        if variants and vn not in variants:
            continue
        eqs = {1: [], 2: []}
        for dof in (1, 2):
            for a_, b_ in d["eqs"][dof]:
                if a_ not in nodeset or b_ not in nodeset:
                    continue
                if vv["contact"] and {node_part[a_], node_part[b_]} == {A, B}:
                    if dof == 2 and (a_ in shank03 or b_ in shank03):
                        eqs[dof].append((a_, b_))       # thread interlock kept
                    continue
                eqs[dof].append((a_, b_))
        slave = faces_on(d, B, s03, els) if vv["contact"] else []
        master = faces_on(d, A, s02, els) if vv["contact"] else []
        for cid, st in CASES.items():
            if cases and cid not in cases:
                continue
            key = f"{vn}_{cid}_{st}"
            if key in res["runs"] and (OUTROOT / key / "res.npz").exists():
                print(key, "kept from an earlier invocation", flush=True)
                continue
            c = co_all[cid]
            co, sfy, sfu = c[3], c[4], c[5]
            T, prov = sax.state_temperature(st, d, info)
            z = np.load(rd_lin / st / "res.npz", allow_pickle=True)
            U1 = z["U1"]
            Sg, Ug, Tg, _ = sax.combo_fields(1, cid, st)
            assert np.allclose(Tg, T), "thermal field differs from the linear run"
            wd = OUTROOT / key
            wd.mkdir(parents=True, exist_ok=True)
            job = wd / "con.inp"
            write_deck(job, d, els, nodes, cut, eqs, fb, info, T, gp, plug, co, U1, Ug, vv["contact"], slave, master, vv["mu"],
                       f"S-AX submodel {key} (v3.5.1, T-F2)")
            r = run_ccx(job)
            row = {"variant": vn, **vv, "case": cid, "state": st, "coefficients": co, "SF": [sfy, sfu], "ccx": r,
                   "n_slave_faces": len(slave), "n_master_faces": len(master),
                   "n_eq": sum(len(eqs[k]) for k in (1, 2))}
            frd = wd / "con.frd"
            if r["returncode"] == 0 and not r["errors"] and frd.exists():
                steps = sax.read_frd(frd, len(X))
                U, S = steps[-1]["U"], steps[-1]["S"]
                row["n_result_blocks"] = len(steps)
                row["margins"] = margins(d, nodes, S, T, sfy, sfu, reg)
                gl = margins(d, nodes, Sg, T, sfy, sfu, reg)
                row["global_linear_same_nodes"] = gl
                if vn == "C0":     # submodel check: interior stress vs the global linear combined field
                    inner = np.array([n for n in nodes if n not in set(int(q) for q in cut)])
                    dv = np.abs(sax.vm(S[inner]) - sax.vm(Sg[inner]))
                    row["check_vs_global"] = {"max_abs_dvm_MPa": round(float(dv.max()), 6), "max_vm_MPa": round(float(sax.vm(Sg[inner]).max()), 3),
                                              "max_abs_du_mm": round(float(np.abs(U[inner, :2] - Ug[inner, :2]).max()), 9)}
                if vv["contact"]:
                    gap = [float(U[i03, 0] - U[i02, 0]) for _, (i02, i03) in ifc if abs(X[i03, 0] - 7.0) < 1e-3]
                    flg = [float(U[i02, 1] - U[i03, 1]) for _, (i02, i03) in ifc if abs(X[i03, 1] - info["inj_face"] - 4.0) < 1e-3]
                    top = [float(U[i02, 1] - U[i03, 1]) for _, (i02, i03) in ifc if abs(X[i03, 1] - info["inj_face"] - 14.0) < 1e-3]
                    row["shank_radial_gap_mm"] = {"min": round(min(gap), 6), "max": round(max(gap), 6),
                                                  "note": "u_r(TC-03 shank) - u_r(TC-02 bore) at the paired nodes: > 0 = overclosure (contact)"}
                    row["flange_top_axial_opening_mm"] = ({"min": round(min(flg), 6), "max": round(max(flg), 6), "n": len(flg),
                                                           "note": "u_z(TC-02 counterbore floor) - u_z(TC-03 flange top): > 0 = open"} if flg else None)
                    row["insert_top_axial_opening_mm"] = ({"min": round(min(top), 6), "max": round(max(top), 6), "n": len(top)} if top else None)
                np.savez_compressed(wd / "res.npz", U=U[nodes], S=S[nodes], T=T[nodes], nodes=nodes)
                for f_ in ("con.frd", "con.12d"):
                    (wd / f_).unlink(missing_ok=True)
            res["runs"][key] = row
            print(key, r, json.dumps(row.get("margins", {}).get(A, {}))[:400], flush=True)
            part_f.write_text(json.dumps(res, indent=1, default=float))
    s = json.dumps(res, indent=1, default=float)
    (OUTROOT / "sax_contact_tc0203_sub_v1.json").write_text(s)
    print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])


if __name__ == "__main__":
    a = sys.argv[1:]
    main(variants=(a[0].split(",") if a else None), cases=(a[1].split(",") if len(a) > 1 else None))
