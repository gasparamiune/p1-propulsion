"""Head-end bleed drive v1 (06-electronics, firmware v2.10, schematic v2.5), 2026-10-13.

Answers LEAD CHANGELOG 166 (3) items that need numbers before the bleed valve is selected:
  (1) hardware purge window (LTC6993-1 one-shot on the FC PURGE_EN line): bounds and the powered span it must cover;
  (2) purge mass at the firmware cap and at the hardware window bound, on the Combustion and the SIL flow basis;
  (3) valve flow requirement: Kv for 'valves >= 4 x the restriction capacity' on the decided path;
  (4) fast-release clamp (SS14 + SMAJ24A per channel, drawn since v2.4): drain voltage, release energy and release time for a
      PARAMETRIC coil set (the replacement valve's coil is unknown), against the SMAJ24A and DMN6075S ratings;
  (5) what a high-current N2O solenoid (candidate B, 8.6-10.3 A listed) implies for the drive.
Every input carries its tag. Missing data stays missing: the coil inductance, resistance and pull-in/hold currents are UNKNOWN, so
(4)-(5) are a parametric screen, not a design. Outputs: ../results/bleed_driver_v1.json, ../results/bleed_driver_v1.txt
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

# ---------------------------------------------------------------- inputs (tagged)
FW = {  # firmware v2.10 config.h (DESIGN / LEAD values, read from the source of this build)
    "kPurgeRelight_s": 2.90, "kPurgeFlow_s": 2.5, "kPurgeFlowEndLead_s": 0.05, "kHbleedOpenTime_s": 0.030,
    "kHbleedCloseTime_s": 0.080, "kHbleedPathBy_s": 0.10, "kHbleedVentMax_s": 0.030, "kFcPurgeEnLead_s": 0.020,
}
FW["kPurgeFlowStart_s"] = FW["kPurgeRelight_s"] - FW["kPurgeFlowEndLead_s"] - FW["kPurgeFlow_s"]          # DERIVED 0.35 s
FW["kHbleedCap_s"] = FW["kPurgeFlow_s"] + FW["kHbleedOpenTime_s"] + FW["kHbleedCloseTime_s"]               # LEAD formula 2.61 s
LTC6993 = {  # DATASHEET LTC6993 Rev F (analog.com 69931234fc.pdf, read 2026-10-13)
    "equation": "tOUT = NDIV x RSET / 50k x 1 us", "rset_range_ohm": [50e3, 800e3], "ndiv_divcode7": 2 ** 21,
    "divcode7_R1_R2_ohm": [1.0e6, 887e3], "err_max_25C": 0.023, "err_max_grade": 0.030, "rset_tol": 0.001,
    "startup": "OUT held low for 500 tMASTER; POL 0 stays low", "variant": "-1 rising edge, non-retriggerable",
}
RSET = 75.0e3                       # DESIGN (E96, 0.1 %)
MDOT_COMB_G_S = 73.0 / 2.5          # COMB (lead l.166 (3)): <= 73.0 g in 2.5 s on the decided path -> 29.2 g/s
MDOT_SIL_G_S = 78.6 / 2.5           # SIL S12 v2.10 purge_integrated_nominal (plant Cd 0.70, ASSUMED) -> 31.44 g/s
MASS_LIMIT_G = 76.0                 # LEAD l.166 (10) ICD-AIRFRAME purge mass
RESTRICTOR_EQ_D_M = 1.0e-3          # LEAD decided path: 0.707 mm per tap = 1.0 mm equivalent
CD_ASSUMED = 0.70                   # ASSUMED discharge coefficient (as the SIL plant)
SMAJ24A = {"VRWM_V": 24.0, "VBR_min_V": 26.7, "VBR_max_V": 29.5, "VC_max_V": 38.9, "IPP_A": 10.3, "PPP_W_10_1000us": 400.0,
           "source": "DATASHEET-class (Littelfuse/Vishay SMAJ series table, AS-RECALLED values; TO-VERIFY against the ordered part)"}
DMN6075S = {"VDS_V": 60.0, "ID_A": 2.0, "source": "DATASHEET DS37023 Rev 6-2 (as in ecu_design.py)"}
VSUP_V = 12.0                       # DESIGN +12V_ARM nominal (regulation band TO-VERIFY, RE-09)
VD_V = 0.5                          # SS14 forward drop at ~1 A (DATASHEET-class)


def window():
    t_nom = LTC6993["ndiv_divcode7"] * RSET / 50e3 * 1e-6
    e = LTC6993["err_max_grade"] + LTC6993["rset_tol"]
    t_min, t_max = t_nom * (1 - e), t_nom * (1 + e)
    # powered span from the PURGE command (firmware schedule): V1 opens at entry (fill step), V2 at flow start - open time
    # (+ path-proof delay worst case), V1 close command at flow start + flow - close time, V2 close command <= V1 close + close + vent
    fs = FW["kPurgeFlowStart_s"] + FW["kHbleedPathBy_s"]
    v1_close_cmd = fs + FW["kPurgeFlow_s"] - FW["kHbleedCloseTime_s"]
    v2_close_cmd = v1_close_cmd + FW["kHbleedCloseTime_s"] + FW["kHbleedVentMax_s"]
    need = v2_close_cmd + FW["kFcPurgeEnLead_s"]
    nominal_span = FW["kPurgeFlowStart_s"] + FW["kPurgeFlow_s"] + FW["kHbleedVentMax_s"]
    return {"rset_ohm": RSET, "t_nom_s": round(t_nom, 4), "error_total": e, "t_min_s": round(t_min, 4), "t_max_s": round(t_max, 4),
            "rset_in_range": LTC6993["rset_range_ohm"][0] <= RSET <= LTC6993["rset_range_ohm"][1],
            "powered_span_needed_s": round(need, 3), "powered_span_nominal_s": round(nominal_span, 3),
            "margin_min_s": round(t_min - need, 3), "covers": t_min >= need,
            "cap_equal_window_would_cut_flow": FW["kHbleedCap_s"] < need,
            "basis": "DERIVED from config.h v2.10 schedule + DATASHEET LTC6993 Rev F"}


def masses(w):
    cap_flow = FW["kHbleedCap_s"] - FW["kHbleedOpenTime_s"] + FW["kHbleedCloseTime_s"]      # both commanded open for the cap
    hw_flow = w["t_max_s"] - FW["kHbleedOpenTime_s"] + FW["kHbleedCloseTime_s"]             # both open for the whole window
    rows = []
    for name, flow in [("nominal 2.5 s flow", FW["kPurgeFlow_s"]), ("firmware cap (both open 2.61 s)", cap_flow),
                       ("hardware window bound (both open t_max)", hw_flow)]:
        rows.append({"case": name, "flow_s": round(flow, 3), "mass_comb_basis_g": round(flow * MDOT_COMB_G_S, 1),
                     "mass_sil_basis_g": round(flow * MDOT_SIL_G_S, 1),
                     "le_76g_comb": flow * MDOT_COMB_G_S <= MASS_LIMIT_G, "le_76g_sil": flow * MDOT_SIL_G_S <= MASS_LIMIT_G})
    flow_76 = MASS_LIMIT_G / MDOT_COMB_G_S
    return {"rows": rows, "flow_for_76g_comb_s": round(flow_76, 3),
            "powered_both_open_for_76g_comb_s": round(flow_76 + FW["kHbleedOpenTime_s"] - FW["kHbleedCloseTime_s"], 3),
            "basis": "COMB 29.2 g/s (lead l.166 (3)) and SIL 31.44 g/s (S12 nominal); valve times ASSUMED 30/80 ms",
            "quantity": "VENTED N2O (vehicle-level mass leaving through the bleed; the 76 g limit applies to it). Tank LIQUID depletion is "
                        "larger: 81.6 g at 73.0 g vented, 8.6 g boils into the ullage (LEAD CHANGELOG 181 (10)); tank-outlet coverage "
                        "checks use the liquid figure"}


def kv_requirement():
    a = math.pi / 4 * RESTRICTOR_EQ_D_M ** 2
    kv_restr = 3600 * CD_ASSUMED * a * math.sqrt(2 * 1e5 / 1000.0)     # m3/h of water at 1 bar
    return {"restrictor_equivalent_d_mm": 1.0, "cd_assumed": CD_ASSUMED, "kv_restriction_m3h": round(kv_restr, 4),
            "kv_valve_min_m3h_4x": round(4 * kv_restr, 3),
            "seat_force_2mm_55bar_N": round(math.pi / 4 * (2e-3) ** 2 * 55e5, 1),
            "candidate_A_burkert_6027_1p5mm_kv_m3h": 0.07, "candidate_A_meets_kv": 0.07 >= 4 * kv_restr,
            "basis": "DERIVED (incompressible water-equivalent Kv; flashing N2O changes the real capacity: B-BLEED-1 measures)"}


def clamp_screen():
    vds = VSUP_V + VD_V + SMAJ24A["VBR_max_V"]
    e_pulse_J = SMAJ24A["PPP_W_10_1000us"] * 1.44e-3      # 10/1000 us exponential: energy ~ Ppk x 1.44 ms (DERIVED)
    rows = []
    for L_mH in (10.0, 30.0, 100.0):
        for I in (0.5, 1.0, 2.0, 10.0):
            L = L_mH * 1e-3
            vz = SMAJ24A["VBR_max_V"]
            e = 0.5 * L * I * I * vz / (vz + VD_V)
            t_rel = L * I / (vz + VD_V)
            rows.append({"L_mH": L_mH, "I_release_A": I, "E_tvs_mJ": round(e * 1e3, 2), "t_release_ms": round(t_rel * 1e3, 2),
                         "within_single_pulse_rating": e <= e_pulse_J, "fet_current_ok": I <= DMN6075S["ID_A"]})
    return {"vds_peak_V": round(vds, 1), "vds_ok_60V": vds < DMN6075S["VDS_V"], "tvs_single_pulse_energy_J": round(e_pulse_J, 3),
            "rows": rows, "smaj24a": SMAJ24A, "dmn6075s": DMN6075S,
            "note": "coil L, R and currents UNKNOWN (valve not selected): parametric screen. Repetitive release (purge per flight, BIT steps) "
                    "is far below any duty limit at these energies except the 10 A rows"}


def main():
    w = window()
    out = {"id": "bleed_driver", "version": "v1", "date": "2026-10-13", "owner": "electronics",
           "inputs": {"firmware": FW, "ltc6993": LTC6993, "mdot_comb_g_s": MDOT_COMB_G_S, "mdot_sil_g_s": round(MDOT_SIL_G_S, 3),
                      "mass_limit_g": MASS_LIMIT_G},
           "hardware_window": w, "purge_mass": masses(w), "valve_kv": kv_requirement(), "fast_release_clamp": clamp_screen(),
           "high_current_candidate_B": {
               "listed_current_A": [8.6, 10.3], "power_at_12V_W": [round(12 * 8.6, 1), round(12 * 10.3, 1)],
               "implications": ["DMN6075S (2.0 A) and the SS14/SMAJ24A clamp are NOT rated for it: channel redesign (FET >= 20 A, clamp >= SMCJ)",
                                "+12V_ARM must source 2 x 10 A peaks: power budget RE-09 and the boost converter rating TO-VERIFY",
                                "peak-and-hold (TI DRV110 class controller with external FET, Rev G 2018; Vs range TO-VERIFY) cuts the hold to the "
                                "coil's hold current (UNKNOWN)"],
               "source": "retail listing jbspowercentre.com 18020BNOS (conflicting 8.6 / 10.3 A), not a datasheet"},
           "findings": []}
    m = out["purge_mass"]["rows"]
    out["findings"] = [
        "hardware window %.3f-%.3f s covers the %.3f s scheduled powered span (margin %.3f s)" % (w["t_min_s"], w["t_max_s"], w["powered_span_needed_s"], w["margin_min_s"]),
        "a window equal to the 2.61 s both-open cap would cut the schedule (V1 is powered from the PURGE entry for the fill step)",
        "mass: nominal %.1f g (COMB basis) / %.1f g (SIL); firmware cap %.1f / %.1f g; hardware bound %.1f / %.1f g; limit 76 g" % (
            m[0]["mass_comb_basis_g"], m[0]["mass_sil_basis_g"], m[1]["mass_comb_basis_g"], m[1]["mass_sil_basis_g"],
            m[2]["mass_comb_basis_g"], m[2]["mass_sil_basis_g"]),
        "all masses are VENTED N2O; tank liquid depletion is larger (81.6 g at 73.0 g vented, LEAD CHANGELOG 181 (10))",
        "to keep the firmware cap inside 76 g on the COMB basis the both-open command must be <= %.3f s (cap today 2.61 s)" % out["purge_mass"]["powered_both_open_for_76g_comb_s"],
        "valve Kv >= %.3f m3/h (4 x restriction); Burkert 6027 1.5 mm Kv 0.07 fails" % out["valve_kv"]["kv_valve_min_m3h_4x"],
    ]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "bleed_driver_v1.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(OUT, "bleed_driver_v1.txt"), "w") as f:
        f.write("bleed_driver_v1 (Electronics 2026-10-13)\n" + "\n".join("- " + x for x in out["findings"]) + "\n")
    print("\n".join(out["findings"]))
    for r in out["fast_release_clamp"]["rows"]:
        if r["I_release_A"] in (1.0, 10.0):
            print("  L %5.0f mH I %4.1f A: E %8.2f mJ, t_rel %6.2f ms, pulse ok %s, FET ok %s" % (
                r["L_mH"], r["I_release_A"], r["E_tvs_mJ"], r["t_release_ms"], r["within_single_pulse_rating"], r["fet_current_ok"]))


if __name__ == "__main__":
    main()
