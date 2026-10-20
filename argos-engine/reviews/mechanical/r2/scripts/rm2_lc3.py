"""REV-MECH-2 (independent reviewer): own re-post of FEA3D LC3 (8 deg stop, runaway) and F2 GS (servo stall) from stored unit fields.

LC3 (REPORT-FEA3D 2.3 / post_lc3 docstring, re-implemented): OP x 2.501 MPa + 6.29 g lateral (8 dirs) + GZ {0, 5.43 g} + 79.28 rad/s2
about the (EAX, EAY) direction that extremises the rods' moment into the stop (2 signs) + bumper force {0, fb_run}; fb_run = the largest
fb with actuator moment into the stop <= 41.14 N m and each |rod| <= 609 N.  COLD (no TH step); allowables at the B1_21.65 node T.
GS (S-3D, re-implemented): rods at (+/-F_d, +/-F_d) via EAX/EAY + OP Pc_max + lateral (0.61 g + hose-equivalent g) 8 dirs + GZ {0, 4.04}.
Rod forces from the stored displacements and the SPRINGA definition in the solved deck (k (u_aux - u_H) . e, aux tied to the lever eye).

usage: python -I rm2_lc3.py LC3 <run> <base_run_for_rod_geom> <out.json>
       python -I rm2_lc3.py GS <run> <F_d N> <g_hose> <out.json>
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rm2_repost as RP  # noqa: E402  (own module)

RUNS = RP.RUNS
STATE = "B1_21.65"


def rods_from_deck(meta, z, X):
    """SPRINGA rod elements: the two springs with k = k_chain (11418.2 N/mm) -> (n1, n2, k, e12)."""
    ks = meta["spring_k"]
    out = []
    for eid, n1, n2, es in meta["springs"]:
        k = ks[es]
        if abs(k - 11418.21) < 1.0:
            d = X[n2] - X[n1]
            out.append((int(n1), int(n2), float(k), d / np.linalg.norm(d)))
    return out


def rod_tension(F, st, rods):
    return np.array([k * (F[f"U_{st}"][n2] - F[f"U_{st}"][n1]) @ e for n1, n2, k, e in rods])


def main_lc3(run, base, outp):
    t0 = time.time()
    z, meta = RP.load_deck(run, STATE)
    mesh = RP.Mesh(z, meta)
    model = json.loads((RUNS / run / "model.json").read_text())
    rg = model.get("rod_geom") or json.loads((RUNS / base / "model.json").read_text())["rod_geom"]
    F = dict(np.load(RUNS / run / STATE / "fields.npz"))
    steps = [k[2:] for k in F if k.startswith("U_")]
    T = np.full(len(mesh.X), 293.15)
    Tz = np.load(RUNS / run / STATE / "T.npz")        # COLD run: no TH step in the deck; allowable temperatures from T.npz (per body)
    for nm in mesh.names:
        nodes = mesh.bodies[nm]["nodes"]
        T[nodes] = Tz[nm]
    rods = rods_from_deck(meta, z, mesh.X)
    Rg = {k: np.asarray(v) for k, v in model["Rg"].items()}
    aX, aY = np.array([1.0, 0, 0]), Rg["ring"] @ np.array([0, 1.0, 0])
    A = np.zeros((2, 2))
    order = sorted(rg, key=int)
    # rod order in the deck = servo order (H nodes ascending), as in the model bush list
    for j, i in enumerate(order):
        xL, e = np.asarray(rg[i]["lever_eye"]), np.asarray(rg[i]["e_push_on_engine"])
        m = np.cross(xL, -e)
        A[:, j] = [m @ aX, m @ aY]
    s = {st: rod_tension(F, st, rods) for st in steps}
    Q = {st: A @ s[st] for st in steps}
    bu = model["bumper"]
    xc, nout = np.asarray(bu["contact_point_mm"]), np.asarray(bu["n_out"])
    mb = np.cross(xc, -nout)
    Qb = np.array([mb @ aX, mb @ aY])
    QB = Q["BUMP"]
    u = QB / np.linalg.norm(QB)
    eq_res = float(np.linalg.norm(QB + Qb) / np.linalg.norm(Qb))
    qx, qy = Q["EAX"] @ u, Q["EAY"] @ u
    psi = math.atan2(qy, qx)
    subs, info = [], []
    for k in range(8):
        ph = 2 * math.pi * k / 8
        for gz in (0.0, 5.43):
            for sg in (1.0, -1.0):
                co = {"OP": RP.PC_MAX, "GX": 6.29 * math.cos(ph), "GY": 6.29 * math.sin(ph), "GZ": gz,
                      "EAX": sg * 79.28 * math.cos(psi), "EAY": sg * 79.28 * math.sin(psi)}
                QL = sum(c * Q[st] for st, c in co.items())
                tL = sum(c * s[st] for st, c in co.items())
                lims = [(41.14e3 - QL @ u) / np.linalg.norm(QB)]
                for j_ in range(2):
                    sb = s["BUMP"][j_]
                    if abs(sb) > 1e-9:
                        lims.append(((-609.0 if sb < 0 else 609.0) - tL[j_]) / sb)
                fb = max(min(lims), 0.0)
                for f_ in (0.0, fb):
                    subs.append(dict(co, BUMP=f_))
                    t = tL + f_ * s["BUMP"]
                    info.append({"fb": float(f_), "rods_N": t.tolist(), "act_moment_into_stop_Nm": float((A @ t) @ u / 1e3)})
    S_, rep = RP.singular_sets(mesh, model, z)
    reg, dist, cls = RP.regular_mask(mesh, S_)
    sets = {"all": np.ones(mesh.n_mesh + 1, bool), "regular": reg}
    parts = RP.margins(mesh, F, T, subs, 1.5, 2.0, sets, cls, dist)
    out = {"run": run, "case": "LC3", "n_subcases": len(subs), "psi_deg": math.degrees(psi), "eq_residual_rel": eq_res,
           "fb_run_range_N": [min(i["fb"] for i in info[1::2]), max(i["fb"] for i in info[1::2])],
           "rod_max_abs_N": float(max(max(abs(x) for x in i["rods_N"]) for i in info)),
           "act_moment_max_Nm": float(max(i["act_moment_into_stop_Nm"] for i in info)),
           "parts": parts, "subcases": subs, "info": info, "n_regular": int(reg.sum())}
    Path(outp).write_text(json.dumps(out, indent=1, default=float))
    for p in ("GM-01", "GM-02", "GM-16a", "GM-16b", "NZ-03", "TC-01", "GM-03"):
        if p in parts:
            r = parts[p]["regular"]
            a = parts[p]["all"]
            print(f"{run} {p}: reg {r['MS']:+.3f} / {r.get('MS_u', float('nan')):+.3f} vm {r['vm']} node {r['node']} {r['r_th_z']}; "
                  f"all {a['MS']:+.3f} vm {a['vm']} ({a['nearest_singular_class']} {a['dist_to_singular_mm']})")
    print(f"fb_run {out['fb_run_range_N']}, rods max {out['rod_max_abs_N']:.1f} N, act moment max {out['act_moment_max_Nm']:.2f} N m, "
          f"eq residual {eq_res:.2e}, {time.time() - t0:.1f} s")


def main_gs(run, fd, g_hose, outp):
    t0 = time.time()
    z, meta = RP.load_deck(run, STATE)
    mesh = RP.Mesh(z, meta)
    model = json.loads((RUNS / run / "model.json").read_text())
    F = dict(np.load(RUNS / run / STATE / "fields.npz"))
    steps = [k[2:] for k in F if k.startswith("U_")]
    T = np.full(len(mesh.X), 293.15)
    Tz = np.load(RUNS / run / STATE / "T.npz")
    for nm in mesh.names:
        T[mesh.bodies[nm]["nodes"]] = Tz[nm]
    rods = rods_from_deck(meta, z, mesh.X)
    s = {st: rod_tension(F, st, rods) for st in steps}
    S2 = np.column_stack([s["EAX"], s["EAY"]])
    subs, info = [], []
    for k in range(8):
        ph = 2 * math.pi * k / 8
        for gz in (0.0, 4.04):
            for c1 in (1, -1):
                for c2 in (1, -1):
                    co = {"OP": RP.PC_MAX, "GX": (0.61 + g_hose) * math.cos(ph), "GY": (0.61 + g_hose) * math.sin(ph), "GZ": gz}
                    tL = sum(c * s[st] for st, c in co.items())
                    ea = np.linalg.solve(S2, np.array([c1 * fd, c2 * fd]) - tL)
                    co.update({"EAX": float(ea[0]), "EAY": float(ea[1])})
                    subs.append(co)
                    t = sum(c * s[st] for st, c in co.items())
                    info.append({"rods_N": t.tolist(), "ang_acc": float(np.hypot(*ea))})
    S_, rep = RP.singular_sets(mesh, model, z)
    reg, dist, cls = RP.regular_mask(mesh, S_)
    sets = {"all": np.ones(mesh.n_mesh + 1, bool), "regular": reg}
    parts = RP.margins(mesh, F, T, subs, 1.5, 2.0, sets, cls, dist)
    out = {"run": run, "case": "GS", "F_d": fd, "g_hose": g_hose, "parts": parts, "info": info, "n_regular": int(reg.sum()),
           "ang_acc_range": [min(i["ang_acc"] for i in info), max(i["ang_acc"] for i in info)]}
    Path(outp).write_text(json.dumps(out, indent=1, default=float))
    for p in ("GM-01", "GM-02", "GM-16a", "GM-16b", "TC-01", "GM-03"):
        r = parts[p]["regular"]
        a = parts[p]["all"]
        print(f"{run} GS {p}: reg {r['MS']:+.3f} / {r.get('MS_u', float('nan')):+.3f} vm {r['vm']} node {r['node']} {r['r_th_z']}; "
              f"all {a['MS']:+.3f} vm {a['vm']} ({a['nearest_singular_class']} {a['dist_to_singular_mm']})")
    print(f"ang acc {out['ang_acc_range']}, {time.time() - t0:.1f} s")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "LC3":
        main_lc3(a[1], a[2], a[3])
    else:
        main_gs(a[1], float(a[2]), float(a[3]), a[4])
