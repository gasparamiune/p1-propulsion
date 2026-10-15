"""m2_relight_seg44 v1.5 (GNC, 2026-10-13): cost of the VAPOUR-START FALLBACK for the A1 relight (every relight planned as a start
with a vapour-full ~44 cm3 MV-to-seat segment).

v1.1 (after the v1 run, whose 14 cases are kept unchanged): (1) GNC-added alternative (b'): planning value kept at 0.81 s with
the ECU window widened to W 1.05 s, flown as the vapour tables at plan 0.81 s (the vapour start lights LATE instead of the liquid
line lighting early; sim6 has no ECU deadline, so these runs are the W >= 1.0 s configuration); (2) the ECU abort probability at
W 0.65 s (v3) and W 1.05 s (fallback) from Combustion's false_abort_vs_W_from_E1 (the window counts from E1, the torch
confirmation): seg44 file (44 cm3), seg32.6 file (proxy for Mechanical's 34 cm3 LO bound, shifted by the volume-scaled purge
difference, DERIVED), v2p4 file (liquid); (3) expected-P decision table against the unknown probability that the segment is liquid
at RELIGHT, with the break-even probability, for v3 (plan 0.81 s, W 0.65 s), fallback (b) (plan 1.21 s, W 1.05 s) and (b')
(plan 0.81 s, W 1.05 s); an aborted relight is counted as a lost landing (ASSUMED; the abort path is not modelled); (4) case keys
<state>_p<plan> in by_base and pooled.

v1.2 (after the v1.1 run: the vapour-full start planned at 0.81 s lights late and loses as much as the liquid line planned at
1.21 s): planning-value sweep 0.91 / 1.01 / 1.11 s for the liquid line and the 44 cm3 vapour-full start on the two no-growth
bases (A1_none, A1J_none; 500 paired runs each), the P(plan) curves of both states with the 0.81 and 1.21 s points of the same
two bases, and the planning value that maximises the expected P for each probability of a liquid segment (W 1.05 s assumed for
every plan, so no ECU abort: Combustion's abort probability is 0 for W >= 1.0 s in both states).

v1.3 (REV-GNC-1 RG-01 items 1-3, after the v1.2 run whose 36 cases are kept unchanged): (1) the partially vapour-filled
segment at Combustion's GOVERNING pocket (relight_vapour_states_v2p4.json, relight_vapour_order_v2p4.json, Combustion work
folder): vapLO = 'LO|min bore_leg_refilled' V_eff 29.28 cm3 (largest LO pocket; LO pockets 26.5-29.3 cm3), vapHI = HI V_eff
38.66 cm3 (every HI sub-case); start delay = Combustion's E0->E2 given-light 5 % quantiles at W 1.05 s (no abort, so the table
is not truncated), planning values 0.81 / 0.91 / 1.01 / 1.21 s on the two no-growth bases (500 paired runs each); (2) the abort
at the window folded in per state and policy (plan, W): P_total = (1 - P_abort,s(W)) x P|lit, with Combustion's P_abort per W
and P|lit of the surviving runs, ASSUMED to be the earliest lights (the runs with the lowest start-delay draw u; bracket: the
abort independent of the outcome); (3) fault path on the 44 cm3 segment, a HYPOTHESIS until Electronics publishes it:
fp150 = fixed 1.50 s (reviewer arithmetic 0.81 + 0.69 s purge) planned 1.41 / 1.51 s; prepLO / prepHI = the vapour pocket on
the prep path (flag UNKNOWN or UNPRIMED): start delay = prep 0.56 s + the vapLO / vapHI table, planned 1.41 s (W 0.65 s, the
v2.8 prep bound 1.37 s) and 1.77 s (Combustion option b, unprimed planning 0.56 + 1.21 s); C3 = a primed (liquid) line
planned at 1.51 / 1.77 s (wrong UNPRIMED flag); (4) policy matrix and maximin over the line states.
Electronics' fault_path_v1 (work folder draft, NOT published; read only): drained 44 cm3 segment on the prep path command ->
E2 0.752 s (E0 at 0.560 s); vapour-full 44 cm3 read PRIMED: NO_IGNITION 0.696 s; vapour-full 44 cm3 on the prep path (UNKNOWN):
NO_IGNITION 1.256 s. Recorded in the output as context, not used as a flown value.

v1.4 (lead request after Electronics' REV-GNC-1 answers, CHANGELOG 2026-10-13: the ECU cannot detect saturated vapour; PRIMED
means "direct path"; SIL S11 44 cm3: minimum W to light the vapour-full segment 0.76 s on the prep path, 0.93 s on the direct
path; what-if W 1.05 s: prep lights at 1.364 s, direct at 0.971 s from RELIGHT): the P cost of planning EVERY relight as a
vapour start at the minimum lighting window, (a) prep path forced on every relight, W 0.76 s, planning value = deadline 0.56 +
0.16 + 0.76 = 1.48 s; (b) direct path, W 0.93 s, planning value 0.16 + 0.93 = 1.09 s; each paired against the liquid plan (v3
liq @ 0.81 s) and including the early-light cost of a line that is in fact liquid. Prep-path start delays: liquid = liquid
table + 0.56 s (Electronics: liquid on the prep path E0 at 0.560 s, E2 at 0.753 s); vapour = direct vapour table + 0.393 s
(DERIVED from Electronics' W 1.05 s what-if 1.364 - 0.971 s = 0.56 s prep - 0.167 s purge credit; the credit equals the
difference of the minimum windows 0.93 - 0.76 s; ASSUMED to hold for the partial pockets). Abort at the window: Combustion's
direct-path curves (seg44 0.05 s grid for the whole segment; the governing pockets from the W 1.05 s E0->E2 distribution with
an effective E0->E1 fitted to Combustion's P_abort at W 0.85 / 0.65 s); prep path: the direct curve at W + 0.167 s (ASSUMED).
The minimum windows light Electronics' single nominal trace; against Combustion's distribution they abort part of the
vapour-full starts (folded in).

v1.5 (2026-10-13, after the v1.4 run): Combustion re-issued relight_vapour_states_v2p4.json at 05:31 ("void fix"; the previous file
is kept by Combustion as relight_vapour_states_v2p4_pre_void_fix.json): the LO pockets grew from 26.5-29.3 to 33.7-35.1 cm3; the
governing LO pocket is now 'LO|min bore_leg_refilled (V_eff 35.09 cm3)' (P_abort 0.984 / 0.184 / 0 at W 0.65 / 0.85 / 1.05 s);
the HI pocket (38.66 cm3) and every other input of this script are unchanged. The v1.4 run part read the pre-fix file, its eval
part failed on the renamed key (KeyError, kept in logs/seg44_v14_eval.log). Changes: (1) the governing states are selected by
key PREFIX ('LO|min bore_leg_refilled', 'HI|min bore_leg_refilled') and the resolved key, V_eff and file hash are recorded; (2) every
case built on the LO table (vapLO, vapLOP, prepLO; 16 cases) was moved to out/relight_seg44/superseded_pre_void_fix/ with a copy of
the pre-fix states file and is re-flown on the current table; the superseded P values are reported as evidence
(superseded_pre_void_fix); (3) the W 0.93 s abort fit uses the grid window with 0 < P_abort < 1 NEAREST to 0.93 s (v1.4: the
first such window; the old LO pocket had only W 0.65 s), the other grid windows are reported as checks.

Lead request (2026-10-13): Mechanical finds that the MV-to-seat segment may hold more vapour at RELIGHT than the 0.65 s window
can purge: 34 cm3 (LO) up to the whole segment (HI), against the 19 cm3 flight requirement. Fallback under study: Combustion's
window for lighting a vapour-full ~44 cm3 segment, W 1.05 s (E1->E2 max 0.993 s plus the lift correction); planning value
0.16 (torch gate) + 1.05 = 1.21 s for every relight. Report P paired on the four A1 bases against the 0.81 s baseline of
gnc.json v3, and P when the line is in fact liquid and is planned at 1.21 s (it lights early).

Start-delay tables (the m2_relight_v28 construction: E0->E2 5 % quantiles = Combustion's E0_E3 5 % quantiles (Pc loop K15) -
(median E0_E3 - median E0_E2); valve pre-opened = the v2.8 configuration; the 6-DOF lights at the drawn delay after the relight
command, thrust rise by its own loop):
  vap44F    Combustion relight_latency_sup_seg44_v2p4.json, case 'relight_valve_preopened_full_vapour|0.125|loopK15' (segment
            44.0 cm3, whole-segment purge 0.637 s, DERIVED by Combustion from 0.31 s for 21.42 cm3 scaled with volume). The file
            is in Combustion's work folder, NOT in the hub (as relight_latency_sup_v2p4.json for gnc.json v3); its table equals
            the v2p4 full-vapour table shifted by +(0.637 - 0.31) s, i.e. the lead's alternative construction at the 0.64 s end
            of the purge range (checked in eval).
  vap44F69  the lead's alternative at the 0.69 s end of the purge range: v2p4 full-vapour table + (0.69 - 0.31) s (ASSUMED shift,
            sensitivity, A1_none and A1J_none only).
  vap34F    Mechanical's LO vapour volume 34 cm3: v2p4 full-vapour table + (0.637 x 34 / 44 - 0.31) s (DERIVED with Combustion's
            volume scaling; the vapour state at RELIGHT between LO and HI is not known).
  liq       the liquid-line table of gnc.json v3 / m2_relight_v28 (the segment primed after all, planned at 1.21 s).
Cases (500 runs each; draws seed 101 and the start-delay generator seed 20261018, as every v28 case, so each run pairs run by
run with the v28 baseline and with each other):
  v31_<state>_p1.21_<base>_k2 for state vap44F, vap34F, liq on the four A1 bases (A1_none, A1_pc, A1J_none, A1J_pc), and
  vap44F69 on A1_none and A1J_none.
Baseline: v28_liq_p0.81_<base>_k2 (gnc.json v3, out/relight_v28). Context (published v28): vapF / liq at 1.41 s.
Evaluation: P with Wilson 95 % intervals, paired exact McNemar against the baseline (lost / gained runs, two-sided binomial p),
pairing check (identical uniform start-delay draw per run), P by light-minus-plan band, failure modes, engine-on counter
against the A1 sizing cycle, usable liquid at landing; DERIVED: the share of vapour-segment relights whose Pc confirmation
would come after the v2.8 deadline (0.81 s from E0) if the fallback were not adopted.
Not modelled: the ECU deadline itself (sim6 lights at the drawn delay; every fallback table ends below 1.21 s, checked), the
vapour state distribution at RELIGHT (each state is flown on every run), Combustion's buoyant-venting check (pending).
Parts (GNC_SEG44_PARTS, default run,eval); GNC_SEG44_SPLIT k/n runs every n-th case from k (2 processes: 0/2 and 1/2).
Env: GNC_IFACE, GNC_ACT_RATE (as m2_relight_v28), GNC_SEG44_OUT (default out/relight_seg44)."""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_V28_OUT", "/home/claude/work/space/out/relight_v28")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_relight_v28 as V  # noqa: E402  (sets the v28 GNC_* defaults; base configurations and the v2p4 tables)
import m2_mc6 as M  # noqa: E402
import m2_throat_mc as TG  # noqa: E402
from gncsim import sim6 as s6  # noqa: E402

VERSION = "m2_relight_seg44 v1.5"
S = V.S
OUT = os.environ.get("GNC_SEG44_OUT", f"{S}/relight_seg44")
V28 = f"{S}/relight_v28"
PARTS = os.environ.get("GNC_SEG44_PARTS", "run,eval").split(",")
SPLIT = os.environ.get("GNC_SEG44_SPLIT", "0/1")
SEG44 = "/home/claude/work/combustion/data/v2/v2p4/relight_latency_sup_seg44_v2p4.json"   # Combustion work folder (read only)
SEG44_HUB = "/home/claude/work/shared-fallback/engine/02-combustion/data/v2/v2p4/relight_latency_sup_seg44_v2p4.json"
KEY_F = "relight_valve_preopened_full_vapour|0.125|loopK15"
TORCH_GATE = 0.16          # REQ lead / Electronics v2.8 (torch gate)
W_FALLBACK = 1.05          # REQ lead relay of Combustion (E1->E2 max 0.993 s + lift correction)
PLAN_FB = round(TORCH_GATE + W_FALLBACK, 2)   # 1.21 s (REQ lead)
PLAN_BASE = V.SEQ_WORST    # 0.81 s (gnc.json v3 baseline: torch gate 0.16 + W 0.65)
PURGE_V2P4 = 0.31          # Combustion v2p4 full-vapour purge (note of relight_latency_sup_v2p4.json)
PURGE_HI = 0.69            # REQ lead: upper end of the 0.64-0.69 s purge range for the alternative construction
SEG_CM3, LO_CM3 = 44.0, 34.0   # REQ lead relay of Mechanical (segment; LO vapour volume)
STATES_ALL = ("vap44F", "vap34F", "liq")
STATES_SENS = ("vap44F69",)
SENS_BASES = ("A1_none", "A1J_none")
STATES_LATE = ("vap44F", "vap34F")   # v1.1 alternative (b'): vapour starts flown at the 0.81 s planning value (W 1.05 s)
W_V3 = 0.65                # REQ v3 window from E1 (torch gate 0.16 + W 0.65 = 0.81 s)
SEG326 = "/home/claude/work/combustion/data/v2/v2p4/relight_latency_sup_seg32.6_v2p4.json"   # Combustion work folder (read only)
SEG326_CM3 = 32.6
P_LIQ_GRID = (0.0, 0.5, 0.8, 0.9, 0.95, 0.97, 0.99, 1.0)
SWEEP_PLANS = (0.91, 1.01, 1.11)     # v1.2 planning-value sweep (W 1.05 s)
SWEEP_STATES = ("liq", "vap44F")
# v1.3 (RG-01): Combustion's governing pockets and the 44 cm3 fault-path bracket
STATES_FILE = "/home/claude/work/combustion/data/v2/v2p4/relight_vapour_states_v2p4.json"   # Combustion work folder (read only)
ORDER_FILE = "/home/claude/work/combustion/data/v2/v2p4/relight_vapour_order_v2p4.json"     # Combustion work folder (read only)
EL_FAULT = "/home/claude/work/electronics/results/fault_path_v1.json"                         # Electronics work folder draft (read only)
GOV_STATES = {"vapLO": "LO|min bore_leg_refilled", "vapHI": "HI|min bore_leg_refilled"}   # v1.5: key PREFIXES (V_eff in the key)
SUPERSEDED = os.path.join(OUT, "superseded_pre_void_fix")    # v1.5: LO-table cases flown on the pre-fix states file (evidence)
GOV_PLANS = (0.81, 0.91, 1.01, 1.21)
PREP_S = V.PREP_RERUN       # 0.56 s (DERIVED 1.37 - 0.81; Electronics fault_path_v1 draft: E0 at 0.560 s on the prep path)
FP_FIXED = 1.50             # HYPOTHESIS (reviewer RG-01: 0.81 + purge 0.69 s)
FP_CASES = (("fp150", 1.41), ("fp150", 1.51), ("prepLO", 1.41), ("prepLO", 1.77), ("prepHI", 1.41), ("prepHI", 1.77),
            ("liq", 1.51), ("liq", 1.77))
W_GRID = (0.65, 0.85, 1.05)
POLICIES = (("v3: plan 0.81, W 0.65", 0.81, 0.65), ("plan 0.91, W 0.85", 0.91, 0.85), ("plan 1.01, W 0.85", 1.01, 0.85),
            ("(b'): plan 0.81, W 1.05", 0.81, 1.05), ("plan 0.91, W 1.05", 0.91, 1.05), ("plan 1.01, W 1.05", 1.01, 1.05),
            ("(b): plan 1.21, W 1.05", 1.21, 1.05))
POLICY_STATES = ("liq", "vapLO", "vapHI", "vap44F")
# v1.4: minimum lighting windows (Electronics SIL S11, 44 cm3, single nominal trace, plant ASSUMED; CHANGELOG 2026-10-13)
W_PREP_MIN, W_DIRECT_MIN = 0.76, 0.93          # REQ relay of Electronics
PREP_CREDIT = round(W_DIRECT_MIN - W_PREP_MIN, 3)  # 0.17 s DERIVED purge credit of the prep path (0.926 - 0.759 in the SIL traces)
PREP_VAP_SHIFT = 0.393                          # DERIVED Electronics what-if W 1.05 s: prep 1.364 s - direct 0.971 s
PLAN_PREP = round(PREP_S + TORCH_GATE + W_PREP_MIN, 2)    # 1.48 s
PLAN_DIRECT = round(TORCH_GATE + W_DIRECT_MIN, 2)        # 1.09 s
# v1.5: prep path at the window equivalent to Combustion's zero-abort direct window (W 1.05 - 0.17 s credit = 0.88 s; ASSUMED transfer)
W_PREP_ZERO = round(W_FALLBACK - PREP_CREDIT, 2)          # 0.88 s
PLAN_PREP_ZERO = round(PREP_S + TORCH_GATE + W_PREP_ZERO, 2)   # 1.60 s
OPT_STATES_DIRECT = ("liq", "vap44F", "vapLO", "vapHI")
OPT_STATES_PREP = ("liqP", "vap44FP", "vapLOP", "vapHIP")
GROWTH_BASES = ("A1_pc", "A1J_pc")
OPT_GROWTH = (("liq", PLAN_DIRECT), ("vap44F", PLAN_DIRECT), ("liqP", PLAN_PREP), ("vap44FP", PLAN_PREP))
PRIORS = {"LO only": (0.0, 1.0, 0.0, 0.0), "HI only": (0.0, 0.0, 1.0, 0.0), "LO/HI 50/50": (0.0, 0.5, 0.5, 0.0),
          "liquid 1/3, LO 1/3, HI 1/3": (1 / 3, 1 / 3, 1 / 3, 0.0), "liquid 0.5, LO 0.25, HI 0.25": (0.5, 0.25, 0.25, 0.0),
          "whole segment 44 cm3 only": (0.0, 0.0, 0.0, 1.0)}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def gov_key(ds, prefix):
    """v1.5: the unique state key of the Combustion states file that starts with the governing prefix."""
    ks = [k for k in ds["states"] if k.startswith(prefix + " ")]
    if len(ks) != 1:
        raise KeyError(f"governing prefix {prefix!r}: {len(ks)} matches in the states file")
    return ks[0]


def qcdf(q, x):
    """P(delay <= x) for the piecewise-linear 21-point quantile table q (0, 5, ..., 100 %)."""
    return float(np.interp(x, q, np.linspace(0.0, 1.0, len(q)), left=0.0, right=1.0))


def tables():
    tv = V.e0e2_tables()                       # v2p4: liq, vapU, vapF (0.31 s purge)
    src = SEG44_HUB if os.path.isfile(SEG44_HUB) else SEG44
    d = json.load(open(src))
    c = d["cases"][KEY_F]
    q3 = np.array(c["E0_E3_quantiles_5pct_s"], dtype=float)
    off = c["E0_E3_s"]["median"] - c["E0_E2_s"]["median"]
    q44 = q3 - off
    tp = float(d["t_purge_segment_s"])
    vf = np.array(tv["vapF"]["quantiles_5pct_s"], dtype=float)
    t = dict(liq=list(tv["liq"]["quantiles_5pct_s"]), vap44F=q44.tolist(), vap44F69=(vf + (PURGE_HI - PURGE_V2P4)).tolist(),
             vap34F=(vf + (tp * LO_CM3 / SEG_CM3 - PURGE_V2P4)).tolist())
    # v1.3: Combustion's governing pockets (W 1.05 s given-light quantiles: P_abort 0, so not truncated) and the fault bracket
    ds = json.load(open(STATES_FILE))
    gov = {}
    for lab, pre in GOV_STATES.items():
        key = gov_key(ds, pre)
        x = ds["states"][key]
        q = np.array(x["W1.05"]["E0_E2_given_light_quantiles_5pct_s"], dtype=float)
        t[lab] = q.tolist()
        t["prep" + lab[3:]] = (q + PREP_S).tolist()
        gov[lab] = dict(key=key, V_eff_cm3=x.get("V_eff_cm3"), P_abort={W: x[W]["P_abort"] for W in ("W0.35", "W0.65", "W0.85", "W1.05")},
                        E0_E2_given_light_W105_s=x["W1.05"]["E0_E2_given_light_s"])
    t["fp150"] = [FP_FIXED] * 21
    # v1.4: prep path (liquid: + 0.56 s; vapour: + 0.393 s, Electronics-derived purge credit)
    t["liqP"] = (np.array(t["liq"]) + PREP_S).tolist()
    for k in ("vap44F", "vapLO", "vapHI"):
        t[k + "P"] = (np.array(t[k]) + PREP_VAP_SHIFT).tolist()
    ql = np.array(ds["states"]["liquid (primed, no pocket)"]["W1.05"]["E0_E2_given_light_quantiles_5pct_s"], dtype=float)
    dl = np.abs(ql - np.array(t["liq"]))
    info = dict(
        seg44_file=dict(path=src, in_hub=src == SEG44_HUB, sha256_16=sha16(src), version=d.get("version"), date=d.get("date"),
                        segment_cm3=d.get("segment_cm3"), t_purge_segment_s=tp, case=KEY_F,
                        E0_E1_max_s=c["E0_E1_s"]["max"], E1_E2_median_max_s=[c["E1_E2_s"]["median"], c["E1_E2_s"]["max"]],
                        E0_E2_given_s={k: c["E0_E2_s"][k] for k in ("median", "p95", "p99", "max")},
                        constructed_p95_max_s=[float(q44[19]), float(q44[20])]),
        v2p4_file=dict(path=V.RC03, sha256_16=sha16(V.RC03)),
        check_seg44_equals_v2p4_full_shifted=dict(shift_s=tp - PURGE_V2P4,
                                                   max_abs_diff_s=float(np.max(np.abs(q44 - (vf + tp - PURGE_V2P4))))),
        states_file=dict(path=STATES_FILE, in_hub=False, sha256_16=sha16(STATES_FILE), version=ds.get("version"), date=ds.get("date"),
                         tag=ds.get("tag"), purge_s_per_cm3=ds.get("purge_s_per_cm3"), governing=gov,
                         check_liquid_table_vs_gnc_v3=dict(max_abs_diff_s=float(dl.max()), max_abs_diff_above_q5_s=float(dl[1:].max()),
                                                           note="Combustion's liquid W1.05 table vs the v3 constructed liquid table")),
        order_file=dict(path=ORDER_FILE, sha256_16=sha16(ORDER_FILE)),
        construction={"vap44F": "Combustion seg44 table (E0_E3 quantiles - (median E0_E3 - median E0_E2))",
                      "vap44F69": f"v2p4 full-vapour table + ({PURGE_HI} - {PURGE_V2P4}) s (lead's alternative, 0.69 s purge)",
                      "vap34F": f"v2p4 full-vapour table + ({tp:.4f} x {LO_CM3:g}/{SEG_CM3:g} - {PURGE_V2P4}) s",
                      "liq": "v2p4 liquid-line table (gnc.json v3)",
                      "vapLO": f"Combustion relight_vapour_states_v2p4 '{gov['vapLO']['key']}' W1.05 E0->E2 given-light quantiles",
                      "vapHI": f"Combustion relight_vapour_states_v2p4 '{gov['vapHI']['key']}' W1.05 E0->E2 given-light quantiles",
                      "prepLO": f"vapLO + prep {PREP_S:.2f} s (vapour pocket on the prep path; HYPOTHESIS)",
                      "prepHI": f"vapHI + prep {PREP_S:.2f} s (vapour pocket on the prep path; HYPOTHESIS)",
                      "fp150": f"fixed {FP_FIXED:.2f} s (reviewer arithmetic 0.81 + 0.69 s; HYPOTHESIS)",
                      "liqP": f"liq + prep {PREP_S:.2f} s (prep path forced; Electronics liquid prep E2 0.753 s)",
                      "vap44FP": f"vap44F + {PREP_VAP_SHIFT} s (prep path; DERIVED Electronics what-if 1.364 - 0.971 s)",
                      "vapLOP": f"vapLO + {PREP_VAP_SHIFT} s (prep path; credit ASSUMED to transfer)",
                      "vapHIP": f"vapHI + {PREP_VAP_SHIFT} s (prep path; credit ASSUMED to transfer)"},
        tables_E0E2_quantiles_5pct_s={k: [round(x, 4) for x in v] for k, v in t.items()},
        max_below_plan_fb=all(max(t[k]) < PLAN_FB for k in ("liq", "vap44F", "vap44F69", "vap34F", "vapLO", "vapHI")),
        share_E0E2_after_0p81s_from_E0={k: 1.0 - qcdf(v, PLAN_BASE) for k, v in t.items()},
        share_after_fallback_deadline={k: 1.0 - qcdf(v, PLAN_FB) for k, v in t.items()},
        note_shares=("E0-referenced shares of the constructed E0->E2 tables (secondary check); the ECU window counts from E1 "
                     "(torch confirmation): the governing abort probabilities are ecu_abort_probability (Combustion)"))
    return t, info


def case_over(base, q, plan):
    o = V.base_over(base)
    o.update(t_ign_q=tuple(float(x) for x in q), t_ign_add=0.0, t_ign_est=float(plan))
    return o


def cname(state, base, plan=PLAN_FB):
    return f"v31_{state}_p{plan:.2f}_{base}_k2"


def case_list():
    """(state, plan, bases) of every case: fallback (b) at 1.21 s, sensitivity, and the v1.1 alternative (b') at 0.81 s."""
    return ([(st, PLAN_FB, V.BASES) for st in STATES_ALL] + [(st, PLAN_FB, SENS_BASES) for st in STATES_SENS] +
            [(st, PLAN_BASE, V.BASES) for st in STATES_LATE] + [(st, PLAN_BASE, SENS_BASES) for st in STATES_SENS] +
            [(st, pl, SENS_BASES) for pl in SWEEP_PLANS for st in SWEEP_STATES] +
            [(st, pl, SENS_BASES) for st in GOV_STATES for pl in GOV_PLANS] +
            [(st, pl, SENS_BASES) for st, pl in FP_CASES] +
            [(st, PLAN_DIRECT, SENS_BASES) for st in OPT_STATES_DIRECT] + [(st, PLAN_PREP, SENS_BASES) for st in OPT_STATES_PREP] +
            [(st, PLAN_PREP_ZERO, SENS_BASES) for st in OPT_STATES_PREP] +
            [(st, pl, GROWTH_BASES) for st, pl in OPT_GROWTH])


def all_cases(t):
    cs = {}
    for st, plan, bases in case_list():
        for base in bases:
            if (st in OPT_STATES_DIRECT and abs(plan - PLAN_DIRECT) < 1e-9) or st in OPT_STATES_PREP:
                what = ("v1.4 option (b-min): direct path, W 0.93 s, plan = deadline" if st in OPT_STATES_DIRECT else
                        "v1.4 option (a-min): prep path forced, W 0.76 s, plan = deadline" if abs(plan - PLAN_PREP) < 1e-9 else
                        "v1.5 option (a-0): prep path forced, W 0.88 s (direct-equivalent 1.05 s), plan = deadline")
            elif st in GOV_STATES:
                what = "RG-01 governing pocket (Combustion v2p4), W 1.05 s table"
            elif st in ("fp150", "prepLO", "prepHI") or (st == "liq" and plan in (1.51, 1.77)):
                what = "RG-01 fault-path bracket on the 44 cm3 segment (HYPOTHESIS)" if st != "liq" else "RG-01 C3: primed line, wrong UNPRIMED flag"
            else:
                what = ("vapour-start fallback (b)" if plan == PLAN_FB else "alternative (b'): plan kept, W 1.05 s" if plan == PLAN_BASE
                        else "planning-value sweep, W 1.05 s") + (" sensitivity" if st in STATES_SENS else "")
            cs[cname(st, base, plan)] = (case_over(base, t[st], plan),
                                         f"{base} k_est_asc 2, {what}: planning value {plan:.2f} s, start delay ~ {st}")
    return cs


def abort_tables():
    """ECU abort probability of a relight that would light, against the window W counted from E1 (Combustion
    false_abort_vs_W_from_E1, pre-opened valve, Pc loop K15), at the v3 window and the fallback window."""
    def curve(path, key):
        c = json.load(open(path))["cases"][key]["false_abort_vs_W_from_E1"]
        w = np.array(sorted(float(k) for k in c))
        return w, np.array([c[f"{x:.2f}"] for x in w])

    out = {}
    w44, a44 = curve(SEG44_HUB if os.path.isfile(SEG44_HUB) else SEG44, KEY_F)
    w32, a32 = curve(SEG326, KEY_F)
    wl, al = curve(V.RC03, "relight_valve_preopened_liquid|0.125|loopK15")
    tp44 = float(json.load(open(SEG44))["t_purge_segment_s"])
    dsh = tp44 * (LO_CM3 - SEG326_CM3) / SEG_CM3     # purge-time difference 34 vs 32.6 cm3 (Combustion's linear volume scaling)
    for lab, (w, a, sh) in dict(vap44F=(w44, a44, 0.0), vap34F=(w32, a32, dsh), liq=(wl, al, 0.0)).items():
        out[lab] = {f"W{W:.2f}": float(np.interp(W - sh, w, a)) for W in W_GRID}
    # v1.4: the whole-segment curves also at the minimum lighting window (0.05 s grid, linear)
    for lab, (w, a, sh) in dict(vap44F=(w44, a44, 0.0), vap34F=(w32, a32, dsh), liq=(wl, al, 0.0)).items():
        out[lab][f"W{W_DIRECT_MIN:.2f}"] = float(np.interp(W_DIRECT_MIN - sh, w, a))
    ds = json.load(open(STATES_FILE))     # v1.3: governing pockets, Combustion's P_abort per W (no interpolation needed)
    fit = {}
    keys = {}
    for lab, pre in GOV_STATES.items():
        key = keys[lab] = gov_key(ds, pre)
        out[lab] = {f"W{W:.2f}": float(ds["states"][key][f"W{W:.2f}"]["P_abort"]) for W in W_GRID}
        # v1.4: P_abort at W 0.93 s from the W 1.05 s (unconditional) E0->E2 distribution with an effective E0->E1 t1 fitted
        # to Combustion's P_abort at the grid window where 0 < P_abort < 1 (DERIVED; checked at the other grid windows)
        q = np.array(ds["states"][key]["W1.05"]["E0_E2_given_light_quantiles_5pct_s"], dtype=float)
        ref = [W for W in W_GRID if 0.0 < out[lab][f"W{W:.2f}"] < 1.0]
        Wr = min(ref, key=lambda W: abs(W - W_DIRECT_MIN))      # v1.5: nearest interior grid window (v1.4: the first)
        ar = out[lab][f"W{Wr:.2f}"]
        t1 = float(np.interp(1.0 - ar, np.linspace(0.0, 1.0, 21), q)) - Wr
        pa = lambda W: 1.0 - qcdf(q, t1 + W)   # noqa: E731
        out[lab][f"W{W_DIRECT_MIN:.2f}"] = float(pa(W_DIRECT_MIN))
        fit[lab] = dict(ref_W=Wr, ref_P_abort=ar, t1_eff_s=t1,
                        check={f"W{W:.2f}": dict(combustion=out[lab][f"W{W:.2f}"], cdf_fit=float(pa(W))) for W in W_GRID})
    out["liq_states_file"] = {f"W{W:.2f}": float(ds["states"]["liquid (primed, no pocket)"][f"W{W:.2f}"]["P_abort"]) for W in W_GRID}
    out["liq_states_file"][f"W{W_DIRECT_MIN:.2f}"] = 0.0
    out["fit_W093"] = fit
    # prep path at W 0.76 s = the direct curve at W + PREP_CREDIT (ASSUMED transfer of Electronics' purge credit)
    out["prep_equivalent_direct_W_s"] = round(W_PREP_MIN + PREP_CREDIT, 3)
    out["source"] = dict(
        vap44F=f"{SEG44} (sha256/16 {sha16(SEG44)}) {KEY_F}",
        vap34F=f"{SEG326} (sha256/16 {sha16(SEG326)}) {KEY_F}, curve shifted by +{dsh:.4f} s (34 vs 32.6 cm3, DERIVED)",
        liq=f"{V.RC03} relight_valve_preopened_liquid|0.125|loopK15",
        vapLO=f"{STATES_FILE} (sha256/16 {sha16(STATES_FILE)}) '{keys['vapLO']}' P_abort",
        vapHI=f"{STATES_FILE} (sha256/16 {sha16(STATES_FILE)}) '{keys['vapHI']}' P_abort",
        rule="linear interpolation on Combustion's 0.05 s grid; W counted from E1 (torch confirmation)")
    return out


def run(cs):
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    names = sorted(cs, key=lambda c: (0 if (f"_p{PLAN_PREP:.2f}_" in c or f"_p{PLAN_DIRECT:.2f}_" in c or f"_p{PLAN_PREP_ZERO:.2f}_" in c) else
                                      1 if ("_vapLO_" in c or "_vapHI_" in c) else 2, c))[k::n]   # v1.4 options first
    for name in names:
        over, note = cs[name]
        p = os.path.join(OUT, f"mc6_runs_{name}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_SEG44_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        o, rows = M.run_case(name, over, note)
        gate = "m2_mc6.run_case (nominal sizing gate passed)"
        if not rows:
            print(f"{name}: run_case nominal sizing gate did not close; fixed-load Monte Carlo (same draws)", flush=True)
            o, rows = V.run_case_fixed(name, over, note)
            gate = "m2_relight_v28.run_case_fixed (nominal sizing gate skipped: did not close)"
        M.write_csv(p, rows)
        keep = {kk: o.get(kk) for kk in ("case", "note", "m_n2o_mc_kg", "m_liftoff_kg", "cpu_s", "sim")}
        keep["runner"] = gate
        keep["fail_modes"] = o["summary"]["fail_modes"]
        keep["config"] = {kk: over.get(kk) for kk in ("t_ign_est", "t_ign_add", "throat_g_band", "throat_jref", "k_est_asc")}
        keep["t_ign_q"] = list(over.get("t_ign_q") or [])
        with open(os.path.join(OUT, f"case_{name}.json"), "w") as f:
            json.dump(keep, f, indent=1, default=float)
        print(f"{name}: P {np.mean([r['ok'] for r in rows]):.3f} fails {o['summary']['fail_modes']} ({o.get('cpu_s', 0):.0f} s)",
              flush=True)


def case_stats(rr, cj, sz):
    st = TG.stats(rr, cj["m_n2o_mc_kg"], None)
    plan = cj["config"]["t_ign_est"]
    sd = np.array([float(r["start_delay"]) for r in rr])
    ok = np.array([float(r["ok"]) for r in rr]) > 0.5
    err = sd - plan
    st.update(fail_modes=cj["fail_modes"], planning_value_s=plan, runner=cj.get("runner"),
              start_delay_min_p50_max_s=[float(sd.min()), float(np.median(sd)), float(sd.max())],
              light_minus_plan_s_min_p50_max=[float(err.min()), float(np.median(err)), float(err.max())])
    for lab, m in (("early_gt_0.75s", err < -0.75), ("early_0.5_0.75s", (err >= -0.75) & (err < -0.5)),
                   ("early_0.25_0.5s", (err >= -0.5) & (err < -0.25)), ("within_0.25s", np.abs(err) <= 0.25),
                   ("late_gt_0.25s", err > 0.25)):
        st.setdefault("P_by_light_minus_plan", {})[lab] = dict(n=int(m.sum()), P=float(ok[m].mean()) if m.any() else None)
    bt = np.array([float(r["burn_time"]) for r in rr])
    st["engine_on_counter_p50_p99_max_s"] = [float(np.percentile(bt, 50)), float(np.percentile(bt, 99)), float(bt.max())]
    st["engine_on_counter_over_a1_sizing"] = dict(sizing_counter_s=sz, n_over=int(np.sum(bt > sz)))
    hi = np.array([float(r["h_ign"]) for r in rr])
    st["relight_command_height_p01_p50_p99_m"] = [float(np.percentile(hi, 1)), float(np.percentile(hi, 50)),
                                                  float(np.percentile(hi, 99))]
    return st


def pairing_check(a, b):
    ua = np.array([float(r["t_ign_u"]) for r in a])
    ub = np.array([float(r["t_ign_u"]) for r in b])
    da = [r["wind"] for r in a] == [r["wind"] for r in b]
    return dict(same_uniform_start_draw=bool(np.array_equal(ua, ub)), same_wind_draw=bool(da), n=len(a))


def decision_table(pooled, ab):
    """expected P against p = probability that the segment is liquid at RELIGHT (the vapour state otherwise), pooled P of the
    four bases (2000 paired runs per entry); an aborted relight = lost landing (ASSUMED, abort path not modelled)."""
    Pb = pooled["baseline"]["P"]
    out = dict(rule=("P_v3 = p P(liq @0.81) + (1 - p) (1 - a_W0.65) P(vap @0.81); P_b = p P(liq @1.21) + (1 - p) P(vap @1.21); "
                     "P_b' = p P(liq @0.81) + (1 - p) (1 - a_W1.05) P(vap @0.81); a = Combustion ECU abort probability at the "
                     "window (from E1); the surviving v3 vapour runs are approximated by the (b') runs (ASSUMED: the abort "
                     "removes runs independently of their outcome)"), by_state={})
    for st in STATES_LATE:
        k21, k81 = f"{st}_p{PLAN_FB:.2f}", f"{st}_p{PLAN_BASE:.2f}"
        if k21 not in pooled or k81 not in pooled or "liq_p1.21" not in pooled:
            continue
        Pl21, Pv21, Pv81 = pooled["liq_p1.21"]["P"], pooled[k21]["P"], pooled[k81]["P"]
        a65, a105 = ab[st][f"W{W_V3:.2f}"], ab[st][f"W{W_FALLBACK:.2f}"]
        rows = []
        for p in P_LIQ_GRID:
            rows.append(dict(p_liquid=p, P_v3=p * Pb + (1 - p) * (1 - a65) * Pv81, P_fallback_b=p * Pl21 + (1 - p) * Pv21,
                             P_alt_bprime=p * Pb + (1 - p) * (1 - a105) * Pv81))
        num = Pv21 - (1 - a65) * Pv81
        den = (Pb - Pl21) + num
        out["by_state"][st] = dict(abort_W065=a65, abort_W105=a105, P_liq_081=Pb, P_liq_121=Pl21, P_vap_121=Pv21, P_vap_081=Pv81,
                                   break_even_p_liquid_v3_vs_b=(num / den if den > 0 else None), table=rows)
    return out


def plan_curve(by_base, ab):
    """P against the planning value for the liquid line and the 44 cm3 vapour-full start on the two no-growth bases (1000 paired
    runs per point), and the expected-P optimum for each probability of a liquid segment (W 1.05 s: no ECU abort)."""
    plans = sorted(set((PLAN_BASE, PLAN_FB) + SWEEP_PLANS))
    cur = {}
    for st in SWEEP_STATES:
        for pl in plans:
            oks = []
            for base in SENS_BASES:
                key = "baseline" if (st == "liq" and pl == PLAN_BASE) else f"{st}_p{pl:.2f}"
                x = by_base.get(base, {}).get(key)
                if x is None:
                    break
                oks.append((x["P"], x["n"]))
            if len(oks) == len(SENS_BASES):
                k = sum(p * n for p, n in oks)
                n = sum(n for _, n in oks)
                cur.setdefault(st, {})[f"{pl:.2f}"] = dict(P=k / n, ci95=TG.wilson(int(round(k)), n), n=n)
    best = []
    if all(st in cur and len(cur[st]) == len(plans) for st in SWEEP_STATES):
        for p in P_LIQ_GRID:
            ev = {f"{pl:.2f}": p * cur["liq"][f"{pl:.2f}"]["P"] + (1 - p) * (1 - ab["vap44F"][f"W{W_FALLBACK:.2f}"]) *
                  cur["vap44F"][f"{pl:.2f}"]["P"] for pl in plans}
            kb = max(ev, key=ev.get)
            best.append(dict(p_liquid=p, best_plan_s=float(kb), P_best=ev[kb], P_by_plan=ev))
        mm = {f"{pl:.2f}": min(cur["liq"][f"{pl:.2f}"]["P"], cur["vap44F"][f"{pl:.2f}"]["P"]) for pl in plans}
        km = max(mm, key=mm.get)
    else:
        mm, km = {}, None
    # paired exact McNemar on the two bases: every point against the state's reference (liquid: the v3 0.81 s baseline runs;
    # vapour-full: the 1.21 s fallback runs) and the 0.91 s point against both references
    from scipy.stats import binomtest

    def ok_of(st, pl, base):
        if st == "liq" and abs(pl - PLAN_BASE) < 1e-9:
            rr = rows_csv(os.path.join(V28, f"mc6_runs_v28_liq_p{PLAN_BASE:.2f}_{base}_k2_v28.csv"))
        else:
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{cname(st, base, pl)}.csv"))
        return None if rr is None else np.array([float(r["ok"]) for r in rr]) > 0.5

    def mcn(a, b):
        lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
        return dict(lost=lost, gained=gained, p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0,
                    dP=float(b.mean() - a.mean()))

    paired = {}
    refs = dict(liq=PLAN_BASE, vap44F=PLAN_FB)
    for st in SWEEP_STATES:
        for pl in plans:
            for rs, rp in refs.items():
                if rs != st:
                    continue
                if abs(pl - rp) < 1e-9:
                    continue
                a = [ok_of(st, rp, b) for b in SENS_BASES]
                b = [ok_of(st, pl, b) for b in SENS_BASES]
                if any(x is None for x in a + b):
                    continue
                paired[f"{st}: {pl:.2f} vs {rp:.2f}"] = mcn(np.concatenate(a), np.concatenate(b))
    return dict(bases=list(SENS_BASES), W_s=W_FALLBACK, curve=cur, expected_P_best_plan=best, maximin_plan_s=(float(km) if km else None),
                min_over_states_by_plan=mm, paired_vs_state_reference=paired,
                note="pooled over A1_none and A1J_none (no throat growth); 0.81 s liquid = the v3 baseline runs; W 1.05 s for all")


def _runs(st, pl, bases=SENS_BASES):
    """ok and start-delay uniform draw u of a state / planning value, concatenated over the bases (None if missing)."""
    oks, us = [], []
    for base in bases:
        if st == "liq" and abs(pl - PLAN_BASE) < 1e-9:
            rr = rows_csv(os.path.join(V28, f"mc6_runs_v28_liq_p{PLAN_BASE:.2f}_{base}_k2_v28.csv"))
        else:
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{cname(st, base, pl)}.csv"))
        if not rr:
            return None, None
        oks.append(np.array([float(r["ok"]) for r in rr]) > 0.5)
        us.append(np.array([float(r["t_ign_u"]) for r in rr]))
    return np.concatenate(oks), np.concatenate(us)


def p_total(ok, u, a):
    """P with the ECU abort at the window folded in: survivors ASSUMED to be the earliest lights (lowest u; the start delay is
    monotone in u), bracket: abort independent of the outcome. Returns dict."""
    n = len(ok)
    if a >= 1.0 - 1e-12:
        # v1.5: P_lit_all kept for the report (the v1.5 first eval failed on the missing key at prepHI @ 1.41 s, abort 1.0)
        return dict(P_abort=a, P_lit_late=None, P_lit_all=float(ok.mean()), P_total=0.0, P_total_indep=0.0, n=n, n_surv=0)
    surv = u <= np.quantile(u, 1.0 - a) if a > 0 else np.ones(n, bool)
    pl = float(ok[surv].mean())
    k = int(ok[surv].sum())
    lo, hi = TG.wilson(k, int(surv.sum()))
    return dict(P_abort=a, P_lit_late=pl, P_lit_all=float(ok.mean()), P_total=(1 - a) * pl, P_total_ci95=[(1 - a) * lo, (1 - a) * hi],
                P_total_indep=(1 - a) * float(ok.mean()), n=n, n_surv=int(surv.sum()))


def gov_eval(ab):
    """RG-01 item 3: policy (plan, W) x line state matrix on the two no-growth bases (1000 paired runs per entry), the abort at
    W folded in, maximin and expected P for a set of priors over the line state at RELIGHT."""
    mat, missing = {}, []
    for lab, pl, W in POLICIES:
        row = {}
        for st in POLICY_STATES:
            ok, u = _runs(st, pl)
            if ok is None:
                missing.append(f"{st}@{pl:.2f}")
                continue
            a = ab[st][f"W{W:.2f}"] if st != "liq" else ab["liq_states_file"][f"W{W:.2f}"]
            row[st] = p_total(ok, u, a)
        mat[lab] = dict(plan_s=pl, W_s=W, by_state=row)
    out = dict(rule=("P_total,s = (1 - P_abort,s(W)) x P|lit,s(plan); P_abort from Combustion (W from E1); P|lit from the surviving "
                     "runs, ASSUMED to be the earliest lights (lowest start-delay draw u); P_total_indep = abort independent of "
                     "outcome (bracket); no retry; p_nl,ign = 0 here (RG-02 carries it)"),
               bases=list(SENS_BASES), states=list(POLICY_STATES), matrix=mat, missing=missing)
    if missing:
        return out
    worst = {lab: min(v["by_state"][st]["P_total"] for st in ("liq", "vapLO", "vapHI")) for lab, v in mat.items()}
    worst4 = {lab: min(v["by_state"][st]["P_total"] for st in POLICY_STATES) for lab, v in mat.items()}
    out["maximin_over_liq_LO_HI"] = dict(worst_P=worst, best=max(worst, key=worst.get))
    out["maximin_over_all_four"] = dict(worst_P=worst4, best=max(worst4, key=worst4.get))
    ev = {}
    for pn, pi in PRIORS.items():
        e = {lab: sum(w * v["by_state"][st]["P_total"] for w, st in zip(pi, POLICY_STATES)) for lab, v in mat.items()}
        ev[pn] = dict(prior=dict(zip(POLICY_STATES, pi)), expected_P=e, best=max(e, key=e.get))
    out["expected_P_by_prior"] = ev
    # paired: each vapour state, plan 0.91 / 1.01 / 1.21 vs 0.81 (P|lit, W 1.05) and 1.01 vs 0.91
    from scipy.stats import binomtest
    pr = {}
    for st in ("vapLO", "vapHI"):
        for a_, b_ in ((0.81, 0.91), (0.81, 1.01), (0.81, 1.21), (0.91, 1.01), (1.01, 1.21)):
            A, _ = _runs(st, a_)
            B, _ = _runs(st, b_)
            lost, gained = int(np.sum(A & ~B)), int(np.sum(~A & B))
            pr[f"{st}: {b_:.2f} vs {a_:.2f}"] = dict(P_a=float(A.mean()), P_b=float(B.mean()), lost=lost, gained=gained,
                                                     p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0)
    out["paired_P_lit"] = pr
    return out


def opt_eval(ab):
    """v1.4: options (a-min) prep path W 0.76 s plan 1.48 s and (b-min) direct path W 0.93 s plan 1.09 s, every relight planned as
    a vapour start; per line state P|lit (paired against the liquid plan, v3 liq @ 0.81 s, same draws), abort at the window folded
    in (survivors = earliest lights, ASSUMED; bracket: independent), comparators from the governing matrix; 2 no-growth bases
    (1000 runs) and, for liquid and the whole 44 cm3 segment, the four bases (2000 runs)."""
    from scipy.stats import binomtest

    def mcn(A, B):
        lost, gained = int(np.sum(A & ~B)), int(np.sum(~A & B))
        return dict(P_ref=float(A.mean()), P=float(B.mean()), lost=lost, gained=gained, dP=float(B.mean() - A.mean()),
                    p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0)

    Wk = f"W{W_DIRECT_MIN:.2f}"
    opts = {"(a-min) prep path, W 0.76 s, plan 1.48 s": (PLAN_PREP, dict(liq="liqP", vapLO="vapLOP", vapHI="vapHIP", vap44F="vap44FP")),
            "(b-min) direct path, W 0.93 s, plan 1.09 s": (PLAN_DIRECT, dict(liq="liq", vapLO="vapLO", vapHI="vapHI", vap44F="vap44F")),
            "(a-0) prep path, W 0.88 s, plan 1.60 s": (PLAN_PREP_ZERO, dict(liq="liqP", vapLO="vapLOP", vapHI="vapHIP", vap44F="vap44FP"))}
    wkey = {PLAN_PREP: Wk, PLAN_DIRECT: Wk, PLAN_PREP_ZERO: f"W{W_FALLBACK:.2f}"}   # v1.5: (a-0) = direct-equivalent W 1.05 s
    ref_ok, _ = _runs("liq", PLAN_BASE)
    out = dict(rule=("P_total,s = (1 - P_abort,s) x P|lit,s; P_abort at W 0.93 s direct (prep: W 0.76 + 0.17 s credit = the same "
                     "direct-equivalent window); paired: P|lit of each state against the liquid line planned at 0.81 s (v3)"),
               abort_at_min_window={st: (ab[st][Wk] if st != "liq" else 0.0) for st in POLICY_STATES}, options={})
    for lab, (pl, mp) in opts.items():
        row = {}
        for st, cs in mp.items():
            ok, u = _runs(cs, pl)
            if ok is None:
                row[st] = None
                continue
            a = ab[st][wkey[pl]] if st != "liq" else 0.0
            x = p_total(ok, u, a)
            x["case_state"] = cs
            x["paired_P_lit_vs_liquid_plan"] = mcn(ref_ok, ok) if ref_ok is not None else None
            x["light_minus_plan_p50_s"] = None
            row[st] = x
        g4 = {}
        for st, cs in (("liq", mp["liq"]), ("vap44F", mp["vap44F"])):
            ok4, u4 = _runs(cs, pl, tuple(SENS_BASES) + tuple(GROWTH_BASES))
            r4, _ = _runs("liq", PLAN_BASE, tuple(SENS_BASES) + tuple(GROWTH_BASES))
            if ok4 is not None and r4 is not None:
                a = ab[st][wkey[pl]] if st != "liq" else 0.0
                g4[st] = dict(p_total(ok4, u4, a), paired_P_lit_vs_liquid_plan=mcn(r4, ok4), bases=list(SENS_BASES) + list(GROWTH_BASES))
        out["options"][lab] = dict(plan_s=pl, by_state=row, four_bases=g4)
    return out


def fault_eval(ab):
    """RG-01 item 1 bracket (HYPOTHESIS until Electronics publishes the 44 cm3 fault path) and C3 on the new unprimed plans."""
    from scipy.stats import binomtest

    def mcn(A, B):
        lost, gained = int(np.sum(A & ~B)), int(np.sum(~A & B))
        return dict(P_a=float(A.mean()), P_b=float(B.mean()), lost=lost, gained=gained,
                    p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0)

    out = dict(note=("fp150: fixed 1.50 s (reviewer arithmetic); prepLO / prepHI: vapour pocket on the prep path (prep 0.56 s + "
                     "Combustion's W 1.05 s table); at plan 1.41 s the prep path keeps the v2.8 window W 0.65 s (prep bound 1.37 s), at "
                     "1.77 s Combustion's option (b) W 1.05 s; C3: liquid line planned at the unprimed value"), cases={}, paired={})
    for st, pl in FP_CASES:
        ok, u = _runs(st, pl)
        if ok is None:
            out["cases"][f"{st}@{pl:.2f}"] = None
            continue
        if st in ("prepLO", "prepHI"):
            W = 0.65 if pl < 1.5 else 1.05
            a = ab["vap" + st[4:]][f"W{W:.2f}"]
        else:
            W, a = None, 0.0
        x = p_total(ok, u, a)
        x.update(W_s=W, ci95_lit=TG.wilson(int(ok.sum()), len(ok)))
        out["cases"][f"{st}@{pl:.2f}"] = x
    for st, a_, b_ in (("fp150", 1.41, 1.51), ("prepLO", 1.41, 1.77), ("prepHI", 1.41, 1.77), ("liq", 0.81, 1.51), ("liq", 0.81, 1.77)):
        A, _ = _runs(st, a_)
        B, _ = _runs(st, b_)
        if A is not None and B is not None:
            out["paired"][f"{st}: {b_:.2f} vs {a_:.2f} (P|lit)"] = mcn(A, B)
    try:
        el = json.load(open(EL_FAULT))
        out["electronics_draft"] = dict(path=EL_FAULT, sha256_16=sha16(EL_FAULT), published=False,
                                        note="Electronics work-folder draft fault_path_v1 (SIL S11, firmware v2.8.1); context only")
    except Exception as e:   # noqa: BLE001
        out["electronics_draft"] = dict(path=EL_FAULT, error=str(e))
    return out


def superseded_eval():
    """v1.5: P of the LO-table cases flown on the pre-void-fix states file (LO pocket 29.28 cm3), kept as evidence."""
    out = dict(folder=SUPERSEDED, cases={})
    pf = os.path.join(SUPERSEDED, "relight_vapour_states_v2p4_pre_void_fix.json")
    if os.path.exists(pf):
        dsx = json.load(open(pf))
        k = gov_key(dsx, GOV_STATES["vapLO"])
        out["states_file"] = dict(path=pf, sha256_16=sha16(pf), governing_LO_key=k,
                                  P_abort={W: dsx["states"][k][W]["P_abort"] for W in ("W0.65", "W0.85", "W1.05")})
    if os.path.isdir(SUPERSEDED):
        for fn in sorted(os.listdir(SUPERSEDED)):
            if fn.startswith("mc6_runs_") and fn.endswith(".csv"):
                rr = rows_csv(os.path.join(SUPERSEDED, fn))
                ok = np.array([float(r["ok"]) for r in rr]) > 0.5
                out["cases"][fn[len("mc6_runs_"):-4]] = dict(P=float(ok.mean()), n=int(len(ok)))
    out["note"] = ("flown in the v1.3 / v1.4 runs on the pre-fix LO table (V_eff 29.28 cm3); superseded by the re-flown cases on the "
                   "current table (V_eff 35.09 cm3); not used in any v1.5 result")
    return out


def part_eval(t, info):
    a1s = json.load(open(f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"))
    sz = max((c.get("engine_on_counter_s") or 0.0) for c in a1s["cycles"] if c["name"].startswith("DC-A1_full_flight_disp_p99"))
    ab = abort_tables()
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=V.R.IFACE, request=(
        "lead 2026-10-13: cost of the fallback in which every relight is planned as a vapour-segment start: W 1.05 s, planning "
        "value 0.16 + 1.05 = 1.21 s; P paired on the four A1 bases against the 0.81 s baseline; P when a liquid line is planned "
        "at 1.21 s. GNC addition (v1.1): alternative (b') plan 0.81 s with W 1.05 s, ECU abort probabilities, decision table"),
        plan_fallback_s=PLAN_FB, plan_baseline_s=PLAN_BASE, w_fallback_s=W_FALLBACK, w_v3_s=W_V3, torch_gate_s=TORCH_GATE,
        tables=info, ecu_abort_probability=ab, a1_sizing_counter_s=sz, by_base={}, pooled={}, context_v28={})
    pooled = {}
    for base in V.BASES:
        b0 = rows_csv(os.path.join(V28, f"mc6_runs_v28_liq_p{PLAN_BASE:.2f}_{base}_k2_v28.csv"))
        c0 = json.load(open(os.path.join(V28, f"v28_case_v28_liq_p{PLAN_BASE:.2f}_{base}_k2.json")))
        bb = dict(baseline=dict(case=f"v28_liq_p{PLAN_BASE:.2f}_{base}_k2", **case_stats(b0, c0, sz)))
        pooled.setdefault("baseline", []).append(np.array([float(r["ok"]) for r in b0]) > 0.5)
        for st, plan, bases in case_list():
            if base not in bases:
                continue
            name = cname(st, base, plan)
            key = f"{st}_p{plan:.2f}"
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{name}.csv"))
            cjp = os.path.join(OUT, f"case_{name}.json")
            if not rr or not os.path.exists(cjp):
                print("missing", name, flush=True)
                continue
            cj = json.load(open(cjp))
            x = case_stats(rr, cj, sz)
            pr = TG.pair(b0, rr)
            x["vs_baseline_paired"] = dict(lost=pr["lost"], gained=pr["gained"], p_exact=pr["p"], P_base=pr["P_base"],
                                           P_case=pr["P_case"], dP=pr["P_case"] - pr["P_base"], loses=pr["loses"],
                                           lost_runs=pr["lost_runs"], gained_runs=pr["gained_runs"])
            x["pairing_check"] = pairing_check(b0, rr)
            x["case"] = name
            bb[key] = x
            if tuple(bases) == tuple(V.BASES) and st not in STATES_SENS and plan not in SWEEP_PLANS:
                pooled.setdefault(key, []).append(np.array([float(r["ok"]) for r in rr]) > 0.5)
            print(f"{name:32s} P {x['P']:.3f} [{x['ci95'][0]:.3f},{x['ci95'][1]:.3f}] vs base {pr['P_base']:.3f}: -{pr['lost']}/"
                  f"+{pr['gained']} p {pr['p']:.2g} | delay {x['start_delay_min_p50_max_s'][0]:.2f}..{x['start_delay_min_p50_max_s'][2]:.2f}"
                  f" | light-plan p50 {x['light_minus_plan_s_min_p50_max'][1]:+.2f} | counter p99 "
                  f"{x['engine_on_counter_p50_p99_max_s'][1]:.2f} (over sizing {x['engine_on_counter_over_a1_sizing']['n_over']}) | "
                  f"usable p01 {x['usable_left_p01_kg']:.3f} | pairing {x['pairing_check']['same_uniform_start_draw']} | "
                  f"{x['fail_modes']}", flush=True)
        for ctx in ("vapF_p1.41", "liq_p1.41", "vapF_p0.81", "vapU_p1.41"):
            rr = rows_csv(os.path.join(V28, f"mc6_runs_v28_{ctx}_{base}_k2_v28.csv"))
            if rr:
                ok = np.array([float(r["ok"]) for r in rr]) > 0.5
                out["context_v28"].setdefault(ctx, {})[base] = dict(P=float(ok.mean()), ci95=TG.wilson(int(ok.sum()), len(ok)))
        out["by_base"][base] = bb
    from scipy.stats import binomtest
    for st, arrs in pooled.items():
        a = np.concatenate(arrs)
        d = dict(n=int(len(a)), P=float(a.mean()), ci95=TG.wilson(int(a.sum()), len(a)))
        if st != "baseline":
            b = np.concatenate(pooled["baseline"])
            lost, gained = int(np.sum(b & ~a)), int(np.sum(~b & a))
            d.update(lost=lost, gained=gained, p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0,
                     dP=float(a.mean() - b.mean()))
        out["pooled"][st] = d
        print(f"pooled {st:14s}: P {d['P']:.4f} [{d['ci95'][0]:.4f},{d['ci95'][1]:.4f}]" +
              (f" vs baseline -{d['lost']}/+{d['gained']} p {d['p_exact']:.2g}" if st != "baseline" else ""), flush=True)
    # paired (b') vs (b) on the same vapour state (same runs, same draws)
    out["bprime_vs_b_paired"] = {}
    for st in STATES_LATE:
        k21, k81 = f"{st}_p{PLAN_FB:.2f}", f"{st}_p{PLAN_BASE:.2f}"
        if k21 in pooled and k81 in pooled:
            a, b = np.concatenate(pooled[k81]), np.concatenate(pooled[k21])
            lost, gained = int(np.sum(b & ~a)), int(np.sum(~b & a))
            out["bprime_vs_b_paired"][st] = dict(P_b=float(b.mean()), P_bprime=float(a.mean()), lost=lost, gained=gained,
                                                 p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0)
    out["decision"] = decision_table(out["pooled"], ab)
    out["plan_curve"] = plan_curve(out["by_base"], ab)
    out["governing_pocket"] = gov_eval(ab)
    out["fault_path_44"] = fault_eval(ab)
    out["min_window_options"] = opt_eval(ab)
    out["superseded_pre_void_fix"] = superseded_eval()
    for lab, o in out["min_window_options"]["options"].items():
        print(f"option {lab}:", flush=True)
        for st, x in o["by_state"].items():
            if x:
                pq = x["paired_P_lit_vs_liquid_plan"]
                print(f"   {st:7s} P|lit {x['P_lit_all']:.3f} abort {x['P_abort']:.3f} P_total {x['P_total']:.3f} (indep "
                      f"{x['P_total_indep']:.3f}) | vs liquid plan: -{pq['lost']}/+{pq['gained']} p {pq['p_exact']:.2g}", flush=True)
        for st, x in o["four_bases"].items():
            pq = x["paired_P_lit_vs_liquid_plan"]
            print(f"   4 bases {st}: P_total {x['P_total']:.3f} | vs liquid plan -{pq['lost']}/+{pq['gained']} p {pq['p_exact']:.2g}",
                  flush=True)
    g = out["governing_pocket"]
    if not g["missing"]:
        print("governing-pocket policy matrix (P_total, survivors = earliest lights; 2 no-growth bases, 1000 runs):", flush=True)
        for lab, v in g["matrix"].items():
            print(f"   {lab:26s} " + "  ".join(f"{st} {v['by_state'][st]['P_total']:.3f} (a {v['by_state'][st]['P_abort']:.3f})"
                                              for st in POLICY_STATES), flush=True)
        print(f"   maximin liq/LO/HI: {g['maximin_over_liq_LO_HI']['best']}  {g['maximin_over_liq_LO_HI']['worst_P']}", flush=True)
        for pn, e in g["expected_P_by_prior"].items():
            print(f"   prior {pn}: best {e['best']} {e['expected_P'][e['best']]:.4f}", flush=True)
        for k, v in g["paired_P_lit"].items():
            print(f"   paired {k}: {v['P_a']:.3f} -> {v['P_b']:.3f} -{v['lost']}/+{v['gained']} p {v['p_exact']:.2g}", flush=True)
    else:
        print("governing-pocket matrix incomplete:", g["missing"], flush=True)
    for k, v in out["fault_path_44"]["cases"].items():
        if v:
            print(f"   fault {k}: P|lit {v['P_lit_all']:.3f} abort {v['P_abort']:.3f} P_total {v['P_total']:.3f}", flush=True)
    for k, v in out["fault_path_44"]["paired"].items():
        print(f"   fault paired {k}: {v['P_a']:.3f} -> {v['P_b']:.3f} -{v['lost']}/+{v['gained']} p {v['p_exact']:.2g}", flush=True)
    for st, x in out["decision"]["by_state"].items():
        print(f"decision {st}: abort W0.65 {x['abort_W065']:.3f} W1.05 {x['abort_W105']:.3f}; break-even p_liquid (v3 vs b) "
              f"{x['break_even_p_liquid_v3_vs_b']}", flush=True)
        for r in x["table"]:
            print(f"   p_liq {r['p_liquid']:.2f}: v3 {r['P_v3']:.4f}  b {r['P_fallback_b']:.4f}  b' {r['P_alt_bprime']:.4f}", flush=True)
    pc = out["plan_curve"]
    for st, cc in pc["curve"].items():
        print(f"plan curve {st}: " + "  ".join(f"{k} {v['P']:.3f}" for k, v in cc.items()), flush=True)
    for r in pc["expected_P_best_plan"]:
        print(f"   p_liq {r['p_liquid']:.2f}: best plan {r['best_plan_s']:.2f} s, E[P] {r['P_best']:.4f}", flush=True)
    print(f"   maximin plan {pc['maximin_plan_s']} {pc['min_over_states_by_plan']}", flush=True)
    for k, v in pc["paired_vs_state_reference"].items():
        print(f"   paired {k}: -{v['lost']}/+{v['gained']} p {v['p_exact']:.2g} dP {v['dP']:+.4f}", flush=True)
    out["not_modelled"] = [
        "the ECU Pc-confirm deadline (sim6 lights at the drawn delay; every fallback table ends below the 1.21 s deadline); the "
        "abort probabilities are Combustion's, applied outside the 6-DOF in the decision table",
        "the abort path: an aborted relight is counted as a lost landing (ASSUMED); a retry or drogue landing is not modelled",
        "the vapour state distribution at RELIGHT: each state is flown on all 500 runs; the expected P of the fallback depends on "
        "how often the segment is liquid, partly vapour or vapour-full (Combustion's buoyant-venting check is pending)",
        "seat-leak or fault-path starts (the v3 fault path 1.37 s is not re-run here)",
        "the A1 coast and drogue phases are the v3 ones; the vapour state does not change the trajectory before the relight",
        "(b'): a W 1.05 s window on a liquid line keeps a failed ignition flowing up to 0.40 s longer before the abort "
        "(hard-start / accumulation question for Combustion; not assessed by GNC)"]
    with open(os.path.join(OUT, "relight_seg44.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "relight_seg44.json"), flush=True)


def main():
    t, info = tables()
    print(json.dumps({k: info[k] for k in ("check_seg44_equals_v2p4_full_shifted", "max_below_plan_fb",
                                           "share_E0E2_after_0p81s_from_E0", "share_after_fallback_deadline")}), flush=True)
    for k, v in t.items():
        print(f"{k:9s} E0->E2 min {v[0]:.3f} median {v[10]:.3f} p95 {v[19]:.3f} max {v[20]:.3f}", flush=True)
    if "run" in PARTS:
        run(all_cases(t))
    if "eval" in PARTS:
        part_eval(t, info)


if __name__ == "__main__":
    main()
