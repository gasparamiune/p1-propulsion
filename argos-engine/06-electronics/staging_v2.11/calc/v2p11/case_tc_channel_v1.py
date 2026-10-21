#!/usr/bin/env python3
"""Electronics v2.11 Part A (lead brief 2026-10-20; CHANGELOG 243 (3), 242 (7), mechanical.json v2.2 requests_v352[0]).

Case over-temperature abort channel at A = 150 C (423.15 K) on the case TC station (TC1 az 90 / TC2 az 270, type K, MAX31856
U604 / U605):
  A1 (a) false-trip side: high-reading error stack term by term, worst case and RSS, against the +12.26 K margin to the rev-3 merged
         perfect-contact armed maximum 137.74 C (Mechanical bpkg_abort_v352_v1.json); the persistence filter, its conversion count and
         its trip-delay cost;
  A1 (b) low-reading tolerance at the trip including the surface-mount error (junction-to-case contact and lag; the true metal hotter
         than the reading), with its basis, for the T-F1 exposure temperature (150 C + this tolerance);
  A2     a relight refusal limit kCaseRelightMax_K consistent with A, with its basis (the lead decides).
Reads only (Mechanical's histories and bpkg are read, never written). Evidence tags per term. Nothing here is physical approval.
Usage: python3 -I calc/v2p11/case_tc_channel_v1.py  -> results/case_tc_channel_v1.json + .txt
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/home/claude/work/electronics")
OUT_J = ROOT / "results" / "case_tc_channel_v1.json"
OUT_T = ROOT / "results" / "case_tc_channel_v1.txt"
HIST = Path("/home/claude/work/mechanical/v352/tb70/hist")
BPKG = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/bpkg/bpkg_abort_v352_v1.json")
RUNS = {
    "B1_rev3_merged": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b",
    "B1_rev4_GVHI": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVHI",
    "B1_rev4_GVLO": "DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_R4_GVLO",
    "A1_rev3_merged": "DC-A1dispp99_tg711_hi_SS316L_L2.5_v352_NF2b",
}
STATION_MM = (12.6, 17.6)          # [MECH bpkg normal_operation_case_TC.station] TC-01 OD 12.6-17.6 mm aft of the injector face
A_C = 150.0                         # [LEAD 243 (3) ADOPTED] case-TC abort, 423.15 K
T_ARMED_MAX_C = 137.74              # [MECH bpkg false_trip_floor_C, SIM] B1 rev-3 merged perfect-contact armed maximum

DS_MAX = ("DATASHEET Maxim/ADI MAX31856 19-7534 Rev 0 (2/15), Electrical Characteristics; retrieved 2026-10-20 from "
          "www-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/MAX31856.pdf (analog.com media)")
LIT_IEC = "LITERATURE IEC 60584-1:2013 tolerance classes, type K Class 1 +/-1.5 C over -40..375 C (AS RECALLED, TO-VERIFY against the standard)"
LIT_NIST = "LITERATURE NIST ITS-90 type K reference function (NIST Monograph 175), coefficients AS RECALLED, checked E(100 C) = 4.096 mV"


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


# ---------------- NIST ITS-90 type K, 0..1372 C (mV, C)
_C = [-0.176004136860e-01, 0.389212049750e-01, 0.185587700320e-04, -0.994575928740e-07, 0.318409457190e-09,
      -0.560728448890e-12, 0.560750590590e-15, -0.320207200030e-18, 0.971511471520e-22, -0.121047212750e-25]
_A0, _A1, _A2 = 0.1185976, -0.1183432e-03, 126.9686


def emf_K_mV(t):
    return sum(c * t ** i for i, c in enumerate(_C)) + _A0 * math.exp(_A1 * (t - _A2) ** 2)


def seebeck_K_uV(t):
    d = sum(i * c * t ** (i - 1) for i, c in enumerate(_C) if i > 0)
    d += _A0 * math.exp(_A1 * (t - _A2) ** 2) * 2.0 * _A1 * (t - _A2)
    return 1000.0 * d                                      # uV/K


assert abs(emf_K_mV(100.0) - 4.096) < 0.0015 and abs(emf_K_mV(1000.0) - 41.276) < 0.003, "NIST type K function check failed"


def station_series(label):
    z = np.load(HIST / f"{label}_hist.npz", allow_pickle=False)
    info = json.loads(str(z["info"]))
    t, X, T = z["t_s"], z["od_X"], z["od_T"] - 273.15
    aft = -(X[:, 1] - info["inj_face_z_mm"])               # mm aft of the injector face (thermal frame z decreases aft)
    sel = np.where((aft >= STATION_MM[0] - 1e-6) & (aft <= STATION_MM[1] + 1e-6))[0]
    order = np.argsort(aft)
    return {"t": t, "aft": aft, "T": T, "sel": sel, "order": order, "info": info,
            "file": str(HIST / f"{label}_hist.npz"), "sha": sha16(HIST / f"{label}_hist.npz")}


def interp_at(s, k, mm):
    a, T = s["aft"][s["order"]], s["T"][k, s["order"]]
    m = (a >= 5.0) & (a <= 25.0)
    return float(np.interp(mm, a[m], T[m]))


def main():
    out = {"script": "calc/v2p11/case_tc_channel_v1.py", "version": "v1", "date": "2026-10-20",
           "status": "CALC / DERIVED on SIM inputs and DATASHEET / LITERATURE / ASSUMED terms as tagged; not physical approval",
           "inputs": {}, "notes": []}
    for k, lab in RUNS.items():
        out["inputs"][k] = {"file": str(HIST / f"{lab}_hist.npz"), "sha256_16": sha16(HIST / f"{lab}_hist.npz"),
                            "tag": "SIM (Mechanical CalculiX thermal, read only; 20 C start in every run)"}
    out["inputs"]["bpkg"] = {"file": str(BPKG), "sha256_16": sha16(BPKG), "tag": "Mechanical (b) package (SIM / CALC)"}
    bp = json.loads(BPKG.read_text())
    assert abs(bp["normal_operation_case_TC"]["false_trip_floor_C"] - T_ARMED_MAX_C) < 1e-9
    out["inputs"]["firmware_v2p10_hub"] = {
        "engine_ecu.cpp": "06-electronics/firmware/src/core/engine_ecu.cpp 6e62a7e4e37930bd: l.1043 hot = MV latched/OPEN AND tc_K > "
                          "kCaseOverTemp_K; l.1050 p_otemp_.step(hot, kOverTempTime_s, dt) -> OVER_TEMP abort in IGNITION / RUN / "
                          "PREPRESS / PURGE; l.763 ARM check (direct, no persistence, k < 3 incl. the nozzle holder TC3)",
        "config.h": "l.391 kCaseOverTemp_K 448.15; l.397 kCaseRelightMax_K 433.15; l.404 kOverTempTime_s 0.20 s [MECH 2026-10-13]",
        "engine_ecu.h": "l.191 caseHot(): direct comparison with kCaseRelightMax_K (relight / start refusal CASE_HOT)",
        "correction_to_brief": "the v2.10 in-burn case-TC abort HAS a 0.2 s persistence (one Persist shared by TC1 / TC2 / TC3); the "
                               "direct comparisons are the ARM check and the start refusal"}

    # ---------------- station histories
    S = {k: station_series(v) for k, v in RUNS.items()}
    hist = {}
    for k in ("B1_rev3_merged", "B1_rev4_GVHI", "B1_rev4_GVLO"):
        s = S[k]
        t = s["t"]
        ke = int(np.argmin(abs(t - 21.651)))
        smax = s["T"][:, s["sel"]].max(axis=1)
        rate_end = float((smax[ke] - smax[ke - 1]) / (t[ke] - t[ke - 1]))
        hist[k] = {"armed_end_t_s": float(t[ke]), "station_max_C": float(smax[ke]), "rate_end_K_per_s": round(rate_end, 3),
                   "node_spread_K": float(s["T"][ke, s["sel"]].max() - s["T"][ke, s["sel"]].min()),
                   "profile_C_at_mm": {f"{mm:.2f}": round(interp_at(s, ke, mm), 3) for mm in (12.6, 13.0, 13.48, 14.0, 15.1, 16.1, 17.6)},
                   "post_burn_1s_C": float(smax[int(np.argmin(abs(t - 22.651)))])}
    out["station_history_B1"] = hist
    r_basis = max(h["rate_end_K_per_s"] for h in hist.values())          # highest end-of-burn station rate of the three bounds

    # ---------------- constants and terms
    S150, S138, S25 = seebeck_K_uV(150.0), seebeck_K_uV(T_ARMED_MAX_C), seebeck_K_uV(25.0)
    fs_uV = 78125.0                      # [DS Note 7] input-referred full scale at AV 8 (type K needs the +/-78.125 mV range: 54.9 mV at 1372 C)
    k_cj = S25 / S138                    # a cold-junction error maps into the hot-junction reading by S(Tcj)/S(Thot)
    P_conv_max = 0.110 + 0.013           # [DS] auto conversions 2..n at 50 Hz 98-110 ms; + open-circuit test every 16th conversion (Table 4, 13 ms
                                         #  typ at OCFAULT 01 for < 5 kOhm and a filter tau < 2 ms: 200 ohm x 105 nF = 21 us) -> 123 ms worst gap
    t_persist = 0.200                    # [config.h kOverTempTime_s, MECH 2026-10-13]
    t_det = 0.5 * 0.110 + P_conv_max + 0.002 + t_persist   # first conversion whose average is above A + HAL read + persistence
    n_conv = [math.ceil(t_persist / 0.110 + 1e-9), math.ceil(t_persist / 0.098 + 1e-9) + 0]

    terms = [
        # name, bound_K (both signs unless one_sided), source tag, note
        ("tc_wire_class1", 1.5, LIT_IEC + "; BOM v2.2 row 203 specifies Class 1", "EMF deviation of the supplied TC pair"),
        ("cj_sensor", 0.7 * k_cj, DS_MAX + ": cold-junction temperature error +/-0.7 C (TA -20..+85 C)",
         f"x S(25 C)/S(137.7 C) = {k_cj:.3f}; board -20..+85 C ASSUMED (bay; ARM <= 45 C bay)"),
        ("cj_gradient_terminal_to_die", 1.0, "ASSUMED (layout not started): J605/J606 within 5 mm of U604/U605, isothermal copper "
         "pour, no power part within 20 mm (datasheet: keep heat sources away from the cold junction)",
         "includes the die self-heating 2 mA x 3.3 V x 110 K/W (TSSOP-14 theta_JA AS RECALLED) = 0.73 K max, DERIVED; B-TC-1 measures it"),
        ("adc_fullscale_inl", 0.0015 * fs_uV / S138, DS_MAX + ": Full-Scale and INL Error +/-0.15 %FS (TA -20..+85 C), FS 78.125 mV",
         "datasheet-literal bound at any input (117.2 uV); a pure gain error would give 0.15 % of the 4.6 mV signal = 0.17 K "
         "(information, not taken)"),
        ("adc_offset", 11.7 / S138, DS_MAX + ": input offset +/-11.7 uV (AV 8, TA -20..+85 C)", ""),
        ("linearisation", 0.13, DS_MAX + ": Thermocouple Linearity Correction Error type K -0.13 / +0.12 C", ""),
        ("noise_6sigma", 6.0 * 1.3 / S138, DS_MAX + ": input-referred noise 1.3 uVrms (AV 8), AVGSEL = 1 sample", "6 sigma of one conversion"),
        ("bias_current_x_leads", (65e-9 * 6.0 + 4e-9 * 215.0) * 1e6 / S138,
         DS_MAX + ": TC bias current -10..+65 nA, differential +/-4 nA (-40..+85 C); leads ASSUMED 3 m 24 AWG K (Chromel 3.44 / "
         "Alumel 1.43 ohm/m AS RECALLED) + 2 x 100 ohm filter", "DERIVED, negligible"),
        ("emi_ground_offset", 0.5, "ASSUMED: ungrounded (isolated) junction, BIAS to T- (DS), shielded twisted pair, 100 ohm + 100 nF + "
         "2 x 10 nF filter (schematic v2.5), 50 Hz notch; spikes of one conversion are rejected by the persistence",
         "TO-VERIFY at B-TC-1 (servos, pintle rail and spark running) and IGN-1"),
        ("wire_inhomogeneity_install", 0.3, "ASSUMED: cold work from forming / clamping in the gradient zone (no anneal)",
         "TO-VERIFY at B-TC-1 (in-situ comparison)"),
    ]
    stack_hi = [{"term": n, "bound_K": round(b, 3), "source": s, "note": note} for (n, b, s, note) in terms]
    place_hi = hist["B1_rev3_merged"]["profile_C_at_mm"]["13.00"] - T_ARMED_MAX_C   # junction at 13.5 +/- 0.5 mm: forward limit
    stack_hi.append({"term": "junction_placement_13p5_pm0p5_mm", "bound_K": round(max(place_hi, 0.0), 3),
                     "source": "DERIVED from the merged B1 end-of-burn OD profile (SIM)",
                     "note": "callout: junction centre 13.5 +/- 0.5 mm aft of the injector face (the hottest station node 13.48 mm); "
                             "at the band's forward edge 12.6 mm it would be +0.46 K"})
    stack_hi.append({"term": "surface_contact_and_lag", "bound_K": 0.0, "source": "DERIVED (sign): on a rising or steady hotter case the "
                     "junction reads LOW (lag, fin and pad heat loss); leads routed on the hoop isotherm, no path over a hotter region",
                     "note": "a credit on the false-trip side, NOT taken"})
    stack_hi.append({"term": "persistence_filter", "bound_K": 0.0, "source": "config.h kOverTempTime_s 0.20 s",
                     "note": f"no static error; needs {n_conv[0]}-{n_conv[1]} consecutive conversions above A (98-110 ms each), so one "
                             "corrupted conversion cannot trip; on the B1 ramp ending at disarm it is a further credit, NOT taken"})
    wc_hi = sum(x["bound_K"] for x in stack_hi)
    rss_hi = math.sqrt(sum(x["bound_K"] ** 2 for x in stack_hi))
    margin = A_C - T_ARMED_MAX_C
    out["A1a_false_trip_side"] = {
        "criterion": "true station at 137.74 C (B1 rev-3 merged perfect contact, armed maximum at the end of the burn): reading must stay "
                     "<= 150.00 C; margin 12.26 K",
        "terms": stack_hi, "worst_case_K": round(wc_hi, 2), "rss_K": round(rss_hi, 2),
        "margin_K": round(margin, 2), "worst_case_spare_K": round(margin - wc_hi, 2), "rss_spare_K": round(margin - rss_hi, 2),
        "verdict": "INSIDE +12.3 K (worst case and RSS)" if wc_hi < margin else "NOT INSIDE",
        "board_hot_variant": {"note": "if the ECU board runs -40..+105 C: FS+INL 0.2 %FS and CJ +/-1.0 C [DS]",
                              "worst_case_K": round(wc_hi - 0.0015 * fs_uV / S138 + 0.002 * fs_uV / S138 - 0.7 * k_cj + 1.0 * k_cj
                                                    - 11.7 / S138 + 13.3 / S138, 2)},
        "armed_window": "the abort is armed only in IGNITION / RUN (and PREPRESS / PURGE) with the MV latched or OPEN; MECO enters "
                        "SHUTDOWN and ends the arming at the command (burning = IGNITION || RUN), so the post-burn soak (+5.9 K in "
                        "the first second, SIM) never meets the abort; in SHUTDOWN it can only set the OVER_TEMP fault bit",
        "hot_day_sensitivity": {
            "basis": "every Mechanical thermal run starts at 20 C (ASSUMED); for a convective-conductive case with T_gas >> T_case "
                     "dT_station/dT0 = 1 - (T - T0)/(T_aw - T0) = about 0.96 (T_aw about 2800 K ASSUMED) [DERIVED]",
            "margin_K_at_T0_C": {str(T0): round(margin - 0.96 * (T0 - 20.0), 2) for T0 in (20, 25, 30, 35, 40)},
            "finding": "the 12.26 K margin is a 20 C-start margin: a stand B1-length burn with the engine at T0 > about "
                       f"{20 + (margin - wc_hi) / 0.96:.1f} C no longer covers the worst-case channel, > about {20 + (margin - rss_hi) / 0.96:.1f} C "
                       "not the RSS; flight A1 (station armed max 83.46 C) keeps > 45 K at a 40 C day. Lead / Mechanical: a hot-day "
                       "B1 run or a stand T0 limit for B1-length burns"},
    }

    # ---------------- (b) low-reading tolerance at the trip
    k_cj150 = S25 / S150
    static_lo = [
        ("tc_wire_class1", 1.5, LIT_IEC),
        ("cj_sensor", 0.7 * k_cj150, DS_MAX),
        ("cj_gradient_terminal_to_die", 1.0, "ASSUMED (as above)"),
        ("adc_fullscale_inl", 0.0015 * fs_uV / S150, DS_MAX),
        ("adc_offset", 11.7 / S150, DS_MAX),
        ("linearisation", 0.13, DS_MAX),
        ("noise_6sigma", 6.0 * 1.3 / S150, DS_MAX),
        ("bias_current_x_leads", (65e-9 * 6.0 + 4e-9 * 215.0) * 1e6 / S150, "DERIVED"),
        ("emi_ground_offset", 0.5, "ASSUMED"),
        ("wire_inhomogeneity_install", 0.3, "ASSUMED"),
    ]
    st_wc = sum(b for _, b, _ in static_lo)
    st_rss = math.sqrt(sum(b * b for _, b, _ in static_lo))
    # placement: the reading point can sit 0.5 mm aft of the hottest station node; the TB surrogate shifts the end-of-burn field
    place_lo = max(hist[k]["station_max_C"] - hist[k]["profile_C_at_mm"]["14.00"] for k in hist)
    # pad installation (DESIGN proposal): TC spot-welded to a 4 x 4 x 0.05 mm 304 shim, polyimide 25 um (electrical isolation) bonded
    # to the 6061 OD with two 25 um adhesive layers; two 0.25 mm glass-braid K leads
    A_pad = 16e-6
    R_c = 25e-6 / (0.12 * A_pad) + 2 * 25e-6 / (1.0 * A_pad)            # [ASSUMED k: polyimide 0.12, filled adhesive 1.0 W/mK]
    C_pad = 0.8e-9 * 7900 * 500 + 1.6e-9 * 2000 * 1000                   # shim + adhesive / overcoat 0.1 mm [ASSUMED]
    h_out = 15.0 + 3.3                                                     # [ASSUMED] natural convection + radiation (eps 0.3)
    R_surf = 1.0 / (h_out * A_pad)
    kA_leads = (19.0 + 30.0) * math.pi / 4 * (0.25e-3) ** 2              # Chromel / Alumel k AS RECALLED
    G_fin = math.sqrt(h_out * 2 * math.pi * 0.25e-3 * kA_leads)
    dT_case_amb = 150.0 - 25.0
    ss_err = dT_case_amb * R_c * (1.0 / R_surf + G_fin) / (1.0 + R_c * (1.0 / R_surf + G_fin))
    tau_calc = C_pad * R_c
    tau_target = 0.25                                                      # [DESIGN target; B-TC-1 acceptance]
    rows = []
    for r in (3.5, r_basis, 14.0, 28.0):
        dyn = r * (tau_target + t_det)
        rows.append({"rate_K_per_s": round(r, 2), "lag_K": round(r * tau_target, 2), "detection_delay_K": round(r * t_det, 2),
                     "worst_case_K": round(st_wc + place_lo + ss_err + dyn, 2),
                     "rss_static_plus_deterministic_K": round(st_rss + place_lo + ss_err + dyn, 2),
                     "T_F1_station_C_worst": round(A_C + st_wc + place_lo + ss_err + dyn, 1)})
    basis_row = rows[1]
    out["A1b_low_reading_tolerance"] = {
        "definition": "true station metal minus the reading when the abort command is issued (reading crossed 150.00 C and the "
                      "persistence completed), on a station heating at rate r",
        "static_terms": [{"term": n, "bound_K": round(b, 3), "source": s} for (n, b, s) in static_lo],
        "static_worst_K": round(st_wc, 2), "static_rss_K": round(st_rss, 2),
        "placement_K": {"v": round(place_lo, 2), "basis": "junction up to 0.5 mm aft of the hottest station node (callout 13.5 +/- 0.5 mm); "
                        "max over the three B1 bounds, field shape of the end of burn (the TB surrogate is a uniform shift) [DERIVED SIM]"},
        "surface_mount": {
            "installation_DESIGN": "TC junction spot-welded to a 4 x 4 x 0.05 mm 304 SS shim; 25 um polyimide film between shim and "
                                   "the 6061 case OD (electrical isolation: the MAX31856 needs a floating TC, BIAS to T-, DS Note 6); "
                                   "high-temperature filled adhesive both sides (>= 200 C continuous rating: soak 190.9 C SIM); 0.25 mm "
                                   "glass-braid K leads anchored 15 mm along the hoop isotherm, then strain-relieved; no connector "
                                   "(continuous Class 1 wire to J605 / J606)",
            "R_contact_K_per_W": round(R_c, 2), "C_junction_J_per_K": round(C_pad, 4), "tau_calc_s": round(tau_calc, 3),
            "steady_error_K": round(ss_err, 2), "steady_basis": "pad top-face loss (h 18.3 W/m2K incl. radiation ASSUMED) and the lead "
                                                              "fin through R_contact at 150 C case / 25 C bay [DERIVED]",
            "tau_target_s": tau_target, "tau_basis": "DESIGN target (the calculated pad tau is shorter; a void or a thicker bond line "
                                                    "raises it): B-TC-1 measures tau and the steady offset; acceptance tau <= 0.25 s, "
                                                    "|offset| <= 0.6 K"},
        "detection_delay_s": {"v": round(t_det, 3), "basis": "half a 110 ms conversion (result = window average) + the 123 ms worst "
                              "conversion gap (DS: 98-110 ms at 50 Hz + 13 ms OC test every 16th) + 2 ms HAL read + 0.200 s persistence"},
        "rows": rows,
        "basis_rate_K_per_s": round(r_basis, 2),
        "basis_rate_note": "highest B1 end-of-burn station rate of the three bounds (GVHI 6.99 K/s; merged 6.51, GVLO 6.73) = a burn "
                           "overrunning at the nominal heating rate; a faster failure (film-cooling loss, hot streak) gives "
                           "delta = static + placement + steady + r x (tau + t_det)",
        "formula_K": f"delta_lo = {st_wc + place_lo + ss_err:.2f} + r x {tau_target + t_det:.3f} (worst case); "
                     f"{st_rss + place_lo + ss_err:.2f} + r x {tau_target + t_det:.3f} (RSS of the static terms)",
        "T_F1_exposure_station_C": {"worst_case_at_basis_rate": basis_row["T_F1_station_C_worst"],
                                    "rss_static_at_basis_rate": round(A_C + basis_row["rss_static_plus_deterministic_K"], 1),
                                    "note": "Mechanical adds its station-to-part offset (TC-01 max about A + 1.4 to 2.6 K, 243 (3)(c))"},
        "valve_closure_after_command": "MV-P closes about 30 ms after the abort (ASSUMED, B-MV-1): + r x 0.03 s, in Mechanical's "
                                       "post-trip history, not in this tolerance",
    }
    # calibrated variant (B-TC-1 channel calibration at 150 C, CJTO trim)
    cal = [("reference", 0.3), ("cj_variation", 0.5), ("adc_residual_tempco", 0.0010 * fs_uV / S150), ("linearisation", 0.13),
           ("noise_6sigma", 6.0 * 1.3 / S150), ("emi", 0.5), ("cj_gradient_residual", 0.5), ("inhomogeneity", 0.3)]
    cal_wc = sum(b for _, b in cal)
    out["A1b_low_reading_tolerance"]["after_B_TC_1_calibration"] = {
        "method": "each case TC on its pad on a heated 6061 coupon with its own ECU channel against a reference thermometer at 150 C; "
                  "offset written to CJTO (DS: +/-8 C, 0.0625 C LSB)",
        "terms_K": {n: round(b, 3) for n, b in cal}, "static_worst_K": round(cal_wc, 2),
        "adc_residual_basis": "DS FS+INL 0.15 %FS (-20..85 C) minus 0.05 %FS (25 C) = 0.10 %FS: board-temperature residual (bound)",
        "worst_case_at_basis_rate_K": round(cal_wc + place_lo + ss_err + r_basis * (tau_target + t_det), 2)}

    # ---------------- persistence and its cost
    out["persistence"] = {
        "as_built_v2p10": "0.200 s of 1 ms ticks on the HAL-held reading (one Persist for TC1 / TC2 / nozzle holder)",
        "conversion_count": f"{n_conv[0]} consecutive conversions above A when the conversion period is >= 100 ms, {n_conv[1]} when < 100 ms (DS 98-110 ms)",
        "v2p11": "kept (no change); the HAL rule is made explicit: auto mode, 50 Hz notch, AVGSEL 1, OC test every 16 conversions, "
                 "any SR fault bit -> tc_valid false for that channel",
        "trip_delay_cost": {"t_det_s": round(t_det, 3), "of_which_persistence_s": t_persist,
                            "K_at_basis_rate": round(r_basis * t_det, 2), "K_per_K_per_s": round(t_det, 3)},
        "alternative_not_proposed": "0.12 s (still >= 2 conversions at <= 110 ms) would save 0.08 s (0.56 K at 7 K/s) at the cost of "
                                    "a single-conversion spike rejection margin of 10 ms; not proposed"}

    # ---------------- A2 relight refusal
    a1 = S["A1_rev3_merged"]
    t = a1["t"]
    sm = a1["T"][:, a1["sel"]].max(axis=1)
    k_rl = int(np.argmin(abs(t - 22.211)))
    k_pg = int(np.argmin(abs(t - (22.211 - 2.90))))
    k_end = int(np.argmin(abs(t - 26.781)))
    rate_b2_end = float((sm[k_end] - sm[k_end - 1]) / (t[k_end] - t[k_end - 1]))
    rise_burn2 = float(sm[k_end] - sm[k_rl])
    rise_purge = float(sm[k_rl] - sm[k_pg])
    allowance = rise_purge + rise_burn2 + 1.0 * rate_b2_end + 1.0
    R_prop = 5.0 * math.floor((A_C - allowance) / 5.0)
    nominal_start_reading = float(sm[k_pg]) + 20.0 + wc_hi
    out["A2_relight_refusal"] = {
        "v2p10": "kCaseRelightMax_K 433.15 K (160 C) > the new A 150 C: a start would be accepted at a case reading that aborts as "
                 "soon as the MV latches (PURGE / PREPRESS / IGNITION are armed) -> relight lockout; the v2.10 static_assert "
                 "(kCaseRelightMax_K <= kCaseOverTemp_K) fails to compile at A = 423.15 K",
        "check_points": "startBlock() refuses CASE_HOT in ARMED / COAST / PREPRESS (engine_ecu.cpp l.546), i.e. at the PURGE command and at "
                        "a COAST relight; not re-checked inside PURGE",
        "A1_merged_SIM": {"station_at_PURGE_cmd_C": round(float(sm[k_pg]), 2), "station_at_relight_E0_C": round(float(sm[k_rl]), 2),
                          "station_end_relight_burn_C": round(float(sm[k_end]), 2), "rise_purge_K": round(rise_purge, 2),
                          "rise_relight_burn_K": round(rise_burn2, 2), "rate_end_relight_burn_K_per_s": round(rate_b2_end, 2)},
        "allowance_K": {"v": round(allowance, 2), "basis": "purge rise + relight-burn rise (A1 rev-3 merged dispersed p99, SIM) + 1.0 s "
                        "longer relight burn at its end rate + 1.0 K relative channel error between two readings seconds apart "
                        "(noise, EMI, CJ drift; offset terms cancel on the same channel) [DERIVED]"},
        "proposed_C": R_prop, "proposed_K": round(R_prop + 273.15, 2),
        "check_consistency": f"{R_prop:.0f} C + {allowance:.1f} K = {R_prop + allowance:.1f} C <= A 150 C",
        "check_no_nominal_refusal": f"A1 nominal start reading <= {nominal_start_reading:.1f} C (station at the PURGE command "
                                    f"{float(sm[k_pg]):.1f} C + 20 K hot-day shift ASSUMED + high-side channel {wc_hi:.1f} K) < {R_prop:.0f} C",
        "firmware_v2p11": "kCaseRelightMax_K = proposed value, kCaseRelightRise_K = 150 - proposed; static_assert(kCaseRelightMax_K + "
                          "kCaseRelightRise_K <= kCaseOverTemp_K); ARM refuses a case TC above kCaseRelightMax_K (the start limit) and "
                          "the nozzle holder above kNozzleHolderOverTemp_K (v2.10 compared all three with the abort value)",
        "status": "PROPOSED, lead decides",
    }
    out["seebeck_uV_per_K"] = {"25C": round(S25, 2), "137.74C": round(S138, 2), "150C": round(S150, 2), "tag": LIT_NIST}

    OUT_J.write_text(json.dumps(out, indent=1))
    L = []
    L.append(f"A1(a) false-trip side at A 150 C vs true 137.74 C (margin {margin:.2f} K): worst case {wc_hi:.2f} K, RSS {rss_hi:.2f} K -> "
             f"{out['A1a_false_trip_side']['verdict']} (spare {margin - wc_hi:.2f} / {margin - rss_hi:.2f} K)")
    for x in stack_hi:
        L.append(f"   {x['term']:34s} {x['bound_K']:6.3f} K  {x['source'][:110]}")
    L.append(f"   hot day: margin at T0 25/30/40 C = {out['A1a_false_trip_side']['hot_day_sensitivity']['margin_K_at_T0_C']}")
    L.append(f"A1(b) low-reading: static worst {st_wc:.2f} K (RSS {st_rss:.2f}), placement {place_lo:.2f}, surface steady {ss_err:.2f} "
             f"(pad tau calc {tau_calc:.3f} s, target {tau_target} s), t_det {t_det:.3f} s")
    for r in rows:
        L.append(f"   r {r['rate_K_per_s']:5.2f} K/s: worst {r['worst_case_K']:5.2f} K (RSS-static {r['rss_static_plus_deterministic_K']:5.2f}) "
                 f"-> T-F1 station {r['T_F1_station_C_worst']:.1f} C")
    L.append(f"   after B-TC-1 calibration: static worst {cal_wc:.2f} K; at the basis rate {out['A1b_low_reading_tolerance']['after_B_TC_1_calibration']['worst_case_at_basis_rate_K']} K")
    L.append(f"A2 relight refusal: allowance {allowance:.2f} K -> proposed {R_prop:.0f} C ({R_prop + 273.15:.2f} K); "
             f"{out['A2_relight_refusal']['check_no_nominal_refusal']}")
    OUT_T.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print("json", sha16(OUT_J), "txt", sha16(OUT_T))


if __name__ == "__main__":
    sys.exit(main())
