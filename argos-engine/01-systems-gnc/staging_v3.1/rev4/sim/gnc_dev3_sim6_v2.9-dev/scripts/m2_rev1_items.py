"""m2_rev1_items v1.2 (GNC, 2026-10-13; v1.2 adds bleed_1mm_fault_bracket from m2_purge_bleed v1.2): the interface-facing values of the GNC rev1 set (response to REV-GNC-1), collected from
the result files so that the lead can fold them into gnc.json v3.1 without retyping. Every value is read from a result file
whose sha256/16 is recorded beside it; nothing here is a new computation. gnc.json v3 is NOT modified (review in progress).
Tags: SIM = 6-DOF Monte Carlo result; DERIVED = computed from sourced inputs; PROPOSAL = GNC proposal awaiting a lead decision;
DESIGN = adopted design value (LEAD decision cited).
v1.1: Electronics v2.9 handback items (electronics.json v2 da067408c1594814; LEAD decisions on the handback): release rule on the
TLM_FAST d1 flags (b4 / b7, state mask d1 & 0x0F), FC relight-planning source and key paths (the gnc.json v3 keys are nested,
not removed), pre-scheduled purge cost in the A1 reserve (m2_purge_cost) and theta at RELIGHT with the 1.0 mm balanced purge
(m2_relight_attitude v1.1 arm A1|PS10_nojet), FSW record v1.4 as-flown table.
Output: <out>/rev1_items.json"""
import hashlib
import json
import os

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_ITEMS_OUT", f"{S}/rev1_items")
VERSION = "m2_rev1_items v1.2"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def J(p):
    return json.load(open(p)), f"{p} (sha256/16 {sha16(p)})"


def build():
    e7, e7s = J(f"{S}/eng07_6v6/eng07_6v6.json")
    st, sts = J(f"{S}/start_transient/start_transient.json")
    rr, rrs = J(f"{S}/release_rule/release_rule.json")
    fr, frs = J(f"{S}/fsw_record/fsw_config_record_v1.json")
    pb, pbs = J(f"{S}/purge_bleed/purge_bleed.json")
    rg, rgs = J(f"{S}/rg16_terms/rg16_fct_terms.json")
    ga, gas = J(f"{S}/rg11a_growth/rg11a_growth.json")
    gu, gus = J(f"{S}/gust_criterion/gust_criterion.json")
    cr, crs = J(f"{S}/cap_rule/cap_rule.json")
    pc, pcs = J(f"{S}/purge_cost/purge_cost.json")
    ra, ras = J(f"{S}/relight_attitude_ps10/relight_attitude_v1.json")
    ra0, ra0s = J(f"{S}/relight_attitude/relight_attitude_v1.json")
    lim = e7["EI_limit"]["v3.4.1 re-route|RR66"]
    limp = e7["EI_limit"]["v3.4.1 re-route|PR66"]
    pooled = e7["pooled"]
    items = dict(
        version=VERSION, date="2026-10-13", status="STAGED (rev1); gnc.json v3 unchanged while REV-GNC-1 runs",
        hose_stiffness_6V6=dict(
            tag="SIM", source=e7s,
            statement=("re-routed coil (CAD v3.4.1): pressurised hose EI <= 0.25 N m2, i.e. K_max <= 23.4 N m/rad (scalar at the "
                       "largest eigenvalue of the coupled K, including any other line across the gimbal), flown at the 6.6 V "
                       "degraded plug without a loss by the decision rule on both actuator methods; EI 0.5 (K 46.7) loses at 6.6 V "
                       "and at 7.4 V on both methods. The lead criterion K_max <= 17.2 N m/rad at 7.4 V is stricter and is "
                       "supported. B-FD-1 measures the pressurised EI: its upper bound must not exceed 0.25 N m2"),
            rule_method=dict(points=[(p["EI"], p["hose_K"], p["cmd_rate"], p["lost"], p["gained"], p["p_exact"]) for p in lim["points"]],
                             EI_largest_not_losing=lim["EI_largest_not_losing"], EI_smallest_losing=lim["EI_smallest_losing"]),
            physical_method=dict(points=[(p["EI"], p["hose_K"], p["lost"], p["gained"], p["p_exact"]) for p in limp["points"]],
                                 EI_largest_not_losing=limp["EI_largest_not_losing"], EI_smallest_losing=limp["EI_smallest_losing"]),
            supply_7V4_at_EI_0p5={k: {kk: pooled[k][kk] for kk in ("P_arm", "P_ref", "lost", "gained", "p_exact", "loses")}
                                  for k in ("RR74_EI05", "PR74_EI05") if k in pooled},
            point_format="(EI N m2, K N m/rad, [command slew deg/s,] lost, gained, p) pooled A1 + B1 62 m, 1000 paired runs"),
        drogue_release_rule=dict(
            tag="DESIGN (LEAD 2026-10-13) / SIM", sources=[rrs, sts, frs],
            rule=fr["release_rule_decided"]["rule"],
            fsw_values=dict(rel_Pc_Pa=3.0e5, rel_F_N=st["cases"]["A1_none|L400"]["rel_F_N"], rise_Pa=0.8e5,
                            rel_rise_Pc_Pa_abs=2.11325e5, rel_Frise_N=st["cases"]["A1_none|L400"]["rel_Frise_N"], rel_to_s=0.10),
            start_transient_pooled_vs_decided=st["pooled_vs_decided_rule"],
            persistence_branch_on_vs_off=st["persistence_branch_on_vs_off_L400"].get("pooled"),
            note=("plateau = Combustion fuel-starved start 2.4-3.6 bar abs for 0.1-0.4 s; no plateau arm loses P against the decided "
                  "rule without a plateau; the branch is P-neutral against waiting for 3.0 bar; its value is the bounded hold")),
        relight_planner=dict(
            tag="SIM", source=sts,
            statement="do NOT add the start plateau to the relight planning value: t_ign_est + 0.3 s LOSES (pooled)",
            evidence=st["pooled_vs_decided_rule"].get("L400_te")),
        purge_trigger_gate=dict(
            tag="PROPOSAL", source=pbs,
            finding=("prg_T 3.0 s: 6 of 500 runs start the purge 10.15-10.54 s into the flight at h 301-304 m (drogue deployment) "
                     "because the trigger extrapolates h and v over lag + prg_T + prg_lead with the measured acceleration (about "
                     "-g just after deployment); duration up to 13.9 s, purge mass up to 278 g; all 6 landed"),
            P30_duration_s=pb["arms"]["A1|P30"]["purge"]["duration_s"], P25_duration_s=pb["arms"]["A1|P25"]["purge"]["duration_s"],
            gate=("evaluate the extended purge trigger only once the drogue descent is quasi-steady (|a_z,est - a_drogue| small for "
                  "a hold time, or t >= t_drogue + settle), use constant velocity beyond the plain lag, and cap the purge duration "
                  "at prg_T + margin; to be flown before the purge sequence is frozen")),
        mass_budget_rg16=dict(
            tag="SIM / DERIVED", source=rgs,
            purge_booking_residual_bound_g=rg["combustion_purge"]["residual_bound_g"],
            offsets_kg=rg["offsets_kg"],
            held_max_N={k: v["held_max_N"] for k, v in rg["cases"].items()},
            misses_670N={k: v["stuck"]["670"]["misses"] for k, v in rg["cases"].items()},
            statement=("with the adopted estimator (rocket-equation Pc-lost rule + lever/direction compensation) every case keeps "
                       "the held maximum <= 593.9 N (margin >= 56 N to 650 N) and misses no 670 N stuck case; the stuck-open bleed "
                       "is a FAULT outside the nominal budget (no FSW model, no detector)")),
        growth_beyond_Jref_rg11a=dict(tag="SIM", source=gas, mc=ga.get("mc"),
                                      cap={k: v.get("cap_m") for k, v in ga["cases"].items() if "cap_m" in v}),
        launch_commit_proposal=dict(
            tag="PROPOSAL (site data TO-DEFINE)", source=gus,
            rule=f"W10 < {gu['W_lim_10m']} m/s AND sigma_u(3 m) <= {gu['S_lim_3m']} m/s",
            sensor="anemometer at 3.0 m above the pad (sonic or fast cup); W10 from the 3 m mean by the power law alpha 0.14 or a "
                   "10 m mast",
            averaging=("mean and standard deviation over the 10 min before ARM (LITERATURE convention for mean wind and turbulence "
                       "intensity, e.g. IEC 61400-1 10-min sigma); the 6-DOF imposes sigma_u as the Dryden intensity, so the "
                       "equivalence of the two is a model-form ASSUMPTION")),
        cap_rule_proposal=dict(tag="PROPOSAL", source=crs, rule=cr["method"].split("Pre-T1-T4")[0].strip()),
        fsw_record=dict(source=frs, bases={k: dict(fsw_sha16=v["fsw_sha16"], par_sha16_nominal=v["par_sha16_nominal"])
                                           for k, v in fr["bases"].items()}, sim6=fr["sources"]["sim6"], run6=fr["sources"]["run6"],
                        as_flown={k: v["fsw_sha16"] for k, v in fr.get("as_flown", {}).items()},
                        as_flown_note=fr.get("as_flown_note")))
    # v1.1: Electronics v2.9 handback items
    a_ps = ra["arms"]["A1|PS10_nojet"]["all"]
    a_ref = ra0["arms"]["A1|ref"]["all"]
    items["drogue_release_rule"]["fc_implementation"] = dict(source=frs, **{k: v for k, v in fr["release_rule_decided"]
                                                                            ["fc_implementation"].items()})
    items["relight_planning_source"] = dict(source=frs, **fr["relight_planning_source"])
    pooled_pc = pc["pooled_vs_decided_rule"]
    items["purge_cost_A1_reserve"] = dict(
        tag="SIM (bounding: the modelled purge runs 2.6-3.4 s to the lift, the ECU's pre-scheduled purge 2.5 s)", source=pcs,
        decision="LEAD 2026-10-13 on the Electronics handback (1): PURGE PRE-SCHEDULED (ends before T_fire), 0.81 s plan holds; "
                 "GNC flies the purge N2O cost (~76 g at 1.0 mm, ~50 g at 0.8 mm) in the A1 reserve; vent balanced or axial",
        arms={k: dict(spec={kk: vv for kk, vv in v["arm"].items()}, vs_decided_rule=v["vs_decided_rule"],
                      purge_mass_g=v["purge"]["mass_g"], liq_left_g=v["liq_left_g"],
                      liq_left_shift_vs_decided_g=v["liq_left_shift_vs_decided_g"], exhausted=v["exhausted"],
                      exhausted_decided=v["exhausted_decided"], fail_modes=v["fail_modes"])
              for k, v in pc["cases"].items()},
        pooled_vs_decided_rule=pooled_pc,
        reserve_statement=("decided rule without purge: liquid left at touchdown min 114.1 g (A1_none) / 123.7 g (A1J_pc) "
                           "including the unusable 3 % (ASSUMED, about 59 g), i.e. 55-65 g usable in the worst of 500 draws; "
                           "the two lowest-reserve draws (runs 14 and 108) exhaust with the 1.0 mm purge and survive a 50 g "
                           "purge with >= 5 g usable left; the 0.8 mm bleed (~50 g) fits the A1 reserve, the 1.0 mm bleed "
                           "(~76 g) exhausts 2/500 per base (P-neutral by the decision rule; the combination with the 0.4 s "
                           "start plateau is pooled -11/+3, p 0.057, within 1 %: near the loss threshold)"),
        theta_at_RELIGHT_balanced_1mm=dict(
            source=ras, tag="SIM (flown-mass-estimator FSW, quasi-steady massless drogue: canopy oscillation not modelled)",
            hose_theta_deg=a_ps["at_relight"]["hose"]["theta_deg"], runs_above_deg=a_ps["at_relight"]["hose"]["runs_above_deg"],
            purge_window_pooled_deg=a_ps.get("purge", {}).get("hose", {}).get("pooled_time"),
            no_purge_reference_deg=a_ref["at_relight"]["hose"]["theta_deg"], reference_source=ra0s,
            statement="LEAD criterion theta <= 2 deg at RELIGHT met in the model: max 0.76 deg, 0/500 runs above 1 deg"))
    # v1.2: 1.0 mm bleed (31.3 g/s) purge / stuck-open arms with a balanced vent (m2_purge_bleed v1.2, own folder)
    pb1p = f"{S}/purge_bleed_1mm/purge_bleed.json"
    if os.path.exists(pb1p):
        pb1, pb1s = J(pb1p)
        ident = {}
        for a in ("A1_ref", "B1_ref"):
            p0, p1 = f"{S}/purge_bleed/pb_{a}.csv", f"{S}/purge_bleed_1mm/pb_{a}.csv"
            if os.path.exists(p0) and os.path.exists(p1):
                ident[a] = dict(stored=sha16(p0), reflown=sha16(p1), byte_identical=sha16(p0) == sha16(p1))
        items["bleed_1mm_fault_bracket"] = dict(
            tag="SIM (flown-mass-estimator FSW of m2_purge_bleed; v2.8 release model; balanced vent; additive / subtractive "
                "brackets of the stuck-open flow)", source=pb1s,
            arms={k: dict(P=v["P"], vs_ref=v.get("vs_ref"), exhausted=v["exhausted"],
                          bled_g=(v.get("bleed") or {}).get("bled_g"), purge_mass_g=(v.get("purge") or {}).get("mass_g"),
                          liquid_left_shift_kg=v.get("liquid_left_shift_kg"))
                  for k, v in pb1["arms"].items()},
            reference_identity=ident,
            flows="Electronics DERIVED bleed flow 11.3 / 20.1 / 31.3 g/s at 0.6 / 0.8 / 1.0 mm; the v1.1 stuck-open bracket "
                  "(6.3-19.4 g/s) covers 0.6-0.8 mm only")
    items["electronics_handback_responses"] = dict(
        source="interfaces/electronics.json v2 (da067408c1594814), 06-electronics/REPORT-v2.9-HANDBACK.md; LEAD decisions "
               "on the handback (interfaces/CHANGELOG.md 2026-10-13)",
        tlm_fast_d1=("adopted: the FC decoders mask d1 & 0x0F for the state; the release predicate uses b4 (E2 of this start) "
                     "and b7 (rise held to E2 + 0.10 s, latched) with Pc from d2-d3 (see drogue_release_rule.fc_implementation)"),
        removed_keys=("disputed with evidence: gnc.json v3 carries requirements.ignition.relight_planning_value_s."
                      "{option_c_unprimed_s, stale_or_missing_flag} (nested, as published in CHANGELOG line 98); the "
                      "Electronics generator reads them one level too high (calc/make_interface_json_v2.py line 332); "
                      "OI-GNC-V3 closes with a lookup-path fix on the Electronics side; v3.1 keeps the paths"),
        purge=("pre-scheduled purge mass flown in the A1 reserve now as a bounding check (purge_cost_A1_reserve); the full "
               "RG-01 re-fly keeps it with the Combustion tables"),
        e2_latency="16-18 ms after the light: inside the P-neutral release bracket (+100 ms -4/+4); no GNC action")
    return items


def write(items):
    p = os.path.join(OUT, "rev1_items.json")
    with open(p, "w") as f:
        json.dump(items, f, indent=1, default=float)
    print("wrote", p, sha16(p))


def main():
    os.makedirs(OUT, exist_ok=True)
    write(build())


if __name__ == "__main__":
    main()
