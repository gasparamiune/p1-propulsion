"""T-F2 / RM1-03 (lead CHANGELOG 212): contact FE of the TC-02 / TC-03 seat-insert interface on the v3.5.1 S-AX L1 model.
Mechanical, 2026-10-13, v1.

Same mesh (runs/structural/L1_thv351_TB1GC_cad351/mesh.npz, b780ed547ad8f3ba), materials, thermal mapping (thermal v351_TB1GC) and loads
as the linear S-AX run; ONLY the TC-02/TC-03 interface changes: the tie equations of the M14x1 shank (r 7.0), the flange top on the
counterbore floor (z 107.513) and the insert top on the tap bottom (z 117.513) are replaced by CalculiX surface-to-surface penalty
contact with Coulomb friction.  Variants:
  C1  mu 0.2, shank axially free (thread modelled as a frictional cylinder: upper bound of the slip relief)
  C2  mu 0.6, shank axially free
  C3  mu 0.2, shank axially tied (thread interlock, as the linear model) + radial contact on the shank, contact at the flange and tap bottom
  C4  as C3 with mu 0.6
Each run: step 1 = thermal state (u_z = 0 at one groove node), step 2 = the case's mechanical loads (groove band fixed at its step-1
displacement), both nonlinear (contact).  The TC-02 / TC-03 margins use the S-AX nodal criterion (von Mises vs Fty(T)/SF_y, Ftu(T)/SF_u;
'regular' = nodes farther than 1.0 mm from the singular points of the LINEAR model; 'all' = every node) and are compared with the linear
tie result of the same state.  Not a mesh-convergence study; the thread is not modelled as a profile (no flank wedge, no preload)."""
from __future__ import annotations
import os, sys, json, math, time, hashlib
from pathlib import Path
os.environ.setdefault("SAX_CAD", "v351")
os.environ.setdefault("SAX_THERMAL_TAG", "v351_TB1GC")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/structural")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/src")
import numpy as np
import sax, engmat

OUTROOT = Path("/home/claude/work/mechanical/runs/structural/contact_tc0203_cad351")
VARIANTS = {"C1": {"mu": 0.2, "shank_tie": False}, "C2": {"mu": 0.6, "shank_tie": False}, "C3": {"mu": 0.2, "shank_tie": True},
            "C4": {"mu": 0.6, "shank_tie": True}}
# Default run set C3, C4 (thread interlock kept).  C1 / C2 (shank axially free) are NOT run by default: a threaded insert cannot slip
# axially, and with the shank free the insert is held in -z only by friction, i.e. it is a free body in the thermal step unless the
# shank closes radially (singular stiffness risk).  They stay available as an explicit bounding request.
DEFAULT_VARIANTS = ("C3", "C4")
CASES = {"LC2": "B1_19", "TB70": "TB"}
K_PEN, SIG_INF, STICK = 5.0e5, 0.25, 1.0e4       # MPa/mm, MPa, MPa/mm (penalty; ASSUMED numerical parameters)
A, B = "ENG-TC-02", "ENG-TC-03"


def interface(d):
    """TC-02 / TC-03 coincident copies: [(orig, id_TC02, id_TC03)], plus the part of every node."""
    out = []
    for (n, pa, pb, ia, ib, rule) in d["pairs"]:
        pa, pb = str(pa), str(pb)
        if {pa, pb} == {A, B}:
            i02, i03 = (int(ia), int(ib)) if pa == A else (int(ib), int(ia))
            out.append((int(n), i02, i03))
    return out


def faces_on(d, part, nodeset):
    E, pn = d["E"], d["pn"]
    out = []
    for e in np.nonzero(pn == part)[0]:
        for f, (i, j, k) in sax.EDGE.items():
            if int(E[e, i]) in nodeset and int(E[e, j]) in nodeset and int(E[e, k]) in nodeset:
                out.append((int(e), f))
    return out


def write_deck(path, d, eqs, fb, info, T, gp, plug, co, slave, master, mu, title):
    X, E, pn, mat = d["X"], d["E"], d["pn"], d["mat"]
    L = [f"*HEADING\n{title}\n", "*NODE, NSET=NALL\n"]
    L += [f"{i + 1}, {x[0]:.6f}, {x[1]:.6f}\n" for i, x in enumerate(X)]
    for m_ in sax.MAT_MECH:
        idx = np.nonzero(mat == m_)[0]
        if len(idx):
            L.append(f"*ELEMENT, TYPE=CAX6, ELSET=M_{m_.replace('-', '_')}\n")
            L += [f"{e + 1}, " + ", ".join(str(int(n) + 1) for n in E[e]) + "\n" for e in idx]
    sup = sax.support_nodes(d, info)
    L.append("*NSET, NSET=NSUP\n")
    L += [", ".join(str(int(n) + 1) for n in sup[k:k + 12]) + "\n" for k in range(0, len(sup), 12)]
    sup0 = sax.support_node0(d, info, sup)
    L.append(f"*NSET, NSET=NSUP0\n{sup0 + 1}\n")
    for m_ in sax.MAT_MECH:
        if (mat == m_).any():
            L.append(sax.mat_cards(m_))
            L.append(f"*SOLID SECTION, ELSET=M_{m_.replace('-', '_')}, MATERIAL={m_.replace('-', '_')}\n")
    for dof in (1, 2):
        for a_, b_ in eqs[dof]:
            L.append(f"*EQUATION\n2\n{a_ + 1}, {dof}, 1., {b_ + 1}, {dof}, -1.\n")
    L.append("*SURFACE, NAME=SLV, TYPE=ELEMENT\n")
    L += [f"{e + 1}, S{f}\n" for (e, f) in slave]
    L.append("*SURFACE, NAME=MST, TYPE=ELEMENT\n")
    L += [f"{e + 1}, S{f}\n" for (e, f) in master]
    L.append("*CONTACT PAIR, INTERACTION=SI1, TYPE=SURFACE TO SURFACE\nSLV, MST\n")
    L.append(f"*SURFACE INTERACTION, NAME=SI1\n*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR\n{K_PEN:.3e}, {SIG_INF}\n*FRICTION\n{mu}, {STICK:.3e}\n")
    L.append("*BOUNDARY\nNSUP0, 2, 2\n")
    L.append(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {sax.T_REF}\n")
    outq = "*NODE FILE\nU\n*EL FILE\nS\n*NODE PRINT, NSET=NSUP, TOTALS=ONLY\nRF\n"
    L.append("*STEP, INC=200\n*STATIC\n0.1, 1.0, 1e-6, 0.25\n*TEMPERATURE\n")
    L += [f"{i + 1}, {t:.3f}\n" for i, t in enumerate(T)]
    L.append(outq + "*END STEP\n")
    L.append("*STEP, INC=200\n*STATIC\n0.1, 1.0, 1e-6, 0.25\n*BOUNDARY, FIXED\nNSUP, 2, 2\n*DLOAD, OP=NEW\n")
    for (e, f, c, r, z, n, Lf) in fb:
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
            if (mat == m_).any():
                L.append(f"M_{m_.replace('-', '_')}, GRAV, {sax.G * co['G']:.6f}, 0., -1., 0.\n")
    L.append(outq + "*END STEP\n")
    Path(path).write_text("".join(L))


def margins(d, S, T, sfy, sfu, reg, parts=(A, B)):
    node_part, node_mat = sax.node_maps(d)
    v = sax.vm(S)
    out = {}
    for p in parts:
        nodes = np.nonzero(node_part == p)[0]
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
                      "vm_MPa": round(float(v[n]), 2), "T_C": round(float(T[n] - 273.15), 1), "MS_y_min": round(float(ms[j]), 4)}
        out[p] = o
    return out


def main(variants=None, cases=None):
    faces, info = sax.geometry()
    d, meta_m = sax.load_mesh(1)
    fb = sax.boundary_faces(d, info)                       # with the linear ties: interface faces stay unloaded
    gp, gmeta = sax.gas_profile(info)
    plug, pmeta = sax.plug_band(fb, info, d["X"], d["E"])
    from scipy.spatial import cKDTree
    sp = sax.singular_points(d, info)
    reg = cKDTree(sp).query(d["X"])[0] > 1.0
    ifc = interface(d)
    X = d["X"]
    s02 = {i02 for (_, i02, _) in ifc}
    s03 = {i03 for (_, _, i03) in ifc}
    shank03 = {i03 for (_, i02, i03) in ifc if abs(X[i03, 0] - 7.0) < 1e-3}
    node_part, _ = sax.node_maps(d)
    co_all = {c[0]: c for c in sax.combos(info)}
    rd_lin = sax.run_dir(1)
    res = {"id": "sax_contact_tc0203", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "request": "lead CHANGELOG 212: T-F2 / RM1-03",
           "doc": __doc__, "mesh": {"file": str(rd_lin / "mesh.npz"), "sha256_16": hashlib.sha256((rd_lin / "mesh.npz").read_bytes()).hexdigest()[:16]},
           "cad": "v3.5.1 (geom_v351)", "thermal": "v351_TB1GC", "penalty": {"K_MPa_per_mm": K_PEN, "sigma_inf_MPa": SIG_INF, "stick_slope_MPa_per_mm": STICK},
           "interface_nodes": len(ifc), "shank_nodes": len(shank03), "runs": {}}
    part_f = OUTROOT / "sax_contact_tc0203_v1_partial.json"
    if part_f.exists():                                  # keep completed runs of earlier invocations (same mesh only)
        old = json.loads(part_f.read_text())
        if old.get("mesh", {}).get("sha256_16") == res["mesh"]["sha256_16"]:
            res["runs"].update({k: v for k, v in old.get("runs", {}).items() if v.get("margins")})
    for vn, vv in VARIANTS.items():
        if vn not in (variants or DEFAULT_VARIANTS):
            continue
        eqs = {1: [], 2: []}
        for dof in (1, 2):
            for a_, b_ in d["eqs"][dof]:
                pa, pb = node_part[a_], node_part[b_]
                if {pa, pb} == {A, B}:
                    if vv["shank_tie"] and dof == 2 and (a_ in shank03 or b_ in shank03):
                        eqs[dof].append((a_, b_))
                    continue
                eqs[dof].append((a_, b_))
        slave = faces_on(d, B, s03)
        master = faces_on(d, A, s02)
        for cid, st in CASES.items():
            if cases and cid not in cases:
                continue
            if f"{vn}_{cid}_{st}" in res["runs"] and (OUTROOT / f"{vn}_{cid}_{st}" / "res.npz").exists():
                print(vn, cid, st, "kept from an earlier invocation", flush=True)
                continue
            c = co_all[cid]
            co, sfy, sfu = c[3], c[4], c[5]
            T, prov = sax.state_temperature(st, d, info)
            wd = OUTROOT / f"{vn}_{cid}_{st}"
            wd.mkdir(parents=True, exist_ok=True)
            job = wd / "con.inp"
            write_deck(job, d, eqs, fb, info, T, gp, plug, co, slave, master, vv["mu"], f"S-AX contact {vn} {cid} {st} (v3.5.1, T-F2)")
            r = sax.run_ccx(job, threads=1, timeout=3 * 3600)
            row = {"variant": vn, **vv, "case": cid, "state": st, "coefficients": co, "SF": [sfy, sfu], "ccx": r,
                   "n_slave_faces": len(slave), "n_master_faces": len(master), "n_eq_removed": sum(len(d["eqs"][k]) for k in (1, 2)) - sum(len(eqs[k]) for k in (1, 2))}
            frd = wd / "con.frd"
            if r["returncode"] == 0 and not r["errors"] and frd.exists():
                steps = sax.read_frd(frd, len(X))
                U, S = steps[-1]["U"], steps[-1]["S"]
                row["n_result_blocks"] = len(steps)
                row["margins"] = margins(d, S, T, sfy, sfu, reg)
                # interface state from the paired copies: radial gap on the shank (+ open), axial slip
                gap = [float(U[i03, 0] - U[i02, 0]) for (_, i02, i03) in ifc if abs(X[i03, 0] - 7.0) < 1e-3]
                slip = [float(U[i03, 1] - U[i02, 1]) for (_, i02, i03) in ifc if abs(X[i03, 0] - 7.0) < 1e-3]
                flg = [float(U[i02, 1] - U[i03, 1]) for (_, i02, i03) in ifc if abs(X[i03, 1] - 107.51342601773104) < 1e-3]
                row["shank_radial_gap_mm"] = {"min": round(min(gap), 5), "max": round(max(gap), 5), "note": "TC-02 bore minus TC-03 shank radial displacement: < 0 = overclosure (contact)"}
                row["shank_axial_slip_mm"] = {"min": round(min(slip), 5), "max": round(max(slip), 5)}
                row["flange_axial_gap_mm"] = {"min": round(min(flg), 5), "max": round(max(flg), 5), "note": "counterbore floor minus flange top z displacement: > 0 = open"} if flg else None
                np.savez_compressed(wd / "res.npz", U=U, S=S, T=T)
                for f_ in ("con.frd", "con.12d"):
                    (wd / f_).unlink(missing_ok=True)
            res["runs"][f"{vn}_{cid}_{st}"] = row
            print(vn, cid, st, r["seconds"], r["returncode"], r["errors"][:2], json.dumps(row.get("margins", {}).get(A, {}))[:300], flush=True)
            (OUTROOT / "sax_contact_tc0203_v1_partial.json").write_text(json.dumps(res, indent=1, default=float))
    # linear (tie) reference at the same states
    ev = json.loads((Path("/home/claude/work/mechanical/v351/engine/04-fea/structural/results") / "sax_results_L1_thv351_TB1GC_cad351_v1.json").read_text())
    ref = {}
    for cid, st in CASES.items():
        for p in (A, B):
            for tag in ("regular", "all"):
                rr = [r for r in ev["rows"] if r["case"] == cid and r["state"] == st and r["part"] == p and r["set"] == tag]
                if rr:
                    ref[f"{cid}_{st}_{p}_{tag}"] = {"MS_ult": rr[0]["MS_ult"], "MS": rr[0]["MS"], "at_r_z_mm": rr[0]["at_r_z_mm"], "vm_MPa": rr[0]["vm_MPa"]}
    res["linear_tie_reference"] = ref
    s = json.dumps(res, indent=1, default=float)
    (OUTROOT / "sax_contact_tc0203_v1.json").write_text(s)
    print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])


if __name__ == "__main__":
    a = sys.argv[1:]
    main(variants=(a[0].split(",") if a else None), cases=(a[1].split(",") if len(a) > 1 else None))
