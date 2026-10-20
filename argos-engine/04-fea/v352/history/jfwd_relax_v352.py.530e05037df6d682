"""J-FWD: TC-01 wall relaxation at the screw plane and the no-slack check over two consecutive firings (lead 08:40Z ruling 1 (a) / (b);
lead 09:15Z item A).  Mechanical, 2026-10-20, v2 (v1 859f40081b5a2499 kept as jfwd_relax_v352_v1.py; v1 json 49dbf5b92b461a0b).
CALC on SIM temperatures; every number DERIVED unless tagged.  H8 / f7 stays (lead 08:40Z).

Lead 08:40Z ruling 1: the preload pull on the TC-01 wall is SECONDARY (self-limited by the fit gap; no collapse path).  Because a
self-limiting stress costs preload:
 (a) P+Q <= 2 Fty(T) at the soak at both band ends (0.040 / 0.078), at the J-F1 acceptance maximum 4096 N as well as at 3750 N;
 (b) relaxation: where the elastic preload + soak wall stress exceeds Fty(T), cap the shell force at its first-yield value at that
     frame's temperature and carry the excess as permanent wall set; add the resulting preload loss to the embedding; repeat the no-slack
     check at 0.040 / 0.059 / 0.078 for 2250 N and 4096 N installations, basis and sensitivity embedding, over two consecutive firings:
     every head must stay seated.
Lead 09:15Z A: FEA3D js5_mu0_T3750_g078 (s5 spot-face mesh, mu 0, 3750 N, fit 0.078, solved at 20 C) [SIM]: F_sh = 3749.9 - 1118.7
(fit radial on TC-01) = 2631.2 N (js4 at 0.025: 1438.3 N); the fit closes on an annulus at the hole edge.  Preload-only Pm+Pb: mid-bay
160.8, ring 166.6 (Pm 99.1), seat line 0.26 mm from the hole wall 226.5 (Pm 92.8), bore node 197.8 MPa; all elastic at 20 C (Fty 240).
'Bound it with first yield on the seat line (conservative).  If the no-slack check passes there, that closes it.  If it fails only
there, also give the bound with first yield on the ring line, say which you propose, and I rule.'
(FEA3D relax_partial.json of the run, read-only, sha at read in the inputs.)

Joint model: jfwd_embed_v352 v1 (its head is executed: clamped-wall k_c, k_b calibrated to js4's +927 N, through-wall d_w and ring growth
d_r per frame), extended by a permanent inward wall set s at the screw: the shell spring acts from the set position,
F_sh = k_sh (g - s + d_r - u); the fit contact is unchanged, F_c = k_c (-u) for u < 0; screw F_S = F_V + k_b (d_w - f + u - u0) with u0
the installation position (s = 0); equilibrium F_S = F_sh + F_c; F_S < 0 = slack (head unseated).
Calibrations of the shell stiffness k_sh:
  K_js5 (GOVERNING, v3.5.2 spot-face geometry): k_sh such that the model reproduces js5's F_sh 2631.2 N at 3750 N and 0.078 (with the
        model's k_c: fit closed, F_c = 1118.7 N): k_sh = 2631.2 / (0.078 + 1118.7 / k_c);
  K_js4 (v1 basis, s4 mesh without the spot face): k_sh = 1.4 kN / 0.025 mm (jfwd_embed v1), for continuity.
  k_b stays at its js4 calibration in both (js5's soak steps, when published, re-calibrate it for s5).
Wall stress per line: sigma_line = c_line F_sh with c_line = js5 preload-only Pm+Pb / js5's F_sh 2631.2 N (the FE stress per unit shell
pull; K_js5 reproduces that shell pull, so the model gives the FE line stress at the js5 state): seat 226.5, ring 166.6, mid-bay 160.8 MPa.  The seat line is the bound (lead 09:15Z); the ring line is the alternative, run beside it.
Elastic-perfectly-plastic wall, no reverse yielding: at every frame, if c F_sh > Fty(T01) the set grows until c F_sh = Fty(T01) (first
yield at that frame's TC-01 row temperature; engmat 6061-T6 Fty(T), ASTM minimum x ASM 10 000 h ratio); the set is carried to the next
frame, through the cold state (20 C, d_w = d_r = 0) after the firing, into the second firing.
Frames: the rev-4 B1 row histories at the J-FWD screw plane (v352_NF2b_R4_GVLO / _GVHI), every frame of the firing, then a cold frame;
embedding f_Z (spot face (a)) applied from the first frame (complete at installation: conservative), basis 8 um / sensitivity 21 um
(jfwd_embed v1).  Installations: 2250 N and 4096 N (J-F1 acceptance band, lead 08:40Z) and 3750 N (+25 % at 3.0 N m, K 0.20) for (a);
gaps 0.040 / 0.059 / 0.078 (H8 / f7) and the CAD 0.025 beside them.
(a): elastic P+Q (no cap, no embedding: the largest shell pull) = c F_sh at the soak frames (t > burn end) vs 2 Fty(T01) of that frame,
minimum margin; the FE soak values of js5 (3750 N, 0.078) replace this scaling when FEA3D publishes them."""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
OUT = J / "jfwd_relax_v352_v2.json"
JS5_RELAX = Path("/home/claude/work/fea3d/jfwd/runs/js5_mu0_T3750_g078/relax_partial.json")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_embed_v352.py").read_text().split("# ---- embedding: residual preload")[0]
NS = {"__file__": str(J / "jfwd_embed_v352.py")}
exec(compile(SRC, str(J / "jfwd_embed_v352.py") + "(head)", "exec"), NS)
deltas, K_B, K_SH, K_C, FZ, tab, T_BURN_END = (NS[k] for k in ("deltas", "K_B", "K_SH", "K_C", "FZ", "tab", "T_BURN_END"))
Z_ROW, DZ_ROW, R_TAP = NS["Z_ROW"], NS["DZ_ROW"], NS["R_TAP"]
JS5 = {"F_screw_N": 3749.9, "F_fit_N": 1118.7, "F_sh_N": 2631.2, "gap_mm": 0.078, "FV_N": 3750.0,
       "PmPb_preload_MPa": {"seat": 226.5, "ring": 166.6, "midbay": 160.8}, "Pm_preload_MPa": {"seat": 92.8, "ring": 99.1, "midbay": 64.7}}
_j5 = json.loads(JS5_RELAX.read_text())
_g = {f: _j5["steps"]["SOAK"]["families"][f]["governing_by_preload_only"]["preload_only"]["PmPb"] for f in ("seat", "ring", "midbay")}
assert all(abs(_g[f] - JS5["PmPb_preload_MPa"][f]) < 0.05 for f in _g), _g
assert abs(_j5["shell_pull"]["PRELOAD"]["F_sh_N"] - JS5["F_sh_N"]) < 0.05
K_SH_JS4 = K_SH
K_SH_JS5 = JS5["F_sh_N"] / (JS5["gap_mm"] + JS5["F_fit_N"] / K_C)
CALIB = {"K_js5": K_SH_JS5, "K_js4": K_SH_JS4}
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


def u_install(FV, g, ksh):
    return g - FV / ksh if FV <= ksh * g else -(FV - ksh * g) / (ksh + K_C)


def state_s(FV, g, dw, dr, f, s, ksh, kb=K_B):
    """jfwd_embed state() with a permanent inward wall set s (shell spring from the set position)."""
    u0 = u_install(FV, g, ksh)
    N = ksh * (g - s + dr) - FV - kb * (dw - f) + kb * u0
    u = N / (kb + ksh + K_C) if N < 0.0 else N / (kb + ksh)
    FS = FV + kb * (dw - f + u - u0)
    Fsh = ksh * (g - s + dr - u)
    Fc = -K_C * u if u < 0.0 else 0.0
    return FS, u, Fc, Fsh


# line coefficients, normalised on the model's js5 shell pull per calibration (K_js5 reproduces 2631.2 N exactly)
FSH_MODEL_JS5 = {cn: state_s(JS5["FV_N"], JS5["gap_mm"], 0.0, 0.0, 0.0, 0.0, k)[3] for cn, k in CALIB.items()}
C_LINE = {cn: {ln: JS5["PmPb_preload_MPa"][ln] / JS5["F_sh_N"] for ln in ("seat", "ring", "midbay")} for cn in CALIB}


def fire(FV, g, f, fr, s0, c, ksh):
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
        FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f, s, ksh)
        yielded = False
        if FS > 0.0 and c * Fsh > Fy:                 # first yield at this frame's temperature: grow the set until c F_sh = Fty(T01)
            lo, hi = s, s + 1.0
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if c * state_s(FV, g, dw, dr, f, mid, ksh)[3] > Fy:
                    lo = mid
                else:
                    hi = mid
            s = hi
            FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f, s, ksh)
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


res = {"id": "jfwd_relax_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_embed_v352.py": sha(J / "jfwd_embed_v352.py"), "js5_relax_partial_json": {"path": str(JS5_RELAX), "sha256_16_at_read": sha(JS5_RELAX)},
                  "js5_preload": JS5, "rows": SRC4, "k_c_N_mm": round(K_C), "k_b_N_mm": round(K_B),
                  "k_sh_N_mm": {cn: round(k) for cn, k in CALIB.items()},
                  "model_F_sh_at_js5_state_N": {cn: round(v, 1) for cn, v in FSH_MODEL_JS5.items()},
                  "fit_closes_at_install_N": {cn: {gn: round(k * g) for gn, g in GAPS.items()} for cn, k in CALIB.items()},
                  "c_line_MPa_per_N": {ln: round(v, 5) for ln, v in C_LINE["K_js5"].items()},
                  "first_yield_F_sh_N": {f"{T:g}C": {ln: round(float(tab("AL6061-T6", "Fty", T)) / v) for ln, v in C_LINE["K_js5"].items()}
                                         for T in (20.0, 100.0, 150.0, 158.0, 170.0)},
                  "embedding_um": {k: v * 1e3 for k, v in EMB.items()},
                  "Fty_MPa": {f"{T:g}C": round(float(tab("AL6061-T6", "Fty", T)), 1) for T in (20.0, 100.0, 150.0, 158.0, 170.0)}},
       "b_relaxation": {}, "a_PQ_soak": {}}
for cn, ksh in CALIB.items():
    for ln in ("seat", "ring"):
        c = C_LINE[cn][ln]
        for gn, g in GAPS.items():
            for iname, FV in INSTALL.items():
                if iname == "Fmax_3.0Nm_3750":
                    continue
                for en, f in EMB.items():
                    for gv, fr in ROWS4.items():
                        rec1, s1 = fire(FV, g, f, fr, 0.0, c, ksh)
                        rec2, s2 = fire(FV, g, f, fr, s1, c, ksh)
                        FS_cold0 = state_s(FV, g, 0.0, 0.0, f, 0.0, ksh)[0]
                        key = f"{cn}|{ln}|{gn}|{iname}|{en}|{gv}"
                        res["b_relaxation"][key] = {
                            "gap_mm": g, "F_install_N": FV, "embedding_um": round(f * 1e3, 1), "bound": gv, "k_sh_N_mm": round(ksh), "line": ln,
                            "c_MPa_per_N": round(c, 5), "installed_cold_after_embedding_N": round(FS_cold0),
                            "firing_1": summary(rec1), "firing_2": summary(rec2),
                            "set_after_firing_1_um": round(s1 * 1e3, 3), "set_after_firing_2_um": round(s2 * 1e3, 3),
                            "relaxation_loss_cold_N": round(FS_cold0 - rec1[-1]["FS"]),
                            "heads_seated_both_firings": not any(q["slack"] for q in rec1 + rec2),
                            "shakedown_second_firing_elastic": (s2 - s1) < 1e-9}
    # (a) elastic P+Q at the soak frames (no cap, no embedding: the largest shell pull), vs 2 Fty(T01)
    for ln in ("seat", "ring", "midbay"):
        c = C_LINE[cn][ln]
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
                        FS, u, Fc, Fsh = state_s(FV, g, dw, dr, 0.0, 0.0, ksh)
                        pq = c * Fsh
                        ms = 2.0 * float(tab("AL6061-T6", "Fty", float(T01[i]))) / pq - 1.0
                        if best is None or ms < best[0]:
                            best = (ms, float(t[i]), float(T01[i]), pq, Fsh, FS, Fc > 0)
                    res["a_PQ_soak"][f"{cn}|{ln}|{gn}|{iname}|{gv}"] = {"MS_PQ_vs_2Fty": round(best[0], 3), "t_s": round(best[1], 3), "T01_C": round(best[2], 1),
                                                                     "PQ_MPa": round(best[3], 1), "F_sh_N": round(best[4]), "F_S_N": round(best[5]),
                                                                     "fit": "closed" if best[6] else "open"}
# verdict rows
gov = {k: v for k, v in res["b_relaxation"].items() if k.startswith("K_js5|seat|") and not k.split("|")[2].startswith("CAD")}
alt = {k: v for k, v in res["b_relaxation"].items() if k.startswith("K_js5|ring|") and not k.split("|")[2].startswith("CAD")}
def vsum(d):
    j = min(d, key=lambda k: min(d[k]["firing_1"]["F_S_min_N"], d[k]["firing_2"]["F_S_min_N"]))
    v = d[j]
    return {"all_seated": all(x["heads_seated_both_firings"] for x in d.values()), "n_cases": len(d),
            "n_unseated": sum(1 for x in d.values() if not x["heads_seated_both_firings"]),
            "unseated_cases": [k for k, x in d.items() if not x["heads_seated_both_firings"]],
            "min_case": j, "F_S_min_N": min(v["firing_1"]["F_S_min_N"], v["firing_2"]["F_S_min_N"]),
            "max_set_um": max(x["set_after_firing_2_um"] for x in d.values()), "max_cold_loss_N": max(x["relaxation_loss_cold_N"] for x in d.values()),
            "all_shakedown": all(x["shakedown_second_firing_elastic"] for x in d.values())}
res["verdict"] = {"b_seat_line_bound_K_js5": vsum(gov), "b_ring_line_K_js5": vsum(alt)}
s = json.dumps(res, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps(res["inputs"]["k_sh_N_mm"]), json.dumps(res["inputs"]["model_F_sh_at_js5_state_N"]), json.dumps(res["inputs"]["fit_closes_at_install_N"]))
print(json.dumps(res["inputs"]["c_line_MPa_per_N"]), json.dumps(res["inputs"]["first_yield_F_sh_N"]))
for k, v in res["a_PQ_soak"].items():
    if k.startswith("K_js5"):
        print("PQ", k, v["MS_PQ_vs_2Fty"], v["PQ_MPa"], v["T01_C"], v["F_sh_N"], v["fit"])
for k, v in res["b_relaxation"].items():
    f1, f2 = v["firing_1"], v["firing_2"]
    print(f"{k:48s} cold0 {v['installed_cold_after_embedding_N']:5d} set1 {v['set_after_firing_1_um']:7.3f} set2 {v['set_after_firing_2_um']:7.3f} loss {v['relaxation_loss_cold_N']:5d} "
          f"| f1 min {f1['F_S_min_N']:5d} @{f1['at_t_s']} {f1['fit_at_min']:6s} s/Fy {f1['max_sig_over_Fty']:.3f} | f2 min {f2['F_S_min_N']:5d} @{f2['at_t_s']} "
          f"{f2['fit_at_min']:6s} cold {f2['cold_end_F_S_N']:5d} | seated {v['heads_seated_both_firings']} sd {v['shakedown_second_firing_elastic']}")
print(json.dumps(res["verdict"], indent=1))
