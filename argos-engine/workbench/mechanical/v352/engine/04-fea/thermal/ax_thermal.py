"""2-D axisymmetric transient thermal FE of the engine (04-fea/thermal, v1.1, 2026-10-12, Mechanical).

v1.1 (2026-10-12): gas radiation is a gray gas-wall EXCHANGE (*RADIATE to T_g = T_aw(x) f_T(t), emissivity
eps_eff(x) = q_rad(x)/(sigma T_aw(x)^4) x f_q(t)/f_T(t)^4), equal to Combustion's incident term on a cold wall and zero at T_w = T_g.
v1 applied the incident term as a fixed *DFLUX (no re-emission) and drove insulating hot faces above the gas temperature
(smoke2: 2914.7 K at 1.0 s vs T_aw 2756.8 K; runs/thermal/DC-B1_gncv2_hi_SS316L_L2.5_smoke2_v1DFLUX_killed/NOTE.txt).
Also v1.1: geometry plane 214 deg (ax_section v1.1); DT_BURN 0.05 s (dt check 0.02/0.05/0.10 in the report); monitor parser fixed.

Model
  Geometry   CAD v3.3 engine group cut at azimuth 214 deg (ax_section.py v1.1) + parametric fuel-grain annulus (ABS) from the END-OF-CYCLE port
             radius of the design cycle to the grain OD (thinnest web held for the whole cycle: conservative for the case) + a 0.225 mm
             gas-gap strip between the grain OD 53.50 and the liner ID 53.95 (CAD clearance) with k_eff = k_air(T) + radiation.
  Contacts   all other part interfaces PERFECT (conforming mesh; CAD clearances <= TOL_MM closed by a fuzzy OCC fragment).  This is the
             UPPER BOUND of heat reaching the metal structure from the hot parts; joint-resistance variants are separate runs.
  Mesh       gmsh OCC 2-D, 6-node triangles -> CalculiX CAX6; size per material x LEVEL factor, refined towards the gas-side curves.
  Units      mm, t, s, mW, K (k in mW/mm/K = W/m/K; rho t/mm3; cp mJ/t/K; h mW/mm2/K = 1e-3 W/m2K; q mW/mm2 = 1e-3 W/m2).
  BCs        burn:  gas side  h(x) f_h(t) x HMUL to T_aw(x) f_T(t)  + gray gas-wall radiation (v1.1, see above), q band lo/hi
                    (Combustion thermal_bc_max_v2.csv Bartz table along x_face; time factors from headend_bc_<DC>_v2.csv);
                    grain   burning surface T_S_GRAIN with h 1e4 W/m2K (pyrolysis-limited surface);
                    N2O     manifold bore h_c(t) to T_N2O(t) (headend_bc CSV);
             coast: cavity walls ADIABATIC except the faces downstream of the throat, which radiate to the exit aperture with
                    emissivity x F_exit (ring-to-disc view factor, numerical) - internal radiative exchange neglected: upper bound for
                    the structure (CalculiX cavity radiation, CR_MODE 'ccx', did not finish its view factors for 1177 faces in > 15 min:
                    smoke run kept in runs/thermal/DC-B1_gncv2_hi_SS316L_L2.5_smoke); N2O static G_N2O_COAST (1 W/K, Combustion)
                    spread over the wetted bore;
             soak:  as coast, no N2O credit, to t_last_shutdown + 3600 s;
             always: outer surfaces h_EXT to T_BAY + radiation (emissivity per material, low values = conservative for the structure).
  Time       fixed increments (*HEAT TRANSFER, DIRECT): DT_BURN in burns, DT_COAST in coasts, soak 0.5 / 5 / 20 s.
Outputs (runs/thermal/<case>/): .inp/.dat/.frd, monitors.csv, envelopes.json (per part max over the sampled frd times), summary.json.
"""
from __future__ import annotations
import sys, os, math, json, time, hashlib, subprocess, re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import engmat
import ax_section

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
COMB = Path("/home/claude/work/shared-fallback/engine/02-combustion/data/v2")
# head-end BC files that Combustion has not published yet but Mechanical generated with Combustion's own unchanged
# run_dispersed_v2p4.py (provenance in that folder's PROVENANCE.txt; Combustion to confirm or replace): searched after COMB
COMB_ALT = Path("/home/claude/work/mechanical/runs/comb_bcgen")
VERSION = "v1.1"


def bc_dir(dc):
    """Directory holding headend_bc_<dc>_v2.csv: the Combustion hub first, then the Mechanical-generated folder."""
    for d in (COMB, COMB_ALT):
        if (d / f"headend_bc_{dc}_v2.csv").exists():
            return d
    raise FileNotFoundError(f"headend_bc_{dc}_v2.csv in {COMB} or {COMB_ALT}")

# ---------------------------------------------------------------- constants (tagged)
SIGMA = 5.670374e-11          # mW/mm2/K4
T_INIT = 293.15               # K   initial (Combustion head-end BC uses 293.15 K N2O / 20 C); hot-day shift reported separately
T_BAY = 288.15                # K   engine-bay air / walls (ASSUMED; airframe bay environment UNKNOWN)
T_AMB_CR = 288.15             # K   environment seen through the nozzle exit (cavity radiation openings)
H_EXT = 10.0e-3               # mW/mm2/K = 10 W/m2K natural convection (ASSUMED bound; Combustion coast h_nc 10 W/m2K)
T_S_GRAIN = 900.0             # K   ABS burning-surface temperature, upper of 700-900 K (Combustion thermal_bc_max_v2 GRAIN PORT row)
H_GRAIN = 10.0                # mW/mm2/K = 1e4 W/m2K (pins the burning surface)
G_N2O_COAST = 1.0e3           # mW/K = 1 W/K static liquid N2O in the manifold during coasts (Combustion headend_thermal_v2)
TOL_MM = 0.10                 # CAD clearances <= TOL_MM are closed (perfect contact); 0.225 mm grain gap is modelled explicitly
GAP_GRAIN = (26.75, 26.975)   # mm  grain OD / liner ID radii (CAD v3.3)
EMIS = {"AL6061-T6": 0.25, "SS316L": 0.40, "SS17-4PH-H1150": 0.40, "IN718": 0.40, "TI6AL4V": 0.40, "PHENOLIC": 0.85, "GRAPHITE-ISO": 0.85,
        "MICA": 0.80, "ABS": 0.90, "GAP-GRAIN": 0.90, "CARBON-PHENOLIC": 0.85, "FLEX-GRAPHITE-OI": 0.50, "ZIRCONIA-FS": 0.50, "YSZ-APS": 0.50, "GLIDCOP-AL15": 0.40,
        "FLEX-GRAPHITE-TH": 0.50}   # v352 N-F2 foil (engmat v1.7, ASSUMED, enclosed in the stack)
EMIS_TAG = ("engmat: Al 0.25 ASSUMED (0.05-0.3, low = conservative for soak-back), 316L/17-4PH/Ti 0.40 ASSUMED (0.3-0.6), graphite 0.85 "
            "LITERATURE-approx, phenolic char 0.85 ASSUMED; mica 0.80 / ABS 0.90 ASSUMED (cavity only); v1.2 carbon-phenolic 0.85 / flexible graphite 0.50 ASSUMED "
            "(engmat v1.2; enclosed in the J1 stack, cavity faces only); v1.4 J2 screen: zirconia 0.50 ASSUMED (engmat v1.4, enclosed, cavity faces only)")
SIZE = {"AL6061-T6": 1.0, "SS316L": 0.7, "SS17-4PH-H1150": 0.5, "IN718": 0.5, "TI6AL4V": 0.7, "PHENOLIC": 0.30, "GRAPHITE-ISO": 0.45, "MICA": 0.25,
        "ABS": 0.6, "GAP-GRAIN": 0.12, "CARBON-PHENOLIC": 0.25, "FLEX-GRAPHITE-OI": 0.08, "ZIRCONIA-FS": 0.25, "YSZ-APS": 0.10, "GLIDCOP-AL15": 0.5, "FLEX-GRAPHITE-TH": 0.08}   # v1.2: J1 hot layer 2.0 mm / seal 0.5 mm; J2 zirconia as the J1 hot layer
SIZE_PN = {"ENG-NZ-05": 0.08, "ENG-TC-03C": 0.05, "ENG-NZ-06": 0.05}   # v352: 0.25 mm N-F2 foil >= 2 quadratic elements through at L2.5  # v1.3 (J1b screen): the 0.5-1.0 mm mica layer meshed like the seal (>= 2 elements through); MICA size kept for the v1.1 runs
SIZE_SURF = 0.12              # mm at gas-side curves (x LEVEL)
SIZE_DIST = 3.0               # mm transition distance from gas-side curves
DT_BURN, DT_COAST = 0.05, 0.10   # s; v1 used 0.02 (smoke2); dt check 0.02 / 0.05 / 0.10 on level 2.5
CR_MODE = "exitview"          # 'exitview' (v1 default) or 'ccx' (CalculiX cavity radiation; view factors too slow for the fine meshes)
SOAK = [(60.0, 0.5), (600.0, 5.0), (3600.0, 20.0)]   # (end of segment after last shutdown, increment)


# ---------------------------------------------------------------- materials (mm-t-s-mW-K)
def air_k(T):
    """W/m/K, air at 1 atm, Incropera & DeWitt 6th ed. Table A.4 (LITERATURE, verify): 300 K 0.0263 ... 1000 K 0.0667."""
    Tt = [300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1400]
    kk = [0.0263, 0.0338, 0.0407, 0.0469, 0.0524, 0.0573, 0.0620, 0.0667, 0.0763, 0.0852]
    return float(np.interp(T, Tt, kk))


def mat_tables(mat, k_scale=1.0):
    """(rho t/mm3, [(k, T)], [(cp, T)]) in mm-t-s-mW-K."""
    if mat == "GAP-GRAIN":
        d = (GAP_GRAIN[1] - GAP_GRAIN[0]) * 1e-3
        eps_eff = 1.0 / (1 / EMIS["ABS"] + 1 / EMIS["PHENOLIC"] - 1)
        Ts = [293.15, 400, 600, 800, 1000, 1200, 1400]
        kt = [(air_k(T) + 4 * 5.670374e-8 * T ** 3 * d * eps_eff, T) for T in Ts]
        return 1.0e-12, kt, [(1000.0e6, 293.15)]
    M = engmat.MATERIALS[mat]
    rho = M["rho"]["v"] * 1e-12
    kk = M["k"]
    cc = M["cp"]
    kt = [(v * k_scale, T + 273.15) for T, v in zip(kk.get("T_C", [20]), kk.get("v", [kk.get("v")]))] if "T_C" in kk else [(kk["v"] * k_scale, 293.15)]
    ct = [(v * 1e6, T + 273.15) for T, v in zip(cc["T_C"], cc["v"])] if "T_C" in cc else [(cc["v"] * 1e6, 293.15)]
    return rho, kt, ct


# ---------------------------------------------------------------- BC data (Combustion)
def read_headend(dc):
    f = bc_dir(dc) / f"headend_bc_{dc}_v2.csv"
    d = np.genfromtxt(f, delimiter=",", names=True, skip_header=1)
    return d, f


def read_bartz():
    """x_face (m) -> h_g (W/m2K) at Tw 600 K, T_aw (K), q_rad lo/hi (W/m2) at the max-thrust point (thermal_bc_max_v2.csv)."""
    f = COMB / "thermal_bc_max_v2.csv"
    xs, hs, ts, ql, qh = [], [], [], [], []
    import csv
    with open(f) as fh:
        rows = [r for r in csv.reader(l for l in fh if not l.startswith("#"))]
    hdr = rows[0]
    ix = {k: hdr.index(k) for k in ("x_face_m", "T_aw_K", "h_g_Tw600_W_m2K", "q_rad_band_W_m2")}
    for r in rows[1:]:
        try:
            x = float(r[ix["x_face_m"]]); h = float(r[ix["h_g_Tw600_W_m2K"]]); T = float(r[ix["T_aw_K"]])
            lo, hi = [float(v) for v in r[ix["q_rad_band_W_m2"]].split("-")]
        except (ValueError, IndexError):
            continue
        xs.append(x); hs.append(h); ts.append(T); ql.append(lo); qh.append(hi)
    o = np.argsort(xs, kind="stable")
    return {"x": np.array(xs)[o], "h": np.array(hs)[o], "Taw": np.array(ts)[o], "qlo": np.array(ql)[o], "qhi": np.array(qh)[o], "file": f}


def end_port_radius(dc):
    """End-of-cycle port radius (mm) from the duty-cycle history named in the head-end CSV header."""
    bd = bc_dir(dc)
    hdr = open(bd / f"headend_bc_{dc}_v2.csv").readline()
    m = re.search(r"Source DC: (\S+?)\.?\s", hdr)
    src = bd / m.group(1).rstrip(".")
    import csv
    rows = list(csv.DictReader(open(src)))
    D = max(float(r["D_max"]) for r in rows if r["D_max"])
    return 0.5 * D * 1e3, src


# ---------------------------------------------------------------- geometry + mesh
def faces_model(aft_material="SS316L", r_port=None, overrides=None):
    import cadquery as cq
    ov = dict(overrides or {})
    if aft_material != "SS316L":
        ov["aft_section_material"] = aft_material
    faces, info, _ = ax_section.section(overrides=ov or None)
    rp = r_port if r_port is not None else info["D_port0"] / 2
    zt, zb = info["grain_top"], info["grain_bot"]
    g = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(rp, zb, 0), cq.Vector(GAP_GRAIN[0], zb, 0), cq.Vector(GAP_GRAIN[0], zt, 0),
                                                   cq.Vector(rp, zt, 0)], close=True))
    gap = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(GAP_GRAIN[0], zb, 0), cq.Vector(GAP_GRAIN[1], zb, 0), cq.Vector(GAP_GRAIN[1], zt, 0),
                                                     cq.Vector(GAP_GRAIN[0], zt, 0)], close=True))
    faces = faces + [{"pn": "ENG-GR", "material": "ABS", "face": g, "area_mm2": g.Area()},
                     {"pn": "GAP-GRAIN", "material": "GAP-GRAIN", "face": gap, "area_mm2": gap.Area()}]
    info["r_port_mm"] = rp
    return faces, info


def face_paths(faces):
    from matplotlib.path import Path as MPath
    out = []
    for f in faces:
        ow = f["face"].outerWire()
        pts = np.array([v.toTuple()[:2] for v in ow.positions(np.linspace(0, 1, 2000).tolist())])
        holes = [np.array([v.toTuple()[:2] for v in w.positions(np.linspace(0, 1, 800).tolist())]) for w in f["face"].innerWires()]
        out.append((MPath(pts), [MPath(h) for h in holes]))
    return out


def inside_any(paths, P, skip=None, rad=0.0):
    P = np.atleast_2d(P)
    res = np.zeros(len(P), bool)
    for i, (op, hs) in enumerate(paths):
        if skip is not None and i == skip:
            continue
        m = op.contains_points(P, radius=rad)
        for h in hs:
            m &= ~h.contains_points(P)
        res |= m
    return res


class Classifier:
    """Boundary classification of a point just outside a solid (probe): GAS (chamber cavity), N2O (manifold bore), EXT (outside air),
    VOID (enclosed gap/groove: adiabatic)."""

    def __init__(self, info, paths):
        self.i, self.paths = info, paths
        c = np.array(info["contour"])                  # (z, r) nozzle contour, z descending
        self.cz, self.cr = c[:, 0], c[:, 1]

    def r_wall(self, z):
        i = self.i
        d = 0.35
        if z > i["grain_top"] - d:
            return i["r_pre"] + d                       # pre-chamber (up to the injector face)
        if z > i["grain_bot"] - d:
            return i["r_port_mm"] + d                   # port (end-of-cycle web)
        if z > i["post_bot"] - d:
            return i["r_post"] + d                      # post-chamber
        o = np.argsort(self.cz)
        return float(np.interp(z, self.cz[o], self.cr[o])) + d

    def cls(self, p):
        r, z = float(p[0]), float(p[1])
        i = self.i
        if i["exit"] - 3.5 <= z <= i["inj_face"] + 0.02 and r <= self.r_wall(z):
            return "GAS"
        if i["inj_face"] < z <= i["z_seat"] + 0.05 and r <= 7.35:
            return "GAS"                                # TC-03 diffuser cone downstream of the seat line (chamber side)
        if i["z_seat"] + 0.05 < z < i["bonnet_top"] - 9.0 + 0.05 and r < 5.25:
            return "N2O"                                # manifold bore up to the stem-seal gland (TC-04, z bonnet_top - 9)
        rr = np.arange(r + 0.06, 60.0, 0.05)
        ray = np.column_stack([rr, np.full(len(rr), z)])
        if inside_any(self.paths, ray).any():
            return "VOID"
        return "EXT"


def mesh(faces, info, level=1.0, workdir=None, verbose=False):
    """Conforming 2-D tri6 mesh.  Returns dict(X (mm, Nx2), E (Mx6, 0-based, CalculiX CAX6 order, CCW), mat (M,), pn (M,))."""
    import gmsh
    import cadquery as cq
    workdir = Path(workdir or RUNS / "mesh")
    workdir.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.model.add("ax")
    in_tags = []
    for k, f in enumerate(faces):
        b = workdir / f"f{k}.brep"
        f["face"].exportBrep(str(b))
        tags = gmsh.model.occ.importShapes(str(b))
        in_tags.append([t for d, t in tags if d == 2])
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Geometry.ToleranceBoolean", TOL_MM)
    allin = [(2, t) for ts in in_tags for t in ts]
    out, omap = gmsh.model.occ.fragment(allin[:1], allin[1:])
    gmsh.model.occ.synchronize()
    # map fragment surfaces -> source face (first owner wins; overlaps reported)
    owner, overl = {}, []
    flat_src = [k for k, ts in enumerate(in_tags) for _ in ts]
    for j, lst in enumerate(omap):
        for d, t in lst:
            if d != 2:
                continue
            k = flat_src[j]
            if t in owner and owner[t] != k:
                # overlap of two source faces (CAD interference, e.g. a threaded insert modelled at the major diameter):
                # the SMALLER source face owns the region (the inserted part keeps its full section)
                a_old, a_new = faces[owner[t]]["area_mm2"], faces[k]["area_mm2"]
                overl.append({"surf": t, "faces": [faces[owner[t]]["pn"], faces[k]["pn"]], "area_mm2": round(gmsh.model.occ.getMass(2, t), 3),
                              "owner": faces[k]["pn"] if a_new < a_old else faces[owner[t]]["pn"]})
                if a_new < a_old:
                    owner[t] = k
            else:
                owner.setdefault(t, k)
    surfs = [t for d, t in gmsh.model.getEntities(2)]
    paths = face_paths(faces)
    for t in surfs:
        if t not in owner:                                   # not in the fragment map: centroid test
            c = gmsh.model.occ.getCenterOfMass(2, t)
            for k in range(len(faces)):
                if inside_any([paths[k]], np.array([c[:2]]))[0]:
                    owner[t] = k
                    break
    # size fields
    clf = Classifier(info, paths)
    gas_curves = []
    for d, c in gmsh.model.getEntities(1):
        up, _ = gmsh.model.getAdjacencies(1, c)
        if len(up) != 1:
            continue
        lo, hi = gmsh.model.getParametrizationBounds(1, c)
        u = 0.5 * (lo[0] + hi[0])
        p = np.array(gmsh.model.getValue(1, c, [u]))[:2]
        dv = np.array(gmsh.model.getDerivative(1, c, [u]))[:2]
        n = np.array([dv[1], -dv[0]]) / (np.linalg.norm(dv) + 1e-30)
        q1, q2 = p + 0.05 * n, p - 0.05 * n
        s1 = inside_any(paths, q1)[0]
        probe = q2 if s1 else q1
        if clf.cls(probe) == "GAS":
            gas_curves.append(c)
    fields = []
    for k, f in enumerate(faces):
        ss = [t for t in surfs if owner.get(t) == k]
        if not ss:
            continue
        fc = gmsh.model.mesh.field.add("Constant")
        gmsh.model.mesh.field.setNumbers(fc, "SurfacesList", ss)
        gmsh.model.mesh.field.setNumber(fc, "VIn", SIZE_PN.get(f["pn"], SIZE[f["material"]]) * level)
        gmsh.model.mesh.field.setNumber(fc, "VOut", 1e3)
        fields.append(fc)
    if gas_curves:
        fd = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(fd, "CurvesList", gas_curves)
        gmsh.model.mesh.field.setNumber(fd, "Sampling", 400)
        ft = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(ft, "InField", fd)
        gmsh.model.mesh.field.setNumber(ft, "SizeMin", SIZE_SURF * level)
        gmsh.model.mesh.field.setNumber(ft, "SizeMax", 50.0)
        gmsh.model.mesh.field.setNumber(ft, "DistMin", 0.0)
        gmsh.model.mesh.field.setNumber(ft, "DistMax", SIZE_DIST * 25)      # linear growth ~ 2 mm per mm of depth
        fields.append(ft)
    fm = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(fm, "FieldsList", fields)
    gmsh.model.mesh.field.setAsBackgroundMesh(fm)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)                    # Frontal-Delaunay 2-D
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 1)
    t0 = time.time()
    gmsh.model.mesh.generate(2)
    tags, coords, _ = gmsh.model.mesh.getNodes()
    X = coords.reshape(-1, 3)[:, :2]
    idx = -np.ones(int(tags.max()) + 1, np.int64)
    idx[tags.astype(np.int64)] = np.arange(len(tags))
    E, M, PN = [], [], []
    for t in surfs:
        et, _, en = gmsh.model.mesh.getElements(2, t)
        for typ, nn in zip(et, en):
            if typ != 9:                                          # 6-node triangle
                continue
            c = idx[np.array(nn, np.int64).reshape(-1, 6)]
            E.append(c)
            k = owner.get(t, -1)
            M += [faces[k]["material"] if k >= 0 else "UNKNOWN"] * len(c)
            PN += [faces[k]["pn"] if k >= 0 else "UNKNOWN"] * len(c)
    gmsh.finalize()
    E = np.vstack(E)
    used = np.unique(E)
    remap = -np.ones(len(X), np.int64)
    remap[used] = np.arange(len(used))
    X, E = X[used], remap[E]
    # orientation (CCW in r-z)
    a = X[E[:, 1]] - X[E[:, 0]]
    b = X[E[:, 2]] - X[E[:, 0]]
    neg = (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) < 0
    E[neg] = E[neg][:, [0, 2, 1, 5, 4, 3]]
    return {"X": X, "E": E, "mat": np.array(M), "pn": np.array(PN), "overlaps": overl, "n_gas_curves": len(gas_curves),
            "t_mesh_s": round(time.time() - t0, 1), "paths": paths, "clf": clf, "level": level}


EDGE_NODES = {1: (0, 1, 3), 2: (1, 2, 4), 3: (2, 0, 5)}            # CAX6 face -> (corner, corner, mid)


def exit_view_factor(r1, z1, n, Ra, za, nr=80, nphi=160):
    """View factor from a wall ring element (r1, z1) with unit normal n = (n_r, n_z) into the gas, to the coaxial exit aperture disc
    (radius Ra at z = za, facing +z into the cavity); unobstructed line of sight assumed (valid downstream of the throat: the
    divergent cone + exit cylinder is convex).  Midpoint rule over the disc (polar grid)."""
    rho = (np.arange(nr) + 0.5) / nr * Ra
    phi = (np.arange(nphi) + 0.5) / nphi * 2 * math.pi
    R, PH = np.meshgrid(rho, phi)
    dA = (Ra / nr) * (2 * math.pi / nphi) * R
    sx, sy, sz = R * np.cos(PH) - r1, R * np.sin(PH), za - z1
    s2 = sx * sx + sy * sy + sz * sz
    s = np.sqrt(s2)
    c1 = (n[0] * sx + n[1] * sz) / s
    c2 = (z1 - za) / s
    return float(np.sum(np.clip(c1, 0, None) * np.clip(c2, 0, None) / (math.pi * s2) * dA))


def boundary_edges(m):
    """[(elem, face, class, r_mid, z_mid, length, area_axisym)] for every free edge."""
    X, E = m["X"], m["E"]
    cnt = {}
    for e in range(len(E)):
        for f, (i, j, _) in EDGE_NODES.items():
            key = (min(E[e, i], E[e, j]), max(E[e, i], E[e, j]))
            cnt.setdefault(key, []).append((e, f))
    out = []
    clf = m["clf"]
    for key, lst in cnt.items():
        if len(lst) != 1:
            continue
        e, f = lst[0]
        i, j, k = EDGE_NODES[f]
        p0, p1, pm = X[E[e, i]], X[E[e, j]], X[E[e, k]]
        t = p1 - p0
        L = float(np.linalg.norm(t))
        n = np.array([t[1], -t[0]]) / max(L, 1e-12)               # CCW element: outward normal = rotate tangent clockwise
        probe = pm + 0.04 * n
        c = clf.cls(probe)
        r_ = 0.5 * (p0[0] + p1[0])
        out.append((e, f, c, float(pm[0]), float(pm[1]), L, 2 * math.pi * max(r_, 1e-6) * L, n))
    return out


# ---------------------------------------------------------------- case setup / input deck
def decimate(t, ys, dt_min):
    keep = [0]
    for k in range(1, len(t) - 1):
        if t[k] - t[keep[-1]] >= dt_min or any(abs(y[k] - y[keep[-1]]) > 0.02 * (abs(y[keep[-1]]) + 1e-9) for y in ys):
            keep.append(k)
    keep.append(len(t) - 1)
    return np.array(keep)


def segments(d):
    t, b = d["t_s"], d["burning"] > 0.5
    segs, on = [], False
    for k in range(len(t)):
        if b[k] and not on:
            on, t0 = True, t[k]
        if not b[k] and on:
            on = False
            segs.append((float(t0), float(t[k - 1])))
    if on:
        segs.append((float(t0), float(t[-1])))
    return segs


def write_case(case, m, edges, info, out_dir):
    """case: dict(dc, HMUL_ch, HMUL_nz, QMUL ('lo'/'hi'), soak_end, monitors, k_phen_scale, label)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    d, fhe = read_headend(case["dc"])
    bz = read_bartz()
    segs = segments(d)
    t_last = segs[-1][1]
    soak_end = t_last + case.get("soak_s", 3600.0)
    # gas-side reference values (max point) per edge: x_face from the injector face along the axis
    xs = bz["x"]
    def at_x(arr, x):
        return float(np.interp(x, xs, arr))
    h_ref, T_ref, q_ref = 889.4, float(bz["Taw"][0]), (bz["qhi"][0] if case["QMUL"] == "hi" else bz["qlo"][0])
    he = {"h": d["h_g_face_W_m2K"], "T": d["T_aw_upper_K"], "q": d[f"q_rad_{case['QMUL']}_W_m2"], "hc": d["h_c_N2O_W_m2K"], "TN": d["T_N2O_liquid_K"]}
    burning = d["burning"] > 0.5
    fh = np.where(burning, he["h"] / h_ref, 0.0)
    fT = np.where(burning, np.nan_to_num(he["T"], nan=T_ref) / T_ref, 1.0)
    fq = np.where(burning, he["q"] / q_ref, 0.0)
    hc = np.nan_to_num(he["hc"], nan=0.0)
    hc_ref = max(hc.max(), 1.0)
    fhc = np.where(burning, hc / hc_ref, 0.0)
    TN_ref = 293.15
    fTN = he["TN"] / TN_ref
    gas = [e for e in edges if e[2] == "GAS" and m["mat"][e[0]] not in ("ABS", "GAP-GRAIN")]
    grain = [e for e in edges if e[2] == "GAS" and m["mat"][e[0]] in ("ABS", "GAP-GRAIN")]
    n2o = [e for e in edges if e[2] == "N2O"]
    ext = [e for e in edges if e[2] == "EXT"]
    A_n2o = sum(e[6] for e in n2o)
    # coast/soak cavity treatment (CR_MODE 'exitview'): internal exchange neglected (adiabatic cavity walls = upper bound for the
    # structure); faces downstream of the throat radiate to the exit aperture (insert bottom, radius re) with emissivity x F_exit
    exit_rad = []
    if CR_MODE != "ccx":
        za, Ra = info["insert_bot"], info["re"]
        for e in gas:
            if e[4] < info["throat"] - 1e-6:
                Fx = exit_view_factor(e[3], e[4], e[7], Ra, za)
                if Fx > 1e-4:
                    exit_rad.append((e, Fx))
    h_n2o_coast = G_N2O_COAST / max(A_n2o, 1e-9)
    X, E = m["X"], m["E"]
    mats = sorted(set(m["mat"]))
    jn = case["label"]
    inp = out_dir / f"{jn}.inp"
    with open(inp, "w") as f:
        f.write(f"*HEADING\nENG 2-D axisymmetric thermal {VERSION} case {jn} ({case['dc']}) ax_thermal.py\n")
        f.write("*NODE, NSET=NALL\n")
        for q, x in enumerate(X):
            f.write(f"{q+1}, {x[0]:.6f}, {x[1]:.6f}\n")
        for mt in mats:
            ids = np.nonzero(m["mat"] == mt)[0]
            f.write(f"*ELEMENT, TYPE=CAX6, ELSET=M_{mt.replace('-', '_')}\n")
            for e in ids:
                f.write(f"{e+1}, " + ", ".join(str(int(n) + 1) for n in E[e]) + "\n")
        for pn in sorted(set(m["pn"])):
            ids = np.nonzero(m["pn"] == pn)[0] + 1
            f.write(f"*ELSET, ELSET=P_{pn.replace('-', '_')}\n")
            for k in range(0, len(ids), 12):
                f.write(", ".join(str(int(x)) for x in ids[k:k + 12]) + "\n")
        for mt in mats:
            rho, kt, ct = mat_tables(mt, k_scale=case.get("k_scale", {}).get(mt, 1.0))
            f.write(f"*MATERIAL, NAME={mt.replace('-', '_')}\n*DENSITY\n{rho:.6e}\n*CONDUCTIVITY\n")
            for k_, T_ in kt:
                f.write(f"{k_:.6e}, {T_:.2f}\n")
            f.write("*SPECIFIC HEAT\n")
            for c_, T_ in ct:
                f.write(f"{c_:.6e}, {T_:.2f}\n")
            f.write(f"*SOLID SECTION, ELSET=M_{mt.replace('-', '_')}, MATERIAL={mt.replace('-', '_')}\n")
        # monitors
        mon = []
        for name, (r, z, pn) in case["monitors"].items():
            sel = np.unique(E[m["pn"] == pn]) if pn else np.arange(len(X))
            if len(sel) == 0:
                continue
            k = sel[np.argmin(np.hypot(X[sel, 0] - r, X[sel, 1] - z))]
            mon.append((name, int(k), float(X[k, 0]), float(X[k, 1]), pn))
        f.write("*NSET, NSET=NMON\n" + "\n".join(str(k + 1) for _, k, *_ in mon) + "\n")
        f.write(f"*PHYSICAL CONSTANTS, ABSOLUTE ZERO=0., STEFAN BOLTZMANN={SIGMA:.6e}\n")
        f.write(f"*INITIAL CONDITIONS, TYPE=TEMPERATURE\nNALL, {T_INIT}\n")
        # amplitudes (total time)
        t = d["t_s"]
        keep = decimate(t, [fh, fT, fq, fhc, fTN], 0.05)
        fqr = np.where(burning, fq / np.maximum(fT, 1e-6) ** 4, 0.0)       # v1.1 emissivity amplitude (product = q_inc(t) on a cold wall)
        for nm, y in (("AH", fh), ("AT", fT), ("AQ", fq), ("AQR", fqr), ("AHN", fhc), ("ATN", fTN)):
            f.write(f"*AMPLITUDE, NAME={nm}, TIME=TOTAL TIME\n0., {y[0]:.6f}\n")
            for k in keep:
                if t[k] > 0:
                    f.write(f"{t[k]:.4f}, {y[k]:.6f}\n")
            f.write(f"{soak_end + 10:.1f}, {y[-1] if nm in ('ATN',) else (1.0 if nm == 'AT' else 0.0):.6f}\n")
        # step list
        steps = []
        tc = 0.0
        for k, (a, b) in enumerate(segs):
            if a > tc + 1e-9:
                steps.append(("COAST", tc, a))
            steps.append(("BURN", a, b))
            tc = b
        for s_end, dt in SOAK:
            te = t_last + s_end
            if te > tc + 1e-9:
                steps.append((f"SOAK{dt:g}", tc, min(te, soak_end)))
                tc = min(te, soak_end)
        def bc_ext(f):
            f.write("*FILM, OP=NEW\n")
            for e in ext:
                f.write(f"{e[0]+1}, F{e[1]}, {T_BAY}, {H_EXT:.6e}\n")
        for kind, a, b in steps:
            dur = b - a
            if dur <= 1e-9:
                continue
            dt = DT_BURN if kind == "BURN" else (DT_COAST if kind == "COAST" else float(kind[4:]))
            n_inc = max(1, int(math.ceil(dur / dt - 1e-9)))
            f.write(f"** {kind} {a:.3f} -> {b:.3f} s\n*STEP, INC={n_inc + 10}\n*HEAT TRANSFER, DIRECT\n{dur / n_inc:.6f}, {dur:.6f}\n")
            bc_ext(f)
            if kind == "BURN":
                f.write("*FILM, AMPLITUDE=AT, FILM AMPLITUDE=AH\n")
                for e in gas:
                    x = max(0.0, (info["inj_face"] - e[4]) * 1e-3)
                    hmul = case["HMUL_nz"] if x > 0.300 else case["HMUL_ch"]
                    h = at_x(bz["h"], x) * hmul
                    Taw = at_x(bz["Taw"], x)
                    f.write(f"{e[0]+1}, F{e[1]}, {Taw:.2f}, {h * 1e-3:.6e}\n")
                f.write("*FILM\n")
                for e in grain:
                    f.write(f"{e[0]+1}, F{e[1]}, {T_S_GRAIN:.2f}, {H_GRAIN:.6e}\n")
                f.write("*FILM, AMPLITUDE=ATN, FILM AMPLITUDE=AHN\n")
                for e in n2o:
                    f.write(f"{e[0]+1}, F{e[1]}, {TN_ref:.2f}, {hc_ref * 1e-3:.6e}\n")
                f.write("*DFLUX, OP=NEW\n")
                f.write("*RADIATE, OP=NEW\n")
                for e in ext:
                    f.write(f"{e[0]+1}, R{e[1]}, {T_BAY}, {EMIS[m['mat'][e[0]]]:.3f}\n")
                # v1.1 gray gas-wall exchange: q = eps_eff sigma (T_g^4 - T_w^4), eps_eff = q_inc/(sigma T_aw^4) on a cold wall
                f.write("*RADIATE, AMPLITUDE=AT, RADIATION AMPLITUDE=AQR\n")
                for e in gas:
                    x = max(0.0, (info["inj_face"] - e[4]) * 1e-3)
                    qx = at_x(bz["qhi"] if case["QMUL"] == "hi" else bz["qlo"], x)
                    Taw = at_x(bz["Taw"], x)
                    eps = qx / (SIGMA * 1e3 * Taw ** 4)
                    f.write(f"{e[0]+1}, R{e[1]}, {Taw:.2f}, {eps:.5f}\n")
            else:
                if kind == "COAST":
                    f.write("*FILM\n")
                    TNc = float(he["TN"][np.searchsorted(t, a) - 1]) if a > t[0] else TN_ref
                    for e in n2o:
                        f.write(f"{e[0]+1}, F{e[1]}, {TNc:.2f}, {h_n2o_coast:.6e}\n")
                f.write("*DFLUX, OP=NEW\n")
                f.write("*RADIATE, OP=NEW\n")
                for e in ext:
                    f.write(f"{e[0]+1}, R{e[1]}, {T_BAY}, {EMIS[m['mat'][e[0]]]:.3f}\n")
                if CR_MODE == "ccx":
                    for e in gas + grain:
                        f.write(f"{e[0]+1}, R{e[1]}CR, {T_AMB_CR}, {EMIS[m['mat'][e[0]]]:.3f}\n")
                else:
                    for e, Fx in exit_rad:
                        f.write(f"{e[0]+1}, R{e[1]}, {T_AMB_CR}, {EMIS[m['mat'][e[0]]] * Fx:.4f}\n")
            f.write("*NODE PRINT, NSET=NMON, FREQUENCY=1\nNT\n")
            # frd sampling (TIME POINTS cannot be combined with DIRECT): ~0.5 s in burns, ~1 s in coasts and the first soak minute, every increment later
            frq = max(1, int(round((0.5 if kind == "BURN" else (1.0 if kind in ("COAST", "SOAK0.5") else dt)) / (dur / n_inc))))
            f.write(f"*NODE FILE, FREQUENCY={frq}\nNT\n*END STEP\n")
    meta = {"case": case, "inp": str(inp), "headend_csv": str(fhe), "headend_sha256_16": hashlib.sha256(Path(fhe).read_bytes()).hexdigest()[:16],
            "bartz_csv": str(bz["file"]), "bartz_sha256_16": hashlib.sha256(Path(bz["file"]).read_bytes()).hexdigest()[:16],
            "segments_s": segs, "t_last_shutdown_s": t_last, "soak_end_s": soak_end, "steps": steps,
            "n_nodes": int(len(X)), "n_elems": int(len(E)), "n_edges": {"gas": len(gas), "grain": len(grain), "n2o": len(n2o), "ext": len(ext),
                                                                      "void": sum(1 for e in edges if e[2] == "VOID")},
            "A_n2o_mm2": A_n2o, "h_n2o_coast_W_m2K": h_n2o_coast * 1e3, "monitors": mon, "cr_mode": CR_MODE,
            "exit_view": {"n_faces": len(exit_rad), "F_min": min((x for _, x in exit_rad), default=None), "F_max": max((x for _, x in exit_rad), default=None)}}
    (out_dir / f"{jn}_meta.json").write_text(json.dumps(meta, indent=1, default=str))
    return inp, meta


def run(inp, threads=1, timeout=6 * 3600):
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads))
    t0 = time.time()
    r = subprocess.run(["ccx", "-i", inp.stem], cwd=str(inp.parent), env=env, capture_output=True, text=True, timeout=timeout)
    (inp.parent / f"{inp.stem}.log").write_text(r.stdout[-200000:] + "\n" + r.stderr)
    err = [l for l in r.stdout.splitlines() if "*ERROR" in l]
    return {"seconds": round(time.time() - t0, 1), "errors": err[:5], "returncode": r.returncode}


def read_monitors(dat, mon):
    """{name: (t array, T array)} from *NODE PRINT NT blocks."""
    ids = {}
    for nm, k, *_ in mon:                       # v1.3: several monitors may share one node (J1b: NZ03_mica = NZ05_mica_top_r20)
        ids.setdefault(k + 1, []).append(nm)
    out = {nm: ([], []) for nms in ids.values() for nm in nms}
    cur_t = None
    with open(dat) as fh:
        for line in fh:
            if line.strip().startswith("temperatures") and "time" in line:
                cur_t = float(line.split()[-1])
                continue
            p = line.split()
            if cur_t is not None and len(p) == 2:
                try:
                    n, T = int(p[0]), float(p[1])
                except ValueError:
                    continue
                for nm in ids.get(n, ()):
                    out[nm][0].append(cur_t)
                    out[nm][1].append(T)
    return {k: (np.array(a), np.array(b)) for k, (a, b) in out.items()}


def read_frd_nt(frd):
    """Generator of (time, {node: T}) from an ASCII .frd (NDTEMP blocks)."""
    t, vals, inblk = None, None, False
    with open(frd) as fh:
        for line in fh:
            if line.startswith("    1PSTEP"):
                continue
            if line.startswith("  100CL"):
                t = float(line[12:24])
                vals, inblk = {}, False
                continue
            if line.startswith(" -4  NDTEMP"):
                inblk = True
                continue
            if inblk:
                if line.startswith(" -1"):
                    vals[int(line[3:13])] = float(line[13:25])
                elif line.startswith(" -3"):
                    inblk = False
                    yield t, vals


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dc", default="DC-B1_gncv2")
    ap.add_argument("--level", type=float, default=1.4)
    ap.add_argument("--mesh_only", action="store_true")
    a = ap.parse_args()
    rp, src = end_port_radius(a.dc)
    faces, info = faces_model(r_port=rp)
    m = mesh(faces, info, level=a.level, workdir=RUNS / "mesh")
    ed = boundary_edges(m)
    from collections import Counter
    print("nodes", len(m["X"]), "elems", len(m["E"]), "overlaps", m["overlaps"][:5], "gas curves", m["n_gas_curves"], "t", m["t_mesh_s"])
    print(Counter(e[2] for e in ed), Counter(m["mat"]))
