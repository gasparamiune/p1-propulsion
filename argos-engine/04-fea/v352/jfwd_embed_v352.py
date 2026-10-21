"""J-FWD HW-101 preload after embedding, with a joint stiffness consistent with FEA3D js4 (lead 06:23Z item 6).  Mechanical, 2026-10-20, v1.
CALC on SIM temperatures; every number DERIVED unless tagged.

Lead 06:23Z item 6: '(c) is rejected ... (a) the d10.5 spot face if FEA3D's SCL ... stay positive, otherwise (b). Whichever lands, your
preload-loss allowance must include flat-seat embedding (VDI 2230 f_Z for the head, the fit interface and the thread). Make its joint
stiffness consistent with js4 ... State the in-service minimum preload after embedding against what the joint needs. In js4, about 1.4 kN
of the 3750 N preload goes into closing the 0.025 mm fit clearance.'

js4 (FEA3D contact sub-model js4_mu0_T3750, relayed by the lead 06:18Z / 06:23Z; SIM, TO-CONFIRM against FEA3D's published table):
installation preload 3750 N (the +25 % bound at 3.0 N m, K 0.20), soak thermal rise +927 N (F 4677 N), about 1.4 kN of the preload closes the
0.025 mm radial fit clearance (CAD nominal: plug r 28.600, bore r 28.625), mu 0.  js4 state: GVLO soak at the TC-01 158 C row maximum, taken
here as the GVLO frame 63.651 s (TC-01 row 157.9 C, TC-02 tap zone 95.8 C; ASSUMED from the lead's 'at 158 C').

Per-screw model (radial, outward +; 1 DOF u = case-wall position relative to the plug OD at the screw; u < 0 = fit in contact):
  shell (case wall pulled in at the screw, ring + local mode): F_sh = k_sh (g + d_r - u), k_sh = 1.4 kN / 0.025 mm (js4, DERIVED)
  fit contact (wall through-thickness + contact + plug local): F_c = k_c (-u) for u < 0, k_c = the jfwd_preload_v352 clamped-wall estimate
  screw: F_S = F_V + k_b (d_w - f + u - u0) (installation at u0, then thermal d_w / embedding f), equilibrium F_S = F_sh + F_c, F_S >= 0
  d_w = through-wall differential expansion over L_G 3.15 mm (aluminium wall at T01, A4 screw at Ts = (T01 + T02) / 2) and
  d_r = ring growth of the case against the plug alpha_Al (T01 - T02) r_fit (r_fit 28.6), both exactly as jfwd_variant_v352 v2.
  k_b is calibrated so that the model reproduces js4's +927 N (k_sh, k_c fixed); the v2 stiff hand value (k_b 4.73e5, k_bm 3.65e5 N/mm) and a
  VDI 2230-form screw resilience (head 0.4 d, free thread over A_d3, engaged thread 0.5 d over A_d3, tapped-part 0.33 d with E_Al; AS RECALLED
  form, TO-VERIFY) are reported beside it.
Two regimes follow from js4's numbers: fit CLOSED (F_S > k_sh g: stiff joint, k_J = k_b (k_c + k_sh) / (k_b + k_c + k_sh)) and fit OPEN
(F_S < k_sh g: the screw pulls the shell, k_J = k_b k_sh / (k_b + k_sh)).  The drawing gap (TC-01 fwd bore 57.25 H8 +0.046/0, TC-02 plug
57.20 f7 -0.030/-0.060: radial 0.040-0.078, mean 0.059) is wider than the CAD's 0.025, so both regimes are evaluated at the CAD gap and at the
drawing min / mean / max gap.
Embedding f_Z (VDI 2230 guide values for steel parts, 10 <= Rz < 40 um: 3 um in the thread, 3 um per head bearing, 2 um per inner interface;
LITERATURE: MESYS AG bolted-joint manual, https://www.mesys.ch/manual/bolted_joint.html, accessed 2026-10-20, 'fz = 3+3+2 = 8 um'):
  (a) spot face: thread 3 + head on the 6061 spot face 3 + fit (6061 / 6061) 2 = 8 um
  (b) saddle washer (A4 ASSUMED): thread 3 + head on washer 3 + washer on the OD 2 + fit 2 = 10 um
  sensitivity (ASSUMED, no source): x1.5 on the head bearing and inner interfaces (transverse-loaded joint) and x2 on every interface with
  a 6061-T6 face (the guide values are for steel parts): (a) 21 um, (b) 22.5 um.
Checks at every frame (as jfwd_variant_v352 v2): LC2 (45 bar, SF 1.5 / 2.0) combined yield / ultimate interaction at the burn frames, soak
screw tension yield / ultimate after the burn, TC-02 internal-thread shear at every frame; the allowed installation preload (J-F1 maximum)
is recomputed with this model, without embedding credit (first firing)."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np

JF = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
src = (JF / "jfwd_preload_v352.py").read_text().split("T_LC2, T_LC2B, T_FA1, T_SOAK")[0]
ns = {}
exec(compile(src, "jfwd_preload_v352.py(head)", "exec"), ns)
tab, kT, kTu, strip_area, TH, A3, RP20, RM20, K_B_HAND, k_m = (ns[k] for k in ("tab", "kT", "kTu", "strip_area", "TH", "A3", "RP20", "RM20", "K_B", "k_m"))
A_P, L_EFF, T_WALL, GAP_FIT, MAT, E_S = ns["A_P"], ns["L_EFF"], ns["T_WALL"], ns["GAP_FIT"], ns["MAT"], ns["E_S"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


L_G, R_FIT = T_WALL + GAP_FIT, 28.6
P_LC2, SFY, SFU, T_BURN_END = 4.5, 1.5, 2.0, 21.651
TORQUE, K_NUT = 3.0, 0.20
F_NOM = TORQUE * 1e3 / (K_NUT * TH["d"])
F_MIN, F_MAX = 0.75 * F_NOM, 1.25 * F_NOM
JS4 = {"F_V_N": 3750.0, "dF_thermal_N": 927.0, "F_total_N": 4677.0, "F_gap_N": 1400.0, "gap_mm": 0.025, "frame_bound": "GVLO", "frame_t_s": 63.651,
       "screw_MS_y": 0.439, "screw_MS_u": 1.33, "head_band_MPa_line_contact_158C": 495.0,
       "source": "FEA3D js4_mu0_T3750 (SIM), relayed by the lead 06:18Z / 06:23Z; TO-CONFIRM against FEA3D's published js4 table"}
K_SH = JS4["F_gap_N"] / JS4["gap_mm"]                 # N/mm per screw, DERIVED from js4
K_C = k_m(20.0)                                         # N/mm, clamped-wall estimate of jfwd_preload_v352 (A_m 72.4 mm2, E_Al 20 C)
GAPS = {"CAD_nominal_js4": 0.025, "drawing_min_H8f7": 0.040, "drawing_mean": 0.059, "drawing_max": 0.078}
FZ = {"a_spot_face": {"basis_um": 3 + 3 + 2, "sens_um": 3 * 2 + 3 * 1.5 * 2 + 2 * 1.5 * 2,
                      "parts": "thread 3 (6061 tap: x2 in sens), head on 6061 spot face 3 (x1.5 x2), fit 6061/6061 2 (x1.5 x2)"},
      "b_saddle_washer": {"basis_um": 3 + 3 + 2 + 2, "sens_um": 3 * 2 + 3 * 1.5 + 2 * 1.5 * 2 + 2 * 1.5 * 2,
                          "parts": "thread 3 (x2), head on A4 washer 3 (x1.5), washer on 6061 OD 2 (x1.5 x2), fit 2 (x1.5 x2)"}}


def a_al(T):
    return tab("AL6061-T6", "alpha", T)


def deltas(T01, T02):
    Ts = 0.5 * (T01 + T02)
    dw = (a_al(T01) * (T01 - 20.0) - tab("SS316L", "alpha", Ts) * (Ts - 20.0)) * L_G
    dr = a_al(Ts) * (T01 - T02) * R_FIT
    return Ts, dw, dr


def state(FV, g, dw, dr, f, kb, ksh=K_SH, kc=K_C):
    """screw force, wall position and fit contact force after installation at FV (cold, gap g) and a change (dw, dr, f). Vectorised."""
    FV, dw, dr, f = (np.asarray(x, float) for x in (FV, dw, dr, f))
    u0 = np.where(FV <= ksh * g, g - FV / ksh, -(FV - ksh * g) / (ksh + kc))
    N = ksh * (g + dr) - FV - kb * (dw - f) + kb * u0
    u = np.where(N < 0.0, N / (kb + ksh + kc), N / (kb + ksh))
    FS = FV + kb * (dw - f + u - u0)
    slack = FS < 0.0
    FS = np.where(slack, 0.0, FS)
    Fc = np.where(u < 0.0, -kc * u, 0.0)
    return FS, u, Fc, slack


# ---- row temperatures (rev-3 B1 histories: merged / GVLO / GVHI, as jfwd_variant_v352 v2; the rev-4 histories replace them when available)
Z_ROW, DZ_ROW, R_TAP = 134.06, 2.6, 19.5
LABELS = {"merged": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b", "GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO",
          "GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVHI"}
ROWS, SRC = {}, {}
for b, lab in LABELS.items():
    fh = HIST / f"{lab}_hist.npz"
    z = np.load(fh, allow_pickle=True)
    X1, T1, X2, T2 = z["X_TC01"], z["T_TC01"], z["X_TC02"], z["T_TC02"]
    m1 = np.abs(X1[:, 1] - Z_ROW) <= DZ_ROW
    m2 = (np.abs(X2[:, 1] - Z_ROW) <= DZ_ROW) & (X2[:, 0] >= R_TAP)
    t = np.asarray(z["t_s"], float)
    ROWS[b] = (t, T1[:, m1].mean(axis=1) - 273.15, T2[:, m2].mean(axis=1) - 273.15)
    SRC[b] = {"hist_npz": f"tb70/hist/{fh.name}", "sha256_16": sha16(fh), "n_frames": int(len(t))}

# ---- js4 calibration of k_b (k_sh, k_c fixed)
tq_, a_, c_ = ROWS[JS4["frame_bound"]]
i4 = int(np.argmin(np.abs(tq_ - JS4["frame_t_s"])))
T01_4, T02_4 = float(a_[i4]), float(c_[i4])
Ts4, dw4, dr4 = deltas(T01_4, T02_4)
lo, hi = 1.0e4, 2.0e6
for _ in range(200):
    mid = 0.5 * (lo + hi)
    FS4 = float(state(JS4["F_V_N"], JS4["gap_mm"], dw4, dr4, 0.0, mid)[0])
    lo, hi = (mid, hi) if FS4 - JS4["F_V_N"] < JS4["dF_thermal_N"] else (lo, mid)
K_B = 0.5 * (lo + hi)
FS4, u4, Fc4, _ = (float(x) for x in state(JS4["F_V_N"], JS4["gap_mm"], dw4, dr4, 0.0, K_B))
# VDI 2230-form screw resilience (AS RECALLED form, TO-VERIFY): head 0.4 d / A_N, free thread (grip 3.15 + 0.5 mouth) / A_d3, engaged 0.5 d / A_d3,
# tapped part 0.33 d / A_N with E_Al
A_N, A_D3 = math.pi / 4 * TH["d"] ** 2, A3
E_AL20 = tab("AL6061-T6", "E", 20.0)
dS = (0.4 * TH["d"] / A_N + (L_G + 0.5) / A_D3 + 0.5 * TH["d"] / A_D3) / E_S + 0.33 * TH["d"] / (E_AL20 * A_N)
K_B_VDI = 1.0 / dS
kJ = lambda kb, closed: kb * (K_C + K_SH) / (kb + K_C + K_SH) if closed else kb * K_SH / (kb + K_SH)
F_hand_js4 = None
try:   # the v2 hand thermal rise at the js4 frame (k_sh 21 kN/mm series K_B 4.73e5, through-wall with k_bm), for the record
    kbm = K_B_HAND * K_C / (K_B_HAND + K_C)
    F_hand_js4 = dw4 * kbm + a_al(Ts4) * (T01_4 - T02_4) * R_FIT * 21000.0 * K_B_HAND / (21000.0 + K_B_HAND)
except Exception:
    pass
calib = {"js4": JS4, "frame": {"bound": JS4["frame_bound"], "t_s": round(float(tq_[i4]), 3), "T01_C": round(T01_4, 1), "T02_tap_C": round(T02_4, 1),
                               "Ts_C": round(Ts4, 1), "d_w_um": round(dw4 * 1e3, 2), "d_r_um": round(dr4 * 1e3, 2)},
         "k_sh_N_mm_from_js4": round(K_SH), "k_c_N_mm_clamped_wall": round(K_C),
         "k_b_calibrated_N_mm": round(K_B), "model_at_js4": {"F_S_N": round(FS4), "dF_N": round(FS4 - JS4["F_V_N"]), "fit_contact_N": round(Fc4),
                                                             "u_um": round(u4 * 1e3, 3)},
         "k_J_closed_N_mm": round(kJ(K_B, True)), "k_J_open_N_mm": round(kJ(K_B, False)),
         "comparison": {"v2_hand_k_b_N_mm": round(K_B_HAND), "v2_hand_k_bm_N_mm": round(K_B_HAND * K_C / (K_B_HAND + K_C)),
                        "v2_hand_thermal_rise_at_js4_frame_N": round(F_hand_js4) if F_hand_js4 else None,
                        "VDI_form_k_b_N_mm": round(K_B_VDI), "VDI_form_k_J_closed_N_mm": round(kJ(K_B_VDI, True)),
                        "VDI_form_model_dF_at_js4_N": round(float(state(JS4["F_V_N"], JS4["gap_mm"], dw4, dr4, 0.0, K_B_VDI)[0]) - JS4["F_V_N"])},
         "statement": None}
calib["statement"] = (
    f"With k_sh = 1.4 kN / 0.025 mm = {K_SH / 1e3:.0f} kN/mm (js4) and the clamped-wall k_c {K_C / 1e6:.2f}e6 N/mm, a screw stiffness k_b "
    f"{K_B / 1e5:.2f}e5 N/mm reproduces js4's +927 N at the GVLO soak frame (fit stays closed, residual fit contact {Fc4:.0f} N): the joint "
    f"stiffness for an axial mismatch is {kJ(K_B, True) / 1e5:.2f}e5 N/mm with the fit closed and {kJ(K_B, False) / 1e3:.0f} kN/mm with it open, "
    f"against the v2 stiff hand value k_bm {K_B_HAND * K_C / (K_B_HAND + K_C) / 1e5:.2f}e5 (k_b {K_B_HAND / 1e5:.2f}e5: A_s over the grip, E_steel in the "
    f"tapped part); the VDI-form screw resilience gives k_b {K_B_VDI / 1e5:.2f}e5 (closed k_J {kJ(K_B_VDI, True) / 1e5:.2f}e5, js4 frame "
    f"+{calib['comparison']['VDI_form_model_dF_at_js4_N']} N). The v2 hand rise at that frame was {F_hand_js4:.0f} N because it put the ring growth "
    f"(d_r {dr4 * 1e3:.1f} um) through the screw in series with a 21 kN/mm shell; with the fit closed the ring growth mainly unloads the fit contact.")

# ---- embedding: residual preload (cold, after embedding) for the installation range, both options, basis / sensitivity, every gap
emb = {}
for opt, fz in FZ.items():
    for lvl in ("basis_um", "sens_um"):
        f = fz[lvl] * 1e-3
        for gname, g in GAPS.items():
            row = {}
            for fl, FV in (("F_min_2250", F_MIN), ("F_nom_3000", F_NOM), ("F_max_3750", F_MAX)):
                FS0, u0_, Fc0, _ = (float(x) for x in state(FV, g, 0.0, 0.0, 0.0, K_B))
                FS1, u1, Fc1, sl = (float(x) for x in state(FV, g, 0.0, 0.0, f, K_B))
                row[fl] = {"installed_fit": "closed" if Fc0 > 0 else "open", "installed_fit_contact_N": round(Fc0),
                           "F_after_embedding_N": round(FS1), "loss_N": round(FV - FS1), "fit_after": "closed" if Fc1 > 0 else ("open" if not sl else "SLACK"),
                           "fit_contact_after_N": round(Fc1), "wall_lift_um": round(max(u1, 0.0) * 1e3, 2),
                           "F_gap_cold_N": round(K_SH * g)}
            emb[f"{opt}|{lvl}|{gname}"] = row
# ---- every frame: in-service minimum (after embedding) and the first-firing maximum (no embedding credit) with the checks
V_LC2 = P_LC2 * A_P / 10.0
TF = SFY * V_LC2 / A3
AN = strip_area(L_EFF)


def limits(T01, T02, burn):
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


frames = {}
for b, (t, a, c) in ROWS.items():
    Ts, dw, dr = np.array([deltas(float(x), float(y)) for x, y in zip(a, c)]).T
    frames[b] = (t, a, c, Ts, dw, dr, t <= T_BURN_END + 1e-6)
allowed, firstfire, inservice = {}, {}, {}
for gname, g in GAPS.items():
    best = None
    for b, (t, a, c, Ts, dw, dr, burn) in frames.items():
        for i in range(len(t)):
            lim = limits(float(a[i]), float(c[i]), bool(burn[i]))
            for kk, Fl in lim.items():
                lo_, hi_ = 0.0, 2.0e4
                for _ in range(60):
                    m_ = 0.5 * (lo_ + hi_)
                    lo_, hi_ = (m_, hi_) if float(state(m_, g, dw[i], dr[i], 0.0, K_B)[0]) <= Fl else (lo_, m_)
                if best is None or lo_ < best[0]:
                    best = (lo_, kk, b, float(t[i]), float(a[i]), float(c[i]))
    allowed[gname] = {"F_inst_max_N": round(best[0]), "K_min_at_3Nm": round(TORQUE * 1e3 / (best[0] * TH["d"]), 4), "governing_check": best[1],
                      "bound": best[2], "frame_t_s": round(best[3], 3), "T01_C": round(best[4], 1), "T02_C": round(best[5], 1)}
    # first firing at the +25 % installation preload (no embedding): max screw force and its regime
    mx = None
    for b, (t, a, c, Ts, dw, dr, burn) in frames.items():
        FS, u, Fc, sl = state(np.full(len(t), F_MAX), g, dw, dr, 0.0, K_B)
        j = int(np.argmax(FS))
        if mx is None or FS[j] > mx[0]:
            mx = (float(FS[j]), b, float(t[j]), float(a[j]), float(c[j]), bool(Fc[j] > 0))
    firstfire[gname] = {"F_max_inst_3750_N": round(mx[0]), "dF_thermal_N": round(mx[0] - F_MAX), "bound": mx[1], "t_s": round(mx[2], 3),
                        "T01_T02_C": [round(mx[3], 1), round(mx[4], 1)], "fit": "closed" if mx[5] else "open"}
    for opt, fz in FZ.items():
        for lvl in ("basis_um", "sens_um"):
            f = fz[lvl] * 1e-3
            mn = None
            n_open = {}
            for b, (t, a, c, Ts, dw, dr, burn) in frames.items():
                FS, u, Fc, sl = state(np.full(len(t), F_MIN), g, dw, dr, np.full(len(t), f), K_B)
                j = int(np.argmin(FS))
                n_open[b] = int((Fc <= 0).sum())
                if mn is None or FS[j] < mn[0]:
                    mn = (float(FS[j]), b, float(t[j]), float(a[j]), float(c[j]), bool(Fc[j] > 0), bool(sl[j]))
            FScold = float(state(F_MIN, g, 0.0, 0.0, f, K_B)[0])
            inservice[f"{opt}|{lvl}|{gname}"] = {
                "F_min_inst_N": round(F_MIN), "f_Z_um": fz[lvl], "F_cold_after_embedding_N": round(FScold),
                "F_min_any_frame_N": round(mn[0]), "at": {"bound": mn[1], "t_s": round(mn[2], 3), "T01_T02_C": [round(mn[3], 1), round(mn[4], 1)]},
                "fit_at_min": "closed" if mn[5] else ("SLACK" if mn[6] else "open"), "frames_with_fit_open": n_open,
                "need_fit_closed_cold_N": round(K_SH * g), "MS_vs_fit_closing_cold": round(FScold / (K_SH * g) - 1.0, 3),
                "head_seated_everywhere": bool(mn[0] > 0.0)}
# ---- first firing at the +25 % preload: minimum screw / thread margin over every frame (no embedding credit), per gap and torque; and the
# alternative torque 4.0 N m (allowed when F_inst_max above stays >= its +25 % preload): in-service minimum after embedding
A_HEAD = math.pi / 4.0 * (TH["dk"] ** 2 - TH["hole"] ** 2)


def first_fire_ms(FV, g):
    best = None
    for b, (t, a, c, Ts, dw, dr, burn) in frames.items():
        FS = state(np.full(len(t), FV), g, dw, dr, 0.0, K_B)[0]
        for i in range(len(t)):
            for kk, Fl in limits(float(a[i]), float(c[i]), bool(burn[i])).items():
                ms_ = Fl / max(float(FS[i]), 1e-9) - 1.0
                if best is None or ms_ < best[0]:
                    best = (ms_, kk, b, float(t[i]), float(FS[i]), float(a[i]))
    return {"MS_min": round(best[0], 4), "check": best[1], "bound": best[2], "t_s": round(best[3], 3), "F_S_N": round(best[4]),
            "head_bearing_MPa_on_spot_face": round(best[4] / A_HEAD, 1), "T01_C": round(best[5], 1),
            "Fty_6061_T01_MPa": round(tab("AL6061-T6", "Fty", best[5]), 1)}


torque_rows = {}
for tq in (3.0, 4.0):
    Fn_ = tq * 1e3 / (K_NUT * TH["d"])
    Fmin_, Fmax_ = 0.75 * Fn_, 1.25 * Fn_
    for gname, g in GAPS.items():
        r_ = {"F_min_N": round(Fmin_), "F_max_N": round(Fmax_), "allowed_F_inst_max_N": allowed[gname]["F_inst_max_N"],
              "within_allowed": bool(Fmax_ <= allowed[gname]["F_inst_max_N"]), "first_firing": first_fire_ms(Fmax_, g)}
        for opt, fz in FZ.items():
            for lvl in ("basis_um", "sens_um"):
                f = fz[lvl] * 1e-3
                FSc, uc, Fcc, slc = (float(x) for x in state(Fmin_, g, 0.0, 0.0, f, K_B))
                mn = None
                for b, (t, a, c, Ts, dw, dr, burn) in frames.items():
                    FS, u, Fc, sl = state(np.full(len(t), Fmin_), g, dw, dr, np.full(len(t), f), K_B)
                    j = int(np.argmin(FS))
                    if mn is None or FS[j] < mn[0]:
                        mn = (float(FS[j]), b, float(t[j]), bool(sl[j]))
                r_[f"{opt}|{lvl}"] = {"cold_after_embedding_N": round(FSc), "fit_cold": "closed" if Fcc > 0 else ("SLACK" if slc else "open"),
                                      "fit_contact_cold_N": round(Fcc), "min_any_frame_N": round(mn[0]), "min_at": [mn[1], round(mn[2], 3)],
                                      "slack": mn[3], "MS_vs_fit_closing_cold": round(FSc / (K_SH * g) - 1.0, 3)}
        torque_rows[f"{tq:g}Nm|{gname}"] = r_
out = {"id": "jfwd_embed_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_preload_v352.py": sha16(JF / "jfwd_preload_v352.py"), "jfwd_variant_v352_v2.json": sha16(JF / "jfwd_variant_v352_v2.json"),
                  "row_histories_SIM": SRC, "torque_Nm": TORQUE, "K": K_NUT, "preload_N": {"min": F_MIN, "nom": F_NOM, "max": F_MAX},
                  "gaps_mm": GAPS, "f_Z_um": FZ},
       "stiffness_js4_consistent": calib, "embedding_cold": emb, "allowed_installation_preload_no_embedding": allowed,
       "first_firing_max_at_3750N": firstfire, "in_service_minimum_after_embedding": inservice, "torque_rows_3.0_4.0Nm": torque_rows}
s = json.dumps(out, indent=1, default=float)
(JF / "jfwd_embed_v352_v1.json").write_text(s)
print("jfwd_embed_v352_v1.json", hashlib.sha256(s.encode()).hexdigest()[:16])
print(calib["statement"])
print(json.dumps(calib["model_at_js4"]), "k_J closed", calib["k_J_closed_N_mm"], "open", calib["k_J_open_N_mm"], json.dumps(calib["comparison"]))
for k, v in emb.items():
    print(k, {kk: (vv["installed_fit"], vv["F_after_embedding_N"], vv["fit_after"], vv["fit_contact_after_N"]) for kk, vv in v.items()})
for k, v in allowed.items():
    print("allowed", k, v)
for k, v in firstfire.items():
    print("first firing", k, v)
for k, v in inservice.items():
    print("in-service", k, {kk: v[kk] for kk in ("F_cold_after_embedding_N", "F_min_any_frame_N", "fit_at_min", "need_fit_closed_cold_N",
                                                   "MS_vs_fit_closing_cold", "head_seated_everywhere")}, v["at"])
for k, v in torque_rows.items():
    print("torque", k, {kk: v[kk] for kk in ("F_min_N", "F_max_N", "allowed_F_inst_max_N", "within_allowed")}, "first", v["first_firing"])
    for kk in ("a_spot_face|basis_um", "a_spot_face|sens_um", "b_saddle_washer|basis_um", "b_saddle_washer|sens_um"):
        print("    ", kk, v[kk])
