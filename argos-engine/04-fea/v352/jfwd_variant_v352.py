"""J-FWD HW-101 at the gap-conductance variant temperatures (lead 2026-10-20 (2) variant; CHANGELOG 234 (1)(b) basis kept).  Mechanical,
2026-10-20, v2 (v1 = jfwd_variant_v352_v1.py -> jfwd_variant_v352_v1.json 9a7165eeda7cfc71, kept).  CALC on SIM temperatures; stiffnesses
ASSUMED as in jfwd_preload_v352.py.
v2 adds (lead 2026-10-20: 'J-FWD 3.0 N m ACCEPTED'; '2.5 N m fallback rows'; 'GVHI rows'): the GVHI bound; 2.5 N m; every row at
k_sh x0.5 / x1 / x1.5; every output frame of the B1 runs instead of 7 picked times (LC2 at every burn frame, soak at every frame after the
burn); the maximum installation preload each check allows (the J-F1 acceptance limit) with the governing bound, frame and check.
Row temperatures (SIM): read from tb70/hist/<label>_hist.npz (case_tc_hist_v352.py, streamed from the thermal frd.gz) with the v1 rule:
TC-01 = mean of the ENG-TC-01 nodes within +/- 2.6 mm of the screw row (thermal frame z 134.06), TC-02 = mean of the ENG-TC-02 nodes with
r >= 19.5 mm in the same band (tap zone); v1's hand-entered rows are reproduced to 0.05 K (asserted).
What the variant adds to jfwd_preload_v352 (uniform joint temperature): TC-01 and TC-02 at different temperatures at the screw row.
  (a) through-wall term: dF_w = (alpha_Al(T01) dT01 - alpha_A4(Ts) dTs) L_grip k_bm  (L_grip 3.15 mm, k_bm = k_b k_m / (k_b + k_m));
  (b) ring-growth mismatch: the case ring (T01) grows radially against the plug (T02) by d = alpha_Al (T01 - T02) r_fit at r_fit 28.6 mm
      (> 0: the case moves away from the plug and stretches the screws; < 0 unloads them), resisted by the case shell at the 10 screws
      (long thin cylinder, ring-load mode + local point-load mode: k_sh about 21 kN/mm per screw, CALC (Roark-type, ASSUMED +/-50 %)) in
      series with the screw: dF_r = d k_sh k_b / (k_sh + k_b).
  Screw temperature Ts = mean of the TC-01 wall mean and the TC-02 tap-zone mean at the row (ASSUMED; the 2D model has no screw).
Checks (max installation preload F_inst = 1.25 F_nom, K 0.20; F_max = F_inst + dF_w + dF_r):
  LC2 (45 bar, SF 1.5 / 2.0) at every burn frame: combined yield sqrt(st^2 + 3 tf^2) <= kT Rp0.2, ultimate interaction Rt^2 + Rs^2 <= 1;
  soak (no pressure) at every frame after the burn: screw tension F_max / A_s <= kT Rp0.2 (and kTu Rm);
  TC-02 internal thread (FED-STD-H28 strip area, L_eff 6.35 mm, unfactored installation load) <= 0.577 Fty(T02) / Fsu(T02), every frame.
Allowed installation preload (J-F1 acceptance): the largest F_inst with every check above >= 0 at every frame of the bound."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np

JF = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
src = (JF / "jfwd_preload_v352.py").read_text().split("T_LC2, T_LC2B, T_FA1, T_SOAK")[0]
ns = {}
exec(compile(src, "jfwd_preload_v352.py(head)", "exec"), ns)
tab, kT, kTu, strip_area, TH, A3, RP20, RM20, K_B, k_m = (ns[k] for k in ("tab", "kT", "kTu", "strip_area", "TH", "A3", "RP20", "RM20", "K_B", "k_m"))
A_P, L_EFF, T_WALL, GAP_FIT, MAT = ns["A_P"], ns["L_EFF"], ns["T_WALL"], ns["GAP_FIT"], ns["MAT"]
K_SH = 21000.0
R_FIT = 28.6
L_G = T_WALL + GAP_FIT
P_LC2, SFY, SFU = 4.5, 1.5, 2.0
T_BURN_END = 21.651
TORQUES = (4.0, 3.5, 3.0, 2.5)
KSH_F = (0.5, 1.0, 1.5)
Z_ROW, DZ_ROW, R_TAP = 134.06, 2.6, 19.5
LABELS = {"merged": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b", "GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO",
          "GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVHI"}
ROW_V1 = {"merged": {21.65: (75.8, 75.9), 64.7: (110.7, 110.6), 166.7: (119.6, 119.6)},
          "GVLO": {21.65: (60.0, 81.2), 37.7: (126.4, 92.2), 51.7: (152.6, 93.7), 64.7: (158.0, 96.0), 100.0: (147.1, 101.6),
                   166.7: (129.1, 106.5), 266.7: (117.3, 108.2)}}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def a_al(T):
    return tab("AL6061-T6", "alpha", T)


def dF(T01, T02, f_ksh=1.0):
    Ts = 0.5 * (T01 + T02)
    kbm = K_B * k_m(T01) / (K_B + k_m(T01))
    dw = (a_al(T01) * (T01 - 20.0) - tab("SS316L", "alpha", Ts) * (Ts - 20.0)) * L_G * kbm
    ksh = K_SH * f_ksh
    d = a_al(0.5 * (T01 + T02)) * (T01 - T02) * R_FIT
    dr = d * ksh * K_B / (ksh + K_B)
    return Ts, dw, dr


AN = strip_area(L_EFF)
V_LC2 = P_LC2 * A_P / 10.0
TF = SFY * V_LC2 / A3


def allowed(T01, T02, burn, f_ksh=1.0):
    """largest installation preload F_inst (N) with every check >= 0 at this frame, per check."""
    Ts, dw, dr = dF(T01, T02, f_ksh)
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
    return {k: v - dw - dr for k, v in out.items()}, (Ts, dw, dr)


def check(torque, T01, T02, burn, f_ksh=1.0):
    Ts, dw, dr = dF(T01, T02, f_ksh)
    Finst = 1.25 * torque * 1e3 / (0.20 * TH["d"])
    Fmax = Finst + dw + dr
    Rp, Rm = RP20 * kT(Ts), RM20 * kTu(Ts)
    st = Fmax / TH["As"]
    o = {"T01_C": round(T01, 1), "T02_C": round(T02, 1), "Ts_C": round(Ts, 1), "dF_wall_N": round(dw), "dF_ring_N": round(dr), "F_max_N": round(Fmax)}
    if burn:
        o["MS_y_combined"] = round(Rp / math.sqrt(st ** 2 + 3 * TF ** 2) - 1, 4)
        Rt, Rs = Fmax / (Rm * TH["As"]), SFU * V_LC2 / (0.6 * Rm * A3)
        o["MS_u_interaction"] = round(1 / math.sqrt(Rt ** 2 + Rs ** 2) - 1, 4)
    else:
        o["MS_y_tension"] = round(Rp / st - 1, 4)
        o["MS_u_tension"] = round(Rm * TH["As"] / Fmax - 1, 4)
    o["TC02_thread_MS_y"] = round(0.577 * tab("AL6061-T6", "Fty", T02) / (Fmax / AN) - 1, 4)
    o["TC02_thread_MS_u"] = round(MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * tab("AL6061-T6", "Ftu", T02) / (Fmax / AN) - 1, 4)
    return o


# ---- row temperatures from the stored histories
ROWS, SRC = {}, {}
for b, lab in LABELS.items():
    f = HIST / f"{lab}_hist.npz"
    z = np.load(f, allow_pickle=True)
    info = json.loads(str(z["info"]))
    X1, T1, X2, T2 = z["X_TC01"], z["T_TC01"], z["X_TC02"], z["T_TC02"]
    m1 = np.abs(X1[:, 1] - Z_ROW) <= DZ_ROW
    m2 = (np.abs(X2[:, 1] - Z_ROW) <= DZ_ROW) & (X2[:, 0] >= R_TAP)
    t = np.asarray(z["t_s"], float)
    ROWS[b] = (t, T1[:, m1].mean(axis=1) - 273.15, T2[:, m2].mean(axis=1) - 273.15)
    a_, c_ = ROWS[b][1], ROWS[b][2]
    SRC[b] = {"hist_npz": f"tb70/hist/{f.name}", "hist_sha256_16": sha16(f), "frd": info["frd"], "frd_sha256_16": info["frd_sha256_16"],
              "gap_variant": info["gap_variant"], "n_frames": int(len(t)), "n_TC01_row_nodes": int(m1.sum()), "n_TC02_tap_nodes": int(m2.sum()),
              "row_T_max_C": {"TC01": [round(float(a_.max()), 1), round(float(t[int(a_.argmax())]), 3)],
                              "TC02_tap": [round(float(c_.max()), 1), round(float(t[int(c_.argmax())]), 3)],
                              "Ts": [round(float((0.5 * (a_ + c_)).max()), 1), round(float(t[int((a_ + c_).argmax())]), 3)]}}
repro = {}
for b, d in ROW_V1.items():
    t, a, c = ROWS[b]
    repro[b] = {}
    for tt, (v1a, v1c) in d.items():
        i = int(np.argmin(np.abs(t - tt)))
        assert abs(round(float(a[i]), 1) - v1a) <= 0.05 and abs(round(float(c[i]), 1) - v1c) <= 0.05, (b, tt, a[i], c[i], v1a, v1c)
        repro[b][f"{tt:g}"] = {"frame_t_s": round(float(t[i]), 3), "v1_T01_T02_C": [v1a, v1c], "v2_T01_T02_C": [round(float(a[i]), 2), round(float(c[i]), 2)]}

out = {"id": "jfwd_variant_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "supersedes": {"file": "jfwd_variant_v352_v1.json", "sha256_16": sha16(JF / "jfwd_variant_v352_v1.json"),
                      "script": "jfwd_variant_v352_v1.py", "script_sha256_16": sha16(JF / "jfwd_variant_v352_v1.py"),
                      "what_changed": "GVHI bound, 2.5 N m, k_sh x0.5/x1/x1.5 on every row, every output frame, allowed installation preload"},
       "k_sh_N_mm_ASSUMED": K_SH, "k_sh_factors": KSH_F, "k_b_N_mm_ASSUMED": round(K_B), "row_rule": {"z_row_thermal_mm": Z_ROW, "dz_mm": DZ_ROW, "TC02_r_min_mm": R_TAP},
       "sources_SIM": SRC, "v1_row_reproduction": repro, "results": {}, "allowed_installation_preload_N": {}, "summary_rows": []}
sel_frames = (21.651, 37.651, 51.651, 64.651, 101.651, 166.651, 266.651)
for b, (t, a, c) in ROWS.items():
    burn = t <= T_BURN_END + 1e-6
    rb = {}
    for f_k in KSH_F:
        # allowed installation preload over all frames
        best = None
        for i in range(len(t)):
            al, _ = allowed(float(a[i]), float(c[i]), bool(burn[i]), f_k)
            for kk, v in al.items():
                if best is None or v < best[0]:
                    best = (v, kk, float(t[i]), float(a[i]), float(c[i]))
        out["allowed_installation_preload_N"][f"{b}_ksh_x{f_k:g}"] = {
            "F_inst_max_N": round(best[0]), "governing_check": best[1], "frame_t_s": round(best[2], 3), "T01_C": round(best[3], 1), "T02_C": round(best[4], 1),
            "K_min": {f"{tq:g}Nm": round(tq * 1e3 / (best[0] * TH["d"]), 4) for tq in TORQUES}}
        for tq in TORQUES:
            rows_b = [check(tq, float(a[i]), float(c[i]), True, f_k) | {"t_s": round(float(t[i]), 3)} for i in np.where(burn)[0]]
            rows_s = [check(tq, float(a[i]), float(c[i]), False, f_k) | {"t_s": round(float(t[i]), 3)} for i in np.where(~burn)[0]]
            gb = min(rows_b, key=lambda o: o["MS_y_combined"])
            gs = min(rows_s, key=lambda o: o["MS_y_tension"])
            gt = min(rows_b + rows_s, key=lambda o: o["TC02_thread_MS_y"])
            eob = next(o for o in rows_b if abs(o["t_s"] - T_BURN_END) < 1e-3)
            r = {"LC2_burn_governing": gb, "LC2_end_of_burn": eob,
                 "LC2_burn_min": {"MS_y_combined": gb["MS_y_combined"], "MS_u_interaction": min(o["MS_u_interaction"] for o in rows_b)},
                 "soak_governing": gs, "soak_min": {"MS_y_tension": gs["MS_y_tension"], "MS_u_tension": min(o["MS_u_tension"] for o in rows_s)},
                 "TC02_thread_governing": gt}
            if f_k == 1.0:
                r["soak_selected_frames"] = {f"t{o['t_s']:g}": o for o in rows_s if any(abs(o["t_s"] - x) < 1e-3 for x in sel_frames)}
            rb[f"{tq:g}Nm_ksh_x{f_k:g}"] = r
            out["summary_rows"].append({"bound": b, "torque_Nm": tq, "k_sh_factor": f_k, "LC2_MS_y_min": gb["MS_y_combined"], "LC2_at_t_s": gb["t_s"],
                                        "LC2_MS_u_min": r["LC2_burn_min"]["MS_u_interaction"], "soak_MS_y_min": gs["MS_y_tension"], "soak_at_t_s": gs["t_s"],
                                        "soak_T01_T02_C": [gs["T01_C"], gs["T02_C"]], "soak_MS_u_min": r["soak_min"]["MS_u_tension"],
                                        "thread_MS_y_min": gt["TC02_thread_MS_y"], "thread_at_t_s": gt["t_s"]})
    out["results"][b] = rb
# J-F1 limit over the three bounds (k_sh x1 = the nominal estimate; x1.5 = the stiff-shell sensitivity)
for f_k in KSH_F:
    cand = [(v["F_inst_max_N"], k) for k, v in out["allowed_installation_preload_N"].items() if k.endswith(f"_ksh_x{f_k:g}")]
    F, k = min(cand)
    out["allowed_installation_preload_N"][f"ALL_BOUNDS_ksh_x{f_k:g}"] = {"F_inst_max_N": F, "governing_bound": k.split("_ksh")[0],
                                                                         "K_min": {f"{tq:g}Nm": round(tq * 1e3 / (F * TH["d"]), 4) for tq in TORQUES}}
s = json.dumps(out, indent=1)
(JF / "jfwd_variant_v352_v2.json").write_text(s)
print("jfwd_variant_v352_v2.json", hashlib.sha256(s.encode()).hexdigest()[:16])
print("reproduction of v1 rows OK:", {b: len(v) for b, v in repro.items()})
for k, v in out["allowed_installation_preload_N"].items():
    print(k, v)
for r in out["summary_rows"]:
    print(r)
