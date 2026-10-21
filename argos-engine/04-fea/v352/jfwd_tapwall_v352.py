"""TC-02 J-FWD tap wall to the torch passage: CALC row, v3 (lead 2026-10-21T08:05:00Z F5 and 08:39:41Z item 1; REV-COMB-4 R4-01, MAJOR,
closes on this row's publication).  Mechanical, 2026-10-21.  CALC on FEA3D SIM screw forces (rows v8) and SIM temperatures; DERIVED unless
tagged; SF 1.0 on Fty / Ftu (as the J-FWD rows and the FA-1 rule of CHANGELOG 176).  Not physical approval.  v1 6687d52e4c66f332 / json
bcb21243d57af998 kept as jfwd_tapwall_v352_v1.py; v2 b7d7aad6eacef440 / json 9f8849412d4419d7 (the file REV-COMB-4 read) kept as
jfwd_tapwall_v352_v2.py.

v3 (what changes; every number of v2 is reproduced and asserted equal to the v2 json):
 - R4-01 (a): the tap ligament's lowest local natural frequency, CALC on bounding beam-strip idealisations of the thin web between the M5
   tap bore and the d5.2 passage bore (web thickness = the three walls; spans 5.2 mm = the passage bore and 10.4 mm = twice it as the
   extreme; clamped and simply supported edges ASSUMED; Euler-Bernoulli with a -15 % shear / rotary-inertia allowance ASSUMED; AL6061-T6
   E(T) engmat LITERATURE-approx, rho 2700 LITERATURE) at the SOAK52 thread and the SOAK70 screw temperatures.
 - R4-01 (b): the passage effects NOT MODELLED, as the reviewer lists them.
 - R4-01 (c): the reviewer's correction text, verbatim, as the published P_torch statement.
 - The reviewer's final numbers (REVIEW-COMBUSTION-R4.md 2908321d7f75d439, r4_torch_passage.json 8cb4b0c80173b88d) are recorded beside
   the interim basis; the row is unchanged.

v2 (what changed against v1):
 - P_torch: the torch-passage pressure is the FA1S step 151.04 bar abs (15.104 MPa abs = FEA3D's FA1S = DLF 2.0 x the 75.519 FA-1 head
   peak; gauge 15.002675 MPa) applied UNIFORMLY over the passage at EVERY state of v1 (PRELOAD, SOAK70, SOAK, SOAK52, FA1S), both J-F1
   columns (3750 N governing, 4096 N information) and the three walls.  Basis [DERIVED by the reviewer on SIM inputs, REV-COMB-4 interim
   (e)]: a two-segment lossless duct (3 mm x 9.24 mm outlet + 5.2 mm x 48.6 mm passage, closed at the torch seat) driven by the 896 v2.4b
   head histories, c 150-1200 m/s: tap station max 129.9 bar abs (c 150), torch seat max 148.7, 0 of 896 above 151.04 at any station or
   c; the pressure rises monotonically from the face to the seat.  The uniform 151.04 therefore bounds every station of that model.  The
   102 bar abs rule value does NOT cover the passage (up to 48 of 896 above 102 at the tap station): the v1 rows at 75.5 / 90 / 102 bar abs
   are SUPERSEDED for the passage and are re-run on rows v8 as INFORMATION only.  The ligament (1.5-1.9 mm of AL6061-T6) is ASSUMED
   quasi-static under the passage pressure (its own period is far below the 0.842 ms minimum 10-90 % rise of the grid), so the peak
   passage pressure enters as a static load (DLF 1.0 on it, as v1).
 - Screw forces: rows v8 (af072cc2e70711ca, module 62fd8d590ade2875, the published basis: relax v8 on FEA3D-2 envelope v6 + the cD record;
   resultant-type inputs take every instance including cD, worst-of); v1 was on rows v7 (6113d28b64d0dba5); the governing forces move by
   <= 0.2 N (tabled).  Temperatures as v1 (js5 cells, TC-02 thread and screw per state).
 - The v1 json is read: every v1 case is reproduced from its own N, T and pressure with this script's formula (exact check) and the v1
   governing values are quoted beside.
 - The reviewer's own estimate (from the v1 linear terms sigma = sigma_thread + 2.208 x p_g: SOAK52 MS_y +0.67 at the thread T / +0.30 at
   the screw T; SOAK70 +0.275 at the screw T) is quoted as the REVIEWER'S, beside the row; the row is this run.

As v1 (unchanged):
Geometry (rev 5, config.V352_R5 stations: head top z 169.513, injector face z 103.513, J-FWD row z 127.513; parts_engine.py TC-02):
  M5-6H tap at az 18 (and 342), radial, from the plug OD r 28.6 to r 19.6 (drill 4.2 x 9.0, full thread 8.0); torch passage d 5.2 from
  (r 25, az 0, z 160.013) to (r 21.5, az 0, z 111.513) (+2.0 run-out).  The closest approach is recomputed here from the two axes and
  checked against the CAD check v2 (f) wall (1.906-1.922 from the M5 major, probe step 0.016).
  Wall t (lead F5 of 2026-10-20): 1.64 net at the ruled clocking +/-0.25 deg (index pin in the drill fixture): 1.906 - 0.376 x 0.25 (CAD
  (f): 0.188 per 0.5 deg) - 0.1765 (hole position 0.05 + tap-to-hole 0.0485 + registration 0.078); 1.54 at +/-0.5 deg (information);
  1.906 nominal (information).
Loads:
  thread radial (wedging) load of the 60 deg ISO thread: F_r = N tan 30 deg (frictionless upper bound), spread uniformly over the engaged
  length on the pitch cylinder: p_t = F_r / (pi D2_min L_e), D2_min 4.480 (M5-6H), L_e 7.294 (THE ROW, route (i)) (ASSUMED uniform: the
  closest approach sits about 0.2-0.6 mm above the screw tip, in the last engaged thread, which in tension carries less than the average:
  TO-VERIFY); N = the IN718 screw force at the 3750 N J-F1 cap (GOVERNING; 4096 N information) per state and instance (the largest).
  The tap hole is at ambient (dry side of the TC-01 / TC-02 seals: ASSUMED).
  Combination (bounding, not simultaneous by the timeline): each state's screw force with the passage pressure (a relight pulse on a warm
  joint for the soak states).
Model (CALC, ASSUMED conservative): the ligament as the thin side of each hole, Lame hoop at the bore with the outer radius = bore + t:
  sigma = p_t L(2.5, t) + p_g L(2.6, t), L(a, t) = ((a + t)^2 + a^2) / ((a + t)^2 - a^2); the two hoop stresses are near-perpendicular at the
  crossing of a radial tap and a near-axial passage, and adding them bounds the von Mises of the biaxial state.  The FA-1 shear V on the
  screw bears on the tap in the engine-axial direction, perpendicular to the ligament: not added (the bearing row is rows v8 FA1S_tap_bearing).
Material: AL6061-T6 Fty / Ftu (engmat) at FEA3D's TC-02 thread temperature per state; sensitivity at the screw temperature (hotter)."""
import importlib.util, json, math, hashlib, time
from pathlib import Path
import numpy as np

T0 = time.time()
J = Path("/home/claude/work/mechanical/v352/jfwd")
HUB = Path("/home/claude/work/shared-fallback/engine/04-fea/v352")
OUT = J / "jfwd_tapwall_v352_v3.json"
ROWS_PY, ROWS8J = J / "jfwd_in718_rows_v352.py", J / "jfwd_in718_rows_v352_v8.json"
V1J = J / "jfwd_tapwall_v352_v1.json"
V2J, V2PY = J / "jfwd_tapwall_v352_v2.json", J / "jfwd_tapwall_v352_v2.py"
R4 = Path("/home/claude/work/shared-fallback/engine/reviews")
R4_REVIEW, R4_TORCH = R4 / "REVIEW-COMBUSTION-R4.md", R4 / "combustion/r4/r4_torch_passage.json"
CK5 = Path("/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v2.json")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
assert sha(ROWS_PY) == "62fd8d590ade2875" and sha(ROWS8J) == "af072cc2e70711ca" and sha(CK5) == "32c41e1e207f9d64" and sha(V1J) == "bcb21243d57af998"
assert sha(HUB / "jfwd_in718_rows_v352.py") == sha(ROWS_PY) and sha(HUB / "jfwd_in718_rows_v352_v8.json") == sha(ROWS8J)   # = the published rows v8
assert sha(HUB / "jfwd_tapwall_v352_v1.json") == sha(V1J)
assert sha(V2J) == "9f8849412d4419d7" and sha(V2PY) == "b7d7aad6eacef440"                     # the reviewed v2 row and its script
assert sha(R4_REVIEW) == "2908321d7f75d439" and sha(R4_TORCH) == "8cb4b0c80173b88d"            # REV-COMB-4 final (lead 08:39:41Z)
v2 = json.loads(V2J.read_text())
_sw = importlib.util.spec_from_file_location("jfwd_in718_rows_v352_v8", str(ROWS_PY))
W = importlib.util.module_from_spec(_sw)
_sw.loader.exec_module(W)
R = W.R
assert "v8 (v7 880ffe58c8af05e6" in W.__doc__
ck = json.loads(CK5.read_text())
v1 = json.loads(V1J.read_text())
rows8 = json.loads(ROWS8J.read_text())
assert abs(ck["S"]["bolt_z_fwd"] - 127.51342601773104) < 1e-9 and abs(ck["S"]["inj_face"] - 103.51342601773104) < 1e-9

# ---- geometry: closest approach of the tap axis (az 18) and the torch passage axis (az 0) (as v1; asserted equal to v1)
ZT, ZF, ZB = 169.51342601773104, 103.51342601773104, ck["S"]["bolt_z_fwd"]


def polar(r, a, z=0.0):
    a = math.radians(a)
    return np.array([r * math.cos(a), r * math.sin(a), z])


P0, P1 = polar(25.0, 0.0, ZT - 9.5), polar(21.5, 0.0, ZF + 8.0)
vp = (P1 - P0) / np.linalg.norm(P1 - P0)
L_P = np.linalg.norm(P1 - P0) + 2.0
geo = {}
for az in (18.0, 342.0):
    best = None
    for r in np.linspace(19.6, 28.6, 9001):
        q = polar(r, az, ZB)
        s = float(np.clip(np.dot(q - P0, vp), 0.0, L_P))
        d = float(np.linalg.norm(q - (P0 + s * vp)))
        if best is None or d < best[0]:
            best = (d, r, s)
    d, r, s = best
    geo[f"az{az:.0f}"] = {"axis_distance_mm": round(d, 4), "wall_from_M5_major_to_d5.2_mm": round(d - 2.5 - 2.6, 4), "at_tap_r_mm": round(r, 3),
                          "depth_below_plug_OD_mm": round(28.6 - r, 3), "passage_z_mm": round(float((P0 + s * vp)[2]), 3)}
W_PAPER = geo["az18"]["wall_from_M5_major_to_d5.2_mm"]
assert abs(W_PAPER - 1.914) < 0.02, W_PAPER                          # CAD check v2 (f): 1.906-1.922 (probe step 0.016)
W_NOM = 1.906
NET = 0.05 + 0.0485 + 0.078
WALLS = {"ruled_+/-0.25deg_net_GOVERNING": round(W_NOM - 0.376 * 0.25 - NET, 4), "+/-0.5deg_net_info": round(W_NOM - 0.376 * 0.5 - NET, 4),
         "nominal_CAD_info": W_NOM}
assert abs(WALLS["ruled_+/-0.25deg_net_GOVERNING"] - 1.64) < 0.005 and abs(WALLS["+/-0.5deg_net_info"] - 1.54) < 0.005
tip_r = {"deepest (L max, t min, wall min, gap 0)": 28.6 - (10.8 - 0.44 - 2.665 - 0.0), "shallowest (L min, t max, wall max, gap 0.078)": 28.6 - (10.6 - 0.52 - 2.708 - 0.078)}
geo["screw_tip_r_mm"] = {k: round(v, 3) for k, v in tip_r.items()}
geo["closest_approach_above_tip_mm"] = {k: round(geo["az18"]["at_tap_r_mm"] - v, 3) for k, v in tip_r.items()}
assert geo == v1["geometry"] and WALLS == v1["walls_mm"], "geometry / walls differ from v1"

# ---- loads
D2, L_E = 4.480, W.THE_ROW["L_e_gap_bound_mm"]
assert abs(L_E - 7.294) < 1e-6 and abs(L_E - v1["inputs"]["L_e_mm"]) < 1e-9 and D2 == v1["inputs"]["D2_min_mm"]
TAN30 = math.tan(math.radians(30.0))
P_ATM = 0.101325
P_FA1_PEAK, DLF = 75.519, 2.0                                         # lc_tb70_envelope v1 Z3 ceiling (sax.py FA1) and the FA1S DLF
P_TORCH_FA1S_ABS_MPA = 15.104                                         # FEA3D FA1S step (151.04 bar abs = 2.0 x 75.52)
assert abs(DLF * P_FA1_PEAK / 10.0 - P_TORCH_FA1S_ABS_MPA) < 0.001
PK_V2 = "P_torch_FA1S_151.04bar_abs_uniform"
PRESS_V1 = v1["inputs"]["pressures_gauge_MPa"]
PRESS = dict(PRESS_V1)
PRESS[PK_V2] = P_TORCH_FA1S_ABS_MPA - P_ATM
assert abs(PRESS[PK_V2] - PRESS_V1["FE_FA1S_15.104MPa_info"]) < 1e-12
REVIEWER = {"source": "REV-COMB-4 interim 2026-10-21T07:52:49Z item (e), handback text sha256/16 d88da047a6652181 (DERIVED by the reviewer on SIM inputs)",
            "duct_model": "two-segment lossless duct (3 mm x 9.24 mm outlet + 5.2 mm x 48.6 mm passage, closed at the torch seat), 896 v2.4b head histories, c 150-1200 m/s",
            "tap_station_max_bar_abs": {"c150": 129.9, "c181": 122.0, "c222": 108.0, "c250-1200": [89.5, 118.5]},
            "tap_station_cases_above_102_of_896_max": 48, "torch_seat_max_bar_abs": {"c150": 148.7, "c181": 129.8},
            "cases_above_151.04_of_896": 0, "MEOP_case": "passage dead-ended: uniform at Pc, at most 45 bar abs", "torch_run": "about 3 bar abs in the torch body",
            "estimate_from_v1_linear_terms": {"formula": "sigma = sigma_thread + 2.208 x p_g", "SOAK52_MS_y_thread_T": 0.67, "SOAK52_MS_y_screw_T": 0.30,
                                              "SOAK70_MS_y_screw_T": 0.275, "tag": "the REVIEWER'S estimate (DERIVED by the reviewer), not this row"}}


def Lame(a, t):
    b = a + t
    return (b * b + a * a) / (b * b - a * a)


def screw_forces(FV):
    out = {}
    for st in ("PRELOAD",) + tuple(R.SOAKS) + ("FA1S",):
        T2 = W.CELLS[st]["TC-02"]["thread_shear_An"]["T_C"]
        Ts = W.CELLS[st]["SCREW"]["T_C"]
        hs = R.H_at(st)
        j = max(hs, key=lambda h: W.n_in(st, h, FV))
        out[st] = {"N_IN718_N": round(W.n_in(st, j, FV), 1), "from": R.LABEL[j], "T_TC02_thread_C": T2, "T_screw_C": Ts,
                   "instances": {R.LABEL[h]: round(W.n_in(st, h, FV), 1) for h in hs}}
    return out


def case(N, frm, T2, Ts, pg, t):
    pt = N * TAN30 / (math.pi * D2 * L_E)
    sig_t, sig_g = pt * Lame(2.5, t), pg * Lame(2.6, t)
    sig = sig_t + sig_g
    out = {"N_N": N, "from": frm, "p_thread_MPa": round(pt, 2), "p_passage_gauge_MPa": round(pg, 3), "wall_mm": t,
           "sigma_thread_MPa": round(sig_t, 1), "sigma_passage_MPa": round(sig_g, 1), "sigma_MPa": round(sig, 1)}
    for tk, T in (("TC02_thread_T", T2), ("screw_T_sensitivity", Ts)):
        fty, ftu = R.tab("AL6061-T6", "Fty", T), R.tab("AL6061-T6", "Ftu", T)
        out[tk] = {"T_C": T, "Fty_MPa": round(fty, 1), "Ftu_MPa": round(ftu, 1), "MS_y": round(fty / sig - 1.0, 3), "MS_u": round(ftu / sig - 1.0, 3)}
    return out


# ---- reproduction of every v1 case from its own N, T and pressure (formula check, exact)
n_rep = 0
for FVk, blk in v1["rows"].items():
    for k, c in blk["cases"].items():
        st, pk, wk = k.split("|")
        f = blk["screw_forces"][st]
        rc = case(c["N_N"], c["from"], f["T_TC02_thread_C"], f["T_screw_C"], PRESS_V1[pk], v1["walls_mm"][wk])
        assert rc == c, (FVk, k, rc, c)
        n_rep += 1
assert n_rep == 126, n_rep

STATES = ("PRELOAD",) + tuple(R.SOAKS) + ("FA1S",)
assert STATES == ("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S")
V1_COMBOS = [("PRELOAD", "none"), ("PRELOAD", "MEOP_45bar_abs")] + [(st, pk) for st in R.SOAKS for pk in ("none", "MEOP_45bar_abs", "FA-1_pulse_75.5bar_abs",
             "FA-1_rule_90bar_abs_QS", "FA-1_rule_102bar_abs_0.25-1ms_parts")] + \
            [("FA1S", pk) for pk in ("FA-1_pulse_75.5bar_abs", "FA-1_rule_90bar_abs_QS", "FA-1_rule_102bar_abs_0.25-1ms_parts", "FE_FA1S_15.104MPa_info")]
FLAG = 0.05


def govern(cases):
    gk = [k for k in cases if k.endswith("GOVERNING")]
    jm = min(gk, key=lambda k: cases[k]["TC02_thread_T"]["MS_y"])
    js = min(gk, key=lambda k: cases[k]["screw_T_sensitivity"]["MS_y"])
    ju = min(gk, key=lambda k: cases[k]["TC02_thread_T"]["MS_u"])
    return {"case": jm, **cases[jm], "worst_with_screw_T_sensitivity": {"case": js, **cases[js]["screw_T_sensitivity"]},
            "lowest_MS_u_thread_T": {"case": ju, **cases[ju]["TC02_thread_T"]}}


res = {"id": "jfwd_tapwall_v352", "version": "v3", "date": "2026-10-21", "owner": "mechanical", "basis": __doc__.strip(),
       "status": "CALC on SIM; ASSUMED conservative ligament model; negatives SHOWN AS FOUND; not physical approval",
       "inputs": {"rows_v8_module": {"path": str(ROWS_PY), "sha256_16": sha(ROWS_PY), "hub_copy_identical": True},
                  "rows_v8_json": {"path": str(ROWS8J), "sha256_16": sha(ROWS8J), "hub_copy_identical": True},
                  "tapwall_v1_json": {"path": str(V1J), "sha256_16": sha(V1J)},
                  "cad_check_v2": {"path": str(CK5), "sha256_16": sha(CK5)}, "D2_min_mm": D2, "L_e_mm": L_E, "pressures_gauge_MPa": PRESS,
                  "P_torch_v2": {"abs_MPa": P_TORCH_FA1S_ABS_MPA, "gauge_MPa": round(PRESS[PK_V2], 6), "basis": "FA1S = DLF 2.0 x 75.519 bar abs (FEA3D FA1S step 15.104 MPa), uniform over the passage (lead F5)"},
                  "reviewer_basis": REVIEWER},
       "geometry": geo, "walls_mm": WALLS, "v1_reproduction": {"cases_reproduced_exactly": n_rep, "from": "each v1 case's own N, T, pressure and wall"},
       "rows": {}}
for FVk, FV in (("3750", 3750.0), ("4096", 4096.0)):
    SF_ = screw_forces(FV)
    dN = {st: round(SF_[st]["N_IN718_N"] - v1["rows"][FVk]["screw_forces"][st]["N_IN718_N"], 1) for st in STATES}
    for st in STATES:
        for kk in ("T_TC02_thread_C", "T_screw_C"):
            assert SF_[st][kk] == v1["rows"][FVk]["screw_forces"][st][kk], (st, kk)
    assert max(abs(x) for x in dN.values()) <= 0.25, dN
    blk = {"column": "GOVERNING (J-F1 cap)" if FVk == "3750" else "INFORMATION (superseded maximum)", "screw_forces_rows_v8": SF_,
           "dN_rows_v8_minus_v1_rows_v7_N": dN, "row_P_torch_FA1S": {}, "v1_pressure_set_on_rows_v8_info": {}}
    for st in STATES:
        f = SF_[st]
        for wk, t in WALLS.items():
            blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|{wk}"] = case(f["N_IN718_N"], f["from"], f["T_TC02_thread_C"], f["T_screw_C"], PRESS[PK_V2], t)
    for st, pk in V1_COMBOS:
        f = SF_[st]
        for wk, t in WALLS.items():
            c = case(f["N_IN718_N"], f["from"], f["T_TC02_thread_C"], f["T_screw_C"], PRESS[pk], t)
            if pk.startswith("FA-1_"):
                c["note"] = "SUPERSEDED for the passage (REV-COMB-4 (e): the FA-1 passage pressure exceeds 75.5 / 90 / 102 bar abs); information"
            blk["v1_pressure_set_on_rows_v8_info"][f"{st}|{pk}|{wk}"] = c
    blk["governing"] = govern(blk["row_P_torch_FA1S"])
    blk["per_state_GOVERNING_wall"] = {st: {"N_N": blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]["N_N"],
                                            "sigma_MPa": blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]["sigma_MPa"],
                                            "MS_y_thread_T": blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]["TC02_thread_T"]["MS_y"],
                                            "MS_u_thread_T": blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]["TC02_thread_T"]["MS_u"],
                                            "MS_y_screw_T": blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]["screw_T_sensitivity"]["MS_y"],
                                            "MS_u_screw_T": blk["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]["screw_T_sensitivity"]["MS_u"]}
                                       for st in STATES}
    blk["v1_governing_record"] = v1["rows"][FVk]["governing"]
    blk["flags_within_0.05_or_negative"] = sorted(k for k, c in blk["row_P_torch_FA1S"].items()
                                                  if min(c["TC02_thread_T"]["MS_y"], c["TC02_thread_T"]["MS_u"], c["screw_T_sensitivity"]["MS_y"], c["screw_T_sensitivity"]["MS_u"]) < FLAG)
    res["rows"][FVk] = blk
g = res["rows"]["3750"]["governing"]
gs = g["worst_with_screw_T_sensitivity"]
g1 = v1["rows"]["3750"]["governing"]
cmpr = {}
for st in ("SOAK52", "SOAK70"):
    c = res["rows"]["3750"]["row_P_torch_FA1S"][f"{st}|{PK_V2}|ruled_+/-0.25deg_net_GOVERNING"]
    cmpr[st] = {"this_row_MS_y_thread_T": c["TC02_thread_T"]["MS_y"], "this_row_MS_y_screw_T": c["screw_T_sensitivity"]["MS_y"]}
cmpr["reviewer_estimate"] = REVIEWER["estimate_from_v1_linear_terms"]
cmpr["Lame_passage_factor_governing_wall"] = round(Lame(2.6, WALLS["ruled_+/-0.25deg_net_GOVERNING"]), 4)
res["comparison_with_reviewer_estimate"] = cmpr
res["verdict"] = (f"Tap wall to the torch passage (az 18 / 342), wall {g['wall_mm']} mm net at +/-0.25 deg, CALC on SIM at the 3750 N J-F1 cap, "
                  f"P_torch = FA1S 151.04 bar abs uniform over the passage at every state: governing {g['case'].rsplit('|', 2)[0]} (N {g['N_N']} N "
                  f"from {g['from']}, p_thread {g['p_thread_MPa']} MPa, passage {g['p_passage_gauge_MPa']} MPa gauge): sigma {g['sigma_MPa']} MPa, "
                  f"MS_y {g['TC02_thread_T']['MS_y']:+.3f} / MS_u {g['TC02_thread_T']['MS_u']:+.3f} at the TC-02 thread temperature {g['TC02_thread_T']['T_C']} C; "
                  f"with the screw temperature as a sensitivity MS_y {gs['MS_y']:+.3f} ({gs['case'].rsplit('|', 2)[0]}, {gs['T_C']} C).  "
                  f"v1 (P_torch 102 bar abs, rows v7): MS_y {g1['TC02_thread_T']['MS_y']:+.3f} / screw T {g1['worst_with_screw_T_sensitivity']['MS_y']:+.3f}.  "
                  f"Flags within 0.05 or negative (3750 column, all walls): {len(res['rows']['3750']['flags_within_0.05_or_negative'])}; "
                  f"4096 information column: {len(res['rows']['4096']['flags_within_0.05_or_negative'])}.")
# ---- v3: every v2 block reproduced exactly (the row REV-COMB-4 read), then the R4-01 additions
_rt = lambda o: json.loads(json.dumps(o, default=float))
for kk in ("geometry", "walls_mm", "v1_reproduction", "rows", "comparison_with_reviewer_estimate", "verdict"):
    assert _rt(res[kk]) == v2[kk], kk
assert _rt(res["inputs"]) == v2["inputs"]
res["inputs"]["tapwall_v2_json_reviewed"] = {"path": str(V2J), "sha256_16": sha(V2J), "script": str(V2PY), "script_sha256_16": sha(V2PY),
                                             "note": "REV-COMB-4 read this file (R4-01); v3 reproduces its blocks exactly (asserted) and adds R4-01 (a)-(c)"}
res["inputs"]["REV-COMB-4_final"] = {"review": {"path": str(R4_REVIEW), "sha256_16": sha(R4_REVIEW)},
                                     "torch_passage": {"path": str(R4_TORCH), "sha256_16": sha(R4_TORCH)},
                                     "numbers_DERIVED_by_the_reviewer": {"tap_station_peak_bar_abs": {"c150": 129.85, "c181": 121.96, "c202": 116.61, "c222": 108.0},
                                                                         "tap_station_cases_above_102_of_896": {"c150": 48, "c181": 42, "c202": 36, "c222": 12, "c400-450": 22},
                                                                         "closed_seat_peak_bar_abs_max": 148.72, "cases_above_151.04_any_c_150-1200": 0},
                                     "R4-01_on_this_row": "the reviewer's linear-term estimate +0.671 / +0.787 / +0.295 / +0.275 against the row +0.670 / +0.785 / +0.294 / +0.275 (within 0.002); DLF 1.0 accepted without a separate finding (FA1S >= 16 % above the 129.85 linear tap peak, 24 % at c >= 181)"}
# R4-01 (a): lowest local natural frequency of the tap ligament (the thin web between the M5 tap bore and the d5.2 passage bore)
RHO_AL = 2700.0                                                       # engmat AL6061-T6 rho, LITERATURE
BETA2 = {"clamped-clamped": 4.730040744862704 ** 2, "simply_supported": math.pi ** 2}
SPANS = {"5.2_passage_bore": 5.2, "10.4_twice_the_passage_bore_EXTREME": 10.4}
TB_ALLOW = 0.85                                                       # shear-deformation / rotary-inertia allowance on Euler-Bernoulli (ASSUMED)
f3750 = res["rows"]["3750"]["screw_forces_rows_v8"]
T_SET = {"SOAK52_TC02_thread_T": f3750["SOAK52"]["T_TC02_thread_C"], "hottest_screw_T_of_all_states": max(f3750[st]["T_screw_C"] for st in STATES)}
lig = {}
for tk, T in T_SET.items():
    E = R.tab("AL6061-T6", "E", T) * 1e6
    for wk, t in WALLS.items():
        for sk, L in SPANS.items():
            for bk, b2 in BETA2.items():
                f = TB_ALLOW * b2 / (2.0 * math.pi) * (t * 1e-3) / (L * 1e-3) ** 2 * math.sqrt(E / (12.0 * RHO_AL))
                lig[f"{tk}|{wk}|{sk}|{bk}"] = {"T_C": T, "E_GPa": round(E / 1e9, 2), "t_mm": t, "span_mm": L, "f_kHz": round(f / 1e3, 1),
                                               "period_ms": round(1e3 / f, 4)}
kmin = min(lig, key=lambda k: lig[k]["f_kHz"])
k_rep = [k for k in lig if k.startswith("SOAK52_TC02_thread_T|ruled_+/-0.25deg_net_GOVERNING|5.2_passage_bore|")]
F_PASS_MAX_HZ = 1.0 / 0.29e-3                                         # shortest passage period 0.29 ms (REV-COMB-4 R4-01)
r_ = F_PASS_MAX_HZ / (lig[kmin]["f_kHz"] * 1e3)
res["R4-01_additions"] = {
    "(a)_ligament_lowest_local_natural_frequency": {
        "value": f"lowest local natural frequency >= {lig[kmin]['f_kHz']:.0f} kHz (period <= {lig[kmin]['period_ms']:.3f} ms) on the extreme bounding idealisation "
                 f"({kmin.replace('|', ', ')}); {min(lig[k]['f_kHz'] for k in k_rep):.0f}-{max(lig[k]['f_kHz'] for k in k_rep):.0f} kHz for the governing wall spanning the "
                 f"5.2 mm passage bore (simply supported / clamped) at the SOAK52 thread temperature",
        "tag": "CALC (Euler-Bernoulli beam strip, edge conditions and span ASSUMED, -15 % shear / rotary-inertia allowance ASSUMED; E engmat LITERATURE-approx, rho LITERATURE); "
               "the web is 1.54-1.91 mm thick and thickens to about +0.4 mm within +/-2.5 mm of the closest approach (two near-perpendicular bores), so the strip spans bound it from below; not an FE modal",
        "against_the_passage": {"shortest_passage_period_ms": 0.29, "passage_frequency_max_Hz": round(F_PASS_MAX_HZ, 0),
                                "ratio_passage_over_ligament_lowest": round(r_, 4), "harmonic_DLF_1_over_1_minus_r2": round(1.0 / (1.0 - r_ * r_), 4),
                                "verdict": "the ligament is quasi-static under the passage pressure: DLF 1.0 on the passage peak (as the row); the FA1S design case is >= 16 % above the linear tap peak (REV-COMB-4 R4-01)"},
        "cases": lig},
    "(b)_NOT_MODELLED": ["wave steepening and shock reflection", "losses", "torch-chamber compliance", "N2O decomposition", "a blocked-outlet deflagration"],
    "(b)_source": "REV-COMB-4 R4-01 'Residual, not modelled' (REVIEW-COMBUSTION-R4.md 2908321d7f75d439); these are outside the row's basis, not covered by it",
    "(c)_P_torch_statement_verbatim_REV-COMB-4": "P_torch during FA-1: design case FA1S 151.04 bar abs uniform over the passage (REV-COMB-4 R4-01); linear lossless passage peaks <= 129.9 bar abs at the J-FWD tap and <= 148.7 at the torch seat for c 150-1200 m/s; the band values 94 / 121 / 147 / 94 do not bound gas-filled passages."}
res["verdict"] = res["verdict"] + (f"  R4-01: ligament lowest local natural frequency >= {lig[kmin]['f_kHz']:.0f} kHz on the extreme bounding strip "
                                   f"(CALC, ASSUMED edges), far above the passage (<= {F_PASS_MAX_HZ / 1e3:.2f} kHz): DLF 1.0 on the passage peak; NOT MODELLED: "
                                   + ", ".join(res["R4-01_additions"]["(b)_NOT_MODELLED"]) + ".")
res["t_run_s"] = round(time.time() - T0, 1)
s = json.dumps(res, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], res["t_run_s"], "v1 cases reproduced", n_rep)
print(res["verdict"])
for FVk in ("3750", "4096"):
    b = res["rows"][FVk]
    print(FVk, "dN", json.dumps(b["dN_rows_v8_minus_v1_rows_v7_N"]))
    print("  forces", json.dumps({st: (b["screw_forces_rows_v8"][st]["N_IN718_N"], b["screw_forces_rows_v8"][st]["from"]) for st in STATES}))
    for k, v in b["row_P_torch_FA1S"].items():
        print("  ", k, v["N_N"], v["p_thread_MPa"], v["p_passage_gauge_MPa"], v["sigma_thread_MPa"], v["sigma_passage_MPa"], v["sigma_MPa"],
              v["TC02_thread_T"]["T_C"], v["TC02_thread_T"]["MS_y"], v["TC02_thread_T"]["MS_u"], v["screw_T_sensitivity"]["T_C"],
              v["screw_T_sensitivity"]["MS_y"], v["screw_T_sensitivity"]["MS_u"])
    print("  flags", b["flags_within_0.05_or_negative"])
print(json.dumps(res["comparison_with_reviewer_estimate"]))
print(json.dumps({k: v for k, v in res["R4-01_additions"]["(a)_ligament_lowest_local_natural_frequency"].items() if k != "cases"}))
