"""FEA3D J-FWD one-sector contact sub-model: deck writer, runner and post (v3.5.2 item 2; lead 231 (3), 234 (1)(b)/(c)/(e); relays
2026-10-20 ~03:10Z (HW-101 3.0 N m: preload 3000 N nominal / 3750 N +25 %; soak step at 64.7 s GVLO row means) and ~04:05Z (gap-variant
fields published; keep the row means until the S-AX dirs land).  Geometry and mesh: jfwd_sub.py (docstring there).

Model (all SIM unless tagged):
  bodies   TC-01 case sector (AL6061-T6), TC-02 head sector (AL6061-T6), HW-101 solid screw (A4-80: E 193 GPa x SS316L E(T)/E(20),
           SS316L alpha(T) secant from 20 C, nu 0.29; engmat, LITERATURE / ASSUMED proxy).  C3D10 straight-sided.
  thread   bonded: the screw nodes on the tap cylinder (x' 21.75..28.6, D 5.0) are duplicated and tied 1:1 to the TC-02 nodes by
           *EQUATION (each body keeps its own temperature at the interface).
  preload  pretension section at x' 30.2 (in the TC-01 hole): the head-side screw nodes are duplicated; u_A - u_B + n d1 + t1 d2 + t2 d3 = 0
           with the reference node R (d1 = shortening along the screw axis n; d2, d3 fixed: their reactions = section shear).
           SEAT: d1 prescribed 0.05 mm (closes the 0.01 mm head gap and the 0.025 mm fit gap); PRELOAD: *CLOAD T on d1 (one increment);
           afterwards d1 FIXED (the installation stretch is locked; the bolt force then follows the thermal and pressure loads).
  contact  surface-to-surface penalty, linear pressure-overclosure K 5e5 MPa/mm (Mechanical's TC-02/TC-03 sub-model value, ASSUMED
           numerical), frictionless or Coulomb mu 0.2 with stick slope 1e4 MPa/mm: HEAD (TC-01 OD patch r' <= 5.3 / screw head flat face),
           BEAR (TC-01 hole r' 2.75 / screw shank), FIT (TC-02 OD r 28.600 / TC-01 bore r 28.625; 0.025 mm radial gap).
  BCs      az 0 plane u_y = 0; az 36 plane u_theta = 0 (*EQUATION); TC-01 aft cut (z 97.5 - shift) u_z = 0; TC-02 only on 10 SPRING1
           z-springs 1.0 N/mm (10 N/mm total, since 05:15Z; t1 had 0.1) against the frictionless rigid-body mode before the shank bears.
  loads    Pc (absolute; flight, vacuum ambient) on the wetted faces of TC-02 (chamber face, step r 24.95, lip, spigot OD below gland 1,
           gland 1 incl. its ceiling, TC-03 pocket wall r 10.1, torch passage drill / outlet / counterbore) and of TC-01 (bore up to the
           gland-1 ceiling z 111.363); + cap force Pc pi 4.5^2 / 2 as +z traction on the torch-counterbore wall; + TC-03 disc load
           Pc pi 10.1^2 / 10 as +z traction on the M14 bore (TB1: TC-03 not modelled).  No manifold pressure (internal to the TC-02 /
           TC-03 / TC-04 manifold, no net J-FWD load; > 18 mm from the screw).  Temperatures uniform per part and step.
usage: jfwd_deck.py build <mesh_tag>            -> jfwd/model_<tag>.npz/.json (face classes, sets, checks)
       jfwd_deck.py deck <mesh_tag> <job> mu=<0|0.2> T=<preload N> steps=<A,B,...>
       jfwd_deck.py run <job> [expect=GB]
       jfwd_deck.py post <job>
"""
from __future__ import annotations
import sys, json, math, time, gzip, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS          # noqa: E402
import mesh3d                  # noqa: E402
import asm3d as A3             # noqa: E402

OUT = JS.OUT
RUNS = OUT / "runs"
MAT = A3.engmat.MATERIALS
C0 = np.array([0.0, 0.0, JS.Z_SCREW])
EN = JS.er(JS.AZ_SCREW)                                   # screw axis n (radially outward)
ET1 = np.array([-math.sin(math.radians(JS.AZ_SCREW)), math.cos(math.radians(JS.AZ_SCREW)), 0.0])
ET2 = np.array([0.0, 0.0, 1.0])
S36, C36 = math.sin(math.radians(JS.SECTOR)), math.cos(math.radians(JS.SECTOR))
K_PEN, STICK = 5.0e5, 1.0e4
K_SPR = 1.0              # N/mm per TC-02 axial ground spring (10 springs)
FIT_CLEARANCE = 0.025    # mm, FIT pair (CAD 57.25 / 57.20)
D_SEAT = 0.05
Z_SEAL1 = 111.363                    # gland-1 ceiling (TC-02 local -58.15 + 169.513)
FACES = mesh3d.TET_FACES
FMID = mesh3d.FACE_MID
TK = 273.15

# load steps: name -> (Pc MPa abs, {part: T_C}, label).  Row means (Mechanical jfwd_variant_v352_v1.json 9a7165eeda7cfc71, SIM row
# temperatures of the GVLO field): 64.7 s TC-01 158.0 / TC-02 96.0 / screw 127.0 (mean of the two, ASSUMED by Mechanical); 21.65 s
# 60.0 / 81.2 / 70.6.  78.6 C = Mechanical's LC2 uniform joint temperature (jfwd_preload_v352_v1.json 5dbcb3597d009b0e); 45.6 C FA1.
U = lambda t: {"TC-01": t, "TC-02": t, "SCREW": t}
STEPS = {
    "SOAK": (0.0, {"TC-01": 158.0, "TC-02": 96.0, "SCREW": 127.0}, "soak 64.7 s GVLO row means, unpressurised"),
    "LC2N": (4.5, U(78.6), "LC2 MEOP 4.5 MPa abs x1.0, 78.6 C uniform"),
    "LC2Y": (6.75, U(78.6), "LC2 x1.5 (yield factor) 6.75 MPa, 78.6 C"),
    "LC2U": (9.0, U(78.6), "LC2 x2.0 (ultimate factor) 9.0 MPa, 78.6 C"),
    "LC2G": (4.5, {"TC-01": 60.0, "TC-02": 81.2, "SCREW": 70.6}, "LC2 x1.0 at the GVLO 21.65 s row means"),
    "LC2GY": (6.75, {"TC-01": 60.0, "TC-02": 81.2, "SCREW": 70.6}, "LC2 x1.5 at GVLO 21.65 s"),
    "LC2GU": (9.0, {"TC-01": 60.0, "TC-02": 81.2, "SCREW": 70.6}, "LC2 x2.0 at GVLO 21.65 s"),
    "FA1Q": (9.4, U(45.6), "FA1Q 94 bar abs, 45.6 C"),
    "FA1D": (12.1, U(45.6), "FA1D 121 bar abs, 45.6 C"),
    "FA1U": (14.7, U(45.6), "FA1U 147 bar abs, 45.6 C"),
    "FA1S": (15.104, U(45.6), "FA1S 151.04 bar abs, 45.6 C"),
    "COLD": (0.0, U(20.0), "unloaded, 20 C (preload check)"),
    # mapped S-AX fields (lead ~04:13Z): GVLO soak B1_70.7 (nearest stored state to 64.7 s) and B1_51.7; LC2 at the GVLO end of burn
    "SOAK70": (0.0, ("map", "GVLO", "B1_70.7"), "soak GVLO B1_70.7 mapped (S-AX field), unpressurised"),
    "SOAK52": (0.0, ("map", "GVLO", "B1_51.7"), "soak GVLO B1_51.7 mapped (S-AX field), unpressurised"),
    "LC2M": (4.5, ("map", "GVLO", "B1_21.65"), "LC2 x1.0 at the GVLO B1_21.65 mapped field"),
    "LC2MY": (6.75, ("map", "GVLO", "B1_21.65"), "LC2 x1.5 at the GVLO B1_21.65 mapped field"),
    "LC2MU": (9.0, ("map", "GVLO", "B1_21.65"), "LC2 x2.0 at the GVLO B1_21.65 mapped field"),
    "LC2H": (4.5, ("map", "GVHI", "B1_21.65"), "LC2 x1.0 at the GVHI B1_21.65 mapped field"),
}
SAX_DIRS = {"NF2b": "L1_thv352_NF2b_cad352", "GVLO": "L1_thv352_NF2b_GVLO_r10free_cad352", "GVHI": "L1_thv352_NF2b_GVHI_r10free_cad352"}


def mapped_temps(m, shift, tag, state):
    """nodal temperatures (K) from a published S-AX field: TC-01 nodes at their material position (z + shift), TC-02 at (r, z); screw
    nodes take the field of the member they sit in (x' < 28.6: TC-02 at (r, z); else TC-01 at (min(r, 31.75), z + shift))."""
    import asm_build as AB
    A3.SAX_RUN = A3._MR / SAX_DIRS[tag]
    ST = AB.SaxThermal()
    Tf = ST.field(state)
    X = m["X"]
    T = np.full(len(X), np.nan)
    st = {"sax_run": str(A3.SAX_RUN), "state": state,
          "mesh_npz_sha16": hashlib.sha256((A3.SAX_RUN / "mesh.npz").read_bytes()).hexdigest()[:16],
          "res_npz_sha16": hashlib.sha256((A3.SAX_RUN / state / "res.npz").read_bytes()).hexdigest()[:16]}
    for part, ns, dz in (("TC-01", m["n01"], shift), ("TC-02", m["n02"], 0.0)):
        r = np.hypot(X[ns, 0], X[ns, 1])
        v, nmiss, dmax = ST.at(part, Tf, r, X[ns, 2] + dz)
        T[ns] = v
        st[part] = {"n_outside": nmiss, "max_nearest_mm": round(dmax, 4), "T_min_C": round(float(v.min()) - TK, 2), "T_max_C": round(float(v.max()) - TK, 2)}
    ns = m["nsc"]
    xa = loc(X[ns])[0]
    r = np.hypot(X[ns, 0], X[ns, 1])
    i2 = xa < JS.R_OD02
    v2, n2, d2 = ST.at("TC-02", Tf, r[i2], X[ns[i2], 2])
    v1, n1, d1 = ST.at("TC-01", Tf, np.minimum(r[~i2], JS.R_OD - 1e-3), X[ns[~i2], 2] + shift)
    T[ns[i2]] = v2
    T[ns[~i2]] = v1
    st["SCREW"] = {"n_outside": n1 + n2, "max_nearest_mm": round(max(d1, d2), 4), "T_mean_C": round(float(T[ns].mean()) - TK, 2),
                   "T_min_C": round(float(T[ns].min()) - TK, 2), "T_max_C": round(float(T[ns].max()) - TK, 2)}
    # J-FWD row means (z within +/-2.75 of the hole axis): TC-01 wall, TC-02 tap zone (r 21.75..28.6)
    X1 = X[m["n01"]]
    z1 = X1[:, 2] + shift
    row1 = np.abs(z1 - JS.Z_SCREW) <= 2.75
    X2 = X[m["n02"]]
    r2 = np.hypot(X2[:, 0], X2[:, 1])
    row2 = (np.abs(X2[:, 2] - JS.Z_SCREW) <= 2.75) & (r2 >= 21.75)
    st["row_mean_C"] = {"TC-01": round(float(T[m["n01"]][row1].mean()) - TK, 2), "TC-02": round(float(T[m["n02"]][row2].mean()) - TK, 2)}
    assert np.isfinite(T[np.unique(m["T"])]).all()
    return T, st


def loc(X, dz=0.0):
    """screw-local coordinates; dz = -shift for points of the (shifted) TC-01 sector (hole axis at Z_SCREW - shift)."""
    rel = np.asarray(X) - (C0 + np.array([0.0, 0.0, dz]))
    xa = rel @ EN
    ya = rel @ ET1
    za = rel @ ET2
    return xa, ya, za, np.hypot(ya, za)


def tri_area_normal(P):
    """P (m,3,3) -> area (m,), unit normal (m,3) by the corner order."""
    c = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    a = np.linalg.norm(c, axis=1)
    return 0.5 * a, c / np.maximum(a, 1e-30)[:, None]


def samples(P, n=4):
    L = []
    for i in range(n):
        for j in range(n - i):
            L.append((1.0 - (i + 1 / 3) / n - (j + 1 / 3) / n, (i + 1 / 3) / n, (j + 1 / 3) / n))
            if i + j < n - 1:
                L.append((1.0 - (i + 2 / 3) / n - (j + 2 / 3) / n, (i + 2 / 3) / n, (j + 2 / 3) / n))
    L = np.asarray(L)
    return np.einsum("sk,mkd->msd", L, P)


def in_capsule(P, pt, ax, R, s0, s1, tolR=0.02):
    ax = np.asarray(ax, float) / np.linalg.norm(ax)
    v = P - np.asarray(pt, float)
    s = v @ ax
    d = np.linalg.norm(v - s[..., None] * ax, axis=-1)
    return (d <= R + tolR) & (s >= s0) & (s <= s1)


# ===================================================================================================== build
def build(tag):
    JS.use_mesh(tag)      # 2026-10-20 08:20Z: GEO (seat, x_seat, x_tip, x_tap_lo) from the mesh json (spot-face meshes: seat 'spot')
    d = np.load(OUT / f"mesh_{tag}.npz", allow_pickle=False)
    X, T, B = d["X"], d["T"].astype(np.int64), d["B"].astype(str)
    mj = json.loads((OUT / f"mesh_{tag}.json").read_text())
    shift = mj["shift"]
    N, M = len(X), len(T)
    body = {b: np.nonzero(B == b)[0] for b in ("TC-01", "TC-02", "SCREW")}
    nodes_of = {b: np.unique(T[e]) for b, e in body.items()}
    # ---- shared-node checks
    s01_02 = np.intersect1d(nodes_of["TC-01"], nodes_of["TC-02"])
    s01_s = np.intersect1d(nodes_of["TC-01"], nodes_of["SCREW"])
    thr = np.intersect1d(nodes_of["TC-02"], nodes_of["SCREW"])           # bonded thread nodes (conformal fragment)
    assert len(s01_02) == 0 and len(s01_s) == 0, (len(s01_02), len(s01_s))
    # ---- screw split at the pretension section
    es = body["SCREW"]
    cx = loc(X[T[es, :4]].mean(1))[0]
    eA = es[cx > JS.GEO["x_pre"]]
    eBs = es[cx <= JS.GEO["x_pre"]]
    xa, ya, za, ra = loc(X)
    nA = np.unique(T[eA])
    nBs = np.unique(T[eBs])
    sec = np.intersect1d(nA, nBs)
    assert np.all(np.abs(xa[sec] - JS.GEO["x_pre"]) < 1e-4), "section nodes off the x' plane"
    assert len(np.intersect1d(sec, thr)) == 0
    # ---- thread nodes must lie on the bonded cylinder r' 2.5, x' 21.75..28.6
    # (midside nodes of the straight-sided C3D10 sit on chords: r' down to 2.5 - h^2 / 20)
    assert np.all(np.abs(ra[thr] - JS.GEO["shank_r"]) < 0.03) and xa[thr].min() > JS.GEO["x_tip"] - 1e-3 and xa[thr].max() < JS.R_OD02 + 1e-3, \
        (ra[thr].min(), ra[thr].max(), xa[thr].min(), xa[thr].max())
    # ---- duplicates: section (A side) and thread (screw side)
    new_sec = N + np.arange(len(sec))
    new_thr = N + len(sec) + np.arange(len(thr))
    ref = N + len(sec) + len(thr)
    Xn = np.vstack([X, X[sec], X[thr], (C0 + JS.GEO["x_pre"] * EN)[None]])
    Tn = T.copy()
    mp_thr = -np.ones(N, np.int64)
    mp_thr[thr] = new_thr
    sub = Tn[es]
    hit = mp_thr[sub] >= 0
    sub[hit] = mp_thr[sub][hit]
    Tn[es] = sub
    mp_sec = -np.ones(N, np.int64)
    mp_sec[sec] = new_sec
    sub = Tn[eA]
    hit = mp_sec[sub] >= 0
    sub[hit] = mp_sec[sub][hit]
    Tn[eA] = sub
    nset = {b: np.unique(Tn[e]) for b, e in body.items()}
    assert len(np.intersect1d(nset["TC-02"], nset["SCREW"])) == 0
    # ---- boundary faces on the ORIGINAL connectivity (thread and section faces are interior)
    fl = []
    for k in (1, 2, 3, 4):
        cn = T[:, list(FACES[k])]
        fl.append((np.sort(cn, 1), np.full(M, k), np.arange(M)))
    keys = np.vstack([f[0] for f in fl])
    fk = np.concatenate([f[1] for f in fl])
    fe = np.concatenate([f[2] for f in fl])
    _, inv, cnt = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    bnd = cnt[inv] == 1
    fe, fk = fe[bnd], fk[bnd]
    cidx = np.array([FACES[int(k)] for k in fk])
    midx = np.array([FMID[int(k)] for k in fk])
    fcn = np.take_along_axis(Tn[fe], cidx, 1)       # corner nodes of the face (new numbering)
    fmn = np.take_along_axis(Tn[fe], midx, 1)
    P = Xn[fcn]
    area, nrm = tri_area_normal(P)
    # outward: away from the opposite corner
    opp = np.array([[i for i in range(4) if i not in FACES[int(k)]][0] for k in fk])
    xo = Xn[Tn[fe, opp]]
    cen = P.mean(1)
    flip = np.einsum("ij,ij->i", nrm, xo - cen) > 0
    nrm[flip] *= -1
    fb = B[fe]
    r = np.hypot(cen[:, 0], cen[:, 1])
    z = cen[:, 2]
    er_ = np.stack([cen[:, 0] / r, cen[:, 1] / r, np.zeros_like(r)], 1)
    nr = np.einsum("ij,ij->i", nrm, er_)
    nz = nrm[:, 2]
    az = np.degrees(np.arctan2(cen[:, 1], cen[:, 0]))
    fxa, fya, fza, fra = loc(cen)
    tol = 0.01
    # corner-based tests (vertices lie on the CAD surfaces; face centroids of curved faces sit inside by up to 2/3 of the sagitta)
    rC = np.hypot(P[..., 0], P[..., 1])
    zC = P[..., 2]
    xaC, _, _, raC = loc(P.reshape(-1, 3))
    xaC, raC = xaC.reshape(-1, 3), raC.reshape(-1, 3)
    _, _, _, raC1 = loc(P.reshape(-1, 3), -shift)          # TC-01: relative to its own (shifted) hole axis
    raC1 = raC1.reshape(-1, 3)
    fra1 = loc(cen, -shift)[3]
    onR = lambda R, t=1e-3: (np.abs(rC - R) < t).all(1)
    onZ = lambda Z, t=1e-4: (np.abs(zC - Z) < t).all(1)
    onRa = lambda R, t=1e-3: (np.abs(raC - R) < t).all(1)
    cls = np.full(len(fe), "", dtype=object)
    on0 = (np.abs(Xn[fcn][..., 1]) < 1e-5).all(1)
    n36 = np.array([-S36, C36, 0.0])
    on36 = (np.abs(Xn[fcn] @ n36) < 1e-5).all(1)
    cls[on0] = "SYM0"
    cls[on36] = "SYM36"
    zc = JS.Z_OFF and None
    zcut = mj["zcut"] - shift
    is01, is02, iss = fb == "TC-01", fb == "TC-02", fb == "SCREW"
    cut = is01 & (np.abs(z - zcut) < 1e-4) & (nz < -0.99)
    cls[cut & (cls == "")] = "CUT"
    free = cls == ""
    # ---- wetted faces (fraction of 16 sub-samples)
    S = samples(P)
    rS = np.hypot(S[..., 0], S[..., 1])
    zS = S[..., 2]
    wet = np.zeros(len(fe))
    lab = {}

    wlab = np.full(len(fe), -1, np.int64)

    def put(name, msk_face, frac=None):
        f = msk_face & free & (wet == 0)
        v = np.ones(len(fe)) if frac is None else frac
        wet[f] = v[f]
        wlab[f & (v > 0)] = len(lab)
        lab[name] = {"faces": int((f & (v > 0)).sum()), "area_mm2": round(float((area * v)[f].sum()), 3),
                     "Fz_per_MPa_N": round(float(-(v * area * nrm[:, 2])[f].sum()), 3)}
        return f
    ZH = 169.513426018
    put("TC02_chamber_face", is02 & onZ(ZH - 64.0) & (nz < -0.99))
    put("TC02_step_r24.95", is02 & onR(24.95) & (nr < -0.9) & (zC < ZH - 64.0 + tol).all(1))
    put("TC02_lip_z103.513", is02 & onZ(ZH - 66.0) & (nz < -0.99))
    put("TC02_spigotOD_below_g1", is02 & onR(28.6) & (nr > 0.9) & (zC < ZH - 63.0 + tol).all(1))
    put("TC02_g1_lower_flank", is02 & onZ(ZH - 63.0) & (nz > 0.99))
    put("TC02_g1_bottom", is02 & onR(25.825) & (nr > 0.9) & (zC > ZH - 63.0 - tol).all(1) & (zC < ZH - 58.15 + tol).all(1))
    put("TC02_g1_ceiling", is02 & onZ(ZH - 58.15) & (nz < -0.99))
    put("TC02_pocket_wall_r10.1", is02 & onR(10.1) & (nr < -0.9) & (zC < ZH - 62.0 + tol).all(1))
    for nm, (pt, ax, R, s0, s1) in {"torch_drill": ((23.17, 0.0, 134.61), (-0.072, 0.0, -0.997), 2.6, -25.2, 25.25),
                                    "torch_outlet": ((19.18, 0.0, 107.49), (-0.5, 0.0, -0.866), 1.5, -3.2, 3.2),
                                    "torch_counterbore": ((25.0, 0.0, 0.0), (0.0, 0.0, 1.0), 4.5, 159.49, 169.52)}.items():
        put("TC02_" + nm, is02 & in_capsule(S, pt, ax, R, s0, s1).all(1))
    frac01 = (zS <= Z_SEAL1).mean(1)
    put("TC01_bore_to_g1_ceiling", is01 & (rC < 28.63).all(1) & ((nr < -0.5) | (np.abs(nz) > 0.99)), frac01)
    # ---- traction faces
    cbw = is02 & in_capsule(S, (25.0, 0.0, 0.0), (0, 0, 1), 4.5, 159.6, 169.52).all(1) & (np.abs(nz) < 0.5) & free
    m14 = is02 & onR(6.5) & (zC > ZH - 62.0 - tol).all(1) & (zC < ZH - 52.0 + tol).all(1) & (np.abs(nz) < 0.2) & free
    # ---- contact surfaces
    # 2026-10-20 08:20Z: head seat at x' = x_seat (CAD: the OD R31.75; spot face: the d10.5 flat at x' 31.313, normal to the hole axis)
    head_m = iss & (np.abs(xaC - (JS.GEO["x_seat"] + JS.GEO["head_gap"])) < 1e-4).all(1) & (np.einsum("ij,j->i", nrm, EN) < -0.99)
    if JS.GEO.get("seat") == "spot":
        head_s = is01 & (np.abs(xaC - JS.GEO["x_seat"]) < 1e-3).all(1) & (np.einsum("ij,j->i", nrm, EN) > 0.99) & (fra1 <= 5.3) & free
    else:
        head_s = is01 & onR(JS.R_OD) & (nr > 0.9) & (fra1 <= 5.3) & free
    bear_s = is01 & (np.abs(raC1 - JS.GEO["hole_r"]) < 1e-3).all(1) & (xaC > JS.R_BORE01 - 0.05).all(1) & (xaC < JS.R_OD + 0.05).all(1)
    brk = max(float(JS.GEO.get("brk_r", 0.0) or 0.0), float(JS.GEO.get("brk_c", 0.0) or 0.0))
    if brk > 0:
        # 2026-10-20 ~11:10Z (mesh s6, lead 10:08:44Z / ~10:15Z: R0.2 at the bore end of the hole + 0.1 deburr at the flat end): the fillet and
        # the chamfer faces join the BEAR slave (TC-01): every corner at r' in [hole_r, hole_r + brk + 0.01] about the (shifted) hole axis and
        # the outward normal pointing toward the hole axis (n . -e_rad > 0.2; excludes the bore and the spot-face flat).  FIT master stays the
        # bore r 28.625 only (the *CLEARANCE value would replace the fillet's geometric gap).
        relc = cen - (C0 + np.array([0.0, 0.0, -shift]))
        radv = relc - np.outer(relc @ EN, EN)
        erad = radv / np.linalg.norm(radv, axis=1)[:, None]
        inward = np.einsum("ij,ij->i", nrm, -erad) > 0.2
        bear_s = (is01 & (raC1 > JS.GEO["hole_r"] - 1e-3).all(1) & (raC1 < JS.GEO["hole_r"] + brk + 0.01).all(1) & inward
                  & (xaC > JS.R_BORE01 - 0.05).all(1) & (xaC < JS.R_OD + 0.05).all(1))
    bear_m = iss & onRa(JS.GEO["shank_r"]) & (xaC > 28.0).all(1) & (xaC < JS.R_OD + 0.02).all(1)
    fit_s = is02 & onR(JS.R_OD02) & (nr > 0.9) & free
    fit_m = is01 & onR(JS.R_BORE01) & (nr < -0.9) & free
    # ---- nodes on BCs
    allnodes = np.arange(len(Xn))
    used = np.unique(Tn)
    y0 = used[(np.abs(Xn[used, 1]) < 1e-5)]
    y36 = used[(np.abs(Xn[used] @ n36) < 1e-5)]
    ncut = np.intersect1d(nset["TC-01"], used[np.abs(Xn[used, 2] - zcut) < 1e-4])
    top02 = np.intersect1d(nset["TC-02"], used[np.abs(Xn[used, 2] - 169.513426) < 1e-3])
    rng = np.random.default_rng(1)
    springs = np.sort(rng.choice(top02, size=min(10, len(top02)), replace=False))
    model = dict(X=Xn, T=Tn, B=B, sec=sec, new_sec=new_sec, thr=thr, new_thr=new_thr, ref=np.array([ref]),
                 wlab=wlab, fe=fe, fk=fk, fcn=fcn, fmn=fmn, area=area, nrm=nrm, wet=wet, cbw=cbw, m14=m14, head_m=head_m, head_s=head_s,
                 bear_s=bear_s, bear_m=bear_m, fit_s=fit_s, fit_m=fit_m, y0=y0, y36=y36, ncut=ncut, springs=springs,
                 n01=nset["TC-01"], n02=nset["TC-02"], nsc=nset["SCREW"], eA=eA, cls=cls.astype(str))
    np.savez_compressed(OUT / f"model_{tag}.npz", **model)
    # ---- checks
    Fz_unit = float(-(wet * area * nrm[:, 2])[fb == "TC-02"].sum())        # +z force on TC-02 per MPa (pressure only)
    Fz_cap = math.pi * 4.5 ** 2 / 2.0
    Fz_tc03 = math.pi * 10.1 ** 2 / 10.0
    Fz01 = float(-(wet * area * nrm[:, 2])[fb == "TC-01"].sum())
    # tap-to-passage wall: min distance between the TC-02 tap-cylinder nodes and the drill surface nodes
    drill_nodes = np.unique(fcn[is02 & (lab and True) & in_capsule(S, (23.17, 0.0, 134.61), (-0.072, 0.0, -0.997), 2.6, -25.2, 25.25).all(1)])
    from scipy.spatial import cKDTree
    dmin = float(cKDTree(Xn[drill_nodes]).query(Xn[thr])[0].min()) if len(drill_nodes) else None
    info = {"mesh": tag, "n_nodes": int(len(Xn)), "n_elem": int(M), "n_section_pairs": int(len(sec)), "n_thread_pairs": int(len(thr)),
            "ref_node": int(ref) + 1, "n_sym0": int(len(y0)), "n_sym36": int(len(y36)), "n_cut": int(len(ncut)), "springs": (springs + 1).tolist(),
            "wetted": lab, "TC02_axial_force_per_MPa_N": round(Fz_unit, 3), "cap_force_per_MPa_N": round(Fz_cap, 3),
            "TC03_force_per_MPa_N": round(Fz_tc03, 3),
            "TC02_total_axial_per_MPa_N": round(Fz_unit + Fz_cap + Fz_tc03, 3),
            "ref_head_load_per_screw_per_MPa_N": round(math.pi / 4 * 57.25 ** 2 / 10.0, 3),
            "TC01_axial_force_per_MPa_N": round(Fz01, 3),
            "cap_wall_faces": int(cbw.sum()), "cap_wall_area": round(float(area[cbw].sum()), 3),
            "m14_faces": int(m14.sum()), "m14_area": round(float(area[m14].sum()), 3),
            "contact_faces": {k: int(v.sum()) for k, v in (("head_s", head_s), ("head_m", head_m), ("bear_s", bear_s), ("bear_m", bear_m),
                                                           ("fit_s", fit_s), ("fit_m", fit_m))},
            "contact_area_mm2": {k: round(float(area[v].sum()), 3) for k, v in (("head_s", head_s), ("head_m", head_m), ("bear_s", bear_s),
                                                                                  ("bear_m", bear_m), ("fit_s", fit_s), ("fit_m", fit_m))},
            "tap_to_drill_min_node_distance_mm": None if dmin is None else round(dmin, 4)}
    (OUT / f"model_{tag}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))
    return model, info


# ===================================================================================================== deck
def mat_al():
    return A3_mat_block("AL", "AL6061-T6")


def A3_mat_block(name, mat):
    import asm_build as AB
    return AB.mat_block(name, mat)


def mat_screw():
    E316 = MAT["SS316L"]["E"]
    a316 = MAT["SS316L"]["alpha"]
    E0 = 193.0e3
    s = ["*MATERIAL, NAME=A480", "*DENSITY", "8.0e-09", "*ELASTIC"]
    for Tc, v in zip(E316["T_C"], E316["v"]):
        s.append(f"{E0 * v / E316['v'][0]:.6e}, 0.29, {Tc + TK:.2f}")
    s.append(f"*EXPANSION, ZERO={A3.T_REF}")
    for Tc, v in zip(a316["T_C"], a316["v"]):
        s.append(f"{v:.6e}, {Tc + TK:.2f}")
    return "\n".join(s) + "\n"


def lines_set(name, ids, per=12):
    out = [f"*NSET, NSET={name}"]
    ids = list(ids)
    for i in range(0, len(ids), per):
        out.append(", ".join(str(int(v) + 1) for v in ids[i:i + per]))
    return "\n".join(out) + "\n"


def surface(name, fe, fk):
    s = [f"*SURFACE, NAME={name}, TYPE=ELEMENT"]
    s += [f"{int(e) + 1}, S{int(k)}" for e, k in zip(fe, fk)]
    return "\n".join(s) + "\n"


def traction_cloads(m, mask, F_vec):
    """consistent nodal forces of a uniform traction (total F_vec) on straight T6 faces: midside nodes area/3, corners 0."""
    a = m["area"][mask]
    tot = a.sum()
    f = {}
    for mids, ai in zip(m["fmn"][mask], a):
        for nd in mids:
            f[int(nd)] = f.get(int(nd), 0.0) + ai / 3.0 / tot
    return {nd: w * np.asarray(F_vec) for nd, w in f.items()}


def write_deck(tag, job, mu, T_pre, steps, fitc=FIT_CLEARANCE):
    """fitc: FIT radial clearance (mm) for every slave node (2026-10-20 08:20Z, lead 07:43Z: drawing H8/f7 max 0.078 and the CAD 0.025)."""
    mj0 = JS.use_mesh(tag)
    m = dict(np.load(OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T = m["X"], m["T"]
    ref = int(m["ref"][0])
    wd = RUNS / job
    wd.mkdir(parents=True, exist_ok=True)
    f = open(wd / f"{job}.inp", "w")
    w = f.write
    w(f"*HEADING\nFEA3D J-FWD one-sector contact sub-model mesh {tag} (seat {JS.GEO.get('seat')}) mu {mu} preload {T_pre} N fit {fitc} mm steps {','.join(steps)}\n")
    w("*NODE, NSET=NALL\n")
    used = np.zeros(len(X), bool)
    used[np.unique(T)] = True
    used[ref] = True
    for i in np.nonzero(used)[0]:
        x = X[i]
        w(f"{i + 1}, {x[0]:.7f}, {x[1]:.7f}, {x[2]:.7f}\n")
    B = m["B"]
    for b, es in (("TC01", "TC-01"), ("TC02", "TC-02"), ("SCR", "SCREW")):
        w(f"*ELEMENT, TYPE=C3D10, ELSET=E_{b}\n")
        for e in np.nonzero(B == es)[0]:
            w(f"{e + 1}, " + ", ".join(str(int(v) + 1) for v in T[e]) + "\n")
    # springs
    nel = len(T)
    w("*ELEMENT, TYPE=SPRING1, ELSET=E_SPR\n")
    for k, nd in enumerate(m["springs"]):
        w(f"{nel + 1 + k}, {int(nd) + 1}\n")
    # 2026-10-20 05:15Z: 1.0 N/mm each (10 N/mm total; was 0.1): the frictionless TC-02 + screw float axially when no pressure acts (faceted
    # contact normals give ~0.4 N residuals: 0.44 mm drift at 1 N/mm total on t1); spring force <= ~1 N in every case (soak +0.1 mm, FA1S ~0.06 mm)
    w(f"*SPRING, ELSET=E_SPR\n3\n{K_SPR}\n")
    w(lines_set("N_TC01", m["n01"]) + lines_set("N_TC02", m["n02"]) + lines_set("N_SCR", m["nsc"]))
    w(lines_set("N_REF", [ref]) + lines_set("N_SYM0", m["y0"]) + lines_set("N_CUT", m["ncut"]))
    w(mat_al() + mat_screw())
    w("*SOLID SECTION, ELSET=E_TC01, MATERIAL=AL\n*SOLID SECTION, ELSET=E_TC02, MATERIAL=AL\n*SOLID SECTION, ELSET=E_SCR, MATERIAL=A480\n")
    # equations
    w("*EQUATION\n")
    for nd in m["y36"]:
        w(f"2\n{int(nd) + 1}, 2, {C36:.9f}, {int(nd) + 1}, 1, {-S36:.9f}\n")
    for a, b in zip(m["new_thr"], m["thr"]):
        for i in (1, 2, 3):
            w(f"2\n{int(a) + 1}, {i}, 1.0, {int(b) + 1}, {i}, -1.0\n")
    R = ref + 1
    for a, b in zip(m["new_sec"], m["sec"]):
        A_, B_ = int(a) + 1, int(b) + 1
        w(f"4\n{A_}, 1, 1.0, {B_}, 1, -1.0, {R}, 1, {EN[0]:.9f}, {R}, 2, {ET1[0]:.9f}\n")
        w(f"4\n{A_}, 2, 1.0, {B_}, 2, -1.0, {R}, 1, {EN[1]:.9f}, {R}, 2, {ET1[1]:.9f}\n")
        w(f"3\n{A_}, 3, 1.0, {B_}, 3, -1.0, {R}, 3, 1.0\n")
    # contact
    for nm, s, mm in (("HEAD", "head_s", "head_m"), ("BEAR", "bear_s", "bear_m"), ("FIT", "fit_s", "fit_m")):
        w(surface(f"S_{nm}_S", m["fe"][m[s]], m["fk"][m[s]]))
        w(surface(f"S_{nm}_M", m["fe"][m[mm]], m["fk"][m[mm]]))
        w(f"*CONTACT PAIR, INTERACTION=SI, TYPE=SURFACE TO SURFACE\nS_{nm}_S, S_{nm}_M\n")
    # 2026-10-20 05:15Z: FIT clearance set to the CAD value (case bore 57.25 / plug OD 57.20: 0.025 mm radial, CAD) for every slave node:
    # the straight-sided C3D10 faces scatter the geometric FIT gap about the design 0.025 mm (midside nodes on the chords up to 0.05 mm inside
    # r 28.625; t1 undeformed: median 0.024, p1 -0.002 / p99 +0.053 mm, 13 of 1025 slave nodes in interference, min -0.009 mm).  Restated
    # 2026-10-20 06:35Z (MF-J1): the '51 kN radial' quoted for t1 was the biased CPRESS face-mean integral; exact K u 1878 N (0.626 T).
    w(f"*CLEARANCE, MASTER=S_FIT_M, SLAVE=S_FIT_S, VALUE={fitc}\n")
    w(f"*SURFACE INTERACTION, NAME=SI\n*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR\n{K_PEN:.3e}\n")
    if mu > 0:
        w(f"*FRICTION\n{mu}, {STICK:.3e}\n")
    w(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {A3.T_REF}\n")
    wet_i = np.nonzero(m["wet"] > 0)[0]
    # cap force: closes the faceted-geometry axial balance so that the TC-02 net axial load is exactly pi 28.625^2 / 10 per MPa (Mechanical's
    # joint-load basis p pi/4 57.25^2 per 10 screws; the gland-1 O-ring carries the 28.600-28.625 annulus); the analytic pi 4.5^2 / 2 on the
    # coarse counterbore facets would add +0.53 %
    minfo = json.loads((OUT / f"model_{tag}.json").read_text())
    cap_unit = math.pi * 28.625 ** 2 / 10.0 - minfo["TC02_axial_force_per_MPa_N"] - minfo["TC03_force_per_MPa_N"]

    def out_req(full=True):
        s = "*NODE PRINT, NSET=N_REF\nU, RF\n"
        if full:
            s += "*NODE FILE\nU\n*EL FILE\nS\n*CONTACT FILE\nCDIS, CSTR\n"
        return s

    def bcs():
        return "N_SYM0, 2, 2\nN_CUT, 3, 3\nN_REF, 2, 3\n"

    mapstats = {}
    mj = json.loads((OUT / f"mesh_{tag}.json").read_text())

    def temps(tc):
        if isinstance(tc, tuple):
            key = f"{tc[1]}:{tc[2]}"
            Tn, stt = mapped_temps(m, mj["shift"], tc[1], tc[2])
            mapstats[key] = stt
            ids = np.nonzero(np.isfinite(Tn))[0]
            return "*TEMPERATURE\n" + "".join(f"{i + 1}, {Tn[i]:.3f}\n" for i in ids)
        return (f"*TEMPERATURE\nN_TC01, {tc['TC-01'] + TK:.2f}\nN_TC02, {tc['TC-02'] + TK:.2f}\nN_SCR, {tc['SCREW'] + TK:.2f}\n")
    inc = "*STEP, INC=200\n*STATIC\n{0}, 1.0, 1e-6, 1.0\n"
    # step 1 SEAT
    w(inc.format(0.5) + "*BOUNDARY\n" + bcs() + f"N_REF, 1, 1, {D_SEAT}\n" + temps(U(20.0)) + out_req(False) + "*END STEP\n")
    # step 2 PRELOAD
    w(inc.format(1.0) + "*BOUNDARY, OP=NEW\n" + bcs() + f"*CLOAD\nN_REF, 1, {T_pre}\n" + temps(U(20.0)) + out_req(True) + "*END STEP\n")
    first = True
    for st in steps:
        pc, tc, _ = STEPS[st]
        w(inc.format(1.0 if mu == 0 else 0.25))
        if first:
            w("*BOUNDARY, FIXED\nN_REF, 1, 1\n")
            first = False
        w("*CLOAD, OP=NEW\n")
        if pc > 0:
            for nd, F in traction_cloads(m, m["cbw"], [0.0, 0.0, pc * cap_unit]).items():
                w(f"{nd + 1}, 3, {F[2]:.6e}\n")
            for nd, F in traction_cloads(m, m["m14"], [0.0, 0.0, pc * math.pi * 10.1 ** 2 / 10.0]).items():
                w(f"{nd + 1}, 3, {F[2]:.6e}\n")
        w("*DLOAD, OP=NEW\n")
        if pc > 0:
            for i in wet_i:
                w(f"{int(m['fe'][i]) + 1}, P{int(m['fk'][i])}, {pc * m['wet'][i]:.6e}\n")
        w(temps(tc) + out_req(True) + "*END STEP\n")
    f.close()
    meta = {"job": job, "mesh": tag, "mu": mu, "preload_N": T_pre, "steps": ["SEAT", "PRELOAD"] + list(steps),
            "cap_force_per_MPa_N": round(cap_unit, 4), "TC02_axial_per_MPa_N": round(math.pi * 28.625 ** 2 / 10.0, 4),
            "step_defs": {s: STEPS[s] for s in steps}, "K_pen": K_PEN, "stick": STICK, "d_seat_mm": D_SEAT, "K_spring_N_mm": K_SPR, "FIT_clearance_mm": fitc, "mapped_fields": mapstats,
            "seat": JS.GEO.get("seat"), "x_seat": JS.GEO.get("x_seat"), "TC01_step_sha16": mj0.get("TC01_step_sha16"), "TC02_step_sha16": mj0.get("TC02_step_sha16"),
            "deck_sha16": hashlib.sha256((wd / f"{job}.inp").read_bytes()).hexdigest()[:16]}
    (wd / "meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta))
    return wd


def run(job, expect=2.5, cap=8.0, timeout_h=4.0):
    import os, ccxrun
    os.environ["FEA3D_EXPECT_GB"] = str(expect)
    os.environ.setdefault("FEA3D_NICE", "10")
    wd = RUNS / job
    res = ccxrun.run_ccx(job, wd, threads=2, mem_cap_gb=cap, timeout_s=timeout_h * 3600)
    (wd / "ccx_run.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res.get(k) for k in ("job", "seconds", "peak_rss_GB", "returncode", "killed", "errors")}, default=str))
    return res


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(sys.argv[2])
    elif cmd == "deck":
        kw = dict(a.split("=", 1) for a in sys.argv[4:])
        write_deck(sys.argv[2], sys.argv[3], float(kw.get("mu", 0.0)), float(kw.get("T", 3000.0)), kw.get("steps", "SOAK").split(","),
                   float(kw.get("fitc", FIT_CLEARANCE)))
    elif cmd == "run":
        kw = dict(a.split("=", 1) for a in sys.argv[3:])
        run(sys.argv[2], float(kw.get("expect", 2.5)), float(kw.get("cap", 8.0)), float(kw.get("timeout_h", 4.0)))
