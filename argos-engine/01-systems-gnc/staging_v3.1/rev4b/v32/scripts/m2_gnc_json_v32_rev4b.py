"""m2_gnc_json_v32_rev4b v1.0 (GNC rev4b, 2026-10-19): the gnc.json v3.2 candidate, built from the published gnc.json v3.1
(interfaces/gnc.json 4f3209323b0e0ed4) as a DOCUMENT CHANGE with no new flight and no new GNC-computed number.

It folds (lead CHANGELOG line 227 (10)):
  - the GNC rev3 / rev4 v3.2 proposals [0]-[15] as staged in staging_v3.1/rev4 (out_rev4/v32/v32_proposals_rev4.json
    6fd6d66e08aef5d8, MANIFEST_rev4 083675a6abddaabe), with the exact correction texts RV6-01 to RV6-14 of the independent
    delta re-check REV-GNC-6 (reviews/REVIEW-GNC-R4.md d83c93504accd30a, section (e));
  - the lead decisions of CHANGELOG lines 204, 208, 213, 214, 219, 222 and 227 (2)-(9) (verbatim + fold map).
Every replaced value keeps its old text under a sibling key ending in '_superseded_rev4b' (or an inline '[SUPERSEDED
rev4b: ...]' marker, or a 'SUPERSEDED (rev4b; ...)' list prefix); the rev4 proposal texts that RV6 corrects are not carried
into the candidate: their old / new substrings are logged in v32_corrections_log_rev4b.json beside it.  Numbers quoted here
come from the staged GNC files, the reviewer's files or the lead lines, each with its source; the few arithmetic restatements
(1.5 x landing weight) are tagged DERIVED.
Every exact RV6 text used is asserted to occur verbatim in the pinned review file, and every quoted lead sentence in the
pinned CHANGELOG line; every replaced substring is asserted to occur exactly once.
Outputs (deterministic; run twice -> identical bytes): <OUTD>/gnc_v3.2_rev4b.json, gnc_v3.2_rev4b_keydiff.json (paths vs
v3.1), gnc_v3.2_rev4b_vs_v3.1.diff (unified text diff), v32_corrections_log_rev4b.json.
GNC does not write interfaces/gnc.json: the REV-GNC reviewer does a document diff and the lead publishes."""
import copy
import difflib
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

sys.dont_write_bytecode = True
VERSION = "m2_gnc_json_v32_rev4b v1.0"
SP = "/home/claude/work/space"
HUB = "/home/claude/work/shared-fallback/engine"
V31 = f"{HUB}/interfaces/gnc.json"
V31_SHA16 = "4f3209323b0e0ed4"
R4 = "01-systems-gnc/staging_v3.1/rev4"
STAGE = "01-systems-gnc/staging_v3.1/rev4b"
OUTD = os.environ.get("GNC_V32_OUT", f"{SP}/out/rev4b/v32")
OUT = f"{OUTD}/gnc_v3.2_rev4b.json"
KEYDIFF = f"{OUTD}/gnc_v3.2_rev4b_keydiff.json"
TXTDIFF = f"{OUTD}/gnc_v3.2_rev4b_vs_v3.1.diff"
CORRLOG = f"{OUTD}/v32_corrections_log_rev4b.json"
CHLOG = f"{HUB}/interfaces/CHANGELOG.md"
CHLOG_N = 228
CHLOG_SHA16 = "4ab6945a31b8cc01"          # sha256/16 of lines 1-228 (the file as read for this build)
LEAD_LINES = (204, 208, 213, 214, 219, 222, 227)
SRC = OrderedDict([  # cited files: path relative to the hub, pinned sha256/16
    ("gnc_json_v3.1", ("interfaces/gnc.json", V31_SHA16)),
    ("review_rev_gnc_6", ("reviews/REVIEW-GNC-R4.md", "d83c93504accd30a")),
    ("review_rev_gnc_6_manifest", ("reviews/gnc/rev4/MANIFEST_REV-GNC-6.sha256", "0102191ef982cb8b")),
    ("rv6_v02_dcrit_duty", ("reviews/gnc/rev4/results/v02_dcrit_duty.json", "0de7dcb9c2ecc03f")),
    ("rv6_v04_items", ("reviews/gnc/rev4/results/v04_items.json", "daa13dcfd36bd5d9")),
    ("rv6_v05_eng11_env", ("reviews/gnc/rev4/results/v05_eng11_env.json", "f0432df3c70dad6e")),
    ("rv6_v07_extra", ("reviews/gnc/rev4/results/v07_extra.json", "58ff60a78416f8fd")),
    ("rv6_v09_fe_plant", ("reviews/gnc/rev4/results/v09_fe_plant.json", "a513b164c16d37d1")),
    ("review_rev_gnc_5", ("reviews/REVIEW-GNC-R3.md", "f2aafa51c7117ba8")),
    ("rev4_manifest", (f"{R4}/MANIFEST_rev4.sha256", "083675a6abddaabe")),
    ("rev4_proposals", (f"{R4}/out_rev4/v32/v32_proposals_rev4.json", "6fd6d66e08aef5d8")),
    ("rev4_new_items", (f"{R4}/out_rev4/v32/v32_new_items_rev4.json", "76b1944af3bc9a95")),
    ("rev4_results", (f"{R4}/out_rev4/rev4_results.json", "31eb2290c2e8c74b")),
    ("rev4_withdrawn_index", (f"{R4}/withdrawn_markers/WITHDRAWN_INDEX.json", "9a652a75813fada2")),
    ("rev3_manifest", ("01-systems-gnc/staging_v3.1/rev3/MANIFEST_rev3.sha256", "79c2c8cd5d10e3c4")),
    ("rev3_results", ("01-systems-gnc/staging_v3.1/rev3/results/rev3_results.json", "e0f6e7611fe523b5")),
    ("p2_rev4", (f"{R4}/out_rev4/p2/p2_rev4.json", "68cf1f643effd5b9")),
    ("landing_mass_h210", (f"{R4}/out_rev4/p2/landing_mass_coverage_h210.json", "d40472c8d92eaac9")),
    ("eng11_final", (f"{R4}/out_rev4/eng11/lin_v351/eng11_final.json", "47190558a3ae45e3")),
    ("re24", (f"{R4}/out_rev4/re24/v351_h210/re24.json", "b2e784adbfe205be")),
    ("r2_starve", (f"{R4}/out_rev4/r2_starve/r2_starve.json", "d743193bd5bdf88b")),
    ("payload_n500", (f"{R4}/out_rev4/payload_n500/payload_rev4.json", "6d62104dac3f4fcd")),
    ("fea3d_report", ("04-fea/assembly3d/REPORT-FEA3D.md", "ff24718e9db201e5")),
    ("fea3d_modal", ("04-fea/assembly3d/results/modal_summary_v351.json", "242b38ffab643434")),
    ("massprops_v351", ("03-cad/v3.5.1/massprops_v3.5.1.json", "488b47f9d55ff91b")),
])
# evidence paths of the rev4 proposals (author work area) -> staged hub copies (checked by sha256/16 at build time)
EVMAP = ((f"{SP}/out/rev4/wmark/", f"{R4}/withdrawn_markers/"), (f"{SP}/out/rev4/", f"{R4}/out_rev4/"),
         (f"{SP}/gnc_dev7/", f"{R4}/sim/gnc_dev7_sim6_v2.13-dev/"), (f"{HUB}/", ""))

# ------------------------------------------------------------------------------------------------ exact RV6 texts
# (each asserted verbatim in the pinned review; quoted strings of REVIEW-GNC-R4.md section (e))
RV6_01_MAIN = (
    "FINAL REQUIREMENT PROPOSED (DERIVED, linear, on the V5c structure (CAD v3.3), at the ASSUMED J 1.6e-3 kg m2 (servo "
    "output shaft, reflected by g = n^2 at the centre and added to the engine inertia), cons kinematics and first bending "
    "24.3 Hz full / 25.64 Hz landing): (1) design-to window for the servo output stiffness 100 <= K_s <= 130 N m/rad "
    "(two-sided; the only contiguous window that passes ENG-07d on every floor20 corner on the continuous pose envelope "
    "between the 9 V5c poses; margins 0.03-0.28 dB above 6 dB; conditional on the plant, see the RV6-14 sentence); (2) "
    "acceptance: ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, continuous pose envelope, notch as flown) re-run "
    "on the B-TVC-1 measured K_s (with its measurement uncertainty), J and reflected-inertia convention and rocking modes at "
    "the poses, and on the measured or airframe-FE first bending mode (full and landing); K_s is frozen only on a PASS; on a "
    "FAIL the notch set (second notch on the measured bending mode) is changed and the margins re-run before any K_s change. "
    "The 9-pose passes at 190 and 220-230 N m/rad are WITHDRAWN (pose sampling); 250-270 N m/rad pass on both axes but are "
    "not a design-to value.")
RV6_01_I_OLD = "No K_s in 58-174 N m/rad is robust to a -10 % bending error with one fixed notch"
RV6_01_I_NEW = (
    "No K_s in 58-174 N m/rad is robust to a -10 % bending error with one fixed notch; with that notch the 100-130 window "
    "passes only for a full-tank first bending >= 24.3 Hz among the values tested (10, 12, 15, 18, 20 and 22 Hz each fail on "
    "at least one axis; 24.3, 27 and 30 Hz pass; REV-GNC-6 v05 part C, DERIVED)")
RV6_01_II_OLD = ("The grid gives no simple separation rule (beta passes at 220-270 with its pose range spanning the bending "
                 "frequency)")
RV6_01_II_NEW = (
    "The grid gives no simple separation rule: on the continuous pose envelope beta fails at 190 and 220-230 and passes at "
    "250-270 with its pose range spanning the bending frequency; every failing corner at the nominal bending has its "
    "full-tank rocking frequency at 24.14-24.71 Hz")
RV6_01_III = (
    "NOT CONSISTENT with ENG-07d at K_s 100-130 with the single fixed ECU notch (DERIVED, REV-GNC-6 v05 part C). Set the "
    "airframe minimum from the measured bending mode and the ENG-07d re-run, or adopt the second notch.")
RV6_02 = (
    "landing_mass_window_kg: lower bounds unchanged (DERIVED hover rule: floor 12.5 % 7.08, 20 % 11.33, 25 % 14.16 kg). Upper "
    "bound: REQ reference for the lead to restate; GNC evidence: nominal touchdown 16.11 kg (DERIVED, A1_none liq, tank at "
    "0.58 m, 210 m) / 16.15 kg (lead's v3.5.1 estimate) is covered by the line-208 210 m decision MC (SIM, N=1000 per main "
    "base). Record, kept as engine data / open item for the airframe work (CHANGELOG 222: ICD-AIRFRAME v2.1 is out of the "
    "finish scope; SIM, not a controller-qualified window): dispersed touchdown mass in that MC 14.18-18.13 kg (p01 14.50, "
    "p50 16.03, p99 17.47 kg); P(80 g) falls with touchdown mass inside it (pooled liq 0.976 at >= 16.15 kg vs 0.989 below, "
    "Fisher p 0.049). Paired record (SIM, liq, N=500/base, payload arms): nominal 17.25 kg with the propellant restored "
    "PASSES against the 0 kg vehicle (-8/+8, UB95 0.66 pp); 18.49 / 18.64 kg LOSE (p 0.035 / 7.2e-4). A planning touchdown "
    "mass above 16.15 kg needs its own paired arm.")
RV6_03 = (
    "At the A1 trim 210 m the line 204 (1) / 208 (4) premises hold only at 285 m: nominal commit leads go down to 2.264 s "
    "(A1_none) and 1.946 s (A1J_pc, A1_pc), 16 of 1000 runs per main base commit with zero slack, D_crit(2.1 s) is 0.164 / "
    "-0.154 s (p01 0.576 / 0.674 s). The A1 = 210 m P (line-208 PASS, UB95 0.802 pp) holds for zero effective gate delay; by "
    "a reviewer estimate (ASSUMED transfer of the 285 m P-by-lead curve) it holds to about 0.5 s and is consumed near 0.75 s. "
    "CONDITION: a gate-delay injection arm at 210 m (D = 0.25 / 0.5 / 0.75 / 1.0 s, both states, N=1000 per main base, "
    "line-208 statistics) is flown, and the drogue deploy-to-inflation delay is bounded (TO-VERIFY, canopy data), before the "
    "210 m relight P is used for flight acceptance.")
RV6_04_OLD = "the 285 m tolerance (3.765 s for 2.1 s; +0.156 s on pc bases)"
RV6_04_NEW = "the 285 m tolerance at N=1000 (3.765 s A1_none / 3.633 s A1J_pc for 2.1 s; 3.921 s on A1_pc, N=500)"
RV6_04_ADD = ("the A1J_pc run 191 (nominal lead 1.946 s) is not a landing under 204 (1); with that rule on every nominal run "
              "the band is unchanged (liq 210 m -26/+20, UB95 0.858 pp)")
RV6_05_NEW = (
    "liq|G73 burn_time p99 at N=1000: A1_none 8.443 s at 210 m vs 8.446 s at 285 m; A1J_pc 8.270 vs 8.227 s (pw 8.339 / "
    "8.337 and 8.165 / 8.111 s). Line 213's 'the A1 duty cycle shortens' is not supported: equal within 0.003 s on A1_none, "
    "+0.043 s on A1J_pc.")
RV6_06_NEW = (
    "a landing-burn jam that the monitor does not trip on before touchdown lost no landing in this set: 31 runs per base and "
    "servo, all jams in the last 0.25-1.19 s before the twin's touchdown (onset u >= 0.742 of the landing burn; every earlier "
    "jam was detected), 0 lost / 0 gained against the no-jam twin (one-sided 95 % UB 9.2 % per arm; 60 distinct runs over "
    "the four arms)")
RV6_07_NEW = (
    "5 N rms frame noise (iid ASSUMED) raises the window maximum of the 3-frame minimum by +3.1 N median / +7.8 N p99 over 50 "
    "frames (0.5 s) and +3.8 / +8.2 N over 80 frames (0.8 s). Against the R2 v2 mode-3 margins at W10 < 6 (+5.98 N at 0.5 "
    "s, +5.30 N at 0.8 s) the bounding run would be released with probability 6.5 % / 18.4 %; against the v3.1 R2 margin "
    "(16.31 N = 37.16 - 20.85 N) the probability is about 0.")
RV6_08_ADD = (
    "(SIM, N=60, A1_none pw, 285 m v3d trim; transfer to 210 m / v3.5.1 ASSUMED; 0/60 aborts gives a one-sided 95 % UB of "
    "4.9 %). With the 0.8 s window every lit run is released up to 0.60 s, but landings fall with the plateau (all winds "
    "58/60 at 0.40 s, 55 at 0.45-0.50 s, 50/60 at 0.60 s; W10 < 6 44/44 to 0.55 s, 43/44 at 0.60 s); with 0.5 s at 0.40 s 53 "
    "of 55 released land. The window choice decides release; the starve itself costs landings.")
RV6_09_I = ("touchdown angular rate > 10 deg/s (18/18, 19/19 failures; tilt > 5 deg 4/4, lateral > 0.5 m/s 4/6), no "
            "exhaustion")
RV6_09_II = ("line-208 rule with the sweep floor at 180 m (below it the relight timeline governs; the 0 kg and +0.5 kg 170 m "
             "screens fail, so the rule without a floor gives no band)")
RV6_09_III = ("A1 engine-on p99 8.92 s (A1_none) / 8.71 s (A1J_pc), max 9.24 s, vs 8.37 / 8.20 s at 2.00 kg and the 8.258 s "
              "A1 sizing counter: B1/thermal and erosion check TO-VERIFY before the option is quoted on the datasheet")
RV6_09_IV = "2.20 kg +1 kg vs the 0 kg vehicle (pl0 h210): -8/+8, UB95 0.66 pp"
RV6_09_V = (
    "P 0 when flown at 115 / 90 m, next to their DERIVED equal-margin apogees 117.0 / 91.4 m; the equal-margin apogee is not "
    "a band below the ~180 m relight-timeline floor (at 155 m P(80 g) is 0.55-0.57 with +1 kg (N=500 per base) and 0.71-0.77 "
    "with 0 kg (N=250 per base))")
RV6_10_PATHS = (
    "/P4_R2v2/command_hold_trace/lit_k100_hold/* (9 leaf patterns: n_runs, hold_s[], hold_records_at_62p5N[], "
    "ECU_command_values_N[], F_cold_max_N[], valve_lift_max_mm[], R2_estimate_max_N[] 52.39-60.30 N, F_truth_max_N[] "
    "59.5-65.3 N) and /bitchecks/v2.10_vs_v2.9/functional/checks/hold_trace_lit_k875")
RV6_11 = ("runs 0-499 alone give 210 m and runs 500-999 205 m; paired bootstrap 205 / 210 / 215 m in 28 / 29 / 32 % of "
          "resamples; 215 m fails the bound by 0.026 pp")
RV6_12 = ("0/1000 (UB95 0.30 %); nominal metric max 0.18-0.19 deg vs 1.5 deg with the flexible mount and encoder "
          "quantisation modelled; encoder noise, vibration and supply sag not modelled.")
RV6_13 = "204 (1) counting rule at 210 m: band unchanged"
RV6_14 = (
    "The window is computed on the V5c structure (CAD v3.3). The 3D FE of CAD v3.5.1 (CHANGELOG 221; SIM, coarsened-model "
    "modes, production-model K) agrees with the ENG-11 plant on the engine inertia (0.0585 / 0.0590 vs I_piv 0.0588-0.0594 "
    "kg m2) and on the kinematic factor (23.04). It leaves the servo rotor out: J 1.6e-3 kg m2 is servo-side, 0.0369 kg m2 at "
    "the pivot, added to the engine inertia, so the loop's rocking frequency is 0.786 x the FE's 21-33 Hz. The FE structure is "
    "stiffer: neutral K 7284 / 5370 against V5c centre 6539 / 4325 N m/rad. On that structure, at nominal J, the full-tank "
    "rocking range reaches the coincidence band (24.1-24.7 Hz at the nominal bending) at K_s about 126 (alpha) / 129 (beta) N "
    "m/rad (DERIVED frequency map; uniform pose scaling ASSUMED). At J 0.76e-3 the whole window is exposed. GNC re-verifies "
    "the window before it is quoted as design-to.")
RV6_TEXTS = OrderedDict([("RV6-01", RV6_01_MAIN), ("RV6-01 (i) old", RV6_01_I_OLD), ("RV6-01 (i)", RV6_01_I_NEW),
                         ("RV6-01 (ii) old", RV6_01_II_OLD), ("RV6-01 (ii)", RV6_01_II_NEW), ("RV6-01 (iii)", RV6_01_III),
                         ("RV6-02", RV6_02), ("RV6-03", RV6_03), ("RV6-04 old", RV6_04_OLD), ("RV6-04", RV6_04_NEW),
                         ("RV6-04 add", RV6_04_ADD), ("RV6-05", RV6_05_NEW), ("RV6-06", RV6_06_NEW), ("RV6-07", RV6_07_NEW),
                         ("RV6-08", RV6_08_ADD), ("RV6-09 (i)", RV6_09_I), ("RV6-09 (ii)", RV6_09_II),
                         ("RV6-09 (iii)", RV6_09_III), ("RV6-09 (iv)", RV6_09_IV), ("RV6-09 (v)", RV6_09_V),
                         ("RV6-10", RV6_10_PATHS), ("RV6-11", RV6_11), ("RV6-12", RV6_12), ("RV6-13", RV6_13),
                         ("RV6-14", RV6_14)])

# ------------------------------------------------------------------------------------------------ quoted lead sentences
# (each asserted verbatim in CHANGELOG line 227 / 219 / 222)
L227_2 = (
    "J (1.6e-3 kg m2, range 0.76-2.7e-3) is the servo rotor and gear-train inertia at the servo output shaft (SB-2292SG "
    "DATASHEET-derived, ASSUMED) and is ADDED to the engine inertia I_piv; the FE engine inertia 0.0585 / 0.0590 kg m2 matches "
    "I_piv 0.0588-0.0594 within 1.6 %, and the FE does not inform J. The convention is VERIFIED (code and source data); the "
    "value of J stays TO-VERIFY at B-TVC-1.")
L227_3 = (
    "Design-to window 100 <= K_s <= 130 N m/rad (two-sided) on the V5c plant (CAD v3.3) at the ASSUMED J, cons kinematics and "
    "bending 24.3 / 25.64 Hz. Acceptance is the ENG-07d re-run on the B-TVC-1 measured K_s, J, convention and rocking modes "
    "and on the measured or airframe-FE bending mode, and K_s is frozen only on a PASS. The 9-pose passes at 190 and 220-230 "
    "are WITHDRAWN. On the 3D FE structure (stiffer: neutral 7284 / 5370 against V5c 6539 / 4325 N m/rad) the top of the "
    "window falls to about 126 (alpha) / 129 (beta) N m/rad (DERIVED frequency map, uniform pose scaling ASSUMED). GNC "
    "re-verifies the window on the FE plant (RV6-14 re-run (a)-(e)) before the datasheet quotes it as design-to; until then "
    "the datasheet quotes it with its plant basis. gnc.json airframe_first_bending_min_Hz 10 Hz (goal 15) is recorded NOT "
    "CONSISTENT with ENG-07d at this window with one fixed notch: 10-22 Hz fail on at least one axis, 24.3-30 Hz pass "
    "(DERIVED). This is an open item for the airframe work (line 222); the engine-side remedy (second notch on the measured "
    "bending mode) stays a GNC study.")
L227_4 = (
    "The lead restates the upper bound: nominal planning touchdown mass <= 16.15 kg (the v3.5.1 estimate, covered by the 210 "
    "m decision Monte Carlo, N=1000 per main base); a planning mass above 16.15 kg needs its own paired arm. The lower bounds "
    "are unchanged. The dispersed 14.18-18.13 kg is a record only, with P(80 g) 0.976 at >= 16.15 kg against 0.989 below "
    "(Fisher p 0.049).")
L227_5 = (
    "R2 starve window: 0.8 s ADOPTED for the W10 < 6 m/s launch-commit envelope. GNC shows >= 0.20 s margin over the 0.4 s "
    "top of the starve range (0.5 s has about 0 to -0.1 s), and 0/1502 dead-vehicle releases at W10 < 6; 4/2072 at all winds "
    "are outside the hard wind rule. Scope per RV6-08: SIM, N=60, A1_none pw, 285 m v3d, transfer ASSUMED, thresholds 0.30 / "
    "0.60 s (0.65 s at W10 < 6). Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the "
    "lead.")
L227_6 = (
    "Mode-3 estimator: ADOPTED as a flight-software requirement. The mode-3 filter is re-initialised at the Pc-invalid onset "
    "(GNC rev4 R2 (a), first option). Electronics implements it in v2.11 and runs S17; GNC re-runs R2 with the flush "
    "afterwards. Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin: at 5 N rms (iid "
    "ASSUMED) the bounding run releases with probability 6.5-18.4 % (RV6-07, DERIVED).")
L227_7 = (
    "RE-24, lead safety decision: the GIMBAL_FAULT abort is NOT inhibited near touchdown; a detected landing-burn jam aborts "
    "as designed. Why: continuing gains landing P 0.136-0.150 against 0.084-0.088 only inside a failure whose rate is "
    "unknown; a thrust cut gives a more predictable impact point than a lit engine held at a jammed angle; and an inhibit "
    "adds a mode to verify. Revisit if B-TVC-1 gives a jam rate. The undetected-jam result carries the RV6-06 scope (31 runs "
    "per base and servo, all late jams, 0 lost / 0 gained, one-sided UB95 9.2 % per arm); 0/1000 false aborts (UB95 0.30 %; "
    "encoder noise, vibration and supply sag not modelled).")
L227_8 = (
    "Gate delay, RV6-03 condition ADOPTED: the 210 m relight P is used for flight acceptance only after (a) a gate-delay "
    "injection arm at 210 m (D = 0.25 / 0.5 / 0.75 / 1.0 s, both states, N=1000 per main base, line-208 statistics) and (b) a "
    "bound on the drogue deploy-to-inflation delay (TO-VERIFY, canopy data). It is not needed for v3.2 publication or the "
    "datasheet; it is a GNC open item.")
L227_9 = (
    "Line 213's 'A1 duty cycle shortens' is corrected per RV6-05 (not supported: burn p99 8.443 / 8.270 s at 210 m against "
    "8.446 / 8.227 s at 285 m); B1 governs sizing. Payload record per RV6-09; the 2.20 kg option's A1 burn p99 8.92 / 8.71 s "
    "(max 9.24 s) exceeds the 8.258 s sizing counter, so its B1, thermal and erosion check is TO-VERIFY and the datasheet says "
    "so.")
L227_1 = ("A1 = 210 m (line 214) is ACCEPTED, with the RV6-03 condition in (8).")
L219 = ("Baseline unchanged: no payload, A1 210 m (line 214). The 2.20 kg tank is a characterized OPTION for the datasheet and "
        "ICD-AIRFRAME v2.1, not a baseline; no re-run is requested.")
L222 = ("ICD-AIRFRAME v2.1 is REMOVED from the finish scope and is not written now; 00-requirements/ICD-AIRFRAME.md draft 0.2 "
        "stays as it is (superseded in places, not updated).")
LEAD_QUOTES = ((227, L227_1), (227, L227_2), (227, L227_3), (227, L227_4), (227, L227_5), (227, L227_6), (227, L227_7),
               (227, L227_8), (227, L227_9), (219, L219), (222, L222))

# ------------------------------------------------------------------------------------------------ author's scan
# R-series: the REV-GNC-6 REJECTED texts (section (f)) and the decided-state reversals of this build; S-series: the
# rev2p2 builder's S01-S22 carried for continuity, except S06 (pcf_tmax 0.8 s), which lead 227 (5) reverses.
# A pattern id with a 'rev4b' marker set needs an explicit rev4b marker within the window (older markers do not count).
STALE = OrderedDict([
    ("R01", (r"K_s ?(>=|≥) ?~?100\b(?! <=)", None)),
    ("R02", (r"190-190, 220-270|190, 220-270", None)),
    ("R03", (r"(?i)widen[^.;]{0,80}(landing_mass_window|14\.18)", None)),
    ("R04", (r"(?i)UNDETECTED gimbal jam at the bound does not lose", None)),
    ("R05", (r"0\.144-0\.150", None)),
    ("R06", (r"0\.086-0\.088", None)),
    ("R07", (r"\+0\.156 s on (the )?pc bases", None)),
    ("R08", (r"\+4 N \(median\)", None)),
    ("R09", (r"(?i)37 ?% (below|lower|under)|\bJ\b[^.;]{0,80}\b37 ?%", None)),
    ("R10", (r"(?i)touchdown tilt / lateral speed", None)),
    ("R11", (r"8\.374 / 8\.510|8\.205 / 8\.277", None)),
    ("R12", (r"(?i)duty cycle shortens", None)),
    ("R13", (r"(?i)(A1 apogee target|apogee target|A1 is|A1 target) 285 m|285 m (\(h_target trim\) )?ADOPTED|h_target 300 -> 285 m", "rev4b")),
    ("R14", (r"285 m target and its P are NOT demonstrated", "rev4b")),
    ("R15", (r"pcf_tmax:? \(?0\.5 ?s\)?", "rev4b", ("/reviewer_probes/",))),
    ("R16", (r"(?i)(pcf_tmax )?0\.8 s (proposal is )?NOT adopted", "rev4b")),
    ("R17", (r"(?i)safety decision for the lead[^.;]{0,120}not proposed here", None)),
    ("R18", (r"(?i)gate: >= ~?100|K_s (>=|<) ?~100", "rev4b")),
    ("R19", (r"window to design to\.?(?! The window is computed on the V5c structure)", None)),
    ("R20", (r"(?i)pcf_tmax change is a lead decision", None)),
    ("R21", (r"(?i)Proposal: re-initialise the mode-3 filter", None)),
    ("R22", (r"(?i)every one lands exactly as its no-jam twin", None)),
    ("R23", (r"(?i)ENG-11 stiffness - GNC assesses", "rev4b")),
    ("R24", (r"(?i)planning value[^.;]{0,30}250 m(?! PROVISIONAL)", None)),
    ("R25", (r"(?i)first bending >= 10 Hz", "rev4b")),
    ("R26", (r"(?i)interim[^.;]{0,30}K_s >= 116|at K_s >= 116", "rev4b")),
    ("S01", (r"650 N[^.;]{0,60}(CONFIRMED|confirmed)|(CONFIRMED|confirmed)[^.;]{0,30}650 N", None)),
    ("S02", (r"(<=|≤) ?1 ?% \(1 sigma\)", None)),
    ("S03", (r"300 m baseline|A1 300 m|apogee \(300 m\)|A1 at 300 m", None)),
    ("S04", (r"costs no measurable P|delay <= 0\.6 s costs", None)),
    ("S05", (r"error budget: OPEN", None)),
    ("S07", (r"0xFFFF AND t >= t_E2", None)),
    ("S08", (r"per-flight form[^.;]{0,60}provisional support", None)),
    ("S09", (r"\bfreeze[^.;]{0,40}(k_hat|apex)|(k_hat|apex)[^.;]{0,40}\bfreeze", None)),
    ("S10", (r"0\.30 kg[^.;]{0,40}trigger|trigger[^.;]{0,40}0\.30 kg", None)),
    ("S11", (r"(?i)interim[^.;]{0,20}1\.7 ?s|L\* ?= ?1\.7", None)),
    ("S12", (r"(?i)(?<!no )(?<!alternative: )(relight (proceeds )?unpurged|proceeds unpurged|unpurged relight)"
             r"(?![^.;]{0,80}(E2 ?\+ ?0\.22|held to))", None)),
    ("S13", (r"(?i)P_total ~?0\.75", None)),
    ("S14", (r"RELEASE iff b4 AND \[\(d2-d3 != 0xFFFF", None)),
    ("S15", (r"(?i)0\.81 s plan holds(?![^.;]{0,80}predictor path)", None)),
    ("S16", (r"pivot at 0\.2223 m", None)),
    ("S17", (r"(?i)cold-flow apparent thrust unbounded|0 / 5 / 10 N parametric", None)),
    ("S18", (r"(?i)(H20|OI-31|no relight on that pass)[^\n]{0,200}?(not decided by the lead|pending a lead decision)", None)),
    ("S19", (r"(?i)plain trigger fired \(2000 runs", None)),
    ("S20", (r"(?i)(W10|m/s)[^\n]{0,80}s04_wind\.out", None)),
    ("S21", (r"(?i)margin 0\.012 ?%", None)),
    ("S22", (r"NOT PUBLISHED|Por revisar|nothing yet \(staging\)", None)),
])
MARKERS = ("SUPERSEDED", "WITHDRAWN", "NOT ADOPTED", "NOT adopted", "REFUTED", "REPLACED", "REJECTED", "HISTORY",
           "superseded", "refuted", "replaced", "replaces", "no longer", "ANSWERED", "withdrawn", "Withdrawn", "not supported",
           "corrected", "CORRECTED")
EXEMPT_PREFIX = ("rev2p1_document_self_check", "rev2p2_document_self_check", "rev4b_document_self_check", "changes_rev2",
                 "changes_from_v")


def sha(p, n=16):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]


def shas(s, n=16):
    return hashlib.sha256(s.encode()).hexdigest()[:n]


def jload(p):
    return json.load(open(p), object_pairs_hook=OrderedDict)


def hubp(p):
    return p if p.startswith("/") else f"{HUB}/{p}"


def src(k):
    return f"{SRC[k][0]} ({SRC[k][1]})"


def changelog_lines():
    raw = open(CHLOG, "rb").read()
    lines = raw.split(b"\n")
    pre = b"\n".join(lines[:CHLOG_N]) + b"\n"
    if hashlib.sha256(pre).hexdigest()[:16] != CHLOG_SHA16:
        raise RuntimeError(f"CHANGELOG lines 1-{CHLOG_N} changed (sha256/16 {hashlib.sha256(pre).hexdigest()[:16]})")
    L = [x.decode("utf-8") for x in lines[:CHLOG_N]]
    out = OrderedDict((n, L[n - 1]) for n in LEAD_LINES)
    for n in LEAD_LINES:
        if " | lead | (" not in out[n] or ("(decision" not in out[n] and "(founder decision)" not in out[n]):
            raise RuntimeError(f"CHANGELOG line {n} is not a lead decision: {out[n][:80]}")
    for n, key in ((227, "On REV-GNC-6"), (222, "ICD-AIRFRAME v2.1 is REMOVED"), (219, "N2O TANK STAYS 2.00 kg"),
                   (214, "A1 APOGEE TARGET = 210 m"), (213, "A1 APOGEE TARGET LOWERED"), (208, "On REV-GNC-5"),
                   (204, "On GNC rev3")):
        if key not in out[n]:
            raise RuntimeError(f"CHANGELOG line {n} does not carry '{key}'")
    return out, L


CORR = []  # corrections log (old / new substrings on the rev4 proposal texts)


def rep1(s, old, new, rid, item):
    if s.count(old) != 1:
        raise RuntimeError(f"[{item}] {rid}: substring must occur once (found {s.count(old)}): {old[:90]}")
    CORR.append(OrderedDict(item=item, id=rid, op="replace", old=old, new=new))
    return s.replace(old, new, 1)


def ins_after(s, anchor, text, rid, item):
    if s.count(anchor) != 1:
        raise RuntimeError(f"[{item}] {rid}: anchor must occur once (found {s.count(anchor)}): {anchor[:90]}")
    CORR.append(OrderedDict(item=item, id=rid, op="insert_after", anchor=anchor, new=text))
    return s.replace(anchor, anchor + text, 1)


def app(s, text, rid, item):
    CORR.append(OrderedDict(item=item, id=rid, op="append", new=text))
    return s + text


def inline(s, phrase, note):
    if s.count(phrase) != 1:
        raise RuntimeError(f"phrase must occur once for an inline marker: {phrase}")
    return s.replace(phrase, f"{phrase} [{note}]", 1)


def replace_kept(dct, key, new, suffix="_superseded_rev4b"):
    if key + suffix in dct:
        raise RuntimeError(f"{key}{suffix} exists already")
    if key not in dct:
        raise RuntimeError(f"{key} not in the block")
    dct[key + suffix] = copy.deepcopy(dct[key])
    dct[key] = new


def get(d, path):
    o = d
    for k in path.split("/"):
        o = o[int(k)] if isinstance(o, list) else o[k]
    return o


def evid(p):
    """rev4 evidence path -> staged hub path with its sha256/16 checked."""
    q = p
    for a, b in EVMAP:
        if p.startswith(a):
            q = b + p[len(a):]
            break
    return q


# ------------------------------------------------------------------------------------------------ items [0]-[15]
L227_9A = ("Line 213's 'A1 duty cycle shortens' is corrected per RV6-05 (not supported: burn p99 8.443 / 8.270 s at 210 m "
           "against 8.446 / 8.227 s at 285 m); B1 governs sizing.")
L227_9B = ("Payload record per RV6-09; the 2.20 kg option's A1 burn p99 8.92 / 8.71 s (max 9.24 s) exceeds the 8.258 s sizing "
           "counter, so its B1, thermal and erosion check is TO-VERIFY and the datasheet says so.")
REVIEW_STATUS = {  # REV-GNC-6 section (d) table, per item
    0: "CLOSED (RV5-06 with a residual); RV6-10 applied", 1: "CLOSED; new 210 m reading reproduces; RV6-03 (MAJOR), RV6-04 applied",
    2: "CLOSED", 3: "CLOSED; A1 = 210 m ACCEPTED; RV6-03 condition, RV6-11, RV6-13 (NOTE) applied", 4: "CLOSED",
    5: "CLOSED; figures corrected per RV6-05", 6: "CLOSED; lit bracket reproduces (re-flown); RV6-08 applied", 7: "CLOSED",
    8: "CLOSED", 9: "CLOSED", 10: "CLOSED",
    11: "coverage of 16.15 kg nominal ACCEPTED; widening REJECTED; replaced by the RV6-02 text (MAJOR)",
    12: ("grid, continuous envelope and 6-DOF reproduce; J convention VERIFIED against the FE; requirement wording REJECTED; "
         "window conditional on the plant; RV6-01 and RV6-14 texts applied (MAJOR)"),
    13: "reproduces; undetected-jam claim scoped per RV6-06; RV6-12 applied",
    14: "(a) and (c) reproduce; (b) corrected per RV6-07; RV6-08 applied", 15: "31/31 arms reproduce; RV6-09 (i)-(v) applied"}
LEAD_REF = {0: "227 (10)", 1: "204 (1), 208 (4), 227 (8)", 2: "204 (2), 208 (3)", 3: "208 (1)-(2), 213, 214, 227 (1), (8)",
            4: "204 (4), 208 (5)", 5: "204 (4) F11, 213, 227 (9)", 6: "204 (4) F7, 208 (5), 227 (5)", 7: "204 (4) F8, 208 (5)",
            8: "204 (4) F9", 9: "203 (3), 216 (5)", 10: "204 (4) F10", 11: "222, 227 (4)", 12: "222, 227 (2)-(3)",
            13: "214, 227 (7)", 14: "216 (1)-(2), 227 (5)-(6)", 15: "219, 222, 227 (9)"}


def build_items(prop, v02):
    items = []
    P = {it["index"]: it for it in prop["items"]}
    assert sorted(P) == list(range(16))
    for i in range(16):
        it = P[i]
        t = it["proposal_rev4"]
        ids = []
        extra = OrderedDict()
        if i == 0:
            t = app(t, (" rev4b (RV6-10): the W2 set of the rev3_results.json sidecar now also covers " + RV6_10_PATHS + " ("
                        + STAGE + "/withdrawn_markers/results/rev3_results.json.WITHDRAWN.json, which replaces the rev4 "
                        "sidecar for that file; the rev4 sidecar stays as staged). The lit_k100_hold values are lit-model "
                        "(62.5 N x pcf_k) evidence and are WITHDRAWN with W2; hold_trace_lit_k875 is a code-function check of "
                        "the hold sequencing run on the withdrawn lit model: its pass is kept as a code fact only and is "
                        "withdrawn as lit-side evidence; the flame-out traces (fo_cb_hold, fo_cb_nohold) are not withdrawn. "
                        "The v2.10 bitcheck release_hold_0p22 (the W1 E2 + 0.22 s release hold) is marked the same way in "
                        "a W1 set of that sidecar (beyond the RV6-10 list, for consistency)."),
                    "RV6-10", i)
            ids = ["RV6-10"]
        elif i == 1:
            t = rep1(t, RV6_04_OLD, RV6_04_NEW, "RV6-04", i)
            t = ins_after(t, "now reaches the uncounted band in the worst 1 % of runs.", " Counting (RV6-04): " + RV6_04_ADD + ".",
                          "RV6-04", i)
            t = app(t, " " + RV6_03 + " LEAD (227 (8)): " + L227_8, "RV6-03 / 227 (8)", i)
            ids = ["RV6-04", "RV6-03", "227 (8)"]
            g = v02["gate"]
            comp = OrderedDict(tag=("REVIEWER DERIVED (" + src("rv6_v02_dcrit_duty") + "): D_crit minimum (s) by commit-lead "
                                    "threshold at 285 m on the v3d reference, liq|G73; N=1000 on A1_none / A1J_pc, N=500 on "
                                    "A1_pc / A1J_none"))
            for b in ("A1_none", "A1J_pc", "A1_pc", "A1J_none"):
                row = g[f"{b}|liq|G73|h285(v3d ref)"]
                comp[b] = OrderedDict((f"{th}s", row[f"Dcrit_{th}"]["min"]) for th in ("2.4", "2.1", "1.9", "1.3"))
                comp[b]["n"] = row["n"]
            extra["comparator_285m"] = comp
            old = copy.deepcopy(it["comparator_285m"])
            extra["comparator_285m_superseded_rev4b"] = OrderedDict(
                note=("CORRECTED by RV6-04: the rev4 A1J_pc row carried the A1_pc (N=500) values, offset +0.156 s; A1J_pc at "
                      "N=1000 is 3.633 s for 2.1 s"), v=old)
        elif i == 3:
            t = app(t, (" " + RV6_03 + " Band stability (RV6-11, NOTE): " + RV6_11 + ". The rule's value stands. Counting "
                        "(RV6-13, NOTE): " + RV6_13 + " (liq 210 m -26/+20, UB95 0.858 pp PASS; 215 m 1.081 pp; REV-GNC-6 "
                        "(b)). LEAD (227 (1)): " + L227_1 + " The gate-delay arm and the drogue inflation bound of (8) are a "
                        "GNC open item before flight acceptance; they are not needed for v3.2 or the datasheet."),
                    "RV6-03 / RV6-11 / RV6-13 / 227 (1)", i)
            ids = ["RV6-03", "RV6-11", "RV6-13", "227 (1)"]
        elif i == 5:
            old5 = ("DERIVED reading at the A1 trim from the P2 tables (table column burn_time = the sim6 engine-on counter, "
                    "checked equal on the 285 m tables: p99 8.371 / 8.185 s): liq|G73|v351|h210 p99 8.374 / 8.510 s on A1_none "
                    "(runs 0-499 / 500-999), 8.205 / 8.277 s on A1J_pc, against 8.371 / 8.185 s at 285 m on the v3d ledger and "
                    "the published A1 sizing counter 8.258 s. Line 213's consequence 'the A1 duty cycle shortens' is NOT "
                    "supported on v3.5.1: the lower apogee shortens the ascent burn but the 1.37 kg heavier vehicle lengthens "
                    "the landing burn, and the A1_none p99 stays above the A1 sizing counter as at 285 m and 300 m.")
            new5 = ("DERIVED reading at the A1 trim from the P2 tables (table column burn_time = the sim6 engine-on counter), "
                    "corrected per RV6-05 (the rev4 figures mixed N): " + RV6_05_NEW + " Every A1_none value exceeds the 8.258 "
                    "s A1 sizing counter, as at 285 m (REV-GNC-6 (c)).")
            t = rep1(t, old5, new5, "RV6-05", i)
            t = app(t, " LEAD (227 (9)): " + L227_9A, "227 (9)", i)
            ids = ["RV6-05", "227 (9)"]
        elif i == 6:
            t = ins_after(t, "and the 0.8 s window covers it with >= 0.20 s.", " " + RV6_08_ADD, "RV6-08", i)
            t = rep1(t, ("A pcf_tmax change is a lead decision and waits for Electronics' S17 sweep against GNC's R2 v2 (line "
                         "216 (1)) and for Combustion v2.4b."),
                     ("LEAD DECISION (227 (5)): " + L227_5 + " The lit side stays this bracket on the sim's own thrust model "
                      "until Combustion v2.4b publishes its start history (W2 replacement, rev4 withdrawn markers)."),
                     "227 (5)", i)
            ids = ["RV6-08", "227 (5)"]
        elif i == 11:
            new11 = (RV6_02 + " LEAD (227 (4)): " + L227_4 + " Scope (line 222): " + L222 + " The record is kept as engine "
                     "data and an open item for when the airframe is tackled (icd_inputs_for_airframe.landing_mass_window_kg).")
            CORR.append(OrderedDict(item=i, id="RV6-02 / 227 (4)", op="replace_whole_text", old=t, new=new11))
            t = new11
            ids = ["RV6-02", "227 (4)", "222"]
        elif i == 12:
            old12 = ("FINAL REQUIREMENT PROPOSED: (1) servo output stiffness K_s >= 100 N m/rad, measured at B-TVC-1 together "
                     "with J and the reflected-inertia convention (replaces the interim 'K_s >= 116'); (2) the vehicle first "
                     "bending mode (full and landing) is MEASURED or computed from the airframe (TO-VERIFY: airframe owner / "
                     "Mechanical; the PETG tube value is a placeholder), and the TVC margins are re-run on it before K_s is "
                     "frozen.")
            t = rep1(t, old12, (RV6_01_MAIN + " ADOPTED as the v3.2 text by the lead (227 (3)); it replaces the one-sided "
                                "proposal of line 218 (REJECTED, REV-GNC-6 (f))."), "RV6-01", i)
            t = rep1(t, RV6_01_I_OLD + ".", RV6_01_I_NEW + ".", "RV6-01 (i)", i)
            t = rep1(t, RV6_01_II_OLD, RV6_01_II_NEW, "RV6-01 (ii)", i)
            t = rep1(t, "both axes pass together at 100-130, 190-190, 220-270 N m/rad and fail at 140-180 and 200-210.",
                     ("both axes pass together at 100-130, 190-190, 220-270 N m/rad [the 190 and 220-230 passes are WITHDRAWN "
                      "as pose-sampling artifacts: they fail on the continuous pose envelope (RV6-01); 250-270 pass but are "
                      "not a design-to value] and fail at 140-180 and 200-210."), "RV6-01", i)
            t = ins_after(t, "At the ASSUMED bending mode, K_s 100-130 N m/rad is the window to design to.", " " + RV6_14,
                          "RV6-14", i)
            t = app(t, (" J convention (lead 227 (2); REV-GNC-6 [12] FE plant check (1)): " + L227_2 + " LEAD (227 (3)): "
                        + L227_3 + " The RV6-14 re-run (a)-(e) is staged apart for the reviewer's delta check (" + STAGE +
                        "/eng11_fe/) and is not folded into this text."), "227 (2)-(3)", i)
            ids = ["RV6-01", "RV6-01 (i)", "RV6-01 (ii)", "RV6-14", "227 (2)", "227 (3)"]
        elif i == 13:
            t = rep1(t, ("an UNDETECTED gimbal jam at the bound does not lose a landing: 31 undetected landing-burn jam runs per "
                         "base per servo, every one lands exactly as its no-jam twin (A1_none servo A 30/31 vs ref 30, servo B "
                         "29/31 vs 29; A1J_pc 31/31 vs 31, 30/31 vs 30; p = 1)."),
                     (RV6_06_NEW + " (landed with the jam / no-jam twin: A1_none servo A 30/31 / 30, servo B 29/31 / 29; "
                      "A1J_pc 31/31 / 31, 30/31 / 30)."), "RV6-06", i)
            t = rep1(t, "0.144-0.150", "0.136-0.150", "RV6-06", i)
            t = rep1(t, "0.086-0.088", "0.084-0.088", "RV6-06", i)
            t = rep1(t, ("Nominal flights: 0 false GIMBAL_FAULT aborts in 1000 (mon2), largest no-jam excursion of the monitor "
                         "metric 0.18 deg against 1.5 deg."), "Nominal flights (mon2): false GIMBAL_FAULT aborts " + RV6_12,
                     "RV6-12", i)
            t = rep1(t, ("whether to inhibit the GIMBAL_FAULT abort near touchdown is a safety decision for the lead (a jammed "
                         "engine at up to ~20 deg may leave the range safety envelope) and is not proposed here."),
                     ("whether to inhibit the GIMBAL_FAULT abort near touchdown was put to the lead as a safety decision (a "
                      "jammed engine at up to ~20 deg may leave the range safety envelope); it is DECIDED: NOT inhibited (227 "
                      "(7), below)."), "227 (7)", i)
            t = app(t, " LEAD SAFETY DECISION (227 (7)): " + L227_7, "227 (7)", i)
            ids = ["RV6-06", "RV6-12", "227 (7)"]
        elif i == 14:
            t = rep1(t, ("Proposal: re-initialise the mode-3 filter at the Pc-invalid onset (or start counting at onset + 3 "
                         "tau) and re-run the R2 v2 statistics after Electronics' S17 sweep (onsets 1-50 ms x frame phases x "
                         "noise)."),
                     ("ADOPTED as a flight-software requirement (lead 227 (6), the first option of the rev4 proposal): the "
                      "mode-3 filter is re-initialised at the Pc-invalid onset; Electronics implements it in v2.11 and runs "
                      "S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards "
                      "(the alternative, counting from onset + 3 tau, is not adopted)."), "227 (6)", i)
            t = rep1(t, "(rev2, 0.5 s).", "(R2 v1, rev2, 0.5 s; the v3.1 margin 16.31 N = 37.16 - 20.85 N).",
                     "RV6-07 (margin attribution)", i)
            t = rep1(t, ("Back-of-envelope (DERIVED, independent frames ASSUMED): 5 N rms frame noise raises the window maximum "
                         "of the 3-frame minimum by about +4 N (median) to +8 N (p99) over 50 frames, which is the whole +5.3 to "
                         "+6.0 N W10 < 6 margin, so a frame-noise budget is needed before the 'no released dead vehicle' claim "
                         "is used."),
                     ("Frame noise (DERIVED; REV-GNC-6 Monte Carlo under these assumptions, RV6-07): " + RV6_07_NEW + " LEAD "
                      "(227 (6)): Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin; the "
                      "'no released dead vehicle' claim is used only with that budget."), "RV6-07 / 227 (6)", i)
            t = ins_after(t, "0.60 s at the 0.8 s window (W10 < 6: 0.65 s).", " " + RV6_08_ADD, "RV6-08", i)
            t = app(t, (" LEAD (227 (5)): 0.8 s ADOPTED for the W10 < 6 m/s launch-commit envelope (scope RV6-08); "
                        "Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead."),
                    "227 (5)", i)
            ids = ["227 (6)", "RV6-07", "RV6-08", "227 (5)"]
        elif i == 15:
            t = rep1(t, "touchdown tilt / lateral speed with no exhaustion", RV6_09_I, "RV6-09 (i)", i)
            t = rep1(t, "Bands by the line-208 rule with the sweep floor at 180 m:", "Bands by the " + RV6_09_II + ":",
                     "RV6-09 (ii)", i)
            t = ins_after(t, "So +1 kg reaches 210 m with 2.20 kg N2O (line-208 PASS at N=500/base);", " " + RV6_09_III + ";",
                          "RV6-09 (iii)", i)
            t = ins_after(t, "+1 kg 2.20 kg: P(80 g) 0.990 / 0.984, pooled -9/+11 p 0.824 UB95 0.54 pp -> PASS (N=500/base);",
                          " paired: " + RV6_09_IV + ";", "RV6-09 (iv)", i)
            t = rep1(t, "P 0 at their equal-margin apogees 115 / 90 m", RV6_09_V, "RV6-09 (v)", i)
            t = app(t, (" FOUNDER DECISION (line 219): N2O tank stays 2.00 kg for the first flight. " + L219 + " Scope (line "
                        "222): " + L222 + " The 2.20 kg option is kept as engine data. LEAD (227 (9)): " + L227_9B),
                    "219 / 222 / 227 (9)", i)
            ids = ["RV6-09", "219", "222", "227 (9)"]
        tags = it["tags"]
        if i == 12:
            tags = "DERIVED (linear) / SIM (6-DOF) / ASSUMED (K_s, J value, bending, damping); J convention VERIFIED (227 (2))"
        elif i == 11:
            tags = "SIM (210 m decision MC) / DERIVED (hover rule, statistics); upper bound REQ (lead 227 (4))"
        row = OrderedDict(index=i, path=it["path"],
                          status_v32=("FINAL for v3.2 (" + ("as written in rev4" if not ids else "rev4 text with the "
                                      "corrections " + ", ".join(ids)) + ")"),
                          review_rev_gnc_6=REVIEW_STATUS[i], lead=LEAD_REF[i], tags=tags, text=t)
        row.update(extra)
        row["evidence"] = [OrderedDict(path=evid(e["path"]), sha256_16=e["sha256_16"]) for e in it["evidence"]]
        if i in (1, 3, 5):
            row["evidence"].append(OrderedDict(path=SRC["rv6_v02_dcrit_duty"][0], sha256_16=SRC["rv6_v02_dcrit_duty"][1]))
        if i in (12,):
            row["evidence"] += [OrderedDict(path=SRC[k][0], sha256_16=SRC[k][1]) for k in ("rv6_v05_eng11_env", "rv6_v09_fe_plant")]
        if i in (11, 13, 14, 15):
            row["evidence"] += [OrderedDict(path=SRC[k][0], sha256_16=SRC[k][1]) for k in ("rv6_v04_items", "rv6_v07_extra")]
        row["corrections_rev4b"] = ids
        items.append(row)
    return items


# ------------------------------------------------------------------------------------------------ document texts
VALID4 = ("VALIDITY (rev4b): the A1 decision figures of v32_items_rev4b (A1 210 m band, D_crit at 210 m, landing mass, "
          "RE-24, payload, ENG-11 6-DOF) are SIM / DERIVED at massprops v3.5.1 (488b47f9d55ff91b; rev4 P2, sim6 v2.9-dev and "
          "v2.13-dev); every other P, reserve, propellant-closure and apogee-trim figure carried from v3.1 was computed at "
          "GNC mass ledger v3d (13.6706 kg) and is a record, not demonstrated for the v3.5.1 vehicle; the 285 m target and "
          "its P are SUPERSEDED by the 210 m decision (lead 213 / 214, ACCEPTED in 227 (1))")
ENG11_V = ("design-to window 100 <= K_s <= 130 N m/rad (two-sided) for the servo output stiffness on the V5c plant (CAD "
           "v3.3) at the ASSUMED J 1.6e-3 kg m2 (servo output shaft, added to I_piv), cons kinematics and the ASSUMED first "
           "bending 24.3 Hz full / 25.64 Hz landing; acceptance: ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, "
           "continuous pose envelope, notch as flown) re-run on the B-TVC-1 measured K_s (with its uncertainty), J, "
           "reflected-inertia convention and rocking modes at the poses and on the measured or airframe-FE first bending mode "
           "(full and landing); K_s is frozen only on a PASS; on a FAIL the notch set (second notch on the measured bending "
           "mode) is changed and the margins re-run before any K_s change. Plant basis: on the 3D FE structure of CAD v3.5.1 "
           "the top of the window falls to about 126 (alpha) / 129 (beta) N m/rad (DERIVED frequency map, uniform pose scaling "
           "ASSUMED); GNC re-verifies the window on the FE plant before it is quoted as design-to (RV6-14 re-run, staged apart "
           "in " + STAGE + "/eng11_fe/, not folded here)")
MASS_V = ("nominal planning touchdown mass <= 16.15 kg (lead 227 (4): the v3.5.1 estimate, covered by the 210 m decision "
          "Monte Carlo, SIM N=1000 per main base); a planning mass above 16.15 kg needs its own paired arm; lower bounds "
          "unchanged; the dispersed 14.18-18.13 kg is a record only")
PCF_V = ("pcf_tmax 0.8 s for the W10 < 6 m/s launch-commit envelope (lead 227 (5); it replaces the 0.5 s of v3.1 there; "
         "scope RV6-08: SIM, N=60, A1_none pw, 285 m v3d, transfer to 210 m / v3.5.1 ASSUMED, starve thresholds 0.30 / 0.60 "
         "s (0.65 s at W10 < 6)); Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead")
REINIT_V = ("the mode-3 filter of the R2 v2 estimate is re-initialised at the Pc-invalid onset (flight-software requirement, "
            "lead 227 (6), first option of GNC rev4 R2 (a)); Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x "
            "frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards")


def status_text():
    return (
        "gnc.json v3.2 (2026-10-19): built as staging rev4b from gnc.json v3.1 (4f3209323b0e0ed4), a document change with no "
        "new flight (lead 227 (10)): it folds the GNC rev3 and rev4 results (staging_v3.1/rev3, MANIFEST_rev3 "
        "79c2c8cd5d10e3c4; staging_v3.1/rev4, MANIFEST_rev4 083675a6abddaabe) with the corrections RV6-01 to RV6-14 of the "
        "independent delta re-check REV-GNC-6 (" + src("review_rev_gnc_6") + "; PUBLISHABLE WITH CORRECTIONS, 0 BLOCKING) "
        "and the lead decisions of CHANGELOG lines 204, 208, 213, 214, 219, 222 and 227 (2)-(9); the lead publishes. WHAT "
        "THE NUMBERS ARE: SIM = flown in the GNC 6-DOF Monte Carlo; DERIVED = computed from SIM tables or interface data "
        "(linear CSI margins, band statistics, D_crit, T/W, frequency maps); ASSUMED = an input without a measurement (servo "
        "K_s, J, rocking damping, airframe bending 24.3 / 25.64 Hz, start-plateau lengths, FC frame noise, canopy timing, "
        "the bench condition of the notch); DATASHEET = maker data; TO-VERIFY = needed from a named owner. There is no "
        "hardware data: matching numbers and passing checks are not physical approval, and nothing here is physical "
        "approval. " + VALID4 + ". Decided state for GNC (v3.2): (1) A1 apogee target 210 m (lead 213 / 214; ACCEPTED, "
        "227 (1)): line-208 band liq|G73 210 m (-25/+20, p 0.551, UB95 0.802 pp; SIM N=1000 per main base; pw band 220 m); "
        "the 210 m relight P is used for flight acceptance only after a gate-delay injection arm at 210 m and a bound on "
        "the drogue deploy-to-inflation delay (227 (8), GNC open item; not needed for v3.2 or the datasheet). (2) ENG-11 "
        "(227 (3)): " + ENG11_V + ". J convention VERIFIED, J value TO-VERIFY at B-TVC-1 (227 (2)). "
        "airframe_first_bending_min_Hz 10 Hz (goal 15) is NOT CONSISTENT with ENG-07d at this window with one fixed notch "
        "(open item for the airframe work, line 222; the second notch stays a GNC study). (3) Landing mass: " + MASS_V +
        ". (4) R2 with Pc invalid: " + PCF_V + "; " + REINIT_V + "; Electronics states the FC frame-noise budget against the "
        "+5.3 to +6.0 N mode-3 margin (227 (6)). (5) RE-24 (227 (7)): the GIMBAL_FAULT abort is NOT inhibited near "
        "touchdown. (6) Line 213's 'A1 duty cycle shortens' is not supported (227 (9)); B1 governs thermal and erosion "
        "sizing. (7) Payload (219, 227 (9)): N2O tank 2.00 kg, no payload, A1 210 m; the 2.20 kg tank is a characterized "
        "option whose B1, thermal and erosion check is TO-VERIFY. (8) ICD-AIRFRAME v2.1 is out of the finish scope (222): "
        "icd_inputs_for_airframe stays as engine data and open items. (9) Carried from v3.1 unchanged: FC_THRUST NOT armed "
        "on A1; L* = 1.3 s for both brackets; the R2 command hold at the 62.5 N start level; Pc VALID and W10 < 6 m/s AND "
        "sigma_u(3 m) <= 1.0 m/s HARD at A1 launch commit. The v3.2 item texts are in v32_items_rev4b, the lead lines in "
        "lead_decisions_2026-10-19, the changes in changes_rev4b. Earlier status texts: status_superseded_rev4b (v3.1), "
        "status_superseded_rev2p2 (rev2.1), status_superseded_rev2p1 (rev2).")


def update_document(d, items, cl):
    # ------------------------------------------------------------------------------------------------ identity
    d["version"] = "v3.2"
    d["date"] = "2026-10-19"
    replace_kept(d, "staging", OrderedDict(
        v=("Built as staging rev4b (" + STAGE + ") from the published gnc.json v3.1 (4f3209323b0e0ed4) by " + VERSION +
           ": a document change with no new flight (lead 227 (10)). It folds the rev3 / rev4 v3.2 proposals with the "
           "REV-GNC-6 corrections RV6-01 to RV6-14 and the lead lines 204, 208, 213, 214, 219, 222 and 227 (2)-(9). The REV-GNC "
           "reviewer does a document diff (" + STAGE + "/v32/gnc_v3.2_rev4b_vs_v3.1.diff and the key diff) and a delta check "
           "of the separately staged ENG-11 FE-plant re-run; the lead publishes interfaces/gnc.json v3.2 on a clean check. "
           "GNC does not write interfaces/gnc.json."), tag="BUILD RECORD"))
    replace_kept(d, "supersedes", "gnc.json v3.1 (interfaces/gnc.json 4f3209323b0e0ed4, published 2026-10-13); built from "
                                  "staging rev4b")
    replace_kept(d, "status", status_text())
    d["publication_note"]["built_on_rev4b"] = (
        "the evidence folded in v3.2 is staged in staging_v3.1/rev3 (sim6 v2.12-dev family, iface_v3d, pins_rev3) and "
        "staging_v3.1/rev4 (sim6 v2.9-dev for the P2 band, the payload record and the ENG-11 6-DOF; sim6 v2.13-dev amendment "
        "J for RE-24 and the R2 starve bracket; iface_v351 / pins_rev4_v351 and iface_v3d / pins_rev3; m2_eng11 v1.1 for the "
        "linear ENG-11 margins; trees in staging_v3.1/rev4/sim/); REV-GNC-6 re-flew the six decision tables (6000 flights, "
        "identical) and the R2 starve set; rev4b adds no evidence (document change)")
    d["changes_from_v3"].append("later changes: changes_rev4b (gnc.json v3.2, staging rev4b: rev3 / rev4 results with "
                                "REV-GNC-6 RV6-01 to RV6-14 and lead lines 204-227)")
    # ------------------------------------------------------------------------------------------------ v3.2 items
    d["v32_items_rev4b"] = OrderedDict(
        tag=("GNC rev3 / rev4 v3.2 items [0]-[15] in their FINAL text: the rev4 proposals (" + src("rev4_proposals") + ") "
             "with the REV-GNC-6 exact corrections (" + src("review_rev_gnc_6") + " section (e)) and the lead lines 219, 222, "
             "227 (1)-(9) folded; SIM / DERIVED / ASSUMED as tagged per item; not physical approval"),
        evidence_paths=("hub-relative; every rev4 file is in " + R4 + " (MANIFEST_rev4 083675a6abddaabe) with the sha256/16 "
                        "given; the REVIEWER files are in reviews/gnc/rev4/ (MANIFEST_REV-GNC-6 0102191ef982cb8b)"),
        corrections_log=(STAGE + "/v32/v32_corrections_log_rev4b.json: every old / new substring applied to the rev4 texts, "
                         "with its RV6 or lead id (the rejected rev4 texts are not carried into this document)"),
        items=items)
    # ------------------------------------------------------------------------------------------------ flight profile
    fp = d["flight_profile"]
    rb = fp["recommended_baseline"]
    rb["note_rev2p1"] = inline(rb["note_rev2p1"], "A1 apogee target 285 m (h_target trim) ADOPTED",
                               "SUPERSEDED rev4b: A1 210 m, lead 213 / 214, ACCEPTED 227 (1)")
    rb["note_rev2"] = inline(rb["note_rev2"], "h_target 300 -> 285 m", "HISTORY; SUPERSEDED rev4b by 210 m")
    rb["h_target_A1_m_rev4b"] = 210.0
    rb["note_rev4b"] = ("A1 apogee target 210 m (lead 213 / 214; ACCEPTED in 227 (1) with the RV6-03 condition of 227 (8)): "
                        "MECO on predicted apogee 210 m; line-208 band SIM on massprops v3.5.1 (v32_items_rev4b [3]); the "
                        "300 m of note and the 285 m of note_rev2 / note_rev2p1 / h_target_A1_m_rev2 are SUPERSEDED (HISTORY)")
    a1 = fp["mission_plan_v3"]["v"]["A1"]
    replace_kept(a1, "apogee_target_m", 210.0)
    a1["apogee_target_note_rev4b"] = ("210 m = the A1 trim (lead 213 / 214, 227 (1)); the nominal_* and P_* rows of this "
                                      "table are the v3 sizing records at 300 m (h_max 303.45 m, ledger v3d) and are not "
                                      "re-flown here; the 210 m flights are v32_items_rev4b [3]")
    mp = fp["mission_plan_v3"]
    mp["status_rev2p2"] = inline(mp["status_rev2p2"], "A1 is 285 m", "SUPERSEDED rev4b: A1 is 210 m, lead 213 / 214, 227 (1)")
    mp["status_rev4b"] = ("A1 apogee_target_m = 210 m (old value 300.0 in apogee_target_m_superseded_rev4b); every other "
                          "figure in this table is a v3 sizing record at ledger v3d (" + VALID4 + ")")
    replace_kept(fp, "status_rev2p2", VALID4 + ".")
    # ------------------------------------------------------------------------------------------------ closure / trim
    pc3 = d["propellant_closure_v3"]
    replace_kept(pc3, "status_rev2p2", (
        VALID4 + ". HISTORY for the targets: the DC-A1 / DC-A2 h_target_m 300.0 rows and the A1 / A2 h_target sweeps that "
        "start at 300 m are the v3 closure at 300 m (2026-10-12); A1 was 285 m from lead 175 (1) and is 210 m from lead 213 / "
        "214 (rev4 P2 on massprops v3.5.1); A2 was removed from the 2.00 kg plan (lead line 51)."))
    pc3["a1_210m_rev4b"] = OrderedDict(
        v=("A1 apogee target 210 m by the line-208 rule on massprops v3.5.1 (488b47f9d55ff91b): liq|G73 210 m P 0.9835 vs "
           "0.986 (v3d reference st|G73|h285), -25/+20, p 0.551, UB95 0.802 pp PASS; 215 m UB95 1.026 pp (fails the bound by "
           "0.026 pp); pw|G73 band 220 m; N=1000 per main base (A1_none, A1J_pc), dip onset fixed at 80 g; sensitivity arms "
           "and the four-base pooled reading in v32_items_rev4b [3]; with the RV6-03 condition (227 (8))"),
        tag="SIM (flights) / DERIVED (band rule)", source=src("p2_rev4"))
    at = d["rev2"]["apogee_trim"]
    at["decision"] = inline(at["decision"], "h_target 300 -> 285 m", "HISTORY; SUPERSEDED rev4b: A1 210 m, lead 213 / 214, "
                                                                  "227 (1)")
    at["status_rev2p1"] = inline(at["status_rev2p1"], "285 m ADOPTED (175 (1))",
                                 "SUPERSEDED rev4b: A1 210 m, lead 213 / 214, 227 (1)")
    replace_kept(at, "status_rev2p2", (
        VALID4 + ". Per base, M60-purge-liq-A1none (liq|G73|m60 vs liq|none|m60 on A1_none) is -6/+0 (p 0.031) and LOSES "
        "(comparators_rev2p1); the m60 statement above reports the pooled and mass-effect rows only (RV4-06)."))
    # ------------------------------------------------------------------------------------------------ duty, wind, FC_THRUST
    d["duty_cycles"]["status_rev4b"] = (
        "A1 at 210 m (RV6-05, lead 227 (9)): " + RV6_05_NEW + " B1 governs thermal and erosion sizing; the A1 records "
        "listed here stay records; a 210 m A1 p99 cycle re-flown with the recorder (duty-cycle v3 format) is not produced "
        "(GNC open item). v32_items_rev4b [5]")
    d["launch_commit_wind_evidence"]["status_rev4b"] = (
        "A1: HARD rule unchanged (181 (6)); the 285 m coverage tables (rev3 F6) are COMPARATOR records; the e19|G73|L400 "
        "loss lies at W10 >= 6 m/s (-40/+3, p 3.0e-9) and not inside W10 < 6 m/s (-3/+0, p 0.25, n 728, low power); "
        "coverage at 210 m (e19, L400, wind sweep) is NOT FLOWN (TO-VERIFY, GNC); the W10 < 6 m/s envelope now also carries "
        "pcf_tmax 0.8 s (227 (5)). v32_items_rev4b [4], [6]")
    d["over_thrust_fc_thrust"]["status_rev4b"] = (
        "FC_THRUST stays NOT armed on A1; B1 arming is not proposed before a measured IMU vibration spectrum (204 (4) F8, 208 "
        "(5)); the latency and windowed-budget flights are at the 300 m comparator configuration (conservative for 210 m). "
        "v32_items_rev4b [7]")
    # ------------------------------------------------------------------------------------------------ structure / bending
    st = d["requirements"]["structure"]
    st["airframe_first_bending_min_Hz"]["status_rev4b"] = (
        RV6_01_III + " Per line 222 this is an open item kept for the airframe work, not a new v3.2 number (lead 227 (3): "
        "10-22 Hz fail on at least one axis, 24.3-30 Hz pass, DERIVED); the 10 Hz value and its tag are kept as they were "
        "(REV-GNC-6 [12] bending sweep, " + src("rv6_v05_eng11_env") + ")")
    st["gimballed_engine_first_mode_min_Hz"]["note_rev4b"] = (
        "the rocking-mode targets above (mechanical.json v2 era) are carried; the v3.5.1 TVC loop is set by ENG-11 "
        "(requirements.gimbal.tvc_actuator.ENG-11_servo_output_stiffness)")
    ia = d["icd_inputs_for_airframe"]
    ia["cg_and_length_limits"]["status_rev4b"] = (
        "airframe_first_bending_min_Hz 10 Hz / goal 15 Hz: " + RV6_01_III + " Open item for the airframe work (line 222)")
    # ------------------------------------------------------------------------------------------------ gimbal / ENG-11
    tv = d["requirements"]["gimbal"]["tvc_actuator"]
    tv["ENG-11_servo_output_stiffness"] = OrderedDict(
        v=ENG11_V, tag=("REQ lead 227 (3) (RV6-01 wording + RV6-14 sentence) on DERIVED linear margins (m2_eng11 v1.1); K_s, "
                        "J value, bending and damping ASSUMED; J convention VERIFIED (227 (2))"),
        note=("the line-218 one-sided proposal is REPLACED; the interim 'K_s >= 116' of the v3.1 era is SUPERSEDED; text and "
              "evidence: v32_items_rev4b [12]"),
        J_convention=L227_2)
    tv["ENG-07c_J_int_check_value_kgm2"]["note_rev4b"] = (
        "J convention (lead 227 (2)): " + L227_2)
    tv["ENG-07d_flex_gain_margin_min_dB"]["note_rev4b"] = (
        "on the v3.5.1 vehicle ENG-07d is assessed by ENG-11 (ENG-11_servo_output_stiffness; v32_items_rev4b [12]): the "
        "6-DOF Monte Carlo loses no landing for any K_s arm (K_s 58 included) but does not carry the linear flex corner set, "
        "so the requirement rests on the linear margins")
    bt = tv["B-TVC-1"]
    v_old = bt["v"]
    replace_kept(bt, "v", OrderedDict(
        measure=["servo output stiffness K_s per servo with its measurement uncertainty, the rotor + gear-train inertia J at "
                 "the servo output shaft and the reflected-inertia convention (ENG-11 acceptance, lead 227 (2)-(3))",
                 "axis rocking modes and damping per axis on the powered servos with the engine dummy, at the poses (sets the "
                 "notch centres; ENG-11 re-run input)",
                 v_old["measure"][3], v_old["measure"][4], v_old["measure"][5]],
        acceptance=("ENG-11 (" + ENG11_V + ")"),
        gate_outcomes=OrderedDict([
            ("ENG-07d re-run PASS on the measured K_s, J, convention, rocking and bending modes", "K_s frozen; proceed"),
            ("ENG-07d re-run FAIL", "notch set changed (second notch on the measured bending mode) and the margins re-run "
                                    "before any K_s change; a K_s change (stiffer servo; maxon ECX 22 M class, TO-QUOTE) "
                                    "only after that"),
            ("reduced bandwidth", v_old["gate_outcomes"]["reduced bandwidth"])])))
    bt["tag_rev4b"] = ("REQ lead 227 (3) (ENG-11 acceptance) replacing the K_s ~100 N m/rad gate of 2026-10-12 (old v in "
                       "v_superseded_rev4b)")
    # ------------------------------------------------------------------------------------------------ landing mass
    lm = ia["landing_mass_window_kg"]
    v0 = lm["v"]
    newv = OrderedDict()
    for k, val in v0.items():
        newv[k] = [val[0], 16.15] if isinstance(val, list) else val
    replace_kept(lm, "v", newv)
    replace_kept(lm, "tag", "DERIVED hover rule (lower bounds, unchanged); upper bound REQ lead 227 (4) = nominal planning "
                            "touchdown mass <= 16.15 kg (v3.5.1 estimate covered by the 210 m decision MC, SIM N=1000 per "
                            "main base)")
    replace_kept(lm, "note", "RV-1c nominal 14.83 kg is the ledger-v3d value (HISTORY); v3.5.1 nominal touchdown 16.11 kg "
                             "(DERIVED, A1_none liq, tank at 0.58 m, 210 m)")
    lm["record_rev4b"] = OrderedDict(v=RV6_02, lead=L227_4, tag="SIM / DERIVED record (not a controller-qualified window)",
                                     source=f"{src('landing_mass_h210')}; {src('payload_n500')}; {src('rv6_v04_items')}")
    lm["status_rev4b"] = "upper bound restated by the lead (227 (4)); the rev4 widening to 14.18-18.13 kg is REJECTED (RV6-02)"
    thr = d["requirements"]["throttle"]
    thr["landing_mass_window_min_kg_by_floor"]["note_rev4b"] = (
        "lower bounds unchanged (lead 227 (4)); " + MASS_V + "; the RV-1c 14.83 kg note is the ledger-v3d value (HISTORY)")
    thr["ceiling_at_landing_min_N"]["note_rev4b"] = (
        "the same rule at the v3.5.1 nominal planning touchdown mass 16.15 kg gives 237.6 N (DERIVED, 1.5 x 16.15 kg x "
        "9.80665 m/s2); rated 500 N gives touchdown T/W 3.16 (v32_items_rev4b [15] (c))")
    ia["about"] = ia["about"]
    ia["scope_rev4b"] = (
        "Line 222 (founder decision, 2026-10-19): " + L222 + " This block is kept as engine data and open items for when "
        "the airframe is tackled; items kept: bay bore >= 140 mm down to the nozzle and the v3.5.1 envelope; mounting loads "
        "at the 16 M5 holes and ring resultants (FEA3D lines 217 / 220); engine-mount modes (line 221); BL-06 vent hole; "
        "tank station 0.58-1.08 m; first-flight apogee 210 m; the ENG-11 requirement to MEASURE the airframe first bending "
        "mode before K_s is frozen (lines 218 / 227 (3)); the 2.20 kg tank option (line 219); the landing-mass record "
        "(landing_mass_window_kg.record_rev4b); the drogue deploy-to-inflation bound (227 (8))")
    ia["mass_and_cg"]["status_rev4b"] = (
        "ledger-v3d values (HISTORY for the v3.5.1 vehicle); the A1 210 m decision flies massprops v3.5.1 with the 2.00 kg "
        "tank at 0.58 m (nominal touchdown 16.11 kg DERIVED; dispersed record in landing_mass_window_kg.record_rev4b)")
    ia["drogue"]["status_rev4b"] = (
        "the deploy-to-inflation delay is not modelled (quasi-steady drogue): at the 210 m trim it acts as a gate delay on "
        "every flight (REV-GNC-6 (c)); a bound (TO-VERIFY, canopy data; owner recovery / airframe with GNC) is a condition "
        "for the flight acceptance of the 210 m relight P (lead 227 (8))")
    ia["open"].append("rev4b (lines 222, 227 (3)): measure the airframe first bending mode (full and landing) before K_s is "
                      "frozen; airframe_first_bending_min_Hz 10 Hz is NOT CONSISTENT with ENG-07d at the ENG-11 window with one "
                      "fixed notch (owner: airframe work, deferred by the founder; GNC re-runs ENG-07d on the value)")
    ia["open"].append("rev4b (227 (8)): drogue deploy-to-inflation delay bound (TO-VERIFY, canopy data; owner recovery / "
                      "airframe with GNC)")
    ia["open"].append("rev4b (219, 227 (9)): the 2.20 kg tank option (3.48 L at 85 % fill, inner span 0.58-1.069 m) is a "
                      "characterized option, not a baseline; its B1, thermal and erosion check is TO-VERIFY (Combustion / "
                      "Mechanical)")
    # ------------------------------------------------------------------------------------------------ R2 / pcf_tmax
    rc = d["requirements"]["ignition"]["relight_conditions"]
    old_tail = ("with Pc invalid and no R2 confirmation by t_E2 + pcf_tmax (0.5 s): hold the drogue and command ECU ABORT. "
                "The baseline is frozen at E0 in the flown implementation; R2 v2 (re-reference at E2 or drogue-drag "
                "compensation, threshold for the window, cold-flow apparent thrust F_cold(lift, P_tank) in the flame-out "
                "case) is rev3 P4 and the lead then sets pcf_tmax.")
    vnew = rc["v"]
    if vnew.count(old_tail) != 1:
        raise RuntimeError("relight_conditions.v tail not found once")
    vnew = vnew.replace(old_tail, (
        "with Pc invalid and no R2 confirmation by t_E2 + pcf_tmax: hold the drogue and command ECU ABORT; " + PCF_V + ". "
        "R2 v2 as flown in rev3 / rev4 (mode 3: reference and descent rate sampled at E2, drag term compensated by "
        "(vz/vz(E2))^2, 3-frame running minimum >= 37.16 N; the E0-frozen baseline of the first R2 implementation is "
        "superseded) with " + REINIT_V + "; Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 "
        "margin (227 (6))."), 1)
    replace_kept(rc, "v", vnew)
    replace_kept(rc, "tag", "DESIGN (LEAD CHANGELOG lines 168 (1), 181 (4), 186 (1)-(2), 227 (5)-(6)); S17 confirmation "
                            "(Electronics v2.11) OPEN")
    rc["status_rev2p1"] = inline(rc["status_rev2p1"], "pcf_tmax 0.8 s NOT adopted",
                                 "SUPERSEDED rev4b: 0.8 s ADOPTED for the W10 < 6 m/s envelope, lead 227 (5)")
    rc["status_rev4b"] = ("pcf_tmax 0.8 s (W10 < 6 m/s envelope) and the mode-3 filter re-initialisation folded from lead 227 "
                          "(5)-(6); the v3.1 text is kept in v_superseded_rev4b")
    fe = d["flight_software"]["rev2p1_entries"]
    drp = fe["drogue_release_pc_invalid"]
    replace_kept(drp, "v", ("R2 accelerometer confirmation (relight_conditions.v); " + PCF_V + "; R2 COMMAND HOLD (lead 186 "
                            "(2)): while the drogue is attached with Pc invalid, the ECU open-loop command is held at the "
                            "start level 62.5 N until the release; " + REINIT_V))
    replace_kept(drp, "tag", "DESIGN (LEAD 181 (4), 186 (2), 227 (5)-(6))")
    am = d["rev2"]["amendment_V_pc_invalid"]
    am["status_rev2p1"] = inline(am["status_rev2p1"], "0.8 s NOT adopted",
                                 "SUPERSEDED rev4b: 0.8 s ADOPTED for the W10 < 6 m/s envelope, lead 227 (5)")
    am["status_rev4b"] = (
        "R2 v2 delivered in rev3 P4 / rev4 (v32_items_rev4b [6], [14]); " + PCF_V + "; " + REINIT_V + "; frame-noise budget "
        "by Electronics (227 (6)); the rev3 lit-side statistics are WITHDRAWN (W2; rev4 / rev4b withdrawn markers)")
    oi_txt = d["rev1_items"]["v"]["drogue_release_rule"]["fc_implementation"]
    oi_txt["open_item"] = inline(oi_txt["open_item"], "pcf_tmax 0.5 s",
                                 "SUPERSEDED rev4b: 0.8 s in the W10 < 6 m/s envelope, lead 227 (5)")
    f175 = d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"]["folded"]
    f175["175 (5)"] = inline(f175["175 (5)"], "(pcf_tmax 0.5 s)",
                             "SUPERSEDED rev4b: 0.8 s ADOPTED for the W10 < 6 m/s envelope, lead 227 (5)")
    lc = d["requirements"]["launch_commit_rev2p1"]["v"][1]
    lc["why_rev4b"] = (
        "at the A1 trim 210 m the rule stays HARD (181 (6)); it now also carries pcf_tmax 0.8 s (227 (5)): R2 v2 mode 3 at "
        "the 0.8 s window gives 31.86 N inside W10 < 6 (margin +5.30 N, 0/1502 dead-vehicle releases) and 39.45 N at all "
        "winds (-2.29 N, 4/2072, outside the rule); the frame-noise budget is pending (227 (6); at 5 N rms iid ASSUMED the "
        "bounding run releases with probability 18.4 % at 0.8 s, RV6-07 DERIVED); the wind basis was flown at 285 m and the "
        "210 m wind coverage is not flown (TO-VERIFY, v32_items_rev4b [4])")
    fm = d["fmea_inputs_rev2p1"]
    fm["status_rev4b"] = (
        "item 5 (undetected flame-out): with R2 v2 mode 3 at the adopted 0.8 s window the W10 < 6 m/s margin is +5.30 N "
        "(31.86 N vs 37.16 N; 0/1502 released) and the all-winds margin -2.29 N (4/2072 released, outside the hard wind "
        "rule); the 16.31 N margin of item 5 is the R2 v1 value; frame-noise budget pending (227 (6)). New inputs: a "
        "detected landing-burn gimbal jam aborts (GIMBAL_FAULT not inhibited near touchdown, 227 (7)); at 210 m the drogue "
        "deploy-to-inflation delay acts as a gate delay on every flight (227 (8))")
    # ------------------------------------------------------------------------------------------------ FSW entries
    fs = d["flight_software"]
    fs["rev4b_entries"] = OrderedDict([
        ("mode3_filter_reinit", OrderedDict(v=REINIT_V, tag="REQ flight software (lead 227 (6)); implementation Electronics "
                                                            "v2.11; S17 and the GNC R2 re-run OPEN",
                                            evidence="v32_items_rev4b [14] (a)")),
        ("r2_frame_noise_budget", OrderedDict(
            v=("Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin (227 (6)): " +
               RV6_07_NEW), tag="REQUEST to Electronics (lead 227 (6)); DERIVED (REV-GNC-6 RV6-07, iid ASSUMED)")),
        ("gimbal_fault_monitor_re24", OrderedDict(
            v=("GIMBAL_FAULT abort NOT inhibited near touchdown: a detected landing-burn jam aborts as designed (lead safety "
               "decision 227 (7)); revisit if B-TVC-1 gives a jam rate"),
            tag="DESIGN (LEAD 227 (7)) on SIM RE-24 (sim6 v2.13-dev amendment J; jam bound ASSUMED from Electronics S6/SIL "
                "v2.10)", evidence="v32_items_rev4b [13]", lead=L227_7)),
        ("rg08_replan_research_proposal", OrderedDict(
            v=items[8]["text"], tag="RESEARCH PROPOSAL (not flown; line 161 'UNKNOWN = UNPRIMED from the start' stands, "
                                    "204 (4) F9)")),
    ])
    pb = fs["relight_sequence_placeholder"]["v"]["purge_bound"]
    pb["note_rev4b"] = items[9]["text"]
    fs["eng07d_notch"]["note_rev4b"] = (
        "ENG-11 (227 (3)): with this single fixed notch the 100-130 N m/rad window passes only for a full-tank first bending "
        ">= 24.3 Hz among the values tested (REV-GNC-6 v05 part C); the second notch on the measured bending mode stays a "
        "GNC study (RESEARCH PROPOSAL in v32_items_rev4b [12])")
    d["requirements"]["ignition"]["sim_start_level_open_item_rev4b"] = OrderedDict(
        v=items[10]["text"] + (": sim6 flies the relight start at 100 N (closed-loop floor 0.2 x F_max) before E2 while "
                               "Combustion's start lift is 62.5 N (rev3 F10)"),
        tag="SIM model item (open; 204 (4) F10)")
    # ------------------------------------------------------------------------------------------------ relight planning / G
    d["relight_planning_181"]["status_rev4b"] = (
        "late commit / gate delay (v32_items_rev4b [1], [2]): L* = 1.3 s stays the commit rule and a realised commit lead "
        "below about 2.1 s is not counted as a landing (204 (1), 208 (4)); at the A1 trim 210 m the 285 m gate-delay "
        "tolerance does not carry (D_crit(2.1 s) 0.164 / -0.154 s, 16 of 1000 zero-slack commits per main base); the 210 m "
        "relight P is used for flight acceptance only after the gate-delay injection arm and the drogue inflation bound "
        "(227 (8), GNC open item); the line-194 comparator stays NOT ADOPTED (204 (2), 208 (3))")
    d["rev2"]["amendment_G_late_commit"]["status_rev4b"] = d["relight_planning_181"]["status_rev4b"]
    # ------------------------------------------------------------------------------------------------ requests / stale notes
    rq = d["requests"]
    hits = [i for i, x in enumerate(rq) if isinstance(x, str) and "first bending >= 10 Hz" in x]
    if len(hits) != 1:
        raise RuntimeError(f"requests: 'first bending >= 10 Hz' found {len(hits)} times")
    rq[hits[0]] = inline(rq[hits[0]], "first bending >= 10 Hz",
                         "rev4b: NOT CONSISTENT with ENG-07d at the ENG-11 window with one fixed notch; set from the "
                         "measured mode, lead 227 (3); airframe work deferred, line 222")
    ln = d["mech_v2_rebaseline"]["linkage_ratio_sweep"]
    ln["note"] = inline(ln["note"], "at K_s >= 116", "rev4b: the interim K_s >= 116 is SUPERSEDED by the ENG-11 window, lead "
                                                     "227 (3)")
    d["reference_vehicle"]["status_rev4b"] = (
        "RV-1c is the ledger-v3d reference vehicle (HISTORY for the A1 decision); the A1 210 m decision flies massprops "
        "v3.5.1 (rev4 P2; v32_items_rev4b [3], [11])")
    d["rev3_plan"]["status_rev4b"] = (
        "EXECUTED: staging_v3.1/rev3 (MANIFEST_rev3 79c2c8cd5d10e3c4; REV-GNC-5, lead 207 / 208) and staging_v3.1/rev4 "
        "(MANIFEST_rev4 083675a6abddaabe; REV-GNC-6, lead 227); results in v32_items_rev4b. Not run: P7 (gated at the SIL / "
        "HIL freeze, 181 (7)); P8 re-plan (research proposal, v32_items_rev4b [8])")
    # ------------------------------------------------------------------------------------------------ open items
    oi = d["open_items"]
    n_oi = len(oi)

    def sup(i, why, expect):
        if expect not in oi[i]:
            raise RuntimeError(f"open_items[{i}] does not carry '{expect}'")
        oi[i] = f"SUPERSEDED (rev4b; {why}): {oi[i]}"
    sup(31, "rev3 P5 delivered: FC_THRUST stays NOT armed on A1; B1 arming waits for a measured IMU spectrum (204 (4) F8, "
            "v32_items_rev4b [7]); the open part follows below", "FC_THRUST arming")
    sup(35, "the v3.5.1 re-fly is rev4 P2: A1 210 m on massprops v3.5.1 (lead 213 / 214, 227 (1))", "mass change control")
    sup(36, "rev3 P6 delivered and decided: 204 (1)-(2), 208 (3)-(4); the 210 m gate-delay arm follows below (227 (8))",
        "late purge commit")
    sup(37, "R2 v2 delivered (rev3 P4, rev4); pcf_tmax 0.8 s for W10 < 6 m/s and the mode-3 filter re-initialisation decided "
            "(227 (5)-(6)); the open parts follow below", "R2 v2")
    sup(39, "ENG-11 delivered (rev4) and decided: design-to window with acceptance (227 (3)); the FE-plant re-run follows "
            "below", "ENG-11 stiffness - GNC assesses")
    sup(40, "rev3 P9 delivered (full m2_bitcheck_v29 v1.2 run on the rev3 code: PASS, rev3_results.json bitchecks); the "
            "grain-gate note stays", "m2_bitcheck_v29")
    sup(41, "the A1 decision is on massprops v3.5.1 (rev4 P2); the validity statement is restated in status (VALIDITY rev4b)",
        "VALIDITY")
    new_oi = [
        "rev4b (227 (8); RV6-03): 210 m gate-delay injection arm (D = 0.25 / 0.5 / 0.75 / 1.0 s, both states, N=1000 per main "
        "base, line-208 statistics; about 16,000 flights) and a bound on the drogue deploy-to-inflation delay (TO-VERIFY, "
        "canopy data) before the 210 m relight P is used for flight acceptance; not needed for v3.2 or the datasheet. Owner: "
        "GNC (arm); recovery / airframe with GNC (canopy bound)",
        "rev4b (227 (3); RV6-14): ENG-11 window re-verified on the 3D FE plant of CAD v3.5.1 (neutral, stop and cone poses; "
        "rigid / compliant airframe; T_REF and hot E; J 0.76 / 1.6 / 2.7e-3 with cons and n48; bending x 0.9 / 1.0 / 1.1; "
        "K_s 90-160) before the datasheet quotes the window as design-to; staged apart in " + STAGE + "/eng11_fe/ for the "
        "REV-GNC delta check. Owner: GNC (re-run), REV-GNC reviewer (check), lead (datasheet sentence)",
        "rev4b (227 (3), line 222): airframe first bending mode (full and landing) measured or from the airframe FE; "
        "airframe_first_bending_min_Hz 10 Hz NOT CONSISTENT with ENG-07d at the window with one fixed notch. Owner: airframe "
        "work (deferred by the founder, line 222); GNC re-runs ENG-07d on the value",
        "rev4b (227 (3)): second ECU notch on the measured bending mode (RESEARCH PROPOSAL; hypothesis: removes the "
        "coincidence failures; comparator: the single notch; refutation: any floor20 corner below 6 dB for K_s 100-270 at "
        "0.9-1.1 x bending). Owner: GNC",
        "rev4b (227 (2)-(3)): B-TVC-1 measures K_s (with uncertainty), J at the servo output shaft, the reflected-inertia "
        "convention and the rocking modes at the poses; K_s is frozen only on an ENG-07d PASS. Owner: founders / Electronics "
        "(bench), GNC (re-run)",
        "rev4b (227 (6)): mode-3 filter re-initialisation at the Pc-invalid onset implemented and S17 run (onsets 1-50 ms x "
        "frame phases x noise); FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin. Owner: Electronics v2.11; "
        "then GNC re-runs R2 v2 with the flush",
        "rev4b (227 (5)): pcf_tmax 0.8 s confirmed in the Electronics S17 sweep or returned to the lead; the lit side on "
        "Combustion v2.4b (F_cold + grain_q1d start history). Owner: Electronics (S17), Combustion (v2.4b), then GNC",
        "rev4b (219, 227 (9)): 2.20 kg tank option: A1 engine-on p99 8.92 / 8.71 s (max 9.24 s) exceeds the 8.258 s A1 sizing "
        "counter; B1, thermal and erosion check TO-VERIFY before the option is quoted on the datasheet. Owner: Combustion / "
        "Mechanical",
        "rev4b: coverage at 210 m (e19, L400, wind sweep) not flown; a 210 m A1 duty-cycle record with the recorder not "
        "produced. Owner: GNC",
        "rev4b (204 (4) F10): sim6 relight start level 100 N vs Combustion's 62.5 N start lift (open model item). Owner: GNC",
        "rev4b (227 (7)): GIMBAL_FAULT abort not inhibited near touchdown; revisit if B-TVC-1 gives a jam rate; encoder "
        "noise, vibration and supply sag not modelled in RE-24. Owner: lead (revisit), Electronics / founders (jam rate), "
        "GNC (re-run)",
    ]
    oi.extend(new_oi)
    return n_oi, len(new_oi)


# ------------------------------------------------------------------------------------------------ lead lines + records
def lead_block(cl):
    lines_sha = shas("\n".join(cl[n] for n in sorted(cl)))
    return OrderedDict(
        source=(f"interfaces/CHANGELOG.md lines {', '.join(str(n) for n in LEAD_LINES)} (lead decisions, verbatim; lines 204, "
                f"208, 213, 214 are dated 2026-10-13); file lines 1-{CHLOG_N} sha256/16 {CHLOG_SHA16}; sha256/16 of the quoted "
                f"lines {lines_sha}"),
        verbatim=OrderedDict((str(n), cl[n]) for n in LEAD_LINES),
        reference_lines=OrderedDict([
            ("203 (3)", "purge: ECU both-open cap <= 2.55 s (v32_items_rev4b [9])"),
            ("207", "REV-GNC-5 independent check of GNC rev3 (verdict in 208)"),
            ("216", "REV-ELEC-2: S17 restated as conditional (1), ECU backstop (2)(b), purge basis (5) (v32_items_rev4b [9], [14])"),
            ("218", "GNC rev4 staged (MANIFEST_rev4 083675a6abddaabe); its 'K_s >= 100' proposal is replaced by 227 (3)"),
            ("221", "FEA3D modal and load-path periods (engine-mount modes; ENG-11 plant check, RV6-14)"),
            ("223", "FEA3D TC-01 FA-1 decision: no GNC item; its (5) J reading is WITHDRAWN by 227 (2) and is not carried"),
            ("225 / 226", "FEA3D final handback and republish (REPORT-FEA3D ff24718e9db201e5): ENG-11 FE re-run input"),
            ("228", "TC-01 third condition (Combustion v2.4b spectrum): no GNC item")]),
        folded=OrderedDict([
            ("204 (1)", "L* = 1.3 s; a commit lead below about 2.1 s not counted (v32_items_rev4b [1]); its 'nominal leads >= "
                        "2.65 s ... only after a gate fault' holds at 285 m only (RV6-03, 227 (8))"),
            ("204 (2)", "line-194 comparator NOT ADOPTED (v32_items_rev4b [2])"),
            ("204 (3)", "band rule; the 250 m planning value is WITHDRAWN by 208 (2); A1 = 210 m by 213 / 214"),
            ("204 (4)", "F6-F11 recorded (v32_items_rev4b [4]-[8], [10]); 'AR(1) fails everywhere' corrected by 208 (5)"),
            ("204 (5)-(6)", "REV-GNC-5 and rev4 executed (rev3_plan.status_rev4b)"),
            ("208 (1)-(2)", "line-208 rule (v32_items_rev4b [3]; propellant_closure_v3.a1_210m_rev4b)"),
            ("208 (3)", "revisit rule of the comparator (v32_items_rev4b [2])"),
            ("208 (4)", "D_crit 3.765 s at 285 m; its '+0.156 s on the pc bases' is CORRECTED by RV6-04 (A1J_pc 3.633 s at "
                        "N=1000; 3.921 s on A1_pc, N=500; v32_items_rev4b [1] comparator_285m)"),
            ("208 (5)-(6)", "recorded (v32_items_rev4b [0], [4], [6], [7])"),
            ("213", "A1 lowered to about 210 m; its 'the A1 duty cycle shortens' is corrected by 227 (9); its ICD-AIRFRAME v2.1 "
                    "consequence is removed by 222"),
            ("214", "A1 = 210 m (status (1); flight_profile; propellant_closure_v3; v32_items_rev4b [3])"),
            ("219", "N2O tank 2.00 kg, no payload, A1 210 m; the 2.20 kg tank a characterized option (status (7); "
                    "v32_items_rev4b [15])"),
            ("222", "ICD-AIRFRAME v2.1 out of scope: icd_inputs_for_airframe.scope_rev4b; the airframe items kept as engine "
                    "data and open items"),
            ("227 (1)", "A1 = 210 m ACCEPTED with the RV6-03 condition (status (1); v32_items_rev4b [3])"),
            ("227 (2)", "J convention VERIFIED, value TO-VERIFY (v32_items_rev4b [12]; tvc_actuator ENG-11 and ENG-07c notes); "
                        "the 223 (5) reading is WITHDRAWN and not carried"),
            ("227 (3)", "ENG-11 RV6-01 wording + RV6-14 sentence (v32_items_rev4b [12]; tvc_actuator.ENG-11_servo_output_"
                        "stiffness; B-TVC-1); airframe_first_bending_min_Hz NOT CONSISTENT (requirements.structure, "
                        "icd cg_and_length_limits, requests); FE-plant re-run staged apart"),
            ("227 (4)", "landing mass (icd landing_mass_window_kg v / tag / note / record_rev4b; throttle note; v32_items_rev4b "
                        "[11])"),
            ("227 (5)", "pcf_tmax 0.8 s for W10 < 6 m/s (relight_conditions; flight_software drogue_release_pc_invalid; "
                        "amendment_V status; launch commit why_rev4b; v32_items_rev4b [6], [14])"),
            ("227 (6)", "mode-3 filter re-initialisation (flight_software.rev4b_entries.mode3_filter_reinit; relight_conditions); "
                        "frame-noise budget request (rev4b_entries.r2_frame_noise_budget)"),
            ("227 (7)", "GIMBAL_FAULT not inhibited near touchdown (rev4b_entries.gimbal_fault_monitor_re24; v32_items_rev4b "
                        "[13]; fmea status)"),
            ("227 (8)", "gate-delay arm + inflation bound before flight acceptance: GNC open item (status (1); "
                        "relight_planning_181; icd drogue; open items)"),
            ("227 (9)", "duty-cycle correction and payload record (duty_cycles.status_rev4b; v32_items_rev4b [5], [15])"),
            ("227 (10)", "this build (document change) and the ENG-11 FE-plant re-run staged apart")]),
        tag="LEAD decisions (verbatim) and where rev4b folds them")


def records(d, items, n_oi, n_new, cl):
    lines_sha = shas("\n".join(cl[n] for n in sorted(cl)))
    d["lead_decisions_2026-10-19"] = OrderedDict(rev4b_lines_204_227=lead_block(cl))
    d["changes_rev4b"] = [
        "identity: version v3.2, date 2026-10-19; staging, supersedes and status replaced (old under *_superseded_rev4b); "
        "publication_note.built_on_rev4b; changes_from_v3 pointer",
        "v32_items_rev4b: items [0]-[15] in their final text (rev4 proposals with RV6-01 to RV6-14 and lead 219, 222, 227 "
        "(1)-(9)); item [1] comparator_285m replaced by the REVIEWER N=1000 values (old under comparator_285m_superseded_rev4b)",
        "lead_decisions_2026-10-19.rev4b_lines_204_227: verbatim lines 204, 208, 213, 214, 219, 222, 227, reference lines and "
        "the fold map",
        "flight_profile: recommended_baseline note_rev4b and h_target_A1_m_rev4b (210 m), inline markers on note_rev2 / "
        "note_rev2p1; mission_plan_v3 A1 apogee_target_m 300 -> 210 (old under apogee_target_m_superseded_rev4b), "
        "apogee_target_note_rev4b, status_rev4b, inline marker in status_rev2p2; status_rev2p2 replaced (VALIDITY rev4b)",
        "propellant_closure_v3: status_rev2p2 replaced (VALIDITY rev4b, 210 m), a1_210m_rev4b added; rev2.apogee_trim: "
        "status_rev2p2 replaced, inline marker in status_rev2p1",
        "duty_cycles.status_rev4b (RV6-05, 227 (9)); launch_commit_wind_evidence.status_rev4b; "
        "over_thrust_fc_thrust.status_rev4b",
        "requirements.structure.airframe_first_bending_min_Hz.status_rev4b (RV6-01 (iii) NOT CONSISTENT; value kept, open "
        "item per 222); gimballed_engine_first_mode_min_Hz.note_rev4b; icd cg_and_length_limits.status_rev4b",
        "requirements.gimbal.tvc_actuator: ENG-11_servo_output_stiffness added (227 (3)); ENG-07c and ENG-07d note_rev4b; "
        "B-TVC-1 v replaced (measure list, ENG-11 acceptance, gate outcomes; old under v_superseded_rev4b), tag_rev4b",
        "icd_inputs_for_airframe: landing_mass_window_kg v (upper 16.15 kg), tag, note replaced (old under *_superseded_rev4b), "
        "record_rev4b and status_rev4b added; scope_rev4b (line 222); mass_and_cg and drogue status_rev4b; three open entries",
        "requirements.throttle: landing_mass_window_min_kg_by_floor and ceiling_at_landing_min_N note_rev4b (the 237.6 N is "
        "DERIVED arithmetic, 1.5 x 16.15 kg x g0)",
        "requirements.ignition.relight_conditions: v and tag replaced (pcf_tmax 0.8 s for W10 < 6 m/s, R2 v2 mode 3, mode-3 "
        "filter re-initialisation; old under *_superseded_rev4b), status_rev4b, inline marker in status_rev2p1; "
        "sim_start_level_open_item_rev4b",
        "flight_software: rev2p1_entries.drogue_release_pc_invalid v and tag replaced; rev4b_entries (mode3_filter_reinit, "
        "r2_frame_noise_budget, gimbal_fault_monitor_re24, rg08_replan_research_proposal); purge_bound.note_rev4b; "
        "eng07d_notch.note_rev4b",
        "rev2.amendment_V_pc_invalid.status_rev4b and an inline marker in status_rev2p1; rev1_items drogue_release_rule "
        "fc_implementation.open_item inline marker; lead_decisions_2026-10-13 folded 175 (5) inline marker",
        "requirements.launch_commit_rev2p1.v[1].why_rev4b; fmea_inputs_rev2p1.status_rev4b",
        "relight_planning_181.status_rev4b and rev2.amendment_G_late_commit.status_rev4b",
        "requests: inline marker on 'first bending >= 10 Hz'; mech_v2_rebaseline.linkage_ratio_sweep.note inline marker on "
        "the interim K_s >= 116; reference_vehicle.status_rev4b; rev3_plan.status_rev4b",
        f"open_items: [31], [35], [36], [37], [39], [40], [41] marked SUPERSEDED (rev4b); {n_new} rev4b items appended "
        f"(owners named); {n_oi} -> {n_oi + n_new}",
        "checkpoint_rev2p2 moved to rev2p2_checkpoint_superseded_rev4b; checkpoint_rev4b, inputs_read.rev4b, scripts_rev4b, "
        "rev4b_document_self_check added",
        "not changed: every number computed by GNC in v3.1 (kept as records with the VALIDITY statement), every v3.1 lead "
        "block, the rev2 / rev2.1 / rev2.2 records and self-checks"]
    d["inputs_read"]["rev4b"] = OrderedDict(
        [(k, OrderedDict(path=p, sha256_16=h)) for k, (p, h) in SRC.items()]
        + [("changelog_lines", OrderedDict(lines=list(LEAD_LINES), file_lines_1_228_sha256_16=CHLOG_SHA16,
                                           sha256_16_of_lines=lines_sha))])
    d["scripts_rev4b"] = [f"{STAGE}/v32/scripts/m2_gnc_json_v32_rev4b.py", f"{STAGE}/v32/scripts/m2_rev4b_wmark.py"]
    d["rev2p2_checkpoint_superseded_rev4b"] = d.pop("checkpoint_rev2p2")
    d["checkpoint_rev4b"] = OrderedDict(
        delivered_reviewed_date=("GNC (Senior Space/GNC) / independent delta re-check REV-GNC-6: PUBLISHABLE WITH "
                                 "CORRECTIONS (" + src("review_rev_gnc_6") + ") / 2026-10-19; RV6-01 to RV6-14 applied in "
                                 "this build; the REV-GNC reviewer does a document diff and the lead publishes (227 (10))"),
        configuration=("document change only: no flight and no new GNC-computed number; source gnc.json v3.1 "
                       "4f3209323b0e0ed4; rev4 proposals " + src("rev4_proposals") + "; builder " + VERSION +
                       " (deterministic); CHANGELOG lines quoted (sha256/16 " + lines_sha + ")"),
        claim=["RV6-01 to RV6-14 exact texts applied to items [0]-[15]; each asserted verbatim in the review and each replaced "
               "substring asserted unique (v32_corrections_log_rev4b.json)",
               "lead 227 (2)-(9) folded: J convention, ENG-11 window with acceptance and plant basis, landing mass <= 16.15 "
               "kg, pcf_tmax 0.8 s at W10 < 6 m/s, mode-3 filter re-initialisation, GIMBAL_FAULT not inhibited, gate-delay "
               "condition, duty-cycle correction and payload record",
               "lines 204, 208, 213, 214, 219, 222 folded with the fold map; ICD-AIRFRAME v2.1 out of scope, the airframe "
               "items kept as engine data and open items",
               "every replaced value kept under *_superseded_rev4b or marked inline; the rejected rev4 texts are not carried"],
        sources=[src(k) for k in SRC] + ["interfaces/CHANGELOG.md lines " + ", ".join(str(n) for n in LEAD_LINES)],
        tests=["builder run twice: identical bytes", "author scan rev4b_document_self_check: 0 unmarked; structural checks "
               "all True", "REV-GNC-4 gate t10_postcheck v2 (read-only reviewer tool) run on this file: result recorded in "
               + STAGE + "/v32/logs/ (C06 encodes the v3.1 NOT-ADOPTED state of pcf_tmax 0.8 s that 227 (5) reverses)",
               "key diff and unified text diff against v3.1 recorded", "NOT run: any flight (by design)"],
        unknowns=["no hardware data; nothing here is physical approval",
                  "K_s, J value, rocking damping and the airframe bending mode ASSUMED until B-TVC-1 and the airframe work",
                  "the ENG-11 window on the FE plant (RV6-14 re-run, staged apart)",
                  "the 210 m gate-delay cost and the drogue inflation delay; 210 m coverage (e19, L400, wind)",
                  "S17 confirmation of pcf_tmax 0.8 s, the mode-3 flush, the FC frame-noise budget",
                  "the 2.20 kg option's B1 / thermal / erosion check; payload inertia and station"],
        next_closure=["REV-GNC document diff of this candidate against v3.1 and delta check of the ENG-11 FE-plant re-run; "
                      "the lead publishes interfaces/gnc.json v3.2 on a clean check (227 (10))",
                      "GNC: 210 m gate-delay arm before flight acceptance (227 (8)); R2 re-run after Electronics v2.11 S17"],
        note="carried here and in the session handback")


# ------------------------------------------------------------------------------------------------ checks
def self_check(d):
    hits = []

    def scan(x, path):
        pl = "/".join(path).lower()
        for pid, spec in STALE.items():
            pat, mset = spec[0], spec[1]
            pex = spec[2] if len(spec) > 2 else ()
            for m in re.finditer(pat, x):
                win = x[max(0, m.start() - 160): m.end() + 160] if mset else x[max(0, m.start() - 120): m.end() + 120]
                if mset:
                    marked_win = mset in win
                else:
                    marked_win = any(mk in win for mk in MARKERS)
                ok = ("superseded" in pl or "history" in pl or "/verbatim/" in pl or "withdrawn" in pl
                      or pl.startswith(EXEMPT_PREFIX) or any(e in "/" + pl + "/" for e in pex)
                      or x.startswith(("SUPERSEDED", "HISTORY", "WITHDRAWN")) or marked_win)
                hits.append(dict(pattern=pid, path="/".join(path), marked=bool(ok)))

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                scan(str(k), path + [f"<key>{k}"])
                walk(v, path + [str(k)])
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, path + [str(i)])
        elif isinstance(x, str):
            scan(x, path)
    walk(d, [])
    un = [h for h in hits if not h["marked"]]
    return OrderedDict(
        rule=("author's scan: every string (and key) matching a pattern of the builder's list (R01-R26: the REV-GNC-6 "
              "REJECTED texts of section (f) and the decided-state reversals of lead 227; S01-S22 of the rev2p2 builder "
              "except S06, which 227 (5) reverses) must sit under a key containing 'superseded' / 'history' / 'verbatim' / "
              "'withdrawn', a self-check record or an earlier build's change list (changes_rev2*, changes_from_v*), start "
              "with SUPERSEDED / HISTORY / WITHDRAWN, or carry a marker word "
              "within 120 characters; the reversal patterns (R13-R16, R18, R23, R25, R26) need an explicit 'rev4b' marker "
              "within 160 characters (an older marker does not count); R15 (pcf_tmax 0.5 s) does not apply to the "
              "recorded reviewer probes, which state the setting a value was flown at; pattern texts are in the builder "
              "script"),
        builder=VERSION, patterns=list(STALE), hits=len(hits), unmarked=len(un),
        unmarked_list=[dict(pattern=h["pattern"], path=h["path"]) for h in un],
        hits_by_pattern=OrderedDict((p, sum(1 for h in hits if h["pattern"] == p)) for p in STALE
                                    if any(h["pattern"] == p for h in hits)),
        hit_paths=sorted({h["path"] for h in hits if not h["path"].lower().startswith(EXEMPT_PREFIX)}))


def structural_checks(d, d0, items, cl):
    lm = d["icd_inputs_for_airframe"]["landing_mass_window_kg"]
    lm0 = d0["icd_inputs_for_airframe"]["landing_mass_window_kg"]
    it = {x["index"]: x["text"] for x in items}
    rx_l = {n: cl[n] for n in cl}
    chk = OrderedDict([
        ("X01 version v3.2", d["version"] == "v3.2"),
        ("X02 landing-mass upper bounds 16.15 kg, lower bounds unchanged",
         all((v[1] == 16.15 and v[0] == lm0["v"][k][0]) if isinstance(v, list) else v == lm0["v"][k] for k, v in lm["v"].items())),
        ("X03 airframe_first_bending_min_Hz status NOT CONSISTENT",
         "NOT CONSISTENT" in d["requirements"]["structure"]["airframe_first_bending_min_Hz"].get("status_rev4b", "")),
        ("X04 icd cg_and_length_limits status NOT CONSISTENT",
         "NOT CONSISTENT" in d["icd_inputs_for_airframe"]["cg_and_length_limits"].get("status_rev4b", "")),
        ("X05 [12] carries RV6-01, (i), (ii), RV6-14 and 227 (2); no one-sided K_s bound",
         all(s in it[12] for s in (RV6_01_MAIN, RV6_01_I_NEW, RV6_01_II_NEW, RV6_14, L227_2, L227_3))
         and not re.search(r"K_s ?>= ?100\b", it[12])),
        ("X06 [11] is the RV6-02 text + 227 (4)", it[11].startswith(RV6_02) and L227_4 in it[11]),
        ("X07 RV6 texts present in their items",
         all(s in it[k] for k, s in ((1, RV6_03), (1, RV6_04_NEW), (1, RV6_04_ADD), (3, RV6_03), (3, RV6_11), (5, RV6_05_NEW),
                                     (6, RV6_08_ADD), (13, RV6_06_NEW), (13, RV6_12), (14, RV6_07_NEW), (14, RV6_08_ADD),
                                     (15, RV6_09_I), (15, RV6_09_II), (15, RV6_09_III), (15, RV6_09_IV), (15, RV6_09_V),
                                     (0, RV6_10_PATHS)))),
        ("X08 A1 apogee_target_m 210", d["flight_profile"]["mission_plan_v3"]["v"]["A1"]["apogee_target_m"] == 210.0),
        ("X09 relight_conditions: pcf_tmax 0.8 s for W10 < 6 and mode-3 re-init",
         "pcf_tmax 0.8 s for the W10 < 6 m/s" in d["requirements"]["ignition"]["relight_conditions"]["v"]
         and "re-initialised at the Pc-invalid onset" in d["requirements"]["ignition"]["relight_conditions"]["v"]),
        ("X10 the 223 (5) J reading is not carried",
         not re.search(r"(?i)37 ?% below|near the 2\.7e-3 corner", json.dumps(
             {k: v for k, v in d.items() if k != "lead_decisions_2026-10-19"}, ensure_ascii=False))),
        ("X11 lead verbatim lines equal the CHANGELOG lines",
         all(d["lead_decisions_2026-10-19"]["rev4b_lines_204_227"]["verbatim"][str(n)] == rx_l[n] for n in LEAD_LINES)),
        ("X12 status names SIM / DERIVED / ASSUMED and no physical approval",
         all(s in d["status"] for s in ("SIM =", "DERIVED =", "ASSUMED =", "nothing here is physical approval"))),
        ("X13 RE-24 decision folded", "NOT inhibited" in it[13] and L227_7 in it[13]),
        ("X14 B-TVC-1 gate replaced", "acceptance" in d["requirements"]["gimbal"]["tvc_actuator"]["B-TVC-1"]["v"]),
        ("X15 every v3.1 top-level key kept", all(k in d for k in d0 if k != "checkpoint_rev2p2")),
    ])
    return chk


def keydiff(a, b, path="", out=None, depth=0):
    if out is None:
        out = OrderedDict(changed=[], added=[], removed=[])
    if isinstance(a, dict) and isinstance(b, dict) and depth < 7:
        for k in a:
            if k not in b:
                out["removed"].append(f"{path}/{k}")
            elif a[k] != b[k]:
                keydiff(a[k], b[k], f"{path}/{k}", out, depth + 1)
        for k in b:
            if k not in a:
                out["added"].append(f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list) and depth < 7:
        for i in range(max(len(a), len(b))):
            if i >= len(a):
                out["added"].append(f"{path}/{i}")
            elif i >= len(b):
                out["removed"].append(f"{path}/{i}")
            elif a[i] != b[i]:
                keydiff(a[i], b[i], f"{path}/{i}", out, depth + 1)
    else:
        out["changed"].append(path)
    return out


def main():
    for k, (p, h) in SRC.items():
        if sha(hubp(p)) != h:
            raise RuntimeError(f"{k}: {p} sha256/16 {sha(hubp(p))} != pinned {h}")
    review = open(hubp(SRC["review_rev_gnc_6"][0]), encoding="utf-8").read()
    for rid, txt in RV6_TEXTS.items():
        if txt not in review:
            raise RuntimeError(f"{rid}: text not verbatim in the review: {txt[:80]}")
    cl, L = changelog_lines()
    for n, q in LEAD_QUOTES:
        if q not in L[n - 1]:
            raise RuntimeError(f"line {n}: quote not verbatim: {q[:80]}")
    for q in (L227_9A, L227_9B):
        if q not in L[226]:
            raise RuntimeError(f"line 227: quote not verbatim: {q[:80]}")
    d0 = jload(V31)
    d = copy.deepcopy(d0)
    prop = jload(hubp(SRC["rev4_proposals"][0]))
    v02 = jload(hubp(SRC["rv6_v02_dcrit_duty"][0]))
    items = build_items(prop, v02)
    for it in items:
        for e in it["evidence"]:
            if sha(hubp(e["path"])) != e["sha256_16"]:
                raise RuntimeError(f"[{it['index']}] evidence {e['path']} sha256/16 {sha(hubp(e['path']))} != {e['sha256_16']}")
    n_oi, n_new = update_document(d, items, cl)
    records(d, items, n_oi, n_new, cl)
    d["rev4b_document_self_check"] = OrderedDict()
    sc = self_check(d)
    xc = structural_checks(d, d0, items, cl)
    sc["structural_checks"] = xc
    sc["structural_all_true"] = all(xc.values())
    d["rev4b_document_self_check"] = sc
    os.makedirs(OUTD, exist_ok=True)
    txt = json.dumps(d, indent=1, ensure_ascii=False)
    with open(OUT, "w") as f:
        f.write(txt)
    kd = keydiff(d0, d)
    kd = OrderedDict(builder=VERSION, a=dict(path=src("gnc_json_v3.1")),
                     b=dict(path=f"{STAGE}/v32/gnc_v3.2_rev4b.json", sha256_16=sha(OUT)),
                     n_changed=len(kd["changed"]), n_added=len(kd["added"]), n_removed=len(kd["removed"]), **kd)
    with open(KEYDIFF, "w") as f:
        json.dump(kd, f, indent=1, ensure_ascii=False)
    a_lines = json.dumps(d0, indent=1, ensure_ascii=False).split("\n")
    b_lines = txt.split("\n")
    with open(TXTDIFF, "w") as f:
        for ln in difflib.unified_diff(a_lines, b_lines, fromfile="interfaces/gnc.json (v3.1, 4f3209323b0e0ed4)",
                                       tofile=f"{STAGE}/v32/gnc_v3.2_rev4b.json", lineterm="", n=2):
            f.write(ln + "\n")
    with open(CORRLOG, "w") as f:
        json.dump(OrderedDict(builder=VERSION, source=src("rev4_proposals"), review=src("review_rev_gnc_6"),
                              rule="every op asserted: replace / insert_after anchors occur exactly once in the rev4 text",
                              n_ops=len(CORR), ops=CORR), f, indent=1, ensure_ascii=False)
    print(f"wrote {OUT} {sha(OUT)} keys {len(d)} (v3.1 {len(d0)}); open_items {n_oi} -> {n_oi + n_new}; self-check hits "
          f"{sc['hits']} unmarked {sc['unmarked']}; structural {sum(xc.values())}/{len(xc)}; keydiff changed "
          f"{kd['n_changed']} added {kd['n_added']} removed {kd['n_removed']} ({sha(KEYDIFF)}); diff {sha(TXTDIFF)}; "
          f"corrections {len(CORR)} ({sha(CORRLOG)})")
    for h in sc["unmarked_list"]:
        print("UNMARKED", h["pattern"], h["path"])
    for k, v in xc.items():
        if not v:
            print("STRUCTURAL FAIL", k)
    if sc["unmarked"] or not all(xc.values()):
        sys.exit(2)


if __name__ == "__main__":
    main()
