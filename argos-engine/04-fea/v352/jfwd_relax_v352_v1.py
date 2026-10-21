"""J-FWD: TC-01 wall relaxation at the screw plane and the no-slack check over two consecutive firings (lead 08:40Z ruling 1 (a) / (b)).
Mechanical, 2026-10-20, v1.  CALC on SIM temperatures; every number DERIVED unless tagged.  H8 / f7 stays (lead 08:40Z).

Lead 08:40Z ruling 1: the preload pull on the TC-01 wall is SECONDARY (self-limited by the fit gap; no collapse path).  Because a
self-limiting stress costs preload:
 (a) P+Q <= 2 Fty(T) at the soak at both band ends (0.040 / 0.078), at the J-F1 acceptance maximum 4096 N as well as at 3750 N;
 (b) relaxation: where the elastic preload + soak wall stress exceeds Fty(T) (at 0.078 about 224 MPa preload-only vs 170.3 at 158 C), cap
     the shell force at its first-yield value at that frame's temperature and carry the excess as permanent wall set; add the resulting
     preload loss to the embedding; repeat the no-slack check at 0.040 / 0.059 / 0.078 for 2250 N and 4096 N installations, basis and
     sensitivity embedding, over two consecutive firings: every head must stay seated.

Joint model: jfwd_embed_v352 v1 unchanged (its head is executed: k_sh 56 kN/mm from js4, clamped-wall k_c, k_b calibrated to js4's +927 N,
through-wall d_w and ring growth d_r per frame), extended by a permanent inward wall set s at the screw: the shell spring acts from the
set position, F_sh = k_sh (g - s + d_r - u); the fit contact is unchanged, F_c = k_c (-u) for u < 0; screw F_S = F_V + k_b (d_w - f + u -
u0) with u0 the installation position (s = 0); equilibrium F_S = F_sh + F_c; F_S < 0 = slack (head unseated).
Wall stress at the mid-bay: sigma_w = c F_sh with c = 88.4 MPa / 1480 N (FEA3D js4 preload-only mid-bay value relayed 08:04Z, at the model's
js4 cold shell pull; tc01_midbay_preload v1), the preload-only scaling the lead quotes ('about 224 MPa' at 0.078 and 3750 N); it is above the
js4 soak ratio 190 MPa / 3793 N, so it yields earlier (more set, more preload loss); the soak ratio is the sensitivity row (less set).
Elastic-perfectly-plastic wall, no reverse yielding: at every frame, if c F_sh > Fty(T01) the set grows until c F_sh = Fty(T01) (first
yield at that frame's TC-01 row temperature; engmat 6061-T6 Fty(T), ASTM minimum x ASM 10 000 h ratio); the set is carried to the next
frame, through the cold state (20 C, d_w = d_r = 0) after the firing, into the second firing.
Frames: the rev-4 B1 row histories at the J-FWD screw plane (v352_NF2b_R4_GVLO / _GVHI, as jfwd_fit v1 sensitivity), every frame of the
firing, then a cold frame; embedding f_Z (spot face (a)) applied from the first frame (complete at installation: conservative), basis
8 um / sensitivity 21 um (jfwd_embed v1).  Installations: 2250 N and 4096 N (J-F1 acceptance band, lead 08:40Z) and 3750 N (+25 % at
3.0 N m, K 0.20) for (a); gaps 0.040 / 0.059 / 0.078 (H8 / f7) and the CAD 0.025 beside them.
(a): elastic P+Q (no cap, no embedding: the largest shell pull) = c F_sh at the soak frames vs 2 Fty(T01) of that frame, minimum margin."""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
OUT = J / "jfwd_relax_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_embed_v352.py").read_text().split("# ---- embedding: residual preload")[0]
NS = {"__file__": str(J / "jfwd_embed_v352.py")}
exec(compile(SRC, str(J / "jfwd_embed_v352.py") + "(head)", "exec"), NS)
deltas, K_B, K_SH, K_C, FZ, tab, T_BURN_END = (NS[k] for k in ("deltas", "K_B", "K_SH", "K_C", "FZ", "tab", "T_BURN_END"))
Z_ROW, DZ_ROW, R_TAP = NS["Z_ROW"], NS["DZ_ROW"], NS["R_TAP"]
JS4_PRE_MPA, JS4_FSH_COLD_N = 88.4, 1480.0          # tc01_midbay_preload v1 (model js4 cold F_sh 1480 N)
JS4_SOAK_MPA, JS4_FSH_SOAK_N = 190.0, 3793.0        # js4 soak Pm+Pb, model js4 soak F_sh
C_PRE, C_SOAK = JS4_PRE_MPA / JS4_FSH_COLD_N, JS4_SOAK_MPA / JS4_FSH_SOAK_N
GAPS = {"CAD_0.025": 0.025, "H8f7_min": 0.040, "H8f7_mean": 0.059, "H8f7_max": 0.078}
INSTALL = {"J-F1_min_2250": 2250.0, "J-F1_max_4096": 4096.0, "Fmax_3.0Nm_3750": 3750.0}
EMB = {"basis": FZ["a_spot_face"]["basis_um"] * 1e-3, "sens": FZ["a_spot_face"]["sens_um"] * 1e-3}


def rows_r4():
    R, S = {}, {}
    for gv in ("GVLO", "GVHI"):
        fh = HIST / f"DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_{gv}_hist.npz"
        z = np.load(fh, allow_pickle=True)
        X1, T1, X2, T2 = z["X_TC01"], z["T_TC01"], z["X_TC02"], z["T_TC02"]
        m1 = np.abs(X1[:, 1] - Z_ROW) <= DZ_ROW
        m2 = (np.abs(X2[:, 1] - Z_ROW) <= DZ_ROW) & (X2[:, 0] >= R_TAP)
        t = np.asarray(z["t_s"], float)
        R[gv] = (t, T1[:, m1].mean(axis=1) - 273.15, T2[:, m2].mean(axis=1) - 273.15)
        S[gv] = {"hist_npz": f"tb70/hist/{fh.name}", "sha256_16": sha(fh), "n_frames": int(len(t)), "t_end_s": round(float(t[-1]), 2)}
    return R, S


ROWS4, SRC4 = rows_r4()


def u_install(FV, g):
    return g - FV / K_SH if FV <= K_SH * g else -(FV - K_SH * g) / (K_SH + K_C)


def state_s(FV, g, dw, dr, f, s, kb=K_B):
    """jfwd_embed state() with a permanent inward wall set s (shell spring from the set position)."""
    u0 = u_install(FV, g)
    N = K_SH * (g - s + dr) - FV - kb * (dw - f) + kb * u0
    u = N / (kb + K_SH + K_C) if N < 0.0 else N / (kb + K_SH)
    FS = FV + kb * (dw - f + u - u0)
    Fsh = K_SH * (g - s + dr - u)
    Fc = -K_C * u if u < 0.0 else 0.0
    return FS, u, Fc, Fsh


def fire(FV, g, f, fr, s0, c):
    """one firing (every frame of fr, then a cold frame) from the set s0; returns per-frame records and the set at the end."""
    t, T01, T02 = fr
    s = s0
    rec = []
    for i in list(range(len(t))) + [None]:
        if i is None:
            a_, b_, dw, dr, ti = 20.0, 20.0, 0.0, 0.0, "cold"
        else:
            a_, b_ = float(T01[i]), float(T02[i])
            _, dw, dr = deltas(a_, b_)
            ti = round(float(t[i]), 3)
        Fy = float(tab("AL6061-T6", "Fty", a_))
        FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f, s)
        yielded = False
        if FS > 0.0 and c * Fsh > Fy:                 # first yield at this frame's temperature: grow the set until c F_sh = Fty(T01)
            lo, hi = s, s + 1.0
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if c * state_s(FV, g, dw, dr, f, mid)[3] > Fy:
                    lo = mid
                else:
                    hi = mid
            s = hi
            FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f, s)
            yielded = True
        rec.append({"t": ti, "T01": a_, "T02": b_, "FS": FS, "Fsh": Fsh, "Fc": Fc, "u": u, "sig": c * Fsh, "Fty": Fy, "set": s,
                    "yield": yielded, "slack": FS <= 0.0})
    return rec, s


def summary(rec):
    j = min(range(len(rec)), key=lambda k: rec[k]["FS"])
    r = rec[j]
    return {"F_S_min_N": round(r["FS"]), "at_t_s": r["t"], "T01_T02_C": [round(r["T01"], 1), round(r["T02"], 1)],
            "fit_at_min": "closed" if r["Fc"] > 0 else ("SLACK" if r["slack"] else "open"),
            "slack_frames": int(sum(1 for q in rec if q["slack"])), "yield_frames": int(sum(1 for q in rec if q["yield"])),
            "set_end_um": round(rec[-1]["set"] * 1e3, 3), "cold_end_F_S_N": round(rec[-1]["FS"]),
            "max_sig_over_Fty": round(max(q["sig"] / q["Fty"] for q in rec), 3)}


res = {"id": "jfwd_relax_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_embed_v352.py": sha(J / "jfwd_embed_v352.py"), "tc01_midbay_preload_v352_v1.json": sha(J / "tc01_midbay_preload_v352_v1.json"),
                  "rows": SRC4, "k_sh_N_mm": round(K_SH), "k_c_N_mm": round(K_C), "k_b_N_mm": round(K_B),
                  "c_pre_MPa_per_N": round(C_PRE, 5), "c_soak_MPa_per_N": round(C_SOAK, 5), "embedding_um": {k: v * 1e3 for k, v in EMB.items()},
                  "Fty_MPa": {f"{T:g}C": round(float(tab("AL6061-T6", "Fty", T)), 1) for T in (20.0, 100.0, 150.0, 158.0, 170.0)}},
       "b_relaxation": {}, "a_PQ_soak": {}}
for cn, c in (("c_pre", C_PRE), ("c_soak", C_SOAK)):
    for gn, g in GAPS.items():
        for iname, FV in INSTALL.items():
            if iname == "Fmax_3.0Nm_3750" and cn == "c_soak":
                continue
            for en, f in EMB.items():
                for gv, fr in ROWS4.items():
                    rec1, s1 = fire(FV, g, f, fr, 0.0, c)
                    rec2, s2 = fire(FV, g, f, fr, s1, c)
                    FS_cold0 = state_s(FV, g, 0.0, 0.0, f, 0.0)[0]
                    key = f"{cn}|{gn}|{iname}|{en}|{gv}"
                    res["b_relaxation"][key] = {
                        "gap_mm": g, "F_install_N": FV, "embedding_um": round(f * 1e3, 1), "bound": gv, "c_MPa_per_N": round(c, 5),
                        "installed_cold_after_embedding_N": round(FS_cold0),
                        "firing_1": summary(rec1), "firing_2": summary(rec2),
                        "set_after_firing_1_um": round(s1 * 1e3, 3), "set_after_firing_2_um": round(s2 * 1e3, 3),
                        "relaxation_loss_cold_N": round(FS_cold0 - rec1[-1]["FS"]),
                        "heads_seated_both_firings": not any(q["slack"] for q in rec1 + rec2),
                        "shakedown_second_firing_elastic": (s2 - s1) < 1e-9}
    # (a) elastic P+Q at the soak frames (no cap, no embedding: the largest shell pull), vs 2 Fty(T01)
    for gn in ("H8f7_min", "H8f7_max", "CAD_0.025"):
        g = GAPS[gn]
        for iname in ("Fmax_3.0Nm_3750", "J-F1_max_4096"):
            FV = INSTALL[iname]
            for gv, (t, T01, T02) in ROWS4.items():
                best = None
                for i in range(len(t)):
                    if t[i] <= T_BURN_END:
                        continue
                    _, dw, dr = deltas(float(T01[i]), float(T02[i]))
                    FS, u, Fc, Fsh = state_s(FV, g, dw, dr, 0.0, 0.0)
                    pq = c * Fsh
                    ms = 2.0 * float(tab("AL6061-T6", "Fty", float(T01[i]))) / pq - 1.0
                    if best is None or ms < best[0]:
                        best = (ms, float(t[i]), float(T01[i]), pq, Fsh, FS, Fc > 0)
                res["a_PQ_soak"][f"{cn}|{gn}|{iname}|{gv}"] = {"MS_PQ_vs_2Fty": round(best[0], 3), "t_s": round(best[1], 3), "T01_C": round(best[2], 1),
                                                             "PQ_MPa": round(best[3], 1), "F_sh_N": round(best[4]), "F_S_N": round(best[5]),
                                                             "fit": "closed" if best[6] else "open"}
s = json.dumps(res, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
for k, v in res["a_PQ_soak"].items():
    print("PQ", k, v["MS_PQ_vs_2Fty"], v["PQ_MPa"], v["T01_C"], v["fit"])
for k, v in res["b_relaxation"].items():
    f1, f2 = v["firing_1"], v["firing_2"]
    print(f"{k:42s} cold0 {v['installed_cold_after_embedding_N']:5d} set1 {v['set_after_firing_1_um']:7.3f} um loss {v['relaxation_loss_cold_N']:5d} "
          f"| f1 min {f1['F_S_min_N']:5d} @{f1['at_t_s']} {f1['fit_at_min']:6s} s/Fy {f1['max_sig_over_Fty']:.3f} | f2 min {f2['F_S_min_N']:5d} @{f2['at_t_s']} "
          f"{f2['fit_at_min']:6s} cold {f2['cold_end_F_S_N']:5d} | seated {v['heads_seated_both_firings']} sd {v['shakedown_second_firing_elastic']}")
