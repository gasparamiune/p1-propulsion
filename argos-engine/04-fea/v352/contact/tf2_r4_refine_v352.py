"""T-F2 rev 4 post: the 234 (4) refinement check, the C7 stick-edge zone (236 (9)(a)), the seat-region matrix (236 (9)(b)) and the nodal
183 (1) quantities on the sub-model fields, for the (b) package (lead CHANGELOG 236 (5), 239 (7); lead 14:34Z 'Next as you have it: the (b)
package and the abort decision').  Mechanical, 2026-10-20, v1.  Reads only (runs of sax_contact_tc0203_sub_v352r4.py v1.1 1fce3b7d1f343be2:
its json per bound and entry-h level, the per-run res.npz fields and the S-AX v352r4 meshes); no solver run.  SIM / CALC, not physical
approval; negatives SHOWN AS FOUND.

Definitions
  * fields: res.npz of every run (TC-02 / TC-03 sub-model nodes): S2 = total stress (step 2), S1 = thermal-only step, T (K); von Mises on
    the axisymmetric tensor as sax.vm; allowables engmat at the node temperature (TC-02 AL6061-T6, TC-03 GLIDCOP-AL15: the hot GlidCop values
    are ASSUMED retention, engmat); the json minima of the driver are reproduced from the fields first (assert);
  * criteria per node (sax / driver conventions): combined MS_y = Fty / (SF_y vm) - 1, MS_u = Ftu / (SF_u vm) - 1 at the case SF (TB70
    1.5 / 2.0, TBS 1.0 / 1.5, lead 188 (9)); MS_y_SF1 (line 106 'no yield at Fty(T)', information per 239 (7)); 183 (1) (a) primary
    MS_prim_y / _u on the mechanical increment (S2 - S1); (b) MS_PQ = 2 Fty / vm - 1 (P+Q range from the stress-free 20 C state);
    (c) LCF, the accepted line-212 (c) / tc01_midbay method (ii) assembly-from-zero: de = vm / E, or the Neuber strain vm^2 / (E Fty)
    (elastic-perfectly-plastic first loading) where vm > Fty; Manson universal slopes de = 3.5 Su / E N^-0.12 + D^0.6 N^-0.6,
    D = ln(1 / (1 - RA)), Su = Ftu(T), E(T) engmat; RA 0.30 ASSUMED for 6061-T6 (the accepted value) and 0.27 ASSUMED for GlidCop AL-15
    (taken equal to the Hoganas 0667HOG-2 typical elongation 27 %, no RA published; a ductile metal's RA is normally above its elongation);
    N_allow = min(N(2 de), N(de) / 20), MS_LCF = N_allow / 50 - 1 (every cycle cold -> state -> cold counted as one hot cycle);
  * sets: 'all' = the seat window (r <= 12.5, z_fl1 - 3 .. z_ins_top + 1.5); 'regular' = farther than 1.0 mm from the singular set of the
    run (the json's named points and BREP zero-radius corners; the 'tied' point only in C0 / C6); C7 'outside_zone' = regular AND farther
    than d_zone from every stick edge of that pass (the transitions between stuck and free floor pairs, incl. the entry tangent r 7.5);
  * 234 (4) refinement (the three SAX_ENTRY_H levels 0.2 / 0.1 / 0.05 at two reference states: TBS at the TB state for the TB70 / TBS
    states, LC2 B1_19 for the LC1 / LC2 states): demand D = 1 / (1 + MS) of each cell; the 5 % test is |D(0.05) / D(0.1) - 1| <= 0.05;
  * stick-edge zone (236 (9)(a)): C7 TBS TB, the last pass of the 0.1 and 0.05 levels; the 0.05 field is interpolated linearly on its own
    corner-node triangulation (per part) at the 0.1 nodes; a node fails the 5 % test when |vm(0.1) / vm(0.05) - 1| > 0.05 (nodes with
    vm >= 0.5 Fty(T), outside the 1.0 mm singular exclusion, within 2.0 mm of the floor plane, r 7.0 .. 10.5); d_zone = the largest distance
    from a stick edge of either level among the failing nodes, rounded up to 0.05 mm (the same test on C5 is reported for comparison);
  * cell rule (234 (4)): a cell takes its regular-set value where the all-node minimum sits at a named idealisation that a named
    sub-model replaces (the smeared-thread u_z tie ends -> J-TC03 thread-strip CALC, Mechanical, 236 (10)) or where the regular value
    converges by the 5 % test; otherwise the all-node value; every cell carries the all-node minimum with node, class and distance;
  * seat matrix (236 (9)(b)) = min over C5, C3n, C4n (cells as above) and C7 outside the stick-edge zone; also min(C5, C3n, C4n)
    (236 (5)); the abort and LC states have the 0.1 level only: the reference-state factor D(0.05) / D(0.1) of the same variant / part /
    set / criterion is applied to their demand as an ESTIMATE of the 0.05 value (shown beside, flagged where the reference fails the 5 %
    test); states: LC1 B1_19, LC2 B1_1 / 16 / 19 / 21.65 (C3n / C4n at B1_19 only), TB70 and TBS at TB (175 C) and the trial aborts.
Usage: tf2_r4_refine_v352.py -> v352/contact/tf2_r4_refine_v352_v1.json"""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import matplotlib.tri as mtri
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat

SR = Path("/home/claude/work/mechanical/runs/structural")
OUT = Path("/home/claude/work/mechanical/v352/contact/tf2_r4_refine_v352_v1.json")
BDS, EHS = ("GVLO", "GVHI"), ("eh0p2", "eh0p1", "eh0p05")
A, B = "ENG-TC-02", "ENG-TC-03"
EXCL, R_ENTRY = 1.0, 7.5
ZF, Z_INS_TOP = 107.51342601773104, 117.51342601773104
RA = {"AL6061-T6": 0.30, "GLIDCOP-AL15": 0.27}
VARS = ("C0", "C5", "C3n", "C4n", "C7")
MATRIX_VARS = ("C5", "C3n", "C4n", "C7")
STATES = ("TB", "TB_a165", "TB_a150", "TB_a135", "TB_a120", "TB_a105")
CRIT = ("MS_y", "MS_u", "MS_y_SF1", "MS_prim_y", "MS_prim_u", "MS_PQ", "MS_LCF")
THREAD_TIE = "thread start tie end", "thread end tie end"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def cdir(bd, eh):
    return SR / f"contact_tc0203_sub_r4_L1_thv352_NF2b_R4_{bd}_r10free_cad352r4_{eh}"


def mdir(bd, eh):
    return SR / f"L1_thv352_NF2b_R4_{bd}_r10free_cad352r4_{eh}"


def mtab(mat, key, TC):
    d = engmat.MATERIALS[mat][key]
    return np.interp(TC, d["T_C"], d["v"]) / 1e6


def vm(S):
    sxx, syy, szz, sxy = S[..., 0], S[..., 1], S[..., 2], S[..., 3]
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3.0 * sxy ** 2)


def us_N(de, Su, E, ra):
    """Manson universal slopes, vectorised: N for the total strain range de (bisection on log10 N in 0 .. 15)."""
    D = math.log(1.0 / (1.0 - ra))
    lo, hi = np.zeros_like(de), np.full_like(de, 15.0)
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        f = 3.5 * Su / E * 10.0 ** (-0.12 * mid) + D ** 0.6 * 10.0 ** (-0.6 * mid) - de
        lo, hi = np.where(f > 0, mid, lo), np.where(f > 0, hi, mid)
    return 10.0 ** (0.5 * (lo + hi))


MESH = {}


def mesh(bd, eh):
    if (bd, eh) not in MESH:
        z = np.load(mdir(bd, eh) / "mesh.npz", allow_pickle=True)
        X, E, pn, mat = z["X"], z["E"], z["pn"], z["mat"]
        part = np.empty(len(X), object)
        mats = {}
        for p in (A, B):
            part[np.unique(E[pn == p])] = p
            ms = set(str(m) for m in mat[pn == p])
            assert len(ms) == 1
            mats[p] = ms.pop()
        tri = {p: E[pn == p][:, :3] for p in (A, B)}
        MESH[(bd, eh)] = {"X": X, "part": part, "mats": mats, "tri": tri, "sha": sha(mdir(bd, eh) / "mesh.npz")}
    return MESH[(bd, eh)]


def run_json(bd, eh):
    d = json.loads((cdir(bd, eh) / "sax_contact_tc0203_sub_v352r4_v1.json").read_text())
    pf = cdir(bd, eh) / "sax_contact_tc0203_sub_v352r4_v1_partial.json"
    if pf.exists():                                      # runs finished after the last full write (chain 11 in progress)
        dp = json.loads(pf.read_text())
        for k, v in dp.get("runs", {}).items():
            d["runs"].setdefault(k, v)
    return d


def sing_points(js, vn):
    pts = [(q[1][0], q[1][1], q[0]) for q in js["singular_set"]["named"] if q[2] == "all" or (q[2] == "tied" and vn in ("C0", "C6"))]
    pts += [(q[1][0], q[1][1], f"BREP zero-radius concave corner of {q[0].replace('ENG-', '')} (turn > 60 deg)") for q in js["singular_set"]["corners60"]]
    return pts


def stick_edges(stuck_r, floor_r):
    """radii of the transitions stuck <-> free along the floor pairs (the entry tangent r 7.5 when the first pair is stuck)."""
    st = [any(abs(r - s) < 2e-3 for s in stuck_r) for r in floor_r]
    edges = []
    if st and st[0]:
        edges.append(floor_r[0])
    for i in range(len(floor_r) - 1):
        if st[i] != st[i + 1]:
            edges.append(0.5 * (floor_r[i] + floor_r[i + 1]))
    if st and st[-1]:
        edges.append(floor_r[-1])
    return edges


class Field:
    """nodal criteria of one run (one pass) on the TC-02 / TC-03 window nodes."""

    def __init__(self, bd, eh, rdir, sf, js, vn):
        m = mesh(bd, eh)
        z = np.load(rdir / "res.npz")
        nodes = z["nodes"]
        X = m["X"][nodes]
        part = m["part"][nodes]
        win = (X[:, 0] <= 12.5) & (X[:, 1] >= ZF - 3.0) & (X[:, 1] <= Z_INS_TOP + 1.5)
        self.nodes, self.X, self.part = nodes[win], X[win], part[win]
        S2, S1, T = z["S2"][win].astype(float), z["S1"][win].astype(float), z["T"][win].astype(float) - 273.15
        self.T = T
        self.vt = np.maximum(vm(S2), 1e-9)
        self.vmech = np.maximum(vm(S2 - S1), 1e-9)
        self.sf = sf
        Fy, Fu, Em, RAv = (np.empty(len(T)) for _ in range(4))
        for p in (A, B):
            k = self.part == p
            mt = m["mats"][p]
            Fy[k], Fu[k], Em[k] = mtab(mt, "Fty", T[k]), mtab(mt, "Ftu", T[k]), mtab(mt, "E", T[k])
            RAv[k] = RA[mt]
        self.Fy, self.Fu, self.E = Fy, Fu, Em
        sfy, sfu = sf
        c = {"MS_y": Fy / (sfy * self.vt) - 1.0, "MS_u": Fu / (sfu * self.vt) - 1.0, "MS_y_SF1": Fy / self.vt - 1.0,
             "MS_prim_y": Fy / (sfy * self.vmech) - 1.0, "MS_prim_u": Fu / (sfu * self.vmech) - 1.0, "MS_PQ": 2.0 * Fy / self.vt - 1.0}
        de = np.where(self.vt <= Fy, self.vt / Em, self.vt ** 2 / (Em * Fy))
        Nl = np.empty(len(T))
        for ra in set(RAv.tolist()):
            k = RAv == ra
            N2 = us_N(2.0 * de[k], Fu[k], Em[k], ra)
            N1 = us_N(de[k], Fu[k], Em[k], ra)
            Nl[k] = np.minimum(N2, N1 / 20.0)
        self.de, self.N_allow = de, Nl
        c["MS_LCF"] = Nl / 50.0 - 1.0
        self.c = c
        sp = sing_points(js, vn)
        self.sp = sp
        spx = np.array([(q[0], q[1]) for q in sp])
        self.dsp, isp = cKDTree(spx).query(self.X)
        self.sp_class = [sp[i][2] for i in isp]
        self.regular = self.dsp > EXCL
        if vn == "C7":                                   # as the driver: C7 'regular' also excludes 1.0 mm around the entry tangent (stick edge)
            self.regular &= np.hypot(self.X[:, 0] - R_ENTRY, self.X[:, 1] - ZF) > EXCL
        self.edges = []
        self.dedge = np.full(len(T), np.inf)

    def set_edges(self, edges):
        self.edges = list(edges)
        if edges:
            pe = np.array([(r, ZF) for r in edges])
            self.dedge = cKDTree(pe).query(self.X)[0]

    def classify(self, i, vn):
        x = self.X[i]
        if self.dsp[i] <= EXCL:
            return self.sp_class[i]
        if vn == "C7" and self.dedge[i] <= EXCL:
            return "within 1.0 mm of a C7 stick edge"
        if abs(x[1] - ZF) < 0.6 and 7.3 <= x[0] <= 10.0:
            return "floor / flange-top contact band (regular)"
        if 6.2 <= x[0] <= 7.0 + 1e-6 and self.part[i] == B and ZF < x[1] < 109.112:
            return "TC-03 undercut R0.6 (regular, refined fillet)"
        if x[0] < 6.2 and self.part[i] == B:
            return "TC-03 body / bore (regular; the driver labels r < 7.0 in this band 'undercut')"
        if self.part[i] == A and abs(x[0] - 7.0) < 0.6 and 109.112 <= x[1] <= 116.5563:
            return "TC-02 thread band (regular)"
        return "regular (> 1.0 mm from every singular point)"

    def cell(self, p, crit, mask, vn):
        k = (self.part == p) & mask
        if not k.any():
            return None
        v = np.where(k, self.c[crit], np.inf)
        i = int(np.argmin(v))
        x = self.X[i]
        r = [round(float(v[i]), 4), int(self.nodes[i]) + 1, round(float(x[0]), 3), round(float(x[1]), 3), round(float(self.T[i]), 1),
             round(float(self.vt[i]), 2), round(float(self.dsp[i]), 3), self.classify(i, vn)]
        if crit == "MS_LCF":
            r += [{"de": round(float(self.de[i]), 6), "N_allow": float(f"{self.N_allow[i]:.4g}")}]
        if vn == "C7":
            r += [{"d_stick_edge_mm": round(float(self.dedge[i]), 3)}]
        return r


def load_run(bd, eh, js, key):
    """[(pass label, Field)] of a run: the single run, or the C7 passes that make its final value (last pass if stable, else the last two)."""
    r = js["runs"][key]
    sf = tuple(r["SF"])
    vn = r["variant"]
    if vn != "C7":
        return [("run", Field(bd, eh, cdir(bd, eh) / key, sf, js, vn))], r
    a = r["active_set"]
    n = a["n_passes"]
    use = [n] if a["stable"] else [n - 1, n]
    out = []
    floor_r = js["interface"]["floor_r_mm"]
    for k in use:
        f = Field(bd, eh, cdir(bd, eh) / f"{key}_p{k}", sf, js, vn)
        f.set_edges(stick_edges(r["passes"][k - 1]["stuck_r_mm"], floor_r))
        out.append((f"p{k}", f))
    return out, r


def cells_of(fields, vn, extra_mask=None):
    """per part and criterion: min over the passes (lower of the last two, 236 (9)(c)) for the sets all / regular (/ outside_zone)."""
    res = {}
    for p in (A, B):
        res[p] = {}
        for sname in ("all", "regular") + (("outside_zone",) if extra_mask is not None else ()):
            row = {}
            for cr in CRIT:
                best = None
                for lab, f in fields:
                    msk = np.ones(len(f.vt), bool) if sname == "all" else (f.regular if sname == "regular" else (f.regular & extra_mask(f)))
                    c = f.cell(p, cr, msk, vn)
                    if c is not None and (best is None or c[0] < best[0]):
                        best = c + [lab]
                row[cr] = best
            res[p][sname] = row
    return res


def check_vs_json(cells, rj, key):
    """the driver's json minima reproduced from the fields (all / regular sets; MS_y, MS_u, MS_PQ)"""
    m = rj.get("margins")
    bad = []
    for p in (A, B):
        for s in ("all", "regular"):
            for cr in ("MS_y", "MS_u", "MS_PQ", "MS_prim_y"):
                if cr in m[p].get(s, {}) and cells[p][s][cr] is not None:
                    if abs(m[p][s][cr][0] - cells[p][s][cr][0]) > 2e-3:
                        bad.append((key, p, s, cr, m[p][s][cr][0], cells[p][s][cr][0]))
    return bad


def demand(ms):
    return None if ms is None else 1.0 / (1.0 + ms)


out = {"id": "tf2_r4_refine_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {}, "stick_edge_zone": {}, "runs": {}, "seat_matrix": {}, "checks_vs_driver_json": []}
JS = {}
for bd in BDS:
    for eh in EHS:
        js = run_json(bd, eh)
        JS[(bd, eh)] = js
        out["inputs"][f"{bd}_{eh}"] = {"json": str(cdir(bd, eh) / "sax_contact_tc0203_sub_v352r4_v1.json"),
                                       "json_sha256_16": sha(cdir(bd, eh) / "sax_contact_tc0203_sub_v352r4_v1.json"),
                                       "driver_sha256_16": js["script_sha256_16"], "mesh_sha256_16": mesh(bd, eh)["sha"],
                                       "n_runs": len(js["runs"])}

# ---------------- 1) refinement of every variant at the two reference states (the three levels), cells all / regular:
#                     TBS TB (factor for the TB70 / TBS states) and LC2 B1_19 (factor for the LC1 / LC2 states)
REFSTATE = {"TB": "TBS_TB", "LC": "LC2_B1_19"}
FIELDS_TB = {}
for fam, rs in REFSTATE.items():
    out[f"refinement_{rs}"] = {}
    for bd in BDS:
        for vn in VARS:
            key = f"{vn}_{rs}"
            lv = {}
            for eh in EHS:
                js = JS[(bd, eh)]
                if key not in js["runs"]:
                    continue
                flds, rj = load_run(bd, eh, js, key)
                if fam == "TB":
                    FIELDS_TB[(bd, eh, vn)] = flds
                cl = cells_of(flds, vn)
                out["checks_vs_driver_json"] += check_vs_json(cl, rj, f"{bd}/{eh}/{key}")
                lv[eh] = cl
            tab = {}
            for p in (A, B):
                for s in ("all", "regular"):
                    for cr in CRIT:
                        vals = {eh: lv[eh][p][s][cr] for eh in EHS if eh in lv and lv[eh][p][s][cr] is not None}
                        if len(vals) < 3:
                            continue
                        D = {eh: demand(v[0]) for eh, v in vals.items()}
                        f01 = D["eh0p05"] / D["eh0p1"]
                        tab[f"{p}|{s}|{cr}"] = {"MS_by_level": {eh: v[0] for eh, v in vals.items()},
                                                "where_by_level": {eh: [v[2], v[3], v[7]] for eh, v in vals.items()},
                                                "D_ratio_0p1_over_0p2": round(D["eh0p1"] / D["eh0p2"], 4), "D_ratio_0p05_over_0p1": round(f01, 4),
                                                "converged_5pct": bool(abs(f01 - 1.0) <= 0.05), "refined_value": vals["eh0p05"][0]}
            out[f"refinement_{rs}"][f"{bd}|{vn}"] = tab

# ---------------- 2) stick-edge zone (C7), and the same nodal test on C5 for comparison
def nodal_test(bd, vn):
    f1 = FIELDS_TB[(bd, "eh0p1", vn)][-1][1]
    f2 = FIELDS_TB[(bd, "eh0p05", vn)][-1][1]
    m2 = mesh(bd, "eh0p05")
    z2 = np.load(cdir(bd, "eh0p05") / (f"{vn}_TBS_TB" + (f"_p{JS[(bd, 'eh0p05')]['runs'][f'{vn}_TBS_TB']['active_set']['n_passes']}" if vn == "C7" else "")) / "res.npz")
    vt_full = np.zeros(len(m2["X"]))
    vt_full[z2["nodes"]] = vm(z2["S2"].astype(float))
    edges = sorted(set(f1.edges) | set(f2.edges)) if vn == "C7" else [R_ENTRY]
    pe = np.array([(r, ZF) for r in edges])
    rows = []
    for p in (A, B):
        tri = m2["tri"][p]
        used = np.unique(tri)
        X2 = m2["X"]
        T = mtri.Triangulation(X2[:, 0], X2[:, 1], triangles=tri)
        itp = mtri.LinearTriInterpolator(T, vt_full)
        k = (f1.part == p) & f1.regular & (np.abs(f1.X[:, 1] - ZF) <= 2.0) & (f1.X[:, 0] >= 7.0) & (f1.X[:, 0] <= 10.5) & (f1.vt >= 0.5 * f1.Fy)
        idx = np.nonzero(k)[0]
        v2 = np.asarray(itp(f1.X[idx, 0], f1.X[idx, 1]).filled(np.nan))
        ok = np.isfinite(v2) & (v2 > 0)
        idx, v2 = idx[ok], v2[ok]
        q = f1.vt[idx] / v2
        de = cKDTree(pe).query(f1.X[idx])[0]
        for i, qq, dd in zip(idx, q, de):
            rows.append((p, int(f1.nodes[i]) + 1, float(f1.X[i, 0]), float(f1.X[i, 1]), float(qq), float(dd), float(f1.vt[i] / f1.Fy[i])))
    fail = [r for r in rows if abs(r[4] - 1.0) > 0.05]
    dz = max([r[5] for r in fail], default=0.0)
    dz = math.ceil(dz / 0.05 - 1e-9) * 0.05
    bins = {}
    for lo in np.arange(0.0, 2.0, 0.25):
        sel = [r for r in rows if lo <= r[5] < lo + 0.25]
        if sel:
            bins[f"{lo:.2f}-{lo + 0.25:.2f}"] = {"n": len(sel), "n_fail": sum(1 for r in sel if abs(r[4] - 1.0) > 0.05),
                                                 "max_abs_dev": round(max(abs(r[4] - 1.0) for r in sel), 4)}
    worst = sorted(fail, key=lambda r: -abs(r[4] - 1.0))[:6]
    return {"edges_r_mm": [round(e, 4) for e in edges], "edges_0p1_last_pass": [round(e, 4) for e in f1.edges],
            "edges_0p05_last_pass": [round(e, 4) for e in f2.edges], "n_nodes_tested": len(rows), "n_fail": len(fail),
            "d_zone_mm": round(dz, 3), "by_distance_from_edge": bins,
            "worst_fail": [{"part": r[0], "node_0p1": r[1], "r_z": [round(r[2], 3), round(r[3], 3)], "vm_ratio_0p1_over_0p05": round(r[4], 4),
                            "d_edge_mm": round(r[5], 3), "vm_over_Fty": round(r[6], 3)} for r in worst]}


DZONE = {}
for bd in BDS:
    z7 = nodal_test(bd, "C7")
    z5 = nodal_test(bd, "C5")
    DZONE[bd] = max(z7["d_zone_mm"], EXCL)
    out["stick_edge_zone"][bd] = {"C7": z7, "C5_contact_edge_comparison": z5, "d_zone_used_mm": DZONE[bd],
                                  "rule": "C7 cells outside the zone: regular AND farther than d_zone from every stick edge of the pass (at least the 1.0 mm "
                                          "exclusion the driver already applied around the entry tangent)"}

# ---------------- 3) every TB70 / TBS run at every abort state (0.1 level): cells incl. C7 outside the zone; matrix
js01 = {bd: JS[(bd, "eh0p1")] for bd in BDS}
CASES = (("LC1", ("B1_19",)), ("LC2", ("B1_1", "B1_16", "B1_19", "B1_21.65")), ("TB70", STATES), ("TBS", STATES))
for bd in BDS:
    for case, sts in CASES:
        for st in sts:
            cellset = {}
            for vn in VARS:
                key = f"{vn}_{case}_{st}"
                if key not in js01[bd]["runs"]:
                    continue
                flds, rj = load_run(bd, "eh0p1", js01[bd], key)
                if vn == "C7":
                    dz = DZONE[bd]
                    cl = cells_of(flds, vn, extra_mask=lambda f, dz=dz: f.dedge > dz)
                    cl["stick_edges_by_pass"] = {lab: [round(e, 4) for e in f.edges] for lab, f in flds}
                else:
                    cl = cells_of(flds, vn)
                out["checks_vs_driver_json"] += check_vs_json(cl, rj, f"{bd}/eh0p1/{key}")
                cl["interfaces"] = rj.get("interfaces")
                if vn == "C7":
                    cl["active_set"] = rj.get("active_set")
                cellset[vn] = cl
            if cellset:
                out["runs"][f"{bd}|{case}|{st}"] = cellset

# ---------------- 4) cells per the 234 (4) rule and the seat matrix
def cell_rule(cs, vn, p, cr, bd, rs):
    """the cell value of variant vn: regular where the all-node min is a thread tie end (J-TC03) or the regular converges at the reference
    state rs (TBS_TB for the TB states, LC2_B1_19 for the LC states); C7 outside the stick-edge zone."""
    if vn == "C7":
        v = cs[p]["outside_zone"][cr]
        basis = f"C7 outside the stick-edge zone (d > {DZONE[bd]} mm, 236 (9)(a))"
        allv = cs[p]["all"][cr]
        return v, basis, allv
    allv, regv = cs[p]["all"][cr], cs[p]["regular"][cr]
    if allv is None or regv is None:
        return allv or regv, "single set", allv
    if allv[7].startswith(THREAD_TIE):
        return regv, "regular: all-node minimum at the smeared-thread tie end, replaced by the J-TC03 thread-strip CALC (Mechanical, 236 (10))", allv
    rf = out[f"refinement_{rs}"].get(f"{bd}|{vn}", {}).get(f"{p}|regular|{cr}")
    if allv[6] > EXCL:
        return allv, "all-node minimum is regular", allv
    if rf and rf["converged_5pct"]:
        return regv, f"regular: converged at {rs} by the 5 % test", allv
    return allv, f"all-node: minimum at '{allv[7]}', no replacing sub-model and the regular value not shown converged", allv


for k, cs in out["runs"].items():
    bd, case, st = k.split("|")
    rs = REFSTATE["LC" if case.startswith("LC") else "TB"]
    mat = {}
    for p in (A, B):
        mat[p] = {}
        for cr in CRIT:
            per = {}
            for vn in MATRIX_VARS:
                if vn not in cs:
                    continue
                v, basis, allv = cell_rule(cs[vn], vn, p, cr, bd, rs)
                if v is None:
                    continue
                rf = out[f"refinement_{rs}"].get(f"{bd}|{vn}", {}).get(f"{p}|{'all' if basis.startswith('all-node') else 'regular'}|{cr}")
                est, flag = None, None
                if rf:
                    if cr != "MS_LCF":
                        Dv = demand(v[0])
                        est = {"MS_h0p05_estimate": round(1.0 / (Dv * rf["D_ratio_0p05_over_0p1"]) - 1.0, 4), "factor": rf["D_ratio_0p05_over_0p1"],
                               "factor_from": rs, "converged_5pct_at_ref": rf["converged_5pct"]}
                    if not rf["converged_5pct"]:
                        flag = (f"NOT CONVERGED at {rs}: demand ratio {rf['D_ratio_0p1_over_0p2']} (0.2 -> 0.1) and {rf['D_ratio_0p05_over_0p1']} "
                                f"(0.1 -> 0.05) at {rf['where_by_level']['eh0p05'][:2]} ({rf['where_by_level']['eh0p05'][2]}); quoted at h 0.1 with the "
                                f"h 0.05 estimate beside it")
                per[vn] = {"value": v, "basis": basis, "all_node": allv, "h0p05_estimate": est, "refinement_flag": flag}
            if not per:
                continue
            mn = min(per, key=lambda q: per[q]["value"][0])
            mn3 = min((q for q in per if q != "C7"), key=lambda q: per[q]["value"][0], default=None)
            mat[p][cr] = {"seat_matrix": per[mn]["value"][0], "from": mn, "min_C5_C3n_C4n": per[mn3]["value"][0] if mn3 else None,
                          "from_3": mn3, "per_variant": per}
    out["seat_matrix"][k] = mat

out["d_zone_mm"] = DZONE
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print("checks vs driver json (should be empty):", out["checks_vs_driver_json"][:10])
for bd in BDS:
    z = out["stick_edge_zone"][bd]
    print(bd, "C7 zone", z["C7"]["d_zone_mm"], z["C7"]["edges_r_mm"], z["C7"]["n_fail"], "/", z["C7"]["n_nodes_tested"], z["C7"]["by_distance_from_edge"])
    print(bd, "C5 cmp", z["C5_contact_edge_comparison"]["d_zone_mm"], z["C5_contact_edge_comparison"]["n_fail"], "/", z["C5_contact_edge_comparison"]["n_nodes_tested"],
          z["C5_contact_edge_comparison"]["by_distance_from_edge"])
for rs in REFSTATE.values():
    for k, tab in out[f"refinement_{rs}"].items():
        for kk, v in tab.items():
            if "regular" in kk and ("MS_y_SF1" in kk or "MS_PQ" in kk):
                print(rs, k, kk, v["MS_by_level"], v["D_ratio_0p05_over_0p1"], v["converged_5pct"], v["where_by_level"]["eh0p05"])
for k, mat in out["seat_matrix"].items():
    line = [k]
    for p in (A, B):
        for cr in ("MS_y", "MS_u", "MS_prim_y", "MS_PQ", "MS_LCF"):
            if cr in mat[p]:
                line.append(f"{p[-5:]} {cr} {mat[p][cr]['seat_matrix']:+.3f}({mat[p][cr]['from']}) 3:{mat[p][cr]['min_C5_C3n_C4n']:+.3f}")
    print(" | ".join(line))
