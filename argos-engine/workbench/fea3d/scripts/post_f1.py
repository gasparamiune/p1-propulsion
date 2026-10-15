"""FEA3D F1 post-processing: load-case combination of unit fields, per-part margins (S-AX criteria port extended to the 3-D parts),
singular-point exclusion, SCL linearisation (3-D, several azimuths) for the S-AX cross-check, airframe reactions, connector forces.

usage: post_f1.py RUN STATE[,STATE...] [cases=LC1,...] [ex_r=1.0]
Units: mm, N, MPa, K.  Engine frame (+Z forward, pivot origin).  fea3d 2026-10-13.
"""
from __future__ import annotations
import sys, json, math, csv, time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import asm_build as AB      # noqa: E402
import asm3d as A3          # noqa: E402
import fe3d                 # noqa: E402

RUNS = Path("/home/claude/work/fea3d/runs")
RES = Path("/home/claude/work/fea3d/results")
engmat = A3.engmat
PC_MAX = 2.501007          # MPa, S-AX info params Pc_max (LC1, same as S-AX)
P_MAN = 7.0                # MPa, manifold MEOP_tank (S-AX LC1)
G_AX_FLIGHT = 4.04         # g, gnc.json v3.1 design_limit_loads.axial_accel_flight_g (SIM, max of 500 runs; S-AX used 3.65)
G_LAT_FLIGHT = 0.61        # g, gnc.json v3.1 lateral_accel_at_pivot_flight_g (SIM max)
OP_NET_Z = 202.92487       # N/MPa, 3-D OP pressure resultant along the engine axis (pressure.json OP_net, v3.5.1 L1)
STEPS_DEFAULT = ["TH", "OP", "PM", "GX", "GY", "GZ"]
BRITTLE = {"GRAPHITE-ISO": ("St", "Sc"), "CARBON-PHENOLIC": (None, "Sc"), "FLEX-GRAPHITE-OI": (None, "Sc"), "ZIRCONIA-FS": ("St", "Sc")}

# part roles (S-AX PART_ROLE for the axisymmetric parts, extended for the 3-D-only parts)
ROLE = {
    "TC-01": ("LOAD-BEARING", "case, pressure vessel + thrust path: metal (Fty/Ftu at T; primary SF, P+Q shakedown 2 Fty)"),
    "TC-02": ("LOAD-BEARING", "forward closure (head): metal"),
    "TC-03": ("LOAD-BEARING", "seat insert, pressure + seat: metal (v3.5: IN718; v3.5.1: GlidCop AL-15, TB1 recessed flange, M14 thread)"),
    "TC-04": ("LOAD-BEARING", "bonnet, manifold pressure: metal"),
    "TC-09": ("LOAD-BEARING", "aft section + nozzle holder (J1 lip): metal"),
    "NZ-01": ("LOAD-BEARING (brittle)", "graphite throat insert: s1 vs St, s3 vs Sc at RT strength (rise with T not credited), total stress"),
    "NZ-02": ("ABLATIVE / INSULATING", "carbon-phenolic sleeve: virgin zone brittle compression on total stress; char zone primary only"),
    "NZ-03": ("LOAD-BEARING + ABLATIVE", "carbon-phenolic J1 hot-layer washer: virgin zone brittle compression on total stress; char zone "
              "PRIMARY bearing vs char strength (ASSUMED)"),
    "NZ-04": ("SEAL (bearing)", "flexible-graphite lip seal: compression vs maximum gasket stress (ASSUMED); T vs class limit"),
    "GM-01": ("LOAD-BEARING", "collar half +Y: thrust path case -> inner gimbal pin; servo-1 lever: metal (7075-T6)"),
    "GM-02": ("LOAD-BEARING", "collar half -Y: thrust path case -> inner gimbal pin; servo-2 lever: metal (7075-T6)"),
    "PD-01R": ("LOAD-BEARING", "pintle drive frame +Y piece: needle reaction into the head: metal"),
    "PD-01S": ("LOAD-BEARING", "pintle drive frame -Y piece: needle reaction into the head: metal"),
    "FD-01": ("LOAD-BEARING", "oxidiser inlet block E1-M: manifold pressure cap + feed/bleed bracket loads: metal"),
    "GM-03": ("LOAD-BEARING", "gimbal ring: thrust path inner -> outer bearings: metal"),
    "GM-08a": ("LOAD-BEARING", "yoke post +X: outer bearing seat -> thrust rings: metal"),
    "GM-08b": ("LOAD-BEARING", "yoke post -X: outer bearing seat -> thrust rings: metal"),
    "GM-09": ("LOAD-BEARING", "upper thrust ring, airframe interface 8 x M5: metal"),
    "GM-10": ("LOAD-BEARING", "lower ring, airframe 8 x M5, servo base: metal"),
    "GM-13": ("LOAD-BEARING", "TVC servo-1 bracket: metal"),
    "GM-14": ("LOAD-BEARING", "TVC servo-2 bracket: metal"),
    "GM-16a": ("LOAD-BEARING", "TVC horn servo 1: metal (7075-T6)"),
    "GM-16b": ("LOAD-BEARING", "TVC horn servo 2: metal (7075-T6)"),
}


# =============================================================================================== loading
def load_model(name):
    wd = RUNS / name
    meta = json.loads((wd / "model.json").read_text())
    var = {k: (tuple(v) if isinstance(v, list) else v) for k, v in meta["variant"].items()}
    if var.get("refine"):
        var["refine"] = {bn: [tuple(b) for b in L] for bn, L in var["refine"].items()}
    level = meta.get("level", 1.0)
    if meta.get("cad", "v35") != A3.CAD:
        raise RuntimeError(f"run {name} is CAD {meta.get('cad', 'v35')} but FEA3D_CAD = {A3.CAD}")
    M = AB.Asm(level=level, variant=var)
    AB.define(M)
    if any(str(st).startswith("FREQ") for st in (meta.get("steps") or [])):
        AB.modal_masses(M)          # adds the RBE3 mass reference nodes / equations of the modal deck
    nmax = max([int(k) for k in meta["extra"]] + [b["noff"] + b["n"] - 1 for b in meta["bodies"].values()])
    if M.next_n - 1 != nmax or len(M.C.eqs) != meta["n_eq"]:
        raise RuntimeError(f"rebuilt model differs from the solved one: nodes {M.next_n - 1} vs {nmax}, eqs {len(M.C.eqs)} vs {meta['n_eq']}")
    return M, meta


def load_fields(name, state):
    z = np.load(RUNS / name / state / "fields.npz")
    return {k: z[k] for k in z.files}


def node_arrays(M, name, state):
    n = M.n_mesh
    body = np.full(n + 1, -1, np.int32)
    T = np.full(n + 1, A3.T_REF)
    X = np.zeros((n + 1, 3))
    Tz = np.load(RUNS / name / state / "T.npz")
    names = list(M.bodies)
    for i, (nm, b) in enumerate(M.bodies.items()):
        ids = b.noff + np.arange(len(b.X0))
        body[ids] = i
        T[ids] = Tz[nm]
        X[ids] = M.Xp[nm]
    return names, body, T, X


# =============================================================================================== tensors
def vm(S):
    sx, sy, sz, txy, tyz, tzx = (S[..., k] for k in range(6))
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3.0 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def tensor(S):
    T = np.empty(S.shape[:-1] + (3, 3))
    T[..., 0, 0], T[..., 1, 1], T[..., 2, 2] = S[..., 0], S[..., 1], S[..., 2]
    T[..., 0, 1] = T[..., 1, 0] = S[..., 3]
    T[..., 1, 2] = T[..., 2, 1] = S[..., 4]
    T[..., 2, 0] = T[..., 0, 2] = S[..., 5]
    return T


def principal(S):
    w = np.linalg.eigvalsh(tensor(S.astype(np.float64)))
    return w[..., 2], w[..., 0]


def allowables(mat, T_K):
    TC = np.asarray(T_K) - 273.15
    Mt = engmat.MATERIALS[mat]

    def tab(key):
        if key is None or key not in Mt:
            return None
        d = Mt[key]
        if "T_C" in d:
            return np.interp(TC, d["T_C"], d["v"]) / 1e6
        return np.full(TC.shape, d["v"] / 1e6)
    if mat in BRITTLE:
        kt, kc = BRITTLE[mat]
        return tab(kt), tab(kc)
    return tab("Fty"), tab("Ftu")


# =============================================================================================== singular / quality sets
def tet_quality(X, T10):
    a, b, c, d = (X[T10[:, k]] for k in range(4))
    V = np.abs(np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a)) / 6.0
    L2 = sum(((p - q) ** 2).sum(1) for p, q in ((a, b), (a, c), (a, d), (b, c), (b, d), (c, d)))
    return 12.0 * (3.0 * V) ** (2.0 / 3.0) / np.maximum(L2, 1e-30)


def reentrant_edge_nodes(b, ang_deg=30.0):
    """Corner + mid nodes (local ids) of sharp concave boundary edges (dihedral turn > ang_deg): geometric singular lines."""
    C, Mid = b.bf_n[:, :3], b.bf_n[:, 3:6]
    E = np.vstack([np.sort(C[:, [0, 1]], 1), np.sort(C[:, [1, 2]], 1), np.sort(C[:, [2, 0]], 1)])
    F = np.tile(np.arange(len(C)), 3)
    Mn = np.concatenate([Mid[:, 0], Mid[:, 1], Mid[:, 2]])
    key = E[:, 0].astype(np.int64) * (len(b.X0) + 1) + E[:, 1]
    o = np.argsort(key, kind="stable")
    ks = key[o]
    same = ks[1:] == ks[:-1]
    i1, i2 = o[:-1][same], o[1:][same]
    f1, f2 = F[i1], F[i2]
    cosang = np.einsum("ij,ij->i", b.fn[f1], b.fn[f2])
    conc = (np.einsum("ij,ij->i", b.fc[f2] - b.fc[f1], b.fn[f1]) > 1e-6) & (np.einsum("ij,ij->i", b.fc[f1] - b.fc[f2], b.fn[f2]) > 1e-6)
    sel = (cosang < math.cos(math.radians(ang_deg))) & conc
    nodes = np.unique(np.concatenate([E[i1[sel]].ravel(), Mn[i1[sel]]]))
    return nodes, int(sel.sum())


def singular_sets(M, X, ex_r=1.0, q_bad=0.1):
    """Boolean 'regular' mask over mesh node ids (True = outside ex_r of every idealisation singularity) + report."""
    n = M.n_mesh
    pts = {}
    lab_nodes = {"rigid_connectors": [], "rbe3_couplings": [], "ground": [], "tie_patch_edges": [], "reentrant_edges": [], "bad_tets": []}
    for lab, nodes, ref, rot in M.rigid:
        lab_nodes["rigid_connectors"] += [int(x) for x in nodes if int(x) <= n]
    for lab, d in M.rbe.items():
        lab_nodes["rbe3_couplings"] += [int(x) for x in d["nodes"] if int(x) <= n]
    lab_nodes["ground"] = [int(x) for x in M.gnd if int(x) <= n]
    for lab, L in getattr(M, "tie_edges", {}).items():
        lab_nodes["tie_patch_edges"] += [int(x) for x in L]
    nre = 0
    qrep = {}
    for nm, b in M.bodies.items():
        loc, ne = reentrant_edge_nodes(b)
        nre += ne
        lab_nodes["reentrant_edges"] += [int(x) for x in b.gn(loc)]
        q = tet_quality(b.X0, b.T10)
        bad = q < q_bad
        qrep[nm] = {"q_min": float(q.min()), "n_q_below": int(bad.sum()), "n_reentrant_nodes": int(len(loc))}
        if bad.any():
            lab_nodes["bad_tets"] += [int(x) for x in b.gn(np.unique(b.T10[bad].ravel()))]
    allsing = np.unique(np.concatenate([np.asarray(v, np.int64) for v in lab_nodes.values() if len(v)]))
    tree = cKDTree(X[allsing])
    d, _ = tree.query(X[1:], k=1)
    reg = np.zeros(n + 1, bool)
    reg[1:] = d > ex_r
    reg[allsing] = False
    rep = {"ex_r_mm": ex_r, "q_bad": q_bad, "counts": {k: len(set(v)) for k, v in lab_nodes.items()}, "n_reentrant_edges": nre,
           "n_regular": int(reg[1:].sum()), "n_nodes": n, "quality": qrep}
    return reg, rep, {k: np.unique(np.asarray(v, np.int64)) for k, v in lab_nodes.items()}


# =============================================================================================== combinations
# FA-1 (lead 194 period domain; S-AX convention: bar abs on the OP unit field, vacuum outside; manifold 70 bar; SF 1.0, line 177/188 (9))
FA1_BAR = {"FA1Q": 90.0, "FA1D": 93.0, "FA1U": 102.0, "FA1S": 2.0 * 75.519}
FA1_THRUST_N = 3600.0          # 1.8 kN x 4 ms spike x DLF 2.0 (line 194) for the thrust-path parts with T <= 20 ms
GIMBAL_PARTS = ["GM-01", "GM-02", "GM-03", "GM-08a", "GM-08b", "GM-09", "GM-10", "GM-13", "GM-14", "GM-16a", "GM-16b"]


def combos(state, steps=None):
    """[(id, title, sub-cases [coef dicts], SF_y, SF_u, criterion, parts or None)] for one thermal state (B1_*: LC1; A1_*: FA-1)."""
    if str(state).startswith("A1"):
        out = []
        for cid, bar in FA1_BAR.items():
            what = {"FA1Q": "T <= 0.1 ms paths: quasi-static 90 bar abs (yield and ultimate)",
                    "FA1D": "0.1 < T <= 1 ms paths: YIELD at 93 bar abs (ultimate column informative)",
                    "FA1U": "0.1 < T <= 1 ms paths: ULTIMATE at 102 bar abs (yield column informative)",
                    "FA1S": "T > 1 ms paths until the modal closure: FA1S step bound 2.0 x 75.519 = 151.04 bar abs (yield and ultimate)"}[cid]
            out.append((cid, f"FMEA FA-1 {cid}: {what}; Pc {bar:.2f} bar abs on the operating distribution (vacuum outside) + manifold "
                             f"{P_MAN * 10:.0f} bar, A1 relight thermal state {state}", [{"OP": bar / 10.0, "PM": P_MAN}], 1.0, 1.0,
                        "failure case, SF 1.0: yield Fty(T) and ultimate Ftu(T); brittle St/Sc (lead 177, 188 (9), 194)", None))
        if steps is None or "TZ" in steps:
            dF = FA1_THRUST_N - OP_NET_Z * FA1_BAR["FA1Q"] / 10.0
            out.append(("FA1T", f"FA-1 thrust spike on the thrust path (T <= 20 ms): shell at the quasi-static 90 bar abs (OP {OP_NET_Z * 9.0:.0f} N) "
                                f"+ unit net thrust TZ x {dF:.0f} N = {FA1_THRUST_N:.0f} N total (1.8 kN x 4 ms x DLF 2.0), manifold 70 bar, "
                                f"A1 relight state; gimbal / mount parts only", [{"OP": FA1_BAR["FA1Q"] / 10.0, "PM": P_MAN, "TZ": dF}], 1.0, 1.0,
                        "failure case, SF 1.0 (lead 194: thrust spike only for parts with T <= 20 ms)", GIMBAL_PARTS))
        return out
    lat = [{"GX": G_LAT_FLIGHT}, {"GX": -G_LAT_FLIGHT}, {"GY": G_LAT_FLIGHT}, {"GY": -G_LAT_FLIGHT}]
    base = {"OP": PC_MAX, "PM": P_MAN, "GZ": G_AX_FLIGHT}
    return [
        ("LC1", f"LC1 steady max thrust: Pc {PC_MAX * 10:.2f} bar (operating distribution, vacuum outside) + manifold {P_MAN * 10:.0f} bar "
                f"+ {G_AX_FLIGHT} g axial + {G_LAT_FLIGHT} g lateral (4 directions, envelope), mapped S-AX B1 thermal field",
         [dict(base, **l) for l in lat], 1.5, 2.0, "SF 1.5 yield / 2.0 ultimate at the node temperature (188 (9) nominal; 183 (1))", None),
    ]


def combine(F, key, co):
    """Thermal base (step TH, if solved) + sum c x (step - TH).  Runs without TH: base 0 (initial temperature T_REF everywhere)."""
    any_key = next(k for k in F if k.startswith(key + "_"))
    base = F[f"{key}_TH"].astype(np.float64) if f"{key}_TH" in F else np.zeros(F[any_key].shape, np.float64)
    mech = np.zeros_like(base)
    for st, c in co.items():
        if c:
            mech += c * (F[f"{key}_{st}"].astype(np.float64) - base)
    return base + mech, mech


# =============================================================================================== margins
def margin_status(r):
    role, ms, z = r["role"], r["MS"], r.get("zone") or ""
    hot = " Part above its usable temperature limit (T_limit)." if r.get("T_limit_exceeded") else ""
    if r.get("T_above_allowable_table"):
        hot += f" Node above the end of the allowable table ({r['allowable_table_max_C']:g} C): value held, TO-VERIFY."
    if "BRITTLE" not in r["criterion"].upper():
        if ms >= 0:
            return "MS >= 0 (combined thermal + mechanical vs Fty(T)/SF)." + hot
        if (r.get("MS_primary_only") or 0.0) < 0:
            return "NEGATIVE PRIMARY margin on a load-bearing part: DESIGN CHANGE (or idealisation artefact to be shown by refinement)." + hot
        if (r.get("MS_PQ_nodal_shakedown") or 0.0) < 0:
            return ("P+Q above 2 Fty(T) (no elastic shakedown) on a load-bearing part: DESIGN CHANGE, or an elastic-plastic / low-cycle "
                    "fatigue analysis." + hot)
        return ("NEGATIVE on the combined (thermal + mechanical) / SF screening; primary >= 0 and P+Q <= 2 Fty(T): the excess is "
                "thermal (secondary) stress. NOT a pass: acceptance needs the lead's decision on the criterion for secondary stress." + hot)
    if ms >= 0:
        return ("MS >= 0 (" + ("char zone: primary bearing vs ASSUMED char strength" if z == "char" else "brittle, total stress") + ")." + hot)
    if role.startswith("SEAL"):
        return "NEGATIVE: seal stress above the ASSUMED maximum gasket stress: supplier data or DESIGN CHANGE." + hot
    if role.startswith("ABLATIVE"):
        if z == "char":
            return ("NEGATIVE in the char zone of a non-structural ablative layer (primary compression vs ASSUMED char strength): own "
                    "criterion = char depth + containment; char strength test required. Not a pass." + hot)
        return ("NEGATIVE in the virgin zone of the ablative sleeve (thermal stress vs ASSUMED strength): cracking risk of a non-load-bearing "
                "layer; own criterion = containment + char depth; not a pass." + hot)
    if z == "char":
        return ("NEGATIVE: primary bearing stress in the CHARRED zone of a load-bearing layer vs the ASSUMED char strength: DESIGN CHANGE "
                "or a char compressive-strength test at temperature." + hot)
    return "NEGATIVE on a load-bearing brittle part: DESIGN CHANGE or test-based acceptance (cracked-but-contained). Not a pass." + hot


def part_margins(M, names, body, T, X, reg, F, cid, subcases, sfy, sfu, state):
    """Node-wise envelope over the sub-cases; per part the minimum MS in the regular and in the full node set."""
    nn = M.n_mesh + 1
    best = {}
    ev = []
    for si, co in enumerate(subcases):
        S, Sm = combine(F, "S", co)
        ev.append((co, S, Sm))
    rows = []
    for bi, nm in enumerate(names):
        b = M.bodies[nm]
        nodes = b.noff + np.arange(len(b.X0))
        mat = b.mat
        brittle = mat in BRITTLE
        Mt = engmat.MATERIALS[mat]
        Tn = T[nodes]
        Tc = Tn - 273.15
        a1, a2 = allowables(mat, Tn)
        T_char = Mt["T_char_C"]["v"] if "T_char_C" in Mt else None
        T_lim = Mt["T_max_C"]["v"] if "T_max_C" in Mt else None
        char = (Tc > T_char) if T_char is not None else np.zeros(len(nodes), bool)
        akey = "Fty" if not brittle else ("St" if "St" in Mt else "Sc")
        T_tab = (max(Mt[akey]["T_C"]) if len(Mt.get(akey, {}).get("T_C", [])) > 1 else None)
        env = {k: np.full(len(nodes), np.inf) for k in ("ms", "msu", "msp", "mspq")}
        arg = np.zeros(len(nodes), np.int16)
        keep = {}
        for si, (co, S, Sm) in enumerate(ev):
            Sb, Smb = S[nodes], Sm[nodes]
            v, vmech = vm(Sb), vm(Smb)
            if brittle:
                s1, s3 = principal(Sb)
                s1m, s3m = principal(Smb)
                sfu_b = sfu if sfu else 1.5
                big = np.full(len(nodes), np.inf)
                ms_t = np.where(s1 > 0, a1 / (sfu_b * np.maximum(s1, 1e-9)) - 1.0, np.inf) if a1 is not None else big
                ms_c = np.where(s3 < 0, a2 / (sfu_b * np.maximum(-s3, 1e-9)) - 1.0, np.inf) if a2 is not None else big
                ms = np.minimum(ms_t, ms_c)
                if char.any():
                    ms_ch = np.where(s3m < 0, a2 / (sfu_b * np.maximum(-s3m, 1e-9)) - 1.0, np.inf) if a2 is not None else big
                    ms = np.where(char, ms_ch, ms)
                msu = msp = mspq = big
                kind = (f"brittle: s1 vs St, s3 vs Sc (strength at temperature), SF {sfu_b:.1f}"
                        + (f"; char zone (T > {T_char:g} C): primary s3 vs Sc(T) (ASSUMED char strength)" if T_char is not None else ""))
                keep[si] = (v, vmech, s1, s3, s3m)
            else:
                ms = a1 / (sfy * np.maximum(v, 1e-9)) - 1.0
                msu = (a2 / (sfu * np.maximum(v, 1e-9)) - 1.0) if sfu else np.full(len(nodes), np.inf)
                msp = a1 / (sfy * np.maximum(vmech, 1e-9)) - 1.0
                mspq = 2.0 * a1 / np.maximum(v, 1e-9) - 1.0
                kind = f"von Mises (thermal + mechanical, elastic) vs Fty(T)/{sfy}" + (f", Ftu(T)/{sfu}" if sfu else "")
                keep[si] = (v, vmech, None, None, None)
            upd = ms < env["ms"]
            arg[upd] = si
            env["ms"] = np.minimum(env["ms"], ms)
            env["msu"] = np.minimum(env["msu"], msu)
            env["msp"] = np.minimum(env["msp"], msp)
            env["mspq"] = np.minimum(env["mspq"], mspq)
        for tag, msk in (("regular", reg[nodes]), ("all", np.ones(len(nodes), bool))):
            if not msk.any():
                continue
            i = int(np.argmin(np.where(msk, env["ms"], np.inf)))
            n = nodes[i]
            si = int(arg[i])
            co, S, Sm = ev[si]
            v, vmech, s1, s3, s3m = keep[si]
            if s1 is None:
                s1_, s3_ = principal(S[n][None])
                s1n, s3n = float(s1_[0]), float(s3_[0])
                s3mn = float(principal(Sm[n][None])[1][0])
            else:
                s1n, s3n, s3mn = float(s1[i]), float(s3[i]), float(s3m[i])
            vmax = max(float(np.max(np.where(msk, keep[k][0], -np.inf))) for k in keep)
            x = X[n]
            row = {"case": cid, "state": state, "part": nm, "material": mat, "set": tag, "MS": float(env["ms"][i]),
                   "role": ROLE[nm][0], "role_criterion": ROLE[nm][1],
                   "MS_ult": (float(np.min(np.where(msk, env["msu"], np.inf))) if not brittle and sfu else None),
                   "MS_primary_only": (float(np.min(np.where(msk, env["msp"], np.inf))) if not brittle else None),
                   "MS_PQ_nodal_shakedown": (float(np.min(np.where(msk, env["mspq"], np.inf))) if not brittle else None),
                   "vm_MPa": float(v[i]), "vm_mech_MPa": float(vmech[i]), "vm_thermal_MPa": float(vm(F["S_TH"][n].astype(float))),
                   "vm_max_set_MPa": vmax, "s1_MPa": s1n, "s3_MPa": s3n, "s3_mech_MPa": s3mn, "T_C": float(T[n] - 273.15),
                   "zone": ("char" if char[i] else ("virgin" if T_char is not None else "")),
                   "T_char_C": T_char, "T_limit_C": T_lim, "T_part_max_C": float(Tc.max()),
                   "T_limit_exceeded": (bool(Tc.max() > T_lim) if T_lim is not None else None),
                   "allowable_table_max_C": T_tab, "T_above_allowable_table": (bool(Tc[i] > T_tab) if T_tab is not None else None),
                   "Fty_or_St_MPa": (float(a1[i]) if a1 is not None else None), "Ftu_or_Sc_MPa": (float(a2[i]) if a2 is not None else None),
                   "node": int(n), "xyz_mm": [round(float(c), 3) for c in x],
                   "r_theta_z": [round(math.hypot(x[0], x[1]), 3), round(math.degrees(math.atan2(x[1], x[0])), 1), round(float(x[2]), 3)],
                   "subcase": {k: round(v_, 4) for k, v_ in co.items()}, "criterion": kind, "SF_y": sfy, "SF_u": sfu,
                   "n_nodes_set": int(msk.sum())}
            row["status"] = margin_status(row)
            rows.append(row)
    return rows, ev


# =============================================================================================== point location / SCL
class Locator:
    def __init__(self, M, nm):
        b = M.bodies[nm]
        self.b, self.X = b, M.Xp[nm]
        self.C = self.X[b.T10[:, :4]]
        self.tree = cKDTree(self.C.mean(1))
        self.Tinv = None
        self.clamp = 0.05            # accept points up to 5 % of the element size outside the faceted boundary (clamped)
        self.clamped = 0

    def locate(self, P, k=24):
        P = np.atleast_2d(P)
        _, cand = self.tree.query(P, k=k)
        best = [(-np.inf, -1, None)] * len(P)
        out_t = -np.ones(len(P), np.int64)
        out_L = np.zeros((len(P), 4))
        for q in range(len(P)):
            for t in cand[q]:
                a, b_, c, d = self.C[t]
                Mx = np.column_stack([b_ - a, c - a, d - a])
                try:
                    l = np.linalg.solve(Mx, P[q] - a)
                except np.linalg.LinAlgError:
                    continue
                L = np.array([1.0 - l.sum(), l[0], l[1], l[2]])
                if L.min() >= -1e-6:
                    out_t[q], out_L[q] = t, L
                    break
                if L.min() > best[q][0]:
                    best[q] = (L.min(), t, L)
            if out_t[q] < 0 and best[q][0] > -self.clamp:
                # point just outside the faceted (straight-sided) boundary, e.g. an SCL end point on a convex surface (chord
                # sagitta): clamp to the nearest candidate element (barycentric >= 0, renormalised)
                Lc = np.clip(best[q][2], 0.0, None)
                out_t[q], out_L[q] = best[q][1], Lc / Lc.sum()
                self.clamped += 1
        return out_t, out_L

    def interp(self, t, L, Vnodes):
        """Vnodes: nodal values indexed by LOCAL node id (n, c)."""
        T10 = self.b.T10[t]
        N = np.empty((len(t), 10))
        for i in range(4):
            N[:, i] = L[:, i] * (2 * L[:, i] - 1)
        for m, (i, j) in enumerate(fe3d.EDGES):
            N[:, 4 + m] = 4 * L[:, i] * L[:, j]
        return np.einsum("qk,qkc->qc", N, Vnodes[T10])


# S-AX stress classification lines (copied definitions, v3.4.1 rev B stations = v3.5 engine frame z)
def scl_defs(i):
    return [
        ("case_mid", "TC-01", (28.575, -60.0), (31.75, -60.0)),
        ("case_collar_groove", "TC-01", (28.575, 0.0), (i["collar_groove"][0], 0.0)),
        ("case_prechamber_hot", "TC-01", (28.575, i["inj_face"] - 17.1), (31.75, i["inj_face"] - 17.1)),
        ("case_fwd_gland", "TC-01", (28.575, i["fwd_glands"][0] + 0.5 * i["fwd_glands"][2]), (31.75, i["fwd_glands"][0] + 0.5 * i["fwd_glands"][2])),
        ("case_screw_row", "TC-01", (28.575, i["bolt_z_fwd"]), (31.75, i["bolt_z_fwd"])),
        ("case_thread", "TC-01", (28.575, 0.5 * (i["aft_land_top"] + i["aft_thread_top"])), (31.5, 0.5 * (i["aft_land_top"] + i["aft_thread_top"]))),
        ("case_aft_land", "TC-01", (28.575, i["aft_gland"][0] + 0.5 * i["aft_gland"][1]), (30.5, i["aft_gland"][0] + 0.5 * i["aft_gland"][1])),
        ("tc09_socket", "TC-09", (31.5, 0.5 * (i["aft_land_top"] + i["aft_thread_top"])), (36.0, 0.5 * (i["aft_land_top"] + i["aft_thread_top"]))),
        ("tc09_gland_wall", "TC-09", (i["aft_gland"][2] / 2, i["aft_gland"][0] + 0.5 * i["aft_gland"][1]), (36.0, i["aft_gland"][0] + 0.5 * i["aft_gland"][1])),
        ("tc09_barrel", "TC-09", (30.53, 0.5 * (i["tube_aft"] + i["aft_step"])), (33.03, 0.5 * (i["tube_aft"] + i["aft_step"]))),
        ("tc09_holder", "TC-09", (25.0, 0.5 * (i["aft_step"] + i["lip_top"])), (27.5, 0.5 * (i["aft_step"] + i["lip_top"]))),
        ("tc09_lip_root", "TC-09", (24.6, i["aft_bottom"]), (24.6, i["lip_top"])),
        ("tc09_lip_mid", "TC-09", (20.0, i["aft_bottom"]), (20.0, i["lip_top"])),
        ("head_r15", "TC-02", (15.0, i["inj_face"] + 2.0), (15.0, i["head_top"])),
        ("head_r26_gland_land", "TC-02", (26.5, i["fwd_glands"][0] + i["fwd_glands"][2]), (26.5, i["fwd_glands"][1])),
        ("head_bore_wall", "TC-02", (5.0, 0.5 * (i["z_ins_top"] + i["head_top"])), (28.575, 0.5 * (i["z_ins_top"] + i["head_top"]))),
        # v3.5.1: TC-03 bore R4.0 at this station (v3.5: R2.75); the line ends at the thread root (r 6.45)
        ("tc03_body", "TC-03", (2.75 if A3.CAD == "v35" else 4.0, 0.5 * (i["z_seat"] + i["z_ins_top"])), (6.45, 0.5 * (i["z_seat"] + i["z_ins_top"]))),
        ("bonnet_wall", "TC-04", (5.0, i["head_top"] + 12.0), (12.0, i["head_top"] + 12.0)),
    ]


def linearise(P, S, valid):
    """ASME-style linearisation along points P (q,3) with stresses S (q,6); returns Pm_vm, PmPb_vm, membrane, bending."""
    if valid.sum() < 0.9 * len(valid):
        return None
    x = np.linalg.norm(P - P[0], axis=1)
    t = x[-1]
    S = S[valid]
    x = x[valid]
    Smem = np.trapezoid(S, x, axis=0) / t if hasattr(np, "trapezoid") else np.trapz(S, x, axis=0) / t
    Sben = 6.0 / t ** 2 * (np.trapezoid(S * (t / 2 - x)[:, None], x, axis=0) if hasattr(np, "trapezoid") else np.trapz(S * (t / 2 - x)[:, None], x, axis=0))
    return {"Pm_vm": float(vm(Smem)), "PmPb_vm": float(max(vm(Smem + Sben), vm(Smem - Sben))), "membrane": Smem.tolist(),
            "bending": Sben.tolist(), "peak_vm_on_line": float(vm(S).max())}


def scl_eval(M, F, co, T, state, cid, azimuths=(0, 45, 90, 135, 180, 225, 270, 315), npts=41):
    info, _ = AB.sax_info()
    S, Sm = combine(F, "S", co)
    Re = M.Rg["engine"]
    rows = []
    locs = {}
    for nm, part, (r0, z0), (r1, z1) in scl_defs(info):
        if part not in locs:
            locs[part] = Locator(M, part)
        Lc = locs[part]
        b = M.bodies[part]
        res = []
        for az in azimuths:
            th = math.radians(az)
            e = np.array([math.cos(th), math.sin(th), 0.0])
            s = np.linspace(0, 1, npts)
            Pn = np.outer(1 - s, r0 * e + np.array([0, 0, z0])) + np.outer(s, r1 * e + np.array([0, 0, z1]))
            P = Pn @ Re.T
            t_, L_ = Lc.locate(P)
            ok = t_ >= 0
            if ok.sum() < 0.9 * npts:
                res.append({"az": az, "valid": int(ok.sum())})
                continue
            tt, LL = t_[ok], L_[ok]
            loc_ids = np.arange(len(b.X0))
            Sl = np.zeros((npts, 6))
            Sml = np.zeros((npts, 6))
            Tl = np.zeros(npts)
            Sl[ok] = Lc.interp(tt, LL, S[b.noff + loc_ids])
            Sml[ok] = Lc.interp(tt, LL, Sm[b.noff + loc_ids])
            Tl[ok] = Lc.interp(tt, LL, T[b.noff + loc_ids][:, None])[:, 0]
            lc, lp = linearise(P, Sl, ok), linearise(P, Sml, ok)
            if lc is None or lp is None:
                res.append({"az": az, "valid": int(ok.sum())})
                continue
            fy, fu = allowables(b.mat, np.array([Tl[ok].max()]))
            res.append({"az": az, "valid": int(ok.sum()), "T_max_C": float(Tl[ok].max() - 273.15), "Fty": float(fy[0]),
                        "P_Pm_vm": lp["Pm_vm"], "P_PmPb_vm": lp["PmPb_vm"], "PQ_PmPb_vm": lc["PmPb_vm"], "peak_vm": lc["peak_vm_on_line"]})
        good = [r for r in res if "P_Pm_vm" in r]
        row = {"case": cid, "state": state, "scl": nm, "part": part, "line_r_z": [[r0, z0], [r1, z1]], "azimuths": res}
        if good:
            w = max(good, key=lambda r: r["P_PmPb_vm"])
            row.update({"n_az_valid": len(good), "P_Pm_vm_min": min(r["P_Pm_vm"] for r in good), "P_Pm_vm_max": max(r["P_Pm_vm"] for r in good),
                        "P_Pm_vm_mean": float(np.mean([r["P_Pm_vm"] for r in good])),
                        "P_PmPb_vm_max": w["P_PmPb_vm"], "PQ_PmPb_vm_max": max(r["PQ_PmPb_vm"] for r in good),
                        "MS_PmPb_y_min": min(r["Fty"] / (1.5 * max(r["P_PmPb_vm"], 1e-9)) - 1.0 for r in good),
                        "MS_PQ_shakedown_min": min(2 * r["Fty"] / max(r["PQ_PmPb_vm"], 1e-9) - 1.0 for r in good)})
        rows.append(row)
    return rows


def section_force_z(M, F, co, part, z, r0, r1, nth=72, npts=21):
    """Axial force (N) through the annulus r0..r1 at station z of one part (sum of sigma_zz r dr dtheta), mechanical part only."""
    S, Sm = combine(F, "S", co)
    Lc = Locator(M, part)
    b = M.bodies[part]
    Re = M.Rg["engine"]
    ez = Re @ np.array([0, 0, 1.0])
    loc = b.noff + np.arange(len(b.X0))
    tot, totm, nval = 0.0, 0.0, 0
    rr = np.linspace(r0, r1, npts)
    for k in range(nth):
        th = 2 * math.pi * (k + 0.5) / nth
        e = np.array([math.cos(th), math.sin(th), 0.0])
        P = (np.outer(rr, e) + np.array([0, 0, z])) @ Re.T
        t_, L_ = Lc.locate(P)
        ok = t_ >= 0
        nval += int(ok.sum())
        if not ok.any():
            continue
        Sl = Lc.interp(t_[ok], L_[ok], S[loc])
        Sml = Lc.interp(t_[ok], L_[ok], Sm[loc])
        szz = np.einsum("qij,i,j->q", tensor(Sl), ez, ez)
        szzm = np.einsum("qij,i,j->q", tensor(Sml), ez, ez)
        w = np.zeros(npts)
        w[ok] = 1.0
        dr = (r1 - r0) / (npts - 1)
        wt = np.full(npts, dr)
        wt[0] = wt[-1] = dr / 2
        tot += float((szz * rr[ok] * wt[ok]).sum()) * 2 * math.pi / nth
        totm += float((szzm * rr[ok] * wt[ok]).sum()) * 2 * math.pi / nth
    return {"part": part, "z": z, "r0": r0, "r1": r1, "Fz_total_N": tot, "Fz_mech_N": totm, "valid_fraction": nval / (nth * npts)}


# =============================================================================================== reactions / connectors
def reactions(name, state, steps):
    r = fe3d.read_dat_totals(RUNS / name / state / "f1.dat")
    out = {}
    for t, st, v in r:
        k = steps[int(round(t)) - 1]
        out.setdefault(k, {})[st] = v
    return out


def combine_rf(RF, co):
    any_st = next(iter(RF))
    base = RF["TH"] if "TH" in RF else {s: np.zeros(3) for s in RF[any_st]}
    res = {}
    for s in base:
        v = base[s].copy()
        for st, c in co.items():
            if c:
                v = v + c * (RF[st][s] - base[s])
        res[s] = v
    return res


def hole_frames(M):
    """Airframe hole centres and local frames (posed = fixed group, identity)."""
    out = {}
    for ring, z, s0, s1 in (("GM-09", 27.0, 58.6, 69.9), ("GM-10", -94.8, 40.0, 75.0)):
        for k in range(8):
            phi = math.radians(22.5 + 45 * k)
            er = np.array([math.cos(phi), math.sin(phi), 0.0])
            et = np.array([-math.sin(phi), math.cos(phi), 0.0])
            out[f"AF_{ring.replace('-', '')}_{k}"] = (er * 0.5 * (s0 + s1) + np.array([0, 0, z]), er, et)
    return out


def icd_table(M, rf_sets):
    """Per hole: reaction exerted BY the airframe ON the engine module (ccx RF) and its opposite (load on the airframe), local frame."""
    hf = hole_frames(M)
    rows = []
    Ft, Mt = np.zeros(3), np.zeros(3)
    for lab, v in rf_sets.items():
        x, er, et = hf[lab]
        L = -np.asarray(v)          # force applied by the engine module on the airframe at this hole
        rows.append({"hole": lab, "x_mm": [round(float(c), 2) for c in x], "F_on_airframe_N": [round(float(c), 3) for c in L],
                     "radial_N": round(float(L @ er), 3), "tangential_N": round(float(L @ et), 3), "axial_N": round(float(L[2]), 3),
                     "shear_in_screw_N": round(float(math.hypot(L @ et, L[2])), 3)})
        Ft += L
        Mt += np.cross(x, L)
    return rows, {"F_total_on_airframe_N": Ft.tolist(), "M_total_about_pivot_Nmm": Mt.tolist()}


def connector_forces(M, U):
    """Spring forces (N) from displacements: f = k (u2 - u1) . e12 (linear SPRINGA), e12 in the posed geometry."""
    lab2 = {}
    for lab, e, n1, n2, k in M.springA:
        x1, x2 = M.xyzp([n1])[0], M.xyzp([n2])[0]
        d = x2 - x1
        L = np.linalg.norm(d)
        e12 = d / L
        f = float(k * (U[n2] - U[n1]) @ e12)
        lab2[lab] = {"k_N_per_mm": k, "dir": [round(float(c), 4) for c in e12], "force_N": f, "elong_mm": f / k}
    groups = {}
    for lab, v in lab2.items():
        base = lab.rsplit("_", 1)[0] if (lab.rsplit("_", 1)[-1][:1] in "kg" and lab.rsplit("_", 1)[-1][1:].isdigit()) else lab
        groups.setdefault(base, {})[lab] = v
    return groups


def summary_connectors(groups):
    out = {}
    for base, d in groups.items():
        vals = list(d.values())
        if base.startswith("JF"):
            # dirs: k0 radial (screw axis), k1 tangential, k2 axial (both shear)
            fr = d.get(f"{base}_k0", {}).get("force_N", 0.0)
            ft = d.get(f"{base}_k1", {}).get("force_N", 0.0)
            fz = d.get(f"{base}_k2", {}).get("force_N", 0.0)
            out[base] = {"screw_axial_N": fr, "shear_tangential_N": ft, "shear_axial_N": fz, "shear_resultant_N": math.hypot(ft, fz)}
        elif base.startswith("BRG"):
            out[base] = {k.rsplit("_", 1)[1]: v["force_N"] for k, v in d.items()}
            r = [v["force_N"] for k, v in d.items() if k.endswith(("k0", "k1"))]
            out[base]["radial_resultant_N"] = math.hypot(*r) if len(r) == 2 else None
        elif base.startswith("ROD"):
            out[base] = {"axial_N (tension +)": vals[0]["force_N"]}
        else:
            out[base] = {k.rsplit("_", 1)[1]: v["force_N"] for k, v in d.items()}
    return out


def merge_extra(F, RF, xname, state):
    """Add the unit steps of a companion run (same model, same thermal state, e.g. tz_v351 with steps TH,TZ) to F / RF as if solved
    here: field = TH(this run) + (step - TH)(companion).  Returns the list of merged step names."""
    xd = RUNS / xname / state
    if not (xd / "fields.npz").exists():
        return []
    xm = json.loads((RUNS / xname / "model.json").read_text())
    xs = xm.get("steps") or []
    Z = np.load(xd / "fields.npz")
    xrf = reactions(xname, state, xs)
    got = []
    for st in xs:
        if st == "TH" or f"U_{st}" not in Z.files:
            continue
        for key in ("U", "S"):
            if f"{key}_{st}" in Z.files:
                base_x = Z[f"{key}_TH"].astype(np.float64) if f"{key}_TH" in Z.files else 0.0
                base = F[f"{key}_TH"].astype(np.float64) if f"{key}_TH" in F else 0.0
                F[f"{key}_{st}"] = (base + Z[f"{key}_{st}"].astype(np.float64) - base_x).astype(F[f"{key}_OP"].dtype)
        th_x = xrf.get("TH", {k: np.zeros(3) for k in xrf[st]})
        th = RF.get("TH", {k: np.zeros(3) for k in xrf[st]})
        RF[st] = {k: th[k] + xrf[st][k] - th_x[k] for k in xrf[st]}
        got.append(st)
    return got


# =============================================================================================== main
def run(name, states, cases=None, ex_r=1.0, extra=None):
    t0 = time.time()
    M, meta = load_model(name)
    steps = meta.get("steps") or STEPS_DEFAULT
    out = {"run": name, "version": A3.VERSION, "variant": meta["variant"], "ex_r_mm": ex_r, "states": {}, "date": "2026-10-13"}
    RES.mkdir(exist_ok=True)
    for state in states:
        F = load_fields(name, state)
        names, body, T, X = node_arrays(M, name, state)
        reg, srep, sing = singular_sets(M, X, ex_r=ex_r)
        RF = reactions(name, state, steps)
        merged = merge_extra(F, RF, extra, state) if extra else []
        st_out = {"singular": srep, "equilibrium": {}, "cases": {}, "merged_from": {extra: merged} if merged else {}}
        # equilibrium (unit steps)
        for st in list(steps) + merged:
            tot = sum(RF[st].values())
            th = sum(RF["TH"].values()) if "TH" in RF else np.zeros(3)
            st_out["equilibrium"][st] = {"sum_RF_N": [float(c) for c in tot], "unit_minus_TH_N": [float(c) for c in tot - th]}
        all_rows = []
        for cid, title, subs, sfy, sfu, crit, parts in combos(state, [k[2:] for k in F if k.startswith("U_")]):
            if cases and cid not in cases:
                continue
            rows, ev = part_margins(M, names, body, T, X, reg, F, cid, subs, sfy, sfu, state)
            if parts:
                rows = [r for r in rows if r["part"] in parts]
            all_rows += rows
            # reactions / ICD for the sub-cases
            icd = []
            for co in subs:
                rfc = combine_rf(RF, co)
                tab, tot = icd_table(M, rfc)
                icd.append({"subcase": co, "holes": tab, **tot})
            # connector forces (sub-case envelope by label: max |F|)
            con = []
            for co in subs:
                U, _ = combine(F, "U", co)
                con.append({"subcase": co, "forces": summary_connectors(connector_forces(M, U))})
            # displacements
            U0, Um = combine(F, "U", subs[0])
            disp = {nm: float(np.linalg.norm(U0[M.bodies[nm].noff:M.bodies[nm].noff + len(M.bodies[nm].X0)], axis=1).max()) for nm in names}
            scl = scl_eval(M, F, subs[0], T, state, cid)
            secF = section_force_z(M, F, subs[0], "TC-01", -60.0, 28.575, 31.75)
            st_out["cases"][cid] = {"title": title, "criterion": crit, "subcases": subs, "margins": rows, "icd": icd, "connectors": con,
                                    "max_abs_U_mm_subcase0": disp, "scl": scl, "section_force_case_mid": secF}
        out["states"][state] = st_out
        print(f"[post {name}/{state}] {time.time() - t0:.1f} s", flush=True)
    tag = f"{name}"
    (RES / f"f1_post_{tag}.json").write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    opts = dict(x.split("=", 1) for x in a[2:])
    run(a[0], a[1].split(","), cases=(opts["cases"].split(",") if "cases" in opts else None), ex_r=float(opts.get("ex_r", 1.0)),
        extra=opts.get("extra"))
