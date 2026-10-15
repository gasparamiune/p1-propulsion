"""m2_rev3_results v1.0 (GNC rev3, 2026-10-13): the GNC rev3 results record for lead CHANGELOG line 181 items P2-P9, as
amended by lines 182, 186, 188 and 194 and by the coordinator's messages of 2026-10-13.

The builder collects; it does not fly and does not recompute a physical result. Every number is read from an evaluation output
named in `sources` (sha256/16 recorded at build time) or quoted from a CHANGELOG / review line named next to it, and every
section carries its label (SIM / DERIVED / ASSUMED / DATASHEET / TO-VERIFY). This file is NOT gnc.json: changes that rev3
implies for gnc.json are listed under proposed_for_v3p2 and need their own independent check before v3.2 (coordinator,
2026-10-13). No hardware data exist; matching numbers or passing checks are not physical approval.
Output: <out>/rev3_results.json (out = /home/claude/work/space/out/rev3)."""
import glob
import hashlib
import json
import os
from collections import OrderedDict

VERSION = "m2_rev3_results v1.0"
SP = "/home/claude/work/space"
OUT = f"{SP}/out/rev3"
HUB = "/home/claude/work/shared-fallback/engine"
BASES = ("A1_none", "A1J_pc")
ALL4 = ("A1_none", "A1J_pc", "A1_pc", "A1J_none")
SRC = OrderedDict(
    fly=f"{OUT}/fly/rev3_fly.json",
    p6=f"{OUT}/fly/p6_late_commit_v1p1.json",
    p6_v10=f"{OUT}/fly/p6_late_commit.json",
    reserve_dip=f"{OUT}/fly/reserve_dip.json",
    r2v2=f"{OUT}/fly/r2v2_eval.json",
    hold_trace=f"{OUT}/fly/hold_trace.json",
    dc_record=f"{OUT}/dc_record_285/dc_record_285m.json",
    p5=f"{OUT}/p5/p5_latency.json",
    rg16w=f"{OUT}/rg16w/rg16w.json",
    mass_v35=f"{OUT}/mass_v35/mass_v35_vs_v3d.json",
    bc210_off=f"{OUT}/bitcheck_v210/bitcheck_v210_offparts.json",
    bc210_func=f"{OUT}/bitcheck_v210/bitcheck_v210_func.json",
    bc211_off=f"{OUT}/bitcheck_v211/bitcheck_v211_offparts.json",
    bc211_func=f"{OUT}/bitcheck_v211/bitcheck_v211_func.json",
    bc212_off=f"{OUT}/bitcheck_v212/bitcheck_v212_offparts.json",
    bc212_func_v10=f"{OUT}/bitcheck_v212/bitcheck_v212_func.json",
    bc212_func_v11=f"{OUT}/bitcheck_v212/bitcheck_v212_func_v1p1.json",
    bc29_rev3=f"{OUT}/bitcheck_v29_rev3/bitcheck_v29.json",
    g6_recheck=f"{OUT}/rev2p1/bit29_g6_recheck.json",
    reviewer_hold_table=f"{HUB}/reviews/combustion/r3/r3_unpurged_classes.json",
    reviewer_tank_outlet=f"{HUB}/reviews/combustion/r3/r3_tank_outlet.json",
    gnc_json_v3p1=f"{HUB}/interfaces/gnc.json",
)
TREES = OrderedDict([("gnc_dev3", "v2.9-dev"), ("gnc_dev4", "v2.10-dev"), ("gnc_dev5", "v2.11-dev"), ("gnc_dev6", "v2.12-dev")])
SCRIPTS = (  # (tree, script, role)
    ("gnc_dev3", "m2_rev3_fly.py", "v1.1: repro, P2 sweep, P2 v3.5 brackets, P3, P2opt v35a / v35t (sim6 v2.9-dev); the queue-1 runs used v1.0 (out/rev3/logs/m2_rev3_fly_v1.0_snapshot.py; v1.1 only added arms)"),
    ("gnc_dev3", "m2_rev3_dc_record.py", "v1.0: P3 285 m duty-cycle record (A1 p99 runs re-flown with the recorder, sim6 v2.9-dev)"),
    ("gnc_dev4", "m2_rev3_fly.py", "v2.1: P4s, P6, P8 (v2.0 flights), P6b (sim6 v2.10-dev); the v2.0 source is rev3_notes/m2_rev3_fly_v2.0_snapshot.py"),
    ("gnc_dev4", "m2_rev3_r2v2_eval.py", "v1.1: P4 R2 v2 statistics evaluation"),
    ("gnc_dev4", "m2_rev3_p6.py", "v1.0: P6 evaluation (superseded by v1.1 for the release hold; kept)"),
    ("gnc_dev4", "patch_sim6_v210.py", "sim6 v2.10-dev amendment V2"),
    ("gnc_dev4", "patch_run6_v210.py", "run6 v2.10-dev"),
    ("gnc_dev4", "m2_bitcheck_v210.py", "bit-check v2.10 vs v2.9"),
    ("gnc_dev5", "m2_rev3_p5.py", "v1.0: P5 latency allowance flights (sim6 v2.11-dev)"),
    ("gnc_dev5", "m2_rev3_rg16w.py", "v1.0: P5 RG-16 windowed budget A1 / B1 + vibration sensitivity"),
    ("gnc_dev5", "patch_sim6_v211.py", "sim6 v2.11-dev amendment L"),
    ("gnc_dev5", "patch_run6_v211.py", "run6 v2.11-dev"),
    ("gnc_dev5", "m2_bitcheck_v211.py", "bit-check v2.11 vs v2.10"),
    ("gnc_dev6", "m2_rev3_fly.py", "v2.2: P6c release-hold comparator (sim6 v2.12-dev); final evaluation of all arms"),
    ("gnc_dev6", "m2_rev3_p6.py", "v1.1: P6 evaluation with the line-194 comparator"),
    ("gnc_dev6", "m2_rev3_reserve_dip.py", "v1.1: R3-17 dip-onset effect on every A1 table + paired re-test of the P2 options with the onset on both tables (v1.0 snapshot in rev3_notes)"),
    ("gnc_dev6", "m2_rev3_hold_trace.py", "v1.0: P4 command-hold trace"),
    ("gnc_dev6", "patch_sim6_v212.py", "sim6 v2.12-dev amendment V3"),
    ("gnc_dev6", "patch_run6_v212.py", "run6 v2.12-dev"),
    ("gnc_dev6", "m2_bitcheck_v212.py", "v1.1: bit-check v2.12 vs v2.11 (v1.0 functional criterion defect kept)"),
    ("gnc_dev6", "m2_bitcheck_v29.py", "v1.2: full rev2.1 bit-check suite, run on the rev3 code (queue 5)"),
    ("gnc_dev6", "m2_rev3_results.py", "v1.0: this builder"),
)


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def J(p):
    return json.load(open(p))


def r4(x):
    return None if x is None else round(float(x), 4)


def case(fly, base, arm):
    return fly["cases"].get(f"{base}|{arm}")


def arm_row(fly, arm, bases=BASES, dip=None):
    """Per-base summary of one arm (SIM)."""
    row = OrderedDict()
    for b in bases:
        c = case(fly, b, arm)
        if c is None:
            row[b] = "NOT FLOWN"
            continue
        w = c["wind"]["inside_W10_lt6"]
        e = OrderedDict(P=c["P"], P_wilson=[r4(x) for x in c["P_wilson"]], n=c["n"], exhausted=c["exhausted"],
                        P_inside_W10_lt6=r4(w["P"]), n_inside_W10_lt6=w["n"],
                        usable_reserve_g_60g_basis=OrderedDict(p01=round(c["usable_reserve_g"]["p01"], 1),
                                                               min=round(c["usable_reserve_g"]["min"], 1)),
                        fail_modes=c["fail_modes"])
        if dip is not None:
            k = f"{b}_{arm.replace('|', '_')}"
            d = dip["arms"].get(k)
            if d:
                e["P_adjusted_dip_onset"] = OrderedDict((o, d[o]["P_adjusted"]) for o in ("125N_62g", "250N_69g", "500N_80g"))
        row[b] = e
    return row


def pooled_for(fly, arm):
    out = OrderedDict()
    for k, v in fly["pooled"].items():
        if k.startswith(arm + "|vs_"):
            ref = k[len(arm) + 4:]
            out[ref] = OrderedDict(P_ref=r4(v["P_ref"]), P_case=r4(v["P_case"]), lost=v["lost"], gained=v["gained"],
                                   p_exact=float(f"{v['p_exact']:.3g}"), loses=v["loses"],
                                   inside_W10_lt6=OrderedDict(lost=v["inside_W10_lt6"]["lost"],
                                                              gained=v["inside_W10_lt6"]["gained"],
                                                              p_exact=float(f"{v['inside_W10_lt6']['p_exact']:.3g}"))
                                   if "inside_W10_lt6" in v else None)
    return out


def wind_bins(fly, arm, bases):
    out = OrderedDict()
    for b in bases:
        c = case(fly, b, arm)
        if c:
            out[b] = OrderedDict((k, f"{v['fail']}/{v['n']}") for k, v in c["wind"]["by_W10_bin"].items())
    return out


# --------------------------------------------------------------------------------------------------------------- sections
def sec_configuration(src):
    trees = OrderedDict()
    for t, v in TREES.items():
        g = f"{SP}/{t}/gncsim"
        trees[t] = OrderedDict(sim6=v, sim6_sha16=sha16(f"{g}/sim6.py"), run6_sha16=sha16(f"{g}/run6.py"),
                               engine_v2_sha16=sha16(f"{g}/engine_v2.py") if os.path.exists(f"{g}/engine_v2.py") else None,
                               data=os.path.realpath(f"{SP}/{t}/data"))
    flown_on = OrderedDict([
        ("gnc_dev3 (sim6 v2.9-dev)", "repro, P2 sweep, P2 v3.5 brackets, P3, P2opt v35a, P2opt v35t, the 285 m duty-cycle record"),
        ("gnc_dev4 (sim6 v2.10-dev, amendment V2)", "P4s R2 v2 statistics, P6 (rh220/rh250 SUPERSEDED, L400 late commit), P8, P6b"),
        ("gnc_dev5 (sim6 v2.11-dev, amendment L)", "P5 latency allowance flights, P5 RG-16 windowed budget"),
        ("gnc_dev6 (sim6 v2.12-dev, amendment V3)", "P6c release-hold comparator, P4 command-hold trace, final evaluation, full v2.9 bit-check suite"),
    ])
    return OrderedDict(
        tag="CONFIGURATION (records)",
        trees=trees, groups_flown_on=flown_on,
        why_several_trees=("each amendment is off by default and bit-identical when off (bit-checks v2.10 / v2.11 / v2.12 below), "
                           "so the decided-path arms keep their earlier tree and only the arms that need an amendment are flown on "
                           "the tree that carries it"),
        env=OrderedDict(script="gnc_dev3/scripts/m2r3_env.sh (sha256/16 " + sha16(f"{SP}/gnc_dev3/scripts/m2r3_env.sh") + ")",
                        GNC_IFACE="iface_v3d (v3.5 bracket arms: iface_v35a)", GNC_IFACE_PIN="pins_rev3/pins_rev3.sha256 (v3.5 arms: pins_rev3_v35a.sha256)",
                        GNC_STRICT=1, GNC_PC_RATCHET=1, threads=1, seed=101,
                        runs_per_arm="500 (P5 latency and RG-16: 200; trace and functional checks: 4-12)",
                        apogee_target="285 m for P2 / P3 / P4 / P6 / P8; P5 flights and the RG-16 budget keep the rev2 300 m A1 target of "
                                      "their stored comparators (m2_fault_f / m2_rg16_fct_terms definitions; the reviewer's 2.973 % / "
                                      "4.015 % are at that configuration); B1 at 62 m"),
        pins=OrderedDict((os.path.basename(p), sha16(p)) for p in sorted(glob.glob(f"{SP}/pins_rev3/*.sha256"))),
    )


def sec_bitchecks(src):
    def off(p):
        d = J(p)
        return OrderedDict(file=f"{p} ({sha16(p)})", a=d["a"]["sim"], b=d["b"]["sim"], a_sim6=d["a"]["sim6_sha16"], b_sim6=d["b"]["sim6_sha16"],
                           a_run6=d["a"]["run6_sha16"], b_run6=d["b"]["run6_sha16"], common_results=d["common_results"],
                           common_record_columns=d["common_record_columns"], new_results=d["new_results"],
                           new_record_columns=d["new_record_columns"], cases=len(d["cases"]), all_identical=d["all_identical"])

    def func(p, key_pass=("all_pass",)):
        d = J(p)
        allp = d.get("all_pass")
        if allp is None:
            allp = all(v.get("pass_", v.get("passed", False)) for v in d.get("checks", {}).values()) if "checks" in d else None
        return OrderedDict(file=f"{p} ({sha16(p)})", version=d.get("version"), all_pass=allp,
                           checks=OrderedDict((k, v.get("pass_", v.get("passed"))) for k, v in d.get("checks", {}).items()))

    out = OrderedDict(tag="SIM (code checks; not physical evidence)")
    out["v2.10_vs_v2.9"] = OrderedDict(off=off(src["bc210_off"]), functional=func(src["bc210_func"]))
    out["v2.11_vs_v2.10"] = OrderedDict(off=off(src["bc211_off"]), functional=func(src["bc211_func"]))
    out["v2.12_vs_v2.11"] = OrderedDict(off=off(src["bc212_off"]), functional_v1p0_FAIL_kept=func(src["bc212_func_v10"]),
                                        functional_v1p1=func(src["bc212_func_v11"]),
                                        v1p0_failure=("criterion defect, not a patch defect: v1.0 required the recorded command to equal pv2_rhF "
                                                      "nowhere else in the flight, but the guidance itself commands exactly 500 N on the ascent "
                                                      "burn (phase 1) and, through the command quantisation, exactly 200 N on isolated landing-burn "
                                                      "records (phase 6) (probe rev3_notes/v212_func_probe.py); v1.1 checks the block after the "
                                                      "relight; part A was not re-flown"))
    p = src["bc29_rev3"]
    if os.path.exists(p):
        d = J(p)
        parts = d.get("parts") or {}
        out["v2.9_full_suite_on_rev3_code"] = OrderedDict(
            file=f"{p} ({sha16(p)})", tree="gnc_dev6 (sim6 v2.12-dev)", tool=d.get("tool"), sim=d.get("sim"), pins=d.get("pins"),
            strict=d.get("strict"), parts_run=d.get("parts_run"), result=d.get("all_passed"),
            parts=OrderedDict((k, v.get("passed") if isinstance(v, dict) else v) for k, v in parts.items()),
            part_wall_s=OrderedDict((k, round(float(v), 1)) for k, v in (d.get("part_wall_s") or {}).items()),
            code_sha256_16=d.get("code_sha256_16"), code_unchanged_during_run=d.get("code_unchanged_during_run"),
            inputs_opened=len(d.get("inputs_opened_sha256_16") or {}),
            log=f"{OUT}/logs/bitcheck_v29_rev3.log",
            note=("the rev2.1 suite (written for sim6 v2.9-dev) run unchanged on the rev3 code with every rev3 amendment off "
                  "by default (V2, L, V3): the decided-path checks must still hold; it does not test the rev3 amendments "
                  "themselves (bit-checks v2.10 / v2.11 / v2.12 above do)"),
            observation=("the strict-mode error texts of run6 still begin 'run6 v2.9-dev:' (gnc_dev6/gncsim/run6.py lines 87, 107, 129: "
                         "unchanged since the v2.9-dev strict loader) while the module and every result record name v2.12-dev; "
                         "text only, no effect on a result (N1-N4 match on the message body); not changed in rev3 because the "
                         "code is bit-checked as is; to correct at the next amendment"))
    else:
        out["v2.9_full_suite_on_rev3_code"] = "NOT RUN at build time (queue 5 pending); see the handback"
    g = J(src["g6_recheck"])
    out["G6_P30_reproduced_in_pass"] = OrderedDict(file=f"{src['g6_recheck']} ({sha16(src['g6_recheck'])})",
                                                   note="rev2.1 recheck (m2_bitcheck_v29 v1.2): run 1 (no P30 arm) fails under the v1.2 "
                                                        "criterion, run 2 passes with P30_reproduced, the gate-off CA arm and the positive "
                                                        "control", detail={k: v for k, v in g.items() if k in ("runs", "test_passed")} or None)
    return out


def sec_P2(fly, dip, mass):
    sweep = OrderedDict()
    for st in ("liq", "pw"):
        for dm in (100, 200, 300, 450):
            a = f"{st}|G73|dm{dm}g|h285"
            sweep[a] = OrderedDict(per_base=arm_row(fly, a, dip=dip), pooled=pooled_for(fly, a))
    br = OrderedDict()
    for v, sts in (("v35a", ("liq", "pw")), ("v35t", ("liq", "pw")), ("v35g", ("liq",))):
        for st in sts:
            a = f"{st}|G73|{v}|h285"
            br[a] = OrderedDict(per_base=arm_row(fly, a, dip=dip), pooled=pooled_for(fly, a))
    opts = OrderedDict()
    for v in ("v35a", "v35t"):
        for st in ("liq", "pw"):
            for o in ("h275", "h265", "h255", "h245", "kd70|h285", "ht5|h285"):
                a = f"{st}|G73|{v}|{o}"
                opts[a] = OrderedDict(per_base=arm_row(fly, a, dip=dip), pooled=pooled_for(fly, a))
    t = mass["totals"]
    return OrderedDict(
        tag="SIM (flights) / DERIVED (mass mapping, dip-onset adjustment); ASSUMED bleed-valve masses",
        mass_mapping=OrderedDict(source=f"{SRC['mass_v35']} ({sha16(SRC['mass_v35'])})",
                                 v35a_landing_mass_delta_kg=t["landing_mass_delta_kg"]["v"],
                                 gimballed_delta_kg=t["gimballed_delta_kg"]["v"], fixed_delta_kg=t["fixed_delta_kg"]["v"],
                                 v35t="valves at the 0.15 kg target: +0.868 kg (DERIVED)",
                                 v35g="gimballed engine, ring and P07 from CAD v3.5 only: +0.341 kg (DERIVED)",
                                 ASSUMED="bleed valves 2 x 0.30 kg until a maker datasheet (line 182 (3))"),
        sweep_point_mass_at_P07=sweep, v35_brackets=br, options_lead_181_5=opts,
        options_paired_with_dip_onset=OrderedDict(
            tag="DERIVED (SIM tables re-counted with the R3-17 onset on both arms; exact McNemar pooled over A1_none and A1J_pc)",
            definition=dip.get("paired_adjusted_vs_v3d_mass", {}).get("definition"),
            arms=dip.get("paired_adjusted_vs_v3d_mass", {}).get("arms")),
        not_flown=OrderedDict(
            v3p5p1_ledger="NOT FLOWN: Mechanical massprops_v3.5.1 not in the hub at build time (lead 182 (8), 188 (11)); re-fly trigger "
                          "per 181 (5) stands (>= 0.10 kg confirmed growth over ledger v3d)",
            allowance_0p20kg="NOT FLOWN as its own arm. Bracket only (DERIVED): v35t + 0.20 kg = +1.068 kg lies between the flown v35t "
                             "(+0.868 kg) and v35a (+1.168 kg) arms"),
        residual_basis=("every P2 / P3 table above was flown with the sim6 unusable residual of 3 % of the liquid at t0 (60 g, "
                        "ASSUMED); P_adjusted_dip_onset re-counts a successful run with liquid left below the REV-COMB-3 R3-17 "
                        "dip onset (62 / 69 / 80 g at 125 / 250 / 500 N, DERIVED) as lost (lead line 194 (6); outlet geometry "
                        "MISSING, Mechanical OI-32)"),
    )


P3_ARMS = (("liq|none|h285", ALL4), ("liq|G73|h285", ALL4), ("pw|G73|h285", ALL4), ("pl|G73|h285", ALL4), ("e19|G73|h285", ALL4),
           ("liq|none|L400|h285", BASES), ("liqP|G73|h285", BASES), ("pwP|G73|h285", BASES), ("liq|G73|L400|h285", BASES),
           ("pw|G73|L400|h285", BASES), ("e19|G73|L400|h285", BASES), ("nrLO|G73z|h285", BASES), ("nrLO|none|h285", BASES))


def sec_P3(fly, dip, dcr):
    arms = OrderedDict()
    for a, bs in P3_ARMS:
        arms[a] = OrderedDict(per_base=arm_row(fly, a, bs, dip=dip), failures_by_W10_bin=wind_bins(fly, a, bs),
                              pooled=pooled_for(fly, a))
    rep = OrderedDict((k, v) for k, v in fly["repro"].items())
    recs = OrderedDict()
    for r in dcr["records"]:
        recs[r["name"]] = OrderedDict(
            file=r["file"], sha256_16=r["sha256_16"], source=r["source"], run_index=r["run_index"], run_seed=r["run_seed"],
            reproduces_mc_row=r["reproduces_mc_row"], mismatched_fields=r["mismatched_fields"], success=r["success"],
            selection=r["selection"], engine_on_counter_s=round(r["engine_on_counter_s"], 3), thrust_on_s=round(r["burn_time_s"], 3),
            burns_s=[[round(a, 3), round(b, 3)] for a, b in r["burns_s"]], total_impulse_Ns=round(r["total_impulse_Ns"], 1),
            n2o_burned_kg=round(r["n2o_burned_kg"], 4), fuel_burned_kg=round(r["fuel_burned_kg"], 4), apex_m=round(r["summary"]["h_max"], 1),
            td_vz_mps=round(r["summary"]["td_vz"], 2), Pc_max_bar=round(r["Pc_max_Pa"] / 1e5, 2),
            max_axial_specific_airborne_mps2=round(r["max_axial_specific_airborne_mps2"], 2),
            max_axial_specific_leg_contact_mps2=round(r["max_axial_specific_leg_contact_mps2"], 2),
            vs_a1_sizing_cycle=r["vs_a1_sizing_cycle"], residual=r["residual"])
    pub = dcr["published_a1_cycles"]
    dcrec = OrderedDict(
        tag="SIM (one Monte Carlo run per file, re-flown with the recorder); RECORD, not a sizing case",
        source=f"{SRC['dc_record']} ({sha16(SRC['dc_record'])}); generator {dcr['version']} (sha256/16 {dcr['script_sha16']}), "
               f"{dcr['sim']} sim6 {dcr['sim6_sha16']} run6 {dcr['run6_sha16']}, pins {dcr['pin_sha16']}",
        method=dcr["method"], records=recs,
        comparison=OrderedDict((k, v) for k, v in pub.items()),
        reading=("both files reproduce their Monte Carlo rows field by field; same 23-column format as the published duty cycles; "
                 "staged in staging_v3.1/rev3/duty_cycles/, the published duty_cycles index is not touched (the lead decides at v3.2)"))
    return OrderedDict(tag="SIM", arms=arms, repro_against_staged_rev2=rep, duty_cycle_record_285m=dcrec,
                       wind_rule="launch-commit W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s is a HARD rule for A1 (lead 181 (6)); the "
                                 "flights draw W10 ~ U(0, 8) m/s; sigma_u is not a flight variable here (TO-VERIFY at SIL)")


def sec_P4(r2, hold):
    th = OrderedDict()
    for k, v in r2["thresholds"].items():
        e = OrderedDict()
        for wk in ("all_winds", "W10_lt6"):
            x = v[wk]
            e[wk] = OrderedDict(lit_min_N_WITHDRAWN_MODEL=r4(x["lit_min_N"]), flameout_design_max_N=r4(x["flameout_design_max_N"]),
                                gap_N=r4(x["gap_N"]), T_mid_N=r4(x["T_mid_N"]),
                                at_T_rev2=OrderedDict(T_N=r4(x["at_T_rev2"]["T"]),
                                                      lit_margin_N_WITHDRAWN_MODEL=r4(x["at_T_rev2"]["lit_margin_N"]),
                                                      flameout_margin_N=r4(x["at_T_rev2"]["flameout_margin_N"]),
                                                      lit_not_released_WITHDRAWN_MODEL=f"{x['at_T_rev2']['lit_not_released']}/{x['at_T_rev2']['n_lit']}",
                                                      flameout_released=f"{x['at_T_rev2']['flameout_released']}/{x['at_T_rev2']['n_fo']}"),
                                flameout_sensitivities_max_N=OrderedDict((s, r4(y["max_N"])) for s, y in x["sensitivities_at_T_mid"].items()))
        th[k] = e
    tr = OrderedDict()
    for name, c in hold["cases"].items():
        runs = c["runs"]
        tr[name] = OrderedDict(n_runs=len(runs), hold_s=[r["hold_s"] for r in runs], hold_records_at_62p5N=[r["hold_records"] for r in runs],
                               ECU_command_values_N=sorted(set(v for r in runs for v in r["Fcmd_values_in_window"]))[:12],
                               F_cold_max_N=[r["Fcl_max"] for r in runs], valve_lift_max_mm=[r["lift_max_mm"] for r in runs],
                               R2_estimate_max_N=[r["pfa_max"] for r in runs], F_truth_max_N=[r["F_truth_max_in_window"] for r in runs])
    return OrderedDict(
        tag="SIM statistics on DERIVED cold-flow bounds; lit side PENDING",
        source=f"{SRC['r2v2']} ({sha16(SRC['r2v2'])}); trace {SRC['hold_trace']} ({sha16(SRC['hold_trace'])})",
        status=("lit side PENDING: lead line 194 (2) withdraws the lit model 62.5 N x pcf_k used by the lit statistics arms "
                "(values kept below, marked WITHDRAWN_MODEL, as evidence only); the lit side is re-run on F_cold(lift, P_tank) plus "
                "the grain_q1d start-level lit thrust history (fuel-starved 0.1-0.4 s at 0.2039 mm) when Combustion v2.4b publishes "
                "the CSV. The flame-out side (cold-flow DERIVED design bound, x 1.3 heat pick-up, HEM nominal, none) stands. The "
                "16.31 N start-level margin is CONDITIONAL on a CF-3 start-lift measurement (lead 194 (2)); the heat TO-VERIFY moves "
                "to the injector body and feed soak-back (2.8-3.7 kW threshold, Combustion)."),
        modes="0 E0-frozen (flown amendment V form); 1 E2 re-reference; 2 E0-frozen + drogue-drag compensation; 3 E2 re-reference + "
              "drogue-drag compensation; windows E2 + 0.5 s / 0.8 s; T_rev2 = rel_F 37.159 N",
        thresholds=th,
        reading=("flame-out side only (lit side pending): in mode 3 with the 0.8 s window inside W10 < 6 m/s the flame-out design "
                 "maximum is the lowest-risk case at T_rev2 (margin listed); over all winds every mode has a negative gap under the "
                 "withdrawn lit model, so no threshold is proposed until the v2.4b lit history is flown"),
        command_hold_trace=tr,
        command_hold_reading=("with the hold the ECU command stays at 62.5 N for the 0.8 s window (40 records at 20 ms), the valve lift "
                              "stays near the start lift and the flame-out cold-flow thrust near the DERIVED bound at the start lift; "
                              "without the hold the guidance command rises and the cold-flow thrust and the R2 estimate rise with it "
                              "(values above): the hold is what keeps an undetected flame-out below the release threshold"),
        P4c_confirmation="NOT FLOWN: 20 arms defined (m2_rev3_fly v2.1 P4c) but held after lead 194 (2) withdrew the lit model; the "
                         "flame-out confirmation is deferred to the joint lit / flame-out confirmation on the v2.4b history because the "
                         "threshold depends on both sides",
        landings_after_late_release="NOT FLOWN as separate arms in rev3 (part of the P4c confirmation set)",
        incoming_electronics_line_198_6=("Electronics SIL (CHANGELOG line 198 (6), S17): after a Pc loss 1-2 frames above 37.16 N are "
                                         "carried through the estimator lag at the W6 bound, so the R2 counting start after a Pc "
                                         "loss needs a rule; also DROGUE 1 / 0 and the d6 b6 echo check before a RELIGHT in the FSW "
                                         "record. Not flown in rev3 (sim6 has no ECU frame model of that lag); carried into the joint "
                                         "lit / flame-out confirmation (P4c) and the FSW record"),
    )


def sec_P5(p5, rg):
    lat = OrderedDict()
    for k, a in p5["arms"].items():
        if "|nom|" in k:
            lat[k] = OrderedDict(P=a.get("P"), apex_m_p50=a.get("apex_m", {}).get("p50"))
            continue
        nomp = next((v for kk, v in a.items() if kk.startswith("paired_vs_") and "|nom|" in kk), None)
        zl = next((v for kk, v in a.items() if kk.startswith("paired_vs_") and "dla00" in kk), None)
        lat[k] = OrderedDict(
            forced=f"{a.get('forced_decisions')}/{a.get('onset_reached')}", P=a.get("P"),
            dv_allowance_mps=OrderedDict(p50=a["dv_allowance_mps"]["p50"], p99=a["dv_allowance_mps"]["p99"]) if a.get("dv_allowance_mps") else None,
            dv_derived_mps_p50=a.get("dv_allowance_derived_mps", {}).get("p50"),
            apex_m=OrderedDict((q, a["apex_m"][q]) for q in ("p50", "p99", "max")) if a.get("apex_m") else None,
            apex_minus_nominal_m=OrderedDict((q, nomp["apex_minus_ref_m"][q]) for q in ("p50", "p99", "max")) if nomp else None,
            apex_minus_zero_latency_m=OrderedDict((q, zl["apex_minus_ref_m"][q]) for q in ("p50", "p99", "max")) if zl else None,
            max_true_height_after_onset_m=OrderedDict((q, a["max_true_height_after_onset_m"][q]) for q in ("p50", "p99", "max"))
            if a.get("max_true_height_after_onset_m") else None,
            touchdown_vz_mps_p01=a.get("touchdown_vz_mps", {}).get("p01"),
            FC_THRUST_in_loop_not_acting=OrderedDict(tripped_650_inside_allowance=a["fct_inloop"].get("tripped_650_inside_allowance"),
                                                     trip_after_plateau_ms=a["fct_inloop"].get("trip_after_plateau_ms"))
            if a.get("fct_inloop") else None,
        )
    bud = OrderedDict()
    for c, e in rg["cases"].items():
        bud[c] = OrderedDict(reproduction_identical=e["reproduction"]["pooled_quantiles_identical"],
                             per_run_mismatches=e["reproduction"]["per_run_mismatches"],
                             s_mass=r4(e["terms"]["s_mass"]), bias=r4(e["terms"]["bias"]),
                             segments_ge_52_frames_share=e["vib"]["white"]["selected_segments_frames"]["share_ge_52"],
                             strict_total_pct=OrderedDict((v, round(100 * x["strict_windowed_500ms"]["strict_total"], 3)) for v, x in e["vib"].items()),
                             strict_pass=OrderedDict((v, x["strict_windowed_500ms"]["strict_passes"]) for v, x in e["vib"].items()),
                             strict_margin_pp=OrderedDict((v, round(x["strict_windowed_500ms"]["strict_margin_pct_points"], 3)) for v, x in e["vib"].items()))
    return OrderedDict(
        tag="SIM on an ASSUMED fault shape and ASSUMED vibration models; DERIVED budget",
        sources=f"{SRC['p5']} ({sha16(SRC['p5'])}); {SRC['rg16w']} ({sha16(SRC['rg16w'])})",
        allowance="PROVISIONAL 0.5 s from the onset of the 670 N plateau, strict windowed form, no window-gain credit (lead 181 (3))",
        latency_consequence=lat,
        latency_reading=("every forced decision is an abort and a lost vehicle by definition (an aborted flight is not a landing); the "
                         "0.5 s allowance adds 16-19 m/s (p50, SIM; the DERIVED (670 / m - g) x 0.5 s is 0.3-0.9 m/s higher: it "
                         "ignores drag and the ramp); on A1 "
                         "ascent the apex can exceed the nominal by up to the p99 listed (the zero-latency arm stays below nominal); on "
                         "B1 floor phases the vehicle climbs to ~106-120 m (nominal apex 62 m); the in-loop FC_THRUST statistic "
                         "(computed, not acting) would have tripped inside the allowance in every dla05 run"),
        windowed_budget=bud, allowed_total_pct=round(100 * rg["allowed_total"], 3),
        reviewer_reference=rg["reviewer_reference"],
        budget_reading=("A1 comp path reproduces the reviewer's 2.973 % (PASS by 0.012 pp) and the non-comp path 4.015 % (FAIL); B1 "
                        "(new) passes on the white model (2.083 % comp, 2.385 % without); any correlated vibration at the same RMS (AR(1) "
                        "5-100 ms) fails A1 and B1; at the same frame-level RMS A1 fails from AR 20 ms and B1 passes except AR 100 ms "
                        "without compensation (-0.006 pp); B1: 9-10 % of the nominal FC segments are shorter than 0.52 s, where the "
                        "500 ms window cannot be formed (budget over the remaining segments). A measured spectrum is TO-VERIFY "
                        "(Electronics / Mechanical); per 181 (3) a failing budget changes the detector, not the allowance."),
    )


def sec_P6(p6, p6v10):
    c = p6["release_hold_v1p1"]
    comp = OrderedDict()
    for name, e in c["arms"].items():
        d = OrderedDict(hold_s=e["hold_s"], profile=e["profile"], status=e["status"])
        for b in BASES:
            if b in e:
                x = e[b]
                d[b] = OrderedDict(P_GNC=x["P_GNC"], P_wilson=x["P_wilson"],
                                   vs_nrLO_release_at_E2=OrderedDict((k, x["vs_nrLO|none|h285"][k]) for k in ("P_ref", "lost", "gained", "p_exact", "loses"))
                                   if "vs_nrLO|none|h285" in x else None,
                                   profile_time_s=x.get("profile_time_s"), F_truth_max_under_profile_N=x.get("F_truth_max_under_profile_N"))
            else:
                d[b] = "NOT FLOWN"
        d["residual_released_then_A3_per_group"] = e["residual_released_then_A3_per_group"]
        d["P_total_DERIVED"] = e["P_total_DERIVED"]
        comp[name] = d
    return OrderedDict(
        tag="SIM (GNC trajectory P) x DERIVED (Combustion / reviewer classes); canopy dynamics TO-VERIFY",
        sources=f"{SRC['p6']} ({sha16(SRC['p6'])}); v1.0 evaluation kept: {SRC['p6_v10']} ({sha16(SRC['p6_v10'])})",
        contingency=p6["contingency"], P_by_realised_lead=p6["lead_bins"], gate_delay_tolerance=p6["gate_delay"],
        lstar_table=p6["lstar_table"], findings=p6["findings"],
        comparator_line194=OrderedDict(admissible_with_Pc_invalid=c["admissible_with_Pc_invalid"], why=c["why_not_admissible"],
                                       latest_A3_trip_after_E2_s=c["latest_A3_trip_after_E2_s"],
                                       P_success_population=c["P_success_population"], P_success_note=c["P_success_note"],
                                       arms=comp),
        superseded_evidence=("rh220 / rh250 (E2 + 0.22 / 0.25 s) were flown on the sim's guidance profile (~100 N) before lead 194 "
                             "withdrew the 0.22 s hold; their tables and the v1.0 P_total are kept under the superseded keys of the "
                             "P6 evaluation, not used for any decision"),
    )


def sec_P8(fly):
    out = OrderedDict()
    for a in ("liqF|G73|h285", "pwF|G73|h285"):
        out[a] = OrderedDict(per_base=arm_row(fly, a), pooled=pooled_for(fly, a))
    return OrderedDict(tag="SIM", definition="RG-08 flag flips to UNPRIMED after the T_fire plan (prep-path start delays +0.56 s, plan "
                                             "still 0.81 s); UNKNOWN = UNPRIMED is liqP / pwP (P3)", arms=out)


def sec_P9_pins():
    dirs = OrderedDict([("pins_rev3.sha256", f"{SP}/iface_v3d"), ("pins_rev3_v35a.sha256", f"{SP}/iface_v35a"),
                        ("pins_rev3_v35a_cold.sha256", f"{SP}/iface_v35a")])
    extra = (f"{HUB}/02-combustion/data/v2p4", f"{HUB}/02-combustion/data/v2/v2p4", f"{HUB}/02-combustion/data/v2p4a",
             f"{HUB}/06-electronics/results", f"{HUB}/03-cad/calcs")
    out = OrderedDict()
    for pl, idir in dirs.items():
        p = f"{SP}/pins_rev3/{pl}"
        ent = []
        for ln in open(p):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            h, n = ln.split(None, 1)
            n = os.path.basename(n.strip().lstrip("*"))
            cand = [os.path.join(idir, n)] + [os.path.join(d, n) for d in extra]
            found = [(c_, hashlib.sha256(open(c_, "rb").read()).hexdigest() == h) for c_ in cand if os.path.exists(c_)]
            ent.append(OrderedDict(name=n, pinned_sha16=h[:16], resolved=[f for f, _ in found], match=[m for _, m in found],
                                   ok=bool(found) and found[0][1]))
        out[pl] = OrderedDict(file=f"{p} ({sha16(p)})", n=len(ent), all_resolved_match=all(e["ok"] for e in ent), entries=ent)
    return out


def sec_P9_code():
    out = OrderedDict()
    for t, s, role in SCRIPTS:
        p = f"{SP}/{t}/scripts/{s}"
        out[f"{t}/scripts/{s}"] = OrderedDict(sha256_16=sha16(p) if os.path.exists(p) else "MISSING", role=role)
    for p in sorted(glob.glob(f"{SP}/rev3_notes/*.py")) + sorted(glob.glob(f"{OUT}/logs/*_snapshot.py")):
        out[p.replace(SP + "/", "")] = OrderedDict(sha256_16=sha16(p), role="snapshot / probe (evidence)")
    return out


def P(fly, b, a):
    c = case(fly, b, a)
    return None if c is None else c["P"]


def Ps(fly, a, bases=BASES):
    return " / ".join("n/a" if P(fly, b, a) is None else f"{P(fly, b, a):.3f}" for b in bases)


def pool_str(fly, a, ref, grp="main2"):
    v = fly["pooled"].get(f"{a}|vs_{ref}|{grp}")
    if not v:
        return "n/a"
    return (f"pooled {v['P_case']:.4f} vs {v['P_ref']:.4f}, -{v['lost']}/+{v['gained']}, p {v['p_exact']:.3g}"
            + (" LOSES" if v["loses"] else ""))


def sec_synthesis(out, fly, p6, dip, p5, rg, r2):
    ct = p6["contingency"]

    def cg(k, f, sub=None):
        e = ct.get(k)
        if e is None:
            return None
        x = e[f]
        return x[sub] if sub else x

    ant = OrderedDict()
    for x in (13, 17, 21, 25):
        for start, tag in (("", "nominal"), ("L400|", "L400")):
            a = f"e19|G73|{start}ant{x}|h285"
            ant[f"{tag}|ant{x}"] = OrderedDict(
                P=Ps(fly, a), lead_p50_s=cg(f"A1_none|{a}", "lead_commit_to_plain_s", "p50"),
                tfire_after_plain_p50_s=cg(f"A1_none|{a}", "tfire_after_plain_s", "p50"),
                E0_height_p50_m=cg(f"A1_none|{a}", "E0_height_m", "p50"), td_vz_p50_mps=cg(f"A1_none|{a}", "td_vz_m_s", "p50"))
    gd = p6["gate_delay"]
    slack_min = min(v["slack_commit_minus_gate_open_s"]["min"] for v in gd.values())
    dcrit13 = min(v["D_crit_lead_below_1.3s"]["min"] for v in gd.values())
    comp = p6["release_hold_v1p1"]["arms"]

    def compstr(a):
        e = comp.get(a)
        if not e:
            return f"{a}: NOT FLOWN"
        s = []
        for b in BASES:
            if b in e:
                v = e[b].get("vs_nrLO|none|h285") or {}
                s.append(f"{b} {e[b]['P_GNC']:.3f} (vs release at E2 {v.get('P_ref', float('nan')):.3f}, -{v.get('lost')}/+{v.get('gained')}, "
                         f"p {v.get('p_exact', float('nan')):.3g})")
        pt = e.get("P_total_DERIVED")
        if isinstance(pt, dict):
            s.append("P_total DERIVED (min over bases) " + ", ".join(f"{g} {min(v):.3f}" for g, v in pt.items() if isinstance(v, list))
                     + f", worst states {pt.get('worst_states')}")
        return f"{a} [{e['profile']}]: " + "; ".join(s)

    th = r2["thresholds"]
    m3 = th["mode3|w0.8s"]
    v35opt, rec = OrderedDict(), OrderedDict()
    for v in ("v35a", "v35t"):
        for st in ("liq", "pw"):
            row = OrderedDict()
            for o in ("h285", "h275", "h265", "h255", "h245", "kd70|h285", "ht5|h285"):
                a = f"{st}|G73|{v}|{o}"
                ex = [case(fly, b, a)["exhausted"] if case(fly, b, a) else None for b in BASES]
                row[o] = f"P {Ps(fly, a)}, exhausted {ex[0]} / {ex[1]}; vs v3d mass: {pool_str(fly, a, f'{st}|G73|h285')}"
            v35opt[f"{st}|{v}"] = row
            ev = [o for o in ("h275", "h265", "h255", "h245", "kd70|h285", "ht5|h285")
                  if fly["pooled"].get(f"{st}|G73|{v}|{o}|vs_{st}|G73|h285|main2") is not None]
            rec[f"{st}|{v}"] = ("NOT EVALUATED" if not ev else
                                [o for o in ev if not fly["pooled"][f"{st}|G73|{v}|{o}|vs_{st}|G73|h285|main2"]["loses"]] or "none")

    pad = dip.get("paired_adjusted_vs_v3d_mass", {}).get("arms", {})
    recdip = OrderedDict()
    for onset in ("flown_60g", "250N_69g", "500N_80g"):
        r_ = OrderedDict()
        for v in ("v35a", "v35t"):
            for st in ("liq", "pw"):
                ev = [o for o in ("h275", "h265", "h255", "h245", "kd70|h285", "ht5|h285")
                      if f"{st}_G73_{v}_{o.replace('|', '_')}" in pad]
                r_[f"{st}|{v}"] = ("NOT EVALUATED" if not ev else
                                   [o for o in ev if not pad[f"{st}_G73_{v}_{o.replace('|', '_')}"][onset]["loses"]] or "none")
        recdip[onset] = r_

    def dipstr(a):
        r = []
        for b in BASES:
            d = dip["arms"].get(f"{b}_{a.replace('|', '_')}")
            if d:
                r.append(f"{b} {d['P_flown']:.3f} -> {d['500N_80g']['P_adjusted']:.3f} (80 g), {d['250N_69g']['P_adjusted']:.3f} (69 g)")
        return "; ".join(r) if r else "n/a"

    fnd = OrderedDict()
    fnd["F1_late_commit_L_star_edge"] = (
        "CONFIRMED (coordinator's watch item; SIM): at the L* = 1.3 s edge the late-commit contingency does not land. "
        f"e19|G73|ant13 (commit lead p50 {ant['nominal|ant13']['lead_p50_s']} s): P {ant['nominal|ant13']['P']} (A1_none / A1J_pc) with "
        f"the nominal start and {ant['L400|ant13']['P']} with the L400 start. Mechanism: the flight software holds T_fire until 1.9 s of "
        f"flow (amendment G pgg_Tmin, lead 164 (2)), so the light comes {ant['nominal|ant13']['tfire_after_plain_p50_s']} s (p50) after the "
        f"plain trigger, E0 at {ant['nominal|ant13']['E0_height_p50_m']} m (p50), too low to arrest the descent (tipover / no touchdown). "
        f"At lead 1.7 s: {ant['nominal|ant17']['P']} nominal, {ant['L400|ant17']['P']} L400; at 2.1 s: {ant['nominal|ant21']['P']} nominal, "
        f"{ant['L400|ant21']['P']} L400; at 2.5 s: {ant['nominal|ant25']['P']} nominal, {ant['L400|ant25']['P']} L400; decided horizon "
        f"2.90 s: {Ps(fly, 'e19|G73|h285')} nominal, {Ps(fly, 'e19|G73|L400|h285')} L400. The baseline below L* (no purge, no unpurged "
        "relight) is a vehicle loss, so purging at >= 1.3 s is never worse than skipping, but the contingency band 1.3-1.7 s carries "
        "P_GNC ~0 (L400) to ~0.78 (nominal start). Holds with and without L400; not a physical result (canopy, valve timing and the "
        "Tp < 1.9 s outcome class are not modelled)")
    dcrit24 = min(v["D_crit_lead_below_2.4s"]["min"] for v in gd.values())
    leadmin = min(v["lead_nominal_s"]["min"] for v in gd.values())
    fnd["F2_gate_delay"] = (
        f"DERIVED from the nominal predictor tables: the commit happens >= {slack_min:.3f} s after the gate opens (minimum over "
        f"{len(gd)} tables), so a gate opening delayed by less than that changes nothing; a commit lead below 2.4 s needs a gate "
        f"delay >= {dcrit24:.3f} s and below 1.3 s >= {dcrit13:.3f} s. On the decided predictor path the smallest commit lead is "
        f"{leadmin:.2f} s (these tables; the reviewer: lead >= 2.66 s in 2000/2000 runs, REVIEW-GNC-R2 l.202). The probability of "
        "such a gate delay is TO-VERIFY (canopy dynamics and gate-opening dispersion are not modelled)")
    fnd["F3_release_hold_comparator"] = (
        "Line-194 comparator (SIM P_GNC x DERIVED classes): " + " | ".join(compstr(a) for a in (
            "nrLO|none|rh300c200|h285", "nrLO|none|rh190c500|h285", "nrLO|none|rh400c200|h285", "nrLO|none|rh300|h285"))
        + ". Failure modes (A1J_pc): " + "; ".join(
            f"{'release at E2' if a == 'nrLO|none|h285' else a.split('|')[2]} "
            f"{case(fly, 'A1J_pc', a)['fail_modes'] if case(fly, 'A1J_pc', a) else 'n/a'}"
            for a in ("nrLO|none|h285", "nrLO|none|rh300c200|h285", "nrLO|none|rh190c500|h285", "nrLO|none|rh400c200|h285"))
        + "; release vertical speed p50 (A1J_pc): " + ", ".join(
            f"{a.split('|')[2]} {comp[a]['A1J_pc']['rel_vz_m_s']['p50']} m/s" for a in comp
            if a in ("nrLO|none|rh300|h285", "nrLO|none|rh300c200|h285", "nrLO|none|rh190c500|h285", "nrLO|none|rh400c200|h285")
            and isinstance(comp[a].get("A1J_pc"), dict) and comp[a]["A1J_pc"].get("rel_vz_m_s"))
        + " (the extra losses against the release at E2 are mostly touchdown-criterion failures: lateral speed, rate, tilt, tipover; "
          "no-touchdown / crash cases rise from 3 to 6 only at rh400c200)"
        + ". Residual released-then-A3 from the reviewer's per-H table: 0 for H >= 0.30 s on the 200 N ramp in every group; the 500 N "
          "profile at 0.19 s covers the latest trip + one frame in every group. The worst states keep P_success 0 (LO and HI), so the "
          "comparator gains nothing there; not admissible with Pc invalid (186 (2) holds the command at the start level = lift flow).")
    fnd["F4_mass_285m"] = (
        f"v3.5 ledger at 285 m (SIM): v35a liq {Ps(fly, 'liq|G73|v35a|h285')}, pw {Ps(fly, 'pw|G73|v35a|h285')}; v35t liq "
        f"{Ps(fly, 'liq|G73|v35t|h285')}, pw {Ps(fly, 'pw|G73|v35t|h285')}; both lose against the ledger-v3d mass "
        f"({pool_str(fly, 'liq|G73|v35a|h285', 'liq|G73|h285')}; {pool_str(fly, 'liq|G73|v35t|h285', 'liq|G73|h285')}) by propellant "
        "exhaustion. Options (lead 181 (5)) without a significant pooled loss against the v3d mass at 285 m (exact McNemar p >= 0.05; "
        f"not a proof of equivalence): {json.dumps(rec)}; per option P, exhaustions and the paired result in F4_options_P. kd 0.7 "
        f"against the same bracket at 285 m: {pool_str(fly, 'liq|G73|v35a|kd70|h285', 'liq|G73|v35a|h285')} (liq v35a); the 5 m "
        f"terminal gate: {pool_str(fly, 'liq|G73|v35a|ht5|h285', 'liq|G73|v35a|h285')} (liq v35a, rate failures). The 0.20 kg "
        "allowance and the v3.5.1 ledger are NOT FLOWN (input pending). Reading: the pooled test resolves about 1-2 pp at 1000 paired "
        "runs, so the boundary is not sharp: liq v35t is not monotone in trim (h275 not significant, h265 loses at p 0.03, h255 "
        "equal); treat the trims as bands, and see F5 for the same test with the R3-17 dip onset")
    fnd["F4_options_P"] = v35opt
    fnd["F5_reserve_dip"] = (
        "Every P2 / P3 table used the 60 g ASSUMED residual. Counting a landed run with liquid below the R3-17 onset as lost (DERIVED): "
        f"liq|G73|h285 {dipstr('liq|G73|h285')}; liq|G73|v35a|h255 {dipstr('liq|G73|v35a|h255')}; liq|G73|v35a|h245 "
        f"{dipstr('liq|G73|v35a|h245')}; pw|G73|v35a|h255 {dipstr('pw|G73|v35a|h255')}. The onset near touchdown depends on the "
        "thrust then (bracket 62-80 g); outlet geometry MISSING (Mechanical OI-32). Paired re-test of the P2 options against the "
        "ledger-v3d mass with the SAME onset on both tables (DERIVED, m2_rev3_reserve_dip v1.1; the 60 g column reproduces F4): "
        "options without a significant pooled loss: " + "; ".join(f"{k}: {json.dumps(v)}" for k, v in recdip.items())
        + ". With the 69 g or 80 g onset liq v35t h275 and kd 0.7 become significant losses and pw v35a h255 at 80 g; what remains "
          "is 245 m at v35a (both states) and <= 255 m (liq) / <= 265 m (pw) at v35t")
    fnd["F6_coverage_285m"] = (
        f"285 m (SIM): liq|none {Ps(fly, 'liq|none|h285', ALL4)}, liq|G73 {Ps(fly, 'liq|G73|h285', ALL4)}, pw|G73 "
        f"{Ps(fly, 'pw|G73|h285', ALL4)}, pl|G73 {Ps(fly, 'pl|G73|h285', ALL4)}, e19|G73 {Ps(fly, 'e19|G73|h285', ALL4)} (A1_none / A1J_pc "
        f"/ A1_pc / A1J_none). Against 300 m (all four bases): liq|G73 {pool_str(fly, 'liq|G73|h285', 'liq|G73', 'all4')}, i.e. the "
        f"285 m trim gains (exhaustions 8 at 300 m -> 0 at 285 m over the four bases, staged rev2 tables; the rest of the net gain is "
        f"in the other touchdown criteria). Exception: e19|G73|L400 "
        f"{Ps(fly, 'e19|G73|L400|h285')} ({pool_str(fly, 'e19|G73|L400|h285', 'liq|none|L400|h285')}): the e19 purge edge with the "
        "fuel-starved start loses ~4 pp, mostly no-touchdown and lateral-speed failures")
    fnd["F7_R2v2"] = (
        "R2 v2 (SIM statistics): lit side PENDING (line 194 (2)). Flame-out side, mode 3 (E2 re-reference + drag compensation), "
        f"0.8 s window: inside W10 < 6 m/s the DERIVED-bound maximum is {m3['W10_lt6']['flameout_design_max_N']:.2f} N (margin "
        f"{m3['W10_lt6']['at_T_rev2']['flameout_margin_N']:+.2f} N at T_rev2 {m3['W10_lt6']['at_T_rev2']['T']:.3f} N; x 1.3 heat "
        f"pick-up {m3['W10_lt6']['sensitivities_at_T_mid']['fo_cb130']['max_N']:.1f} N); over all winds "
        f"{m3['all_winds']['flameout_design_max_N']:.2f} N (margin {m3['all_winds']['at_T_rev2']['flameout_margin_N']:+.2f} N, "
        f"{m3['all_winds']['at_T_rev2']['flameout_released']} of {m3['all_winds']['at_T_rev2']['n_fo']} flame-out runs above T_rev2). "
        "Without the command hold an undetected flame-out reaches R2 50-63 N (trace): the hold is load-bearing.")
    a5 = p5["arms"]
    fnd["F8_RG16_allowance"] = (
        f"0.5 s at 670 N (SIM, A1 at the 300 m comparator target): delta-v p50 {a5['A1asc|dla05|V']['dv_allowance_mps']['p50']:.2f} m/s "
        f"(DERIVED {a5['A1asc|dla05|V']['dv_allowance_derived_mps']['p50']:.2f}); A1 ascent apex p99 {a5['A1asc|dla05|V']['apex_m']['p99']:.1f} m "
        f"(V) / {a5['A1asc|dla05|Lhi']['apex_m']['p99']:.1f} m (Lhi), max {a5['A1asc|dla05|Lhi']['apex_m']['max']:.1f} m; B1 floor highest "
        f"height after onset p99 {a5['B1floor|dla05|V']['max_true_height_after_onset_m']['p99']:.1f} m (nominal apex "
        f"{a5['B1|nom|V']['apex_m']['p50']:.1f} m). Windowed budget: A1 comp {round(100 * rg['cases']['A1|H_cal_comp_path']['vib']['white']['strict_windowed_500ms']['strict_total'], 3)} % "
        f"(PASS by {rg['cases']['A1|H_cal_comp_path']['vib']['white']['strict_windowed_500ms']['strict_margin_pct_points']:.3f} pp), "
        f"B1 comp {round(100 * rg['cases']['B1|H_cal_comp']['vib']['white']['strict_windowed_500ms']['strict_total'], 3)} % (PASS); "
        "AR(1) vibration at the same RMS fails both; the margin is not robust")
    fnd["F9_RG08_late_flip"] = (
        f"Late flip to UNPRIMED after the plan (SIM): liqF {Ps(fly, 'liqF|G73|h285')} ({pool_str(fly, 'liqF|G73|h285', 'liq|G73|h285')}); "
        f"pwF {Ps(fly, 'pwF|G73|h285')} ({pool_str(fly, 'pwF|G73|h285', 'pw|G73|h285')}). Treating UNKNOWN as UNPRIMED from the "
        f"start costs nothing measurable (liqP {Ps(fly, 'liqP|G73|h285')}, pwP {Ps(fly, 'pwP|G73|h285')}); a flip after the plan is "
        "what costs P")
    fnd["F10_sim_start_level"] = (
        "Discrepancy kept: sim6 flies the relight start at 100 N (closed-loop floor 0.2 x F_max, relight_start_frac 0.2) before E2 "
        "while Combustion's start lift is 62.5 N (F_lift); the V2 hold flies 62.5 N after E2. The natural release-hold profile in the "
        "sim is therefore ~100 N (probe: truth 90-115 N), which is not in the hold table")
    dr = out["P3_coverage_285m"]["duty_cycle_record_285m"]["records"]
    pub = out["P3_coverage_285m"]["duty_cycle_record_285m"]["comparison"]
    v28 = pub.get("DC-A1_full_flight_disp_p99_kest2_v28liq_v3", {})
    fnd["F11_duty_cycle_record_285m"] = (
        "285 m duty-cycle record (SIM, one Monte Carlo run each, re-flown with the recorder; reproduces its table row: "
        + ", ".join(f"{v['reproduces_mc_row']}" for v in dr.values()) + "): "
        + "; ".join(f"{k.split('_')[-2]} run {v['run_index']}: engine-on counter {v['engine_on_counter_s']:.3f} s, thrust-on "
                    f"{v['thrust_on_s']:.2f} s, impulse {v['total_impulse_Ns']:.0f} N s, apex {v['apex_m']:.1f} m, liquid left "
                    f"{v['residual']['liquid_left_g']:.0f} g, inside the A1 sizing cycle ({v['vs_a1_sizing_cycle']['sizing_engine_on_counter_s']:.3f} s): "
                    f"{v['vs_a1_sizing_cycle']['inside']}" for k, v in dr.items())
        + f". The 300 m v2.8 liquid-line record burns longer (counter {v28.get('engine_on_counter_s', float('nan')):.3f} s, "
          f"impulse {v28.get('total_impulse_Ns', float('nan')):.0f} N s): the 285 m trim shortens the A1 p99 cycle; the A1_none record "
          "still lies above the published A1 sizing counter, as the 300 m record did. B1 governs thermal and erosion (lead "
          "decision 2026-10-13), so this is a record, not a sizing case")
    out["findings"] = fnd

    out["proposed_for_v3p2"] = OrderedDict(
        note="PROPOSED only. Each item needs the independent check of staging rev3 before the lead publishes v3.2; none is in gnc.json.",
        items=[
            OrderedDict(path="/rev3 (new block)", proposal="reference block to staging_v3.1/rev3 with the status of P2-P9 (done / pending / not run) "
                                                           "and the findings F1-F11, each labelled", evidence="this file"),
            OrderedDict(path="/relight_planning_181 and /rev2/amendment_G_late_commit",
                        proposal="record F1: at L* = 1.3 s the contingency purge gives P_GNC ~0 because T_fire waits for 1.9 s of flow; "
                                 "the L* rule is unchanged (purging is never worse than the no-relight baseline) but the band 1.3-1.7 s must "
                                 "not be counted as a landing; the gate-delay tolerance (F2) replaces 'probability by gate-failure injection' "
                                 "until canopy data exist", evidence="P6_late_commit"),
            OrderedDict(path="/relight_planning_181 (alternative)",
                        proposal="replace the withdrawn E2 + 0.22 s figures by the line-194 comparator results (F3), status COMPARATOR, "
                                 "not admissible with Pc invalid", evidence="P6_late_commit.comparator_line194"),
            OrderedDict(path="/propellant_closure_v3 and /flight_profile",
                        proposal="record F4 / F5: the v3.5-class landing mass re-exhausts at 285 m. On the 60 g basis the significant "
                                 "loss disappears at <= 255 m (pw) / 245 m (liq) for v35a and at <= 265 m (pw) / 275 or <= 255 m (liq) "
                                 "for v35t; with the R3-17 onset (69-80 g) on both sides it disappears only at 245 m (v35a) and "
                                 "<= 265 m (pw) / <= 255 m (liq) (v35t). Bands, not thresholds; the decision waits for massprops "
                                 "v3.5.1, the valve datasheet and the outlet geometry (OI-32)", evidence="P2_mass_285m, findings F4 / F5"),
            OrderedDict(path="/launch_commit_wind_evidence", proposal="285 m coverage tables (F6) incl. the e19|G73|L400 loss",
                        evidence="P3_coverage_285m"),
            OrderedDict(path="duty_cycles index (01-systems-gnc/duty_cycles, 'records')",
                        proposal="add the two 285 m A1 p99 records (F11) as records, not sizing cases, if the lead adopts the 285 m "
                                 "trim; the files are staged in staging_v3.1/rev3/duty_cycles/ and the published index is unchanged",
                        evidence="P3_coverage_285m.duty_cycle_record_285m"),
            OrderedDict(path="/rev2/amendment_V_pc_invalid (R2 v2)", proposal="statistics with the flame-out side and the hold trace (F7); "
                                                                              "lit side PENDING v2.4b; no pcf_tmax or threshold change proposed",
                        evidence="P4_R2v2"),
            OrderedDict(path="/over_thrust_fc_thrust and /rev2/rg16_v2", proposal="latency consequence and the windowed budget incl. B1 and "
                                                                                 "the vibration sensitivity (F8); FC_THRUST stays NOT armed on A1; "
                                                                                 "B1 arming not proposed before a measured spectrum",
                        evidence="P5_RG16_allowance"),
            OrderedDict(path="/flight_software (RG-08)", proposal="RESEARCH PROPOSAL: re-plan T_fire when the RG-08 flag flips to UNPRIMED "
                                                                 "after the plan. Hypothesis: re-planning removes the late-flip loss (F9). "
                                                                 "Comparator: liqF / pwF as flown. Evidence: paired flights with the re-plan. "
                                                                 "Refutation: the re-plan arm loses against liqF / pwF or against liqP / pwP "
                                                                 "(p < 0.05). Not flown.", evidence="P8_RG08_late_flip"),
            OrderedDict(path="/flight_software/relight_sequence_placeholder/v/purge_bound (request from Electronics, CHANGELOG line 198 (1))",
                        proposal="text correction: 2.5 s is the scheduled purge flow, not the ECU duration cap (the firmware v2.10 "
                                 "both-open cap is 2.61 s); Electronics gives 77.7 g (Combustion basis) / 83.6 g (SIL basis) vented at "
                                 "that cap, above the 76 g allowance (OI-PURGE-CAP, lead). Not flown in rev3 (G73 = 73 g booked); the "
                                 "nearest flown evidence is the rev2 G76 (76 g) and PS10 (81-107 g, upper bound) arms at 300 m, liq / pw on A1_none / A1J_pc", evidence="CHANGELOG line 198"),
            OrderedDict(path="/requirements/ignition (sim discrepancy)", proposal="state the 100 N sim start level vs 62.5 N F_lift (F10) as an "
                                                                                "open model item until a sim amendment aligns it",
                        evidence="findings.F10_sim_start_level"),
        ])

    out["line194_folds"] = OrderedDict(
        hold_withdrawn="(1) E2 + 0.22 s WITHDRAWN: the comparator is re-flown as P6c with the population hold table (0.30 s at 200 N, 0.19 s "
                       "at 500 N, 0.40 s at 200 N for the P cost, and 0.30 s on the sim's natural profile for the decomposition); the "
                       "post-E2 command profile is stated per arm; the residual released-then-A3 class comes from the reviewer's per-record "
                       "table (r3_unpurged_classes.json c162cde0363c4917; v2.4b CSV later); baseline unchanged (below L* = 1.3 s no purge "
                       "and no unpurged relight)",
        R2v2="(2) lit model 62.5 N x pcf_k WITHDRAWN: P4c not flown, lit side PENDING v2.4b; flame-out side on F_cold(lift, P_tank) "
             "stands; 16.31 N margin CONDITIONAL on CF-3; heat TO-VERIFY moved to the injector body and feed soak-back",
        R3_17="(3) dip onset carried as the effect on every flown table (reserve_dip.json); not re-flown",
        old_values_used=OrderedDict(
            hold_0p22_0p25s="nrLO|none|rh220|h285 and rh250 (both bases) used the withdrawn 0.22 / 0.25 s holds on the ~100 N guidance "
                            "profile (m2_rev3_fly v2.0, sim6 v2.10-dev); the P6 v1.0 evaluation (p6_late_commit.json) computed P_total "
                            "from them; both kept as SUPERSEDED evidence",
            residual_60g="every flown A1 table (repro, P2, P2v35, P2opt v35a / v35t, P3, P4s, P6, P6b, P6c, P8) and the 285 m duty-cycle "
                         "record used the 60 g ASSUMED residual; the dip-onset effect is applied afterwards (DERIVED), not flown",
            lit_62p5N_x_pcf_k="the P4s lit statistics arms (lit_k100, lit_k875, lit_k875_L400, lit_k875_dt05, lit_k875_dt10) and the "
                              "r2v2_eval lit columns",
        ))

    out["not_run"] = [
        "P2: the v3.5.1 ledger re-fly and a separate 0.20 kg allowance arm (Mechanical massprops_v3.5.1 not delivered)",
        "P4: the lit side on the Combustion v2.4b grain_q1d history (CSV not published); the P4c confirmation set (20 arms) incl. the "
        "landings after 0.5-0.8 s releases",
        "P5: the latency and budget flights at the 285 m trim (flown at the 300 m comparator configuration); a measured vibration spectrum",
        "P6: a gate-failure probability (canopy dynamics not modelled; only the DERIVED tolerance); the Tp < 1.9 s purge class",
        "P7: the K replacement on FSW-R2 with a throttle-map error band (SIL/HIL gate)",
        "P8: the T_fire re-plan on a late flip (proposal only)",
        "sigma_u(3 m) as a flight variable (the hard launch-commit rule is not simulated)",
        "188 (7) TVC robustness over the V5c stiffness range and the bay-wall / stop item (outside the line-181 list)",
    ]
    out["to_verify"] = [
        OrderedDict(item="bleed valve pair mass (2 x 0.30 kg ASSUMED)", owner="Mechanical / procurement (maker datasheet)", ref="182 (3)"),
        OrderedDict(item="massprops v3.5.1 (TC-02 head, 608 bearings, NZ-04 seal, bay-wall trims, GM-01/02)", owner="Mechanical", ref="182 (8)"),
        OrderedDict(item="tank outlet geometry (dip onset)", owner="Mechanical", ref="OI-32, R3-17"),
        OrderedDict(item="grain_q1d start-level lit thrust history CSV; per-record classes incl. the 500 N profile", owner="Combustion", ref="v2.4b, 194 (2)/(3)"),
        OrderedDict(item="CF-3 start-lift point (16.31 N margin condition)", owner="founders (cold-flow test) / Combustion", ref="194 (2)"),
        OrderedDict(item="injector body and feed soak-back heat (2.8-3.7 kW threshold)", owner="Combustion", ref="194 (2)"),
        OrderedDict(item="vibration spectrum at the IMU (RG-16 budget)", owner="Electronics / Mechanical (static fire or CF accelerometer record)", ref="181 (3)"),
        OrderedDict(item="canopy dynamics and gate-opening dispersion", owner="GNC with the recovery design (Mechanical)", ref="181 (2)"),
        OrderedDict(item="purge outcome class for flows 1.9-2.2 s and below 1.9 s", owner="Combustion", ref="P6 L* table"),
        OrderedDict(item="dropout length for the K replacement; throttle-map error band", owner="GNC / Electronics; Combustion", ref="181 (7)"),
        OrderedDict(item="sigma_u(3 m) measurement procedure at the pad", owner="founders (launch commit)", ref="181 (6)"),
    ]


def main():
    src = OrderedDict((k, v) for k, v in SRC.items())
    fly, p6, p6v10 = J(src["fly"]), J(src["p6"]), J(src["p6_v10"])
    dip, r2, hold = J(src["reserve_dip"]), J(src["r2v2"]), J(src["hold_trace"])
    p5, rg, mass = J(src["p5"]), J(src["rg16w"]), J(src["mass_v35"])
    dcr = J(src["dc_record"])
    out = OrderedDict(
        id="gnc-rev3-results", version="rev3 v1.0", date="2026-10-13", owner="gnc", builder=VERSION,
        status=("STAGED for an independent check (staging_v3.1/rev3/); not gnc.json; SIM / DERIVED evidence only; no hardware data; "
                "not a physical approval"),
        why="lead CHANGELOG line 181 items P2-P9 (P1 = rev2.1 / rev2.2, done); folds lines 182, 186, 188 and 194; coordinator "
            "messages of 2026-10-13 (v3.1 published at line 192; line 194 relay)",
        labels="SIM = flown in the 6-DOF Monte Carlo; DERIVED = computed from SIM tables or interface data; ASSUMED = an input "
               "without a source; DATASHEET = maker data; TO-VERIFY = needs a measurement or a decision, owner named",
        sources=OrderedDict((k, (f"{v} ({sha16(v)})" if os.path.exists(v) else f"{v} (ABSENT at build time)")) for k, v in src.items()),
    )
    out["configuration"] = sec_configuration(src)
    out["bitchecks"] = sec_bitchecks(src)
    out["P2_mass_285m"] = sec_P2(fly, dip, mass)
    out["P3_coverage_285m"] = sec_P3(fly, dip, dcr)
    out["P4_R2v2"] = sec_P4(r2, hold)
    out["P5_RG16_allowance"] = sec_P5(p5, rg)
    out["P6_late_commit"] = sec_P6(p6, p6v10)
    out["P7_K_replacement"] = OrderedDict(
        status="NOT RUN",
        why=("the replacement (k_hat / apex-predictor re-reference to throttle-map thrust with Pc invalid; freeze only for short "
             "dropouts) needs a new sim6 amendment with its own bit-check, a defined dropout length (TO-DEFINE, GNC with "
             "Electronics) and a throttle-map error band (TO-VERIFY, Combustion); the lead gates it at SIL/HIL freeze (181 (7)), "
             "not at v3.2"),
        evidence_today="rev2 amendment K evidence was flown on the mass-estimator Pc-lost configuration, not FSW-R2 (RV3-10); the "
                       "refutation stands; no over-thrust detector after an in-flight Pc loss on A1 (RV3-12, FMEA record)")
    out["P8_RG08_late_flip"] = sec_P8(fly)
    out["P9_configuration"] = OrderedDict(tag="CONFIGURATION (records)", pins=sec_P9_pins(), code=sec_P9_code(),
                                          strict_mode=("every rev3 flight ran with GNC_STRICT=1 and a pin list: an input that is unreadable or "
                                                       "differs from its pin raises before the first run (run6 / engine_v2.pin_check; "
                                                       "negative tests N1-N4 of m2_bitcheck_v29)"))
    out["missing_arms_final_eval"] = fly.get("missing", [])
    sec_synthesis(out, fly, p6, dip, p5, rg, r2)
    files = []
    for p in [v for v in src.values() if v.startswith(OUT)] + sorted(glob.glob(f"{OUT}/logs/*.log")):
        if os.path.exists(p):
            files.append(OrderedDict(path=p, sha256_16=sha16(p)))
    bc = out["bitchecks"]
    out["checkpoint"] = OrderedDict(
        delivered_date="2026-10-13", author="GNC (rev3 session)", reviewer="independent check pending (SUPERVISION-WORKFLOW)",
        claim=("SIM / DERIVED results for lead line 181 P2-P6 and P8-P9 on the rev3 code (sim6 v2.9-dev to v2.12-dev, bit-checked), "
               "with the line-194 folds; P7 not run; nothing here is a physical approval or a gnc.json change"),
        configuration="see configuration (trees, hashes, env, pins, apogee targets)",
        sources="see sources (paths and sha256/16 at build time) and the CHANGELOG / review lines quoted in each section",
        files=files,
        tests=OrderedDict(
            bitcheck_v2p10=bc["v2.10_vs_v2.9"]["off"]["all_identical"], bitcheck_v2p11=bc["v2.11_vs_v2.10"]["off"]["all_identical"],
            bitcheck_v2p12_off=bc["v2.12_vs_v2.11"]["off"]["all_identical"],
            bitcheck_v2p12_functional_v1p1=bc["v2.12_vs_v2.11"]["functional_v1p1"]["all_pass"],
            bitcheck_v2p12_functional_v1p0="FAIL (criterion defect, kept)",
            full_v29_suite_on_rev3_code=bc["v2.9_full_suite_on_rev3_code"] if isinstance(bc["v2.9_full_suite_on_rev3_code"], str)
            else bc["v2.9_full_suite_on_rev3_code"].get("result"),
            repro_against_staged_rev2=all(v["identical"] for v in fly["repro"].values()),
            rg16_reproduction_of_stored_comparators=all(e["reproduction"]["pooled_quantiles_identical"] and e["reproduction"]["per_run_mismatches"] == 0
                                                        for e in rg["cases"].values()),
            pins_resolved_and_matching=all(v["all_resolved_match"] for v in out["P9_configuration"]["pins"].values()),
            not_tested="hardware (none exists); SIL/HIL; canopy; measured vibration; the lit start history"),
        unknowns="see to_verify (owners named) and not_run",
        next_closure=["independent check of staging_v3.1/rev3 (reviewer distinct from the author), then the lead decides on "
                      "proposed_for_v3p2",
                      "Combustion v2.4b CSV -> P4 lit side and the joint P4c confirmation; then the lead sets pcf_tmax",
                      "Mechanical massprops v3.5.1 + valve datasheet -> P2 re-fly at the ledger incl. the 0.20 kg allowance",
                      "lead: trim decision for the v3.5-class mass; RG-08 re-plan proposal; F1 wording in relight planning",
                      "P7 before SIL/HIL freeze"])
    json.dump(out, open(f"{OUT}/rev3_results.json", "w"), indent=1)
    print("wrote", f"{OUT}/rev3_results.json", sha16(f"{OUT}/rev3_results.json"))


if __name__ == "__main__":
    main()
