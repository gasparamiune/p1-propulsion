"""TC-02 J-FWD tap wall to the torch passage: CALC row (lead 17:55:55Z F5: 'Add a CALC tap-wall row in rev 5: thread radial load at the 3750 N
maximum plus the torch-passage pressure, including the 75 bar FA-1 pulse.').  Mechanical, 2026-10-20, v1.  CALC on FEA3D / rows v7 screw
forces and SIM temperatures; DERIVED unless tagged; SF 1.0 on Fty / Ftu (as the J-FWD rows and the FA-1 rule of CHANGELOG 176).

Geometry (rev 5, config.V352_R5 stations: head top z 169.513, injector face z 103.513, J-FWD row z 127.513; parts_engine.py TC-02):
  M5-6H tap at az 18 (and 342), radial, from the plug OD r 28.6 to r 19.6 (drill 4.2 x 9.0, full thread 8.0); torch passage d 5.2 from
  (r 25, az 0, z 160.013) to (r 21.5, az 0, z 111.513) (+2.0 run-out).  The closest approach is recomputed here from the two axes and
  checked against the CAD check v2 (f) wall (1.906-1.922 from the M5 major, probe step 0.016).
  Wall t (lead F5): 1.64 net at the ruled clocking +/-0.25 deg (index pin in the drill fixture): 1.906 - 0.376 x 0.25 (CAD (f): 0.188 per
  0.5 deg) - 0.1765 (hole position 0.05 + tap-to-hole 0.0485 + registration 0.078); 1.54 at +/-0.5 deg (information); 1.906 nominal (info).
Loads:
  thread radial (wedging) load of the 60 deg ISO thread: F_r = N tan 30 deg (frictionless upper bound), spread uniformly over the engaged
  length on the pitch cylinder: p_t = F_r / (pi D2_min L_e), D2_min 4.480 (M5-6H), L_e 7.294 (THE ROW, route (i)) (ASSUMED uniform: the
  closest approach sits about 0.4-0.7 mm above the screw tip, in the last engaged thread, which in tension carries less than the average:
  TO-VERIFY); N = the IN718 screw force of rows v7 at the 3750 N J-F1 cap (GOVERNING; 4096 N information) per state and history: PRELOAD,
  the soak states SOAK70 / SOAK / SOAK52 (the largest force), FA1S;
  torch-passage gauge pressure: chamber MEOP 45 bar abs (ENG-IG-02 check valves 'rated to chamber MEOP 45 bar'; the passage opens into the
  chamber: ASSUMED at chamber pressure, the torch's own P_torch TO-CONFIRM from Combustion); the FA-1 pulse 75.5 bar abs (the lead's '75
  bar', CHANGELOG 164 / 170); the FA-1 structural rule 90 bar abs quasi-static and 102 bar abs for the 0.25-1 ms parts (TC-02 head on its
  screws 0.27-0.39 ms, CHANGELOG 176); FEA3D's FA1S step (15.104 MPa = 2 x 75.5 bar abs) as information.  The tap hole is at ambient
  (dry side of the TC-01 / TC-02 seals: ASSUMED).
  Combination (bounding, not simultaneous by the timeline): the largest soak screw force with each passage pressure (a relight pulse on a
  warm joint); the FA1S screw force with the pulse pressures as information.
Model (CALC, ASSUMED conservative): the ligament as the thin side of each hole, Lame hoop at the bore with the outer radius = bore + t:
  sigma = p_t L(2.5, t) + p_g L(2.6, t), L(a, t) = ((a + t)^2 + a^2) / ((a + t)^2 - a^2); the two hoop stresses are near-perpendicular at the
  crossing of a radial tap and a near-axial passage, and adding them bounds the von Mises of the biaxial state.  The FA-1 shear V on the
  screw bears on the tap in the engine-axial direction, perpendicular to the ligament: not added (the bearing row is rows v7 FA1S_tap_bearing).
Material: AL6061-T6 Fty / Ftu (engmat) at FEA3D's TC-02 thread temperature per state; sensitivity at the screw temperature (hotter)."""
import importlib.util, json, math, hashlib, time
from pathlib import Path
import numpy as np

T0 = time.time()
J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_tapwall_v352_v1.json"
ROWS_PY, ROWS7J = J / "jfwd_in718_rows_v352.py", J / "jfwd_in718_rows_v352_v7.json"
CK5 = Path("/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v2.json")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
assert sha(ROWS_PY) == "880ffe58c8af05e6" and sha(ROWS7J) == "6113d28b64d0dba5" and sha(CK5) == "32c41e1e207f9d64"
_sw = importlib.util.spec_from_file_location("jfwd_in718_rows_v352_v7", str(ROWS_PY))
W = importlib.util.module_from_spec(_sw)
_sw.loader.exec_module(W)
R = W.R
ck = json.loads(CK5.read_text())
assert abs(ck["S"]["bolt_z_fwd"] - 127.51342601773104) < 1e-9 and abs(ck["S"]["inj_face"] - 103.51342601773104) < 1e-9

# ---- geometry: closest approach of the tap axis (az 18) and the torch passage axis (az 0)
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

# ---- screw tip vs the closest approach (route (i): L 10.7 +/-0.1 over spring A t 0.44-0.52; wall 2.665-2.708; gap 0-0.078)
tip_r = {"deepest (L max, t min, wall min, gap 0)": 28.6 - (10.8 - 0.44 - 2.665 - 0.0), "shallowest (L min, t max, wall max, gap 0.078)": 28.6 - (10.6 - 0.52 - 2.708 - 0.078)}
geo["screw_tip_r_mm"] = {k: round(v, 3) for k, v in tip_r.items()}
geo["closest_approach_above_tip_mm"] = {k: round(geo["az18"]["at_tap_r_mm"] - v, 3) for k, v in tip_r.items()}

# ---- loads
D2, L_E = 4.480, W.THE_ROW["L_e_gap_bound_mm"]
assert abs(L_E - 7.294) < 1e-6
TAN30 = math.tan(math.radians(30.0))
P_ATM = 0.101325
PRESS = {"none": 0.0, "MEOP_45bar_abs": 4.5 - P_ATM, "FA-1_pulse_75.5bar_abs": 7.55 - P_ATM, "FA-1_rule_90bar_abs_QS": 9.0 - P_ATM,
         "FA-1_rule_102bar_abs_0.25-1ms_parts": 10.2 - P_ATM, "FE_FA1S_15.104MPa_info": 15.104 - P_ATM}


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
        out[st] = {"N_IN718_N": round(W.n_in(st, j, FV), 1), "from": R.LABEL[j], "T_TC02_thread_C": T2, "T_screw_C": Ts}
    return out


res = {"id": "jfwd_tapwall_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "status": "CALC; ASSUMED conservative ligament model; negatives SHOWN AS FOUND",
       "inputs": {"rows_v7_module": {"path": str(ROWS_PY), "sha256_16": sha(ROWS_PY)}, "rows_v7_json": {"path": str(ROWS7J), "sha256_16": sha(ROWS7J)},
                  "cad_check_v2": {"path": str(CK5), "sha256_16": sha(CK5)}, "D2_min_mm": D2, "L_e_mm": L_E, "pressures_gauge_MPa": PRESS},
       "geometry": geo, "walls_mm": WALLS, "rows": {}}
for FVk, FV in (("3750", 3750.0), ("4096", 4096.0)):
    SF_ = screw_forces(FV)
    res["rows"][FVk] = {"column": "GOVERNING (J-F1 cap)" if FVk == "3750" else "INFORMATION (superseded maximum)", "screw_forces": SF_, "cases": {}}
    soak_max = max(R.SOAKS, key=lambda st: SF_[st]["N_IN718_N"])
    combos = [("PRELOAD", "none"), ("PRELOAD", "MEOP_45bar_abs")] + [(st, pk) for st in R.SOAKS for pk in ("none", "MEOP_45bar_abs", "FA-1_pulse_75.5bar_abs",
                                                                                                         "FA-1_rule_90bar_abs_QS", "FA-1_rule_102bar_abs_0.25-1ms_parts")] + \
             [("FA1S", pk) for pk in ("FA-1_pulse_75.5bar_abs", "FA-1_rule_90bar_abs_QS", "FA-1_rule_102bar_abs_0.25-1ms_parts", "FE_FA1S_15.104MPa_info")]
    for st, pk in combos:
        f = SF_[st]
        N = f["N_IN718_N"]
        pt = N * TAN30 / (math.pi * D2 * L_E)
        pg = PRESS[pk]
        for wk, t in WALLS.items():
            sig_t, sig_g = pt * Lame(2.5, t), pg * Lame(2.6, t)
            sig = sig_t + sig_g
            out = {"N_N": N, "from": f["from"], "p_thread_MPa": round(pt, 2), "p_passage_gauge_MPa": round(pg, 3), "wall_mm": t,
                   "sigma_thread_MPa": round(sig_t, 1), "sigma_passage_MPa": round(sig_g, 1), "sigma_MPa": round(sig, 1)}
            for tk, T in (("TC02_thread_T", f["T_TC02_thread_C"]), ("screw_T_sensitivity", f["T_screw_C"])):
                fty, ftu = R.tab("AL6061-T6", "Fty", T), R.tab("AL6061-T6", "Ftu", T)
                out[tk] = {"T_C": T, "Fty_MPa": round(fty, 1), "Ftu_MPa": round(ftu, 1), "MS_y": round(fty / sig - 1.0, 3), "MS_u": round(ftu / sig - 1.0, 3)}
            res["rows"][FVk]["cases"][f"{st}|{pk}|{wk}"] = out
    gk = [k for k in res["rows"][FVk]["cases"] if k.endswith("GOVERNING")]
    jm = min(gk, key=lambda k: res["rows"][FVk]["cases"][k]["TC02_thread_T"]["MS_y"])
    js = min(gk, key=lambda k: res["rows"][FVk]["cases"][k]["screw_T_sensitivity"]["MS_y"])
    res["rows"][FVk]["governing"] = {"case": jm, **res["rows"][FVk]["cases"][jm], "worst_with_screw_T_sensitivity": {"case": js, **res["rows"][FVk]["cases"][js]["screw_T_sensitivity"]}}
g = res["rows"]["3750"]["governing"]
res["verdict"] = (f"Tap wall to the torch passage (az 18 / 342), wall {g['wall_mm']} mm net at +/-0.25 deg, CALC at the 3750 N J-F1 cap: governing "
                  f"{g['case'].rsplit('|', 1)[0]} (N {g['N_N']} N from {g['from']}, p_thread {g['p_thread_MPa']} MPa, passage {g['p_passage_gauge_MPa']} MPa gauge): "
                  f"sigma {g['sigma_MPa']} MPa, MS_y {g['TC02_thread_T']['MS_y']:+.3f} / MS_u {g['TC02_thread_T']['MS_u']:+.3f} at the TC-02 thread temperature "
                  f"{g['TC02_thread_T']['T_C']} C; with the screw temperature as a sensitivity MS_y {g['worst_with_screw_T_sensitivity']['MS_y']:+.3f} "
                  f"({g['worst_with_screw_T_sensitivity']['case'].rsplit('|', 1)[0]}).  Closest approach {geo['az18']['wall_from_M5_major_to_d5.2_mm']} mm "
                  f"(paper, axes) at tap r {geo['az18']['at_tap_r_mm']} ({geo['az18']['depth_below_plug_OD_mm']} mm below the plug OD), "
                  f"{min(geo['closest_approach_above_tip_mm'].values())}-{max(geo['closest_approach_above_tip_mm'].values())} mm above the screw tip.")
res["t_run_s"] = round(time.time() - T0, 1)
s = json.dumps(res, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], res["t_run_s"])
print(json.dumps(geo))
print(json.dumps(WALLS))
print(res["verdict"])
for FVk in ("3750", "4096"):
    print(FVk, json.dumps(res["rows"][FVk]["screw_forces"]))
    for k, v in res["rows"][FVk]["cases"].items():
        if k.endswith("GOVERNING") or FVk == "3750":
            print(" ", k, v["N_N"], v["p_thread_MPa"], v["p_passage_gauge_MPa"], v["sigma_MPa"], v["TC02_thread_T"]["MS_y"], v["TC02_thread_T"]["MS_u"], v["screw_T_sensitivity"]["MS_y"])
