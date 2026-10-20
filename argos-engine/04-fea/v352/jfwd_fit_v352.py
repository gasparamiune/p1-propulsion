"""J-FWD contingency fits H7/h6 and H7/g6 (lead 08:10Z): the jfwd_embed_v352 v1 joint model at two candidate J-FWD fits, at 3.0 and 4.0 N m,
with the basis and the sensitivity flat-seat embedding, gap 0 included.  Mechanical, 2026-10-20, v1.  CALC on SIM temperatures; every number
DERIVED unless tagged.  A contingency only: the drawing stays H8 / f7 unless FEA3D's 0.078 seat run fails (lead 08:10Z).

Lead 08:10Z: 'run your jfwd_embed model at two candidate fits, H7/h6 (radial 0-0.0245) and H7/g6 (radial 0.005-0.0295), at 3.0 N m and
4.0 N m, with the basis and sensitivity embedding. Include gap 0. Give: slack or minimum force at every frame; the fit regime; the soak tension
yield; the J-F1 maximum. State, too, whether either fit is a problem for the gland-1 O-ring or for assembly.'

Model: exactly jfwd_embed_v352 v1 (its head is executed unchanged: js4-consistent k_sh 56 kN/mm, clamped-wall k_c, k_b calibrated to js4's
+927 N, through-wall d_w and ring growth d_r per frame, rev-3 B1 row histories merged / GVLO / GVHI), K 0.20, installation scatter
+/-25 % (F_min 0.75 F_nom for the in-service minimum after embedding, F_max 1.25 F_nom without embedding credit for the first firing),
head seat (a) spot face embedding f_Z basis 8 um / sensitivity 21 um (jfwd_embed v1).  The candidate radial gaps are the lead's
(min / mean / max of each fit); the H8 / f7 drawing gaps and the CAD 0.025 are shown beside them.  Sensitivity: the same at the rev-4 row
histories (v352_NF2b_R4_GVLO / _GVHI, chain 8).
Outputs per fit gap x torque x embedding: the minimum screw force over every frame of every bound (slack = F_S 0 at any frame, counted
per bound), the fit regime (at installation, cold after embedding, and the number of frames with the fit open), the first-firing
maximum with the soak tension yield (Rp(Ts) A_s / F_S - 1 over the post-burn frames) and the minimum of every screw / thread check,
and the J-F1 maximum (largest installation preload, no embedding credit, that passes every check at every frame; K_min = T / (F d)).
Gland 1 (S01) and assembly: the extrusion gap of 04-fea/v352/gland_fwd_v352_v1.json recomputed with the candidate maximum clearance;
the burn closure of the S01 forward land (gland_fwd: plug hotter than the case) against the candidate minimum clearance; the thermal
interference pressure where the closure exceeds the clearance (Lame, case bore 57.25 / OD 63.5, plug OD with the d10 manifold bore,
E(T) at the case land; CALC)."""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
OUT = J / "jfwd_fit_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_embed_v352.py").read_text().split("# ---- embedding: residual preload")[0]
NS = {"__file__": str(J / "jfwd_embed_v352.py")}
exec(compile(SRC, str(J / "jfwd_embed_v352.py") + "(head)", "exec"), NS)
g_ = NS.get
state, deltas, ROWS, K_B, K_SH, K_C, FZ = (NS[k] for k in ("state", "deltas", "ROWS", "K_B", "K_SH", "K_C", "FZ"))
tab, kT, kTu, TH, A3, RP20, RM20, MAT = (NS[k] for k in ("tab", "kT", "kTu", "TH", "A3", "RP20", "RM20", "MAT"))
strip_area, L_EFF, A_P, K_NUT = NS["strip_area"], NS["L_EFF"], NS["A_P"], NS["K_NUT"]
P_LC2, SFY, SFU, T_BURN_END = NS["P_LC2"], NS["SFY"], NS["SFU"], NS["T_BURN_END"]
Z_ROW, DZ_ROW, R_TAP = NS["Z_ROW"], NS["DZ_ROW"], NS["R_TAP"]
EMB = json.loads((J / "jfwd_embed_v352_v1.json").read_text())
GL = json.loads((J / "gland_fwd_v352_v1.json").read_text())

FITS = {"H7h6": {"radial_mm": (0.0, 0.0245), "src": "lead 08:10Z 'H7/h6 (radial 0-0.0245)'"},
        "H7g6": {"radial_mm": (0.005, 0.0295), "src": "lead 08:10Z 'H7/g6 (radial 0.005-0.0295)'"}}
GAPS = {}
for f, v in FITS.items():
    lo, hi = v["radial_mm"]
    GAPS.update({f"{f}_min": lo, f"{f}_mean": round(0.5 * (lo + hi), 5), f"{f}_max": hi})
REF = {"CAD_0.025_js4": 0.025, "H8f7_min": 0.040, "H8f7_max": 0.078}
ALLG = dict(GAPS, **REF)
TORQUES = (3.0, 4.0)
EMBED = {"basis": FZ["a_spot_face"]["basis_um"], "sens": FZ["a_spot_face"]["sens_um"]}


def limits(T01, T02, burn):                      # = jfwd_embed_v352 v1 limits()
    V_LC2 = P_LC2 * A_P / 10.0
    TF = SFY * V_LC2 / A3
    AN = strip_area(L_EFF)
    Ts = 0.5 * (T01 + T02)
    Rp, Rm = RP20 * kT(Ts), RM20 * kTu(Ts)
    out = {}
    if burn:
        out["LC2_yield_combined"] = math.sqrt(max(Rp ** 2 - 3.0 * TF ** 2, 0.0)) * TH["As"]
        Rs = SFU * V_LC2 / (0.6 * Rm * A3)
        out["LC2_ult_interaction"] = math.sqrt(max(1.0 - Rs ** 2, 0.0)) * Rm * TH["As"]
    else:
        out["soak_tension_yield"] = Rp * TH["As"]
        out["soak_tension_ult"] = Rm * TH["As"]
    out["TC02_thread_yield"] = 0.577 * tab("AL6061-T6", "Fty", T02) * AN
    out["TC02_thread_ult"] = MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * tab("AL6061-T6", "Ftu", T02) * AN
    return out


def rows_r4():
    R, S = {}, {}
    for gv in ("GVLO", "GVHI"):
        fh = HIST / f"DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_{gv}_hist.npz"
        z = np.load(fh, allow_pickle=True)
        X1, T1, X2, T2 = z["X_TC01"], z["T_TC01"], z["X_TC02"], z["T_TC02"]
        m1 = np.abs(X1[:, 1] - Z_ROW) <= DZ_ROW
        m2 = (np.abs(X2[:, 1] - Z_ROW) <= DZ_ROW) & (X2[:, 0] >= R_TAP)
        t = np.asarray(z["t_s"], float)
        R[f"R4_{gv}"] = (t, T1[:, m1].mean(axis=1) - 273.15, T2[:, m2].mean(axis=1) - 273.15)
        S[f"R4_{gv}"] = {"hist_npz": f"tb70/hist/{fh.name}", "sha256_16": sha(fh), "n_frames": int(len(t)),
                         "inj_face_z_mm": json.loads(str(z["info"])).get("inj_face_z_mm")}
    return R, S


R4, SRC4 = rows_r4()


def frames_of(rows):
    fr = {}
    for b, (t, a, c) in rows.items():
        Ts, dw, dr = np.array([deltas(float(x), float(y)) for x, y in zip(a, c)]).T
        fr[b] = (t, a, c, dw, dr, t <= T_BURN_END + 1e-6)
    return fr


FR3, FR4 = frames_of(ROWS), frames_of(R4)
LIM = {}
for nm, fr in (("rev3", FR3), ("rev4", FR4)):
    for b, (t, a, c, dw, dr, burn) in fr.items():
        LIM[(nm, b)] = [limits(float(a[i]), float(c[i]), bool(burn[i])) for i in range(len(t))]


def in_service(FV, g, f, fr, nm):
    """minimum screw force over every frame after embedding f (installation FV cold at gap g)."""
    mn, per = None, {}
    for b, (t, a, c, dw, dr, burn) in fr.items():
        FS, u, Fc, sl = state(np.full(len(t), FV), g, dw, dr, np.full(len(t), f), K_B)
        j = int(np.argmin(FS))
        per[b] = {"min_N": round(float(FS[j])), "t_s": round(float(t[j]), 3), "frames_slack": int(sl.sum()), "frames_fit_open": int((Fc <= 0).sum()),
                  "n_frames": int(len(t))}
        if mn is None or FS[j] < mn[0]:
            mn = (float(FS[j]), b, float(t[j]), bool(Fc[j] > 0), bool(sl[j]), float(a[j]), float(c[j]))
    return {"F_min_any_frame_N": round(mn[0]), "at": {"bound": mn[1], "t_s": round(mn[2], 3), "T01_T02_C": [round(mn[5], 1), round(mn[6], 1)]},
            "fit_at_min": "closed" if mn[3] else ("SLACK" if mn[4] else "open"), "slack_any_frame": any(v["frames_slack"] > 0 for v in per.values()),
            "per_bound": per}


def first_firing(FV, g, fr, nm):
    """no embedding credit: max screw force, the soak tension yield and the minimum of every check over every frame."""
    best, soak, fmax = None, None, None
    for b, (t, a, c, dw, dr, burn) in fr.items():
        FS, u, Fc, sl = state(np.full(len(t), FV), g, dw, dr, 0.0, K_B)
        j = int(np.argmax(FS))
        if fmax is None or FS[j] > fmax[0]:
            fmax = (float(FS[j]), b, float(t[j]), bool(Fc[j] > 0), float(a[j]), float(c[j]))
        L = LIM[(nm, b)]
        for i in range(len(t)):
            for kk, Fl in L[i].items():
                ms_ = Fl / max(float(FS[i]), 1e-9) - 1.0
                if best is None or ms_ < best[0]:
                    best = (ms_, kk, b, float(t[i]), float(FS[i]))
                if kk == "soak_tension_yield" and (soak is None or ms_ < soak[0]):
                    soak = (ms_, b, float(t[i]), float(FS[i]), float(a[i]), float(c[i]))
    return {"F_max_N": round(fmax[0]), "F_max_at": {"bound": fmax[1], "t_s": round(fmax[2], 3), "T01_T02_C": [round(fmax[4], 1), round(fmax[5], 1)],
                                                     "fit": "closed" if fmax[3] else "open"},
            "soak_tension_yield": {"MS": round(soak[0], 4), "bound": soak[1], "t_s": round(soak[2], 3), "F_S_N": round(soak[3]),
                                   "T01_T02_C": [round(soak[4], 1), round(soak[5], 1)]},
            "min_check": {"MS": round(best[0], 4), "check": best[1], "bound": best[2], "t_s": round(best[3], 3), "F_S_N": round(best[4])}}


def jf1_max(g, fr, nm):
    """largest installation preload (no embedding credit) that passes every check at every frame (= jfwd_embed v1 'allowed')."""
    best = None
    for b, (t, a, c, dw, dr, burn) in fr.items():
        L = LIM[(nm, b)]
        for i in range(len(t)):
            for kk, Fl in L[i].items():
                lo_, hi_ = 0.0, 2.0e4
                for _ in range(60):
                    m_ = 0.5 * (lo_ + hi_)
                    lo_, hi_ = (m_, hi_) if float(state(m_, g, dw[i], dr[i], 0.0, K_B)[0]) <= Fl else (lo_, m_)
                if best is None or lo_ < best[0]:
                    best = (lo_, kk, b, float(t[i]), float(a[i]), float(c[i]))
    return {"F_inst_max_N": round(best[0]), "K_min_at_3.0Nm": round(3.0e3 / (best[0] * TH["d"]), 4), "K_min_at_4.0Nm": round(4.0e3 / (best[0] * TH["d"]), 4),
            "governing_check": best[1], "bound": best[2], "t_s": round(best[3], 3), "T01_T02_C": [round(best[4], 1), round(best[5], 1)]}


res = {}
for nm, fr in (("rev3", FR3), ("rev4", FR4)):
    for gname, g in ALLG.items():
        if nm == "rev4" and gname in REF and gname != "H8f7_max":
            continue
        jf = jf1_max(g, fr, nm)
        for tq in TORQUES:
            Fn = tq * 1e3 / (K_NUT * TH["d"])
            Fmin, Fmax = 0.75 * Fn, 1.25 * Fn
            r = {"gap_mm": g, "torque_Nm": tq, "F_min_N": round(Fmin), "F_max_N": round(Fmax),
                 "installation_fit": {"at_F_min": "closed" if Fmin > K_SH * g else "open", "at_F_max": "closed" if Fmax > K_SH * g else "open",
                                      "F_to_close_N": round(K_SH * g)},
                 "first_firing_no_embedding": first_firing(Fmax, g, fr, nm), "J_F1_max": jf, "F_max_within_J_F1_max": bool(Fmax <= jf["F_inst_max_N"])}
            for lvl, fz in EMBED.items():
                f = fz * 1e-3
                FSc, uc, Fcc, slc = (float(x) for x in state(Fmin, g, 0.0, 0.0, f, K_B))
                r[f"in_service_{lvl}_fZ{fz:g}um"] = dict(in_service(Fmin, g, f, fr, nm), F_cold_after_embedding_N=round(FSc),
                                                         fit_cold_after_embedding=("closed" if Fcc > 0 else ("SLACK" if slc else "open")),
                                                         fit_contact_cold_N=round(Fcc))
            res[f"{nm}|{gname}|{tq:g}Nm"] = r

# ---- torque window per candidate gap (rev-3 rows): the smallest torque whose F_min (0.75 F_nom) after embedding keeps F_S > 0 at every
# frame, against the largest torque whose F_max (1.25 F_nom) stays within the J-F1 maximum (K 0.20 nominal, +/-25 % scatter as above)
window = {}
for gname, g in ALLG.items():
    jf = res[f"rev3|{gname}|3Nm"]["J_F1_max"]["F_inst_max_N"]
    t_hi = jf / 1.25 * K_NUT * TH["d"] / 1e3
    w = {"J_F1_max_N": jf, "T_max_Nm_F_max_within_J_F1": round(t_hi, 3)}
    for lvl, fz in EMBED.items():
        f = fz * 1e-3
        lo_, hi_ = 0.5, 12.0
        for _ in range(40):
            tq = 0.5 * (lo_ + hi_)
            Fmin = 0.75 * tq * 1e3 / (K_NUT * TH["d"])
            ok = in_service(Fmin, g, f, FR3, "rev3")["F_min_any_frame_N"] > 0
            lo_, hi_ = (lo_, tq) if ok else (tq, hi_)
        w[f"T_min_Nm_no_slack_{lvl}_fZ{fz:g}um"] = round(hi_, 3)
        w[f"window_{lvl}"] = (f"{hi_:.2f}-{t_hi:.2f} N m" if hi_ <= t_hi else "NONE (no torque keeps the head seated within the J-F1 maximum)")
    window[gname] = w
# ---- gland 1 (S01) and assembly
ext = GL["extrusion"]
c_dwg = ext["MEOP_45_bar_abs"]["gap_bore_minus_piston_mm"]["drawing_max_rest"]
closure = {gv: GL["thermal_rev4"][gv]["burn_min_dD_mm"] for gv in ("GVLO", "GVHI")}
E_case = GL["E_case_MPa_at_T"]["E_MPa"]
a_b, b_o, r_m, b_p, NU = 57.25 / 2.0, 63.5 / 2.0, 5.0, 57.25 / 2.0, 0.33
c_case = a_b * ((b_o ** 2 + a_b ** 2) / (b_o ** 2 - a_b ** 2) + NU)       # u_case = c_case p / E
c_plug = b_p * ((b_p ** 2 + r_m ** 2) / (b_p ** 2 - r_m ** 2) - NU)     # |u_plug| = c_plug p / E
hoop_k = (b_o ** 2 + a_b ** 2) / (b_o ** 2 - a_b ** 2)
gland = {"basis": "gland_fwd_v352_v1.json: plug glands on the J-FWD plug diameter (the extrusion gap is the fit clearance, bore - piston, all to one "
                  "side); squeeze / fill are set by the bore and the groove root 51.65 h9 and stay as in gland_fwd if the groove root is held "
                  "(the groove gets 0.025 mm deeper from the larger plug OD)",
         "FNST_90_limits_mm": {k: v["allowable_D1_90duro_mm"] for k, v in ext.items()}, "fits": {}}
for f, v in dict(FITS, H8f7={"radial_mm": (0.040, 0.078)}).items():
    lo, hi = v["radial_mm"]
    rows = {}
    for k, e in ext.items():
        gp = 2.0 * hi + e["gap_bore_minus_piston_mm"]["plus_pressure"] + e["gap_bore_minus_piston_mm"]["plus_thermal_burn_max"]
        al = e["allowable_D1_90duro_mm"]
        rows[k] = {"gap_mm": round(gp, 4), "MS": round(al / gp - 1.0, 3) if al else None, "verdict": ("PASS" if al and gp <= al else
                                                                                                        ("FAIL" if al else "OUTSIDE THE SOURCE TABLE (> 1500 psi)"))}
    intf = {}
    for gv, dD in closure.items():
        for lab, c in (("at_min_clearance", 2.0 * lo), ("at_max_clearance", 2.0 * hi)):
            d_int = -(dD + c)                                    # diametral interference (+) during the burn
            if d_int > 0:
                p = 0.5 * d_int * E_case / (c_case + c_plug)
                intf[f"{gv}|{lab}"] = {"interference_diametral_mm": round(d_int, 4), "contact_p_MPa": round(p, 2), "case_bore_hoop_MPa": round(p * hoop_k, 1)}
            else:
                intf[f"{gv}|{lab}"] = {"clearance_left_diametral_mm": round(-d_int, 4)}
    gland["fits"][f] = {"radial_mm": [lo, hi], "diametral_mm": [round(2 * lo, 4), round(2 * hi, 4)], "extrusion": rows, "burn_closure_S01_land": intf}
gland["burn_closure_diametral_mm"] = closure
gland["E_case_MPa"] = E_case
gland["note"] = ("the S01 forward land closes in the burn because the plug runs hotter than the case (gland_fwd: plug land 123.7 / 118.7 C, case "
                 "land 75.5 / 90.7 C max, GVLO / GVHI); with H8 / f7 the minimum clearance 0.080 just absorbs the GVLO closure 0.0803; both candidate "
                 "fits turn it into a thermal interference fit during the burn (self-limiting, secondary): the S-AX keeps that interface released, "
                 "so S-AX TC-01 / TC-02 rows at the glands would need the contact re-checked if a candidate fit is adopted")
out = {"id": "jfwd_fit_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_embed_v352.py": sha(J / "jfwd_embed_v352.py"), "jfwd_embed_v352_v1.json": sha(J / "jfwd_embed_v352_v1.json"),
                  "gland_fwd_v352_v1.json": sha(J / "gland_fwd_v352_v1.json"), "k_sh_N_mm": round(K_SH), "k_c_N_mm": round(K_C), "k_b_N_mm": round(K_B),
                  "K": K_NUT, "f_Z_um_spot_face": EMBED, "gaps_mm": ALLG, "fits": FITS,
                  "row_histories_rev3": EMB["inputs"]["row_histories_SIM"], "row_histories_rev4": SRC4},
       "rows": res, "torque_window_rev3": window, "gland_1_and_assembly": gland}
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for k, r in res.items():
    ib, isn = r["in_service_basis_fZ8um"], r[f"in_service_sens_fZ{EMBED['sens']:g}um"]
    ff = r["first_firing_no_embedding"]
    print(f"{k:28s} inst {r['installation_fit']['at_F_min']}/{r['installation_fit']['at_F_max']} | basis min {ib['F_min_any_frame_N']:5d} {ib['fit_at_min']:6s} "
          f"slack {ib['slack_any_frame']!s:5s} cold {ib['F_cold_after_embedding_N']} {ib['fit_cold_after_embedding']} | sens min {isn['F_min_any_frame_N']:5d} "
          f"{isn['fit_at_min']:6s} slack {isn['slack_any_frame']!s:5s} cold {isn['F_cold_after_embedding_N']} {isn['fit_cold_after_embedding']} | Fmax {ff['F_max_N']} "
          f"{ff['F_max_at']['fit']} soakY {ff['soak_tension_yield']['MS']:+.3f} min {ff['min_check']['MS']:+.3f} {ff['min_check']['check']} | JF1 "
          f"{r['J_F1_max']['F_inst_max_N']} ({r['J_F1_max']['governing_check']}) within {r['F_max_within_J_F1_max']}")
for k, w in window.items():
    print("window", k, w)
for f, v in gland["fits"].items():
    print("gland", f, {k: (x["gap_mm"], x["MS"]) for k, x in v["extrusion"].items()}, v["burn_closure_S01_land"])
