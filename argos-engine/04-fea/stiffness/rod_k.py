"""Axial stiffness of the TVC pushrod GM-17 with its two pressed GE 5 E outer rings (04-fea/stiffness, v1, 2026-10-12, Mechanical).

Model (mm, N, MPa): GM-17 dog-bone exactly as parts_gimbal.py v3.3 builds it (eyes 18 x 4 with 14 bores, shank 4 x 7, eye
centres L_pr apart) + two GE 5 E outer rings (OD 14, width C 4, spherical bore R 5 = dk/2), conforming mesh (press fit treated
as bonded).  The GE inner ring is not meshed: the ball load enters the outer-ring spherical bore as a contact pressure
p = p0 max(0, n . e_load) (cosine law, conformal sphere) on the half that bears; tension loads the out-board halves (load goes
round the eye), compression the in-board halves.  Self-equilibrated end loads +/-F, statically determinate 3-2-1 support at the
shank centre (reactions ~0), so the compliance is exact from the strain energy: c = 2 U / F^2.  A second variant ties the
bearing half to a rigid body (upper bound of the load introduction).
Materials: 7075-T6 E 71.7 GPa nu 0.33 (engmat); GE ring bearing steel E 208 GPa nu 0.30 (ASSUMED handbook value).
Output: rod_k_v1.json (k per load sense, mesh study, bilinear equivalent), runs in /home/claude/work/mechanical/runs/stiff/rod.
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CAD = HERE.parents[1] / "03-cad" / "src"
sys.path.insert(0, str(CAD))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import fe_util as fu
import engmat

RUNS = Path("/home/claude/work/mechanical/runs/stiff/rod")
E_ROD = engmat.prop("AL7075-T6", "E") / 1e6
E_STEEL, NU_STEEL = 208e3, 0.30
F = 1000.0                                            # N


def geometry():
    import config, tvc_kinematics as tk
    import cadquery as cq
    P, _ = config.build()
    g = tk.geometry(P)
    Lp = g["L_pr"]
    D, C, dk, e_od = 14.0, 4.0, 10.0, 18.0

    def cyl_x(d, w, zc):
        return cq.Solid.makeCylinder(d / 2, w, cq.Vector(-w / 2, 0, zc), cq.Vector(1, 0, 0))

    dog = cyl_x(e_od, C, 0.0).fuse(cyl_x(e_od, C, Lp)).fuse(cq.Solid.makeBox(C, 7.0, Lp, cq.Vector(-C / 2, -3.5, 0.0)))
    dog = dog.cut(cyl_x(D, C + 2, 0.0)).cut(cyl_x(D, C + 2, Lp)).clean()
    rings = []
    for zc in (0.0, Lp):
        r = cyl_x(D, C, zc).cut(cq.Solid.makeSphere(dk / 2, cq.Vector(0, 0, zc), angleDegrees1=-90, angleDegrees2=90))
        rings.append(r)
    return Lp, dog, rings, {"L_pr_mm": Lp, "eye_od": e_od, "eye_t": C, "bore": D, "shank": [4.0, 7.0], "dk": dk}


def run_case(X, conn, body, Lp, sense, intro, wd, tag):
    """sense 'T' (tension) / 'C' (compression); intro 'cos' (pressure) / 'rigid' (rigid half bore)."""
    Rk = 5.0
    on_sph = np.zeros(len(X), bool)
    centre_of = np.zeros(len(X))
    for zc in (0.0, Lp):
        d = np.linalg.norm(X - np.array([0.0, 0.0, zc]), axis=1)
        m = (np.abs(d - Rk) < 0.02) & (np.abs(X[:, 0]) <= 2.0 + 1e-6)
        on_sph |= m
        centre_of[m] = zc
    faces = fu.surface_faces(conn, on_sph)
    loads = []           # (elem, face, p)
    sets = {0.0: [], Lp: []}
    Fres = {0.0: np.zeros(3), Lp: np.zeros(3)}
    for (e, f) in faces:
        cn = [conn[e, k] for k in fu.TET_FACES[f]]
        zc = centre_of[cn[0]]
        # load direction on the rod at this eye: tension pulls the eye away from the shank
        out_dir = -1.0 if zc == 0.0 else 1.0                        # out-board direction (away from the shank) along z
        e_load = np.array([0.0, 0.0, out_dir if sense == "T" else -out_dir])
        cen = X[cn].mean(axis=0)
        n = (cen - np.array([0.0, 0.0, zc]))
        n /= np.linalg.norm(n)                                      # sphere normal, pointing into the ring material
        cosv = float(n @ e_load)
        if cosv <= 0.0:
            continue
        va = fu.face_vector_area(X, conn, e, f)
        if va @ n < 0:
            va = -va
        loads.append((e, f, cosv))
        Fres[zc] += cosv * va
        sets[zc].extend(cn + [conn[e, k] for k in fu.FACE_MID[f]])
    p0 = {zc: F / abs(Fres[zc][2]) for zc in Fres}
    # 3-2-1 support at the shank centre
    def near(p):
        return int(np.argmin(np.linalg.norm(X - np.asarray(p), axis=1)))
    n1, n2, n3 = near((0, 0, Lp / 2)), near((0, 0, Lp / 2 + 6.0)), near((0, 3.5, Lp / 2))
    job = f"rod_{tag}_{sense}_{intro}"
    with open(wd / f"{job}.inp", "w") as f:
        f.write(f"*HEADING\nGM-17 pushrod axial stiffness ({sense}, {intro}) rod_k.py v1\n*NODE, NSET=NALL\n")
        for q, x in enumerate(X):
            f.write(f"{q+1}, {x[0]:.6f}, {x[1]:.6f}, {x[2]:.6f}\n")
        for b, nm in ((0, "ROD"), (1, "RING1"), (2, "RING2")):
            f.write(f"*ELEMENT, TYPE=C3D10, ELSET=E_{nm}\n")
            for e in np.nonzero(body == b)[0]:
                f.write(f"{e+1}, " + ", ".join(str(int(n) + 1) for n in conn[e]) + "\n")
        f.write("*ELSET, ELSET=EALL\nE_ROD, E_RING1, E_RING2\n")
        f.write(f"*MATERIAL, NAME=AL7075\n*ELASTIC\n{E_ROD:.1f}, 0.33\n*MATERIAL, NAME=STEEL\n*ELASTIC\n{E_STEEL:.1f}, {NU_STEEL}\n")
        f.write("*SOLID SECTION, ELSET=E_ROD, MATERIAL=AL7075\n*SOLID SECTION, ELSET=E_RING1, MATERIAL=STEEL\n*SOLID SECTION, ELSET=E_RING2, MATERIAL=STEEL\n")
        f.write(f"*BOUNDARY\n{n1+1}, 1, 3\n{n2+1}, 1, 2\n{n3+1}, 1, 1\n")
        refs = {}
        if intro == "rigid":
            nid = len(X)
            for k_, zc in enumerate((0.0, Lp)):
                f.write(f"*NODE, NSET=NREF{k_}\n{nid+1}, 0, 0, {zc}\n{nid+2}, 0, 0, {zc}\n")
                f.write(f"*NSET, NSET=NB{k_}\n")
                fu.write_lines(f, sorted(set(int(x) + 1 for x in sets[zc])))
                f.write(f"*RIGID BODY, NSET=NB{k_}, REF NODE={nid+1}, ROT NODE={nid+2}\n")
                refs[zc] = nid + 1
                nid += 2
        f.write("*STEP\n*STATIC\n")
        if intro == "cos":
            f.write("*DLOAD\n")
            for (e, fc, cosv) in loads:
                zc = centre_of[conn[e, fu.TET_FACES[fc][0]]]
                f.write(f"{e+1}, P{fc}, {p0[zc] * cosv:.6e}\n")
        else:
            f.write("*CLOAD\n")
            for zc, nid_ in refs.items():
                out_dir = -1.0 if zc == 0.0 else 1.0
                f.write(f"{nid_}, 3, {F * (out_dir if sense == 'T' else -out_dir):.6f}\n")
        f.write(f"*NODE PRINT, NSET=NALL, TOTALS=ONLY\nRF\n*EL PRINT, ELSET=EALL, TOTALS=ONLY\nELSE\n*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n")
    r = fu.run_ccx(job, wd, threads=int(__import__('os').environ.get('OMP_NUM_THREADS', '1')))  # compute budget: <= 2 solver threads in total (lead 2026-10-12)
    if r["errors"]:
        raise RuntimeError(f"{job}: {r['errors'][:2]}")
    d = fu.parse_dat(wd / f"{job}.dat")
    t = sorted(d)[-1]
    U = d[t]["ETOT"]["EALL"]
    txt = (wd / f"{job}.dat").read_text()
    return {"job": job, "ccx": r, "U_Nmm": U, "k_N_mm": F ** 2 / (2 * U), "n_load_faces": len(loads),
            "F_resultant_check": {str(k): (p0[k] * Fres[k]).tolist() for k in Fres}}


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    Lp, dog, rings, geo = geometry()
    hs = [1.2, 0.8, 0.55]          # gmsh HighOrderOptimize 2 on every level (h 0.55 without it: nonpositive Jacobian, run kept in runs/stiff/rod_fail_h055)
    out = {"version": "v1", "date": "2026-10-12", "owner": "Mechanical", "script": "04-fea/stiffness/rod_k.py v1", "geometry": geo,
           "materials": {"rod": f"7075-T6 E {E_ROD:.0f} MPa nu 0.33 (engmat)", "GE_outer_ring": f"bearing steel E {E_STEEL:.0f} MPa nu {NU_STEEL} ASSUMED"},
           "F_N": F, "mesh_study": []}
    for h in hs:
        t0 = time.time()
        X, conn, body = fu.mesh_multi([dog] + rings, h, h / 4.0, name=f"rod_h{h:g}", workdir=RUNS)
        vol = fu.tet_volumes(X, conn)
        assert (vol > 0).all(), "inverted tets"
        row = {"h_mm": h, "nodes": int(len(X)), "tets": int(len(conn)), "t_mesh_s": round(time.time() - t0, 1),
               "body_tets": [int((body == b).sum()) for b in range(3)]}
        for sense in ("T", "C"):
            for intro in ("cos", "rigid"):
                res = run_case(X, conn, body, Lp, sense, intro, RUNS, f"h{h:g}")
                row[f"{sense}_{intro}"] = res
                print(h, sense, intro, round(res["k_N_mm"]), res["ccx"], flush=True)
        out["mesh_study"].append(row)
    fine = out["mesh_study"][-1]
    kT, kC = fine["T_cos"]["k_N_mm"], fine["C_cos"]["k_N_mm"]
    # Richardson-type check on the two finest meshes
    conv = {k: abs(out["mesh_study"][-1][k]["k_N_mm"] / out["mesh_study"][-2][k]["k_N_mm"] - 1.0) for k in ("T_cos", "C_cos", "T_rigid", "C_rigid")}
    k_bil = 4.0 * kT * kC / (math.sqrt(kT) + math.sqrt(kC)) ** 2
    out.update({"k_tension_N_mm": kT, "k_compression_N_mm": kC, "k_mean_N_mm": 0.5 * (kT + kC), "k_bilinear_equiv_N_mm": k_bil,
                "k_N_mm": kT, "k_used_note": "k_N_mm = TENSION value (lower; conservative for an axis whose rods load in the same sense, beta); "
                                             "alpha loads one rod in tension and the other in compression (mean)",
                "k_rigid_intro_tension_N_mm": fine["T_rigid"]["k_N_mm"], "k_rigid_intro_compression_N_mm": fine["C_rigid"]["k_N_mm"],
                "k_shank_only_EA_over_L_N_mm": E_ROD * 28.0 / Lp, "mesh_change_last_two": conv,
                "tag": "FEA CalculiX 2.21 C3D10 (gmsh OCC), bonded press fit, cosine contact pressure (rigid-half variant bounds it)"})
    (HERE / "rod_k_v1.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in out if k.startswith("k_")}, indent=1, default=float))


if __name__ == "__main__":
    main()
