"""J-FWD: TC-01 wall relaxation at the screw plane, screw plastic set and the no-slack check over two consecutive firings.
Mechanical, 2026-10-20, v3 (v2 530e05037df6d682 kept as jfwd_relax_v352_v2.py; v1 as jfwd_relax_v352_v1.py).  CALC on SIM temperatures
and SIM (FEA3D) calibration states; every number DERIVED unless tagged.  H8 / f7 stays (lead 08:40Z).

v3 (lead 09:45Z, 'joint model on K_js5 APPROVED; (b) closes on the re-run'; lead 10:08:57Z ruling 3):
 - k_sh = K_js5 (unchanged: reproduces js5's PRELOAD shell pull 2631.2 N at 3750 N / 0.078 with the model's k_c);
 - k_b RE-CALIBRATED to js5 SOAK70 (FEA3D js5_mu0_T3750_g078 step SOAK70 = GVLO B1_70.7 mapped, unpressurised: head force 5694.7 N,
   fit radial 1400.7 N, F_sh 4294.0 N): the model's screw force at the GVLO frame nearest 70.7 s (3750 N, 0.078, no embedding, no set)
   equals 5694.7 N.  The model's F_sh / F_c split at that state is reported against the FE (4294.0 / 1400.7);
 - seat-line stress sigma = c F_sh_model with c anchored on the FE at BOTH FE states: c_pre = 226.5 / 2631.2 (PRELOAD) and
   c_soak = 345.7 / F_sh_model(SOAK70) (SOAK70, the 1-of-54 seat line d+6.05 z'0); the cap uses c = max(c_pre, c_soak) (more set =
   more preload loss = conservative); the ring line (288.3 at SOAK70) runs beside it as information;
 - SCREW PLASTIC SET (ruling 3): at SOAK70 the screw carries seat-tilt bending (FEA3D screw_bend.json: M 1151-1281 N mm along the
   shank, V <= 34 N; PRELOAD M 61-201 N mm).  The tilt moment is interpolated linearly in the model's F_sh between the two FE states
   (max section moment: 201.1 at PRELOAD, 1280.7 at SOAK70), the section tension is the head force x 1.019 (FE max section N / head
   force at PRELOAD; 1.015 at SOAK70); fibre stress = N / A_s + M / Z_3 (A_s 14.18, Z_3 6.373, as FEA3D).  Where it exceeds
   kT Rp0.2 at the screw temperature (taken = T01, the FE puts the screw at 158.6 C in SOAK70, the model's row mean T01 is the closer
   proxy: conservative), the screw takes a permanent axial set delta_p grown until the fibre stress equals kT Rp0.2: an UPPER BOUND
   (the whole section is stretched by the fibre's excess, not only the yielded fibres), carried like embedding: F_S = F_V +
   k_b (d_w - f - delta_p + u - u0).  The wall set s (seat cap) and delta_p are solved together at every frame;
 - shakedown of the screw fibre: elastic fibre range over the second firing (cold to its maximum) vs 2 kT Rp0.2 at the hot end;
   the fibre stress history is written for the screw LCF (b package);
 - soak membrane yield under the head-bearing edge (FEA3D SOAK70: 12 of 54 seat lines Pm > Fty(T) at z' +-3, max 1.064): its
   treatment is stated from the capped states (see 'membrane_yield'); a +1 um extra-embedding sensitivity row bounds it;
 - break-even k_sh (first of the 24 cases slack), with k_b re-calibrated to SOAK70 at each trial k_sh and c unchanged (the FE stress
   per unit pull), compared with 33.4 (K_js5) and 35.64 (js4 56 x (2.688 / 3.125)^3, lead);
 - (a) gap at which the seat line reaches 2 Fty(T) at 3750 and 4096 N with the FE coefficient 345.7 / 4294.0 at SOAK70 (lead
   09:45Z), the model giving dF_sh / dg and dF_sh / dF_V about the FE state;
 - SOAK and SOAK52 (FEA3D steps 5-6) re-run when they land (the script reads them if present and reports them; not yet landed).
Joint model (jfwd_embed_v352 head, executed): F_sh = k_sh (g - s + d_r - u); F_c = k_c (-u) for u < 0; F_S = F_V + k_b (d_w - f -
delta_p + u - u0); equilibrium F_S = F_sh + F_c; F_S <= 0 = slack.  Frames: rev-4 B1 row histories at the J-FWD screw plane
(v352_NF2b_R4_GVLO / _GVHI), every frame, then a cold frame (20 C), two consecutive firings; embedding f_Z basis 8 / sensitivity 21 um
from the first frame; installations 2250 / 4096 N; gaps 0.040 / 0.059 / 0.078; 2 x 3 x 2 x 2 = 24 cases on the seat line."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
OUT = J / "jfwd_relax_v352_v3.json"
JS5_RELAX = Path("/home/claude/work/fea3d/jfwd/runs/js5_mu0_T3750_g078/relax_partial.json")
SCREW_BEND = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352/jfwd_interim/js5_mu0_T3750_g078_upto4_screw_bend.json")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
SRC = (J / "jfwd_embed_v352.py").read_text().split("# ---- embedding: residual preload")[0]
NS = {"__file__": str(J / "jfwd_embed_v352.py")}
exec(compile(SRC, str(J / "jfwd_embed_v352.py") + "(head)", "exec"), NS)
deltas, K_C, FZ, tab, T_BURN_END, kT = (NS[k] for k in ("deltas", "K_C", "FZ", "tab", "T_BURN_END", "kT"))
a_al, L_G, R_FIT = NS["a_al"], NS["L_G"], NS["R_FIT"]
Z_ROW, DZ_ROW, R_TAP = NS["Z_ROW"], NS["DZ_ROW"], NS["R_TAP"]
K_B_JS4 = NS["K_B"]

_j5 = json.loads(JS5_RELAX.read_text())
_sb = json.loads(SCREW_BEND.read_text())
SP = _j5["shell_pull"]
FE = {"PRELOAD": {"F_S": SP["PRELOAD"]["screw_force_N"], "F_fit": SP["PRELOAD"]["FIT_radial_N"], "F_sh": SP["PRELOAD"]["F_sh_N"]},
      "SOAK70": {"F_S": SP["SOAK70"]["screw_force_N"], "F_fit": SP["SOAK70"]["FIT_radial_N"], "F_sh": SP["SOAK70"]["F_sh_N"]}}
assert abs(FE["SOAK70"]["F_S"] - 5694.7) < 0.05 and abs(FE["SOAK70"]["F_sh"] - 4294.0) < 0.05
seat70 = _j5["steps"]["SOAK70"]["families"]["seat"]
ring70 = _j5["steps"]["SOAK70"]["families"]["ring"]
SEAT_PQ = seat70["governing_by_soak_PQ"]
assert abs(SEAT_PQ["preload_plus_soak"]["PmPb"] - 345.7) < 0.05 and abs(SEAT_PQ["preload_only"]["PmPb"] - 226.5) < 0.05
RING_PQ = ring70["governing_by_soak_PQ"]
SEAT_PM = seat70["governing_by_soak_Pm"]
LANDED = {k: bool(_j5["steps"][k]["soak_landed"]) for k in _j5["steps"]}
FV0, G0 = 3750.0, 0.078
K_SH_JS5 = FE["PRELOAD"]["F_sh"] / (G0 + FE["PRELOAD"]["F_fit"] / K_C)
GAPS = {"H8f7_min": 0.040, "H8f7_mean": 0.059, "H8f7_max": 0.078}
INSTALL = {"J-F1_min_2250": 2250.0, "J-F1_max_4096": 4096.0}
EMB = {"basis": FZ["a_spot_face"]["basis_um"] * 1e-3, "sens": FZ["a_spot_face"]["sens_um"] * 1e-3}
# screw section (FEA3D's values) and the A4-80 proxy
A_S, Z_3, E_S20 = 14.18, math.pi * 4.019 ** 3 / 32.0, 193000.0
L_FREE = L_G + 0.5                                  # free screw length credited for the plastic set (grip + uncredited tap mouth)
RP20 = 600.0
M_TILT = {"PRELOAD": max(s["M"] for s in _sb["steps"]["PRELOAD"]["sections"]), "SOAK70": max(s["M"] for s in _sb["steps"]["SOAK70"]["sections"])}
N_RATIO = max(max(s["N"] for s in _sb["steps"]["PRELOAD"]["sections"]) / FE["PRELOAD"]["F_S"],
              max(s["N"] for s in _sb["steps"]["SOAK70"]["sections"]) / FE["SOAK70"]["F_S"])


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


class Screw:
    """screw material / size for the joint model: thermal strain over its grip, stiffness ratio on k_b (applied by the caller), Rp0.2(T),
    the section (A_s, Z_3) for the fibre cap and the grip length L_g (default the model's L_G)."""
    def __init__(self, name, alpha_mat, E_ratio, rp, rp_src, A_s=None, Z_3=None, L_g=None, kb_ratio=None, tilt_ratio=None):
        self.name, self.alpha_mat, self.E_ratio, self.rp, self.rp_src = name, alpha_mat, E_ratio, rp, rp_src
        self.A_s = A_s if A_s is not None else 14.18
        self.Z_3 = Z_3 if Z_3 is not None else math.pi * 4.019 ** 3 / 32.0
        self.L_g = L_g if L_g is not None else L_G
        self.kb_ratio = kb_ratio if kb_ratio is not None else E_ratio
        self.tilt_ratio = tilt_ratio if tilt_ratio is not None else E_ratio     # imposed seat rotation: M scales with the screw E I

    def deltas(self, T01, T02):
        Ts = 0.5 * (T01 + T02)
        dw = (a_al(T01) * (T01 - 20.0) - tab(self.alpha_mat, "alpha", Ts) * (Ts - 20.0)) * self.L_g
        dr = a_al(Ts) * (T01 - T02) * R_FIT
        return Ts, dw, dr


A4_80 = Screw("A4-80", "SS316L", 1.0, lambda T: RP20 * kT(T), "ISO 3506-1 class 80 minimum 600 MPa x SS316L Fty(T) ratio (engmat; FEA3D's proxy)")
TILT = {"mode": "Fsh"}      # 'Fsh': tilt moment on the capped shell pull (v3 basis); 'kin': on the elastic-equivalent pull F_sh + k_sh s (seat rotation
                            # follows the total wall deflection, the screw-conservative bound)


def u_install(FV, g, ksh):
    return g - FV / ksh if FV <= ksh * g else -(FV - ksh * g) / (ksh + K_C)


def state_s(FV, g, dw, dr, f, s, ksh, kb):
    """screw force, wall position, fit contact, shell pull with wall set s and total axial loss f (embedding + screw set)."""
    u0 = u_install(FV, g, ksh)
    N = ksh * (g - s + dr) - FV - kb * (dw - f) + kb * u0
    u = N / (kb + ksh + K_C) if N < 0.0 else N / (kb + ksh)
    FS = FV + kb * (dw - f + u - u0)
    Fsh = ksh * (g - s + dr - u)
    Fc = -K_C * u if u < 0.0 else 0.0
    return FS, u, Fc, Fsh


GV70 = "GVLO"
_t, _a, _c = ROWS4[GV70]
I70 = int(np.argmin(np.abs(_t - 70.7)))
T70 = (float(_a[I70]), float(_c[I70]))


def calib_kb(ksh, scr=A4_80):
    _, dw, dr = A4_80.deltas(*T70)                 # the FE screw is A4-80: k_b is calibrated with A4-80 thermal strain
    lo, hi = 1.0e3, 5.0e7
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if state_s(FV0, G0, dw, dr, 0.0, 0.0, ksh, mid)[0] < FE["SOAK70"]["F_S"]:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


K_B5 = calib_kb(K_SH_JS5)
_, DW70, DR70 = A4_80.deltas(*T70)
S70 = state_s(FV0, G0, DW70, DR70, 0.0, 0.0, K_SH_JS5, K_B5)
S00 = state_s(FV0, G0, 0.0, 0.0, 0.0, 0.0, K_SH_JS5, K_B5)
C_PRE = 226.5 / S00[3]
C_SOAK = 345.7 / S70[3]
C_SEAT = max(C_PRE, C_SOAK)
C_RING = max(166.6 / S00[3], RING_PQ["preload_plus_soak"]["PmPb"] / S70[3])
C_FE70 = 345.7 / FE["SOAK70"]["F_sh"]


def m_tilt(Fsh, fsh_pre=None, fsh_70=None):
    a = S00[3] if fsh_pre is None else fsh_pre
    b = S70[3] if fsh_70 is None else fsh_70
    return M_TILT["PRELOAD"] + (M_TILT["SOAK70"] - M_TILT["PRELOAD"]) * (Fsh - a) / (b - a)


def fibre(FS, Fsh, scr=None, s=0.0, ksh=0.0):
    """screw fibre stress N / A_s + M_tilt / Z_3; the tilt is taken on the capped pull ('Fsh') or on the elastic-equivalent pull
    F_sh + k_sh s ('kin'); the section is the screw's (A4-80 M5 default = FEA3D's A_s 14.18 / Z_3 6.373)."""
    a_s, z_3, tr = (A_S, Z_3, 1.0) if scr is None else (scr.A_s, scr.Z_3, scr.tilt_ratio)
    ft = Fsh + (ksh * s if TILT["mode"] == "kin" else 0.0)
    return N_RATIO * FS / a_s + tr * max(m_tilt(ft), 0.0) / z_3


def fire(FV, g, f, fr, s0, dp0, c, ksh, kb, scr=A4_80, screw_set=True, cap=True):
    """one firing (every frame, then a cold frame) from wall set s0 and screw set dp0."""
    t, T01, T02 = fr
    s, dp = s0, dp0
    rec = []
    for i in list(range(len(t))) + [None]:
        if i is None:
            a_, b_, dw, dr, ti = 20.0, 20.0, 0.0, 0.0, "cold"
        else:
            a_, b_ = float(T01[i]), float(T02[i])
            _, dw, dr = scr.deltas(a_, b_)
            ti = round(float(t[i]), 3)
        Fy = float(tab("AL6061-T6", "Fty", a_))
        Rp = scr.rp(a_)
        wy = sy = False
        for _ in range(60):                     # joint fixed point of the two caps (both sets only grow)
            FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            changed = False
            if cap and FS > 0.0 and c * Fsh > Fy * (1 + 1e-9):
                lo, hi = s, s + 1.0
                for _ in range(100):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if c * state_s(FV, g, dw, dr, f + dp, mid, ksh, kb)[3] > Fy else (lo, mid)
                s, wy, changed = hi, True, True
                FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            if screw_set and FS > 0.0 and fibre(FS, Fsh, scr, s, ksh) > Rp * (1 + 1e-9):
                lo, hi = dp, dp + 0.2
                for _ in range(100):
                    mid = 0.5 * (lo + hi)
                    q = state_s(FV, g, dw, dr, f + mid, s, ksh, kb)
                    lo, hi = (mid, hi) if fibre(q[0], q[3], scr, s, ksh) > Rp else (lo, mid)
                dp, sy, changed = hi, True, True
                FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            if not changed:
                break
        rec.append({"t": ti, "T01": a_, "T02": b_, "FS": FS, "Fsh": Fsh, "Fc": Fc, "u": u, "sig": c * Fsh, "Fty": Fy, "set": s,
                    "dp": dp, "fib": fibre(FS, Fsh, scr, s, ksh) if FS > 0 else 0.0, "Rp": Rp, "wyield": wy, "syield": sy, "slack": FS <= 0.0})
    return rec, s, dp


def summary(rec):
    j = min(range(len(rec)), key=lambda k: rec[k]["FS"])
    r = rec[j]
    jf = max(range(len(rec)), key=lambda k: rec[k]["fib"])
    return {"F_S_min_N": round(r["FS"]), "at_t_s": r["t"], "T01_T02_C": [round(r["T01"], 1), round(r["T02"], 1)],
            "fit_at_min": "closed" if r["Fc"] > 0 else ("SLACK" if r["slack"] else "open"),
            "slack_frames": int(sum(1 for q in rec if q["slack"])), "wall_yield_frames": int(sum(1 for q in rec if q["wyield"])),
            "screw_yield_frames": int(sum(1 for q in rec if q["syield"])),
            "wall_set_end_um": round(rec[-1]["set"] * 1e3, 3), "screw_set_end_um": round(rec[-1]["dp"] * 1e3, 3),
            "cold_end_F_S_N": round(rec[-1]["FS"]), "F_S_max_N": round(max(q["FS"] for q in rec)),
            "max_sig_over_Fty": round(max(q["sig"] / q["Fty"] for q in rec), 3),
            "fibre_max_MPa": round(rec[jf]["fib"], 1), "fibre_max_at": rec[jf]["t"], "fibre_min_MPa": round(min(q["fib"] for q in rec), 1),
            "Rp_at_fibre_max_MPa": round(rec[jf]["Rp"], 1)}


def run_case(FV, g, f, fr, c, ksh, kb, scr=A4_80, screw_set=True, cap=True):
    rec1, s1, d1 = fire(FV, g, f, fr, 0.0, 0.0, c, ksh, kb, scr, screw_set, cap)
    rec2, s2, d2 = fire(FV, g, f, fr, s1, d1, c, ksh, kb, scr, screw_set, cap)
    FS_cold0 = state_s(FV, g, 0.0, 0.0, f, 0.0, ksh, kb)[0]
    f2 = summary(rec2)
    j2 = max(range(len(rec2)), key=lambda k: rec2[k]["fib"])
    rng = rec2[j2]["fib"] - min(q["fib"] for q in rec2)
    return {"gap_mm": g, "F_install_N": FV, "embedding_um": round(f * 1e3, 1), "k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb),
            "c_MPa_per_N": round(c, 5), "screw": scr.name, "installed_cold_after_embedding_N": round(FS_cold0),
            "firing_1": summary(rec1), "firing_2": f2,
            "wall_set_after_firing_1_um": round(s1 * 1e3, 3), "wall_set_after_firing_2_um": round(s2 * 1e3, 3),
            "screw_set_after_firing_1_um": round(d1 * 1e3, 3), "screw_set_after_firing_2_um": round(d2 * 1e3, 3),
            "relaxation_loss_cold_N": round(FS_cold0 - rec1[-1]["FS"]),
            "heads_seated_both_firings": not any(q["slack"] for q in rec1 + rec2),
            "second_firing_elastic": (s2 - s1) < 1e-9 and (d2 - d1) < 1e-9,
            "screw_shakedown": {"fibre_range_firing2_MPa": round(rng, 1), "two_kT_Rp_hot_MPa": round(2.0 * rec2[j2]["Rp"], 1),
                                "MS": round(2.0 * rec2[j2]["Rp"] / max(rng, 1e-9) - 1.0, 3)},
            "_rec2": rec2}


def run24(ksh, kb, c, scr=A4_80, screw_set=True, extra_f=0.0, keep=False, cap=True):
    out = {}
    for gn, g in GAPS.items():
        for iname, FV in INSTALL.items():
            for en, f in EMB.items():
                for gv, fr in ROWS4.items():
                    r = run_case(FV, g, f + extra_f, fr, c, ksh, kb, scr, screw_set, cap)
                    if not keep:
                        r.pop("_rec2")
                    out[f"{gn}|{iname}|{en}|{gv}"] = r
    return out


def run_grid(gaps, installs, ksh, kb, c, scr=A4_80, screw_set=True, cap=True, emb=None, rows=None):
    """the 24-case product over any gap / installation set (select-fit and preload sweeps)."""
    out = {}
    for gn, g in gaps.items():
        for iname, FV in installs.items():
            for en, f in (emb or EMB).items():
                for gv, fr in (rows or ROWS4).items():
                    r = run_case(FV, g, f, fr, c, ksh, kb, scr, screw_set, cap)
                    r.pop("_rec2")
                    out[f"{gn}|{iname}|{en}|{gv}"] = r
    return out


def vsum(d):
    def mn(x):
        return min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"])
    j = min(d, key=lambda k: mn(d[k]))
    jf = max(d, key=lambda k: d[k]["firing_2"]["fibre_max_MPa"] / max(d[k]["firing_2"]["Rp_at_fibre_max_MPa"], 1e-9))
    return {"all_seated": all(x["heads_seated_both_firings"] for x in d.values()), "n_cases": len(d),
            "F_S_max_N": max(max(x["firing_1"]["F_S_max_N"], x["firing_2"]["F_S_max_N"]) for x in d.values()),
            "fibre_over_Rp_max": round(d[jf]["firing_2"]["fibre_max_MPa"] / d[jf]["firing_2"]["Rp_at_fibre_max_MPa"], 3),
            "fibre_over_Rp_max_case": jf,
            "max_seat_over_Fty": max(max(x["firing_1"]["max_sig_over_Fty"], x["firing_2"]["max_sig_over_Fty"]) for x in d.values()),
            "n_unseated": sum(1 for x in d.values() if not x["heads_seated_both_firings"]),
            "unseated_cases": [k for k, x in d.items() if not x["heads_seated_both_firings"]],
            "min_case": j, "F_S_min_N": mn(d[j]),
            "max_wall_set_um": max(x["wall_set_after_firing_2_um"] for x in d.values()),
            "max_screw_set_um": max(x["screw_set_after_firing_2_um"] for x in d.values()),
            "max_cold_loss_N": max(x["relaxation_loss_cold_N"] for x in d.values()),
            "all_second_firing_elastic": all(x["second_firing_elastic"] for x in d.values()),
            "n_second_firing_not_elastic": sum(1 for x in d.values() if not x["second_firing_elastic"]),
            "screw_shakedown_min_MS": min(x["screw_shakedown"]["MS"] for x in d.values()),
            "screw_fibre_max_MPa": max(x["firing_2"]["fibre_max_MPa"] for x in d.values()),
            "screw_fibre_range_max_MPa": max(x["screw_shakedown"]["fibre_range_firing2_MPa"] for x in d.values()),
            "cold_end_F_S_min_N": min(x["firing_2"]["cold_end_F_S_N"] for x in d.values())}


if __name__ == "__main__":
    res = {"id": "jfwd_relax_v352", "version": "v3", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {"jfwd_embed_v352.py": sha(J / "jfwd_embed_v352.py"),
                      "js5_relax_partial_json": {"path": str(JS5_RELAX), "sha256_16_at_read": sha(JS5_RELAX), "steps_landed": LANDED},
                      "js5_screw_bend_json": {"path": str(SCREW_BEND), "sha256_16_at_read": sha(SCREW_BEND)},
                      "FE_states": FE, "rows": SRC4, "k_c_N_mm": round(K_C), "k_sh_K_js5_N_mm": round(K_SH_JS5),
                      "k_b_js4_N_mm_v2": round(K_B_JS4), "embedding_um": {k: v * 1e3 for k, v in EMB.items()},
                      "screw_section": {"A_s_mm2": A_S, "Z_3_mm3": round(Z_3, 3), "L_free_mm": round(L_FREE, 3), "N_ratio": round(N_RATIO, 4),
                                        "M_tilt_max_section_Nmm": M_TILT}}}
    cal = {"frame": {"bound": GV70, "t_s": round(float(_t[I70]), 3), "T01_C": round(T70[0], 1), "T02_C": round(T70[1], 1),
                     "d_w_um": round(DW70 * 1e3, 2), "d_r_um": round(DR70 * 1e3, 2)},
           "k_b_N_mm": round(K_B5), "k_b_over_js4": round(K_B5 / K_B_JS4, 3),
           "model_at_SOAK70": {"F_S_N": round(S70[0], 1), "F_sh_N": round(S70[3], 1), "F_fit_N": round(S70[2], 1), "u_um": round(S70[1] * 1e3, 3)},
           "FE_SOAK70": FE["SOAK70"],
           "split_error": {"F_sh_N": round(S70[3] - FE["SOAK70"]["F_sh"], 1), "F_fit_N": round(S70[2] - FE["SOAK70"]["F_fit"], 1)},
           "model_at_PRELOAD": {"F_S_N": round(S00[0], 1), "F_sh_N": round(S00[3], 1), "F_fit_N": round(S00[2], 1)},
           "c_seat_MPa_per_N": {"c_pre": round(C_PRE, 5), "c_soak_on_model_F_sh": round(C_SOAK, 5), "used": round(C_SEAT, 5), "c_FE_SOAK70": round(C_FE70, 5)},
           "c_ring_used": round(C_RING, 5),
           "seat_line_FE_T_C": SEAT_PQ["T_soak_mean_C"], "model_T01_at_frame_C": round(T70[0], 1)}
    res["calibration_SOAK70"] = cal
    # ---- (b) the 24 cases: seat bound with screw plastic set (governing), without screw set (v2 form), ring line (information)
    gov = run24(K_SH_JS5, K_B5, C_SEAT, A4_80, True)
    nos = run24(K_SH_JS5, K_B5, C_SEAT, A4_80, False)
    rng = run24(K_SH_JS5, K_B5, C_RING, A4_80, True)
    emb1 = run24(K_SH_JS5, K_B5, C_SEAT, A4_80, True, extra_f=0.001)
    res["b_seat_screwset"] = gov
    res["b_seat_no_screwset_info"] = nos
    res["b_ring_screwset_info"] = rng
    res["b_seat_screwset_plus1um_membrane_bound"] = emb1
    res["verdict"] = {"b_seat_line_K_js5_SOAK70_with_screw_set": vsum(gov), "b_seat_line_without_screw_set_info": vsum(nos),
                      "b_ring_line_info": vsum(rng), "b_seat_plus_1um_extra_embedding": vsum(emb1)}
    # ---- membrane yield under the head-bearing edge: Pm at the capped states
    caps = []
    for k, v in gov.items():
        for fn in ("firing_1", "firing_2"):
            pass
    # the capped soak state of the governing case family: F_sh at first yield of the seat line at the SOAK70 line temperature
    fy70 = float(tab("AL6061-T6", "Fty", T70[0]))
    fsh_cap70 = fy70 / C_SEAT
    pm_fe = SEAT_PM["preload_plus_soak"]["Pm"]
    pm_fty = SEAT_PM["preload_plus_soak"]["Pm_over_Fty"]
    res["membrane_yield"] = {
        "FE_SOAK70": {"n_lines_Pm_gt_Fty": seat70["n_lines_soak_Pm_gt_Fty"], "governing_line": SEAT_PM["line"], "Pm_MPa": pm_fe, "Pm_over_Fty": pm_fty,
                      "F_sh_FE_N": FE["SOAK70"]["F_sh"], "F_S_FE_N": FE["SOAK70"]["F_S"]},
        "capped_state_SOAK70": {"F_sh_cap_N": round(fsh_cap70, 1),
                                "Pm_over_Fty_if_Pm_scales_with_F_sh": round(pm_fty * fsh_cap70 / S70[3], 3)},
        "extra_embedding_bound_um": round((pm_fty - 1.0) * SEAT_PM["Fty_T_MPa"] / tab("AL6061-T6", "E", SEAT_PM["T_soak_mean_C"]) * SEAT_PM["t_mm"] * 1e3, 3)}
    # Pm with the head force: the capped head force of the max-set governing case at its hottest frame
    # ---- break-even k_sh.  v3 fix (10:50Z): the first v3 pass bisected upward from K_js5 although K_js5 itself is slack, so it returned
    #      K_js5; the search now brackets the largest all-seated k_sh on whichever side of K_js5 it lies (geometric bisection, k_b
    #      re-calibrated to SOAK70 at every trial), for the seat-line and the ring-line bounds.
    def any_slack(ksh, c):
        kb = calib_kb(ksh)
        v = vsum(run24(ksh, kb, c, A4_80, True))
        return (not v["all_seated"]), v, kb

    def break_even(c, label):
        s0, v0, kb0 = any_slack(K_SH_JS5, c)
        out = {"bound": label, "at_K_js5": {"slack": s0, "n_unseated": v0["n_unseated"], "F_S_min_N": v0["F_S_min_N"], "k_b": round(kb0)}}
        if s0:
            lo, hi = 1000.0, K_SH_JS5
            sl, vl, _ = any_slack(lo, c)
            out["at_1000"] = {"slack": sl, "F_S_min_N": vl["F_S_min_N"]}
            if sl:
                out["k_sh_break_even_N_mm"] = "< 1000 (slack at every k_sh tried)"
                return out
        else:
            lo, hi = K_SH_JS5, 120000.0
            sh, vh, _ = any_slack(hi, c)
            out["at_120000"] = {"slack": sh, "F_S_min_N": vh["F_S_min_N"]}
            if not sh:
                out["k_sh_break_even_N_mm"] = "> 120000 (no case slack)"
                return out
        for _ in range(24):
            mid = math.sqrt(lo * hi)
            s_, _, _ = any_slack(mid, c)
            lo, hi = (lo, mid) if s_ else (mid, hi)
        _, vb, _ = any_slack(hi, c)
        _, va, kba = any_slack(lo, c)
        out.update({"k_sh_break_even_N_mm": round(lo), "k_b_at_break_even": round(kba), "F_S_min_at_break_even_N": va["F_S_min_N"],
                    "first_slack_cases_just_above": vb["unseated_cases"][:3],
                    "vs_K_js5_33433": round(lo / K_SH_JS5 - 1.0, 3), "vs_js4_scaled_35640": round(lo / 35640.0 - 1.0, 3)})
        return out
    res["break_even_k_sh"] = {"seat_line": break_even(C_SEAT, "seat line (c = max(c_pre, c_soak))"),
                              "ring_line": break_even(C_RING, "ring line (information bound)")}
    be = res["break_even_k_sh"]
    # ---- (a) gap at which the seat line reaches 2 Fty(T) at SOAK70 with the FE coefficient
    fy_line = SEAT_PQ["Fty_T_MPa"]
    ga = {}
    for FV in (3750.0, 4096.0):
        def fsh_fe(g):
            return FE["SOAK70"]["F_sh"] + (state_s(FV, g, DW70, DR70, 0.0, 0.0, K_SH_JS5, K_B5)[3] - S70[3])
        lo_, hi_ = 0.0, 0.2
        for _ in range(100):
            mid = 0.5 * (lo_ + hi_)
            lo_, hi_ = (mid, hi_) if C_FE70 * fsh_fe(mid) < 2.0 * fy_line else (lo_, mid)
        ga[f"{FV:.0f}N"] = {"g_at_2Fty_mm": round(0.5 * (lo_ + hi_), 5), "F_sh_FE_at_g_N": round(fsh_fe(0.5 * (lo_ + hi_)), 1),
                            "seat_PQ_at_0.078_MPa": round(C_FE70 * fsh_fe(0.078), 1), "MS_PQ_at_0.078": round(2.0 * fy_line / (C_FE70 * fsh_fe(0.078)) - 1.0, 4),
                            "MS_PQ_at_0.059": round(2.0 * fy_line / (C_FE70 * fsh_fe(0.059)) - 1.0, 4),
                            "MS_PQ_at_0.040": round(2.0 * fy_line / (C_FE70 * fsh_fe(0.040)) - 1.0, 4)}
    res["a_gap_at_2Fty_SOAK70"] = {"c_FE_MPa_per_N": round(C_FE70, 6), "line_T_C": SEAT_PQ["T_soak_mean_C"], "Fty_T_MPa": fy_line,
                                   "two_Fty_MPa": 2.0 * fy_line, "dFsh_dg_N_per_mm_model": round((state_s(3750.0, 0.079, DW70, DR70, 0, 0, K_SH_JS5, K_B5)[3]
                                                                                                    - state_s(3750.0, 0.077, DW70, DR70, 0, 0, K_SH_JS5, K_B5)[3]) / 0.002),
                                   "rows": ga}
    # ---- screw plastic set bounds (ruling 3).  The v3 basis interpolates the tilt moment on the CAPPED shell pull: once the seat line yields,
    #      F_sh falls to Fty / c (1986.6 N at the SOAK70 frame) below the PRELOAD pull, so the tilt falls with it and no screw set results.
    #      Two screw-conservative bounds beside it: (k) the tilt follows the elastic-equivalent pull F_sh + k_sh s (the seat rotation follows
    #      the total wall deflection, plastic hinge at the seat line), (w) the wall stays elastic (no seat-line cap) and the screw takes the
    #      set (the FE's elastic SOAK70 state: fibre 570 MPa > kT Rp 447).
    TILT["mode"] = "kin"
    kin = run24(K_SH_JS5, K_B5, C_SEAT, A4_80, True)
    TILT["mode"] = "Fsh"
    wel = run24(K_SH_JS5, K_B5, C_SEAT, A4_80, True, cap=False)
    res["b_seat_screwset_tilt_kinematic"] = kin
    res["b_wall_elastic_screw_takes_set"] = wel
    res["screw_set_bounds"] = {"v3_basis_tilt_on_capped_pull": vsum(gov), "tilt_on_elastic_equivalent_pull": vsum(kin),
                               "wall_elastic_screw_takes_the_set": vsum(wel)}
    # ---- (c) screw options: no-slack, all 24 cases, both bounds (lead 10:47Z item 3).  Grade options keep the geometry (k_sh, c); the
    #      screw changes k_b by its E (k_b x E ratio, upper bound: the calibrated k_b is treated as all screw), its thermal strain over the
    #      grip (alpha) and its fibre cap (Rp0.2(T)).  Size options are ESTIMATES (no FE): M6 = wall 2.600 under a d11.5 spot face (k_sh x
    #      (2.600 / 2.688)^3, the lead's js4 -> js5 form; c x (2.688 / 2.600)^2, wall bending; k_b x 1.275 = (A_s / L_eff) ratio with L_eff =
    #      grip + 0.4 d + 0.5 d; grip x 2.625 / 2.713; tilt moment x (d3 ratio)^4 for the same imposed seat rotation); 12x M5 = the same
    #      local joint per screw (k_sh x 1) and a ring-dominated shell bound (k_sh x 10 / 12).
    E20 = {"A4": 193000.0, "IN718": tab("IN718", "E", 20.0)}
    A4_100 = Screw("A4-100", "SS316L", 1.0, lambda T: 800.0 * kT(T),
                   "property class 100 minimum Rp0.2 800 MPa (ISO 3506-1:2020 class 100: TO-VERIFY; no M5 head part found) x SS316L Fty(T) ratio")
    IN718_S = Screw("IN718", "IN718", E20["IN718"] / E20["A4"], lambda T: tab("IN718", "Fty", T),
                    "IN718 AMS 5662/5663 minimum Fty(T) (Special Metals SMC-045, DATASHEET in engmat; linear 20-649 C)")
    L_EFF5, L_EFF6 = (2.688 + 0.025) + 0.4 * 5.0 + 0.5 * 5.0, (2.600 + 0.025) + 0.4 * 6.0 + 0.5 * 6.0
    KB_M6 = (20.12 / L_EFF6) / (14.18 / L_EFF5)
    M6_S = Screw("M6 A4-80", "SS316L", 1.0, lambda T: RP20 * kT(T), "as A4-80 (ISO 3506-1 class 80)", A_s=20.12, Z_3=math.pi * 4.773 ** 3 / 32.0,
                 L_g=L_G * (2.600 + 0.025) / (2.688 + 0.025), kb_ratio=KB_M6, tilt_ratio=(4.773 / 4.019) ** 4)
    OPTS = {"A4-80 M5 x10 (baseline)": (A4_80, 1.0, 1.0, "FE-calibrated"),
            "A4-100 M5 x10": (A4_100, 1.0, 1.0, "grade: same alpha / E as A4-80"),
            "IN718 M5 x10": (IN718_S, 1.0, 1.0, "grade: alpha IN718, k_b x E ratio"),
            "A4-80 M6 x10": (M6_S, (2.600 / 2.688) ** 3, (2.688 / 2.600) ** 2, "ESTIMATE (no FE)"),
            "A4-80 12x M5 (local k_sh)": (A4_80, 1.0, 1.0, "ESTIMATE: per-screw joint unchanged"),
            "A4-80 12x M5 (ring k_sh x10/12)": (A4_80, 10.0 / 12.0, 1.0, "ESTIMATE: ring-dominated shell")}
    cand = {}
    for nm, (scr, kf, cf, tag) in OPTS.items():
        kb, ksh = K_B5 * scr.kb_ratio, K_SH_JS5 * kf
        cand[nm] = {"tag": tag, "screw": scr.name, "rp_src": scr.rp_src, "k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb),
                    "c_seat": round(C_SEAT * cf, 5), "c_ring": round(C_RING * cf, 5), "grip_mm": round(scr.L_g, 3), "tilt_ratio": round(scr.tilt_ratio, 3),
                    "seat_line": vsum(run24(ksh, kb, C_SEAT * cf, scr, True)), "ring_line": vsum(run24(ksh, kb, C_RING * cf, scr, True))}
    res["c_screw_options_no_slack"] = cand
    # ---- joint fix (i): select-fit gap cap (all 24 seated) per option, both bounds.  Band from 0 up; the cap is the largest gap at which
    #      every installation / embedding / GV case stays seated (bisection on a coarse sweep; monotonic in the sweep).
    def seated_at(g, scr, ksh, kb, c):
        return vsum(run_grid({f"g{g:.4f}": g}, INSTALL, ksh, kb, c, scr))

    def gap_cap(scr, ksh, kb, c):
        coarse = []
        for k in range(0, 17):
            g = 0.0025 * k
            v = seated_at(g, scr, ksh, kb, c)
            coarse.append({"gap_mm": round(g, 4), "all_seated": v["all_seated"], "n_unseated": v["n_unseated"], "F_S_min_N": v["F_S_min_N"],
                           "max_wall_set_um": v["max_wall_set_um"], "max_seat_over_Fty": v["max_seat_over_Fty"]})
        ok = [r["gap_mm"] for r in coarse if r["all_seated"]]
        if not ok or coarse[0]["all_seated"] is False:
            return {"g_cap_mm": None, "note": "slack even at zero radial gap", "sweep": coarse}
        first_bad = next((r["gap_mm"] for r in coarse if not r["all_seated"]), None)
        if first_bad is None:
            return {"g_cap_mm": ">= 0.040 (all seated over 0-0.040)", "sweep": coarse}
        lo, hi = first_bad - 0.0025, first_bad
        for _ in range(16):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if seated_at(mid, scr, ksh, kb, c)["all_seated"] else (lo, mid)
        return {"g_cap_mm": round(lo, 5), "contiguous_from_zero": all(r["all_seated"] for r in coarse if r["gap_mm"] <= lo), "sweep": coarse}
    sf = {}
    for nm, (scr, kf, cf, tag) in OPTS.items():
        kb, ksh = K_B5 * scr.kb_ratio, K_SH_JS5 * kf
        sf[nm] = {"seat_line": gap_cap(scr, ksh, kb, C_SEAT * cf), "ring_line": gap_cap(scr, ksh, kb, C_RING * cf)}
    res["fix_i_select_fit_gap_cap"] = sf
    # ---- joint fix (ii): higher installation preload (J-F1 band F_min .. F_max = 5/3 F_min, +/-25 % about F_nom), H8 / f7 gaps kept;
    #      the lowest F_min at which all 24 cases stay seated, per grade (the screw fibre cap is active in the run: a preload the screw cannot
    #      hold sets the screw); with the run's F_S max, fibre / Rp, seat ratio and wall set at that band.
    def preload_band(scr, ksh, kb, c, label):
        rows_ = []
        found = None
        for k in range(0, 41):
            fmin = 2250.0 + 250.0 * k
            v = vsum(run_grid(GAPS, {"F_min": fmin, "F_max": fmin * 5.0 / 3.0}, ksh, kb, c, scr))
            rows_.append({"F_min_N": fmin, "F_max_N": round(fmin * 5.0 / 3.0), "all_seated": v["all_seated"], "n_unseated": v["n_unseated"],
                          "F_S_min_N": v["F_S_min_N"], "F_S_max_N": v["F_S_max_N"], "fibre_over_Rp_max": v["fibre_over_Rp_max"],
                          "max_screw_set_um": v["max_screw_set_um"], "max_wall_set_um": v["max_wall_set_um"], "max_seat_over_Fty": v["max_seat_over_Fty"]})
            if v["all_seated"] and found is None:
                found = rows_[-1]
                break
        if found:
            fnom = found["F_min_N"] / 0.75
            found = dict(found, F_nom_N=round(fnom), torque_Nm_K0p20=round(0.20 * fnom * (6.0 if "M6" in scr.name else 5.0) * 1e-3, 2))
        return {"screw": label, "first_all_seated_band": found, "sweep": rows_}
    hp = {}
    for nm in ("A4-80 M5 x10 (baseline)", "A4-100 M5 x10", "IN718 M5 x10"):
        scr, kf, cf, tag = OPTS[nm]
        kb, ksh = K_B5 * scr.kb_ratio, K_SH_JS5 * kf
        hp[nm] = {"seat_line": preload_band(scr, ksh, kb, C_SEAT * cf, scr.name), "ring_line": preload_band(scr, ksh, kb, C_RING * cf, scr.name)}
    res["fix_ii_higher_preload"] = hp
    # ---- information sensitivities (not fixes): (1) the seat-line cap at the bending limit load (rectangular section shape factor 1.5 on
    #      the first-yield cap: elastic-perfectly-plastic hinge, the set starts at collapse), (2) a series compliance under the head (k_b x
    #      0.75 / 0.5 / 0.25 / 0.1: what a spring element or a longer grip would have to give), (3) the H8 / f7 range and beyond on the
    #      seat line (0.040-0.120: the pinned regime).
    info = {"seat_line_cap_at_limit_load_x1.5": vsum(run24(K_SH_JS5, K_B5, C_SEAT / 1.5, A4_80, True)),
            "kb_series_compliance": {f"k_b_x{f:g}": vsum(run24(K_SH_JS5, K_B5 * f, C_SEAT, A4_80, True)) for f in (0.75, 0.5, 0.25, 0.1)},
            "gap_sweep_0p040_0p120_seat_line": [dict(gap_mm=round(0.040 + 0.010 * k, 3),
                                                     **{kk: vv for kk, vv in seated_at(0.040 + 0.010 * k, A4_80, K_SH_JS5, K_B5, C_SEAT).items()
                                                        if kk in ("all_seated", "n_unseated", "F_S_min_N", "max_wall_set_um")}) for k in range(0, 9)]}
    res["info_sensitivities"] = info
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
    print(json.dumps(cal, indent=1))
    print(json.dumps(res["verdict"], indent=1))
    print(json.dumps(res["membrane_yield"], indent=1))
    print(json.dumps(be, indent=1))
    print(json.dumps(res["a_gap_at_2Fty_SOAK70"], indent=1))
    for k, v in gov.items():
        f1, f2 = v["firing_1"], v["firing_2"]
        print(f"{k:40s} cold0 {v['installed_cold_after_embedding_N']:5d} ws1 {v['wall_set_after_firing_1_um']:7.3f} ws2 {v['wall_set_after_firing_2_um']:7.3f} "
              f"ss1 {v['screw_set_after_firing_1_um']:6.3f} ss2 {v['screw_set_after_firing_2_um']:6.3f} loss {v['relaxation_loss_cold_N']:5d} | f1 min {f1['F_S_min_N']:5d} "
              f"| f2 min {f2['F_S_min_N']:5d} cold {f2['cold_end_F_S_N']:5d} fib {f2['fibre_max_MPa']:6.1f}/{f2['Rp_at_fibre_max_MPa']:5.1f} | seated "
              f"{v['heads_seated_both_firings']} el2 {v['second_firing_elastic']} sd {v['screw_shakedown']['MS']:+.3f}")
    print("== screw set bounds")
    for k, v in res["screw_set_bounds"].items():
        print(f"  {k:36s} unseated {v['n_unseated']:2d} min {v['F_S_min_N']:6d} screw set {v['max_screw_set_um']:7.3f} fibre max {v['screw_fibre_max_MPa']:6.1f} "
              f"fib/Rp {v['fibre_over_Rp_max']:.3f} range {v['screw_fibre_range_max_MPa']:6.1f} shakedown MS {v['screw_shakedown_min_MS']:+.3f} wall set {v['max_wall_set_um']:.1f}")
    print("== (c) options, no-slack 24 cases")
    for k, v in cand.items():
        a, b = v["seat_line"], v["ring_line"]
        print(f"  {k:34s} seat: unseated {a['n_unseated']:2d} min {a['F_S_min_N']:6d} set {a['max_wall_set_um']:6.1f} Fmax {a['F_S_max_N']:6d} fib/Rp {a['fibre_over_Rp_max']:.3f}"
              f" | ring: unseated {b['n_unseated']:2d} min {b['F_S_min_N']:6d}")
    print("== fix (i) select-fit gap cap")
    for k, v in sf.items():
        print(f"  {k:34s} seat g_cap {v['seat_line']['g_cap_mm']} | ring g_cap {v['ring_line']['g_cap_mm']}")
    print("== fix (ii) higher preload")
    for k, v in hp.items():
        for bnd in ("seat_line", "ring_line"):
            f = v[bnd]["first_all_seated_band"]
            print(f"  {k:28s} {bnd:9s}", "none up to 12250 N" if not f else
                  f"F_min {f['F_min_N']:.0f} F_max {f['F_max_N']} F_nom {f['F_nom_N']} T {f['torque_Nm_K0p20']} N m | F_S_max {f['F_S_max_N']} fib/Rp {f['fibre_over_Rp_max']} "
                  f"screw set {f['max_screw_set_um']} wall set {f['max_wall_set_um']} seat/Fty {f['max_seat_over_Fty']}")
    print("== information sensitivities")
    v = info["seat_line_cap_at_limit_load_x1.5"]
    print(f"  seat cap x1.5 (limit load): unseated {v['n_unseated']} min {v['F_S_min_N']} set {v['max_wall_set_um']}")
    for k, v in info["kb_series_compliance"].items():
        print(f"  {k}: unseated {v['n_unseated']} min {v['F_S_min_N']} set {v['max_wall_set_um']} cold-end min {v['cold_end_F_S_min_N']}")
    for r in info["gap_sweep_0p040_0p120_seat_line"]:
        print("  gap", r)
