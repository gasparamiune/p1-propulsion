"""m2_changelog_1013b v2 (GNC, 2026-10-13; v2: after the lead decisions of 2026-10-13 evening - planning value 0.81 s adopted,
option (c) adopted provisionally, B1 cap 62 m provisional; v1 composed the lines for the proposal stage and was not appended):
compose the GNC lines for interfaces/CHANGELOG.md (append-only) from the built gnc.json v3, so that no number is hand-copied.
Prints the lines; the caller appends them after reading the hub file again.
Format: date | owner | file vN | what changed | why.
Env: GNC_PUB_SHA (sha256/16 of the published gnc.json), GNC_DCI_SHA (sha256/16 of the published duty-cycle index), GNC_GJ3."""
import json
import os

O = "/home/claude/work/space/out"
D = "2026-10-13"
BASES = ("A1_none", "A1_pc", "A1J_none", "A1J_pc")
LAB = {"A1_none": "A1", "A1_pc": "A1 growth", "A1J_none": "ENG-07d", "A1J_pc": "ENG-07d growth"}


def jl(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return None


def pt(d):
    return f"{d['P_base']:.3f} -> {d['P_case']:.3f} (-{d['lost']}/+{d['gained']}, p {d.get('p_2sig', d['p'])})"


def main():
    g = jl(os.environ.get("GNC_GJ3", f"{O}/gnc_json/gnc_v3.json"))
    v28 = g["relight_planning_v28"]["v"]
    sm = v28["sweep_and_full_by_base"]
    oc = v28["option_c_fault_aware_plan"]
    vb = oc["verification_by_base"]
    rb = g["b1_regression_band"]["v"]
    lc = rb["lead_cap"]
    pg = f"{v28['planning_value_s']['v']:.2f}"
    pf = f"{v28['planning_value_fault_path_s']['v']:.2f}"

    def ps(pk):
        return "; ".join(f"{LAB[b]} " + "/".join(f"{sm[b][pk]['P_by_state'][s]:.3f}" for s in ("liq", "vapU", "vapF")
                                                 if s in sm[b][pk]["P_by_state"])
                         for b in BASES if b in sm and pk in sm[b])
    fpair = "; ".join(f"{LAB[b]} {pt(vb[b]['fault_paired'])}" for b in BASES if b in vb and "fault_paired" in vb[b])
    fspread = "; ".join(f"{LAB[b]} " + "/".join(f"{d['P_case']:.3f}" for d in vb[b]["fault_spread_paired"].values())
                        + " (at " + pg + " s: " + "/".join(f"{d['P_base']:.3f}" for d in vb[b]["fault_spread_paired"].values()) + ")"
                        for b in BASES if b in vb and vb[b].get("fault_spread_paired"))
    fu = "; ".join(f"{LAB[b]} " + ", ".join(f"{st} {pt(d)}" for st, d in vb[b]["false_unprimed_paired"].items())
                   for b in BASES if b in vb and vb[b].get("false_unprimed_paired"))
    mm = "; ".join(f"{LAB[b]} {vb[b]['maximin'][pg]['worst_P']:.3f} at {pg} s vs {vb[b]['maximin'][pf]['worst_P']:.3f} at {pf} s"
                   for b in BASES if b in vb and "maximin" in vb[b])
    qr = oc["q_star_range"]
    lines = []
    lines.append(
        f"{D} | gnc | (result) | RELIGHT v2.8 FULL SET + OPTION (c) VERIFICATION (sim6/run6 v2.7.1-dev start-delay option, FSW v2.7 "
        f"k_est_asc 2, 500 paired runs seed 101, start delay = Combustion RC-03 preopened E0->E2 per line state): adopted planning "
        f"value {pg} s, P liquid/vapour U01/full vapour {ps(pg)}. Option (c), same draws, 1.37 s fault path planned {pg} -> {pf} s: "
        f"{fpair}. Fault-path spread (E0->E2 + 0.56 s prep, 0.69-1.37 s) planned {pf} s, liq/vapU/vapF: {fspread}. Cost of a wrong "
        f"UNPRIMED (primed line planned {pf} s): {fu}. Worst P over the four line states: {mm}. Break-even prior of an unreported "
        f"emptying q* {qr[0]:.3f}-{qr[1]:.3f}. STALE OR MISSING FLAG (GNC decision): hold the last valid flag since the MECO valve "
        f"closure (UNPRIMED -> {pf} s, PRIMED -> {pg} s), none -> {pg} s: a stale flag is one fault, the plan is wrong only with a "
        "second unreported emptying, and UNPRIMED persists through the coast. Needed: Electronics UNKNOWN state (FC treats as "
        "UNPRIMED) and staleness limit (GNC assumes 0.3 s); Electronics + Mechanical segment drain time under a seat leak. "
        "gnc.json v3 relight_planning_v28.option_c_fault_aware_plan | lead decision 2026-10-13 (planning value 0.81 s; option (c) "
        "provisional, GNC verifies paired and decides the stale-flag plan)")
    mcl = rb["monte_carlo"]["rbl_B1_lead62_pc_k2"]
    mcl0 = rb["monte_carlo"]["tgl_B1_lead62_pc_k2"]
    sr = lc["nominal_worst_corner_scan_rows"].get("g0.11", {})
    ec = lc["engine_on_counter_vs_85m_sizing"]
    lines.append(
        f"{D} | gnc | (result) | B1 AT THE LEAD'S {lc['h_m']:g} m CAP (m2_regband_mc v1.1; band a x0.6-1.5 / n 0.35-0.68 uniform + "
        f"growth 7-11 %, 500 runs seed 101): nominal closes the +25 % rule at the worst corner ({rb['governing_cap']['case'].split('|g')[0]}, "
        f"g 0.11, reserve {100 * sr.get('reserve_frac', float('nan')):.1f} %); band + growth P {mcl['P']:.3f} vs growth only "
        f"{mcl0['P']:.3f} ({mcl['paired']}), {mcl['n_exhausted']} exhausted, usable liquid p01 {mcl['usable_left_p01_kg']:.3f} kg; "
        f"engine-on counter p99/max {ec['p50_p99_max_62m_band_growth_s'][1]:.2f}/{ec['p50_p99_max_62m_band_growth_s'][2]:.2f} s vs the "
        "85 m dispersed sizing cycles " + ", ".join(f"{k.replace('DC-B1_hop_85m_disp_', '')} {v:.2f} s" for k, v in ec["sizing_counters_s"].items())
        + f" (62 m runs above: {sum(ec['n_runs_above'].values())} in total): the 85 m cycles stay the conservative sizing cases. "
        "gnc.json v3 b1_regression_band.lead_cap, flight_profile.mission_plan_v3.B1.h_target_m | lead decision 2026-10-13 (B1 cap "
        "62 m provisional until T1-T4)")
    fct = g.get("over_thrust_fc_thrust")
    if fct:
        lines.append(f"{D} | gnc | (result) | FC_THRUST / OVER-THRUST ABORT: {fct['v']['finding']} gnc.json v3 over_thrust_fc_thrust | "
                     "lead decision 2026-10-13 (publish 3-sigma error and latency, false-abort rate, stuck-pintle detection, threshold)")
    sha = os.environ.get("GNC_PUB_SHA", "<sha>")
    lines.append(
        f"{D} | gnc | interfaces/gnc.json v3 (sha256/16 {sha}; builder m2_gnc_json_v3 v5, sim6/run6 v2.7.1-dev, iface_v3c = "
        "combustion.json v2.3 / mechanical.json v2 / electronics.json v1) | v3 PUBLISHED (supersedes v2 of 2026-10-12): mechanical.json "
        "v2 re-baseline, propellant closure, FSW v2.6 + v2.7 PROVISIONAL (k_est_asc 2), throat growth, abort law, no-retry and "
        "no-light accounting, dispersed duty cycles, relight 1.81 s (v2.7 sequence, history) and v2.8 (relight_planning_v28: "
        f"requirements.ignition.relight_planning_value_s = {pg} s lead decision, option_c_unprimed_s {pf} s provisional, "
        "stale_or_missing_flag GNC rule), B1 regression band and the lead's 62 m cap (b1_regression_band; mission plan B1 h_target_m "
        "62, h_sizing_m 85), verification_v26/v27/v271; "
        + ("over_thrust_fc_thrust; " if fct else "FC_THRUST error budget OPEN (m2_fc_thrust.py staged, not run); ")
        + "scripts, results and README v3 in 01-systems-gnc/sim and 01-systems-gnc/results. OPEN, new input after these runs: the "
        "~44 cm3 MV-to-seat segment (lead, MV-P/FS-01 Option A) replaces the 21.4 cm3 of the abort tail-off bracket, and the 1.37 s "
        "fault path / RC-03 tables were derived on the old segment while option (c) plans only 0.04 s above 1.37 s (open_items) | "
        "lead decisions 2026-10-12 / 2026-10-13; simulation only, no physical acceptance")
    dsha = os.environ.get("GNC_DCI_SHA", "<sha>")
    lines.append(
        f"{D} | gnc | 01-systems-gnc/duty_cycles/duty_cycles_index_v3.json v3 rev d (sha256/16 {dsha}; + 2 record CSVs) | rev c: "
        "airborne and leg-contact axial maxima and the location of the overall maximum (max_axial_definition; the overall maximum "
        "of the two failed max runs is the touchdown crash impact), cycle files unchanged; rev d: 'records' = A1 p99 cycles of the "
        f"v2.8 liquid-line (earliest) lights at the planning value {pg} s (DC-A1_full_flight_disp_p99_kest2_v28liq_v3, "
        "..._tg711_v3), RECORDS, not sizing cases | lead 2026-10-13: B1 governs thermal; GNC publishes the early-light A1 p99 cycle "
        "as a record once the fix is chosen")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
