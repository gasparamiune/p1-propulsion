"""REV-MECH-2 (independent reviewer): re-post of FEA3D stored unit fields with own code (no FEA3D module imported).

Inputs (read-only): FEA3D run folder /home/claude/work/fea3d/runs/<run>/<state>/{f1.inp.gz, fields.npz, T.npz}, <run>/model.json
(connector / tie lists = model definition), hub 04-fea/src/engmat.py (allowables, 46ba163b864c7fc5).
Own: deck parse (rm2_deck.py), node temperatures from the solved deck's TH step, combination of unit steps, von Mises / principal
stresses, MS at node temperature, regular-node set rebuilt with the published rule (1.0 mm from RBE3 / rigid / ground / tie-patch-edge
/ re-entrant-edge (dihedral > 30 deg, concave) / bad-tet (q < 0.1) nodes), and the exclusion-band audit (minimum MS per exclusion class).

usage: python -I rm2_repost.py <run> <state[,state..]> <casegroup: LC1|FA1|FA1T|LC2|LC2F(interim, superseded)> <out.json>
Units mm, N, MPa, K.  2026-10-19.
"""
from __future__ import annotations
import sys, json, math, time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rm2_deck  # noqa: E402

HUB = Path("/home/claude/work/shared-fallback/engine")
sys.path.insert(0, str(HUB / "04-fea/src"))
import engmat  # noqa: E402  (hub materials module, read-only)

RUNS = Path("/home/claude/work/fea3d/runs")
CACHE = Path("/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/r2cache")
MAT = {"AL6061_T6": "AL6061-T6", "AL6061_T6_NX": "AL6061-T6", "AL7075_T6": "AL7075-T6", "AL7075_T6_NX": "AL7075-T6",
       "GLIDCOP_AL15": "GLIDCOP-AL15", "IN718": "IN718", "GRAPHITE_ISO": "GRAPHITE-ISO", "CARBON_PHENOLIC": "CARBON-PHENOLIC",
       "FLEX_GRAPHITE_OI": "FLEX-GRAPHITE-OI", "SS316L": "SS316L"}
BRITTLE = {"GRAPHITE-ISO": ("St", "Sc"), "CARBON-PHENOLIC": (None, "Sc"), "FLEX-GRAPHITE-OI": (None, "Sc")}
# load-case constants as published by the lead / interfaces (REPORT-FEA3D 2.3; CHANGELOG 188 (9), 194, 230; REQUIREMENTS ENG-09)
PC_MAX = 2.501007            # MPa LC1
P_MAN = 7.0                  # MPa manifold
G_AX, G_LAT = 4.04, 0.61     # g flight (gnc.json v3.1)
OP_NET = 202.92487           # N/MPa (FEA3D pressure resultant; checked separately in rm2_handcalc.py)
T_STUCK = 907.7              # N stuck-pintle thrust (loadcases_v1 LC2F, structure case) -> 4.473 MPa on OP_NET (interim basis only)
P_MEOP = 4.5                 # MPa chamber MEOP (ENG-09 45 bar; loadcases_v1 LC2 chamber_Pa 4.5e6) -> group LC2 (final basis)
FA1 = {"FA1Q": 9.0, "FA1D": 9.3, "FA1U": 10.2, "FA1S": 15.1038}   # MPa abs on the OP field (lead 194; FA1S 2 x 75.519 bar)
FA1_R230 = {"R230_T01": 9.4, "R230_B01_1": 12.1, "R230_B1_20": 14.7}  # lead 230 (2) restated band values (bar/10)
FA1_THRUST = 3600.0          # N, FA1T total net thrust (lead 194: 1.8 kN x 4 ms x DLF 2.0)
FACES = [(0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4), (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6)]   # C3D10 faces: corners + mids (0-based)


def body_name(es):
    return es.replace("B_", "").replace("TC0", "TC-0").replace("NZ0", "NZ-0").replace("GM0", "GM-0").replace("GM1", "GM-1") \
        .replace("PD01", "PD-01").replace("FD01", "FD-01").replace("TC09", "TC-09")


def load_deck(run, state):
    stem = CACHE / f"{run}_{state}"
    if not Path(str(stem) + ".npz").exists():
        d = rm2_deck.parse(RUNS / run / state / "f1.inp.gz")
        rm2_deck.save(d, stem)
    z = np.load(str(stem) + ".npz")
    meta = json.loads(Path(str(stem) + ".json").read_text())
    return z, meta


def vm(S):
    sx, sy, sz, txy, tyz, tzx = (S[..., k] for k in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def principal(S):
    T = np.empty(S.shape[:-1] + (3, 3))
    T[..., 0, 0], T[..., 1, 1], T[..., 2, 2] = S[..., 0], S[..., 1], S[..., 2]
    T[..., 0, 1] = T[..., 1, 0] = S[..., 3]
    T[..., 1, 2] = T[..., 2, 1] = S[..., 4]
    T[..., 0, 2] = T[..., 2, 0] = S[..., 5]
    w = np.linalg.eigvalsh(T)
    return w[..., 2], w[..., 0]


def allow(mat, key, TK):
    Mt = engmat.MATERIALS[mat]
    if key is None or key not in Mt:
        return None
    d = Mt[key]
    TC = np.asarray(TK) - 273.15
    if "T_C" in d:
        return np.interp(TC, d["T_C"], d["v"]) / 1e6
    return np.full(TC.shape, d["v"] / 1e6)


class Mesh:
    def __init__(self, z, meta):
        self.X = np.zeros((int(z["nodes_id"].max()) + 2, 3))
        self.X[z["nodes_id"]] = z["nodes_x"]
        self.bodies = {}
        self.n_mesh = 0
        for es in meta["bodies"]:
            E = z[f"E_{es}"]
            nm = body_name(es)
            nodes = np.unique(E[:, 1:])
            self.bodies[nm] = {"E": E[:, 1:], "nodes": nodes, "mat_deck": meta["sections"][es], "mat": MAT[meta["sections"][es]]}
            self.n_mesh = max(self.n_mesh, int(nodes.max()))
        self.node_body = np.full(len(self.X), -1, np.int32)
        for i, (nm, b) in enumerate(self.bodies.items()):
            self.node_body[b["nodes"]] = i
        self.names = list(self.bodies)

    def boundary(self, nm):
        b = self.bodies[nm]
        if "bf" in b:
            return b
        E = b["E"]
        F = np.concatenate([E[:, list(f)] for f in FACES])          # (4 ne, 6)
        opp = np.concatenate([E[:, [3]], E[:, [2]], E[:, [0]], E[:, [1]]])[:, 0]
        key = np.sort(F[:, :3], 1)
        _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        bnd = cnt[inv.ravel()] == 1
        bf = F[bnd]
        X = self.X
        P = X[bf[:, :3]]
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        c = P.mean(1)
        s = np.sign(np.einsum("ij,ij->i", n, c - X[opp[bnd]]))
        n = n * s[:, None]
        a = 0.5 * np.linalg.norm(n, axis=1)
        b["bf"], b["fn"], b["fc"], b["fa"] = bf, n / np.maximum(2 * a, 1e-30)[:, None], c, a
        return b

    def reentrant_nodes(self, nm, ang=30.0):
        b = self.boundary(nm)
        C, Mid = b["bf"][:, :3], b["bf"][:, 3:6]
        E = np.vstack([np.sort(C[:, [0, 1]], 1), np.sort(C[:, [1, 2]], 1), np.sort(C[:, [2, 0]], 1)])
        Fi = np.tile(np.arange(len(C)), 3)
        Mn = np.concatenate([Mid[:, 0], Mid[:, 1], Mid[:, 2]])
        key = E[:, 0].astype(np.int64) * (len(self.X) + 1) + E[:, 1]
        o = np.argsort(key, kind="stable")
        ks = key[o]
        same = ks[1:] == ks[:-1]
        i1, i2 = o[:-1][same], o[1:][same]
        f1, f2 = Fi[i1], Fi[i2]
        cosang = np.einsum("ij,ij->i", b["fn"][f1], b["fn"][f2])
        conc = (np.einsum("ij,ij->i", b["fc"][f2] - b["fc"][f1], b["fn"][f1]) > 1e-6) & \
               (np.einsum("ij,ij->i", b["fc"][f1] - b["fc"][f2], b["fn"][f2]) > 1e-6)
        sel = (cosang < math.cos(math.radians(ang))) & conc
        nodes = np.unique(np.concatenate([E[i1[sel]].ravel(), Mn[i1[sel]]]))
        turn = np.degrees(np.arccos(np.clip(cosang[sel], -1, 1)))
        return nodes, int(sel.sum()), turn

    def bad_tet_nodes(self, nm, qb=0.1):
        E = self.bodies[nm]["E"]
        a, b_, c, d = (self.X[E[:, k]] for k in range(4))
        V = np.abs(np.einsum("ij,ij->i", np.cross(b_ - a, c - a), d - a)) / 6.0
        L2 = sum(((p - q) ** 2).sum(1) for p, q in ((a, b_), (a, c), (a, d), (b_, c), (b_, d), (c, d)))
        q = 12.0 * (3.0 * V) ** (2.0 / 3.0) / np.maximum(L2, 1e-30)
        bad = q < qb
        return (np.unique(E[bad].ravel()) if bad.any() else np.zeros(0, np.int64)), int(bad.sum()), float(q.min())


def singular_sets(mesh, model, z):
    n = mesh.n_mesh
    S = {}
    S["rigid"] = np.unique([x for lab, nodes, ref, rot in model["rigid"] for x in nodes if x <= n]).astype(np.int64)
    S["rbe3"] = np.unique([x for lab, d in model["rbe"].items() for x in d["nodes"] if x <= n]).astype(np.int64)
    S["ground"] = np.unique([x for x in model["gnd"] if x <= n]).astype(np.int64)
    S["tie_edge"] = np.unique([x for lab, L in model["tie_edges"].items() for x in L]).astype(np.int64)
    re_, bt = [], []
    rep = {}
    for nm in mesh.names:
        r_nodes, ne, turn = mesh.reentrant_nodes(nm)
        b_nodes, nb, qmin = mesh.bad_tet_nodes(nm)
        re_.append(r_nodes)
        bt.append(b_nodes)
        rep[nm] = {"reentrant_edges": ne, "reentrant_nodes": int(len(r_nodes)), "bad_tets": nb, "q_min": qmin}
    S["reentrant"] = np.unique(np.concatenate(re_)).astype(np.int64)
    S["bad_tet"] = np.unique(np.concatenate(bt)).astype(np.int64)
    return S, rep


def regular_mask(mesh, S, ex_r=1.0):
    n = mesh.n_mesh
    allsing = np.unique(np.concatenate([v for v in S.values() if len(v)]))
    tree = cKDTree(mesh.X[allsing])
    d, j = tree.query(mesh.X[1:n + 1], k=1)
    dist = np.full(n + 1, np.inf)
    dist[1:] = d
    reg = np.zeros(n + 1, bool)
    reg[1:] = d > ex_r
    reg[allsing] = False
    # class of the nearest singular node (for the band audit)
    cls = np.full(n + 1, "", dtype=object)
    owner = {}
    for k, v in S.items():
        for x in v:
            owner.setdefault(int(x), k)
    near = allsing[j]
    cls[1:] = [owner[int(x)] for x in near]
    return reg, dist, cls


def combos(group, state):
    if group == "LC1":
        lat = [{"GX": G_LAT}, {"GX": -G_LAT}, {"GY": G_LAT}, {"GY": -G_LAT}]
        return [("LC1", [dict({"OP": PC_MAX, "PM": P_MAN, "GZ": G_AX}, **l) for l in lat], 1.5, 2.0)]
    if group == "LC2F":
        # INTERIM basis (superseded; kept only to reproduce results/rm2_repost_lc2f_lc1v351_c71.json): OP from the LC2F thrust
        # 907.7 N / 202.92 N/MPa = 4.473 MPa; the label 'LC2F' was wrong for the pressure parts (see group LC2 and the review RM2-02).
        pc = T_STUCK / OP_NET
        lat = [{"GX": G_LAT * math.cos(2 * math.pi * k / 8), "GY": G_LAT * math.sin(2 * math.pi * k / 8)} for k in range(8)]
        subs = [dict({"OP": pc, "PM": P_MAN, "GZ": gz}, **l) for gz in (0.0, G_AX) for l in lat]
        return [("LC2F_SF1.0/1.5", subs, 1.0, 1.5), ("LC2_ENG09_SF1.5/2.0", subs, 1.5, 2.0)]
    if group == "LC2":
        # FINAL basis: loadcases_v1.json LC2 (cbafa22eb69ef039): chamber MEOP 4.5 MPa (ENG-09, 45 bar) on the OP distribution
        # (vacuum outside) + manifold 7.0 MPa, at the stored thermal states, SF 1.5 / 2.0 (ENG-09; line 188 (9) 'LC1-LC4').
        # Flight inertia 0.61 g lateral (8 directions) x GZ {0, 4.04 g} added (not in the LC2 definition; small, kept as a bound).
        lat = [{"GX": G_LAT * math.cos(2 * math.pi * k / 8), "GY": G_LAT * math.sin(2 * math.pi * k / 8)} for k in range(8)]
        subs = [dict({"OP": P_MEOP, "PM": P_MAN, "GZ": gz}, **l) for gz in (0.0, G_AX) for l in lat]
        return [("LC2_MEOP45_SF1.5/2.0", subs, 1.5, 2.0)]
    if group == "FA1":
        out = [(k, [{"OP": v, "PM": P_MAN}], 1.0, 1.0) for k, v in FA1.items()]
        out += [(k, [{"OP": v, "PM": P_MAN}], 1.0, 1.0) for k, v in FA1_R230.items()]
        return out
    if group == "FA1T":
        # lead 194 thrust spike 1.8 kN x 4 ms x DLF 2.0 = 3600 N total for T <= 20 ms paths: shell at 90 bar abs (OP 9.0) + unit net
        # thrust step TZ x (3600 - OP_NET x 9.0) N, manifold 7.0 MPa, SF 1.0 (REPORT-FEA3D 2.3; FEA3D reports gimbal / mount parts only)
        return [("FA1T", [{"OP": 9.0, "PM": P_MAN, "TZ": FA1_THRUST - OP_NET * 9.0}], 1.0, 1.0)]
    raise ValueError(group)


def combine(F, key, co):
    base = F[f"{key}_TH"].astype(np.float64) if f"{key}_TH" in F else 0.0
    out = np.array(base, dtype=np.float64, copy=True) if not np.isscalar(base) else None
    if out is None:
        any_k = next(k for k in F if k.startswith(key + "_"))
        out = np.zeros(F[any_k].shape)
        base = np.zeros(F[any_k].shape)
    mech = np.zeros_like(out)
    for st, c in co.items():
        if c:
            mech += c * (F[f"{key}_{st}"].astype(np.float64) - base)
    return out + mech, mech


def margins(mesh, F, T, subs, sfy, sfu, sets, cls, dist):
    """per part: min MS in each node set, with the node data.  Metals MS_y, MS_u (independent minima) + primary-only MS;
    brittle: s1/St, s3/Sc at SF sfu; carbon-phenolic char zone (T > T_char) primary s3."""
    ev = [combine(F, "S", co) for co in subs]
    rows = {}
    for nm in mesh.names:
        b = mesh.bodies[nm]
        nodes = b["nodes"]
        mat = b["mat"]
        Tn = T[nodes]
        brittle = mat in BRITTLE
        Mt = engmat.MATERIALS[mat]
        msy = np.full(len(nodes), np.inf)
        msu = np.full(len(nodes), np.inf)
        msp = np.full(len(nodes), np.inf)
        vmx = np.zeros(len(nodes))
        arg = np.zeros(len(nodes), np.int16)
        if brittle:
            kt, kc = BRITTLE[mat]
            St, Sc = allow(mat, kt, Tn), allow(mat, kc, Tn)
            Tch = Mt["T_char_C"]["v"] if "T_char_C" in Mt else None
            char = (Tn - 273.15 > Tch) if Tch is not None else np.zeros(len(nodes), bool)
            sf = sfu
            for si, (S, Sm) in enumerate(ev):
                s1, s3 = principal(S[nodes])
                ms = np.full(len(nodes), np.inf)
                if St is not None:
                    ms = np.minimum(ms, np.where(s1 > 0, St / (sf * np.maximum(s1, 1e-9)) - 1, np.inf))
                if Sc is not None:
                    ms = np.minimum(ms, np.where(s3 < 0, Sc / (sf * np.maximum(-s3, 1e-9)) - 1, np.inf))
                if char.any() and Sc is not None:
                    _, s3m = principal(Sm[nodes])
                    msc = np.where(s3m < 0, Sc / (sf * np.maximum(-s3m, 1e-9)) - 1, np.inf)
                    ms = np.where(char, msc, ms)
                upd = ms < msy
                arg[upd] = si
                msy = np.minimum(msy, ms)
                vmx = np.maximum(vmx, vm(S[nodes]))
        else:
            Fy, Fu = allow(mat, "Fty", Tn), allow(mat, "Ftu", Tn)
            for si, (S, Sm) in enumerate(ev):
                v = vm(S[nodes])
                vmech = vm(Sm[nodes])
                ms = Fy / (sfy * np.maximum(v, 1e-9)) - 1
                upd = ms < msy
                arg[upd] = si
                msy = np.minimum(msy, ms)
                msu = np.minimum(msu, Fu / (sfu * np.maximum(v, 1e-9)) - 1)
                msp = np.minimum(msp, Fy / (sfy * np.maximum(vmech, 1e-9)) - 1)
                vmx = np.maximum(vmx, v)
        out = {}
        for tag, msk_all in sets.items():
            msk = msk_all[nodes]
            if not msk.any():
                continue
            i = int(np.argmin(np.where(msk, msy, np.inf)))
            nd = int(nodes[i])
            x = mesh.X[nd]
            S, Sm = ev[int(arg[i])]
            row = {"MS": float(msy[i]), "node": nd, "xyz": [round(float(c), 3) for c in x],
                   "r_th_z": [round(math.hypot(x[0], x[1]), 3), round(math.degrees(math.atan2(x[1], x[0])), 1), round(float(x[2]), 3)],
                   "T_C": round(float(T[nd] - 273.15), 1), "vm": round(float(vm(S[nd])), 2), "vm_mech": round(float(vm(Sm[nd])), 2),
                   "subcase": int(arg[i]), "dist_to_singular_mm": (round(float(dist[nd]), 3) if np.isfinite(dist[nd]) else None),
                   "nearest_singular_class": cls[nd], "n_nodes": int(msk.sum())}
            if not brittle:
                row["MS_u"] = float(np.min(np.where(msk, msu, np.inf)))
                row["MS_primary"] = float(np.min(np.where(msk, msp, np.inf)))
                row["Fty"] = round(float(allow(mat, "Fty", np.array([T[nd]]))[0]), 2)
            else:
                s1, s3 = principal(S[nd][None])
                row["s1"], row["s3"] = round(float(s1[0]), 2), round(float(s3[0]), 2)
            out[tag] = row
        rows[nm] = out
    return rows


def main(run, states, group, outp):
    t0 = time.time()
    model = json.loads((RUNS / run / "model.json").read_text())
    res = {"run": run, "group": group, "date": "2026-10-19", "tool": "REV-MECH-2 rm2_repost.py (own code)",
           "engmat_sha16": "46ba163b864c7fc5", "states": {}}
    for state in states:
        z, meta = load_deck(run, state)
        mesh = Mesh(z, meta)
        F = dict(np.load(RUNS / run / state / "fields.npz"))
        # node temperatures from the solved deck (TH step); compare with FEA3D T.npz (per-body arrays)
        T = np.full(len(mesh.X), 293.15)
        if "T_0" in z.files:
            Tt = z["T_0"]
            T[Tt[:, 0].astype(int)] = Tt[:, 1]
        tchk = {}
        Tz = np.load(RUNS / run / state / "T.npz")
        for nm in mesh.names:
            nodes = mesh.bodies[nm]["nodes"]
            if nm in Tz.files and len(Tz[nm]) == len(nodes):
                tchk[nm] = float(np.max(np.abs(Tz[nm] - T[nodes])))
        S, srep = singular_sets(mesh, model, z)
        reg, dist, cls = regular_mask(mesh, S)
        n = mesh.n_mesh
        sets = {"all": np.ones(n + 1, bool), "regular": reg}
        for k, v in S.items():           # nodes excluded because of class k: nearest singular node of class k within 1 mm, or a member
            m = np.zeros(n + 1, bool)
            m[1:] = (~reg[1:]) & (cls[1:] == k)
            sets[f"excl_{k}"] = m
        st_out = {"T_deck_vs_Tnpz_maxabs_K": tchk, "singular_counts": {k: int(len(v)) for k, v in S.items()},
                  "n_regular": int(reg[1:].sum()), "n_mesh": n, "mesh_report": srep, "cases": {}}
        for cid, subs, sfy, sfu in combos(group, state):
            st_out["cases"][cid] = {"subcases": subs, "SF": [sfy, sfu], "parts": margins(mesh, F, T, subs, sfy, sfu, sets, cls, dist)}
        res["states"][state] = st_out
        print(f"[rm2_repost {run} {state} {group}] {time.time() - t0:.1f} s", flush=True)
    Path(outp).write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2].split(","), sys.argv[3], sys.argv[4])
