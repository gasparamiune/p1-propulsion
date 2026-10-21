#!/usr/bin/env python3
"""Electronics v2.12 Part A (R3-01 items 1-4, 7, 8): C1 thermal-zero drift budget on Mechanical's C1 seat history.
DERIVED on SIM inputs (Mechanical c1_seat_v352_v1.json: the diaphragm point r 25.0, z = zt - 9.5, SIM nodal values, DERIVED interpolation;
the TC-02 / case OD nodal fields of the same NF2b runs, tb70/hist/*.npz), the DATASHEET typical coefficient and ASSUMED terms as tagged.
Not physical approval.  Run: PYTHONDONTWRITEBYTECODE=1 nice -n 15 python3 -I calc/v2p12/c1_drift_v2p12.py <out.json> <sil_hist_dir>
Writes the JSON and, for the SIL drift model, one CSV per run: t_s, dT_seat_K (diaphragm), dT_sensor_K (head-top seat-TC node), dT_station_K."""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np

HUB = Path("/home/claude/work/shared-fallback/engine")
SEAT = HUB / "04-fea/v352/c1seat/c1_seat_v352_v1.json"
XCHK = HUB / "04-fea/v352/c1seat/c1_seat_xcheck_v352_v1.json"
TORCH = HUB / "04-fea/v352/c1seat/torch_port_bl08_v352_v1.json"
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
RUNS = {"A1_NF2b": "DC-A1dispp99_tg711_hi_SS316L_L2.5_v352_NF2b",
        "B1_R4_GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI",
        "B1_R4_GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO"}
FS_BAR = 137.9                       # [DATASHEET Kulite XTL-190SM-2000A] 2000 psia
C_TYP = 0.0248                       # [DATASHEET] 1 %FS / 100 F = 137.9 x 0.01 / 55.56 K = 0.02482 bar/K (pc_transducer_v3 B, Mechanical F1)
K_SWEEP = (1.0, 1.5, 2.0, 3.0)       # [MISSING F-10] max / typ, ASSUMED sweep until Kulite answers
T_TRIM_C = 20.0                      # [DESIGN] U330 / bench trim temperature (pc_transducer_v3.py:465)
T_AW = (2800.0, 1500.0)              # [ASSUMED, Mechanical F1 08:02:01Z first-order T0 estimate] adiabatic-wall bounds
SENSOR_RZ = (25.875, 0.0)            # seat TC junction: head top at r 25.875 mm (= the T1_head_top_bracket_foot monitor's own node, z = zt)
STATION_MM = 13.5                    # case-TC station (TC1 / TC2 junction centre, 13.5 mm aft of the injector face)
TAU_TC_S = 0.25                      # [ASSUMED = B-TC-1 acceptance tau <= 0.25 s] seat TC time constant (bonded junction)
DT_SENS_ERR_K = 0.30                 # [ASSUMED] differential (ARM-referenced) seat-TC reading error: type K slope 0.4 % of dT + MAX31856
                                     #   CJ drift between ARM and the relight (B-TC-1 measures)
EPS_COEF = 0.10                      # [ASSUMED, B-PC-1 acceptance TO-SET] per-serial coefficient error after the B-PC-1 table
LIM_RZ_V211, BASE_DEF, BASE_BPC1 = 0.30, 0.70, 0.40     # [config.h v2.11] bar
RESID_ZERO = 0.05                    # [ASSUMED, B-PC-1 '20 s drift' row] non-thermal zero drift ARM -> relight
VENT_OUTGAS = 0.05                   # [DESIGN config.h l.805] post-burn outgassing allowance at the re-zero block
NOISE_BLK = 0.0012                   # [DERIVED config.h kPcRezeroN] 1.7 kPa rms / sqrt(200)
U330_TRIP, U330_HALF = 32.59, 1.513  # [DERIVED pc_transducer_v3 F] bar abs, circuit band half-width
FW_OVP = 30.0                        # [config.h] firmware Pc over-pressure abort level, bar abs
C_070BG = 1.05 / 105.0               # [DATASHEET TE M3234 070BG TEB 1.5 %FS = 1.05 bar over -20..85 C] about 0.010 bar/K if linear


def h16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def r(x, n=4):
    return None if x is None else round(float(x), n)


def main():
    out_json, hist_dir = Path(sys.argv[1]), Path(sys.argv[2])
    hist_dir.mkdir(parents=True, exist_ok=True)
    seat = json.loads(SEAT.read_text()); xchk = json.loads(XCHK.read_text()); torch = json.loads(TORCH.read_text())
    assert h16(SEAT) == "435f5d71f6213160" and h16(XCHK) == "02a9f27c7965f223" and h16(TORCH) == "20220647d32cbbbc"
    O = {"script": "calc/v2p12/c1_drift_v2p12.py", "version": "v1", "date": "2026-10-21",
         "status": "DERIVED on SIM (Mechanical seat history) x DATASHEET typical coefficient; k, eps, sensor terms ASSUMED; not physical approval",
         "inputs": {"c1_seat_v352_v1.json": h16(SEAT), "c1_seat_xcheck_v352_v1.json": h16(XCHK), "torch_port_bl08_v352_v1.json": h16(TORCH)},
         "coef_typ_bar_per_K": C_TYP, "coef_exact_bar_per_K": round(0.01 * FS_BAR / (100.0 / 1.8), 6), "k_sweep_ASSUMED": list(K_SWEEP)}
    # ------------------------------------------------------------------ A2 seat histories (diaphragm, SIM) and the T0 statement
    ev, hist = {}, {}
    for rn, lab in RUNS.items():
        a = seat["runs"][rn]
        assert a["dir"] == lab
        O["inputs"][lab + "_hist.npz"] = h16(HIST / f"{lab}_hist.npz")
        T0K = a["T_K_at_events"]["ARM"]["diaphragm_zt-9.5"]
        ev[rn] = {k: {"t_s": v["t_s"], "dT_seat_K": v["diaphragm_zt-9.5"] - T0K} for k, v in a["T_K_at_events"].items()}
        h = np.array(a["history_diaphragm"], float)
        z = np.load(HIST / f"{lab}_hist.npz", allow_pickle=False)
        info = json.loads(str(z["info"]))
        assert info["frd_sha256_16"] == a["frd_gz_sha16"], rn
        t = z["t_s"]; assert len(t) == len(h) and np.allclose(t, h[:, 0], atol=1e-3)
        X, T2 = z["X_TC02"], z["T_TC02"].astype(float)
        zt = a["zt_mm"]
        d = np.hypot(X[:, 0] - SENSOR_RZ[0], X[:, 1] - (zt + SENSOR_RZ[1]))
        js = int(np.argmin(d)); assert d[js] < 1e-3, (rn, d[js])
        sens = T2[:, js]
        aft = -(z["od_X"][:, 1] - info["inj_face_z_mm"]); o = np.argsort(aft)
        ODT = z["od_T"].astype(float)
        stat = np.array([np.interp(STATION_MM, aft[o], ODT[k, o]) for k in range(len(t))])
        hist[rn] = {"t": t, "seat": h[:, 1] - T0K, "sens": sens - sens[0], "stat": stat - stat[0]}
        m = t <= 3700.0
        np.savetxt(hist_dir / f"seat_hist_{rn}.csv", np.column_stack([t[m], hist[rn]["seat"][m], hist[rn]["sens"][m], hist[rn]["stat"][m]]),
                   delimiter=",", fmt="%.5f", header="t_s,dT_seat_K,dT_sensor_K,dT_station_K", comments="")
        O["inputs"]["sil_hist_" + rn] = {"file": str(hist_dir / f"seat_hist_{rn}.csv"), "sha256_16": h16(hist_dir / f"seat_hist_{rn}.csv")}
    O["A2_seat_rise_vs_ARM_K"] = {rn: {k: r(v["dT_seat_K"], 3) for k, v in e.items()} for rn, e in ev.items()}
    O["A2_seat_drifts_K_Mechanical"] = {rn: seat["runs"][rn]["drifts"] and {k: r(v["diaphragm_zt-9.5"]["dT_K"]) for k, v in seat["runs"][rn]["drifts"].items()}
                                        for rn in RUNS}
    fac = {}
    for taw in T_AW:
        lo, hi = (taw - 273.15) / (taw - 293.15), (taw - 313.15) / (taw - 293.15)
        fac[str(taw)] = [r(lo, 4), r(hi, 4)]
    O["A2_T0"] = {"statement": "the ARM-referenced rise is T0-independent to first order: rise(T0) = rise(20 C) x (T_aw - T0) / (T_aw - 293.15 K) "
                  "(Mechanical F1 08:02:01Z, quoted by the lead brief: +/-0.8 % over 0-40 C at T_aw 2800 K, +/-1.7 % at 1500 K, <= 0.035 K on any "
                  "re-zero2-referenced drift) [DERIVED]; the limits below carry the 1500 K factor (1.0166) on every ARM-referenced rise",
                  "factor_at_0C_and_40C_by_T_aw": fac, "factor_used": r(fac["1500.0"][0], 4),
                  "not_covered_MISSING": ["T-dependent Al6061 conductivity", "N2O feed temperature different from T0",
                                          "non-uniform pre-ARM temperature (sun, a warm stand): the F-13 soak condition bounds it on the stand only"],
                  "ranges": {"stand": "T0 <= 24 C (F-13, 249 (2)); lower end stated 0 C", "flight": "0-40 C (stated here for the A1 relight; GNC / lead to confirm)"},
                  "comparator": "U330 sees s k c (T_seat - T_trim) = s k c ((T0 - 20 C) + rise): the T0 term is NOT removed by any zero"}
    F0 = fac["1500.0"][0]
    # ------------------------------------------------------------------ A1 / A3 option (a): uncompensated, widened limit
    def dT(rn, key):
        return ev[rn][key]["dT_seat_K"]
    A1 = {"rz1": dT("A1_NF2b", "rezero1_end_COAST+1.4s"), "rz2": dT("A1_NF2b", "rezero2_end"), "E1": dT("A1_NF2b", "E1"), "light": dT("A1_NF2b", "light"),
          "end2": dT("A1_NF2b", "shutdown2")}
    ST = {}
    for rn in ("B1_R4_GVHI", "B1_R4_GVLO"):
        ST[rn] = {"rz1": dT(rn, "rezero1_end_S+1.4s"), "rz2": dT(rn, "stand_rezero2_end_S+15.72s"), "E1": dT(rn, "stand_E1_S+18.715s"),
                  "light": dT(rn, "stand_light_S+19.03s"), "end1": dT(rn, "shutdown")}
    stw = {k: max(ST[rn][k] for rn in ST) for k in ST["B1_R4_GVHI"]}
    rows = {}
    for k in K_SWEEP:
        a = k * C_TYP
        row = {"A1_shift_rz1_bar": r(a * A1["rz1"] * F0), "A1_shift_rz2_bar": r(a * A1["rz2"] * F0), "A1_drift_ARM_to_E1_bar": r(a * A1["E1"] * F0),
               "A1_drift_rz2_to_E1_bar": r(a * (A1["E1"] - A1["rz2"]) * F0), "stand_shift_rz1_bar": r(a * stw["rz1"] * F0),
               "stand_shift_rz2_bar": r(a * stw["rz2"] * F0), "stand_drift_ARM_to_E1_bar": r(a * stw["E1"] * F0),
               "stand_drift_rz2_to_E1_bar": r(a * max(ST[rn]["E1"] - ST[rn]["rz2"] for rn in ST) * F0),
               "v211_A1_rz2_accepted_0p30": bool(a * A1["rz2"] * F0 <= LIM_RZ_V211), "v211_stand_rz2_accepted_0p30": bool(a * stw["rz2"] * F0 <= LIM_RZ_V211)}
        add = RESID_ZERO + VENT_OUTGAS + NOISE_BLK
        LA, LS = a * A1["rz2"] * F0 + add, a * stw["rz2"] * F0 + add
        row["option_a_limit_A1_bar"] = r(LA, 3); row["option_a_limit_stand_bar"] = r(LS, 3)
        row["option_a_largest_nonvented_accepted_A1_bar"] = r(LA + a * A1["rz2"] * F0, 3)
        row["option_a_largest_nonvented_accepted_stand_bar"] = r(LS + a * stw["rz2"] * F0, 3)
        rows[str(k)] = row
    O["A1_A3_uncompensated_by_k"] = rows
    O["A1_k_at_which_v211_rz2_rejected"] = {"A1_seat": r(LIM_RZ_V211 / (C_TYP * A1["rz2"] * F0), 3), "A1_seat_T0_20C": r(LIM_RZ_V211 / (C_TYP * A1["rz2"]), 3),
                                           "stand_seat": r(LIM_RZ_V211 / (C_TYP * stw["rz2"] * F0), 3)}
    O["A3_option_a"] = {"rule": "kPcRezeroMax_Pa >= k_max x 0.0248 x max rise(ARM -> re-zero2 block) x 1.0166 (T0) + zero drift 0.05 (ASSUMED, B-PC-1) + "
                        "outgassing 0.05 (DESIGN) + block noise 0.0012 bar",
                        "k3_A1_flight_bar": rows["3.0"]["option_a_limit_A1_bar"], "k3_stand_after_B1_bar": rows["3.0"]["option_a_limit_stand_bar"],
                        "largest_nonvented_chamber_accepted_as_zero_bar": {"A1_k3": rows["3.0"]["option_a_largest_nonvented_accepted_A1_bar"],
                                                                           "stand_k3": rows["3.0"]["option_a_largest_nonvented_accepted_stand_bar"],
                                                                           "v211_reference": round(LIM_RZ_V211 + 0.0, 3)},
                        "reading": "a non-vented chamber (OI-12: MV seat leak, blocked nozzle) up to that gauge pressure is taken as the zero; every later "
                                   "Pc then reads that much low (firmware 30 bar abort, the light floor and the vented check all shift); the OI-12 "
                                   "vented check (0.1 bar) loses its meaning after such a zero"}
    # ------------------------------------------------------------------ A3 option (b): temperature-compensated zero
    def interp(rn, key, tq):
        H = hist[rn]
        return float(np.interp(tq, H["t"], H[key]))
    def rate(rn, tq, w=0.05):
        return (interp(rn, "seat", tq + w) - interp(rn, "seat", tq - w)) / (2 * w)
    evb = {"A1_NF2b": {"rz1": "rezero1_end_COAST+1.4s", "rz2": "rezero2_end", "E1": "E1", "light": "light"},
           "B1_R4_GVHI": {"rz1": "rezero1_end_S+1.4s", "rz2": "stand_rezero2_end_S+15.72s", "E1": "stand_E1_S+18.715s", "light": "stand_light_S+19.03s"},
           "B1_R4_GVLO": {"rz1": "rezero1_end_S+1.4s", "rz2": "stand_rezero2_end_S+15.72s", "E1": "stand_E1_S+18.715s", "light": "stand_light_S+19.03s"}}
    sens = {}
    for rn, km in evb.items():
        s = {}
        for kk, key in km.items():
            tq = ev[rn][key]["t_s"]
            s[kk] = {"t_s": tq, "seat_K": r(interp(rn, "seat", tq), 3), "sensor_K": r(interp(rn, "sens", tq), 3),
                     "gradient_err_K": r(interp(rn, "sens", tq) - interp(rn, "seat", tq), 3), "seat_rate_K_per_s": r(rate(rn, tq), 3),
                     "lag_err_K": r(-rate(rn, tq) * TAU_TC_S, 3), "station_K": r(interp(rn, "stat", tq), 2)}
        sens[rn] = s
    O["A3_option_b_seat_tc_errors_vs_ARM"] = sens
    # case-TC predictor: seat rise from the station rise through a first-order lag, (a, tau) fitted on A1 0-27 s, tested on B1
    def lagged(t, x, tau):
        y = np.zeros_like(x)
        for i in range(1, len(t)):
            dt = t[i] - t[i - 1]; al = 1.0 - math.exp(-dt / tau)
            y[i] = y[i - 1] + (x[i - 1] + 0.5 * (x[i] - x[i - 1]) - y[i - 1]) * al
        return y
    HA = hist["A1_NF2b"]; mA = HA["t"] <= 27.0
    best = None
    for tau in np.concatenate([np.arange(1.0, 30.0, 0.5), np.arange(30.0, 400.0, 5.0)]):
        y = lagged(HA["t"][mA], HA["stat"][mA], tau)
        aa = float(np.dot(y, HA["seat"][mA]) / max(np.dot(y, y), 1e-12))
        e = float(np.max(np.abs(aa * y - HA["seat"][mA])))
        if best is None or e < best[2]:
            best = (float(tau), aa, e)
    tau, aa, eA = best
    pred = {}
    for rn, km in evb.items():
        H = hist[rn]; m = H["t"] <= (27.0 if rn.startswith("A1") else 45.0)
        y = aa * lagged(H["t"][m], H["stat"][m], tau)
        p = {}
        for kk, key in km.items():
            tq = ev[rn][key]["t_s"]
            p[kk] = {"seat_K": r(np.interp(tq, H["t"][m], H["seat"][m]), 3), "predicted_K": r(np.interp(tq, H["t"][m], y), 3),
                     "err_K": r(np.interp(tq, H["t"][m], y) - np.interp(tq, H["t"][m], H["seat"][m]), 3)}
        p["max_abs_err_K_0_to_light"] = r(float(np.max(np.abs(y - H["seat"][m])[H["t"][m] <= ev[rn][km["light"]]["t_s"]])), 3)
        pred[rn] = p
    O["A3_option_b_case_tc_predictor"] = {"model": "rise_seat ~= a x lag(rise_station, tau), (a, tau) least-max fit on A1 0-27 s [DERIVED]",
                                          "a": r(aa, 4), "tau_s": tau, "fit_max_err_A1_K": r(eA, 3), "per_run": pred,
                                          "verdict": None}
    wB = max(abs(pred[rn][kk]["err_K"]) for rn in ("B1_R4_GVHI", "B1_R4_GVLO") for kk in ("rz1", "rz2", "E1"))
    O["A3_option_b_case_tc_predictor"]["worst_err_on_B1_events_K"] = r(wB, 3)
    O["A3_option_b_case_tc_predictor"]["verdict"] = (
        "NOT usable: the case station leads the head by tens of seconds and cools in the coast while the seat still heats; the A1-fitted "
        f"predictor misses the B1 seat by up to {wB:.1f} K at the re-zero / E1 events (x k x 0.0248 = {wB * C_TYP:.2f} / {3 * wB * C_TYP:.2f} bar at k 1 / 3); "
        "a seat temperature measurement is needed")
    # residual budget of the compensated zero, per k and location (ARM-referenced and latest-zero-referenced)
    budget = {}
    for k in K_SWEEP:
        a = k * C_TYP; b = {}
        for loc, rn_list in (("A1", ["A1_NF2b"]), ("stand_B1", ["B1_R4_GVHI", "B1_R4_GVLO"])):
            for kk in ("rz1", "rz2", "E1"):
                vals = []
                for rn in rn_list:
                    s = sens[rn][kk]
                    vals.append(EPS_COEF * a * abs(s["seat_K"]) * F0 + a * (abs(s["gradient_err_K"]) + abs(s["lag_err_K"]) + DT_SENS_ERR_K))
                b[f"{loc}_ARM_to_{kk}_bar"] = r(max(vals), 3)
            vals = []
            for rn in rn_list:
                s2, sE = sens[rn]["rz2"], sens[rn]["E1"]
                d_seat = sE["seat_K"] - s2["seat_K"]; d_grad = sE["gradient_err_K"] - s2["gradient_err_K"]
                vals.append(EPS_COEF * a * abs(d_seat) + a * (abs(d_grad) + abs(sE["lag_err_K"] - s2["lag_err_K"]) + 0.1))
            b[f"{loc}_rz2_to_E1_bar"] = r(max(vals), 3)
        b["A1_rz2_accepted_at_0p30"] = bool(b["A1_ARM_to_rz2_bar"] + RESID_ZERO + VENT_OUTGAS <= LIM_RZ_V211)
        b["stand_rz1_accepted_at_0p30"] = bool(b["stand_B1_ARM_to_rz1_bar"] + RESID_ZERO + VENT_OUTGAS <= LIM_RZ_V211)
        b["stand_rz2_accepted_at_0p30"] = bool(b["stand_B1_ARM_to_rz2_bar"] + RESID_ZERO + VENT_OUTGAS <= LIM_RZ_V211)
        budget[str(k)] = b
    O["A3_option_b_residual_budget"] = {"terms": f"eps {EPS_COEF} x k c rise x 1.0166 (ASSUMED B-PC-1 per-serial table) + k c (gradient head-top node vs "
                                                 f"diaphragm, SIM + lag {TAU_TC_S} s x seat rate (ASSUMED tau) + {DT_SENS_ERR_K} K (ASSUMED TC + CJ))",
                                        "by_k": budget,
                                        "largest_nonvented_accepted_bar": r(LIM_RZ_V211 + max(budget[str(k)]["A1_ARM_to_rz2_bar"] for k in K_SWEEP), 3)}
    # ------------------------------------------------------------------ A4 kIgnBaseCheck_Pa
    a3 = 3.0 * C_TYP
    O["A4_base_check"] = {
        "rule": "kIgnBaseCheck_Pa >= residual + k_max c rise(latest accepted zero -> E1) + 0.1 bar (R3-01 item 4)",
        "uncompensated_drift_rz2_to_E1_bar_k3": {"A1": rows["3.0"]["A1_drift_rz2_to_E1_bar"], "stand": rows["3.0"]["stand_drift_rz2_to_E1_bar"]},
        "uncompensated_needed_bar": {"default": r(0.60 + a3 * (A1["E1"] - A1["rz2"]) * F0 + 0.10, 3), "bpc1": r(0.30 + a3 * (A1["E1"] - A1["rz2"]) * F0 + 0.10, 3)},
        "compensated_residual_rz2_to_E1_bar_k3": {"A1": budget["3.0"]["A1_rz2_to_E1_bar"], "stand": budget["3.0"]["stand_B1_rz2_to_E1_bar"]},
        "rejected_rezero_uncompensated_ARM_to_E1_bar": {str(k): {"A1": rows[str(k)]["A1_drift_ARM_to_E1_bar"], "stand": rows[str(k)]["stand_drift_ARM_to_E1_bar"]} for k in K_SWEEP}}
    # ------------------------------------------------------------------ A7 torch transducer (070BG)
    tp = torch["torch_port"] if "torch_port" in torch else torch
    head_r25_A1 = max(seat["runs"]["A1_NF2b"]["rise_K_vs_ARM"]["rezero2_end"][p] for p in ("tap_mouth_zt-0.5", "tap_mid_zt-4.75", "zt-8.0", "diaphragm_zt-9.5", "zt-11.0"))
    head_r25_st = max(seat["runs"][rn]["rise_K_vs_ARM"]["stand_rezero2_end_S+15.72s"][p] for rn in ("B1_R4_GVHI", "B1_R4_GVLO")
                      for p in ("tap_mouth_zt-0.5", "tap_mid_zt-4.75", "zt-8.0", "diaphragm_zt-9.5", "zt-11.0"))
    O["A7_torch"] = {"coef_070BG_bar_per_K": r(C_070BG, 4), "head_contribution_ARM_to_rz2_K": {"A1": r(head_r25_A1, 3), "stand_B1": r(head_r25_st, 3)},
                     "shift_at_head_contribution_bar": {"A1": r(C_070BG * head_r25_A1, 3), "stand_B1": r(C_070BG * head_r25_st, 3)},
                     "upper_bracket": "070BG compensated band edge 85 C (the TEB holds only inside -20..85 C): rise <= 85 C - T0; TEB worst-case change <= 2 x 1.05 = 2.1 bar",
                     "local_heat": "MISSING (torch heat into the seat / passage, ENG-IG-01 conduction, 3-D boss, the 070BG's own temperature): Mechanical torch_port_bl08_v352"}
    # ------------------------------------------------------------------ A8 U330 band term
    u = {}
    for k in K_SWEEP:
        a = k * C_TYP; row = {}
        for loc, T0s, rise in (("A1_relight_burn_end", (0.0, 20.0, 40.0), A1["end2"] * F0), ("B1_burn_end_stand", (0.0, 24.0), stw["end1"] * F0),
                               ("stand_relight_light", (0.0, 24.0), stw["light"] * F0)):
            for T0 in T0s:
                sh = a * ((T0 - T_TRIM_C) + rise)
                row[f"{loc}_T0_{T0:g}C_shift_bar"] = r(sh, 3)
                row[f"{loc}_T0_{T0:g}C_band_bar_abs"] = [r(U330_TRIP - U330_HALF - abs(sh), 2), r(U330_TRIP + U330_HALF + abs(sh), 2)]
        u[str(k)] = row
    O["A8_U330"] = {"by_k": u, "low_end_below_fw30_when_shift_gt_bar": r(U330_TRIP - U330_HALF - FW_OVP, 3),
                    "k_low_end_below_30_A1_T0_40C": r((U330_TRIP - U330_HALF - FW_OVP) / (C_TYP * ((40.0 - T_TRIM_C) + A1["end2"] * F0)), 3),
                    "k_low_end_below_30_A1_T0_20C": r((U330_TRIP - U330_HALF - FW_OVP) / (C_TYP * (A1["end2"] * F0)), 3),
                    "k_low_end_below_30_stand_T0_24C_B1_end": r((U330_TRIP - U330_HALF - FW_OVP) / (C_TYP * ((24.0 - T_TRIM_C) + stw["end1"] * F0)), 3),
                    "band_high_add_for_S6R_S6C_recheck_bar": r(3.0 * C_TYP * max((40.0 - T_TRIM_C) + A1["end2"] * F0, (24.0 - T_TRIM_C) + stw["light"] * F0), 3)}
    out_json.write_text(json.dumps(O, indent=1))
    print(json.dumps({k: O[k] for k in ("A1_k_at_which_v211_rz2_rejected", "A3_option_a", "A4_base_check")}, indent=1))
    print("predictor", O["A3_option_b_case_tc_predictor"]["a"], O["A3_option_b_case_tc_predictor"]["tau_s"], O["A3_option_b_case_tc_predictor"]["worst_err_on_B1_events_K"])
    print(json.dumps(O["A3_option_b_residual_budget"]["by_k"], indent=0))
    print(json.dumps(O["A3_option_b_seat_tc_errors_vs_ARM"], indent=0))
    print(json.dumps(O["A7_torch"], indent=0)); print(json.dumps({k: O["A8_U330"][k] for k in O["A8_U330"] if k != "by_k"}, indent=0))
    print(json.dumps(O["A8_U330"]["by_k"]["3.0"], indent=0))


if __name__ == "__main__":
    main()
