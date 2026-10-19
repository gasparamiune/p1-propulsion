"""m2_rev4_v32prop v1.0 (GNC rev4, 2026-10-19): corrected gnc.json v3.2 proposal set (REV-GNC-5 verdict table, lead
CHANGELOG 208 (6); line 213: the 210 m-class trim becomes the A1 configuration, the 285 m figures become comparators).
Items [0]-[10] keep the rev3 numbering (rev3 text quoted from rev3_results.json proposed_for_v3p2, sha256/16 below), with
the reviewer's verdict, the corrections applied and the corrected proposal. Items [11]-[17] are NEW in rev4 and have not
been reviewed (REV-GNC-5 delta re-check). GNC does not write gnc.json; the lead publishes after the independent check.
Output: out/rev4/v32/v32_proposals_rev4.json. Numbers are read from the evidence files named in each item."""
import hashlib
import json
import os
import time
from collections import OrderedDict

VERSION = "m2_rev4_v32prop v1.0"
SP = "/home/claude/work/space"
O = f"{SP}/out/rev4"
HUB = "/home/claude/work/shared-fallback/engine"
REV3R = f"{HUB}/01-systems-gnc/staging_v3.1/rev3/results/rev3_results.json"
REVIEW = f"{HUB}/reviews/REVIEW-GNC-R3.md"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None


def E(*ps):
    return [dict(path=p, sha256_16=sha16(p)) for p in ps]


def main():
    rev3 = json.load(open(REV3R))["proposed_for_v3p2"]["items"]
    res = json.load(open(f"{O}/rev4_results.json"))
    p2 = res["A1_apogee_P2"]["variants"]
    v = p2["v351"]["states"]
    dc = res["gate_delay_210m"]["D_crit_min_per_base"]
    rv = json.load(open(f"{O}/v32/v32_recompute.json"))
    g = res["ENG11"]["linear"]["grid"]
    r2 = res["R2v2"]["starve"]
    b = lambda st, h: v[st]["bands"][str(h)]  # noqa: E731
    items = []

    def item(i, verdict, corr, text, status, ev, tags, comparator=None):
        e = OrderedDict(index=i)
        if i <= 10:
            e["path"] = rev3[i]["path"]
            e["rev3_proposal"] = rev3[i]["proposal"]
        e["REV_GNC_5_verdict"] = verdict
        e["corrections_applied"] = corr
        e["proposal_rev4"] = text
        if comparator:
            e["comparator_285m"] = comparator
        e["status"] = status
        e["tags"] = tags
        e["evidence"] = ev
        items.append(e)

    # [0]
    item(0, "Publishable with corrections: fold in RV5-03, 05, 06, 09 and 10",
         ["RV5-03 pooled ECU-hold losses added", "RV5-05 W10 split of the e19|G73|L400 loss added",
          "RV5-06 withdrawn-value markers added (rev4 sidecars; rev3 untouched)", "RV5-09 both R2 windows",
          "RV5-10 AR(1) wording corrected"],
         ("Reference block /rev3_rev4 to staging_v3.1/rev3 (MANIFEST_rev3 79c2c8cd5d10e3c4) and staging_v3.1/rev4 (MANIFEST_rev4): "
          "status of rev3 P2-P9 and rev4 P2/ENG-11/RE-24/payload/R2-starve, findings rev3 F1-F11 and rev4 R4-F1..F8, each "
          "labelled. Folded corrections: (RV5-03) pooled over A1_none + A1J_pc all ECU-hold arms lose against release at E2: "
          "rh300c200 0.983 vs 0.992 (-11/+2, p 0.0225), rh400c200 0.979 vs 0.992 (-13/+0, p 2.4e-4), rh190c500 0.977 vs 0.992 "
          "(-15/+0, p 6.1e-5); (RV5-05) the e19|G73|L400 loss at 285 m is -40/+3 at W10 >= 6 m/s (p 3.0e-9) and -3/+0 inside "
          "W10 < 6 (p 0.25, n 728, low power); (RV5-06) withdrawn values are marked by sidecars in rev4/withdrawn_markers/ "
          "(W1 rh220/rh250 E2 + 0.22 s arms; W2 lit model 62.5 N x pcf_k incl. P4 gap_N/T_mid_N; W3 60 g bands SUPERSEDED); "
          "(RV5-09) R2 v2 carries both windows (item [6]); (RV5-10) 'AR(1) fails everywhere' reads 'fails for the same-RMS "
          "variants; with the frame-level RMS equal to the white model, B1 comp passes at all three correlation times and A1 "
          "comp passes at 5 ms by 0.0016 pp'."),
         "CORRECTED, for REV-GNC-5 delta re-check", E(f"{O}/v32/v32_recompute.json", f"{O}/wmark/WITHDRAWN_INDEX.json", REV3R),
         "DERIVED (recomputed from staged rev3 SIM tables) / SIM")
    # [1]
    item(1, "Publishable with corrections: RV5-04",
         ["band per 204 (1) (below about 2.1 s not counted), D_crit per threshold, L400 lead bins, pc offset +0.156 s; "
          "rev4 adds the 210 m recomputation (A1 trim)"],
         ("Record F1 as decided in 204 (1) / 208 (4): L* = 1.3 s stays the commit rule; a realised commit lead below about "
          "2.1 s is not counted as a landing. P by realised lead (285 m, nominal start, pooled contingency arms): 2.4-2.9 s "
          "0.994; 2.1-2.4 s 0.993; 1.9-2.1 s 0.982; 1.7-1.9 s 0.835; 1.5-1.7 s 0.604; 1.3-1.5 s 0.009; < 1.3 s 0; with L400 "
          "2.4-2.9 s 0.825, 2.1-2.4 s 0.764, 1.9-2.1 s 0.454, below 1.9 s 0. Gate-delay tolerance D_crit (gate delay that drives "
          "the worst run's lead below the threshold) at the A1 trim 210 m on v3.5.1 (DERIVED from the P2 tables, liq/pw "
          f"G73, N=1000 on the main bases): 2.4 s {dc['A1_none']['2.4s']} / {dc['A1J_pc']['2.4s']} s; 2.1 s "
          f"{dc['A1_none']['2.1s']} / {dc['A1J_pc']['2.1s']} s; 1.9 s {dc['A1_none']['1.9s']} / {dc['A1J_pc']['1.9s']} s; "
          f"1.3 s {dc['A1_none']['1.3s']} / {dc['A1J_pc']['1.3s']} s (A1_none / A1J_pc; A1J_none like A1_none +0.07 s, "
          "A1_pc like A1J_pc). The p01 tolerance for 2.1 s is 0.58 / 0.67 s. At 210 m 16 of 1000 runs per main base commit "
          "with zero slack at the gate opening and the nominal lead minimum is 2.264 s (A1_none) / 1.946 s (A1J_pc), so the "
          "285 m tolerance (3.765 s for 2.1 s; +0.156 s on pc bases) does NOT carry to 210 m: a gate fault of about 0.2-0.7 "
          "s now reaches the uncounted band in the worst 1 % of runs. The runs below 2.4 s at 210 m (3 / 2 per 1000) all "
          "landed in the sim; the P cost of a gate delay at 210 m is not flown (TO-VERIFY, next closure: gate-delay "
          "injection arm at 210 m). Predictor failure (commit at the plain trigger) is a separate fault class."),
         "CORRECTED, for REV-GNC-5 delta re-check; the 210 m gate-delay reading is NEW (rev4 finding R4-F5)",
         E(f"{O}/v32/v32_recompute.json", f"{O}/v32/dcrit_210.json"), "DERIVED from SIM tables",
         comparator=rv["RV5_04"]["D_crit_min_per_base"])
    # [2]
    item(2, "Publishable with corrections: RV5-03 and RV5-08; add NOT ADOPTED per 204 (2)",
         ["NOT ADOPTED status", "pooled losses (RV5-03)", "revisit rule per 208 (3) incl. RV5-08 timing margin"],
         ("Line-194 comparator (P6c) recorded as COMPARATOR and NOT ADOPTED (lead 204 (2), strengthened by 208 (3)): "
          "with a hold >= 0.30 s on the 200 N ramp it leaves no released-then-A3 residual and gives P_total LO 0.39-0.46, HI "
          "0-0.036, 0 at the worst states, only in the below-L* branch and only with Pc valid. Pooled over the two main bases "
          "all ECU-hold arms lose against release at E2 (rh300c200 -11/+2 p 0.0225; rh400c200 -13/+0 p 2.4e-4; rh190c500 "
          "-15/+0 p 6.1e-5; rh190c500 also loses against liq|none -12/+2 p 0.013). The 'ramp' P_success is the best case "
          "over both conventions and modes (an upper bound). Timing: at H = 0.30 s on the 200 N ramp lin1.0|LO is 0.25 ms "
          "short of the frame rule (latest trip 0.2902 s + 10 ms > 0.30 s); H = 0.19 s at 500 N has 2.5-2.7 ms. Revisit "
          "rule (208 (3)): expected gain q x P_total >= 0.5 pp per flight (q = gate-fault probability) with an ECU timing "
          "margin >= 10 ms on the hold frame rule, or the CF-4/T4 condition of 204 (2). The withdrawn E2 + 0.22 s figures "
          "(rh220/rh250) are marked W1. All at 285 m (COMPARATOR configuration); not re-flown at 210 m."),
         "CORRECTED, for REV-GNC-5 delta re-check", E(f"{O}/v32/v32_recompute.json", f"{O}/wmark/WITHDRAWN_INDEX.json"),
         "SIM / DERIVED")
    # [3]
    lb = b("liq", 210)
    item(3, "Publishable with corrections: RV5-01 and RV5-06; RV5-02 for context",
         ["rule restated per 208 (1) (80 g onset, UB95 <= 1.0 pp, monotone)", "60 g-basis bands SUPERSEDED (W3)",
          "250 m planning value WITHDRAWN (RV5-02, 208 (2))", "A1 = 210 m from rev4 P2 (line 213/214); 285 m F4/F5 as comparators"],
         ("A1 apogee target = 210 m (lead 214) by the line-208 rule on massprops v3.5.1 (488b47f9d55ff91b) in sim6 v2.9-dev: "
          "highest 5 m band h with h and every lower flown band showing no significant pooled loss (A1_none + A1J_pc, paired "
          "exact McNemar) against the v3d reference st|G73|h285 with the dip onset fixed at 80 g, and a one-sided 95 % upper "
          f"deficit bound <= 1.0 pp. N = 1000 per base. liq|G73: 210 m P {lb['P_case']} vs {lb['P_ref']}, "
          f"-{lb['lost']}/+{lb['gained']}, p {lb['p_exact']}, UB95 {lb['ub95_pp']} pp (Newcombe {lb['ub95_newcombe_pp']}) PASS; "
          f"215 m UB95 {b('liq', 215)['ub95_pp']} pp (fails by 0.03 pp; statistical, not a physical margin); 220/225 m "
          f"significant losses (p {b('liq', 220)['p_exact']} / {b('liq', 225)['p_exact']}). pw|G73: band 220 m (UB95 "
          f"{b('pw', 220)['ub95_pp']} pp), 225 m UB95 {b('pw', 225)['ub95_pp']} pp. Decision value = the lower state = 210 m. "
          "Four-base pooled (informational, A1_pc + A1J_none at N=500 added): liq 210 m -33/+28 UB95 0.595 pp PASS, 215 m "
          "-47/+29 p 0.0505 UB95 1.078 pp; pw 210 m UB95 0.277 pp, 215 m 0.498 pp. Sensitivity arms (N=500/base, flown at "
          "210 and 215 m only): ~80 g purge (G80) at 210 m vs the v3d reference liq UB95 0.97 pp / pw 0.62 pp PASS (vs G73 at "
          "the same band: liq -1/+0, pw identical); valve target 2 x 0.15 kg (v351t): liq 210 m (215 m UB95 1.21 pp), pw "
          ">= 215 m; v3.5.2 (-91.6 g, line 209): >= 215 m on both states (highest flown band, upper-censored). The rev3 F4/F5 "
          "285 m bands are COMPARATOR records; their 60 g-basis values are SUPERSEDED (204 (4)); the 250 m planning value is "
          "WITHDRAWN (208 (2)). The superseded 204 (3) reading would have given 230 m (liq) / 235 m (pw): kept as record."),
         "CORRECTED, for REV-GNC-5 delta re-check",
         E(f"{O}/p2/p2_rev4.json", f"{O}/mass_v351/mass_v351_vs_v3d.json", f"{O}/mass_v352/mass_v352_vs_v3d.json"),
         "SIM (flights) / DERIVED (band rule)",
         comparator="rev3 F4/F5 at 285 m on v35a/v35t: see rev3_results.json findings F4_mass_285m / F5_reserve_dip (60 g basis SUPERSEDED)")
    # [4]
    item(4, "Publishable with corrections: RV5-05",
         ["W10 split of the e19|G73|L400 loss", "P with the 80 g dip onset", "285 m = COMPARATOR (line 213)",
          "210 m coverage not flown stated"],
         ("285 m coverage tables (rev3 F6) recorded as COMPARATOR (the A1 trim is 210 m). The e19|G73|L400 loss is not a "
          "trim effect and lies almost entirely outside the hard launch-commit rule: all winds 0.946 vs 0.986 (-43/+3, p "
          "4.6e-10); W10 >= 6 m/s 0.816 vs 0.952 (-40/+3, p 3.0e-9, n 272); inside W10 < 6 m/s 0.9945 vs 0.9986 (-3/+0, p "
          "0.25, n 728, low power); against the same arm at 300 m -25/+24, p 1 (the loss is already in the rev2 data, line "
          "180); with the 80 g dip onset on both arms unchanged (-43/+3). Coverage at 210 m (e19, L400, wind sweep) is NOT "
          "FLOWN in rev4 (TO-VERIFY; next closure: the rev3 P3 coverage set re-flown at liq/pw|G73|v351|h210)."),
         "CORRECTED, for REV-GNC-5 delta re-check", E(f"{O}/v32/v32_recompute.json"), "SIM / DERIVED")
    # [5]
    item(5, "Publishable as written (a record, conditional on the 285 m trim)",
         ["condition not met: the 285 m trim was not adopted (line 214 A1 = 210 m)", "210 m reading added (DERIVED)"],
         ("The two 285 m A1 p99 records are NOT added (their condition, adoption of the 285 m trim, is not met; they stay "
          "staged in rev3/duty_cycles as records). DERIVED reading at the A1 trim from the P2 tables (table column burn_time = "
          "the sim6 engine-on counter, checked equal on the 285 m tables: p99 8.371 / 8.185 s): liq|G73|v351|h210 p99 8.374 / "
          "8.510 s on A1_none (runs 0-499 / 500-999), 8.205 / 8.277 s on A1J_pc, against 8.371 / 8.185 s at 285 m on the v3d "
          "ledger and the published A1 sizing counter 8.258 s. Line 213's consequence 'the A1 duty cycle shortens' is NOT "
          "supported on v3.5.1: the lower apogee shortens the ascent burn but the 1.37 kg heavier vehicle lengthens the "
          "landing burn, and the A1_none p99 stays above the A1 sizing counter as at 285 m and 300 m. B1 governs thermal and "
          "erosion (lead decision 2026-10-13), so this is a record, not a sizing case. A 210 m p99 cycle re-flown with the "
          "recorder (duty-cycle v3 format) is not produced (next closure)."),
         "CORRECTED (condition outcome stated), NEW 210 m reading for REV-GNC-5 delta re-check",
         E(f"{O}/p2/p2_rev4.json"), "DERIVED from SIM tables")
    # [6]
    w5, w8 = r2["windows"]["w0.5"], r2["windows"]["w0.8"]
    item(6, "Publishable with corrections: RV5-06 (gap_N, T_mid_N) and RV5-09",
         ["gap_N / T_mid_N marked WITHDRAWN (W2)", "both windows carried", "rev4 lit-side start-plateau bracket added",
          "answers to lead 2026-10-13 ~19:05Z (a)-(c)"],
         ("R2 v2 statistics (amendment V, Pc invalid from E2): flame-out side as found in rev3 (mode 3, design bound x 1.3 "
          "heat pick-up, HEM nominal): window 0.5 s all winds max 34.88 N, margin +2.28 N at T 37.16 N, 0/2072 released; "
          "W10 < 6 31.18 N, +5.98 N, 0/1502. Window 0.8 s all winds 39.45 N, -2.29 N, 4/2072 released (dead vehicles "
          "released); W10 < 6 31.86 N, +5.30 N, 0/1502. The hold is load-bearing (fo_cb_nohold max 86.6 N). The lit-side "
          "statistics of rev3 (lit_* and gap_N / T_mid_N) are WITHDRAWN (W2, lead 194 (2)). NEW rev4 lit-side bracket "
          f"(SIM, sim6 v2.13-dev, A1_none pw, 285 m trim, N={r2['N']}, start plateau 2.4 bar abs for st_T s, T 37.16 N): "
          f"window 0.5 s releases every lit run up to st_T {w5['starve_threshold_s']['all']} s; at 0.40 s "
          f"{w5['by_st_T']['0.4']['aborted']}/60 lit vehicles are aborted, at 0.45 s {w5['by_st_T']['0.45']['aborted']}/60; "
          f"window 0.8 s releases every lit run up to {w8['starve_threshold_s']['all']} s (W10 < 6: "
          f"{w8['starve_threshold_s']['W10lt6']} s), 1/60 aborted at 0.65 s, 6/60 at 0.70 s. Release comes 0.08-0.12 s after "
          "the plateau ends. So the 0.5 s window does not cover the top of Combustion's 0.1-0.4 s fuel-starved range (margin "
          "about 0 to -0.1 s, not Electronics' +60-80 ms from its stand-in) and the 0.8 s window covers it with >= 0.20 s. "
          "Trade (for the lead): 0.8 s releases 4/2072 dead vehicles at all winds but 0/1502 inside W10 < 6 m/s (the hard "
          "launch-commit rule); 0.5 s aborts about 8 % of 0.4 s-plateau lit vehicles. A pcf_tmax change is a lead decision "
          "and waits for Electronics' S17 sweep against GNC's R2 v2 (line 216 (1)) and for Combustion v2.4b."),
         "CORRECTED, for REV-GNC-5 delta re-check; lit-side bracket NEW",
         E(f"{O}/r2_starve/r2_starve.json", REV3R, f"{O}/wmark/WITHDRAWN_INDEX.json"),
         "SIM (flights) / DERIVED (thresholds) / ASSUMED (plateau level and length: Combustion bracket)")
    # [7]
    item(7, "Publishable as written; RV5-10 as a NOTE", ["RV5-10 note attached"],
         (rev3[7]["proposal"] + ". NOTE (RV5-10): with the frame-level RMS equal to the white model's (_fr variants) B1 comp "
          "passes at all three correlation times and A1 comp passes at 5 ms by 0.0016 pp; the B1 |b_sys median| comes from "
          "fct2_B1_H_cal(_comp).json, not in the hub (TO-VERIFY, <= 0.044 pp). Flown at the 300 m comparator configuration, "
          "so the apex figures are conservative for 210 m (RV5-13)."),
         "AS WRITTEN + NOTE", E(REV3R), "SIM / DERIVED")
    # [8]
    item(8, "Publishable as written", [], rev3[8]["proposal"], "AS WRITTEN", E(REV3R), "RESEARCH PROPOSAL (not flown)")
    # [9]
    item(9, "Publishable with corrections: RV5-07",
         ["ECU cap <= 2.55 s per line 203 (3) and 216 (5)", "~80 g sensitivity flown at 210 m"],
         ("Text correction of /flight_software/relight_sequence_placeholder/v/purge_bound: 2.5 s is the scheduled purge flow; "
          "the ECU both-open cap is <= 2.55 s (lead 203 (3); 75.9 g on the Combustion basis, <= 76 g allowance); the v2.10 "
          "firmware cap of 2.61 s is SUPERSEDED. REV-ELEC-2 R2-05 (line 216 (5)) found the 75.9 g basis ambiguous (at 29.8 "
          "g/s the 2.55 s cap gives 77.5 g; the 2.5 s schedule meets 76 g only for mdot <= 30.4 g/s; the hardware one-shot "
          "bound is 3.293 s of flow, 96.2-103.5 g): the purge limit is restated by the lead there, GNC carries about 80 g as "
          "a sensitivity. Flown at the A1 trim (SIM, N=500/base, G80 = 80 g booked): liq|G80|v351|h210 UB95 0.97 pp and "
          "pw 0.62 pp against the v3d reference (line-208 rule PASS), and against G73 at the same band liq -1/+0, pw "
          "identical. The ~80 g case is not flown at 285 m (COMPARATOR), and the 96-104 g hardware bound is not flown at 210 m "
          "(nearest: rev2 PS10 81-107 g at 300 m)."),
         "CORRECTED, for REV-GNC-5 delta re-check", E(f"{O}/p2/p2_rev4.json"), "SIM / DERIVED")
    # [10]
    item(10, "Publishable as written", [], rev3[10]["proposal"], "AS WRITTEN", E(REV3R), "SIM model item (open)")
    res_out = OrderedDict(version=VERSION, date="2026-10-19", generated_utc=time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
                          status="AUTHOR PROPOSALS for gnc.json v3.2; NOT PUBLISHED; REV-GNC-5 delta re-check first (lead 208 (6))",
                          sources=dict(rev3_results=dict(path=REV3R, sha256_16=sha16(REV3R)),
                                       review=dict(path=REVIEW, sha256_16=sha16(REVIEW)),
                                       rev4_results=dict(path=f"{O}/rev4_results.json", sha256_16=sha16(f"{O}/rev4_results.json"))),
                          a1_configuration="A1 trim 210 m (line 213/214) on massprops v3.5.1; 285 m figures are COMPARATORS",
                          items=items)
    extra = f"{O}/v32/v32_new_items_rev4.json"
    if os.path.exists(extra):
        res_out["items"] += json.load(open(extra))["items"]
        res_out["sources"]["new_items"] = dict(path=extra, sha256_16=sha16(extra))
    p = f"{O}/v32/v32_proposals_rev4.json"
    json.dump(res_out, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p), len(res_out["items"]), "items")


if __name__ == "__main__":
    main()
