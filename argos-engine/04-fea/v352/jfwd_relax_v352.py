"""J-FWD: TC-01 wall relaxation, screw plastic set and the no-slack check over two consecutive firings.
Mechanical, 2026-10-20, v4 (v3 48c2ab7d2698bb2f kept as jfwd_relax_v352_v3.py and imported for the shared joint machinery: Screw, state_s,
u_install, the rev-4 row histories, engmat tables; v2 / v1 kept).  CALC on SIM temperatures and SIM (FEA3D) calibration states; every number
DERIVED unless tagged.  H8 / f7 stays (lead 08:40Z).

v4 (lead 11:25Z items 1-4, lead 11:41Z):
 - SCREW RULED: IN718 M5 x10, ENG-HW-101-IN718 (AMS 5662 bar aged to AMS 5663, ISO 7380-1 form).  A4-80 is WITHDRAWN for J-FWD (its rows
   are information); M6 A4-80 is the FALLBACK (ESTIMATE rows, not a passed design).
 - FE inputs: the COMPLETE js5 run (hub jfwd_interim relax / seatforce / screw_bend / cells) and FEA3D's seat patch (a) seat_s5L8_mu0
   (run dir, read only): same mesh s5, mu 0, 3750 N, FIT 0.078, cut boundary driven by js5; step order SEAT-PRELOAD-SOAK52-SOAK-SOAK70-FA1S
   against js5's PRELOAD-SOAK70-FA1S-SOAK-SOAK52.  The patch reproduces js5 within 5 % at PRELOAD and FA1S; at the soak steps the state
   depends on the step history (sharp-corner penalty-contact non-uniqueness, lead 11:41Z).  RULED: until a history-robust model exists,
   every sharp-edge soak quantity is the WORST of the two histories, per state and per quantity: the highest screw N (SOAK 7383, SOAK52
   6560, SOAK70 6389), the lowest seat window force, the lowest MS per line, and (here) the highest screw section moment.
 - k_b BRACKET (lead 11:41Z): k_b,lo = the v3 calibration to js5 SOAK70 (head force 5694.7 N); k_b,hi = calibrated the same way to the
   patch SOAK70 (head force 6389.1 N; seat 2318.1 N main cluster, 2385.0 N window, 2430.0 N along n).  Every 24-case check runs at both
   ends and the worse is quoted.
 - model check against BOTH histories at SOAK70 / SOAK / SOAK52 (model = history free: one value per state).
 - c (P+Q per unit model shell pull) per family and per k_b end = the max over PRELOAD / SOAK70 / SOAK / SOAK52 of the worst-history
   FE P+Q divided by the model's F_sh at that state (seat line d+6.051 z'0; ring line d-8.126 z'3 with the patch's d-8.02 z'3 beside it).
 - TILT MOMENT (v4 basis 'Fc'; the v3 basis linear in the capped shell pull is WITHDRAWN: at SOAK / SOAK52 js5 carries 3849 / 2661 N mm
   at about the SOAK70 shell pull, where v3 gave 1281): soak moment = an upper-bound line in the seat contact force over the six soak FE
   points of both histories (max section moment along the shank, the threaded sections included), M_soak(F_c) = a + b F_c (b the
   least-squares slope, a raised until every point lies on or below the line); cold / preload moment M_pre(F_S) = the PRELOAD envelope
   moment x F_S / 3750; at a frame M = M_pre + w max(0, M_soak(F_c) - M_pre) with w = d_r / d_r(SOAK70) >= 0 (not capped above); the screw
   moment scales with the screw E (tilt ratio, as v3).  Fibre = N_ratio F_S / A_s + M / Z_3 with N_ratio the max section N / head force
   over all FE states of both histories.
 - shakedown, the fibre history for the screw LCF, embedding, the wall cap and the two-firing structure as v3.
Joint model (jfwd_embed_v352 head): F_sh = k_sh (g - s + d_r - u); F_c = k_c (-u) for u < 0; F_S = F_V + k_b (d_w - f - delta_p + u - u0);
equilibrium F_S = F_sh + F_c; F_S <= 0 = slack.  Frames: rev-4 B1 row histories at the J-FWD screw plane (v352_NF2b_R4_GVLO / _GVHI), every
frame, then a cold frame (20 C), two consecutive firings; embedding f_Z basis 8 / sensitivity 21 um; installations 2250 / 4096 N; gaps
0.040 / 0.059 / 0.078: 3 x 2 x 2 x 2 = 24 cases."""
import json, math, hashlib, sys, importlib.util
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_relax_v352_v4.json"
V3 = J / "jfwd_relax_v352_v3.py"
_spec = importlib.util.spec_from_file_location("jfwd_relax_v352_v3", str(V3))
RV3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RV3)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
state_s, u_install, Screw, A4_80, ROWS4, SRC4 = RV3.state_s, RV3.u_install, RV3.Screw, RV3.A4_80, RV3.ROWS4, RV3.SRC4
tab, kT, K_C, EMB, GAPS, INSTALL = RV3.tab, RV3.kT, RV3.K_C, RV3.EMB, RV3.GAPS, RV3.INSTALL
L_G, A_S, Z_3 = RV3.L_G, RV3.A_S, RV3.Z_3

HUBI = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352/jfwd_interim")
F_RELAX = HUBI / "js5_mu0_T3750_g078_relax.json"
F_SEATF = HUBI / "js5_mu0_T3750_g078_seatforce.json"
F_BEND = HUBI / "js5_mu0_T3750_g078_screw_bend.json"
F_CELLS = HUBI / "js5_mu0_T3750_g078_cells.json"
PATCH = Path("/home/claude/work/fea3d/jfwd/runs/seat_s5L8_mu0")
P_SEATF, P_CMP, P_RUNCMP, P_META = (PATCH / n for n in ("seatforce.json", "compare.json", "runcmp_js5_mu0_T3750_g078.json", "meta.json"))
INPUT_FILES = {"js5_relax": F_RELAX, "js5_seatforce": F_SEATF, "js5_screw_bend": F_BEND, "js5_cells": F_CELLS,
               "patch_a_seatforce": P_SEATF, "patch_a_compare": P_CMP, "patch_a_runcmp_vs_js5": P_RUNCMP, "patch_a_meta": P_META,
               "relax_v3_module": V3}

_rel = json.loads(F_RELAX.read_text())
_sfj, _sfp = json.loads(F_SEATF.read_text()), json.loads(P_SEATF.read_text())
_cmp, _rc = json.loads(P_CMP.read_text()), json.loads(P_RUNCMP.read_text())
_meta = json.loads(P_META.read_text())
SP = _rel["shell_pull"]
FE = {k: {"F_S": SP[k]["screw_force_N"], "F_fit": SP[k]["FIT_radial_N"], "F_sh": SP[k]["F_sh_N"]} for k in ("PRELOAD", "SOAK70", "SOAK", "SOAK52")}
assert abs(FE["SOAK70"]["F_S"] - 5694.7) < 0.05 and abs(FE["SOAK"]["F_S"] - 7382.8) < 0.05 and abs(FE["SOAK52"]["F_S"] - 6559.9) < 0.05
FV0, G0 = 3750.0, 0.078
K_SH_JS5 = FE["PRELOAD"]["F_sh"] / (G0 + FE["PRELOAD"]["F_fit"] / K_C)
assert abs(K_SH_JS5 - RV3.K_SH_JS5) < 1.0
ORDER = {"js5": ["PRELOAD", "SOAK70", "FA1S", "SOAK", "SOAK52"], "patch_a": ["SEAT", "PRELOAD", "SOAK52", "SOAK", "SOAK70", "FA1S"]}
assert _meta["steps"] == ORDER["patch_a"]
SOAKS = ("SOAK70", "SOAK", "SOAK52")
STATES = ("PRELOAD", "SOAK70", "SOAK", "SOAK52", "FA1S")


def entered_from(h, st):
    o = ORDER[h]
    i = o.index(st)
    return o[i - 1] if i > 0 else "assembly"


def _ring_relax(st):
    """js5 relax.json ring family, governing soak P+Q line (d-8.126 z'3) at a soak step; PRELOAD = its preload-only value."""
    if st == "PRELOAD":
        g = _rel["steps"]["SOAK70"]["families"]["ring"]["governing_by_soak_PQ"]
        return g["preload_only"]["PmPb"], None
    g = _rel["steps"][st]["families"]["ring"]["governing_by_soak_PQ"]
    return g["preload_plus_soak"]["PmPb"], g["preload_plus_soak"]["MS_PQ_2Fty"]


def hist_row(h, st):
    sf = _sfj if h == "js5" else _sfp
    side, key = ("global_same_sets", "B") if h == "js5" else ("patch", "A")
    s = sf["steps"][st]
    fp = s["seat_TC02"]["footprint"]
    cl = max(fp["clusters"], key=lambda c: c["Fn_N"])
    c = _cmp["steps"][st][side]
    z0 = [r for r in _cmp["steps"][st]["z0_gradient"] if r["family"] == "seat" and abs(r["delta_deg"] - 6.051) < 0.01 and abs(r["z_prime_mm"]) < 0.01]
    assert len(z0) == 1
    z0 = z0[0]
    rc = _rc["steps"][st]
    secs = list(c["screw_sections"].values()) + [rc["M_max_threaded"][key], rc["M_max_shank_in_TC01"][key]]
    uh = c["under_head_band"]
    nh = s["screw"]["HEAD_on_screw_along_n_N"]
    seat_n = s["seat_TC02"]["along_n_inward_N"]
    out = {"entered_from": entered_from(h, st), "N_head_N": nh, "N_plane_N": s["screw"]["N_plane_N_tension_pos"],
           "seat_window_N": fp.get("window_daz9_zp9_N"), "seat_along_n_N": seat_n, "seat_radial_N": s["seat_TC02"]["normal_force_radial_sum_N"],
           "seat_main_cluster_N": cl["Fn_N"], "main_cluster_zp_mm": cl["z_prime_mm"], "centroid_zp_mm": fp["centroid_force_weighted"]["z_prime_mm"],
           "r_prime_force_weighted_mm": fp.get("r_prime_force_weighted_mm"), "r_prime_5_95_mm": fp.get("r_prime_quantiles_5_95_mm"),
           "CPRESS_r_prime_extent_mm": fp.get("extent_CPRESS_pos", {}).get("r_prime_mm"), "zp_5_95_mm": fp.get("quantiles_5_95_of_Fn", {}).get("z_prime_mm"),
           "F_sh_TC01_N": round(nh - seat_n, 1),
           "seat_line_PmPb_MPa": z0["PmPb_global" if h == "js5" else "PmPb_patch"], "seat_line_MS_PQ": z0["MS_PQ_global" if h == "js5" else "MS_PQ_patch"],
           "seat_line_T_C": z0["T_mean_C"],
           "ring_line_d8p02_PmPb_MPa": c["lines"]["ring"]["PmPb"], "ring_line_d8p02_MS_PQ": c["lines"]["ring"]["MS_PQ_2Fty"],
           "M_max_Nmm": max(x["M"] for x in secs), "N_section_max_N": max(x["N"] for x in secs),
           "UH_band_vm_MPa": uh["vm_MPa"], "UH_band_T_C": uh["T_C"],
           "UH_band_MS_strain_min_n15_n30": min(uh["neuber_MS_strain_n15"], uh["neuber_MS_strain_n30"])}
    if h == "js5":
        r, m = _ring_relax(st) if st != "FA1S" else (None, None)
        out["ring_line_d8p126_PmPb_MPa"], out["ring_line_d8p126_MS_PQ"] = r, m
    return out


HISTS = {st: {h: hist_row(h, st) for h in ("js5", "patch_a")} for st in STATES}


def envelope(st):
    a, b = HISTS[st]["js5"], HISTS[st]["patch_a"]
    hi = lambda k: max((a, b), key=lambda x: x[k])
    lo = lambda k: min((a, b), key=lambda x: x[k])
    ring = [v for v in (a["ring_line_d8p02_PmPb_MPa"], b["ring_line_d8p02_PmPb_MPa"], a.get("ring_line_d8p126_PmPb_MPa")) if v is not None]
    e = {"N_head_N": hi("N_head_N")["N_head_N"], "N_head_from": "js5" if hi("N_head_N") is a else "patch_a",
         "seat_window_N": lo("seat_window_N")["seat_window_N"], "seat_window_from": "js5" if lo("seat_window_N") is a else "patch_a",
         "seat_line_PmPb_MPa": hi("seat_line_PmPb_MPa")["seat_line_PmPb_MPa"], "seat_line_MS_PQ": lo("seat_line_MS_PQ")["seat_line_MS_PQ"],
         "seat_line_from": "js5" if lo("seat_line_MS_PQ") is a else "patch_a",
         "ring_line_PmPb_MPa": max(ring), "M_max_Nmm": hi("M_max_Nmm")["M_max_Nmm"], "M_from": "js5" if hi("M_max_Nmm") is a else "patch_a",
         "N_section_max_N": hi("N_section_max_N")["N_section_max_N"], "UH_band_MS_strain_min": lo("UH_band_MS_strain_min_n15_n30")["UH_band_MS_strain_min_n15_n30"],
         "UH_from": "js5" if lo("UH_band_MS_strain_min_n15_n30") is a else "patch_a",
         "spread_N_rel": round(abs(a["N_head_N"] - b["N_head_N"]) / min(a["N_head_N"], b["N_head_N"]), 4)}
    return e


ENV = {st: envelope(st) for st in STATES}

# ---- model temperatures per FE state (A4-80 deltas: the FE screw is A4-80)
_tL, _aL, _cL = ROWS4["GVLO"]


def frame_near(t0):
    i = int(np.argmin(np.abs(_tL - t0)))
    return float(_aL[i]), float(_cL[i]), round(float(_tL[i]), 3)


TST = {"SOAK70": frame_near(70.7), "SOAK52": frame_near(51.7), "SOAK": (158.0, 96.0, "uniform per part (FEA3D jfwd_deck SOAK: TC-01 158.0, TC-02 96.0, screw 127.0)")}
_, DW70, DR70 = A4_80.deltas(*TST["SOAK70"][:2])
assert abs(DW70 - RV3.DW70) < 1e-12 and abs(DR70 - RV3.DR70) < 1e-12


def model_state(st, kb, scr=A4_80, FV=FV0, g=G0, ksh=None):
    if st == "PRELOAD":
        return state_s(FV, g, 0.0, 0.0, 0.0, 0.0, ksh or K_SH_JS5, kb * scr.kb_ratio)
    T01, T02 = TST[st][:2]
    _, dw, dr = scr.deltas(T01, T02)
    return state_s(FV, g, dw, dr, 0.0, 0.0, ksh or K_SH_JS5, kb * scr.kb_ratio)


def calib_kb(ksh, target):
    _, dw, dr = A4_80.deltas(*TST["SOAK70"][:2])
    lo, hi = 1.0e3, 5.0e7
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if state_s(FV0, G0, dw, dr, 0.0, 0.0, ksh, mid)[0] < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


N70_PATCH = _sfp["steps"]["SOAK70"]["screw"]["HEAD_on_screw_along_n_N"]
KB = {"lo_js5_SOAK70": calib_kb(K_SH_JS5, FE["SOAK70"]["F_S"]), "hi_patch_SOAK70": calib_kb(K_SH_JS5, N70_PATCH)}
assert abs(KB["lo_js5_SOAK70"] - RV3.K_B5) < 1.0

# ---- c per family and per k_b end: worst-history FE P+Q over the model's F_sh at each state
PQ_SEAT = {st: max(HISTS[st]["js5"]["seat_line_PmPb_MPa"], HISTS[st]["patch_a"]["seat_line_PmPb_MPa"]) for st in ("PRELOAD",) + SOAKS}
PQ_RING = {st: ENV[st]["ring_line_PmPb_MPa"] for st in ("PRELOAD",) + SOAKS}


def c_family(pq, kb):
    per = {st: pq[st] / model_state(st, kb)[3] for st in pq}
    st = max(per, key=per.get)
    return per[st], st, {k: round(v, 5) for k, v in per.items()}


CFAM = {e: {"seat": c_family(PQ_SEAT, kb), "ring": c_family(PQ_RING, kb)} for e, kb in KB.items()}

# ---- tilt moment basis 'Fc'
SOAK_PTS = [(HISTS[st][h]["seat_radial_N"], HISTS[st][h]["M_max_Nmm"], f"{h}:{st}") for st in SOAKS for h in ("js5", "patch_a")]
_x = np.array([p[0] for p in SOAK_PTS])
_y = np.array([p[1] for p in SOAK_PTS])
B_M = float(np.sum((_x - _x.mean()) * (_y - _y.mean())) / np.sum((_x - _x.mean()) ** 2))
A_M = float(np.max(_y - B_M * _x))
M_PRE_ENV = max(HISTS["PRELOAD"]["js5"]["M_max_Nmm"], HISTS["PRELOAD"]["patch_a"]["M_max_Nmm"])
N_RATIO = max(HISTS[st][h]["N_section_max_N"] / HISTS[st][h]["N_head_N"] for st in ("PRELOAD",) + SOAKS for h in ("js5", "patch_a"))


def m_soak(Fc):
    return A_M + B_M * Fc


def m_tilt(FS, Fc, w):
    mp = M_PRE_ENV * max(FS, 0.0) / FV0
    return mp + max(w, 0.0) * max(0.0, m_soak(Fc) - mp)


def fibre(FS, Fc, w, scr):
    if FS <= 0.0:
        return 0.0
    return N_RATIO * FS / scr.A_s + scr.tilt_ratio * m_tilt(FS, Fc, w) / scr.Z_3


def fire(FV, g, f, fr, s0, dp0, c, ksh, kb, scr, screw_set=True, cap=True):
    """one firing (every frame, then a cold frame) from wall set s0 and screw set dp0 (v3 structure, v4 tilt)."""
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
        w = dr / DR70
        Fy = float(tab("AL6061-T6", "Fty", a_))
        Rp = scr.rp(a_)
        wy = sy = False
        for _ in range(60):
            FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            changed = False
            if cap and FS > 0.0 and c * Fsh > Fy * (1 + 1e-9):
                lo, hi = s, s + 1.0
                for _ in range(100):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if c * state_s(FV, g, dw, dr, f + dp, mid, ksh, kb)[3] > Fy else (lo, mid)
                s, wy, changed = hi, True, True
                FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            if screw_set and FS > 0.0 and fibre(FS, Fc, w, scr) > Rp * (1 + 1e-9):
                lo, hi = dp, dp + 0.2
                for _ in range(100):
                    mid = 0.5 * (lo + hi)
                    q = state_s(FV, g, dw, dr, f + mid, s, ksh, kb)
                    lo, hi = (mid, hi) if fibre(q[0], q[2], w, scr) > Rp else (lo, mid)
                dp, sy, changed = hi, True, True
                FS, u, Fc, Fsh = state_s(FV, g, dw, dr, f + dp, s, ksh, kb)
            if not changed:
                break
        rec.append({"t": ti, "T01": a_, "T02": b_, "FS": FS, "Fsh": Fsh, "Fc": Fc, "u": u, "w": w, "sig": c * Fsh, "Fty": Fy, "set": s,
                    "dp": dp, "M": m_tilt(FS, Fc, w) * scr.tilt_ratio, "fib": fibre(FS, Fc, w, scr), "Rp": Rp, "wyield": wy, "syield": sy,
                    "slack": FS <= 0.0})
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
            "F_c_max_N": round(max(q["Fc"] for q in rec)), "F_c_min_N": round(min(q["Fc"] for q in rec)),
            "max_sig_over_Fty": round(max(q["sig"] / q["Fty"] for q in rec), 3),
            "fibre_max_MPa": round(rec[jf]["fib"], 1), "fibre_max_at": rec[jf]["t"], "M_at_fibre_max_Nmm": round(rec[jf]["M"], 1),
            "fibre_min_MPa": round(min(q["fib"] for q in rec), 1), "Rp_at_fibre_max_MPa": round(rec[jf]["Rp"], 1)}


def run_case(FV, g, f, fr, c, ksh, kb, scr, screw_set=True, cap=True, keep=False):
    rec1, s1, d1 = fire(FV, g, f, fr, 0.0, 0.0, c, ksh, kb, scr, screw_set, cap)
    rec2, s2, d2 = fire(FV, g, f, fr, s1, d1, c, ksh, kb, scr, screw_set, cap)
    FS_cold0 = state_s(FV, g, 0.0, 0.0, f, 0.0, ksh, kb)[0]
    j2 = max(range(len(rec2)), key=lambda k: rec2[k]["fib"])
    rng = rec2[j2]["fib"] - min(q["fib"] for q in rec2)
    out = {"gap_mm": g, "F_install_N": FV, "embedding_um": round(f * 1e3, 1), "k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb),
           "c_MPa_per_N": round(c, 5), "screw": scr.name, "installed_cold_after_embedding_N": round(FS_cold0),
           "firing_1": summary(rec1), "firing_2": summary(rec2),
           "wall_set_after_firing_1_um": round(s1 * 1e3, 3), "wall_set_after_firing_2_um": round(s2 * 1e3, 3),
           "screw_set_after_firing_1_um": round(d1 * 1e3, 3), "screw_set_after_firing_2_um": round(d2 * 1e3, 3),
           "relaxation_loss_cold_N": round(FS_cold0 - rec1[-1]["FS"]),
           "heads_seated_both_firings": not any(q["slack"] for q in rec1 + rec2),
           "second_firing_elastic": (s2 - s1) < 1e-9 and (d2 - d1) < 1e-9,
           "screw_shakedown": {"fibre_range_firing2_MPa": round(rng, 1), "two_Rp_hot_MPa": round(2.0 * rec2[j2]["Rp"], 1),
                               "MS": round(2.0 * rec2[j2]["Rp"] / max(rng, 1e-9) - 1.0, 3)}}
    if keep:
        out["_rec2"] = rec2
    return out


def run_grid(gaps, installs, ksh, kb, c, scr, screw_set=True, cap=True, emb=None, rows=None):
    out = {}
    for gn, g in gaps.items():
        for iname, FV in installs.items():
            for en, f in (emb or EMB).items():
                for gv, fr in (rows or ROWS4).items():
                    out[f"{gn}|{iname}|{en}|{gv}"] = run_case(FV, g, f, fr, c, ksh, kb, scr, screw_set, cap)
    return out


def run24(ksh, kb, c, scr, screw_set=True, cap=True):
    return run_grid(GAPS, INSTALL, ksh, kb, c, scr, screw_set, cap)


def vsum(d):
    mn = lambda x: min(x["firing_1"]["F_S_min_N"], x["firing_2"]["F_S_min_N"])
    j = min(d, key=lambda k: mn(d[k]))
    jf = max(d, key=lambda k: d[k]["firing_2"]["fibre_max_MPa"] / max(d[k]["firing_2"]["Rp_at_fibre_max_MPa"], 1e-9))
    j_cold = min(d, key=lambda k: d[k]["firing_2"]["cold_end_F_S_N"])
    return {"all_seated": all(x["heads_seated_both_firings"] for x in d.values()), "n_cases": len(d),
            "n_unseated": sum(1 for x in d.values() if not x["heads_seated_both_firings"]),
            "unseated_cases": [k for k, x in d.items() if not x["heads_seated_both_firings"]],
            "min_case": j, "F_S_min_N": mn(d[j]), "min_at": d[j]["firing_2" if d[j]["firing_2"]["F_S_min_N"] <= d[j]["firing_1"]["F_S_min_N"] else "firing_1"]["at_t_s"],
            "F_S_max_N": max(max(x["firing_1"]["F_S_max_N"], x["firing_2"]["F_S_max_N"]) for x in d.values()),
            "F_c_max_N": max(max(x["firing_1"]["F_c_max_N"], x["firing_2"]["F_c_max_N"]) for x in d.values()),
            "fibre_over_Rp_max": round(d[jf]["firing_2"]["fibre_max_MPa"] / d[jf]["firing_2"]["Rp_at_fibre_max_MPa"], 3), "fibre_over_Rp_max_case": jf,
            "screw_fibre_max_MPa": max(max(x["firing_1"]["fibre_max_MPa"], x["firing_2"]["fibre_max_MPa"]) for x in d.values()),
            "max_seat_over_Fty": max(max(x["firing_1"]["max_sig_over_Fty"], x["firing_2"]["max_sig_over_Fty"]) for x in d.values()),
            "max_wall_set_um": max(x["wall_set_after_firing_2_um"] for x in d.values()),
            "max_screw_set_um": max(x["screw_set_after_firing_2_um"] for x in d.values()),
            "max_cold_loss_N": max(x["relaxation_loss_cold_N"] for x in d.values()),
            "all_second_firing_elastic": all(x["second_firing_elastic"] for x in d.values()),
            "n_second_firing_not_elastic": sum(1 for x in d.values() if not x["second_firing_elastic"]),
            "screw_shakedown_min_MS": min(x["screw_shakedown"]["MS"] for x in d.values()),
            "screw_fibre_range_max_MPa": max(x["screw_shakedown"]["fibre_range_firing2_MPa"] for x in d.values()),
            "cold_end_F_S_min_N": d[j_cold]["firing_2"]["cold_end_F_S_N"], "cold_end_min_case": j_cold,
            "cold_end_F_S_min_2250_N": min(x["firing_2"]["cold_end_F_S_N"] for k, x in d.items() if "2250" in k)}


# ---- screws (v3 definitions; IN718 is the ruled screw)
E20 = {"A4": 193000.0, "IN718": tab("IN718", "E", 20.0)}
IN718_S = Screw("IN718", "IN718", E20["IN718"] / E20["A4"], lambda T: tab("IN718", "Fty", T),
                "IN718 AMS 5662/5663 minimum Fty(T) (Special Metals SMC-045, DATASHEET in engmat; linear 20-649 C)")
L_EFF5, L_EFF6 = (2.688 + 0.025) + 0.4 * 5.0 + 0.5 * 5.0, (2.600 + 0.025) + 0.4 * 6.0 + 0.5 * 6.0
KB_M6 = (20.12 / L_EFF6) / (14.18 / L_EFF5)
M6_S = Screw("M6 A4-80", "SS316L", 1.0, lambda T: RV3.RP20 * kT(T), "as A4-80 (ISO 3506-1 class 80)", A_s=20.12, Z_3=math.pi * 4.773 ** 3 / 32.0,
             L_g=L_G * (2.600 + 0.025) / (2.688 + 0.025), kb_ratio=KB_M6, tilt_ratio=(4.773 / 4.019) ** 4)
OPTS = {"IN718 M5 x10 (RULED, ENG-HW-101-IN718)": (IN718_S, 1.0, 1.0, "grade: alpha IN718, k_b x E ratio"),
        "A4-80 M5 x10 (WITHDRAWN, information)": (A4_80, 1.0, 1.0, "FE-calibrated screw"),
        "M6 A4-80 x10 (FALLBACK, ESTIMATE)": (M6_S, (2.600 / 2.688) ** 3, (2.688 / 2.600) ** 2, "ESTIMATE (no FE): v3 size factors")}


def opt_params(nm, end, fam):
    scr, kf, cf, tag = OPTS[nm]
    c = CFAM[end][fam][0] * cf
    return scr, K_SH_JS5 * kf, KB[end] * scr.kb_ratio, c


if __name__ == "__main__":
    res = {"id": "jfwd_relax_v352", "version": "v4", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {k: {"path": str(p), "sha256_16_at_read": sha(p)} for k, p in INPUT_FILES.items()}}
    res["inputs"]["rows"] = SRC4
    res["inputs"]["constants"] = {"k_c_N_mm": round(K_C), "k_sh_K_js5_N_mm": round(K_SH_JS5, 1), "embedding_um": {k: v * 1e3 for k, v in EMB.items()},
                                  "A_s_mm2": A_S, "Z_3_mm3": round(Z_3, 3), "N_ratio": round(N_RATIO, 4),
                                  "k_sh_from_seatforce_exact_split_info": round(_sfj["steps"]["PRELOAD"]["shell_TC02"]["shell_pull_N_tie_minus_seat"]
                                                                                 / (G0 + _sfj["steps"]["PRELOAD"]["seat_TC02"]["normal_force_radial_sum_N"] / K_C), 1)}
    res["history_table"] = HISTS
    res["history_envelope"] = ENV
    res["model_frames"] = TST
    # ---- calibration bracket and the model check against both histories
    chk = {}
    for e, kb in KB.items():
        rows = {}
        for st in SOAKS:
            FS, u, Fc, Fsh = model_state(st, kb)
            r = {"model": {"F_S_N": round(FS, 1), "F_c_N": round(Fc, 1), "F_sh_N": round(Fsh, 1)}}
            for h in ("js5", "patch_a"):
                x = HISTS[st][h]
                r[h] = {"entered_from": x["entered_from"], "N_head_N": x["N_head_N"], "seat_window_N": x["seat_window_N"], "seat_main_cluster_N": x["seat_main_cluster_N"],
                        "F_sh_TC01_N": x["F_sh_TC01_N"],
                        "model_vs_FE_N_rel": round(FS / x["N_head_N"] - 1.0, 4), "model_vs_FE_seat_window_rel": round(Fc / x["seat_window_N"] - 1.0, 4)}
            r["model_vs_envelope_N_rel"] = round(FS / ENV[st]["N_head_N"] - 1.0, 4)
            r["model_vs_lowest_seat_window_rel"] = round(Fc / ENV[st]["seat_window_N"] - 1.0, 4)
            rows[st] = r
        chk[e] = {"k_b_N_mm": round(kb), "k_b_over_lo": round(kb / KB["lo_js5_SOAK70"], 4), "states": rows,
                  "c_seat": {"used": round(CFAM[e]["seat"][0], 5), "governing_state": CFAM[e]["seat"][1], "per_state": CFAM[e]["seat"][2]},
                  "c_ring": {"used": round(CFAM[e]["ring"][0], 5), "governing_state": CFAM[e]["ring"][1], "per_state": CFAM[e]["ring"][2]}}
    res["calibration_bracket_and_model_check"] = chk
    res["tilt_basis_Fc"] = {"soak_points_Fc_N_M_Nmm": [[round(a, 1), round(b, 1), n] for a, b, n in SOAK_PTS], "slope_b": round(B_M, 4),
                            "intercept_a_Nmm": round(A_M, 1), "M_pre_env_Nmm_at_3750N": M_PRE_ENV,
                            "residuals_line_minus_FE_Nmm": {n: round(A_M + B_M * a - b, 1) for a, b, n in SOAK_PTS}}
    # ---- the 24-case no-slack check, both k_b ends, seat and ring bounds, per option
    cases, verdict = {}, {}
    for nm in OPTS:
        for e in KB:
            for fam in ("seat", "ring"):
                scr, ksh, kb, c = opt_params(nm, e, fam)
                d = run24(ksh, kb, c, scr, True)
                cases[f"{nm}|{e}|{fam}"] = d
                v = vsum(d)
                v.update({"k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb), "c": round(c, 5)})
                verdict[f"{nm}|{e}|{fam}"] = v
    res["cases_24"] = cases
    res["verdict_24"] = verdict
    worse = {}
    for nm in OPTS:
        for fam in ("seat", "ring"):
            vs = {e: verdict[f"{nm}|{e}|{fam}"] for e in KB}
            we = min(vs, key=lambda e: (vs[e]["F_S_min_N"], -vs[e]["n_unseated"]))
            worse[f"{nm}|{fam}"] = {"worse_end": we, "F_S_min_N": vs[we]["F_S_min_N"], "n_unseated": vs[we]["n_unseated"], "min_case": vs[we]["min_case"],
                                    "both_ends": {e: {"F_S_min_N": vs[e]["F_S_min_N"], "n_unseated": vs[e]["n_unseated"], "cold_end_F_S_min_2250_N": vs[e]["cold_end_F_S_min_2250_N"],
                                                      "max_wall_set_um": vs[e]["max_wall_set_um"], "max_screw_set_um": vs[e]["max_screw_set_um"],
                                                      "fibre_over_Rp_max": vs[e]["fibre_over_Rp_max"], "screw_shakedown_min_MS": vs[e]["screw_shakedown_min_MS"]} for e in KB}}
    res["worse_end_quoted"] = worse
    # ---- (a) series compliance for IN718 on the seat line: the largest k_b factor that seats all 24 at each end
    IN = "IN718 M5 x10 (RULED, ENG-HW-101-IN718)"
    sc = {}
    for e in KB:
        scr, ksh, kb, c = opt_params(IN, e, "seat")
        if vsum(run24(ksh, kb, c, scr))["all_seated"]:
            sc[e] = {"f_max": 1.0, "note": "seated without added compliance"}
            continue
        lo, hi = 0.02, 1.0
        if not vsum(run24(ksh, kb * lo, c, scr))["all_seated"]:
            sc[e] = {"f_max": None, "note": "slack even at k_b x 0.02"}
            continue
        for _ in range(14):
            mid = math.sqrt(lo * hi)
            lo, hi = (mid, hi) if vsum(run24(ksh, kb * mid, c, scr))["all_seated"] else (lo, mid)
        vf = vsum(run24(ksh, kb * lo, c, scr))
        sc[e] = {"f_max": round(lo, 4), "k_b_at_f_N_mm": round(kb * lo), "added_series_compliance_um_per_kN": round((1.0 / (kb * lo) - 1.0 / kb) * 1e6, 3),
                 "F_S_min_at_f_N": vf["F_S_min_N"], "min_case": vf["min_case"], "cold_end_F_S_min_2250_N": vf["cold_end_F_S_min_2250_N"],
                 "F_S_max_N": vf["F_S_max_N"], "fibre_over_Rp_max": vf["fibre_over_Rp_max"]}
    res["a_series_compliance_IN718_seat_line"] = sc
    # ---- ring-line select-fit band for IN718 (information unless the ring line stands): largest gap with all 24 seated, per end
    def gap_cap(scr, ksh, kb, c):
        """band from the 0.040 drawing minimum upward (the minimum stays, lead 11:25Z): the largest gap with all cases seated; the sweep
        below 0.040 is information (not buildable)."""
        seated = lambda g: vsum(run_grid({f"g{g:.4f}": g}, INSTALL, ksh, kb, c, scr))["all_seated"]
        grid = [0.040 + 0.0025 * k for k in range(0, 33)]
        sweep = {round(g, 4): seated(g) for g in grid}
        below = {round(0.0025 * k, 4): seated(0.0025 * k) for k in range(0, 16)}
        if not sweep[0.04]:
            return {"g_cap_mm": None, "note": "not seated at the 0.040 drawing minimum: no band", "sweep_0.040_0.120": sweep, "below_0.040_info": below}
        bad = [g for g in grid if not seated(g)]
        if not bad:
            return {"g_cap_mm": "> 0.120", "sweep_0.040_0.120": sweep, "below_0.040_info": below}
        fb = min(bad)
        lo, hi = fb - 0.0025, fb
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if seated(mid) else (lo, mid)
        return {"g_cap_mm": round(lo, 5), "contiguous_from_0.040": all(v for g, v in sweep.items() if g <= lo), "sweep_0.040_0.120": sweep,
                "below_0.040_info": below}
    sfb = {}
    for e in KB:
        for fam in ("seat", "ring"):
            scr, ksh, kb, c = opt_params(IN, e, fam)
            sfb[f"{e}|{fam}"] = gap_cap(scr, ksh, kb, c)
    res["select_fit_gap_cap_IN718"] = sfb
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
    print("K_B", {k: round(v) for k, v in KB.items()}, "N_RATIO", round(N_RATIO, 4), "tilt a b", round(A_M, 1), round(B_M, 4), "M_pre", M_PRE_ENV)
    for st in STATES:
        print(st, json.dumps(ENV[st]))
    for e, v in chk.items():
        print("==", e, v["k_b_N_mm"], "c_seat", v["c_seat"]["used"], v["c_seat"]["governing_state"], "c_ring", v["c_ring"]["used"], v["c_ring"]["governing_state"])
        for st, r in v["states"].items():
            print(f"   {st:7s} model F_S {r['model']['F_S_N']:7.1f} F_c {r['model']['F_c_N']:7.1f} F_sh {r['model']['F_sh_N']:7.1f} | js5 {r['js5']['N_head_N']:7.1f} "
                  f"({r['js5']['model_vs_FE_N_rel']:+.3f}) seat {r['js5']['seat_window_N']:7.1f} ({r['js5']['model_vs_FE_seat_window_rel']:+.3f}) | patch "
                  f"{r['patch_a']['N_head_N']:7.1f} ({r['patch_a']['model_vs_FE_N_rel']:+.3f}) seat {r['patch_a']['seat_window_N']:7.1f} "
                  f"({r['patch_a']['model_vs_FE_seat_window_rel']:+.3f}) | env N {r['model_vs_envelope_N_rel']:+.3f}")
    for k, v in verdict.items():
        print(f"  {k:62s} seated {v['all_seated']!s:5s} unseated {v['n_unseated']:2d} min {v['F_S_min_N']:6d} ({v['min_case']}, t {v['min_at']}) cold2250 "
              f"{v['cold_end_F_S_min_2250_N']:5d} set {v['max_wall_set_um']:6.1f} sset {v['max_screw_set_um']:6.3f} fib/Rp {v['fibre_over_Rp_max']:.3f} "
              f"shk {v['screw_shakedown_min_MS']:+.3f} Fmax {v['F_S_max_N']}")
    print(json.dumps(worse, indent=0)[:3000])
    print(json.dumps(sc, indent=1))
    print(json.dumps(sfb, indent=1))
