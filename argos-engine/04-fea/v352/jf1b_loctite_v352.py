"""J-F1b cycle temperature (rule of lead 19:53:27Z item 4) and the LOCTITE 243 tap-zone temperature at the abort TB states (same item;
continued 20:30:00Z and 20:49:35Z: read-only).  Mechanical, 2026-10-20, v1.  Reads only existing fields and records (no solver run, no
thermal run, no ccx); every file is read into memory (npz arrays by numpy, JSON as text); nothing is decompressed to disk.
SIM (CalculiX thermal / S-AX fields) and ASSUMED (the TB surrogate) as tagged; not physical approval.

J-F1b RULE (lead 19:53:27Z (4), verbatim): "Peak = max(160 C, the highest J-FWD spring/screw-zone temperature in any soak or abort TB
state that rows v7 used, + 10 C), rounded up to the next 5 C. Dwell at peak is at least that state's computed time above (peak - 10 C)."
  States rows v7 used (jfwd_in718_rows_v352_v7.json 'states', thermal definitions from FEA3D js5 meta.json step_defs, the same in every
  history (a), (a'), (a''), (b2)): PRELOAD 20 C; SOAK70 = S-AX GVLO field B1_70.7 mapped; SOAK = uniform 'soak 64.7 s GVLO row means'
  (TC-01 158.0 / TC-02 96.0 / SCREW 127.0); SOAK52 = S-AX GVLO field B1_51.7 mapped; FA1S = uniform 45.6 C.  No abort TB state is used by
  rows v7 (no TB, abort or B1_ key in the file).
  Spring / screw zone (drawn and ruled geometry): the screw (head dk max 9.5, ISO 7380-1 M5; shank and thread d 5.0; thread engaged in the
  TC-02 tap from the TC-02 OD to the tip at r_flat + t_spring,min - L_max = 31.313 + 0.44 - 10.8 = 20.953) and the disc spring HW-170 solid
  under the head (De 10.0 h12 max, Di 5.2; the full annulus bears on the TC-01 flat at r_flat 31.313 and under the head), each placed with
  the ruled offsets: axial 0.3705 (F4, the z-direction centring stack) and tangential 0.557 (full float; F2 registered stack 0.4865 is
  inside it).  The axisymmetric fields have no hole: a point (y tangential, dz axial) on the flat is read at r = sqrt(r_flat^2 + y^2),
  z = z_row + dz, z_row = TC-01 forward end - 12.000 (hole row 12.000 BASIC from datum B, the TC-01 forward end face); the head, outside
  the TC-01 material, takes the TC-01 OD value at its z (as the part-aware nearest-node mapping does).
  Values: (1) FEA3D's js5 records of the states as applied (meta mapped_fields, post steps: SCREW node set max / mean, shank maximum,
  TC-01 band, TC-02 thread); (2) the S-AX state field itself (res.npz T, the file FEA3D mapped: quadratic CAX6 interpolation on the
  TC-01 / TC-02 elements) over the zone; (3) the B1 history of the thermal run behind the S-AX states (every output frame of
  DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO, thermal frame z = S-AX z + 6.544 (run.json dz_frame), linear interpolation on the
  thermal nodes) for the 'computed time above' (linear crossing interpolation as tf1_exposure_v352.py).
LOCTITE 243 tap zone at the abort TB states: the adopted abort value A = 150 C (CHANGELOG 243 (3), 16:53Z) on both gap-conductance
  bounds: the TB_a150 state field = the B1 end-of-burn field (t 21.651 s) of the rev-4 thermal run + the uniform shift_K of the S-AX
  TB_a150 run.json (sax.py 'case_to_abort', ASSUMED surrogate; the S-AX res.npz of the TB states are not on disk, so the field is read
  from the thermal history at the same frame plus the recorded shift, which is how sax.py built it).  Tap zone = TC-02 nodes within the
  thread band |dz| <= 2.5 + 0.3705 of the hole row and r from the screw tip 20.953 to the TC-02 OD; the TC-02 part maximum is checked
  against bpkg_abort_v352_v1 (223.4 / 208.0 C).  The ASSUMED shifted history (the whole B1 history with the shift) is information only.
Usage: jf1b_loctite_v352.py -> v352/jfwd/jf1b_loctite_v352_v1.json"""
import hashlib, json, math, time
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay

T0 = time.time()
MECH = Path("/home/claude/work/mechanical")
OUT = MECH / "v352/jfwd/jf1b_loctite_v352_v1.json"
ROWS7 = MECH / "v352/jfwd/jfwd_in718_rows_v352_v7.json"
CELLS = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352/jfwd_interim/js5_mu0_T3750_g078_cells.json")
JS5 = Path("/home/claude/work/fea3d/jfwd/runs/js5_mu0_T3750_g078")
SAX = MECH / "runs/structural/L1_thv352_NF2b_GVLO_r10free_cad352"
HIST = MECH / "v352/tb70/hist"
TH_GVLO = "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO"
R4 = {"GVLO": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO", MECH / "runs/structural/L1_thv352_NF2b_R4_GVLO_r10free_cad352r4_eh0p1"),
      "GVHI": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI", MECH / "runs/structural/L1_thv352_NF2b_R4_GVHI_r10free_cad352r4_eh0p1")}
BPKG = MECH / "v352/bpkg/bpkg_abort_v352_v1.json"
EXPECT = {str(ROWS7): "6113d28b64d0dba5", str(CELLS): "f9ed41727b0d4a46", str(JS5 / "post.json"): "0a7a6a6f678957f7",
          str(JS5 / "meta.json"): "782bb37c280f9efa", str(SAX / "mesh.npz"): "c1b81a9aea53d395",
          str(SAX / "B1_70.7/res.npz"): "5d0783af6cdf0a94", str(SAX / "B1_51.7/res.npz"): "a11bec10dbc54cf7",
          str(HIST / f"{TH_GVLO}_hist.npz"): "1c083a6c9246abb8", str(HIST / f"{R4['GVLO'][0]}_hist.npz"): "b51e5672fb41058e",
          str(HIST / f"{R4['GVHI'][0]}_hist.npz"): "e525fa1ad783b7de", str(R4["GVLO"][1] / "TB_a150/run.json"): "8511f3049b5dc1b0",
          str(R4["GVHI"][1] / "TB_a150/run.json"): "7aa967e846fd2ab0"}
# drawn / ruled geometry (sources in the docstring)
R_FLAT, T_SPR_MIN, L_MAX = 31.313, 0.44, 10.8
R_TIP = R_FLAT + T_SPR_MIN - L_MAX                         # 20.953
DE_MAX, DI, DK_MAX, D_SCREW = 10.0, 5.2, 9.5, 5.0
AX, TAN = 0.3705, 0.557                                    # F4 axial basis; full-float tangential basis
LIM = 150.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def t_above(t, T, thr):                                    # as tf1_exposure_v352.py (linear crossing interpolation)
    tot = 0.0
    for k in range(len(t) - 1):
        a, b, dt = T[k] - thr, T[k + 1] - thr, t[k + 1] - t[k]
        if a >= 0 and b >= 0:
            tot += dt
        elif a >= 0 > b:
            tot += dt * a / (a - b)
        elif a < 0 <= b:
            tot += dt * b / (b - a)
    return tot


for p, s16 in EXPECT.items():
    assert sha(p) == s16, (p, sha(p), s16)

# ---- zone sample points (y tangential, dz axial, on the flat) -------------------------------------------------------------------------
def annulus(ro, ri, n_r=9, n_a=360):
    pts = []
    for rr in np.linspace(ri, ro, n_r):
        for a in np.linspace(0.0, 2 * math.pi, n_a, endpoint=False):
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return np.array(pts)


OFFS = [(sy * TAN, sz * AX) for sy in (-1, 0, 1) for sz in (-1, 0, 1)]
HALF_CHORD = 4.6633                                        # worst-stack flat after the 0.1 flat-to-OD break (rows v7): no contact beyond
SPRING = np.vstack([annulus(DE_MAX / 2, DI / 2) + np.array(o) for o in OFFS])          # (y, dz)
SPRING = SPRING[np.abs(SPRING[:, 0]) <= HALF_CHORD]
HEAD = np.vstack([annulus(DK_MAX / 2, 0.0) + np.array(o) for o in OFFS])
SHANK_DZ = np.linspace(-(D_SCREW / 2 + AX), D_SCREW / 2 + AX, 41)                       # through the TC-01 wall and in the TC-02 tap


class Field:
    """quadratic CAX6 interpolation of a nodal field on the elements of one part (S-AX mesh)"""
    def __init__(self, X, E, sel):
        self.X, self.E = X, E[sel]
        c = X[self.E[:, :3]]
        self.c = c
        self.lo, self.hi = c.min(axis=1), c.max(axis=1)

    def __call__(self, T, P):
        out = np.full(len(P), np.nan)
        for j, (r, z) in enumerate(P):
            cand = np.where((self.lo[:, 0] <= r + 1e-9) & (self.hi[:, 0] >= r - 1e-9) & (self.lo[:, 1] <= z + 1e-9) & (self.hi[:, 1] >= z - 1e-9))[0]
            for e in cand:
                (x1, y1), (x2, y2), (x3, y3) = self.c[e]
                d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
                L1 = ((y2 - y3) * (r - x3) + (x3 - x2) * (z - y3)) / d
                L2 = ((y3 - y1) * (r - x3) + (x1 - x3) * (z - y3)) / d
                L3 = 1.0 - L1 - L2
                if min(L1, L2, L3) >= -1e-9:
                    N = np.array([L1 * (2 * L1 - 1), L2 * (2 * L2 - 1), L3 * (2 * L3 - 1), 4 * L1 * L2, 4 * L2 * L3, 4 * L3 * L1])
                    out[j] = float(N @ T[self.E[e]])
                    break
        return out


def flat_rz(YZ, z_row):
    return np.column_stack([np.sqrt(R_FLAT ** 2 + YZ[:, 0] ** 2), z_row + YZ[:, 1]])


rec = {"id": "jf1b_loctite_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": [{"path": p, "sha256_16": s} for p, s in EXPECT.items()],
       "geometry": {"r_flat_mm": R_FLAT, "screw_tip_r_mm": round(R_TIP, 3), "spring_De_max_Di_mm": [DE_MAX, DI], "head_dk_max_mm": DK_MAX,
                    "screw_d_mm": D_SCREW, "axial_offset_F4_mm": AX, "tangential_offset_full_float_mm": TAN,
                    "z_row": "TC-01 forward end - 12.000 in each model's own frame"}}

# ---- (1) the states rows v7 used, and FEA3D's records of them ---------------------------------------------------------------------------
rows7 = json.loads(ROWS7.read_text())
rows7_txt = ROWS7.read_text()
meta = json.loads((JS5 / "meta.json").read_text())
post = json.loads((JS5 / "post.json").read_text())
assert list(rows7["states"]) == ["PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S"]
assert all(k not in rows7_txt for k in ("TB_a", "\"TB\"", "abort", "B1_"))
st_used = {}
for stn in rows7["states"]:
    sd = meta["step_defs"].get(stn)
    ps = post["steps"].get(stn, {})
    st_used[stn] = {"kind_in_rows_v7": rows7["states"][stn].get("kind"),
                    "thermal_definition_js5": (sd[2] if sd else "PRELOAD 20 C (assembly)"),
                    "fea3d_js5_record": {"SCREW_node_set": ps.get("mapped_T", {}).get("SCREW"),
                                         "screw_T_shank_max_C": ps.get("screw", {}).get("T_shank_max_C"),
                                         "TC01_band_T_C": ps.get("TC-01", {}).get("band", {}).get("T_C"),
                                         "TC01_all_T_C": ps.get("TC-01", {}).get("all", {}).get("T_C"),
                                         "TC02_thread_T_C": ps.get("screw_check", {}).get("TC02_thread", {}).get("T02_C")}}
rec["states_rows_v7_used"] = st_used
rec["abort_TB_states_in_rows_v7"] = "none (no TB, abort or B1_ key in jfwd_in718_rows_v352_v7.json; its five states are listed above)"

# ---- (2) the S-AX state fields over the zone ----------------------------------------------------------------------------------------------
ms = np.load(SAX / "mesh.npz", allow_pickle=False)
X, E, pn = ms["X"], ms["E"], ms["pn"]
n1 = np.unique(E[pn == "ENG-TC-01"].ravel())
n2 = np.unique(E[pn == "ENG-TC-02"].ravel())
zf_sax = float(X[n1, 1].max())
zr_sax = zf_sax - 12.0
F1, F2 = Field(X, E, pn == "ENG-TC-01"), Field(X, E, pn == "ENG-TC-02")
near = n1[(np.abs(X[n1, 1] - zr_sax) <= 8.0)]
od = near[np.abs(X[near, 0] - X[n1, 0].max()) < 1e-6]
od = od[np.argsort(X[od, 1])]
zone = {}
for stn, key in (("SOAK70", "B1_70.7"), ("SOAK52", "B1_51.7")):
    T = np.load(SAX / key / "res.npz", allow_pickle=False)["T"] - 273.15
    sp = F1(T, flat_rz(SPRING, zr_sax))
    hd = np.interp(zr_sax + HEAD[:, 1], X[od, 1], T[od])              # head: the TC-01 OD value at its z
    sh_rz = np.array([(r, zr_sax + d) for r in np.linspace(28.7, 31.3, 14) for d in SHANK_DZ])
    sh = F1(T, sh_rz)
    tc02 = X[n2]
    rmax02 = float(tc02[np.abs(tc02[:, 1] - zr_sax) <= 3.0, 0].max())
    th_rz = np.array([(r, zr_sax + d) for r in np.linspace(R_TIP, rmax02 - 1e-6, 30) for d in SHANK_DZ])
    th = F2(T, th_rz)
    n_nan = {"spring": int(np.isnan(sp).sum()), "shank": int(np.isnan(sh).sum()), "thread": int(np.isnan(th).sum())}
    assert n_nan["spring"] == 0 and n_nan["shank"] == 0, n_nan
    j = int(np.nanargmax(sp))
    zone[stn] = {"field": f"S-AX GVLO {key} ({SAX.name}/{key}/res.npz)",
                 "spring_footprint_on_TC01_flat_max_C": round(float(sp.max()), 2),
                 "at_y_dz_mm": [round(float(SPRING[j, 0]), 3), round(float(SPRING[j, 1]), 3)],
                 "head_max_C": round(float(hd.max()), 2), "shank_in_TC01_wall_max_C": round(float(sh.max()), 2),
                 "thread_in_TC02_tap_max_C": round(float(np.nanmax(th)), 2), "thread_in_TC02_tap_min_C": round(float(np.nanmin(th)), 2),
                 "points_outside_the_part_mesh": n_nan,
                 "zone_max_C": round(float(max(sp.max(), hd.max(), sh.max(), np.nanmax(th))), 2),
                 "TC02_OD_at_row_mm": round(rmax02, 3)}
zone["SOAK"] = {"field": "uniform (js5 step_defs: 'soak 64.7 s GVLO row means')", "zone_max_C": 158.0,
                "TC01_C": 158.0, "SCREW_C": 127.0, "TC02_C": 96.0}
zone["PRELOAD"] = {"zone_max_C": 20.0}
zone["FA1S"] = {"zone_max_C": 45.6, "note": "FA-1 state, not a soak or TB state"}
rec["zone_temperatures_by_state"] = zone
soak = {k: zone[k]["zone_max_C"] for k in ("SOAK70", "SOAK", "SOAK52")}
gov = max(soak, key=soak.get)
js5_screw = {k: (st_used[k]["fea3d_js5_record"]["SCREW_node_set"] or {}).get("T_max_C") for k in ("SOAK70", "SOAK52")}
T_gov = max(soak[gov], max(v for v in js5_screw.values() if v is not None))

# ---- (3) the B1 history behind the governing state (computed time above) ------------------------------------------------------------------
z = np.load(HIST / f"{TH_GVLO}_hist.npz", allow_pickle=False)
info = json.loads(str(z["info"]))
t = z["t_s"].astype(float)
Xh, Th = z["X_TC01"], z["T_TC01"].astype(float) - 273.15
zf_th = float(Xh[:, 1].max())
zr_th = zf_th - 12.0
dzf = zf_th - zf_sax
loc = np.where(np.abs(Xh[:, 1] - zr_th) <= 9.0)[0]
tri = Delaunay(Xh[loc])
P = flat_rz(SPRING, zr_th)
s_ = tri.find_simplex(P)
assert (s_ >= 0).all()
Tm = tri.transform[s_]
b = np.einsum("ijk,ik->ij", Tm[:, :2], P - Tm[:, 2])
W = np.column_stack([b, 1 - b.sum(axis=1)])
V = loc[tri.simplices[s_]]
curve_spring = np.einsum("ij,tij->ti", W, Th[:, V]).max(axis=1)
odh = loc[np.abs(Xh[loc, 0] - Xh[:, 0].max()) < 1e-6]
odh = odh[np.argsort(Xh[odh, 1])]
curve_head = np.array([np.interp(zr_th + HEAD[:, 1], Xh[odh, 1], Th[k, odh]).max() for k in range(len(t))])
curve = np.maximum(curve_spring, curve_head)
k70 = int(np.argmin(np.abs(t - 70.651)))
k52 = int(np.argmin(np.abs(t - 51.651)))
k64 = int(np.argmin(np.abs(t - 64.651)))
km = int(np.argmax(curve))
hist = {"thermal_run": TH_GVLO, "frd_sha256_16": info.get("frd_sha256_16"), "frames": len(t), "dz_frame_thermal_minus_sax_mm": round(dzf, 3),
        "zone_curve": "max over the spring footprint (flat) and the head (TC-01 OD at its z) per frame",
        "at_B1_70.7_frame_C": round(float(curve[k70]), 2), "at_B1_51.7_frame_C": round(float(curve[k52]), 2),
        "at_64.65_s_frame_C": round(float(curve[k64]), 2), "history_max_C": round(float(curve[km]), 2),
        "t_of_history_max_s": round(float(t[km]), 2),
        "t_above_s": {f"{x:g}C": round(t_above(t, curve, x), 1) for x in (150.0, 155.0, 160.0, 165.0, 170.0)}}
rec["B1_history_GVLO_NF2b"] = hist

peak_raw = max(160.0, T_gov + 10.0)
peak = 5.0 * math.ceil(peak_raw / 5.0 - 1e-12)
dwell = t_above(t, curve, peak - 10.0)
rec["J_F1b"] = {
    "rule": ("lead 19:53:27Z (4): Peak = max(160 C, the highest J-FWD spring/screw-zone temperature in any soak or abort TB state that rows "
             "v7 used, + 10 C), rounded up to the next 5 C; dwell at peak at least that state's computed time above (peak - 10 C)"),
    "governing_state": gov, "governing_field": zone[gov].get("field"),
    "governing_location": ("HW-170 spring outer rim on the TC-01 flat, aft side (De 10.0 max, F4 axial offset 0.3705 aft), "
                           f"(y, dz) = {zone[gov].get('at_y_dz_mm')} mm from the hole axis"),
    "T_zone_max_C": round(T_gov, 2),
    "js5_SCREW_node_set_max_C": js5_screw,
    "peak_raw_C": round(peak_raw, 2), "peak_C": peak,
    "dwell_min_s": round(dwell, 1),
    "dwell_basis": f"time above {peak - 10.0:g} C of the zone curve in the B1 GVLO history (the thermal run behind {gov})",
    "sensitivity": {
        "zone = js5 SCREW node set only (159.8 C at SOAK70)": {"peak_C": 5.0 * math.ceil(max(160.0, 159.8 + 10.0) / 5.0 - 1e-12),
                                                                "dwell_min_s": round(t_above(t, curve_head, 160.0), 1),
                                                                "dwell_basis": "time above 160 C of the head curve"},
        "spring centred (no F4 offset)": "see zone_centred_C"},
    "purpose_now": ("J-F1b now checks one fresh single-use J-FWD joint (new IN718 screw, new HW-170 spring, LOCTITE 243, J-F1 torque) "
                    "through the hottest soak the rows assume: residual preload, breakaway torque and the spring / locker condition after "
                    "the cycle; its replacement-interval purpose is superseded by the single-use rule (lead 19:53:27Z (4))")}
# spring centred, for the record
spc = np.vstack([annulus(DE_MAX / 2, DI / 2) + np.array((sy * TAN, 0.0)) for sy in (-1, 0, 1)])
spc = spc[np.abs(spc[:, 0]) <= HALF_CHORD]
Tc = np.load(SAX / "B1_70.7/res.npz", allow_pickle=False)["T"] - 273.15
rec["J_F1b"]["zone_centred_C"] = {"spring_footprint_max_C_SOAK70_no_axial_offset": round(float(F1(Tc, flat_rz(spc, zr_sax)).max()), 2)}

# ---- LOCTITE 243 tap zone at the abort TB states (A = 150 C), both bounds -----------------------------------------------------------------
bp = json.loads(BPKG.read_text())


def find(x, key):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == key:
                return v
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(x, list):
        for v in x:
            r = find(v, key)
            if r is not None:
                return r
    return None


loc_rec = {}
for bd, (lab, run) in R4.items():
    zz = np.load(HIST / f"{lab}_hist.npz", allow_pickle=False)
    tt = zz["t_s"].astype(float)
    i_eob = int(np.argmin(np.abs(tt - 21.651)))
    X1, T1 = zz["X_TC01"], zz["T_TC01"].astype(float) - 273.15
    X2, T2 = zz["X_TC02"], zz["T_TC02"].astype(float) - 273.15
    zr = float(X1[:, 1].max()) - 12.0
    rj = json.loads((run / "TB_a150/run.json").read_text())
    shift = float(find(rj, "shift_K"))
    band = np.abs(X2[:, 1] - zr) <= (D_SCREW / 2 + AX)
    r_od2 = float(X2[band, 0].max())
    tap = band & (X2[:, 0] >= R_TIP)
    tap_eob = T2[i_eob, tap]
    jtap = int(np.argmax(tap_eob))
    idx = np.where(tap)[0][jtap]
    tap_hist = T2[:, tap].max(axis=1) + shift
    wide = (np.abs(X2[:, 1] - zr) <= 2.75)
    # J-FWD spring / screw zone at the TB_a150 field (information: rows v7 used no TB state)
    jz = np.abs(X1[:, 1] - zr) <= (DE_MAX / 2 + AX)
    tc02_bpkg = bp["global_sax_rows"][bd]["TB70"]["TB_a150"]["parts"]["ENG-TC-02"]["T_part_max_C"]
    loc_rec[bd] = {
        "thermal_run": lab, "TB_a150_run_json": str(run / "TB_a150/run.json"), "shift_K": round(shift, 3),
        "end_of_burn_frame_s": round(float(tt[i_eob]), 3),
        "TC02_part_max_TB_a150_C": round(float(T2[i_eob].max() + shift), 1),
        "TC02_part_max_bpkg_S-AX_C": tc02_bpkg,
        "tap_zone": f"TC-02 thermal nodes |dz| <= {D_SCREW / 2 + AX:.4f} mm of the hole row, r {R_TIP:.3f} to the TC-02 OD {r_od2:.3f}",
        "n_tap_nodes": int(tap.sum()),
        "TB_a150_tap_zone_max_C": round(float(tap_eob.max() + shift), 1),
        "TB_a150_tap_zone_min_C": round(float(tap_eob.min() + shift), 1),
        "at_r_dz_mm": [round(float(X2[idx, 0]), 3), round(float(X2[idx, 1] - zr), 3)],
        "TB_a150_TC02_band_all_r_max_C": round(float(T2[i_eob, wide].max() + shift), 1),
        "TB_a150_jfwd_TC01_zone_max_C_info": round(float(T1[i_eob, jz].max() + shift), 1),
        "shifted_history_ASSUMED_info": {"tap_zone_max_C": round(float(tap_hist.max()), 1),
                                         "t_of_max_s": round(float(tt[int(np.argmax(tap_hist))]), 2),
                                         "t_above_150C_s": round(t_above(tt, tap_hist, 150.0), 1),
                                         "t_above_180C_s": round(t_above(tt, tap_hist, 180.0), 1),
                                         "jfwd_TC01_zone_max_C": round(float((T1[:, jz].max(axis=1) + shift).max()), 1)},
        "nominal_unshifted_tap_zone_max_C_info": round(float(T2[:, tap].max()), 1)}
rec["LOCTITE_243_tap_zone_TB_a150"] = loc_rec
rec["t_s"] = round(time.time() - T0, 1)
s = json.dumps(rec, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps({k: rec[k] for k in ("zone_temperatures_by_state", "B1_history_GVLO_NF2b", "J_F1b", "LOCTITE_243_tap_zone_TB_a150")}, indent=1))
