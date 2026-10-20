"""T-F2 rev 4: TC-02 / TC-03 seat contact SUB-MODEL of the S-AX v352r4 L1 model (Mechanical, 2026-10-20, v1).  CALC / SIM, not physical
approval; negatives SHOWN AS FOUND.  Requests: lead CHANGELOG 212 (T-F2 / RM1-03), 234 (4) (all-node rule, refinement), 236 (9) (C5 / C7
bracket, stick-edge class, seat-matrix rule, C7 active set), 236 (10)-(11) (rev 4 seat, rev-4 thermal), lead 06:05Z / 06:23Z / 08:25Z /
08:40Z ('Proceed: T-F2 rev 4, then the (b) package').

Port of v352/contact/sax_contact_tc0203_sub_v352.py (rev 3, sha256/16 d856077b6adf78cb; its deck writer, sub-model cut and face finder
are imported and used unchanged).  Rev-4 changes:
  * global model = S-AX v352r4 (SAX_CAD=v352r4, SAX_R10=free, SAX_ENTRY_H level tag, rev-4 thermal SAX_THERMAL_TAG=v352_NF2b_R4_<bound>);
    trimmed global states read through sax.load_res_any (finite on every sub-model node, asserted);
  * rev-4 interface (80 shared node pairs, all u_z-tied in S-AX): 57 pairs on the M14x1 band at r 7.0 (z thread start .. thread end,
    smeared thread: the u_z tie is the thread interlock in every variant) and 23 pairs on the counterbore floor z_fl1 (TC-03 flange top =
    datum A = S03 lands, r 7.5 .. 10.0).  The top gap (0.15 nominal), the flange-OD clearance (0.10 radial) and the seat-entry cavity
    have no shared nodes (two-stage fragment): an unpaired-proximity check reports whether any of them closes;
  * variants: C0 S-AX ties (sub-model check), C5 frictionless (floor normal contact, thread radial contact), C7 = C5 + radial stick tie
    on the floor pairs CLOSED in the previous solution (active set, from the C5 solution, iterated to a stable set, cap 5 passes; if it
    does not settle, the last two passes are kept and the lower value is taken per cell: lead 236 (9)(c)), C6 bonded (information),
    C3n / C4n node-to-surface Coulomb mu 0.2 / 0.6;
  * margins per part on the seat window, for every set: case SF (lead 188 (9) rule as sax.combos: LC1 / LC2 / TB70 1.5 / 2.0, TBS
    1.0 / 1.5) AND SF 1.0 yield (line 106 'no yield at Fty(T)'); primary-only on the mechanical increment (step 2 - step 1);
    nodal P+Q vs 2 Fty(T) on the total stress (stress-free at 20 C);
  * singular set (234 (4)): BREP zero-radius concave corners (facet turn > 60 deg) of TC-02 / TC-03 and the named idealisation points
    (thread tie ends; floor contact edge at the TC-03 flange OD zero-radius corner; in C0 / C6 the floor tie end at the entry tangent);
    fillets (entry R0.5, undercut R0.6, relief R0.5, blend R0.25) are NOT excluded (S-AX's 10 deg detector flags the relief facets at
    h 0.1; not used here); 'regular' = farther than 1.0 mm from the singular set; every cell carries the all-node minimum with node,
    class and distance; the C7 stick-edge zone is set by the refinement post (tf2_r4_refine_v352.py) from the SAX_ENTRY_H levels;
  * per-run fields (TC-02 / TC-03 sub-model nodes, float32) kept for the refinement post; decks gzipped; frd deleted after reading;
  * caps (lead): <= 1 ccx of mine (sequential), <= 2 machine-wide, combined ccx RSS <= 9 GB, nice >= 10 (the caller), 1 solver thread,
    no new ccx below the disk floor (SUB_DISK_FLOOR_MB, default 2048): HOLD = exit 3, never routed around.
v1.1 (2026-10-20 ~09:00Z): the C7 loop stops when the active set alternates with period 2 (the closed set after pass k equals the stuck set
of pass k-1, so pass k+1 would repeat pass k-1 exactly): reported as 'unsettled, period-2 cycle', lower of the two passes per cell (the
lead 236 (9)(c) rule; results identical to running on to the cap); every run row records the script sha256/16 it ran with.
Usage: python sax_contact_tc0203_sub_v352r4.py <variants,...> <case:state,...>   (variants from C0,C5,C7,C6,C3n,C4n)"""
from __future__ import annotations
import os, sys, json, math, time, hashlib, subprocess, gzip, shutil
from pathlib import Path
os.environ.setdefault("SAX_CAD", "v352r4")
os.environ.setdefault("SAX_R10", "free")
os.environ.setdefault("SAX_TB_ABORTS", "165,150,135,120,105")
assert os.environ["SAX_CAD"] == "v352r4" and os.environ["SAX_R10"] == "free", "rev-4 driver: SAX_CAD=v352r4, SAX_R10=free"
assert os.environ.get("SAX_THERMAL_TAG", "").startswith("v352_NF2b_R4_"), "set SAX_THERMAL_TAG=v352_NF2b_R4_<GVLO|GVHI>"
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/structural")
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
sys.path.insert(0, "/home/claude/work/mechanical/v352/contact")
import numpy as np
import sax
import sax_contact_tc0203_sub_v352 as base          # rev-3 driver: write_deck / faces_on / submodel / run_ccx used unchanged

HERE = Path(__file__).resolve()
BASE_SHA = hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest()[:16]
SCRIPT_SHA = hashlib.sha256(HERE.read_bytes()).hexdigest()[:16]
RD = sax.run_dir(1)
OUTROOT = Path("/home/claude/work/mechanical/runs/structural") / ("contact_tc0203_sub_r4_" + RD.name)
A, B = "ENG-TC-02", "ENG-TC-03"
VARIANTS = {"C0": {"contact": False, "mu": None}, "C5": {"contact": True, "mu": 0.0}, "C7": {"contact": True, "mu": 0.0, "stick": True},
            "C6": {"contact": False, "mu": None, "bond_r": True}, "C3n": {"contact": True, "mu": 0.2, "n2s": True},
            "C4n": {"contact": True, "mu": 0.6, "n2s": True}}
C7_PASSES = 5
EXCL_MM = 1.0
FLOOR_MB = float(os.environ.get("SUB_DISK_FLOOR_MB", "2048"))
RSS_CAP_GB, EXPECT_GB = 9.0, float(os.environ.get("SUB_EXPECT_GB", "0.6"))
WAIT_S = float(os.environ.get("SUB_CCX_WAIT_S", "3600"))
POST_EH0P1 = Path("/home/claude/work/mechanical/v352/engine/04-fea/structural/results") / \
    f"sax_results_{RD.name.rsplit('_eh', 1)[0]}_eh0p1_v1.json"        # governing states: the eh 0.1 post of the same bound


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def guard(tag):
    """lead caps: wait for a ccx slot (< 2 machine-wide, RSS budget); HOLD (exit 3) on the disk floor or after WAIT_S."""
    t0 = time.time()
    while True:
        free_mb = shutil.disk_usage("/home/claude").free / 2 ** 20
        if free_mb < FLOOR_MB:
            print(f"HOLD before {tag}: disk {free_mb:.0f} MiB free < floor {FLOOR_MB:.0f} MiB", flush=True)
            sys.exit(3)
        out = subprocess.run(["ps", "-C", "ccx", "-o", "rss="], capture_output=True, text=True).stdout.split()
        n, rss_gb = len(out), sum(int(x) for x in out) / 2 ** 20
        if n < 2 and rss_gb + EXPECT_GB <= RSS_CAP_GB:
            return {"disk_free_MiB": round(free_mb), "ccx_running": n, "ccx_rss_GB": round(rss_gb, 2)}
        if time.time() - t0 > WAIT_S:
            print(f"HOLD before {tag}: {n} ccx, {rss_gb:.2f} GB for {WAIT_S:.0f} s", flush=True)
            sys.exit(3)
        time.sleep(15)


def read_frd_steps(frd, n_nodes):
    """(U, S) at the end of step 1 and at the end of step 2 of a two-step static ccx .frd.  Each result block carries its time on the
    '100C' record; step 1 ends at the first block with time 1.0, step 2 at the last block (step or total time convention alike)."""
    blocks, cur, blk, vals, tcur = [], {}, None, [], None
    with open(frd) as fh:
        for line in fh:
            if line.startswith("  100C"):
                try:
                    tcur = float(line[12:24])
                except ValueError:
                    tcur = None
                continue
            if line.startswith(" -4  "):
                blk = line[5:13].strip()
                if blk not in ("DISP", "STRESS"):
                    blk = None
                vals = []
                continue
            if blk is None:
                continue
            if line.startswith(" -5"):
                continue
            if line.startswith(" -1"):
                vals.append(line)
                continue
            if line.startswith(" -3"):
                ncomp = 3 if blk == "DISP" else 6
                arr = np.zeros((n_nodes, ncomp))
                for l in vals:
                    arr[int(l[3:13]) - 1] = [float(l[13 + 12 * k:25 + 12 * k]) for k in range(ncomp)]
                if blk == "DISP":
                    cur = {"U": arr, "t": tcur}
                else:
                    cur["S"] = arr
                    blocks.append(cur)
                blk = None
    times = [b["t"] for b in blocks]
    i1 = next((i for i, t in enumerate(times) if t is not None and abs(t - 1.0) < 1e-6), None)
    if i1 is None or i1 == len(blocks) - 1:
        raise RuntimeError(f"step split failed: block times {times}")
    return blocks[i1], blocks[-1], times


def corners60(d, parts):
    """BREP zero-radius concave corners of the given parts (234 (4): right turn > 60 deg on the CCW boundary)."""
    X, E, pn = d["X"], d["E"], d["pn"]
    pts = []
    for p in parts:
        cnt = {}
        for e in np.nonzero(pn == p)[0]:
            for f, (i, j, k) in sax.EDGE.items():
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
            if math.degrees(math.atan2(u[0] * w[1] - u[1] * w[0], u @ w)) < -60.0:
                pts.append((p, X[n].copy()))
    return pts


def boundary_nodes(d, part):
    X, E, pn = d["X"], d["E"], d["pn"]
    cnt = {}
    for e in np.nonzero(pn == part)[0]:
        for f, (i, j, k) in sax.EDGE.items():
            key = (min(E[e, i], E[e, j]), max(E[e, i], E[e, j]))
            cnt.setdefault(key, []).append((int(E[e, i]), int(E[e, j]), int(E[e, k])))
    nodes = set()
    for lst in cnt.values():
        if len(lst) == 1:
            nodes.update(lst[0])
    return np.array(sorted(nodes), dtype=np.int64)


def main(variants, picks):
    faces, info = sax.geometry()
    d, meta_m = sax.load_mesh(1)
    X = d["X"]
    fb = sax.boundary_faces(d, info)
    gp, gmeta = sax.gas_profile(info)
    plug, pmeta = sax.plug_band(fb, info, X, d["E"])
    from scipy.spatial import cKDTree
    node_part, node_mat = sax.node_maps(d)
    els, nodes, cut, other, z_cut = base.submodel(d, info)
    assert len(other) == 0, f"submodel touches other parts at {len(other)} nodes"
    nodeset = set(int(n) for n in nodes)
    zf, r4c, r4t = info["z_fl1"], info["tc02_r4"], info["tc03_r4"]
    z_ts, z_te = zf + r4t["thread_major_from_z_above_flange"], r4c["thread_end_z_top"]
    ifc = [(int(n), (int(ia), int(ib)) if str(pa) == A else (int(ib), int(ia))) for (n, pa, pb, ia, ib, rule) in d["pairs"]
           if {str(pa), str(pb)} == {A, B}]
    thread = [(i02, i03) for _, (i02, i03) in ifc if abs(X[i03, 0] - 7.0) < 1e-3]
    floor = sorted([(i02, i03) for _, (i02, i03) in ifc if abs(X[i03, 1] - zf) < 1e-3], key=lambda q: X[q[1], 0])
    assert len(thread) + len(floor) == len(ifc), "rev-4 interface: pairs off the thread band and off the floor"
    assert all(z_ts - 1e-3 <= X[i03, 1] <= z_te + 1e-3 for _, i03 in thread), "thread pairs outside the engaged band"
    shank03 = {i03 for _, i03 in thread}
    s02 = {i02 for _, (i02, _) in ifc}
    s03 = {i03 for _, (_, i03) in ifc}
    # seat window and singular set (234 (4))
    win = lambda n: X[n, 0] <= 12.5 and zf - 3.0 <= X[n, 1] <= info["z_ins_top"] + 1.5
    c60 = corners60(d, (A, B))
    named = [("thread start tie end (smeared M14x1 thread, u_z interlock tie)", (7.0, z_ts), "all"),
             ("thread end tie end (smeared M14x1 thread, u_z interlock tie; relief run-out)", (7.0, z_te), "all"),
             ("floor contact edge at the TC-03 flange OD corner (zero radius in the CAD, no edge break modelled)", (10.0, zf), "all"),
             ("floor tie end at the TC-02 entry R0.5 tangent point (S-AX tie idealisation)", (r4c["entry_floor_tangent_r"], zf), "tied")]
    c60n = [(f"BREP zero-radius concave corner of {p.replace('ENG-', '')} (turn > 60 deg)", (float(x[0]), float(x[1])), "all") for p, x in c60]
    feats = named + c60n + [("TC-02 entry R0.5 tangent point on the floor (tangential parting; stick edge in C7)", (r4c["entry_floor_tangent_r"], zf), "feature"),
                            ("TC-03 undercut R0.6 root (fillet, refined, not excluded)", (r4t["uc_root_r"], None), "feature"),
                            ("TC-02 thread relief R0.5 / run-out (fillet, refined, not excluded)", (r4c["relief_r_max"], z_te + 0.46), "feature")]

    def sing_pts(vn):
        pts = [q[1] for q in named + c60n if q[2] == "all" or (q[2] == "tied" and not VARIANTS[vn]["contact"])]
        return np.array(pts)

    def classify(n, vn, sp):
        x = X[n]
        dd = np.hypot(sp[:, 0] - x[0], sp[:, 1] - x[1])
        dsp = float(dd.min())
        cands = [q for q in named + c60n if q[2] == "all" or (q[2] == "tied" and not VARIANTS[vn]["contact"])]
        if dsp <= EXCL_MM:
            i = int(np.argmin([math.hypot(q[1][0] - x[0], q[1][1] - x[1]) for q in cands]))
            return dsp, cands[i][0]
        if vn == "C7" and math.hypot(x[0] - r4c["entry_floor_tangent_r"], x[1] - zf) <= EXCL_MM:
            return dsp, "within 1.0 mm of the C7 stick edge (entry tangent point): zone set by the refinement post"
        if abs(x[1] - zf) < 0.6 and 7.3 <= x[0] <= 10.0:
            return dsp, "floor / flange-top contact band (regular)"
        if x[0] <= 7.0 + 1e-6 and node_part[n] == B and zf < x[1] < z_ts:
            return dsp, "TC-03 undercut R0.6 (regular, refined fillet)"
        if node_part[n] == A and abs(x[0] - 7.0) < 0.6 and z_ts <= x[1] <= z_te:
            return dsp, "TC-02 thread band (regular)"
        return dsp, "regular (> 1.0 mm from every singular point)"

    def margins(S2, S1, T, sfy, sfu, vn):
        sp = sing_pts(vn)
        tree = cKDTree(sp)
        out = {}
        vt, vmech = sax.vm(S2), sax.vm(S2 - S1)
        for p in (A, B):
            pn_nodes = np.array([n for n in nodes if node_part[n] == p])
            wn = np.array([n for n in pn_nodes if win(n)])
            m_ = node_mat[pn_nodes[0]]
            res = {}
            for setname, ns in (("all", wn), ("part_all", pn_nodes)):
                Fy, Fu = sax.allowables(m_, T[ns])
                v, vm_ = np.maximum(vt[ns], 1e-9), np.maximum(vmech[ns], 1e-9)
                crit = {"MS_y": Fy / (sfy * v) - 1.0, "MS_u": (Fu / (sfu * v) - 1.0) if sfu else None, "MS_y_SF1": Fy / v - 1.0,
                        "MS_prim_y": Fy / (sfy * vm_) - 1.0, "MS_prim_u": (Fu / (sfu * vm_) - 1.0) if sfu else None, "MS_PQ": 2.0 * Fy / v - 1.0}
                dsp = tree.query(X[ns])[0]
                regm = dsp > EXCL_MM
                if vn == "C7":
                    regm = regm & (np.hypot(X[ns, 0] - r4c["entry_floor_tangent_r"], X[ns, 1] - zf) > EXCL_MM)
                masks = {setname: np.ones(len(ns), bool)}
                if setname == "all":
                    masks["regular"] = regm
                    if vn == "C7":
                        masks["regular_incl_stick_edge"] = dsp > EXCL_MM
                for mk, msk in masks.items():
                    o = {}
                    for cn, cv in crit.items():
                        if cv is None or not msk.any():
                            continue
                        if setname == "part_all" and cn not in ("MS_y", "MS_u"):
                            continue
                        i = int(np.argmin(np.where(msk, cv, np.inf)))
                        n = int(ns[i])
                        ds, cl = classify(n, vn, sp)
                        o[cn] = [round(float(cv[i]), 4), n + 1, round(float(X[n, 0]), 3), round(float(X[n, 1]), 3), round(float(T[n] - 273.15), 1),
                                 round(float(vt[n]), 2), round(ds, 3), cl]
                    res[mk] = o
            out[p] = res
        return out

    def interfaces(U):
        o = {}
        dz = np.array([U[i02, 1] - U[i03, 1] for i02, i03 in floor])          # > 0 = open
        rr = np.array([X[i03, 0] for _, i03 in floor])
        o["floor"] = {"n_pairs": len(floor), "n_closed": int((dz < 0).sum()), "opening_max_mm": round(float(dz.max()), 7),
                      "penetration_max_mm": round(float(-dz.min()), 7), "p_max_MPa_penalty": round(float(max(0.0, -dz.min()) * base.K_PEN), 2),
                      "open_r_mm": [round(float(x), 3) for x in rr[dz >= 0]],
                      "note": "u_z(TC-02 counterbore floor) - u_z(TC-03 flange top) per pair: > 0 open; closed = penalty overclosure (< 0); "
                              "S03 lands: the S03 groove is not modelled (open item)"}
        gr = np.array([U[i03, 0] - U[i02, 0] for i02, i03 in thread])
        o["thread_radial"] = {"overclosure_min_mm": round(float(gr.min()), 7), "overclosure_max_mm": round(float(gr.max()), 7),
                              "n_in_contact": int((gr > 0).sum()), "n": len(thread),
                              "note": "u_r(TC-03 shank) - u_r(TC-02 bore) at the paired nodes: > 0 = overclosure (radial contact)"}
        # unpaired proximity: TC-03 boundary nodes in the window vs the nearest unpaired TC-02 boundary node (signed gap on the TC-02 normal)
        t02 = cKDTree(X[b02])
        dist, j = t02.query(X[b03])
        near = dist < 0.6
        rows = []
        for k in np.nonzero(near)[0]:
            n3, n2 = int(b03[k]), int(b02[j[k]])
            v0 = X[n3] - X[n2]
            g0 = float(np.linalg.norm(v0))
            if g0 < 1e-6:
                continue
            nrm = v0 / g0
            g = float((X[n3] + U[n3, :2] - X[n2] - U[n2, :2]) @ nrm)
            rows.append((g, g0, n3, n2))
        rows.sort()
        o["unpaired_proximity"] = {"n_checked": len(rows), "closest": [{"gap_mm": round(g, 6), "gap0_mm": round(g0, 6), "tc03_node": n3 + 1,
                                                                        "at_r_z_mm": [round(float(X[n3, 0]), 3), round(float(X[n3, 1]), 3)]}
                                                                       for g, g0, n3, n2 in rows[:4]],
                                   "note": "signed gap along the initial TC-02 -> TC-03 node vector, CAD clearances (top gap 0.15 nominal, drawing "
                                           "minimum 0.125; flange OD 0.10 radial; seat-entry cavity); < 0 = closes (contact not modelled there)"}
        top = [rw for rw in rows if abs(X[rw[2], 1] - info["tc03_top_z"]) < 1e-3]
        if top:
            g = min(top)[0]
            o["top_gap"] = {"min_nominal_mm": round(g, 6), "min_at_drawing_minimum_0.125_mm": round(g - 0.025, 6)}
        return o

    b02 = np.array([n for n in boundary_nodes(d, A) if win(n) and n not in s02])
    b03 = np.array([n for n in boundary_nodes(d, B) if win(n) and n not in s03])
    co_all = {c[0]: c for c in sax.combos(info)}
    gj = json.loads(POST_EH0P1.read_text()) if POST_EH0P1.exists() else None
    cases = []
    for pk in picks:
        cid, st = pk.split(":")
        if st == "gov":
            rr = [r for r in gj["rows"] if r["case"] == cid and r["part"] == A and r["set"] == "regular" and r.get("MS_ult") is not None]
            st = min(rr, key=lambda r: r["MS_ult"])["state"]
        cases.append((cid, st))
    if os.environ.get("SUB_DRYRUN"):
        print("DRYRUN", RD.name, cases, "pairs", len(ifc), "thread", len(thread), "floor", len(floor), "els", len(els), "nodes", len(nodes),
              "cut", len(cut), "z_cut", round(z_cut, 3), "corners60", len(c60), flush=True)
        for p, x in c60:
            if x[0] <= 12.5 and zf - 3 <= x[1] <= info["z_ins_top"] + 1.5:
                print("  corner60", p, np.round(x, 4))
        return
    OUTROOT.mkdir(parents=True, exist_ok=True)
    part_f = OUTROOT / "sax_contact_tc0203_sub_v352r4_v1_partial.json"
    res = {"id": "sax_contact_tc0203_sub_v352r4", "version": "v1", "date": "2026-10-20", "owner": "mechanical",
           "status": "SIM / CALC (contact sub-model of a linear-elastic axisymmetric model); not physical approval; negatives SHOWN AS FOUND",
           "script": str(HERE), "script_sha256_16": sha16(HERE), "base_driver_sha256_16": BASE_SHA, "global_run": RD.name,
           "entry_h_mm": sax.ENTRY_H, "thermal": os.environ["SAX_THERMAL_TAG"], "doc": __doc__,
           "mesh": {"file": str(RD / "mesh.npz"), "sha256_16": sha16(RD / "mesh.npz"), "nodes": int(len(X)), "elements": int(len(d["E"]))},
           "submodel": {"n_elements": int(len(els)), "n_nodes": int(len(nodes)), "n_cut_nodes": int(len(cut)), "z_cut_mm": round(z_cut, 3)},
           "interface": {"pairs": len(ifc), "thread_pairs": len(thread), "floor_pairs": len(floor), "z_thread_start_mm": round(z_ts, 4),
                         "z_thread_end_mm": round(z_te, 4), "z_floor_mm": round(zf, 4),
                         "floor_r_mm": [round(float(X[i03, 0]), 4) for _, i03 in floor]},
           "singular_set": {"named": [[q[0], [round(q[1][0], 4), round(q[1][1], 4)], q[2]] for q in named],
                            "corners60": [[p, [round(float(x[0]), 4), round(float(x[1]), 4)]] for p, x in c60],
                            "exclusion_mm": EXCL_MM, "features_not_excluded": [q[0] for q in feats if q[2] == "feature"]},
           "penalty": {"K_MPa_per_mm": base.K_PEN, "stick_slope_MPa_per_mm": base.STICK}, "runs": {}}
    if part_f.exists():
        old = json.loads(part_f.read_text())
        if old.get("mesh", {}).get("sha256_16") == res["mesh"]["sha256_16"]:
            res["runs"].update({k: v for k, v in old.get("runs", {}).items() if v.get("margins") or v.get("passes")})

    def eqs_for(vv, stick_pairs=()):
        eqs = {1: [], 2: []}
        for dof in (1, 2):
            for a_, b_ in d["eqs"][dof]:
                if a_ not in nodeset or b_ not in nodeset:
                    continue
                if vv["contact"] and {node_part[a_], node_part[b_]} == {A, B}:
                    if dof == 2 and (a_ in shank03 or b_ in shank03):
                        eqs[dof].append((a_, b_))         # thread interlock kept
                    continue
                eqs[dof].append((a_, b_))
        zmap = {frozenset((int(a_), int(b_))): (int(a_), int(b_)) for a_, b_ in d["eqs"][2]}
        if vv.get("bond_r"):
            for _, (i02, i03) in ifc:
                eqs[1].append(zmap[frozenset((i02, i03))])
        for (i02, i03) in stick_pairs:
            eqs[1].append(zmap[frozenset((i02, i03))])
        return eqs

    def one_run(key, vv, cid, st, eqs, T, U1, Ug, Sg, co, sfy, sfu, vn):
        wd = OUTROOT / key
        wd.mkdir(parents=True, exist_ok=True)
        job = wd / "con.inp"
        slave = base.faces_on(d, B, s03, els) if vv["contact"] else []
        master = base.faces_on(d, A, s02, els) if vv["contact"] else []
        base.write_deck(job, d, els, nodes, cut, eqs, fb, info, T, gp, plug, co, U1, Ug, vv["contact"], slave, master, vv["mu"],
                        f"S-AX v352r4 sub-model {key} (T-F2 rev 4)", ctype=("NODE TO SURFACE" if vv.get("n2s") else "SURFACE TO SURFACE"))
        g = guard(key)
        r = base.run_ccx(job)
        r["guard"] = g
        row = {"variant": vn, "case": cid, "state": st, "script_sha256_16": SCRIPT_SHA, "coefficients": co, "SF": [sfy, sfu], "ccx": r, "n_slave_faces": len(slave),
               "n_master_faces": len(master), "n_eq": sum(len(eqs[k]) for k in (1, 2))}
        frd = wd / "con.frd"
        ok = r["returncode"] == 0 and not r["errors"] and frd.exists()
        U = None
        if ok:
            b1, b2, times = read_frd_steps(frd, len(X))
            U, S2, S1 = b2["U"], b2["S"][:, :4], b1["S"][:, :4]
            row["frd_block_times"] = times
            row["margins"] = margins(S2, S1, T, sfy, sfu, vn)
            if vn == "C0":
                inner = np.array([n for n in nodes if n not in set(int(q) for q in cut)])
                dv = np.abs(sax.vm(S2[inner]) - sax.vm(Sg[inner, :4]))
                row["check_vs_global"] = {"max_abs_dvm_MPa": round(float(dv.max()), 6), "max_vm_MPa": round(float(sax.vm(Sg[inner, :4]).max()), 3),
                                          "max_abs_du_mm": round(float(np.abs(U[inner, :2] - Ug[inner, :2]).max()), 9)}
            if vv["contact"] or vn == "C6":
                row["interfaces"] = interfaces(U)
            keep = np.array([n for n in nodes if node_part[n] in (A, B)])
            np.savez_compressed(wd / "res.npz", nodes=keep, U=U[keep, :2].astype(np.float32), S2=S2[keep].astype(np.float32),
                                S1=S1[keep].astype(np.float32), T=T[keep].astype(np.float32))
        for f_ in ("con.frd", "con.12d", "con.dat", "con.cvg", "con.sta"):
            (wd / f_).unlink(missing_ok=True)
        with open(job, "rb") as fi, gzip.open(str(job) + ".gz", "wb", compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
        job.unlink()
        return row, U

    def pick_min(rows):
        """per cell, the lower value of the last two C7 passes (lead 236 (9)(c) when the set does not settle)."""
        out = {}
        for p in rows[0]:
            out[p] = {}
            for s in rows[0][p]:
                out[p][s] = {}
                for c in rows[0][p][s]:
                    cand = [rw[p][s][c] for rw in rows if c in rw[p].get(s, {})]
                    out[p][s][c] = min(cand, key=lambda q: q[0])
        return out

    for cid, st in cases:
        c = co_all[cid]
        co, sfy, sfu = c[3], c[4], c[5]
        assert st in c[2], f"{st} is not a state of {cid}"
        T, prov = sax.state_temperature(st, d, info)
        z = sax.load_res_any(1, st)
        U1 = z["U1"]
        Sg, Ug, Tg, _ = sax.combo_fields(1, cid, st)
        nl = np.array(sorted(nodeset))
        assert np.isfinite(U1[nl]).all() and np.isfinite(Sg[nl]).all(), f"{st}: global field not finite on the sub-model (trim region)"
        assert np.allclose(Tg[nl], T[nl], rtol=1e-6, atol=1e-3), "thermal field differs from the linear run"
        for vn in variants:
            vv = dict(VARIANTS[vn])
            key = f"{vn}_{cid}_{st}"
            if key in res["runs"]:
                print(key, "kept from an earlier invocation", flush=True)
                continue
            if vn != "C7":
                row, U = one_run(key, vv, cid, st, eqs_for(vv), T, U1, Ug, Sg, co, sfy, sfu, vn)
                row["global_linear_same_nodes"] = margins(Sg[:, :4], Sg[:, :4] - (z["S1"][:, :4] if "S1" in z else 0.0), T, sfy, sfu, "C0") \
                    if vn == "C0" else None
                res["runs"][key] = row
            else:
                c5 = OUTROOT / f"C5_{cid}_{st}" / "res.npz"
                assert c5.exists(), f"C7 needs the C5 solution of {cid} {st} first"
                zr = np.load(c5)
                Uc5 = np.zeros((len(X), 2))
                Uc5[zr["nodes"]] = zr["U"]
                closed = {q for q in floor if Uc5[q[0], 1] - Uc5[q[1], 1] < 0}
                passes, rows_m, hist = [], [], []
                stable, cycle = False, False
                for k in range(1, C7_PASSES + 1):
                    stick = sorted(closed, key=lambda q: X[q[1], 0])
                    row, U = one_run(f"{key}_p{k}", vv, cid, st, eqs_for(vv, stick), T, U1, Ug, Sg, co, sfy, sfu, vn)
                    if U is None:
                        passes.append({"pass": k, "ccx": row["ccx"], "n_stuck": len(stick)})
                        break
                    new = {q for q in floor if U[q[0], 1] - U[q[1], 1] < 0}
                    added, removed = new - closed, closed - new
                    passes.append({"pass": k, "n_stuck": len(stick), "stuck_r_mm": [round(float(X[q[1], 0]), 3) for q in stick],
                                   "n_closed_after": len(new), "added_r_mm": [round(float(X[q[1], 0]), 3) for q in sorted(added)],
                                   "removed_r_mm": [round(float(X[q[1], 0]), 3) for q in sorted(removed)], "ccx": row["ccx"],
                                   "interfaces": row.get("interfaces"), "margins": row.get("margins")})
                    rows_m.append(row.get("margins"))
                    hist.append(frozenset(stick))
                    if not added and not removed:
                        stable = True
                        break
                    if len(hist) >= 2 and frozenset(new) == hist[-2]:
                        cycle = True            # period 2: pass k+1 would repeat pass k-1
                        break
                    closed = new
                fin = passes[-1].get("margins") if stable else (pick_min([m for m in rows_m[-2:] if m]) if len([m for m in rows_m if m]) >= 2 else None)
                res["runs"][key] = {"variant": "C7", "case": cid, "state": st, "SF": [sfy, sfu], "active_set": {
                    "rule": "stick only the floor pairs closed in the previous solution (pass 0 = C5), until the set is stable, cap 5 (lead 236 (9)(c))",
                    "n_passes": len(passes), "stable": stable, "period_2_cycle": cycle,
                    "final": ("last pass" if stable else "lower of the last two passes per cell")},
                    "passes": passes, "margins": fin, "interfaces": passes[-1].get("interfaces")}
            r_ = res["runs"][key]
            mm = r_.get("margins") or {}
            print(key, {p: {s: {c_: v[0] for c_, v in mm[p][s].items() if c_ in ("MS_y", "MS_u", "MS_y_SF1")} for s in ("all", "regular") if s in mm[p]}
                        for p in mm}, (r_.get("active_set") or {}).get("n_passes"), flush=True)
            part_f.write_text(json.dumps(res, indent=1, default=float))
    s = json.dumps(res, indent=1, default=float)
    (OUTROOT / "sax_contact_tc0203_sub_v352r4_v1.json").write_text(s)
    print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16], flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(variants=a[0].split(","), picks=a[1].split(","))
