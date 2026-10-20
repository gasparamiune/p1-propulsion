"""FEA3D J-FWD local seat sub-model (fea3d 2026-10-20 ~08:45Z; lead 08:17Z item (2): the mu 0.2 closure of the TC-01 under-head cell).

Why: the one-sector J-FWD model at mu 0.2 needs the unsymmetric SPOOLES LU (~2x the symmetric factor: > 8 GB cap); a local patch of the
same mesh round the head seat is small enough.  Condition (lead 08:17Z): first run the patch at mu 0 and show that it reproduces the
global run's under-head, hole-bearing and seat P+Q values at the same steps (within ~5 %; else enlarge the patch beyond +/-8 mm); then mu 0.2.

Patch (SIM, same mesh / numbering as the global job): the elements of the global model (model_<tag>.npz) whose centroid lies in the
screw-local box x' >= xcut, |y'| <= L, |z'| <= L (x' along the screw axis from the engine axis, y' tangential, z' axial; base L 8, xcut 26.0:
the TC-01 wall, the head and the shank, the TC-02 OD slab x' 26..28.6 with the outer 2.6 mm of the bonded thread).
  cut boundary  every patch node that also belongs to a removed element gets the global run's nodal displacement (u_x, u_y, u_z from the
                global .frd) per step; thread-tie pairs with a cut or missing partner are dropped and their patch nodes prescribed alike;
                symmetry-plane nodes that are not cut keep the symmetry BC (L 12 reaches the az 0 / 36 planes).
  screw         the pretension section (x' 30.2, REF node d1/d2/d3) lies inside the patch: SEAT d1 prescribed d1_seat (closes the 0.01 mm head
                gap with ~0.005 mm), boundary = s x U_PRELOAD (s = (d1_seat - 0.01) / (d1_PRELOAD - 0.01), the linear-compliance share, so
                the PRELOAD ramp is proportional); PRELOAD = *CLOAD on d1 (preload N) with the boundary at U_PRELOAD; then d1 FIXED (the
                installation stretch locked, as in the global deck).
  contact       HEAD / BEAR / FIT pairs restricted to the patch faces, same penalty (5e5) and FIT clearance as the global deck;
                mu 0 or Coulomb mu with stick slope 1e4 MPa/mm on all three pairs.
  loads         temperatures exactly as the global deck (mapped S-AX fields recomputed by jfwd_deck.mapped_temps, uniform rows);
                chamber pressure on any wetted global face inside the patch (none for L 8 / xcut 26: checked and printed).
  steps         SEAT, PRELOAD, then the global run's states in the physical order SOAK52 (51.7 s), SOAK (64.7 s row means), SOAK70 (70.7 s),
                FA1S (a later firing at 45.6 C after the soak): at mu 0 the states are path independent (reproduction check); at mu 0.2 the
                friction state follows this history (stated in the report).
  remesh mode   (fea3d 2026-10-20 ~11:15Z, (b2)/(b1) on mesh s6 with the TC-01 hole edge break R0.2 / 0.1x45): pmesh=<tag> selects the
                patch on ANOTHER mesh (model_<pmesh>.npz, same box) and the prescribed nodes take the global field interpolated in the
                global run's elements of the SAME body (quadratic C3D10 shape functions at the node's barycentric coordinates, jfwd_post.
                Locator; nodes outside the global body's faceted volume take the nearest element's extrapolation, the distance is
                recorded).  Thread pairs and the pretension section are the patch mesh's own.  The global d1 (pretension stretch) per step
                is the global run's.
usage: jfwd_seat.py build GJOB STAG L=8 xcut=26.0 [pmesh=TAG] -> jfwd/seat_STAG.npz/.json (patch sets, sizes, checks)
       jfwd_seat.py deck GJOB STAG JOB mu=0 [d1_seat=0.015] [seat_out=0|1] [end_only=0|1] [order=S1,S2,..]
                                                              -> jfwd/runs/JOB/JOB.inp + meta.json (needs the global .frd complete)
       jfwd_seat.py compare JOB                              -> jfwd/runs/JOB/compare.json (patch vs global on the same node / line sets)
"""
from __future__ import annotations
import sys, json, math, hashlib, gzip, time
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS          # noqa: E402
import jfwd_deck as JD         # noqa: E402
import jfwd_post as JP         # noqa: E402

OUT = JD.OUT
RUNS = JD.RUNS
TK = 273.15
ORDER = ["SOAK52", "SOAK", "SOAK70", "FA1S"]


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def select(m, L, xcut):
    X, T = m["X"], m["T"]
    C = X[T[:, :4]].mean(1)
    xa, ya, za, _ = JD.loc(C)
    return (xa >= xcut) & (np.abs(ya) <= L) & (np.abs(za) <= L)


def build(gjob, stag, L=8.0, xcut=26.0, pmesh=None):
    gm = json.loads((RUNS / gjob / "meta.json").read_text())
    gtag = gm["mesh"]
    tag = pmesh or gtag
    JS.use_mesh(tag)
    m = dict(np.load(OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
    keep = select(m, L, xcut)
    Nk = np.unique(T[keep])
    Nr = np.unique(T[~keep])
    cut = np.intersect1d(Nk, Nr)
    inK = np.zeros(len(X), bool)
    inK[Nk] = True
    isC = np.zeros(len(X), bool)
    isC[cut] = True
    # thread-tie pairs (a = screw-side duplicate, b = TC-02 node)
    a, b = m["new_thr"], m["thr"]
    pair_in = inK[a] & inK[b] & ~isC[a] & ~isC[b]
    pair_drop = (inK[a] | inK[b]) & ~pair_in
    pres = set(cut.tolist())
    for arr in (a[pair_drop], b[pair_drop]):
        pres.update(int(v) for v in arr if inK[v])
    # pretension section pairs: must be interior
    sa, sb = m["new_sec"], m["sec"]
    assert inK[sa].all() and inK[sb].all() and not isC[sa].any() and not isC[sb].any(), "pretension section cut by the patch"
    # symmetry planes: non-cut patch nodes keep the symmetry BC
    y0 = np.array([v for v in m["y0"] if inK[v] and v not in pres], np.int64)
    y36 = np.array([v for v in m["y36"] if inK[v] and v not in pres], np.int64)
    assert not inK[m["ncut"]].any(), "aft cut inside the patch"
    assert not inK[m["springs"]].any(), "TC-02 ground springs inside the patch"
    pres = np.array(sorted(pres), np.int64)
    # faces
    fk_keep = keep[m["fe"]]
    faces = {k: np.nonzero(m[k] & fk_keep)[0] for k in ("head_s", "head_m", "bear_s", "bear_m", "fit_s", "fit_m")}
    wet_p = np.nonzero((m["wet"] > 0) & fk_keep)[0]
    assert not (m["cbw"] & fk_keep).any() and not (m["m14"] & fk_keep).any(), "cap / M14 traction faces inside the patch"
    # free-surface check: patch boundary faces that are neither global boundary faces nor fully prescribed would be new free surfaces
    sel = {"global_job": gjob, "mesh": tag, "L_mm": L, "xcut_mm": xcut, "n_elem": int(keep.sum()), "n_elem_global": int(len(T)),
           "n_nodes": int(len(Nk)) + 1, "n_nodes_global": int(len(np.unique(T))) + 1, "n_cut_nodes": int(len(cut)),
           "n_prescribed_nodes": int(len(pres)), "thread_pairs_kept": int(pair_in.sum()), "thread_pairs_dropped": int(pair_drop.sum()),
           "section_pairs": int(len(sa)), "sym0_nodes_bc": int(len(y0)), "sym36_nodes_eq": int(len(y36)),
           "per_body_elem": {bb: int((keep & (B == bb)).sum()) for bb in ("TC-01", "TC-02", "SCREW")},
           "contact_faces": {k: [int(len(v)), int(m[k].sum())] for k, v in faces.items()},
           "contact_area_mm2": {k: [round(float(m["area"][v].sum()), 3), round(float(m["area"][m[k]].sum()), 3)] for k, v in faces.items()},
           "wetted_faces_in_patch": int(len(wet_p)), "wetted_area_in_patch_mm2": round(float((m["area"] * m["wet"])[wet_p].sum()), 3)}
    extra = {}
    if tag != gtag:
        # remesh mode: interpolation of the global field at the prescribed nodes, body by body
        mg = dict(np.load(OUT / f"model_{gtag}.npz", allow_pickle=False))
        Xg, Tg, Bg = mg["X"], mg["T"], mg["B"]
        body = np.full(len(X), "", dtype=object)
        for bb, key in (("TC-01", "n01"), ("TC-02", "n02"), ("SCREW", "nsc")):
            body[m[key]] = bb
        iel = -np.ones(len(pres), np.int64)
        iN = np.zeros((len(pres), 10))
        ibest = np.zeros(len(pres))
        idist = np.zeros(len(pres))
        for bb in ("TC-01", "TC-02", "SCREW"):
            k = np.nonzero(body[pres] == bb)[0]
            if not len(k):
                continue
            eg = np.nonzero(Bg == bb)[0]
            loc = JP.Locator(Xg, Tg[eg])
            el, Lb, best = loc.bary(X[pres[k]], k=128)
            L1, L2, L3, L4 = Lb.T
            iN[k] = np.column_stack([L1 * (2 * L1 - 1), L2 * (2 * L2 - 1), L3 * (2 * L3 - 1), L4 * (2 * L4 - 1),
                                     4 * L1 * L2, 4 * L2 * L3, 4 * L1 * L3, 4 * L1 * L4, 4 * L2 * L4, 4 * L3 * L4])
            iel[k] = eg[el]
            ibest[k] = best
            # distance outside the element (0 inside): |P - projection| approximated by the negative barycentric times the element size
            h = np.cbrt(1.414 * np.abs(np.linalg.det(np.stack([Xg[Tg[eg[el], 1]] - Xg[Tg[eg[el], 0]], Xg[Tg[eg[el], 2]] - Xg[Tg[eg[el], 0]],
                                                        Xg[Tg[eg[el], 3]] - Xg[Tg[eg[el], 0]]], 2))))
            idist[k] = np.where(best < 0, -best * h, 0.0)
        assert (iel >= 0).all(), "remesh: prescribed node without a global element"
        extra = {"interp_el": iel, "interp_N": iN, "interp_best": ibest}
        sel["remesh"] = {"global_mesh": gtag, "patch_mesh": tag, "n_interp": int(len(pres)), "n_outside_global_element": int((ibest < -1e-9).sum()),
                         "min_bary": round(float(ibest.min()), 4), "max_extrap_dist_mm_est": round(float(idist.max()), 4),
                         "n_extrap_gt_0p01mm": int((idist > 0.01).sum())}
    np.savez_compressed(OUT / f"seat_{stag}.npz", keep=keep, nodes=Nk, cut=cut, pres=pres, pair_in=pair_in, y0=y0, y36=y36, wet=wet_p,
                        **{f"f_{k}": v for k, v in faces.items()}, **extra)
    (OUT / f"seat_{stag}.json").write_text(json.dumps(sel, indent=1))
    print(json.dumps(sel, indent=1))
    return sel


def global_states(gjob, n):
    """{step name: U (n,3)} of the global job's .frd (all frd steps) + the dat d1 per step."""
    wd = RUNS / gjob
    gm = json.loads((wd / "meta.json").read_text())
    frd = wd / f"{gjob}.frd"
    if frd.exists():
        by = JP.read_frd_steps(frd, n)
    else:
        JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)
        try:
            by = JP.read_frd_steps(frd, n)
        finally:
            del JP.open
    names = gm["steps"]
    U = {nm: by[k + 1]["DISP"][:, :3] for k, nm in enumerate(names) if (k + 1) in by}
    dat = JP.read_dat(wd / f"{gjob}.dat")
    last = {}
    for d in dat:
        last[round(d["time"], 6)] = d
    d1 = {nm: last[float(k + 1)]["U"][0] for k, nm in enumerate(names) if float(k + 1) in last}
    return gm, U, d1, (sha16(frd) if frd.exists() else sha16(str(frd) + ".gz"))


def write_deck(gjob, stag, job, mu=0.0, d1_seat=0.015, seat_out=True, end_only=False, order=None):
    """order: the states after PRELOAD (default ORDER, the physical soak order; (a') 11:40Z = the global run's order, the history check);
    an entry LABEL:BASE repeats the global state BASE under the step name LABEL (lead 11:41Z (b2) form (A): SOAK after FA1S, SOAK52 after
    SOAK in the same run = the in-run history check); meta step_base / step_after record the mapping and the predecessor.
    seat_out False: no field output at the SEAT step; end_only True: field output only at the end of each step (FREQUENCY=1000: ccx 2.21 still
    writes the last increment of every step, tested 11:28Z; a mu 0.2 patch takes >= 4 increments per step and ccx writes every increment by
    default: disk) - fea3d 11:15Z / 11:28Z."""
    sel = json.loads((OUT / f"seat_{stag}.json").read_text())
    S = dict(np.load(OUT / f"seat_{stag}.npz", allow_pickle=False))
    gm = json.loads((RUNS / gjob / "meta.json").read_text())
    gtag = gm["mesh"]
    tag = sel.get("mesh", gtag)
    mj0 = JS.use_mesh(tag)
    m = dict(np.load(OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
    ref = int(m["ref"][0])
    keep, Nk, pres = S["keep"], S["nodes"], S["pres"]
    if tag != gtag:
        mg = np.load(OUT / f"model_{gtag}.npz", allow_pickle=False)
        Tg = mg["T"]
        gmeta, Ug, d1, gsha = global_states(gjob, len(mg["X"]))
        U = {}
        for st_, u in Ug.items():
            up = np.zeros((len(X), 3))
            up[pres] = np.einsum("nk,nkj->nj", S["interp_N"], u[Tg[S["interp_el"]]])
            U[st_] = up
    else:
        gmeta, U, d1, gsha = global_states(gjob, len(X))
    ORD0 = list(order) if order else list(ORDER)
    ORD = [o.split(":", 1)[0] for o in ORD0]
    BASE = {o.split(":", 1)[0]: (o.split(":", 1)[1] if ":" in o else o) for o in ORD0}
    assert len(set(ORD)) == len(ORD), "step labels must be unique"
    AFTER = {lab: prev for prev, lab in zip(["PRELOAD"] + ORD[:-1], ORD)}
    need = ["PRELOAD"] + sorted(set(BASE.values()))
    miss = [s for s in need if s not in U]
    if miss:
        raise RuntimeError(f"global job {gjob}: frd steps missing {miss}")
    g = JS.GEO["head_gap"]
    s_seat = (d1_seat - g) / (d1["PRELOAD"] - g)
    wd = RUNS / job
    wd.mkdir(parents=True, exist_ok=True)
    f = open(wd / f"{job}.inp", "w")
    w = f.write
    w(f"*HEADING\nFEA3D J-FWD local seat sub-model {stag} (L {sel['L_mm']}, xcut {sel['xcut_mm']}) of {gjob}: mu {mu}, preload {gm['preload_N']} N, "
      f"fit {gm.get('FIT_clearance_mm')} mm, steps SEAT,PRELOAD,{','.join(ORD)}\n")
    w("*NODE, NSET=NALL\n")
    for i in list(Nk) + [ref]:
        x = X[i]
        w(f"{i + 1}, {x[0]:.7f}, {x[1]:.7f}, {x[2]:.7f}\n")
    for bname, bb in (("TC01", "TC-01"), ("TC02", "TC-02"), ("SCR", "SCREW")):
        w(f"*ELEMENT, TYPE=C3D10, ELSET=E_{bname}\n")
        for e in np.nonzero(keep & (B == bb))[0]:
            w(f"{e + 1}, " + ", ".join(str(int(v) + 1) for v in T[e]) + "\n")
    inK = np.zeros(len(X), bool)
    inK[Nk] = True
    n01, n02, nsc = (m[k][inK[m[k]]] for k in ("n01", "n02", "nsc"))
    w(JD.lines_set("N_TC01", n01) + JD.lines_set("N_TC02", n02) + JD.lines_set("N_SCR", nsc))
    w(JD.lines_set("N_REF", [ref]))
    if len(S["y0"]):
        w(JD.lines_set("N_SYM0", S["y0"]))
    w(JD.mat_al() + JD.mat_screw())
    w("*SOLID SECTION, ELSET=E_TC01, MATERIAL=AL\n*SOLID SECTION, ELSET=E_TC02, MATERIAL=AL\n*SOLID SECTION, ELSET=E_SCR, MATERIAL=A480\n")
    w("*EQUATION\n")
    for nd in S["y36"]:
        w(f"2\n{int(nd) + 1}, 2, {JD.C36:.9f}, {int(nd) + 1}, 1, {-JD.S36:.9f}\n")
    for a, b in zip(m["new_thr"][S["pair_in"]], m["thr"][S["pair_in"]]):
        for i in (1, 2, 3):
            w(f"2\n{int(a) + 1}, {i}, 1.0, {int(b) + 1}, {i}, -1.0\n")
    R = ref + 1
    EN, ET1 = JD.EN, JD.ET1
    for a, b in zip(m["new_sec"], m["sec"]):
        A_, B_ = int(a) + 1, int(b) + 1
        w(f"4\n{A_}, 1, 1.0, {B_}, 1, -1.0, {R}, 1, {EN[0]:.9f}, {R}, 2, {ET1[0]:.9f}\n")
        w(f"4\n{A_}, 2, 1.0, {B_}, 2, -1.0, {R}, 1, {EN[1]:.9f}, {R}, 2, {ET1[1]:.9f}\n")
        w(f"3\n{A_}, 3, 1.0, {B_}, 3, -1.0, {R}, 3, 1.0\n")
    for nm, s_, mm in (("HEAD", "head_s", "head_m"), ("BEAR", "bear_s", "bear_m"), ("FIT", "fit_s", "fit_m")):
        fs, fm = S[f"f_{s_}"], S[f"f_{mm}"]
        w(JD.surface(f"S_{nm}_S", m["fe"][fs], m["fk"][fs]))
        w(JD.surface(f"S_{nm}_M", m["fe"][fm], m["fk"][fm]))
        w(f"*CONTACT PAIR, INTERACTION=SI, TYPE=SURFACE TO SURFACE\nS_{nm}_S, S_{nm}_M\n")
    w(f"*CLEARANCE, MASTER=S_FIT_M, SLAVE=S_FIT_S, VALUE={gm.get('FIT_clearance_mm', JD.FIT_CLEARANCE)}\n")
    w(f"*SURFACE INTERACTION, NAME=SI\n*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR\n{JD.K_PEN:.3e}\n")
    if mu > 0:
        w(f"*FRICTION\n{mu}, {JD.STICK:.3e}\n")
    w(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {JD.A3.T_REF}\n")
    mj = json.loads((OUT / f"mesh_{tag}.json").read_text())
    mapstats = {}

    def temps(tc):
        if isinstance(tc, (list, tuple)):
            Tn, stt = JD.mapped_temps(m, mj["shift"], tc[1], tc[2])
            mapstats[f"{tc[1]}:{tc[2]}"] = {k: stt[k] for k in ("res_npz_sha16", "row_mean_C")}
            return "*TEMPERATURE\n" + "".join(f"{i + 1}, {Tn[i]:.3f}\n" for i in Nk)
        return f"*TEMPERATURE\nN_TC01, {tc['TC-01'] + TK:.2f}\nN_TC02, {tc['TC-02'] + TK:.2f}\nN_SCR, {tc['SCREW'] + TK:.2f}\n"

    def ubc(Ust, scale=1.0):
        return "".join(f"{int(n) + 1}, {k + 1}, {k + 1}, {scale * Ust[n, k]:.6e}\n" for n in pres for k in range(3))

    def bcs():
        return ("N_SYM0, 2, 2\n" if len(S["y0"]) else "") + "N_REF, 2, 3\n"
    tp = ", FREQUENCY=1000" if end_only else ""     # 11:28Z test (scratchpad tptest): ccx 2.21 writes the LAST increment of every step at FREQUENCY > n_inc
    out_req = f"*NODE PRINT, NSET=N_REF\nU\n*NODE FILE{tp}\nU\n*EL FILE{tp}\nS\n*CONTACT FILE{tp}\nCDIS, CSTR\n"
    dinc = 1.0 if mu == 0 else 0.25
    inc = "*STEP, INC=400\n*STATIC\n{0}, 1.0, 1e-6, {1}\n"
    # SEAT
    w(inc.format(0.5, 1.0) + "*BOUNDARY\n" + bcs() + ubc(U["PRELOAD"], s_seat) + f"N_REF, 1, 1, {d1_seat}\n" + temps(JD.U(20.0)))
    w((out_req if seat_out else "*NODE PRINT, NSET=N_REF\nU\n") + "*END STEP\n")
    # PRELOAD
    w(inc.format(dinc, dinc) + "*BOUNDARY, OP=NEW\n" + bcs() + ubc(U["PRELOAD"]) + f"*CLOAD\nN_REF, 1, {gm['preload_N']}\n" + temps(JD.U(20.0)) + out_req + "*END STEP\n")
    first = True
    wet = S["wet"]
    for st in ORD:
        pc, tc, _ = gm["step_defs"][BASE[st]]
        w(inc.format(dinc, dinc))
        if first:
            w("*BOUNDARY, FIXED\nN_REF, 1, 1\n")
            first = False
        w("*BOUNDARY\n" + ubc(U[BASE[st]]))
        w("*CLOAD, OP=NEW\n*DLOAD, OP=NEW\n")      # removes the PRELOAD *CLOAD on d1 (d1 FIXED), as the global deck
        if pc > 0:
            for i in wet:
                w(f"{int(m['fe'][i]) + 1}, P{int(m['fk'][i])}, {pc * m['wet'][i]:.6e}\n")
        w(temps(tc) + out_req + "*END STEP\n")
    f.close()
    meta = {"job": job, "kind": "seat_submodel", "global_job": gjob, "global_frd_sha16": gsha, "global_deck_sha16": gm.get("deck_sha16"),
            "seat_tag": stag, "mesh": tag, "L_mm": sel["L_mm"], "xcut_mm": sel["xcut_mm"], "mu": mu, "preload_N": gm["preload_N"],
            "steps": ["SEAT", "PRELOAD"] + ORD, "step_defs": {s: gm["step_defs"][BASE[s]] for s in ORD},
            "step_base": {s: BASE[s] for s in ORD if BASE[s] != s}, "step_after": AFTER, "K_pen": JD.K_PEN, "stick": JD.STICK,
            "FIT_clearance_mm": gm.get("FIT_clearance_mm"), "seat": JS.GEO.get("seat"), "x_seat": JS.GEO.get("x_seat"),
            "d1_seat_mm": d1_seat, "s_seat": round(s_seat, 5), "d1_global_mm": d1, "mapped_fields": mapstats, "selection": sel,
            "increments": dinc, "TC01_step_sha16": mj0.get("TC01_step_sha16"),
            "seat_field_output": bool(seat_out), "end_only_output": bool(end_only), "global_mesh": gtag,
            "deck_sha16": sha16(wd / f"{job}.inp")}
    (wd / "meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("job", "mu", "L_mm", "xcut_mm", "s_seat", "d1_global_mm", "deck_sha16")}))
    return wd


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        kw = dict(a.split("=", 1) for a in sys.argv[4:])
        build(sys.argv[2], sys.argv[3], float(kw.get("L", 8.0)), float(kw.get("xcut", 26.0)), kw.get("pmesh"))
    elif cmd == "deck":
        kw = dict(a.split("=", 1) for a in sys.argv[5:])
        write_deck(sys.argv[2], sys.argv[3], sys.argv[4], float(kw.get("mu", 0.0)), float(kw.get("d1_seat", 0.015)),
                   kw.get("seat_out", "1") == "1", kw.get("end_only", "0") == "1", kw["order"].split(",") if kw.get("order") else None)
    elif cmd == "compare":
        import jfwd_seat_cmp
        jfwd_seat_cmp.compare(sys.argv[2])
